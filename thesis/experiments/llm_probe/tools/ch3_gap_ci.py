# -*- coding: utf-8 -*-
"""XGBoost 与 CPA-ELP 实体级差距的配对自助置信区间。

回答一个问题：实体 AP 落后 0.0689、DR@4%FPR 落后 0.1210，是真实差距还是
752 个正例实体上的抽样噪声。不训练、不改机制、不新增评价口径。

方法：以**实体**为重抽样单元做配对自助（两个模型在同一批重抽样实体上评价，
故差值的方差已扣除实体难度带来的共同波动）。每次重抽样内部重新确定
DR@4%FPR 的阈值，因为阈值本身依赖该次样本的负实体分布。

重抽样单元选实体而非流：第三章的决策单元是实体，指标也定义在实体上；
按流重抽样会破坏实体内部的流构成，得到的区间回答的是另一个问题。
"""
import json
import os

import numpy as np
from sklearn.metrics import average_precision_score

CH3 = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-full"
XGB = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-entity"
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-gap-ci"
os.makedirs(OUT, exist_ok=True)
P_LEARNED = 1.2235541820526123
TARGET_FPR = 0.04
B = 2000
SEED = 42

sc_c11 = np.load(f"{CH3}/scores_C11.npy")
sc_xgb = np.load(f"{XGB}/scores_xgb.npy")
y24 = np.load(f"{CACHE}/y24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
assert len(sc_c11) == len(sc_xgb) == len(y24), "两份分数与标签长度必须一致"

key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = int(ent24.max()) + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
assert N_ENT == 47115 and int(ent_lab.sum()) == 752, "实体口径与冻结不符"
del key24, s24, d24
print(f"实体 {N_ENT:,}  正例实体 {int(ent_lab.sum()):,}  自助次数 {B:,}", flush=True)


def ent_scores(sc, p=None):
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24, sc)
        return es
    num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
    np.add.at(num, ent24, np.clip(sc, 1e-7, 1.0).astype(np.float64) ** p)
    np.add.at(cnt, ent24, 1.0)
    return np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


# 两边都取各自最优的聚合算子：C11 用学到的 Lp，XGBoost 用它更强的 Lp（借 p）与 max 各算一版
ES = {"C11_Lp": ent_scores(sc_c11, P_LEARNED),
      "XGB_Lp": ent_scores(sc_xgb, P_LEARNED),
      "XGB_max": ent_scores(sc_xgb, None)}
del sc_c11, sc_xgb


def dr_at(v, l, target=TARGET_FPR):
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0:
        return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


point = {k: {"ap": float(average_precision_score(ent_lab, v)), "dr": dr_at(v, ent_lab)}
         for k, v in ES.items()}
print("点估计：", json.dumps({k: {m: round(x, 6) for m, x in d.items()}
                          for k, d in point.items()}, ensure_ascii=False), flush=True)

rng = np.random.default_rng(SEED)
pairs = [("XGB_Lp", "C11_Lp"), ("XGB_max", "C11_Lp")]
boot = {f"{a}−{b}": {"ap": [], "dr": []} for a, b in pairs}

for i in range(B):
    idx = rng.integers(0, N_ENT, N_ENT)          # 按实体重抽样，两模型共用同一批
    l = ent_lab[idx]
    if l.sum() < 2 or l.sum() == len(l):         # 极端重抽样样本无法定义 AP，跳过
        continue
    cur = {k: (float(average_precision_score(l, v[idx])), dr_at(v[idx], l)) for k, v in ES.items()}
    for a, b in pairs:
        boot[f"{a}−{b}"]["ap"].append(cur[a][0] - cur[b][0])
        boot[f"{a}−{b}"]["dr"].append(cur[a][1] - cur[b][1])
    if (i + 1) % 500 == 0:
        print(f"  自助 {i+1}/{B}", flush=True)

W = 104
print("\n" + "=" * W)
print("XGBoost 相对 CPA-ELP 的实体级优势：配对自助 95% 置信区间（重抽样单元 = 实体）")
print(f"{'比较':<24}{'指标':<12}{'点估计差':>12}{'自助均值':>12}{'95% CI':>26}{'XGB 更优占比':>14}")
res = {}
for k, d in boot.items():
    for m, name in (("ap", "实体 AP"), ("dr", "DR@4%FPR")):
        arr = np.asarray(d[m], np.float64)
        arr = arr[np.isfinite(arr)]
        lo, hi = np.percentile(arr, [2.5, 97.5])
        a, b = k.split("−")
        pt = point[a][m] - point[b][m]
        frac = float((arr > 0).mean())
        print(f"{k:<24}{name:<12}{pt:>12.6f}{arr.mean():>12.6f}"
              f"{f'[{lo:+.6f}, {hi:+.6f}]':>26}{frac:>14.4f}")
        res[f"{k}|{m}"] = {"point": pt, "boot_mean": float(arr.mean()),
                           "ci_lo": float(lo), "ci_hi": float(hi),
                           "frac_xgb_better": frac, "n_boot": int(len(arr))}
print("-" * W)
print("判读：区间不跨 0 且「XGB 更优占比」接近 1，说明差距不是抽样噪声，")
print("CPA-ELP 在实体级确实落后；区间跨 0 则当前证据不足以断言两者有差别。")
print("=" * W)

json.dump({"point": point, "bootstrap": res, "n_boot": B, "seed": SEED,
           "p_learned": P_LEARNED, "target_fpr": TARGET_FPR},
          open(f"{OUT}/gap_ci.json", "w"), ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/gap_ci.json")
