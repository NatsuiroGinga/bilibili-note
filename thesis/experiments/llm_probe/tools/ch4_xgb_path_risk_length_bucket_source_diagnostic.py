#!/usr/bin/env python3
"""按冻结长度桶诊断源年实体路径最大风险，不训练新模型。"""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

np: Any = None
base: Any = None
path_max: Any = None

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-path-risk-length-bucket-lspr23-diagnostic-seed42-v1"
DISPLAY_NAME = "路径最大条件风险与漏检轨迹源年零训练诊断"
SCHEMA_VERSION = "ch4-xgb-path-risk-length-bucket-source-diagnostic-v1"
CONFIG_NAME = "ch4-xgb-path-risk-length-bucket-source-diagnostic-seed42-v1.json"
BASE_CONFIG_NAME = "ch4-xgb-entity-exposure-lesion-source-diagnostic-seed42-v1.json"
PARENT_M1_RUN_ID = "ch4-xgb-entity-path-max-tong-same-model-q0-seed42-v1"
PARENT_MODEL_RUN_ID = "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
ALLOWED_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "ent23", "t23_flow")
METHODS = (
    "B0_first",
    "B1_all_source",
    "M1_path_max_tong_same_model_crosscal",
)
BUCKETS = (
    ("1-2", 1, 2),
    ("3-10", 3, 10),
    ("11-100", 11, 100),
    ("101-1000", 101, 1000),
    ("1001+", 1001, None),
)
SOURCE_THRESHOLD = 3.660049696918577e-05
MODELS_TRAINED = 0


class InputContractError(RuntimeError):
    """输入身份、隔离或聚合合同无效。"""


