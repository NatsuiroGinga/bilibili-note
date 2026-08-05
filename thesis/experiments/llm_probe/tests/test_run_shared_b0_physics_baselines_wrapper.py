import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRAPPER_SOURCE = PROJECT_ROOT / "scripts" / "run_shared_b0_physics_baselines.sh"


@dataclass(frozen=True)
class WrapperFixture:
    project_root: Path
    wrapper_path: Path
    fake_bin: Path
    model_path: Path
    output_by_baseline: dict[str, Path]
    environment: dict[str, str]
    uv_log: Path
    screen_log: Path


def _write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _write_required_file(path: Path, content: str = "fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_fixture(tmp_path: Path) -> WrapperFixture:
    project_root = tmp_path / "llm_probe"
    wrapper_path = project_root / "scripts" / WRAPPER_SOURCE.name
    wrapper_path.parent.mkdir(parents=True)
    shutil.copy2(WRAPPER_SOURCE, wrapper_path)

    config_path = project_root / "configs/shared_b0_physics_baselines_seed42_200_v1.yaml"
    _write_required_file(
        config_path,
        """schema_version: flow_probe_shared_b0_physics_baselines_config_v1
tracking:
  project: malicious-traffic-llm
  workspace: mortiswang
  mode: online
  description: 测试配置
  tags: [shared-b0]
""",
    )
    required_paths = (
        "src/flow_probe/shared_b0_physics_train.py",
        "src/flow_probe/shared_b0_physics_sidecar.py",
        "src/flow_probe/train_sft.py",
        "runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl",
        "runs/data-frozen/dataset-v1-shared-b0/validation/genis_qwen.jsonl",
        "runs/data-frozen/dataset-v1-shared-b0-physics-v1/candidate/ns3_physics_train.jsonl",
        "runs/data-frozen/dataset-v1-shared-b0-physics-v1/dataset_manifest.json",
        "runs/data-frozen/dataset-v1-shared-b0-physics-v1/source_manifest.json",
        "runs/data-frozen/dataset-v1-shared-b0-physics-v1/join_audit.json",
        "runs/data-frozen/dataset-v1-shared-b0-physics-v1/materialization_audit.json",
    )
    for relative_path in required_paths:
        _write_required_file(project_root / relative_path)

    model_path = project_root / "models/Qwen3-1.7B"
    _write_required_file(model_path / "config.json", "{}\n")
    output_by_baseline = {
        "state_supervision": project_root
        / "runs/baselines/shared-b0-qwen-state-supervision-seed42-200-v1",
        "standard_pinn": project_root
        / "runs/baselines/shared-b0-qwen-standard-pinn-seed42-200-v1",
    }

    fake_bin = project_root / "fake-bin"
    uv_log = project_root / "fake-uv.log"
    screen_log = project_root / "fake-screen.log"
    _write_executable(
        fake_bin / "uv",
        """#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s\n' "$*" >>"${FAKE_UV_LOG}"
if [[ "$*" == *"python -c"* ]]; then
  printf '%s\n' '{"cuda_available": true, "bf16_supported": true}'
  exit 0
fi
if [[ "$*" == *"--preflight-only"* ]]; then
  printf '%s\n' '{"status": "passed", "max_steps": 200}'
  exit 0
fi
if [[ "$*" == *"flow-probe-train-shared-b0-physics"* ]]; then
  printf '%s\n' '假的正式训练开始'
  status=${FAKE_TRAIN_EXIT:-0}
  if [[ "$status" -ne 0 ]]; then
    printf '假的训练失败，退出码=%s\n' "$status" >&2
    exit "$status"
  fi
  output=${FAKE_OUTPUT_DIR:?缺少假的输出目录}
  mkdir -p "$output/checkpoints/checkpoint-000200" "$output/swanlog/run-fixture"
  printf '%s\n' '{"status":"completed","optimization_step":200,"physics_micro_step":400,"generation_cursor":800,"physics_cursor":2421}' >"$output/run_state.json"
  printf '%s\n' '{"status":"completed","max_steps":200,"metrics_count":200,"nonfinite_count":0}' >"$output/train_summary.json"
  printf '%s\n' '{"status":"completed","artifacts":[{"path":"train_summary.json"}]}' >"$output/artifact_manifest.json"
  : >"$output/step_metrics.jsonl"
  for ((step = 1; step <= 200; step++)); do
    printf '{"step":%s}\n' "$step" >>"$output/step_metrics.jsonl"
  done
  printf '%s\n' '本地 SwanLab 日志' >"$output/swanlog/run-fixture/run.log"
  printf '%s\n' '假的正式训练完成'
  exit 0
fi
printf '假的 uv 收到未知命令：%s\n' "$*" >&2
exit 97
""",
    )
    _write_executable(
        fake_bin / "screen",
        """#!/usr/bin/env bash
set -Eeuo pipefail
printf '%s\n' "$*" >>"${FAKE_SCREEN_LOG}"
if [[ "$*" == *" -Q select ."* ]]; then
  [[ -f "${FAKE_SCREEN_STATE}" ]]
  exit $?
fi
if [[ "$*" == *" -DmS "* ]]; then
  : >"${FAKE_SCREEN_STATE}"
  exit 0
fi
exit 96
""",
    )
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "FAKE_UV_LOG": str(uv_log),
        "FAKE_SCREEN_LOG": str(screen_log),
        "FAKE_SCREEN_STATE": str(project_root / "fake-screen.state"),
        "SHARED_B0_PHYSICS_MODEL_PATH": str(model_path),
    }
    return WrapperFixture(
        project_root=project_root,
        wrapper_path=wrapper_path,
        fake_bin=fake_bin,
        model_path=model_path,
        output_by_baseline=output_by_baseline,
        environment=environment,
        uv_log=uv_log,
        screen_log=screen_log,
    )


