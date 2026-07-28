import ipaddress
import json
import struct
from collections import Counter
from hashlib import sha256
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from flow_probe.tqh_c2 import (
    MODEL_INPUT_FIELDS,
    MODEL_PACKET_FIELDS,
    FlowIdentity,
    PcapFrame,
    TQHC2Error,
    _canonical_origin_direction,
    audit_label_cell,
    audit_profile,
    build_parser,
    build_sample_id,
    extract_cell,
    iter_pcap,
    materialize_profile,
    parse_ip_packet,
)

CELL_NAMES = (
    "C_i30_j0",
    "C_i30_j30",
    "C_i30_j70",
    "C_i300_j0",
    "C_i300_j30",
    "C_i300_j70",
    "C_i1800_j0",
    "C_i1800_j30",
    "C_i1800_j70",
    "C_i3600_j0",
    "C_i3600_j30",
    "C_i3600_j70",
)
B_CELL_NAMES = tuple(name.replace("C_", "B_", 1) for name in CELL_NAMES)
VALID_FIXTURE_LABELS = (
    "malicious_c2",
    "malicious_lateral",
    "malicious_recon",
    "benign",
    "benign_external",
    "unknown",
)


def _cell_parts(cell_name: str) -> tuple[int, int]:
    interval_text, jitter_text = cell_name.split("_i", maxsplit=1)[1].split("_j", maxsplit=1)
    return int(interval_text), int(jitter_text)


def _tcp_frame(
    *,
    src: str,
    src_port: int,
    dst: str,
    dst_port: int,
    payload: bytes,
    flags: int,
) -> bytes:
    ethernet = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x08\x00"
    total_length = 20 + 20 + len(payload)
    ipv4 = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,
        0,
        total_length,
        1,
        0,
        64,
        6,
        0,
        ipaddress.IPv4Address(src).packed,
        ipaddress.IPv4Address(dst).packed,
    )
    tcp = struct.pack(
        "!HHIIBBHHH",
        src_port,
        dst_port,
        1,
        0,
        5 << 4,
        flags,
        65535,
        0,
        0,
    )
    return ethernet + ipv4 + tcp + payload


