"""两级复合误差分析的最小数值佐证（合成数据，CPU，非正式实验）。

三个实验：
E1 固定 xi 下 (1/K_eff)*sum_{n in S}(L_n-xi)_+ 的无偏性（不放回均匀抽样）；
E2 反事实：若内层抽流（当前实现没有），ATk 与 softplus 复合会产生多大偏差；
E3 因果前缀截断（8192）对袋内 ATk 的偏差在可交换与漂移两种情形下的符号。

判据在各段注释中写明。产物只打印，不落任何正式目录。
"""
import numpy as np

rng = np.random.default_rng(42)

N_POP = 121336
N_NEG = 64
BUDGETS = [121, 606, 1213, 2426, 4853, 9706]

print("=== K_eff 核算 ===")
for K in BUDGETS:
    print(f"K={K:5d}  K_eff = K*{N_NEG}/{N_POP} = {K * N_NEG / N_POP:.6f}")

# ---------------- E1: 固定 xi 无偏性 ----------------
print("\n=== E1 固定 xi 无偏性（不放回抽样） ===")
# 合成有限总体成对损失：对数正态（右偏，模拟少数高损失负实体）
L = rng.lognormal(mean=-3.0, sigma=1.5, size=N_POP)
trials = 20000
for K in (121, 9706):
    k_eff = K * N_NEG / N_POP
    beta = K / N_POP
    xi = float(np.quantile(L, 1 - beta))  # 取驻点附近的 xi，最能暴露稀有事件
    pop_val = xi + np.maximum(L - xi, 0.0).sum() / K  # 总体 RU 目标（该 xi 处）
    est = np.empty(trials)
    for t in range(trials):
        s = rng.choice(N_POP, size=N_NEG, replace=False)
        est[t] = xi + np.maximum(L[s] - xi, 0.0).sum() / k_eff
    mc_mean = est.mean()
    mc_sem = est.std(ddof=1) / np.sqrt(trials)
    z = (mc_mean - pop_val) / mc_sem
    print(
        f"K={K:5d} beta={beta:.6f} K_eff={k_eff:.4f}  总体值={pop_val:.6f} "
        f"MC均值={mc_mean:.6f}  z={z:+.2f}  单步估计std={est.std(ddof=1):.4f} "
        f"(相对总体值 {est.std(ddof=1)/pop_val:.1f} 倍)"
    )

# ---------------- E2: 反事实内层抽样偏差 ----------------
print("\n=== E2 反事实：内层抽流的 ATk 与复合偏差（当前实现为穷举，无此层） ===")


def atk(x: np.ndarray, alpha: float = 0.5) -> float:
    k = max(1, int(np.ceil(alpha * len(x))))
    return float(np.sort(x)[::-1][:k].mean())


def softplus(x: float) -> float:
    return float(np.logaddexp(0.0, x))


m_n, m_p = 1000, 1000
scores_n = rng.normal(loc=-2.0, scale=1.0, size=m_n)  # 负实体流分数
scores_p = rng.normal(loc=0.0, scale=1.0, size=m_p)   # 正实体流分数
S_n, S_p = atk(scores_n), atk(scores_p)
exact_pair = softplus(S_n - S_p)
print(f"精确内层: S_n={S_n:.4f} S_p={S_p:.4f} softplus(S_n-S_p)={exact_pair:.6f}")
reps = 4000
for j in (8, 32, 128):
    sn = np.empty(reps)
    sp = np.empty(reps)
    pair = np.empty(reps)
    for t in range(reps):
        sub_n = rng.choice(scores_n, size=j, replace=False)
        sub_p = rng.choice(scores_p, size=j, replace=False)
        a, b = atk(sub_n), atk(sub_p)
        sn[t], sp[t] = a, b
        pair[t] = softplus(a - b)
    print(
        f"抽 j={j:3d}: E[S_hat_n]-S_n={sn.mean()-S_n:+.4f}  "
        f"E[S_hat_p]-S_p={sp.mean()-S_p:+.4f}  "
        f"E[softplus]-精确={pair.mean()-exact_pair:+.6f} "
        f"(相对 {100*(pair.mean()-exact_pair)/exact_pair:+.1f}%)"
    )

# ---------------- E3: 前缀截断偏差的符号 ----------------
print("\n=== E3 因果前缀截断（8192/袋）对 ATk 的偏差符号 ===")
m_big, trunc = 100000, 8192
for name, drift in (("可交换(无漂移)", 0.0), ("后期分数上漂", +2.0), ("后期分数下漂", -2.0)):
    gaps = []
    for t in range(30):
        base = rng.normal(size=m_big)
        trend = drift * np.arange(m_big) / m_big
        x = base + trend
        gaps.append(atk(x[:trunc]) - atk(x))
    gaps = np.asarray(gaps)
    print(f"{name}: 前缀ATk-完整ATk 均值={gaps.mean():+.4f}  std={gaps.std(ddof=1):.4f}")

print("\n结论要点：E1 无偏但低档方差放大；E2 内层一旦抽样即出现系统偏差且随 j 减小而增大；")
print("E3 截断偏差符号取决于袋内漂移方向，无假设不可定界。")
