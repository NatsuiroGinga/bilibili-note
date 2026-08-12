"""E2 困难域正式包装器与冻结配置的最小合同。"""

from __future__ import annotations

import copy
import json
import os
import random
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
import yaml

import flow_probe.e2_hard_domain_train as hard_domain_train
from flow_probe.e2_hard_domain_data import E2_FEATURE_FIELDS, E2Panel, E2Sample
from flow_probe.e2_hard_domain_train import (
    E2RunError,
    TrackingConfig,
    _SwanLabLogger,
    load_config,
)
from flow_probe.e2_shared_pinn import E2_PINN_VARIANTS


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = PROJECT_ROOT / "scripts/run_e2_hard_domain.sh"
CONFIGS = tuple(
    PROJECT_ROOT / f"configs/e2_hard_domain_seed{seed}.yaml" for seed in (42, 43, 44)
)


def _raw_config(path: Path) -> dict[str, object]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _gate_receipt(path: Path, *, variant: str, attempt: int) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": "flow_probe_e2_swanlab_gate_v1",
                "status": "passed",
                "variant": variant,
                "attempt": attempt,
                "ping_exit": 0,
                "verify_exit": 0,
                "checked_at": time.time(),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _seed_fake_finished_variant(output_dir: Path, variant_slug: str) -> Path:
    variant_dir = output_dir / "variants" / variant_slug
    (variant_dir / "checkpoints").mkdir(parents=True)
    (variant_dir / "predictions").mkdir()
    (variant_dir / "swanlog").mkdir()
    summary_path = variant_dir / "summary.json"
    summary_path.write_text(
        '{"status":"finished","sentinel":"preserve-existing-variant"}\n',
        encoding="utf-8",
    )
    (variant_dir / "metrics.jsonl").write_text("{}\n", encoding="utf-8")
    (variant_dir / "predictions" / "target_c.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    (variant_dir / "predictions" / "source_calibration.jsonl").write_text(
        "{}\n", encoding="utf-8"
    )
    (variant_dir / "checkpoints" / "checkpoint-000200.pt").write_text(
        "checkpoint\n", encoding="utf-8"
    )
    (variant_dir / "swanlog" / ".gitignore").write_text("*\n", encoding="utf-8")
    return summary_path


def _completed_optimizer(
    model: torch.nn.Module,
    *,
    config: hard_domain_train.E2RunConfig,
    variant: str,
) -> torch.optim.AdamW:
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    for name, parameter in model.named_parameters():
        parameter.grad = (
            None
            if variant == "E2-A" and name.startswith("state_head.")
            else torch.zeros_like(parameter)
        )
    for _step in range(config.max_steps):
        optimizer.step()
    return optimizer


def _finished_checkpoint_payload(
    config: hard_domain_train.E2RunConfig,
    *,
    model: torch.nn.Module,
    variant: str,
    initial_state_sha256: str,
) -> dict[str, object]:
    optimizer = _completed_optimizer(model, config=config, variant=variant)
    return {
        "schema_version": "flow_probe_e2_checkpoint_v1",
        "variant": variant,
        "seed": config.seed,
        "step": config.max_steps,
        "initial_state_sha256": initial_state_sha256,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "torch_rng_state": torch.get_rng_state(),
        "numpy_rng_state": np.random.get_state(),
        "python_rng_state": random.getstate(),
    }


def _fake_worker_environment(
    tmp_path: Path, *, run_mode: str = "formal"
) -> tuple[dict[str, str], Path, Path, Path]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    calls_path = tmp_path / "calls.log"
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()
    output_dir = tmp_path / "output"
    home = tmp_path / "home"
    home.mkdir()
    (home / ".bashrc").write_text("", encoding="utf-8")
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env bash
set -eu
if [[ "$1" == run && "$2" == --no-sync && "$3" == swanlab ]]; then
  printf 'gate:%s\n' "$4" >>"$FAKE_SWANLAB_CALLS"
  if [[ "$4" == ping && "${FAKE_PING_FAIL:-0}" == 1 ]]; then
    exit 1
  fi
  exit 0
fi
if [[ "$1" != run || "$2" != --no-sync || "$3" != python ]]; then
  exit 2
fi
shift 3
output=
variant=
attempt=
while (($#)); do
  case "$1" in
    --output-dir) output=$2; shift 2 ;;
    --variant) variant=$2; shift 2 ;;
    --attempt) attempt=$2; shift 2 ;;
    *) shift ;;
  esac
