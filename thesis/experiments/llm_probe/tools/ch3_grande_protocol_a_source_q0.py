# -*- coding: utf-8 -*-
"""GRANDE 可微树骨干 LSPR23 协议 A 源年 Q0。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import resource
import sys
import time
import traceback
from pathlib import Path
from typing import Any

try:
    import numpy as np
    from sklearn.metrics import average_precision_score, roc_auc_score
except ModuleNotFoundError:
    np = None
    average_precision_score = None
    roc_auc_score = None

try:
    import torch
    import torch.nn as nn
except ModuleNotFoundError:
    torch = None
    nn = None

VENDOR_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "grande"
if str(VENDOR_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_ROOT))
try:
    from core import GrandeCore
except ModuleNotFoundError:
    GrandeCore = None


SCHEMA_VERSION = "ch3-grande-protocol-a-source-q0-config-v1"
RESULT_SCHEMA_VERSION = "ch3-grande-protocol-a-source-q0-results-v1"
RUN_ID = "ch3-grande-c00-protocolA-source-q0-seed42-v1"
SOURCE_ARRAYS = ("X23", "y23", "I23", "M23", "E23", "T23")
DR_FPR_GRID = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)
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
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def atomic_torch(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    torch.save(value, temporary)
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def process_peak_rss_mib() -> float:
    peak = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak / 1024.0 if sys.platform != "darwin" else peak / (1024.0 * 1024.0)


def write_status(
    output_root: Path,
    state: str,
    stage: str,
    exit_code: int | None,
    detail: str,
) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-grande-protocol-a-source-q0-status-v1",
            "run_id": RUN_ID,
            "state": state,
            "stage": stage,
            "exit_code": exit_code,
            "detail": detail,
            "updated_at_unix": time.time(),
            "source_year_only": True,
            "target_year_arrays_read": 0,
            "target_year_paths_enumerated": 0,
            "downstream_entry_generated": False,
        },
    )


def expected_candidates() -> list[dict[str, Any]]:
    common = {
        "dropout": 0.2,
        "selected_variables": 0.8,
        "data_subset_fraction": 1.0,
        "bootstrap": False,
        "use_category_embeddings": False,
        "use_numeric_embeddings": False,
        "use_freq_enc": False,
        "use_robust_scale_smoothing": False,
        "implementation_role": "official-pytorch-postpaper",
    }
    return [
        {"unit_key": "G-A", "display_name": "GRANDE论文最大数据结构", "depth": 4, "n_estimators": 512, **common},
        {"unit_key": "G-B", "display_name": "GRANDE当前官方默认结构", "depth": 5, "n_estimators": 1024, **common},
    ]


def _legacy_validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("源年数组清单不符")
    if any("24" in name for name in config["source_arrays"]):
        raise ValueError("源年筛选禁止出现名称含 24 的数组")
    if config.get("target_year_arrays_read") != 0 or not config.get("source_year_only"):
        raise ValueError("必须冻结为仅源年且目标年数组读取数为零")
    if config.get("candidates") != expected_candidates():
        raise ValueError("八个候选单元及其顺序不是冻结值")
    expected_training = {
        "seed": 42,
        "feature_count": 83,
        "sequence_length": 128,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "gradient_clip_norm": 1.0,
        "validation_fraction": 0.1,
        "time_tail_fraction": 0.15,
        "activation": "relu",
        "optimizer": "adamw",
        "scheduler": "none",
        "cell": "C00",
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
        "candidate_tie_break": ["higher_validation_flow_ap", "lower_parameter_count", "lower_learning_rate"],
        "deterministic_algorithms": True,
        "cublas_workspace_config": ":4096:8",
    }
    if config.get("training") != expected_training:
        raise ValueError("源年训练与选择合同不符")
    expected_split = {
        "flow_count": 16_353_511,
        "sequence_count": 271_815,
        "entity_count": 150_680,
        "feature_count": 83,
        "sequence_length": 128,
        "train_sequences": 208_598,
        "validation_sequences": 22_444,
    }
    if config.get("input_contract") != expected_split:
        raise ValueError("源年输入与切分统计合同不符")
    if config.get("evaluation") != {
        "selection_metric_only": "validation_flow_average_precision",
        "diagnostic_flow_roc_auc": True,
        "diagnostic_entity_average_precision": True,
        "diagnostic_dr_fpr_grid": list(DR_FPR_GRID),
        "diagnostics_do_not_select_candidate": True,
    }:
        raise ValueError("源年评价合同不符")
    if config.get("artifact_policy") != {
        "epoch_atomic_inflight_checkpoint": True,
        "checkpoint_includes_model_optimizer_best_rng_and_identity": True,
        "completed_unit_is_idempotently_skipped_on_resume": True,
        "persist_selected_checkpoint_per_unit": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "generate_target_entry": False,
    }:
        raise ValueError("检查点与制品合同不符")
    if config.get("stop_gate") != {
        "anchor_architecture_key": "mlp-depth2-width192-anchor",
        "anchor_value": "best_of_two_paper_recipes_in_this_source_screen",
        "pass_rule": "best_non_anchor_validation_flow_ap_strictly_greater_than_anchor",
        "stop_verdict": "reject_full_capacity_mlp_candidate_set_on_lspr23",
        "pass_verdict": "freeze_unique_non_anchor_backbone_and_recipe_on_lspr23",
        "target_entry_on_stop": False,
    }:
        raise ValueError("源年科学停止门不符")
    if config.get("anchor_policy") != {
        "source_screen_anchor_retrained_with_both_paper_recipes": True,
        "historical_protocol_a_target_result_loaded": False,
        "historical_protocol_a_target_result_retrained": False,
        "historical_anchor_role": "identity_and_parameter_reference_only",
    }:
        raise ValueError("90K 锚点复用与重训边界不符")
    resource = config.get("resource_contract")
    if resource != {
        "serial_minimum_free_gpu_memory_gib": 12,
        "serial_minimum_cgroup_available_memory_gib": 40,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_training_units": 1,
        "resource_sample_interval_seconds": 5,
        "candidate_execution_order": "as_listed",
        "first_non_anchor_epoch_calibration": True,
        "reauthorization_if_calibrated_total_exceeds_gpu_hours": 5.0,
    }:
        raise ValueError("资源合同不符")
    paths = config.get("paths", {})
    if Path(paths.get("output_root", "")).name != RUN_ID:
        raise ValueError("输出目录与运行身份不一致")
    swanlab = config.get("swanlab", {})
    if swanlab.get("group") != RUN_ID or swanlab.get("name") != config.get("display_name"):
        raise ValueError("SwanLab 展示身份与运行身份不符")
    if config.get("formal_paper_evidence") or config.get("independent_test"):
        raise ValueError("源年单种子筛选不能宣称正式论文证据或独立测试")
    if config.get("mechanism_policy") != {
        "screening_cell": "C00",
        "cpa_enabled": False,
        "elp_enabled": False,
        "frozen_during_this_screen": True,
        "future_versions_may_revise_with_development_evidence": True,
    }:
        raise ValueError("本轮机制冻结边界不符")


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("源年数组合同不符")
    if any("24" in name for name in config["source_arrays"]):
        raise ValueError("禁止目标年名称")
    for key in (
        "source_year_only",
        "target_label_used_for_selection",
        "target_entry_generated",
    ):
        expected = key == "source_year_only"
        if config.get(key) is not expected:
            raise ValueError(f"证据边界不符：{key}")
    if config.get("target_year_arrays_read") != 0 or config.get("target_year_paths_enumerated") != 0:
        raise ValueError("目标年必须零读取且零枚举")
    if config.get("candidates") != expected_candidates():
        raise ValueError("G-A/G-B 结构不符")
    if config.get("training") != {
        "seed": 42,
        "feature_count": 83,
        "sequence_length": 128,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "gradient_clip_norm": 1.0,
        "validation_fraction": 0.1,
        "time_tail_fraction": 0.15,
        "optimizer": "adam",
        "learning_rate_weights": 0.001,
        "learning_rate_index": 0.01,
        "learning_rate_values": 0.05,
        "learning_rate_leaf": 0.05,
        "scheduler": "none",
        "focal_loss": False,
        "use_class_weights": True,
        "swa": False,
        "cell": "C00",
        "selection_metric": "lspr23_entity_disjoint_validation_flow_ap",
        "selection_rule": "single_epoch_argmax_earliest_tie_no_early_stopping",
        "deterministic_algorithms": True,
        "cublas_workspace_config": ":4096:8",
    }:
        raise ValueError("训练合同不符")
    if config.get("input_contract") != {
        "flow_count": 16_353_511,
        "sequence_count": 271_815,
        "entity_count": 150_680,
        "feature_count": 83,
        "sequence_length": 128,
        "train_sequences": 208_598,
        "validation_sequences": 22_444,
    }:
        raise ValueError("协议 A 输入统计不符")
    evaluation = config.get("evaluation", {})
    if evaluation.get("dr_fpr_grid") != list(DR_FPR_GRID) or not evaluation.get("complete_reachable_alert_budget_curve"):
        raise ValueError("完整指标合同不符")
    if config.get("resource_contract") != {
        "total_gpu_hour_cap": 4.5,
        "maximum_parallel_training_units": 1,
        "minimum_free_gpu_memory_gib": 12,
        "minimum_cgroup_available_memory_gib": 30,
        "minimum_free_disk_gib": 10,
        "r0_real_batch_sequences": 64,
        "r1_steps": 1000,
        "g_b_requires_projected_budget": True,
    }:
        raise ValueError("资源合同不符")
    upstream = config.get("upstream", {})
    if upstream != {
        "repository": "https://github.com/s-marton/GRANDE",
        "commit": "07f7278b30ab9ebbbdc544e5f9a91f1b5df7fecb",
        "license": "MIT",
        "package_version": "0.2.0",
        "role": "official-pytorch-postpaper",
        "supported_torch": ">=2.6,<2.10",
        "runtime_torch_gate": "2.13-compatible-only-if-r0-passes",
    }:
        raise ValueError("上游身份不符")
    if Path(config.get("paths", {}).get("output_root", "")).name != RUN_ID:
        raise ValueError("输出根与运行身份不符")
    if config.get("swanlab", {}).get("group") != RUN_ID:
        raise ValueError("SwanLab 分组不符")
    if config.get("formal_paper_evidence") or config.get("independent_test"):
        raise ValueError("不得声称正式证据或独立测试")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GRANDE 可微树骨干 LSPR23 协议 A 源年 Q0")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--validate-config", action="store_true", help="只核验冻结配置")
    parser.add_argument(
        "--phase",
        choices=("prepare", "resource-calibrate", "train-unit", "aggregate", "publish-aggregate"),
        default="prepare",
    )
    parser.add_argument("--structure", choices=("G-A", "G-B"))
    parser.add_argument("--resume", action="store_true", help="恢复同一运行身份")
    parser.add_argument("--resource-receipt", help="启动器资源收据")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser.parse_args()


if nn is not None and np is not None:
    class FullCapacityMLP(nn.Module):
        """保持 C00/C01/C10/C11 同形参数外壳的普通多层感知机。"""

        def __init__(self, feature_count: int, hidden_depth: int, hidden_size: int, dropout: float):
            super().__init__()
            encoder_depth = hidden_depth - 1
            layers: list[nn.Module] = []
            input_size = feature_count
            for _ in range(encoder_depth):
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
            context = torch.zeros_like(hidden)
            fused = self.fusion(torch.cat((hidden, context), dim=-1)) * mask.unsqueeze(-1)
            return self.output(fused).squeeze(-1)
else:
    class FullCapacityMLP:
        pass


def build_model(candidate: dict[str, Any], feature_count: int) -> Any:
    if torch is None or nn is None or GrandeCore is None:
        raise RuntimeError("正式计算缺少 PyTorch 或固定 GRANDE 核心")
    model = GrandeCore(
        number_of_variables=feature_count,
        depth=candidate["depth"],
        n_estimators=candidate["n_estimators"],
        dropout=candidate["dropout"],
        selected_variables=candidate["selected_variables"],
        random_seed=42,
    )
    if sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad) <= 0:
        raise RuntimeError("GRANDE 可训练参数量无效")
    return model


def move_optimizer_state(optimizer: Any, device: Any) -> None:
    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                state[key] = value.to(device)


def source_inventory(cache_root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for name in SOURCE_ARRAYS:
        if "24" in name:
            raise RuntimeError("禁止读取名称含 24 的数组")
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结源年缓存：{path}")
        stat = path.stat()
        log(f"计算源年输入摘要：{path.name}")
        files.append(
            {
                "name": path.name,
                "bytes": stat.st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "schema_version": "ch3-full-capacity-mlp-source-inventory-v1",
        "cache_root": str(cache_root),
        "files": files,
        "sha256": canonical_sha256(files),
        "source_year_arrays_read": len(files),
        "target_year_arrays_read": 0,
    }


def load_source_arrays(cache_root: Path) -> dict[str, Any]:
    arrays: dict[str, Any] = {}
    for name in SOURCE_ARRAYS:
        if "24" in name:
            raise RuntimeError("禁止读取名称含 24 的数组")
        arrays[name] = np.load(cache_root / f"{name}.npy", allow_pickle=False)
    return arrays


def source_split(source: dict[str, Any], config: dict[str, Any]) -> tuple[Any, Any, dict[str, int]]:
    training = config["training"]
    unique_entity = np.unique(source["E23"])
    permutation = np.random.RandomState(training["seed"]).permutation(len(unique_entity))
    count = max(1, int(len(unique_entity) * training["validation_fraction"]))
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    entity_mask = np.fromiter((value in validation_entities for value in source["E23"]), bool, len(source["E23"]))
    time_cut = np.quantile(source["T23"], 1.0 - training["time_tail_fraction"])
    time_mask = source["T23"] >= time_cut
    train_rows = np.flatnonzero(~(entity_mask | time_mask))
    validation_rows = np.flatnonzero(entity_mask & ~time_mask)
    stats = {
        "entity_count": int(len(unique_entity)),
        "train_sequences": int(len(train_rows)),
        "validation_sequences": int(len(validation_rows)),
        "train_validation_row_intersection": int(np.intersect1d(train_rows, validation_rows).size),
    }
    expected = config["input_contract"]
    if stats != {
        "entity_count": expected["entity_count"],
        "train_sequences": expected["train_sequences"],
        "validation_sequences": expected["validation_sequences"],
        "train_validation_row_intersection": 0,
    }:
        raise RuntimeError(f"协议 A 源年切分统计不符：{stats}")
    return train_rows, validation_rows, stats


def validate_source_shapes(source: dict[str, Any], config: dict[str, Any]) -> None:
    contract = config["input_contract"]
    if source["X23"].shape != (contract["flow_count"], contract["feature_count"]):
        raise RuntimeError(f"X23 形状不符：{source['X23'].shape}")
    expected_sequence_shape = (contract["sequence_count"], contract["sequence_length"])
    if source["I23"].shape != expected_sequence_shape or source["M23"].shape != expected_sequence_shape:
        raise RuntimeError("I23/M23 冻结序列形状不符")
    if len(source["y23"]) != contract["flow_count"]:
        raise RuntimeError("y23 流数不符")
    if len(source["E23"]) != contract["sequence_count"] or len(source["T23"]) != contract["sequence_count"]:
        raise RuntimeError("E23/T23 序列数不符")
    for start in range(0, len(source["X23"]), 1_000_000):
        if not np.isfinite(source["X23"][start : start + 1_000_000]).all():
            raise RuntimeError("源年特征含非有限值")
    if not np.isfinite(source["y23"]).all():
        raise RuntimeError("源年特征或标签含非有限值")


@torch.no_grad() if torch is not None else (lambda function: function)
def predict_validation(
    model: Any,
    validation_rows: Any,
    source: dict[str, Any],
    gpu: dict[str, Any],
    sequence_length: int,
) -> tuple[Any, Any, Any]:
    model.eval()
    predictions: list[Any] = []
    labels: list[Any] = []
    entities: list[Any] = []
    for start in range(0, len(validation_rows), 64):
        rows = validation_rows[start : start + 64]
        selected = torch.from_numpy(rows).to(gpu["X"].device)
        indices = gpu["I"][selected][:, :sequence_length]
        valid = gpu["M"][selected][:, :sequence_length] > 0.5
        batch = indices.shape[0]
        values = gpu["X"][indices.reshape(-1)].reshape(batch, sequence_length, gpu["X"].shape[1])
        flat_values = values[valid]
        probabilities = [
            torch.sigmoid(model(flat_values[flow_start : flow_start + 512]))
            for flow_start in range(0, len(flat_values), 512)
        ]
        predictions.append(torch.cat(probabilities).float().cpu().numpy())
        labels.append(gpu["y"][indices.reshape(-1)].reshape(indices.shape)[valid].float().cpu().numpy())
        valid_count = valid.sum(1).cpu().numpy().astype(np.int64)
        entities.append(np.repeat(source["E23"][rows], valid_count))
    model.train()
    return np.concatenate(predictions), np.concatenate(labels), np.concatenate(entities)


def entity_diagnostics(predictions: Any, labels: Any, entities: Any) -> dict[str, Any]:
    unique_entities, inverse = np.unique(entities, return_inverse=True)
    entity_scores = np.full(len(unique_entities), -np.inf, np.float32)
    entity_labels = np.zeros(len(unique_entities), np.float32)
    np.maximum.at(entity_scores, inverse, predictions.astype(np.float32))
    np.maximum.at(entity_labels, inverse, labels.astype(np.float32))
    if not np.isfinite(entity_scores).all() or entity_labels.min() < 0 or entity_labels.max() > 1:
        raise RuntimeError("源年实体诊断输入无效")
    positives = int(entity_labels.sum())
    negatives = int(len(entity_labels) - positives)
    if positives == 0 or negatives == 0:
        raise RuntimeError("源年实体验证缺少正类或负类")
    order = np.argsort(-entity_scores, kind="mergesort")
    sorted_scores = entity_scores[order]
    sorted_labels = entity_labels[order].astype(np.int64)
    group_end = np.r_[sorted_scores[1:] != sorted_scores[:-1], True]
    cumulative_true = np.cumsum(sorted_labels)[group_end]
    cumulative_false = (np.arange(1, len(sorted_labels) + 1) - np.cumsum(sorted_labels))[group_end]
    true_rate = cumulative_true / positives
    false_rate = cumulative_false / negatives
    dr: dict[str, float] = {}
    for target in DR_FPR_GRID:
        reachable = true_rate[false_rate <= target]
        dr[f"{target:.3f}"] = float(reachable[-1]) if len(reachable) else 0.0
    curve_digest = canonical_sha256(
        {
            "false_positive_rate": false_rate.tolist(),
            "detection_rate": true_rate.tolist(),
        }
    )
    return {
        "entity_average_precision": float(average_precision_score(entity_labels, entity_scores)),
        "entity_count": int(len(unique_entities)),
        "positive_entity_count": positives,
        "dr_at_fpr": dr,
        "complete_reachable_curve_points": int(len(true_rate)),
        "complete_reachable_curve_sha256": curve_digest,
        "curve_complexity": "stable_sort_and_tie_group_scan_O_n_log_n",
    }


def complete_entity_curve(predictions: Any, labels: Any, entities: Any) -> dict[str, Any]:
    unique_entities, inverse = np.unique(entities, return_inverse=True)
    scores = np.full(len(unique_entities), -np.inf, np.float32)
    targets = np.zeros(len(unique_entities), np.float32)
    np.maximum.at(scores, inverse, predictions.astype(np.float32))
    np.maximum.at(targets, inverse, labels.astype(np.float32))
    order = np.argsort(-scores, kind="mergesort")
    sorted_scores = scores[order]
    sorted_targets = targets[order].astype(np.int64)
    group_end = np.r_[sorted_scores[1:] != sorted_scores[:-1], True]
    true_positive = np.cumsum(sorted_targets)[group_end]
    false_positive = (np.arange(1, len(sorted_targets) + 1) - np.cumsum(sorted_targets))[group_end]
    positive_count = int(targets.sum())
    negative_count = int(len(targets) - positive_count)
    return {
        "n_false_positive_entity": false_positive.astype(np.int64),
        "nominal_fpr": np.arange(len(false_positive), dtype=np.float64) / max(len(false_positive), 1),
        "realized_fpr": false_positive.astype(np.float64) / negative_count,
        "detection_rate": true_positive.astype(np.float64) / positive_count,
    }


def unit_identity(run_identity: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "ch3-full-capacity-mlp-source-unit-identity-v1",
        **run_identity,
        "unit_key": candidate["unit_key"],
        "candidate_sha256": canonical_sha256(candidate),
        "cell": "C00",
    }


def append_progress(output_root: Path, candidate: dict[str, Any], selection: dict[str, Any]) -> None:
    path = output_root / "progress.jsonl"
    existing: list[dict[str, Any]] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing.append(json.loads(line))
    if any(item.get("unit_key") == candidate["unit_key"] for item in existing):
        return
    existing.append(
        {
            "unit_key": candidate["unit_key"],
            "display_name": candidate["display_name"],
            "completed_at_unix": time.time(),
            "selected_epoch": selection["selected_epoch"],
            "validation_flow_ap": selection["validation_flow_ap"],
            "checkpoint_sha256": selection["checkpoint"]["sha256"],
            "target_year_arrays_read": 0,
        }
    )
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(
        "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in existing),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def gradient_group_stats(
    groups: dict[str, list[Any]],
    override: dict[int, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, parameters in groups.items():
        gradients = [override.get(id(parameter)) if override is not None else parameter.grad for parameter in parameters]
        present = [gradient for gradient in gradients if gradient is not None]
        norms = [float(gradient.detach().float().norm()) for gradient in present]
        result[name] = {
            "parameter_count": int(sum(parameter.numel() for parameter in parameters)),
            "parameters_with_gradient": len(present),
            "parameters_with_nonzero_gradient": int(sum(value > 0 for value in norms)),
            "parameters_with_finite_gradient": int(
                sum(bool(torch.isfinite(gradient).all()) for gradient in present)
            ),
            "gradient_norm_minimum": min(norms) if norms else None,
            "gradient_norm_median": float(np.median(norms)) if norms else None,
            "gradient_norm_maximum": max(norms) if norms else None,
        }
    return result


def gradient_groups_pass(stats: dict[str, Any]) -> bool:
    return all(
        item["parameters_with_gradient"] > 0
        and item["parameters_with_nonzero_gradient"] == item["parameters_with_gradient"]
        and item["parameters_with_finite_gradient"] == item["parameters_with_gradient"]
        for item in stats.values()
    )


def write_first_non_anchor_calibration(
    output_root: Path,
    config: dict[str, Any],
    candidate: dict[str, Any],
    epoch_seconds: float,
    peak_gpu_mib: float,
) -> None:
    path = output_root / "first-non-anchor-calibration.json"
    if path.is_file():
        if load_json(path).get("requires_resource_reauthorization"):
            raise RuntimeError("首个非锚点实测外推超过冻结 GPU 小时上限，须新建授权版本")
        return
    candidates = config["candidates"]
    index = next(index for index, item in enumerate(candidates) if item["unit_key"] == candidate["unit_key"])
    current_steps = (config["training"]["epochs"] - 1) * config["training"]["steps_per_epoch"]
    scaled_steps = float(current_steps)
    for later in candidates[index + 1 :]:
        scaled_steps += (
            config["training"]["epochs"]
            * config["training"]["steps_per_epoch"]
            * later["parameter_count"]
            / candidate["parameter_count"]
        )
    seconds_per_step = epoch_seconds / config["training"]["steps_per_epoch"]
    estimated_remaining_seconds = seconds_per_step * scaled_steps
    limit_hours = config["resource_contract"]["reauthorization_if_calibrated_total_exceeds_gpu_hours"]
    receipt = {
        "schema_version": "ch3-full-capacity-mlp-first-non-anchor-calibration-v1",
        "unit_key": candidate["unit_key"],
        "epoch": 1,
        "epoch_seconds": epoch_seconds,
        "seconds_per_optimizer_step": seconds_per_step,
        "peak_gpu_allocated_mib": peak_gpu_mib,
        "estimated_remaining_gpu_seconds_by_parameter_ratio": estimated_remaining_seconds,
        "estimated_remaining_gpu_hours_by_parameter_ratio": estimated_remaining_seconds / 3600.0,
        "reauthorization_limit_gpu_hours": limit_hours,
        "requires_resource_reauthorization": estimated_remaining_seconds / 3600.0 > limit_hours,
        "estimate_is_engineering_only": True,
        "target_year_arrays_read": 0,
    }
    atomic_json(path, receipt)
    if receipt["requires_resource_reauthorization"]:
        raise RuntimeError("首个非锚点实测外推超过冻结 GPU 小时上限，须重新取得资源授权")


def train_candidate(
    config: dict[str, Any],
    candidate: dict[str, Any],
    output_root: Path,
    run_identity: dict[str, Any],
    source: dict[str, Any],
    gpu: dict[str, Any],
    train_rows: Any,
    validation_rows: Any,
    device: Any,
    resume: bool,
    calibration_only: bool = False,
) -> dict[str, Any]:
    key = candidate["unit_key"]
    checkpoint_path = output_root / "checkpoints" / f"selected-{key}.pt"
    receipt_path = output_root / "receipts" / f"selection-{key}.json"
    inflight_path = output_root / "inflight" / f"{key}.pt"
    identity = unit_identity(run_identity, candidate)
    completed_paths = (checkpoint_path.is_file(), receipt_path.is_file())
    if any(completed_paths) and not all(completed_paths):
        if not resume or not inflight_path.is_file():
            raise RuntimeError(f"{key} 完成制品不完整且无合法在途检查点")
        log(f"{candidate['display_name']} 检测到完成发布中断，将从在途 epoch 检查点重新发布")
    if all(completed_paths):
        receipt = load_json(receipt_path)
        if not resume:
            raise RuntimeError(f"{key} 已有完成制品但未显式恢复")
        selection = receipt.get("selection", {})
        if receipt.get("identity") != identity or selection.get("checkpoint", {}).get("sha256") != sha256_file(checkpoint_path):
            raise RuntimeError(f"{key} 完成制品身份或摘要不符")
        log(f"{candidate['display_name']} 已完成，恢复时幂等跳过")
        inflight_path.unlink(missing_ok=True)
        append_progress(output_root, candidate, selection)
        return selection
    if not resume and inflight_path.exists():
        raise RuntimeError(f"{key} 存在在途检查点但未显式恢复")

    training = config["training"]
    random.seed(training["seed"])
    np.random.seed(training["seed"])
    torch.manual_seed(training["seed"])
    torch.cuda.manual_seed_all(training["seed"])
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != training["cublas_workspace_config"]:
        raise RuntimeError("CUBLAS 确定性工作区配置不符")
    torch.use_deterministic_algorithms(training["deterministic_algorithms"])
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    model = build_model(candidate, training["feature_count"]).to(device)
    groups = model.parameter_groups()
    optimizer = torch.optim.Adam(
        [
            {"params": groups["instance_leaf_weights"], "lr": training["learning_rate_weights"]},
            {"params": groups["split_index"], "lr": training["learning_rate_index"]},
            {"params": groups["split_values"], "lr": training["learning_rate_values"]},
            {"params": groups["leaf_values"], "lr": training["learning_rate_leaf"]},
        ]
    )
    generator = torch.Generator().manual_seed(training["seed"])
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_state: dict[str, Any] | None = None
    elapsed_before = 0.0
    optimizer_steps = 0
    valid_training_flows = 0
    resume_count = 0
    start_epoch = 1
    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("identity") != identity:
            raise RuntimeError(f"{key} 在途检查点身份不符")
        model.load_state_dict(inflight["model"])
        optimizer.load_state_dict(inflight["optimizer"])
        move_optimizer_state(optimizer, device)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_state = inflight["best_state"]
        elapsed_before = float(inflight["elapsed_seconds"])
        optimizer_steps = int(inflight["optimizer_steps"])
        valid_training_flows = int(inflight["valid_training_flows"])
        resume_count = int(inflight["resume_count"]) + 1
        random.setstate(inflight["python_rng_state"])
        np.random.set_state(inflight["numpy_rng_state"])
        torch.set_rng_state(inflight["torch_cpu_rng_state"])
        torch.cuda.set_rng_state_all(inflight["torch_cuda_rng_state_all"])
        generator.set_state(inflight["batch_generator_state"])
        start_epoch = int(inflight["epoch"]) + 1
        log(f"{candidate['display_name']} 从 epoch {start_epoch} 恢复")

    train_indices = source["I23"][train_rows]
    train_mask = source["M23"][train_rows] > 0
    positive_rate = float(source["y23"][train_indices][train_mask].mean())
    if not 0.0 < positive_rate < 1.0:
        raise RuntimeError("源年逐流标签先验无效")
    positive_weight = torch.tensor([(1.0 - positive_rate) / positive_rate], device=device)
    loss_function = nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    model.train()
    for epoch in range(start_epoch, training["epochs"] + 1):
        epoch_started = time.time()
        running_loss = 0.0
        for step in range(1, training["steps_per_epoch"] + 1):
            positions = torch.randint(0, len(train_rows), (training["batch_size"],), generator=generator)
            selected_rows = torch.from_numpy(train_rows[positions.numpy()]).to(device)
            indices = gpu["I"][selected_rows][:, : training["sequence_length"]]
            valid = gpu["M"][selected_rows][:, : training["sequence_length"]] > 0.5
            values = gpu["X"][indices.reshape(-1)].reshape(
                training["batch_size"], training["sequence_length"], training["feature_count"]
            )
            labels = gpu["y"][indices.reshape(-1)].reshape(indices.shape)
            flat_values = values[valid]
            flat_labels = labels[valid]
            first_batch = key == "G-A" and epoch == 1 and step == 1 and start_epoch == 1
            if first_batch:
                forward_started = time.time()
                logits, tree_outputs, tree_weights, route_diagnostics = model(
                    flat_values,
                    return_per_estimator_logits=True,
                    return_diagnostics=True,
                )
                forward_seconds = time.time() - forward_started
            else:
                logits = model(flat_values)
            loss = loss_function(logits, flat_labels).mean()
            if not torch.isfinite(loss):
                raise RuntimeError(f"{key} epoch={epoch} step={step} 训练损失非有限")
            optimizer.zero_grad(set_to_none=True)
            backward_started = time.time()
            loss.backward()
            backward_seconds = time.time() - backward_started
            if first_batch:
                core_gradient_stats = gradient_group_stats(groups)
                parameters_before = {
                    name: [parameter.detach().clone() for parameter in parameters]
                    for name, parameters in groups.items()
                }
            torch.nn.utils.clip_grad_norm_(model.parameters(), training["gradient_clip_norm"])
            optimizer_started = time.time()
            optimizer.step()
            optimizer_seconds = time.time() - optimizer_started
            if first_batch:
                changed = {
                    name: any(
                        not torch.equal(before, after.detach())
                        for before, after in zip(parameters_before[name], groups[name])
                    )
                    for name in groups
                }
                mechanism_head = nn.Linear(2, 1, bias=True, device=device)
                p_log = nn.Parameter(torch.tensor(float(np.log(2.0)), device=device))
                diagnostic_logits = model(flat_values)
                logit_matrix = torch.zeros_like(labels)
                logit_matrix[valid] = diagnostic_logits
                mask = valid.to(logit_matrix.dtype)
                context = torch.cumsum(logit_matrix * mask, dim=1) / torch.cumsum(mask, dim=1).clamp(min=1.0)
                fused_logits = mechanism_head(torch.stack((logit_matrix, context), dim=-1)).squeeze(-1)
                probabilities = torch.sigmoid(fused_logits).clamp(1e-7, 1.0)
                p_value = torch.exp(p_log)
                pooled = (
                    ((probabilities**p_value) * mask).sum(1) / mask.sum(1).clamp(min=1.0)
                ) ** (1.0 / p_value)
                entity_labels = (labels * mask).amax(1)
                entity_loss = nn.functional.binary_cross_entropy(pooled, entity_labels)
                core_parameters = [parameter for parameters in groups.values() for parameter in parameters]
                mechanism_gradients = torch.autograd.grad(
                    entity_loss,
                    core_parameters,
                    allow_unused=True,
                )
                override = {id(parameter): gradient for parameter, gradient in zip(core_parameters, mechanism_gradients)}
                mechanism_gradient_stats = gradient_group_stats(groups, override)
                receipt = {
                    "schema_version": "ch3-grande-gradient-gate-v1",
                    "structure": key,
                    "real_batch_sequences": int(len(selected_rows)),
                    "real_batch_effective_flows": int(valid.sum()),
                    "loss": float(loss.detach()),
                    "entity_diagnostic_loss": float(entity_loss.detach()),
                    "forward_seconds": forward_seconds,
                    "backward_seconds": backward_seconds,
                    "optimizer_seconds": optimizer_seconds,
                    "core_gradients": core_gradient_stats,
                    "mechanism_path_gradients": mechanism_gradient_stats,
                    "core_parameter_changed": changed,
                    "route_diagnostics": {
                        name: float(value.detach()) for name, value in route_diagnostics.items()
                    },
                    "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
                    "peak_process_rss_mib": process_peak_rss_mib(),
                    "passed": gradient_groups_pass(core_gradient_stats)
                    and gradient_groups_pass(mechanism_gradient_stats)
                    and all(changed.values())
                    and all(bool(torch.isfinite(value)) for value in route_diagnostics.values()),
                    "target_year_arrays_read": 0,
                }
                atomic_json(output_root / "gradient-gate-receipt.json", receipt)
                if not receipt["passed"]:
                    raise RuntimeError("gradient_gate_failed")
                dependency_path = output_root / "dependency-receipt.json"
                dependency = load_json(dependency_path)
                dependency["runtime_torch_compatibility_passed"] = True
                dependency["torch_2_13_compatibility_claimed"] = str(torch.__version__).startswith("2.13")
                dependency["compatibility_scope"] = "fixed_grande_core_G-A_R0_real_forward_backward_only"
                dependency["gradient_gate_receipt_sha256"] = sha256_file(output_root / "gradient-gate-receipt.json")
                atomic_json(dependency_path, dependency)
            running_loss += float(loss.detach())
            optimizer_steps += 1
            valid_training_flows += int(valid.sum())
            if step % 250 == 0:
                elapsed = elapsed_before + time.time() - started
                total_steps = training["epochs"] * training["steps_per_epoch"]
                eta = elapsed * max(total_steps - optimizer_steps, 0) / max(optimizer_steps, 1)
                log(
                    f"{candidate['display_name']} 心跳 epoch={epoch}/{training['epochs']} "
                    f"step={step}/{training['steps_per_epoch']} 累计={elapsed/60:.1f}分 "
                    f"预计剩余={eta/60:.1f}分"
                )
        predictions, labels_np, _ = predict_validation(
            model,
            validation_rows,
            source,
            gpu,
            training["sequence_length"],
        )
        validation_ap = float(average_precision_score(labels_np, predictions))
        if not math.isfinite(validation_ap):
            raise RuntimeError(f"{key} epoch={epoch} 验证逐流 AP 非有限")
        epoch_seconds = time.time() - epoch_started
        history.append(
            {
                "epoch": epoch,
                "validation_flow_ap": validation_ap,
                "mean_training_loss": running_loss / training["steps_per_epoch"],
                "epoch_seconds": epoch_seconds,
                "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
            }
        )
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
        elapsed = elapsed_before + time.time() - started
        atomic_torch(
            inflight_path,
            {
                "schema_version": "ch3-full-capacity-mlp-source-inflight-v1",
                "identity": identity,
                "epoch": epoch,
                "model": {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()},
                "optimizer": optimizer.state_dict(),
                "history": history,
                "best_ap": best_ap,
                "best_epoch": best_epoch,
                "best_state": best_state,
                "elapsed_seconds": elapsed,
                "optimizer_steps": optimizer_steps,
                "valid_training_flows": valid_training_flows,
                "resume_count": resume_count,
                "python_rng_state": random.getstate(),
                "numpy_rng_state": np.random.get_state(),
                "torch_cpu_rng_state": torch.get_rng_state(),
                "torch_cuda_rng_state_all": torch.cuda.get_rng_state_all(),
                "batch_generator_state": generator.get_state(),
            },
        )
        completed_prior_seconds = 0.0
        if key == "G-B":
            ga_receipt = output_root / "receipts" / "selection-G-A.json"
            if ga_receipt.is_file():
                completed_prior_seconds = float(load_json(ga_receipt)["selection"]["training_seconds"])
        cumulative_gpu_hours = (completed_prior_seconds + elapsed) / 3600.0
        if cumulative_gpu_hours >= config["resource_contract"]["total_gpu_hour_cap"]:
            atomic_json(
                output_root / "node-fallback-receipt.json",
                {
                    "node_fallback_required": True,
                    "reason": "engineering_rejected_resource_cap",
                    "structure": key,
                    "cumulative_gpu_hours": cumulative_gpu_hours,
                    "node_started": False,
                    "target_year_arrays_read": 0,
                },
            )
            raise RuntimeError("engineering_rejected_resource_cap")
        if epoch == 1:
            prior_seconds = 0.0
            if key == "G-B":
                prior_receipt = output_root / "receipts" / "selection-G-A.json"
                if not prior_receipt.is_file():
                    raise RuntimeError("G-B 资源标定前缺少完整 G-A 收据")
                prior_seconds = float(load_json(prior_receipt)["selection"]["training_seconds"])
            projected_seconds = prior_seconds + epoch_seconds * training["epochs"]
            calibration = {
                "schema_version": "ch3-grande-resource-calibration-v1",
                "structure": key,
                "r1_complete_epoch_steps": training["steps_per_epoch"],
                "epoch_seconds": epoch_seconds,
                "prior_completed_gpu_seconds": prior_seconds,
                "projected_cumulative_gpu_seconds": projected_seconds,
                "projected_cumulative_gpu_hours": projected_seconds / 3600.0,
                "gpu_hour_cap": config["resource_contract"]["total_gpu_hour_cap"],
                "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
                "peak_process_rss_mib": process_peak_rss_mib(),
                "projection_uses_complete_real_epoch": True,
                "paper_runtime_or_parameter_ratio_used": False,
                "target_year_arrays_read": 0,
            }
            calibration["passed"] = (
                calibration["projected_cumulative_gpu_hours"]
                <= config["resource_contract"]["total_gpu_hour_cap"]
            )
            atomic_json(output_root / f"resource-calibration-{key}.json", calibration)
            if not calibration["passed"]:
                if key == "G-B":
                    atomic_json(
                        output_root / "g-b-not-started-receipt.json",
                        {
                            "verdict": "not_started_due_to_preregistered_resource_cap",
                            "calibration_epoch_completed": True,
                            "full_unit_started": False,
                            "node_fallback_required": False,
                            "target_year_arrays_read": 0,
                        },
                    )
                    return {"calibration_only": True, "structure": key, "resource_calibration": calibration}
                atomic_json(
                    output_root / "node-fallback-receipt.json",
                    {
                        "node_fallback_required": True,
                        "reason": "engineering_rejected_resource_cap",
                        "structure": key,
                        "node_started": False,
                        "target_year_arrays_read": 0,
                    },
                )
                raise RuntimeError("engineering_rejected_resource_cap")
            if calibration_only:
                return {"calibration_only": True, "structure": key, "resource_calibration": calibration}
        log(
            f"{candidate['display_name']} epoch={epoch}/{training['epochs']} "
            f"验证逐流AP={validation_ap:.8f}"
        )
    if best_state is None:
        raise RuntimeError(f"{key} 未产生可选检查点")
    training_seconds = elapsed_before + time.time() - started
    model.load_state_dict(best_state)
    diagnostic_started = time.time()
    predictions, labels_np, entities_np = predict_validation(
        model,
        validation_rows,
        source,
        gpu,
        training["sequence_length"],
    )
    flow_ap = float(average_precision_score(labels_np, predictions))
    flow_auc = float(roc_auc_score(labels_np, predictions))
    diagnostics = entity_diagnostics(predictions, labels_np, entities_np)
    curve = complete_entity_curve(predictions, labels_np, entities_np)
    curve_root = output_root / "receipts" / f"validation-{key}"
    curve_root.mkdir(parents=True, exist_ok=True)
    curve_path = curve_root / "complete-alert-budget-curve.npz"
    temporary_curve_path = curve_path.with_name(f"{curve_path.name}.partial.{os.getpid()}")
    with temporary_curve_path.open("wb") as handle:
        np.savez_compressed(handle, **curve)
    os.replace(temporary_curve_path, curve_path)
    diagnostic_seconds = time.time() - diagnostic_started
    if abs(flow_ap - best_ap) > 1e-12:
        raise RuntimeError(f"{key} 最优权重回载后的验证逐流 AP 与选择记录不一致")
    atomic_torch(
        checkpoint_path,
        {
            "schema_version": "ch3-full-capacity-mlp-source-selected-checkpoint-v1",
            "identity": identity,
            "model": best_state,
            "selected_epoch": best_epoch,
        },
    )
    model_weight_bytes = sum(parameter.numel() * parameter.element_size() for parameter in model.parameters())
    selection = {
        "unit_key": key,
        "display_name": candidate["display_name"],
        "depth": candidate["depth"],
        "n_estimators": candidate["n_estimators"],
        "dropout": candidate["dropout"],
        "parameter_count_framework": sum(parameter.numel() for parameter in model.parameters()),
        "parameter_groups": {
            name: {
                "shapes": [list(parameter.shape) for parameter in parameters],
                "requires_grad": [parameter.requires_grad for parameter in parameters],
                "parameter_count": int(sum(parameter.numel() for parameter in parameters)),
            }
            for name, parameters in model.parameter_groups().items()
        },
        "model_weight_bytes": model_weight_bytes,
        "selected_epoch": best_epoch,
        "validation_flow_ap": best_ap,
        "diagnostic_flow_roc_auc": flow_auc,
        "diagnostic_entity": diagnostics,
        "complete_alert_budget_curve": {
            "filename": str(curve_path.relative_to(output_root)),
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
            "crossing_with_baselines": None,
            "crossing_unavailable_reason": "same_split_baseline_complete_curves_not_persisted",
        },
        "history": history,
        "training_seconds": training_seconds,
        "diagnostic_seconds": diagnostic_seconds,
        "optimizer_steps": optimizer_steps,
        "valid_training_flows": valid_training_flows,
        "training_valid_flows_per_second": valid_training_flows / max(training_seconds, 1e-12),
        "diagnostic_flows_per_second": len(predictions) / max(diagnostic_seconds, 1e-12),
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_process_rss_mib": process_peak_rss_mib(),
        "resume_count": resume_count,
        "checkpoint": {
            "filename": str(checkpoint_path.relative_to(output_root)),
            "bytes": checkpoint_path.stat().st_size,
            "sha256": sha256_file(checkpoint_path),
        },
        "selection_signal": "validation_flow_average_precision_only",
        "target_year_arrays_read": 0,
    }
    atomic_json(receipt_path, {"identity": identity, "candidate": candidate, "selection": selection})
    inflight_path.unlink(missing_ok=True)
    append_progress(output_root, candidate, selection)
    del model, optimizer, predictions, labels_np, entities_np
    torch.cuda.empty_cache()
    return selection


def rank_key(selection: dict[str, Any]) -> tuple[float, int, float]:
    return (
        -float(selection["validation_flow_ap"]),
        int(selection["parameter_count_framework"]),
        float(selection["learning_rate"]),
    )


def _legacy_freeze_backbone_selection(
    config: dict[str, Any],
    output_root: Path,
    run_identity: dict[str, Any],
    source_inventory_value: dict[str, Any],
    split_stats: dict[str, int],
    selections: list[dict[str, Any]],
) -> dict[str, Any]:
    anchors = [selection for selection in selections if selection["anchor"]]
    non_anchors = [selection for selection in selections if not selection["anchor"]]
    if len(anchors) != 2 or len(non_anchors) != 6:
        raise RuntimeError("锚点或非锚点完成数不符")
    best_anchor = sorted(anchors, key=rank_key)[0]
    best_non_anchor = sorted(non_anchors, key=rank_key)[0]
    passed = best_non_anchor["validation_flow_ap"] > best_anchor["validation_flow_ap"]
    verdict_code = (
        "freeze_unique_non_anchor_backbone_and_recipe_on_lspr23"
        if passed
        else "reject_full_capacity_mlp_candidate_set_on_lspr23"
    )
    selected_candidate = (
        {
            key: best_non_anchor[key]
            for key in (
                "unit_key",
                "display_name",
                "architecture_key",
                "recipe_key",
                "hidden_depth",
                "hidden_size",
                "learning_rate",
                "weight_decay",
                "dropout",
                "parameter_count_framework",
                "selected_epoch",
                "validation_flow_ap",
                "checkpoint",
            )
        }
        if passed
        else None
    )
    seal = {
        "schema_version": "ch3-full-capacity-mlp-backbone-selection-frozen-v1",
        "run_id": RUN_ID,
        "identity": run_identity,
        "source_data_inventory": source_inventory_value,
        "source_split": split_stats,
        "protocol": "八个C00单元在LSPR23实体不相交验证逐流AP选最早最大轮次，候选按预注册顺序执行",
        "candidate_ranking_rule": [
            "higher_validation_flow_ap",
            "lower_parameter_count_on_exact_tie",
            "lower_learning_rate_on_remaining_exact_tie",
        ],
        "candidate_count": len(selections),
        "all_candidates_completed": len(selections) == 8,
        "candidates": selections,
        "anchor": best_anchor,
        "best_non_anchor": best_non_anchor,
        "source_gate": {
            "passed": passed,
            "verdict_code": verdict_code,
            "strict_ap_delta_over_anchor": (
                float(best_non_anchor["validation_flow_ap"]) - float(best_anchor["validation_flow_ap"])
            ),
        },
        "selected_candidate": selected_candidate,
        "downstream_entry_generated": False,
        "target_year_arrays_read": 0,
        "evidence_scope": "lspr23_single_seed_source_screening_experiment_pending_cross_year_validation",
        "mechanism_freeze_scope": "仅本轮C00筛选期间冻结；后续版本可依据开发证据修订CPA或ELP",
        "sealed_at_unix": time.time(),
    }
    path = output_root / "backbone_selection_frozen.json"
    atomic_json(path, seal)
    if load_json(path).get("identity") != run_identity or sha256_file(path) == "":
        raise RuntimeError("骨干选择封印回读失败")
    return seal


def freeze_backbone_selection(
    config: dict[str, Any],
    output_root: Path,
    run_identity: dict[str, Any],
    source_inventory_value: dict[str, Any],
    split_stats: dict[str, int],
    selections: list[dict[str, Any]],
) -> dict[str, Any]:
    if not selections or len(selections) > 2:
        raise RuntimeError("GRANDE 完成结构数不符")
    ordered = sorted(
        selections,
        key=lambda value: (
            -float(value["validation_flow_ap"]),
            int(value["n_estimators"]),
            0 if value["unit_key"] == "G-A" else 1,
        ),
    )
    winner = ordered[0]
    reference_root = Path(config["paths"]["full_mlp_reference_root"])
    reference_path = reference_root / "backbone_selection_frozen.json"
    if not reference_path.is_file():
        raise RuntimeError("缺少全容量 MLP 源年封印收据")
    reference = load_json(reference_path)
    full_mlp = reference.get("selected_candidate")
    anchor = reference.get("anchor")
    if not full_mlp or not anchor:
        raise RuntimeError("全容量 MLP 或 90K 锚点收据不完整")
    full_mlp_ap = float(full_mlp["validation_flow_ap"])
    anchor_ap = float(anchor["validation_flow_ap"])
    xgb_receipt = None
    xgb_path_value = config["paths"].get("xgb_protocol_a_c00_receipt")
    if xgb_path_value and Path(xgb_path_value).is_file():
        candidate_receipt = load_json(Path(xgb_path_value))
        if candidate_receipt.get("same_protocol_a_split") is True:
            xgb_receipt = candidate_receipt
    criteria = {
        "winner_gt_full_mlp": float(winner["validation_flow_ap"]) > full_mlp_ap,
        "winner_gt_90k_anchor": float(winner["validation_flow_ap"]) > anchor_ap,
        "gradient_gate_valid": (
            (output_root / "gradient-gate-receipt.json").is_file()
            and load_json(output_root / "gradient-gate-receipt.json").get("passed") is True
        ),
        "resource_calibration_valid": all(
            (output_root / f"resource-calibration-{selection['unit_key']}.json").is_file()
            and load_json(output_root / f"resource-calibration-{selection['unit_key']}.json").get("passed") is True
            for selection in selections
        ),
        "target_year_arrays_read_zero": True,
    }
    if xgb_receipt is not None:
        xgb_ap = float(xgb_receipt["validation_flow_ap"])
        criteria["xgb_gap_smaller_than_full_mlp_gap"] = (
            xgb_ap - float(winner["validation_flow_ap"])
            < xgb_ap - full_mlp_ap
        )
    passed = all(criteria.values())
    seal = {
        "schema_version": "ch3-grande-backbone-selection-frozen-v1",
        "run_id": RUN_ID,
        "identity": run_identity,
        "source_data_inventory": source_inventory_value,
        "source_split": split_stats,
        "candidate_ranking_rule": ["higher_validation_flow_ap", "fewer_estimators_on_tie", "G-A_on_remaining_tie"],
        "completed_structures": selections,
        "winner": winner,
        "baselines": {
            "full_mlp_validation_flow_ap": full_mlp_ap,
            "anchor_90k_validation_flow_ap": anchor_ap,
            "xgb_same_split_receipt": xgb_receipt,
            "historical_xgb_per_array_hash_persisted": False,
        },
        "source_gate": {
            "passed": passed,
            "criteria": criteria,
            "verdict": "grande_c00_source_qualified" if passed else "grande_c00_source_rejected",
        },
        "target_year_arrays_read": 0,
        "target_entry_generated": False,
        "sealed_at_unix": time.time(),
    }
    atomic_json(output_root / "backbone_selection_frozen.json", seal)
    atomic_json(output_root / "parent-baseline-receipt.json", seal["baselines"])
    if not passed:
        atomic_json(
            output_root / "node-fallback-receipt.json",
            {
                "node_fallback_required": True,
                "reason": "grande_c00_source_rejected",
                "node_started": False,
                "target_year_arrays_read": 0,
            },
        )
    else:
        atomic_json(
            output_root / "node-fallback-receipt.json",
            {
                "node_fallback_required": False,
                "reason": None,
                "node_started": False,
                "target_year_arrays_read": 0,
            },
        )
    return seal


def build_manifest(output_root: Path) -> None:
    files: dict[str, Any] = {}
    top_level = (
        "config.json",
        "input-identity.json",
        "dependency-receipt.json",
        "structure-candidates-frozen.json",
        "source-input-receipt.json",
        "parent-baseline-receipt.json",
        "gradient-gate-receipt.json",
        "resource-calibration-G-A.json",
        "resource-calibration-G-B.json",
        "g-b-not-started-receipt.json",
        "progress.jsonl",
        "backbone_selection_frozen.json",
        "grande-c00-source-results.json",
        "source-screen-results.json",
        "complete-alert-budget-curves.npz",
        "complete-alert-budget-curves-receipt.json",
        "node-fallback-receipt.json",
        "resource-receipt.json",
        "swanlab-receipt.json",
        "status.json",
    )
    for relative in top_level:
        path = output_root / relative
        if path.is_file():
            files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    for candidate in expected_candidates():
        for relative in (
            f"inflight/{candidate['unit_key']}.pt",
            f"checkpoints/selected-{candidate['unit_key']}.pt",
            f"receipts/selection-{candidate['unit_key']}.json",
        ):
            path = output_root / relative
            if path.is_file():
                files[relative] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-grande-protocol-a-source-q0-manifest-v1",
            "run_id": RUN_ID,
            "files": files,
            "completed_candidate_checkpoints": sum(path.startswith("checkpoints/") for path in files),
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "target_year_arrays_read": 0,
            "target_year_paths_enumerated": 0,
            "downstream_entry_generated": False,
        },
    )


def _legacy_write_source_screen_result(
    config: dict[str, Any],
    output_root: Path,
    seal: dict[str, Any],
    resource_receipt_path: str | None,
) -> None:
    selections = seal["candidates"]
    resource_receipt = load_json(Path(resource_receipt_path)) if resource_receipt_path else None
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": config["display_name"],
        "source_year_only": True,
        "target_year_arrays_read": 0,
        "candidate_count": 8,
        "fits_completed": 8,
        "source_split": seal["source_split"],
        "source_selection": seal,
        "resource": {
            "training_wall_seconds_sum": sum(item["training_seconds"] for item in selections),
            "diagnostic_wall_seconds_sum": sum(item["diagnostic_seconds"] for item in selections),
            "optimizer_steps_sum": sum(item["optimizer_steps"] for item in selections),
            "model_weight_bytes_sum": sum(item["model_weight_bytes"] for item in selections),
            "maximum_parameter_count": max(item["parameter_count_framework"] for item in selections),
            "peak_gpu_allocated_mib": max(item["peak_gpu_allocated_mib"] for item in selections),
            "peak_process_rss_mib": max(item["peak_process_rss_mib"] for item in selections),
            "resume_count_sum": sum(item["resume_count"] for item in selections),
            "launcher_admission_receipt": resource_receipt,
        },
        "verdict": seal["source_gate"],
        "selected_candidate": seal["selected_candidate"],
        "downstream_entry_generated": False,
        "cross_year_effectiveness_claimed": False,
        "formal_paper_evidence": False,
        "independent_test": False,
    }
    atomic_json(output_root / "source-screen-results.json", result)
    write_status(output_root, "computed", "publish-pending", 0, seal["source_gate"]["verdict_code"])
    build_manifest(output_root)


def write_source_screen_result(
    config: dict[str, Any],
    output_root: Path,
    seal: dict[str, Any],
    resource_receipt_path: str | None,
) -> None:
    selections = seal["completed_structures"]
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": config["display_name"],
        "source_year_only": True,
        "target_year_arrays_read": 0,
        "target_year_paths_enumerated": 0,
        "fits_completed": len(selections),
        "source_split": seal["source_split"],
        "source_selection": seal,
        "complete_metrics": {
            selection["unit_key"]: {
                "flow_average_precision": selection["validation_flow_ap"],
                "flow_roc_auc": selection["diagnostic_flow_roc_auc"],
                "entity_average_precision": selection["diagnostic_entity"]["entity_average_precision"],
                "maximum_entity_average_precision": selection["diagnostic_entity"]["entity_average_precision"],
                "dr_at_fpr": selection["diagnostic_entity"]["dr_at_fpr"],
                "complete_alert_budget_curve": selection["complete_alert_budget_curve"],
            }
            for selection in selections
        },
        "gradient_gate": load_json(output_root / "gradient-gate-receipt.json"),
        "resource": {
            "training_wall_seconds_sum": sum(item["training_seconds"] for item in selections),
            "diagnostic_wall_seconds_sum": sum(item["diagnostic_seconds"] for item in selections),
            "optimizer_steps_sum": sum(item["optimizer_steps"] for item in selections),
            "model_weight_bytes_sum": sum(item["model_weight_bytes"] for item in selections),
            "maximum_parameter_count": max(item["parameter_count_framework"] for item in selections),
            "peak_gpu_allocated_mib": max(item["peak_gpu_allocated_mib"] for item in selections),
            "peak_process_rss_mib": max(item["peak_process_rss_mib"] for item in selections),
            "resume_count_sum": sum(item["resume_count"] for item in selections),
            "cumulative_gpu_hours": sum(item["training_seconds"] for item in selections) / 3600.0,
            "gpu_hour_cap": config["resource_contract"]["total_gpu_hour_cap"],
            "launcher_admission_receipt": load_json(Path(resource_receipt_path)) if resource_receipt_path else None,
        },
        "verdict": seal["source_gate"],
        "selected_candidate": seal["winner"] if seal["source_gate"]["passed"] else None,
        "node_fallback_receipt": load_json(output_root / "node-fallback-receipt.json"),
        "downstream_entry_generated": False,
        "formal_paper_evidence": False,
        "independent_test": False,
    }
    atomic_json(output_root / "grande-c00-source-results.json", result)
    atomic_json(output_root / "source-screen-results.json", result)
    write_status(output_root, "computed", "publish-pending", 0, seal["source_gate"]["verdict"])
    build_manifest(output_root)


def prepare_stage(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    snapshot = output_root / "config.json"
    if snapshot.exists():
        if not args.resume or load_json(snapshot) != config:
            raise RuntimeError("输出根已有不匹配配置")
    else:
        atomic_json(snapshot, config)
    vendor_manifest = VENDOR_ROOT / "manifest.json"
    if not vendor_manifest.is_file():
        raise RuntimeError("固定 GRANDE vendor manifest 不存在")
    import pandas
    import sklearn

    def version_pair(value: str) -> tuple[int, int]:
        parts = value.split(".")
        return int(parts[0]), int(parts[1])

    numpy_pair = version_pair(np.__version__)
    pandas_pair = version_pair(pandas.__version__)
    sklearn_pair = version_pair(sklearn.__version__)
    if not ((1, 25) <= numpy_pair < (2, 4)):
        raise RuntimeError("NumPy 实际版本越出上游范围")
    if not ((2, 0) <= pandas_pair < (2, 4)):
        raise RuntimeError("pandas 实际版本越出上游范围")
    if not ((1, 4) <= sklearn_pair < (1, 8)):
        raise RuntimeError("scikit-learn 实际版本越出上游范围")
    dependency = {
        "schema_version": "ch3-grande-dependency-receipt-v1",
        "python": sys.version,
        "numpy": np.__version__ if np is not None else None,
        "torch": torch.__version__ if torch is not None else None,
        "pandas": pandas.__version__,
        "sklearn": sklearn.__version__,
        "upstream_supported_torch": config["upstream"]["supported_torch"],
        "torch_2_13_compatibility_claimed": False,
        "compatibility_requires_r0": True,
        "vendor_manifest_sha256": sha256_file(vendor_manifest),
        "uv_lock_sha256": sha256_file(Path(config["paths"]["uv_lock"])),
        "pyproject_sha256": sha256_file(Path(config["paths"]["pyproject"])),
        "target_year_arrays_read": 0,
        "target_year_paths_enumerated": 0,
    }
    atomic_json(output_root / "dependency-receipt.json", dependency)
    structures = {
        "schema_version": "ch3-grande-structure-candidates-frozen-v1",
        "candidates": config["candidates"],
        "sha256": canonical_sha256(config["candidates"]),
        "frozen_before_data_content_read": True,
        "target_year_arrays_read": 0,
    }
    atomic_json(output_root / "structure-candidates-frozen.json", structures)
    reference_path = Path(config["paths"]["full_mlp_reference_root"]) / "backbone_selection_frozen.json"
    if not reference_path.is_file():
        raise RuntimeError("缺少全容量 MLP 协议 A 源年基线收据")
    reference = load_json(reference_path)
    if not reference.get("selected_candidate") or not reference.get("anchor"):
        raise RuntimeError("全容量 MLP 或 90K 锚点基线不完整")
    atomic_json(
        output_root / "parent-baseline-receipt.json",
        {
            "full_mlp_reference_sha256": sha256_file(reference_path),
            "full_mlp_validation_flow_ap": float(reference["selected_candidate"]["validation_flow_ap"]),
            "anchor_90k_validation_flow_ap": float(reference["anchor"]["validation_flow_ap"]),
            "xgb_same_split_receipt_available": bool(
                config["paths"].get("xgb_protocol_a_c00_receipt")
                and Path(config["paths"]["xgb_protocol_a_c00_receipt"]).is_file()
            ),
            "historical_xgb_per_array_hash_persisted": False,
            "target_year_arrays_read": 0,
        },
    )
    cache_root = Path(config["paths"]["cache_root"])
    files = []
    for name in SOURCE_ARRAYS:
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"源年缓存缺失：{path}")
        files.append({"name": path.name, "bytes": path.stat().st_size})
    atomic_json(
        output_root / "source-input-receipt.json",
        {
            "schema_version": "ch3-grande-source-input-static-receipt-v1",
            "files": files,
            "content_not_read_in_prepare": True,
            "target_year_arrays_read": 0,
            "target_year_paths_enumerated": 0,
        },
    )
    write_status(output_root, "prepared", "static-prepared", 0, "固定源码、依赖、结构与源年静态门已冻结")
    build_manifest(output_root)


def load_training_context(
    config: dict[str, Any],
    config_path: Path,
) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any], Any, Any, dict[str, int], Any]:
    if np is None or torch is None or nn is None or GrandeCore is None or not torch.cuda.is_available():
        raise RuntimeError("GRANDE 正式 Q0 要求完整 GPU 依赖与 CUDA")
    output_root = Path(config["paths"]["output_root"])
    if not (output_root / "structure-candidates-frozen.json").is_file():
        raise RuntimeError("必须先执行 prepare")
    cache_root = Path(config["paths"]["cache_root"])
    inventory = source_inventory(cache_root)
    code_sha = sha256_file(Path(__file__).resolve())
    run_identity = {
        "run_id": RUN_ID,
        "config_sha256": sha256_file(config_path),
        "code_sha256": code_sha,
        "vendor_manifest_sha256": sha256_file(VENDOR_ROOT / "manifest.json"),
        "candidate_table_sha256": canonical_sha256(config["candidates"]),
        "source_data_inventory_sha256": inventory["sha256"],
        "seed": config["training"]["seed"],
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_device_name": torch.cuda.get_device_name(0),
    }
    identity_path = output_root / "input-identity.json"
    value = {"identity": run_identity, "source_data_inventory": inventory}
    if identity_path.is_file():
        if load_json(identity_path) != value:
            raise RuntimeError("输入身份与已冻结值不符")
    else:
        atomic_json(identity_path, value)
    source = load_source_arrays(cache_root)
    validate_source_shapes(source, config)
    train_rows, validation_rows, split_stats = source_split(source, config)
    device = torch.device("cuda")
    gpu = {
        "X": torch.from_numpy(source["X23"]).to(device),
        "y": torch.from_numpy(source["y23"]).to(device),
        "I": torch.from_numpy(source["I23"]).to(device),
        "M": torch.from_numpy(source["M23"]).to(device),
    }
    return output_root, inventory, run_identity, source, train_rows, validation_rows, split_stats, gpu


def train_stage(
    config: dict[str, Any],
    args: argparse.Namespace,
    config_path: Path,
    calibration_only: bool,
) -> None:
    if args.structure is None:
        raise ValueError("资源标定或训练必须指定结构")
    output_root, _, run_identity, source, train_rows, validation_rows, _, gpu = load_training_context(config, config_path)
    candidate = next(item for item in config["candidates"] if item["unit_key"] == args.structure)
    if args.structure == "G-B" and not (output_root / "receipts" / "selection-G-A.json").is_file():
        raise RuntimeError("G-B 前必须完整完成 G-A")
    write_status(output_root, "running", "resource-calibrate" if calibration_only else "train-unit", None, candidate["display_name"])
    selection = train_candidate(
        config,
        candidate,
        output_root,
        run_identity,
        source,
        gpu,
        train_rows,
        validation_rows,
        torch.device("cuda"),
        args.resume,
        calibration_only=calibration_only,
    )
    stage = "resource-calibrated" if selection.get("calibration_only") else "unit-complete"
    write_status(output_root, "prepared" if calibration_only else "running", stage, 0, candidate["display_name"])
    build_manifest(output_root)


def aggregate_stage(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    output_root, inventory, run_identity, source, train_rows, validation_rows, split_stats, gpu = load_training_context(config, config_path)
    selections = []
    curve_arrays: dict[str, Any] = {}
    for candidate in config["candidates"]:
        receipt_path = output_root / "receipts" / f"selection-{candidate['unit_key']}.json"
        if not receipt_path.is_file():
            continue
        selection = load_json(receipt_path)["selection"]
        selections.append(selection)
        curve_path = output_root / selection["complete_alert_budget_curve"]["filename"]
        with np.load(curve_path, allow_pickle=False) as payload:
            for field in payload.files:
                curve_arrays[f"{candidate['unit_key']}__{field}"] = payload[field]
    if not selections or selections[0]["unit_key"] != "G-A":
        raise RuntimeError("聚合前至少必须完整完成 G-A")
    seal = freeze_backbone_selection(config, output_root, run_identity, inventory, split_stats, selections)
    curve_path = output_root / "complete-alert-budget-curves.npz"
    temporary = curve_path.with_name(f"{curve_path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **curve_arrays)
    os.replace(temporary, curve_path)
    atomic_json(
        output_root / "complete-alert-budget-curves-receipt.json",
        {
            "schema_version": "ch3-grande-complete-alert-budget-curves-v1",
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
            "structures": [item["unit_key"] for item in selections],
            "thresholds_persisted": False,
            "per_sample_scores_persisted": False,
        },
    )
    write_source_screen_result(config, output_root, seal, args.resource_receipt)
    del source, train_rows, validation_rows, gpu
    torch.cuda.empty_cache()


def run_screen(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> dict[str, Any]:
    if (
        np is None
        or average_precision_score is None
        or roc_auc_score is None
        or torch is None
        or nn is None
        or not torch.cuda.is_available()
    ):
        raise RuntimeError("全容量多层感知机源年筛选要求完整 GPU 依赖与可用 CUDA")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    config_sha = sha256_file(config_path)
    code_sha = sha256_file(Path(__file__).resolve())
    frozen_config_path = output_root / "config.json"
    if frozen_config_path.is_file():
        if not args.resume or load_json(frozen_config_path) != config:
            raise RuntimeError("输出根已有不兼容冻结配置")
    else:
        atomic_json(frozen_config_path, config)
    cache_root = Path(config["paths"]["cache_root"])
    inventory = source_inventory(cache_root)
    run_identity = {
        "run_id": RUN_ID,
        "config_sha256": config_sha,
        "code_sha256": code_sha,
        "candidate_table_sha256": canonical_sha256(config["candidates"]),
        "source_data_inventory_sha256": inventory["sha256"],
        "seed": config["training"]["seed"],
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_device_name": torch.cuda.get_device_name(0),
    }
    identity_path = output_root / "input-identity.json"
    if identity_path.is_file():
        if not args.resume or load_json(identity_path) != {"identity": run_identity, "source_data_inventory": inventory}:
            raise RuntimeError("恢复时输入身份不一致")
    else:
        atomic_json(identity_path, {"identity": run_identity, "source_data_inventory": inventory})
    seal_path = output_root / "backbone_selection_frozen.json"
    if seal_path.is_file():
        if not args.resume:
            raise RuntimeError("已有骨干选择封印但未显式恢复")
        seal = load_json(seal_path)
        if seal.get("identity") != run_identity or seal.get("candidate_count") != 8:
            raise RuntimeError("骨干选择封印身份或候选数不符")
        log("骨干选择已封印，恢复时跳过全部训练")
        write_source_screen_result(config, output_root, seal, args.resource_receipt)
        return seal

    write_status(output_root, "running", "source-screen", None, "只加载 LSPR23，顺序执行八个 C00 单元")
    source = load_source_arrays(cache_root)
    validate_source_shapes(source, config)
    train_rows, validation_rows, split_stats = source_split(source, config)
    device = torch.device("cuda")
    gpu = {
        "X": torch.from_numpy(source["X23"]).to(device),
        "y": torch.from_numpy(source["y23"]).to(device),
        "I": torch.from_numpy(source["I23"]).to(device),
        "M": torch.from_numpy(source["M23"]).to(device),
    }
    log(f"源年冻结数组已加载，GPU 已分配 {torch.cuda.memory_allocated(device)/2**30:.2f} GiB")
    selections: list[dict[str, Any]] = []
    for index, candidate in enumerate(config["candidates"], start=1):
        write_status(
            output_root,
            "running",
            "source-screen",
            None,
            f"候选 {index}/8：{candidate['display_name']}",
        )
        log(f"开始候选 {index}/8：{candidate['display_name']}")
        selections.append(
            train_candidate(
                config,
                candidate,
                output_root,
                run_identity,
                source,
                gpu,
                train_rows,
                validation_rows,
                device,
                args.resume,
            )
        )
    seal = freeze_backbone_selection(
        config,
        output_root,
        run_identity,
        inventory,
        split_stats,
        selections,
    )
    write_source_screen_result(config, output_root, seal, args.resource_receipt)
    del gpu, source, train_rows, validation_rows
    torch.cuda.empty_cache()
    return seal


def publish_aggregate(config: dict[str, Any], args: argparse.Namespace) -> None:
    destination = config["swanlab"]
    if (
        args.authorized_swanlab_workspace != destination["workspace"]
        or args.authorized_swanlab_project != destination["project"]
    ):
        raise RuntimeError("SwanLab 授权目的地与冻结配置不一致")
    output_root = Path(config["paths"]["output_root"])
    result = load_json(output_root / "source-screen-results.json")
    resource_path = Path(args.resource_receipt) if args.resource_receipt else None
    if resource_path is None or not resource_path.is_file():
        raise RuntimeError("发布前缺少已完成的启动器资源收据")
    result["resource"]["launcher_admission_receipt"] = load_json(resource_path)
    atomic_json(output_root / "source-screen-results.json", result)
    import swanlab

    swanlab.init(
        workspace=destination["workspace"],
        project=destination["project"],
        name=destination["name"],
        mode=destination["mode"],
        group=destination["group"],
        tags=destination["tags"],
        log_dir=str(output_root / "swanlog"),
        config={
            "run_id": RUN_ID,
            "protocol": "lspr23_grande_protocol_a_source_q0",
            "candidate_count": len(result["source_selection"]["completed_structures"]),
            "seed": config["training"]["seed"],
            "source_year_only": True,
            "target_year_arrays_read": 0,
        },
    )
    metrics: dict[str, float] = {}
    for selection in result["source_selection"]["completed_structures"]:
        prefix = f"source/{selection['unit_key']}"
        metrics[f"{prefix}/selected_epoch"] = float(selection["selected_epoch"])
        metrics[f"{prefix}/validation_flow_ap"] = float(selection["validation_flow_ap"])
        metrics[f"{prefix}/diagnostic_entity_ap"] = float(
            selection["diagnostic_entity"]["entity_average_precision"]
        )
        metrics[f"{prefix}/parameter_count"] = float(selection["parameter_count_framework"])
        metrics[f"{prefix}/training_seconds"] = float(selection["training_seconds"])
        metrics[f"{prefix}/peak_gpu_allocated_mib"] = float(selection["peak_gpu_allocated_mib"])
        for key, value in selection["diagnostic_entity"]["dr_at_fpr"].items():
            metrics[f"{prefix}/diagnostic_dr_fpr_{key}"] = float(value)
    metrics["source/gate_passed"] = float(result["verdict"]["passed"])
    metrics["resource/training_wall_seconds_sum"] = float(result["resource"]["training_wall_seconds_sum"])
    metrics["resource/peak_gpu_allocated_mib"] = float(result["resource"]["peak_gpu_allocated_mib"])
    swanlab.log(metrics, step=0)
    swanlab.finish()
    atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-grande-protocol-a-source-q0-swanlab-receipt-v1",
            "completed": True,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "metric_count": len(metrics),
            "aggregate_only": True,
            "per_sample_values_uploaded": False,
            "target_year_arrays_read": 0,
        },
    )
    verdict = result["verdict"]["verdict"]
    write_status(output_root, "complete", "finished", 0, verdict)
    build_manifest(output_root)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("配置核验通过：G-A/G-B 协议 A C00，目标年读取与枚举均为 0")
        return 0
    output_root = Path(config["paths"]["output_root"])
    try:
        if args.phase == "prepare":
            prepare_stage(config, args, config_path)
        else:
            destination = config["swanlab"]
            if (
                args.authorized_swanlab_workspace != destination["workspace"]
                or args.authorized_swanlab_project != destination["project"]
            ):
                raise RuntimeError("正式数据或发布前必须确认 SwanLab 目的地")
        if args.phase == "resource-calibrate":
            train_stage(config, args, config_path, calibration_only=True)
        elif args.phase == "train-unit":
            train_stage(config, args, config_path, calibration_only=False)
        elif args.phase == "aggregate":
            aggregate_stage(config, args, config_path)
        elif args.phase == "publish-aggregate":
            publish_aggregate(config, args)
    except Exception as error:
        output_root.mkdir(parents=True, exist_ok=True)
        detail = f"{type(error).__name__}: {error}"[:1000]
        if any(
            reason in detail
            for reason in (
                "gradient_gate_failed",
                "engineering_rejected_resource_cap",
                "PyTorch",
                "GRANDE",
                "CUDA",
                "NumPy",
                "pandas",
                "scikit-learn",
            )
        ):
            atomic_json(
                output_root / "node-fallback-receipt.json",
                {
                    "node_fallback_required": True,
                    "reason": detail,
                    "node_started": False,
                    "target_year_arrays_read": 0,
                    "target_year_paths_enumerated": 0,
                },
            )
        write_status(output_root, "failed", "runtime", 1, detail)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
