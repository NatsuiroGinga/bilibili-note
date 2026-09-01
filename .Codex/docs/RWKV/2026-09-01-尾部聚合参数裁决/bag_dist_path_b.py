# -*- coding: utf-8 -*-
"""验证/训练袋分布精确复算 + 路径 B（α 复用 β 预算网格）退化率核算。

只读 E23/T23/M23（实体、时间戳、有效掩码），不读 y23，不读 LSPR24。
切分逐字复刻 ch3_ft_transformer_field_token_protocol_a.source_split。
"""
import json
import numpy as np

ROOT = "/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe"
CACHE = ROOT + "/runs/diagnostics/dijk-repro/cache"

SEED = 42
VALIDATION_FRACTION = 0.1
TIME_TAIL_FRACTION = 0.15
SEQUENCE_LENGTH = 128

E = np.load(f"{CACHE}/E23.npy")
T = np.load(f"{CACHE}/T23.npy")
M = np.load(f"{CACHE}/M23.npy", mmap_mode="r")

# --- source_split 逐字复刻 ---
unique_entity = np.unique(E)
perm = np.random.RandomState(SEED).permutation(len(unique_entity))
count = max(1, int(len(unique_entity) * VALIDATION_FRACTION))
validation_entities = set(unique_entity[perm[:count]].tolist())
entity_mask = np.fromiter((v in validation_entities for v in E), bool, len(E))
time_cut = np.quantile(T, 1.0 - TIME_TAIL_FRACTION)
time_mask = T >= time_cut
train_rows = np.flatnonzero(~(entity_mask | time_mask))
validation_rows = np.flatnonzero(entity_mask & ~time_mask)
stats = dict(
    entity_count=int(len(unique_entity)),
    train_sequences=int(len(train_rows)),
    validation_sequences=int(len(validation_rows)),
    intersection=int(np.intersect1d(train_rows, validation_rows).size),
)
assert stats == dict(entity_count=150680, train_sequences=208598,
                     validation_sequences=22444, intersection=0), stats
print("切分统计与冻结身份逐项相等:", stats)

def bag_sizes(rows):
    valid_counts = (np.asarray(M[rows][:, :SEQUENCE_LENGTH]) > 0.5).sum(axis=1)
    ent = E[rows]
    uniq, inv = np.unique(ent, return_inverse=True)
    m = np.bincount(inv, weights=valid_counts).astype(np.int64)
    return m, int(valid_counts.sum())

m_val, val_flows = bag_sizes(validation_rows)
m_trn, trn_flows = bag_sizes(train_rows)

# --- 与 probe.json 锚点逐位核验（验证侧）---
anchors = {
    "scored_flows": (val_flows, 1238500),
    "scored_entities": (len(m_val), 13529),
    "flow_count_median": (float(np.median(m_val)), 2.0),
    "m_ge_2": (int((m_val >= 2).sum()), 7239),
    "m_eq_1": (int((m_val == 1).sum()), 6290),
    "m_2_to_9": (int(((m_val >= 2) & (m_val <= 9)).sum()), 5919),
    "m_10_to_99": (int(((m_val >= 10) & (m_val <= 99)).sum()), 874),
    "m_ge_100": (int((m_val >= 100).sum()), 446),
}
# α 档 k>1 计数锚点：⌈α·m⌉>=2 ⟺ m > 1/α
for a, expect in [(0.05, 850), (0.1, 1224), (0.2, 2140), (0.3, 3186),
                  (0.5, 4279), (0.7, 7239), (1.0, 7239)]:
    got = int((np.ceil(a * m_val) >= 2).sum())
    anchors[f"alpha={a}_k_gt_1"] = (got, expect)
# max_k 锚点：α=0.05 时 max_k=22407
anchors["alpha=0.05_max_k"] = (int(np.ceil(0.05 * m_val.max())), 22407)
ok = all(g == e for g, e in anchors.values())
for k, (g, e) in anchors.items():
    print(f"  锚点 {k}: 复算 {g} 记录 {e} {'一致' if g == e else '不一致'}")
assert ok, "锚点核验失败"
print("验证袋分布复算与 probe.json 全部锚点一致；最大袋 m_max =", int(m_val.max()))

# --- 路径 B：k = max(1, ⌈β·m⌉)，β 取冻结六档 K/N_-（N_- 按预算文档 121336）---
N_NEG = 121336
BUDGETS = [121, 606, 1213, 2426, 4853, 9706]
print("\n训练侧实体数 =", len(m_trn), "训练侧流数 =", trn_flows,
      "训练袋中位数 =", float(np.median(m_trn)), "训练最大袋 =", int(m_trn.max()))

def path_b_row(m, name):
    print(f"\n[{name}] 实体数 {len(m)}")
    print(f"{'K':>6} {'beta':>10} {'m_min(k>1)':>10} {'k>1实体数':>9} {'k>1占比':>8} "
          f"{'mean_k':>9} {'mean_k/max袋k':>12}")
    for K in BUDGETS:
        beta = K / N_NEG
        k = np.maximum(1, np.ceil(beta * m).astype(np.int64))
        n_act = int((k > 1).sum())
        m_min = int(np.floor(1.0 / beta)) + 1  # 最小的使 β·m>1 的整数 m
        print(f"{K:>6} {beta:>10.6f} {m_min:>10} {n_act:>9} {n_act/len(m):>8.4f} "
              f"{float(k.mean()):>9.4f} {int(k.max()):>12}")

path_b_row(m_val, "验证袋（评价侧）")
# 训练侧：BER 排序袋截断 8192
m_trn_trunc = np.minimum(m_trn, 8192)
path_b_row(m_trn_trunc, "训练袋（截断 8192，BER 排序侧）")

# --- 路径 A 对照：α=0.5 与 α∈{0.25,1/3} 的作用面与梯度支撑 ---
print("\n[路径 A 对照] k = max(1, ⌈α·m⌉)")
for a in [0.25, 1/3, 0.5]:
    for m, name in [(m_val, "验证"), (m_trn_trunc, "训练截断")]:
        k = np.maximum(1, np.ceil(a * m).astype(np.int64))
        sat = int((k >= np.maximum(m, 1))[m >= 2].sum())  # m>=2 中 k==m（饱和为均值）的实体
        print(f"  α={a:.4f} [{name}] k>1 实体 {int((k>1).sum())} "
          f"({int((k>1).sum())/len(m):.4f}) mean_k {float(k.mean()):.3f} "
          f"饱和为均值的 m>=2 实体 {sat}")

# 训练袋分布的补充分位数（供报告引用）
qs = [50, 75, 90, 95, 99, 99.9]
print("\n验证袋分位数:", {q: float(np.percentile(m_val, q)) for q in qs})
print("训练袋分位数:", {q: float(np.percentile(m_trn, q)) for q in qs})
for thr in [13, 26, 51, 101, 201, 1003]:
    print(f"  m>={thr}: 验证 {int((m_val>=thr).sum())} 训练 {int((m_trn>=thr).sum())}")
