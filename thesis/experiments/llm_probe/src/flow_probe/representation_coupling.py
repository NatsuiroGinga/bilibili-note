"""把预测物理状态显式注入生成词表投影前的隐藏表示。"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import torch
from torch.nn import functional as F

VARIANTS = ("B0", "B1")


class RepresentationCouplingError(ValueError):
    """物理表征耦合接口或张量形状不满足实验契约。"""


def normalize_variant(value: str) -> str:
    """只接受任务十六冻结的 B0 与 B1。"""
    variant = str(value).upper()
    if variant not in VARIANTS:
        raise RepresentationCouplingError(f"未知物理表征耦合变体：{value}")
    return variant


def prompt_anchor_positions(labels: torch.Tensor) -> torch.Tensor:
    """返回每条样本首个监督令牌之前的提示末令牌位置。"""
    if labels.ndim != 2:
        raise RepresentationCouplingError("生成标签必须采用[批量, 序列]二维形状")
    supervised = labels.ne(-100)
    if not bool(supervised.any(dim=1).all().item()):
        raise RepresentationCouplingError("每条生成样本都必须包含监督完成文本")
    first_supervised = supervised.to(dtype=torch.int64).argmax(dim=1)
    if bool(first_supervised.eq(0).any().item()):
        raise RepresentationCouplingError("监督完成文本前必须至少保留一个提示令牌")
    return first_supervised - 1


def select_prompt_anchor_hidden(hidden_states: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    """从不含完成文本信息的提示末令牌取得状态头输入。"""
    if hidden_states.ndim != 3 or labels.shape != hidden_states.shape[:2]:
        raise RepresentationCouplingError("隐藏状态与生成标签形状不匹配")
    positions = prompt_anchor_positions(labels)
    rows = torch.arange(hidden_states.shape[0], device=hidden_states.device)
    return hidden_states[rows, positions]


def supervised_prediction_mask(labels: torch.Tensor) -> torch.Tensor:
    """标记其下一令牌由因果语言模型监督的隐藏位置。"""
    if labels.ndim != 2:
        raise RepresentationCouplingError("生成标签必须采用[批量, 序列]二维形状")
    mask = torch.zeros_like(labels, dtype=torch.bool)
    mask[:, :-1] = labels[:, 1:].ne(-100)
    if not bool(mask.any(dim=1).all().item()):
        raise RepresentationCouplingError("每条样本至少需要一个受监督的预测位置")
    return mask


def causal_lm_loss(logits: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
    """计算与标准因果语言模型一致的移位交叉熵。"""
    if logits.ndim != 3 or labels.shape != logits.shape[:2]:
        raise RepresentationCouplingError("词表输出与标签形状不匹配")
    return F.cross_entropy(
        logits[:, :-1].float().reshape(-1, logits.shape[-1]),
        labels[:, 1:].reshape(-1),
        ignore_index=-100,
    )


def decoder_last_hidden(
    model: object,
    *,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
) -> torch.Tensor:
    """绕过词表投影，读取带 LoRA 解码器的最终隐藏状态。"""
    get_base_model = getattr(model, "get_base_model", None)
    base_model = get_base_model() if callable(get_base_model) else model
    decoder = getattr(base_model, "model", None)
    if decoder is None or not callable(decoder):
        raise RepresentationCouplingError("模型未暴露可调用的因果解码器接口")
    outputs = decoder(
        input_ids=input_ids,
        attention_mask=attention_mask,
        use_cache=False,
        return_dict=True,
    )
    hidden = getattr(outputs, "last_hidden_state", None)
    if not isinstance(hidden, torch.Tensor) or hidden.ndim != 3:
        raise RepresentationCouplingError("因果解码器未返回三维最终隐藏状态")
    return hidden


def output_embeddings(model: object) -> torch.nn.Module:
    """取得原因果语言模型的词表输出层。"""
    getter = getattr(model, "get_output_embeddings", None)
    layer = getter() if callable(getter) else None
    if layer is None:
        get_base_model = getattr(model, "get_base_model", None)
        base_model = get_base_model() if callable(get_base_model) else model
        getter = getattr(base_model, "get_output_embeddings", None)
        layer = getter() if callable(getter) else None
    if not isinstance(layer, torch.nn.Module):
        raise RepresentationCouplingError("模型未暴露词表输出层")
    return layer


@dataclass(frozen=True)
class CouplingResult:
    """一次物理状态门控融合的张量结果。"""

    hidden_states: torch.Tensor
    reliability: torch.Tensor
    physical_embedding: torch.Tensor


class PhysicalRepresentationCoupling(torch.nn.Module):
    """在词表投影前注入五维预测物理状态。"""

    def __init__(self, hidden_size: int, *, state_size: int = 5, variant: str) -> None:
        super().__init__()
        if hidden_size <= 0 or state_size <= 0:
            raise RepresentationCouplingError("隐藏维度和状态维度必须大于零")
        self.hidden_size = int(hidden_size)
        self.state_size = int(state_size)
        self.variant = normalize_variant(variant)
        self.physical_projection = torch.nn.Parameter(
            torch.empty(self.hidden_size, self.state_size, dtype=torch.float32)
        )
        torch.nn.init.orthogonal_(self.physical_projection)
        self.reliability_gate = torch.nn.Linear(self.state_size, 1, dtype=torch.float32)
        torch.nn.init.zeros_(self.reliability_gate.weight)
        torch.nn.init.zeros_(self.reliability_gate.bias)

    def effective_projection(self) -> torch.Tensor:
        """B1 以薄 QR 保持投影矩阵列正交，B0 返回普通矩阵。"""
        projection = self.physical_projection.float()
        if self.variant == "B1":
            orthogonal, upper = torch.linalg.qr(projection, mode="reduced")
            diagonal = torch.diagonal(upper)
            signs = torch.where(diagonal < 0, -torch.ones_like(diagonal), torch.ones_like(diagonal))
            projection = orthogonal * signs.unsqueeze(0)
        return projection

    def orthogonality_error(self) -> torch.Tensor:
        """返回有效投影矩阵偏离 Stiefel 流形的 Frobenius 范数。"""
        projection = self.effective_projection()
        identity = torch.eye(self.state_size, device=projection.device, dtype=projection.dtype)
        return torch.linalg.matrix_norm(projection.transpose(0, 1) @ projection - identity)

    def forward(
        self,
        hidden_states: torch.Tensor,
        predicted_state: torch.Tensor,
        *,
        token_mask: torch.Tensor | None = None,
    ) -> CouplingResult:
        if hidden_states.ndim != 3 or hidden_states.shape[-1] != self.hidden_size:
            raise RepresentationCouplingError("待融合隐藏状态形状不合法")
        if predicted_state.shape != (hidden_states.shape[0], self.state_size):
            raise RepresentationCouplingError("预测状态必须采用[批量, 5]形状")
        if not bool(torch.isfinite(predicted_state).all().item()):
            raise RepresentationCouplingError("预测状态包含非有限数值")
        if bool(predicted_state.lt(0).any().item()):
            raise RepresentationCouplingError("预测队列状态不得为负")
        normalized_state = torch.log1p(predicted_state.float())
        projection = self.effective_projection()
        physical_embedding = normalized_state @ projection.transpose(0, 1)
        physical_embedding = physical_embedding / math.sqrt(self.state_size)
        reliability = torch.sigmoid(self.reliability_gate(normalized_state))
        injection = reliability * physical_embedding
        if token_mask is not None:
            if token_mask.shape != hidden_states.shape[:2]:
                raise RepresentationCouplingError("注入掩码形状必须匹配隐藏状态前两维")
            injection = injection[:, None, :] * token_mask[:, :, None].to(injection.dtype)
        else:
            injection = injection[:, None, :]
        fused = hidden_states + injection.to(dtype=hidden_states.dtype)
        return CouplingResult(
            hidden_states=fused,
            reliability=reliability,
            physical_embedding=physical_embedding,
        )


@dataclass(frozen=True)
class CoupledGenerationOutput:
    """显式物理耦合生成前向的完整诊断输出。"""

    loss: torch.Tensor
    logits: torch.Tensor
    predicted_state: torch.Tensor
    reliability: torch.Tensor
    base_hidden_states: torch.Tensor
    prediction_mask: torch.Tensor


def coupled_generation_forward(
    model: object,
    state_head: torch.nn.Module,
    coupling: PhysicalRepresentationCoupling,
    batch: Mapping[str, torch.Tensor],
) -> CoupledGenerationOutput:
    """执行单次因果安全的训练或验证前向。"""
    required = {"input_ids", "attention_mask", "labels"}
    missing = sorted(required.difference(batch))
    if missing:
        raise RepresentationCouplingError("生成批次缺少字段：" + ", ".join(missing))
    hidden = decoder_last_hidden(
        model,
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
    )
    prompt_hidden = select_prompt_anchor_hidden(hidden, batch["labels"])
    predicted_state = state_head(prompt_hidden)
    prediction_mask = supervised_prediction_mask(batch["labels"])
    coupled = coupling(hidden, predicted_state, token_mask=prediction_mask)
    logits = output_embeddings(model)(coupled.hidden_states).float()
    return CoupledGenerationOutput(
        loss=causal_lm_loss(logits, batch["labels"]),
        logits=logits,
        predicted_state=predicted_state,
        reliability=coupled.reliability,
        base_hidden_states=hidden,
        prediction_mask=prediction_mask,
    )


@torch.no_grad()
def perturbed_supervised_logit_delta(
    model: object,
    coupling: PhysicalRepresentationCoupling,
    output: CoupledGenerationOutput,
    *,
    delta: float = 0.5,
) -> float:
    """保持语言隐藏状态不变，仅扰动状态并测量监督位置输出变化。"""
    if not math.isfinite(delta) or delta <= 0:
        raise RepresentationCouplingError("状态扰动幅度必须为有限正数")
    first_positions = output.prediction_mask.to(dtype=torch.int64).argmax(dim=1)
    rows = torch.arange(output.base_hidden_states.shape[0], device=first_positions.device)
    selected_hidden = output.base_hidden_states.detach()[rows, first_positions][:, None, :]
    perturbed_state = output.predicted_state.detach().clone()
    perturbed_state[:, 0] = perturbed_state[:, 0] + delta
    perturbed = coupling(
        selected_hidden,
        perturbed_state,
        token_mask=torch.ones(
            (selected_hidden.shape[0], 1), dtype=torch.bool, device=selected_hidden.device
        ),
    )
    perturbed_logits = output_embeddings(model)(perturbed.hidden_states[:, 0]).float()
    reference_logits = output.logits.detach()[rows, first_positions]
    return float((perturbed_logits - reference_logits).abs().max().item())


@dataclass(frozen=True)
class CoupledNextTokenOutput:
    """不依赖队列真值的下一令牌推理结果。"""

    logits: torch.Tensor
    predicted_state: torch.Tensor
    reliability: torch.Tensor


def coupled_next_token_forward(
    model: object,
    state_head: torch.nn.Module,
    coupling: PhysicalRepresentationCoupling,
    *,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    predicted_state: torch.Tensor | None = None,
) -> CoupledNextTokenOutput:
    """仅凭真实数据提示计算状态、可靠性门和下一令牌输出。"""
    hidden = decoder_last_hidden(
        model,
        input_ids=input_ids,
        attention_mask=attention_mask,
    )
    if attention_mask.shape != hidden.shape[:2]:
        raise RepresentationCouplingError("推理注意力掩码与隐藏状态形状不匹配")
    valid = attention_mask.bool()
    if not bool(valid.any(dim=1).all().item()):
        raise RepresentationCouplingError("每条推理输入至少需要一个有效令牌")
    positions = torch.arange(hidden.shape[1], device=hidden.device)
    last_positions = positions.expand_as(valid).masked_fill(~valid, -1).max(dim=1).values
    rows = torch.arange(hidden.shape[0], device=hidden.device)
    last_hidden = hidden[rows, last_positions][:, None, :]
    state = state_head(last_hidden[:, 0]) if predicted_state is None else predicted_state
    coupled = coupling(last_hidden, state)
    logits = output_embeddings(model)(coupled.hidden_states[:, 0]).float()
    return CoupledNextTokenOutput(
        logits=logits, predicted_state=state, reliability=coupled.reliability
    )
