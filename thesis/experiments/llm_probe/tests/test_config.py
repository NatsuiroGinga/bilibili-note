import pytest

from flow_probe.config import ConfigError, ProbeConfig, override_model_id


def valid_mapping() -> dict[str, object]:
    return {
        "model_id": "Qwen/Qwen3-1.7B",
        "feature_view": "canonical_core_v1",
        "seed": 42,
        "max_input_length": 512,
        "max_new_tokens": 16,
        "lora_rank": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
    }


def test_config_accepts_probe_defaults() -> None:
    config = ProbeConfig.from_mapping(valid_mapping())

    assert config.model_id == "Qwen/Qwen3-1.7B"
    assert config.feature_view == "canonical_core_v1"
    assert config.seed == 42


def test_model_id_override_preserves_experiment_parameters() -> None:
    config = ProbeConfig.from_mapping(valid_mapping())

    overridden = override_model_id(config, "/root/models/Qwen3-1.7B")

    assert overridden.model_id == "/root/models/Qwen3-1.7B"
    assert overridden.seed == config.seed
    assert overridden.max_input_length == config.max_input_length
    assert overridden.lora_rank == config.lora_rank
    assert config.model_id == "Qwen/Qwen3-1.7B"


def test_model_id_override_rejects_empty_path() -> None:
    config = ProbeConfig.from_mapping(valid_mapping())

    with pytest.raises(ConfigError, match="model_id"):
        override_model_id(config, "  ")


@pytest.mark.parametrize("feature_view", ["", "dataset_name", "unknown"])
def test_config_rejects_unknown_feature_view(feature_view: str) -> None:
    data = valid_mapping()
    data["feature_view"] = feature_view

    with pytest.raises(ConfigError, match="字段视图"):
        ProbeConfig.from_mapping(data)


@pytest.mark.parametrize("field", ["max_input_length", "max_new_tokens", "lora_rank"])
def test_config_rejects_non_positive_integer(field: str) -> None:
    data = valid_mapping()
    data[field] = 0

    with pytest.raises(ConfigError, match=field):
        ProbeConfig.from_mapping(data)
