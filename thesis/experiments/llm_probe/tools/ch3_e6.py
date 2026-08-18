# -*- coding: utf-8 -*-
"""E6 攻击类别分面（独立后处理，消费冻结的 C11 分数）。

本脚本落实 2026-08-13 代码审查的五条意见：
  W1 直接消费 ch3-full 的 scores_C11.npy，不再复用 E5 的 L=128 模型（那是另一个模型）
  W2 Rec@FPR 阈值改为并列感知，并报出实际 FPR，而非假定恰好 4%
  W3 用 placement value 分解算 AUC 与其标准误，全局只排序一次；表中给 AUC±1.96SE 而非二元标签
  C4 未标注桶（占正例 99.84%）移出类别表单列，占位名与 ch3_full 统一为「(空)」
  另：跨类比较只用 ROC-AUC 与 Rec@FPR。合成数据实测同难度下 AP 变 8 倍、lift 变 506 倍，二者不可比。
纯 CPU 后处理，不训练、不创建 SwanLab 运行身份。
"""
import json, os
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

CH3 = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-full"
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-e6-v2"
os.makedirs(OUT, exist_ok=True)
TARGET_FPR = 0.04
MIN_POS = 50          # 低于此数不单独下结论，但仍列出并给 CI

sc = np.load(f"{CH3}/scores_C11.npy")
seen = np.load(f"{CH3}/seen_C11.npy")
y24 = np.load(f"{CACHE}/y24.npy")
cat24 = np.load(f"{CACHE}/cat24.npy", allow_pickle=True)
assert len(sc) == len(y24) == len(cat24), f"长度不一致 {len(sc)}/{len(y24)}/{len(cat24)}"
assert seen.all(), f"C11 分数覆盖不全：{seen.mean():.6f}"
print(f"消费冻结制品：{CH3}/scores_C11.npy  流数 {len(sc):,}  覆盖 {seen.mean():.4f}")
print(f"全局 C11 逐流 AP = {average_precision_score(y24, sc):.10f}  ROC-AUC = {roc_auc_score(y24, sc):.10f}")

neg = y24 == 0
neg_sorted = np.sort(sc[neg])                       # 全局排序一次，供所有类别复用
n_neg = len(neg_sorted)

# W2：并列感知阈值——取满足「越阈负例数 ≤ 预算」的最低分数，并报实际 FPR
u, c = np.unique(neg_sorted, return_counts=True)
tail = np.cumsum(c[::-1])[::-1]                      # tail[i] = 分数 ≥ u[i] 的负例数
budget = int(n_neg * TARGET_FPR)
ok_idx = np.flatnonzero(tail <= budget)
# ok_idx 为空意味着最高分处就已有超过预算的负例并列，此时阈值取 +inf、全类召回恒为 0，
# 会静默产出一张全零的表 3-5。这是分数严重退化（例如全部并列）的信号，必须中止而非出表。
assert len(ok_idx) > 0, (
    f"无法在 FPR<={TARGET_FPR} 下取到阈值：最高分处越阈负例已达 {int(tail[0]):,} > 预算 {budget:,}，"
    f"负例唯一分数仅 {len(u):,} 个，分数分布严重退化")
THR = float(u[ok_idx[0]])
FPR_REAL = float(tail[ok_idx[0]]) / n_neg
print(f"并列感知阈值 = {THR:.10f}   实际 FPR = {FPR_REAL:.6f}（目标 {TARGET_FPR}，预算 {budget:,}/{n_neg:,} 负例）")

def auc_se(pos_scores):
    """W3：placement value 分解。AUC = 正例在负例总体中的分位均值，SE 为其标准误。"""
    lo = np.searchsorted(neg_sorted, pos_scores, "left")
    hi = np.searchsorted(neg_sorted, pos_scores, "right")
    v = (lo + hi) / 2.0 / n_neg                      # 含 0.5 并列信用
    return float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 1 else float("nan")

