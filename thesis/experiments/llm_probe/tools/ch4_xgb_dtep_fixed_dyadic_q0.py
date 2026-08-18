#!/usr/bin/env python3
"""第四章 DTEP 固定二进多尺度 XGBoost 快速筛选。"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import resource
import subprocess
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
    DIJK_FEATURES,
    EXPECTED_XGB_PARAMS,
    N_FLOW_24,
    NUMERIC_IDX,
    PARENT_RUN_ID,
    atomic_json,
    configure_prediction_device,
    predict_rows,
    sha256_file,
    validate_parent_inputs,
)

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-dtep-fixed-dyadic-q0-seed42-v1"
PARENT_BUCKET_RUN_ID = "ch4-xgb-long-entity-bucket-diagnostic-seed42-v1"
N_FLOW_23 = 16_353_511
N_ENTITY_23 = 150_680
N_POS_ENTITY_23 = 239
N_ENTITY_24 = 47_115
N_POS_ENTITY_24 = 752
N_FOLD = 3
N_TREE = 800
SEQUENCE_LENGTH = 128
SEMANTIC_DIM = 168
RECENT_DIM = 83
FIXED_DYADIC_DIM = 251
COMPLETE_SCALES = (1, 2, 4, 8, 16, 32, 64, 128)
RECENT_SCALES = (2, 4, 8, 16, 32, 64)
RECENT_WEIGHT = 1.0 / len(RECENT_SCALES)
EXPECTED_PARENT_RESULT_SHA256 = (
    "128b1225c96bb07c5b808dc2e0092223d1acb4c039b487a7007551a4f6b5135f"
)
EXPECTED_PARENT_EVAL_MANIFEST_SHA256 = (
    "f6b66cc94ef09b169ff29ce317464109bc701fa109875f6e9b7d09c889516115"
)
Q00_FOLD_AP = (
    0.9050526558099626,
    0.9406196353987395,
    0.918485495392647,
)
Q00_POOLED_AP = 0.9222351129941275
Q00_TARGET_AP = 0.5650784187138617
Q00_TARGET_DR = {
    "0.01": 0.5319148936170213,
    "0.02": 0.75,
    "0.04": 0.8896276595744681,
}
Q00_BUCKET_ROUNDED = {
    "1-2": 0.671626,
    "3-10": 0.598131,
    "11-100": 0.664015,
    "101-1000": 0.464749,
    "1001+": 0.451578,
}
T0 = time.time()
LAST_BEAT = [T0]
RESOURCE_SAMPLES: list[dict[str, Any]] = []


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
    parser = argparse.ArgumentParser(description="XGBoost DTEP 固定二进多尺度 Q0")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/ch4-xgb-dtep-fixed-dyadic-q0-seed42-v1.json",
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
        "--parent-bucket-root",
        type=Path,
        default=ROOT / "runs/diagnostics" / PARENT_BUCKET_RUN_ID,
    )
    parser.add_argument(
        "--parent-config",
        type=Path,
        default=ROOT / "configs/ch3-xgb-cpa-elp-gpu-oof-seed42-v1.json",
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
    expected = {
        "schema_version": "ch4-xgb-dtep-fixed-dyadic-q0-v1",
        "run_id": RUN_ID,
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "parent_run_id": PARENT_RUN_ID,
        "parent_eval_run_id": CONTINUATION_RUN_ID,
        "parent_bucket_run_id": PARENT_BUCKET_RUN_ID,
        "sequence_length": SEQUENCE_LENGTH,
        "complete_dyadic_scales": list(COMPLETE_SCALES),
        "recent_scales": list(RECENT_SCALES),
        "recent_channel_dim": RECENT_DIM,
        "n_fold": N_FOLD,
        "num_boost_round": N_TREE,
        "xgb_params": EXPECTED_XGB_PARAMS,
        "effective_config_float_compare": {"rel_tol": 1e-7, "abs_tol": 1e-12},
        "target_fpr_grid": [0.01, 0.02, 0.04],
    }
    for key, wanted in expected.items():
        if config.get(key) != wanted:
            raise SystemExit(f"DTEP 配置字段不符：{key}")
    expected_cells = {
        "Q00": {
            "display_name": "XGBoost 块内长证据对照",
            "view": "semantic168",
            "input_dim": SEMANTIC_DIM,
            "power_mean_p": 1.0,
        },
        "Q10": {
            "display_name": "XGBoost 块内长证据＋固定二进近期混合",
            "view": "fixed_dyadic251",
            "input_dim": FIXED_DYADIC_DIM,
            "power_mean_p": 1.0,
        },
    }
    if config.get("cells") != expected_cells:
        raise SystemExit("DTEP 两格定义不符")
    weights = config.get("recent_scale_weights", [])
    if len(weights) != len(RECENT_SCALES) or any(
        not math.isclose(float(value), RECENT_WEIGHT, rel_tol=0.0, abs_tol=1e-15)
        for value in weights
    ):
        raise SystemExit("近期尺度必须固定六档等权")
    source_gate = config.get("source_gate", {})
    if source_gate != {
        "fold_delta_operator": ">",
        "fold_delta_threshold": 0.0,
        "pooled_delta_operator": ">",
        "pooled_delta_threshold": 0.0,
        "reuse_parent_q00_metrics": False,
        "q00_metric_source": "same_run_retrain_due_parent_data_hash_unavailable",
        "train_same_run_q00_efficiency_reference": True,
    }:
        raise SystemExit("源方向门配置不符")
    buckets = config.get("entity_flow_count_buckets")
    if buckets != [
        {"name": "1-2", "lower": 1, "upper": 2},
        {"name": "3-10", "lower": 3, "upper": 10},
        {"name": "11-100", "lower": 11, "upper": 100},
        {"name": "101-1000", "lower": 101, "upper": 1000},
        {"name": "1001+", "lower": 1001, "upper": None},
    ]:
        raise SystemExit("实体流数桶边界不符")
    if config.get("target_gate") != {
        "overall_ap_min_delta": 0.0,
        "long_bucket_strict_min_delta": 0.0,
        "short_bucket_min_delta": -0.01,
        "combined_short_min_delta": 0.0,
        "dr_0.01_min_delta": -0.01,
        "dr_0.02_min_delta": -0.01,
        "dr_0.04_min_delta": 0.0,
        "minimum_nonnegative_dr_points": 2,
    }:
        raise SystemExit("目标性能门配置不符")
    efficiency = config.get("efficiency_gate", {})
    if efficiency != {
        "max_q10_to_q00_ratio": 2.0,
        "max_host_peak_gib": 65.0,
        "max_gpu_peak_gib": 24.0,
        "max_recent_state_flows": 64,
        "require_same_device": True,
        "require_same_batch": True,
        "require_same_prediction_backend": True,
    }:
        raise SystemExit("效率门配置不符")
    artifact_policy = config.get("artifact_policy", {})
    if artifact_policy != {
        "persist_source_q10_models": True,
        "persist_aggregate_json": True,
        "persist_status_log_manifest_resource": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_derived_matrices": False,
        "persist_bucket_membership": False,
        "persist_target_models": False,
    }:
        raise SystemExit("制品策略不符")
    tracking = config.get("tracking", {})
    if tracking != {
        "workspace": "mortiswang",
        "project": "ns3-rwkv-lspr24",
        "mode": "online",
        "aggregate_only": True,
    }:
        raise SystemExit("SwanLab 目的地或聚合模式不符")
    for key in (
        "predict_batch",
        "dmatrix_batch",
        "sequence_batch",
        "gpu_need_gib",
        "gpu_floor_gib",
        "estimated_peak_host_gib",
        "estimated_peak_gpu_gib",
    ):
        if float(config.get(key, 0)) <= 0:
            raise SystemExit(f"配置数值必须为正：{key}")


def validate_parent_evidence(
    args: argparse.Namespace, config: dict[str, Any]
) -> dict[str, Any]:
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
    selection = parent["selection"]
    semantic = selection["p_selection"]["semantic168"]
    if float(semantic["p_selected"]) != 1.0:
        raise SystemExit("父 semantic168 幂指数不是 1.0")
    curve_p1 = next(item for item in semantic["curve"] if float(item["p"]) == 1.0)
    actual_fold_ap = tuple(float(value) for value in curve_p1["fold_ent_ap"])
    if actual_fold_ap != Q00_FOLD_AP or float(curve_p1["oof_ent_ap"]) != Q00_POOLED_AP:
        raise SystemExit("父 Q00 源折 AP 或 pooled AP 与冻结锚点不符")
    fold_stat = selection.get("fold_stat", [])
    if [item.get("n_pos_entity") for item in fold_stat] != [80, 80, 79]:
        raise SystemExit("父实体三折正例数不是 80/80/79")

    eval_root = args.parent_eval_root.resolve()
    if eval_root.name != CONTINUATION_RUN_ID:
        raise SystemExit("父评价运行身份不符")
    expected_eval = {
        "xgb_cpa_elp_results.json": EXPECTED_PARENT_RESULT_SHA256,
        "manifest.json": EXPECTED_PARENT_EVAL_MANIFEST_SHA256,
    }
    eval_hashes: dict[str, str] = {}
    for name, wanted in expected_eval.items():
        path = eval_root / name
        if not path.is_file() or sha256_file(path) != wanted:
            raise SystemExit(f"父评价制品缺失或摘要不符：{name}")
        eval_hashes[name] = wanted
    eval_status = load_json(eval_root / "status.json")
    if (
        eval_status.get("state") != "finished"
        or eval_status.get("stage") != "complete"
        or eval_status.get("exit_code") != 0
    ):
        raise SystemExit("父评价状态不是 finished/complete/exit=0")
    eval_result = load_json(eval_root / "xgb_cpa_elp_results.json")
    parent_q00 = eval_result.get("cells", {}).get("C11", {})
    if float(parent_q00.get("ent_ap", math.nan)) != Q00_TARGET_AP:
        raise SystemExit("父 Q00 目标总体 AP 与冻结锚点不符")
    for rate, wanted in Q00_TARGET_DR.items():
        actual = float(parent_q00.get("dr_curve", {}).get(f"fpr_{rate}", math.nan))
        if actual != wanted:
            raise SystemExit(f"父 Q00 DR@{rate}FPR 与冻结锚点不符")

    bucket_root = args.parent_bucket_root.resolve()
    if bucket_root.name != PARENT_BUCKET_RUN_ID:
        raise SystemExit("父分桶诊断运行身份不符")
    bucket_result_path = bucket_root / "xgb_long_entity_bucket_results.json"
    bucket_manifest_path = bucket_root / "manifest.json"
    if not bucket_result_path.is_file() or not bucket_manifest_path.is_file():
        raise SystemExit("父分桶诊断结果或清单缺失")
    bucket_manifest = load_json(bucket_manifest_path)
    manifest_item = bucket_manifest.get("files", {}).get(bucket_result_path.name, {})
    actual_bucket_sha = sha256_file(bucket_result_path)
    if (
        bucket_manifest.get("run_id") != PARENT_BUCKET_RUN_ID
        or manifest_item.get("sha256") != actual_bucket_sha
        or manifest_item.get("bytes") != bucket_result_path.stat().st_size
    ):
        raise SystemExit("父分桶诊断清单不能证明结果身份")
    bucket_result = load_json(bucket_result_path)
    if (
        bucket_result.get("schema_version")
        != "ch4-xgb-long-entity-bucket-diagnostic-v1"
        or bucket_result.get("run_id") != PARENT_BUCKET_RUN_ID
        or bucket_result.get("parent", {}).get("eval_run_id") != CONTINUATION_RUN_ID
        or bucket_result.get("protocol", {}).get("target_labels_used_for_parameter_selection")
        is not False
    ):
        raise SystemExit("父分桶诊断合同不符")
    full_precision_bucket_ap: dict[str, float] = {}
    for name, rounded in Q00_BUCKET_ROUNDED.items():
        value = float(bucket_result["buckets"][name]["cells"]["semantic_elp"]["entity_ap"])
        if round(value, 6) != rounded:
            raise SystemExit(f"父 Q00 分桶 AP 人工锚点不符：{name}")
        full_precision_bucket_ap[name] = value

    for cache_name in ("X23", "y23", "I23", "M23", "E23", "ent23", "t23_flow"):
        path = CACHE / f"{cache_name}.npy"
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"源共同缓存缺失或为空：{path}")
    parent["parent_eval_sha256"] = eval_hashes
    parent["parent_bucket_sha256"] = actual_bucket_sha
    parent["q00_target_bucket_ap"] = full_precision_bucket_ap
    return parent


def assert_sequence_contract(
    timestamps: np.ndarray,
    indices: np.ndarray,
    mask: np.ndarray,
    expected_flow_count: int,
    tag: str,
) -> None:
    if indices.shape[1] != SEQUENCE_LENGTH or mask.shape != indices.shape:
        raise SystemExit(f"{tag} 序列形状不符")
    valid = mask > 0
    if int(valid.sum()) != expected_flow_count:
        raise SystemExit(f"{tag} 有效位不能恰好覆盖全部流")
    if np.any(valid[:, 1:] & ~valid[:, :-1]):
        raise SystemExit(f"{tag} 掩码不是连续有效前缀")
    if len(timestamps) != expected_flow_count or not np.isfinite(timestamps).all():
        raise SystemExit(f"{tag} 时间戳数量异常或含非有限值")
    reversed_pairs = 0
    started = time.time()
    for start in range(0, len(indices), 20_000):
        batch_indices = indices[start : start + 20_000]
        batch_valid = valid[start : start + 20_000]
        values = timestamps[batch_indices]
        adjacent = batch_valid[:, 1:] & batch_valid[:, :-1]
        reversed_pairs += int(((values[:, 1:] < values[:, :-1]) & adjacent).sum())
        beat(f"{tag}/时间核验", min(start + 20_000, len(indices)), len(indices), started)
    if reversed_pairs:
        raise SystemExit(f"{tag} 序列存在 {reversed_pairs} 个时间逆序相邻对")


def build_fixed_dyadic_matrix(
    x_path: Path,
    n_flow: int,
    indices: np.ndarray,
    mask: np.ndarray,
    sequence_batch: int,
    copy_batch: int,
    tag: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    """构造 semantic168 加 83 维固定近期混合，不展开六个尺度。"""
    valid = mask > 0
    if indices.shape[1] != SEQUENCE_LENGTH or mask.shape != indices.shape:
        raise SystemExit(f"{tag} 序列形状异常")
    if int(valid.sum()) != n_flow or np.any(valid[:, 1:] & ~valid[:, :-1]):
        raise SystemExit(f"{tag} 掩码覆盖或连续性异常")
    matrix = np.empty((n_flow, FIXED_DYADIC_DIM), np.float32)
    source = np.load(x_path, mmap_mode="r")
    if source.shape != (n_flow, D_RAW):
        raise SystemExit(f"{tag} 原始矩阵形状不符：{source.shape}")
    copy_started = time.time()
    for start in range(0, n_flow, copy_batch):
        stop = min(start + copy_batch, n_flow)
        matrix[start:stop, :D_RAW] = source[start:stop]
        beat(f"{tag}/raw83", stop, n_flow, copy_started)
    raw_seconds = time.time() - copy_started
    del source

    positions = np.arange(SEQUENCE_LENGTH)
    lower = positions[None, :] <= positions[:, None]
    window_masks = {
        scale: lower & (positions[None, :] >= positions[:, None] - scale + 1)
        for scale in RECENT_SCALES
    }
    cover = np.zeros(n_flow, bool)
    semantic_seconds = 0.0
    recent_seconds = 0.0
    started = time.time()
    for start in range(0, len(indices), sequence_batch):
        batch_indices = indices[start : start + sequence_batch]
        batch_valid = valid[start : start + sequence_batch]
        batch, width = batch_indices.shape
        flat = batch_indices.reshape(-1)
        flat_valid = batch_valid.reshape(-1)
        target = flat[flat_valid]
        current = matrix[flat, :D_RAW].reshape(batch, width, D_RAW)
        count = np.cumsum(batch_valid, axis=1, dtype=np.int32)
        prefix_denom = np.maximum(count, 1).astype(np.float64)

        semantic_started = time.time()
        numeric = current[:, :, NUMERIC_IDX]
        numeric_cumulative = np.cumsum(
            numeric * batch_valid[:, :, None], axis=1, dtype=np.float64
        )
        long_residual = numeric - numeric_cumulative / prefix_denom[:, :, None]
        cursor = D_RAW
        matrix[target, cursor : cursor + len(NUMERIC_IDX)] = long_residual.reshape(
            -1, len(NUMERIC_IDX)
        )[flat_valid]
        cursor += len(NUMERIC_IDX)
        prefix_mask = lower[None, :, :] & batch_valid[:, None, :]
        for feature_idx in CATEGORICAL_IDX:
            values = current[:, :, feature_idx]
            equal = values[:, :, None] == values[:, None, :]
            frequency = (equal & prefix_mask).sum(axis=2) / prefix_denom
            matrix[target, cursor] = frequency.reshape(-1)[flat_valid]
            cursor += 1
        truth_cumulative: dict[int, np.ndarray] = {}
        for feature_idx in BOOLEAN_IDX:
            truth = (current[:, :, feature_idx] > 0) & batch_valid
            cumulative = np.cumsum(truth, axis=1, dtype=np.int32)
            truth_cumulative[feature_idx] = cumulative
            truth_rate = cumulative / prefix_denom
            matrix[target, cursor] = truth_rate.reshape(-1)[flat_valid]
            cursor += 1
        matrix[target, cursor] = np.log1p(count).reshape(-1)[flat_valid]
        cursor += 1
        matrix[target, cursor] = (count == 1).reshape(-1)[flat_valid]
        cursor += 1
        if cursor != SEMANTIC_DIM:
            raise AssertionError(f"{tag} semantic168 游标异常：{cursor}")
        semantic_seconds += time.time() - semantic_started

        recent_started = time.time()
        recent_numeric = np.zeros_like(numeric, dtype=np.float64)
        for scale in RECENT_SCALES:
            window_sum = numeric_cumulative.copy()
            window_sum[:, scale:] -= numeric_cumulative[:, :-scale]
            denom = np.minimum(count, scale).astype(np.float64)
            recent_numeric += (numeric - window_sum / denom[:, :, None]) * RECENT_WEIGHT
        matrix[target, cursor : cursor + len(NUMERIC_IDX)] = recent_numeric.reshape(
            -1, len(NUMERIC_IDX)
        )[flat_valid]
        cursor += len(NUMERIC_IDX)
        for feature_idx in CATEGORICAL_IDX:
            values = current[:, :, feature_idx]
            equal = values[:, :, None] == values[:, None, :]
            mixed = np.zeros((batch, width), np.float64)
            for scale in RECENT_SCALES:
                denom = np.minimum(count, scale)
                active_window = window_masks[scale][None, :, :] & batch_valid[:, None, :]
                mixed += (equal & active_window).sum(axis=2) / denom * RECENT_WEIGHT
            matrix[target, cursor] = mixed.reshape(-1)[flat_valid]
            cursor += 1
        for feature_idx in BOOLEAN_IDX:
            cumulative = truth_cumulative[feature_idx]
            mixed = np.zeros((batch, width), np.float64)
            for scale in RECENT_SCALES:
                window_sum = cumulative.copy()
                window_sum[:, scale:] -= cumulative[:, :-scale]
                mixed += window_sum / np.minimum(count, scale) * RECENT_WEIGHT
            matrix[target, cursor] = mixed.reshape(-1)[flat_valid]
            cursor += 1
        if cursor != FIXED_DYADIC_DIM:
            raise AssertionError(f"{tag} fixed_dyadic251 游标异常：{cursor}")
        recent_seconds += time.time() - recent_started
        cover[target] = True
        beat(
            f"{tag}/fixed_dyadic251",
            min(start + sequence_batch, len(indices)),
            len(indices),
            started,
        )

    if not bool(cover.all()) or not np.isfinite(matrix).all():
        raise SystemExit(f"{tag} 视图覆盖不完整或含非有限值")
    receipt = {
        "view": "fixed_dyadic251",
        "shape": [n_flow, FIXED_DYADIC_DIM],
        "dtype": str(matrix.dtype),
        "semantic_prefix_dim": SEMANTIC_DIM,
        "recent_channel_dim": RECENT_DIM,
        "complete_dyadic_scales": list(COMPLETE_SCALES),
        "recent_scales": list(RECENT_SCALES),
        "recent_scale_weights": [RECENT_WEIGHT] * len(RECENT_SCALES),
        "max_recent_state_flows": max(RECENT_SCALES),
        "per_scale_columns_exposed": False,
        "raw_copy_seconds": raw_seconds,
        "semantic_seconds": semantic_seconds,
        "recent_seconds": recent_seconds,
        "q00_feature_seconds": raw_seconds + semantic_seconds,
        "q10_feature_seconds": raw_seconds + semantic_seconds + recent_seconds,
        "total_seconds": time.time() - copy_started,
        "matrix_gib": matrix.nbytes / 2**30,
    }
    log(
        f"{tag} fixed_dyadic251 完成：{matrix.shape}，{receipt['matrix_gib']:.2f} GiB，"
        f"总耗时 {receipt['total_seconds']:.0f}s"
    )
    return matrix, receipt


def host_peak_gib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 2**30 if sys.platform == "darwin" else peak * 1024 / 2**30


def sample_resources(torch_module: Any, stage: str) -> dict[str, Any]:
    free, total = torch_module.cuda.mem_get_info()
    gpu_used_gib = (total - free) / 2**30
    try:
        probe = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=False,
        )
        nvidia_used_gib = float(probe.stdout.strip().splitlines()[0]) / 1024
    except (OSError, ValueError, IndexError):
        nvidia_used_gib = gpu_used_gib
    receipt = {
        "stage": stage,
        "host_peak_gib": host_peak_gib(),
        "gpu_total_used_gib": max(gpu_used_gib, nvidia_used_gib),
        "gpu_free_gib": free / 2**30,
    }
    RESOURCE_SAMPLES.append(receipt)
    return receipt


def effective_config_receipt(booster: Any, tag: str) -> dict[str, Any]:
    config = json.loads(booster.save_config())
    exact = {
        ("learner", "generic_param", "device"): "cuda:0",
        ("learner", "gradient_booster", "gbtree_train_param", "updater"): "grow_gpu_hist",
        ("learner", "learner_train_param", "objective"): "binary:logistic",
        ("learner", "gradient_booster", "tree_train_param", "max_depth"): "8",
        ("learner", "gradient_booster", "tree_train_param", "max_bin"): "256",
    }
    floating = {
        ("learner", "gradient_booster", "tree_train_param", "eta"): 0.05,
        ("learner", "gradient_booster", "tree_train_param", "subsample"): 0.8,
        ("learner", "gradient_booster", "tree_train_param", "colsample_bytree"): 0.8,
        ("learner", "gradient_booster", "tree_train_param", "lambda"): 1.0,
    }

    def dig(path: tuple[str, ...]) -> Any:
        value: Any = config
        for key in path:
            value = value[key]
        return value

    checks: list[dict[str, Any]] = []
    for path, wanted in exact.items():
        actual = dig(path)
        checks.append({"path": ".".join(path), "actual": actual, "expected": wanted})
        if actual != wanted:
            raise SystemExit(f"{tag} 有效 XGBoost 配置不符：{'.'.join(path)}")
    for path, wanted in floating.items():
        actual = float(dig(path))
        checks.append({"path": ".".join(path), "actual": actual, "expected": wanted})
        if not math.isclose(actual, wanted, rel_tol=1e-7, abs_tol=1e-12):
            raise SystemExit(f"{tag} 有效 XGBoost 浮点配置不符：{'.'.join(path)}")
    return {"tag": tag, "passed": True, "checks": checks}


def train_booster(
    xgb_module: Any,
    torch_module: Any,
    matrix: np.ndarray,
    labels: np.ndarray,
    rows: np.ndarray,
    batch_size: int,
    tag: str,
) -> tuple[Any, dict[str, Any]]:
    class RowBatchIter(xgb_module.DataIter):
        def __init__(self) -> None:
            self.position = 0
            self.started = time.time()
            super().__init__()

        def reset(self) -> None:
            self.position = 0
            self.started = time.time()

        def next(self, input_data: Any) -> bool:
            start = self.position * batch_size
            if start >= len(rows):
                return False
            selected = rows[start : start + batch_size]
            input_data(data=matrix[selected], label=labels[selected])
            self.position += 1
            beat(f"{tag}/量化矩阵", min(start + batch_size, len(rows)), len(rows), self.started)
            return True

    started = time.time()
    dmatrix = xgb_module.QuantileDMatrix(
        RowBatchIter(), max_bin=EXPECTED_XGB_PARAMS["max_bin"]
    )
    dmatrix_seconds = time.time() - started
    if dmatrix.num_row() != len(rows) or dmatrix.num_col() != matrix.shape[1]:
        raise SystemExit(f"{tag} 量化矩阵形状不符")
    dmatrix_resource = sample_resources(torch_module, f"{tag}/量化矩阵后")
    train_started = time.time()
    booster = xgb_module.train(EXPECTED_XGB_PARAMS, dmatrix, num_boost_round=N_TREE)
    train_seconds = time.time() - train_started
    if int(booster.num_boosted_rounds()) != N_TREE:
        raise SystemExit(f"{tag} 树数不是 {N_TREE}")
    effective = effective_config_receipt(booster, tag)
    train_resource = sample_resources(torch_module, f"{tag}/训练后")
    del dmatrix
    return booster, {
        "dmatrix_seconds": dmatrix_seconds,
        "train_seconds": train_seconds,
        "total_seconds": dmatrix_seconds + train_seconds,
        "n_row": int(len(rows)),
        "n_col": int(matrix.shape[1]),
        "num_boost_round": N_TREE,
        "device": "cuda:0",
        "dmatrix_batch": batch_size,
        "effective_config": effective,
        "resource_samples": [dmatrix_resource, train_resource],
        "gpu_peak_observed_gib": max(
            dmatrix_resource["gpu_total_used_gib"], train_resource["gpu_total_used_gib"]
        ),
    }


def save_model_atomic(booster: Any, path: Path) -> dict[str, Any]:
    partial = path.with_name(path.stem + ".partial.json")
    booster.save_model(str(partial))
    partial.replace(path)
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "num_boost_round": int(booster.num_boosted_rounds()),
    }


def mean_entity_scores(
    scores: np.ndarray, entities: np.ndarray, n_entity: int
) -> np.ndarray:
    total = np.zeros(n_entity, np.float64)
    count = np.zeros(n_entity, np.int64)
    np.add.at(total, entities, scores.astype(np.float64, copy=False))
    np.add.at(count, entities, 1)
    return np.where(count > 0, total / np.maximum(count, 1), -np.inf).astype(np.float32)


def entity_ap(labels: np.ndarray, scores: np.ndarray) -> float:
    finite = np.isfinite(scores)
    return float(average_precision_score(labels[finite], scores[finite]))


def dr_at_fpr(labels: np.ndarray, scores: np.ndarray, target: float) -> float:
    finite = np.isfinite(scores)
    values = scores[finite]
    binary = labels[finite]
    negative = np.sort(values[binary == 0])[::-1]
    if len(negative) == 0:
        return float("nan")
    threshold = negative[min(int(len(negative) * target), len(negative) - 1)]
    return float((values[binary == 1] >= threshold).mean())


def build_entity_folds(labels: np.ndarray) -> np.ndarray:
    random_state = np.random.RandomState(42)
    fold = np.empty(len(labels), np.int64)
    for group in (0.0, 1.0):
        entity_ids = np.flatnonzero(labels == group)
        shuffled = entity_ids[random_state.permutation(len(entity_ids))]
        fold[shuffled] = np.arange(len(shuffled)) % N_FOLD
    return fold


def validate_target_cache() -> None:
    for name in ("X24", "y24", "I24", "M24", "s24", "d24", "t24"):
        path = CACHE / f"{name}.npy"
        if not path.is_file() or path.stat().st_size <= 0:
            raise SystemExit(f"目标共同缓存缺失或为空：{path}")


def bucket_mask(flow_counts: np.ndarray, lower: int, upper: int | None) -> np.ndarray:
    result = flow_counts >= lower
    if upper is not None:
        result &= flow_counts <= upper
    return result


def predict_selected_rows(
    booster: Any,
    matrix: np.ndarray,
    rows: np.ndarray,
    batch_size: int,
    tag: str,
) -> np.ndarray:
    """只预测指定行，返回值与 rows 等长且顺序一致。"""
    if rows.ndim != 1 or len(rows) == 0:
        raise AssertionError(f"{tag} 预测行必须是一维非空数组")
    if int(rows.min()) < 0 or int(rows.max()) >= len(matrix):
        raise AssertionError(f"{tag} 预测行超出矩阵范围")
    scores = np.empty(len(rows), np.float32)
    started = time.time()
    for start in range(0, len(rows), batch_size):
        stop = min(start + batch_size, len(rows))
        selected = rows[start:stop]
        scores[start:stop] = np.asarray(
            booster.inplace_predict(matrix[selected]),
            np.float32,
        )
        beat(f"{tag}/选定行推理", stop, len(rows), started)
    if len(scores) != len(rows) or not np.isfinite(scores).all():
        raise AssertionError(f"{tag} 选定行推理覆盖不完整或含非有限值")
    return scores


def write_manifest(out: Path, script_sha: str) -> None:
    names = sorted(
        path.name
        for path in out.iterdir()
        if path.is_file()
        and not path.name.endswith(".partial")
        and path.name not in {"status.json", "run.log", "resource-receipt.json"}
    )
    manifest = {
        "schema_version": "ch4-xgb-dtep-fixed-dyadic-q0-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "per_sample_artifacts_persisted": False,
        "derived_matrices_persisted": False,
        "files": {},
    }
    for name in names:
        path = out / name
        manifest["files"][name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    atomic_json(out / "manifest.json", manifest)


def main() -> None:
    args = parse_args()
    config = load_json(args.config)
    validate_config(config)
    if args.validate_config:
        print("DTEP_FIXED_DYADIC_CONFIG_VALID", flush=True)
        return
    parent = validate_parent_evidence(args, config)
    if args.validate_inputs:
        print("DTEP_FIXED_DYADIC_INPUTS_VALID", flush=True)
        return

    protected = (
        args.out / "source-gate.json",
        args.out / "target-evaluation-seal.json",
        args.out / "dtep-fixed-dyadic-q0-results.json",
        args.out / "manifest.json",
        args.out / "swanlog",
    )
    if any(path.exists() for path in protected):
        raise SystemExit(f"DTEP 科学制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    script_sha = sha256_file(Path(__file__).resolve())
    config_sha = sha256_file(args.config)
    feature_schema = {
        "semantic168": (
            list(DIJK_FEATURES)
            + [f"numeric_residual::{DIJK_FEATURES[index]}" for index in NUMERIC_IDX]
            + [
                f"prefix_same_value_frequency::{DIJK_FEATURES[index]}"
                for index in CATEGORICAL_IDX
            ]
            + [f"prefix_truth_rate::{DIJK_FEATURES[index]}" for index in BOOLEAN_IDX]
            + ["log1p_prefix_count", "is_segment_start"]
        ),
        "fixed_dyadic_recent83": (
            [
                f"fixed_dyadic_recent_numeric_residual::{DIJK_FEATURES[index]}"
                for index in NUMERIC_IDX
            ]
            + [
                f"fixed_dyadic_recent_same_value_frequency::{DIJK_FEATURES[index]}"
                for index in CATEGORICAL_IDX
            ]
            + [
                f"fixed_dyadic_recent_truth_rate::{DIJK_FEATURES[index]}"
                for index in BOOLEAN_IDX
            ]
        ),
    }
    if len(feature_schema["semantic168"]) != SEMANTIC_DIM:
        raise AssertionError("semantic168 模式维度异常")
    if len(feature_schema["fixed_dyadic_recent83"]) != RECENT_DIM:
        raise AssertionError("近期混合模式维度异常")
    feature_receipt = {
        "schema": feature_schema,
        "fixed_dyadic251": feature_schema["semantic168"]
        + feature_schema["fixed_dyadic_recent83"],
        "sha256": canonical_sha256(feature_schema),
        "per_scale_columns_exposed": False,
    }
    atomic_json(args.out / "feature-schema.json", feature_receipt)

    import swanlab
    import torch
    import xgboost as xgb

    if xgb.__version__ != "3.2.0" or xgb.build_info().get("USE_CUDA") is not True:
        raise SystemExit("要求 XGBoost 3.2.0 CUDA 构建")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA 不可用，拒绝 CPU 回退")
    free, total = torch.cuda.mem_get_info()
    if free / 2**30 < float(config["gpu_need_gib"]):
        raise SystemExit("可用 GPU 显存低于 20 GiB 启动门")
    tracking = config["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=RUN_ID,
        config={
            "seed": 42,
            "cells": config["cells"],
            "complete_dyadic_scales": list(COMPLETE_SCALES),
            "recent_scales": list(RECENT_SCALES),
            "recent_scale_weights": [RECENT_WEIGHT] * len(RECENT_SCALES),
            "script_sha256": script_sha,
            "config_sha256": config_sha,
            "xgboost_version": xgb.__version__,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )
    sample_resources(torch, "启动后")
    log("阶段一：只读 LSPR23，构造固定 251 维视图并执行三折源方向门")
    y23 = np.load(CACHE / "y23.npy")
    indices23 = np.load(CACHE / "I23.npy")
    mask23 = np.load(CACHE / "M23.npy")
    sequence_entity23 = np.load(CACHE / "E23.npy")
    entity23 = np.load(CACHE / "ent23.npy")
    time23 = np.load(CACHE / "t23_flow.npy")
    if len(y23) != N_FLOW_23 or len(entity23) != N_FLOW_23:
        raise SystemExit("LSPR23 流数不符")
    entity_labels23 = np.zeros(N_ENTITY_23, np.float32)
    np.maximum.at(entity_labels23, entity23, y23)
    if int(entity_labels23.sum()) != N_POS_ENTITY_23:
        raise SystemExit("LSPR23 正实体数不符")
    for start in range(0, len(indices23), 20_000):
        batch_indices = indices23[start : start + 20_000]
        batch_valid = mask23[start : start + 20_000] > 0
        actual = np.where(
            batch_valid,
            entity23[batch_indices],
            sequence_entity23[start : start + 20_000, None],
        )
        if not np.all(actual == sequence_entity23[start : start + 20_000, None]):
            raise SystemExit("LSPR23 序列跨实体")
    assert_sequence_contract(time23, indices23, mask23, N_FLOW_23, "LSPR23")
    del time23, sequence_entity23
    source_matrix, source_feature_timing = build_fixed_dyadic_matrix(
        CACHE / "X23.npy",
        N_FLOW_23,
        indices23,
        mask23,
        int(config["sequence_batch"]),
        int(config["predict_batch"]),
        "LSPR23",
    )
    del indices23, mask23
    fold_of_entity = build_entity_folds(entity_labels23)
    fold_of_flow = fold_of_entity[entity23]
    fold_stat = []
    for fold in range(N_FOLD):
        fold_stat.append(
            {
                "fold": fold,
                "n_entity": int((fold_of_entity == fold).sum()),
                "n_positive_entity": int(entity_labels23[fold_of_entity == fold].sum()),
                "n_flow": int((fold_of_flow == fold).sum()),
            }
        )
    if [item["n_positive_entity"] for item in fold_stat] != [80, 80, 79]:
        raise SystemExit("重建实体三折正例数不是 80/80/79")
    source_oof_q00 = np.full(N_FLOW_23, np.nan, np.float32)
    source_oof_q10 = np.full(N_FLOW_23, np.nan, np.float32)
    fold_q00_ap: list[float] = []
    fold_q10_ap: list[float] = []
    fold_timing: list[dict[str, Any]] = []
    model_receipts: list[dict[str, Any]] = []
    all_rows = np.arange(N_FLOW_23, dtype=np.int64)
    for fold in range(N_FOLD):
        train_rows = all_rows[fold_of_flow != fold]
        holdout_rows = all_rows[fold_of_flow == fold]
        q00_model, q00_timing = train_booster(
            xgb,
            torch,
            source_matrix[:, :SEMANTIC_DIM],
            y23,
            train_rows,
            int(config["dmatrix_batch"]),
            f"Q00/fold{fold}/同机效率参照",
        )
        q00_score_started = time.time()
        source_oof_q00[holdout_rows] = predict_selected_rows(
            q00_model,
            source_matrix[:, :SEMANTIC_DIM],
            holdout_rows,
            int(config["predict_batch"]),
            f"Q00/fold{fold}/OOF",
        )
        q00_timing["predict_seconds"] = time.time() - q00_score_started
        del q00_model
        torch.cuda.empty_cache()
        q10_model, q10_timing = train_booster(
            xgb,
            torch,
            source_matrix,
            y23,
            train_rows,
            int(config["dmatrix_batch"]),
            f"Q10/fold{fold}",
        )
        score_started = time.time()
        source_oof_q10[holdout_rows] = predict_selected_rows(
            q10_model,
            source_matrix,
            holdout_rows,
            int(config["predict_batch"]),
            f"Q10/fold{fold}/OOF",
        )
        q10_timing["predict_seconds"] = time.time() - score_started
        model_path = args.out / f"model_q10_fixed_dyadic251_fold{fold}.json"
        model_receipt = save_model_atomic(q10_model, model_path)
        model_receipt["fold"] = fold
        model_receipts.append(model_receipt)
        del q10_model, train_rows, holdout_rows
        torch.cuda.empty_cache()
        q00_entity_scores = mean_entity_scores(
            source_oof_q00[fold_of_flow == fold],
            entity23[fold_of_flow == fold],
            N_ENTITY_23,
        )
        q10_entity_scores = mean_entity_scores(
            source_oof_q10[fold_of_flow == fold],
            entity23[fold_of_flow == fold],
            N_ENTITY_23,
        )
        fold_q00_ap.append(entity_ap(entity_labels23, q00_entity_scores))
        fold_q10_ap.append(entity_ap(entity_labels23, q10_entity_scores))
        del q00_entity_scores, q10_entity_scores
        fold_timing.append(
            {
                "fold": fold,
                "q00": q00_timing,
                "q10": q10_timing,
                "q10_to_q00_train_ratio": q10_timing["total_seconds"]
                / max(q00_timing["total_seconds"], 1e-9),
                "same_device": True,
                "same_dmatrix_batch": True,
            }
        )
    if not np.isfinite(source_oof_q00).all() or not np.isfinite(source_oof_q10).all():
        raise SystemExit("Q00 或 Q10 源折外分数覆盖不完整")
    pooled_q00_scores = mean_entity_scores(source_oof_q00, entity23, N_ENTITY_23)
    pooled_q10_scores = mean_entity_scores(source_oof_q10, entity23, N_ENTITY_23)
    pooled_q00_ap = entity_ap(entity_labels23, pooled_q00_scores)
    pooled_q10_ap = entity_ap(entity_labels23, pooled_q10_scores)
    fold_delta = [
        candidate - baseline
        for candidate, baseline in zip(fold_q10_ap, fold_q00_ap, strict=True)
    ]
    pooled_delta = pooled_q10_ap - pooled_q00_ap
    source_passed = all(delta > 0.0 for delta in fold_delta) and pooled_delta > 0.0
    source_gate = {
        "schema_version": "ch4-xgb-dtep-fixed-dyadic-source-gate-v1",
        "run_id": RUN_ID,
        "seed": 42,
        "uses_lspr23_only": True,
        "target_cache_loads": 0,
        "selection_role": "完整候选方向粗淘汰，不选择尺度、权重、p 或轮数",
        "q00_parent_receipt": {
            "fold_entity_ap": list(Q00_FOLD_AP),
            "pooled_entity_ap": Q00_POOLED_AP,
            "parent_artifact_sha256": parent["artifact_sha256"],
            "fold_stat": parent["selection"]["fold_stat"],
            "role": "历史核验锚点；缺少可逐项比对的父数据哈希，未作本次方向门比较值",
        },
        "q00_same_run_retrain": {
            "reason": "父收据不能逐项证明当前共享缓存的数据哈希，按冻结回退条款同合同重训",
            "fold_entity_ap": fold_q00_ap,
            "pooled_entity_ap": pooled_q00_ap,
            "models_persisted": False,
        },
        "q10": {
            "fold_entity_ap": fold_q10_ap,
            "pooled_entity_ap": pooled_q10_ap,
        },
        "delta": {"fold": fold_delta, "pooled": pooled_delta},
        "rule": "三个折差值与 pooled 差值全部严格大于 0",
        "passed": source_passed,
        "decision": "SOURCE_DIRECTION_PASSED" if source_passed else "Q0_REJECTED_SOURCE_DIRECTION",
        "fold_stat": fold_stat,
        "feature_timing": source_feature_timing,
        "fold_timing": fold_timing,
        "models": model_receipts,
        "oof_scores_persisted": False,
    }
    atomic_json(args.out / "source-gate.json", source_gate)
    del source_oof_q00, source_oof_q10, pooled_q00_scores, pooled_q10_scores
    if not source_passed:
        result = {
            "schema_version": "ch4-xgb-dtep-fixed-dyadic-q0-results-v1",
            "run_id": RUN_ID,
            "seed": 42,
            "screening_only": True,
            "formal_paper_evidence": False,
            "independent_test": False,
            "decision": "Q0_REJECTED_SOURCE_DIRECTION",
            "source_gate": source_gate,
            "isolation": {
                "target_cache_loads": 0,
                "target_label_loads": 0,
                "target_score_calls": 0,
                "per_flow_scores_persisted": False,
                "per_entity_scores_persisted": False,
                "derived_matrices_persisted": False,
            },
        }
        atomic_json(args.out / "dtep-fixed-dyadic-q0-results.json", result)
        swanlab.log(
            {
                "source/q10_pooled_entity_ap": pooled_q10_ap,
                "source/q10_minus_q00_pooled": pooled_delta,
                "source/gate_passed": 0,
            },
            step=0,
        )
        swanlab.finish()
        atomic_json(
            args.out / "swanlab-receipt.json",
            {
                "completed": True,
                "aggregate_only": True,
                "workspace": tracking["workspace"],
                "project": tracking["project"],
                "source_rejected_before_target": True,
            },
        )
        write_manifest(args.out, script_sha)
        log("源方向门失败：Q0_REJECTED_SOURCE_DIRECTION；LSPR24 零读取")
        return

    log("源方向门通过：训练一个 Q10 全源模型，之后才允许目标一次评价")
    q10_final, q10_final_timing = train_booster(
        xgb,
        torch,
        source_matrix,
        y23,
        all_rows,
        int(config["dmatrix_batch"]),
        "Q10/final",
    )
    q10_final_receipt = save_model_atomic(
        q10_final, args.out / "model_q10_fixed_dyadic251.json"
    )
    source_gate["q10_final"] = {
        "model": q10_final_receipt,
        "timing": q10_final_timing,
    }
    atomic_json(args.out / "source-gate.json", source_gate)
    del source_matrix, y23, entity23, entity_labels23, fold_of_entity, fold_of_flow, all_rows
    gc.collect()

    q00_final = xgb.Booster()
    q00_final.load_model(str(args.parent_run_root / "model_semantic168.json"))
    if int(q00_final.num_boosted_rounds()) != N_TREE:
        raise SystemExit("父 Q00 最终模型树数不是 800")
    q00_prediction_device = configure_prediction_device(q00_final, "Q00/final")
    q10_prediction_device = configure_prediction_device(q10_final, "Q10/final")
    seal = {
        "schema_version": "ch4-xgb-dtep-fixed-dyadic-target-seal-v1",
        "run_id": RUN_ID,
        "sealed_before_target_feature_and_label_load": True,
        "target_labels_loaded": False,
        "target_score_call_budget": 2,
        "cells": config["cells"],
        "feature_schema_sha256": feature_receipt["sha256"],
        "complete_dyadic_scales": list(COMPLETE_SCALES),
        "recent_scales": list(RECENT_SCALES),
        "recent_scale_weights": [RECENT_WEIGHT] * len(RECENT_SCALES),
        "target_gate": config["target_gate"],
        "efficiency_gate": config["efficiency_gate"],
        "bucket_contract": config["entity_flow_count_buckets"],
        "models": {
            "Q00": {
                "sha256": parent["artifact_sha256"]["model_semantic168.json"],
                "prediction_device": q00_prediction_device,
            },
            "Q10": {**q10_final_receipt, "prediction_device": q10_prediction_device},
        },
        "script_sha256": script_sha,
        "config_sha256": config_sha,
        "source_gate_sha256": sha256_file(args.out / "source-gate.json"),
    }
    atomic_json(args.out / "target-evaluation-seal.json", seal)
    validate_target_cache()
    log("阶段二：封印后读取无标签目标特征，只构造一次 fixed_dyadic251")
    indices24 = np.load(CACHE / "I24.npy")
    mask24 = np.load(CACHE / "M24.npy")
    source24 = np.load(CACHE / "s24.npy", allow_pickle=True)
    destination24 = np.load(CACHE / "d24.npy", allow_pickle=True)
    time24 = np.load(CACHE / "t24.npy")
    assert_sequence_contract(time24, indices24, mask24, N_FLOW_24, "LSPR24")
    del time24
    entity_key24 = np.array(
        [
            left + "|" + right if left <= right else right + "|" + left
            for left, right in zip(source24, destination24, strict=True)
        ],
        object,
    )
    _, entity24 = np.unique(entity_key24, return_inverse=True)
    if int(entity24.max()) + 1 != N_ENTITY_24:
        raise SystemExit("LSPR24 实体数不符")
    del entity_key24, source24, destination24
    target_matrix, target_feature_timing = build_fixed_dyadic_matrix(
        CACHE / "X24.npy",
        N_FLOW_24,
        indices24,
        mask24,
        int(config["sequence_batch"]),
        int(config["predict_batch"]),
        "LSPR24",
    )
    del indices24, mask24
    prediction_ledger: list[dict[str, Any]] = []
    q00_predict_started = time.time()
    q00_flow_scores = predict_rows(
        q00_final,
        target_matrix[:, :SEMANTIC_DIM],
        int(config["predict_batch"]),
        "Q00/LSPR24",
    )
    q00_predict_seconds = time.time() - q00_predict_started
    q00_predict_resource = sample_resources(torch, "Q00/LSPR24/预测后")
    prediction_ledger.append(
        {"call": 1, "cell": "Q00", "view": "semantic168", "n_flow": N_FLOW_24}
    )
    q10_predict_started = time.time()
    q10_flow_scores = predict_rows(
        q10_final,
        target_matrix,
        int(config["predict_batch"]),
        "Q10/LSPR24",
    )
    q10_predict_seconds = time.time() - q10_predict_started
    q10_predict_resource = sample_resources(torch, "Q10/LSPR24/预测后")
    prediction_ledger.append(
        {"call": 2, "cell": "Q10", "view": "fixed_dyadic251", "n_flow": N_FLOW_24}
    )
    prediction_receipt = {
        "schema_version": "ch4-xgb-dtep-fixed-dyadic-target-prediction-v1",
        "run_id": RUN_ID,
        "sealed_before_target_labels": True,
        "target_label_loads": 0,
        "target_matrix_builds": 1,
        "target_score_calls": 2,
        "prediction_ledger": prediction_ledger,
        "coverage_rows": {"Q00": len(q00_flow_scores), "Q10": len(q10_flow_scores)},
        "prediction_seconds": {"Q00": q00_predict_seconds, "Q10": q10_predict_seconds},
        "per_flow_scores_persisted": False,
    }
    atomic_json(args.out / "target-prediction-receipt.json", prediction_receipt)
    del target_matrix, q00_final, q10_final
    torch.cuda.empty_cache()
    gc.collect()

    log("阶段三：预测收据落盘后首次读取目标标签，执行冻结聚合评价")
    y24 = np.load(CACHE / "y24.npy")
    if len(y24) != N_FLOW_24:
        raise SystemExit("LSPR24 标签长度不符")
    entity_labels24 = np.zeros(N_ENTITY_24, np.float32)
    np.maximum.at(entity_labels24, entity24, y24)
    if int(entity_labels24.sum()) != N_POS_ENTITY_24:
        raise SystemExit("LSPR24 正实体数不符")
    q00_entity_scores = mean_entity_scores(q00_flow_scores, entity24, N_ENTITY_24)
    q10_entity_scores = mean_entity_scores(q10_flow_scores, entity24, N_ENTITY_24)
    flow_counts = np.bincount(entity24, minlength=N_ENTITY_24)
    q00_ap = entity_ap(entity_labels24, q00_entity_scores)
    q10_ap = entity_ap(entity_labels24, q10_entity_scores)
    if not math.isclose(q00_ap, Q00_TARGET_AP, rel_tol=0.0, abs_tol=1e-10):
        raise SystemExit(f"Q00 目标总体 AP 未复现父全精度锚点：{q00_ap}")
    bucket_results: dict[str, Any] = {}
    bucket_masks: dict[str, np.ndarray] = {}
    for item in config["entity_flow_count_buckets"]:
        mask = bucket_mask(flow_counts, int(item["lower"]), item["upper"])
        bucket_masks[item["name"]] = mask
        q00_bucket_ap = entity_ap(entity_labels24[mask], q00_entity_scores[mask])
        q10_bucket_ap = entity_ap(entity_labels24[mask], q10_entity_scores[mask])
        parent_anchor = parent["q00_target_bucket_ap"][item["name"]]
        if not math.isclose(q00_bucket_ap, parent_anchor, rel_tol=0.0, abs_tol=1e-10):
            raise SystemExit(f"Q00 分桶 AP 未复现父全精度锚点：{item['name']}")
        bucket_results[item["name"]] = {
            "lower": item["lower"],
            "upper": item["upper"],
            "n_entity": int(mask.sum()),
            "n_positive_entity": int(entity_labels24[mask].sum()),
            "Q00_entity_ap": q00_bucket_ap,
            "Q10_entity_ap": q10_bucket_ap,
            "delta": q10_bucket_ap - q00_bucket_ap,
        }
    short_mask = flow_counts <= 100
    combined_short = {
        "Q00_entity_ap": entity_ap(entity_labels24[short_mask], q00_entity_scores[short_mask]),
        "Q10_entity_ap": entity_ap(entity_labels24[short_mask], q10_entity_scores[short_mask]),
    }
    combined_short["delta"] = combined_short["Q10_entity_ap"] - combined_short["Q00_entity_ap"]
    dr_results: dict[str, Any] = {}
    for rate in config["target_fpr_grid"]:
        key = f"{float(rate):g}"
        q00_dr = dr_at_fpr(entity_labels24, q00_entity_scores, float(rate))
        q10_dr = dr_at_fpr(entity_labels24, q10_entity_scores, float(rate))
        if not math.isclose(q00_dr, Q00_TARGET_DR[key], rel_tol=0.0, abs_tol=1e-12):
            raise SystemExit(f"Q00 DR@{key}FPR 未复现父全精度锚点")
        dr_results[key] = {"Q00": q00_dr, "Q10": q10_dr, "delta": q10_dr - q00_dr}

    target_gate_checks = {
        "overall_ap_nonnegative": q10_ap - q00_ap >= 0.0,
        "bucket_101_1000_strict_positive": bucket_results["101-1000"]["delta"] > 0.0,
        "bucket_1001_plus_strict_positive": bucket_results["1001+"]["delta"] > 0.0,
        "first_three_each_protected": all(
            bucket_results[name]["delta"] >= -0.01 for name in ("1-2", "3-10", "11-100")
        ),
        "first_three_combined_nonnegative": combined_short["delta"] >= 0.0,
        "dr_0.01_protected": dr_results["0.01"]["delta"] >= -0.01,
        "dr_0.02_protected": dr_results["0.02"]["delta"] >= -0.01,
        "dr_0.04_nonnegative": dr_results["0.04"]["delta"] >= 0.0,
        "at_least_two_dr_points_nonnegative": sum(
            item["delta"] >= 0.0 for item in dr_results.values()
        )
        >= 2,
    }
    target_metrics_passed = all(target_gate_checks.values())

    source_ratios = [item["q10_to_q00_train_ratio"] for item in fold_timing]
    q00_target_seconds = target_feature_timing["q00_feature_seconds"] + q00_predict_seconds
    q10_target_seconds = target_feature_timing["q10_feature_seconds"] + q10_predict_seconds
    target_time_ratio = q10_target_seconds / max(q00_target_seconds, 1e-9)
    q00_memory_estimate = (
        N_FLOW_24 * SEMANTIC_DIM * 4
        + int(config["predict_batch"]) * SEMANTIC_DIM * 4
    ) / 2**30
    q10_memory_estimate = (
        N_FLOW_24 * FIXED_DYADIC_DIM * 4
        + int(config["predict_batch"]) * FIXED_DYADIC_DIM * 4
    ) / 2**30
    observed_host_peak = max(item["host_peak_gib"] for item in RESOURCE_SAMPLES)
    observed_gpu_peak = max(item["gpu_total_used_gib"] for item in RESOURCE_SAMPLES)
    q00_gpu_samples = [
        max(sample["gpu_total_used_gib"] for sample in item["q00"]["resource_samples"])
        for item in fold_timing
    ] + [q00_predict_resource["gpu_total_used_gib"]]
    q10_gpu_samples = [
        max(sample["gpu_total_used_gib"] for sample in item["q10"]["resource_samples"])
        for item in fold_timing
    ] + [q10_predict_resource["gpu_total_used_gib"]]
    gpu_ratios = [
        candidate / max(baseline, 1e-9)
        for candidate, baseline in zip(q10_gpu_samples, q00_gpu_samples, strict=True)
    ]
    efficiency_checks = {
        "input_dim_is_251": FIXED_DYADIC_DIM == 251,
        "no_per_scale_expansion": feature_receipt["per_scale_columns_exposed"] is False,
        "each_fold_train_ratio_le_2": all(value <= 2.0 for value in source_ratios),
        "target_feature_plus_predict_ratio_le_2": target_time_ratio <= 2.0,
        "host_peak_below_65_gib": observed_host_peak < 65.0,
        "gpu_peak_below_24_gib": observed_gpu_peak < 24.0,
        "host_estimate_ratio_le_2": q10_memory_estimate / q00_memory_estimate <= 2.0,
        "gpu_observed_ratios_le_2": all(value <= 2.0 for value in gpu_ratios),
        "recent_state_at_most_64_flows": target_feature_timing["max_recent_state_flows"] <= 64,
        "same_prediction_backend": q00_prediction_device == q10_prediction_device == "cuda:0",
        "same_prediction_batch": True,
    }
    efficiency_passed = all(efficiency_checks.values())
    if not target_metrics_passed:
        decision = "Q0_REJECTED_TARGET_METRICS"
    elif not efficiency_passed:
        decision = "Q0_REJECTED_EFFICIENCY"
    else:
        decision = "Q0_ADVANCE_FORMAL_PENDING"

    result = {
        "schema_version": "ch4-xgb-dtep-fixed-dyadic-q0-results-v1",
        "run_id": RUN_ID,
        "seed": 42,
        "screening_only": True,
        "formal": False,
        "formal_paper_evidence": False,
        "independent_test": False,
        "decision": decision,
        "evidence_status": "实验待证；单种子 Q0 只决定是否进入正式重复实验",
        "source_gate": source_gate,
        "target": {
            "Q00": {"entity_ap": q00_ap, "view": "semantic168", "p": 1.0},
            "Q10": {"entity_ap": q10_ap, "view": "fixed_dyadic251", "p": 1.0},
            "overall_ap_delta": q10_ap - q00_ap,
            "buckets": bucket_results,
            "first_three_combined": combined_short,
            "dr_at_fpr": dr_results,
            "gate_checks": target_gate_checks,
            "gate_passed": target_metrics_passed,
            "anchor_receipt": {
                "parent_eval_sha256": parent["parent_eval_sha256"],
                "parent_bucket_sha256": parent["parent_bucket_sha256"],
                "q00_full_precision_reproduced": True,
            },
        },
        "efficiency": {
            "source_fold_train_ratios": source_ratios,
            "target_q00_feature_plus_predict_seconds": q00_target_seconds,
            "target_q10_feature_plus_predict_seconds": q10_target_seconds,
            "target_time_ratio": target_time_ratio,
            "q00_host_matrix_plus_batch_estimate_gib": q00_memory_estimate,
            "q10_host_matrix_plus_batch_estimate_gib": q10_memory_estimate,
            "host_estimate_ratio": q10_memory_estimate / q00_memory_estimate,
            "observed_host_peak_gib": observed_host_peak,
            "observed_gpu_peak_gib": observed_gpu_peak,
            "gpu_observed_ratios": gpu_ratios,
            "resource_samples": RESOURCE_SAMPLES,
            "feature_timing": target_feature_timing,
            "checks": efficiency_checks,
            "passed": efficiency_passed,
        },
        "isolation": {
            "target_feature_loads": 1,
            "target_label_loads": 1,
            "target_matrix_builds": 1,
            "target_score_calls": 2,
            "prediction_ledger": prediction_ledger,
            "target_labels_loaded_after_prediction_receipt": True,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "derived_matrices_persisted": False,
            "bucket_membership_persisted": False,
            "target_models_persisted": False,
        },
        "timing": {"total_seconds": time.time() - T0},
    }
    atomic_json(args.out / "dtep-fixed-dyadic-q0-results.json", result)
    metric_payload = {
        "source/q10_minus_q00_pooled": pooled_delta,
        "source/gate_passed": 1,
        "target/Q00_entity_ap": q00_ap,
        "target/Q10_entity_ap": q10_ap,
        "target/Q10_minus_Q00_entity_ap": q10_ap - q00_ap,
        "target/gate_passed": int(target_metrics_passed),
        "efficiency/gate_passed": int(efficiency_passed),
        "efficiency/target_time_ratio": target_time_ratio,
        "efficiency/host_peak_gib": observed_host_peak,
        "efficiency/gpu_peak_gib": observed_gpu_peak,
        "runtime/total_seconds": result["timing"]["total_seconds"],
    }
    for name, values in bucket_results.items():
        metric_payload[f"target/bucket/{name}/delta_entity_ap"] = values["delta"]
    for rate, values in dr_results.items():
        metric_payload[f"target/dr_at_fpr/{rate}/delta"] = values["delta"]
    swanlab.log(metric_payload, step=0)
    swanlab.finish()
    atomic_json(
        args.out / "swanlab-receipt.json",
        {
            "schema_version": "ch4-xgb-dtep-fixed-dyadic-swanlab-v1",
            "completed": True,
            "workspace": tracking["workspace"],
            "project": tracking["project"],
            "mode": tracking["mode"],
            "aggregate_only": True,
            "metric_keys": sorted(metric_payload),
        },
    )
    del q00_flow_scores, q10_flow_scores, q00_entity_scores, q10_entity_scores
    del entity24, entity_labels24, y24, flow_counts, bucket_masks
    write_manifest(args.out, script_sha)
    log(f"DTEP 固定二进 Q0 完成：{decision}")


if __name__ == "__main__":
    main()
