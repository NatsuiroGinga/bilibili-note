"""R2 GeNIS 官方原始行回接、共同观测复算与单位证据门禁。"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import zipfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any

from flow_probe.adapters.base import DatasetSchemaError, sample_id
from flow_probe.adapters.genis import REQUIRED_COLUMNS, adapt_row
from flow_probe.r2_protocol_contract import (
    COMMON_FIELDS,
    GeNISArchiveInventory,
    R2ProtocolConfig,
    canonical_json_sha256,
    verify_genis_archive,
)
from flow_probe.serialize import serialize_flow

OFFICIAL_GENIS_ARCHIVE_SHA256 = (
    "72033b5e3df6e45cda9a339985194d8232c437c243a5037a62ebeff457489b30"
)
CANDIDATE_NAMESPACE = "dataset-candidate-genis-v0"
UNIT_GATE_GO = "GO"
UNIT_GATE_NO_GO = "NO-GO"
_SHA256_LENGTH = 64
_RAW_REQUIRED_COLUMNS = frozenset(
    (*REQUIRED_COLUMNS, "FlowID", "Proto", "Loss", "Retrans", "TcpRtt", "SrcWin", "DstWin")
)
_CANDIDATE_REQUIRED_COLUMNS = frozenset(
    {
        "sample_id",
        "source_record_sha256",
        "source_dataset",
        "group_id",
        "binary_label",
        "family_label",
        "subtype_label",
        *(item for name in COMMON_FIELDS for item in (name, f"{name}_missing")),
    }
)
_SOURCE_ROW_MAP_FIELDS = frozenset(
    {
        "sample_id",
        "old_sample_id_sha256",
        "archive_sha256",
        "member_sha256",
        "source_row_reference_sha256",
        "join_status",
        "source_record_sha256",
        "record_sha256",
    }
)


class GeNISProtocolError(ValueError):
    """GeNIS 原始回接、字段复算或单位证据不满足 R2 合同。"""


@dataclass(frozen=True, slots=True)
class GeNISRawRow:
    """仅在回接进程内存中存在的官方原始行。"""

    archive_sha256: str
    member_sha256: str
    member_basename: str
    csv_row_number: int
    old_sample_id: str
    candidate_sample_id: str
    values: Mapping[str, str | None]


@dataclass(frozen=True, slots=True)
class GeNISMaterialization:
    """不含原始身份字段或可逆行号的 GeNIS 回接结果。"""

    archive_inventory: GeNISArchiveInventory
    candidate_records: tuple[Mapping[str, object], ...]
    common_features: tuple[Mapping[str, object], ...]
    protocol_observations: tuple[Mapping[str, object], ...]
    source_row_map: tuple[Mapping[str, object], ...]
    join_audit: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class FieldUnitEvidence:
    """单字段的一手语义或逐包复算证据。"""

    field_name: str
    status: str
    authority_kind: str | None = None
    evidence_logical_path: str | None = None
    evidence_artifact_sha256: str | None = None
    algorithm: str | None = None
    unit: str | None = None
    scale_factor: float | None = None
    aggregation_semantics: str | None = None
    semantic_role: str | None = None
    compared_rows: int = 0
    exact_integer_matches: int = 0


@dataclass(frozen=True, slots=True)
class GeNISUnitEvidence:
    """四个不得猜测的 GeNIS 单位与聚合语义证据。"""

    tot_bytes: FieldUnitEvidence
    tcp_rtt: FieldUnitEvidence
    src_window: FieldUnitEvidence
    dst_window: FieldUnitEvidence


@dataclass(frozen=True, slots=True)
class UnitGateResult:
    """单位证据总门禁；证据不足返回 NO-GO，不以异常伪装通过。"""

    status: str
    passed: bool
    field_passed: Mapping[str, bool]
    reasons: tuple[str, ...]
    evidence_sha256: str


def _file_hashes(path: Path) -> tuple[int, str, str]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size += len(chunk)
            sha256.update(chunk)
            md5.update(chunk)
    return size, sha256.hexdigest(), md5.hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_sha256(value: object) -> bool:
    text = str(value)
    return len(text) == _SHA256_LENGTH and all(
        character in "0123456789abcdef" for character in text
    )


def _candidate_sample_id(old_sample_id: str) -> str:
    digest = hashlib.sha256(
        f"{CANDIDATE_NAMESPACE}\0{old_sample_id}".encode("utf-8")
    ).hexdigest()
    return f"genis:{digest}"


def _group_id(member_basename: str, flow_id: str) -> str:
    digest = hashlib.blake2b(digest_size=16)
    digest.update(member_basename.encode("utf-8"))
    digest.update(b"\0")
    digest.update(flow_id.encode("utf-8"))
    return digest.hexdigest()


def _normalise_member_basename(member_path: str) -> str:
    basename = PurePosixPath(member_path).name.strip()
    if not basename or basename in {".", ".."}:
        raise GeNISProtocolError("GeNIS ZIP 成员缺少稳定 basename")
    return basename


def _assert_inventory_binding(
    archive: Path, inventory: GeNISArchiveInventory
) -> None:
    if archive.is_symlink() or not archive.is_file():
        raise GeNISProtocolError("GeNIS 归档必须是存在的非符号链接普通文件")
    size, sha256, md5 = _file_hashes(archive)
    if (size, sha256, md5) != (
        inventory.size_bytes,
        inventory.sha256,
        inventory.md5,
    ):
        raise GeNISProtocolError("GeNIS 归档已偏离已验收归档清单")
    member_paths = [item.member_path for item in inventory.materialization_members]
    if len(member_paths) != len(set(member_paths)) or not member_paths:
        raise GeNISProtocolError("GeNIS 10 秒成员清单为空或含重复路径")
    basenames = [_normalise_member_basename(path) for path in member_paths]
    if len(basenames) != len(set(basenames)):
        raise GeNISProtocolError("GeNIS 10 秒成员 basename 不唯一，旧标识会发生碰撞")


def iter_genis_10s_rows(
    archive: Path, inventory: GeNISArchiveInventory
) -> Iterator[GeNISRawRow]:
    """按成员名与 CSV 数据行一基序号流式重建旧样本标识。"""

    archive = Path(archive)
    _assert_inventory_binding(archive, inventory)
    try:
        source = zipfile.ZipFile(archive)
    except (OSError, zipfile.BadZipFile) as error:
        raise GeNISProtocolError("GeNIS ZIP 无法打开") from error
    try:
        with source:
            for member in sorted(
                inventory.materialization_members, key=lambda item: item.member_path
            ):
                if member.scale_seconds != 10:
                    raise GeNISProtocolError("归档清单混入非 10 秒物化成员")
                try:
                    payload = source.read(member.member_path)
                except (KeyError, OSError, RuntimeError, zipfile.BadZipFile) as error:
                    raise GeNISProtocolError(
                        f"无法读取登记成员：{member.logical_path}"
                    ) from error
                if len(payload) != member.size_bytes:
                    raise GeNISProtocolError("GeNIS 成员字节数偏离归档清单")
                if hashlib.sha256(payload).hexdigest() != member.sha256:
                    raise GeNISProtocolError("GeNIS 成员 SHA-256 偏离归档清单")
                try:
                    text = payload.decode("utf-8-sig")
                except UnicodeDecodeError as error:
                    raise GeNISProtocolError("GeNIS CSV 不是合法 UTF-8") from error
                reader = csv.DictReader(io.StringIO(text, newline=""))
                missing = sorted(_RAW_REQUIRED_COLUMNS.difference(reader.fieldnames or ()))
                if missing:
                    raise GeNISProtocolError(
                        f"GeNIS CSV 缺少任务 02 字段：{', '.join(missing)}"
                    )
                basename = _normalise_member_basename(member.member_path)
                for row_number, row in enumerate(reader, start=1):
                    old_id = sample_id("genis", basename, row_number)
                    yield GeNISRawRow(
                        archive_sha256=inventory.sha256,
                        member_sha256=member.sha256,
                        member_basename=basename,
                        csv_row_number=row_number,
                        old_sample_id=old_id,
                        candidate_sample_id=_candidate_sample_id(old_id),
                        values=dict(row),
                    )
    except csv.Error as error:
        raise GeNISProtocolError("GeNIS CSV 结构损坏") from error


def _candidate_artifact_sha256(config: R2ProtocolConfig) -> str:
    matches = [item for item in config.frozen_inputs if item.role == "genis_candidate"]
    if len(matches) != 1 or not matches[0].sha256:
        raise GeNISProtocolError("配置必须恰好绑定一份带 SHA-256 的 GeNIS 候选")
    return matches[0].sha256


def _load_candidate_rows(
    candidate: Path, config: R2ProtocolConfig
) -> tuple[dict[str, dict[str, object]], tuple[str, ...], str]:
    candidate = Path(candidate)
    if candidate.is_symlink() or not candidate.is_file():
        raise GeNISProtocolError("GeNIS 候选必须是存在的非符号链接普通文件")
    _, candidate_sha256, _ = _file_hashes(candidate)
    expected_sha256 = _candidate_artifact_sha256(config)
    if candidate_sha256 != expected_sha256:
        raise GeNISProtocolError("GeNIS 候选 SHA-256 偏离任务 01 冻结配置")
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise GeNISProtocolError("读取 GeNIS 候选需要 PyArrow") from error
    parquet = pq.ParquetFile(candidate)
    missing = sorted(_CANDIDATE_REQUIRED_COLUMNS.difference(parquet.schema.names))
    if missing:
        raise GeNISProtocolError(
            f"GeNIS 候选缺少回接字段：{', '.join(missing)}"
        )
    rows: dict[str, dict[str, object]] = {}
    order: list[str] = []
    for batch in parquet.iter_batches(batch_size=65_536):
        for raw in batch.to_pylist():
            row = {str(key): value for key, value in raw.items()}
            candidate_id = str(row.get("sample_id", ""))
            if not candidate_id.startswith("genis:") or len(candidate_id) != 70:
                raise GeNISProtocolError("GeNIS 候选 sample_id 不符合冻结哈希格式")
            if candidate_id in rows:
                raise GeNISProtocolError("GeNIS 候选 sample_id 重复")
            if row.get("source_dataset") != "genis":
                raise GeNISProtocolError("GeNIS 候选混入其他来源")
            if not _is_sha256(row.get("source_record_sha256")):
                raise GeNISProtocolError("GeNIS 候选 source_record_sha256 不合法")
            rows[candidate_id] = row
            order.append(candidate_id)
    if not rows:
        raise GeNISProtocolError("GeNIS 候选为空")
    return rows, tuple(order), candidate_sha256


def _normalise_candidate_number(value: object, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise GeNISProtocolError(f"候选字段 {field_name} 不能是布尔值")
    if not isinstance(value, (int, float, str, Decimal)):
        raise GeNISProtocolError(f"候选字段 {field_name} 不是数值")
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise GeNISProtocolError(f"候选字段 {field_name} 不是数值") from error
    if not math.isfinite(parsed):
        raise GeNISProtocolError(f"候选字段 {field_name} 不是有限数")
    return 0.0 if parsed == 0.0 else parsed


def _packet_count(row: Mapping[str, str | None], field_name: str) -> int | None:
    raw = row.get(field_name)
    if raw is None or not str(raw).strip():
        return None
    try:
        value = Decimal(str(raw).strip())
    except InvalidOperation as error:
        raise GeNISProtocolError(f"GeNIS {field_name} 不是包计数") from error
    if not value.is_finite() or value < 0 or value != value.to_integral_value():
        raise GeNISProtocolError(f"GeNIS {field_name} 必须是非负整数包计数")
    return int(value)


def _transport_family(value: object) -> str:
    normalised = str(value or "").strip().lower()
    aliases = {
        "6": "TCP",
        "tcp": "TCP",
        "17": "UDP",
        "udp": "UDP",
        "1": "ICMP",
        "icmp": "ICMP",
        "132": "SCTP",
        "sctp": "SCTP",
        "33": "DCCP",
        "dccp": "DCCP",
        "50": "ESP",
        "esp": "ESP",
    }
    return aliases.get(normalised, "UNKNOWN" if not normalised else "OTHER")


def _training_record(sample: Any) -> dict[str, object]:
    return {
        "sample_id": sample.sample_id,
        "group_id": sample.group_id,
        "source_dataset": sample.source_dataset,
        "binary_label": sample.binary_label,
        "attack_family": sample.attack_family,
        "attack_subtype": sample.original_label,
        "features": dict(sample.features),
        "prompt": serialize_flow(sample),
        "completion": json.dumps(
            {"label": sample.binary_label},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }


def _assert_same_number(
    candidate_value: object, expected_value: float | None, field_name: str
) -> None:
    actual = _normalise_candidate_number(candidate_value, field_name)
    expected = 0.0 if expected_value == 0.0 else expected_value
    if actual != expected:
        raise GeNISProtocolError(f"GeNIS 回接后字段不一致：{field_name}")


def _missing_mask(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise GeNISProtocolError(f"GeNIS 候选缺失掩码不合法：{field_name}")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise GeNISProtocolError(
            f"GeNIS 候选缺失掩码不合法：{field_name}"
        ) from error
    if parsed not in {0, 1}:
        raise GeNISProtocolError(f"GeNIS 候选缺失掩码不合法：{field_name}")
    return parsed


def _recompute_match(
    raw: GeNISRawRow, candidate: Mapping[str, object]
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    flow_id = str(raw.values.get("FlowID") or "").strip()
    if not flow_id:
        raise GeNISProtocolError("GeNIS 原始行 FlowID 为空")
    group_id = _group_id(raw.member_basename, flow_id)
    try:
        sample = replace(
            adapt_row(raw.values, raw.member_basename, raw.csv_row_number),
            group_id=group_id,
        )
    except (DatasetSchemaError, TypeError, ValueError) as error:
        raise GeNISProtocolError("GeNIS 原始行无法按冻结适配器复算") from error
    source_record_sha256 = canonical_json_sha256(_training_record(sample))
    exact_values = {
        "sample_id": raw.candidate_sample_id,
        "source_dataset": "genis",
        "group_id": group_id,
        "binary_label": sample.binary_label,
        "family_label": sample.attack_family,
        "subtype_label": sample.original_label,
        "source_record_sha256": source_record_sha256,
    }
    for field_name, expected in exact_values.items():
        if str(candidate.get(field_name, "")) != str(expected):
            raise GeNISProtocolError(f"GeNIS 回接后身份或标签不一致：{field_name}")
    common: dict[str, object] = {"sample_id": raw.candidate_sample_id}
    for field_name in COMMON_FIELDS:
        raw_expected_value = sample.features[field_name]
        if raw_expected_value is not None and (
            isinstance(raw_expected_value, bool)
            or not isinstance(raw_expected_value, (int, float))
        ):
            raise GeNISProtocolError(f"GeNIS 适配器字段不是数值：{field_name}")
        expected_value = (
            None if raw_expected_value is None else float(raw_expected_value)
        )
        _assert_same_number(candidate.get(field_name), expected_value, field_name)
        expected_missing = int(expected_value is None)
        actual_missing = _missing_mask(
            candidate.get(f"{field_name}_missing"), field_name
        )
        if actual_missing != expected_missing:
            raise GeNISProtocolError(f"GeNIS 回接后缺失掩码不一致：{field_name}")
        common[field_name] = expected_value
        common[f"{field_name}_missing"] = expected_missing
    loss_packets = _packet_count(raw.values, "Loss")
    retrans_packets = _packet_count(raw.values, "Retrans")
    transport = _transport_family(raw.values.get("Proto"))
    protocol = {
        "sample_id": raw.candidate_sample_id,
        "transport_family": transport,
        "loss_packets": loss_packets,
        "loss_packets_missing": int(loss_packets is None),
        "loss_packets_applicable": int(loss_packets is not None),
        "retrans_packets": retrans_packets,
        "retrans_packets_missing": int(retrans_packets is None),
        "retrans_packets_applicable": int(transport == "TCP"),
        "tcp_rtt_ms": None,
        "tcp_rtt_ms_missing": 1,
        "tcp_rtt_ms_applicable": int(transport == "TCP"),
        "src_window_bytes": None,
        "src_window_bytes_missing": 1,
        "src_window_bytes_applicable": int(transport == "TCP"),
        "dst_window_bytes": None,
        "dst_window_bytes_missing": 1,
        "dst_window_bytes_applicable": int(transport == "TCP"),
        "src_window_semantic": "advertised_receive_window",
        "dst_window_semantic": "advertised_receive_window",
        "semantic_gate_status": UNIT_GATE_NO_GO,
    }
    source_map: dict[str, object] = {
        "sample_id": raw.candidate_sample_id,
        "old_sample_id_sha256": _sha256_text(raw.old_sample_id),
        "archive_sha256": raw.archive_sha256,
        "member_sha256": raw.member_sha256,
        "source_row_reference_sha256": _sha256_text(
            f"{raw.archive_sha256}\0{raw.member_sha256}\0{raw.csv_row_number}"
        ),
        "join_status": "matched_by_frozen_sample_hash",
        "source_record_sha256": source_record_sha256,
    }
    source_map["record_sha256"] = canonical_json_sha256(source_map)
    if set(source_map) != _SOURCE_ROW_MAP_FIELDS:
        raise GeNISProtocolError("source_row_map 字段偏离不可逆最小合同")
    return common, protocol, source_map


def reconnect_genis_candidate(
    candidate: Path, archive: Path, config: R2ProtocolConfig
) -> GeNISMaterialization:
    """只以旧标识固定哈希回接冻结候选，并逐行复算全部任务字段。"""

    if tuple(config.common_fields) != tuple(COMMON_FIELDS):
        raise GeNISProtocolError("任务 02 只接受任务 01 冻结的八字段顺序")
    required_gates = {"TotBytes", "TcpRtt", "SrcWin", "DstWin"}
    if set(config.semantic_gates) != required_gates:
        raise GeNISProtocolError("GeNIS 四项语义门禁不完整")
    inventory = verify_genis_archive(Path(archive), config.genis)
    if (
        config.genis.record_id == "14919237"
        and config.genis.version == "1.0.0"
        and inventory.sha256 != OFFICIAL_GENIS_ARCHIVE_SHA256
    ):
        raise GeNISProtocolError("GeNIS 官方归档 SHA-256 偏离冻结值")
    candidates, order, candidate_sha256 = _load_candidate_rows(candidate, config)
    matched: dict[
        str, tuple[dict[str, object], dict[str, object], dict[str, object]]
    ] = {}
    generated_ids: set[str] = set()
    for raw in iter_genis_10s_rows(archive, inventory):
        if raw.candidate_sample_id in generated_ids:
            raise GeNISProtocolError("ZIP 成员与一基行号生成了重复候选标识")
        generated_ids.add(raw.candidate_sample_id)
        frozen = candidates.get(raw.candidate_sample_id)
        if frozen is None:
            continue
        if raw.candidate_sample_id in matched:
            raise GeNISProtocolError("一条冻结候选命中多条官方原始行")
        matched[raw.candidate_sample_id] = _recompute_match(raw, frozen)
    missing = sorted(set(candidates).difference(matched))
    if missing:
        raise GeNISProtocolError(
            f"存在未消费的 GeNIS 目标候选：{len(missing)} 条"
        )
    common_rows = tuple(matched[sample][0] for sample in order)
    protocol_rows = tuple(matched[sample][1] for sample in order)
    source_rows = tuple(matched[sample][2] for sample in order)
    candidate_rows = tuple(candidates[sample] for sample in order)
    join_audit: dict[str, object] = {
        "schema_version": "flow_probe_r2_genis_join_audit_v1",
        "status": "passed",
        "join_method": "zip_member_basename_plus_csv_data_row_one_based_then_frozen_sha256",
        "candidate_sha256": candidate_sha256,
        "archive_sha256": inventory.sha256,
        "candidate_rows": len(candidate_rows),
        "matched_rows": len(matched),
        "duplicate_candidate_ids": 0,
        "duplicate_generated_ids": 0,
        "missing_candidates": 0,
        "source_row_map_sha256": canonical_json_sha256(source_rows),
        "semantic_gate_status": UNIT_GATE_NO_GO,
        "blocked_semantics": sorted(required_gates),
    }
    join_audit["audit_sha256"] = canonical_json_sha256(join_audit)
    return GeNISMaterialization(
        archive_inventory=inventory,
        candidate_records=candidate_rows,
        common_features=common_rows,
        protocol_observations=protocol_rows,
        source_row_map=source_rows,
        join_audit=join_audit,
    )


def _safe_evidence_path(value: str | None) -> bool:
    if value is None or not value.strip() or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def _base_evidence_reasons(evidence: FieldUnitEvidence) -> list[str]:
    reasons: list[str] = []
    if evidence.status != "verified":
        reasons.append("status_not_verified")
    if not _safe_evidence_path(evidence.evidence_logical_path):
        reasons.append("evidence_logical_path_missing_or_unsafe")
    if not _is_sha256(evidence.evidence_artifact_sha256):
        reasons.append("evidence_artifact_sha256_invalid")
    if not evidence.algorithm or not evidence.algorithm.strip():
        reasons.append("algorithm_missing")
    if not evidence.aggregation_semantics or not evidence.aggregation_semantics.strip():
        reasons.append("aggregation_semantics_missing")
    scale_is_valid = False
    if evidence.scale_factor is not None and not isinstance(
        evidence.scale_factor, bool
    ):
        try:
            scale = float(evidence.scale_factor)
        except (TypeError, ValueError):
            scale = math.nan
        scale_is_valid = math.isfinite(scale) and scale > 0
    if not scale_is_valid:
        reasons.append("scale_factor_invalid")
    return reasons


def _evaluate_unit_field(
    evidence: FieldUnitEvidence, expected_field: str
) -> tuple[bool, tuple[str, ...]]:
    reasons = _base_evidence_reasons(evidence)
    if evidence.field_name != expected_field:
        reasons.append("field_name_mismatch")
    if expected_field == "TotBytes":
        if evidence.authority_kind not in {
            "hera_primary_source",
            "network_layer_packet_recalculation",
        }:
            reasons.append("authority_not_primary_or_packet_recalculation")
        if evidence.unit != "network_layer_bytes":
            reasons.append("unit_not_network_layer_bytes")
        if evidence.semantic_role != "network_layer_byte_sum":
            reasons.append("semantic_role_not_network_layer_byte_sum")
        if (
            evidence.compared_rows <= 0
            or evidence.exact_integer_matches != evidence.compared_rows
        ):
            reasons.append("exact_integer_comparison_incomplete")
    elif expected_field == "TcpRtt":
        if evidence.authority_kind != "primary_source":
            reasons.append("authority_not_primary_source")
        if evidence.unit != "milliseconds":
            reasons.append("unit_not_milliseconds")
        if evidence.semantic_role != "handshake_round_trip_time":
            reasons.append("semantic_role_not_handshake_round_trip_time")
    else:
        if evidence.authority_kind != "primary_source":
            reasons.append("authority_not_primary_source")
        if evidence.unit != "bytes":
            reasons.append("unit_not_bytes")
        if evidence.semantic_role != "advertised_receive_window":
            reasons.append("semantic_role_not_advertised_receive_window")
    return not reasons, tuple(reasons)


def validate_genis_units(evidence: GeNISUnitEvidence) -> UnitGateResult:
    """四项一手证据全部闭合才返回 GO；任何不足均明确返回 NO-GO。"""

    fields = {
        "TotBytes": evidence.tot_bytes,
        "TcpRtt": evidence.tcp_rtt,
        "SrcWin": evidence.src_window,
        "DstWin": evidence.dst_window,
    }
    passed: dict[str, bool] = {}
    reasons: list[str] = []
    evidence_rows: list[dict[str, object]] = []
    for field_name, field_evidence in fields.items():
        field_passed, field_reasons = _evaluate_unit_field(field_evidence, field_name)
        passed[field_name] = field_passed
        reasons.extend(f"{field_name}:{reason}" for reason in field_reasons)
        evidence_rows.append(
            {
                "field_name": field_evidence.field_name,
                "status": field_evidence.status,
                "authority_kind": field_evidence.authority_kind,
                "evidence_logical_path": field_evidence.evidence_logical_path,
                "evidence_artifact_sha256": field_evidence.evidence_artifact_sha256,
                "algorithm": field_evidence.algorithm,
                "unit": field_evidence.unit,
                "scale_factor": field_evidence.scale_factor,
                "aggregation_semantics": field_evidence.aggregation_semantics,
                "semantic_role": field_evidence.semantic_role,
                "compared_rows": field_evidence.compared_rows,
                "exact_integer_matches": field_evidence.exact_integer_matches,
            }
        )
    all_passed = all(passed.values())
    return UnitGateResult(
        status=UNIT_GATE_GO if all_passed else UNIT_GATE_NO_GO,
        passed=all_passed,
        field_passed=passed,
        reasons=tuple(reasons),
        evidence_sha256=canonical_json_sha256(evidence_rows),
    )
