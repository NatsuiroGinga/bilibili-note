#!/usr/bin/env python3
"""从已冻结的源年模型接续 XGBoost+CPA+ELP 的 LSPR24 评价。

本入口只读取指定父运行的选择收据、有效配置收据和两个最终模型。它重新从共享只读缓存
构造 LSPR24 的 raw83/semantic168 输入并完成四格评价，不训练、不中间保存逐样本分数。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "runs/diagnostics/dijk-repro/cache"
BASE_FULL = ROOT / "runs/diagnostics/ch3-baselines-full"
DIJK_MODULE_ROOT = ROOT / "tools/dijk2026_replication"
if str(DIJK_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(DIJK_MODULE_ROOT))

from dijk_fields import DIJK_FEATURES  # noqa: E402


PARENT_RUN_ID = "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1"
CONTINUATION_RUN_ID = f"{PARENT_RUN_ID}-eval-continuation2"
EXPECTED_SHA256 = {
    "selection_frozen_xgb2x2.json": "a9075653efc6b29b6eb9d72f04409781af18e7c65cb31c1ba9bac941e1293943",
    "effective_config_receipts.json": "657c9f88b3c37f15e48817b145ad8bb22b8f4edd5ba700742b945c84c413515d",
    "model_raw83.json": "fcff042b8621812d8ed781e5571edae36ec8c9d43ec4840e6b27ae9a0302e218",
    "model_semantic168.json": "1805e15d96ac4ebb57df910640a4c5e1af58f692659db2eb80b724851efe42e9",
}
AUTHORIZED_SWANLAB_WORKSPACE = "mortiswang"
AUTHORIZED_SWANLAB_PROJECT = "ns3-rwkv-lspr24"
EXPECTED_XGB_PARAMS = {
    "tree_method": "hist",
    "device": "cuda",
    "max_depth": 8,
    "eta": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "lambda": 1.0,
    "max_bin": 256,
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "seed": 42,
    "nthread": 32,
}
EXPECTED_CONFIG = {
    "run_id": PARENT_RUN_ID,
    "seed": 42,
    "n_fold": 3,
    "p_grid": [0.5, 1.0, 2.0, 4.0, 8.0],
    "num_boost_round": 800,
    "xgb_params": EXPECTED_XGB_PARAMS,
    "effective_config_float_compare": {"rel_tol": 1e-7, "abs_tol": 1e-12},
    "adapters": ["mean166", "semantic168"],
    "target_fpr_grid": [0.001, 0.005, 0.01, 0.02, 0.04, 0.08],
    "artifact_policy": {
        "persist_fold_models": True,
        "persist_final_models": True,
        "persist_oof_scores": False,
        "persist_target_scores": False,
    },
}
L = 128
D_RAW = 83
N_FLOW_24 = 20_227_356
N_ENT_24_EXPECT = 47_115
N_POS_ENT_24_EXPECT = 752
FLOW_PI_24_EXPECT = 0.0257073138
TARGET_FPR = 0.04
CPU_ANCHOR = {
    "flow_ap": 0.2223914545997109,
    "ent_ap_max": 0.512898847990404,
    "dr_at_fpr_max": 0.6928191489361702,
}
GATE_TOL = 1e-10
CPU_SCORES_NPY = BASE_FULL / "scores_xgboost_dijk2026.npy"
BOOT_SEED = 20260818
BACKBONE_CONTEXT = {
    "感知机": {"no_mech": 0.3350, "with_mech": 0.5184, "gain_points": 18.34},
    "一维卷积": {"no_mech": 0.2794, "with_mech": 0.4352, "gain_points": 15.58},
    "全注意力": {"no_mech": 0.0917, "with_mech": 0.2168, "gain_points": 12.51},
    "门控循环": {"no_mech": 0.1648, "with_mech": 0.1921, "gain_points": 2.73},
}

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
    idx
    for idx in range(len(DIJK_FEATURES))
    if idx not in CATEGORICAL_IDX and idx not in BOOLEAN_IDX
)
assert len(DIJK_FEATURES) == D_RAW
assert len(NUMERIC_IDX) == 76

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, value: Any) -> None:
    partial = path.with_suffix(path.suffix + ".partial")
    with partial.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, default=str)
    os.replace(partial, path)


def dig(config: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = config
    for key in path:
        value = value[key]
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="接续 XGBoost+CPA+ELP 的 LSPR24 仅评价阶段")
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
        "--out",
        type=Path,
        default=ROOT / "runs/diagnostics" / CONTINUATION_RUN_ID,
    )
    parser.add_argument("--bootstrap", type=int, default=int(os.environ.get("XGB2X2_BOOT", "1000")))
    parser.add_argument(
        "--predict-batch", type=int, default=int(os.environ.get("XGB2X2_PRED_BATCH", "2000000"))
    )
    parser.add_argument(
        "--sequence-batch", type=int, default=int(os.environ.get("XGB2X2_SEQ_BATCH", "2048"))
    )
    parser.add_argument(
        "--gpu-need-gib", type=float, default=float(os.environ.get("XGB2X2_GPU_NEED_GIB", "11"))
    )
    parser.add_argument(
        "--gpu-floor-gib", type=float, default=float(os.environ.get("XGB2X2_GPU_FLOOR_GIB", "8"))
    )
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def validate_parent_inputs(args: argparse.Namespace) -> dict[str, Any]:
    parent = args.parent_run_root.resolve()
    if parent.name != PARENT_RUN_ID:
        raise SystemExit(f"父运行身份不符：{parent.name}")
    if args.out.resolve() == parent:
        raise SystemExit("接续输出目录不得覆盖父运行目录")
    if args.bootstrap <= 0 or args.predict_batch <= 0 or args.sequence_batch <= 0:
        raise SystemExit("批大小与自助法次数必须为正整数")

    actual_hashes: dict[str, str] = {}
    for name, expected in EXPECTED_SHA256.items():
        path = parent / name
        if not path.is_file():
            raise SystemExit(f"父运行制品缺失：{path}")
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"父运行制品摘要不符：{name} 实际 {actual}，期望 {expected}")
        actual_hashes[name] = actual

    if not args.parent_config.is_file():
        raise SystemExit(f"父配置缺失：{args.parent_config}")
    config = load_json(args.parent_config)
    for key, expected in EXPECTED_CONFIG.items():
        if config.get(key) != expected:
            raise SystemExit(f"父配置字段不符：{key}")
    tracking = config.get("tracking", {})
    if tracking.get("workspace") != AUTHORIZED_SWANLAB_WORKSPACE:
        raise SystemExit("SwanLab 工作空间与授权目的地不符")
    if tracking.get("project") != AUTHORIZED_SWANLAB_PROJECT:
        raise SystemExit("SwanLab 项目与授权目的地不符")
    if tracking.get("mode") != "online" or tracking.get("aggregate_only") is not True:
        raise SystemExit("SwanLab 必须使用在线聚合信息模式")

    selection = load_json(parent / "selection_frozen_xgb2x2.json")
    if selection.get("run_name") != PARENT_RUN_ID:
        raise SystemExit("选择收据的父运行身份不符")
    if selection.get("xgboost_version") != "3.2.0":
        raise SystemExit("选择收据的 XGBoost 版本不符")
    if selection.get("num_boost_round") != 800 or selection.get("seed") != 42:
        raise SystemExit("选择收据的树数或种子不符")
    if selection.get("xgb_params") != EXPECTED_XGB_PARAMS:
        raise SystemExit("选择收据的 XGBoost 参数不符")
    adapter = selection.get("adapter_selection", {}).get("selected")
    if adapter != "semantic168":
        raise SystemExit(f"冻结适配器应为 semantic168，实为 {adapter}")
    p_selection = selection.get("p_selection", {})
    p_raw = float(p_selection.get("raw83", {}).get("p_selected", math.nan))
    p_semantic = float(p_selection.get("semantic168", {}).get("p_selected", math.nan))
    if p_raw != 2.0 or p_semantic != 1.0:
        raise SystemExit(f"冻结 p 不符：raw83={p_raw} semantic168={p_semantic}")
    final_models = selection.get("final_models", {})
    for name in ("raw83", "semantic168"):
        if int(final_models.get(name, {}).get("n_tree", -1)) != 800:
            raise SystemExit(f"选择收据中的最终模型树数不符：{name}")

    effective_receipts = load_json(parent / "effective_config_receipts.json")
    if not isinstance(effective_receipts, list) or not effective_receipts:
        raise SystemExit("父有效配置收据为空或结构异常")
    receipt_by_tag = {item.get("tag"): item for item in effective_receipts if isinstance(item, dict)}
    for tag in ("raw83/final", "semantic168/final"):
        if receipt_by_tag.get(tag, {}).get("passed") is not True:
            raise SystemExit(f"父有效配置收据未通过：{tag}")

    return {
        "parent_run_root": str(parent),
        "parent_run_id": PARENT_RUN_ID,
        "parent_config_path": str(args.parent_config.resolve()),
        "parent_config_sha256": sha256_file(args.parent_config),
        "artifact_sha256": actual_hashes,
        "selection": selection,
        "tracking": tracking,
        "selected_adapter": adapter,
        "p_selection": {"raw83": p_raw, "semantic168": p_semantic},
    }


def configure_prediction_device(booster: Any, tag: str) -> str:
    """模型加载态配置只描述当前推理器；历史训练身份由父收据与摘要证明。"""
    booster.set_param({"device": "cuda:0"})
    config = json.loads(booster.save_config())
    device = str(dig(config, ("learner", "generic_param", "device")))
    if device != "cuda:0":
        raise SystemExit(f"{tag} 推理设备应为 cuda:0，实为 {device}")
    return device


def assert_sequence_time_monotonic(t_flow: np.ndarray, indices: np.ndarray, mask: np.ndarray) -> None:
    if len(t_flow) != N_FLOW_24 or not np.isfinite(t_flow).all():
        raise SystemExit("LSPR24 时间戳数量异常或含非有限值")
    reversed_pairs = 0
    checked_pairs = 0
    started = time.time()
    for start in range(0, len(indices), 20_000):
        idx = indices[start : start + 20_000]
        valid = mask[start : start + 20_000] > 0
        timestamp = t_flow[idx]
        adjacent = valid[:, 1:] & valid[:, :-1]
        checked_pairs += int(adjacent.sum())
        reversed_pairs += int(((timestamp[:, 1:] < timestamp[:, :-1]) & adjacent).sum())
        beat("LSPR24/时间核验", min(start + 20_000, len(indices)), len(indices), started)
    if reversed_pairs:
        raise SystemExit(f"LSPR24 序列存在 {reversed_pairs} 个时间逆序相邻对")
    log(f"LSPR24 时间非降核验通过：检查 {checked_pairs:,} 个有效相邻对")


def build_semantic_matrix(
    x_path: Path,
    indices: np.ndarray,
    mask_values: np.ndarray,
    predict_batch: int,
    sequence_batch: int,
) -> np.ndarray:
    if indices.shape[1] != L or mask_values.shape != indices.shape:
        raise SystemExit(f"LSPR24 序列形状异常：I={indices.shape} M={mask_values.shape}")
    n_valid = int((mask_values > 0).sum())
    if n_valid != N_FLOW_24:
        raise SystemExit(f"LSPR24 掩码有效位 {n_valid:,} 与流数 {N_FLOW_24:,} 不符")
    dim = D_RAW + len(NUMERIC_IDX) + len(CATEGORICAL_IDX) + len(BOOLEAN_IDX) + 2
    if dim != 168:
        raise SystemExit(f"semantic168 维度推导异常：{dim}")

    output = np.empty((N_FLOW_24, dim), np.float32)
    source = np.load(x_path, mmap_mode="r")
    if source.shape != (N_FLOW_24, D_RAW):
        raise SystemExit(f"LSPR24 原始宽表形状不符：{source.shape}")
    started = time.time()
    for start in range(0, N_FLOW_24, predict_batch):
        stop = min(start + predict_batch, N_FLOW_24)
        output[start:stop, :D_RAW] = source[start:stop]
        beat("LSPR24/读入raw83", stop, N_FLOW_24, started)
    del source

    cover = np.zeros(N_FLOW_24, bool)
    lower = np.tri(L, L, dtype=bool)
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
            -1, len(NUMERIC_IDX)
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
        if cursor != dim:
            raise AssertionError(f"semantic168 游标异常：{cursor}")
        cover[target] = True
        beat("LSPR24/semantic168", min(start + sequence_batch, len(indices)), len(indices), started)
        del current, numeric, numeric_sum, residual, prefix_mask

    if not bool(cover.all()) or not np.isfinite(output).all():
        raise SystemExit("LSPR24 semantic168 覆盖不完整或含非有限值")
    log(f"LSPR24 semantic168 构造完成，用时 {time.time() - started:.0f}s")
    return output


def predict_rows(booster: Any, matrix: np.ndarray, batch_size: int, tag: str) -> np.ndarray:
    output = np.empty(len(matrix), np.float32)
    started = time.time()
    for start in range(0, len(matrix), batch_size):
        stop = min(start + batch_size, len(matrix))
        output[start:stop] = np.asarray(booster.inplace_predict(matrix[start:stop]), np.float32)
        beat(f"推理/{tag}", stop, len(matrix), started)
    if not np.isfinite(output).all():
        raise SystemExit(f"{tag} 的逐流分数含非有限值")
    log(f"[{tag}] 推理完成 {len(matrix):,} 行，用时 {time.time() - started:.0f}s")
    return output


def ent_scores(scores: np.ndarray, entity: np.ndarray, n_entity: int, p: float | None = None) -> np.ndarray:
    if p is None:
        values = np.full(n_entity, -np.inf, np.float32)
        np.maximum.at(values, entity, scores)
        return values
    numerator = np.zeros(n_entity, np.float64)
    count = np.zeros(n_entity, np.float64)
    np.add.at(numerator, entity, np.clip(scores, 1e-7, 1.0).astype(np.float64) ** p)
    np.add.at(count, entity, 1.0)
    return np.where(
        count > 0,
        (numerator / np.maximum(count, 1)) ** (1.0 / p),
        -np.inf,
    ).astype(np.float32)


def ent_ap_from(entity_scores: np.ndarray, labels: np.ndarray) -> tuple[float, int]:
    valid = np.isfinite(entity_scores)
    return float(average_precision_score(labels[valid], entity_scores[valid])), int(valid.sum())


def dr_at_fpr_from(entity_scores: np.ndarray, labels: np.ndarray, target: float = TARGET_FPR) -> float:
    valid = np.isfinite(entity_scores)
    values = entity_scores[valid]
    valid_labels = labels[valid]
    negative = np.sort(values[valid_labels == 0])[::-1]
    if len(negative) == 0:
        return float("nan")
    threshold = negative[min(int(len(negative) * target), len(negative) - 1)]
    return float((values[valid_labels == 1] >= threshold).mean())


def run_regression_gate(y24: np.ndarray, entity: np.ndarray, entity_labels: np.ndarray) -> dict[str, Any]:
    if not CPU_SCORES_NPY.is_file():
        raise SystemExit(f"回归锚点分数缺失：{CPU_SCORES_NPY}")
    scores = np.load(CPU_SCORES_NPY)
    if len(scores) != N_FLOW_24:
        raise SystemExit("回归锚点分数长度与 LSPR24 流数不符")
    aggregate = ent_scores(scores, entity, N_ENT_24_EXPECT)
    recomputed = {
        "flow_ap": float(average_precision_score(y24, scores)),
        "ent_ap_max": ent_ap_from(aggregate, entity_labels)[0],
        "dr_at_fpr_max": dr_at_fpr_from(aggregate, entity_labels),
    }
    delta = {key: recomputed[key] - expected for key, expected in CPU_ANCHOR.items()}
    failed = [key for key, value in delta.items() if abs(value) > GATE_TOL]
    gate = {
        "nature": "失败门",
        "kind": "结构性核验（同一份分数走冻结评价代码）",
        "tolerance": GATE_TOL,
        "anchor": CPU_ANCHOR,
        "recomputed": recomputed,
        "delta": delta,
        "passed": not failed,
    }
    if failed:
        gate["failed_keys"] = failed
        raise SystemExit(f"回归比对门禁失败：{failed}")
    log(f"回归比对门禁通过：全部 |差值| ≤ {GATE_TOL}")
    return gate


def ci_of(values: np.ndarray) -> dict[str, float | int]:
    finite = values[np.isfinite(values)]
    return {
        "n": int(len(finite)),
        "mean": float(finite.mean()),
        "lo95": float(np.percentile(finite, 2.5)),
        "hi95": float(np.percentile(finite, 97.5)),
    }


def verdict(interval: dict[str, float | int]) -> str:
    if float(interval["lo95"]) > 0:
        return "显著为正"
    if float(interval["hi95"]) < 0:
        return "显著为负"
    return "落在波动幅度内"


def gpu_guard(torch_module: Any, floor_gib: float, stage: str) -> float:
    free = torch_module.cuda.mem_get_info()[0] / 2**30
    if free < floor_gib:
        raise SystemExit(f"{stage}：可用显存 {free:.2f} GiB 低于下限 {floor_gib:.1f} GiB")
    return free


def main() -> None:
    args = parse_args()
    parent = validate_parent_inputs(args)
    if args.validate_inputs:
        print("CONTINUATION_INPUTS_VALID", flush=True)
        return

    protected_outputs = (
        args.out / "continuation_receipt.json",
        args.out / "xgb_cpa_elp_results.json",
        args.out / "manifest.json",
        args.out / "swanlog",
    )
    if any(path.exists() for path in protected_outputs):
        raise SystemExit(f"接续科学制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    self_sha = sha256_file(Path(__file__).resolve())
    log(f"接续运行 {CONTINUATION_RUN_ID}，父运行 {PARENT_RUN_ID}")
    log("协议：复用父运行最终模型；不重训源年；重新构建目标年；不保存逐样本分数")

    import swanlab
    import torch
    import xgboost as xgb

    build_info = xgb.build_info()
    if xgb.__version__ != "3.2.0" or build_info.get("USE_CUDA") is not True:
        raise SystemExit(f"XGBoost 环境不符：version={xgb.__version__} USE_CUDA={build_info.get('USE_CUDA')}")
    if not torch.cuda.is_available():
        raise SystemExit("CUDA 不可用，拒绝以 CPU 冒充 GPU 运行")
    free, total = torch.cuda.mem_get_info()
    log(f"GPU 总显存 {total / 2**30:.2f} GiB，当前可用 {free / 2**30:.2f} GiB")
    if free / 2**30 < args.gpu_need_gib:
        raise SystemExit(f"可用显存低于启动门槛 {args.gpu_need_gib:.1f} GiB")
    try:
        processes = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in processes.stdout.strip().splitlines():
            log(f"同卡在跑：{line}")
    except OSError as error:
        log(f"nvidia-smi 不可用（{type(error).__name__}），跳过进程枚举")

    models: dict[str, Any] = {}
    model_receipts: dict[str, Any] = {}
    for view in ("raw83", "semantic168"):
        booster = xgb.Booster()
        booster.load_model(parent["parent_run_root"] + f"/model_{view}.json")
        n_tree = int(booster.num_boosted_rounds())
        if n_tree != 800:
            raise SystemExit(f"{view} 模型树数应为 800，实为 {n_tree}")
        prediction_device = configure_prediction_device(booster, view)
        models[view] = booster
        model_receipts[view] = {
            "n_tree": n_tree,
            "sha256": parent["artifact_sha256"][f"model_{view}.json"],
            "prediction_device": prediction_device,
            "historical_training_config_evidence": "父 selection 与 effective_config_receipts 的固定摘要",
        }
        log(f"父模型核验通过：{view}，树数={n_tree}，SHA-256={model_receipts[view]['sha256']}")

    receipt = {
        "run_id": CONTINUATION_RUN_ID,
        "script_sha256": self_sha,
        "parent_run_id": PARENT_RUN_ID,
        "parent_run_root": parent["parent_run_root"],
        "parent_config_path": parent["parent_config_path"],
        "parent_config_sha256": parent["parent_config_sha256"],
        "parent_artifact_sha256": parent["artifact_sha256"],
        "models": model_receipts,
        "selected_adapter_read_from_parent": parent["selected_adapter"],
        "p_selection_read_from_parent": parent["p_selection"],
        "source_year_retrained": False,
        "target_year_rebuilt": True,
        "target_per_sample_scores_persisted": False,
    }
    atomic_json(args.out / "continuation_receipt.json", receipt)

    tracking = parent["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=CONTINUATION_RUN_ID,
        config={
            "parent_run_id": PARENT_RUN_ID,
            "source_year_retrained": False,
            "target_year_rebuilt": True,
            "selected_adapter": parent["selected_adapter"],
            "p_raw83": parent["p_selection"]["raw83"],
            "p_semantic168": parent["p_selection"]["semantic168"],
            "xgboost_version": xgb.__version__,
            "script_sha256": self_sha,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )

    log("阶段一：读取并核验 LSPR24 共享只读缓存")
    y24 = np.load(CACHE / "y24.npy")
    indices = np.load(CACHE / "I24.npy")
    mask = np.load(CACHE / "M24.npy")
    source_address = np.load(CACHE / "s24.npy", allow_pickle=True)
    destination_address = np.load(CACHE / "d24.npy", allow_pickle=True)
    time_values = np.load(CACHE / "t24.npy")
    if len(y24) != N_FLOW_24:
        raise SystemExit(f"LSPR24 流数应为 {N_FLOW_24:,}，实为 {len(y24):,}")
    assert_sequence_time_monotonic(time_values, indices, mask)
    del time_values

    entity_key = np.array(
        [a + "|" + b if a <= b else b + "|" + a for a, b in zip(source_address, destination_address)],
        object,
    )
    _, entity = np.unique(entity_key, return_inverse=True)
    n_entity = int(entity.max()) + 1
    entity_labels = np.zeros(n_entity, np.float32)
    np.maximum.at(entity_labels, entity, y24)
    flow_positive_rate = float(y24.astype(np.float64).mean())
    if n_entity != N_ENT_24_EXPECT:
        raise SystemExit(f"LSPR24 实体数应为 {N_ENT_24_EXPECT:,}，实为 {n_entity:,}")
    if int(entity_labels.sum()) != N_POS_ENT_24_EXPECT:
        raise SystemExit("LSPR24 正例实体数不符")
    if abs(flow_positive_rate - FLOW_PI_24_EXPECT) >= 1e-9:
        raise SystemExit(f"LSPR24 逐流正例率不符：{flow_positive_rate:.12f}")
    del entity_key, source_address, destination_address
    regression_gate = run_regression_gate(y24, entity, entity_labels)

    log("阶段二：从共享缓存重新构建 LSPR24 raw83/semantic168")
    semantic = build_semantic_matrix(
        CACHE / "X24.npy", indices, mask, args.predict_batch, args.sequence_batch
    )
    del indices, mask
    log(f"LSPR24 输入就位：raw83={semantic[:, :D_RAW].shape} semantic168={semantic.shape}")

    log("阶段三：两模型各执行一次目标年推理")
    scores: dict[str, np.ndarray] = {}
    score_ledger: list[dict[str, Any]] = []
    for call, view in enumerate(("raw83", "semantic168"), start=1):
        gpu_guard(torch, args.gpu_floor_gib, f"{view}/目标年推理前")
        matrix = semantic[:, :D_RAW] if view == "raw83" else semantic
        scores[view] = predict_rows(models[view], matrix, args.predict_batch, f"{view}/LSPR24")
        score_ledger.append({"call": call, "view": view})
        torch.cuda.empty_cache()
    del semantic, models

    target_fpr_grid = tuple(float(value) for value in EXPECTED_CONFIG["target_fpr_grid"])
    cells = [
        ("C00", "raw83", None),
        ("C01", "raw83", parent["p_selection"]["raw83"]),
        ("C10", "semantic168", None),
        ("C11", "semantic168", parent["p_selection"]["semantic168"]),
    ]
    display_names = {
        "C00": "XGBoost 原始输入＋取最大聚合",
        "C01": "XGBoost 原始输入＋源年选定幂平均聚合",
        "C10": "XGBoost 语义前缀输入＋取最大聚合",
        "C11": "XGBoost 语义前缀输入＋源年选定幂平均聚合",
    }
    results: dict[str, dict[str, Any]] = {}
    entity_scores_by_cell: dict[str, np.ndarray] = {}
    log("阶段四：按父选择收据冻结的适配器与 p 评价四格")
    for cell, view, p_value in cells:
        aggregate = ent_scores(scores[view], entity, n_entity, p_value)
        entity_scores_by_cell[cell] = aggregate
        entity_ap, n_scored = ent_ap_from(aggregate, entity_labels)
        results[cell] = {
            "display_name": display_names[cell],
            "input_view": view,
            "input_dim": D_RAW if view == "raw83" else 168,
            "mech1_prefix_context": view != "raw83",
            "mech2_power_mean": p_value is not None,
            "p": p_value,
            "ent_ap": entity_ap,
            "n_ent_scored": n_scored,
            "dr_at_fpr": dr_at_fpr_from(aggregate, entity_labels),
            "dr_curve": {
                f"fpr_{fpr:g}": dr_at_fpr_from(aggregate, entity_labels, fpr)
                for fpr in target_fpr_grid
            },
            "flow_ap": float(average_precision_score(y24, scores[view])),
            "flow_auc": float(roc_auc_score(y24, scores[view])),
        }
        log(
            f"{cell} 输入={view} p={'取最大' if p_value is None else f'{p_value:g}'} "
            f"实体AP={entity_ap:.6f} DR@4%FPR={results[cell]['dr_at_fpr']:.6f}"
        )

    log(f"阶段五：实体级配对自助法 B={args.bootstrap}，种子={BOOT_SEED}")
    random_state = np.random.RandomState(BOOT_SEED)
    bootstrap = {cell: np.empty(args.bootstrap, np.float64) for cell in results}
    finite = {cell: np.isfinite(value) for cell, value in entity_scores_by_cell.items()}
    started = time.time()
    for iteration in range(args.bootstrap):
        sampled = random_state.randint(0, n_entity, n_entity)
        sampled_labels = entity_labels[sampled]
        if sampled_labels.max() <= 0:
            for cell in results:
                bootstrap[cell][iteration] = np.nan
            continue
        for cell in results:
            valid = finite[cell][sampled]
            bootstrap[cell][iteration] = average_precision_score(
                sampled_labels[valid], entity_scores_by_cell[cell][sampled][valid]
            )
        beat("实体配对自助法", iteration + 1, args.bootstrap, started, every=60.0)

    expressions = {
        "combo_C11_minus_C00": lambda values: values["C11"] - values["C00"],
        "mech1_only_C10_minus_C00": lambda values: values["C10"] - values["C00"],
        "mech2_only_C01_minus_C00": lambda values: values["C01"] - values["C00"],
        "interaction": lambda values: values["C11"] - values["C10"] - values["C01"] + values["C00"],
    }
    contrast: dict[str, dict[str, Any]] = {}
    for name, expression in expressions.items():
        point = float(expression({cell: results[cell]["ent_ap"] for cell in results}))
        interval = ci_of(expression(bootstrap))
        contrast[name] = {
            "point": point,
            "point_points": point * 100,
            "ci95": interval,
            "verdict": verdict(interval),
        }
    effect_a = contrast["mech1_only_C10_minus_C00"]["point"]
    effect_b = contrast["mech2_only_C01_minus_C00"]["point"]
    if effect_a > 0 and effect_b > 0:
        sign_pattern = "A>0 且 B>0"
    elif effect_a > 0:
        sign_pattern = "A>0 且 B≤0"
    elif effect_b > 0:
        sign_pattern = "A≤0 且 B>0"
    else:
        sign_pattern = "A≤0 且 B≤0"
    main_verdict = contrast["combo_C11_minus_C00"]["verdict"]
    main_case = {
        "显著为正": "情形一 增益显著为正",
        "落在波动幅度内": "情形二 落在波动幅度内",
        "显著为负": "情形三 增益为负",
    }[main_verdict]

    c00 = results["C00"]["ent_ap"]
    result = {
        "run_name": CONTINUATION_RUN_ID,
        "script_sha256": self_sha,
        "continuation_receipt": receipt,
        "seed": 42,
        "device": "cuda",
        "xgboost_version": xgb.__version__,
        "xgb_params": EXPECTED_XGB_PARAMS,
        "num_boost_round": 800,
        "regression_gate": regression_gate,
        "c00_baseline_identity": {
            "role": "本行的同设备科学基线",
            "device": "cuda",
            "value_ent_ap": c00,
            "cpu_reference_ent_ap": CPU_ANCHOR["ent_ap_max"],
            "cpu_reference_source": str(BASE_FULL / "trees_results.json"),
            "delta_vs_cpu_reference": c00 - CPU_ANCHOR["ent_ap_max"],
            "delta_nature": "诊断，不作失败门",
        },
        "cells": results,
        "contrast": contrast,
        "main_case": main_case,
        "sign_pattern_case4": sign_pattern,
        "bootstrap": {
            "B": args.bootstrap,
            "seed": BOOT_SEED,
            "unit": "实体",
            "covers": "评价集抽样波动",
            "does_not_cover": "p 的选择波动（p 在源年选定后固定）",
        },
        "p_selection": parent["selection"]["p_selection"],
        "adapter_selection": parent["selection"]["adapter_selection"],
        "n_fold": parent["selection"]["n_fold"],
        "fold_stat": parent["selection"]["fold_stat"],
        "p_grid": parent["selection"]["p_grid"],
        "lspr23": parent["selection"]["lspr23"],
        "lspr24": {
            "n_flow": N_FLOW_24,
            "n_entity": n_entity,
            "n_pos_entity": int(entity_labels.sum()),
            "flow_pos_rate": flow_positive_rate,
        },
        "backbone_context": BACKBONE_CONTEXT,
        "isolation": {
            "source_year_retrained": False,
            "target_year_rebuilt": True,
            "target_disk_loads": 1,
            "target_score_calls": 2,
            "ledger": score_ledger,
            "target_scores_persisted": False,
            "note": "四格由两个内存分数向量派生，不保存逐样本分数",
        },
        "timing": {"total_seconds": time.time() - T0},
    }
    result_path = args.out / "xgb_cpa_elp_results.json"
    atomic_json(result_path, result)

    swanlab.log(
        {
            "target/C00_entity_ap": results["C00"]["ent_ap"],
            "target/C01_entity_ap": results["C01"]["ent_ap"],
            "target/C10_entity_ap": results["C10"]["ent_ap"],
            "target/C11_entity_ap": results["C11"]["ent_ap"],
            "target/C11_minus_C00": contrast["combo_C11_minus_C00"]["point"],
            "target/C11_dr_at_fpr_0.04": results["C11"]["dr_at_fpr"],
            "target/C11_flow_ap": results["C11"]["flow_ap"],
            "source/selected_adapter_oof_ap": parent["selection"]["p_selection"]["semantic168"][
                "oof_ent_ap_at_max"
            ],
            "runtime/total_seconds": result["timing"]["total_seconds"],
        },
        step=0,
    )
    swanlab.finish()
    result["tracking"] = {
        "completed": True,
        "aggregate_only": True,
        "workspace": tracking["workspace"],
        "project": tracking["project"],
    }
    atomic_json(result_path, result)

    manifest_files = ["continuation_receipt.json", "xgb_cpa_elp_results.json"]
    manifest = {
        "run_id": CONTINUATION_RUN_ID,
        "script_sha256": self_sha,
        "parent_run_id": PARENT_RUN_ID,
        "source_year_retrained": False,
        "target_year_rebuilt": True,
        "per_sample_artifacts_persisted": False,
        "files": {},
    }
    for name in manifest_files:
        path = args.out / name
        manifest["files"][name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(args.out / "manifest.json", manifest)
    log(
        f"核心结果：C00={results['C00']['ent_ap'] * 100:.2f} "
        f"C11={results['C11']['ent_ap'] * 100:.2f} "
        f"增益={contrast['combo_C11_minus_C00']['point_points']:+.2f} 个点"
    )
    log(f"结果已存 {result_path}，总耗时 {(time.time() - T0) / 60:.1f} 分")


if __name__ == "__main__":
    main()
