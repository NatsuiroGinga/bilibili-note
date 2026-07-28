from pathlib import Path

import pytest

from flow_probe.representation_train import (
    RepresentationTrainingError,
    _build_settings,
    _tracking_settings,
)


def _raw_config():
    return {
        "training": {
            "generation_train_file": "gen-train.jsonl",
            "generation_validation_file": "gen-validation.jsonl",
            "physics_train_file": "physics-train.jsonl",
            "physics_validation_file": "physics-validation.jsonl",
            "physics_test_file": "physics-test.jsonl",
            "learning_rate": 0.0002,
            "generation_batch_size": 4,
            "gradient_accumulation_steps": 4,
            "physics_batch_size": 4,
            "validation_batch_size": 8,
            "state_supervision_mode": "anchor0_plus_one",
            "lambda_state": 1.0,
            "lambda_physics": 0.01,
            "max_grad_norm": 1.0,
        }
    }


@pytest.mark.parametrize(("variant", "max_steps"), [("B0", 2), ("B1", 50)])
def test_settings_accept_only_frozen_probe_budgets(variant, max_steps):
    settings = _build_settings(
        _raw_config(),
        variant=variant,
        output_dir=Path(f"runs/representation-coupling/{variant.lower()}"),
        max_steps=max_steps,
        validation_limit=8,
    )

    assert settings.variant == variant
    assert settings.max_steps == max_steps
    assert settings.effective_generation_batch_size == 16
    assert settings.state_supervision_mode == "anchor0_plus_one"


def test_settings_reject_202_steps():
    with pytest.raises(RepresentationTrainingError, match="只允许 2 步冒烟或 50 步探索"):
        _build_settings(
            _raw_config(),
            variant="B0",
            output_dir=Path("runs/representation-coupling/b0"),
            max_steps=202,
            validation_limit=None,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("state_supervision_mode", "anchor0_only", "anchor0_plus_one"),
        ("lambda_state", 0.5, "状态损失权重"),
        ("lambda_physics", 0.1, "物理损失权重"),
    ],
)
def test_settings_reject_scope_expansion(field, value, message):
    raw = _raw_config()
    raw["training"][field] = value

    with pytest.raises(RepresentationTrainingError, match=message):
        _build_settings(
            raw,
            variant="B1",
            output_dir=Path("runs/representation-coupling/b1"),
            max_steps=2,
            validation_limit=8,
        )


def test_tracking_tags_satisfy_swanlab_length_contract_without_duplicates():
    raw = {
        "tracking": {
            "project": "malicious-traffic-llm",
            "workspace": "mortiswang",
            "run_name": "unused",
            "description": "unused",
            "mode": "online",
            "tags": ["llm-probe", "repr-coupling"],
        }
    }

    settings = _tracking_settings(raw, "b0-smoke", "B0")

    assert all(len(tag) <= 20 for tag in settings.tags)
    assert settings.tags.count("repr-coupling") == 1
