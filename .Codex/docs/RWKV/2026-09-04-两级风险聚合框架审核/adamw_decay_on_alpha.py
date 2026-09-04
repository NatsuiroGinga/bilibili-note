# -*- coding: utf-8 -*-
"""E5：AdamW 的权重衰减单独作用在 α 上能走多远？——判据 3 会不会被假阳性触发。

生产优化器是 AdamW（ch3_ft_transformer_field_token_protocol_a.py:3139），
分组由 resolve_weight_decay_groups（同文件 :2545）按参数角色决定：
排除项只有 tokenizer.* / LayerNorm / *.bias / p_log。
一个名为 alpha 的标量参数**不在排除项里** ⟹ 落入 with_decay 组。

冻结候选（同文件 :225-244）：lr=1e-4，weight_decay=1e-5（候选一）
                            lr=1e-4，weight_decay=3.1622776601683794e-05（候选二）

判据 3（被审文档 §三）：证伪条件是「位移 < 1e-6」。
"""
import torch

LR = 1e-4
WDS = [("候选一 FT-Transformer-论文默认优化器", 1e-5),
       ("候选二 FT-Transformer-官方调参空间对数中位优化器", 3.1622776601683794e-05)]
ALPHA0 = 0.5
FALSIFY = 1e-6

print("梯度**恒为零**时，AdamW 的解耦权重衰减单独把 α 推离 0.5 多少？")
print(f"（判据 3 的证伪线是位移 < {FALSIFY:g}；超过它即判「α 确实移动」）\n")
print(f"{'优化器候选':>46} {'步数':>8} {'末值 α':>18} {'|位移|':>12} {'越过证伪线':>10}")
for name, wd in WDS:
    for steps in (1_000, 2_000, 5_000, 10_000, 50_000):
        a = torch.nn.Parameter(torch.tensor(ALPHA0, dtype=torch.float64))
        opt = torch.optim.AdamW([{"params": [a], "weight_decay": wd}], lr=LR)
        for _ in range(steps):
            opt.zero_grad(set_to_none=True)
            a.grad = torch.zeros_like(a)          # c=0 或 α 无信号的极端情形
            opt.step()
        disp = abs(float(a.detach()) - ALPHA0)
        print(f"{name:>46} {steps:>8} {float(a.detach()):>18.12f} {disp:>12.3e} "
              f"{'**是**' if disp >= FALSIFY else '否':>10}")

print()
print("对照：把 α 放进 without_decay 组（如同 p_log 的既有处置）")
for name, wd in WDS[:1]:
    a = torch.nn.Parameter(torch.tensor(ALPHA0, dtype=torch.float64))
    opt = torch.optim.AdamW([{"params": [a], "weight_decay": 0.0}], lr=LR)
    for _ in range(50_000):
        opt.zero_grad(set_to_none=True)
        a.grad = torch.zeros_like(a)
        opt.step()
    print(f"  weight_decay=0.0，50000 步，末值 α = {float(a.detach())!r}，"
          f"位移 = {abs(float(a.detach())-ALPHA0):.3e}")

print()
print("判读：若上表出现「**是**」，则判据 3 可被**零学习信号**满足，")
print("      它测的是 AdamW 的衰减，不是 α 学到了东西。")
