"""只读探查 LSPR23 CSV 前 20 万行，确认 83 字段可解析与取值域（有界读取）。"""
import io
import subprocess
import sys

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv

sys.path.insert(0, "/root/autodl-tmp/thesis/experiments/llm_probe/tools/dijk2026_replication")
from dijk_fields import DIJK_FEATURES, LABEL_COLUMN, TIME_LAST_COLUMN, TIME_START_COLUMN

ZIP = "/root/autodl-tmp/thesis/experiments/llm_probe/data/raw/lspr23-v1/ls23pr_flows.zip"
MEMBER = "ls23pr_v1.csv"
N_LINES = 200001

print("开始有界读取前 %d 行" % N_LINES, flush=True)
proc = subprocess.run(
    f"unzip -p {ZIP} {MEMBER} | head -n {N_LINES}",
    shell=True, capture_output=True,
)
raw = proc.stdout
print("原始字节 =", len(raw), flush=True)

wanted = list(DIJK_FEATURES) + [TIME_START_COLUMN, TIME_LAST_COLUMN, LABEL_COLUMN]
types = {name: pa.float64() for name in DIJK_FEATURES}
types[TIME_START_COLUMN] = pa.int64()
types[TIME_LAST_COLUMN] = pa.int64()
types[LABEL_COLUMN] = pa.int32()

t = pacsv.read_csv(
    io.BytesIO(raw),
    read_options=pacsv.ReadOptions(use_threads=True),
    convert_options=pacsv.ConvertOptions(include_columns=wanted, column_types=types),
)
print("解析行数 =", t.num_rows, " 列数 =", t.num_columns, flush=True)
for c in ("External_src", "External_dst", "L3/L4 Protocol", "Int/Ext Dst IP",
          "Protocol", "SrcPort", "DstPort", LABEL_COLUMN):
    u = pc.unique(t.column(c))
    vals = sorted(x for x in u.to_pylist() if x is not None)
    print(c, "distinct=", len(u), vals[:8], "...", vals[-3:] if len(vals) > 8 else "", flush=True)
print("mTimestampStart min/max =", pc.min(t.column(TIME_START_COLUMN)).as_py(),
      pc.max(t.column(TIME_START_COLUMN)).as_py(), flush=True)
nulls = [(c, t.column(c).null_count) for c in DIJK_FEATURES if t.column(c).null_count]
print("含空值字段 =", nulls[:20], flush=True)
import numpy as np
m = np.stack([t.column(c).to_numpy(zero_copy_only=False).astype(np.float32) for c in DIJK_FEATURES], axis=1)
print("非有限值个数 =", int((~np.isfinite(m)).sum()), " 形状 =", m.shape, flush=True)
print("PROBE23_DONE", flush=True)
