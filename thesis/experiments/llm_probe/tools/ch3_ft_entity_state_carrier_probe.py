#!/usr/bin/env python3
"""M-E 状态载体候选诊断：只用 LSPR23，判断哪些严格过去可观测量值得进入 s_e。

存在理由（2026-08-31）：CEM 的失败诊断确立，跨流状态若取「模型自身表示的摘要」
会随输入分布漂移而失效（目标年逐流 ROC-AUC `0.421902`，低于随机）。
第二机制 M-E 改用原始可观测量作状态载体，但「用哪些量」此前没有数据支撑。

本脚本对每个候选量计算：与实体标签的区分力（AUC）、跨时间前后半段的分布稳定性。
两者都要看——区分力决定它有没有信息，稳定性决定它跨年后是否还成立。

严格过去约束：每条流的状态只由该实体在它之前的流计算，绝不使用当前流或未来流。
只读 LSPR23，`target_reads = 0`。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def strict_past_state(entity_of_flow: np.ndarray, stamp: np.ndarray) -> Dict[str, np.ndarray]:
    """按 (实体, 时间) 升序向量化推进，为每条流生成其到达前的实体状态。

    全向量化，无 Python 逐行循环——语料是千万级流，逐行循环属实现缺陷。

    返回的每个数组与流一一对应，第 i 项只依赖该实体在流 i 之前的流：
    - `prior_flow_count`：该流到达前，同实体已出现的流数（首条为 0）
    - `gap_since_last_event`：距同实体上一条流的时间间隔（首条为 -1，表示无历史）

    指数衰减统计量暂不计算：它是组内递推，且 `exp(rate * t)` 在秒级时间戳上会溢出，
    需要分组重标定才能向量化；本轮先用计数与间隔两个量判断状态载体是否有信息。
    """
    order = np.lexsort((stamp, entity_of_flow))
    entity_sorted = entity_of_flow[order]
    stamp_sorted = stamp[order]
    n = entity_sorted.size

    # 组边界：同一实体的流在排序后连续
    is_group_start = np.empty(n, dtype=bool)
    is_group_start[0] = True
    np.not_equal(entity_sorted[1:], entity_sorted[:-1], out=is_group_start[1:])

    group_id = np.cumsum(is_group_start) - 1
    group_start_index = np.flatnonzero(is_group_start)
    position_in_group = np.arange(n, dtype=np.int64) - group_start_index[group_id]

    prior_count = position_in_group.astype(np.float64)

    gap = np.empty(n, dtype=np.float64)
    gap[0] = -1.0
    np.subtract(stamp_sorted[1:], stamp_sorted[:-1], out=gap[1:])
    gap[is_group_start] = -1.0

    inverse = np.empty(n, dtype=np.int64)
    inverse[order] = np.arange(n, dtype=np.int64)
    return {
        "prior_flow_count": prior_count[inverse],
        "gap_since_last_event": gap[inverse],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--decay-halflife", type=float, default=3600.0,
                        help="指数衰减半衰期，单位与 T23 一致；仅用于诊断，非冻结值")
    parser.add_argument("--limit", type=int, default=0, help="只取前 N 条流，0 表示全量")
    args = parser.parse_args()

    cache = Path(args.cache_root)
    entity = np.load(cache / "E23.npy", allow_pickle=False)
    stamp = np.load(cache / "T23.npy", allow_pickle=False)
    flow_labels = np.load(cache / "y23.npy", allow_pickle=False)
    log(f"E23 {entity.shape} {entity.dtype} / T23 {stamp.shape} {stamp.dtype} / y23 {flow_labels.shape}")

    # E23/T23 是逐序列，y23 是逐流，二者不可直接对齐。
    # 必须经 I23（序列→流索引）与 M23（有效位掩码）把标签聚合到序列级：
    # 序列为正当且仅当其有效流中存在正流，与实体级评价的标签口径一致。
    require = entity.size == stamp.size
    if not require:
        raise RuntimeError(f"E23 与 T23 长度不一致：{entity.size} != {stamp.size}")
    indices = np.load(cache / "I23.npy", allow_pickle=False)
    masks = np.load(cache / "M23.npy", allow_pickle=False)
    if indices.shape[0] != entity.size:
        raise RuntimeError(f"I23 序列数 {indices.shape[0]} 与 E23 {entity.size} 不一致，口径不同源")
    log(f"I23 {indices.shape} {indices.dtype} / M23 {masks.shape} {masks.dtype}")

    valid = np.asarray(masks) > 0
    valid_per_sequence = valid.sum(axis=1)
    flat_flow_index = np.asarray(indices)[valid]
    flat_flow_label = flow_labels[flat_flow_index].astype(np.float32, copy=False)
    sequence_of_flat = np.repeat(np.arange(entity.size, dtype=np.int64), valid_per_sequence)
    sequence_label = np.zeros(entity.size, dtype=np.float32)
    np.maximum.at(sequence_label, sequence_of_flat, flat_flow_label)
    log(f"序列级标签聚合完成：有效流 {int(valid_per_sequence.sum())}，正序列 {int((sequence_label > 0.5).sum())}")

    if args.limit:
        entity = entity[: args.limit]
        stamp = stamp[: args.limit]
        sequence_label = sequence_label[: args.limit]

    states = strict_past_state(entity, stamp)

    from sklearn.metrics import roc_auc_score

    binary = (sequence_label > 0.5).astype(np.int64)
    report: Dict[str, Any] = {
        "schema_version": "ch3-ft-entity-state-carrier-probe-v1",
        "target_reads": 0,
        "decay_halflife": args.decay_halflife,
        "sample_count": int(entity.size),
        "positive_rate": float(binary.mean()),
        "candidates": {},
    }

    half = entity.size // 2
    for name, values in states.items():
        finite = np.isfinite(values)
        usable = finite & (values >= 0) if name == "gap_since_last_event" else finite
        auc = float(roc_auc_score(binary[usable], values[usable])) if usable.sum() > 1 else None
        first_half = values[:half][np.isfinite(values[:half])]
        second_half = values[half:][np.isfinite(values[half:])]
        report["candidates"][name] = {
            "discrimination_auc": auc,
            "usable_fraction": float(usable.mean()),
            "mean_first_half": float(first_half.mean()) if first_half.size else None,
            "mean_second_half": float(second_half.mean()) if second_half.size else None,
            "median": float(np.median(values[usable])) if usable.sum() else None,
            "p99": float(np.percentile(values[usable], 99)) if usable.sum() else None,
        }
        log(f"{name}: AUC={auc} 可用比例={usable.mean():.4f}")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"已写入 {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
