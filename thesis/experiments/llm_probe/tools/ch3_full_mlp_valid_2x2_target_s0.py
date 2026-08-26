#!/usr/bin/env python3
"""把已封印的有效 2x2 原样评价到 LSPR24，不训练、不选择。"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import ch3_full_mlp_s0_precision_aggregation_diagnostic as shared
import ch3_full_mlp_valid_2x2_source_s0 as source


RUN_ID = "ch3-full-mlp-valid-2x2-target-s0-seed42-v1"
SCHEMA_VERSION = "ch3-full-mlp-valid-2x2-target-s0-config-v1"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def validate_config(config: dict[str, Any]) -> None:
    source.require(config.get("schema_version") == SCHEMA_VERSION, "配置模式版本不符")
    source.require(config.get("run_id") == RUN_ID, "运行身份不符")
    source.require(config.get("dataset_year") == "LSPR24", "目标年度必须是 LSPR24")
    source.require(config.get("target_arrays") == ["X24", "y24", "I24", "M24", "s24", "d24"], "目标数组白名单不符")
    source.require(config.get("target_informed") is True, "必须标记 target_informed=true")
    source.require(config.get("independent_test") is False, "不得标记为独立测试")
    source.require(config.get("selection_or_tuning_on_target") is False, "目标年禁止选择或调参")
    source.require(config.get("training_runs") == 0 and config.get("parameter_updates") == 0, "目标描述禁止训练")
    source.require(Path(config["output_root"]).name == RUN_ID, "输出目录与运行身份不符")
    source.require(len(config.get("source_artifacts", {})) == 3, "源年封印制品清单不完整")


def load_source_contract(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    source_config_path = PROJECT_ROOT / config["source_config_path"]
    source.require(source_config_path.is_file(), f"源年配置不存在：{source_config_path}", source.EXIT_INPUT)
    source.require(shared.sha256_file(source_config_path) == config["source_config_sha256"], "源年配置摘要漂移", source.EXIT_INPUT)
    source_config = source.load_json(source_config_path)
    source.validate_config(source_config)
    source_run_root = Path(config["source_run_root"])
    if not source_run_root.is_dir():
        source_run_root = PROJECT_ROOT / "runs" / "diagnostics" / source_run_root.name
    for name, expected_sha256 in config["source_artifacts"].items():
        path = source_run_root / name
        source.require(path.is_file(), f"源年封印制品不存在：{path}", source.EXIT_INPUT)
        source.require(shared.sha256_file(path) == expected_sha256, f"源年封印制品摘要漂移：{name}", source.EXIT_INPUT)
    seal = source.load_json(source_run_root / "source-seal.json")
    source.require(seal.get("sealed") is True and seal.get("target_reads") == 0, "源年运行未合法封印", source.EXIT_INPUT)
    formula = source.load_json(source_run_root / "formula-identity-receipt.json")
    source.require(formula.get("same_checkpoint_flow_identity") is True, "源年逐流身份护栏未通过", source.EXIT_INPUT)
    return source_config, source.load_reference(source_config)


def build_manifest(output_root: Path) -> None:
    files = {}
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "run.log"}:
            relative = path.relative_to(output_root).as_posix()
            files[relative] = {"bytes": path.stat().st_size, "sha256": shared.sha256_file(path)}
    shared.atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-full-mlp-valid-2x2-target-s0-manifest-v1",
            "run_id": RUN_ID,
            "complete": True,
            "target_informed": True,
            "independent_test": False,
            "training_runs": 0,
            "parameter_updates": 0,
            "excluded_append_only_files": ["run.log"],
            "files": files,
        },
    )


def run_target(config: dict[str, Any], config_path: Path) -> None:
    np = shared.require_numpy()
    torch = shared.require_torch()
    source_config, parent = load_source_contract(config)
    output_root = Path(config["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    shared.atomic_json(output_root / "config.json", config)
    shared.atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "running", "stage": "target", "target_informed": True})
    started = time.time()
    inputs = shared.validate_inputs(parent, tuple(config["target_arrays"]))
    shared.atomic_json(output_root / "input-validation-receipt.json", inputs)
    cache_root = Path(parent["paths"]["cache_root"])
    arrays = {
        name: np.load(cache_root / f"{name}.npy", allow_pickle=name in {"s24", "d24"})
        for name in config["target_arrays"]
    }
    entity_base = shared.build_target_context(parent, arrays)
    flow_labels = arrays["y24"]
    length = parent["model"]["sequence_length"]
    seen = np.zeros(len(flow_labels), dtype=bool)
    indices = arrays["I24"][:, :length]
    masks = arrays["M24"][:, :length] > 0.5
    seen[indices[masks]] = True
    order = shared.ordered_exposures(seen, entity_base["flow_entity"])
    scored_entities = np.zeros(entity_base["count"], dtype=bool)
    scored_entities[order["entity_ids"]] = True
    device = torch.device("cuda")
    profiles = shared.validate_precision_profiles(parent)
    profile = dict(profiles["bf16"])
    profile["profile_id"] = source_config["precision_profile"]
    tensors = {
        "X": torch.from_numpy(arrays["X24"]).to(device),
        "I": torch.from_numpy(arrays["I24"]).to(device),
        "M": torch.from_numpy(arrays["M24"]).to(device),
    }
    for name in config["target_arrays"]:
        if name != "y24":
            arrays.pop(name, None)
    cells: dict[str, Any] = {}
    curve_vectors_all: dict[str, Any] = {}
    curve_objects: dict[str, Any] = {}
    flow_receipts: dict[str, Any] = {}
    for checkpoint in source.CHECKPOINT_ORDER:
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
            None,
            len(flow_labels),
            f"target/{checkpoint}",
        )
        source.require(np.array_equal(actual_seen, seen), f"{checkpoint} 目标打分流集合漂移", source.EXIT_RUNTIME)
        ordered_logits = logits[order["flow_ids"]].astype(np.float64)
        source.require(bool(np.isfinite(ordered_logits).all()), f"{checkpoint} 出现非有限对数几率", source.EXIT_RUNTIME)
        probabilities = shared.stable_sigmoid(ordered_logits)
        flow_ap = float(shared.require_metrics()(flow_labels[order["flow_ids"]], probabilities))
        flow_identity = {
            "checkpoint": checkpoint,
            "flow_count": int(len(probabilities)),
            "flow_order_sha256": source.array_sha256(order["flow_ids"]),
            "logits_sha256": source.array_sha256(ordered_logits),
            "probabilities_sha256": source.array_sha256(probabilities),
            "weights_sha256": weights_sha256,
            "model_receipt": model_receipt,
            "forward_receipt": forward_receipt,
        }
        flow_receipts[checkpoint] = flow_identity
        for cell in source.CELL_ORDER:
            if source_config["cells"][cell]["checkpoint"] != checkpoint:
                continue
            metrics, vectors, _, objects = source.evaluate_cell(
                source_config,
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
    source.require(cells["C00"]["flow_identity"] == cells["C01p"]["flow_identity"], "B00 配对格逐流身份不一致", source.EXIT_RUNTIME)
    source.require(cells["C10"]["flow_identity"] == cells["C11p"]["flow_identity"], "B10 配对格逐流身份不一致", source.EXIT_RUNTIME)
    comparisons = {
        "B00_max_vs_mix": source.compare_pair("C00", "C01p", cells, curve_objects, curve_vectors_all),
        "B10_max_vs_mix": source.compare_pair("C10", "C11p", cells, curve_objects, curve_vectors_all),
    }
    curve_receipt = shared.atomic_npz(output_root / "curves.npz", curve_vectors_all)
    results = {
        "schema_version": "ch3-full-mlp-valid-2x2-target-s0-results-v1",
        "run_id": RUN_ID,
        "scientific_status": "LSPR24描述性评价完成",
        "target_informed": True,
        "independent_test": False,
        "selection_or_tuning_on_target": False,
        "training_runs": 0,
        "parameter_updates": 0,
        "identity": {
            "config_sha256": shared.sha256_file(config_path),
            "code_sha256": shared.sha256_file(Path(__file__)),
            "source_config_sha256": config["source_config_sha256"],
            "source_artifacts": config["source_artifacts"],
        },
        "cells": cells,
        "comparisons": comparisons,
        "interaction_entity_average_precision": float(
            cells["C11p"]["entity_average_precision"]
            - cells["C10"]["entity_average_precision"]
            - cells["C01p"]["entity_average_precision"]
            + cells["C00"]["entity_average_precision"]
        ),
        "curve_artifact": {"filename": "curves.npz", "sha256": curve_receipt["sha256"]},
        "resource_contention": config["resource_contention"],
        "formal_paper_evidence": False,
    }
    shared.atomic_json(output_root / "flow-identity-receipt.json", flow_receipts)
    shared.atomic_json(output_root / "aggregate-results.json", results)
    torch.cuda.synchronize()
    shared.atomic_json(
        output_root / "resource-receipt.json",
        {
            "wall_seconds": time.time() - started,
            "peak_gpu_allocated_mib": max(item["forward_receipt"]["peak_gpu_allocated_mib"] for item in flow_receipts.values()),
            "peak_gpu_reserved_mib": max(item["forward_receipt"]["peak_gpu_reserved_mib"] for item in flow_receipts.values()),
            "peak_process_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
            "resource_contention": config["resource_contention"],
            "efficiency_comparison_allowed": False,
        },
    )
    shared.atomic_json(output_root / "status.json", {"run_id": RUN_ID, "state": "finished", "stage": "target", "exit_code": 0, "target_informed": True})
    build_manifest(output_root)
    print(json.dumps({"run_id": RUN_ID, "cells": {key: value["entity_average_precision"] for key, value in cells.items()}}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="全容量 MLP 有效2x2 LSPR24零训练描述评价")
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
        run_target(config, config_path)
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
