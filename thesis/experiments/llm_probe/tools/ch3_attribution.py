# -*- coding: utf-8 -*-
"""第三章「实体级 CPA-ELP 输给 XGBoost 0.127」的归因诊断（E1/E2/E3/E6/E7）。

只消费冻结分数，不重训、不改机制、不创建 SwanLab 运行身份。全部 CPU 后处理。

口径逐字复刻 tools/ch3_full.py：
  实体构造     ch3_full.py:130-133   sortlex{srcIP,dstIP}，实体标签取组内逐流标签最大值
  max 聚合     ch3_full.py:219       组内最大，float32
  Lp 聚合      ch3_full.py:221-223   (sum clip(s,1e-7,1)^p / n)^(1/p)，末尾 .astype(np.float32)
  DR@FPR       ch3_full.py:236-240   负实体分数降序，取第 int(n_neg*target) 位作阈值
  实体内时序秩 ch3_full.py:136-140   np.lexsort((t24, ent24)) 后按实体分段

自检：启动即用 scores_C11.npy 重算实体数/正例实体/AP(max)/AP(Lp)，对不上立即停止。

性能实现说明：np.maximum.at / np.add.at 在 2000 万元素上是无缓冲慢路径，本文件改用
「按实体一次稳定排序 + reduceat」的等价实现（group_max / group_powsum），并在自检阶段
与 ch3_full 的原始 at-路径逐位比对，确认 AP 完全一致后才用于后续扫描。
"""

import json
import os
import time

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
CH3 = f"{ROOT}/runs/diagnostics/ch3-full"
XGBD = f"{ROOT}/runs/diagnostics/ch3-xgb-entity"
OUT = f"{ROOT}/runs/diagnostics/ch3-attribution"
os.makedirs(OUT, exist_ok=True)

P_LEARNED = 1.2235541820526123
TARGET_FPR = 0.04
BLOCK = 128
CLIP_LO, CLIP_HI = 1e-7, 1.0
LOGIT_LO, LOGIT_HI = 1e-7, 1.0 - 1e-7
N_BOOT = 2000
BOOT_SEED = 20260817
FROZEN = {"n_ent": 47115, "n_pos": 752,
          "ap_max": 0.3858276572759182, "ap_lp": 0.46298806991944896}
R = {}   # 结果汇总

# ================= 载入 =================
y24 = np.load(f"{CACHE}/y24.npy")
t24 = np.load(f"{CACHE}/t24.npy")
sc_c = np.load(f"{CH3}/scores_C11.npy")
seen = np.load(f"{CH3}/seen_C11.npy")
sc_x = np.load(f"{XGBD}/scores_xgb.npy")
N = len(y24)
log(f"载入完成 流={N:,} 逐流正例率={y24.mean():.10f} seen 覆盖={seen.mean():.6f}")
assert seen.all(), "seen 非全量，本文件的 reduceat 实现假定全覆盖，请停止并改回掩码版本"

if os.path.exists(f"{OUT}/ent24.npy"):
    ent24 = np.load(f"{OUT}/ent24.npy")
    log("实体键复用缓存 ent24.npy")
else:
    s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
    d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
    key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
    _, _inv = np.unique(key24, return_inverse=True)
    ent24 = _inv.astype(np.int32)
    np.save(f"{OUT}/ent24.npy", ent24)
    del s24, d24, key24, _inv
    log("实体键构造完成并落盘（int32，81 MB）")

N_ENT = int(ent24.max()) + 1
ent_lab = np.zeros(N_ENT, np.float32)
np.maximum.at(ent_lab, ent24, y24)
n_pos_ent = int(ent_lab.sum())
log(f"实体={N_ENT:,} 正例实体={n_pos_ent:,} 先验={ent_lab.mean():.10f}")
assert N_ENT == FROZEN["n_ent"], f"实体数 {N_ENT} 与冻结 47115 不符"
assert n_pos_ent == FROZEN["n_pos"], f"正例实体 {n_pos_ent} 与冻结 752 不符"

# 按实体分组的稳定排序（供 reduceat 用）
oe = np.argsort(ent24, kind="stable")
_es = ent24[oe]
_st = np.flatnonzero(np.r_[True, _es[1:] != _es[:-1]])
_uq = _es[_st]
cnt_ent = np.bincount(ent24, minlength=N_ENT).astype(np.int64)
assert (cnt_ent > 0).all(), "存在无流实体，与构造方式矛盾"
log(f"实体分组就绪 实体流数中位={np.median(cnt_ent):.0f} 最大={cnt_ent.max():,}")


