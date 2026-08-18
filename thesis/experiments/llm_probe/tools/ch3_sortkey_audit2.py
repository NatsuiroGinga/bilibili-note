# -*- coding: utf-8 -*-
"""序列排序键核实第二部分：量化按起始时间排序带来的因果性偏差（只读，不占 GPU）。

E. 相邻位置上「前一条流的 mTimestampLast 晚于后一条流的 mTimestampStart」的比例，
   即按起始时间拼接上下文时，前文流在后文流开始时尚未结束、其完整流统计尚不可见的比例。
F. mTimestampStart > mTimestampLast 的行数（冻结合同要求整行隔离）。
G. 若改按 available_ns = mTimestampLast 排序，序列内成员的重排比例（相对当前顺序）。
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

bad = 0
total = 0
reorder = 0
for a in range(0, len(I24), CHUNK):
    i = I24[a:a + CHUNK]
    m = M24[a:a + CHUNK]
    ok = (m[:, 1:] > 0) & (m[:, :-1] > 0)
    prev_last = last_col[i][:, :-1]
    next_start = start_col[i][:, 1:]
    bad += int(((prev_last > next_start) & ok).sum())
    total += int(ok.sum())
    # G：同一相邻对在 available_ns 口径下是否需要交换
    prev_avail = last_col[i][:, :-1]
    next_avail = last_col[i][:, 1:]
    reorder += int(((prev_avail > next_avail) & ok).sum())

log(f"E. 前流未结束即出现后流的相邻位置：{bad}/{total} = {bad / total:.6f}")
log(f"G. 改按 available_ns 排序时需要交换的相邻位置：{reorder}/{total} = {reorder / total:.6f}")

neg = int((start_col > last_col).sum())
log(f"F. mTimestampStart > mTimestampLast 的行数：{neg}/{n24} = {neg / n24:.8f}")
log("核实完成")
