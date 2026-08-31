#!/usr/bin/env python3
"""目标年「纯流数先验」基线探测：不加载模型、不做前向、不读检查点。

存在理由（2026-08-31）：目标年实测发现两个机制臂的逐流 ROC-AUC 均低于 0.5
（C01 `0.469308`、C10 `0.421902`），而裸 FT 为 `0.737832`；但 C01 的实体 AP
反而最高（`0.741039`）。怀疑实体分数取最大池化时，恶意实体流数更多
（`691.5` 对良性 `425.1`，比值 `1.63`）本身就会抬高最大值期望，
使实体 AP 在逐流判别失效时仍显得很高。

本脚本用随机分数替代模型分数，保持每实体的流数与标签不变，
量化「纯流数先验」在各聚合口径下能产生多高的实体 AP。
若随机基线已接近既有读数，则说明该指标口径缺乏区分力。

只读 `s24`/`d24`/`y24`/`I24`/`M24`，不触碰任何运行制品与检查点。
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


def probe_arrays(cache: Path, entity_index: Path) -> Dict[str, Any]:
    """先只读形状与 dtype，不做任何计算，用于确认口径假设。

    `s24`/`d24` 是 object dtype（字符串 IP），不能内存映射，只报告字节数。
    """
    report: Dict[str, Any] = {}
    targets = [(name, cache / f"{name}.npy") for name in ("s24", "d24", "y24", "I24", "M24", "t24")]
    targets.append(("ent24", entity_index))
    for name, path in targets:
        if not path.is_file():
            report[name] = {"exists": False, "path": str(path)}
            continue
        entry: Dict[str, Any] = {"exists": True, "path": str(path), "bytes": int(path.stat().st_size)}
        try:
            array = np.load(path, mmap_mode="r", allow_pickle=False)
            entry.update({"shape": list(array.shape), "dtype": str(array.dtype)})
        except ValueError as error:
            entry["note"] = f"不可内存映射：{error}"
        report[name] = entry
    return report


def build_entity_index(cache: Path, entity_index: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """取逐流实体下标，优先复用既有缓存，避免重复归并 2000 万条字符串键。

    既有口径（`tools/ch3_auxw_sweep.py:123-128`）：
    `key = a + "|" + b if a <= b else b + "|" + a`，再 `np.unique(..., return_inverse=True)`。
    本脚本优先读该口径已落盘的结果，只在缺失时按同一公式重算。

    返回 (逐流实体下标, 逐实体流数, 逐实体标签)。
    实体标签取该实体全部流标签的最大值，与 `maximum_over_validation_flows` 口径一致
    （既有实现同为 `np.maximum.at(ent_lab, ent24, y24)`）。
    """
    labels = np.load(cache / "y24.npy", allow_pickle=False)
    if entity_index.is_file():
        entity_of_flow = np.load(entity_index, allow_pickle=False).astype(np.int64, copy=False)
        log(f"复用既有实体索引 {entity_index}，长度 {entity_of_flow.size}")
    else:
        log("未找到既有实体索引，按既有公式重算（较慢）")
        src = np.load(cache / "s24.npy", allow_pickle=True)
        dst = np.load(cache / "d24.npy", allow_pickle=True)
        key = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(src, dst)], object)
        del src, dst
        _, entity_of_flow = np.unique(key, return_inverse=True)
        entity_of_flow = np.asarray(entity_of_flow).reshape(-1).astype(np.int64)
        del key

    if entity_of_flow.size != labels.size:
        raise RuntimeError(
            f"实体索引与标签长度不一致：{entity_of_flow.size} != {labels.size}，口径可能不同源"
        )
    log(f"y24 {labels.shape} {labels.dtype}")

    entity_count = int(entity_of_flow.max()) + 1
    flows_per_entity = np.bincount(entity_of_flow, minlength=entity_count)
    entity_score_label = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_score_label, entity_of_flow, labels.astype(np.float32, copy=False))
    entity_label = (entity_score_label > 0.5).astype(np.int64)
    return entity_of_flow, flows_per_entity, entity_label


def aggregate(scores: np.ndarray, entity_of_flow: np.ndarray, entity_count: int, mode: str) -> np.ndarray:
    """按指定口径把逐流分数聚合为实体分数。"""
    if mode == "max":
        out = np.full(entity_count, -np.inf, dtype=np.float64)
        np.maximum.at(out, entity_of_flow, scores)
        return out
    if mode == "mean":
        total = np.bincount(entity_of_flow, weights=scores, minlength=entity_count)
        count = np.bincount(entity_of_flow, minlength=entity_count).astype(np.float64)
        return total / np.maximum(count, 1.0)
    if mode.startswith("lp"):
        power = float(mode[2:])
        total = np.bincount(entity_of_flow, weights=np.power(scores, power), minlength=entity_count)
        count = np.bincount(entity_of_flow, minlength=entity_count).astype(np.float64)
        return np.power(total / np.maximum(count, 1.0), 1.0 / power)
    raise ValueError(f"未知聚合口径：{mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--entity-index", required=True, help="既有逐流实体下标 npy，缺失时按既有公式重算")
    parser.add_argument("--output", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 22, 33])
    parser.add_argument("--probe-only", action="store_true", help="只报告数组形状与 dtype，不做计算")
    args = parser.parse_args()

    cache = Path(args.cache_root)
    entity_index = Path(args.entity_index)
    shapes = probe_arrays(cache, entity_index)
    log(json.dumps(shapes, ensure_ascii=False, indent=2))
    if args.probe_only:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps({"stage": "probe", "arrays": shapes}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return 0

    entity_of_flow, flows_per_entity, entity_label = build_entity_index(cache, entity_index)
    entity_count = int(entity_label.size)
    positive_entities = int(entity_label.sum())
    log(f"实体数={entity_count} 正实体={positive_entities} 流数={entity_of_flow.size}")

    positive_mask = entity_label > 0
    flows_positive = float(flows_per_entity[positive_mask].mean())
    flows_negative = float(flows_per_entity[~positive_mask].mean())

    from sklearn.metrics import average_precision_score, roc_auc_score

    modes = ("max", "mean", "lp2", "lp4", "lp8")
    results: Dict[str, Any] = {}
    for seed in args.seeds:
        rng = np.random.default_rng(seed)
        scores = rng.random(entity_of_flow.size)
        per_mode = {}
        for mode in modes:
            entity_score = aggregate(scores, entity_of_flow, entity_count, mode)
            per_mode[mode] = {
                "entity_average_precision": float(average_precision_score(entity_label, entity_score)),
                "entity_roc_auc": float(roc_auc_score(entity_label, entity_score)),
            }
            log(f"seed={seed} {mode}: AP={per_mode[mode]['entity_average_precision']:.6f}")
        results[str(seed)] = per_mode

    payload = {
        "schema_version": "ch3-ft-target-entity-prior-probe-v1",
        "purpose": "量化纯流数先验在各实体聚合口径下的实体 AP，判断该口径是否具备区分力",
        "arrays": shapes,
        "entity_count": entity_count,
        "positive_entity_count": positive_entities,
        "flow_count": int(entity_of_flow.size),
        "entity_positive_rate": positive_entities / entity_count,
        "mean_flows_per_positive_entity": flows_positive,
        "mean_flows_per_negative_entity": flows_negative,
        "flow_count_ratio_positive_over_negative": flows_positive / flows_negative,
        "random_score_baseline": results,
        "note": "随机分数只用于构造流数先验基线，不是方法的多种子评估；模型未加载，无前向、无参数更新",
        "training_runs": 0,
        "parameter_updates": 0,
        "checkpoints_loaded": 0,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"已写入 {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
