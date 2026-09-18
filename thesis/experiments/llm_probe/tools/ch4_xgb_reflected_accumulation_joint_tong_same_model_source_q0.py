#!/usr/bin/env python3
"""零训练检验原子分数反射累积与路径最大联合 Tong 控制。"""

from __future__ import annotations

import argparse
import hashlib
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
SOURCE_RUN_ID = (
    "ch4-xgb-reflected-cumulative-dual-evidence-lspr23-q0-seed42-v1-rerun1"
)
RUN_ID = "ch4-xgb-reflected-cumulative-dual-evidence-lspr23-q0-seed42-v1-rerun2"
DISPLAY_NAME = "原子分数反射累积与路径最大双证据统一风险控制源年零训练Q0"
SCHEMA_VERSION = "ch4-xgb-reflected-accumulation-joint-tong-same-model-source-q0-v1"
CONFIG_NAME = "ch4-xgb-reflected-accumulation-joint-tong-same-model-source-q0-seed42-v1.json"
BASE_CONFIG_NAME = "ch4-xgb-entity-exposure-lesion-source-diagnostic-seed42-v1.json"
PARENT_MODEL_RUN_ID = "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
PARENT_M1_RUN_ID = "ch4-xgb-entity-path-max-tong-same-model-q0-seed42-v1"
DIAGNOSTIC_RUN_ID = "ch4-xgb-path-risk-length-bucket-lspr23-diagnostic-seed42-v1"
METHODS = ("B0", "B1", "M1", "A1", "J1")
BUCKETS = (
    ("1-2", 1, 2),
    ("3-10", 3, 10),
    ("11-100", 11, 100),
    ("101-1000", 101, 1000),
    ("1001+", 1001, None),
)
SOURCE_THRESHOLD = 3.660049696918577e-05
Q = 0.04
GLOBAL_DELTA = 0.05
DIRECTION_COUNT = 9
PER_DIRECTION_DELTA = GLOBAL_DELTA / DIRECTION_COUNT
MODELS_TRAINED = 0
P1_CHECKPOINT_DATA_NAME = "p1-checkpoint.npz"
P1_CHECKPOINT_RECEIPT_NAME = "p1-checkpoint-receipt.json"
P1_CHECKPOINT_SCHEMA = "ch4-xgb-reflected-cumulative-dual-evidence-p1-checkpoint-v1"
SOURCE_CHECKPOINT_IMPLEMENTATION_SHA256 = (
    "d26ff2ad892d7f2860d0ee0c679f318a6395ea8a14b2b492c75b170e0ed49bdc"
)
SOURCE_CHECKPOINT_CONFIG_SHA256 = (
    "c72cce87d163940cf8d9d26fad6e3cbf8f584371e37b59b4828120fd8b4948ca"
)
P1_CHECKPOINT_ARRAY_NAMES = (
    "atomic_mean",
    "first_scores",
    "path_maximum",
    "exposure_count",
    "reflected_path_maximum",
)


