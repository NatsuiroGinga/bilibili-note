"""探针实验配置及其边界校验。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace


class ConfigError(ValueError):
    """配置不满足实验协议。"""


@dataclass(frozen=True)
class ProbeConfig:
    """一次生成式探针运行所需的稳定配置。"""

    model_id: str
    feature_view: str
    seed: int
    max_input_length: int
    max_new_tokens: int
    lora_rank: int
    lora_alpha: int
    lora_dropout: float

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> ProbeConfig:
        """从映射创建配置，并拒绝会破坏公平比较的值。"""
        required = {field.name for field in cls.__dataclass_fields__.values()}
        missing = sorted(required.difference(data))
        if missing:
            raise ConfigError(f"缺少配置字段：{', '.join(missing)}")

        feature_view = str(data["feature_view"])
        if feature_view not in {
            "canonical_core_v1",
            "dataset_full_v1",
            "shared_b0_common_v1",
        }:
            raise ConfigError(f"未知字段视图：{feature_view!r}")

        model_id = str(data["model_id"]).strip()
        if not model_id:
            raise ConfigError("model_id 不能为空")

        integer_fields = ("seed", "max_input_length", "max_new_tokens", "lora_rank", "lora_alpha")
        integers: dict[str, int] = {}
        for field in integer_fields:
            value = data[field]
            if not isinstance(value, int) or isinstance(value, bool):
                raise ConfigError(f"{field} 必须是整数")
            if field != "seed" and value <= 0:
                raise ConfigError(f"{field} 必须大于 0")
            integers[field] = value

        dropout = data["lora_dropout"]
        if not isinstance(dropout, (int, float)) or isinstance(dropout, bool):
            raise ConfigError("lora_dropout 必须是数值")
        if not 0 <= float(dropout) < 1:
            raise ConfigError("lora_dropout 必须位于 [0, 1) 区间")

        return cls(
            model_id=model_id,
            feature_view=feature_view,
            seed=integers["seed"],
            max_input_length=integers["max_input_length"],
            max_new_tokens=integers["max_new_tokens"],
            lora_rank=integers["lora_rank"],
            lora_alpha=integers["lora_alpha"],
            lora_dropout=float(dropout),
        )


def override_model_id(config: ProbeConfig, model_id: str) -> ProbeConfig:
    """仅替换模型来源，保持实验参数不变。"""
    cleaned = model_id.strip()
    if not cleaned:
        raise ConfigError("model_id 不能为空")
    return replace(config, model_id=cleaned)
