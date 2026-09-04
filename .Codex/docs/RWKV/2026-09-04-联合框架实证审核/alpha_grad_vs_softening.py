# -*- coding: utf-8 -*-
"""证伪 §2.3 第一条：「软化是 α 可学的前提」。

文档主张：α 学不动是因为硬计数下过半的步排序梯度为零（c_scaling_median=0），
          软化使活动集不再恒空，α 才有梯度可学。

可证伪推论：若该主张成立，则在一个**活动集 100% 非空**的排序损失下，α.grad 应非零。
本脚本构造三种活动率的损失，逐一实测 α.grad。

判据：三种情形 α.grad 全为 0 ⟹ 主张的因果链错误（症结是 ceil，不是活动集）。
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

from ch3_ft_entity_ranking_loss import cvar_pauc_loss, tail_aggregate  # noqa: E402

torch.manual_seed(1)

# 排序批构成照冻结配置：n_pos=2, n_neg=64；袋大小取实测分位点
N_POS, N_NEG = 2, 64
BAGS = [9] * N_POS + [9] * N_NEG          # 全部 m=9 → k_e=5，远离 k=1 退化
BUDGETS = [121, 606, 1213, 2426, 4853, 9706]
N_NEG_POOL = 121336

flow_entity = torch.cat(
    [torch.full((m,), i, dtype=torch.long) for i, m in enumerate(BAGS)]
)
n = flow_entity.numel()
flow_valid = torch.ones(n, dtype=torch.bool)
base_scores = torch.randn(n, dtype=torch.float32)


def alpha_grad_under(xi_value: float, label: str) -> None:
    """xi 越低活动集越大；xi=-1e4 使 [L_pn - xi]_+ 对全部 (p,n) 对活动。"""
    alpha = torch.tensor(0.5, dtype=torch.float32, requires_grad=True)
    scores = base_scores.clone().requires_grad_(True)
    out = tail_aggregate(scores, flow_valid, flow_entity, len(BAGS), alpha)
    S = out["entity_scores"]
    pos, neg = S[:N_POS], S[N_POS:]
    xi = torch.full((N_POS, len(BUDGETS)), xi_value, requires_grad=True)
    # K_eff 折算照 effective_budget 口径：K * n_neg / N⁻
    keff = [k * N_NEG / N_NEG_POOL for k in BUDGETS]
    loss, diag = cvar_pauc_loss(pos, neg, keff, xi)
    loss.backward()
    active = diag.get("active_pair_fraction", diag.get("active_fraction", "n/a"))
    ag = alpha.grad
    print(f"  {label}")
    print(f"      活动集诊断        = {active}")
    print(f"      loss              = {float(loss):.6f}")
    print(f"      α.grad            = {ag}  →  为零? {bool((ag == 0).all())}")
    print(f"      ξ.grad 非零数     = {int((xi.grad != 0).sum())}/{xi.numel()}"
          f"   （非零⟹排序梯度确实在流动）")
    print(f"      logit.grad 非零数 = {int((scores.grad != 0).sum())}/{n}")
    print()


print("=" * 78)
print("§2.3 第一条的证伪检验：活动率从 0 到 100%，α.grad 是否随之变化")
print("=" * 78)
print()
alpha_grad_under(1e4, "情形 A：ξ 极高 → 活动集恒空（对应实测 c_scaling_median=0）")
alpha_grad_under(0.0, "情形 B：ξ=0 → 部分活动（接近实测 C01 的工况）")
alpha_grad_under(-1e4, "情形 C：ξ 极低 → 活动集 100% 非空（文档设想的软化后工况）")

print("=" * 78)
print("对照：同一批上 α 用有限差分的真实敏感度（证明 S_e 确实随 α 变，只是不可微）")
print("=" * 78)
with torch.no_grad():
    for a in (0.4, 0.5, 0.6):
        o = tail_aggregate(base_scores, flow_valid, flow_entity, len(BAGS), a)
        print(f"  α={a}: k_e={o['k_per_entity'][0].item():.0f}, "
              f"S_e[0]={o['entity_scores'][0].item():+.6f}")
