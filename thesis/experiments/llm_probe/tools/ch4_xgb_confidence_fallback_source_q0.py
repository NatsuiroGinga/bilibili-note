#!/usr/bin/env python3
"""机制二源年三角色、零训练置信确认与源阈值回退 Q0。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from ch3_xgb_cpa_elp_eval_continuation import (  # noqa: E402
    AUTHORIZED_SWANLAB_PROJECT,
    AUTHORIZED_SWANLAB_WORKSPACE,
    BOOLEAN_IDX,
    CATEGORICAL_IDX,
    D_RAW,
    EXPECTED_CONFIG,
    EXPECTED_SHA256,
    EXPECTED_XGB_PARAMS,
    NUMERIC_IDX,
    PARENT_RUN_ID,
    configure_prediction_device,
    gpu_guard,
)

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "runs/diagnostics/dijk-repro/cache"
RUN_ID = "ch4-xgb-confidence-fallback-source-q0-seed42-v1"
DISPLAY_NAME = "有限样本目标确认与源阈值回退源年 Q0"
SCHEMA_VERSION = "ch4-xgb-confidence-fallback-source-q0-v1"
PBC_RECOVERY_CONSUMER_ID = "ch4-xgb-pbc-q0-seed42-v1-rerun2"
PARENT_RECOVERY_SCHEMA = "ch3-xgb-parent-recovery-proof-v1"
PARENT_RECOVERY_FILENAME = "parent-recovery-proof.json"
ALLOWED_ARRAYS = ("X23", "y23", "E23", "I23", "M23")
N_FLOW = 16_353_511
N_SEQUENCE = 271_815
N_ENTITY = 150_680
N_POS_ENTITY = 239
N_FOLD = 3
N_TREE = 800
SEQUENCE_LENGTH = 128
ROLE_BY_FOLD = {0: "development", 1: "calibration", 2: "holdout"}
EXPECTED_FOLD_COUNTS = (50_227, 50_227, 50_226)
EXPECTED_FOLD_POSITIVE_COUNTS = (80, 80, 79)
EXPECTED_PARENT_ARTIFACTS = (
    "selection_frozen_xgb2x2.json",
    "effective_config_receipts.json",
    "model_oof_semantic168_fold0.json",
    "model_oof_semantic168_fold1.json",
    "model_oof_semantic168_fold2.json",
)
T0 = time.time()
LAST_BEAT = [T0]
TARGET_YEAR_ARRAYS_READ = 0
NEW_MODELS_TRAINED = 0


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    now = time.time()
    if now - LAST_BEAT[0] < every and done < total:
        return
    LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    eta = (total - done) / max(rate, 1e-9)
    log(
        f"  [{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {eta:.0f}s"
    )


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_array(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(array.shape, separators=(",", ":")).encode("ascii"))
    digest.update(memoryview(array).cast("B"))
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(partial, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/ch4-xgb-confidence-fallback-source-q0-seed42-v1.json",
    )
    parser.add_argument(
        "--parent-run-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / PARENT_RUN_ID,
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
            / f"{PARENT_RUN_ID}-for-{PBC_RECOVERY_CONSUMER_ID}-v1"
            / PARENT_RECOVERY_FILENAME
        ),
    )
    parser.add_argument("--out", type=Path, default=ROOT / "runs/candidates" / RUN_ID)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


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
        "source_year_only": True,
        "zero_training": True,
        "parent_run_id": PARENT_RUN_ID,
        "parent_recovery_proof": {
            "schema_version": PARENT_RECOVERY_SCHEMA,
            "requires_parent_incomplete": True,
            "original_manifest_expected": False,
        },
        "base_adapter": "semantic168",
        "power_mean_p": 1.0,
        "observation_index": 1,
        "candidate_count": 1,
        "comparison_operator": "strict_greater_than",
        "fold_roles": {"development": 0, "calibration": 1, "holdout": 2},
        "entity_fpr_budget": 0.04,
        "confirmation_failure_probability": 0.05,
        "minimum_zero_error_calibration_negatives": 74,
        "allowed_arrays": list(ALLOWED_ARRAYS),
        "target_year_arrays_read": 0,
        "new_models_trained": 0,
        "predict_batch": 2_000_000,
        "artifact_policy": {
            "persist_aggregate_json": True,
            "persist_status_log_manifest_resource": True,
            "persist_per_flow_scores": False,
            "persist_per_entity_scores": False,
            "persist_fold_membership": False,
            "persist_label_details": False,
            "persist_new_models": False,
        },
    }
    for key, expected_value in expected.items():
        if config.get(key) != expected_value:
            raise SystemExit(f"源年 Q0 配置字段不符：{key}")
    if config.get("input_contract") != {
        "flow_count": N_FLOW,
        "sequence_count": N_SEQUENCE,
        "entity_count": N_ENTITY,
        "positive_entity_count": N_POS_ENTITY,
        "feature_count": D_RAW,
        "sequence_length": SEQUENCE_LENGTH,
        "fold_entity_counts": list(EXPECTED_FOLD_COUNTS),
        "fold_positive_entity_counts": list(EXPECTED_FOLD_POSITIVE_COUNTS),
    }:
        raise SystemExit("源年输入规模合同不符")
    if config.get("tracking") != {
        "workspace": AUTHORIZED_SWANLAB_WORKSPACE,
        "project": AUTHORIZED_SWANLAB_PROJECT,
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 目的地或聚合模式不符")
    resources = config.get("resource_contract", {})
    if resources != {
        "estimated_peak_host_gib": 58,
        "minimum_free_gpu_memory_gib": 11,
        "runtime_gpu_floor_gib": 8,
        "minimum_free_disk_gib": 30,
        "inheritance": "沿用既有 XGBoost PBC 保守资源门，不新增训练资源参数",
    }:
        raise SystemExit("资源合同不符")


def validate_parent_and_inputs(
    args: argparse.Namespace, config: dict[str, Any]
) -> dict[str, Any]:
    parent_root = args.parent_run_root.resolve()
    if parent_root.name != PARENT_RUN_ID:
        raise SystemExit(f"父运行身份不符：{parent_root.name}")
    if args.out.resolve().name != RUN_ID or args.out.resolve() == parent_root:
        raise SystemExit("输出身份不符或将覆盖父运行")

    if not args.parent_config.is_file():
        raise SystemExit(f"父配置缺失：{args.parent_config}")
    parent_config = load_json(args.parent_config)
    for key, expected in EXPECTED_CONFIG.items():
        if parent_config.get(key) != expected:
            raise SystemExit(f"父配置字段不符：{key}")
    if parent_config.get("tracking") != config["tracking"]:
        raise SystemExit("父配置与本轮 SwanLab 目的地不一致")

    proof_path = args.parent_recovery_proof.resolve()
    if proof_path.name != PARENT_RECOVERY_FILENAME or not proof_path.is_file():
        raise SystemExit(f"父恢复证明缺失：{proof_path}")
    if parent_root in proof_path.parents:
        raise SystemExit("父恢复证明不得写在父运行目录内")
    proof = load_json(proof_path)
    if proof.get("schema_version") != PARENT_RECOVERY_SCHEMA:
        raise SystemExit("父恢复证明模式版本不符")
    if proof.get("parent_run_id") != PARENT_RUN_ID:
        raise SystemExit("父恢复证明运行身份不符")
    if Path(str(proof.get("parent_run_root", ""))).resolve() != parent_root:
        raise SystemExit("父恢复证明中的父运行路径不符")
    if proof.get("does_not_assert_parent_completion") is not True:
        raise SystemExit("父恢复证明错误声明父运行已完成")
    parent_state = proof.get("parent_state", {})
    historical_status = parent_state.get("historical_status", {})
    if (
        parent_state.get("complete") is not False
        or historical_status.get("state") != "running"
        or historical_status.get("stage") != "source_selection"
        or historical_status.get("exit_code") is not None
        or parent_state.get("missing_completion_artifacts")
        != ["xgb_cpa_elp_results.json", "manifest.json"]
    ):
        raise SystemExit("父恢复证明未保留已核验的中断事实")
    parent_status_path = parent_root / "status.json"
    if (
        not parent_status_path.is_file()
        or historical_status.get("filename") != parent_status_path.name
        or historical_status.get("sha256") != sha256_file(parent_status_path)
        or historical_status.get("bytes") != parent_status_path.stat().st_size
    ):
        raise SystemExit("父实际状态与恢复证明不符")
    for name in parent_state["missing_completion_artifacts"]:
        if (parent_root / name).exists():
            raise SystemExit(f"父运行出现证明声明缺失的完成制品：{name}")

    proof_artifacts = proof.get("artifacts", {})
    artifact_hashes: dict[str, str] = {}
    for name in EXPECTED_PARENT_ARTIFACTS:
        path = parent_root / name
        receipt = proof_artifacts.get(name, {})
        if not path.is_file() or not receipt:
            raise SystemExit(f"父恢复证明或实际制品缺失：{name}")
        actual = sha256_file(path)
        if actual != receipt.get("sha256") or path.stat().st_size != receipt.get("bytes"):
            raise SystemExit(f"父制品与恢复证明不符：{name}")
        if name.startswith("model_") and receipt.get("num_boosted_rounds") != N_TREE:
            raise SystemExit(f"父折模型树数不是 {N_TREE}：{name}")
        artifact_hashes[name] = actual
    for name in ("selection_frozen_xgb2x2.json", "effective_config_receipts.json"):
        if artifact_hashes[name] != EXPECTED_SHA256[name]:
            raise SystemExit(f"父固定收据摘要不符：{name}")

    selection = load_json(parent_root / "selection_frozen_xgb2x2.json")
    if selection.get("run_name") != PARENT_RUN_ID:
        raise SystemExit("父选择收据运行身份不符")
    if selection.get("seed") != 42 or selection.get("n_fold") != N_FOLD:
        raise SystemExit("父选择收据种子或折数不符")
    if selection.get("xgb_params") != EXPECTED_XGB_PARAMS:
        raise SystemExit("父选择收据 XGBoost 参数不符")
    if selection.get("adapter_selection", {}).get("selected") != "semantic168":
        raise SystemExit("父选择收据未冻结 semantic168")
    if float(selection.get("p_selection", {}).get("semantic168", {}).get("p_selected", math.nan)) != 1.0:
        raise SystemExit("父选择收据 semantic168 的 p 不是 1")
    if selection.get("lspr23") != {
        "n_flow": N_FLOW,
        "n_entity": N_ENTITY,
        "n_pos_entity": N_POS_ENTITY,
    }:
        raise SystemExit("父选择收据 LSPR23 规模不符")

    receipts = load_json(parent_root / "effective_config_receipts.json")
    receipt_by_tag = {
        item.get("tag"): item for item in receipts if isinstance(item, dict)
    }
    for fold in range(N_FOLD):
        tag = f"semantic168/fold{fold}"
        if receipt_by_tag.get(tag, {}).get("passed") is not True:
            raise SystemExit(f"父有效配置收据未通过：{tag}")

    cache_receipts: dict[str, Any] = {}
    for name in ALLOWED_ARRAYS:
        if "24" in name or not name.endswith("23"):
            raise AssertionError(f"源年白名单含非法数组：{name}")
        path = CACHE / f"{name}.npy"
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"源年缓存缺失或为空：{path}")
        cache_receipts[name] = {"filename": path.name, "bytes": path.stat().st_size}

    return {
        "parent_run_root": str(parent_root),
        "parent_config_path": str(args.parent_config.resolve()),
        "parent_config_sha256": sha256_file(args.parent_config),
        "parent_recovery_proof_path": str(proof_path),
        "parent_recovery_proof_sha256": sha256_file(proof_path),
        "artifact_sha256": artifact_hashes,
        "selection_sha256": artifact_hashes["selection_frozen_xgb2x2.json"],
        "selection": selection,
        "cache_receipts": cache_receipts,
    }


def guarded_source_load(name: str) -> np.ndarray:
    global TARGET_YEAR_ARRAYS_READ
    if "24" in name:
        raise RuntimeError(f"拒绝读取目标年数组：{name}")
    if name not in ALLOWED_ARRAYS or not name.endswith("23"):
        raise RuntimeError(f"拒绝读取源年合同外数组：{name}")
    if TARGET_YEAR_ARRAYS_READ != 0:
        raise AssertionError("目标年读取计数在源年 Q0 中必须恒为零")
    return np.load(CACHE / f"{name}.npy", mmap_mode="r", allow_pickle=False)


def scan_source_structure(
    labels: np.ndarray,
    indices: np.ndarray,
    masks: np.ndarray,
    sequence_entities: np.ndarray,
) -> dict[str, np.ndarray]:
    if labels.shape != (N_FLOW,) or indices.shape != (N_SEQUENCE, SEQUENCE_LENGTH):
        raise SystemExit(f"源年标签或索引形状不符：y={labels.shape} I={indices.shape}")
    if masks.shape != indices.shape or sequence_entities.shape != (N_SEQUENCE,):
        raise SystemExit(f"源年掩码或序列实体形状不符：M={masks.shape} E={sequence_entities.shape}")
    if int(sequence_entities.min()) != 0 or int(sequence_entities.max()) != N_ENTITY - 1:
        raise SystemExit("E23 实体编号范围不符")
    if np.any(sequence_entities[1:] < sequence_entities[:-1]):
        raise SystemExit("E23 未按实体稳定分块，无法确定唯一首曝")
    entity_ids, first_sequence = np.unique(sequence_entities, return_index=True)
    if not np.array_equal(entity_ids, np.arange(N_ENTITY)):
        raise SystemExit("E23 未恰好覆盖全部冻结实体")
    first_flow = np.asarray(indices[first_sequence, 0], np.int64)
    if not np.all(np.asarray(masks[first_sequence, 0]) > 0):
        raise SystemExit("实体首序列的首位置不是有效流")
    if len(np.unique(first_flow)) != N_ENTITY:
        raise SystemExit("实体首曝流索引不唯一")

    entity_labels = np.zeros(N_ENTITY, np.int8)
    entity_flow_counts = np.zeros(N_ENTITY, np.int64)
    entity_positive_flow_counts = np.zeros(N_ENTITY, np.int64)
    flow_seen = np.zeros(N_FLOW, np.bool_)
    started = time.time()
    for start in range(0, N_SEQUENCE, 20_000):
        stop = min(start + 20_000, N_SEQUENCE)
        block_indices = np.asarray(indices[start:stop])
        block_valid = np.asarray(masks[start:stop]) > 0
        valid_indices = block_indices[block_valid]
        if len(valid_indices) != len(np.unique(valid_indices)):
            raise SystemExit(f"I23/M23 在序列块 {start}:{stop} 内重复覆盖流")
        if len(valid_indices) and (
            int(valid_indices.min()) < 0 or int(valid_indices.max()) >= N_FLOW
        ):
            raise SystemExit("I23 有效位置包含越界流索引")
        if flow_seen[valid_indices].any():
            raise SystemExit(f"I23/M23 在序列块 {start}:{stop} 跨块重复覆盖流")
        flow_seen[valid_indices] = True
        block_labels = np.asarray(labels[block_indices])
        if not np.isin(block_labels[block_valid], (0.0, 1.0)).all():
            raise SystemExit("y23 包含非二元标签")
        block_labels = np.where(block_valid, block_labels, 0.0)
        block_entities = np.asarray(sequence_entities[start:stop], np.int64)
        np.maximum.at(
            entity_labels,
            block_entities,
            block_labels.max(axis=1).astype(np.int8, copy=False),
        )
        np.add.at(entity_flow_counts, block_entities, block_valid.sum(axis=1))
        np.add.at(
            entity_positive_flow_counts,
            block_entities,
            block_labels.sum(axis=1).astype(np.int64, copy=False),
        )
        beat("源年结构扫描", stop, N_SEQUENCE, started)
    if not flow_seen.all():
        raise SystemExit(f"I23/M23 未覆盖全部流：缺少 {int((~flow_seen).sum()):,} 条")
    if int(entity_labels.sum()) != N_POS_ENTITY or np.any(entity_flow_counts <= 0):
        raise SystemExit("源年正实体数或实体流支持数不符")
    return {
        "entity_ids": entity_ids.astype(np.int64, copy=False),
        "entity_labels": entity_labels,
        "first_flow": first_flow,
        "entity_flow_counts": entity_flow_counts,
        "entity_positive_flow_counts": entity_positive_flow_counts,
    }


def make_folds(entity_labels: np.ndarray, seed: int) -> np.ndarray:
    random_state = np.random.RandomState(seed)
    fold_of_entity = np.empty(N_ENTITY, np.int8)
    for label in (0, 1):
        entity_ids = np.flatnonzero(entity_labels == label)
        entity_ids = entity_ids[random_state.permutation(len(entity_ids))]
        fold_of_entity[entity_ids] = np.arange(len(entity_ids)) % N_FOLD
    counts = tuple(int((fold_of_entity == fold).sum()) for fold in range(N_FOLD))
    positives = tuple(
        int(entity_labels[fold_of_entity == fold].sum()) for fold in range(N_FOLD)
    )
    if counts != EXPECTED_FOLD_COUNTS or positives != EXPECTED_FOLD_POSITIVE_COUNTS:
        raise SystemExit(f"实体三折规模不符：counts={counts} positives={positives}")
    return fold_of_entity


def fold_statistics(
    fold_of_entity: np.ndarray,
    entity_labels: np.ndarray,
    entity_flow_counts: np.ndarray,
    entity_positive_flow_counts: np.ndarray,
) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    for fold in range(N_FOLD):
        mask = fold_of_entity == fold
        result.append(
            {
                "fold": fold,
                "n_entity": int(mask.sum()),
                "n_pos_entity": int(entity_labels[mask].sum()),
                "n_flow": int(entity_flow_counts[mask].sum()),
                "n_pos_flow": int(entity_positive_flow_counts[mask].sum()),
            }
        )
    return result


def build_first_exposure_semantic168(
    raw_values: np.ndarray, first_flow: np.ndarray
) -> np.ndarray:
    if raw_values.shape != (N_FLOW, D_RAW):
        raise SystemExit(f"X23 形状不符：{raw_values.shape}")
    first_raw = np.asarray(raw_values[first_flow], np.float32)
    dimension = D_RAW + len(NUMERIC_IDX) + len(CATEGORICAL_IDX) + len(BOOLEAN_IDX) + 2
    if dimension != 168:
        raise AssertionError(f"semantic168 维度推导异常：{dimension}")
    matrix = np.empty((N_ENTITY, dimension), np.float32)
    matrix[:, :D_RAW] = first_raw
    cursor = D_RAW
    matrix[:, cursor : cursor + len(NUMERIC_IDX)] = 0.0
    cursor += len(NUMERIC_IDX)
    matrix[:, cursor : cursor + len(CATEGORICAL_IDX)] = 1.0
    cursor += len(CATEGORICAL_IDX)
    matrix[:, cursor : cursor + len(BOOLEAN_IDX)] = (
        first_raw[:, BOOLEAN_IDX] > 0
    ).astype(np.float32)
    cursor += len(BOOLEAN_IDX)
    matrix[:, cursor] = np.float32(math.log1p(1.0))
    cursor += 1
    matrix[:, cursor] = 1.0
    cursor += 1
    if cursor != dimension or not np.isfinite(matrix).all():
        raise SystemExit("首曝 semantic168 构造不完整或含非有限值")
    return matrix


def load_booster(xgb_module: Any, path: Path, tag: str) -> tuple[Any, dict[str, Any]]:
    booster = xgb_module.Booster()
    booster.load_model(path)
    tree_count = int(booster.num_boosted_rounds())
    if tree_count != N_TREE:
        raise SystemExit(f"{tag} 模型树数应为 {N_TREE}，实为 {tree_count}")
    device = configure_prediction_device(booster, tag)
    return booster, {
        "filename": path.name,
        "sha256": sha256_file(path),
        "num_boosted_rounds": tree_count,
        "prediction_device": device,
    }


def score_oof_first_exposures(
    xgb_module: Any,
    torch_module: Any,
    matrix: np.ndarray,
    fold_of_entity: np.ndarray,
    parent_root: Path,
    predict_batch: int,
    gpu_floor_gib: float,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    scores = np.full(N_ENTITY, np.nan, np.float32)
    receipts: list[dict[str, Any]] = []
    for fold in range(N_FOLD):
        entity_rows = np.flatnonzero(fold_of_entity == fold)
        path = parent_root / f"model_oof_semantic168_fold{fold}.json"
        booster, receipt = load_booster(xgb_module, path, f"semantic168/fold{fold}")
        gpu_guard(torch_module, gpu_floor_gib, f"semantic168/fold{fold}/首曝推理前")
        started = time.time()
        for start in range(0, len(entity_rows), predict_batch):
            stop = min(start + predict_batch, len(entity_rows))
            rows = entity_rows[start:stop]
            scores[rows] = np.asarray(
                booster.inplace_predict(matrix[rows]),
                np.float32,
            )
            beat(f"semantic168/fold{fold}/首曝OOF", stop, len(entity_rows), started)
        receipt.update(
            {
                "fold": fold,
                "holdout_entity_count": int(len(entity_rows)),
                "score_sha256": sha256_array(scores[entity_rows]),
            }
        )
        receipts.append(receipt)
        del booster, entity_rows
        torch_module.cuda.empty_cache()
    if not np.isfinite(scores).all():
        raise SystemExit("源年首曝折外分数存在未覆盖或非有限实体")
    return scores, receipts


def strict_empirical_threshold(values: np.ndarray, rate: float) -> dict[str, Any]:
    finite = np.asarray(values, np.float64)
    if len(finite) == 0 or not np.isfinite(finite).all():
        raise ValueError("阈值选择没有有限良性实体分数")
    count_cap = int(math.floor(rate * len(finite)))
    ordered = np.sort(finite)
    order_index = len(ordered) - count_cap - 1
    if order_index < 0 or order_index >= len(ordered):
        raise ValueError("严格阈值次序索引不可计算")
    threshold = float(ordered[order_index])
    selected = int((finite > threshold).sum())
    if selected > count_cap:
        raise AssertionError("严格阈值拆分并列组或超过经验预算")
    return {
        "threshold": threshold,
        "population": int(len(finite)),
        "rate_requested": rate,
        "count_cap": count_cap,
        "strictly_above_count": selected,
        "empirical_fpr": selected / len(finite),
        "order_statistic_index_zero_based": order_index,
        "boundary_tie_count": int((finite == threshold).sum()),
        "comparison_operator": ">",
        "tie_policy": "阈值同分实体全部不告警，不拆并列组",
    }


def log_binomial_cdf(k: int, n: int, probability: float) -> float:
    if k < 0:
        return -math.inf
    if k >= n or probability <= 0.0:
        return 0.0
    if probability >= 1.0:
        return -math.inf
    log_p = math.log(probability)
    log_q = math.log1p(-probability)
    terms = [
        math.lgamma(n + 1)
        - math.lgamma(index + 1)
        - math.lgamma(n - index + 1)
        + index * log_p
        + (n - index) * log_q
        for index in range(k + 1)
    ]
    maximum = max(terms)
    return maximum + math.log(math.fsum(math.exp(term - maximum) for term in terms))


def clopper_pearson_upper(k: int, n: int, delta: float) -> float | None:
    if n <= 0 or k < 0 or k > n or not 0.0 < delta < 1.0:
        return None
    if k == n:
        return 1.0
    if k == 0:
        return -math.expm1(math.log(delta) / n)
    target = math.log(delta)
    lower = k / n
    upper = 1.0
    for _ in range(100):
        middle = (lower + upper) / 2.0
        if log_binomial_cdf(k, n, middle) > target:
            lower = middle
        else:
            upper = middle
    result = (lower + upper) / 2.0
    return result if math.isfinite(result) else None


def role_receipt(
    role: str,
    fold: int,
    entity_ids: np.ndarray,
    labels: np.ndarray,
    scores: np.ndarray,
) -> dict[str, Any]:
    negative = labels == 0
    positive = labels == 1
    _, tie_counts = np.unique(scores, return_counts=True)
    return {
        "role": role,
        "fold": fold,
        "entity_count": int(len(entity_ids)),
        "negative_entity_count": int(negative.sum()),
        "positive_entity_count": int(positive.sum()),
        "duplicate_entity_key_count": int(len(entity_ids) - len(np.unique(entity_ids))),
        "entity_key_sha256": sha256_array(entity_ids.astype(np.int64, copy=False)),
        "score_sha256": sha256_array(scores.astype(np.float32, copy=False)),
        "finite_score_count": int(np.isfinite(scores).sum()),
        "score_minimum": float(scores.min()),
        "score_maximum": float(scores.max()),
        "largest_tie_group": int(tie_counts.max()),
    }


def evaluate_rule(threshold: float, labels: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    predicted = scores > threshold
    negative = labels == 0
    positive = labels == 1
    false_positive = int((predicted & negative).sum())
    true_positive = int((predicted & positive).sum())
    negative_count = int(negative.sum())
    positive_count = int(positive.sum())
    return {
        "threshold": threshold,
        "comparison_operator": ">",
        "negative_entity_count": negative_count,
        "positive_entity_count": positive_count,
        "false_positive_count": false_positive,
        "true_positive_count": true_positive,
        "entity_fpr": false_positive / negative_count,
        "detection_rate": true_positive / positive_count,
    }


def verify_role_disjointness(role_ids: dict[str, np.ndarray]) -> dict[str, Any]:
    intersections: dict[str, int] = {}
    roles = tuple(role_ids)
    for left_index, left in enumerate(roles):
        for right in roles[left_index + 1 :]:
            intersections[f"{left}__{right}"] = int(
                np.intersect1d(role_ids[left], role_ids[right]).size
            )
    return {
        "pairwise_intersection_counts": intersections,
        "all_pairwise_disjoint": all(value == 0 for value in intersections.values()),
    }


def main() -> None:
    args = parse_args()
    config = load_json(args.config)
    if not isinstance(config, dict):
        raise SystemExit("配置顶层必须是对象")
    validate_config(config)
    if args.validate_config:
        print("SOURCE_Q0_CONFIG_VALID", flush=True)
        return
    parent = validate_parent_and_inputs(args, config)
    if args.validate_inputs:
        print("SOURCE_Q0_INPUTS_VALID", flush=True)
        return

    protected = (
        "source-threshold-seal.json",
        "target-candidate-seal.json",
        "aggregate-results.json",
        "swanlab-receipt.json",
        "manifest.json",
    )
    if any((args.out / name).exists() for name in protected):
        raise SystemExit(f"同名科学制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    script_sha = sha256_file(Path(__file__).resolve())
    config_sha = sha256_file(args.config.resolve())
    log("阶段一：只读加载五个 LSPR23 数组并重建既有实体折")
    raw_values = guarded_source_load("X23")
    labels = guarded_source_load("y23")
    sequence_entities = guarded_source_load("E23")
    indices = guarded_source_load("I23")
    masks = guarded_source_load("M23")
    structure = scan_source_structure(labels, indices, masks, sequence_entities)
    fold_of_entity = make_folds(structure["entity_labels"], int(config["seed"]))
    actual_fold_stats = fold_statistics(
        fold_of_entity,
        structure["entity_labels"],
        structure["entity_flow_counts"],
        structure["entity_positive_flow_counts"],
    )
    if actual_fold_stats != parent["selection"].get("fold_stat"):
        raise SystemExit("源实体三折统计与父选择收据不符")
    fold_sha = sha256_array(fold_of_entity)
    entity_ids = structure["entity_ids"]
    role_ids = {
        role: entity_ids[fold_of_entity == fold] for fold, role in ROLE_BY_FOLD.items()
    }
    disjointness = verify_role_disjointness(role_ids)
    if not disjointness["all_pairwise_disjoint"]:
        raise SystemExit("开发、校准与持出实体键发生交叉")

    log("阶段二：构造 observation_index=1 的 semantic168 并用三个父折模型重算 OOF 分数")
    first_matrix = build_first_exposure_semantic168(raw_values, structure["first_flow"])
    del raw_values, indices, masks, sequence_entities
    import torch
    import xgboost as xgb

    if xgb.__version__ != "3.2.0" or xgb.build_info().get("USE_CUDA") is not True:
        raise SystemExit(
            f"XGBoost 环境不符：version={xgb.__version__} "
            f"USE_CUDA={xgb.build_info().get('USE_CUDA')}"
        )
    if not torch.cuda.is_available():
        raise SystemExit("CUDA 不可用，拒绝以 CPU 冒充父模型 GPU 推理")
    source_scores, model_receipts = score_oof_first_exposures(
        xgb,
        torch,
        first_matrix,
        fold_of_entity,
        args.parent_run_root.resolve(),
        int(config["predict_batch"]),
        float(config["resource_contract"]["runtime_gpu_floor_gib"]),
    )
    del first_matrix
    torch.cuda.empty_cache()

    entity_labels = structure["entity_labels"]
    budget = float(config["entity_fpr_budget"])
    delta = float(config["confirmation_failure_probability"])
    all_negative_scores = source_scores[entity_labels == 0]
    source_threshold = strict_empirical_threshold(all_negative_scores, budget)
    source_seal_payload = {
        "schema_version": "ch4-xgb-confidence-fallback-source-threshold-seal-v1",
        "run_id": RUN_ID,
        "sealed_before_development_selection": True,
        "source_threshold": source_threshold,
        "entity_count": N_ENTITY,
        "negative_entity_count": int((entity_labels == 0).sum()),
        "entity_key_sha256": sha256_array(entity_ids),
        "score_sha256": sha256_array(source_scores),
        "negative_score_sha256": sha256_array(all_negative_scores),
        "fold_assignment_sha256": fold_sha,
        "parent_selection_sha256": parent["selection_sha256"],
        "source_model_receipts": model_receipts,
        "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
        "new_models_trained": NEW_MODELS_TRAINED,
    }
    source_seal_payload["receipt_sha256"] = canonical_sha256(source_seal_payload)
    atomic_json(args.out / "source-threshold-seal.json", source_seal_payload)
    log("源阈值已在开发折选阈值前封印")

    role_receipts: dict[str, Any] = {}
    for fold, role in ROLE_BY_FOLD.items():
        mask = fold_of_entity == fold
        role_receipts[role] = role_receipt(
            role,
            fold,
            entity_ids[mask],
            entity_labels[mask],
            source_scores[mask],
        )

    log("阶段三：fold0 只选择一个严格阈值并立即封印")
    development = fold_of_entity == config["fold_roles"]["development"]
    development_negative_scores = source_scores[development & (entity_labels == 0)]
    candidate_threshold: dict[str, Any] | None
    candidate_failure_reason: str | None = None
    try:
        candidate_threshold = strict_empirical_threshold(
            development_negative_scores,
            budget,
        )
    except ValueError as error:
        candidate_threshold = None
        candidate_failure_reason = f"development_candidate_unavailable:{error}"
    candidate_seal_payload = {
        "schema_version": "ch4-xgb-confidence-fallback-target-candidate-seal-v1",
        "run_id": RUN_ID,
        "candidate_count": 1 if candidate_threshold is not None else 0,
        "candidate_search_count": 0,
        "development_fold": 0,
        "development_negative_entity_count": int(len(development_negative_scores)),
        "development_negative_score_sha256": sha256_array(development_negative_scores),
        "target_candidate": candidate_threshold,
        "candidate_failure_reason": candidate_failure_reason,
        "sealed_before_calibration_confirmation": True,
        "source_threshold_receipt_sha256": source_seal_payload["receipt_sha256"],
        "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
    }
    candidate_seal_payload["receipt_sha256"] = canonical_sha256(candidate_seal_payload)
    atomic_json(args.out / "target-candidate-seal.json", candidate_seal_payload)

    log("阶段四：fold1 只确认已封印的唯一候选，失败即回退源阈值")
    calibration = fold_of_entity == config["fold_roles"]["calibration"]
    calibration_negative = calibration & (entity_labels == 0)
    calibration_negative_count = int(calibration_negative.sum())
    minimum_units = int(config["minimum_zero_error_calibration_negatives"])
    false_positive: int | None = None
    upper: float | None = None
    confirmed = False
    fallback_reason: str | None = None
    if candidate_threshold is None:
        fallback_reason = candidate_failure_reason
    elif calibration_negative_count < minimum_units:
        fallback_reason = "calibration_negative_entities_insufficient"
    else:
        threshold_value = float(candidate_threshold["threshold"])
        false_positive = int((source_scores[calibration_negative] > threshold_value).sum())
        upper = clopper_pearson_upper(false_positive, calibration_negative_count, delta)
        if upper is None:
            fallback_reason = "clopper_pearson_upper_not_computable"
        elif upper > budget:
            fallback_reason = "clopper_pearson_upper_exceeds_budget"
        else:
            confirmed = True
    active_threshold = (
        float(candidate_threshold["threshold"])
        if confirmed and candidate_threshold is not None
        else float(source_threshold["threshold"])
    )
    decision_source = "target_confirmed" if confirmed else "source_fallback"
    certificate = {
        "schema_version": "ch4-xgb-confidence-fallback-certificate-v1",
        "budget": budget,
        "failure_probability": delta,
        "confidence_level": 1.0 - delta,
        "minimum_zero_error_negative_entities": minimum_units,
        "calibration_negative_entities": calibration_negative_count,
        "calibration_false_positive_entities": false_positive,
        "calibration_empirical_fpr": (
            false_positive / calibration_negative_count
            if false_positive is not None and calibration_negative_count
            else None
        ),
        "clopper_pearson_upper": upper,
        "target_confirmed": confirmed,
        "decision_source": decision_source,
        "fallback_reason": fallback_reason,
        "candidate_receipt_sha256": candidate_seal_payload["receipt_sha256"],
    }
    certificate["certificate_sha256"] = canonical_sha256(certificate)

    log("阶段五：fold2 只评价冻结源阈值、未确认诊断阈值与最终活动阈值")
    holdout = fold_of_entity == config["fold_roles"]["holdout"]
    holdout_labels = entity_labels[holdout]
    holdout_scores = source_scores[holdout]
    source_metrics = evaluate_rule(
        float(source_threshold["threshold"]), holdout_labels, holdout_scores
    )
    candidate_metrics = (
        evaluate_rule(
            float(candidate_threshold["threshold"]), holdout_labels, holdout_scores
        )
        if candidate_threshold is not None
        else None
    )
    active_metrics = evaluate_rule(active_threshold, holdout_labels, holdout_scores)

    gates = {
        "gate_1_parent_and_score_reproduction": {
            "passed": True,
            "base_adapter": "semantic168",
            "power_mean_p": 1.0,
            "fold_statistics_match_parent": True,
            "score_sha256": sha256_array(source_scores),
        },
        "gate_2_role_isolation_and_units": {
            "passed": disjointness["all_pairwise_disjoint"]
            and calibration_negative_count >= minimum_units,
            **disjointness,
            "calibration_negative_entities": calibration_negative_count,
            "minimum_required": minimum_units,
        },
        "gate_3_single_finite_candidate": {
            "passed": candidate_threshold is not None
            and math.isfinite(float(candidate_threshold["threshold"])),
            "candidate_count": candidate_seal_payload["candidate_count"],
            "candidate_search_count": 0,
        },
        "gate_4_confirmation_without_fallback": {
            "passed": confirmed and upper is not None and upper <= budget,
            "clopper_pearson_upper": upper,
            "decision_source": decision_source,
        },
        "gate_5_holdout_candidate_fpr": {
            "passed": candidate_metrics is not None
            and candidate_metrics["entity_fpr"] <= budget,
            "candidate_entity_fpr": (
                candidate_metrics["entity_fpr"] if candidate_metrics is not None else None
            ),
        },
        "gate_6_holdout_candidate_dr_gain": {
            "passed": candidate_metrics is not None
            and candidate_metrics["detection_rate"] > source_metrics["detection_rate"],
            "candidate_detection_rate": (
                candidate_metrics["detection_rate"] if candidate_metrics is not None else None
            ),
            "source_detection_rate": source_metrics["detection_rate"],
        },
        "gate_7_source_only_frozen_contract": {
            "passed": TARGET_YEAR_ARRAYS_READ == 0
            and NEW_MODELS_TRAINED == 0
            and config["observation_index"] == 1
            and config["candidate_count"] == 1,
            "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
            "new_models_trained": NEW_MODELS_TRAINED,
            "observation_index": config["observation_index"],
        },
    }
    qualified = all(item["passed"] for item in gates.values())
    result = {
        "schema_version": "ch4-xgb-confidence-fallback-source-q0-results-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "evidence": {
            "screening_only": True,
            "formal": False,
            "formal_paper_evidence": False,
            "independent_test": False,
            "source_year_pseudo_target_only": True,
        },
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "parent": {
            "run_id": PARENT_RUN_ID,
            "parent_config_sha256": parent["parent_config_sha256"],
            "parent_recovery_proof_sha256": parent["parent_recovery_proof_sha256"],
            "selection_sha256": parent["selection_sha256"],
            "artifact_sha256": parent["artifact_sha256"],
            "source_model_receipts": model_receipts,
        },
        "contract": {
            "base_adapter": "semantic168",
            "power_mean_p": 1.0,
            "observation_index": 1,
            "candidate_count": 1,
            "candidate_search_count": 0,
            "comparison_operator": ">",
            "entity_fpr_budget": budget,
            "confirmation_failure_probability": delta,
            "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
            "new_models_trained": NEW_MODELS_TRAINED,
        },
        "folds": {
            "assignment": "seeded-stratified-entity-round-robin",
            "assignment_sha256": fold_sha,
            "statistics": actual_fold_stats,
            "roles": role_receipts,
            "disjointness": disjointness,
        },
        "source_threshold": source_seal_payload,
        "target_candidate": candidate_seal_payload,
        "target_certificate": certificate,
        "decision": {
            "active_threshold": active_threshold,
            "decision_source": decision_source,
            "fallback_reason": fallback_reason,
            "rule_version": certificate["certificate_sha256"],
        },
        "holdout_evaluation": {
            "source_threshold_baseline": source_metrics,
            "target_candidate_without_confirmation_diagnostic": candidate_metrics,
            "final_active_rule": active_metrics,
            "source_threshold_not_independent_of_holdout": True,
        },
        "direction_gates": gates,
        "mechanical_verdict": {
            "qualified": qualified,
            "verdict": (
                "source_year_pseudo_target_direction_signal"
                if qualified
                else "mechanism_2_rejected_at_source_q0"
            ),
            "forbidden_claims": [
                "跨年度有效",
                "LSPR24 实体假阳率受控",
                "第四章正式算法成立",
            ],
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "fold_membership_persisted": False,
            "label_details_persisted": False,
            "new_models_persisted": False,
            "aggregate_receipts_only": True,
        },
        "timing": {"total_seconds": time.time() - T0},
    }
    result_path = args.out / "aggregate-results.json"
    atomic_json(result_path, result)

    import swanlab

    tracking = config["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=RUN_ID,
        config={
            "seed": 42,
            "source_year_only": True,
            "zero_training": True,
            "base_adapter": "semantic168",
            "power_mean_p": 1.0,
            "observation_index": 1,
            "candidate_count": 1,
            "entity_fpr_budget": budget,
            "confirmation_failure_probability": delta,
            "script_sha256": script_sha,
            "config_sha256": config_sha,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )
    metrics: dict[str, float | int] = {
        "calibration/negative_entities": calibration_negative_count,
        "calibration/clopper_pearson_upper": upper if upper is not None else 1.0,
        "holdout/source_fpr": source_metrics["entity_fpr"],
        "holdout/source_detection_rate": source_metrics["detection_rate"],
        "holdout/active_fpr": active_metrics["entity_fpr"],
        "holdout/active_detection_rate": active_metrics["detection_rate"],
        "verdict/qualified": int(qualified),
        "runtime/total_seconds": result["timing"]["total_seconds"],
    }
    if false_positive is not None:
        metrics["calibration/false_positive_entities"] = false_positive
    if candidate_metrics is not None:
        metrics["holdout/candidate_fpr"] = candidate_metrics["entity_fpr"]
        metrics["holdout/candidate_detection_rate"] = candidate_metrics["detection_rate"]
    swanlab.log(metrics, step=0)
    swanlab.finish()
    atomic_json(
        args.out / "swanlab-receipt.json",
        {
            "schema_version": "ch4-xgb-confidence-fallback-source-q0-swanlab-v1",
            "completed": True,
            "workspace": tracking["workspace"],
            "project": tracking["project"],
            "mode": tracking["mode"],
            "aggregate_only": True,
            "metric_keys": sorted(metrics),
            "per_sample_values_uploaded": False,
        },
    )

    manifest_names = (
        "resource-receipt.json",
        "source-threshold-seal.json",
        "target-candidate-seal.json",
        "aggregate-results.json",
        "swanlab-receipt.json",
    )
    manifest = {
        "schema_version": "ch4-xgb-confidence-fallback-source-q0-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "target_year_arrays_read": TARGET_YEAR_ARRAYS_READ,
        "new_models_trained": NEW_MODELS_TRAINED,
        "per_sample_artifacts_persisted": False,
        "files": {},
    }
    for name in manifest_names:
        path = args.out / name
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"必需聚合制品缺失：{path}")
        manifest["files"][name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    atomic_json(args.out / "manifest.json", manifest)
    log(f"源年 Q0 聚合结果已保存：{result_path}")


if __name__ == "__main__":
    main()
