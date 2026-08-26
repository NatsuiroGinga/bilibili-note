#!/usr/bin/env python3
"""全容量 MLP 有效 2x2 的 LSPR23 零训练快速实验。"""

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

import ch3_full_mlp_s0_precision_aggregation_diagnostic as shared


RUN_ID = "ch3-full-mlp-valid-2x2-source-s0-seed42-v1"
SCHEMA_VERSION = "ch3-full-mlp-valid-2x2-source-s0-config-v1"
CELL_ORDER = ("C00", "C01p", "C10", "C11p")
CHECKPOINT_ORDER = ("B00", "B10")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXIT_CONFIG = 2
EXIT_INPUT = 3
EXIT_RUNTIME = 4


class ExperimentError(RuntimeError):
    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def require(condition: bool, message: str, exit_code: int = EXIT_CONFIG) -> None:
    if not condition:
        raise ExperimentError(message, exit_code)


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ExperimentError(f"JSON 读取失败：{path}：{error}", EXIT_CONFIG) from error


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def array_sha256(values: Any) -> str:
    digest = hashlib.sha256()
    digest.update(str(values.dtype).encode("ascii"))
    digest.update(json.dumps(list(values.shape)).encode("ascii"))
    digest.update(values.tobytes(order="C"))
    return digest.hexdigest()


def validate_config(config: dict[str, Any]) -> None:
    require(config.get("schema_version") == SCHEMA_VERSION, "配置模式版本不符")
    require(config.get("run_id") == RUN_ID, "运行身份不符")
    require(config.get("dataset_year") == "LSPR23", "本实验只允许 LSPR23")
    require(config.get("target_arrays_read") == 0, "目标年读取计数必须为零")
    require(config.get("approved_plan_sha256") == "3f8333da65f1fb7acf0f3aae7c1729114ce2b1ad043cb179ec74e38c191f2d38", "冻结计划摘要不符")
    require(config.get("source_arrays") == ["X23", "y23", "I23", "M23", "E23", "T23"], "源数组白名单不符")
    require(config.get("precision_profile") == "cuda-bf16-amp-fp32-sensitive-v1", "推理精度档案不符")
    require(config.get("inference_sequence_batch") == 2048, "推理序列批量不符")
    require(tuple(config.get("cells", {})) == CELL_ORDER, "四格键或顺序不符")
    require(
        config["cells"]
        == {
            "C00": {"checkpoint": "B00", "operator": "max"},
            "C01p": {"checkpoint": "B00", "operator": "mean_max_mix"},
            "C10": {"checkpoint": "B10", "operator": "max"},
            "C11p": {"checkpoint": "B10", "operator": "mean_max_mix"},
        },
        "四格公式不符",
    )
    require(config.get("mix_weights") == {"mean": 0.5, "max": 0.5}, "混合权重必须固定为 0.5/0.5")
    evaluation = config.get("evaluation", {})
    require(evaluation.get("fpr_grid") == [0.001, 0.005, 0.01, 0.02, 0.04, 0.08], "六档误报预算不符")
    require(evaluation.get("interpolation_allowed") is False, "禁止插值")
    require(evaluation.get("first_alert_axis") == "exposure_index", "首次告警轴不符")
    require(config.get("isolation") == {"training_runs": 0, "parameter_updates": 0, "new_checkpoints": 0, "target_reads": 0, "formal_paper_evidence": False}, "零训练或年度隔离合同不符")
    require(Path(config["output_root"]).name == RUN_ID, "输出目录名与运行身份不符")
    reference = config.get("reference", {})
    for key in ("config_sha256", "tool_sha256"):
        require(isinstance(reference.get(key), str) and len(reference[key]) == 64, f"参照摘要缺失：{key}")


def load_reference(config: dict[str, Any]) -> dict[str, Any]:
    reference = config["reference"]
    config_path = PROJECT_ROOT / reference["config_path"]
    tool_path = PROJECT_ROOT / reference["tool_path"]
    require(config_path.is_file(), f"参照配置不存在：{config_path}", EXIT_INPUT)
    require(tool_path.is_file(), f"参照工具不存在：{tool_path}", EXIT_INPUT)
    require(shared.sha256_file(config_path) == reference["config_sha256"], "参照配置摘要漂移", EXIT_INPUT)
    require(shared.sha256_file(tool_path) == reference["tool_sha256"], "参照工具摘要漂移", EXIT_INPUT)
    parent = load_json(config_path)
    shared.validate_config(parent)
    require(parent["parent_selection"]["identity"]["config_sha256"] == "673bab8ef85e4653f8b104180dbe296f89e6a6468a4a91e53dc5bcfa65805161", "父配置身份漂移", EXIT_INPUT)
    for checkpoint, expected in {
        "B00": "d9a89e0d40488686c5db2cca86bd8e2de9ab85200e23c4bc57b8171217531995",
        "B10": "5816387f1af57518a22514d5e21b8343a65747e4ffff41c6e6ef4786dd60d763",
    }.items():
        require(parent["parent_selection"]["checkpoints"][checkpoint]["sha256"] == expected, f"{checkpoint} 摘要漂移", EXIT_INPUT)
    return parent


