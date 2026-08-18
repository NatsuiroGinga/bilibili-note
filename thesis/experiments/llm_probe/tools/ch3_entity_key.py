# -*- coding: utf-8 -*-
"""实体键对照：同一份冻结分数，只换分组键与聚合规则。

不训练、不改机制、不创建 SwanLab 运行身份。消费 ch3-full 的 scores_C11.npy，
把它分别按三种键聚合，回答「为什么用 2-IP 无向对」这个问题时能给出本课题自己的数字，
而不是只引 Dijk 在他自己模型上的结论。

三种键（定义逐字取自原论文）：
  src      Gehri 2023 的主机级键：源 IP。一条流只归发起方一组。
  1-IP     Dijk 2026 §4.1.3：Phi(f)={a,b}，一条流**同时归源 IP 和目的 IP 两组**。
  2-IP     Dijk 2026 §4.1.5：Phi(f)={a,b} 无序对。一条流只归一组。本课题当前所用。

两种聚合，各键都算：
  max      分数取组内最大
  Lp       (sum s^p / n)^(1/p)，p 取冻结 C11 学到的 1.2236

指标沿用第三章口径：实体级 AP，以及固定 4% 实体 FPR 下的检出率。
实体标签定义为「组内至少有一条恶意流」，与逐流标签一致，不引入新标注。
"""
import json
import os

import numpy as np
from sklearn.metrics import average_precision_score

CH3 = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-full"
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-entity-key"
os.makedirs(OUT, exist_ok=True)
P_LEARNED = 1.2236          # 冻结 C11 学到的 Lp 指数
TARGET_FPR = 0.04

sc = np.load(f"{CH3}/scores_C11.npy")
seen = np.load(f"{CH3}/seen_C11.npy")
y24 = np.load(f"{CACHE}/y24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
assert len(sc) == len(y24) == len(s24) == len(d24), "长度不一致"
assert seen.all(), f"C11 分数覆盖不全：{seen.mean():.6f}"
print(f"消费冻结制品 {CH3}/scores_C11.npy  流数 {len(sc):,}  正例率 {y24.mean():.10f}")


def group_stats(keys_per_flow, flow_idx, name):
    """keys_per_flow 与 flow_idx 等长；同一条流可出现多次（1-IP 的双归属）。"""
    uniq, inv = np.unique(keys_per_flow, return_inverse=True)
    n_ent = len(uniq)
    y = y24[flow_idx]
    s = sc[flow_idx]

    lab = np.zeros(n_ent, np.float32)
    np.maximum.at(lab, inv, y)

    es_max = np.full(n_ent, -np.inf, np.float32)
    np.maximum.at(es_max, inv, s)

    num = np.zeros(n_ent, np.float64)
    cnt = np.zeros(n_ent, np.float64)
    np.add.at(num, inv, np.clip(s, 1e-7, 1.0).astype(np.float64) ** P_LEARNED)
    np.add.at(cnt, inv, 1.0)
    es_lp = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / P_LEARNED), -np.inf).astype(np.float32)

    rows = {}
    for agg, es in (("max", es_max), ("Lp", es_lp)):
        ok = np.isfinite(es)
        ap = average_precision_score(lab[ok], es[ok])
        # 并列感知阈值：取满足「越阈负实体数 <= 预算」的最低分数，并报实际 FPR
        neg = es[ok][lab[ok] == 0]
        u, c = np.unique(np.sort(neg), return_counts=True)
        tail = np.cumsum(c[::-1])[::-1]
        budget = int(len(neg) * TARGET_FPR)
        idx = np.flatnonzero(tail <= budget)
        assert len(idx) > 0, f"{name}/{agg} 取不到 {TARGET_FPR} 阈值，分数分布退化"
        thr = float(u[idx[0]])
        fpr_real = float(tail[idx[0]]) / len(neg)
        pos = es[ok][lab[ok] > 0]
        dr = float((pos >= thr).mean())
        rows[agg] = {"ap": float(ap), "dr_at_fpr": dr, "fpr_real": fpr_real}
    return {"key": name, "n_entity": int(n_ent), "n_pos_entity": int(lab.sum()),
            "prior": float(lab.mean()), "median_flows": float(np.median(np.bincount(inv))),
            **{f"{a}_{k}": v for a, r in rows.items() for k, v in r.items()}}


N = len(sc)
all_idx = np.arange(N)
RES = []

# 2-IP：无序对，一条流归一组（本课题当前所用）
RES.append(group_stats(
    np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object),
    all_idx, "2-IP 无向对（当前）"))

# src：Gehri 主机级键，一条流只归发起方
RES.append(group_stats(s24, all_idx, "src 源IP（Gehri）"))

# 1-IP：Dijk §4.1.3，一条流同时归两端，故把流索引复制一份
RES.append(group_stats(np.concatenate([s24, d24]),
                       np.concatenate([all_idx, all_idx]), "1-IP 双归属（Dijk）"))

W = 118
print("\n" + "=" * W)
print("同一份冻结 C11 分数，只换分组键与聚合规则")
print(f"{'分组键':<24}{'实体数':>10}{'正例实体':>10}{'先验':>10}{'流数中位':>10}"
      f"{'max AP':>10}{'Lp AP':>10}{'max DR@4%':>12}{'Lp DR@4%':>12}")
for r in RES:
    print(f"{r['key']:<24}{r['n_entity']:>10,}{r['n_pos_entity']:>10,}{r['prior']:>10.6f}"
          f"{r['median_flows']:>10.1f}{r['max_ap']:>10.6f}{r['Lp_ap']:>10.6f}"
          f"{r['max_dr_at_fpr']:>12.6f}{r['Lp_dr_at_fpr']:>12.6f}")
print("-" * W)
print("先验随键改变，故 AP 不可跨键直接比大小；跨键比较看 DR@4%FPR 与 AP/先验的提升倍数。")
for r in RES:
    print(f"  {r['key']:<24} Lp AP/先验 = {r['Lp_ap']/r['prior']:>8.2f} 倍   "
          f"max AP/先验 = {r['max_ap']/r['prior']:>8.2f} 倍")
print("=" * W)

json.dump({"p_learned": P_LEARNED, "target_fpr": TARGET_FPR, "rows": RES},
          open(f"{OUT}/entity_key_compare.json", "w"), ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/entity_key_compare.json")
