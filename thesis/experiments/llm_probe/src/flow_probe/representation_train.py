"""运行 B0/B1 物理表征显式耦合探针训练。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.physics_train import (
    ContinuousQueueStateHead,
    _environment_manifest,
    _generation_batch,
    _load_jsonl,
    _load_model,
    _state_batch,
    _state_mask_sha256,
    _write_json,
    build_state_supervision_masks,
    masked_state_target_loss,
    physics_sample_schedule,
    queue_balance_residual,
)
from flow_probe.qwen_physics_gradient import select_last_token_hidden
from flow_probe.representation_coupling import (
    VARIANTS,
    CoupledGenerationOutput,
    PhysicalRepresentationCoupling,
    coupled_generation_forward,
    decoder_last_hidden,
    normalize_variant,
    perturbed_supervised_logit_delta,
)
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

PHASE = "representation-train"
STATE_SUPERVISION_MODE = "anchor0_plus_one"
ALLOWED_STEPS = (2, 50)


class RepresentationTrainingError(ValueError):
    """任务十六训练配置、数据或运行制品不满足冻结契约。"""


@dataclass(frozen=True)
class RepresentationTrainingSettings:
    """B0/B1 共享的固定数据、预算和损失设置。"""

    variant: str
    output_dir: Path
    generation_train_file: Path
    generation_validation_file: Path
    physics_train_file: Path
    physics_validation_file: Path
    physics_test_file: Path
    learning_rate: float
    generation_batch_size: int
    gradient_accumulation_steps: int
    physics_batch_size: int
    validation_batch_size: int
    max_steps: int
    state_supervision_mode: str
    lambda_state: float
    lambda_physics: float
    max_grad_norm: float
    validation_limit: int | None

    @property
    def effective_generation_batch_size(self) -> int:
        return self.generation_batch_size * self.gradient_accumulation_steps


@dataclass(frozen=True)
class RepresentationRunLayout:
    """一次表征耦合运行必须持久化的完整制品。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_manifest: Path
    console_log: Path
    step_metrics: Path
    training_summary: Path
    final_adapter: Path
    state_head: Path
    coupling: Path
    sample_order: Path
    state_mask: Path
    validation_predictions: Path
    artifact_manifest: Path

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return (
            self.config_snapshot,
            self.environment,
            self.input_manifest,
            self.console_log,
            self.step_metrics,
            self.training_summary,
            self.final_adapter,
            self.state_head,
            self.coupling,
            self.sample_order,
            self.state_mask,
            self.validation_predictions,
            self.artifact_manifest,
        )


def create_run_layout(output_dir: Path) -> RepresentationRunLayout:
    """创建不可复用且位于 representation-coupling 下的运行目录。"""
    output_dir = Path(output_dir)
    if "representation-coupling" not in output_dir.parts:
        raise RepresentationTrainingError("输出目录必须位于 runs/representation-coupling/ 下")
    output_dir.mkdir(parents=True, exist_ok=False)
    return RepresentationRunLayout(
        output_dir=output_dir,
        config_snapshot=output_dir / "config_snapshot.yaml",
        environment=output_dir / "environment.json",
        input_manifest=output_dir / "input_manifest.json",
        console_log=output_dir / "console.log",
        step_metrics=output_dir / "step_metrics.jsonl",
        training_summary=output_dir / "training_summary.json",
        final_adapter=output_dir / "final_adapter",
        state_head=output_dir / "state_head.pt",
        coupling=output_dir / "representation_coupling.pt",
        sample_order=output_dir / "sample_order.json",
        state_mask=output_dir / "state_mask.json",
        validation_predictions=output_dir / "validation_predictions.jsonl",
        artifact_manifest=output_dir / "artifact_manifest.json",
    )


def validate_completed_artifacts(layout: RepresentationRunLayout) -> None:
    """只有全部强制制品存在时才允许报告运行完成。"""
    missing = [str(path) for path in layout.required_paths if not path.exists()]
    if missing:
        raise RepresentationTrainingError("运行制品不完整：" + ", ".join(missing))


