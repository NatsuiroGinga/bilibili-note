# -*- coding: utf-8 -*-
"""全容量 MLP 严格过去 CPA 协议 A Q0。"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import ch3_full_mlp_complete_entity_lp_protocol_a_q0 as parent


np = parent.np
torch = parent.torch
nn = parent.nn
average_precision_score = parent.average_precision_score

SCHEMA_VERSION = "ch3-full-mlp-strict-past-cpa-protocol-a-q0-config-v1"
RESULT_SCHEMA_VERSION = "ch3-full-mlp-strict-past-cpa-protocol-a-q0-results-v1"
RUN_ID = "ch3-full-mlp-strict-past-cpa-protocol-a-q0-seed42-v1"
PARENT_RUN_ID = "ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1"
CELL_ORDER = ("S10", "S11")
EVALUATION_ORDER = ("B10", "O11", "S10", "S11")
CELLS = {
    "S10": {
        "strict_past_causal_prefix_aggregation": True,
        "learned_lp_pooling": False,
    },
    "S11": {
        "strict_past_causal_prefix_aggregation": True,
        "learned_lp_pooling": True,
    },
}
SOURCE_ARRAYS = parent.SOURCE_ARRAYS
TARGET_ARRAYS = parent.TARGET_ARRAYS
DR_FPR_GRID = parent.DR_FPR_GRID
PARENT_BUILD_MODEL = parent.build_model
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="全容量 MLP 严格过去 CPA 协议 A Q0")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--validate-config", action="store_true", help="只核验配置")
    parser.add_argument("--resume", action="store_true", help="恢复同身份在途检查点")
    parser.add_argument("--publish-only", action="store_true", help="仅发布已有聚合指标")
    parser.add_argument("--resource-receipt", help="启动器资源准入收据")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser.parse_args()


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    if config.get("model_key") != "full_mlp" or config.get("cells") != CELLS:
        raise ValueError("只允许全容量 MLP 的 S10/S11 严格过去 CPA 单元")
    if config.get("source_arrays") != list(SOURCE_ARRAYS) or config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("源年或目标年数组合同不符")
    expected_training = {
        "seed": 42,
        "sequence_length": 128,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.0003162277660168379,
        "weight_decay": 0.0,
        "dropout": 0.1,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
        "validation_fraction": 0.1,
        "time_tail_fraction": 0.15,
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
    }
    if config.get("training") != expected_training:
        raise ValueError("协议 A 训练合同不符")
    expected_candidate = {
        "hidden_depth": 8,
        "hidden_size": 512,
        "activation": "relu",
        "dropout": 0.1,
        "context_definition": "strict_past_mean_h1_to_h_t_minus_1_first_flow_zero",
        "stable_row_order_unchanged": True,
        "parameter_formula": "m*d^2+(m+84)*d+2",
        "parameter_count": 2_144_258,
        "complexity_same_as_parent_cpa": True,
    }
    if config.get("candidate") != expected_candidate:
        raise ValueError("严格过去 CPA 或冻结骨干合同不符")
    evaluation = config.get("evaluation", {})
    if evaluation.get("dr_fpr_grid") != list(DR_FPR_GRID):
        raise ValueError("六档误报预算不符")
    if evaluation.get("length_buckets") != [[1, 2], [3, 10], [11, 100], [101, 1000], [1001, None]]:
        raise ValueError("长度桶不符")
    if evaluation.get("target_load_after_source_gate") is not True or evaluation.get("target_evaluation_calls") != 4:
        raise ValueError("目标年一次加载与四模型评价合同不符")
    if evaluation.get("source_gate_pairs") != [["S10", "B10"], ["S11", "O11"]]:
        raise ValueError("源年对照配对不符")
    if evaluation.get("minimum_positive_length_buckets_per_pair") != 2:
        raise ValueError("长度桶通过门不符")
    if config.get("artifact_policy") != {
        "persist_selected_checkpoint_per_cell": True,
        "persist_every_epoch_checkpoint_per_cell": True,
        "persist_inflight_epoch_checkpoint": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_complete_budget_curve_aggregate": True,
        "reuse_parent_checkpoints_read_only": True,
    }:
        raise ValueError("制品合同不符")
    if config.get("resource_contract") != {
        "minimum_free_gpu_memory_mib": 12_288,
        "minimum_cgroup_available_memory_gib": 30,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_jobs": 1,
        "maximum_parallel_cells_per_job": 1,
        "resource_sample_interval_seconds": 5,
        "estimated_training_minutes": [8, 12],
    }:
        raise ValueError("资源合同不符")
    parent_contract = config.get("parent", {})
    if parent_contract.get("run_id") != PARENT_RUN_ID or parent_contract.get("cells") != ["B10", "O11"]:
        raise ValueError("父运行或父对照单元不符")
    if parent_contract.get("config_sha256") != "f13ddd96d8a09b122004fb2c281cedb4411f03420a0eddc04cfc03b46f943f34":
        raise ValueError("父配置摘要不符")
    if parent_contract.get("code_sha256") != "45ad7d1be85832e4b235a8942615e4aad7b94c154ec2cef7ad00ec2510feb2da":
        raise ValueError("父代码摘要不符")
    if config.get("target_informed") is not True or config.get("screening_only") is not True:
        raise ValueError("筛选证据身份不符")
    if config.get("formal_paper_evidence") or config.get("independent_test"):
        raise ValueError("本 Q0 不能声称正式论文证据或独立测试")
    if config.get("target_year_arrays_read") != 0 or config.get("source_gate_failure_target_reads") != 0:
        raise ValueError("源年失败必须保持目标年零读取")
    if Path(config.get("paths", {}).get("output_root", "")).name != RUN_ID:
        raise ValueError("输出根与运行身份不符")
    if config.get("swanlab", {}).get("group") != RUN_ID:
        raise ValueError("SwanLab 分组与运行身份不符")


if nn is not None:
    class StrictPastFullCapacityMLP(nn.Module):
        """只把父 CPA 的自包含前缀替换为严格过去前缀。"""

        def __init__(self, feature_count: int, hidden_depth: int, hidden_size: int, dropout: float):
            super().__init__()
            layers: list[nn.Module] = []
            input_size = feature_count
            for _ in range(hidden_depth - 1):
                layers.extend((nn.Linear(input_size, hidden_size), nn.ReLU(), nn.Dropout(dropout)))
                input_size = hidden_size
            self.encoder = nn.Sequential(*layers)
            self.fusion = nn.Sequential(
                nn.Linear(hidden_size * 2, hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout),
            )
            self.output = nn.Linear(hidden_size, 1)
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

        @property
        def p(self) -> torch.Tensor:
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            mask = valid.to(values.dtype)
            hidden = self.encoder(values) * mask.unsqueeze(-1)
            inclusive_sum = torch.cumsum(hidden, dim=1)
            inclusive_count = torch.cumsum(mask, dim=1)
            past_sum = torch.cat((torch.zeros_like(inclusive_sum[:, :1]), inclusive_sum[:, :-1]), dim=1)
            past_count = torch.cat((torch.zeros_like(inclusive_count[:, :1]), inclusive_count[:, :-1]), dim=1)
            has_past = (past_count > 0).to(hidden.dtype)
            context = past_sum / past_count.clamp(min=1.0).unsqueeze(-1)
            context = context * has_past.unsqueeze(-1) * mask.unsqueeze(-1)
            fused = self.fusion(torch.cat((hidden, context), dim=-1)) * mask.unsqueeze(-1)
            return self.output(fused).squeeze(-1)
else:
    class StrictPastFullCapacityMLP:
        pass


def build_model(config: dict[str, Any], cell: str) -> Any:
    if torch is None or nn is None:
        raise RuntimeError("正式计算缺少 PyTorch GPU 依赖")
    if cell not in CELL_ORDER:
        raise ValueError(f"未知严格过去单元：{cell}")
    candidate = config["candidate"]
    model = StrictPastFullCapacityMLP(
        83,
        candidate["hidden_depth"],
        candidate["hidden_size"],
        config["training"]["dropout"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != candidate["parameter_count"]:
        raise RuntimeError(f"严格过去模型参数量不符：{actual}")
    return model


def train_new_cell(
    config: dict[str, Any],
    cell: str,
    output_root: Path,
    run_identity: dict[str, Any],
    source: dict[str, np.ndarray],
    train_rows: np.ndarray,
    validation_rows: np.ndarray,
    device: torch.device,
    resume: bool,
) -> dict[str, Any]:
    original_builder = parent.build_model
    try:
        parent.build_model = build_model
        return parent.train_cell(
            config,
            cell,
            output_root,
            run_identity,
            source,
            train_rows,
            validation_rows,
            device,
            resume,
        )
    finally:
        parent.build_model = original_builder


def _require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"缺少{description}：{path}")


def validate_parent_artifacts(config: dict[str, Any]) -> dict[str, Any]:
    contract = config["parent"]
    parent_config_path = Path(contract["config_path"])
    parent_code_path = Path(contract["code_path"])
    parent_root = Path(contract["output_root"])
    _require_file(parent_config_path, "父配置")
    _require_file(parent_code_path, "父代码")
    if parent.sha256_file(parent_config_path) != contract["config_sha256"]:
        raise RuntimeError("父配置 SHA-256 不符")
    if parent.sha256_file(parent_code_path) != contract["code_sha256"]:
        raise RuntimeError("父代码 SHA-256 不符")
    parent_config = parent.load_json(parent_config_path)
    parent.validate_config(parent_config)
    for key in ("model_key", "source_arrays", "target_arrays", "training"):
        if parent_config[key] != config[key]:
            raise RuntimeError(f"父配置与新配置的 {key} 不一致")
    if parent_config["candidate"] != {
        key: config["candidate"][key]
        for key in ("hidden_depth", "hidden_size", "activation", "dropout", "parameter_formula", "parameter_count")
    }:
        raise RuntimeError("父骨干与新骨干不一致")
    for key in ("dr_fpr_grid", "length_buckets"):
        if parent_config["evaluation"][key] != config["evaluation"][key]:
            raise RuntimeError(f"父评价合同 {key} 与新实验不一致")
    status_path = parent_root / "status.json"
    seal_path = parent_root / "selection_frozen.json"
    source_gate_path = parent_root / "source-gate-results.json"
    for path, description in (
        (status_path, "父完成状态"),
        (seal_path, "父选择封印"),
        (source_gate_path, "父源年门收据"),
    ):
        _require_file(path, description)
    status = parent.load_json(status_path)
    if status.get("state") != "complete" or status.get("exit_code") != 0:
        raise RuntimeError("父运行未以 complete/exit=0 完成")
    source_gate = parent.load_json(source_gate_path)
    if source_gate.get("target_year_arrays_read") != 0:
        raise RuntimeError("父源年门不是目标年零读取状态")
    seal = parent.load_json(seal_path)
    if seal.get("run_id") != PARENT_RUN_ID or seal.get("all_four_cells_sealed") is not True:
        raise RuntimeError("父选择未完整封印")
    if seal.get("config_sha256") != contract["config_sha256"]:
        raise RuntimeError("父选择封印的配置摘要不符")
    parent_identity = seal.get("identity", {})
    if (
        parent_identity.get("config_sha256") != contract["config_sha256"]
        or parent_identity.get("code_sha256") != contract["code_sha256"]
        or not parent_identity.get("source_data_inventory_sha256")
    ):
        raise RuntimeError("父选择封印的代码或源数据身份不完整")
    parent_cells: dict[str, Any] = {}
    for cell in contract["cells"]:
        receipt_path = parent_root / "receipts" / f"selection-{cell}.json"
        _require_file(receipt_path, f"父 {cell} 选择收据")
        receipt = parent.load_json(receipt_path)
        selection = seal.get("cells", {}).get(cell)
        if not isinstance(selection, dict):
            raise RuntimeError(f"父选择封印缺少 {cell}")
        if receipt.get("selection") != selection or receipt.get("checkpoint") != selection.get("checkpoint"):
            raise RuntimeError(f"父 {cell} 选择封印与收据不一致")
        receipt_identity = receipt.get("identity", {})
        if (
            receipt_identity.get("run_id") != PARENT_RUN_ID
            or receipt_identity.get("cell") != cell
            or receipt_identity.get("config_sha256") != contract["config_sha256"]
            or receipt_identity.get("code_sha256") != contract["code_sha256"]
            or receipt_identity.get("source_data_inventory_sha256")
            != parent_identity["source_data_inventory_sha256"]
        ):
            raise RuntimeError(f"父 {cell} 选择收据身份不符")
        checkpoint_path = parent_root / selection["checkpoint"]["filename"]
        _require_file(checkpoint_path, f"父 {cell} 选中检查点")
        if parent.sha256_file(checkpoint_path) != selection["checkpoint"]["sha256"]:
            raise RuntimeError(f"父 {cell} 选中检查点摘要不符")
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if checkpoint.get("identity") != receipt.get("identity"):
            raise RuntimeError(f"父 {cell} 检查点身份与选择收据不一致")
        model = PARENT_BUILD_MODEL(parent_config, cell)
        model.load_state_dict(checkpoint["model"], strict=True)
        del model, checkpoint
        parent_cells[cell] = {
            "selection": selection,
            "checkpoint_path": checkpoint_path,
            "receipt_sha256": parent.sha256_file(receipt_path),
        }
    return {
        "config": parent_config,
        "root": parent_root,
        "cells": parent_cells,
        "status_sha256": parent.sha256_file(status_path),
        "selection_frozen_sha256": parent.sha256_file(seal_path),
        "source_gate_sha256": parent.sha256_file(source_gate_path),
        "config_sha256": contract["config_sha256"],
        "code_sha256": contract["code_sha256"],
        "source_data_inventory_sha256": parent_identity["source_data_inventory_sha256"],
    }


def model_specs(
    config: dict[str, Any],
    output_root: Path,
    selections: dict[str, Any],
    parent_artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for cell in ("B10", "O11"):
        specs.append(
            {
                "cell": cell,
                "config": parent_artifacts["config"],
                "selection": parent_artifacts["cells"][cell]["selection"],
                "checkpoint_path": parent_artifacts["cells"][cell]["checkpoint_path"],
                "builder": PARENT_BUILD_MODEL,
                "parent": True,
            }
        )
    for cell in CELL_ORDER:
        specs.append(
            {
                "cell": cell,
                "config": config,
                "selection": selections[cell],
                "checkpoint_path": output_root / selections[cell]["checkpoint"]["filename"],
                "builder": build_model,
                "parent": False,
            }
        )
    return specs


def load_selected_model(spec: dict[str, Any], device: torch.device) -> Any:
    checkpoint_path = spec["checkpoint_path"]
    selection = spec["selection"]
    if parent.sha256_file(checkpoint_path) != selection["checkpoint"]["sha256"]:
        raise RuntimeError(f"{spec['cell']} 选中检查点摘要不符")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model = spec["builder"](spec["config"], spec["cell"]).to(device)
    model.load_state_dict(checkpoint["model"], strict=True)
    if abs(float(model.p.detach()) - float(selection["p_at_selection"])) > 1e-9:
        raise RuntimeError(f"{spec['cell']} 回载后的 p 与选择收据不符")
    return model


def evaluate_source_gate(
    config: dict[str, Any],
    output_root: Path,
    source: dict[str, np.ndarray],
    validation_rows: np.ndarray,
    selections: dict[str, Any],
    parent_artifacts: dict[str, Any],
    device: torch.device,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    flow_entity = parent.build_flow_entity(source["I23"], source["M23"], source["E23"], len(source["y23"]))
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    entity_lengths = np.zeros(entity_count, dtype=np.int64)
    np.maximum.at(entity_labels, flow_entity, source["y23"])
    np.add.at(entity_lengths, flow_entity, 1)
    gX = torch.from_numpy(source["X23"]).to(device)
    gy = torch.from_numpy(source["y23"]).to(device)
    gI = torch.from_numpy(source["I23"]).to(device)
    gM = torch.from_numpy(source["M23"]).to(device)
    branches: dict[str, Any] = {}
    entity_scores: dict[str, np.ndarray] = {}
    curve_arrays: dict[str, np.ndarray] = {}
    for spec in model_specs(config, output_root, selections, parent_artifacts):
        cell = spec["cell"]
        model = load_selected_model(spec, device)
        predictions, _, flow_ids = parent.predict_sequences(
            spec["config"], model, validation_rows, gX, gy, gI, gM
        )
        flow_scores = np.full(len(source["y23"]), np.nan, dtype=np.float32)
        seen = np.zeros(len(source["y23"]), dtype=np.bool_)
        flow_scores[flow_ids] = predictions
        seen[flow_ids] = True
        p_value = float(model.p.detach()) if spec["config"]["cells"][cell]["learned_lp_pooling"] else None
        metrics, scores, curve = parent.evaluate_entity_branch(
            flow_scores,
            seen,
            source["y23"],
            flow_entity,
            entity_labels,
            p_value,
            config["evaluation"]["dr_fpr_grid"],
        )
        metrics.update(
            {
                "p": p_value,
                "flow_score_sha256": hashlib.sha256(np.ascontiguousarray(predictions).view(np.uint8)).hexdigest(),
                "flow_ids_sha256": hashlib.sha256(np.ascontiguousarray(flow_ids).view(np.uint8)).hexdigest(),
                "source": "parent_reused" if spec["parent"] else "new_training",
            }
        )
        branches[cell] = metrics
        entity_scores[cell] = scores
        for field, values in curve.items():
            curve_arrays[f"source__{cell}__{field}"] = values
        del model
        torch.cuda.empty_cache()
    del gX, gy, gI, gM
    torch.cuda.empty_cache()
    buckets = parent.length_bucket_metrics(
        entity_scores,
        entity_labels,
        entity_lengths,
        config["evaluation"]["length_buckets"],
        config["evaluation"]["dr_fpr_grid"],
    )
    criteria: dict[str, bool] = {}
    comparisons: dict[str, Any] = {}
    minimum_buckets = config["evaluation"]["minimum_positive_length_buckets_per_pair"]
    for candidate, baseline in config["evaluation"]["source_gate_pairs"]:
        positive_buckets = sum(
            item["branches"].get(candidate, {}).get("entity_average_precision") is not None
            and item["branches"].get(baseline, {}).get("entity_average_precision") is not None
            and item["branches"][candidate]["entity_average_precision"]
            > item["branches"][baseline]["entity_average_precision"]
            for item in buckets
        )
        pair = f"{candidate}_vs_{baseline}"
        pair_criteria = {
            "entity_ap_positive": branches[candidate]["entity_average_precision"] > branches[baseline]["entity_average_precision"],
            "curve_area_positive": branches[candidate]["normalized_area_0_8_fpr"] > branches[baseline]["normalized_area_0_8_fpr"],
            "flow_ap_not_lower": branches[candidate]["flow_average_precision"] >= branches[baseline]["flow_average_precision"],
            "dr4_not_lower": branches[candidate]["dr_at_fpr"]["fpr_0.04"] >= branches[baseline]["dr_at_fpr"]["fpr_0.04"],
            "dr8_not_lower": branches[candidate]["dr_at_fpr"]["fpr_0.08"] >= branches[baseline]["dr_at_fpr"]["fpr_0.08"],
            "positive_length_buckets_at_least_two": positive_buckets >= minimum_buckets,
        }
        criteria.update({f"{pair}__{name}": value for name, value in pair_criteria.items()})
        candidate_x = curve_arrays[f"source__{candidate}__realized_fpr"]
        candidate_dr = curve_arrays[f"source__{candidate}__detection_rate"]
        baseline_x = curve_arrays[f"source__{baseline}__realized_fpr"]
        baseline_dr = curve_arrays[f"source__{baseline}__detection_rate"]
        if not np.array_equal(candidate_x, baseline_x):
            raise RuntimeError(f"{pair} 完整预算曲线横轴不一致")
        selected = candidate_x <= 0.08
        difference = candidate_dr[selected] - baseline_dr[selected]
        comparisons[pair] = {
            "candidate": candidate,
            "baseline": baseline,
            "entity_ap_difference": branches[candidate]["entity_average_precision"] - branches[baseline]["entity_average_precision"],
            "normalized_area_difference": branches[candidate]["normalized_area_0_8_fpr"] - branches[baseline]["normalized_area_0_8_fpr"],
            "flow_ap_difference": branches[candidate]["flow_average_precision"] - branches[baseline]["flow_average_precision"],
            "positive_length_buckets": positive_buckets,
            "advantage_point_fraction_0_8_fpr": float((difference > 0).mean()),
            "harmful_point_fraction_0_8_fpr": float((difference < 0).mean()),
            "criteria": pair_criteria,
        }
    passed = all(criteria.values())
    result = {
        "schema_version": "ch3-full-mlp-strict-past-cpa-source-gate-v1",
        "branches": branches,
        "length_buckets": buckets,
        "comparisons": comparisons,
        "criteria": criteria,
        "passed": passed,
        "verdict": "source_gate_passed" if passed else "source_gate_rejected",
        "same_selection_and_source_description": True,
        "parent_cells_reused_read_only": ["B10", "O11"],
        "new_cells_trained": ["S10", "S11"],
        "target_year_arrays_read": 0,
    }
    return result, curve_arrays


def build_manifest(output_root: Path, run_id: str) -> None:
    files: dict[str, Any] = {}
    names = (
        "config.json",
        "parent-artifact-receipt.json",
        "selection_frozen.json",
        "source-gate-results.json",
        "source-complete-alert-budget-curves.npz",
        "length-bucket-results.json",
        "aggregate-results.json",
        "complete-alert-budget-curves.npz",
        "complete-alert-budget-curves-receipt.json",
        "resource-receipt.json",
        "swanlab-receipt.json",
        "status.json",
    )
    for name in names:
        path = output_root / name
        if path.is_file():
            files[name] = {"bytes": path.stat().st_size, "sha256": parent.sha256_file(path)}
    for cell in CELL_ORDER:
        relatives = (
            f"checkpoints/selected-{cell}.pt",
            f"receipts/selection-{cell}.json",
            f"receipts/target-evaluation-{cell}/receipt.json",
            f"receipts/target-evaluation-{cell}/complete-alert-budget-curve.npz",
        )
        for relative in relatives:
            path = output_root / relative
            if path.is_file():
                files[relative] = {"bytes": path.stat().st_size, "sha256": parent.sha256_file(path)}
        epoch_root = output_root / "checkpoints" / "epochs" / cell
        for epoch_path in sorted(epoch_root.glob("epoch-*.pt")):
            relative = str(epoch_path.relative_to(output_root))
            files[relative] = {"bytes": epoch_path.stat().st_size, "sha256": parent.sha256_file(epoch_path)}
    for cell in ("B10", "O11"):
        for relative in (
            f"receipts/target-evaluation-{cell}/receipt.json",
            f"receipts/target-evaluation-{cell}/complete-alert-budget-curve.npz",
        ):
            path = output_root / relative
            if path.is_file():
                files[relative] = {"bytes": path.stat().st_size, "sha256": parent.sha256_file(path)}
    parent.atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-full-mlp-strict-past-cpa-protocol-a-q0-manifest-v1",
            "run_id": run_id,
            "files": files,
            "parent_checkpoints_copied": False,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "target_year_arrays_read": 7 if "complete-alert-budget-curves.npz" in files else 0,
        },
    )


def _save_curves(path: Path, curves: dict[str, np.ndarray]) -> None:
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **curves)
    os.replace(temporary, path)


def _parent_receipt(parent_artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "ch3-strict-past-cpa-parent-artifact-receipt-v1",
        "run_id": PARENT_RUN_ID,
        "config_sha256": parent_artifacts["config_sha256"],
        "code_sha256": parent_artifacts["code_sha256"],
        "status_sha256": parent_artifacts["status_sha256"],
        "selection_frozen_sha256": parent_artifacts["selection_frozen_sha256"],
        "source_gate_sha256": parent_artifacts["source_gate_sha256"],
        "source_data_inventory_sha256": parent_artifacts["source_data_inventory_sha256"],
        "cells": {
            cell: {
                "selection_receipt_sha256": parent_artifacts["cells"][cell]["receipt_sha256"],
                "checkpoint_sha256": parent_artifacts["cells"][cell]["selection"]["checkpoint"]["sha256"],
                "selected_epoch": parent_artifacts["cells"][cell]["selection"]["selected_epoch"],
                "p_at_selection": parent_artifacts["cells"][cell]["selection"]["p_at_selection"],
            }
            for cell in ("B10", "O11")
        },
        "read_only_reuse": True,
    }


def evaluate_target(
    config: dict[str, Any],
    output_root: Path,
    selections: dict[str, Any],
    parent_artifacts: dict[str, Any],
    run_identity: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    cache_root = Path(config["paths"]["cache_root"])
    target_inventory = parent.data_inventory(cache_root, TARGET_ARRAYS)
    target = parent.load_arrays(cache_root, TARGET_ARRAYS)
    parent.write_status(
        output_root,
        "running",
        "target-evaluation-loaded",
        None,
        "LSPR24 七个数组已一次加载，正在评价四个封印模型",
        7,
    )
    if target["X24"].shape != (20_227_356, 83):
        raise RuntimeError("LSPR24 冻结缓存形状不符")
    keys = np.array(
        [left + "|" + right if left <= right else right + "|" + left for left, right in zip(target["s24"], target["d24"])],
        dtype=object,
    )
    _, flow_entity = np.unique(keys, return_inverse=True)
    entity_count = int(flow_entity.max()) + 1
    entity_labels = np.zeros(entity_count, dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, target["y24"])
    entity_lengths = np.bincount(flow_entity, minlength=entity_count).astype(np.int64)
    flow_positive_rate = float(target["y24"].astype(np.float64).mean())
    if entity_count != 47_115 or int(entity_labels.sum()) != 752 or abs(flow_positive_rate - 0.0257073138) >= 1e-9:
        raise RuntimeError("LSPR24 实体与标签自检失败")
    cells: dict[str, Any] = {}
    all_curves: dict[str, np.ndarray] = {}
    calls = 0
    reused = 0
    evaluation_peak_gpu_mib = 0.0
    evaluation_started = time.time()
    for call_index, spec in enumerate(model_specs(config, output_root, selections, parent_artifacts), start=1):
        cell = spec["cell"]
        identity = {
            **run_identity,
            "target_data_inventory_sha256": target_inventory["sha256"],
            "cell": cell,
            "checkpoint_sha256": spec["selection"]["checkpoint"]["sha256"],
            "source": "parent_reused" if spec["parent"] else "new_training",
        }
        restored = parent.load_target_evaluation(output_root, cell, identity)
        if restored is not None:
            cell_result, curves = restored
            cells[cell] = cell_result
            all_curves.update(curves)
            reused += 1
            continue
        model = load_selected_model(spec, torch.device("cuda"))
        torch.cuda.reset_peak_memory_stats()
        started = time.time()
        flow_scores, seen = parent.score_target(spec["config"], model, target, torch.device("cuda"))
        evaluation_seconds = time.time() - started
        calls += 1
        evaluation_peak_gpu_mib = max(evaluation_peak_gpu_mib, torch.cuda.max_memory_allocated() / 2**20)
        p_value = float(model.p.detach()) if spec["config"]["cells"][cell]["learned_lp_pooling"] else None
        metrics, scores, curves = parent.evaluate_entity_branch(
            flow_scores,
            seen,
            target["y24"],
            flow_entity,
            entity_labels,
            p_value,
            config["evaluation"]["dr_fpr_grid"],
        )
        metrics.update(
            {
                "p": p_value,
                "evaluation_seconds": evaluation_seconds,
                "target_evaluation_call": call_index,
                "source": "parent_reused" if spec["parent"] else "new_training",
            }
        )
        buckets = parent.length_bucket_metrics(
            {cell: scores},
            entity_labels,
            entity_lengths,
            config["evaluation"]["length_buckets"],
            config["evaluation"]["dr_fpr_grid"],
        )
        metrics["length_buckets"] = [
            {
                "bucket": item["bucket"],
                "entities": item["entities"],
                "positive_entities": item["positive_entities"],
                "negative_entities": item["negative_entities"],
                **item["branches"][cell],
            }
            for item in buckets
        ]
        cell_result = {
            "cell": cell,
            "selection": spec["selection"],
            "mechanisms": spec["config"]["cells"][cell],
            "target": metrics,
        }
        namespaced_curves = {f"{cell}__{field}": values for field, values in curves.items()}
        parent.save_target_evaluation(output_root, cell, identity, cell_result, namespaced_curves)
        cells[cell] = cell_result
        all_curves.update(namespaced_curves)
        del model, flow_scores, seen, scores
        torch.cuda.empty_cache()
    if calls + reused != 4:
        raise RuntimeError("目标年四模型评价次数不符")
    return (
        {
            "dataset": "LSPR24",
            "flow_count": int(len(target["y24"])),
            "entity_count": entity_count,
            "positive_entity_count": int(entity_labels.sum()),
            "flow_positive_rate": flow_positive_rate,
            "cells": cells,
            "data_inventory": target_inventory,
            "target_disk_loads": 1,
            "target_evaluation_calls": 4,
            "target_evaluation_calls_this_process": calls,
            "target_evaluation_receipts_reused": reused,
            "evaluation_wall_seconds": time.time() - evaluation_started,
            "peak_gpu_allocated_mib": evaluation_peak_gpu_mib,
        },
        all_curves,
    )


def run_experiment(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    if np is None or average_precision_score is None or torch is None or nn is None or not torch.cuda.is_available():
        raise RuntimeError("严格过去 CPA Q0 要求完整 GPU 可选依赖与可用 CUDA")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    config_sha = parent.sha256_file(config_path)
    code_sha = parent.sha256_file(Path(__file__).resolve())
    parent_artifacts = validate_parent_artifacts(config)
    parent_receipt = _parent_receipt(parent_artifacts)
    parent_receipt_path = output_root / "parent-artifact-receipt.json"
    if parent_receipt_path.is_file():
        if parent.load_json(parent_receipt_path) != parent_receipt:
            raise RuntimeError("父制品收据发生变化，拒绝恢复")
    else:
        parent.atomic_json(parent_receipt_path, parent_receipt)
    cache_root = Path(config["paths"]["cache_root"])
    source_inventory = parent.data_inventory(cache_root, SOURCE_ARRAYS)
    if source_inventory["sha256"] != parent_artifacts["source_data_inventory_sha256"]:
        raise RuntimeError("当前 LSPR23 数据清单与父 B10/O11 训练身份不一致")
    run_identity = {
        "config_sha256": config_sha,
        "code_sha256": code_sha,
        "source_data_inventory_sha256": source_inventory["sha256"],
        "parent_artifact_receipt_sha256": parent.canonical_sha256(parent_receipt),
        "context_definition": config["candidate"]["context_definition"],
    }
    frozen_config_path = output_root / "config.json"
    if frozen_config_path.is_file():
        if not args.resume or parent.load_json(frozen_config_path) != config:
            raise RuntimeError("输出根已有不兼容冻结配置")
    else:
        parent.atomic_json(frozen_config_path, config)
    parent.write_status(output_root, "running", "source-selection", None, "父制品核验通过，只加载 LSPR23 并训练 S10/S11")
    selection_path = output_root / "selection_frozen.json"
    selections: dict[str, Any]
    if selection_path.is_file():
        if not args.resume:
            raise RuntimeError("全新运行已存在选择封印")
        seal = parent.load_json(selection_path)
        if seal.get("identity") != run_identity or set(seal.get("cells", {})) != set(CELL_ORDER):
            raise RuntimeError("选择封印身份不符")
        selections = seal["cells"]
        split_stats = seal["source_split"]
        source_gate = seal["source_gate"]
    else:
        source = parent.load_arrays(cache_root, SOURCE_ARRAYS)
        if source["X23"].shape != (16_353_511, 83) or source["I23"].shape != (271_815, 128):
            raise RuntimeError("LSPR23 冻结缓存形状不符")
        train_rows, validation_rows, split_stats = parent.source_split(source, config)
        device = torch.device("cuda")
        selections = {}
        for cell in CELL_ORDER:
            log(f"开始 {cell} 严格过去 CPA 协议 A 训练与选择")
            selections[cell] = train_new_cell(
                config,
                cell,
                output_root,
                run_identity,
                source,
                train_rows,
                validation_rows,
                device,
                args.resume,
            )
        source_gate, source_curves = evaluate_source_gate(
            config,
            output_root,
            source,
            validation_rows,
            selections,
            parent_artifacts,
            device,
        )
        parent.atomic_json(output_root / "source-gate-results.json", source_gate)
        parent.atomic_json(output_root / "length-bucket-results.json", {"source": source_gate["length_buckets"]})
        _save_curves(output_root / "source-complete-alert-budget-curves.npz", source_curves)
        seal = {
            "schema_version": "ch3-strict-past-cpa-protocol-a-selection-frozen-v1",
            "run_id": config["run_id"],
            "config_sha256": config_sha,
            "identity": run_identity,
            "source_data_inventory": source_inventory,
            "protocol": "LSPR23实体不相交验证逐流AP最早最大轮次，20轮跑满且不早停",
            "source_split": split_stats,
            "cells": selections,
            "parent": parent_receipt,
            "source_gate": source_gate,
            "all_new_cells_sealed": True,
            "all_parent_cells_verified": True,
            "target_arrays_loaded_before_seal": 0,
            "sealed_at_unix": time.time(),
        }
        parent.atomic_json(selection_path, seal)
        del source, train_rows, validation_rows
        torch.cuda.empty_cache()
    frozen_seal = parent.load_json(selection_path)
    if frozen_seal.get("all_new_cells_sealed") is not True or frozen_seal.get("all_parent_cells_verified") is not True:
        raise RuntimeError("新单元选择或父对照未全部封印")
    training_seconds = sum(float(selections[cell]["training_seconds"]) for cell in CELL_ORDER)
    if not source_gate.get("passed"):
        result = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "run_id": config["run_id"],
            "model": {"model_key": config["model_key"], "display_name": config["display_name"], **config["candidate"]},
            "parent": parent_receipt,
            "source_selection": {"split": split_stats, "cells": selections},
            "source_gate": source_gate,
            "target_year_arrays_read": 0,
            "target_evaluation_skipped": True,
            "verdict": "source_gate_rejected_target_not_loaded",
            "artifact_policy": {"per_flow_scores_persisted": False, "per_entity_scores_persisted": False},
            "resource": {
                "parameter_count": config["candidate"]["parameter_count"],
                "new_training_cells": 2,
                "training_wall_seconds_sum": training_seconds,
                "gpu_hours": training_seconds / 3600.0,
                "peak_gpu_allocated_mib": max(float(selections[cell]["peak_gpu_allocated_mib"]) for cell in CELL_ORDER),
                "peak_process_rss_mib": parent.process_peak_rss_mib(),
                "launcher_admission_receipt": parent.load_json(Path(args.resource_receipt)) if args.resource_receipt else None,
            },
        }
        parent.atomic_json(output_root / "aggregate-results.json", result)
        parent.write_status(output_root, "finished", "complete", 0, "源年方向门否决，目标年零读取")
        build_manifest(output_root, config["run_id"])
        return
    parent.write_status(output_root, "running", "target-evaluation", None, "源年门通过，一次加载 LSPR24 并同时评价父 B10/O11 与新 S10/S11")
    target_evaluation, curves = evaluate_target(
        config,
        output_root,
        selections,
        parent_artifacts,
        run_identity,
    )
    _save_curves(output_root / "complete-alert-budget-curves.npz", curves)
    curve_path = output_root / "complete-alert-budget-curves.npz"
    curve_receipt = {
        "schema_version": "ch3-strict-past-cpa-complete-alert-budget-curves-v1",
        "artifact": {
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": parent.sha256_file(curve_path),
        },
        "branches": list(EVALUATION_ORDER),
        "complete_over_all_reachable_negative_entity_budgets": True,
        "per_flow_scores_persisted": False,
        "per_entity_scores_persisted": False,
    }
    parent.atomic_json(output_root / "complete-alert-budget-curves-receipt.json", curve_receipt)
    length_payload = parent.load_json(output_root / "length-bucket-results.json")
    length_payload["target"] = {
        cell: target_evaluation["cells"][cell]["target"]["length_buckets"]
        for cell in EVALUATION_ORDER
    }
    parent.atomic_json(output_root / "length-bucket-results.json", length_payload)
    comparisons: dict[str, Any] = {}
    for candidate, baseline in config["evaluation"]["source_gate_pairs"]:
        comparisons[f"{candidate}_vs_{baseline}"] = {
            metric: target_evaluation["cells"][candidate]["target"][metric]
            - target_evaluation["cells"][baseline]["target"][metric]
            for metric in ("flow_average_precision", "entity_average_precision", "normalized_area_0_8_fpr")
        }
    evaluation_seconds = float(target_evaluation["evaluation_wall_seconds"])
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": config["run_id"],
        "model": {"model_key": config["model_key"], "display_name": config["display_name"], **config["candidate"]},
        "evidence": {
            "target_informed": True,
            "screening_only": True,
            "formal_paper_evidence": False,
            "target_previously_accessed": True,
            "independent_test": False,
            "target_metrics_used_for_selection_or_tuning": False,
        },
        "parent": parent_receipt,
        "source_selection": {"split": split_stats, "cells": selections},
        "source_gate": source_gate,
        "target_evaluation": target_evaluation,
        "target_comparisons_descriptive_only": comparisons,
        "isolation": {
            "all_new_selections_and_parent_receipts_sealed_before_target_load": True,
            "target_disk_loads": 1,
            "target_evaluation_calls": 4,
            "one_call_per_model": True,
            "target_year_arrays_read": 7,
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "new_selected_checkpoints_persisted": 2,
            "parent_checkpoints_copied": False,
            "complete_alert_budget_curve": curve_receipt,
        },
        "resource": {
            "parameter_count": config["candidate"]["parameter_count"],
            "new_training_cells": 2,
            "training_wall_seconds_sum": training_seconds,
            "evaluation_wall_seconds_sum": evaluation_seconds,
            "peak_gpu_allocated_mib": max(
                float(target_evaluation["peak_gpu_allocated_mib"]),
                *[float(selections[cell]["peak_gpu_allocated_mib"]) for cell in CELL_ORDER],
            ),
            "peak_process_rss_mib": parent.process_peak_rss_mib(),
            "gpu_hours": (training_seconds + evaluation_seconds) / 3600.0,
            "launcher_admission_receipt": parent.load_json(Path(args.resource_receipt)) if args.resource_receipt else None,
        },
    }
    parent.atomic_json(output_root / "aggregate-results.json", result)
    parent.write_status(output_root, "computed", "publish-pending", 0, "四模型目标评价完成，等待聚合发布", 7)
    build_manifest(output_root, config["run_id"])
    log(f"严格过去 CPA Q0 完成，总耗时 {(time.time() - T0) / 60:.1f} 分")


def publish_aggregate(config: dict[str, Any], args: argparse.Namespace) -> None:
    destination = config["swanlab"]
    if (
        args.authorized_swanlab_workspace != destination["workspace"]
        or args.authorized_swanlab_project != destination["project"]
    ):
        raise RuntimeError("SwanLab 授权目的地与冻结配置不一致")
    output_root = Path(config["paths"]["output_root"])
    result = parent.load_json(output_root / "aggregate-results.json")
    import swanlab

    swanlab.init(
        workspace=destination["workspace"],
        project=destination["project"],
        name=config["run_id"],
        mode=destination["mode"],
        group=destination["group"],
        tags=destination["tags"],
        log_dir=str(output_root / "swanlog"),
        config={
            "run_id": config["run_id"],
            "model_key": config["model_key"],
            "seed": config["training"]["seed"],
            "protocol": "strict_past_cpa_protocol_a_q0",
            "target_informed": True,
            "independent_test": False,
        },
    )
    metrics: dict[str, float] = {}
    for cell in CELL_ORDER:
        selection = result["source_selection"]["cells"][cell]
        metrics[f"source/{cell}_selected_epoch"] = float(selection["selected_epoch"])
        metrics[f"source/{cell}_validation_flow_ap"] = float(selection["validation_flow_ap"])
    for cell, values in result["source_gate"]["branches"].items():
        metrics[f"source/{cell}_flow_ap"] = values["flow_average_precision"]
        metrics[f"source/{cell}_entity_ap"] = values["entity_average_precision"]
        metrics[f"source/{cell}_curve_area"] = values["normalized_area_0_8_fpr"]
    if "target_evaluation" in result:
        for cell, payload in result["target_evaluation"]["cells"].items():
            values = payload["target"]
            metrics[f"target/{cell}_flow_ap"] = values["flow_average_precision"]
            metrics[f"target/{cell}_entity_ap"] = values["entity_average_precision"]
            metrics[f"target/{cell}_curve_area"] = values["normalized_area_0_8_fpr"]
    metrics["resource/training_wall_seconds"] = result["resource"]["training_wall_seconds_sum"]
    metrics["resource/gpu_hours"] = result["resource"]["gpu_hours"]
    swanlab.log(metrics, step=0)
    swanlab.finish()
    parent.atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-full-mlp-strict-past-cpa-protocol-a-q0-swanlab-receipt-v1",
            "completed": True,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "metric_count": len(metrics),
            "per_sample_values_uploaded": False,
        },
    )
    target_reads = int(result.get("isolation", {}).get("target_year_arrays_read", 0))
    parent.write_status(output_root, "complete", "finished", 0, "严格过去 CPA 协议 A Q0 结果与聚合指标已完成", target_reads)
    build_manifest(output_root, config["run_id"])


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = parent.load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("配置核验通过")
        return 0
    try:
        if args.publish_only:
            publish_aggregate(config, args)
        else:
            run_experiment(config, args, config_path)
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        target_reads = 0
        status_path = output_root / "status.json"
        if status_path.is_file():
            target_reads = int(parent.load_json(status_path).get("target_year_arrays_read", 0))
        parent.write_status(
            output_root,
            "failed",
            "runtime",
            1,
            f"{type(error).__name__}: {error}"[:1000],
            target_reads,
        )
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
