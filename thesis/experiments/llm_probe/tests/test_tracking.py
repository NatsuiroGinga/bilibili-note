import sys
from pathlib import Path

import pytest
import yaml

from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingConfigError,
    TrackingSettings,
    build_artifact_manifest,
    build_init_kwargs,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)


def valid_mapping() -> dict[str, object]:
    return {
        "project": "malicious-traffic-llm",
        "workspace": "mortiswang",
        "run_name": "llm-probe-hikari-pilot-seed42",
        "description": "HIKARI 诊断性 QLoRA 探针",
        "mode": "online",
        "tags": ["llm-probe", "hikari", "qlora"],
    }


def test_tracking_settings_require_online_mode() -> None:
    settings = TrackingSettings.from_mapping(valid_mapping())

    assert settings.project == "malicious-traffic-llm"
    assert settings.workspace == "mortiswang"
    assert settings.mode == "online"
    assert settings.tags == ("llm-probe", "hikari", "qlora")


def test_tracking_settings_reject_offline_fallback() -> None:
    data = valid_mapping()
    data["mode"] = "offline"

    with pytest.raises(TrackingConfigError, match="online"):
        TrackingSettings.from_mapping(data)


def test_tracking_settings_reject_tags_longer_than_swanlab_limit() -> None:
    data = valid_mapping()
    data["tags"] = ["x" * 21]

    with pytest.raises(TrackingConfigError, match="20"):
        TrackingSettings.from_mapping(data)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("project", "ci-prd-pinn", REQUIRED_SWANLAB_PROJECT),
        ("workspace", "other-user", REQUIRED_SWANLAB_WORKSPACE),
    ],
)
def test_tracking_settings_reject_wrong_cloud_destination(
    field: str, value: str, message: str
) -> None:
    data = valid_mapping()
    data[field] = value

    with pytest.raises(TrackingConfigError, match=message):
        TrackingSettings.from_mapping(data)


def test_tracking_init_groups_train_and_evaluation_runs() -> None:
    settings = TrackingSettings.from_mapping(valid_mapping())

    kwargs = build_init_kwargs(
        settings,
        phase="train",
        config={"seed": 42},
        log_dir=Path("runs/pilot/swanlog/train"),
    )

    assert kwargs["project"] == "malicious-traffic-llm"
    assert kwargs["workspace"] == "mortiswang"
    assert kwargs["name"] == "llm-probe-hikari-pilot-seed42-train"
    assert kwargs["group"] == "llm-probe-hikari-pilot-seed42"
    assert kwargs["job_type"] == "train"
    assert kwargs["mode"] == "online"
    assert kwargs["log_dir"] == "runs/pilot/swanlog/train"
    assert kwargs["config"] == {"seed": 42}


def test_artifact_manifest_records_cloud_and_local_paths() -> None:
    settings = TrackingSettings.from_mapping(valid_mapping())

    manifest = build_artifact_manifest(
        settings=settings,
        phase="evaluation",
        run_id="abc123",
        artifact_dir=Path("runs/pilot/evaluation"),
        data_files={
            "evaluation_summary": Path("runs/pilot/evaluation/evaluation_summary.json"),
            "predictions": Path("runs/pilot/evaluation/predictions.jsonl"),
        },
        status="finished",
    )

    assert manifest["run_url"] == (
        "https://swanlab.cn/@mortiswang/malicious-traffic-llm/runs/abc123/chart"
    )
    assert manifest["data_files"] == {
        "artifact_manifest": "runs/pilot/evaluation/artifact_manifest.json",
        "console_log": "runs/pilot/evaluation/console.log",
        "evaluation_summary": "runs/pilot/evaluation/evaluation_summary.json",
        "predictions": "runs/pilot/evaluation/predictions.jsonl",
        "swanlab_log_dir": "runs/pilot/evaluation/swanlog/evaluation",
    }


def test_flatten_scalar_metrics_keeps_only_trackable_values() -> None:
    flattened = flatten_scalar_metrics(
        {
            "metrics": {"macro_f1": 0.98, "sample_count": 100},
            "efficiency": {"wall_seconds": 37.5},
            "model_id": "本地模型路径",
            "predictions": ["benign"],
        },
        prefix="evaluation",
    )

    assert flattened == {
        "evaluation/metrics/macro_f1": 0.98,
        "evaluation/metrics/sample_count": 100,
        "evaluation/efficiency/wall_seconds": 37.5,
    }