def segmented_prefix_max(values: Any, starts: Any, ends: Any) -> Any:
    np = shared.require_numpy()
    result = np.empty_like(values, dtype=np.float64)
    for start, end in zip(starts.tolist(), ends.tolist(), strict=True):
        result[start:end] = np.maximum.accumulate(values[start:end])
    return result


def curve_vectors(prefix: str, curve: dict[str, Any]) -> dict[str, Any]:
    return {
        f"{prefix}__{field}": curve[field]
        for field in ("threshold", "negative_tie_group_size", "n_false_positive_entity", "realized_fpr", "detection_rate")
    }


def evaluate_cell(
    config: dict[str, Any],
    cell: str,
    checkpoint: str,
    probabilities: Any,
    flow_ap: float,
    flow_identity: dict[str, Any],
    order: dict[str, Any],
    entity_labels: Any,
    scored_entities: Any,
) -> tuple[dict[str, Any], dict[str, Any], Any, dict[str, Any]]:
    np = shared.require_numpy()
    average_precision_score = shared.require_metrics()
    prefix_sum = shared.prefix_group_sums(probabilities, order)
    prefix_mean = prefix_sum / order["exposure_index"].astype(np.float64)
    prefix_max = segmented_prefix_max(probabilities, order["starts"], order["ends"])
    if config["cells"][cell]["operator"] == "max":
        running = prefix_max
    else:
        running = 0.5 * prefix_mean + 0.5 * prefix_max
    terminal = running[order["ends"] - 1]
    entity_scores = np.full(len(entity_labels), np.nan, dtype=np.float64)
    entity_scores[order["entity_ids"]] = terminal
    max_scores = np.full(len(entity_labels), np.nan, dtype=np.float64)
    max_scores[order["entity_ids"]] = prefix_max[order["ends"] - 1]
    terminal_curve = shared.complete_tied_budget_curve(entity_scores, entity_labels)
    path_scores = np.full(len(entity_labels), np.nan, dtype=np.float64)
    path_scores[order["entity_ids"]] = np.maximum.reduceat(running, order["starts"])
    path_curve = shared.complete_tied_budget_curve(path_scores, entity_labels)
    grid = config["evaluation"]["fpr_grid"]
    terminal_common = shared.common_integer_fp_budget_readouts(terminal_curve, grid)
    path_common = shared.common_integer_fp_budget_readouts(path_curve, grid)
    branch = {"key": cell}
    first_alert, first_alert_vectors = shared.first_alert_aggregate(
        branch,
        running,
        order,
        entity_labels,
        scored_entities,
        path_common,
        "common_actual_fp_budget",
        config["evaluation"]["first_alert_quantiles"],
    )
    require(np.array_equal(terminal, running[order["ends"] - 1]), f"{cell} 终端分数不等于末前缀", EXIT_RUNTIME)
    metrics = {
        "cell": cell,
        "checkpoint": checkpoint,
        "operator": config["cells"][cell]["operator"],
        "flow_average_precision": flow_ap,
        "entity_average_precision": float(average_precision_score(entity_labels[scored_entities], entity_scores[scored_entities])),
        "max_entity_average_precision": float(average_precision_score(entity_labels[scored_entities], max_scores[scored_entities])),
        "actual_reachable_dr_at_fpr": shared.actual_reachable_readouts(terminal_curve, grid),
        "common_actual_dr_at_integer_fp_budget": terminal_common,
        "normalized_curve": shared.normalized_curve_area(terminal_curve, config["evaluation"]["curve_maximum_fpr"]),
        "tie_profile": shared.tie_profile(entity_scores, entity_labels),
        "first_alert": first_alert,
        "flow_identity": flow_identity,
        "terminal_equals_last_prefix": True,
        "training_runs": 0,
        "parameter_updates": 0,
        "target_reads": 0,
    }
    vectors = {}
    vectors.update(curve_vectors(f"{cell}__terminal", terminal_curve))
    vectors.update(curve_vectors(f"{cell}__path", path_curve))
    vectors.update(first_alert_vectors)
    return metrics, vectors, entity_scores, {"terminal": terminal_curve, "path": path_curve}


