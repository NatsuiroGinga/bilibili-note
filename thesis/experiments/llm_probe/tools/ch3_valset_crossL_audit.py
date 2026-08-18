# -*- coding: utf-8 -*-
"""只读诊断：24 配置跨 L 排序时，LSPR23 验证集的**逐流集合**在 L=32/64/128 下是否相同。

动机：selection 的第二级要在 L∈{32,64,128} 之间比大小。验证实体集合与 L 无关
（RandomState(42) 对实体排列），但时间尾部剔除用的是**逐序列起始时间**的 0.85 分位，
分块粒度变了，被剔掉的序列就不同，验证集实际覆盖的流可能随 L 漂移。
本脚本精确算出各 L 的验证流集合大小、两两交集与正例数，把这一项写成可核查的数字，
而不是留成文字推测。

只读 ent23 / t23_flow / y23，不加载 X23，不触碰任何 LSPR24 数组，不训练，不建运行身份。
"""

import json
import time

import numpy as np

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-hparam-fairsel-v2"
SEED, VAL_FRAC, TIME_TAIL = 42, 0.10, 0.15
GRID_L = (32, 64, 128)

for n in ("ent23", "t23_flow", "y23"):
    assert "24" not in n
e23f = np.load(f"{CACHE}/ent23.npy")
t23f = np.load(f"{CACHE}/t23_flow.npy")
y23 = np.load(f"{CACHE}/y23.npy")
log(f"LSPR23 流={len(y23):,}")

_ORD = np.lexsort((t23f, e23f))
_IV = e23f[_ORD]
_BND = np.flatnonzero(np.r_[True, _IV[1:] != _IV[:-1], True])
_SEGLEN = np.diff(_BND)
del _IV

_rs = np.random.RandomState(SEED)
_uent = np.unique(e23f)
_perm = _rs.permutation(len(_uent))
VAL_ENT = set(_uent[_perm[:max(1, int(len(_uent) * VAL_FRAC))]].tolist())
log(f"实体 {len(_uent):,}，验证实体 {len(VAL_ENT):,}（与 L 无关）")

RES = {}
FLOWSETS = {}
for Lu in GRID_L:
    nch = -(-_SEGLEN // Lu)
    n = int(nch.sum())
    off = np.repeat(np.cumsum(nch) - nch, nch)
    starts = np.repeat(_BND[:-1], nch) + (np.arange(n) - off) * Lu
    ends = np.repeat(_BND[1:], nch)
    real = np.minimum(Lu, ends - starts)
    EL = e23f[_ORD[starts]]
    TL = t23f[_ORD[starts]]
    m_ent = np.fromiter((e in VAL_ENT for e in EL), bool, len(EL))
    t_cut = np.quantile(TL, 1.0 - TIME_TAIL)
    m_time = TL >= t_cut
    val_seq = np.flatnonzero(m_ent & ~m_time)
    # 展开成逐流索引：第 i 段的真实流是 _ORD[starts[i] : starts[i]+real[i]]
    s_, r_ = starts[val_seq], real[val_seq]
    pos = np.repeat(s_, r_) + (np.arange(r_.sum()) - np.repeat(np.cumsum(r_) - r_, r_))
    flows = _ORD[pos]
    assert len(np.unique(flows)) == len(flows), f"L={Lu} 验证流出现重复"
    FLOWSETS[Lu] = flows
    RES[Lu] = {"n_seq_total": int(n), "n_val_seq": int(len(val_seq)),
               "n_val_flow": int(len(flows)), "n_val_pos_flow": int(y23[flows].sum()),
               "val_pos_rate": float(y23[flows].mean()), "t_cut": float(t_cut)}
    log(f"  L={Lu:>3}: 总序列 {n:,} 验证序列 {len(val_seq):,} 验证流 {len(flows):,} "
        f"正例流 {int(y23[flows].sum()):,} 正例率 {y23[flows].mean():.6f} 时间分位阈 {t_cut:.3f}")

log("-" * 92)
PAIR = {}
for a in GRID_L:
    for b in GRID_L:
        if a >= b:
            continue
        A, B = FLOWSETS[a], FLOWSETS[b]
        inter = np.intersect1d(A, B, assume_unique=True)
        jac = len(inter) / (len(A) + len(B) - len(inter))
        PAIR[f"{a}vs{b}"] = {"n_a": int(len(A)), "n_b": int(len(B)),
                             "n_intersection": int(len(inter)), "jaccard": float(jac),
                             "only_a": int(len(A) - len(inter)), "only_b": int(len(B) - len(inter))}
        log(f"  L={a} vs L={b}: 交集 {len(inter):,} | 仅 L={a} {len(A)-len(inter):,} | "
            f"仅 L={b} {len(B)-len(inter):,} | Jaccard={jac:.6f}")

same = len({RES[L]["n_val_flow"] for L in GRID_L}) == 1 and all(
    PAIR[k]["jaccard"] == 1.0 for k in PAIR)
log("=" * 92)
log(f"★ 三个 L 的验证逐流集合{'完全相同 → 跨 L 排序的 AP 直接可比' if same else '不完全相同 → 跨 L 排序的 AP 存在口径漂移，须在报告中标注'}")
json.dump({"per_L": {str(k): v for k, v in RES.items()}, "pairwise": PAIR,
           "identical_across_L": bool(same),
           "note": "验证实体集合与 L 无关；时间尾部按逐序列起始时间的 0.85 分位剔除，"
                   "分块粒度改变会使被剔除的序列不同"},
          open(f"{OUT}/valset_crossL_audit.json", "w"), ensure_ascii=False, indent=2)
log(f"已存 {OUT}/valset_crossL_audit.json 总耗时 {time.time()-T0:.1f} 秒")