def _write_pcap(path: Path, frames: list[tuple[int, int, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as output:
        output.write(b"\xd4\xc3\xb2\xa1")
        output.write(struct.pack("<HHIIII", 2, 4, 0, 0, 262144, 1))
        for seconds, microseconds, frame in frames:
            output.write(struct.pack("<IIII", seconds, microseconds, len(frame), len(frame)))
            output.write(frame)


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def _write_cell(
    labels_root: Path,
    pcap_root: Path,
    cell_name: str,
    *,
    uid_suffix: str,
    official_c2_count: int | None = None,
    native_labels: list[str] | None = None,
    gate: dict[str, object] | None = None,
    invariant_violations: int | None = None,
    manifest_result: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    interval, jitter = _cell_parts(cell_name)
    profile = cell_name.split("_", maxsplit=1)[0]
    capture_id = f"fixture-{cell_name}"
    cell_dir = labels_root / profile / cell_name
    cell_dir.mkdir(parents=True)
    labels_to_write = native_labels or ["malicious_c2"]
    labels = []
    conn_records = []
    for index, native_label in enumerate(labels_to_write):
        uid = f"uid-{uid_suffix}" if len(labels_to_write) == 1 else f"uid-{uid_suffix}-{index}"
        label = {
            "ts": 1000.0 + index,
            "uid": uid,
            "orig_h": "10.0.0.1",
            "resp_h": "10.0.0.2",
            "orig_p": 12345 + index,
            "resp_p": 443,
            "proto": "tcp",
            "duration": 0.1,
            "orig_bytes": 5,
            "resp_bytes": 5,
            "orig_pkts": 1,
            "resp_pkts": 1,
            "conn_state": "SF",
            "history": "ShADadFf",
            "label": native_label,
            "capture_id": capture_id,
            "profile": profile,
            "framework": "fixture",
            "encryption_profile": "quic" if profile == "B" else "http_aes",
            "interval_s": interval,
            "jitter_pct": jitter,
        }
        labels.append(label)
        conn_records.append(
            {
                "ts": label["ts"],
                "uid": uid,
                "id.orig_h": label["orig_h"],
                "id.orig_p": label["orig_p"],
                "id.resp_h": label["resp_h"],
                "id.resp_p": label["resp_p"],
                "proto": label["proto"],
                "duration": label["duration"],
                "orig_pkts": 1,
                "resp_pkts": 1,
            }
        )
    _write_jsonl(cell_dir / "labeled.jsonl", labels)
    _write_jsonl(cell_dir / "conn.log", conn_records)
    manifest = {
        "capture_id": capture_id,
        "profile": profile,
        "framework": "fixture",
        "encryption_profile": "quic" if profile == "B" else "http_aes",
        "interval_s": interval,
        "jitter_pct": jitter,
    }
    if manifest_result is not None:
        manifest["result"] = manifest_result
    (cell_dir / "manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    gate_document = dict(gate or {"status": "PASS"})
    gate_document.setdefault("capture_id", capture_id)
    (cell_dir / "gate.json").write_text(json.dumps(gate_document) + "\n", encoding="utf-8")
    label_counts = Counter(labels_to_write)
    counts = {
        "flows_total": len(labels_to_write),
        **{
            f"flows_{native_label}": label_counts[native_label]
            for native_label in VALID_FIXTURE_LABELS
        },
    }
    if official_c2_count is not None:
        counts["flows_malicious_c2"] = official_c2_count
    if invariant_violations is not None:
        counts["invariant_violations"] = invariant_violations
    (cell_dir / "labeled.jsonl.counts.json").write_text(
        json.dumps(counts),
        encoding="utf-8",
    )

    request = _tcp_frame(
        src="10.0.0.1",
        src_port=12345,
        dst="10.0.0.2",
        dst_port=443,
        payload=b"hello",
        flags=0x18,
    )
    response = _tcp_frame(
        src="10.0.0.2",
        src_port=443,
        dst="10.0.0.1",
        dst_port=12345,
        payload=b"world",
        flags=0x18,
    )
    pcap_path = pcap_root / cell_name / f"{cell_name}.pcap"
    _write_pcap(pcap_path, [(1000, 0, request), (1000, 50_000, response)])
    return cell_dir, pcap_path


def _b_failed_gate(
    failed_checks: frozenset[str] = frozenset({"H1_c2_signal", "H3_balance", "H7_unknown_ratio"}),
) -> dict[str, object]:
    details = {
        "H1_c2_signal": "c2=15 (partial needs >= 50)",
        "H2_benign_vs_c2": "benign=0 need>=0.8*c2=12",
        "H3_balance": "positive_ratio=0.0138 target[0.4,0.6]",
        "H4_all_victims_present": "all present",
        "H5_benign_gen_active": "benign_gen_flows=133",
        "H6_no_invariant_violation": "violations=0",
        "H7_unknown_ratio": "unknown=1 ratio=0.0196 max<0.05",
    }
    return {
        "status": "FAIL",
        "checks": {
            name: {"pass": name not in failed_checks, "detail": detail}
            for name, detail in details.items()
        },
    }


def _write_b_exception_cell(
    labels_root: Path,
    pcap_root: Path,
    cell_name: str = "B_i30_j0",
    *,
    uid_suffix: str = "b-exception",
    c2_count: int = 50,
    unknown_count: int = 1,
    failed_checks: frozenset[str] = frozenset({"H1_c2_signal", "H3_balance", "H7_unknown_ratio"}),
) -> tuple[Path, Path]:
    native_labels = ["malicious_c2"] * c2_count + ["unknown"] * unknown_count
    revised_counts = Counter(native_labels)
    stale_result = {
        "status": "FAIL",
        "flows_total": len(native_labels),
        **{
            f"flows_{native_label}": revised_counts[native_label]
            for native_label in VALID_FIXTURE_LABELS
        },
    }
    stale_result["flows_malicious_c2"] = min(15, c2_count)
    return _write_cell(
        labels_root,
        pcap_root,
        cell_name,
        uid_suffix=uid_suffix,
        native_labels=native_labels,
        gate=_b_failed_gate(failed_checks),
        invariant_violations=0,
        manifest_result=stale_result,
    )


def test_audit_label_cell_recalculates_version_101_counts_from_flow_rows(tmp_path: Path) -> None:
    cell_dir, _pcap_path = _write_cell(
        tmp_path / "labels",
        tmp_path / "pcaps",
        "C_i30_j70",
        uid_suffix="count-difference",
        official_c2_count=2,
    )

    audit = audit_label_cell(cell_dir)

    assert audit["uid_join_rate"] == 1.0
    assert audit["uid_matches"] == 1
    assert audit["counts_difference"] == {"flows_malicious_c2": {"official": 2, "recalculated": 1}}


def test_audit_label_cell_rejects_missing_conn_uid(tmp_path: Path) -> None:
    cell_dir, _pcap_path = _write_cell(
        tmp_path / "labels",
        tmp_path / "pcaps",
        "C_i30_j0",
        uid_suffix="missing",
    )
    (cell_dir / "conn.log").write_text("", encoding="utf-8")

    with pytest.raises(TQHC2Error, match="UID 连接不完整"):
        audit_label_cell(cell_dir)


def test_audit_label_cell_rejects_failed_gate(tmp_path: Path) -> None:
    cell_dir, _pcap_path = _write_cell(
        tmp_path / "labels",
        tmp_path / "pcaps",
        "C_i30_j0",
        uid_suffix="failed-gate",
    )
    (cell_dir / "gate.json").write_text('{"status":"FAIL"}\n', encoding="utf-8")

    with pytest.raises(TQHC2Error, match="gate 未通过"):
        audit_label_cell(cell_dir)


def test_audit_label_cell_accepts_only_b_v101_revised_gate_after_full_audit(
    tmp_path: Path,
) -> None:
    cell_dir, _pcap_path = _write_b_exception_cell(tmp_path / "labels", tmp_path / "pcaps")

    audit = audit_label_cell(
        cell_dir,
        dataset_version="1.0.1",
        profile="B",
    )

    assert audit["source_gate_status"] == "FAIL"
    assert audit["source_gate_failed_checks"] == [
        "H1_c2_signal",
        "H3_balance",
        "H7_unknown_ratio",
    ]
    assert audit["source_gate_failed_check_details"] == {
        "H1_c2_signal": "c2=15 (partial needs >= 50)",
        "H3_balance": "positive_ratio=0.0138 target[0.4,0.6]",
        "H7_unknown_ratio": "unknown=1 ratio=0.0196 max<0.05",
    }
    assert audit["quality_acceptance"] == "accepted_b_v1_0_1_revised_counts"
    assert audit["quality_exception_reason"]
    assert audit["revised_counts_source"] == "labeled.jsonl.counts.json"
    assert audit["revised_counts_match_recalculated"] is True
    assert audit["stale_gate_manifest_counts_difference"] == {
        "flows_malicious_c2": {"revised": 50, "stale": 15}
    }
    assert audit["integrity_audit"] == {
        "five_tuple": "pass",
        "invariant": "pass",
        "label_legality": "pass",
        "metadata": "pass",
        "revised_counts": "pass",
        "uid": "pass",
    }


@pytest.mark.parametrize(
    ("dataset_version", "profile"),
    [
        (None, "B"),
        ("1.0.0", "B"),
        ("1.0.1", None),
        ("1.0.1", "C"),
    ],
)
def test_b_gate_exception_requires_explicit_v101_and_b_profile(
    tmp_path: Path,
    dataset_version: str | None,
    profile: str | None,
) -> None:
    cell_dir, _pcap_path = _write_b_exception_cell(tmp_path / "labels", tmp_path / "pcaps")

    with pytest.raises(TQHC2Error, match="仅允许 B v1.0.1"):
        audit_label_cell(
            cell_dir,
            dataset_version=dataset_version,
            profile=profile,
        )


def test_materialize_profile_and_cli_require_explicit_dataset_version(
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match="dataset_version"):
        materialize_profile(
            labels_root=tmp_path / "labels",
            pcap_root=tmp_path / "pcaps",
            profile="B",
            output_dir=tmp_path / "dataset-v1-provisional" / "missing-version",
        )

    parser = build_parser()
    with pytest.raises(SystemExit) as error:
        parser.parse_args(
            [
                "--profile",
                "B",
                "--pcap-root",
                str(tmp_path / "pcaps"),
                "--labels-root",
                str(tmp_path / "labels"),
                "--output",
                str(tmp_path / "dataset-v1-provisional" / "missing-cli-version"),
            ]
        )
    assert error.value.code == 2


@pytest.mark.parametrize("case", ["missing", "mismatch"])
def test_b_gate_exception_binds_gate_capture_id_to_cell(
    tmp_path: Path,
    case: str,
) -> None:
    cell_dir, _pcap_path = _write_b_exception_cell(tmp_path / "labels", tmp_path / "pcaps")
    gate_path = cell_dir / "gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if case == "missing":
        del gate["capture_id"]
    else:
        gate["capture_id"] = "fixture-B_i300_j0"
    gate_path.write_text(json.dumps(gate) + "\n", encoding="utf-8")

    with pytest.raises(TQHC2Error, match="gate capture_id"):
        audit_label_cell(cell_dir, dataset_version="1.0.1", profile="B")


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("missing_address", "非空字符串字段"),
        ("missing_protocol", "非空字符串字段"),
        ("invalid_ip", "不是有效 IP"),
        ("invalid_protocol", "传输协议不合法"),
        ("boolean_port", "端口必须是整数"),
        ("decimal_port", "端口必须是整数"),
        ("string_port", "端口必须是整数"),
        ("numeric_uid", "非空字符串字段"),
    ],
)
def test_b_gate_exception_rejects_incomplete_or_coerced_five_tuple(
    tmp_path: Path,
    case: str,
    expected: str,
) -> None:
    cell_dir, _pcap_path = _write_b_exception_cell(tmp_path / "labels", tmp_path / "pcaps")
    labels_path = cell_dir / "labeled.jsonl"
    conn_path = cell_dir / "conn.log"
    labels = [json.loads(line) for line in labels_path.read_text().splitlines()]
    conn_records = [json.loads(line) for line in conn_path.read_text().splitlines()]
    if case == "missing_address":
        del labels[0]["orig_h"]
        del conn_records[0]["id.orig_h"]
    elif case == "missing_protocol":
        del labels[0]["proto"]
        del conn_records[0]["proto"]
    elif case == "invalid_ip":
        labels[0]["orig_h"] = "not-an-ip"
        conn_records[0]["id.orig_h"] = "not-an-ip"
    elif case == "invalid_protocol":
        labels[0]["proto"] = "not-a-transport"
        conn_records[0]["proto"] = "not-a-transport"
    elif case == "numeric_uid":
        labels[0]["uid"] = 123
        conn_records[0]["uid"] = 123
    else:
        invalid_port: object = {
            "boolean_port": True,
            "decimal_port": 12345.5,
            "string_port": "12345",
        }[case]
        labels[0]["orig_p"] = invalid_port
        conn_records[0]["id.orig_p"] = invalid_port
    _write_jsonl(labels_path, labels)
    _write_jsonl(conn_path, conn_records)

    with pytest.raises(TQHC2Error, match=expected):
        audit_label_cell(cell_dir, dataset_version="1.0.1", profile="B")


@pytest.mark.parametrize(
    "case",
    [
        "unknown_failure",
        "missing_h2",
        "missing_h4",
        "h4_failed",
        "h5_failed",
        "h6_failed",
        "non_boolean_h4",
    ],
)
def test_b_gate_exception_rejects_unapproved_or_invalid_hard_checks(
    tmp_path: Path,
    case: str,
) -> None:
    cell_dir, _pcap_path = _write_b_exception_cell(tmp_path / "labels", tmp_path / "pcaps")
    gate_path = cell_dir / "gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    checks = gate["checks"]
    if case == "unknown_failure":
        checks["H8_unapproved"] = {"pass": False, "detail": "not approved"}
        expected = "失败项不在允许集合"
    elif case == "missing_h2":
        del checks["H2_benign_vs_c2"]
        expected = "缺少完整硬检查"
    elif case == "missing_h4":
        del checks["H4_all_victims_present"]
        expected = "缺少必须通过的硬检查"
    else:
        check_name = {
            "h4_failed": "H4_all_victims_present",
            "h5_failed": "H5_benign_gen_active",
            "h6_failed": "H6_no_invariant_violation",
            "non_boolean_h4": "H4_all_victims_present",
        }[case]
        checks[check_name]["pass"] = 1 if case == "non_boolean_h4" else False
        expected = "硬检查 pass 必须是布尔值" if case == "non_boolean_h4" else "失败项不在允许集合"
    gate_path.write_text(json.dumps(gate) + "\n", encoding="utf-8")

    with pytest.raises(TQHC2Error, match=expected):
        audit_label_cell(cell_dir, dataset_version="1.0.1", profile="B")


@pytest.mark.parametrize(
    "case",
    [
        "row_mismatch",
        "invariant_violation",
        "c2_below_minimum",
        "string_count",
        "unexpected_count_field",
    ],
)
def test_b_gate_exception_rejects_invalid_revised_counts(
    tmp_path: Path,
    case: str,
) -> None:
    c2_count = 49 if case == "c2_below_minimum" else 50
    cell_dir, _pcap_path = _write_b_exception_cell(
        tmp_path / "labels",
        tmp_path / "pcaps",
        c2_count=c2_count,
    )
    counts_path = cell_dir / "labeled.jsonl.counts.json"
    counts = json.loads(counts_path.read_text(encoding="utf-8"))
    if case == "row_mismatch":
        counts["flows_malicious_c2"] += 1
        expected = "修订计数与逐行重计不一致"
    elif case == "invariant_violation":
        counts["invariant_violations"] = 1
        expected = "invariant_violations 必须为 0"
    elif case == "string_count":
        counts["flows_malicious_c2"] = "50"
        expected = "修订计数字段必须是非负整数"
    elif case == "unexpected_count_field":
        counts["unexpected"] = 0
        expected = "修订计数字段集合不一致"
    else:
        expected = "flows_malicious_c2 不得低于 50"
    counts_path.write_text(json.dumps(counts) + "\n", encoding="utf-8")

    with pytest.raises(TQHC2Error, match=expected):
        audit_label_cell(cell_dir, dataset_version="1.0.1", profile="B")


@pytest.mark.parametrize(
    "case",
    ["illegal_label", "five_tuple_mismatch", "metadata_mismatch"],
)
def test_b_gate_exception_rejects_failed_row_integrity_audit(
    tmp_path: Path,
    case: str,
) -> None:
    cell_dir, _pcap_path = _write_b_exception_cell(tmp_path / "labels", tmp_path / "pcaps")
    if case == "illegal_label":
        labels_path = cell_dir / "labeled.jsonl"
        labels = [json.loads(line) for line in labels_path.read_text().splitlines()]
        labels[0]["label"] = "not_a_label"
        _write_jsonl(labels_path, labels)
        expected = "未知 TQH-C2 标签"
    elif case == "five_tuple_mismatch":
        conn_path = cell_dir / "conn.log"
        conn_records = [json.loads(line) for line in conn_path.read_text().splitlines()]
        conn_records[0]["id.orig_p"] = 9
        _write_jsonl(conn_path, conn_records)
        expected = "五元组不一致"
    else:
        labels_path = cell_dir / "labeled.jsonl"
        labels = [json.loads(line) for line in labels_path.read_text().splitlines()]
        labels[0]["profile"] = "A"
        _write_jsonl(labels_path, labels)
        expected = "标签元数据与 cell 不一致"

    with pytest.raises(TQHC2Error, match=expected):
        audit_label_cell(cell_dir, dataset_version="1.0.1", profile="B")


def test_b_gate_exception_propagates_to_profile_and_materialization(
    tmp_path: Path,
) -> None:
    labels_root = tmp_path / "labels"
    pcap_root = tmp_path / "pcaps"
    for index, cell_name in enumerate(B_CELL_NAMES):
        _write_b_exception_cell(
            labels_root,
            pcap_root,
            cell_name,
            uid_suffix=f"profile-{index}",
        )

    profile_audit = audit_profile(
        labels_root,
        pcap_root,
        "B",
        dataset_version="1.0.1",
    )
    output = tmp_path / "dataset-v1-provisional" / "tqh-c2-B-provisional"
    manifest = materialize_profile(
        labels_root=labels_root,
        pcap_root=pcap_root,
        profile="B",
        output_dir=output,
        dataset_version="1.0.1",
    )

    assert profile_audit["cell_count"] == 12
    assert {cell["quality_acceptance"] for cell in profile_audit["cells"]} == {
        "accepted_b_v1_0_1_revised_counts"
    }
    assert manifest["master_record_count"] == 612
    coverage = json.loads((output / "audit" / "label-coverage.json").read_text())
    assert coverage["label_status_counts"] == {"mapped": 600, "unresolved": 12}
    master = pq.read_table(output / "master_records.parquet").to_pylist()
    unknown_rows = [row for row in master if row["native_label"] == "unknown"]
    assert len(unknown_rows) == 12
    assert {row["binary_label"] for row in unknown_rows} == {None}
    assert {row["label_status"] for row in unknown_rows} == {"unresolved"}
    cell_audit = json.loads((output / "audit" / "cell-audit.json").read_text())
    assert {cell["source_gate_status"] for cell in cell_audit["cells"]} == {"FAIL"}


def test_parse_ip_packet_preserves_header_observations_without_identifiers() -> None:
    frame_bytes = _tcp_frame(
        src="10.0.0.1",
        src_port=12345,
        dst="10.0.0.2",
        dst_port=443,
        payload=b"hello",
        flags=0x18,
    )

    parsed = parse_ip_packet(
        PcapFrame(
            timestamp_ns=1_000_000_000,
            data=frame_bytes,
            original_length=len(frame_bytes),
            capture_truncated=False,
        )
    )

    assert parsed.status == "parsed"
    assert parsed.packet is not None
    assert parsed.packet.network_length_bytes == 45
    assert parsed.packet.payload_length_bytes == 5
    assert parsed.packet.tcp_flags == 0x18
    assert parsed.packet.identity.src == "10.0.0.1"
    assert parsed.packet.identity.dst_port == 443


def test_canonical_direction_does_not_depend_on_originator_role() -> None:
    forward = FlowIdentity("tcp", "10.0.0.1", 50000, "10.0.0.2", 443)
    reverse_origin = FlowIdentity("tcp", "10.0.0.2", 443, "10.0.0.1", 50000)

    assert _canonical_origin_direction(forward) == 1
    assert _canonical_origin_direction(reverse_origin) == -1


def test_parse_ip_packet_rejects_first_fragment_with_more_fragments() -> None:
    frame_bytes = bytearray(
        _tcp_frame(
            src="10.0.0.1",
            src_port=12345,
            dst="10.0.0.2",
            dst_port=443,
            payload=b"hello",
            flags=0x18,
        )
    )
    struct.pack_into("!H", frame_bytes, 14 + 6, 0x2000)

    parsed = parse_ip_packet(
        PcapFrame(
            timestamp_ns=1_000_000_000,
            data=bytes(frame_bytes),
            original_length=len(frame_bytes),
            capture_truncated=False,
        )
    )

    assert parsed.status == "fragment_without_transport"
    assert parsed.packet is None


def test_iter_pcap_rejects_truncated_record(tmp_path: Path) -> None:
    path = tmp_path / "truncated.pcap"
    path.write_bytes(
        b"\xd4\xc3\xb2\xa1"
        + struct.pack("<HHIIII", 2, 4, 0, 0, 262144, 1)
        + struct.pack("<IIII", 1, 0, 100, 100)
        + b"too-short"
    )

    with pytest.raises(TQHC2Error, match="数据截断"):
        list(iter_pcap(path))


def test_extract_cell_builds_direction_interval_burst_and_stable_sample_id(tmp_path: Path) -> None:
    cell_dir, pcap_path = _write_cell(
        tmp_path / "labels",
        tmp_path / "pcaps",
        "C_i30_j0",
        uid_suffix="extract",
    )
    packets: list[dict[str, object]] = []
    pcap_sha256 = sha256(pcap_path.read_bytes()).hexdigest()

    result = extract_cell(
        cell_dir=cell_dir,
        pcap_path=pcap_path,
        dataset_version="1.0.1",
        source_capture_sha256=pcap_sha256,
        extractor_contract_sha256="e" * 64,
        packet_sink=packets.extend,
    )

    assert len(result.master_records) == 1
    assert len(packets) == 2
    assert [packet["direction"] for packet in packets] == [1, -1]
    assert [packet["delta_time_us"] for packet in packets] == [0, 50_000]
    assert [packet["burst_id"] for packet in packets] == [0, 1]
    assert [packet["payload_length_bytes"] for packet in packets] == [5, 5]
    assert result.master_records[0]["packet_count_raw"] == 2
    assert result.master_records[0]["packet_count_kept"] == 2
    assert result.audit["join_rate"] == 1.0
    expected = build_sample_id(
        dataset_version="1.0.1",
        source_capture_sha256=pcap_sha256,
        extractor_contract_sha256="e" * 64,
        parent_session_id="uid-extract",
        window_start_ns=1_000_000_000_000,
        window_end_ns=1_000_100_000_000,
    )
    assert result.master_records[0]["sample_id"] == expected
    assert packets[0]["sample_id"] == expected
    assert tuple(packets[0]) == MODEL_PACKET_FIELDS
    assert "truncation_mask" in MODEL_PACKET_FIELDS
    assert "capture_truncated" not in MODEL_PACKET_FIELDS


def test_materialize_profile_writes_provisional_parquet_without_sensitive_fields(
    tmp_path: Path,
) -> None:
    labels_root = tmp_path / "labels"
    pcap_root = tmp_path / "pcaps"
    for index, cell_name in enumerate(CELL_NAMES):
        _write_cell(
            labels_root,
            pcap_root,
            cell_name,
            uid_suffix=str(index),
        )
    output = tmp_path / "dataset-v1-provisional" / "tqh-c2-C-provisional"

    manifest = materialize_profile(
        labels_root=labels_root,
        pcap_root=pcap_root,
        profile="C",
        output_dir=output,
        dataset_version="1.0.1",
    )

    assert manifest["status"] == "provisional"
    assert manifest["cell_count"] == 12
    assert manifest["master_record_count"] == 12
    assert manifest["packet_record_count"] == 24
    master = pq.read_table(output / "master_records.parquet")
    packets = pq.read_table(output / "views" / "packet_observations.parquet")
    assert master.num_rows == 12
    assert packets.num_rows == 24
    assert tuple(packets.schema.names) == MODEL_PACKET_FIELDS
    assert len(set(master.column("sample_id").to_pylist())) == 12
    leakage = json.loads((output / "audit" / "leakage-audit.json").read_text())
    assert leakage["status"] == "pass"
    assert leakage["sensitive_field_hits"] == []
    assert leakage["model_input_fields"] == list(MODEL_INPUT_FIELDS)
    assert "sample_id" not in leakage["model_input_fields"]
    schema = json.loads((output / "schema.provisional.json").read_text())
    assert schema["model_packet_field_roles"]["sample_id"] == "audit_only"
    assert not (output / "_INCOMPLETE").exists()
    coverage = json.loads((output / "audit" / "label-coverage.json").read_text())
    assert coverage["label_status_counts"] == {"mapped": 12}
    assert coverage["join_status_counts"] == {"matched_packets": 12}
    source_checksums = json.loads((output / "source_checksums.json").read_text())
    assert [item for item in source_checksums["files"] if item["role"] == "extractor_source"]
    artifact_checksums = json.loads((output / "artifact_checksums.provisional.json").read_text())
    for item in artifact_checksums["files"]:
        artifact_path = output / item["path"]
        assert artifact_path.stat().st_size == item["size_bytes"]
        assert sha256(artifact_path.read_bytes()).hexdigest() == item["sha256"]

    second_output = tmp_path / "dataset-v1-provisional" / "tqh-c2-C-repeat"
    materialize_profile(
        labels_root=labels_root,
        pcap_root=pcap_root,
        profile="C",
        output_dir=second_output,
        dataset_version="1.0.1",
    )
    for relative_path in (
        "master_records.parquet",
        "views/packet_observations.parquet",
    ):
        assert (
            sha256((output / relative_path).read_bytes()).digest()
            == sha256((second_output / relative_path).read_bytes()).digest()
        )


def test_materialize_profile_refuses_final_dataset_path(tmp_path: Path) -> None:
    with pytest.raises(TQHC2Error, match="provisional"):
        materialize_profile(
            labels_root=tmp_path / "labels",
            pcap_root=tmp_path / "pcaps",
            profile="C",
            output_dir=tmp_path / "dataset-v1",
            dataset_version="1.0.1",
        )


def test_materialize_profile_marks_failed_output_incomplete(tmp_path: Path) -> None:
    labels_root = tmp_path / "labels"
    pcap_root = tmp_path / "pcaps"
    (labels_root / "C").mkdir(parents=True)
    pcap_root.mkdir()
    output = tmp_path / "dataset-v1-provisional" / "tqh-c2-C-incomplete"

    with pytest.raises(TQHC2Error, match="12 个"):
        materialize_profile(
            labels_root=labels_root,
            pcap_root=pcap_root,
            profile="C",
            output_dir=output,
            dataset_version="1.0.1",
        )

    assert (output / "_INCOMPLETE").read_text() == '{"status":"incomplete"}\n'
