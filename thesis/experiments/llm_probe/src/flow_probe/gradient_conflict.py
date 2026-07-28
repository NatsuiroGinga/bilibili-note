"""在真实 GeNIS 与 ns-3 批次上诊断三个目标的共享 LoRA 梯度关系。"""

from __future__ import annotations

import argparse
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
    _sha256,
    _state_batch,
    _write_json,
    masked_state_target_loss,
    physics_sample_schedule,
    queue_balance_residual,
    state_target_loss,
)
from flow_probe.qwen_physics_gradient import select_last_token_hidden
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

LAMBDA_PHYSICS = (0.001, 0.01, 0.03, 0.1)
PHASE = "gradient-conflict"


class GradientDiagnosticError(ValueError):
    """梯度诊断输入、数值或制品不满足固定协议。"""


@dataclass(frozen=True)
class PairedBatch:
    """一个诊断步使用的四个生成微批次和一个物理批次。"""

    step: int
    generation_microbatches: tuple[tuple[int, ...], ...]
    physics_indices: tuple[int, ...]


@dataclass(frozen=True)
class GradientTripletSummary:
    """三个目标在同一组共享参数上的范数、方向和尺度关系。"""

    generation_norm: float
    state_norm: float
    physics_norm: float
    cosine_generation_state: float
    cosine_generation_physics: float
    cosine_state_physics: float
    weighted_physics_to_generation: dict[str, float]
    weighted_physics_to_state: dict[str, float]


@dataclass(frozen=True)
class DiagnosticSettings:
    """真实批次诊断的固定路径与批量协议。"""

    output_dir: Path
    generation_train_file: Path
    physics_train_file: Path
    generation_batch_size: int
    generation_accumulation_steps: int
    physics_batch_size: int
    paired_batches: int


