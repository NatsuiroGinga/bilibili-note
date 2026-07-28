"""GeNIS-2025 官方 Argus 流字段适配。"""

from __future__ import annotations

from collections.abc import Mapping

from flow_probe.adapters.base import (
    max_if_present,
    min_if_present,
    number,
    parse_binary_label,
    require_columns,
    sample_id,
    source_name,
)
from flow_probe.schemas import FlowSample

DATASET = "genis"
REQUIRED_COLUMNS = (
    "BinaryLabel",
    "CategoryLabel",
    "SubCategoryLabel",
    "TotPkts",
    "SrcPkts",
    "DstPkts",
    "TotBytes",
    "sMinPktSz",
    "dMinPktSz",
    "sMaxPktSz",
    "dMaxPktSz",
    "SIntPkt",
    "DIntPkt",
    "Rate",
    "Load",
)


def _weighted_iat(
    src_packets: float | None,
    dst_packets: float | None,
    src_iat: float | None,
    dst_iat: float | None,
) -> float | None:
    weighted: list[tuple[float, float]] = []
    if src_packets is not None and src_iat is not None and src_packets > 1:
        weighted.append((src_iat, src_packets - 1))
    if dst_packets is not None and dst_iat is not None and dst_packets > 1:
        weighted.append((dst_iat, dst_packets - 1))
    weight = sum(item[1] for item in weighted)
    if not weight:
        return None
    return sum(value * item_weight for value, item_weight in weighted) / weight


def adapt_row(row: Mapping[str, object], source_file: str, row_number: int) -> FlowSample:
    """将一条 GeNIS 官方流记录转换为共有字段样本。"""
    binary_label = parse_binary_label(DATASET, row.get("BinaryLabel"))
    require_columns(DATASET, row, REQUIRED_COLUMNS)

    total_packets = number(DATASET, row, "TotPkts")
    src_packets = number(DATASET, row, "SrcPkts")
    dst_packets = number(DATASET, row, "DstPkts")
    total_bytes = number(DATASET, row, "TotBytes")
    mean_length = None
    if total_packets not in {None, 0} and total_bytes is not None:
        mean_length = total_bytes / total_packets

    source = source_name(source_file)
    category = str(row["CategoryLabel"]).strip() or binary_label
    original_label = str(row["SubCategoryLabel"]).strip() or category
    load_bits = number(DATASET, row, "Load")
    features = {
        "total_packets": total_packets,
        "total_bytes": total_bytes,
        "packet_length_mean": mean_length,
        "packet_length_min": min_if_present(
            number(DATASET, row, "sMinPktSz"), number(DATASET, row, "dMinPktSz")
        ),
        "packet_length_max": max_if_present(
            number(DATASET, row, "sMaxPktSz"), number(DATASET, row, "dMaxPktSz")
        ),
        "iat_mean_ms": _weighted_iat(
            src_packets,
            dst_packets,
            number(DATASET, row, "SIntPkt"),
            number(DATASET, row, "DIntPkt"),
        ),
        "packet_rate": number(DATASET, row, "Rate"),
        "byte_rate": load_bits / 8 if load_bits is not None else None,
    }
    return FlowSample(
        sample_id=sample_id(DATASET, source, row_number),
        source_dataset=DATASET,
        source_file=source,
        group_id=source,
        original_label=original_label,
        binary_label=binary_label,
        attack_family=category,
        feature_view="canonical_core_v1",
        features=features,
    )
