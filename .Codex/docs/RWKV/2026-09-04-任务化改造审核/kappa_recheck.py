"""复算 §2.6.2 的 κ 扫描，并把「β̃/β 依赖真实分布的哪一个量」显式分离出来。

三件事：
1. 复现文档表格（指数分布，均值 0.0039），确认主代理的扫描可复现；
2. 证明 β̃/β 在局部指数尾下只经 a = λ_loc/κ 依赖分布，λ_loc 是阈值处的局部衰减率；
3. 用 C01 真实收据检验「指数分布、均值 0.0039」这一构造本身。

只用 numpy 与标准库，CPU 秒级。运行：
  /opt/miniconda3/envs/rwkv/bin/python <本文件>
"""

import math

import numpy as np

# ---------------------------------------------------------------- 冻结常量
# 来源：configs/ch3-ft-c01-entity-ranking-cuda-formal-v1.json
BUDGETS = [121, 606, 1213, 2426, 4853, 9706]
NEG_POOL = 121336
BETAS = [k / NEG_POOL for k in BUDGETS]
PAIR_MEAN_EP8 = 0.003910887792673691  # C01 halfwidth 第 8 轮 pair_loss_batch_mean
PAIR_VAR_EP8 = 0.00026609637560695955  # 同轮 pair_loss_batch_var（逐步批均值的总体方差）
N_PAIR_PER_STEP = 2 * 64  # n_pos=2, n_neg=64


def survival_exp(t, lam):
    return math.exp(-lam * t)


def e_sigmoid_exp(s, lam, kappa):
    """E[sigma(kappa*(L-s))]，L ~ Exp(rate=lam) 在 [0, inf)，高精度数值积分。

    换元 u = kappa*(t-s)：E = (lam/kappa)*exp(-lam*s)*Int_{-kappa*s}^{inf} exp(-a*u)*sigma(u) du,
    a = lam/kappa。被积函数在 u 大时 ~ exp(-a*u)，u 小时 ~ exp((1-a)*u)，两端都指数收敛。
    """
    a = lam / kappa
    lo = -kappa * s
    hi = 60.0 / max(a, 1e-12)
    lo = max(lo, -60.0 / max(1.0 - a, 1e-12))
    n = 400001
    u = np.linspace(lo, hi, n)
    # 数值稳定的 log(sigma(u))
    log_sig = np.where(u >= 0, -np.log1p(np.exp(-np.clip(u, 0, 700))),
                       u - np.log1p(np.exp(np.clip(u, -700, 0))))
    integ = np.exp(np.clip(-a * u + log_sig, -700, 700))
    val = np.trapezoid(integ, u) if hasattr(np, "trapezoid") else np.trapz(integ, u)
    return a * math.exp(-lam * s) * val


def solve_threshold(beta, lam, kappa):
    """解 E[sigma(kappa*(L-s))] = beta，返回 s_tilde；单调递减，用二分。"""
    lo, hi = 0.0, 1.0
    while e_sigmoid_exp(hi, lam, kappa) > beta:
        hi *= 2.0
        if hi > 1e6:
            return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if e_sigmoid_exp(mid, lam, kappa) > beta:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def analytic_ratio(a):
    """局部指数尾下的闭式：beta_tilde/beta = sin(pi*a)/(pi*a)，a = lam_loc/kappa，0<a<1。"""
    if a <= 0:
        return 1.0
    if a >= 1:
        return float("nan")
    return math.sin(math.pi * a) / (math.pi * a)


def main():
    lam = 1.0 / PAIR_MEAN_EP8
    print("=" * 78)
    print("零、构造参数")
    print(f"  文档构造：指数分布，均值 = {PAIR_MEAN_EP8:.6g} -> lambda = {lam:.4f}")
    print(f"  六档 beta = {['%.3e' % b for b in BETAS]}")

    print("=" * 78)
    print("一、复现文档 §2.6.2 表格（最低档 beta = %.4e）" % BETAS[0])
    print(f"{'kappa':>8} {'a=lam/kappa':>12} {'数值 bt/b':>12} {'解析 sin/pi a':>14} {'带宽/均值':>10}")
    for kappa in (256.0, 1000.0, 1e4, 1e5):
        s_t = solve_threshold(BETAS[0], lam, kappa)
        ratio = survival_exp(s_t, lam) / BETAS[0]
        a = lam / kappa
        print(f"{kappa:>8.0f} {a:>12.5f} {ratio:>12.4f} {analytic_ratio(a):>14.4f} "
              f"{(1.0 / kappa) / PAIR_MEAN_EP8 * 100:>9.1f}%")

    print("=" * 78)
    print("二、kappa = 256 时的逐档 beta_tilde/beta（文档称 0.108 -> 0.255，档位不重排）")
    kappa = 256.0
    prev = -1.0
    for k, beta in zip(BUDGETS, BETAS):
        s_t = solve_threshold(beta, lam, kappa)
        bt = survival_exp(s_t, lam)
        print(f"  K={k:>5}  beta={beta:.5e}  s~={s_t:.6f}  beta~={bt:.5e}  bt/b={bt / beta:.4f}"
              f"  {'递增' if bt > prev else '**重排**'}")
        prev = bt

    print("=" * 78)
    print("三、beta_tilde/beta 只经 a = lam_loc/kappa 依赖分布：反解 kappa 要求")
    print("   (要求 bt/b >= 0.998 时 a <= a*，故 kappa >= a*^-1 * lam_loc)")
    target = 0.998
    lo, hi = 1e-6, 0.999
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if analytic_ratio(mid) > target:
            lo = mid
        else:
            hi = mid
    a_star = 0.5 * (lo + hi)
    print(f"   a* = {a_star:.6f}  ->  kappa >= {1.0 / a_star:.2f} * lam_loc")
    print(f"   文档取 lam_loc = 1/均值 = {lam:.1f}  ->  kappa >= {lam / a_star:.4g}（即文档的 1e4）")
    print("   若真实 lam_loc 落在下列各值，kappa 要求为：")
    for lam_loc in (1.0, 10.0, 100.0, 256.0, 1000.0, 5000.0):
        print(f"     lam_loc={lam_loc:>8.1f}  ->  kappa >= {lam_loc / a_star:>10.4g}"
              f"   （相对文档 1e4 差 {lam_loc / lam:>8.3g} 倍）")

    print("=" * 78)
    print("四、用真实收据检验「指数分布、均值 0.0039」这一构造本身")
    std_obs = math.sqrt(PAIR_VAR_EP8)
    # 若每步 128 个配对损失是同一指数分布的 iid 抽样，逐步批均值的标准差应为 mu/sqrt(128)
    std_exp_model = PAIR_MEAN_EP8 / math.sqrt(N_PAIR_PER_STEP)
    print(f"  实测逐步批均值标准差 = sqrt({PAIR_VAR_EP8:.6e}) = {std_obs:.6e}")
    print(f"  指数模型预测          = {PAIR_MEAN_EP8:.6e}/sqrt({N_PAIR_PER_STEP}) = {std_exp_model:.6e}")
    print(f"  实测/预测 = {std_obs / std_exp_model:.1f} 倍（方差比 {PAIR_VAR_EP8 / std_exp_model ** 2:.0f} 倍）")
    print(f"  实测 std/mean = {std_obs / PAIR_MEAN_EP8:.2f}；指数模型 = {1 / math.sqrt(N_PAIR_PER_STEP):.4f}")
    print("  末步实测批均值 = 3.3687e-06 = 轮均值的 1/%.0f" % (PAIR_MEAN_EP8 / 3.3687e-06))


if __name__ == "__main__":
    main()
