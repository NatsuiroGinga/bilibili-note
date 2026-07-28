import hashlib
import json
import shlex
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest


def _experiment_module():
    return import_module("flow_probe.ns3_experiment")


def _prepare_ns3_inputs(tmp_path: Path) -> tuple[Path, Path]:
    ns3_root = tmp_path / "ns-3.48"
    ns3_root.mkdir()
    launcher = ns3_root / "ns3"
    launcher.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    launcher.chmod(0o755)
    source_path = tmp_path / "queue_truth_scenario.cc"
    source_path.write_text("// 固定测试源码\n", encoding="utf-8")
    return ns3_root, source_path


class FakeSwanlabRun:
    id = "ns3-run-123"


class FakeSwanlab:
    def __init__(self) -> None:
        self.init_kwargs: dict[str, object] | None = None
        self.log_calls: list[tuple[int, dict[str, int | float]]] = []
        self.finish_calls: list[dict[str, object]] = []

    def init(self, **kwargs):
        self.init_kwargs = kwargs
        return FakeSwanlabRun()

    def log(self, metrics, *, step: int) -> None:
        assert metrics
        assert all(isinstance(value, (int, float)) for value in metrics.values())
        self.log_calls.append((step, dict(metrics)))

    def finish(self, **kwargs) -> None:
        self.finish_calls.append(kwargs)


def _output_path(command: list[str]) -> Path:
    arguments = shlex.split(command[-1])
    output = next(argument for argument in arguments if argument.startswith("--output="))
    return Path(output.removeprefix("--output="))


