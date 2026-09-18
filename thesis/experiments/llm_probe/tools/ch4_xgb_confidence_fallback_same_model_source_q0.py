#!/usr/bin/env python3
"""机制二同模型三分、零训练源年修正 Q0。"""

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

import ch4_xgb_confidence_fallback_source_q0 as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-confidence-fallback-same-model-source-q0-seed42-v1"
DISPLAY_NAME = "同模型三分有限样本确认与源阈值回退源年修正Q0"
CONFIG_NAME = "ch4-xgb-confidence-fallback-same-model-source-q0-seed42-v1.json"
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
            / (
                f"{base.PARENT_RUN_ID}-for-"
                f"{base.PBC_RECOVERY_CONSUMER_ID}-v1"
            )
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
        "schema_version": "ch4-xgb-confidence-fallback-same-model-source-q0-v1",
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
        "same_model_inner_roles": ["development", "calibration", "holdout"],
        "comparison_operator": "strict_greater_than",
        "target_year_arrays_read": 0,
        "new_models_trained": 0,
        "predict_batch": 2_000_000,
    }
    for key, expected_value in expected.items():
        if config.get(key) != expected_value:
            raise SystemExit(f"修正 Q0 配置字段不符：{key}")
    if config.get("tracking") != {
        "workspace": base.AUTHORIZED_SWANLAB_WORKSPACE,
        "project": base.AUTHORIZED_SWANLAB_PROJECT,
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 目的地不符")


def make_inner_roles(
    fold_of_entity: np.ndarray, entity_labels: np.ndarray, seed: int
) -> np.ndarray:
    """在每个模型自己的留出实体内按类别稳定三分。"""
    roles = np.full(len(entity_labels), -1, np.int8)
    rng = np.random.RandomState(seed)
    for model_fold in range(base.N_FOLD):
        for label in (0, 1):
            members = np.flatnonzero(
                (fold_of_entity == model_fold) & (entity_labels == label)
            )
            shuffled = members[rng.permutation(len(members))]
            roles[shuffled] = np.arange(len(shuffled), dtype=np.int64) % 3
    if np.any(roles < 0):
        raise SystemExit("同模型三分未覆盖全部实体")
    return roles


def add_metrics(total: dict[str, int], metrics: dict[str, Any]) -> None:
    for key in (
        "negative_entity_count",
        "positive_entity_count",
        "false_positive_count",
        "true_positive_count",
    ):
        total[key] = total.get(key, 0) + int(metrics[key])


def pooled_metrics(total: dict[str, int]) -> dict[str, int | float]:
    return {
        **total,
        "entity_fpr": total["false_positive_count"]
        / total["negative_entity_count"],
        "detection_rate": total["true_positive_count"]
        / total["positive_entity_count"],
    }


def main() -> int:
    args = parse_args()
    config = load_json(args.config)
    if not isinstance(config, dict):
        raise SystemExit("配置顶层必须是对象")
    validate_config(config)
    if args.validate_config:
        print("SAME_MODEL_SOURCE_Q0_CONFIG_VALID", flush=True)
        return 0

    base_config_path = ROOT / "configs/ch4-xgb-confidence-fallback-source-q0-seed42-v1.json"
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
        print("SAME_MODEL_SOURCE_Q0_INPUTS_VALID", flush=True)
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
        "schema_version": "ch4-xgb-confidence-fallback-operational-source-threshold-v1",
        "run_id": RUN_ID,
        "threshold": source_threshold,
        "statistical_certificate": False,
        "role": "历史运行基线与确认失败回退，不作为同模型有限样本证书",
        "score_sha256": base.sha256_array(source_scores),
        "model_receipts": model_receipts,
    }
    source_seal["receipt_sha256"] = base.canonical_sha256(source_seal)
    base.atomic_json(args.out / "source-threshold-seal.json", source_seal)

    roles = make_inner_roles(fold_of_entity, entity_labels, int(config["seed"]))
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
        candidate = base.strict_empirical_threshold(
            source_scores[development_negative], budget
        )
        calibration_negative = calibration & (entity_labels == 0)
        calibration_count = int(calibration_negative.sum())
        false_positive = int(
            (
                source_scores[calibration_negative]
                > float(candidate["threshold"])
            ).sum()
        )
        upper = base.clopper_pearson_upper(
            false_positive,
            calibration_count,
            PER_DIRECTION_FAILURE_PROBABILITY,
        )
        confirmed = upper is not None and upper <= budget
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
            add_metrics(totals[name], item)

        gates = {
            "same_model_for_all_roles": all(
                receipt["fold"] == model_fold for receipt in role_receipts.values()
            ),
            "role_entities_disjoint": disjointness["all_pairwise_disjoint"],
            "calibration_units_sufficient": calibration_count
            >= minimum_zero_error_units,
            "candidate_confirmed": confirmed,
            "holdout_candidate_fpr_within_budget": metrics["candidate"]["entity_fpr"]
            <= budget,
            "holdout_candidate_dr_strictly_above_source": metrics["candidate"]
            ["detection_rate"]
            > metrics["source_baseline"]["detection_rate"],
        }
        directions.append(
            {
                "model_fold": model_fold,
                "model_receipt": model_by_fold[model_fold],
                "role_receipts": role_receipts,
                "disjointness": disjointness,
                "candidate": candidate,
                "certificate": {
                    "global_failure_probability": GLOBAL_FAILURE_PROBABILITY,
                    "direction_count": DIRECTION_COUNT,
                    "per_direction_failure_probability": PER_DIRECTION_FAILURE_PROBABILITY,
                    "minimum_zero_error_negative_entities": minimum_zero_error_units,
                    "calibration_negative_entities": calibration_count,
                    "calibration_false_positive_entities": false_positive,
                    "clopper_pearson_upper": upper,
                    "confirmed": confirmed,
                },
                "decision": {
                    "active_threshold": active_threshold,
                    "source": "confirmed_candidate" if confirmed else "source_fallback",
                },
                "holdout_metrics": metrics,
                "gates": gates,
                "qualified": all(gates.values()),
            }
        )

    aggregate = {name: pooled_metrics(total) for name, total in totals.items()}
    all_directions_qualified = all(item["qualified"] for item in directions)
    qualified = (
        all_directions_qualified
        and aggregate["candidate"]["entity_fpr"] <= budget
        and aggregate["candidate"]["detection_rate"]
        > aggregate["source_baseline"]["detection_rate"]
    )
    verdict = (
        "MECHANISM2_SAME_MODEL_SOURCE_Q0_QUALIFIED"
        if qualified
        else "MECHANISM2_SAME_MODEL_SOURCE_Q0_REJECTED"
    )
    candidate_seal = {
        "schema_version": "ch4-xgb-confidence-fallback-same-model-candidates-v1",
        "run_id": RUN_ID,
        "sealed_directions": [
            {
                "model_fold": item["model_fold"],
                "model_sha256": item["model_receipt"]["sha256"],
                "candidate": item["candidate"],
                "certificate": item["certificate"],
            }
            for item in directions
        ],
    }
    candidate_seal["receipt_sha256"] = base.canonical_sha256(candidate_seal)
    base.atomic_json(args.out / "target-candidate-seal.json", candidate_seal)

    summary = {
        "schema_version": "ch4-xgb-confidence-fallback-same-model-source-q0-results-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "source_year": "LSPR23",
        "screening_only": True,
        "independent_test": False,
        "target_year_arrays_read": 0,
        "new_models_trained": 0,
        "root_cause_fix": (
            "每个方向的开发、校准、持出分数均来自同一冻结OOF模型"
        ),
        "contract": {
            "entity_fpr_budget": budget,
            "global_failure_probability": GLOBAL_FAILURE_PROBABILITY,
            "direction_count": DIRECTION_COUNT,
            "per_direction_failure_probability": PER_DIRECTION_FAILURE_PROBABILITY,
            "comparison_operator": ">",
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
            "all_directions_qualified": all_directions_qualified,
            "verdict": verdict,
            "rule": (
                "三方向全部通过，且池化候选FPR<=0.04、DR严格高于历史源阈值基线"
            ),
        },
        "limitations": [
            "源年伪目标筛选，不是跨年度证据",
            "历史源阈值使用全体源年OOF标签，只是运行基线而非独立证书",
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
            "entity_fpr_budget": budget,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )
    swanlab.log(
        {
            "source/entity_fpr": aggregate["source_baseline"]["entity_fpr"],
            "source/detection_rate": aggregate["source_baseline"]["detection_rate"],
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
        f"机制二修正Q0完成：FPR={aggregate['candidate']['entity_fpr']:.10f} "
        f"DR={aggregate['candidate']['detection_rate']:.10f} verdict={verdict}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
