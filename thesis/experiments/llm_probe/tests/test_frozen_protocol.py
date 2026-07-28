import json
from pathlib import Path

import pandas as pd
import pytest
import yaml
from frozen_protocol_fixture import refresh_artifact_hash, write_frozen_protocol_fixture

from flow_probe.frozen_protocol import FrozenProtocolError, load_frozen_protocol


def test_load_frozen_protocol_preserves_manifest_order_and_field_budget(
    tmp_path: Path,
) -> None:
    protocol_dir = tmp_path / "protocol"
    expected = write_frozen_protocol_fixture(protocol_dir)

    protocol = load_frozen_protocol(protocol_dir)
    validation = protocol.load_tabular_split(
        "splits/fixture-validation.jsonl", label_field="binary_label"
    )

    assert list(protocol.manifests) == [
        "splits/fixture-train.jsonl",
        "splits/fixture-validation.jsonl",
    ]
    assert validation.sample_ids == tuple(expected["validation"])
    assert validation.feature_fields == ("feature_a", "feature_b")
    assert validation.features.flags.writeable is False
    assert validation.features[:, 0].tolist() == pytest.approx(
        [10.0, 0.01, 20.02, 10.03, 0.04, 10.05]
    )
    assert "audit_token" not in validation.feature_fields


def test_load_frozen_protocol_rejects_unregistered_manifest_change(tmp_path: Path) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(protocol_dir)
    manifest_path = protocol_dir / "splits" / "fixture-validation.jsonl"
    manifest_path.write_text(
        manifest_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    with pytest.raises(FrozenProtocolError, match="清单哈希不一致"):
        load_frozen_protocol(protocol_dir)


def test_load_frozen_protocol_rejects_unknown_manifest_member(tmp_path: Path) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(protocol_dir)
    manifest_path = protocol_dir / "splits" / "fixture-validation.jsonl"
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["sample_id"] = "not-in-samples"
    manifest_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    refresh_artifact_hash(protocol_dir, "splits/fixture-validation.jsonl")

    with pytest.raises(FrozenProtocolError, match="外的样本"):
        load_frozen_protocol(protocol_dir)


def test_load_frozen_protocol_rejects_duplicate_sample_id(tmp_path: Path) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(protocol_dir)
    samples_path = protocol_dir / "samples.parquet"
    samples = pd.read_parquet(samples_path)
    samples.loc[1, "sample_id"] = samples.loc[0, "sample_id"]
    samples.to_parquet(samples_path, index=False)
    refresh_artifact_hash(protocol_dir, "samples.parquet")

    with pytest.raises(FrozenProtocolError, match="全局唯一"):
        load_frozen_protocol(protocol_dir)


def test_load_frozen_protocol_rejects_label_field_in_model_view(tmp_path: Path) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(protocol_dir)
    roles_path = protocol_dir / "field-roles.yaml"
    roles = yaml.safe_load(roles_path.read_text(encoding="utf-8"))
    roles["views"]["tree_flat_view"]["feature_fields"].append("binary_label")
    roles_path.write_text(
        yaml.safe_dump(roles, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )
    refresh_artifact_hash(protocol_dir, "field-roles.yaml")

    with pytest.raises(FrozenProtocolError, match="越过字段预算"):
        load_frozen_protocol(protocol_dir)
