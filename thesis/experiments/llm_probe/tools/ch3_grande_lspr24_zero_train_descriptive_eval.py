# -*- coding: utf-8 -*-
"""GRANDE G-A/G-B 封印检查点的 LSPR24 零重训练描述性评价。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch3_full_mlp_s0_precision_aggregation_diagnostic as shared_eval
import ch3_grande_protocol_a_source_q0 as grande


SCHEMA_VERSION = "ch3-grande-lspr24-zero-train-descriptive-eval-config-v1"
RESULT_SCHEMA_VERSION = "ch3-grande-lspr24-zero-train-descriptive-eval-results-v1"
UNIT_SCHEMA_VERSION = "ch3-grande-lspr24-zero-train-descriptive-eval-unit-v1"
RUN_ID = "ch3-grande-lspr24-zero-train-descriptive-eval-bf16-v1"
PARENT_RUN_ID = "ch3-grande-c00-protocolA-source-q0-seed42-v1-bf16-v1"
STRUCTURE_ORDER = ("G-A", "G-B")
TARGET_ARRAYS = ("X24", "y24", "s24", "d24")
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def process_peak_rss_mib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None, detail: str) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-grande-lspr24-zero-train-descriptive-eval-status-v1",
            "run_id": RUN_ID,
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "detail": detail,
            "updated_at_unix": time.time(),
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_used_for_selection": False,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GRANDE G-A/G-B LSPR24 零重训练描述性评价")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--validate-config", action="store_true", help="只核验配置")
    parser.add_argument("--resume", action="store_true", help="幂等复用已完成结构单元")
    parser.add_argument("--resource-receipt", help="启动器资源收据")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    if config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("目标年数组清单不符")
    if config.get("structures") != grande.expected_candidates():
        raise ValueError("G-A/G-B 结构不符父工具冻结值")
    parent = config.get("parent", {})
    if parent != {
        "run_id": PARENT_RUN_ID,
        "required_structures": list(STRUCTURE_ORDER),
        "source_gate_required": False,
        "source_gate_used_for_structure_selection": False,
        "precision_profile": grande.BF16_PRECISION_PROFILE,
        "target_year_arrays_read": 0,
    }:
        raise ValueError("父运行复用边界不符")
    if config.get("inference") != {
        "device": "cuda",
        "precision": "cuda_bf16_autocast",
        "parameters_fp32": True,
        "sigmoid_fp32": True,
        "feature_count": 83,
        "flow_batch_size": 2048,
        "one_forward_pass_per_structure": True,
    }:
        raise ValueError("推理合同不符")
    evaluation = config.get("evaluation", {})
    if evaluation != {
        "dataset": "LSPR24",
        "role": "previously_accessed_target_year_descriptive_evaluation",
        "entity_key": "unordered_source_destination_ip_pair_grouping_only",
        "entity_score": "maximum_flow_probability",
        "maximum_entity_score": "maximum_flow_probability",
        "dr_fpr_grid": list(grande.DR_FPR_GRID),
        "complete_negative_tie_group_curve": True,
        "first_alert_axis": "exposure_index",
        "first_alert_exposure_index_base": 1,
        "first_alert_order": "ascending_frozen_flow_index_within_entity",
        "first_alert_quantiles": [0.25, 0.5, 0.75, 0.9, 0.95],
    }:
        raise ValueError("描述性评价口径不符")
    if config.get("artifact_policy") != {
        "persist_unit_aggregate_json": True,
        "persist_complete_curve_npz": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_per_entity_first_alert": False,
        "persist_entity_mapping": False,
        "persist_exposure_matrix": False,
        "persist_new_checkpoints": False,
    }:
        raise ValueError("制品策略不符")
    if config.get("isolation") != {
        "training_runs": 0,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "new_checkpoints_written": 0,
        "target_array_load_passes": 1,
        "target_used_for_selection": False,
        "selection_performed": False,
        "winner": None,
    }:
        raise ValueError("零重训练与目标年隔离合同不符")
    evidence = config.get("evidence", {})
    if evidence != {
        "formal_paper_evidence": False,
        "independent_test": False,
        "target_previously_accessed": True,
        "target_metrics_used_for_selection_or_tuning": False,
    }:
        raise ValueError("证据身份不符")
    paths = config.get("paths", {})
    if Path(paths.get("output_root", "")).name != RUN_ID:
        raise ValueError("输出根与运行身份不符")
    if Path(paths.get("parent_run_root", "")).name != PARENT_RUN_ID:
        raise ValueError("父运行根身份不符")
    if config.get("resource_contract") != {
        "minimum_free_gpu_memory_gib": 12,
        "minimum_cgroup_available_memory_gib": 30,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_evaluations": 1,
        "wall_clock_limit": None,
    }:
        raise ValueError("资源合同不符")


def validate_parent(config: dict[str, Any]) -> dict[str, Any]:
    parent_root = Path(config["paths"]["parent_run_root"])
    parent_config_path = parent_root / "config.json"
    seal_path = parent_root / "backbone_selection_frozen.json"
    if not parent_config_path.is_file() or not seal_path.is_file():
        raise FileNotFoundError("父 GRANDE 配置或封印缺失")
    parent_config = load_json(parent_config_path)
    seal = load_json(seal_path)
    if parent_config.get("run_id") != PARENT_RUN_ID or seal.get("run_id") != PARENT_RUN_ID:
        raise RuntimeError("父 GRANDE 运行身份不符")
    if seal.get("target_year_arrays_read") != 0 or seal.get("target_entry_generated") is not False:
        raise RuntimeError("父运行目标年隔离或下游入口状态不符")
    completed = {item.get("unit_key"): item for item in seal.get("completed_structures", [])}
    receipts: dict[str, Any] = {}
    for structure in STRUCTURE_ORDER:
        receipt_path = parent_root / "receipts" / f"selection-{structure}.json"
        checkpoint_path = parent_root / "checkpoints" / f"selected-{structure}.pt"
        if not receipt_path.is_file() or not checkpoint_path.is_file():
            raise FileNotFoundError(f"父 {structure} 选择收据或检查点缺失")
        receipt = load_json(receipt_path)
        selection = receipt.get("selection", {})
        if selection.get("unit_key") != structure or structure not in completed:
            raise RuntimeError(f"父 {structure} 未进入完成结构封印")
        checkpoint_sha256 = sha256_file(checkpoint_path)
        if selection.get("checkpoint", {}).get("sha256") != checkpoint_sha256:
            raise RuntimeError(f"父 {structure} 检查点摘要不符")
        candidate = next(item for item in config["structures"] if item["unit_key"] == structure)
        if receipt.get("candidate") != candidate:
            raise RuntimeError(f"父 {structure} 结构收据与冻结候选不符")
        receipts[structure] = {
            "selection_receipt": {
                "path": str(receipt_path),
                "bytes": receipt_path.stat().st_size,
                "sha256": sha256_file(receipt_path),
            },
            "checkpoint": {
                "path": str(checkpoint_path),
                "bytes": checkpoint_path.stat().st_size,
                "sha256": checkpoint_sha256,
            },
            "selection": selection,
        }
    return {
        "run_id": PARENT_RUN_ID,
        "config": {"path": str(parent_config_path), "sha256": sha256_file(parent_config_path)},
        "seal": {
            "path": str(seal_path),
            "sha256": sha256_file(seal_path),
            "source_gate_passed": bool(seal.get("source_gate", {}).get("passed")),
            "source_gate_used_for_this_evaluation": False,
        },
        "structures": receipts,
    }


def target_file_inventory(config: dict[str, Any]) -> dict[str, Any]:
    cache_root = Path(config["paths"]["cache_root"])
    files: list[dict[str, Any]] = []
    for name in TARGET_ARRAYS:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结目标数组：{path}")
        stat = path.stat()
        files.append({"name": path.name, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns})
    return {
        "files": files,
        "metadata_sha256": canonical_sha256(files),
        "content_hash_read_skipped": True,
        "content_hash_read_skipped_reason": "保持目标数组单次读取，不额外全文扫描数组文件",
    }


def load_target_once(config: dict[str, Any]) -> dict[str, Any]:
    np = shared_eval.require_numpy()
    cache_root = Path(config["paths"]["cache_root"])
    arrays = {
        # 数据身份：X24 是 dijk 复现管线标准化后的特征矩阵（非有限值置 0 → 按 LSPR23 逐列均值和
        # 标准差标准化 → 裁剪 [-10, 10]），不是 raw83 原值。本入口直接送模型是对的，因为 GRANDE
        # 源年就训练在这份缓存上，两侧同源；不得在其上再叠加候选 A/B 变换。见缓存目录 README.md。
        "X24": np.load(cache_root / "X24.npy", mmap_mode="r", allow_pickle=False),
        "y24": np.load(cache_root / "y24.npy", mmap_mode="r", allow_pickle=False),
        "s24": np.load(cache_root / "s24.npy", allow_pickle=True),
        "d24": np.load(cache_root / "d24.npy", allow_pickle=True),
    }
    if arrays["X24"].shape != (20_227_356, 83) or len(arrays["y24"]) != 20_227_356:
        raise RuntimeError("LSPR24 流表或 83 字段形状不符")
    if len(arrays["s24"]) != 20_227_356 or len(arrays["d24"]) != 20_227_356:
        raise RuntimeError("LSPR24 实体分组列长度不符")
    return arrays


def build_target_context(target: dict[str, Any]) -> dict[str, Any]:
    np = shared_eval.require_numpy()
    keys = np.array(
        [left + "|" + right if left <= right else right + "|" + left for left, right in zip(target["s24"], target["d24"])],
        dtype=object,
    )
    _, flow_entity = np.unique(keys, return_inverse=True)
    del keys
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.int8)
    np.maximum.at(entity_labels, flow_entity, target["y24"].astype(np.int8, copy=False))
    flow_positive_rate = float(target["y24"].astype(np.float64).mean())
    if entity_count != 47_115 or int(entity_labels.sum()) != 752:
        raise RuntimeError("LSPR24 实体数或正实体数不符")
    if abs(flow_positive_rate - 0.0257073138) >= 1e-9:
        raise RuntimeError("LSPR24 逐流正例率不符")
    seen = np.ones(len(target["y24"]), dtype=np.bool_)
    order = shared_eval.ordered_exposures(seen, flow_entity)
    return {
        "flow_entity": flow_entity,
        "entity_labels": entity_labels,
        "order": order,
        "flow_positive_rate": flow_positive_rate,
        "flow_count": int(len(target["y24"])),
        "entity_count": entity_count,
        "positive_entity_count": int(entity_labels.sum()),
    }


def unit_identity(
    config_sha256: str,
    target_inventory: dict[str, Any],
    parent_receipt: dict[str, Any],
    structure: str,
) -> dict[str, Any]:
    return {
        "schema_version": "ch3-grande-lspr24-zero-train-descriptive-eval-unit-identity-v1",
        "run_id": RUN_ID,
        "config_sha256": config_sha256,
        "target_inventory_metadata_sha256": target_inventory["metadata_sha256"],
        "parent_run_id": PARENT_RUN_ID,
        "structure": structure,
        "parent_checkpoint_sha256": parent_receipt["checkpoint"]["sha256"],
        "parent_selection_receipt_sha256": parent_receipt["selection_receipt"]["sha256"],
    }


def load_completed_unit(output_root: Path, structure: str, identity: dict[str, Any], resume: bool) -> dict[str, Any] | None:
    unit_root = output_root / "units" / structure
    if not unit_root.exists():
        return None
    if not resume:
        raise RuntimeError(f"{structure} 已有评价制品但未显式 --resume")
    aggregate_path = unit_root / "aggregate.json"
    curve_path = unit_root / "curves.npz"
    if not aggregate_path.is_file() or not curve_path.is_file():
        raise RuntimeError(f"{structure} 存在不完整单元目录")
    aggregate = load_json(aggregate_path)
    if aggregate.get("identity") != identity or aggregate.get("complete") is not True:
        raise RuntimeError(f"{structure} 完成单元身份不符")
    if aggregate.get("curve_artifact", {}).get("sha256") != sha256_file(curve_path):
        raise RuntimeError(f"{structure} 完整曲线摘要不符")
    log(f"{structure} 复用身份与摘要一致的完成单元")
    return aggregate


def score_structure(config: dict[str, Any], structure: str, checkpoint_path: Path, target_x: Any) -> tuple[Any, dict[str, Any]]:
    np = shared_eval.require_numpy()
    torch = grande.torch
    if torch is None or not torch.cuda.is_available():
        raise RuntimeError("GRANDE LSPR24 评价需要可用 CUDA")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("当前 CUDA 设备不支持冻结 BF16 推理")
    candidate = next(item for item in config["structures"] if item["unit_key"] == structure)
    device = torch.device("cuda")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model = grande.build_model(candidate, config["inference"]["feature_count"]).to(device)
    model.load_state_dict(checkpoint["model"])
    if any(parameter.dtype != torch.float32 for parameter in model.parameters()):
        raise RuntimeError(f"{structure} 回载参数未保持 FP32")
    model.eval()
    scores = np.empty(len(target_x), dtype=np.float32)
    batch_size = config["inference"]["flow_batch_size"]
    torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    with torch.inference_mode():
        for start in range(0, len(target_x), batch_size):
            stop = min(start + batch_size, len(target_x))
            values = torch.from_numpy(np.array(target_x[start:stop], copy=True)).to(device)
            with torch.amp.autocast("cuda", dtype=torch.bfloat16):
                logits = model(values)
            with torch.amp.autocast("cuda", enabled=False):
                probabilities = torch.sigmoid(logits.float())
            scores[start:stop] = probabilities.cpu().numpy()
            if start == 0 or stop == len(target_x) or stop % 2_000_000 < batch_size:
                elapsed = max(time.time() - started, 1e-9)
                log(f"{structure} 打分进度={stop}/{len(target_x)} 吞吐={stop / elapsed:.1f}流/秒")
    wall_seconds = time.time() - started
    resources = {
        "pure_inference_wall_seconds": wall_seconds,
        "inference_gpu_hours": wall_seconds / 3600.0,
        "flows_scored": int(len(scores)),
        "flows_per_second": len(scores) / max(wall_seconds, 1e-12),
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
        "parameter_count": int(sum(parameter.numel() for parameter in model.parameters())),
        "model_weight_bytes": int(sum(parameter.numel() * parameter.element_size() for parameter in model.parameters())),
    }
    del model, checkpoint
    torch.cuda.empty_cache()
    return scores, resources


def running_entity_max(flow_scores: Any, order: dict[str, Any]) -> Any:
    np = shared_eval.require_numpy()
    ordered_scores = flow_scores[order["flow_ids"]].astype(np.float64, copy=False)
    running = np.empty(len(ordered_scores), dtype=np.float64)
    for start, end in zip(order["starts"].tolist(), order["ends"].tolist()):
        running[start:end] = np.maximum.accumulate(ordered_scores[start:end])
    return running


def evaluate_structure(
    config: dict[str, Any],
    structure: str,
    flow_scores: Any,
    target_y: Any,
    context: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    np = shared_eval.require_numpy()
    average_precision_score = shared_eval.require_metrics()
    started = time.time()
    flow_entity = context["flow_entity"]
    entity_labels = context["entity_labels"]
    entity_scores = np.full(context["entity_count"], -np.inf, dtype=np.float32)
    np.maximum.at(entity_scores, flow_entity, flow_scores)
    curve = shared_eval.complete_tied_budget_curve(entity_scores, entity_labels)
    grid = config["evaluation"]["dr_fpr_grid"]
    reachable = shared_eval.actual_reachable_readouts(curve, grid)
    common = shared_eval.common_integer_fp_budget_readouts(curve, grid)
    running_scores = running_entity_max(flow_scores, context["order"])
    terminal_from_path = running_scores[context["order"]["ends"] - 1]
    if not np.array_equal(
        terminal_from_path.astype(np.float32),
        entity_scores[context["order"]["entity_ids"]],
    ):
        raise RuntimeError(f"{structure} 前缀最大路径终点与实体最大分数不一致")
    first_alert, first_alert_curves = shared_eval.first_alert_aggregate(
        {"key": structure},
        running_scores,
        context["order"],
        entity_labels,
        np.isfinite(entity_scores),
        reachable,
        "complete_tie_group_actual_reachable",
        config["evaluation"]["first_alert_quantiles"],
    )
    flow_ap = float(average_precision_score(target_y, flow_scores))
    entity_ap = float(average_precision_score(entity_labels, entity_scores))
    curve_arrays = {
        key: value
        for key, value in curve.items()
        if isinstance(value, np.ndarray)
    }
    curve_arrays.update(first_alert_curves)
    result = {
        "structure": structure,
        "display_name": next(item["display_name"] for item in config["structures"] if item["unit_key"] == structure),
        "flow_average_precision": flow_ap,
        "entity_average_precision": entity_ap,
        "maximum_entity_average_precision": entity_ap,
        "entity_and_maximum_entity_score_identical": True,
        "entity_score_semantics": "maximum_flow_probability",
        "actual_reachable_complete_tie_group_readouts": reachable,
        "common_integer_fp_budget_readouts": common,
        "first_alert": first_alert,
        "complete_curve_points": int(len(curve["threshold"])),
        "complete_curve_negative_entity_count": int(curve["negative_entity_count"]),
        "complete_curve_positive_entity_count": int(curve["positive_entity_count"]),
        "flow_score_sha256_in_memory_only": hashlib.sha256(np.ascontiguousarray(flow_scores).view(np.uint8)).hexdigest(),
        "entity_score_sha256_in_memory_only": hashlib.sha256(np.ascontiguousarray(entity_scores).view(np.uint8)).hexdigest(),
        "aggregation_wall_seconds": time.time() - started,
    }
    del entity_scores, running_scores
    return result, curve_arrays


def save_unit(
    output_root: Path,
    structure: str,
    identity: dict[str, Any],
    metrics: dict[str, Any],
    curves: dict[str, Any],
    resources: dict[str, Any],
) -> dict[str, Any]:
    np = shared_eval.require_numpy()
    unit_root = output_root / "units" / structure
    if unit_root.exists():
        raise RuntimeError(f"{structure} 单元目录已存在，拒绝覆盖")
    temporary_root = unit_root.with_name(f"{structure}.partial.{os.getpid()}")
    temporary_root.mkdir(parents=True, exist_ok=False)
    curve_path = temporary_root / "curves.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **curves)
    aggregate = {
        "schema_version": UNIT_SCHEMA_VERSION,
        "identity": identity,
        "metrics": metrics,
        "resource": {
            **resources,
            "peak_process_rss_mib_after_aggregation": process_peak_rss_mib(),
        },
        "isolation": {
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_evaluation_calls": 1,
            "one_forward_pass": True,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
        },
        "curve_artifact": {
            "filename": "curves.npz",
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
            "fields": sorted(curves),
            "complete_negative_tie_group_curve": True,
            "first_alert_aggregate_curves": True,
        },
        "complete": True,
    }
    atomic_json(temporary_root / "aggregate.json", aggregate)
    unit_root.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temporary_root, unit_root)
    return aggregate


def build_manifest(output_root: Path) -> None:
    forbidden = (
        "flow-score",
        "flow_score",
        "entity-score",
        "entity_score",
        "first-alert-position",
        "first_alert_position",
        "entity-mapping",
        "entity_mapping",
        "exposure-matrix",
        "exposure_matrix",
        ".pt",
        ".pth",
        ".ckpt",
    )
    files: dict[str, Any] = {}
    for path in sorted(item for item in output_root.rglob("*") if item.is_file() and item.name != "artifact-manifest.json"):
        relative = str(path.relative_to(output_root))
        if any(token in relative.lower() for token in forbidden):
            raise RuntimeError(f"运行根出现禁止制品：{relative}")
        files[relative] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    atomic_json(
        output_root / "artifact-manifest.json",
        {
            "schema_version": "ch3-grande-lspr24-zero-train-descriptive-eval-manifest-v1",
            "run_id": RUN_ID,
            "files": files,
            "structures": list(STRUCTURE_ORDER),
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
            "forbidden_artifacts_absent": True,
            "complete": True,
        },
    )


def run(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    frozen_config_path = output_root / "config.json"
    if frozen_config_path.is_file():
        if not args.resume or load_json(frozen_config_path) != config:
            raise RuntimeError("输出根已有不兼容冻结配置")
    else:
        atomic_json(frozen_config_path, config)
    write_status(output_root, "running", "parent-validation", None, "核验父 G-A/G-B 检查点与封印")
    parent = validate_parent(config)
    target_inventory = target_file_inventory(config)
    config_sha256 = sha256_file(config_path)
    identities = {
        structure: unit_identity(config_sha256, target_inventory, parent["structures"][structure], structure)
        for structure in STRUCTURE_ORDER
    }
    completed: dict[str, Any] = {}
    for structure in STRUCTURE_ORDER:
        restored = load_completed_unit(output_root, structure, identities[structure], args.resume)
        if restored is not None:
            completed[structure] = restored
    input_identity = {
        "schema_version": "ch3-grande-lspr24-zero-train-descriptive-eval-input-identity-v1",
        "run_id": RUN_ID,
        "config_sha256": config_sha256,
        "code_sha256": sha256_file(Path(__file__).resolve()),
        "shared_grande_tool_sha256": sha256_file(Path(grande.__file__).resolve()),
        "shared_evaluation_tool_sha256": sha256_file(Path(shared_eval.__file__).resolve()),
        "parent": parent,
        "target_inventory": target_inventory,
        "unit_identities": identities,
    }
    identity_path = output_root / "input-identity.json"
    if identity_path.is_file():
        if load_json(identity_path) != input_identity:
            raise RuntimeError("输入身份与已冻结值不符")
    else:
        atomic_json(identity_path, input_identity)
    target_load_passes = 0
    target_array_open_calls = 0
    evaluation_calls_this_process = 0
    evaluation_receipts_reused = len(completed)
    run_started = time.time()
    if len(completed) < len(STRUCTURE_ORDER):
        write_status(output_root, "running", "target-load", None, "LSPR24 数组单次加载")
        target = load_target_once(config)
        target_load_passes = 1
        target_array_open_calls = len(TARGET_ARRAYS)
        context = build_target_context(target)
        for structure in STRUCTURE_ORDER:
            if structure in completed:
                continue
            write_status(output_root, "running", "target-evaluation", None, f"{structure} 单次 BF16 打分与聚合")
            flow_scores, resources = score_structure(
                config,
                structure,
                Path(parent["structures"][structure]["checkpoint"]["path"]),
                target["X24"],
            )
            evaluation_calls_this_process += 1
            metrics, curves = evaluate_structure(config, structure, flow_scores, target["y24"], context)
            completed[structure] = save_unit(
                output_root,
                structure,
                identities[structure],
                metrics,
                curves,
                resources,
            )
            del flow_scores, curves
        del target, context
    if set(completed) != set(STRUCTURE_ORDER):
        raise RuntimeError("G-A/G-B 两个描述性评价单元未全部完成")
    if evaluation_calls_this_process + evaluation_receipts_reused != 2:
        raise RuntimeError("每结构恰好一次评价或幂等复用计数不符")
    launcher_resource = load_json(Path(args.resource_receipt)) if args.resource_receipt else None
    rows = [
        {
            "structure": structure,
            "display_name": completed[structure]["metrics"]["display_name"],
            "metrics": completed[structure]["metrics"],
            "resource": completed[structure]["resource"],
        }
        for structure in STRUCTURE_ORDER
    ]
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": config["display_name"],
        "parent_run_id": PARENT_RUN_ID,
        "evaluation_role": config["evaluation"]["role"],
        "dataset": "LSPR24",
        "rows": rows,
        "structure_order": list(STRUCTURE_ORDER),
        "selection": {
            "selection_performed": False,
            "winner": None,
            "target_used_for_selection": False,
            "source_gate_used_for_structure_selection": False,
            "reporting_rule": "G-A与G-B各一行并列描述，不排名不晋级",
        },
        "isolation": {
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_array_load_passes_this_process": target_load_passes,
            "target_array_open_calls_this_process": target_array_open_calls,
            "target_arrays_opened_once_each_when_evaluation_required": (
                (target_load_passes == 0 and target_array_open_calls == 0)
                or (target_load_passes == 1 and target_array_open_calls == len(TARGET_ARRAYS))
            ),
            "target_evaluation_calls_this_process": evaluation_calls_this_process,
            "target_evaluation_receipts_reused": evaluation_receipts_reused,
            "one_evaluation_per_structure_total": True,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "per_entity_first_alert_persisted": False,
        },
        "evidence": config["evidence"],
        "resource": {
            "controller_wall_seconds": time.time() - run_started,
            "peak_process_rss_mib": process_peak_rss_mib(),
            "launcher_resource_receipt": launcher_resource,
        },
    }
    atomic_json(output_root / "aggregate-results.json", result)
    write_status(output_root, "complete", "complete", 0, "G-A/G-B LSPR24 零重训练描述性评价完成")
    build_manifest(output_root)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    output_root = Path(config.get("paths", {}).get("output_root", "/tmp/invalid-grande-lspr24-eval"))
    try:
        validate_config(config)
        if args.validate_config:
            log("配置核验通过")
            return 0
        run(config, args, config_path)
        return 0
    except Exception as error:
        try:
            output_root.mkdir(parents=True, exist_ok=True)
            write_status(output_root, "failed", "failed", 1, f"{type(error).__name__}: {error}")
        except Exception:
            pass
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
