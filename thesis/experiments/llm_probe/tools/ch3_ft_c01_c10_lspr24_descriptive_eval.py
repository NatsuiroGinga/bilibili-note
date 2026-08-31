#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FT C01/C10 在 LSPR24 上的提前零训练描述性评价。

本入口只消费两个已完成源运行的 ``selected-by-entity.pt``。目标年不拟合、不选轮、
不改阈值、不写检查点，也不把结果反馈给机制或训练配置。C01 与 C10 的历史训练执行
路径不同，因此本制品只能回答提前的目标年描述性问题，不能替代正式同路径四格重跑。

模型、数据、封印变换、目标年实体链和前向全部复用
``ch3_ft_lspr24_descriptive_eval.py`` 的底层函数；本文件只负责两格编排、实际可达 FPR
读数、程序生成基线表和不混池比较。
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np

TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parent
for _root in (TOOL_DIR, PROJECT_ROOT / "src"):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

import ch3_build_metrics_table as metrics_table  # noqa: E402
import ch3_ft_lspr24_descriptive_eval as host  # noqa: E402

RUN_ID = "ch3-ft-c01-c10-lspr24-descriptive-eval-v1"
SCHEMA_VERSION = "ch3-ft-c01-c10-lspr24-descriptive-eval-v1"
CELLS = ("c01", "c10")
SELECTION_ROLE = "entity"
TARGET_POOL = "LSPR24已访问目标年描述性评价池"
TARGET_ROLE = "previously_accessed_target_year_descriptive_evaluation"
FPR_GRID = tuple(float(value) for value in host.base.DR_FPR_GRID)


def load_json(path: Path) -> dict[str, Any]:
    return host.load_json(path)


def atomic_json(path: Path, value: Any) -> None:
    host.atomic_json(path, value)


def canonical_sha256(value: Any) -> str:
    return host.canonical_sha256(value)