@dataclass(frozen=True)
class DiagnosticLayout:
    """一次诊断必须完整写出的制品。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    sample_order: Path
    step_metrics: Path
    summary: Path
    console_log: Path
    artifact_manifest: Path

    @property
    def required_paths(self) -> tuple[Path, ...]:
        return (
            self.config_snapshot,
            self.environment,
            self.input_sha256,
            self.sample_order,
            self.step_metrics,
            self.summary,
            self.console_log,
            self.artifact_manifest,
            self.output_dir / "swanlog" / PHASE,
        )


GradientTuple = tuple[torch.Tensor | None, ...]


def build_paired_schedule(
    *,
    generation_sample_count: int,
    physics_sample_count: int,
    paired_batches: int,
    generation_batch_size: int,
    generation_accumulation_steps: int,
    physics_batch_size: int,
    seed: int,
) -> tuple[PairedBatch, ...]:
    """按首轮训练的批量和随机流构造配对诊断顺序。"""
    if paired_batches <= 0 or generation_accumulation_steps <= 0:
        raise GradientDiagnosticError("配对批次数和生成累积步数必须大于零")
    generation = physics_sample_schedule(
        generation_sample_count,
        batch_size=generation_batch_size,
        steps=paired_batches * generation_accumulation_steps,
        seed=seed,
    )
    physics = physics_sample_schedule(
        physics_sample_count,
        batch_size=physics_batch_size,
        steps=paired_batches,
        seed=seed,
    )
    return tuple(
        PairedBatch(
            step=step,
            generation_microbatches=tuple(
                generation[
                    (step - 1)
                    * generation_accumulation_steps : step
                    * generation_accumulation_steps
                ]
            ),
            physics_indices=physics[step - 1],
        )
        for step in range(1, paired_batches + 1)
    )


def _gradient_norm(name: str, gradients: Sequence[torch.Tensor | None]) -> float:
    total = 0.0
    present = False
    for gradient in gradients:
        if gradient is None:
            continue
        present = True
        value = gradient.detach().float()
        if not bool(torch.isfinite(value).all().item()):
            raise GradientDiagnosticError(f"{name}梯度包含非有限值")
        total += float(value.square().sum().item())
    if not present or total == 0.0:
        raise GradientDiagnosticError(f"{name}梯度严格为零")
    if not math.isfinite(total):
        raise GradientDiagnosticError(f"{name}梯度范数非有限")
    return math.sqrt(total)


def _gradient_dot(
    left: Sequence[torch.Tensor | None],
    right: Sequence[torch.Tensor | None],
) -> float:
    if len(left) != len(right):
        raise GradientDiagnosticError("梯度参数张量数量不一致")
    total = 0.0
    for left_gradient, right_gradient in zip(left, right, strict=True):
        if left_gradient is None or right_gradient is None:
            continue
        if left_gradient.shape != right_gradient.shape:
            raise GradientDiagnosticError("梯度参数张量形状不一致")
        total += float(
            (left_gradient.detach().float() * right_gradient.detach().float()).sum().item()
        )
    if not math.isfinite(total):
        raise GradientDiagnosticError("梯度点积非有限")
    return total


def gradient_triplet_summary(
    generation_gradients: Sequence[torch.Tensor | None],
    state_gradients: Sequence[torch.Tensor | None],
    physics_gradients: Sequence[torch.Tensor | None],
    *,
    lambda_physics: Sequence[float],
) -> GradientTripletSummary:
    """逐参数张量累计三个目标的范数、余弦和加权尺度比。"""
    if not (len(generation_gradients) == len(state_gradients) == len(physics_gradients)):
        raise GradientDiagnosticError("三个目标的梯度参数张量数量不一致")
    generation_norm = _gradient_norm("生成", generation_gradients)
    state_norm = _gradient_norm("状态", state_gradients)
    physics_norm = _gradient_norm("物理", physics_gradients)

    def cosine(
        left: Sequence[torch.Tensor | None],
        right: Sequence[torch.Tensor | None],
        left_norm: float,
        right_norm: float,
    ) -> float:
        value = _gradient_dot(left, right) / (left_norm * right_norm)
        return max(-1.0, min(1.0, value))

    weights = tuple(float(weight) for weight in lambda_physics)
    if not weights or any(not math.isfinite(weight) or weight < 0 for weight in weights):
        raise GradientDiagnosticError("物理损失权重必须为有限非负数")
    to_generation = {f"{weight:g}": weight * physics_norm / generation_norm for weight in weights}
    to_state = {f"{weight:g}": weight * physics_norm / state_norm for weight in weights}
    return GradientTripletSummary(
        generation_norm=generation_norm,
        state_norm=state_norm,
        physics_norm=physics_norm,
        cosine_generation_state=cosine(
            generation_gradients,
            state_gradients,
            generation_norm,
            state_norm,
        ),
        cosine_generation_physics=cosine(
            generation_gradients,
            physics_gradients,
            generation_norm,
            physics_norm,
        ),
        cosine_state_physics=cosine(
            state_gradients,
            physics_gradients,
            state_norm,
            physics_norm,
        ),
        weighted_physics_to_generation=to_generation,
        weighted_physics_to_state=to_state,
    )


def _build_settings(
    raw: Mapping[str, object], output_dir: Path, paired_batches: int
) -> DiagnosticSettings:
    training = raw.get("training")
    if not isinstance(training, Mapping):
        raise GradientDiagnosticError("配置缺少 training")
    required = (
        "generation_train_file",
        "physics_train_file",
        "generation_batch_size",
        "gradient_accumulation_steps",
        "physics_batch_size",
    )
    missing = [name for name in required if name not in training]
    if missing:
        raise GradientDiagnosticError("缺少诊断配置：" + ", ".join(missing))
    settings = DiagnosticSettings(
        output_dir=Path(output_dir),
        generation_train_file=Path(str(training["generation_train_file"])),
        physics_train_file=Path(str(training["physics_train_file"])),
        generation_batch_size=int(training["generation_batch_size"]),
        generation_accumulation_steps=int(training["gradient_accumulation_steps"]),
        physics_batch_size=int(training["physics_batch_size"]),
        paired_batches=int(paired_batches),
    )
    if (
        settings.generation_batch_size,
        settings.generation_accumulation_steps,
        settings.physics_batch_size,
        settings.paired_batches,
    ) != (4, 4, 4, 20):
        raise GradientDiagnosticError("真实诊断必须固定为生成4x4、物理4和20个配对批次")
    for path in (settings.generation_train_file, settings.physics_train_file):
        if not path.is_file():
            raise GradientDiagnosticError(f"诊断输入不存在：{path}")
    return settings


def _create_layout(output_dir: Path) -> DiagnosticLayout:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    return DiagnosticLayout(
        output_dir=output_dir,
        config_snapshot=output_dir / "config_snapshot.yaml",
        environment=output_dir / "environment.json",
        input_sha256=output_dir / "input_sha256.json",
        sample_order=output_dir / "sample_order.json",
        step_metrics=output_dir / "step_metrics.jsonl",
        summary=output_dir / "summary.json",
        console_log=output_dir / "console.log",
        artifact_manifest=output_dir / "artifact_manifest.json",
    )


def _input_manifest(settings: DiagnosticSettings) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, path in (
        ("generation_train", settings.generation_train_file),
        ("physics_train", settings.physics_train_file),
    ):
        with path.open("r", encoding="utf-8") as source:
            records = sum(1 for line in source if line.strip())
        result[name] = {
            "path": str(path),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "records": records,
        }
    return result


def _sample_id(record: Mapping[str, object], index: int) -> str:
    value = record.get("sample_id")
    return str(value) if value is not None else f"index:{index}"


def _write_sample_order(
    path: Path,
    schedule: Sequence[PairedBatch],
    generation_records: Sequence[Mapping[str, object]],
    physics_records: Sequence[Mapping[str, object]],
) -> None:
    _write_json(
        path,
        [
            {
                "step": batch.step,
                "generation_microbatches": [
                    {
                        "indices": list(indices),
                        "sample_ids": [
                            _sample_id(generation_records[index], index) for index in indices
                        ],
                    }
                    for indices in batch.generation_microbatches
                ],
                "physics": {
                    "indices": list(batch.physics_indices),
                    "sample_ids": [
                        _sample_id(physics_records[index], index) for index in batch.physics_indices
                    ],
                },
            }
            for batch in schedule
        ],
    )


def _accumulate_gradients(
    accumulated: GradientTuple | None,
    gradients: Sequence[torch.Tensor | None],
) -> GradientTuple:
    if accumulated is None:
        return tuple(
            None if gradient is None else gradient.detach().float().clone()
            for gradient in gradients
        )
    if len(accumulated) != len(gradients):
        raise GradientDiagnosticError("生成微批次梯度参数数量不一致")
    result: list[torch.Tensor | None] = []
    for previous, gradient in zip(accumulated, gradients, strict=True):
        if gradient is None:
            result.append(previous)
        elif previous is None:
            result.append(gradient.detach().float().clone())
        else:
            result.append(previous + gradient.detach().float())
    return tuple(result)


def _generation_gradients(
    model: object,
    tokenizer: object,
    lora_parameters: Sequence[torch.nn.Parameter],
    generation_records: Sequence[Mapping[str, object]],
    microbatches: Sequence[Sequence[int]],
    *,
    max_length: int,
    device: torch.device,
) -> tuple[float, GradientTuple]:
    accumulated: GradientTuple | None = None
    loss_value = 0.0
    divisor = len(microbatches)
    for indices in microbatches:
        batch = _generation_batch(
            [generation_records[index] for index in indices],
            tokenizer,
            max_length,
            device,
        )
        loss = model(**batch, return_dict=True).loss.float() / divisor
        loss_value += float(loss.detach().item())
        gradients = torch.autograd.grad(
            loss,
            lora_parameters,
            allow_unused=True,
        )
        accumulated = _accumulate_gradients(accumulated, gradients)
    if accumulated is None:
        raise GradientDiagnosticError("生成梯度未计算")
    return loss_value, accumulated


def _state_and_physics_gradients(
    model: object,
    state_head: ContinuousQueueStateHead,
    tokenizer: object,
    lora_parameters: Sequence[torch.nn.Parameter],
    physics_records: Sequence[Mapping[str, object]],
    indices: Sequence[int],
    *,
    max_length: int,
    device: torch.device,
    state_masks: Mapping[str, tuple[bool, bool, bool, bool, bool]] | None = None,
) -> tuple[float, float, GradientTuple, GradientTuple]:
    batch = _state_batch(
        [physics_records[index] for index in indices],
        tokenizer,
        max_length,
        device,
        include_fluxes=True,
        state_masks=state_masks,
    )
    outputs = model(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        output_hidden_states=True,
        return_dict=True,
    )
    hidden = select_last_token_hidden(outputs.hidden_states[-1], batch["attention_mask"])
    predicted = state_head(hidden)
    state_loss = (
        state_target_loss(predicted, batch["state_targets"])
        if state_masks is None
        else masked_state_target_loss(
            predicted,
            batch["state_targets"],
            batch["state_mask"],
        )
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
    physics_loss = residual.square().mean()
    state_gradients = torch.autograd.grad(
        state_loss,
        lora_parameters,
        retain_graph=True,
        allow_unused=True,
    )
    physics_gradients = torch.autograd.grad(
        physics_loss,
        lora_parameters,
        allow_unused=True,
    )
    return (
        float(state_loss.detach().item()),
        float(physics_loss.detach().item()),
        tuple(
            None if gradient is None else gradient.detach().float() for gradient in state_gradients
        ),
        tuple(
            None if gradient is None else gradient.detach().float()
            for gradient in physics_gradients
        ),
    )


def _step_metrics(
    *,
    generation_loss: float,
    state_loss: float,
    physics_loss: float,
    gradients: GradientTripletSummary,
    elapsed_seconds: float,
) -> dict[str, float]:
    metrics = {
        "diagnostic/generation_loss": generation_loss,
        "diagnostic/state_loss": state_loss,
        "diagnostic/physics_loss": physics_loss,
        "diagnostic/generation_gradient_norm": gradients.generation_norm,
        "diagnostic/state_gradient_norm": gradients.state_norm,
        "diagnostic/physics_gradient_norm": gradients.physics_norm,
        "diagnostic/cosine_generation_state": gradients.cosine_generation_state,
        "diagnostic/cosine_generation_physics": gradients.cosine_generation_physics,
        "diagnostic/cosine_state_physics": gradients.cosine_state_physics,
        "diagnostic/negative_generation_state": float(gradients.cosine_generation_state < 0),
        "diagnostic/negative_generation_physics": float(gradients.cosine_generation_physics < 0),
        "diagnostic/negative_state_physics": float(gradients.cosine_state_physics < 0),
        "diagnostic/elapsed_seconds": elapsed_seconds,
        "diagnostic/peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
    }
    for weight, value in gradients.weighted_physics_to_generation.items():
        metrics[f"diagnostic/weighted_physics_to_generation/{weight}"] = value
    for weight, value in gradients.weighted_physics_to_state.items():
        metrics[f"diagnostic/weighted_physics_to_state/{weight}"] = value
    if not all(math.isfinite(value) for value in metrics.values()):
        raise GradientDiagnosticError("逐步诊断指标包含非有限值")
    return metrics


def _record_metrics(path: Path, swanlab: object, step: int, metrics: Mapping[str, float]) -> None:
    normalized = {key: float(value) for key, value in metrics.items()}
    with Path(path).open("a", encoding="utf-8") as target:
        target.write(json.dumps({"step": step, "metrics": normalized}, sort_keys=True) + "\n")
    swanlab.log(normalized, step=step)


def _aggregate(step_records: Sequence[Mapping[str, float]]) -> dict[str, object]:
    if not step_records:
        raise GradientDiagnosticError("没有可汇总的诊断步骤")

    def mean(key: str) -> float:
        return sum(float(record[key]) for record in step_records) / len(step_records)

    cosine_names = (
        "generation_state",
        "generation_physics",
        "state_physics",
    )
    return {
        "mean_losses": {
            name: mean(f"diagnostic/{name}_loss") for name in ("generation", "state", "physics")
        },
        "mean_gradient_norms": {
            name: mean(f"diagnostic/{name}_gradient_norm")
            for name in ("generation", "state", "physics")
        },
        "cosines": {
            name: {
                "mean": mean(f"diagnostic/cosine_{name}"),
                "negative_count": int(
                    sum(record[f"diagnostic/negative_{name}"] for record in step_records)
                ),
                "negative_ratio": mean(f"diagnostic/negative_{name}"),
            }
            for name in cosine_names
        },
        "mean_weighted_physics_to_generation": {
            f"{weight:g}": mean(f"diagnostic/weighted_physics_to_generation/{weight:g}")
            for weight in LAMBDA_PHYSICS
        },
        "mean_weighted_physics_to_state": {
            f"{weight:g}": mean(f"diagnostic/weighted_physics_to_state/{weight:g}")
            for weight in LAMBDA_PHYSICS
        },
        "mean_step_seconds": mean("diagnostic/elapsed_seconds"),
    }


def _tracking_settings(raw: Mapping[str, object], run_name: str) -> TrackingSettings:
    tracking = raw.get("tracking")
    if not isinstance(tracking, Mapping):
        raise GradientDiagnosticError("配置缺少 tracking")
    tags = list(tracking.get("tags", ()))
    if "gradient-conflict" not in tags:
        tags.append("gradient-conflict")
    return TrackingSettings.from_mapping(
        {
            **tracking,
            "run_name": run_name,
            "description": "Qwen3-1.7B 初始化真实批次梯度冲突诊断",
            "tags": tags,
        }
    )


def run_gradient_conflict_diagnostic(
    probe: ProbeConfig,
    settings: DiagnosticSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
) -> dict[str, object]:
    """运行不含参数更新的 20 批次真实梯度诊断。"""
    layout = _create_layout(settings.output_dir)
    generation_records = _load_jsonl(settings.generation_train_file)
    physics_records = _load_jsonl(settings.physics_train_file)
    schedule = build_paired_schedule(
        generation_sample_count=len(generation_records),
        physics_sample_count=len(physics_records),
        paired_batches=settings.paired_batches,
        generation_batch_size=settings.generation_batch_size,
        generation_accumulation_steps=settings.generation_accumulation_steps,
        physics_batch_size=settings.physics_batch_size,
        seed=probe.seed,
    )
    snapshot = {
        "schema_version": "flow_probe_gradient_conflict_v1",
        "probe": {
            "model_id": probe.model_id,
            "seed": probe.seed,
            "max_input_length": probe.max_input_length,
            "lora_rank": probe.lora_rank,
            "lora_alpha": probe.lora_alpha,
            "lora_dropout": probe.lora_dropout,
        },
        "diagnostic": {
            "paired_batches": settings.paired_batches,
            "generation_batch_size": settings.generation_batch_size,
            "generation_accumulation_steps": settings.generation_accumulation_steps,
            "physics_batch_size": settings.physics_batch_size,
            "lambda_physics": list(LAMBDA_PHYSICS),
            "optimizer_updates": 0,
            "residual_denominator": "strict_positive_configured_capacity_integral_link_bytes",
        },
        "tracking": {
            "workspace": tracking.workspace,
            "project": tracking.project,
            "run_name": tracking.run_name,
            "mode": tracking.mode,
        },
        "source_training_config": dict(raw_config["training"]),
    }
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    _write_json(layout.input_sha256, _input_manifest(settings))
    _write_sample_order(layout.sample_order, schedule, generation_records, physics_records)
    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "sample_order": layout.sample_order,
        "step_metrics": layout.step_metrics,
        "summary": layout.summary,
    }
    started = time.perf_counter()
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
        state_head.train()
        lora_parameters = tuple(
            parameter
            for name, parameter in model.named_parameters()
            if parameter.requires_grad and "lora_" in name
        )
        if not lora_parameters:
            raise GradientDiagnosticError("未发现可训练 LoRA 参数")
        step_records: list[dict[str, float]] = []
        for paired in schedule:
            step_started = time.perf_counter()
            generation_loss, generation_gradients = _generation_gradients(
                model,
                tokenizer,
                lora_parameters,
                generation_records,
                paired.generation_microbatches,
                max_length=probe.max_input_length,
                device=device,
            )
            state_loss, physics_loss, state_gradients, physics_gradients = (
                _state_and_physics_gradients(
                    model,
                    state_head,
                    tokenizer,
                    lora_parameters,
                    physics_records,
                    paired.physics_indices,
                    max_length=probe.max_input_length,
                    device=device,
                )
            )
            relationships = gradient_triplet_summary(
                generation_gradients,
                state_gradients,
                physics_gradients,
                lambda_physics=LAMBDA_PHYSICS,
            )
            metrics = _step_metrics(
                generation_loss=generation_loss,
                state_loss=state_loss,
                physics_loss=physics_loss,
                gradients=relationships,
                elapsed_seconds=time.perf_counter() - step_started,
            )
            _record_metrics(layout.step_metrics, swanlab, paired.step, metrics)
            step_records.append(metrics)
            print(
                json.dumps(
                    {"step": paired.step, **metrics},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        if any(parameter.grad is not None for parameter in lora_parameters):
            raise GradientDiagnosticError("诊断期间意外写入了 LoRA 参数梯度")
        torch.cuda.synchronize()
        summary = {
            "schema_version": "flow_probe_gradient_conflict_v1",
            "status": "finished",
            "model_id": probe.model_id,
            "seed": probe.seed,
            "paired_batches": settings.paired_batches,
            "optimizer_updates": 0,
            "trainable_lora_parameter_count": sum(
                parameter.numel() for parameter in lora_parameters
            ),
            "sample_order_sha256": _sha256(layout.sample_order),
            "runtime_seconds": time.perf_counter() - started,
            "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            **_aggregate(step_records),
        }
        _write_json(layout.summary, summary)
        swanlab.log(
            {
                "summary/runtime_seconds": summary["runtime_seconds"],
                "summary/peak_gpu_memory_mib": summary["peak_gpu_memory_mib"],
            },
            step=settings.paired_batches + 1,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    missing = [str(path) for path in layout.required_paths if not path.exists()]
    if missing:
        raise GradientDiagnosticError("诊断制品不完整：" + ", ".join(missing))
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行真实批次共享 LoRA 梯度冲突诊断")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--paired-batches", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise GradientDiagnosticError("配置根节点必须是映射")
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_settings(raw, args.output_dir, args.paired_batches)
    tracking = _tracking_settings(raw, args.run_name)
    manifest = run_gradient_conflict_diagnostic(probe, settings, tracking, raw)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
