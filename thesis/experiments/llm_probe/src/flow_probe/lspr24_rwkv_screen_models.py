"""LSPR24 RWKV 候选快速消融的共享模型组件。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


SCREEN_VARIANTS: Final[tuple[str, ...]] = ("B1", "B1F", "A2", "B3")
VARIANT_NAMES: Final[dict[str, str]] = {
    "B1": "causal_transformer",
    "B1F": "field_attention_transformer",
    "A2": "rwkv_conditioned_field_transformer",
    "B3": "rwkv_time_mixer",
}


class Lspr24RwkvModelError(ValueError):
    """模型配置、输入或参数预算不满足快速消融合同。"""


def reshape_history(
    features: np.ndarray,
    history_length: int,
    feature_count: int,
) -> np.ndarray:
    """把统一加载器的扁平历史恢复为 ``[N,H+1,F]``。"""
    values = np.asarray(features)
    if values.ndim != 2:
        raise Lspr24RwkvModelError("扁平特征必须是二维数组")
    if history_length <= 0 or feature_count <= 0:
        raise Lspr24RwkvModelError("历史长度和字段数必须为正整数")
    expected_width = (history_length + 1) * feature_count
    if values.shape[1] != expected_width:
        raise Lspr24RwkvModelError(
            f"扁平特征宽度不匹配：实际 {values.shape[1]}，预期 {expected_width}"
        )
    return values.reshape(values.shape[0], history_length + 1, feature_count)


@dataclass(frozen=True)
class TrainNormalizer:
    """只由训练切分拟合的逐字段非有限值替换与标准化统计。"""

    replacement: np.ndarray
    mean: np.ndarray
    std: np.ndarray
    clip_value: float = 10.0

    @classmethod
    def fit(cls, train_sequence: np.ndarray, clip_value: float = 10.0) -> TrainNormalizer:
        sequence = np.asarray(train_sequence, dtype=np.float64)
        if sequence.ndim != 3 or sequence.shape[2] == 0:
            raise Lspr24RwkvModelError("训练序列必须是非空的 [N,T,F] 数组")
        if sequence.shape[0] == 0 or sequence.shape[1] == 0:
            raise Lspr24RwkvModelError("训练序列不得为空")
        if not np.isfinite(clip_value) or clip_value <= 0:
            raise Lspr24RwkvModelError("标准化裁剪阈值必须为有限正数")

        feature_count = sequence.shape[2]
        flattened = sequence.reshape(-1, feature_count)
        replacement = np.empty(feature_count, dtype=np.float64)
        for index in range(feature_count):
            finite = flattened[np.isfinite(flattened[:, index]), index]
            if finite.size == 0:
                raise Lspr24RwkvModelError(f"训练字段 {index} 没有有限值")
            replacement[index] = float(np.median(finite))
        filled = np.where(np.isfinite(flattened), flattened, replacement)
        mean = filled.mean(axis=0, dtype=np.float64)
        std = filled.std(axis=0, dtype=np.float64)
        std = np.where(np.isfinite(std) & (std >= 1e-6), std, 1.0)
        return cls(replacement=replacement, mean=mean, std=std, clip_value=clip_value)

    def transform(self, sequence: np.ndarray) -> np.ndarray:
        values = np.asarray(sequence, dtype=np.float64)
        if values.ndim != 3 or values.shape[2] != len(self.mean):
            raise Lspr24RwkvModelError("待转换序列字段数与训练统计不一致")
        filled = np.where(np.isfinite(values), values, self.replacement)
        normalized = (filled - self.mean) / self.std
        transformed = np.clip(normalized, -self.clip_value, self.clip_value).astype(
            np.float32,
            copy=False,
        )
        if not np.isfinite(transformed).all():
            raise Lspr24RwkvModelError("标准化后仍包含非有限值")
        return transformed


@dataclass(frozen=True)
class ScreenModelConfig:
    """四变体共享的候选筛选模型预算。"""

    hidden_size: int = 64
    num_heads: int = 4
    time_layers: int = 2
    feedforward_multiplier: int = 8
    dropout: float = 0.1
    history_length: int = 4

    def validate(self) -> None:
        if self.hidden_size <= 0 or self.hidden_size % self.num_heads != 0:
            raise Lspr24RwkvModelError("hidden_size 必须为 num_heads 的正整数倍")
        if self.time_layers != 2:
            raise Lspr24RwkvModelError("快速消融固定使用两层时间混合器")
        if self.feedforward_multiplier <= 0:
            raise Lspr24RwkvModelError("前馈扩展倍数必须为正整数")
        if not 0.0 <= self.dropout < 1.0:
            raise Lspr24RwkvModelError("dropout 必须位于 [0,1)")
        if self.history_length != 4:
            raise Lspr24RwkvModelError("快速消融固定 H=4")

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


class FieldTokenizer(nn.Module):
    """共享的标量投影、字段嵌入与语义组嵌入。"""

    def __init__(
        self,
        feature_count: int,
        field_group_ids: tuple[int, ...],
        hidden_size: int,
    ) -> None:
        super().__init__()
        if feature_count <= 0 or len(field_group_ids) != feature_count:
            raise Lspr24RwkvModelError("字段数与语义组编号长度不一致")
        if min(field_group_ids, default=-1) < 0:
            raise Lspr24RwkvModelError("语义组编号不得为负数")
        self.feature_count = feature_count
        self.scalar_projection = nn.Linear(1, hidden_size)
        self.field_embedding = nn.Parameter(torch.empty(feature_count, hidden_size))
        self.group_embedding = nn.Embedding(max(field_group_ids) + 1, hidden_size)
        self.register_buffer(
            "field_group_ids",
            torch.tensor(field_group_ids, dtype=torch.long),
            persistent=True,
        )
        nn.init.normal_(self.field_embedding, mean=0.0, std=0.02)
        nn.init.normal_(self.group_embedding.weight, mean=0.0, std=0.02)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        if values.ndim != 3 or values.shape[2] != self.feature_count:
            raise Lspr24RwkvModelError("模型输入必须是字段数匹配的 [B,T,F]")
        token_values = self.scalar_projection(values.unsqueeze(-1))
        identity = self.field_embedding + self.group_embedding(self.field_group_ids)
        return token_values + identity.view(1, 1, self.feature_count, -1)


class FieldAttention(nn.Module):
    """单层无条件字段自注意力，所有含字段交互的变体共享。"""

    def __init__(self, hidden_size: int, num_heads: int, dropout: float) -> None:
        super().__init__()
        self.norm = nn.LayerNorm(hidden_size)
        self.attention = nn.MultiheadAttention(
            hidden_size,
            num_heads,
            dropout=dropout,
            batch_first=True,
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        normalized = self.norm(tokens)
        attended, _ = self.attention(
            normalized,
            normalized,
            normalized,
            need_weights=False,
        )
        return tokens + self.dropout(attended)


class RwkvStateConditioner(nn.Module):
    """按时间递归并以零初始化有界门调制下一步字段标记。"""

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.state_input = nn.Linear(hidden_size, hidden_size, bias=False)
        self.condition_projection = nn.Linear(hidden_size, hidden_size, bias=False)
        self.state_decay = nn.Parameter(torch.zeros(hidden_size))
        self.state_gate = nn.Parameter(torch.zeros(hidden_size))

    def condition(self, tokens: torch.Tensor, previous_state: torch.Tensor) -> torch.Tensor:
        bounded_gate = torch.tanh(self.state_gate)
        modulation = bounded_gate * self.condition_projection(previous_state)
        return tokens + modulation.unsqueeze(1)

    def update(self, previous_state: torch.Tensor, pooled_fields: torch.Tensor) -> torch.Tensor:
        decay = torch.sigmoid(self.state_decay)
        candidate = torch.tanh(self.state_input(pooled_fields))
        return decay * previous_state + (1.0 - decay) * candidate


class CausalTransformerTimeMixer(nn.Module):
    """两层普通因果 Transformer 时间接收基座。"""

    def __init__(self, config: ScreenModelConfig) -> None:
        super().__init__()
        layer = nn.TransformerEncoderLayer(
            d_model=config.hidden_size,
            nhead=config.num_heads,
            dim_feedforward=config.hidden_size * config.feedforward_multiplier,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(
            layer,
            num_layers=config.time_layers,
            norm=nn.LayerNorm(config.hidden_size),
        )

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        length = sequence.shape[1]
        causal_mask = torch.triu(
            torch.ones(length, length, device=sequence.device, dtype=torch.bool),
            diagonal=1,
        )
        return self.encoder(sequence, mask=causal_mask, is_causal=True)


class Rwkv7CoreBlock(nn.Module):
    """候选筛选用 RWKV-7 核心递归，不代表官方完整语言模型。"""

    def __init__(self, config: ScreenModelConfig) -> None:
        super().__init__()
        hidden_size = config.hidden_size
        self.num_heads = config.num_heads
        self.head_size = hidden_size // config.num_heads
        self.time_norm = nn.LayerNorm(hidden_size)
        self.receptance = nn.Linear(hidden_size, hidden_size, bias=False)
        self.key = nn.Linear(hidden_size, hidden_size, bias=False)
        self.value = nn.Linear(hidden_size, hidden_size, bias=False)
        self.decay = nn.Linear(hidden_size, hidden_size, bias=False)
        self.output = nn.Linear(hidden_size, hidden_size, bias=False)
        self.channel_norm = nn.LayerNorm(hidden_size)
        expanded = hidden_size * config.feedforward_multiplier
        self.channel_in = nn.Linear(hidden_size, expanded)
        self.channel_out = nn.Linear(expanded, hidden_size)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        batch_size, time_steps, hidden_size = sequence.shape
        normalized = self.time_norm(sequence)
        state = sequence.new_zeros(
            batch_size,
            self.num_heads,
            self.head_size,
            self.head_size,
        )
        mixed_steps: list[torch.Tensor] = []
        for index in range(time_steps):
            current = normalized[:, index]
            receptance = torch.sigmoid(self.receptance(current)).view(
                batch_size,
                self.num_heads,
                self.head_size,
            )
            key = torch.tanh(self.key(current)).view(
                batch_size,
                self.num_heads,
                self.head_size,
            )
            value = self.value(current).view(batch_size, self.num_heads, self.head_size)
            decay = torch.exp(-F.softplus(self.decay(current))).view(
                batch_size,
                self.num_heads,
                1,
                self.head_size,
            )
            state = state * decay + torch.einsum("bhi,bhj->bhij", value, key)
            readout = torch.einsum("bhij,bhj->bhi", state, key)
            mixed_steps.append((receptance * readout).reshape(batch_size, hidden_size))
        time_mixed = torch.stack(mixed_steps, dim=1)
        sequence = sequence + self.dropout(self.output(time_mixed))
        channel_input = self.channel_norm(sequence)
        channel = self.channel_out(F.gelu(self.channel_in(channel_input)))
        return sequence + self.dropout(channel)


class Rwkv7CoreTimeMixer(nn.Module):
    """由固定状态顺序递归组成的两层候选筛选时间混合器。"""

    def __init__(self, config: ScreenModelConfig) -> None:
        super().__init__()
        self.blocks = nn.ModuleList(Rwkv7CoreBlock(config) for _ in range(config.time_layers))
        self.norm = nn.LayerNorm(config.hidden_size)

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        for block in self.blocks:
            sequence = block(sequence)
        return self.norm(sequence)


class Lspr24ScreenModel(nn.Module):
    """共享输入、分类头，仅替换字段交互或时间混合机制。"""

    def __init__(
        self,
        variant: str,
        feature_count: int,
        field_group_ids: tuple[int, ...],
        config: ScreenModelConfig,
    ) -> None:
        super().__init__()
        if variant not in SCREEN_VARIANTS:
            raise Lspr24RwkvModelError(f"未知快速消融变体：{variant}")
        config.validate()
        self.variant = variant
        self.feature_count = feature_count
        self.expected_steps = config.history_length + 1
        self.tokenizer = FieldTokenizer(
            feature_count=feature_count,
            field_group_ids=field_group_ids,
            hidden_size=config.hidden_size,
        )
        self.field_attention = (
            None
            if variant == "B1"
            else FieldAttention(config.hidden_size, config.num_heads, config.dropout)
        )
        self.time_embedding = nn.Parameter(
            torch.empty(self.expected_steps, config.hidden_size)
        )
        nn.init.normal_(self.time_embedding, mean=0.0, std=0.02)
        self.time_mixer: nn.Module
        if variant == "B3":
            self.time_mixer = Rwkv7CoreTimeMixer(config)
        else:
            self.time_mixer = CausalTransformerTimeMixer(config)
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size),
            nn.Linear(config.hidden_size, 1),
        )
        # A2 专属参数最后初始化，保证同种子下共享主干与 B1F 完全同初始化。
        self.state_conditioner = (
            RwkvStateConditioner(config.hidden_size) if variant == "A2" else None
        )

    def _pool_fields(self, tokens: torch.Tensor) -> torch.Tensor:
        if self.variant == "B1":
            return tokens.mean(dim=2)
        if self.variant != "A2":
            assert self.field_attention is not None
            batch_size, time_steps, feature_count, hidden_size = tokens.shape
            attended = self.field_attention(
                tokens.reshape(batch_size * time_steps, feature_count, hidden_size)
            )
            return attended.mean(dim=1).reshape(batch_size, time_steps, hidden_size)

        assert self.field_attention is not None
        assert self.state_conditioner is not None
        state = tokens.new_zeros(tokens.shape[0], tokens.shape[-1])
        pooled_steps: list[torch.Tensor] = []
        for index in range(tokens.shape[1]):
            conditioned = self.state_conditioner.condition(tokens[:, index], state)
            attended = self.field_attention(conditioned)
            pooled = attended.mean(dim=1)
            pooled_steps.append(pooled)
            state = self.state_conditioner.update(state, pooled)
        return torch.stack(pooled_steps, dim=1)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        if values.ndim != 3 or values.shape[1] != self.expected_steps:
            raise Lspr24RwkvModelError(
                f"模型输入必须是 [B,{self.expected_steps},{self.feature_count}]"
            )
        tokens = self.tokenizer(values)
        sequence = self._pool_fields(tokens)
        sequence = sequence + self.time_embedding.unsqueeze(0)
        mixed = self.time_mixer(sequence)
        return self.classifier(mixed[:, -1]).squeeze(-1)


def build_screen_model(
    name: str,
    feature_count: int,
    field_group_ids: tuple[int, ...],
    config: ScreenModelConfig,
) -> nn.Module:
    """按冻结变体编号或长名称构造快速消融模型。"""
    normalized = name.strip()
    reverse_names = {value: key for key, value in VARIANT_NAMES.items()}
    variant = reverse_names.get(normalized, normalized.upper())
    return Lspr24ScreenModel(variant, feature_count, field_group_ids, config)


def trainable_parameter_count(model: nn.Module) -> int:
    """返回模型可训练参数量。"""
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def parameter_budget(
    feature_count: int,
    field_group_ids: tuple[int, ...],
    config: ScreenModelConfig,
    maximum_ratio: float = 1.15,
) -> dict[str, int]:
    """计算并强制四变体最大/最小参数量比值不超过合同阈值。"""
    counts = {
        variant: trainable_parameter_count(
            build_screen_model(variant, feature_count, field_group_ids, config)
        )
        for variant in SCREEN_VARIANTS
    }
    ratio = max(counts.values()) / min(counts.values())
    if ratio > maximum_ratio:
        details = ", ".join(f"{name}={count}" for name, count in counts.items())
        raise Lspr24RwkvModelError(
            f"参数量比值 {ratio:.6f} 超过 {maximum_ratio:.2f}：{details}"
        )
    return counts