def _build_settings(
    raw: Mapping[str, object],
    *,
    variant: str,
    output_dir: Path,
    max_steps: int,
    validation_limit: int | None,
) -> RepresentationTrainingSettings:
    data = raw.get("training")
    if not isinstance(data, Mapping):
        raise RepresentationTrainingError("配置缺少 training")
    required = (
        "generation_train_file",
        "generation_validation_file",
        "physics_train_file",
        "physics_validation_file",
        "physics_test_file",
        "learning_rate",
        "generation_batch_size",
        "gradient_accumulation_steps",
        "physics_batch_size",
        "validation_batch_size",
        "state_supervision_mode",
        "lambda_state",
        "lambda_physics",
        "max_grad_norm",
    )
    missing = [name for name in required if name not in data]
    if missing:
        raise RepresentationTrainingError("缺少训练配置：" + ", ".join(missing))
    settings = RepresentationTrainingSettings(
        variant=normalize_variant(variant),
        output_dir=Path(output_dir),
        generation_train_file=Path(str(data["generation_train_file"])),
        generation_validation_file=Path(str(data["generation_validation_file"])),
        physics_train_file=Path(str(data["physics_train_file"])),
        physics_validation_file=Path(str(data["physics_validation_file"])),
        physics_test_file=Path(str(data["physics_test_file"])),
        learning_rate=float(data["learning_rate"]),
        generation_batch_size=int(data["generation_batch_size"]),
        gradient_accumulation_steps=int(data["gradient_accumulation_steps"]),
        physics_batch_size=int(data["physics_batch_size"]),
        validation_batch_size=int(data["validation_batch_size"]),
        max_steps=int(max_steps),
        state_supervision_mode=str(data["state_supervision_mode"]).lower(),
        lambda_state=float(data["lambda_state"]),
        lambda_physics=float(data["lambda_physics"]),
        max_grad_norm=float(data["max_grad_norm"]),
        validation_limit=validation_limit,
    )
    positive = (
        settings.learning_rate,
        settings.generation_batch_size,
        settings.gradient_accumulation_steps,
        settings.physics_batch_size,
        settings.validation_batch_size,
        settings.max_grad_norm,
    )
    if any(not math.isfinite(float(value)) or value <= 0 for value in positive):
        raise RepresentationTrainingError("批量、学习率和梯度上限必须为有限正数")
    if settings.max_steps not in ALLOWED_STEPS:
        raise RepresentationTrainingError("表征耦合探针只允许 2 步冒烟或 50 步探索")
    if settings.effective_generation_batch_size != 16:
        raise RepresentationTrainingError("生成有效批量大小必须固定为 16")
    if settings.physics_batch_size != 4:
        raise RepresentationTrainingError("物理批量大小必须固定为 4")
    if settings.state_supervision_mode != STATE_SUPERVISION_MODE:
        raise RepresentationTrainingError("状态监督必须固定为 anchor0_plus_one")
    if not math.isclose(settings.lambda_state, 1.0, rel_tol=0.0, abs_tol=0.0):
        raise RepresentationTrainingError("状态损失权重必须固定为 1.0")
    if not math.isclose(settings.lambda_physics, 0.01, rel_tol=0.0, abs_tol=0.0):
        raise RepresentationTrainingError("物理损失权重必须固定为 0.01")
    if validation_limit is not None and validation_limit <= 0:
        raise RepresentationTrainingError("验证样本上限必须大于零")
    return settings


