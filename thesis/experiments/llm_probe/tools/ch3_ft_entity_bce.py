# -*- coding: utf-8 -*-
"""四格消融共同底座：实体级 BCE 损失（不接入宿主，独立模块）。

背景（`.claude/sdd/2026-09-03-实体级BCE共同底座实施计划/task-1-brief.md`）：现状
四格消融中，机制一（ETA 尾部聚合）只在“开了机制二（BER 排序损失）”的那两格才有
训练梯度通道，交互项因此没有判别力。修法是给全部四格补一个共同底座——实体级
BCE：把逐流 logits 聚合成实体分数后做二分类交叉熵，使 ETA 的聚合算子在这一层
也持续产生梯度，不依赖机制二是否开启。

聚合复用（不重新实现）：本模块的唯一聚合来源是
``ch3_ft_entity_ranking_loss.tail_aggregate``（该文件第 150-244 行，"实体内尾部
聚合的**唯一算术实现**"，含 top-k 均值退化为 max 的自检
``assert_tail_aggregation_degenerates_to_max``、并列取值的 argsort 稳定序核验，
以及 α=0.5 的完整冻结依据）。本模块只做 (a) 参数校验、(b) FP32 精度纪律、
(c) 空实体掩蔽、(d) 二分类损失，不重写任何聚合算术，避免两份实现漂移。

α 冻结依据（照录，不重新论证）：`.Codex/docs/RWKV/2026-09-01-尾部聚合参数裁决/
裁决报告.md` 已把 α 冻结为 0.5（两条结构约束唯一确定），机制来源见
`.Codex/docs/RWKV/2026-09-01-BER同框架机制一可行性/调研报告.md` 第 2.4、2.5 节。
本模块不引入任何新数值魔法数字——``alpha`` 只接受该已冻结值，不接受按本次任务
重新选择的其他值；聚合模式到 ``tail_aggregate`` 的 ``alpha`` 参数映射关系
（"maximum" → None，即 k≡1 退化为 max；"tail_mean" → 0.5，即 ETA）直接复用
``tail_aggregate`` 文档字符串里已经写明的语义，不新增独立公式。

FP32 纪律：仓库合同要求阈值状态、CVaR 归约、梯度范数与投影须 FP32
（`thesis/experiments/llm_probe/AGENTS.md`「实现验证与真实运行」一节，及
``ch3_ft_entity_ranking_loss.py`` 对 ``tail_aggregation_receipt``/
``nonargmax_grad_energy_share`` 的"先 cpu 后 double"处置同一动机）。
``tail_aggregate`` 本身按调用方传入的 dtype 计算，不强制精度，因此本模块在调用
前把 ``flow_logits`` 显式转 FP32；BCE 计算同样在 FP32 下进行。

第三方 API 核验记录（本机 PyTorch 2.12.0，2026-09-03 经
``npx ctx7@latest docs /websites/pytorch_2_12`` 核对，与本机安装版本一致）：
- ``torch.nn.functional.binary_cross_entropy_with_logits(input, target, weight=None,
  size_average=None, reduce=None, reduction='mean', pos_weight=None)``：官方签名
  确认 ``reduction`` 是关键字参数，取值 ``'none'|'mean'|'sum'``，默认 ``'mean'``；
  本模块显式传 ``reduction="none"`` 后自行按"有效实体"掩码取均值，不用默认值，
  因为默认的全局均值会把空实体的零分数一并计入分母。

本模块不接入宿主 ``ch3_ft_c00_dual_selection.py``，不读取目标年（LSPR24）任何
数组，不新增任何训练开关。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from ch3_ft_entity_ranking_loss import require, tail_aggregate  # noqa: E402  复用唯一聚合实现

_FROZEN_ALPHA = 0.5
_VALID_AGGREGATIONS = ("maximum", "tail_mean")


def entity_bce_loss(
    flow_logits: Any,
    flow_valid: Any,
    entity_of_row: Any,
    entity_labels: Any,
    aggregation: str,
    alpha: float,
    torch_module: Any,
) -> tuple[Any, dict[str, Any]]:
    """实体级 BCE：先把逐流 logits 聚合成实体分数，再对实体做二分类。

    ``aggregation="maximum"`` 时取实体内最大值（对应四格 z1'=0 臂，等价于
    ``tail_aggregate(..., alpha=None)``，k≡1 退化为 max，与
    ``ch3_ft_entity_ranking_loss.prefix_scores`` 的 max 语义一致但走的是尾部聚合
    的同一份代码路径，不另起一套 max 实现）；
    ``aggregation="tail_mean"`` 时取 top-⌈alpha·m_e⌉ 的均值（z1'=1，即 ETA）。

    参数：
    - ``flow_logits``/``flow_valid``/``entity_of_row``：一维、长度相同的逐流视图
      （与 ``tail_aggregate`` 的 ``flow_scores``/``flow_valid``/``flow_entity``
      同一层级——本函数是它的直接调用方，不是 ``ch3_ft_entity_ranking_loss.
      tail_scores`` 那个 (B,T) 训练侧入口，调用方若持有 (B,T) 形状须自行展平）。
    - ``entity_labels``：一维，长度即批内实体总数 ``num_entities``，取值
      {0,1}（或可转 {0,1} 的浮点/布尔），下标须与 ``entity_of_row`` 的取值范围
      对齐（即 ``entity_of_row`` 的紧凑实体下标落在 ``[0, entity_labels.numel())``）。
    - ``aggregation``：仅接受 ``"maximum"`` 或 ``"tail_mean"``，其他值 raise。
    - ``alpha``：仅接受已冻结的 ``0.5``，其他值 raise（防御性校验，见模块文档
      字符串——本函数不按任何实验读数回调该值，也不代表调用方决定要不要冻结）。
    - ``torch_module``：调用方注入的 ``torch`` 模块（与本仓库既有的
      ``ch3_ft_c00_dual_selection.py``/``ch3_ft_verify_four_cell_artifacts.py``
      同一依赖注入模式），本函数所有显式 torch 操作都经它调用。

    返回 ``(loss, diagnostics)``：
    - ``loss``：标量张量，对 ``flow_logits`` 可导（梯度经 ``tail_aggregate`` 的
      gather/index_add 路径只回到被选中的 top-k_e 条流，见其文档字符串）；
    - ``diagnostics``：含 ``entity_scores``/``k_per_entity``/``m_per_entity``/
      ``scored_mask``（均为 detach 后的实体级张量，非逐流数组、非实体成员表，
      供调用方诊断或自检核对）与若干 JSON 安全的标量字段。

    空实体处置：``tail_aggregate`` 对 ``m_e=0`` 的实体返回有限值（分数 0，见其
    文档字符串），本函数按 ``m_per_entity > 0`` 掩码将其从 BCE 均值中剔除
    （不是产生 NaN 后再补救——掩码在求均值之前生效，NaN 从未产生）。若一批内
    全部实体都无有效流，判为调用方的数据契约错误，直接 raise，不返回退化为 0
    或 NaN 的损失。
    """
    require(
        aggregation in _VALID_AGGREGATIONS,
        f"aggregation 只接受 {_VALID_AGGREGATIONS}，实得 {aggregation!r}",
    )
    require(
        alpha == _FROZEN_ALPHA,
        f"alpha 只接受已冻结值 {_FROZEN_ALPHA}，不得按任何实验读数回调，实得 {alpha!r}",
    )
    require(
        flow_logits.shape == flow_valid.shape == entity_of_row.shape,
        "flow_logits / flow_valid / entity_of_row 长度须一致",
    )
    require(entity_labels.dim() == 1, "entity_labels 须为一维张量")

    num_entities = int(entity_labels.shape[0])
    require(num_entities > 0, "entity_labels 不得为空")
    require(
        bool((entity_of_row >= 0).all()) and bool((entity_of_row < num_entities).all()),
        "entity_of_row 存在越出 entity_labels 下标范围 [0, num_entities) 的值",
    )

    fp32 = torch_module.float32
    flow_logits_fp32 = flow_logits.to(dtype=fp32)  # 聚合须 FP32，见模块文档字符串

    tail_alpha = None if aggregation == "maximum" else alpha
    aggregated = tail_aggregate(flow_logits_fp32, flow_valid, entity_of_row, num_entities, tail_alpha)
    entity_scores = aggregated["entity_scores"]
    k_per_entity = aggregated["k_per_entity"]
    m_per_entity = aggregated["m_per_entity"]
    scored_mask = m_per_entity > 0
    require(bool(scored_mask.any()), "本批全部实体均无有效流，无法计算实体级 BCE")

    labels_fp32 = entity_labels.to(dtype=fp32)
    per_entity_bce = torch_module.nn.functional.binary_cross_entropy_with_logits(
        entity_scores, labels_fp32, reduction="none"
    )
    loss = per_entity_bce[scored_mask].mean()

    diagnostics: dict[str, Any] = {
        "aggregation": aggregation,
        "alpha": alpha,
        "num_entities": num_entities,
        "scored_entity_count": int(scored_mask.sum().item()),
        "empty_entity_count": int((~scored_mask).sum().item()),
        "entity_bce_loss_value": float(loss.detach().item()),
        "entity_scores": entity_scores.detach(),
        "k_per_entity": k_per_entity.detach(),
        "m_per_entity": m_per_entity.detach(),
        "scored_mask": scored_mask.detach(),
    }
    return loss, diagnostics
