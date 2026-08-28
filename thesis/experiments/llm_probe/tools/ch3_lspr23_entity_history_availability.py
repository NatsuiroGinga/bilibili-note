# -*- coding: utf-8 -*-
"""第三章 LSPR23 实体历史可用性诊断：为因果实体记忆机制提供动机与作用面证据。

回答三个问题，全部只读 LSPR23 冻结缓存，目标年读取为 0：

1. **历史是否存在**：每个实体在源年训练区内有多少条流、多少个片段？只有一条流的
   实体没有任何严格过去可供读取，机制一对其等价于裸 FT。
2. **作用面有多大**：按流加权后，有历史可读的流占多少？这决定机制一的覆盖率，
   而不是按实体数计的比例（两者相差极大）。
3. **历史是否与攻击相关**：恶意实体与良性实体的流链长度分布是否不同？若恶意实体
   系统性更长，则实体历史的作用面与检测目标高度重合，构成机制动机。

口径说明：

- 实体链长度按「该实体全部片段的有效流数之和」计，不是片段数。
- 实体标签取其任一流为恶意（``Y_e = max_t y_{e,t}``），只用于本诊断的分组统计，
  不参与任何模型输入、状态更新或选择。
- 片段级时间戳 ``T23`` 只用于报告时间跨度；同实体片段顺序性另由接口核验负责。

输出收据可被正文第三章动机小节引用；本工具不训练模型、不读取 LSPR24。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

RUN_ID = "ch3-lspr23-entity-history-availability-v1"
SCHEMA_VERSION = "ch3-entity-history-availability-receipt-v1"
CHUNK = 20000
FLOW_THRESHOLDS = (1, 2, 3, 10, 100)
PERCENTILES = (50, 75, 90, 95, 99)
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:7.1f}s] {message}", flush=True)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写 JSON，避免中断产生半份收据。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def load_source(cache_root: Path) -> dict[str, Any]:
    """只加载源年数组；显式拒绝任何目标年文件名。"""
    for name in ("X24", "y24", "I24", "M24", "E24", "T24"):
        if (cache_root / f"{name}.npy").is_file() and name in os.environ.get("ALLOW_TARGET", ""):
            raise RuntimeError("本诊断禁止读取目标年数组")
    return {
        "I23": np.load(cache_root / "I23.npy", mmap_mode="r"),
        "M23": np.load(cache_root / "M23.npy", mmap_mode="r"),
        "E23": np.load(cache_root / "E23.npy"),
        "T23": np.load(cache_root / "T23.npy"),
        "y23": np.load(cache_root / "y23.npy"),
    }


def segment_valid_lengths(mask: np.ndarray, segment_count: int) -> np.ndarray:
    """逐片段有效流数。"""
    lengths = np.zeros(segment_count, dtype=np.int64)
    for start in range(0, segment_count, CHUNK):
        block = np.asarray(mask[start : start + CHUNK]) > 0
        lengths[start : start + CHUNK] = block.sum(axis=1)
    return lengths


def entity_positive_flags(
    indices: np.ndarray,
    mask: np.ndarray,
    entity_of_segment: np.ndarray,
    flow_labels: np.ndarray,
    entity_count: int,
) -> np.ndarray:
    """实体标签：其任一有效流为恶意即为恶意实体。"""
    flags = np.zeros(entity_count, dtype=bool)
    segment_count = len(entity_of_segment)
    for start in range(0, segment_count, CHUNK):
        index_block = np.asarray(indices[start : start + CHUNK])
        mask_block = np.asarray(mask[start : start + CHUNK]) > 0
        owners = entity_of_segment[start : start + CHUNK]
        flat = index_block[mask_block]
        if flat.size == 0:
            continue
        segment_ids = np.repeat(np.arange(len(owners)), mask_block.sum(axis=1))
        positive_flat = flow_labels[flat] > 0.5
        segment_positive = np.zeros(len(owners), dtype=bool)
        np.logical_or.at(segment_positive, segment_ids, positive_flat)
        np.logical_or.at(flags, owners, segment_positive)
    return flags


def describe_group(
    flows_per_entity: np.ndarray,
    segments_per_entity: np.ndarray,
    total_flows: int,
) -> dict[str, Any]:
    """一组实体的链长度、覆盖率与多片段占比。"""
    if flows_per_entity.size == 0:
        return {"entity_count": 0}
    return {
        "entity_count": int(flows_per_entity.size),
        "flow_count": int(flows_per_entity.sum()),
        "flow_share": float(flows_per_entity.sum() / total_flows),
        "flows_per_entity_percentiles": {
            str(q): int(np.percentile(flows_per_entity, q)) for q in PERCENTILES
        },
        "flows_per_entity_mean": float(flows_per_entity.mean()),
        "flows_per_entity_max": int(flows_per_entity.max()),
        "share_with_history": float((flows_per_entity >= 2).mean()),
        "share_multi_segment": float((segments_per_entity > 1).mean()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default="runs/diagnostics/dijk-repro/cache")
    parser.add_argument("--output-root", default=f"runs/diagnostics/{RUN_ID}")
    args = parser.parse_args()

    cache_root = Path(args.cache_root).resolve()
    output_root = Path(args.output_root).resolve()
    atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "running", "target_reads": 0})

    source = load_source(cache_root)
    entity_of_segment = source["E23"]
    segment_count = len(entity_of_segment)
    log(f"加载完成：{segment_count:,} 片段")

    valid_lengths = segment_valid_lengths(source["M23"], segment_count)
    entity_count = int(entity_of_segment.max()) + 1
    flows_per_entity = np.bincount(entity_of_segment, weights=valid_lengths, minlength=entity_count).astype(np.int64)
    segments_per_entity = np.bincount(entity_of_segment, minlength=entity_count)
    alive = flows_per_entity > 0
    total_flows = int(flows_per_entity.sum())
    log(f"实体链长度完成：{int(alive.sum()):,} 个实体、{total_flows:,} 条有效流")

    positive_entity = entity_positive_flags(
        source["I23"], source["M23"], entity_of_segment, source["y23"], entity_count
    )
    log(f"实体标签完成：{int(positive_entity[alive].sum()):,} 个恶意实体")

    flows_alive = flows_per_entity[alive]
    segments_alive = segments_per_entity[alive]
    positive_alive = positive_entity[alive]

    coverage: dict[str, Any] = {}
    for threshold in FLOW_THRESHOLDS:
        selected = flows_alive >= threshold
        coverage[f"flows_ge_{threshold}"] = {
            "entity_count": int(selected.sum()),
            "entity_share": float(selected.mean()),
            "flow_share": float(flows_alive[selected].sum() / total_flows),
        }
    multi_segment = segments_alive > 1
    coverage["multi_segment"] = {
        "entity_count": int(multi_segment.sum()),
        "entity_share": float(multi_segment.mean()),
        "flow_share": float(flows_alive[multi_segment].sum() / total_flows),
    }

    timestamps = source["T23"]
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "cache_root": str(cache_root),
        "target_reads": 0,
        "evidence_tier": "source_year_data_characterization",
        "overall": {
            "entity_count": int(alive.sum()),
            "flow_count": total_flows,
            "segment_count": segment_count,
            "observation_span_days": float((timestamps.max() - timestamps.min()) / 1e6 / 86400),
            "flows_per_entity_percentiles": {
                str(q): int(np.percentile(flows_alive, q)) for q in PERCENTILES
            },
            "segments_per_entity_percentiles": {
                str(q): int(np.percentile(segments_alive, q)) for q in PERCENTILES
            },
        },
        "history_coverage": coverage,
        "by_entity_label": {
            "malicious": describe_group(flows_alive[positive_alive], segments_alive[positive_alive], total_flows),
            "benign": describe_group(flows_alive[~positive_alive], segments_alive[~positive_alive], total_flows),
        },
        "within_segment": {
            "valid_flows_percentiles": {str(q): int(np.percentile(valid_lengths, q)) for q in PERCENTILES},
            "valid_flows_mean": float(valid_lengths.mean()),
            "single_flow_segment_share": float((valid_lengths == 1).mean()),
            "single_flow_segment_flow_share": float(valid_lengths[valid_lengths == 1].sum() / total_flows),
        },
    }
    atomic_json(output_root / "entity-history-availability.json", receipt)
    atomic_json(
        output_root / "status.json",
        {"run_id": RUN_ID, "state": "finished", "exit_code": 0, "target_reads": 0},
    )
    log(f"收据写出：{output_root / 'entity-history-availability.json'}")
    print("CH3_ENTITY_HISTORY_AVAILABILITY_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
