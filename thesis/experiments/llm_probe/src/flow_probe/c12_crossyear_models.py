"""C12 跨年度阶段 A 的共享接收器与公平神经基线。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

import torch
from torch import nn
from torch.nn import functional as F

from flow_probe.lspr24_rwkv_screen_models import FieldAttention, FieldTokenizer


PHASE_A_VARIANTS: Final[tuple[str, ...]] = (
    "RX-TR",
    "K-DELTA",
    "K-RWKV7",
    "K-GDELTA",
)
LITERATURE_BASELINES: Final[tuple[str, ...]] = ("GRU",)
TRAINABLE_VARIANTS: Final[tuple[str, ...]] = PHASE_A_VARIANTS + LITERATURE_BASELINES
PHASE_B_VARIANTS: Final[tuple[str, ...]] = (
    "C12-CTRL",
    "C12-DREF",
    "C12-FULL",
)
VARIANT_DISPLAY_NAMES: Final[dict[str, str]] = {
    "RX-TR": "接收因果 Transformer",
    "K-DELTA": "DeltaNet 更新核",
    "K-RWKV7": "普通 RWKV-7 更新核",
    "K-GDELTA": "门控 DeltaNet 更新核",
    "GRU": "参数匹配 GRU 文献强基线",
    "C12-CTRL": "仅漂移触发有界状态控制",
    "C12-DREF": "仅可信双参照校正",
    "C12-FULL": "完整漂移触发有界状态控制与可信双参照校正",
}
VARIANT_ROLES: Final[dict[str, str]] = {
    "RX-TR": "阶段 A 更新核公平矩阵接收基座",
    "K-DELTA": "阶段 A 既有更新核公平矩阵成员",
    "K-RWKV7": "阶段 A 既有更新核公平矩阵成员",
    "K-GDELTA": "阶段 A 既有更新核公平矩阵成员",
    "GRU": "外部文献强基线，不是更新核公平矩阵成员",
    "C12-CTRL": "阶段 B 机制一独立变体",
    "C12-DREF": "阶段 B 机制二独立变体",
    "C12-FULL": "阶段 B 两机制完整组合",
}

RWKV7_SOURCE_COMMIT: Final[str] = "952102498e9ed367ea0a59ee64106916d474d30f"
DELTANET_SOURCE_COMMIT: Final[str] = "7843b328b0d3860a66de4eb07ba28bb020ceb1d8"
GATED_DELTANET_SOURCE_COMMIT: Final[str] = "b53d6d3a161267432a79c1c04af69fa52bddc921"


class C12ModelError(ValueError):
    """模型输入、配置或公平预算违反阶段 A 合同。"""


@dataclass(frozen=True)
class C12ModelConfig:
    """所有阶段 A 神经变体共享的模型预算。"""

    input_fields: int = 155
    hidden_size: int = 192
    receiver_heads: int = 6
    receiver_layers: int = 2
    feedforward_multiplier: int = 4
    state_heads: int = 6
    state_head_size: int = 32
    state_layers: int = 1
    maximum_sequence_length: int = 128
    dropout: float = 0.1

    def validate(self) -> None:
        if self.input_fields != 155:
            raise C12ModelError("输入必须恰含 77 个值、77 个缺失位和 1 个相对时间字段")
        if self.hidden_size != self.state_heads * self.state_head_size:
            raise C12ModelError("隐藏维必须等于 6 个头乘每头 32 维")
        if self.receiver_heads != self.state_heads:
            raise C12ModelError("接收器与状态核必须共享 6 个头")
        if self.receiver_layers != 2 or self.state_layers != 1:
            raise C12ModelError("Q0 固定两层接收器和一层完整矩阵状态核")
        if self.maximum_sequence_length != 128:
            raise C12ModelError("Q0 序列上限必须为 128")
        if self.feedforward_multiplier <= 0 or not 0.0 <= self.dropout < 1.0:
            raise C12ModelError("前馈倍率或丢弃率不合法")

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


class C12Receiver(nn.Module):
    """共享字段编码、字段交互和两层因果 Transformer 接收器。"""

    def __init__(self, config: C12ModelConfig) -> None:
        super().__init__()
        config.validate()
        group_ids = (0,) * 77 + (1,) * 77 + (2,)
        self.config = config
        self.tokenizer = FieldTokenizer(config.input_fields, group_ids, config.hidden_size)
        self.field_attention = FieldAttention(
            config.hidden_size,
            config.receiver_heads,
            config.dropout,
        )
        self.position_embedding = nn.Parameter(
            torch.empty(config.maximum_sequence_length, config.hidden_size)
        )
        layer = nn.TransformerEncoderLayer(
            d_model=config.hidden_size,
            nhead=config.receiver_heads,
            dim_feedforward=config.hidden_size * config.feedforward_multiplier,
            dropout=config.dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.time_encoder = nn.TransformerEncoder(
            layer,
            num_layers=config.receiver_layers,
            norm=nn.LayerNorm(config.hidden_size),
        )
        nn.init.normal_(self.position_embedding, mean=0.0, std=0.02)

    def forward(self, values: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        if values.ndim != 3 or values.shape[:2] != valid_mask.shape:
            raise C12ModelError("接收器输入和有效位掩码形状不一致")
        if values.shape[2] != self.config.input_fields:
            raise C12ModelError("接收器输入字段数不符合冻结预算")
        if values.shape[1] > self.config.maximum_sequence_length:
            raise C12ModelError("序列超过 128 条流")
        tokens = self.tokenizer(values)
        batch, steps, fields, hidden = tokens.shape
        attended = self.field_attention(tokens.reshape(batch * steps, fields, hidden))
        sequence = attended.mean(dim=1).reshape(batch, steps, hidden)
        sequence = sequence + self.position_embedding[:steps].unsqueeze(0)
        causal_mask = torch.triu(
            torch.ones(steps, steps, device=values.device, dtype=torch.bool),
            diagonal=1,
        )
        return self.time_encoder(
            sequence,
            mask=causal_mask,
            src_key_padding_mask=~valid_mask,
            is_causal=True,
        )


class ReceiverSourceScorer(nn.Module):
    """第一阶段共同源评分器。"""

    def __init__(self, config: C12ModelConfig) -> None:
        super().__init__()
        self.receiver = C12Receiver(config)
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size),
            nn.Linear(config.hidden_size, 1),
        )

    def forward(self, values: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.receiver(values, valid_mask)).squeeze(-1)


class ActiveParameterCompensation(nn.Module):
    """让补偿参数真实改变每步上下文，而不是登记不可达的空参数。"""

    def __init__(self, hidden_size: int, parameter_count: int) -> None:
        super().__init__()
        if parameter_count < 0:
            raise C12ModelError("补偿参数数目不得为负")
        full, remainder = divmod(parameter_count, hidden_size * hidden_size)
        self.hidden_size = hidden_size
        self.matrices = nn.ParameterList(
            nn.Parameter(torch.empty(hidden_size, hidden_size)) for _ in range(full)
        )
        self.remainder = (
            nn.Parameter(torch.empty(remainder)) if remainder else None
        )
        for matrix in self.matrices:
            nn.init.orthogonal_(matrix, gain=0.02)
        if self.remainder is not None:
            nn.init.normal_(self.remainder, mean=0.0, std=0.02)

    def forward(self, values: torch.Tensor) -> torch.Tensor:
        output = values.new_zeros(values.shape)
        current = values
        for matrix in self.matrices:
            current = torch.tanh(F.linear(current, matrix))
            output = output + current
        if self.remainder is not None:
            flat_size = self.hidden_size * self.hidden_size
            indices = torch.arange(
                self.remainder.numel(), device=values.device
            ) % flat_size
            flat = values.new_zeros(flat_size).scatter_add(
                0,
                indices,
                self.remainder.to(values.dtype),
            )
            tail_matrix = flat.view(self.hidden_size, self.hidden_size)
            output = output + torch.tanh(F.linear(values, tail_matrix))
        return output


class MatrixStateKernel(nn.Module):
    """三种既有核的共同逐步接口，预测上下文严格读取更新前状态。"""

    def __init__(self, config: C12ModelConfig) -> None:
        super().__init__()
        self.heads = config.state_heads
        self.head_size = config.state_head_size
        self.hidden_size = config.hidden_size

    def _shape(self, values: torch.Tensor) -> torch.Tensor:
        return values.float().view(values.shape[0], self.heads, self.head_size)

    def _empty_state(self, values: torch.Tensor) -> torch.Tensor:
        return torch.zeros(
            values.shape[0],
            self.heads,
            self.head_size,
            self.head_size,
            device=values.device,
            dtype=torch.float32,
        )


class DeltaNetKernel(MatrixStateKernel):
    """Parallel DeltaNet 公式（3）的纯 PyTorch 顺序参考核。"""

    def __init__(self, config: C12ModelConfig) -> None:
        super().__init__(config)
        self.query = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.key = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.value = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.beta = nn.Linear(self.hidden_size, self.heads, bias=True)
        self.output = nn.Linear(self.hidden_size, self.hidden_size, bias=False)

    def forward(self, sequence: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        state = self._empty_state(sequence)
        contexts: list[torch.Tensor] = []
        for index in range(sequence.shape[1]):
            current = sequence[:, index]
            query = F.normalize(self._shape(self.query(current)), dim=-1)
            key = F.normalize(self._shape(self.key(current)), dim=-1)
            value = self._shape(self.value(current))
            beta = torch.sigmoid(self.beta(current).float()).view(-1, self.heads, 1)
            readout = torch.einsum("bhij,bhj->bhi", state, query)
            contexts.append(self.output(readout.flatten(1).to(current.dtype)))
            prediction = torch.einsum("bhij,bhj->bhi", state, key)
            residual = beta * (value - prediction)
            proposal = state + torch.einsum("bhi,bhj->bhij", residual, key)
            active = valid_mask[:, index].view(-1, 1, 1, 1)
            state = torch.where(active, proposal, state)
        return torch.stack(contexts, dim=1)


class GatedDeltaNetKernel(MatrixStateKernel):
    """Gated DeltaNet 公式（10）的纯 PyTorch 顺序参考核。"""

    def __init__(self, config: C12ModelConfig) -> None:
        super().__init__(config)
        self.query = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.key = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.value = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.alpha = nn.Linear(self.hidden_size, self.heads, bias=True)
        self.beta = nn.Linear(self.hidden_size, self.heads, bias=True)
        self.output = nn.Linear(self.hidden_size, self.hidden_size, bias=False)

    def forward(self, sequence: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        state = self._empty_state(sequence)
        contexts: list[torch.Tensor] = []
        for index in range(sequence.shape[1]):
            current = sequence[:, index]
            query = F.normalize(self._shape(self.query(current)), dim=-1)
            key = F.normalize(self._shape(self.key(current)), dim=-1)
            value = self._shape(self.value(current))
            alpha = torch.sigmoid(self.alpha(current).float()).view(-1, self.heads, 1, 1)
            beta = torch.sigmoid(self.beta(current).float()).view(-1, self.heads, 1)
            readout = torch.einsum("bhij,bhj->bhi", state, query)
            contexts.append(self.output(readout.flatten(1).to(current.dtype)))
            decayed = alpha * state
            prediction = torch.einsum("bhij,bhj->bhi", decayed, key)
            residual = beta * (value - prediction)
            proposal = decayed + torch.einsum("bhi,bhj->bhij", residual, key)
            active = valid_mask[:, index].view(-1, 1, 1, 1)
            state = torch.where(active, proposal, state)
        return torch.stack(contexts, dim=1)


class Rwkv7Kernel(MatrixStateKernel):
    """RWKV-7 式（15）至（19）状态演化的纯 PyTorch任务适配核。"""

    def __init__(self, config: C12ModelConfig) -> None:
        super().__init__(config)
        self.receptance = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.key = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.value = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.decay = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.learning_rate = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.gate = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.output = nn.Linear(self.hidden_size, self.hidden_size, bias=False)
        self.removal_scale = nn.Parameter(torch.ones(self.heads, self.head_size))
        self.replacement_rate = nn.Parameter(torch.full((self.heads, self.head_size), 0.5))
        self.bonus_scale = nn.Parameter(torch.zeros(self.heads, self.head_size))
        self.head_norm = nn.LayerNorm(self.head_size)

    def forward(self, sequence: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        state = self._empty_state(sequence)
        contexts: list[torch.Tensor] = []
        for index in range(sequence.shape[1]):
            current = sequence[:, index]
            receptance = self._shape(self.receptance(current))
            key = self._shape(self.key(current))
            value = self._shape(self.value(current))
            removal = F.normalize(key * self.removal_scale, dim=-1, eps=1e-12)
            rate = torch.sigmoid(self._shape(self.learning_rate(current)))
            replacement = key * (1.0 - self.replacement_rate + rate * self.replacement_rate)
            decay = torch.exp(
                -torch.exp(torch.tensor(-0.5, device=current.device))
                * torch.sigmoid(self._shape(self.decay(current)))
            )
            readout = torch.einsum("bhij,bhj->bhi", state, receptance)
            bonus = (receptance * key * self.bonus_scale).sum(dim=-1, keepdim=True) * value
            normalized = self.head_norm(readout + bonus)
            gated = torch.sigmoid(self._shape(self.gate(current))) * normalized
            contexts.append(self.output(gated.flatten(1).to(current.dtype)))
            decayed = state * decay.unsqueeze(-2)
            removed_value = torch.einsum("bhij,bhj->bhi", state, removal)
            proposal = decayed - torch.einsum(
                "bhi,bhj->bhij", removed_value, removal * rate
            ) + torch.einsum("bhi,bhj->bhij", value, replacement)
            active = valid_mask[:, index].view(-1, 1, 1, 1)
            state = torch.where(active, proposal, state)
        return torch.stack(contexts, dim=1)


class PreviousStateGru(nn.Module):
    """只暴露更新前隐藏状态的 GRU 文献强基线。"""

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        self.cell = nn.GRUCell(hidden_size, hidden_size)

    def forward(self, sequence: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        state = sequence.new_zeros(sequence.shape[0], sequence.shape[2])
        contexts: list[torch.Tensor] = []
        for index in range(sequence.shape[1]):
            contexts.append(state)
            proposal = self.cell(sequence[:, index], state)
            active = valid_mask[:, index].unsqueeze(-1)
            state = torch.where(active, proposal, state)
        return torch.stack(contexts, dim=1)


class PhaseAVariantModel(nn.Module):
    """共享融合分类头，只替换更新前状态上下文来源。"""

    def __init__(
        self,
        variant: str,
        config: C12ModelConfig,
        compensation_parameters: int = 0,
    ) -> None:
        super().__init__()
        if variant not in TRAINABLE_VARIANTS:
            raise C12ModelError(f"未知阶段 A 变体：{variant}")
        config.validate()
        self.variant = variant
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size * 2),
            nn.Linear(config.hidden_size * 2, config.hidden_size),
            nn.GELU(),
            nn.Linear(config.hidden_size, 1),
        )
        if variant == "K-DELTA":
            self.core: nn.Module | None = DeltaNetKernel(config)
        elif variant == "K-RWKV7":
            self.core = Rwkv7Kernel(config)
        elif variant == "K-GDELTA":
            self.core = GatedDeltaNetKernel(config)
        elif variant == "GRU":
            self.core = PreviousStateGru(config.hidden_size)
        else:
            self.core = None
        self.compensation = ActiveParameterCompensation(
            config.hidden_size,
            compensation_parameters,
        )

    def forward(self, sequence: torch.Tensor, valid_mask: torch.Tensor) -> torch.Tensor:
        if sequence.ndim != 3 or sequence.shape[:2] != valid_mask.shape:
            raise C12ModelError("阶段 A 表示与有效位掩码形状不一致")
        if self.core is None:
            context = sequence.new_zeros(sequence.shape)
        else:
            context = self.core(sequence, valid_mask)
        context = context + self.compensation(sequence)
        return self.classifier(torch.cat((sequence, context), dim=-1)).squeeze(-1)


class PhaseBVariantModel(nn.Module):
    """阶段 B 共享门控 Delta 承载器与参照感知检测头。"""

    def __init__(
        self,
        variant: str,
        config: C12ModelConfig,
        compensation_parameters: int = 0,
    ) -> None:
        super().__init__()
        if variant not in PHASE_B_VARIANTS:
            raise C12ModelError(f"未知阶段 B 变体：{variant}")
        config.validate()
        self.variant = variant
        self.core = GatedDeltaNetKernel(config)
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size * 3),
            nn.Linear(config.hidden_size * 3, config.hidden_size),
            nn.GELU(),
            nn.Linear(config.hidden_size, 1),
        )
        self.compensation = ActiveParameterCompensation(
            config.hidden_size,
            compensation_parameters,
        )

    def empty_state(self, current: torch.Tensor) -> torch.Tensor:
        """按当前批量创建六头完整矩阵状态。"""
        return self.core._empty_state(current)

    def predict_step(
        self,
        current: torch.Tensor,
        state: torch.Tensor,
        active_reference: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """只读取更新前状态产生当前预测和承载器上下文。"""
        query = F.normalize(self.core._shape(self.core.query(current)), dim=-1)
        readout = torch.einsum("bhij,bhj->bhi", state, query)
        context = self.core.output(readout.flatten(1).to(current.dtype))
        context = context + self.compensation(current)
        if active_reference.ndim == 1:
            active_reference = active_reference.unsqueeze(0).expand_as(current)
        if active_reference.shape != current.shape:
            raise C12ModelError("激活参照与当前表示形状不一致")
        features = torch.cat((current, context, current - active_reference), dim=-1)
        return self.classifier(features).squeeze(-1), context

    def propose_step(
        self,
        current: torch.Tensor,
        state: torch.Tensor,
    ) -> torch.Tensor:
        """门控 Delta 核只产生状态提议，不决定控制动作。"""
        key = F.normalize(self.core._shape(self.core.key(current)), dim=-1)
        value = self.core._shape(self.core.value(current))
        alpha = torch.sigmoid(self.core.alpha(current).float()).view(
            -1, self.core.heads, 1, 1
        )
        beta = torch.sigmoid(self.core.beta(current).float()).view(
            -1, self.core.heads, 1
        )
        decayed = alpha * state
        prediction = torch.einsum("bhij,bhj->bhi", decayed, key)
        residual = beta * (value - prediction)
        return decayed + torch.einsum("bhi,bhj->bhij", residual, key)

    def forward(
        self,
        sequence: torch.Tensor,
        valid_mask: torch.Tensor,
        active_reference: torch.Tensor,
    ) -> torch.Tensor:
        """源侧训练使用未经目标适应的标准门控 Delta 状态。"""
        if sequence.ndim != 3 or sequence.shape[:2] != valid_mask.shape:
            raise C12ModelError("阶段 B 表示与有效位掩码形状不一致")
        if active_reference.ndim != 1 or active_reference.shape[0] != sequence.shape[2]:
            raise C12ModelError("源锚必须是一维隐藏表示")
        state = self.empty_state(sequence)
        logits: list[torch.Tensor] = []
        for index in range(sequence.shape[1]):
            current = sequence[:, index]
            prediction, _ = self.predict_step(current, state, active_reference)
            logits.append(prediction)
            proposal = self.propose_step(current, state)
            active = valid_mask[:, index].view(-1, 1, 1, 1)
            state = torch.where(active, proposal, state)
        return torch.stack(logits, dim=1)


def trainable_parameter_count(model: nn.Module) -> int:
    """统计真实参与反向传播的参数。"""
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def build_parameter_matched_models(
    config: C12ModelConfig,
    initialization_seed: int = 42,
) -> tuple[dict[str, PhaseAVariantModel], dict[str, int], dict[str, int]]:
    """把全部阶段 A 与 GRU 的可训练参数精确补齐到同一数目。"""
    raw_models: dict[str, PhaseAVariantModel] = {}
    for variant in TRAINABLE_VARIANTS:
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(initialization_seed)
            raw_models[variant] = PhaseAVariantModel(variant, config)
    raw_counts = {
        variant: trainable_parameter_count(model)
        for variant, model in raw_models.items()
    }
    target = max(raw_counts.values())
    models: dict[str, PhaseAVariantModel] = {}
    for variant in TRAINABLE_VARIANTS:
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(initialization_seed)
            models[variant] = PhaseAVariantModel(
                variant,
                config,
                compensation_parameters=target - raw_counts[variant],
            )
    matched_counts = {
        variant: trainable_parameter_count(model)
        for variant, model in models.items()
    }
    if min(matched_counts.values()) <= 0:
        raise C12ModelError("参数匹配后模型不得为空")
    ratio = max(matched_counts.values()) / min(matched_counts.values())
    if ratio > 1.01:
        raise C12ModelError(f"可训练参数差异超过 1%：{matched_counts}")
    return models, raw_counts, matched_counts


def build_phase_b_parameter_matched_models(
    config: C12ModelConfig,
    initialization_seed: int = 42,
) -> tuple[dict[str, PhaseBVariantModel], dict[str, int], dict[str, int]]:
    """把阶段 B 三变体匹配到阶段 A 的冻结可训练参数预算。"""
    _, _, phase_a_counts = build_parameter_matched_models(config, initialization_seed)
    target = max(phase_a_counts.values())
    raw_models: dict[str, PhaseBVariantModel] = {}
    for variant in PHASE_B_VARIANTS:
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(initialization_seed)
            raw_models[variant] = PhaseBVariantModel(variant, config)
    raw_counts = {
        variant: trainable_parameter_count(model)
        for variant, model in raw_models.items()
    }
    if max(raw_counts.values()) > target:
        raise C12ModelError(
            f"阶段 B 原始参数超过阶段 A 冻结预算：目标={target}，实际={raw_counts}"
        )
    models: dict[str, PhaseBVariantModel] = {}
    for variant in PHASE_B_VARIANTS:
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(initialization_seed)
            models[variant] = PhaseBVariantModel(
                variant,
                config,
                compensation_parameters=target - raw_counts[variant],
            )
    matched_counts = {
        variant: trainable_parameter_count(model)
        for variant, model in models.items()
    }
    if set(matched_counts.values()) != {target}:
        raise C12ModelError(f"阶段 B 参数未精确匹配：{matched_counts}")
    return models, raw_counts, matched_counts


def kernel_equivalence_boundaries() -> dict[str, dict[str, object]]:
    """写入运行收据的官方等价边界，禁止误称官方结果。"""
    return {
        "K-DELTA": {
            "status": "既有核的纯 PyTorch 顺序参考实现",
            "source_commit": DELTANET_SOURCE_COMMIT,
            "equivalent": "归一化键、旧值读出、beta 加权预测残差和外积写回",
            "not_equivalent": "未调用 FLA 并行 Triton/CUDA 算子，不复现语言模型短卷积与完整层封装",
            "official_result": False,
        },
        "K-RWKV7": {
            "status": "既有核的纯 PyTorch 任务适配参考实现",
            "source_commit": RWKV7_SOURCE_COMMIT,
            "equivalent": "逐通道衰减、归一化移除键、上下文学习率、独立替换键和值外积的矩阵状态方向",
            "not_equivalent": "不调用官方 BF16 融合核，不复现语言模型令牌移位、跨层值残差、通道混合和专用初始化",
            "official_result": False,
        },
        "K-GDELTA": {
            "status": "既有核的纯 PyTorch 顺序参考实现",
            "source_commit": GATED_DELTANET_SOURCE_COMMIT,
            "equivalent": "数据依赖全局遗忘后执行 beta 加权 Delta 预测残差写回",
            "not_equivalent": "未调用 NVlabs 官方块算子，不复现语言模型短卷积和完整层封装",
            "official_result": False,
        },
    }
