"""只读探查：LSPR24 row group 结构与 External_* 取值基数。

严格遵守最终封存区隔离：先读时间列建立掩码，封存区行在读取标签/特征前丢弃，
不对封存区做任何计数、统计或哈希。
"""
import pyarrow.parquet as pq
import pyarrow.compute as pc

P = "/root/autodl-tmp/thesis/experiments/llm_probe/data/raw/lspr24-v1/lspr24_v2.parquet"
FINAL_CUT_NS = 1709802623000000000

pf = pq.ParquetFile(P)
md = pf.metadata
print("num_rows", md.num_rows, "row_groups", md.num_row_groups)
sizes = [md.row_group(i).num_rows for i in range(md.num_row_groups)]
print("rg rows min/max/mean", min(sizes), max(sizes), sum(sizes) / len(sizes))
print("total_bytes", md.serialized_size)

open_rows = 0
pos_rows = 0
ext_src = set()
ext_dst = set()
l34 = set()
intext = set()
invalid_time = 0

for i in range(md.num_row_groups):
    t = pf.read_row_group(i, columns=["mTimestampStart", "mTimestampLast"])
    s = t.column("mTimestampStart")
    e = t.column("mTimestampLast")
    valid = pc.and_(pc.and_(pc.is_valid(s), pc.is_valid(e)),
                    pc.less_equal(s, e))
    invalid_time += len(t) - pc.sum(pc.cast(valid, "int64")).as_py()
    avail_ns = pc.multiply(pc.cast(e, "int64"), 1000)
    keep = pc.and_(valid, pc.less(avail_ns, FINAL_CUT_NS))
    n_keep = pc.sum(pc.cast(keep, "int64")).as_py()
    if n_keep == 0:
        continue
    d = pf.read_row_group(i, columns=["Label", "External_src", "External_dst",
                                      "L3/L4 Protocol", "Int/Ext Dst IP"])
    d = d.filter(keep)
    open_rows += len(d)
    pos_rows += pc.sum(pc.cast(d.column("Label"), "int64")).as_py()
    ext_src.update(x for x in pc.unique(d.column("External_src")).to_pylist())
    ext_dst.update(x for x in pc.unique(d.column("External_dst")).to_pylist())
    l34.update(pc.unique(d.column("L3/L4 Protocol")).to_pylist())
    intext.update(pc.unique(d.column("Int/Ext Dst IP")).to_pylist())

print("invalid_time_rows(全表时间字段无效计数，不含标签/特征访问) =", invalid_time)
print("open_pool_rows =", open_rows)
print("open_pool_positive =", pos_rows)
print("open_pool_pi =", pos_rows / open_rows if open_rows else None)
print("External_src distinct:", len(ext_src), sorted(map(str, ext_src))[:30])
print("External_dst distinct:", len(ext_dst), sorted(map(str, ext_dst))[:30])
print("L3/L4 Protocol distinct:", len(l34), sorted(map(str, l34))[:30])
print("Int/Ext Dst IP distinct:", len(intext), sorted(map(str, intext))[:30])
