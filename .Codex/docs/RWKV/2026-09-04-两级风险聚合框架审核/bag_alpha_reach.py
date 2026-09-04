# -*- coding: utf-8 -*-
"""E1：用真实袋大小分布，算插值式软 top-k 中 α 的**实际作用面**。

只读 E23/T23/M23（实体、时间戳、有效掩码），**不读 y23**，不读 LSPR24 ⟹ target_reads = 0。
切分与锚点逐字复用 2026-09-01-尾部聚合参数裁决/bag_dist_path_b.py（已与 probe.json 对拍）。

三个观测量（全部与逐流分数取值无关，只由袋大小 m_e 与 α 决定，故是精确结论）：

  硬算子  k(α) = max(1, ceil(α·m))                     —— 现行实现
  软算子  t(α) = clamp(α·m, 1, m)                      —— 被审文档 §二 提出

  (a) 梯度作用面   ∂S_e/∂α ≠ 0 ⟺ 1 < α·m_e < m_e      （clamp 两侧导数为 0）
  (b) 行为改变面   S_e(α) ≠ S_e(0.5) ⟺ t(α) ≠ t(0.5)   （t 相等 ⟹ 逐位相同）
  (c) 硬软一致面   软算子在 α 处是否等于硬算子          （α·m 为整数时相等）
"""
import numpy as np

ROOT = "/Users/bilibili/personal/note/.worktrees/ch4-dtep-pbc-20260819/thesis/experiments/llm_probe"
CACHE = ROOT + "/runs/diagnostics/dijk-repro/cache"
SEED, VALIDATION_FRACTION, TIME_TAIL_FRACTION, SEQUENCE_LENGTH = 42, 0.1, 0.15, 128
TRUNCATE_LENGTH = 8192  # BER 排序侧袋上限（ranking_cfg["truncate_length"]）

E = np.load(f"{CACHE}/E23.npy")
T = np.load(f"{CACHE}/T23.npy")
M = np.load(f"{CACHE}/M23.npy", mmap_mode="r")

unique_entity = np.unique(E)
perm = np.random.RandomState(SEED).permutation(len(unique_entity))
count = max(1, int(len(unique_entity) * VALIDATION_FRACTION))
validation_entities = set(unique_entity[perm[:count]].tolist())
entity_mask = np.fromiter((v in validation_entities for v in E), bool, len(E))
time_cut = np.quantile(T, 1.0 - TIME_TAIL_FRACTION)
train_rows = np.flatnonzero(~(entity_mask | (T >= time_cut)))
validation_rows = np.flatnonzero(entity_mask & ~(T >= time_cut))
stats = dict(entity_count=int(len(unique_entity)), train_sequences=int(len(train_rows)),
             validation_sequences=int(len(validation_rows)),
             intersection=int(np.intersect1d(train_rows, validation_rows).size))
assert stats == dict(entity_count=150680, train_sequences=208598,
                     validation_sequences=22444, intersection=0), stats
print("切分统计与冻结身份逐项相等:", stats)


def bag_sizes(rows):
    valid_counts = (np.asarray(M[rows][:, :SEQUENCE_LENGTH]) > 0.5).sum(axis=1)
    uniq, inv = np.unique(E[rows], return_inverse=True)
    return np.bincount(inv, weights=valid_counts).astype(np.int64)


m_val = bag_sizes(validation_rows)
m_trn = bag_sizes(train_rows)
m_trn_trunc = np.minimum(m_trn, TRUNCATE_LENGTH)

# 锚点复核（防止我算的是另一批袋）
assert len(m_val) == 13529 and int((m_val == 1).sum()) == 6290, "验证袋锚点不符"
print(f"验证袋锚点一致：实体 {len(m_val)}，m=1 实体 {int((m_val==1).sum())}")
print(f"训练袋实体 {len(m_trn)}（文档记 121501），截断 {TRUNCATE_LENGTH} 后最大袋 {int(m_trn_trunc.max())}")
print(f"训练袋 P50/P75/P90/P95/P99 = "
      f"{[float(np.percentile(m_trn, q)) for q in (50, 75, 90, 95, 99)]}，均值 {float(m_trn.mean()):.1f}")
print(f"k_e=1（α=0.5，硬算子）的训练实体占比 = {float((np.ceil(0.5*m_trn_trunc) <= 1).mean()):.4f}")


def report(m, name):
    n = len(m)
    print(f"\n===== {name}（实体 {n}） =====")
    t_half = np.clip(0.5 * m, 1.0, m.astype(float))       # 软算子在 α=0.5 的取用条数
    k_half = np.maximum(1, np.ceil(0.5 * m))              # 硬算子在 α=0.5

    print(f"{'α':>8} {'软:梯度作用面':>14} {'软:相对α=0.5行为改变':>20} "
          f"{'硬:相对α=0.5行为改变':>20} {'软≠硬':>10}")
    for a in (0.02, 0.05, 0.10, 0.20, 1/3, 0.40, 0.50, 0.60, 0.75, 1.00):
        t = np.clip(a * m, 1.0, m.astype(float))
        k = np.maximum(1, np.ceil(a * m))
        grad_face = float(((a * m > 1.0) & (a * m < m)).mean())       # 严格内点
        chg_soft = float((t != t_half).mean())
        chg_hard = float((k != k_half).mean())
        soft_ne_hard = float((t != k).mean())                          # α·m 非整数即不等
        print(f"{a:>8.4f} {grad_face:>14.4f} {chg_soft:>20.4f} "
              f"{chg_hard:>20.4f} {soft_ne_hard:>10.4f}")

    # 关键切面：α 只在 (0, 1/2] 内移动时，行为改变面的上确界
    m_ge3 = float((m >= 3).mean())
    print(f"\n  α ∈ (0, 1/2] 内：行为改变面的**上确界** = P(m_e ≥ 3) = {m_ge3:.4f}"
          f"（m_e ≤ 2 的实体上 t ≡ 1 ≡ max，对每个可取 α 逐位相同）")
    print(f"  α = 0.5 处梯度作用面 = P(2 < m_e) 且 0.5m < m ⟹ P(m_e ≥ 3) = "
          f"{float(((0.5*m > 1.0) & (0.5*m < m)).mean()):.4f}")
    print(f"  m_e = 1 的实体占比 = {float((m == 1).mean()):.4f}（t ≡ 1，α 的梯度恒 0）")
    print(f"  m_e = 2 的实体占比 = {float((m == 2).mean()):.4f}")
    print(f"  m_e = 0 的实体占比 = {float((m == 0).mean()):.4f}")


report(m_trn_trunc, "训练侧（BER 负实体采样池，截断 8192）")
report(m_val, "验证侧（实体 AP 指标口径）")

# n_neg=64 均匀采样下，一步排序批里「α 有梯度」的负实体期望条数
p = float(((0.5 * m_trn_trunc > 1.0) & (0.5 * m_trn_trunc < m_trn_trunc)).mean())
print(f"\nn_neg=64 均匀采样：α=0.5 时每步期望有 {64*p:.1f}/64 个负实体向 α 回传梯度"
      f"（其余 {64*(1-p):.1f} 个的 ∂S_e/∂α 精确为 0）")
