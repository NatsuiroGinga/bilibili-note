# -*- coding: utf-8 -*-
"""序列排序键核实第三部分：按位置统计前缀里的"未来完成流"（只读，不占 GPU）。

3.5.1 的在线可计算性论断是"前缀递推在每条流结束时即可输出分数"。
若序列按 mTimestampStart 排序，前缀中可能存在结束时刻晚于当前流的流，
其完整流统计在当前流结束时尚不可见。本脚本统计这类位置的比例：

H. 位置 t（t>=1，掩码有效）中，前缀 max(mTimestampLast[0..t-1]) > mTimestampLast[t] 的比例。
I. 同一口径下，受影响序列（至少含一个这类位置）的比例。
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

I24 = np.load(f"{CACHE}/I24.npy")
M24 = np.load(f"{CACHE}/M24.npy")
pf = pq.ParquetFile(P24)
n24 = pf.metadata.num_rows
last_col = np.empty(n24, np.float64)
o = 0
for rg in range(pf.metadata.num_row_groups):
    tb = pf.read_row_group(rg, columns=["mTimestampLast"])
    k = tb.num_rows
    last_col[o:o + k] = np.asarray(tb.column("mTimestampLast").to_numpy(zero_copy_only=False), np.float64)
    o += k
    del tb
log(f"I24={I24.shape} parquet 行数={n24:,}")

leak_pos = 0
tot_pos = 0
leak_seq = 0
for a in range(0, len(I24), CHUNK):
    i = I24[a:a + CHUNK]
    m = M24[a:a + CHUNK] > 0
    v = np.where(m, last_col[i], -np.inf)
    pref = np.maximum.accumulate(v, axis=1)
    hit = np.zeros_like(m)
    hit[:, 1:] = m[:, 1:] & (pref[:, :-1] > v[:, 1:])
    leak_pos += int(hit.sum())
    tot_pos += int(m[:, 1:].sum())
    leak_seq += int(hit.any(axis=1).sum())

log(f"H. 前缀含结束更晚的流的位置：{leak_pos}/{tot_pos} = {leak_pos / tot_pos:.6f}")
log(f"I. 至少含一个这类位置的序列：{leak_seq}/{len(I24)} = {leak_seq / len(I24):.6f}")
log("核实完成")
