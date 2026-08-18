# -*- coding: utf-8 -*-
"""E2 切分键偏移核验：在共享筛选视图上核验合同切分键的真实语义。

背景（已通过源码核验，见 tools/lspr24_g0/src/screen/wide.rs）：
- `ActivitySplit::from_active_windows`（wide.rs:1305-1323）在 materialize_
  development_wide 的单趟原始行扫描（wide.rs:197-218）之后、聚合分区写出之前
  （wide.rs:227）计算；该扫描覆盖**全部**原始流（wide.rs:414 对每一条可分配
  受保护端点的流无条件插入 `active_window_starts`，不区分该窗口最终会落在
  train/validation/final 哪一段）。
- `write_partition_rows`（wide.rs:719-817）在聚合阶段对每个窗口调用
  `split.name_for(window_start_ns)`（wide.rs:740），`split_name=="final"` 的
  窗口直接 `continue`（wide.rs:741-747），**不写入** development-wide.parquet。
- 因此物化视图（development-wide.parquet）只包含 train+validation（真实活动
  时间线的前 80%），`final`（后 20%）从未落盘。

已确认的现象（来自 runs/candidates/lspr24-early-warning-cpu-gate-v1/run.log，
见 .Codex/docs/RWKV/2026-08-12-C56三进程并发内存耗尽事故取证.md §6.1）：
    活动窗起始去重数=20716
    推导60%边界=1709758690000000000
    validation_min=1709774230000000000
    train_max=1709774225000000000
    核验=失败
即：直接对**视图内**（development-wide.parquet 自身）重建的去重活动窗口起始
集合取 60% 下标，对不上视图真实的 validation 起点。

待验证假设（非结论）：视图内重建的活动键集合，因为 final 段从未落盘，实际上
只是「真集合（wide.rs 内部单趟扫描得到的完整活动键集合）的前 80%」。若此假设
成立，视图内下标 i 与真集合下标 i 一一对应（i < n_act），故真集合的 60% 分位
点（validation_start_ns 的定义）在视图内重建集合中对应的相对位置应为
0.60 / 0.80 = 0.75，即 `active_starts[n_act * 75 // 100] == validation_min`
应当成立（且应精确成立，因为该关系是纯下标对应关系，不依赖活动时间分布的
均匀性假设）。

本脚本只读：
- 不修改、不重新物化 runs/data-prepared/ 下任何内容。
- 只读取 development-wide.parquet 的 `window_start_ns` 与 `has_activity`
  两列（元数据规模，预计峰值 < 4 GiB，见 tools/memory_admission_gate.sh 前置
  门禁）。
- 结果写入 runs/diagnostics/lspr24-split-key-audit-v1/（只读诊断运行根，不
  与 runs/candidates/ 下任何正式候选共享状态文件或锁）。

screening_only=true, formal_paper_evidence=false, final_accessed=false。
"""
import json
import os
import time

import numpy as np
import pyarrow.parquet as pq

ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-prepared/lspr24-screen-wide-v1"
OUT_DIR = (
    "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/lspr24-split-key-audit-v1"
)
GIB = 1024.0**3

T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {msg}", flush=True)


def _read_cgroup_memory() -> tuple[int, int]:
    """读取 cgroup 内存上限与当前用量（字节），禁止 free/psutil/meminfo。"""
    v2_max = "/sys/fs/cgroup/memory.max"
    v2_cur = "/sys/fs/cgroup/memory.current"
    v1_lim = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
    v1_use = "/sys/fs/cgroup/memory/memory.usage_in_bytes"
    try:
        with open(v2_max) as f:
            raw_limit = f.read().strip()
        with open(v2_cur) as f:
            usage = int(f.read().strip())
        if raw_limit != "max":
            return int(raw_limit), usage
    except (FileNotFoundError, ValueError, OSError):
        pass
    try:
        with open(v1_lim) as f:
            limit = int(f.read().strip())
        with open(v1_use) as f:
            usage = int(f.read().strip())
        return limit, usage
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise RuntimeError(
            "无法读取 cgroup 内存上限，禁止回退 free/psutil 判断容器可用内存"
        ) from exc


