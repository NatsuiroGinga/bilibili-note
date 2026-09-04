# -*- coding: utf-8 -*-
"""门控组合方案审核：用真实采样器测「空活动集是否成串出现」。

被审文档 (thesis/methods/第三章-活动集门控的ETA-BER交替组合.md) §二 硬约定 2 称
「空活动集有强自相关（成串出现），一步滞后是可接受的近似」。本脚本用**真实**
ch3_ft_entity_stratified_sampler.EntityStratifiedSampler 与**真实** LSPR23 缓存
直接测这个假设。只用 numpy，不碰 GPU、不做前向、不训练。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

TOOLS = Path("/root/autodl-tmp/thesis/experiments/llm_probe/tools")
sys.path.insert(0, str(TOOLS))
CACHE = Path("/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache")

import ch3_ft_entity_stratified_sampler as S  # noqa: E402

N_POS, N_NEG, SEED, N_STEPS = 2, 64, 42, 10000

cache = {
    "E23": np.load(CACHE / "E23.npy"),
    "I23": np.load(CACHE / "I23.npy", mmap_mode="r"),
    "M23": np.load(CACHE / "M23.npy", mmap_mode="r"),
    "T23": np.load(CACHE / "T23.npy"),
    "y23": np.load(CACHE / "y23.npy"),
}
cfg = S.EntityStratifiedSamplerConfig(n_pos=N_POS, n_neg=N_NEG, max_bag_flows=8192)
sampler = S.EntityStratifiedSampler(
    entity_of_segment=cache["E23"], segment_flow_indices=cache["I23"],
    segment_valid_mask=cache["M23"], segment_timestamp=cache["T23"],
    flow_labels=cache["y23"], config=cfg,
)
pool = sampler.positive_pool_size
print("POS_POOL", pool, "NEG_POOL", sampler.negative_pool_size, flush=True)

# 只重放正实体轮转（活动集判据 mean(pairwise > xi_k) 里的 xi 是 per-正实体持久状态）。
rng = np.random.default_rng(SEED)
pos_draws = np.empty((N_STEPS, N_POS), dtype=np.int64)
for t in range(N_STEPS):
    pos_draws[t] = sampler._draw_positive_entities(rng)

# ---- 测量 A：相邻步正实体集的重叠 ----
overlaps = np.array([len(set(pos_draws[t]) & set(pos_draws[t + 1])) for t in range(N_STEPS - 1)])
lag1_overlap_rate = float((overlaps > 0).mean())
# 独立均匀抽 2/239 的重叠基线（有放回近似）：1-(1-2/pool)^2
indep_overlap = 1.0 - (1.0 - N_POS / pool) ** N_POS
print("A_lag1_share_any_positive_rate", round(lag1_overlap_rate, 6), flush=True)
print("A_indep_reference_rate", round(indep_overlap, 6), flush=True)
print("A_mean_shared_count", round(float(overlaps.mean()), 6), flush=True)
lag_k = {k: float((np.array([len(set(pos_draws[t]) & set(pos_draws[t + k])) for t in range(N_STEPS - k)]) > 0).mean()) for k in (1, 2, 5, 10, 50, 100, 119, 120, 200)}
print("A_share_rate_by_lag", json.dumps({str(k): round(v, 5) for k, v in lag_k.items()}), flush=True)


def autocorr1(x: np.ndarray) -> float:
    x = x.astype(np.float64)
    m, v = x.mean(), x.var()
    if v == 0:
        return float("nan")
    return float(((x[:-1] - m) * (x[1:] - m)).mean() / v)


# ---- 测量 B：冷实体集模型（entity 驱动 clustering 的**上界**）----
# 假设 empty_t = 1 当且仅当该步抽到的 2 个正实体都属于固定冷集 C。这是「活动集空转
# 完全由实体身份决定」的极端情形，不含任何逐步批噪声，故给出实体驱动自相关的上界。
targets = {"epoch4_0.133": 0.133, "epoch5_0.176": 0.176, "epoch6_0.230": 0.230,
           "epoch7_0.347": 0.347, "epoch8_0.395": 0.395, "run_mean_0.1966": 0.1966}
rows = []
rng2 = np.random.default_rng(20260904)
pos_ids = np.flatnonzero(np.isin(np.arange(pos_draws.max() + 1), np.unique(pos_draws)))
uniq = np.unique(pos_draws)
for name, target in targets.items():
    best = None
    for m in range(2, pool + 1):
        cold = set(uniq[rng2.permutation(len(uniq))[:m]].tolist())
        ind = np.array([1 if (pos_draws[t, 0] in cold and pos_draws[t, 1] in cold) else 0
                        for t in range(N_STEPS)])
        p = ind.mean()
        if best is None or abs(p - target) < abs(best[1] - target):
            best = (m, p, ind)
        if p > target + 0.05:
            break
    m, p, ind = best
    r1 = autocorr1(ind)
    # 门控对位统计：g_t = empty_{t-1}
    g = ind[:-1]
    cur = ind[1:]
    gate_on = g.sum()
    hit = int(((g == 1) & (cur == 1)).sum())
    miss_fire = int(((g == 1) & (cur == 0)).sum())   # 门开但 BER 活动 → 干扰
    miss_skip = int(((g == 0) & (cur == 1)).sum())   # 门关但 BER 空转 → 漏用
    rows.append({
        "case": name, "target_p": target, "cold_set_size": m, "realized_p": round(float(p), 5),
        "lag1_autocorr": round(r1, 5),
        "gate_fire_rate": round(float(gate_on / len(g)), 5),
        "P_empty_given_gate_on": round(hit / gate_on, 5) if gate_on else None,
        "interference_step_frac": round(miss_fire / len(g), 5),
        "missed_opportunity_frac": round(miss_skip / len(g), 5),
    })
    print("B_ROW " + json.dumps(rows[-1]), flush=True)

print("DONE_GATE_AUTOCORR", flush=True)
