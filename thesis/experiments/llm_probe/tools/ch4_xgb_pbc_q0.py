#!/usr/bin/env python3
"""XGBoost 基座上的先导段预算标定零训练 Q0。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

from ch3_xgb_cpa_elp_eval_continuation import (  # noqa: E402
    BOOLEAN_IDX,
    CACHE,
    CATEGORICAL_IDX,
    CONTINUATION_RUN_ID,
    D_RAW,
    EXPECTED_XGB_PARAMS,
    N_FLOW_24,
    NUMERIC_IDX,
    PARENT_RUN_ID,
    atomic_json,
    configure_prediction_device,
    gpu_guard,
    predict_rows,
    sha256_file,
    validate_parent_inputs,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-pbc-q0-seed42-v1-rerun2"
N_FLOW_23 = 16_353_511
N_ENTITY_23 = 150_680
N_POS_ENTITY_23 = 239
N_ENTITY_24 = 47_115
N_POS_ENTITY_24 = 752
N_FOLD = 3
N_TREE = 800
SEQUENCE_LENGTH = 128
EXPECTED_PARENT_RESULT_SHA256 = (
    "128b1225c96bb07c5b808dc2e0092223d1acb4c039b487a7007551a4f6b5135f"
)
EXPECTED_PARENT_EVAL_MANIFEST_SHA256 = (
    "f6b66cc94ef09b169ff29ce317464109bc701fa109875f6e9b7d09c889516115"
)
PARENT_RECOVERY_PROOF_SCHEMA_VERSION = "ch3-xgb-parent-recovery-proof-v1"
PARENT_RECOVERY_PROOF_FILENAME = "parent-recovery-proof.json"
PARENT_RECOVERY_ARTIFACTS = (
    "selection_frozen_xgb2x2.json",
    "effective_config_receipts.json",
    "model_raw83.json",
    "model_semantic168.json",
    "model_oof_semantic168_fold0.json",
    "model_oof_semantic168_fold1.json",
    "model_oof_semantic168_fold2.json",
)
PARENT_RECOVERY_EFFECTIVE_TAGS = {
    "raw83/final",
    "semantic168/final",
    "semantic168/fold0",
    "semantic168/fold1",
    "semantic168/fold2",
}
METHODS = (
    "source_frozen",
    "pilot_quantile",
    "bbse_prior_correction",
    "pbc",
)
METHOD_DISPLAY_NAMES = {
    "source_frozen": "源冻结阈值",
    "pilot_quantile": "普通无标签先导段分位标定",
    "bbse_prior_correction": "BBSE 先验校正",
    "pbc": "先导段预算标定（PBC）",
}
T0 = time.time()
LAST_BEAT = [T0]


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


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="XGBoost PBC 先导段预算标定零训练 Q0")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/ch4-xgb-pbc-q0-seed42-v1.json",
    )
    parser.add_argument(
        "--parent-run-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / PARENT_RUN_ID,
    )
    parser.add_argument(
        "--parent-eval-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / CONTINUATION_RUN_ID,
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
            / f"{PARENT_RUN_ID}-for-{RUN_ID}-v1"
            / PARENT_RECOVERY_PROOF_FILENAME
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "runs/candidates" / RUN_ID,
    )
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    expected_exact = {
        "schema_version": "ch4-xgb-pbc-q0-v1",
        "run_id": RUN_ID,
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "parent_run_id": PARENT_RUN_ID,
        "parent_eval_run_id": CONTINUATION_RUN_ID,
        "parent_recovery_proof": {
            "schema_version": PARENT_RECOVERY_PROOF_SCHEMA_VERSION,
            "requires_parent_incomplete": True,
            "original_manifest_expected": False,
        },
        "base_view": "semantic168",
        "power_mean_p": 1.0,
        "pilot_time_fractions": [0.1, 0.2, 0.3, 0.5],
        "entity_fpr_budgets": [0.01, 0.02, 0.04],
        "bbse_source_fpr_grid": [0.001, 0.002, 0.005, 0.01, 0.02, 0.04, 0.08],
        "artifact_policy": {
            "persist_aggregate_json": True,
            "persist_status_log_manifest_resource": True,
            "persist_per_flow_scores": False,
            "persist_per_entity_scores": False,
            "persist_derived_matrices": False,
            "persist_label_details": False,
            "persist_new_models": False,
        },
    }
    for key, expected in expected_exact.items():
        if config.get(key) != expected:
            raise SystemExit(f"PBC 配置字段不符：{key}")
    expected_provenance = {
        "0.01": "预注册保守敏感性，不是安全标准",
        "0.02": "预注册保守敏感性，不是安全标准",
        "0.04": "Gehri 同源经验工作点，不是安全标准",
    }
    if config.get("budget_provenance") != expected_provenance:
        raise SystemExit("预算来源说明与冻结合同不符")
    numeric_positive = (
        "bbse_min_tpr_fpr_separation",
        "bbse_min_confusion_singular_value",
        "bbse_prior_margin",
        "mismatch_dkw_alpha",
        "time_unit_per_second",
        "predict_batch",
        "sequence_batch",
        "gpu_need_gib",
        "gpu_floor_gib",
        "estimated_peak_host_gib",
    )
    if any(float(config.get(key, 0)) <= 0 for key in numeric_positive):
        raise SystemExit("PBC 数值配置必须为正")
    if not 0 < float(config["mismatch_dkw_alpha"]) < 1:
        raise SystemExit("DKW 显著性水平必须位于 (0,1)")
    if not 0 < float(config["bbse_prior_margin"]) < 0.5:
        raise SystemExit("BBSE 先验内点余量必须位于 (0,0.5)")
    if config.get("expected_time_span_hours") != [140.0, 144.0]:
        raise SystemExit("目标时间跨度门与冻结合同不符")
    tracking = config.get("tracking", {})
    if tracking != {
        "workspace": "mortiswang",
        "project": "ns3-rwkv-lspr24",
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 目的地或聚合模式与授权合同不符")


def validate_inputs(args: argparse.Namespace, config: dict[str, Any]) -> dict[str, Any]:
    if args.out.resolve().name != RUN_ID:
        raise SystemExit(f"输出运行身份必须为 {RUN_ID}")
    parent_args = argparse.Namespace(
        parent_run_root=args.parent_run_root,
        parent_config=args.parent_config,
        out=args.out,
        bootstrap=1,
        predict_batch=int(config["predict_batch"]),
        sequence_batch=int(config["sequence_batch"]),
    )
    parent = validate_parent_inputs(parent_args)
    if parent["selected_adapter"] != "semantic168":
        raise SystemExit("父运行适配器不是 semantic168")
    if float(parent["p_selection"]["semantic168"]) != 1.0:
        raise SystemExit("父运行 semantic168 的 p 不是 1.0")

    parent_eval_root = args.parent_eval_root.resolve()
    if parent_eval_root.name != CONTINUATION_RUN_ID:
        raise SystemExit(f"父评价身份不符：{parent_eval_root.name}")
    expected_eval = {
        "xgb_cpa_elp_results.json": EXPECTED_PARENT_RESULT_SHA256,
        "manifest.json": EXPECTED_PARENT_EVAL_MANIFEST_SHA256,
    }
    eval_hashes: dict[str, str] = {}
    for name, expected in expected_eval.items():
        path = parent_eval_root / name
        if not path.is_file():
            raise SystemExit(f"父评价制品缺失：{path}")
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"父评价制品摘要不符：{name}")
        eval_hashes[name] = actual
    status = load_json(parent_eval_root / "status.json")
    if (
        status.get("state") != "finished"
        or status.get("stage") != "complete"
        or status.get("exit_code") != 0
    ):
        raise SystemExit("父评价未处于 finished/complete/exit=0")
    parent_result = load_json(parent_eval_root / "xgb_cpa_elp_results.json")
    if parent_result.get("isolation", {}).get("target_score_calls") != 2:
        raise SystemExit("父评价没有两次目标预测收据")
    if parent_result.get("isolation", {}).get("target_scores_persisted") is not False:
        raise SystemExit("父评价逐流分数持久化声明异常")

    proof_path = args.parent_recovery_proof.resolve()
    if proof_path.name != PARENT_RECOVERY_PROOF_FILENAME or not proof_path.is_file():
        raise SystemExit(f"父恢复证明缺失或文件名不符：{proof_path}")
    if args.parent_run_root.resolve() in proof_path.parents:
        raise SystemExit("父恢复证明不得位于父运行目录内")
    proof = load_json(proof_path)
    if proof.get("schema_version") != PARENT_RECOVERY_PROOF_SCHEMA_VERSION:
        raise SystemExit("父恢复证明模式版本不符")
    if proof.get("parent_run_id") != PARENT_RUN_ID:
        raise SystemExit("父恢复证明运行身份不符")
    if Path(str(proof.get("parent_run_root", ""))).resolve() != args.parent_run_root.resolve():
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
    parent_status_path = args.parent_run_root.resolve() / "status.json"
    if (
        not parent_status_path.is_file()
        or historical_status.get("filename") != parent_status_path.name
        or historical_status.get("sha256") != sha256_file(parent_status_path)
        or historical_status.get("bytes") != parent_status_path.stat().st_size
    ):
        raise SystemExit("父实际状态与恢复证明不符")
    for name in parent_state["missing_completion_artifacts"]:
        if (args.parent_run_root.resolve() / name).exists():
            raise SystemExit(f"父运行出现证明声明缺失的完成制品：{name}")
    proof_artifacts = proof.get("artifacts", {})
    artifact_hashes: dict[str, str] = {}
    for name in PARENT_RECOVERY_ARTIFACTS:
        path = args.parent_run_root.resolve() / name
        receipt = proof_artifacts.get(name, {})
        if not path.is_file() or not receipt:
            raise SystemExit(f"父恢复证明或实际制品缺失：{name}")
        actual = sha256_file(path)
        if actual != receipt.get("sha256") or path.stat().st_size != receipt.get("bytes"):
            raise SystemExit(f"父制品与恢复证明不符：{name}")
        if name.startswith("model_") and receipt.get("num_boosted_rounds") != N_TREE:
            raise SystemExit(f"父恢复证明中的模型树数不是 {N_TREE}：{name}")
        artifact_hashes[name] = actual
    effective_summary = proof.get("effective_config_receipts", {})
    if (
        effective_summary.get("receipt_count") != 11
        or effective_summary.get("all_passed") is not True
        or set(effective_summary.get("required_dependency_tags", []))
        != PARENT_RECOVERY_EFFECTIVE_TAGS
    ):
        raise SystemExit("父恢复证明中的有效配置收据摘要不符")

    required_cache = (
        "X23",
        "y23",
        "I23",
        "M23",
        "ent23",
        "t23_flow",
        "X24",
        "y24",
        "I24",
        "M24",
        "s24",
        "d24",
        "t24",
    )
    for name in required_cache:
        path = CACHE / f"{name}.npy"
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"共享缓存缺失或为空：{path}")

    parent["parent_eval_root"] = str(parent_eval_root)
    parent["parent_eval_sha256"] = eval_hashes
    parent["parent_recovery_proof_path"] = str(proof_path)
    parent["parent_recovery_proof_sha256"] = sha256_file(proof_path)
    parent["recovery_artifact_sha256"] = artifact_hashes
    return parent


def assert_sequence_time_monotonic(
    time_values: np.ndarray,
    indices: np.ndarray,
    mask: np.ndarray,
    expected_flow_count: int,
    tag: str,
) -> None:
    if len(time_values) != expected_flow_count or not np.isfinite(time_values).all():
        raise SystemExit(f"{tag} 时间戳数量异常或含非有限值")
    reversed_pairs = 0
    checked_pairs = 0
    started = time.time()
    for start in range(0, len(indices), 20_000):
        idx = indices[start : start + 20_000]
        valid = mask[start : start + 20_000] > 0
        timestamp = time_values[idx]
        adjacent = valid[:, 1:] & valid[:, :-1]
        checked_pairs += int(adjacent.sum())
        reversed_pairs += int(((timestamp[:, 1:] < timestamp[:, :-1]) & adjacent).sum())
        beat(f"{tag}/时间核验", min(start + 20_000, len(indices)), len(indices), started)
    if reversed_pairs:
        raise SystemExit(f"{tag} 序列存在 {reversed_pairs} 个时间逆序相邻对")
    log(f"{tag} 时间非降核验通过：{checked_pairs:,} 个有效相邻对")


def build_semantic_matrix(
    x_path: Path,
    n_flow: int,
    indices: np.ndarray,
    mask_values: np.ndarray,
    predict_batch: int,
    sequence_batch: int,
    tag: str,
) -> np.ndarray:
    """按父工具同构公式重建 semantic168，仅驻内存。"""
    if indices.shape[1] != SEQUENCE_LENGTH or mask_values.shape != indices.shape:
        raise SystemExit(f"{tag} 序列形状异常：I={indices.shape} M={mask_values.shape}")
    n_valid = int((mask_values > 0).sum())
    if n_valid != n_flow:
        raise SystemExit(f"{tag} 掩码有效位 {n_valid:,} 与流数 {n_flow:,} 不符")
    dimension = D_RAW + len(NUMERIC_IDX) + len(CATEGORICAL_IDX) + len(BOOLEAN_IDX) + 2
    if dimension != 168:
        raise SystemExit(f"semantic168 维度推导异常：{dimension}")

    output = np.empty((n_flow, dimension), np.float32)
    source = np.load(x_path, mmap_mode="r")
    if source.shape != (n_flow, D_RAW):
        raise SystemExit(f"{tag} 原始宽表形状不符：{source.shape}")
    started = time.time()
    for start in range(0, n_flow, predict_batch):
        stop = min(start + predict_batch, n_flow)
        output[start:stop, :D_RAW] = source[start:stop]
        beat(f"{tag}/读入raw83", stop, n_flow, started)
    del source

    cover = np.zeros(n_flow, bool)
    lower = np.tri(SEQUENCE_LENGTH, SEQUENCE_LENGTH, dtype=bool)
    started = time.time()
    for start in range(0, len(indices), sequence_batch):
        idx = indices[start : start + sequence_batch]
        mask = mask_values[start : start + sequence_batch] > 0
        batch, width = idx.shape
        flat = idx.reshape(-1)
        current = output[flat, :D_RAW].reshape(batch, width, D_RAW)
        count = np.cumsum(mask, axis=1, dtype=np.int32)
        denominator = np.maximum(count, 1).astype(np.float32)
        valid_flat = mask.reshape(-1)
        target = flat[valid_flat]

        numeric = current[:, :, NUMERIC_IDX]
        numeric_sum = np.cumsum(numeric * mask[:, :, None], axis=1, dtype=np.float64)
        residual = numeric - numeric_sum / denominator[:, :, None]
        cursor = D_RAW
        output[target, cursor : cursor + len(NUMERIC_IDX)] = residual.reshape(
            -1,
            len(NUMERIC_IDX),
        )[valid_flat]
        cursor += len(NUMERIC_IDX)

        prefix_mask = lower[None, :, :] & mask[:, None, :]
        for feature_idx in CATEGORICAL_IDX:
            value = current[:, :, feature_idx]
            equal = value[:, :, None] == value[:, None, :]
            frequency = (equal & prefix_mask).sum(axis=2) / denominator
            output[target, cursor] = frequency.reshape(-1)[valid_flat]
            cursor += 1

        for feature_idx in BOOLEAN_IDX:
            truth = (current[:, :, feature_idx] > 0) & mask
            truth_rate = np.cumsum(truth, axis=1) / denominator
            output[target, cursor] = truth_rate.reshape(-1)[valid_flat]
            cursor += 1

        output[target, cursor] = np.log1p(count).reshape(-1)[valid_flat]
        cursor += 1
        output[target, cursor] = (count == 1).reshape(-1)[valid_flat]
        cursor += 1
        if cursor != dimension:
            raise AssertionError(f"semantic168 游标异常：{cursor}")
        cover[target] = True
        beat(f"{tag}/semantic168", min(start + sequence_batch, len(indices)), len(indices), started)
        del current, numeric, numeric_sum, residual, prefix_mask

    if not bool(cover.all()) or not np.isfinite(output).all():
        raise SystemExit(f"{tag} semantic168 覆盖不完整或含非有限值")
    log(f"{tag} semantic168 构造完成，用时 {time.time() - started:.0f}s")
    return output


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


def predict_selected_rows(
    booster: Any,
    matrix: np.ndarray,
    rows: np.ndarray,
    batch_size: int,
    tag: str,
) -> np.ndarray:
    """只对折外留出行分批推理，避免重复扫描完整源矩阵。"""
    output = np.empty(len(rows), np.float32)
    started = time.time()
    for start in range(0, len(rows), batch_size):
        stop = min(start + batch_size, len(rows))
        output[start:stop] = booster.inplace_predict(matrix[rows[start:stop]])
        beat(tag, stop, len(rows), started)
    return output


def reconstruct_source_folds(
    labels: np.ndarray,
    entity: np.ndarray,
    parent_fold_stat: list[dict[str, Any]],
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    entity_labels = np.zeros(N_ENTITY_23, np.float32)
    np.maximum.at(entity_labels, entity, labels)
    if int(entity_labels.sum()) != N_POS_ENTITY_23:
        raise SystemExit(f"LSPR23 正实体数不符：{int(entity_labels.sum())}")
    random_state = np.random.RandomState(seed)
    fold_of_entity = np.empty(N_ENTITY_23, np.int64)
    for group in (0.0, 1.0):
        ids = np.flatnonzero(entity_labels == group)
        ids = ids[random_state.permutation(len(ids))]
        fold_of_entity[ids] = np.arange(len(ids)) % N_FOLD
    fold_of_flow = fold_of_entity[entity]
    actual: list[dict[str, int]] = []
    for fold in range(N_FOLD):
        entity_mask = fold_of_entity == fold
        flow_mask = fold_of_flow == fold
        actual.append(
            {
                "fold": fold,
                "n_entity": int(entity_mask.sum()),
                "n_pos_entity": int(entity_labels[entity_mask].sum()),
                "n_flow": int(flow_mask.sum()),
                "n_pos_flow": int(labels[flow_mask].sum()),
            }
        )
    if actual != parent_fold_stat:
        raise SystemExit("源折号重建统计与父选择收据不符")
    return fold_of_flow, fold_of_entity, entity_labels


def mean_entity_scores(scores: np.ndarray, entity: np.ndarray, n_entity: int) -> np.ndarray:
    numerator = np.zeros(n_entity, np.float64)
    count = np.zeros(n_entity, np.int64)
    np.add.at(numerator, entity, scores.astype(np.float64, copy=False))
    np.add.at(count, entity, 1)
    if np.any(count == 0):
        raise SystemExit("实体平均分存在零支持实体")
    return (numerator / count).astype(np.float32)


def conservative_threshold(values: np.ndarray, rate: float) -> dict[str, Any]:
    """选择不拆并列组且不超过数量预算的最低阈值。"""
    finite = np.asarray(values[np.isfinite(values)], np.float64)
    if len(finite) == 0:
        raise SystemExit("阈值选择没有有限分数")
    cap = int(math.floor(rate * len(finite)))
    unique, counts = np.unique(finite, return_counts=True)
    unique = unique[::-1]
    counts = counts[::-1]
    cumulative = np.cumsum(counts, dtype=np.int64)
    eligible = np.flatnonzero(cumulative <= cap)
    if len(eligible) == 0:
        threshold = float(np.nextafter(float(unique[0]), math.inf))
        selected = 0
        tie_count = int(counts[0])
        excluded_tie_score = float(unique[0])
    else:
        index = int(eligible[-1])
        threshold = float(unique[index])
        selected = int(cumulative[index])
        tie_count = int(counts[index])
        excluded_tie_score = None
    return {
        "threshold": threshold,
        "population": int(len(finite)),
        "rate_requested": float(rate),
        "count_cap": cap,
        "count_selected": selected,
        "selected_rate": selected / len(finite),
        "unused_capacity": cap - selected,
        "boundary_tie_count": tie_count,
        "excluded_top_tie_score": excluded_tie_score,
        "tie_policy": "同分数组整体纳入或整体排除，不拆并列",
    }


def source_operating_point(
    source_scores: np.ndarray,
    source_labels: np.ndarray,
    requested_fpr: float,
) -> dict[str, Any]:
    negative = source_scores[source_labels == 0]
    threshold_receipt = conservative_threshold(negative, requested_fpr)
    threshold = float(threshold_receipt["threshold"])
    predicted = source_scores >= threshold
    negative_mask = source_labels == 0
    positive_mask = source_labels == 1
    false_positive = int((predicted & negative_mask).sum())
    true_positive = int((predicted & positive_mask).sum())
    fpr = false_positive / int(negative_mask.sum())
    tpr = true_positive / int(positive_mask.sum())
    confusion = np.asarray([[1.0 - fpr, 1.0 - tpr], [fpr, tpr]], np.float64)
    singular_values = np.linalg.svd(confusion, compute_uv=False)
    return {
        **threshold_receipt,
        "source_fpr": fpr,
        "source_tpr": tpr,
        "source_false_positive": false_positive,
        "source_true_positive": true_positive,
        "tpr_minus_fpr": tpr - fpr,
        "confusion_min_singular_value": float(singular_values[-1]),
    }


def dkw_epsilon(sample_count: int, alpha_piece: float) -> float:
    return math.sqrt(math.log(2.0 / alpha_piece) / (2.0 * sample_count))


def cdf_components(
    source_scores: np.ndarray,
    source_labels: np.ndarray,
    target_scores: np.ndarray,
) -> dict[str, Any]:
    negative = np.sort(source_scores[source_labels == 0].astype(np.float64, copy=False))
    positive = np.sort(source_scores[source_labels == 1].astype(np.float64, copy=False))
    target = np.sort(target_scores.astype(np.float64, copy=False))
    points = np.unique(np.concatenate((negative, positive, target)))
    return {
        "negative_count": int(len(negative)),
        "positive_count": int(len(positive)),
        "target_count": int(len(target)),
        "negative_cdf": np.searchsorted(negative, points, side="right") / len(negative),
        "positive_cdf": np.searchsorted(positive, points, side="right") / len(positive),
        "target_cdf": np.searchsorted(target, points, side="right") / len(target),
    }


def bbse_candidate(
    operating_point: dict[str, Any],
    target_scores: np.ndarray,
    cdfs: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    threshold = float(operating_point["threshold"])
    target_alert_rate = float((target_scores >= threshold).mean())
    fpr = float(operating_point["source_fpr"])
    tpr = float(operating_point["source_tpr"])
    separation = tpr - fpr
    raw_prior = (target_alert_rate - fpr) / separation if abs(separation) > 1e-15 else math.nan
    reasons: list[str] = []
    if separation < float(config["bbse_min_tpr_fpr_separation"]):
        reasons.append("tpr_fpr_separation_below_gate")
    if float(operating_point["confusion_min_singular_value"]) < float(
        config["bbse_min_confusion_singular_value"]
    ):
        reasons.append("confusion_min_singular_value_below_gate")
    margin = float(config["bbse_prior_margin"])
    if not math.isfinite(raw_prior) or not margin <= raw_prior <= 1.0 - margin:
        reasons.append("estimated_prior_outside_interior")

    prior_for_diagnostic = float(np.clip(raw_prior, margin, 1.0 - margin))
    mixture_cdf = (
        (1.0 - prior_for_diagnostic) * cdfs["negative_cdf"]
        + prior_for_diagnostic * cdfs["positive_cdf"]
    )
    mismatch = float(np.max(np.abs(cdfs["target_cdf"] - mixture_cdf)))
    alpha_piece = float(config["mismatch_dkw_alpha"]) / 3.0
    tolerance = (
        dkw_epsilon(int(cdfs["target_count"]), alpha_piece)
        + (1.0 - prior_for_diagnostic)
        * dkw_epsilon(int(cdfs["negative_count"]), alpha_piece)
        + prior_for_diagnostic * dkw_epsilon(int(cdfs["positive_count"]), alpha_piece)
    )
    if mismatch > tolerance:
        reasons.append("source_conditional_mixture_mismatch")
    return {
        "candidate_source_fpr_requested": operating_point["rate_requested"],
        "source_threshold": threshold,
        "source_fpr": fpr,
        "source_tpr": tpr,
        "tpr_minus_fpr": separation,
        "confusion_min_singular_value": operating_point["confusion_min_singular_value"],
        "pilot_alert_rate": target_alert_rate,
        "estimated_target_positive_prior_raw": raw_prior,
        "estimated_target_positive_prior_for_diagnostic": prior_for_diagnostic,
        "score_mixture_sup_distance": mismatch,
        "score_mixture_dkw_tolerance": tolerance,
        "mismatch_ratio": mismatch / max(tolerance, 1e-15),
        "feasible": not reasons,
        "infeasible_reasons": reasons,
    }


def select_bbse_candidate(
    candidates: list[dict[str, Any]],
    budget: float,
) -> dict[str, Any]:
    eligible = [
        candidate
        for candidate in candidates
        if candidate["feasible"] and float(candidate["source_fpr"]) <= budget + 1e-15
    ]
    if not eligible:
        return {
            "selected": None,
            "tied_candidate_source_fprs": [],
            "reason": "no_feasible_candidate_with_source_fpr_within_budget",
        }

    def ranking_key(candidate: dict[str, Any]) -> tuple[float, float, float, float]:
        return (
            round(abs(float(candidate["source_fpr"]) - budget), 15),
            round(float(candidate["mismatch_ratio"]), 15),
            round(-float(candidate["tpr_minus_fpr"]), 15),
            round(-float(candidate["source_threshold"]), 15),
        )

    ordered = sorted(eligible, key=ranking_key)
    best_key = ranking_key(ordered[0])
    tied = [candidate for candidate in ordered if ranking_key(candidate) == best_key]
    return {
        "selected": ordered[0],
        "tied_candidate_source_fprs": [
            candidate["candidate_source_fpr_requested"] for candidate in tied
        ],
        "reason": "lexicographic_unlabeled_rule",
        "ranking_rule": [
            "source_fpr_within_budget",
            "closest_source_fpr_to_budget",
            "smaller_mismatch_ratio",
            "larger_tpr_fpr_separation",
            "larger_threshold_for_stable_conservative_tie_break",
        ],
    }


def prior_corrected_raw_threshold(
    source_threshold: float,
    source_prior: float,
    target_prior: float,
) -> float:
    epsilon = 1e-12
    threshold = float(np.clip(source_threshold, epsilon, 1.0 - epsilon))
    source_prior = float(np.clip(source_prior, epsilon, 1.0 - epsilon))
    target_prior = float(np.clip(target_prior, epsilon, 1.0 - epsilon))
    source_threshold_odds = threshold / (1.0 - threshold)
    prior_odds_ratio = (
        target_prior / (1.0 - target_prior)
    ) / (source_prior / (1.0 - source_prior))
    raw_odds = source_threshold_odds / prior_odds_ratio
    return float(raw_odds / (1.0 + raw_odds))


def freeze_methods_for_budget(
    pilot_scores: np.ndarray,
    budget: float,
    source_threshold: dict[str, Any],
    candidates: list[dict[str, Any]],
    source_prior: float,
) -> dict[str, Any]:
    source_value = float(source_threshold["threshold"])
    quantile_receipt = conservative_threshold(pilot_scores, budget)
    selection = select_bbse_candidate(candidates, budget)
    selected = selection["selected"]
    if selected is None:
        bbse_threshold = source_value
        pbc_threshold = source_value
        bbse_receipt = {
            "threshold": bbse_threshold,
            "fallback_to_source_frozen": True,
            "fallback_reason": selection["reason"],
        }
        pbc_receipt = {
            "threshold": pbc_threshold,
            "fallback_to_source_frozen": True,
            "fallback_reasons": [selection["reason"]],
            "exact_fallback_asserted": pbc_threshold == source_value,
        }
    else:
        target_prior = float(selected["estimated_target_positive_prior_raw"])
        bbse_threshold = prior_corrected_raw_threshold(
            source_value,
            source_prior,
            target_prior,
        )
        negative_share = 1.0 - target_prior
        pbc_alert_share = budget * negative_share
        pbc_quota = conservative_threshold(pilot_scores, pbc_alert_share)
        pbc_threshold = max(bbse_threshold, float(pbc_quota["threshold"]))
        active_constraints = []
        if math.isclose(pbc_threshold, bbse_threshold, rel_tol=0.0, abs_tol=0.0):
            active_constraints.append("bbse_prior_correction")
        if math.isclose(
            pbc_threshold,
            float(pbc_quota["threshold"]),
            rel_tol=0.0,
            abs_tol=0.0,
        ):
            active_constraints.append("estimated_negative_share_alert_quota")
        bbse_receipt = {
            "threshold": bbse_threshold,
            "fallback_to_source_frozen": False,
            "selected_candidate": selected,
            "assumption_boundary": "将冻结 XGBoost 分数按源/目标先验比作单调赔率校正",
        }
        pbc_receipt = {
            "threshold": pbc_threshold,
            "fallback_to_source_frozen": False,
            "selected_candidate": selected,
            "estimated_negative_share": negative_share,
            "pilot_alert_share_cap": pbc_alert_share,
            "pilot_alert_quota_receipt": pbc_quota,
            "bbse_component_threshold": bbse_threshold,
            "active_constraints": active_constraints,
            "rule": "取 BBSE 阈值与估计负实体占比告警配额阈值中更保守者",
        }

    return {
        "source_frozen": {
            "threshold": source_value,
            "source_operating_point": source_threshold,
        },
        "pilot_quantile": {
            "threshold": float(quantile_receipt["threshold"]),
            "pilot_quantile_receipt": quantile_receipt,
        },
        "bbse_prior_correction": bbse_receipt,
        "pbc": pbc_receipt,
        "bbse_candidate_selection": {
            **selection,
            "selected": None if selected is None else selected,
        },
    }


def percentile_or_none(values: np.ndarray, percentile: float) -> float | None:
    if len(values) == 0:
        return None
    return float(np.percentile(values.astype(np.float64, copy=False), percentile))


def average_precision_or_none(labels: np.ndarray, scores: np.ndarray) -> float | None:
    if len(labels) == 0 or int(labels.sum()) == 0:
        return None
    return float(average_precision_score(labels, scores))


def evaluate_subset(
    subset: np.ndarray,
    labels: np.ndarray,
    final_scores: np.ndarray,
    alerted: np.ndarray,
    first_flow_index: np.ndarray,
    first_seconds: np.ndarray,
    budget: float,
) -> dict[str, Any]:
    negative = subset & (labels == 0)
    positive = subset & (labels == 1)
    false_positive = int((alerted & negative).sum())
    true_positive = int((alerted & positive).sum())
    negative_count = int(negative.sum())
    positive_count = int(positive.sum())
    fpr = false_positive / negative_count if negative_count else math.nan
    dr = true_positive / positive_count if positive_count else math.nan
    alerted_positive = alerted & positive
    censored = positive & ~alerted
    allowed_fp = int(math.floor(budget * negative_count))
    return {
        "n_entity": int(subset.sum()),
        "n_positive_entity": positive_count,
        "n_negative_entity": negative_count,
        "actual_entity_fpr": fpr,
        "detection_rate": dr,
        "false_positive_count": false_positive,
        "true_positive_count": true_positive,
        "budget": budget,
        "budget_allowed_false_positive_count": allowed_fp,
        "budget_violation_fpr": max(0.0, fpr - budget) if math.isfinite(fpr) else None,
        "budget_violation_count": max(0, false_positive - allowed_fp),
        "entity_ap": average_precision_or_none(labels[subset], final_scores[subset]),
        "first_alert_flow_index_median": percentile_or_none(
            first_flow_index[alerted_positive],
            50,
        ),
        "first_alert_flow_index_p90": percentile_or_none(
            first_flow_index[alerted_positive],
            90,
        ),
        "first_alert_seconds_median": percentile_or_none(
            first_seconds[alerted_positive],
            50,
        ),
        "first_alert_seconds_p90": percentile_or_none(
            first_seconds[alerted_positive],
            90,
        ),
        "unalerted_censor_rate": int(censored.sum()) / positive_count if positive_count else None,
        "latency_distribution_population": "已告警正实体；封印时告警记为流序号0、时间0秒",
    }


def evaluate_threshold(
    threshold: float,
    cutoff: float,
    budget: float,
    pilot_scores: np.ndarray,
    pilot_counts: np.ndarray,
    active: np.ndarray,
    new_entity: np.ndarray,
    entity_labels: np.ndarray,
    final_entity_scores: np.ndarray,
    sorted_entity: np.ndarray,
    sorted_time: np.ndarray,
    cumulative_mean: np.ndarray,
    within_entity_rank: np.ndarray,
    sorted_position: np.ndarray,
    time_unit_per_second: float,
) -> dict[str, Any]:
    n_entity = len(entity_labels)
    first_position = np.full(n_entity, len(sorted_entity), np.int64)
    post = sorted_time > cutoff
    crossing = post & (cumulative_mean >= threshold)
    np.minimum.at(first_position, sorted_entity[crossing], sorted_position[crossing])
    alerted_after = first_position < len(sorted_entity)
    seal_alert = active & (pilot_counts > 0) & (pilot_scores >= threshold)
    alerted = active & (seal_alert | alerted_after)

    first_flow_index = np.full(n_entity, np.nan, np.float64)
    first_seconds = np.full(n_entity, np.nan, np.float64)
    first_flow_index[seal_alert] = 0.0
    first_seconds[seal_alert] = 0.0
    after_only = active & ~seal_alert & alerted_after
    entity_ids = np.flatnonzero(after_only)
    positions = first_position[entity_ids]
    first_flow_index[entity_ids] = (
        within_entity_rank[positions] - pilot_counts[entity_ids]
    ).astype(np.float64)
    first_seconds[entity_ids] = (
        sorted_time[positions].astype(np.float64) - cutoff
    ) / time_unit_per_second

    return {
        "threshold": threshold,
        "main_active_entities": evaluate_subset(
            active,
            entity_labels,
            final_entity_scores,
            alerted,
            first_flow_index,
            first_seconds,
            budget,
        ),
        "new_entities_sensitivity": evaluate_subset(
            new_entity,
            entity_labels,
            final_entity_scores,
            alerted,
            first_flow_index,
            first_seconds,
            budget,
        ),
        "alert_rule": "封印时或后续任一流更新后的累计 p=1 实体均分首次达到阈值即锁存告警",
    }


def prepare_sorted_online_state(
    flow_scores: np.ndarray,
    entity: np.ndarray,
    time_values: np.ndarray,
) -> dict[str, np.ndarray]:
    log("构造后段顺序回放索引：按实体、时间、原始行号稳定排序")
    row = np.arange(len(flow_scores), dtype=np.int64)
    order = np.lexsort((row, time_values, entity))
    del row
    sorted_entity = entity[order]
    sorted_time = time_values[order]
    sorted_scores = flow_scores[order].astype(np.float64, copy=False)
    position = np.arange(len(order), dtype=np.int64)
    group_start = np.empty(len(order), bool)
    group_start[0] = True
    group_start[1:] = sorted_entity[1:] != sorted_entity[:-1]
    start_position = np.maximum.accumulate(np.where(group_start, position, 0))
    within_rank = position - start_position + 1
    cumulative = np.cumsum(sorted_scores, dtype=np.float64)
    base_marker = np.zeros(len(order), np.float64)
    starts = np.flatnonzero(group_start)
    if len(starts) > 1:
        base_marker[starts[1:]] = cumulative[starts[1:] - 1]
    base = np.maximum.accumulate(base_marker)
    cumulative_mean = (cumulative - base) / within_rank
    del order, sorted_scores, cumulative, base_marker, base, start_position, group_start, starts
    return {
        "entity": sorted_entity,
        "time": sorted_time,
        "mean": cumulative_mean,
        "rank": within_rank,
        "position": position,
    }


def main() -> None:
    args = parse_args()
    if not args.config.is_file():
        raise SystemExit(f"配置不存在：{args.config}")
    config = load_json(args.config)
    validate_config(config)
    if args.validate_config:
        print("PBC_CONFIG_VALID", flush=True)
        return
    parent = validate_inputs(args, config)
    if args.validate_inputs:
        print("PBC_INPUTS_VALID", flush=True)
        return

    protected = (
        args.out / "selection-seal.json",
        args.out / "pbc-results.json",
        args.out / "manifest.json",
        args.out / "swanlab-receipt.json",
        args.out / "swanlog",
    )
    if any(path.exists() for path in protected):
        raise SystemExit(f"PBC 聚合制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)

    import swanlab
    import torch
    import xgboost as xgb

    build_info = xgb.build_info()
    if xgb.__version__ != "3.2.0" or build_info.get("USE_CUDA") is not True:
        raise SystemExit(
            f"XGBoost 环境不符：version={xgb.__version__} "
            f"USE_CUDA={build_info.get('USE_CUDA')}"
        )
    if not torch.cuda.is_available():
        raise SystemExit("CUDA 不可用，拒绝以 CPU 冒充冻结模型推理")
    free, total = torch.cuda.mem_get_info()
    if free / 2**30 < float(config["gpu_need_gib"]):
        raise SystemExit("可用显存低于 PBC 启动门槛")
    log(f"GPU 总显存 {total / 2**30:.2f} GiB，可用 {free / 2**30:.2f} GiB")

    script_sha = sha256_file(Path(__file__).resolve())
    config_sha = sha256_file(args.config.resolve())
    tracking = config["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=RUN_ID,
        config={
            "seed": 42,
            "screening_only": True,
            "formal": False,
            "parent_run_id": PARENT_RUN_ID,
            "base_view": "semantic168",
            "p": 1.0,
            "pilot_time_fractions": config["pilot_time_fractions"],
            "entity_fpr_budgets": config["entity_fpr_budgets"],
            "source_year_retrained": False,
            "target_score_calls": 1,
            "script_sha256": script_sha,
            "config_sha256": config_sha,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )

    log("阶段一：只读 LSPR23，重建 semantic168 三折折外分数")
    source_labels = np.load(CACHE / "y23.npy")
    source_indices = np.load(CACHE / "I23.npy")
    source_mask = np.load(CACHE / "M23.npy")
    source_entity = np.load(CACHE / "ent23.npy")
    source_time = np.load(CACHE / "t23_flow.npy")
    if len(source_labels) != N_FLOW_23 or len(source_entity) != N_FLOW_23:
        raise SystemExit("LSPR23 流数或实体键长度不符")
    if int(source_entity.max()) + 1 != N_ENTITY_23:
        raise SystemExit("LSPR23 实体数不符")
    assert_sequence_time_monotonic(
        source_time,
        source_indices,
        source_mask,
        N_FLOW_23,
        "LSPR23",
    )
    del source_time
    fold_of_flow, _, source_entity_labels = reconstruct_source_folds(
        source_labels,
        source_entity,
        parent["selection"]["fold_stat"],
        int(config["seed"]),
    )
    source_semantic = build_semantic_matrix(
        CACHE / "X23.npy",
        N_FLOW_23,
        source_indices,
        source_mask,
        int(config["predict_batch"]),
        int(config["sequence_batch"]),
        "LSPR23",
    )
    del source_indices, source_mask
    source_oof = np.full(N_FLOW_23, np.nan, np.float32)
    source_model_receipts: list[dict[str, Any]] = []
    for fold in range(N_FOLD):
        rows = np.flatnonzero(fold_of_flow == fold)
        model_path = args.parent_run_root.resolve() / f"model_oof_semantic168_fold{fold}.json"
        booster, receipt = load_booster(xgb, model_path, f"semantic168/fold{fold}")
        gpu_guard(torch, float(config["gpu_floor_gib"]), f"semantic168/fold{fold}/推理前")
        source_oof[rows] = predict_selected_rows(
            booster,
            source_semantic,
            rows,
            int(config["predict_batch"]),
            f"semantic168/fold{fold}/OOF",
        )
        receipt["holdout_flow_count"] = int(len(rows))
        source_model_receipts.append(receipt)
        del booster, rows
        torch.cuda.empty_cache()
    if not np.isfinite(source_oof).all():
        raise SystemExit("源折外分数存在未覆盖流")
    del source_semantic, fold_of_flow
    source_entity_scores = mean_entity_scores(source_oof, source_entity, N_ENTITY_23)
    del source_oof, source_entity, source_labels
    source_prior = float(source_entity_labels.mean())

    source_operating_points = {
        f"fpr_{fpr:g}": source_operating_point(
            source_entity_scores,
            source_entity_labels,
            float(fpr),
        )
        for fpr in config["bbse_source_fpr_grid"]
    }
    source_budget_thresholds = {
        f"budget_{budget:g}": source_operating_point(
            source_entity_scores,
            source_entity_labels,
            float(budget),
        )
        for budget in config["entity_fpr_budgets"]
    }
    log("源侧收据冻结完成；未训练任何模型，源折外分数仅驻内存")

    log("阶段二：只读无标签目标特征与时间，最终 semantic168 模型只预测一次")
    target_indices = np.load(CACHE / "I24.npy")
    target_mask = np.load(CACHE / "M24.npy")
    source_address = np.load(CACHE / "s24.npy", allow_pickle=True)
    destination_address = np.load(CACHE / "d24.npy", allow_pickle=True)
    target_time = np.load(CACHE / "t24.npy")
    assert_sequence_time_monotonic(
        target_time,
        target_indices,
        target_mask,
        N_FLOW_24,
        "LSPR24",
    )
    entity_key = np.array(
        [
            left + "|" + right if left <= right else right + "|" + left
            for left, right in zip(source_address, destination_address, strict=True)
        ],
        object,
    )
    _, target_entity = np.unique(entity_key, return_inverse=True)
    if int(target_entity.max()) + 1 != N_ENTITY_24:
        raise SystemExit(f"LSPR24 实体数不符：{int(target_entity.max()) + 1:,}")
    del entity_key, source_address, destination_address
    target_semantic = build_semantic_matrix(
        CACHE / "X24.npy",
        N_FLOW_24,
        target_indices,
        target_mask,
        int(config["predict_batch"]),
        int(config["sequence_batch"]),
        "LSPR24",
    )
    del target_indices, target_mask
    final_model_path = args.parent_run_root.resolve() / "model_semantic168.json"
    final_booster, final_model_receipt = load_booster(xgb, final_model_path, "semantic168/final")
    gpu_guard(torch, float(config["gpu_floor_gib"]), "semantic168/final/目标推理前")
    target_flow_scores = predict_rows(
        final_booster,
        target_semantic,
        int(config["predict_batch"]),
        "semantic168/final/LSPR24",
    )
    target_prediction_ledger = [
        {"call": 1, "view": "semantic168", "n_flow": N_FLOW_24, "p": 1.0}
    ]
    del target_semantic, final_booster
    torch.cuda.empty_cache()

    total_sum = np.zeros(N_ENTITY_24, np.float64)
    total_count = np.zeros(N_ENTITY_24, np.int64)
    np.add.at(total_sum, target_entity, target_flow_scores.astype(np.float64, copy=False))
    np.add.at(total_count, target_entity, 1)
    final_entity_scores = (total_sum / total_count).astype(np.float32)
    time_min = float(np.min(target_time))
    time_max = float(np.max(target_time))
    time_span_hours = (
        (time_max - time_min) / float(config["time_unit_per_second"]) / 3600.0
    )
    span_low, span_high = [float(value) for value in config["expected_time_span_hours"]]
    if not span_low <= time_span_hours <= span_high:
        raise SystemExit(f"LSPR24 时间跨度 {time_span_hours:.3f} 小时超出冻结门")

    log("阶段三：只用目标无标签先导段冻结四种方法的数值阈值")
    prefix_receipts: dict[str, Any] = {}
    prefix_state: dict[str, dict[str, np.ndarray | float]] = {}
    for fraction_value in config["pilot_time_fractions"]:
        fraction = float(fraction_value)
        cutoff = time_min + fraction * (time_max - time_min)
        pilot_flow = target_time <= cutoff
        pilot_sum = np.zeros(N_ENTITY_24, np.float64)
        pilot_count = np.zeros(N_ENTITY_24, np.int64)
        np.add.at(
            pilot_sum,
            target_entity[pilot_flow],
            target_flow_scores[pilot_flow].astype(np.float64, copy=False),
        )
        np.add.at(pilot_count, target_entity[pilot_flow], 1)
        pilot_seen = pilot_count > 0
        pilot_scores = np.full(N_ENTITY_24, np.nan, np.float32)
        pilot_scores[pilot_seen] = (pilot_sum[pilot_seen] / pilot_count[pilot_seen]).astype(
            np.float32
        )
        cdfs = cdf_components(
            source_entity_scores,
            source_entity_labels,
            pilot_scores[pilot_seen],
        )
        candidates = [
            bbse_candidate(
                source_operating_points[f"fpr_{float(fpr):g}"],
                pilot_scores[pilot_seen],
                cdfs,
                config,
            )
            for fpr in config["bbse_source_fpr_grid"]
        ]
        budget_methods: dict[str, Any] = {}
        for budget_value in config["entity_fpr_budgets"]:
            budget = float(budget_value)
            budget_methods[f"budget_{budget:g}"] = freeze_methods_for_budget(
                pilot_scores[pilot_seen],
                budget,
                source_budget_thresholds[f"budget_{budget:g}"],
                candidates,
                source_prior,
            )
        prefix_key = f"prefix_{fraction:g}"
        prefix_receipts[prefix_key] = {
            "pilot_time_fraction": fraction,
            "cutoff_time_raw": cutoff,
            "pilot_flow_count": int(pilot_flow.sum()),
            "pilot_entity_count": int(pilot_seen.sum()),
            "bbse_candidates": candidates,
            "budgets": budget_methods,
        }
        prefix_state[prefix_key] = {
            "cutoff": cutoff,
            "pilot_scores": pilot_scores,
            "pilot_counts": pilot_count,
        }
        del pilot_flow, pilot_sum, cdfs

    selection_seal = {
        "schema_version": "ch4-xgb-pbc-selection-seal-v1",
        "run_id": RUN_ID,
        "sealed_before_target_label_load": True,
        "selection_uses_target_labels": False,
        "selection_rule_sha256": canonical_sha256(
            {
                "pilot_time_fractions": config["pilot_time_fractions"],
                "entity_fpr_budgets": config["entity_fpr_budgets"],
                "bbse_source_fpr_grid": config["bbse_source_fpr_grid"],
                "gates": {
                    key: config[key]
                    for key in (
                        "bbse_min_tpr_fpr_separation",
                        "bbse_min_confusion_singular_value",
                        "bbse_prior_margin",
                        "mismatch_dkw_alpha",
                    )
                },
            }
        ),
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "parent": {
            "run_id": PARENT_RUN_ID,
            "eval_run_id": CONTINUATION_RUN_ID,
            "selected_adapter": parent["selected_adapter"],
            "p": parent["p_selection"]["semantic168"],
            "parent_artifact_sha256": parent["artifact_sha256"],
            "parent_eval_sha256": parent["parent_eval_sha256"],
            "parent_recovery_proof_sha256": parent["parent_recovery_proof_sha256"],
            "source_oof_models": source_model_receipts,
            "target_final_model": final_model_receipt,
        },
        "source": {
            "n_flow": N_FLOW_23,
            "n_entity": N_ENTITY_23,
            "n_positive_entity": N_POS_ENTITY_23,
            "entity_positive_prior": source_prior,
            "fold_stat": parent["selection"]["fold_stat"],
            "operating_points": source_operating_points,
            "budget_thresholds": source_budget_thresholds,
            "source_year_retrained": False,
            "oof_scores_persisted": False,
        },
        "target_unlabeled": {
            "n_flow": N_FLOW_24,
            "n_entity": N_ENTITY_24,
            "time_min_raw": time_min,
            "time_max_raw": time_max,
            "time_span_hours": time_span_hours,
            "target_score_calls": 1,
            "prediction_ledger": target_prediction_ledger,
            "target_scores_persisted": False,
        },
        "budget_provenance": config["budget_provenance"],
        "prefixes": prefix_receipts,
        "forbidden_after_seal": [
            "后段重新取分位数",
            "后段全体分数 top-k",
            "用后段标签或指标改阈值",
        ],
    }
    selection_path = args.out / "selection-seal.json"
    atomic_json(selection_path, selection_seal)
    selection_sealed = selection_path.is_file() and sha256_file(selection_path)
    if not selection_sealed:
        raise SystemExit("选择封印未成功落盘")
    log(f"选择封印已原子落盘：{selection_path}")

    log("阶段四：选择封印之后首次加载目标标签，只作冻结评价")
    if not selection_sealed:
        raise AssertionError("目标标签加载前选择封印断言失败")
    target_labels = np.load(CACHE / "y24.npy")
    if len(target_labels) != N_FLOW_24:
        raise SystemExit("LSPR24 标签长度不符")
    target_entity_labels = np.zeros(N_ENTITY_24, np.float32)
    np.maximum.at(target_entity_labels, target_entity, target_labels)
    if int(target_entity_labels.sum()) != N_POS_ENTITY_24:
        raise SystemExit(f"LSPR24 正实体数不符：{int(target_entity_labels.sum())}")
    del target_labels

    online = prepare_sorted_online_state(target_flow_scores, target_entity, target_time)
    evaluation: dict[str, Any] = {}
    metric_payload: dict[str, int | float] = {}
    for prefix_key, receipt in prefix_receipts.items():
        state = prefix_state[prefix_key]
        cutoff = float(state["cutoff"])
        pilot_counts = np.asarray(state["pilot_counts"])
        pilot_scores = np.asarray(state["pilot_scores"])
        active = total_count - pilot_counts > 0
        new_entity = active & (pilot_counts == 0)
        prefix_result: dict[str, Any] = {
            "pilot_time_fraction": receipt["pilot_time_fraction"],
            "cutoff_time_raw": cutoff,
            "main_evaluation_unit": "截止后仍有流的无向2-IP实体；前段见过者继续保留",
            "entity_label_scope": "实体在目标全年任一流为正则实体为正",
            "new_entity_definition": "前段零流且截止后至少一条流",
            "budgets": {},
        }
        for budget_value in config["entity_fpr_budgets"]:
            budget = float(budget_value)
            budget_key = f"budget_{budget:g}"
            method_receipts = receipt["budgets"][budget_key]
            method_results: dict[str, Any] = {}
            for method in METHODS:
                threshold = float(method_receipts[method]["threshold"])
                metrics = evaluate_threshold(
                    threshold,
                    cutoff,
                    budget,
                    pilot_scores,
                    pilot_counts,
                    active,
                    new_entity,
                    target_entity_labels,
                    final_entity_scores,
                    online["entity"],
                    online["time"],
                    online["mean"],
                    online["rank"],
                    online["position"],
                    float(config["time_unit_per_second"]),
                )
                method_results[method] = {
                    "display_name": METHOD_DISPLAY_NAMES[method],
                    "selection_receipt": method_receipts[method],
                    **metrics,
                }
                main_metrics = metrics["main_active_entities"]
                metric_prefix = f"{prefix_key}/{budget_key}/{method}"
                for metric_name in (
                    "actual_entity_fpr",
                    "detection_rate",
                    "false_positive_count",
                    "budget_violation_fpr",
                    "budget_violation_count",
                    "entity_ap",
                    "unalerted_censor_rate",
                ):
                    value = main_metrics[metric_name]
                    if value is not None and math.isfinite(float(value)):
                        metric_payload[f"{metric_prefix}/{metric_name}"] = value
            ap_values = {
                method_results[method]["main_active_entities"]["entity_ap"]
                for method in METHODS
            }
            if len(ap_values) != 1:
                raise SystemExit(f"{prefix_key}/{budget_key} 的单调阈值层意外改变实体 AP")
            prefix_result["budgets"][budget_key] = {
                "budget": budget,
                "provenance": config["budget_provenance"][f"{budget:g}"],
                "methods": method_results,
                "entity_ap_invariance": {
                    "passed": True,
                    "reason": "四种方法只冻结数值阈值，不改变同一冻结实体分数排序",
                    "value": next(iter(ap_values)),
                },
            }
        evaluation[prefix_key] = prefix_result

    result = {
        "schema_version": "ch4-xgb-pbc-q0-results-v1",
        "run_id": RUN_ID,
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "selection_seal_sha256": selection_sealed,
        "selection_sealed_before_target_label_load": True,
        "target_labels_loaded_after_selection_seal": True,
        "source_year_retrained": False,
        "base": {
            "parent_run_id": PARENT_RUN_ID,
            "parent_eval_run_id": CONTINUATION_RUN_ID,
            "view": "semantic168",
            "p": 1.0,
            "num_boost_round": N_TREE,
            "xgboost_version": xgb.__version__,
            "xgboost_params": EXPECTED_XGB_PARAMS,
        },
        "budget_provenance": config["budget_provenance"],
        "evaluation": evaluation,
        "isolation": {
            "target_score_calls": 1,
            "prediction_ledger": target_prediction_ledger,
            "thresholds_frozen_before_target_labels": True,
            "post_seal_top_k": False,
            "post_seal_threshold_reselection": False,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "derived_matrices_persisted": False,
            "label_details_persisted": False,
            "new_models_persisted": False,
        },
        "metric_definitions": {
            "entity_ap": "冻结最终实体分数的平均精确率；单调阈值决策层不改变排序",
            "first_alert": "已告警正实体中，封印时告警记0，否则报封印后实体流序号与秒数",
            "censor_rate": "正实体中截至目标结束仍未告警的比例",
        },
        "timing": {"total_seconds": time.time() - T0},
    }
    result_path = args.out / "pbc-results.json"
    atomic_json(result_path, result)

    metric_payload["runtime/total_seconds"] = result["timing"]["total_seconds"]
    swanlab.log(metric_payload, step=0)
    swanlab.finish()
    swanlab_receipt = {
        "schema_version": "ch4-xgb-pbc-aggregate-swanlab-receipt-v1",
        "completed": True,
        "workspace": tracking["workspace"],
        "project": tracking["project"],
        "mode": tracking["mode"],
        "aggregate_only": True,
        "metric_keys": sorted(metric_payload),
    }
    atomic_json(args.out / "swanlab-receipt.json", swanlab_receipt)

    manifest_names = (
        "resource-receipt.json",
        "selection-seal.json",
        "pbc-results.json",
        "swanlab-receipt.json",
    )
    manifest = {
        "schema_version": "ch4-xgb-pbc-q0-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "screening_only": True,
        "formal": False,
        "per_sample_artifacts_persisted": False,
        "files": {},
    }
    for name in manifest_names:
        path = args.out / name
        if not path.is_file():
            raise SystemExit(f"必需聚合制品缺失：{path}")
        manifest["files"][name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    atomic_json(args.out / "manifest.json", manifest)
    log(f"PBC 聚合结果已保存：{result_path}")


if __name__ == "__main__":
    main()
