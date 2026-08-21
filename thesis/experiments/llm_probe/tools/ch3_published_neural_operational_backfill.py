#!/usr/bin/env python3
"""用已持久化分数回填三种已发表神经基线的目标年运营指标。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import sys
import time
import traceback
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "ch3-published-neural-operational-backfill-v1"
DISPLAY_NAME = "已发表神经基线目标年完整运营指标零训练回填"
FPR_BUDGETS = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)
FIRST_ALERT_QUANTILES = (0.25, 0.5, 0.75, 0.9, 0.95)
N_FLOW = 20_227_356
N_ENTITY = 47_115
N_POSITIVE_ENTITY = 752
MODEL_CONTRACTS = {
    "transformer": {
        "display_name": "全注意力Transformer",
        "relative_path": "runs/diagnostics/ch3-baselines-full/scores_transformer_dijk2026.npy",
        "bytes": 80_909_552,
        "sha256": "4bb845444a03cea0579c28120f2afe2d48559c8644c6a8fc80ddd37b5e63922d",
        "flow_average_precision": 0.325725660495,
        "max_pool_entity_average_precision": 0.353619988596,
        "dr_at_4_percent_fpr": 0.740691489362,
    },
    "cnn": {
        "display_name": "一维CNN",
        "relative_path": "runs/diagnostics/ch3-baselines-full/scores_cnn_leoste2025.npy",
        "bytes": 80_909_552,
        "sha256": "3d3674d98799140b9dadaa580c481986bd579acad6455dae79948adcb1a0749d",
        "flow_average_precision": 0.127082755846,
        "max_pool_entity_average_precision": 0.409638921562,
        "dr_at_4_percent_fpr": 0.648936170213,
    },
    "gru": {
        "display_name": "GRU",
        "relative_path": "runs/diagnostics/ch3-baselines-full/scores_gru_dijk2026.npy",
        "bytes": 80_909_552,
        "sha256": "8e75dcc7b787a4ed3d5c5f2fc250b3b2b20de083c6a5826ef9108d80f9b80ad2",
        "flow_average_precision": 0.287728740908,
        "max_pool_entity_average_precision": 0.159955930349,
        "dr_at_4_percent_fpr": 0.308510638298,
    },
}
SHARED_INPUTS = {
    "flow_labels": {
        "relative_path": "runs/diagnostics/dijk-repro/cache/y24.npy",
        "dtype": "float32",
        "shape": [N_FLOW],
        "sha256": "455a4932e0483af59ebccc64b462d3c620f671c6969f15312d8358cf7f410b46",
    },
    "source_addresses": {
        "relative_path": "runs/diagnostics/dijk-repro/cache/s24.npy",
        "bytes": 494_808_757,
        "sha256": "bdae8476d927d2f6610335649c01e8db71ee48a375bd48f9c13bb7b968d25243",
    },
    "destination_addresses": {
        "relative_path": "runs/diagnostics/dijk-repro/cache/d24.npy",
        "bytes": 495_445_716,
        "sha256": "a3621eaf4d683aac2f6f70ce2c2ad71d769b26fca6bfd981bb98ec81398f21cb",
    },
}
PRE_MANIFEST_FILES = (
    "aggregate-results.json",
    "complete-alert-budget-curves.npz",
    "complete-alert-budget-curves-receipt.json",
    "first-alert-timing-curves.npz",
    "first-alert-timing-receipt.json",
    "resource-receipt.json",
    "input-receipt.json",
)
FINAL_FILES = (*PRE_MANIFEST_FILES, "status.json", "run.log")
FORBIDDEN_ARTIFACTS = (
    "flow-scores.npy",
    "entity-scores.npy",
    "first-alert-per-entity.npy",
    "per-flow-scores.npz",
    "per-entity-scores.npz",
    "per-entity-first-alert.npz",
)
STARTED_AT = time.time()
np: Any = None


def load_numeric_dependencies() -> None:
    """静态入口不依赖数值环境，正式计算时才加载 NumPy。"""
    global np
    if np is not None:
        return
    import numpy as numpy_module

    np = numpy_module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT
        / "configs/ch3-published-neural-operational-backfill-v1.json",
        help="冻结配置路径",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="输入与输出路径的显式项目根，仅计算或最终发布时使用",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-config", action="store_true", help="只核验冻结配置")
    mode.add_argument("--compute", action="store_true", help="计算并原子写出聚合制品")
    mode.add_argument("--finalize", action="store_true", help="核验日志后原子发布最终清单")
    parser.add_argument("--resume", action="store_true", help="幂等核验并跳过已完成阶段")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    return artifact_receipt(path)


def artifact_receipt(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"制品缺失或为空：{path}")
    return {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_status(
    output_root: Path,
    state: str,
    stage: str,
    detail: str,
    exit_code: int | None,
) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-published-neural-operational-backfill-status-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "state": state,
            "stage": stage,
            "detail": detail,
            "exit_code": exit_code,
            "updated_at_unix": time.time(),
            "training_runs": 0,
            "inference_runs": 0,
            "gpu_array_reads": 0,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
        },
    )


def validate_config(config: Mapping[str, Any]) -> None:
    expected_top = {
        "schema_version": "ch3-published-neural-operational-backfill-config-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "dataset": "LSPR24",
        "model_scope": "published_neural_performance_envelope",
        "target_previously_accessed": True,
        "independent_test": False,
        "training_runs": 0,
        "inference_runs": 0,
    }
    for key, expected in expected_top.items():
        if config.get(key) != expected:
            raise SystemExit(f"配置字段不符：{key}")
    if config.get("models") != MODEL_CONTRACTS:
        raise SystemExit("三模型分数身份或历史锚点不符")
    if config.get("shared_inputs") != SHARED_INPUTS:
        raise SystemExit("共享标签与端点输入身份不符")
    if config.get("expected_metrics") != {
        "flow_count": N_FLOW,
        "entity_count": N_ENTITY,
        "positive_entity_count": N_POSITIVE_ENTITY,
        "decimal_places_for_reproduction_gate": 12,
    }:
        raise SystemExit("历史指标机械复现合同不符")
    if config.get("evaluation") != {
        "entity_aggregation": "maximum_flow_score",
        "entity_label": "maximum_flow_label",
        "threshold_semantics": "score_greater_equal_threshold",
        "complete_curve": "all_complete_entity_score_tie_groups",
        "nominal_fpr_budgets": list(FPR_BUDGETS),
        "budget_readout": "last_reachable_complete_tie_group_not_exceeding_budget",
        "next_point": "immediately_following_complete_tie_group",
        "interpolation": False,
        "exposure_order": "ascending_frozen_flow_array_index_within_entity",
        "exposure_index_base": 1,
        "first_alert_quantiles": list(FIRST_ALERT_QUANTILES),
        "timely_detection_denominator": N_POSITIVE_ENTITY,
        "time_delay_available": False,
    }:
        raise SystemExit("完整曲线或首次告警评价合同不符")
    if config.get("resource_contract") != {
        "authorized_server": "B76",
        "device": "cpu",
        "gpu_count": 0,
        "gpu_array_reads": 0,
        "peak_gpu_memory_mib": 0,
        "estimated_peak_process_memory_gib": 4,
        "estimated_cpu_wall_time": "less_than_2_minutes",
        "estimated_input_read_gib": 1.32,
        "estimated_output_mib_upper_bound": 6,
        "minimum_free_disk_gib": 10,
        "allow_parallel_with_grande_only_after_live_gates": True,
        "wall_clock_limit": None,
    }:
        raise SystemExit("CPU、资源或并发合同不符")
    if config.get("artifact_policy") != {
        "output_root": "runs/diagnostics/ch3-published-neural-operational-backfill-v1",
        "atomic_json_and_npz": True,
        "persist_aggregate_results": True,
        "persist_complete_alert_budget_curve": True,
        "persist_first_alert_timing_curve": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_per_entity_first_alert": False,
        "persist_models_or_checkpoints": False,
    }:
        raise SystemExit("原子制品或禁止持久化合同不符")


def resolve_within(project_root: Path, relative_path: str) -> Path:
    if Path(relative_path).is_absolute():
        raise SystemExit(f"配置路径必须相对项目根：{relative_path}")
    resolved = (project_root / relative_path).resolve()
    try:
        resolved.relative_to(project_root)
    except ValueError as error:
        raise SystemExit(f"配置路径越出项目根：{relative_path}") from error
    return resolved


def resolve_runtime_paths(
    config: Mapping[str, Any], project_root_arg: Path | None
) -> tuple[Path, Path, dict[str, Path]]:
    if project_root_arg is None:
        raise SystemExit("计算与最终发布必须显式传入 --project-root")
    project_root = project_root_arg.resolve()
    if project_root.name != "llm_probe" or not (project_root / "pyproject.toml").is_file():
        raise SystemExit("显式项目根不是 llm_probe 生产根")
    output_root = resolve_within(
        project_root, str(config["artifact_policy"]["output_root"])
    )
    if output_root.name != RUN_ID:
        raise SystemExit("输出目录与运行身份不一致")
    inputs = {
        **{
            model_key: resolve_within(project_root, str(contract["relative_path"]))
            for model_key, contract in MODEL_CONTRACTS.items()
        },
        **{
            name: resolve_within(project_root, str(contract["relative_path"]))
            for name, contract in SHARED_INPUTS.items()
        },
    }
    return project_root, output_root, inputs


def rounded_metric_matches(actual: float, expected: float) -> bool:
    return f"{actual:.12f}" == f"{expected:.12f}"


def average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    binary = labels.astype(np.int8, copy=False)
    positive_count = int(binary.sum())
    if positive_count <= 0 or positive_count >= len(binary):
        raise SystemExit("平均精度需要同时存在正负样本")
    order = np.argsort(scores, kind="stable")[::-1]
    ordered_scores = scores[order]
    ordered_labels = binary[order]
    distinct_ends = np.flatnonzero(ordered_scores[1:] != ordered_scores[:-1])
    threshold_ends = np.r_[distinct_ends, len(ordered_scores) - 1]
    true_positive = np.cumsum(ordered_labels, dtype=np.int64)[threshold_ends]
    predicted_positive = threshold_ends.astype(np.int64) + 1
    precision = true_positive.astype(np.float64) / predicted_positive
    recall = true_positive.astype(np.float64) / positive_count
    recall_increment = np.diff(np.r_[0.0, recall])
    return float(np.sum(recall_increment * precision, dtype=np.float64))


def validate_file_identity(
    name: str,
    path: Path,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise SystemExit(f"冻结输入缺失或为空：{path}")
    if "bytes" in contract and path.stat().st_size != contract["bytes"]:
        raise SystemExit(f"冻结输入字节数不符：{name}")
    actual_hash = sha256_file(path)
    if actual_hash != contract["sha256"]:
        raise SystemExit(f"冻结输入摘要不符：{name}")
    return {
        "relative_path": contract["relative_path"],
        "bytes": path.stat().st_size,
        "sha256": actual_hash,
    }


def validate_and_load_shared_inputs(
    config_path: Path,
    inputs: Mapping[str, Path],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    file_receipts: dict[str, Any] = {}
    for model_key, contract in MODEL_CONTRACTS.items():
        receipt = validate_file_identity(model_key, inputs[model_key], contract)
        score_header = np.load(inputs[model_key], mmap_mode="r", allow_pickle=False)
        if score_header.shape != (N_FLOW,) or score_header.dtype != np.dtype("float32"):
            raise SystemExit(f"{model_key} 冻结分数形状或类型不符")
        receipt.update({"shape": [N_FLOW], "dtype": "float32"})
        file_receipts[model_key] = receipt
        del score_header

    for name, contract in SHARED_INPUTS.items():
        file_receipts[name] = validate_file_identity(name, inputs[name], contract)
    labels_float = np.load(inputs["flow_labels"], mmap_mode="r", allow_pickle=False)
    if (
        labels_float.shape != (N_FLOW,)
        or labels_float.dtype != np.dtype("float32")
        or not np.isfinite(labels_float).all()
        or not np.logical_or(labels_float == 0.0, labels_float == 1.0).all()
    ):
        raise SystemExit("冻结逐流标签形状、类型或二元值不符")
    file_receipts["flow_labels"].update({"shape": [N_FLOW], "dtype": "float32"})
    labels = np.asarray(labels_float).astype(np.int8, copy=False)

    source = np.load(inputs["source_addresses"], allow_pickle=True)
    destination = np.load(inputs["destination_addresses"], allow_pickle=True)
    if source.shape != (N_FLOW,) or destination.shape != (N_FLOW,):
        raise SystemExit("冻结源端或目的端地址数组形状不符")
    file_receipts["source_addresses"].update(
        {"shape": [N_FLOW], "dtype": str(source.dtype)}
    )
    file_receipts["destination_addresses"].update(
        {"shape": [N_FLOW], "dtype": str(destination.dtype)}
    )
    entity_keys = np.fromiter(
        (
            f"{left}|{right}" if left <= right else f"{right}|{left}"
            for left, right in zip(source, destination, strict=True)
        ),
        dtype=object,
        count=N_FLOW,
    )
    del source, destination
    _, entity = np.unique(entity_keys, return_inverse=True)
    del entity_keys
    entity = entity.astype(np.int32, copy=False)
    if int(entity.min()) != 0 or int(entity.max()) != N_ENTITY - 1:
        raise SystemExit("内存构造的无向端点实体编号边界不符")
    entity_counts = np.bincount(entity, minlength=N_ENTITY)
    if len(entity_counts) != N_ENTITY or np.any(entity_counts <= 0):
        raise SystemExit("内存构造的实体编号不连续或存在零曝光实体")
    entity_labels = np.zeros(N_ENTITY, dtype=np.int8)
    np.maximum.at(entity_labels, entity, labels)
    if int(entity_labels.sum()) != N_POSITIVE_ENTITY:
        raise SystemExit("冻结正实体数不符")

    receipt = {
        "schema_version": "ch3-published-neural-operational-backfill-input-v1",
        "run_id": RUN_ID,
        "files": file_receipts,
        "tool_sha256": sha256_file(Path(__file__).resolve()),
        "config_sha256": sha256_file(config_path),
        "flow_count": N_FLOW,
        "entity_count": N_ENTITY,
        "positive_entity_count": int(entity_labels.sum()),
        "negative_entity_count": int((entity_labels == 0).sum()),
        "entity_construction": "lexically_factorized_unordered_source_destination_pair",
        "entity_mapping_persisted": False,
        "metric_reproduction_decimal_places": 12,
        "model_reproduction": {},
        "all_reproduction_gates_passed": False,
        "model_loaded": False,
        "training_runs": 0,
        "inference_runs": 0,
        "score_fusion_performed": False,
    }
    return entity, labels, entity_labels, entity_counts, receipt


def complete_tied_curve(
    entity_scores: np.ndarray, entity_labels: np.ndarray
) -> dict[str, np.ndarray]:
    order = np.argsort(entity_scores, kind="stable")[::-1]
    scores = entity_scores[order].astype(np.float64)
    labels = entity_labels[order].astype(np.int8, copy=False)
    starts = np.r_[0, np.flatnonzero(scores[1:] != scores[:-1]) + 1]
    ends = np.r_[starts[1:], len(scores)]
    group_size = (ends - starts).astype(np.int64)
    group_positive = np.add.reduceat(labels.astype(np.int64), starts)
    group_negative = group_size - group_positive
    threshold = scores[starts]

    threshold = np.r_[np.nextafter(threshold[0], math.inf), threshold]
    group_size = np.r_[0, group_size].astype(np.int64)
    group_positive = np.r_[0, group_positive].astype(np.int64)
    group_negative = np.r_[0, group_negative].astype(np.int64)
    cumulative_tp = np.cumsum(group_positive, dtype=np.int64)
    cumulative_fp = np.cumsum(group_negative, dtype=np.int64)
    positive_denominator = int((entity_labels == 1).sum())
    negative_denominator = int((entity_labels == 0).sum())
    return {
        "threshold": threshold.astype(np.float64),
        "threshold_tie_group_size": group_size,
        "tie_group_positive_entity_count": group_positive,
        "tie_group_negative_entity_count": group_negative,
        "true_positive_entity_count": cumulative_tp,
        "false_positive_entity_count": cumulative_fp,
        "actual_fpr": cumulative_fp.astype(np.float64) / negative_denominator,
        "detection_rate": cumulative_tp.astype(np.float64) / positive_denominator,
    }


def curve_point(
    curve: Mapping[str, np.ndarray], index: int, negative_denominator: int
) -> dict[str, Any]:
    return {
        "curve_index": index,
        "threshold": float(curve["threshold"][index]),
        "threshold_semantics": "score_greater_equal_threshold",
        "threshold_tie_group_size": int(curve["threshold_tie_group_size"][index]),
        "tie_group_positive_entity_count": int(
            curve["tie_group_positive_entity_count"][index]
        ),
        "tie_group_negative_entity_count": int(
            curve["tie_group_negative_entity_count"][index]
        ),
        "true_positive_entity_count": int(curve["true_positive_entity_count"][index]),
        "false_positive_entity_count": int(
            curve["false_positive_entity_count"][index]
        ),
        "negative_entity_denominator": negative_denominator,
        "actual_reachable_fpr": float(curve["actual_fpr"][index]),
        "detection_rate": float(curve["detection_rate"][index]),
        "interpolated": False,
    }


def budget_readouts(
    curve: Mapping[str, np.ndarray], negative_denominator: int
) -> dict[str, dict[str, Any]]:
    actual = curve["actual_fpr"]
    readouts: dict[str, dict[str, Any]] = {}
    for budget in FPR_BUDGETS:
        index = int(np.searchsorted(actual, budget, side="right") - 1)
        if index < 0:
            raise RuntimeError("完整曲线缺少零误报边界")
        feasible_detection = curve["detection_rate"][: index + 1]
        if float(curve["detection_rate"][index]) != float(feasible_detection.max()):
            raise RuntimeError("预算内最后可达点未达到预算内最高检测率")
        best = curve_point(curve, index, negative_denominator)
        next_point = (
            curve_point(curve, index + 1, negative_denominator)
            if index + 1 < len(actual)
            else None
        )
        key = f"fpr_{budget:g}"
        readouts[key] = {
            "nominal_target_fpr": budget,
            "actual_reachable_fpr": best["actual_reachable_fpr"],
            "detection_rate": best["detection_rate"],
            "false_positive_entity_count": best["false_positive_entity_count"],
            "negative_entity_denominator": negative_denominator,
            "threshold": best["threshold"],
            "threshold_tie_group_size": best["threshold_tie_group_size"],
            "best_reachable_point": best,
            "next_reachable_point": next_point,
            "next_point_exceeds_nominal_budget": (
                None
                if next_point is None
                else next_point["actual_reachable_fpr"] > budget
            ),
            "selection_rule": "last_complete_tie_group_at_or_below_nominal_budget",
        }
    return readouts


def prepare_entity_exposure(
    entity: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    order = np.argsort(entity, kind="stable")
    ordered_entity = entity[order]
    starts = np.r_[0, np.flatnonzero(ordered_entity[1:] != ordered_entity[:-1]) + 1]
    lengths = np.diff(np.r_[starts, len(ordered_entity)]).astype(np.int64)
    if not np.array_equal(ordered_entity[starts], np.arange(N_ENTITY, dtype=np.int32)):
        raise SystemExit("实体稳定排序未覆盖连续冻结实体编号")
    exposure_index = (
        np.arange(len(ordered_entity), dtype=np.int64)
        - np.repeat(starts, lengths)
        + 1
    )
    return order, starts, exposure_index


def first_alert_metrics(
    scores: np.ndarray,
    entity_labels: np.ndarray,
    entity_counts: np.ndarray,
    entity_order: np.ndarray,
    entity_starts: np.ndarray,
    exposure_index: np.ndarray,
    readouts: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    ordered_scores = scores[entity_order]
    positive = entity_labels == 1
    negative = entity_labels == 0
    negative_count = int(negative.sum())
    summaries: dict[str, Any] = {}
    vectors: dict[str, np.ndarray] = {}

    for key, readout in readouts.items():
        threshold = float(readout["threshold"])
        candidate = np.where(
            ordered_scores >= threshold,
            exposure_index,
            np.iinfo(np.int64).max,
        )
        first_alert = np.minimum.reduceat(candidate, entity_starts)
        first_alert[first_alert == np.iinfo(np.int64).max] = 0
        del candidate

        alerted_positive = positive & (first_alert > 0)
        alerted_negative = negative & (first_alert > 0)
        positive_positions = first_alert[alerted_positive]
        if len(positive_positions):
            axis, counts = np.unique(positive_positions, return_counts=True)
            rate = np.cumsum(counts, dtype=np.int64).astype(np.float64) / N_POSITIVE_ENTITY
            quantiles = np.quantile(
                positive_positions.astype(np.float64),
                FIRST_ALERT_QUANTILES,
                method="linear",
            )
            quantile_summary = {
                "q25": float(quantiles[0]),
                "q50": float(quantiles[1]),
                "q75": float(quantiles[2]),
                "q90": float(quantiles[3]),
                "q95": float(quantiles[4]),
            }
        else:
            axis = np.array([], dtype=np.int64)
            rate = np.array([], dtype=np.float64)
            quantile_summary = {name: None for name in ("q25", "q50", "q75", "q90", "q95")}

        realized_first_alert_fpr = float(alerted_negative.sum() / negative_count)
        if int(alerted_negative.sum()) != int(readout["false_positive_entity_count"]):
            raise SystemExit(f"{key} 首次告警负实体数与终端最大池化曲线不一致")
        summaries[key] = {
            "nominal_target_fpr": float(readout["nominal_target_fpr"]),
            "threshold": threshold,
            "threshold_semantics": "flow_score_greater_equal_threshold",
            "exposure_index_base": 1,
            "positive_entity_denominator": N_POSITIVE_ENTITY,
            "alerted_positive_entity_count": int(alerted_positive.sum()),
            "never_alerted_positive_entity_count": int((positive & (first_alert == 0)).sum()),
            "positive_unalerted_rate": float((positive & (first_alert == 0)).sum() / N_POSITIVE_ENTITY),
            "negative_entity_denominator": negative_count,
            "alerted_negative_entity_count": int(alerted_negative.sum()),
            "realized_first_alert_fpr": realized_first_alert_fpr,
            "terminal_actual_reachable_fpr": float(readout["actual_reachable_fpr"]),
            "malicious_first_alert_exposure_quantiles": quantile_summary,
            "maximum_positive_entity_exposure_count": int(entity_counts[positive].max()),
            "timely_curve_point_count": int(len(axis)),
        }
        vectors[f"{key}__exposure_index"] = axis.astype(np.int64, copy=False)
        vectors[f"{key}__timely_detection_rate"] = rate

    return (
        {
            "axis": "exposure_index",
            "exposure_index_base": 1,
            "curve_encoding": "right_continuous_exact_alert_breakpoints",
            "timely_detection_denominator": N_POSITIVE_ENTITY,
            "time_delay_available": False,
            "all_negative_entities_scanned_per_budget": True,
            "budgets": summaries,
            "persisted_per_flow_scores": False,
            "persisted_per_entity_scores": False,
            "persisted_per_entity_first_alert": False,
        },
        vectors,
    )


def process_peak_rss_mib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def read_cgroup_number(name: str) -> int | None:
    v1_name = {
        "memory.current": "memory.usage_in_bytes",
        "memory.peak": "memory.max_usage_in_bytes",
    }.get(name, name)
    candidates = (Path("/sys/fs/cgroup") / name, Path("/sys/fs/cgroup/memory") / v1_name)
    for path in candidates:
        if path.is_file():
            value = path.read_text(encoding="utf-8").strip()
            if value.isdigit():
                return int(value)
    return None


def verify_receipted_artifact(output_root: Path, receipt_name: str) -> None:
    receipt = load_json(output_root / receipt_name)
    item = receipt.get("artifact", {})
    artifact = output_root / str(item.get("filename", ""))
    if (
        not artifact.is_file()
        or artifact.stat().st_size != item.get("bytes")
        or sha256_file(artifact) != item.get("sha256")
    ):
        raise SystemExit(f"NPZ 制品与收据不符：{receipt_name}")


def verify_compute_outputs(
    output_root: Path, config_path: Path, require_computed_status: bool = True
) -> None:
    for name in PRE_MANIFEST_FILES:
        if not (output_root / name).is_file() or (output_root / name).stat().st_size <= 0:
            raise SystemExit(f"计算阶段制品缺失或为空：{name}")
    verify_receipted_artifact(output_root, "complete-alert-budget-curves-receipt.json")
    verify_receipted_artifact(output_root, "first-alert-timing-receipt.json")
    aggregate = load_json(output_root / "aggregate-results.json")
    input_receipt = load_json(output_root / "input-receipt.json")
    resource_receipt = load_json(output_root / "resource-receipt.json")
    if (
        aggregate.get("run_id") != RUN_ID
        or aggregate.get("complete") is not True
        or aggregate.get("model_count") != len(MODEL_CONTRACTS)
        or set(aggregate.get("models", {})) != set(MODEL_CONTRACTS)
        or aggregate.get("score_fusion_performed") is not False
        or aggregate.get("training_runs") != 0
        or aggregate.get("inference_runs") != 0
        or input_receipt.get("run_id") != RUN_ID
        or input_receipt.get("tool_sha256") != sha256_file(Path(__file__).resolve())
        or input_receipt.get("config_sha256") != sha256_file(config_path)
        or input_receipt.get("all_reproduction_gates_passed") is not True
        or set(input_receipt.get("model_reproduction", {})) != set(MODEL_CONTRACTS)
        or input_receipt.get("entity_mapping_persisted") is not False
        or input_receipt.get("score_fusion_performed") is not False
        or resource_receipt.get("run_id") != RUN_ID
        or resource_receipt.get("device") != "cpu"
        or resource_receipt.get("gpu_array_reads") != 0
        or resource_receipt.get("peak_gpu_memory_mib") != 0
    ):
        raise SystemExit("计算阶段身份、输入复现或 CPU 资源收据不符")
    if require_computed_status:
        status = load_json(output_root / "status.json")
        if status.get("state") != "computed" or status.get("stage") != "finalize_pending":
            raise SystemExit("计算阶段状态不是 computed/finalize_pending")


def validate_manifest(output_root: Path, config_path: Path) -> None:
    manifest = load_json(output_root / "manifest.json")
    if (
        manifest.get("schema_version")
        != "ch3-published-neural-operational-backfill-manifest-v1"
        or manifest.get("run_id") != RUN_ID
        or manifest.get("complete") is not True
        or manifest.get("model_count") != len(MODEL_CONTRACTS)
        or manifest.get("score_fusion_performed") is not False
        or manifest.get("entity_mapping_persisted") is not False
        or manifest.get("tool_sha256") != sha256_file(Path(__file__).resolve())
        or manifest.get("config_sha256") != sha256_file(config_path)
        or manifest.get("training_runs") != 0
        or manifest.get("inference_runs") != 0
        or manifest.get("gpu_array_reads") != 0
        or manifest.get("per_flow_scores_persisted") is not False
        or manifest.get("per_entity_scores_persisted") is not False
        or manifest.get("per_entity_first_alert_persisted") is not False
        or manifest.get("forbidden_artifacts_absent") is not True
        or set(manifest.get("files", {})) != set(FINAL_FILES)
    ):
        raise SystemExit("最终清单身份或零训练零分数持久化合同不符")
    for name, receipt in manifest["files"].items():
        path = output_root / name
        if (
            not path.is_file()
            or path.stat().st_size != receipt.get("bytes")
            or sha256_file(path) != receipt.get("sha256")
        ):
            raise SystemExit(f"最终制品与清单不符：{name}")


def compute(
    config: Mapping[str, Any],
    config_path: Path,
    project_root: Path,
    output_root: Path,
    inputs: Mapping[str, Path],
    resume: bool,
) -> None:
    load_numeric_dependencies()
    manifest_path = output_root / "manifest.json"
    if manifest_path.is_file():
        if not resume:
            raise SystemExit("运行已经完成；仅允许用 --resume 幂等核验")
        validate_manifest(output_root, config_path)
        print(f"RUN_ALREADY_COMPLETE run={RUN_ID}", flush=True)
        return
    output_root.mkdir(parents=True, exist_ok=True)
    status_path = output_root / "status.json"
    if status_path.is_file():
        prior = load_json(status_path)
        if prior.get("state") == "computed" and prior.get("stage") == "finalize_pending":
            if not resume:
                raise SystemExit("计算阶段已完成；仅允许用 --resume 幂等跳过")
            verify_compute_outputs(output_root, config_path)
            print(f"COMPUTE_ALREADY_COMPLETE run={RUN_ID}", flush=True)
            return
        if not resume:
            raise SystemExit("输出根已有未完成状态；必须显式使用 --resume")

    write_status(output_root, "running", "input_validation", "核验六个冻结数组并构造共享实体映射", None)
    entity, labels, entity_labels, entity_counts, input_receipt = (
        validate_and_load_shared_inputs(config_path, inputs)
    )
    negative_count = int((entity_labels == 0).sum())
    entity_order, entity_starts, exposure_index = prepare_entity_exposure(entity)
    curve_vectors: dict[str, np.ndarray] = {}
    first_alert_vectors: dict[str, np.ndarray] = {}
    curve_models: dict[str, Any] = {}
    first_alert_models: dict[str, Any] = {}
    model_results: dict[str, Any] = {}

    for model_key, contract in MODEL_CONTRACTS.items():
        write_status(
            output_root,
            "running",
            f"{model_key}_evaluation",
            f"独立计算 {contract['display_name']} 的完整并列组和首次告警",
            None,
        )
        scores = np.load(inputs[model_key], mmap_mode="r", allow_pickle=False)
        if not np.isfinite(scores).all() or float(scores.min()) < 0.0 or float(scores.max()) > 1.0:
            raise SystemExit(f"{model_key} 冻结分数含非有限值或越出概率范围")
        entity_scores = np.full(N_ENTITY, -math.inf, dtype=np.float32)
        np.maximum.at(entity_scores, entity, scores)
        if not np.isfinite(entity_scores).all():
            raise SystemExit(f"{model_key} 逐实体最大池化分数不完整")
        flow_ap = average_precision(labels, scores)
        entity_ap = average_precision(entity_labels, entity_scores)
        curve = complete_tied_curve(entity_scores, entity_labels)
        readouts = budget_readouts(curve, negative_count)
        dr_at_4 = float(readouts["fpr_0.04"]["detection_rate"])
        actual_metrics = {
            "flow_average_precision": flow_ap,
            "max_pool_entity_average_precision": entity_ap,
            "dr_at_4_percent_fpr": dr_at_4,
        }
        for metric_name, actual in actual_metrics.items():
            if not rounded_metric_matches(actual, float(contract[metric_name])):
                raise SystemExit(
                    f"{model_key} 历史锚点未机械复现：{metric_name}={actual:.15f}"
                )

        first_alert, model_first_vectors = first_alert_metrics(
            scores,
            entity_labels,
            entity_counts,
            entity_order,
            entity_starts,
            exposure_index,
            readouts,
        )
        curve_vectors.update(
            {f"{model_key}__{name}": values for name, values in curve.items()}
        )
        first_alert_vectors.update(
            {
                f"{model_key}__{name}": values
                for name, values in model_first_vectors.items()
            }
        )
        curve_models[model_key] = {
            "display_name": contract["display_name"],
            "fields": list(curve),
            "point_count": int(len(curve["threshold"])),
            "budget_readouts": readouts,
        }
        first_alert_models[model_key] = first_alert
        model_results[model_key] = {
            "display_name": contract["display_name"],
            **actual_metrics,
            "alert_budget_readouts": readouts,
            "first_alert": first_alert,
            "score_fusion_performed": False,
        }
        input_receipt["model_reproduction"][model_key] = {
            "expected": {
                metric_name: contract[metric_name] for metric_name in actual_metrics
            },
            "actual": actual_metrics,
            "passed": True,
        }
        del scores, entity_scores, curve, model_first_vectors

    input_receipt["all_reproduction_gates_passed"] = True
    atomic_json(output_root / "input-receipt.json", input_receipt)
    curve_artifact = atomic_npz(
        output_root / "complete-alert-budget-curves.npz", curve_vectors
    )
    curve_receipt = {
        "schema_version": "ch3-published-neural-complete-alert-budget-curves-v1",
        "run_id": RUN_ID,
        "artifact": curve_artifact,
        "model_count": len(MODEL_CONTRACTS),
        "models": curve_models,
        "entity_count": N_ENTITY,
        "positive_entity_count": N_POSITIVE_ENTITY,
        "negative_entity_count": negative_count,
        "zero_false_positive_boundary_included": True,
        "all_complete_entity_score_tie_groups_included": True,
        "threshold_semantics": "score_greater_equal_threshold",
        "interpolation": False,
        "score_fusion_performed": False,
    }
    atomic_json(output_root / "complete-alert-budget-curves-receipt.json", curve_receipt)
    first_alert_artifact = atomic_npz(
        output_root / "first-alert-timing-curves.npz", first_alert_vectors
    )
    first_alert_receipt = {
        "schema_version": "ch3-published-neural-first-alert-timing-v1",
        "run_id": RUN_ID,
        "artifact": first_alert_artifact,
        "model_count": len(MODEL_CONTRACTS),
        "models": first_alert_models,
        "score_fusion_performed": False,
        "shared_entity_mapping": True,
        "entity_mapping_persisted": False,
    }
    atomic_json(output_root / "first-alert-timing-receipt.json", first_alert_receipt)

    resource_receipt = {
        "schema_version": "ch3-published-neural-operational-backfill-resource-v1",
        "run_id": RUN_ID,
        "authorized_server": config["resource_contract"]["authorized_server"],
        "hostname": platform.node(),
        "device": "cpu",
        "gpu_count": 0,
        "gpu_array_reads": 0,
        "peak_gpu_memory_mib": 0,
        "process_peak_rss_mib": process_peak_rss_mib(),
        "cgroup_current_bytes_at_receipt": read_cgroup_number("memory.current"),
        "cgroup_peak_bytes_at_receipt": read_cgroup_number("memory.peak"),
        "disk_free_bytes_at_receipt": shutil.disk_usage(project_root).free,
        "compute_wall_seconds": time.time() - STARTED_AT,
        "wall_clock_limit": None,
        "estimated_peak_process_memory_gib": 4,
        "estimated_input_read_gib": 1.32,
        "estimated_output_mib_upper_bound": 6,
        "measurement_note": "进程峰值主存为本次进程读数；控制组读数可能包含并发任务",
    }
    atomic_json(output_root / "resource-receipt.json", resource_receipt)

    aggregate = {
        "schema_version": "ch3-published-neural-operational-backfill-results-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "complete": True,
        "dataset": "LSPR24",
        "evaluation_role": "已访问目标年的描述性运营指标回填",
        "model_scope": config["model_scope"],
        "models": model_results,
        "model_count": len(MODEL_CONTRACTS),
        "score_fusion_performed": False,
        "resource": resource_receipt,
        "training_runs": 0,
        "inference_runs": 0,
        "model_loaded": False,
        "target_used_for_selection_or_tuning": False,
        "time_delay_available": False,
        "artifact_policy": config["artifact_policy"],
        "isolation": {
            "input_arrays_read": [
                *[contract["relative_path"] for contract in MODEL_CONTRACTS.values()],
                *[contract["relative_path"] for contract in SHARED_INPUTS.values()],
            ],
            "shared_entity_mapping_constructed_in_memory": True,
            "entity_mapping_persisted": False,
            "gpu_array_reads": 0,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
        },
    }
    atomic_json(output_root / "aggregate-results.json", aggregate)
    write_status(output_root, "computed", "finalize_pending", "聚合制品已完成，等待日志封口与清单发布", 0)
    verify_compute_outputs(output_root, config_path)
    print(f"COMPUTE_COMPLETE run={RUN_ID}", flush=True)


def finalize(
    config_path: Path,
    output_root: Path,
    resume: bool,
) -> None:
    manifest_path = output_root / "manifest.json"
    if manifest_path.is_file():
        if not resume:
            raise SystemExit("最终清单已存在；仅允许用 --resume 幂等核验")
        validate_manifest(output_root, config_path)
        return
    verify_compute_outputs(output_root, config_path)
    run_log = output_root / "run.log"
    if not run_log.is_file() or run_log.stat().st_size <= 0:
        raise SystemExit("run.log 尚未封口或为空，禁止发布最终清单")
    partials = list(output_root.glob("*.partial.*"))
    if partials:
        raise SystemExit("输出根存在未发布临时文件，拒绝宣称完成")
    forbidden_absent = all(
        not (output_root / name).exists() for name in FORBIDDEN_ARTIFACTS
    ) and not any(output_root.glob("*scores*"))
    if not forbidden_absent:
        raise SystemExit("发现禁止持久化的逐流、逐实体或首次告警明细")

    write_status(output_root, "finished", "complete", "全部聚合制品与清单已原子发布", 0)
    files = {name: artifact_receipt(output_root / name) for name in FINAL_FILES}
    manifest = {
        "schema_version": "ch3-published-neural-operational-backfill-manifest-v1",
        "run_id": RUN_ID,
        "display_name": DISPLAY_NAME,
        "complete": True,
        "model_count": len(MODEL_CONTRACTS),
        "score_fusion_performed": False,
        "entity_mapping_persisted": False,
        "tool_sha256": sha256_file(Path(__file__).resolve()),
        "config_sha256": sha256_file(config_path),
        "training_runs": 0,
        "inference_runs": 0,
        "gpu_array_reads": 0,
        "peak_gpu_memory_mib": 0,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
        "per_entity_first_alert_persisted": False,
        "forbidden_artifacts_absent": forbidden_absent,
        "files": files,
    }
    atomic_json(manifest_path, manifest)
    validate_manifest(output_root, config_path)


def main() -> int:
    args = parse_args()
    if not args.config.is_file():
        raise SystemExit(f"配置文件缺失：{args.config}")
    config_path = args.config.resolve()
    config = load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("CONFIG_VALID", flush=True)
        return 0

    project_root, output_root, inputs = resolve_runtime_paths(config, args.project_root)
    if args.compute:
        try:
            compute(config, config_path, project_root, output_root, inputs, args.resume)
        except BaseException as error:
            output_root.mkdir(parents=True, exist_ok=True)
            write_status(output_root, "failed", "compute", str(error), 1)
            traceback.print_exc()
            return 1
        return 0
    finalize(config_path, output_root, args.resume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
