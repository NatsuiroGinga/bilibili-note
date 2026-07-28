"""训练共享低秩基底的单码对照或物理状态路由候选。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Literal

import torch
import torch.nn.functional as functional
import yaml

from flow_probe.bounded_physics_train import (
    FIXED_BASE_MODEL_ID,
    FIXED_DETECTION_ADAPTER,
    _adapter_parameter_digest,
    _directory_manifest,
    load_frozen_s3_model,
)
from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.physics_routed_experts import (
    EXPERT_NAMES,
    PhysicsRoutedExpertRuntime,
    RouteThresholds,
    calibrate_route_thresholds,
    hadamard_expert_codes,
)
from flow_probe.physics_train import (
    PhysicsTrainingError,
    PhysicsTrainingSettings,
    _build_settings,
    _environment_manifest,
    _generation_batch,
    _input_manifest,
    _load_jsonl,
    _sha256,
    _state_batch,
    _state_mask_sha256,
    _tracking_settings,
    _write_json,
    build_physics_prompt,
    build_state_supervision_masks,
    masked_state_target_loss,
    physics_sample_schedule,
    queue_balance_residual,
    record_step_metrics,
)
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

Variant = Literal["single", "routed"]

SCHEMA_VERSION = "physics_routed_experts_v1"
TRAINING_PHASE = "physics-routed-experts-train"
SUBTYPE_TASK = "attack_subtype"
FAMILY_TASK = "attack_family"
FORMAL_STEPS = 50
SMOKE_STEPS = 2
LEARNING_RATE = 2e-4
STATE_LOSS_WEIGHT = 1.0
PHYSICS_LOSS_WEIGHT = 0.01
MAX_GRAD_NORM = 1.0
ROUTE_ALLOWED_FIELDS = (
    "predicted_state.q4_minus_q0",
    "predicted_state.mean_q0_to_q4",
)
ROUTE_REJECTED_FIELDS = (
    "state_target",
    "queue_capacity",
    "received_throughput",
    "dequeued_throughput",
    "dropped_throughput",
    "attack_label",
    "dataset_source",
    "scenario_id",
    "unknown_attack_label",
)


@dataclass(frozen=True)
class RoutedExpertRunLayout:
    """一次单码或路由训练的完整制品布局。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    console_log: Path
    generation_sample_order: Path
    physics_sample_order: Path
    route_thresholds: Path
    routing_contract: Path
    expert_codes: Path
    step_metrics: Path
    structure_config: Path
    structure_state: Path
    expert_condition_gradients: Path
    route_usage: Path
    specialization: Path
    family_equivalence: Path
    training_summary: Path
    artifact_manifest: Path

    @classmethod
    def create(cls, output_dir: Path) -> RoutedExpertRunLayout:
        root = Path(output_dir)
        return cls(
            output_dir=root,
            config_snapshot=root / "config_snapshot.yaml",
            environment=root / "environment.json",
            input_sha256=root / "input_sha256.json",
            console_log=root / "console.log",
            generation_sample_order=root / "generation_sample_order.json",
            physics_sample_order=root / "physics_sample_order.json",
            route_thresholds=root / "route_thresholds.json",
            routing_contract=root / "routing_contract.json",
            expert_codes=root / "expert_codes.json",
            step_metrics=root / "step_metrics.jsonl",
            structure_config=root / "structure_config.json",
            structure_state=root / "structure_state.pt",
            expert_condition_gradients=root / "expert_condition_gradients.json",
            route_usage=root / "route_usage.json",
            specialization=root / "specialization.json",
            family_equivalence=root / "family_equivalence.json",
            training_summary=root / "training_summary.json",
            artifact_manifest=root / "artifact_manifest.json",
        )

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return tuple(
            value
            for name, value in self.__dict__.items()
            if name != "output_dir" and isinstance(value, Path)
        )


def _create_layout(output_dir: Path) -> RoutedExpertRunLayout:
    layout = RoutedExpertRunLayout.create(output_dir)
    if layout.output_dir.exists() or layout.output_dir.is_symlink():
        raise PhysicsTrainingError(f"输出目录必须预先不存在：{layout.output_dir}")
    layout.output_dir.mkdir(parents=True, exist_ok=False)
    return layout


def _validate_artifacts(layout: RoutedExpertRunLayout) -> None:
    missing = [str(path) for path in layout.required_paths if not path.is_file()]
    swanlog = layout.output_dir / "swanlog" / TRAINING_PHASE
    if not swanlog.is_dir():
        missing.append(str(swanlog))
    if missing:
        raise PhysicsTrainingError("共享基底专家运行制品不完整：" + ", ".join(missing))


def _validate_variant(variant: str) -> Variant:
    if variant not in {"single", "routed"}:
        raise PhysicsTrainingError("variant 只允许 single 或 routed")
    return variant


def _validate_method_config(raw_config: Mapping[str, object]) -> None:
    method = raw_config.get("method")
    if not isinstance(method, Mapping):
        raise PhysicsTrainingError("配置缺少 method")
    expected = {
        "source_layer": 13,
        "target_layers": [24, 25, 26, 27],
        "hidden_size": 2048,
        "rank": 16,
        "expert_count": 3,
        "residual_ratio_cap": 0.1,
        "route_quantile": 2.0 / 3.0,
    }
    for name, value in expected.items():
        supplied = method.get(name)
        if isinstance(value, float):
            valid = isinstance(supplied, (int, float)) and math.isclose(
                float(supplied), value, rel_tol=0.0, abs_tol=1e-12
            )
        else:
            valid = supplied == value
        if not valid:
            raise PhysicsTrainingError(f"method.{name} 必须固定为 {value}")


