#!/usr/bin/env python3
"""用源年折外实体路径最大统计量执行零训练 Q0。"""

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

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch4_xgb_entity_exposure_lesion_source_diagnostic as base  # noqa: E402
from ch3_xgb_cpa_elp_eval_continuation import (  # noqa: E402
    AUTHORIZED_SWANLAB_PROJECT,
    AUTHORIZED_SWANLAB_WORKSPACE,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-entity-path-max-tong-same-model-q0-seed42-v1"
DISPLAY_NAME = "Tong有限样本同模型实体路径最大风险源年零训练Q0"
CONFIG_NAME = "ch4-xgb-entity-path-max-np-q0-seed42-v1.json"
BASE_CONFIG_NAME = "ch4-xgb-entity-exposure-lesion-source-diagnostic-seed42-v1.json"
SOURCE_THRESHOLD = 3.660049696918577e-05
Q = 0.04
GLOBAL_VIOLATION_PROBABILITY = 0.05
SIMULTANEOUS_ROUND_COUNT = 6
ROUND_VIOLATION_PROBABILITY = (
    GLOBAL_VIOLATION_PROBABILITY / SIMULTANEOUS_ROUND_COUNT
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
        "--out", type=Path, default=ROOT / "runs/diagnostics" / RUN_ID
    )
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
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
        "schema_version": "ch4-xgb-entity-path-max-tong-same-model-q0-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "source_year": "LSPR23",
        "seed": 42,
        "entity_fpr_budget": Q,
        "global_violation_probability": GLOBAL_VIOLATION_PROBABILITY,
        "simultaneous_round_count": SIMULTANEOUS_ROUND_COUNT,
        "per_round_violation_probability": ROUND_VIOLATION_PROBABILITY,
        "comparison_operator": ">",
        "zero_training": True,
        "target_year_arrays_read": 0,
        "oof_models_loaded": 3,
        "sequence_batch": 2048,
        "methods": [
            "B0_first",
            "B1_all_source",
            "M1_path_max_tong_same_model_crosscal",
        ],
        "deferred_pressure_control": "A1_alpha_j=q/[j(j+1)]",
        "qualification_rule": (
            "all(v(k*)<=delta/6) AND FPR(M1)<=0.04 AND DR(M1)>DR(B0)"
        ),
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise base.InputContractError(f"配置字段不符：{key}")
    if config.get("tracking") != {
        "workspace": AUTHORIZED_SWANLAB_WORKSPACE,
        "project": AUTHORIZED_SWANLAB_PROJECT,
        "mode": "online",
        "aggregate_only": True,
    }:
        raise base.InputContractError("SwanLab 目的地或聚合边界不符")


def binomial_upper_tail(n: int, k: int, success_probability: float) -> float:
    """计算二项分布上尾；搜索区间从均值开始，避免尾项下溢。"""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    log_term = (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
        + k * math.log(success_probability)
        + (n - k) * math.log1p(-success_probability)
    )
    term = math.exp(log_term)
    tail = term
    odds = success_probability / (1.0 - success_probability)
    for j in range(k, n):
        term *= ((n - j) / (j + 1)) * odds
        tail += term
    return min(1.0, tail)


def tong_np_order_threshold(
    values: np.ndarray, rate: float, violation_probability: float
) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    if len(finite) == 0 or not np.isfinite(finite).all():
        raise base.InputContractError("路径最大阈值缺少有限良性实体")
    n = len(finite)
    success_probability = 1.0 - rate
    low = max(1, int(math.floor(n * success_probability)))
    high = n
    while low < high:
        middle = (low + high) // 2
        if (
            binomial_upper_tail(n, middle, success_probability)
            <= violation_probability
        ):
            high = middle
        else:
            low = middle + 1
    rank_one_based = low
    violation_bound = binomial_upper_tail(
        n, rank_one_based, success_probability
    )
    previous_violation_bound = binomial_upper_tail(
        n, rank_one_based - 1, success_probability
    )
    if violation_bound > violation_probability:
        raise base.InputContractError("Tong 次序统计量未满足逐方向违约概率")
    ordered = np.sort(finite)
    index = rank_one_based - 1
    threshold = float(ordered[index])
    selected = int((finite > threshold).sum())
    return {
        "threshold": threshold,
        "population": n,
        "entity_fpr_budget": rate,
        "violation_probability": violation_probability,
        "rank_one_based": rank_one_based,
        "violation_bound": violation_bound,
        "previous_violation_bound": previous_violation_bound,
        "strictly_above_count": selected,
        "empirical_fpr": selected / n,
        "order_statistic_index_zero_based": index,
        "boundary_tie_count": int((finite == threshold).sum()),
        "comparison_operator": ">",
    }


def update_paths(
    entities: np.ndarray,
    raw_scores: np.ndarray,
    cumulative_sum: np.ndarray,
    exposure_count: np.ndarray,
    first_scores: np.ndarray,
    path_max: np.ndarray,
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
        if prior == 0:
            first_scores[entity] = scores[0]
        path_max[entity] = max(float(path_max[entity]), float(running.max()))
        cumulative_sum[entity] = cumulative[-1]
        exposure_count[entity] = prior + len(scores)


def score_entity_paths(
    xgb_module: Any,
    torch_module: Any,
    matrix: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
    fold_of_entity: np.ndarray,
    parent_root: Path,
    seal: dict[str, Any],
    base_config: dict[str, Any],
) -> dict[str, Any]:
    cumulative_sum = np.zeros(base.N_ENTITY, np.float64)
    exposure_count = np.zeros(base.N_ENTITY, np.int64)
    first_scores = np.full(base.N_ENTITY, np.nan, np.float32)
    path_max = np.full(base.N_ENTITY, -np.inf, np.float32)
    seen = np.zeros(base.N_FLOW, np.bool_)
    receipts: list[dict[str, Any]] = []
    sealed = {item["filename"]: item for item in seal["source_model_receipts"]}
    batch_size = int(base_config["sequence_batch"])
    for fold in range(base.N_FOLD):
        name = f"model_oof_semantic168_fold{fold}.json"
        booster, receipt = base.load_booster(
            xgb_module, parent_root / name, fold, sealed[name]["sha256"]
        )
        base.gpu_guard(
            torch_module,
            float(base_config["resource_contract"]["runtime_gpu_floor_gib"]),
            f"semantic168/fold{fold}/路径推理前",
        )
        selected_sequences = np.flatnonzero(fold_of_entity[sequence_entities] == fold)
        started = time.time()
        predicted = 0
        for start in range(0, len(selected_sequences), batch_size):
            selected = selected_sequences[start : start + batch_size]
            index_block = np.asarray(indices[selected])
            valid = np.asarray(masks[selected]) > 0
            rows = np.asarray(index_block[valid], np.int64)
            entities = np.broadcast_to(
                np.asarray(sequence_entities[selected], np.int64)[:, None], valid.shape
            )[valid]
            if seen[rows].any():
                raise base.InputContractError("OOF 路径推理重复覆盖流")
            seen[rows] = True
            scores = np.asarray(booster.inplace_predict(matrix[rows]), np.float32)
            if scores.shape != (len(rows),) or not np.isfinite(scores).all():
                raise base.InputContractError("OOF 路径分数异常")
            update_paths(
                entities,
                scores,
                cumulative_sum,
                exposure_count,
                first_scores,
                path_max,
            )
            predicted += len(rows)
            base.beat(
                f"semantic168/fold{fold}/路径OOF",
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
        torch_module.cuda.empty_cache()
    if not seen.all() or int(exposure_count.sum()) != base.N_FLOW:
        raise base.InputContractError("三折路径推理未覆盖全部源年流")
    if not np.isfinite(first_scores).all() or not np.isfinite(path_max).all():
        raise base.InputContractError("实体首曝或路径最大分数未完整覆盖")
    return {
        "first_scores": first_scores,
        "path_max": path_max,
        "exposure_count": exposure_count,
        "model_receipts": receipts,
        "scored_flow_count": int(seen.sum()),
    }


def counts(labels: np.ndarray, alerts: np.ndarray) -> dict[str, int | float]:
    negative = labels == 0
    positive = labels == 1
    fp = int(np.count_nonzero(alerts & negative))
    tp = int(np.count_nonzero(alerts & positive))
    n_negative = int(negative.sum())
    n_positive = int(positive.sum())
    return {
        "negative_entities": n_negative,
        "positive_entities": n_positive,
        "false_positive_entities": fp,
        "detected_positive_entities": tp,
        "entity_fpr": fp / n_negative,
        "detection_rate": tp / n_positive,
    }


def add_counts(total: dict[str, int], metric: dict[str, int | float]) -> None:
    for key in (
        "negative_entities",
        "positive_entities",
        "false_positive_entities",
        "detected_positive_entities",
    ):
        total[key] = total.get(key, 0) + int(metric[key])


def pooled(total: dict[str, int]) -> dict[str, int | float]:
    return {
        **total,
        "entity_fpr": total["false_positive_entities"] / total["negative_entities"],
        "detection_rate": total["detected_positive_entities"] / total["positive_entities"],
    }


def make_inner_halves(
    fold_of_entity: np.ndarray, entity_labels: np.ndarray, seed: int
) -> np.ndarray:
    """在每个折模型自己的留出实体内，按类别稳定等分校准与评价实体。"""
    halves = np.full(len(entity_labels), -1, np.int8)
    rng = np.random.RandomState(seed)
    for fold in range(base.N_FOLD):
        for label in (0, 1):
            members = np.flatnonzero(
                (fold_of_entity == fold) & (entity_labels == label)
            )
            shuffled = members[rng.permutation(len(members))]
            halves[shuffled] = np.arange(len(shuffled), dtype=np.int64) % 2
    if np.any(halves < 0):
        raise base.InputContractError("同模型交叉校准未覆盖全部实体")
    return halves


def main() -> int:
    args = parse_args()
    try:
        if not args.config.is_file():
            raise base.InputContractError(f"配置缺失：{args.config}")
        config = load_json(args.config)
        validate_config(config)
        if args.validate_config:
            print("CH4_ENTITY_PATH_MAX_NP_CONFIG_VALID", flush=True)
            return 0

        base_config_path = ROOT / "configs" / BASE_CONFIG_NAME
        base_config = load_json(base_config_path)
        base.validate_config(base_config)
        parent_args = argparse.Namespace(
            config=base_config_path,
            parent_run_root=args.parent_run_root,
            parent_config=args.parent_config,
            threshold_seal=None,
            parent_recovery_proof=None,
            # 父校验器仍要求其自身诊断身份；这里只借用父制品校验，不写入该路径。
            out=args.out.parent / base.RUN_ID,
        )
        base.resolve_paths(parent_args, base_config)
        seal = base.validate_threshold_seal(parent_args.threshold_seal.resolve(), base_config)
        parent = base.validate_parent(parent_args, base_config, seal)
        array_receipts = base.hash_allowed_arrays()
        if args.validate_inputs:
            print("CH4_ENTITY_PATH_MAX_NP_INPUTS_VALID", flush=True)
            return 0
        if args.out.exists():
            raise base.InputContractError(f"运行目录已存在，禁止覆盖：{args.out}")
        args.out.mkdir(parents=True)
        started = time.time()

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
        fold_of_entity = base.make_folds(entity_labels, int(config["seed"]))
        fold_sha = base.sha256_array(fold_of_entity)
        if fold_sha != base_config["source_threshold_contract"]["fold_assignment_sha256"]:
            raise base.InputContractError("实体折号哈希不符")
        fold_stats = base.fold_statistics(
            fold_of_entity,
            entity_labels,
            np.asarray(structure["entity_flow_counts"]),
            np.asarray(structure["entity_positive_flow_counts"]),
        )
        if fold_stats != parent["selection"].get("fold_stat"):
            raise base.InputContractError("实体三折统计与父收据不符")

        base.log("构造 semantic168 并执行三折全路径 OOF 推理")
        semantic = base.build_semantic_matrix(base.CACHE / "X23.npy", indices, masks)
        import torch
        import xgboost as xgb

        scored = score_entity_paths(
            xgb,
            torch,
            semantic,
            indices,
            masks,
            sequence_entities,
            fold_of_entity,
            args.parent_run_root,
            seal,
            base_config,
        )
        del semantic
        torch.cuda.empty_cache()

        inner_halves = make_inner_halves(
            fold_of_entity, entity_labels, int(config["seed"])
        )
        totals = {name: {} for name in config["methods"]}
        rounds: list[dict[str, Any]] = []
        for model_fold in range(base.N_FOLD):
            for calibration_half in (0, 1):
                evaluation_half = 1 - calibration_half
                calibration_negative = (
                    (fold_of_entity == model_fold)
                    & (inner_halves == calibration_half)
                    & (entity_labels == 0)
                )
                threshold = tong_np_order_threshold(
                    scored["path_max"][calibration_negative],
                    Q,
                    ROUND_VIOLATION_PROBABILITY,
                )
                evaluation = (fold_of_entity == model_fold) & (
                    inner_halves == evaluation_half
                )
                evaluation_labels = entity_labels[evaluation]
                method_alerts = {
                    "B0_first": scored["first_scores"][evaluation]
                    > SOURCE_THRESHOLD,
                    "B1_all_source": scored["path_max"][evaluation]
                    > SOURCE_THRESHOLD,
                    "M1_path_max_tong_same_model_crosscal": scored["path_max"][
                        evaluation
                    ]
                    > threshold["threshold"],
                }
                metrics: dict[str, Any] = {}
                for name, alert in method_alerts.items():
                    metric = counts(evaluation_labels, alert)
                    metrics[name] = metric
                    add_counts(totals[name], metric)
                rounds.append(
                    {
                        "model_fold": model_fold,
                        "calibration_half": calibration_half,
                        "evaluation_half": evaluation_half,
                        "path_threshold_receipt": threshold,
                        "metrics": metrics,
                    }
                )
        aggregate = {name: pooled(total) for name, total in totals.items()}
        certificates_valid = all(
            item["path_threshold_receipt"]["violation_bound"]
            <= ROUND_VIOLATION_PROBABILITY
            for item in rounds
        )
        qualified = (
            certificates_valid
            and aggregate["M1_path_max_tong_same_model_crosscal"]["entity_fpr"]
            <= Q
            and aggregate["M1_path_max_tong_same_model_crosscal"]["detection_rate"]
            > aggregate["B0_first"]["detection_rate"]
        )
        verdict = (
            "MECHANISM1_PATH_MAX_TONG_Q0_QUALIFIED"
            if qualified
            else "MECHANISM1_PATH_MAX_TONG_Q0_REJECTED"
        )
        summary = {
            "schema_version": "ch4-xgb-entity-path-max-tong-same-model-summary-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "source_year": "LSPR23",
            "screening_only": True,
            "target_year_arrays_read": 0,
            "training_runs_started": 0,
            "comparison_operator": ">",
            "entity_fpr_budget": Q,
            "global_violation_probability": GLOBAL_VIOLATION_PROBABILITY,
            "simultaneous_round_count": SIMULTANEOUS_ROUND_COUNT,
            "per_round_violation_probability": ROUND_VIOLATION_PROBABILITY,
            "source_threshold": SOURCE_THRESHOLD,
            "rounds": rounds,
            "aggregate": aggregate,
            "root_cause_fix": (
                "校准与评价分数来自同一冻结折模型；每个留出折内按类别二分并交换角色"
            ),
            "finite_sample_contract": (
                "每个方向按 Tong 次序统计量控制实体路径最大分数；全局违约概率按六方向并合界分配"
            ),
            "deferred_pressure_control": config["deferred_pressure_control"],
            "mechanical_verdict": {
                "qualified": qualified,
                "all_certificates_valid": certificates_valid,
                "verdict": verdict,
                "rule": config["qualification_rule"],
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
                "scored_flow_count": scored["scored_flow_count"],
                "oof_models_loaded": len(scored["model_receipts"]),
                "per_flow_scores_persisted": 0,
                "per_entity_scores_persisted": 0,
            },
        }
        summary_path = args.out / "summary.json"
        atomic_json(summary_path, summary)
        input_path = args.out / "input_receipt.json"
        atomic_json(
            input_path,
            {
                "run_id": RUN_ID,
                "script_sha256": base.sha256_file(Path(__file__).resolve()),
                "config_sha256": base.sha256_file(args.config.resolve()),
                "parent": parent,
                "arrays": array_receipts,
                "fold_assignment_sha256": fold_sha,
                "source_model_receipts": scored["model_receipts"],
                "target_year_arrays_read": 0,
                "training_runs_started": 0,
            },
        )
        usage = resource.getrusage(resource.RUSAGE_SELF)
        resource_path = args.out / "resource_receipt.json"
        atomic_json(
            resource_path,
            {
                "wall_seconds": time.time() - started,
                "peak_rss_mib": usage.ru_maxrss / 1024.0,
                "peak_gpu_memory_mib": int(torch.cuda.max_memory_allocated() / 2**20),
            },
        )

        import swanlab

        tracking = config["tracking"]
        swanlab.init(
            workspace=tracking["workspace"],
            project=tracking["project"],
            name=RUN_ID,
            config={"seed": 42, "source_year": "LSPR23", "zero_training": True},
        )
        swanlab.log(
            {
                "B0/entity_fpr": aggregate["B0_first"]["entity_fpr"],
                "B0/detection_rate": aggregate["B0_first"]["detection_rate"],
                "B1/entity_fpr": aggregate["B1_all_source"]["entity_fpr"],
                "B1/detection_rate": aggregate["B1_all_source"]["detection_rate"],
                "M1/entity_fpr": aggregate[
                    "M1_path_max_tong_same_model_crosscal"
                ]["entity_fpr"],
                "M1/detection_rate": aggregate[
                    "M1_path_max_tong_same_model_crosscal"
                ]["detection_rate"],
                "qualified": int(qualified),
            },
            step=0,
        )
        swanlab.finish()
        manifest = {
            "run_id": RUN_ID,
            "target_year_arrays_read": 0,
            "training_runs_started": 0,
            "files": {},
        }
        for path in (summary_path, input_path, resource_path):
            manifest["files"][path.name] = {
                "bytes": path.stat().st_size,
                "sha256": base.sha256_file(path),
            }
        atomic_json(args.out / "manifest.json", manifest)
        atomic_json(
            args.out / "status.json",
            {"state": "finished", "stage": "complete", "exit_code": 0},
        )
        base.log(
            "Q0完成：M1 FPR="
            f"{aggregate['M1_path_max_tong_same_model_crosscal']['entity_fpr']:.10f} "
            "DR="
            f"{aggregate['M1_path_max_tong_same_model_crosscal']['detection_rate']:.10f} "
            f"verdict={verdict}"
        )
        return 0
    except base.InputContractError as error:
        print(f"INVALID_INPUT_CONTRACT: {error}", file=sys.stderr, flush=True)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
