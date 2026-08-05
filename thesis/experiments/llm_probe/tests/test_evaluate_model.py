import json
from pathlib import Path

import pytest

import flow_probe.evaluate_model as evaluate_model_module
from flow_probe.config import ProbeConfig
from flow_probe.evaluate_model import (
    EvaluationJournal,
    EvaluationSettings,
    GeneratedResult,
    _generate_batch,
    build_evaluation_binding,
    build_evaluation_progress_metrics,
    build_evaluation_settings,
    build_evaluation_tracking_config,
    evaluation_record_contract,
    evaluation_tracking_artifact_dir,
    format_generation_prompt,
    plan_length_bucketed_batches,
    summarize_generated_results,
    validate_evaluation_records,
)


class FakeTokenizer:
    def __init__(self) -> None:
        self.arguments = None

    def apply_chat_template(self, messages, **kwargs):
        self.arguments = (messages, kwargs)
        return "CHAT_PROMPT"


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


def _write_records(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _prediction_row(index: int, sample_id: str, label: str) -> dict[str, object]:
    return {
        "record_index": index,
        "sample_id": sample_id,
        "true_label": label,
        "generated_text": json.dumps({"label": label}),
        "parsed_label": label,
        "is_valid": True,
        "parse_error": None,
        "expected_output_key": "label",
        "input_tokens": 10,
        "generated_tokens": 2,
        "latency_ms": 5.0,
    }


def _journal_row(
    index: int,
    sample_id: str,
    label: str,
    *,
    batch_number: int,
    batch_size: int,
) -> dict[str, object]:
    row = _prediction_row(index, sample_id, label)
    row.update(
        {
            "_journal_batch": batch_number,
            "_journal_batch_size": batch_size,
            "_journal_batch_elapsed_seconds": 0.1,
            "_journal_batch_peak_gpu_memory_bytes": 1024,
        }
    )
    return row


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


def test_evaluation_settings_preserve_single_sample_defaults() -> None:
    settings = build_evaluation_settings({})

    assert settings == EvaluationSettings(
        batch_size=1,
        length_bucket=False,
        flush_every_batches=1,
        resume=False,
        attention_backend="auto",
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("batch_size", 0, "batch_size 必须是正整数"),
        ("batch_size", True, "batch_size 必须是正整数"),
        ("flush_every_batches", "2", "flush_every_batches 必须是正整数"),
        ("length_bucket", 1, "length_bucket 必须是布尔值"),
        ("resume", "true", "resume 必须是布尔值"),
        ("attention_backend", "flash", "attention_backend 只允许"),
    ],
)
def test_evaluation_settings_reject_invalid_runtime_values(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_evaluation_settings({field: value})


def test_length_bucketed_batches_are_deterministic_and_exact() -> None:
    lengths = [9, 1, 5, 1, 8]

    assert plan_length_bucketed_batches(lengths, 2, enabled=False) == (
        (0, 1),
        (2, 3),
        (4,),
    )
    bucketed = plan_length_bucketed_batches(lengths, 2, enabled=True)

    assert bucketed == ((1, 3), (2, 4), (0,))
    assert sorted(index for batch in bucketed for index in batch) == list(range(len(lengths)))


def test_evaluation_journal_resumes_and_publishes_original_order(tmp_path: Path) -> None:
    records = [
        {"sample_id": "s0", "prompt": "p0", "completion": '{"label":"benign"}'},
        {"sample_id": "s1", "prompt": "p1", "completion": '{"label":"malicious"}'},
        {"sample_id": "s2", "prompt": "p2", "completion": '{"label":"benign"}'},
    ]
    test_file = tmp_path / "test.jsonl"
    _write_records(test_file, records)
    settings = EvaluationSettings(batch_size=2, resume=True)
    binding = build_evaluation_binding(
        probe_config(),
        settings,
        test_file,
        records,
        adapter_path=None,
    )
    output_dir = tmp_path / "run"
    journal = EvaluationJournal(output_dir, binding, records, resume=True)

    progress = journal.append_batch(
        [_prediction_row(2, "s2", "benign"), _prediction_row(0, "s0", "benign")],
        batch_elapsed_seconds=0.2,
        batch_peak_gpu_memory_bytes=4 * 1024 * 1024,
    )

    assert journal.pending_indices == (1,)
    assert progress["completed_samples"] == 2
    assert progress["total_samples"] == 3
    assert progress["completed_batches"] == 1
    assert progress["total_batches"] == 2
    assert progress["samples_per_second"] == pytest.approx(10.0)
    assert progress["elapsed_seconds"] == pytest.approx(0.2)
    assert progress["eta_seconds"] == pytest.approx(0.1)
    assert progress["gpu_peak_mib"] == pytest.approx(4.0)
    partial = [
        json.loads(line)
        for line in (output_dir / "predictions.partial.jsonl").read_text().splitlines()
    ]
    assert [row["sample_id"] for row in partial] == ["s2", "s0"]

    (output_dir / "evaluation_progress.json").write_text(
        '{"completed_samples":999}\n', encoding="utf-8"
    )

    resumed = EvaluationJournal(output_dir, binding, records, resume=True)
    assert resumed.pending_indices == (1,)
    restored_progress = json.loads(
        (output_dir / "evaluation_progress.json").read_text(encoding="utf-8")
    )
    assert restored_progress["completed_samples"] == 2
    assert restored_progress["completed_batches"] == 1
    resumed.append_batch(
        [_prediction_row(1, "s1", "malicious")],
        batch_elapsed_seconds=0.1,
        batch_peak_gpu_memory_bytes=2 * 1024 * 1024,
    )
    ordered, summary = resumed.finalize(lambda rows: {"row_count": len(rows)})

    assert [row["sample_id"] for row in ordered] == ["s0", "s1", "s2"]
    assert all("record_index" not in row for row in ordered)
    assert summary == {"row_count": 3}
    assert json.loads((output_dir / "evaluation_summary.json").read_text(encoding="utf-8")) == {
        "row_count": 3
    }
    assert (
        json.loads((output_dir / "evaluation_progress.json").read_text(encoding="utf-8"))["status"]
        == "finished"
    )
    final_rows = [
        json.loads(line) for line in (output_dir / "predictions.jsonl").read_text().splitlines()
    ]
    assert final_rows == ordered


def test_evaluation_journal_rejects_binding_mismatch_and_duplicate_rows(
    tmp_path: Path,
) -> None:
    records = [
        {"sample_id": "s0", "prompt": "p0", "completion": '{"label":"benign"}'},
        {"sample_id": "s1", "prompt": "p1", "completion": '{"label":"malicious"}'},
    ]
    test_file = tmp_path / "test.jsonl"
    _write_records(test_file, records)
    settings = EvaluationSettings(batch_size=1, resume=True)
    binding = build_evaluation_binding(
        probe_config(), settings, test_file, records, adapter_path=None
    )
    output_dir = tmp_path / "run"
    journal = EvaluationJournal(output_dir, binding, records, resume=True)
    journal.append_batch(
        [_prediction_row(0, "s0", "benign")],
        batch_elapsed_seconds=0.1,
        batch_peak_gpu_memory_bytes=0,
    )

    changed_binding = build_evaluation_binding(
        probe_config(),
        EvaluationSettings(batch_size=2, resume=True),
        test_file,
        records,
        adapter_path=None,
    )
    with pytest.raises(ValueError, match="评测绑定不一致"):
        EvaluationJournal(output_dir, changed_binding, records, resume=True)

    duplicate = json.dumps(
        _journal_row(0, "s0", "benign", batch_number=2, batch_size=1),
        sort_keys=True,
    )
    with (output_dir / "predictions.partial.jsonl").open("a", encoding="utf-8") as target:
        target.write(duplicate + "\n")
    with pytest.raises(ValueError, match="重复"):
        EvaluationJournal(output_dir, binding, records, resume=True)


def test_evaluation_journal_truncates_interrupted_tail_batch(tmp_path: Path) -> None:
    records = [
        {
            "sample_id": f"s{index}",
            "prompt": f"p{index}",
            "completion": '{"label":"benign"}',
        }
        for index in range(4)
    ]
    test_file = tmp_path / "test.jsonl"
    _write_records(test_file, records)
    settings = EvaluationSettings(batch_size=2, resume=True)
    binding = build_evaluation_binding(
        probe_config(), settings, test_file, records, adapter_path=None
    )
    output_dir = tmp_path / "run"
    EvaluationJournal(output_dir, binding, records, resume=True)
    committed_rows = [
        _journal_row(0, "s0", "benign", batch_number=1, batch_size=2),
        _journal_row(1, "s1", "benign", batch_number=1, batch_size=2),
    ]
    interrupted_row = _journal_row(2, "s2", "benign", batch_number=2, batch_size=2)
    partial_path = output_dir / "predictions.partial.jsonl"
    partial_path.write_bytes(
        b"".join(
            json.dumps(row, sort_keys=True).encode("utf-8") + b"\n"
            for row in [*committed_rows, interrupted_row]
        )
        + b'{"record_index":3,"sample_id":"s3"'
    )

    resumed = EvaluationJournal(output_dir, binding, records, resume=True)

    assert resumed.pending_indices == (2, 3)
    progress = json.loads((output_dir / "evaluation_progress.json").read_text(encoding="utf-8"))
    assert progress["completed_batches"] == 1
    restored_rows = [
        json.loads(line) for line in partial_path.read_text(encoding="utf-8").splitlines()
    ]
    assert [row["record_index"] for row in restored_rows] == [0, 1]


@pytest.mark.parametrize(
    "missing_field",
    [
        "generated_text",
        "parsed_label",
        "is_valid",
        "parse_error",
        "input_tokens",
        "generated_tokens",
        "latency_ms",
    ],
)
def test_evaluation_journal_rejects_missing_prediction_semantics(
    tmp_path: Path,
    missing_field: str,
) -> None:
    records = [{"sample_id": "s0", "prompt": "p0", "completion": '{"label":"benign"}'}]
    test_file = tmp_path / "test.jsonl"
    _write_records(test_file, records)
    settings = EvaluationSettings(batch_size=1, resume=True)
    binding = build_evaluation_binding(
        probe_config(), settings, test_file, records, adapter_path=None
    )
    output_dir = tmp_path / "run"
    EvaluationJournal(output_dir, binding, records, resume=True)
    row = _journal_row(0, "s0", "benign", batch_number=1, batch_size=1)
    row.pop(missing_field)
    _write_records(output_dir / "predictions.partial.jsonl", [row])

    with pytest.raises(ValueError, match=missing_field):
        EvaluationJournal(output_dir, binding, records, resume=True)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("generated_text", {}),
        ("parsed_label", []),
        ("parsed_label", "malicious"),
        ("is_valid", 1),
        ("parse_error", "被篡改"),
        ("input_tokens", True),
        ("generated_tokens", -1),
        ("latency_ms", float("inf")),
    ],
)
def test_evaluation_journal_rejects_invalid_prediction_semantics(
    tmp_path: Path,
    field: str,
    invalid_value: object,
) -> None:
    records = [{"sample_id": "s0", "prompt": "p0", "completion": '{"label":"benign"}'}]
    test_file = tmp_path / "test.jsonl"
    _write_records(test_file, records)
    settings = EvaluationSettings(batch_size=1, resume=True)
    binding = build_evaluation_binding(
        probe_config(), settings, test_file, records, adapter_path=None
    )
    output_dir = tmp_path / "run"
    EvaluationJournal(output_dir, binding, records, resume=True)
    row = _journal_row(0, "s0", "benign", batch_number=1, batch_size=1)
    row[field] = invalid_value
    _write_records(output_dir / "predictions.partial.jsonl", [row])

    with pytest.raises(ValueError, match=field):
        EvaluationJournal(output_dir, binding, records, resume=True)