done
printf 'python:%s:%s\n' "$variant" "$attempt" >>"$FAKE_SWANLAB_CALLS"
mkdir -p "$output/variants"
slug=${variant,,}
variant_dir="$output/variants/$slug"
if [[ "$variant" == E2-A && -f "$variant_dir/summary.json" ]]; then
  printf '{"status":"already_finished"}\n'
  exit 0
fi
if [[ "$variant" == E2-S && "$attempt" == 1 ]]; then
  mkdir -p "$variant_dir/swanlog"
  printf '*\n' >"$variant_dir/swanlog/.gitignore"
  printf '{"code":"swanlab_init_unauthorized"}\n' >"$output/failure.json"
  exit 1
fi
if [[ "$variant" == E2-S && "$attempt" == 2 ]]; then
  mkdir -p "$output/failure-history/001" "$output/failed-attempts"
  mv "$output/failure.json" "$output/failure-history/001/failure.json"
  mv "$variant_dir" "$output/failed-attempts/e2-s-zero-step-001"
fi
mkdir -p "$variant_dir/checkpoints" "$variant_dir/predictions" "$variant_dir/swanlog"
printf '{}\n' >"$variant_dir/summary.json"
printf '{}\n' >"$variant_dir/metrics.jsonl"
printf '{}\n' >"$variant_dir/predictions/target_c.jsonl"
printf '{}\n' >"$variant_dir/predictions/source_calibration.jsonl"
printf '{}\n' >"$variant_dir/swanlab-gate.json"
printf 'checkpoint\n' >"$variant_dir/checkpoints/checkpoint-000200.pt"
printf '*\n' >"$variant_dir/swanlog/.gitignore"
if [[ "$variant" == E2-X ]]; then
  printf '{"status":"finished","finished_variants":["E2-A","E2-S","E2-P","E2-X"]}\n' >"$output/run_state.json"
  printf '{"status":"finished","variants":{"E2-A":{},"E2-S":{},"E2-P":{},"E2-X":{}}}\n' >"$output/summary.json"
  printf '{}\n' >"$output/input_binding.json"
  printf '{}\n' >"$output/physics_binding.json"
  printf '{}\n' >"$output/artifact_manifest.json"
