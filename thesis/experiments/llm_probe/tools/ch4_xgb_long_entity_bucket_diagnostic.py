#!/usr/bin/env python3
"""零重训诊断 XGBoost 在 LSPR24 长实体上的四格收益方向。"""

from __future__ import annotations

import argparse
import json
import os
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

from ch3_xgb_cpa_elp_eval_continuation import (  # noqa: E402, I001
    CACHE,
    CONTINUATION_RUN_ID,
    D_RAW,
    EXPECTED_XGB_PARAMS,
    N_ENT_24_EXPECT,
    N_FLOW_24,
    N_POS_ENT_24_EXPECT,
    PARENT_RUN_ID,
    assert_sequence_time_monotonic,
    atomic_json,
    build_semantic_matrix,
    configure_prediction_device,
    ent_scores,
    gpu_guard,
    predict_rows,
    sha256_file,
    validate_parent_inputs,
)


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch4-xgb-long-entity-bucket-diagnostic-seed42-v1"
EXPECTED_PARENT_RESULT_SHA256 = "128b1225c96bb07c5b808dc2e0092223d1acb4c039b487a7007551a4f6b5135f"
EXPECTED_PARENT_MANIFEST_SHA256 = "f6b66cc94ef09b169ff29ce317464109bc701fa109875f6e9b7d09c889516115"
BUCKETS = (
    ("1-2", 1, 2),
    ("3-10", 3, 10),
    ("11-100", 11, 100),
    ("101-1000", 101, 1000),
    ("1001+", 1001, None),
)
CELL_SPECS = (
    ("raw_max", "raw83", None),
    ("raw_elp", "raw83", 2.0),
    ("semantic_max", "semantic168", None),
    ("semantic_elp", "semantic168", 1.0),
)
SPIKE_THRESHOLDS = (0.9, 0.99, 0.999)

T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="XGBoost LSPR24 长实体五档零重训诊断")
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
        "--out",
        type=Path,
        default=ROOT / "runs/diagnostics" / RUN_ID,
    )
    parser.add_argument(
        "--predict-batch",
        type=int,
        default=int(os.environ.get("XGB_LONG_BUCKET_PRED_BATCH", "2000000")),
    )
    parser.add_argument(
        "--sequence-batch",
        type=int,
        default=int(os.environ.get("XGB_LONG_BUCKET_SEQ_BATCH", "2048")),
    )
    parser.add_argument(
        "--gpu-need-gib",
        type=float,
        default=float(os.environ.get("XGB_LONG_BUCKET_GPU_NEED_GIB", "11")),
    )
    parser.add_argument(
        "--gpu-floor-gib",
        type=float,
        default=float(os.environ.get("XGB_LONG_BUCKET_GPU_FLOOR_GIB", "8")),
    )
    parser.add_argument("--validate-inputs", action="store_true")
    return parser.parse_args()


def validate_inputs(args: argparse.Namespace) -> dict[str, Any]:
    if args.out.resolve().name != RUN_ID:
        raise SystemExit(f"输出运行身份必须为 {RUN_ID}")
    if args.predict_batch <= 0 or args.sequence_batch <= 0:
        raise SystemExit("推理批大小与序列批大小必须为正整数")

    parent_args = argparse.Namespace(
        parent_run_root=args.parent_run_root,
        parent_config=args.parent_config,
        out=args.out,
        bootstrap=1,
        predict_batch=args.predict_batch,
        sequence_batch=args.sequence_batch,
    )
    parent = validate_parent_inputs(parent_args)

    parent_eval = args.parent_eval_root.resolve()
    if parent_eval.name != CONTINUATION_RUN_ID:
        raise SystemExit(f"父评价身份不符：{parent_eval.name}")
    expected_files = {
        "xgb_cpa_elp_results.json": EXPECTED_PARENT_RESULT_SHA256,
        "manifest.json": EXPECTED_PARENT_MANIFEST_SHA256,
    }
    eval_hashes: dict[str, str] = {}
    for name, expected in expected_files.items():
        path = parent_eval / name
        if not path.is_file():
            raise SystemExit(f"父评价制品缺失：{path}")
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"父评价制品摘要不符：{name} 实际 {actual}，期望 {expected}")
        eval_hashes[name] = actual

    status = load_json(parent_eval / "status.json")
    if (
        status.get("state") != "finished"
        or status.get("stage") != "complete"
        or status.get("exit_code") != 0
    ):
        raise SystemExit("父评价未处于 finished/complete/exit=0")
    result = load_json(parent_eval / "xgb_cpa_elp_results.json")
    if result.get("run_name") != CONTINUATION_RUN_ID or result.get("num_boost_round") != 800:
        raise SystemExit("父评价结果的运行身份或树数不符")
    if result.get("isolation", {}).get("target_score_calls") != 2:
        raise SystemExit("父评价结果未证明两模型各预测一次")
    if result.get("isolation", {}).get("target_scores_persisted") is not False:
        raise SystemExit("父评价结果的逐流分数持久化声明不符")

    parent["parent_eval_root"] = str(parent_eval)
    parent["parent_eval_sha256"] = eval_hashes
    return parent