def test_evaluation_journal_does_not_publish_before_summary_succeeds(
    tmp_path: Path,
) -> None:
    records = [{"sample_id": "s0", "prompt": "p0", "completion": '{"label":"benign"}'}]
    test_file = tmp_path / "test.jsonl"
    _write_records(test_file, records)
    settings = EvaluationSettings(batch_size=1, resume=True)
    binding = build_evaluation_binding(
        probe_config(), settings, test_file, records, adapter_path=None
    )
    output_dir = tmp_path / "run"
    journal = EvaluationJournal(output_dir, binding, records, resume=True)
    journal.append_batch(
        [_prediction_row(0, "s0", "benign")],
        batch_elapsed_seconds=0.1,
        batch_peak_gpu_memory_bytes=1024,
    )

    def fail_summary(_rows):
        raise RuntimeError("汇总失败")

    with pytest.raises(RuntimeError, match="汇总失败"):
        journal.finalize(fail_summary)

    assert not (output_dir / "predictions.jsonl").exists()
    assert not (output_dir / "evaluation_summary.json").exists()
    progress = json.loads((output_dir / "evaluation_progress.json").read_text(encoding="utf-8"))
    assert progress["status"] == "running"


def test_generate_batch_uses_left_padding_and_excludes_padding_tokens() -> None:
    torch = pytest.importorskip("torch")

    class BatchEncoding(dict):
        def to(self, _device):
            return self

    class BatchTokenizer:
        pad_token_id = 0
        eos_token_id = 0
        padding_side = "left"

        def __init__(self) -> None:
            self.last_input_ids = None

        def __call__(self, prompts, **_kwargs):
            token_map = {"short": [11], "long": [21, 22, 23]}
            sequences = [token_map[prompt] for prompt in prompts]
            width = max(len(sequence) for sequence in sequences)
            padded = [[0] * (width - len(sequence)) + sequence for sequence in sequences]
            masks = [[0] * (width - len(sequence)) + [1] * len(sequence) for sequence in sequences]
            self.last_input_ids = padded
            return BatchEncoding(
                input_ids=torch.tensor(padded),
                attention_mask=torch.tensor(masks),
            )

        def batch_decode(self, token_rows, **_kwargs):
            labels = {91: "benign", 92: "malicious"}
            return [json.dumps({"label": labels[int(row[0])]}) for row in token_rows]

    class BatchModel:
        device = torch.device("cpu")

        def __init__(self) -> None:
            self.generate_calls = 0

        def generate(self, input_ids, **_kwargs):
            self.generate_calls += 1
            codes = torch.tensor([[91, 0] if int(row[-1]) == 11 else [92, 0] for row in input_ids])
            return torch.cat((input_ids, codes), dim=1)

    tokenizer = BatchTokenizer()
    model = BatchModel()
    batched = _generate_batch(
        model,
        tokenizer,
        ["short", "long"],
        max_input_length=16,
        max_new_tokens=2,
        synchronize=lambda: None,
    )

    assert model.generate_calls == 1
    assert tokenizer.last_input_ids == [[0, 0, 11], [21, 22, 23]]
    assert [result.input_tokens for result in batched] == [1, 3]
    assert [result.generated_tokens for result in batched] == [1, 1]
    assert [json.loads(result.text)["label"] for result in batched] == [
        "benign",
        "malicious",
    ]
    single_outputs = [
        _generate_batch(
            model,
            tokenizer,
            [prompt],
            max_input_length=16,
            max_new_tokens=2,
            synchronize=lambda: None,
        )[0].text
        for prompt in ("short", "long")
    ]
    assert [result.text for result in batched] == single_outputs