fi
printf '{"status":"variant_finished"}\n'
""",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    fake_screen = fake_bin / "screen"
    fake_screen.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_screen.chmod(0o755)
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(home),
            "PATH": f"{fake_bin}:{environment['PATH']}",
            "FAKE_SWANLAB_CALLS": str(calls_path),
            "E2_HARD_DOMAIN_FORMAL_WORKER": "1",
            "E2_HARD_DOMAIN_RUN_MODE": run_mode,
            "E2_HARD_DOMAIN_LAUNCHER_DIR": str(launcher_dir),
            "E2_HARD_DOMAIN_OUTPUT_DIR": str(output_dir),
        }
    )
    return environment, launcher_dir, output_dir, calls_path


@dataclass
class _FakeResponse:
    status_code: int


class _FakeUnauthorized(RuntimeError):
    def __init__(self) -> None:
        super().__init__("API Request Failed: [Unauthorized] HTTP 401")
        self.response = _FakeResponse(status_code=401)


def test_wrapper_uses_frozen_uv_and_preserves_pipeline_status() -> None:
    source = WRAPPER.read_text(encoding="utf-8")

    assert "uv run --no-sync python -m flow_probe.e2_hard_domain_train" in source
    assert "PIPESTATUS" in source
    assert "rsync --delete" not in source
    assert "uv sync" not in source
    assert "screen -L" in source
    assert "failure-receipt.json" in source


def test_wrapper_isolates_variants_and_bounds_swanlab_401_recovery() -> None:
    source = WRAPPER.read_text(encoding="utf-8")

    assert "uv run --no-sync swanlab ping" in source
    assert "uv run --no-sync swanlab verify" in source
    assert "--variant" in source
    assert "--resume" in source
    assert "MAX_SWANLAB_ATTEMPTS=2" in source
    assert '"swanlab_init_unauthorized"' in source


def test_resume_worker_preserves_a_and_retries_only_s_init_401_in_new_process(
    tmp_path: Path,
) -> None:
    environment, launcher_dir, output_dir, calls_path = _fake_worker_environment(
        tmp_path, run_mode="resume"
    )
    a_summary = _seed_fake_finished_variant(output_dir, "e2-a")
    original_a_summary = a_summary.read_bytes()

    completed = subprocess.run(
        [
            "bash",
            str(WRAPPER),
            "resume",
            "configs/e2_hard_domain_seed42.yaml",
            "runs/e2-hard-domain/existing-run",
        ],
        cwd=PROJECT_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr
    calls = calls_path.read_text(encoding="utf-8").splitlines()
    assert [line for line in calls if line.startswith("python:")] == [
        "python:E2-A:1",
        "python:E2-S:1",
        "python:E2-S:2",
        "python:E2-P:1",
        "python:E2-X:1",
    ]
    assert calls.count("gate:ping") == 5
    assert calls.count("gate:verify") == 5
    assert a_summary.read_bytes() == original_a_summary
    assert (output_dir / "failed-attempts" / "e2-s-zero-step-001").is_dir()
    assert (launcher_dir / "status.txt").read_text(encoding="utf-8").strip() == "finished"


def test_worker_stops_immediately_when_executable_swanlab_gate_fails(tmp_path: Path) -> None:
    environment, launcher_dir, output_dir, calls_path = _fake_worker_environment(tmp_path)
    environment["FAKE_PING_FAIL"] = "1"

    completed = subprocess.run(
        ["bash", str(WRAPPER), "formal", "configs/e2_hard_domain_seed42.yaml"],
        cwd=PROJECT_ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert completed.returncode != 0
    assert calls_path.read_text(encoding="utf-8").splitlines() == ["gate:ping", "gate:verify"]
    assert not output_dir.exists()
    failure = json.loads((launcher_dir / "failure-receipt.json").read_text(encoding="utf-8"))
    assert failure["failure_code"] == "swanlab_gate_failed"


def test_same_process_second_swanlab_init_is_blocked_before_fake_401(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    init_calls: list[dict[str, object]] = []
    finish_calls: list[dict[str, object]] = []

    def fake_init(**kwargs: object) -> object:
        init_calls.append(dict(kwargs))
        if len(init_calls) == 2:
            raise _FakeUnauthorized()
        return SimpleNamespace(id="first-run")

    fake_client = SimpleNamespace(
        init=fake_init,
        log=lambda *_args, **_kwargs: None,
        finish=lambda **kwargs: finish_calls.append(dict(kwargs)),
    )
    monkeypatch.setitem(sys.modules, "swanlab", fake_client)
    monkeypatch.setattr(hard_domain_train, "_SWANLAB_INIT_ATTEMPTED", False)
    tracking = TrackingConfig(
        workspace="workspace",
        project="project",
        mode="online",
        run_name="e2-seed42",
        tags=("e2",),
    )
    first_output = tmp_path / "first"
    first_output.mkdir()
    first = _SwanLabLogger(
        tracking,
        variant="E2-A",
        seed=42,
        attempt=1,
        gate_receipt=_gate_receipt(tmp_path / "gate-a.json", variant="E2-A", attempt=1),
        output_dir=first_output,
        config={"seed": 42},
    )
    first.finish()

    second_output = tmp_path / "second"
    second_output.mkdir()
    with pytest.raises(E2RunError) as captured:
        _SwanLabLogger(
            tracking,
            variant="E2-S",
            seed=42,
            attempt=1,
            gate_receipt=_gate_receipt(
                tmp_path / "gate-s.json", variant="E2-S", attempt=1
            ),
            output_dir=second_output,
            config={"seed": 42},
        )

    assert captured.value.code == "multiple_swanlab_runs_in_process"
    assert len(init_calls) == 1
    assert len(finish_calls) == 1


def test_swanlab_init_401_is_structured_as_retryable_tracking_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_client = SimpleNamespace(
        init=lambda **_kwargs: (_ for _ in ()).throw(_FakeUnauthorized()),
        log=lambda *_args, **_kwargs: None,
        finish=lambda **_kwargs: None,
    )
    monkeypatch.setitem(sys.modules, "swanlab", fake_client)
    monkeypatch.setattr(hard_domain_train, "_SWANLAB_INIT_ATTEMPTED", False)
    output_dir = tmp_path / "variant"
    output_dir.mkdir()

    with pytest.raises(E2RunError) as captured:
        _SwanLabLogger(
            TrackingConfig(
                workspace="workspace",
                project="project",
                mode="online",
                run_name="e2-seed42",
                tags=("e2",),
            ),
            variant="E2-S",
            seed=42,
            attempt=1,
            gate_receipt=_gate_receipt(
                tmp_path / "gate-s.json", variant="E2-S", attempt=1
            ),
            output_dir=output_dir,
            config={"seed": 42},
        )

    assert captured.value.code == "swanlab_init_unauthorized"
    assert captured.value.details == {
        "stage": "tracking_init",
        "retryable": True,
        "variant": "E2-S",
        "attempt": 1,
    }


def test_recovery_preserves_finished_a_and_archives_only_zero_step_s(tmp_path: Path) -> None:
    config = load_config(CONFIGS[0], project_root=PROJECT_ROOT)
    models, initial_state_sha256 = hard_domain_train._build_models(config)
    budgets = hard_domain_train._shared_budgets(config)
    budget_signatures = {
        variant: asdict(hard_domain_train.training_budget_signature(models[variant], budgets[variant]))
        for variant in config.variants
    }
    calibration_sample = E2Sample(
        sample_id="calibration-1",
        capture_id="capture-a",
        profile="A",
        split_id="calibration",
        label=0,
        features=(0.0,) * len(E2_FEATURE_FIELDS),
        stable_order=1,
    )
    target_sample = E2Sample(
        sample_id="target-1",
        capture_id="capture-c",
        profile="C",
        split_id="validation",
        label=1,
        features=(1.0,) * len(E2_FEATURE_FIELDS),
        stable_order=2,
    )
    panel = E2Panel(
        panel=config.panel,
        train=(),
        calibration=(calibration_sample,),
        target=(target_sample,),
    )
    output_dir = tmp_path / "run"
    a_dir = output_dir / "variants" / "e2-a"
    final_checkpoint = a_dir / "checkpoints" / f"checkpoint-{config.max_steps:06d}.pt"
    final_checkpoint.parent.mkdir(parents=True)
    torch.save(
        _finished_checkpoint_payload(
            config,
            model=models["E2-A"],
            variant="E2-A",
            initial_state_sha256=initial_state_sha256,
        ),
        final_checkpoint,
    )
    metrics_path = a_dir / "metrics.jsonl"
    metric_records = [
        {
            "step": step,
            "event": "optimizer_step",
            "time": float(step),
            "metrics": {"train/total_loss": 1.0 / step},
        }
        for step in range(1, config.max_steps + 1)
        if step == 1 or step % config.log_steps == 0 or step == config.max_steps
    ]
    metric_records.append(
        {
            "step": config.max_steps + 1,
            "event": "target_evaluation",
            "time": float(config.max_steps + 1),
            "metrics": {"target/macro_f1": 0.5},
        }
    )
    metrics_path.write_text(
        "\n".join(json.dumps(record) for record in metric_records) + "\n",
        encoding="utf-8",
    )
    threshold = 0.5
    for path, sample, probability in (
        (
            a_dir / "predictions" / "source_calibration.jsonl",
            calibration_sample,
            0.25,
        ),
        (a_dir / "predictions" / "target_c.jsonl", target_sample, 0.75),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "sample_id": sample.sample_id,
                    "capture_id": sample.capture_id,
                    "profile": sample.profile,
                    "stable_order": sample.stable_order,
                    "label": sample.label,
                    "probability_malicious": probability,
                    "threshold": threshold,
                    "prediction": int(probability >= threshold),
                }
            )
            + "\n",
            encoding="utf-8",
        )
    a_summary = {
        "schema_version": "flow_probe_e2_variant_summary_v1",
        "status": "finished",
        "variant": "E2-A",
        "seed": config.seed,
        "panel": config.panel,
        "initial_state_sha256": initial_state_sha256,
        "optimization_steps": config.max_steps,
        "detection_batch_size": config.batch_size,
        "physics_batch_size": config.batch_size,
        "latest_checkpoint": str(final_checkpoint.resolve()),
        "threshold": threshold,
        "parameter_budget": budget_signatures["E2-A"]["parameter_budget"],
        "training_budget": budget_signatures["E2-A"],
        "source_calibration_metrics": {"macro_f1": 0.5},
        "target_metrics": {"macro_f1": 0.5},
        "last_training_step": {"step": config.max_steps},
    }
    summary_path = a_dir / "summary.json"
    summary_path.write_text(json.dumps(a_summary) + "\n", encoding="utf-8")
    original_a_summary = summary_path.read_bytes()
    s_dir = output_dir / "variants" / "e2-s"
    (s_dir / "swanlog").mkdir(parents=True)
    (s_dir / "swanlog" / ".gitignore").write_text("*\n", encoding="utf-8")
    (output_dir / "failure.json").write_text(
        json.dumps(
            {
                "code": "unhandled_exception",
                "message": "API Request Failed: [Unauthorized]",
                "traceback": "_SwanLabLogger -> swanlab.init",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summaries = hard_domain_train._load_finished_variant_summaries(
        config,
        output_dir=output_dir,
        initial_state_sha256=initial_state_sha256,
        models=models,
        budget_signatures=budget_signatures,
        panel=panel,
    )
    prepared = hard_domain_train._prepare_variant_directory(output_dir, variant="E2-S")

    assert list(summaries) == ["E2-A"]
    assert summary_path.read_bytes() == original_a_summary
    assert prepared == s_dir
    assert not s_dir.exists()
    archives = tuple((output_dir / "failed-attempts").iterdir())
    assert len(archives) == 1
    assert (archives[0] / "swanlog" / ".gitignore").is_file()
    assert (archives[0] / "archive-receipt.json").is_file()


def test_recovery_refuses_to_archive_trained_incomplete_variant(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    s_dir = output_dir / "variants" / "e2-s"
    s_dir.mkdir(parents=True)
    (s_dir / "metrics.jsonl").write_text('{"step": 1}\n', encoding="utf-8")
    (output_dir / "failure.json").write_text(
        json.dumps(
            {
                "code": "swanlab_init_unauthorized",
                "variant": "E2-S",
                "details": {"stage": "tracking_init", "variant": "E2-S"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(E2RunError) as captured:
        hard_domain_train._prepare_variant_directory(output_dir, variant="E2-S")

    assert captured.value.code == "resume_requires_checkpoint_support"
    assert s_dir.is_dir()
    assert not (output_dir / "failed-attempts").exists()


"""种子 42 原始 formal 启动器实际写入的四键 `binding.txt`，不含 `mode`。"""
LEGACY_FORMAL_BINDING_LINES = (
    "config=configs/e2_hard_domain_seed42.yaml",
    "output=runs/e2-hard-domain/existing-run",
    "screen=e2-seed42-original",
    "run_id=original",
)
CURRENT_FORMAL_BINDING_LINES = ("mode=formal",) + LEGACY_FORMAL_BINDING_LINES
RESUME_BINDING_LINES = ("mode=resume",) + LEGACY_FORMAL_BINDING_LINES


def _build_legacy_401_fixture(
    project_root: Path, binding_lines: tuple[str, ...]
) -> tuple[Path, Path, Path]:
    """构造被覆盖根失败收据、零步 `E2-S` 目录和原 formal 启动器 401 证据。"""
    output_dir = project_root / "runs/e2-hard-domain/existing-run"
    s_dir = output_dir / "variants/e2-s"
    (s_dir / "swanlog").mkdir(parents=True)
    (s_dir / "swanlog/.gitignore").write_text("*\n", encoding="utf-8")
    root_failure = output_dir / "failure.json"
    root_failure.write_text(
        '{"code":"unsafe_zero_step_recovery","message":"后续恢复失败"}\n',
        encoding="utf-8",
    )
    formal_launcher = project_root / "runs/launchers/e2-hard-domain-existing-run"
    formal_launcher.mkdir(parents=True)
    binding_path = formal_launcher / "binding.txt"
    binding_path.write_text("\n".join(binding_lines) + "\n", encoding="utf-8")
    log_path = formal_launcher / "launcher.log"
    log_path.write_text(
        json.dumps(
            {
                "status": "failed",
                "code": "unhandled_exception",
                "message": "API Request Failed: [Unauthorized] HTTP 401",
                "traceback": "_SwanLabLogger -> swanlab.init",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    receipt_path = project_root / "runs/launchers/resume/legacy-swanlab-evidence.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(
        json.dumps(
            {
                "schema_version": "flow_probe_e2_legacy_swanlab_evidence_v1",
                "status": "captured",
                "output_dir": "runs/e2-hard-domain/existing-run",
                "formal_launcher": "runs/launchers/e2-hard-domain-existing-run",
                "binding_path": "runs/launchers/e2-hard-domain-existing-run/binding.txt",
                "binding_sha256": hard_domain_train._sha256_file(binding_path),
                "launcher_log_path": "runs/launchers/e2-hard-domain-existing-run/launcher.log",
                "launcher_log_sha256": hard_domain_train._sha256_file(log_path),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return output_dir, s_dir, receipt_path


@pytest.mark.parametrize(
    "binding_lines",
    (
        pytest.param(LEGACY_FORMAL_BINDING_LINES, id="legacy_four_key_binding"),
        pytest.param(CURRENT_FORMAL_BINDING_LINES, id="current_five_key_binding"),
    ),
)
def test_recovery_uses_fixed_formal_launcher_401_after_root_failure_was_overwritten(
    tmp_path: Path, binding_lines: tuple[str, ...]
) -> None:
    project_root = tmp_path / "project"
    output_dir, s_dir, receipt_path = _build_legacy_401_fixture(
        project_root, binding_lines
    )
    original_root_failure = (output_dir / "failure.json").read_bytes()

    prepared = hard_domain_train._prepare_variant_directory(
        output_dir,
        variant="E2-S",
        legacy_failure_evidence=receipt_path,
        project_root=project_root,
    )

    assert prepared == s_dir
    assert not s_dir.exists()
    assert (output_dir / "failure.json").read_bytes() == original_root_failure
    archives = tuple((output_dir / "failed-attempts").iterdir())
    assert len(archives) == 1
    assert (archives[0] / "archive-receipt.json").is_file()


def test_recovery_rejects_non_formal_launcher_binding_as_legacy_evidence(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    output_dir, s_dir, receipt_path = _build_legacy_401_fixture(
        project_root, RESUME_BINDING_LINES
    )

    with pytest.raises(E2RunError) as captured:
        hard_domain_train._prepare_variant_directory(
            output_dir,
            variant="E2-S",
            legacy_failure_evidence=receipt_path,
            project_root=project_root,
        )

    assert captured.value.code == "unsafe_zero_step_recovery"
    assert s_dir.is_dir()
    assert not (output_dir / "failed-attempts").exists()


@pytest.mark.parametrize("corruption", ("optimizer_step", "numpy_rng", "model_nan"))
def test_finished_checkpoint_rejects_corrupt_training_state(
    tmp_path: Path, corruption: str
) -> None:
    config = load_config(CONFIGS[0], project_root=PROJECT_ROOT)
    models, initial_state_sha256 = hard_domain_train._build_models(config)
    model = models["E2-A"]
    payload = _finished_checkpoint_payload(
        config,
        model=model,
        variant="E2-A",
        initial_state_sha256=initial_state_sha256,
    )
    if corruption == "optimizer_step":
        optimizer = payload["optimizer"]
        assert isinstance(optimizer, dict)
        optimizer_state = optimizer["state"]
        assert isinstance(optimizer_state, dict)
        first_state = next(iter(optimizer_state.values()))
        assert isinstance(first_state, dict)
        first_state["step"] = torch.tensor(config.max_steps - 1)
    elif corruption == "numpy_rng":
        payload["numpy_rng_state"] = "invalid"
    else:
        model_state = payload["model"]
        assert isinstance(model_state, dict)
        first_tensor = next(iter(model_state.values()))
        assert isinstance(first_tensor, torch.Tensor)
        with torch.no_grad():
            first_tensor.reshape(-1)[0] = float("nan")
    checkpoint = tmp_path / f"{corruption}.pt"
    torch.save(payload, checkpoint)

    with pytest.raises(E2RunError) as captured:
        hard_domain_train._validate_finished_checkpoint(
            checkpoint,
            config=config,
            variant="E2-A",
            initial_state_sha256=initial_state_sha256,
            expected_model=model,
        )

    assert captured.value.code == "finished_variant_incomplete"


def test_finished_checkpoint_accepts_valid_adamw_state_subset(tmp_path: Path) -> None:
    config = load_config(CONFIGS[0], project_root=PROJECT_ROOT)
    models, initial_state_sha256 = hard_domain_train._build_models(config)
    model = models["E2-A"]
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    first_parameter = next(model.parameters())
    first_parameter.grad = torch.zeros_like(first_parameter)
    for _step in range(config.max_steps):
        optimizer.step()
    optimizer_state = optimizer.state_dict()
    assert len(optimizer_state["state"]) == 1
    checkpoint = tmp_path / "valid-subset.pt"
    torch.save(
        {
            "schema_version": "flow_probe_e2_checkpoint_v1",
            "variant": "E2-A",
            "seed": config.seed,
            "step": config.max_steps,
            "initial_state_sha256": initial_state_sha256,
            "model": model.state_dict(),
            "optimizer": optimizer_state,
            "torch_rng_state": torch.get_rng_state(),
            "numpy_rng_state": np.random.get_state(),
            "python_rng_state": random.getstate(),
        },
        checkpoint,
    )

    hard_domain_train._validate_finished_checkpoint(
        checkpoint,
        config=config,
        variant="E2-A",
        initial_state_sha256=initial_state_sha256,
        expected_model=model,
    )


def test_finished_metrics_require_every_frozen_log_step(tmp_path: Path) -> None:
    config = load_config(CONFIGS[0], project_root=PROJECT_ROOT)
    assert config.log_steps == 1
    metrics_path = tmp_path / "metrics.jsonl"
    metrics_path.write_text(
        "\n".join(
            json.dumps(record)
            for record in (
                {
                    "step": 1,
                    "event": "optimizer_step",
                    "time": 1.0,
                    "metrics": {"train/total_loss": 1.0},
                },
                {
                    "step": config.max_steps,
                    "event": "optimizer_step",
                    "time": float(config.max_steps),
                    "metrics": {"train/total_loss": 0.5},
                },
                {
                    "step": config.max_steps + 1,
                    "event": "target_evaluation",
                    "time": float(config.max_steps + 1),
                    "metrics": {"target/macro_f1": 0.5},
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(E2RunError) as captured:
        hard_domain_train._validate_finished_metrics(
            metrics_path,
            config=config,
            variant="E2-A",
        )

    assert captured.value.code == "finished_variant_incomplete"


def test_seed_configs_freeze_common_scientific_contract() -> None:
    normalized: list[dict[str, object]] = []
    for path in CONFIGS:
        value = copy.deepcopy(_raw_config(path))
        experiment = value["experiment"]
        tracking = value["tracking"]
        assert isinstance(experiment, dict)
        assert isinstance(tracking, dict)
        seed = experiment["seed"]
        experiment["seed"] = 0
        tracking["run_name"] = "e2-hard-domain-seed"
        tracking["tags"] = [tag for tag in tracking["tags"] if tag != f"seed{seed}"]
        normalized.append(value)

    assert normalized[0] == normalized[1] == normalized[2]


def test_configs_bind_exact_seven_fields_and_four_variants() -> None:
    for path in CONFIGS:
        config = load_config(path, project_root=PROJECT_ROOT)

        assert config.feature_fields == E2_FEATURE_FIELDS
        assert config.physics_feature_columns == E2_FEATURE_FIELDS
        assert config.variants == E2_PINN_VARIANTS
        assert config.panel == "abd_to_c"
        assert config.max_steps == 200
        assert config.batch_size == 128
        assert config.tracking.mode == "online"
        assert config.state_supervised_points == (0,)
        assert config.state_evaluation_points == (0, 1)
        assert config.physics_root.name == "e2-physics-auxiliary-v1"
        assert config.physics_table.name == "e2-physics-auxiliary-v1.parquet"


def test_runner_contains_required_validity_gates() -> None:
    source = (
        PROJECT_ROOT / "src/flow_probe/e2_hard_domain_train.py"
    ).read_text(encoding="utf-8")

    for required_gate in (
        "missing_model_feature_columns",
        "distilbert_classifier_head_detected",
        "permutation_receipts.jsonl",
        "initial_state_sha256",
        "physics/shared_encoder_gradient_norm",
        "physics/state_head_gradient_norm",
        "feature_supervision_binding_sha256",
        "detection_source_binding_sha256",
        "assert_shared_training_budget",
    ):
        assert required_gate in source


def test_output_validation_enumerates_artifacts_without_ignore_rules() -> None:
    """运行目录受 Git 忽略，swanlog 还自带 `*`，枚举必须显式关闭忽略规则。"""
    wrapper = (
        PROJECT_ROOT / "scripts/run_e2_hard_domain.sh"
    ).read_text(encoding="utf-8")
    enumerations = [
        line.strip()
        for line in wrapper.splitlines()
        if "rg --files" in line
    ]

    assert enumerations, "后置校验必须保留制品枚举语句"
    for line in enumerations:
        assert "--no-ignore" in line, line
    assert any("checkpoints" in line for line in enumerations)
    assert any("swanlog" in line for line in enumerations)
