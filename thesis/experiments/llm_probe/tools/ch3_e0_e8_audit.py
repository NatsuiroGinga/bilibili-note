# -*- coding: utf-8 -*-
"""E0 并列/饱和审计 + E8 max 聚合专属配对自助。

独立审核（2026-08-17）指出诊断存在两个必须先封死的问题，本脚本只回答这两个：

E0（门禁）：诊断称「max 对单调变换不变，故 0.127 的差距不可能由标定解释」。
  该论证只对**严格**递增变换成立。float32 下 sigmoid(x) 在 x 约 16.6 以上精确等于 1.0，
  而逐流 BCE 的 pos_weight=8.9438 恰好把自信样本推入饱和区。若大量实体的 max
  精确并列在同一个值上，AP 在并列组内退化为组内先验，且结果依赖并列的断开方式。
  这条通道不经过「标定」概念，却确实属于「输出变换而非排序」。
  判读：CPA-ELP 的 AP(max) 在两种极端断开方式下的区间宽度 > 0.01，
  或顶部并列中负实体 >= 20 个，则例外成立，诊断第 2 条的绝对化结论须收回一部分。

E8：已报告的配对自助 CI [+0.0389, +0.0996] 覆盖的是 **Lp** 聚合差 0.0689，
  **不覆盖 max** 聚合差 0.1271。0.127 至今没有区间支撑，本脚本补上。

纯 CPU 后处理，不训练、不改机制、不创建 SwanLab 运行身份。
"""
import json
import os

import numpy as np
from sklearn.metrics import average_precision_score

CH3 = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-full"
XGB = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-entity"
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-e0-e8-audit"
os.makedirs(OUT, exist_ok=True)
P_LEARNED = 1.2235541820526123
B = 2000
SEED = 42

sc = {"C11": np.load(f"{CH3}/scores_C11.npy"), "XGB": np.load(f"{XGB}/scores_xgb.npy")}
y24 = np.load(f"{CACHE}/y24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = int(ent24.max()) + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
assert N_ENT == 47115 and int(ent_lab.sum()) == 752, "实体口径与冻结不符"
del key24, s24, d24
print(f"实体 {N_ENT:,}  正例实体 {int(ent_lab.sum()):,}", flush=True)


def ent_max(v):
    es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24, v)
    return es


def ent_lp(v, p=P_LEARNED):
    num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
    np.add.at(num, ent24, np.clip(v, 1e-7, 1.0).astype(np.float64) ** p)
    np.add.at(cnt, ent24, 1.0)
    return np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


def ap_tie_bounds(es, lab):
    """并列敏感性：在同分组内分别把正例全排前、全排后，得到 AP 的上下界。

    sklearn 的 average_precision_score 按分数降序累计，同分样本按数组顺序进入。
    通过对分数加一个只依赖标签的无穷小扰动，可构造两种极端断开方式：
    正例优先（AP 上界）与负例优先（AP 下界）。扰动量取该分数向量最小正间隔的一半，
    保证不改变不同分数之间的相对顺序，只决定并列组内部的次序。
    """
    v = es.astype(np.float64)
    u = np.unique(v[np.isfinite(v)])
    gap = np.min(np.diff(u)) if len(u) > 1 else 1.0
    eps = gap / 4.0
    hi = average_precision_score(lab, v + eps * lab)          # 正例优先
    lo = average_precision_score(lab, v - eps * lab)          # 负例优先
    return float(lo), float(hi), float(gap), int(len(u))


