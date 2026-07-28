"""TQH-C2 C 理论筛选候选协议的固定夹具测试。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from flow_probe.frozen_protocol import load_frozen_protocol
from flow_probe.tqh_c2_candidate import (
    MODEL_FEATURE_FIELDS,
    PROTOCOL_PHASE,
    PROTOCOL_STATUS,
    PROTOCOL_VERSION,
    SPLIT_FILENAMES,
    TQHC2CandidateError,
    materialize_candidate,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_input_fixture(root: Path) -> None:
    (root / "views").mkdir(parents=True)
    (root / "audit").mkdir()
    master_rows: list[dict[str, object]] = []
    packet_rows: list[dict[str, object]] = []
    sequence = 0
    for interval_s in (30, 300, 1800, 3600):
        for jitter_pct in (0, 30, 70):
            capture_group_id = f"C_i{interval_s}_j{jitter_pct}"
            source_capture_sha256 = _digest(f"pcap:{capture_group_id}")
            allocation_group_id = _digest(f"allocation:{capture_group_id}")
            labels: list[tuple[str, str | None, str]] = [
                ("benign", "benign", "mapped"),
                ("benign_external", "benign", "mapped"),
                ("malicious_c2", "malicious", "mapped"),
                ("malicious_c2", "malicious", "mapped"),
            ]
            if capture_group_id == "C_i30_j0":
                labels.extend(
                    [
                        ("malicious_recon", None, "auxiliary"),
                        ("unknown", None, "unresolved"),
                    ]
                )
            for local_index, (native_label, binary_label, label_status) in enumerate(labels):
                sample_id = _digest(f"sample:{capture_group_id}:{local_index}")
                start_ns = 1_000_000_000 + sequence * 1_000_000
                master_rows.append(
                    {
                        "sample_id": sample_id,
                        "record_sha256": _digest(f"record:{sample_id}"),
                        "dataset_id": "TQH-C2",
                        "dataset_version": "1.0.1",
                        "source_artifact_id": _digest(f"source:{capture_group_id}"),
                        "source_capture_sha256": source_capture_sha256,
                        "extractor_contract_sha256": _digest("extractor"),
                        "allocation_group_id": allocation_group_id,
                        "parent_session_id": f"uid-{sequence}",
                        "capture_group_id": capture_group_id,
                        "sample_unit": "full_flow",
                        "window_start_ns": start_ns,
                        "window_end_ns": start_ns + 2_000_000,
                        "window_ordinal": 0,
                        "packet_count_raw": 2,
                        "packet_count_kept": 2,
                        "native_label": native_label,
                        "binary_label": binary_label,
                        "family_label": "c2" if native_label == "malicious_c2" else None,
                        "subtype_label": "http_aes" if native_label == "malicious_c2" else None,
                        "label_status": label_status,
                        "unknown_role": "unresolved" if native_label == "unknown" else None,
                        "profile": "C",
                        "interval_s": interval_s,
                        "jitter_pct": jitter_pct,
                        "capture_id": f"capture-{capture_group_id}",
                        "join_status": "matched_packets",
                    }
                )
                for packet_index in range(2):
                    packet_rows.append(
                        {
                            "sample_id": sample_id,
                            "packet_index": packet_index,
                            "relative_time_ns": packet_index * (10_000 + sequence),
                            "delta_time_us": packet_index * (10 + sequence),
                            "direction": 1 if packet_index == 0 else -1,
                            "network_length_bytes": 100 + sequence + packet_index,
                            "payload_length_bytes": 40 + local_index + packet_index,
                            "transport_family": "TCP" if local_index % 2 == 0 else "UDP",
                            "tcp_flags": 0x12 if local_index % 2 == 0 else None,
                            "burst_id": packet_index,
                            "is_first_packet": packet_index == 0,
                            "payload_length_observed": True,
                            "tcp_flags_applicable": local_index % 2 == 0,
                            "truncation_mask": False,
                        }
                    )
                sequence += 1

    pd.DataFrame(master_rows).to_parquet(root / "master_records.parquet", index=False)
    pd.DataFrame(packet_rows).to_parquet(
        root / "views" / "packet_observations.parquet", index=False
    )
    (root / "source_checksums.json").write_text(
        json.dumps({"files": []}, sort_keys=True) + "\n", encoding="utf-8"
    )
    for relative_path in (
        "run_manifest.provisional.json",
        "schema.provisional.json",
        "artifact_checksums.provisional.json",
        "audit/cell-audit.json",
        "audit/label-coverage.json",
        "audit/leakage-audit.json",
    ):
        (root / relative_path).write_text("{}\n", encoding="utf-8")


def _artifact_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_materialize_candidate_builds_loadable_group_exclusive_protocol(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "candidate" / "protocol"
    _write_input_fixture(input_dir)

    result = materialize_candidate(input_dir=input_dir, output_dir=output_dir)

    assert result["sample_count"] == 48
    assert result["group_count"] == 12
    assert not (output_dir / "_INCOMPLETE").exists()
    document = yaml.safe_load((output_dir / "protocol.yaml").read_text(encoding="utf-8"))
    assert document["protocol_version"] == PROTOCOL_VERSION
    assert document["status"] == PROTOCOL_STATUS
    assert document["phase"] == PROTOCOL_PHASE
    assert document["review_status"] == "review_pending"
    assert document["final_tuning_allowed"] is False

    protocol = load_frozen_protocol(
        output_dir,
        expected_protocol_version=PROTOCOL_VERSION,
        expected_status=PROTOCOL_STATUS,
        expected_phase=PROTOCOL_PHASE,
    )
    assert tuple(protocol.model_views["tree_flat_view"].feature_fields) == MODEL_FEATURE_FIELDS
    assert set(protocol.manifests) == set(SPLIT_FILENAMES.values())
    manifests = list(protocol.manifests.values())
    all_ids = [sample_id for manifest in manifests for sample_id in manifest.sample_ids]
    assert len(all_ids) == 48
    assert len(set(all_ids)) == 48
    for relative_path in SPLIT_FILENAMES.values():
        split = protocol.load_tabular_split(relative_path)
        assert split.features.shape[1] == len(MODEL_FEATURE_FIELDS)
        assert set(split.labels) == {"benign", "malicious"}

    samples = pd.read_parquet(output_dir / "samples.parquet")
    groups = pd.read_parquet(output_dir / "groups.parquet")
    assert len(groups) == 12
    assert groups.groupby("allocation_group_id")["split_id"].nunique().max() == 1
    assert samples.groupby("allocation_group_id")["split_id"].nunique().max() == 1
    roles = yaml.safe_load((output_dir / "field-roles.yaml").read_text(encoding="utf-8"))
    assert set(roles["fields"]) == set(samples.columns)
    assert all(
        roles["fields"][field_name]["role"] == "model_input" for field_name in MODEL_FEATURE_FIELDS
    )
    labels = json.loads((output_dir / "audit" / "label-coverage.json").read_text())
    assert labels["source_record_count"] == 50
    assert labels["candidate_record_count"] == 48
    assert labels["source_label_status_counts"] == {
        "auxiliary": 1,
        "mapped": 48,
        "unresolved": 1,
    }


def test_materialize_candidate_is_byte_reproducible_and_refuses_overwrite(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    first = tmp_path / "first" / "protocol"
    second = tmp_path / "second" / "protocol"
    _write_input_fixture(input_dir)

    materialize_candidate(input_dir=input_dir, output_dir=first)
    materialize_candidate(input_dir=input_dir, output_dir=second)

    assert _artifact_bytes(first) == _artifact_bytes(second)
    with pytest.raises(TQHC2CandidateError, match="拒绝覆盖"):
        materialize_candidate(input_dir=input_dir, output_dir=first)


def test_materialize_candidate_preserves_incomplete_marker_on_input_failure(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "candidate" / "protocol"
    _write_input_fixture(input_dir)
    packets_path = input_dir / "views" / "packet_observations.parquet"
    packets = pd.read_parquet(packets_path)
    packets = packets.iloc[:-1]
    packets.to_parquet(packets_path, index=False)

    with pytest.raises(TQHC2CandidateError, match="包观测计数"):
        materialize_candidate(input_dir=input_dir, output_dir=output_dir)

    assert (output_dir / "_INCOMPLETE").is_file()


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("binary_label", "malicious"),
        ("label_status", "auxiliary"),
        ("native_label", "unknown"),
    ),
)
def test_materialize_candidate_rejects_invalid_label_contract(
    tmp_path: Path,
    field_name: str,
    invalid_value: str,
) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "candidate" / "protocol"
    _write_input_fixture(input_dir)
    master_path = input_dir / "master_records.parquet"
    master = pd.read_parquet(master_path)
    benign_index = master.index[master["native_label"].eq("benign")][0]
    master.loc[benign_index, field_name] = invalid_value
    master.to_parquet(master_path, index=False)

    with pytest.raises(TQHC2CandidateError, match="标签映射不符合固定契约"):
        materialize_candidate(input_dir=input_dir, output_dir=output_dir)

    assert (output_dir / "_INCOMPLETE").is_file()


def test_materialize_candidate_rejects_nonzero_tcp_flags_when_mask_is_false(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "candidate" / "protocol"
    _write_input_fixture(input_dir)
    packets_path = input_dir / "views" / "packet_observations.parquet"
    packets = pd.read_parquet(packets_path)
    masked_index = packets.index[~packets["tcp_flags_applicable"]][0]
    packets.loc[masked_index, "tcp_flags"] = 0x02
    packets.to_parquet(packets_path, index=False)

    with pytest.raises(TQHC2CandidateError, match="TCP 标志掩码为假"):
        materialize_candidate(input_dir=input_dir, output_dir=output_dir)

    assert (output_dir / "_INCOMPLETE").is_file()