def _validate_settings(
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
    variant: str,
) -> Variant:
    normalized = _validate_variant(variant)
    _validate_method_config(raw_config)
    if probe.model_id != FIXED_BASE_MODEL_ID:
        raise PhysicsTrainingError(f"基座路径必须固定为 {FIXED_BASE_MODEL_ID}")
    if probe.seed != 42:
        raise PhysicsTrainingError("方向探针随机种子必须固定为 42")
    if probe.lora_rank != 16:
        raise PhysicsTrainingError("配置中的秩必须固定为 16")
    if settings.variant != "M2":
        raise PhysicsTrainingError("共享基底专家必须复用 M2 联合损失契约")
    if settings.max_steps not in {SMOKE_STEPS, FORMAL_STEPS}:
        raise PhysicsTrainingError("训练步数只允许 2 或 50")
    if settings.state_supervision_mode != "anchor0_plus_one":
        raise PhysicsTrainingError("状态监督必须固定为双锚点 anchor0_plus_one")
    fixed_values = (
        (settings.learning_rate, LEARNING_RATE, "learning_rate"),
        (settings.lambda_state, STATE_LOSS_WEIGHT, "lambda_state"),
        (settings.lambda_physics, PHYSICS_LOSS_WEIGHT, "lambda_physics"),
        (settings.max_grad_norm, MAX_GRAD_NORM, "max_grad_norm"),
    )
    for supplied, expected, name in fixed_values:
        if not math.isclose(float(supplied), expected, rel_tol=0.0, abs_tol=1e-12):
            raise PhysicsTrainingError(f"{name} 必须固定为 {expected}")
    if (
        settings.generation_batch_size != 4
        or settings.gradient_accumulation_steps != 4
        or settings.physics_batch_size != 4
        or settings.validation_batch_size != 8
    ):
        raise PhysicsTrainingError("批量必须固定为生成 4x4、物理 4、验证 8")
    if tracking.project != "malicious-traffic-llm" or tracking.workspace != "mortiswang":
        raise PhysicsTrainingError("SwanLab 必须固定为 mortiswang/malicious-traffic-llm")
    if tracking.mode != "online":
        raise PhysicsTrainingError("SwanLab 必须使用在线模式")
    return normalized


def _assert_supervised_training_records(records: Sequence[Mapping[str, object]]) -> None:
    if not records:
        raise PhysicsTrainingError("生成训练集为空")
    unexpected = sorted(
        {
            str(record.get("task"))
            for record in records
            if str(record.get("task")) not in {FAMILY_TASK, SUBTYPE_TASK}
        }
    )
    if unexpected:
        raise PhysicsTrainingError("生成训练集包含未知任务：" + ", ".join(unexpected))
    unknown = [
        str(record.get("sample_id", ""))
        for record in records
        if str(record.get("task_label")) == "unknown_attack"
    ]
    if unknown:
        raise PhysicsTrainingError("未知攻击标签不得进入训练：" + ", ".join(unknown[:10]))


def _assert_threshold_records(records: Sequence[Mapping[str, object]]) -> None:
    if not records:
        raise PhysicsTrainingError("阈值校准物理训练集为空")
    if any(str(record.get("task_label")) == "unknown_attack" for record in records):
        raise PhysicsTrainingError("未知攻击标签不得进入阈值校准")


def _write_sample_orders(
    layout: RoutedExpertRunLayout,
    generation_train: Sequence[Mapping[str, object]],
    physics_train: Sequence[Mapping[str, object]],
    generation_schedule: Sequence[Sequence[int]],
    physics_schedule: Sequence[Sequence[int]],
) -> None:
    _write_json(
        layout.generation_sample_order,
        [
            {
                "micro_step": index + 1,
                "indices": list(indices),
                "sample_ids": [generation_train[item]["sample_id"] for item in indices],
                "tasks": [generation_train[item]["task"] for item in indices],
            }
            for index, indices in enumerate(generation_schedule)
        ],
    )
    _write_json(
        layout.physics_sample_order,
        [
            {
                "step": index + 1,
                "indices": list(indices),
                "sample_ids": [physics_train[item]["sample_id"] for item in indices],
            }
            for index, indices in enumerate(physics_schedule)
        ],
    )


def _snapshot(
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
    variant: Variant,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "probe": asdict(probe),
        "training": {
            **dict(raw_config["training"]),
            "variant": variant,
            "output_dir": str(settings.output_dir),
            "max_steps": settings.max_steps,
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "validation_limit": settings.validation_limit,
        },
        "method": dict(raw_config["method"]),
        "routing_contract": {
            "allowed_fields": list(ROUTE_ALLOWED_FIELDS),
            "rejected_fields": list(ROUTE_REJECTED_FIELDS),
            "growth_precedes_pressure": True,
            "attack_family_expert_mask": False,
        },
        "tracking": {
            **dict(raw_config["tracking"]),
            "run_name": tracking.run_name,
        },
    }


def _prompt_with_sentinel_batch(
    records: Sequence[Mapping[str, object]],
    tokenizer: object,
    max_length: int,
    device: torch.device,
) -> dict[str, torch.Tensor]:
    """只从公开提示构造阈值校准输入，不读取状态或通量真值。"""

    prompts = [build_physics_prompt(record) for record in records]
    chat_prompts = [
        tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        for prompt in prompts
    ]
    encoded = tokenizer(
        chat_prompts,
        padding=True,
        truncation=True,
        max_length=max_length - 1,
        add_special_tokens=False,
        return_tensors="pt",
    )
    raw_ids = encoded["input_ids"]
    raw_attention = encoded["attention_mask"]
    sequences = [raw_ids[row][raw_attention[row].bool()] for row in range(raw_ids.shape[0])]
    width = max(sequence.shape[0] for sequence in sequences) + 1
    input_ids = torch.full(
        (len(sequences), width),
        int(tokenizer.pad_token_id),
        dtype=raw_ids.dtype,
    )
    attention_mask = torch.zeros_like(input_ids)
    labels = torch.full_like(input_ids, -100)
    for row, sequence in enumerate(sequences):
        length = sequence.shape[0]
        input_ids[row, :length] = sequence
        input_ids[row, length] = int(tokenizer.eos_token_id)
        attention_mask[row, : length + 1] = 1
        labels[row, length] = int(tokenizer.eos_token_id)
    return {
        "input_ids": input_ids.to(device),
        "attention_mask": attention_mask.to(device),
        "labels": labels.to(device),
    }


