"""跨数据集统一样本契约。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal, TypeAlias

BinaryLabel: TypeAlias = Literal["benign", "malicious"]
FeatureValue: TypeAlias = int | float | str | None

CANONICAL_CORE_FIELDS = (
    "total_packets",
    "total_bytes",
    "packet_length_mean",
    "packet_length_min",
    "packet_length_max",
    "iat_mean_ms",
    "packet_rate",
    "byte_rate",
)


class SchemaError(ValueError):
    """统一样本违反数据契约。"""


@dataclass(frozen=True)
class FlowSample:
    """一条可审计且不包含隐式标签映射的流记录。"""

    sample_id: str
    source_dataset: str
    source_file: str
    group_id: str
    original_label: str
    binary_label: BinaryLabel
    attack_family: str
    feature_view: str
    features: Mapping[str, FeatureValue]

    def __post_init__(self) -> None:
        for field in ("sample_id", "source_dataset", "source_file", "group_id", "original_label"):
            if not str(getattr(self, field)).strip():
                raise SchemaError(f"{field} 不能为空")

        if self.binary_label not in {"benign", "malicious"}:
            raise SchemaError(f"未知二分类标签：{self.binary_label!r}")
        if self.feature_view not in {"canonical_core_v1", "dataset_full_v1"}:
            raise SchemaError(f"未知字段视图：{self.feature_view!r}")

        features = dict(self.features)
        expected = set(CANONICAL_CORE_FIELDS)
        missing = sorted(expected.difference(features))
        unexpected = sorted(set(features).difference(expected))
        if missing:
            raise SchemaError(f"缺少核心字段：{', '.join(missing)}")
        if unexpected:
            raise SchemaError(f"未知核心字段：{', '.join(unexpected)}")
        object.__setattr__(self, "features", features)