def sha256_file(path: Path) -> str:
    return host.sha256_file(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--check-config", action="store_true", help="只核验配置，不读取运行制品")
    parser.add_argument("--resume", action="store_true", help="复用身份与摘要完全一致的已完成评价单元")
    parser.add_argument("--resource-receipt", help="启动器生成的资源准入收据")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != f"{SCHEMA_VERSION}-config" or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    source_cells = config.get("source_cells")
    if not isinstance(source_cells, dict) or tuple(source_cells) != CELLS:
        raise ValueError("只允许按 c01、c10 顺序评价两个已完成源运行")
    expected_runs = {
        "c01": "ch3-ft-c01-entity-ranking-cuda-formal-v1",
        "c10": "ch3-ft-c10-entity-memory-cuda-formal-v1",
    }
    for cell, run_id in expected_runs.items():
        node = source_cells.get(cell, {})
        if node.get("run_id") != run_id or node.get("selection_role") != SELECTION_ROLE:
            raise ValueError(f"{cell} 源运行或选择角色不符")
        if node.get("required_state") != "finished" or node.get("required_source_target_reads") != 0:
            raise ValueError(f"{cell} 源运行完成态或目标年零读取合同不符")
        batch = node.get("target_validation_batch_sequences")
        if not isinstance(batch, int) or batch <= 0:
            raise ValueError(f"{cell} 目标评价批量必须为正整数")
    evaluation = config.get("evaluation", {})
    expected_evaluation = {
        "dataset": "LSPR24",
        "role": TARGET_ROLE,
        "selection_role": SELECTION_ROLE,
        "entity_key": "unordered_source_destination_ip_pair_grouping_only",
        "entity_score": "maximum_flow_probability",
        "maximum_entity_score": "maximum_flow_probability",
        "dr_fpr_grid": list(FPR_GRID),
        "complete_budget_curve": True,
        "target_used_for_selection": False,
        "target_feedback_allowed": False,
    }
    if evaluation != expected_evaluation:
        raise ValueError("目标年评价合同不符")
    isolation = config.get("isolation", {})
    expected_isolation = {
        "training_runs": 0,
        "optimizer_steps": 0,
        "parameter_updates": 0,
        "new_checkpoints_written": 0,
        "source_run_directories_modified": 0,
        "target_data_products_materialized": 0,
        "selection_performed": False,
        "winner": None,
    }
    if isolation != expected_isolation:
        raise ValueError("零训练与目标年隔离合同不符")
    baseline = config.get("baseline_comparison", {})
    if baseline.get("generator_table") != "lspr24-evaluation" or baseline.get("evaluation_pool") != TARGET_POOL:
        raise ValueError("基线表或评价池锚点不符")
    required = baseline.get("required_rows")
    if not isinstance(required, list) or len(required) != 2:
        raise ValueError("必须明确锚定两个强基线")
    expected_names = {"XGBoost＋CPA-ELP", "全容量多层感知机＋完整实体幂平均（BF16）"}
    if {item.get("display_name") for item in required if isinstance(item, dict)} != expected_names:
        raise ValueError("强基线名称不符")
    for item in required:
        if not all(isinstance(item.get(key), str) and item[key] for key in ("display_name", "run_id", "source_schema", "cell")):
            raise ValueError("强基线锚点字段不完整")
    roots = baseline.get("roots")
    if not isinstance(roots, dict) or set(roots) != {"main", "ch4_worktree"}:
        raise ValueError("程序生成基线表的运行根映射不完整")
    paths = config.get("paths", {})
    required_paths = {
        "target_config",
        "output_root",
        "baseline_registry_config",
        "baseline_builder_tool",
    }
    if not required_paths.issubset(paths) or not all(isinstance(paths[key], str) and paths[key] for key in required_paths):
        raise ValueError("路径配置不完整")
    output_root = Path(paths["output_root"])
    for cell in CELLS:
        if output_root == Path(source_cells[cell]["run_root"]):
            raise ValueError("评价输出根不得等于源运行根")


def source_preflight(config: dict[str, Any]) -> tuple[dict[str, Path], dict[str, Any]]:
    cell_runs: dict[str, Path] = {}
    sealed: dict[str, Any] = {}
    for cell in CELLS:
        expected = config["source_cells"][cell]
        root = Path(expected["run_root"])
        receipt = host.load_sealed_selection(root)
        if receipt.get("run_id") != expected["run_id"]:
            raise SystemExit(f"{cell} 选轮收据运行身份不符")
        best = receipt.get("best_by_entity", {})
        checkpoint = root / "checkpoints" / "selected-by-entity.pt"
        if not checkpoint.is_file():
            raise SystemExit(f"{cell} 缺 selected-by-entity.pt")
        cell_runs[cell] = root
        sealed[cell] = {
            "run_id": receipt["run_id"],
            "state": "finished",
            "source_target_reads": 0,
            "selection_role": SELECTION_ROLE,
            "source_entity_ap": best.get("metric"),
            "source_entity_epoch": best.get("epoch"),
            "history_epochs": len(receipt.get("history", [])),
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": sha256_file(checkpoint),
        }
    return cell_runs, sealed


def load_configs_and_agreement(
    config: dict[str, Any], cell_runs: dict[str, Path]
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    configs = host.load_cell_configs(cell_runs)
    shared_getters = {
        "cache_root": lambda value: value["paths"]["cache_root"],
        "input_candidate": lambda value: value["data"]["input_candidate"],
        "sequence_length": lambda value: value["training"]["sequence_length"],
        "device_type": lambda value: value["runtime"]["device_type"],
        "precision_profile_id": lambda value: value["runtime"]["precision_profile_id"],
        "entity_aggregation": lambda value: value["evaluation"]["entity_aggregation"],
        "base_config_sha256": lambda value: value["base"]["config_sha256"],
        "base_tool_sha256": lambda value: value["base"]["tool_sha256"],
    }
    agreement: dict[str, Any] = {}
    for name, getter in shared_getters.items():
        values = {cell: getter(configs[cell]) for cell in CELLS}
        if len({canonical_sha256(value) for value in values.values()}) != 1:
            raise SystemExit(f"C01/C10 在 {name} 上不一致，拒绝混池：{values}")
        agreement[name] = values[CELLS[0]]
    if agreement["entity_aggregation"] != "maximum_over_validation_flows":
        raise SystemExit("C01/C10 不是统一最大实体聚合口径")
    agreement["source_torch_compile"] = {
        cell: configs[cell]["runtime"].get("torch_compile") for cell in CELLS
    }
    agreement["source_validation_batch_sequences"] = {
        cell: int(configs[cell]["training"]["validation_batch_sequences"]) for cell in CELLS
    }
    for cell in CELLS:
        declared_source_batch = int(
            config["source_cells"][cell]["source_validation_batch_sequences"]
        )
        if agreement["source_validation_batch_sequences"][cell] != declared_source_batch:
            raise SystemExit(f"{cell} 源验证批量与配置披露不符")
        declared_override = bool(
            config["source_cells"][cell]["target_batch_override_applied"]
        )
        actual_override = (
            int(config["source_cells"][cell]["target_validation_batch_sequences"])
            != declared_source_batch
        )
        if declared_override != actual_override:
            raise SystemExit(f"{cell} 目标评价批量覆盖披露不实")
    agreement["target_validation_batch_sequences"] = {
        cell: int(config["source_cells"][cell]["target_validation_batch_sequences"])
        for cell in CELLS
    }
    agreement["target_batch_override_applied"] = {
        cell: agreement["target_validation_batch_sequences"][cell]
        != agreement["source_validation_batch_sequences"][cell]
        for cell in CELLS
    }
    agreement["entity_memory_enabled"] = {
        cell: host.dual.entity_memory_enabled_from_config(configs[cell]) for cell in CELLS
    }
    agreement["entity_ranking_enabled"] = {
        cell: host.dual.entity_ranking_enabled_from_config(configs[cell]) for cell in CELLS
    }
    if agreement["entity_memory_enabled"] != {"c01": False, "c10": True}:
        raise SystemExit("C01/C10 的 CEM 开关身份不符")
    if agreement["entity_ranking_enabled"] != {"c01": True, "c10": False}:
        raise SystemExit("C01/C10 的 BER 开关身份不符")
    agreement["formal_cross_cell_fairness_claim_allowed"] = False
    agreement["formal_cross_cell_fairness_reason"] = (
        "历史 C01 与 C10 的 torch.compile 实际训练路径不同；本次只作提前目标年描述"
    )
    return configs, agreement


def load_shared_transform(cell_runs: dict[str, Path]) -> tuple[Any, dict[str, Any]]:
    state_hashes: dict[str, str] = {}
    for cell in CELLS:
        receipt = load_json(cell_runs[cell] / "receipts" / "input-transform.json")
        state_hashes[cell] = str(receipt["state_hash"])
    if len(set(state_hashes.values())) != 1:
        raise SystemExit(f"C01/C10 封印输入变换不一致：{state_hashes}")
    transform_path = cell_runs[CELLS[0]] / "artifacts" / "sealed-input-transform.pkl"
    transform = host.base.load_input_transform(transform_path)
    if transform.state_hash != state_hashes[CELLS[0]]:
        raise SystemExit("封印输入变换对象与收据摘要不一致")
    transform.switch_region("target")
    return transform, {
        "sealed_transform_path": str(transform_path),
        "sealed_transform_file_sha256": sha256_file(transform_path),
        "state_hash": transform.state_hash,
        "state_hash_identical_across_cells": True,
        "per_cell_state_hash": state_hashes,
        "refitted_on_target": False,
    }


def build_current_baseline_table(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    baseline = config["baseline_comparison"]
    registry_path = Path(config["paths"]["baseline_registry_config"])
    builder_path = Path(config["paths"]["baseline_builder_tool"])
    if Path(metrics_table.__file__).resolve() != builder_path.resolve():
        raise SystemExit("导入的指标表程序与配置锚点不是同一文件")
    registry = load_json(registry_path)
    registry_by_name = {
        row.get("display_name"): row
        for row in registry.get("models", [])
        if isinstance(row, dict)
    }
    for anchor in baseline["required_rows"]:
        registered = registry_by_name.get(anchor["display_name"])
        if registered is None:
            raise SystemExit(f"当前来源登记册缺强基线锚点：{anchor['display_name']}")
        for key in ("run_id", "source_schema", "cell"):
            if registered.get(key) != anchor[key]:
                raise SystemExit(f"{anchor['display_name']} 的 {key} 与来源登记册不一致")
        expected_max_cell = anchor.get("maximum_entity_ap_source_cell")
        registered_max_cell = registered.get("max_entity_ap_source_cell", registered.get("cell"))
        if registered_max_cell != expected_max_cell:
            raise SystemExit(
                f"{anchor['display_name']} 最大实体 AP 来源格与来源登记册不一致"
            )
    roots = {name: str(Path(path)) for name, path in baseline["roots"].items()}
    rows, provenance = metrics_table.collect_rows(str(registry_path), roots)
    tables = metrics_table.build_tables(rows)
    baseline_root = output_root / "program-generated-baseline-table"
    metrics_table.write_outputs(tables, str(baseline_root), provenance)
    table_path = baseline_root / "lspr24-evaluation.json"
    table_rows = json.loads(table_path.read_text(encoding="utf-8"))
    if not isinstance(table_rows, list):
        raise SystemExit("程序生成的 LSPR24 基线表顶层不是数组")
    required_rows: dict[str, dict[str, Any]] = {}
    by_name = {
        row.get("display_name"): row for row in table_rows if isinstance(row, dict)
    }
    for anchor in baseline["required_rows"]:
        name = anchor["display_name"]
        row = by_name.get(name)
        if row is None:
            raise SystemExit(f"程序生成基线表缺强制行：{name}")
        if row.get("run_id") != anchor["run_id"]:
            raise SystemExit(f"{name} 运行身份与配置锚点不符")
        if row.get("evaluation_pool") != TARGET_POOL:
            raise SystemExit(f"{name} 不在统一 LSPR24 目标实体池")
        if row.get("pending_reason") is not None:
            raise SystemExit(f"{name} 仍为待补状态：{row['pending_reason']}")
        for metric in ("flow_ap", "entity_ap", "max_entity_ap"):
            if not isinstance(row.get(metric), (int, float)):
                raise SystemExit(f"{name} 缺 {metric}，禁止反推")
        required_rows[name] = row
    comparable = [
        row
        for row in table_rows
        if isinstance(row, dict)
        and row.get("evaluation_pool") == TARGET_POOL
        and row.get("pending_reason") is None
        and isinstance(row.get("entity_ap"), (int, float))
    ]
    excluded = [
        {
            "display_name": row.get("display_name"),
            "pending_reason": row.get("pending_reason"),
            "entity_ap_missing": not isinstance(row.get("entity_ap"), (int, float)),
            "evaluation_pool": row.get("evaluation_pool"),
        }
        for row in table_rows
        if isinstance(row, dict)
        and row.get("evaluation_pool") == TARGET_POOL
        and row not in comparable
    ]
    return {
        "registry_path": str(registry_path),
        "registry_sha256": sha256_file(registry_path),
        "builder_path": str(builder_path),
        "builder_sha256": sha256_file(builder_path),
        "table_path": str(table_path),
        "table_sha256": sha256_file(table_path),
        "provenance_path": str(baseline_root / "provenance.json"),
        "provenance_sha256": sha256_file(baseline_root / "provenance.json"),
        "required_rows": required_rows,
        "comparable_rows": comparable,
        "excluded_target_rows": excluded,
        "all_target_table_row_count": len(table_rows),
        "comparable_entity_ap_row_count": len(comparable),
    }


def actual_reachable_readouts(curve: dict[str, Any]) -> dict[str, Any]:
    realized = np.asarray(curve["realized_fpr"], dtype=np.float64)
    detection = np.asarray(curve["detection_rate"], dtype=np.float64)
    false_positive = np.asarray(curve["n_false_positive_entity"], dtype=np.int64)
    if not (len(realized) == len(detection) == len(false_positive)) or len(realized) == 0:
        raise SystemExit("完整预算曲线字段长度不一致或为空")
    if bool(np.any(realized[1:] < realized[:-1])):
        raise SystemExit("完整预算曲线的实际 FPR 非单调")
    rows: dict[str, Any] = {}
    for nominal in FPR_GRID:
        index = int(np.searchsorted(realized, nominal, side="right") - 1)
        if index < 0:
            rows[f"fpr_{nominal:g}"] = {
                "nominal_target_fpr": nominal,
                "actual_reachable_fpr": 0.0,
                "detection_rate": 0.0,
                "false_positive_entity_count": 0,
                "curve_index": None,
                "zero_point_inserted_for_readout_only": True,
                "interpolated": False,
            }
            continue
        rows[f"fpr_{nominal:g}"] = {
            "nominal_target_fpr": nominal,
            "actual_reachable_fpr": float(realized[index]),
            "detection_rate": float(detection[index]),
            "false_positive_entity_count": int(false_positive[index]),
            "curve_index": index,
            "zero_point_inserted_for_readout_only": False,
            "interpolated": False,
        }
    return rows


def unit_name(cell: str) -> str:
    return f"{cell}-by-entity"


def load_completed_unit(
    output_root: Path, cell: str, identity: dict[str, Any], resume: bool
) -> dict[str, Any] | None:
    root = output_root / "target-cells" / unit_name(cell)
    if not root.exists():
        return None
    if not resume:
        raise SystemExit(f"{unit_name(cell)} 已存在；须显式 --resume")
    aggregate_path = root / "aggregate.json"
    curve_path = root / "complete-alert-budget-curve.npz"
    if not aggregate_path.is_file() or not curve_path.is_file():
        raise SystemExit(f"{unit_name(cell)} 单元不完整")
    aggregate = load_json(aggregate_path)
    if aggregate.get("identity") != identity or aggregate.get("complete") is not True:
        raise SystemExit(f"{unit_name(cell)} 完成单元身份不符")
    if aggregate.get("curve_artifact", {}).get("sha256") != sha256_file(curve_path):
        raise SystemExit(f"{unit_name(cell)} 完整曲线摘要不符")
    return aggregate


def save_unit(
    output_root: Path,
    cell: str,
    identity: dict[str, Any],
    checkpoint: dict[str, Any],
    metrics: dict[str, Any],
    curve: dict[str, Any],
    resources: dict[str, Any],
) -> dict[str, Any]:
    root = output_root / "target-cells" / unit_name(cell)
    if root.exists():
        raise SystemExit(f"{unit_name(cell)} 已存在，拒绝覆盖")
    temporary = root.with_name(f"{root.name}.partial.{os.getpid()}")
    temporary.mkdir(parents=True, exist_ok=False)
    curve_path = temporary / "complete-alert-budget-curve.npz"
    with curve_path.open("wb") as handle:
        np.savez_compressed(handle, **curve)
    aggregate = {
        "schema_version": f"{SCHEMA_VERSION}-unit",
        "cell": cell,
        "selection_role": SELECTION_ROLE,
        "identity": identity,
        "checkpoint": checkpoint,
        "metrics": metrics,
        "resource": resources,
        "isolation": {
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_forward_passes": 1,
            "source_run_directories_modified": 0,
        },
        "curve_artifact": {
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
            "fields": sorted(curve),
        },
        "complete": True,
    }
    atomic_json(temporary / "aggregate.json", aggregate)
    root.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temporary, root)
    return aggregate


def write_status(
    output_root: Path,
    state: str,
    stage: str,
    exit_code: int | None,
    detail: str,
    source_target_reads: dict[str, int] | None,
    target_reads: dict[str, Any] | None,
) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": f"{SCHEMA_VERSION}-status",
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
            "source_run_target_reads": source_target_reads,
            "target_reads": target_reads,
            "target_used_for_selection": False,
            "selection_performed": False,
        },
    )


