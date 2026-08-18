"""Dijk 2026 复现的数据读取层。

只负责把 LSPR23 CSV 与 LSPR24 Parquet 读成 83 维 float32 特征矩阵，
并强制执行 LSPR24 最终封存区隔离（封存行在读取标签与特征前丢弃）。
"""

from __future__ import annotations

import logging
import subprocess
import time
from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from dijk_fields import (
    DIJK_FEATURES,
    LABEL_COLUMN,
    TARGET_FINAL_CUT_NS,
    TIME_LAST_COLUMN,
    TIME_START_COLUMN,
)

logger = logging.getLogger(__name__)

_CSV_BLOCK_BYTES = 1 << 25          # 32 MiB 解析块
# 初始容量按 LSPR23 上界一次性申请，避免 np.resize 复制导致峰值翻倍。
# np.empty 不触碰页面，实际 RSS 只随写入增长。
# 上界依据：表 8 LSPR23 OP Train seq.=102,209 → 102209*128/0.8 ≈ 1.64e7 行，取 2.0e7 留余量。
_INITIAL_CAPACITY = 20_000_000
_HEARTBEAT_SECONDS = 30.0


class SealViolationError(RuntimeError):
    """访问到 LSPR24 最终封存区时抛出。"""


@dataclass
class Lspr23Bundle:
    """LSPR23 全量读取结果。"""

    features: np.ndarray            # (n, 83) float32
    labels: np.ndarray              # (n,) int8
    time_start_us: np.ndarray       # (n,) int64
    rows_total: int
    rows_invalid_time: int
    rows_invalid_label: int


def _rss_gib() -> float:
    """读取当前进程 VmRSS（GiB）。禁止使用 free / psutil / meminfo。"""
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1048576.0
    except OSError:
        pass
    return float("nan")


def cgroup_used_gib() -> float:
    """读取容器 cgroup 当前内存用量（GiB）。"""
    for path in ("/sys/fs/cgroup/memory.current",
                 "/sys/fs/cgroup/memory/memory.usage_in_bytes"):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return int(handle.read().strip()) / 1073741824.0
        except (OSError, ValueError):
            continue
    return float("nan")


