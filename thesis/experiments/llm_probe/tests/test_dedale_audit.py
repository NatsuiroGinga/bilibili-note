import csv
import datetime as dt
import io
import json
import zipfile
from pathlib import Path

import pytest

from flow_probe.dedale_audit import (
    AssociationDecision,
    DEDALEAuditError,
    FlowIdentity,
    FlowRecord,
    associate_record,
    audit_dedale,
    build_flow_index,
    build_input_manifest,
    classify_day,
    normalize_protocol,
    parse_utc_date,
    validate_label,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("6", "tcp"),
        ("17", "udp"),
        ("1", "icmp"),
        ("TCP", "tcp"),
        ("  udp  ", "udp"),
        ("132", "132"),
    ],
)
def test_normalize_protocol_unifies_numeric_and_text_values(raw: str, expected: str) -> None:
    assert normalize_protocol(raw) == expected


def test_parse_utc_date_interprets_nanosecond_text_as_utc() -> None:
    parsed = parse_utc_date("2025-01-06 10:00:13.154357910")
    expected = dt.datetime(2025, 1, 6, 10, 0, 13, 154358, tzinfo=dt.timezone.utc).timestamp()

    assert parsed == pytest.approx(expected, abs=1e-6)


@pytest.mark.parametrize(
    ("day_id", "expected"),
    [(1, "calibration"), (14, "calibration"), (15, "test"), (28, "test")],
)
def test_classify_day_preserves_official_temporal_split(day_id: int, expected: str) -> None:
    assert classify_day(day_id) == expected


@pytest.mark.parametrize("day_id", [0, 29])
def test_classify_day_rejects_values_outside_four_weeks(day_id: int) -> None:
    with pytest.raises(DEDALEAuditError, match="日序"):
        classify_day(day_id)


@pytest.mark.parametrize("label", ["0", "1", "2"])
def test_validate_label_preserves_official_three_class_semantics(label: str) -> None:
    assert validate_label(label) == label


def test_validate_label_rejects_unknown_values() -> None:
    with pytest.raises(DEDALEAuditError, match="标签"):
        validate_label("attack")


def make_record(
    *,
    source: str,
    protocol: str = "tcp",
    src: str = "10.0.0.1",
    src_port: str = "12345",
    dst: str = "10.0.0.2",
    dst_port: str = "443",
    start_ts: float = 100.0,
    end_ts: float = 110.0,
    label: str = "0",
) -> FlowRecord:
    return FlowRecord(
        source=source,
        day_id=15,
        start_ts=start_ts,
        end_ts=end_ts,
        identity=FlowIdentity.from_values(
            protocol=protocol,
            src=src,
            src_port=src_port,
            dst=dst,
            dst_port=dst_port,
        ),
        label=label,
    )


def test_flow_identity_matches_numeric_and_text_protocols() -> None:
    zeek = make_record(source="zeek", protocol="tcp")
    cic = make_record(source="cic", protocol="6")

    assert zeek.identity == cic.identity


def test_associate_record_reports_unique_direct_start_match() -> None:
    zeek = make_record(source="zeek", start_ts=100.0, end_ts=110.0)
    cic = make_record(source="cic", start_ts=100.5, end_ts=108.0)

    decision = associate_record(cic, build_flow_index([zeek]), start_tolerance_seconds=1.0)

    assert decision == AssociationDecision(
        status="matched",
        direction="direct",
        basis="start_tolerance",
        candidate_count=1,
        start_delta_seconds=0.5,
        label_conflict=False,
    )


def test_associate_record_reports_unique_reverse_start_match() -> None:
    zeek = make_record(source="zeek", start_ts=100.0, end_ts=110.0)
    cic = make_record(
        source="cic",
        src="10.0.0.2",
        src_port="443",
        dst="10.0.0.1",
        dst_port="12345",
        start_ts=100.25,
        end_ts=109.0,
    )

    decision = associate_record(cic, build_flow_index([zeek]), start_tolerance_seconds=1.0)

    assert decision.direction == "reverse"
    assert decision.status == "matched"
    assert decision.start_delta_seconds == pytest.approx(0.25)


