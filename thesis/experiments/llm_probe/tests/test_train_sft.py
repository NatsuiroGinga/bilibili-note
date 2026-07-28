import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from flow_probe.config import ProbeConfig
from flow_probe.train_sft import (
    RestartStateCallback,
    _atomic_write_json,
    _prepare_training_run,
    _run_trainer_with_resume,
    build_model_load_spec,
    build_sft_config_kwargs,
    build_training_binding,
    build_training_settings,
    build_training_tracking_config,
    resolve_resume_checkpoint,
    training_binding_sha256,
)

RUN_STATE_FIELDS = {
    "binding_sha256",
    "current_step",
    "failure",
    "latest_checkpoint",
    "run_id",
    "schema_version",
    "started_at",
    "status",
    "swanlab_run_id",
    "updated_at",
}


def probe_config() -> ProbeConfig:
    return ProbeConfig.from_mapping(
        {
            "model_id": "Qwen/Qwen3-1.7B",
            "feature_view": "canonical_core_v1",
            "seed": 42,
            "max_input_length": 512,
            "max_new_tokens": 16,
            "lora_rank": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.05,
        }
    )


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _training_mapping(tmp_path: Path, **overrides: object) -> dict[str, object]:
    train_file = tmp_path / "data" / "train.jsonl"
    validation_file = tmp_path / "data" / "validation.jsonl"
    if not train_file.exists():
        _write_jsonl(train_file, [{"prompt": "train", "completion": "malicious"}])
    if not validation_file.exists():
        _write_jsonl(validation_file, [{"prompt": "valid", "completion": "benign"}])
    data: dict[str, object] = {
        "train_file": str(train_file),
        "validation_file": str(validation_file),
        "output_dir": str(tmp_path / "run"),
        "learning_rate": 0.0002,
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 16,
        "num_train_epochs": 3,
    }
    data.update(overrides)
    return data


def _settings(tmp_path: Path, **overrides: object):
    return build_training_settings(probe_config(), _training_mapping(tmp_path, **overrides))


def _run_state(binding: dict[str, object], status: str = "interrupted") -> dict[str, object]:
    return {
        "schema_version": "qwen_sft_run_state_v1",
        "run_id": "run-fixture",
        "status": status,
        "current_step": 20,
        "latest_checkpoint": None,
        "binding_sha256": training_binding_sha256(binding),
        "swanlab_run_id": None,
        "started_at": "2026-07-28T00:00:00Z",
        "updated_at": "2026-07-28T00:00:01Z",
        "failure": None,
    }


