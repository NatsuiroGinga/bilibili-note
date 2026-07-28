import pytest

from flow_probe.schemas import CANONICAL_CORE_FIELDS, FlowSample, SchemaError


def sample_kwargs() -> dict[str, object]:
    return {
        "sample_id": "genis:flows.csv:1",
        "source_dataset": "genis",
        "source_file": "flows.csv",
        "group_id": "capture-2025-02-10",
        "original_label": "0",
        "binary_label": "benign",
        "attack_family": "benign",
        "feature_view": "canonical_core_v1",
        "features": {field: None for field in CANONICAL_CORE_FIELDS},
    }


def test_canonical_core_contains_only_cross_dataset_fields() -> None:
    assert CANONICAL_CORE_FIELDS == (
        "total_packets",
        "total_bytes",
        "packet_length_mean",
        "packet_length_min",
        "packet_length_max",
        "iat_mean_ms",
        "packet_rate",
        "byte_rate",
    )


def test_sample_accepts_explicit_missing_values_without_zero_fill() -> None:
    sample = FlowSample(**sample_kwargs())

    assert sample.features["iat_mean_ms"] is None
    assert set(sample.features) == set(CANONICAL_CORE_FIELDS)


def test_sample_rejects_unknown_binary_label() -> None:
    kwargs = sample_kwargs()
    kwargs["binary_label"] = "attack"

    with pytest.raises(SchemaError, match="二分类标签"):
        FlowSample(**kwargs)


def test_sample_rejects_empty_group_id() -> None:
    kwargs = sample_kwargs()
    kwargs["group_id"] = ""

    with pytest.raises(SchemaError, match="group_id"):
        FlowSample(**kwargs)


def test_sample_rejects_missing_core_field() -> None:
    kwargs = sample_kwargs()
    features = dict(kwargs["features"])
    features.pop("iat_mean_ms")
    kwargs["features"] = features

    with pytest.raises(SchemaError, match="缺少核心字段.*iat_mean_ms"):
        FlowSample(**kwargs)


def test_sample_rejects_unexpected_core_field() -> None:
    kwargs = sample_kwargs()
    features = dict(kwargs["features"])
    features["source_dataset"] = "genis"
    kwargs["features"] = features

    with pytest.raises(SchemaError, match="未知核心字段.*source_dataset"):
        FlowSample(**kwargs)