def group_max(sc):
    """等价于 ch3_full.py:219 的 np.maximum.at（max 与累加顺序无关，逐位一致）。"""
    es = np.full(N_ENT, -np.inf, np.float32)
    es[_uq] = np.maximum.reduceat(sc[oe], _st)
    return es


def group_powsum(sc, p):
    """等价于 ch3_full.py:221-223 的 np.add.at 幂和，float64 累加。"""
    v = np.clip(sc, CLIP_LO, CLIP_HI).astype(np.float64) ** p
    num = np.zeros(N_ENT, np.float64)
    num[_uq] = np.add.reduceat(v[oe], _st)
    return num


def ent_lp(sc, p):
    """ch3_full.py:221-223，含末尾 .astype(np.float32)。"""
    num = group_powsum(sc, p)
    cnt = cnt_ent.astype(np.float64)
    return np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)


def ent_ap(es, lab=None, sub=None):
    lab = ent_lab if lab is None else lab
    ok = np.isfinite(es)
    if sub is not None:
        ok &= sub
    if ok.sum() == 0 or lab[ok].sum() == 0 or lab[ok].sum() == ok.sum():
        return float("nan")
    return float(average_precision_score(lab[ok], es[ok]))


def dr_at_fpr(es, target=TARGET_FPR):
    """ch3_full.py:236-240 逐字复刻。"""
    ok = np.isfinite(es)
    v = es[ok]
    l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0:
        return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


# ================= 自检：与冻结口径逐位对表 =================
# 先跑 ch3_full 的原始 at-路径，再跑本文件的 reduceat 路径，两者都必须命中冻结值
_es_at = np.full(N_ENT, -np.inf, np.float32)
np.maximum.at(_es_at, ent24, sc_c)
_num_at = np.zeros(N_ENT, np.float64)
_cnt_at = np.zeros(N_ENT, np.float64)
np.add.at(_num_at, ent24, np.clip(sc_c, CLIP_LO, CLIP_HI).astype(np.float64) ** P_LEARNED)
np.add.at(_cnt_at, ent24, 1.0)
_lp_at = np.where(_cnt_at > 0, (_num_at / np.maximum(_cnt_at, 1)) ** (1.0 / P_LEARNED), -np.inf).astype(np.float32)
chk_at = {"ap_max": ent_ap(_es_at), "ap_lp": ent_ap(_lp_at)}
es_c_max, es_c_lp = group_max(sc_c), ent_lp(sc_c, P_LEARNED)
chk_rd = {"ap_max": ent_ap(es_c_max), "ap_lp": ent_ap(es_c_lp)}
log(f"自检 at-路径   AP(max)={chk_at['ap_max']:.16f} AP(Lp)={chk_at['ap_lp']:.16f}")
log(f"自检 reduceat  AP(max)={chk_rd['ap_max']:.16f} AP(Lp)={chk_rd['ap_lp']:.16f}")
for k in ("ap_max", "ap_lp"):
    assert abs(chk_at[k] - FROZEN[k]) < 1e-10, f"自检失败 {k}: at-路径 {chk_at[k]} != 冻结 {FROZEN[k]}"
    assert abs(chk_rd[k] - FROZEN[k]) < 1e-10, f"自检失败 {k}: reduceat {chk_rd[k]} != 冻结 {FROZEN[k]}"
assert np.array_equal(_es_at, es_c_max), "reduceat 的 max 与 at 路径不逐位一致"
del _es_at, _num_at, _cnt_at, _lp_at
log("自检通过：实体数/正例实体/AP(max)/AP(Lp) 与冻结值一致，reduceat 实现等价")

es_x_max, es_x_lp = group_max(sc_x), ent_lp(sc_x, P_LEARNED)
R["baseline"] = {
    "c11": {"flow_ap": float(average_precision_score(y24, sc_c)),
            "ap_max": ent_ap(es_c_max), "ap_lp": ent_ap(es_c_lp),
            "dr_max": dr_at_fpr(es_c_max), "dr_lp": dr_at_fpr(es_c_lp)},
    "xgb": {"flow_ap": float(average_precision_score(y24, sc_x)),
            "ap_max": ent_ap(es_x_max), "ap_lp": ent_ap(es_x_lp),
            "dr_max": dr_at_fpr(es_x_max), "dr_lp": dr_at_fpr(es_x_lp)}}
log(f"基线复算 C11 {R['baseline']['c11']}")
log(f"基线复算 XGB {R['baseline']['xgb']}")

