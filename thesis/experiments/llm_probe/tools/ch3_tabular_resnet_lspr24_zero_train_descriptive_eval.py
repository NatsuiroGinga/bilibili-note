# -*- coding: utf-8 -*-
"""表格预归一化残差多层感知机四格封印检查点的 LSPR24 零重训练描述性评价。

本入口只读评价，不训练、不改阈值、不改模型、不触碰源年封印，也不物化任何目标年
数据产品。目标年特征从 ``runs/diagnostics/dijk-repro/cache/`` 的冻结数组进入，胜出
输入臂变换只在内存中复算一次，任何特征矩阵都不落盘。

指标口径全部直接复用父工具 ``ch3_tabular_resnet_paper_recipe_protocol_a`` 的
``entity_aggregate`` / ``terminal_curve`` / ``budget_points``，保证目标年读数与已封印
的源年读数出自同一段代码。实体口径复用
``ch3_xgb_cpa_elp_operational_backfill`` 的无向地址对分组与三条冻结断言常量。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
for _root in (TOOL_DIR, PROJECT_ROOT / "src"):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

import ch3_tabular_resnet_paper_recipe_protocol_a as parent

RUN_ID = "ch3-tabular-resnet-lspr24-zero-train-descriptive-eval-v1"
DISPLAY_NAME = "表格预归一化残差多层感知机四格LSPR24零重训练描述性评价"
PARENT_RUN_ID = parent.RUN_ID
CELL_ORDER = parent.CELL_ORDER
DR_FPR_GRID = parent.DR_FPR_GRID
TARGET_ARRAYS = ("X24", "y24", "I24", "M24", "s24", "d24")

# 以下五个冻结常量照抄 tools/ch3_xgb_cpa_elp_operational_backfill.py，不得就地放宽。
N_FLOW = 20_227_356
N_SEQUENCE_WIDTH = 128
N_RAW_FEATURE = 83
N_ENTITY = 47_115
N_POSITIVE_ENTITY = 752
FLOW_POSITIVE_RATE = 0.0257073138
N_SEQUENCE = 200_825

VIEW_CLIP = (-10.0, 10.0)
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


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def process_peak_rss_mib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None, detail: str) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-tabular-resnet-lspr24-descriptive-eval-status-v1",
            "run_id": RUN_ID,
            "parent_run_id": PARENT_RUN_ID,
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "detail": detail,
            "updated_at_unix": time.time(),
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_data_products_materialized": 0,
            "target_used_for_selection": False,
        },
    )


# --------------------------------------------------------------------------------------
# 父运行核验
# --------------------------------------------------------------------------------------


def validate_parent(parent_root: Path, source_manifest_path: Path) -> dict[str, Any]:
    """只读核验四格源年封印、胜出臂与四个检查点摘要，绝不改写父运行根。"""

    status = load_json(parent_root / "status.json")
    if status.get("run_id") != PARENT_RUN_ID or status.get("state") != "source-qualified":
        raise RuntimeError(f"父运行未处于源资格封印状态：{status.get('state')}")
    cells_seal = load_json(parent_root / "source-cells-sealed.json")
    if cells_seal.get("run_id") != PARENT_RUN_ID or cells_seal.get("all_four_cells_sealed") is not True:
        raise RuntimeError("四格源年封印不完整")
    if set(cells_seal["cells"]) != set(CELL_ORDER):
        raise RuntimeError("四格封印格集合不符")
    arm = load_json(parent_root / "input-selection-sealed.json")["selected"]
    optimizer_key = load_json(parent_root / "optimizer-selection-sealed.json")["selected"]
    if cells_seal.get("input_arm") != arm or cells_seal.get("optimizer_candidate") != optimizer_key:
        raise RuntimeError("四格封印的臂或优化器与选择封印不符")
    if arm not in {"A", "B"}:
        raise RuntimeError(f"胜出输入臂非法：{arm}")
    arm_receipt = load_json(parent_root / "source-input-arm-receipt.json")
    source_manifest = load_json(source_manifest_path)
    if source_manifest["transform_state_hashes"][arm] != arm_receipt["transform_state_sha256"]:
        raise RuntimeError("源清单胜出臂变换状态 SHA-256 与臂收据不符")
    if source_manifest["view_content_sha256"][arm] != arm_receipt["view_content_sha256"]:
        raise RuntimeError("源清单胜出臂视图内容 SHA-256 与臂收据不符")

    cells: dict[str, Any] = {}
    for cell in CELL_ORDER:
        selection = cells_seal["cells"][cell]["selection"]
        checkpoint_path = Path(selection["checkpoint"]["path"])
        if not checkpoint_path.is_file():
            raise FileNotFoundError(f"{cell} 封印检查点缺失：{checkpoint_path}")
        observed = sha256_file(checkpoint_path)
        if observed != selection["checkpoint"]["sha256"]:
            raise RuntimeError(f"{cell} 封印检查点 SHA-256 不符")
        if selection.get("cell") != cell:
            raise RuntimeError(f"{cell} 选择收据格身份不符")
        cells[cell] = {
            "selection": selection,
            "checkpoint_sha256": observed,
            "source_validation": cells_seal["cells"][cell]["source_validation"],
        }
    return {
        "run_id": PARENT_RUN_ID,
        "input_arm": arm,
        "optimizer_candidate": optimizer_key,
        "source_cells_sealed_sha256": sha256_file(parent_root / "source-cells-sealed.json"),
        "source_input_arm_receipt_sha256": sha256_file(parent_root / "source-input-arm-receipt.json"),
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "cells": cells,
    }


def resolve_state_artifact(source_manifest_path: Path, key: str) -> Path:
    """按源清单登记的字节数与 SHA-256 解析冻结变换状态文件。"""

    manifest = load_json(source_manifest_path)
    item = manifest["artifacts"][key]
    path = Path(item["path"]).resolve(strict=True)
    root = source_manifest_path.parent.resolve(strict=True)
    if path.is_symlink() or not path.is_relative_to(root):
        raise RuntimeError(f"变换状态制品越界或为符号链接：{key}")
    if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
        raise RuntimeError(f"变换状态制品身份不匹配：{key}")
    return path


# --------------------------------------------------------------------------------------
# 胜出臂变换（只在内存复算，绝不落盘）
# --------------------------------------------------------------------------------------


def build_transformer(arm: str, a_state: Path, b_state: Path) -> Any:
    from flow_probe.protocol_a_preprocessing import _restore_quantile_transformer

    return None if arm == "A" else _restore_quantile_transformer(b_state)


def apply_arm(raw_batch: Any, arm: str, a_state: Path, b_state: Path, transformer: Any) -> Any:
    """把冻结的胜出臂变换施加到一批原始 83 字段上，与 P6 年度产品同一段函数。"""

    from flow_probe.protocol_a_preprocessing import _transform_a, _transform_b

    a_batch = _transform_a(raw_batch, a_state, VIEW_CLIP)
    if arm == "A":
        return a_batch
    return _transform_b(raw_batch, a_batch, b_state, transformer)


def verify_transform_reproduces_source_view(
    source_manifest_path: Path,
    arm: str,
    a_state: Path,
    b_state: Path,
    transformer: Any,
    sample_rows: int,
) -> dict[str, Any]:
    """在源年抽样逐位复现已封印视图，证伪"内存复算变换与冻结视图不一致"。"""

    import numpy as np

    manifest = load_json(source_manifest_path)
    raw_path = Path(manifest["artifacts"]["source_raw83"]["path"])
    view_path = Path(manifest["artifacts"][f"source_view_{arm.lower()}"]["path"])
    raw = np.load(raw_path, mmap_mode="r", allow_pickle=False)
    view = np.load(view_path, mmap_mode="r", allow_pickle=False)
    if raw.shape[1] != N_RAW_FEATURE or view.shape != raw.shape:
        raise RuntimeError("源 Raw83 或源视图形状不符")
    generator = np.random.default_rng(42)
    rows = np.unique(generator.integers(0, raw.shape[0], size=sample_rows, dtype=np.int64))
    recomputed = apply_arm(np.asarray(raw[rows]), arm, a_state, b_state, transformer)
    frozen = np.asarray(view[rows])
    identical = bool(np.array_equal(recomputed, frozen))
    maximum_absolute = float(np.max(np.abs(recomputed.astype(np.float64) - frozen.astype(np.float64))))
    if not identical:
        raise RuntimeError(f"内存复算的胜出臂视图与冻结源视图不逐位一致：最大绝对差={maximum_absolute:.6g}")
    log(f"胜出臂 {arm} 变换逐位复现源视图：抽样 {rows.size} 行，最大绝对差={maximum_absolute:.6g}")
    return {
        "sampled_rows": int(rows.size),
        "bitwise_identical_to_frozen_source_view": identical,
        "maximum_absolute_difference": maximum_absolute,
        "source_view_artifact_sha256": manifest["artifacts"][f"source_view_{arm.lower()}"]["sha256"],
    }


# --------------------------------------------------------------------------------------
# 目标年上下文
# --------------------------------------------------------------------------------------


def target_file_inventory(cache_root: Path) -> dict[str, Any]:
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
        "content_hash_read_skipped_reason": "保持目标数组单次读取，不额外全文扫描 6.7 GiB 特征矩阵",
    }


def build_entity_context(cache_root: Path) -> dict[str, Any]:
    """复用 ch3_xgb_cpa_elp_operational_backfill 的无向地址对实体口径与冻结断言。"""

    import numpy as np

    started = time.time()
    y24 = np.asarray(np.load(cache_root / "y24.npy", mmap_mode="r", allow_pickle=False))
    s24 = np.load(cache_root / "s24.npy", allow_pickle=True)
    d24 = np.load(cache_root / "d24.npy", allow_pickle=True)
    if y24.shape != (N_FLOW,) or len(s24) != N_FLOW or len(d24) != N_FLOW:
        raise RuntimeError("LSPR24 标签或实体分组列长度不符")
    entity_key = np.fromiter(
        (
            f"{left}|{right}" if left <= right else f"{right}|{left}"
            for left, right in zip(s24, d24, strict=True)
        ),
        dtype=object,
        count=N_FLOW,
    )
    _, entity = np.unique(entity_key, return_inverse=True)
    entity = entity.astype(np.int64, copy=False)
    del entity_key, s24, d24
    if int(entity.max()) + 1 != N_ENTITY:
        raise RuntimeError(f"LSPR24 实体数应为 {N_ENTITY:,}")
    entity_labels = np.zeros(N_ENTITY, dtype=np.int8)
    np.maximum.at(entity_labels, entity, y24.astype(np.int8, copy=False))
    if int(entity_labels.sum()) != N_POSITIVE_ENTITY:
        raise RuntimeError(f"LSPR24 正实体数应为 {N_POSITIVE_ENTITY}")
    flow_positive_rate = float(np.mean(y24, dtype=np.float64))
    if abs(flow_positive_rate - FLOW_POSITIVE_RATE) >= 1e-9:
        raise RuntimeError(f"LSPR24 逐流正例率不符：{flow_positive_rate:.12f}")
    log(
        f"实体口径已构造：实体={N_ENTITY:,} 正实体={N_POSITIVE_ENTITY} "
        f"逐流正例率={flow_positive_rate:.10f} 用时={time.time() - started:.1f}s"
    )
    return {
        "flow_entity": entity,
        "entity_labels": entity_labels,
        "flow_labels": y24.astype(np.uint8, copy=False),
        "flow_positive_rate": flow_positive_rate,
    }


def build_target_view(
    cache_root: Path,
    arm: str,
    a_state: Path,
    b_state: Path,
    transformer: Any,
    row_batch: int,
) -> Any:
    """在内存中把 LSPR24 的 83 字段一次性变换为胜出臂视图，全程不落盘。"""

    import numpy as np

    started = time.time()
    raw = np.load(cache_root / "X24.npy", mmap_mode="r", allow_pickle=False)
    if raw.shape != (N_FLOW, N_RAW_FEATURE):
        raise RuntimeError("LSPR24 原始 83 字段形状不符")
    view = np.empty((N_FLOW, N_RAW_FEATURE), dtype=np.float32)
    for start in range(0, N_FLOW, row_batch):
        stop = min(start + row_batch, N_FLOW)
        view[start:stop] = apply_arm(np.asarray(raw[start:stop]), arm, a_state, b_state, transformer)
        if start == 0 or stop == N_FLOW or stop % (5 * row_batch) < row_batch:
            log(f"目标年胜出臂视图内存变换进度={stop:,}/{N_FLOW:,}")
    if not np.all(np.isfinite(view)):
        raise RuntimeError("目标年胜出臂视图出现非有限值")
    del raw
    log(f"目标年胜出臂视图内存变换完成，用时={time.time() - started:.1f}s（未写入任何文件）")
    return view


def load_sequences(cache_root: Path) -> tuple[Any, Any]:
    import numpy as np

    indices = np.asarray(np.load(cache_root / "I24.npy", mmap_mode="r", allow_pickle=False))
    masks = np.asarray(np.load(cache_root / "M24.npy", mmap_mode="r", allow_pickle=False)) > 0
    if indices.shape != (N_SEQUENCE, N_SEQUENCE_WIDTH) or masks.shape != indices.shape:
        raise RuntimeError("LSPR24 序列索引或掩码形状不符")
    if int(masks.sum()) != N_FLOW:
        raise RuntimeError("LSPR24 序列有效位置数不等于流数")
    occurrence = np.zeros(N_FLOW, dtype=np.int32)
    np.add.at(occurrence, indices[masks], 1)
    if int((occurrence == 1).sum()) != N_FLOW:
        raise RuntimeError("LSPR24 序列索引没有恰好覆盖每条流一次")
    del occurrence
    return indices, masks


# --------------------------------------------------------------------------------------
# 打分与指标
# --------------------------------------------------------------------------------------


def score_cell(
    receipt: dict[str, Any],
    view: Any,
    indices: Any,
    masks: Any,
    device: Any,
    profile: Any,
    sequence_batch: int,
) -> tuple[Any, dict[str, Any]]:
    """对全部 LSPR24 序列做且只做一次前向，返回逐流概率。"""

    import numpy as np
    import torch

    model = parent.selected_model(receipt, device)
    model.eval()
    expected_p = float(receipt["selected_p"])
    observed_p = float(model.p.detach().cpu())
    if abs(observed_p - expected_p) > 1e-6:
        raise RuntimeError(f"{receipt['cell']} 回载模型的 p 与封印选择不符：{observed_p} vs {expected_p}")
    if any(parameter.dtype != torch.float32 for parameter in model.parameters()):
        raise RuntimeError(f"{receipt['cell']} 回载参数未保持 FP32")

    scores = np.zeros(N_FLOW, dtype=np.float32)
    written = 0
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    with torch.no_grad():
        for start in range(0, N_SEQUENCE, sequence_batch):
            stop = min(start + sequence_batch, N_SEQUENCE)
            batch_indices = indices[start:stop]
            batch_valid = masks[start:stop]
            features = view[batch_indices]
            values = torch.from_numpy(np.ascontiguousarray(features, dtype=np.float32)).to(device)
            valid = torch.from_numpy(np.ascontiguousarray(batch_valid)).to(device)
            with parent.precision_module().autocast_context(profile, device.type, torch):
                logits = model(values, valid)
            probabilities = torch.sigmoid(logits.float()).cpu().numpy()
            flat = batch_valid.reshape(-1)
            scores[batch_indices.reshape(-1)[flat]] = probabilities.reshape(-1)[flat]
            written += int(flat.sum())
            if start == 0 or stop == N_SEQUENCE or stop % (20 * sequence_batch) < sequence_batch:
                elapsed = max(time.time() - started, 1e-9)
                log(
                    f"{receipt['cell']} 打分进度={stop:,}/{N_SEQUENCE:,} 序列 "
                    f"吞吐={written / elapsed:,.0f} 流/秒"
                )
    if written != N_FLOW:
        raise RuntimeError(f"{receipt['cell']} 打分覆盖流数不符：{written} != {N_FLOW}")
    wall_seconds = time.time() - started
    resources = {
        "pure_inference_wall_seconds": wall_seconds,
        "inference_gpu_hours": wall_seconds / 3600.0,
        "sequences_scored": N_SEQUENCE,
        "flows_scored": N_FLOW,
        "flows_per_second": N_FLOW / max(wall_seconds, 1e-12),
        "parameter_count": int(sum(item.numel() for item in model.parameters())),
    }
    if device.type == "cuda":
        resources["peak_gpu_allocated_mib"] = torch.cuda.max_memory_allocated(device) / 2**20
        resources["peak_gpu_reserved_mib"] = torch.cuda.max_memory_reserved(device) / 2**20
        del model
        torch.cuda.empty_cache()
    else:
        del model
    return scores, resources


def curve_to_arrays(curve: list[dict[str, Any]]) -> dict[str, Any]:
    import numpy as np

    return {
        "threshold": np.array(
            [np.nan if item["threshold"] is None else item["threshold"] for item in curve],
            dtype=np.float64,
        ),
        "false_positive_entities": np.array(
            [item["false_positive_entities"] for item in curve], dtype=np.int64
        ),
        "actual_fpr": np.array([item["actual_fpr"] for item in curve], dtype=np.float64),
        "detected_positive_entities": np.array(
            [item["detected_positive_entities"] for item in curve], dtype=np.int64
        ),
        "detection_rate": np.array([item["detection_rate"] for item in curve], dtype=np.float64),
    }


def evaluate_cell(cell: str, receipt: dict[str, Any], scores: Any, context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """完全复用父工具的聚合与曲线函数，保证目标年与源年读数同源。"""

    import numpy as np
    from sklearn.metrics import average_precision_score

    started = time.time()
    flow_labels = context["flow_labels"]
    flow_entity = context["flow_entity"]
    main_p = receipt["selected_p"] if parent.CELLS[cell]["block_auxiliary_objective"] else None

    _, entity_labels, entity_scores = parent.entity_aggregate(scores, flow_labels, flow_entity, main_p)
    _, max_labels, max_scores = parent.entity_aggregate(scores, flow_labels, flow_entity, None)
    if not np.array_equal(entity_labels, max_labels):
        raise RuntimeError(f"{cell} 两条聚合路径的实体标签不一致")
    if not np.array_equal(entity_labels.astype(np.int8), context["entity_labels"]):
        raise RuntimeError(f"{cell} 聚合实体标签与冻结实体口径不一致")

    curve = parent.terminal_curve(entity_scores, entity_labels)
    maximum_curve = parent.terminal_curve(max_scores, max_labels)
    metrics = {
        "cell": cell,
        "causal_prefix_aggregation": parent.CELLS[cell]["causal_prefix_aggregation"],
        "block_auxiliary_objective": parent.CELLS[cell]["block_auxiliary_objective"],
        "entity_aggregation_p": None if main_p is None else float(main_p),
        "entity_score_semantics": (
            "maximum_flow_probability" if main_p is None else "learned_lp_pool_over_entity_flows"
        ),
        "entity_and_maximum_entity_identical_by_construction": main_p is None,
        "flow_average_precision": float(average_precision_score(flow_labels, scores)),
        "entity_average_precision": float(average_precision_score(entity_labels, entity_scores)),
        "maximum_entity_average_precision": float(average_precision_score(max_labels, max_scores)),
        "six_actual_fpr_points": parent.budget_points(curve),
        "six_actual_fpr_points_maximum_pool": parent.budget_points(maximum_curve),
        "complete_curve_points": len(curve),
        "complete_curve_points_maximum_pool": len(maximum_curve),
        "entity_count": int(entity_labels.size),
        "positive_entity_count": int(entity_labels.sum()),
        "negative_entity_count": int((entity_labels == 0).sum()),
        "readout_rule": "budget=int(negative_entities*nominal_fpr)，取不超预算的最后一点，actual_fpr 为实际可达值",
        "nominal_fpr_is_not_actual_fpr": True,
        "aggregation_wall_seconds": time.time() - started,
        "scores_persisted": False,
        "entity_scores_persisted": False,
    }
    arrays = {f"terminal_{key}": value for key, value in curve_to_arrays(curve).items()}
    arrays.update({f"maximum_pool_{key}": value for key, value in curve_to_arrays(maximum_curve).items()})
    del entity_scores, max_scores
    return metrics, arrays


def save_unit(output_root: Path, cell: str, identity: dict[str, Any], metrics: dict[str, Any], arrays: dict[str, Any], resources: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    unit_root = output_root / "units" / cell
    if unit_root.exists():
        raise RuntimeError(f"{cell} 单元目录已存在，拒绝覆盖")
    temporary_root = unit_root.with_name(f"{cell}.partial.{os.getpid()}")
    temporary_root.mkdir(parents=True, exist_ok=False)
    curve_path = temporary_root / "curves.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    aggregate = {
        "schema_version": "ch3-tabular-resnet-lspr24-descriptive-eval-unit-v1",
        "identity": identity,
        "metrics": metrics,
        "resource": {**resources, "peak_process_rss_mib_after_aggregation": process_peak_rss_mib()},
        "isolation": {
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_evaluation_calls": 1,
            "one_forward_pass_over_all_sequences": True,
            "target_data_products_materialized": 0,
        },
        "curve_artifact": {
            "filename": "curves.npz",
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
            "fields": sorted(arrays),
        },
        "complete": True,
    }
    atomic_json(temporary_root / "aggregate.json", aggregate)
    unit_root.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temporary_root, unit_root)
    return aggregate


def load_completed_unit(output_root: Path, cell: str, identity: dict[str, Any], resume: bool) -> dict[str, Any] | None:
    unit_root = output_root / "units" / cell
    if not unit_root.exists():
        return None
    if not resume:
        raise RuntimeError(f"{cell} 已有评价制品但未显式 --resume")
    aggregate_path = unit_root / "aggregate.json"
    curve_path = unit_root / "curves.npz"
    if not aggregate_path.is_file() or not curve_path.is_file():
        raise RuntimeError(f"{cell} 存在不完整单元目录")
    aggregate = load_json(aggregate_path)
    if aggregate.get("identity") != identity or aggregate.get("complete") is not True:
        raise RuntimeError(f"{cell} 完成单元身份不符")
    if aggregate.get("curve_artifact", {}).get("sha256") != sha256_file(curve_path):
        raise RuntimeError(f"{cell} 曲线制品摘要不符")
    log(f"{cell} 复用身份与摘要一致的完成单元")
    return aggregate


def build_manifest(output_root: Path) -> None:
    forbidden = ("flow-score", "flow_score", "entity-score", "entity_score", ".pt", ".pth", ".ckpt", ".npy")
    files: dict[str, Any] = {}
    for path in sorted(item for item in output_root.rglob("*") if item.is_file() and item.name != "artifact-manifest.json"):
        relative = str(path.relative_to(output_root))
        if any(token in relative.lower() for token in forbidden):
            raise RuntimeError(f"运行根出现禁止制品：{relative}")
        files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(
        output_root / "artifact-manifest.json",
        {
            "schema_version": "ch3-tabular-resnet-lspr24-descriptive-eval-manifest-v1",
            "run_id": RUN_ID,
            "files": files,
            "cells": list(CELL_ORDER),
            "training_runs": 0,
            "new_checkpoints_written": 0,
            "target_data_products_materialized": 0,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "forbidden_artifacts_absent": True,
            "complete": True,
        },
    )


# --------------------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=DISPLAY_NAME)
    parser.add_argument(
        "--parent-run-root",
        default=str(PROJECT_ROOT / "runs" / "diagnostics" / PARENT_RUN_ID),
    )
    parser.add_argument(
        "--source-manifest",
        default=str(
            PROJECT_ROOT
            / "runs"
            / "data-prepared"
            / "ch3-protocol-a-raw83-shared-v1"
            / "generations"
            / "source-v1"
            / "dataset-manifest.json"
        ),
    )
    parser.add_argument(
        "--cache-root", default=str(PROJECT_ROOT / "runs" / "diagnostics" / "dijk-repro" / "cache")
    )
    parser.add_argument("--output-root", default=str(PROJECT_ROOT / "runs" / "diagnostics" / RUN_ID))
    parser.add_argument("--sequence-batch", type=int, default=512)
    parser.add_argument("--transform-row-batch", type=int, default=1_000_000)
    parser.add_argument("--transform-check-rows", type=int, default=50_000)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    parent_root = Path(args.parent_run_root).resolve(strict=True)
    source_manifest_path = Path(args.source_manifest).resolve(strict=True)
    cache_root = Path(args.cache_root).resolve(strict=True)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    write_status(output_root, "running", "parent-validation", None, "只读核验四格源年封印与检查点")
    parent_receipt = validate_parent(parent_root, source_manifest_path)
    arm = parent_receipt["input_arm"]
    log(f"父运行核验通过：胜出臂={arm} 优化器={parent_receipt['optimizer_candidate']}")

    a_state = resolve_state_artifact(source_manifest_path, "candidate_a_state")
    b_state = resolve_state_artifact(source_manifest_path, "candidate_b_state")
    transformer = build_transformer(arm, a_state, b_state)

    write_status(output_root, "running", "transform-verification", None, "抽样逐位复现冻结源视图")
    transform_check = verify_transform_reproduces_source_view(
        source_manifest_path, arm, a_state, b_state, transformer, args.transform_check_rows
    )

    inventory = target_file_inventory(cache_root)
    identities = {
        cell: {
            "schema_version": "ch3-tabular-resnet-lspr24-descriptive-eval-unit-identity-v1",
            "run_id": RUN_ID,
            "cell": cell,
            "parent_run_id": PARENT_RUN_ID,
            "input_arm": arm,
            "parent_checkpoint_sha256": parent_receipt["cells"][cell]["checkpoint_sha256"],
            "parent_source_cells_sealed_sha256": parent_receipt["source_cells_sealed_sha256"],
            "target_inventory_metadata_sha256": inventory["metadata_sha256"],
            "evaluation_code_sha256": sha256_file(Path(__file__).resolve()),
            "parent_code_sha256": sha256_file(Path(parent.__file__).resolve()),
        }
        for cell in CELL_ORDER
    }
    completed = {
        cell: unit
        for cell in CELL_ORDER
        if (unit := load_completed_unit(output_root, cell, identities[cell], args.resume)) is not None
    }

    reused_units = len(completed)
    evaluation_calls = 0
    run_started = time.time()
    if len(completed) < len(CELL_ORDER):
        write_status(output_root, "running", "target-context", None, "构造实体口径与内存胜出臂视图")
        context = build_entity_context(cache_root)
        view = build_target_view(cache_root, arm, a_state, b_state, transformer, args.transform_row_batch)
        indices, masks = load_sequences(cache_root)
        device = parent.resolve_device()
        profile = parent.precision_module().get_profile(
            parent.load_json(parent.precision_contract_path()), parent.PRECISION_PROFILE_ID
        )
        for cell in CELL_ORDER:
            if cell in completed:
                continue
            write_status(output_root, "running", "target-evaluation", None, f"{cell} 单次前向与聚合")
            selection = parent_receipt["cells"][cell]["selection"]
            scores, resources = score_cell(selection, view, indices, masks, device, profile, args.sequence_batch)
            evaluation_calls += 1
            metrics, arrays = evaluate_cell(cell, selection, scores, context)
            log(
                f"{cell} 实体AP={metrics['entity_average_precision']:.12f} "
                f"最大池化实体AP={metrics['maximum_entity_average_precision']:.12f} "
                f"逐流AP={metrics['flow_average_precision']:.12f}"
            )
            completed[cell] = save_unit(output_root, cell, identities[cell], metrics, arrays, resources)
            del scores, arrays
        del view, indices, masks, context

    if set(completed) != set(CELL_ORDER):
        raise RuntimeError("四格描述性评价未全部完成")
    if evaluation_calls + reused_units != len(CELL_ORDER):
        raise RuntimeError(
            f"每格恰好一次评价的计数不符：本进程评价={evaluation_calls} 复用={reused_units}"
        )

    rows = [
        {
            "cell": cell,
            "metrics": completed[cell]["metrics"],
            "resource": completed[cell]["resource"],
            "source_validation_reference": parent_receipt["cells"][cell]["source_validation"],
        }
        for cell in CELL_ORDER
    ]
    atomic_json(
        output_root / "aggregate-results.json",
        {
            "schema_version": "ch3-tabular-resnet-lspr24-descriptive-eval-results-v1",
            "run_id": RUN_ID,
            "display_name": DISPLAY_NAME,
            "parent_run_id": PARENT_RUN_ID,
            "dataset": "LSPR24",
            "evaluation_role": "previously_accessed_target_year_descriptive_evaluation",
            "input_arm": arm,
            "optimizer_candidate": parent_receipt["optimizer_candidate"],
            "cell_order": list(CELL_ORDER),
            "dr_fpr_grid": list(DR_FPR_GRID),
            "rows": rows,
            "entity_contract": {
                "entity_key": "unordered_source_destination_ip_pair_grouping_only",
                "entity_count": N_ENTITY,
                "positive_entity_count": N_POSITIVE_ENTITY,
                "flow_positive_rate": FLOW_POSITIVE_RATE,
                "source_of_truth": "tools/ch3_xgb_cpa_elp_operational_backfill.py",
            },
            "transform_verification": transform_check,
            "target_inventory": inventory,
            "parent": {
                key: value for key, value in parent_receipt.items() if key != "cells"
            },
            "selection": {
                "selection_performed": False,
                "winner": None,
                "target_used_for_selection": False,
                "reporting_rule": "四格并列描述，不排名不晋级",
            },
            "isolation": {
                "training_runs": 0,
                "optimizer_steps": 0,
                "parameter_updates": 0,
                "new_checkpoints_written": 0,
                "thresholds_modified": 0,
                "source_seals_modified": 0,
                "target_data_products_materialized": 0,
                "target_evaluation_calls_this_process": evaluation_calls,
                "target_evaluation_units_reused": reused_units,
                "one_evaluation_per_cell_total": True,
            },
            "resource": {
                "controller_wall_seconds": time.time() - run_started,
                "peak_process_rss_mib": process_peak_rss_mib(),
            },
        },
    )
    write_status(output_root, "complete", "complete", 0, "四格 LSPR24 零重训练描述性评价完成")
    build_manifest(output_root)


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root)
    try:
        run(args)
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
