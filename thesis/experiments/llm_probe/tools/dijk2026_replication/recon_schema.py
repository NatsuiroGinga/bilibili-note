"""只读勘察 LSPR23 CSV 表头与 LSPR24 Parquet 模式，核验 Dijk 83 字段可用性。"""
import io
import subprocess
import sys

import pyarrow.parquet as pq

ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe"
LSPR23_ZIP = f"{ROOT}/data/raw/lspr23-v1/ls23pr_flows.zip"
LSPR24_PARQUET = f"{ROOT}/data/raw/lspr24-v1/lspr24_v2.parquet"

DIJK_EXTRA = [
    "SrcPort", "DstPort", "L3/L4 Protocol", "Int/Ext Dst IP",
    "External_src", "External_dst",
]

print("=== LSPR24 parquet 元信息 ===")
pf = pq.ParquetFile(LSPR24_PARQUET)
md = pf.metadata
print("num_rows =", md.num_rows)
print("num_columns =", md.num_columns)
print("num_row_groups =", md.num_row_groups)
sizes = [md.row_group(i).num_rows for i in range(md.num_row_groups)]
print("row_group rows: min=%d max=%d mean=%.1f" % (min(sizes), max(sizes), sum(sizes) / len(sizes)))
schema = pf.schema_arrow
print("--- 全部列名与类型 ---")
for f in schema:
    print(f"{f.name!r}\t{f.type}")

print()
print("=== LSPR23 CSV 表头 ===")
proc = subprocess.Popen(
    ["unzip", "-p", LSPR23_ZIP, "ls23pr_v1.csv"],
    stdout=subprocess.PIPE,
)
raw = proc.stdout.read(200000)
proc.stdout.close()
proc.kill()
text = raw.decode("utf-8", errors="replace")
lines = text.splitlines()
header = lines[0].split(",")
print("csv 列数 =", len(header))
for i, name in enumerate(header):
    print(i, repr(name))
print("--- 前两条样本行 ---")
for line in lines[1:3]:
    print(line[:600])
