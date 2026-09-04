# -*- coding: utf-8 -*-
"""α 可微性实证检验：对生产实现 tail_aggregate 直接反传，看 α.grad。

判据（预注册，写于运行之前）：
  H0（文档 §五之二 的硬伤主张成立）：α.grad 为 None 或恒为 0，
      且 S_e 作为 α 的函数是分段常数（阶梯）。
  H1（硬伤不成立）：α.grad 非零且随 α 连续变化。

不创建 SwanLab 身份，不读任何真实数据，纯合成输入，CPU。
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

from ch3_ft_entity_ranking_loss import tail_aggregate  # noqa: E402

torch.manual_seed(0)

# 合成：3 个实体，袋大小 m = [2, 9, 511]（取自文档 §五之一 的实测分位点 P50/P90/P99）
BAGS = [2, 9, 511]
flow_entity = torch.cat(
    [torch.full((m,), i, dtype=torch.long) for i, m in enumerate(BAGS)]
)
n = flow_entity.numel()
flow_valid = torch.ones(n, dtype=torch.bool)
base_scores = torch.randn(n, dtype=torch.float32)


def run(alpha_value: float, requires_grad: bool = True):
    alpha = torch.tensor(alpha_value, dtype=torch.float32, requires_grad=requires_grad)
    scores = base_scores.clone().requires_grad_(True)
    out = tail_aggregate(scores, flow_valid, flow_entity, len(BAGS), alpha)
    S = out["entity_scores"]
    loss = S.sum()
    loss.backward()
    return alpha, scores, S, out


print("=" * 78)
print("检验 1：α 作为 requires_grad 张量，反传后 α.grad 是什么")
print("=" * 78)
alpha, scores, S, out = run(0.5)
print(f"  袋大小 m_e            = {out['m_per_entity'].tolist()}")
print(f"  k_e = ceil(0.5*m_e)   = {out['k_per_entity'].detach().tolist()}")
print(f"  k_per_entity.grad_fn  = {out['k_per_entity'].grad_fn}")
print(f"  entity_scores.grad_fn = {S.grad_fn}")
print(f"  α.grad                = {alpha.grad}")
print(f"  α.grad is None        = {alpha.grad is None}")
if alpha.grad is not None:
    print(f"  α.grad 绝对值         = {float(alpha.grad.abs()):.6e}")
print(f"  logit 侧 grad 非零数  = {int((scores.grad != 0).sum())} / {n}"
      f"   （证明反传本身通了，不是图断了）")

print()
print("=" * 78)
print("检验 2：S_e(α) 是否分段常数——α 在 (0,1] 上细扫，看 S_e 的取值")
print("=" * 78)
prev = None
jumps = 0
distinct = []
for i in range(1, 1001):
    a = i / 1000.0
    with torch.no_grad():
        o = tail_aggregate(base_scores, flow_valid, flow_entity, len(BAGS), a)
    cur = o["entity_scores"].clone()
    if prev is None or not torch.equal(prev, cur):
        jumps += 1
        distinct.append((a, o["k_per_entity"].tolist(), [round(float(x), 6) for x in cur]))
    prev = cur
print(f"  α 从 0.001 扫到 1.000（步长 0.001，共 1000 点）")
print(f"  S_e 取值发生变化的次数 = {jumps}（连续函数应为 ~1000，阶梯函数应远小于）")
print(f"  前 6 个台阶：")
for a, k, s in distinct[:6]:
    print(f"    α={a:.3f}  k_e={k}  S_e={s}")

print()
print("=" * 78)
print("检验 3：有限差分——α 的数值导数")
print("=" * 78)
for a in (0.10, 0.30, 0.50, 0.70):
    for eps in (1e-4, 1e-2):
        with torch.no_grad():
            lo = tail_aggregate(base_scores, flow_valid, flow_entity, len(BAGS), max(a - eps, 1e-6))["entity_scores"].sum()
            hi = tail_aggregate(base_scores, flow_valid, flow_entity, len(BAGS), min(a + eps, 1.0))["entity_scores"].sum()
        fd = float((hi - lo) / (2 * eps))
        print(f"  α={a:.2f}  eps={eps:.0e}  中心差分 dΣS/dα = {fd:+.6e}")

print()
print("=" * 78)
print("检验 4：单实体大袋（m=511）——最有利于「α 有梯度」的情形")
print("=" * 78)
m = 511
fe = torch.zeros(m, dtype=torch.long)
fv = torch.ones(m, dtype=torch.bool)
fs = torch.randn(m, dtype=torch.float32)
a1 = torch.tensor(0.5, requires_grad=True)
o1 = tail_aggregate(fs, fv, fe, 1, a1)
o1["entity_scores"].sum().backward()
print(f"  m=511, k_e={o1['k_per_entity'].item():.0f}, α.grad = {a1.grad}")

print()
print("=" * 78)
print("检验 5：优化器能否推动 α——把 α 交给 Adam 跑 200 步")
print("=" * 78)
a2 = torch.tensor(0.5, requires_grad=True)
opt = torch.optim.Adam([a2], lr=1e-2)
target = torch.tensor([2.0, 2.0, 2.0])
for step in range(200):
    opt.zero_grad()
    o = tail_aggregate(base_scores, flow_valid, flow_entity, len(BAGS), a2)
    loss = ((o["entity_scores"] - target) ** 2).mean()
    loss.backward()
    opt.step()
    with torch.no_grad():
        a2.clamp_(1e-6, 1.0)
print(f"  初值 α=0.500000  →  200 步 Adam 后 α={float(a2):.6f}")
print(f"  位移 = {abs(float(a2) - 0.5):.6e}")
print()
print("结论行：ALPHA_GRAD_IS_ZERO =",
      (alpha.grad is None) or bool((alpha.grad == 0).all()))
