# -*- coding: utf-8 -*-
"""序列排序键核实第四部分：把同一组判据补到训练年度 LSPR23（只读，不占 GPU）。

只从压缩 CSV 里取 mTimestampStart / mTimestampLast 两列，不读特征列。
"""

import time
import zipfile

import numpy as np
import pyarrow.csv as pacsv

T0 = time.time()


def log(m: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
Z23 = f"{ROOT}/data/raw/lspr23-v1/ls23pr_flows.zip"
CHUNK = 20000

log("解析 LSPR23 时间列")
with zipfile.ZipFile(Z23) as zf:
    inner = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
    with zf.open(inner) as fh:
        t = pacsv.read_csv(
            fh,
            read_options=pacsv.ReadOptions(block_size=1 << 26),
            convert_options=pacsv.ConvertOptions(include_columns=["mTimestampStart", "mTimestampLast"]),
        )
start_col = np.asarray(t.column("mTimestampStart").to_numpy(zero_copy_only=False), np.float64)
last_col = np.asarray(t.column("mTimestampLast").to_numpy(zero_copy_only=False), np.float64)
del t
log(f"LSPR23 行数={len(start_col):,}")

t23_flow = np.load(f"{CACHE}/t23_flow.npy")
log(f"t23_flow 与 CSV mTimestampStart 逐位相等：{bool(np.array_equal(t23_flow, start_col))}")
del t23_flow

I23 = np.load(f"{CACHE}/I23.npy")
M23 = np.load(f"{CACHE}/M23.npy")

bad_s = bad_l = tot = leak_pos = leak_seq = 0
for a in range(0, len(I23), CHUNK):
    i = I23[a:a + CHUNK]
    m = M23[a:a + CHUNK] > 0
    ok = m[:, 1:] & m[:, :-1]
    s = start_col[i]
    v = last_col[i]
    bad_s += int(((np.diff(s, axis=1) < 0) & ok).sum())
    bad_l += int(((np.diff(v, axis=1) < 0) & ok).sum())
    tot += int(ok.sum())
    vm = np.where(m, v, -np.inf)
    pref = np.maximum.accumulate(vm, axis=1)
    hit = np.zeros_like(m)
    hit[:, 1:] = m[:, 1:] & (pref[:, :-1] > vm[:, 1:])
    leak_pos += int(hit.sum())
    leak_seq += int(hit.any(axis=1).sum())

log(f"B23. 序列内 mTimestampStart 逆序位置：{bad_s}/{tot}")
log(f"C23. 序列内 mTimestampLast  逆序位置：{bad_l}/{tot} = {bad_l / tot:.6f}")
log(f"H23. 前缀含结束更晚的流的位置：{leak_pos}/{tot} = {leak_pos / tot:.6f}")
log(f"I23seq. 至少含一个这类位置的序列：{leak_seq}/{len(I23)} = {leak_seq / len(I23):.6f}")

neg = int((start_col > last_col).sum())
log(f"F23. mTimestampStart > mTimestampLast 的行数：{neg}/{len(start_col)} = {neg / len(start_col):.8f}")
dur = last_col - start_col
q = np.percentile(dur, [0, 50, 90, 99, 100])
log("D23. 流持续时间（微秒）分位 0/50/90/99/100：" + " ".join(f"{x:.0f}" for x in q))
log("核实完成")
