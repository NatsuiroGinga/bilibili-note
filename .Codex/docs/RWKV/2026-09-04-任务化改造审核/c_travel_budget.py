"""检验 §2.6.4 推荐的 c = 1e-5 是否给 xi 留下了够用的行程预算。

§2.6.5 自陈「最低档步长降至 9.97e-09，该档的收敛速度代价未评估」。本脚本评估它。

两条论证：
(A) 分布无关的行程上界。单步位移 = lr_K*|dL/dxi| = c*beta_K*(1/(Np|K|))*(n/K_eff - 1)
    <= c*beta_K*(1/(Np|K|))*(1/beta_K - 1) = (c/(Np|K|))*(1 - beta_K)。
    故 T 步内 |xi_T - xi_0| <= T*c*(1-beta_K)/(Np*|K|)，**六档同界**（lr_K ∝ beta_K 的本意）。
    与实测工作点水平比较即可判定够不够。
(B) 复刻生效路径的动力学模拟（沿用主代理 xi_lag.py 的正确梯度式与同款合成分数），
    比较标量 lr 与 lr_K = c*beta_K 两种策略下最低档的活动率与末段 xi。
    模拟只作设计依据，不作实验证据（与 §2.6.5 第二条同一边界）。

单进程、纯 numpy、秒级。运行：/opt/miniconda3/envs/rwkv/bin/python <本文件>
"""

import numpy as np

BUDGETS = [121, 606, 1213, 2426, 4853, 9706]
NEG_POOL, N_NEG, N_POS = 121336, 64, 2
NK = len(BUDGETS)
EFF = [k * N_NEG / NEG_POOL for k in BUDGETS]
BETAS = [k / NEG_POOL for k in BUDGETS]

# 实测锚点（ch3-ft-c01-entitybce-halfwidth-screening-v1）
XI_LEVEL_EP8 = 5.5309e-3   # 第 8 轮末步空活动集，loss == mean_{k,p} xi
STEPS_PER_EPOCH = 1000
EPOCHS = 10


def part_a():
    T = STEPS_PER_EPOCH * EPOCHS
    print("=" * 78)
    print("(A) 分布无关的行程上界：|xi_T - xi_0| <= T*c*(1-beta_K)/(Np*|K|)")
    print(f"    T = {T} 步（{EPOCHS} 轮 x {STEPS_PER_EPOCH} 步），实测工作点 mean xi = {XI_LEVEL_EP8:.4e}")
    print(f"{'c':>10} {'最低档行程上界':>16} {'/ 工作点':>10} {'判定':>28}")
    for c in (1e-5, 1.2e-4, 1e-3, 1e-2):
        bound = T * c * (1 - BETAS[0]) / (N_POS * NK)
        ratio = bound / XI_LEVEL_EP8
        if ratio < 1:
            verdict = "上界都到不了工作点"
        elif ratio < 5:
            verdict = "仅在全程满活动才勉强到"
        else:
            verdict = "有余量"
        print(f"{c:>10.1e} {bound:>16.4e} {ratio:>10.2f} {verdict:>28}")
    print("    注：该上界要求每步 128 对全部活动，实际远达不到（实测活动率 0.42%~4.3%）。")


def run_dynamics(lr_policy, steps=STEPS_PER_EPOCH * EPOCHS, seed=20260904):
    """沿用 xi_lag.py 的合成分数与正确梯度式；lr_policy 是 (NK,) 步长向量。"""
    rng = np.random.default_rng(seed)
    xi = np.zeros((N_POS, NK))
    eff = np.array(EFF)[None, :]
    act = np.zeros(NK)
    empty = 0
    for t in range(steps):
        sep = 3.0 * (t / steps) ** 0.6
        sp = rng.normal(sep, 1.0, N_POS)
        sn = rng.normal(0.0, 1.0, N_NEG)
        m = sn[None, :] - sp[:, None]
        L = np.log1p(np.exp(-np.abs(m))) + np.maximum(m, 0.0)  # softplus, 数值稳定
        nact = (L[:, :, None] > xi[:, None, :]).sum(axis=1)      # (N_POS, NK)
        if t >= steps * 2 // 3:
            act += nact.sum(axis=0) / (N_POS * N_NEG)
            empty += int(nact.sum() == 0)
        grad = (1.0 / (N_POS * NK)) * (1.0 - nact / eff)
        xi = xi - lr_policy[None, :] * grad
    n_tail = steps - steps * 2 // 3
    return act / n_tail, empty / n_tail, xi


def part_b():
    print("\n" + "=" * 78)
    print("(B) 动力学模拟（后 1/3 段统计）：活动率对 beta 的比值应接近 1")
    policies = {
        "现行标量 lr=1e-4": np.full(NK, 1e-4),
        "lr_K=c*beta_K, c=1e-5（文档推荐）": np.array([1e-5 * b for b in BETAS]),
        "lr_K=c*beta_K, c=1.2e-4（12 倍常数修正后）": np.array([1.2e-4 * b for b in BETAS]),
        "lr_K=c*beta_K, c=1e-2": np.array([1e-2 * b for b in BETAS]),
    }
    for name, lr in policies.items():
        rate, empty, xi = run_dynamics(lr)
        ratios = [r / b for r, b in zip(rate, BETAS)]
        print(f"\n  {name}")
        print(f"    空活动步率 = {empty:.3f}   末段 xi(档0) = {xi[0, 0]:.4e}  xi(档5) = {xi[0, 5]:.4e}")
        print("    活动率/beta 逐档 = " + "  ".join("%.3f" % r for r in ratios))
        print("    最低档活动率 = %.5f（目标 beta = %.5f，比值 %.1f）"
              % (rate[0], BETAS[0], ratios[0]))


def part_c():
    """(C) 在**实测活动率**下，c=1e-5 的逐步行程有多少。

    实测（第 8 轮 per_budget_active_rate_epoch_mean，活动率是 128 对中的比例，
    每正实体活动数 = rate * n_neg）。
    """
    rates = [0.004203125, 0.0096484375, 0.0135, 0.01925, 0.0288125, 0.0425390625]
    T = STEPS_PER_EPOCH * EPOCHS
    print("\n" + "=" * 78)
    print("(C) 实测活动率下的实际行程（c = 1e-5）")
    print(f"{'K':>6} {'实测活动率':>11} {'n/正实体':>10} {'|dL/dxi|':>11} "
          f"{'单步行程':>12} {'T=1e4 总行程':>14} {'/ 工作点 5.53e-3':>18}")
    c = 1e-5
    for k, b, e, r in zip(BUDGETS, BETAS, EFF, rates):
        n = r * N_NEG
        g = abs(1.0 - n / e) / (N_POS * NK)
        step = c * b * g
        print(f"{k:>6} {r:>11.6f} {n:>10.3f} {g:>11.4e} {step:>12.4e} "
              f"{step * T:>14.4e} {step * T / XI_LEVEL_EP8:>18.2e}")
    print("    最低档总行程 2.67e-05，只有工作点 5.53e-03 的 0.48%（差 207 倍，约 2 个数量级）。")
    print("    xi 因而停在初值 0 附近；此时 L_pn = softplus(.) > 0 恒成立，活动率 -> 1，")
    print("    与目标 beta = 9.97e-4 差约 1000 倍（与 (B) 模拟的 947 倍同量级）。")
    print("    注：上表用的是**当前 lr 下已达平衡的**活动率，属自洽性检验——")
    print("    它说明 c=1e-5 无法维持该平衡点，不是说 xi 从 0 出发时逐步行程就这么小。")


if __name__ == "__main__":
    part_a()
    part_b()
    part_c()
