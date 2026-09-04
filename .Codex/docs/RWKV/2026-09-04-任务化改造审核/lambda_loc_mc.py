"""用蒙特卡洛复核 lambda_loc_generality.py 里唯一发散的一行（对数正态 s=3）。

该行数值积分带 IntegrationWarning，且 beta_tilde/beta 随 kappa 单调**增大**
（1.09 -> 1.47 -> 2.22），方向与「kappa -> inf 时收敛到 1」矛盾，疑为求积失败。
蒙特卡洛不依赖被积函数的光滑性，用同一组随机数（common random numbers）
使根求解稳定。

单进程、纯 numpy、N=2e7 分块，峰值内存 < 0.5 GB，秒级。
运行：/opt/miniconda3/envs/rwkv/bin/python <本文件>
"""

import math

import numpy as np
from scipy import optimize, stats

BETA = 121 / 121336
MEAN = 0.003910887792673691
N = 20_000_000
CHUNK = 2_000_000


def sample(dist, seed):
    rng = np.random.default_rng(seed)
    return dist.rvs(size=N, random_state=rng).astype(np.float64)


def e_sigmoid_mc(x, s, kappa):
    tot = 0.0
    for i in range(0, x.size, CHUNK):
        u = np.clip(kappa * (x[i:i + CHUNK] - s), -700, 700)
        tot += float(np.sum(1.0 / (1.0 + np.exp(-u))))
    return tot / x.size


def sf_mc(x, s):
    tot = 0
    for i in range(0, x.size, CHUNK):
        tot += int(np.count_nonzero(x[i:i + CHUNK] > s))
    return tot / x.size


def main():
    cases = {
        "对数正态 s=3": stats.lognorm(s=3.0, scale=MEAN * math.exp(-4.5)),
        "对数正态 s=2": stats.lognorm(s=2.0, scale=MEAN * math.exp(-2.0)),
    }
    for name, dist in cases.items():
        x = sample(dist, 20260904)
        s_star_theory = dist.ppf(1 - BETA)
        lam_loc = dist.pdf(s_star_theory) / BETA
        # 用样本自身的经验分位数，避免理论/经验不一致污染比值
        s_star = float(np.quantile(x, 1 - BETA))
        print("=" * 74)
        print("%s  N=%d" % (name, N))
        print("  理论 s* = %.6g   经验 s* = %.6g   lam_loc = %.4g" % (s_star_theory, s_star, lam_loc))
        print("  经验 sf(s*) = %.6e  (目标 beta = %.6e)" % (sf_mc(x, s_star), BETA))
        print("  %-10s %-12s %-14s %-16s %-10s" %
              ("kappa", "a=lam/kappa", "MC bt/b", "sin(pi a)/(pi a)", "相对差"))
        for mult in (10, 30, 100):
            kappa = mult * lam_loc
            g = lambda s: e_sigmoid_mc(x, s, kappa) - BETA  # noqa: E731
            lo, hi = s_star * 0.2, s_star * 5.0
            while g(lo) < 0:
                lo *= 0.5
                if lo < 1e-12:
                    break
            while g(hi) > 0:
                hi *= 2.0
                if hi > 1e6:
                    break
            s_t = optimize.brentq(g, lo, hi, xtol=1e-14, rtol=1e-13, maxiter=200)
            ratio = sf_mc(x, s_t) / BETA
            a = lam_loc / kappa
            pred = math.sin(math.pi * a) / (math.pi * a)
            print("  %-10.4g %-12.5f %-14.5f %-16.5f %-10.2e"
                  % (kappa, a, ratio, pred, abs(ratio - pred) / pred))
        del x


if __name__ == "__main__":
    main()
