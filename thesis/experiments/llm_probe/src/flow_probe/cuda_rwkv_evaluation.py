"""CUDA-RWKV Raw83 源年与目标年聚合评价。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from sklearn.metrics import average_precision_score

from flow_probe.protocol_a_raw83 import sha256_file


DISPLAY_FPR_ANCHORS = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _verified_artifact_path(dataset: Any, key: str) -> Path:
    manifest = dataset.manifest
    item = manifest.get("artifacts", {}).get(key)
    if not isinstance(item, dict):
        raise RuntimeError(f"Raw83 数据清单缺少评价制品：{key}")
    root = Path(dataset.manifest_path).resolve(strict=True).parent
    path = Path(item["path"])
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_relative_to(root):
        raise RuntimeError(f"Raw83 评价制品路径越界或为符号链接：{key}")
    if resolved.stat().st_size != int(item["bytes"]):
        raise RuntimeError(f"Raw83 评价制品字节数不符：{key}")
    if sha256_file(resolved) != item["sha256"]:
        raise RuntimeError(f"Raw83 评价制品 SHA-256 不符：{key}")
    return resolved


def sequence_rows_for_purpose(dataset: Any, purpose: str) -> np.ndarray:
    if purpose == "validate":
        return np.asarray(
            np.load(
                _verified_artifact_path(dataset, "validation_rows"),
                mmap_mode="r",
                allow_pickle=False,
            ),
            dtype=np.int64,
        )
    if purpose == "target-evaluate":
        sequence_count = np.load(
            _verified_artifact_path(dataset, "I24"),
            mmap_mode="r",
            allow_pickle=False,
        ).shape[0]
        return np.arange(sequence_count, dtype=np.int64)
    raise ValueError(f"评价不支持 purpose={purpose}")


def _sequence_sidecars(dataset: Any, purpose: str) -> tuple[np.ndarray, np.ndarray]:
    if purpose == "validate":
        entity_key, time_key = "E23", "T23"
    elif purpose == "target-evaluate":
        entity_key, time_key = "sequence_entity_id", "sequence_start_time_ns"
    else:
        raise ValueError(f"评价不支持 purpose={purpose}")
    entities = np.load(
        _verified_artifact_path(dataset, entity_key),
        mmap_mode="r",
        allow_pickle=False,
    )
    times = np.load(
        _verified_artifact_path(dataset, time_key),
        mmap_mode="r",
        allow_pickle=False,
    )
    if entities.shape != times.shape or entities.ndim != 1:
        raise RuntimeError("Raw83 序列实体与开始时刻侧车形状不符")
    return entities, times


def _timely_detection_ladder(
    positive_paths: Mapping[int, np.ndarray], threshold: float
) -> dict[str, Any]:
    exposures: list[int] = []
    for path in positive_paths.values():
        reached = np.flatnonzero(path >= threshold)
        if reached.size:
            exposures.append(int(reached[0]) + 1)
    total = len(positive_paths)
    alerted = len(exposures)
    points: list[dict[str, Any]] = []
    if exposures:
        unique_exposures, counts = np.unique(
            np.asarray(exposures, dtype=np.int64), return_counts=True
        )
        cumulative = 0
        for exposure_index, count in zip(unique_exposures, counts, strict=True):
            cumulative += int(count)
            points.append(
                {
                    "exposure_index": int(exposure_index),
                    "cumulative_detected_entities": cumulative,
                    "timely_detection_rate": None if total == 0 else cumulative / total,
                    "unalerted_fraction": None if total == 0 else (total - cumulative) / total,
                }
            )
    unsigned = {
        "schema_version": "first-alert-right-continuous-ladder-v1",
        "threshold": threshold,
        "exposure_index_base": 1,
        "right_continuous": True,
        "positive_entity_denominator": total,
        "positive_entity_denominator_fixed": True,
        "positive_entities": total,
        "alerted_positive_entities": alerted,
        "unalerted_positive_entities": total - alerted,
        "final_unalerted_fraction": None if total == 0 else (total - alerted) / total,
        "points": points,
    }
    return {**unsigned, "ladder_sha256": canonical_sha256(unsigned)}


def _complete_group_states(
    scores: np.ndarray, labels: np.ndarray
) -> tuple[list[dict[str, Any]], int, int]:
    if scores.ndim != 1 or labels.shape != scores.shape:
        raise ValueError("实体分数与标签必须是同形一维数组")
    if scores.size == 0 or not np.isfinite(scores).all():
        raise ValueError("实体分数为空或包含非有限值")
    if not np.isin(labels, (0, 1)).all():
        raise ValueError("实体标签必须为二元")
    order = np.argsort(-scores, kind="stable")
    ordered_scores = scores[order]
    ordered_labels = labels[order].astype(np.int64, copy=False)
    positives = int(ordered_labels.sum())
    negatives = int(ordered_labels.size - positives)
    sentinel = float(np.nextafter(float(ordered_scores[0]), np.inf))
    states: list[dict[str, Any]] = [
        {
            "threshold": sentinel,
            "tp": 0,
            "fp": 0,
            "tie_group_size": 0,
            "tie_group_positive": 0,
            "tie_group_negative": 0,
        }
    ]
    tp = 0
    fp = 0
    start = 0
    while start < ordered_scores.size:
        stop = start + 1
        while stop < ordered_scores.size and ordered_scores[stop] == ordered_scores[start]:
            stop += 1
        group_labels = ordered_labels[start:stop]
        group_positive = int(group_labels.sum())
        group_negative = int(group_labels.size - group_positive)
        tp += group_positive
        fp += group_negative
        states.append(
            {
                "threshold": float(ordered_scores[start]),
                "tp": tp,
                "fp": fp,
                "tie_group_size": int(stop - start),
                "tie_group_positive": group_positive,
                "tie_group_negative": group_negative,
            }
        )
        start = stop
    return states, positives, negatives


def complete_integer_fp_curve(
    scores: np.ndarray,
    labels: np.ndarray,
    *,
    positive_paths: Mapping[int, np.ndarray] | None = None,
) -> dict[str, Any]:
    states, positives, negatives = _complete_group_states(scores, labels)
    best_at_fp: dict[int, dict[str, Any]] = {}
    for state in states:
        best_at_fp[int(state["fp"])] = state
    reachable = sorted(best_at_fp)
    next_reachable = {
        fp: (reachable[index + 1] if index + 1 < len(reachable) else None)
        for index, fp in enumerate(reachable)
    }
    curve: list[dict[str, Any]] = []
    reachable_index = 0
    selected_fp = reachable[0]
    for budget in range(negatives + 1):
        while (
            reachable_index + 1 < len(reachable)
            and reachable[reachable_index + 1] <= budget
        ):
            reachable_index += 1
            selected_fp = reachable[reachable_index]
        state = best_at_fp[selected_fp]
        detection_rate = None if positives == 0 else state["tp"] / positives
        point = {
            "budget_fp": budget,
            "threshold": state["threshold"],
            "tp": state["tp"],
            "fp": state["fp"],
            "actual_fpr": None if negatives == 0 else state["fp"] / negatives,
            "detection_rate": detection_rate,
            "tie_group_size": state["tie_group_size"],
            "tie_group_positive": state["tie_group_positive"],
            "tie_group_negative": state["tie_group_negative"],
            "next_reachable_fp": next_reachable[selected_fp],
        }
        if positive_paths is not None:
            point["unalerted_fraction"] = (
                None if detection_rate is None else 1.0 - detection_rate
            )
        curve.append(point)
    anchors = []
    for nominal_fpr in DISPLAY_FPR_ANCHORS:
        budget = min(negatives, int(np.floor(nominal_fpr * negatives)))
        anchors.append({"nominal_fpr": nominal_fpr, **curve[budget]})
    timely_detection_ladders: list[dict[str, Any]] = []
    if positive_paths is not None:
        ladder_references: dict[float, tuple[int, str]] = {}
        for anchor in anchors:
            threshold = float(anchor["threshold"])
            if threshold not in ladder_references:
                ladder = _timely_detection_ladder(positive_paths, threshold)
                ladder_index = len(timely_detection_ladders)
                timely_detection_ladders.append(ladder)
                ladder_references[threshold] = (
                    ladder_index,
                    str(ladder["ladder_sha256"]),
                )
            ladder_index, ladder_sha256 = ladder_references[threshold]
            anchor.update(
                {
                    "timely_detection_ladder_index": ladder_index,
                    "timely_detection_ladder_sha256": ladder_sha256,
                }
            )
        total_ladder_points = sum(
            len(ladder["points"]) for ladder in timely_detection_ladders
        )
        if len(timely_detection_ladders) > len(DISPLAY_FPR_ANCHORS):
            raise RuntimeError("及时检出阶梯数超过六个预注册锚点")
        if total_ladder_points > len(DISPLAY_FPR_ANCHORS) * positives:
            raise RuntimeError("及时检出压缩阶梯点数超过 6×正实体上界")
    result = {
        "schema_version": "common-integer-fp-curve-v1",
        "positive_entities": positives,
        "negative_entities": negatives,
        "budget_axis_start": 0,
        "budget_axis_stop": negatives,
        "complete_tie_groups": True,
        "interpolation": False,
        "curve": curve,
        "anchors": anchors,
    }
    if positive_paths is not None:
        result.update(
            {
                "timely_detection_ladder_contract": {
                    "schema_version": "integer-fp-ladder-reference-v1",
                    "exposure_index_base": 1,
                    "right_continuous": True,
                    "positive_entity_denominator_fixed": True,
                    "anchor_only": True,
                    "same_threshold_stored_once": True,
                    "anchor_reference_fields": [
                        "timely_detection_ladder_index",
                        "timely_detection_ladder_sha256",
                    ],
                    "maximum_ladders": len(DISPLAY_FPR_ANCHORS),
                    "maximum_total_points_formula": (
                        "display_anchor_count*positive_entity_denominator"
                    ),
                },
                "timely_detection_ladders": timely_detection_ladders,
                "timely_detection_ladder_count": len(
                    timely_detection_ladders
                ),
                "timely_detection_ladder_total_points": sum(
                    len(ladder["points"]) for ladder in timely_detection_ladders
                ),
                "timely_detection_ladders_sha256": canonical_sha256(
                    timely_detection_ladders
                ),
            }
        )
    return result


def _entity_aggregates(
    probabilities: np.ndarray,
    labels: np.ndarray,
    entity_ids: np.ndarray,
    exposure_indices: np.ndarray,
    power: float,
) -> dict[str, Any]:
    order = np.lexsort((exposure_indices, entity_ids))
    probabilities = probabilities[order].astype(np.float64, copy=False)
    labels = labels[order].astype(np.uint8, copy=False)
    entity_ids = entity_ids[order].astype(np.int64, copy=False)
    unique_entities, starts = np.unique(entity_ids, return_index=True)
    stops = np.r_[starts[1:], entity_ids.size]
    entity_labels = np.empty(unique_entities.size, dtype=np.uint8)
    entity_scores = np.empty(unique_entities.size, dtype=np.float64)
    maximum_scores = np.empty(unique_entities.size, dtype=np.float64)
    operational_scores = np.empty(unique_entities.size, dtype=np.float64)
    positive_paths: dict[int, np.ndarray] = {}
    for output_index, (start, stop) in enumerate(zip(starts, stops, strict=True)):
        values = probabilities[start:stop]
        entity_labels[output_index] = np.max(labels[start:stop])
        powered = np.power(np.clip(values, 1e-12, 1.0), power)
        prefix = np.power(
            np.cumsum(powered) / np.arange(1, values.size + 1, dtype=np.float64),
            1.0 / power,
        )
        entity_scores[output_index] = prefix[-1]
        maximum_scores[output_index] = np.max(values)
        operational_scores[output_index] = np.max(prefix)
        if entity_labels[output_index] == 1:
            positive_paths[int(unique_entities[output_index])] = prefix
    return {
        "labels": entity_labels,
        "scores": entity_scores,
        "maximum_scores": maximum_scores,
        "operational_scores": operational_scores,
        "positive_paths": positive_paths,
    }


@torch.inference_mode()
def evaluate_dataset(
    *,
    model: Any,
    dataset: Any,
    purpose: str,
    label_stage_token: str,
    batch_sequences: int,
    device: torch.device,
) -> dict[str, Any]:
    """评价时只返回聚合指标，不持久化个体数组。"""

    if batch_sequences <= 0:
        raise ValueError("评价序列批量必须为正")
    rows = sequence_rows_for_purpose(dataset, purpose)
    sequence_entities, sequence_times = _sequence_sidecars(dataset, purpose)
    order = np.argsort(np.asarray(sequence_times[rows]), kind="stable")
    rows = rows[order]
    resolver = dataset.open_label_resolver(label_stage_token)
    probability_parts: list[np.ndarray] = []
    label_parts: list[np.ndarray] = []
    entity_parts: list[np.ndarray] = []
    exposure_parts: list[np.ndarray] = []
    exposure_counts: dict[int, int] = {}
    model.eval()
    for start in range(0, rows.size, batch_sequences):
        batch_rows = rows[start : start + batch_sequences]
        batch = dataset.gather_sequences(batch_rows)
        features = torch.as_tensor(
            batch["features"], dtype=torch.float32, device=device
        )
        valid_mask = torch.as_tensor(
            batch["valid_mask"], dtype=torch.bool, device=device
        )
        logits = model(features, valid_mask)
        probabilities = torch.sigmoid(logits.float()).cpu().numpy()
        mask = np.asarray(batch["valid_mask"], dtype=bool)
        raw_rows = np.asarray(batch["raw_row_indices"])
        flat_raw_rows = raw_rows[mask]
        flat_labels = resolver.resolve(flat_raw_rows)
        flat_probabilities = probabilities[mask].astype(np.float64, copy=False)
        batch_entity_values: list[np.ndarray] = []
        batch_exposure_values: list[np.ndarray] = []
        for local_index, sequence_row in enumerate(batch_rows):
            count = int(np.count_nonzero(mask[local_index]))
            entity = int(sequence_entities[sequence_row])
            previous = exposure_counts.get(entity, 0)
            batch_entity_values.append(np.full(count, entity, dtype=np.int64))
            batch_exposure_values.append(
                np.arange(previous + 1, previous + count + 1, dtype=np.int64)
            )
            exposure_counts[entity] = previous + count
        probability_parts.append(flat_probabilities)
        label_parts.append(flat_labels.astype(np.uint8, copy=False))
        entity_parts.append(np.concatenate(batch_entity_values))
        exposure_parts.append(np.concatenate(batch_exposure_values))
    probabilities = np.concatenate(probability_parts)
    labels = np.concatenate(label_parts)
    entity_ids = np.concatenate(entity_parts)
    exposure_indices = np.concatenate(exposure_parts)
    if not (
        probabilities.size
        == labels.size
        == entity_ids.size
        == exposure_indices.size
    ):
        raise RuntimeError("CUDA-RWKV 评价聚合数组行数不一致")
    power = float(model.pooling_power.detach().cpu().item())
    aggregates = _entity_aggregates(
        probabilities, labels, entity_ids, exposure_indices, power
    )
    entity_labels = aggregates["labels"]
    entity_scores = aggregates["scores"]
    maximum_scores = aggregates["maximum_scores"]
    terminal_curve = complete_integer_fp_curve(entity_scores, entity_labels)
    first_alert_curve = complete_integer_fp_curve(
        aggregates["operational_scores"],
        entity_labels,
        positive_paths=aggregates["positive_paths"],
    )
    result = {
        "schema_version": "cuda-rwkv-aggregate-evaluation-v1",
        "purpose": purpose,
        "flow_count": int(labels.size),
        "entity_count": int(entity_labels.size),
        "positive_flow_count": int(labels.sum()),
        "positive_entity_count": int(entity_labels.sum()),
        "pooling_power": power,
        "flow_average_precision": float(average_precision_score(labels, probabilities)),
        "entity_average_precision": float(
            average_precision_score(entity_labels, entity_scores)
        ),
        "maximum_entity_average_precision": float(
            average_precision_score(entity_labels, maximum_scores)
        ),
        "terminal_common_integer_fp": terminal_curve,
        "first_alert_common_integer_fp": first_alert_curve,
        "persisted_score_rows": 0,
        "persisted_label_rows": 0,
        "persisted_member_rows": 0,
    }
    result["result_sha256"] = canonical_sha256(result)
    return result
