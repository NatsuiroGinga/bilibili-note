# -*- coding: utf-8 -*-
"""P2 可行性探针：1e-7 截断是否真的压住了实体 AP。

背景：实体聚合 `(Σ clip(s,1e-7,1)^p / n)^(1/p)` 里的 clip 下限，把大量低分流拉到同一常数。
实测 CPA-ELP 有 92.3% 的流落在该下限（XGBoost 78.6%）。

独立审核指出：「AP 不受截断影响」只在**并列块内没有正例实体**时成立。
实体流数中位数为 2，大量实体的 Lp 分数会恰好并列在 clip 常数上；
若并列块含正例实体，恢复数值保真会直接抬高实体 AP，否则只重排负例、AP 不动。

本脚本回答三个问题，全部只用已落盘分数，不重训：
  一、保存的分数里有多少被 float32 sigmoid 压到恰好 0.0（这部分信息在保存时已丢失，不可恢复）
  二、按当前 clip 算出的实体 Lp 分数，有多少实体恰好并列在下限上，其中有几个是正例实体
  三、把 clip 下限从 1e-7 依次降到 1e-12、1e-20，以及改用 log 空间精确计算，实体 AP 各是多少

第三问是探针，用于估计效果规模；正式采用时修法须事前定死、只评一次。

纯 CPU，不训练、不改机制、不创建 SwanLab 运行身份。
"""
import json
import os

import numpy as np
from sklearn.metrics import average_precision_score

R = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics"
CACHE = f"{R}/dijk-repro/cache"
OUT = f"{R}/ch3-trunc-probe"
os.makedirs(OUT, exist_ok=True)
P_NEW = 1.056217          # 新协议 C11 学到的 Lp 指数
TARGET_FPR = 0.04

SRC = {"CPA-ELP(新协议)": f"{R}/ch3-2x2-fairsel/scores_C11.npy",
       "XGBoost": f"{R}/ch3-xgb-entity/scores_xgb.npy"}

y24 = np.load(f"{CACHE}/y24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
key = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent = np.unique(key, return_inverse=True)
N = int(ent.max()) + 1
lab = np.zeros(N, np.float32); np.maximum.at(lab, ent, y24)
assert N == 47115 and int(lab.sum()) == 752, "实体口径与冻结不符"
del key, s24, d24
print(f"实体 {N:,}  正例实体 {int(lab.sum()):,}", flush=True)


def ent_lp_clip(v, p, floor):
    """现行做法：先 clip 到 floor，再算幂平均。"""
    num = np.zeros(N, np.float64); c = np.zeros(N, np.float64)
    np.add.at(num, ent, np.clip(v, floor, 1.0).astype(np.float64) ** p)
    np.add.at(c, ent, 1.0)
    return np.where(c > 0, (num / np.maximum(c, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


def ent_lp_logspace(v, p):
    """log 空间精确计算：exp((logsumexp(p*log s) - log n)/p)，只对 s>0 的流。

    s 恰好为 0 的流无法取 log，这部分信息在保存时已经丢失，
    只能以 float32 最小正规数替代，并在报告中标出其占比。
    """
    tiny = np.finfo(np.float32).tiny          # 约 1.18e-38
    vv = np.where(v > 0, v, tiny).astype(np.float64)
    lg = np.log(vv) * p
    m = np.full(N, -np.inf, np.float64); np.maximum.at(m, ent, lg)
    acc = np.zeros(N, np.float64); c = np.zeros(N, np.float64)
    np.add.at(acc, ent, np.exp(lg - m[ent]))
    np.add.at(c, ent, 1.0)
    lse = m + np.log(np.maximum(acc, 1e-300))
    return np.exp((lse - np.log(np.maximum(c, 1))) / p).astype(np.float32)


def dr_at(es):
    ok = np.isfinite(es); vv = es[ok]; l = lab[ok]
    neg = np.sort(vv[l == 0])[::-1]
    thr = neg[min(int(len(neg) * TARGET_FPR), len(neg) - 1)]
    return float((vv[l == 1] >= thr).mean())


def ap(es):
    ok = np.isfinite(es)
    return float(average_precision_score(lab[ok], es[ok]))


RES = {}
for name, path in SRC.items():
    v = np.load(path)
    n_zero = int((v == 0.0).sum())
    n_below = int((v < 1e-7).sum())
    print("\n" + "=" * 96)
    print(f"[{name}]  流数 {len(v):,}")
    print(f"  一、保存时已丢失：分数恰好为 0.0 的流 {n_zero:,}（{n_zero/len(v):.4%}）—— 这部分不可恢复")
    print(f"     低于 1e-7 但大于 0 的流 {n_below-n_zero:,}（{(n_below-n_zero)/len(v):.4%}）—— 这部分可恢复")

    es0 = ent_lp_clip(v, P_NEW, 1e-7)
    floor_val = np.float32(1e-7)
    tie = np.isclose(es0, floor_val, rtol=0, atol=np.float32(1e-12))
    tie_pos = int(lab[tie].sum())
    print(f"  二、按 1e-7 算出的实体分数中，恰好并列在下限的实体 {int(tie.sum()):,}，"
          f"其中正例实体 {tie_pos}")
    if tie_pos == 0:
        print("     并列块内无正例实体 → 恢复保真只会重排负例，实体 AP 预期不动")
    else:
        print(f"     并列块内含 {tie_pos} 个正例实体 → 恢复保真有望直接抬高实体 AP")

    row = {"n_flow": len(v), "n_zero": n_zero, "n_below_1e7": n_below,
           "tie_at_floor": int(tie.sum()), "tie_pos": tie_pos, "variants": {}}
    print(f"  三、不同数值处理下的实体指标（p={P_NEW}）")
    print(f"     {'处理方式':<24}{'实体 AP':>12}{'ΔAP':>11}{'DR@4%FPR':>12}")
    base_ap = ap(es0)
    for tag, es in (("clip 1e-7（现行）", es0),
                    ("clip 1e-12", ent_lp_clip(v, P_NEW, 1e-12)),
                    ("clip 1e-20", ent_lp_clip(v, P_NEW, 1e-20)),
                    ("log 空间精确", ent_lp_logspace(v, P_NEW))):
        a, d = ap(es), dr_at(es)
        row["variants"][tag] = {"ap": a, "dr": d}
        print(f"     {tag:<24}{a:>12.6f}{a-base_ap:>+11.6f}{d:>12.4f}")
    RES[name] = row
    del v

print("\n" + "=" * 96)
c = RES["CPA-ELP(新协议)"]["variants"]; x = RES["XGBoost"]["variants"]
XGB_REF = 0.533104
print(f"XGBoost 基线（同 p 口径，clip 1e-7）= {XGB_REF:.6f}")
for tag in c:
    print(f"  {tag:<24} CPA-ELP {c[tag]['ap']:.6f}  vs  XGBoost {x[tag]['ap']:.6f}  "
          f"差 {c[tag]['ap']-x[tag]['ap']:+.6f}")
print("\n判读：若 log 空间精确计算下 CPA-ELP 的实体 AP 明显高于 clip 1e-7，"
      "\n      且差值向正方向移动，则 P2 值得作为正式修法（届时修法事前定死、只评一次）；"
      "\n      若各变体几乎不动，说明截断只压负例，P2 放弃。")
print("=" * 96)

json.dump({"p": P_NEW, "xgb_ref_clip1e7": XGB_REF, "results": RES},
          open(f"{OUT}/trunc_probe.json", "w"), ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/trunc_probe.json")