def compare_baselines(
    completed: dict[str, dict[str, Any]], baseline_receipt: dict[str, Any]
) -> dict[str, Any]:
    required_names = set(baseline_receipt["required_rows"])
    comparable = baseline_receipt["comparable_rows"]
    per_cell: dict[str, Any] = {}
    for cell in CELLS:
        metrics = completed[unit_name(cell)]["metrics"]
        rows = []
        for baseline in comparable:
            comparison: dict[str, Any] = {
                "display_name": baseline.get("display_name"),
                "run_id": baseline.get("run_id"),
                "evaluation_pool": baseline.get("evaluation_pool"),
                "required_strong_baseline": baseline.get("display_name") in required_names,
            }
            for ft_key, baseline_key in (
                ("flow_average_precision", "flow_ap"),
                ("entity_average_precision", "entity_ap"),
                ("maximum_entity_average_precision", "max_entity_ap"),
            ):
                left = metrics.get(ft_key)
                right = baseline.get(baseline_key)
                key = baseline_key
                if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                    comparison[key] = {
                        "comparable": False,
                        "reason": "任一侧指标缺失，未反推",
                    }
                else:
                    comparison[key] = {
                        "comparable": True,
                        "ft": float(left),
                        "baseline": float(right),
                        "difference": float(left) - float(right),
                        "ft_strictly_greater": float(left) > float(right),
                    }
            rows.append(comparison)
        primary_flags = [row["entity_ap"]["ft_strictly_greater"] for row in rows]
        required_flags = [
            row["entity_ap"]["ft_strictly_greater"]
            for row in rows
            if row["required_strong_baseline"]
        ]
        per_cell[cell] = {
            "rows": rows,
            "beats_all_same_pool_rows_with_available_entity_ap": bool(primary_flags) and all(primary_flags),
            "beats_both_required_strong_baselines_on_entity_ap": (
                len(required_flags) == len(required_names) and all(required_flags)
            ),
            "dominance_claimed": False,
            "dominance_note": "逐流、实体、最大实体与完整预算曲线分别报告；实体 AP 胜出不自动推成全指标支配",
        }
    return {
        "evaluation_pool": TARGET_POOL,
        "primary_comparison_metric": "entity_average_precision",
        "strict_operator": ">",
        "per_cell": per_cell,
        "excluded_target_rows": baseline_receipt["excluded_target_rows"],
        "missing_metrics_inferred": False,
        "mixed_pool_comparisons": 0,
        "target_used_for_model_or_checkpoint_selection": False,
    }


