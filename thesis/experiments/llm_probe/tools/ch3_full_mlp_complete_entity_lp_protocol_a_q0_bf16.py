# -*- coding: utf-8 -*-
"""全容量多层感知机统一 BF16 协议 A 资格实验。

本入口只消费父源年筛选已经封印的 8x512 胜出配置，不重新比较容量或配方。
数据划分和评价纯函数复用旧 FP32 入口；模型前向、训练、恢复和资源收据在本文件
按 ``cuda-bf16-amp-fp32-sensitive-v1`` 独立实现，绝不加载旧 FP32 权重或优化器。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
import traceback
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import ch3_full_mlp_complete_entity_lp_protocol_a_q0 as legacy
import neural_precision_runtime as precision


SCHEMA_VERSION = "ch3-full-mlp-complete-entity-lp-protocol-a-q0-bf16-config-v1"
RESULT_SCHEMA_VERSION = "ch3-full-mlp-complete-entity-lp-protocol-a-q0-bf16-results-v1"
RUN_ID = "ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1"
PROFILE_ID = precision.DEFAULT_PROFILE_ID
PARENT_RUN_ID = "ch3-full-capacity-mlp-source-screen-seed42-v1"
PARENT_UNIT_KEY = "mlp-depth8-width512-full--paper-log-median"
CELL_ORDER = legacy.CELL_ORDER
DR_FPR_GRID = legacy.DR_FPR_GRID
SOURCE_ARRAYS = legacy.SOURCE_ARRAYS
TARGET_ARRAYS = legacy.TARGET_ARRAYS
T0 = time.time()

_PROFILE: dict[str, Any] | None = None
_CONTRACT: dict[str, Any] | None = None
_ARGS: argparse.Namespace | None = None
_PARENT_RECEIPT: dict[str, Any] | None = None
_LAST_INFERENCE_SECONDS = 0.0
_ORDER_CACHE: dict[str, Any] = {}


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="全容量多层感知机统一 BF16 协议 A 资格实验")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置")
    parser.add_argument("--validate-config", action="store_true", help="只核验配置与精度合同")
    parser.add_argument("--resume", action="store_true", help="恢复同身份步级检查点")
    parser.add_argument("--publish-only", action="store_true", help="只发布已有聚合指标")
    parser.add_argument("--resource-receipt", help="启动器资源准入收据")
    parser.add_argument("--authorized-swanlab-workspace")
    parser.add_argument("--authorized-swanlab-project")
    return parser.parse_args()


def _expected_training() -> dict[str, Any]:
    return {
        "seed": 42,
        "sequence_length": 128,
        "batch_size": 64,
        "microbatch_size": 64,
        "accumulation_steps": 1,
        "normalization_unit": "flow",
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
        "checkpoint_interval_optimizer_steps": 20,
        "precision_profile_id": PROFILE_ID,
    }


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或新 BF16 运行身份不符")
    if config.get("model_key") != "full_mlp" or config.get("cells") != legacy.CELLS:
        raise ValueError("只允许全容量多层感知机协议 A 四个训练格")
    if config.get("source_arrays") != list(SOURCE_ARRAYS) or config.get("target_arrays") != list(TARGET_ARRAYS):
        raise ValueError("源年或目标年数组合同不符")
    if config.get("training") != _expected_training():
        raise ValueError("训练、微批、恢复或精度合同不符")
    candidate = config.get("candidate")
    expected_candidate = {
        "unit_key": PARENT_UNIT_KEY,
        "hidden_depth": 8,
        "hidden_size": 512,
        "activation": "relu",
        "dropout": 0.1,
        "parameter_formula": "m*d^2+(m+84)*d+2",
        "parameter_count": 2_144_258,
    }
    if candidate != expected_candidate or legacy.mlp_parameter_count(83, 8, 512) != 2_144_258:
        raise ValueError("未严格复用父封印的 8x512 胜出结构")
    parent = config.get("parent_selection")
    if parent != {
        "run_id": PARENT_RUN_ID,
        "seal_path": (
            "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/"
            "ch3-full-capacity-mlp-source-screen-seed42-v1/backbone_selection_frozen.json"
        ),
        "selected_unit_key": PARENT_UNIT_KEY,
        "selected_epoch": 10,
        "validation_flow_ap": 0.9997527228408204,
        "hidden_depth": 8,
        "hidden_size": 512,
        "learning_rate": 0.0003162277660168379,
        "weight_decay": 0.0,
        "dropout": 0.1,
        "parameter_count": 2_144_258,
        "target_year_arrays_read": 0,
    }:
        raise ValueError("父选择封印摘要不符")
    evaluation = config.get("evaluation", {})
    if evaluation.get("p_grid") != [0.5, 1.0, 2.0, 4.0, 8.0]:
        raise ValueError("实体幂平均 p 网格不符")
    if evaluation.get("p_tie_break") != "smaller_p" or evaluation.get("dr_fpr_grid") != list(DR_FPR_GRID):
        raise ValueError("幂选择或六档误报预算不符")
    if evaluation.get("length_buckets") != [[1, 2], [3, 10], [11, 100], [101, 1000], [1001, None]]:
        raise ValueError("长度桶不符")
    if evaluation.get("target_load_after_all_selections_sealed") is not True:
        raise ValueError("目标年必须在全部源年选择封印后才可加载")
    if evaluation.get("target_evaluation_calls") != 4:
        raise ValueError("目标年必须每个训练格恰好一次前向")
    if evaluation.get("first_alert_exposure_order") != "ascending_frozen_flow_index_within_entity":
        raise ValueError("首次告警曝光顺序不符")
    if evaluation.get("first_alert_quantiles") != [0.25, 0.5, 0.75, 0.9, 0.95]:
        raise ValueError("首次告警曝光分位合同不符")
    precision_path = resolve_precision_contract(config)
    contract = precision.load_and_validate_contract(precision_path)
    profile = precision.get_profile(contract, PROFILE_ID)
    if profile["compute_dtype"] != "bfloat16" or profile["grad_scaler"] is not False:
        raise ValueError("本身份只允许 BF16 autocast 且不得使用 GradScaler")
    precision.validate_microbatch_plan(64, 64, 1, "flow", is_tail_batch=False)
    if Path(config.get("paths", {}).get("output_root", "")).name != RUN_ID:
        raise ValueError("输出根与新运行身份不符")
    if config.get("swanlab", {}).get("group") != RUN_ID:
        raise ValueError("SwanLab 分组与新运行身份不符")
    artifact = config.get("artifact_policy", {})
    if artifact != {
        "persist_selected_checkpoint_per_cell": True,
        "persist_every_epoch_checkpoint_per_cell": True,
        "persist_inflight_optimizer_step_checkpoint": True,
        "persist_per_flow_scores": False,
        "persist_per_entity_scores": False,
        "persist_complete_budget_curve_aggregate": True,
        "persist_first_alert_aggregate_only": True,
    }:
        raise ValueError("制品合同不符")
    if config.get("target_year_arrays_read") != 0 or config.get("formal_paper_evidence"):
        raise ValueError("运行前目标读取或证据身份不符")


def resolve_precision_contract(config: dict[str, Any]) -> Path:
    configured = Path(config.get("paths", {}).get("precision_contract", ""))
    if configured.is_file():
        return configured
    local = TOOL_DIR.parent / "configs" / configured.name
    if configured.name == "neural-precision-profiles-v1.json" and local.is_file():
        return local
    raise FileNotFoundError(f"统一精度合同不存在：{configured}")


def validate_parent_seal(config: dict[str, Any]) -> dict[str, Any]:
    parent = config["parent_selection"]
    path = Path(parent["seal_path"])
    if not path.is_file():
        raise FileNotFoundError(f"父筛选封印不存在：{path}")
    seal = legacy.load_json(path)
    selected = seal.get("selected_candidate")
    if seal.get("run_id") != parent["run_id"] or seal.get("source_gate", {}).get("passed") is not True:
        raise RuntimeError("父运行未封印可消费的胜出配置")
    expected = {
        "unit_key": parent["selected_unit_key"],
        "hidden_depth": parent["hidden_depth"],
        "hidden_size": parent["hidden_size"],
        "learning_rate": parent["learning_rate"],
        "weight_decay": parent["weight_decay"],
        "dropout": parent["dropout"],
        "parameter_count_framework": parent["parameter_count"],
        "selected_epoch": parent["selected_epoch"],
        "validation_flow_ap": parent["validation_flow_ap"],
    }
    if not isinstance(selected, dict) or any(selected.get(key) != value for key, value in expected.items()):
        raise RuntimeError("父封印胜出配置、轮次或源年选择证据不符")
    if seal.get("target_year_arrays_read") != 0 or not seal.get("all_candidates_completed"):
        raise RuntimeError("父封印目标年隔离或候选完成状态不符")
    return {
        "schema_version": "ch3-full-mlp-bf16-parent-selection-receipt-v1",
        "path": str(path),
        "sha256": legacy.sha256_file(path),
        "run_id": parent["run_id"],
        "selected_candidate": expected,
        "parent_target_year_arrays_read": 0,
    }


if legacy.nn is not None:
    class FullCapacityMLPBF16(legacy.nn.Module):
        """参数保持 FP32，线性与激活由外层 CUDA BF16 autocast 执行。"""

        def __init__(self, feature_count: int, hidden_depth: int, hidden_size: int, dropout: float, aggregate: bool):
            super().__init__()
            self.aggregate = aggregate
            layers: list[Any] = []
            input_size = feature_count
            for _ in range(hidden_depth - 1):
                layers.extend((legacy.nn.Linear(input_size, hidden_size), legacy.nn.ReLU(), legacy.nn.Dropout(dropout)))
                input_size = hidden_size
            self.encoder = legacy.nn.Sequential(*layers)
            self.fusion = legacy.nn.Sequential(
                legacy.nn.Linear(hidden_size * 2, hidden_size), legacy.nn.ReLU(), legacy.nn.Dropout(dropout)
            )
            self.output = legacy.nn.Linear(hidden_size, 1)
            self.p_log = legacy.nn.Parameter(legacy.torch.tensor(float(math.log(2.0)), dtype=legacy.torch.float32))

        @property
        def p(self) -> Any:
            return legacy.torch.exp(self.p_log.float()).clamp(1e-3, 1e3)

        def forward(self, values: Any, valid: Any) -> Any:
            mask = valid.to(values.dtype)
            hidden = self.encoder(values) * mask.unsqueeze(-1)
            if self.aggregate:
                with precision.fp32_island(hidden, mask, device_type=values.device.type, torch_module=legacy.torch) as (hidden32, mask32):
                    count = legacy.torch.cumsum(mask32, 1).clamp(min=1.0).unsqueeze(-1)
                    context = legacy.torch.cumsum(hidden32, 1) / count
                    context = context * mask32.unsqueeze(-1)
            else:
                context = legacy.torch.zeros_like(hidden)
            fused = self.fusion(legacy.torch.cat((hidden, context), dim=-1))
            return self.output(fused * mask.unsqueeze(-1)).squeeze(-1)
else:
    class FullCapacityMLPBF16:
        pass


def build_model(config: dict[str, Any], cell: str) -> Any:
    if legacy.torch is None or legacy.nn is None:
        raise RuntimeError("正式计算缺少 PyTorch GPU 依赖")
    candidate = config["candidate"]
    model = FullCapacityMLPBF16(
        83,
        candidate["hidden_depth"],
        candidate["hidden_size"],
        config["training"]["dropout"],
        config["cells"][cell]["causal_prefix_aggregation"],
    )
    actual = sum(parameter.numel() for parameter in model.parameters())
    if actual != 2_144_258:
        raise RuntimeError(f"框架实测参数量不符：{actual}")
    if any(parameter.dtype != legacy.torch.float32 for parameter in model.parameters()):
        raise RuntimeError("模型参数未全部保持 FP32")
    return model


def lp_pool_fp32(scores: Any, valid: Any, p_value: Any) -> Any:
    with precision.fp32_island(scores, valid, p_value, device_type=scores.device.type, torch_module=legacy.torch) as (scores32, valid32, exponent):
        log_scores = legacy.torch.log(scores32.clamp(min=1e-7))
        count = valid32.sum(1).clamp(min=1.0)
        summed = legacy.torch.logsumexp((exponent * log_scores).masked_fill(valid32 < 0.5, -1e30), 1)
        return legacy.torch.exp((summed - legacy.torch.log(count)) / exponent)


def _external_process_gpu_memory_mib(device: Any) -> float:
    free_bytes, total_bytes = legacy.torch.cuda.mem_get_info()
    reserved = int(legacy.torch.cuda.memory_reserved(device))
    return max(int(total_bytes) - int(free_bytes) - reserved, 0) / 2**20


def _restore_rng(runtime_state: dict[str, Any], generator: Any) -> None:
    rng = runtime_state["rng_state"]
    random.setstate(rng["python_random"])
    legacy.torch.set_rng_state(rng["torch_cpu"])
    if rng["torch_cuda_all"] is not None:
        legacy.torch.cuda.set_rng_state_all(rng["torch_cuda_all"])
    if rng["numpy_random"] is not None:
        legacy.np.random.set_state(rng["numpy_random"])
    generator.set_state(runtime_state["sampler_generator_state"])


def _runtime_state(config: dict[str, Any], optimizer_step: int, generator: Any) -> dict[str, Any]:
    assert _PROFILE is not None
    training = config["training"]
    state = precision.build_checkpoint_runtime_state(
        profile_id=PROFILE_ID,
        profile=_PROFILE,
        scaler=None,
        effective_batch_items=training["batch_size"],
        effective_batch_item_unit="sequence",
        microbatch_items=training["microbatch_size"],
        accumulation_steps=training["accumulation_steps"],
        normalization_unit=training["normalization_unit"],
        is_tail_batch=False,
        optimizer_step=optimizer_step,
        optimizer_step_boundary=True,
        torch_module=legacy.torch,
    )
    state["sampler_generator_state"] = generator.get_state()
    return state


def _save_inflight(
    path: Path,
    identity: dict[str, Any],
    epoch: int,
    step: int,
    epoch_completed: bool,
    model: Any,
    optimizer: Any,
    history: list[dict[str, Any]],
    best_ap: float,
    best_epoch: int,
    best_p: float,
    best_state: dict[str, Any] | None,
    running_loss: float,
    elapsed_seconds: float,
    optimizer_step: int,
    generator: Any,
    recovery_count: int,
    processed_valid_flows: int,
) -> None:
    runtime = _runtime_state(_ACTIVE_CONFIG, optimizer_step, generator)
    legacy.atomic_torch(
        path,
        {
            "schema_version": "ch3-full-mlp-bf16-inflight-optimizer-step-v1",
            "identity": identity,
            "epoch": epoch,
            "step": step,
            "epoch_completed": epoch_completed,
            "model": {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()},
            "optimizer": optimizer.state_dict(),
            "history": history,
            "best_ap": best_ap,
            "best_epoch": best_epoch,
            "best_p": best_p,
            "best_state": best_state,
            "running_loss": running_loss,
            "elapsed_seconds": elapsed_seconds,
            "optimizer_step": optimizer_step,
            "optimizer_step_boundary": True,
            "precision_profile_id": PROFILE_ID,
            "runtime_state": runtime,
            "recovery_count": recovery_count,
            "processed_valid_flows": processed_valid_flows,
        },
    )


_ACTIVE_CONFIG: dict[str, Any] = {}


@legacy.torch.no_grad() if legacy.torch is not None else (lambda function: function)
def predict_sequences(
    config: dict[str, Any],
    model: Any,
    rows: Any,
    gX: Any,
    gy: Any,
    gI: Any,
    gM: Any,
    batch_size: int = 2048,
) -> tuple[Any, Any, Any]:
    global _LAST_INFERENCE_SECONDS
    assert _PROFILE is not None
    started = time.time()
    model.eval()
    predictions: list[Any] = []
    labels: list[Any] = []
    flow_ids: list[Any] = []
    length = config["training"]["sequence_length"]
    for start in range(0, len(rows), batch_size):
        selected = legacy.torch.from_numpy(rows[start : start + batch_size]).to(gX.device)
        indices = gI[selected][:, :length]
        valid = gM[selected][:, :length] > 0.5
        batch = indices.shape[0]
        values = gX[indices.reshape(-1)].reshape(batch, length, gX.shape[1])
        with precision.autocast_context(_PROFILE, gX.device.type, legacy.torch):
            logits = model(values, valid)
        with precision.fp32_island(logits, device_type=gX.device.type, torch_module=legacy.torch) as (logits32,):
            probabilities = legacy.torch.sigmoid(logits32)
        mask = valid.reshape(-1)
        predictions.append(probabilities.reshape(-1)[mask].cpu().numpy())
        labels.append(gy[indices.reshape(-1)].reshape(-1)[mask].float().cpu().numpy())
        flow_ids.append(indices.reshape(-1)[mask].cpu().numpy())
    _LAST_INFERENCE_SECONDS = time.time() - started
    model.train()
    return legacy.np.concatenate(predictions), legacy.np.concatenate(labels), legacy.np.concatenate(flow_ids)


def train_cell(
    config: dict[str, Any],
    cell: str,
    output_root: Path,
    run_identity: dict[str, Any],
    source: dict[str, Any],
    train_rows: Any,
    validation_rows: Any,
    device: Any,
    resume: bool,
) -> dict[str, Any]:
    assert _PROFILE is not None and _PARENT_RECEIPT is not None
    checkpoint_path = output_root / "checkpoints" / f"selected-{cell}.pt"
    receipt_path = output_root / "receipts" / f"selection-{cell}.json"
    inflight_path = output_root / "inflight" / f"{cell}.pt"
    identity = {
        "schema_version": "ch3-full-mlp-bf16-cell-identity-v1",
        "run_id": RUN_ID,
        "cell": cell,
        "precision_profile_id": PROFILE_ID,
        "parent_selection_sha256": _PARENT_RECEIPT["sha256"],
        **run_identity,
    }
    if checkpoint_path.is_file() and receipt_path.is_file():
        receipt = legacy.load_json(receipt_path)
        if not resume or receipt.get("identity") != identity:
            raise RuntimeError(f"{cell} 已有完成制品但不可合法复用")
        if receipt.get("checkpoint", {}).get("sha256") != legacy.sha256_file(checkpoint_path):
            raise RuntimeError(f"{cell} 选择检查点摘要不符")
        log(f"{cell} 完成制品身份匹配，恢复时幂等跳过")
        return receipt["selection"]
    if not resume and any(path.exists() for path in (checkpoint_path, receipt_path, inflight_path)):
        raise RuntimeError(f"全新 BF16 运行存在 {cell} 历史制品")

    training = config["training"]
    random.seed(training["seed"])
    legacy.np.random.seed(training["seed"])
    legacy.torch.manual_seed(training["seed"])
    legacy.torch.cuda.manual_seed_all(training["seed"])
    model = build_model(config, cell).to(device)
    optimizer = legacy.make_optimizer(config, model)
    precision.validate_model_optimizer_fp32(model, optimizer, legacy.torch)
    scaler = precision.create_grad_scaler(_PROFILE, legacy.torch)
    if scaler is not None:
        raise RuntimeError("BF16 资格身份禁止 GradScaler")
    generator = legacy.torch.Generator().manual_seed(training["seed"])
    history: list[dict[str, Any]] = []
    best_ap = -1.0
    best_epoch = 0
    best_p = float("nan")
    best_state: dict[str, Any] | None = None
    elapsed_before = 0.0
    start_epoch = 1
    start_step = 1
    running_loss = 0.0
    optimizer_step_count = 0
    recovery_count = 0
    processed_valid_flows = 0
    first_step_path = output_root / "receipts" / f"first-optimizer-step-{cell}.json"
    first_step_receipt: dict[str, Any] | None = (
        legacy.load_json(first_step_path) if resume and first_step_path.is_file() else None
    )
    if resume and inflight_path.is_file():
        inflight = legacy.torch.load(inflight_path, map_location="cpu", weights_only=False)
        if inflight.get("identity") != identity or inflight.get("optimizer_step_boundary") is not True:
            raise RuntimeError(f"{cell} 在途检查点身份或优化器步边界不符")
        runtime = inflight["runtime_state"]
        sampler_state = runtime.pop("sampler_generator_state")
        precision.validate_checkpoint_runtime_state(runtime)
        runtime["sampler_generator_state"] = sampler_state
        if runtime["precision_profile_id"] != PROFILE_ID or runtime["scaler_state_dict"] is not None:
            raise RuntimeError(f"{cell} 在途检查点精度身份不符")
        model.load_state_dict(inflight["model"])
        optimizer.load_state_dict(inflight["optimizer"])
        legacy.move_optimizer_state(optimizer, device)
        history = inflight["history"]
        best_ap = float(inflight["best_ap"])
        best_epoch = int(inflight["best_epoch"])
        best_p = float(inflight["best_p"])
        best_state = inflight["best_state"]
        elapsed_before = float(inflight["elapsed_seconds"])
        optimizer_step_count = int(inflight["optimizer_step"])
        recovery_count = int(inflight.get("recovery_count", 0)) + 1
        processed_valid_flows = int(inflight.get("processed_valid_flows", 0))
        _restore_rng(runtime, generator)
        if inflight["epoch_completed"]:
            start_epoch = int(inflight["epoch"]) + 1
            start_step = 1
            running_loss = 0.0
        else:
            start_epoch = int(inflight["epoch"])
            start_step = int(inflight["step"]) + 1
            running_loss = float(inflight["running_loss"])
        log(f"{cell} 从 epoch={start_epoch} step={start_step} 恢复，恢复次数={recovery_count}")

    X, y, I, M = source["X23"], source["y23"], source["I23"], source["M23"]
    gX = legacy.torch.from_numpy(X).to(device)
    gy = legacy.torch.from_numpy(y).to(device)
    gI = legacy.torch.from_numpy(I).to(device)
    gM = legacy.torch.from_numpy(M).to(device)
    train_indices = I[train_rows]
    train_mask = M[train_rows] > 0
    train_labels = y[train_indices]
    valid_train_labels = train_labels[train_mask]
    sequence_labels = (train_labels * train_mask).max(1) > 0
    sequence_positive_weight = float((1 - sequence_labels.mean()) / max(sequence_labels.mean(), 1e-8))
    flow_positive_rate = float(valid_train_labels.mean())
    positive_weight = legacy.torch.tensor([(1 - flow_positive_rate) / flow_positive_rate], device=device)
    uses_lp = config["cells"][cell]["learned_lp_pooling"]
    length = training["sequence_length"]
    precision.reset_cuda_peak_memory(legacy.torch, device)
    started = time.time()
    validation_seconds_sum = sum(float(item.get("validation_seconds", 0.0)) for item in history)
    model.train()
    for epoch in range(start_epoch, training["epochs"] + 1):
        if epoch != start_epoch:
            start_step = 1
            running_loss = 0.0
        for step in range(start_step, training["steps_per_epoch"] + 1):
            positions = legacy.torch.randint(0, len(train_rows), (training["batch_size"],), generator=generator)
            selected_rows = legacy.torch.from_numpy(train_rows[positions.numpy()]).to(device)
            indices = gI[selected_rows][:, :length]
            valid = gM[selected_rows][:, :length] > 0.5
            values = gX[indices.reshape(-1)].reshape(training["batch_size"], length, gX.shape[1])
            labels = gy[indices.reshape(-1)].reshape(indices.shape)
            valid_units = int(valid.sum().item())
            accumulator = precision.EffectiveBatchAccumulator(
                total_valid_units=valid_units,
                normalization_unit="flow",
                torch_module=legacy.torch,
                expected_microbatches=1,
            )
            accumulator.begin(optimizer)
            with precision.autocast_context(_PROFILE, device.type, legacy.torch):
                logits = model(values, valid)
            with precision.fp32_island(logits, labels, valid, device_type=device.type, torch_module=legacy.torch) as (logits32, labels32, valid32):
                mask32 = valid32.float()
                flow_loss_sum = legacy.torch.nn.functional.binary_cross_entropy_with_logits(
                    logits32,
                    labels32.float(),
                    reduction="none",
                    pos_weight=positive_weight.float(),
                ).mul(mask32).sum(dtype=legacy.torch.float32)
                loss_sum = flow_loss_sum
                if uses_lp:
                    probabilities = legacy.torch.sigmoid(logits32)
                    pooled = lp_pool_fp32(probabilities, mask32, model.p).clamp(1e-6, 1 - 1e-6)
                    auxiliary_labels = (labels32.float() * mask32).amax(-1)
                    weights = 1.0 + (sequence_positive_weight - 1.0) * auxiliary_labels
                    auxiliary_sum = legacy.torch.nn.functional.binary_cross_entropy(
                        pooled, auxiliary_labels, reduction="none"
                    ).mul(weights).sum(dtype=legacy.torch.float32)
                    loss_sum = loss_sum + training["auxiliary_loss_weight"] * auxiliary_sum * valid_units / weights.sum()
            normalized = accumulator.backward(loss_sum, valid_units, scaler=None)
            gradient_norm = accumulator.finish(
                model.parameters(), optimizer, legacy.torch, training["gradient_clip_norm"], scaler=None
            )
            optimizer_step_count += 1
            processed_valid_flows += valid_units
            loss_value = float(normalized.detach())
            running_loss += loss_value
            if optimizer_step_count == 1:
                gradient_value = float(gradient_norm.detach())
                if not math.isfinite(loss_value) or not math.isfinite(gradient_value) or gradient_value <= 0:
                    raise RuntimeError("首个完整优化器步损失或梯度不是有限非零值")
                fp32_state = precision.validate_model_optimizer_fp32(model, optimizer, legacy.torch)
                first_step_receipt = precision.collect_resource_receipt(
                    profile_id=PROFILE_ID,
                    device_type="cuda",
                    effective_batch_items=64,
                    microbatch_items=64,
                    accumulation_steps=1,
                    normalization_unit="flow",
                    processed_valid_units=valid_units,
                    elapsed_seconds=max(time.time() - started, 1e-9),
                    external_process_gpu_memory_mib=_external_process_gpu_memory_mib(device),
                    external_measurement_source="torch.cuda.mem_get_info_minus_process_reserved",
                    torch_module=legacy.torch,
                    device=device,
                )
                first_step_receipt.update(
                    {
                        "schema_version": "ch3-full-mlp-bf16-first-optimizer-step-v1",
                        "cell": cell,
                        "finite_loss": True,
                        "loss": loss_value,
                        "finite_nonzero_gradient": True,
                        "gradient_norm": gradient_value,
                        "parameter_optimizer_fp32": fp32_state,
                        "grad_scaler_used": False,
                    }
                )
                legacy.atomic_json(first_step_path, first_step_receipt)
            if optimizer_step_count % training["checkpoint_interval_optimizer_steps"] == 0:
                _save_inflight(
                    inflight_path, identity, epoch, step, False, model, optimizer, history,
                    best_ap, best_epoch, best_p, best_state, running_loss,
                    elapsed_before + time.time() - started, optimizer_step_count, generator, recovery_count,
                    processed_valid_flows,
                )
            if step % 250 == 0:
                elapsed = elapsed_before + time.time() - started
                total = training["epochs"] * training["steps_per_epoch"]
                eta = elapsed * max(total - optimizer_step_count, 0) / max(optimizer_step_count, 1)
                log(f"{cell} epoch={epoch}/20 step={step}/1000 optimizer_step={optimizer_step_count} 剩余约={eta/60:.1f}分")

        validation_started = time.time()
        predictions, labels_np, _ = predict_sequences(config, model, validation_rows, gX, gy, gI, gM)
        validation_seconds = time.time() - validation_started
        validation_seconds_sum += validation_seconds
        validation_ap = float(legacy.average_precision_score(labels_np, predictions))
        p_value = float(model.p.detach())
        history.append(
            {
                "epoch": epoch,
                "validation_flow_ap": validation_ap,
                "p": p_value,
                "mean_training_loss": running_loss / training["steps_per_epoch"],
                "validation_seconds": validation_seconds,
            }
        )
        if validation_ap > best_ap:
            best_ap = validation_ap
            best_epoch = epoch
            best_p = p_value
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
        elapsed = elapsed_before + time.time() - started
        _save_inflight(
            inflight_path, identity, epoch, training["steps_per_epoch"], True, model, optimizer,
            history, best_ap, best_epoch, best_p, best_state, running_loss, elapsed,
            optimizer_step_count, generator, recovery_count, processed_valid_flows,
        )
        legacy.atomic_torch(
            output_root / "checkpoints" / "epochs" / cell / f"epoch-{epoch:02d}.pt",
            {
                "schema_version": "ch3-full-mlp-bf16-epoch-checkpoint-v1",
                "identity": identity,
                "epoch": epoch,
                "optimizer_step": optimizer_step_count,
                "optimizer_step_boundary": True,
                "precision_profile_id": PROFILE_ID,
                "model": {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()},
            },
        )
        log(f"{cell} epoch={epoch}/20 验证逐流AP={validation_ap:.8f} p={p_value:.6f}")
    if best_state is None or first_step_receipt is None:
        raise RuntimeError(f"{cell} 未产生可选检查点或首步收据")
    training_seconds = elapsed_before + time.time() - started
    selected_runtime = _runtime_state(config, optimizer_step_count, generator)
    legacy.atomic_torch(
        checkpoint_path,
        {
            "schema_version": "ch3-full-mlp-bf16-selected-checkpoint-v1",
            "identity": identity,
            "model": best_state,
            "precision_profile_id": PROFILE_ID,
            "runtime_state_at_training_end": selected_runtime,
        },
    )
    weight_bytes = sum(parameter.numel() * parameter.element_size() for parameter in model.parameters())
    resource_receipt = precision.collect_resource_receipt(
        profile_id=PROFILE_ID,
        device_type="cuda",
        effective_batch_items=64,
        microbatch_items=64,
        accumulation_steps=1,
        normalization_unit="flow",
        processed_valid_units=processed_valid_flows,
        elapsed_seconds=max(training_seconds, 1e-9),
        external_process_gpu_memory_mib=_external_process_gpu_memory_mib(device),
        external_measurement_source="torch.cuda.mem_get_info_minus_process_reserved",
        torch_module=legacy.torch,
        device=device,
    )
    selection = {
        "selected_epoch": best_epoch,
        "validation_flow_ap": best_ap,
        "p_at_selection": best_p,
        "history": history,
        "training_seconds": training_seconds,
        "training_compute_seconds": training_seconds - validation_seconds_sum,
        "selection_validation_seconds": validation_seconds_sum,
        "checkpoint": {
            "filename": str(checkpoint_path.relative_to(output_root)),
            "bytes": checkpoint_path.stat().st_size,
            "sha256": legacy.sha256_file(checkpoint_path),
        },
        "parameter_count": 2_144_258,
        "model_weight_bytes": weight_bytes,
        "optimizer_steps": optimizer_step_count,
        "encoded_sequences": optimizer_step_count * training["batch_size"],
        "processed_valid_flows": processed_valid_flows,
        "precision_profile_id": PROFILE_ID,
        "grad_scaler_used": False,
        "checkpoint_interval_optimizer_steps": 20,
        "recovery_count": recovery_count,
        "recomputed_optimizer_steps_upper_bound": recovery_count * 19,
        "recomputed_sequences_upper_bound": recovery_count * 19 * training["batch_size"],
        "first_optimizer_step": first_step_receipt,
        "precision_resource_receipt": resource_receipt,
        "training_label_balance": {
            "train_sequences": int(len(train_rows)),
            "train_effective_flows": int(train_mask.sum()),
            "train_positive_flows": int(valid_train_labels.sum()),
            "flow_positive_weight": float(positive_weight.item()),
            "train_positive_sequences": int(sequence_labels.sum()),
            "sequence_positive_weight": sequence_positive_weight,
        },
        "peak_gpu_allocated_mib": resource_receipt["cuda_max_memory_allocated_bytes"] / 2**20,
        "peak_gpu_reserved_mib": resource_receipt["cuda_max_memory_reserved_bytes"] / 2**20,
        "peak_process_rss_mib": legacy.process_peak_rss_mib(),
    }
    legacy.atomic_json(receipt_path, {"identity": identity, "selection": selection, "checkpoint": selection["checkpoint"]})
    inflight_path.unlink(missing_ok=True)
    del model, optimizer, gX, gy, gI, gM
    legacy.torch.cuda.empty_cache()
    return selection


@legacy.torch.no_grad() if legacy.torch is not None else (lambda function: function)
def score_target(config: dict[str, Any], model: Any, target: dict[str, Any], device: Any) -> tuple[Any, Any]:
    global _LAST_INFERENCE_SECONDS
    assert _PROFILE is not None
    started = time.time()
    X, I, M = target["X24"], target["I24"], target["M24"]
    gX = legacy.torch.from_numpy(X).to(device)
    gI = legacy.torch.from_numpy(I).to(device)
    gM = legacy.torch.from_numpy(M).to(device)
    scores = legacy.torch.zeros(len(target["y24"]), dtype=legacy.torch.float32, device=device)
    seen = legacy.torch.zeros(len(target["y24"]), dtype=legacy.torch.bool, device=device)
    length = config["training"]["sequence_length"]
    model.eval()
    for start in range(0, len(I), 2048):
        indices = gI[start : start + 2048][:, :length]
        valid = gM[start : start + 2048][:, :length] > 0.5
        batch = indices.shape[0]
        values = gX[indices.reshape(-1)].reshape(batch, length, gX.shape[1])
        with precision.autocast_context(_PROFILE, device.type, legacy.torch):
            logits = model(values, valid)
        with precision.fp32_island(logits, device_type=device.type, torch_module=legacy.torch) as (logits32,):
            probabilities = legacy.torch.sigmoid(logits32)
        flow_ids = indices.reshape(-1)
        mask = valid.reshape(-1)
        scores[flow_ids[mask]] = probabilities.reshape(-1)[mask]
        seen[flow_ids[mask]] = True
    _LAST_INFERENCE_SECONDS = time.time() - started
    result = scores.cpu().numpy(), seen.cpu().numpy()
    del gX, gI, gM, scores, seen
    legacy.torch.cuda.empty_cache()
    return result


def _ordered_exposures(seen: Any, flow_entity: Any) -> dict[str, Any]:
    global _ORDER_CACHE
    key = (int(seen.__array_interface__["data"][0]), int(flow_entity.__array_interface__["data"][0]), len(seen))
    if _ORDER_CACHE.get("key") == key:
        return _ORDER_CACHE
    flow_ids = legacy.np.flatnonzero(seen).astype(legacy.np.int64, copy=False)
    entities = flow_entity[flow_ids]
    order = legacy.np.lexsort((flow_ids, entities))
    ordered_flow_ids = flow_ids[order]
    ordered_entities = entities[order]
    starts = legacy.np.flatnonzero(legacy.np.r_[True, ordered_entities[1:] != ordered_entities[:-1]])
    lengths = legacy.np.diff(legacy.np.r_[starts, len(ordered_entities)]).astype(legacy.np.int64)
    exposure_index = legacy.np.arange(len(ordered_entities), dtype=legacy.np.int64) - legacy.np.repeat(starts, lengths) + 1
    _ORDER_CACHE = {
        "key": key,
        "flow_ids": ordered_flow_ids,
        "entities": ordered_entities,
        "starts": starts,
        "lengths": lengths,
        "exposure_index": exposure_index,
    }
    return _ORDER_CACHE


def first_alert_aggregate(
    flow_scores: Any,
    seen: Any,
    flow_entity: Any,
    entity_labels: Any,
    final_scores: Any,
    p_value: float | None,
    fpr_grid: list[float],
) -> tuple[dict[str, Any], dict[str, Any]]:
    ordered = _ordered_exposures(seen, flow_entity)
    ordered_scores = legacy.np.clip(flow_scores[ordered["flow_ids"]].astype(legacy.np.float64), 1e-7, 1.0)
    if p_value is None:
        running_scores = ordered_scores
    else:
        transformed = ordered_scores**p_value
        cumulative = legacy.np.cumsum(transformed, dtype=legacy.np.float64)
        previous = legacy.np.zeros(len(ordered["starts"]), dtype=legacy.np.float64)
        previous[1:] = cumulative[ordered["starts"][1:] - 1]
        group_sums = cumulative - legacy.np.repeat(previous, ordered["lengths"])
        running_scores = (group_sums / ordered["exposure_index"]) ** (1.0 / p_value)
    valid_entities = legacy.np.isfinite(final_scores)
    positive_entities = valid_entities & (entity_labels == 1)
    benign_entities = valid_entities & (entity_labels == 0)
    positive_count = int(positive_entities.sum())
    benign_count = int(benign_entities.sum())
    negative_scores = legacy.np.sort(final_scores[benign_entities])[::-1]
    summaries: dict[str, Any] = {}
    curves: dict[str, Any] = {}
    quantiles = _ACTIVE_CONFIG["evaluation"]["first_alert_quantiles"]
    for target_fpr in fpr_grid:
        budget_key = f"fpr_{target_fpr:g}"
        threshold = float(negative_scores[min(int(benign_count * target_fpr), benign_count - 1)])
        crossing = legacy.np.flatnonzero(running_scores >= threshold)
        crossing_entities = ordered["entities"][crossing]
        unique_entities, first_positions = legacy.np.unique(crossing_entities, return_index=True)
        first_crossing = crossing[first_positions]
        first_alert = legacy.np.zeros(len(entity_labels), dtype=legacy.np.int64)
        first_alert[unique_entities] = ordered["exposure_index"][first_crossing]
        alerted_positive = positive_entities & (first_alert > 0)
        positive_exposures = first_alert[alerted_positive]
        if len(positive_exposures):
            quantile_values = legacy.np.quantile(positive_exposures, quantiles)
            unique_deadlines, detected_at_deadline = legacy.np.unique(positive_exposures, return_counts=True)
            cumulative_detected = legacy.np.cumsum(detected_at_deadline, dtype=legacy.np.int64)
            deadlines = legacy.np.r_[0, unique_deadlines].astype(legacy.np.int64)
            on_time = legacy.np.r_[0.0, cumulative_detected / positive_count].astype(legacy.np.float64)
        else:
            quantile_values = legacy.np.full(len(quantiles), legacy.np.nan)
            deadlines = legacy.np.array([0], dtype=legacy.np.int64)
            on_time = legacy.np.array([0.0], dtype=legacy.np.float64)
        summaries[budget_key] = {
            "axis": "exposure_index",
            "exposure_index_base": 1,
            "time_delay_available": False,
            "time_delay_unavailable_reason": "T23/t24不是完整流available_ns且available_ns顺序存在逆序",
            "threshold": threshold,
            "positive_entities": positive_count,
            "alerted_positive_entities": int(alerted_positive.sum()),
            "positive_unalerted_rate": float((positive_entities & (first_alert == 0)).sum() / positive_count),
            "benign_entities": benign_count,
            "alerted_benign_entities": int((benign_entities & (first_alert > 0)).sum()),
            "realized_first_alert_fpr": float((benign_entities & (first_alert > 0)).sum() / benign_count),
            "first_alert_exposure_quantiles": {
                f"q{int(value * 100):02d}": None if not math.isfinite(float(result)) else float(result)
                for value, result in zip(quantiles, quantile_values)
            },
            "on_time_detection_curve_points": int(len(deadlines)),
            "on_time_detection_fixed_positive_denominator": positive_count,
        }
        curves[f"first_alert__{budget_key}__exposure_index"] = deadlines
        curves[f"first_alert__{budget_key}__on_time_detection_rate"] = on_time
    return summaries, curves


_LEGACY_EVALUATE_ENTITY_BRANCH = legacy.evaluate_entity_branch
_LEGACY_EVALUATE_SOURCE_GATE = legacy.evaluate_source_gate
_LEGACY_BUILD_MANIFEST = legacy.build_manifest


def evaluate_entity_branch(
    flow_scores: Any,
    seen: Any,
    flow_labels: Any,
    flow_entity: Any,
    entity_labels: Any,
    p_value: float | None,
    fpr_grid: list[float],
) -> tuple[dict[str, Any], Any, dict[str, Any]]:
    metrics, entity_score_values, curve = _LEGACY_EVALUATE_ENTITY_BRANCH(
        flow_scores, seen, flow_labels, flow_entity, entity_labels, p_value, fpr_grid
    )
    latency, latency_curves = first_alert_aggregate(
        flow_scores, seen, flow_entity, entity_labels, entity_score_values, p_value, fpr_grid
    )
    metrics["first_alert"] = latency
    metrics["pure_inference_seconds_shared_forward"] = _LAST_INFERENCE_SECONDS
    curve.update(latency_curves)
    return metrics, entity_score_values, curve


def evaluate_source_gate(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], dict[str, float], dict[str, Any]]:
    result, derived_p, curves = _LEGACY_EVALUATE_SOURCE_GATE(*args, **kwargs)
    result["legacy_mechanism_gate_passed"] = bool(result["passed"])
    result["legacy_mechanism_gate_verdict"] = result["verdict"]
    result["passed"] = True
    result["verdict"] = "bf16_qualification_continues_after_all_source_selections_sealed"
    result["target_authorization_basis"] = "all_four_source_selections_sealed_not_mechanism_gate"
    return result, derived_p, curves


def _rewrite_npz_without_mean_branches(path: Path) -> None:
    if not path.is_file():
        return
    with legacy.np.load(path, allow_pickle=False) as payload:
        values = {name: payload[name] for name in payload.files if "M00" not in name and "M10" not in name}
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        legacy.np.savez_compressed(handle, **values)
    os.replace(temporary, path)


def _strip_mean_branches(value: Any) -> None:
    if isinstance(value, dict):
        value.pop("M00", None)
        value.pop("M10", None)
        for nested in value.values():
            _strip_mean_branches(nested)
    elif isinstance(value, list):
        for nested in value:
            _strip_mean_branches(nested)


def _postprocess_outputs(config: dict[str, Any], output_root: Path, started: float) -> None:
    result_path = output_root / "aggregate-results.json"
    result = legacy.load_json(result_path)
    _strip_mean_branches(result)
    selection_path = output_root / "selection_frozen.json"
    selection = legacy.load_json(selection_path)
    _strip_mean_branches(selection)
    legacy.atomic_json(selection_path, selection)
    source_path = output_root / "source-gate-results.json"
    source = legacy.load_json(source_path)
    _strip_mean_branches(source)
    legacy.atomic_json(source_path, source)
    length_path = output_root / "length-bucket-results.json"
    length_payload = legacy.load_json(length_path)
    _strip_mean_branches(length_payload)
    legacy.atomic_json(length_path, length_payload)
    _rewrite_npz_without_mean_branches(output_root / "source-complete-alert-budget-curves.npz")
    _rewrite_npz_without_mean_branches(output_root / "complete-alert-budget-curves.npz")
    selections = result["source_selection"]["cells"]
    training_seconds = sum(float(selections[cell]["training_compute_seconds"]) for cell in CELL_ORDER)
    selection_seconds = sum(float(selections[cell]["selection_validation_seconds"]) for cell in CELL_ORDER)
    source_inference_seconds = sum(
        float(result["source_gate"]["branches"][cell]["pure_inference_seconds_shared_forward"])
        for cell in CELL_ORDER
    )
    target_inference_seconds = sum(
        float(result["target_evaluation"]["cells"][cell]["target"]["pure_inference_seconds_shared_forward"])
        for cell in CELL_ORDER
    )
    checkpoint_bytes = sum(int(selections[cell]["checkpoint"]["bytes"]) for cell in CELL_ORDER)
    resource = result.setdefault("resource", {})
    resource.update(
        {
            "parameter_count": 2_144_258,
            "model_weight_bytes_fp32": 2_144_258 * 4,
            "training_compute_seconds_sum": training_seconds,
            "selection_seconds_sum": selection_seconds,
            "source_evaluation_pure_inference_seconds_sum": source_inference_seconds,
            "target_evaluation_pure_inference_seconds_sum": target_inference_seconds,
            "pure_inference_seconds_sum": source_inference_seconds + target_inference_seconds,
            "total_process_seconds_before_publish": time.time() - started,
            "selected_checkpoint_bytes_sum": checkpoint_bytes,
            "recovery_count_sum": sum(int(selections[cell]["recovery_count"]) for cell in CELL_ORDER),
            "recomputed_optimizer_steps_upper_bound_sum": sum(
                int(selections[cell]["recomputed_optimizer_steps_upper_bound"]) for cell in CELL_ORDER
            ),
            "processed_training_flows_sum": sum(int(selections[cell]["processed_valid_flows"]) for cell in CELL_ORDER),
            "effective_training_flows_per_second": sum(
                int(selections[cell]["processed_valid_flows"]) for cell in CELL_ORDER
            ) / max(training_seconds, 1e-9),
            "peak_gpu_reserved_mib": max(float(selections[cell]["peak_gpu_reserved_mib"]) for cell in CELL_ORDER),
            "precision_profile_id": PROFILE_ID,
            "effective_batch_sequences": 64,
            "microbatch_sequences": 64,
            "accumulation_steps": 1,
            "checkpoint_interval_optimizer_steps": 20,
        }
    )
    result["schema_version"] = RESULT_SCHEMA_VERSION
    result["parent_selection_receipt"] = _PARENT_RECEIPT
    result["precision"] = precision.contract_summary(_CONTRACT, PROFILE_ID)
    result["source_year_table"] = {
        branch: metrics for branch, metrics in result["source_gate"]["branches"].items()
    }
    result["target_year_table"] = {
        branch: payload["target"] for branch, payload in result["target_evaluation"]["cells"].items()
    }
    result["artifact_policy"].update(
        {
            "per_flow_scores_persisted": False,
            "per_entity_scores_persisted": False,
            "first_alert_per_entity_values_persisted": False,
            "first_alert_aggregate_curves_persisted": True,
        }
    )
    legacy.atomic_json(result_path, result)
    legacy.atomic_json(
        output_root / "source-year-metrics.json",
        {
            "schema_version": "ch3-full-mlp-bf16-source-year-metrics-v1",
            "run_id": RUN_ID,
            "dataset": "LSPR23",
            "target_year_arrays_read": 0,
            "branches": result["source_year_table"],
        },
    )
    legacy.atomic_json(
        output_root / "target-year-metrics.json",
        {
            "schema_version": "ch3-full-mlp-bf16-target-year-metrics-v1",
            "run_id": RUN_ID,
            "dataset": "LSPR24",
            "selection_sealed_before_target_load": True,
            "target_year_arrays_read": result["isolation"]["target_year_arrays_read"],
            "branches": result["target_year_table"],
        },
    )
    curve_receipt_path = output_root / "complete-alert-budget-curves-receipt.json"
    curve_receipt = legacy.load_json(curve_receipt_path)
    curve_receipt["branches"] = sorted(result["target_year_table"])
    curve_receipt["first_alert_aggregate_only"] = True
    curve_receipt["on_time_detection_curve_persisted"] = True
    curve_receipt["axis"] = "exposure_index"
    curve_receipt["exposure_index_base"] = 1
    curve_receipt["time_delay_available"] = False
    curve_receipt["artifact"] = {
        "filename": "complete-alert-budget-curves.npz",
        "bytes": (output_root / "complete-alert-budget-curves.npz").stat().st_size,
        "sha256": legacy.sha256_file(output_root / "complete-alert-budget-curves.npz"),
    }
    legacy.atomic_json(curve_receipt_path, curve_receipt)


def build_manifest(output_root: Path, run_id: str) -> None:
    _LEGACY_BUILD_MANIFEST(output_root, run_id)
    manifest = legacy.load_json(output_root / "manifest.json")
    for name in ("source-year-metrics.json", "target-year-metrics.json", "parent-selection-receipt.json"):
        path = output_root / name
        if path.is_file():
            manifest["files"][name] = {"bytes": path.stat().st_size, "sha256": legacy.sha256_file(path)}
    manifest["schema_version"] = "ch3-full-mlp-bf16-manifest-v1"
    manifest["run_id"] = RUN_ID
    manifest["precision_profile_id"] = PROFILE_ID
    manifest["per_flow_scores_persisted"] = False
    manifest["per_entity_scores_persisted"] = False
    legacy.atomic_json(output_root / "manifest.json", manifest)


def install_runtime(config: dict[str, Any], args: argparse.Namespace) -> None:
    global _ACTIVE_CONFIG, _ARGS, _CONTRACT, _PROFILE
    _ACTIVE_CONFIG = config
    _ARGS = args
    _CONTRACT = precision.load_and_validate_contract(resolve_precision_contract(config))
    _PROFILE = precision.get_profile(_CONTRACT, PROFILE_ID)
    legacy.SCHEMA_VERSION = SCHEMA_VERSION
    legacy.RESULT_SCHEMA_VERSION = RESULT_SCHEMA_VERSION
    legacy.RUN_ID = RUN_ID
    legacy.__file__ = __file__
    legacy.build_model = build_model
    legacy.predict_sequences = predict_sequences
    legacy.train_cell = train_cell
    legacy.score_target = score_target
    legacy.evaluate_entity_branch = evaluate_entity_branch
    legacy.evaluate_source_gate = evaluate_source_gate
    legacy.build_manifest = build_manifest


def run_experiment(config: dict[str, Any], args: argparse.Namespace, config_path: Path) -> None:
    global _PARENT_RECEIPT
    if legacy.torch is None or not legacy.torch.cuda.is_available():
        raise RuntimeError("BF16 资格实验要求可用 CUDA")
    assert _CONTRACT is not None
    precision.validate_runtime_profile(_CONTRACT, PROFILE_ID, "cuda", legacy.torch)
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    legacy.torch.use_deterministic_algorithms(True)
    _PARENT_RECEIPT = validate_parent_seal(config)
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    parent_path = output_root / "parent-selection-receipt.json"
    if parent_path.is_file() and legacy.load_json(parent_path) != _PARENT_RECEIPT:
        raise RuntimeError("既有父选择绑定收据与当前封印不符")
    legacy.atomic_json(parent_path, _PARENT_RECEIPT)
    started = time.time()
    legacy.run_experiment(config, args, config_path)
    _postprocess_outputs(config, output_root, started)
    build_manifest(output_root, RUN_ID)


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = legacy.load_json(config_path)
    validate_config(config)
    install_runtime(config, args)
    if args.validate_config:
        print("配置、父封印摘要与统一 BF16 静态合同核验通过")
        return 0
    try:
        if args.publish_only:
            legacy.publish_aggregate(config, args)
        else:
            run_experiment(config, args, config_path)
    except Exception as error:
        output_root = Path(config["paths"]["output_root"])
        output_root.mkdir(parents=True, exist_ok=True)
        legacy.write_status(output_root, "failed", "runtime", 1, f"{type(error).__name__}: {error}"[:1000])
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
