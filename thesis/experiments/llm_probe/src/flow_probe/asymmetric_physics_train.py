"""冻结检测 LoRA 并训练任务条件化物理私有 LoRA。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType

import torch
import torch.nn.functional as functional
import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.physics_train import (
    ContinuousQueueStateHead,
    PhysicsTrainingError,
    PhysicsTrainingSettings,
    _build_settings,
    _environment_manifest,
    _evaluate_generation,
    _evaluate_state,
    _generation_batch,
    _gradient_norm,
    _input_manifest,
    _load_jsonl,
    _sha256,
    _state_batch,
    _state_mask_sha256,
    _tracking_settings,
    _write_json,
    build_state_supervision_masks,
    masked_state_target_loss,
    physics_sample_schedule,
    queue_balance_residual,
    record_step_metrics,
)
from flow_probe.qwen_physics_gradient import select_last_token_hidden
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

DETECTION_ADAPTER = "detection"
PRIVATE_ADAPTER = "physics_private"
SUBTYPE_TASK = "attack_subtype"
DIAGNOSTIC_CONTRACT_VERSION = "asymmetric_private_diagnostic_v1"
FORMAL_DIAGNOSTIC_STEPS = 202
D3_WARMUP_STEPS = 20
D3_PEAK_LEARNING_RATE = 2e-4
D3_MIN_LEARNING_RATE = 2e-5


@dataclass(frozen=True)
class DiagnosticModeContract:
    """固定一次归因干预允许启用的损失与学习率轨迹。"""

    name: str
    generation_loss_enabled: bool
    state_loss_enabled: bool
    physics_loss_enabled: bool
    learning_rate_schedule: str

    @property
    def physics_batch_enabled(self) -> bool:
        return self.state_loss_enabled or self.physics_loss_enabled


DIAGNOSTIC_MODE_CONTRACTS: Mapping[str, DiagnosticModeContract] = MappingProxyType(
    {
        "joint_constant": DiagnosticModeContract(
            name="joint_constant",
            generation_loss_enabled=True,
            state_loss_enabled=True,
            physics_loss_enabled=True,
            learning_rate_schedule="constant",
        ),
        "generation_only": DiagnosticModeContract(
            name="generation_only",
            generation_loss_enabled=True,
            state_loss_enabled=False,
            physics_loss_enabled=False,
            learning_rate_schedule="constant",
        ),
        "physics_only": DiagnosticModeContract(
            name="physics_only",
            generation_loss_enabled=False,
            state_loss_enabled=True,
            physics_loss_enabled=True,
            learning_rate_schedule="constant",
        ),
        "joint_warmup_cosine": DiagnosticModeContract(
            name="joint_warmup_cosine",
            generation_loss_enabled=True,
            state_loss_enabled=True,
            physics_loss_enabled=True,
            learning_rate_schedule="linear_warmup_cosine_decay",
        ),
    }
)


def resolve_diagnostic_mode(name: str) -> DiagnosticModeContract:
    """把命令行名称解析为预注册契约，并拒绝临时变体。"""
    try:
        return DIAGNOSTIC_MODE_CONTRACTS[name]
    except KeyError as error:
        choices = "、".join(DIAGNOSTIC_MODE_CONTRACTS)
        raise PhysicsTrainingError(f"未知诊断模式：{name}；只允许 {choices}") from error


def diagnostic_learning_rate(
    mode: str | DiagnosticModeContract,
    step: int,
    *,
    peak_learning_rate: float = D3_PEAK_LEARNING_RATE,
) -> float:
    """返回当前优化步实际使用的预注册学习率。"""
    contract = resolve_diagnostic_mode(mode) if isinstance(mode, str) else mode
    if step <= 0:
        raise PhysicsTrainingError("学习率轨迹的优化步必须为正整数")
    if contract.learning_rate_schedule == "constant":
        return float(peak_learning_rate)
    if step > FORMAL_DIAGNOSTIC_STEPS:
        raise PhysicsTrainingError(f"D3 学习率轨迹只预注册到第 {FORMAL_DIAGNOSTIC_STEPS} 步")
    if not math.isclose(
        peak_learning_rate,
        D3_PEAK_LEARNING_RATE,
        rel_tol=0.0,
        abs_tol=1e-12,
    ):
        raise PhysicsTrainingError("D3 峰值学习率必须固定为 2e-4")
    if step <= D3_WARMUP_STEPS:
        progress = (step - 1) / (D3_WARMUP_STEPS - 1)
        return D3_MIN_LEARNING_RATE + progress * (D3_PEAK_LEARNING_RATE - D3_MIN_LEARNING_RATE)
    decay_progress = (step - D3_WARMUP_STEPS) / (FORMAL_DIAGNOSTIC_STEPS - D3_WARMUP_STEPS)
    return D3_MIN_LEARNING_RATE + 0.5 * (D3_PEAK_LEARNING_RATE - D3_MIN_LEARNING_RATE) * (
        1.0 + math.cos(math.pi * decay_progress)
    )


@dataclass(frozen=True)
class AsymmetricRunLayout:
    """唯一修复实验必须保存的制品路径。"""

    output_dir: Path
    config_snapshot: Path
    environment: Path
    input_sha256: Path
    console_log: Path
    step_metrics: Path
    training_summary: Path
    private_adapter_root: Path
    private_adapter: Path
    state_head: Path
    generation_sample_order: Path
    physics_sample_order: Path
    route_equivalence: Path
    artifact_manifest: Path

    @classmethod
    def create(cls, output_dir: Path) -> AsymmetricRunLayout:
        output_dir = Path(output_dir)
        return cls(
            output_dir=output_dir,
            config_snapshot=output_dir / "config_snapshot.yaml",
            environment=output_dir / "environment.json",
            input_sha256=output_dir / "input_sha256.json",
            console_log=output_dir / "console.log",
            step_metrics=output_dir / "step_metrics.jsonl",
            training_summary=output_dir / "training_summary.json",
            private_adapter_root=output_dir / "final_private_adapter",
            private_adapter=output_dir / "final_private_adapter" / PRIVATE_ADAPTER,
            state_head=output_dir / "state_head.pt",
            generation_sample_order=output_dir / "generation_sample_order.json",
            physics_sample_order=output_dir / "physics_sample_order.json",
            route_equivalence=output_dir / "family_route_equivalence.json",
            artifact_manifest=output_dir / "artifact_manifest.json",
        )


def _directory_manifest(path: Path) -> dict[str, object]:
    """记录检测适配器目录中每个文件的摘要。"""
    path = Path(path)
    if not path.is_dir():
        raise PhysicsTrainingError(f"检测适配器目录不存在：{path}")
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise PhysicsTrainingError(f"检测适配器目录为空：{path}")
    entries = [
        {
            "path": str(item.relative_to(path)),
            "bytes": item.stat().st_size,
            "sha256": _sha256(item),
        }
        for item in files
    ]
    digest = hashlib.sha256(
        json.dumps(entries, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {"path": str(path), "sha256": digest, "files": entries}


def _adapter_parameter_digest(model: object, adapter_name: str) -> str:
    """计算指定 LoRA 参数的内存摘要，用于证明冻结参数未改变。"""
    digest = hashlib.sha256()
    marker = f".{adapter_name}."
    matched = 0
    for name, parameter in sorted(model.named_parameters()):
        if marker not in name:
            continue
        matched += 1
        digest.update(name.encode("utf-8"))
        raw = parameter.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()
        digest.update(raw)
    if matched == 0:
        raise PhysicsTrainingError(f"未找到适配器参数：{adapter_name}")
    return digest.hexdigest()


def _set_adapter_route(model: object, *, use_private: bool, train_private: bool) -> None:
    """切换任务路由，并在组合激活后显式冻结检测适配器。"""
    active = [DETECTION_ADAPTER, PRIVATE_ADAPTER] if use_private else DETECTION_ADAPTER
    model.base_model.set_adapter(active, inference_mode=not train_private)
    marker = f".{PRIVATE_ADAPTER}."
    for name, parameter in model.named_parameters():
        parameter.requires_grad = bool(train_private and use_private and marker in name)


def _load_model(probe: ProbeConfig, detection_adapter_path: Path) -> tuple[object, object]:
    """加载量化基座、冻结的 S3 LoRA 和零初始化私有 LoRA。"""
    from peft import LoraConfig, PeftModel, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动非对称物理适配训练")
    tokenizer_source = (
        detection_adapter_path
        if (detection_adapter_path / "tokenizer_config.json").is_file()
        else probe.model_id
    )
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        probe.model_id,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    base_model = prepare_model_for_kbit_training(
        base_model,
        use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )
    model = PeftModel.from_pretrained(
        base_model,
        str(detection_adapter_path),
        adapter_name=DETECTION_ADAPTER,
        is_trainable=False,
    )
    model.add_adapter(
        PRIVATE_ADAPTER,
        LoraConfig(
            r=probe.lora_rank,
            lora_alpha=probe.lora_alpha,
            lora_dropout=probe.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules="all-linear",
            init_lora_weights=True,
        ),
    )
    _set_adapter_route(model, use_private=True, train_private=True)
    model.config.use_cache = False
    model.train()
    return tokenizer, model


def _subtype_generation_loss(
    model: object,
    tokenizer: object,
    records: Sequence[Mapping[str, object]],
    *,
    max_length: int,
    device: torch.device,
) -> tuple[torch.Tensor, int, int]:
    """保留原调度批次，但只累计子类样本的完成令牌损失。"""
    batch = _generation_batch(records, tokenizer, max_length, device)
    outputs = model(
        input_ids=batch["input_ids"],
        attention_mask=batch["attention_mask"],
        return_dict=True,
    )
    shifted_logits = outputs.logits[:, :-1, :].float()
    shifted_labels = batch["labels"][:, 1:]
    valid_tokens = shifted_labels.ne(-100)
    subtype_rows = torch.tensor(
        [str(record.get("task")) == SUBTYPE_TASK for record in records],
        dtype=torch.bool,
        device=device,
    )
    selected = valid_tokens & subtype_rows.unsqueeze(1)
    selected_tokens = int(selected.sum().item())
    selected_samples = int(subtype_rows.sum().item())
    if selected_tokens == 0:
        return outputs.logits[..., 0].sum() * 0.0, selected_samples, selected_tokens
    token_losses = functional.cross_entropy(
        shifted_logits.reshape(-1, shifted_logits.shape[-1]),
        shifted_labels.clamp_min(0).reshape(-1),
        reduction="none",
    ).view_as(shifted_labels)
    loss = (token_losses * selected).sum() / selected.sum()
    return loss, selected_samples, selected_tokens


def _last_token_logits(
    model: object,
    tokenizer: object,
    record: Mapping[str, object],
    *,
    max_length: int,
    device: torch.device,
) -> torch.Tensor:
    batch = _generation_batch([record], tokenizer, max_length, device)
    model.eval()
    with torch.no_grad():
        logits = model(
            input_ids=batch["input_ids"],
            attention_mask=batch["attention_mask"],
            return_dict=True,
        ).logits[:, -1, :]
    return logits.detach().float().cpu()


def _max_abs_difference(left: torch.Tensor, right: torch.Tensor) -> float:
    return float((left - right).abs().max().item())


def _validate_settings(settings: PhysicsTrainingSettings, contract: DiagnosticModeContract) -> None:
    if settings.variant != "M2":
        raise PhysicsTrainingError("非对称物理适配只允许 M2 损失契约")
    if settings.state_supervision_mode != "anchor0_plus_one":
        raise PhysicsTrainingError("非对称物理适配必须使用双锚点监督")
    if settings.lambda_state != 1.0 or settings.lambda_physics != 0.01:
        raise PhysicsTrainingError("损失权重必须固定为 lambda_state=1.0、lambda_physics=0.01")
    if contract.name != "joint_constant":
        if not math.isclose(
            settings.learning_rate,
            D3_PEAK_LEARNING_RATE,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise PhysicsTrainingError("诊断实验学习率必须固定为 2e-4")
        if settings.max_steps > FORMAL_DIAGNOSTIC_STEPS:
            raise PhysicsTrainingError(f"诊断实验最多允许 {FORMAL_DIAGNOSTIC_STEPS} 个优化步")


def train_asymmetric_physics(
    probe: ProbeConfig,
    settings: PhysicsTrainingSettings,
    tracking: TrackingSettings,
    raw_config: Mapping[str, object],
    detection_adapter_path: Path,
    diagnostic_mode: str = "joint_constant",
) -> dict[str, object]:
    """执行冻结检测路径的预注册单私有 LoRA 诊断训练。"""
    contract = resolve_diagnostic_mode(diagnostic_mode)
    _validate_settings(settings, contract)
    layout = AsymmetricRunLayout.create(settings.output_dir)
    if layout.output_dir.exists():
        raise PhysicsTrainingError(f"输出目录已存在，拒绝复用：{layout.output_dir}")
    generation_train = _load_jsonl(settings.generation_train_file)
    generation_validation = [
        record
        for record in _load_jsonl(settings.generation_validation_file)
        if str(record.get("task")) == SUBTYPE_TASK
    ]
    if settings.validation_limit is not None:
        generation_validation = generation_validation[: settings.validation_limit]
    if not generation_validation:
        raise PhysicsTrainingError("生成验证集缺少 attack_subtype 样本")
    physics_train = _load_jsonl(settings.physics_train_file)
    physics_validation = _load_jsonl(settings.physics_validation_file)
    if settings.validation_limit is not None:
        physics_validation = physics_validation[: settings.validation_limit]

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
        physics_train, settings.state_supervision_mode, probe.seed
    )
    validation_state_masks = build_state_supervision_masks(
        physics_validation, settings.state_supervision_mode, probe.seed
    )
    state_mask_sha256 = _state_mask_sha256(train_state_masks)

    snapshot = {
        "probe": asdict(probe),
        "training": {
            **dict(raw_config["training"]),
            "output_dir": str(settings.output_dir),
            "max_steps": settings.max_steps,
            "state_supervision_mode": settings.state_supervision_mode,
        },
        "method": {
            "detection_adapter_path": str(detection_adapter_path),
            "detection_adapter": DETECTION_ADAPTER,
            "private_adapter": PRIVATE_ADAPTER,
            "family_route": [DETECTION_ADAPTER],
            "subtype_and_open_route": [DETECTION_ADAPTER, PRIVATE_ADAPTER],
            "generation_objective_task": SUBTYPE_TASK,
            "diagnostic_contract": {
                "schema_version": DIAGNOSTIC_CONTRACT_VERSION,
                "mode": contract.name,
                "generation_loss_enabled": contract.generation_loss_enabled,
                "state_loss_enabled": contract.state_loss_enabled,
                "physics_loss_enabled": contract.physics_loss_enabled,
                "state_head_gradient_expected": contract.physics_batch_enabled,
                "learning_rate_schedule": contract.learning_rate_schedule,
                "peak_learning_rate": settings.learning_rate,
                "minimum_learning_rate": (
                    D3_MIN_LEARNING_RATE
                    if contract.learning_rate_schedule == "linear_warmup_cosine_decay"
                    else settings.learning_rate
                ),
                "warmup_steps": (
                    D3_WARMUP_STEPS
                    if contract.learning_rate_schedule == "linear_warmup_cosine_decay"
                    else 0
                ),
                "formal_schedule_steps": FORMAL_DIAGNOSTIC_STEPS,
            },
        },
        "tracking": {**dict(raw_config["tracking"]), "run_name": tracking.run_name},
    }
    layout.output_dir.mkdir(parents=True, exist_ok=False)
    layout.config_snapshot.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=True), encoding="utf-8"
    )
    _write_json(layout.environment, _environment_manifest())
    input_manifest = _input_manifest(settings)
    input_manifest["detection_adapter"] = _directory_manifest(detection_adapter_path)
    _write_json(layout.input_sha256, input_manifest)
    _write_json(
        layout.generation_sample_order,
        [
            {
                "micro_step": index + 1,
                "indices": list(indices),
                "sample_ids": [generation_train[item]["sample_id"] for item in indices],
                "tasks": [generation_train[item].get("task") for item in indices],
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

    data_files = {
        "config_snapshot": layout.config_snapshot,
        "environment": layout.environment,
        "input_sha256": layout.input_sha256,
        "step_metrics": layout.step_metrics,
        "training_summary": layout.training_summary,
        "private_adapter": layout.private_adapter,
        "state_head": layout.state_head,
        "generation_sample_order": layout.generation_sample_order,
        "physics_sample_order": layout.physics_sample_order,
        "family_route_equivalence": layout.route_equivalence,
    }
    started = time.perf_counter()
    with (
        capture_console_log(layout.console_log),
        swanlab_run(
            settings=tracking,
            phase="asymmetric-physics-train",
            config=snapshot,
            artifact_dir=layout.output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        torch.manual_seed(probe.seed)
        torch.cuda.manual_seed_all(probe.seed)
        torch.cuda.reset_peak_memory_stats()
        tokenizer, model = _load_model(probe, detection_adapter_path)
        device = next(model.parameters()).device
        family_records = [
            record for record in generation_train if str(record.get("task")) == "attack_family"
        ]
        if not family_records:
            raise PhysicsTrainingError("训练集缺少 attack_family 等价性探针样本")

        _set_adapter_route(model, use_private=False, train_private=False)
        family_logits_before = _last_token_logits(
            model,
            tokenizer,
            family_records[0],
            max_length=probe.max_input_length,
            device=device,
        )
        _set_adapter_route(model, use_private=True, train_private=False)
        combined_logits_at_init = _last_token_logits(
            model,
            tokenizer,
            family_records[0],
            max_length=probe.max_input_length,
            device=device,
        )
        zero_init_difference = _max_abs_difference(family_logits_before, combined_logits_at_init)
        if zero_init_difference != 0.0:
            raise PhysicsTrainingError(
                f"物理私有 LoRA 未保持零初始化：最大 logits 差={zero_init_difference}"
            )

        _set_adapter_route(model, use_private=True, train_private=True)
        model.train()
        detection_digest_before = _adapter_parameter_digest(model, DETECTION_ADAPTER)
        private_parameters = [
            parameter
            for name, parameter in model.named_parameters()
            if parameter.requires_grad and f".{PRIVATE_ADAPTER}." in name
        ]
        if not private_parameters:
            raise PhysicsTrainingError("未发现可训练物理私有 LoRA 参数")
        leaked_trainable = [
            name
            for name, parameter in model.named_parameters()
            if parameter.requires_grad and f".{PRIVATE_ADAPTER}." not in name
        ]
        if leaked_trainable:
            raise PhysicsTrainingError("检测到私有 LoRA 之外的可训练模型参数")
        state_head = ContinuousQueueStateHead(model.config.hidden_size).to(
            device=device, dtype=torch.bfloat16
        )
        state_head.train()
        trainable = [*private_parameters, *state_head.parameters()]
        optimizer = torch.optim.AdamW(trainable, lr=settings.learning_rate)

        total_subtype_samples = 0
        total_subtype_tokens = 0
        total_generation_records_processed = 0
        total_physics_samples_processed = 0
        total_generation_forward_only_records = 0
        total_physics_forward_only_samples = 0
        empty_micro_batches = 0
        private_lora_nonzero_gradient_steps = 0
        state_head_nonzero_gradient_steps = 0
        for step in range(1, settings.max_steps + 1):
            step_started = time.perf_counter()
            learning_rate = diagnostic_learning_rate(
                contract,
                step,
                peak_learning_rate=settings.learning_rate,
            )
            for parameter_group in optimizer.param_groups:
                parameter_group["lr"] = learning_rate
            optimizer.zero_grad(set_to_none=True)
            generation_loss_value = 0.0
            step_subtype_samples = 0
            step_subtype_tokens = 0
            step_generation_records = 0
            step_generation_forward_only_records = 0
            micro_start = (step - 1) * settings.gradient_accumulation_steps
            for micro in range(settings.gradient_accumulation_steps):
                indices = generation_schedule[micro_start + micro]
                records = [generation_train[index] for index in indices]
                if contract.generation_loss_enabled:
                    generation_loss, subtype_samples, subtype_tokens = _subtype_generation_loss(
                        model,
                        tokenizer,
                        records,
                        max_length=probe.max_input_length,
                        device=device,
                    )
                    if subtype_tokens == 0:
                        empty_micro_batches += 1
                    step_generation_records += len(records)
                    step_subtype_samples += subtype_samples
                    step_subtype_tokens += subtype_tokens
                    generation_loss_value += float(generation_loss.detach().item())
                    (generation_loss / settings.gradient_accumulation_steps).backward()
                else:
                    with torch.no_grad():
                        _subtype_generation_loss(
                            model,
                            tokenizer,
                            records,
                            max_length=probe.max_input_length,
                            device=device,
                        )
                    step_generation_forward_only_records += len(records)
            if contract.generation_loss_enabled:
                generation_loss_value /= settings.gradient_accumulation_steps
            total_subtype_samples += step_subtype_samples
            total_subtype_tokens += step_subtype_tokens
            total_generation_records_processed += step_generation_records
            total_generation_forward_only_records += step_generation_forward_only_records

            state_loss_value = 0.0
            physics_loss_value = 0.0
            step_physics_samples = 0
            step_physics_forward_only_samples = 0
            indices = physics_schedule[step - 1]
            physics_records = [physics_train[index] for index in indices]
            state_batch = _state_batch(
                physics_records,
                tokenizer,
                probe.max_input_length,
                device,
                include_fluxes=True,
                state_masks=train_state_masks,
            )
            with torch.set_grad_enabled(contract.physics_batch_enabled):
                outputs = model(
                    input_ids=state_batch["input_ids"],
                    attention_mask=state_batch["attention_mask"],
                    output_hidden_states=True,
                    return_dict=True,
                )
                hidden = select_last_token_hidden(
                    outputs.hidden_states[-1], state_batch["attention_mask"]
                )
                predicted = state_head(hidden)
                state_loss = masked_state_target_loss(
                    predicted,
                    state_batch["state_targets"],
                    state_batch["state_mask"],
                )
                residual = queue_balance_residual(
                    predicted,
                    state_batch["scale"],
                    state_batch["capacity"],
                    state_batch["received"],
                    state_batch["dequeued"],
                    state_batch["dropped_before"],
                    state_batch["dropped_after"],
                )
                physics_loss = residual.square().mean()
                if contract.physics_batch_enabled:
                    auxiliary_loss = predicted.sum() * 0.0
                    if contract.state_loss_enabled:
                        auxiliary_loss = auxiliary_loss + settings.lambda_state * state_loss
                    if contract.physics_loss_enabled:
                        auxiliary_loss = auxiliary_loss + settings.lambda_physics * physics_loss
                    state_loss_value = float(state_loss.detach().item())
                    physics_loss_value = float(physics_loss.detach().item())
                    auxiliary_loss.backward()
                    step_physics_samples = len(physics_records)
                else:
                    step_physics_forward_only_samples = len(physics_records)
            total_physics_samples_processed += step_physics_samples
            total_physics_forward_only_samples += step_physics_forward_only_samples

            private_gradient_norm = _gradient_norm(private_parameters)
            state_head_gradient_norm = _gradient_norm(list(state_head.parameters()))
            private_lora_nonzero_gradient_steps += int(private_gradient_norm > 0.0)
            state_head_nonzero_gradient_steps += int(state_head_gradient_norm > 0.0)
            torch.nn.utils.clip_grad_norm_(trainable, settings.max_grad_norm)
            optimizer.step()
            elapsed = time.perf_counter() - step_started
            processed_samples = step_generation_records + step_physics_samples
            forward_samples = (
                processed_samples
                + step_generation_forward_only_records
                + step_physics_forward_only_samples
            )
            metrics = {
                "train/total_loss": generation_loss_value
                + settings.lambda_state * state_loss_value
                + settings.lambda_physics * physics_loss_value,
                "train/generation_loss": generation_loss_value,
                "train/state_loss": state_loss_value,
                "train/physics_loss": physics_loss_value,
                "train/generation_loss_enabled": float(contract.generation_loss_enabled),
                "train/state_loss_enabled": float(contract.state_loss_enabled),
                "train/physics_loss_enabled": float(contract.physics_loss_enabled),
                "train/lora_gradient_norm": private_gradient_norm,
                "train/private_lora_gradient_norm": private_gradient_norm,
                "train/state_head_gradient_norm": state_head_gradient_norm,
                "train/subtype_samples": float(step_subtype_samples),
                "train/subtype_tokens": float(step_subtype_tokens),
                "train/generation_records_processed": float(step_generation_records),
                "train/physics_samples_processed": float(step_physics_samples),
                "train/generation_forward_only_records": float(
                    step_generation_forward_only_records
                ),
                "train/physics_forward_only_samples": float(step_physics_forward_only_samples),
                "train/processed_samples": float(processed_samples),
                "train/forward_samples": float(forward_samples),
                "train/learning_rate": learning_rate,
                "train/throughput_samples_per_second": forward_samples / elapsed,
                "train/peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            }
            if not all(math.isfinite(float(value)) for value in metrics.values()):
                raise PhysicsTrainingError("训练指标出现非有限数")
            record_step_metrics(layout.step_metrics, swanlab, step=step, metrics=metrics)
            print(json.dumps({"step": step, **metrics}, ensure_ascii=False, sort_keys=True))

        detection_digest_after = _adapter_parameter_digest(model, DETECTION_ADAPTER)
        if detection_digest_after != detection_digest_before:
            raise PhysicsTrainingError("冻结的 S3 检测 LoRA 在训练后发生变化")
        _set_adapter_route(model, use_private=False, train_private=False)
        family_logits_after = _last_token_logits(
            model,
            tokenizer,
            family_records[0],
            max_length=probe.max_input_length,
            device=device,
        )
        family_route_difference = _max_abs_difference(family_logits_before, family_logits_after)
        route_equivalence = {
            "sample_id": family_records[0]["sample_id"],
            "zero_init_combined_vs_detection_max_abs_logits": zero_init_difference,
            "family_detection_only_before_vs_after_max_abs_logits": family_route_difference,
            "detection_adapter_sha256_before": detection_digest_before,
            "detection_adapter_sha256_after": detection_digest_after,
            "detection_adapter_unchanged": detection_digest_before == detection_digest_after,
            "family_route_exact": family_route_difference == 0.0,
        }
        _write_json(layout.route_equivalence, route_equivalence)
        if family_route_difference != 0.0:
            raise PhysicsTrainingError(
                f"家族关闭私有分支后输出发生变化：最大 logits 差={family_route_difference}"
            )

        _set_adapter_route(model, use_private=True, train_private=False)
        model.save_pretrained(
            layout.private_adapter_root,
            selected_adapters=[PRIVATE_ADAPTER],
            safe_serialization=True,
        )
        tokenizer.save_pretrained(layout.private_adapter)
        if not (layout.private_adapter / "adapter_config.json").is_file():
            raise PhysicsTrainingError("物理私有 LoRA 保存路径缺少 adapter_config.json")
        torch.save(
            {name: value.detach().cpu() for name, value in state_head.state_dict().items()},
            layout.state_head,
        )
        generation_validation_loss = _evaluate_generation(
            model,
            tokenizer,
            generation_validation,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
        )
        (
            validation_state_loss,
            validation_physics_loss,
            validation_state_observed_loss,
            validation_state_unobserved_loss,
        ) = _evaluate_state(
            model,
            state_head,
            tokenizer,
            physics_validation,
            batch_size=settings.validation_batch_size,
            max_length=probe.max_input_length,
            device=device,
            state_masks=validation_state_masks,
        )
        torch.cuda.synchronize()
        summary = {
            "schema_version": "flow_probe_asymmetric_physics_adapter_v1",
            "status": "finished",
            "seed": probe.seed,
            "max_steps": settings.max_steps,
            "model_id": probe.model_id,
            "detection_adapter_path": str(detection_adapter_path),
            "private_adapter_path": str(layout.private_adapter),
            "train_samples": len(generation_train),
            "subtype_validation_samples": len(generation_validation),
            "physics_train_samples": len(physics_train),
            "physics_validation_samples": len(physics_validation),
            "total_subtype_samples_seen": total_subtype_samples,
            "total_subtype_tokens_seen": total_subtype_tokens,
            "empty_generation_micro_batches": empty_micro_batches,
            "total_generation_records_processed": total_generation_records_processed,
            "total_physics_samples_processed": total_physics_samples_processed,
            "total_generation_forward_only_records": total_generation_forward_only_records,
            "total_physics_forward_only_samples": total_physics_forward_only_samples,
            "total_actual_samples_processed": (
                total_generation_records_processed + total_physics_samples_processed
            ),
            "total_forward_samples": (
                total_generation_records_processed
                + total_physics_samples_processed
                + total_generation_forward_only_records
                + total_physics_forward_only_samples
            ),
            "effective_generation_batch_size": settings.effective_generation_batch_size,
            "state_supervision_mode": settings.state_supervision_mode,
            "state_mask_sha256": state_mask_sha256,
            "lambda_state": settings.lambda_state,
            "lambda_physics": settings.lambda_physics,
            "diagnostic_contract": {
                "schema_version": DIAGNOSTIC_CONTRACT_VERSION,
                "mode": contract.name,
                "generation_loss_enabled": contract.generation_loss_enabled,
                "state_loss_enabled": contract.state_loss_enabled,
                "physics_loss_enabled": contract.physics_loss_enabled,
                "learning_rate_schedule": contract.learning_rate_schedule,
                "peak_learning_rate": settings.learning_rate,
                "minimum_learning_rate": (
                    D3_MIN_LEARNING_RATE
                    if contract.learning_rate_schedule == "linear_warmup_cosine_decay"
                    else settings.learning_rate
                ),
                "warmup_steps": (
                    D3_WARMUP_STEPS
                    if contract.learning_rate_schedule == "linear_warmup_cosine_decay"
                    else 0
                ),
                "formal_schedule_steps": FORMAL_DIAGNOSTIC_STEPS,
                "state_head_received_training_gradient": (state_head_nonzero_gradient_steps > 0),
                "state_head_nonzero_gradient_steps": state_head_nonzero_gradient_steps,
                "private_lora_nonzero_gradient_steps": private_lora_nonzero_gradient_steps,
            },
            "routing": {
                "family": [DETECTION_ADAPTER],
                "subtype_and_open": [DETECTION_ADAPTER, PRIVATE_ADAPTER],
            },
            "route_equivalence": route_equivalence,
            "validation": {
                "subtype_generation_loss": generation_validation_loss,
                "state_mse": validation_state_loss,
                "state_mse_observed": validation_state_observed_loss,
                "state_mse_unobserved": validation_state_unobserved_loss,
                "physics_residual_mse": validation_physics_loss,
            },
            "runtime_seconds": time.perf_counter() - started,
            "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            "trainable_private_lora_parameter_count": sum(
                parameter.numel() for parameter in private_parameters
            ),
            "state_head_parameter_count": sum(
                parameter.numel() for parameter in state_head.parameters()
            ),
        }
        _write_json(layout.training_summary, summary)
        swanlab.log(
            {
                "validation/subtype_generation_loss": generation_validation_loss,
                "validation/state_mse": validation_state_loss,
                "validation/state_mse_observed": validation_state_observed_loss,
                "validation/state_mse_unobserved": validation_state_unobserved_loss,
                "validation/physics_residual_mse": validation_physics_loss,
                "validation/family_route_max_abs_logits": family_route_difference,
            },
            step=settings.max_steps + 1,
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    required = (
        layout.config_snapshot,
        layout.environment,
        layout.input_sha256,
        layout.console_log,
        layout.step_metrics,
        layout.training_summary,
        layout.private_adapter,
        layout.state_head,
        layout.generation_sample_order,
        layout.physics_sample_order,
        layout.route_equivalence,
        layout.artifact_manifest,
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise PhysicsTrainingError("运行完成后制品缺失：" + ", ".join(missing))
    return json.loads(layout.artifact_manifest.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="训练任务条件化物理私有 LoRA")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--detection-adapter-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-steps", type=int, required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--validation-limit", type=int)
    parser.add_argument(
        "--diagnostic-mode",
        choices=tuple(DIAGNOSTIC_MODE_CONTRACTS),
        default="joint_constant",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise PhysicsTrainingError("配置根节点必须是映射")
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = _build_settings(
        raw,
        variant="M2",
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        validation_limit=args.validation_limit,
        lambda_physics_override=0.01,
        state_supervision_mode_override="anchor0_plus_one",
    )
    tracking = _tracking_settings(raw, args.run_name)
    manifest = train_asymmetric_physics(
        probe,
        settings,
        tracking,
        raw,
        args.detection_adapter_path,
        diagnostic_mode=args.diagnostic_mode,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