def test_evaluation_tracking_config_records_runtime_settings() -> None:
    settings = EvaluationSettings(
        batch_size=16,
        length_bucket=True,
        flush_every_batches=2,
        resume=True,
        attention_backend="sdpa",
    )

    config = build_evaluation_tracking_config(
        probe_config(),
        test_file="data/test.jsonl",
        adapter_path=None,
        settings=settings,
    )

    assert config["batch_size"] == 16
    assert config["length_bucket"] is True
    assert config["flush_every_batches"] == 2
    assert config["resume"] is True
    assert config["attention_backend"] == "sdpa"


def test_evaluation_progress_metrics_use_stable_swanlab_keys() -> None:
    metrics = build_evaluation_progress_metrics(
        {
            "completed_samples": 8,
            "total_samples": 20,
            "samples_per_second": 4.0,
            "eta_seconds": 3.0,
            "gpu_peak_mib": 1024.0,
            "batch_gpu_peak_mib": 256.0,
        },
        batch_latency_ms=2000.0,
    )

    assert metrics == {
        "progress/completed": 8,
        "progress/ratio": 0.4,
        "throughput/samples_per_second": 4.0,
        "runtime/eta_seconds": 3.0,
        "runtime/batch_latency_ms": 2000.0,
        "memory/gpu_peak_mib": 256.0,
    }