# ================= 位置重建（供 E1b / E2 用） =================
_ord = np.lexsort((t24, ent24))
_e = ent24[_ord]
_s2 = np.flatnonzero(np.r_[True, _e[1:] != _e[:-1]])
rank_ent = np.empty(N, np.int64)
rank_ent[_ord] = np.arange(N) - np.repeat(_s2, np.diff(np.r_[_s2, N]))
pos = (rank_ent % BLOCK + 1).astype(np.int16)
del _e, _s2, _ord, rank_ent

I24 = np.load(f"{CACHE}/I24.npy")
M24 = np.load(f"{CACHE}/M24.npy")
pos_true = np.zeros(N, np.int16)
_cols = np.broadcast_to((np.arange(I24.shape[1]) + 1).astype(np.int16), I24.shape)
_m = M24 > 0.5
pos_true[I24[_m]] = _cols[_m]
n_cov = int((pos_true > 0).sum())
n_agree = int((pos_true == pos).sum())
log(f"位置重建核对：I24 覆盖流={n_cov:,}/{N:,}  与 lexsort 重建一致={n_agree:,}"
    f"（{n_agree / N:.6f}）")
R["pos_check"] = {"covered": n_cov, "agree": n_agree, "frac": n_agree / N}
if n_agree == N:
    log("位置重建与冻结分块逐位一致，采用重建值")
else:
    log("位置重建与 I24 不完全一致，改用 I24 直接给出的真实分块位置")
    pos = pos_true
del I24, M24, _cols, _m, pos_true, t24

# ================= 通用工具 =================
def to_logit(sc):
    p = np.clip(sc, LOGIT_LO, LOGIT_HI).astype(np.float64)
    return np.log(p) - np.log1p(-p)


def clip_diag(sc, tag):
    """logit 变换前的截断饱和度：截断比例过高会人为压低组内方差、抬高 ICC。"""
    lo = int((sc <= LOGIT_LO).sum())
    hi = int((sc >= LOGIT_HI).sum())
    d = {"n_at_lo": lo, "n_at_hi": hi, "frac_lo": lo / N, "frac_hi": hi / N,
         "min": float(sc.min()), "max": float(sc.max())}
    log(f"  截断诊断 {tag}: 分数<={LOGIT_LO:g} 的流={lo:,}（{lo / N:.6f}） "
        f">={LOGIT_HI:g} 的流={hi:,}  min={d['min']:.3e} max={d['max']:.8f}")
    return d


def from_logit(z):
    return (1.0 / (1.0 + np.exp(-np.clip(z, -60.0, 60.0)))).astype(np.float32)


def paired_boot(es_a, es_b, n_boot=N_BOOT, seed=BOOT_SEED):
    """配对自助，重抽样单元=实体。返回 (mean_diff, lo, hi, win_frac)，diff = a - b。"""
    rng = np.random.default_rng(seed)
    ok = np.isfinite(es_a) & np.isfinite(es_b)
    a, b, l = es_a[ok], es_b[ok], ent_lab[ok]
    n = len(l)
    d = np.empty(n_boot)
    for i in range(n_boot):
        ix = rng.integers(0, n, n)
        li = l[ix]
        if li.sum() == 0 or li.sum() == n:
            d[i] = np.nan
            continue
        d[i] = average_precision_score(li, a[ix]) - average_precision_score(li, b[ix])
    d = d[np.isfinite(d)]
    return (float(d.mean()), float(np.percentile(d, 2.5)),
            float(np.percentile(d, 97.5)), float((d > 0).mean()), int(len(d)))


# ================= E2：负实体高分尖峰（H1） =================
log("=" * 96)
log("E2 —— H1「负实体高分尖峰」")


def intrusion(es, recalls=(0.3, 0.5, 0.7)):
    o = np.argsort(-es, kind="stable")
    l = ent_lab[o]
    tp = np.cumsum(l)
    fp = np.cumsum(1.0 - l)
    rows = []
    for r in recalls:
        need = np.ceil(r * n_pos_ent)
        k = int(np.searchsorted(tp, need, side="left"))
        k = min(k, len(tp) - 1)
        rows.append({"recall_target": r, "recall_actual": float(tp[k] / n_pos_ent),
                     "k_prefix": k + 1, "n_neg_above": int(fp[k]),
                     "precision": float(tp[k] / (k + 1)), "thr": float(es[o[k]])})
    return rows


e2 = {"intrusion": {"c11": intrusion(es_c_max), "xgb": intrusion(es_x_max)}}
log(f"{'召回':>6}{'C11 负实体侵入':>16}{'XGB 负实体侵入':>16}{'倍率 C11/XGB':>16}"
    f"{'C11 精确率':>14}{'XGB 精确率':>14}")
