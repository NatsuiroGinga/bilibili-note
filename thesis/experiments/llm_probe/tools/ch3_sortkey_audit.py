# -*- coding: utf-8 -*-
"""序列排序键只读核实：判定 dijk-repro 缓存里的 I23/I24/T23 用的是哪个时间字段。

只读，不写任何缓存，不占 GPU。判据：
  A. T23[i] 是否等于 t23_flow[I23[i, 0]]（即序列首流的 mTimestampStart）。
  B. 每条 LSPR23 序列内，mTimestampStart 是否逐位非降。
  C. 每条 LSPR24 序列内，mTimestampStart 与 mTimestampLast 分别是否逐位非降。
     若 start 违例为 0 而 last 违例大于 0，则排序键是起始时间而非可用时刻。
  D. 报告 LSPR24 的 last-start（流持续时间）分位数，佐证两字段并非同一个量。
"""

import time

import numpy as np
import pyarrow.parquet as pq

T0 = time.time()


def log(m: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
P24 = f"{ROOT}/data/raw/lspr24-v1/lspr24_v2.parquet"
CHUNK = 20000


def seq_violations(idx: np.ndarray, msk: np.ndarray, values: np.ndarray) -> tuple:
    """返回 (逆序位置数, 参与比较的位置数)。只在掩码有效的相邻位置上比较。"""
    bad = 0
    total = 0
    for a in range(0, len(idx), CHUNK):
        i = idx[a:a + CHUNK]
        m = msk[a:a + CHUNK]
        v = values[i]
        d = np.diff(v, axis=1)
        ok = (m[:, 1:] > 0) & (m[:, :-1] > 0)
        bad += int(((d < 0) & ok).sum())
        total += int(ok.sum())
    return bad, total


log("载入 LSPR23 缓存")
I23 = np.load(f"{CACHE}/I23.npy")
M23 = np.load(f"{CACHE}/M23.npy")
T23 = np.load(f"{CACHE}/T23.npy")
t23_flow = np.load(f"{CACHE}/t23_flow.npy")
log(f"I23={I23.shape} T23={T23.shape} t23_flow={t23_flow.shape}")

head_start = t23_flow[I23[:, 0]]
same = int((T23 == head_start).sum())
log(f"A. T23 == t23_flow[I23[:,0]] 的比例：{same}/{len(T23)}")
log(f"   T23 范围 [{T23.min():.0f}, {T23.max():.0f}]，"
    f"t23_flow 范围 [{t23_flow.min():.0f}, {t23_flow.max():.0f}]")

bad23, tot23 = seq_violations(I23, M23, t23_flow)
log(f"B. LSPR23 序列内 mTimestampStart 逆序位置：{bad23}/{tot23}")
del I23, M23, T23, t23_flow, head_start

log("载入 LSPR24 缓存与 parquet 时间列")
I24 = np.load(f"{CACHE}/I24.npy")
M24 = np.load(f"{CACHE}/M24.npy")
t24_start = np.load(f"{CACHE}/t24.npy")
pf = pq.ParquetFile(P24)
n24 = pf.metadata.num_rows
start_col = np.empty(n24, np.float64)
last_col = np.empty(n24, np.float64)
o = 0
for rg in range(pf.metadata.num_row_groups):
    tb = pf.read_row_group(rg, columns=["mTimestampStart", "mTimestampLast"])
    k = tb.num_rows
    start_col[o:o + k] = np.asarray(tb.column("mTimestampStart").to_numpy(zero_copy_only=False), np.float64)
    last_col[o:o + k] = np.asarray(tb.column("mTimestampLast").to_numpy(zero_copy_only=False), np.float64)
    o += k
    del tb
log(f"I24={I24.shape} parquet 行数={n24:,}")
log(f"   t24.npy 与 parquet mTimestampStart 逐位相等：{bool(np.array_equal(t24_start, start_col))}")

bad_s, tot_s = seq_violations(I24, M24, start_col)
bad_l, tot_l = seq_violations(I24, M24, last_col)
log(f"C. LSPR24 序列内 mTimestampStart 逆序位置：{bad_s}/{tot_s}")
log(f"   LSPR24 序列内 mTimestampLast  逆序位置：{bad_l}/{tot_l}")

dur = last_col - start_col
q = np.percentile(dur, [0, 25, 50, 75, 90, 99, 100])
log("D. LSPR24 流持续时间（微秒）分位 0/25/50/75/90/99/100："
    + " ".join(f"{v:.0f}" for v in q))
log(f"   持续时间为 0 的流占比：{float((dur == 0).mean()):.6f}")
log("核实完成")