def _run_wrapper(
    fixture: WrapperFixture,
    *args: str,
    extra_environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = dict(fixture.environment)
    if extra_environment:
        environment.update(extra_environment)
    return subprocess.run(
        ["bash", str(fixture.wrapper_path), *args],
        cwd=fixture.project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("smoke", "state_supervision"),
        ("formal", "unknown"),
        ("formal", "state_supervision", "extra"),
    ],
)
def test_wrapper_accepts_only_formal_and_two_semantic_baselines(
    tmp_path: Path, args: tuple[str, ...]
) -> None:
    fixture = _build_fixture(tmp_path)

    result = _run_wrapper(fixture, *args)

    assert result.returncode == 2
    assert "用法" in result.stderr
    assert not fixture.uv_log.exists()


@pytest.mark.parametrize("baseline", ["state_supervision", "standard_pinn"])
def test_formal_launcher_preflights_and_uses_isolated_fixed_output(
    tmp_path: Path, baseline: str
) -> None:
    fixture = _build_fixture(tmp_path)
    environment = {
        "FAKE_OUTPUT_DIR": str(fixture.output_by_baseline[baseline]),
    }

    result = _run_wrapper(fixture, "formal", baseline, extra_environment=environment)

    assert result.returncode == 0, result.stderr
    launchers = list(
        (fixture.project_root / "runs/launchers").glob(
            f"shared-b0-physics-formal-*-*"
        )
    )
    assert len(launchers) == 1
    launcher = launchers[0]
    assert (launcher / "status.txt").read_text(encoding="utf-8").strip() == "running"
    assert (launcher / "preflight.log").is_file()
    assert (launcher / "training-preflight.json").is_file()
    assert (launcher / "capabilities.json").is_file()
    assert (launcher / "bindings.sha256").is_file()
    uv_calls = fixture.uv_log.read_text(encoding="utf-8")
    assert "--preflight-only" in uv_calls
    assert f"--baseline {baseline}" in uv_calls
    screen_call = fixture.screen_log.read_text(encoding="utf-8")
    assert "-DmS" in screen_call
    assert f"formal {baseline}" in screen_call
    assert str(fixture.output_by_baseline[baseline].relative_to(fixture.project_root)) in result.stdout


def test_wrapper_rejects_completed_formal_output_before_preflight(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    output = fixture.output_by_baseline["state_supervision"]
    _write_required_file(output / "run_state.json", '{"status":"completed"}\n')

    result = _run_wrapper(fixture, "formal", "state_supervision")

    assert result.returncode == 3
    assert "已经完成" in result.stderr
    assert not fixture.uv_log.exists()


def test_worker_preserves_training_exit_code_and_nonempty_log(tmp_path: Path) -> None:
    fixture = _build_fixture(tmp_path)
    launcher = fixture.project_root / "runs/launchers/worker-failure"
    launcher.mkdir(parents=True)
    result = _run_wrapper(
        fixture,
        "formal",
        "state_supervision",
        extra_environment={
            "FAKE_OUTPUT_DIR": str(fixture.output_by_baseline["state_supervision"]),
            "FAKE_TRAIN_EXIT": "23",
            "SHARED_B0_PHYSICS_FORMAL_WORKER": "1",
            "SHARED_B0_PHYSICS_LAUNCHER_DIR": str(launcher.relative_to(fixture.project_root)),
        },
    )

    assert result.returncode == 23
    assert (launcher / "exit-code.txt").read_text(encoding="utf-8").strip() == "23"
    assert (launcher / "status.txt").read_text(encoding="utf-8").strip() == "failed"
    assert (launcher / "launcher.log").read_text(encoding="utf-8").strip()


@pytest.mark.parametrize("baseline", ["state_supervision", "standard_pinn"])
def test_worker_accepts_only_complete_training_and_swanlab_artifacts(
    tmp_path: Path, baseline: str
) -> None:
    fixture = _build_fixture(tmp_path)
    launcher = fixture.project_root / f"runs/launchers/worker-success-{baseline}"
    launcher.mkdir(parents=True)
    output = fixture.output_by_baseline[baseline]

    result = _run_wrapper(
        fixture,
        "formal",
        baseline,
        extra_environment={
            "FAKE_OUTPUT_DIR": str(output),
            "SHARED_B0_PHYSICS_FORMAL_WORKER": "1",
            "SHARED_B0_PHYSICS_LAUNCHER_DIR": str(launcher.relative_to(fixture.project_root)),
        },
    )

    assert result.returncode == 0, result.stderr
    assert (launcher / "exit-code.txt").read_text(encoding="utf-8").strip() == "0"
    assert (launcher / "status.txt").read_text(encoding="utf-8").strip() == "finished"
    assert (output / "checkpoints/checkpoint-000200").is_dir()
    assert len((output / "step_metrics.jsonl").read_text(encoding="utf-8").splitlines()) == 200
    assert list((output / "swanlog").rglob("*"))


def test_pyproject_registers_only_the_required_training_entry() -> None:
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert pyproject_text.count("flow-probe-train-shared-b0-physics =") == 1
    assert "flow-probe-build-shared-b0-physics-sidecar =" not in pyproject_text
    assert "flow-probe-evaluate-shared-b0-physics =" not in pyproject_text