print("\n" + "=" * 104)
print("E0 并列与饱和审计")
E0 = {}
for name, v in sc.items():
    finite = np.isfinite(v)
    n_uniq_flow = int(len(np.unique(v)))
    n_at_one = int((v >= 1.0).sum())
    es = ent_max(v)
    top = es.max()
    tie_top = np.isclose(es, top, rtol=0, atol=0)
    tie_top_pos = int(ent_lab[tie_top].sum())
    tie_top_neg = int(tie_top.sum()) - tie_top_pos
    lo, hi, gap, n_uniq_ent = ap_tie_bounds(es, ent_lab)
    E0[name] = {"dtype": str(v.dtype), "n_flow": int(len(v)), "finite_all": bool(finite.all()),
                "n_unique_flow_scores": n_uniq_flow,
                "n_flow_score_eq_1": n_at_one,
                "n_unique_entity_max": n_uniq_ent,
                "entity_max_top_value": float(top),
                "n_entity_tied_at_top": int(tie_top.sum()),
                "tied_at_top_pos": tie_top_pos, "tied_at_top_neg": tie_top_neg,
                "min_positive_gap_entity_max": gap,
                "ap_max_tie_lo": lo, "ap_max_tie_hi": hi, "ap_max_tie_width": hi - lo}
    r = E0[name]
    print(f"\n[{name}] dtype={r['dtype']}  逐流唯一分数 {r['n_unique_flow_scores']:,}  "
          f"分数恰好为 1.0 的流 {r['n_flow_score_eq_1']:,}")
    print(f"  实体 max 唯一值 {r['n_unique_entity_max']:,}  顶部并列实体 {r['n_entity_tied_at_top']:,}"
          f"（正 {r['tied_at_top_pos']:,} / 负 {r['tied_at_top_neg']:,}）")
    print(f"  AP(max) 并列敏感区间 [{lo:.6f}, {hi:.6f}]  宽度 {hi-lo:.6f}")

c_w = E0["C11"]["ap_max_tie_width"]
c_neg = E0["C11"]["tied_at_top_neg"]
verdict = ("例外 A 成立：并列伪影显著，诊断第 2 条的绝对化结论须收回一部分，"
           "后续归因应在去伪影后的差距上重做"
           if (c_w > 0.01 or c_neg >= 20) else
           "例外 A 排除：并列伪影可忽略，诊断第 2 条可升级为成立")
print(f"\n判读（事前判据：区间宽度 > 0.01 或顶部负实体并列 >= 20）→ {verdict}")

print("\n" + "=" * 104)
print("E8 max 聚合专属配对自助（重抽样单元 = 实体）")
ES = {"C11_max": ent_max(sc["C11"]), "XGB_max": ent_max(sc["XGB"]),
      "C11_Lp": ent_lp(sc["C11"]), "XGB_Lp": ent_lp(sc["XGB"])}
del sc
point = {k: float(average_precision_score(ent_lab, v)) for k, v in ES.items()}
print("点估计 AP：", json.dumps({k: round(v, 6) for k, v in point.items()}, ensure_ascii=False))

rng = np.random.default_rng(SEED)
pairs = [("XGB_max", "C11_max"), ("XGB_Lp", "C11_Lp")]
boot = {f"{a}-{b}": [] for a, b in pairs}
for i in range(B):
    idx = rng.integers(0, N_ENT, N_ENT)
    l = ent_lab[idx]
    if l.sum() < 2 or l.sum() == len(l):
        continue
    cur = {k: average_precision_score(l, v[idx]) for k, v in ES.items()}
    for a, b in pairs:
        boot[f"{a}-{b}"].append(float(cur[a] - cur[b]))
    if (i + 1) % 500 == 0:
        print(f"  自助 {i+1}/{B}", flush=True)

E8 = {}
print(f"\n{'比较':<22}{'点估计差':>12}{'自助均值':>12}{'95% CI':>28}{'XGB更优占比':>14}")
for k, arr in boot.items():
    a = np.asarray(arr); a = a[np.isfinite(a)]
    lo, hi = np.percentile(a, [2.5, 97.5])
    x, y = k.split("-")
    pt = point[x] - point[y]
    frac = float((a > 0).mean())
    E8[k] = {"point": pt, "boot_mean": float(a.mean()), "ci_lo": float(lo),
             "ci_hi": float(hi), "frac_xgb_better": frac, "n_boot": int(len(a))}
    print(f"{k:<22}{pt:>12.6f}{a.mean():>12.6f}{f'[{lo:+.6f}, {hi:+.6f}]':>28}{frac:>14.4f}")
print("=" * 104)

json.dump({"E0": E0, "E0_verdict": verdict, "E8": E8, "point_ap": point,
           "n_boot": B, "seed": SEED, "p_learned": P_LEARNED},
          open(f"{OUT}/e0_e8_audit.json", "w"), ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/e0_e8_audit.json")
