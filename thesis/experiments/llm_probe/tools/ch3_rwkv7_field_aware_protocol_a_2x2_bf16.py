"""固定 R2 与已封印容量的 RWKV-7 Protocol A 统一 BF16 重训入口。

旧 FP32 运行只提供架构选择收据。本入口不复用旧模型、优化器、轮次选择或
目标结果，也不重新比较输入适配器和容量候选。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
import traceback
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

import ch3_rwkv7_field_aware_protocol_a_2x2 as legacy
from neural_precision_runtime import (
    DEFAULT_PROFILE_ID,
    autocast_context,
    build_checkpoint_runtime_state,
    collect_resource_receipt,
    create_grad_scaler,
    fp32_island,
    load_and_validate_contract,
    validate_checkpoint_runtime_state,
    validate_microbatch_plan,
    validate_model_optimizer_fp32,
    validate_runtime_profile,
)


SCHEMA_VERSION = "ch3-rwkv7-fixed-architecture-protocol-a-bf16-config-v1"
RESULT_SCHEMA_VERSION = "ch3-rwkv7-fixed-architecture-protocol-a-bf16-results-v1"
RUN_ID = "ch3-rwkv7-field-aware-protocol-a-2x2-seed42-v1-bf16-v1"
SOURCE_RUN_ID = "ch3-rwkv7-field-aware-protocol-a-2x2-seed42-v1-rerun1"
SOURCE_ARRAYS = legacy.SOURCE_ARRAYS
TARGET_ARRAYS = legacy.TARGET_ARRAYS
CELL_ORDER = legacy.CELL_ORDER
DR_FPR_GRID = legacy.DR_FPR_GRID
R2_PARAMETER_COUNTS = {"K0": 104_274, "K1": 5_458_754, "K2": 9_490_178}
CAPACITY_SHAPES = {
    "K0": (112, 16, 8, 1, "legacy_single_time_mix"),
    "K1": (576, 64, 32, 3, "preln_value_residual_time_mix_stack"),
    "K2": (768, 64, 32, 3, "preln_value_residual_time_mix_stack"),
}
T0 = time.time()


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def load_json(path: Path) -> dict[str, Any]:
    return legacy.load_json(path)


def atomic_json(path: Path, value: Any) -> None:
    legacy.atomic_json(path, value)


def sha256_file(path: Path) -> str:
    return legacy.sha256_file(path)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(__file__).resolve().parents[1] / path


def expected_cells() -> dict[str, dict[str, bool]]:
    return legacy.expected_cells()


def validate_config(config: Mapping[str, Any], require_resolved: bool) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("BF16 配置模式或运行身份不符")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("源年数组白名单不符")
    if config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("目标年数组白名单不符")
    if config.get("cells") != expected_cells():
        raise ValueError("Protocol A 四格不符")
    if config.get("target_year_arrays_read_before_source_cells_frozen") != 0:
        raise ValueError("源年四格封印前目标数组读取计数必须为零")

    architecture = config.get("architecture_selection", {})
    if (
        architecture.get("source_run_id") != SOURCE_RUN_ID
        or architecture.get("source_precision") != "float32"
        or architecture.get("required_adapter") != "R2"
        or architecture.get("selected_adapter") != "R2"
        or architecture.get("precision_changed_after_architecture_selection") is not True
        or architecture.get("bf16_architecture_search_repeated") is not False
        or architecture.get("target_metrics_allowed_for_architecture_resolution") is not False
    ):
        raise ValueError("旧 FP32 架构选择来源或固定 R2 合同不符")
    selected_capacity = architecture.get("selected_capacity")
    receipt_sha = architecture.get("capacity_receipt_sha256")
    if require_resolved:
        if selected_capacity not in CAPACITY_SHAPES:
            raise ValueError("容量选择尚未由旧 FP32 收据封印")
        if not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
            raise ValueError("旧 FP32 容量收据摘要尚未注入")
    elif selected_capacity is not None or receipt_sha is not None:
        if selected_capacity not in CAPACITY_SHAPES or not isinstance(receipt_sha, str):
            raise ValueError("模板中的部分架构注入状态非法")

    precision = config.get("precision", {})
    if precision != {
        "contract_path": "configs/neural-precision-profiles-v1.json",
        "profile_id": DEFAULT_PROFILE_ID,
        "parameter_dtype": "float32",
        "optimizer_state_dtype": "float32",
        "scaler": None,
        "activation_checkpointing": False,
    }:
        raise ValueError("统一 BF16 精度配置不符")
    contract = load_and_validate_contract(resolve_project_path(precision["contract_path"]))
    if contract["default_profile"] != DEFAULT_PROFILE_ID:
        raise ValueError("共享精度合同默认配置不符")

    training = config.get("training", {})
    expected_training = {
        "seed": 42,
        "effective_batch_sequences": 64,
        "microbatch_sequences": 8,
        "accumulation_steps": 8,
        "flow_normalization_unit": "flow",
        "auxiliary_normalization_unit": "sequence",
        "epochs": 20,
        "steps_per_epoch": 1000,
        "learning_rate": 0.002,
        "w0_learning_rate_scale": 2.0,
        "weight_decay": 0.01,
        "gradient_clip_norm": 1.0,
        "auxiliary_loss_weight": 1.0,
        "dropout": 0.1,
        "validation_fraction": 0.1,
        "time_tail_fraction": 0.15,
        "actual_parallelism": 1,
        "checkpoint_interval_optimizer_steps": 20,
        "precision_profile_id": DEFAULT_PROFILE_ID,
    }
    if training != expected_training:
        raise ValueError("训练、微批或双归一合同不符")
    validate_microbatch_plan(
        effective_batch_items=training["effective_batch_sequences"],
        microbatch_items=training["microbatch_sequences"],
        accumulation_steps=training["accumulation_steps"],
        normalization_unit="flow",
        is_tail_batch=False,
    )
    validate_microbatch_plan(
        effective_batch_items=training["effective_batch_sequences"],
        microbatch_items=training["microbatch_sequences"],
        accumulation_steps=training["accumulation_steps"],
        normalization_unit="sequence",
        is_tail_batch=False,
    )
    if any("maximum" in key and "hour" in key for key in training):
        raise ValueError("BF16 重训不得包含人为训练时长上限")

    capacities = config.get("capacities", {})
    if list(capacities) != list(CAPACITY_SHAPES):
        raise ValueError("容量定义集合或顺序不符")
    for key, expected in CAPACITY_SHAPES.items():
        capacity = capacities[key]
        actual = (
            capacity.get("hidden_size"),
            capacity.get("head_size"),
            capacity.get("lora_size"),
            capacity.get("time_mix_layers"),
            capacity.get("structure"),
        )
        if actual != expected or capacity.get("r2_parameter_count") != R2_PARAMETER_COUNTS[key]:
            raise ValueError(f"{key} 结构或 R2 参数量台账不符")
    if config.get("resource_contract", {}).get("wall_clock_limit", "missing") is not None:
        raise ValueError("资源合同不得设置墙钟上限")
    evaluation = config.get("evaluation", {})
    if (
        evaluation.get("selection_rule") != "maximum_validation_flow_ap_then_earliest_epoch"
        or evaluation.get("target_evaluation_calls") != 4
        or evaluation.get("dr_fpr_grid") != list(DR_FPR_GRID)
        or evaluation.get("target_load_after_all_source_cells_sealed") is not True
    ):
        raise ValueError("评价或最早最佳轮选择合同不符")
    first_alert = config.get("first_alert_contract", {})
    if first_alert != {
        "budgets": list(DR_FPR_GRID),
        "threshold_semantics": "same_complete_tied_score_group_greater_equal",
        "online_entity_score": {
            "maximum_pool_cells": ["C00", "C10"],
            "prefix_lp_mean_cells": ["C01", "C11"],
        },
        "axis": "exposure_index",
        "curve_encoding": "right_continuous_exact_breakpoints",
        "quantiles": [0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0],
        "denominator": "all_positive_entities_in_evaluation_pool",
        "time_delay_available": False,
        "time_delay_unavailable_reason": (
            "现有T23与t24是mTimestampStart而非完整流available_ns，"
            "禁止猜测时间单位或合法可观测时刻"
        ),
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_per_entity_first_alert": False,
    }:
        raise ValueError("首次告警曝光序号、并列阈值或非持久化合同不符")
    if require_resolved:
        model = build_model(config, selected_capacity, "C00", DEFAULT_PROFILE_ID)
        del model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="固定 R2 与 FP32 封印容量的 RWKV-7 Protocol A 统一 BF16 重训"
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--require-resolved", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--resource-receipt")
    parser.add_argument("--publish-only", action="store_true")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser.parse_args()


class BF16RWKV7TimeMix(legacy.RWKV7TimeMix):
    """线性投影走 autocast，递归、衰减、归一化与归约固定为 FP32。"""

    def forward(
        self, values: torch.Tensor, value_first: torch.Tensor | None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        batch, length, channels = values.shape
        shifted = self.time_shift(values) - values
        xr = values + shifted * self.x_r
        xw = values + shifted * self.x_w
        xk = values + shifted * self.x_k
        xv = values + shifted * self.x_v
        xa = values + shifted * self.x_a
        xg = values + shifted * self.x_g
        r = self.receptance(xr)
        k = self.key(xk)
        v = self.value(xv)
        if self.layer_id == 0:
            value_first = v
        else:
            if value_first is None:
                raise RuntimeError("多层 RWKV-7 缺少首层 value residual")
            v = v + (value_first - v) * torch.sigmoid(
                self.v0 + (xv @ self.v1) @ self.v2
            )
        a = torch.sigmoid(self.a0 + (xa @ self.a1) @ self.a2)
        g = torch.sigmoid(xg @ self.g1) @ self.g2
        with fp32_island(xw, device_type="cuda", torch_module=torch) as (xw32,):
            w = -F.softplus(
                -(self.w0 + torch.tanh(xw32 @ self.w1) @ self.w2)
            ) - 0.5
        with fp32_island(k, a, device_type="cuda", torch_module=torch) as (k32, a32):
            kk = F.normalize(
                (k32 * self.k_k).view(batch, length, self.heads, -1),
                dim=-1,
                p=2.0,
            ).view(batch, length, channels)
            recurrent_k = k32 * (1 + (a32 - 1) * self.k_a)
        with fp32_island(
            r, w, recurrent_k, v, a, kk, device_type="cuda", torch_module=torch
        ) as (r32, w32, k32, v32, a32, kk32):
            output = legacy.rwkv7_op(
                r32, w32, k32, v32, -kk32, kk32 * a32, self.head_size
            )
            output = self.ln_x(output.view(batch * length, channels)).view(
                batch, length, channels
            )
            bonus = (
                (
                    r32.view(batch, length, self.heads, -1)
                    * k32.view(batch, length, self.heads, -1)
                    * self.r_k
                ).sum(dim=-1, keepdim=True)
                * v32.view(batch, length, self.heads, -1)
            ).view(batch, length, channels)
        return self.output((output + bonus) * g), value_first


class BF16RWKV7TimeMixLayer(nn.Module):
    def __init__(
        self,
        channels: int,
        head_size: int,
        lora_size: int,
        layer_id: int,
        layer_count: int,
        residual: bool,
    ) -> None:
        super().__init__()
        self.residual = residual
        self.normalization = nn.LayerNorm(channels) if residual else nn.Identity()
        self.time_mix = BF16RWKV7TimeMix(
            channels, head_size, lora_size, layer_id, layer_count
        )

    def forward(
        self, values: torch.Tensor, value_first: torch.Tensor | None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.residual:
            with fp32_island(values, device_type="cuda", torch_module=torch) as (values32,):
                normalized = self.normalization(values32)
        else:
            normalized = values
        update, value_first = self.time_mix(normalized, value_first)
        return (values + update if self.residual else update), value_first


class BF16RWKV7ProtocolAModel(nn.Module):
    def __init__(
        self,
        capacity_key: str,
        capacity: Mapping[str, Any],
        aggregate: bool,
        learned_lp: bool,
        dropout: float,
        precision_profile_id: str,
    ) -> None:
        super().__init__()
        self.adapter_key = "R2"
        self.capacity_key = capacity_key
        self.aggregate = aggregate
        self.learned_lp = learned_lp
        self.precision_profile_id = precision_profile_id
        hidden_size = int(capacity["hidden_size"])
        layer_count = int(capacity["time_mix_layers"])
        residual = capacity["structure"] == "preln_value_residual_time_mix_stack"
        self.time_mix_layers = nn.ModuleList(
            BF16RWKV7TimeMixLayer(
                hidden_size,
                int(capacity["head_size"]),
                int(capacity["lora_size"]),
                layer_id,
                layer_count,
                residual,
            )
            for layer_id in range(layer_count)
        )
        self.fusion_layer = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.output_layer = nn.Linear(hidden_size, 1)
        self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))
        self.input_adapter = legacy.MatchedProjectionInputAdapter(hidden_size)

    @property
    def p(self) -> torch.Tensor:
        with fp32_island(self.p_log, device_type="cuda", torch_module=torch) as (p_log32,):
            return torch.exp(p_log32).clamp(1e-3, 1e3)

    def forward(self, values: torch.Tensor, valid: torch.Tensor) -> torch.Tensor:
        if self.precision_profile_id != DEFAULT_PROFILE_ID:
            raise RuntimeError("RWKV 模型未绑定统一 CUDA BF16 精度配置")
        if not values.is_floating_point() or valid.dtype != torch.bool:
            raise RuntimeError("RWKV 输入值必须为浮点张量且掩码必须为布尔张量")
        mask = valid.float()
        hidden = self.input_adapter(values * mask.unsqueeze(-1))
        value_first = None
        for layer in self.time_mix_layers:
            hidden, value_first = layer(hidden * mask.unsqueeze(-1), value_first)
            hidden = hidden * mask.unsqueeze(-1)
        if self.aggregate:
            with fp32_island(hidden, mask, device_type="cuda", torch_module=torch) as (
                hidden32,
                mask32,
            ):
                count = torch.cumsum(mask32, dim=1).clamp(min=1.0).unsqueeze(-1)
                context = torch.cumsum(hidden32, dim=1) / count
                context = context * mask32.unsqueeze(-1)
        else:
            context = torch.zeros_like(hidden)
        fused = self.fusion_layer(torch.cat((hidden, context), dim=-1))
        fused = fused * mask.unsqueeze(-1)
        return self.output_layer(fused).squeeze(-1)


def build_model(
    config: Mapping[str, Any],
    capacity_key: str,
    cell: str,
    profile_id: str,
) -> BF16RWKV7ProtocolAModel:
    if capacity_key not in CAPACITY_SHAPES:
        raise ValueError(f"未知已封印容量：{capacity_key}")
    cell_config = config["cells"][cell]
    model = BF16RWKV7ProtocolAModel(
        capacity_key,
        config["capacities"][capacity_key],
        cell_config["causal_prefix_aggregation"],
        cell_config["learned_lp_pooling"],
        config["training"]["dropout"],
        profile_id,
    )
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != R2_PARAMETER_COUNTS[capacity_key]:
        raise RuntimeError(
            f"{capacity_key}/R2 参数量不符：实际 {actual}，冻结 {R2_PARAMETER_COUNTS[capacity_key]}"
        )
    return model


def make_optimizer(
    config: Mapping[str, Any], model: nn.Module
) -> tuple[torch.optim.Optimizer, list[dict[str, Any]]]:
    return legacy.make_optimizer(config, model)


def lp_pool_fp32(
    probabilities: torch.Tensor, valid: torch.Tensor, p: torch.Tensor
) -> torch.Tensor:
    with fp32_island(
        probabilities, p, device_type="cuda", torch_module=torch
    ) as (probabilities32, p32):
        logs = torch.log(probabilities32.clamp(min=1e-7))
        count = valid.float().sum(1).clamp(min=1.0)
        powered = (p32 * logs).masked_fill(~valid, -1e30)
        return torch.exp((torch.logsumexp(powered, 1) - torch.log(count)) / p32)


def predict_source_rows(
    model: BF16RWKV7ProtocolAModel,
    source: Mapping[str, np.ndarray],
    rows: np.ndarray,
    device: torch.device,
    batch_size: int,
    profile: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    model.eval()
    predictions: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    entities: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(rows), batch_size):
            selected_rows = rows[start : start + batch_size]
            values, valid, targets, _ = legacy.gather_sequence_batch(
                source, "23", selected_rows, device
            )
            with autocast_context(profile, device.type, torch):
                logits = model(values, valid)
            with fp32_island(logits, device_type=device.type, torch_module=torch) as (
                logits32,
            ):
                probabilities = torch.sigmoid(logits32)
            flat_valid = valid.reshape(-1)
            predictions.append(probabilities.reshape(-1)[flat_valid].cpu().numpy())
            labels.append(targets.reshape(-1)[flat_valid].cpu().numpy())
            repeated_entities = np.repeat(
                np.asarray(source["E23"][selected_rows]), valid.shape[1]
            )
            entities.append(repeated_entities[flat_valid.cpu().numpy()])
    model.train()
    return (
        np.concatenate(predictions),
        np.concatenate(labels),
        np.concatenate(entities),
    )


def score_target(
    config: Mapping[str, Any],
    model: BF16RWKV7ProtocolAModel,
    target: Mapping[str, np.ndarray],
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    scores = np.zeros(len(target["y24"]), dtype=np.float32)
    seen = np.zeros(len(target["y24"]), dtype=bool)
    batch_size = int(config["evaluation"]["sequence_batch_size"])
    contract = load_and_validate_contract(
        resolve_project_path(config["precision"]["contract_path"])
    )
    profile = validate_runtime_profile(
        contract, config["precision"]["profile_id"], device.type, torch
    )
    model.eval()
    with torch.no_grad():
        for start in range(0, len(target["I24"]), batch_size):
            rows = np.arange(start, min(start + batch_size, len(target["I24"])))
            values, valid, _, indices = legacy.gather_sequence_batch(
                target, "24", rows, device
            )
            with autocast_context(profile, device.type, torch):
                logits = model(values, valid)
            with fp32_island(logits, device_type=device.type, torch_module=torch) as (
                logits32,
            ):
                probabilities = torch.sigmoid(logits32).cpu().numpy()
            valid_np = valid.cpu().numpy()
            scores[indices[valid_np]] = probabilities[valid_np]
            seen[indices[valid_np]] = True
    return scores, seen


def effective_batch_denominators(
    source: Mapping[str, np.ndarray],
    rows: np.ndarray,
    sequence_positive_weight: float,
) -> tuple[int, float]:
    indices = np.asarray(source["I23"][rows], dtype=np.int64)
    valid = np.asarray(source["M23"][rows] > 0.5, dtype=bool)
    labels = np.asarray(source["y23"][indices], dtype=np.float32)
    valid_flow_count = int(valid.sum())
    sequence_labels = (labels * valid).max(1)
    sequence_weights = 1.0 + (sequence_positive_weight - 1.0) * sequence_labels
    total_sequence_weight = float(sequence_weights.sum(dtype=np.float64))
    if valid_flow_count <= 0 or not math.isfinite(total_sequence_weight) or total_sequence_weight <= 0:
        raise RuntimeError("有效批的流或加权序列归一化分母非法")
    return valid_flow_count, total_sequence_weight


def checkpoint_runtime_states(
    config: Mapping[str, Any],
    profile: Mapping[str, Any],
    scaler: Any | None,
    optimizer_step: int,
    uses_lp: bool,
) -> dict[str, Any]:
    training = config["training"]
    common = {
        "profile_id": config["precision"]["profile_id"],
        "profile": profile,
        "scaler": scaler,
        "effective_batch_items": int(training["effective_batch_sequences"]),
        "effective_batch_item_unit": "sequence",
        "microbatch_items": int(training["microbatch_sequences"]),
        "accumulation_steps": int(training["accumulation_steps"]),
        "is_tail_batch": False,
        "optimizer_step": optimizer_step,
        "optimizer_step_boundary": True,
        "torch_module": torch,
    }
    states = {
        "flow": build_checkpoint_runtime_state(
            normalization_unit="flow",
            **common,
        )
    }
    if uses_lp:
        states["sequence"] = build_checkpoint_runtime_state(
            normalization_unit="sequence",
            **common,
        )
    return states


def validate_precision_checkpoint(
    checkpoint: Mapping[str, Any], config: Mapping[str, Any], uses_lp: bool
) -> None:
    states = checkpoint.get("precision_runtime")
    expected_keys = {"flow", "sequence"} if uses_lp else {"flow"}
    if not isinstance(states, dict) or set(states) != expected_keys:
        raise RuntimeError("检查点缺少分离的流/序列精度运行时状态")
    for state in states.values():
        validate_checkpoint_runtime_state(state)
        if (
            state["precision_profile_id"] != config["precision"]["profile_id"]
            or state["scaler_state_dict"] is not None
            or state["optimizer_step_boundary"] is not True
        ):
            raise RuntimeError("检查点精度配置、缩放器或优化步边界不符")
    if checkpoint.get("scaler") is not None:
        raise RuntimeError("BF16 检查点不得包含 GradScaler")


def checkpoint_payload(
    *,
    config: Mapping[str, Any],
    profile: Mapping[str, Any],
    scaler: Any | None,
    identity: Mapping[str, Any],
    epoch: int,
    step: int,
    complete_epoch: bool,
    completed: bool,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    history: list[dict[str, Any]],
    best_ap: float,
    best_epoch: int,
    best_p: float,
    best_state: Mapping[str, torch.Tensor] | None,
    gradient_gate: Mapping[str, Any] | None,
    generator: torch.Generator,
    elapsed_seconds: float,
    running_loss: float,
    epoch_seconds: float,
    processed_valid_flows: int,
    uses_lp: bool,
) -> dict[str, Any]:
    optimizer_step = (epoch - 1) * int(config["training"]["steps_per_epoch"]) + step
    return {
        "schema_version": "ch3-rwkv7-bf16-complete-inflight-v1",
        "identity": dict(identity),
        "epoch": epoch,
        "step": step,
        "optimizer_step": optimizer_step,
        "complete_step": True,
        "complete_epoch": complete_epoch,
        "completed": completed,
        "model": {
            name: tensor.detach().cpu().clone()
            for name, tensor in model.state_dict().items()
        },
        "optimizer": optimizer.state_dict(),
        "scheduler_state": {"name": "none", "state": None},
        "precision_runtime": checkpoint_runtime_states(
            config, profile, scaler, optimizer_step, uses_lp
        ),
        "scaler": None,
        "history": history,
        "best_ap": best_ap,
        "best_epoch": best_epoch,
        "best_p": best_p,
        "best_state": best_state,
        "gradient_gate": gradient_gate,
        "elapsed_seconds": elapsed_seconds,
        "partial_running_loss": running_loss,
        "partial_epoch_seconds": epoch_seconds,
        "processed_valid_flows": processed_valid_flows,
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated() / 2**20,
        "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved() / 2**20,
        "peak_process_rss_mib": legacy.process_peak_rss_mib(),
        "generator_state": generator.get_state(),
        "torch_rng_state": torch.get_rng_state(),
        "cuda_rng_state_all": torch.cuda.get_rng_state_all(),
        "numpy_rng_state": np.random.get_state(),
        "python_rng_state": random.getstate(),
    }


def external_gpu_peak_mib(samples_path: Path) -> float:
    rows = samples_path.read_text(encoding="utf-8").splitlines()[1:]
    values = [float(row.split("\t")[1]) for row in rows if row.count("\t") == 2]
    if not values:
        raise RuntimeError("首个完整优化步缺少启动器外部显存采样")
    return max(values)


def write_first_step_resource_receipt(
    config: Mapping[str, Any],
    output_root: Path,
    cell: str,
    step_started: float,
    valid_flow_count: int,
    uses_lp: bool,
) -> None:
    path = (
        output_root
        / "receipts"
        / f"first-complete-optimizer-step-resource-{cell}.json"
    )
    if path.exists():
        return
    training = config["training"]
    common = {
        "profile_id": config["precision"]["profile_id"],
        "device_type": "cuda",
        "effective_batch_items": int(training["effective_batch_sequences"]),
        "microbatch_items": int(training["microbatch_sequences"]),
        "accumulation_steps": int(training["accumulation_steps"]),
        "elapsed_seconds": time.time() - step_started,
        "external_process_gpu_memory_mib": external_gpu_peak_mib(
            output_root / "resource-samples.tsv"
        ),
        "external_measurement_source": "launcher_nvidia_smi_5s_sampler",
        "torch_module": torch,
        "device": torch.device("cuda"),
    }
    receipts = {
        "flow": collect_resource_receipt(
            normalization_unit="flow",
            processed_valid_units=valid_flow_count,
            **common,
        )
    }
    if uses_lp:
        receipts["sequence"] = collect_resource_receipt(
            normalization_unit="sequence",
            processed_valid_units=int(training["effective_batch_sequences"]),
            **common,
        )
    atomic_json(
        path,
        {
            "schema_version": "ch3-rwkv7-bf16-first-optimizer-step-resource-v1",
            "receipts": receipts,
            "state_dtype": "float32",
            "scaler": None,
        },
    )


def strict_tied_budget_thresholds(
    entity_scores: np.ndarray,
    entity_labels: np.ndarray,
) -> dict[str, dict[str, float | int]]:
    """按完整负类并列分数组生成六档阈值，不截断同分实体。"""

    valid = np.isfinite(entity_scores)
    scores = np.asarray(entity_scores[valid], dtype=np.float64)
    labels = np.asarray(entity_labels[valid], dtype=np.float32)
    negative = np.sort(scores[labels == 0])[::-1]
    positive_count = int((labels == 1).sum())
    if len(negative) == 0 or positive_count == 0:
        raise RuntimeError("首次告警阈值缺少正类或负类实体")
    thresholds: dict[str, dict[str, float | int]] = {}
    for target_fpr in DR_FPR_GRID:
        key = f"fpr_{target_fpr:g}"
        threshold = float(
            negative[min(int(len(negative) * target_fpr), len(negative) - 1)]
        )
        false_positive_count = int((negative >= threshold).sum())
        thresholds[key] = {
            "target_fpr": float(target_fpr),
            "threshold": threshold,
            "negative_entity_count": int(len(negative)),
            "positive_entity_count": positive_count,
            "false_positive_entity_count": false_positive_count,
            "realized_fpr": false_positive_count / len(negative),
            "comparison": "score_greater_equal_threshold",
            "tied_group_kept_complete": True,
        }
    return thresholds


def _update_positive_entity_path(
    *,
    entity_code: int,
    scores: np.ndarray,
    positive_lookup: np.ndarray,
    exposure_count: np.ndarray,
    running_maximum: np.ndarray,
    running_power_sum: np.ndarray,
    first_alert_exposure: np.ndarray,
    thresholds: np.ndarray,
    p_value: float | None,
) -> None:
    positive_index = int(positive_lookup[entity_code])
    if positive_index < 0:
        return
    values = np.asarray(scores, dtype=np.float64)
    if not len(values) or not np.isfinite(values).all():
        raise RuntimeError("首次告警路径包含空分数或非有限分数")
    prior_count = int(exposure_count[positive_index])
    if p_value is None:
        online = np.maximum.accumulate(
            np.maximum(values, running_maximum[positive_index])
        )
        running_maximum[positive_index] = float(online[-1])
    else:
        powered = np.clip(values, 1e-7, 1.0) ** p_value
        cumulative = running_power_sum[positive_index] + np.cumsum(powered)
        counts = prior_count + np.arange(1, len(values) + 1, dtype=np.int64)
        online = (cumulative / counts) ** (1.0 / p_value)
        running_power_sum[positive_index] = float(cumulative[-1])
    for budget_index, threshold in enumerate(thresholds):
        if first_alert_exposure[budget_index, positive_index] != 0:
            continue
        crossing = np.flatnonzero(online >= threshold)
        if len(crossing):
            first_alert_exposure[budget_index, positive_index] = (
                prior_count + int(crossing[0]) + 1
            )
    exposure_count[positive_index] = prior_count + len(values)


def _first_alert_distribution(values: np.ndarray) -> dict[str, float | int | None]:
    if not len(values):
        return {
            "count": 0,
            "minimum": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p90": None,
            "p95": None,
            "p99": None,
            "maximum": None,
        }
    quantiles = np.quantile(
        values.astype(np.float64),
        [0.0, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 1.0],
    )
    names = ("minimum", "p25", "median", "p75", "p90", "p95", "p99", "maximum")
    return {"count": int(len(values)), **dict(zip(names, map(float, quantiles), strict=True))}


def _finalize_first_alert_aggregate(
    *,
    config: Mapping[str, Any],
    thresholds: Mapping[str, Mapping[str, float | int]],
    first_alert_exposure: np.ndarray,
    exposure_count: np.ndarray,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    positive_count = int(len(exposure_count))
    if positive_count == 0 or np.any(exposure_count <= 0):
        raise RuntimeError("首次告警聚合缺少恶意实体曝光路径")
    summaries: dict[str, Any] = {}
    curves: dict[str, np.ndarray] = {}
    for budget_index, (key, threshold_receipt) in enumerate(thresholds.items()):
        positions = first_alert_exposure[budget_index]
        alerted = positions > 0
        axis = np.unique(
            np.concatenate(
                (
                    np.array([0], dtype=np.int64),
                    positions[alerted],
                    np.array([int(exposure_count.max())], dtype=np.int64),
                )
            )
        )
        rate = np.array(
            [float(((positions > 0) & (positions <= point)).sum()) / positive_count for point in axis],
            dtype=np.float64,
        )
        summaries[key] = {
            "threshold": dict(threshold_receipt),
            "positive_entity_count": positive_count,
            "alerted_entity_count": int(alerted.sum()),
            "never_alerted_entity_count": int((~alerted).sum()),
            "unalerted_rate": float((~alerted).mean()),
            "first_alert_exposure_index": _first_alert_distribution(positions[alerted]),
            "maximum_positive_entity_exposure_count": int(exposure_count.max()),
            "curve_point_count": int(len(axis)),
        }
        curves[f"{key}__exposure_index"] = axis
        curves[f"{key}__timely_detection_rate"] = rate
    definition = (
        "从恶意实体第一条进入本评价池的合法序列流开始，以1基实体内曝光序号计数；"
        "在线实体分数按格使用运行最大值或前缀Lp均值，首次满足score>=同档完整并列阈值即告警；"
        "累计检出率分母始终为全部恶意实体，未告警实体保留为删失。"
        + config["first_alert_contract"]["time_delay_unavailable_reason"]
    )
    summary = {
        "definition": definition,
        "axis": config["first_alert_contract"]["axis"],
        "curve_encoding": config["first_alert_contract"]["curve_encoding"],
        "threshold_semantics": config["first_alert_contract"]["threshold_semantics"],
        "time_delay_available": False,
        "time_delay_unavailable_reason": config["first_alert_contract"][
            "time_delay_unavailable_reason"
        ],
        "positive_entity_count": positive_count,
        "unalerted_rate_at_fpr": {
            key: value["unalerted_rate"] for key, value in summaries.items()
        },
        "delay_summary_at_fpr": summaries,
        "first_alert_exposure_summary_at_fpr": summaries,
        "persisted_per_flow_scores": False,
        "persisted_per_entity_scores": False,
        "persisted_per_entity_first_alert": False,
    }
    return summary, curves


def source_first_alert_aggregate(
    *,
    config: Mapping[str, Any],
    source: Mapping[str, np.ndarray],
    validation_rows: np.ndarray,
    ordered_flow_scores: np.ndarray,
    ordered_flow_entity: np.ndarray,
    entity_labels: np.ndarray,
    entity_scores: np.ndarray,
    p_value: float | None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    thresholds = strict_tied_budget_thresholds(entity_scores, entity_labels)
    positive_entities = np.flatnonzero(entity_labels == 1)
    positive_lookup = np.full(len(entity_labels), -1, dtype=np.int32)
    positive_lookup[positive_entities] = np.arange(len(positive_entities), dtype=np.int32)
    exposure_count = np.zeros(len(positive_entities), dtype=np.int64)
    running_maximum = np.full(len(positive_entities), -np.inf, dtype=np.float64)
    running_power_sum = np.zeros(len(positive_entities), dtype=np.float64)
    first_alert_exposure = np.zeros(
        (len(DR_FPR_GRID), len(positive_entities)), dtype=np.int64
    )
    threshold_values = np.array(
        [float(receipt["threshold"]) for receipt in thresholds.values()],
        dtype=np.float64,
    )
    cursor = 0
    for row in validation_rows:
        valid = np.asarray(source["M23"][row] > 0.5, dtype=bool)
        count = int(valid.sum())
        scores = ordered_flow_scores[cursor : cursor + count]
        entities = ordered_flow_entity[cursor : cursor + count]
        cursor += count
        if count == 0 or not np.all(entities == entities[0]):
            raise RuntimeError("源年首次告警序列缺少流或跨越多个实体")
        _update_positive_entity_path(
            entity_code=int(entities[0]),
            scores=scores,
            positive_lookup=positive_lookup,
            exposure_count=exposure_count,
            running_maximum=running_maximum,
            running_power_sum=running_power_sum,
            first_alert_exposure=first_alert_exposure,
            thresholds=threshold_values,
            p_value=p_value,
        )
    if cursor != len(ordered_flow_scores):
        raise RuntimeError("源年首次告警路径未无重无漏消费验证分数")
    return _finalize_first_alert_aggregate(
        config=config,
        thresholds=thresholds,
        first_alert_exposure=first_alert_exposure,
        exposure_count=exposure_count,
    )


def target_first_alert_aggregate(
    *,
    config: Mapping[str, Any],
    target: Mapping[str, np.ndarray],
    flow_scores: np.ndarray,
    flow_entity: np.ndarray,
    entity_labels: np.ndarray,
    entity_scores: np.ndarray,
    p_value: float | None,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    thresholds = strict_tied_budget_thresholds(entity_scores, entity_labels)
    positive_entities = np.flatnonzero(entity_labels == 1)
    positive_lookup = np.full(len(entity_labels), -1, dtype=np.int32)
    positive_lookup[positive_entities] = np.arange(len(positive_entities), dtype=np.int32)
    exposure_count = np.zeros(len(positive_entities), dtype=np.int64)
    running_maximum = np.full(len(positive_entities), -np.inf, dtype=np.float64)
    running_power_sum = np.zeros(len(positive_entities), dtype=np.float64)
    first_alert_exposure = np.zeros(
        (len(DR_FPR_GRID), len(positive_entities)), dtype=np.int64
    )
    threshold_values = np.array(
        [float(receipt["threshold"]) for receipt in thresholds.values()],
        dtype=np.float64,
    )
    for row in range(len(target["I24"])):
        indices = np.asarray(target["I24"][row], dtype=np.int64)
        valid = np.asarray(target["M24"][row] > 0.5, dtype=bool)
        valid_indices = indices[valid]
        entities = flow_entity[valid_indices]
        if not len(valid_indices) or not np.all(entities == entities[0]):
            raise RuntimeError("目标年首次告警序列缺少流或跨越多个实体")
        _update_positive_entity_path(
            entity_code=int(entities[0]),
            scores=flow_scores[valid_indices],
            positive_lookup=positive_lookup,
            exposure_count=exposure_count,
            running_maximum=running_maximum,
            running_power_sum=running_power_sum,
            first_alert_exposure=first_alert_exposure,
            thresholds=threshold_values,
            p_value=p_value,
        )
    return _finalize_first_alert_aggregate(
        config=config,
        thresholds=thresholds,
        first_alert_exposure=first_alert_exposure,
        exposure_count=exposure_count,
    )


def save_npz_atomic(path: Path, vectors: Mapping[str, np.ndarray]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **vectors)
    os.replace(temporary, path)
    return {
        "filename": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "fields": list(vectors),
    }


def train_cell(
    config: Mapping[str, Any],
    cell: str,
    capacity_key: str,
    output_root: Path,
    run_identity: Mapping[str, Any],
    source: Mapping[str, np.ndarray],
    train_rows: np.ndarray,
    validation_rows: np.ndarray,
    loss_weights: tuple[float, float],
    device: torch.device,
    profile: Mapping[str, Any],
    resume: bool,
) -> dict[str, Any]:
    task_key = f"protocol-{cell}-{capacity_key}-R2-bf16"
    receipt_path = output_root / "receipts" / f"selection-{task_key}.json"
    inflight_path = output_root / "inflight" / f"{task_key}.pt"
    epoch_root = output_root / "checkpoints" / "epochs" / task_key
    identity = {
        "schema_version": "ch3-rwkv7-bf16-protocol-a-task-identity-v1",
        **run_identity,
        "task_key": task_key,
        "adapter_key": "R2",
        "capacity_key": capacity_key,
        "cell": cell,
        "precision_profile_id": config["precision"]["profile_id"],
    }
    if receipt_path.is_file():
        receipt = load_json(receipt_path)
        checkpoint_path = output_root / receipt["selection"]["checkpoint"]["filename"]
        valid = (
            checkpoint_path.is_file()
            and receipt.get("identity") == identity
            and receipt.get("selection", {}).get("checkpoint", {}).get("sha256")
            == sha256_file(checkpoint_path)
        )
        if not resume or not valid:
            raise RuntimeError(f"{task_key} 已有检查点但不可合法复用")
        return receipt["selection"]
    if not resume and (
        receipt_path.exists() or inflight_path.exists() or epoch_root.exists()
    ):
        raise RuntimeError(f"全新 BF16 运行存在 {task_key} 历史制品")

    training = config["training"]
    seed = int(training["seed"])
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    model = build_model(config, capacity_key, cell, config["precision"]["profile_id"]).to(
        device
    )
    optimizer, optimizer_groups = make_optimizer(config, model)
    scaler = create_grad_scaler(profile, torch)
    if scaler is not None:
        raise RuntimeError("统一 BF16 配置禁止创建 GradScaler")
    validate_model_optimizer_fp32(model, optimizer, torch)
    generator = torch.Generator().manual_seed(seed)
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_p = float("nan")
    best_state: dict[str, torch.Tensor] | None = None
    gradient_gate: dict[str, Any] | None = None
    elapsed_before = 0.0
    start_epoch = 1
    start_step = 1
    partial_running_loss = 0.0
    partial_epoch_seconds = 0.0
    processed_valid_flows = 0
    uses_lp = bool(config["cells"][cell]["learned_lp_pooling"])
    if resume and inflight_path.is_file():
        inflight = torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("identity") != identity or not inflight.get("complete_step"):
            raise RuntimeError(f"{task_key} 在途检查点不是最新完整优化步")
        validate_precision_checkpoint(inflight, config, uses_lp)
        model.load_state_dict(inflight["model"])
        optimizer.load_state_dict(inflight["optimizer"])
        legacy.move_optimizer_state(optimizer, device)
        validate_model_optimizer_fp32(model, optimizer, torch)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_p = float(inflight["best_p"])
        best_state = inflight["best_state"]
        gradient_gate = inflight["gradient_gate"]
        elapsed_before = float(inflight["elapsed_seconds"])
        generator.set_state(inflight["generator_state"])
        torch.set_rng_state(inflight["torch_rng_state"])
        torch.cuda.set_rng_state_all(inflight["cuda_rng_state_all"])
        np.random.set_state(inflight["numpy_rng_state"])
        random.setstate(inflight["python_rng_state"])
        processed_valid_flows = int(inflight["processed_valid_flows"])
        if inflight.get("complete_epoch"):
            start_epoch = int(inflight["epoch"]) + 1
        else:
            start_epoch = int(inflight["epoch"])
            start_step = int(inflight["step"]) + 1
            partial_running_loss = float(inflight["partial_running_loss"])
            partial_epoch_seconds = float(inflight["partial_epoch_seconds"])

    flow_positive_weight, sequence_positive_weight = loss_weights
    flow_pos_weight = torch.tensor(flow_positive_weight, device=device, dtype=torch.float32)
    microbatch_size = int(training["microbatch_sequences"])
    effective_batch_size = int(training["effective_batch_sequences"])
    torch.cuda.reset_peak_memory_stats(device)
    started = time.time()
    epoch_started = started
    for epoch in range(start_epoch, int(training["epochs"]) + 1):
        running_loss = partial_running_loss if epoch == start_epoch else 0.0
        step_first = start_step if epoch == start_epoch else 1
        model.train()
        for step in range(step_first, int(training["steps_per_epoch"]) + 1):
            step_started = time.time()
            positions = torch.randint(
                0,
                len(train_rows),
                (effective_batch_size,),
                generator=generator,
            ).numpy()
            rows = train_rows[positions]
            total_valid_flows, total_sequence_weight = effective_batch_denominators(
                source, rows, sequence_positive_weight
            )
            optimizer.zero_grad(set_to_none=True)
            effective_step_loss = 0.0
            for micro_start in range(0, effective_batch_size, microbatch_size):
                micro_rows = rows[micro_start : micro_start + microbatch_size]
                values, valid, labels, _ = legacy.gather_sequence_batch(
                    source, "23", micro_rows, device
                )
                with autocast_context(profile, device.type, torch):
                    logits = model(values, valid)
                with fp32_island(
                    logits, labels, device_type=device.type, torch_module=torch
                ) as (logits32, labels32):
                    mask32 = valid.float()
                    flow_loss_sum = (
                        F.binary_cross_entropy_with_logits(
                            logits32,
                            labels32,
                            pos_weight=flow_pos_weight,
                            reduction="none",
                        )
                        * mask32
                    ).sum()
                    micro_loss = flow_loss_sum / total_valid_flows
                    entity_component: torch.Tensor | None = None
                    if uses_lp:
                        probabilities32 = torch.sigmoid(logits32)
                        pooled = lp_pool_fp32(probabilities32, valid, model.p).clamp(
                            1e-6, 1 - 1e-6
                        )
                        sequence_labels = (labels32 * mask32).amax(-1)
                        sequence_weights = 1.0 + (
                            sequence_positive_weight - 1.0
                        ) * sequence_labels
                        sequence_loss_sum = (
                            F.binary_cross_entropy(
                                pooled,
                                sequence_labels,
                                reduction="none",
                            )
                            * sequence_weights
                        ).sum()
                        entity_component = float(training["auxiliary_loss_weight"]) * (
                            sequence_loss_sum / total_sequence_weight
                        )
                        micro_loss = micro_loss + entity_component
                if cell == "C11" and gradient_gate is None and micro_start == 0:
                    if entity_component is None:
                        raise RuntimeError("C11 缺少 ELP 实体辅助损失")
                    entity_component.backward(retain_graph=True)
                    current_gradient = legacy.gradient_receipt(model, require_elp=True)
                    if epoch == 1 and step == 1:
                        atomic_json(
                            output_root
                            / "receipts"
                            / f"gradient-first-step-entity-only-{task_key}.json",
                            {
                                "identity": identity,
                                "loss_scope": "ELP_entity_auxiliary_only",
                                "precision_profile_id": config["precision"]["profile_id"],
                                **current_gradient,
                            },
                        )
                    if current_gradient["all_required_groups_pass"]:
                        gradient_gate = {
                            "first_reachable_step": step,
                            "loss_scope": "ELP_entity_auxiliary_only",
                            **current_gradient,
                        }
                        atomic_json(
                            output_root / "receipts" / f"gradient-{task_key}.json",
                            {"identity": identity, **gradient_gate},
                        )
                    elif step >= 3:
                        raise RuntimeError(
                            f"{task_key} 三步内实体损失梯度门未通过：{current_gradient['groups']}"
                        )
                    optimizer.zero_grad(set_to_none=True)
                micro_loss.backward()
                effective_step_loss += float(micro_loss.detach())
            if gradient_gate is None and cell != "C11":
                current_gradient = legacy.gradient_receipt(model, require_elp=False)
                if epoch == 1 and step == 1:
                    atomic_json(
                        output_root / "receipts" / f"gradient-first-step-{task_key}.json",
                        {
                            "identity": identity,
                            "precision_profile_id": config["precision"]["profile_id"],
                            **current_gradient,
                        },
                    )
                if current_gradient["all_required_groups_pass"]:
                    gradient_gate = {"first_reachable_step": step, **current_gradient}
                    atomic_json(
                        output_root / "receipts" / f"gradient-{task_key}.json",
                        {"identity": identity, **gradient_gate},
                    )
                elif step >= 3:
                    raise RuntimeError(
                        f"{task_key} 三步内端到端梯度门未通过：{current_gradient['groups']}"
                    )
            gradient_norm = float(
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), float(training["gradient_clip_norm"])
                )
            )
            if not math.isfinite(gradient_norm):
                raise RuntimeError(f"{task_key} 出现非有限梯度")
            optimizer.step()
            validate_model_optimizer_fp32(model, optimizer, torch)
            running_loss += effective_step_loss
            processed_valid_flows += total_valid_flows
            if epoch == 1 and step == 1:
                write_first_step_resource_receipt(
                    config,
                    output_root,
                    cell,
                    step_started,
                    total_valid_flows,
                    uses_lp,
                )
            elapsed = elapsed_before + time.time() - started
            if step % int(training["checkpoint_interval_optimizer_steps"]) == 0:
                payload = checkpoint_payload(
                    config=config,
                    profile=profile,
                    scaler=scaler,
                    identity=identity,
                    epoch=epoch,
                    step=step,
                    complete_epoch=False,
                    completed=False,
                    model=model,
                    optimizer=optimizer,
                    history=history,
                    best_ap=best_ap,
                    best_epoch=best_epoch,
                    best_p=best_p,
                    best_state=best_state,
                    gradient_gate=gradient_gate,
                    generator=generator,
                    elapsed_seconds=elapsed,
                    running_loss=running_loss,
                    epoch_seconds=partial_epoch_seconds + time.time() - epoch_started,
                    processed_valid_flows=processed_valid_flows,
                    uses_lp=uses_lp,
                )
                legacy.atomic_torch(inflight_path, payload)
            if step % 250 == 0:
                log(
                    f"{task_key} epoch={epoch}/{training['epochs']} "
                    f"step={step}/{training['steps_per_epoch']} 累计={elapsed / 60:.1f}分"
                )

        predictions, labels_np, _ = predict_source_rows(
            model,
            source,
            validation_rows,
            device,
            int(config["evaluation"]["sequence_batch_size"]),
            profile,
        )
        validation_ap = float(legacy.average_precision_score(labels_np, predictions))
        p_value = float(model.p.detach())
        epoch_seconds = partial_epoch_seconds + time.time() - epoch_started
        epoch_started = time.time()
        partial_epoch_seconds = 0.0
        history.append(
            {
                "epoch": epoch,
                "validation_flow_ap": validation_ap,
                "p": p_value,
                "mean_training_loss": running_loss / int(training["steps_per_epoch"]),
                "epoch_seconds": epoch_seconds,
            }
        )
        current_state = {
            name: tensor.detach().cpu().clone()
            for name, tensor in model.state_dict().items()
        }
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_p = p_value
            best_state = current_state
        elapsed = elapsed_before + time.time() - started
        payload = checkpoint_payload(
            config=config,
            profile=profile,
            scaler=scaler,
            identity=identity,
            epoch=epoch,
            step=int(training["steps_per_epoch"]),
            complete_epoch=True,
            completed=epoch == int(training["epochs"]),
            model=model,
            optimizer=optimizer,
            history=history,
            best_ap=best_ap,
            best_epoch=best_epoch,
            best_p=best_p,
            best_state=best_state,
            gradient_gate=gradient_gate,
            generator=generator,
            elapsed_seconds=elapsed,
            running_loss=running_loss,
            epoch_seconds=epoch_seconds,
            processed_valid_flows=processed_valid_flows,
            uses_lp=uses_lp,
        )
        epoch_path = epoch_root / f"epoch-{epoch:02d}.pt"
        legacy.atomic_torch(epoch_path, payload)
        legacy.atomic_torch(inflight_path, payload)
        log(f"{task_key} epoch={epoch} 验证逐流AP={validation_ap:.8f}")

    if best_state is None or gradient_gate is None:
        raise RuntimeError(f"{task_key} 未产生可选检查点")
    training_seconds = elapsed_before + time.time() - started
    checkpoint_path = epoch_root / f"epoch-{best_epoch:02d}.pt"
    model.load_state_dict(best_state)
    validation_scores, validation_labels, validation_entities = predict_source_rows(
        model,
        source,
        validation_rows,
        device,
        int(config["evaluation"]["sequence_batch_size"]),
        profile,
    )
    _, validation_flow_entity = np.unique(validation_entities, return_inverse=True)
    validation_entity_labels = np.zeros(
        int(validation_flow_entity.max()) + 1, dtype=np.float32
    )
    np.maximum.at(
        validation_entity_labels, validation_flow_entity, validation_labels
    )
    validation_seen = np.ones(len(validation_scores), dtype=bool)
    main_p = best_p if uses_lp else None
    validation_entity_scores = legacy.entity_scores(
        validation_scores,
        validation_seen,
        validation_flow_entity,
        len(validation_entity_labels),
        main_p,
    )
    validation_maximum_scores = legacy.entity_scores(
        validation_scores,
        validation_seen,
        validation_flow_entity,
        len(validation_entity_labels),
        None,
    )
    validation_metrics = {
        "flow_average_precision": float(
            legacy.average_precision_score(validation_labels, validation_scores)
        ),
        "flow_roc_auc": float(
            legacy.roc_auc_score(validation_labels, validation_scores)
        ),
        "entity_average_precision": float(
            legacy.average_precision_score(
                validation_entity_labels, validation_entity_scores
            )
        ),
        "maximum_entity_average_precision": float(
            legacy.average_precision_score(
                validation_entity_labels, validation_maximum_scores
            )
        ),
        "dr_at_fpr": {
            f"fpr_{value:g}": legacy.dr_at_fpr(
                validation_entity_scores, validation_entity_labels, value
            )
            for value in DR_FPR_GRID
        },
        "maximum_dr_at_fpr": {
            f"fpr_{value:g}": legacy.dr_at_fpr(
                validation_maximum_scores, validation_entity_labels, value
            )
            for value in DR_FPR_GRID
        },
        "flow_count": len(validation_scores),
        "entity_count": len(validation_entity_labels),
    }
    if abs(validation_metrics["flow_average_precision"] - best_ap) > 1e-12:
        raise RuntimeError("选中轮复算逐流 AP 与选择历史不一致")
    first_alert_started = time.time()
    source_first_alert, source_first_alert_curves = source_first_alert_aggregate(
        config=config,
        source=source,
        validation_rows=validation_rows,
        ordered_flow_scores=validation_scores,
        ordered_flow_entity=validation_flow_entity,
        entity_labels=validation_entity_labels,
        entity_scores=validation_entity_scores,
        p_value=main_p,
    )
    source_first_alert["aggregation_seconds"] = time.time() - first_alert_started
    source_first_alert_path = (
        output_root / "receipts" / f"source-first-alert-{task_key}.npz"
    )
    source_first_alert_artifact = save_npz_atomic(
        source_first_alert_path, source_first_alert_curves
    )
    source_first_alert_artifact["filename"] = str(
        source_first_alert_path.relative_to(output_root)
    )
    source_first_alert["artifact"] = source_first_alert_artifact
    source_curve = legacy.complete_budget_curve(
        validation_entity_scores, validation_entity_labels
    )
    source_curve_path = output_root / "receipts" / f"source-budget-{task_key}.npz"
    source_curve_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_curve = source_curve_path.with_name(
        f"{source_curve_path.name}.partial.{os.getpid()}"
    )
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **source_curve)
    os.replace(temporary_curve, source_curve_path)
    selection = {
        "task_key": task_key,
        "adapter_key": "R2",
        "capacity_key": capacity_key,
        "cell": cell,
        "selected_epoch": best_epoch,
        "validation_flow_ap": best_ap,
        "p_at_selection": best_p,
        "history": history,
        "training_seconds": training_seconds,
        "processed_valid_flows": processed_valid_flows,
        "effective_training_flow_throughput_per_second": processed_valid_flows
        / training_seconds,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "optimizer_groups": optimizer_groups,
        "gradient_gate": gradient_gate,
        "precision_profile_id": config["precision"]["profile_id"],
        "scaler": None,
        "normalization_units": ["flow", "sequence"] if uses_lp else ["flow"],
        "selected_validation_metrics": validation_metrics,
        "source_first_alert": source_first_alert,
        "selected_validation_complete_budget_curve": {
            "filename": str(source_curve_path.relative_to(output_root)),
            "bytes": source_curve_path.stat().st_size,
            "sha256": sha256_file(source_curve_path),
        },
        "epoch_checkpoint_count": len(history),
        "latest_complete_inflight": str(inflight_path.relative_to(output_root)),
        "checkpoint": {
            "filename": str(checkpoint_path.relative_to(output_root)),
            "bytes": checkpoint_path.stat().st_size,
            "sha256": sha256_file(checkpoint_path),
        },
        "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
        "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
        "peak_process_rss_mib": legacy.process_peak_rss_mib(),
        "nonfinite_gradient_or_loss_count": 0,
    }
    atomic_json(receipt_path, {"identity": identity, "selection": selection})
    del model, optimizer
    torch.cuda.empty_cache()
    return selection


def save_target_evaluation(
    output_root: Path,
    cell: str,
    identity: Mapping[str, Any],
    cell_result: Mapping[str, Any],
    budget_curve: Mapping[str, np.ndarray],
    first_alert_curves: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if receipt_root.exists():
        raise RuntimeError(f"{cell} 目标评价完成目录已存在，拒绝覆盖")
    temporary_root = receipt_root.with_name(
        f"{receipt_root.name}.partial.{os.getpid()}"
    )
    temporary_root.mkdir(parents=True, exist_ok=False)
    budget_path = temporary_root / "complete-alert-budget-curve.npz"
    first_alert_path = temporary_root / "first-alert-exposure-curves.npz"
    budget_artifact = save_npz_atomic(budget_path, budget_curve)
    first_alert_artifact = save_npz_atomic(first_alert_path, first_alert_curves)
    final_result = dict(cell_result)
    final_result["first_alert"] = dict(cell_result["first_alert"])
    final_result["first_alert"]["artifact"] = {
        **first_alert_artifact,
        "filename": str(
            (receipt_root / first_alert_path.name).relative_to(output_root)
        ),
    }
    atomic_json(
        temporary_root / "receipt.json",
        {
            "schema_version": "ch3-rwkv7-bf16-target-cell-receipt-v1",
            "identity": dict(identity),
            "cell_result": final_result,
            "curve": {
                **budget_artifact,
                "filename": budget_path.name,
            },
            "first_alert_curve": {
                **first_alert_artifact,
                "filename": first_alert_path.name,
            },
            "complete": True,
        },
    )
    os.replace(temporary_root, receipt_root)
    return final_result


def load_target_evaluation(
    output_root: Path,
    cell: str,
    identity: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, np.ndarray]] | None:
    receipt_root = output_root / "receipts" / f"target-evaluation-{cell}"
    if not receipt_root.exists():
        return None
    receipt = load_json(receipt_root / "receipt.json")
    budget_path = receipt_root / receipt["curve"]["filename"]
    first_alert_path = receipt_root / receipt["first_alert_curve"]["filename"]
    if (
        receipt.get("schema_version") != "ch3-rwkv7-bf16-target-cell-receipt-v1"
        or receipt.get("identity") != identity
        or not receipt.get("complete")
        or sha256_file(budget_path) != receipt["curve"]["sha256"]
        or sha256_file(first_alert_path) != receipt["first_alert_curve"]["sha256"]
    ):
        raise RuntimeError(f"{cell} 目标评价完成收据身份或摘要不符")
    with np.load(budget_path) as payload:
        budget_curve = {name: payload[name] for name in payload.files}
    with np.load(first_alert_path) as payload:
        first_alert_curves = {name: payload[name] for name in payload.files}
    return receipt["cell_result"], budget_curve, first_alert_curves


def evaluate_target(
    config: Mapping[str, Any],
    output_root: Path,
    run_identity: Mapping[str, Any],
    selections: Mapping[str, Mapping[str, Any]],
    capacity_key: str,
    target_inventory: Mapping[str, Any],
    target: Mapping[str, np.ndarray],
) -> tuple[dict[str, Any], dict[str, np.ndarray], dict[str, int]]:
    flow_entity, entity_labels, entity_stats = legacy.build_target_entity_map(target)
    if entity_stats.get("unmapped_flow_count") != 0:
        raise RuntimeError("目标年实体映射未覆盖全部流，禁止首次告警聚合")
    device = torch.device("cuda")
    cells: dict[str, Any] = {}
    curves: dict[str, np.ndarray] = {}
    calls = 0
    reused = 0
    for cell in CELL_ORDER:
        selection = selections[cell]
        checkpoint_path = output_root / selection["checkpoint"]["filename"]
        if sha256_file(checkpoint_path) != selection["checkpoint"]["sha256"]:
            raise RuntimeError(f"{cell} 选择检查点摘要不符")
        identity = {
            **run_identity,
            "target_data_inventory_sha256": target_inventory["sha256"],
            "cell": cell,
            "checkpoint_sha256": selection["checkpoint"]["sha256"],
            "first_alert_contract": config["first_alert_contract"],
        }
        restored = load_target_evaluation(output_root, cell, identity)
        if restored is not None:
            cell_result, budget_curve, _first_alert_curves = restored
            cells[cell] = cell_result
            for name, values in budget_curve.items():
                curves[f"{cell}__{name}"] = values
            reused += 1
            continue
        model = build_model(
            config, capacity_key, cell, config["precision"]["profile_id"]
        ).to(device)
        checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        model.load_state_dict(checkpoint["model"])
        selected_p = float(model.p.detach())
        if abs(selected_p - float(selection["p_at_selection"])) > 1e-9:
            raise RuntimeError(f"{cell} 回载 p 与源年选择封印不符")
        torch.cuda.reset_peak_memory_stats(device)
        started = time.time()
        flow_scores, seen = score_target(config, model, target, device)
        if not seen.all():
            raise RuntimeError(f"{cell} 目标评价未覆盖全部流，禁止首次告警聚合")
        inference_seconds = time.time() - started
        calls += 1
        main_p = selected_p if config["cells"][cell]["learned_lp_pooling"] else None
        main_scores = legacy.entity_scores(
            flow_scores, seen, flow_entity, len(entity_labels), main_p
        )
        maximum_scores = legacy.entity_scores(
            flow_scores, seen, flow_entity, len(entity_labels), None
        )
        valid_entity = np.isfinite(main_scores)
        valid_maximum = np.isfinite(maximum_scores)
        first_alert_started = time.time()
        first_alert, first_alert_curves = target_first_alert_aggregate(
            config=config,
            target=target,
            flow_scores=flow_scores,
            flow_entity=flow_entity,
            entity_labels=entity_labels,
            entity_scores=main_scores,
            p_value=main_p,
        )
        first_alert["aggregation_seconds"] = time.time() - first_alert_started
        elapsed = time.time() - started
        metrics = {
            "flow_average_precision": float(
                legacy.average_precision_score(target["y24"][seen], flow_scores[seen])
            ),
            "flow_roc_auc": float(
                legacy.roc_auc_score(target["y24"][seen], flow_scores[seen])
            ),
            "entity_average_precision": float(
                legacy.average_precision_score(
                    entity_labels[valid_entity], main_scores[valid_entity]
                )
            ),
            "maximum_entity_average_precision": float(
                legacy.average_precision_score(
                    entity_labels[valid_maximum], maximum_scores[valid_maximum]
                )
            ),
            "dr_at_fpr": {
                f"fpr_{value:g}": legacy.dr_at_fpr(main_scores, entity_labels, value)
                for value in DR_FPR_GRID
            },
            "maximum_dr_at_fpr": {
                f"fpr_{value:g}": legacy.dr_at_fpr(
                    maximum_scores, entity_labels, value
                )
                for value in DR_FPR_GRID
            },
            "flows_scored": int(seen.sum()),
            "entities_scored": int(valid_entity.sum()),
            "inference_seconds": inference_seconds,
            "first_alert_aggregation_seconds": first_alert["aggregation_seconds"],
            "evaluation_seconds": elapsed,
            "effective_flow_throughput_per_second": int(seen.sum()) / elapsed,
            "peak_gpu_allocated_mib": torch.cuda.max_memory_allocated(device) / 2**20,
            "peak_gpu_reserved_mib": torch.cuda.max_memory_reserved(device) / 2**20,
            "target_evaluation_call": CELL_ORDER.index(cell) + 1,
        }
        budget_curve = legacy.complete_budget_curve(main_scores, entity_labels)
        cell_result = save_target_evaluation(
            output_root,
            cell,
            identity,
            {
                "mechanisms": config["cells"][cell],
                "selection": selection,
                "selected_p": selected_p,
                "target": metrics,
                "first_alert": first_alert,
            },
            budget_curve,
            first_alert_curves,
        )
        cells[cell] = cell_result
        for name, values in budget_curve.items():
            curves[f"{cell}__{name}"] = values
        del model, checkpoint, flow_scores, seen, main_scores, maximum_scores
        torch.cuda.empty_cache()
    if calls + reused != 4:
        raise RuntimeError("目标四格评价次数不符")
    return cells, curves, {
        "calls_this_process": calls,
        "receipts_reused": reused,
        **entity_stats,
    }


def publish_first_alert_bundle(
    output_root: Path,
    selections: Mapping[str, Mapping[str, Any]],
    target_cells: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    vectors: dict[str, np.ndarray] = {}
    source_cells: dict[str, Any] = {}
    cells: dict[str, Any] = {}
    for scope, records in (("source", selections), ("target", target_cells)):
        for cell in CELL_ORDER:
            first_alert = (
                records[cell]["source_first_alert"]
                if scope == "source"
                else records[cell]["first_alert"]
            )
            artifact_path = output_root / first_alert["artifact"]["filename"]
            if sha256_file(artifact_path) != first_alert["artifact"]["sha256"]:
                raise RuntimeError(f"{scope}/{cell} 首次告警分格制品摘要不符")
            with np.load(artifact_path) as payload:
                local_vectors = {name: payload[name] for name in payload.files}
            for name, values in local_vectors.items():
                vectors[f"{scope}__{cell}__{name}"] = values
                if scope == "target":
                    vectors[f"{cell}__{name}"] = values
            summary = {
                key: value for key, value in first_alert.items() if key != "artifact"
            }
            if scope == "source":
                source_cells[cell] = summary
            else:
                cells[cell] = summary
    artifact_path = output_root / "first-alert-timing-curves.npz"
    artifact = save_npz_atomic(artifact_path, vectors)
    artifact["filename"] = artifact_path.name
    receipt = {
        "schema_version": "ch3-first-alert-timing-v1",
        "run_id": RUN_ID,
        "axis": "exposure_index",
        "axis_field_suffix": "exposure_index",
        "rate_field_suffix": "timely_detection_rate",
        "time_delay_available": False,
        "curve_encoding": "right_continuous_exact_breakpoints",
        "artifact": artifact,
        "cells": cells,
        "source_cells": source_cells,
        "scopes": ["source", "target"],
        "budget_count_per_cell": len(DR_FPR_GRID),
        "persisted_per_flow_scores": False,
        "persisted_per_entity_scores": False,
        "persisted_per_entity_first_alert": False,
    }
    receipt_path = output_root / "first-alert-timing-receipt.json"
    atomic_json(receipt_path, receipt)
    return receipt, {
        "receipt": {
            "filename": receipt_path.name,
            "bytes": receipt_path.stat().st_size,
            "sha256": sha256_file(receipt_path),
        },
        "artifact": artifact,
    }


def build_manifest(output_root: Path) -> None:
    legacy.RUN_ID = RUN_ID
    legacy.build_manifest(output_root)
    manifest_path = output_root / "manifest.json"
    manifest = load_json(manifest_path)
    manifest.get("files", {}).pop("manifest.json", None)
    receipt_path = output_root / "first-alert-timing-receipt.json"
    artifact_path = output_root / "first-alert-timing-curves.npz"
    if receipt_path.is_file() and artifact_path.is_file():
        receipt = load_json(receipt_path)
        manifest["first_alert_aggregation"] = {
            "schema_version": receipt["schema_version"],
            "axis": receipt["axis"],
            "time_delay_available": receipt["time_delay_available"],
            "source_cell_count": len(receipt["source_cells"]),
            "target_cell_count": len(receipt["cells"]),
            "budget_count_per_cell": receipt["budget_count_per_cell"],
            "curve_field_count": len(receipt["artifact"]["fields"]),
            "receipt_sha256": sha256_file(receipt_path),
            "artifact_sha256": sha256_file(artifact_path),
            "persisted_per_flow_scores": False,
            "persisted_per_entity_scores": False,
            "persisted_per_entity_first_alert": False,
        }
    atomic_json(manifest_path, manifest)


def verify_architecture_receipt(config: Mapping[str, Any]) -> dict[str, Any]:
    architecture = config["architecture_selection"]
    path = Path(architecture["capacity_receipt_path"])
    if not path.is_file():
        raise RuntimeError("旧 FP32 容量选择尚未封印，拒绝启动 BF16 重训")
    if sha256_file(path) != architecture["capacity_receipt_sha256"]:
        raise RuntimeError("旧 FP32 容量选择收据摘要不符")
    receipt = load_json(path)
    if (
        receipt.get("schema_version") != "ch3-rwkv7-capacity-selection-v1"
        or receipt.get("selected_adapter") != "R2"
        or receipt.get("selected_capacity") != architecture["selected_capacity"]
        or receipt.get("selected_capacity") not in CAPACITY_SHAPES
        or receipt.get("target_arrays_loaded") != 0
    ):
        raise RuntimeError("旧 FP32 容量收据未封印 R2 与合法最终容量")
    return receipt


def _legacy_build_model(
    config: Mapping[str, Any], adapter_key: str, capacity_key: str, cell: str
) -> BF16RWKV7ProtocolAModel:
    if adapter_key != "R2":
        raise RuntimeError("BF16 固定结构入口禁止构造 R0 或 R1")
    return build_model(
        config, capacity_key, cell, config["precision"]["profile_id"]
    )


def run_experiment(
    config: Mapping[str, Any], args: argparse.Namespace, config_path: Path
) -> None:
    from sklearn.metrics import average_precision_score, roc_auc_score

    legacy.average_precision_score = average_precision_score
    legacy.roc_auc_score = roc_auc_score
    legacy.RUN_ID = RUN_ID
    legacy.build_model = _legacy_build_model
    legacy.score_target = score_target
    if not torch.cuda.is_available():
        raise RuntimeError("统一 BF16 Protocol A 正式运行要求可用 CUDA")
    device = torch.device("cuda")
    precision_contract_path = resolve_project_path(
        config["precision"]["contract_path"]
    )
    precision_contract = load_and_validate_contract(precision_contract_path)
    profile = validate_runtime_profile(
        precision_contract,
        config["precision"]["profile_id"],
        device.type,
        torch,
    )
    if create_grad_scaler(profile, torch) is not None:
        raise RuntimeError("BF16 运行不得创建 GradScaler")
    architecture_receipt = verify_architecture_receipt(config)
    capacity_key = str(config["architecture_selection"]["selected_capacity"])
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    source_inventory = legacy.data_inventory(
        Path(config["paths"]["cache_root"]), SOURCE_ARRAYS
    )
    run_identity = {
        "run_id": RUN_ID,
        "config_sha256": sha256_file(config_path),
        "code_sha256": sha256_file(Path(__file__).resolve()),
        "source_data_inventory_sha256": source_inventory["sha256"],
        "architecture_selection_receipt_sha256": config["architecture_selection"][
            "capacity_receipt_sha256"
        ],
        "precision_contract_sha256": sha256_file(precision_contract_path),
        "precision_profile_id": config["precision"]["profile_id"],
    }
    frozen_config_path = output_root / "config.json"
    if frozen_config_path.is_file():
        if not args.resume or load_json(frozen_config_path) != config:
            raise RuntimeError("BF16 输出根已有不兼容冻结配置")
    else:
        atomic_json(frozen_config_path, config)
    architecture_evidence = {
        "schema_version": "ch3-rwkv7-bf16-architecture-evidence-v1",
        "source_run_id": SOURCE_RUN_ID,
        "source_precision": "float32",
        "selected_adapter": "R2",
        "selected_capacity": capacity_key,
        "capacity_selection_receipt": {
            "path": config["architecture_selection"]["capacity_receipt_path"],
            "sha256": config["architecture_selection"]["capacity_receipt_sha256"],
        },
        "source_selection_metric": architecture_receipt["selection_metric"],
        "precision_changed_after_architecture_selection": True,
        "bf16_architecture_search_repeated": False,
        "target_metrics_used_for_architecture_selection": False,
    }
    atomic_json(output_root / "architecture-selection-evidence.json", architecture_evidence)

    selection_path = output_root / "selection_frozen.json"
    if selection_path.is_file():
        if not args.resume:
            raise RuntimeError("全新 BF16 运行已存在源年四格封印")
        seal = load_json(selection_path)
        if seal.get("identity") != run_identity or not seal.get("all_source_cells_sealed"):
            raise RuntimeError("BF16 源年四格封印身份不符")
        selections = seal["cells"]
        split_stats = seal["source_split"]
        source_training_seconds = float(seal["source_training_seconds"])
    else:
        legacy.write_status(
            output_root,
            "running",
            "source-fixed-architecture-four-cells",
            None,
            f"只训练旧 FP32 已封印的 R2/{capacity_key}，目标数组读取计数为零",
        )
        cache_root = Path(config["paths"]["cache_root"])
        source = legacy.load_arrays(cache_root, SOURCE_ARRAYS)
        if source["X23"].shape != (16_353_511, 83) or source["I23"].shape != (
            271_815,
            128,
        ):
            raise RuntimeError("LSPR23 冻结缓存形状不符")
        train_rows, validation_rows, split_stats = legacy.source_split(source, config)
        weights = legacy.source_loss_weights(source, train_rows)
        selections: dict[str, Any] = {}
        source_training_seconds = 0.0
        for cell in CELL_ORDER:
            selections[cell] = train_cell(
                config,
                cell,
                capacity_key,
                output_root,
                run_identity,
                source,
                train_rows,
                validation_rows,
                weights,
                device,
                profile,
                args.resume,
            )
            source_training_seconds += float(selections[cell]["training_seconds"])
        seal = {
            "schema_version": "ch3-rwkv7-bf16-all-source-cells-frozen-v1",
            "identity": run_identity,
            "source_data_inventory": source_inventory,
            "source_split": split_stats,
            "architecture_selection": architecture_evidence,
            "selected_adapter": "R2",
            "selected_capacity": capacity_key,
            "cells": selections,
            "all_source_cells_sealed": True,
            "target_arrays_loaded_before_seal": 0,
            "source_training_seconds": source_training_seconds,
            "sealed_at_unix": time.time(),
        }
        atomic_json(selection_path, seal)
        del source, train_rows, validation_rows
        torch.cuda.empty_cache()
    if not load_json(selection_path).get("all_source_cells_sealed"):
        raise RuntimeError("BF16 源年四格未全部封印，禁止加载 LSPR24")

    legacy.write_status(
        output_root,
        "running",
        "target-evaluation",
        None,
        "BF16 四格源年选择封印后首次加载 LSPR24",
    )
    cache_root = Path(config["paths"]["cache_root"])
    target_inventory = legacy.data_inventory(cache_root, TARGET_ARRAYS)
    target = legacy.load_arrays(cache_root, TARGET_ARRAYS)
    if target["X24"].shape != (20_227_356, 83):
        raise RuntimeError("LSPR24 冻结缓存形状不符")
    target_started = time.time()
    cells, curves, evaluation_counts = evaluate_target(
        config,
        output_root,
        run_identity,
        selections,
        capacity_key,
        target_inventory,
        target,
    )
    curve_path = output_root / "complete-alert-budget-curves.npz"
    temporary_curve = curve_path.with_name(
        f"{curve_path.name}.partial.{os.getpid()}"
    )
    with temporary_curve.open("wb") as handle:
        np.savez_compressed(handle, **curves)
    os.replace(temporary_curve, curve_path)
    curve_receipt = {
        "schema_version": "ch3-rwkv7-bf16-complete-alert-budget-curves-v1",
        "artifact": {
            "filename": curve_path.name,
            "bytes": curve_path.stat().st_size,
            "sha256": sha256_file(curve_path),
        },
        "cells": list(CELL_ORDER),
        "complete_over_all_reachable_negative_entity_budgets": True,
    }
    atomic_json(
        output_root / "complete-alert-budget-curves-receipt.json", curve_receipt
    )
    first_alert_receipt, first_alert_artifacts = publish_first_alert_bundle(
        output_root, selections, cells
    )
    interaction: dict[str, Any] = {}
    for metric in (
        "flow_average_precision",
        "entity_average_precision",
        "maximum_entity_average_precision",
    ):
        values = {cell: cells[cell]["target"][metric] for cell in CELL_ORDER}
        interaction[metric] = {
            **values,
            "causal_prefix_effect": values["C10"] - values["C00"],
            "elp_effect": values["C01"] - values["C00"],
            "combined_effect": values["C11"] - values["C00"],
            "interaction": values["C11"] - values["C10"] - values["C01"] + values["C00"],
        }
    target_seconds = time.time() - target_started
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "model": {
            "display_name": config["display_name"],
            "selected_adapter": "R2",
            "selected_capacity": capacity_key,
            "parameter_count": R2_PARAMETER_COUNTS[capacity_key],
            "official_source_commit": config["candidate"]["official_source_commit"],
            "official_license": config["candidate"]["official_license"],
            "pytorch_version": torch.__version__,
            "precision_profile_id": config["precision"]["profile_id"],
        },
        "evidence": {
            "experiment_status": "computed_not_yet_analyzed",
            "formal_paper_evidence": False,
            "target_previously_accessed": True,
            "independent_test": False,
            "target_metrics_used_for_selection_or_tuning": False,
            "precision_changed_after_architecture_selection": True,
            "bf16_architecture_search_repeated": False,
            "architecture_causal_claim_allowed_from_this_run": False,
        },
        "architecture_selection": architecture_evidence,
        "source_selection": load_json(selection_path),
        "target_evaluation": {
            "dataset": "LSPR24",
            "flow_count": int(len(target["y24"])),
            "flow_positive_rate": float(np.mean(target["y24"], dtype=np.float64)),
            "cells": cells,
            "data_inventory": target_inventory,
            "counts": evaluation_counts,
        },
        "interaction": interaction,
        "first_alert": first_alert_receipt,
        "isolation": {
            "all_source_cells_sealed_before_target_load": True,
            "target_disk_loads": 1,
            "target_evaluation_calls": 4,
            "one_call_per_cell_or_matching_complete_receipt": True,
        },
        "artifact_policy": {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "all_epoch_checkpoints_persisted": True,
            "latest_complete_inflight_persisted": True,
            "complete_alert_budget_curve": curve_receipt,
            "first_alert_timing": first_alert_artifacts,
            "per_entity_first_alert_persisted": False,
        },
        "resource": {
            "source_training_wall_seconds": source_training_seconds,
            "target_stage_wall_seconds": target_seconds,
            "gpu_hours": (source_training_seconds + target_seconds) / 3600.0,
            "gpu_hours_observed_without_limit": (
                source_training_seconds + target_seconds
            )
            / 3600.0,
            "peak_process_rss_mib": legacy.process_peak_rss_mib(),
            "first_alert_aggregation": {
                "axis": "exposure_index",
                "budget_count_per_cell": len(DR_FPR_GRID),
                "source_cell_count": len(CELL_ORDER),
                "target_cell_count": len(CELL_ORDER),
                "source_aggregation_seconds": sum(
                    float(selections[cell]["source_first_alert"]["aggregation_seconds"])
                    for cell in CELL_ORDER
                ),
                "target_aggregation_seconds": sum(
                    float(cells[cell]["first_alert"]["aggregation_seconds"])
                    for cell in CELL_ORDER
                ),
                "artifact_bytes": first_alert_artifacts["artifact"]["bytes"],
                "curve_field_count": len(first_alert_artifacts["artifact"]["fields"]),
                "temporary_state": "六档乘恶意实体数的int64首次曝光矩阵及每实体常数聚合状态",
                "persisted_per_flow_scores": False,
                "persisted_per_entity_scores": False,
                "persisted_per_entity_first_alert": False,
            },
            "launcher_admission_receipt": load_json(Path(args.resource_receipt))
            if args.resource_receipt
            else None,
        },
    }
    atomic_json(output_root / "aggregate-results.json", result)
    legacy.write_status(
        output_root,
        "computed",
        "publish-pending",
        0,
        "固定 R2/容量的 BF16 源年选择与目标四格评价完成",
    )
    build_manifest(output_root)


def publish_aggregate(config: Mapping[str, Any], args: argparse.Namespace) -> None:
    destination = config["swanlab"]
    if (
        args.authorized_swanlab_workspace != destination["workspace"]
        or args.authorized_swanlab_project != destination["project"]
    ):
        raise RuntimeError("SwanLab 授权目的地与 BF16 冻结配置不一致")
    output_root = Path(config["paths"]["output_root"])
    result = load_json(output_root / "aggregate-results.json")
    import swanlab

    swanlab.init(
        workspace=destination["workspace"],
        project=destination["project"],
        name=RUN_ID,
        mode=destination["mode"],
        group=destination["group"],
        tags=destination["tags"],
        log_dir=str(output_root / "swanlog"),
        config={
            "run_id": RUN_ID,
            "seed": config["training"]["seed"],
            "protocol": "protocol_a_fixed_r2_sealed_capacity_bf16",
            "selected_adapter": "R2",
            "selected_capacity": result["model"]["selected_capacity"],
            "precision_profile_id": config["precision"]["profile_id"],
            "precision_changed_after_architecture_selection": True,
            "target_previously_accessed": True,
            "independent_test": False,
        },
    )
    metrics: dict[str, float] = {}
    for cell in CELL_ORDER:
        selection = result["source_selection"]["cells"][cell]
        target = result["target_evaluation"]["cells"][cell]["target"]
        metrics[f"source/{cell}_selected_epoch"] = float(
            selection["selected_epoch"]
        )
        metrics[f"source/{cell}_validation_flow_ap"] = float(
            selection["validation_flow_ap"]
        )
        metrics[f"target/{cell}_flow_ap"] = target["flow_average_precision"]
        metrics[f"target/{cell}_entity_ap"] = target["entity_average_precision"]
        metrics[f"target/{cell}_maximum_entity_ap"] = target[
            "maximum_entity_average_precision"
        ]
        for key, value in target["dr_at_fpr"].items():
            metrics[f"target/{cell}_dr_{key}"] = value
    metrics["resource/gpu_hours"] = result["resource"]["gpu_hours"]
    metrics["resource/peak_process_rss_mib"] = result["resource"][
        "peak_process_rss_mib"
    ]
    swanlab.log(metrics, step=0)
    swanlab.finish()
    atomic_json(
        output_root / "swanlab-receipt.json",
        {
            "schema_version": "ch3-rwkv7-fixed-bf16-swanlab-receipt-v1",
            "completed": True,
            "workspace": destination["workspace"],
            "project": destination["project"],
            "metric_count": len(metrics),
            "per_sample_values_uploaded": False,
        },
    )
    legacy.RUN_ID = RUN_ID
    legacy.write_status(output_root, "complete", "finished", 0, "统一 BF16 聚合指标发布完成")
    build_manifest(output_root)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_json(config_path)
    validate_config(config, require_resolved=args.require_resolved or not args.validate_config)
    if args.validate_config:
        status = (
            "配置核验通过（容量待旧 FP32 收据注入）"
            if config["architecture_selection"]["selected_capacity"] is None
            else "解析配置核验通过"
        )
        print(status)
        return 0
    try:
        if args.publish_only:
            publish_aggregate(config, args)
        else:
            run_experiment(config, args, config_path)
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        legacy.RUN_ID = RUN_ID
        legacy.write_status(
            output_root,
            "failed",
            "runtime",
            1,
            f"{type(error).__name__}: {error}"[:1000],
        )
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