class InputContractError(RuntimeError):
    """冻结输入、隔离、角色或统计合同无效。"""


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
    parser.add_argument(
        "--parent-m1-summary",
        type=Path,
        default=ROOT / "runs/diagnostics" / PARENT_M1_RUN_ID / "summary.json",
    )
    parser.add_argument(
        "--qualification-diagnostic-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / DIAGNOSTIC_RUN_ID,
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "runs/diagnostics" / RUN_ID
    )
    parser.add_argument(
        "--resume-run-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / SOURCE_RUN_ID,
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


def atomic_npz(path: Path, arrays: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with partial.open("wb") as handle:
        np.savez(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(partial, path)


def cleanup_p1_checkpoint(out: Path) -> None:
    for name in (P1_CHECKPOINT_RECEIPT_NAME, P1_CHECKPOINT_DATA_NAME):
        (out / name).unlink(missing_ok=True)


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
        "models_trained": 0,
        "target_year_arrays_read": 0,
        "oof_models_loaded": 3,
        "prediction_device": "cpu",
        "entity_fpr_budget": Q,
        "global_violation_probability": GLOBAL_DELTA,
        "direction_count": DIRECTION_COUNT,
        "per_direction_violation_probability": PER_DIRECTION_DELTA,
        "comparison_operator": ">",
        "same_model_roles": ["development", "calibration", "evaluation"],
        "role_rotation_count": 3,
        "methods": list(METHODS),
        "length_buckets": [
            {"name": name, "minimum": lower, "maximum": upper}
            for name, lower, upper in BUCKETS
        ],
        "kappa_rule": "(entity_equal_weight_atomic_mean_mu0+mu1)/2",
        "reflected_update": "A_j=max(0,A_{j-1}+r_j-kappa)",
        "rank_rule": "R=1-(1+count(development_benign_stat>=x))/(n+1)",
        "joint_rule": "J=max(R_S(S),R_A(C))",
        "a1_threshold_policy": "reuse_joint_tong_threshold_without_certificate",
        "tong_calibration_count_per_direction": 1,
        "score_pass_count": 2,
        "source_score_clip": [1e-7, 1.0],
        "near_threshold_challenge_ratio": 0.9777939759877333,
        "qualification_status": "QUALIFIED_SOURCE_Q0",
        "rejection_status": "REJECTED_SOURCE_Q0",
        "drift_rejection_status": "REJECTED_DRIFT_ORIENTATION",
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise InputContractError(f"配置字段不符：{key}")
    if config.get("diagnostic_contract") != {
        "run_id": DIAGNOSTIC_RUN_ID,
        "aggregate_results_sha256": "2a6a60712be81b6bb6aff8b2172ba512b18057ccd20248f478e714273b26a172",
        "manifest_sha256": "bfe4de81316d0ab5a2d6e6f640d90f1400d98e0271aba14a9eeed82a3057066a",
        "resource_summary_sha256": "7839ec5c9f7a600e38c033165706e7311830ee9e5179cfe56d95f6146d886c1b",
    }:
        raise InputContractError("资格诊断合同不符")
    if config.get("parent_m1_summary") != {
        "run_id": PARENT_M1_RUN_ID,
        "sha256": "2e4bbfe044b9ce9407090af765220fc7bc5829188cadcdfb33284002f633d462",
        "schema_version": "ch4-xgb-entity-path-max-tong-same-model-summary-v1",
    }:
        raise InputContractError("父 M1 摘要合同不符")
    if config.get("expected_parent_aggregate") != expected_parent_aggregate():
        raise InputContractError("父 B0/B1/M1 计数合同不符")
    if config.get("tong_reference") != {
        "16715": {
            "rank_one_based": 16111,
            "strictly_above_cap": 604,
            "violation_bound": 0.0051685926697284165,
            "previous_violation_bound": 0.005808086444466389,
        },
        "16716": {
            "rank_one_based": 16112,
            "strictly_above_cap": 604,
            "violation_bound": 0.005145538980673262,
            "previous_violation_bound": 0.005782506693476885,
        },
    }:
        raise InputContractError("Tong 标准库参考值不符")
    if config.get("resource_contract") != {
        "estimated_wall_minutes_min": 6,
        "estimated_wall_minutes_max": 8,
        "estimated_peak_host_gib": 18,
        "minimum_available_host_gib": 18,
        "minimum_free_gpu_memory_gib": 0,
        "minimum_free_disk_gib": 30,
    }:
        raise InputContractError("CPU 资源合同不符")
    if config.get("artifact_policy") != {
        "allowed_outputs": [
            "aggregate-results.json",
            "certificate-receipt.json",
            "input-receipt.json",
            "manifest.json",
            "resource-summary.json",
            "status.json",
            "run.log",
        ],
        "persist_entity_keys": False,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_new_models": False,
        "temporary_checkpoint_outputs": [
            P1_CHECKPOINT_DATA_NAME,
            P1_CHECKPOINT_RECEIPT_NAME,
        ],
        "temporary_checkpoint_cleanup_on_success": True,
    }:
        raise InputContractError("输出白名单不符")


def expected_parent_aggregate() -> dict[str, Any]:
    return {
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
    }


def distribution(values: Any) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    finite = finite[np.isfinite(finite)]
    if len(finite) == 0:
        return {
            "count": 0,
            "minimum": None,
            "median": None,
            "mean": None,
            "p90": None,
            "p95": None,
            "maximum": None,
        }
    return {
        "count": int(len(finite)),
        "minimum": float(finite.min()),
        "median": float(np.median(finite)),
        "mean": float(finite.mean()),
        "p90": float(np.percentile(finite, 90)),
        "p95": float(np.percentile(finite, 95)),
        "maximum": float(finite.max()),
    }


def binomial_upper_tail(n: int, k: int, success_probability: float) -> float:
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    term = success_probability**n
    terms = [term]
    failure_odds = (1.0 - success_probability) / success_probability
    for index in range(n, k, -1):
        term *= (index / (n - index + 1)) * failure_odds
        terms.append(term)
    return min(1.0, math.fsum(terms))


def tong_threshold(values: Any, config: dict[str, Any]) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    if len(finite) == 0 or not np.isfinite(finite).all():
        raise InputContractError("Tong 校准缺少有限良性实体")
    n = len(finite)
    low = max(1, int(math.floor(n * (1.0 - Q))))
    high = n
    while low < high:
        middle = (low + high) // 2
        if binomial_upper_tail(n, middle, 1.0 - Q) <= PER_DIRECTION_DELTA:
            high = middle
        else:
            low = middle + 1
    rank = low
    violation = binomial_upper_tail(n, rank, 1.0 - Q)
    previous = binomial_upper_tail(n, rank - 1, 1.0 - Q)
    reference = config["tong_reference"].get(str(n))
    if reference is None:
        raise InputContractError(f"Tong 校准良性数不在冻结参考中：{n}")
    if (
        rank != reference["rank_one_based"]
        or n - rank != reference["strictly_above_cap"]
        or violation > PER_DIRECTION_DELTA
        or previous <= PER_DIRECTION_DELTA
    ):
        raise InputContractError("Tong 最小次序位置未复现标准库参考值")
    ordered = np.sort(finite)
    threshold = float(ordered[rank - 1])
    return {
        "population": n,
        "entity_fpr_budget": Q,
        "violation_probability": PER_DIRECTION_DELTA,
        "rank_one_based": rank,
        "strictly_above_cap": n - rank,
        "violation_bound": violation,
        "previous_violation_bound": previous,
        "threshold": threshold,
        "threshold_tie_count": int((finite == threshold).sum()),
        "strictly_above_count": int((finite > threshold).sum()),
        "comparison_operator": ">",
        "certificate_valid": True,
    }


def stable_role_groups(
    fold_of_entity: Any, entity_labels: Any
) -> tuple[Any, list[dict[str, Any]]]:
    groups = np.full(base.N_ENTITY, -1, np.int8)
    receipts: list[dict[str, Any]] = []
    for fold in range(base.N_FOLD):
        for label in (0, 1):
            members = np.flatnonzero(
                (fold_of_entity == fold) & (entity_labels == label)
            ).astype(np.int64, copy=False)
            keyed = sorted(
                (hashlib.sha256(entity.tobytes()).digest(), int(entity))
                for entity in members
            )
            ordered = np.asarray([entity for _, entity in keyed], np.int64)
            assigned = np.arange(len(ordered), dtype=np.int64) % 3
            groups[ordered] = assigned
            receipts.append(
                {
                    "model_fold": fold,
                    "label": label,
                    "population": int(len(ordered)),
                    "ordering": "sha256(int64_entity_index_bytes)_ascending",
                    "ordered_entity_set_sha256": base.sha256_array(ordered),
                    "group_counts": [
                        int((assigned == group).sum()) for group in range(3)
                    ],
                }
            )
    if np.any(groups < 0):
        raise InputContractError("同模型三角色未覆盖全部实体")
    return groups, receipts


def role_receipt(name: str, mask: Any, labels: Any) -> dict[str, Any]:
    entity_ids = np.flatnonzero(mask).astype(np.int64, copy=False)
    return {
        "role": name,
        "entity_count": int(len(entity_ids)),
        "negative_entities": int((labels[mask] == 0).sum()),
        "positive_entities": int((labels[mask] == 1).sum()),
        "entity_set_sha256": base.sha256_array(entity_ids),
    }


def validate_diagnostic(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    contract = config["diagnostic_contract"]
    paths = {
        "aggregate-results.json": root / "aggregate-results.json",
        "manifest.json": root / "manifest.json",
        "resource-summary.json": root / "resource-summary.json",
    }
    expected_hashes = {
        "aggregate-results.json": contract["aggregate_results_sha256"],
        "manifest.json": contract["manifest_sha256"],
        "resource-summary.json": contract["resource_summary_sha256"],
    }
    for name, path in paths.items():
        if not path.is_file() or base.sha256_file(path) != expected_hashes[name]:
            raise InputContractError(f"资格诊断制品缺失或 SHA-256 不符：{name}")
    aggregate = load_json(paths["aggregate-results.json"])
    manifest = load_json(paths["manifest.json"])
    resource_summary = load_json(paths["resource-summary.json"])
    if (
        aggregate.get("run_id") != DIAGNOSTIC_RUN_ID
        or aggregate.get("parent_reproduction", {}).get("exact_aggregate_match")
        is not True
        or aggregate.get("parent_reproduction", {}).get("aggregate")
        != expected_parent_aggregate()
        or aggregate.get("m1_missed_positive_path_summary", {}).get("entity_count")
        != 4
        or aggregate.get("integrity", {}).get("target_year_arrays_read") != 0
        or aggregate.get("integrity", {}).get("models_trained") != 0
        or manifest.get("target_year_arrays_read") != 0
        or manifest.get("models_trained") != 0
        or resource_summary.get("prediction_device") != "cpu"
        or resource_summary.get("cuda_peak_allocated_bytes") != 0
    ):
        raise InputContractError("资格诊断身份、父复现或零训练边界不符")
    observed_ratio = aggregate["m1_missed_positive_path_summary"]["statistics"][
        "path_maximum_over_threshold"
    ]["maximum"]
    if observed_ratio != config["near_threshold_challenge_ratio"]:
        raise InputContractError("唯一近阈值挑战比例与资格诊断不符")
    return {
        "root": str(root.resolve()),
        "files": {
            name: {"sha256": expected_hashes[name], "bytes": path.stat().st_size}
            for name, path in paths.items()
        },
    }


def validate_parent_m1(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    contract = config["parent_m1_summary"]
    if not path.is_file() or base.sha256_file(path) != contract["sha256"]:
        raise InputContractError("父 M1 摘要缺失或 SHA-256 不符")
    summary = load_json(path)
    if (
        summary.get("schema_version") != contract["schema_version"]
        or summary.get("run_id") != contract["run_id"]
        or summary.get("aggregate") != expected_parent_aggregate()
        or len(summary.get("rounds", [])) != 6
    ):
        raise InputContractError("父 M1 摘要身份、方向或指标不符")
    return summary


def source_model_identities(
    parent_root: Path, seal: dict[str, Any]
) -> list[dict[str, Any]]:
    sealed = {item["filename"]: item for item in seal["source_model_receipts"]}
    identities: list[dict[str, Any]] = []
    for fold in range(base.N_FOLD):
        name = f"model_oof_semantic168_fold{fold}.json"
        path = parent_root / name
        if not path.is_file():
            raise InputContractError(f"折 {fold} 模型缺失")
        actual_sha = base.sha256_file(path)
        if actual_sha != sealed[name]["sha256"]:
            raise InputContractError(f"折 {fold} 模型 SHA-256 不符")
        identities.append({"fold": fold, "filename": name, "sha256": actual_sha})
    return identities


def p1_checkpoint_identity(
    args: argparse.Namespace,
    parent: dict[str, Any],
    diagnostic_receipt: dict[str, Any],
    array_receipts: dict[str, Any],
    model_identities: list[dict[str, Any]],
    fold_sha: str,
    grouping_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "implementation_sha256": base.sha256_file(Path(__file__).resolve()),
        "config_sha256": base.sha256_file(args.config.resolve()),
        "base_config_sha256": base.sha256_file(ROOT / "configs" / BASE_CONFIG_NAME),
        "parent_config_sha256": base.sha256_file(args.parent_config.resolve()),
        "parent_m1_summary_sha256": base.sha256_file(
            args.parent_m1_summary.resolve()
        ),
        "parent_model_run": parent,
        "qualification_diagnostic": diagnostic_receipt,
        "source_arrays": array_receipts,
        "source_models": model_identities,
        "fold_assignment_sha256": fold_sha,
        "role_grouping_receipts": grouping_receipts,
    }


def checkpoint_array_receipt(values: Any) -> dict[str, Any]:
    array = np.ascontiguousarray(values)
    return {
        "dtype": str(array.dtype),
        "shape": list(array.shape),
        "sha256": base.sha256_array(array),
    }


def write_p1_checkpoint(
    out: Path,
    identity: dict[str, Any],
    first_stats: dict[str, Any],
    reflected_first: dict[str, Any],
) -> dict[str, Any]:
    arrays = {
        "atomic_mean": np.ascontiguousarray(first_stats["atomic_mean"]),
        "first_scores": np.ascontiguousarray(first_stats["first_scores"]),
        "path_maximum": np.ascontiguousarray(first_stats["path_maximum"]),
        "exposure_count": np.ascontiguousarray(first_stats["exposure_count"]),
        "reflected_path_maximum": np.ascontiguousarray(
            reflected_first["path_maximum"]
        ),
    }
    receipt_path = out / P1_CHECKPOINT_RECEIPT_NAME
    data_path = out / P1_CHECKPOINT_DATA_NAME
    receipt_path.unlink(missing_ok=True)
    atomic_npz(data_path, arrays)
    receipt = {
        "schema_version": P1_CHECKPOINT_SCHEMA,
        "run_id": RUN_ID,
        "completed_stage": "P1",
        "resume_stage": "P2",
        "temporary": True,
        "identity": identity,
        "data_file": P1_CHECKPOINT_DATA_NAME,
        "data_file_sha256": base.sha256_file(data_path),
        "arrays": {
            name: checkpoint_array_receipt(arrays[name])
            for name in P1_CHECKPOINT_ARRAY_NAMES
        },
        "first_raw_persisted": False,
        "per_flow_scores_persisted": 0,
        "entity_keys_persisted": 0,
    }
    atomic_json(receipt_path, receipt)
    return receipt


def load_p1_checkpoint(
    out: Path,
    identity: dict[str, Any],
    entity_lengths: Any,
    *,
    expected_run_id: str = RUN_ID,
    source_checkpoint: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    receipt_path = out / P1_CHECKPOINT_RECEIPT_NAME
    data_path = out / P1_CHECKPOINT_DATA_NAME
    if not receipt_path.exists() and not data_path.exists():
        return None
    try:
        if not receipt_path.is_file() or not data_path.is_file():
            raise ValueError("数据或收据不完整")
        receipt = load_json(receipt_path)
        stored_identity = receipt.get("identity", {})
        expected_identity = identity
        if source_checkpoint:
            if (
                stored_identity.get("implementation_sha256")
                != SOURCE_CHECKPOINT_IMPLEMENTATION_SHA256
                or stored_identity.get("config_sha256")
                != SOURCE_CHECKPOINT_CONFIG_SHA256
            ):
                raise ValueError("恢复源的生产实现或配置 SHA 不符")
            stored_identity = dict(stored_identity)
            expected_identity = dict(identity)
            stored_identity.pop("implementation_sha256", None)
            stored_identity.pop("config_sha256", None)
            expected_identity.pop("implementation_sha256", None)
            expected_identity.pop("config_sha256", None)
        if (
            receipt.get("schema_version") != P1_CHECKPOINT_SCHEMA
            or receipt.get("run_id") != expected_run_id
            or receipt.get("completed_stage") != "P1"
            or receipt.get("resume_stage") != "P2"
            or receipt.get("temporary") is not True
            or stored_identity != expected_identity
            or receipt.get("data_file") != P1_CHECKPOINT_DATA_NAME
            or receipt.get("data_file_sha256") != base.sha256_file(data_path)
            or receipt.get("first_raw_persisted") is not False
            or receipt.get("per_flow_scores_persisted") != 0
            or receipt.get("entity_keys_persisted") != 0
        ):
            raise ValueError("身份、输入、模型、实现或数据文件 SHA 不符")
        with np.load(data_path, allow_pickle=False) as stored:
            if tuple(stored.files) != P1_CHECKPOINT_ARRAY_NAMES:
                raise ValueError("实体级数组清单不符")
            arrays = {name: np.array(stored[name], copy=True) for name in stored.files}
        expected_types = {
            "atomic_mean": ((base.N_ENTITY,), np.dtype(np.float64)),
            "first_scores": ((base.N_ENTITY,), np.dtype(np.float32)),
            "path_maximum": ((base.N_ENTITY,), np.dtype(np.float32)),
            "exposure_count": ((base.N_ENTITY,), np.dtype(np.int64)),
            "reflected_path_maximum": (
                (3, base.N_ENTITY),
                np.dtype(np.float64),
            ),
        }
        for name, (shape, dtype) in expected_types.items():
            values = arrays[name]
            if values.shape != shape or values.dtype != dtype:
                raise ValueError(f"{name} 的形状或类型不符")
            if receipt.get("arrays", {}).get(name) != checkpoint_array_receipt(
                values
            ):
                raise ValueError(f"{name} 的内容 SHA 不符")
            if np.issubdtype(dtype, np.floating) and not np.isfinite(values).all():
                raise ValueError(f"{name} 含非有限值")
        exposure_count = arrays["exposure_count"]
        if (
            np.any(exposure_count <= 0)
            or int(exposure_count.sum()) != base.N_FLOW
            or not np.array_equal(exposure_count, entity_lengths)
        ):
            raise ValueError("曝光数覆盖不符")
        if np.any(arrays["reflected_path_maximum"] < 0.0):
            raise ValueError("反射路径统计出现负值")
    except Exception as error:
        base.log(f"P1临时检查点无效，重新计算P1：{error}")
        if not source_checkpoint:
            cleanup_p1_checkpoint(out)
        return None
    first_stats = {
        "atomic_mean": arrays["atomic_mean"],
        "first_scores": arrays["first_scores"],
        "path_maximum": arrays["path_maximum"],
        "exposure_count": arrays["exposure_count"],
    }
    reflected_first = {"path_maximum": arrays["reflected_path_maximum"]}
    return first_stats, reflected_first, receipt


def load_cpu_boosters(
    xgb_module: Any, parent_root: Path, seal: dict[str, Any]
) -> tuple[list[Any], list[dict[str, Any]]]:
    sealed = {item["filename"]: item for item in seal["source_model_receipts"]}
    boosters: list[Any] = []
    receipts: list[dict[str, Any]] = []
    for fold in range(base.N_FOLD):
        name = f"model_oof_semantic168_fold{fold}.json"
        path = parent_root / name
        actual_sha = base.sha256_file(path)
        if actual_sha != sealed[name]["sha256"]:
            raise InputContractError(f"折 {fold} 模型 SHA-256 不符")
        booster = xgb_module.Booster()
        booster.load_model(path)
        if int(booster.num_boosted_rounds()) != base.N_TREE:
            raise InputContractError(f"折 {fold} 模型树数不符")
        booster.set_param({"device": "cpu"})
        boosters.append(booster)
        receipts.append(
            {
                "fold": fold,
                "filename": name,
                "sha256": actual_sha,
                "num_boosted_rounds": base.N_TREE,
                "prediction_device": "cpu",
            }
        )
    return boosters, receipts


def score_all_flows(
    boosters: list[Any],
    matrix: Any,
    indices: Any,
    masks: Any,
    sequence_entities: Any,
    fold_of_entity: Any,
    batch_size: int,
    stage: str,
) -> Any:
    scores = np.full(base.N_FLOW, np.nan, np.float32)
    seen = np.zeros(base.N_FLOW, np.bool_)
    for fold, booster in enumerate(boosters):
        selected_sequences = np.flatnonzero(fold_of_entity[sequence_entities] == fold)
        started = time.time()
        for start in range(0, len(selected_sequences), batch_size):
            selected = selected_sequences[start : start + batch_size]
            index_block = np.asarray(indices[selected])
            valid = np.asarray(masks[selected]) > 0
            rows = np.asarray(index_block[valid], np.int64)
            if seen[rows].any():
                raise InputContractError(f"{stage} 重复覆盖流")
            predicted = np.asarray(booster.inplace_predict(matrix[rows]), np.float32)
            if predicted.shape != (len(rows),) or not np.isfinite(predicted).all():
                raise InputContractError(f"{stage} 分数形状异常或含非有限值")
            scores[rows] = predicted
            seen[rows] = True
            base.beat(
                f"{stage}/fold{fold}",
                min(start + batch_size, len(selected_sequences)),
                len(selected_sequences),
                started,
            )
    if not seen.all() or not np.isfinite(scores).all():
        raise InputContractError(f"{stage} 未恰好覆盖全部源年流")
    return scores


def first_pass_path_statistics(
    raw_scores: Any, indices: Any, masks: Any, sequence_entities: Any
) -> dict[str, Any]:
    cumulative_sum = np.zeros(base.N_ENTITY, np.float64)
    exposure_count = np.zeros(base.N_ENTITY, np.int64)
    first_scores = np.full(base.N_ENTITY, np.nan, np.float32)
    path_maximum = np.full(base.N_ENTITY, -np.inf, np.float32)
    started = time.time()
    for sequence in range(base.N_SEQUENCE):
        valid = np.asarray(masks[sequence]) > 0
        rows = np.asarray(indices[sequence, valid], np.int64)
        entity = int(sequence_entities[sequence])
        prior = int(exposure_count[entity])
        raw = np.asarray(raw_scores[rows], np.float32)
        clipped = np.clip(raw, 1e-7, 1.0).astype(np.float64)
        cumulative = np.cumsum(clipped, dtype=np.float64) + cumulative_sum[entity]
        denominator = np.arange(prior + 1, prior + len(raw) + 1, dtype=np.float64)
        running = (cumulative / denominator).astype(np.float32)
        if prior == 0:
            first_scores[entity] = raw[0]
        path_maximum[entity] = max(
            float(path_maximum[entity]), float(running.max())
        )
        cumulative_sum[entity] = cumulative[-1]
        exposure_count[entity] = prior + len(raw)
        base.beat("第一遍/原子均值与强证据路径", sequence + 1, base.N_SEQUENCE, started)
    if (
        int(exposure_count.sum()) != base.N_FLOW
        or not np.isfinite(first_scores).all()
        or not np.isfinite(path_maximum).all()
    ):
        raise InputContractError("第一遍实体路径聚合不完整")
    return {
        "atomic_mean": cumulative_sum / exposure_count,
        "first_scores": first_scores,
        "path_maximum": path_maximum,
        "exposure_count": exposure_count,
    }


def build_direction_specs(
    fold_of_entity: Any,
    groups: Any,
    labels: Any,
    atomic_mean: Any,
) -> tuple[list[dict[str, Any]], Any, list[str]]:
    specs: list[dict[str, Any]] = []
    kappas = np.full((base.N_FOLD, 3), np.nan, np.float64)
    orientation_failures: list[str] = []
    evaluation_coverage = np.zeros(base.N_ENTITY, np.int8)
    for fold in range(base.N_FOLD):
        for rotation in range(3):
            development_group = rotation
            calibration_group = (rotation + 1) % 3
            evaluation_group = (rotation + 2) % 3
            development = (fold_of_entity == fold) & (groups == development_group)
            calibration = (fold_of_entity == fold) & (groups == calibration_group)
            evaluation = (fold_of_entity == fold) & (groups == evaluation_group)
            if (
                np.any(development & calibration)
                or np.any(development & evaluation)
                or np.any(calibration & evaluation)
                or int((development | calibration | evaluation).sum())
                != int((fold_of_entity == fold).sum())
            ):
                raise InputContractError("D/C/E 角色交集或覆盖无效")
            expected_positive_groups = (
                (27, 27, 26) if fold in (0, 1) else (27, 26, 26)
            )
            for group in range(3):
                group_mask = (fold_of_entity == fold) & (groups == group)
                negative_count = int((group_mask & (labels == 0)).sum())
                positive_count = int((group_mask & (labels == 1)).sum())
                if (
                    negative_count not in (16715, 16716)
                    or positive_count != expected_positive_groups[group]
                ):
                    raise InputContractError(
                        f"fold={fold}/group={group} 三角色类别计数不符"
                    )
            mu0 = float(atomic_mean[development & (labels == 0)].mean())
            mu1 = float(atomic_mean[development & (labels == 1)].mean())
            kappa = (mu0 + mu1) / 2.0
            orientation_valid = 0.0 <= mu0 < kappa < mu1 <= 1.0
            direction_id = f"fold{fold}-rotation{rotation}"
            if not orientation_valid:
                orientation_failures.append(direction_id)
            kappas[fold, rotation] = kappa
            evaluation_coverage[evaluation] += 1
            specs.append(
                {
                    "direction_index": fold * 3 + rotation,
                    "direction_id": direction_id,
                    "model_fold": fold,
                    "rotation": rotation,
                    "development_group": development_group,
                    "calibration_group": calibration_group,
                    "evaluation_group": evaluation_group,
                    "development_mask": development,
                    "calibration_mask": calibration,
                    "evaluation_mask": evaluation,
                    "role_receipts": {
                        "development": role_receipt("development", development, labels),
                        "calibration": role_receipt("calibration", calibration, labels),
                        "evaluation": role_receipt("evaluation", evaluation, labels),
                    },
                    "mu0": mu0,
                    "mu1": mu1,
                    "kappa": kappa,
                    "orientation_valid": orientation_valid,
                }
            )
    if not np.all(evaluation_coverage == 1):
        raise InputContractError("九方向评价实体未恰好覆盖一次")
    return specs, kappas, orientation_failures


def reflected_final_statistics(
    raw_scores: Any,
    indices: Any,
    masks: Any,
    sequence_entities: Any,
    fold_of_entity: Any,
    kappas: Any,
) -> dict[str, Any]:
    current = np.zeros((3, base.N_ENTITY), np.float64)
    maximum = np.zeros((3, base.N_ENTITY), np.float64)
    zero_count = np.zeros((3, base.N_ENTITY), np.int64)
    maximum_position = np.zeros((3, base.N_ENTITY), np.int64)
    exposure_count = np.zeros(base.N_ENTITY, np.int64)
    started = time.time()
    for sequence in range(base.N_SEQUENCE):
        valid = np.asarray(masks[sequence]) > 0
        rows = np.asarray(indices[sequence, valid], np.int64)
        entity = int(sequence_entities[sequence])
        fold = int(fold_of_entity[entity])
        prior = int(exposure_count[entity])
        scores = np.clip(raw_scores[rows], 1e-7, 1.0).astype(np.float64)
        increments = scores[None, :] - kappas[fold, :, None]
        unreflected = current[:, entity, None] + np.cumsum(increments, axis=1)
        reflected = unreflected - np.minimum(
            np.minimum.accumulate(unreflected, axis=1), 0.0
        )
        local_maximum = reflected.max(axis=1)
        for rotation in range(3):
            if local_maximum[rotation] > maximum[rotation, entity]:
                offset = int(np.argmax(reflected[rotation]))
                maximum[rotation, entity] = float(local_maximum[rotation])
                maximum_position[rotation, entity] = prior + offset + 1
        current[:, entity] = reflected[:, -1]
        zero_count[:, entity] += np.count_nonzero(reflected == 0.0, axis=1)
        exposure_count[entity] = prior + len(scores)
        base.beat("第一遍/三组反射终值", sequence + 1, base.N_SEQUENCE, started)
    if int(exposure_count.sum()) != base.N_FLOW:
        raise InputContractError("反射终值未覆盖全部源年流")
    return {
        "path_maximum": maximum,
        "zero_count": zero_count,
        "maximum_position": maximum_position,
    }


def tail_rank(sorted_development: Any, values: Any) -> Any:
    indices = np.searchsorted(sorted_development, values, side="left")
    return indices.astype(np.float64) / (len(sorted_development) + 1.0)


def seal_certificates(
    specs: list[dict[str, Any]],
    labels: Any,
    strong_final: Any,
    reflected_final: Any,
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    public_directions: list[dict[str, Any]] = []
    runtime_directions: list[dict[str, Any]] = []
    for spec in specs:
        rotation = int(spec["rotation"])
        development_negative = spec["development_mask"] & (labels == 0)
        calibration_negative = spec["calibration_mask"] & (labels == 0)
        development_strong = np.sort(strong_final[development_negative])
        development_reflected = np.sort(
            reflected_final[rotation, development_negative]
        )
        calibration_strong = strong_final[calibration_negative]
        calibration_reflected = reflected_final[rotation, calibration_negative]
        calibration_joint = np.maximum(
            tail_rank(development_strong, calibration_strong),
            tail_rank(development_reflected, calibration_reflected),
        )
        m1_receipt = tong_threshold(calibration_strong, config)
        joint_receipt = tong_threshold(calibration_joint, config)
        development_strong_ranks = tail_rank(
            development_strong, development_strong
        )
        development_reflected_ranks = tail_rank(
            development_reflected, development_reflected
        )
        public = {
            key: value
            for key, value in spec.items()
            if not key.endswith("_mask")
        }
        public.update(
            {
                "development_benign_count": int(development_negative.sum()),
                "calibration_benign_count": int(calibration_negative.sum()),
                "development_benign_statistics": {
                    "strong_final": distribution(development_strong),
                    "reflected_final": distribution(development_reflected),
                    "strong_danger_rank": distribution(development_strong_ranks),
                    "reflected_danger_rank": distribution(
                        development_reflected_ranks
                    ),
                },
                "m1_tong": m1_receipt,
                "joint_tong": joint_receipt,
                "a1_uses_joint_threshold_without_separate_certificate": True,
            }
        )
        public_directions.append(public)
        runtime_directions.append(
            {
                **spec,
                "development_strong": development_strong,
                "development_reflected": development_reflected,
                "m1_threshold": m1_receipt["threshold"],
                "joint_threshold": joint_receipt["threshold"],
            }
        )
    receipt = {
        "schema_version": "ch4-xgb-reflected-cumulative-dual-evidence-certificate-v1",
        "run_id": RUN_ID,
        "source_year": "LSPR23",
        "entity_fpr_budget": Q,
        "global_violation_probability": GLOBAL_DELTA,
        "direction_count": DIRECTION_COUNT,
        "per_direction_violation_probability": PER_DIRECTION_DELTA,
        "comparison_operator": ">",
        "joint_tong_calibrations_per_direction": 1,
        "a1_separate_certificate_count": 0,
        "all_m1_certificates_valid": all(
            item["m1_tong"]["certificate_valid"] for item in public_directions
        ),
        "all_joint_certificates_valid": all(
            item["joint_tong"]["certificate_valid"] for item in public_directions
        ),
        "evaluation_metrics_computed_before_seal": False,
        "directions": public_directions,
    }
    return receipt, runtime_directions


def parent_reproduction(
    parent_summary: dict[str, Any],
    fold_of_entity: Any,
    labels: Any,
    first_scores: Any,
    strong_final: Any,
) -> tuple[dict[str, Any], Any, Any]:
    halves = path_max.make_inner_halves(fold_of_entity, labels, 42)
    parent_thresholds = np.full(base.N_ENTITY, np.nan, np.float64)
    for item in parent_summary["rounds"]:
        mask = (fold_of_entity == int(item["model_fold"])) & (
            halves == int(item["evaluation_half"])
        )
        parent_thresholds[mask] = float(item["path_threshold_receipt"]["threshold"])
    if not np.isfinite(parent_thresholds).all():
        raise InputContractError("父 M1 六方向阈值未覆盖全部实体")
    alerts = {
        "B0_first": first_scores > SOURCE_THRESHOLD,
        "B1_all_source": strong_final > SOURCE_THRESHOLD,
        "M1_path_max_tong_same_model_crosscal": strong_final > parent_thresholds,
    }
    aggregate = {
        name: metric_counts(labels, alert, np.ones(base.N_ENTITY, np.bool_))
        for name, alert in alerts.items()
    }
    if aggregate != expected_parent_aggregate():
        raise InputContractError("父 B0/B1/M1 计数未精确复现")
    missed = (labels == 1) & ~alerts["M1_path_max_tong_same_model_crosscal"]
    ratios = np.where(missed, strong_final / parent_thresholds, -np.inf)
    if int(missed.sum()) != 4:
        raise InputContractError("父 M1 漏检正实体数不是 4")
    challenge = ratios == ratios.max()
    if int(challenge.sum()) != 1 or float(ratios.max()) != 0.9777939759877333:
        raise InputContractError("唯一近阈值父 M1 漏检挑战未精确重建")
    return {
        "exact_match": True,
        "aggregate": aggregate,
        "parent_summary_sha256": "2e4bbfe044b9ce9407090af765220fc7bc5829188cadcdfb33284002f633d462",
        "m1_missed_positive_count": 4,
        "unique_near_threshold_ratio": float(ratios.max()),
    }, missed, challenge


def metric_counts(labels: Any, alerts: Any, selection: Any) -> dict[str, Any]:
    negative = selection & (labels == 0)
    positive = selection & (labels == 1)
    fp = int((alerts & negative).sum())
    tp = int((alerts & positive).sum())
    n_negative = int(negative.sum())
    n_positive = int(positive.sum())
    return {
        "negative_entities": n_negative,
        "positive_entities": n_positive,
        "false_positive_entities": fp,
        "detected_positive_entities": tp,
        "entity_fpr": fp / n_negative if n_negative else None,
        "detection_rate": tp / n_positive if n_positive else None,
    }


def first_alert_summary(
    selection: Any,
    exposure: Any,
    alert_time: Any,
    first_time: Any,
) -> dict[str, Any]:
    alerted = selection & (exposure > 0)
    return {
        "eligible_entity_count": int(selection.sum()),
        "alerted_entity_count": int(alerted.sum()),
        "never_alerted_entity_count": int((selection & ~alerted).sum()),
        "exposure": distribution(exposure[alerted]),
        "raw_time_difference": distribution(alert_time[alerted] - first_time[alerted]),
    }


def update_first_alert(
    exposure: Any,
    alert_time: Any,
    entity: int,
    prior: int,
    crossings: Any,
    times: Any,
) -> int | None:
    if exposure[entity] != 0:
        return None
    found = np.flatnonzero(crossings)
    if len(found) == 0:
        return None
    offset = int(found[0])
    exposure[entity] = prior + offset + 1
    alert_time[entity] = float(times[offset])
    return offset


def second_pass_alerts(
    raw_scores: Any,
    indices: Any,
    masks: Any,
    sequence_entities: Any,
    flow_times: Any,
    fold_of_entity: Any,
    groups: Any,
    runtime_directions: list[dict[str, Any]],
) -> dict[str, Any]:
    evaluation_rotation = (groups.astype(np.int64) + 1) % 3
    direction_index = fold_of_entity.astype(np.int64) * 3 + evaluation_rotation
    kappa = np.asarray(
        [runtime_directions[index]["kappa"] for index in direction_index], np.float64
    )
    m1_threshold = np.asarray(
        [runtime_directions[index]["m1_threshold"] for index in direction_index],
        np.float64,
    )
    joint_threshold = np.asarray(
        [runtime_directions[index]["joint_threshold"] for index in direction_index],
        np.float64,
    )
    cumulative_sum = np.zeros(base.N_ENTITY, np.float64)
    exposure_count = np.zeros(base.N_ENTITY, np.int64)
    strong_maximum = np.zeros(base.N_ENTITY, np.float32)
    reflected_current = np.zeros(base.N_ENTITY, np.float64)
    reflected_maximum = np.zeros(base.N_ENTITY, np.float64)
    reflected_zero_count = np.zeros(base.N_ENTITY, np.int64)
    reflected_maximum_position = np.zeros(base.N_ENTITY, np.int64)
    exposures = {name: np.zeros(base.N_ENTITY, np.int64) for name in METHODS}
    alert_times = {
        name: np.full(base.N_ENTITY, np.nan, np.float64) for name in METHODS
    }
    attribution = np.zeros(base.N_ENTITY, np.int8)
    started = time.time()
    for sequence in range(base.N_SEQUENCE):
        valid = np.asarray(masks[sequence]) > 0
        rows = np.asarray(indices[sequence, valid], np.int64)
        entity = int(sequence_entities[sequence])
        prior = int(exposure_count[entity])
        times = np.asarray(flow_times[rows], np.float64)
        raw = np.asarray(raw_scores[rows], np.float32)
        clipped = np.clip(raw, 1e-7, 1.0).astype(np.float64)
        cumulative = np.cumsum(clipped, dtype=np.float64) + cumulative_sum[entity]
        denominator = np.arange(prior + 1, prior + len(raw) + 1, dtype=np.float64)
        running = (cumulative / denominator).astype(np.float32)
        strong_path = np.maximum.accumulate(
            np.maximum(running, strong_maximum[entity])
        )
        unreflected = reflected_current[entity] + np.cumsum(
            clipped - kappa[entity], dtype=np.float64
        )
        reflected = unreflected - np.minimum(
            np.minimum.accumulate(unreflected), 0.0
        )
        reflected_path = np.maximum.accumulate(
            np.maximum(reflected, reflected_maximum[entity])
        )
        spec = runtime_directions[int(direction_index[entity])]
        strong_rank = tail_rank(spec["development_strong"], strong_path)
        reflected_rank = tail_rank(spec["development_reflected"], reflected_path)
        joint_rank = np.maximum(strong_rank, reflected_rank)
        if prior == 0 and raw[0] > SOURCE_THRESHOLD:
            exposures["B0"][entity] = 1
            alert_times["B0"][entity] = float(times[0])
        update_first_alert(
            exposures["B1"],
            alert_times["B1"],
            entity,
            prior,
            strong_path > SOURCE_THRESHOLD,
            times,
        )
        update_first_alert(
            exposures["M1"],
            alert_times["M1"],
            entity,
            prior,
            strong_path > m1_threshold[entity],
            times,
        )
        update_first_alert(
            exposures["A1"],
            alert_times["A1"],
            entity,
            prior,
            reflected_rank > joint_threshold[entity],
            times,
        )
        offset = update_first_alert(
            exposures["J1"],
            alert_times["J1"],
            entity,
            prior,
            joint_rank > joint_threshold[entity],
            times,
        )
        if offset is not None:
            strong_cross = bool(strong_rank[offset] > joint_threshold[entity])
            reflected_cross = bool(
                reflected_rank[offset] > joint_threshold[entity]
            )
            attribution[entity] = (
                3 if strong_cross and reflected_cross else 2 if strong_cross else 1
            )
        local_maximum = float(reflected.max())
        if local_maximum > reflected_maximum[entity]:
            offset_max = int(np.argmax(reflected))
            reflected_maximum_position[entity] = prior + offset_max + 1
        reflected_current[entity] = reflected[-1]
        reflected_maximum[entity] = max(
            reflected_maximum[entity], local_maximum
        )
        reflected_zero_count[entity] += int(np.count_nonzero(reflected == 0.0))
        cumulative_sum[entity] = cumulative[-1]
        strong_maximum[entity] = strong_path[-1]
        exposure_count[entity] = prior + len(raw)
        base.beat("第二遍/封印规则首次告警", sequence + 1, base.N_SEQUENCE, started)
    if int(exposure_count.sum()) != base.N_FLOW or np.any(attribution > 3):
        raise InputContractError("第二遍告警重放未覆盖全部源年流")
    return {
        "exposures": exposures,
        "alert_times": alert_times,
        "attribution": attribution,
        "atomic_mean": cumulative_sum / exposure_count,
        "strong_maximum": strong_maximum,
        "reflected_maximum": reflected_maximum,
        "reflected_zero_count": reflected_zero_count,
        "reflected_maximum_position": reflected_maximum_position,
        "exposure_count": exposure_count,
        "direction_index": direction_index,
        "kappa": kappa,
    }


def assign_buckets(lengths: Any) -> Any:
    assigned = np.full(len(lengths), -1, np.int8)
    for index, (_, lower, upper) in enumerate(BUCKETS):
        mask = lengths >= lower
        if upper is not None:
            mask &= lengths <= upper
        if np.any((assigned >= 0) & mask):
            raise InputContractError("最终长度桶重叠")
        assigned[mask] = index
    if np.any(assigned < 0):
        raise InputContractError("最终长度桶未覆盖全部实体")
    return assigned


def four_grid(labels: Any, m1: Any, j1: Any, selection: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for label, name in ((0, "negative"), (1, "positive")):
        mask = selection & (labels == label)
        result[name] = {
            "J1_only": int((mask & j1 & ~m1).sum()),
            "M1_only": int((mask & m1 & ~j1).sum()),
            "both": int((mask & m1 & j1).sum()),
            "neither": int((mask & ~m1 & ~j1).sum()),
        }
    return result


def paired_difference(values: Any) -> dict[str, Any]:
    array = np.asarray(values, np.float64)
    return {
        "count": int(len(array)),
        "earlier_count": int((array < 0).sum()),
        "equal_count": int((array == 0).sum()),
        "later_count": int((array > 0).sum()),
        "mean": float(array.mean()) if len(array) else None,
        "median": float(np.median(array)) if len(array) else None,
        "maximum_absolute_difference": float(np.abs(array).max())
        if len(array)
        else None,
    }


def build_aggregate_results(
    config: dict[str, Any],
    labels: Any,
    lengths: Any,
    first_time: Any,
    specs: list[dict[str, Any]],
    certificate: dict[str, Any],
    replay: dict[str, Any],
    parent_result: dict[str, Any],
    parent_missed: Any,
    challenge: Any,
    wall_started: float,
) -> dict[str, Any]:
    exposures = replay["exposures"]
    alert_times = replay["alert_times"]
    alerts = {name: exposure > 0 for name, exposure in exposures.items()}
    bucket_ids = assign_buckets(lengths)
    all_entities = np.ones(base.N_ENTITY, np.bool_)
    overall = {
        name: {
            "metrics": metric_counts(labels, alerts[name], all_entities),
            "first_alert": first_alert_summary(
                all_entities, exposures[name], alert_times[name], first_time
            ),
        }
        for name in METHODS
    }
    directions: list[dict[str, Any]] = []
    for spec in specs:
        evaluation = spec["evaluation_mask"]
        method_results = {
            name: {
                "metrics": metric_counts(labels, alerts[name], evaluation),
                "first_alert": first_alert_summary(
                    evaluation, exposures[name], alert_times[name], first_time
                ),
            }
            for name in METHODS
        }
        bucket_results: list[dict[str, Any]] = []
        for bucket_index, (bucket_name, lower, upper) in enumerate(BUCKETS):
            selection = evaluation & (bucket_ids == bucket_index)
            bucket_results.append(
                {
                    "bucket": bucket_name,
                    "minimum_length": lower,
                    "maximum_length": upper,
                    "methods": {
                        name: {
                            "metrics": metric_counts(labels, alerts[name], selection),
                            "first_alert": first_alert_summary(
                                selection,
                                exposures[name],
                                alert_times[name],
                                first_time,
                            ),
                        }
                        for name in METHODS
                    },
                }
            )
        directions.append(
            {
                "direction_id": spec["direction_id"],
                "model_fold": spec["model_fold"],
                "rotation": spec["rotation"],
                "evaluation_entity_count": int(evaluation.sum()),
                "methods": method_results,
                "m1_j1_four_grid": four_grid(
                    labels, alerts["M1"], alerts["J1"], evaluation
                ),
                "length_buckets": bucket_results,
            }
        )
    pooled_buckets: list[dict[str, Any]] = []
    for bucket_index, (bucket_name, lower, upper) in enumerate(BUCKETS):
        selection = bucket_ids == bucket_index
        pooled_buckets.append(
            {
                "bucket": bucket_name,
                "minimum_length": lower,
                "maximum_length": upper,
                "methods": {
                    name: metric_counts(labels, alerts[name], selection)
                    for name in METHODS
                },
            }
        )
    positive_common = (labels == 1) & alerts["M1"] & alerts["J1"]
    exposure_difference = (
        exposures["J1"][positive_common] - exposures["M1"][positive_common]
    )
    normalized_difference = (
        exposures["J1"][positive_common] / lengths[positive_common]
        - exposures["M1"][positive_common] / lengths[positive_common]
    )
    time_difference = (
        alert_times["J1"][positive_common] - alert_times["M1"][positive_common]
    )
    grid = four_grid(labels, alerts["M1"], alerts["J1"], all_entities)
    attribution_names = {
        0: "never_alerted",
        1: "reflected_only",
        2: "strong_only",
        3: "both_branches",
    }
    reflected_new_tp = int(
        (
            (labels == 1)
            & alerts["J1"]
            & ~alerts["M1"]
            & (replay["attribution"] == 1)
        ).sum()
    )
    reflected_tp = int(
        ((labels == 1) & alerts["J1"] & (replay["attribution"] == 1)).sum()
    )
    reflected_fp = int(
        ((labels == 0) & alerts["J1"] & (replay["attribution"] == 1)).sum()
    )
    near_index = int(np.flatnonzero(challenge)[0])
    challenge_attribution = attribution_names[int(replay["attribution"][near_index])]
    other_missed = parent_missed & ~challenge
    long_bucket_gates: dict[str, bool] = {}
    for bucket in pooled_buckets:
        if bucket["bucket"] in {"101-1000", "1001+"}:
            j1_fpr = bucket["methods"]["J1"]["entity_fpr"]
            m1_fpr = bucket["methods"]["M1"]["entity_fpr"]
            long_bucket_gates[bucket["bucket"]] = bool(
                j1_fpr is not None
                and m1_fpr is not None
                and j1_fpr <= Q
                and j1_fpr <= m1_fpr
            )
    paired_exposure = paired_difference(exposure_difference)
    paired_normalized = paired_difference(normalized_difference)
    gates = {
        "all_nine_joint_tong_certificates_valid": certificate[
            "all_joint_certificates_valid"
        ],
        "pooled_J1_FPR_le_0_04": overall["J1"]["metrics"]["entity_fpr"] <= Q,
        "both_long_buckets_J1_FPR_le_0_04_and_not_above_M1": all(
            long_bucket_gates.values()
        )
        and len(long_bucket_gates) == 2,
        "M1_only_TP_eq_0": grid["positive"]["M1_only"] == 0,
        "J1_adds_at_least_one_TP_with_reflected_only_new_TP": (
            grid["positive"]["J1_only"] >= 1 and reflected_new_tp >= 1
        ),
        "A1_and_J1_recover_unique_near_threshold_challenge_with_reflected_only_J1": (
            bool(alerts["A1"][near_index])
            and bool(alerts["J1"][near_index])
            and challenge_attribution == "reflected_only"
        ),
        "paired_common_TP_median_alert_position_not_later": (
            paired_exposure["median"] is not None
            and paired_normalized["median"] is not None
            and paired_exposure["median"] <= 0
            and paired_normalized["median"] <= 0
        ),
    }
    qualified = all(gates.values())
    scientific_status = (
        config["qualification_status"] if qualified else config["rejection_status"]
    )
    increments = replay["atomic_mean"] - replay["kappa"]
    runtime_diagnostics: dict[str, Any] = {}
    for label, name in ((0, "benign"), (1, "positive")):
        mask = labels == label
        runtime_diagnostics[name] = {
            "mean_single_step_increment": distribution(increments[mask]),
            "reflected_zero_count": distribution(
                replay["reflected_zero_count"][mask]
            ),
            "reflected_path_maximum_position": distribution(
                replay["reflected_maximum_position"][mask]
            ),
        }
    return {
        "schema_version": "ch4-xgb-reflected-cumulative-dual-evidence-aggregate-v1",
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
        "parent_reproduction": parent_result,
        "overall": overall,
        "directions": directions,
        "pooled_length_buckets": pooled_buckets,
        "m1_j1_four_grid": grid,
        "m1_j1_unique_true_positive_counts": {
            "J1_only_TP": grid["positive"]["J1_only"],
            "M1_only_TP": grid["positive"]["M1_only"],
            "both_TP": grid["positive"]["both"],
            "neither_positive": grid["positive"]["neither"],
            "reflected_only_driven_J1_only_TP": reflected_new_tp,
        },
        "parent_m1_missed_challenge": {
            "parent_missed_positive_count": 4,
            "unique_near_threshold_challenge": {
                "entity_count": 1,
                "path_maximum_over_parent_threshold": config[
                    "near_threshold_challenge_ratio"
                ],
                "A1_detected": bool(alerts["A1"][near_index]),
                "J1_detected": bool(alerts["J1"][near_index]),
                "J1_first_crossing_attribution": challenge_attribution,
            },
            "other_three_exploratory_aggregate": {
                "entity_count": 3,
                "A1_detected_count": int((other_missed & alerts["A1"]).sum()),
                "J1_detected_count": int((other_missed & alerts["J1"]).sum()),
                "J1_first_crossing_attribution_counts": {
                    name: int(
                        (other_missed & (replay["attribution"] == code)).sum()
                    )
                    for code, name in attribution_names.items()
                },
            },
        },
        "common_positive_first_alert_paired_difference_J1_minus_M1": {
            "exposure_position": paired_exposure,
            "normalized_position": paired_normalized,
            "raw_time_delay": paired_difference(time_difference),
        },
        "joint_first_crossing_attribution": {
            "reflected_only_TP": reflected_tp,
            "reflected_only_FP": reflected_fp,
            "all_alerted_counts": {
                name: int((alerts["J1"] & (replay["attribution"] == code)).sum())
                for code, name in attribution_names.items()
            },
        },
        "runtime_diagnostics": {
            **runtime_diagnostics,
            "online_reflected_state_bytes_per_entity": 16,
            "scored_flow_count_across_two_passes": 2 * base.N_FLOW,
            "throughput_flows_per_second": (2 * base.N_FLOW)
            / max(time.time() - wall_started, 1e-9),
            "prediction_device": "cpu",
            "cuda_peak_bytes": 0,
        },
        "mechanical_verdict": {
            "scientific_status": scientific_status,
            "qualified": qualified,
            "gates": gates,
            "failed_gates": [name for name, passed in gates.items() if not passed],
            "claim_boundary": (
                "仅裁决LSPR23种子42零训练源年Q0；不构成跨年度、多种子、正式论文或部署证据"
            ),
        },
        "integrity": {
            "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
            "models_trained": MODELS_TRAINED,
            "oof_models_loaded": 3,
            "model_load_operations": 3,
            "score_pass_count": 2,
            "flow_coverage_count_per_pass": base.N_FLOW,
            "evaluation_entity_count": base.N_ENTITY,
            "per_flow_scores_persisted": 0,
            "per_entity_scores_persisted": 0,
            "entity_keys_persisted": 0,
            "length_used_online": False,
            "certificate_sealed_before_evaluation_metrics": True,
        },
    }


def resource_summary(started: float, score_passes: int) -> dict[str, Any]:
    maximum_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_host_bytes = int(maximum_rss * (1 if sys.platform == "darwin" else 1024))
    wall = time.time() - started
    return {
        "schema_version": "ch4-xgb-reflected-cumulative-dual-evidence-resource-v1",
        "run_id": RUN_ID,
        "wall_seconds": wall,
        "peak_host_rss_bytes": peak_host_bytes,
        "prediction_device": "cpu",
        "cuda_peak_allocated_bytes": 0,
        "cuda_peak_reserved_bytes": 0,
        "score_pass_count": score_passes,
        "scored_flow_count": score_passes * base.N_FLOW,
        "throughput_flows_per_second": (score_passes * base.N_FLOW)
        / max(wall, 1e-9),
        "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
        "models_trained": MODELS_TRAINED,
    }


def write_final_artifacts(
    args: argparse.Namespace,
    config: dict[str, Any],
    aggregate: dict[str, Any],
    input_receipt: dict[str, Any],
    started: float,
    score_passes: int,
) -> None:
    cleanup_p1_checkpoint(args.out)
    aggregate_path = args.out / "aggregate-results.json"
    atomic_json(aggregate_path, aggregate)
    input_path = args.out / "input-receipt.json"
    atomic_json(input_path, input_receipt)
    resource_path = args.out / "resource-summary.json"
    atomic_json(resource_path, resource_summary(started, score_passes))
    manifest_names = (
        "aggregate-results.json",
        "certificate-receipt.json",
        "input-receipt.json",
        "resource-summary.json",
    )
    manifest = {
        "schema_version": "ch4-xgb-reflected-cumulative-dual-evidence-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": base.sha256_file(Path(__file__).resolve()),
        "config_sha256": base.sha256_file(args.config.resolve()),
        "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
        "models_trained": MODELS_TRAINED,
        "entity_keys_persisted": 0,
        "per_flow_scores_persisted": 0,
        "per_entity_scores_persisted": 0,
        "allowed_outputs": config["artifact_policy"]["allowed_outputs"],
        "files": {},
    }
    for name in manifest_names:
        path = args.out / name
        if not path.is_file() or path.stat().st_size <= 0:
            raise InputContractError(f"必需聚合制品缺失：{name}")
        manifest["files"][name] = {
            "bytes": path.stat().st_size,
            "sha256": base.sha256_file(path),
        }
    atomic_json(args.out / "manifest.json", manifest)


def run(args: argparse.Namespace, config: dict[str, Any]) -> None:
    load_runtime_dependencies()
    diagnostic_receipt = validate_diagnostic(
        args.qualification_diagnostic_root.resolve(), config
    )
    parent_m1 = validate_parent_m1(args.parent_m1_summary.resolve(), config)
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
        print("CH4_REFLECTED_ACCUMULATION_JOINT_TONG_INPUTS_VALID", flush=True)
        return
    protected = (
        "aggregate-results.json",
        "certificate-receipt.json",
        "input-receipt.json",
        "manifest.json",
        "resource-summary.json",
    )
    if any((args.out / name).exists() for name in protected):
        raise InputContractError(f"同名 Q0 制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    base.log("阶段P0：只读加载LSPR23并封印折号、角色、模型和资格诊断")
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
    groups, grouping_receipts = stable_role_groups(fold_of_entity, entity_labels)

    import xgboost as xgb

    if xgb.__version__ != "3.2.0":
        raise InputContractError(f"XGBoost版本不符：{xgb.__version__}")
    model_identities = source_model_identities(
        args.parent_run_root.resolve(), seal
    )
    checkpoint_identity = p1_checkpoint_identity(
        args,
        parent,
        diagnostic_receipt,
        array_receipts,
        model_identities,
        fold_sha,
        grouping_receipts,
    )
    restored = load_p1_checkpoint(
        args.resume_run_root.resolve(),
        checkpoint_identity,
        entity_lengths,
        expected_run_id=SOURCE_RUN_ID,
        source_checkpoint=True,
    )
    if restored is None:
        restored = load_p1_checkpoint(args.out, checkpoint_identity, entity_lengths)
    semantic = None
    boosters = None
    model_receipts = model_identities
    if restored is None:
        base.log("阶段P1：构造semantic168并执行第一遍CPU折外评分")
        semantic = base.build_semantic_matrix(base.CACHE / "X23.npy", indices, masks)
        boosters, model_receipts = load_cpu_boosters(
            xgb, args.parent_run_root.resolve(), seal
        )
        first_raw = score_all_flows(
            boosters,
            semantic,
            indices,
            masks,
            sequence_entities,
            fold_of_entity,
            int(base_config["sequence_batch"]),
            "第一遍CPU折外评分",
        )
        first_stats = first_pass_path_statistics(
            first_raw, indices, masks, sequence_entities
        )
        if not np.array_equal(first_stats["exposure_count"], entity_lengths):
            raise InputContractError("第一遍曝光数与最终长度不符")
    else:
        first_stats, reflected_first, _ = restored
        base.log("阶段P1：检查点身份与内容核验通过，直接从P2恢复")
    parent_result, parent_missed, challenge = parent_reproduction(
        parent_m1,
        fold_of_entity,
        entity_labels,
        first_stats["first_scores"],
        first_stats["path_maximum"],
    )
    specs, kappas, orientation_failures = build_direction_specs(
        fold_of_entity, groups, entity_labels, first_stats["atomic_mean"]
    )
    input_receipt = {
        "schema_version": "ch4-xgb-reflected-cumulative-dual-evidence-input-v1",
        "run_id": RUN_ID,
        "script_sha256": base.sha256_file(Path(__file__).resolve()),
        "config_sha256": base.sha256_file(args.config.resolve()),
        "qualification_diagnostic": diagnostic_receipt,
        "parent_m1_summary": {
            "path": str(args.parent_m1_summary.resolve()),
            "sha256": config["parent_m1_summary"]["sha256"],
        },
        "parent_model_run": parent,
        "arrays": array_receipts,
        "fold_assignment_sha256": fold_sha,
        "entity_key_sha256": base.sha256_array(structure["entity_ids"]),
        "role_grouping_receipts": grouping_receipts,
        "source_model_receipts": model_receipts,
        "source_year": "LSPR23",
        "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
        "models_trained": MODELS_TRAINED,
        "oof_models_loaded": len(model_receipts),
        "per_flow_scores_persisted": 0,
        "per_entity_scores_persisted": 0,
        "entity_keys_persisted": 0,
    }
    if orientation_failures:
        certificate = {
            "schema_version": "ch4-xgb-reflected-cumulative-dual-evidence-certificate-v1",
            "run_id": RUN_ID,
            "scientific_status": config["drift_rejection_status"],
            "evaluation_metrics_computed_before_seal": False,
            "evaluation_metrics_computed": False,
            "failed_directions": orientation_failures,
            "directions": [
                {
                    key: value
                    for key, value in spec.items()
                    if not key.endswith("_mask")
                }
                for spec in specs
            ],
        }
        atomic_json(args.out / "certificate-receipt.json", certificate)
        aggregate = {
            "schema_version": "ch4-xgb-reflected-cumulative-dual-evidence-aggregate-v1",
            "run_id": RUN_ID,
            "parent_reproduction": parent_result,
            "mechanical_verdict": {
                "scientific_status": config["drift_rejection_status"],
                "qualified": False,
                "failed_directions": orientation_failures,
                "evaluation_metrics_opened": False,
            },
            "integrity": {
                "target_year_arrays_read": base.TARGET_YEAR_ARRAYS_READ,
                "models_trained": MODELS_TRAINED,
                "per_flow_scores_persisted": 0,
                "per_entity_scores_persisted": 0,
                "entity_keys_persisted": 0,
            },
        }
        if restored is None:
            del first_raw
        write_final_artifacts(args, config, aggregate, input_receipt, started, 1)
        base.log(f"科学否决：{config['drift_rejection_status']}")
        return

    if restored is None:
        reflected_first = reflected_final_statistics(
            first_raw,
            indices,
            masks,
            sequence_entities,
            fold_of_entity,
            kappas,
        )
        del first_raw
        write_p1_checkpoint(
            args.out,
            checkpoint_identity,
            first_stats,
            reflected_first,
        )
        base.log("阶段P1：实体级原子检查点已持久化，可从P2恢复")

    base.log("阶段P2：只用开发与校准角色封印九方向M1和联合Tong证书")
    certificate, runtime_directions = seal_certificates(
        specs,
        entity_labels,
        first_stats["path_maximum"],
        reflected_first["path_maximum"],
        config,
    )
    atomic_json(args.out / "certificate-receipt.json", certificate)

    base.log("阶段P3：执行第二遍CPU折外评分并按封印阈值计算首次告警")
    if semantic is None:
        semantic = base.build_semantic_matrix(base.CACHE / "X23.npy", indices, masks)
    if boosters is None:
        boosters, model_receipts = load_cpu_boosters(
            xgb, args.parent_run_root.resolve(), seal
        )
    second_raw = score_all_flows(
        boosters,
        semantic,
        indices,
        masks,
        sequence_entities,
        fold_of_entity,
        int(base_config["sequence_batch"]),
        "第二遍CPU折外评分",
    )
    replay = second_pass_alerts(
        second_raw,
        indices,
        masks,
        sequence_entities,
        flow_times,
        fold_of_entity,
        groups,
        runtime_directions,
    )
    del second_raw, semantic, boosters
    if not np.array_equal(replay["exposure_count"], entity_lengths):
        raise InputContractError("第二遍曝光数与封印最终长度不符")

    base.log("阶段P4：只在规则封印后计算九方向、五桶、归因与七项机械门")
    aggregate = build_aggregate_results(
        config,
        entity_labels,
        entity_lengths,
        np.asarray(structure["first_time"], np.float64),
        specs,
        certificate,
        replay,
        parent_result,
        parent_missed,
        challenge,
        started,
    )
    write_final_artifacts(args, config, aggregate, input_receipt, started, 2)
    base.log(
        "Q0完成："
        f"status={aggregate['mechanical_verdict']['scientific_status']} "
        f"J1_FPR={aggregate['overall']['J1']['metrics']['entity_fpr']:.10f} "
        f"J1_DR={aggregate['overall']['J1']['metrics']['detection_rate']:.10f}"
    )


def main() -> int:
    args = parse_args()
    try:
        if not args.config.is_file():
            raise InputContractError(f"配置缺失：{args.config}")
        config = load_json(args.config)
        validate_config(config)
        if args.validate_config:
            print("CH4_REFLECTED_ACCUMULATION_JOINT_TONG_CONFIG_VALID", flush=True)
            return 0
        run(args, config)
        return 0
    except InputContractError as error:
        print(f"INVALID_INPUT_CONTRACT: {error}", file=sys.stderr, flush=True)
        return 78
    except Exception as error:
        if base is not None and isinstance(error, base.InputContractError):
            print(f"INVALID_INPUT_CONTRACT: {error}", file=sys.stderr, flush=True)
            return 78
        raise


if __name__ == "__main__":
    raise SystemExit(main())
