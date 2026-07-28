from pathlib import Path

import pytest
import torch

from flow_probe.hierarchical_evaluation import (
    FAMILY_LABELS,
    SUBTYPE_LABELS,
    EvaluationSettings,
    build_candidate_completion,
    build_evaluation_plan,
    completion_mean_log_probability,
    decode_candidate_scores,
    encode_candidate_sequence,
    select_stratified_records,
)


def _settings() -> EvaluationSettings:
    return EvaluationSettings.from_mapping(
        {
            "sample_dir": "runs/data-sampled/genis-hierarchical-v2-seed42",
            "output_dir": "runs/qwen-evaluation/genis-hierarchical-v2-seed42-pilot",
            "samples_per_label": 2,
            "generation_batch_size": 4,
            "scoring_batch_size": 8,
            "progress_every_batches": 2,
            "max_known_rejection_rate": 0.05,
            "seed": 42,
        }
    )


def test_evaluation_plan_uses_only_subtype_validation_for_threshold() -> None:
    plan = build_evaluation_plan(_settings())

    assert [split.name for split in plan] == [
        "family_test",
        "subtype_validation",
        "subtype_test",
        "ood_dos_icmp",
        "ood_dos_pushack",
        "ood_dos_udp",
    ]
    assert [split.name for split in plan if split.calibrates_threshold] == ["subtype_validation"]
    assert plan[0].candidate_labels == FAMILY_LABELS
    assert plan[1].candidate_labels == SUBTYPE_LABELS
    assert plan[3].free_generation_labels == (*SUBTYPE_LABELS, "unknown_attack")
    assert plan[3].candidate_labels == SUBTYPE_LABELS


def test_evaluation_plan_resolves_all_paths_under_sample_directory() -> None:
    settings = _settings()
    plan = build_evaluation_plan(settings)

    assert plan[0].path == settings.sample_dir / "family" / "test.jsonl"
    assert plan[1].path == settings.sample_dir / "subtype" / "validation.jsonl"
    assert plan[-1].path == settings.sample_dir / "subtype_ood" / "dos-udp.jsonl"


def test_settings_reject_invalid_budget_and_batch_size() -> None:
    base = {
        "sample_dir": "samples",
        "output_dir": "output",
        "samples_per_label": 2,
        "generation_batch_size": 4,
        "scoring_batch_size": 8,
        "progress_every_batches": 2,
        "max_known_rejection_rate": 0.05,
        "seed": 42,
    }

    with pytest.raises(ValueError, match="拒识率"):
        EvaluationSettings.from_mapping({**base, "max_known_rejection_rate": 1.0})
    with pytest.raises(ValueError, match="批量"):
        EvaluationSettings.from_mapping({**base, "generation_batch_size": 0})


def test_stratified_selection_is_balanced_deterministic_and_non_mutating() -> None:
    records = [{"sample_id": f"benign-{index}", "task_label": "benign"} for index in range(4)] + [
        {"sample_id": f"dos-{index}", "task_label": "dos"} for index in range(4)
    ]
    original_ids = [record["sample_id"] for record in records]

    first = select_stratified_records(records, ("benign", "dos"), per_label=2, seed=42)
    second = select_stratified_records(records, ("benign", "dos"), per_label=2, seed=42)

    assert first == second
    assert [record["task_label"] for record in first].count("benign") == 2
    assert [record["task_label"] for record in first].count("dos") == 2
    assert [record["sample_id"] for record in records] == original_ids


def test_stratified_selection_rejects_missing_label_capacity() -> None:
    records = [{"sample_id": "only", "task_label": "benign"}]

    with pytest.raises(ValueError, match="dos"):
        select_stratified_records(records, ("benign", "dos"), per_label=1, seed=42)


def test_candidate_completion_is_canonical_single_key_json() -> None:
    assert build_candidate_completion("slowloris") == '{"label":"slowloris"}'

    with pytest.raises(ValueError, match="标签"):
        build_candidate_completion("")


def test_settings_keep_paths_as_path_objects() -> None:
    settings = _settings()

    assert isinstance(settings.sample_dir, Path)
    assert isinstance(settings.output_dir, Path)


class _FakeTokenizer:
    eos_token_id = 0

    def encode(self, text: str, **_: object) -> list[int]:
        values = {
            "格式化提示": [10, 11],
            '{"label":"ftp"}': [20, 21],
        }
        return values[text]


def test_candidate_sequence_marks_only_completion_and_eos_for_scoring() -> None:
    sequence = encode_candidate_sequence(
        _FakeTokenizer(),
        formatted_prompt="格式化提示",
        label="ftp",
        max_length=8,
    )

    assert sequence.input_ids == (10, 11, 20, 21, 0)
    assert sequence.completion_start == 2
    assert sequence.completion_token_ids == (20, 21, 0)


def test_candidate_sequence_rejects_truncation_that_would_change_protocol() -> None:
    with pytest.raises(ValueError, match="最大长度"):
        encode_candidate_sequence(
            _FakeTokenizer(),
            formatted_prompt="格式化提示",
            label="ftp",
            max_length=4,
        )


def test_candidate_score_decoding_preserves_record_order_and_confidence() -> None:
    decisions = decode_candidate_scores(
        flat_scores=[3.0, 1.0, 0.0, -1.0, 2.0, 0.0],
        candidate_labels=FAMILY_LABELS,
    )

    assert [decision.label for decision in decisions] == ["benign", "bruteforce"]
    assert all(0.0 < decision.confidence < 1.0 for decision in decisions)
    assert decisions[0].probabilities[0] > decisions[0].probabilities[1]
    assert decisions[1].probabilities[1] > decisions[1].probabilities[2]


def test_candidate_score_decoding_rejects_incomplete_rows() -> None:
    with pytest.raises(ValueError, match="整除"):
        decode_candidate_scores([1.0, 2.0], FAMILY_LABELS)


def test_completion_log_probability_uses_shifted_completion_positions_only() -> None:
    sequence = encode_candidate_sequence(
        _FakeTokenizer(),
        formatted_prompt="格式化提示",
        label="ftp",
        max_length=8,
    )
    logits = torch.zeros((len(sequence.input_ids), 32), dtype=torch.float32)
    logits[1, 20] = 4.0
    logits[2, 21] = 3.0
    logits[3, 0] = 2.0
    log_probabilities = torch.log_softmax(logits, dim=-1)
    expected = torch.stack(
        [
            log_probabilities[1, 20],
            log_probabilities[2, 21],
            log_probabilities[3, 0],
        ]
    ).mean()

    actual = completion_mean_log_probability(logits, sequence)

    assert actual == pytest.approx(float(expected))
