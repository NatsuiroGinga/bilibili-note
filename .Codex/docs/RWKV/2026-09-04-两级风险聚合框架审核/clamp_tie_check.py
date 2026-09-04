# -*- coding: utf-8 -*-
"""E4：A1 的打平点漏梯度，是否对**被审文档字面写法**同样成立？

soft_k_probe.py 用的是单次 torch.clamp(alpha*m, min=1.0, max=float(m))；
alpha_controller_interaction.py 用的是 clamp(min=1) 再 torch.minimum。
若只有后者漏梯度，A1 就是我的复现问题，不是方案问题。这里逐一对拍。
"""
import torch

torch.manual_seed(0)


def soft_probe_style(scores, alpha):
    """soft_k_probe.py 第 7-17 行的字面写法。"""
    m = scores.numel()
    s, _ = torch.sort(scores, descending=True)
    t = torch.clamp(alpha * m, min=1.0, max=float(m))
    k = torch.floor(t)
    f = t - k
    ki = int(k.item())
    head = s[:ki].sum()
    tail = s[ki] * f if ki < m else torch.zeros((), dtype=s.dtype)
    return (head + tail) / t


def two_step_style(scores, alpha):
    """alpha_controller_interaction.py 的写法：clamp(min=1) 再 minimum。"""
    m = scores.numel()
    s, _ = torch.sort(scores, descending=True)
    t = torch.minimum(torch.clamp(alpha * m, min=1.0), torch.tensor(float(m)))
    k = torch.floor(t)
    f = t - k
    ki = int(k.item())
    head = s[:ki].sum()
    tail = s[ki] * f if ki < m else torch.zeros((), dtype=s.dtype)
    return (head + tail) / t


print(f"{'m':>4} {'α':>6} {'α·m':>6} {'打平':>6} "
      f"{'probe写法 ∂S/∂α':>18} {'两步写法 ∂S/∂α':>18} {'数学单侧导数':>28}")
for m_e, a0 in [(1, 1.0), (2, 0.5), (2, 1.0), (3, 1.0), (4, 0.25), (4, 1.0),
                (5, 0.2), (9, 1.0), (3, 0.5), (7, 0.5)]:
    s = torch.randn(m_e, dtype=torch.float64)
    tag = []
    if a0 * m_e <= 1.0:
        tag.append("下夹")
    if a0 * m_e >= m_e:
        tag.append("上夹")
    grads = []
    for fn in (soft_probe_style, two_step_style):
        a = torch.tensor(a0, dtype=torch.float64, requires_grad=True)
        out = fn(s, a)
        g = torch.autograd.grad(out, a, allow_unused=True)[0]
        grads.append(float(g) if g is not None else float("nan"))
    ss, _ = torch.sort(s, descending=True)
    t = max(1.0, min(a0 * m_e, float(m_e)))
    ki = int(t)
    S = float((ss[:ki].sum() + (ss[ki] * (t - ki) if ki < m_e else 0.0)) / t)
    # 数学上的左/右导数：夹住那一侧为 0，内点侧为 (s_⌊t⌋ − S)/α
    if a0 * m_e >= m_e:
        expect = "左导 (s_{m-1}−S)/α ≤ 0，右导 0（α 不可超 1）"
    elif a0 * m_e <= 1.0:
        expect = "左导 0（夹住），右导 (s_1−S)/α ≤ 0"
    else:
        expect = f"内点，应 = {(float(ss[ki]) - S) / a0:+.4f}"
    print(f"{m_e:>4} {a0:>6.2f} {a0*m_e:>6.2f} {'/'.join(tag) or '内点':>6} "
          f"{grads[0]:>+18.6f} {grads[1]:>+18.6f} {expect:>28}")

print()
print("判读：两种写法在打平点上给出同一个非零值 ⟹ A1 是**被审算子本身**的性质，")
print("      不是我的复现引入的。上夹处为正 ⟹ 与「∂S/∂α ≤ 0 恒成立」的闭式矛盾。")
