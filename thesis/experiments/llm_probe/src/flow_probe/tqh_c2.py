"""TQH-C2 标签连接审计与包级观测提取。"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import re
import struct
from collections import Counter, defaultdict
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATASET_ID = "TQH-C2"
VALID_LABELS = frozenset(
    {
        "malicious_c2",
        "malicious_lateral",
        "malicious_recon",
        "benign",
        "benign_external",
        "unknown",
    }
)
B_GATE_EXCEPTION_VERSION = "1.0.1"
B_GATE_ALLOWED_FAILURES = frozenset({"H1_c2_signal", "H3_balance", "H7_unknown_ratio"})
B_GATE_REQUIRED_PASSES = frozenset(
    {
        "H4_all_victims_present",
        "H5_benign_gen_active",
        "H6_no_invariant_violation",
    }
)
B_GATE_REQUIRED_CHECKS = B_GATE_ALLOWED_FAILURES | B_GATE_REQUIRED_PASSES | {"H2_benign_vs_c2"}
B_GATE_QUALITY_ACCEPTANCE = "accepted_b_v1_0_1_revised_counts"
B_GATE_EXCEPTION_REASON = (
    "B/QUIC v1.0.1 的逐流标签未变，修订计数与逐行重计一致；" "仅接受已批准的 H1/H3/H7 旧门禁失败。"
)
ROW_COUNT_FIELDS = (
    "flows_total",
    *(f"flows_{label}" for label in sorted(VALID_LABELS)),
)
REVISED_COUNT_FIELDS = (*ROW_COUNT_FIELDS, "invariant_violations")
CELL_PATTERN = re.compile(
    r"^(?P<profile>[ABC])_i(?P<interval>30|300|1800|3600)_j(?P<jitter>0|30|70)$"
)
MODEL_PACKET_FIELDS = (
    "sample_id",
    "packet_index",
    "relative_time_ns",
    "delta_time_us",
    "direction",
    "network_length_bytes",
    "payload_length_bytes",
    "transport_family",
    "tcp_flags",
    "burst_id",
    "is_first_packet",
    "payload_length_observed",
    "tcp_flags_applicable",
    "truncation_mask",
)
MODEL_INPUT_FIELDS = MODEL_PACKET_FIELDS[1:]
SENSITIVE_FIELD_TOKENS = frozenset(
    {
        "address",
        "capture",
        "cell",
        "config",
        "dataset",
        "encryption",
        "filename",
        "framework",
        "host",
        "ip",
        "label",
        "path",
        "port",
        "profile",
        "source",
        "topology",
        "uid",
    }
)
_PCAP_MAGIC = {
    b"\xd4\xc3\xb2\xa1": ("<", 1_000),
    b"\xa1\xb2\xc3\xd4": (">", 1_000),
    b"\x4d\x3c\xb2\xa1": ("<", 1),
    b"\xa1\xb2\x3c\x4d": (">", 1),
}
_TRANSPORT_NAMES = {1: "icmp", 6: "tcp", 17: "udp", 58: "icmp"}
_VALID_TRANSPORT_PROTOCOLS = frozenset(_TRANSPORT_NAMES.values())


class TQHC2Error(ValueError):
    """TQH-C2 输入或连接结果不满足冻结前审计要求。"""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _stable_hash(value: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def build_sample_id(
    *,
    dataset_version: str,
    source_capture_sha256: str,
    extractor_contract_sha256: str,
    parent_session_id: str,
    window_start_ns: int,
    window_end_ns: int,
    window_ordinal: int = 0,
) -> str:
    """按候选 data-protocol-v1.0 公式生成与标签和划分无关的主键。"""
    return _stable_hash(
        {
            "dataset_id": DATASET_ID,
            "dataset_version": dataset_version,
            "extractor_contract_sha256": extractor_contract_sha256,
            "parent_session_id": parent_session_id,
            "source_capture_sha256": source_capture_sha256,
            "window_end_ns": window_end_ns,
            "window_ordinal": window_ordinal,
            "window_start_ns": window_start_ns,
        }
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TQHC2Error(f"JSON 无法读取：{path}") from error
    if not isinstance(value, dict):
        raise TQHC2Error(f"JSON 顶层必须是对象：{path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise TQHC2Error(f"JSONL 记录必须是对象：{path}:{line_number}")
                records.append(value)
    except (OSError, json.JSONDecodeError) as error:
        raise TQHC2Error(f"JSONL 无法读取：{path}") from error
    return records


def _required_text(record: Mapping[str, Any], field_name: str, location: str) -> str:
    value = record.get(field_name)
    if type(value) is not str or not value.strip():
        raise TQHC2Error(f"缺少非空字符串字段 {field_name}：{location}")
    return value.strip()


def _port(value: object, location: str) -> int:
    if type(value) is not int:
        raise TQHC2Error(f"端口必须是整数：{location}")
    if not 0 <= value <= 65535:
        raise TQHC2Error(f"端口超出范围：{location}")
    return value


def _ip_text(record: Mapping[str, Any], field_name: str, location: str) -> str:
    value = _required_text(record, field_name, location)
    try:
        ipaddress.ip_address(value)
    except ValueError as error:
        raise TQHC2Error(f"地址不是有效 IP：{location}/{field_name}") from error
    return value


def _transport_protocol(record: Mapping[str, Any], field_name: str, location: str) -> str:
    value = _required_text(record, field_name, location).lower()
    if value not in _VALID_TRANSPORT_PROTOCOLS:
        raise TQHC2Error(f"传输协议不合法：{location}/{field_name}")
    return value


def _finite_float(value: object, location: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise TQHC2Error(f"数值无法解析：{location}") from error
    if not math.isfinite(number):
        raise TQHC2Error(f"数值必须有限：{location}")
    return number


def _parse_cell_name(cell_name: str) -> tuple[str, int, int]:
    match = CELL_PATTERN.fullmatch(cell_name)
    if match is None:
        raise TQHC2Error(f"TQH-C2 cell 名称无效：{cell_name}")
    return (
        match.group("profile"),
        int(match.group("interval")),
        int(match.group("jitter")),
    )


def _row_counts(records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    labels = Counter(str(record.get("label", "")) for record in records)
    return {
        "flows_total": len(records),
        **{f"flows_{label}": labels.get(label, 0) for label in sorted(VALID_LABELS)},
    }


def _counts_difference(
    official: Mapping[str, Any], recalculated: Mapping[str, int]
) -> dict[str, dict[str, int]]:
    differences: dict[str, dict[str, int]] = {}
    for field_name, actual in recalculated.items():
        try:
            expected = int(official.get(field_name, 0))
        except (TypeError, ValueError) as error:
            raise TQHC2Error(f"官方计数字段无法解析：{field_name}") from error
        if expected != actual:
            differences[field_name] = {"official": expected, "recalculated": actual}
    return differences


def _strict_count_values(
    counts: Mapping[str, Any],
    *,
    expected_fields: Sequence[str],
    location: str,
    require_exact_fields: bool,
) -> dict[str, int]:
    expected = set(expected_fields)
    actual = set(counts)
    if not expected.issubset(actual) or (require_exact_fields and actual != expected):
        raise TQHC2Error(
            f"{location}字段集合不一致：missing={sorted(expected - actual)} "
            f"unexpected={sorted(actual - expected)}"
        )
    validated: dict[str, int] = {}
    for field_name in expected_fields:
        value = counts[field_name]
        if type(value) is not int or value < 0:
            raise TQHC2Error(f"{location}字段必须是非负整数：{field_name}")
        validated[field_name] = value
    return validated


def _stale_revised_difference(
    stale: Mapping[str, int], revised: Mapping[str, int]
) -> dict[str, dict[str, int]]:
    return {
        field_name: {"revised": revised[field_name], "stale": stale[field_name]}
        for field_name in ROW_COUNT_FIELDS
        if stale[field_name] != revised[field_name]
    }


def _b_gate_exception_audit(
    *,
    cell_dir: Path,
    dataset_version: str | None,
    profile: str | None,
    manifest: Mapping[str, Any],
    gate: Mapping[str, Any],
    revised_counts: Mapping[str, Any],
    recalculated_counts: Mapping[str, int],
) -> dict[str, object]:
    cell_profile, _interval, _jitter = _parse_cell_name(cell_dir.name)
    if (
        type(dataset_version) is not str
        or dataset_version != B_GATE_EXCEPTION_VERSION
        or profile != "B"
        or cell_profile != "B"
        or manifest.get("profile") != "B"
    ):
        raise TQHC2Error("TQH-C2 B 受限例外仅允许 B v1.0.1，且必须显式声明版本与 profile")

    manifest_capture_id = _required_text(manifest, "capture_id", "manifest capture_id")
    gate_capture_id = _required_text(gate, "capture_id", "gate capture_id")
    if gate_capture_id != manifest_capture_id:
        raise TQHC2Error("gate capture_id 与 manifest、标签及当前 cell 身份不一致")

    checks = gate.get("checks")
    if not isinstance(checks, Mapping) or not checks:
        raise TQHC2Error("B 受限例外缺少 gate.json 硬检查对象")
    parsed_checks: dict[str, tuple[bool, str]] = {}
    for check_name, check in checks.items():
        if not isinstance(check_name, str) or not check_name:
            raise TQHC2Error("B 受限例外硬检查名称必须是非空字符串")
        if not isinstance(check, Mapping):
            raise TQHC2Error(f"B 受限例外硬检查必须是对象：{check_name}")
        passed = check.get("pass")
        if type(passed) is not bool:
            raise TQHC2Error(f"B 受限例外硬检查 pass 必须是布尔值：{check_name}")
        detail = check.get("detail")
        if not isinstance(detail, str) or not detail.strip():
            raise TQHC2Error(f"B 受限例外硬检查 detail 必须是非空字符串：{check_name}")
        parsed_checks[check_name] = (passed, detail)

    missing_required = sorted(B_GATE_REQUIRED_PASSES - parsed_checks.keys())
    if missing_required:
        raise TQHC2Error(f"B 受限例外缺少必须通过的硬检查：{', '.join(missing_required)}")
    missing_checks = sorted(B_GATE_REQUIRED_CHECKS - parsed_checks.keys())
    if missing_checks:
        raise TQHC2Error(f"B 受限例外缺少完整硬检查：{', '.join(missing_checks)}")
    failed_checks = sorted(
        check_name for check_name, (passed, _detail) in parsed_checks.items() if not passed
    )
    if not failed_checks:
        raise TQHC2Error("B 受限例外的失败硬检查集合不得为空")
    unapproved_failures = sorted(set(failed_checks) - B_GATE_ALLOWED_FAILURES)
    if unapproved_failures:
        raise TQHC2Error(f"B 受限例外失败项不在允许集合：{', '.join(unapproved_failures)}")
    required_not_passed = sorted(
        check_name
        for check_name in B_GATE_REQUIRED_PASSES
        if parsed_checks[check_name][0] is not True
    )
    if required_not_passed:
        raise TQHC2Error(f"B 受限例外硬检查必须明确通过：{', '.join(required_not_passed)}")

    validated_revised = _strict_count_values(
        revised_counts,
        expected_fields=REVISED_COUNT_FIELDS,
        location="B 受限例外修订计数",
        require_exact_fields=True,
    )
    if validated_revised["invariant_violations"] != 0:
        raise TQHC2Error("B 受限例外 invariant_violations 必须为 0")
    revised_row_counts = {
        field_name: validated_revised[field_name] for field_name in ROW_COUNT_FIELDS
    }
    if revised_row_counts != dict(recalculated_counts):
        raise TQHC2Error("B 受限例外修订计数与逐行重计不一致")
    if validated_revised["flows_malicious_c2"] < 50:
        raise TQHC2Error("B 受限例外 flows_malicious_c2 不得低于 50")

    manifest_result = manifest.get("result")
    if not isinstance(manifest_result, Mapping):
        raise TQHC2Error("B 受限例外 manifest 缺少旧 gate/manifest 计数")
    stale_counts = _strict_count_values(
        manifest_result,
        expected_fields=ROW_COUNT_FIELDS,
        location="B 受限例外旧 gate/manifest 计数",
        require_exact_fields=False,
    )
    return {
        "integrity_audit": {
            "five_tuple": "pass",
            "invariant": "pass",
            "label_legality": "pass",
            "metadata": "pass",
            "revised_counts": "pass",
            "uid": "pass",
        },
        "quality_acceptance": B_GATE_QUALITY_ACCEPTANCE,
        "quality_exception_reason": B_GATE_EXCEPTION_REASON,
        "revised_counts": validated_revised,
        "revised_counts_match_recalculated": True,
        "revised_counts_source": "labeled.jsonl.counts.json",
        "source_gate_failed_check_details": {
            check_name: parsed_checks[check_name][1] for check_name in failed_checks
        },
        "source_gate_failed_checks": failed_checks,
        "source_gate_status": "FAIL",
        "stale_gate_manifest_counts": stale_counts,
        "stale_gate_manifest_counts_difference": _stale_revised_difference(
            stale_counts,
            revised_row_counts,
        ),
    }


@dataclass(frozen=True, slots=True)
class FlowIdentity:
    """有向网络层与传输层身份，仅在内存中用于包关联。"""

    protocol: str
    src: str
    src_port: int
    dst: str
    dst_port: int

    def reverse(self) -> FlowIdentity:
        return FlowIdentity(
            protocol=self.protocol,
            src=self.dst,
            src_port=self.dst_port,
            dst=self.src,
            dst_port=self.src_port,
        )


def _canonical_origin_direction(identity: FlowIdentity) -> int:
    """按 IP 字节与端口的稳定顺序确定原始方向，避免使用会话角色。"""

    try:
        source_ip = ipaddress.ip_address(identity.src)
        destination_ip = ipaddress.ip_address(identity.dst)
    except ValueError as error:
        raise TQHC2Error(f"流端点不是有效 IP：{identity.src}/{identity.dst}") from error
    source = (source_ip.version, source_ip.packed, identity.src_port)
    destination = (destination_ip.version, destination_ip.packed, identity.dst_port)
    if source == destination:
        raise TQHC2Error("流的两个规范端点不能完全相同")
    return 1 if source < destination else -1


@dataclass(frozen=True, slots=True)
class FlowSession:
    uid: str
    sample_id: str
    start_ns: int
    end_ns: int
    identity: FlowIdentity
    label: str
    label_record: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class SessionReference:
    session: FlowSession
    direction: int


@dataclass(frozen=True, slots=True)
class PcapFrame:
    timestamp_ns: int
    data: bytes
    original_length: int
    capture_truncated: bool


@dataclass(frozen=True, slots=True)
class ParsedPacket:
    timestamp_ns: int
    protocol: str
    src: str
    src_port: int
    dst: str
    dst_port: int
    network_length_bytes: int
    payload_length_bytes: int | None
    tcp_flags: int | None
    capture_truncated: bool

    @property
    def identity(self) -> FlowIdentity:
        return FlowIdentity(
            protocol=self.protocol,
            src=self.src,
            src_port=self.src_port,
            dst=self.dst,
            dst_port=self.dst_port,
        )


@dataclass(frozen=True, slots=True)
class PacketParseResult:
    status: str
    packet: ParsedPacket | None


@dataclass(slots=True)
class _PacketState:
    packet_count: int = 0
    previous_timestamp_ns: int | None = None
    previous_direction: int | None = None
    burst_id: int = 0


@dataclass(slots=True)
class CellExtraction:
    master_records: list[dict[str, object]]
    audit: dict[str, object]
    source_files: list[dict[str, object]]


def _validate_cell_metadata(
    *,
    cell_name: str,
    manifest: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
) -> None:
    profile, interval, jitter = _parse_cell_name(cell_name)
    expected = {
        "profile": profile,
        "interval_s": interval,
        "jitter_pct": jitter,
    }
    for field_name, value in expected.items():
        if manifest.get(field_name) != value:
            raise TQHC2Error(f"manifest 与 cell 名称不一致：{cell_name}/{field_name}")
    capture_id = _required_text(manifest, "capture_id", str(cell_name))
    for row_number, record in enumerate(records, start=1):
        for field_name, value in expected.items():
            if record.get(field_name) != value:
                raise TQHC2Error(f"标签元数据与 cell 不一致：{cell_name}:{row_number}/{field_name}")
        if record.get("capture_id") != capture_id:
            raise TQHC2Error(f"标签 capture_id 不一致：{cell_name}:{row_number}")


def _essential_conn_values(record: Mapping[str, Any]) -> tuple[object, ...]:
    return (
        _ip_text(record, "id.orig_h", "conn.orig_h"),
        _port(record.get("id.orig_p"), "conn.orig_p"),
        _ip_text(record, "id.resp_h", "conn.resp_h"),
        _port(record.get("id.resp_p"), "conn.resp_p"),
        _transport_protocol(record, "proto", "conn.proto"),
    )


def _essential_label_values(record: Mapping[str, Any]) -> tuple[object, ...]:
    return (
        _ip_text(record, "orig_h", "label.orig_h"),
        _port(record.get("orig_p"), "label.orig_p"),
        _ip_text(record, "resp_h", "label.resp_h"),
        _port(record.get("resp_p"), "label.resp_p"),
        _transport_protocol(record, "proto", "label.proto"),
    )


def _load_cell_records(
    cell_dir: Path,
    *,
    dataset_version: str | None = None,
    profile: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, object]]:
    required = (
        "manifest.json",
        "conn.log",
        "labeled.jsonl",
        "labeled.jsonl.counts.json",
        "gate.json",
    )
    missing = [name for name in required if not (cell_dir / name).is_file()]
    if missing:
        raise TQHC2Error(f"cell 缺少文件 {', '.join(missing)}：{cell_dir}")

    manifest = _read_json(cell_dir / "manifest.json")
    gate = _read_json(cell_dir / "gate.json")
    gate_status = _required_text(gate, "status", str(cell_dir / "gate.json"))
    official_counts = _read_json(cell_dir / "labeled.jsonl.counts.json")
    labels = _read_jsonl(cell_dir / "labeled.jsonl")
    conn_records = _read_jsonl(cell_dir / "conn.log")
    if not labels:
        raise TQHC2Error(f"cell 标签为空：{cell_dir}")

    label_by_uid: dict[str, dict[str, Any]] = {}
    for row_number, record in enumerate(labels, start=1):
        uid = _required_text(record, "uid", f"{cell_dir}/labeled.jsonl:{row_number}")
        label = _required_text(record, "label", f"{cell_dir}/labeled.jsonl:{row_number}")
        if label not in VALID_LABELS:
            raise TQHC2Error(f"未知 TQH-C2 标签：{label}")
        if uid in label_by_uid:
            raise TQHC2Error(f"标签 UID 重复：{cell_dir}/{uid}")
        label_by_uid[uid] = record

    conn_by_uid: dict[str, dict[str, Any]] = {}
    for row_number, record in enumerate(conn_records, start=1):
        uid = _required_text(record, "uid", f"{cell_dir}/conn.log:{row_number}")
        if uid in conn_by_uid:
            raise TQHC2Error(f"conn UID 重复：{cell_dir}/{uid}")
        conn_by_uid[uid] = record

    missing_labels = sorted(conn_by_uid.keys() - label_by_uid.keys())
    missing_conn = sorted(label_by_uid.keys() - conn_by_uid.keys())
    if missing_labels or missing_conn:
        raise TQHC2Error(
            f"UID 连接不完整：{cell_dir} missing_labels={len(missing_labels)} "
            f"missing_conn={len(missing_conn)}"
        )

    connection_mismatches = 0
    for uid, label_record in label_by_uid.items():
        if _essential_label_values(label_record) != _essential_conn_values(conn_by_uid[uid]):
            connection_mismatches += 1
    if connection_mismatches:
        raise TQHC2Error(f"UID 连接后的五元组不一致：{cell_dir}/{connection_mismatches}")

    _validate_cell_metadata(cell_name=cell_dir.name, manifest=manifest, records=labels)
    recalculated_counts = _row_counts(labels)
    counts_difference = _counts_difference(official_counts, recalculated_counts)
    if gate_status == "PASS":
        quality_audit: dict[str, object] = {
            "quality_acceptance": "strict_source_gate_pass",
            "quality_exception_reason": None,
            "revised_counts_match_recalculated": not counts_difference,
            "revised_counts_source": None,
            "source_gate_failed_check_details": {},
            "source_gate_failed_checks": [],
            "source_gate_status": "PASS",
            "stale_gate_manifest_counts_difference": {},
        }
    elif gate_status == "FAIL":
        cell_profile, _interval, _jitter = _parse_cell_name(cell_dir.name)
        if cell_profile != "B" or manifest.get("profile") != "B":
            raise TQHC2Error(f"cell gate 未通过：{cell_dir}/{gate_status}")
        quality_audit = _b_gate_exception_audit(
            cell_dir=cell_dir,
            dataset_version=dataset_version,
            profile=profile,
            manifest=manifest,
            gate=gate,
            revised_counts=official_counts,
            recalculated_counts=recalculated_counts,
        )
    else:
        raise TQHC2Error(f"cell gate 未通过：{cell_dir}/{gate_status}")
    audit = {
        **quality_audit,
        "capture_id": manifest["capture_id"],
        "cell": cell_dir.name,
        "conn_rows": len(conn_records),
        "counts_difference": counts_difference,
        "gate_status": gate_status,
        "label_counts": recalculated_counts,
        "label_rows": len(labels),
        "uid_join_rate": 1.0,
        "uid_matches": len(labels),
        "uid_missing_conn": 0,
        "uid_missing_label": 0,
    }
    return labels, audit


def audit_label_cell(
    cell_dir: Path,
    *,
    dataset_version: str | None = None,
    profile: str | None = None,
) -> dict[str, object]:
    """独立复核单个 cell 的 UID、标签计数和元数据一致性。"""
    _records, audit = _load_cell_records(
        Path(cell_dir),
        dataset_version=dataset_version,
        profile=profile,
    )
    return audit


def _pcap_for_cell(pcap_root: Path, cell_name: str) -> Path:
    pcaps = sorted((pcap_root / cell_name).glob("*.pcap"))
    if len(pcaps) != 1:
        raise TQHC2Error(f"cell 必须且只能对应一个 PCAP：{cell_name}/{len(pcaps)}")
    return pcaps[0]


def _profile_cell_names(root: Path, profile: str) -> list[str]:
    names = []
    for path in Path(root).iterdir():
        if not path.is_dir():
            continue
        match = CELL_PATTERN.fullmatch(path.name)
        if match is not None and match.group("profile") == profile:
            names.append(path.name)
    return sorted(names)


def audit_profile(
    labels_root: Path,
    pcap_root: Path,
    profile: str,
    *,
    dataset_version: str | None = None,
) -> dict[str, object]:
    """复核一个 profile 的 12 个标签 cell 与 12 个 PCAP cell 一一对应。"""
    if profile not in {"A", "B", "C"}:
        raise TQHC2Error(f"未知 TQH-C2 profile：{profile}")
    labels_profile = Path(labels_root) / profile
    label_cells = _profile_cell_names(labels_profile, profile)
    pcap_cells = _profile_cell_names(Path(pcap_root), profile)
    if label_cells != pcap_cells:
        raise TQHC2Error(
            f"标签与 PCAP cell 集合不同：labels={len(label_cells)} pcaps={len(pcap_cells)}"
        )
    if len(label_cells) != 12:
        raise TQHC2Error(f"profile {profile} 必须包含 12 个 cell：{len(label_cells)}")

    cells = []
    label_rows = 0
    counts_difference_cells = 0
    for cell_name in label_cells:
        _pcap_for_cell(Path(pcap_root), cell_name)
        audit = audit_label_cell(
            labels_profile / cell_name,
            dataset_version=dataset_version,
            profile=profile,
        )
        cells.append(audit)
        label_rows += int(audit["label_rows"])
        counts_difference_cells += bool(audit["counts_difference"])
    return {
        "cell_count": len(cells),
        "cells": cells,
        "counts_difference_cells": counts_difference_cells,
        "label_rows": label_rows,
        "profile": profile,
        "uid_join_rate": 1.0,
    }


def iter_pcap(path: Path) -> Iterator[PcapFrame]:
    """流式读取经典 PCAP；不接受 PCAPNG 或非以太网链路类型。"""
    path = Path(path)
    with path.open("rb") as source:
        magic = source.read(4)
        format_info = _PCAP_MAGIC.get(magic)
        if format_info is None:
            raise TQHC2Error(f"不是受支持的经典 PCAP：{path}")
        endian, fractional_nanoseconds = format_info
        rest = source.read(20)
        if len(rest) != 20:
            raise TQHC2Error(f"PCAP 全局头截断：{path}")
        major, minor, _zone, _sigfigs, snaplen, network = struct.unpack(f"{endian}HHIIII", rest)
        if (major, minor) != (2, 4):
            raise TQHC2Error(f"PCAP 版本不受支持：{major}.{minor}")
        if network != 1:
            raise TQHC2Error(f"PCAP 链路类型必须是 Ethernet：{network}")
        if snaplen <= 0:
            raise TQHC2Error(f"PCAP snaplen 无效：{snaplen}")

        while True:
            record_header = source.read(16)
            if not record_header:
                return
            if len(record_header) != 16:
                raise TQHC2Error(f"PCAP 记录头截断：{path}")
            seconds, fraction, captured_length, original_length = struct.unpack(
                f"{endian}IIII", record_header
            )
            fraction_limit = 1_000_000_000 if fractional_nanoseconds == 1 else 1_000_000
            if fraction >= fraction_limit:
                raise TQHC2Error(f"PCAP 时间戳小数部分无效：{path}")
            if captured_length > snaplen:
                raise TQHC2Error(f"PCAP 记录超过 snaplen：{path}")
            if original_length < captured_length:
                raise TQHC2Error(f"PCAP 原始长度小于捕获长度：{path}")
            data = source.read(captured_length)
            if len(data) != captured_length:
                raise TQHC2Error(f"PCAP 记录数据截断：{path}")
            yield PcapFrame(
                timestamp_ns=seconds * 1_000_000_000 + fraction * fractional_nanoseconds,
                data=data,
                original_length=original_length,
                capture_truncated=captured_length < original_length,
            )


def _transport_packet(
    *,
    frame: PcapFrame,
    protocol_number: int,
    src: str,
    dst: str,
    transport_offset: int,
    transport_length: int,
    network_length: int,
) -> PacketParseResult:
    protocol = _TRANSPORT_NAMES.get(protocol_number)
    if protocol is None:
        return PacketParseResult(status="unsupported_transport", packet=None)
    data = frame.data
    if protocol == "tcp":
        if transport_length < 20 or len(data) < transport_offset + 20:
            return PacketParseResult(status="malformed", packet=None)
        src_port, dst_port = struct.unpack_from("!HH", data, transport_offset)
        header_length = (data[transport_offset + 12] >> 4) * 4
        if header_length < 20 or header_length > transport_length:
            return PacketParseResult(status="malformed", packet=None)
        flags = ((data[transport_offset + 12] & 1) << 8) | data[transport_offset + 13]
        payload_length = transport_length - header_length
    elif protocol == "udp":
        if transport_length < 8 or len(data) < transport_offset + 8:
            return PacketParseResult(status="malformed", packet=None)
        src_port, dst_port, udp_length = struct.unpack_from("!HHH", data, transport_offset)
        if udp_length < 8 or udp_length > transport_length:
            return PacketParseResult(status="malformed", packet=None)
        flags = None
        payload_length = udp_length - 8
    else:
        if transport_length < 2 or len(data) < transport_offset + 2:
            return PacketParseResult(status="malformed", packet=None)
        icmp_type, icmp_code = struct.unpack_from("!BB", data, transport_offset)
        src_port, dst_port = icmp_type, icmp_code
        flags = None
        payload_length = max(transport_length - 8, 0)

    return PacketParseResult(
        status="parsed",
        packet=ParsedPacket(
            timestamp_ns=frame.timestamp_ns,
            protocol=protocol,
            src=src,
            src_port=src_port,
            dst=dst,
            dst_port=dst_port,
            network_length_bytes=network_length,
            payload_length_bytes=payload_length,
            tcp_flags=flags,
            capture_truncated=frame.capture_truncated,
        ),
    )


def _parse_ipv4(frame: PcapFrame, offset: int) -> PacketParseResult:
    data = frame.data
    if len(data) < offset + 20:
        return PacketParseResult(status="malformed", packet=None)
    version_ihl = data[offset]
    if version_ihl >> 4 != 4:
        return PacketParseResult(status="malformed", packet=None)
    header_length = (version_ihl & 0x0F) * 4
    if header_length < 20 or len(data) < offset + header_length:
        return PacketParseResult(status="malformed", packet=None)
    total_length = struct.unpack_from("!H", data, offset + 2)[0]
    if total_length < header_length:
        return PacketParseResult(status="malformed", packet=None)
    fragment = struct.unpack_from("!H", data, offset + 6)[0]
    if fragment & 0x3FFF:
        return PacketParseResult(status="fragment_without_transport", packet=None)
    protocol_number = data[offset + 9]
    src = str(ipaddress.IPv4Address(data[offset + 12 : offset + 16]))
    dst = str(ipaddress.IPv4Address(data[offset + 16 : offset + 20]))
    return _transport_packet(
        frame=frame,
        protocol_number=protocol_number,
        src=src,
        dst=dst,
        transport_offset=offset + header_length,
        transport_length=total_length - header_length,
        network_length=total_length,
    )


def _parse_ipv6(frame: PcapFrame, offset: int) -> PacketParseResult:
    data = frame.data
    if len(data) < offset + 40 or data[offset] >> 4 != 6:
        return PacketParseResult(status="malformed", packet=None)
    payload_length = struct.unpack_from("!H", data, offset + 4)[0]
    next_header = data[offset + 6]
    src = str(ipaddress.IPv6Address(data[offset + 8 : offset + 24]))
    dst = str(ipaddress.IPv6Address(data[offset + 24 : offset + 40]))
    transport_offset = offset + 40
    remaining = payload_length

    while next_header in {0, 43, 44, 51, 60}:
        if next_header == 44:
            if remaining < 8 or len(data) < transport_offset + 8:
                return PacketParseResult(status="malformed", packet=None)
            following = data[transport_offset]
            fragment = struct.unpack_from("!H", data, transport_offset + 2)[0]
            if fragment & 0xFFF9:
                return PacketParseResult(status="fragment_without_transport", packet=None)
            extension_length = 8
        elif next_header == 51:
            if remaining < 2 or len(data) < transport_offset + 2:
                return PacketParseResult(status="malformed", packet=None)
            following = data[transport_offset]
            extension_length = (data[transport_offset + 1] + 2) * 4
        else:
            if remaining < 2 or len(data) < transport_offset + 2:
                return PacketParseResult(status="malformed", packet=None)
            following = data[transport_offset]
            extension_length = (data[transport_offset + 1] + 1) * 8
        if extension_length > remaining or len(data) < transport_offset + extension_length:
            return PacketParseResult(status="malformed", packet=None)
        next_header = following
        transport_offset += extension_length
        remaining -= extension_length

    return _transport_packet(
        frame=frame,
        protocol_number=next_header,
        src=src,
        dst=dst,
        transport_offset=transport_offset,
        transport_length=remaining,
        network_length=40 + payload_length,
    )


def parse_ip_packet(frame: PcapFrame) -> PacketParseResult:
    """解析以太网中的 IP 包并返回可连接的公开头部观测。"""
    data = frame.data
    if len(data) < 14:
        return PacketParseResult(status="malformed", packet=None)
    ethertype = struct.unpack_from("!H", data, 12)[0]
    offset = 14
    while ethertype in {0x8100, 0x88A8, 0x9100}:
        if len(data) < offset + 4:
            return PacketParseResult(status="malformed", packet=None)
        ethertype = struct.unpack_from("!H", data, offset + 2)[0]
        offset += 4
    if ethertype == 0x0800:
        return _parse_ipv4(frame, offset)
    if ethertype == 0x86DD:
        return _parse_ipv6(frame, offset)
    return PacketParseResult(status="non_ip", packet=None)


def _label_to_session(
    *,
    record: Mapping[str, Any],
    dataset_version: str,
    pcap_sha256: str,
    extractor_sha256: str,
) -> FlowSession:
    uid = _required_text(record, "uid", "labeled.jsonl")
    start = _finite_float(record.get("ts"), f"{uid}/ts")
    duration = _finite_float(record.get("duration", 0.0) or 0.0, f"{uid}/duration")
    if duration < 0:
        raise TQHC2Error(f"流时长不能为负：{uid}")
    start_ns = int(round(start * 1_000_000_000))
    end_ns = start_ns + int(round(duration * 1_000_000_000))
    identity = FlowIdentity(
        protocol=_required_text(record, "proto", uid).lower(),
        src=_required_text(record, "orig_h", uid),
        src_port=_port(record.get("orig_p"), f"{uid}/orig_p"),
        dst=_required_text(record, "resp_h", uid),
        dst_port=_port(record.get("resp_p"), f"{uid}/resp_p"),
    )
    sample_id = build_sample_id(
        dataset_version=dataset_version,
        source_capture_sha256=pcap_sha256,
        extractor_contract_sha256=extractor_sha256,
        parent_session_id=uid,
        window_start_ns=start_ns,
        window_end_ns=end_ns,
    )
    return FlowSession(
        uid=uid,
        sample_id=sample_id,
        start_ns=start_ns,
        end_ns=end_ns,
        identity=identity,
        label=_required_text(record, "label", uid),
        label_record=record,
    )


def _session_index(sessions: Sequence[FlowSession]) -> dict[FlowIdentity, list[SessionReference]]:
    index: defaultdict[FlowIdentity, list[SessionReference]] = defaultdict(list)
    for session in sessions:
        origin_direction = _canonical_origin_direction(session.identity)
        index[session.identity].append(
            SessionReference(session=session, direction=origin_direction)
        )
        index[session.identity.reverse()].append(
            SessionReference(session=session, direction=-origin_direction)
        )
    for values in index.values():
        values.sort(key=lambda item: (item.session.start_ns, item.session.end_ns, item.session.uid))
    return dict(index)


def _match_packet(
    packet: ParsedPacket,
    index: Mapping[FlowIdentity, Sequence[SessionReference]],
    tolerance_ns: int,
) -> tuple[str, SessionReference | None]:
    candidates = [
        reference
        for reference in index.get(packet.identity, ())
        if reference.session.start_ns - tolerance_ns
        <= packet.timestamp_ns
        <= reference.session.end_ns + tolerance_ns
    ]
    unique = {(reference.session.uid, reference.direction): reference for reference in candidates}
    if not unique:
        return "unmatched", None
    if len(unique) != 1:
        return "ambiguous", None
    return "matched", next(iter(unique.values()))


def _binary_label(native_label: str) -> tuple[str | None, str]:
    if native_label == "malicious_c2":
        return "malicious", "mapped"
    if native_label in {"benign", "benign_external"}:
        return "benign", "mapped"
    if native_label in {"malicious_lateral", "malicious_recon"}:
        return None, "auxiliary"
    return None, "unresolved"


def _raw_packet_count(record: Mapping[str, Any]) -> int:
    total = 0
    for field_name in ("orig_pkts", "resp_pkts"):
        value = record.get(field_name, 0) or 0
        try:
            total += int(value)
        except (TypeError, ValueError) as error:
            raise TQHC2Error(f"包数无法解析：{record.get('uid')}/{field_name}") from error
    return total


def _master_record(
    *,
    session: FlowSession,
    dataset_version: str,
    pcap_sha256: str,
    extractor_sha256: str,
    cell_name: str,
    packet_count: int,
) -> dict[str, object]:
    binary_label, label_status = _binary_label(session.label)
    label_record = session.label_record
    source_artifact_id = _stable_hash(
        {
            "dataset_id": DATASET_ID,
            "dataset_version": dataset_version,
            "source_capture_sha256": pcap_sha256,
        }
    )
    allocation_group_id = _stable_hash(
        {
            "dataset_version": dataset_version,
            "interval_s": int(label_record["interval_s"]),
            "jitter_pct": int(label_record["jitter_pct"]),
            "profile": str(label_record["profile"]),
            "source_capture_sha256": pcap_sha256,
        }
    )
    record = {
        "sample_id": session.sample_id,
        "dataset_id": DATASET_ID,
        "dataset_version": dataset_version,
        "source_artifact_id": source_artifact_id,
        "source_capture_sha256": pcap_sha256,
        "extractor_contract_sha256": extractor_sha256,
        "allocation_group_id": allocation_group_id,
        "parent_session_id": session.uid,
        "capture_group_id": cell_name,
        "sample_unit": "full_flow",
        "window_start_ns": session.start_ns,
        "window_end_ns": session.end_ns,
        "window_ordinal": 0,
        "packet_count_raw": _raw_packet_count(label_record),
        "packet_count_kept": packet_count,
        "native_label": session.label,
        "binary_label": binary_label,
        "family_label": "c2" if session.label == "malicious_c2" else None,
        "subtype_label": None,
        "label_status": label_status,
        "unknown_role": "not_applicable",
        "profile": str(label_record["profile"]),
        "interval_s": int(label_record["interval_s"]),
        "jitter_pct": int(label_record["jitter_pct"]),
        "capture_id": str(label_record["capture_id"]),
        "join_status": "matched_packets" if packet_count else "label_only_no_packets",
    }
    record["record_sha256"] = _stable_hash(record)
    return record


def extract_cell(
    *,
    cell_dir: Path,
    pcap_path: Path,
    dataset_version: str,
    profile: str | None = None,
    source_capture_sha256: str,
    extractor_contract_sha256: str,
    packet_sink: Callable[[list[dict[str, object]]], None],
    packet_batch_size: int = 65_536,
    time_tolerance_ns: int = 1_000_000,
) -> CellExtraction:
    """流式提取单个 cell，并把无敏感字段包记录分批交给写入器。"""
    if packet_batch_size <= 0:
        raise TQHC2Error("packet_batch_size 必须为正数")
    labels, label_audit = _load_cell_records(
        Path(cell_dir),
        dataset_version=dataset_version,
        profile=profile,
    )
    sessions = [
        _label_to_session(
            record=record,
            dataset_version=dataset_version,
            pcap_sha256=source_capture_sha256,
            extractor_sha256=extractor_contract_sha256,
        )
        for record in labels
    ]
    index = _session_index(sessions)
    states = {session.uid: _PacketState() for session in sessions}
    audit_counts: Counter[str] = Counter()
    packet_batch: list[dict[str, object]] = []

    for frame in iter_pcap(Path(pcap_path)):
        audit_counts["pcap_frames"] += 1
        parsed = parse_ip_packet(frame)
        audit_counts[f"parse_{parsed.status}"] += 1
        if parsed.packet is None:
            continue
        audit_counts["eligible_packets"] += 1
        status, reference = _match_packet(parsed.packet, index, time_tolerance_ns)
        audit_counts[f"join_{status}"] += 1
        if reference is None:
            continue

        session = reference.session
        state = states[session.uid]
        first_packet = state.previous_timestamp_ns is None
        if first_packet:
            delta_time_us = 0
            relative_time_ns = max(parsed.packet.timestamp_ns - session.start_ns, 0)
        else:
            raw_delta = parsed.packet.timestamp_ns - int(state.previous_timestamp_ns)
            if raw_delta < 0:
                audit_counts["negative_packet_delta"] += 1
            delta_time_us = max(raw_delta, 0) // 1_000
            relative_time_ns = max(parsed.packet.timestamp_ns - session.start_ns, 0)
            if reference.direction != state.previous_direction:
                state.burst_id += 1

        packet_batch.append(
            {
                "sample_id": session.sample_id,
                "packet_index": state.packet_count,
                "relative_time_ns": relative_time_ns,
                "delta_time_us": delta_time_us,
                "direction": reference.direction,
                "network_length_bytes": parsed.packet.network_length_bytes,
                "payload_length_bytes": parsed.packet.payload_length_bytes,
                "transport_family": parsed.packet.protocol.upper(),
                "tcp_flags": parsed.packet.tcp_flags,
                "burst_id": state.burst_id,
                "is_first_packet": first_packet,
                "payload_length_observed": parsed.packet.payload_length_bytes is not None,
                "tcp_flags_applicable": parsed.packet.protocol == "tcp",
                "truncation_mask": parsed.packet.capture_truncated,
            }
        )
        state.packet_count += 1
        state.previous_timestamp_ns = parsed.packet.timestamp_ns
        state.previous_direction = reference.direction
        if len(packet_batch) >= packet_batch_size:
            packet_sink(packet_batch)
            packet_batch = []
    if packet_batch:
        packet_sink(packet_batch)

    master_records = [
        _master_record(
            session=session,
            dataset_version=dataset_version,
            pcap_sha256=source_capture_sha256,
            extractor_sha256=extractor_contract_sha256,
            cell_name=Path(cell_dir).name,
            packet_count=states[session.uid].packet_count,
        )
        for session in sessions
    ]
    matched_sessions = sum(state.packet_count > 0 for state in states.values())
    audit = {
        **label_audit,
        "eligible_packets": audit_counts["eligible_packets"],
        "join_ambiguous": audit_counts["join_ambiguous"],
        "join_matched": audit_counts["join_matched"],
        "join_rate": (
            audit_counts["join_matched"] / audit_counts["eligible_packets"]
            if audit_counts["eligible_packets"]
            else 0.0
        ),
        "join_unmatched": audit_counts["join_unmatched"],
        "matched_sessions": matched_sessions,
        "negative_packet_delta": audit_counts["negative_packet_delta"],
        "parse_status": {
            key.removeprefix("parse_"): value
            for key, value in sorted(audit_counts.items())
            if key.startswith("parse_")
        },
        "pcap_frames": audit_counts["pcap_frames"],
        "sessions_without_packets": len(sessions) - matched_sessions,
    }
    source_files = [
        {
            "path": str(Path(pcap_path)),
            "role": "source_pcap",
            "sha256": source_capture_sha256,
            "size_bytes": Path(pcap_path).stat().st_size,
        }
    ]
    for filename in (
        "manifest.json",
        "conn.log",
        "labeled.jsonl",
        "labeled.jsonl.counts.json",
        "gate.json",
    ):
        path = Path(cell_dir) / filename
        source_files.append(
            {
                "path": str(path),
                "role": "label_or_audit_source",
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return CellExtraction(
        master_records=master_records,
        audit=audit,
        source_files=source_files,
    )


def _packet_schema() -> Any:
    try:
        import pyarrow as pa
    except ImportError as error:
        raise TQHC2Error("写入 Parquet 需要项目依赖 pyarrow") from error
    return pa.schema(
        [
            ("sample_id", pa.string()),
            ("packet_index", pa.int32()),
            ("relative_time_ns", pa.int64()),
            ("delta_time_us", pa.int64()),
            ("direction", pa.int8()),
            ("network_length_bytes", pa.int32()),
            ("payload_length_bytes", pa.int32()),
            ("transport_family", pa.string()),
            ("tcp_flags", pa.int16()),
            ("burst_id", pa.int32()),
            ("is_first_packet", pa.bool_()),
            ("payload_length_observed", pa.bool_()),
            ("tcp_flags_applicable", pa.bool_()),
            ("truncation_mask", pa.bool_()),
        ]
    )


def _master_schema() -> Any:
    try:
        import pyarrow as pa
    except ImportError as error:
        raise TQHC2Error("写入 Parquet 需要项目依赖 pyarrow") from error
    return pa.schema(
        [
            ("sample_id", pa.string()),
            ("record_sha256", pa.string()),
            ("dataset_id", pa.string()),
            ("dataset_version", pa.string()),
            ("source_artifact_id", pa.string()),
            ("source_capture_sha256", pa.string()),
            ("extractor_contract_sha256", pa.string()),
            ("allocation_group_id", pa.string()),
            ("parent_session_id", pa.string()),
            ("capture_group_id", pa.string()),
            ("sample_unit", pa.string()),
            ("window_start_ns", pa.int64()),
            ("window_end_ns", pa.int64()),
            ("window_ordinal", pa.int32()),
            ("packet_count_raw", pa.int64()),
            ("packet_count_kept", pa.int64()),
            ("native_label", pa.string()),
            ("binary_label", pa.string()),
            ("family_label", pa.string()),
            ("subtype_label", pa.string()),
            ("label_status", pa.string()),
            ("unknown_role", pa.string()),
            ("profile", pa.string()),
            ("interval_s", pa.int64()),
            ("jitter_pct", pa.int64()),
            ("capture_id", pa.string()),
            ("join_status", pa.string()),
        ]
    )


def _sensitive_packet_fields(field_names: Sequence[str]) -> list[str]:
    findings = []
    for field_name in field_names:
        tokens = set(field_name.lower().split("_"))
        if tokens.intersection(SENSITIVE_FIELD_TOKENS):
            findings.append(field_name)
    return findings


def materialize_profile(
    *,
    labels_root: Path,
    pcap_root: Path,
    profile: str,
    output_dir: Path,
    dataset_version: str,
) -> dict[str, object]:
    """生成一个 profile 的临时主记录、包观测、哈希和审计制品。"""
    output_dir = Path(output_dir)
    if "provisional" not in output_dir.name and "provisional" not in str(output_dir.parent):
        raise TQHC2Error("冻结前输出路径必须显式包含 provisional")
    if output_dir.exists():
        raise TQHC2Error(f"输出目录已存在，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True)
    incomplete_marker = output_dir / "_INCOMPLETE"
    incomplete_marker.write_text('{"status":"incomplete"}\n', encoding="utf-8")
    views_dir = output_dir / "views"
    audit_dir = output_dir / "audit"
    views_dir.mkdir()
    audit_dir.mkdir()

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as error:
        raise TQHC2Error("写入 Parquet 需要项目依赖 pyarrow") from error

    packet_schema = _packet_schema()
    sensitive = _sensitive_packet_fields(MODEL_INPUT_FIELDS)
    if sensitive or tuple(packet_schema.names) != MODEL_PACKET_FIELDS:
        raise TQHC2Error(f"包观测字段预算违规：{sensitive}")
    packet_path = views_dir / "packet_observations.parquet"
    packet_writer = pq.ParquetWriter(packet_path, packet_schema, compression="zstd")
    packet_rows = 0

    def write_packets(rows: list[dict[str, object]]) -> None:
        nonlocal packet_rows
        packet_writer.write_table(pa.Table.from_pylist(rows, schema=packet_schema))
        packet_rows += len(rows)

    module_path = Path(__file__)
    extractor_sha256 = _sha256_file(module_path)
    labels_profile = Path(labels_root) / profile
    cell_names = _profile_cell_names(labels_profile, profile)
    pcap_cell_names = _profile_cell_names(Path(pcap_root), profile)
    if cell_names != pcap_cell_names or len(cell_names) != 12:
        packet_writer.close()
        raise TQHC2Error(
            f"profile 必须有 12 个一一对应的标签和 PCAP cell：{len(cell_names)}/"
            f"{len(pcap_cell_names)}"
        )

    master_records: list[dict[str, object]] = []
    cell_audits: list[dict[str, object]] = []
    source_files: list[dict[str, object]] = []
    try:
        for cell_name in cell_names:
            pcap_path = _pcap_for_cell(Path(pcap_root), cell_name)
            pcap_sha256 = _sha256_file(pcap_path)
            result = extract_cell(
                cell_dir=labels_profile / cell_name,
                pcap_path=pcap_path,
                dataset_version=dataset_version,
                profile=profile,
                source_capture_sha256=pcap_sha256,
                extractor_contract_sha256=extractor_sha256,
                packet_sink=write_packets,
            )
            master_records.extend(result.master_records)
            cell_audits.append(result.audit)
            source_files.extend(result.source_files)
    finally:
        packet_writer.close()

    sample_ids = [str(record["sample_id"]) for record in master_records]
    if len(sample_ids) != len(set(sample_ids)):
        raise TQHC2Error("临时主记录 sample_id 不唯一")
    master_path = output_dir / "master_records.parquet"
    pq.write_table(
        pa.Table.from_pylist(master_records, schema=_master_schema()),
        master_path,
        compression="zstd",
    )

    label_counts = Counter(str(record["native_label"]) for record in master_records)
    binary_label_counts = Counter(
        str(record["binary_label"])
        for record in master_records
        if record["binary_label"] is not None
    )
    label_status_counts = Counter(str(record["label_status"]) for record in master_records)
    join_status = Counter(str(record["join_status"]) for record in master_records)
    source_files.append(
        {
            "path": str(module_path),
            "role": "extractor_source",
            "sha256": extractor_sha256,
            "size_bytes": module_path.stat().st_size,
        }
    )
    source_files = sorted(source_files, key=lambda item: (str(item["path"]), str(item["role"])))
    leakage_audit = {
        "model_input_fields": list(MODEL_INPUT_FIELDS),
        "sensitive_field_hits": sensitive,
        "status": "pass" if not sensitive else "fail",
    }
    label_coverage = {
        "binary_mapped": sum(record["label_status"] == "mapped" for record in master_records),
        "binary_label_counts": dict(sorted(binary_label_counts.items())),
        "join_status_counts": dict(sorted(join_status.items())),
        "label_counts": dict(sorted(label_counts.items())),
        "label_status_counts": dict(sorted(label_status_counts.items())),
        "record_count": len(master_records),
    }
    schema = {
        "schema_version": "tqhc2_provisional_v1",
        "status": "provisional",
        "master_record_fields": _master_schema().names,
        "model_packet_fields": packet_schema.names,
        "model_packet_field_roles": {
            field_name: "audit_only" if field_name == "sample_id" else "model_input"
            for field_name in packet_schema.names
        },
        "notes": "最终协议验收前不冻结字段、划分或模型视图。",
    }
    run_manifest = {
        "cell_count": len(cell_names),
        "dataset_id": DATASET_ID,
        "dataset_version": dataset_version,
        "extractor_contract_sha256": extractor_sha256,
        "master_record_count": len(master_records),
        "packet_record_count": packet_rows,
        "profile": profile,
        "artifact_checksum_manifest": "artifact_checksums.provisional.json",
        "status": "provisional",
    }
    artifacts = {
        audit_dir / "cell-audit.json": {"cells": cell_audits, "profile": profile},
        audit_dir / "label-coverage.json": label_coverage,
        audit_dir / "leakage-audit.json": leakage_audit,
        output_dir / "run_manifest.provisional.json": run_manifest,
        output_dir / "schema.provisional.json": schema,
        output_dir / "source_checksums.json": {"files": source_files},
    }
    for path, value in artifacts.items():
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    artifact_paths = sorted(
        [master_path, packet_path, *artifacts],
        key=lambda path: str(path.relative_to(output_dir)),
    )
    artifact_checksums = {
        "files": [
            {
                "path": str(path.relative_to(output_dir)),
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in artifact_paths
        ],
        "status": "provisional",
    }
    (output_dir / "artifact_checksums.provisional.json").write_text(
        json.dumps(artifact_checksums, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    incomplete_marker.unlink()
    return run_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="审计并提取 TQH-C2 包级临时观测")
    parser.add_argument("--profile", choices=("A", "B", "C"), required=True)
    parser.add_argument("--pcap-root", type=Path, required=True)
    parser.add_argument("--labels-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset-version", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = materialize_profile(
        labels_root=args.labels_root,
        pcap_root=args.pcap_root,
        profile=args.profile,
        output_dir=args.output,
        dataset_version=args.dataset_version,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