def _write_run_metadata(
    output_dir: Path,
    binding: dict[str, object],
    *,
    status: str = "interrupted",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(output_dir / "training_binding.json", binding)
    _atomic_write_json(output_dir / "run_state.json", _run_state(binding, status))


def _write_checkpoint(
    output_dir: Path,
    step: int,
    *,
    missing: frozenset[str] = frozenset(),
    model_filename: str = "adapter_model.safetensors",
) -> Path:
    checkpoint = output_dir / f"checkpoint-{step}"
    checkpoint.mkdir(parents=True)
    filenames = {
        "trainer_state.json",
        "optimizer.pt",
        "scheduler.pt",
        "rng_state.pth",
        model_filename,
    }
    for filename in sorted(filenames - missing):
        (checkpoint / filename).write_text(filename, encoding="utf-8")
    return checkpoint


def test_training_settings_preserve_effective_batch_and_probe_limits(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    assert settings.effective_batch_size == 64
    assert settings.max_length == 512
    assert settings.max_new_tokens == 16
    assert settings.completion_only_loss is True
    assert settings.save_steps == 20
    assert settings.resume_from_checkpoint == "auto"


@pytest.mark.parametrize("save_steps", [0, 21, 1.5, "20", True])
def test_training_settings_reject_invalid_save_steps(
    tmp_path: Path,
    save_steps: object,
) -> None:
    with pytest.raises(ValueError, match="save_steps 必须是 1 到 20 的整数"):
        _settings(tmp_path, save_steps=save_steps)


@pytest.mark.parametrize("resume_policy", ["latest", "", 1, None])
def test_training_settings_reject_invalid_resume_policy(
    tmp_path: Path,
    resume_policy: object,
) -> None:
    with pytest.raises(ValueError, match="resume_from_checkpoint 只允许 auto 或 never"):
        _settings(tmp_path, resume_from_checkpoint=resume_policy)


def test_model_load_spec_uses_nf4_bf16_and_all_linear_lora() -> None:
    spec = build_model_load_spec(probe_config())

    assert spec == {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": "bfloat16",
        "bnb_4bit_use_double_quant": True,
        "lora_rank": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": "all-linear",
        "enable_thinking": False,
    }


def test_training_tracking_config_contains_restart_fields(tmp_path: Path) -> None:
    probe = probe_config()
    settings = _settings(
        tmp_path,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        num_train_epochs=1,
        max_steps=50,
        save_steps=10,
        resume_from_checkpoint="never",
    )

    config = build_training_tracking_config(probe, settings)

    assert config["model_id"] == "Qwen/Qwen3-1.7B"
    assert config["train_file"] == str(settings.train_file)
    assert config["seed"] == 42
    assert config["lora_rank"] == 16
    assert config["effective_batch_size"] == 4
    assert config["max_steps"] == 50
    assert config["save_steps"] == 10
    assert config["resume_from_checkpoint"] == "never"


def test_training_binding_is_stable_and_changes_with_scientific_inputs(
    tmp_path: Path,
) -> None:
    probe = probe_config()
    settings = _settings(tmp_path)
    model_path = tmp_path / "models" / "Qwen3-1.7B"
    baseline = build_training_binding(probe, settings, model_path)

    assert build_training_binding(probe, settings, model_path) == baseline

    settings.train_file.write_text('{"prompt":"changed"}\n', encoding="utf-8")
    assert build_training_binding(probe, settings, model_path) != baseline
    _write_jsonl(settings.train_file, [{"prompt": "train", "completion": "malicious"}])

    settings.validation_file.write_text('{"prompt":"changed"}\n', encoding="utf-8")
    assert build_training_binding(probe, settings, model_path) != baseline
    _write_jsonl(settings.validation_file, [{"prompt": "valid", "completion": "benign"}])

    variants = (
        build_training_binding(replace(probe, seed=43), settings, model_path),
        build_training_binding(replace(probe, lora_rank=8), settings, model_path),
        build_training_binding(probe, replace(settings, learning_rate=0.0001), model_path),
        build_training_binding(
            probe,
            replace(settings, per_device_train_batch_size=2),
            model_path,
        ),
        build_training_binding(probe, settings, tmp_path / "models" / "other"),
    )
    assert all(binding != baseline for binding in variants)


def test_resolve_resume_checkpoint_uses_latest_complete_checkpoint(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    binding = build_training_binding(probe_config(), settings, tmp_path / "model")
    _write_run_metadata(settings.output_dir, binding)
    checkpoint_20 = _write_checkpoint(settings.output_dir, 20)
    _write_checkpoint(
        settings.output_dir,
        40,
        missing=frozenset({"scheduler.pt"}),
        model_filename="model.safetensors",
    )

    resolved = resolve_resume_checkpoint(settings.output_dir, binding, "auto")

    assert resolved == checkpoint_20


def test_resolve_resume_checkpoint_accepts_full_model_weights(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    binding = build_training_binding(probe_config(), settings, tmp_path / "model")
    _write_run_metadata(settings.output_dir, binding)
    checkpoint = _write_checkpoint(
        settings.output_dir,
        20,
        model_filename="model.safetensors",
    )

    assert resolve_resume_checkpoint(settings.output_dir, binding, "auto") == checkpoint


def test_resolve_resume_checkpoint_rejects_binding_mismatch(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    binding = build_training_binding(probe_config(), settings, tmp_path / "model")
    _write_run_metadata(settings.output_dir, binding)
    _write_checkpoint(settings.output_dir, 20)
    mismatched = {**binding, "seed": 43}

    with pytest.raises(ValueError, match="seed"):
        resolve_resume_checkpoint(settings.output_dir, mismatched, "auto")


def test_resolve_resume_checkpoint_returns_none_when_resume_is_forbidden(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    binding = build_training_binding(probe_config(), settings, tmp_path / "model")
    _write_run_metadata(settings.output_dir, binding, status="finished")
    _write_checkpoint(settings.output_dir, 20)

    assert resolve_resume_checkpoint(settings.output_dir, binding, "auto") is None
    assert resolve_resume_checkpoint(settings.output_dir, binding, "never") is None
    assert resolve_resume_checkpoint(tmp_path / "missing", binding, "auto") is None


def test_resolve_resume_checkpoint_returns_none_without_complete_checkpoint(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    binding = build_training_binding(probe_config(), settings, tmp_path / "model")
    _write_run_metadata(settings.output_dir, binding)
    _write_checkpoint(
        settings.output_dir,
        20,
        missing=frozenset({"optimizer.pt", "rng_state.pth"}),
    )

    assert resolve_resume_checkpoint(settings.output_dir, binding, "auto") is None


def test_prepare_training_run_writes_binding_snapshot_and_prepared_state(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)

    prepared = _prepare_training_run(probe_config(), settings, tmp_path / "model")

    assert prepared.resume_checkpoint is None
    assert json.loads((settings.output_dir / "training_binding.json").read_text()) == dict(
        prepared.binding
    )
    assert (settings.output_dir / "training_config.json").is_file()
    state = json.loads((settings.output_dir / "run_state.json").read_text())
    assert set(state) == RUN_STATE_FIELDS
    assert state["status"] == "prepared"
    assert state["current_step"] == 0
    assert state["binding_sha256"] == training_binding_sha256(prepared.binding)


def test_prepare_training_run_rejects_finished_and_mismatched_runs_before_training(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    binding = build_training_binding(probe_config(), settings, tmp_path / "model")
    _write_run_metadata(settings.output_dir, binding, status="finished")

    with pytest.raises(ValueError, match="finished"):
        _prepare_training_run(probe_config(), settings, tmp_path / "model")

    state = _run_state(binding)
    _atomic_write_json(settings.output_dir / "run_state.json", state)
    with pytest.raises(ValueError, match="seed"):
        _prepare_training_run(replace(probe_config(), seed=43), settings, tmp_path / "model")


def test_prepare_training_run_resumes_from_complete_checkpoint(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    binding = build_training_binding(probe_config(), settings, tmp_path / "model")
    _write_run_metadata(settings.output_dir, binding)
    checkpoint = _write_checkpoint(settings.output_dir, 20)

    prepared = _prepare_training_run(probe_config(), settings, tmp_path / "model")

    assert prepared.resume_checkpoint == checkpoint
    state = json.loads((settings.output_dir / "run_state.json").read_text())
    assert state["status"] == "prepared"
    assert state["current_step"] == 20
    assert state["latest_checkpoint"] == str(checkpoint)


def test_restart_state_callback_writes_running_save_and_finished_transitions(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "run" / "run_state.json"
    initial = _run_state({"binding": "fixture"}, status="prepared")
    initial["current_step"] = 0
    initial["binding_sha256"] = "a" * 64
    callback = RestartStateCallback(state_path, initial)
    args = SimpleNamespace(output_dir=str(tmp_path / "run"))
    trainer_state = SimpleNamespace(global_step=0)
    control = SimpleNamespace()

    assert callback.on_train_begin(args, trainer_state, control) is control
    assert json.loads(state_path.read_text())["status"] == "running"

    trainer_state.global_step = 20
    assert callback.on_save(args, trainer_state, control) is control
    saved = json.loads(state_path.read_text())
    assert saved["status"] == "running"
    assert saved["current_step"] == 20
    assert saved["latest_checkpoint"] == str(tmp_path / "run" / "checkpoint-20")

    assert callback.on_train_end(args, trainer_state, control) is control
    finished = json.loads(state_path.read_text())
    assert set(finished) == RUN_STATE_FIELDS
    assert finished["status"] == "finished"
    assert finished["failure"] is None


class _FakeTrainer:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.resume_arguments: list[str | None] = []

    def train(self, *, resume_from_checkpoint: str | None):
        self.resume_arguments.append(resume_from_checkpoint)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(metrics={})


def test_run_trainer_passes_native_resume_argument(tmp_path: Path) -> None:
    state_path = tmp_path / "run_state.json"
    initial = _run_state({"binding": "fixture"}, status="prepared")
    initial["binding_sha256"] = "b" * 64
    callback = RestartStateCallback(state_path, initial)
    fresh = _FakeTrainer()
    resumed = _FakeTrainer()
    checkpoint = tmp_path / "checkpoint-40"

    _run_trainer_with_resume(fresh, None, callback)
    _run_trainer_with_resume(resumed, checkpoint, callback)

    assert fresh.resume_arguments == [None]
    assert resumed.resume_arguments == [str(checkpoint)]


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [(KeyboardInterrupt(), "interrupted"), (RuntimeError("boom"), "failed")],
)
def test_run_trainer_records_interruption_and_failure(
    tmp_path: Path,
    error: BaseException,
    expected_status: str,
) -> None:
    state_path = tmp_path / expected_status / "run_state.json"
    initial = _run_state({"binding": expected_status}, status="prepared")
    initial["binding_sha256"] = "c" * 64
    callback = RestartStateCallback(state_path, initial)

    with pytest.raises(type(error)):
        _run_trainer_with_resume(_FakeTrainer(error), None, callback)

    state = json.loads(state_path.read_text())
    assert state["status"] == expected_status
    assert type(error).__name__ in state["failure"]


def test_sft_config_uses_bounded_step_checkpoints(tmp_path: Path) -> None:
    settings = _settings(tmp_path, save_steps=10)

    config = build_sft_config_kwargs(settings, tracking_enabled=False)

    assert config["save_strategy"] == "steps"
    assert config["save_steps"] == 10
    assert config["save_total_limit"] == 3
    assert config["save_only_model"] is False
    assert config["logging_steps"] == 1
    assert config["report_to"] == "none"