def _tracking_settings(raw: Mapping[str, object], run_name: str, variant: str) -> TrackingSettings:
    tracking = raw.get("tracking")
    if not isinstance(tracking, Mapping):
        raise RepresentationTrainingError("配置缺少 tracking")
    tags = tracking.get("tags")
    if not isinstance(tags, (list, tuple)):
        raise RepresentationTrainingError("tracking.tags 必须是列表")
    normalized_tags = list(dict.fromkeys([*tags, "repr-coupling", variant.lower()]))
    return TrackingSettings.from_mapping(
        {
            **tracking,
            "run_name": run_name,
            "description": "预测队列状态到生成表征的显式可靠性门控耦合探针",
            "tags": normalized_tags,
        }
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _input_manifest(settings: RepresentationTrainingSettings) -> dict[str, object]:
    files = {
        "generation_train": settings.generation_train_file,
        "generation_validation": settings.generation_validation_file,
        "physics_train": settings.physics_train_file,
        "physics_validation": settings.physics_validation_file,
        "physics_test": settings.physics_test_file,
    }
    result: dict[str, object] = {}
    for name, path in files.items():
        if not path.is_file():
            raise RepresentationTrainingError(f"输入文件不存在：{path}")
        with path.open("r", encoding="utf-8") as source:
            records = sum(1 for line in source if line.strip())
        result[name] = {
            "path": str(path),
            "sha256": _file_sha256(path),
            "bytes": path.stat().st_size,
            "records": records,
        }
    return result


def _snapshot(
    raw: Mapping[str, object],
    probe: ProbeConfig,
    settings: RepresentationTrainingSettings,
    tracking: TrackingSettings,
) -> dict[str, object]:
    return {
        "probe": {
            "model_id": probe.model_id,
            "feature_view": probe.feature_view,
            "seed": probe.seed,
            "max_input_length": probe.max_input_length,
            "max_new_tokens": probe.max_new_tokens,
            "lora_rank": probe.lora_rank,
            "lora_alpha": probe.lora_alpha,
            "lora_dropout": probe.lora_dropout,
        },
        "training": {
            **dict(raw["training"]),
            "variant": settings.variant,
            "output_dir": str(settings.output_dir),
            "max_steps": settings.max_steps,
            "validation_limit": settings.validation_limit,
            "effective_generation_batch_size": settings.effective_generation_batch_size,
        },
        "coupling": {
            "state_size": 5,
            "injection_point": "final_hidden_before_lm_head",
            "state_source": "last_prompt_token_hidden",
            "reliability_gate": "sigmoid_linear_of_log1p_predicted_state",
            "projection": (
                "stiefel_thin_qr" if settings.variant == "B1" else "unconstrained_linear"
            ),
            "state_perturbation_delta": 0.5,
        },
        "tracking": {
            "workspace": tracking.workspace,
            "project": tracking.project,
            "run_name": tracking.run_name,
            "mode": tracking.mode,
            "tags": list(tracking.tags),
        },
    }


def _write_sample_order(
    path: Path,
    generation_schedule: Sequence[Sequence[int]],
    physics_schedule: Sequence[Sequence[int]],
    generation_records: Sequence[Mapping[str, object]],
    physics_records: Sequence[Mapping[str, object]],
    *,
    accumulation_steps: int,
) -> None:
    steps = []
    for step, physics_indices in enumerate(physics_schedule, start=1):
        begin = (step - 1) * accumulation_steps
        generation_microbatches = []
        for indices in generation_schedule[begin : begin + accumulation_steps]:
            generation_microbatches.append(
                {
                    "indices": list(indices),
                    "sample_ids": [
                        str(generation_records[index]["sample_id"]) for index in indices
                    ],
                }
            )
        steps.append(
            {
                "step": step,
                "generation_microbatches": generation_microbatches,
                "physics": {
                    "indices": list(physics_indices),
                    "sample_ids": [
                        str(physics_records[index]["sample_id"]) for index in physics_indices
                    ],
                },
            }
        )
    _write_json(path, steps)


def _write_state_mask(path: Path, masks: Mapping[str, tuple[bool, bool, bool, bool, bool]]) -> None:
    _write_json(
        path,
        {
            "mode": STATE_SUPERVISION_MODE,
            "masks": [
                {"sample_id": sample_id, "mask": list(masks[sample_id])}
                for sample_id in sorted(masks)
            ],
        },
    )


def _parameter_gradient_norm(parameters: Sequence[torch.nn.Parameter]) -> float:
    total = 0.0
    for parameter in parameters:
        if parameter.grad is None:
            continue
        gradient = parameter.grad.detach().float()
        if not bool(torch.isfinite(gradient).all().item()):
            return math.inf
        total += float(gradient.square().sum().item())
    return math.sqrt(total)


def _state_prediction(
    model: object,
    state_head: ContinuousQueueStateHead,
    batch: Mapping[str, object],
) -> torch.Tensor:
    hidden = decoder_last_hidden(
        model,
        input_ids=batch["input_ids"],  # type: ignore[arg-type]
        attention_mask=batch["attention_mask"],  # type: ignore[arg-type]
    )
    selected = select_last_token_hidden(hidden, batch["attention_mask"])  # type: ignore[arg-type]
    return state_head(selected)


def _record_step(
    path: Path,
    swanlab: object,
    *,
    step: int,
    metrics: Mapping[str, float],
) -> None:
    normalized = {key: float(value) for key, value in metrics.items()}
    if not normalized or not all(math.isfinite(value) for value in normalized.values()):
        raise RepresentationTrainingError("逐步指标必须完整且全部为有限数值")
    with path.open("a", encoding="utf-8") as target:
        target.write(json.dumps({"step": step, "metrics": normalized}, sort_keys=True) + "\n")
    swanlab.log(normalized, step=step)


@torch.no_grad()
def _evaluate_generation(
    model: object,
    state_head: ContinuousQueueStateHead,
    coupling: PhysicalRepresentationCoupling,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    batch_size: int,
    max_length: int,
    device: torch.device,
) -> tuple[float, list[dict[str, object]]]:
    total_loss = 0.0
    total_records = 0
    predictions: list[dict[str, object]] = []
    for offset in range(0, len(records), batch_size):
        selected = records[offset : offset + batch_size]
        batch = _generation_batch(selected, tokenizer, max_length, device)
        output = coupled_generation_forward(model, state_head, coupling, batch)
        total_loss += float(output.loss.item()) * len(selected)
        total_records += len(selected)
        states = output.predicted_state.float().cpu().tolist()
        gates = output.reliability.float().cpu().reshape(-1).tolist()
        predictions.extend(
            {
                "kind": "generation",
                "sample_id": str(record["sample_id"]),
                "task": str(record.get("task", "")),
                "target": str(record.get("task_label", "")),
                "predicted_state": state,
                "reliability": gate,
            }
            for record, state, gate in zip(selected, states, gates, strict=True)
        )
    if total_records == 0:
        raise RepresentationTrainingError("生成验证集为空")
    return total_loss / total_records, predictions


@torch.no_grad()
def _evaluate_physics(
    model: object,
    state_head: ContinuousQueueStateHead,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]],
    batch_size: int,
    max_length: int,
    device: torch.device,
) -> tuple[dict[str, float], list[dict[str, object]]]:
    state_error_sum = 0.0
    state_count = 0
    observed_error_sum = 0.0
    observed_count = 0
    unobserved_error_sum = 0.0
    unobserved_count = 0
    residual_sum = 0.0
    residual_count = 0
    predictions: list[dict[str, object]] = []
    for offset in range(0, len(records), batch_size):
        selected = records[offset : offset + batch_size]
        batch = _state_batch(
            selected,
            tokenizer,
            max_length,
            device,
            include_fluxes=True,
            state_masks=state_masks,
        )
        predicted = _state_prediction(model, state_head, batch)
        targets = batch["state_targets"].float()  # type: ignore[union-attr]
        squared_error = (predicted.float() - targets).square()
        observed = batch["state_mask"].bool()  # type: ignore[union-attr]
        unobserved = ~observed
        residual = queue_balance_residual(
            predicted,
            batch["scale"],  # type: ignore[arg-type]
            batch["capacity"],  # type: ignore[arg-type]
            batch["received"],  # type: ignore[arg-type]
            batch["dequeued"],  # type: ignore[arg-type]
            batch["dropped_before"],  # type: ignore[arg-type]
            batch["dropped_after"],  # type: ignore[arg-type]
        )
        state_error_sum += float(squared_error.sum().item())
        state_count += squared_error.numel()
        observed_error_sum += float(squared_error.masked_select(observed).sum().item())
        observed_count += int(observed.sum().item())
        unobserved_error_sum += float(squared_error.masked_select(unobserved).sum().item())
        unobserved_count += int(unobserved.sum().item())
        residual_sum += float(residual.float().square().sum().item())
        residual_count += residual.numel()
        states = predicted.float().cpu().tolist()
        target_values = targets.cpu().tolist()
        masks = observed.cpu().tolist()
        residual_values = residual.float().square().mean(dim=1).cpu().tolist()
        predictions.extend(
            {
                "kind": "physics",
                "sample_id": str(record["sample_id"]),
                "predicted_state": state,
                "target_state": target,
                "state_mask": mask,
                "physics_residual_mse": residual_mse,
            }
            for record, state, target, mask, residual_mse in zip(
                selected,
                states,
                target_values,
                masks,
                residual_values,
                strict=True,
            )
        )
    if not state_count or not observed_count or not unobserved_count or not residual_count:
        raise RepresentationTrainingError("物理验证集或状态掩码为空")
    return (
        {
            "state_mse": state_error_sum / state_count,
            "state_mse_observed": observed_error_sum / observed_count,
            "state_mse_unobserved": unobserved_error_sum / unobserved_count,
            "physics_residual_mse": residual_sum / residual_count,
        },
        predictions,
    )


