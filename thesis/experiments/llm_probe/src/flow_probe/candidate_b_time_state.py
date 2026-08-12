"""候选 B 角色分离物理时间 RWKV 的五变体共同状态核。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

import torch
from torch import nn
from torch.nn import functional as F


VARIANTS = (
    "B-DISCRETE-RWKV",
    "B-DELTA-FEATURE",
    "B-DYG-SPAN",
    "B-LINEAR-CLIPPED",
    "B-ROLE-SEPARATED",
)

DISPLAY_NAMES = {
    "B-DISCRETE-RWKV": "离散步长 RWKV 状态对照",
    "B-DELTA-FEATURE": "显式流间隔普通特征对照",
    "B-DYG-SPAN": "DyG-Mamba 式单调跨度控制对照",
    "B-LINEAR-CLIPPED": "线性裁剪时间衰减对照",
    "B-ROLE-SEPARATED": "角色分离物理时间 RWKV",
}

TIME_CONTROL_VARIANTS = (
    "B-DELTA-FEATURE",
    "B-DYG-SPAN",
    "B-LINEAR-CLIPPED",
    "B-ROLE-SEPARATED",
)


class CandidateBStateError(ValueError):
    """状态核输入或冻结合同不合法。"""


@dataclass(frozen=True)
class TimeTransform:
    """只由源训练区拟合的精确时间变换。"""

    unit: str
    clip_delta_t_us: int
    median_delta_t_us: int
    log1p_mean: float
    log1p_std: float
    quartile_delta_t_us: tuple[int, int, int]
    quartile_sequence_span_us: tuple[int, int, int]

    def validate(self) -> None:
        if self.unit != "microseconds" or self.clip_delta_t_us <= 0:
            raise CandidateBStateError("时间单位或源域裁剪上限不合法")
        if self.median_delta_t_us < 0 or self.log1p_std <= 0.0:
            raise CandidateBStateError("源域时间中位数或标准差不合法")
        if tuple(sorted(self.quartile_delta_t_us)) != self.quartile_delta_t_us:
            raise CandidateBStateError("源域时间四分位边界必须单调")
        if tuple(sorted(self.quartile_sequence_span_us)) != self.quartile_sequence_span_us:
            raise CandidateBStateError("源域序列跨度四分位边界必须单调")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "TimeTransform":
        quartiles = value.get("quartile_delta_t_us")
        if not isinstance(quartiles, (list, tuple)) or len(quartiles) != 3:
            raise CandidateBStateError("时间四分位边界必须恰有三个值")
        span_quartiles = value.get("quartile_sequence_span_us")
        if not isinstance(span_quartiles, (list, tuple)) or len(span_quartiles) != 3:
            raise CandidateBStateError("序列跨度四分位边界必须恰有三个值")
        result = cls(
            unit=str(value.get("unit")),
            clip_delta_t_us=int(value.get("clip_delta_t_us", -1)),
            median_delta_t_us=int(value.get("median_delta_t_us", -1)),
            log1p_mean=float(value.get("log1p_mean", float("nan"))),
            log1p_std=float(value.get("log1p_std", float("nan"))),
            quartile_delta_t_us=tuple(int(item) for item in quartiles),
            quartile_sequence_span_us=tuple(int(item) for item in span_quartiles),
        )
        result.validate()
        return result


@dataclass(frozen=True)
class CandidateBModelConfig:
    input_size: int = 192
    hidden_size: int = 192
    state_heads: int = 6
    state_head_size: int = 32
    minimum_retention: float = 1.0e-4

    def validate(self) -> None:
        if self.input_size != 192 or self.hidden_size != 192:
            raise CandidateBStateError("候选 B 冻结表示与隐藏维必须均为 192")
        if self.state_heads * self.state_head_size != self.hidden_size:
            raise CandidateBStateError("头数乘状态维必须等于隐藏维")
        if not 0.0 < self.minimum_retention < 1.0:
            raise CandidateBStateError("最小保留率必须位于 (0,1)")


@dataclass
class StateDiagnostics:
    state_norm_sum: torch.Tensor
    retention_sum: torch.Tensor
    valid_count: torch.Tensor
    exact_time_used: bool

    def means(self) -> tuple[torch.Tensor, torch.Tensor]:
        denominator = self.valid_count.clamp_min(1.0)
        return self.state_norm_sum / denominator, self.retention_sum / denominator


class ConstantParameterCompensation(nn.Module):
    """不读取样本输入，但让精确补偿参数参与优化并改变分类上下文。"""

    def __init__(self, hidden_size: int, parameter_count: int) -> None:
        super().__init__()
        if parameter_count < 0:
            raise CandidateBStateError("补偿参数数目不得为负")
        self.hidden_size = hidden_size
        self.values = nn.Parameter(torch.zeros(parameter_count)) if parameter_count else None

    def forward(self, reference: torch.Tensor) -> torch.Tensor:
        if self.values is None:
            return reference.new_zeros(reference.shape)
        indices = torch.arange(self.values.numel(), device=self.values.device) % self.hidden_size
        bias = self.values.new_zeros(self.hidden_size).scatter_add(0, indices, self.values)
        counts = torch.bincount(indices, minlength=self.hidden_size).clamp_min(1)
        bias = torch.tanh(bias / counts.to(bias.dtype)).to(reference.dtype)
        return bias.view(1, 1, -1).expand(reference.shape[0], reference.shape[1], -1)


class PhysicalTimeStateKernel(nn.Module):
    """逐位置预测更新前状态，并按变体更新完整矩阵状态。"""

    def __init__(
        self,
        variant: str,
        config: CandidateBModelConfig,
        time_transform: TimeTransform,
    ) -> None:
        super().__init__()
        if variant not in VARIANTS:
            raise CandidateBStateError(f"未知候选 B 变体：{variant}")
        config.validate()
        time_transform.validate()
        self.variant = variant
        self.config = config
        self.time_transform = time_transform
        hidden = config.hidden_size
        self.content = nn.Linear(config.input_size, hidden, bias=False)
        self.receptance = nn.Linear(hidden, hidden, bias=False)
        self.key = nn.Linear(hidden, hidden, bias=False)
        self.value = nn.Linear(hidden, hidden, bias=False)
        self.content_decay = (
            nn.Linear(hidden, hidden, bias=False)
            if variant in {"B-DISCRETE-RWKV", "B-DELTA-FEATURE"}
            else None
        )
        self.learning_rate = nn.Linear(hidden, hidden, bias=False)
        self.gate = nn.Linear(hidden, hidden, bias=False)
        self.output = nn.Linear(hidden, hidden, bias=False)
        self.removal_scale = nn.Parameter(torch.ones(config.state_heads, config.state_head_size))
        self.replacement_rate = nn.Parameter(
            torch.full((config.state_heads, config.state_head_size), 0.5)
        )
        self.bonus_scale = nn.Parameter(torch.zeros(config.state_heads, config.state_head_size))
        self.head_norm = nn.LayerNorm(config.state_head_size)
        self.time_feature_projection = (
            nn.Linear(1, hidden, bias=False) if variant == "B-DELTA-FEATURE" else None
        )
        self.span_rate = (
            nn.Parameter(torch.zeros(config.state_heads)) if variant == "B-DYG-SPAN" else None
        )
        self.physical_rate = (
            nn.Parameter(torch.zeros(config.state_heads, config.state_head_size))
            if variant == "B-ROLE-SEPARATED"
            else None
        )

    def _shape(self, value: torch.Tensor) -> torch.Tensor:
        return value.float().view(
            value.shape[0], self.config.state_heads, self.config.state_head_size
        )

    def _time_values(self, delta_t_us: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        clipped = delta_t_us.float().clamp(0.0, float(self.time_transform.clip_delta_t_us))
        seconds = clipped / 1_000_000.0
        log_value = torch.log1p(seconds)
        standardized = (log_value - self.time_transform.log1p_mean) / self.time_transform.log1p_std
        return seconds, standardized

    def _retention(self, content: torch.Tensor, seconds: torch.Tensor) -> torch.Tensor:
        minimum = self.config.minimum_retention
        if self.variant in {"B-DISCRETE-RWKV", "B-DELTA-FEATURE"}:
            assert self.content_decay is not None
            return torch.exp(
                -torch.exp(content.new_tensor(-0.5))
                * torch.sigmoid(self._shape(self.content_decay(content)))
            )
        if self.variant == "B-DYG-SPAN":
            assert self.span_rate is not None
            rate = F.softplus(self.span_rate.float()).view(1, self.config.state_heads, 1)
            return torch.exp(-rate * seconds.view(-1, 1, 1)).clamp_min(minimum)
        if self.variant == "B-LINEAR-CLIPPED":
            scaled = seconds / max(self.time_transform.clip_delta_t_us / 1_000_000.0, 1e-12)
            return (
                (1.0 - scaled.view(-1, 1, 1))
                .clamp(minimum, 1.0)
                .expand(-1, self.config.state_heads, self.config.state_head_size)
            )
        assert self.physical_rate is not None
        rate = F.softplus(self.physical_rate.float()).unsqueeze(0)
        return torch.exp(-rate * seconds.view(-1, 1, 1)).clamp_min(minimum)

    def forward(
        self,
        phi: torch.Tensor,
        delta_t_us: torch.Tensor,
        valid_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, StateDiagnostics]:
        if phi.ndim != 3 or phi.shape[:2] != valid_mask.shape:
            raise CandidateBStateError("冻结表示与有效位形状不一致")
        if delta_t_us.shape != valid_mask.shape or delta_t_us.dtype not in {
            torch.int32,
            torch.int64,
            torch.float32,
            torch.float64,
        }:
            raise CandidateBStateError("精确 delta_t_us 形状或类型不合法")
        state = torch.zeros(
            phi.shape[0],
            self.config.state_heads,
            self.config.state_head_size,
            self.config.state_head_size,
            device=phi.device,
            dtype=torch.float32,
        )
        contexts: list[torch.Tensor] = []
        norm_sum = phi.new_zeros((), dtype=torch.float32)
        retention_sum = phi.new_zeros((), dtype=torch.float32)
        valid_count = phi.new_zeros((), dtype=torch.float32)
        for index in range(phi.shape[1]):
            raw = phi[:, index]
            seconds, standardized = self._time_values(delta_t_us[:, index])
            content = self.content(raw)
            if self.time_feature_projection is not None:
                content = content + self.time_feature_projection(
                    standardized[:, None].to(raw.dtype)
                )
            receptance = self._shape(self.receptance(content))
            key = self._shape(self.key(content))
            value = self._shape(self.value(content))
            removal = F.normalize(key * self.removal_scale, dim=-1, eps=1e-12)
            rate = torch.sigmoid(self._shape(self.learning_rate(content)))
            replacement = key * (1.0 - self.replacement_rate + rate * self.replacement_rate)
            retention = self._retention(content, seconds)
            readout = torch.einsum("bhij,bhj->bhi", state, receptance)
            bonus = (receptance * key * self.bonus_scale).sum(dim=-1, keepdim=True) * value
            normalized = self.head_norm(readout + bonus)
            gated = torch.sigmoid(self._shape(self.gate(content))) * normalized
            contexts.append(self.output(gated.flatten(1).to(raw.dtype)))
            retained = state * retention.unsqueeze(-2)
            removed_value = torch.einsum("bhij,bhj->bhi", retained, removal)
            proposal = (
                retained
                - torch.einsum("bhi,bhj->bhij", removed_value, removal * rate)
                + torch.einsum("bhi,bhj->bhij", value, replacement)
            )
            active = valid_mask[:, index].view(-1, 1, 1, 1)
            state = torch.where(active, proposal, state)
            active_rows = valid_mask[:, index]
            if torch.any(active_rows):
                norm_sum = (
                    norm_sum
                    + torch.linalg.matrix_norm(state[active_rows], ord="fro", dim=(-2, -1))
                    .mean(dim=-1)
                    .sum()
                )
                retention_sum = retention_sum + retention[active_rows].mean(dim=(-2, -1)).sum()
                valid_count = valid_count + active_rows.sum()
        return torch.stack(contexts, dim=1), StateDiagnostics(
            state_norm_sum=norm_sum,
            retention_sum=retention_sum,
            valid_count=valid_count,
            exact_time_used=self.variant != "B-DISCRETE-RWKV",
        )


class CandidateBTimeModel(nn.Module):
    """五变体共享分类结构，只替换状态时间作用。"""

    def __init__(
        self,
        variant: str,
        config: CandidateBModelConfig,
        time_transform: TimeTransform,
        compensation_parameters: int = 0,
    ) -> None:
        super().__init__()
        self.variant = variant
        self.state = PhysicalTimeStateKernel(variant, config, time_transform)
        self.compensation = ConstantParameterCompensation(
            config.hidden_size, compensation_parameters
        )
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size * 2),
            nn.Linear(config.hidden_size * 2, config.hidden_size),
            nn.GELU(),
            nn.Linear(config.hidden_size, 1),
        )

    def forward(
        self,
        phi: torch.Tensor,
        delta_t_us: torch.Tensor,
        valid_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, StateDiagnostics]:
        context, diagnostics = self.state(phi, delta_t_us, valid_mask)
        context = context + self.compensation(context)
        logits = self.classifier(torch.cat((phi, context), dim=-1)).squeeze(-1)
        return logits, diagnostics


def trainable_parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def build_parameter_matched_models(
    config: CandidateBModelConfig,
    time_transform: TimeTransform,
    initialization_seed: int = 42,
) -> tuple[dict[str, CandidateBTimeModel], dict[str, int], dict[str, int]]:
    """以五个原始模型最大参数量为目标进行精确主动补偿。"""
    raw_counts: dict[str, int] = {}
    for variant in VARIANTS:
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(initialization_seed)
            raw_counts[variant] = trainable_parameter_count(
                CandidateBTimeModel(variant, config, time_transform)
            )
    target = max(raw_counts.values())
    models: dict[str, CandidateBTimeModel] = {}
    for variant in VARIANTS:
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(initialization_seed)
            models[variant] = CandidateBTimeModel(
                variant,
                config,
                time_transform,
                compensation_parameters=target - raw_counts[variant],
            )
    matched = {variant: trainable_parameter_count(model) for variant, model in models.items()}
    if set(matched.values()) != {target}:
        raise CandidateBStateError(f"五变体可训练参数量未精确一致：{matched}")
    return models, raw_counts, matched
