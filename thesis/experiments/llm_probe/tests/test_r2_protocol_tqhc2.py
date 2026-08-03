from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from flow_probe.r2_protocol_contract import (
    GeNISArchiveInventory,
    SourceArtifactLock,
    SourceLock,
    load_r2_config,
)
from flow_probe.r2_protocol_tqhc2 import (
    BASE_PACKET_FIELDS,
    PACKET_OBSERVATION_FIELDS,
    PROTOCOL_STAGE_FIELDS,
    QUIC_PACKET_FIELDS,
    QUIC_PARSER_VERSION,
    SOURCE_ROW_MAP_FIELDS,
    PacketObservation,
    PcapPacketMatch,
    QuicConnectionContext,
    TQHProfileBinding,
    TQHPcapSource,
    TQHProtocolTruthEvidence,
    TQHSourceBindings,
    TQHC2ProtocolError,
    TrustedProtocolTarget,
    _QuicContextRegistry,
    _base_packet_schema,
    _legacy_sequence_sha256,
    _observation_records_sha256,
    _packet_schema,
    _quic_observation,
    _read_quic_buckets,
    _validate_bindings,
    _validate_packet_field_order,
    aggregate_packet_sequence,
    materialize_tqhc2_sequences,
    parse_quic_wire_image,
)
from flow_probe.tqh_c2 import PcapFrame, parse_ip_packet

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "r2_protocol_data_v1.yaml"