def test_associate_record_uses_unique_interval_overlap_after_start_tolerance() -> None:
    zeek = make_record(source="zeek", start_ts=100.0, end_ts=200.0)
    cic = make_record(source="cic", start_ts=150.0, end_ts=180.0)

    decision = associate_record(cic, build_flow_index([zeek]), start_tolerance_seconds=1.0)

    assert decision.status == "matched"
    assert decision.basis == "interval_overlap"
    assert decision.start_delta_seconds == pytest.approx(50.0)


def test_associate_record_rejects_non_overlapping_time_range() -> None:
    zeek = make_record(source="zeek", start_ts=100.0, end_ts=110.0)
    cic = make_record(source="cic", start_ts=120.0, end_ts=130.0)

    decision = associate_record(cic, build_flow_index([zeek]), start_tolerance_seconds=1.0)

    assert decision.status == "unmatched"
    assert decision.candidate_count == 0


def test_associate_record_reports_multiple_qualifying_candidates_as_ambiguous() -> None:
    first = make_record(source="zeek", start_ts=100.0, end_ts=110.0)
    second = make_record(source="zeek", start_ts=100.4, end_ts=112.0)
    cic = make_record(source="cic", start_ts=100.2, end_ts=109.0)

    decision = associate_record(
        cic,
        build_flow_index([first, second]),
        start_tolerance_seconds=1.0,
    )

    assert decision.status == "ambiguous"
    assert decision.direction == "direct"
    assert decision.candidate_count == 2
    assert decision.start_delta_seconds is None


def test_associate_record_prefers_unique_start_match_before_interval_overlap() -> None:
    long_lived = make_record(source="zeek", start_ts=50.0, end_ts=200.0)
    near_start = make_record(source="zeek", start_ts=100.0, end_ts=110.0)
    cic = make_record(source="cic", start_ts=100.2, end_ts=109.0)

    decision = associate_record(
        cic,
        build_flow_index([long_lived, near_start]),
        start_tolerance_seconds=1.0,
    )

    assert decision.status == "matched"
    assert decision.basis == "start_tolerance"
    assert decision.start_delta_seconds == pytest.approx(0.2)


def test_associate_record_reports_label_conflict_without_changing_labels() -> None:
    zeek = make_record(source="zeek", label="0")
    cic = make_record(source="cic", label="1")

    decision = associate_record(cic, build_flow_index([zeek]), start_tolerance_seconds=1.0)

    assert decision.status == "matched"
    assert decision.label_conflict is True
    assert zeek.label == "0"
    assert cic.label == "1"


def test_flow_record_excludes_same_named_uid_from_association_contract() -> None:
    assert "uid" not in FlowRecord.__dataclass_fields__


SHARED_FIELDS = (
    "date",
    "ts",
    "uid",
    "ip_src",
    "port_src",
    "ip_dst",
    "port_dst",
    "proto",
    "duration",
    "label",
    "step",
    "attack_step",
    "tactic",
    "technique",
    "comments",
)
DATASET_START = dt.datetime(2024, 12, 23, tzinfo=dt.timezone.utc)


def day_date(day_id: int) -> dt.date:
    return (DATASET_START + dt.timedelta(days=day_id - 1)).date()


def timestamp_text(timestamp: float) -> str:
    value = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
    return value.strftime("%Y-%m-%d %H:%M:%S.%f") + "000"


def flow_row(
    day_id: int,
    *,
    source: str,
    label: str = "0",
    reverse: bool = False,
    offset_seconds: float = 0.0,
    identity_suffix: str | None = None,
) -> dict[str, str]:
    suffix = identity_suffix or str(day_id)
    src = f"10.0.0.{suffix}"
    dst = "10.0.1.1"
    src_port = str(10000 + day_id)
    dst_port = "443"
    if reverse:
        src, dst = dst, src
        src_port, dst_port = dst_port, src_port
    timestamp = DATASET_START.timestamp() + (day_id - 1) * 86400 + 3600 + offset_seconds
    protocol = "tcp" if source == "zeek" else "6"
    return {
        "date": timestamp_text(timestamp),
        "ts": f"{timestamp:.6f}",
        "uid": f"{source}-uid-{day_id}-{offset_seconds}",
        "ip_src": src,
        "port_src": src_port,
        "ip_dst": dst,
        "port_dst": dst_port,
        "proto": protocol,
        "duration": "10.0",
        "label": label,
        "step": "1" if label != "0" else "0",
        "attack_step": "initial_access" if label != "0" else "benign",
        "tactic": "TA0001" if label != "0" else "",
        "technique": "T1566" if label != "0" else "",
        "comments": "测试攻击事件" if label != "0" else "",
    }


