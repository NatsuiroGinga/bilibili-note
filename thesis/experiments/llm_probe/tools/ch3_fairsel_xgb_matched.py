# -*- coding: utf-8 -*-
"""把 XGBoost 基线的 Lp 聚合口径对齐到新协议 C11 学到的 p，做同 p 比较。

背景：ch3-xgb-entity 的「实体 AP(Lp)=0.531917 / DR@4%FPR(Lp)=0.816489」是**借用冻结 C11 的
p=1.223554** 算出来的（XGBoost 自己没有学得的 Lp 指数）。新协议下 C11 的 p 变成 1.056217，
再拿 p=1.223554 的 XGB 数字对比就不是同口径。本脚本用同一 p 重算 XGB，并顺带做 p 敏感性。

只读 CPU 作业：读 ch3-xgb-entity/scores_xgb.npy（只读）与 dijk-repro/cache，
产物写 ch3-2x2-fairsel/xgb_matched_p.json。不训练、不创建运行身份、不改任何既有目录。

聚合与判据逐字复刻 ch3_full.py 第 213-240 行（含末尾 .astype(np.float32)）。
"""
import json
import time

import numpy as np
from sklearn.metrics import average_precision_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
XGBD = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-entity"
FAIR = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-2x2-fairsel"
P_FROZEN = 1.2235541820526123      # 冻结 C11 的 p（XGB 已发布 Lp 数字所用）
P_NEW = 1.056217                   # 新协议 C11 选中 epoch 10 的 p
TARGET_FPR = 0.04

y24 = np.load(f"{CACHE}/y24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = int(ent24.max()) + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
assert N_ENT == 47115 and int(ent_lab.sum()) == 752
del key24, s24, d24
log(f"实体 {N_ENT:,} 正例 {int(ent_lab.sum())}")


def ent_scores(sc, p=None, m=None):
    e, s = (ent24, sc) if m is None else (ent24[m], sc[m])
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, e, s); return es
    num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
    np.add.at(num, e, np.clip(s, 1e-7, 1.0).astype(np.float64) ** p); np.add.at(cnt, e, 1.0)
    return np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


def ent_ap(es):
    ok = np.isfinite(es)
    return float(average_precision_score(ent_lab[ok], es[ok]))


def dr_at_fpr(es, target=TARGET_FPR):
    ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


# ---- 自检：用 p_frozen 必须重算出已发布的 0.531917 / 0.816489 ----
sx = np.load(f"{XGBD}/scores_xgb.npy")
e0 = ent_scores(sx, P_FROZEN)
a0, d0 = ent_ap(e0), dr_at_fpr(e0)
log(f"自检 p={P_FROZEN:.6f}: 实体AP={a0:.6f} DR={d0:.6f}（应为 0.531917 / 0.816489）")
assert abs(a0 - 0.531917) < 1e-5 and abs(d0 - 0.816489) < 1e-5, "自检失败，聚合口径未对齐"

OUT = {"xgb": {}, "c11_new": {}}
for tag, p in [("max", None), ("p_frozen_1.223554", P_FROZEN), ("p_new_1.056217", P_NEW),
               ("p_0.8", 0.8), ("p_1.0", 1.0), ("p_1.5", 1.5), ("p_2.0", 2.0)]:
    es = ent_scores(sx, p)
    OUT["xgb"][tag] = {"ent_ap": ent_ap(es), "dr_at_4pct_fpr": dr_at_fpr(es)}
    log(f"XGB {tag:>20}: 实体AP={OUT['xgb'][tag]['ent_ap']:.6f} DR@4%FPR={OUT['xgb'][tag]['dr_at_4pct_fpr']:.6f}")
del sx, e0

# ---- 新协议 C11：从落盘分数重算，核对与主脚本一致，并做同样的 p 敏感性 ----
sc = np.load(f"{FAIR}/scores_C11.npy"); seen = np.load(f"{FAIR}/seen_C11.npy")
log(f"新协议 C11 覆盖率={seen.mean():.6f} 逐流AP={average_precision_score(y24[seen], sc[seen]):.6f}（主脚本 0.291843）")
for tag, p in [("max", None), ("p_new_1.056217", P_NEW), ("p_frozen_1.223554", P_FROZEN),
               ("p_0.8", 0.8), ("p_1.0", 1.0), ("p_1.5", 1.5), ("p_2.0", 2.0)]:
    es = ent_scores(sc, p, seen)
    OUT["c11_new"][tag] = {"ent_ap": ent_ap(es), "dr_at_4pct_fpr": dr_at_fpr(es)}
    log(f"C11新 {tag:>20}: 实体AP={OUT['c11_new'][tag]['ent_ap']:.6f} DR@4%FPR={OUT['c11_new'][tag]['dr_at_4pct_fpr']:.6f}")

m = "p_new_1.056217"
OUT["matched_gap"] = {
    "p": P_NEW,
    "ent_ap_c11_minus_xgb": OUT["c11_new"][m]["ent_ap"] - OUT["xgb"][m]["ent_ap"],
    "dr_c11_minus_xgb": OUT["c11_new"][m]["dr_at_4pct_fpr"] - OUT["xgb"][m]["dr_at_4pct_fpr"],
    "ent_ap_c11_minus_xgb_max": OUT["c11_new"]["max"]["ent_ap"] - OUT["xgb"]["max"]["ent_ap"],
    "dr_c11_minus_xgb_max": OUT["c11_new"]["max"]["dr_at_4pct_fpr"] - OUT["xgb"]["max"]["dr_at_4pct_fpr"]}
log("=" * 90)
log(f"同 p={P_NEW} 口径：实体AP 差 {OUT['matched_gap']['ent_ap_c11_minus_xgb']:+.6f}  "
    f"DR 差 {OUT['matched_gap']['dr_c11_minus_xgb']:+.6f}")
log(f"max 口径（与 p 无关）：实体AP 差 {OUT['matched_gap']['ent_ap_c11_minus_xgb_max']:+.6f}  "
    f"DR 差 {OUT['matched_gap']['dr_c11_minus_xgb_max']:+.6f}")
json.dump(OUT, open(f"{FAIR}/xgb_matched_p.json", "w"), ensure_ascii=False, indent=2)
log(f"已存 {FAIR}/xgb_matched_p.json，总耗时 {(time.time()-T0)/60:.1f} 分")