for a, b in zip(e2["intrusion"]["c11"], e2["intrusion"]["xgb"]):
    ratio = a["n_neg_above"] / max(b["n_neg_above"], 1)
    log(f"{a['recall_target']:>6.1f}{a['n_neg_above']:>16,}{b['n_neg_above']:>16,}"
        f"{ratio:>16.3f}{a['precision']:>14.4f}{b['precision']:>14.4f}")
    a["ratio_vs_xgb"] = ratio

# 逐流上尾：同一分位阈值以上的流数，及其覆盖的「不同负实体」数
neg_flow = ent_lab[ent24] == 0
tail = []
for q in (0.999, 0.9999, 0.99999):
    row = {"q": q}
    for tag, sc in (("c11", sc_c), ("xgb", sc_x)):
        thr = float(np.quantile(sc[neg_flow], q))
        hit = neg_flow & (sc >= thr)
        row[tag] = {"thr": thr, "n_flow": int(hit.sum()),
                    "n_distinct_neg_ent": int(len(np.unique(ent24[hit])))}
    tail.append(row)
    log(f"  良性流上尾 q={q}: C11 {row['c11']['n_flow']:>8,} 流 / "
        f"{row['c11']['n_distinct_neg_ent']:>6,} 个不同负实体   "
        f"XGB {row['xgb']['n_flow']:>8,} 流 / {row['xgb']['n_distinct_neg_ent']:>6,} 个不同负实体")
e2["neg_flow_upper_tail"] = tail

# C11 排名前 500 的负实体画像
_o_sc = np.argsort(sc_c, kind="stable")
argmax_flow = np.full(N_ENT, -1, np.int64)
argmax_flow[ent24[_o_sc]] = _o_sc          # 升序最后写入 = 组内最大
del _o_sc
rank_x = np.empty(N_ENT, np.int64)
rank_x[np.argsort(-es_x_max, kind="stable")] = np.arange(N_ENT) + 1
rank_c = np.empty(N_ENT, np.int64)
rank_c[np.argsort(-es_c_max, kind="stable")] = np.arange(N_ENT) + 1

order_c = np.argsort(-es_c_max, kind="stable")
top_neg = order_c[ent_lab[order_c] == 0][:500]
tf = argmax_flow[top_neg]
prof = {"n": int(len(top_neg)),
        "c11_rank": {"min": int(rank_c[top_neg].min()), "max": int(rank_c[top_neg].max())},
        "argmax_score_c11": {q: float(np.percentile(sc_c[tf], q)) for q in (5, 25, 50, 75, 95)},
        "argmax_score_xgb_same_flow": {q: float(np.percentile(sc_x[tf], q)) for q in (5, 25, 50, 75, 95)},
        "block_pos": {q: float(np.percentile(pos[tf], q)) for q in (5, 25, 50, 75, 95)},
        "block_pos_le2_frac": float((pos[tf] <= 2).mean()),
        "ent_nflow": {q: float(np.percentile(cnt_ent[top_neg], q)) for q in (5, 25, 50, 75, 95)},
        "ent_nflow_le2_frac": float((cnt_ent[top_neg] <= 2).mean()),
        "xgb_rank": {q: float(np.percentile(rank_x[top_neg], q)) for q in (5, 25, 50, 75, 95)},
        "xgb_rank_gt_5000_frac": float((rank_x[top_neg] > 5000).mean()),
        "xgb_rank_gt_20000_frac": float((rank_x[top_neg] > 20000).mean())}
e2["top500_neg_profile"] = prof
log(f"  C11 前 500 负实体：C11 名次 {prof['c11_rank']['min']}–{prof['c11_rank']['max']}")
log(f"    argmax 流 C11 分数 分位 5/25/50/75/95 = "
    + "/".join(f"{prof['argmax_score_c11'][q]:.4f}" for q in (5, 25, 50, 75, 95)))
log(f"    同一条流的 XGB 分数 分位 = "
    + "/".join(f"{prof['argmax_score_xgb_same_flow'][q]:.6f}" for q in (5, 25, 50, 75, 95)))
log(f"    argmax 流的块内位置 分位 = "
    + "/".join(f"{prof['block_pos'][q]:.0f}" for q in (5, 25, 50, 75, 95))
    + f"  位置<=2 占比={prof['block_pos_le2_frac']:.4f}")
log(f"    该实体流数 分位 = " + "/".join(f"{prof['ent_nflow'][q]:.0f}" for q in (5, 25, 50, 75, 95))
    + f"  流数<=2 占比={prof['ent_nflow_le2_frac']:.4f}")
log(f"    这些实体在 XGB 下的名次 分位 = "
    + "/".join(f"{prof['xgb_rank'][q]:.0f}" for q in (5, 25, 50, 75, 95))
    + f"  名次>5000 占比={prof['xgb_rank_gt_5000_frac']:.4f}"
    + f"  >20000 占比={prof['xgb_rank_gt_20000_frac']:.4f}")
