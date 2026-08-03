"""R2 TQH-C2 包序列重组、QUIC 线图像解析与聚合重算。"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import logging
import math
import os
import shutil
import struct
import sys
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import AbstractSet, Any, Protocol

from flow_probe.r2_protocol_contract import (
    AGGREGATE_FRACTION_FIELDS,
    COMMON_FIELDS,
    PROTOCOL_TARGETS,
    QUIC_AGGREGATE_FIELDS,
    QUIC_EVIDENCE_CLASSES,
    QUIC_EVIDENCE_PRIORITY,
    TRANSPORT_FAMILIES,
    ExecutionCodeLock,
    ParquetWriteSpec,
    R2ProtocolConfig,
    SourceArtifactLock,
    SourceLock,
    canonical_json_sha256,
    load_execution_code_lock,
    load_r2_config,
    verify_execution_code_lock,
)
from flow_probe.tqh_c2 import (
    PcapFrame,
    ParsedPacket,
    _label_to_session,
    _load_cell_records,
    _match_packet,
    _session_index,
    iter_pcap,
    parse_ip_packet,
)

QUIC_PARSER_VERSION = "flow_probe_quic_wire_image_v1"
_BUCKET_COUNT = 64
_MAX_BUCKET_ROWS = 200_000
_BUCKET_WRITE_BUFFER_ROWS = 4_096
_WRITE_BATCH_ROWS = 65_536
_SHA256_HEX_LENGTH = 64
_MAX_QUIC_CONTEXT_DIRECTIONS = 64
_MATCH_TOLERANCE_NS = 1_000_000
_SOURCE_LOCK_SCHEMA_VERSION = "flow_probe_r2_source_lock_v1"
_PROTOCOL_TRUTH_SCHEMA_VERSION = "flow_probe_r2_tqhc2_protocol_truth_v1"
_PROTOCOL_TRUTH_KINDS = frozenset({"controlled_configuration", "trusted_log"})
_PROTOCOL_TRUTH_INPUT_FIELDS = frozenset(
    {"sample_id", "transport_family", "quic_version", "controlled_run_id", "event_type"}
)
_PROTOCOL_TRUTH_LOCK_ROLES = frozenset(
    {"label_or_audit_source", "protocol_truth_source"}
)
_LOGGER = logging.getLogger(__name__)

BASE_PACKET_FIELDS = (
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

QUIC_PACKET_FIELDS = (
    "quic_header_form",
    "quic_header_form_observed",
    "quic_header_form_applicable",
    "quic_version_u32",
    "quic_version_observed",
    "quic_version_applicable",
    "quic_v1_packet_type",
    "quic_v1_packet_type_observed",
    "quic_v1_packet_type_applicable",
    "quic_fixed_bit",
    "quic_fixed_bit_observed",
    "quic_fixed_bit_applicable",
    "quic_spin_bit",
    "quic_spin_bit_observed",
    "quic_spin_bit_applicable",
    "quic_src_cid_length_bytes",
    "quic_src_cid_length_observed",
    "quic_src_cid_length_applicable",
    "quic_dst_cid_length_bytes",
    "quic_dst_cid_length_observed",
    "quic_dst_cid_length_applicable",
    "quic_cid_changed",
    "quic_cid_changed_observed",
    "quic_cid_changed_applicable",
    "quic_parser_version",
)

PACKET_OBSERVATION_FIELDS = (*BASE_PACKET_FIELDS, *QUIC_PACKET_FIELDS)

PROTOCOL_STAGE_FIELDS = (
    "sample_id",
    "transport_family",
    "transport_family_observed",
    "quic_evidence_class",
    "protocol_target",
    *(item for name in COMMON_FIELDS for item in (name, f"{name}_missing")),
    *AGGREGATE_FRACTION_FIELDS,
    *(
        item
        for name in QUIC_AGGREGATE_FIELDS
        for item in (name, f"{name}_missing", f"{name}_applicable")
    ),
)

SOURCE_ROW_MAP_FIELDS = (
    "sample_id",
    "source_binding_sha256",
    "upstream_observation_sequence_sha256",
    "base_observation_sequence_sha256",
    "observation_sequence_sha256",
    "quic_parser_version",
    "protocol_target_evidence_sha256",
)

_LEGACY_HASH_FIELDS = BASE_PACKET_FIELDS[2:]
_V1_PACKET_TYPES = {
    0: "INITIAL",
    1: "0RTT",
    2: "HANDSHAKE",
    3: "RETRY",
}


class TQHC2ProtocolError(ValueError):
    """TQH-C2 R2 输入、序列或 QUIC 观测不满足冻结合同。"""


def _validate_packet_field_order(fields: Sequence[str]) -> None:
    if tuple(fields) != PACKET_OBSERVATION_FIELDS:
        raise TQHC2ProtocolError("发布包字段顺序偏离冻结的 39 列合同")


@dataclass(frozen=True, slots=True)
class QuicObservation:
    """不含原始连接标识的单包 QUIC 线图像。"""

    evidence_class: str
    quic_header_form: int | None
    quic_header_form_observed: bool
    quic_header_form_applicable: bool
    quic_version_u32: int | None
    quic_version_observed: bool
    quic_version_applicable: bool
    quic_v1_packet_type: str | None
    quic_v1_packet_type_observed: bool
    quic_v1_packet_type_applicable: bool
    quic_fixed_bit: int | None
    quic_fixed_bit_observed: bool
    quic_fixed_bit_applicable: bool
    quic_spin_bit: int | None
    quic_spin_bit_observed: bool
    quic_spin_bit_applicable: bool
    quic_src_cid_length_bytes: int | None
    quic_src_cid_length_observed: bool
    quic_src_cid_length_applicable: bool
    quic_dst_cid_length_bytes: int | None
    quic_dst_cid_length_observed: bool
    quic_dst_cid_length_applicable: bool
    quic_cid_changed: bool | None
    quic_cid_changed_observed: bool
    quic_cid_changed_applicable: bool
    quic_parser_version: str

    def as_packet_fields(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in QUIC_PACKET_FIELDS}


@dataclass(slots=True)
class QuicConnectionContext:
    """只在内存中保存方向化连接标识，表示时不会泄漏原始字节。"""

    max_directions: int = _MAX_QUIC_CONTEXT_DIRECTIONS
    _directions: dict[
        tuple[str, int, str, int], tuple[bytes, bytes]
    ] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.max_directions <= 0:
            raise TQHC2ProtocolError("QUIC 上下文方向容量必须为正")

    @staticmethod
    def _key(packet: ParsedPacket) -> tuple[str, int, str, int]:
        return (packet.src, packet.src_port, packet.dst, packet.dst_port)

    def lookup(self, packet: ParsedPacket) -> tuple[bytes, bytes] | None:
        return self._directions.get(self._key(packet))

    def compare(
        self, packet: ParsedPacket, destination_cid: bytes, source_cid: bytes
    ) -> bool | None:
        previous = self.lookup(packet)
        if previous is None:
            return None
        return previous != (destination_cid, source_cid)

    def bind(
        self, packet: ParsedPacket, destination_cid: bytes, source_cid: bytes
    ) -> bool | None:
        key = self._key(packet)
        reverse = (packet.dst, packet.dst_port, packet.src, packet.src_port)
        changed = self.compare(packet, destination_cid, source_cid)
        updates = {
            key: (destination_cid, source_cid),
            reverse: (source_cid, destination_cid),
        }
        added = sum(direction not in self._directions for direction in updates)
        if len(self._directions) + added > self.max_directions:
            raise TQHC2ProtocolError(
                f"单样本 QUIC 上下文超过方向容量：{self.max_directions}"
            )
        self._directions.update(updates)
        return changed

    @property
    def direction_count(self) -> int:
        return len(self._directions)

    def __repr__(self) -> str:
        return f"QuicConnectionContext(direction_count={len(self._directions)})"


@dataclass(slots=True)
class _QuicContextRegistry:
    """只为冻结样本分配彼此隔离且数量有界的 QUIC 上下文。"""

    allowed_sample_ids: frozenset[str]
    _contexts: dict[str, QuicConnectionContext] = field(
        default_factory=dict, repr=False
    )

    def for_sample(self, sample_id: str) -> QuicConnectionContext:
        if sample_id not in self.allowed_sample_ids:
            raise TQHC2ProtocolError("不得为未冻结样本分配 QUIC 上下文")
        context = self._contexts.get(sample_id)
        if context is None:
            if len(self._contexts) >= len(self.allowed_sample_ids):
                raise TQHC2ProtocolError("QUIC 样本上下文超过冻结样本容量")
            context = QuicConnectionContext()
            self._contexts[sample_id] = context
        return context

    @property
    def sample_count(self) -> int:
        return len(self._contexts)

    @property
    def capacity(self) -> int:
        return len(self.allowed_sample_ids)


@dataclass(frozen=True, slots=True)
class PacketObservation:
    sample_id: str
    packet_index: int
    relative_time_ns: int
    delta_time_us: int
    direction: int
    network_length_bytes: int
    payload_length_bytes: int | None
    transport_family: str
    tcp_flags: int | None
    burst_id: int
    is_first_packet: bool
    payload_length_observed: bool
    tcp_flags_applicable: bool
    truncation_mask: bool
    quic_header_form: int | None
    quic_header_form_observed: bool
    quic_header_form_applicable: bool
    quic_version_u32: int | None
    quic_version_observed: bool
    quic_version_applicable: bool
    quic_v1_packet_type: str | None
    quic_v1_packet_type_observed: bool
    quic_v1_packet_type_applicable: bool
    quic_fixed_bit: int | None
    quic_fixed_bit_observed: bool
    quic_fixed_bit_applicable: bool
    quic_spin_bit: int | None
    quic_spin_bit_observed: bool
    quic_spin_bit_applicable: bool
    quic_src_cid_length_bytes: int | None
    quic_src_cid_length_observed: bool
    quic_src_cid_length_applicable: bool
    quic_dst_cid_length_bytes: int | None
    quic_dst_cid_length_observed: bool
    quic_dst_cid_length_applicable: bool
    quic_cid_changed: bool | None
    quic_cid_changed_observed: bool
    quic_cid_changed_applicable: bool
    quic_parser_version: str
    quic_evidence_class: str = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        _validate_packet_observation(self)

    def as_record(self) -> dict[str, object]:
        return {name: getattr(self, name) for name in PACKET_OBSERVATION_FIELDS}


@dataclass(frozen=True, slots=True)
class TQHAggregates:
    sample_id: str
    transport_family: str
    quic_evidence_class: str
    common: Mapping[str, float | None]
    common_missing: Mapping[str, int]
    fractions: Mapping[str, float | None]
    quic: Mapping[str, float | None]
    quic_missing: Mapping[str, int]
    quic_applicable: Mapping[str, int]
    base_observation_sequence_sha256: str
    observation_sequence_sha256: str

    def protocol_record(self, protocol_target: str) -> dict[str, object]:
        row: dict[str, object] = {
            "sample_id": self.sample_id,
            "transport_family": self.transport_family,
            "transport_family_observed": 1,
            "quic_evidence_class": self.quic_evidence_class,
            "protocol_target": protocol_target,
        }
        for name in COMMON_FIELDS:
            row[name] = self.common[name]
            row[f"{name}_missing"] = self.common_missing[name]
        for name in AGGREGATE_FRACTION_FIELDS:
            row[name] = self.fractions[name]
        for name in QUIC_AGGREGATE_FIELDS:
            row[name] = self.quic[name]
            row[f"{name}_missing"] = self.quic_missing[name]
            row[f"{name}_applicable"] = self.quic_applicable[name]
        return row


@dataclass(frozen=True, slots=True)
class PcapPacketMatch:
    """PCAP 与既有基础包行的无敏感字段连接结果。"""

    sample_id: str
    packet_index: int
    relative_time_ns: int
    delta_time_us: int
    direction: int
    burst_id: int
    is_first_packet: bool


class PcapPacketMatcher(Protocol):
    def __call__(
        self, frame: PcapFrame, packet: ParsedPacket
    ) -> PcapPacketMatch | None: ...


@dataclass(frozen=True, slots=True)
class TQHPcapSource:
    logical_id: str
    path: Path
    match_packet: PcapPacketMatcher


@dataclass(frozen=True, slots=True)
class TrustedProtocolTarget:
    target: str
    evidence_logical_path: str


@dataclass(frozen=True, slots=True)
class TQHProtocolTruthEvidence:
    logical_path: str
    path: Path


@dataclass(frozen=True, slots=True)
class TQHProfileBinding:
    profile: str
    packet_observations_path: Path
    expected_base_sequence_sha256: Mapping[str, str]
    pcap_sources: tuple[TQHPcapSource, ...]
    trusted_protocol_targets: Mapping[str, TrustedProtocolTarget] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class TQHSourceBindings:
    config: R2ProtocolConfig
    profiles: tuple[TQHProfileBinding, ...]
    source_lock: SourceLock | None = None
    protocol_truth_evidence: tuple[TQHProtocolTruthEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class _VerifiedProtocolTarget:
    target: str
    evidence_sha256: str
    profile: str | None


@dataclass(frozen=True, slots=True)
class TQHMaterialization:
    packet_observations_path: Path
    protocol_path: Path
    source_row_map_path: Path
    sequence_audit_path: Path
    packet_row_count: int
    sample_count: int
    artifact_sha256: Mapping[str, str]


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == _SHA256_HEX_LENGTH and all(
        character in "0123456789abcdef" for character in value
    )


def _quic_observation(**overrides: object) -> QuicObservation:
    values: dict[str, object] = {
        "evidence_class": "NONE",
        "quic_header_form": None,
        "quic_header_form_observed": False,
        "quic_header_form_applicable": False,
        "quic_version_u32": None,
        "quic_version_observed": False,
        "quic_version_applicable": False,
        "quic_v1_packet_type": None,
        "quic_v1_packet_type_observed": False,
        "quic_v1_packet_type_applicable": False,
        "quic_fixed_bit": None,
        "quic_fixed_bit_observed": False,
        "quic_fixed_bit_applicable": False,
        "quic_spin_bit": None,
        "quic_spin_bit_observed": False,
        "quic_spin_bit_applicable": False,
        "quic_src_cid_length_bytes": None,
        "quic_src_cid_length_observed": False,
        "quic_src_cid_length_applicable": False,
        "quic_dst_cid_length_bytes": None,
        "quic_dst_cid_length_observed": False,
        "quic_dst_cid_length_applicable": False,
        "quic_cid_changed": None,
        "quic_cid_changed_observed": False,
        "quic_cid_changed_applicable": False,
        "quic_parser_version": QUIC_PARSER_VERSION,
    }
    values.update(overrides)
    return QuicObservation(**values)  # type: ignore[arg-type]


def _udp_transport_bounds(frame: PcapFrame) -> tuple[int, int, bool] | None:
    data = frame.data
    if len(data) < 14:
        return None
    ethertype = struct.unpack_from("!H", data, 12)[0]
    offset = 14
    while ethertype in {0x8100, 0x88A8, 0x9100}:
        if len(data) < offset + 4:
            return None
        ethertype = struct.unpack_from("!H", data, offset + 2)[0]
        offset += 4
    if ethertype == 0x0800:
        if len(data) < offset + 20:
            return None
        header_length = (data[offset] & 0x0F) * 4
        if data[offset] >> 4 != 4 or header_length < 20 or len(data) < offset + header_length:
            return None
        total_length = struct.unpack_from("!H", data, offset + 2)[0]
        if total_length < header_length + 8 or data[offset + 9] != 17:
            return None
        transport_offset = offset + header_length
        network_end = offset + total_length
    elif ethertype == 0x86DD:
        if len(data) < offset + 40 or data[offset] >> 4 != 6:
            return None
        payload_length = struct.unpack_from("!H", data, offset + 4)[0]
        next_header = data[offset + 6]
        transport_offset = offset + 40
        remaining = payload_length
        while next_header in {0, 43, 44, 51, 60}:
            if remaining < 2 or len(data) < transport_offset + 2:
                return None
            following = data[transport_offset]
            if next_header == 44:
                extension_length = 8
            elif next_header == 51:
                extension_length = (data[transport_offset + 1] + 2) * 4
            else:
                extension_length = (data[transport_offset + 1] + 1) * 8
            if extension_length > remaining or len(data) < transport_offset + extension_length:
                return None
            next_header = following
            transport_offset += extension_length
            remaining -= extension_length
        if next_header != 17 or remaining < 8:
            return None
        network_end = offset + 40 + payload_length
    else:
        return None
    if len(data) < transport_offset + 8:
        return None
    udp_length = struct.unpack_from("!H", data, transport_offset + 4)[0]
    if udp_length < 8 or transport_offset + udp_length > network_end:
        return None
    declared_end = transport_offset + udp_length
    visible_end = min(declared_end, len(data))
    truncated = frame.capture_truncated or visible_end < declared_end
    return transport_offset + 8, visible_end, truncated


def _decode_quic_varint(payload: bytes, offset: int) -> tuple[int, int] | None:
    if offset >= len(payload):
        return None
    length = 1 << (payload[offset] >> 6)
    end = offset + length
    if end > len(payload):
        return None
    value = int.from_bytes(payload[offset:end], "big")
    value &= (1 << (length * 8 - 2)) - 1
    return value, end


def _has_complete_protected_body(payload: bytes, length_offset: int) -> bool:
    decoded = _decode_quic_varint(payload, length_offset)
    if decoded is None:
        return False
    protected_length, protected_start = decoded
    return protected_length > 0 and protected_start + protected_length <= len(payload)


def _has_complete_v1_type_structure(
    payload: bytes, type_offset: int, packet_type: int
) -> bool:
    if packet_type == 0:
        token_length = _decode_quic_varint(payload, type_offset)
        if token_length is None:
            return False
        token_size, token_start = token_length
        length_offset = token_start + token_size
        if length_offset > len(payload):
            return False
        return _has_complete_protected_body(payload, length_offset)
    if packet_type in {1, 2}:
        return _has_complete_protected_body(payload, type_offset)
    return len(payload) - type_offset >= 16


def parse_quic_wire_image(
    frame: PcapFrame, context: QuicConnectionContext
) -> QuicObservation:
    """仅从可见 UDP 线图像解析允许的 QUIC 字段。"""

    parsed = parse_ip_packet(frame)
    packet = parsed.packet
    if parsed.status != "parsed" or packet is None or packet.protocol != "udp":
        return _quic_observation()
    bounds = _udp_transport_bounds(frame)
    if bounds is None:
        return _quic_observation(
            evidence_class="AMBIGUOUS" if frame.capture_truncated else "NONE",
            quic_header_form_applicable=True,
            quic_fixed_bit_applicable=True,
        )
    payload_start, payload_end, truncated = bounds
    payload = frame.data[payload_start:payload_end]
    if not payload:
        return _quic_observation(
            evidence_class="AMBIGUOUS" if truncated else "NONE",
            quic_header_form_applicable=True,
            quic_fixed_bit_applicable=True,
        )

    first = payload[0]
    header_form = (first >> 7) & 1
    fixed_bit = (first >> 6) & 1
    common = {
        "quic_header_form": header_form,
        "quic_header_form_observed": True,
        "quic_header_form_applicable": True,
        "quic_fixed_bit": fixed_bit,
        "quic_fixed_bit_observed": True,
        "quic_fixed_bit_applicable": True,
    }
    if header_form == 0:
        bound = context.lookup(packet)
        if bound is None:
            return _quic_observation(
                **common,
                evidence_class="AMBIGUOUS" if truncated else "NONE",
            )
        destination_cid, _source_cid = bound
        cid_end = 1 + len(destination_cid)
        short_common = {
            **common,
            "quic_spin_bit": (first >> 5) & 1,
            "quic_spin_bit_observed": True,
            "quic_spin_bit_applicable": True,
            "quic_dst_cid_length_bytes": len(destination_cid),
            "quic_dst_cid_length_observed": True,
            "quic_dst_cid_length_applicable": True,
            "quic_cid_changed_applicable": True,
        }
        if truncated or len(payload) < cid_end:
            return _quic_observation(
                **short_common,
                evidence_class="AMBIGUOUS",
            )
        cid_changed = payload[1:cid_end] != destination_cid
        return _quic_observation(
            **short_common,
            evidence_class=("AMBIGUOUS" if cid_changed else "CONTEXT_BOUND_SHORT_HEADER"),
            quic_cid_changed=cid_changed,
            quic_cid_changed_observed=True,
        )

    long_common: dict[str, object] = {
        **common,
        "quic_version_applicable": True,
        "quic_src_cid_length_applicable": True,
        "quic_dst_cid_length_applicable": True,
        "quic_cid_changed_applicable": True,
    }
    if len(payload) < 5:
        return _quic_observation(**long_common, evidence_class="AMBIGUOUS")
    version = int.from_bytes(payload[1:5], "big")
    long_common.update(
        quic_version_u32=version,
        quic_version_observed=True,
        quic_v1_packet_type_applicable=version == 1,
    )
    if len(payload) < 6:
        return _quic_observation(**long_common, evidence_class="AMBIGUOUS")
    destination_length = payload[5]
    long_common.update(
        quic_dst_cid_length_bytes=destination_length,
        quic_dst_cid_length_observed=True,
    )
    if destination_length > 20:
        return _quic_observation(**long_common, evidence_class="AMBIGUOUS")
    source_length_offset = 6 + destination_length
    if len(payload) <= source_length_offset:
        return _quic_observation(**long_common, evidence_class="AMBIGUOUS")
    source_length = payload[source_length_offset]
    long_common.update(
        quic_src_cid_length_bytes=source_length,
        quic_src_cid_length_observed=True,
    )
    if source_length > 20:
        return _quic_observation(**long_common, evidence_class="AMBIGUOUS")
    source_end = source_length_offset + 1 + source_length
    if len(payload) < source_end:
        return _quic_observation(**long_common, evidence_class="AMBIGUOUS")
    destination_cid = payload[6:source_length_offset]
    source_cid = payload[source_length_offset + 1 : source_end]
    if version != 1:
        changed = None if truncated else context.compare(packet, destination_cid, source_cid)
        return _quic_observation(
            **long_common,
            evidence_class="AMBIGUOUS",
            quic_cid_changed=changed,
            quic_cid_changed_observed=changed is not None,
        )
    packet_type = (first & 0x30) >> 4
    long_common.update(
        quic_v1_packet_type=_V1_PACKET_TYPES[packet_type],
        quic_v1_packet_type_observed=True,
    )
    if truncated or not _has_complete_v1_type_structure(
        payload, source_end, packet_type
    ):
        return _quic_observation(**long_common, evidence_class="AMBIGUOUS")
    changed = context.bind(packet, destination_cid, source_cid)
    return _quic_observation(
        **long_common,
        evidence_class="V1_LONG_HEADER",
        quic_cid_changed=changed,
        quic_cid_changed_observed=changed is not None,
    )


def _validate_observed_value(
    name: str, value: object, observed: bool, applicable: bool
) -> None:
    if observed and (not applicable or value is None):
        raise TQHC2ProtocolError(f"{name} 声明已观测时必须适用且非空")
    if not observed and value is not None:
        raise TQHC2ProtocolError(f"{name} 未观测时不得携带数值")


def _validate_packet_observation(row: PacketObservation) -> None:
    if not row.sample_id:
        raise TQHC2ProtocolError("sample_id 不得为空")
    if row.packet_index < 0 or row.relative_time_ns < 0 or row.delta_time_us < 0:
        raise TQHC2ProtocolError("包序号、相对时间和间隔不得为负")
    if row.burst_id < 0:
        raise TQHC2ProtocolError("burst_id 不得为负")
    if row.direction not in {-1, 1}:
        raise TQHC2ProtocolError("包方向只能为 -1 或 1")
    if row.network_length_bytes < 0:
        raise TQHC2ProtocolError("网络层长度不得为负")
    if row.payload_length_bytes is not None and row.payload_length_bytes < 0:
        raise TQHC2ProtocolError("载荷长度不得为负")
    if row.payload_length_observed != (row.payload_length_bytes is not None):
        raise TQHC2ProtocolError("载荷长度观测掩码与数值不一致")
    if row.transport_family not in TRANSPORT_FAMILIES:
        raise TQHC2ProtocolError(f"传输族不符合合同：{row.transport_family}")
    tcp = row.transport_family == "TCP"
    if row.tcp_flags_applicable != tcp:
        raise TQHC2ProtocolError("TCP 标志适用性与传输族不一致")
    if tcp and (row.tcp_flags is None or not 0 <= row.tcp_flags <= 0x1FF):
        raise TQHC2ProtocolError("TCP 标志必须是 0 至 0x1FF")
    if not tcp and row.tcp_flags is not None:
        raise TQHC2ProtocolError("非 TCP 包不得携带 TCP 标志")
    if row.is_first_packet != (row.packet_index == 0):
        raise TQHC2ProtocolError("首包标志必须与 packet_index=0 一致")
    boolean_fields = (
        "is_first_packet",
        "payload_length_observed",
        "tcp_flags_applicable",
        "truncation_mask",
        *(name for name in QUIC_PACKET_FIELDS if name.endswith(("_observed", "_applicable"))),
    )
    if any(not isinstance(getattr(row, name), bool) for name in boolean_fields):
        raise TQHC2ProtocolError("包观测掩码必须是布尔值")
    if row.quic_parser_version != QUIC_PARSER_VERSION:
        raise TQHC2ProtocolError("QUIC 解析器版本不符合合同")
    if row.quic_evidence_class not in QUIC_EVIDENCE_CLASSES:
        raise TQHC2ProtocolError("QUIC 证据类别不符合合同")
    for prefix in (
        "quic_header_form",
        "quic_version",
        "quic_v1_packet_type",
        "quic_fixed_bit",
        "quic_spin_bit",
        "quic_src_cid_length",
        "quic_dst_cid_length",
        "quic_cid_changed",
    ):
        value_name = f"{prefix}_bytes" if prefix.endswith("cid_length") else prefix
        if prefix == "quic_version":
            value_name = "quic_version_u32"
        _validate_observed_value(
            value_name,
            getattr(row, value_name),
            bool(getattr(row, f"{prefix}_observed")),
            bool(getattr(row, f"{prefix}_applicable")),
        )
    for bit_name in ("quic_header_form", "quic_fixed_bit", "quic_spin_bit"):
        value = getattr(row, bit_name)
        if value is not None and value not in {0, 1}:
            raise TQHC2ProtocolError(f"{bit_name} 只能为 0 或 1")
    if row.quic_version_u32 is not None and not 0 <= row.quic_version_u32 <= 0xFFFFFFFF:
        raise TQHC2ProtocolError("QUIC 版本超出 uint32")
    if row.quic_v1_packet_type is not None and row.quic_v1_packet_type not in set(
        _V1_PACKET_TYPES.values()
    ):
        raise TQHC2ProtocolError("QUIC v1 包类型不符合合同")
    for length in (
        row.quic_src_cid_length_bytes,
        row.quic_dst_cid_length_bytes,
    ):
        if length is not None and not 0 <= length <= 20:
            raise TQHC2ProtocolError("QUIC 连接标识长度必须为 0 至 20")


def _legacy_json_scalar(value: object) -> object:
    if value is None or isinstance(value, (str, bool, int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            return None
        return value
    if hasattr(value, "item"):
        return _legacy_json_scalar(value.item())
    raise TQHC2ProtocolError(f"基础序列值无法规范化：{type(value).__name__}")


def _legacy_sequence_sha256(rows: Sequence[PacketObservation]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        values: list[object] = []
        for name in _LEGACY_HASH_FIELDS:
            value = getattr(row, name)
            # 冻结候选按含 UDP 空值的整行组转为数据框，TCP 标志因此以浮点数入旧哈希。
            if name == "tcp_flags" and value is not None:
                value = float(value)
            values.append(_legacy_json_scalar(value))
        digest.update(
            json.dumps(
                values,
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("ascii")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _observation_records_sha256(rows: Sequence[Mapping[str, object]]) -> str:
    records: list[dict[str, object]] = []
    for row in rows:
        _validate_packet_field_order(tuple(row))
        records.append({name: row[name] for name in PACKET_OBSERVATION_FIELDS})
    return canonical_json_sha256(records)


def _fraction(count: int, denominator: int) -> float:
    return float(count / denominator)


def _masked_quic_fraction(
    rows: Sequence[PacketObservation],
    value_field: str,
    observed_field: str,
    *,
    observed_denominator: bool,
) -> tuple[float | None, int, int]:
    observed = [row for row in rows if bool(getattr(row, observed_field))]
    if not observed:
        return None, 1, 0
    ones = sum(int(bool(getattr(row, value_field))) for row in observed)
    denominator = len(observed) if observed_denominator else len(rows)
    return _fraction(ones, denominator), 0, 1


def _quic_evidence(rows: Sequence[PacketObservation]) -> str:
    present = {row.quic_evidence_class for row in rows}
    return next(name for name in QUIC_EVIDENCE_PRIORITY if name in present)


def aggregate_packet_sequence(rows: Sequence[PacketObservation]) -> TQHAggregates:
    """严格校验单样本序列并重算共同字段、协议比例与双序列哈希。"""

    if not rows:
        raise TQHC2ProtocolError("包序列不得为空")
    sample_id = rows[0].sample_id
    if any(row.sample_id != sample_id for row in rows):
        raise TQHC2ProtocolError("聚合输入只能包含一个 sample_id")
    for index, row in enumerate(rows):
        if row.packet_index != index:
            raise TQHC2ProtocolError(f"包序号不连续：{sample_id}:{row.packet_index}")
        if index == 0:
            if row.delta_time_us != 0 or not row.is_first_packet:
                raise TQHC2ProtocolError("首包间隔必须为 0 且首包标志必须为真")
        else:
            previous = rows[index - 1]
            if row.is_first_packet:
                raise TQHC2ProtocolError(
                    f"非首包不得设置首包标志：{sample_id}:{row.packet_index}"
                )
            relative_delta_ns = row.relative_time_ns - previous.relative_time_ns
            if relative_delta_ns < 0:
                if row.delta_time_us != 0:
                    raise TQHC2ProtocolError(
                        f"时间戳回退时包间隔必须截断为 0：{sample_id}:{row.packet_index}"
                    )
            elif previous.relative_time_ns == 0:
                expected_delta = relative_delta_ns // 1_000
                tolerance_us = _MATCH_TOLERANCE_NS // 1_000
                if not expected_delta <= row.delta_time_us <= expected_delta + tolerance_us:
                    raise TQHC2ProtocolError(
                        f"会话起点截断后的包间隔越界：{sample_id}:{row.packet_index}"
                    )
            else:
                expected_delta = relative_delta_ns // 1_000
                if row.delta_time_us != expected_delta:
                    raise TQHC2ProtocolError(
                        f"相邻包间隔不符合原始时间序列：{sample_id}:{row.packet_index}"
                    )
    families = {row.transport_family for row in rows}
    if len(families) != 1:
        raise TQHC2ProtocolError("单个 TQH 流样本不得混合传输族")
    transport_family = next(iter(families))
    packet_count = len(rows)
    lengths = [row.network_length_bytes for row in rows]
    total_bytes = sum(lengths)
    duration_us = max(row.relative_time_ns for row in rows) / 1_000.0
    duration_seconds = duration_us / 1_000_000.0
    common: dict[str, float | None] = {
        "total_packets": float(packet_count),
        "total_bytes": float(total_bytes),
        "packet_length_mean": float(total_bytes / packet_count),
        "packet_length_min": float(min(lengths)),
        "packet_length_max": float(max(lengths)),
        "iat_mean_ms": float(sum(row.delta_time_us for row in rows) / packet_count / 1_000.0),
        "packet_rate": (
            float(packet_count / duration_seconds) if duration_seconds > 0 else None
        ),
        "byte_rate": float(total_bytes / duration_seconds) if duration_seconds > 0 else None,
    }
    common_missing = {name: int(common[name] is None) for name in COMMON_FIELDS}
    tcp_rows = [row for row in rows if row.transport_family == "TCP"]
    fractions: dict[str, float | None] = {
        "tcp_packet_fraction": _fraction(len(tcp_rows), packet_count),
        "udp_packet_fraction": _fraction(
            sum(row.transport_family == "UDP" for row in rows), packet_count
        ),
        "icmp_packet_fraction": _fraction(
            sum(row.transport_family == "ICMP" for row in rows), packet_count
        ),
        "other_transport_packet_fraction": _fraction(
            sum(row.transport_family not in {"TCP", "UDP", "ICMP"} for row in rows),
            packet_count,
        ),
        "payload_observed_fraction": _fraction(
            sum(row.payload_length_observed for row in rows), packet_count
        ),
        "tcp_flags_applicable_fraction": _fraction(
            sum(row.tcp_flags_applicable for row in rows), packet_count
        ),
        "truncation_fraction": _fraction(
            sum(row.truncation_mask for row in rows), packet_count
        ),
    }
    for name, bit in (
        ("tcp_syn_packet_fraction", 0x02),
        ("tcp_ack_packet_fraction", 0x10),
        ("tcp_fin_packet_fraction", 0x01),
        ("tcp_rst_packet_fraction", 0x04),
        ("tcp_psh_packet_fraction", 0x08),
    ):
        fractions[name] = (
            _fraction(sum(bool(row.tcp_flags & bit) for row in tcp_rows), packet_count)
            if tcp_rows
            else None
        )
    if tuple(fractions) != AGGREGATE_FRACTION_FIELDS:
        fractions = {name: fractions[name] for name in AGGREGATE_FRACTION_FIELDS}

    udp_applicable = any(row.transport_family == "UDP" for row in rows)
    quic: dict[str, float | None] = {}
    quic_missing: dict[str, int] = {}
    quic_applicable: dict[str, int] = {}

    def set_quic(name: str, value: float | None, applicable: bool) -> None:
        quic[name] = value
        quic_missing[name] = int(value is None)
        quic_applicable[name] = int(applicable)

    evidence = _quic_evidence(rows)
    for name, evidence_name in (
        ("quic_observed_packet_fraction", None),
        ("quic_v1_long_packet_fraction", "V1_LONG_HEADER"),
        ("quic_context_short_packet_fraction", "CONTEXT_BOUND_SHORT_HEADER"),
        ("quic_ambiguous_packet_fraction", "AMBIGUOUS"),
    ):
        if not udp_applicable:
            set_quic(name, None, False)
            continue
        if evidence_name is None:
            count = sum(row.quic_evidence_class != "NONE" for row in rows)
        else:
            count = sum(row.quic_evidence_class == evidence_name for row in rows)
        set_quic(name, _fraction(count, packet_count), True)

    for name, value_field, observed_field in (
        (
            "quic_fixed_bit_one_fraction",
            "quic_fixed_bit",
            "quic_fixed_bit_observed",
        ),
        (
            "quic_spin_bit_one_fraction",
            "quic_spin_bit",
            "quic_spin_bit_observed",
        ),
        (
            "quic_cid_changed_packet_fraction",
            "quic_cid_changed",
            "quic_cid_changed_observed",
        ),
    ):
        value, missing, applicable = _masked_quic_fraction(
            rows,
            value_field,
            observed_field,
            observed_denominator=name == "quic_cid_changed_packet_fraction",
        )
        quic[name] = value
        quic_missing[name] = missing
        quic_applicable[name] = applicable

    for name, value_field, observed_field in (
        (
            "quic_src_cid_length_mean",
            "quic_src_cid_length_bytes",
            "quic_src_cid_length_observed",
        ),
        (
            "quic_dst_cid_length_mean",
            "quic_dst_cid_length_bytes",
            "quic_dst_cid_length_observed",
        ),
    ):
        values = [
            float(getattr(row, value_field))
            for row in rows
            if bool(getattr(row, observed_field))
        ]
        set_quic(name, float(sum(values) / len(values)) if values else None, bool(values))

    return TQHAggregates(
        sample_id=sample_id,
        transport_family=transport_family,
        quic_evidence_class=evidence,
        common=common,
        common_missing=common_missing,
        fractions=fractions,
        quic=quic,
        quic_missing=quic_missing,
        quic_applicable=quic_applicable,
        base_observation_sequence_sha256=_legacy_sequence_sha256(rows),
        observation_sequence_sha256=_observation_records_sha256(
            [row.as_record() for row in rows]
        ),
    )


def _require_pyarrow() -> tuple[Any, Any, Any]:
    try:
        import pyarrow as pa
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
    except ImportError as error:
        raise TQHC2ProtocolError("TQH R2 物化需要项目依赖 pyarrow") from error
    return pa, pc, pq


def _base_packet_schema(pa: Any) -> Any:
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


def _quic_packet_schema(pa: Any, *, internal: bool) -> Any:
    fields = [
        ("quic_header_form", pa.int8()),
        ("quic_header_form_observed", pa.bool_()),
        ("quic_header_form_applicable", pa.bool_()),
        ("quic_version_u32", pa.uint32()),
        ("quic_version_observed", pa.bool_()),
        ("quic_version_applicable", pa.bool_()),
        ("quic_v1_packet_type", pa.string()),
        ("quic_v1_packet_type_observed", pa.bool_()),
        ("quic_v1_packet_type_applicable", pa.bool_()),
        ("quic_fixed_bit", pa.int8()),
        ("quic_fixed_bit_observed", pa.bool_()),
        ("quic_fixed_bit_applicable", pa.bool_()),
        ("quic_spin_bit", pa.int8()),
        ("quic_spin_bit_observed", pa.bool_()),
        ("quic_spin_bit_applicable", pa.bool_()),
        ("quic_src_cid_length_bytes", pa.uint8()),
        ("quic_src_cid_length_observed", pa.bool_()),
        ("quic_src_cid_length_applicable", pa.bool_()),
        ("quic_dst_cid_length_bytes", pa.uint8()),
        ("quic_dst_cid_length_observed", pa.bool_()),
        ("quic_dst_cid_length_applicable", pa.bool_()),
        ("quic_cid_changed", pa.bool_()),
        ("quic_cid_changed_observed", pa.bool_()),
        ("quic_cid_changed_applicable", pa.bool_()),
        ("quic_parser_version", pa.string()),
    ]
    if internal:
        fields.append(("quic_evidence_class", pa.string()))
    return pa.schema(fields)


def _packet_schema(pa: Any) -> Any:
    base = _base_packet_schema(pa)
    quic = _quic_packet_schema(pa, internal=False)
    schema = pa.schema([*base, *quic])
    _validate_packet_field_order(tuple(schema.names))
    return schema


def _protocol_schema(pa: Any) -> Any:
    fields: list[tuple[str, Any]] = [
        ("sample_id", pa.string()),
        ("transport_family", pa.string()),
        ("transport_family_observed", pa.uint8()),
        ("quic_evidence_class", pa.string()),
        ("protocol_target", pa.string()),
    ]
    for name in COMMON_FIELDS:
        fields.extend(((name, pa.float64()), (f"{name}_missing", pa.uint8())))
    for name in AGGREGATE_FRACTION_FIELDS:
        fields.append((name, pa.float64()))
    for name in QUIC_AGGREGATE_FIELDS:
        fields.extend(
            (
                (name, pa.float64()),
                (f"{name}_missing", pa.uint8()),
                (f"{name}_applicable", pa.uint8()),
            )
        )
    schema = pa.schema(fields)
    if tuple(schema.names) != PROTOCOL_STAGE_FIELDS:
        raise TQHC2ProtocolError("协议阶段字段顺序偏离冻结合同")
    return schema


def _source_row_map_schema(pa: Any) -> Any:
    schema = pa.schema(
        [
            ("sample_id", pa.string()),
            ("source_binding_sha256", pa.string()),
            ("upstream_observation_sequence_sha256", pa.string()),
            ("base_observation_sequence_sha256", pa.string()),
            ("observation_sequence_sha256", pa.string()),
            ("quic_parser_version", pa.string()),
            ("protocol_target_evidence_sha256", pa.string()),
        ]
    )
    if tuple(schema.names) != SOURCE_ROW_MAP_FIELDS:
        raise TQHC2ProtocolError("TQH 源映射字段顺序偏离冻结合同")
    return schema


def _parquet_writer(pq: Any, path: Path, schema: Any, spec: ParquetWriteSpec) -> Any:
    return pq.ParquetWriter(
        path,
        schema,
        version=spec.version,
        compression=spec.compression,
        compression_level=spec.compression_level,
        use_dictionary=spec.use_dictionary,
        write_statistics=spec.write_statistics,
        data_page_version=spec.data_page_version,
    )


def _bucket(sample_id: str) -> int:
    digest = hashlib.sha256(sample_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % _BUCKET_COUNT


class _BucketSink:
    def __init__(self, root: Path, prefix: str, schema: Any, parquet: ParquetWriteSpec) -> None:
        self.root = root
        self.prefix = prefix
        self.schema = schema
        self.parquet = parquet
        self._writers: dict[int, Any] = {}
        self._buffers: dict[int, list[Mapping[str, object]]] = {}
        self.counts: Counter[int] = Counter()

    def path(self, bucket: int) -> Path:
        return self.root / f"{self.prefix}-{bucket:03d}.parquet"

    def _flush(self, bucket: int) -> None:
        rows = self._buffers.get(bucket, [])
        if not rows:
            return
        pa, _pc, pq = _require_pyarrow()
        writer = self._writers.get(bucket)
        if writer is None:
            writer = _parquet_writer(pq, self.path(bucket), self.schema, self.parquet)
            self._writers[bucket] = writer
        writer.write_table(
            pa.Table.from_pylist(list(rows), schema=self.schema),
            row_group_size=self.parquet.row_group_size,
        )
        rows.clear()

    def write(self, bucket: int, rows: Sequence[Mapping[str, object]]) -> None:
        if not rows:
            return
        next_count = self.counts[bucket] + len(rows)
        if next_count > _MAX_BUCKET_ROWS:
            raise TQHC2ProtocolError(
                f"稳定哈希桶超过有界内存门槛：{bucket}:{next_count}"
            )
        self.counts[bucket] = next_count
        buffer = self._buffers.setdefault(bucket, [])
        buffer.extend(rows)
        if len(buffer) >= _BUCKET_WRITE_BUFFER_ROWS:
            self._flush(bucket)

    def close(self) -> None:
        for bucket in sorted(self._buffers):
            self._flush(bucket)
        for writer in self._writers.values():
            writer.close()
        self._writers.clear()
        self._buffers.clear()


def _normalise_base_record(row: Mapping[str, object]) -> dict[str, object]:
    result = {name: row.get(name) for name in BASE_PACKET_FIELDS}
    result["sample_id"] = str(result["sample_id"] or "")
    for name in (
        "packet_index",
        "relative_time_ns",
        "delta_time_us",
        "direction",
        "network_length_bytes",
        "burst_id",
    ):
        value = result[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TQHC2ProtocolError(f"基础包字段 {name} 必须是整数")
        integer = int(value)
        if float(value) != integer:
            raise TQHC2ProtocolError(f"基础包字段 {name} 不得含小数")
        result[name] = integer
    for name in (
        "payload_length_bytes",
        "tcp_flags",
    ):
        value = result[name]
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TQHC2ProtocolError(f"基础包字段 {name} 必须是可空整数")
            integer = int(value)
            if float(value) != integer:
                raise TQHC2ProtocolError(f"基础包字段 {name} 不得含小数")
            result[name] = integer
    result["transport_family"] = str(result["transport_family"] or "").upper()
    for name in (
        "is_first_packet",
        "payload_length_observed",
        "tcp_flags_applicable",
        "truncation_mask",
    ):
        if not isinstance(result[name], bool):
            raise TQHC2ProtocolError(f"基础包字段 {name} 必须是布尔值")
    blank = _quic_observation()
    PacketObservation(
        **result,
        **blank.as_packet_fields(),
        quic_evidence_class=blank.evidence_class,
    )
    return result


def _profile_targets(
    bindings: TQHSourceBindings, selected_ids: frozenset[str]
) -> dict[str, frozenset[str]]:
    configured_profiles = set(bindings.config.tqhc2_profiles)
    seen_profiles: set[str] = set()
    claimed: dict[str, str] = {}
    targets: dict[str, frozenset[str]] = {}
    for binding in bindings.profiles:
        if binding.profile not in configured_profiles:
            raise TQHC2ProtocolError(f"TQH profile 不在任务01合同中：{binding.profile}")
        if binding.profile in seen_profiles:
            raise TQHC2ProtocolError(f"TQH profile 重复绑定：{binding.profile}")
        seen_profiles.add(binding.profile)
        profile_ids = frozenset(selected_ids.intersection(binding.expected_base_sequence_sha256))
        for sample_id in profile_ids:
            previous = claimed.setdefault(sample_id, binding.profile)
            if previous != binding.profile:
                raise TQHC2ProtocolError(f"样本被多个 profile 声明：{sample_id}")
        targets[binding.profile] = profile_ids
    if set(claimed) != set(selected_ids):
        missing = sorted(selected_ids.difference(claimed))
        raise TQHC2ProtocolError(
            f"冻结样本缺少唯一 profile 序列哈希绑定：{missing[0] if missing else ''}"
        )
    return targets


def _read_base_buckets(
    bindings: TQHSourceBindings,
    targets: Mapping[str, frozenset[str]],
    sink: _BucketSink,
) -> Counter[str]:
    pa, pc, pq = _require_pyarrow()
    counts: Counter[str] = Counter()
    base_fields = list(BASE_PACKET_FIELDS)
    by_profile = {binding.profile: binding for binding in bindings.profiles}
    try:
        for profile in sorted(by_profile):
            binding = by_profile[profile]
            target_ids = targets[profile]
            if not target_ids:
                continue
            packet_path = Path(binding.packet_observations_path)
            parquet = pq.ParquetFile(packet_path)
            missing = sorted(set(BASE_PACKET_FIELDS).difference(parquet.schema_arrow.names))
            if missing:
                raise TQHC2ProtocolError(
                    f"{profile} 包表缺少基础字段：{','.join(missing)}"
                )
            value_set = pa.array(sorted(target_ids), type=pa.string())
            for row_group in range(parquet.num_row_groups):
                table = parquet.read_row_group(row_group, columns=base_fields)
                mask = pc.fill_null(pc.is_in(table["sample_id"], value_set=value_set), False)
                retained = table.filter(mask)
                grouped: dict[int, list[dict[str, object]]] = {}
                for raw in retained.to_pylist():
                    row = _normalise_base_record(raw)
                    bucket = _bucket(str(row["sample_id"]))
                    grouped.setdefault(bucket, []).append(row)
                    counts[profile] += 1
                for bucket, rows in grouped.items():
                    sink.write(bucket, rows)
            _LOGGER.info(
                "TQH 基础包表完成：profile=%s，保留包=%d",
                profile,
                counts[profile],
            )
    finally:
        sink.close()
    return counts


def _pcap_base_record(match: PcapPacketMatch, packet: ParsedPacket) -> dict[str, object]:
    return _normalise_base_record(
        {
            "sample_id": match.sample_id,
            "packet_index": match.packet_index,
            "relative_time_ns": match.relative_time_ns,
            "delta_time_us": match.delta_time_us,
            "direction": match.direction,
            "network_length_bytes": packet.network_length_bytes,
            "payload_length_bytes": packet.payload_length_bytes,
            "transport_family": packet.protocol.upper(),
            "tcp_flags": packet.tcp_flags,
            "burst_id": match.burst_id,
            "is_first_packet": match.is_first_packet,
            "payload_length_observed": packet.payload_length_bytes is not None,
            "tcp_flags_applicable": packet.protocol == "tcp",
            "truncation_mask": packet.capture_truncated,
        }
    )


def _read_quic_buckets(
    bindings: TQHSourceBindings,
    targets: Mapping[str, frozenset[str]],
    sink: _BucketSink,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    by_profile = {binding.profile: binding for binding in bindings.profiles}
    try:
        for profile in sorted(by_profile):
            binding = by_profile[profile]
            target_ids = targets[profile]
            if not target_ids:
                continue
            if not binding.pcap_sources:
                raise TQHC2ProtocolError(f"{profile} 有目标样本但未绑定 PCAP 源")
            logical_ids = [source.logical_id for source in binding.pcap_sources]
            if len(logical_ids) != len(set(logical_ids)) or any(not item for item in logical_ids):
                raise TQHC2ProtocolError(f"{profile} PCAP 逻辑标识必须非空且唯一")
            contexts = _QuicContextRegistry(target_ids)
            for source in sorted(binding.pcap_sources, key=lambda item: item.logical_id):
                source_rows = 0
                for frame in iter_pcap(source.path):
                    parsed = parse_ip_packet(frame)
                    packet = parsed.packet
                    if parsed.status != "parsed" or packet is None:
                        continue
                    match = source.match_packet(frame, packet)
                    if match is None or match.sample_id not in target_ids:
                        continue
                    context = contexts.for_sample(match.sample_id)
                    quic = parse_quic_wire_image(frame, context)
                    base = _pcap_base_record(match, packet)
                    record = {
                        **base,
                        **quic.as_packet_fields(),
                        "quic_evidence_class": quic.evidence_class,
                    }
                    sink.write(_bucket(match.sample_id), [record])
                    counts[profile] += 1
                    source_rows += 1
                _LOGGER.info(
                    "TQH PCAP 完成：profile=%s，source=%s，保留包=%d，累计包=%d",
                    profile,
                    source.logical_id,
                    source_rows,
                    counts[profile],
                )
    finally:
        sink.close()
    return counts


def _table_sorted_rows(path: Path, schema: Any) -> list[dict[str, object]]:
    _pa, pc, pq = _require_pyarrow()
    table = pq.read_table(path, schema=schema)
    indices = pc.sort_indices(
        table,
        sort_keys=[("sample_id", "ascending"), ("packet_index", "ascending")],
    )
    return table.take(indices).to_pylist()


def _packet_from_joined(
    base: Mapping[str, object], quic: Mapping[str, object]
) -> PacketObservation:
    for name in BASE_PACKET_FIELDS:
        if base.get(name) != quic.get(name):
            raise TQHC2ProtocolError(
                f"PCAP 与上游基础包字段不一致：{base.get('sample_id')}:{base.get('packet_index')}:{name}"
            )
    return PacketObservation(
        **{name: base[name] for name in BASE_PACKET_FIELDS},
        **{name: quic[name] for name in QUIC_PACKET_FIELDS},
        quic_evidence_class=str(quic["quic_evidence_class"]),
    )


def _verified_protocol_truth_index(
    bindings: TQHSourceBindings,
) -> dict[tuple[str, str], _VerifiedProtocolTarget]:
    if not bindings.protocol_truth_evidence:
        if any(binding.trusted_protocol_targets for binding in bindings.profiles):
            raise TQHC2ProtocolError("可信协议真值缺少锁定证据文件")
        return {}
    source_lock = bindings.source_lock
    if source_lock is None:
        raise TQHC2ProtocolError("可信协议真值必须绑定任务01源锁")
    config = bindings.config
    if (
        source_lock.schema_version != _SOURCE_LOCK_SCHEMA_VERSION
        or source_lock.config_sha256 != config.config_sha256
        or source_lock.dataset_version != config.dataset_version
        or source_lock.stage != config.stage
        or source_lock.status != config.status
    ):
        raise TQHC2ProtocolError("协议真值源锁与任务01配置不一致")

    lock_by_path: dict[str, SourceArtifactLock] = {}
    for artifact in source_lock.tqhc2_artifacts:
        if artifact.logical_path in lock_by_path:
            raise TQHC2ProtocolError(
                f"任务01源锁含重复协议真值逻辑路径：{artifact.logical_path}"
            )
        lock_by_path[artifact.logical_path] = artifact

    evidence_paths: set[str] = set()
    verified: dict[tuple[str, str], _VerifiedProtocolTarget] = {}
    for evidence in bindings.protocol_truth_evidence:
        logical_path = evidence.logical_path
        if not logical_path or logical_path in evidence_paths:
            raise TQHC2ProtocolError("协议真值证据逻辑路径必须非空且唯一")
        evidence_paths.add(logical_path)
        artifact = lock_by_path.get(logical_path)
        if artifact is None:
            raise TQHC2ProtocolError(
                f"协议真值证据不在任务01源锁中：{logical_path}"
            )
        if artifact.role not in _PROTOCOL_TRUTH_LOCK_ROLES:
            raise TQHC2ProtocolError(
                f"协议真值源锁角色不受信任：{logical_path}:{artifact.role}"
            )
        if artifact.evidence_status == "blocked":
            raise TQHC2ProtocolError(f"协议真值证据仍被阻塞：{logical_path}")
        path = Path(evidence.path)
        if not path.is_file():
            raise TQHC2ProtocolError(f"协议真值证据文件不存在：{logical_path}")
        if path.stat().st_size != artifact.size_bytes:
            raise TQHC2ProtocolError(f"协议真值证据大小与源锁不一致：{logical_path}")
        if _sha256_file(path) != artifact.sha256:
            raise TQHC2ProtocolError(f"协议真值证据摘要与源锁不一致：{logical_path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TQHC2ProtocolError(
                f"协议真值证据不是有效 UTF-8 JSON：{logical_path}"
            ) from error
        if not isinstance(payload, dict) or set(payload) != {
            "schema_version",
            "evidence_kind",
            "input_fields",
            "samples",
        }:
            raise TQHC2ProtocolError(f"协议真值证据顶层结构不符合合同：{logical_path}")
        if payload["schema_version"] != _PROTOCOL_TRUTH_SCHEMA_VERSION:
            raise TQHC2ProtocolError(f"协议真值证据模式版本不符合合同：{logical_path}")
        evidence_kind = payload["evidence_kind"]
        if not isinstance(evidence_kind, str) or evidence_kind not in _PROTOCOL_TRUTH_KINDS:
            raise TQHC2ProtocolError(f"协议真值证据类型不受信任：{logical_path}")
        input_fields = payload["input_fields"]
        if (
            not isinstance(input_fields, list)
            or not input_fields
            or any(not isinstance(name, str) or not name for name in input_fields)
            or len(input_fields) != len(set(input_fields))
            or "sample_id" not in input_fields
        ):
            raise TQHC2ProtocolError(f"协议真值输入字段清单无效：{logical_path}")
        forbidden = sorted(set(input_fields).difference(_PROTOCOL_TRUTH_INPUT_FIELDS))
        if forbidden:
            raise TQHC2ProtocolError(
                f"协议真值输入字段不在显式允许清单：{logical_path}:{','.join(forbidden)}"
            )
        samples = payload["samples"]
        if not isinstance(samples, list) or not samples:
            raise TQHC2ProtocolError(f"协议真值证据没有样本映射：{logical_path}")
        for row in samples:
            if not isinstance(row, dict) or set(row) != {
                "sample_id",
                "protocol_target",
            }:
                raise TQHC2ProtocolError(
                    f"协议真值样本映射结构不符合合同：{logical_path}"
                )
            sample_id = row["sample_id"]
            target = row["protocol_target"]
            if not isinstance(sample_id, str) or not sample_id:
                raise TQHC2ProtocolError(f"协议真值 sample_id 无效：{logical_path}")
            if target not in PROTOCOL_TARGETS:
                raise TQHC2ProtocolError(f"协议真值目标不符合枚举：{logical_path}")
            key = (logical_path, sample_id)
            if key in verified:
                raise TQHC2ProtocolError(
                    f"协议真值证据含重复样本映射：{logical_path}:{sample_id}"
                )
            verified[key] = _VerifiedProtocolTarget(
                target=target,
                evidence_sha256=artifact.sha256,
                profile=artifact.profile,
            )
    return verified


def _validate_trusted_protocol_targets(
    bindings: TQHSourceBindings,
    verified: Mapping[tuple[str, str], _VerifiedProtocolTarget],
) -> None:
    for binding in bindings.profiles:
        for sample_id, trusted in binding.trusted_protocol_targets.items():
            if sample_id not in binding.expected_base_sequence_sha256:
                raise TQHC2ProtocolError(
                    f"协议真值样本未绑定上游基础序列：{binding.profile}:{sample_id}"
                )
            key = (trusted.evidence_logical_path, sample_id)
            resolved = verified.get(key)
            if resolved is None:
                raise TQHC2ProtocolError(
                    f"锁定协议真值证据未覆盖样本：{trusted.evidence_logical_path}:{sample_id}"
                )
            if resolved.profile not in {None, binding.profile}:
                raise TQHC2ProtocolError(
                    f"协议真值证据 profile 与样本绑定冲突：{sample_id}"
                )
            if resolved.target != trusted.target:
                raise TQHC2ProtocolError(
                    f"协议真值目标与锁定证据映射冲突：{sample_id}"
                )


def _trusted_target(
    binding: TQHProfileBinding,
    aggregate: TQHAggregates,
    verified: Mapping[tuple[str, str], _VerifiedProtocolTarget],
) -> tuple[str, str | None]:
    trusted = binding.trusted_protocol_targets.get(aggregate.sample_id)
    if trusted is not None:
        if trusted.target not in PROTOCOL_TARGETS:
            raise TQHC2ProtocolError(f"可信协议真值不符合枚举：{trusted.target}")
        if trusted.target == "QUIC" and aggregate.transport_family != "UDP":
            raise TQHC2ProtocolError("QUIC 真值只能绑定 UDP 传输样本")
        if trusted.target not in {"QUIC", "UNKNOWN", aggregate.transport_family}:
            raise TQHC2ProtocolError("协议真值与直接观测传输族冲突")
        resolved = verified.get((trusted.evidence_logical_path, aggregate.sample_id))
        if resolved is None or resolved.target != trusted.target:
            raise TQHC2ProtocolError("协议真值未通过锁定证据解析")
        return trusted.target, resolved.evidence_sha256
    if aggregate.transport_family == "UDP":
        return "UNKNOWN", None
    return aggregate.transport_family, None


def _write_sorted_bucket(
    bucket: int,
    base_path: Path,
    quic_path: Path,
    output_path: Path,
    bindings: TQHSourceBindings,
    profile_by_sample: Mapping[str, TQHProfileBinding],
    verified_truth: Mapping[tuple[str, str], _VerifiedProtocolTarget],
    protocol_rows: list[dict[str, object]],
    source_rows: list[dict[str, object]],
    evidence_counts: Counter[str],
    target_counts: Counter[str],
) -> int:
    pa, _pc, pq = _require_pyarrow()
    base_rows = _table_sorted_rows(base_path, _base_packet_schema(pa))
    quic_schema = pa.schema(
        [*_base_packet_schema(pa), *_quic_packet_schema(pa, internal=True)]
    )
    quic_rows = _table_sorted_rows(quic_path, quic_schema)
    base_keys = [(row["sample_id"], row["packet_index"]) for row in base_rows]
    quic_keys = [(row["sample_id"], row["packet_index"]) for row in quic_rows]
    if base_keys != quic_keys or len(base_keys) != len(set(base_keys)):
        raise TQHC2ProtocolError(f"稳定桶 {bucket} 的包主键不唯一或 PCAP 连接不完整")
    packet_schema = _packet_schema(pa)
    writer = _parquet_writer(pq, output_path, packet_schema, bindings.config.parquet)
    written = 0
    try:
        current_id: str | None = None
        sequence: list[PacketObservation] = []

        def flush_sequence() -> None:
            nonlocal sequence
            if not sequence:
                return
            aggregate = aggregate_packet_sequence(sequence)
            binding = profile_by_sample[aggregate.sample_id]
            expected = binding.expected_base_sequence_sha256[aggregate.sample_id]
            if not _is_sha256(expected) or expected != aggregate.base_observation_sequence_sha256:
                raise TQHC2ProtocolError(
                    f"旧基础序列哈希不匹配：{aggregate.sample_id}"
                )
            protocol_target, evidence_sha256 = _trusted_target(
                binding, aggregate, verified_truth
            )
            protocol_rows.append(aggregate.protocol_record(protocol_target))
            source_rows.append(
                {
                    "sample_id": aggregate.sample_id,
                    "source_binding_sha256": canonical_json_sha256(
                        {"profile": binding.profile, "sample_id": aggregate.sample_id}
                    ),
                    "upstream_observation_sequence_sha256": expected,
                    "base_observation_sequence_sha256": aggregate.base_observation_sequence_sha256,
                    "observation_sequence_sha256": aggregate.observation_sequence_sha256,
                    "quic_parser_version": QUIC_PARSER_VERSION,
                    "protocol_target_evidence_sha256": evidence_sha256,
                }
            )
            evidence_counts[aggregate.quic_evidence_class] += 1
            target_counts[protocol_target] += 1
            sequence = []

        chunk: list[dict[str, object]] = []
        for base, quic in zip(base_rows, quic_rows, strict=True):
            packet = _packet_from_joined(base, quic)
            if current_id is not None and packet.sample_id != current_id:
                flush_sequence()
            current_id = packet.sample_id
            sequence.append(packet)
            chunk.append(packet.as_record())
            if len(chunk) >= _WRITE_BATCH_ROWS:
                writer.write_table(
                    pa.Table.from_pylist(chunk, schema=packet_schema),
                    row_group_size=bindings.config.parquet.row_group_size,
                )
                written += len(chunk)
                chunk = []
        flush_sequence()
        if chunk:
            writer.write_table(
                pa.Table.from_pylist(chunk, schema=packet_schema),
                row_group_size=bindings.config.parquet.row_group_size,
            )
            written += len(chunk)
    finally:
        writer.close()
    return written


def _iter_parquet_rows(path: Path) -> Iterator[dict[str, object]]:
    _pa, _pc, pq = _require_pyarrow()
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(batch_size=2048):
        yield from batch.to_pylist()


def _merge_sorted_buckets(
    inputs: Sequence[Path], output: Path, spec: ParquetWriteSpec
) -> int:
    pa, _pc, pq = _require_pyarrow()
    schema = _packet_schema(pa)
    iterators = [_iter_parquet_rows(path) for path in inputs]
    heap: list[tuple[str, int, int, dict[str, object]]] = []
    for index, iterator in enumerate(iterators):
        try:
            row = next(iterator)
        except StopIteration:
            continue
        heapq.heappush(
            heap,
            (str(row["sample_id"]), int(row["packet_index"]), index, row),
        )
    partial = output.with_name(f"{output.name}.partial")
    writer = _parquet_writer(pq, partial, schema, spec)
    chunk: list[dict[str, object]] = []
    count = 0
    previous: tuple[str, int] | None = None
    try:
        while heap:
            sample_id, packet_index, source_index, row = heapq.heappop(heap)
            key = (sample_id, packet_index)
            if previous is not None and key <= previous:
                raise TQHC2ProtocolError("最终包表主键未严格递增")
            previous = key
            chunk.append(row)
            if len(chunk) >= _WRITE_BATCH_ROWS:
                writer.write_table(
                    pa.Table.from_pylist(chunk, schema=schema),
                    row_group_size=spec.row_group_size,
                )
                count += len(chunk)
                chunk = []
            try:
                following = next(iterators[source_index])
            except StopIteration:
                continue
            heapq.heappush(
                heap,
                (
                    str(following["sample_id"]),
                    int(following["packet_index"]),
                    source_index,
                    following,
                ),
            )
        if chunk:
            writer.write_table(
                pa.Table.from_pylist(chunk, schema=schema),
                row_group_size=spec.row_group_size,
            )
            count += len(chunk)
    finally:
        writer.close()
    os.replace(partial, output)
    return count


def _write_table(path: Path, rows: Sequence[Mapping[str, object]], schema: Any, spec: ParquetWriteSpec) -> None:
    pa, _pc, pq = _require_pyarrow()
    partial = path.with_name(f"{path.name}.partial")
    writer = _parquet_writer(pq, partial, schema, spec)
    try:
        writer.write_table(
            pa.Table.from_pylist(list(rows), schema=schema),
            row_group_size=spec.row_group_size,
        )
    finally:
        writer.close()
    os.replace(partial, path)


def _write_canonical_json(path: Path, value: object) -> None:
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    partial = path.with_name(f"{path.name}.partial")
    with partial.open("xb") as output:
        output.write(payload)
        output.flush()
        os.fsync(output.fileno())
    os.replace(partial, path)


def _validate_bindings(bindings: TQHSourceBindings) -> None:
    config = bindings.config
    _validate_packet_field_order(PACKET_OBSERVATION_FIELDS)
    if config.quic_parser_version != QUIC_PARSER_VERSION:
        raise TQHC2ProtocolError("任务01配置中的 QUIC 解析器版本不匹配")
    if config.common_fields != COMMON_FIELDS:
        raise TQHC2ProtocolError("任务01配置中的共同字段顺序不匹配")
    if config.aggregate_fraction_fields != AGGREGATE_FRACTION_FIELDS:
        raise TQHC2ProtocolError("任务01配置中的 12 个聚合比例顺序不匹配")
    if config.quic_aggregate_fields != QUIC_AGGREGATE_FIELDS:
        raise TQHC2ProtocolError("任务01配置中的 9 个 QUIC 聚合字段顺序不匹配")
    expected_enums = {
        "transport_family": TRANSPORT_FAMILIES,
        "protocol_target": PROTOCOL_TARGETS,
        "quic_evidence_class": QUIC_EVIDENCE_CLASSES,
        "quic_evidence_priority": QUIC_EVIDENCE_PRIORITY,
    }
    for name, expected in expected_enums.items():
        if name not in config.enum_values or tuple(config.enum_values[name]) != expected:
            raise TQHC2ProtocolError(f"任务01配置枚举顺序不匹配：{name}")
    if not bindings.profiles:
        raise TQHC2ProtocolError("至少需要一个 TQH profile 绑定")


def materialize_tqhc2_sequences(
    bindings: TQHSourceBindings,
    selected_ids: AbstractSet[str],
    work_dir: Path,
) -> TQHMaterialization:
    """对冻结样本做列裁剪、哈希分桶、PCAP 连接和确定性序列物化。"""

    _validate_bindings(bindings)
    frozen_ids = frozenset(str(sample_id) for sample_id in selected_ids)
    if not frozen_ids or any(not sample_id for sample_id in frozen_ids):
        raise TQHC2ProtocolError("冻结样本 ID 集必须非空且不含空字符串")
    verified_truth = _verified_protocol_truth_index(bindings)
    _validate_trusted_protocol_targets(bindings, verified_truth)
    targets = _profile_targets(bindings, frozen_ids)
    work_dir = Path(work_dir)
    if work_dir.exists():
        raise TQHC2ProtocolError(f"TQH 阶段目录已存在，拒绝覆盖：{work_dir}")
    work_dir.mkdir(parents=True)
    bucket_root = work_dir / ".packet-buckets"
    bucket_root.mkdir()
    pa, _pc, _pq = _require_pyarrow()
    base_sink = _BucketSink(
        bucket_root, "base", _base_packet_schema(pa), bindings.config.parquet
    )
    quic_internal_schema = pa.schema(
        [*_base_packet_schema(pa), *_quic_packet_schema(pa, internal=True)]
    )
    quic_sink = _BucketSink(
        bucket_root, "quic", quic_internal_schema, bindings.config.parquet
    )
    try:
        base_profile_counts = _read_base_buckets(bindings, targets, base_sink)
        pcap_profile_counts = _read_quic_buckets(bindings, targets, quic_sink)
        if base_profile_counts != pcap_profile_counts:
            raise TQHC2ProtocolError(
                f"上游包行与 PCAP 连接计数不一致：{dict(base_profile_counts)} != {dict(pcap_profile_counts)}"
            )
        profile_by_sample = {
            sample_id: binding
            for binding in bindings.profiles
            for sample_id in targets[binding.profile]
        }
        protocol_rows: list[dict[str, object]] = []
        source_rows: list[dict[str, object]] = []
        evidence_counts: Counter[str] = Counter()
        target_counts: Counter[str] = Counter()
        sorted_bucket_paths: list[Path] = []
        staged_packet_rows = 0
        for bucket in range(_BUCKET_COUNT):
            base_path = base_sink.path(bucket)
            quic_path = quic_sink.path(bucket)
            if base_path.exists() != quic_path.exists():
                raise TQHC2ProtocolError(f"稳定桶 {bucket} 缺少包表或 PCAP 连接侧")
            if not base_path.exists():
                continue
            sorted_path = bucket_root / f"sorted-{bucket:03d}.parquet"
            staged_packet_rows += _write_sorted_bucket(
                bucket,
                base_path,
                quic_path,
                sorted_path,
                bindings,
                profile_by_sample,
                verified_truth,
                protocol_rows,
                source_rows,
                evidence_counts,
                target_counts,
            )
            sorted_bucket_paths.append(sorted_path)
        if len(protocol_rows) != len(frozen_ids):
            raise TQHC2ProtocolError(
                f"物化样本数错误：期望 {len(frozen_ids)}，实际 {len(protocol_rows)}"
            )
        packet_path = work_dir / "packet-observations.parquet"
        packet_rows = _merge_sorted_buckets(
            sorted_bucket_paths, packet_path, bindings.config.parquet
        )
        if packet_rows != staged_packet_rows:
            raise TQHC2ProtocolError("最终包表行数与稳定桶行数不一致")
        protocol_rows.sort(key=lambda row: str(row["sample_id"]))
        source_rows.sort(key=lambda row: str(row["sample_id"]))
        protocol_path = work_dir / "protocol.parquet"
        source_map_path = work_dir / "source-row-map.parquet"
        _write_table(
            protocol_path,
            protocol_rows,
            _protocol_schema(pa),
            bindings.config.parquet,
        )
        _write_table(
            source_map_path,
            source_rows,
            _source_row_map_schema(pa),
            bindings.config.parquet,
        )
        artifact_sha256 = {
            "packet-observations.parquet": _sha256_file(packet_path),
            "protocol.parquet": _sha256_file(protocol_path),
            "source-row-map.parquet": _sha256_file(source_map_path),
        }
        audit = {
            "schema_version": "flow_probe_r2_tqhc2_sequence_audit_v1",
            "status": "pass",
            "quic_parser_version": QUIC_PARSER_VERSION,
            "selected_sample_count": len(frozen_ids),
            "packet_row_count": packet_rows,
            "profile_sample_counts": {
                profile: len(targets[profile]) for profile in sorted(targets)
            },
            "profile_packet_counts": dict(sorted(base_profile_counts.items())),
            "quic_evidence_counts": dict(sorted(evidence_counts.items())),
            "protocol_target_counts": dict(sorted(target_counts.items())),
            "artifacts": {
                name: {"sha256": digest}
                for name, digest in sorted(artifact_sha256.items())
            },
        }
        audit_path = work_dir / "sequence-audit.json"
        _write_canonical_json(audit_path, audit)
        artifact_sha256["sequence-audit.json"] = _sha256_file(audit_path)
        return TQHMaterialization(
            packet_observations_path=packet_path,
            protocol_path=protocol_path,
            source_row_map_path=source_map_path,
            sequence_audit_path=audit_path,
            packet_row_count=packet_rows,
            sample_count=len(frozen_ids),
            artifact_sha256=artifact_sha256,
        )
    except Exception:
        for path in work_dir.glob("*.partial"):
            try:
                path.unlink()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(bucket_root, ignore_errors=True)


_FORMAL_CANDIDATE_COLUMNS = (
    "sample_id",
    "profile",
    "dataset_version",
    "capture_id",
    "parent_session_id",
    "source_capture_sha256",
    "extractor_contract_sha256",
    "window_start_ns",
    "window_end_ns",
    "observation_sequence_sha256",
)
_TQH_PAYLOAD_FILES = (
    "packet-observations.parquet",
    "protocol.parquet",
    "source-row-map.parquet",
    "sequence-audit.json",
)


@dataclass(slots=True)
class _MatcherState:
    packet_count: int = 0
    previous_timestamp_ns: int | None = None
    previous_direction: int | None = None
    burst_id: int = 0


class _FrozenCellPacketMatcher:
    """复现旧提取器的会话匹配和逐会话包状态。"""

    def __init__(self, sessions: Sequence[Any], selected_ids: AbstractSet[str]) -> None:
        self._index = _session_index(sessions)
        self._selected_ids = frozenset(selected_ids)
        self._states = {
            session.uid: _MatcherState()
            for session in sessions
            if session.sample_id in self._selected_ids
        }

    def __call__(
        self, _frame: PcapFrame, packet: ParsedPacket
    ) -> PcapPacketMatch | None:
        status, reference = _match_packet(packet, self._index, _MATCH_TOLERANCE_NS)
        if status != "matched" or reference is None:
            return None
        session = reference.session
        if session.sample_id not in self._selected_ids:
            return None
        state = self._states[session.uid]
        first_packet = state.previous_timestamp_ns is None
        if first_packet:
            delta_time_us = 0
        else:
            delta_time_us = max(
                packet.timestamp_ns - int(state.previous_timestamp_ns), 0
            ) // 1_000
            if reference.direction != state.previous_direction:
                state.burst_id += 1
        result = PcapPacketMatch(
            sample_id=session.sample_id,
            packet_index=state.packet_count,
            relative_time_ns=max(packet.timestamp_ns - session.start_ns, 0),
            delta_time_us=delta_time_us,
            direction=reference.direction,
            burst_id=state.burst_id,
            is_first_packet=first_packet,
        )
        state.packet_count += 1
        state.previous_timestamp_ns = packet.timestamp_ns
        state.previous_direction = reference.direction
        return result


def _candidate_cell_name(profile: str, capture_id: str) -> str:
    parts = capture_id.split("-")
    if len(parts) < 5 or parts[-3] != profile:
        raise TQHC2ProtocolError(
            f"候选 capture_id 不能映射到 profile：{profile}:{capture_id}"
        )
    cell_name = f"{profile}_{parts[-2]}_{parts[-1]}"
    if not parts[-2].startswith("i") or not parts[-1].startswith("j"):
        raise TQHC2ProtocolError(f"候选 capture_id 缺少间隔或抖动：{capture_id}")
    return cell_name


def _single_value(rows: Sequence[Mapping[str, object]], name: str) -> object:
    values = {row.get(name) for row in rows}
    if len(values) != 1:
        raise TQHC2ProtocolError(f"同一 TQH cell 的 {name} 不唯一")
    return next(iter(values))


def _formal_candidate_rows(path: Path) -> list[dict[str, object]]:
    _pa, _pc, pq = _require_pyarrow()
    candidate_path = Path(path)
    parquet = pq.ParquetFile(candidate_path)
    missing = sorted(set(_FORMAL_CANDIDATE_COLUMNS).difference(parquet.schema_arrow.names))
    if missing:
        raise TQHC2ProtocolError(
            f"TQH 冻结候选缺少正式绑定字段：{','.join(missing)}"
        )
    rows = pq.read_table(candidate_path, columns=list(_FORMAL_CANDIDATE_COLUMNS)).to_pylist()
    if not rows:
        raise TQHC2ProtocolError("TQH 冻结候选为空")
    sample_ids = [str(row["sample_id"]) for row in rows]
    if len(sample_ids) != len(set(sample_ids)) or any(not item for item in sample_ids):
        raise TQHC2ProtocolError("TQH 冻结候选 sample_id 必须非空且唯一")
    for row in rows:
        profile = str(row["profile"])
        if profile not in {"A", "B", "C"}:
            raise TQHC2ProtocolError(f"TQH 冻结候选 profile 非法：{profile}")
        for name in (
            "source_capture_sha256",
            "extractor_contract_sha256",
            "observation_sequence_sha256",
        ):
            if not _is_sha256(str(row[name])):
                raise TQHC2ProtocolError(f"TQH 冻结候选 {name} 非法")
    return rows


def _single_pcap(raw_root: Path, cell_name: str) -> Path:
    cell_root = raw_root / cell_name
    paths = sorted(
        path
        for path in (*cell_root.glob("*.pcap"), *cell_root.glob("*.pcapng"))
        if path.is_file() and not path.is_symlink()
    )
    if len(paths) != 1:
        raise TQHC2ProtocolError(
            f"TQH cell 必须恰有一个普通 PCAP：{cell_name}:{len(paths)}"
        )
    return paths[0]


def build_formal_tqhc2_bindings(
    *,
    config: R2ProtocolConfig,
    candidate_samples_path: Path,
    raw_root: Path,
    profile_packet_paths: Mapping[str, Path],
) -> tuple[TQHSourceBindings, frozenset[str]]:
    """从冻结候选、原始标签和 PCAP 构造正式任务03输入。"""

    rows = _formal_candidate_rows(candidate_samples_path)
    raw_root = Path(raw_root)
    if not raw_root.is_dir():
        raise TQHC2ProtocolError(f"TQH 原始根不存在：{raw_root}")
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        profile = str(row["profile"])
        cell_name = _candidate_cell_name(profile, str(row["capture_id"]))
        grouped.setdefault((profile, cell_name), []).append(row)

    profile_sources: dict[str, list[TQHPcapSource]] = {name: [] for name in ("A", "B", "C")}
    profile_expected: dict[str, dict[str, str]] = {name: {} for name in ("A", "B", "C")}
    for (profile, cell_name), cell_rows in sorted(grouped.items()):
        dataset_version = str(_single_value(cell_rows, "dataset_version"))
        capture_sha256 = str(_single_value(cell_rows, "source_capture_sha256"))
        extractor_sha256 = str(_single_value(cell_rows, "extractor_contract_sha256"))
        pcap_path = _single_pcap(raw_root, cell_name)
        _LOGGER.info("核对 TQH PCAP 摘要：profile=%s，cell=%s", profile, cell_name)
        if _sha256_file(pcap_path) != capture_sha256:
            raise TQHC2ProtocolError(f"TQH PCAP 摘要变化：{profile}:{cell_name}")
        label_root = raw_root / profile / cell_name
        records, _audit = _load_cell_records(
            label_root,
            dataset_version=dataset_version,
            profile=profile,
        )
        sessions = [
            _label_to_session(
                record=record,
                dataset_version=dataset_version,
                pcap_sha256=capture_sha256,
                extractor_sha256=extractor_sha256,
            )
            for record in records
        ]
        sessions_by_sample = {session.sample_id: session for session in sessions}
        selected_ids = {str(row["sample_id"]) for row in cell_rows}
        if len(sessions_by_sample) != len(sessions):
            raise TQHC2ProtocolError(f"TQH 原始会话 sample_id 重复：{profile}:{cell_name}")
        for row in cell_rows:
            sample_id = str(row["sample_id"])
            session = sessions_by_sample.get(sample_id)
            if session is None:
                raise TQHC2ProtocolError(
                    f"冻结样本无法回接原始会话：{profile}:{cell_name}:{sample_id}"
                )
            if (
                session.uid != str(row["parent_session_id"])
                or session.start_ns != int(row["window_start_ns"])
                or session.end_ns != int(row["window_end_ns"])
            ):
                raise TQHC2ProtocolError(
                    f"冻结样本会话边界变化：{profile}:{cell_name}:{sample_id}"
                )
            profile_expected[profile][sample_id] = str(
                row["observation_sequence_sha256"]
            )
        matcher = _FrozenCellPacketMatcher(sessions, selected_ids)
        profile_sources[profile].append(
            TQHPcapSource(
                logical_id=f"tqhc2/{profile}/{cell_name}/{pcap_path.name}",
                path=pcap_path,
                match_packet=matcher,
            )
        )
        _LOGGER.info(
            "TQH cell 绑定完成：profile=%s，cell=%s，冻结样本=%d，原始会话=%d",
            profile,
            cell_name,
            len(selected_ids),
            len(sessions),
        )

    bindings: list[TQHProfileBinding] = []
    for profile in ("A", "B", "C"):
        packet_path = Path(profile_packet_paths[profile])
        if not packet_path.is_file() or packet_path.is_symlink():
            raise TQHC2ProtocolError(f"TQH 上游包表不存在：{profile}:{packet_path}")
        bindings.append(
            TQHProfileBinding(
                profile=profile,
                packet_observations_path=packet_path,
                expected_base_sequence_sha256=profile_expected[profile],
                pcap_sources=tuple(profile_sources[profile]),
            )
        )
    selected = frozenset(str(row["sample_id"]) for row in rows)
    if sum(len(value) for value in profile_expected.values()) != len(selected):
        raise TQHC2ProtocolError("TQH 正式绑定没有覆盖全部冻结候选")
    return TQHSourceBindings(config=config, profiles=tuple(bindings)), selected


@dataclass(frozen=True, slots=True)
class TQHArtifactFingerprint:
    relative_path: str
    size_bytes: int
    sha256: str
    row_count: int | None
    schema_sha256: str | None
    semantic_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "relative_path": self.relative_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "row_count": self.row_count,
            "schema_sha256": self.schema_sha256,
            "semantic_sha256": self.semantic_sha256,
        }


@dataclass(frozen=True, slots=True)
class TQHDeterministicComparison:
    schema_version: str
    status: str
    artifacts: tuple[TQHArtifactFingerprint, ...]
    payload_merkle_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "artifacts": [item.as_dict() for item in self.artifacts],
            "payload_merkle_sha256": self.payload_merkle_sha256,
        }


@dataclass(frozen=True, slots=True)
class TQHHandoffLocks:
    project_root: Path
    source_lock_path: Path
    tqhc2_source_lock_path: Path
    execution_code_lock_path: Path
    config_path: Path
    comparison_receipt_path: Path


@dataclass(frozen=True, slots=True)
class TQHHandoffBoundFile:
    role: str
    logical_path: str
    size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "logical_path": self.logical_path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class TQHHandoffManifest:
    schema_version: str
    dataset_version: str
    stage: str
    status: str
    bindings: tuple[TQHHandoffBoundFile, ...]
    artifacts: tuple[TQHArtifactFingerprint, ...]
    total_size_bytes: int
    payload_merkle_sha256: str
    comparison_object_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset_version": self.dataset_version,
            "stage": self.stage,
            "status": self.status,
            "bindings": [item.as_dict() for item in self.bindings],
            "artifacts": [item.as_dict() for item in self.artifacts],
            "total_size_bytes": self.total_size_bytes,
            "payload_merkle_sha256": self.payload_merkle_sha256,
            "comparison_object_sha256": self.comparison_object_sha256,
        }


@dataclass(frozen=True, slots=True)
class TQHHandoffReceipt:
    schema_version: str
    status: str
    manifest_sha256: str
    payload_merkle_sha256: str
    total_size_bytes: int
    artifact_count: int
    packet_row_count: int
    sample_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "manifest_sha256": self.manifest_sha256,
            "payload_merkle_sha256": self.payload_merkle_sha256,
            "total_size_bytes": self.total_size_bytes,
            "artifact_count": self.artifact_count,
            "packet_row_count": self.packet_row_count,
            "sample_count": self.sample_count,
        }


def _parquet_fingerprint(path: Path, relative_path: str) -> TQHArtifactFingerprint:
    pa, _pc, pq = _require_pyarrow()
    parquet = pq.ParquetFile(path)
    schema_rows = [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in parquet.schema_arrow
    ]
    schema_sha256 = canonical_json_sha256(schema_rows)
    batch_rows: list[dict[str, object]] = []
    row_count = 0
    for batch in parquet.iter_batches(batch_size=65_536):
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, batch.schema) as writer:
            writer.write_batch(batch)
        digest = hashlib.sha256(sink.getvalue().to_pybytes()).hexdigest()
        batch_rows.append(
            {"batch_index": len(batch_rows), "row_count": batch.num_rows, "sha256": digest}
        )
        row_count += batch.num_rows
    semantic_sha256 = canonical_json_sha256(
        {"schema_sha256": schema_sha256, "batches": batch_rows}
    )
    return TQHArtifactFingerprint(
        relative_path=relative_path,
        size_bytes=path.stat().st_size,
        sha256=_sha256_file(path),
        row_count=row_count,
        schema_sha256=schema_sha256,
        semantic_sha256=semantic_sha256,
    )


def _json_fingerprint(path: Path, relative_path: str) -> TQHArtifactFingerprint:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TQHC2ProtocolError(f"TQH JSON 制品无效：{relative_path}") from error
    return TQHArtifactFingerprint(
        relative_path=relative_path,
        size_bytes=path.stat().st_size,
        sha256=_sha256_file(path),
        row_count=None,
        schema_sha256=None,
        semantic_sha256=canonical_json_sha256(value),
    )


def _materialization_fingerprints(root: Path) -> tuple[TQHArtifactFingerprint, ...]:
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise TQHC2ProtocolError(f"TQH 物化根不是普通目录：{root}")
    actual = sorted(path.name for path in root.iterdir())
    if actual != sorted(_TQH_PAYLOAD_FILES):
        raise TQHC2ProtocolError(f"TQH 物化根文件集合不符合合同：{actual}")
    fingerprints: list[TQHArtifactFingerprint] = []
    for name in _TQH_PAYLOAD_FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise TQHC2ProtocolError(f"TQH 物化制品不是普通文件：{name}")
        if path.suffix == ".parquet":
            fingerprints.append(_parquet_fingerprint(path, name))
        else:
            fingerprints.append(_json_fingerprint(path, name))
    return tuple(fingerprints)


def compare_tqhc2_materializations(
    left: Path, right: Path
) -> TQHDeterministicComparison:
    """逐字节并独立核对行数、模式和语义载荷。"""

    left_items = _materialization_fingerprints(left)
    right_items = _materialization_fingerprints(right)
    if left_items != right_items:
        for left_item, right_item in zip(left_items, right_items, strict=True):
            if left_item != right_item:
                raise TQHC2ProtocolError(
                    f"TQH 双物化不一致：{left_item.relative_path}"
                )
        raise TQHC2ProtocolError("TQH 双物化文件集合不一致")
    payload_merkle_sha256 = canonical_json_sha256(
        [item.as_dict() for item in left_items]
    )
    return TQHDeterministicComparison(
        schema_version="flow_probe_r2_tqhc2_deterministic_comparison_v1",
        status="pass",
        artifacts=left_items,
        payload_merkle_sha256=payload_merkle_sha256,
    )


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise TQHC2ProtocolError("TQH 移交对象不能编码为规范 JSON") from error


def _regular_json(path: Path, description: str) -> Mapping[str, object]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise TQHC2ProtocolError(f"{description}不是普通文件：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TQHC2ProtocolError(f"{description}不是合法 JSON：{path}") from error
    if not isinstance(value, Mapping):
        raise TQHC2ProtocolError(f"{description}必须是 JSON 对象")
    return value


def _write_no_replace_json(path: Path, value: object, description: str) -> None:
    path = Path(path)
    if os.path.lexists(path):
        raise TQHC2ProtocolError(f"{description}已存在，拒绝覆盖：{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial")
    if os.path.lexists(partial):
        raise TQHC2ProtocolError(f"{description}临时文件已存在：{partial}")
    payload = _canonical_json_bytes(value)
    try:
        with partial.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.link(partial, path)
        partial.unlink()
    except FileExistsError as error:
        raise TQHC2ProtocolError(f"{description}并发出现，拒绝覆盖：{path}") from error
    except Exception:
        if os.path.lexists(partial):
            try:
                partial.unlink()
            except OSError:
                pass
        raise


def _materialization_from_root(root: Path) -> TQHMaterialization:
    root = Path(root)
    fingerprints = _materialization_fingerprints(root)
    by_name = {item.relative_path: item for item in fingerprints}
    audit = _regular_json(root / "sequence-audit.json", "TQH 序列审计")
    if audit.get("status") != "pass":
        raise TQHC2ProtocolError("TQH 序列审计状态不是 pass")
    packet_row_count = audit.get("packet_row_count")
    sample_count = audit.get("selected_sample_count")
    if not isinstance(packet_row_count, int) or not isinstance(sample_count, int):
        raise TQHC2ProtocolError("TQH 序列审计缺少整数行数")
    packet_item = by_name["packet-observations.parquet"]
    protocol_item = by_name["protocol.parquet"]
    source_map_item = by_name["source-row-map.parquet"]
    if packet_item.row_count != packet_row_count:
        raise TQHC2ProtocolError("TQH 包表行数与序列审计不一致")
    if protocol_item.row_count != sample_count or source_map_item.row_count != sample_count:
        raise TQHC2ProtocolError("TQH 样本表行数与序列审计不一致")
    return TQHMaterialization(
        packet_observations_path=root / "packet-observations.parquet",
        protocol_path=root / "protocol.parquet",
        source_row_map_path=root / "source-row-map.parquet",
        sequence_audit_path=root / "sequence-audit.json",
        packet_row_count=packet_row_count,
        sample_count=sample_count,
        artifact_sha256={item.relative_path: item.sha256 for item in fingerprints},
    )


def _materialization_root(materialization: TQHMaterialization) -> Path:
    paths = (
        materialization.packet_observations_path,
        materialization.protocol_path,
        materialization.source_row_map_path,
        materialization.sequence_audit_path,
    )
    parents = {Path(path).parent.resolve() for path in paths}
    if len(parents) != 1:
        raise TQHC2ProtocolError("TQH 物化四项载荷不在同一目录")
    return next(iter(parents))


def _bound_file(role: str, logical_path: str, path: Path) -> TQHHandoffBoundFile:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise TQHC2ProtocolError(f"TQH 移交绑定不是普通文件：{role}")
    return TQHHandoffBoundFile(
        role=role,
        logical_path=logical_path,
        size_bytes=path.stat().st_size,
        sha256=_sha256_file(path),
    )


def _validate_handoff_locks(
    locks: TQHHandoffLocks,
    comparison: TQHDeterministicComparison,
) -> tuple[TQHHandoffBoundFile, ...]:
    code_lock: ExecutionCodeLock = load_execution_code_lock(
        locks.execution_code_lock_path
    )
    verify_execution_code_lock(locks.project_root, code_lock)
    config = load_r2_config(locks.config_path)
    source_lock = _regular_json(locks.source_lock_path, "R2 source-lock.json")
    if source_lock.get("schema_version") != _SOURCE_LOCK_SCHEMA_VERSION:
        raise TQHC2ProtocolError("R2 source-lock.json 模式版本变化")
    if source_lock.get("dataset_version") != config.dataset_version:
        raise TQHC2ProtocolError("R2 源锁数据版本与配置不一致")
    if source_lock.get("stage") != config.stage or source_lock.get("status") != config.status:
        raise TQHC2ProtocolError("R2 源锁阶段或状态与配置不一致")
    if source_lock.get("config_sha256") != config.config_sha256:
        raise TQHC2ProtocolError("R2 源锁配置哈希与当前配置不一致")
    if source_lock.get("code_commit") != code_lock.code_commit:
        raise TQHC2ProtocolError("R2 源锁提交与执行代码锁不一致")
    execution_reference = source_lock.get("execution_code_lock")
    tqh_reference = source_lock.get("tqhc2_source_lock")
    if not isinstance(execution_reference, Mapping) or not isinstance(
        tqh_reference, Mapping
    ):
        raise TQHC2ProtocolError("R2 正式源锁缺少代码锁或 TQH 子锁绑定")
    if execution_reference.get("logical_path") != "execution-code-lock.json":
        raise TQHC2ProtocolError("R2 源锁中的执行代码锁逻辑路径变化")
    if execution_reference.get("sha256") != _sha256_file(
        locks.execution_code_lock_path
    ):
        raise TQHC2ProtocolError("R2 源锁中的执行代码锁哈希不一致")
    if tqh_reference.get("logical_path") != "tqhc2-source-lock.jsonl":
        raise TQHC2ProtocolError("R2 源锁中的 TQH 子锁逻辑路径变化")
    if tqh_reference.get("sha256") != _sha256_file(locks.tqhc2_source_lock_path):
        raise TQHC2ProtocolError("R2 源锁中的 TQH 子锁哈希不一致")
    extractor_evidence: dict[str, tuple[str, str]] = {}
    try:
        with Path(locks.tqhc2_source_lock_path).open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.endswith("\n") or not line.strip():
                    raise TQHC2ProtocolError(
                        f"TQH 子锁含非规范行：{line_number}"
                    )
                row = json.loads(line)
                if not isinstance(row, Mapping):
                    raise TQHC2ProtocolError("TQH 子锁行必须是对象")
                if row.get("role") == "extractor_source":
                    profile = row.get("profile")
                    mode = row.get("evidence_mode")
                    status = row.get("evidence_status")
                    if not all(isinstance(value, str) for value in (profile, mode, status)):
                        raise TQHC2ProtocolError("TQH 提取器子锁证据字段无效")
                    extractor_evidence[str(profile)] = (str(mode), str(status))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TQHC2ProtocolError("无法读取 TQH 子锁") from error
    if extractor_evidence != {
        "A": ("approved_manifest_only_blocked", "blocked"),
        "B": ("verified_snapshot", "verified"),
        "C": ("approved_manifest_only_blocked", "blocked"),
    }:
        raise TQHC2ProtocolError("A/B/C 提取器证据状态被提升、缺失或改变")
    comparison_document = _regular_json(
        locks.comparison_receipt_path, "TQH 双物化比较回执"
    )
    if dict(comparison_document) != comparison.as_dict():
        raise TQHC2ProtocolError("TQH 双物化比较回执与本次重算不一致")
    canonical_comparison = _canonical_json_bytes(comparison.as_dict())
    if Path(locks.comparison_receipt_path).read_bytes() != canonical_comparison:
        raise TQHC2ProtocolError("TQH 双物化比较回执不是规范 JSON 字节")
    bindings = (
        _bound_file("source_lock", "source-lock.json", locks.source_lock_path),
        _bound_file(
            "tqhc2_source_lock",
            "tqhc2-source-lock.jsonl",
            locks.tqhc2_source_lock_path,
        ),
        _bound_file(
            "execution_code_lock",
            "execution-code-lock.json",
            locks.execution_code_lock_path,
        ),
        _bound_file(
            "r2_protocol_config",
            "configs/r2_protocol_data_v1.yaml",
            locks.config_path,
        ),
        _bound_file(
            "double_materialization_comparison",
            "comparison.json",
            locks.comparison_receipt_path,
        ),
    )
    return tuple(sorted(bindings, key=lambda item: (item.role, item.logical_path)))


def _build_tqhc2_handoff_manifest(
    materialization: TQHMaterialization,
    comparison: TQHDeterministicComparison,
    locks: TQHHandoffLocks,
) -> TQHHandoffManifest:
    root = _materialization_root(materialization)
    artifacts = _materialization_fingerprints(root)
    if comparison.status != "pass" or comparison.artifacts != artifacts:
        raise TQHC2ProtocolError("TQH 物化与双构建比较对象不一致")
    if comparison.payload_merkle_sha256 != canonical_json_sha256(
        [item.as_dict() for item in artifacts]
    ):
        raise TQHC2ProtocolError("TQH 双构建载荷 Merkle 不一致")
    if materialization.artifact_sha256 != {
        item.relative_path: item.sha256 for item in artifacts
    }:
        raise TQHC2ProtocolError("TQH 物化对象登记哈希与实物不一致")
    config = load_r2_config(locks.config_path)
    bindings = _validate_handoff_locks(locks, comparison)
    return TQHHandoffManifest(
        schema_version="flow_probe_r2_tqhc2_handoff_manifest_v1",
        dataset_version=config.dataset_version,
        stage=config.stage,
        status=config.status,
        bindings=bindings,
        artifacts=artifacts,
        total_size_bytes=sum(item.size_bytes for item in artifacts),
        payload_merkle_sha256=comparison.payload_merkle_sha256,
        comparison_object_sha256=canonical_json_sha256(comparison.as_dict()),
    )


def write_tqhc2_handoff(
    materialization: TQHMaterialization,
    comparison: TQHDeterministicComparison,
    locks: TQHHandoffLocks,
    output: Path,
) -> TQHHandoffManifest:
    """写出只绑定规范逻辑路径、锁和双物化对象的正式移交清单。"""

    manifest = _build_tqhc2_handoff_manifest(materialization, comparison, locks)
    _write_no_replace_json(output, manifest.as_dict(), "TQH 移交清单")
    return manifest


def verify_tqhc2_handoff(
    root: Path,
    manifest: TQHHandoffManifest,
    locks: TQHHandoffLocks,
) -> TQHHandoffReceipt:
    """重新核对移交根文件集合、模式、行数、语义、源锁和代码锁。"""

    materialization = _materialization_from_root(root)
    comparison = compare_tqhc2_materializations(root, root)
    expected_manifest = _build_tqhc2_handoff_manifest(
        materialization, comparison, locks
    )
    if expected_manifest != manifest:
        raise TQHC2ProtocolError("TQH 移交清单与当前载荷或锁不一致")
    return TQHHandoffReceipt(
        schema_version="flow_probe_r2_tqhc2_handoff_receipt_v1",
        status="pass",
        manifest_sha256=hashlib.sha256(
            _canonical_json_bytes(manifest.as_dict())
        ).hexdigest(),
        payload_merkle_sha256=manifest.payload_merkle_sha256,
        total_size_bytes=manifest.total_size_bytes,
        artifact_count=len(manifest.artifacts),
        packet_row_count=materialization.packet_row_count,
        sample_count=materialization.sample_count,
    )


def _absolute_parameter_path(
    parameters: Mapping[str, object], key: str, description: str
) -> Path:
    raw_value = parameters.get(key)
    if not isinstance(raw_value, str) or not raw_value:
        raise TQHC2ProtocolError(f"{description}必须是非空绝对路径")
    path = Path(raw_value)
    if not path.is_absolute():
        raise TQHC2ProtocolError(f"{description}必须是绝对路径")
    return path


def _assert_regular_file_set(root: Path, expected_names: Sequence[str]) -> None:
    if root.is_symlink() or not root.is_dir():
        raise TQHC2ProtocolError(f"TQH 锁定根不是普通目录：{root}")
    actual_names = sorted(path.name for path in root.iterdir())
    if actual_names != sorted(expected_names):
        raise TQHC2ProtocolError(
            f"TQH 锁定根文件集合变化：期望 {sorted(expected_names)}，实际 {actual_names}"
        )
    for name in expected_names:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise TQHC2ProtocolError(f"TQH 锁定制品不是普通文件：{name}")


def run_formal_tqhc2_handoff(parameters_path: Path) -> Mapping[str, object]:
    """在一次正式运行内完成双物化复算、锁绑定、发布和本机消费验收。"""

    parameters_path = Path(parameters_path)
    parameters = _regular_json(parameters_path, "TQH 正式移交参数")
    expected_keys = {
        "schema_version",
        "host_role",
        "project_root",
        "project_data_root",
        "python_executable",
        "config_path",
        "build_a",
        "build_b",
        "handoff_root",
        "source_lock_root",
        "comparison_receipt",
        "receipt_path",
        "expected_handoff_bytes",
    }
    if set(parameters) != expected_keys:
        raise TQHC2ProtocolError("TQH 正式移交参数字段集合变化")
    if parameters.get("schema_version") != "flow_probe_r2_tqhc2_handoff_params_v1":
        raise TQHC2ProtocolError("TQH 正式移交参数模式版本变化")
    if parameters.get("host_role") != "local_producer":
        raise TQHC2ProtocolError("本机移交只允许 local_producer 主机角色")
    project_root = _absolute_parameter_path(parameters, "project_root", "代码项目根")
    project_data_root = _absolute_parameter_path(
        parameters, "project_data_root", "数据项目根"
    )
    python_executable = _absolute_parameter_path(
        parameters, "python_executable", "正式 Python 解释器"
    )
    if Path(sys.executable).resolve() != python_executable.resolve():
        raise TQHC2ProtocolError("TQH 正式移交 Python 解释器与参数不一致")
    build_a = _absolute_parameter_path(parameters, "build_a", "build-a 根")
    build_b = _absolute_parameter_path(parameters, "build_b", "build-b 根")
    handoff_root = _absolute_parameter_path(parameters, "handoff_root", "TQH 规范移交根")
    source_lock_root = _absolute_parameter_path(
        parameters, "source_lock_root", "R2 源锁根"
    )
    comparison_receipt = _absolute_parameter_path(
        parameters, "comparison_receipt", "双物化比较回执"
    )
    receipt_path = _absolute_parameter_path(parameters, "receipt_path", "本机移交回执")
    if parameters.get("config_path") != "configs/r2_protocol_data_v1.yaml":
        raise TQHC2ProtocolError("TQH 正式移交配置路径不符合固定合同")
    expected_paths = {
        "build_a": project_data_root
        / "runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-a.partial",
        "build_b": project_data_root
        / "runs/data-frozen/r2-protocol-tqhc2-handoff-v0.build-b.partial",
        "handoff_root": project_data_root
        / "runs/data-frozen/r2-protocol-tqhc2-handoff-v0",
        "source_lock_root": project_data_root
        / "runs/data-freeze-configs/r2-protocol-v1",
    }
    actual_paths = {
        "build_a": build_a,
        "build_b": build_b,
        "handoff_root": handoff_root,
        "source_lock_root": source_lock_root,
    }
    for name, expected in expected_paths.items():
        if actual_paths[name] != expected:
            raise TQHC2ProtocolError(f"TQH 正式移交路径不符合固定合同：{name}")
    expected_handoff_bytes = parameters.get("expected_handoff_bytes")
    if expected_handoff_bytes != 858_993_460:
        raise TQHC2ProtocolError("TQH 移交制品上界必须固定为 858,993,460 字节")
    required_free_bytes = max(3_221_225_472, 3 * int(expected_handoff_bytes))
    available_bytes = shutil.disk_usage(project_data_root).free
    if available_bytes < required_free_bytes:
        raise TQHC2ProtocolError(
            f"本机 TQH 移交磁盘不足：需要 {required_free_bytes}，可用 {available_bytes}"
        )
    if os.path.lexists(handoff_root):
        raise TQHC2ProtocolError("TQH 规范移交根已存在，拒绝覆盖")
    source_lock_names = (
        "execution-code-lock.json",
        "genis-member-lock.jsonl",
        "source-lock.json",
        "tqhc2-source-lock.jsonl",
    )
    _assert_regular_file_set(source_lock_root, source_lock_names)
    config_path = project_root / "configs/r2_protocol_data_v1.yaml"
    locks = TQHHandoffLocks(
        project_root=project_root,
        source_lock_path=source_lock_root / "source-lock.json",
        tqhc2_source_lock_path=source_lock_root / "tqhc2-source-lock.jsonl",
        execution_code_lock_path=source_lock_root / "execution-code-lock.json",
        config_path=config_path,
        comparison_receipt_path=comparison_receipt,
    )
    comparison = compare_tqhc2_materializations(build_a, build_b)
    materialization = _materialization_from_root(build_a)
    manifest = _build_tqhc2_handoff_manifest(materialization, comparison, locks)
    if manifest.total_size_bytes > int(expected_handoff_bytes):
        raise TQHC2ProtocolError(
            "TQH 实物超过预注册移交上界，必须先更新发布根外尺寸回执与计划"
        )
    if build_a.parent.stat().st_dev != handoff_root.parent.stat().st_dev:
        raise TQHC2ProtocolError("TQH build-a 与规范移交根不在同一文件系统")
    if os.path.lexists(handoff_root):
        raise TQHC2ProtocolError("TQH 规范移交根并发出现，拒绝覆盖")
    os.rename(build_a, handoff_root)
    manifest_path = source_lock_root / "tqhc2-handoff-manifest.json"
    written_manifest = write_tqhc2_handoff(
        _materialization_from_root(handoff_root), comparison, locks, manifest_path
    )
    if written_manifest != manifest:
        raise TQHC2ProtocolError("TQH 移交清单在原子发布后发生变化")
    if manifest_path.read_bytes() != _canonical_json_bytes(manifest.as_dict()):
        raise TQHC2ProtocolError("TQH 移交清单落盘字节与验收对象不一致")
    _assert_regular_file_set(
        source_lock_root, (*source_lock_names, "tqhc2-handoff-manifest.json")
    )
    published_comparison = compare_tqhc2_materializations(handoff_root, build_b)
    if published_comparison != comparison:
        raise TQHC2ProtocolError("TQH 原子发布后与保留 build-b 不一致")
    handoff_receipt = verify_tqhc2_handoff(handoff_root, manifest, locks)
    receipt = {
        **handoff_receipt.as_dict(),
        "host_role": "local_producer",
        "params_sha256": _sha256_file(parameters_path),
        "required_free_bytes": required_free_bytes,
        "available_bytes": available_bytes,
        "handoff_root": str(handoff_root),
        "retained_build_b": str(build_b),
        "manifest_path": str(manifest_path),
        "comparison_receipt_sha256": _sha256_file(comparison_receipt),
    }
    _write_no_replace_json(receipt_path, receipt, "TQH 本机移交验收回执")
    return receipt


def _materialize_command(args: argparse.Namespace) -> None:
    config = load_r2_config(Path(args.config))
    bindings, selected = build_formal_tqhc2_bindings(
        config=config,
        candidate_samples_path=Path(args.candidate_samples),
        raw_root=Path(args.raw_root),
        profile_packet_paths={
            "A": Path(args.profile_a_packets),
            "B": Path(args.profile_b_packets),
            "C": Path(args.profile_c_packets),
        },
    )
    result = materialize_tqhc2_sequences(bindings, selected, Path(args.output))
    print(
        json.dumps(
            {
                "status": "completed",
                "sample_count": result.sample_count,
                "packet_row_count": result.packet_row_count,
                "artifact_sha256": dict(sorted(result.artifact_sha256.items())),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        flush=True,
    )


def _compare_command(args: argparse.Namespace) -> None:
    comparison = compare_tqhc2_materializations(Path(args.left), Path(args.right))
    payload = json.dumps(
        comparison.as_dict(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"
    if args.receipt:
        receipt = Path(args.receipt)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        if receipt.exists():
            raise TQHC2ProtocolError(f"比较回执已存在，拒绝覆盖：{receipt}")
        with receipt.open("xb") as output:
            output.write(payload.encode("utf-8"))
            output.flush()
            os.fsync(output.fileno())
    print(payload, end="", flush=True)


def _handoff_command(args: argparse.Namespace) -> None:
    receipt = run_formal_tqhc2_handoff(Path(args.params))
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R2 TQH-C2 正式协议派生物化")
    subparsers = parser.add_subparsers(dest="command", required=True)
    materialize = subparsers.add_parser("materialize")
    materialize.add_argument("--config", required=True)
    materialize.add_argument("--candidate-samples", required=True)
    materialize.add_argument("--raw-root", required=True)
    materialize.add_argument("--profile-a-packets", required=True)
    materialize.add_argument("--profile-b-packets", required=True)
    materialize.add_argument("--profile-c-packets", required=True)
    materialize.add_argument("--output", required=True)
    materialize.set_defaults(handler=_materialize_command)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--left", required=True)
    compare.add_argument("--right", required=True)
    compare.add_argument("--receipt")
    compare.set_defaults(handler=_compare_command)
    handoff = subparsers.add_parser("handoff")
    handoff.add_argument("--params", required=True)
    handoff.set_defaults(handler=_handoff_command)
    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
