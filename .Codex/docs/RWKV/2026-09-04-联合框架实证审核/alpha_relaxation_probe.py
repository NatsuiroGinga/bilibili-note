# -*- coding: utf-8 -*-
"""回答追问：把硬 top-k 换成连续松弛后会怎样。

三问，逐一实测：
  Q1 连续松弛（RU/CVaR 形式）能否让 α 拿到非零梯度？
  Q2 该松弛是否需要 BER 侧的软化配合？（即 §2.3「互为前提」是否成立）
  Q3 松弛后 α→0 是否仍与 max 逐位相等？（四格 z1'=0 臂的正确性基石）

RU 恒等式：top-α 均值 = min_ξ { ξ + 1/(α·m) · Σ_t [l_t − ξ]_+ }
α 在其中是**连续系数** 1/α，不再经 ceil，故可微。
这与 BER 的 R_K = ξ + (1/K_eff)·Σ_n [L_pn − ξ]_+ 是**同一个算子**。
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch

TOOLS = Path(
    "/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819"
    "/thesis/experiments/llm_probe/tools"
)
sys.path.insert(0, str(TOOLS))

from ch3_ft_entity_ranking_loss import prefix_scores, tail_aggregate  # noqa: E402

torch.manual_seed(2)


def ru_tail_aggregate(logits, entity, num_entities, alpha, n_inner=200, lr=0.5):
    """ETA 的 RU 连续形式。ξ_e 由内层优化求解（detach），α 只经外层系数 1/α 出现。"""
    m = torch.zeros(num_entities).index_add_(0, entity, torch.ones_like(logits))
    with torch.no_grad():
        xi = torch.zeros(num_entities, requires_grad=True)
        opt = torch.optim.Adam([xi], lr=lr)
    for _ in range(n_inner):
        opt.zero_grad()
        with torch.enable_grad():
            excess = torch.clamp(logits.detach() - xi[entity], min=0.0)
            s = torch.zeros(num_entities).index_add_(0, entity, excess)
            obj = (xi + s / (alpha.detach() * m)).sum()
        obj.backward()
        opt.step()
    xi_star = xi.detach()
    excess = torch.clamp(logits - xi_star[entity], min=0.0)
    s = torch.zeros(num_entities).index_add_(0, entity, excess)
    return xi_star + s / (alpha * m)


BAGS = [9, 30, 511]
entity = torch.cat([torch.full((m,), i, dtype=torch.long) for i, m in enumerate(BAGS)])
logits = torch.randn(entity.numel(), dtype=torch.float32)

print("=" * 78)
print("Q1：连续松弛后 α 能否拿到非零梯度")
print("=" * 78)
a_hard = torch.tensor(0.5, requires_grad=True)
tail_aggregate(logits, torch.ones_like(entity, dtype=torch.bool), entity,
               len(BAGS), a_hard)["entity_scores"].sum().backward()
a_soft = torch.tensor(0.5, requires_grad=True)
ru_tail_aggregate(logits, entity, len(BAGS), a_soft).sum().backward()
print(f"  现行硬 top-k 实现   α.grad = {a_hard.grad}")
print(f"  RU 连续松弛         α.grad = {a_soft.grad}")
print(f"  → 松弛确实解锁梯度? {bool((a_soft.grad != 0).any())}")

print()
print("=" * 78)
print("Q2：解锁 α 是否需要 BER 软化配合（§2.3「互为前提」）")
print("=" * 78)
print("  上面 Q1 的 RU 松弛**完全没有涉及 BER**：损失是 S_e.sum()，")
print("  没有排序、没有 hinge、没有 ξ_{p,K}、没有 τ_K。α.grad 已非零。")
print(f"  ⟹ α 可微性是机制一**自身**的改写就能解决的，不需要机制二。")

print()
print("=" * 78)
print("Q3：松弛后 α→0 是否仍与 max 逐位相等（四格 z1'=0 臂的基石）")
print("=" * 78)
lg2 = logits.reshape(1, -1)
ref, _ = prefix_scores(lg2, torch.ones_like(lg2, dtype=torch.bool),
                       torch.zeros(1, dtype=torch.long))
print(f"  参照 max（prefix_scores） = {float(ref[0]):+.8f}")
ent0 = torch.zeros(entity.numel(), dtype=torch.long)
hard0 = tail_aggregate(logits, torch.ones_like(ent0, dtype=torch.bool), ent0, 1,
                       None)["entity_scores"]
print(f"  现行 α=None（k≡1）        = {float(hard0[0]):+.8f}"
      f"   逐位相等? {bool(torch.equal(ref, hard0))}")
for a in (0.2, 0.05, 0.01, 0.002):
    with torch.no_grad():
        v = ru_tail_aggregate(logits, ent0, 1, torch.tensor(a))
    print(f"  RU 松弛 α={a:<6}          = {float(v[0]):+.8f}"
          f"   逐位相等? {bool(torch.equal(ref, v))}   偏差={float((v-ref).abs().max()):.2e}")

print()
print("=" * 78)
print("附：m_e=2 的实体上 α 的可达行为（文档称此类占 67.8%）")
print("=" * 78)
print("  k_e = ceil(2α)：α∈(0,0.5] ⟹ k=1（=max）；α∈(0.5,1] ⟹ k=2（=mean）")
print("  即 m=2 的袋上 ETA 只有两种可达行为，二者之间没有「尾部」。")
two = torch.randn(2)
e2 = torch.zeros(2, dtype=torch.long)
for a in (0.10, 0.30, 0.50, 0.51, 0.80, 1.00):
    o = tail_aggregate(two, torch.ones(2, dtype=torch.bool), e2, 1, a)
    print(f"    α={a:.2f}  k_e={o['k_per_entity'].item():.0f}  "
          f"S_e={float(o['entity_scores']):+.6f}")
print(f"  参照：max={float(two.max()):+.6f}  mean={float(two.mean()):+.6f}")
