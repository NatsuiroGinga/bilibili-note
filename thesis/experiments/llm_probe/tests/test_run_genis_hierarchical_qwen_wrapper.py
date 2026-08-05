import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.train_sft import (
    _atomic_write_json,
    build_training_binding,
    build_training_settings,
    training_binding_sha256,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRAPPER_PATH = PROJECT_ROOT / "scripts" / "run_genis_hierarchical_qwen.sh"


@dataclass(frozen=True)
class WrapperFixture:
    work_dir: Path
    config_path: Path
    model_path: Path
    output_dir: Path
    raw_config: dict[str, object]
    environment: dict[str, str]
    uv_log: Path


def _write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def _create_wrapper_fixture(
    tmp_path: Path,
    *,
    resume_policy: str = "auto",
) -> WrapperFixture:
    work_dir = tmp_path / "work"
    data_dir = work_dir / "data"
    model_path = work_dir / "models" / "Qwen3-1.7B"
    output_dir = work_dir / "runs" / "qwen"
    config_path = work_dir / "config.yaml"
    uv_log = work_dir / "fake-uv.log"
    data_dir.mkdir(parents=True)
    model_path.mkdir(parents=True)
    (data_dir / "train.jsonl").write_text(
        '{"prompt":"train","completion":"malicious"}\n',
        encoding="utf-8",
    )
    (data_dir / "validation.jsonl").write_text(
        '{"prompt":"valid","completion":"benign"}\n',
        encoding="utf-8",
    )
    (data_dir / "bundle_manifest.json").write_text("{}\n", encoding="utf-8")
    raw_config: dict[str, object] = {
        "probe": {
            "model_id": "Qwen/Qwen3-1.7B",
            "feature_view": "canonical_core_v1",
            "seed": 42,
            "max_input_length": 512,
            "max_new_tokens": 16,
            "lora_rank": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
        },
        "training": {
            "train_file": str(data_dir / "train.jsonl"),
            "validation_file": str(data_dir / "validation.jsonl"),
            "output_dir": str(output_dir),
            "learning_rate": 0.0002,
            "per_device_train_batch_size": 4,
            "gradient_accumulation_steps": 16,
            "num_train_epochs": 3,
            "save_steps": 20,
            "resume_from_checkpoint": resume_policy,
        },
        "tracking": {},
    }
    config_path.write_text(
        json.dumps(raw_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    venv_bin = work_dir / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    _write_executable(
        venv_bin / "python",
        "#!/usr/bin/env bash\n" f'exec {shlex.quote(sys.executable)} "$@"\n',
    )
    _write_executable(
        venv_bin / "swanlab",
        "#!/usr/bin/env bash\nset -euo pipefail\nprintf '假的 SwanLab：%s\\n' \"$1\"\n",
    )

    fake_bin = work_dir / "fake-bin"
    _write_executable(
        fake_bin / "uv",
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_UV_LOG}"
mkdir -p "${FAKE_OUTPUT_DIR}"
printf '假的训练命令完成\n'
""",
    )
    _write_executable(
        fake_bin / "nvidia-smi",
        "#!/usr/bin/env bash\nprintf 'Fake GPU, 24576 MiB, 0 MiB\\n'\n",
    )
    _write_executable(
        fake_bin / "df",
        "#!/usr/bin/env bash\nprintf '假的数据盘状态\\n'\n",
    )
    source_path = str(PROJECT_ROOT / "src")
    existing_pythonpath = os.environ.get("PYTHONPATH")
    environment = {
        **os.environ,
        "FAKE_OUTPUT_DIR": str(output_dir),
        "FAKE_UV_LOG": str(uv_log),
        "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
        "PYTHONPATH": (
            f"{source_path}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else source_path
        ),
    }
    return WrapperFixture(
        work_dir=work_dir,
        config_path=config_path,
        model_path=model_path,
        output_dir=output_dir,
        raw_config=raw_config,
        environment=environment,
        uv_log=uv_log,
    )


def _prepare_existing_run(
    fixture: WrapperFixture,
    *,
    status: str = "interrupted",
    complete_checkpoint: bool = True,
    write_binding: bool = True,
    write_manifest: bool = False,
) -> None:
    probe_mapping = fixture.raw_config["probe"]
    training_mapping = fixture.raw_config["training"]
    assert isinstance(probe_mapping, dict)
    assert isinstance(training_mapping, dict)
    probe = override_model_id(
        ProbeConfig.from_mapping(probe_mapping),
        str(fixture.model_path),
    )
    settings = build_training_settings(probe, training_mapping)
    binding = build_training_binding(probe, settings, fixture.model_path)
    checkpoint = fixture.output_dir / "checkpoint-20"
    checkpoint.mkdir(parents=True)
    filenames = {
        "adapter_model.safetensors",
        "optimizer.pt",
        "rng_state.pth",
        "scheduler.pt",
        "trainer_state.json",
    }
    if not complete_checkpoint:
        filenames.remove("scheduler.pt")
    for filename in sorted(filenames):
        (checkpoint / filename).write_text(filename, encoding="utf-8")
    if write_binding:
        _atomic_write_json(fixture.output_dir / "training_binding.json", binding)
    _atomic_write_json(
        fixture.output_dir / "run_state.json",
        {
            "schema_version": "qwen_sft_run_state_v1",
            "run_id": "run-fixture",
            "status": status,
            "current_step": 20,
            "latest_checkpoint": str(checkpoint),
            "binding_sha256": training_binding_sha256(binding),
            "swanlab_run_id": None,
            "started_at": "2026-07-28T00:00:00Z",
            "updated_at": "2026-07-28T00:00:01Z",
            "failure": None,
        },
    )
    if write_manifest:
        _atomic_write_json(
            fixture.output_dir / "artifact_manifest.json",
            {"run_id": "old-run", "status": "crashed"},
        )


def _run_wrapper(fixture: WrapperFixture) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "bash",
            str(WRAPPER_PATH),
            str(fixture.config_path),
            str(fixture.model_path),
        ],
        cwd=fixture.work_dir,
        env=fixture.environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_wrapper_starts_fresh_run_and_moves_log_into_output_dir(tmp_path: Path) -> None:
    fixture = _create_wrapper_fixture(tmp_path)

    result = _run_wrapper(fixture)

    assert result.returncode == 0, result.stderr
    launcher_log = fixture.output_dir / "launcher.attempt-0001.log"
    assert launcher_log.is_file()
    assert "=== 新训练预检 ===" in launcher_log.read_text(encoding="utf-8")
    assert not Path(f"{fixture.output_dir}.launcher.attempt-0001.log").exists()
    assert fixture.uv_log.read_text(encoding="utf-8").count("flow-probe-train") == 1


@pytest.mark.parametrize("status", ["prepared", "running", "interrupted"])
def test_wrapper_accepts_each_resumable_status(tmp_path: Path, status: str) -> None:
    fixture = _create_wrapper_fixture(tmp_path)
    _prepare_existing_run(fixture, status=status)

    result = _run_wrapper(fixture)

    assert result.returncode == 0, result.stderr
    launcher_log = fixture.output_dir / "launcher.attempt-0001.log"
    assert "恢复检查点" in launcher_log.read_text(encoding="utf-8")
    assert fixture.uv_log.read_text(encoding="utf-8").count("flow-probe-train") == 1


def test_wrapper_archives_manifest_and_never_overwrites_attempt_logs(tmp_path: Path) -> None:
    fixture = _create_wrapper_fixture(tmp_path)
    _prepare_existing_run(fixture, write_manifest=True)
    first_log = fixture.output_dir / "launcher.attempt-0001.log"
    first_log.write_text("第一轮日志\n", encoding="utf-8")

    first_result = _run_wrapper(fixture)
    second_result = _run_wrapper(fixture)

    assert first_result.returncode == 0, first_result.stderr
    assert second_result.returncode == 0, second_result.stderr
    assert first_log.read_text(encoding="utf-8") == "第一轮日志\n"
    assert (fixture.output_dir / "launcher.attempt-0002.log").is_file()
    assert (fixture.output_dir / "launcher.attempt-0003.log").is_file()
    archived_manifest = fixture.output_dir / "artifact_manifest.before-attempt-0002.json"
    assert json.loads(archived_manifest.read_text(encoding="utf-8")) == {
        "run_id": "old-run",
        "status": "crashed",
    }
    assert not (fixture.output_dir / "artifact_manifest.json").exists()
    assert len(fixture.uv_log.read_text(encoding="utf-8").splitlines()) == 2


@pytest.mark.parametrize(
    (
        "status",
        "complete_checkpoint",
        "write_binding",
        "resume_policy",
        "expected_error",
    ),
    [
        ("finished", True, True, "auto", "finished"),
        ("failed", True, True, "auto", "failed"),
        ("interrupted", True, False, "auto", "training_binding.json"),
        ("interrupted", False, True, "auto", "完整检查点"),
        ("interrupted", True, True, "never", "必须为 auto"),
    ],
)
def test_wrapper_rejects_unsafe_existing_runs_before_uv(
    tmp_path: Path,
    status: str,
    complete_checkpoint: bool,
    write_binding: bool,
    resume_policy: str,
    expected_error: str,
) -> None:
    fixture = _create_wrapper_fixture(tmp_path, resume_policy=resume_policy)
    _prepare_existing_run(
        fixture,
        status=status,
        complete_checkpoint=complete_checkpoint,
        write_binding=write_binding,
        write_manifest=True,
    )

    result = _run_wrapper(fixture)

    assert result.returncode != 0
    assert expected_error in result.stderr
    assert not fixture.uv_log.exists()
    assert (fixture.output_dir / "artifact_manifest.json").is_file()
    assert not list(fixture.output_dir.glob("artifact_manifest.before-attempt-*.json"))