R["E2"] = e2

# ================= E1：实体规模 / 序列位置混杂（H2） =================
log("=" * 96)
log("E1(a) —— 按实体流数分箱的实体 AP(max)")
SIZE_BINS = [(1, 2), (3, 10), (11, 100), (101, 10_000), (10_001, 1 << 62)]
rows_a = []
for lo, hi in SIZE_BINS:
    sub = (cnt_ent >= lo) & (cnt_ent <= hi)
    npos = int(ent_lab[sub].sum())
    row = {"bin": f"{lo}-{'inf' if hi > 10 ** 12 else hi}", "n_ent": int(sub.sum()), "n_pos": npos,
           "prior": float(ent_lab[sub].mean()) if sub.sum() else float("nan"),
           "c11_ap_max": ent_ap(es_c_max, sub=sub), "xgb_ap_max": ent_ap(es_x_max, sub=sub),
           "c11_ap_lp": ent_ap(es_c_lp, sub=sub), "xgb_ap_lp": ent_ap(es_x_lp, sub=sub)}
    row["gap_max"] = row["xgb_ap_max"] - row["c11_ap_max"]
    row["gap_lp"] = row["xgb_ap_lp"] - row["c11_ap_lp"]
    rows_a.append(row)
log(f"{'流数箱':>12}{'实体数':>10}{'正例实体':>10}{'先验':>10}"
    f"{'C11 AP(max)':>14}{'XGB AP(max)':>14}{'差 XGB-C11':>13}")
for r in rows_a:
    log(f"{r['bin']:>12}{r['n_ent']:>10,}{r['n_pos']:>10,}{r['prior']:>10.5f}"
        f"{r['c11_ap_max']:>14.6f}{r['xgb_ap_max']:>14.6f}{r['gap_max']:>+13.6f}")

log("E1(b) —— 按流在 128 块内位置分箱的逐流判别力")
POS_BINS = [(1, 1), (2, 2), (3, 8), (9, 32), (33, 128)]
rows_b = []
for lo, hi in POS_BINS:
    m = (pos >= lo) & (pos <= hi)
    yy = y24[m]
    row = {"bin": f"{lo}-{hi}" if lo != hi else f"{lo}", "n_flow": int(m.sum()),
           "n_pos": int(yy.sum()), "pi": float(yy.mean())}
    if 0 < yy.sum() < len(yy):
        row["c11_flow_ap"] = float(average_precision_score(yy, sc_c[m]))
        row["xgb_flow_ap"] = float(average_precision_score(yy, sc_x[m]))
        row["c11_auc"] = float(roc_auc_score(yy, sc_c[m]))
        row["xgb_auc"] = float(roc_auc_score(yy, sc_x[m]))
        row["gap_ap"] = row["xgb_flow_ap"] - row["c11_flow_ap"]
        row["gap_auc"] = row["xgb_auc"] - row["c11_auc"]
        # 基率归一的提升，避免各箱正例率不同带来的不可比
        row["c11_lift"] = row["c11_flow_ap"] / row["pi"]
        row["xgb_lift"] = row["xgb_flow_ap"] / row["pi"]
    rows_b.append(row)
    log(f"  位置 {row['bin']:>6}: 流={row['n_flow']:>12,} 正例率={row['pi']:.6f}  "
        f"C11 AP={row.get('c11_flow_ap', float('nan')):.6f} AUC={row.get('c11_auc', float('nan')):.6f}  |  "
        f"XGB AP={row.get('xgb_flow_ap', float('nan')):.6f} AUC={row.get('xgb_auc', float('nan')):.6f}  |  "
        f"ΔAUC={row.get('gap_auc', float('nan')):+.6f}")
R["E1"] = {"size_bins": rows_a, "pos_bins": rows_b}

# ================= E3：组内相关性（H3） =================
log("=" * 96)
log("E3 —— H3「机制一的组内相关性稀释峰值」")
R["clip_diag"] = {"c11": clip_diag(sc_c, "C11"), "xgb": clip_diag(sc_x, "XGB")}
lg_c = to_logit(sc_c)
lg_x = to_logit(sc_x)
neg_ent = ent_lab == 0


