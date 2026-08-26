#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""表格预归一化残差多层感知机四格在 LSPR24 上的零物化内存直读描述性评价。

本入口不训练、不改阈值、不改模型、不碰源年封印，也不写任何数据制品：目标年的
83 字段原值直接从冻结的 LSPR24 Parquet 流式读入，胜出输入臂变换只在内存中复算，
序列结构用被 ``configs/ch3-protocol-a-raw83-target-v1.json`` 以冻结 SHA-256 登记的
``I24.npy`` / ``M24.npy``。

为什么不能读 ``runs/diagnostics/dijk-repro/cache/X24.npy``：实测该数组不是 Dijk 83
字段原值，而是 dijk 复现管线自己标准化后的特征矩阵（LSPR23 对照实测：与协议A冻结
raw83 有 ``1,224,589,881`` 个有限值单元不同，前 20 万行最大绝对差 ``251799984.0``）。
把它送进按 ``raw83 → 候选A → 候选B`` 拟合的模型，等于给模型从未见过的输入分布，
读数无效。上一轮运行 ``ch3-tabular-resnet-lspr24-zero-train-descriptive-eval-v1``
即踩中该缺陷，本运行是它的更正重跑，使用独立运行身份，不覆盖旧制品。

指标口径全部复用父工具 ``ch3_tabular_resnet_paper_recipe_protocol_a`` 的
``entity_aggregate`` / ``terminal_curve`` / ``budget_points``；实体口径复用
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
from typing import Any, Mapping, Sequence

os.environ.setdefault("OMP_NUM_THREADS", "1")

TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
for _root in (TOOL_DIR, PROJECT_ROOT / "src"):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

import ch3_tabular_resnet_paper_recipe_protocol_a as parent  # noqa: E402

SCHEMA_VERSION = "ch3-tabular-resnet-lspr24-inmemory-descriptive-eval-v1"
RUN_ID = SCHEMA_VERSION
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / f"{SCHEMA_VERSION}.json"
SUPERSEDED_RUN_ID = "ch3-tabular-resnet-lspr24-zero-train-descriptive-eval-v1"
PARENT_RUN_ID = parent.RUN_ID
CELL_ORDER = parent.CELL_ORDER
DR_FPR_GRID = parent.DR_FPR_GRID

T0 = time.time()
_LAST_BEAT = [T0]


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    now = time.time()
    if now - _LAST_BEAT[0] < every and done < total:
        return
    _LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    remaining = (total - done) / max(rate, 1e-9)
    log(
        f"[{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {remaining:.0f}s"
    )