def _state_expert_batch(
    records: Sequence[Mapping[str, object]],
    tokenizer: object,
    max_length: int,
    device: torch.device,
    *,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> dict[str, object]:
    """复用物理批次后追加一个定位提示末端的监督令牌。"""

    raw = _state_batch(
        records,
        tokenizer,
        max_length - 1,
        device,
        include_fluxes=True,
        state_masks=state_masks,
    )
    raw_ids = raw["input_ids"]
    raw_attention = raw["attention_mask"]
    if not isinstance(raw_ids, torch.Tensor) or not isinstance(raw_attention, torch.Tensor):
        raise PhysicsTrainingError("物理批次缺少输入张量")
    sequences = [raw_ids[row][raw_attention[row].bool()] for row in range(raw_ids.shape[0])]
    width = max(sequence.shape[0] for sequence in sequences) + 1
    if width > max_length:
        raise PhysicsTrainingError("追加状态定位令牌后超过最大输入长度")
    input_ids = torch.full(
        (len(sequences), width),
        int(tokenizer.pad_token_id),
        dtype=raw_ids.dtype,
        device=device,
    )
    attention_mask = torch.zeros_like(input_ids)
    labels = torch.full_like(input_ids, -100)
    for row, sequence in enumerate(sequences):
        length = sequence.shape[0]
        input_ids[row, :length] = sequence
        input_ids[row, length] = int(tokenizer.eos_token_id)
        attention_mask[row, : length + 1] = 1
        labels[row, length] = int(tokenizer.eos_token_id)
    return {
        **raw,
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def _distribution_summary(values: torch.Tensor) -> dict[str, float | int]:
    data = values.detach().to(dtype=torch.float32)
    return {
        "count": int(data.numel()),
        "minimum": float(data.min().item()),
        "maximum": float(data.max().item()),
        "mean": float(data.mean().item()),
        "quantile_two_thirds": float(torch.quantile(data, 2.0 / 3.0).item()),
    }


def _calibrate_thresholds(
    model: torch.nn.Module,
    state_head: torch.nn.Module,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
) -> tuple[RouteThresholds, dict[str, object]]:
    """以专家全关的临时运行时提取冻结第 13 层预测状态。"""

    runtime = PhysicsRoutedExpertRuntime(
        model,
        state_head,
        RouteThresholds(growth=0.0, pressure=0.0),
        variant="routed",
    ).to(device=device, dtype=torch.bfloat16)
    runtime.eval()
    runtime.router_state_head.eval()
    states: list[torch.Tensor] = []
    try:
        with torch.no_grad():
            for start in range(0, len(records), batch_size):
                batch = _prompt_with_sentinel_batch(
                    records[start : start + batch_size],
                    tokenizer,
                    max_length,
                    device,
                )
                row_mask = torch.zeros(batch["input_ids"].shape[0], dtype=torch.bool, device=device)
                output = runtime(**batch, expert_row_mask=row_mask, return_dict=True)
                if output.predicted_router_state is None:
                    raise PhysicsTrainingError("阈值校准未返回冻结预测状态")
                states.append(output.predicted_router_state.detach().float().cpu())
    finally:
        runtime.close()
    predicted_state = torch.cat(states, dim=0)
    thresholds = calibrate_route_thresholds(predicted_state)
    growth = predicted_state[:, 4] - predicted_state[:, 0]
    pressure = predicted_state.mean(dim=1)
    summary = {
        "calibration_source": "frozen_router_state_head_predictions_only",
        "quantile": 2.0 / 3.0,
        "unknown_attack_labels_used": False,
        "saved_raw_predictions": False,
        "growth": _distribution_summary(growth),
        "pressure": _distribution_summary(pressure),
    }
    return thresholds, summary


def _parameter_digest(module: torch.nn.Module) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(module.state_dict().items()):
        digest.update(name.encode("utf-8"))
        digest.update(value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def _configure_trainability(
    model: torch.nn.Module,
    runtime: PhysicsRoutedExpertRuntime,
) -> tuple[torch.nn.Parameter, ...]:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
    for parameter in runtime.router_state_head.parameters():
        parameter.requires_grad_(False)
        parameter.grad = None
    for parameter in runtime.outcome_state_head.parameters():
        parameter.requires_grad_(True)
        parameter.grad = None
    for expert in runtime.experts:
        for parameter in expert.parameters():
            parameter.requires_grad_(True)
            parameter.grad = None
    leaked = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    if leaked:
        raise PhysicsTrainingError("检测到冻结 Qwen/S3 中的可训练参数：" + ", ".join(leaked))
    unexpected = [
        name
        for name, parameter in runtime.named_parameters()
        if parameter.requires_grad and not name.startswith(("outcome_state_head.", "experts."))
    ]
    if unexpected:
        raise PhysicsTrainingError("检测到白名单之外的结构参数：" + ", ".join(unexpected))
    if any(parameter.requires_grad for parameter in runtime.router_state_head.parameters()):
        raise PhysicsTrainingError("router_state_head 必须全程冻结")
    if runtime.unexpected_base_parameter_names():
        raise PhysicsTrainingError("运行时意外注册了冻结基座参数")
    trainable = runtime.trainable_parameters()
    if not trainable:
        raise PhysicsTrainingError("共享基底运行时缺少可训练参数")
    if len({id(parameter) for parameter in trainable}) != len(trainable):
        raise PhysicsTrainingError("可训练参数白名单包含重复参数")
    return trainable


def _gradient_norm(parameters: Sequence[torch.nn.Parameter]) -> float:
    total = 0.0
    for parameter in parameters:
        if parameter.grad is not None:
            gradient = parameter.grad.detach().float()
            if not bool(torch.isfinite(gradient).all().item()):
                raise PhysicsTrainingError("训练梯度包含非有限值")
            total += float(gradient.square().sum().item())
    return math.sqrt(total)


def _subtype_generation_loss(
    runtime: PhysicsRoutedExpertRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    max_length: int,
    device: torch.device,
) -> tuple[torch.Tensor, object, int, int]:
    batch = _generation_batch(records, tokenizer, max_length, device)
    subtype_rows = torch.tensor(
        [str(record.get("task")) == SUBTYPE_TASK for record in records],
        dtype=torch.bool,
        device=device,
    )
    output = runtime(
        **batch,
        expert_row_mask=subtype_rows,
        return_dict=True,
    )
    logits = output.logits
    if not isinstance(logits, torch.Tensor):
        raise PhysicsTrainingError("生成前向未返回 logits 张量")
    shifted_logits = logits[:, :-1, :].float()
    shifted_labels = batch["labels"][:, 1:]
    selected = shifted_labels.ne(-100) & subtype_rows.unsqueeze(1)
    selected_tokens = int(selected.sum().item())
    selected_samples = int(subtype_rows.sum().item())
    if selected_tokens == 0:
        return shifted_logits.sum() * 0.0, output, selected_samples, selected_tokens
    token_losses = functional.cross_entropy(
        shifted_logits.reshape(-1, shifted_logits.shape[-1]),
        shifted_labels.clamp_min(0).reshape(-1),
        reduction="none",
    ).view_as(shifted_labels)
    loss = token_losses.masked_select(selected).mean()
    return loss, output, selected_samples, selected_tokens


def _state_losses(
    output: object,
    batch: Mapping[str, object],
) -> tuple[torch.Tensor, torch.Tensor]:
    predicted = output.predicted_outcome_state
    if not isinstance(predicted, torch.Tensor):
        raise PhysicsTrainingError("物理前向未返回可训练结果状态")
    state_loss = masked_state_target_loss(
        predicted,
        batch["state_targets"],
        batch["state_mask"],
    )
    residual = queue_balance_residual(
        predicted,
        batch["scale"],
        batch["capacity"],
        batch["received"],
        batch["dequeued"],
        batch["dropped_before"],
        batch["dropped_after"],
    )
    return state_loss, residual.square().mean()


def _route_usage(route_ids: Sequence[int]) -> dict[str, object]:
    counts = [sum(int(route == expert) for route in route_ids) for expert in range(3)]
    total = sum(counts)
    rates = [count / total if total else 0.0 for count in counts]
    entropy = -sum(rate * math.log(rate) for rate in rates if rate > 0.0)
    normalized_entropy = entropy / math.log(3.0) if total else 0.0
    return {
        "expert_names": list(EXPERT_NAMES),
        "counts": counts,
        "rates": rates,
        "normalized_entropy": normalized_entropy,
        "minimum_rate": min(rates) if rates else 0.0,
        "sample_count": total,
    }


def _evaluate_generation(
    runtime: PhysicsRoutedExpertRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
) -> tuple[float, list[int]]:
    subtype_records = [record for record in records if str(record.get("task")) == SUBTYPE_TASK]
    if not subtype_records:
        raise PhysicsTrainingError("生成验证集缺少 attack_subtype 样本")
    weighted_loss = 0.0
    token_count = 0
    route_ids: list[int] = []
    runtime.eval()
    runtime.router_state_head.eval()
    with torch.no_grad():
        for start in range(0, len(subtype_records), batch_size):
            batch_records = subtype_records[start : start + batch_size]
            loss, output, _samples, tokens = _subtype_generation_loss(
                runtime,
                tokenizer,
                batch_records,
                max_length=max_length,
                device=device,
            )
            weighted_loss += float(loss.item()) * tokens
            token_count += tokens
            if output.route_ids is None:
                raise PhysicsTrainingError("生成验证未返回路由")
            route_ids.extend(int(value) for value in output.route_ids.detach().cpu().tolist())
    if token_count == 0:
        raise PhysicsTrainingError("生成验证没有可评分的子类令牌")
    return weighted_loss / token_count, route_ids


def _evaluate_physics(
    runtime: PhysicsRoutedExpertRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
    fixed_expert: int | None = None,
    removed_expert: int | None = None,
) -> tuple[dict[str, float], list[int]]:
    if not records:
        raise PhysicsTrainingError("物理验证记录为空")
    observed_error = 0.0
    observed_count = 0
    unobserved_error = 0.0
    unobserved_count = 0
    residual_error = 0.0
    residual_count = 0
    route_ids: list[int] = []
    runtime.eval()
    runtime.router_state_head.eval()
    with torch.no_grad():
        for start in range(0, len(records), batch_size):
            batch_records = records[start : start + batch_size]
            batch = _state_expert_batch(
                batch_records,
                tokenizer,
                max_length,
                device,
                state_masks=state_masks,
            )
            row_mask = torch.ones(len(batch_records), dtype=torch.bool, device=device)
            output = runtime(
                input_ids=batch["input_ids"],
                attention_mask=batch["attention_mask"],
                labels=batch["labels"],
                expert_row_mask=row_mask,
                fixed_expert=fixed_expert,
                removed_expert=removed_expert,
                return_dict=True,
            )
            predicted = output.predicted_outcome_state
            if not isinstance(predicted, torch.Tensor) or output.route_ids is None:
                raise PhysicsTrainingError("物理验证缺少结果状态或路由")
            target = batch["state_targets"]
            mask = batch["state_mask"].to(dtype=torch.bool)
            squared = (predicted.float() - target.float()).square()
            observed_error += float(squared.masked_select(mask).sum().item())
            observed_count += int(mask.sum().item())
            unobserved_error += float(squared.masked_select(~mask).sum().item())
            unobserved_count += int((~mask).sum().item())
            residual = queue_balance_residual(
                predicted,
                batch["scale"],
                batch["capacity"],
                batch["received"],
                batch["dequeued"],
                batch["dropped_before"],
                batch["dropped_after"],
            )
            residual_error += float(residual.square().sum().item())
            residual_count += residual.numel()
            route_ids.extend(int(value) for value in output.route_ids.detach().cpu().tolist())
    if not observed_count or not unobserved_count or not residual_count:
        raise PhysicsTrainingError("物理验证缺少观测、未观测或残差元素")
    return (
        {
            "state_mse_observed": observed_error / observed_count,
            "state_mse_unobserved": unobserved_error / unobserved_count,
            "physics_residual_mse": residual_error / residual_count,
        },
        route_ids,
    )


def _collect_physics_routes(
    runtime: PhysicsRoutedExpertRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> list[int]:
    _metrics, routes = _evaluate_physics(
        runtime,
        tokenizer,
        records,
        batch_size=batch_size,
        max_length=max_length,
        device=device,
        state_masks=state_masks,
    )
    return routes


def _expert_condition_gradient(
    runtime: PhysicsRoutedExpertRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    expert: int,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> float:
    batch_records = records[:8]
    batch = _state_expert_batch(
        batch_records,
        tokenizer,
        max_length,
        device,
        state_masks=state_masks,
    )
    row_mask = torch.ones(len(batch_records), dtype=torch.bool, device=device)
    output = runtime(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        labels=batch["labels"],
        expert_row_mask=row_mask,
        fixed_expert=expert,
        return_dict=True,
    )
    state_loss, physics_loss = _state_losses(output, batch)
    joint = state_loss + PHYSICS_LOSS_WEIGHT * physics_loss
    basis_parameters = runtime.shared_basis_parameters()
    gradients = torch.autograd.grad(
        joint,
        basis_parameters,
        allow_unused=True,
        retain_graph=False,
    )
    square_sum = 0.0
    for gradient in gradients:
        if gradient is not None:
            square_sum += float(gradient.detach().float().square().sum().item())
    return math.sqrt(square_sum)


def _specialization_audit(
    runtime: PhysicsRoutedExpertRuntime,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
) -> tuple[dict[str, object], dict[str, object]]:
    routes = _collect_physics_routes(
        runtime,
        tokenizer,
        records,
        batch_size=batch_size,
        max_length=max_length,
        device=device,
        state_masks=state_masks,
    )
    groups = [
        [record for record, route in zip(records, routes, strict=True) if route == condition]
        for condition in range(3)
    ]
    matrix: list[list[float | None]] = []
    row_diagonal_best: list[bool] = []
    diagonal_margins: list[float | None] = []
    removal_degradation: list[float | None] = []
    gradient_norms: list[float] = []
    for condition, group in enumerate(groups):
        if not group:
            matrix.append([None, None, None])
            row_diagonal_best.append(False)
            diagonal_margins.append(None)
            removal_degradation.append(None)
            gradient_norms.append(0.0)
            continue
        row: list[float | None] = []
        state_losses: list[float] = []
        for expert in range(3):
            metrics, _routes = _evaluate_physics(
                runtime,
                tokenizer,
                group,
                batch_size=batch_size,
                max_length=max_length,
                device=device,
                state_masks=state_masks,
                fixed_expert=expert,
            )
            state_losses.append(metrics["state_mse_observed"])
            row.append(
                metrics["state_mse_observed"]
                + PHYSICS_LOSS_WEIGHT * metrics["physics_residual_mse"]
            )
        matrix.append(row)
        diagonal = float(row[condition])
        off_diagonal = [float(value) for index, value in enumerate(row) if index != condition]
        margin = min(off_diagonal) - diagonal
        diagonal_margins.append(margin)
        row_diagonal_best.append(margin > 0.0)
        removed, _routes = _evaluate_physics(
            runtime,
            tokenizer,
            group,
            batch_size=batch_size,
            max_length=max_length,
            device=device,
            state_masks=state_masks,
            fixed_expert=condition,
            removed_expert=condition,
        )
        removal_degradation.append(removed["state_mse_observed"] - state_losses[condition])
        gradient_norms.append(
            _expert_condition_gradient(
                runtime,
                tokenizer,
                group,
                expert=condition,
                max_length=max_length,
                device=device,
                state_masks=state_masks,
            )
        )
    group_counts = [len(group) for group in groups]
    specialization = {
        "expert_names": list(EXPERT_NAMES),
        "condition_group_counts": group_counts,
        "joint_loss_matrix": matrix,
        "row_diagonal_best": row_diagonal_best,
        "diagonal_margins": diagonal_margins,
        "corresponding_expert_removal_state_loss_degradation": removal_degradation,
        "all_conditions_present": all(count > 0 for count in group_counts),
        "all_diagonal_best": all(row_diagonal_best),
        "all_removals_degrade": all(
            value is not None and value > 0.0 for value in removal_degradation
        ),
    }
    specialization["pass"] = bool(
        specialization["all_conditions_present"]
        and specialization["all_diagonal_best"]
        and specialization["all_removals_degrade"]
    )
    gradient_evidence = {
        "evidence_name": "expert_condition_gradient",
        "parameter_scope": "four_layer_shared_A_B",
        "independent_expert_parameter_updates_claimed": False,
        "expert_names": list(EXPERT_NAMES),
        "gradient_norms": gradient_norms,
        "all_nonzero": all(value > 0.0 for value in gradient_norms),
    }
    return specialization, gradient_evidence


def _max_abs_difference(left: torch.Tensor, right: torch.Tensor) -> float:
    if left.shape != right.shape:
        raise PhysicsTrainingError("逻辑值等价性比较形状不一致")
    return float((left.float() - right.float()).abs().max().item())


def _direct_logits(
    model: torch.nn.Module,
    tokenizer: object,
    record: Mapping[str, object],
    *,
    max_length: int,
    device: torch.device,
) -> torch.Tensor:
    batch = _generation_batch([record], tokenizer, max_length, device)
    with torch.no_grad():
        output = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            labels=batch["labels"],
            return_dict=True,
        )
    return output.logits.detach().float().cpu()


def _runtime_family_logits(
    runtime: PhysicsRoutedExpertRuntime,
    tokenizer: object,
    record: Mapping[str, object],
    *,
    max_length: int,
    device: torch.device,
) -> torch.Tensor:
    batch = _generation_batch([record], tokenizer, max_length, device)
    row_mask = torch.zeros(1, dtype=torch.bool, device=device)
    with torch.no_grad():
        output = runtime(
            **batch,
            expert_row_mask=row_mask,
            return_dict=True,
        )
    return output.logits.detach().float().cpu()


def _budget_audit(runtime: PhysicsRoutedExpertRuntime) -> dict[str, object]:
    basis_count = sum(parameter.numel() for parameter in runtime.shared_basis_parameters())
    gate_count = sum(expert.alpha.numel() for expert in runtime.experts)
    outcome_count = sum(parameter.numel() for parameter in runtime.outcome_state_head.parameters())
    router_count = sum(parameter.numel() for parameter in runtime.router_state_head.parameters())
    trainable_count = sum(parameter.numel() for parameter in runtime.trainable_parameters())
    return {
        "target_layers": [24, 25, 26, 27],
        "rank_per_layer": 16,
        "rank_sum": 64,
        "full_rank_channels_activated_per_forward": 16,
        "shared_basis_parameter_count": basis_count,
        "gate_parameter_count": gate_count,
        "outcome_state_head_parameter_count": outcome_count,
        "frozen_router_state_head_parameter_count": router_count,
        "trainable_parameter_count": trainable_count,
        "expected_trainable_parameter_count": basis_count + gate_count + outcome_count,
        "codes_are_parameters": False,
        "three_independent_lora_experts": False,
    }


def train_physics_routed_expert_variant(
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
    detection_adapter_path: Path,
    variant: Literal["single", "routed"],
) -> dict[str, object]:
    """执行固定种子 42、2 或 50 步的共享基底专家方向探针。"""

    normalized_variant = _validate_settings(
        probe,
        settings,
        tracking,
        raw_config,
        variant,
    )
    if Path(detection_adapter_path) != FIXED_DETECTION_ADAPTER:
        raise PhysicsTrainingError(f"S3 路径必须固定为 {FIXED_DETECTION_ADAPTER}")
    layout = _create_layout(settings.output_dir)
    generation_train = _load_jsonl(settings.generation_train_file)
    generation_validation = _load_jsonl(settings.generation_validation_file)
    physics_train = _load_jsonl(settings.physics_train_file)
    physics_validation = _load_jsonl(settings.physics_validation_file)
    _assert_supervised_training_records(generation_train)
    _assert_threshold_records(physics_train)
    if settings.validation_limit is not None:
        generation_validation = generation_validation[: settings.validation_limit]
        physics_validation = physics_validation[: settings.validation_limit]
    if not physics_validation:
        raise PhysicsTrainingError("物理验证集为空")
    family_records = [
        record for record in generation_train if str(record.get("task")) == FAMILY_TASK
    ]
    if not family_records:
        raise PhysicsTrainingError("训练集缺少 attack_family 路径审计样本")

    generation_schedule = physics_sample_schedule(
        len(generation_train),
        batch_size=settings.generation_batch_size,
        steps=settings.max_steps * settings.gradient_accumulation_steps,
        seed=probe.seed,
    )
    physics_schedule = physics_sample_schedule(
        len(physics_train),
        batch_size=settings.physics_batch_size,
        steps=settings.max_steps,
        seed=probe.seed,
    )
    train_state_masks = build_state_supervision_masks(
        physics_train,
        settings.state_supervision_mode,
        probe.seed,
    )
    validation_state_masks = build_state_supervision_masks(
        physics_validation,
        settings.state_supervision_mode,
        probe.seed,
    )
    _write_sample_orders(
        layout,
        generation_train,
        physics_train,
        generation_schedule,
        physics_schedule,
    )
    snapshot = _snapshot(probe, settings, tracking, raw_config, normalized_variant)
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )
    _write_json(layout.environment, _environment_manifest())
    input_manifest = _input_manifest(settings)
    input_manifest["detection_adapter"] = _directory_manifest(detection_adapter_path)
    state_head_path = detection_adapter_path.parent / "state_head.pt"
    input_manifest["s3_state_head"] = {
        "path": str(state_head_path),
        "sha256": _sha256(state_head_path),
        "bytes": state_head_path.stat().st_size,
    }
    _write_json(layout.input_sha256, input_manifest)
    _write_json(
        layout.routing_contract,
        {
            "schema_version": SCHEMA_VERSION,
            "router_function_input": "predicted_state[B,5]",
            "allowed_fields": list(ROUTE_ALLOWED_FIELDS),
            "rejected_fields": list(ROUTE_REJECTED_FIELDS),
            "growth_rule": "q4-q0 >= fixed_two_thirds_quantile",
            "pressure_rule": "mean(q0..q4) >= fixed_two_thirds_quantile",
            "precedence": ["accumulating", "saturated", "steady"],
            "family_expert_mask_fixed_false": True,
            "unknown_attack_labels_in_training_or_calibration": False,
        },
    )
    codes = hadamard_expert_codes()
    _write_json(
        layout.expert_codes,
        {
            "schema_version": SCHEMA_VERSION,
            "single_code": [1.0] * 16,
            "routed_codes": codes.tolist(),
            "pairwise_inner_products": (codes @ codes.transpose(0, 1)).tolist(),
            "full_support": bool((codes != 0).all().item()),
            "codes_are_parameters": False,
        },
    )

    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "generation_sample_order": layout.generation_sample_order,
        "physics_sample_order": layout.physics_sample_order,
        "route_thresholds": layout.route_thresholds,
        "routing_contract": layout.routing_contract,
        "expert_codes": layout.expert_codes,
        "step_metrics": layout.step_metrics,
        "structure_config": layout.structure_config,
        "structure_state": layout.structure_state,
        "expert_condition_gradients": layout.expert_condition_gradients,
        "route_usage": layout.route_usage,
        "specialization": layout.specialization,
        "family_equivalence": layout.family_equivalence,
        "training_summary": layout.training_summary,
    }
    started = time.perf_counter()
    runtime: PhysicsRoutedExpertRuntime | None = None
    with (
        capture_console_log(layout.console_log),
        swanlab_run(
            settings=tracking,
            phase=TRAINING_PHASE,
            config=snapshot,
            artifact_dir=layout.output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        torch.manual_seed(probe.seed)
        torch.cuda.manual_seed_all(probe.seed)
        torch.cuda.reset_peak_memory_stats()
        tokenizer, model, s3_state_head, checkpoint_audit = load_frozen_s3_model(
            probe,
            detection_adapter_path,
        )
        device = next(model.parameters()).device
        thresholds, calibration_summary = _calibrate_thresholds(
            model,
            s3_state_head,
            tokenizer,
            physics_train,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
        )
        _write_json(
            layout.route_thresholds,
            {
                "schema_version": SCHEMA_VERSION,
                "growth": thresholds.growth,
                "pressure": thresholds.pressure,
                "calibration": calibration_summary,
            },
        )
        torch.manual_seed(probe.seed)
        runtime = PhysicsRoutedExpertRuntime(
            model,
            s3_state_head,
            thresholds,
            variant=normalized_variant,
        ).to(device=device, dtype=torch.bfloat16)
        try:
            model.eval()
            runtime.train()
            runtime.router_state_head.eval()
            trainable = _configure_trainability(model, runtime)
            budget = _budget_audit(runtime)
            if budget["trainable_parameter_count"] != budget["expected_trainable_parameter_count"]:
                raise PhysicsTrainingError("共享基底专家可训练参数预算不一致")
            detection_digest_before = _adapter_parameter_digest(model)
            router_digest_before = _parameter_digest(runtime.router_state_head)
            direct_family_before = _direct_logits(
                model,
                tokenizer,
                family_records[0],
                max_length=probe.max_input_length,
                device=device,
            )
            routed_family_before = _runtime_family_logits(
                runtime,
                tokenizer,
                family_records[0],
                max_length=probe.max_input_length,
                device=device,
            )
            initial_family_difference = _max_abs_difference(
                direct_family_before,
                routed_family_before,
            )
            if initial_family_difference > 1e-6:
                raise PhysicsTrainingError("攻击大类专家掩码未保持冻结 S3 等价")

            optimizer = torch.optim.AdamW(
                trainable,
                lr=settings.learning_rate,
                weight_decay=0.0,
            )
            basis_parameters = runtime.shared_basis_parameters()
            gate_parameters = tuple(expert.alpha for expert in runtime.experts)
            outcome_parameters = tuple(runtime.outcome_state_head.parameters())
            nonzero_basis_gradient_steps = 0
            nonzero_gate_gradient_steps = 0
            nonzero_outcome_gradient_steps = 0
            for step in range(1, settings.max_steps + 1):
                step_started = time.perf_counter()
                optimizer.zero_grad(set_to_none=True)
                generation_loss_sum = 0.0
                subtype_samples = 0
                subtype_tokens = 0
                generation_route_counts = [0, 0, 0]
                micro_start = (step - 1) * settings.gradient_accumulation_steps
                for micro in range(settings.gradient_accumulation_steps):
                    indices = generation_schedule[micro_start + micro]
                    records = [generation_train[index] for index in indices]
                    generation_loss, output, samples, tokens = _subtype_generation_loss(
                        runtime,
                        tokenizer,
                        records,
                        max_length=probe.max_input_length,
                        device=device,
                    )
                    generation_loss_sum += float(generation_loss.detach().item())
                    subtype_samples += samples
                    subtype_tokens += tokens
                    if output.route_ids is not None:
                        for route, active in zip(
                            output.route_ids.detach().cpu().tolist(),
                            [str(record.get("task")) == SUBTYPE_TASK for record in records],
                            strict=True,
                        ):
                            if active:
                                generation_route_counts[int(route)] += 1
                    if tokens > 0:
                        (generation_loss / settings.gradient_accumulation_steps).backward()
                generation_loss_value = generation_loss_sum / settings.gradient_accumulation_steps

                physics_indices = physics_schedule[step - 1]
                physics_records = [physics_train[index] for index in physics_indices]
                state_batch = _state_expert_batch(
                    physics_records,
                    tokenizer,
                    probe.max_input_length,
                    device,
                    state_masks=train_state_masks,
                )
                active_physics = torch.ones(len(physics_records), dtype=torch.bool, device=device)
                state_output = runtime(
                    input_ids=state_batch["input_ids"],
                    attention_mask=state_batch["attention_mask"],
                    labels=state_batch["labels"],
                    expert_row_mask=active_physics,
                    return_dict=True,
                )
                state_loss, physics_loss = _state_losses(state_output, state_batch)
                auxiliary = (
                    settings.lambda_state * state_loss + settings.lambda_physics * physics_loss
                )
                auxiliary.backward()
                basis_gradient_norm = _gradient_norm(basis_parameters)
                gate_gradient_norm = _gradient_norm(gate_parameters)
                outcome_gradient_norm = _gradient_norm(outcome_parameters)
                nonzero_basis_gradient_steps += int(basis_gradient_norm > 0.0)
                nonzero_gate_gradient_steps += int(gate_gradient_norm > 0.0)
                nonzero_outcome_gradient_steps += int(outcome_gradient_norm > 0.0)
                total_gradient_norm = _gradient_norm(trainable)
                torch.nn.utils.clip_grad_norm_(trainable, settings.max_grad_norm)
                optimizer.step()

                physics_route_counts = [0, 0, 0]
                if state_output.route_ids is None:
                    raise PhysicsTrainingError("物理训练前向未返回路由")
                for route in state_output.route_ids.detach().cpu().tolist():
                    physics_route_counts[int(route)] += 1
                elapsed = time.perf_counter() - step_started
                metrics = {
                    "train/total_loss": (
                        generation_loss_value
                        + settings.lambda_state * float(state_loss.detach().item())
                        + settings.lambda_physics * float(physics_loss.detach().item())
                    ),
                    "train/generation_loss": generation_loss_value,
                    "train/state_loss": float(state_loss.detach().item()),
                    "train/physics_loss": float(physics_loss.detach().item()),
                    "train/lora_gradient_norm": total_gradient_norm,
                    "train/state_head_gradient_norm": outcome_gradient_norm,
                    "train/shared_basis_gradient_norm": basis_gradient_norm,
                    "train/gate_gradient_norm": gate_gradient_norm,
                    "train/subtype_samples": float(subtype_samples),
                    "train/subtype_tokens": float(subtype_tokens),
                    "train/generation_route_steady": float(generation_route_counts[0]),
                    "train/generation_route_accumulating": float(generation_route_counts[1]),
                    "train/generation_route_saturated": float(generation_route_counts[2]),
                    "train/physics_route_steady": float(physics_route_counts[0]),
                    "train/physics_route_accumulating": float(physics_route_counts[1]),
                    "train/physics_route_saturated": float(physics_route_counts[2]),
                    "train/max_residual_ratio": state_output.diagnostics.max_residual_ratio,
                    "train/learning_rate": settings.learning_rate,
                    "train/throughput_samples_per_second": (
                        settings.effective_generation_batch_size + settings.physics_batch_size
                    )
                    / elapsed,
                    "train/peak_gpu_memory_mib": (torch.cuda.max_memory_allocated() / (1024**2)),
                }
                record_step_metrics(
                    layout.step_metrics,
                    swanlab,
                    step=step,
                    metrics=metrics,
                )
                print(json.dumps({"step": step, **metrics}, ensure_ascii=False, sort_keys=True))

            detection_digest_after = _adapter_parameter_digest(model)
            router_digest_after = _parameter_digest(runtime.router_state_head)
            if detection_digest_after != detection_digest_before:
                raise PhysicsTrainingError("冻结 S3 检测适配器在训练后发生变化")
            if router_digest_after != router_digest_before:
                raise PhysicsTrainingError("冻结 router_state_head 在训练后发生变化")

            direct_family_after = _direct_logits(
                model,
                tokenizer,
                family_records[0],
                max_length=probe.max_input_length,
                device=device,
            )
            routed_family_after = _runtime_family_logits(
                runtime,
                tokenizer,
                family_records[0],
                max_length=probe.max_input_length,
                device=device,
            )
            family_equivalence = {
                "sample_id": family_records[0]["sample_id"],
                "expert_row_mask": False,
                "direct_before_vs_runtime_before_max_abs_logits": initial_family_difference,
                "direct_before_vs_direct_after_max_abs_logits": _max_abs_difference(
                    direct_family_before,
                    direct_family_after,
                ),
                "direct_after_vs_runtime_after_max_abs_logits": _max_abs_difference(
                    direct_family_after,
                    routed_family_after,
                ),
                "detection_adapter_sha256_before": detection_digest_before,
                "detection_adapter_sha256_after": detection_digest_after,
                "router_state_head_sha256_before": router_digest_before,
                "router_state_head_sha256_after": router_digest_after,
            }
            family_equivalence["maximum_difference"] = max(
                float(family_equivalence[key])
                for key in (
                    "direct_before_vs_runtime_before_max_abs_logits",
                    "direct_before_vs_direct_after_max_abs_logits",
                    "direct_after_vs_runtime_after_max_abs_logits",
                )
            )
            family_equivalence["within_1e-6"] = family_equivalence["maximum_difference"] <= 1e-6
            _write_json(layout.family_equivalence, family_equivalence)

            generation_validation_loss, generation_routes = _evaluate_generation(
                runtime,
                tokenizer,
                generation_validation,
                batch_size=settings.validation_batch_size,
                max_length=probe.max_input_length,
                device=device,
            )
            physics_metrics, physics_routes = _evaluate_physics(
                runtime,
                tokenizer,
                physics_validation,
                batch_size=settings.validation_batch_size,
                max_length=probe.max_input_length,
                device=device,
                state_masks=validation_state_masks,
            )
            route_usage = {
                "subtype_generation_validation": _route_usage(generation_routes),
                "physics_validation": _route_usage(physics_routes),
            }
            _write_json(layout.route_usage, route_usage)
            specialization, gradient_evidence = _specialization_audit(
                runtime,
                tokenizer,
                physics_validation,
                batch_size=settings.validation_batch_size,
                max_length=probe.max_input_length,
                device=device,
                state_masks=validation_state_masks,
            )
            _write_json(layout.specialization, specialization)
            _write_json(layout.expert_condition_gradients, gradient_evidence)

            structure_config = {
                "schema_version": SCHEMA_VERSION,
                "variant": normalized_variant,
                "budget": budget,
                "trainable_parameter_names": list(runtime.trainable_parameter_names()),
                "frozen_router_parameter_names": [
                    name
                    for name, _parameter in runtime.router_state_head.named_parameters(
                        prefix="router_state_head"
                    )
                ],
                "route_thresholds": asdict(thresholds),
                "gate_values": [
                    float(
                        (
                            expert.residual_ratio_cap * torch.tanh(expert.alpha.detach().float())
                        ).item()
                    )
                    for expert in runtime.experts
                ],
                "residual_ratio_cap": 0.1,
                "same_A_B_rank_parameter_and_activation_budget_across_variants": True,
            }
            _write_json(layout.structure_config, structure_config)
            torch.save(
                {
                    name: value.detach().cpu()
                    for name, value in runtime.structure_state_dict().items()
                },
                layout.structure_state,
            )
            saved_state = torch.load(
                layout.structure_state,
                map_location="cpu",
                weights_only=True,
            )
            runtime.load_structure_state_dict(saved_state, strict=True)

            sample_order = {
                "generation_sha256": _sha256(layout.generation_sample_order),
                "physics_sha256": _sha256(layout.physics_sample_order),
            }
            summary = {
                "schema_version": SCHEMA_VERSION,
                "status": "finished",
                "variant": normalized_variant,
                "seed": probe.seed,
                "max_steps": settings.max_steps,
                "formal_probe": settings.max_steps == FORMAL_STEPS,
                "model_id": probe.model_id,
                "detection_adapter_path": str(detection_adapter_path),
                "checkpoint_audit": checkpoint_audit,
                "training": {
                    "learning_rate": settings.learning_rate,
                    "effective_generation_batch_size": settings.effective_generation_batch_size,
                    "physics_batch_size": settings.physics_batch_size,
                    "validation_batch_size": settings.validation_batch_size,
                    "state_supervision_mode": settings.state_supervision_mode,
                    "state_mask_sha256": _state_mask_sha256(train_state_masks),
                    "lambda_state": settings.lambda_state,
                    "lambda_physics": settings.lambda_physics,
                    "max_grad_norm": settings.max_grad_norm,
                    "nonzero_shared_basis_gradient_steps": nonzero_basis_gradient_steps,
                    "nonzero_gate_gradient_steps": nonzero_gate_gradient_steps,
                    "nonzero_outcome_state_head_gradient_steps": (nonzero_outcome_gradient_steps),
                },
                "sample_order": sample_order,
                "route_thresholds": asdict(thresholds),
                "routing_contract": {
                    "allowed_fields": list(ROUTE_ALLOWED_FIELDS),
                    "rejected_fields": list(ROUTE_REJECTED_FIELDS),
                    "unknown_attack_labels_used": False,
                    "family_expert_mask_fixed_false": True,
                },
                "budget": budget,
                "validation": {
                    "subtype_generation_loss": generation_validation_loss,
                    **physics_metrics,
                },
                "route_usage": route_usage,
                "specialization": specialization,
                "expert_condition_gradients": gradient_evidence,
                "family_equivalence": family_equivalence,
                "runtime_seconds": time.perf_counter() - started,
                "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            }
            _write_json(layout.training_summary, summary)
            swanlab.log(
                {
                    "validation/subtype_generation_loss": generation_validation_loss,
                    "validation/state_mse_observed": physics_metrics["state_mse_observed"],
                    "validation/state_mse_unobserved": physics_metrics["state_mse_unobserved"],
                    "validation/physics_residual_mse": physics_metrics["physics_residual_mse"],
                    "validation/family_max_abs_logits": family_equivalence["maximum_difference"],
                    "validation/specialization_pass": float(specialization["pass"]),
                    "validation/expert_condition_gradients_pass": float(
                        gradient_evidence["all_nonzero"]
                    ),
                },
                step=settings.max_steps + 1,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        finally:
            runtime.close()
    _validate_artifacts(layout)
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _build_probe_settings(
    raw: Mapping[str, object],
    *,
    output_dir: Path,
    max_steps: int,
    validation_limit: int | None,
) -> PhysicsTrainingSettings:
    reused = _build_settings(
        raw,
        variant="M2",
        output_dir=output_dir,
        max_steps=max_steps,
        validation_limit=validation_limit,
        lambda_physics_override=PHYSICS_LOSS_WEIGHT,
        state_supervision_mode_override="anchor0_plus_one",
    )
    return replace(reused, variant="M2")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="训练共享低秩基底的物理状态编码专家")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--variant", choices=("single", "routed"), required=True)
    parser.add_argument("--detection-adapter-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-steps", type=int, choices=(SMOKE_STEPS, FORMAL_STEPS), required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--validation-limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise PhysicsTrainingError("配置根节点必须是映射")
    probe_data = raw.get("probe")
    if not isinstance(probe_data, Mapping):
        raise PhysicsTrainingError("配置缺少 probe")
    probe = ProbeConfig.from_mapping(probe_data)
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_probe_settings(
        raw,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        validation_limit=args.validation_limit,
    )
    tracking = _tracking_settings(raw, args.run_name)
    manifest = train_physics_routed_expert_variant(
        probe,
        settings,
        tracking,
        raw,
        args.detection_adapter_path,
        args.variant,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
