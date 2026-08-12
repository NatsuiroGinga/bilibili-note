"""LSPR24 流级诊断基线：只用开发区（前 80%），只用合同允许的合法字段。

这不是合同定义的公平基线，结果不得写入论文。唯一目的是回答：
去掉身份、端口、绝对时间、IDS 输出之后，剩余合法字段是否还有可分性。

安全边界：
- 切点只由 mTimestampLast 的活动秒秩计算，不读标签；
- 只保留 last_ns < cut80 的行，最终 20% 不读特征、不读标签、不统计；
- 禁入列显式黑名单，命中即断言失败。
"""

from __future__ import annotations

import logging
import sys
import time
from typing import List, Tuple

import numpy as np
import pyarrow.parquet as pq
import pyarrow.compute as pc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

PARQUET = "/Users/bilibili/personal/note/thesis/experiments/llm_probe/data/raw/lspr24-v1/lspr24_v2.parquet"

# 合同 §6.2 禁入集合：身份、端口、绝对时间、标签、IDS 输出、派生捷径
FORBIDDEN = {
    "Flow ID", "SrcIP", "DstIP", "SrcPort", "DstPort",
    "mTimestampStart", "mTimestampLast",
    "Label", "Label_src", "Label_dst",
    "SigID revision", "Category", "Severity", "Anomaly_event",
    "External_src", "External_dst", "Segment_src", "Segment_dst",
    "Expoid_src", "Expoid_dst", "Int/Ext Dst IP", "Service",
    "L3/L4 Protocol",
}

TARGET_ROWS = 1_500_000  # 抽样规模，控制内存与耗时


def legal_feature_columns(schema) -> List[str]:
    """返回合法数值特征列；命中禁入集合即排除。"""
    cols = []
    for field in schema:
        if field.name in FORBIDDEN:
            continue
        if not (pa_is_numeric(field.type)):
            continue
        cols.append(field.name)
    return cols


def pa_is_numeric(t) -> bool:
    s = str(t)
    return s.startswith(("int", "uint", "float", "double"))


def compute_cut80(path: str) -> int:
    """只读 mTimestampLast，按活动秒秩计算 80% 切点（微秒单位）。"""
    t0 = time.time()
    tbl = pq.read_table(path, columns=["mTimestampLast"])
    last_us = tbl.column("mTimestampLast").to_numpy()
    seconds = np.unique(last_us // 1_000_000)
    n = seconds.size
    b80 = -(-80 * n // 100)  # ceil(0.8 * n)
    cut_s = int(seconds[b80])
    logger.info("活动秒总数 N=%d，b80=%d，cut_s=%d，耗时 %.1fs", n, b80, cut_s, time.time() - t0)
    return cut_s * 1_000_000


def load_dev_sample(path: str, cut_us: int, feature_cols: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """按行组流式读取，只保留开发区行并按固定步长抽样。"""
    pf = pq.ParquetFile(path)
    need = feature_cols + ["mTimestampLast", "Label"]
    xs, ys = [], []
    kept = 0
    for rg in range(pf.metadata.num_row_groups):
        batch = pf.read_row_group(rg, columns=need)
        mask = pc.less(batch.column("mTimestampLast"), cut_us)
        batch = batch.filter(mask)
        if batch.num_rows == 0:
            continue
        step = max(1, (pf.metadata.num_rows * 8 // 10) // TARGET_ROWS)
        idx = np.arange(0, batch.num_rows, step)
        sub = batch.take(idx)
        y = sub.column("Label").to_numpy(zero_copy_only=False)
        keep = ~np.isnan(y.astype(float)) if y.dtype.kind == "f" else np.ones(len(y), bool)
        x = np.column_stack([
            sub.column(c).to_numpy(zero_copy_only=False).astype(np.float32)
            for c in feature_cols
        ])
        xs.append(x[keep])
        ys.append(y[keep].astype(np.int8))
        kept += int(keep.sum())
        logger.info("行组 %d/%d 累计样本 %d", rg + 1, pf.metadata.num_row_groups, kept)
    return np.vstack(xs), np.concatenate(ys)


def main() -> None:
    pf = pq.ParquetFile(PARQUET)
    feature_cols = legal_feature_columns(pf.schema_arrow)
    logger.info("合法特征列 %d 个", len(feature_cols))
    leaked = set(feature_cols) & FORBIDDEN
    assert not leaked, f"禁入列泄漏：{leaked}"

    cut_us = compute_cut80(PARQUET)
    x, y = load_dev_sample(PARQUET, cut_us, feature_cols)
    logger.info("开发区样本 %d 行 × %d 列，正类率 %.4f", x.shape[0], x.shape[1], y.mean())

    np.save("/tmp/qb_x.npy", x)
    np.save("/tmp/qb_y.npy", y)
    with open("/tmp/qb_cols.txt", "w") as f:
        f.write("\n".join(feature_cols))
    logger.info("已保存到 /tmp/qb_*.npy")


if __name__ == "__main__":
    main()
