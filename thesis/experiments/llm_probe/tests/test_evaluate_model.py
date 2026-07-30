import pytest

from flow_probe.config import ProbeConfig
from flow_probe.evaluate_model import (
    GeneratedResult,
    build_evaluation_tracking_config,
    evaluation_record_contract,
    format_generation_prompt,
    summarize_generated_results,
    validate_evaluation_records,
)


class FakeTokenizer:
    def __init__(self) -> None:
        self.arguments = None

    def apply_chat_template(self, messages, **kwargs):
        self.arguments = (messages, kwargs)
        return "CHAT_PROMPT"


def test_generation_prompt_explicitly_disables_thinking() -> None:
    tokenizer = FakeTokenizer()

    result = format_generation_prompt(tokenizer, "流量提示")

    assert result == "CHAT_PROMPT"
    messages, kwargs = tokenizer.arguments
    assert messages == [{"role": "user", "content": "流量提示"}]
    assert kwargs["enable_thinking"] is False
    assert kwargs["add_generation_prompt"] is True


def test_generated_summary_combines_strict_metrics_and_latency() -> None:
    records = [
        {"sample_id": "1", "binary_label": "benign"},
        {"sample_id": "2", "binary_label": "malicious"},
    ]
    generated = [
        GeneratedResult('{"label":"benign"}', 20, 4, 10.0),
        GeneratedResult('```json\n{"label":"malicious"}\n```', 20, 8, 30.0),
    ]

    summary, rows = summarize_generated_results(records, generated)

    assert summary["json_valid_rate"] == pytest.approx(0.5)
    assert summary["macro_f1"] == pytest.approx(1 / 3)
    assert summary["latency_p50_ms"] == pytest.approx(20.0)
    assert summary["latency_p95_ms"] == pytest.approx(29.0)
    assert summary["input_tokens"] == 40
    assert summary["generated_tokens"] == 12
    assert rows[1]["is_valid"] is False


def test_generated_summary_supports_shared_binary_label_contract() -> None:
    records = [
        {
            "sample_id": "shared-1",
            "prompt": "只输出 binary_label",
            "completion": '{"binary_label":"malicious"}',
        }
    ]
    generated = [GeneratedResult('{"binary_label":"malicious"}', 20, 5, 10.0)]

    summary, rows = summarize_generated_results(records, generated)

    assert summary["json_valid_rate"] == pytest.approx(1.0)
    assert rows[0]["true_label"] == "malicious"
    assert rows[0]["expected_output_key"] == "binary_label"


def test_evaluation_record_gate_rejects_unknown_completion_key() -> None:
    records = [{"prompt": "流量提示", "completion": '{"class":"malicious"}'}]

    with pytest.raises(ValueError, match="第 1 条测试记录合同非法"):
        validate_evaluation_records(records)


def test_evaluation_record_contract_rejects_conflicting_labels() -> None:
    record = {
        "binary_label": "benign",
        "completion": '{"binary_label":"malicious"}',
    }

    with pytest.raises(ValueError, match="标签不一致"):
        evaluation_record_contract(record)


def test_evaluation_tracking_config_records_adapter_state() -> None:
    probe = ProbeConfig.from_mapping(
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

    config = build_evaluation_tracking_config(
        probe,
        test_file="data/test.jsonl",
        adapter_path="runs/pilot/final_adapter",
    )

    assert config["model_id"] == "Qwen/Qwen3-1.7B"
    assert config["test_file"] == "data/test.jsonl"
    assert config["adapter_path"] == "runs/pilot/final_adapter"
    assert config["max_new_tokens"] == 16