def test_cuda_peak_memory_is_reset_for_every_batch() -> None:
    class FakeCuda:
        def __init__(self) -> None:
            self.reset_calls = 0
            self.peaks = iter([8 * 1024 * 1024, 2 * 1024 * 1024])

        def reset_peak_memory_stats(self) -> None:
            self.reset_calls += 1

        def max_memory_allocated(self) -> int:
            return next(self.peaks)

    cuda = FakeCuda()
    first_result, first_peak = evaluate_model_module._run_with_fresh_cuda_peak(
        lambda: "first", cuda
    )
    second_result, second_peak = evaluate_model_module._run_with_fresh_cuda_peak(
        lambda: "second", cuda
    )

    assert cuda.reset_calls == 2
    assert (first_result, first_peak) == ("first", 8 * 1024 * 1024)
    assert (second_result, second_peak) == ("second", 2 * 1024 * 1024)


def test_resume_uses_new_tracking_attempt_without_overwriting_manifest(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "run"
    output_dir.mkdir()
    (output_dir / "artifact_manifest.json").write_text("{}\n", encoding="utf-8")

    first = evaluation_tracking_artifact_dir(output_dir, resume=True)
    assert first == output_dir / "tracking-attempts" / "attempt-0001"
    first.mkdir(parents=True)
    (first / "artifact_manifest.json").write_text("{}\n", encoding="utf-8")

    assert evaluation_tracking_artifact_dir(output_dir, resume=True) == (
        output_dir / "tracking-attempts" / "attempt-0002"
    )
    assert evaluation_tracking_artifact_dir(output_dir, resume=False) == output_dir