def icc_eta2(lg, ent_subset_mask):
    """组间方差 / 总方差（eta^2），只在给定实体子集的流上计算；附 ANOVA ICC(1)。"""
    fm = ent_subset_mask[ent24]
    v = lg[fm]
    e = ent24[fm]
    n = len(v)
    grand = v.mean()
    ssum = np.bincount(e, weights=v, minlength=N_ENT)
    scnt = np.bincount(e, minlength=N_ENT).astype(np.float64)
    act = scnt > 0
    gm = ssum[act] / scnt[act]
    k = int(act.sum())
    ss_between = float((scnt[act] * (gm - grand) ** 2).sum())
    ss_total = float(((v - grand) ** 2).sum())
    eta2 = ss_between / ss_total if ss_total > 0 else float("nan")
    ss_within = ss_total - ss_between
    msb = ss_between / (k - 1) if k > 1 else float("nan")
    msw = ss_within / (n - k) if n > k else float("nan")
    n0 = (n - (scnt[act] ** 2).sum() / n) / (k - 1) if k > 1 else float("nan")
    icc1 = (msb - msw) / (msb + (n0 - 1) * msw) if np.isfinite(msb) and np.isfinite(msw) else float("nan")
    return {"n_flow": n, "n_ent": k, "eta2": eta2, "icc1": float(icc1),
            "sd_flow_logit": float(v.std())}


e3 = {"icc": {}}
for tag, lg in (("c11", lg_c), ("xgb", lg_x)):
    e3["icc"][tag] = {"all_neg": icc_eta2(lg, neg_ent),
                      "neg_n_ge5": icc_eta2(lg, neg_ent & (cnt_ent >= 5))}
for scope in ("all_neg", "neg_n_ge5"):
    a, b = e3["icc"]["c11"][scope], e3["icc"]["xgb"][scope]
    log(f"  ICC[{scope}]  C11 eta2={a['eta2']:.6f} ICC(1)={a['icc1']:.6f} sd={a['sd_flow_logit']:.4f}"
        f"  |  XGB eta2={b['eta2']:.6f} ICC(1)={b['icc1']:.6f} sd={b['sd_flow_logit']:.4f}"
        f"  | 实体={a['n_ent']:,} 流={a['n_flow']:,}")

# (b) E[max-logit] 对 log n 的分箱回归（负实体）
NBINS = [(1, 1), (2, 2), (3, 4), (5, 8), (9, 16), (17, 32), (33, 64),
         (65, 128), (129, 512), (513, 4096), (4097, 1 << 62)]
e3["slope"] = {}
for tag, lg in (("c11", lg_c), ("xgb", lg_x)):
    mx = np.full(N_ENT, -np.inf, np.float64)
    mx[_uq] = np.maximum.reduceat(lg[oe], _st)
    sd = e3["icc"][tag]["all_neg"]["sd_flow_logit"]
    pts = []
    for lo, hi in NBINS:
        sub = neg_ent & (cnt_ent >= lo) & (cnt_ent <= hi)
        if sub.sum() < 20:
            continue
        pts.append({"bin": f"{lo}-{'inf' if hi > 10 ** 12 else hi}", "n_ent": int(sub.sum()),
                    "mean_log_n": float(np.log(cnt_ent[sub]).mean()),
                    "mean_max_logit": float(mx[sub].mean()),
                    "mean_max_logit_sd_units": float(mx[sub].mean() / sd)})
    xs = np.array([p["mean_log_n"] for p in pts])
    ys = np.array([p["mean_max_logit"] for p in pts])
    sl = float(np.polyfit(xs, ys, 1)[0])
    e3["slope"][tag] = {"points": pts, "slope_raw": sl, "slope_sd_units": sl / sd,
                        "sd_flow_logit": sd}
    log(f"  E[max-logit]~log n（负实体，{len(pts)} 箱）{tag}: 斜率={sl:+.6f} logit/ln n  "
        f"= {sl / sd:+.6f} 个逐流 logit 标准差 / ln n")

# (c) 组内异常化 max
e3["anomaly"] = {}
for tag, lg in (("c11", lg_c), ("xgb", lg_x)):
    gsum = np.bincount(ent24, weights=lg, minlength=N_ENT)
    gmean = gsum / cnt_ent
    a = lg - gmean[ent24]
    amx = np.full(N_ENT, -np.inf, np.float64)
    amx[_uq] = np.maximum.reduceat(a[oe], _st)
    amx32 = amx.astype(np.float32)
    sub3 = cnt_ent >= 3
    e3["anomaly"][tag] = {"ap_anom_max_all": ent_ap(amx32),
                          "ap_anom_max_n_ge3": ent_ap(amx32, sub=sub3),
                          "ap_plain_max_n_ge3": ent_ap(es_c_max if tag == "c11" else es_x_max, sub=sub3)}
    del gsum, gmean, a, amx, amx32
