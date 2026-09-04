"""检验「beta_tilde/beta 只经 a = lam_loc/kappa 依赖分布」是否普遍成立。

若普遍成立，则 §2.6.2 缺的实测量收敛为**一个标量**（工作阈值处的局部衰减率），
最小取数方案就成立；若只对指数分布成立，则必须测整条尾巴。

取四族尾部形状完全不同的分布，在同一 beta 下算 beta_tilde/beta，
再与 sin(pi*a)/(pi*a) 比较，a = lam_loc/kappa，lam_loc = f(s*)/S(s*) 由该分布自身给出。

只用 numpy + scipy，CPU 秒级。
运行：/opt/miniconda3/envs/rwkv/bin/python <本文件>
"""

import math

import numpy as np
from scipy import integrate, optimize, stats

BETA = 121 / 121336  # 最低档 beta
MEAN = 0.003910887792673691  # C01 第 8 轮 pair_loss_batch_mean


def make_dists():
    """四族分布，全部缩放到均值 = MEAN，支撑 [0, inf)。"""
    out = {}
    # 1) 指数（文档的构造）
    out["指数 Exp"] = stats.expon(scale=MEAN)
    # 2) 对数正态，sigma=2（中等重尾）
    s = 2.0
    out["对数正态 s=2"] = stats.lognorm(s=s, scale=MEAN * math.exp(-s * s / 2))
    # 3) 对数正态，sigma=3（重尾，接近实测 std/mean=4.2 的形态）
    s = 3.0
    out["对数正态 s=3"] = stats.lognorm(s=s, scale=MEAN * math.exp(-s * s / 2))
    # 4) 韦布尔 c=0.4（次指数、重尾）
    c = 0.4
    scale = MEAN / math.gamma(1 + 1 / c)
    out["韦布尔 c=0.4"] = stats.weibull_min(c=c, scale=scale)
    # 5) 帕累托（幂律尾），alpha=2.5
    b = 2.5
    out["帕累托 a=2.5"] = stats.pareto(b=b, scale=MEAN * (b - 1) / b)
    return out


def e_sigmoid(dist, s, kappa):
    """E[sigma(kappa*(L-s))]，对分布做数值积分（分段以保精度）。"""
    def f(t):
        u = kappa * (t - s)
        return dist.pdf(t) / (1.0 + np.exp(-np.clip(u, -700, 700)))

    lo = max(dist.ppf(1e-14), 0.0)
    hi = dist.ppf(1 - 1e-14)
    # 在 s 附近（宽度 ~ 40/kappa）加密
    pts = sorted({lo, max(lo, s - 40 / kappa), s, min(hi, s + 40 / kappa), hi})
    total = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        if b <= a:
            continue
        val, _ = integrate.quad(f, a, b, limit=400)
        total += val
    return total


def solve_s_tilde(dist, beta, kappa):
    lo = dist.ppf(1 - min(0.5, beta * 200))
    hi = dist.ppf(1 - beta * 1e-6)
    g = lambda s: e_sigmoid(dist, s, kappa) - beta  # noqa: E731
    if g(lo) < 0 or g(hi) > 0:
        return None
    return optimize.brentq(g, lo, hi, xtol=1e-16, rtol=1e-14, maxiter=300)


def main():
    print("beta = %.6e   均值统一为 %.6e" % (BETA, MEAN))
    print("lam_loc := f(s*)/S(s*)，s* 是硬阈值（S(s*) = beta）\n")
    for name, dist in make_dists().items():
        s_star = dist.ppf(1 - BETA)
        lam_loc = dist.pdf(s_star) / BETA
        print("=" * 74)
        print("%-16s  s* = %.6g   lam_loc = %.4g   (1/均值 = %.4g)"
              % (name, s_star, lam_loc, 1 / MEAN))
        print("  %-10s %-12s %-14s %-14s %-10s" %
              ("kappa", "a=lam/kappa", "数值 bt/b", "sin(pi a)/(pi a)", "相对差"))
        for kappa in (10 * lam_loc, 30 * lam_loc, 100 * lam_loc):
            s_t = solve_s_tilde(dist, BETA, kappa)
            if s_t is None:
                print("  %-10.4g  求解失败" % kappa)
                continue
            ratio = dist.sf(s_t) / BETA
            a = lam_loc / kappa
            pred = math.sin(math.pi * a) / (math.pi * a)
            print("  %-10.4g %-12.5f %-14.5f %-14.5f %-10.2e"
                  % (kappa, a, ratio, pred, abs(ratio - pred) / pred))

    print("\n" + "=" * 74)
    print("判读：若各族的『数值 bt/b』都贴住 sin(pi a)/(pi a)，")
    print("      则 beta_tilde/beta 只经 lam_loc 依赖分布，实测一个标量即可定 kappa。")
    print("      并且 1 - bt/b ~ (pi*lam_loc/kappa)^2/6 = O(1/kappa^2)，不是 O(1/kappa)。")


if __name__ == "__main__":
    main()
