# -*- coding: utf-8 -*-
"""第三章神经骨干源年实体三折折外资格门。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import average_precision_score

try:
    import torch
    import torch.nn as nn
except ModuleNotFoundError:
    torch = None
    nn = None


SCHEMA_VERSION = "ch3-neural-backbone-source-oof-gate-config-v1"
CHECKPOINT_SCHEMA = "ch3-neural-backbone-source-oof-selected-checkpoint-v1"
INFLIGHT_SCHEMA = "ch3-neural-backbone-source-oof-inflight-v1"
RECEIPT_SCHEMA = "ch3-neural-backbone-source-oof-unit-receipt-v1"
UNIT_STATUS_SCHEMA = "ch3-neural-backbone-source-oof-unit-status-v1"
ALLOWED_ARRAYS = ("X23", "y23", "I23", "M23", "E23")
CELL_ORDER = ("C00", "C11")
T0 = time.time()


def no_grad_if_available(function: Any) -> Any:
    if torch is None:
        return function
    return torch.no_grad()(function)


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def sha256_array(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(array.shape).encode("ascii"))
    digest.update(memoryview(array).cast("B"))
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


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def residual_parameter_count(feature_count: int, hidden_size: int, blocks: int) -> int:
    input_projection = feature_count * hidden_size + hidden_size
    residual = blocks * (2 * hidden_size * hidden_size + 4 * hidden_size)
    fusion = 2 * hidden_size * hidden_size + hidden_size
    output_and_shared_p = hidden_size + 2
    return input_projection + residual + fusion + output_and_shared_p


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("配置模式版本不符")
    if config.get("run_id") != "ch3-resmlp2-cpa-elp-source-oof-gate-seed42-v1":
        raise ValueError("运行身份不符")
    if config.get("model_key") != "resmlp2":
        raise ValueError("首阶段只允许 resmlp2，不得启动其他候选")
    input_contract = config["input_contract"]
    allowed = tuple(input_contract["allowed_arrays"])
    if allowed != ALLOWED_ARRAYS or any(not name.endswith("23") for name in allowed):
        raise ValueError("输入必须严格锁定为五个源年数组")
    if tuple(config.get("allowed_arrays", ())) != ALLOWED_ARRAYS:
        raise ValueError("顶层输入白名单与源年合同不符")
    expected_input = {
        "flow_count": 16_353_511,
        "sequence_count": 271_815,
        "entity_count": 150_680,
        "positive_entity_count": 239,
        "feature_count": 83,
        "sequence_length": 128,
        "entity_code_minimum": 0,
        "entity_code_maximum": 150_679,
    }
    for key, expected in expected_input.items():
        if input_contract.get(key) != expected:
            raise ValueError(f"输入合同 {key} 不是冻结值 {expected}")
    fold = config["fold_contract"]
    if fold != {
        "count": 3,
        "assignment": "seeded-stratified-entity-round-robin",
        "map_to_sequences_via": "E23",
        "map_to_flows_via": ["I23", "M23"],
        "require_each_entity_once_oof": True,
        "require_train_holdout_entity_disjoint": True,
    }:
        raise ValueError("实体三折合同不符")
    if config["cells"] != {
        "C00": {"causal_prefix_aggregation": False, "learned_lp_pooling": False},
        "C11": {"causal_prefix_aggregation": True, "learned_lp_pooling": True},
    }:
        raise ValueError("仅允许 C00 与 C11 两格")
    candidate = config["candidate"]
    expected_candidate = {
        "residual_blocks": 1,
        "residual_affine_layers": 2,
        "hidden_size": 139,
        "activation": "relu",
        "dropout": 0.1,
        "residual_coefficient": 1.0,
        "pre_normalization": True,
        "parameter_formula": "(2+2B)d^2+(86+4B)d+2",
        "parameter_count": 89_796,
        "reference_parameter_count": 90_242,
        "parameter_tolerance_fraction": 0.01,
    }
    if candidate != expected_candidate:
        raise ValueError("resmlp2 结构或参数预算不是预注册值")
    calculated_parameter_count = residual_parameter_count(
        input_contract["feature_count"],
        candidate["hidden_size"],
        candidate["residual_blocks"],
    )
    if calculated_parameter_count != candidate["parameter_count"]:
        raise ValueError("resmlp2 参数公式计算值与冻结参数量不符")
    training = config["training"]
    expected_training = {
        "seed": 42,
        "hidden_size": 139,
        "dropout": 0.1,
        "parameter_count": 89_796,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.002,
        "weight_decay": 0.01,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
        "selection_metric": "holdout_flow_average_precision",
        "selection_rule": "single_epoch_argmax_earliest_tie",
    }
    if training != expected_training:
        raise ValueError("训练预算或选择规则不是冻结值")
    scalar_mirrors = {
        "seed": 42,
        "fold_count": 3,
        "batch_size": 64,
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.002,
        "weight_decay": 0.01,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
    }
    if any(config.get(key) != value for key, value in scalar_mirrors.items()):
        raise ValueError("顶层预注册训练镜像字段不符")
    evaluation = config["evaluation"]
    if evaluation["c00_entity_aggregation"] != "maximum":
        raise ValueError("C00 必须使用实体最大聚合")
    if evaluation["c11_entity_aggregation"] != "fold_learned_p":
        raise ValueError("C11 必须使用各折学得的 p")
    if evaluation["p_diagnostic_grid"] != [0.5, 1.0, 2.0, 4.0, 8.0]:
        raise ValueError("辅助 p 网格不符")
    if evaluation["mlp_reference_c00_pooled"] != 0.5109066464488172:
        raise ValueError("现有多层感知机 C00 参照值不符")
    if evaluation["mlp_reference_c11_pooled"] != 0.5447784766847485:
        raise ValueError("现有多层感知机 C11 参照值不符")
    if evaluation["qualification_rule"] != (
        "candidate_c11_gt_xgb_and_candidate_c11_gt_c00_and_"
        "all_fold_c11_gt_c00_and_at_least_two_fold_c11_gt_xgb"
    ):
        raise ValueError("源年资格规则不符")
    parent = config["parent_contract"]
    if parent != {
        "mlp_run_id": "ch4-e1-source-entity-oof-gate-seed42-v1",
        "xgb_run_id": "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1",
        "xgb_adapter": "semantic168",
        "xgb_p": 1.0,
        "xgb_recovery_proof_schema": "ch3-xgb-parent-recovery-proof-v1",
    }:
        raise ValueError("父基线身份合同不符")
    artifacts = config["artifact_policy"]
    if any(artifacts[key] for key in (
        "persist_per_flow_scores",
        "persist_per_entity_scores",
        "persist_fold_membership",
    )):
        raise ValueError("禁止持久化逐流、逐实体分数或折成员")
    resources = config["resource_contract"]
    if resources != {
        "serial_minimum_free_gpu_memory_gib": 10,
        "serial_minimum_cgroup_available_memory_gib": 40,
        "parallel_minimum_free_gpu_memory_gib": 24,
        "parallel_minimum_cgroup_available_memory_gib": 65,
        "minimum_free_disk_gib": 10,
        "maximum_parallel_training_units": 2,
        "adaptive_parallelism": True,
        "parallelism_policy": (
            "parallel_2_if_gpu_ge_24_gib_and_cgroup_available_ge_65_gib_else_"
            "serial_1_if_gpu_ge_10_gib_and_cgroup_available_ge_40_gib_else_block"
        ),
    }:
        raise ValueError("资源合同不符")
    if not config.get("screening_only") or config.get("formal_paper_evidence"):
        raise ValueError("证据等级必须是快速筛选且非正式论文证据")
    if config.get("independent_test") or config.get("target_year_arrays_read") != 0:
        raise ValueError("本门禁不得访问独立测试或目标年数组")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="第三章 resmlp2 源年实体三折折外资格门")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument(
        "--phase",
        choices=("prepare", "train-unit", "aggregate", "publish-aggregate"),
        default="prepare",
    )
    parser.add_argument("--resume", action="store_true", help="显式恢复合法检查点")
    parser.add_argument("--validate-config", action="store_true", help="只解析并核验配置")
    parser.add_argument("--cell", choices=CELL_ORDER)
    parser.add_argument("--fold", type=int, choices=(0, 1, 2))
    parser.add_argument("--actual-parallelism", type=int, choices=(1, 2))
    parser.add_argument("--resource-receipt", help="启动器写入的资源收据")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    parser.add_argument("--tracking-attempt", type=int, choices=(1, 2), default=1)
    return parser.parse_args()


if nn is not None:
    class PreNormResidualBlock(nn.Module):
        def __init__(self, hidden_size: int, dropout: float):
            super().__init__()
            self.normalization = nn.LayerNorm(hidden_size)
            self.linear1 = nn.Linear(hidden_size, hidden_size)
            self.linear2 = nn.Linear(hidden_size, hidden_size)
            self.activation = nn.ReLU()
            self.dropout1 = nn.Dropout(dropout)
            self.dropout2 = nn.Dropout(dropout)

        def forward(self, values: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
            residual = self.normalization(values)
            residual = self.linear1(residual)
            residual = self.dropout1(self.activation(residual))
            residual = self.dropout2(self.linear2(residual))
            return (values + residual) * mask.unsqueeze(-1)


    class ResidualMlpBackbone(nn.Module):
        def __init__(
            self,
            feature_count: int,
            hidden_size: int,
            dropout: float,
            residual_blocks: int,
            aggregate: bool,
        ):
            super().__init__()
            self.aggregate = aggregate
            self.input_projection = nn.Linear(feature_count, hidden_size)
            self.blocks = nn.ModuleList(
                PreNormResidualBlock(hidden_size, dropout)
                for _ in range(residual_blocks)
            )
            self.fusion = nn.Sequential(
                nn.Linear(hidden_size * 2, hidden_size), nn.ReLU(), nn.Dropout(dropout)
            )
            self.output = nn.Linear(hidden_size, 1)
            self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

        @property
        def p(self) -> torch.Tensor:
            return torch.exp(self.p_log).clamp(1e-3, 1e3)

        def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
            mask = valid.to(values.dtype)
            hidden = self.input_projection(values) * mask.unsqueeze(-1)
            for block in self.blocks:
                hidden = block(hidden, mask)
            if self.aggregate:
                context = torch.cumsum(hidden, 1) / torch.cumsum(mask, 1).clamp(min=1.0).unsqueeze(-1)
                context = context * mask.unsqueeze(-1)
            else:
                context = torch.zeros_like(hidden)
            return self.output(self.fusion(torch.cat((hidden, context), dim=-1))).squeeze(-1)
else:
    class ResidualMlpBackbone:
        pass


def lp_pool(scores: torch.Tensor, valid: torch.Tensor, p_value: torch.Tensor) -> torch.Tensor:
    log_scores = torch.log(scores.clamp(min=1e-7))
    count = valid.sum(1).clamp(min=1.0)
    summed = torch.logsumexp(
        (p_value * log_scores).masked_fill(valid < 0.5, -1e30), dim=1
    )
    return torch.exp((summed - torch.log(count)) / p_value)


def build_model(config: dict[str, Any], cell: str) -> ResidualMlpBackbone:
    if torch is None or nn is None:
        raise RuntimeError("正式计算缺少 torch；请加载项目 GPU 可选依赖")
    cell_config = config["cells"][cell]
    model = ResidualMlpBackbone(
        config["input_contract"]["feature_count"],
        config["training"]["hidden_size"],
        config["training"]["dropout"],
        config["candidate"]["residual_blocks"],
        cell_config["causal_prefix_aggregation"],
    )
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    if parameter_count != config["training"]["parameter_count"]:
        raise RuntimeError(f"模型参数量不符：{parameter_count}")
    reference_count = config["candidate"]["reference_parameter_count"]
    tolerance = config["candidate"]["parameter_tolerance_fraction"]
    if abs(parameter_count - reference_count) / reference_count > tolerance:
        raise RuntimeError("模型参数量超出相对现有多层感知机的百分之一预算")
    return model


def validate_destination(config: dict[str, Any], args: argparse.Namespace) -> None:
    destination = config["swanlab"]
    if (
        args.authorized_swanlab_workspace != destination["workspace"]
        or args.authorized_swanlab_project != destination["project"]
    ):
        raise SystemExit("SwanLab 授权目的地与冻结配置不一致")


def guarded_load(config: dict[str, Any], name: str) -> np.ndarray:
    if name not in ALLOWED_ARRAYS or not name.endswith("23"):
        raise RuntimeError(f"拒绝读取非源年合同数组：{name}")
    if tuple(config["input_contract"]["allowed_arrays"]) != ALLOWED_ARRAYS:
        raise RuntimeError("运行时输入白名单被改变")
    path = Path(config["paths"]["cache_root"]) / f"{name}.npy"
    if not path.is_file():
        raise FileNotFoundError(f"源年数组不存在：{path}")
    return np.load(path, mmap_mode="r", allow_pickle=False)


def source_identity(config: dict[str, Any], output_root: Path, resume: bool) -> dict[str, Any]:
    cache_root = Path(config["paths"]["cache_root"])
    files: dict[str, Any] = {}
    for index, name in enumerate(ALLOWED_ARRAYS, start=1):
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少输入：{path}")
        started = time.time()
        files[name] = {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        log(f"输入哈希 {index}/{len(ALLOWED_ARRAYS)} {name}，耗时 {time.time()-started:.1f}s")
    receipt = {
        "schema_version": "ch3-neural-backbone-source-input-identity-v1",
        "allowed_arrays": list(ALLOWED_ARRAYS),
        "files": files,
        "combined_sha256": canonical_sha256(files),
        "target_year_arrays_read": 0,
    }
    path = output_root / "input-identity.json"
    if path.exists():
        if not resume:
            raise RuntimeError("全新运行已存在输入身份收据，拒绝覆盖")
        if load_json(path) != receipt:
            raise RuntimeError("恢复时输入身份收据不符")
    else:
        atomic_json(path, receipt)
    return receipt


def require_manifest_file(root: Path, manifest: dict[str, Any], name: str) -> Path:
    path = root / name
    entry = manifest.get("files", {}).get(name, {})
    if not path.is_file() or entry.get("bytes") != path.stat().st_size:
        raise RuntimeError(f"多层感知机参照清单缺少或大小不符：{name}")
    if entry.get("sha256") != sha256_file(path):
        raise RuntimeError(f"多层感知机参照清单摘要不符：{name}")
    return path


def parse_source_hash_receipt(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError(f"XGBoost 父输入摘要收据不存在：{path}")
    hashes: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        fields = raw_line.strip().split(maxsplit=1)
        if len(fields) != 2:
            continue
        digest, raw_name = fields
        name = Path(raw_name.lstrip("* ")).name
        array_name = name.removesuffix(".npy")
        if array_name not in ALLOWED_ARRAYS:
            continue
        if (
            array_name in hashes
            or len(digest) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in digest)
        ):
            raise RuntimeError(f"XGBoost 父输入摘要收据含重复或无效项：{array_name}")
        hashes[array_name] = digest
    if tuple(name for name in ALLOWED_ARRAYS if name in hashes) != ALLOWED_ARRAYS:
        raise RuntimeError("XGBoost 父输入摘要收据未完整列出五个源年数组")
    return hashes


def validate_parent_baselines(
    config: dict[str, Any],
    input_identity: dict[str, Any],
    fold_stats: list[dict[str, Any]],
    output_root: Path,
    write_receipt: bool,
) -> dict[str, Any]:
    paths = config["paths"]
    parent_contract = config["parent_contract"]

    mlp_root = Path(paths["mlp_reference_root"])
    mlp_manifest = load_json(mlp_root / "manifest.json")
    if mlp_manifest.get("run_id") != parent_contract["mlp_run_id"]:
        raise RuntimeError("多层感知机参照运行身份不符")
    mlp_aggregate_path = require_manifest_file(mlp_root, mlp_manifest, "aggregate-results.json")
    mlp_fold_path = require_manifest_file(mlp_root, mlp_manifest, "fold-results.json")
    mlp_input_path = require_manifest_file(mlp_root, mlp_manifest, "input-identity.json")
    mlp_aggregate = load_json(mlp_aggregate_path)
    mlp_fold_file = load_json(mlp_fold_path)
    mlp_input = load_json(mlp_input_path)
    mlp_pooled = mlp_aggregate.get("pooled_oof", {})
    mlp_cells = mlp_aggregate.get("cells", {})
    if not isinstance(mlp_cells, dict):
        raise RuntimeError("现有多层感知机参照单元结果不是对象")
    if (
        mlp_aggregate.get("run_id") != parent_contract["mlp_run_id"]
        or mlp_aggregate.get("coverage", {}).get("fits_completed") != 6
        or mlp_aggregate.get("coverage", {}).get("each_entity_oof_exactly_once") is not True
        or mlp_aggregate.get("coverage", {}).get("train_holdout_entity_intersection") != 0
        or mlp_aggregate.get("input", {}).get("arrays") != list(ALLOWED_ARRAYS)
        or mlp_aggregate.get("input", {}).get("target_year_arrays_read") != 0
        or mlp_pooled.get("C00_entity_ap")
        != config["evaluation"]["mlp_reference_c00_pooled"]
        or mlp_pooled.get("C11_entity_ap")
        != config["evaluation"]["mlp_reference_c11_pooled"]
        or mlp_input.get("target_year_arrays_read") != 0
        or mlp_input.get("files") != input_identity.get("files")
        or set(mlp_cells) != set(CELL_ORDER)
        or any(not isinstance(mlp_cells[cell], list) for cell in CELL_ORDER)
        or any(len(mlp_cells[cell]) != 3 for cell in CELL_ORDER)
        or any(
            unit.get("action") not in ("trained", "reused")
            for cell in CELL_ORDER
            for unit in mlp_cells[cell]
        )
    ):
        raise RuntimeError("现有多层感知机 E1 参照合同不符")
    for cell in CELL_ORDER:
        for fold in range(3):
            require_manifest_file(
                mlp_root, mlp_manifest, f"checkpoints/selected-{cell}-fold{fold}.pt"
            )
            status_path = require_manifest_file(
                mlp_root, mlp_manifest, f"units/{cell}-fold{fold}/status.json"
            )
            unit_status = load_json(status_path)
            if unit_status.get("state") != "complete" or unit_status.get("exit_code") != 0:
                raise RuntimeError(f"多层感知机参照 {cell}/fold{fold} 未完成")
    mlp_folds = mlp_fold_file.get("folds")
    if not isinstance(mlp_folds, list) or len(mlp_folds) != 3:
        raise RuntimeError("现有多层感知机参照不是完整三折")
    for fold, (current, reference) in enumerate(zip(fold_stats, mlp_folds, strict=True)):
        expected_stats = {
            key: current[key]
            for key in (
                "fold",
                "holdout_entities",
                "holdout_positive_entities",
                "holdout_sequences",
                "train_sequences",
                "holdout_flows",
                "holdout_positive_flows",
                "train_holdout_entity_intersection",
            )
        }
        if any(reference.get(key) != value for key, value in expected_stats.items()):
            raise RuntimeError(f"多层感知机参照 fold{fold} 统计与本次折不符")
        if not math.isfinite(float(reference.get("C00_entity_ap", float("nan")))):
            raise RuntimeError(f"多层感知机参照 fold{fold} C00 指标无效")
        if not math.isfinite(float(reference.get("C11_entity_ap", float("nan")))):
            raise RuntimeError(f"多层感知机参照 fold{fold} C11 指标无效")

    xgb_root = Path(paths["xgb_parent_root"])
    selection_path = xgb_root / "selection_frozen_xgb2x2.json"
    selection = load_json(selection_path)
    xgb_p = selection.get("p_selection", {}).get(parent_contract["xgb_adapter"], {})
    if (
        selection.get("run_name") != parent_contract["xgb_run_id"]
        or selection.get("seed") != 42
        or selection.get("n_fold") != 3
        or selection.get("adapter_selection", {}).get("selected")
        != parent_contract["xgb_adapter"]
        or xgb_p.get("p_selected") != parent_contract["xgb_p"]
    ):
        raise RuntimeError("XGBoost-C11 父选择收据身份或冻结选择不符")
    selected_curve = [point for point in xgb_p.get("curve", []) if point.get("p") == 1.0]
    if len(selected_curve) != 1:
        raise RuntimeError("XGBoost-C11 父选择曲线缺少唯一 p=1 项")
    xgb_pooled = float(xgb_p.get("oof_ent_ap_at_p", float("nan")))
    xgb_folds = selected_curve[0].get("fold_ent_ap")
    if (
        not math.isfinite(xgb_pooled)
        or not isinstance(xgb_folds, list)
        or len(xgb_folds) != 3
        or not all(math.isfinite(float(value)) for value in xgb_folds)
    ):
        raise RuntimeError("XGBoost-C11 源年 pooled 或三折指标无效")
    parent_fold_stats = selection.get("fold_stat")
    if not isinstance(parent_fold_stats, list) or len(parent_fold_stats) != 3:
        raise RuntimeError("XGBoost 父折统计不完整")
    for fold, (current, parent) in enumerate(zip(fold_stats, parent_fold_stats, strict=True)):
        expected = {
            "fold": current["fold"],
            "n_entity": current["holdout_entities"],
            "n_pos_entity": current["holdout_positive_entities"],
            "n_flow": current["holdout_flows"],
            "n_pos_flow": current["holdout_positive_flows"],
        }
        if parent != expected:
            raise RuntimeError(f"XGBoost 父 fold{fold} 统计与本次折不符")

    recovery_path = Path(paths["xgb_recovery_proof"])
    recovery = load_json(recovery_path)
    recovery_artifacts = recovery.get("artifacts", {})
    required_models = [f"model_oof_semantic168_fold{fold}.json" for fold in range(3)]
    for name in ["effective_config_receipts.json", *required_models]:
        path = xgb_root / name
        artifact = recovery_artifacts.get(name, {})
        if (
            not path.is_file()
            or artifact.get("bytes") != path.stat().st_size
            or artifact.get("sha256") != sha256_file(path)
        ):
            raise RuntimeError(f"XGBoost 父恢复证明与源年制品不符：{name}")
    if (
        recovery.get("schema_version") != parent_contract["xgb_recovery_proof_schema"]
        or recovery.get("parent_run_id") != parent_contract["xgb_run_id"]
        or recovery.get("sourced_from_existing_parent_artifacts_only") is not True
        or recovery.get("does_not_assert_parent_completion") is not True
        or Path(str(recovery.get("parent_run_root", ""))).resolve() != xgb_root.resolve()
        or recovery.get("selection_contract", {}).get("selected_adapter") != "semantic168"
        or recovery.get("selection_contract", {}).get("p_semantic168") != 1.0
        or recovery.get("effective_config_receipts", {}).get("receipt_count") != 11
        or recovery.get("effective_config_receipts", {}).get("all_passed") is not True
        or recovery_artifacts.get("selection_frozen_xgb2x2.json", {}).get("sha256")
        != sha256_file(selection_path)
        or any(
            recovery_artifacts.get(name, {}).get("num_boosted_rounds") != 800
            for name in required_models
        )
    ):
        raise RuntimeError("XGBoost 父恢复证明不能证明冻结源年三折模型完整")

    parent_hashes = parse_source_hash_receipt(Path(paths["xgb_input_sha256_receipt"]))
    current_hashes = {
        name: input_identity["files"][name]["sha256"] for name in ALLOWED_ARRAYS
    }
    if parent_hashes != current_hashes:
        raise RuntimeError("XGBoost 父五数组摘要与本次源年输入不符")

    receipt = {
        "schema_version": "ch3-neural-backbone-source-baseline-receipt-v1",
        "target_year_arrays_read": 0,
        "source_data_sha256": input_identity["combined_sha256"],
        "mlp": {
            "run_id": parent_contract["mlp_run_id"],
            "aggregate_sha256": sha256_file(mlp_aggregate_path),
            "manifest_sha256": sha256_file(mlp_root / "manifest.json"),
            "C00_pooled": float(mlp_pooled["C00_entity_ap"]),
            "C11_pooled": float(mlp_pooled["C11_entity_ap"]),
            "folds": [
                {
                    "fold": fold["fold"],
                    "C00_entity_ap": float(fold["C00_entity_ap"]),
                    "C11_entity_ap": float(fold["C11_entity_ap"]),
                }
                for fold in mlp_folds
            ],
        },
        "xgb": {
            "run_id": parent_contract["xgb_run_id"],
            "selection_sha256": sha256_file(selection_path),
            "recovery_proof_sha256": sha256_file(recovery_path),
            "input_sha256_receipt_sha256": sha256_file(
                Path(paths["xgb_input_sha256_receipt"])
            ),
            "adapter": parent_contract["xgb_adapter"],
            "p": parent_contract["xgb_p"],
            "C11_pooled": xgb_pooled,
            "C11_folds": [float(value) for value in xgb_folds],
        },
    }
    receipt_path = output_root / "baseline-receipt.json"
    if receipt_path.exists():
        if load_json(receipt_path) != receipt:
            raise RuntimeError("父基线收据与当前重算结果不符")
    elif write_receipt:
        atomic_json(receipt_path, receipt)
    else:
        raise RuntimeError("父基线收据不存在；必须先执行 prepare 阶段")
    return receipt


def validate_shapes(
    config: dict[str, Any], X: np.ndarray, y: np.ndarray, I: np.ndarray, M: np.ndarray, E: np.ndarray
) -> None:
    contract = config["input_contract"]
    expected = {
        "X23": (contract["flow_count"], contract["feature_count"]),
        "y23": (contract["flow_count"],),
        "I23": (contract["sequence_count"], contract["sequence_length"]),
        "M23": (contract["sequence_count"], contract["sequence_length"]),
        "E23": (contract["sequence_count"],),
    }
    actual = {"X23": X.shape, "y23": y.shape, "I23": I.shape, "M23": M.shape, "E23": E.shape}
    if actual != expected:
        raise RuntimeError(f"源年数组形状不符：{actual}")
    if not np.isin(np.unique(y), (0.0, 1.0)).all():
        raise RuntimeError("源年标签不是二元标签")
    if int(E.min()) != contract["entity_code_minimum"] or int(E.max()) != contract["entity_code_maximum"]:
        raise RuntimeError("E23 实体码范围不符")
    if len(np.unique(E)) != contract["entity_count"]:
        raise RuntimeError("E23 未覆盖全部冻结实体")


def build_flow_entity(
    I: np.ndarray, M: np.ndarray, E: np.ndarray, flow_count: int, entity_count: int
) -> np.ndarray:
    log("构建仅驻内存的序列到逐流实体映射")
    flow_entity = np.full(flow_count, -1, dtype=np.int32)
    chunk_size = 20_000
    for start in range(0, len(I), chunk_size):
        stop = min(start + chunk_size, len(I))
        indices = np.asarray(I[start:stop])
        valid = np.asarray(M[start:stop]) > 0.5
        if valid.any():
            if int(indices[valid].min()) < 0 or int(indices[valid].max()) >= flow_count:
                raise RuntimeError("I23 有效位置含越界流索引")
            owners = np.broadcast_to(np.asarray(E[start:stop])[:, None], indices.shape)[valid]
            flow_entity[indices[valid]] = owners.astype(np.int32, copy=False)
    if np.any(flow_entity < 0):
        raise RuntimeError(f"I23/M23 未覆盖全部流：缺少 {int((flow_entity < 0).sum())} 条")
    for start in range(0, len(I), chunk_size):
        stop = min(start + chunk_size, len(I))
        indices = np.asarray(I[start:stop])
        valid = np.asarray(M[start:stop]) > 0.5
        owners = np.broadcast_to(np.asarray(E[start:stop])[:, None], indices.shape)[valid]
        if not np.array_equal(flow_entity[indices[valid]], owners):
            raise RuntimeError(f"序列 {start}:{stop} 内出现跨实体流")
    if int(flow_entity.max()) >= entity_count:
        raise RuntimeError("逐流实体映射越界")
    log(f"逐流实体映射完成：{flow_count:,} 条流，{entity_count:,} 个实体，未落盘成员明细")
    return flow_entity


def make_entity_folds(labels: np.ndarray, seed: int, count: int) -> np.ndarray:
    random_state = np.random.RandomState(seed)
    fold_of_entity = np.empty(len(labels), dtype=np.int8)
    for label in (0.0, 1.0):
        entity_ids = np.flatnonzero(labels == label)
        entity_ids = entity_ids[random_state.permutation(len(entity_ids))]
        fold_of_entity[entity_ids] = np.arange(len(entity_ids)) % count
    coverage = np.bincount(fold_of_entity, minlength=count)
    if int(coverage.sum()) != len(labels) or np.any(coverage == 0):
        raise RuntimeError("实体折覆盖失败")
    return fold_of_entity


def capture_rng(generator: torch.Generator) -> dict[str, Any]:
    return {
        "torch_cpu": torch.get_rng_state(),
        "torch_cuda": torch.cuda.get_rng_state_all(),
        "numpy": np.random.get_state(),
        "batch_generator": generator.get_state(),
    }


def restore_rng(state: dict[str, Any], generator: torch.Generator) -> None:
    torch.set_rng_state(state["torch_cpu"])
    torch.cuda.set_rng_state_all(state["torch_cuda"])
    np.random.set_state(state["numpy"])
    generator.set_state(state["batch_generator"])


def move_optimizer_state(optimizer: torch.optim.Optimizer, device: torch.device) -> None:
    for state in optimizer.state.values():
        for key, value in state.items():
            if isinstance(value, torch.Tensor):
                state[key] = value.to(device)


def unit_paths(output_root: Path, cell: str, fold: int) -> tuple[Path, Path, Path]:
    stem = f"{cell}-fold{fold}"
    return (
        output_root / "checkpoints" / f"selected-{stem}.pt",
        output_root / "checkpoints" / f"inflight-{stem}.pt",
        output_root / "receipts" / f"unit-{stem}.json",
    )


def unit_identity(
    config_sha256: str,
    source_sha256: str,
    fold_sha256: str,
    cell: str,
    fold: int,
    train_rows: np.ndarray,
    holdout_rows: np.ndarray,
) -> dict[str, Any]:
    return {
        "cell": cell,
        "fold": fold,
        "config_sha256": config_sha256,
        "source_sha256": source_sha256,
        "fold_assignment_sha256": fold_sha256,
        "train_sequences": {"count": len(train_rows), "sha256": sha256_array(train_rows)},
        "holdout_sequences": {"count": len(holdout_rows), "sha256": sha256_array(holdout_rows)},
    }


def resource_snapshot() -> dict[str, float]:
    rss_mib = float("nan")
    peak_rss_mib = float("nan")
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                rss_mib = int(line.split()[1]) / 1024.0
            elif line.startswith("VmHWM:"):
                peak_rss_mib = int(line.split()[1]) / 1024.0
    except OSError:
        pass
    return {
        "rss_mib": rss_mib,
        "peak_rss_mib": peak_rss_mib,
        "gpu_allocated_mib": torch.cuda.memory_allocated() / 2**20,
        "gpu_reserved_mib": torch.cuda.memory_reserved() / 2**20,
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
        "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
    }


def unit_status_path(output_root: Path, cell: str, fold: int) -> Path:
    return output_root / "units" / f"{cell}-fold{fold}" / "status.json"


def write_unit_status(
    output_root: Path,
    cell: str,
    fold: int,
    state: str,
    stage: str,
    exit_code: int | None,
    detail: str,
    **extra: Any,
) -> None:
    atomic_json(
        unit_status_path(output_root, cell, fold),
        {
            "schema_version": UNIT_STATUS_SCHEMA,
            "cell": cell,
            "fold": fold,
            "state": state,
            "stage": stage,
            "detail": detail,
            "exit_code": exit_code,
            "updated_at_unix": time.time(),
            **extra,
        },
    )


@no_grad_if_available
def holdout_predictions(
    model: ResidualMlpBackbone,
    rows: np.ndarray,
    gX: torch.Tensor,
    gy: torch.Tensor,
    gI: torch.Tensor,
    gM: torch.Tensor,
    inference_batch_size: int = 2048,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    predictions: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    flow_ids: list[np.ndarray] = []
    device = gX.device
    for start in range(0, len(rows), inference_batch_size):
        selected = torch.from_numpy(rows[start : start + inference_batch_size]).to(device)
        indices = gI[selected]
        valid = gM[selected] > 0.5
        batch = indices.shape[0]
        logits = model(gX[indices.reshape(-1)].reshape(batch, indices.shape[1], gX.shape[1]), valid)
        mask = valid.reshape(-1)
        predictions.append(torch.sigmoid(logits).reshape(-1)[mask].float().cpu().numpy())
        labels.append(gy[indices.reshape(-1)].reshape(-1)[mask].float().cpu().numpy())
        flow_ids.append(indices.reshape(-1)[mask].cpu().numpy())
    model.train()
    return np.concatenate(predictions), np.concatenate(labels), np.concatenate(flow_ids)


def validate_selected_checkpoint(
    checkpoint_path: Path,
    receipt_path: Path,
    identity: dict[str, Any],
) -> dict[str, Any] | None:
    checkpoint_exists = checkpoint_path.is_file()
    receipt_exists = receipt_path.is_file()
    if checkpoint_exists != receipt_exists:
        raise RuntimeError(f"检查点与收据不成对，拒绝覆盖：{checkpoint_path}")
    if not checkpoint_exists:
        return None
    receipt = load_json(receipt_path)
    if receipt.get("schema_version") != RECEIPT_SCHEMA or receipt.get("identity") != identity:
        raise RuntimeError(f"检查点身份收据不符：{receipt_path}")
    if receipt.get("checkpoint", {}).get("sha256") != sha256_file(checkpoint_path):
        raise RuntimeError(f"检查点哈希不符：{checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if checkpoint.get("schema_version") != CHECKPOINT_SCHEMA or checkpoint.get("identity") != identity:
        raise RuntimeError(f"检查点内部身份不符：{checkpoint_path}")
    return checkpoint


def train_or_resume_unit(
    config: dict[str, Any],
    output_root: Path,
    identity: dict[str, Any],
    cell: str,
    fold: int,
    train_rows: np.ndarray,
    holdout_rows: np.ndarray,
    gX: torch.Tensor,
    gy: torch.Tensor,
    gI: torch.Tensor,
    gM: torch.Tensor,
    positive_weight: torch.Tensor,
    sequence_positive_weight: float,
    resume: bool,
) -> tuple[ResidualMlpBackbone, dict[str, Any], str]:
    checkpoint_path, inflight_path, receipt_path = unit_paths(output_root, cell, fold)
    identity = {**identity, "schema_version": "ch3-neural-backbone-source-unit-identity-v1"}
    selected = validate_selected_checkpoint(checkpoint_path, receipt_path, identity)
    if selected is not None:
        if not resume:
            raise RuntimeError(f"全新运行已有完成单元，拒绝覆盖：{cell}/fold{fold}")
        model = build_model(config, cell).to(gX.device)
        model.load_state_dict(selected["model"])
        log(f"{cell}/fold{fold} 合法检查点复用，跳过训练")
        return model, selected["selection"], "reused"
    if (inflight_path.exists() or receipt_path.exists()) and not resume:
        raise RuntimeError(f"全新运行已有单元制品，拒绝覆盖：{cell}/fold{fold}")

    training = config["training"]
    seed = training["seed"]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    model = build_model(config, cell).to(gX.device)
    decay = [parameter for parameter in model.parameters() if parameter.ndim > 1]
    no_decay = [parameter for parameter in model.parameters() if parameter.ndim <= 1]
    optimizer = torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": training["weight_decay"]},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=training["learning_rate"],
    )
    generator = torch.Generator().manual_seed(seed)
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_p = float("nan")
    best_state: dict[str, torch.Tensor] | None = None
    elapsed_before = 0.0
    encoded_sequences = 0
    encoded_effective_flows = 0
    selection_inference_seconds = 0.0
    start_epoch = 1

    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("schema_version") != INFLIGHT_SCHEMA or inflight.get("identity") != identity:
            raise RuntimeError(f"在途检查点身份不符：{inflight_path}")
        model.load_state_dict(inflight["model"])
        optimizer.load_state_dict(inflight["optimizer"])
        move_optimizer_state(optimizer, gX.device)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_p = float(inflight["best_p"])
        best_state = inflight["best_state"]
        elapsed_before = float(inflight["elapsed_seconds"])
        encoded_sequences = int(inflight["encoded_sequences"])
        encoded_effective_flows = int(inflight["encoded_effective_flows"])
        selection_inference_seconds = float(inflight["selection_inference_seconds"])
        restore_rng(inflight["rng"], generator)
        start_epoch = int(inflight["epoch"]) + 1
        log(f"{cell}/fold{fold} 从 epoch {start_epoch-1} 边界恢复")

    flow_loss = nn.BCEWithLogitsLoss(reduction="none", pos_weight=positive_weight)
    entity_loss = nn.BCELoss(reduction="none")
    uses_lp = config["cells"][cell]["learned_lp_pooling"]
    device = gX.device
    effective_flow_counter = torch.tensor(
        encoded_effective_flows, dtype=torch.int64, device=device
    )
    unit_started = time.time()
    total_steps = training["epochs"] * training["steps_per_epoch"]
    completed_before = (start_epoch - 1) * training["steps_per_epoch"]
    model.train()
    for epoch in range(start_epoch, training["epochs"] + 1):
        epoch_started = time.time()
        running_loss = 0.0
        for step in range(1, training["steps_per_epoch"] + 1):
            random_positions = torch.randint(0, len(train_rows), (training["batch_size"],), generator=generator)
            selected_rows = torch.from_numpy(train_rows[random_positions.numpy()]).to(device)
            indices = gI[selected_rows]
            valid = gM[selected_rows] > 0.5
            batch = indices.shape[0]
            values = gX[indices.reshape(-1)].reshape(batch, indices.shape[1], gX.shape[1])
            labels = gy[indices.reshape(-1)].reshape(batch, indices.shape[1])
            logits = model(values, valid)
            mask = valid.to(logits.dtype)
            encoded_sequences += batch
            effective_flow_counter += valid.sum()
            loss = (flow_loss(logits, labels) * mask).sum() / mask.sum().clamp(min=1.0)
            if uses_lp:
                sequence_score = lp_pool(torch.sigmoid(logits), mask, model.p).clamp(1e-6, 1 - 1e-6)
                sequence_label = (labels * mask).amax(1)
                weight = 1.0 + (sequence_positive_weight - 1.0) * sequence_label
                loss = loss + training["auxiliary_loss_weight"] * (
                    (entity_loss(sequence_score, sequence_label) * weight).sum() / weight.sum()
                )
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), training["gradient_clip_norm"])
            optimizer.step()
            running_loss += float(loss.detach())
            if step % 250 == 0:
                completed = completed_before + (epoch - start_epoch) * training["steps_per_epoch"] + step
                elapsed = elapsed_before + time.time() - unit_started
                rate = completed / max(elapsed, 1e-9)
                eta = (total_steps - completed) / max(rate, 1e-9)
                resources = resource_snapshot()
                log(
                    f"{cell}/fold{fold} 心跳 epoch={epoch}/{training['epochs']} "
                    f"step={step}/{training['steps_per_epoch']} 总步={completed}/{total_steps} "
                    f"吞吐={rate:.1f}步/s 累计={elapsed/60:.1f}分 预计剩余={eta/60:.1f}分 "
                    f"RSS={resources['rss_mib']:.0f}MiB GPU={resources['gpu_allocated_mib']:.0f}MiB"
                )
        inference_started = time.time()
        predictions, labels, _ = holdout_predictions(model, holdout_rows, gX, gy, gI, gM)
        inference_seconds = time.time() - inference_started
        selection_inference_seconds += inference_seconds
        if labels.max() <= 0:
            raise RuntimeError(f"{cell}/fold{fold} 留出逐流标签无正例")
        validation_ap = float(average_precision_score(labels, predictions))
        p_value = float(model.p.detach())
        history.append(
            {
                "epoch": epoch,
                "holdout_flow_ap": validation_ap,
                "p": p_value if uses_lp else None,
                "mean_training_loss": running_loss / training["steps_per_epoch"],
                "holdout_inference_seconds": inference_seconds,
                "epoch_seconds": time.time() - epoch_started,
            }
        )
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_p = p_value
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
        elapsed = elapsed_before + time.time() - unit_started
        encoded_effective_flows = int(effective_flow_counter.detach())
        atomic_torch(
            inflight_path,
            {
                "schema_version": INFLIGHT_SCHEMA,
                "identity": identity,
                "epoch": epoch,
                "model": {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()},
                "optimizer": optimizer.state_dict(),
                "history": history,
                "best_ap": best_ap,
                "best_epoch": best_epoch,
                "best_p": best_p,
                "best_state": best_state,
                "elapsed_seconds": elapsed,
                "encoded_sequences": encoded_sequences,
                "encoded_effective_flows": encoded_effective_flows,
                "selection_inference_seconds": selection_inference_seconds,
                "rng": capture_rng(generator),
            },
        )
        append_jsonl(
            output_root / "units" / f"{cell}-fold{fold}" / "progress.jsonl",
            {
                "cell": cell,
                "fold": fold,
                "epoch": epoch,
                "holdout_flow_ap": validation_ap,
                "p": p_value if uses_lp else None,
                "elapsed_seconds": elapsed,
            },
        )
        log(
            f"{cell}/fold{fold} epoch {epoch}/{training['epochs']} "
            f"留出逐流AP={validation_ap:.8f} p={p_value:.6f}"
        )

    if best_state is None or best_epoch <= 0:
        raise RuntimeError(f"{cell}/fold{fold} 未产生可选检查点")
    model.load_state_dict(best_state)
    selection = {
        "selected_epoch": best_epoch,
        "holdout_flow_ap": best_ap,
        "p": best_p if uses_lp else None,
        "history": history,
        "training_seconds": elapsed_before + time.time() - unit_started,
        "selection_inference_seconds": selection_inference_seconds,
        "encoded_sequences": encoded_sequences,
        "encoded_effective_flows": encoded_effective_flows,
        "optimizer_steps": training["epochs"] * training["steps_per_epoch"],
        "sequences_per_step": training["batch_size"],
    }
    atomic_torch(
        checkpoint_path,
        {
            "schema_version": CHECKPOINT_SCHEMA,
            "identity": identity,
            "model": best_state,
            "selection": selection,
        },
    )
    checkpoint_sha = sha256_file(checkpoint_path)
    atomic_json(
        receipt_path,
        {
            "schema_version": RECEIPT_SCHEMA,
            "identity": identity,
            "checkpoint": {
                "filename": checkpoint_path.name,
                "bytes": checkpoint_path.stat().st_size,
                "sha256": checkpoint_sha,
            },
            "selection": selection,
            "completed": True,
        },
    )
    inflight_path.unlink(missing_ok=True)
    log(f"{cell}/fold{fold} 完成：epoch={best_epoch} AP={best_ap:.8f} checkpoint={checkpoint_sha}")
    return model, selection, "trained"


def entity_scores(
    flow_scores: np.ndarray,
    flow_entity: np.ndarray,
    entity_count: int,
    p_value: float | None,
    flow_mask: np.ndarray | None = None,
) -> np.ndarray:
    mask = np.isfinite(flow_scores)
    if flow_mask is not None:
        mask &= flow_mask
    entities = flow_entity[mask]
    scores = flow_scores[mask]
    if p_value is None:
        result = np.full(entity_count, -np.inf, dtype=np.float32)
        np.maximum.at(result, entities, scores)
        return result
    numerator = np.zeros(entity_count, dtype=np.float64)
    count = np.zeros(entity_count, dtype=np.float64)
    np.add.at(numerator, entities, np.clip(scores, 1e-7, 1.0).astype(np.float64) ** p_value)
    np.add.at(count, entities, 1.0)
    return np.where(
        count > 0,
        (numerator / np.maximum(count, 1.0)) ** (1.0 / p_value),
        -np.inf,
    ).astype(np.float32)


def ap_for_entities(labels: np.ndarray, scores: np.ndarray, mask: np.ndarray | None = None) -> float:
    valid = np.isfinite(scores)
    if mask is not None:
        valid &= mask
    if labels[valid].max() <= 0 or labels[valid].min() >= 1:
        raise RuntimeError("实体 AP 子集缺少正类或负类")
    return float(average_precision_score(labels[valid], scores[valid]))


def fold_receipt(
    fold: int,
    fold_of_entity: np.ndarray,
    fold_of_sequence: np.ndarray,
    fold_of_flow: np.ndarray,
    entity_labels: np.ndarray,
    flow_labels: np.ndarray,
) -> dict[str, Any]:
    entity_mask = fold_of_entity == fold
    sequence_mask = fold_of_sequence == fold
    flow_mask = fold_of_flow == fold
    return {
        "fold": fold,
        "holdout_entities": int(entity_mask.sum()),
        "holdout_positive_entities": int(entity_labels[entity_mask].sum()),
        "holdout_sequences": int(sequence_mask.sum()),
        "train_sequences": int((~sequence_mask).sum()),
        "holdout_flows": int(flow_mask.sum()),
        "holdout_positive_flows": int(flow_labels[flow_mask].sum()),
        "train_holdout_entity_intersection": 0,
    }


def write_status(output_root: Path, state: str, stage: str, exit_code: int | None, detail: str) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-neural-backbone-source-oof-status-v1",
            "state": state,
            "stage": stage,
            "detail": detail,
            "exit_code": exit_code,
            "updated_at_unix": time.time(),
            "screening_only": True,
            "formal_paper_evidence": False,
            "target_year_arrays_read": 0,
        },
    )


def build_manifest(output_root: Path, run_id: str) -> None:
    names = [
        "config.json",
        "input-identity.json",
        "fold-assignment-receipt.json",
        "baseline-receipt.json",
        "resource-receipt.json",
        "resume-receipt.json",
        "fold-results.json",
        "aggregate-results.json",
        "status.json",
    ]
    tracking = output_root / "swanlab-receipt.json"
    if tracking.is_file():
        names.append("swanlab-receipt.json")
    for cell in CELL_ORDER:
        for fold in range(3):
            names.extend(
                (
                    f"checkpoints/selected-{cell}-fold{fold}.pt",
                    f"receipts/unit-{cell}-fold{fold}.json",
                    f"units/{cell}-fold{fold}/status.json",
                )
            )
    files: dict[str, Any] = {}
    for name in names:
        path = output_root / name
        if not path.is_file():
            raise RuntimeError(f"制品清单缺少：{name}")
        files[name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    atomic_json(
        output_root / "manifest.json",
        {
            "schema_version": "ch3-neural-backbone-source-oof-manifest-v1",
            "run_id": run_id,
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "fold_membership_persisted": False,
            "files": files,
        },
    )


def load_prepared_identity(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    receipt_path = output_root / "input-identity.json"
    if not receipt_path.is_file():
        raise RuntimeError("源年输入身份收据不存在；必须先执行 prepare 阶段")
    receipt = load_json(receipt_path)
    if (
        receipt.get("schema_version") != "ch3-neural-backbone-source-input-identity-v1"
        or receipt.get("allowed_arrays") != list(ALLOWED_ARRAYS)
        or receipt.get("target_year_arrays_read") != 0
    ):
        raise RuntimeError("源年输入身份收据不符合冻结合同")
    cache_root = Path(config["paths"]["cache_root"])
    for name in ALLOWED_ARRAYS:
        path = cache_root / f"{name}.npy"
        recorded = receipt.get("files", {}).get(name, {})
        if not path.is_file() or recorded.get("filename") != path.name:
            raise RuntimeError(f"源年输入身份缺少 {name}")
        if recorded.get("bytes") != path.stat().st_size:
            raise RuntimeError(f"源年输入大小在 prepare 后发生变化：{name}")
    return receipt


def load_source_context(
    config: dict[str, Any],
    args: argparse.Namespace,
    config_path: Path,
    prepare: bool,
) -> dict[str, Any]:
    validate_destination(config, args)
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    config_sha = sha256_file(config_path)
    config_snapshot = {**config, "config_file_sha256": config_sha}
    snapshot_path = output_root / "config.json"
    if snapshot_path.exists():
        if load_json(snapshot_path) != config_snapshot:
            raise RuntimeError("运行根已有不匹配配置快照，拒绝覆盖")
        if prepare and not args.resume:
            raise RuntimeError("全新运行已有配置快照，拒绝覆盖")
    else:
        if not prepare:
            raise RuntimeError("配置快照不存在；必须先执行 prepare 阶段")
        atomic_json(snapshot_path, config_snapshot)
    if prepare:
        write_status(output_root, "running", "input-identity", None, "开始核验五个源年数组")
        input_identity = source_identity(config, output_root, args.resume)
    else:
        input_identity = load_prepared_identity(config, output_root)

    X = guarded_load(config, "X23")
    y = guarded_load(config, "y23")
    I = guarded_load(config, "I23")
    M = guarded_load(config, "M23")
    E = guarded_load(config, "E23")
    validate_shapes(config, X, y, I, M, E)
    contract = config["input_contract"]
    flow_entity = build_flow_entity(I, M, E, contract["flow_count"], contract["entity_count"])
    entity_labels = np.zeros(contract["entity_count"], dtype=np.float32)
    np.maximum.at(entity_labels, flow_entity, np.asarray(y))
    if int(entity_labels.sum()) != contract["positive_entity_count"]:
        raise RuntimeError(f"正例实体数不符：{int(entity_labels.sum())}")
    fold_count = config["fold_contract"]["count"]
    fold_of_entity = make_entity_folds(entity_labels, config["training"]["seed"], fold_count)
    fold_of_sequence = fold_of_entity[np.asarray(E)]
    fold_of_flow = fold_of_entity[flow_entity]
    fold_sha = canonical_sha256(
        {
            "dtype": str(fold_of_entity.dtype),
            "shape": fold_of_entity.shape,
            "sha256": sha256_array(fold_of_entity),
        }
    )
    fold_stats = [
        fold_receipt(k, fold_of_entity, fold_of_sequence, fold_of_flow, entity_labels, np.asarray(y))
        for k in range(fold_count)
    ]
    if sum(item["holdout_entities"] for item in fold_stats) != contract["entity_count"]:
        raise RuntimeError("三折实体覆盖不是恰好一次")
    fold_receipt_value = {
        "schema_version": "ch3-neural-backbone-source-entity-fold-receipt-v1",
        "assignment_sha256": fold_sha,
        "assignment_persisted": False,
        "entity_coverage_count": contract["entity_count"],
        "each_entity_holdout_count": 1,
        "folds": fold_stats,
    }
    fold_receipt_path = output_root / "fold-assignment-receipt.json"
    if fold_receipt_path.exists():
        if load_json(fold_receipt_path) != fold_receipt_value:
            raise RuntimeError("实体三折收据与重算结果不符")
    elif prepare:
        atomic_json(fold_receipt_path, fold_receipt_value)
    else:
        raise RuntimeError("实体三折收据不存在；必须先执行 prepare 阶段")
    baseline = validate_parent_baselines(
        config,
        input_identity,
        fold_stats,
        output_root,
        write_receipt=prepare,
    )
    log(f"实体确定性三折核验完成，身份 SHA-256={fold_sha}；成员明细未落盘")
    return {
        "output_root": output_root,
        "config_sha": config_sha,
        "input_identity": input_identity,
        "X": X,
        "y": y,
        "I": I,
        "M": M,
        "E": E,
        "contract": contract,
        "flow_entity": flow_entity,
        "entity_labels": entity_labels,
        "fold_count": fold_count,
        "fold_of_entity": fold_of_entity,
        "fold_of_sequence": fold_of_sequence,
        "fold_of_flow": fold_of_flow,
        "fold_sha": fold_sha,
        "fold_stats": fold_stats,
        "baseline": baseline,
    }


def prepare(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    context = load_source_context(config, args, config_path, prepare=True)
    write_status(
        context["output_root"],
        "prepared",
        "training-pending",
        None,
        "输入身份与实体三折收据已冻结，等待六个训练单元",
    )


def train_unit(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    if args.cell is None or args.fold is None:
        raise ValueError("train-unit 阶段必须同时指定 --cell 与 --fold")
    if torch is None or not torch.cuda.is_available():
        raise RuntimeError("CUDA 不可用，拒绝启动正式训练单元")
    started = time.time()
    context = load_source_context(config, args, config_path, prepare=False)
    output_root = context["output_root"]
    cell = args.cell
    fold = args.fold
    previous_status: dict[str, Any] | None = None
    status_path = unit_status_path(output_root, cell, fold)
    if status_path.is_file():
        previous_status = load_json(status_path)
        if not args.resume:
            raise RuntimeError(f"全新运行已有单元状态，拒绝覆盖：{cell}/fold{fold}")
        atomic_json(
            status_path.with_name(f"status-before-resume-{time.time_ns()}.json"),
            previous_status,
        )
    train_rows = np.flatnonzero(context["fold_of_sequence"] != fold).astype(np.int64, copy=False)
    holdout_rows = np.flatnonzero(context["fold_of_sequence"] == fold).astype(np.int64, copy=False)
    train_entities = np.unique(np.asarray(context["E"])[train_rows])
    holdout_entities = np.unique(np.asarray(context["E"])[holdout_rows])
    if np.intersect1d(train_entities, holdout_entities).size != 0:
        raise RuntimeError(f"{cell}/fold{fold} 训练与留出实体相交")
    identity = unit_identity(
        context["config_sha"],
        context["input_identity"]["combined_sha256"],
        context["fold_sha"],
        cell,
        fold,
        train_rows,
        holdout_rows,
    )
    checkpoint_path, _, receipt_path = unit_paths(output_root, cell, fold)
    selected = validate_selected_checkpoint(
        checkpoint_path,
        receipt_path,
        {**identity, "schema_version": "ch3-neural-backbone-source-unit-identity-v1"},
    )
    if selected is not None:
        if not args.resume:
            raise RuntimeError(f"全新运行已有完成单元，拒绝覆盖：{cell}/fold{fold}")
        selection = selected["selection"]
        write_unit_status(
            output_root,
            cell,
            fold,
            "complete",
            "finished",
            0,
            "合法完成单元已幂等跳过",
            action="reused",
            wall_seconds=(previous_status or {}).get("wall_seconds", time.time() - started),
            selection={
                "selected_epoch": selection["selected_epoch"],
                "holdout_flow_ap": selection["holdout_flow_ap"],
                "p": selection["p"],
                "training_seconds": selection["training_seconds"],
                "selection_inference_seconds": selection["selection_inference_seconds"],
                "encoded_sequences": selection["encoded_sequences"],
                "encoded_effective_flows": selection["encoded_effective_flows"],
                "optimizer_steps": selection["optimizer_steps"],
                "sequences_per_step": selection["sequences_per_step"],
            },
            resource=(previous_status or {}).get("resource", {}),
        )
        log(f"{cell}/fold{fold} 合法完成单元已幂等跳过")
        return
    write_unit_status(output_root, cell, fold, "running", "device-load", None, "加载源年数组")
    torch.cuda.reset_peak_memory_stats()
    device = torch.device("cuda")
    gX = torch.from_numpy(np.asarray(context["X"])).to(device)
    gy = torch.from_numpy(np.asarray(context["y"])).to(device)
    gI = torch.from_numpy(np.asarray(context["I"])).to(device)
    gM = torch.from_numpy(np.asarray(context["M"])).to(device)
    positive_rate = float(np.asarray(context["y"]).mean())
    positive_weight = torch.tensor([(1.0 - positive_rate) / positive_rate], device=device)
    sequence_labels = (
        np.asarray(context["y"])[np.asarray(context["I"])]
        * (np.asarray(context["M"]) > 0.5)
    ).max(axis=1) > 0
    sequence_positive_weight = float(
        (1.0 - sequence_labels.mean()) / max(sequence_labels.mean(), 1e-8)
    )
    write_unit_status(output_root, cell, fold, "running", "training", None, "训练或恢复折单元")
    _, selection, action = train_or_resume_unit(
        config,
        output_root,
        identity,
        cell,
        fold,
        train_rows,
        holdout_rows,
        gX,
        gy,
        gI,
        gM,
        positive_weight,
        sequence_positive_weight,
        args.resume,
    )
    wall_seconds = time.time() - started
    write_unit_status(
        output_root,
        cell,
        fold,
        "complete",
        "finished",
        0,
        "训练单元完成",
        action=action,
        wall_seconds=wall_seconds,
        selection={
            "selected_epoch": selection["selected_epoch"],
            "holdout_flow_ap": selection["holdout_flow_ap"],
            "p": selection["p"],
            "training_seconds": selection["training_seconds"],
            "selection_inference_seconds": selection["selection_inference_seconds"],
            "encoded_sequences": selection["encoded_sequences"],
            "encoded_effective_flows": selection["encoded_effective_flows"],
            "optimizer_steps": selection["optimizer_steps"],
            "sequences_per_step": selection["sequences_per_step"],
        },
        resource=resource_snapshot(),
    )


def aggregate(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    if args.actual_parallelism is None or args.resource_receipt is None:
        raise ValueError("aggregate 阶段必须提供实际并发数与资源收据")
    if torch is None or not torch.cuda.is_available():
        raise RuntimeError("CUDA 不可用，拒绝执行正式聚合")
    context = load_source_context(config, args, config_path, prepare=False)
    output_root = context["output_root"]
    config_sha = context["config_sha"]
    input_identity = context["input_identity"]
    X, y, I, M, E = (context[name] for name in ("X", "y", "I", "M", "E"))
    contract = context["contract"]
    flow_entity = context["flow_entity"]
    entity_labels = context["entity_labels"]
    fold_count = context["fold_count"]
    fold_of_entity = context["fold_of_entity"]
    fold_of_sequence = context["fold_of_sequence"]
    fold_of_flow = context["fold_of_flow"]
    fold_sha = context["fold_sha"]
    fold_stats = context["fold_stats"]
    baseline = context["baseline"]
    resource_receipt_path = Path(args.resource_receipt)
    if not resource_receipt_path.is_file():
        raise RuntimeError("启动器资源收据不存在")
    resource_receipt = load_json(resource_receipt_path)
    if resource_receipt.get("actual_parallelism") != args.actual_parallelism:
        raise RuntimeError("资源收据中的实际并发数不符")

    device = torch.device("cuda")
    write_status(output_root, "running", "device-load", None, "源年数组加载到单卡")
    gX = torch.from_numpy(np.asarray(X)).to(device)
    gy = torch.from_numpy(np.asarray(y)).to(device)
    gI = torch.from_numpy(np.asarray(I)).to(device)
    gM = torch.from_numpy(np.asarray(M)).to(device)
    log(f"源年五数组就位；GPU 已分配 {torch.cuda.memory_allocated()/2**30:.2f} GiB")
    unit_results: dict[str, list[dict[str, Any]]] = {cell: [] for cell in CELL_ORDER}
    entity_results: dict[str, np.ndarray] = {}
    grid_results: list[dict[str, Any]] = []
    resume_events: list[dict[str, Any]] = []
    for cell in CELL_ORDER:
        flow_scores = np.full(contract["flow_count"], np.nan, dtype=np.float32)
        seen = np.zeros(contract["flow_count"], dtype=np.bool_)
        selected_p: list[float | None] = []
        for fold in range(fold_count):
            train_rows = np.flatnonzero(fold_of_sequence != fold).astype(np.int64, copy=False)
            holdout_rows = np.flatnonzero(fold_of_sequence == fold).astype(np.int64, copy=False)
            train_entities = np.unique(np.asarray(E)[train_rows])
            holdout_entities = np.unique(np.asarray(E)[holdout_rows])
            if np.intersect1d(train_entities, holdout_entities).size != 0:
                raise RuntimeError(f"{cell}/fold{fold} 训练与留出实体相交")
            identity = unit_identity(
                config_sha,
                input_identity["combined_sha256"],
                fold_sha,
                cell,
                fold,
                train_rows,
                holdout_rows,
            )
            identity = {**identity, "schema_version": "ch3-neural-backbone-source-unit-identity-v1"}
            checkpoint_path, _, receipt_path = unit_paths(output_root, cell, fold)
            selected = validate_selected_checkpoint(checkpoint_path, receipt_path, identity)
            if selected is None:
                raise RuntimeError(f"{cell}/fold{fold} 缺少完成检查点")
            status = load_json(unit_status_path(output_root, cell, fold))
            if (
                status.get("schema_version") != UNIT_STATUS_SCHEMA
                or status.get("state") != "complete"
                or status.get("exit_code") != 0
            ):
                raise RuntimeError(f"{cell}/fold{fold} 单元状态未完成")
            action = status.get("action")
            if action not in ("trained", "reused"):
                raise RuntimeError(f"{cell}/fold{fold} 单元动作无效")
            model = build_model(config, cell).to(device)
            model.load_state_dict(selected["model"])
            selection = selected["selection"]
            inference_started = time.time()
            predictions, labels, flow_ids = holdout_predictions(model, holdout_rows, gX, gy, gI, gM)
            aggregate_inference_seconds = time.time() - inference_started
            if not np.all(fold_of_flow[flow_ids] == fold):
                raise RuntimeError(f"{cell}/fold{fold} 预测流越出留出实体折")
            flow_scores[flow_ids] = predictions
            seen[flow_ids] = True
            selected_p.append(selection["p"])
            unit_results[cell].append(
                {
                    "fold": fold,
                    "action": action,
                    "selected_epoch": selection["selected_epoch"],
                    "holdout_flow_ap": selection["holdout_flow_ap"],
                    "p": selection["p"],
                    "holdout_prediction_occurrences": int(len(predictions)),
                    "holdout_unique_flows": int(np.unique(flow_ids).size),
                    "wall_seconds": status.get("wall_seconds"),
                    "training_seconds": selection["training_seconds"],
                    "selection_inference_seconds": selection[
                        "selection_inference_seconds"
                    ],
                    "aggregate_inference_seconds": aggregate_inference_seconds,
                    "optimizer_steps": selection["optimizer_steps"],
                    "encoded_sequences": selection["encoded_sequences"],
                    "encoded_effective_flows": selection["encoded_effective_flows"],
                    "sequences_per_step": selection["sequences_per_step"],
                    "resource": status.get("resource"),
                }
            )
            resume_events.append({"cell": cell, "fold": fold, "action": action})
            del model, predictions, labels, flow_ids, train_entities, holdout_entities
            torch.cuda.empty_cache()
        if not seen.all() or not np.isfinite(flow_scores).all():
            raise RuntimeError(
                f"{cell} pooled OOF 未覆盖全部流：seen={int(seen.sum())}/{len(seen)}"
            )
        if cell == "C00":
            scores = entity_scores(flow_scores, flow_entity, contract["entity_count"], None)
        else:
            scores = np.full(contract["entity_count"], -np.inf, dtype=np.float32)
            for fold, p_value in enumerate(selected_p):
                if p_value is None:
                    raise RuntimeError(f"C11/fold{fold} 缺少学得的 p")
                fold_scores = entity_scores(
                    flow_scores,
                    flow_entity,
                    contract["entity_count"],
                    float(p_value),
                    fold_of_flow == fold,
                )
                mask = fold_of_entity == fold
                scores[mask] = fold_scores[mask]
            for p_value in config["evaluation"]["p_diagnostic_grid"]:
                diagnostic_scores = entity_scores(
                    flow_scores, flow_entity, contract["entity_count"], float(p_value)
                )
                grid_results.append(
                    {
                        "p": p_value,
                        "pooled_oof_entity_ap": ap_for_entities(entity_labels, diagnostic_scores),
                    }
                )
        if not np.isfinite(scores).all():
            raise RuntimeError(f"{cell} 实体折外分数未完整覆盖")
        entity_results[cell] = scores
        del flow_scores, seen

    fold_results: list[dict[str, Any]] = []
    for fold in range(fold_count):
        mask = fold_of_entity == fold
        c00_ap = ap_for_entities(entity_labels, entity_results["C00"], mask)
        c11_ap = ap_for_entities(entity_labels, entity_results["C11"], mask)
        fold_results.append(
            {
                **fold_stats[fold],
                "C00_entity_ap": c00_ap,
                "C11_entity_ap": c11_ap,
                "delta_C11_minus_C00": c11_ap - c00_ap,
                "C00_selected_epoch": unit_results["C00"][fold]["selected_epoch"],
                "C11_selected_epoch": unit_results["C11"][fold]["selected_epoch"],
                "C11_learned_p": unit_results["C11"][fold]["p"],
            }
        )
    c00_pooled = ap_for_entities(entity_labels, entity_results["C00"])
    c11_pooled = ap_for_entities(entity_labels, entity_results["C11"])
    delta_pooled = c11_pooled - c00_pooled
    fold_deltas = [item["delta_C11_minus_C00"] for item in fold_results]
    fold_delta_range = max(fold_deltas) - min(fold_deltas)
    mlp_reference = baseline["mlp"]
    xgb_reference = baseline["xgb"]
    for fold, item in enumerate(fold_results):
        item["delta_C11_minus_mlp_C11"] = (
            item["C11_entity_ap"] - mlp_reference["folds"][fold]["C11_entity_ap"]
        )
        item["delta_C11_minus_xgb_C11"] = (
            item["C11_entity_ap"] - xgb_reference["C11_folds"][fold]
        )
    depth_gain = c11_pooled - mlp_reference["C11_pooled"]
    xgb_gap = xgb_reference["C11_pooled"] - c11_pooled
    current_xgb_gap = xgb_reference["C11_pooled"] - mlp_reference["C11_pooled"]
    all_fold_mechanism_positive = all(value > 0 for value in fold_deltas)
    depth_signal = (
        depth_gain > 0
        and all_fold_mechanism_positive
        and xgb_gap < current_xgb_gap
    )
    folds_above_xgb = sum(
        item["delta_C11_minus_xgb_C11"] > 0 for item in fold_results
    )
    source_qualified = (
        c11_pooled > xgb_reference["C11_pooled"]
        and c11_pooled > c00_pooled
        and all_fold_mechanism_positive
        and folds_above_xgb >= 2
    )
    qualification_status = "source_qualified" if source_qualified else "source_rejected"
    depth_verdict = (
        "allow_resmlp4"
        if depth_signal
        else "reject_residual_depth_family_at_resmlp2"
    )
    all_units = [unit for cell_units in unit_results.values() for unit in cell_units]
    total_optimizer_steps = sum(int(unit["optimizer_steps"]) for unit in all_units)
    total_encoded_sequences = sum(int(unit["encoded_sequences"]) for unit in all_units)
    total_effective_flows = sum(int(unit["encoded_effective_flows"]) for unit in all_units)
    total_training_seconds = sum(float(unit["training_seconds"]) for unit in all_units)
    total_selection_inference_seconds = sum(
        float(unit["selection_inference_seconds"]) for unit in all_units
    )
    total_aggregate_inference_seconds = sum(
        float(unit["aggregate_inference_seconds"]) for unit in all_units
    )
    resource_receipt["aggregate_finished_at_unix"] = time.time()
    resource_receipt["overall_wall_seconds_through_aggregate"] = (
        resource_receipt["aggregate_finished_at_unix"]
        - float(resource_receipt["run_started_at_unix"])
    )
    atomic_json(resource_receipt_path, resource_receipt)
    result = {
        "schema_version": "ch3-neural-backbone-source-oof-results-v1",
        "run_id": config["run_id"],
        "evidence": {
            "screening_only": True,
            "formal_paper_evidence": False,
            "independent_test": False,
        },
        "input": {
            "arrays": list(ALLOWED_ARRAYS),
            "source_data_sha256": input_identity["combined_sha256"],
            "target_year_arrays_read": 0,
        },
        "coverage": {
            "entities": contract["entity_count"],
            "positive_entities": contract["positive_entity_count"],
            "flows": contract["flow_count"],
            "sequences": contract["sequence_count"],
            "folds": fold_count,
            "fits_completed": 6,
            "each_entity_oof_exactly_once": True,
            "train_holdout_entity_intersection": 0,
        },
        "model": {
            "model_key": config["model_key"],
            "display_name": config["display_name"],
            "residual_blocks": config["candidate"]["residual_blocks"],
            "residual_affine_layers": config["candidate"]["residual_affine_layers"],
            "hidden_size": config["candidate"]["hidden_size"],
            "parameter_count": config["candidate"]["parameter_count"],
            "parameter_formula": config["candidate"]["parameter_formula"],
            "pytorch_version": torch.__version__,
        },
        "cells": unit_results,
        "folds": fold_results,
        "pooled_oof": {
            "C00_entity_ap": c00_pooled,
            "C11_entity_ap": c11_pooled,
            "delta_C11_minus_C00": delta_pooled,
            "fold_delta_range": fold_delta_range,
        },
        "baselines": baseline,
        "comparisons": {
            "candidate_C11_minus_mlp_C11": depth_gain,
            "candidate_C11_minus_xgb_C11": (
                c11_pooled - xgb_reference["C11_pooled"]
            ),
            "xgb_gap": xgb_gap,
            "current_mlp_xgb_gap": current_xgb_gap,
            "fold_candidate_C11_minus_mlp_C11": [
                item["delta_C11_minus_mlp_C11"] for item in fold_results
            ],
            "fold_candidate_C11_minus_xgb_C11": [
                item["delta_C11_minus_xgb_C11"] for item in fold_results
            ],
        },
        "p_grid_diagnostic": {
            "participates_in_main_verdict": False,
            "values": grid_results,
        },
        "mechanical_verdict": {
            "qualification_status": qualification_status,
            "source_qualified": source_qualified,
            "source_rejected": not source_qualified,
            "invalid": False,
            "criteria": {
                "candidate_C11_gt_xgb_C11": (
                    c11_pooled > xgb_reference["C11_pooled"]
                ),
                "candidate_C11_gt_candidate_C00": c11_pooled > c00_pooled,
                "all_fold_C11_minus_C00_gt_zero": all_fold_mechanism_positive,
                "folds_candidate_C11_gt_xgb_C11": folds_above_xgb,
                "at_least_two_folds_candidate_C11_gt_xgb_C11": folds_above_xgb >= 2,
                "all_contract_receipts_valid": True,
            },
            "depth_signal": {
                "depth_gain_gt_zero": depth_gain > 0,
                "all_fold_C11_minus_C00_gt_zero": all_fold_mechanism_positive,
                "xgb_gap_lt_current_mlp_xgb_gap": xgb_gap < current_xgb_gap,
                "has_depth_signal": depth_signal,
                "verdict": depth_verdict,
            },
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "fold_membership_persisted": False,
            "selected_checkpoints": 6,
        },
        "resource": {
            "adaptive_parallelism": True,
            "maximum_parallel_training_units": config["resource_contract"][
                "maximum_parallel_training_units"
            ],
            "actual_parallelism": args.actual_parallelism,
            "launcher_receipt": resource_receipt,
            "aggregate_process_final": resource_snapshot(),
            "aggregate_process_seconds": time.time() - T0,
            "parameter_count": config["candidate"]["parameter_count"],
            "optimizer_steps": total_optimizer_steps,
            "sequences_per_step": config["training"]["batch_size"],
            "encoded_sequences": total_encoded_sequences,
            "encoded_effective_flows": total_effective_flows,
            "training_seconds_sum_across_units": total_training_seconds,
            "selection_inference_seconds_sum_across_units": (
                total_selection_inference_seconds
            ),
            "aggregate_inference_seconds": total_aggregate_inference_seconds,
            "gpu_hours_from_unit_training_seconds": total_training_seconds / 3600.0,
            "no_claim_parallel_is_faster_without_receipt": True,
        },
    }
    atomic_json(output_root / "fold-results.json", {"folds": fold_results})
    atomic_json(output_root / "aggregate-results.json", result)
    atomic_json(
        output_root / "resume-receipt.json",
        {
            "schema_version": "ch3-neural-backbone-source-oof-resume-receipt-v1",
            "resume_requested": args.resume,
            "source_data_sha256": input_identity["combined_sha256"],
            "fold_assignment_sha256": fold_sha,
            "units": resume_events,
            "counts": {
                "trained": sum(event["action"] == "trained" for event in resume_events),
                "reused": sum(event["action"] == "reused" for event in resume_events),
            },
        },
    )
    write_status(output_root, "computed", "aggregate-pending", 0, "六个训练单元与机械裁决已完成")
    build_manifest(output_root, config["run_id"])
    log(
        f"计算完成：C00={c00_pooled:.8f} C11={c11_pooled:.8f} "
        f"qualification={qualification_status} depth={depth_verdict}"
    )


def is_swanlab_init_401(error: BaseException) -> bool:
    messages: list[str] = []
    current: BaseException | None = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        messages.append(f"{type(current).__name__}: {current}")
        current = current.__cause__ or current.__context__
    message = "\n".join(messages).lower()
    return "401" in message and ("unauthorized" in message or "/api/projects/" in message)


def validate_tracking_gate(output_root: Path, attempt: int) -> None:
    gate = output_root / "tracking-gates" / "aggregate" / f"attempt-{attempt}"
    required = (
        gate / "swanlab-ping.exit-code.txt",
        gate / "swanlab-verify.exit-code.txt",
        gate / "swanlab-ping.log",
        gate / "swanlab-verify.log",
    )
    if not all(path.is_file() for path in required):
        raise RuntimeError("SwanLab 聚合运行初始化前门禁收据不完整")
    codes = [int(required[index].read_text(encoding="utf-8").strip()) for index in (0, 1)]
    if codes != [0, 0]:
        raise RuntimeError(f"SwanLab ping/verify 门失败：{codes}")


def publish_aggregate(config: dict[str, Any], args: argparse.Namespace) -> None:
    validate_destination(config, args)
    output_root = Path(config["paths"]["output_root"])
    result_path = output_root / "aggregate-results.json"
    if not result_path.is_file():
        raise RuntimeError("聚合结果不存在，禁止创建 SwanLab 运行")
    result = load_json(result_path)
    if result["input"]["arrays"] != list(ALLOWED_ARRAYS) or result["input"]["target_year_arrays_read"] != 0:
        raise RuntimeError("聚合结果不能证明源年隔离")
    validate_tracking_gate(output_root, args.tracking_attempt)
    import swanlab

    destination = config["swanlab"]
    try:
        swanlab.init(
            workspace=args.authorized_swanlab_workspace,
            project=args.authorized_swanlab_project,
            name=config["run_id"],
            mode=destination["mode"],
            group=destination["group"],
            tags=[*destination["tags"], "aggregate-only"],
            log_dir=str(output_root / "swanlog" / "aggregate" / f"attempt-{args.tracking_attempt}"),
            config={
                "run_id": config["run_id"],
                "seed": config["training"]["seed"],
                "fits": 6,
                "folds": 3,
                "screening_only": True,
                "formal_paper_evidence": False,
                "aggregate_only": True,
            },
        )
    except Exception as error:
        retryable = is_swanlab_init_401(error) and args.tracking_attempt == 1
        atomic_json(
            output_root / "tracking-attempts" / f"attempt-{args.tracking_attempt}-failure.json",
            {
                "error_type": type(error).__name__,
                "error": str(error)[:1000],
                "http_401_unauthorized": is_swanlab_init_401(error),
                "bounded_retry_allowed": retryable,
                "requires_new_process": True,
            },
        )
        raise SystemExit(81 if retryable else 82) from error
    pooled = result["pooled_oof"]
    metrics: dict[str, float] = {
        "source_oof/C00_entity_ap": pooled["C00_entity_ap"],
        "source_oof/C11_entity_ap": pooled["C11_entity_ap"],
        "source_oof/delta_C11_minus_C00": pooled["delta_C11_minus_C00"],
        "source_oof/fold_delta_range": pooled["fold_delta_range"],
        "source_oof/C11_minus_mlp_C11": result["comparisons"][
            "candidate_C11_minus_mlp_C11"
        ],
        "source_oof/C11_minus_xgb_C11": result["comparisons"][
            "candidate_C11_minus_xgb_C11"
        ],
        "source_oof/source_qualified": float(
            result["mechanical_verdict"]["source_qualified"]
        ),
        "runtime/total_seconds": result["resource"]["launcher_receipt"][
            "overall_wall_seconds_through_aggregate"
        ],
    }
    for fold in result["folds"]:
        index = fold["fold"]
        metrics[f"fold{index}/C00_entity_ap"] = fold["C00_entity_ap"]
        metrics[f"fold{index}/C11_entity_ap"] = fold["C11_entity_ap"]
        metrics[f"fold{index}/delta"] = fold["delta_C11_minus_C00"]
        metrics[f"fold{index}/C11_learned_p"] = fold["C11_learned_p"]
    for point in result["p_grid_diagnostic"]["values"]:
        metrics[f"p_grid/p_{point['p']:g}_entity_ap"] = point["pooled_oof_entity_ap"]
    swanlab.log(metrics, step=0)
    swanlab.finish()
    atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-neural-backbone-source-oof-swanlab-receipt-v1",
            "completed": True,
            "aggregate_only": True,
            "attempt": args.tracking_attempt,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "metric_count": len(metrics),
            "per_sample_values_uploaded": False,
        },
    )
    write_status(output_root, "complete", "finished", 0, "计算与聚合上报完成")
    build_manifest(output_root, config["run_id"])
    log("SwanLab 聚合指标上传完成")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    validate_config(config)
    if args.validate_config:
        print("配置核验通过")
        return 0
    try:
        if args.phase == "prepare":
            prepare(config, args, config_path)
        elif args.phase == "train-unit":
            train_unit(config, args, config_path)
        elif args.phase == "aggregate":
            aggregate(config, args, config_path)
        else:
            publish_aggregate(config, args)
    except SystemExit:
        raise
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        detail = f"{type(error).__name__}: {error}"[:1000]
        if args.phase == "train-unit" and args.cell is not None and args.fold is not None:
            write_unit_status(
                output_root,
                args.cell,
                args.fold,
                "failed",
                args.phase,
                1,
                detail,
                resource=(
                    resource_snapshot()
                    if torch is not None and torch.cuda.is_available()
                    else {}
                ),
            )
        else:
            write_status(output_root, "failed", args.phase, 1, detail)
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