def write_zeek_day(root: Path, day_id: int, rows: list[dict[str, str]]) -> Path:
    directory = root / f"D{day_id}_{day_date(day_id).isoformat()}_output_orange_dmz_Zeek"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "conn_labeled.csv"
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=SHARED_FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_cic_zip(path: Path, rows_by_day: dict[int, list[dict[str, str]]]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for day_id, rows in sorted(rows_by_day.items()):
            member = (
                f"orange_dmz/D{day_id}_{day_date(day_id).isoformat()}_output_orange_dmz"
                ".pcap_Flow_labeled.csv"
            )
            buffer = io.StringIO(newline="")
            writer = csv.DictWriter(buffer, fieldnames=SHARED_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
            archive.writestr(member, buffer.getvalue())


def build_audit_fixture(tmp_path: Path) -> tuple[Path, Path]:
    zeek_root = tmp_path / "zeek"
    cic_rows: dict[int, list[dict[str, str]]] = {}
    for day_id in range(1, 29):
        zeek_label = "1" if day_id == 15 else "0"
        cic_label = "1" if day_id in {15, 18} else "0"
        zeek_rows = [flow_row(day_id, source="zeek", label=zeek_label)]
        cic_row = flow_row(
            day_id,
            source="cic",
            label=cic_label,
            reverse=day_id == 15,
        )
        if day_id == 16:
            zeek_rows.append(flow_row(day_id, source="zeek", offset_seconds=0.5))
            cic_row = flow_row(day_id, source="cic", offset_seconds=0.25)
        elif day_id == 17:
            cic_row = flow_row(
                day_id,
                source="cic",
                identity_suffix="unmatched",
            )
        write_zeek_day(zeek_root, day_id, zeek_rows)
        cic_rows[day_id] = [cic_row]
    cic_zip = tmp_path / "cic.zip"
    write_cic_zip(cic_zip, cic_rows)
    return zeek_root, cic_zip


def test_audit_dedale_reports_temporal_labels_and_association_without_identifiers(
    tmp_path: Path,
) -> None:
    zeek_root, cic_zip = build_audit_fixture(tmp_path)

    audit = audit_dedale(zeek_root, cic_zip, start_tolerance_seconds=1.0)

    assert audit["schema_version"] == "dedale_orange_dmz_audit_v1"
    assert audit["sources"]["zeek"]["file_count"] == 28
    assert audit["sources"]["zeek"]["row_count"] == 29
    assert audit["sources"]["zeek"]["stage_rows"] == {
        "calibration": 14,
        "test": 15,
    }
    assert audit["sources"]["cicflowmeter"]["row_count"] == 28
    assert audit["sources"]["cicflowmeter"]["stage_rows"] == {
        "calibration": 14,
        "test": 14,
    }
    assert audit["sources"]["cicflowmeter"]["label_rows"] == {
        "0": 26,
        "1": 2,
    }
    assert audit["sources"]["zeek"]["utc_mismatch_count"] == 0
    assert audit["sources"]["cicflowmeter"]["utc_mismatch_count"] == 0
    assert audit["sources"]["cicflowmeter"]["nonbenign_calibration_count"] == 0
    assert audit["sources"]["cicflowmeter"]["nonbenign_outside_attack_envelope_count"] == 0
    assert audit["association"] == {
        "ambiguous": 1,
        "cic_records_on_reused_zeek_targets": 0,
        "direct": 25,
        "interval_overlap": 0,
        "label_conflicts": 1,
        "matched_unique_zeek_records": 26,
        "matched": 26,
        "match_rate": pytest.approx(26 / 28),
        "max_cic_records_per_zeek_target": 1,
        "one_to_one_cic_records": 26,
        "reverse": 1,
        "start_tolerance": 26,
        "start_tolerance_seconds": 1.0,
        "total_cicflowmeter_rows": 28,
        "unmatched": 1,
        "zeek_targets_reused": 0,
    }
    serialized = json.dumps(audit, ensure_ascii=False)
    assert "zeek-uid" not in serialized
    assert "10.0.0." not in serialized
    assert audit["privacy"] == {
        "addresses_written": False,
        "ports_written": False,
        "raw_uids_written": False,
        "inferred_labels_written": False,
    }


def test_audit_dedale_rejects_date_and_timestamp_timezone_mismatch(tmp_path: Path) -> None:
    zeek_root, cic_zip = build_audit_fixture(tmp_path)
    first = flow_row(1, source="zeek")
    first["date"] = "2024-12-23 09:00:00.000000000"
    write_zeek_day(zeek_root, 1, [first])

    with pytest.raises(DEDALEAuditError, match="UTC"):
        audit_dedale(zeek_root, cic_zip, start_tolerance_seconds=1.0)


def test_build_input_manifest_hashes_all_read_only_inputs(tmp_path: Path) -> None:
    zeek_root, cic_zip = build_audit_fixture(tmp_path)

    manifest = build_input_manifest(zeek_root, cic_zip)

    assert manifest["schema_version"] == "dedale_orange_dmz_input_manifest_v1"
    assert manifest["cicflowmeter_zip"]["path"] == str(cic_zip)
    assert len(manifest["cicflowmeter_zip"]["sha256"]) == 64
    assert manifest["zeek"]["file_count"] == 28
    assert len(manifest["zeek"]["files"]) == 28
    assert all(len(item["sha256"]) == 64 for item in manifest["zeek"]["files"])


def test_audit_dedale_converts_cicflowmeter_microsecond_duration_before_boundaries(
    tmp_path: Path,
) -> None:
    zeek_root, cic_zip = build_audit_fixture(tmp_path)
    cic_rows = {
        day_id: [flow_row(day_id, source="cic", label="1" if day_id == 15 else "0")]
        for day_id in range(1, 29)
    }
    boundary_ts = dt.datetime(2025, 1, 6, tzinfo=dt.timezone.utc).timestamp()
    cic_rows[14][0]["ts"] = f"{boundary_ts - 10:.6f}"
    cic_rows[14][0]["date"] = timestamp_text(boundary_ts - 10)
    cic_rows[14][0]["duration"] = "5000000"
    write_cic_zip(cic_zip, cic_rows)

    audit = audit_dedale(zeek_root, cic_zip, start_tolerance_seconds=1.0)

    assert audit["sources"]["zeek"]["duration_unit"] == "seconds"
    assert audit["sources"]["cicflowmeter"]["duration_unit"] == "microseconds"
    assert audit["sources"]["cicflowmeter"]["crosses_calibration_test_boundary_count"] == 0


def test_audit_dedale_reports_multiple_cic_records_reusing_one_zeek_target(
    tmp_path: Path,
) -> None:
    zeek_root, cic_zip = build_audit_fixture(tmp_path)
    cic_rows = {
        day_id: [
            flow_row(
                day_id,
                source="cic",
                label="1" if day_id == 15 else "0",
            )
        ]
        for day_id in range(1, 29)
    }
    cic_rows[1].append(flow_row(1, source="cic", offset_seconds=0.1))
    write_zeek_day(zeek_root, 16, [flow_row(16, source="zeek")])
    write_cic_zip(cic_zip, cic_rows)

    audit = audit_dedale(zeek_root, cic_zip, start_tolerance_seconds=1.0)

    assert audit["association"]["matched"] == 29
    assert audit["association"]["matched_unique_zeek_records"] == 28
    assert audit["association"]["zeek_targets_reused"] == 1
    assert audit["association"]["cic_records_on_reused_zeek_targets"] == 2
    assert audit["association"]["one_to_one_cic_records"] == 27
    assert audit["association"]["max_cic_records_per_zeek_target"] == 2
