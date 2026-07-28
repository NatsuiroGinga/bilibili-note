from pathlib import Path

import yaml

from flow_probe.config import ProbeConfig
from flow_probe.tracking import TrackingSettings
from flow_probe.train_sft import build_training_settings


def test_hierarchical_qwen_pilot_config_fixes_data_budget_and_tracking() -> None:
    config_path = Path("configs/genis_hierarchical_v2_qwen3_1_7b_seed42_pilot.yaml")
    assert config_path.is_file()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    probe = ProbeConfig.from_mapping(raw["probe"])
    training = build_training_settings(probe, raw["training"])
    tracking = TrackingSettings.from_mapping(raw["tracking"])

    assert probe.model_id == "Qwen/Qwen3-1.7B"
    assert probe.seed == 42
    assert training.train_file == Path(
        "runs/data-bundled/genis-hierarchical-v2-multitask-seed42/train.jsonl"
    )
    assert training.validation_file == Path(
        "runs/data-bundled/genis-hierarchical-v2-multitask-seed42/validation.jsonl"
    )
    assert training.max_steps == 200
    assert training.effective_batch_size == 16
    assert tracking.project == "malicious-traffic-llm"
    assert tracking.workspace == "mortiswang"
    assert tracking.mode == "online"
    assert "hierarchical-v2" in tracking.tags
