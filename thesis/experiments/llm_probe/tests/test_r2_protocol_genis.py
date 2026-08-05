from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

pa = pytest.importorskip("pyarrow")
pq = pytest.importorskip("pyarrow.parquet")

from flow_probe.adapters.genis import adapt_row
from flow_probe.r2_protocol_contract import (
    COMMON_FIELDS,
    GeNISArtifactSpec,
    canonical_json_sha256,
    load_r2_config,
    verify_genis_archive,
)
from flow_probe.r2_protocol_genis import (
    FieldUnitEvidence,
    GeNISProtocolError,
    GeNISUnitEvidence,
    iter_genis_10s_rows,
    reconnect_genis_candidate,
    validate_genis_units,
)
from flow_probe.serialize import serialize_flow

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs/r2_protocol_data_v1.yaml"
MEMBER_PATH = "2-flows/flows-10-sec/benign-admin.csv"
MEMBER_BASENAME = "benign-admin.csv"


def _raw_row(**overrides: str) -> dict[str, str]:
    row = {
        "FlowID": "10.0.0.1:1234-10.0.0.2:443-tcp",
        "Proto": "tcp",
        "BinaryLabel": "0",
        "CategoryLabel": "benign",
        "SubCategoryLabel": "benign-admin",
        "TotPkts": "4",
        "SrcPkts": "2",
        "DstPkts": "2",
        "TotBytes": "400",
        "sMinPktSz": "80",
        "dMinPktSz": "90",
        "sMaxPktSz": "120",
        "dMaxPktSz": "130",
        "SIntPkt": "2",
        "DIntPkt": "4",
        "Rate": "10",
        "Load": "800",
        "Loss": "0",
        "Retrans": "0",
        "TcpRtt": "0.01",
        "SrcWin": "8192",
        "DstWin": "8192",
    }
    row.update(overrides)
    return row


def _write_archive(path: Path, rows: list[dict[str, str]]) -> GeNISArtifactSpec:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MEMBER_PATH, output.getvalue().encode("utf-8"))
    payload = path.read_bytes()
    return GeNISArtifactSpec(
        logical_path="fixture:genis/2-flows.zip",
        record_id="fixture",
        doi="fixture",
        version="fixture-v1",
        url="https://example.invalid/2-flows.zip",
        size_bytes=len(payload),
        md5=hashlib.md5(payload, usedforsecurity=False).hexdigest(),
        scales_seconds=(10,),
        csv_per_scale=1,
        materialization_scale_seconds=10,
    )


def _old_sample_id(row_number: int = 1) -> str:
    return f"genis:{MEMBER_BASENAME}:{row_number}"


def _candidate_id(row_number: int = 1) -> str:
    digest = hashlib.sha256(
        f"dataset-candidate-genis-v0\0{_old_sample_id(row_number)}".encode()
    ).hexdigest()
    return f"genis:{digest}"


def _group_id(flow_id: str) -> str:
    digest = hashlib.blake2b(digest_size=16)
    digest.update(MEMBER_BASENAME.encode())
    digest.update(b"\0")
    digest.update(flow_id.encode())
    return digest.hexdigest()


def _candidate_row(raw: dict[str, str], row_number: int = 1) -> dict[str, object]:
    sample = replace(
        adapt_row(raw, MEMBER_BASENAME, row_number),
        group_id=_group_id(raw["FlowID"]),
    )
    training_record = {
        "sample_id": sample.sample_id,
        "group_id": sample.group_id,
        "source_dataset": sample.source_dataset,
        "binary_label": sample.binary_label,
        "attack_family": sample.attack_family,
        "attack_subtype": sample.original_label,
        "features": dict(sample.features),
        "prompt": serialize_flow(sample),
        "completion": json.dumps(
            {"label": sample.binary_label}, ensure_ascii=False, separators=(",", ":")
        ),
    }
    row: dict[str, object] = {
        "sample_id": _candidate_id(row_number),
        "source_record_sha256": canonical_json_sha256(training_record),
        "source_dataset": "genis",
        "group_id": sample.group_id,
        "binary_label": sample.binary_label,
        "family_label": sample.attack_family,
        "subtype_label": sample.original_label,
    }
    for field_name in COMMON_FIELDS:
        row[field_name] = sample.features[field_name]
        row[f"{field_name}_missing"] = int(sample.features[field_name] is None)
    return row


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_candidate(path: Path, rows: list[dict[str, object]]) -> None:
    pq.write_table(pa.Table.from_pylist(rows), path)


