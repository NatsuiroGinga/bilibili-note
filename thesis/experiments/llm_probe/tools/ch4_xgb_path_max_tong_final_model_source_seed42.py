#!/usr/bin/env python3
"""训练种子 42 最终单模型并执行源年实体路径最大 Tong 六臂评价。"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import resource
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch4_xgb_dtep_fixed_dyadic_q0 as xgb_parent  # noqa: E402
import ch4_xgb_entity_exposure_lesion_source_diagnostic as base  # noqa: E402
import ch4_xgb_entity_path_max_np_q0 as path_q0  # noqa: E402
from ch3_xgb_cpa_elp_eval_continuation import (  # noqa: E402
    AUTHORIZED_SWANLAB_PROJECT,
    AUTHORIZED_SWANLAB_WORKSPACE,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN_ID = "ch4-xgb-path-max-tong-final-model-source-seed42-v1-rerun1"
RUN_ID = "ch4-xgb-path-max-tong-final-model-source-seed42-v1-rerun2"
DISPLAY_NAME = "种子42最终单模型实体路径最大Tong源年六臂实验"
CONFIG_NAME = "ch4-xgb-path-max-tong-final-model-source-seed42-v1.json"
MODEL_NAME = "model_semantic168_final_source_seed42.json"
MODEL_RECEIPT_NAME = "final_model_receipt.json"
THRESHOLD_RECEIPT_NAME = "model_bound_threshold_receipt.json"
RESULT_NAME = "source_six_arm_results.json"
Q = 0.04
DELTA = 0.05
HOLDOUT_FOLD = 2
CALIBRATION_HALF = 1
EVALUATION_HALF = 0
METHODS = (
    "B0_first_empirical",
    "B1_all_fixed_empirical",
    "B2_first_tong",
    "B3_path_max_empirical",
    "B4_summable_exposure_budget",
    "M1_path_max_tong",
)
T0 = time.time()
LAST_BEAT = [T0]


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float) -> None:
    now = time.time()
    if now - LAST_BEAT[0] < 30.0 and done < total:
        return
    LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    eta = (total - done) / max(rate, 1e-9)
    log(
        f"  [{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {eta:.0f}s"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / CONFIG_NAME)
    parser.add_argument(
        "--parent-run-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / base.PARENT_RUN_ID,
    )
    parser.add_argument(
        "--parent-config",
        type=Path,
        default=ROOT / "configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json",
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "runs/candidates" / RUN_ID
    )
    parser.add_argument(
        "--resume-run-root",
        type=Path,
        default=ROOT / "runs/candidates" / SOURCE_RUN_ID,
    )
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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
        "schema_version": "ch4-xgb-path-max-tong-final-model-source-seed42-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "source_year": "LSPR23",
        "source_year_only": True,
        "seed": 42,
        "training_folds": [0, 1],
        "holdout_fold": HOLDOUT_FOLD,
        "calibration_half": CALIBRATION_HALF,
        "evaluation_half": EVALUATION_HALF,
        "base_adapter": "semantic168",
        "power_mean_p": 1.0,
        "num_boost_round": 800,
        "xgb_params": base.EXPECTED_XGB_PARAMS,
        "entity_fpr_budget": Q,
        "global_violation_probability": DELTA,
        "simultaneous_claim_count": 1,
        "m1_violation_probability": DELTA,
        "comparison_operator": ">",
        "methods": list(METHODS),
        "target_year_arrays_read": 0,
        "training_runs": 0,
        "allowed_arrays": list(base.ALLOWED_ARRAYS),
        "sequence_batch": 2048,
        "dmatrix_batch": 500000,
        "budget_curve": {
            "integer_budget_min": 0,
            "integer_budget_max_rule": "floor(q*n_cal_negative)",
            "confirmatory_budget": Q,
            "curve_is_descriptive": True,
        },
        "qualification_rule": (
            "M1_certificate_valid AND FPR(M1)<=0.04 AND "
            "delta_DR(M1-B0)>0 AND paired_95pct_lower>0"
        ),
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise base.InputContractError(f"配置字段不符：{key}")
    if config.get("fold_contract") != {
        "fold_assignment_sha256": (
            "a206048274edd5bb20c8e92874c0c2c1853009ebbd5ea1533940f2ab34fd5aa5"
        ),
        "fold_entity_counts": [50227, 50227, 50226],
        "fold_positive_entity_counts": [80, 80, 79],
        "half_algorithm": "make_inner_halves_randomstate42_class_stratified_mod2_v1",
        "training_entities": 100454,
        "training_negative_entities": 100294,
        "training_positive_entities": 160,
        "calibration_entities": 25112,
        "calibration_negative_entities": 25073,
        "calibration_positive_entities_unused": 39,
        "evaluation_entities": 25114,
        "evaluation_negative_entities": 25074,
        "evaluation_positive_entities": 40,
    }:
        raise base.InputContractError("实体折与角色容量合同不符")
    if config.get("score_contract") != {
        "first_exposure_score": "raw_float32_xgboost_score",
        "path_score": (
            "clip_[1e-7,1]_then_float64_cumulative_sum_then_float32_readout"
        ),
        "power": 1.0,
        "feature_view": "semantic168",
    }:
        raise base.InputContractError("分数合同不符")
    if config.get("entity_path_contract") != {
        "entity_key": "LSPR23_frozen_entity_index",
        "ordering": "stable_recorded_timestamp_order",
        "path_end_rule": "LSPR23_frozen_capture_all_recorded_exposures",
        "exposure_cutoff": None,
        "state": [
            "entity_key",
            "cumulative_score",
            "exposure_count",
            "last_timestamp",
            "alerted",
            "first_crossing_exposure",
        ],
    }:
        raise base.InputContractError("实体路径合同不符")
    if config.get("b4_contract") != {
        "allocation": "q_j=q/[j(j+1)]",
        "calibration": "empirical_strict_greater_than",
        "unavailable_level_threshold": "positive_infinity",
        "certificate_claimed": False,
    }:
        raise base.InputContractError("B4 压力对照合同不符")
    if config.get("artifact_policy") != {
        "persist_final_model": True,
        "persist_model_and_threshold_receipts": True,
        "persist_aggregate_results_and_integer_budget_curve": True,
        "persist_input_resource_swanlab_manifest": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_entity_ids": False,
        "persist_fold_membership": False,
        "persist_target_year_artifacts": False,
    }:
        raise base.InputContractError("制品白名单合同不符")
    if config.get("resource_contract") != {
        "estimated_wall_minutes_min": 5,
        "estimated_wall_minutes_max": 10,
        "estimated_peak_host_gib": 17.0,
        "host_admission_gib": 20.0,
        "estimated_peak_gpu_gib": 18.0,
        "gpu_floor_gib": 20.0,
        "required_gpu_count": 1,
        "required_gpu_memory_class_gib": 24,
    }:
        raise base.InputContractError("资源估算与准入合同不符")
    if config.get("tracking") != {
        "workspace": AUTHORIZED_SWANLAB_WORKSPACE,
        "project": AUTHORIZED_SWANLAB_PROJECT,
        "mode": "online",
        "aggregate_only": True,
    }:
        raise base.InputContractError("SwanLab 目的地或聚合边界不符")


def validate_parent_contract(args: argparse.Namespace) -> dict[str, Any]:
    parent_root = args.parent_run_root.resolve()
    if parent_root.name != base.PARENT_RUN_ID:
        raise base.InputContractError("父运行身份不符")
    if not args.parent_config.is_file():
        raise base.InputContractError(f"父配置缺失：{args.parent_config}")
    parent_config = load_json(args.parent_config)
    for key, value in base.EXPECTED_CONFIG.items():
        if parent_config.get(key) != value:
            raise base.InputContractError(f"父配置字段不符：{key}")
    receipts: dict[str, dict[str, Any]] = {}
    for name in ("selection_frozen_xgb2x2.json", "effective_config_receipts.json"):
        path = parent_root / name
        if not path.is_file() or path.stat().st_size <= 0:
            raise base.InputContractError(f"父冻结收据缺失：{path}")
        digest = base.sha256_file(path)
        if digest != base.EXPECTED_SHA256[name]:
            raise base.InputContractError(f"父冻结收据 SHA-256 不符：{name}")
        receipts[name] = {"bytes": path.stat().st_size, "sha256": digest}
    selection = load_json(parent_root / "selection_frozen_xgb2x2.json")
    if (
        selection.get("run_name") != base.PARENT_RUN_ID
        or selection.get("seed") != 42
        or selection.get("n_fold") != base.N_FOLD
        or selection.get("xgb_params") != base.EXPECTED_XGB_PARAMS
        or selection.get("adapter_selection", {}).get("selected") != "semantic168"
        or float(
            selection.get("p_selection", {})
            .get("semantic168", {})
            .get("p_selected", math.nan)
        )
        != 1.0
    ):
        raise base.InputContractError("父选择未冻结 semantic168、p=1 或 XGBoost 配置")
    return {
        "run_id": base.PARENT_RUN_ID,
        "root": str(parent_root),
        "config_path": str(args.parent_config.resolve()),
        "config_sha256": base.sha256_file(args.parent_config.resolve()),
        "receipts": receipts,
        "fold_stat": selection.get("fold_stat"),
    }


def role_manifest(
    role: str, entity_ids: np.ndarray, entity_labels: np.ndarray
) -> tuple[dict[str, Any], str]:
    labels = np.asarray(entity_labels[entity_ids], np.int8)
    manifest = {
        "role": role,
        "entity_count": int(len(entity_ids)),
        "negative_entity_count": int((labels == 0).sum()),
        "positive_entity_count": int((labels == 1).sum()),
        "entity_ids_sha256": base.sha256_array(np.asarray(entity_ids, np.int64)),
    }
    return manifest, base.canonical_sha256(manifest)


def empirical_threshold(values: np.ndarray, allowed_count: int) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    if len(finite) == 0 or not np.isfinite(finite).all():
        raise base.InputContractError("经验阈值缺少有限良性实体")
    return empirical_threshold_sorted(np.sort(finite), allowed_count)


def empirical_threshold_sorted(
    ordered: np.ndarray, allowed_count: int
) -> dict[str, Any]:
    if allowed_count < 0 or allowed_count >= len(ordered):
        raise base.InputContractError("经验阈值允许告警数越界")
    threshold = float(ordered[len(ordered) - allowed_count - 1])
    selected = int((ordered > threshold).sum())
    if selected > allowed_count:
        raise base.InputContractError("经验阈值严格越界数超过整数预算")
    return {
        "threshold": threshold,
        "population": int(len(ordered)),
        "allowed_count": allowed_count,
        "strictly_above_count": selected,
        "empirical_fpr": selected / len(ordered),
        "boundary_tie_count": int((ordered == threshold).sum()),
        "comparison_operator": ">",
    }


def tong_threshold_sorted(
    ordered: np.ndarray, rate: float, violation_probability: float
) -> dict[str, Any]:
    n = len(ordered)
    if n == 0 or rate <= 0.0:
        return {"available": False, "threshold": None, "population": n}
    if n * math.log1p(-rate) > math.log(violation_probability):
        return {"available": False, "threshold": None, "population": n}
    success_probability = 1.0 - rate
    low = max(1, int(math.floor(n * success_probability)))
    high = n
    while low < high:
        middle = (low + high) // 2
        if (
            path_q0.binomial_upper_tail(n, middle, success_probability)
            <= violation_probability
        ):
            high = middle
        else:
            low = middle + 1
    k_star = low
    threshold = float(ordered[k_star - 1])
    return {
        "available": True,
        "threshold": threshold,
        "population": n,
        "entity_fpr_budget": rate,
        "violation_probability": violation_probability,
        "rank_one_based": k_star,
        "violation_bound": path_q0.binomial_upper_tail(
            n, k_star, success_probability
        ),
        "previous_violation_bound": path_q0.binomial_upper_tail(
            n, k_star - 1, success_probability
        ),
        "strictly_above_count": int((ordered > threshold).sum()),
        "boundary_tie_count": int((ordered == threshold).sum()),
        "comparison_operator": ">",
    }


def maximum_b4_level(population: int, rate: float) -> int:
    level = 0
    while math.floor(rate * population / ((level + 1) * (level + 2))) >= 1:
        level += 1
    return level


def b4_thresholds(
    level_scores: np.ndarray, rate: float
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    ordered_levels = []
    for column in range(level_scores.shape[1]):
        values = np.asarray(level_scores[:, column], np.float64)
        ordered_levels.append(np.sort(values[np.isfinite(values)]))
    return b4_thresholds_sorted(ordered_levels, rate)


def b4_thresholds_sorted(
    ordered_levels: list[np.ndarray], rate: float
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    thresholds = np.full(len(ordered_levels), np.inf, np.float64)
    receipts: list[dict[str, Any]] = []
    for column, values in enumerate(ordered_levels):
        level = column + 1
        allocated_rate = rate / (level * (level + 1))
        allowed = int(math.floor(allocated_rate * len(values) + 1e-12))
        if allowed == 0:
            receipts.append(
                {
                    "exposure_index": level,
                    "support": int(len(values)),
                    "allocated_rate": allocated_rate,
                    "allowed_count": 0,
                    "available": False,
                    "threshold": None,
                }
            )
            continue
        receipt = empirical_threshold_sorted(values, allowed)
        thresholds[column] = receipt["threshold"]
        receipts.append(
            {
                "exposure_index": level,
                "support": int(len(values)),
                "allocated_rate": allocated_rate,
                "available": True,
                **receipt,
            }
        )
    return thresholds, receipts


def update_role_paths(
    entities: np.ndarray,
    times: np.ndarray,
    raw_scores: np.ndarray,
    local_of_entity: np.ndarray,
    cumulative_sum: np.ndarray,
    exposure_count: np.ndarray,
    first_scores: np.ndarray,
    path_max: np.ndarray,
    level_scores: np.ndarray,
    alert_thresholds: dict[str, Any] | None,
    first_alert_exposure: dict[str, np.ndarray],
    first_alert_time: dict[str, np.ndarray],
    crossing_counts: dict[str, int],
) -> None:
    boundaries = np.flatnonzero(np.r_[True, entities[1:] != entities[:-1], True])
    for left, right in zip(boundaries[:-1], boundaries[1:]):
        entity = int(entities[left])
        local = int(local_of_entity[entity])
        if local < 0:
            raise base.InputContractError("角色推理出现白名单外实体")
        prior = int(exposure_count[local])
        raw = np.asarray(raw_scores[left:right], np.float32)
        clipped = np.clip(raw, 1e-7, 1.0).astype(np.float64)
        cumulative = np.cumsum(clipped, dtype=np.float64) + cumulative_sum[local]
        indices = np.arange(prior + 1, prior + len(raw) + 1, dtype=np.int64)
        running = (cumulative / indices).astype(np.float32)
        if prior == 0:
            first_scores[local] = raw[0]
        path_max[local] = max(float(path_max[local]), float(running.max()))
        level_stop = min(prior + len(raw), level_scores.shape[1])
        if prior < level_stop:
            level_scores[local, prior:level_stop] = running[: level_stop - prior]
        if alert_thresholds is not None:
            scalar_rules = {
                "B1_all_fixed_empirical": alert_thresholds["B1_all_fixed_empirical"],
                "B3_path_max_empirical": alert_thresholds["B3_path_max_empirical"],
                "M1_path_max_tong": alert_thresholds["M1_path_max_tong"],
            }
            if prior == 0:
                for name in ("B0_first_empirical", "B2_first_tong"):
                    if raw[0] > float(alert_thresholds[name]):
                        first_alert_exposure[name][local] = 1
                        first_alert_time[name][local] = float(times[left])
                        crossing_counts[name] += 1
            for name, threshold in scalar_rules.items():
                crossing = np.flatnonzero(running > float(threshold))
                crossing_counts[name] += int(len(crossing))
                if len(crossing) and first_alert_exposure[name][local] == 0:
                    offset = int(crossing[0])
                    first_alert_exposure[name][local] = prior + offset + 1
                    first_alert_time[name][local] = float(times[left + offset])
            b4_values = np.full(len(running), np.inf, np.float64)
            valid = indices <= len(alert_thresholds["B4_summable_exposure_budget"])
            b4_values[valid] = np.asarray(
                alert_thresholds["B4_summable_exposure_budget"], np.float64
            )[indices[valid] - 1]
            crossing = np.flatnonzero(running > b4_values)
            crossing_counts["B4_summable_exposure_budget"] += int(len(crossing))
            if (
                len(crossing)
                and first_alert_exposure["B4_summable_exposure_budget"][local] == 0
            ):
                offset = int(crossing[0])
                first_alert_exposure["B4_summable_exposure_budget"][local] = (
                    prior + offset + 1
                )
                first_alert_time["B4_summable_exposure_budget"][local] = float(
                    times[left + offset]
                )
        cumulative_sum[local] = cumulative[-1]
        exposure_count[local] = prior + len(raw)


def score_role(
    booster: Any,
    matrix: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
    flow_times: np.ndarray,
    role_entities: np.ndarray,
    entity_flow_counts: np.ndarray,
    sequence_batch: int,
    level_count: int,
    tag: str,
    alert_thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    local_of_entity = np.full(base.N_ENTITY, -1, np.int32)
    local_of_entity[role_entities] = np.arange(len(role_entities), dtype=np.int32)
    cumulative_sum = np.zeros(len(role_entities), np.float64)
    exposure_count = np.zeros(len(role_entities), np.int64)
    first_scores = np.full(len(role_entities), np.nan, np.float32)
    path_max = np.full(len(role_entities), -np.inf, np.float32)
    level_scores = np.full((len(role_entities), level_count), np.nan, np.float32)
    first_alert_exposure = {
        name: np.zeros(len(role_entities), np.int64) for name in METHODS
    }
    first_alert_time = {
        name: np.full(len(role_entities), np.nan, np.float64) for name in METHODS
    }
    crossing_counts = {name: 0 for name in METHODS}
    selected_sequences = np.flatnonzero(local_of_entity[sequence_entities] >= 0)
    expected_flows = int(entity_flow_counts[role_entities].sum())
    predicted = 0
    prediction_seconds = 0.0
    update_seconds = 0.0
    started = time.time()
    for start in range(0, len(selected_sequences), sequence_batch):
        selected = selected_sequences[start : start + sequence_batch]
        index_block = np.asarray(indices[selected])
        valid = np.asarray(masks[selected]) > 0
        rows = np.asarray(index_block[valid], np.int64)
        entities = np.broadcast_to(
            np.asarray(sequence_entities[selected], np.int64)[:, None], valid.shape
        )[valid]
        predict_started = time.time()
        scores = np.asarray(booster.inplace_predict(matrix[rows]), np.float32)
        prediction_seconds += time.time() - predict_started
        if scores.shape != (len(rows),) or not np.isfinite(scores).all():
            raise base.InputContractError(f"{tag} 逐流分数异常")
        update_started = time.time()
        update_role_paths(
            entities,
            np.asarray(flow_times[rows], np.float64),
            scores,
            local_of_entity,
            cumulative_sum,
            exposure_count,
            first_scores,
            path_max,
            level_scores,
            alert_thresholds,
            first_alert_exposure,
            first_alert_time,
            crossing_counts,
        )
        update_seconds += time.time() - update_started
        predicted += len(rows)
        beat(tag, min(start + sequence_batch, len(selected_sequences)), len(selected_sequences), started)
    if (
        predicted != expected_flows
        or int(exposure_count.sum()) != expected_flows
        or not np.isfinite(first_scores).all()
        or not np.isfinite(path_max).all()
    ):
        raise base.InputContractError(f"{tag} 覆盖数或实体路径状态不完整")
    return {
        "first_scores": first_scores,
        "path_max": path_max,
        "level_scores": level_scores,
        "exposure_count": exposure_count,
        "first_alert_exposure": first_alert_exposure,
        "first_alert_time": first_alert_time,
        "crossing_counts": crossing_counts,
        "scored_flow_count": predicted,
        "wall_seconds": time.time() - started,
        "prediction_seconds": prediction_seconds,
        "control_update_seconds": update_seconds,
    }


def receipt_with_hash(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["receipt_sha256"] = base.canonical_sha256(result)
    return result


def validate_hashed_receipt(value: dict[str, Any], name: str) -> None:
    receipt_sha = value.get("receipt_sha256")
    unsigned = dict(value)
    unsigned.pop("receipt_sha256", None)
    if receipt_sha != base.canonical_sha256(unsigned):
        raise base.InputContractError(f"{name} 内部收据 SHA-256 不符")


def reload_serialized_identity_receipt(booster: Any) -> dict[str, Any]:
    config = json.loads(booster.save_config())
    expected = {
        ("learner", "learner_train_param", "booster"): "gbtree",
        ("learner", "learner_train_param", "objective"): "binary:logistic",
        ("learner", "gradient_booster", "name"): "gbtree",
        ("learner", "objective", "name"): "binary:logistic",
    }
    checks: list[dict[str, str]] = []
    for path, wanted in expected.items():
        value: Any = config
        try:
            for key in path:
                value = value[key]
        except (KeyError, TypeError) as error:
            raise base.InputContractError(
                f"重载模型缺少可持久化身份字段：{'.'.join(path)}"
            ) from error
        checks.append(
            {"path": ".".join(path), "actual": str(value), "expected": wanted}
        )
        if value != wanted:
            raise base.InputContractError(
                f"重载模型可持久化身份不符：{'.'.join(path)}"
            )
    return {
        "tag": "semantic168/final_seed42/reload_serialized_identity",
        "passed": True,
        "scope": "serialized_inference_identity_only",
        "training_hyperparameters_verified_by": "effective_training_receipt",
        "checks": checks,
    }


def load_bound_model(
    xgb_module: Any,
    model_path: Path,
    model_receipt_path: Path,
    threshold_receipt_path: Path,
    expected_run_id: str = RUN_ID,
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    model_receipt = load_json(model_receipt_path)
    threshold_receipt = load_json(threshold_receipt_path)
    validate_hashed_receipt(model_receipt, "最终模型")
    validate_hashed_receipt(threshold_receipt, "模型阈值")
    actual_model_sha = base.sha256_file(model_path)
    binding_fields = (
        "model_sha256",
        "training_entity_manifest_sha256",
        "calibration_entity_manifest_sha256",
        "score_contract_sha256",
        "entity_path_contract_sha256",
    )
    if (
        model_receipt.get("run_id") != expected_run_id
        or threshold_receipt.get("run_id") != expected_run_id
    ):
        raise base.InputContractError("模型或阈值收据运行身份不符")
    if actual_model_sha != model_receipt.get("model_sha256"):
        raise base.InputContractError("最终模型文件与模型收据不符")
    if model_receipt.get("num_boost_round") != base.N_TREE:
        raise base.InputContractError("最终模型收据树数不符")
    for field in binding_fields:
        if threshold_receipt.get(field) != model_receipt.get(field):
            raise base.InputContractError(f"模型—阈值强绑定字段不符：{field}")
    booster = xgb_module.Booster()
    booster.load_model(model_path)
    if int(booster.num_boosted_rounds()) != base.N_TREE:
        raise base.InputContractError("绑定后最终模型树数不符")
    device = base.configure_prediction_device(booster, "semantic168/final_seed42")
    model_receipt["reload_prediction_device"] = device
    model_receipt["reload_serialized_identity"] = reload_serialized_identity_receipt(
        booster
    )
    return booster, model_receipt, threshold_receipt


def wilson_interval(successes: int, population: int) -> list[float]:
    z = 1.959963984540054
    proportion = successes / population
    denominator = 1.0 + z * z / population
    center = (proportion + z * z / (2.0 * population)) / denominator
    radius = (
        z
        * math.sqrt(
            proportion * (1.0 - proportion) / population
            + z * z / (4.0 * population * population)
        )
        / denominator
    )
    return [max(0.0, center - radius), min(1.0, center + radius)]


def exact_mcnemar_pvalue(left_only: int, right_only: int) -> float:
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0
    lower = min(left_only, right_only)
    probability = sum(math.comb(discordant, k) for k in range(lower + 1)) / 2**discordant
    return min(1.0, 2.0 * probability)


def paired_difference(
    labels: np.ndarray,
    candidate: np.ndarray,
    reference: np.ndarray,
    label: int,
) -> dict[str, Any]:
    mask = labels == label
    candidate_only = int(np.count_nonzero(candidate[mask] & ~reference[mask]))
    reference_only = int(np.count_nonzero(reference[mask] & ~candidate[mask]))
    population = int(mask.sum())
    difference = (candidate_only - reference_only) / population
    variance = max(
        0.0,
        (candidate_only + reference_only) / population - difference * difference,
    ) / population
    radius = 1.959963984540054 * math.sqrt(variance)
    return {
        "population": population,
        "candidate_only": candidate_only,
        "reference_only": reference_only,
        "difference": difference,
        "paired_wald_95_interval": [difference - radius, difference + radius],
        "exact_mcnemar_two_sided_p": exact_mcnemar_pvalue(
            candidate_only, reference_only
        ),
    }


def arm_counts(labels: np.ndarray, alerts: np.ndarray) -> dict[str, Any]:
    result = path_q0.counts(labels, alerts)
    result["entity_fpr_wilson_95"] = wilson_interval(
        int(result["false_positive_entities"]), int(result["negative_entities"])
    )
    result["detection_rate_wilson_95"] = wilson_interval(
        int(result["detected_positive_entities"]), int(result["positive_entities"])
    )
    return result


def distribution(values: np.ndarray) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        return {"count": 0, "min": None, "median": None, "mean": None, "p95": None, "max": None}
    return {
        "count": int(len(finite)),
        "min": float(finite.min()),
        "median": float(np.median(finite)),
        "mean": float(finite.mean()),
        "p95": float(np.percentile(finite, 95)),
        "max": float(finite.max()),
    }


def integer_budget_curve(
    calibration: dict[str, Any],
    evaluation: dict[str, Any],
    evaluation_labels: np.ndarray,
    maximum_budget: int,
) -> list[dict[str, Any]]:
    first_sorted = np.sort(np.asarray(calibration["first_scores"], np.float64))
    path_sorted = np.sort(np.asarray(calibration["path_max"], np.float64))
    level_sorted = []
    for column in range(calibration["level_scores"].shape[1]):
        values = np.asarray(calibration["level_scores"][:, column], np.float64)
        level_sorted.append(np.sort(values[np.isfinite(values)]))
    population = len(first_sorted)
    curve: list[dict[str, Any]] = []
    started = time.time()
    for budget in range(maximum_budget + 1):
        rate = budget / population
        b0 = empirical_threshold_sorted(first_sorted, budget)["threshold"]
        b3 = empirical_threshold_sorted(path_sorted, budget)["threshold"]
        b2_receipt = tong_threshold_sorted(first_sorted, rate, DELTA)
        m1_receipt = tong_threshold_sorted(path_sorted, rate, DELTA)
        b2 = math.inf if not b2_receipt["available"] else b2_receipt["threshold"]
        m1 = math.inf if not m1_receipt["available"] else m1_receipt["threshold"]
        b4_values, _ = b4_thresholds_sorted(level_sorted, rate)
        b4_alert = np.any(
            evaluation["level_scores"] > b4_values[None, :], axis=1
        )
        alerts = {
            "B0_first_empirical": evaluation["first_scores"] > b0,
            "B1_all_fixed_empirical": evaluation["path_max"] > b0,
            "B2_first_tong": evaluation["first_scores"] > b2,
            "B3_path_max_empirical": evaluation["path_max"] > b3,
            "B4_summable_exposure_budget": b4_alert,
            "M1_path_max_tong": evaluation["path_max"] > m1,
        }
        curve.append(
            {
                "allowed_calibration_false_entities": budget,
                "q_b": rate,
                "tong_available": {
                    "B2": bool(b2_receipt["available"]),
                    "M1": bool(m1_receipt["available"]),
                },
                "arms": {
                    name: path_q0.counts(evaluation_labels, values)
                    for name, values in alerts.items()
                },
            }
        )
        beat("完整整数预算曲线", budget + 1, maximum_budget + 1, started)
    return curve


def host_peak_bytes() -> int:
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def main() -> int:
    args = parse_args()
    try:
        if not args.config.is_file():
            raise base.InputContractError(f"配置缺失：{args.config}")
        config = load_json(args.config)
        validate_config(config)
        if args.validate_config:
            print("CH4_PATH_MAX_TONG_FINAL_MODEL_SOURCE_CONFIG_VALID", flush=True)
            return 0

        parent = validate_parent_contract(args)
        array_receipts = base.hash_allowed_arrays()
        if args.validate_inputs:
            print("CH4_PATH_MAX_TONG_FINAL_MODEL_SOURCE_INPUTS_VALID", flush=True)
            return 0
        protected = (
            MODEL_NAME,
            MODEL_RECEIPT_NAME,
            THRESHOLD_RECEIPT_NAME,
            RESULT_NAME,
            "input_receipt.json",
            "resource_receipt.json",
            "swanlab_receipt.json",
            "manifest.json",
        )
        if any((args.out / name).exists() for name in protected):
            raise base.InputContractError(f"同名生产制品已存在，禁止覆盖：{args.out}")
        args.out.mkdir(parents=True, exist_ok=True)
        started = time.time()
        script_sha = base.sha256_file(Path(__file__).resolve())
        config_sha = base.sha256_file(args.config.resolve())

        log("阶段一：只读加载 LSPR23 并执行覆盖、实体、时间和确定性角色门")
        labels = base.guarded_source_load("y23")
        indices = base.guarded_source_load("I23")
        masks = base.guarded_source_load("M23")
        sequence_entities = base.guarded_source_load("E23")
        flow_entities = base.guarded_source_load("ent23")
        flow_times = base.guarded_source_load("t23_flow")
        structure = base.scan_source_structure(
            labels, indices, masks, sequence_entities, flow_entities, flow_times
        )
        entity_labels = np.asarray(structure["entity_labels"], np.int8)
        entity_flow_counts = np.asarray(structure["entity_flow_counts"], np.int64)
        fold_of_entity = base.make_folds(entity_labels, 42)
        fold_sha = base.sha256_array(fold_of_entity)
        if fold_sha != config["fold_contract"]["fold_assignment_sha256"]:
            raise base.InputContractError("实体三折 SHA-256 不符")
        fold_stats = base.fold_statistics(
            fold_of_entity,
            entity_labels,
            entity_flow_counts,
            np.asarray(structure["entity_positive_flow_counts"]),
        )
        if fold_stats != parent["fold_stat"]:
            raise base.InputContractError("实体三折统计与父冻结选择不符")
        halves = path_q0.make_inner_halves(fold_of_entity, entity_labels, 42)
        training_entities = np.flatnonzero(fold_of_entity != HOLDOUT_FOLD)
        calibration_entities = np.flatnonzero(
            (fold_of_entity == HOLDOUT_FOLD) & (halves == CALIBRATION_HALF)
        )
        calibration_negative_entities = calibration_entities[
            entity_labels[calibration_entities] == 0
        ]
        evaluation_entities = np.flatnonzero(
            (fold_of_entity == HOLDOUT_FOLD) & (halves == EVALUATION_HALF)
        )
        manifests: dict[str, Any] = {}
        manifest_hashes: dict[str, str] = {}
        for role, ids in (
            ("training_fold0_plus_fold1", training_entities),
            ("calibration_fold2_half1_all", calibration_entities),
            ("calibration_fold2_half1_negative", calibration_negative_entities),
            ("evaluation_fold2_half0", evaluation_entities),
        ):
            manifests[role], manifest_hashes[role] = role_manifest(
                role, ids, entity_labels
            )
        expected_counts = config["fold_contract"]
        if (
            manifests["training_fold0_plus_fold1"]["entity_count"]
            != expected_counts["training_entities"]
            or manifests["training_fold0_plus_fold1"]["negative_entity_count"]
            != expected_counts["training_negative_entities"]
            or manifests["training_fold0_plus_fold1"]["positive_entity_count"]
            != expected_counts["training_positive_entities"]
            or manifests["calibration_fold2_half1_all"]["entity_count"]
            != expected_counts["calibration_entities"]
            or manifests["calibration_fold2_half1_negative"]["entity_count"]
            != expected_counts["calibration_negative_entities"]
            or manifests["evaluation_fold2_half0"]["entity_count"]
            != expected_counts["evaluation_entities"]
            or manifests["evaluation_fold2_half0"]["negative_entity_count"]
            != expected_counts["evaluation_negative_entities"]
            or manifests["evaluation_fold2_half0"]["positive_entity_count"]
            != expected_counts["evaluation_positive_entities"]
        ):
            raise base.InputContractError("训练、校准或评价实体容量不符")
        if (
            np.intersect1d(training_entities, calibration_entities).size
            or np.intersect1d(training_entities, evaluation_entities).size
            or np.intersect1d(calibration_entities, evaluation_entities).size
        ):
            raise base.InputContractError("训练、校准与评价实体不互斥")

        log("阶段二：按父冻结语义构造 semantic168")
        semantic = base.build_semantic_matrix(base.CACHE / "X23.npy", indices, masks)
        training_rows = np.flatnonzero(fold_of_entity[flow_entities] != HOLDOUT_FOLD)
        expected_training_flows = int(entity_flow_counts[training_entities].sum())
        if len(training_rows) != expected_training_flows:
            raise base.InputContractError("训练流数与训练实体清单不符")

        log("阶段三：复用 rerun1 已封印的最终模型与阈值，不重复训练")
        import torch
        import xgboost as xgb

        if xgb.__version__ != "3.2.0" or xgb.build_info().get("USE_CUDA") is not True:
            raise base.InputContractError(
                f"XGBoost 环境不符：version={xgb.__version__} "
                f"USE_CUDA={xgb.build_info().get('USE_CUDA')}"
            )
        del training_rows
        if not torch.cuda.is_available():
            raise base.InputContractError("CUDA 不可用，拒绝 CPU 回退")
        resume_root = args.resume_run_root.resolve()
        if resume_root.name != SOURCE_RUN_ID:
            raise base.InputContractError("断点恢复源运行身份不符")
        source_model_path = resume_root / MODEL_NAME
        source_model_receipt_path = resume_root / MODEL_RECEIPT_NAME
        source_threshold_receipt_path = resume_root / THRESHOLD_RECEIPT_NAME
        booster, source_model_receipt, source_threshold_receipt = load_bound_model(
            xgb,
            source_model_path,
            source_model_receipt_path,
            source_threshold_receipt_path,
            expected_run_id=SOURCE_RUN_ID,
        )
        score_contract_sha = base.canonical_sha256(config["score_contract"])
        path_contract_sha = base.canonical_sha256(config["entity_path_contract"])
        expected_bindings = {
            "training_entity_manifest_sha256": manifest_hashes[
                "training_fold0_plus_fold1"
            ],
            "calibration_entity_manifest_sha256": manifest_hashes[
                "calibration_fold2_half1_negative"
            ],
            "score_contract_sha256": score_contract_sha,
            "entity_path_contract_sha256": path_contract_sha,
        }
        for field, expected in expected_bindings.items():
            if source_model_receipt.get(field) != expected:
                raise base.InputContractError(f"断点模型绑定字段不符：{field}")
        args.out.mkdir(parents=True, exist_ok=True)
        model_path = args.out / MODEL_NAME
        model_receipt_path = args.out / MODEL_RECEIPT_NAME
        threshold_receipt_path = args.out / THRESHOLD_RECEIPT_NAME
        shutil.copy2(source_model_path, model_path)
        shutil.copy2(source_model_receipt_path, model_receipt_path)
        shutil.copy2(source_threshold_receipt_path, threshold_receipt_path)
        model_file_receipt = {
            "sha256": base.sha256_file(model_path),
            "bytes": model_path.stat().st_size,
            "num_boost_round": base.N_TREE,
        }
        training_receipt = {
            "training_executed": False,
            "reused_model": True,
            "source_run_id": SOURCE_RUN_ID,
            "source_model_sha256": model_file_receipt["sha256"],
            "source_effective_training_receipt": source_model_receipt[
                "effective_training_receipt"
            ],
        }

        log("阶段四：重算折2/half1聚合曲线，阈值仍使用 rerun1 封印值")
        max_b4_level = maximum_b4_level(
            len(calibration_negative_entities), Q
        )
        calibration = score_role(
            booster,
            semantic,
            indices,
            masks,
            sequence_entities,
            flow_times,
            calibration_negative_entities,
            entity_flow_counts,
            int(config["sequence_batch"]),
            max_b4_level,
            "折2/half1良性路径校准",
        )
        allowed_main = int(math.floor(Q * len(calibration_negative_entities)))
        arms = source_threshold_receipt["arm_thresholds"]
        b0_receipt = arms["B0_first_empirical"]
        b2_receipt = arms["B2_first_tong"]
        b3_receipt = arms["B3_path_max_empirical"]
        b4_receipts = arms["B4_summable_exposure_budget"]["levels"]
        b4_values = np.full(max_b4_level, np.inf, np.float64)
        for level_receipt in b4_receipts:
            if level_receipt["available"]:
                b4_values[level_receipt["exposure_index"] - 1] = level_receipt[
                    "threshold"
                ]
        m1_receipt = arms["M1_path_max_tong"]

        log("阶段五：重新读取模型与阈值收据并执行强绑定门")
        del booster
        gc.collect()
        torch.cuda.empty_cache()
        booster, reloaded_model_receipt, bound_threshold = load_bound_model(
            xgb,
            model_path,
            model_receipt_path,
            threshold_receipt_path,
            expected_run_id=SOURCE_RUN_ID,
        )
        alert_thresholds = {
            "B0_first_empirical": b0_receipt["threshold"],
            "B1_all_fixed_empirical": b0_receipt["threshold"],
            "B2_first_tong": b2_receipt["threshold"],
            "B3_path_max_empirical": b3_receipt["threshold"],
            "B4_summable_exposure_budget": b4_values,
            "M1_path_max_tong": bound_threshold["threshold"],
        }

        log("阶段六：封印后只在折2/half0评价六臂")
        evaluation = score_role(
            booster,
            semantic,
            indices,
            masks,
            sequence_entities,
            flow_times,
            evaluation_entities,
            entity_flow_counts,
            int(config["sequence_batch"]),
            max_b4_level,
            "折2/half0六臂独立评价",
            alert_thresholds,
        )
        evaluation_labels = entity_labels[evaluation_entities]
        alerts = {
            name: evaluation["first_alert_exposure"][name] > 0 for name in METHODS
        }
        metrics = {name: arm_counts(evaluation_labels, alert) for name, alert in alerts.items()}
        comparisons: dict[str, Any] = {}
        for reference, candidate in (
            ("B0_first_empirical", "B1_all_fixed_empirical"),
            ("B0_first_empirical", "M1_path_max_tong"),
            ("B2_first_tong", "M1_path_max_tong"),
            ("B3_path_max_empirical", "M1_path_max_tong"),
            ("B4_summable_exposure_budget", "M1_path_max_tong"),
            ("B0_first_empirical", "B2_first_tong"),
        ):
            key = f"{candidate}_minus_{reference}"
            comparisons[key] = {
                "entity_fpr": paired_difference(
                    evaluation_labels, alerts[candidate], alerts[reference], 0
                ),
                "detection_rate": paired_difference(
                    evaluation_labels, alerts[candidate], alerts[reference], 1
                ),
            }
        primary_pair = comparisons[
            "M1_path_max_tong_minus_B0_first_empirical"
        ]["detection_rate"]
        certificate_valid = (
            m1_receipt["violation_bound"] <= DELTA
            and m1_receipt["previous_violation_bound"] > DELTA
        )
        qualified = (
            certificate_valid
            and metrics["M1_path_max_tong"]["entity_fpr"] <= Q
            and primary_pair["difference"] > 0.0
            and primary_pair["paired_wald_95_interval"][0] > 0.0
        )
        late_positive = (
            (evaluation_labels == 1)
            & alerts["M1_path_max_tong"]
            & ~alerts["B0_first_empirical"]
        )
        late_positions = evaluation["first_alert_exposure"]["M1_path_max_tong"][
            late_positive
        ]
        late_delays = (
            evaluation["first_alert_time"]["M1_path_max_tong"][late_positive]
            - np.asarray(structure["first_time"])[evaluation_entities][late_positive]
        )

        log("阶段七：生成全部可达整数预算点的描述性六臂前沿")
        budget_curve = integer_budget_curve(
            calibration,
            evaluation,
            evaluation_labels,
            allowed_main,
        )
        result = {
            "schema_version": "ch4-xgb-path-max-tong-final-model-source-results-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "source_year": "LSPR23",
            "seed": 42,
            "evidence_boundary": {
                "single_seed_source_year_only": True,
                "training_randomness_not_estimated": True,
                "cross_year_claim": False,
                "target_year_arrays_read": 0,
            },
            "roles": manifests,
            "model_binding": {
                "model_sha256": model_file_receipt["sha256"],
                "model_receipt_sha256": reloaded_model_receipt["receipt_sha256"],
                "threshold_receipt_sha256": bound_threshold["receipt_sha256"],
                "binding_valid": True,
            },
            "thresholds": bound_threshold["arm_thresholds"],
            "metrics": metrics,
            "paired_comparisons": comparisons,
            "late_positive_detection": {
                "entity_count": int(late_positive.sum()),
                "first_alert_exposure": distribution(late_positions),
                "delay_from_first_exposure": distribution(late_delays),
            },
            "alert_accounting": {
                name: {
                    "alerted_entities": int(alerts[name].sum()),
                    "crossing_exposures": int(evaluation["crossing_counts"][name]),
                    "suppressed_repeated_crossings": int(
                        evaluation["crossing_counts"][name] - alerts[name].sum()
                    ),
                }
                for name in METHODS
            },
            "integer_budget_curve": {
                "calibration_negative_entities": len(calibration_negative_entities),
                "minimum_allowed_count": 0,
                "maximum_allowed_count": allowed_main,
                "points": budget_curve,
                "confirmatory_q": Q,
                "curve_is_descriptive": True,
            },
            "mechanical_verdict": {
                "qualified": qualified,
                "m1_certificate_valid": certificate_valid,
                "verdict": (
                    "MECHANISM1_FINAL_SINGLE_MODEL_SOURCE_SEED42_SUPPORTED"
                    if qualified
                    else "MECHANISM1_FINAL_SINGLE_MODEL_SOURCE_SEED42_NOT_SUPPORTED"
                ),
                "rule": config["qualification_rule"],
                "claim_boundary": (
                    "只裁决种子42的LSPR23最终单模型源年支持，不外推训练随机性或跨年度"
                ),
            },
            "integrity": {
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
                "training_runs_started": 0,
                "models_saved": 0,
                "models_reused": 1,
                "resume_source_run_id": SOURCE_RUN_ID,
                "calibration_scored_flows": calibration["scored_flow_count"],
                "evaluation_scored_flows": evaluation["scored_flow_count"],
                "target_year_arrays_read": 0,
                "per_flow_scores_persisted": 0,
                "per_entity_scores_persisted": 0,
                "entity_ids_persisted": 0,
            },
        }
        result_path = args.out / RESULT_NAME
        atomic_json(result_path, result)

        input_path = args.out / "input_receipt.json"
        atomic_json(
            input_path,
            {
                "schema_version": "ch4-xgb-path-max-tong-final-model-input-v1",
                "run_id": RUN_ID,
                "script_sha256": script_sha,
                "config_sha256": config_sha,
                "parent": parent,
                "arrays": array_receipts,
                "fold_assignment_sha256": fold_sha,
                "half_assignment_sha256": base.sha256_array(halves),
                "role_manifests": manifests,
                "role_manifest_sha256": manifest_hashes,
                "score_contract_sha256": score_contract_sha,
                "entity_path_contract_sha256": path_contract_sha,
                "target_year_arrays_read": 0,
                "training_runs_started": 0,
                "resume_source_run_id": SOURCE_RUN_ID,
            },
        )
        resource_path = args.out / "resource_receipt.json"
        atomic_json(
            resource_path,
            {
                "schema_version": "ch4-xgb-path-max-tong-final-model-resource-v1",
                "run_id": RUN_ID,
                "wall_seconds": time.time() - started,
                "peak_host_rss_bytes": host_peak_bytes(),
                "cuda_device": torch.cuda.get_device_name(0),
                "cuda_peak_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
                "cuda_peak_reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
                "model_bytes": model_path.stat().st_size,
                "training": training_receipt,
                "calibration": {
                    "wall_seconds": calibration["wall_seconds"],
                    "prediction_seconds": calibration["prediction_seconds"],
                    "control_update_seconds": calibration["control_update_seconds"],
                },
                "evaluation": {
                    "wall_seconds": evaluation["wall_seconds"],
                    "prediction_seconds": evaluation["prediction_seconds"],
                    "control_update_seconds": evaluation["control_update_seconds"],
                },
                "m1_state_bytes_per_active_entity_lower_bound": 33,
                "m1_state_fields": config["entity_path_contract"]["state"],
            },
        )

        log("阶段八：仅上传聚合指标到已授权 SwanLab 目的地")
        import swanlab

        tracking = config["tracking"]
        swanlab.init(
            workspace=tracking["workspace"],
            project=tracking["project"],
            name=RUN_ID,
            config={
                "seed": 42,
                "source_year": "LSPR23",
                "methods": list(METHODS),
                "target_year_arrays_read": 0,
            },
        )
        metric_payload: dict[str, int | float] = {
            "source/qualified": int(qualified),
            "source/m1_certificate_valid": int(certificate_valid),
        }
        for name, values in metrics.items():
            metric_payload[f"source/{name}/entity_fpr"] = float(values["entity_fpr"])
            metric_payload[f"source/{name}/detection_rate"] = float(
                values["detection_rate"]
            )
            metric_payload[f"source/{name}/false_positive_entities"] = int(
                values["false_positive_entities"]
            )
            metric_payload[f"source/{name}/detected_positive_entities"] = int(
                values["detected_positive_entities"]
            )
        swanlab.log(metric_payload, step=0)
        swanlab.finish()
        swanlab_path = args.out / "swanlab_receipt.json"
        atomic_json(
            swanlab_path,
            {
                "schema_version": "ch4-xgb-path-max-tong-final-model-swanlab-v1",
                "completed": True,
                "workspace": tracking["workspace"],
                "project": tracking["project"],
                "mode": tracking["mode"],
                "aggregate_only": True,
                "metric_keys": sorted(metric_payload),
            },
        )

        manifest_names = (
            MODEL_NAME,
            MODEL_RECEIPT_NAME,
            THRESHOLD_RECEIPT_NAME,
            RESULT_NAME,
            "input_receipt.json",
            "resource_receipt.json",
            "swanlab_receipt.json",
        )
        manifest = {
            "schema_version": "ch4-xgb-path-max-tong-final-model-manifest-v1",
            "run_id": RUN_ID,
            "script_sha256": script_sha,
            "config_sha256": config_sha,
            "target_year_arrays_read": 0,
            "training_runs_started": 0,
            "models_saved": 0,
            "models_reused": 1,
            "resume_source_run_id": SOURCE_RUN_ID,
            "per_flow_scores_persisted": 0,
            "per_entity_scores_persisted": 0,
            "files": {},
        }
        for name in manifest_names:
            path = args.out / name
            if not path.is_file() or path.stat().st_size <= 0:
                raise base.InputContractError(f"必需制品缺失：{path}")
            manifest["files"][name] = {
                "bytes": path.stat().st_size,
                "sha256": base.sha256_file(path),
            }
        atomic_json(args.out / "manifest.json", manifest)
        log(
            "最终单模型源年实验完成："
            f"M1 FPR={metrics['M1_path_max_tong']['entity_fpr']:.10f} "
            f"DR={metrics['M1_path_max_tong']['detection_rate']:.10f} "
            f"verdict={result['mechanical_verdict']['verdict']}"
        )
        return 0
    except base.InputContractError as error:
        print(f"INVALID_INPUT_CONTRACT: {error}", file=sys.stderr, flush=True)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