def wilson(k, n, z=1.96):
    """二项比例的 Wilson 得分区间。

    Wald 区间 p ± z·sqrt(p(1-p)/n) 在本表上会失效：多数攻击类别正例数只有几十条，
    且召回常常贴近 0 或 1。p=0 时 Wald 给出零宽区间，读起来像「精确地测到 0」；
    p 接近 1 且 n 小时区间会越出 [0,1]。Wilson 在两种情形下都给非退化且落在 [0,1] 的区间。
    """
    if n <= 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1.0 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return float(max(0.0, c-h)), float(min(1.0, c+h))

cats = np.array([c if c else "(空)" for c in cat24], object)   # C4：占位名与 ch3_full 统一
UNLAB = "(空)"
rows, unlab = [], None
for cname in np.unique(cats[y24 > 0]):
    m_pos = (cats == cname) & (y24 > 0)
    n_c = int(m_pos.sum())
    if n_c < 2: continue
    ps = sc[m_pos]
    a, se = auc_se(ps)
    n_hit = int((ps >= THR).sum())
    rec = n_hit / n_c
    base = n_c / (n_c + n_neg)
    ap = average_precision_score(np.r_[np.ones(n_c), np.zeros(n_neg)], np.r_[ps, sc[neg]])
    rec_lo, rec_hi = wilson(n_hit, n_c)
    # AUC 区间同样夹到 [0,1]：正态近似在类别 AUC 接近 1、正例数又少时会越界。
    row = {"cat": str(cname), "n_pos": n_c, "n_hit": n_hit, "base_rate": base,
           "auc": a, "auc_se": se,
           "auc_lo": max(0.0, a-1.96*se), "auc_hi": min(1.0, a+1.96*se),
           "rec_at_fpr": rec, "rec_lo": rec_lo, "rec_hi": rec_hi, "ap_noncomparable": ap}
    if str(cname) == UNLAB: unlab = row
    else: rows.append(row)
rows.sort(key=lambda r: -r["n_pos"])

print("\n" + "="*112)
print(f"表 3-5  攻击类别细粒度检测能力（LSPR23→LSPR24 零样本，C11，实际 FPR {FPR_REAL:.4f}）")
print(f"{'攻击类别':<40}{'正例数':>8}{'ROC-AUC (95% CI)':>26}{'Rec@FPR (95% CI)':>26}{'AP(不可比)':>12}")
for r in rows:
    auc_s = f"{r['auc']:.4f} [{r['auc_lo']:.4f},{r['auc_hi']:.4f}]"
    rec_s = f"{r['rec_at_fpr']:.4f} [{r['rec_lo']:.4f},{r['rec_hi']:.4f}]"
    mark = "" if r["n_pos"] >= MIN_POS else "  †"
    print(f"{r['cat'][:38]:<40}{r['n_pos']:>8,}{auc_s:>26}{rec_s:>26}{r['ap_noncomparable']:>12.6f}{mark}")
print("-"*112)
if unlab:
    print(f"未标注桶（不参与类别比较）：正例 {unlab['n_pos']:,} 占全部正例 "
          f"{unlab['n_pos']/int((y24>0).sum()):.4%}，ROC-AUC {unlab['auc']:.4f}")
print(f"† 正例数 < {MIN_POS}，区间过宽，不单独下结论。")
print("跨类比较只用 ROC-AUC 与 Rec@FPR：二者与类别正例数无关（AUC 为固定负例总体上 placement 的样本均值）；")
print("AP 与 lift 随基率变化数量级，仅列 AP 作参考。")
print("区间口径：AUC 用 placement value 的正态近似并夹到 [0,1]；Rec 用 Wilson 得分区间，")
print("因多数类别正例只有几十条且召回常贴近 0 或 1，Wald 区间会给出零宽或越界的结果。")
print("="*112)
json.dump({"threshold": THR, "fpr_real": FPR_REAL, "n_neg": n_neg,
           "classes": rows, "unlabeled": unlab}, open(f"{OUT}/e6_v2.json", "w"),
          ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/e6_v2.json")