def _fixture_config(spec: GeNISArtifactSpec, candidate: Path):
    base = load_r2_config(CONFIG_PATH)
    inputs = tuple(
        replace(item, sha256=_sha256_file(candidate))
        if item.role == "genis_candidate"
        else item
        for item in base.frozen_inputs
    )
    return replace(base, genis=spec, frozen_inputs=inputs)


def test_iter_rows_reconstructs_member_and_one_based_row_hash(tmp_path: Path) -> None:
    archive = tmp_path / "2-flows.zip"
    spec = _write_archive(archive, [_raw_row(), _raw_row(FlowID="second")])
    inventory = verify_genis_archive(archive, spec)

    rows = list(iter_genis_10s_rows(archive, inventory))

    assert [row.old_sample_id for row in rows] == [
        _old_sample_id(1),
        _old_sample_id(2),
    ]
    assert [row.candidate_sample_id for row in rows] == [
        _candidate_id(1),
        _candidate_id(2),
    ]


def test_iter_rows_rejects_member_hash_drift(tmp_path: Path) -> None:
    archive = tmp_path / "2-flows.zip"
    spec = _write_archive(archive, [_raw_row()])
    inventory = verify_genis_archive(archive, spec)
    broken_member = replace(inventory.materialization_members[0], sha256="0" * 64)

    with pytest.raises(GeNISProtocolError, match="成员 SHA-256"):
        list(
            iter_genis_10s_rows(
                archive,
                replace(inventory, materialization_members=(broken_member,)),
            )
        )


def test_reconnect_uses_only_fixed_identity_hash_and_recomputes_fields(
    tmp_path: Path,
) -> None:
    raw = _raw_row()
    archive = tmp_path / "2-flows.zip"
    spec = _write_archive(archive, [raw])
    candidate = tmp_path / "samples.parquet"
    _write_candidate(candidate, [_candidate_row(raw)])
    config = _fixture_config(spec, candidate)

    result = reconnect_genis_candidate(candidate, archive, config)

    assert result.join_audit["status"] == "passed"
    assert result.join_audit["matched_rows"] == 1
    assert result.common_features[0]["total_bytes"] == 400.0
    assert result.common_features[0]["iat_mean_ms"] == 3.0
    assert result.protocol_observations[0]["loss_packets"] == 0
    assert result.protocol_observations[0]["retrans_packets"] == 0
    assert result.protocol_observations[0]["tcp_rtt_ms"] is None
    source_map = result.source_row_map[0]
    assert set(source_map) == {
        "sample_id",
        "old_sample_id_sha256",
        "archive_sha256",
        "member_sha256",
        "source_row_reference_sha256",
        "join_status",
        "source_record_sha256",
        "record_sha256",
    }
    rendered = json.dumps(source_map, sort_keys=True)
    assert MEMBER_BASENAME not in rendered
    assert raw["FlowID"] not in rendered
    assert "csv_row_number" not in rendered


def test_reconnect_never_falls_back_to_label_or_feature_join(tmp_path: Path) -> None:
    raw = _raw_row()
    archive = tmp_path / "2-flows.zip"
    spec = _write_archive(archive, [raw])
    row = _candidate_row(raw)
    row["sample_id"] = "genis:" + "f" * 64
    candidate = tmp_path / "samples.parquet"
    _write_candidate(candidate, [row])
    config = _fixture_config(spec, candidate)

    with pytest.raises(GeNISProtocolError, match="未消费"):
        reconnect_genis_candidate(candidate, archive, config)


def test_reconnect_rejects_duplicate_candidate_ids(tmp_path: Path) -> None:
    raw = _raw_row()
    archive = tmp_path / "2-flows.zip"
    spec = _write_archive(archive, [raw])
    row = _candidate_row(raw)
    candidate = tmp_path / "samples.parquet"
    _write_candidate(candidate, [row, dict(row)])
    config = _fixture_config(spec, candidate)

    with pytest.raises(GeNISProtocolError, match="sample_id 重复"):
        reconnect_genis_candidate(candidate, archive, config)


