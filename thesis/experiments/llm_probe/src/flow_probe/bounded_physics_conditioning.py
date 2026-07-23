"""有界物理条件注入的纯数学组件。"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

import torch
from torch.utils.hooks import RemovableHandle

__all__ = [
    "BoundedPhysicsCrossAttention",
    "ConditioningDiagnostics",
    "ConditioningSpec",
    "PhysicalConditionEncoder",
    "PhysicsConditionedGeneration",
    "PhysicsConditionedOutput",
    "PhysicsConditionedRuntime",
    "build_candidate_injection_mask",
    "build_condition_state",
    "build_training_injection_mask",
    "resolve_conditioning_layers",
]


@dataclass(frozen=True)
class ConditioningSpec:
    """Qwen3-1.7B 有界物理条件注入的固定结构契约。"""

    num_hidden_layers: int = 28
    hidden_size: int = 2048
    source_layer: int = 13
    target_layers: tuple[int, int, int, int] = (24, 25, 26, 27)
    state_size: int = 5
    condition_tokens: int = 9
    bottleneck_size: int = 256
    attention_heads: int = 4
    residual_ratio_cap: float = 0.1
    norm_epsilon: float = 1e-6
    gate_init: float = 0.0

    def __post_init__(self) -> None:
        integer_values = (
            ("num_hidden_layers", self.num_hidden_layers, 28),
            ("hidden_size", self.hidden_size, 2048),
            ("source_layer", self.source_layer, 13),
            ("state_size", self.state_size, 5),
            ("condition_tokens", self.condition_tokens, 9),
            ("bottleneck_size", self.bottleneck_size, 256),
            ("attention_heads", self.attention_heads, 4),
        )
        for name, value, expected in integer_values:
            if type(value) is not int or value != expected:
                raise ValueError(f"{name} 必须固定为 {expected}")

        if type(self.target_layers) is not tuple or self.target_layers != (24, 25, 26, 27):
            raise ValueError("target_layers 必须固定为 (24, 25, 26, 27)")
        if any(type(layer) is not int for layer in self.target_layers):
            raise ValueError("target_layers 中的层索引必须为整数")

        float_values = (
            ("residual_ratio_cap", self.residual_ratio_cap, 0.1),
            ("norm_epsilon", self.norm_epsilon, 1e-6),
            ("gate_init", self.gate_init, 0.0),
        )
        for name, value, expected in float_values:
            if type(value) is not float or not math.isfinite(value) or value != expected:
                raise ValueError(f"{name} 必须固定为有限值 {expected}")

        if self.hidden_size % self.attention_heads != 0:
            raise ValueError("hidden_size 必须能被 attention_heads 整除")
        if self.hidden_size % self.bottleneck_size != 0:
            raise ValueError("hidden_size 必须能被 bottleneck_size 整除")
        if self.bottleneck_size % self.attention_heads != 0:
            raise ValueError("bottleneck_size 必须能被 attention_heads 整除")
        if self.condition_tokens != self.state_size + self.state_size - 1:
            raise ValueError("condition_tokens 必须等于状态数与相邻差分数之和")

        all_layers = (self.source_layer, *self.target_layers)
        if any(layer < 0 or layer >= self.num_hidden_layers for layer in all_layers):
            raise ValueError("源层和目标层索引必须位于模型层范围内")
        if len(set(self.target_layers)) != len(self.target_layers):
            raise ValueError("目标层索引不得重复")
        if self.source_layer in self.target_layers:
            raise ValueError("源层不得同时作为目标层")
        if any(layer <= self.source_layer for layer in self.target_layers):
            raise ValueError("每个目标层必须位于源层之后")


def resolve_conditioning_layers(num_hidden_layers: int) -> tuple[int, tuple[int, int, int, int]]:
    """解析固定 Qwen3-1.7B 层位置，拒绝其他模型深度。"""

    if type(num_hidden_layers) is not int or num_hidden_layers != 28:
        raise ValueError("num_hidden_layers 必须固定为 28")
    return 13, (24, 25, 26, 27)


@dataclass(frozen=True)
class ConditioningDiagnostics:
    """一次有界条件注入运行的四层诊断快照。"""

    gate_values: tuple[float, float, float, float]
    attention_entropies: tuple[float, float, float, float]
    max_residual_ratio: float
    source_hook_count: int
    target_hook_counts: tuple[int, int, int, int]
    prefill_count: int
    cached_decode_count: int

    def __post_init__(self) -> None:
        for name, values in (
            ("gate_values", self.gate_values),
            ("attention_entropies", self.attention_entropies),
        ):
            if type(values) is not tuple or len(values) != 4:
                raise ValueError(f"{name} 必须是固定长度为 4 的元组")
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in values
            ):
                raise ValueError(f"{name} 必须只包含有限数值")

        if (
            isinstance(self.max_residual_ratio, bool)
            or not isinstance(self.max_residual_ratio, (int, float))
            or not math.isfinite(float(self.max_residual_ratio))
            or self.max_residual_ratio < 0
        ):
            raise ValueError("max_residual_ratio 必须是非负有限数值")
        if type(self.target_hook_counts) is not tuple or len(self.target_hook_counts) != 4:
            raise ValueError("target_hook_counts 必须是固定长度为 4 的元组")
        counts = (
            self.source_hook_count,
            *self.target_hook_counts,
            self.prefill_count,
            self.cached_decode_count,
        )
        if any(type(count) is not int or count < 0 for count in counts):
            raise ValueError("所有挂钩与解码次数必须是非负整数")


class PhysicalConditionEncoder(torch.nn.Module):
    """把五个非负状态及其四个有符号差分编码为九个条件令牌。"""

    def __init__(self, spec: ConditioningSpec | None = None) -> None:
        super().__init__()
        self.spec = ConditioningSpec() if spec is None else spec
        if not isinstance(self.spec, ConditioningSpec):
            raise ValueError("spec 必须是 ConditioningSpec")

        embedding_size = self.spec.bottleneck_size
        self.type_embedding = torch.nn.Embedding(2, embedding_size)
        self.position_embedding = torch.nn.Embedding(self.spec.condition_tokens, embedding_size)
        self.encoder = torch.nn.Sequential(
            torch.nn.Linear(1 + 2 * embedding_size, self.spec.bottleneck_size),
            torch.nn.SiLU(),
            torch.nn.Linear(self.spec.bottleneck_size, self.spec.bottleneck_size),
        )

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        if (
            not isinstance(state, torch.Tensor)
            or state.ndim != 2
            or state.shape[1] != self.spec.state_size
        ):
            raise ValueError("state 必须是形状为 [B,5] 的张量")
        if state.dtype == torch.bool or torch.is_complex(state):
            raise ValueError("state 必须是实数张量")
        if not bool(torch.isfinite(state).all().item()):
            raise ValueError("state 必须只包含有限数值")
        if bool((state < 0).any().item()):
            raise ValueError("state 不得包含负值")

        first_weight = self.encoder[0].weight
        if state.device != first_weight.device:
            raise ValueError("state 与条件编码器必须位于同一设备")
        aligned_state = state.to(dtype=first_weight.dtype)
        differences = aligned_state[:, 1:] - aligned_state[:, :-1]
        scalar_tokens = torch.cat((aligned_state, differences), dim=1).unsqueeze(-1)
        if not bool(torch.isfinite(scalar_tokens).all().item()):
            raise ValueError("state 在编码器数据类型中发生非有限溢出")

        token_count = self.spec.condition_tokens
        type_ids = torch.cat(
            (
                torch.zeros(self.spec.state_size, dtype=torch.long, device=state.device),
                torch.ones(self.spec.state_size - 1, dtype=torch.long, device=state.device),
            )
        )
        position_ids = torch.arange(token_count, dtype=torch.long, device=state.device)
        batch_size = state.shape[0]
        type_vectors = self.type_embedding(type_ids).unsqueeze(0).expand(batch_size, -1, -1)
        position_vectors = (
            self.position_embedding(position_ids).unsqueeze(0).expand(batch_size, -1, -1)
        )
        encoded = self.encoder(torch.cat((scalar_tokens, type_vectors, position_vectors), dim=-1))
        if not bool(torch.isfinite(encoded).all().item()):
            raise ValueError("条件编码器输出包含非有限数值")
        return encoded


class BoundedPhysicsCrossAttention(torch.nn.Module):
    """以逐令牌范数上界向隐藏状态注入物理条件。"""

    def __init__(self, spec: ConditioningSpec | None = None) -> None:
        super().__init__()
        self.spec = ConditioningSpec() if spec is None else spec
        if not isinstance(self.spec, ConditioningSpec):
            raise ValueError("spec 必须是 ConditioningSpec")

        self.q_proj = torch.nn.Linear(self.spec.hidden_size, self.spec.bottleneck_size)
        self.k_proj = torch.nn.Linear(self.spec.bottleneck_size, self.spec.bottleneck_size)
        self.v_proj = torch.nn.Linear(self.spec.bottleneck_size, self.spec.bottleneck_size)
        self.out_proj = torch.nn.Linear(self.spec.bottleneck_size, self.spec.hidden_size)
        self.alpha = torch.nn.Parameter(torch.tensor(self.spec.gate_init))
        self.head_dim = self.spec.bottleneck_size // self.spec.attention_heads

    def _validate_inputs(
        self,
        hidden: torch.Tensor,
        condition: torch.Tensor,
        injection_mask: torch.Tensor,
    ) -> None:
        if (
            not isinstance(hidden, torch.Tensor)
            or hidden.ndim != 3
            or hidden.shape[0] < 1
            or hidden.shape[1] < 1
            or hidden.shape[2] != self.spec.hidden_size
        ):
            raise ValueError("hidden 必须是非空的 [B,T,2048] 张量")
        if (
            not isinstance(condition, torch.Tensor)
            or condition.ndim != 3
            or condition.shape
            != (hidden.shape[0], self.spec.condition_tokens, self.spec.bottleneck_size)
        ):
            raise ValueError("condition 必须是与 hidden 同批次的 [B,9,256] 张量")
        if (
            not isinstance(injection_mask, torch.Tensor)
            or injection_mask.dtype != torch.bool
            or injection_mask.shape != hidden.shape[:2]
        ):
            raise ValueError("injection_mask 必须是形状为 [B,T] 的布尔张量")
        if not torch.is_floating_point(hidden) or not torch.is_floating_point(condition):
            raise ValueError("hidden 和 condition 必须是浮点张量")
        if hidden.device != condition.device or hidden.device != injection_mask.device:
            raise ValueError("hidden、condition 与 injection_mask 必须位于同一设备")
        if hidden.device != self.q_proj.weight.device:
            raise ValueError("输入与交叉注意力模块必须位于同一设备")
        if not bool(torch.isfinite(hidden).all().item()):
            raise ValueError("hidden 必须只包含有限数值")
        if not bool(torch.isfinite(condition).all().item()):
            raise ValueError("condition 必须只包含有限数值")

    def forward(
        self,
        hidden: torch.Tensor,
        condition: torch.Tensor,
        injection_mask: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        self._validate_inputs(hidden, condition, injection_mask)
        batch_size, sequence_length, _ = hidden.shape

        query = self.q_proj(hidden.to(dtype=self.q_proj.weight.dtype))
        key = self.k_proj(condition.to(dtype=self.k_proj.weight.dtype))
        value = self.v_proj(condition.to(dtype=self.v_proj.weight.dtype))
        query = query.reshape(
            batch_size, sequence_length, self.spec.attention_heads, self.head_dim
        ).transpose(1, 2)
        key = key.reshape(
            batch_size, self.spec.condition_tokens, self.spec.attention_heads, self.head_dim
        ).transpose(1, 2)
        value = value.reshape(
            batch_size, self.spec.condition_tokens, self.spec.attention_heads, self.head_dim
        ).transpose(1, 2)

        scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(self.head_dim)
        softmax_dtype = (
            torch.float32 if scores.dtype in {torch.float16, torch.bfloat16} else scores.dtype
        )
        attention_weights = torch.softmax(scores, dim=-1, dtype=softmax_dtype)
        if not bool(torch.isfinite(attention_weights).all().item()):
            raise ValueError("交叉注意力权重包含非有限数值")
        context = torch.matmul(attention_weights.to(dtype=value.dtype), value)
        context = context.transpose(1, 2).reshape(
            batch_size, sequence_length, self.spec.bottleneck_size
        )
        attention_output = self.out_proj(context.to(dtype=self.out_proj.weight.dtype))
        if not bool(torch.isfinite(attention_output).all().item()):
            raise ValueError("交叉注意力输出包含非有限数值")
        if not bool(torch.isfinite(self.alpha).all().item()):
            raise ValueError("alpha 必须是有限标量")

        calculation_dtype = (
            torch.float32
            if hidden.dtype in {torch.float16, torch.bfloat16}
            or attention_output.dtype in {torch.float16, torch.bfloat16}
            else torch.promote_types(hidden.dtype, attention_output.dtype)
        )
        hidden_for_norm = hidden.to(dtype=calculation_dtype)
        output_for_norm = attention_output.to(dtype=calculation_dtype)
        hidden_norm = torch.linalg.vector_norm(hidden_for_norm, dim=-1, keepdim=True).detach()
        output_norm = torch.linalg.vector_norm(output_for_norm, dim=-1, keepdim=True)
        if not bool(torch.isfinite(hidden_norm).all().item()):
            raise ValueError("隐藏状态范数包含非有限数值")
        if not bool(torch.isfinite(output_norm).all().item()):
            raise ValueError("交叉注意力输出范数包含非有限数值")
        gate = self.spec.residual_ratio_cap * torch.tanh(self.alpha.to(dtype=calculation_dtype))
        residual = gate * hidden_norm * output_for_norm / (output_norm + self.spec.norm_epsilon)
        masked_residual = torch.where(
            injection_mask.unsqueeze(-1), residual, torch.zeros_like(residual)
        )
        corrected_hidden = hidden + masked_residual.to(dtype=hidden.dtype)
        if not bool(torch.isfinite(corrected_hidden).all().item()):
            raise ValueError("修正隐藏状态包含非有限数值")

        entropy_terms = (
            attention_weights
            * attention_weights.clamp_min(torch.finfo(attention_weights.dtype).tiny).log()
        )
        entropy_per_query = -entropy_terms.sum(dim=-1)
        entropy_mask = injection_mask.unsqueeze(1).expand(-1, self.spec.attention_heads, -1)
        entropy_count = entropy_mask.sum()
        attention_entropy = torch.where(
            entropy_count > 0,
            torch.where(entropy_mask, entropy_per_query, 0.0).sum() / entropy_count.clamp_min(1),
            entropy_per_query.new_zeros(()),
        )

        residual_norm = torch.linalg.vector_norm(masked_residual, dim=-1)
        measured_ratios = residual_norm / (hidden_norm.squeeze(-1) + self.spec.norm_epsilon)
        max_residual_ratio = measured_ratios.amax()
        if not bool(torch.isfinite(attention_entropy).item()):
            raise ValueError("注意力熵包含非有限数值")
        if not bool(torch.isfinite(max_residual_ratio).item()):
            raise ValueError("最大残差比例包含非有限数值")
        return corrected_hidden, attention_entropy, max_residual_ratio


def _anchor_position_tensor(
    anchor_positions: int | Sequence[int] | torch.Tensor,
    *,
    batch_size: int,
    sequence_length: int,
    device: torch.device,
) -> torch.Tensor:
    if isinstance(anchor_positions, bool):
        raise ValueError("anchor_positions 必须为整数或逐样本整数序列")
    if isinstance(anchor_positions, int):
        positions = torch.full((batch_size,), anchor_positions, dtype=torch.long, device=device)
    elif isinstance(anchor_positions, torch.Tensor):
        integer_dtypes = {
            torch.uint8,
            torch.int8,
            torch.int16,
            torch.int32,
            torch.int64,
        }
        if (
            anchor_positions.dtype not in integer_dtypes
            or anchor_positions.ndim != 1
            or anchor_positions.shape[0] != batch_size
        ):
            raise ValueError("anchor_positions 张量必须是形状为 [B] 的整数张量")
        positions = anchor_positions.to(device=device, dtype=torch.long)
    elif isinstance(anchor_positions, Sequence) and not isinstance(anchor_positions, (str, bytes)):
        if any(isinstance(value, bool) or not isinstance(value, int) for value in anchor_positions):
            raise ValueError("anchor_positions 序列必须只包含整数")
        if len(anchor_positions) != batch_size:
            raise ValueError("anchor_positions 序列长度必须等于批次大小")
        positions = torch.tensor(tuple(anchor_positions), dtype=torch.long, device=device)
    else:
        raise ValueError("anchor_positions 必须为整数或逐样本整数序列")

    if bool(((positions < 0) | (positions >= sequence_length)).any().item()):
        raise ValueError("anchor_positions 包含越界位置")
    return positions


def build_condition_state(
    hidden: torch.Tensor,
    anchor_positions: int | Sequence[int] | torch.Tensor,
    state_head: Callable[[torch.Tensor], torch.Tensor],
) -> torch.Tensor:
    """提取逐样本锚点隐藏状态并通过既有状态头生成五维条件状态。"""

    if (
        not isinstance(hidden, torch.Tensor)
        or hidden.ndim != 3
        or hidden.shape[0] < 1
        or hidden.shape[1] < 1
        or hidden.shape[2] != 2048
    ):
        raise ValueError("hidden 必须是非空的 [B,T,2048] 张量")
    if not torch.is_floating_point(hidden) or not bool(torch.isfinite(hidden).all().item()):
        raise ValueError("hidden 必须只包含有限浮点数")
    if not callable(state_head):
        raise ValueError("state_head 必须可调用")

    batch_size, sequence_length, _ = hidden.shape
    positions = _anchor_position_tensor(
        anchor_positions,
        batch_size=batch_size,
        sequence_length=sequence_length,
        device=hidden.device,
    )
    batch_indices = torch.arange(batch_size, dtype=torch.long, device=hidden.device)
    selected_hidden = hidden[batch_indices, positions]
    state = state_head(selected_hidden)
    if not isinstance(state, torch.Tensor) or state.shape != (batch_size, 5):
        raise ValueError("state_head 输出必须是形状为 [B,5] 的张量")
    if not torch.is_floating_point(state):
        raise ValueError("state_head 输出必须是浮点张量")
    if not bool(torch.isfinite(state).all().item()):
        raise ValueError("state_head 输出必须只包含有限数值")
    if bool((state < 0).any().item()):
        raise ValueError("state_head 输出不得包含负值")
    return state


def build_training_injection_mask(labels: torch.Tensor) -> torch.Tensor:
    """把受监督标签右移映射到产生这些标签的预测位置。"""

    if not isinstance(labels, torch.Tensor) or labels.ndim != 2 or labels.shape[1] < 1:
        raise ValueError("labels 必须是形状为 [B,T] 且 T 至少为 1 的张量")
    mask = torch.zeros_like(labels, dtype=torch.bool)
    mask[:, :-1] = labels[:, 1:] != -100
    return mask


def _completion_starts(
    completion_start: int | Sequence[int] | torch.Tensor,
    *,
    batch_size: int,
    device: torch.device,
) -> torch.Tensor:
    if isinstance(completion_start, bool):
        raise ValueError("completion_start 必须为整数或逐样本整数序列")
    if isinstance(completion_start, int):
        return torch.full((batch_size,), completion_start, dtype=torch.long, device=device)
    if isinstance(completion_start, torch.Tensor):
        starts = completion_start
    elif isinstance(completion_start, Sequence) and not isinstance(completion_start, (str, bytes)):
        if any(isinstance(value, bool) or not isinstance(value, int) for value in completion_start):
            raise ValueError("completion_start 序列必须只包含整数")
        starts = torch.tensor(tuple(completion_start), dtype=torch.long, device=device)
    else:
        raise ValueError("completion_start 必须为整数或逐样本整数序列")

    integer_dtypes = {
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
    }
    if starts.dtype not in integer_dtypes or starts.ndim != 1 or starts.shape[0] != batch_size:
        raise ValueError("completion_start 张量必须是形状为 [B] 的整数张量")
    return starts.to(device=device, dtype=torch.long)


def build_candidate_injection_mask(
    completion_start: int | Sequence[int] | torch.Tensor,
    attention_mask: torch.Tensor,
) -> torch.Tensor:
    """为候选补全部分建立与自回归预测位置对应的注入掩码。"""

    if (
        not isinstance(attention_mask, torch.Tensor)
        or attention_mask.ndim != 2
        or attention_mask.shape[0] < 1
        or attention_mask.shape[1] < 1
    ):
        raise ValueError("attention_mask 必须是非空的 [B,T] 张量")
    if attention_mask.dtype == torch.bool:
        valid_tokens = attention_mask
    elif attention_mask.dtype in {
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
    }:
        if not bool(((attention_mask == 0) | (attention_mask == 1)).all().item()):
            raise ValueError("attention_mask 整数元素只能为 0 或 1")
        valid_tokens = attention_mask.to(dtype=torch.bool)
    else:
        raise ValueError("attention_mask 必须是布尔或 0/1 整数张量")

    batch_size, sequence_length = valid_tokens.shape
    starts = _completion_starts(
        completion_start,
        batch_size=batch_size,
        device=attention_mask.device,
    )
    positions = torch.arange(sequence_length, device=attention_mask.device).expand(batch_size, -1)
    last_valid = positions.masked_fill(~valid_tokens, -1).amax(dim=1)
    if bool((last_valid < 0).any().item()):
        raise ValueError("attention_mask 的每条样本必须至少包含一个有效令牌")
    if bool(((starts < 1) | (starts > last_valid)).any().item()):
        raise ValueError("completion_start 必须位于 1 到最后一个有效令牌之间")

    start_is_valid = valid_tokens.gather(1, starts.unsqueeze(1)).squeeze(1)
    predecessor_is_valid = valid_tokens.gather(1, (starts - 1).unsqueeze(1)).squeeze(1)
    if not bool((start_is_valid & predecessor_is_valid).all().item()):
        raise ValueError("completion_start 及其前一位置都必须是有效令牌")

    mask = (positions >= (starts - 1).unsqueeze(1)) & (positions < last_valid.unsqueeze(1))
    covered_tokens = (positions >= (starts - 1).unsqueeze(1)) & (
        positions <= last_valid.unsqueeze(1)
    )
    if not bool((valid_tokens | ~covered_tokens).all().item()):
        raise ValueError("completion_start 到最后有效令牌之间不得包含掩码空洞")
    return mask


def _read_named_output(model_output: object, name: str) -> object:
    if isinstance(model_output, Mapping) and name in model_output:
        return model_output[name]
    try:
        return getattr(model_output, name)
    except AttributeError as error:
        raise AttributeError(f"底层模型输出不包含 {name!r}") from error


@dataclass(frozen=True)
class PhysicsConditionedOutput:
    """普通前向的底层输出、条件状态和诊断。"""

    model_output: object
    predicted_state: torch.Tensor | None
    condition_tokens: torch.Tensor | None
    diagnostics: ConditioningDiagnostics

    @property
    def loss(self) -> object:
        """读取底层输出的损失。"""

        return _read_named_output(self.model_output, "loss")

    @property
    def logits(self) -> object:
        """读取底层输出的逻辑值。"""

        return _read_named_output(self.model_output, "logits")

    def __getitem__(self, name: str) -> object:
        if not isinstance(name, str):
            raise TypeError("PhysicsConditionedOutput 只支持按名称读取")
        return _read_named_output(self.model_output, name)

    def __getattr__(self, name: str) -> object:
        model_output = object.__getattribute__(self, "model_output")
        return _read_named_output(model_output, name)


@dataclass(frozen=True)
class PhysicsConditionedGeneration:
    """缓存自由生成的底层结果与最终诊断。"""

    model_output: object
    diagnostics: ConditioningDiagnostics

    def __getitem__(self, name: str) -> object:
        if not isinstance(name, str):
            raise TypeError("PhysicsConditionedGeneration 只支持按名称读取")
        return _read_named_output(self.model_output, name)

    def __getattr__(self, name: str) -> object:
        model_output = object.__getattribute__(self, "model_output")
        return _read_named_output(model_output, name)


@dataclass
class _ConditioningSession:
    """一次同步调用独占的挂钩状态。"""

    mode: str
    anchor_positions: torch.Tensor | None
    injection_mask: torch.Tensor | None
    predicted_state: torch.Tensor | None = None
    condition_tokens: torch.Tensor | None = None
    current_injection_mask: torch.Tensor | None = None
    cache_ready: bool = False
    source_hook_count: int = 0
    target_hook_counts: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    target_seen_in_step: list[bool] = field(default_factory=lambda: [False, False, False, False])
    attention_entropy_sums: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    max_residual_ratio: float = 0.0
    prefill_count: int = 0
    cached_decode_count: int = 0


class PhysicsConditionedRuntime(torch.nn.Module):
    """通过 Qwen 解码层挂钩执行单进程、同步的有界物理条件注入。"""

    _STRUCTURE_PREFIXES = ("state_head.", "condition_encoder.", "injectors.")

    def __init__(
        self,
        model: torch.nn.Module,
        state_head: torch.nn.Module,
        spec: ConditioningSpec | None = None,
    ) -> None:
        super().__init__()
        if not isinstance(model, torch.nn.Module):
            raise ValueError("model 必须是 torch.nn.Module")
        if not isinstance(state_head, torch.nn.Module):
            raise ValueError("state_head 必须是 torch.nn.Module")
        self.spec = ConditioningSpec() if spec is None else spec
        if not isinstance(self.spec, ConditioningSpec):
            raise ValueError("spec 必须是 ConditioningSpec")

        layers = self._resolve_decoder_layers(model)
        self.state_head = state_head
        self.condition_encoder = PhysicalConditionEncoder(self.spec)
        self.injectors = torch.nn.ModuleList(
            BoundedPhysicsCrossAttention(self.spec) for _ in self.spec.target_layers
        )
        object.__setattr__(self, "_model", model)
        object.__setattr__(self, "_active_session", None)
        object.__setattr__(self, "_closed", False)
        object.__setattr__(self, "_hook_handles", [])

        handles: list[RemovableHandle] = []
        try:
            handles.append(layers[self.spec.source_layer].register_forward_hook(self._source_hook))
            for target_index, layer_index in enumerate(self.spec.target_layers):
                handles.append(
                    layers[layer_index].register_forward_pre_hook(
                        self._make_target_hook(target_index),
                        with_kwargs=True,
                    )
                )
        except Exception:
            for handle in handles:
                handle.remove()
            raise
        object.__setattr__(self, "_hook_handles", handles)

    @property
    def model(self) -> torch.nn.Module:
        """返回未注册到底层状态字典的模型引用。"""

        return object.__getattribute__(self, "_model")

    def _resolve_decoder_layers(self, model: torch.nn.Module) -> torch.nn.ModuleList:
        config = getattr(model, "config", None)
        if config is None:
            raise ValueError("model 必须公开 Qwen 配置")
        num_hidden_layers = getattr(config, "num_hidden_layers", None)
        hidden_size = getattr(config, "hidden_size", None)
        resolve_conditioning_layers(num_hidden_layers)
        if type(hidden_size) is not int or hidden_size != self.spec.hidden_size:
            raise ValueError("model.config.hidden_size 必须固定为 2048")

        candidates = (
            ("model", "layers"),
            ("base_model", "model", "model", "layers"),
        )
        resolved: list[tuple[tuple[str, ...], object]] = []
        for path in candidates:
            current: object = model
            for name in path:
                try:
                    current = getattr(current, name)
                except AttributeError:
                    break
            else:
                resolved.append((path, current))

        if len(resolved) != 1:
            paths = "、".join(".".join(path) for path, _ in resolved)
            if not paths:
                paths = "无"
            raise ValueError(f"无法唯一解析受支持的 Qwen/PeftModel 解码层路径，命中：{paths}")
        layers = resolved[0][1]
        if not isinstance(layers, torch.nn.ModuleList):
            raise ValueError("Qwen 解码层容器必须是 torch.nn.ModuleList")
        if len(layers) != self.spec.num_hidden_layers:
            raise ValueError("实际 Qwen 解码层数量必须固定为 28")
        if any(not isinstance(layer, torch.nn.Module) for layer in layers):
            raise ValueError("Qwen 解码层容器只能包含 torch.nn.Module")
        return layers

    @staticmethod
    def _validate_attention_mask(
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        if (
            not isinstance(input_ids, torch.Tensor)
            or input_ids.ndim != 2
            or input_ids.shape[0] < 1
            or input_ids.shape[1] < 1
        ):
            raise ValueError("input_ids 必须是非空的 [B,T] 张量")
        if not isinstance(attention_mask, torch.Tensor) or attention_mask.shape != input_ids.shape:
            raise ValueError("attention_mask 必须与 input_ids 形状相同")
        if input_ids.device != attention_mask.device:
            raise ValueError("input_ids 与 attention_mask 必须位于同一设备")
        if attention_mask.dtype == torch.bool:
            valid_tokens = attention_mask
        elif attention_mask.dtype in {
            torch.uint8,
            torch.int8,
            torch.int16,
            torch.int32,
            torch.int64,
        }:
            if not bool(((attention_mask == 0) | (attention_mask == 1)).all().item()):
                raise ValueError("attention_mask 整数元素只能为 0 或 1")
            valid_tokens = attention_mask.to(dtype=torch.bool)
        else:
            raise ValueError("attention_mask 必须是布尔或 0/1 整数张量")
        if bool((valid_tokens.sum(dim=1) == 0).any().item()):
            raise ValueError("attention_mask 的每条样本必须至少包含一个有效令牌")
        return valid_tokens

    def _ensure_available(self) -> None:
        if object.__getattribute__(self, "_closed"):
            raise RuntimeError("PhysicsConditionedRuntime 已关闭")
        if object.__getattribute__(self, "_active_session") is not None:
            raise RuntimeError("不允许嵌套或并发调用 PhysicsConditionedRuntime")

    def _begin_session(self, session: _ConditioningSession) -> None:
        self._ensure_available()
        object.__setattr__(self, "_active_session", session)

    def _end_session(self, session: _ConditioningSession) -> None:
        if object.__getattribute__(self, "_active_session") is session:
            object.__setattr__(self, "_active_session", None)

    @staticmethod
    def _hidden_from_source_output(output: object) -> torch.Tensor:
        if isinstance(output, torch.Tensor):
            hidden = output
        elif isinstance(output, tuple) and output and isinstance(output[0], torch.Tensor):
            hidden = output[0]
        else:
            raise RuntimeError("第 13 层输出必须是 Tensor 或首元素为 Tensor 的 tuple")
        if hidden.ndim != 3 or hidden.shape[2] != 2048:
            raise RuntimeError("第 13 层隐藏状态必须是 [B,T,2048]")
        return hidden

    def _compute_condition(
        self,
        session: _ConditioningSession,
        hidden: torch.Tensor,
    ) -> None:
        if session.anchor_positions is None:
            raise RuntimeError("条件会话缺少提示锚点")
        if session.predicted_state is not None or session.condition_tokens is not None:
            raise RuntimeError("条件状态不得在同一会话中重复计算")
        predicted_state = build_condition_state(hidden, session.anchor_positions, self.state_head)
        condition_tokens = self.condition_encoder(predicted_state)
        session.predicted_state = predicted_state
        session.condition_tokens = condition_tokens
        session.cache_ready = True

    def _source_hook(
        self,
        _module: torch.nn.Module,
        _args: tuple[object, ...],
        output: object,
    ) -> None:
        session = object.__getattribute__(self, "_active_session")
        if session is None or session.mode == "bypass":
            return
        if session.source_hook_count > 0 and not all(session.target_seen_in_step):
            raise RuntimeError("新的源层调用早于上一轮四个目标层完成")

        hidden = self._hidden_from_source_output(output)
        if session.mode in {"training", "candidate"}:
            if session.source_hook_count != 0:
                raise RuntimeError("普通前向中的第 13 层只能调用一次")
            if session.injection_mask is None or session.injection_mask.shape != hidden.shape[:2]:
                raise RuntimeError("普通前向注入掩码与第 13 层隐藏状态不匹配")
            self._compute_condition(session, hidden)
            session.current_injection_mask = session.injection_mask
        elif session.mode == "generate":
            if hidden.shape[1] > 1:
                if session.prefill_count != 0 or session.cache_ready:
                    raise RuntimeError("缓存生成只允许一次完整提示预填充")
                if (
                    session.injection_mask is None
                    or session.injection_mask.shape != hidden.shape[:2]
                ):
                    raise RuntimeError("生成预填充掩码与第 13 层隐藏状态不匹配")
                self._compute_condition(session, hidden)
                session.current_injection_mask = session.injection_mask
                session.prefill_count += 1
            else:
                if not session.cache_ready or session.condition_tokens is None:
                    raise RuntimeError("缓存解码发生在条件预填充之前")
                if hidden.shape[0] != session.condition_tokens.shape[0]:
                    raise RuntimeError("缓存解码批次与已缓存条件不匹配")
                session.current_injection_mask = torch.ones(
                    hidden.shape[:2], dtype=torch.bool, device=hidden.device
                )
                session.cached_decode_count += 1
        else:
            raise RuntimeError(f"未知条件会话模式：{session.mode}")

        session.source_hook_count += 1
        session.target_seen_in_step = [False, False, False, False]

    @staticmethod
    def _hidden_from_target_input(
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> tuple[torch.Tensor, bool]:
        if "hidden_states" in kwargs:
            hidden = kwargs["hidden_states"]
            from_kwargs = True
        elif args:
            hidden = args[0]
            from_kwargs = False
        else:
            raise RuntimeError("目标 Qwen 层调用缺少 hidden_states")
        if not isinstance(hidden, torch.Tensor):
            raise RuntimeError("目标 Qwen 层的 hidden_states 必须是 Tensor")
        return hidden, from_kwargs

    def _make_target_hook(
        self,
        target_index: int,
    ) -> Callable[
        [torch.nn.Module, tuple[object, ...], dict[str, object]],
        tuple[tuple[object, ...], dict[str, object]] | None,
    ]:
        def hook(
            _module: torch.nn.Module,
            args: tuple[object, ...],
            kwargs: dict[str, object],
        ) -> tuple[tuple[object, ...], dict[str, object]] | None:
            session = object.__getattribute__(self, "_active_session")
            if session is None or session.mode == "bypass":
                return None
            if session.source_hook_count == 0:
                raise RuntimeError("目标层调用早于第 13 层条件源")
            if session.condition_tokens is None or session.current_injection_mask is None:
                raise RuntimeError("目标层调用时缺失条件词元或注入掩码")
            next_target = next(
                (index for index, seen in enumerate(session.target_seen_in_step) if not seen),
                None,
            )
            if next_target != target_index:
                raise RuntimeError("四个目标层必须按 24、25、26、27 顺序各调用一次")

            hidden, from_kwargs = self._hidden_from_target_input(args, kwargs)
            if hidden.shape[:2] != session.current_injection_mask.shape:
                raise RuntimeError("目标层隐藏状态与当前注入掩码形状不匹配")
            corrected, entropy, residual_ratio = self.injectors[target_index](
                hidden,
                session.condition_tokens,
                session.current_injection_mask,
            )
            session.target_seen_in_step[target_index] = True
            session.target_hook_counts[target_index] += 1
            session.attention_entropy_sums[target_index] += float(entropy.detach().item())
            session.max_residual_ratio = max(
                session.max_residual_ratio,
                float(residual_ratio.detach().item()),
            )

            if from_kwargs:
                updated_kwargs = dict(kwargs)
                updated_kwargs["hidden_states"] = corrected
                return args, updated_kwargs
            updated_args = (corrected, *args[1:])
            return updated_args, kwargs

        return hook

    def _validate_complete(self, session: _ConditioningSession) -> None:
        if session.mode == "bypass":
            return
        if session.predicted_state is None or session.condition_tokens is None:
            raise RuntimeError("底层模型未经过第 13 层条件源")
        if not all(session.target_seen_in_step):
            raise RuntimeError("底层模型未完成四个目标层注入")
        expected_counts = (session.source_hook_count,) * 4
        if tuple(session.target_hook_counts) != expected_counts:
            raise RuntimeError("源层与四个目标层挂钩次数不一致")
        if session.mode == "generate":
            if session.prefill_count != 1:
                raise RuntimeError("缓存生成必须恰好执行一次完整提示预填充")
            if session.source_hook_count != session.prefill_count + session.cached_decode_count:
                raise RuntimeError("生成源层计数与预填充/缓存解码计数不一致")
        elif session.source_hook_count != 1:
            raise RuntimeError("普通前向必须恰好执行一次条件源与注入")

    def _diagnostics(self, session: _ConditioningSession) -> ConditioningDiagnostics:
        gate_values = tuple(
            float(
                (
                    self.spec.residual_ratio_cap
                    * torch.tanh(injector.alpha.detach().to(dtype=torch.float32))
                ).item()
            )
            for injector in self.injectors
        )
        entropies = tuple(
            total / count if count else 0.0
            for total, count in zip(
                session.attention_entropy_sums,
                session.target_hook_counts,
                strict=True,
            )
        )
        return ConditioningDiagnostics(
            gate_values=gate_values,
            attention_entropies=entropies,
            max_residual_ratio=session.max_residual_ratio,
            source_hook_count=session.source_hook_count,
            target_hook_counts=tuple(session.target_hook_counts),
            prefill_count=session.prefill_count,
            cached_decode_count=session.cached_decode_count,
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
        completion_start: int | Sequence[int] | torch.Tensor | None = None,
        bypass: bool = False,
        **kwargs: object,
    ) -> PhysicsConditionedOutput:
        """执行训练、候选评分或显式旁路前向。"""

        self._ensure_available()
        if type(bypass) is not bool:
            raise ValueError("bypass 必须是布尔值")

        if bypass:
            session = _ConditioningSession("bypass", None, None)
        else:
            valid_tokens = self._validate_attention_mask(input_ids, attention_mask)
            if labels is not None and completion_start is None:
                if labels.shape != input_ids.shape or labels.device != input_ids.device:
                    raise ValueError("labels 必须与 input_ids 形状和设备相同")
                supervised = labels != -100
                if bool((supervised.sum(dim=1) == 0).any().item()):
                    raise ValueError("labels 的每条样本必须至少包含一个监督令牌")
                first_supervised = supervised.to(dtype=torch.int64).argmax(dim=1)
                if bool((first_supervised < 1).any().item()):
                    raise ValueError("首个监督令牌之前必须存在提示锚点")
                session = _ConditioningSession(
                    "training",
                    first_supervised - 1,
                    build_training_injection_mask(labels),
                )
            elif completion_start is not None:
                injection_mask = build_candidate_injection_mask(
                    completion_start,
                    attention_mask,
                )
                starts = _completion_starts(
                    completion_start,
                    batch_size=input_ids.shape[0],
                    device=input_ids.device,
                )
                session = _ConditioningSession("candidate", starts - 1, injection_mask)
            else:
                raise ValueError("结构前向必须提供 labels 或 completion_start")
            if valid_tokens.shape != session.injection_mask.shape:
                raise RuntimeError("内部注入掩码形状错误")

        self._begin_session(session)
        model_kwargs = dict(kwargs)
        if labels is not None:
            model_kwargs["labels"] = labels
        try:
            model_output = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **model_kwargs,
            )
            self._validate_complete(session)
            return PhysicsConditionedOutput(
                model_output=model_output,
                predicted_state=session.predicted_state,
                condition_tokens=session.condition_tokens,
                diagnostics=self._diagnostics(session),
            )
        finally:
            self._end_session(session)

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        bypass: bool = False,
        **kwargs: object,
    ) -> PhysicsConditionedGeneration:
        """以一次预填充和后续单令牌缓存步骤执行自由生成。"""

        self._ensure_available()
        if type(bypass) is not bool:
            raise ValueError("bypass 必须是布尔值")
        num_beams = kwargs.get("num_beams", 1)
        if isinstance(num_beams, bool) or not isinstance(num_beams, int) or num_beams != 1:
            raise ValueError("PhysicsConditionedRuntime.generate 只支持 num_beams=1")

        if bypass:
            session = _ConditioningSession("bypass", None, None)
        else:
            valid_tokens = self._validate_attention_mask(input_ids, attention_mask)
            positions = torch.arange(input_ids.shape[1], device=input_ids.device).expand_as(
                input_ids
            )
            anchors = positions.masked_fill(~valid_tokens, -1).amax(dim=1)
            prefill_mask = torch.zeros_like(valid_tokens)
            prefill_mask.scatter_(1, anchors.unsqueeze(1), True)
            session = _ConditioningSession("generate", anchors, prefill_mask)

        self._begin_session(session)
        try:
            model_output = self.model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **kwargs,
            )
            self._validate_complete(session)
            return PhysicsConditionedGeneration(
                model_output=model_output,
                diagnostics=self._diagnostics(session),
            )
        finally:
            self._end_session(session)

    def structure_parameter_names(self) -> tuple[str, ...]:
        """返回训练器可使用的结构参数白名单。"""

        return tuple(name for name, _ in self.named_parameters())

    def structure_parameter_count(self) -> int:
        """返回全部结构参数的标量数量。"""

        return sum(parameter.numel() for parameter in self.parameters())

    def unexpected_base_parameter_names(self) -> tuple[str, ...]:
        """返回意外同时注册为底层模型参数的结构参数名。"""

        base_parameter_ids = {id(parameter) for parameter in self.model.parameters()}
        return tuple(
            name
            for name, parameter in self.named_parameters()
            if id(parameter) in base_parameter_ids
        )

    def structure_state_dict(self) -> dict[str, torch.Tensor]:
        """复制只含状态头、共享编码器和四个注入器的状态。"""

        state = self.state_dict()
        unexpected = tuple(name for name in state if not name.startswith(self._STRUCTURE_PREFIXES))
        if unexpected:
            raise RuntimeError(f"运行时状态字典包含意外参数：{unexpected}")
        if self.unexpected_base_parameter_names():
            raise RuntimeError("运行时意外注册了底层模型参数")
        return {name: value.detach().clone() for name, value in state.items()}

    def load_structure_state_dict(
        self,
        state: Mapping[str, torch.Tensor],
        strict: bool = True,
    ) -> object:
        """在完整校验后加载结构状态，避免部分写入。"""

        if not isinstance(state, Mapping):
            raise ValueError("state 必须是参数名称到张量的映射")
        if type(strict) is not bool:
            raise ValueError("strict 必须是布尔值")
        expected = self.state_dict()
        supplied_keys = set(state)
        expected_keys = set(expected)
        missing = tuple(sorted(expected_keys - supplied_keys))
        unexpected = tuple(sorted(supplied_keys - expected_keys))
        if strict and (missing or unexpected):
            raise ValueError(f"结构状态键不匹配：缺失={missing}，多余={unexpected}")

        compatible: dict[str, torch.Tensor] = {}
        for name in sorted(expected_keys & supplied_keys):
            value = state[name]
            if not isinstance(value, torch.Tensor):
                raise ValueError(f"结构状态 {name} 必须是 Tensor")
            if value.shape != expected[name].shape:
                raise ValueError(
                    f"结构状态 {name} 形状不匹配：{tuple(value.shape)} != "
                    f"{tuple(expected[name].shape)}"
                )
            if name.endswith(".alpha") and not bool(torch.isfinite(value).all().item()):
                raise ValueError(f"门参数 {name} 必须只包含有限值")
            compatible[name] = value
        return super().load_state_dict(compatible, strict=strict)

    def close(self) -> None:
        """显式移除全部挂钩；关闭后不再允许运行时调用。"""

        if object.__getattribute__(self, "_active_session") is not None:
            raise RuntimeError("活动会话期间不得关闭 PhysicsConditionedRuntime")
        if object.__getattribute__(self, "_closed"):
            return
        handles = object.__getattribute__(self, "_hook_handles")
        for handle in handles:
            handle.remove()
        handles.clear()
        object.__setattr__(self, "_closed", True)
