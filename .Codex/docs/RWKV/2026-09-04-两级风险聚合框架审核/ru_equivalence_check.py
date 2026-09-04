# -*- coding: utf-8 -*-
"""E6：主代理对文献代理 Q1 结论的**独立复核**（不接受代理自报）。

文献代理称：待审插值算子 ≡ Rockafellar-Uryasev (2002) 式 (25) 在等概率经验分布下的代入。
本脚本**照式 (25) 的字面形式独立实现一遍**，与待审算子逐位对拍。
若两者在随机样本上逐位相等，则该算子不是新的。

RU 式 (25)（φ 是 α-CVaR，α 是**置信水平**，损失升序 z_1 < … < z_N，概率 p_k）：

    φ_α = 1/(1−α) · [ ( Σ_{k=1}^{k_α} p_k − α ) · z_{k_α} + Σ_{k=k_α+1}^{N} p_k · z_k ]

    其中 k_α 由式 (23) 唯一确定： Σ_{k=1}^{k_α} p_k ≥ α > Σ_{k=1}^{k_α−1} p_k
"""
import math
import torch

torch.manual_seed(20260904)


def proposed_operator(scores, alpha):
    """待审文档 §二 的算子（soft_k_probe.py 字面写法）。"""
    m = scores.numel()
    s, _ = torch.sort(scores, descending=True)
    t = torch.clamp(alpha * m, min=1.0, max=float(m))
    k = int(torch.floor(t))
    f = t - k
    head = s[:k].sum()
    tail = s[k] * f if k < m else torch.zeros((), dtype=s.dtype)
    return (head + tail) / t


def ru_eq25(scores, tail_fraction):
    """RU (2002) 式 (25) 的字面实现，等概率 p_k = 1/m，置信水平 α = 1 − tail_fraction。

    完全按论文口径写：损失**升序**，用式 (23) 定 k_α，不引用待审算子的任何中间量。
    """
    m = scores.numel()
    z, _ = torch.sort(scores, descending=False)          # 升序，论文口径
    p = 1.0 / m
    conf = 1.0 - tail_fraction                            # 论文的 α
    # 式 (23)：最小的 k 使 k·p >= conf
    k_alpha = None
    for k in range(1, m + 1):
        if k * p >= conf - 1e-15 and (k - 1) * p < conf - 1e-15:
            k_alpha = k
            break
    if k_alpha is None:
        k_alpha = m
    lead = (k_alpha * p - conf) * z[k_alpha - 1]          # 1-indexed → 0-indexed
    rest = z[k_alpha:].sum() * p
    return (lead + rest) / (1.0 - conf)


"""判据说明：两份实现的求和顺序与除数写法不同（`/t` 对 `/(1−conf)`），
故不能要求逐位相同——那是浮点结合律的问题，不是数学等价性的问题。
正确判据是**相对误差落在 float64 的 ULP 量级**（`≤ 8 eps ≈ 1.8e-15`）。"""
EPS = 2.220446049250313e-16
TOL = 8 * EPS

print("对拍：待审算子 vs RU (2002) 式 (25) 的独立实现（float64，判据为 ULP 量级）")
print(f"{'m':>5} {'α(尾部比例)':>12} {'待审算子':>22} {'RU 式(25)':>22} {'相对误差':>11} {'ULP 内':>7}")
worst = 0.0
bad = 0
checked = 0
for m in (3, 4, 5, 7, 9, 16, 33, 64, 101):
    s = torch.randn(m, dtype=torch.float64)
    for a in (0.1, 0.2, 0.25, 1 / 3, 0.4, 0.5, 0.6, 0.75, 0.9):
        if a * m < 1.0:
            continue                                       # 下夹区，RU 的 CVaR 无对应（尾部不足一个样本）
        checked += 1
        lhs = float(proposed_operator(s, torch.tensor(a, dtype=torch.float64)))
        rhs = float(ru_eq25(s, a))
        rel = abs(lhs - rhs) / max(abs(lhs), abs(rhs), 1e-12)
        worst = max(worst, rel)
        if rel > TOL:
            bad += 1
        if m in (3, 9, 101) and a in (0.25, 1 / 3, 0.5, 0.9):
            print(f"{m:>5} {a:>12.6f} {lhs:>22.15f} {rhs:>22.15f} "
                  f"{rel:>11.2e} {str(rel <= TOL):>7}")

print()
print(f"共对拍 {checked} 组 (m, α)；最大相对误差 = {worst:.3e}（判据 {TOL:.2e}）；"
      f"**超出 ULP 量级的组数 = {bad}**")
print()
if bad == 0:
    print("裁断：待审算子与 RU (2002) 式 (25) 在等概率经验分布下**在浮点精度内恒等**，")
    print("      全部差异是求和顺序造成的 1–2 ULP 舍入，不含任何归一化差异。")
    print("      ⟹ 该算子不是新的，是 CVaR 离散样本定义的直接代入。文献代理的 Q1 结论**复核通过**。")
else:
    print("裁断：存在超出舍入量级的差异，文献代理的等价性主张需要重新核对。")
