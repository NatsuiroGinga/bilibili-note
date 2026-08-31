# -*- coding: utf-8 -*-
"""机制二：实体路径最大分数与多预算 CVaR-pAUC 排序损失（spec 5.1、5.3、5.3.1）。

设计依据（`.Codex/docs/RWKV/2026-08-28-机制二梯度信号实测裁决.md`）：收敛模型上普通
成对排序（RankNet，随机负例）梯度范数中位为 6.08e-14，比逐流梯度低约 12 个数量级、
12 批中 3 批严格为零；CVaR 形式相对普通形式的梯度范数比在收敛模型上为 16.61（随机
初始化时仅 1.30）。故本模块只把 CVaR-pAUC 形式作为主损失，普通形式只作对照。

三个公开接口：
- `prefix_scores`：实体路径最大分数 `S_e = max_t l_{e,t}`（spec 5.1），部署同构，
  唯一最大值时梯度只回到取得最大 logit 的流，并列时用固定稳定顺序的合法子梯度
  （实现细节见 `prefix_scores` 文档字符串，对应的 PyTorch API 行为已用
  `npx ctx7@latest docs` 核验，见下方“第三方 API 核验记录”）。
- `cvar_pauc_loss`：多预算 CVaR-pAUC（spec 5.3），`xi` 是训练私有阈值状态，按公式
  字面实现，不做 5.4 节讨论的总体负实体重加权（见 `effective_budget` 与其文档）。
- `bag_policy_diagnostics`：同一批上并行计算三种袋处置（完整袋／因果前缀截断／
  分层加权，spec 5.3.1）的损失，只对配置指定的一种保留反传图，另两种只记录数值。

第三方 API 核验记录（本机 PyTorch 2.12.0，通过 npx ctx7@latest 核对
docs.pytorch.org/docs/2.11 与 2.12 兼容的官方文档，2.11 与 2.12 之间这几个算子
签名未变）：
- `torch.Tensor.argmax(dim, keepdim=False)`：官方文档原文「If multiple values equal
  the maximum of the tensor, the first occurrence of the maximum value is returned」——
  并列取首个最大值，已确认，故本模块不依赖 `torch.max` 反传时对并列的隐式处理，
  改用 `argmax` 定位 + `gather` 取值的组合，让梯度只回到确定的单一位置。
- `Tensor.scatter_reduce(dim, index, src, reduce, *, include_self=True) -> Tensor`：
  核验其为 out-of-place、支持 `reduce="amax"/"amin"` 的公开签名；本模块只用它定位
  数值与位置（对其自身不反传，先 `.detach()`），真正的梯度路径始终经 `gather`。
- `Tensor.scatter(dim, index, src)`：核验其为 out-of-place 版本，用于把逐实体的
  选中值放回稠密张量。

本模块不接入宿主 `ch3_ft_c00_dual_selection.py`，不读取目标年数组。
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

_VALID_POLICIES = ("full", "causal_prefix_truncation", "stratified_weighting")


def require(condition: bool, message: str) -> None:
    """运行断言：条件不满足即视为无效结果，立即停止，不吞掉错误。"""
    if not condition:
        raise RuntimeError(message)


# --------------------------------------------------------------------------
# 1. 实体路径最大分数
# --------------------------------------------------------------------------


def prefix_scores(
    logits: torch.Tensor,
    valid: torch.Tensor,
    segment_owner: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    """实体路径最大分数。

    logits: (B, T) 逐流 logit；valid: (B, T) 有效掩码；
    segment_owner: (B,) 每个片段所属实体在本批内的紧凑下标，取值 0..E-1。
    返回 (entity_scores[E], entity_source_row[E])：
    - entity_scores：`S_e = max_t l_{e,t}`，梯度只回到取得最大值的那一条流；
    - entity_source_row：取得该最大值的片段在输入 (B,...) 中的行下标，用于诊断。

    实现：先对每个片段用 -inf 填充无效位后取列内最大值（并列取首个最大值列，
    argmax 的该行为已由官方文档确认，见模块顶部核验记录），得到确定性的片段级
    分数；再在实体内部对片段级分数定位「数值最大值」与「最靠前的来源片段」
    （用 scatter_reduce 的 amax/amin 只做定位，不对其反传），最终用 gather 取值，
    保证梯度只走一条确定的流，不依赖 scatter_reduce 自身对并列的反传行为。

    允许整片段无有效流（例如因果前缀截断后，超出预算的片段被整体置为无效）；
    此时该片段的片段级分数为 -inf，不参与其所属实体的最大值竞争。但要求每个
    实体至少有一个有效流——这是数据契约（企图截断到 0 长度是调用方的配置错误），
    在实体级别核验，不在片段级别核验。
    """
    require(logits.shape == valid.shape, "logits 与 valid 形状不一致")
    require(segment_owner.shape[0] == logits.shape[0], "segment_owner 长度须等于片段数 B")
    valid_bool = valid if valid.dtype == torch.bool else valid > 0

    filled = logits.masked_fill(~valid_bool, float("-inf"))
    seg_col_idx = filled.argmax(dim=1)  # (B,) 并列取首个最大值列位置（官方文档确认）
    segment_scores = filled.gather(1, seg_col_idx.unsqueeze(1)).squeeze(1)  # (B,)

    num_entities = int(segment_owner.max().item()) + 1
    device = segment_scores.device
    dtype = segment_scores.dtype

    max_per_entity = torch.full((num_entities,), float("-inf"), dtype=dtype, device=device)
    max_per_entity = max_per_entity.scatter_reduce(
        0, segment_owner, segment_scores.detach(), reduce="amax", include_self=True
    )
    is_entity_max = segment_scores.detach() == max_per_entity[segment_owner]
    positions = torch.arange(segment_scores.shape[0], device=device)
    sentinel = segment_scores.shape[0]
    candidate_pos = torch.where(is_entity_max, positions, torch.full_like(positions, sentinel))
    first_pos = torch.full((num_entities,), sentinel, dtype=positions.dtype, device=device)
    first_pos = first_pos.scatter_reduce(0, segment_owner, candidate_pos, reduce="amin", include_self=True)
    require(not bool((first_pos == sentinel).any()), "存在没有任何片段的实体紧凑下标")

    entity_scores = segment_scores.gather(0, first_pos)
    require(
        bool(torch.isfinite(entity_scores).all()),
        "存在完全无有效流的实体（-inf 分数），违反数据契约"
        "（因果前缀截断的 truncate_length 不得截到某实体 0 条有效流）",
    )
    return entity_scores, first_pos


# --------------------------------------------------------------------------
# 2. 多预算 CVaR-pAUC 损失
# --------------------------------------------------------------------------


def cvar_pauc_loss(
    pos: torch.Tensor,
    neg: torch.Tensor,
    budgets: Sequence[int | float],
    xi: torch.Tensor,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """多预算 CVaR-pAUC 排序损失（spec 5.3 公式字面实现）。

    R_K(theta,xi) = mean_p[ xi_{p,K} + (1/K) * sum_n [L_pn - xi_{p,K}]_+ ]，
    L_pn = softplus(S_n - S_p)，L_rank = mean_K R_K。

    pos: (Np,) 正实体路径最大分数 S_p；neg: (Nn,) 负实体路径最大分数 S_n；
    budgets: 预算序列，K 须满足 1<=K<=Nn；xi: (Np, len(budgets)) 训练期阈值状态，
    须 requires_grad=True 才能与共享参数联合反传（xi 自身的梯度由调用方另行更新，
    见 CvarThresholdState，不受机制二任务 3 的梯度控制器投影）。

    接口约定（5.4 节留下的一处显式处置）：本函数按字面公式对「当前传入的 neg」
    求和，即把 neg 当作该步的全体负实体。若 neg 实际是从更大总体 N_- 中均匀抽样
    而来，调用方须用 `effective_budget()` 把真实预算折算成与抽样规模一致的等效
    K，才能得到 5.4 节定义的无偏估计；否则本函数计算的是「以当前 neg 为全体负
    实体」的精确 CVaR。诊断验证中按探针脚本同款约定处理（见本文件 main()）。

    返回 (标量损失, 诊断字典)。诊断含每预算 CVaR 活动率（L_pn>xi 的比例，
    退化为 0 说明该预算项梯度为零，见 spec 5.6.3）。
    """
    require(pos.dim() == 1 and neg.dim() == 1, "pos 与 neg 须为一维张量")
    require(pos.numel() > 0 and neg.numel() > 0, "cvar_pauc_loss 要求正负实体分数均非空")
    require(
        tuple(xi.shape) == (pos.numel(), len(budgets)),
        f"xi 形状须为 ({pos.numel()}, {len(budgets)})，实得 {tuple(xi.shape)}",
    )

    pairwise = torch.nn.functional.softplus(neg.unsqueeze(0) - pos.unsqueeze(1))  # (Np, Nn) = L_pn
    n_neg = neg.numel()

    budget_terms = []
    per_budget_active_rate: dict[str, float] = {}
    per_budget_mean_xi: dict[str, float] = {}
    for col, k in enumerate(budgets):
        require(0 < k <= n_neg, f"预算 K={k} 越出合法范围 (1..{n_neg})")
        xi_k = xi[:, col]
        hinge = torch.relu(pairwise - xi_k.unsqueeze(1))  # [.]_+，relu 在 0 点子梯度取 0
        r_k = xi_k + hinge.sum(dim=1) / float(k)
        budget_terms.append(r_k.mean())
        with torch.no_grad():
            per_budget_active_rate[str(k)] = float((pairwise > xi_k.unsqueeze(1)).float().mean())
            per_budget_mean_xi[str(k)] = float(xi_k.mean())

    loss = torch.stack(budget_terms).mean()
    diagnostics = {
        "budgets": [float(k) for k in budgets],
        "per_budget_active_rate": per_budget_active_rate,
        "per_budget_mean_xi": per_budget_mean_xi,
        "pairwise_loss_mean": float(pairwise.detach().mean()),
        "pairwise_loss_max": float(pairwise.detach().max()),
        "positive_entity_count": int(pos.numel()),
        "negative_entity_count": int(neg.numel()),
    }
    return loss, diagnostics


def effective_budget(
    real_budget: int, population_negative_count: int, sampled_negative_count: int
) -> float:
    """把冻结告警合同的真实整数预算 K 折算为「以当前抽样负实体数为分母」的等效 K。

    推导（spec 5.4）：单样本无偏估计量 r_hat = xi + (1/beta_K)[L_pn-xi]_+，
    beta_K=K/N_-。若把 K_eff = K * n_sampled / N_- 传给 cvar_pauc_loss，则
    (1/K_eff) * sum_{n in sampled} [.]_+ = (N_-/(K*n_sampled)) * sum_{n in sampled}[.]_+
    = (1/beta_K) * mean_{n in sampled}[.]_+，与对单样本无偏估计量取样本均值一致。
    K_eff 一般不是整数，按 float 返回，调用方决定是否取整（取整会引入可忽略的
    离散化偏差，不改变数量级）。
    """
    require(
        population_negative_count > 0 and sampled_negative_count > 0,
        "population_negative_count 与 sampled_negative_count 必须为正",
    )
    return real_budget * sampled_negative_count / population_negative_count


class CvarThresholdState:
    """维护每个 (正实体全局 ID, 预算 K) 对的训练期阈值 xi_{p,K}（spec 5.3、6.4）。

    xi 只在损失侧参与反向传播、不进推理模型；本类只负责按全局实体 ID（task1
    `EntityStratifiedSampler.sample()` 输出的 positive_entities，是 E23 原始下标，
    不是 prefix_scores 用的批内紧凑下标）存取、惰性初始化与序列化，不绑定优化器
    ——调用方对 get() 返回的叶张量完成一次反向传播后，需显式调用 commit() 写回。

    2026-08-31 增加跨步水库分位数估计（见
    `.Codex/docs/RWKV/2026-08-31-CVaR预算失配数学分析/分析报告.md`）：
    Rockafellar-Uryasev 变分形式下 xi_{p,K} 的最优值恰是配对损失 L_pn 的
    (1 - K_eff/N_n) 分位数，故不需要用子梯度 SGD 去追踪它——子梯度追踪产生的滞后
    正是各预算档 CVaR 活动率偏离设计值 beta 的直接原因。本类因此为每个正实体维护
    一个跨步环形水库，直接对水库取分位数。**跨步是关键**：单步只有 n_neg 个负实体
    （冻结配置为 64），估不出最低档所需的 1/beta_min ≈ 1003 分位数，跨步累积可以，
    所以不必增大 n_neg。

    子梯度接口 get()/commit() 保留不删：旧检查点与旧诊断脚本仍在调用，且水库尚未
    积累到某档所需样本量时需要回退到 init_value 起步。
    """

    def __init__(
        self,
        budgets: Sequence[int],
        init_value: float = 0.0,
        reservoir_size: int = 4096,
        dtype: torch.dtype = torch.float32,
    ) -> None:
        self._budgets = tuple(int(k) for k in budgets)
        self._init_value = float(init_value)
        self._dtype = dtype
        self._table: dict[int, torch.Tensor] = {}
        self._reservoir_size = int(reservoir_size)
        require(self._reservoir_size > 0, "reservoir_size 须为正整数")
        # 每个正实体一个环形缓冲：样本是该实体与各负实体的配对损失 L_pn。
        # 跨步累积是本修法的关键——单步只有 n_neg 个负实体，
        # 估不出最低档所需的 1/beta_min 分位数，跨步可以。
        self._reservoir: dict[int, torch.Tensor] = {}
        self._reservoir_fill: dict[int, int] = {}

    @property
    def budgets(self) -> tuple[int, ...]:
        return self._budgets

    def get(self, positive_entity_ids: np.ndarray | torch.Tensor) -> torch.Tensor:
        """取出（惰性初始化）对应 xi 行，返回 requires_grad=True 的叶张量，形状 (Np, |K|)。"""
        ids = [int(e) for e in positive_entity_ids]
        rows = []
        for entity_id in ids:
            if entity_id not in self._table:
                self._table[entity_id] = torch.full(
                    (len(self._budgets),), self._init_value, dtype=self._dtype
                )
            rows.append(self._table[entity_id])
        stacked = torch.stack(rows).clone().detach()
        stacked.requires_grad_(True)
        return stacked

    def commit(self, positive_entity_ids: np.ndarray | torch.Tensor, xi_updated: torch.Tensor) -> None:
        """把一步更新后的 xi（例如 xi - lr * xi.grad）写回持久表，detach 后以 FP32 存储。"""
        ids = [int(e) for e in positive_entity_ids]
        detached = xi_updated.detach().to(self._dtype)
        require(detached.shape[0] == len(ids), "commit 的行数须与 positive_entity_ids 一致")
        for row, entity_id in zip(detached, ids):
            self._table[entity_id] = row.clone()

    def observe(
        self, positive_entity_ids: np.ndarray | torch.Tensor, pairwise: torch.Tensor
    ) -> None:
        """把本步观测到的配对损失写入各正实体的环形水库。

        pairwise 形状 (Np, Nn)，第 p 行是该正实体对本步全部负实体的 L_pn。
        只存数值不存图：阈值是统计量而非优化变量，不参与反向传播。

        调用顺序有科学含义：必须**先** quantile() 取阈值、算完损失，**再** observe()
        写入本步样本。顺序颠倒会让本步样本污染本步阈值，破坏「阈值由严格过去样本
        估计」这一性质。
        """
        require(pairwise.dim() == 2, "pairwise 须为二维 (Np, Nn)")
        ids = [int(e) for e in positive_entity_ids]
        require(pairwise.shape[0] == len(ids), "pairwise 行数须与正实体数一致")
        samples = pairwise.detach().to(self._dtype).cpu()
        for row, entity_id in zip(samples, ids):
            if entity_id not in self._reservoir:
                self._reservoir[entity_id] = torch.zeros(self._reservoir_size, dtype=self._dtype)
                self._reservoir_fill[entity_id] = 0
            buffer = self._reservoir[entity_id]
            fill = self._reservoir_fill[entity_id]
            incoming = row.reshape(-1)
            take = min(int(incoming.numel()), self._reservoir_size)
            head = incoming[-take:]
            start = fill % self._reservoir_size
            end = start + take
            if end <= self._reservoir_size:
                buffer[start:end] = head
            else:
                split = self._reservoir_size - start
                buffer[start:] = head[:split]
                buffer[: end - self._reservoir_size] = head[split:]
            self._reservoir_fill[entity_id] = fill + take

    def quantile(
        self,
        positive_entity_ids: np.ndarray | torch.Tensor,
        effective_budgets: Sequence[float],
        sampled_negative_count: int,
    ) -> torch.Tensor:
        """按 Rockafellar-Uryasev 最优点直接取分位数，返回 detached 阈值 (Np, |K|)。

        第 col 列取 1 - eff_K[col] / sampled_negative_count 分位数：CVaR 的内层
        min 恰在该分位数取得，故不需要用子梯度追踪它。effective_budgets 与
        sampled_negative_count 的口径与 effective_budget() 一致（前者是已按抽样
        规模折算的等效 K，后者是该折算所用的分母 n_neg）。

        水库未积累到该分位数所需样本量时，退回 init_value 并可由
        reservoir_diagnostics() 看出，不静默给出不可靠的极端分位数。
        """
        require(sampled_negative_count > 0, "sampled_negative_count 须为正")
        ids = [int(e) for e in positive_entity_ids]
        levels: list[float] = []
        for eff_k in effective_budgets:
            level = 1.0 - float(eff_k) / float(sampled_negative_count)
            require(0.0 < level < 1.0, f"分位数水平越界：{level}")
            levels.append(level)
        rows = []
        for entity_id in ids:
            fill = self._reservoir_fill.get(entity_id, 0)
            usable = min(fill, self._reservoir_size)
            if usable == 0:
                rows.append(torch.full((len(levels),), self._init_value, dtype=self._dtype))
                continue
            window = self._reservoir[entity_id][:usable].to(torch.float32)
            values = []
            for level in levels:
                # 该分位数需要至少 1/(1-level) 个样本才有意义，否则退回初值。
                needed = 1.0 / max(1.0 - level, 1e-12)
                if usable < needed:
                    values.append(self._init_value)
                else:
                    values.append(float(torch.quantile(window, level)))
            rows.append(torch.tensor(values, dtype=self._dtype))
        return torch.stack(rows)

    def reservoir_diagnostics(self) -> dict[str, Any]:
        """水库占用与分位数可用性，供运行收据记录。"""
        if not self._reservoir_fill:
            return {"tracked_entities": 0, "reservoir_size": self._reservoir_size}
        fills = np.array([min(v, self._reservoir_size) for v in self._reservoir_fill.values()])
        return {
            "tracked_entities": int(fills.size),
            "reservoir_size": self._reservoir_size,
            "fill_median": float(np.median(fills)),
            "fill_min": int(fills.min()),
            "fill_full_fraction": float((fills >= self._reservoir_size).mean()),
        }

    def state_dict(self) -> dict[str, Any]:
        # 水库以张量而非列表导出：本状态只进 torch.save 的检查点载荷
        # （ch3_ft_c00_dual_selection.checkpoint_payload -> atomic_torch），
        # 不进 JSON；张量导出比 tolist() 小得多也快得多。
        # 冻结配置下上界为 165 个正实体 × 4096 × 4B ≈ 2.6 MiB。
        return {
            "budgets": list(self._budgets),
            "init_value": self._init_value,
            "entries": {str(k): v.tolist() for k, v in self._table.items()},
            "reservoir_size": self._reservoir_size,
            "reservoir": {str(k): v.clone() for k, v in self._reservoir.items()},
            "reservoir_fill": {str(k): int(v) for k, v in self._reservoir_fill.items()},
        }

    def load_state_dict(self, payload: dict[str, Any]) -> None:
        """加载阈值状态。水库三键缺失时降级为空水库而不是抛异常——

        本方法在 2026-08-31 之前写出的检查点里没有这三个键，续训必须仍能加载；
        空水库会让 quantile() 先按 init_value 起步，再由后续步重新积累样本。
        """
        self._budgets = tuple(int(k) for k in payload["budgets"])
        self._init_value = float(payload["init_value"])
        self._table = {
            int(k): torch.tensor(v, dtype=self._dtype) for k, v in payload["entries"].items()
        }
        self._reservoir_size = int(payload.get("reservoir_size", self._reservoir_size))
        require(self._reservoir_size > 0, "检查点中的 reservoir_size 非正")
        self._reservoir = {
            int(k): torch.as_tensor(v, dtype=self._dtype).clone()
            for k, v in (payload.get("reservoir") or {}).items()
        }
        self._reservoir_fill = {
            int(k): int(v) for k, v in (payload.get("reservoir_fill") or {}).items()
        }


# --------------------------------------------------------------------------
# 3. 三种袋处置的并行诊断
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BagPolicyConfig:
    """三种袋处置的选择与参数（spec 5.3.1，尚处「待裁决」状态，见本文件对
    stratified_weighting 的口径说明）。"""

    active_policy: str  # "full" | "causal_prefix_truncation" | "stratified_weighting"
    truncate_length: int  # 因果前缀截断的 L；分层加权与完整袋分支不使用，但仍需提供
    num_length_buckets: int  # 分层加权的 log2 链长分桶数


def _length_buckets(chain_length: torch.Tensor, num_buckets: int) -> torch.Tensor:
    """log2 尺度分桶，边界由本批实体链长自身量级决定，不引入外部魔法阈值。"""
    log_length = torch.log2(chain_length.clamp(min=1).to(torch.float32))
    max_log = float(log_length.max().item())
    if max_log <= 0:
        return torch.zeros_like(chain_length, dtype=torch.long)
    bucket_width = max_log / num_buckets
    bucket_ids = torch.clamp((log_length / bucket_width).floor().long(), max=num_buckets - 1)
    return bucket_ids


def _stratified_mean(values: torch.Tensor, bucket_ids: torch.Tensor, num_buckets: int) -> torch.Tensor:
    """两层分层均值：先桶内等权均值，再桶间等权均值（跳过空桶）。"""
    bucket_means = []
    for b in range(num_buckets):
        selector = bucket_ids == b
        if bool(selector.any()):
            bucket_means.append(values[selector].mean())
    require(len(bucket_means) > 0, "分层加权：所有桶均为空，无法计算")
    return torch.stack(bucket_means).mean()


def _cvar_pauc_loss_stratified(
    pos: torch.Tensor,
    neg: torch.Tensor,
    budgets: Sequence[int],
    xi: torch.Tensor,
    pos_bucket: torch.Tensor,
    neg_bucket: torch.Tensor,
    num_buckets: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """分层加权版 CVaR-pAUC——本实现对 5.3.1 节「分层加权」处置的具体口径：

    把 cvar_pauc_loss 中「负实体的 (1/K)*sum_n」与「正实体的外层 mean_p」两处
    等权均值，都换成「先桶内等权均值、再桶间等权均值」的两层分层均值。当全部
    实体落在同一个桶时，退化为与 cvar_pauc_loss 完全一致的等权均值。该处置仍
    在 5.3.1 节标注为「待裁决」，本函数是可运行、可比较的一种忠实解释，不代表
    最终冻结公式；若源年数据裁决出不同权重公式，只需替换本函数，不影响其余
    接口。
    """
    require(pos.numel() > 0 and neg.numel() > 0, "cvar_pauc_loss 要求正负实体分数均非空")
    pairwise = torch.nn.functional.softplus(neg.unsqueeze(0) - pos.unsqueeze(1))  # (Np, Nn)
    n_neg = neg.numel()

    per_positive_terms = []
    per_budget_active_rate: dict[str, float] = {}
    for col, k in enumerate(budgets):
        require(0 < k <= n_neg, f"预算 K={k} 越出合法范围 (1..{n_neg})")
        xi_k = xi[:, col]
        hinge = torch.relu(pairwise - xi_k.unsqueeze(1))  # (Np, Nn)
        stratified_hinge_mean = torch.stack(
            [_stratified_mean(hinge[p], neg_bucket, num_buckets) for p in range(hinge.shape[0])]
        )  # (Np,)
        r_k = xi_k + (float(n_neg) / float(k)) * stratified_hinge_mean
        per_positive_terms.append(r_k)
        with torch.no_grad():
            per_budget_active_rate[str(k)] = float((pairwise > xi_k.unsqueeze(1)).float().mean())

    stacked = torch.stack(per_positive_terms, dim=1)  # (Np, |K|)
    per_budget_loss = torch.stack(
        [_stratified_mean(stacked[:, col], pos_bucket, num_buckets) for col in range(len(budgets))]
    )
    loss = per_budget_loss.mean()
    diagnostics = {
        "budgets": [float(k) for k in budgets],
        "per_budget_active_rate": per_budget_active_rate,
        "pairwise_loss_mean": float(pairwise.detach().mean()),
        "positive_entity_count": int(pos.numel()),
        "negative_entity_count": int(neg.numel()),
        "num_length_buckets": num_buckets,
    }
    return loss, diagnostics


def _entity_groups(segment_owner: torch.Tensor, num_entities: int) -> list[torch.Tensor]:
    """按 task1 的 segment_rows 约定（segment_owner 已按 (entity,T23) 分组有序），
    切出每个实体对应的片段下标（原始顺序）。若该约定被违反（同一实体片段分布
    不连续），判为数据契约错误并停止。
    """
    n = segment_owner.shape[0]
    device = segment_owner.device
    if n == 0:
        return [torch.empty(0, dtype=torch.long, device=device) for _ in range(num_entities)]
    positions = torch.arange(n, device=device)
    boundary_mask = torch.cat(
        [torch.ones(1, dtype=torch.bool, device=device), segment_owner[1:] != segment_owner[:-1]]
    )
    boundary_positions = positions[boundary_mask]
    boundary_entities = segment_owner[boundary_mask]
    require(
        int(boundary_entities.unique().numel()) == int(boundary_entities.numel()),
        "segment_owner 未按 (entity,T23) 分组有序，违反 task1 的 segment_rows 约定",
    )
    ends = torch.cat([boundary_positions[1:], torch.tensor([n], device=device)])
    groups: list[torch.Tensor] = [torch.empty(0, dtype=torch.long, device=device) for _ in range(num_entities)]
    for start, end, entity_id in zip(
        boundary_positions.tolist(), ends.tolist(), boundary_entities.tolist()
    ):
        groups[entity_id] = positions[start:end]
    return groups


def _causal_truncate_valid(
    valid: torch.Tensor, entity_groups: list[torch.Tensor], truncate_length: int
) -> torch.Tensor:
    """按 (片段序号, 列位置) 因果序，每实体只保留前 truncate_length 条有效流。"""
    truncated = valid.clone()
    for rows in entity_groups:
        if rows.numel() == 0:
            continue
        remaining = truncate_length
        for row in rows.tolist():
            if remaining <= 0:
                truncated[row] = False
                continue
            row_valid = truncated[row]
            count = int(row_valid.sum().item())
            if count <= remaining:
                remaining -= count
                continue
            valid_cols = torch.nonzero(row_valid, as_tuple=True)[0]
            keep_cols = valid_cols[:remaining]
            new_row = torch.zeros_like(row_valid)
            new_row[keep_cols] = True
            truncated[row] = new_row
            remaining = 0
    return truncated


def bag_policy_diagnostics(
    logits: torch.Tensor,
    valid: torch.Tensor,
    segment_owner: torch.Tensor,
    entity_is_positive: torch.Tensor,
    entity_chain_length: torch.Tensor,
    budgets: Sequence[int],
    xi: torch.Tensor,
    config: BagPolicyConfig,
) -> dict[str, Any]:
    """同一批上并行计算三种袋处置的损失，只对 config.active_policy 保留反传图，
    另两种只记录数值（spec 5.3.1：「跑一臂比较三条曲线」的实现）。

    entity_is_positive、entity_chain_length 下标须与 segment_owner 的紧凑下标
    对齐（长度 E，E = 批内实体数）。xi 的行须与 entity_is_positive 中的正实体
    顺序对齐（即 entity_scores[entity_is_positive] 的顺序）。
    """
    require(config.active_policy in _VALID_POLICIES, f"未知袋处置策略：{config.active_policy}")
    num_entities = int(segment_owner.max().item()) + 1
    require(
        entity_is_positive.shape[0] == num_entities and entity_chain_length.shape[0] == num_entities,
        "entity_is_positive / entity_chain_length 长度须等于批内实体数 E",
    )

    def _score_and_loss(
        valid_mask: torch.Tensor, stratified: bool
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        entity_scores, source_row = prefix_scores(logits, valid_mask, segment_owner)
        pos_scores = entity_scores[entity_is_positive]
        neg_scores = entity_scores[~entity_is_positive]
        if stratified:
            pos_bucket = _length_buckets(entity_chain_length[entity_is_positive], config.num_length_buckets)
            neg_bucket = _length_buckets(entity_chain_length[~entity_is_positive], config.num_length_buckets)
            loss, diag = _cvar_pauc_loss_stratified(
                pos_scores, neg_scores, budgets, xi, pos_bucket, neg_bucket, config.num_length_buckets
            )
        else:
            loss, diag = cvar_pauc_loss(pos_scores, neg_scores, budgets, xi)
        diag["entity_score_source_row"] = source_row.detach().tolist()
        return loss, diag

    results: dict[str, Any] = {"active_policy": config.active_policy, "policies": {}}

    full_loss, full_diag = _score_and_loss(valid, stratified=False)
    results["policies"]["full"] = {"loss_value": float(full_loss.detach()), **full_diag}

    entity_groups = _entity_groups(segment_owner, num_entities)
    truncated_valid = _causal_truncate_valid(valid, entity_groups, config.truncate_length)
    truncated_loss, truncated_diag = _score_and_loss(truncated_valid, stratified=False)
    results["policies"]["causal_prefix_truncation"] = {
        "loss_value": float(truncated_loss.detach()),
        **truncated_diag,
    }

    stratified_loss, stratified_diag = _score_and_loss(valid, stratified=True)
    results["policies"]["stratified_weighting"] = {
        "loss_value": float(stratified_loss.detach()),
        **stratified_diag,
    }

    active_loss = {
        "full": full_loss,
        "causal_prefix_truncation": truncated_loss,
        "stratified_weighting": stratified_loss,
    }[config.active_policy]
    results["loss"] = active_loss
    return results


# --------------------------------------------------------------------------
# 真实数据核验（spec 与实施计划要求：用第四章已训练检查点核对 CVaR/普通梯度比）
# --------------------------------------------------------------------------


def _quantile_init_xi(pairwise: torch.Tensor, k: int) -> torch.Tensor:
    """把 xi 初始化为每正实体损失分布的第 K 大值（CVaR 变分形式在该点附近取得
    最优，见 Rockafellar-Uryasev），仅用于本诊断脚本做单步梯度比较，不代表训练
    期 xi 的真实演化轨迹（后者应从 0 或历史值出发，由优化器逐步逼近）。"""
    k = min(k, pairwise.shape[1])
    topk_vals, _ = torch.topk(pairwise, k=k, dim=1)
    return topk_vals[:, -1].detach().unsqueeze(1)  # (Np, 1) 第 K 大值


def _cap_segments_per_entity(rows: np.ndarray, entity_of_row: np.ndarray, max_segments: int) -> np.ndarray:
    """诊断脚本专用子采样：每实体最多保留因果最早的 max_segments 个片段。

    负实体池中存在最大 2,475,228 条流的极端袋（见 5.3.1 节），若不加控制，诊断
    脚本单次前向可能吃到该规模的实体，运行时间不可控。`rows` 已按 (entity,T23)
    升序排列（task1 的 segment_rows 约定），故"前 max_segments 个"即因果最早的
    片段——这与本文件已实现的因果前缀截断（`_causal_truncate_valid`）同一原理，
    只是在诊断脚本层面提前应用，不改变 prefix_scores/cvar_pauc_loss 等库函数
    对任意袋规模的支持能力。
    """
    if rows.size == 0:
        return rows
    boundaries = np.flatnonzero(np.r_[True, entity_of_row[1:] != entity_of_row[:-1]])
    ends = np.r_[boundaries[1:], len(entity_of_row)]
    parts = [rows[start : min(start + max_segments, end)] for start, end in zip(boundaries, ends)]
    return np.concatenate(parts)


def _flat_grad(loss: torch.Tensor, params: list[torch.nn.Parameter]) -> torch.Tensor:
    """对共享参数求梯度并展平；未参与计算图的参数补零。与
    ch3_gradient_controller_conflict_probe.py 的同名函数逻辑一致，独立实现避免
    跨文件耦合。"""
    grads = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
    pieces = [
        (torch.zeros_like(p) if g is None else g).reshape(-1) for p, g in zip(params, grads)
    ]
    return torch.cat(pieces)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument(
        "--checkpoint",
        default="runs/diagnostics/ch4-mlp-o11-oof-fold-models-seed42-v1/fold-0/checkpoints/selected-O11.pt",
    )
    parser.add_argument("--n-pos", type=int, default=2, help="诊断用，非冻结训练配置")
    parser.add_argument("--n-neg", type=int, default=64, help="诊断用，非冻结训练配置")
    parser.add_argument("--beta", type=float, default=0.04, help="诊断用 CVaR 预算比例，对齐探针脚本")
    parser.add_argument(
        "--truncate-length",
        type=int,
        default=256,
        help="诊断用因果截断长度，取小值以在诊断脚本的子采样批（每实体<=8段）上实际触发截断；"
        "5.3.1 节记录的真实单步流预算是 8192，未来宿主接入训练时应使用该值而非本诊断默认值",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    from ch3_ft_entity_stratified_sampler import (
        EntityStratifiedSampler,
        EntityStratifiedSamplerConfig,
    )
    from ch4_mlp_o11_oof_fold_models_local_screen import LocalFullMLP

    cache_root = Path(args.cache_root).resolve()
    for name in ("X24", "y24", "I24", "M24", "E24", "T24"):
        require(not (cache_root / f"{name}.npy").is_file(), f"检测到目标年文件 {name}.npy")

    E = np.load(cache_root / "E23.npy")
    I = np.load(cache_root / "I23.npy", mmap_mode="r")
    M = np.load(cache_root / "M23.npy", mmap_mode="r")
    T = np.load(cache_root / "T23.npy")
    y = np.load(cache_root / "y23.npy")
    X = np.load(cache_root / "X23.npy", mmap_mode="r")
    print(f"缓存就绪：{len(E):,} 片段", flush=True)

    config = EntityStratifiedSamplerConfig(n_pos=args.n_pos, n_neg=args.n_neg)
    sampler = EntityStratifiedSampler(E, I, M, T, y, config)

    checkpoint_path = Path(args.checkpoint).resolve()
    payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    trained = LocalFullMLP(aggregate=True)
    trained.load_state_dict(payload["model"])
    trained.eval()
    torch.manual_seed(args.seed)
    untrained = LocalFullMLP(aggregate=True)
    untrained.eval()
    print(f"加载检查点：{checkpoint_path}", flush=True)

    rng = np.random.default_rng(args.seed)
    ratios_trained = []
    ratios_untrained = []
    invariant_records = []
    bag_policy_report = None

    for repeat in range(12):
        batch = sampler.sample(rng)
        rows = _cap_segments_per_entity(batch["segment_rows"], E[batch["segment_rows"]], max_segments=8)
        idx = np.asarray(I[rows])[:, :128]
        valid_np = np.asarray(M[rows])[:, :128] > 0
        values = torch.from_numpy(np.asarray(X[idx.reshape(-1)])).reshape(len(rows), 128, 83)
        valid = torch.from_numpy(valid_np)

        entity_raw = E[rows]
        unique_entities, segment_owner_np = np.unique(entity_raw, return_inverse=True)
        segment_owner = torch.from_numpy(segment_owner_np.astype(np.int64))
        entity_is_positive = torch.from_numpy(
            np.isin(unique_entities, batch["positive_entities"])
        )
        entity_chain_length = torch.from_numpy(sampler.flows_per_entity[unique_entities])

        for model, bucket in ((trained, ratios_trained), (untrained, ratios_untrained)):
            params = [p for p in model.parameters() if p.requires_grad]
            logits = model(values, valid)
            flow_labels = torch.from_numpy(y[idx.reshape(-1)]).reshape(len(rows), 128)
            flow_loss = torch.nn.functional.binary_cross_entropy_with_logits(
                logits[valid], flow_labels[valid]
            )

            entity_scores, _src = prefix_scores(logits, valid, segment_owner)
            pos_scores = entity_scores[entity_is_positive]
            neg_scores = entity_scores[~entity_is_positive]
            pairwise = torch.nn.functional.softplus(neg_scores.unsqueeze(0) - pos_scores.unsqueeze(1))
            n_neg = neg_scores.numel()
            k_cvar = max(1, int(np.ceil(args.beta * n_neg)))

            xi_plain = torch.zeros(pos_scores.numel(), 1)
            loss_plain, _diag_plain = cvar_pauc_loss(pos_scores, neg_scores, [n_neg], xi_plain)
            xi_cvar = _quantile_init_xi(pairwise, k_cvar)
            loss_cvar, diag_cvar = cvar_pauc_loss(pos_scores, neg_scores, [k_cvar], xi_cvar)

            g_f = _flat_grad(flow_loss, params)
            g_r_plain = _flat_grad(loss_plain, params)
            g_r_cvar = _flat_grad(loss_cvar, params)
            norm_f = float(g_f.norm())
            norm_r_plain = float(g_r_plain.norm())
            norm_r_cvar = float(g_r_cvar.norm())
            ratio = (norm_r_cvar / norm_r_plain) if norm_r_plain > 0 else float("inf")
            bucket.append(ratio)

            if model is trained and repeat == 0:
                bag_config = BagPolicyConfig(
                    active_policy="causal_prefix_truncation",
                    truncate_length=args.truncate_length,
                    num_length_buckets=4,
                )
                xi_bag = torch.zeros(pos_scores.numel(), 1)
                bag_result = bag_policy_diagnostics(
                    logits,
                    valid,
                    segment_owner,
                    entity_is_positive,
                    entity_chain_length,
                    [k_cvar],
                    xi_bag,
                    bag_config,
                )
                bag_policy_report = {
                    name: info["loss_value"] for name, info in bag_result["policies"].items()
                }

            if model is trained:
                invariant_records.append(
                    {
                        "norm_f": norm_f,
                        "norm_r_cvar": norm_r_cvar,
                        "ratio": ratio,
                        "active_rate": diag_cvar["per_budget_active_rate"],
                        "k_cvar": k_cvar,
                        "n_neg": n_neg,
                    }
                )

        print(
            f"批 {repeat + 1}/12  已训练比值={ratios_trained[-1]:.6g}  "
            f"随机初始化比值={ratios_untrained[-1]:.6g}",
            flush=True,
        )

    median_trained = float(np.median(ratios_trained))
    median_untrained = float(np.median(ratios_untrained))
    print("=== 中位数结果 ===", flush=True)
    print(f"已训练收敛 CVaR/普通梯度范数比 中位数 = {median_trained:.6g}", flush=True)
    print(f"随机初始化 CVaR/普通梯度范数比 中位数 = {median_untrained:.6g}", flush=True)
    print(f"探针脚本参照值：16.61（收敛）/ 1.30（随机初始化）", flush=True)
    if bag_policy_report is not None:
        print(f"袋处置并行诊断（截断长度={args.truncate_length}）: {bag_policy_report}", flush=True)

    order_match = median_trained / 16.61
    print(f"本模块/探针比值 = {order_match:.4g}（阻断条件：差一个数量级以上，即 <1.661 或 >166.1）", flush=True)
    print("CH3_FT_ENTITY_RANKING_LOSS_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