def train_representation_variant(
    probe: ProbeConfig,
    settings: RepresentationTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
) -> dict[str, object]:
    """训练一个严格隔离且除 Stiefel 约束外同构的 B0 或 B1。"""
    layout = create_run_layout(settings.output_dir)
    snapshot = _snapshot(raw_config, probe, settings, tracking)
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    _write_json(layout.input_manifest, _input_manifest(settings))
    generation_train = _load_jsonl(settings.generation_train_file)
    generation_validation = _load_jsonl(settings.generation_validation_file)
    physics_train = _load_jsonl(settings.physics_train_file)
    physics_validation = _load_jsonl(settings.physics_validation_file)
    if settings.validation_limit is not None:
        generation_validation = generation_validation[: settings.validation_limit]
        physics_validation = physics_validation[: settings.validation_limit]
    train_state_masks = build_state_supervision_masks(
        physics_train, settings.state_supervision_mode, probe.seed
    )
    validation_state_masks = build_state_supervision_masks(
        physics_validation, settings.state_supervision_mode, probe.seed
    )
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
    _write_sample_order(
        layout.sample_order,
        generation_schedule,
        physics_schedule,
        generation_train,
        physics_train,
        accumulation_steps=settings.gradient_accumulation_steps,
    )
    _write_state_mask(layout.state_mask, train_state_masks)
    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_manifest": layout.input_manifest,
        "step_metrics": layout.step_metrics,
        "training_summary": layout.training_summary,
        "final_adapter": layout.final_adapter,
        "state_head": layout.state_head,
        "representation_coupling": layout.coupling,
        "sample_order": layout.sample_order,
        "state_mask": layout.state_mask,
        "validation_predictions": layout.validation_predictions,
    }
    started = time.perf_counter()
    step_records: list[dict[str, float]] = []
    with (
        capture_console_log(layout.console_log),
        swanlab_run(
            settings=tracking,
            phase=PHASE,
            config=snapshot,
            artifact_dir=layout.output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        torch.manual_seed(probe.seed)
        torch.cuda.manual_seed_all(probe.seed)
        torch.cuda.reset_peak_memory_stats()
        tokenizer, model = _load_model(probe)
        device = next(model.parameters()).device
        state_head = ContinuousQueueStateHead(model.config.hidden_size).to(
            device=device, dtype=torch.bfloat16
        )
        coupling = PhysicalRepresentationCoupling(
            model.config.hidden_size,
            state_size=5,
            variant=settings.variant,
        ).to(device=device)
        state_head.train()
        coupling.train()
        lora_parameters = tuple(
            parameter
            for name, parameter in model.named_parameters()
            if parameter.requires_grad and "lora_" in name
        )
        if not lora_parameters:
            raise RepresentationTrainingError("未发现可训练 LoRA 参数")
        state_head_parameters = tuple(state_head.parameters())
        coupling_parameters = tuple(coupling.parameters())
        trainable = lora_parameters + state_head_parameters + coupling_parameters
        optimizer = torch.optim.AdamW(trainable, lr=settings.learning_rate)
        for step in range(1, settings.max_steps + 1):
            step_started = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            generation_loss_sum = 0.0
            q_gradient_norms = []
            reliability_values = []
            perturbation_delta = 0.0
            micro_start = (step - 1) * settings.gradient_accumulation_steps
            for micro in range(settings.gradient_accumulation_steps):
                indices = generation_schedule[micro_start + micro]
                batch = _generation_batch(
                    [generation_train[index] for index in indices],
                    tokenizer,
                    probe.max_input_length,
                    device,
                )
                output: CoupledGenerationOutput = coupled_generation_forward(
                    model, state_head, coupling, batch
                )
                q_gradient = torch.autograd.grad(
                    output.loss,
                    output.predicted_state,
                    retain_graph=True,
                    create_graph=False,
                )[0]
                q_gradient_norm = float(torch.linalg.vector_norm(q_gradient.float()).item())
                if not math.isfinite(q_gradient_norm) or q_gradient_norm <= 0:
                    raise RepresentationTrainingError("生成损失对预测状态的梯度必须有限且非零")
                if micro == 0:
                    perturbation_delta = perturbed_supervised_logit_delta(
                        model, coupling, output, delta=0.5
                    )
                    if not math.isfinite(perturbation_delta) or perturbation_delta <= 0:
                        raise RepresentationTrainingError("生成输出对预测状态扰动必须有限且敏感")
                generation_loss_sum += float(output.loss.detach().item())
                q_gradient_norms.append(q_gradient_norm)
                reliability_values.append(float(output.reliability.detach().float().mean().item()))
                (output.loss / settings.gradient_accumulation_steps).backward()
            physics_indices = physics_schedule[step - 1]
            state_batch = _state_batch(
                [physics_train[index] for index in physics_indices],
                tokenizer,
                probe.max_input_length,
                device,
                include_fluxes=True,
                state_masks=train_state_masks,
            )
            predicted_state = _state_prediction(model, state_head, state_batch)
            state_loss = masked_state_target_loss(
                predicted_state,
                state_batch["state_targets"],  # type: ignore[arg-type]
                state_batch["state_mask"],  # type: ignore[arg-type]
            )
            residual = queue_balance_residual(
                predicted_state,
                state_batch["scale"],  # type: ignore[arg-type]
                state_batch["capacity"],  # type: ignore[arg-type]
                state_batch["received"],  # type: ignore[arg-type]
                state_batch["dequeued"],  # type: ignore[arg-type]
                state_batch["dropped_before"],  # type: ignore[arg-type]
                state_batch["dropped_after"],  # type: ignore[arg-type]
            )
            physics_loss = residual.square().mean()
            auxiliary_loss = (
                settings.lambda_state * state_loss + settings.lambda_physics * physics_loss
            )
            auxiliary_loss.backward()
            lora_gradient_norm = _parameter_gradient_norm(lora_parameters)
            state_head_gradient_norm = _parameter_gradient_norm(state_head_parameters)
            coupling_gradient_norm = _parameter_gradient_norm(coupling_parameters)
            if not all(
                math.isfinite(value)
                for value in (
                    lora_gradient_norm,
                    state_head_gradient_norm,
                    coupling_gradient_norm,
                )
            ):
                raise RepresentationTrainingError("训练梯度包含非有限数值")
            torch.nn.utils.clip_grad_norm_(trainable, settings.max_grad_norm)
            optimizer.step()
            elapsed = time.perf_counter() - step_started
            metrics = {
                "train/generation_loss": generation_loss_sum / settings.gradient_accumulation_steps,
                "train/state_loss": float(state_loss.detach().item()),
                "train/physics_loss": float(physics_loss.detach().item()),
                "coupling/q_gradient_norm": sum(q_gradient_norms) / len(q_gradient_norms),
                "coupling/perturbed_logit_max_delta": perturbation_delta,
                "coupling/reliability_mean": sum(reliability_values) / len(reliability_values),
                "coupling/projection_orthogonality_error": float(
                    coupling.orthogonality_error().detach().item()
                ),
                "gradient/lora_norm": lora_gradient_norm,
                "gradient/state_head_norm": state_head_gradient_norm,
                "gradient/coupling_norm": coupling_gradient_norm,
                "runtime/throughput_samples_per_second": (
                    settings.effective_generation_batch_size + settings.physics_batch_size
                )
                / elapsed,
                "runtime/peak_memory_mib": float(torch.cuda.max_memory_allocated() / (1024**2)),
            }
            _record_step(layout.step_metrics, swanlab, step=step, metrics=metrics)
            step_records.append(metrics)
            print(json.dumps({"step": step, **metrics}, ensure_ascii=False, sort_keys=True))
        model.eval()
        state_head.eval()
        coupling.eval()
        generation_validation_loss, generation_predictions = _evaluate_generation(
            model,
            state_head,
            coupling,
            tokenizer,
            generation_validation,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
        )
        physics_metrics, physics_predictions = _evaluate_physics(
            model,
            state_head,
            tokenizer,
            physics_validation,
            state_masks=validation_state_masks,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
        )
        with layout.validation_predictions.open("w", encoding="utf-8") as target:
            for prediction in (*generation_predictions, *physics_predictions):
                target.write(json.dumps(prediction, ensure_ascii=False, sort_keys=True) + "\n")
        model.save_pretrained(layout.final_adapter)
        tokenizer.save_pretrained(layout.final_adapter)
        torch.save(
            {name: value.detach().cpu() for name, value in state_head.state_dict().items()},
            layout.state_head,
        )
        torch.save(
            {name: value.detach().cpu() for name, value in coupling.state_dict().items()},
            layout.coupling,
        )
        validation_metrics = {
            "validation/generation_loss": generation_validation_loss,
            "validation/state_mse": physics_metrics["state_mse"],
            "validation/state_mse_observed": physics_metrics["state_mse_observed"],
            "validation/state_mse_unobserved": physics_metrics["state_mse_unobserved"],
            "validation/physics_residual_mse": physics_metrics["physics_residual_mse"],
        }
        summary = {
            "schema_version": "flow_probe_representation_coupling_v1",
            "status": "finished",
            "variant": settings.variant,
            "seed": probe.seed,
            "max_steps": settings.max_steps,
            "optimizer_updates": settings.max_steps,
            "model_id": probe.model_id,
            "state_supervision_mode": settings.state_supervision_mode,
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "generation_train_samples": len(generation_train),
            "physics_train_samples": len(physics_train),
            "generation_validation_samples": len(generation_validation),
            "physics_validation_samples": len(physics_validation),
            "sample_order_sha256": _file_sha256(layout.sample_order),
            "state_mask_sha256": _state_mask_sha256(train_state_masks),
            "gradient_path": {
                "all_steps_nonzero": all(
                    record["coupling/q_gradient_norm"] > 0 for record in step_records
                ),
                "minimum_q_gradient_norm": min(
                    record["coupling/q_gradient_norm"] for record in step_records
                ),
            },
            "perturbation": {
                "all_steps_sensitive": all(
                    record["coupling/perturbed_logit_max_delta"] > 0 for record in step_records
                ),
                "minimum_logit_max_delta": min(
                    record["coupling/perturbed_logit_max_delta"] for record in step_records
                ),
                "delta": 0.5,
            },
            "projection_orthogonality_error": float(coupling.orthogonality_error().detach().item()),
            "validation": {
                "generation_loss": generation_validation_loss,
                **physics_metrics,
            },
            "runtime_seconds": time.perf_counter() - started,
            "peak_memory_mib": float(torch.cuda.max_memory_allocated() / (1024**2)),
        }
        _write_json(layout.training_summary, summary)
        swanlab.log(validation_metrics, step=settings.max_steps + 1)
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    validate_completed_artifacts(layout)
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 B0/B1 物理表征显式耦合探针")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-steps", type=int, choices=ALLOWED_STEPS, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--validation-limit", type=int)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise RepresentationTrainingError("配置根节点必须是映射")
    probe_data = raw.get("probe")
    if not isinstance(probe_data, Mapping):
        raise RepresentationTrainingError("配置缺少 probe")
    probe = ProbeConfig.from_mapping(probe_data)
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_settings(
        raw,
        variant=args.variant,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        validation_limit=args.validation_limit,
    )
    tracking = _tracking_settings(raw, args.run_name, settings.variant)
    manifest = train_representation_variant(probe, settings, tracking, raw)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