def test_capture_console_log_keeps_stdout_and_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    console_log = tmp_path / "run" / "console.log"

    with capture_console_log(console_log):
        print("标准输出记录")
        print("标准错误记录", file=sys.stderr)

    captured = capsys.readouterr()
    saved = console_log.read_text(encoding="utf-8")
    assert "标准输出记录" in captured.out
    assert "标准错误记录" in captured.err
    assert "标准输出记录" in saved
    assert "标准错误记录" in saved


def test_swanlab_run_writes_finished_artifact_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeRun:
        id = "run123"

    class FakeSwanlab:
        def __init__(self) -> None:
            self.init_kwargs = None
            self.finish_calls = []

        def init(self, **kwargs):
            self.init_kwargs = kwargs
            return FakeRun()

        def finish(self, **kwargs) -> None:
            self.finish_calls.append(kwargs)

    fake_swanlab = FakeSwanlab()
    monkeypatch.setitem(sys.modules, "swanlab", fake_swanlab)
    artifact_dir = tmp_path / "run"
    metrics_path = artifact_dir / "swanlab_metrics.json"

    with swanlab_run(
        TrackingSettings.from_mapping(valid_mapping()),
        phase="evaluation",
        config={"seed": 42},
        artifact_dir=artifact_dir,
        data_files={"swanlab_metrics": metrics_path},
    ) as swanlab:
        assert swanlab is fake_swanlab
        metrics_path.write_text('{"macro_f1": 1.0}\n', encoding="utf-8")

    manifest = yaml.safe_load((artifact_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "finished"
    assert manifest["run_id"] == "run123"
    assert manifest["data_files"]["swanlab_metrics"] == str(metrics_path)
    assert fake_swanlab.finish_calls == [{}]
    assert fake_swanlab.init_kwargs["log_dir"] == str(artifact_dir / "swanlog" / "evaluation")


def test_swanlab_run_writes_crashed_artifact_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeRun:
        id = "failed123"

    class FakeSwanlab:
        def __init__(self) -> None:
            self.finish_calls = []

        def init(self, **kwargs):
            return FakeRun()

        def finish(self, **kwargs) -> None:
            self.finish_calls.append(kwargs)

    fake_swanlab = FakeSwanlab()
    monkeypatch.setitem(sys.modules, "swanlab", fake_swanlab)
    artifact_dir = tmp_path / "failed-run"

    with (
        pytest.raises(RuntimeError, match="诊断异常"),
        swanlab_run(
            TrackingSettings.from_mapping(valid_mapping()),
            phase="train",
            config={"seed": 42},
            artifact_dir=artifact_dir,
            data_files={"training_summary": artifact_dir / "training_summary.json"},
        ),
    ):
        raise RuntimeError("诊断异常")

    manifest = yaml.safe_load((artifact_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "crashed"
    assert manifest["run_id"] == "failed123"
    assert fake_swanlab.finish_calls == [{"state": "crashed", "error": "诊断异常"}]


def test_swanlab_run_rejects_reused_artifact_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeSwanlab:
        def init(self, **kwargs):
            raise AssertionError("复用目录时不得创建云端运行")

    monkeypatch.setitem(sys.modules, "swanlab", FakeSwanlab())
    artifact_dir = tmp_path / "existing-run"
    artifact_dir.mkdir()
    (artifact_dir / "artifact_manifest.json").write_text("{}\n", encoding="utf-8")

    with (
        pytest.raises(TrackingConfigError, match="不得复用"),
        swanlab_run(
            TrackingSettings.from_mapping(valid_mapping()),
            phase="train",
            config={"seed": 42},
            artifact_dir=artifact_dir,
            data_files={},
        ),
    ):
        pass


CONFIG_PATHS = sorted(
    path for path in Path("configs").glob("*.yaml") if not path.name.startswith(".")
)


@pytest.mark.parametrize("config_path", CONFIG_PATHS)
def test_all_experiment_configs_enable_online_tracking(config_path: Path) -> None:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    settings = TrackingSettings.from_mapping(raw["tracking"])

    assert settings.project == "malicious-traffic-llm"
    assert settings.workspace == "mortiswang"
    assert settings.mode == "online"
