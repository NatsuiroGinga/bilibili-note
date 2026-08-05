import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import flow_probe.train_sft as train_sft_module
from flow_probe.config import ProbeConfig
from flow_probe.train_sft import (
    RestartStateCallback,
    _atomic_write_json,
    _prepare_training_run,
    _run_trainer_with_resume,
    _train_impl,
    build_chat_dataset,
    build_chat_training_records,
    build_lora_config,
    build_lora_config_kwargs,
    build_model_load_kwargs,
    build_model_load_spec,
    build_optimizer_scheduler_kwargs,
    build_qwen_model_and_tokenizer,
    build_quantization_config_kwargs,
    build_sft_config_kwargs,
    build_sft_trainer,
    build_training_binding,
    build_training_settings,
    build_training_tracking_config,
    load_training_records,
    resolve_resume_checkpoint,
    training_binding_sha256,
)

QWEN_TOKENIZER_PATH = Path("/root/autodl-tmp/thesis/models/Qwen3-1.7B")

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


def _legacy_chat_training_record(
    record: dict[str, object],
    tokenizer,
) -> dict[str, str]:
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": record["prompt"]}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    return {
        "prompt": prompt,
        "completion": str(record["completion"]) + tokenizer.eos_token,
    }


def _legacy_chat_dataset(records: list[dict[str, object]], tokenizer):
    from datasets import Dataset

    return Dataset.from_list(
        [_legacy_chat_training_record(record, tokenizer) for record in records]
    )


def _prepare_with_real_trl(
    dataset,
    tokenizer,
    max_length: int,
    output_dir: Path,
):
    from trl import SFTConfig, SFTTrainer

    args = SFTConfig(
        output_dir=str(output_dir),
        max_length=max_length,
        completion_only_loss=True,
        bf16=False,
        fp16=False,
        report_to="none",
        shuffle_dataset=False,
    )
    trainer = object.__new__(SFTTrainer)
    trainer._is_vlm = False
    return SFTTrainer._prepare_dataset(
        trainer,
        dataset,
        tokenizer,
        args,
        False,
        None,
        output_dir.name,
    )


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
    assert settings.attention_backend == "auto"
    assert settings.group_by_length is False


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
        "attention_backend": "auto",
    }


def test_extracted_model_lora_optimizer_and_scheduler_parameters_match_plain_qwen(
    tmp_path: Path,
) -> None:
    probe = probe_config()
    settings = _settings(tmp_path, attention_backend="sdpa")
    compute_dtype = object()
    quantization_config = object()

    assert build_quantization_config_kwargs(compute_dtype) == {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": compute_dtype,
        "bnb_4bit_use_double_quant": True,
    }
    assert build_model_load_kwargs(
        settings,
        quantization_config,
        compute_dtype,
    ) == {
        "quantization_config": quantization_config,
        "dtype": compute_dtype,
        "device_map": "auto",
        "attn_implementation": "sdpa",
    }
    assert build_lora_config_kwargs(probe) == {
        "r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "bias": "none",
        "task_type": "CAUSAL_LM",
        "target_modules": "all-linear",
    }
    optimizer_scheduler = build_optimizer_scheduler_kwargs(settings)
    assert optimizer_scheduler == {
        "learning_rate": 0.0002,
        "optim": "paged_adamw_8bit",
        "lr_scheduler_type": "linear",
        "warmup_ratio": 0.0,
        "warmup_steps": 0,
        "max_grad_norm": 1.0,
    }
    sft_parameters = build_sft_config_kwargs(settings, tracking_enabled=False)
    assert all(sft_parameters[key] == value for key, value in optimizer_scheduler.items())
    assert sft_parameters["max_length"] == 512
    assert sft_parameters["group_by_length"] is False


