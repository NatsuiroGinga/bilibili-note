# -*- coding: utf-8 -*-
"""三条路径的逻辑自检：在已知真值的合成数据上验证公式实现是否正确。"""
import numpy as np
rng = np.random.default_rng(0)

def thr_at_fpr(scores, labels, target):
    neg = np.sort(scores[labels == 0])[::-1]
    return float(neg[min(int(len(neg)*target), len(neg)-1)])

def fpr_dr(scores, labels, thr):
    return float((scores[labels==0] >= thr).mean()), float((scores[labels==1] >= thr).mean())

print("═══ 检 1：thr_at_fpr 是否给出目标 FPR ═══")
for N in (1000, 46363):
    s = rng.random(N); l = np.zeros(N)
    t = thr_at_fpr(s, l, 0.04); f, _ = fpr_dr(s, l, t)
    print(f"  N={N:<7} 目标FPR=0.04  实测={f:.6f}  偏差={f-0.04:+.6f}")

print("\n═══ 检 2：BBSE 在「标签漂移」合成数据上应精确复原先验 ═══")
print("  构造：p(x|y) 完全不变，只改 π。BBSE 若实现正确，误差应 ~0")
def make(pi, n, seed):
    r = np.random.default_rng(seed)
    y = (r.random(n) < pi).astype(float)
    s = np.where(y==1, r.beta(6,2,n), r.beta(2,6,n))   # p(x|y) 固定
    return s, y
s_src, y_src = make(0.10, 400000, 1)
for pi_t in (0.0257, 0.05, 0.10):
    s_tgt, y_tgt = make(pi_t, 400000, 2)
    print(f"  目标真值 π={pi_t}")
    for f_op in (0.01, 0.05, 0.10, 0.30, 0.50):
        op = thr_at_fpr(s_src, y_src, f_op)
        tpr = float((s_src[y_src==1] >= op).mean()); fpr = float((s_src[y_src==0] >= op).mean())
        q = float((s_tgt >= op).mean())
        den = tpr - fpr
        pi_h = np.clip((q - fpr)/den, 0, 1) if abs(den)>1e-8 else np.nan
        print(f"    源FPR={f_op:<5} TPR={tpr:.4f} TPR-FPR={den:.4f} → π̂={pi_h:.6f} 误差={abs(pi_h-pi_t)/pi_t:.4f}")

print("\n═══ 检 3：TPR 饱和时 BBSE 是否病态（复现今晚的失败模式）═══")
def make_sep(pi, n, seed, sep=8.0):
    r = np.random.default_rng(seed)
    y = (r.random(n) < pi).astype(float)
    s = 1/(1+np.exp(-(r.normal(0,1,n) + sep*y)))       # 高度可分 → TPR 饱和
    return s, y
s2, y2 = make_sep(0.10, 400000, 3)
s3, y3 = make_sep(0.0257, 400000, 4)
for f_op in (0.01, 0.10, 0.30):
    op = thr_at_fpr(s2, y2, f_op)
    tpr = float((s2[y2==1]>=op).mean()); fpr = float((s2[y2==0]>=op).mean())
    q = float((s3>=op).mean()); den = tpr-fpr
    pi_h = np.clip((q-fpr)/den,0,1) if abs(den)>1e-8 else np.nan
    print(f"  源FPR={f_op:<5} TPR={tpr:.4f} den={den:.4f} q={q:.6f} → π̂={pi_h:.6f} 误差={abs(pi_h-0.0257)/0.0257:.4f}")
print("  说明：p(x|y) 不变时即使 TPR 饱和 BBSE 仍准；今晚 q<FPR 出负值，说明 p(x|y) 变了")

print("\n═══ 检 4：EM（Saerens 1998）实现是否正确 ═══")
def em_prior(scores, pi_s, iters=200):
    p = np.clip(scores.astype(np.float64), 1e-7, 1-1e-7); pi = pi_s
    for it in range(iters):
        w1 = (pi/pi_s)*p; w0 = ((1-pi)/(1-pi_s))*(1-p)
        new = float((w1/(w1+w0)).mean())
        if abs(new-pi) < 1e-12: break
        pi = new
    return pi, it+1
for pi_t in (0.0257, 0.05, 0.20):
    s_t, _ = make(pi_t, 400000, 10)
    pe, it = em_prior(s_t, 0.10)
    print(f"  真值 π={pi_t:<7} EM π̂={pe:.6f} 误差={abs(pe-pi_t)/pi_t:.4f}  迭代={it}")
print("  注意：EM 要求 scores 是「源先验下的后验概率」。若模型用 pos_weight 训练，")
print("        输出已非校准后验，EM 假设被违反——这是本课题的真实风险，必须实测。")

print("\n═══ 检 5：路径3 分位数校准的逻辑缺陷检查 ═══")
print("  问题：在「前缀实体分数」上取分位数，却应用到「全年实体分数」上。")
print("        同一实体在前缀里只聚合了早期流，全年聚合了全部流，两者分布不同。")
n_ent = 47115
r = np.random.default_rng(7)
n_flow = np.maximum(r.zipf(1.6, n_ent), 1)            # 重尾流数，中位≈2
base = r.beta(2, 30, n_ent)
def agg(k, p=1.2):
    kk = np.minimum(n_flow, k)
    noise = r.normal(0, 0.02/np.sqrt(kk))
    return np.clip(base + noise, 1e-6, 1)
S_pre = agg(3); S_full = agg(10**9)
print(f"  前缀分数 均值={S_pre.mean():.6f} 标准差={S_pre.std():.6f} 96%分位={np.quantile(S_pre,0.96):.6f}")
print(f"  全年分数 均值={S_full.mean():.6f} 标准差={S_full.std():.6f} 96%分位={np.quantile(S_full,0.96):.6f}")
thr = np.quantile(S_pre, 0.96)
print(f"  用前缀 96% 分位阈值套到全年 → 实际越阈率={float((S_full>=thr).mean()):.6f}（目标 0.04）")
print("  → 若两者分位数差异大，路径3 会系统性偏离目标 FPR。必须在真实数据上测这个差异，不能假设。")
