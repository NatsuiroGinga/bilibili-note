# -*- coding: utf-8 -*-
"""分组粒度扫描的前置侦察：只读，确认三件事后才允许写正式扫描脚本。

1. t24 的时间单位（秒还是毫秒），决定会话切分阈值 Delta 的量纲
2. IP 字符串格式与唯一 IP 数，决定 /24 与 /64 截断如何实现
3. parquet 行序与 cache 行序是否逐位一致，决定能否从 parquet 取端口/协议拼 5 元组

本文件是一次性侦察，跑完即删，不产生任何实验结论。
"""
import numpy as np
import pyarrow.parquet as pq

ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
CACHE = f"{ROOT}/runs/diagnostics/dijk-repro/cache"
P24 = f"{ROOT}/data/raw/lspr24-v1/lspr24_v2.parquet"

t24 = np.load(f"{CACHE}/t24.npy")
print(f"[t24] n={len(t24):,} min={t24.min():.3f} max={t24.max():.3f} "
      f"跨度={t24.max()-t24.min():.1f} dtype={t24.dtype}")
d = np.diff(np.sort(t24))
d = d[d > 0]
print(f"[t24] 正的相邻间隔：min={d.min():.9f} 中位={np.median(d):.9f} max={d.max():.3f}")
print(f"[t24] 若为秒，跨度={(t24.max()-t24.min())/3600:.2f} 小时；"
      f"若为毫秒，跨度={(t24.max()-t24.min())/3600/1000:.2f} 小时")

s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
print(f"[ip] s24 dtype={s24.dtype} 前3={list(s24[:3])}")
print(f"[ip] d24 dtype={d24.dtype} 前3={list(d24[:3])}")
allip = np.unique(np.concatenate([s24, d24]))
print(f"[ip] 唯一 IP 总数={len(allip):,} 唯一源={len(np.unique(s24)):,} 唯一目的={len(np.unique(d24)):,}")
v6 = [a for a in allip if ":" in str(a)]
print(f"[ip] 含冒号(IPv6)={len(v6):,} 例={v6[:3]}")
odd = [a for a in allip if ":" not in str(a) and str(a).count(".") != 3]
print(f"[ip] 非标准 IPv4 形态={len(odd)} 例={odd[:5]}")
import ipaddress
bad = []
for a in allip:
    try:
        ipaddress.ip_address(str(a))
    except ValueError:
        bad.append(a)
print(f"[ip] ipaddress 无法解析={len(bad)} 例={bad[:5]}")

# parquet 行序对齐：逐行组比对 SrcIP/DstIP，任何一处不一致即判定不可用
pf = pq.ParquetFile(P24)
print(f"[parquet] 行数={pf.metadata.num_rows:,} 行组={pf.metadata.num_row_groups} "
      f"与 cache 等长={pf.metadata.num_rows == len(s24)}")
o = 0
mismatch = 0
for rg in range(pf.metadata.num_row_groups):
    tb = pf.read_row_group(rg, columns=["SrcIP", "DstIP"])
    k = tb.num_rows
    a = np.asarray(tb.column("SrcIP").to_pylist(), object)
    b = np.asarray(tb.column("DstIP").to_pylist(), object)
    mismatch += int((a != s24[o:o + k]).sum() + (b != d24[o:o + k]).sum())
    o += k
    del tb
print(f"[parquet] 行序比对完成，覆盖 {o:,} 行，不一致 {mismatch} 处")

tb = pf.read_row_group(0, columns=["SrcPort", "DstPort", "Protocol", "L3/L4 Protocol"])
for c in ["SrcPort", "DstPort", "Protocol", "L3/L4 Protocol"]:
    col = tb.column(c)
    print(f"[五元组] {c}: type={col.type} 前5={col.slice(0,5).to_pylist()}")

import pandas
import scipy
print(f"[env] pandas={pandas.__version__} scipy={scipy.__version__} numpy={np.__version__}")