def load_models(xgb_module: Any, parent: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    models: dict[str, Any] = {}
    receipts: dict[str, Any] = {}
    for view in ("raw83", "semantic168"):
        model_path = Path(parent["parent_run_root"]) / f"model_{view}.json"
        booster = xgb_module.Booster()
        booster.load_model(model_path)
        n_tree = int(booster.num_boosted_rounds())
        if n_tree != 800:
            raise SystemExit(f"{view} 模型树数应为 800，实为 {n_tree}")
        prediction_device = configure_prediction_device(booster, view)
        models[view] = booster
        receipts[view] = {
            "path": str(model_path.resolve()),
            "sha256": parent["artifact_sha256"][f"model_{view}.json"],
            "n_tree": n_tree,
            "prediction_device": prediction_device,
        }
    return models, receipts


def score_summary(values: np.ndarray) -> dict[str, int | float | None]:
    if len(values) == 0:
        return {"n": 0, "median": None, "p90": None, "p99": None, "max": None}
    return {
        "n": int(len(values)),
        "median": float(np.median(values)),
        "p90": float(np.percentile(values, 90)),
        "p99": float(np.percentile(values, 99)),
        "max": float(np.max(values)),
    }


def bucket_ap(labels: np.ndarray, scores: np.ndarray) -> float | None:
    if len(labels) == 0 or labels.min() == labels.max():
        return None
    return float(average_precision_score(labels, scores))


def make_bucket_mask(flow_counts: np.ndarray, lower: int, upper: int | None) -> np.ndarray:
    mask = flow_counts >= lower
    if upper is not None:
        mask &= flow_counts <= upper
    return mask


def summarize_buckets(
    flow_counts: np.ndarray,
    entity_labels: np.ndarray,
    cell_scores: dict[str, np.ndarray],
) -> dict[str, Any]:
    buckets: dict[str, Any] = {}
    for bucket_name, lower, upper in BUCKETS:
        mask = make_bucket_mask(flow_counts, lower, upper)
        labels = entity_labels[mask].astype(np.int8, copy=False)
        positive = labels == 1
        negative = labels == 0
        cells: dict[str, Any] = {}
        for cell_name, _, _ in CELL_SPECS:
            values = cell_scores[cell_name][mask]
            cells[cell_name] = {
                "entity_ap": bucket_ap(labels, values),
                "positive_score": score_summary(values[positive]),
                "negative_score": score_summary(values[negative]),
                "benign_high_score_count": {
                    f"ge_{threshold:g}": int((values[negative] >= threshold).sum())
                    for threshold in SPIKE_THRESHOLDS
                },
            }
        raw_ap = cells["raw_max"]["entity_ap"]
        contrasts = {
            "semantic_elp_minus_raw_max": (
                None
                if raw_ap is None or cells["semantic_elp"]["entity_ap"] is None
                else float(cells["semantic_elp"]["entity_ap"] - raw_ap)
            ),
            "semantic_max_minus_raw_max": (
                None
                if raw_ap is None or cells["semantic_max"]["entity_ap"] is None
                else float(cells["semantic_max"]["entity_ap"] - raw_ap)
            ),
            "raw_elp_minus_raw_max": (
                None
                if raw_ap is None or cells["raw_elp"]["entity_ap"] is None
                else float(cells["raw_elp"]["entity_ap"] - raw_ap)
            ),
        }
        buckets[bucket_name] = {
            "lower_inclusive": lower,
            "upper_inclusive": upper,
            "n_entity": int(mask.sum()),
            "n_positive_entity": int(positive.sum()),
            "n_negative_entity": int(negative.sum()),
            "n_flow": int(flow_counts[mask].sum()),
            "cells": cells,
            "contrasts": contrasts,
        }
    return buckets


def mechanical_verdict(buckets: dict[str, Any]) -> dict[str, Any]:
    long_names = ("101-1000", "1001+")
    positive_counts = {name: buckets[name]["n_positive_entity"] for name in long_names}
    deltas = {
        name: buckets[name]["contrasts"]["semantic_elp_minus_raw_max"] for name in long_names
    }
    low_support = any(count < 10 for count in positive_counts.values())
    if low_support or any(value is None for value in deltas.values()):
        decision = "混合或低支持信号"
    elif all(float(value) < 0 for value in deltas.values()):
        decision = "XGBoost 复现长实体方向翻转"
    elif all(float(value) >= 0 for value in deltas.values()):
        decision = "XGBoost 未复现该病灶"
    else:
        decision = "混合或低支持信号"
    return {
        "decision": decision,
        "long_bucket_positive_entity_counts": positive_counts,
        "semantic_elp_minus_raw_max": deltas,
        "rule_frozen_before_target_diagnostic": True,
        "selects_backbone": False,
    }


def main() -> None:
    args = parse_args()
    parent = validate_inputs(args)

    import swanlab
    import torch
    import xgboost as xgb

    build_info = xgb.build_info()
    if xgb.__version__ != "3.2.0" or build_info.get("USE_CUDA") is not True:
        raise SystemExit(
            f"XGBoost 环境不符：version={xgb.__version__} USE_CUDA={build_info.get('USE_CUDA')}"
        )
    models, model_receipts = load_models(xgb, parent)
    if args.validate_inputs:
        print("XGB_LONG_ENTITY_BUCKET_INPUTS_VALID", flush=True)
        return

    protected = (
        args.out / "xgb_long_entity_bucket_results.json",
        args.out / "manifest.json",
        args.out / "swanlab-receipt.json",
        args.out / "swanlog",
    )
    if any(path.exists() for path in protected):
        raise SystemExit(f"诊断制品已存在，禁止覆盖：{args.out}")
    args.out.mkdir(parents=True, exist_ok=True)
    script_sha = sha256_file(Path(__file__).resolve())
    log(f"启动 {RUN_ID}，父模型运行 {PARENT_RUN_ID}，父评价 {CONTINUATION_RUN_ID}")
    log("协议：零重训、两次逐流预测、四格复用、仅持久化聚合诊断")

    if not torch.cuda.is_available():
        raise SystemExit("CUDA 不可用，拒绝以 CPU 冒充 GPU 运行")
    free, total = torch.cuda.mem_get_info()
    if free / 2**30 < args.gpu_need_gib:
        raise SystemExit(f"可用显存低于启动门槛 {args.gpu_need_gib:.1f} GiB")
    log(f"GPU 总显存 {total / 2**30:.2f} GiB，当前可用 {free / 2**30:.2f} GiB")
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

    tracking = parent["tracking"]
    swanlab.init(
        workspace=tracking["workspace"],
        project=tracking["project"],
        name=RUN_ID,
        config={
            "parent_run_id": PARENT_RUN_ID,
            "parent_eval_run_id": CONTINUATION_RUN_ID,
            "seed": 42,
            "screening_only": True,
            "formal_paper_evidence": False,
            "source_year_retrained": False,
            "target_score_calls": 2,
            "script_sha256": script_sha,
        },
        mode=tracking["mode"],
        logdir=str(args.out / "swanlog"),
    )

    log("阶段一：读取 LSPR24 缓存并重建实体身份")
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
        [
            a + "|" + b if a <= b else b + "|" + a
            for a, b in zip(source_address, destination_address, strict=True)
        ],
        object,
    )
    _, entity = np.unique(entity_key, return_inverse=True)
    n_entity = int(entity.max()) + 1
    entity_labels = np.zeros(n_entity, np.float32)
    np.maximum.at(entity_labels, entity, y24)
    flow_counts = np.bincount(entity, minlength=n_entity).astype(np.int64, copy=False)
    if n_entity != N_ENT_24_EXPECT or int(entity_labels.sum()) != N_POS_ENT_24_EXPECT:
        raise SystemExit(
            f"LSPR24 实体统计不符：实体={n_entity:,}，正实体={int(entity_labels.sum()):,}"
        )
    del entity_key, source_address, destination_address

    log("阶段二：仅在内存重建 raw83/semantic168")
    # 数据身份：X24 是 dijk 复现管线标准化后的特征矩阵（非有限值置 0 → 按 LSPR23 逐列均值和标准差
    # 标准化 → 裁剪 [-10, 10]），不是 raw83 原值；"raw83" 在这里只表示前 83 列。冻结 XGBoost 与它
    # 同源，故可直接读；按 raw83 拟合的模型不得读它。见该缓存目录的 README.md。
    semantic = build_semantic_matrix(
        CACHE / "X24.npy", indices, mask, args.predict_batch, args.sequence_batch
    )
    del indices, mask

    log("阶段三：两份冻结模型各预测一次")
    flow_scores: dict[str, np.ndarray] = {}
    prediction_ledger: list[dict[str, Any]] = []
    for call, view in enumerate(("raw83", "semantic168"), start=1):
        gpu_guard(torch, args.gpu_floor_gib, f"{view}/推理前")
        matrix = semantic[:, :D_RAW] if view == "raw83" else semantic
        flow_scores[view] = predict_rows(models[view], matrix, args.predict_batch, view)
        prediction_ledger.append({"call": call, "view": view, "n_flow": N_FLOW_24})
        torch.cuda.empty_cache()
    del semantic, models

    log("阶段四：复用两路分数生成冻结四格并计算五档聚合统计")
    cell_scores = {
        cell_name: ent_scores(flow_scores[view], entity, n_entity, p_value)
        for cell_name, view, p_value in CELL_SPECS
    }
    del flow_scores
    buckets = summarize_buckets(flow_counts, entity_labels, cell_scores)
    verdict = mechanical_verdict(buckets)

    result = {
        "schema_version": "ch4-xgb-long-entity-bucket-diagnostic-v1",
        "run_id": RUN_ID,
        "seed": 42,
        "screening_only": True,
        "formal_paper_evidence": False,
        "independent_test": False,
        "script_sha256": script_sha,
        "parent": {
            "run_id": PARENT_RUN_ID,
            "eval_run_id": CONTINUATION_RUN_ID,
            "parent_artifact_sha256": parent["artifact_sha256"],
            "parent_eval_sha256": parent["parent_eval_sha256"],
            "selected_adapter": parent["selected_adapter"],
            "p_selection": parent["p_selection"],
            "models": model_receipts,
        },
        "protocol": {
            "source_year_retrained": False,
            "target_year_rebuilt_in_memory": True,
            "target_labels_used_for_parameter_selection": False,
            "target_score_calls": 2,
            "prediction_ledger": prediction_ledger,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "derived_matrices_persisted": False,
            "new_models_persisted": False,
            "bucket_boundaries_selected_before_diagnostic": True,
        },
        "xgboost": {
            "version": xgb.__version__,
            "num_boost_round": 800,
            "params": EXPECTED_XGB_PARAMS,
        },
        "lspr24": {
            "n_flow": N_FLOW_24,
            "n_entity": n_entity,
            "n_positive_entity": int(entity_labels.sum()),
            "n_negative_entity": int(n_entity - entity_labels.sum()),
        },
        "cells": {
            name: {
                "input_view": view,
                "p": p_value,
                "aggregation": "max" if p_value is None else "power_mean",
            }
            for name, view, p_value in CELL_SPECS
        },
        "buckets": buckets,
        "mechanical_verdict": verdict,
        "timing": {"total_seconds": time.time() - T0},
    }

    metric_payload: dict[str, int | float] = {}
    for bucket_name, bucket in buckets.items():
        metric_prefix = f"bucket/{bucket_name}"
        metric_payload[f"{metric_prefix}/n_entity"] = bucket["n_entity"]
        metric_payload[f"{metric_prefix}/n_positive_entity"] = bucket["n_positive_entity"]
        for cell_name in ("raw_max", "raw_elp", "semantic_max", "semantic_elp"):
            value = bucket["cells"][cell_name]["entity_ap"]
            if value is not None:
                metric_payload[f"{metric_prefix}/{cell_name}_entity_ap"] = value
        delta = bucket["contrasts"]["semantic_elp_minus_raw_max"]
        if delta is not None:
            metric_payload[f"{metric_prefix}/semantic_elp_minus_raw_max"] = delta
        for threshold_key, count in bucket["cells"]["semantic_elp"][
            "benign_high_score_count"
        ].items():
            metric_payload[f"{metric_prefix}/semantic_elp_benign_{threshold_key}"] = count
    metric_payload["runtime/total_seconds"] = result["timing"]["total_seconds"]
    swanlab.log(metric_payload, step=0)
    swanlab.finish()

    swanlab_receipt = {
        "schema_version": "aggregate-swanlab-receipt-v1",
        "completed": True,
        "workspace": tracking["workspace"],
        "project": tracking["project"],
        "mode": tracking["mode"],
        "aggregate_only": True,
        "metric_keys": sorted(metric_payload),
    }
    atomic_json(args.out / "swanlab-receipt.json", swanlab_receipt)
    result["tracking"] = swanlab_receipt
    result_path = args.out / "xgb_long_entity_bucket_results.json"
    atomic_json(result_path, result)

    manifest_names = (
        "resource-receipt.json",
        "swanlab-receipt.json",
        "xgb_long_entity_bucket_results.json",
    )
    manifest = {
        "schema_version": "ch4-xgb-long-entity-bucket-manifest-v1",
        "run_id": RUN_ID,
        "script_sha256": script_sha,
        "screening_only": True,
        "formal_paper_evidence": False,
        "per_sample_artifacts_persisted": False,
        "files": {},
    }
    for name in manifest_names:
        path = args.out / name
        if not path.is_file():
            raise SystemExit(f"必需聚合制品缺失：{path}")
        manifest["files"][name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(args.out / "manifest.json", manifest)
    log(f"机械裁决：{verdict['decision']}")
    log(f"聚合结果已保存：{result_path}")


if __name__ == "__main__":
    main()