def curve_on_all_integer_budgets(curve: dict[str, Any]) -> Any:
    np = shared.require_numpy()
    budgets = np.arange(curve["negative_entity_count"] + 1, dtype=np.int64)
    indices = np.searchsorted(curve["n_false_positive_entity"], budgets, side="right") - 1
    return curve["detection_rate"][indices]


def compare_pair(max_cell: str, mix_cell: str, cells: dict[str, Any], curve_objects: dict[str, Any], curve_vectors_all: dict[str, Any]) -> dict[str, Any]:
    np = shared.require_numpy()
    baseline = cells[max_cell]
    candidate = cells[mix_cell]
    baseline_curve = curve_on_all_integer_budgets(curve_objects[max_cell]["terminal"])
    candidate_curve = curve_on_all_integer_budgets(curve_objects[mix_cell]["terminal"])
    terminal_delta = candidate_curve - baseline_curve
    nested_first = {
        max_cell: {"common_actual_fp_budget": baseline["first_alert"]},
        mix_cell: {"common_actual_fp_budget": candidate["first_alert"]},
    }
    first_comparison = shared.compare_first_alert_on_common_axis(
        mix_cell, max_cell, nested_first, curve_vectors_all
    )
    entity_delta = candidate["entity_average_precision"] - baseline["entity_average_precision"]
    terminal_strict = bool((terminal_delta > 0.0).any())
    terminal_not_worse = bool((terminal_delta >= 0.0).all())
    first_strict = any(item["strictly_better_on_common_exposure_axis"] for item in first_comparison.values())
    first_not_worse = all(item["not_worse_on_common_exposure_axis"] for item in first_comparison.values())
    strict_improvement = bool(entity_delta > 0.0 or terminal_strict or first_strict)
    baseline_dominates = bool(
        entity_delta <= 0.0
        and bool((terminal_delta <= 0.0).all())
        and all(
            item["minimum_on_time_detection_rate_delta"] <= 0.0
            and item["maximum_on_time_detection_rate_delta"] <= 0.0
            and item["positive_unalerted_rate_delta"] >= 0.0
            for item in first_comparison.values()
        )
        and (entity_delta < 0.0 or bool((terminal_delta < 0.0).any()))
    )
    return {
        "baseline_cell": max_cell,
        "candidate_cell": mix_cell,
        "entity_average_precision_delta": float(entity_delta),
        "max_entity_average_precision_delta": float(candidate["max_entity_average_precision"] - baseline["max_entity_average_precision"]),
        "minimum_terminal_detection_rate_delta": float(terminal_delta.min()),
        "maximum_terminal_detection_rate_delta": float(terminal_delta.max()),
        "terminal_curve_not_worse": terminal_not_worse,
        "first_alert": first_comparison,
        "first_alert_not_worse": first_not_worse,
        "strict_improvement_on_any_primary_axis": strict_improvement,
        "candidate_dominated_by_max": baseline_dominates,
        "source_signal": bool(strict_improvement and not baseline_dominates),
    }


def build_manifest(output_root: Path) -> None:
    files = {}
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "run.log"}:
            relative = path.relative_to(output_root).as_posix()
            files[relative] = {"bytes": path.stat().st_size, "sha256": shared.sha256_file(path)}
    shared.atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-full-mlp-valid-2x2-manifest-v1",
            "run_id": RUN_ID,
            "complete": True,
            "training_runs": 0,
            "parameter_updates": 0,
            "target_reads": 0,
            "excluded_append_only_files": ["run.log"],
            "files": files,
        },
    )


