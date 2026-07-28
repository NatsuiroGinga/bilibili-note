"""将统一流样本转换为固定短提示词。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from flow_probe.schemas import CANONICAL_CORE_FIELDS, FeatureValue, FlowSample


def _format_value(value: FeatureValue) -> str:
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".6g")
    return value.strip().lower()


def serialize_feature_mapping(features: Mapping[str, FeatureValue]) -> str:
    """按统一字段顺序序列化数值特征，不携带来源或标签元数据。"""
    missing = [field for field in CANONICAL_CORE_FIELDS if field not in features]
    if missing:
        raise ValueError(f"缺少统一流量字段：{', '.join(missing)}")
    return ";".join(f"{field}={_format_value(features[field])}" for field in CANONICAL_CORE_FIELDS)


def serialize_label_task(
    features: Mapping[str, FeatureValue],
    *,
    instruction: str,
    allowed_labels: Sequence[str],
) -> str:
    """为指定标签空间构造严格 JSON 输出提示词。"""
    if not instruction.strip():
        raise ValueError("任务说明不能为空")
    labels = [str(label).strip() for label in allowed_labels]
    if not labels or any(not label for label in labels) or len(set(labels)) != len(labels):
        raise ValueError("候选标签必须非空且不能重复")
    fields = serialize_feature_mapping(features)
    return (
        f"任务：{instruction.strip()}\n"
        f"流量：{fields}\n"
        f"只输出 JSON，label 必须为以下之一：{'、'.join(labels)}"
    )


def serialize_flow(sample: FlowSample) -> str:
    """按版本化字段顺序构造不含来源和标签元数据的输入。"""
    fields = serialize_feature_mapping(sample.features)
    return (
        "任务：判断以下网络流是良性还是恶意。\n"
        f"流量：{fields}\n"
        '只输出 JSON：{"label":"benign"} 或 {"label":"malicious"}'
    )