def load_runtime_dependencies() -> None:
    global np, base, path_max
    import numpy as numpy_module
    import ch4_xgb_entity_exposure_lesion_source_diagnostic as base_module
    import ch4_xgb_entity_path_max_np_q0 as path_max_module

    np = numpy_module
    base = base_module
    path_max = path_max_module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / CONFIG_NAME)
    parser.add_argument(
        "--parent-run-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / PARENT_MODEL_RUN_ID,
    )
    parser.add_argument(
        "--parent-config",
        type=Path,
        default=ROOT / "configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json",
    )
    parser.add_argument("--threshold-seal", type=Path)
    parser.add_argument("--parent-recovery-proof", type=Path)
    parser.add_argument("--parent-m1-summary", type=Path)
    parser.add_argument(
        "--out", type=Path, default=ROOT / "runs/diagnostics" / RUN_ID
    )
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise InputContractError(f"JSON 顶层不是对象：{path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(partial, path)


def validate_config(config: dict[str, Any]) -> None:
    expected = {
        "schema_version": SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "source_year": "LSPR23",
        "source_year_only": True,
        "zero_training": True,
        "parent_m1_run_id": PARENT_M1_RUN_ID,
        "comparison_operator": ">",
        "entity_fpr_budget": 0.04,
        "allowed_arrays": list(ALLOWED_ARRAYS),
        "target_year_arrays_read": 0,
        "models_trained": 0,
        "oof_models_loaded": 3,
        "sequence_batch": 2048,
        "methods": list(METHODS),
        "length_buckets": [
            {"name": name, "minimum": lower, "maximum": upper}
            for name, lower, upper in BUCKETS
        ],
        "missed_path_quantiles": [0.75, 0.9, 0.95],
        "length_usage": "sealed_path_offline_bucketing_only",
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise InputContractError(f"配置字段不符：{key}")
    parent_contract = config.get("parent_m1_summary", {})
    if parent_contract != {
        "relative_path": (
            "runs/diagnostics/"
            "ch4-xgb-entity-path-max-tong-same-model-q0-seed42-v1/summary.json"
        ),
        "sha256": "2e4bbfe044b9ce9407090af765220fc7bc5829188cadcdfb33284002f633d462",
        "schema_version": "ch4-xgb-entity-path-max-tong-same-model-summary-v1",
        "run_id": PARENT_M1_RUN_ID,
        "simultaneous_round_count": 6,
    }:
        raise InputContractError("父 M1 摘要合同不符")
    if config.get("expected_parent_aggregate") != {
        "B0_first": {
            "negative_entities": 150441,
            "positive_entities": 239,
            "false_positive_entities": 6017,
            "detected_positive_entities": 232,
            "entity_fpr": 0.03999574584056208,
            "detection_rate": 0.9707112970711297,
        },
        "B1_all_source": {
            "negative_entities": 150441,
            "positive_entities": 239,
            "false_positive_entities": 7329,
            "detected_positive_entities": 236,
            "entity_fpr": 0.04871677268829641,
            "detection_rate": 0.9874476987447699,
        },
        "M1_path_max_tong_same_model_crosscal": {
            "negative_entities": 150441,
            "positive_entities": 239,
            "false_positive_entities": 5583,
            "detected_positive_entities": 235,
            "entity_fpr": 0.03711089397172313,
            "detection_rate": 0.9832635983263598,
        },
    }:
        raise InputContractError("父 M1 总体指标合同不符")
    if config.get("artifact_policy") != {
        "persist_aggregate_results": True,
        "persist_input_resource_status_log_manifest": True,
        "persist_entity_keys": False,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_fold_membership": False,
        "persist_new_models": False,
    }:
        raise InputContractError("聚合制品边界不符")
    if config.get("resource_contract") != {
        "estimated_peak_host_gib": 17,
        "minimum_available_host_gib": 17,
        "minimum_free_gpu_memory_gib": 0,
        "runtime_gpu_floor_gib": 0,
        "minimum_free_disk_gib": 30,
    }:
        raise InputContractError("CPU 资源合同不符")


def resolve_paths(args: argparse.Namespace, config: dict[str, Any]) -> None:
    if args.parent_m1_summary is None:
        args.parent_m1_summary = ROOT / config["parent_m1_summary"]["relative_path"]


def validate_parent_m1_summary(
    path: Path, config: dict[str, Any]
) -> dict[str, Any]:
    contract = config["parent_m1_summary"]
    if not path.is_file() or base.sha256_file(path) != contract["sha256"]:
        raise InputContractError("父 M1 摘要缺失或 SHA-256 不符")
    summary = load_json(path)
    if (
        summary.get("schema_version") != contract["schema_version"]
        or summary.get("run_id") != contract["run_id"]
        or summary.get("source_year") != "LSPR23"
        or summary.get("target_year_arrays_read") != 0
        or summary.get("training_runs_started") != 0
        or summary.get("comparison_operator") != ">"
        or summary.get("simultaneous_round_count") != 6
        or summary.get("aggregate") != config["expected_parent_aggregate"]
    ):
        raise InputContractError("父 M1 摘要身份、隔离字段或总体指标不符")
    integrity = summary.get("integrity", {})
    if integrity != {
        "flow_coverage_count": base.N_FLOW,
        "duplicate_flow_coverage_count": 0,
        "within_segment_time_reversals": 0,
        "cross_segment_time_reversals": 0,
        "scored_flow_count": base.N_FLOW,
        "oof_models_loaded": 3,
        "per_flow_scores_persisted": 0,
        "per_entity_scores_persisted": 0,
    }:
        raise InputContractError("父 M1 覆盖或持久化边界不符")
    rounds = summary.get("rounds")
    expected_directions = [
        (fold, calibration_half, 1 - calibration_half)
        for fold in range(base.N_FOLD)
        for calibration_half in (0, 1)
    ]
    if not isinstance(rounds, list) or len(rounds) != len(expected_directions):
        raise InputContractError("父 M1 六方向缺失")
    actual_directions = [
        (
            item.get("model_fold"),
            item.get("calibration_half"),
            item.get("evaluation_half"),
        )
        for item in rounds
    ]
    if actual_directions != expected_directions:
        raise InputContractError("父 M1 六方向顺序或角色不符")
    for item in rounds:
        threshold = item.get("path_threshold_receipt", {})
        if (
            not math.isfinite(float(threshold.get("threshold", math.nan)))
            or threshold.get("comparison_operator") != ">"
            or threshold.get("violation_bound") > (0.05 / 6)
            or item.get("metrics", {}).keys() != set(METHODS)
        ):
            raise InputContractError("父 M1 方向阈值、证书或方法不符")
    return summary


def make_m1_thresholds(
    parent_summary: dict[str, Any],
    fold_of_entity: np.ndarray,
    inner_halves: np.ndarray,
) -> np.ndarray:
    thresholds = np.full(base.N_ENTITY, np.nan, np.float64)
    for item in parent_summary["rounds"]:
        mask = (fold_of_entity == int(item["model_fold"])) & (
            inner_halves == int(item["evaluation_half"])
        )
        thresholds[mask] = float(item["path_threshold_receipt"]["threshold"])
    if not np.isfinite(thresholds).all():
        raise InputContractError("六方向未给全部实体分配 M1 阈值")
    return thresholds


def update_entity_paths(
    rows: np.ndarray,
    entities: np.ndarray,
    times: np.ndarray,
    raw_scores: np.ndarray,
    m1_thresholds: np.ndarray,
    cumulative_sum: np.ndarray,
    exposure_count: np.ndarray,
    first_scores: np.ndarray,
    path_maximum: np.ndarray,
    running_scores: np.ndarray,
    b1_first_alert_exposure: np.ndarray,
    b1_first_alert_time: np.ndarray,
    m1_first_alert_exposure: np.ndarray,
    m1_first_alert_time: np.ndarray,
) -> None:
    boundaries = np.flatnonzero(np.r_[True, entities[1:] != entities[:-1], True])
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        entity = int(entities[left])
        prior = int(exposure_count[entity])
        scores = np.asarray(raw_scores[left:right], np.float32)
        clipped = np.clip(scores, 1e-7, 1.0).astype(np.float64)
        cumulative = np.cumsum(clipped, dtype=np.float64) + cumulative_sum[entity]
        denominator = np.arange(prior + 1, prior + len(scores) + 1, dtype=np.float64)
        running = (cumulative / denominator).astype(np.float32)
        running_scores[rows[left:right]] = running
        if prior == 0:
            first_scores[entity] = scores[0]
        path_maximum[entity] = max(
            float(path_maximum[entity]), float(running.max())
        )
        if b1_first_alert_exposure[entity] == 0:
            crossing = np.flatnonzero(running > SOURCE_THRESHOLD)
            if len(crossing):
                offset = int(crossing[0])
                b1_first_alert_exposure[entity] = prior + offset + 1
                b1_first_alert_time[entity] = float(times[left + offset])
        if m1_first_alert_exposure[entity] == 0:
            crossing = np.flatnonzero(running > m1_thresholds[entity])
            if len(crossing):
                offset = int(crossing[0])
                m1_first_alert_exposure[entity] = prior + offset + 1
                m1_first_alert_time[entity] = float(times[left + offset])
        cumulative_sum[entity] = cumulative[-1]
        exposure_count[entity] = prior + len(scores)


def score_entity_paths(
    xgb_module: Any,
    matrix: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
    flow_times: np.ndarray,
    fold_of_entity: np.ndarray,
    m1_thresholds: np.ndarray,
    parent_root: Path,
    seal: dict[str, Any],
    base_config: dict[str, Any],
) -> dict[str, Any]:
    cumulative_sum = np.zeros(base.N_ENTITY, np.float64)
    exposure_count = np.zeros(base.N_ENTITY, np.int64)
    first_scores = np.full(base.N_ENTITY, np.nan, np.float32)
    path_maximum = np.full(base.N_ENTITY, -np.inf, np.float32)
    running_scores = np.full(base.N_FLOW, np.nan, np.float32)
    b1_first_alert_exposure = np.zeros(base.N_ENTITY, np.int64)
    b1_first_alert_time = np.full(base.N_ENTITY, np.nan, np.float64)
    m1_first_alert_exposure = np.zeros(base.N_ENTITY, np.int64)
    m1_first_alert_time = np.full(base.N_ENTITY, np.nan, np.float64)
    seen = np.zeros(base.N_FLOW, np.bool_)
    receipts: list[dict[str, Any]] = []
    sealed = {item["filename"]: item for item in seal["source_model_receipts"]}
    batch_size = int(base_config["sequence_batch"])
    for fold in range(base.N_FOLD):
        name = f"model_oof_semantic168_fold{fold}.json"
        model_path = parent_root / name
        actual_sha = base.sha256_file(model_path)
        if actual_sha != sealed[name]["sha256"]:
            raise InputContractError(f"折 {fold} 模型 SHA-256 不符")
        booster = xgb_module.Booster()
        booster.load_model(model_path)
        if int(booster.num_boosted_rounds()) != base.N_TREE:
            raise InputContractError(f"折 {fold} 模型树数不符")
        booster.set_param({"device": "cpu"})
        receipt = {
            "fold": fold,
            "filename": name,
            "sha256": actual_sha,
            "num_boosted_rounds": base.N_TREE,
            "prediction_device": "cpu",
        }
        selected_sequences = np.flatnonzero(fold_of_entity[sequence_entities] == fold)
        predicted = 0
        started = time.time()
        for start in range(0, len(selected_sequences), batch_size):
            selected = selected_sequences[start : start + batch_size]
            index_block = np.asarray(indices[selected])
            valid = np.asarray(masks[selected]) > 0
            rows = np.asarray(index_block[valid], np.int64)
            entities = np.broadcast_to(
                np.asarray(sequence_entities[selected], np.int64)[:, None], valid.shape
            )[valid]
            if seen[rows].any():
                raise InputContractError("OOF 长度桶诊断重复覆盖流")
            seen[rows] = True
            raw_scores = np.asarray(booster.inplace_predict(matrix[rows]), np.float32)
            if raw_scores.shape != (len(rows),) or not np.isfinite(raw_scores).all():
                raise InputContractError("OOF 长度桶诊断分数异常")
            update_entity_paths(
                rows,
                entities,
                np.asarray(flow_times[rows], np.float64),
                raw_scores,
                m1_thresholds,
                cumulative_sum,
                exposure_count,
                first_scores,
                path_maximum,
                running_scores,
                b1_first_alert_exposure,
                b1_first_alert_time,
                m1_first_alert_exposure,
                m1_first_alert_time,
            )
            predicted += len(rows)
            base.beat(
                f"semantic168/fold{fold}/长度桶诊断OOF",
                min(start + batch_size, len(selected_sequences)),
                len(selected_sequences),
                started,
            )
        receipt.update(
            {
                "holdout_entity_count": int((fold_of_entity == fold).sum()),
                "predicted_flow_count": predicted,
            }
        )
        receipts.append(receipt)
        del booster, selected_sequences
    if (
        not seen.all()
        or int(exposure_count.sum()) != base.N_FLOW
        or not np.isfinite(first_scores).all()
        or not np.isfinite(path_maximum).all()
        or not np.isfinite(running_scores).all()
    ):
        raise InputContractError("三折路径诊断未完整覆盖源年流或实体")
    return {
        "first_scores": first_scores,
        "path_maximum": path_maximum,
        "running_scores": running_scores,
        "exposure_count": exposure_count,
        "b1_first_alert_exposure": b1_first_alert_exposure,
        "b1_first_alert_time": b1_first_alert_time,
        "m1_first_alert_exposure": m1_first_alert_exposure,
        "m1_first_alert_time": m1_first_alert_time,
        "model_receipts": receipts,
        "scored_flow_count": int(seen.sum()),
    }


def distribution(values: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        return {
            "count": 0,
            "minimum": None,
            "p25": None,
            "median": None,
            "mean": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "maximum": None,
        }
    return {
        "count": int(len(finite)),
        "minimum": float(finite.min()),
        "p25": float(np.percentile(finite, 25)),
        "median": float(np.median(finite)),
        "mean": float(finite.mean()),
        "p75": float(np.percentile(finite, 75)),
        "p90": float(np.percentile(finite, 90)),
        "p95": float(np.percentile(finite, 95)),
        "maximum": float(finite.max()),
    }


def method_counts(
    entity_labels: np.ndarray, alerts: np.ndarray, selection: np.ndarray
) -> dict[str, int | float | None]:
    negative = selection & (entity_labels == 0)
    positive = selection & (entity_labels == 1)
    n_negative = int(negative.sum())
    n_positive = int(positive.sum())
    fp = int((alerts & negative).sum())
    tp = int((alerts & positive).sum())
    return {
        "negative_entities": n_negative,
        "positive_entities": n_positive,
        "false_positive_entities": fp,
        "detected_positive_entities": tp,
        "entity_fpr": fp / n_negative if n_negative else None,
        "detection_rate": tp / n_positive if n_positive else None,
    }


def add_counts(total: dict[str, int], metric: dict[str, Any]) -> None:
    for key in (
        "negative_entities",
        "positive_entities",
        "false_positive_entities",
        "detected_positive_entities",
    ):
        total[key] = total.get(key, 0) + int(metric[key])


def pooled_counts(total: dict[str, int]) -> dict[str, int | float | None]:
    negative = total["negative_entities"]
    positive = total["positive_entities"]
    return {
        **total,
        "entity_fpr": total["false_positive_entities"] / negative
        if negative
        else None,
        "detection_rate": total["detected_positive_entities"] / positive
        if positive
        else None,
    }


def metric_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    def difference(key: str) -> float | int | None:
        left = candidate[key]
        right = baseline[key]
        if left is None or right is None:
            return None
        return left - right

    return {
        "false_positive_entities": difference("false_positive_entities"),
        "detected_positive_entities": difference("detected_positive_entities"),
        "entity_fpr": difference("entity_fpr"),
        "detection_rate": difference("detection_rate"),
    }


def first_alert_summary(
    selection: np.ndarray,
    exposure: np.ndarray,
    alert_time: np.ndarray,
    first_time: np.ndarray,
) -> dict[str, Any]:
    alerted = selection & (exposure > 0)
    return {
        "eligible_entity_count": int(selection.sum()),
        "alerted_entity_count": int(alerted.sum()),
        "never_alerted_entity_count": int((selection & (exposure == 0)).sum()),
        "first_alert_exposure": distribution(exposure[alerted]),
        "raw_time_difference": distribution(alert_time[alerted] - first_time[alerted]),
    }


def assign_length_buckets(lengths: np.ndarray) -> np.ndarray:
    result = np.full(len(lengths), -1, np.int8)
    for index, (_, lower, upper) in enumerate(BUCKETS):
        mask = lengths >= lower
        if upper is not None:
            mask &= lengths <= upper
        if np.any((result >= 0) & mask):
            raise InputContractError("最终长度桶发生重叠")
        result[mask] = index
    if np.any(result < 0):
        raise InputContractError("最终长度桶未覆盖全部实体")
    return result


def missed_path_summary(
    missed: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
    running_scores: np.ndarray,
    exposure_count: np.ndarray,
    thresholds: np.ndarray,
) -> dict[str, Any]:
    missed_entities = np.flatnonzero(missed)
    paths: dict[int, list[np.ndarray]] = {int(entity): [] for entity in missed_entities}
    missed_sequences = np.flatnonzero(missed[sequence_entities])
    for sequence in missed_sequences:
        valid = np.asarray(masks[sequence]) > 0
        rows = np.asarray(indices[sequence, valid], np.int64)
        entity = int(sequence_entities[sequence])
        paths[entity].append(np.asarray(running_scores[rows], np.float32))
    descriptors: dict[str, list[float]] = {
        "path_length": [],
        "direction_threshold": [],
        "path_maximum": [],
        "path_mean": [],
        "path_median": [],
        "path_p75": [],
        "path_p90": [],
        "path_p95": [],
        "path_maximum_over_threshold": [],
        "path_mean_over_threshold": [],
        "path_median_over_threshold": [],
        "path_p75_over_threshold": [],
        "path_p90_over_threshold": [],
        "path_p95_over_threshold": [],
    }
    for entity in missed_entities:
        values = np.concatenate(paths[int(entity)]).astype(np.float64, copy=False)
        if len(values) != int(exposure_count[entity]) or not np.isfinite(values).all():
            raise InputContractError("M1 漏检正实体轨迹聚合不完整")
        threshold = float(thresholds[entity])
        statistics = {
            "path_maximum": float(values.max()),
            "path_mean": float(values.mean()),
            "path_median": float(np.median(values)),
            "path_p75": float(np.percentile(values, 75)),
            "path_p90": float(np.percentile(values, 90)),
            "path_p95": float(np.percentile(values, 95)),
        }
        descriptors["path_length"].append(float(len(values)))
        descriptors["direction_threshold"].append(threshold)
        for name, value in statistics.items():
            descriptors[name].append(value)
            descriptors[f"{name}_over_threshold"].append(value / threshold)
    return {
        "entity_count": int(missed.sum()),
        "aggregation_boundary": (
            "仅输出全部 M1 漏检正实体的描述性聚合，不输出实体键或逐实体统计"
        ),
        "statistics": {
            name: distribution(np.asarray(values, np.float64))
            for name, values in descriptors.items()
        },
    }


def build_results(
    config: dict[str, Any],
    parent_summary: dict[str, Any],
    entity_labels: np.ndarray,
    entity_lengths: np.ndarray,
    first_time: np.ndarray,
    fold_of_entity: np.ndarray,
    inner_halves: np.ndarray,
    scored: dict[str, Any],
    m1_thresholds: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
) -> dict[str, Any]:
    length_bucket = assign_length_buckets(entity_lengths)
    b0_exposure = np.where(scored["first_scores"] > SOURCE_THRESHOLD, 1, 0).astype(
        np.int64
    )
    b0_time = np.where(b0_exposure > 0, first_time, np.nan)
    exposures = {
        "B0_first": b0_exposure,
        "B1_all_source": scored["b1_first_alert_exposure"],
        "M1_path_max_tong_same_model_crosscal": scored[
            "m1_first_alert_exposure"
        ],
    }
    alert_times = {
        "B0_first": b0_time,
        "B1_all_source": scored["b1_first_alert_time"],
        "M1_path_max_tong_same_model_crosscal": scored["m1_first_alert_time"],
    }
    alerts = {name: values > 0 for name, values in exposures.items()}
    direction_results: list[dict[str, Any]] = []
    aggregate_totals = {name: {} for name in METHODS}
    bucket_totals = {
        bucket_name: {name: {} for name in METHODS}
        for bucket_name, _, _ in BUCKETS
    }
    for parent_round in parent_summary["rounds"]:
        fold = int(parent_round["model_fold"])
        evaluation_half = int(parent_round["evaluation_half"])
        evaluation = (fold_of_entity == fold) & (inner_halves == evaluation_half)
        overall_metrics = {
            name: method_counts(entity_labels, alerts[name], evaluation)
            for name in METHODS
        }
        if overall_metrics != parent_round["metrics"]:
            raise InputContractError(
                f"方向 fold={fold}/eval={evaluation_half} 未精确复现父 M1 指标"
            )
        for name in METHODS:
            add_counts(aggregate_totals[name], overall_metrics[name])
        bucket_results: list[dict[str, Any]] = []
        direction_covered = 0
        for bucket_index, (bucket_name, lower, upper) in enumerate(BUCKETS):
            selection = evaluation & (length_bucket == bucket_index)
            direction_covered += int(selection.sum())
            method_results: dict[str, Any] = {}
            for name in METHODS:
                metric = method_counts(entity_labels, alerts[name], selection)
                add_counts(bucket_totals[bucket_name][name], metric)
                method_results[name] = {
                    "metrics": metric,
                    "first_alert": first_alert_summary(
                        selection,
                        exposures[name],
                        alert_times[name],
                        first_time,
                    ),
                }
            m1_metric = method_results[
                "M1_path_max_tong_same_model_crosscal"
            ]["metrics"]
            bucket_results.append(
                {
                    "bucket": bucket_name,
                    "minimum_length": lower,
                    "maximum_length": upper,
                    "entity_count": int(selection.sum()),
                    "methods": method_results,
                    "deltas": {
                        "M1_minus_B0": metric_delta(
                            m1_metric, method_results["B0_first"]["metrics"]
                        ),
                        "M1_minus_B1": metric_delta(
                            m1_metric, method_results["B1_all_source"]["metrics"]
                        ),
                    },
                }
            )
        if direction_covered != int(evaluation.sum()):
            raise InputContractError("方向长度桶未互斥覆盖全部评价实体")
        direction_results.append(
            {
                "model_fold": fold,
                "calibration_half": int(parent_round["calibration_half"]),
                "evaluation_half": evaluation_half,
                "m1_threshold": float(
                    parent_round["path_threshold_receipt"]["threshold"]
                ),
                "overall_metrics": overall_metrics,
                "length_buckets": bucket_results,
            }
        )
    aggregate = {
        name: pooled_counts(aggregate_totals[name]) for name in METHODS
    }
    if aggregate != parent_summary["aggregate"]:
        raise InputContractError("总体 B0/B1/M1 未精确复现父 M1 摘要")
    pooled_buckets: list[dict[str, Any]] = []
    for bucket_name, lower, upper in BUCKETS:
        metrics = {
            name: pooled_counts(bucket_totals[bucket_name][name]) for name in METHODS
        }
        m1_metric = metrics["M1_path_max_tong_same_model_crosscal"]
        pooled_buckets.append(
            {
                "bucket": bucket_name,
                "minimum_length": lower,
                "maximum_length": upper,
                "methods": metrics,
                "deltas": {
                    "M1_minus_B0": metric_delta(m1_metric, metrics["B0_first"]),
                    "M1_minus_B1": metric_delta(
                        m1_metric, metrics["B1_all_source"]
                    ),
                },
            }
        )
    method_risk_summary: dict[str, Any] = {}
    for name in METHODS:
        valid = [
            bucket
            for bucket in pooled_buckets
            if bucket["methods"][name]["entity_fpr"] is not None
        ]
        fprs = [float(bucket["methods"][name]["entity_fpr"]) for bucket in valid]
        worst = max(valid, key=lambda bucket: bucket["methods"][name]["entity_fpr"])
        method_risk_summary[name] = {
            "worst_bucket": worst["bucket"],
            "worst_bucket_fpr": worst["methods"][name]["entity_fpr"],
            "between_bucket_fpr_spread": max(fprs) - min(fprs),
            "long_bucket_support": {
                bucket["bucket"]: {
                    "negative_entities": bucket["methods"][name][
                        "negative_entities"
                    ],
                    "positive_entities": bucket["methods"][name][
                        "positive_entities"
                    ],
                }
                for bucket in pooled_buckets
                if bucket["bucket"] in {"101-1000", "1001+"}
            },
        }
    missed = (entity_labels == 1) & ~alerts[
        "M1_path_max_tong_same_model_crosscal"
    ]
    expected_missed = (
        int(parent_summary["aggregate"]["M1_path_max_tong_same_model_crosscal"][
            "positive_entities"
        ])
        - int(parent_summary["aggregate"]["M1_path_max_tong_same_model_crosscal"][
            "detected_positive_entities"
        ])
    )
    if int(missed.sum()) != expected_missed:
        raise InputContractError("M1 漏检正实体数未复现父摘要")
    return {
        "schema_version": "ch4-xgb-path-risk-length-bucket-aggregate-results-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "source_year": "LSPR23",
        "evidence": {
            "screening_only": True,
            "formal": False,
            "formal_paper_evidence": False,
            "independent_test": False,
            "zero_training": True,
        },
        "offline_length_bucketing_contract": {
            "buckets": config["length_buckets"],
            "sealed_after_online_scoring": True,
            "length_used_by_threshold_or_alert_rule": False,
            "mutually_exclusive_complete": True,
        },
        "parent_reproduction": {
            "parent_run_id": PARENT_M1_RUN_ID,
            "parent_summary_sha256": config["parent_m1_summary"]["sha256"],
            "exact_round_metrics_match": True,
            "exact_aggregate_match": True,
            "aggregate": aggregate,
        },
        "directions": direction_results,
        "pooled_length_buckets": pooled_buckets,
        "conditional_risk_summary": method_risk_summary,
        "m1_missed_positive_path_summary": missed_path_summary(
            missed,
            indices,
            masks,
            sequence_entities,
            scored["running_scores"],
            entity_lengths,
            m1_thresholds,
        ),
        "integrity": {
            "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
            "models_trained": MODELS_TRAINED,
            "oof_models_loaded": len(scored["model_receipts"]),
            "per_flow_scores_persisted": 0,
            "per_entity_scores_persisted": 0,
            "entity_keys_persisted": 0,
        },
        "claim_boundary": (
            "仅诊断 LSPR23 源年条件风险与漏检轨迹，不选择反射累积参数，"
            "不构成机制有效性或正式论文证据"
        ),
    }


def resource_summary(started: float) -> dict[str, Any]:
    maximum_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_host_bytes = int(maximum_rss * (1 if sys.platform == "darwin" else 1024))
    return {
        "schema_version": "ch4-xgb-path-risk-length-bucket-resource-summary-v1",
        "run_id": RUN_ID,
        "wall_seconds": time.time() - started,
        "peak_host_rss_bytes": peak_host_bytes,
        "prediction_device": "cpu",
        "cuda_peak_allocated_bytes": 0,
        "cuda_peak_reserved_bytes": 0,
        "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
        "models_trained": MODELS_TRAINED,
    }


def run(args: argparse.Namespace, config: dict[str, Any]) -> None:
    load_runtime_dependencies()
    resolve_paths(args, config)
    parent_summary = validate_parent_m1_summary(
        args.parent_m1_summary.resolve(), config
    )
    base_config_path = ROOT / "configs" / BASE_CONFIG_NAME
    base_config = load_json(base_config_path)
    base.validate_config(base_config)
    parent_args = argparse.Namespace(
        config=base_config_path,
        parent_run_root=args.parent_run_root,
        parent_config=args.parent_config,
        threshold_seal=args.threshold_seal,
        parent_recovery_proof=args.parent_recovery_proof,
        out=args.out.parent / base.RUN_ID,
    )
    base.resolve_paths(parent_args, base_config)
    seal = base.validate_threshold_seal(
        parent_args.threshold_seal.resolve(), base_config
    )
    parent = base.validate_parent(parent_args, base_config, seal)
    array_receipts = base.hash_allowed_arrays()
    if args.validate_inputs:
        print("CH4_PATH_RISK_LENGTH_BUCKET_INPUTS_VALID", flush=True)
        return

    protected = (
        "aggregate-results.json",
        "input-receipt.json",
        "resource-summary.json",
        "manifest.json",
    )
    if any((args.out / name).exists() for name in protected):
        raise InputContractError(f"同名诊断制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()
    script_sha = base.sha256_file(Path(__file__).resolve())
    config_sha = base.sha256_file(args.config.resolve())

    base.log("阶段一：只读加载 LSPR23 数组并执行覆盖、实体和时间硬门")
    labels = base.guarded_source_load("y23")
    indices = base.guarded_source_load("I23")
    masks = base.guarded_source_load("M23")
    sequence_entities = base.guarded_source_load("E23")
    flow_entities = base.guarded_source_load("ent23")
    flow_times = base.guarded_source_load("t23_flow")
    if base.TARGET_YEAR_ARRAYS_READ != 0:
        raise InputContractError("目标年数组读取计数非零")
    structure = base.scan_source_structure(
        labels, indices, masks, sequence_entities, flow_entities, flow_times
    )
    entity_labels = np.asarray(structure["entity_labels"], np.int8)
    entity_lengths = np.asarray(structure["entity_flow_counts"], np.int64)
    fold_of_entity = base.make_folds(entity_labels, int(config["seed"]))
    fold_sha = base.sha256_array(fold_of_entity)
    if fold_sha != base_config["source_threshold_contract"]["fold_assignment_sha256"]:
        raise InputContractError("实体折号哈希不符")
    fold_stats = base.fold_statistics(
        fold_of_entity,
        entity_labels,
        entity_lengths,
        np.asarray(structure["entity_positive_flow_counts"]),
    )
    if fold_stats != parent["selection"].get("fold_stat"):
        raise InputContractError("实体三折统计与父收据不符")
    inner_halves = path_max.make_inner_halves(
        fold_of_entity, entity_labels, int(config["seed"])
    )
    m1_thresholds = make_m1_thresholds(
        parent_summary, fold_of_entity, inner_halves
    )

    base.log("阶段二：构造 semantic168 并按三个冻结折模型重建路径分数")
    # 数据身份：X23 是 dijk 复现管线标准化后的特征矩阵（非有限值置 0 → 按 LSPR23 逐列均值和标准差
    # 标准化 → 裁剪 [-10, 10]），不是 raw83 原值。三个冻结折模型与它同源，故可直接读；
    # 按 raw83 拟合的模型不得读它。见该缓存目录的 README.md。
    semantic = base.build_semantic_matrix(base.CACHE / "X23.npy", indices, masks)
    import xgboost as xgb

    if xgb.__version__ != "3.2.0":
        raise InputContractError(f"XGBoost 版本不符：{xgb.__version__}")
    scored = score_entity_paths(
        xgb,
        semantic,
        indices,
        masks,
        sequence_entities,
        flow_times,
        fold_of_entity,
        m1_thresholds,
        args.parent_run_root.resolve(),
        seal,
        base_config,
    )
    del semantic
    if not np.array_equal(scored["exposure_count"], entity_lengths):
        raise InputContractError("在线评分曝光数与封印后最终长度不符")

    base.log("阶段三：封印在线告警后执行五桶离线聚合与父摘要精确核对")
    results = build_results(
        config,
        parent_summary,
        entity_labels,
        entity_lengths,
        np.asarray(structure["first_time"], np.float64),
        fold_of_entity,
        inner_halves,
        scored,
        m1_thresholds,
        indices,
        masks,
        sequence_entities,
    )
    results["integrity"].update(
        {
            "flow_coverage_count": structure["flow_coverage_count"],
            "duplicate_flow_coverage_count": structure[
                "duplicate_flow_coverage_count"
            ],
            "within_segment_time_reversals": structure[
                "within_segment_time_reversals"
            ],
            "cross_segment_time_reversals": structure[
                "cross_segment_time_reversals"
            ],
            "scored_flow_count": scored["scored_flow_count"],
            "length_bucket_entity_count": int(base.N_ENTITY),
        }
    )
    del scored["running_scores"]

    results_path = args.out / "aggregate-results.json"
    atomic_json(results_path, results)
    input_path = args.out / "input-receipt.json"
    atomic_json(
        input_path,
        {
            "schema_version": "ch4-xgb-path-risk-length-bucket-input-receipt-v1",
            "run_id": RUN_ID,
            "script_sha256": script_sha,
            "config_sha256": config_sha,
            "parent_m1_summary": {
                "path": str(args.parent_m1_summary.resolve()),
                "sha256": config["parent_m1_summary"]["sha256"],
            },
            "parent_model_run": parent,
            "arrays": array_receipts,
            "fold_assignment_sha256": fold_sha,
            "source_model_receipts": scored["model_receipts"],
            "source_year": "LSPR23",
            "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
            "models_trained": MODELS_TRAINED,
            "oof_models_loaded": len(scored["model_receipts"]),
            "entity_keys_persisted": 0,
            "per_flow_scores_persisted": 0,
            "per_entity_scores_persisted": 0,
        },
    )
    resource_path = args.out / "resource-summary.json"
    atomic_json(resource_path, resource_summary(started))
    manifest_names = (
        "aggregate-results.json",
        "input-receipt.json",
        "resource-summary.json",
    )
    manifest = {
        "schema_version": "ch4-xgb-path-risk-length-bucket-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
        "models_trained": MODELS_TRAINED,
        "entity_keys_persisted": 0,
        "per_flow_scores_persisted": 0,
        "per_entity_scores_persisted": 0,
        "files": {},
    }
    for name in manifest_names:
        path = args.out / name
        if not path.is_file() or path.stat().st_size <= 0:
            raise InputContractError(f"必需聚合制品缺失：{path}")
        manifest["files"][name] = {
            "bytes": path.stat().st_size,
            "sha256": base.sha256_file(path),
        }
    atomic_json(args.out / "manifest.json", manifest)
    base.log(
        "诊断完成：父 B0/B1/M1 六方向与总体精确复现，"
        f"M1漏检正实体={results['m1_missed_positive_path_summary']['entity_count']}"
    )


def main() -> int:
    args = parse_args()
    try:
        if not args.config.is_file():
            raise InputContractError(f"配置缺失：{args.config}")
        config = load_json(args.config)
        validate_config(config)
        if args.validate_config:
            print("CH4_PATH_RISK_LENGTH_BUCKET_CONFIG_VALID", flush=True)
            return 0
        run(args, config)
        return 0
    except InputContractError as error:
        print(f"INVALID_INPUT_CONTRACT: {error}", file=sys.stderr, flush=True)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