def build_manifest(output_root: Path) -> None:
    forbidden = (
        "flow-score",
        "flow_score",
        "entity-score",
        "entity_score",
        ".pt",
        ".pth",
        ".ckpt",
        ".npy",
        ".parquet",
        ".pkl",
    )
    files: dict[str, Any] = {}
    for path in sorted(
        item for item in output_root.rglob("*")
        if item.is_file() and item.name != "artifact-manifest.json"
    ):
        relative = str(path.relative_to(output_root))
        if any(token in relative.lower() for token in forbidden):
            raise SystemExit(f"运行根出现禁止制品：{relative}")
        files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(
        output_root / "artifact-manifest.json",
        {
            "schema_version": f"{SCHEMA_VERSION}-manifest",
            "run_id": RUN_ID,
            "files": files,
            "cells": list(CELLS),
            "selection_roles": [SELECTION_ROLE],
            "training_runs": 0,
            "optimizer_steps": 0,
            "parameter_updates": 0,
            "new_checkpoints_written": 0,
            "target_data_products_materialized": 0,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "forbidden_artifacts_absent": True,
            "complete": True,
        },
    )


def run(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    cell_runs, sealed = source_preflight(config)
    source_target_reads = {
        cell: int(sealed[cell]["source_target_reads"]) for cell in CELLS
    }
    target_reads: dict[str, Any] = {
        "definition": "目标数组载入次数加本进程全量前向次数；基线聚合表读取另列，不计原始数组读取",
        "target_array_loads": 0,
        "target_forward_passes_this_process": 0,
        "target_forward_units_reused": 0,
        "total": 0,
    }
    write_status(
        output_root,
        "running",
        "source-preflight",
        None,
        "C01/C10 完成态、源侧目标年零读取与实体选轮检查点通过",
        source_target_reads,
        target_reads,
    )
    configs, agreement = load_configs_and_agreement(config, cell_runs)
    transform, transform_receipt = load_shared_transform(cell_runs)
    baseline_receipt = build_current_baseline_table(config, output_root)
    atomic_json(output_root / "baseline-table-receipt.json", baseline_receipt)

    cache_root = Path(agreement["cache_root"])
    data_receipt = host.verify_target_arrays(
        cache_root, Path(config["paths"]["target_config"])
    )
    atomic_json(
        output_root / "data-verification.json",
        {
            "schema_version": f"{SCHEMA_VERSION}-data-verification",
            "run_id": RUN_ID,
            **data_receipt,
            "cross_cell_agreement": agreement,
            "sealed_input_transform": transform_receipt,
        },
    )
    target = host.load_target_year(cache_root)
    target_reads["target_array_loads"] = len(host.TARGET_ARRAY_NAMES)
    target_reads["total"] = target_reads["target_array_loads"]
    if target["receipt"]["entity_count"] != config["baseline_comparison"]["expected_entity_count"]:
        raise SystemExit("FT 目标实体数与冻结基线比较池不一致")
    atomic_json(
        output_root / "target-year-read.json",
        {
            "schema_version": f"{SCHEMA_VERSION}-target-year-read",
            "run_id": RUN_ID,
            "cache_root": str(cache_root),
            **target["receipt"],
        },
    )
    torch_module, device, profile, precision = host.dual.resolve_runtime(configs[CELLS[0]])
    view = host.build_target_view(target, transform)
    identity_common = {
        "schema_version": f"{SCHEMA_VERSION}-unit-identity",
        "run_id": RUN_ID,
        "config_sha256": sha256_file(config_path),
        "evaluation_code_sha256": sha256_file(Path(__file__).resolve()),
        "host_tool_sha256": sha256_file(Path(host.__file__).resolve()),
        "baseline_table_sha256": baseline_receipt["table_sha256"],
        "sealed_transform_state_hash": transform_receipt["state_hash"],
        "target_array_sha256": {
            name: item["sha256"] for name, item in data_receipt["target_arrays"].items()
        },
    }
    completed: dict[str, dict[str, Any]] = {}
    run_started = time.time()
    for cell in CELLS:
        eval_config = copy.deepcopy(configs[cell])
        eval_config["training"]["validation_batch_sequences"] = agreement[
            "target_validation_batch_sequences"
        ][cell]
        checkpoint_path = cell_runs[cell] / "checkpoints" / "selected-by-entity.pt"
        identity = {
            **identity_common,
            "cell": cell,
            "selection_role": SELECTION_ROLE,
            "source_run_id": sealed[cell]["run_id"],
            "checkpoint_sha256": sealed[cell]["checkpoint_sha256"],
            "target_validation_batch_sequences": agreement[
                "target_validation_batch_sequences"
            ][cell],
            "source_torch_compile": agreement["source_torch_compile"][cell],
        }
        restored = load_completed_unit(output_root, cell, identity, args.resume)
        if restored is not None:
            completed[unit_name(cell)] = restored
            target_reads["target_forward_units_reused"] += 1
            continue
        write_status(
            output_root,
            "running",
            "target-evaluation",
            None,
            f"{unit_name(cell)} 单次全量前向",
            source_target_reads,
            target_reads,
        )
        base_config = host.dual.effective_base_config(eval_config)
        model, checkpoint_receipt = host.load_cell_model(
            eval_config, base_config, view, checkpoint_path, torch_module, device
        )
        if checkpoint_receipt.get("selection_role") != SELECTION_ROLE:
            raise SystemExit(f"{cell} 检查点载荷并非 selected-by-entity")
        if checkpoint_receipt.get("selected_epoch") != sealed[cell]["source_entity_epoch"]:
            raise SystemExit(f"{cell} 检查点轮次与实体选轮收据不一致")
        if agreement["entity_memory_enabled"][cell]:
            scheduler = host.dual.EntityChainScheduler(
                np.arange(target["n_sequence"], dtype=np.int64),
                target["sequence_entity"],
                target["interface"]["segment_ordinal"],
            )
            memory_state = host.dual.build_entity_memory_state(
                eval_config,
                base_config,
                {
                    "entity_count": target["entity_count"],
                    "role_of_entity": np.full(
                        target["entity_count"], host.TARGET_ENTITY_ROLE, dtype=np.int8
                    ),
                },
                torch_module,
                device,
            )
            scores, seen, resources = host.score_target_entity_memory(
                eval_config,
                model,
                view,
                scheduler,
                memory_state,
                target["interface"],
                target["sequence_entity"],
                device,
                profile,
                precision,
                torch_module,
                target["n_flow"],
                target["n_sequence"],
                f"LSPR24/{unit_name(cell)}打分",
            )
        else:
            scores, seen, resources = host.score_target_bare(
                eval_config,
                model,
                view,
                device,
                profile,
                precision,
                torch_module,
                target["n_flow"],
                target["n_sequence"],
                f"LSPR24/{unit_name(cell)}打分",
            )
        target_reads["target_forward_passes_this_process"] += 1
        target_reads["total"] = (
            target_reads["target_array_loads"]
            + target_reads["target_forward_passes_this_process"]
        )
        if int(seen.sum()) != target["n_flow"]:
            raise SystemExit(f"{cell} 逐流覆盖不完整")
        metrics, curve = host.cell_metrics(cell, scores, seen, target)
        metrics["actual_reachable_dr_at_fpr"] = actual_reachable_readouts(curve)
        metrics["target_validation_batch_sequences"] = agreement[
            "target_validation_batch_sequences"
        ][cell]
        metrics["target_batch_override_applied"] = agreement[
            "target_batch_override_applied"
        ][cell]
        completed[unit_name(cell)] = save_unit(
            output_root,
            cell,
            identity,
            checkpoint_receipt,
            metrics,
            curve,
            resources,
        )
        del model, scores, seen, curve, metrics
        if device.type == "cuda":
            torch_module.cuda.empty_cache()
    expected = {unit_name(cell) for cell in CELLS}
    if set(completed) != expected:
        raise SystemExit(f"评价单元未齐：{sorted(expected - set(completed))}")
    comparison = compare_baselines(completed, baseline_receipt)
    resource_receipt = None
    if args.resource_receipt:
        resource_path = Path(args.resource_receipt)
        resource_receipt = {
            "path": str(resource_path),
            "sha256": sha256_file(resource_path),
            "content": load_json(resource_path),
        }
    result = {
        "schema_version": f"{SCHEMA_VERSION}-results",
        "run_id": RUN_ID,
        "dataset": "LSPR24",
        "evaluation_role": TARGET_ROLE,
        "cells": list(CELLS),
        "selection_role": SELECTION_ROLE,
        "source_sealed": sealed,
        "source_run_target_reads": source_target_reads,
        "cross_cell_agreement": agreement,
        "formal_four_cell_result": False,
        "formal_four_cell_reason": "只评价 C01/C10，且历史训练执行路径不同；C00/C11 未纳入",
        "target_year_read": target["receipt"],
        "units": {name: completed[name] for name in sorted(completed)},
        "baseline_table": baseline_receipt,
        "baseline_comparison": comparison,
        "selection": {
            "selection_performed": False,
            "winner": None,
            "target_used_for_selection": False,
            "target_feedback_allowed": False,
            "reporting_rule": "两格并列描述；目标年胜负不改变检查点、机制、阈值或正式四格合同",
        },
        "isolation": {
            **config["isolation"],
            "input_transform_refitted_on_target": False,
            "entity_memory_restored_from_source_checkpoint": False,
            "optimizer_objects_constructed_by_shared_model_factory": len(CELLS),
            "optimizer_steps": 0,
        },
        "target_reads": target_reads,
        "resource": {
            "controller_wall_seconds": time.time() - run_started,
            "launcher_receipt": resource_receipt,
        },
    }
    result["result_sha256"] = canonical_sha256(result)
    atomic_json(output_root / "target-results.json", result)
    atomic_json(
        output_root / "target-summary.json",
        {
            "schema_version": f"{SCHEMA_VERSION}-summary",
            "run_id": RUN_ID,
            "rows": [
                {
                    "cell": cell,
                    "source_entity_ap": sealed[cell]["source_entity_ap"],
                    "source_entity_epoch": sealed[cell]["source_entity_epoch"],
                    "target_flow_ap": completed[unit_name(cell)]["metrics"][
                        "flow_average_precision"
                    ],
                    "target_entity_ap": completed[unit_name(cell)]["metrics"][
                        "entity_average_precision"
                    ],
                    "target_maximum_entity_ap": completed[unit_name(cell)]["metrics"][
                        "maximum_entity_average_precision"
                    ],
                    "actual_reachable_dr_at_fpr": completed[unit_name(cell)]["metrics"][
                        "actual_reachable_dr_at_fpr"
                    ],
                    "beats_all_registered_comparable_entity_ap_rows": comparison["per_cell"][cell][
                        "beats_all_same_pool_rows_with_available_entity_ap"
                    ],
                    "beats_xgb_cpa_elp_and_full_mlp_on_entity_ap": comparison["per_cell"][cell][
                        "beats_both_required_strong_baselines_on_entity_ap"
                    ],
                }
                for cell in CELLS
            ],
            "target_reads": target_reads,
            "source_run_target_reads": source_target_reads,
            "result_sha256": result["result_sha256"],
        },
    )
    write_status(
        output_root,
        "finished",
        "complete",
        0,
        "C01/C10 selected-by-entity 目标年描述性评价与同池基线比较完成",
        source_target_reads,
        target_reads,
    )
    build_manifest(output_root)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    try:
        config = load_json(config_path)
        validate_config(config)
        if args.check_config:
            print(f"配置核验通过：{config_path}")
            return 0
        run(config, args, config_path)
        return 0
    except (SystemExit, ValueError) as error:
        if isinstance(error, SystemExit) and error.code in (0, None):
            return 0
        print(f"评价停止：{error}", file=sys.stderr, flush=True)
        try:
            config = locals().get("config", {})
            output = Path(config.get("paths", {}).get("output_root", f"runs/diagnostics/{RUN_ID}"))
            output.mkdir(parents=True, exist_ok=True)
            write_status(output, "failed", "failed", 1, str(error), None, None)
        except Exception:  # noqa: BLE001
            pass
        return 1
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        try:
            config = locals().get("config", {})
            output = Path(config.get("paths", {}).get("output_root", f"runs/diagnostics/{RUN_ID}"))
            output.mkdir(parents=True, exist_ok=True)
            write_status(
                output,
                "failed",
                "failed",
                1,
                f"{type(error).__name__}: {error}",
                None,
                None,
            )
        except Exception:  # noqa: BLE001
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
