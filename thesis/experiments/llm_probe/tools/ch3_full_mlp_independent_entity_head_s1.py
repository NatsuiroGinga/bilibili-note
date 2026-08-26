#!/usr/bin/env python3
"""B10 冻结骨干上的三参数多算子实体头 S1 快速实验。"""

from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import ch3_full_mlp_s0_precision_aggregation_diagnostic as shared
import ch3_full_mlp_valid_2x2_source_s0 as source


RUN_ID = "ch3-full-mlp-independent-entity-head-s1-seed42-v1"
SCHEMA_VERSION = "ch3-full-mlp-independent-entity-head-s1-config-v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HEAD_ORDER = ("max_baseline", "control_mean_mean", "candidate_mean_max")


def validate_config(config: dict[str, Any]) -> None:
    source.require(config.get("schema_version") == SCHEMA_VERSION, "配置模式版本不符")
    source.require(config.get("run_id") == RUN_ID, "运行身份不符")
    source.require(config.get("contract_revision") == "S1-r0-lbfgs-3param-20260826", "S1 合同版本不符")
    source.require(config.get("parent_checkpoint") == "B10", "父检查点必须是 B10")
    source.require(config.get("parent_checkpoint_sha256") == "5816387f1af57518a22514d5e21b8343a65747e4ffff41c6e6ef4786dd60d763", "B10 摘要不符")
    source.require(
        config.get("heads")
        == {
            "candidate_mean_max": {"features": ["prefix_mean", "prefix_max"], "parameter_count": 3},
            "control_mean_mean": {"features": ["prefix_mean", "prefix_mean"], "parameter_count": 3},
        },
        "候选头或参数匹配控制头定义不符",
    )
    expected_optimizer = {
        "name": "torch.optim.LBFGS",
        "lr": 1.0,
        "max_iter": 100,
        "max_eval": 125,
        "tolerance_grad": 1e-7,
        "tolerance_change": 1e-9,
        "history_size": 10,
        "line_search_fn": "strong_wolfe",
        "full_batch": True,
        "parameter_dtype": "float64",
        "loss": "weighted_binary_cross_entropy_with_logits",
        "initialization": "all_zero",
        "hyperparameter_searches": 0,
    }
    source.require(config.get("optimizer") == expected_optimizer, "优化器冻结值不符")
    evaluation = config.get("evaluation", {})
    source.require(evaluation.get("fpr_grid") == [0.001, 0.005, 0.01, 0.02, 0.04, 0.08], "六档预算不符")
    source.require(evaluation.get("low_budget_count") == 3, "低预算护栏数量不符")
    source.require(evaluation.get("interpolation_allowed") is False, "禁止插值")
    isolation = config.get("isolation", {})
    source.require(isolation.get("dataset_year") == "LSPR23", "S1 只允许 LSPR23")
    source.require(isolation.get("validation_labels_used_for_fit") is False, "验证标签不得参与拟合")
    source.require(isolation.get("target_reads") == 0, "目标读取必须为零")
    source.require(isolation.get("backbone_parameter_updates") == 0, "骨干参数更新必须为零")
    source.require(Path(config["output_root"]).name == RUN_ID, "输出根与运行身份不符")


