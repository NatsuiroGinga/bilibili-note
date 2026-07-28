"""CICIoT2023 已核验社区镜像字段适配。"""

from __future__ import annotations

from collections.abc import Mapping

from flow_probe.adapters.base import (
    number,
    parse_binary_label,
    require_columns,
    sample_id,
    source_name,
)
from flow_probe.schemas import FlowSample

DATASET = "ciciot"
REQUIRED_COLUMNS = (
    "Number",
    "Tot sum",
    "Min",
    "Max",
    "AVG",
    "IAT",
    "Rate",
    "Label",
    "attack_class",
    "label",
)


def adapt_row(row: Mapping[str, object], source_file: str, row_number: int) -> FlowSample:
    """将社区镜像的一条 CICIoT 流记录转换为诊断样本。"""
    binary_label = parse_binary_label(DATASET, row.get("label"))
    require_columns(DATASET, row, REQUIRED_COLUMNS)

    source = source_name(source_file)
    mean_length = number(DATASET, row, "AVG")
    packet_rate = number(DATASET, row, "Rate")
    iat_seconds = number(DATASET, row, "IAT")
    byte_rate = None
    if mean_length is not None and packet_rate is not None:
        byte_rate = mean_length * packet_rate
    original_label = str(row["Label"]).strip() or binary_label
    attack_family = str(row["attack_class"]).strip() or binary_label
    features = {
        "total_packets": number(DATASET, row, "Number"),
        "total_bytes": number(DATASET, row, "Tot sum"),
        "packet_length_mean": mean_length,
        "packet_length_min": number(DATASET, row, "Min"),
        "packet_length_max": number(DATASET, row, "Max"),
        "iat_mean_ms": iat_seconds * 1000 if iat_seconds is not None else None,
        "packet_rate": packet_rate,
        "byte_rate": byte_rate,
    }
    return FlowSample(
        sample_id=sample_id(DATASET, source, row_number),
        source_dataset=DATASET,
        source_file=source,
        group_id=source,
        original_label=original_label,
        binary_label=binary_label,
        attack_family=attack_family,
        feature_view="canonical_core_v1",
        features=features,
    )
