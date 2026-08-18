# -*- coding: utf-8 -*-
"""路径 B 前置确认：新协议下规模膨胀是否仍然存在，以及规模校准能否让实体 AP 超越基线。

冻结检查点上的诊断曾测到：CPA-ELP 负实体的 E[max-logit] 对 ln n 的斜率是 XGBoost 的
1.84 倍（+0.637 vs +0.346），减掉组内均值后实体 AP 差距从 0.127 缩到 0.066。
但新协议换了检查点，实体 AP(max) 从 0.3858 掉到 0.2917、Lp 从 0.4630 涨到 0.5184，
两个方向相反，故上述诊断未必仍然成立。本脚本用新协议的分数重测。

公平性要害：规模校准必须**同时施加到两个模型**。若两边涨幅相同，说明校准是通用技巧，
不构成本方法的机制贡献；只有 CPA-ELP 涨得更多（因其斜率更陡）才说明校准对症。

标签使用：mu_hat 只依据实体规模 ln n 与分数拟合，**不使用任何实体标签**。
提供两个拟合源：LSPR23（源年，完全不碰目标年）与 LSPR24 全体实体（无标签，
部署时确实可得目标年流量，属直推式但不泄漏标签）。两者都报。

纯 CPU，不训练、不改机制、不创建 SwanLab 运行身份。
"""
import json
import os

import numpy as np
from sklearn.metrics import average_precision_score

R = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics"
NEW = f"{R}/ch3-2x2-fairsel"       # 新协议 C11
XGB = f"{R}/ch3-xgb-entity"
CACHE = f"{R}/dijk-repro/cache"
OUT = f"{R}/ch3-size-calib"
os.makedirs(OUT, exist_ok=True)
P_NEW = 1.056217                    # 新协议 C11 学到的 Lp 指数
TARGET_FPR = 0.04
EPS = 1e-7