def run_experiment(config: dict[str, Any], config_path: Path) -> None:
    np = shared.require_numpy()
    torch = shared.require_torch()
    parent = load_reference(config)
    output_root = Path(config["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    shared.atomic_json(output_root / "config.json", config)
    shared.atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "running", "stage": "source", "target_reads": 0})
    started = time.time()
    inputs = shared.validate_inputs(parent, tuple(config["source_arrays"]))
    shared.atomic_json(output_root / "input-validation-receipt.json", inputs)
    cache_root = Path(parent["paths"]["cache_root"])
    arrays = {name: np.load(cache_root / f"{name}.npy") for name in config["source_arrays"]}
    entity_base, validation_rows, split_stats = shared.build_source_context(parent, arrays)
    flow_labels = arrays["y23"]
    seen = np.zeros(len(flow_labels), dtype=bool)
    indices = arrays["I23"][validation_rows, : parent["model"]["sequence_length"]]
    masks = arrays["M23"][validation_rows, : parent["model"]["sequence_length"]] > 0.5
    seen[indices[masks]] = True
    order = shared.ordered_exposures(seen, entity_base["flow_entity"])
    scored_entities = np.zeros(entity_base["count"], dtype=bool)
    scored_entities[order["entity_ids"]] = True
    device = torch.device("cuda")
    profiles = shared.validate_precision_profiles(parent)
    profile = dict(profiles["bf16"])
    profile["profile_id"] = config["precision_profile"]
    tensors = {
        "X": torch.from_numpy(arrays["X23"]).to(device),
        "I": torch.from_numpy(arrays["I23"]).to(device),
        "M": torch.from_numpy(arrays["M23"]).to(device),
    }
    for name in ("X23", "I23", "M23", "E23", "T23"):
        arrays.pop(name, None)
    cells: dict[str, Any] = {}
    curve_vectors_all: dict[str, Any] = {}
    curve_objects: dict[str, Any] = {}
    flow_receipts: dict[str, Any] = {}
    for checkpoint in CHECKPOINT_ORDER:
        checkpoint_receipt = inputs["checkpoints"][checkpoint]
        model, weights_sha256, model_receipt = shared.build_frozen_model(
            parent, checkpoint, Path(checkpoint_receipt["path"]), device
        )
        logits, actual_seen, forward_receipt = shared.forward_logits(
            parent,
            model,
            "bf16",
            profile,
            device,
            tensors["X"],
            tensors["I"],
            tensors["M"],
            validation_rows,
            len(flow_labels),
            f"source/{checkpoint}",
        )
        require(np.array_equal(actual_seen, seen), f"{checkpoint} 打分流集合漂移", EXIT_RUNTIME)
        ordered_logits = logits[order["flow_ids"]].astype(np.float64)
        require(bool(np.isfinite(ordered_logits).all()), f"{checkpoint} 出现非有限对数几率", EXIT_RUNTIME)
        probabilities = shared.stable_sigmoid(ordered_logits)
        flow_ap = float(shared.require_metrics()(flow_labels[order["flow_ids"]], probabilities))
        flow_identity = {
            "checkpoint": checkpoint,
            "flow_count": int(len(probabilities)),
            "flow_order_sha256": array_sha256(order["flow_ids"]),
            "logits_sha256": array_sha256(ordered_logits),
            "probabilities_sha256": array_sha256(probabilities),
            "weights_sha256": weights_sha256,
            "model_receipt": model_receipt,
            "forward_receipt": forward_receipt,
        }
        flow_receipts[checkpoint] = flow_identity
        for cell in CELL_ORDER:
            if config["cells"][cell]["checkpoint"] != checkpoint:
                continue
            metrics, vectors, _, objects = evaluate_cell(
                config,
                cell,
                checkpoint,
                probabilities,
                flow_ap,
                flow_identity,
                order,
                entity_base["labels"],
                scored_entities,
            )
            cells[cell] = metrics
            curve_vectors_all.update(vectors)
            curve_objects[cell] = objects
        del model, logits, actual_seen, ordered_logits, probabilities
        torch.cuda.empty_cache()
    require(cells["C00"]["flow_identity"] == cells["C01p"]["flow_identity"], "B00 配对格逐流身份不一致", EXIT_RUNTIME)
    require(cells["C10"]["flow_identity"] == cells["C11p"]["flow_identity"], "B10 配对格逐流身份不一致", EXIT_RUNTIME)
    comparisons = {
        "B00_max_vs_mix": compare_pair("C00", "C01p", cells, curve_objects, curve_vectors_all),
        "B10_max_vs_mix": compare_pair("C10", "C11p", cells, curve_objects, curve_vectors_all),
    }
    signal = any(item["source_signal"] for item in comparisons.values())
    if signal:
        verdict = "source_signal_or_nondominated_tradeoff"
    elif all(item["candidate_dominated_by_max"] for item in comparisons.values()):
        verdict = "source_no_signal_keep_existing_O11_and_stop"
    else:
        verdict = "source_no_strict_signal_keep_existing_O11_and_stop"
    curve_receipt = shared.atomic_npz(output_root / "curves.npz", curve_vectors_all)
    identity = {
        "config_sha256": shared.sha256_file(config_path),
        "code_sha256": shared.sha256_file(Path(__file__)),
        "approved_plan_sha256": config["approved_plan_sha256"],
        "parent_config_sha256": parent["parent_selection"]["identity"]["config_sha256"],
        "source_inventory_sha256": parent["parent_selection"]["identity"]["source_data_inventory_sha256"],
    }
    results = {
        "schema_version": "ch3-full-mlp-valid-2x2-source-s0-results-v1",
        "run_id": RUN_ID,
        "evidence_level": "zero_train_source_screening",
        "scientific_status": "实验支持源年信号" if signal else "实验未支持固定混合算子",
        "verdict": verdict,
        "identity": identity,
        "source_split": split_stats,
        "cells": cells,
        "comparisons": comparisons,
        "interaction_entity_average_precision": float(
            cells["C11p"]["entity_average_precision"]
            - cells["C10"]["entity_average_precision"]
            - cells["C01p"]["entity_average_precision"]
            + cells["C00"]["entity_average_precision"]
        ),
        "curve_artifact": {"filename": "curves.npz", "sha256": curve_receipt["sha256"]},
        "target_reads": 0,
        "training_runs": 0,
        "parameter_updates": 0,
        "resource_contention": config["resource_disclosure"]["resource_contention"],
        "formal_paper_evidence": False,
    }
    shared.atomic_json(output_root / "flow-identity-receipt.json", flow_receipts)
    shared.atomic_json(
        output_root / "formula-identity-receipt.json",
        {
            "cells": config["cells"],
            "mix_weights": config["mix_weights"],
            "terminal_equals_last_prefix": True,
            "same_checkpoint_flow_identity": True,
            "formula_sha256": canonical_sha256({"cells": config["cells"], "mix_weights": config["mix_weights"]}),
        },
    )
    shared.atomic_json(output_root / "aggregate-results.json", results)
    shared.atomic_json(
        output_root / "source-seal.json",
        {
            "run_id": RUN_ID,
            "sealed": True,
            "identity": identity,
            "verdict": verdict,
            "target_reads": 0,
            "aggregate_results_sha256": shared.sha256_file(output_root / "aggregate-results.json"),
        },
    )
    torch.cuda.synchronize()
    shared.atomic_json(
        output_root / "resource-receipt.json",
        {
            "wall_seconds": time.time() - started,
            "peak_gpu_allocated_mib": max(item["forward_receipt"]["peak_gpu_allocated_mib"] for item in flow_receipts.values()),
            "peak_gpu_reserved_mib": max(item["forward_receipt"]["peak_gpu_reserved_mib"] for item in flow_receipts.values()),
            "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
            "resource_contention": config["resource_disclosure"]["resource_contention"],
            "efficiency_comparison_allowed": False,
        },
    )
    shared.atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "finished", "stage": "source", "exit_code": 0, "verdict": verdict, "target_reads": 0})
    build_manifest(output_root)
    print(json.dumps({"run_id": RUN_ID, "verdict": verdict, "cells": {key: value["entity_average_precision"] for key, value in cells.items()}}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="全容量 MLP 有效2x2源年mean-max零训练快速实验")
    parser.add_argument("--config", required=True, help="冻结配置")
    parser.add_argument("--validate-config", action="store_true", help="仅核验配置与参照身份")
    parser.add_argument("--run", action="store_true", help="执行 LSPR23 源年快速实验")
    parser.add_argument("--finalize-manifest", action="store_true", help="不重算指标，只重建最终制品清单")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    try:
        config = load_json(config_path)
        validate_config(config)
        load_reference(config)
        if args.validate_config:
            print("配置核验通过")
            return 0
        if args.finalize_manifest:
            output_root = Path(config["output_root"])
            require((output_root / "aggregate-results.json").is_file(), "缺少聚合结果，不能重建清单", EXIT_INPUT)
            build_manifest(output_root)
            print("清单重建完成")
            return 0
        require(args.run, "必须指定 --run 或 --validate-config")
        run_experiment(config, config_path)
        return 0
    except ExperimentError as error:
        print(str(error), file=sys.stderr, flush=True)
        return error.exit_code
    except shared.StageError as error:
        print(str(error), file=sys.stderr, flush=True)
        return error.exit_code
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        print(f"未预期错误：{error}", file=sys.stderr, flush=True)
        return EXIT_RUNTIME


if __name__ == "__main__":
    sys.exit(main())
