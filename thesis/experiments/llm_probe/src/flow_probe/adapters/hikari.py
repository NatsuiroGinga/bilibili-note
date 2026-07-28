"""HIKARI-2021 已发表流字段适配。"""

from __future__ import annotations

from collections.abc import Mapping

from flow_probe.adapters.base import (
    add_if_complete,
    number,
    parse_binary_label,
    require_columns,
    sample_id,
    source_name,
)
from flow_probe.schemas import FlowSample

DATASET = "hikari"
REQUIRED_COLUMNS = (
    "uid",
    "originh",
    "responh",
    "fwd_pkts_tot",
    "bwd_pkts_tot",
    "fwd_pkts_payload.tot",
    "bwd_pkts_payload.tot",
    "flow_pkts_payload.min",
    "flow_pkts_payload.max",
    "flow_pkts_payload.avg",
    "flow_iat.avg",
    "flow_pkts_per_sec",
    "payload_bytes_per_second",
    "traffic_category",
    "Label",
)


def adapt_row(row: Mapping[str, object], source_file: str, row_number: int) -> FlowSample:
    """将一条 HIKARI 流记录转换为共有字段样本。"""
    binary_label = parse_binary_label(DATASET, row.get("Label"))
    require_columns(DATASET, row, REQUIRED_COLUMNS)

    source = source_name(source_file)
    origin = str(row["originh"]).strip()
    response = str(row["responh"]).strip()
    category = str(row["traffic_category"]).strip() or binary_label
    iat_microseconds = number(DATASET, row, "flow_iat.avg")
    features = {
        "total_packets": add_if_complete(
            number(DATASET, row, "fwd_pkts_tot"), number(DATASET, row, "bwd_pkts_tot")
        ),
        "total_bytes": add_if_complete(
            number(DATASET, row, "fwd_pkts_payload.tot"),
            number(DATASET, row, "bwd_pkts_payload.tot"),
        ),
        "packet_length_mean": number(DATASET, row, "flow_pkts_payload.avg"),
        "packet_length_min": number(DATASET, row, "flow_pkts_payload.min"),
        "packet_length_max": number(DATASET, row, "flow_pkts_payload.max"),
        "iat_mean_ms": iat_microseconds / 1000 if iat_microseconds is not None else None,
        "packet_rate": number(DATASET, row, "flow_pkts_per_sec"),
        "byte_rate": number(DATASET, row, "payload_bytes_per_second"),
    }
    return FlowSample(
        sample_id=sample_id(DATASET, source, row_number),
        source_dataset=DATASET,
        source_file=source,
        group_id=f"{source}:{origin}->{response}",
        original_label=category,
        binary_label=binary_label,
        attack_family=category,
        feature_view="canonical_core_v1",
        features=features,
    )