def test_reconnect_rejects_recomputed_label_or_observation_drift(
    tmp_path: Path,
) -> None:
    raw = _raw_row()
    archive = tmp_path / "2-flows.zip"
    spec = _write_archive(archive, [raw])
    row = _candidate_row(raw)
    row["total_bytes"] = 401.0
    candidate = tmp_path / "samples.parquet"
    _write_candidate(candidate, [row])
    config = _fixture_config(spec, candidate)

    with pytest.raises(GeNISProtocolError, match="total_bytes"):
        reconnect_genis_candidate(candidate, archive, config)


def test_reconnect_rejects_negative_or_fractional_packet_counts(
    tmp_path: Path,
) -> None:
    raw = _raw_row(Loss="-1", Retrans="0.5")
    archive = tmp_path / "2-flows.zip"
    spec = _write_archive(archive, [raw])
    candidate = tmp_path / "samples.parquet"
    _write_candidate(candidate, [_candidate_row(raw)])
    config = _fixture_config(spec, candidate)

    with pytest.raises(GeNISProtocolError, match="非负整数包计数"):
        reconnect_genis_candidate(candidate, archive, config)


def _missing_evidence(field_name: str) -> FieldUnitEvidence:
    return FieldUnitEvidence(field_name=field_name, status="missing")


def _verified_evidence(field_name: str) -> FieldUnitEvidence:
    common = {
        "field_name": field_name,
        "status": "verified",
        "evidence_logical_path": f"evidence/{field_name}.json",
        "evidence_artifact_sha256": hashlib.sha256(field_name.encode()).hexdigest(),
        "algorithm": "primary_definition_with_exact_scale",
        "scale_factor": 1.0,
        "aggregation_semantics": "flow_level_value",
    }
    if field_name == "TotBytes":
        return FieldUnitEvidence(
            **common,
            authority_kind="network_layer_packet_recalculation",
            unit="network_layer_bytes",
            semantic_role="network_layer_byte_sum",
            compared_rows=3973,
            exact_integer_matches=3973,
        )
    if field_name == "TcpRtt":
        return FieldUnitEvidence(
            **common,
            authority_kind="primary_source",
            unit="milliseconds",
            semantic_role="handshake_round_trip_time",
        )
    return FieldUnitEvidence(
        **common,
        authority_kind="primary_source",
        unit="bytes",
        semantic_role="advertised_receive_window",
    )


def test_unit_gate_is_no_go_when_any_primary_semantics_are_missing() -> None:
    result = validate_genis_units(
        GeNISUnitEvidence(
            tot_bytes=_verified_evidence("TotBytes"),
            tcp_rtt=_missing_evidence("TcpRtt"),
            src_window=_missing_evidence("SrcWin"),
            dst_window=_missing_evidence("DstWin"),
        )
    )

    assert result.status == "NO-GO"
    assert result.passed is False
    assert result.field_passed["TotBytes"] is True
    assert result.field_passed["TcpRtt"] is False


def test_unit_gate_rejects_incomplete_totbytes_exact_integer_comparison() -> None:
    tot_bytes = replace(
        _verified_evidence("TotBytes"), exact_integer_matches=3972
    )
    result = validate_genis_units(
        GeNISUnitEvidence(
            tot_bytes=tot_bytes,
            tcp_rtt=_verified_evidence("TcpRtt"),
            src_window=_verified_evidence("SrcWin"),
            dst_window=_verified_evidence("DstWin"),
        )
    )

    assert result.status == "NO-GO"
    assert "TotBytes:exact_integer_comparison_incomplete" in result.reasons


def test_unit_gate_go_requires_all_four_verified_primary_evidence() -> None:
    result = validate_genis_units(
        GeNISUnitEvidence(
            tot_bytes=_verified_evidence("TotBytes"),
            tcp_rtt=_verified_evidence("TcpRtt"),
            src_window=_verified_evidence("SrcWin"),
            dst_window=_verified_evidence("DstWin"),
        )
    )

    assert result.status == "GO"
    assert result.passed is True
    assert all(result.field_passed.values())
    assert len(result.evidence_sha256) == 64