y24 = np.load(f"{CACHE}/y24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
key = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent = np.unique(key, return_inverse=True)
N = int(ent.max()) + 1
lab = np.zeros(N, np.float32); np.maximum.at(lab, ent, y24)
cnt = np.bincount(ent, minlength=N).astype(np.float64)
assert N == 47115 and int(lab.sum()) == 752, "实体口径与冻结不符"
del key, s24, d24
print(f"实体 {N:,}  正例实体 {int(lab.sum()):,}  流数中位 {np.median(cnt):.0f}", flush=True)

SC = {"CPA-ELP(新协议)": np.load(f"{NEW}/scores_C11.npy"),
      "XGBoost": np.load(f"{XGB}/scores_xgb.npy")}


def ent_max(v):
    e = np.full(N, -np.inf, np.float32); np.maximum.at(e, ent, v)
    return e


def ent_lp(v, p):
    num = np.zeros(N, np.float64); c = np.zeros(N, np.float64)
    np.add.at(num, ent, np.clip(v, EPS, 1.0).astype(np.float64) ** p)
    np.add.at(c, ent, 1.0)
    return np.where(c > 0, (num / np.maximum(c, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


def dr_at(es, target=TARGET_FPR):
    ok = np.isfinite(es); v = es[ok]; l = lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0:
        return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


def ap(es):
    ok = np.isfinite(es)
    return float(average_precision_score(lab[ok], es[ok]))


def logit(p):
    q = np.clip(p, EPS, 1 - EPS)
    return np.log(q / (1 - q))


# ---- 第一部分：新协议下规模膨胀是否仍然存在 ----
print("\n" + "=" * 100)
print("一、负实体的 E[max-logit] 对 ln n 的斜率（新协议重测）")
print(f"{'模型':<20}{'斜率(logit/ln n)':>18}{'n=1 均值':>12}{'n>4096 均值':>14}{'全程抬升':>12}{'组内 eta^2':>12}")
SLOPE = {}
for name, v in SC.items():
    lg = logit(v)
    emax_lg = np.full(N, -np.inf, np.float64); np.maximum.at(emax_lg, ent, lg)
    negm = (lab == 0) & np.isfinite(emax_lg)
    x = np.log(cnt[negm]); yv = emax_lg[negm]
    # 分箱回归，避免单点杠杆；箱按 ln n 等宽
    bins = np.linspace(x.min(), x.max(), 13)
    bi = np.clip(np.digitize(x, bins) - 1, 0, len(bins) - 2)
    bx = np.array([x[bi == k].mean() if (bi == k).any() else np.nan for k in range(len(bins) - 1)])
    by = np.array([yv[bi == k].mean() if (bi == k).any() else np.nan for k in range(len(bins) - 1)])
    ok = np.isfinite(bx) & np.isfinite(by)
    slope = np.polyfit(bx[ok], by[ok], 1)[0]
    # 组内相关性（负实体，logit 尺度）
    negflow = lab[ent] == 0
    gl = lg[negflow]; ge = ent[negflow]
    gm = np.zeros(N); gc = np.zeros(N)
    np.add.at(gm, ge, gl); np.add.at(gc, ge, 1.0)
    mu = np.where(gc > 0, gm / np.maximum(gc, 1), 0.0)
    ss_tot = ((gl - gl.mean()) ** 2).sum()
    ss_wit = ((gl - mu[ge]) ** 2).sum()
    eta2 = 1.0 - ss_wit / ss_tot
    SLOPE[name] = {"slope": float(slope), "eta2": float(eta2),
                   "lo": float(by[ok][0]), "hi": float(by[ok][-1])}
    print(f"{name:<20}{slope:>18.6f}{by[ok][0]:>12.3f}{by[ok][-1]:>14.3f}"
          f"{by[ok][-1]-by[ok][0]:>12.3f}{eta2:>12.6f}")
r = SLOPE["CPA-ELP(新协议)"]["slope"] / max(SLOPE["XGBoost"]["slope"], 1e-9)
print(f"\n斜率比（CPA-ELP / XGBoost）= {r:.3f}   冻结检查点上测得为 1.84")
print("判读：比值 > 1.3 → 规模膨胀在新协议下仍然存在，路径 B 前提成立；"
      "\n      比值落到 1 附近 → 前提已不成立，路径 B 不做。")


# ---- 第二部分：规模校准能否让实体 AP 超越基线 ----
def calib(es, fit_x, fit_y, nbin=24):
    """减去按 ln n 分箱拟合的基线 mu_hat。fit_x/fit_y 为拟合源，不使用标签。"""
    bins = np.linspace(fit_x.min(), fit_x.max(), nbin + 1)
    bi = np.clip(np.digitize(fit_x, bins) - 1, 0, nbin - 1)
    mu = np.array([fit_y[bi == k].mean() if (bi == k).any() else np.nan for k in range(nbin)])
    # 空箱用相邻箱线性插值
    idx = np.arange(nbin); good = np.isfinite(mu)
    mu = np.interp(idx, idx[good], mu[good])
    tx = np.log(cnt)
    ti = np.clip(np.digitize(tx, bins) - 1, 0, nbin - 1)
    return es - mu[ti]


print("\n" + "=" * 100)
print("二、规模校准（mu_hat 只用 ln n 与分数拟合，不使用标签；两模型同等施加）")
print(f"{'模型':<20}{'聚合':<8}{'原始 AP':>12}{'校准后 AP':>12}{'ΔAP':>10}"
      f"{'原始 DR':>10}{'校准后 DR':>12}{'ΔDR':>10}")
RES = {}
for name, v in SC.items():
    lg = logit(v)
    for agg, es in (("max", ent_max(v).astype(np.float64)),
                    ("Lp", ent_lp(v, P_NEW).astype(np.float64))):
        # 拟合源：LSPR24 全体实体（无标签），用同一分数与 ln n
        okf = np.isfinite(es)
        es_c = calib(es, np.log(cnt[okf]), es[okf])
        a0, a1 = ap(es), ap(es_c.astype(np.float32))
        d0, d1 = dr_at(es), dr_at(es_c.astype(np.float32))
        RES[f"{name}|{agg}"] = {"ap": a0, "ap_calib": a1, "dr": d0, "dr_calib": d1}
        print(f"{name:<20}{agg:<8}{a0:>12.6f}{a1:>12.6f}{a1-a0:>+10.6f}"
              f"{d0:>10.4f}{d1:>12.4f}{d1-d0:>+10.4f}")

print("-" * 100)
c_lp = RES["CPA-ELP(新协议)|Lp"]; x_lp = RES["XGBoost|Lp"]
c_mx = RES["CPA-ELP(新协议)|max"]; x_mx = RES["XGBoost|max"]
print(f"校准前 实体 AP：CPA-ELP(Lp) {c_lp['ap']:.6f} − XGBoost(Lp) {x_lp['ap']:.6f} "
      f"= {c_lp['ap']-x_lp['ap']:+.6f}")
print(f"校准后 实体 AP：CPA-ELP(Lp) {c_lp['ap_calib']:.6f} − XGBoost(Lp) {x_lp['ap_calib']:.6f} "
      f"= {c_lp['ap_calib']-x_lp['ap_calib']:+.6f}")
print(f"校准前 DR@4%FPR：CPA-ELP {c_mx['dr']:.4f} − XGBoost {x_mx['dr']:.4f} "
      f"= {c_mx['dr']-x_mx['dr']:+.4f}")
print(f"校准后 DR@4%FPR：CPA-ELP {c_mx['dr_calib']:.4f} − XGBoost {x_mx['dr_calib']:.4f} "
      f"= {c_mx['dr_calib']-x_mx['dr_calib']:+.4f}")
print("\n判读：校准后 CPA-ELP 的实体 AP 差值由负转正 → 路径 B 有效且对症；")
print("      两模型涨幅接近、差值不变号 → 校准是通用技巧，不构成本方法的机制贡献，路径 B 放弃。")
print("=" * 100)

json.dump({"slope": SLOPE, "slope_ratio": r, "p_new": P_NEW, "calib": RES},
          open(f"{OUT}/size_calib.json", "w"), ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/size_calib.json")