def _successful_executor(commands: list[list[str]]):
    def execute(command, **kwargs):
        command = list(command)
        commands.append(command)
        output_path = _output_path(command)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("测试 CSV 内容\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "ns-3 标准输出\n", "ns-3 标准错误\n")

    return execute


def _summary(path_count: int) -> dict[str, object]:
    return {
        "schema_version": "flow_probe_ns3_truth_validation_v2",
        "validation_status": "passed",
        "file_count": path_count,
        "group_count": path_count,
        "total_window_count": 120 * path_count,
        "scenario_window_counts": {},
        "qdisc_drop_l3_bytes": 100 * path_count,
        "downstream_error_loss_ppp_frame_bytes": 10 * path_count,
        "nonzero_l3_residual_count": 0,
        "nonzero_packet_residual_count": 0,
        "transition_window_count": 0,
    }


def test_formal_plan_expands_stable_unique_traceable_groups(tmp_path: Path) -> None:
    experiment = _experiment_module()
    ns3_root, _ = _prepare_ns3_inputs(tmp_path)
    output_dir = tmp_path / "formal"

    groups = experiment.build_matrix_plan(ns3_root=ns3_root, output_dir=output_dir)

    assert len(groups) == 21
    assert len({group.group_id for group in groups}) == 21
    assert len({group.csv_path.name for group in groups}) == 21
    assert [(group.scenario, group.seed) for group in groups[:4]] == [
        ("benign-low", 42),
        ("benign-low", 43),
        ("benign-low", 44),
        ("benign-high", 42),
    ]
    assert groups[0].group_id == "star-bottleneck-v1|benign-low|seed42|run1"
    assert groups[0].csv_path.name == "01-benign-low-seed42-run1.csv"
    assert groups[-1].csv_path.name == "21-dos-udp-capacity-shift-seed44-run1.csv"
    assert groups[0].command[:2] == ("env", "USER=ns3builder")
    assert groups[0].command[2:4] == (str(ns3_root / "ns3"), "run")
    assert shlex.split(groups[0].command[-1]) == [
        "scratch/flow-probe-queue-truth",
        "--scenario=benign-low",
        f"--output={groups[0].csv_path}",
        "--seed=42",
        "--run=1",
    ]


@pytest.mark.parametrize("with_file", [False, True])
def test_runner_rejects_every_existing_output_directory(tmp_path: Path, with_file: bool) -> None:
    experiment = _experiment_module()
    ns3_root, source_path = _prepare_ns3_inputs(tmp_path)
    output_dir = tmp_path / "existing"
    output_dir.mkdir()
    if with_file:
        (output_dir / "old.txt").write_text("旧制品\n", encoding="utf-8")

    with pytest.raises(experiment.MatrixConfigError, match="已存在"):
        experiment.run_ns3_matrix(
            ns3_root=ns3_root,
            source_path=source_path,
            output_dir=output_dir,
            run_name="ns3-existing-test",
        )


@pytest.mark.parametrize(
    ("scenarios", "seeds", "message"),
    [
        (("unknown-scenario",), (42,), "场景"),
        (("benign-low",), (0,), "随机种子"),
        (("benign-low",), (42, 42), "重复"),
        ((), (42,), "场景"),
    ],
)
def test_plan_rejects_invalid_scenarios_and_seeds(
    tmp_path: Path,
    scenarios: tuple[str, ...],
    seeds: tuple[int, ...],
    message: str,
) -> None:
    experiment = _experiment_module()
    ns3_root, _ = _prepare_ns3_inputs(tmp_path)

    with pytest.raises(experiment.MatrixConfigError, match=message):
        experiment.build_matrix_plan(
            ns3_root=ns3_root,
            output_dir=tmp_path / "invalid",
            scenarios=scenarios,
            seeds=seeds,
        )


@pytest.mark.parametrize("run_name", ["", "包含 空格", "../越界"])
def test_runner_rejects_invalid_run_name(tmp_path: Path, run_name: str) -> None:
    experiment = _experiment_module()
    ns3_root, source_path = _prepare_ns3_inputs(tmp_path)

    with pytest.raises(experiment.MatrixConfigError, match="运行名称"):
        experiment.run_ns3_matrix(
            ns3_root=ns3_root,
            source_path=source_path,
            output_dir=tmp_path / "invalid-run-name",
            run_name=run_name,
        )


def test_runner_rejects_missing_ns3_and_source_paths(tmp_path: Path) -> None:
    experiment = _experiment_module()
    ns3_root, source_path = _prepare_ns3_inputs(tmp_path)

    with pytest.raises(experiment.MatrixConfigError, match="ns-3 根目录"):
        experiment.run_ns3_matrix(
            ns3_root=tmp_path / "missing-ns3",
            source_path=source_path,
            output_dir=tmp_path / "missing-ns3-output",
            run_name="ns3-missing-root",
        )
    with pytest.raises(experiment.MatrixConfigError, match="源码"):
        experiment.run_ns3_matrix(
            ns3_root=ns3_root,
            source_path=tmp_path / "missing.cc",
            output_dir=tmp_path / "missing-source-output",
            run_name="ns3-missing-source",
        )


def test_successful_run_saves_logs_hashes_snapshots_metrics_and_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    experiment = _experiment_module()
    ns3_root, source_path = _prepare_ns3_inputs(tmp_path)
    output_dir = tmp_path / "smoke"
    commands: list[list[str]] = []
    validation_calls: list[list[Path]] = []
    fake_swanlab = FakeSwanlab()
    monkeypatch.setitem(sys.modules, "swanlab", fake_swanlab)

    def validator(paths):
        paths = [Path(path) for path in paths]
        validation_calls.append(paths)
        return _summary(len(paths))

    manifest = experiment.run_ns3_matrix(
        ns3_root=ns3_root,
        source_path=source_path,
        output_dir=output_dir,
        run_name="ns3-two-scenario-smoke",
        scenarios=("benign-low", "benign-random-loss"),
        seeds=(42,),
        executor=_successful_executor(commands),
        validator=validator,
    )

    assert len(commands) == 2
    assert [len(paths) for paths in validation_calls] == [1, 1, 2]
    assert (output_dir / "logs" / "01-benign-low-seed42-run1.stdout.log").read_text(
        encoding="utf-8"
    ) == "ns-3 标准输出\n"
    assert (output_dir / "logs" / "01-benign-low-seed42-run1.stderr.log").read_text(
        encoding="utf-8"
    ) == "ns-3 标准错误\n"
    assert json.loads((output_dir / "config_snapshot.json").read_text(encoding="utf-8"))[
        "seeds"
    ] == [42]
    environment = json.loads((output_dir / "environment_snapshot.json").read_text(encoding="utf-8"))
    assert environment["enforced_ns3_user"] == "ns3builder"
    source_hash = json.loads((output_dir / "source_sha256.json").read_text(encoding="utf-8"))
    assert source_hash["sha256"] == hashlib.sha256(source_path.read_bytes()).hexdigest()
    csv_hashes = json.loads((output_dir / "csv_sha256.json").read_text(encoding="utf-8"))
    assert len(csv_hashes["files"]) == 2
    assert all(len(item["sha256"]) == 64 for item in csv_hashes["files"])
    validation = json.loads((output_dir / "validation_summary.json").read_text(encoding="utf-8"))
    assert len(validation["groups"]) == 2
    assert validation["aggregate"]["total_window_count"] == 240
    statuses = json.loads((output_dir / "group_status.json").read_text(encoding="utf-8"))
    assert [item["status"] for item in statuses["groups"]] == ["finished", "finished"]
    assert (
        json.loads((output_dir / "run_status.json").read_text(encoding="utf-8"))["status"]
        == "finished"
    )

    metrics = json.loads((output_dir / "swanlab_metrics.json").read_text(encoding="utf-8"))
    assert [item["step"] for item in metrics] == [1, 2, 3]
    assert len(fake_swanlab.log_calls) == 3
    assert fake_swanlab.init_kwargs is not None
    assert fake_swanlab.init_kwargs["mode"] == "online"
    assert fake_swanlab.init_kwargs["workspace"] == "mortiswang"
    assert fake_swanlab.init_kwargs["project"] == "malicious-traffic-llm"
    assert fake_swanlab.init_kwargs["log_dir"] == str(output_dir / "swanlog" / "ns3-matrix")
    assert (output_dir / "swanlog" / "ns3-matrix").is_dir()
    assert fake_swanlab.finish_calls == [{}]

    assert manifest["status"] == "finished"
    assert manifest["run_id"] == "ns3-run-123"
    required_artifacts = {
        "config_snapshot",
        "environment_snapshot",
        "source_sha256",
        "csv_sha256",
        "group_status",
        "validation_summary",
        "swanlab_metrics",
        "stdout_log_01",
        "stderr_log_01",
        "csv_01",
    }
    assert required_artifacts.issubset(manifest["data_files"])


def test_failed_subprocess_preserves_logs_return_code_and_crashes_swanlab(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    experiment = _experiment_module()
    ns3_root, source_path = _prepare_ns3_inputs(tmp_path)
    output_dir = tmp_path / "failed"
    fake_swanlab = FakeSwanlab()
    monkeypatch.setitem(sys.modules, "swanlab", fake_swanlab)

    def failing_executor(command, **kwargs):
        return subprocess.CompletedProcess(command, 17, "失败前标准输出\n", "生成器失败\n")

    with pytest.raises(experiment.NS3GroupExecutionError, match="benign-low") as raised:
        experiment.run_ns3_matrix(
            ns3_root=ns3_root,
            source_path=source_path,
            output_dir=output_dir,
            run_name="ns3-failure-test",
            scenarios=("benign-low",),
            seeds=(42,),
            executor=failing_executor,
            validator=lambda paths: pytest.fail("子进程失败后不得验证 CSV"),
        )

    assert raised.value.returncode == 17
    assert (output_dir / "logs" / "01-benign-low-seed42-run1.stdout.log").read_text(
        encoding="utf-8"
    ) == "失败前标准输出\n"
    assert (output_dir / "logs" / "01-benign-low-seed42-run1.stderr.log").read_text(
        encoding="utf-8"
    ) == "生成器失败\n"
    run_status = json.loads((output_dir / "run_status.json").read_text(encoding="utf-8"))
    assert run_status["status"] == "crashed"
    assert run_status["failed_group_id"] == "star-bottleneck-v1|benign-low|seed42|run1"
    manifest = json.loads((output_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "crashed"
    assert fake_swanlab.finish_calls == [
        {"state": "crashed", "error": str(raised.value)},
    ]
    metrics = json.loads((output_dir / "swanlab_metrics.json").read_text(encoding="utf-8"))
    assert metrics[-1]["metrics"]["ns3/failed_group_count"] == 1
    assert all(isinstance(value, (int, float)) for value in metrics[-1]["metrics"].values())