_GOLDEN_BASE_PACKET_FIELDS = (
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

_GOLDEN_QUIC_PACKET_FIELDS = (
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

_GOLDEN_PACKET_FIELDS = (
    *_GOLDEN_BASE_PACKET_FIELDS,
    *_GOLDEN_QUIC_PACKET_FIELDS,
)

_GOLDEN_PACKET_TYPES = (
    ("sample_id", "string"),
    ("packet_index", "int32"),
    ("relative_time_ns", "int64"),
    ("delta_time_us", "int64"),
    ("direction", "int8"),
    ("network_length_bytes", "int32"),
    ("payload_length_bytes", "int32"),
    ("transport_family", "string"),
    ("tcp_flags", "int16"),
    ("burst_id", "int32"),
    ("is_first_packet", "bool"),
    ("payload_length_observed", "bool"),
    ("tcp_flags_applicable", "bool"),
    ("truncation_mask", "bool"),
    ("quic_header_form", "int8"),
    ("quic_header_form_observed", "bool"),
    ("quic_header_form_applicable", "bool"),
    ("quic_version_u32", "uint32"),
    ("quic_version_observed", "bool"),
    ("quic_version_applicable", "bool"),
    ("quic_v1_packet_type", "string"),
    ("quic_v1_packet_type_observed", "bool"),
    ("quic_v1_packet_type_applicable", "bool"),
    ("quic_fixed_bit", "int8"),
    ("quic_fixed_bit_observed", "bool"),
    ("quic_fixed_bit_applicable", "bool"),
    ("quic_spin_bit", "int8"),
    ("quic_spin_bit_observed", "bool"),
    ("quic_spin_bit_applicable", "bool"),
    ("quic_src_cid_length_bytes", "uint8"),
    ("quic_src_cid_length_observed", "bool"),
    ("quic_src_cid_length_applicable", "bool"),
    ("quic_dst_cid_length_bytes", "uint8"),
    ("quic_dst_cid_length_observed", "bool"),
    ("quic_dst_cid_length_applicable", "bool"),
    ("quic_cid_changed", "bool"),
    ("quic_cid_changed_observed", "bool"),
    ("quic_cid_changed_applicable", "bool"),
    ("quic_parser_version", "string"),
)


def _udp_frame(
    payload: bytes,
    *,
    timestamp_ns: int = 0,
    source_octet: int = 1,
    source_port: int = 10_000,
    destination_port: int = 443,
    capture_truncated: bool = False,
) -> PcapFrame:
    udp_length = 8 + len(payload)
    ip_length = 20 + udp_length
    ethernet = b"\x00" * 12 + b"\x08\x00"
    ipv4 = (
        b"\x45\x00"
        + struct.pack("!H", ip_length)
        + b"\x00\x00\x00\x00\x40\x11\x00\x00"
        + bytes((10, 0, 0, source_octet))
        + bytes((10, 0, 1, source_octet))
    )
    udp = struct.pack("!HHHH", source_port, destination_port, udp_length, 0)
    data = ethernet + ipv4 + udp + payload
    return PcapFrame(
        timestamp_ns=timestamp_ns,
        data=data,
        original_length=len(data) + (8 if capture_truncated else 0),
        capture_truncated=capture_truncated,
    )


def _long_header(
    *,
    version: int = 1,
    destination_cid: bytes = b"abcd",
    source_cid: bytes = b"efgh",
    packet_type: int = 0,
    fixed_bit: int = 1,
    type_payload: bytes | None = None,
) -> bytes:
    first = 0x80 | (fixed_bit << 6) | (packet_type << 4)
    prefix = (
        bytes((first,))
        + version.to_bytes(4, "big")
        + bytes((len(destination_cid),))
        + destination_cid
        + bytes((len(source_cid),))
        + source_cid
    )
    if type_payload is not None:
        return prefix + type_payload
    if version != 1:
        return prefix
    if packet_type == 0:
        return prefix + b"\x00\x01\x00"
    if packet_type in {1, 2}:
        return prefix + b"\x01\x00"
    return prefix + b"\x00" * 16


def _short_header(
    destination_cid: bytes = b"abcd", *, fixed_bit: int = 1, spin_bit: int = 0
) -> bytes:
    return bytes(((fixed_bit << 6) | (spin_bit << 5),)) + destination_cid + b"payload"


def _base_packet(
    *,
    sample_id: str = "sample",
    packet_index: int = 0,
    relative_time_ns: int = 0,
    delta_time_us: int = 0,
    direction: int = 1,
    network_length_bytes: int = 100,
    payload_length_bytes: int | None = 50,
    transport_family: str = "UDP",
    tcp_flags: int | None = None,
    tcp_flags_applicable: bool = False,
    burst_id: int = 0,
    truncation_mask: bool = False,
) -> dict[str, object]:
    return {
        "sample_id": sample_id,
        "packet_index": packet_index,
        "relative_time_ns": relative_time_ns,
        "delta_time_us": delta_time_us,
        "direction": direction,
        "network_length_bytes": network_length_bytes,
        "payload_length_bytes": payload_length_bytes,
        "transport_family": transport_family,
        "tcp_flags": tcp_flags,
        "burst_id": burst_id,
        "is_first_packet": packet_index == 0,
        "payload_length_observed": payload_length_bytes is not None,
        "tcp_flags_applicable": tcp_flags_applicable,
        "truncation_mask": truncation_mask,
    }


def _packet(
    *,
    quic=None,
    **base_overrides: object,
) -> PacketObservation:
    base = _base_packet(**base_overrides)
    observation = quic if quic is not None else _quic_observation()
    return PacketObservation(
        **base,
        **observation.as_packet_fields(),
        quic_evidence_class=observation.evidence_class,
    )


def test_task01_contract_field_order_and_enums_are_reused() -> None:
    config = load_r2_config(CONFIG_PATH)
    assert BASE_PACKET_FIELDS == _GOLDEN_BASE_PACKET_FIELDS
    assert QUIC_PACKET_FIELDS == _GOLDEN_QUIC_PACKET_FIELDS
    assert PACKET_OBSERVATION_FIELDS == _GOLDEN_PACKET_FIELDS
    schema = _packet_schema(pa)
    assert tuple((field.name, str(field.type)) for field in schema) == _GOLDEN_PACKET_TYPES
    assert config.quic_parser_version == QUIC_PARSER_VERSION
    assert tuple(config.enum_values["transport_family"]) == (
        "TCP",
        "UDP",
        "ICMP",
        "SCTP",
        "DCCP",
        "ESP",
        "OTHER",
        "UNKNOWN",
    )
    assert tuple(config.enum_values["quic_evidence_class"]) == (
        "NONE",
        "V1_LONG_HEADER",
        "CONTEXT_BOUND_SHORT_HEADER",
        "AMBIGUOUS",
    )


@pytest.mark.parametrize("mutation", ["delete", "swap"])
def test_packet_field_order_gate_rejects_deleted_or_swapped_fields(
    mutation: str,
) -> None:
    fields = list(_GOLDEN_PACKET_FIELDS)
    if mutation == "delete":
        fields.pop(20)
    else:
        fields[20], fields[21] = fields[21], fields[20]
    with pytest.raises(TQHC2ProtocolError, match="39 列合同"):
        _validate_packet_field_order(fields)


def test_binding_gate_rejects_task01_enum_order_drift() -> None:
    config = load_r2_config(CONFIG_PATH)
    enum_values = dict(config.enum_values)
    enum_values["protocol_target"] = tuple(reversed(enum_values["protocol_target"]))
    drifted = replace(config, enum_values=enum_values)
    profile = TQHProfileBinding(
        profile="B",
        packet_observations_path=Path("unused.parquet"),
        expected_base_sequence_sha256={"sample": "0" * 64},
        pcap_sources=(),
    )
    with pytest.raises(TQHC2ProtocolError, match="枚举顺序不匹配"):
        _validate_bindings(TQHSourceBindings(config=drifted, profiles=(profile,)))


@pytest.mark.parametrize(
    ("packet_type", "expected"),
    [(0, "INITIAL"), (1, "0RTT"), (2, "HANDSHAKE"), (3, "RETRY")],
)
def test_parse_v1_long_header_packet_types(packet_type: int, expected: str) -> None:
    context = QuicConnectionContext()
    observation = parse_quic_wire_image(
        _udp_frame(_long_header(packet_type=packet_type)), context
    )
    assert observation.evidence_class == "V1_LONG_HEADER"
    assert observation.quic_version_u32 == 1
    assert observation.quic_v1_packet_type == expected
    assert observation.quic_dst_cid_length_bytes == 4
    assert observation.quic_src_cid_length_bytes == 4
    assert observation.quic_cid_changed is None
    assert observation.quic_cid_changed_observed is False


@pytest.mark.parametrize("version", [0, 0xFF00001D])
def test_version_negotiation_and_unknown_versions_are_ambiguous(version: int) -> None:
    observation = parse_quic_wire_image(
        _udp_frame(_long_header(version=version)), QuicConnectionContext()
    )
    assert observation.evidence_class == "AMBIGUOUS"
    assert observation.quic_version_u32 == version
    assert observation.quic_v1_packet_type is None
    assert observation.quic_cid_changed is None
    assert observation.quic_cid_changed_observed is False


def test_context_bound_short_header_reads_spin_bit() -> None:
    context = QuicConnectionContext()
    first = parse_quic_wire_image(_udp_frame(_long_header()), context)
    repeated = parse_quic_wire_image(
        _udp_frame(_long_header(), timestamp_ns=500), context
    )
    observation = parse_quic_wire_image(
        _udp_frame(_short_header(spin_bit=1), timestamp_ns=1_000), context
    )
    assert first.quic_cid_changed is None
    assert first.quic_cid_changed_observed is False
    assert repeated.quic_cid_changed is False
    assert repeated.quic_cid_changed_observed is True
    assert observation.evidence_class == "CONTEXT_BOUND_SHORT_HEADER"
    assert observation.quic_header_form == 0
    assert observation.quic_spin_bit == 1
    assert observation.quic_cid_changed is False


def test_short_header_without_context_is_not_a_hard_quic_label() -> None:
    observation = parse_quic_wire_image(
        _udp_frame(_short_header()), QuicConnectionContext()
    )
    assert observation.evidence_class == "NONE"
    assert observation.quic_header_form == 0
    assert observation.quic_fixed_bit == 1
    assert observation.quic_spin_bit is None


def test_truncated_empty_or_context_free_short_payload_is_ambiguous() -> None:
    empty = parse_quic_wire_image(
        _udp_frame(b"", capture_truncated=True), QuicConnectionContext()
    )
    short = parse_quic_wire_image(
        _udp_frame(_short_header(), capture_truncated=True),
        QuicConnectionContext(),
    )
    assert empty.evidence_class == "AMBIGUOUS"
    assert short.evidence_class == "AMBIGUOUS"
    assert short.quic_cid_changed is None
    assert short.quic_cid_changed_observed is False


def test_fixed_bit_zero_does_not_reject_v1_long_header() -> None:
    observation = parse_quic_wire_image(
        _udp_frame(_long_header(fixed_bit=0)), QuicConnectionContext()
    )
    assert observation.evidence_class == "V1_LONG_HEADER"
    assert observation.quic_fixed_bit == 0


@pytest.mark.parametrize("packet_type", [0, 1, 2, 3])
def test_truncated_long_header_is_ambiguous_and_does_not_bind(
    packet_type: int,
) -> None:
    context = QuicConnectionContext()
    observation = parse_quic_wire_image(
        _udp_frame(
            _long_header(packet_type=packet_type), capture_truncated=True
        ),
        context,
    )
    assert observation.evidence_class == "AMBIGUOUS"
    assert observation.quic_cid_changed is None
    assert observation.quic_cid_changed_observed is False
    following = parse_quic_wire_image(_udp_frame(_short_header()), context)
    assert following.evidence_class == "NONE"


@pytest.mark.parametrize(
    ("packet_type", "type_payload"),
    [
        (0, b""),
        (0, b"\x40"),
        (0, b"\x02x"),
        (0, b"\x00"),
        (0, b"\x00\x40"),
        (0, b"\x00\x02x"),
        (1, b""),
        (1, b"\x40"),
        (1, b"\x02x"),
        (2, b""),
        (2, b"\x40"),
        (2, b"\x02x"),
        (3, b"\x00" * 15),
    ],
)
def test_incomplete_v1_type_structure_is_ambiguous_and_never_binds(
    packet_type: int,
    type_payload: bytes,
) -> None:
    context = QuicConnectionContext()
    observation = parse_quic_wire_image(
        _udp_frame(
            _long_header(packet_type=packet_type, type_payload=type_payload)
        ),
        context,
    )
    assert observation.evidence_class == "AMBIGUOUS"
    assert observation.quic_cid_changed is None
    assert observation.quic_cid_changed_observed is False
    assert parse_quic_wire_image(
        _udp_frame(_short_header()), context
    ).evidence_class == "NONE"


def test_unknown_version_compares_cids_only_with_existing_context() -> None:
    context = QuicConnectionContext()
    first_unknown = parse_quic_wire_image(
        _udp_frame(_long_header(version=0xFF00001D)), context
    )
    parse_quic_wire_image(_udp_frame(_long_header()), context)
    same_unknown = parse_quic_wire_image(
        _udp_frame(_long_header(version=0xFF00001D)), context
    )
    changed_unknown = parse_quic_wire_image(
        _udp_frame(
            _long_header(
                version=0xFF00001D,
                destination_cid=b"wxyz",
                source_cid=b"ijkl",
            )
        ),
        context,
    )
    assert first_unknown.quic_cid_changed is None
    assert first_unknown.quic_cid_changed_observed is False
    assert same_unknown.quic_cid_changed is False
    assert same_unknown.quic_cid_changed_observed is True
    assert changed_unknown.quic_cid_changed is True
    assert changed_unknown.quic_cid_changed_observed is True


def test_connection_id_change_is_visible_without_serialising_raw_ids() -> None:
    context = QuicConnectionContext()
    first = parse_quic_wire_image(_udp_frame(_long_header()), context)
    changed = parse_quic_wire_image(
        _udp_frame(
            _long_header(destination_cid=b"wxyz", source_cid=b"ijkl"),
            timestamp_ns=1_000,
        ),
        context,
    )
    assert first.quic_cid_changed is None
    assert first.quic_cid_changed_observed is False
    assert changed.quic_cid_changed is True
    encoded = json.dumps(changed.as_packet_fields(), sort_keys=True)
    assert "wxyz" not in encoded
    assert "ijkl" not in encoded
    assert "abcd" not in repr(context)
    assert "efgh" not in repr(context)


@pytest.mark.parametrize(
    "changes",
    [
        {"packet_index": -1, "is_first_packet": False},
        {"direction": 0},
        {"network_length_bytes": -1},
        {"payload_length_bytes": None, "payload_length_observed": True},
        {
            "transport_family": "TCP",
            "tcp_flags": 0x200,
            "tcp_flags_applicable": True,
        },
        {"truncation_mask": 1},
        {"quic_parser_version": "unfrozen-parser"},
    ],
)
def test_packet_contract_rejects_invalid_base_or_mask_fields(
    changes: dict[str, object],
) -> None:
    packet = _packet()
    with pytest.raises(TQHC2ProtocolError):
        replace(packet, **changes)


def test_aggregate_recomputes_common_ratios_and_both_hashes() -> None:
    long = _quic_observation(
        evidence_class="V1_LONG_HEADER",
        quic_header_form=1,
        quic_header_form_observed=True,
        quic_header_form_applicable=True,
        quic_version_u32=1,
        quic_version_observed=True,
        quic_version_applicable=True,
        quic_v1_packet_type="INITIAL",
        quic_v1_packet_type_observed=True,
        quic_v1_packet_type_applicable=True,
        quic_fixed_bit=1,
        quic_fixed_bit_observed=True,
        quic_fixed_bit_applicable=True,
        quic_src_cid_length_bytes=4,
        quic_src_cid_length_observed=True,
        quic_src_cid_length_applicable=True,
        quic_dst_cid_length_bytes=4,
        quic_dst_cid_length_observed=True,
        quic_dst_cid_length_applicable=True,
        quic_cid_changed=False,
        quic_cid_changed_observed=True,
        quic_cid_changed_applicable=True,
    )
    rows = [
        _packet(quic=long, packet_index=0, relative_time_ns=0, delta_time_us=0),
        _packet(
            packet_index=1,
            relative_time_ns=1_500,
            delta_time_us=1,
            network_length_bytes=200,
            payload_length_bytes=100,
        ),
    ]
    aggregate = aggregate_packet_sequence(rows)
    assert aggregate.common == {
        "total_packets": 2.0,
        "total_bytes": 300.0,
        "packet_length_mean": 150.0,
        "packet_length_min": 100.0,
        "packet_length_max": 200.0,
        "iat_mean_ms": 0.0005,
        "packet_rate": pytest.approx(1_333_333.3333333333),
        "byte_rate": 200_000_000.0,
    }
    assert aggregate.fractions["udp_packet_fraction"] == 1.0
    assert aggregate.fractions["tcp_syn_packet_fraction"] is None
    assert aggregate.quic["quic_observed_packet_fraction"] == 0.5
    assert aggregate.quic["quic_v1_long_packet_fraction"] == 0.5
    assert aggregate.quic["quic_fixed_bit_one_fraction"] == 0.5
    assert aggregate.quic["quic_src_cid_length_mean"] == 4.0
    assert aggregate.base_observation_sequence_sha256 == _legacy_sequence_sha256(rows)
    assert aggregate.base_observation_sequence_sha256 != aggregate.observation_sequence_sha256


def _golden_hash_rows() -> list[PacketObservation]:
    return [
        _packet(
            sample_id="golden",
            network_length_bytes=64,
            payload_length_bytes=None,
            truncation_mask=True,
        ),
        _packet(
            sample_id="golden",
            packet_index=1,
            relative_time_ns=2_500,
            delta_time_us=2,
            direction=-1,
            network_length_bytes=128,
            payload_length_bytes=0,
            burst_id=1,
        ),
    ]


def test_legacy_and_new_sequence_hashes_match_independent_golden_vectors() -> None:
    rows = _golden_hash_rows()
    assert (
        _legacy_sequence_sha256(rows)
        == "71cec0cec723c79ef0113380cf093aebfb863fb76e0a128cf4d7587014edde05"
    )
    records = [row.as_record() for row in rows]
    assert (
        _observation_records_sha256(records)
        == "25443476ddf407757f5e84bb850f64a154a69706163e5f116f2997b6d67fb2b7"
    )
    assert (
        aggregate_packet_sequence(rows).observation_sequence_sha256
        == "25443476ddf407757f5e84bb850f64a154a69706163e5f116f2997b6d67fb2b7"
    )


@pytest.mark.parametrize(
    ("field_name", "changed_value"),
    [
        ("relative_time_ns", 1),
        ("delta_time_us", 1),
        ("direction", -1),
        ("network_length_bytes", 65),
        ("payload_length_bytes", 0),
        ("transport_family", "ICMP"),
        ("tcp_flags", 16),
        ("burst_id", 1),
        ("is_first_packet", False),
        ("payload_length_observed", True),
        ("tcp_flags_applicable", True),
        ("truncation_mask", False),
    ],
)
def test_each_legacy_hash_field_changes_the_digest(
    field_name: str,
    changed_value: object,
) -> None:
    values = {
        "relative_time_ns": 0,
        "delta_time_us": 0,
        "direction": 1,
        "network_length_bytes": 64,
        "payload_length_bytes": None,
        "transport_family": "UDP",
        "tcp_flags": None,
        "burst_id": 0,
        "is_first_packet": True,
        "payload_length_observed": False,
        "tcp_flags_applicable": False,
        "truncation_mask": True,
    }
    baseline = _legacy_sequence_sha256([SimpleNamespace(**values)])  # type: ignore[list-item]
    values[field_name] = changed_value
    changed = _legacy_sequence_sha256([SimpleNamespace(**values)])  # type: ignore[list-item]
    assert changed != baseline


def test_each_published_field_including_parser_version_changes_new_hash() -> None:
    records = [row.as_record() for row in _golden_hash_rows()]
    baseline = _observation_records_sha256(records)
    for field_name in _GOLDEN_PACKET_FIELDS:
        changed = [dict(row) for row in records]
        value = changed[0][field_name]
        if isinstance(value, bool):
            replacement: object = not value
        elif isinstance(value, int):
            replacement = value + 1
        elif isinstance(value, str):
            replacement = f"{value}-changed"
        else:
            replacement = "now-observed"
        changed[0][field_name] = replacement
        assert _observation_records_sha256(changed) != baseline, field_name


def test_cid_change_fraction_ignores_packets_without_comparison_basis() -> None:
    context = QuicConnectionContext()
    first = parse_quic_wire_image(_udp_frame(_long_header()), context)
    changed = parse_quic_wire_image(
        _udp_frame(
            _long_header(destination_cid=b"wxyz", source_cid=b"ijkl"),
            timestamp_ns=1_000,
        ),
        context,
    )
    missing = aggregate_packet_sequence([_packet(quic=first)])
    observed = aggregate_packet_sequence(
        [
            _packet(quic=first),
            _packet(
                quic=changed,
                packet_index=1,
                relative_time_ns=1_000,
                delta_time_us=1,
            ),
        ]
    )
    assert missing.quic["quic_cid_changed_packet_fraction"] is None
    assert missing.quic_missing["quic_cid_changed_packet_fraction"] == 1
    assert missing.quic_applicable["quic_cid_changed_packet_fraction"] == 0
    assert observed.quic["quic_cid_changed_packet_fraction"] == 1.0


def test_zero_duration_rates_are_missing_not_zero() -> None:
    aggregate = aggregate_packet_sequence([_packet()])
    assert aggregate.common["packet_rate"] is None
    assert aggregate.common["byte_rate"] is None
    assert aggregate.common_missing["packet_rate"] == 1
    assert aggregate.common_missing["byte_rate"] == 1


@pytest.mark.parametrize(
    "rows",
    [
        [_packet(), _packet(packet_index=2, relative_time_ns=1_000, delta_time_us=1)],
        [_packet(), _packet(packet_index=1, relative_time_ns=1_000, delta_time_us=2)],
        [_packet(), _packet(sample_id="other", packet_index=1, relative_time_ns=1_000, delta_time_us=1)],
        [
            _packet(),
            _packet(
                packet_index=1,
                relative_time_ns=1_000,
                delta_time_us=1,
                transport_family="TCP",
                tcp_flags=0x10,
                tcp_flags_applicable=True,
            ),
        ],
    ],
)
def test_aggregate_rejects_key_time_sample_or_transport_contract(
    rows: list[PacketObservation],
) -> None:
    with pytest.raises(TQHC2ProtocolError):
        aggregate_packet_sequence(rows)


def _write_pcap(path: Path, frames: list[PcapFrame]) -> None:
    payload = bytearray(b"\x4d\x3c\xb2\xa1")
    payload.extend(struct.pack("<HHIIII", 2, 4, 0, 0, 65_535, 1))
    for frame in frames:
        seconds, nanoseconds = divmod(frame.timestamp_ns, 1_000_000_000)
        payload.extend(
            struct.pack(
                "<IIII",
                seconds,
                nanoseconds,
                len(frame.data),
                frame.original_length,
            )
        )
        payload.extend(frame.data)
    path.write_bytes(bytes(payload))


class _CapturingSink:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = []
        self.closed = False

    def write(self, _bucket: int, rows: list[dict[str, object]]) -> None:
        self.rows.extend(rows)

    def close(self) -> None:
        self.closed = True


def _read_context_rows(
    tmp_path: Path,
    frames: list[PcapFrame],
    matches: list[PcapPacketMatch],
    selected_ids: frozenset[str],
) -> list[dict[str, object]]:
    pcap_path = tmp_path / "context-isolation.pcap"
    _write_pcap(pcap_path, frames)
    by_timestamp = {
        frame.timestamp_ns: match
        for frame, match in zip(frames, matches, strict=True)
    }

    def matcher(frame: PcapFrame, _packet) -> PcapPacketMatch | None:
        return by_timestamp.get(frame.timestamp_ns)

    profile = TQHProfileBinding(
        profile="B",
        packet_observations_path=tmp_path / "unused.parquet",
        expected_base_sequence_sha256={sample_id: "0" * 64 for sample_id in selected_ids},
        pcap_sources=(TQHPcapSource("context-capture", pcap_path, matcher),),
    )
    bindings = TQHSourceBindings(
        config=load_r2_config(CONFIG_PATH), profiles=(profile,)
    )
    sink = _CapturingSink()
    counts = _read_quic_buckets(
        bindings,
        {"B": selected_ids},
        sink,  # type: ignore[arg-type]
    )
    assert sink.closed
    assert counts["B"] == len(sink.rows)
    return sink.rows


def test_unselected_long_header_cannot_seed_selected_short_context(
    tmp_path: Path,
) -> None:
    selected = "selected"
    frames = [
        _udp_frame(_long_header(), timestamp_ns=1_000),
        _udp_frame(_short_header(), timestamp_ns=2_000),
    ]
    matches = [
        PcapPacketMatch("unselected", 0, 0, 0, 1, 0, True),
        PcapPacketMatch(selected, 0, 0, 0, 1, 0, True),
    ]
    rows = _read_context_rows(tmp_path, frames, matches, frozenset({selected}))
    assert len(rows) == 1
    assert rows[0]["quic_evidence_class"] == "NONE"
    assert rows[0]["quic_spin_bit"] is None


def test_selected_samples_with_same_four_tuple_keep_separate_contexts(
    tmp_path: Path,
) -> None:
    frames = [
        _udp_frame(_long_header(), timestamp_ns=1_000),
        _udp_frame(_short_header(), timestamp_ns=2_000),
    ]
    matches = [
        PcapPacketMatch("first", 0, 0, 0, 1, 0, True),
        PcapPacketMatch("second", 0, 0, 0, 1, 0, True),
    ]
    rows = _read_context_rows(
        tmp_path, frames, matches, frozenset({"first", "second"})
    )
    assert [row["quic_evidence_class"] for row in rows] == [
        "V1_LONG_HEADER",
        "NONE",
    ]


def test_quic_context_capacity_is_bounded_by_frozen_samples_and_fixed_limit() -> None:
    registry = _QuicContextRegistry(frozenset({"first", "second"}))
    assert registry.capacity == 2
    assert registry.for_sample("first") is registry.for_sample("first")
    registry.for_sample("second")
    assert registry.sample_count == registry.capacity
    with pytest.raises(TQHC2ProtocolError, match="未冻结样本"):
        registry.for_sample("third")

    context = QuicConnectionContext(max_directions=2)
    first = parse_ip_packet(_udp_frame(_long_header())).packet
    second = parse_ip_packet(
        _udp_frame(_long_header(), source_octet=2, source_port=20_000)
    ).packet
    assert first is not None and second is not None
    context.bind(first, b"abcd", b"efgh")
    with pytest.raises(TQHC2ProtocolError, match="方向容量"):
        context.bind(second, b"wxyz", b"ijkl")


def _base_from_frame(frame: PcapFrame, match: PcapPacketMatch) -> dict[str, object]:
    parsed = parse_ip_packet(frame)
    assert parsed.status == "parsed" and parsed.packet is not None
    packet = parsed.packet
    return {
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


def _write_interleaved_packet_table(
    path: Path, row_groups: list[list[dict[str, object]]]
) -> None:
    writer = pq.ParquetWriter(path, _base_packet_schema(pa), compression="zstd")
    try:
        for rows in row_groups:
            writer.write_table(pa.Table.from_pylist(rows, schema=_base_packet_schema(pa)))
    finally:
        writer.close()


def _independent_legacy_hash(rows: list[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    fields = _GOLDEN_BASE_PACKET_FIELDS[2:]
    for row in rows:
        digest.update(
            json.dumps(
                [row[name] for name in fields],
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("ascii")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _minimal_source_lock(
    config,
    artifact: SourceArtifactLock,
) -> SourceLock:
    inventory = GeNISArchiveInventory(
        logical_path="unused.zip",
        record_id="unused",
        version="unused",
        size_bytes=0,
        md5="0" * 32,
        sha256="0" * 64,
        scale_member_counts=(),
        materialization_members=(),
    )
    return SourceLock(
        schema_version="flow_probe_r2_source_lock_v1",
        dataset_version=config.dataset_version,
        stage=config.stage,
        status=config.status,
        config_sha256=config.config_sha256,
        code_commit=config.implementation_base_commit,
        frozen_inputs=(),
        tqhc2_artifacts=(artifact,),
        genis=inventory,
        candidate_source_counts=(),
    )


def _micro_binding(
    tmp_path: Path,
    *,
    expected_override: str | None = None,
    trusted_quic: bool = False,
) -> tuple[TQHSourceBindings, set[str], bytes, bytes]:
    config = load_r2_config(CONFIG_PATH)
    first_id = hashlib.sha256(b"first").hexdigest()
    second_id = hashlib.sha256(b"second").hexdigest()
    dcid_one, scid_one = b"abcd", b"efgh"
    dcid_two, scid_two = b"wxyz", b"ijkl"
    frames = [
        _udp_frame(
            _long_header(destination_cid=dcid_one, source_cid=scid_one),
            timestamp_ns=1_000,
            source_octet=1,
            source_port=10_001,
        ),
        _udp_frame(
            _long_header(destination_cid=dcid_two, source_cid=scid_two),
            timestamp_ns=2_000,
            source_octet=2,
            source_port=10_002,
        ),
        _udp_frame(
            _short_header(dcid_one, spin_bit=1),
            timestamp_ns=3_000,
            source_octet=1,
            source_port=10_001,
        ),
        _udp_frame(
            _short_header(dcid_two),
            timestamp_ns=4_000,
            source_octet=2,
            source_port=10_002,
        ),
    ]
    matches = [
        PcapPacketMatch(first_id, 0, 0, 0, 1, 0, True),
        PcapPacketMatch(second_id, 0, 0, 0, -1, 0, True),
        PcapPacketMatch(first_id, 1, 2_000, 2, 1, 0, False),
        PcapPacketMatch(second_id, 1, 2_000, 2, -1, 0, False),
    ]
    base_rows = [_base_from_frame(frame, match) for frame, match in zip(frames, matches, strict=True)]
    packet_path = tmp_path / "upstream-packets.parquet"
    _write_interleaved_packet_table(
        packet_path,
        [[base_rows[0], base_rows[1]], [base_rows[2], base_rows[3]]],
    )
    pcap_path = tmp_path / "capture.pcap"
    _write_pcap(pcap_path, frames)
    match_by_timestamp = {
        frame.timestamp_ns: match for frame, match in zip(frames, matches, strict=True)
    }

    def matcher(frame: PcapFrame, _packet) -> PcapPacketMatch | None:
        return match_by_timestamp.get(frame.timestamp_ns)

    expected: dict[str, str] = {}
    for sample_id in (first_id, second_id):
        sample_rows = sorted(
            (row for row in base_rows if row["sample_id"] == sample_id),
            key=lambda item: int(item["packet_index"]),
        )
        expected[sample_id] = _independent_legacy_hash(sample_rows)
    if expected_override is not None:
        expected[first_id] = expected_override
    trusted = {}
    source_lock = None
    truth_evidence: tuple[TQHProtocolTruthEvidence, ...] = ()
    if trusted_quic:
        logical_path = "truth/profile-b.json"
        evidence_path = tmp_path / "protocol-truth.json"
        evidence_payload = {
            "schema_version": "flow_probe_r2_tqhc2_protocol_truth_v1",
            "evidence_kind": "trusted_log",
            "input_fields": [
                "sample_id",
                "transport_family",
                "quic_version",
                "controlled_run_id",
                "event_type",
            ],
            "samples": [
                {"sample_id": sample_id, "protocol_target": "QUIC"}
                for sample_id in (first_id, second_id)
            ],
        }
        evidence_path.write_text(
            json.dumps(
                evidence_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )
        artifact = SourceArtifactLock(
            logical_path=logical_path,
            role="label_or_audit_source",
            sha256=hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
            size_bytes=evidence_path.stat().st_size,
            profile="B",
            evidence_status="verified",
        )
        source_lock = _minimal_source_lock(config, artifact)
        truth_evidence = (
            TQHProtocolTruthEvidence(logical_path=logical_path, path=evidence_path),
        )
        trusted = {
            sample_id: TrustedProtocolTarget(
                target="QUIC",
                evidence_logical_path=logical_path,
            )
            for sample_id in (first_id, second_id)
        }
    profile = TQHProfileBinding(
        profile="B",
        packet_observations_path=packet_path,
        expected_base_sequence_sha256=expected,
        pcap_sources=(TQHPcapSource("capture-b", pcap_path, matcher),),
        trusted_protocol_targets=trusted,
    )
    return (
        TQHSourceBindings(
            config=config,
            profiles=(profile,),
            source_lock=source_lock,
            protocol_truth_evidence=truth_evidence,
        ),
        {first_id, second_id},
        dcid_one,
        scid_one,
    )


def test_materialize_handles_interleaved_samples_and_nonadjacent_row_groups(
    tmp_path: Path,
) -> None:
    bindings, selected, dcid, scid = _micro_binding(tmp_path)
    result = materialize_tqhc2_sequences(bindings, selected, tmp_path / "stage")
    packets = pq.read_table(result.packet_observations_path)
    protocol = pq.read_table(result.protocol_path)
    source_map = pq.read_table(result.source_row_map_path)
    assert tuple(packets.column_names) == PACKET_OBSERVATION_FIELDS
    assert tuple(protocol.column_names) == PROTOCOL_STAGE_FIELDS
    assert tuple(source_map.column_names) == SOURCE_ROW_MAP_FIELDS
    keys = list(
        zip(
            packets["sample_id"].to_pylist(),
            packets["packet_index"].to_pylist(),
            strict=True,
        )
    )
    assert keys == sorted(keys)
    assert result.sample_count == 2
    assert result.packet_row_count == 4
    assert set(protocol["quic_evidence_class"].to_pylist()) == {"V1_LONG_HEADER"}
    assert set(protocol["protocol_target"].to_pylist()) == {"UNKNOWN"}
    assert (
        source_map["upstream_observation_sequence_sha256"].to_pylist()
        == source_map["base_observation_sequence_sha256"].to_pylist()
    )
    assert source_map["base_observation_sequence_sha256"].to_pylist() != source_map[
        "observation_sequence_sha256"
    ].to_pylist()
    audit = result.sequence_audit_path.read_text(encoding="utf-8")
    assert dcid.decode() not in audit
    assert scid.decode() not in audit
    assert not (tmp_path / "stage" / ".packet-buckets").exists()


def test_profile_b_never_creates_quic_target_without_trusted_truth(
    tmp_path: Path,
) -> None:
    bindings, selected, _dcid, _scid = _micro_binding(tmp_path)
    result = materialize_tqhc2_sequences(bindings, selected, tmp_path / "stage")
    targets = pq.read_table(result.protocol_path, columns=["protocol_target"])[
        "protocol_target"
    ].to_pylist()
    assert targets == ["UNKNOWN", "UNKNOWN"]


def test_controlled_or_logged_truth_may_bind_quic_target(tmp_path: Path) -> None:
    bindings, selected, _dcid, _scid = _micro_binding(tmp_path, trusted_quic=True)
    result = materialize_tqhc2_sequences(bindings, selected, tmp_path / "stage")
    targets = pq.read_table(result.protocol_path, columns=["protocol_target"])[
        "protocol_target"
    ].to_pylist()
    assert targets == ["QUIC", "QUIC"]
    assert bindings.source_lock is not None
    expected_digest = bindings.source_lock.tqhc2_artifacts[0].sha256
    evidence_digests = pq.read_table(
        result.source_row_map_path,
        columns=["protocol_target_evidence_sha256"],
    )["protocol_target_evidence_sha256"].to_pylist()
    assert evidence_digests == [expected_digest, expected_digest]


def _rewrite_truth_payload(
    bindings: TQHSourceBindings,
    payload: dict[str, object],
    *,
    relock: bool,
) -> TQHSourceBindings:
    evidence = bindings.protocol_truth_evidence[0]
    evidence.path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    if not relock:
        return bindings
    assert bindings.source_lock is not None
    artifact = bindings.source_lock.tqhc2_artifacts[0]
    updated_artifact = replace(
        artifact,
        sha256=hashlib.sha256(evidence.path.read_bytes()).hexdigest(),
        size_bytes=evidence.path.stat().st_size,
    )
    return replace(
        bindings,
        source_lock=replace(
            bindings.source_lock,
            tqhc2_artifacts=(updated_artifact,),
        ),
    )


def _read_truth_payload(bindings: TQHSourceBindings) -> dict[str, object]:
    return json.loads(
        bindings.protocol_truth_evidence[0].path.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("failure", ["arbitrary_digest", "missing_lock_item"])
def test_protocol_truth_rejects_unbound_or_arbitrary_source_lock(
    tmp_path: Path,
    failure: str,
) -> None:
    bindings, selected, _dcid, _scid = _micro_binding(tmp_path, trusted_quic=True)
    assert bindings.source_lock is not None
    if failure == "arbitrary_digest":
        artifact = replace(
            bindings.source_lock.tqhc2_artifacts[0], sha256="0" * 64
        )
        source_lock = replace(bindings.source_lock, tqhc2_artifacts=(artifact,))
    else:
        source_lock = replace(bindings.source_lock, tqhc2_artifacts=())
    with pytest.raises(TQHC2ProtocolError, match="源锁|摘要"):
        materialize_tqhc2_sequences(
            replace(bindings, source_lock=source_lock),
            selected,
            tmp_path / "stage",
        )


@pytest.mark.parametrize("forbidden_field", ["profile", "binary_label"])
def test_protocol_truth_rejects_profile_or_label_derived_inputs(
    tmp_path: Path,
    forbidden_field: str,
) -> None:
    bindings, selected, _dcid, _scid = _micro_binding(tmp_path, trusted_quic=True)
    payload = _read_truth_payload(bindings)
    input_fields = list(payload["input_fields"])
    input_fields.append(forbidden_field)
    payload["input_fields"] = input_fields
    bindings = _rewrite_truth_payload(bindings, payload, relock=True)
    with pytest.raises(TQHC2ProtocolError, match="显式允许清单"):
        materialize_tqhc2_sequences(bindings, selected, tmp_path / "stage")


@pytest.mark.parametrize("failure", ["tampered", "missing_sample", "target_mismatch", "kind"])
def test_protocol_truth_rejects_tampering_or_untrusted_mapping(
    tmp_path: Path,
    failure: str,
) -> None:
    bindings, selected, _dcid, _scid = _micro_binding(tmp_path, trusted_quic=True)
    payload = _read_truth_payload(bindings)
    if failure == "tampered":
        payload["evidence_kind"] = "controlled_configuration"
        bindings = _rewrite_truth_payload(bindings, payload, relock=False)
        pattern = "大小|摘要"
    elif failure == "missing_sample":
        payload["samples"] = list(payload["samples"])[1:]
        bindings = _rewrite_truth_payload(bindings, payload, relock=True)
        pattern = "未覆盖样本"
    elif failure == "target_mismatch":
        samples = list(payload["samples"])
        samples[0] = {**samples[0], "protocol_target": "TCP"}
        payload["samples"] = samples
        bindings = _rewrite_truth_payload(bindings, payload, relock=True)
        pattern = "映射冲突"
    else:
        payload["evidence_kind"] = "self_declared"
        bindings = _rewrite_truth_payload(bindings, payload, relock=True)
        pattern = "类型不受信任"
    with pytest.raises(TQHC2ProtocolError, match=pattern):
        materialize_tqhc2_sequences(bindings, selected, tmp_path / "stage")


def test_materialize_rejects_changed_upstream_base_sequence_hash(
    tmp_path: Path,
) -> None:
    bindings, selected, _dcid, _scid = _micro_binding(
        tmp_path, expected_override="0" * 64
    )
    with pytest.raises(TQHC2ProtocolError, match="旧基础序列哈希不匹配"):
        materialize_tqhc2_sequences(bindings, selected, tmp_path / "stage")