n1 = int((cnt_ent == 1).sum())
n1p = int(ent_lab[cnt_ent == 1].sum())
n3 = int((cnt_ent >= 3).sum())
n3p = int(ent_lab[cnt_ent >= 3].sum())
e3["anomaly"]["degeneracy"] = {"n_ent_1flow": n1, "n_pos_ent_1flow": n1p,
                               "n_ent_ge3": n3, "n_pos_ent_ge3": n3p}
ga = e3["anomaly"]["xgb"]["ap_anom_max_all"] - e3["anomaly"]["c11"]["ap_anom_max_all"]
g3 = e3["anomaly"]["xgb"]["ap_anom_max_n_ge3"] - e3["anomaly"]["c11"]["ap_anom_max_n_ge3"]
g3p = e3["anomaly"]["xgb"]["ap_plain_max_n_ge3"] - e3["anomaly"]["c11"]["ap_plain_max_n_ge3"]
log(f"  组内异常 max（全部实体，n=1 实体恒为 0，占 {n1:,}/{N_ENT:,}，含 {n1p} 个正例实体）：")
log(f"    C11={e3['anomaly']['c11']['ap_anom_max_all']:.6f}  "
    f"XGB={e3['anomaly']['xgb']['ap_anom_max_all']:.6f}  差={ga:+.6f}（原始差 +0.127071）")
log(f"  仅 n>=3 实体（{n3:,} 个，正例 {n3p}）：普通 max 差={g3p:+.6f} → 异常 max 差={g3:+.6f}")
R["E3"] = e3
del lg_c, lg_x

# ================= E6：p 扫描 =================
log("=" * 96)
log("E6 —— 评价期 Lp 指数扫描")
PS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 8.0, 16.0, float("inf")]
e6 = {"c11": [], "xgb": []}
for tag, sc in (("c11", sc_c), ("xgb", sc_x)):
    for p in PS:
        es = group_max(sc) if np.isinf(p) else ent_lp(sc, p)
        e6[tag].append({"p": ("inf" if np.isinf(p) else p), "ap": ent_ap(es),
                        "dr": dr_at_fpr(es)})
log(f"{'p':>8}{'C11 实体AP':>14}{'XGB 实体AP':>14}{'差 XGB-C11':>13}"
    f"{'C11 DR@4%':>12}{'XGB DR@4%':>12}")
for a, b in zip(e6["c11"], e6["xgb"]):
    log(f"{str(a['p']):>8}{a['ap']:>14.6f}{b['ap']:>14.6f}{b['ap'] - a['ap']:>+13.6f}"
        f"{a['dr']:>12.4f}{b['dr']:>12.4f}")
best_c = max(e6["c11"], key=lambda r: r["ap"])
best_x = max(e6["xgb"], key=lambda r: r["ap"])
e6["best"] = {"c11": best_c, "xgb": best_x,
              "xgb_at_borrowed_p": R["baseline"]["xgb"]["ap_lp"],
              "xgb_best_minus_borrowed": best_x["ap"] - R["baseline"]["xgb"]["ap_lp"],
              "c11_best_minus_learned": best_c["ap"] - R["baseline"]["c11"]["ap_lp"],
              "gap_at_each_best": best_x["ap"] - best_c["ap"]}
log(f"  C11 峰值 p={best_c['p']} AP={best_c['ap']:.6f}（学到 p=1.2236 时 "
    f"{R['baseline']['c11']['ap_lp']:.6f}，差 {e6['best']['c11_best_minus_learned']:+.6f}）")
log(f"  XGB 峰值 p={best_x['p']} AP={best_x['ap']:.6f}（借用 p=1.2236 时 "
    f"{R['baseline']['xgb']['ap_lp']:.6f}，差 {e6['best']['xgb_best_minus_borrowed']:+.6f}）")
log(f"  各自最优 p 下的差距 XGB-C11 = {e6['best']['gap_at_each_best']:+.6f}")
R["E6"] = e6

# ================= E7：logit 融合 =================
log("=" * 96)
log("E7 —— 逐流 logit 融合的敏感性（w 不可在 LSPR24 上选）")
have23 = all(os.path.exists(f"{CH3}/{f}") for f in ("scores23_C11.npy",)) and \
         os.path.exists(f"{XGBD}/scores23_xgb.npy")
e7 = {"lspr23_scores_available": bool(have23),
      "w_selectable_without_leakage": bool(have23),
      "note": ("LSPR23 逐流分数与 C11 检查点均不存在（ch3_full.py 未保存权重，"
               "ch3_xgb_entity.py 未保存训练集分数），在不重训的前提下无法用 LSPR23 拟合 w。"
               "下列曲线仅为敏感性展示，禁止据此选点，选点即测试集泄漏。")}