def test_public_builders_and_train_impl_are_strictly_wired(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peft
    import torch
    import transformers
    import trl

    probe = probe_config()
    settings = _settings(
        tmp_path,
        attention_backend="sdpa",
        group_by_length=True,
    )
    calls: dict[str, object] = {}

    class RecordingTokenizerFactory:
        tokenizer: object

        @classmethod
        def from_pretrained(cls, model_id, **kwargs):
            calls["tokenizer"] = (model_id, kwargs)
            return cls.tokenizer

    class RecordingQuantizationConfig:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            calls["quantization"] = kwargs

    class RecordingModelFactory:
        @classmethod
        def from_pretrained(cls, model_id, **kwargs):
            calls["model"] = (model_id, kwargs)
            return "model-sentinel"

    monkeypatch.setattr(transformers, "AutoTokenizer", RecordingTokenizerFactory)
    monkeypatch.setattr(transformers, "BitsAndBytesConfig", RecordingQuantizationConfig)
    monkeypatch.setattr(transformers, "AutoModelForCausalLM", RecordingModelFactory)
    for pad_token_id, pad_token in ((None, None), (17, "<pad>")):
        tokenizer = SimpleNamespace(
            pad_token_id=pad_token_id,
            pad_token=pad_token,
            eos_token="<eos>",
        )
        RecordingTokenizerFactory.tokenizer = tokenizer
        model, returned_tokenizer = build_qwen_model_and_tokenizer(
            probe,
            settings,
            SimpleNamespace(bfloat16="bf16-sentinel"),
        )

        assert model == "model-sentinel"
        assert returned_tokenizer is tokenizer
        assert tokenizer.pad_token == ("<eos>" if pad_token_id is None else "<pad>")
        assert calls["tokenizer"] == (probe.model_id, {"use_fast": True})
        assert calls["quantization"] == {
            "load_in_4bit": True,
            "bnb_4bit_quant_type": "nf4",
            "bnb_4bit_compute_dtype": "bf16-sentinel",
            "bnb_4bit_use_double_quant": True,
        }
        model_kwargs = calls["model"][1]
        assert model_kwargs["dtype"] == "bf16-sentinel"
        assert model_kwargs["device_map"] == "auto"
        assert model_kwargs["attn_implementation"] == "sdpa"
        assert isinstance(model_kwargs["quantization_config"], RecordingQuantizationConfig)

    class RecordingLoraConfig:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            calls["lora"] = kwargs

    class RecordingSFTConfig:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            calls["sft_config"] = kwargs

    class RecordingSFTTrainer:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs
            calls["sft_trainer"] = kwargs

    monkeypatch.setattr(peft, "LoraConfig", RecordingLoraConfig)
    monkeypatch.setattr(trl, "SFTConfig", RecordingSFTConfig)
    monkeypatch.setattr(trl, "SFTTrainer", RecordingSFTTrainer)
    lora_config = build_lora_config(probe)
    callbacks = [object()]
    trainer = build_sft_trainer(
        probe,
        settings,
        model="model",
        tokenizer="tokenizer",
        train_dataset="train-dataset",
        validation_dataset="validation-dataset",
        tracking_enabled=False,
        callbacks=callbacks,
    )

    assert isinstance(lora_config, RecordingLoraConfig)
    assert calls["lora"] == build_lora_config_kwargs(probe)
    assert calls["sft_config"]["seed"] == probe.seed
    assert calls["sft_config"]["data_seed"] == probe.seed
    assert calls["sft_config"]["optim"] == "paged_adamw_8bit"
    assert calls["sft_config"]["lr_scheduler_type"] == "linear"
    assert calls["sft_config"]["max_grad_norm"] == 1.0
    assert calls["sft_config"]["group_by_length"] is True
    assert trainer.kwargs["model"] == "model"
    assert trainer.kwargs["processing_class"] == "tokenizer"
    assert trainer.kwargs["train_dataset"] == "train-dataset"
    assert trainer.kwargs["eval_dataset"] == "validation-dataset"
    assert isinstance(trainer.kwargs["peft_config"], RecordingLoraConfig)
    assert isinstance(trainer.kwargs["args"], RecordingSFTConfig)
    assert trainer.kwargs["callbacks"] is callbacks

    runtime_calls: list[str] = []
    runtime_tokenizer = SimpleNamespace(
        save_pretrained=lambda path: runtime_calls.append(f"save-tokenizer:{path}")
    )
    runtime_trainer = SimpleNamespace(
        save_model=lambda path: runtime_calls.append(f"save-model:{path}"),
        state=SimpleNamespace(log_history=[], global_step=3),
    )
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "is_bf16_supported", lambda: True)
    monkeypatch.setattr(
        train_sft_module,
        "build_qwen_model_and_tokenizer",
        lambda *args: (runtime_calls.append("model-builder") or "model", runtime_tokenizer),
    )
    monkeypatch.setattr(
        train_sft_module,
        "load_training_records",
        lambda path: runtime_calls.append(f"load:{path.name}")
        or [{"sample_id": path.name, "prompt": "p", "completion": "c"}],
    )
    monkeypatch.setattr(
        train_sft_module,
        "build_chat_dataset",
        lambda records, tokenizer: runtime_calls.append(
            f"chat-dataset:{records[0]['sample_id']}"
        )
        or records,
    )

    def record_trainer_builder(*args, **kwargs):
        runtime_calls.append("trainer-builder")
        assert kwargs["train_dataset"][0]["sample_id"] == settings.train_file.name
        assert kwargs["validation_dataset"][0]["sample_id"] == settings.validation_file.name
        return runtime_trainer

    monkeypatch.setattr(train_sft_module, "build_sft_trainer", record_trainer_builder)
    monkeypatch.setattr(
        train_sft_module,
        "_run_trainer_with_resume",
        lambda *args: SimpleNamespace(metrics={}),
    )
    monkeypatch.setattr(train_sft_module, "_atomic_write_json", lambda *args: None)
    state_callback = SimpleNamespace(mark_finished=lambda step: runtime_calls.append(f"step:{step}"))
    prepared = SimpleNamespace(resume_checkpoint=None, binding_sha256="a" * 64)

    _train_impl(
        probe,
        settings,
        tracking_enabled=False,
        prepared=prepared,
        state_callback=state_callback,
    )

    assert runtime_calls[:6] == [
        "model-builder",
        f"load:{settings.train_file.name}",
        f"chat-dataset:{settings.train_file.name}",
        f"load:{settings.validation_file.name}",
        f"chat-dataset:{settings.validation_file.name}",
        "trainer-builder",
    ]


