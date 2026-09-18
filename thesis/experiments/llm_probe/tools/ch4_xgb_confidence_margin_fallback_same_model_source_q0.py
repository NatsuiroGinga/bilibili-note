#!/usr/bin/env python3
"""机制二同模型三分、风险余量阈值、零训练源年 Q0。"""

from __future__ import annotations

import argparse
import json
import math
import resource
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch4_xgb_confidence_fallback_same_model_source_q0 as prior  # noqa: E402

base = prior.base
ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-confidence-margin-fallback-same-model-source-q0-seed42-v1"
DISPLAY_NAME = "同模型三分风险余量有限样本确认与源阈值回退源年Q0"
CONFIG_NAME = (
    "ch4-xgb-confidence-margin-fallback-same-model-source-q0-seed42-v1.json"
)
GLOBAL_FAILURE_PROBABILITY = 0.05
DIRECTION_COUNT = 3
PER_DIRECTION_FAILURE_PROBABILITY = GLOBAL_FAILURE_PROBABILITY / DIRECTION_COUNT


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
        "--parent-recovery-proof",
        type=Path,
        default=(
            ROOT
            / "runs/recovery"
            / f"{base.PARENT_RUN_ID}-for-{base.PBC_RECOVERY_CONSUMER_ID}-v1"
            / base.PARENT_RECOVERY_FILENAME
        ),
    )
    parser.add_argument("--out", type=Path, default=ROOT / "runs/candidates" / RUN_ID)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_config(config: dict[str, Any]) -> None:
    expected = {
        "schema_version": (
            "ch4-xgb-confidence-margin-fallback-same-model-source-q0-v1"
        ),
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "seed": 42,
        "source_year_only": True,
        "zero_training": True,
        "base_adapter": "semantic168",
        "power_mean_p": 1.0,
        "observation_index": 1,
        "entity_fpr_budget": 0.04,
        "global_failure_probability": GLOBAL_FAILURE_PROBABILITY,
        "direction_count": DIRECTION_COUNT,
        "per_direction_failure_probability": PER_DIRECTION_FAILURE_PROBABILITY,
        "development_candidate_rule": "tong_one_sided_exact_upper_inverse",
        "same_model_inner_roles": ["development", "calibration", "holdout"],
        "comparison_operator": "strict_greater_than",
        "target_year_arrays_read": 0,
        "new_models_trained": 0,
        "predict_batch": 2_000_000,
    }
    for key, expected_value in expected.items():
        if config.get(key) != expected_value:
            raise SystemExit(f"风险余量 Q0 配置字段不符：{key}")
    if config.get("tracking") != {
        "workspace": base.AUTHORIZED_SWANLAB_WORKSPACE,
        "project": base.AUTHORIZED_SWANLAB_PROJECT,
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 目的地不符")


def maximum_allowed_false_positives(n: int, budget: float, delta: float) -> int:
    """反解满足单侧精确上界不超过预算的最大误报数。"""
    if n <= 0 or not 0.0 < budget < 1.0 or not 0.0 < delta < 1.0:
        return -1
    zero_upper = base.clopper_pearson_upper(0, n, delta)
    if zero_upper is None or zero_upper > budget:
        return -1

    low = 0
    high = n
    while low < high:
        middle = (low + high + 1) // 2
        upper = base.clopper_pearson_upper(middle, n, delta)
        if upper is not None and upper <= budget:
            low = middle
        else:
            high = middle - 1

    next_upper = (
        base.clopper_pearson_upper(low + 1, n, delta) if low < n else None
    )
    if next_upper is not None and next_upper <= budget:
        raise AssertionError("最大允许开发误报数反解不完整")
    return low


def risk_margin_threshold(
    values: np.ndarray, budget: float, delta: float
) -> dict[str, Any]:
    """按风险上界反解唯一严格阈值，并保持边界同分整体不告警。"""
    finite = np.asarray(values, np.float64)
    if len(finite) == 0 or not np.isfinite(finite).all():
        raise ValueError("风险余量阈值选择没有有限良性实体分数")
    n = int(len(finite))
    k_max = maximum_allowed_false_positives(n, budget, delta)
    if k_max < 0 or k_max >= n:
        raise ValueError("当前开发负实体数无法生成有限风险余量阈值")

    ordered = np.sort(finite, kind="stable")
    threshold_index = n - k_max - 1
    threshold = float(ordered[threshold_index])
    actual_false_positive = int((finite > threshold).sum())
    actual_upper = base.clopper_pearson_upper(actual_false_positive, n, delta)
    k_max_upper = base.clopper_pearson_upper(k_max, n, delta)
    if actual_false_positive > k_max:
        raise AssertionError("严格风险余量阈值拆分并列组或超过误报上限")
    if actual_upper is None or actual_upper > budget:
        raise AssertionError("开发风险余量阈值未满足单侧精确上界")
    if n == 16_716 and (k_max != 614 or threshold_index != 16_101):
        raise AssertionError("冻结样本量下的风险余量机械锚点不符")

    return {
        "threshold": threshold,
        "comparison_operator": ">",
        "development_negative_entities": n,
        "entity_fpr_budget": budget,
        "per_direction_failure_probability": delta,
        "maximum_allowed_development_false_positive_entities": k_max,
        "threshold_order": "ascending",
        "threshold_zero_based_index": threshold_index,
        "actual_development_false_positive_entities": actual_false_positive,
        "actual_development_empirical_fpr": actual_false_positive / n,
        "actual_development_clopper_pearson_upper": actual_upper,
        "k_max_clopper_pearson_upper": k_max_upper,
        "boundary_tie_count": int((finite == threshold).sum()),
    }


def main() -> int:
    args = parse_args()
    config = load_json(args.config)
    if not isinstance(config, dict):
        raise SystemExit("配置顶层必须是对象")
    validate_config(config)
    if args.validate_config:
        print("CONFIDENCE_MARGIN_SAME_MODEL_SOURCE_Q0_CONFIG_VALID", flush=True)
        return 0

    base_config_path = (
        ROOT / "configs/ch4-xgb-confidence-fallback-source-q0-seed42-v1.json"
    )
    base_config = load_json(base_config_path)
    base.validate_config(base_config)
    parent_args = argparse.Namespace(
        config=base_config_path,
        parent_run_root=args.parent_run_root,
        parent_config=args.parent_config,
        parent_recovery_proof=args.parent_recovery_proof,
        out=ROOT / "runs/candidates" / base.RUN_ID,
    )
    parent = base.validate_parent_and_inputs(parent_args, base_config)
    if args.validate_inputs:
        print("CONFIDENCE_MARGIN_SAME_MODEL_SOURCE_Q0_INPUTS_VALID", flush=True)
        return 0

    protected = (
        "aggregate-results.json",
        "source-threshold-seal.json",
        "target-candidate-seal.json",
        "manifest.json",
    )
    if any((args.out / name).exists() for name in protected):
        raise SystemExit(f"同名科学制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)

    started = time.time()
    base.log("加载 LSPR23 并重建实体折")
    raw_values = base.guarded_source_load("X23")
    labels = base.guarded_source_load("y23")
    sequence_entities = base.guarded_source_load("E23")
    indices = base.guarded_source_load("I23")
    masks = base.guarded_source_load("M23")
    structure = base.scan_source_structure(labels, indices, masks, sequence_entities)
    entity_labels = np.asarray(structure["entity_labels"], np.int8)
    fold_of_entity = base.make_folds(entity_labels, int(config["seed"]))
    fold_stats = base.fold_statistics(
        fold_of_entity,
        entity_labels,
        structure["entity_flow_counts"],
        structure["entity_positive_flow_counts"],
    )
    if fold_stats != parent["selection"].get("fold_stat"):
        raise SystemExit("源实体折统计与父收据不符")

    base.log("构造首曝 semantic168 并重算三折 OOF 分数")
    matrix = base.build_first_exposure_semantic168(raw_values, structure["first_flow"])
    del raw_values, indices, masks, sequence_entities
    import torch
    import xgboost as xgb

    source_scores, model_receipts = base.score_oof_first_exposures(
        xgb,
        torch,
        matrix,
        fold_of_entity,
        args.parent_run_root.resolve(),
        int(config["predict_batch"]),
        float(base_config["resource_contract"]["runtime_gpu_floor_gib"]),
    )
    del matrix
    torch.cuda.empty_cache()

    budget = float(config["entity_fpr_budget"])
    source_threshold = base.strict_empirical_threshold(
        source_scores[entity_labels == 0], budget
    )
    source_seal = {
        "schema_version": "ch4-xgb-confidence-margin-operational-source-threshold-v1",
        "run_id": RUN_ID,
        "threshold": source_threshold,
        "statistical_certificate": False,
        "role": "历史运行基线与确认失败回退，不作为风险余量有限样本证书",
        "score_sha256": base.sha256_array(source_scores),
        "model_receipts": model_receipts,
    }
    source_seal["receipt_sha256"] = base.canonical_sha256(source_seal)
    base.atomic_json(args.out / "source-threshold-seal.json", source_seal)

    roles = prior.make_inner_roles(fold_of_entity, entity_labels, int(config["seed"]))
    minimum_zero_error_units = math.ceil(
        math.log(PER_DIRECTION_FAILURE_PROBABILITY) / math.log1p(-budget)
    )
    totals = {name: {} for name in ("source_baseline", "candidate", "active")}
    directions: list[dict[str, Any]] = []
    model_by_fold = {int(item["fold"]): item for item in model_receipts}
    entity_ids = structure["entity_ids"]

    for model_fold in range(base.N_FOLD):
        development = (fold_of_entity == model_fold) & (roles == 0)
        calibration = (fold_of_entity == model_fold) & (roles == 1)
        holdout = (fold_of_entity == model_fold) & (roles == 2)
        role_ids = {
            "development": entity_ids[development],
            "calibration": entity_ids[calibration],
            "holdout": entity_ids[holdout],
        }
        disjointness = base.verify_role_disjointness(role_ids)
        role_receipts = {
            name: base.role_receipt(
                name,
                model_fold,
                entity_ids[mask],
                entity_labels[mask],
                source_scores[mask],
            )
            for name, mask in {
                "development": development,
                "calibration": calibration,
                "holdout": holdout,
            }.items()
        }

        development_negative = development & (entity_labels == 0)
        candidate = risk_margin_threshold(
            source_scores[development_negative],
            budget,
            PER_DIRECTION_FAILURE_PROBABILITY,
        )
        calibration_negative = calibration & (entity_labels == 0)
        calibration_count = int(calibration_negative.sum())
        false_positive = int(
            (
                source_scores[calibration_negative]
                > float(candidate["threshold"])
            ).sum()
        )
        calibration_upper = base.clopper_pearson_upper(
            false_positive,
            calibration_count,
            PER_DIRECTION_FAILURE_PROBABILITY,
        )
        confirmed = calibration_upper is not None and calibration_upper <= budget
        active_threshold = (
            float(candidate["threshold"])
            if confirmed
            else float(source_threshold["threshold"])
        )

        holdout_labels = entity_labels[holdout]
        holdout_scores = source_scores[holdout]
        metrics = {
            "source_baseline": base.evaluate_rule(
                float(source_threshold["threshold"]), holdout_labels, holdout_scores
            ),
            "candidate": base.evaluate_rule(
                float(candidate["threshold"]), holdout_labels, holdout_scores
            ),
            "active": base.evaluate_rule(
                active_threshold, holdout_labels, holdout_scores
            ),
        }
        for name, item in metrics.items():
            prior.add_metrics(totals[name], item)

        gates = {
            "same_model_for_all_roles": all(
                receipt["fold"] == model_fold for receipt in role_receipts.values()
            ),
            "role_entities_disjoint": disjointness["all_pairwise_disjoint"],
            "development_risk_upper_within_budget": candidate[
                "actual_development_clopper_pearson_upper"
            ]
            <= budget,
            "calibration_units_sufficient": calibration_count
            >= minimum_zero_error_units,
            "candidate_confirmed": confirmed,
        }
        directions.append(
            {
                "model_fold": model_fold,
                "model_receipt": model_by_fold[model_fold],
                "model_sha256": model_by_fold[model_fold]["sha256"],
                "role_receipts": role_receipts,
                "disjointness": disjointness,
                "candidate": candidate,
                "certificate": {
                    "global_failure_probability": GLOBAL_FAILURE_PROBABILITY,
                    "direction_count": DIRECTION_COUNT,
                    "per_direction_failure_probability": (
                        PER_DIRECTION_FAILURE_PROBABILITY
                    ),
                    "minimum_zero_error_negative_entities": (
                        minimum_zero_error_units
                    ),
                    "calibration_negative_entities": calibration_count,
                    "calibration_false_positive_entities": false_positive,
                    "calibration_empirical_fpr": false_positive / calibration_count,
                    "calibration_clopper_pearson_upper": calibration_upper,
                    "confirmed": confirmed,
                },
                "decision": {
                    "active_threshold": active_threshold,
                    "source": (
                        "confirmed_risk_margin_candidate"
                        if confirmed
                        else "source_fallback"
                    ),
                    "fallback_reason": (
                        None
                        if confirmed
                        else (
                            "calibration_clopper_pearson_upper_not_computable"
                            if calibration_upper is None
                            else "calibration_clopper_pearson_upper_exceeds_budget"
                        )
                    ),
                },
                "holdout_metrics": metrics,
                "gates": gates,
                "qualified": all(gates.values()),
            }
        )

    aggregate = {name: prior.pooled_metrics(total) for name, total in totals.items()}
    all_directions_certified = all(
        item["certificate"]["confirmed"] for item in directions
    )
    all_direction_contracts_valid = all(
        item["qualified"] for item in directions
    )
    pooled_candidate_fpr_within_budget = (
        aggregate["candidate"]["entity_fpr"] <= budget
    )
    pooled_candidate_dr_not_below_source = (
        aggregate["candidate"]["detection_rate"]
        >= aggregate["source_baseline"]["detection_rate"]
    )
    qualified = (
        all_direction_contracts_valid
        and pooled_candidate_fpr_within_budget
        and pooled_candidate_dr_not_below_source
    )
    verdict = (
        "MECHANISM2_CONFIDENCE_MARGIN_SAME_MODEL_SOURCE_Q0_QUALIFIED"
        if qualified
        else "MECHANISM2_CONFIDENCE_MARGIN_SAME_MODEL_SOURCE_Q0_REJECTED"
    )
    candidate_seal = {
        "schema_version": (
            "ch4-xgb-confidence-margin-fallback-same-model-candidates-v1"
        ),
        "run_id": RUN_ID,
        "sealed_directions": [
            {
                "model_fold": item["model_fold"],
                "model_sha256": item["model_sha256"],
                "candidate": item["candidate"],
                "certificate": item["certificate"],
            }
            for item in directions
        ],
    }
    candidate_seal["receipt_sha256"] = base.canonical_sha256(candidate_seal)
    base.atomic_json(args.out / "target-candidate-seal.json", candidate_seal)

    summary = {
        "schema_version": (
            "ch4-xgb-confidence-margin-fallback-same-model-source-q0-results-v1"
        ),
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "source_year": "LSPR23",
        "screening_only": True,
        "independent_test": False,
        "target_year_arrays_read": 0,
        "new_models_trained": 0,
        "single_variable_revision": (
            "开发候选从经验贴满q改为Tong单侧精确上界反解风险余量阈值"
        ),
        "contract": {
            "entity_fpr_budget": budget,
            "global_failure_probability": GLOBAL_FAILURE_PROBABILITY,
            "direction_count": DIRECTION_COUNT,
            "per_direction_failure_probability": (
                PER_DIRECTION_FAILURE_PROBABILITY
            ),
            "development_candidate_rule": (
                "tong_one_sided_exact_upper_inverse"
            ),
            "comparison_operator": ">",
            "boundary_ties_alerted": False,
            "source_threshold_is_operational_not_certified": True,
        },
        "parent": parent,
        "fold_statistics": fold_stats,
        "fold_assignment_sha256": base.sha256_array(fold_of_entity),
        "source_threshold": source_seal,
        "directions": directions,
        "aggregate_holdout": aggregate,
        "mechanical_verdict": {
            "qualified": qualified,
            "all_directions_certified": all_directions_certified,
            "all_direction_contracts_valid": all_direction_contracts_valid,
            "pooled_candidate_fpr_within_budget": (
                pooled_candidate_fpr_within_budget
            ),
            "pooled_candidate_dr_not_below_source": (
                pooled_candidate_dr_not_below_source
            ),
            "strict_detection_rate_gain_required": False,
            "verdict": verdict,
            "rule": (
                "三方向全部获证，且池化持出候选FPR<=0.04、DR不低于源阈值"
            ),
        },
        "limitations": [
            "源年伪目标筛选，不是跨年度证据",
            "历史源阈值使用全体源年OOF标签，只是运行基线而非独立证书",
            "开发上界只生成候选，最终证书仅由独立校准角色签发",
            "实体同分布与统计独立性仍是有限样本解释条件",
        ],
        "timing": {"total_seconds": time.time() - started},
    }
    result_path = args.out / "aggregate-results.json"
    base.atomic_json(result_path, summary)

    import swanlab

    tracking = config["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=RUN_ID,
        config={
            "seed": 42,
            "source_year": "LSPR23",
            "zero_training": True,
            "same_model_roles": True,
            "risk_margin_candidate": True,
            "entity_fpr_budget": budget,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )
    swanlab.log(
        {
            "source/entity_fpr": aggregate["source_baseline"]["entity_fpr"],
            "source/detection_rate": aggregate["source_baseline"][
                "detection_rate"
            ],
            "candidate/entity_fpr": aggregate["candidate"]["entity_fpr"],
            "candidate/detection_rate": aggregate["candidate"]["detection_rate"],
            "active/entity_fpr": aggregate["active"]["entity_fpr"],
            "active/detection_rate": aggregate["active"]["detection_rate"],
            "qualified": int(qualified),
        },
        step=0,
    )
    swanlab.finish()
    base.atomic_json(
        args.out / "swanlab-receipt.json",
        {
            "completed": True,
            "workspace": tracking["workspace"],
            "project": tracking["project"],
            "aggregate_only": True,
        },
    )

    usage = resource.getrusage(resource.RUSAGE_SELF)
    base.atomic_json(
        args.out / "resource-receipt.json",
        {
            "wall_seconds": time.time() - started,
            "peak_rss_mib": usage.ru_maxrss / 1024.0,
            "peak_gpu_memory_mib": int(torch.cuda.max_memory_allocated() / 2**20),
        },
    )
    manifest = {
        "run_id": RUN_ID,
        "target_year_arrays_read": 0,
        "new_models_trained": 0,
        "files": {},
    }
    for path in (
        result_path,
        args.out / "source-threshold-seal.json",
        args.out / "target-candidate-seal.json",
        args.out / "swanlab-receipt.json",
        args.out / "resource-receipt.json",
    ):
        manifest["files"][path.name] = {
            "bytes": path.stat().st_size,
            "sha256": base.sha256_file(path),
        }
    base.atomic_json(args.out / "manifest.json", manifest)
    base.atomic_json(
        args.out / "status.json",
        {"state": "finished", "stage": "complete", "exit_code": 0},
    )
    base.log(
        f"机制二风险余量Q0完成：FPR={aggregate['candidate']['entity_fpr']:.10f} "
        f"DR={aggregate['candidate']['detection_rate']:.10f} verdict={verdict}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