def load_source_contract(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    config_path = PROJECT_ROOT / config["source_config_path"]
    tool_path = PROJECT_ROOT / config["source_tool_path"]
    source.require(config_path.is_file() and tool_path.is_file(), "S0 参照文件缺失", source.EXIT_INPUT)
    source.require(shared.sha256_file(config_path) == config["source_config_sha256"], "S0 配置摘要漂移", source.EXIT_INPUT)
    source.require(shared.sha256_file(tool_path) == config["source_tool_sha256"], "S0 工具摘要漂移", source.EXIT_INPUT)
    source_config = source.load_json(config_path)
    source.validate_config(source_config)
    parent = source.load_reference(source_config)
    source.require(parent["parent_selection"]["checkpoints"]["B10"]["sha256"] == config["parent_checkpoint_sha256"], "父 B10 摘要漂移", source.EXIT_INPUT)
    return source_config, parent


def exposure_summary(probabilities: Any, seen: Any, flow_entity: Any, entity_count: int) -> dict[str, Any]:
    np = shared.require_numpy()
    order = shared.ordered_exposures(seen, flow_entity)
    ordered = probabilities[order["flow_ids"]].astype(np.float64)
    prefix_sum = shared.prefix_group_sums(ordered, order)
    prefix_mean = prefix_sum / order["exposure_index"].astype(np.float64)
    prefix_max = source.segmented_prefix_max(ordered, order["starts"], order["ends"])
    terminal_mean = np.full(entity_count, np.nan, dtype=np.float64)
    terminal_max = np.full(entity_count, np.nan, dtype=np.float64)
    terminal_mean[order["entity_ids"]] = prefix_mean[order["ends"] - 1]
    terminal_max[order["entity_ids"]] = prefix_max[order["ends"] - 1]
    scored = np.zeros(entity_count, dtype=bool)
    scored[order["entity_ids"]] = True
    return {
        "order": order,
        "ordered_probabilities": ordered,
        "prefix_mean": prefix_mean,
        "prefix_max": prefix_max,
        "terminal_mean": terminal_mean,
        "terminal_max": terminal_max,
        "scored": scored,
    }


def fit_head(config: dict[str, Any], key: str, features: Any, labels: Any, device: Any) -> tuple[dict[str, Any], Any]:
    torch = shared.require_torch()
    optimizer_config = config["optimizer"]
    x = torch.from_numpy(features).to(device=device, dtype=torch.float64)
    y = torch.from_numpy(labels).to(device=device, dtype=torch.float64)
    positives = int((labels == 1).sum())
    negatives = int((labels == 0).sum())
    source.require(positives > 0 and negatives > 0, f"{key} 训练实体缺少正类或负类", source.EXIT_INPUT)
    head = torch.nn.Linear(2, 1, bias=True, dtype=torch.float64, device=device)
    torch.nn.init.zeros_(head.weight)
    torch.nn.init.zeros_(head.bias)
    source.require(sum(parameter.numel() for parameter in head.parameters()) == 3, f"{key} 参数量不是 3", source.EXIT_RUNTIME)
    pos_weight = torch.tensor(negatives / positives, dtype=torch.float64, device=device)
    criterion = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.LBFGS(
        head.parameters(),
        lr=optimizer_config["lr"],
        max_iter=optimizer_config["max_iter"],
        max_eval=optimizer_config["max_eval"],
        tolerance_grad=optimizer_config["tolerance_grad"],
        tolerance_change=optimizer_config["tolerance_change"],
        history_size=optimizer_config["history_size"],
        line_search_fn=optimizer_config["line_search_fn"],
    )
    closure_calls = 0

    def closure() -> Any:
        nonlocal closure_calls
        optimizer.zero_grad(set_to_none=True)
        logits = head(x).reshape(-1)
        loss = criterion(logits, y)
        loss.backward()
        closure_calls += 1
        return loss

    with torch.no_grad():
        initial_loss = float(criterion(head(x).reshape(-1), y).item())
    optimizer.step(closure)
    with torch.no_grad():
        final_loss = float(criterion(head(x).reshape(-1), y).item())
        weight = head.weight.detach().cpu().numpy().reshape(-1).astype("float64")
        bias = float(head.bias.detach().cpu().item())
    source.require(bool(shared.require_numpy().isfinite(weight).all()) and math_isfinite(bias), f"{key} 参数非有限", source.EXIT_RUNTIME)
    receipt = {
        "key": key,
        "parameter_count": 3,
        "dtype": "float64",
        "weight": weight.tolist(),
        "bias": bias,
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "closure_calls": closure_calls,
        "positive_entities": positives,
        "negative_entities": negatives,
        "pos_weight": negatives / positives,
        "optimizer": optimizer_config,
    }
    return receipt, head


def math_isfinite(value: float) -> bool:
    return value == value and value not in (float("inf"), float("-inf"))


def running_from_head(head: Any, first: Any, second: Any) -> Any:
    np = shared.require_numpy()
    torch = shared.require_torch()
    with torch.no_grad():
        weight = head.weight.detach().cpu().numpy().reshape(-1).astype(np.float64)
        bias = float(head.bias.detach().cpu().item())
    return shared.stable_sigmoid(bias + weight[0] * first + weight[1] * second)


def evaluate_running(
    config: dict[str, Any],
    key: str,
    running: Any,
    max_running: Any,
    flow_ap: float,
    summary: dict[str, Any],
    entity_labels: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    np = shared.require_numpy()
    average_precision_score = shared.require_metrics()
    order = summary["order"]
    scored = summary["scored"]
    terminal = running[order["ends"] - 1]
    entity_scores = np.full(len(entity_labels), np.nan, dtype=np.float64)
    entity_scores[order["entity_ids"]] = terminal
    max_scores = np.full(len(entity_labels), np.nan, dtype=np.float64)
    max_scores[order["entity_ids"]] = max_running[order["ends"] - 1]
    terminal_curve = shared.complete_tied_budget_curve(entity_scores, entity_labels)
    path_scores = np.full(len(entity_labels), np.nan, dtype=np.float64)
    path_scores[order["entity_ids"]] = np.maximum.reduceat(running, order["starts"])
    path_curve = shared.complete_tied_budget_curve(path_scores, entity_labels)
    grid = config["evaluation"]["fpr_grid"]
    terminal_common = shared.common_integer_fp_budget_readouts(terminal_curve, grid)
    path_common = shared.common_integer_fp_budget_readouts(path_curve, grid)
    first_alert, first_vectors = shared.first_alert_aggregate(
        {"key": key},
        running,
        order,
        entity_labels,
        scored,
        path_common,
        "common_actual_fp_budget",
        config["evaluation"]["first_alert_quantiles"],
    )
    metrics = {
        "key": key,
        "flow_average_precision": flow_ap,
        "entity_average_precision": float(average_precision_score(entity_labels[scored], entity_scores[scored])),
        "max_entity_average_precision": float(average_precision_score(entity_labels[scored], max_scores[scored])),
        "actual_reachable_dr_at_fpr": shared.actual_reachable_readouts(terminal_curve, grid),
        "common_actual_dr_at_integer_fp_budget": terminal_common,
        "normalized_curve": shared.normalized_curve_area(terminal_curve, config["evaluation"]["curve_maximum_fpr"]),
        "tie_profile": shared.tie_profile(entity_scores, entity_labels),
        "first_alert": first_alert,
    }
    vectors = {}
    vectors.update(source.curve_vectors(f"{key}__terminal", terminal_curve))
    vectors.update(source.curve_vectors(f"{key}__path", path_curve))
    vectors.update(first_vectors)
    return metrics, vectors, {"terminal": terminal_curve, "path": path_curve}


def low_budget_not_worse(
    comparison: dict[str, Any], baseline: dict[str, Any], candidate: dict[str, Any], count: int
) -> bool:
    budget_keys = list(baseline["common_actual_dr_at_integer_fp_budget"])[:count]
    first_items = [comparison["first_alert"][key] for key in budget_keys]
    return bool(
        all(
            candidate["common_actual_dr_at_integer_fp_budget"][key]["detection_rate"]
            >= baseline["common_actual_dr_at_integer_fp_budget"][key]["detection_rate"]
            for key in budget_keys
        )
        and all(
            item["minimum_on_time_detection_rate_delta"] >= 0.0
            and item["positive_unalerted_rate_delta"] <= 0.0
            for item in first_items
        )
    )


def build_manifest(output_root: Path) -> None:
    files = {}
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "run.log"}:
            relative = path.relative_to(output_root).as_posix()
            files[relative] = {"bytes": path.stat().st_size, "sha256": shared.sha256_file(path)}
    shared.atomic_json(output_root / "manifest.json", {"schema_version": "ch3-full-mlp-independent-entity-head-s1-manifest-v1", "run_id": RUN_ID, "complete": True, "target_reads": 0, "backbone_parameter_updates": 0, "excluded_append_only_files": ["run.log"], "files": files})


def run(config: dict[str, Any], config_path: Path) -> None:
    np = shared.require_numpy()
    torch = shared.require_torch()
    source_config, parent = load_source_contract(config)
    output_root = Path(config["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    shared.atomic_json(output_root / "config.json", config)
    shared.atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "running", "stage": "source", "target_reads": 0})
    started = time.time()
    inputs = shared.validate_inputs(parent, tuple(source_config["source_arrays"]))
    cache_root = Path(parent["paths"]["cache_root"])
    arrays = {name: np.load(cache_root / f"{name}.npy") for name in source_config["source_arrays"]}
    legacy, _, _ = shared.require_project_modules()
    split_config = {"training": {"seed": 42, "validation_fraction": 0.1, "time_tail_fraction": 0.15}}
    train_rows, validation_rows, split_stats = legacy.source_split(arrays, split_config)
    flow_entity = legacy.build_flow_entity(arrays["I23"], arrays["M23"], arrays["E23"], len(arrays["y23"]))
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, arrays["y23"])
    length = parent["model"]["sequence_length"]

    def seen_for_rows(rows: Any) -> Any:
        seen = np.zeros(len(arrays["y23"]), dtype=bool)
        idx = arrays["I23"][rows, :length]
        mask = arrays["M23"][rows, :length] > 0.5
        seen[idx[mask]] = True
        return seen

    train_seen = seen_for_rows(train_rows)
    validation_seen = seen_for_rows(validation_rows)
    device = torch.device("cuda")
    profiles = shared.validate_precision_profiles(parent)
    profile = dict(profiles["bf16"])
    profile["profile_id"] = source_config["precision_profile"]
    tensors = {"X": torch.from_numpy(arrays["X23"]).to(device), "I": torch.from_numpy(arrays["I23"]).to(device), "M": torch.from_numpy(arrays["M23"]).to(device)}
    checkpoint = inputs["checkpoints"]["B10"]
    model, weights_sha256, model_receipt = shared.build_frozen_model(parent, "B10", Path(checkpoint["path"]), device)
    train_logits, actual_train_seen, train_forward = shared.forward_logits(parent, model, "bf16", profile, device, tensors["X"], tensors["I"], tensors["M"], train_rows, len(arrays["y23"]), "source/B10/train")
    validation_logits, actual_validation_seen, validation_forward = shared.forward_logits(parent, model, "bf16", profile, device, tensors["X"], tensors["I"], tensors["M"], validation_rows, len(arrays["y23"]), "source/B10/validation")
    source.require(np.array_equal(train_seen, actual_train_seen) and np.array_equal(validation_seen, actual_validation_seen), "训练或验证打分流集合漂移", source.EXIT_RUNTIME)
    train_probabilities = shared.stable_sigmoid(train_logits)
    validation_probabilities = shared.stable_sigmoid(validation_logits)
    train_summary = exposure_summary(train_probabilities, train_seen, flow_entity, entity_count)
    validation_summary = exposure_summary(validation_probabilities, validation_seen, flow_entity, entity_count)
    train_entities = train_summary["scored"]
    candidate_features = np.column_stack((train_summary["terminal_mean"][train_entities], train_summary["terminal_max"][train_entities]))
    control_features = np.column_stack((train_summary["terminal_mean"][train_entities], train_summary["terminal_mean"][train_entities]))
    train_targets = entity_labels[train_entities].astype(np.float64)
    candidate_receipt, candidate_head = fit_head(config, "candidate_mean_max", candidate_features, train_targets, device)
    control_receipt, control_head = fit_head(config, "control_mean_mean", control_features, train_targets, device)
    max_running = validation_summary["prefix_max"]
    candidate_running = running_from_head(candidate_head, validation_summary["prefix_mean"], validation_summary["prefix_max"])
    control_running = running_from_head(control_head, validation_summary["prefix_mean"], validation_summary["prefix_mean"])
    flow_ap = float(shared.require_metrics()(arrays["y23"][validation_summary["order"]["flow_ids"]], validation_summary["ordered_probabilities"]))
    metrics: dict[str, Any] = {}
    vectors: dict[str, Any] = {}
    objects: dict[str, Any] = {}
    for key, running_scores in (("max_baseline", max_running), ("control_mean_mean", control_running), ("candidate_mean_max", candidate_running)):
        item, item_vectors, item_objects = evaluate_running(config, key, running_scores, max_running, flow_ap, validation_summary, entity_labels)
        metrics[key] = item
        vectors.update(item_vectors)
        objects[key] = item_objects
    candidate_vs_control = source.compare_pair("control_mean_mean", "candidate_mean_max", metrics, objects, vectors)
    candidate_vs_max = source.compare_pair("max_baseline", "candidate_mean_max", metrics, objects, vectors)
    low_budget_ok = low_budget_not_worse(
        candidate_vs_control,
        metrics["control_mean_mean"],
        metrics["candidate_mean_max"],
        config["evaluation"]["low_budget_count"],
    ) and low_budget_not_worse(
        candidate_vs_max,
        metrics["max_baseline"],
        metrics["candidate_mean_max"],
        config["evaluation"]["low_budget_count"],
    )
    passed = bool(candidate_vs_control["source_signal"] and candidate_vs_max["source_signal"] and low_budget_ok)
    verdict = "s1_source_passed" if passed else "s1_source_rejected_keep_existing_O11"
    heads_path = output_root / "entity-heads.pt"
    temporary_heads = heads_path.with_name(f"{heads_path.name}.partial.{os.getpid()}")
    torch.save({"schema_version": "ch3-independent-entity-heads-v1", "run_id": RUN_ID, "candidate": candidate_head.state_dict(), "control": control_head.state_dict(), "candidate_receipt": candidate_receipt, "control_receipt": control_receipt, "parent_checkpoint_sha256": config["parent_checkpoint_sha256"]}, temporary_heads)
    os.replace(temporary_heads, heads_path)
    curve_receipt = shared.atomic_npz(output_root / "curves.npz", vectors)
    results = {
        "schema_version": "ch3-full-mlp-independent-entity-head-s1-results-v1",
        "run_id": RUN_ID,
        "verdict": verdict,
        "source_passed": passed,
        "split": split_stats,
        "train_entity_counts": {"all": int(train_entities.sum()), "positive": int((train_entities & (entity_labels == 1)).sum()), "negative": int((train_entities & (entity_labels == 0)).sum())},
        "validation_entity_counts": {"all": int(validation_summary["scored"].sum()), "positive": int((validation_summary["scored"] & (entity_labels == 1)).sum()), "negative": int((validation_summary["scored"] & (entity_labels == 0)).sum())},
        "heads": {"candidate_mean_max": candidate_receipt, "control_mean_mean": control_receipt},
        "metrics": metrics,
        "comparisons": {"candidate_vs_control": candidate_vs_control, "candidate_vs_max": candidate_vs_max, "low_budget_not_worse": low_budget_ok},
        "identity": {"config_sha256": shared.sha256_file(config_path), "code_sha256": shared.sha256_file(Path(__file__)), "source_config_sha256": config["source_config_sha256"], "parent_checkpoint_sha256": config["parent_checkpoint_sha256"], "parent_weights_sha256": weights_sha256},
        "model_receipt": model_receipt,
        "forward_receipts": {"train": train_forward, "validation": validation_forward},
        "curve_artifact": {"filename": "curves.npz", "sha256": curve_receipt["sha256"]},
        "heads_artifact": {"filename": "entity-heads.pt", "sha256": shared.sha256_file(heads_path)},
        "target_reads": 0,
        "backbone_parameter_updates": 0,
        "formal_paper_evidence": False,
    }
    shared.atomic_json(output_root / "aggregate-results.json", results)
    torch.cuda.synchronize()
    shared.atomic_json(output_root / "resource-receipt.json", {"wall_seconds": time.time() - started, "peak_gpu_allocated_mib": max(train_forward["peak_gpu_allocated_mib"], validation_forward["peak_gpu_allocated_mib"]), "peak_gpu_reserved_mib": max(train_forward["peak_gpu_reserved_mib"], validation_forward["peak_gpu_reserved_mib"]), "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, "resource_contention": config["resource_contention"], "efficiency_comparison_allowed": False})
    shared.atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "finished", "stage": "source", "exit_code": 0, "verdict": verdict, "target_reads": 0})
    build_manifest(output_root)
    print(json.dumps({"run_id": RUN_ID, "verdict": verdict, "entity_ap": {key: value["entity_average_precision"] for key, value in metrics.items()}}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="B10冻结骨干独立多算子实体头S1快速实验")
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    try:
        config = source.load_json(config_path)
        validate_config(config)
        load_source_contract(config)
        if args.validate_config:
            print("配置核验通过")
            return 0
        source.require(args.run, "必须指定 --run 或 --validate-config")
        run(config, config_path)
        return 0
    except source.ExperimentError as error:
        print(str(error), file=sys.stderr)
        return error.exit_code
    except shared.StageError as error:
        print(str(error), file=sys.stderr)
        return error.exit_code
    except Exception as error:  # noqa: BLE001
        traceback.print_exc()
        print(f"未预期错误：{error}", file=sys.stderr)
        return source.EXIT_RUNTIME


if __name__ == "__main__":
    sys.exit(main())