def test_real_trl_qwen_preprocessing_matches_legacy_and_isolates_sample_id(
    tmp_path: Path,
) -> None:
    from transformers import AutoTokenizer
    from trl.trainer.sft_trainer import DataCollatorForLanguageModeling

    assert QWEN_TOKENIZER_PATH.is_dir()
    tokenizer = AutoTokenizer.from_pretrained(
        QWEN_TOKENIZER_PATH,
        use_fast=True,
        local_files_only=True,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    records = [
        {
            "sample_id": "sample-short",
            "prompt": "flow duration=1.0 packets=4",
            "completion": '{"label":"benign"}',
        },
        {
            "sample_id": "sample-truncated",
            "prompt": " ".join(["flow duration=1.0 packets=4"] * 8),
            "completion": " ".join(['{"label":"malicious"}'] * 32),
        },
    ]
    legacy_dataset = _legacy_chat_dataset(records, tokenizer)
    extracted_dataset = build_chat_dataset(records, tokenizer)
    long_prompt_ids = tokenizer(text=extracted_dataset[1]["prompt"])["input_ids"]
    long_full_ids = tokenizer(
        text=extracted_dataset[1]["prompt"] + extracted_dataset[1]["completion"]
    )["input_ids"]
    short_full_ids = tokenizer(
        text=extracted_dataset[0]["prompt"] + extracted_dataset[0]["completion"]
    )["input_ids"]
    max_length = len(long_prompt_ids) + 4

    assert len(short_full_ids) < max_length
    assert max_length < len(long_full_ids)
    legacy_processed = _prepare_with_real_trl(
        legacy_dataset,
        tokenizer,
        max_length,
        tmp_path / "legacy",
    )
    extracted_processed = _prepare_with_real_trl(
        extracted_dataset,
        tokenizer,
        max_length,
        tmp_path / "extracted",
    )

    assert extracted_dataset["sample_id"] == [record["sample_id"] for record in records]
    assert extracted_processed["sample_id"] == [record["sample_id"] for record in records]
    for index in range(len(records)):
        assert extracted_processed[index]["input_ids"] == legacy_processed[index]["input_ids"]
        assert extracted_processed[index]["completion_mask"] == legacy_processed[index][
            "completion_mask"
        ]
    assert len(extracted_processed[0]["input_ids"]) == len(short_full_ids)
    assert len(extracted_processed[1]["input_ids"]) == max_length
    assert sum(extracted_processed[1]["completion_mask"]) == 4

    collator = DataCollatorForLanguageModeling(
        pad_token_id=tokenizer.pad_token_id,
        completion_only_loss=True,
    )
    legacy_batch = collator([legacy_processed[index] for index in range(len(records))])
    extracted_batch = collator(
        [extracted_processed[index] for index in range(len(records))]
    )
    assert extracted_batch["input_ids"].equal(legacy_batch["input_ids"])
    assert extracted_batch["labels"].equal(legacy_batch["labels"])
    assert "sample_id" not in extracted_batch
    model_keys: set[str] = set()

    def strict_model(**kwargs):
        model_keys.update(kwargs)

    strict_model(**extracted_batch)
    assert model_keys == {"attention_mask", "input_ids", "labels"}


@pytest.mark.parametrize("attention_backend", ["flash", "", 1, None])
def test_training_settings_reject_invalid_attention_backend(
    tmp_path: Path,
    attention_backend: object,
) -> None:
    with pytest.raises(ValueError, match="attention_backend 只允许"):
        _settings(tmp_path, attention_backend=attention_backend)


@pytest.mark.parametrize("group_by_length", [1, "true", None])
def test_training_settings_reject_invalid_group_by_length(
    tmp_path: Path,
    group_by_length: object,
) -> None:
    with pytest.raises(ValueError, match="group_by_length 必须是布尔值"):
        _settings(tmp_path, group_by_length=group_by_length)


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
    assert config["attention_backend"] == "auto"
    assert config["group_by_length"] is False


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
        build_training_binding(
            probe,
            replace(settings, attention_backend="sdpa"),
            model_path,
        ),
        build_training_binding(
            probe,
            replace(settings, group_by_length=True),
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
    assert config["group_by_length"] is False


def test_training_runtime_acceleration_does_not_change_effective_batch(
    tmp_path: Path,
) -> None:
    settings = _settings(
        tmp_path,
        attention_backend="flash_attention_2",
        group_by_length=True,
    )

    assert settings.effective_batch_size == 64
    assert build_sft_config_kwargs(settings, tracking_enabled=False)["group_by_length"] is True
    assert build_model_load_spec(probe_config(), settings)["attention_backend"] == (
        "flash_attention_2"
    )