def sha256_file(path: Path, chunk_bytes: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_bytes):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON 顶层必须是对象：{path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path = Path(path)
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
            "schema_version": f"{SCHEMA_VERSION}-status-v1",
            "run_id": RUN_ID,
            "parent_run_id": PARENT_RUN_ID,
            "supersedes_run_id": SUPERSEDED_RUN_ID,
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
# 父运行核验（只读）
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
    """按源清单登记的字节数与 SHA-256 解析冻结制品，并拒绝越界或符号链接。"""

    manifest = load_json(source_manifest_path)
    item = manifest["artifacts"][key]
    path = Path(item["path"]).resolve(strict=True)
    root = source_manifest_path.parent.resolve(strict=True)
    if path.is_symlink() or not path.is_relative_to(root):
        raise RuntimeError(f"冻结制品越界或为符号链接：{key}")
    if path.stat().st_size != int(item["bytes"]) or sha256_file(path) != item["sha256"]:
        raise RuntimeError(f"冻结制品身份不匹配：{key}")
    return path


# --------------------------------------------------------------------------------------
# 胜出臂变换（只在内存复算，绝不落盘）
# --------------------------------------------------------------------------------------


def build_transformer(arm: str, b_state: Path) -> Any:
    from flow_probe.protocol_a_preprocessing import _restore_quantile_transformer

    return None if arm == "A" else _restore_quantile_transformer(b_state)


def apply_arm(raw_batch: Any, arm: str, a_state: Path, b_state: Path, transformer: Any, clip: tuple[float, float]) -> Any:
    """把冻结的胜出臂变换施加到一批原始 83 字段上，与 P6 年度产品同一段函数。"""

    from flow_probe.protocol_a_preprocessing import _transform_a, _transform_b

    a_batch = _transform_a(raw_batch, a_state, clip)
    if arm == "A":
        return a_batch
    return _transform_b(raw_batch, a_batch, b_state, transformer)


def build_source_view_in_memory(
    raw_path: Path,
    *,
    arm: str,
    a_state: Path,
    b_state: Path,
    transformer: Any,
    clip: tuple[float, float],
    row_count: int,
    feature_count: int,
    batch_rows: int,
) -> Any:
    """从冻结 raw83 按胜出臂在内存重建源年视图，只驻内存。"""

    import numpy as np

    raw = np.load(raw_path, mmap_mode="r", allow_pickle=False)
    if raw.shape != (row_count, feature_count):
        raise RuntimeError(f"源年 Raw83 形状不符：{raw.shape}")
    view = np.empty((row_count, feature_count), dtype="<f4")
    started = time.time()
    for start in range(0, row_count, batch_rows):
        stop = min(start + batch_rows, row_count)
        view[start:stop] = apply_arm(np.asarray(raw[start:stop]), arm, a_state, b_state, transformer, clip)
        beat("LSPR23/视图重建", stop, row_count, started)
    return view


def compare_view_with_sealed_product(view: Any, sealed_path: Path, sealed_sha256: str) -> dict[str, Any]:
    """把重建的源年视图与已封印视图逐单元比对，要求 mismatched_cells 为零。"""

    import numpy as np

    published = np.load(sealed_path, mmap_mode="r", allow_pickle=False)
    if published.shape != view.shape:
        raise RuntimeError(f"封印源年视图形状不符：{published.shape}")
    block = 1_048_576
    mismatched = 0
    started = time.time()
    for start in range(0, view.shape[0], block):
        stop = min(start + block, view.shape[0])
        mismatched += int(np.count_nonzero(np.asarray(published[start:stop]) != view[start:stop]))
        beat("LSPR23/视图逐单元比对", stop, view.shape[0], started)
    return {
        "sealed_view_path": str(sealed_path),
        "sealed_view_sha256": sealed_sha256,
        "compared_cells": int(view.shape[0]) * int(view.shape[1]),
        "mismatched_cells": mismatched,
        "passed": mismatched == 0,
    }


# --------------------------------------------------------------------------------------
# 数据身份核验
# --------------------------------------------------------------------------------------


def verify_data_identity(config: Mapping[str, Any], parent_receipt: Mapping[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pyarrow.parquet as pq

    from flow_probe.protocol_a_raw83 import _arrow_schema_identity

    cache_root = Path(config["cache"]["root"])
    contract = config["contract"]
    arm = str(parent_receipt["input_arm"])
    target_config_path = Path(config["target_materialization_config"])
    target_config = load_json(target_config_path)
    source_manifest_path = Path(config["source_product"]["dataset_manifest"])
    artifacts = load_json(source_manifest_path)["artifacts"]
    checks: list[dict[str, Any]] = []

    def record(name: str, observed: Any, expected: Any, note: str, *, blocking: bool) -> None:
        checks.append(
            {
                "check": name,
                "observed": observed,
                "expected": expected,
                "passed": observed == expected,
                "blocking": blocking,
                "note": note,
            }
        )

    log("核验：LSPR24 序列数组对目标物化配置的冻结哈希")
    product = target_config["year_product"]
    sequence_arrays = product["sequence_arrays"]
    for name in ("I24", "M24"):
        declared = Path(sequence_arrays[f"{name}_path"])
        local = cache_root / f"{name}.npy"
        if declared.resolve() != local.resolve():
            raise RuntimeError(f"{name} 缓存路径与目标物化配置声明不一致：{declared}")
        record(
            f"frozen_{name}_sha256",
            sha256_file(local),
            str(sequence_arrays[f"{name}_sha256"]),
            "目标年物化配置直接把该缓存文件登记为冻结序列数组",
            blocking=True,
        )

    log("核验：LSPR24 Parquet 的字节数、摘要、行数、行组、字段与物理模式")
    parquet_path = Path(product["parquet_path"])
    record("frozen_parquet_bytes", int(parquet_path.stat().st_size), int(product["expected_bytes"]), "冻结年度 Parquet 字节数", blocking=True)
    record("frozen_parquet_sha256", sha256_file(parquet_path), str(product["expected_sha256"]), "冻结年度 Parquet 内容摘要", blocking=True)
    parquet_file = pq.ParquetFile(parquet_path)
    record("frozen_parquet_rows", int(parquet_file.metadata.num_rows), int(product["expected_rows"]), "冻结年度 Parquet 行数", blocking=True)
    record("frozen_parquet_row_groups", int(parquet_file.metadata.num_row_groups), int(product["expected_row_groups"]), "冻结年度 Parquet 行组数", blocking=True)
    record("frozen_parquet_field_count", int(len(parquet_file.schema_arrow)), int(product["expected_field_count"]), "冻结年度 Parquet 字段数", blocking=True)
    record(
        "frozen_parquet_schema_sha256",
        canonical_sha256(_arrow_schema_identity(parquet_file.schema_arrow)),
        str(product["expected_schema_sha256"]),
        "冻结年度 Parquet 物理模式摘要",
        blocking=True,
    )
    record("frozen_parquet_rows_equals_contract", int(parquet_file.metadata.num_rows), int(contract["n_flow"]), "Parquet 行数等于合同流数", blocking=True)

    log("核验：源年冻结 raw83、两份变换状态与胜出臂封印视图")
    for key in ("source_raw83", "candidate_a_state", "candidate_b_state", f"source_view_{arm.lower()}", "I23", "M23"):
        record(
            f"source_{key}_sha256",
            sha256_file(Path(artifacts[key]["path"])),
            str(artifacts[key]["sha256"]),
            f"源年冻结制品 {key} 的内容摘要",
            blocking=True,
        )

    log("核验：LSPR24 缓存数组形状")
    shapes: dict[str, list[int]] = {}
    for name, expected_shape in (
        ("I24", (int(contract["n_sequence"]), int(contract["sequence_width"]))),
        ("M24", (int(contract["n_sequence"]), int(contract["sequence_width"]))),
        ("y24", (int(contract["n_flow"]),)),
        ("t24", (int(contract["n_flow"]),)),
    ):
        values = np.load(cache_root / f"{name}.npy", mmap_mode="r", allow_pickle=False)
        shapes[name] = list(values.shape)
        if tuple(values.shape) != expected_shape:
            raise RuntimeError(f"{name} 形状不符：{values.shape} != {expected_shape}")

    log("披露：被拒绝的 dijk-repro 缓存数组")
    rejected: list[dict[str, Any]] = []
    for name in config["cache"]["rejected_arrays"]:
        path = cache_root / f"{name}.npy"
        rejected.append(
            {
                "array": name,
                "path": str(path),
                "exists": path.is_file(),
                "bytes": int(path.stat().st_size) if path.is_file() else None,
                "opened_by_this_run": False,
            }
        )

    receipt = {
        "schema_version": f"{SCHEMA_VERSION}-data-verification-v1",
        "run_id": RUN_ID,
        "input_arm": arm,
        "cache_root": str(cache_root),
        "parquet_path": str(parquet_path),
        "source_manifest_path": str(source_manifest_path),
        "source_manifest_file_sha256": sha256_file(source_manifest_path),
        "target_materialization_config_sha256": sha256_file(target_config_path),
        "checks": checks,
        "blocking_passed": all(item["passed"] for item in checks if item["blocking"]),
        "observed_shapes": shapes,
        "rejected_cache_arrays": rejected,
        "rejection_reason": config["cache"]["rejection_reason"],
        "parent": {key: value for key, value in parent_receipt.items() if key != "cells"},
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    for item in checks:
        level = "阻断项" if item["blocking"] else "披露项"
        log(f"  {item['check']}（{level}）: {'通过' if item['passed'] else '不通过'}")
    return receipt


# --------------------------------------------------------------------------------------
# 打分：与父工具 score_source 逐句同构
# --------------------------------------------------------------------------------------


def load_cell_model(receipt: Mapping[str, Any], device: Any) -> Any:
    import torch

    model = parent.selected_model(dict(receipt), device)
    model.eval()
    expected_p = float(receipt["selected_p"])
    observed_p = float(model.p.detach().cpu())
    if abs(observed_p - expected_p) > 1e-6:
        raise RuntimeError(f"{receipt['cell']} 回载模型的 p 与封印选择不符：{observed_p} vs {expected_p}")
    if any(parameter.dtype != torch.float32 for parameter in model.parameters()):
        raise RuntimeError(f"{receipt['cell']} 回载参数未保持 FP32")
    return model


def score_source_validation(
    *,
    model: Any,
    view: Any,
    indices_all: Any,
    masks_all: Any,
    validation_rows: Any,
    resolver: Any,
    device: Any,
    profile: Any,
    batch_sequences: int,
    stage: str,
) -> dict[str, Any]:
    """在源年验证区打分，批循环与父工具 ``score_source`` 完全一致（批 64、同一顺序）。"""

    import numpy as np
    import torch

    scores: list[Any] = []
    labels: list[Any] = []
    raw_rows: list[Any] = []
    total = int(len(validation_rows))
    started = time.time()
    with torch.no_grad():
        for start in range(0, total, batch_sequences):
            rows = np.asarray(validation_rows[start : start + batch_sequences], dtype=np.int64)
            indices = np.asarray(indices_all[rows])
            valid = np.asarray(masks_all[rows], dtype=bool)
            features = np.ascontiguousarray(view[indices], dtype=np.float32)
            targets = np.zeros(indices.shape, dtype=np.float32)
            targets[valid] = resolver.resolve(indices[valid]).astype(np.float32, copy=False)
            with parent.precision_module().autocast_context(profile, device.type, torch):
                logits = model(torch.from_numpy(features).to(device), torch.from_numpy(valid).to(device))
            flat = valid.reshape(-1)
            scores.append(torch.sigmoid(logits.float()).cpu().numpy().reshape(-1)[flat])
            labels.append(targets.reshape(-1)[flat])
            raw_rows.append(indices.reshape(-1)[flat])
            beat(stage, min(start + batch_sequences, total), total, started)
    return {
        "scores": np.concatenate(scores),
        "labels": np.concatenate(labels).astype(np.uint8, copy=False),
        "raw_rows": np.concatenate(raw_rows).astype(np.int64, copy=False),
    }


def score_target_sequences(
    *,
    model: Any,
    view: Any,
    indices_all: Any,
    masks_all: Any,
    device: Any,
    profile: Any,
    batch_sequences: int,
    n_flow: int,
    n_sequence: int,
    stage: str,
) -> tuple[Any, dict[str, Any]]:
    """对全部 LSPR24 序列做且只做一次前向，返回按流行号散布的概率。"""

    import numpy as np
    import torch

    scores = np.zeros(n_flow, dtype=np.float32)
    written = 0
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    with torch.no_grad():
        for start in range(0, n_sequence, batch_sequences):
            stop = min(start + batch_sequences, n_sequence)
            batch_indices = np.asarray(indices_all[start:stop])
            batch_valid = np.asarray(masks_all[start:stop]) > 0
            features = np.ascontiguousarray(view[batch_indices], dtype=np.float32)
            values = torch.from_numpy(features).to(device)
            valid = torch.from_numpy(np.ascontiguousarray(batch_valid)).to(device)
            with parent.precision_module().autocast_context(profile, device.type, torch):
                logits = model(values, valid)
            probabilities = torch.sigmoid(logits.float()).cpu().numpy()
            flat = batch_valid.reshape(-1)
            scores[batch_indices.reshape(-1)[flat]] = probabilities.reshape(-1)[flat]
            written += int(flat.sum())
            beat(stage, stop, n_sequence, started)
    if written != n_flow:
        raise RuntimeError(f"打分覆盖流数不符：{written} != {n_flow}")
    wall_seconds = time.time() - started
    resources = {
        "pure_inference_wall_seconds": wall_seconds,
        "inference_gpu_hours": wall_seconds / 3600.0,
        "sequences_scored": n_sequence,
        "flows_scored": n_flow,
        "flows_per_second": n_flow / max(wall_seconds, 1e-12),
        "parameter_count": int(sum(item.numel() for item in model.parameters())),
        "resource_contention_note": "同卡可能存在其他进程，时间与显存按并发条件实测记录",
    }
    if device.type == "cuda":
        resources["peak_gpu_allocated_mib"] = torch.cuda.max_memory_allocated(device) / 2**20
        resources["peak_gpu_reserved_mib"] = torch.cuda.max_memory_reserved(device) / 2**20
    return scores, resources


# --------------------------------------------------------------------------------------
# 指标
# --------------------------------------------------------------------------------------


def cell_metrics(cell: str, receipt: Mapping[str, Any], scores: Any, labels: Any, entities: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    """完全复用父工具的聚合与曲线函数，保证与已封印源年读数同源。"""

    import numpy as np
    from sklearn.metrics import average_precision_score

    started = time.time()
    main_p = receipt["selected_p"] if parent.CELLS[cell]["block_auxiliary_objective"] else None
    _, entity_labels, entity_scores = parent.entity_aggregate(scores, labels, entities, main_p)
    _, max_labels, max_scores = parent.entity_aggregate(scores, labels, entities, None)
    if not np.array_equal(entity_labels, max_labels):
        raise RuntimeError(f"{cell} 两条聚合路径的实体标签不一致")

    curve = parent.terminal_curve(entity_scores, entity_labels)
    maximum_curve = parent.terminal_curve(max_scores, max_labels)
    metrics = {
        "cell": cell,
        "causal_prefix_aggregation": parent.CELLS[cell]["causal_prefix_aggregation"],
        "block_auxiliary_objective": parent.CELLS[cell]["block_auxiliary_objective"],
        "entity_aggregation_p": None if main_p is None else float(main_p),
        "entity_score_semantics": ("maximum_flow_probability" if main_p is None else "learned_lp_pool_over_entity_flows"),
        "entity_and_maximum_entity_identical_by_construction": main_p is None,
        "flow_count": int(labels.size),
        "positive_flow_count": int(labels.sum()),
        "flow_average_precision": float(average_precision_score(labels, scores)),
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


def curve_to_arrays(curve: list[dict[str, Any]]) -> dict[str, Any]:
    import numpy as np

    return {
        "threshold": np.array([np.nan if item["threshold"] is None else item["threshold"] for item in curve], dtype=np.float64),
        "false_positive_entities": np.array([item["false_positive_entities"] for item in curve], dtype=np.int64),
        "actual_fpr": np.array([item["actual_fpr"] for item in curve], dtype=np.float64),
        "detected_positive_entities": np.array([item["detected_positive_entities"] for item in curve], dtype=np.int64),
        "detection_rate": np.array([item["detection_rate"] for item in curve], dtype=np.float64),
    }


def compact_readouts(metrics: Mapping[str, Any], key: str) -> list[dict[str, Any]]:
    readouts: list[dict[str, Any]] = []
    for nominal in DR_FPR_GRID:
        point = metrics[key][f"fpr_{nominal:g}"]
        readouts.append(
            {
                "nominal_fpr": point["nominal_fpr"],
                "integer_false_positive_budget": point["integer_false_positive_budget"],
                "achievable_fpr": point["actual_fpr"],
                "false_positive_entities": point["false_positive_entities"],
                "detection_rate": point["detection_rate"],
                "detected_positive_entities": point["detected_positive_entities"],
                "threshold": point["threshold"],
            }
        )
    return readouts


def compact_cell_summary(cell: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cell": cell,
        "flow_count": metrics["flow_count"],
        "entity_count": metrics["entity_count"],
        "positive_entity_count": metrics["positive_entity_count"],
        "entity_aggregation_p": metrics["entity_aggregation_p"],
        "entity_average_precision": metrics["entity_average_precision"],
        "maximum_entity_average_precision": metrics["maximum_entity_average_precision"],
        "flow_average_precision": metrics["flow_average_precision"],
        "terminal_budget_readouts": compact_readouts(metrics, "six_actual_fpr_points"),
        "maximum_pool_budget_readouts": compact_readouts(metrics, "six_actual_fpr_points_maximum_pool"),
    }


# --------------------------------------------------------------------------------------
# 源年自检：同一套打分与聚合代码复算四格并与封印对表
# --------------------------------------------------------------------------------------


def action_selfcheck(config: Mapping[str, Any], parent_receipt: Mapping[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch

    contract = config["contract"]
    arm = str(parent_receipt["input_arm"])
    source_manifest_path = Path(config["source_product"]["dataset_manifest"])
    artifacts = load_json(source_manifest_path)["artifacts"]
    clip = tuple(float(value) for value in contract["transform_clip"])
    a_state = resolve_state_artifact(source_manifest_path, "candidate_a_state")
    b_state = resolve_state_artifact(source_manifest_path, "candidate_b_state")
    transformer = build_transformer(arm, b_state)

    log(f"自检：从源年冻结 raw83 重建胜出臂 {arm} 视图")
    view = build_source_view_in_memory(
        resolve_state_artifact(source_manifest_path, "source_raw83"),
        arm=arm,
        a_state=a_state,
        b_state=b_state,
        transformer=transformer,
        clip=clip,
        row_count=int(contract["source_row_count"]),
        feature_count=int(contract["raw_feature"]),
        batch_rows=int(config["evaluation"]["transform_batch_rows"]),
    )
    sealed_key = f"source_view_{arm.lower()}"
    view_comparison = compare_view_with_sealed_product(
        view, Path(artifacts[sealed_key]["path"]), str(artifacts[sealed_key]["sha256"])
    )
    log(f"自检：视图逐单元比对 mismatched_cells={view_comparison['mismatched_cells']}")
    if not view_comparison["passed"]:
        raise RuntimeError("重建的源年胜出臂视图与封印视图不一致，停止自检")

    parent_config = load_json(Path(config["parent"]["config_path"]))
    api = parent.raw83_module()
    dataset = api.open_protocol_a_dataset(parent_config["paths"]["source_dataset_manifest"], "LSPR23", "validate", arm=arm)
    validation_rows = np.load(parent.artifact_path(dataset, "validation_rows"), mmap_mode="r", allow_pickle=False)
    if int(validation_rows.size) != int(contract["validation_sequence_count"]):
        raise RuntimeError(f"源年验证序列数不符：{validation_rows.size}")
    resolver = dataset.open_label_resolver(parent.stage_token(parent_config, "validate"))
    indices_all = np.load(parent.artifact_path(dataset, "I23"), mmap_mode="r", allow_pickle=False)
    masks_all = np.load(parent.artifact_path(dataset, "M23"), mmap_mode="r", allow_pickle=False)
    entity_all = np.load(parent.artifact_path(dataset, "source_flow_entity_id"), mmap_mode="r", allow_pickle=False)

    device = parent.resolve_device()
    profile = parent.precision_module().get_profile(parent.load_json(parent.precision_contract_path()), parent.PRECISION_PROFILE_ID)
    tolerance = float(config["evaluation"]["selfcheck_metric_tolerance"])
    batch_sequences = int(config["evaluation"]["selfcheck_batch_sequences"])
    comparisons: list[dict[str, Any]] = []
    for cell in config["evaluation"]["cells"]:
        log(f"自检：加载封印 {cell} 并在源年验证区复算")
        selection = parent_receipt["cells"][cell]["selection"]
        model = load_cell_model(selection, device)
        scored = score_source_validation(
            model=model,
            view=view,
            indices_all=indices_all,
            masks_all=masks_all,
            validation_rows=validation_rows,
            resolver=resolver,
            device=device,
            profile=profile,
            batch_sequences=batch_sequences,
            stage=f"LSPR23/{cell}打分",
        )
        entities = np.asarray(entity_all[scored["raw_rows"]])
        metrics, _ = cell_metrics(cell, selection, scored["scores"], scored["labels"], entities)
        sealed = parent_receipt["cells"][cell]["source_validation"]
        entry: dict[str, Any] = {"cell": cell, "metrics": {}}
        for key in ("flow_average_precision", "entity_average_precision", "maximum_entity_average_precision"):
            difference = abs(float(metrics[key]) - float(sealed[key]))
            entry["metrics"][key] = {
                "recomputed": metrics[key],
                "sealed": sealed[key],
                "absolute_difference": difference,
                "exactly_zero": difference == 0.0,
                "within_tolerance": difference <= tolerance,
            }
        sealed_points = sealed["six_actual_fpr_points"]
        budget_differences: list[dict[str, Any]] = []
        for nominal in DR_FPR_GRID:
            name = f"fpr_{nominal:g}"
            recomputed_point = metrics["six_actual_fpr_points"][name]
            sealed_point = sealed_points[name]
            budget_differences.append(
                {
                    "nominal_fpr": nominal,
                    "actual_fpr_absolute_difference": abs(float(recomputed_point["actual_fpr"]) - float(sealed_point["actual_fpr"])),
                    "detection_rate_absolute_difference": abs(
                        float(recomputed_point["detection_rate"]) - float(sealed_point["detection_rate"])
                    ),
                }
            )
        entry["six_actual_fpr_points_differences"] = budget_differences
        entry["maximum_absolute_difference"] = max(
            [item["absolute_difference"] for item in entry["metrics"].values()]
            + [item["actual_fpr_absolute_difference"] for item in budget_differences]
            + [item["detection_rate_absolute_difference"] for item in budget_differences]
        )
        entry["all_within_tolerance"] = entry["maximum_absolute_difference"] <= tolerance
        entry["all_exactly_zero"] = entry["maximum_absolute_difference"] == 0.0
        comparisons.append(entry)
        log(
            f"自检：{cell} 实体AP 复算 {metrics['entity_average_precision']:.12f} "
            f"对封印 {float(sealed['entity_average_precision']):.12f}，最大绝对差 {entry['maximum_absolute_difference']:.3g}"
        )
        del model, scored, entities, metrics
        if device.type == "cuda":
            torch.cuda.empty_cache()

    receipt = {
        "schema_version": f"{SCHEMA_VERSION}-selfcheck-v1",
        "run_id": RUN_ID,
        "input_arm": arm,
        "view_comparison": view_comparison,
        "metric_tolerance": tolerance,
        "batch_sequences": batch_sequences,
        "validation_sequence_count": int(validation_rows.size),
        "cells": comparisons,
        "all_passed": all(item["all_within_tolerance"] for item in comparisons),
        "all_exactly_zero": all(item["all_exactly_zero"] for item in comparisons),
        "peak_process_rss_mib": process_peak_rss_mib(),
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    del view
    return receipt


# --------------------------------------------------------------------------------------
# 目标年：直读冻结 Parquet，在内存内重建视图、实体、开始时刻与标签
# --------------------------------------------------------------------------------------


def read_target_year(config: Mapping[str, Any], parent_receipt: Mapping[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pyarrow.parquet as pq

    from dijk2026_replication.dijk_fields import DIJK_FEATURES
    from flow_probe.protocol_a_raw83 import (
        IP_COLUMNS,
        LABEL_COLUMN,
        TIME_START_COLUMN,
        _arrow_to_float64,
        _arrow_to_int64,
        _batch_column,
        _canonicalize_raw83,
        _parse_binary_labels,
    )

    contract = config["contract"]
    arm = str(parent_receipt["input_arm"])
    n_flow = int(contract["n_flow"])
    width = int(contract["raw_feature"])
    if len(DIJK_FEATURES) != width:
        raise RuntimeError("Dijk 字段数与冻结宽度不符")
    product = load_json(Path(config["target_materialization_config"]))["year_product"]
    parquet_path = Path(product["parquet_path"])
    if sha256_file(parquet_path) != product["expected_sha256"]:
        raise RuntimeError("冻结年度 Parquet SHA-256 不符")

    source_manifest_path = Path(config["source_product"]["dataset_manifest"])
    a_state = resolve_state_artifact(source_manifest_path, "candidate_a_state")
    b_state = resolve_state_artifact(source_manifest_path, "candidate_b_state")
    transformer = build_transformer(arm, b_state)
    clip = tuple(float(value) for value in contract["transform_clip"])

    view = np.empty((n_flow, width), dtype="<f4")
    entity_key = np.empty(n_flow, dtype=object)
    flow_time = np.empty(n_flow, dtype=np.int64)
    flow_labels = np.empty(n_flow, dtype=np.uint8)
    raw_content_digest = hashlib.sha256()
    view_content_digest = hashlib.sha256()
    label_digest = hashlib.sha256()
    disclosure: dict[str, Any] = {}
    disclosure_rows = int(config["evaluation"]["disclosure_compare_rows"])

    parquet_file = pq.ParquetFile(parquet_path)
    required = list(DIJK_FEATURES) + [*IP_COLUMNS, TIME_START_COLUMN, LABEL_COLUMN]
    if not set(required).issubset(parquet_file.schema_arrow.names):
        raise RuntimeError("冻结年度 Parquet 缺少合法投影字段")
    batch_rows = int(config["evaluation"]["parquet_batch_rows"])
    offset = 0
    started = time.time()
    for row_group in range(parquet_file.metadata.num_row_groups):
        for batch in parquet_file.iter_batches(batch_size=batch_rows, row_groups=[row_group], columns=required, use_threads=False):
            count = batch.num_rows
            stop = offset + count
            values = np.empty((count, width), dtype=np.float64)
            for feature_index, name in enumerate(DIJK_FEATURES):
                values[:, feature_index] = _arrow_to_float64(_batch_column(batch, name))
            raw_batch, _, _, _ = _canonicalize_raw83(values)
            del values
            winning_batch = apply_arm(raw_batch, arm, a_state, b_state, transformer, clip)
            view[offset:stop] = winning_batch
            raw_content_digest.update(raw_batch.tobytes(order="C"))
            view_content_digest.update(np.ascontiguousarray(winning_batch).tobytes(order="C"))
            if offset == 0:
                disclosure = compare_first_batch_with_rejected_cache(
                    raw_batch, Path(config["cache"]["root"]) / "X24.npy", min(disclosure_rows, count)
                )
            source_ip = tuple(str(value) for value in _batch_column(batch, IP_COLUMNS[0]).to_pylist())
            destination_ip = tuple(str(value) for value in _batch_column(batch, IP_COLUMNS[1]).to_pylist())
            entity_key[offset:stop] = np.fromiter(
                (f"{left}|{right}" if left <= right else f"{right}|{left}" for left, right in zip(source_ip, destination_ip, strict=True)),
                dtype=object,
                count=count,
            )
            flow_time[offset:stop] = _arrow_to_int64(_batch_column(batch, TIME_START_COLUMN))
            labels = _parse_binary_labels(_batch_column(batch, LABEL_COLUMN).to_pylist())
            flow_labels[offset:stop] = labels
            label_digest.update(labels.tobytes(order="C"))
            offset = stop
            beat("LSPR24/Parquet直读与视图重建", offset, n_flow, started)
    if offset != n_flow:
        raise RuntimeError(f"冻结年度 Parquet 行数不符：{offset:,}")
    if not np.isfinite(view).all():
        raise RuntimeError("重建的 LSPR24 胜出臂视图含非有限值")

    log("LSPR24：按无向地址对口径归并实体")
    _, entity = np.unique(entity_key, return_inverse=True)
    entity = entity.astype(np.int64, copy=False)
    del entity_key
    entity_count = int(entity.max()) + 1
    if entity_count != int(contract["n_entity"]):
        raise RuntimeError(f"LSPR24 实体数应为 {int(contract['n_entity']):,}，实为 {entity_count:,}")
    entity_labels = np.zeros(entity_count, dtype=np.int8)
    np.maximum.at(entity_labels, entity, flow_labels.astype(np.int8, copy=False))
    positive_entities = int(entity_labels.sum())
    if positive_entities != int(contract["n_positive_entity"]):
        raise RuntimeError(f"LSPR24 正实体数应为 {int(contract['n_positive_entity'])}，实为 {positive_entities}")
    flow_positive_rate = float(np.mean(flow_labels, dtype=np.float64))
    if abs(flow_positive_rate - float(contract["flow_positive_rate"])) >= 1e-9:
        raise RuntimeError(f"LSPR24 逐流正例率不符：{flow_positive_rate:.12f}")

    cache_root = Path(config["cache"]["root"])
    cache_labels = np.asarray(np.load(cache_root / "y24.npy", mmap_mode="r", allow_pickle=False))
    cache_times = np.asarray(np.load(cache_root / "t24.npy", mmap_mode="r", allow_pickle=False))
    label_alignment = bool(np.array_equal(cache_labels.astype(np.uint8), flow_labels))
    time_alignment = bool(np.all(cache_times == flow_time))
    del cache_labels, cache_times
    if not (label_alignment and time_alignment):
        raise RuntimeError("冻结 Parquet 与缓存的标签或开始时刻不对齐，I24/M24 无法用于索引 Parquet 行")

    receipt = {
        "parquet_path": str(parquet_path),
        "parquet_sha256": str(product["expected_sha256"]),
        "input_arm": arm,
        "row_count": n_flow,
        "raw_content_sha256": raw_content_digest.hexdigest(),
        "winning_view_content_sha256": view_content_digest.hexdigest(),
        "label_content_sha256": label_digest.hexdigest(),
        "entity_key_recipe": contract["entity_key_recipe"],
        "entity_count": entity_count,
        "positive_entity_count": positive_entities,
        "flow_positive_rate": flow_positive_rate,
        "cache_y24_matches_parquet_labels": label_alignment,
        "cache_t24_matches_parquet_start_time": time_alignment,
        "rejected_cache_x24_disclosure": disclosure,
        "persisted_rows": 0,
    }
    reference = config.get("cross_reference")
    if isinstance(reference, dict):
        receipt["cross_reference"] = {
            "run_id": reference.get("run_id"),
            "note": reference.get("note"),
            "raw_content_sha256_matches": receipt["raw_content_sha256"] == reference.get("target_raw_content_sha256"),
            "label_content_sha256_matches": receipt["label_content_sha256"] == reference.get("target_label_content_sha256"),
            "candidate_b_view_content_sha256_matches": (
                receipt["winning_view_content_sha256"] == reference.get("target_candidate_b_view_content_sha256")
            ),
            "winning_arm_is_b": arm == "B",
            "blocking": False,
        }
        log(
            "LSPR24 交叉核对（披露项）："
            f"raw={receipt['cross_reference']['raw_content_sha256_matches']} "
            f"label={receipt['cross_reference']['label_content_sha256_matches']} "
            f"viewB={receipt['cross_reference']['candidate_b_view_content_sha256_matches']}"
        )
    log(f"LSPR24：实体 {entity_count:,}，正实体 {positive_entities}，逐流正例率 {flow_positive_rate:.14f}")
    return {"view": view, "flow_entity": entity, "flow_time": flow_time, "flow_labels": flow_labels, "receipt": receipt}


def compare_first_batch_with_rejected_cache(raw_batch: Any, cache_path: Path, rows: int) -> dict[str, Any]:
    """披露性对照：证明缓存 X24 不是 Parquet 的 83 字段原值。只读前若干行。"""

    import numpy as np

    if not cache_path.is_file():
        return {"cache_path": str(cache_path), "exists": False}
    cached = np.asarray(np.load(cache_path, mmap_mode="r", allow_pickle=False)[:rows], dtype=np.float64)
    fresh = np.asarray(raw_batch[:rows], dtype=np.float64)
    finite = np.isfinite(cached) & np.isfinite(fresh)
    difference = np.abs(cached - fresh)
    return {
        "cache_path": str(cache_path),
        "exists": True,
        "compared_rows": int(rows),
        "differing_finite_cells": int(np.count_nonzero(finite & (cached != fresh))),
        "maximum_absolute_difference_over_finite_cells": float(difference[finite].max()) if finite.any() else None,
        "cache_is_dijk_raw83": bool(np.array_equal(cached, fresh)),
        "conclusion": "缓存 X24 不是 Dijk 83 字段原值，本运行不使用它",
    }


def load_target_sequences(config: Mapping[str, Any]) -> tuple[Any, Any]:
    import numpy as np

    contract = config["contract"]
    cache_root = Path(config["cache"]["root"])
    n_flow = int(contract["n_flow"])
    indices = np.asarray(np.load(cache_root / "I24.npy", mmap_mode="r", allow_pickle=False))
    masks = np.asarray(np.load(cache_root / "M24.npy", mmap_mode="r", allow_pickle=False)) > 0
    expected = (int(contract["n_sequence"]), int(contract["sequence_width"]))
    if indices.shape != expected or masks.shape != expected:
        raise RuntimeError("LSPR24 序列索引或掩码形状不符")
    if int(masks.sum()) != n_flow:
        raise RuntimeError("LSPR24 序列有效位置数不等于流数")
    if int(indices[masks].min()) < 0 or int(indices[masks].max()) >= n_flow:
        raise RuntimeError("LSPR24 序列索引越界")
    occurrence = np.zeros(n_flow, dtype=np.int32)
    np.add.at(occurrence, indices[masks], 1)
    if int((occurrence == 1).sum()) != n_flow:
        raise RuntimeError("LSPR24 序列索引没有恰好覆盖每条流一次")
    del occurrence
    return indices, masks


# --------------------------------------------------------------------------------------
# 单元制品
# --------------------------------------------------------------------------------------


def save_unit(output_root: Path, cell: str, identity: dict[str, Any], metrics: dict[str, Any], arrays: dict[str, Any], resources: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    unit_root = output_root / "target-cells" / cell
    if unit_root.exists():
        raise RuntimeError(f"{cell} 单元目录已存在，拒绝覆盖")
    temporary_root = unit_root.with_name(f"{cell}.partial.{os.getpid()}")
    temporary_root.mkdir(parents=True, exist_ok=False)
    curve_path = temporary_root / "curves.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
    aggregate = {
        "schema_version": f"{SCHEMA_VERSION}-unit-v1",
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


def load_completed_unit(output_root: Path, cell: str, identity: dict[str, Any]) -> dict[str, Any] | None:
    unit_root = output_root / "target-cells" / cell
    if not unit_root.exists():
        return None
    aggregate_path = unit_root / "aggregate.json"
    curve_path = unit_root / "curves.npz"
    if not aggregate_path.is_file() or not curve_path.is_file():
        raise RuntimeError(f"{cell} 存在不完整单元目录")
    aggregate = load_json(aggregate_path)
    if aggregate.get("identity") != identity or aggregate.get("complete") is not True:
        raise RuntimeError(f"{cell} 完成单元身份不符")
    if aggregate.get("curve_artifact", {}).get("sha256") != sha256_file(curve_path):
        raise RuntimeError(f"{cell} 曲线制品摘要不符")
    log(f"{cell} 复用身份与摘要一致的完成单元，不重复评价")
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
            "schema_version": f"{SCHEMA_VERSION}-manifest-v1",
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
# 目标年评价
# --------------------------------------------------------------------------------------


def action_evaluate(config: Mapping[str, Any], parent_receipt: Mapping[str, Any], verification: Mapping[str, Any]) -> dict[str, Any]:
    import torch

    output_root = Path(config["paths"]["output_root"])
    arm = str(parent_receipt["input_arm"])
    identity_common = {
        "schema_version": f"{SCHEMA_VERSION}-unit-identity-v1",
        "run_id": RUN_ID,
        "parent_run_id": PARENT_RUN_ID,
        "input_arm": arm,
        "parent_source_cells_sealed_sha256": parent_receipt["source_cells_sealed_sha256"],
        "data_verification_receipt_sha256": verification["receipt_sha256"],
        "evaluation_code_sha256": sha256_file(Path(__file__).resolve()),
        "parent_code_sha256": sha256_file(Path(parent.__file__).resolve()),
    }
    identities = {
        cell: {**identity_common, "cell": cell, "parent_checkpoint_sha256": parent_receipt["cells"][cell]["checkpoint_sha256"]}
        for cell in CELL_ORDER
    }
    completed = {
        cell: unit for cell in CELL_ORDER if (unit := load_completed_unit(output_root, cell, identities[cell])) is not None
    }

    reused_units = len(completed)
    evaluation_calls = 0
    run_started = time.time()
    target_receipt: dict[str, Any] | None = None
    if len(completed) < len(CELL_ORDER):
        write_status(output_root, "running", "target-context", None, "直读冻结 Parquet 并在内存重建目标年视图")
        target = read_target_year(config, parent_receipt)
        target_receipt = target["receipt"]
        atomic_json(output_root / "target-year-read.json", target_receipt)
        indices, masks = load_target_sequences(config)
        device = parent.resolve_device()
        profile = parent.precision_module().get_profile(parent.load_json(parent.precision_contract_path()), parent.PRECISION_PROFILE_ID)
        batch_sequences = int(config["evaluation"]["target_batch_sequences"])
        for cell in CELL_ORDER:
            if cell in completed:
                continue
            write_status(output_root, "running", "target-evaluation", None, f"{cell} 单次前向与聚合")
            selection = parent_receipt["cells"][cell]["selection"]
            model = load_cell_model(selection, device)
            scores, resources = score_target_sequences(
                model=model,
                view=target["view"],
                indices_all=indices,
                masks_all=masks,
                device=device,
                profile=profile,
                batch_sequences=batch_sequences,
                n_flow=int(config["contract"]["n_flow"]),
                n_sequence=int(config["contract"]["n_sequence"]),
                stage=f"LSPR24/{cell}打分",
            )
            evaluation_calls += 1
            del model
            if device.type == "cuda":
                torch.cuda.empty_cache()
            metrics, arrays = cell_metrics(cell, selection, scores, target["flow_labels"], target["flow_entity"])
            log(
                f"{cell} 实体AP={metrics['entity_average_precision']:.12f} "
                f"最大池化实体AP={metrics['maximum_entity_average_precision']:.12f} "
                f"逐流AP={metrics['flow_average_precision']:.12f}"
            )
            completed[cell] = save_unit(output_root, cell, identities[cell], metrics, arrays, resources)
            del scores, arrays
        del target, indices, masks
    else:
        path = output_root / "target-year-read.json"
        target_receipt = load_json(path) if path.is_file() else None

    if set(completed) != set(CELL_ORDER):
        raise RuntimeError("四格描述性评价未全部完成")
    if evaluation_calls + reused_units != len(CELL_ORDER):
        raise RuntimeError(f"每格恰好一次评价的计数不符：本进程评价={evaluation_calls} 复用={reused_units}")

    summaries = [compact_cell_summary(cell, completed[cell]["metrics"]) for cell in CELL_ORDER]
    result = {
        "schema_version": f"{SCHEMA_VERSION}-target-descriptive-evaluation-v1",
        "run_id": RUN_ID,
        "display_name": config["display_name"],
        "parent_run_id": PARENT_RUN_ID,
        "supersedes_run_id": SUPERSEDED_RUN_ID,
        "supersede_reason": "旧运行从 dijk-repro 缓存 X24.npy 取特征，实测该数组不是 Dijk 83 字段原值",
        "dataset": "LSPR24",
        "evaluation_role": "previously_accessed_target_year_descriptive_evaluation",
        "boundary": config["boundary"],
        "input_arm": arm,
        "optimizer_candidate": parent_receipt["optimizer_candidate"],
        "cell_order": list(CELL_ORDER),
        "dr_fpr_grid": list(DR_FPR_GRID),
        "rows": [
            {
                "cell": cell,
                "metrics": completed[cell]["metrics"],
                "resource": completed[cell]["resource"],
                "source_validation_reference": parent_receipt["cells"][cell]["source_validation"],
            }
            for cell in CELL_ORDER
        ],
        "summaries": summaries,
        "entity_contract": {
            "entity_key": "unordered_source_destination_ip_pair_grouping_only",
            "entity_count": int(config["contract"]["n_entity"]),
            "positive_entity_count": int(config["contract"]["n_positive_entity"]),
            "flow_positive_rate": float(config["contract"]["flow_positive_rate"]),
            "source_of_truth": config["contract"]["entity_key_source_of_truth"],
        },
        "target_year_read": target_receipt,
        "data_verification_receipt_sha256": verification["receipt_sha256"],
        "parent": {key: value for key, value in parent_receipt.items() if key != "cells"},
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
        "resource": {"controller_wall_seconds": time.time() - run_started, "peak_process_rss_mib": process_peak_rss_mib()},
    }
    result["result_sha256"] = canonical_sha256(result)
    return result


# --------------------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------------------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--action", choices=("verify", "selfcheck", "evaluate", "all"), default="all")
    return parser.parse_args(argv)


def run(arguments: argparse.Namespace) -> None:
    config = load_json(arguments.config)
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise RuntimeError("配置模式或运行身份不符")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    parent_root = Path(config["parent"]["run_root"]).resolve(strict=True)
    if parent_root.name != config["parent"]["run_id"]:
        raise RuntimeError("父运行根与登记的父运行身份不符")
    source_manifest_path = Path(config["source_product"]["dataset_manifest"]).resolve(strict=True)

    write_status(output_root, "running", "parent-validation", None, "只读核验四格源年封印与检查点")
    parent_receipt = validate_parent(parent_root, source_manifest_path)
    log(f"父运行核验通过：胜出臂={parent_receipt['input_arm']} 优化器={parent_receipt['optimizer_candidate']}")

    actions = ("verify", "selfcheck", "evaluate") if arguments.action == "all" else (arguments.action,)
    verification_path = output_root / "data-verification.json"
    for action in actions:
        log(f"==== 动作 {action} 开始 ====")
        if action == "verify":
            write_status(output_root, "running", "verify", None, "冻结数据身份核验")
            receipt = verify_data_identity(config, parent_receipt)
            atomic_json(verification_path, receipt)
            if not receipt["blocking_passed"]:
                failed = [item["check"] for item in receipt["checks"] if not item["passed"] and item["blocking"]]
                raise RuntimeError(f"数据身份阻断核验不通过：{failed}")
        elif action == "selfcheck":
            write_status(output_root, "running", "selfcheck", None, "源年验证区复算并与封印对表")
            receipt = action_selfcheck(config, parent_receipt)
            atomic_json(output_root / "source-selfcheck.json", receipt)
            if not receipt["view_comparison"]["passed"]:
                raise RuntimeError("源年视图重建不一致")
            if not receipt["all_passed"]:
                raise RuntimeError("源年复算与封印指标不一致，拒绝进入目标年评价")
        else:
            if not verification_path.is_file():
                raise RuntimeError("缺少数据身份核验收据，先运行 verify")
            verification = load_json(verification_path)
            if not verification.get("blocking_passed"):
                raise RuntimeError("数据身份核验收据未通过")
            result = action_evaluate(config, parent_receipt, verification)
            atomic_json(output_root / "target-results.json", result)
            atomic_json(
                output_root / "target-summary.json",
                {
                    "schema_version": f"{SCHEMA_VERSION}-summary-v1",
                    "run_id": RUN_ID,
                    "target_year_read": result["target_year_read"],
                    "summaries": result["summaries"],
                    "result_sha256": result["result_sha256"],
                },
            )
            write_status(output_root, "complete", "complete", 0, "四格 LSPR24 零物化描述性评价完成")
            build_manifest(output_root)
        log(f"==== 动作 {action} 完成 ====")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    try:
        run(arguments)
        return 0
    except Exception as error:
        try:
            config = load_json(arguments.config)
            output_root = Path(config["paths"]["output_root"])
            output_root.mkdir(parents=True, exist_ok=True)
            write_status(output_root, "failed", "failed", 1, f"{type(error).__name__}: {error}")
        except Exception:
            pass
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
