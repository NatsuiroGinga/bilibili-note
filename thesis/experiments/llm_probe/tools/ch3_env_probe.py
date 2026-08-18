# -*- coding: utf-8 -*-
"""探针：LSPR23 内部是否存在可用作「多源环境」的划分依据。

动因：Gehri 2023 的多环境选择用了四个源数据集（LS17/18/19/21A，不同年份 + 不同参演国），
本课题此前断言「只有一个源年、无法照做」。但该断言未经核查——
LSPR 是多国联合演习，原始流表里有 Segment 与 Expoid 等演习身份字段，
它们被禁止入模，但用作**环境划分依据**是另一回事（Dijk 2026 即用 Expoid 做分组键）。

本脚本只统计基数与规模，不训练、不评价、不接触 LSPR24。
回答：这些字段能否切出若干个规模相当、且各自含足够恶意实体的「环境」，
以支持留一环境交叉验证。

判据（事前定死）：至少 3 个环境，每个环境的恶意实体数 >= 30，
且最大环境的流数不超过最小环境的 20 倍。三条全满足才算可行。
"""
import json
import os
import zipfile

import numpy as np
import pyarrow.csv as pacsv

BASE = "/root/autodl-tmp/thesis/experiments/llm_probe/data/raw"
Z23 = f"{BASE}/lspr23-v1/ls23pr_flows.zip"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-env-probe"
os.makedirs(OUT, exist_ok=True)

CAND = ["Segment_src", "Segment_dst", "Expoid_src", "Expoid_dst",
        "profile", "capture_id", "Label_src", "Label_dst"]

with zipfile.ZipFile(Z23) as zf:
    inner = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
    with zf.open(inner) as fh:
        head = pacsv.read_csv(fh, read_options=pacsv.ReadOptions(block_size=1 << 22))
        cols = head.schema.names
        break_at = head.num_rows

print(f"LSPR23 表头共 {len(cols)} 列，首块 {break_at:,} 行")
present = [c for c in CAND if c in cols]
absent = [c for c in CAND if c not in cols]
print(f"存在的候选划分字段：{present}")
print(f"不存在的：{absent}")

if not present:
    print("\n无任何候选划分字段 → 多源环境不可构造，Gehri 路线确实不适用")
    json.dump({"present": [], "feasible": False}, open(f"{OUT}/env_probe.json", "w"),
              ensure_ascii=False, indent=2)
    raise SystemExit(0)

# 全量读取所需列（含分组键与标签），统计每个候选字段的环境划分质量
need = present + ["SrcIP", "DstIP", "Label"]
with zipfile.ZipFile(Z23) as zf:
    inner = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
    with zf.open(inner) as fh:
        t = pacsv.read_csv(fh, read_options=pacsv.ReadOptions(block_size=1 << 26),
                           convert_options=pacsv.ConvertOptions(include_columns=need))
print(f"全量读入 {t.num_rows:,} 行，取用 {len(need)} 列")

y = np.asarray(t.column("Label").to_numpy(zero_copy_only=False)).astype(np.float32)
s = np.asarray(t.column("SrcIP").to_pylist(), object)
d = np.asarray(t.column("DstIP").to_pylist(), object)
key = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s, d)], object)
_, ent = np.unique(key, return_inverse=True)
NE = int(ent.max()) + 1
elab = np.zeros(NE, np.float32); np.maximum.at(elab, ent, y)
print(f"LSPR23 实体 {NE:,}  恶意实体 {int(elab.sum()):,}")
del key, s, d

W = 96
print("\n" + "=" * W)
print("各候选字段作为环境划分依据的质量")
print(f"{'字段':<16}{'取值数':>9}{'最大环境流数':>14}{'最小环境流数':>14}{'规模比':>9}"
      f"{'恶意实体>=30 的环境数':>22}")
RES = {}
for c in present:
    v = np.asarray(t.column(c).to_pylist(), object)
    uv, inv = np.unique(v, return_inverse=True)
    k = len(uv)
    if k < 2 or k > 5000:
        print(f"{c:<16}{k:>9,}{'—':>14}{'—':>14}{'—':>9}{'取值数不适合分环境':>22}")
        RES[c] = {"n_values": int(k), "usable": False, "reason": "取值数不适合"}
        continue
    flows = np.bincount(inv, minlength=k)
    # 每个环境内的恶意实体数：该环境内出现过的实体中，恶意实体的个数
    npos = []
    for j in range(k):
        m = inv == j
        e_in = np.unique(ent[m])
        npos.append(int(elab[e_in].sum()))
    npos = np.array(npos)
    ok_env = int((npos >= 30).sum())
    ratio = flows.max() / max(flows.min(), 1)
    RES[c] = {"n_values": int(k), "flows_max": int(flows.max()), "flows_min": int(flows.min()),
              "size_ratio": float(ratio), "env_with_30plus_pos": ok_env,
              "pos_per_env": npos.tolist()[:20]}
    print(f"{c:<16}{k:>9,}{flows.max():>14,}{flows.min():>14,}{ratio:>9.1f}{ok_env:>22}")
    del v

print("-" * W)
print("事前判据：至少 3 个环境、每环境恶意实体 >= 30、最大/最小环境流数比 <= 20，三条全满足")
feasible = []
for c, r in RES.items():
    if not r.get("usable", True):
        continue
    if r.get("env_with_30plus_pos", 0) >= 3 and r.get("size_ratio", 1e9) <= 20:
        feasible.append(c)
if feasible:
    print(f"→ 可行的划分字段：{feasible}。Gehri 式多源环境选择在本课题**可以构造**，"
          f"此前「只有一个源环境」的断言不成立。")
else:
    print("→ 无字段同时满足三条判据。Gehri 式多源环境选择不可构造，此前断言成立。")
print("=" * W)

json.dump({"present": present, "absent": absent, "n_entity": NE,
           "n_pos_entity": int(elab.sum()), "fields": RES, "feasible": feasible},
          open(f"{OUT}/env_probe.json", "w"), ensure_ascii=False, indent=2)
print(f"结果已存 {OUT}/env_probe.json")