def _read_process_rss_bytes() -> int:
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    raise RuntimeError("/proc/self/status 中未找到 VmRSS 行")


def log_memory_state(tag: str) -> None:
    limit, usage = _read_cgroup_memory()
    rss = _read_process_rss_bytes()
    log(
        f"[mem:{tag}] cgroup上限={limit / GIB:.2f}GiB 已用={usage / GIB:.2f}GiB "
        f"可用={(limit - usage) / GIB:.2f}GiB 进程VmRSS={rss / GIB:.2f}GiB"
    )


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    log_memory_state("startup")

    log("读取 development-wide.parquet 的 2 列元数据（只读，不重新物化）")
    meta = pq.read_table(
        f"{ROOT}/development-wide.parquet",
        columns=["window_start_ns", "split_name", "has_activity"],
    )
    ws_raw = meta.column("window_start_ns").to_numpy().astype(np.int64)
    act_raw = meta.column("has_activity").to_numpy(zero_copy_only=False).astype(bool)
    split_names = meta.column("split_name").to_pandas().to_numpy()
    n_rows = len(ws_raw)
    del meta
    log_memory_state("元数据载入完成")

    is_train = split_names == "train"
    is_validation = split_names == "validation"
    assert bool((is_train | is_validation).all()), "视图内出现 train/validation 之外的切分名"
    val_min = int(ws_raw[is_validation].min())
    val_max = int(ws_raw[is_validation].max())
    train_min = int(ws_raw[is_train].min())
    train_max = int(ws_raw[is_train].max())
    log(
        f"行数={n_rows} train=[{train_min},{train_max}] "
        f"validation=[{val_min},{val_max}]"
    )

    active_starts = np.unique(ws_raw[act_raw])
    n_act = int(len(active_starts))
    log(f"去重活动窗起始数={n_act}")

    def idx_at(k_over_100: int) -> int:
        return int(active_starts[n_act * k_over_100 // 100])

    b60 = idx_at(60)
    key_verified_60 = b60 == val_min
    log(f"k=60: active_starts[n_act*60//100]={b60} validation_min={val_min} 核验={'通过' if key_verified_60 else '失败'}")

    b75 = idx_at(75)
    key_verified_75 = b75 == val_min
    log(f"k=75: active_starts[n_act*75//100]={b75} validation_min={val_min} 核验={'通过' if key_verified_75 else '失败'}")

    # k/1000 网格扫描：找出使 active_starts[n_act*k//1000] 最接近
    # validation_min / train_max 的 k，不为让结论好看而调整网格或容差。
    def grid_scan(target: int) -> dict:
        best_k = None
        best_abs_diff = None
        best_value = None
        for k in range(0, 1001):
            index = n_act * k // 1000
            if index >= n_act:
                index = n_act - 1
            value = int(active_starts[index])
            diff = abs(value - target)
            if best_abs_diff is None or diff < best_abs_diff:
                best_abs_diff = diff
                best_k = k
                best_value = value
        return {
            "target": target,
            "best_k_over_1000": best_k,
            "best_value": best_value,
            "abs_diff_ns": best_abs_diff,
            "abs_diff_seconds": best_abs_diff / 1e9 if best_abs_diff is not None else None,
        }

    grid_val_min = grid_scan(val_min)
    grid_train_max = grid_scan(train_max)
    log(f"网格扫描 validation_min: {grid_val_min}")
    log(f"网格扫描 train_max: {grid_train_max}")

    result = {
        "schema_version": "lspr24-e2-split-key-offset-grid-scan-v1",
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "n_rows": n_rows,
        "n_active_starts": n_act,
        "train_min_ns": train_min,
        "train_max_ns": train_max,
        "validation_min_ns": val_min,
        "validation_max_ns": val_max,
        "k60_derived_ns": b60,
        "k60_key_verified": key_verified_60,
        "k75_derived_ns": b75,
        "k75_key_verified": key_verified_75,
        "grid_scan_validation_min": grid_val_min,
        "grid_scan_train_max": grid_train_max,
    }
    out_path = f"{OUT_DIR}/split-key-offset-grid-scan-result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"结果已写入 {out_path}")
    log_memory_state("完成")


if __name__ == "__main__":
    main()
