from flow_probe.config import ProbeConfig
from flow_probe.train_sft import (
    build_model_load_spec,
    build_training_settings,
    build_training_tracking_config,
)


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


def test_training_settings_preserve_effective_batch_and_probe_limits() -> None:
    settings = build_training_settings(
        probe_config(),
        {
            "train_file": "data/train.jsonl",
            "validation_file": "data/validation.jsonl",
            "output_dir": "runs/smoke",
            "learning_rate": 0.0002,
            "per_device_train_batch_size": 4,
            "gradient_accumulation_steps": 16,
            "num_train_epochs": 3,
        },
    )

    assert settings.effective_batch_size == 64
    assert settings.max_length == 512
    assert settings.max_new_tokens == 16
    assert settings.completion_only_loss is True


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


def test_training_tracking_config_contains_reproducibility_fields() -> None:
    probe = probe_config()
    settings = build_training_settings(
        probe,
        {
            "train_file": "data/train.jsonl",
            "validation_file": "data/validation.jsonl",
            "output_dir": "runs/pilot",
            "learning_rate": 0.0002,
            "per_device_train_batch_size": 2,
            "gradient_accumulation_steps": 2,
            "num_train_epochs": 1,
            "max_steps": 50,
        },
    )

    config = build_training_tracking_config(probe, settings)

    assert config["model_id"] == "Qwen/Qwen3-1.7B"
    assert config["train_file"] == "data/train.jsonl"
    assert config["seed"] == 42
    assert config["lora_rank"] == 16
    assert config["effective_batch_size"] == 4
    assert config["max_steps"] == 50
