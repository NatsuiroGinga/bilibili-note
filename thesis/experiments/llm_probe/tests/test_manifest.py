from hashlib import sha256

import pytest

from flow_probe.manifest import ManifestError, build_manifest
from flow_probe.schemas import CANONICAL_CORE_FIELDS, FlowSample


def make_sample(index: int, label: str, missing_iat: bool) -> FlowSample:
    features = {field: float(index + 1) for field in CANONICAL_CORE_FIELDS}
    if missing_iat:
        features["iat_mean_ms"] = None
    return FlowSample(
        sample_id=f"sample-{index}",
        source_dataset="fixture",
        source_file="fixture.csv",
        group_id=f"group-{index}",
        original_label=label,
        binary_label=label,
        attack_family=label,
        feature_view="canonical_core_v1",
        features=features,
    )


def test_manifest_contains_hash_distribution_and_missing_rate(tmp_path) -> None:
    source = tmp_path / "fixture.csv"
    source.write_bytes(b"a,b\n1,2\n")
    samples = [make_sample(0, "benign", True), make_sample(1, "malicious", False)]
    split_summary = {
        "train": 1,
        "validation": 0,
        "test": 1,
        "group_basis": "source_file",
        "evidence_level": "primary",
    }

    manifest = build_manifest(samples, [source], split_summary)

    assert manifest["sample_count"] == 2
    assert manifest["label_distribution"] == {"benign": 1, "malicious": 1}
    assert manifest["field_missing_rate"]["iat_mean_ms"] == pytest.approx(0.5)
    assert manifest["sources"][0]["sha256"] == sha256(source.read_bytes()).hexdigest()
    assert manifest["split_summary"]["group_basis"] == "source_file"


def test_manifest_requires_group_basis(tmp_path) -> None:
    source = tmp_path / "fixture.csv"
    source.write_text("x\n", encoding="utf-8")

    with pytest.raises(ManifestError, match="group_basis"):
        build_manifest(
            [make_sample(0, "benign", False)],
            [source],
            {"evidence_level": "diagnostic"},
        )
