import pytest

from flow_probe.schemas import CANONICAL_CORE_FIELDS, FlowSample
from flow_probe.split import (
    DatasetSplits,
    SplitError,
    _assignment_score,
    assert_no_group_overlap,
    grouped_split,
)


def make_sample(group: int, index: int, label: str) -> FlowSample:
    return FlowSample(
        sample_id=f"sample-{group}-{index}",
        source_dataset="fixture",
        source_file="fixture.csv",
        group_id=f"group-{group}",
        original_label=label,
        binary_label=label,
        attack_family=label,
        feature_view="canonical_core_v1",
        features={field: None for field in CANONICAL_CORE_FIELDS},
    )


def grouped_samples(group_count: int = 12) -> list[FlowSample]:
    samples = []
    for group in range(group_count):
        samples.append(make_sample(group, 0, "benign"))
        samples.append(make_sample(group, 1, "malicious"))
    return samples


def test_assignment_score_uses_aggregate_counts() -> None:
    score = _assignment_score(
        current_size=8,
        current_labels={"benign": 6, "malicious": 2},
        group_size=4,
        group_labels={"benign": 1, "malicious": 3},
        target_size=10,
        target_labels={"benign": 7, "malicious": 3},
    )

    assert score == pytest.approx(2 / 10 + 0 / 7 + 2 / 3)


def test_grouped_split_keeps_each_group_in_one_partition() -> None:
    splits = grouped_split(grouped_samples(), ratios=(0.5, 0.25, 0.25), seed=42)

    assert_no_group_overlap(splits)
    assert len(splits.train) == 12
    assert len(splits.validation) == 6
    assert len(splits.test) == 6
    assert splits.evidence_level == "primary"


def test_grouped_split_is_reproducible() -> None:
    first = grouped_split(grouped_samples(), ratios=(0.5, 0.25, 0.25), seed=42)
    second = grouped_split(grouped_samples(), ratios=(0.5, 0.25, 0.25), seed=42)

    assert [sample.sample_id for sample in first.train] == [
        sample.sample_id for sample in second.train
    ]


def test_grouped_split_marks_unverified_groups_as_diagnostic() -> None:
    splits = grouped_split(
        grouped_samples(), ratios=(0.5, 0.25, 0.25), seed=42, reliable_groups=False
    )

    assert splits.evidence_level == "diagnostic"


def test_grouped_split_preserves_class_coverage_when_three_groups_exist() -> None:
    samples = [make_sample(group, 0, "benign") for group in range(120)]
    for group in range(120, 124):
        samples.extend(make_sample(group, index, "malicious") for index in range(50))

    splits = grouped_split(samples, ratios=(0.8, 0.1, 0.1), seed=42)

    for partition in (splits.train, splits.validation, splits.test):
        assert {sample.binary_label for sample in partition} == {"benign", "malicious"}
    assert_no_group_overlap(splits)


def test_class_coverage_overrides_soft_group_quota_for_pure_label_groups() -> None:
    samples = []
    for group in range(3):
        samples.extend(make_sample(group, index, "benign") for index in range(10))
    for group in range(3, 11):
        samples.extend(make_sample(group, index, "malicious") for index in range(20))

    splits = grouped_split(samples, ratios=(0.8, 0.1, 0.1), seed=42)

    for partition in (splits.train, splits.validation, splits.test):
        assert {sample.binary_label for sample in partition} == {"benign", "malicious"}
    assert_no_group_overlap(splits)


def test_grouped_split_rejects_duplicate_sample_ids() -> None:
    samples = grouped_samples()
    samples.append(samples[0])

    with pytest.raises(SplitError, match="样本标识重复"):
        grouped_split(samples, ratios=(0.5, 0.25, 0.25), seed=42)


def test_grouped_split_does_not_fall_back_to_row_split() -> None:
    with pytest.raises(SplitError, match="至少需要 3 个分组"):
        grouped_split(grouped_samples(group_count=2), ratios=(0.5, 0.25, 0.25), seed=42)


def test_overlap_assertion_detects_manual_group_leakage() -> None:
    sample = make_sample(1, 0, "benign")
    splits = DatasetSplits(
        train=(sample,), validation=(sample,), test=(), evidence_level="diagnostic"
    )

    with pytest.raises(SplitError, match="分组交叉"):
        assert_no_group_overlap(splits)
