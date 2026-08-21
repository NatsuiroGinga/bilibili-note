#!/usr/bin/env python3
"""为冻结 XGBoost＋CPA-ELP C11 回填完整目标年运营指标。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DIJK_MODULE_ROOT = ROOT / "tools/dijk2026_replication"
if str(DIJK_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(DIJK_MODULE_ROOT))

from dijk_fields import DIJK_FEATURES  # noqa: E402


RUN_ID = "ch3-xgb-cpa-elp-c11-operational-backfill-v1"
DISPLAY_NAME = "XGBoost＋CPA-ELP C11目标年完整运营指标零训练回填"
PARENT_RUN_ID = "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
PARENT_EVAL_RUN_ID = f"{PARENT_RUN_ID}-eval-continuation2"
RECOVERY_SCHEMA = "ch3-xgb-parent-recovery-proof-v1"
TARGET_ARRAYS = ("X24", "y24", "I24", "M24", "s24", "d24", "t24")
FPR_BUDGETS = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)
FIRST_ALERT_QUANTILES = (0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0)
EXPECTED_HASHES = {
    "selection_frozen_xgb2x2.json": "a9075653efc6b29b6eb9d72f04409781af18e7c65cb31c1ba9bac941e1293943",
    "effective_config_receipts.json": "657c9f88b3c37f15e48817b145ad8bb22b8f4edd5ba700742b945c84c413515d",
    "model_semantic168.json": "1805e15d96ac4ebb57df910640a4c5e1af58f692659db2eb80b724851efe42e9",
    "parent_evaluation_result": "128b1225c96bb07c5b808dc2e0092223d1acb4c039b487a7007551a4f6b5135f",
    "parent_evaluation_manifest": "f6b66cc94ef09b169ff29ce317464109bc701fa109875f6e9b7d09c889516115",
}
N_FLOW = 20_227_356
N_SEQUENCE_WIDTH = 128
N_RAW_FEATURE = 83
N_SEMANTIC_FEATURE = 168
N_ENTITY = 47_115
N_POSITIVE_ENTITY = 752
FLOW_POSITIVE_RATE = 0.0257073138
N_TREE = 800
CELL = "C11"

CATEGORICAL_NAMES = (
    "SrcPort",
    "DstPort",
    "Protocol",
    "L3/L4 Protocol",
    "Int/Ext Dst IP",
)
BOOLEAN_NAMES = ("External_src", "External_dst")
CATEGORICAL_IDX = tuple(DIJK_FEATURES.index(name) for name in CATEGORICAL_NAMES)
BOOLEAN_IDX = tuple(DIJK_FEATURES.index(name) for name in BOOLEAN_NAMES)
NUMERIC_IDX = tuple(
    index
    for index in range(len(DIJK_FEATURES))
    if index not in CATEGORICAL_IDX and index not in BOOLEAN_IDX
)
if len(DIJK_FEATURES) != N_RAW_FEATURE or len(NUMERIC_IDX) != 76:
    raise RuntimeError("Dijk 83 字段或 semantic168 派生索引不符")

T0 = time.time()
LAST_BEAT = [T0]
np: Any = None
average_precision_score: Any = None
roc_auc_score: Any = None


def load_numeric_dependencies() -> None:
    """静态入口不加载训练依赖；计算阶段才加载冻结环境中的数值库。"""
    global np, average_precision_score, roc_auc_score
    if np is not None:
        return
    import numpy as numpy_module
    from sklearn.metrics import average_precision_score as average_precision_score_function
    from sklearn.metrics import roc_auc_score as roc_auc_score_function

    np = numpy_module
    average_precision_score = average_precision_score_function
    roc_auc_score = roc_auc_score_function


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    now = time.time()
    if now - LAST_BEAT[0] < every and done < total:
        return
    LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    remaining = (total - done) / max(rate, 1e-9)
    log(
        f"[{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {remaining:.0f}s"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def atomic_npz(path: Path, vectors: Mapping[str, np.ndarray]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **vectors)
    os.replace(temporary, path)
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "fields": list(vectors),
    }


def artifact_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"制品缺失或为空：{path}")
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_stage_status(output_root: Path, stage: str, detail: str) -> None:
    atomic_json(
        output_root / "stage-status.json",
        {
            "schema_version": "ch3-xgb-cpa-elp-operational-backfill-stage-status-v1",
            "run_id": RUN_ID,
            "stage": stage,
            "detail": detail,
            "updated_at_unix": time.time(),
            "target_retrained": False,
            "target_scores_persisted": False,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/ch3-xgb-cpa-elp-operational-backfill-v1.json",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--compute", action="store_true", help="计算并原子发布聚合制品")
    mode.add_argument("--finalize", action="store_true", help="资源采样结束后发布跟踪收据和清单")
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--resource-receipt", type=Path)
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    expected_top = {
        "schema_version": "ch3-xgb-cpa-elp-operational-backfill-config-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "seed": 42,
        "screening_only": False,
        "formal_paper_evidence": False,
        "target_previously_accessed": True,
        "independent_test": False,
    }
    for key, expected in expected_top.items():
        if config.get(key) != expected:
            raise SystemExit(f"配置字段不符：{key}")
    if tuple(config.get("target_arrays", [])) != TARGET_ARRAYS:
        raise SystemExit("目标缓存必须恰为 X24/y24/I24/M24/s24/d24/t24")
    parent = config.get("parent_contract", {})
    expected_parent = {
        "run_id": PARENT_RUN_ID,
        "evaluation_run_id": PARENT_EVAL_RUN_ID,
        "recovery_proof_schema": RECOVERY_SCHEMA,
        "selection_sha256": EXPECTED_HASHES["selection_frozen_xgb2x2.json"],
        "effective_config_receipts_sha256": EXPECTED_HASHES[
            "effective_config_receipts.json"
        ],
        "semantic168_model_sha256": EXPECTED_HASHES["model_semantic168.json"],
        "evaluation_result_sha256": EXPECTED_HASHES["parent_evaluation_result"],
        "evaluation_manifest_sha256": EXPECTED_HASHES["parent_evaluation_manifest"],
        "selected_adapter": "semantic168",
        "power_mean_p": 1.0,
        "num_boost_round": N_TREE,
        "target_retrained": False,
        "target_score_calls": 1,
        "target_scores_persisted": False,
    }
    if parent != expected_parent:
        raise SystemExit("父运行或零训练身份合同不符")
    target = config.get("target_contract", {})
    expected_target = {
        "dataset": "LSPR24",
        "flow_count": N_FLOW,
        "sequence_length": N_SEQUENCE_WIDTH,
        "raw_feature_count": N_RAW_FEATURE,
        "semantic_feature_count": N_SEMANTIC_FEATURE,
        "entity_count": N_ENTITY,
        "positive_entity_count": N_POSITIVE_ENTITY,
        "flow_positive_rate": FLOW_POSITIVE_RATE,
        "entity_key": "unordered_source_destination_address_pair",
        "exposure_order": "ascending_frozen_flow_index_within_entity",
        "time_order_required": True,
        "target_used_for_selection_or_tuning": False,
    }
    if target != expected_target:
        raise SystemExit("LSPR24 冻结目标合同不符")
    evaluation = config.get("evaluation", {})
    if (
        evaluation.get("cell") != CELL
        or tuple(evaluation.get("fpr_budgets", [])) != FPR_BUDGETS
        or tuple(evaluation.get("first_alert_quantiles", [])) != FIRST_ALERT_QUANTILES
        or evaluation.get("complete_curve")
        != "all_reachable_complete_negative_tie_groups"
        or evaluation.get("budget_readout")
        != "largest_realized_fpr_not_exceeding_nominal_budget"
        or evaluation.get("nominal_point_interpolation") is not False
        or evaluation.get("first_alert_axis") != "exposure_index"
        or evaluation.get("exposure_index_base") != 1
        or evaluation.get("first_alert_threshold_semantics")
        != "same_complete_tied_score_group_greater_equal"
        or evaluation.get("time_delay_available") is not False
        or int(evaluation.get("predict_batch", 0)) <= 0
        or int(evaluation.get("sequence_batch", 0)) <= 0
    ):
        raise SystemExit("运营评价合同不符")
    resources = config.get("resource_contract", {})
    if resources != {
        "minimum_free_gpu_memory_gib": 11,
        "minimum_cgroup_available_memory_gib": 48,
        "minimum_free_disk_gib": 10,
        "maximum_disk_used_percent": 79,
        "maximum_parallel_units": 1,
        "wall_clock_limit": None,
        "stage_atomic_resume": True,
    }:
        raise SystemExit("资源或无时长上限合同不符")
    if config.get("tracking") != {
        "workspace": "mortiswang",
        "project": "ns3-rwkv-lspr24",
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 授权目的地或聚合模式不符")
    if config.get("artifact_policy") != {
        "persist_aggregate_json": True,
        "persist_complete_budget_curve": True,
        "persist_first_alert_aggregate_curve": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_per_entity_first_alert": False,
        "persist_derived_matrices": False,
        "persist_new_models": False,
    }:
        raise SystemExit("制品持久化合同不符")
    paths = config.get("paths", {})
    required_paths = {
        "cache_root",
        "parent_run_root",
        "parent_config",
        "parent_recovery_proof",
        "parent_evaluation_root",
        "output_root",
    }
    if set(paths) != required_paths or Path(paths["output_root"]).name != RUN_ID:
        raise SystemExit("路径清单或输出身份不符")


def validate_manifest_files(root: Path, manifest: Mapping[str, Any]) -> None:
    files = manifest.get("files", {})
    if not isinstance(files, dict) or not files:
        raise RuntimeError("manifest 文件清单为空")
    for name, receipt in files.items():
        path = root / name
        if (
            not path.is_file()
            or path.stat().st_size != receipt.get("bytes")
            or sha256_file(path) != receipt.get("sha256")
        ):
            raise RuntimeError(f"manifest 制品不完整或摘要不符：{name}")


def validate_parent_and_cache(config: dict[str, Any]) -> dict[str, Any]:
    paths = config["paths"]
    parent_root = Path(paths["parent_run_root"]).resolve()
    parent_eval_root = Path(paths["parent_evaluation_root"]).resolve()
    parent_config_path = Path(paths["parent_config"]).resolve()
    proof_path = Path(paths["parent_recovery_proof"]).resolve()
    cache_root = Path(paths["cache_root"]).resolve()
    if parent_root.name != PARENT_RUN_ID or parent_eval_root.name != PARENT_EVAL_RUN_ID:
        raise SystemExit("父训练或父评价运行目录身份不符")

    proof = load_json(proof_path)
    if (
        proof.get("schema_version") != RECOVERY_SCHEMA
        or proof.get("parent_run_id") != PARENT_RUN_ID
        or Path(str(proof.get("parent_run_root", ""))).resolve() != parent_root
        or proof.get("sourced_from_existing_parent_artifacts_only") is not True
        or proof.get("does_not_assert_parent_completion") is not True
        or proof.get("parent_state", {}).get("complete") is not False
    ):
        raise SystemExit("父恢复证明身份或未完成事实不符")

    parent_artifacts: dict[str, Any] = {}
    proof_artifacts = proof.get("artifacts", {})
    for name in (
        "selection_frozen_xgb2x2.json",
        "effective_config_receipts.json",
        "model_semantic168.json",
    ):
        path = parent_root / name
        expected = EXPECTED_HASHES[name]
        actual = sha256_file(path)
        proof_receipt = proof_artifacts.get(name, {})
        if (
            actual != expected
            or proof_receipt.get("sha256") != actual
            or proof_receipt.get("bytes") != path.stat().st_size
        ):
            raise SystemExit(f"父制品固定摘要或恢复证明不符：{name}")
        if name == "model_semantic168.json" and proof_receipt.get(
            "num_boosted_rounds"
        ) != N_TREE:
            raise SystemExit("恢复证明中的 semantic168 最终模型不是 800 树")
        parent_artifacts[name] = artifact_receipt(path)

    selection = load_json(parent_root / "selection_frozen_xgb2x2.json")
    effective = load_json(parent_root / "effective_config_receipts.json")
    if (
        selection.get("run_name") != PARENT_RUN_ID
        or selection.get("adapter_selection", {}).get("selected") != "semantic168"
        or float(
            selection.get("p_selection", {})
            .get("semantic168", {})
            .get("p_selected", math.nan)
        )
        != 1.0
        or int(
            selection.get("final_models", {})
            .get("semantic168", {})
            .get("n_tree", -1)
        )
        != N_TREE
    ):
        raise SystemExit("父选择不是 semantic168、p=1、800 树")
    if (
        not isinstance(effective, list)
        or len(effective) != 11
        or any(not isinstance(item, dict) or item.get("passed") is not True for item in effective)
        or not any(item.get("tag") == "semantic168/final" for item in effective)
    ):
        raise SystemExit("父有效配置收据不是完整通过的 11 项")

    result_path = parent_eval_root / "xgb_cpa_elp_results.json"
    manifest_path = parent_eval_root / "manifest.json"
    status_path = parent_eval_root / "status.json"
    if sha256_file(result_path) != EXPECTED_HASHES["parent_evaluation_result"]:
        raise SystemExit("父完成评价结果固定摘要不符")
    if sha256_file(manifest_path) != EXPECTED_HASHES["parent_evaluation_manifest"]:
        raise SystemExit("父完成评价清单固定摘要不符")
    parent_manifest = load_json(manifest_path)
    validate_manifest_files(parent_eval_root, parent_manifest)
    status = load_json(status_path)
    if (
        status.get("state") != "finished"
        or status.get("stage") != "complete"
        or status.get("exit_code") != 0
    ):
        raise SystemExit("父评价未处于 finished/complete/exit=0")
    parent_result = load_json(result_path)
    isolation = parent_result.get("isolation", {})
    continuation = parent_result.get("continuation_receipt", {})
    c11 = parent_result.get("cells", {}).get(CELL, {})
    if (
        isolation.get("source_year_retrained") is not False
        or isolation.get("target_score_calls") != 2
        or isolation.get("target_scores_persisted") is not False
        or continuation.get("parent_run_id") != PARENT_RUN_ID
        or continuation.get("models", {})
        .get("semantic168", {})
        .get("sha256")
        != EXPECTED_HASHES["model_semantic168.json"]
        or c11.get("input_view") != "semantic168"
        or float(c11.get("p", math.nan)) != 1.0
    ):
        raise SystemExit("父完成评价的模型、C11 或目标隔离收据不符")
    parent_config_sha = sha256_file(parent_config_path)
    if continuation.get("parent_config_sha256") != parent_config_sha:
        raise SystemExit("当前父配置与已完成父评价使用的配置摘要不符")
    parent_config = load_json(parent_config_path)
    if (
        parent_config.get("run_id") != PARENT_RUN_ID
        or parent_config.get("num_boost_round") != N_TREE
    ):
        raise SystemExit("父配置运行身份或树数不符")

    cache_files: dict[str, Any] = {}
    for name in TARGET_ARRAYS:
        path = cache_root / f"{name}.npy"
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"目标缓存缺失或为空：{path}")
        started = time.time()
        digest = sha256_file(path)
        cache_files[name] = {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "mtime_ns": path.stat().st_mtime_ns,
            "sha256": digest,
        }
        log(f"目标缓存摘要完成：{name}，用时 {time.time() - started:.1f}s")

    return {
        "parent_run_id": PARENT_RUN_ID,
        "parent_run_root": str(parent_root),
        "parent_config": {
            "path": str(parent_config_path),
            "sha256": parent_config_sha,
        },
        "parent_recovery_proof": {
            "path": str(proof_path),
            "sha256": sha256_file(proof_path),
            "does_not_assert_parent_completion": True,
        },
        "parent_artifacts": parent_artifacts,
        "parent_evaluation": {
            "run_id": PARENT_EVAL_RUN_ID,
            "result_sha256": EXPECTED_HASHES["parent_evaluation_result"],
            "manifest_sha256": EXPECTED_HASHES["parent_evaluation_manifest"],
            "status": {"state": "finished", "stage": "complete", "exit_code": 0},
        },
        "cache_inventory": {
            "arrays": list(TARGET_ARRAYS),
            "files": cache_files,
            "canonical_sha256": canonical_sha256(cache_files),
        },
        "selection": {
            "adapter": "semantic168",
            "power_mean_p": 1.0,
            "num_boost_round": N_TREE,
        },
    }


def load_frozen_model(config: dict[str, Any]) -> tuple[Any, Any, str]:
    import torch
    import xgboost as xgb

    build_info = xgb.build_info()
    if xgb.__version__ != "3.2.0" or build_info.get("USE_CUDA") is not True:
        raise SystemExit(
            f"XGBoost 环境不符：version={xgb.__version__} "
            f"USE_CUDA={build_info.get('USE_CUDA')}"
        )
    if not torch.cuda.is_available():
        raise SystemExit("CUDA 不可用，拒绝以 CPU 冒充 GPU 打分")
    model_path = Path(config["paths"]["parent_run_root"]) / "model_semantic168.json"
    booster = xgb.Booster()
    booster.load_model(model_path)
    if int(booster.num_boosted_rounds()) != N_TREE:
        raise SystemExit("实际加载的 semantic168 最终模型不是 800 树")
    booster.set_param({"device": "cuda:0"})
    saved = json.loads(booster.save_config())
    device = saved["learner"]["generic_param"]["device"]
    if device != "cuda:0":
        raise SystemExit(f"冻结模型推理设备应为 cuda:0，实为 {device}")
    return booster, torch, xgb.__version__


def assert_sequence_time_monotonic(
    time_values: np.ndarray,
    indices: np.ndarray,
    mask_values: np.ndarray,
) -> int:
    if len(time_values) != N_FLOW or not np.isfinite(time_values).all():
        raise SystemExit("LSPR24 时间戳数量异常或含非有限值")
    reversed_pairs = 0
    checked_pairs = 0
    started = time.time()
    for start in range(0, len(indices), 20_000):
        idx = indices[start : start + 20_000]
        valid = mask_values[start : start + 20_000] > 0
        values = time_values[idx]
        adjacent = valid[:, 1:] & valid[:, :-1]
        checked_pairs += int(adjacent.sum())
        reversed_pairs += int(((values[:, 1:] < values[:, :-1]) & adjacent).sum())
        beat("LSPR24/序列时间核验", min(start + 20_000, len(indices)), len(indices), started)
    if reversed_pairs:
        raise SystemExit(f"LSPR24 序列存在 {reversed_pairs} 个时间逆序相邻对")
    return checked_pairs


def assert_entity_time_monotonic(
    time_values: np.ndarray,
    entity: np.ndarray,
) -> tuple[np.ndarray, int]:
    flow_index = np.arange(N_FLOW, dtype=np.int64)
    order = np.lexsort((flow_index, entity))
    ordered_entity = entity[order]
    ordered_time = time_values[order]
    same_entity = ordered_entity[1:] == ordered_entity[:-1]
    reversed_pairs = int(((ordered_time[1:] < ordered_time[:-1]) & same_entity).sum())
    if reversed_pairs:
        raise SystemExit(f"LSPR24 实体内冻结流序存在 {reversed_pairs} 个时间逆序相邻对")
    return order, int(same_entity.sum())


def build_semantic_matrix(
    source: Any,
    indices: np.ndarray,
    mask_values: np.ndarray,
    predict_batch: int,
    sequence_batch: int,
) -> np.ndarray:
    """逐字复现父入口的 semantic168 公式，结果仅驻内存。"""
    if indices.shape[1] != N_SEQUENCE_WIDTH or mask_values.shape != indices.shape:
        raise SystemExit(f"LSPR24 序列形状异常：I={indices.shape} M={mask_values.shape}")
    if int((mask_values > 0).sum()) != N_FLOW:
        raise SystemExit("LSPR24 掩码没有无重无漏覆盖全部流")
    output = np.empty((N_FLOW, N_SEMANTIC_FEATURE), dtype=np.float32)
    if source.shape != (N_FLOW, N_RAW_FEATURE):
        raise SystemExit(f"X24 形状不符：{source.shape}")
    started = time.time()
    for start in range(0, N_FLOW, predict_batch):
        stop = min(start + predict_batch, N_FLOW)
        output[start:stop, :N_RAW_FEATURE] = source[start:stop]
        beat("LSPR24/读入基础83字段", stop, N_FLOW, started)

    cover = np.zeros(N_FLOW, dtype=bool)
    lower = np.tri(N_SEQUENCE_WIDTH, N_SEQUENCE_WIDTH, dtype=bool)
    started = time.time()
    for start in range(0, len(indices), sequence_batch):
        idx = indices[start : start + sequence_batch]
        valid = mask_values[start : start + sequence_batch] > 0
        batch, width = idx.shape
        flat = idx.reshape(-1)
        current = output[flat, :N_RAW_FEATURE].reshape(batch, width, N_RAW_FEATURE)
        count = np.cumsum(valid, axis=1, dtype=np.int32)
        denominator = np.maximum(count, 1).astype(np.float32)
        valid_flat = valid.reshape(-1)
        target = flat[valid_flat]

        numeric = current[:, :, NUMERIC_IDX]
        numeric_sum = np.cumsum(numeric * valid[:, :, None], axis=1, dtype=np.float64)
        residual = numeric - numeric_sum / denominator[:, :, None]
        cursor = N_RAW_FEATURE
        output[target, cursor : cursor + len(NUMERIC_IDX)] = residual.reshape(
            -1, len(NUMERIC_IDX)
        )[valid_flat]
        cursor += len(NUMERIC_IDX)

        prefix_mask = lower[None, :, :] & valid[:, None, :]
        for feature_idx in CATEGORICAL_IDX:
            value = current[:, :, feature_idx]
            equal = value[:, :, None] == value[:, None, :]
            frequency = (equal & prefix_mask).sum(axis=2) / denominator
            output[target, cursor] = frequency.reshape(-1)[valid_flat]
            cursor += 1
        for feature_idx in BOOLEAN_IDX:
            truth = (current[:, :, feature_idx] > 0) & valid
            truth_rate = np.cumsum(truth, axis=1) / denominator
            output[target, cursor] = truth_rate.reshape(-1)[valid_flat]
            cursor += 1
        output[target, cursor] = np.log1p(count).reshape(-1)[valid_flat]
        cursor += 1
        output[target, cursor] = (count == 1).reshape(-1)[valid_flat]
        cursor += 1
        if cursor != N_SEMANTIC_FEATURE:
            raise RuntimeError(f"semantic168 游标异常：{cursor}")
        cover[target] = True
        beat("LSPR24/semantic168", min(start + sequence_batch, len(indices)), len(indices), started)
    if not bool(cover.all()) or not np.isfinite(output).all():
        raise SystemExit("semantic168 覆盖不完整或含非有限值")
    return output


def predict_once(
    booster: Any,
    matrix: np.ndarray,
    batch_size: int,
    torch_module: Any,
) -> tuple[np.ndarray, int]:
    scores = np.empty(len(matrix), dtype=np.float32)
    api_batches = 0
    started = time.time()
    for start in range(0, len(matrix), batch_size):
        stop = min(start + batch_size, len(matrix))
        scores[start:stop] = np.asarray(
            booster.inplace_predict(matrix[start:stop]), dtype=np.float32
        )
        api_batches += 1
        beat("C11/GPU打分", stop, len(matrix), started)
    if not np.isfinite(scores).all():
        raise SystemExit("C11 逐流分数含非有限值")
    torch_module.cuda.empty_cache()
    return scores, api_batches


def entity_mean_scores(
    flow_scores: np.ndarray,
    entity: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    numerator = np.zeros(N_ENTITY, dtype=np.float64)
    count = np.zeros(N_ENTITY, dtype=np.int64)
    np.add.at(numerator, entity, np.clip(flow_scores, 1e-7, 1.0).astype(np.float64))
    np.add.at(count, entity, 1)
    if np.any(count <= 0):
        raise SystemExit("C11 实体聚合存在零曝光实体")
    return (numerator / count).astype(np.float32), count


def complete_tied_budget_curve(
    entity_scores: np.ndarray,
    entity_labels: np.ndarray,
) -> dict[str, np.ndarray]:
    valid = np.isfinite(entity_scores)
    scores = entity_scores[valid].astype(np.float64)
    labels = entity_labels[valid]
    negative = scores[labels == 0]
    positive = np.sort(scores[labels == 1])
    if not len(negative) or not len(positive):
        raise SystemExit("完整预算曲线缺少正类或负类实体")
    unique_ascending, tie_count_ascending = np.unique(negative, return_counts=True)
    thresholds = unique_ascending[::-1]
    tie_counts = tie_count_ascending[::-1].astype(np.int64)
    zero_threshold = np.nextafter(float(thresholds[0]), math.inf)
    thresholds = np.concatenate(([zero_threshold], thresholds)).astype(np.float64)
    tie_counts = np.concatenate(([0], tie_counts)).astype(np.int64)
    false_positive = np.concatenate(([0], np.cumsum(tie_counts[1:], dtype=np.int64)))
    detection = (
        len(positive) - np.searchsorted(positive, thresholds, side="left")
    ) / len(positive)
    realized = false_positive.astype(np.float64) / len(negative)
    return {
        "n_false_positive_entity": false_positive,
        "nominal_fpr": realized.copy(),
        "realized_fpr": realized,
        "detection_rate": detection.astype(np.float64),
        "threshold": thresholds,
        "negative_tie_group_size": tie_counts,
    }


def budget_readouts(curve: Mapping[str, np.ndarray]) -> dict[str, dict[str, Any]]:
    realized = curve["realized_fpr"]
    results: dict[str, dict[str, Any]] = {}
    for budget in FPR_BUDGETS:
        index = int(np.searchsorted(realized, budget, side="right") - 1)
        if index < 0:
            raise RuntimeError("完整曲线缺少零误报可达点")
        key = f"fpr_{budget:g}"
        results[key] = {
            "nominal_fpr": budget,
            "realized_fpr": float(realized[index]),
            "false_positive_entity_count": int(curve["n_false_positive_entity"][index]),
            "detection_rate": float(curve["detection_rate"][index]),
            "threshold": float(curve["threshold"][index]),
            "negative_tie_group_size": int(curve["negative_tie_group_size"][index]),
            "interpolated": False,
        }
    return results


def distribution(values: np.ndarray) -> dict[str, float | int | None]:
    if not len(values):
        return {
            "count": 0,
            "minimum": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "maximum": None,
        }
    points = np.quantile(values.astype(np.float64), FIRST_ALERT_QUANTILES)
    names = ("minimum", "p25", "median", "p75", "p90", "p95", "p99", "maximum")
    return {"count": int(len(values)), **dict(zip(names, map(float, points), strict=True))}


def first_alert_aggregate(
    flow_scores: np.ndarray,
    entity: np.ndarray,
    entity_labels: np.ndarray,
    entity_order: np.ndarray,
    entity_counts: np.ndarray,
    readouts: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    ordered_entity = entity[entity_order]
    ordered_scores = np.clip(
        flow_scores[entity_order].astype(np.float64), 1e-7, 1.0
    )
    starts = np.flatnonzero(np.r_[True, ordered_entity[1:] != ordered_entity[:-1]])
    lengths = np.diff(np.r_[starts, len(ordered_entity)]).astype(np.int64)
    exposure_index = (
        np.arange(len(ordered_entity), dtype=np.int64) - np.repeat(starts, lengths) + 1
    )
    cumulative = np.cumsum(ordered_scores, dtype=np.float64)
    previous = np.zeros(len(starts), dtype=np.float64)
    previous[1:] = cumulative[starts[1:] - 1]
    running_scores = (cumulative - np.repeat(previous, lengths)) / exposure_index

    positive = entity_labels == 1
    benign = entity_labels == 0
    positive_count = int(positive.sum())
    benign_count = int(benign.sum())
    summaries: dict[str, Any] = {}
    vectors: dict[str, np.ndarray] = {}
    unalerted: dict[str, float] = {}
    realized_first_alert: dict[str, float] = {}
    for key, readout in readouts.items():
        threshold = float(readout["threshold"])
        crossing = np.flatnonzero(running_scores >= threshold)
        crossing_entity = ordered_entity[crossing]
        unique_entity, first_positions = np.unique(crossing_entity, return_index=True)
        first_crossing = crossing[first_positions]
        first_alert = np.zeros(N_ENTITY, dtype=np.int64)
        first_alert[unique_entity] = exposure_index[first_crossing]

        alerted_positive = positive & (first_alert > 0)
        alerted_benign = benign & (first_alert > 0)
        positive_positions = first_alert[alerted_positive]
        axis = np.unique(
            np.concatenate(
                (
                    np.array([0], dtype=np.int64),
                    positive_positions,
                    np.array([int(entity_counts[positive].max())], dtype=np.int64),
                )
            )
        )
        rate = np.array(
            [
                float(((first_alert > 0) & positive & (first_alert <= point)).sum())
                / positive_count
                for point in axis
            ],
            dtype=np.float64,
        )
        positive_unalerted_rate = float((positive & (first_alert == 0)).sum() / positive_count)
        actual_first_alert_fpr = float(alerted_benign.sum() / benign_count)
        unalerted[key] = positive_unalerted_rate
        realized_first_alert[key] = actual_first_alert_fpr
        summaries[key] = {
            "nominal_fpr": float(readout["nominal_fpr"]),
            "final_score_realized_fpr": float(readout["realized_fpr"]),
            "threshold": threshold,
            "threshold_comparison": "score_greater_equal_threshold",
            "tied_group_kept_complete": True,
            "positive_entity_count": positive_count,
            "alerted_positive_entity_count": int(alerted_positive.sum()),
            "never_alerted_positive_entity_count": int((positive & (first_alert == 0)).sum()),
            "unalerted_rate": positive_unalerted_rate,
            "benign_entity_count": benign_count,
            "alerted_benign_entity_count": int(alerted_benign.sum()),
            "realized_first_alert_fpr": actual_first_alert_fpr,
            "first_alert_exposure_index": distribution(positive_positions),
            "maximum_positive_entity_exposure_count": int(entity_counts[positive].max()),
            "curve_point_count": int(len(axis)),
        }
        vectors[f"{CELL}__{key}__exposure_index"] = axis
        vectors[f"{CELL}__{key}__timely_detection_rate"] = rate
        del first_alert

    definition = (
        "从实体第一条进入目标评价池的合法流开始，以1基实体内曝光序号计数；"
        "在线C11实体分数为冻结p=1的前缀算术平均，首次满足score>=同档完整并列阈值即告警；"
        "累计按时检出率分母固定为全部恶意实体，未告警实体保留为删失。"
    )
    summary = {
        "definition": definition,
        "axis": "exposure_index",
        "exposure_index_base": 1,
        "curve_encoding": "right_continuous_exact_breakpoints",
        "threshold_semantics": "same_complete_tied_score_group_greater_equal",
        "time_delay_available": False,
        "time_delay_unavailable_reason": config["evaluation"][
            "time_delay_unavailable_reason"
        ],
        "positive_entity_count": positive_count,
        "unalerted_rate_at_fpr": unalerted,
        "realized_fpr_at_fpr": realized_first_alert,
        "delay_summary_at_fpr": summaries,
        "first_alert_exposure_summary_at_fpr": summaries,
        "persisted_per_flow_scores": False,
        "persisted_per_entity_scores": False,
        "persisted_per_entity_first_alert": False,
    }
    return summary, vectors


def verify_compute_receipt(output_root: Path) -> dict[str, Any] | None:
    path = output_root / "compute-complete-receipt.json"
    if not path.is_file():
        return None
    receipt = load_json(path)
    if receipt.get("run_id") != RUN_ID or receipt.get("stage") != "compute_complete":
        raise SystemExit("已有计算收据身份异常，拒绝覆盖")
    for name, item in receipt.get("artifacts", {}).items():
        artifact = output_root / name
        if (
            not artifact.is_file()
            or artifact.stat().st_size != item.get("bytes")
            or sha256_file(artifact) != item.get("sha256")
        ):
            raise SystemExit(f"已有计算制品与收据不符，拒绝覆盖：{name}")
    return receipt


def compute(config: dict[str, Any], config_path: Path, resume: bool) -> None:
    load_numeric_dependencies()
    output_root = Path(config["paths"]["output_root"]).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    existing = verify_compute_receipt(output_root)
    if existing is not None:
        if not resume:
            raise SystemExit("计算阶段已完成；仅允许使用 --resume 幂等跳过")
        print(f"COMPUTE_ALREADY_COMPLETE run={RUN_ID}", flush=True)
        return
    write_stage_status(output_root, "input_validation", "核验父身份、固定哈希与七个目标缓存")
    validation = validate_parent_and_cache(config)
    booster, torch_module, xgboost_version = load_frozen_model(config)
    model_path = Path(config["paths"]["parent_run_root"]) / "model_semantic168.json"
    validation["loaded_model"] = {
        "filename": model_path.name,
        "sha256": sha256_file(model_path),
        "num_boosted_rounds": int(booster.num_boosted_rounds()),
        "prediction_device": "cuda:0",
        "xgboost_version": xgboost_version,
    }
    validation["tool_sha256"] = sha256_file(Path(__file__).resolve())
    validation["config_sha256"] = sha256_file(config_path)
    atomic_json(output_root / "input-validation-receipt.json", validation)
    atomic_json(output_root / "config.json", config)

    write_stage_status(output_root, "target_load", "只加载七个冻结 LSPR24 数组")
    cache_root = Path(config["paths"]["cache_root"])
    arrays = {
        name: np.load(
            cache_root / f"{name}.npy",
            mmap_mode=None if name in {"s24", "d24"} else "r",
            allow_pickle=name in {"s24", "d24"},
        )
        for name in TARGET_ARRAYS
    }
    if (
        arrays["X24"].shape != (N_FLOW, N_RAW_FEATURE)
        or arrays["y24"].shape != (N_FLOW,)
        or arrays["I24"].shape[1] != N_SEQUENCE_WIDTH
        or arrays["M24"].shape != arrays["I24"].shape
        or any(len(arrays[name]) != N_FLOW for name in ("s24", "d24", "t24"))
    ):
        raise SystemExit("七个 LSPR24 缓存的冻结形状不符")
    sequence_pairs = assert_sequence_time_monotonic(
        arrays["t24"], arrays["I24"], arrays["M24"]
    )

    write_stage_status(output_root, "entity_identity", "构造无向地址对实体并核验实体内时间顺序")
    entity_key = np.fromiter(
        (
            f"{left}|{right}" if left <= right else f"{right}|{left}"
            for left, right in zip(arrays["s24"], arrays["d24"], strict=True)
        ),
        dtype=object,
        count=N_FLOW,
    )
    _, entity = np.unique(entity_key, return_inverse=True)
    entity = entity.astype(np.int64, copy=False)
    del entity_key, arrays["s24"], arrays["d24"]
    if int(entity.max()) + 1 != N_ENTITY:
        raise SystemExit(f"LSPR24 实体数应为 {N_ENTITY:,}")
    entity_labels = np.zeros(N_ENTITY, dtype=np.int8)
    np.maximum.at(entity_labels, entity, arrays["y24"].astype(np.int8, copy=False))
    if int(entity_labels.sum()) != N_POSITIVE_ENTITY:
        raise SystemExit(f"LSPR24 正实体数应为 {N_POSITIVE_ENTITY}")
    flow_positive_rate = float(np.mean(arrays["y24"], dtype=np.float64))
    if abs(flow_positive_rate - FLOW_POSITIVE_RATE) >= 1e-9:
        raise SystemExit(f"LSPR24 逐流正例率不符：{flow_positive_rate:.12f}")
    entity_order, entity_time_pairs = assert_entity_time_monotonic(
        arrays["t24"], entity
    )
    del arrays["t24"]

    write_stage_status(output_root, "semantic168", "只在内存重建一次冻结 semantic168")
    semantic = build_semantic_matrix(
        arrays["X24"],
        arrays["I24"],
        arrays["M24"],
        int(config["evaluation"]["predict_batch"]),
        int(config["evaluation"]["sequence_batch"]),
    )
    del arrays["X24"], arrays["I24"], arrays["M24"]

    write_stage_status(output_root, "single_gpu_score", "冻结最终模型执行一次逻辑目标打分")
    score_started = time.time()
    flow_scores, api_batches = predict_once(
        booster,
        semantic,
        int(config["evaluation"]["predict_batch"]),
        torch_module,
    )
    scoring_seconds = time.time() - score_started
    del semantic, booster
    torch_module.cuda.empty_cache()

    write_stage_status(output_root, "aggregate", "内存计算完整并列组曲线与首次告警")
    entity_scores, entity_counts = entity_mean_scores(flow_scores, entity)
    curve = complete_tied_budget_curve(entity_scores, entity_labels)
    readouts = budget_readouts(curve)
    first_alert, first_alert_vectors = first_alert_aggregate(
        flow_scores,
        entity,
        entity_labels,
        entity_order,
        entity_counts,
        readouts,
        config,
    )
    curve_vectors = {f"{CELL}__{name}": values for name, values in curve.items()}
    curve_artifact = atomic_npz(
        output_root / "complete-alert-budget-curves.npz", curve_vectors
    )
    curve_receipt = {
        "schema_version": "ch3-xgb-cpa-elp-operational-complete-alert-budget-curves-v1",
        "run_id": RUN_ID,
        "cells": [CELL],
        "fields": list(curve),
        "artifact": curve_artifact,
        "complete_over_all_reachable_negative_entity_budgets": True,
        "curve_is_complete_over_all_reachable_negative_entity_budgets": True,
        "complete_negative_tie_groups": True,
        "zero_false_positive_boundary_included": True,
        "nominal_point_interpolation": False,
        "point_count": int(len(curve["realized_fpr"])),
        "negative_entity_count": int((entity_labels == 0).sum()),
    }
    atomic_json(output_root / "complete-alert-budget-curves-receipt.json", curve_receipt)

    first_alert_artifact = atomic_npz(
        output_root / "first-alert-timing-curves.npz", first_alert_vectors
    )
    first_alert_receipt = {
        "schema_version": "ch3-first-alert-timing-v1",
        "run_id": RUN_ID,
        "axis": "exposure_index",
        "axis_field_suffix": "exposure_index",
        "rate_field_suffix": "timely_detection_rate",
        "time_delay_available": False,
        "curve_encoding": "right_continuous_exact_breakpoints",
        "artifact": first_alert_artifact,
        "cells": {CELL: first_alert},
        "scopes": ["target"],
        "budget_count_per_cell": len(FPR_BUDGETS),
        "persisted_per_flow_scores": False,
        "persisted_per_entity_scores": False,
        "persisted_per_entity_first_alert": False,
    }
    atomic_json(output_root / "first-alert-timing-receipt.json", first_alert_receipt)

    valid_entity = np.isfinite(entity_scores)
    target_metrics = {
        "schema_version": "ch3-xgb-cpa-elp-operational-backfill-target-metrics-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "dataset": "LSPR24",
        "evaluation_pool": "LSPR24已访问目标年描述性评价池",
        "cell": CELL,
        "model": {
            "parent_run_id": PARENT_RUN_ID,
            "adapter": "semantic168",
            "power_mean_p": 1.0,
            "num_boost_round": N_TREE,
            "model_sha256": EXPECTED_HASHES["model_semantic168.json"],
        },
        "cells": {
            CELL: {
                "flow_average_precision": float(
                    average_precision_score(arrays["y24"], flow_scores)
                ),
                "flow_roc_auc": float(roc_auc_score(arrays["y24"], flow_scores)),
                "entity_average_precision": float(
                    average_precision_score(
                        entity_labels[valid_entity], entity_scores[valid_entity]
                    )
                ),
                "dr_at_fpr": {
                    key: value["detection_rate"] for key, value in readouts.items()
                },
                "dr_at_fpr_receipts": readouts,
                "first_alert": first_alert,
                "flows_scored": N_FLOW,
                "entities_scored": int(valid_entity.sum()),
            }
        },
        "target_contract": {
            "flow_count": N_FLOW,
            "entity_count": N_ENTITY,
            "positive_entity_count": N_POSITIVE_ENTITY,
            "flow_positive_rate": flow_positive_rate,
            "sequence_time_adjacent_pairs_checked": sequence_pairs,
            "entity_time_adjacent_pairs_checked": entity_time_pairs,
        },
        "isolation": {
            "target_retrained": False,
            "source_year_retrained": False,
            "target_used_for_selection_or_tuning": False,
            "target_arrays_loaded": list(TARGET_ARRAYS),
            "target_array_load_count": 1,
            "semantic168_build_count": 1,
            "target_score_calls": 1,
            "predict_api_batches_within_single_logical_call": api_batches,
            "target_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
            "raw83_evaluation_performed": False,
            "fold_or_oof_evaluation_performed": False,
        },
        "artifact_policy": config["artifact_policy"],
        "timing": {
            "single_logical_gpu_score_seconds": scoring_seconds,
            "compute_total_seconds": time.time() - T0,
            "wall_clock_limit": None,
        },
    }
    atomic_json(output_root / "target-year-metrics.json", target_metrics)
    del flow_scores, entity_scores, entity_order, entity, arrays, first_alert_vectors

    artifact_names = (
        "config.json",
        "input-validation-receipt.json",
        "target-year-metrics.json",
        "complete-alert-budget-curves.npz",
        "complete-alert-budget-curves-receipt.json",
        "first-alert-timing-curves.npz",
        "first-alert-timing-receipt.json",
    )
    artifacts = {name: artifact_receipt(output_root / name) for name in artifact_names}
    compute_receipt = {
        "schema_version": "ch3-xgb-cpa-elp-operational-backfill-compute-v1",
        "run_id": RUN_ID,
        "stage": "compute_complete",
        "target_retrained": False,
        "target_score_calls": 1,
        "target_scores_persisted": False,
        "semantic168_build_count": 1,
        "artifacts": artifacts,
        "completed_at_unix": time.time(),
    }
    atomic_json(output_root / "compute-complete-receipt.json", compute_receipt)
    write_stage_status(output_root, "compute_complete", "聚合计算已原子完成，等待资源收据和发布")
    print(f"COMPUTE_COMPLETE run={RUN_ID}", flush=True)


def validate_resource_receipt(path: Path, config: Mapping[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"资源收据缺失：{path}")
    receipt = load_json(path)
    if (
        receipt.get("run_id") != RUN_ID
        or receipt.get("finalized") is not True
        or int(receipt.get("sample_count", 0)) <= 0
        or receipt.get("wall_clock_limit") is not None
        or receipt.get("admission", {}).get("minimum_free_gpu_memory_gib")
        != config["resource_contract"]["minimum_free_gpu_memory_gib"]
        or receipt.get("admission", {}).get("minimum_cgroup_available_memory_gib")
        != config["resource_contract"]["minimum_cgroup_available_memory_gib"]
        or receipt.get("admission", {}).get("minimum_free_disk_gib")
        != config["resource_contract"]["minimum_free_disk_gib"]
    ):
        raise SystemExit("资源收据未完成或与冻结资源门不符")
    return receipt


def finalize(
    config: dict[str, Any],
    config_path: Path,
    resource_receipt_path: Path,
    resume: bool,
) -> None:
    output_root = Path(config["paths"]["output_root"]).resolve()
    manifest_path = output_root / "manifest.json"
    if manifest_path.is_file():
        if not resume:
            raise SystemExit("最终 manifest 已存在；仅允许使用 --resume 幂等核验")
        manifest = load_json(manifest_path)
        validate_manifest_files(output_root, manifest)
        if (
            manifest.get("run_id") != RUN_ID
            or manifest.get("complete") is not True
            or manifest.get("script_sha256") != sha256_file(Path(__file__).resolve())
            or manifest.get("config_sha256") != sha256_file(config_path)
            or manifest.get("target_retrained") is not False
            or manifest.get("target_score_calls") != 1
            or manifest.get("target_scores_persisted") is not False
        ):
            raise SystemExit("已有 manifest 身份或目标只评价合同不符")
        print(f"RUN_ALREADY_COMPLETE run={RUN_ID}", flush=True)
        return
    compute_receipt = verify_compute_receipt(output_root)
    if compute_receipt is None:
        raise SystemExit("计算阶段尚未完成，禁止发布")
    resource = validate_resource_receipt(resource_receipt_path, config)
    write_stage_status(output_root, "tracking_publish", "仅发布聚合指标")
    metrics = load_json(output_root / "target-year-metrics.json")
    cell = metrics["cells"][CELL]

    import swanlab

    tracking = config["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=DISPLAY_NAME,
        config={
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "parent_run_id": PARENT_RUN_ID,
            "target_retrained": False,
            "target_score_calls": 1,
            "target_scores_persisted": False,
            "model_sha256": EXPECTED_HASHES["model_semantic168.json"],
            "config_sha256": sha256_file(config_path),
        },
        mode=tracking["mode"],
        logdir=str(output_root / "swanlog"),
    )
    log_values = {
        "target/C11_flow_ap": cell["flow_average_precision"],
        "target/C11_entity_ap": cell["entity_average_precision"],
        "runtime/peak_gpu_used_mib": resource["peak_gpu_used_mib"],
        "runtime/peak_cgroup_current_bytes": resource["peak_cgroup_current_bytes"],
    }
    for key, value in cell["dr_at_fpr"].items():
        log_values[f"target/C11_dr_at_{key}"] = value
    swanlab.log(log_values, step=0)
    swanlab.finish()
    atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-xgb-cpa-elp-operational-backfill-swanlab-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "workspace": tracking["workspace"],
            "project": tracking["project"],
            "mode": tracking["mode"],
            "aggregate_only": True,
            "completed": True,
            "per_flow_scores_logged": False,
            "per_entity_scores_logged": False,
        },
    )

    operational_receipt = {
        "schema_version": "ch3-xgb-cpa-elp-operational-backfill-receipt-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "parent_run_id": PARENT_RUN_ID,
        "parent_evaluation_run_id": PARENT_EVAL_RUN_ID,
        "model_sha256": EXPECTED_HASHES["model_semantic168.json"],
        "num_boost_round": N_TREE,
        "selected_adapter": "semantic168",
        "power_mean_p": 1.0,
        "target_retrained": False,
        "target_score_calls": 1,
        "target_scores_persisted": False,
        "per_entity_scores_persisted": False,
        "per_entity_first_alert_persisted": False,
        "target_arrays": list(TARGET_ARRAYS),
        "semantic168_build_count": 1,
        "raw83_evaluation_performed": False,
        "fold_or_oof_evaluation_performed": False,
        "time_delay_available": False,
        "nominal_point_interpolation": False,
        "complete_negative_tie_groups": True,
        "resource_receipt": artifact_receipt(resource_receipt_path),
        "compute_receipt_sha256": sha256_file(
            output_root / "compute-complete-receipt.json"
        ),
    }
    atomic_json(output_root / "operational-backfill-receipt.json", operational_receipt)
    write_stage_status(output_root, "complete", "运营指标、资源与跟踪制品完整发布")

    required_names = (
        "config.json",
        "input-validation-receipt.json",
        "target-year-metrics.json",
        "complete-alert-budget-curves.npz",
        "complete-alert-budget-curves-receipt.json",
        "first-alert-timing-curves.npz",
        "first-alert-timing-receipt.json",
        "compute-complete-receipt.json",
        resource_receipt_path.name,
        "swanlab-receipt.json",
        "operational-backfill-receipt.json",
        "stage-status.json",
    )
    files = {name: artifact_receipt(output_root / name) for name in required_names}
    manifest = {
        "schema_version": "ch3-xgb-cpa-elp-operational-backfill-manifest-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "complete": True,
        "script_sha256": sha256_file(Path(__file__).resolve()),
        "config_sha256": sha256_file(config_path),
        "parent_run_id": PARENT_RUN_ID,
        "target_retrained": False,
        "target_score_calls": 1,
        "target_scores_persisted": False,
        "per_entity_scores_persisted": False,
        "per_entity_first_alert_persisted": False,
        "complete_negative_tie_groups": True,
        "time_delay_available": False,
        "files": files,
        "forbidden_artifacts_absent": all(
            not (output_root / name).exists()
            for name in (
                "flow-scores.npy",
                "entity-scores.npy",
                "first-alert-per-entity.npy",
                "semantic168.npy",
                "model.json",
            )
        ),
    }
    if not manifest["forbidden_artifacts_absent"]:
        raise SystemExit("发现禁止持久化的分数、派生矩阵或新模型")
    atomic_json(manifest_path, manifest)
    validate_manifest_files(output_root, manifest)
    print(f"OPERATIONAL_BACKFILL_COMPLETE run={RUN_ID}", flush=True)


def main() -> None:
    args = parse_args()
    if not args.config.is_file():
        raise SystemExit(f"配置文件缺失：{args.config}")
    config = load_json(args.config)
    validate_config(config)
    if args.validate_config:
        print("CONFIG_VALID", flush=True)
        return
    if args.validate_inputs:
        validation = validate_parent_and_cache(config)
        booster, _torch_module, version = load_frozen_model(config)
        if int(booster.num_boosted_rounds()) != N_TREE:
            raise SystemExit("输入核验阶段模型树数不符")
        print(
            f"INPUTS_VALID parent={validation['parent_run_id']} "
            f"model_sha256={EXPECTED_HASHES['model_semantic168.json']} xgboost={version}",
            flush=True,
        )
        return
    if args.compute:
        compute(config, args.config.resolve(), args.resume)
        return
    if args.finalize:
        if args.resource_receipt is None:
            raise SystemExit("--finalize 必须提供 --resource-receipt")
        finalize(config, args.config.resolve(), args.resource_receipt.resolve(), args.resume)
        return
    raise SystemExit("必须指定 --compute、--finalize、--validate-config 或 --validate-inputs")


if __name__ == "__main__":
    main()