def cgroup_limit_gib() -> float:
    """读取容器 cgroup 内存上限（GiB）。"""
    for path in ("/sys/fs/cgroup/memory.max",
                 "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw = handle.read().strip()
            if raw == "max":
                return float("inf")
            return int(raw) / 1073741824.0
        except (OSError, ValueError):
            continue
    return float("nan")


def log_memory(stage: str) -> None:
    """打印进程 RSS 与 cgroup 用量。"""
    logger.info(
        "[内存] %s VmRSS=%.2f GiB cgroup_used=%.2f GiB cgroup_limit=%.2f GiB",
        stage, _rss_gib(), cgroup_used_gib(), cgroup_limit_gib(),
    )


def _to_float32_matrix(table: pa.Table) -> np.ndarray:
    """按 DIJK_FEATURES 顺序把 Arrow 表转成 (n, 83) float32 矩阵。空值转 NaN。"""
    n_rows = table.num_rows
    matrix = np.empty((n_rows, len(DIJK_FEATURES)), dtype=np.float32)
    for index, name in enumerate(DIJK_FEATURES):
        column = table.column(name)
        if not pa.types.is_floating(column.type):
            column = pc.cast(column, pa.float64(), safe=False)
        values = column.to_numpy(zero_copy_only=False)
        matrix[:, index] = values.astype(np.float32, copy=False)
    # ±inf 统一按缺失处理；论文未报告缺失策略，XGBoost 原生把 NaN 当 missing。
    np.nan_to_num(matrix, copy=False, nan=np.nan, posinf=np.nan, neginf=np.nan)
    return matrix


def read_lspr23(zip_path: str, member: str) -> Lspr23Bundle:
    """流式解压并读取 LSPR23 全量 CSV，返回 83 维特征矩阵与标签。

    有效性规则与冻结物化器一致：mTimestampStart / mTimestampLast 非空且 start <= last。
    """
    wanted = list(DIJK_FEATURES) + [TIME_START_COLUMN, TIME_LAST_COLUMN, LABEL_COLUMN]
    column_types = {name: pa.float64() for name in DIJK_FEATURES}
    column_types[TIME_START_COLUMN] = pa.int64()
    column_types[TIME_LAST_COLUMN] = pa.int64()
    column_types[LABEL_COLUMN] = pa.int32()

    process = subprocess.Popen(
        ["unzip", "-p", zip_path, member],
        stdout=subprocess.PIPE,
        bufsize=1 << 22,
    )
    if process.stdout is None:
        raise RuntimeError("无法取得 unzip 标准输出")

    capacity = _INITIAL_CAPACITY
    features = np.empty((capacity, len(DIJK_FEATURES)), dtype=np.float32)
    labels = np.empty(capacity, dtype=np.int8)
    starts = np.empty(capacity, dtype=np.int64)
    filled = 0
    rows_total = 0
    rows_invalid_time = 0
    rows_invalid_label = 0
    last_beat = time.monotonic()
    started = last_beat

    reader = pacsv.open_csv(
        process.stdout,
        read_options=pacsv.ReadOptions(block_size=_CSV_BLOCK_BYTES, use_threads=True),
        convert_options=pacsv.ConvertOptions(include_columns=wanted, column_types=column_types),
    )
    try:
        for batch in reader:
            table = pa.Table.from_batches([batch])
            rows_total += table.num_rows

            start_col = table.column(TIME_START_COLUMN)
            last_col = table.column(TIME_LAST_COLUMN)
            label_col = table.column(LABEL_COLUMN)
            time_ok = pc.and_(
                pc.and_(pc.is_valid(start_col), pc.is_valid(last_col)),
                pc.less_equal(start_col, last_col),
            )
            label_ok = pc.and_(
                pc.is_valid(label_col),
                pc.is_in(label_col, value_set=pa.array([0, 1], pa.int32())),
            )
            n_time_bad = table.num_rows - int(pc.sum(pc.cast(time_ok, pa.int64())).as_py() or 0)
            keep = pc.and_(time_ok, label_ok)
            n_keep = int(pc.sum(pc.cast(keep, pa.int64())).as_py() or 0)
            rows_invalid_time += n_time_bad
            rows_invalid_label += table.num_rows - n_keep - n_time_bad

            if n_keep == 0:
                continue
            table = table.filter(keep)

            while filled + table.num_rows > capacity:
                capacity = max(capacity * 2, filled + table.num_rows)
                features = np.resize(features, (capacity, len(DIJK_FEATURES)))
                labels = np.resize(labels, capacity)
                starts = np.resize(starts, capacity)
                logger.info("[LSPR23] 扩容至 %d 行（%.2f GiB）",
                            capacity, capacity * len(DIJK_FEATURES) * 4 / 1073741824.0)

            block = _to_float32_matrix(table)
            features[filled:filled + block.shape[0]] = block
            labels[filled:filled + block.shape[0]] = (
                table.column(LABEL_COLUMN).to_numpy(zero_copy_only=False).astype(np.int8)
            )
            starts[filled:filled + block.shape[0]] = (
                table.column(TIME_START_COLUMN).to_numpy(zero_copy_only=False).astype(np.int64)
            )
            filled += block.shape[0]

            now = time.monotonic()
            if now - last_beat >= _HEARTBEAT_SECONDS:
                elapsed = now - started
                logger.info(
                    "[LSPR23] 心跳 已读 %d 行 保留 %d 行 用时 %.0f s 吞吐 %.0f 行/s RSS=%.2f GiB",
                    rows_total, filled, elapsed, rows_total / max(elapsed, 1e-9), _rss_gib(),
                )
                last_beat = now
    finally:
        reader.close()
        process.stdout.close()
        process.wait()

    logger.info("[LSPR23] 读取完成：总行 %d 保留 %d 时间无效 %d 标签无效 %d 用时 %.0f s",
                rows_total, filled, rows_invalid_time, rows_invalid_label,
                time.monotonic() - started)
    return Lspr23Bundle(
        features=features[:filled],
        labels=labels[:filled],
        time_start_us=starts[:filled],
        rows_total=rows_total,
        rows_invalid_time=rows_invalid_time,
        rows_invalid_label=rows_invalid_label,
    )


def _open_pool_mask(table: pa.Table) -> pa.Array:
    """按时间列构造开放池掩码：时间有效且 available_ns < 最终封存边界。"""
    start_col = table.column(TIME_START_COLUMN)
    last_col = table.column(TIME_LAST_COLUMN)
    time_ok = pc.and_(
        pc.and_(pc.is_valid(start_col), pc.is_valid(last_col)),
        pc.less_equal(start_col, last_col),
    )
    available_ns = pc.multiply(pc.cast(last_col, pa.int64()), pa.scalar(1000, pa.int64()))
    mask = pc.and_(time_ok, pc.less(available_ns, pa.scalar(TARGET_FINAL_CUT_NS, pa.int64())))
    # 空值一律按不保留处理：无法证明该行在封存边界之外时保守丢弃。
    return pc.fill_null(mask, False)


def iter_lspr24_open_pool(
    parquet_path: str,
    payload_columns: list[str],
) -> Iterator[tuple[np.ndarray, pa.Table]]:
    """按 row group 迭代 LSPR24 开放池。

    先只读时间列建立掩码，封存区行在读取 `payload_columns` 之后立即丢弃，
    绝不参与任何计数、统计或哈希。返回 (全局行号数组, 已过滤的载荷表)。
    """
    if TIME_LAST_COLUMN in payload_columns or TIME_START_COLUMN in payload_columns:
        raise ValueError("payload_columns 不应重复包含时间列")

    parquet_file = pq.ParquetFile(parquet_path)
    metadata = parquet_file.metadata
    offset = 0
    started = time.monotonic()
    last_beat = started
    emitted = 0

    for group_index in range(metadata.num_row_groups):
        group_rows = metadata.row_group(group_index).num_rows
        time_table = parquet_file.read_row_group(
            group_index, columns=[TIME_START_COLUMN, TIME_LAST_COLUMN]
        )
        keep = _open_pool_mask(time_table)
        n_keep = int(pc.sum(pc.cast(keep, pa.int64())).as_py() or 0)
        if n_keep == 0:
            offset += group_rows
            continue

        keep_numpy = keep.to_numpy(zero_copy_only=False).astype(bool)
        del time_table
        payload = parquet_file.read_row_group(group_index, columns=payload_columns)
        payload = payload.filter(keep)
        if payload.num_rows != n_keep:
            raise SealViolationError(
                f"row group {group_index} 过滤后行数 {payload.num_rows} != 掩码 {n_keep}"
            )
        row_index = offset + np.flatnonzero(keep_numpy).astype(np.int64)
        offset += group_rows
        emitted += n_keep

        now = time.monotonic()
        if now - last_beat >= _HEARTBEAT_SECONDS:
            logger.info(
                "[LSPR24] 心跳 row_group %d/%d 已产出 %d 行 用时 %.0f s RSS=%.2f GiB",
                group_index + 1, metadata.num_row_groups, emitted, now - started, _rss_gib(),
            )
            last_beat = now

        yield row_index, payload

    logger.info("[LSPR24] 迭代完成：开放池 %d 行 用时 %.0f s", emitted, time.monotonic() - started)


def payload_to_matrix(payload: pa.Table) -> np.ndarray:
    """把 LSPR24 载荷表转成 (n, 83) float32 矩阵。"""
    return _to_float32_matrix(payload)