lz_c = to_logit(sc_c)
lz_x = to_logit(sc_x)
curve = []
for w in np.round(np.arange(0.0, 1.0001, 0.05), 2):
    f = from_logit(w * lz_x + (1.0 - w) * lz_c)
    em, el = group_max(f), ent_lp(f, P_LEARNED)
    curve.append({"w": float(w), "ap_max": ent_ap(em), "ap_lp": ent_ap(el),
                  "dr_max": dr_at_fpr(em), "dr_lp": dr_at_fpr(el)})
    del f, em, el
log(f"{'w(XGB权重)':>12}{'融合 AP(max)':>15}{'融合 AP(Lp)':>15}{'ΔAP(max) vs XGB':>18}")
for r in curve:
    r["d_max_vs_xgb"] = r["ap_max"] - R["baseline"]["xgb"]["ap_max"]
    r["d_lp_vs_xgb"] = r["ap_lp"] - R["baseline"]["xgb"]["ap_lp"]
    log(f"{r['w']:>12.2f}{r['ap_max']:>15.6f}{r['ap_lp']:>15.6f}{r['d_max_vs_xgb']:>+18.6f}")
e7["curve"] = curve
best_w = max(curve, key=lambda r: r["ap_max"])
e7["best_w_on_test_INVALID"] = best_w
log(f"  曲线峰值 w={best_w['w']}（在测试集上取的，不可用于选点，仅作上界参照）")

# 先验中性的 w=0.5 做配对自助，避免用测试集挑 w
f5 = from_logit(0.5 * lz_x + 0.5 * lz_c)
em5, el5 = group_max(f5), ent_lp(f5, P_LEARNED)
log("  配对自助（w=0.5，先验中性，非测试集选点）…")
e7["boot_w05_vs_xgb_max"] = paired_boot(em5, es_x_max)
e7["boot_w05_vs_xgb_lp"] = paired_boot(el5, es_x_lp)
m, lo, hi, wf, nb = e7["boot_w05_vs_xgb_max"]
log(f"    融合(w=0.5) − XGB，AP(max)：{m:+.6f}  CI[{lo:+.6f}, {hi:+.6f}]  胜率 {wf:.4f}（{nb} 次）")
m2, lo2, hi2, wf2, _ = e7["boot_w05_vs_xgb_lp"]
log(f"    融合(w=0.5) − XGB，AP(Lp) ：{m2:+.6f}  CI[{lo2:+.6f}, {hi2:+.6f}]  胜率 {wf2:.4f}")
log("  配对自助（测试集最优 w，仅作上界，标记为无效选点）…")
fb = from_logit(best_w["w"] * lz_x + (1.0 - best_w["w"]) * lz_c)
e7["boot_bestw_vs_xgb_max_INVALID"] = paired_boot(group_max(fb), es_x_max)
m3, lo3, hi3, wf3, _ = e7["boot_bestw_vs_xgb_max_INVALID"]
log(f"    融合(w={best_w['w']}) − XGB，AP(max)：{m3:+.6f}  CI[{lo3:+.6f}, {hi3:+.6f}]  胜率 {wf3:.4f}")
del f5, em5, el5, fb, lz_c, lz_x
R["E7"] = e7

# 基线差距的配对自助复算（对表已确立事实）
log("=" * 96)
log("基线差距配对自助复算（核对已确立事实）")
R["boot_xgb_minus_c11_max"] = paired_boot(es_x_max, es_c_max)
R["boot_xgb_minus_c11_lp"] = paired_boot(es_x_lp, es_c_lp)
m, lo, hi, wf, _ = R["boot_xgb_minus_c11_max"]
log(f"  XGB−C11 AP(max)：{m:+.6f} CI[{lo:+.6f}, {hi:+.6f}] 胜率 {wf:.4f}（已确立 +0.127071 [+0.099220,+0.155792]）")
m, lo, hi, wf, _ = R["boot_xgb_minus_c11_lp"]
log(f"  XGB−C11 AP(Lp) ：{m:+.6f} CI[{lo:+.6f}, {hi:+.6f}] 胜率 {wf:.4f}（已确立 +0.068929 [+0.038904,+0.099633]）")

R["meta"] = {"p_learned": P_LEARNED, "target_fpr": TARGET_FPR, "n_boot": N_BOOT,
             "boot_seed": BOOT_SEED, "numpy": np.__version__,
             "selfcheck_at_path": chk_at, "selfcheck_reduceat": chk_rd, "frozen": FROZEN}
json.dump(R, open(f"{OUT}/attribution.json", "w"), ensure_ascii=False, indent=2, default=float)
log(f"全部结果已存 {OUT}/attribution.json")
