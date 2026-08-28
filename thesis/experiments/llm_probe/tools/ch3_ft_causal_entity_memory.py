# -*- coding: utf-8 -*-
"""机制一（因果实体记忆交叉注意力）：记忆状态容器与交叉注意力模块。

只含 ``EntityMemoryState`` 与 ``CausalEntityMemoryAttention`` 两个类，不含训练循环、
调度或配置解析——这些由 ``ch3_ft_c00_dual_selection.py``（任务 3）负责。

依据：``.Codex/docs/RWKV/2026-08-28-因果实体记忆交叉注意力与低误报实体排序/
机制设计与实验计划.md`` 第 4.1～4.4 节。

- **严格过去状态**（4.1 节）：槽 0 为跨片段 Welford 在线均值，槽 1..R-1 为最近表示的
  有界队列；预测完成后才写回（``write`` 由调用方在完整流预测与告警之后调用）。
- **交叉注意力**（4.2 节）：当前 ``[CLS]`` 单向查询严格过去记忆，标量门控残差注入。
  ``z1=0`` 由调用方旁路（本模块从不构造、不含开关），``z1=1`` 时才调用本模块；
  模块自身对"无历史"逐行退化为恒等（``c=0`` 时 ``h'=h`` 逐位相等），不对全掩码
  行做 softmax。
- **数值稳定**（4.4 节）：状态、注意力 logits、softmax、门与归约使用 FP32；
  经 ``neural_precision_runtime.fp32_island`` 接入，与本仓库既有注意力实现
  （``ch3_ft_transformer_field_token_protocol_a.MultiheadAttention``）同一精度合同，
  不自建第二套精度实现。

参数量闭式核验（第 4.5 节，``d=192``）：四个 ``d×d`` 投影＋偏置
（``W_Q``/``W_K``/``W_V``/``W_out``）、标量门 ``Linear(2d,1)``、两处
``LayerNorm(d)``、``R×d`` 角色嵌入。``R=8`` 时闭式与实测均为 ``150,913``，
占裸 FT ``924,283`` 参数的 ``16.33%``，与设计规约表格逐格核验一致
（``R∈{2,4,8,16}`` 均已交叉验证，见 ``causal_entity_memory_parameter_count``）。

按仓库既有惯例（对照 ``ch3_ft_transformer_field_token_protocol_a.py`` 顶部注释），
本文件在模块顶层直接导入 torch——因为本文件的唯一职责就是提供 torch 模块，
没有需要保持"无 torch 也能跑"的 ``--validate-config`` 式入口。消费方
（``ch3_ft_c00_dual_selection.py``）若要保持配置校验路径无 torch 依赖，须把本模块
的导入延迟到真正构造模型的函数内部，不得放在其模块顶层导入列表——这一约束在
任务 3 中落实。
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import torch
from torch import nn

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import neural_precision_runtime as precision  # noqa: E402  （同目录模块，需先插入 sys.path）


def causal_entity_memory_parameter_count(width: int, slots: int) -> int:
    """机制一交叉注意力可训练参数量闭式：``4(d²+d) + (2d+1) + 2·2d + R·d``。

    四项依次对应：``W_Q``/``W_K``/``W_V``/``W_out`` 四个 ``Linear(d,d)``（含偏置）、
    标量门 ``Linear(2d,1)``（含偏置）、``norm_query``/``norm_memory`` 两处
    ``LayerNorm(d)``（权重+偏置各 ``d``）、``R×d`` 角色嵌入。``d=192`` 时：
    ``R=2→149,761``、``R=4→150,145``、``R=8→150,913``、``R=16→152,449``，
    与设计规约第 4.5 节表格逐格一致。
    """
    projections = 4 * (width * width + width)
    gate = 2 * width + 1
    norms = 2 * (2 * width)
    role_embedding = slots * width
    return projections + gate + norms + role_embedding


class EntityMemoryState:
    """按实体与数据角色隔离的严格过去状态；先读后写，状态本身不参与反向传播。

    形状约定（``d`` = 记忆宽度，须与 FT 主干 ``[CLS]`` 表示同宽；``R`` = 槽数）：

    - ``mean``：``(entity_count, d)``，槽 0，Welford 在线均值，FP32。
    - ``queue``：``(entity_count, R-1, d)``，槽 1..R-1，最近表示的有界队列，FP32。
    - ``count``：``(entity_count,)``，Welford 计数，int64。
    - ``filled``：``(entity_count,)``，队列已填充条数（上限 ``R-1``），int64。

    实体键只作状态索引，不作为数值特征进入模型输入（对应设计规约第 3.1 节
    ``entity_id`` 的硬约束）。
    """

    def __init__(
        self,
        entity_count: int,
        slots: int,
        width: int,
        *,
        device: Any = None,
        role_of_entity: torch.Tensor | None = None,
    ) -> None:
        if entity_count <= 0:
            raise ValueError(f"entity_count 必须为正，实际 {entity_count}")
        if slots < 1:
            raise ValueError(f"slots 必须 ≥1，实际 {slots}")
        if width <= 0:
            raise ValueError(f"width 必须为正，实际 {width}")
        # 设备无关：不硬编码 .cuda()/.mps()，由调用方通过 device 传入目标设备；
        # 未指定时落在 CPU，供只做形状/逻辑核验的场景使用。
        target_device = torch.device(device) if device is not None else torch.device("cpu")
        self.entity_count = entity_count
        self.slots = slots
        self.width = width
        self.device = target_device
        self.mean = torch.zeros(entity_count, width, dtype=torch.float32, device=target_device)
        self.queue = torch.zeros(entity_count, slots - 1, width, dtype=torch.float32, device=target_device)
        self.count = torch.zeros(entity_count, dtype=torch.int64, device=target_device)
        self.filled = torch.zeros(entity_count, dtype=torch.int64, device=target_device)
        # role_of_entity：(entity_count,) 逐实体角色，供 reset_role 按角色清零；
        # 未提供时 reset_role 会显式报错，不静默跳过。
        self.role_of_entity = (
            role_of_entity.to(device=target_device) if role_of_entity is not None else None
        )

    def read(self, rows: torch.Tensor) -> torch.Tensor:
        """按实体行取严格过去记忆，返回 ``(B, R, d)``：槽 0 均值＋槽 1..R-1 队列。"""
        mean_slot = self.mean[rows].unsqueeze(1)  # (B, 1, d)
        queue_slots = self.queue[rows]  # (B, R-1, d)
        return torch.cat([mean_slot, queue_slots], dim=1)  # (B, R, d)

    def valid(self, rows: torch.Tensor) -> torch.Tensor:
        """按实体行取槽有效掩码，返回 ``(B, R)`` bool。

        均值槽在 ``count>0`` 时有效；队列槽按"最近写入靠右"的约定，只有队列最右侧
        ``filled`` 个位置有效（左侧是尚未写入的零填充位）。
        """
        count = self.count[rows]  # (B,)
        filled = self.filled[rows]  # (B,)
        mean_valid = (count > 0).unsqueeze(1)  # (B, 1)
        queue_width = self.slots - 1
        if queue_width == 0:
            return mean_valid
        position = torch.arange(queue_width, device=self.device).unsqueeze(0)  # (1, R-1)
        queue_valid = position >= (queue_width - filled.unsqueeze(1))  # (B, R-1)
        return torch.cat([mean_valid, queue_valid], dim=1)  # (B, R)

    def write(self, rows: torch.Tensor, summary: torch.Tensor) -> None:
        """预测与告警完成后才调用。Welford 在线均值，队列取最近 ``R-1`` 条。

        ``summary``：``(B, d)``，调用方须已按 spec 4.1 节做 ``SG(LN(h'))``（严格
        过去更新不得反传到本次前向）；本方法内部显式 ``detach`` 作为二次保险与
        自文档化——即便调用方遗漏，状态张量本身也从不 ``requires_grad``，因此
        原本就不会产生梯度，这里的 ``detach`` 只是让该不变量在代码里可见。

        ``rows`` 内若出现重复实体行，``self.mean[rows] += ...`` 这类花式索引写入
        对重复下标不会逐个累积（PyTorch/NumPy 的已知行为：等价于先聚集旧值再整体
        写回，后写覆盖先写），会静默丢失更新，因此显式拒绝。
        """
        if rows.numel() == 0:
            return
        if rows.numel() != torch.unique(rows).numel():
            raise RuntimeError("同一批次内出现重复实体行，Welford 状态更新会静默丢失更新")
        summary = summary.detach().to(self.mean.dtype)
        self.count[rows] += 1
        delta = summary - self.mean[rows]
        self.mean[rows] += delta / self.count[rows].to(self.mean.dtype).unsqueeze(1)
        if self.slots > 1:
            self.queue[rows] = torch.cat([self.queue[rows][:, 1:], summary.unsqueeze(1)], dim=1)
            self.filled[rows] = torch.clamp(self.filled[rows] + 1, max=self.slots - 1)

    def reset_role(self, role_id: int) -> None:
        """把属于指定角色的全部实体状态清零。

        用于每个训练轮起点或每次验证前的干净重放，保证状态严格从
        ``is_entity_start`` 开始累积，不携带跨轮次的历史。角色边界由构造函数的
        ``role_of_entity`` 给出；未配置时报错而不是静默跳过。
        """
        if self.role_of_entity is None:
            raise RuntimeError("EntityMemoryState 未配置 role_of_entity，无法按角色重置")
        selected = self.role_of_entity == role_id
        self.mean[selected] = 0.0
        self.queue[selected] = 0.0
        self.count[selected] = 0
        self.filled[selected] = 0

    def reset_all(self) -> None:
        """把全部实体状态清零，不区分角色；供没有角色隔离需求的场景使用。"""
        self.mean.zero_()
        self.queue.zero_()
        self.count.zero_()
        self.filled.zero_()


class CausalEntityMemoryAttention(nn.Module):
    """当前 ``[CLS]`` 单向查询严格过去记忆；无历史时返回零上下文，不做全掩码 softmax。

    ``z1=0`` 由调用方旁路（本模块不含开关，不在此处判断是否启用机制一）；
    调用方只在 ``z1=1`` 时才构造记忆并调用本模块。当某一行 ``memory_valid`` 全假
    （该实体无严格过去可读）时，该行的上下文直接置零，不参与 softmax——这既避免
    全 ``-inf`` softmax 产生 NaN，也让该行的门控残差退化为恒等（``c=0`` ⇒
    ``h'=h`` 逐位相等，与 ``z1=0`` 的裸 FT 路径同构）。
    """

    def __init__(self, width: int, heads: int, slots: int) -> None:
        super().__init__()
        if width % heads != 0:
            raise ValueError(f"宽度 {width} 不能被头数 {heads} 整除，注意力无法按 d//heads 切头")
        if slots < 1:
            raise ValueError(f"slots 必须 ≥1，实际 {slots}")
        self.width = width
        self.heads = heads
        self.slots = slots
        self.head_dim = width // heads

        self.norm_query = nn.LayerNorm(width)
        self.norm_memory = nn.LayerNorm(width)
        self.w_q = nn.Linear(width, width)
        self.w_k = nn.Linear(width, width)
        self.w_v = nn.Linear(width, width)
        self.w_out = nn.Linear(width, width)
        self.gate = nn.Linear(2 * width, 1)
        # R×d 角色嵌入，只用于区分长期均值槽与最近性槽（4.2 节 P_R）；零初始化，
        # 不引入未经证据登记的初始化幅度，完全由训练塑形。
        self.role_embedding = nn.Parameter(torch.zeros(slots, width))

        # 显式初始化：偏置清零，权重沿用 nn.Linear 的默认 Kaiming 均匀初始化——
        # 与本仓库 FT-Transformer 主干在 initialization="kaiming" 分支下的做法
        # 一致（只清零偏置，不改动权重的 PyTorch 默认初始化）。
        for module in (self.w_q, self.w_k, self.w_v, self.w_out, self.gate):
            nn.init.zeros_(module.bias)

        self._last_gate: torch.Tensor | None = None

    def gate_statistics(self) -> dict[str, float]:
        """返回最近一次 ``forward`` 调用的门统计，供训练诊断埋点使用。

        ``forward`` 之前调用会报错；数值来自 FP32 门（未做梯度关联的只读统计）。
        """
        if self._last_gate is None:
            raise RuntimeError("尚未调用 forward，没有门统计可读")
        gate = self._last_gate
        probability = gate.clamp(1e-6, 1.0 - 1e-6)
        entropy = -(probability * probability.log() + (1.0 - probability) * (1.0 - probability).log())
        return {
            "gate_mean": float(gate.mean().item()),
            "gate_entropy_mean": float(entropy.mean().item()),
        }

    def forward(
        self, cls_hidden: torch.Tensor, memory: torch.Tensor, memory_valid: torch.Tensor
    ) -> torch.Tensor:
        """``h'=h+g·c``；``c`` 只在存在有效历史的行上由交叉注意力给出。

        形状：
          cls_hidden:   ``(B, d)``      当前流最终 [CLS] 表示（骨干末块输出）
          memory:       ``(B, R, d)``   EntityMemoryState.read 的输出
          memory_valid: ``(B, R)``      EntityMemoryState.valid 的输出，bool
          返回:         ``(B, d)``
        """
        if cls_hidden.ndim != 2 or cls_hidden.shape[-1] != self.width:
            raise RuntimeError(f"cls_hidden 必须是 B×{self.width}，实际 {tuple(cls_hidden.shape)}")
        batch = cls_hidden.shape[0]
        if tuple(memory.shape) != (batch, self.slots, self.width):
            raise RuntimeError(
                f"memory 必须是 {batch}×{self.slots}×{self.width}，实际 {tuple(memory.shape)}"
            )
        if tuple(memory_valid.shape) != (batch, self.slots):
            raise RuntimeError(f"memory_valid 必须是 {batch}×{self.slots}，实际 {tuple(memory_valid.shape)}")

        device_type = cls_hidden.device.type
        has_history = memory_valid.any(dim=1)  # (B,)
        context = torch.zeros_like(cls_hidden)  # (B, d)，无历史行保持精确零

        if bool(has_history.any()):
            active_hidden = cls_hidden[has_history]  # (n, d)
            active_memory = memory[has_history]  # (n, R, d)
            active_valid = memory_valid[has_history]  # (n, R)

            # 投影本身允许环境精度（CUDA 下可能是 BF16 autocast）；
            # logits、softmax 与加权归约随后显式进 FP32 岛。
            query_input = self.norm_query(active_hidden)  # (n, d)
            key_value_input = self.norm_memory(active_memory) + self.role_embedding  # (n, R, d)
            query = self.w_q(query_input).view(-1, self.heads, self.head_dim)  # (n, H, d_h)
            key = self.w_k(key_value_input).view(-1, self.slots, self.heads, self.head_dim)  # (n, R, H, d_h)
            value = self.w_v(key_value_input).view(-1, self.slots, self.heads, self.head_dim)  # (n, R, H, d_h)

            with precision.fp32_island(
                query, key, value, device_type=device_type, torch_module=torch
            ) as (query32, key32, value32):
                scores = torch.einsum("nhd,nshd->nhs", query32, key32) / math.sqrt(self.head_dim)  # (n, H, R)
                scores = scores.masked_fill(~active_valid.unsqueeze(1), float("-inf"))
                scores = scores - scores.max(dim=-1, keepdim=True).values  # 先减行最大值，4.4 节数值稳定
                weights = torch.softmax(scores, dim=-1)  # (n, H, R)
                merged32 = torch.einsum("nhs,nshd->nhd", weights, value32).reshape(-1, self.width)  # (n, d)

            active_context = self.w_out(merged32.to(cls_hidden.dtype))  # 输出投影回到环境精度
            context[has_history] = active_context.to(context.dtype)

        gate_input = torch.cat([self.norm_query(cls_hidden), context], dim=-1)  # (B, 2d)
        with precision.fp32_island(gate_input, device_type=device_type, torch_module=torch) as (gate_input32,):
            gate = torch.sigmoid(self.gate(gate_input32))  # (B, 1) FP32
        self._last_gate = gate.detach()
        gate = gate.to(cls_hidden.dtype)

        return cls_hidden + gate * context
