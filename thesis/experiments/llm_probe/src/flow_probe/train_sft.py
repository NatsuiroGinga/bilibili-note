"""Qwen3-1.7B QLoRA 监督微调入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

_BINDING_SCHEMA_VERSION = "qwen_sft_training_binding_v1"
_RUN_STATE_SCHEMA_VERSION = "qwen_sft_run_state_v1"
_RUN_STATE_FIELDS = frozenset(
    {
        "schema_version",
        "run_id",
        "status",
        "current_step",
        "latest_checkpoint",
        "binding_sha256",
        "swanlab_run_id",
        "started_at",
        "updated_at",
        "failure",
    }
)
_RUN_STATUSES = frozenset({"prepared", "running", "interrupted", "failed", "finished"})
_RESUMABLE_STATUSES = frozenset({"prepared", "running", "interrupted"})
_CHECKPOINT_PATTERN = re.compile(r"checkpoint-(\d+)")
_REQUIRED_CHECKPOINT_FILES = frozenset(
    {"trainer_state.json", "optimizer.pt", "scheduler.pt", "rng_state.pth"}
)
_MODEL_CHECKPOINT_FILES = frozenset({"adapter_model.safetensors", "model.safetensors"})
_UNSET = object()


@dataclass(frozen=True)
class TrainingSettings:
    """与模型无关、可在 CPU 单元测试中检查的训练设置。"""

    train_file: Path
    validation_file: Path
    output_dir: Path
    learning_rate: float
    per_device_train_batch_size: int
    gradient_accumulation_steps: int
    num_train_epochs: float
    max_length: int
    max_new_tokens: int
    completion_only_loss: bool = True
    max_steps: int = -1
    save_steps: int = 20
    resume_from_checkpoint: str = "auto"
    attention_backend: str = "auto"
    group_by_length: bool = False

    @property
    def effective_batch_size(self) -> int:
        return self.per_device_train_batch_size * self.gradient_accumulation_steps


@dataclass(frozen=True)
class _PreparedTrainingRun:
    binding: Mapping[str, object]
    binding_sha256: str
    state_path: Path
    state: Mapping[str, object]
    resume_checkpoint: Path | None


def _validate_resume_policy(resume_policy: object) -> str:
    if not isinstance(resume_policy, str) or resume_policy not in {"auto", "never"}:
        raise ValueError("resume_from_checkpoint 只允许 auto 或 never")
    return resume_policy


def _validate_attention_backend(value: object) -> str:
    allowed = {"auto", "sdpa", "flash_attention_2"}
    if not isinstance(value, str) or value not in allowed:
        raise ValueError("attention_backend 只允许 auto、sdpa 或 flash_attention_2")
    return value


def build_training_settings(probe: ProbeConfig, data: Mapping[str, object]) -> TrainingSettings:
    """从配置构造训练设置并校验计算预算。"""
    required = (
        "train_file",
        "validation_file",
        "output_dir",
        "learning_rate",
        "per_device_train_batch_size",
        "gradient_accumulation_steps",
        "num_train_epochs",
    )
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"缺少训练字段：{', '.join(missing)}")
    batch_size = int(data["per_device_train_batch_size"])
    accumulation = int(data["gradient_accumulation_steps"])
    epochs = float(data["num_train_epochs"])
    learning_rate = float(data["learning_rate"])
    if batch_size <= 0 or accumulation <= 0 or epochs <= 0 or learning_rate <= 0:
        raise ValueError("批量、累积步数、训练轮数和学习率必须大于 0")
    save_steps = data.get("save_steps", 20)
    if type(save_steps) is not int or not 1 <= save_steps <= 20:
        raise ValueError("save_steps 必须是 1 到 20 的整数")
    resume_policy = _validate_resume_policy(data.get("resume_from_checkpoint", "auto"))
    attention_backend = _validate_attention_backend(data.get("attention_backend", "auto"))
    group_by_length = data.get("group_by_length", False)
    if type(group_by_length) is not bool:
        raise ValueError("group_by_length 必须是布尔值")
    return TrainingSettings(
        train_file=Path(str(data["train_file"])),
        validation_file=Path(str(data["validation_file"])),
        output_dir=Path(str(data["output_dir"])),
        learning_rate=learning_rate,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=accumulation,
        num_train_epochs=epochs,
        max_length=probe.max_input_length,
        max_new_tokens=probe.max_new_tokens,
        max_steps=int(data.get("max_steps", -1)),
        save_steps=save_steps,
        resume_from_checkpoint=resume_policy,
        attention_backend=attention_backend,
        group_by_length=group_by_length,
    )


def build_model_load_spec(
    probe: ProbeConfig,
    settings: TrainingSettings | None = None,
) -> dict[str, object]:
    """返回可审计的量化、LoRA 与思考模式设置。"""
    return {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": "bfloat16",
        "bnb_4bit_use_double_quant": True,
        "lora_rank": probe.lora_rank,
        "lora_alpha": probe.lora_alpha,
        "lora_dropout": probe.lora_dropout,
        "target_modules": "all-linear",
        "enable_thinking": False,
        "attention_backend": (settings.attention_backend if settings is not None else "auto"),
    }


def build_quantization_config_kwargs(compute_dtype: object) -> dict[str, object]:
    """构造普通 Qwen 路径使用的 NF4 量化参数。"""
    return {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_compute_dtype": compute_dtype,
        "bnb_4bit_use_double_quant": True,
    }


def build_model_load_kwargs(
    settings: TrainingSettings,
    quantization_config: object,
    compute_dtype: object,
) -> dict[str, object]:
    """构造模型加载参数，同时保留可选注意力后端。"""
    kwargs: dict[str, object] = {
        "quantization_config": quantization_config,
        "dtype": compute_dtype,
        "device_map": "auto",
    }
    if settings.attention_backend != "auto":
        kwargs["attn_implementation"] = settings.attention_backend
    return kwargs


def build_lora_config_kwargs(probe: ProbeConfig) -> dict[str, object]:
    """构造由 SFTTrainer 挂载的普通 Qwen LoRA 参数。"""
    return {
        "r": probe.lora_rank,
        "lora_alpha": probe.lora_alpha,
        "lora_dropout": probe.lora_dropout,
        "bias": "none",
        "task_type": "CAUSAL_LM",
        "target_modules": "all-linear",
    }


def build_optimizer_scheduler_kwargs(settings: TrainingSettings) -> dict[str, object]:
    """显式冻结普通 Qwen 的优化器、调度器和梯度裁剪默认值。"""
    return {
        "learning_rate": settings.learning_rate,
        "optim": "paged_adamw_8bit",
        "lr_scheduler_type": "linear",
        "warmup_ratio": 0.0,
        "warmup_steps": 0,
        "max_grad_norm": 1.0,
    }


def build_training_tracking_config(
    probe: ProbeConfig, settings: TrainingSettings
) -> dict[str, object]:
    """构造足以复现训练运行的 SwanLab 配置。"""
    return {
        "model_id": probe.model_id,
        "feature_view": probe.feature_view,
        "seed": probe.seed,
        "max_input_length": probe.max_input_length,
        "max_new_tokens": probe.max_new_tokens,
        "lora_rank": probe.lora_rank,
        "lora_alpha": probe.lora_alpha,
        "lora_dropout": probe.lora_dropout,
        "train_file": str(settings.train_file),
        "validation_file": str(settings.validation_file),
        "output_dir": str(settings.output_dir),
        "learning_rate": settings.learning_rate,
        "per_device_train_batch_size": settings.per_device_train_batch_size,
        "gradient_accumulation_steps": settings.gradient_accumulation_steps,
        "effective_batch_size": settings.effective_batch_size,
        "num_train_epochs": settings.num_train_epochs,
        "max_steps": settings.max_steps,
        "save_steps": settings.save_steps,
        "resume_from_checkpoint": settings.resume_from_checkpoint,
        "attention_backend": settings.attention_backend,
        "group_by_length": settings.group_by_length,
        "quantization": "NF4",
        "compute_dtype": "BF16",
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def training_binding_sha256(binding: Mapping[str, object]) -> str:
    """计算与键顺序无关的训练绑定摘要。"""
    return hashlib.sha256(_canonical_json_bytes(binding)).hexdigest()


def build_training_binding(
    probe: ProbeConfig,
    settings: TrainingSettings,
    model_path: Path,
) -> dict[str, object]:
    """冻结恢复训练时不得变化的模型、数据和科学参数。"""
    train_file = settings.train_file.expanduser().resolve()
    validation_file = settings.validation_file.expanduser().resolve()
    resolved_model_path = model_path.expanduser().resolve()
    return {
        "schema_version": _BINDING_SCHEMA_VERSION,
        "model_id": probe.model_id,
        "model_path": str(resolved_model_path),
        "feature_view": probe.feature_view,
        "seed": probe.seed,
        "train_file": str(train_file),
        "train_file_sha256": _sha256_file(train_file),
        "validation_file": str(validation_file),
        "validation_file_sha256": _sha256_file(validation_file),
        "learning_rate": settings.learning_rate,
        "per_device_train_batch_size": settings.per_device_train_batch_size,
        "gradient_accumulation_steps": settings.gradient_accumulation_steps,
        "effective_batch_size": settings.effective_batch_size,
        "num_train_epochs": settings.num_train_epochs,
        "max_steps": settings.max_steps,
        "max_length": settings.max_length,
        "max_new_tokens": settings.max_new_tokens,
        "completion_only_loss": settings.completion_only_loss,
        "lora_rank": probe.lora_rank,
        "lora_alpha": probe.lora_alpha,
        "lora_dropout": probe.lora_dropout,
        "target_modules": "all-linear",
        "attention_backend": settings.attention_backend,
        "group_by_length": settings.group_by_length,
        "training_code_sha256": _sha256_file(Path(__file__)),
    }


def _atomic_write_json(path: Path, value: object) -> None:
    """在目标目录内落临时文件后原子替换 JSON。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary_path.open("x", encoding="utf-8", newline="\n") as target:
            json.dump(
                value,
                target,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _read_json_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取有效 JSON：{path}：{error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return value


def _binding_mismatch_fields(
    stored_binding: Mapping[str, object], expected_binding: Mapping[str, object]
) -> list[str]:
    fields = set(stored_binding) | set(expected_binding)
    return sorted(
        field
        for field in fields
        if stored_binding.get(field, _UNSET) != expected_binding.get(field, _UNSET)
    )


def _validate_matching_binding(
    stored_binding: Mapping[str, object], expected_binding: Mapping[str, object]
) -> None:
    mismatch_fields = _binding_mismatch_fields(stored_binding, expected_binding)
    if mismatch_fields:
        raise ValueError(f"训练绑定不一致，字段：{', '.join(mismatch_fields)}")


def _validate_run_state(value: Mapping[str, object], path: Path) -> dict[str, object]:
    fields = set(value)
    if fields != _RUN_STATE_FIELDS:
        missing = sorted(_RUN_STATE_FIELDS - fields)
        unexpected = sorted(fields - _RUN_STATE_FIELDS)
        details = []
        if missing:
            details.append(f"缺少字段 {', '.join(missing)}")
        if unexpected:
            details.append(f"多余字段 {', '.join(unexpected)}")
        raise ValueError(f"运行状态字段非法：{path}：{'；'.join(details)}")
    if value["schema_version"] != _RUN_STATE_SCHEMA_VERSION:
        raise ValueError(f"运行状态 schema_version 非法：{path}")
    status = value["status"]
    if not isinstance(status, str) or status not in _RUN_STATUSES:
        raise ValueError(f"运行状态 status 非法：{path}：{status}")
    current_step = value["current_step"]
    if type(current_step) is not int or current_step < 0:
        raise ValueError(f"运行状态 current_step 非法：{path}：{current_step}")
    binding_sha256 = value["binding_sha256"]
    if (
        not isinstance(binding_sha256, str)
        or len(binding_sha256) != 64
        or any(character not in "0123456789abcdef" for character in binding_sha256)
    ):
        raise ValueError(f"运行状态 binding_sha256 非法：{path}")
    for field in ("run_id", "started_at", "updated_at"):
        if not isinstance(value[field], str) or not value[field]:
            raise ValueError(f"运行状态 {field} 非法：{path}")
    for field in ("latest_checkpoint", "swanlab_run_id", "failure"):
        if value[field] is not None and not isinstance(value[field], str):
            raise ValueError(f"运行状态 {field} 非法：{path}")
    return dict(value)


def _checkpoint_candidates(output_dir: Path) -> list[tuple[int, Path]]:
    candidates = []
    for path in output_dir.iterdir():
        match = _CHECKPOINT_PATTERN.fullmatch(path.name)
        if path.is_dir() and match is not None:
            candidates.append((int(match.group(1)), path))
    return sorted(candidates, key=lambda item: item[0], reverse=True)


def _missing_checkpoint_files(checkpoint: Path) -> list[str]:
    missing = sorted(
        filename for filename in _REQUIRED_CHECKPOINT_FILES if not (checkpoint / filename).is_file()
    )
    if not any((checkpoint / filename).is_file() for filename in _MODEL_CHECKPOINT_FILES):
        missing.append("adapter_model.safetensors 或 model.safetensors")
    return missing


def _incomplete_checkpoint_details(output_dir: Path) -> str:
    candidates = _checkpoint_candidates(output_dir)
    if not candidates:
        return "未找到 checkpoint-<step> 目录"
    details = []
    for _, checkpoint in candidates:
        missing = _missing_checkpoint_files(checkpoint)
        if missing:
            details.append(f"{checkpoint.name} 缺少 {', '.join(missing)}")
    return "；".join(details) if details else "未找到可恢复检查点"


def resolve_resume_checkpoint(
    output_dir: Path,
    expected_binding: Mapping[str, object],
    resume_policy: str,
) -> Path | None:
    """选择绑定一致、未完成运行中步数最大的完整检查点。"""
    policy = _validate_resume_policy(resume_policy)
    if policy == "never" or not output_dir.exists():
        return None
    if not output_dir.is_dir():
        raise ValueError(f"训练输出路径不是目录：{output_dir}")

    binding_path = output_dir / "training_binding.json"
    state_path = output_dir / "run_state.json"
    missing_metadata = [str(path.name) for path in (binding_path, state_path) if not path.is_file()]
    if missing_metadata:
        raise ValueError(f"恢复元数据缺失：{', '.join(missing_metadata)}")

    stored_binding = _read_json_object(binding_path)
    _validate_matching_binding(stored_binding, expected_binding)
    state = _validate_run_state(_read_json_object(state_path), state_path)
    stored_digest = training_binding_sha256(stored_binding)
    if state["binding_sha256"] != stored_digest:
        raise ValueError("run_state.json 的 binding_sha256 与 training_binding.json 不一致")
    if state["status"] not in _RESUMABLE_STATUSES:
        return None

    for _, checkpoint in _checkpoint_candidates(output_dir):
        if not _missing_checkpoint_files(checkpoint):
            return checkpoint
    return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _new_run_state(binding_sha256: str) -> dict[str, object]:
    timestamp = _utc_now()
    return {
        "schema_version": _RUN_STATE_SCHEMA_VERSION,
        "run_id": uuid.uuid4().hex,
        "status": "prepared",
        "current_step": 0,
        "latest_checkpoint": None,
        "binding_sha256": binding_sha256,
        "swanlab_run_id": None,
        "started_at": timestamp,
        "updated_at": timestamp,
        "failure": None,
    }


def _training_config_snapshot(
    probe: ProbeConfig,
    settings: TrainingSettings,
    binding_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": "qwen_sft_training_config_v1",
        "binding_sha256": binding_sha256,
        "model_load_spec": build_model_load_spec(probe, settings),
        "training": build_training_tracking_config(probe, settings),
    }


def _prepare_training_run(
    probe: ProbeConfig,
    settings: TrainingSettings,
    model_path: Path,
) -> _PreparedTrainingRun:
    """在加载模型前创建新运行或验证可恢复运行。"""
    binding = build_training_binding(probe, settings, model_path)
    binding_sha256 = training_binding_sha256(binding)
    output_dir = settings.output_dir
    binding_path = output_dir / "training_binding.json"
    state_path = output_dir / "run_state.json"
    binding_exists = binding_path.is_file()
    state_exists = state_path.is_file()

    if not binding_exists and not state_exists:
        if output_dir.exists():
            if not output_dir.is_dir():
                raise ValueError(f"训练输出路径不是目录：{output_dir}")
            existing_names = sorted(path.name for path in output_dir.iterdir())
            if existing_names:
                raise ValueError(
                    "输出目录非空且缺少恢复元数据，拒绝覆盖：" f"{', '.join(existing_names)}"
                )
        output_dir.mkdir(parents=True, exist_ok=True)
        state = _new_run_state(binding_sha256)
        _atomic_write_json(binding_path, binding)
        _atomic_write_json(
            output_dir / "training_config.json",
            _training_config_snapshot(probe, settings, binding_sha256),
        )
        _atomic_write_json(state_path, state)
        return _PreparedTrainingRun(
            binding=binding,
            binding_sha256=binding_sha256,
            state_path=state_path,
            state=state,
            resume_checkpoint=None,
        )

    if not binding_exists or not state_exists:
        missing_name = binding_path.name if not binding_exists else state_path.name
        raise ValueError(f"已有运行缺少 {missing_name}，拒绝覆盖或恢复")
    if settings.resume_from_checkpoint == "never":
        raise ValueError("输出目录已存在且 resume_from_checkpoint=never，拒绝覆盖")

    stored_binding = _read_json_object(binding_path)
    _validate_matching_binding(stored_binding, binding)
    state = _validate_run_state(_read_json_object(state_path), state_path)
    if state["binding_sha256"] != training_binding_sha256(stored_binding):
        raise ValueError("run_state.json 的 binding_sha256 与 training_binding.json 不一致")
    if state["status"] not in _RESUMABLE_STATUSES:
        raise ValueError(f"运行状态为 {state['status']}，拒绝覆盖或恢复")

    resume_checkpoint = resolve_resume_checkpoint(
        output_dir,
        binding,
        settings.resume_from_checkpoint,
    )
    if resume_checkpoint is None:
        details = _incomplete_checkpoint_details(output_dir)
        raise ValueError(f"已有运行没有完整检查点，拒绝恢复：{details}")

    match = _CHECKPOINT_PATTERN.fullmatch(resume_checkpoint.name)
    if match is None:
        raise ValueError(f"检查点目录名非法：{resume_checkpoint}")
    state.update(
        {
            "status": "prepared",
            "current_step": int(match.group(1)),
            "latest_checkpoint": str(resume_checkpoint),
            "updated_at": _utc_now(),
            "failure": None,
        }
    )
    _atomic_write_json(state_path, state)
    return _PreparedTrainingRun(
        binding=binding,
        binding_sha256=binding_sha256,
        state_path=state_path,
        state=state,
        resume_checkpoint=resume_checkpoint,
    )


class RestartStateCallback:
    """把 Trainer 生命周期转换为可恢复的原子运行状态。"""

    def __init__(
        self,
        state_path: Path,
        initial_state: Mapping[str, object] | None = None,
    ) -> None:
        self.state_path = state_path
        source = _read_json_object(state_path) if initial_state is None else dict(initial_state)
        self._state = _validate_run_state(source, state_path)

    @property
    def status(self) -> str:
        return str(self._state["status"])

    def _transition(
        self,
        status: str,
        *,
        current_step: int | None = None,
        latest_checkpoint: object = _UNSET,
        failure: object = _UNSET,
    ) -> None:
        if status not in _RUN_STATUSES:
            raise ValueError(f"非法运行状态：{status}")
        next_state = dict(self._state)
        next_state["status"] = status
        if current_step is not None:
            next_state["current_step"] = current_step
        if latest_checkpoint is not _UNSET:
            next_state["latest_checkpoint"] = latest_checkpoint
        if failure is not _UNSET:
            next_state["failure"] = failure
        next_state["updated_at"] = _utc_now()
        self._state = _validate_run_state(next_state, self.state_path)
        _atomic_write_json(self.state_path, self._state)

    def _step(self, state: object) -> int:
        trainer_step = int(getattr(state, "global_step", 0))
        return max(trainer_step, int(self._state["current_step"]))

    def on_train_begin(self, args, state, control, **kwargs):
        del args, kwargs
        self._transition("running", current_step=self._step(state), failure=None)
        return control

    def on_save(self, args, state, control, **kwargs):
        del kwargs
        current_step = self._step(state)
        checkpoint = Path(str(args.output_dir)) / f"checkpoint-{current_step}"
        self._transition(
            "running",
            current_step=current_step,
            latest_checkpoint=str(checkpoint),
            failure=None,
        )
        return control

    def on_train_end(self, args, state, control, **kwargs):
        del args, kwargs
        self.mark_finished(self._step(state))
        return control

    def mark_finished(self, current_step: int | None = None) -> None:
        self._transition("finished", current_step=current_step, failure=None)

    def mark_interrupted(self, error: BaseException) -> None:
        self._transition(
            "interrupted",
            failure=f"{type(error).__name__}: {error}",
        )

    def mark_failed(self, error: BaseException) -> None:
        self._transition("failed", failure=f"{type(error).__name__}: {error}")


def build_sft_config_kwargs(
    settings: TrainingSettings,
    tracking_enabled: bool,
) -> dict[str, object]:
    """构造保持科学参数不变的步级检查点配置。"""
    return {
        "output_dir": str(settings.output_dir),
        "max_length": settings.max_length,
        "completion_only_loss": settings.completion_only_loss,
        "per_device_train_batch_size": settings.per_device_train_batch_size,
        "per_device_eval_batch_size": settings.per_device_train_batch_size,
        "gradient_accumulation_steps": settings.gradient_accumulation_steps,
        "num_train_epochs": settings.num_train_epochs,
        "max_steps": settings.max_steps,
        "bf16": True,
        "gradient_checkpointing": True,
        "gradient_checkpointing_kwargs": {"use_reentrant": False},
        **build_optimizer_scheduler_kwargs(settings),
        "eval_strategy": "epoch",
        "save_strategy": "steps",
        "save_steps": settings.save_steps,
        "save_total_limit": 3,
        "save_only_model": False,
        "logging_steps": 1,
        "report_to": "swanlab" if tracking_enabled else "none",
        "group_by_length": settings.group_by_length,
    }


def _run_trainer_with_resume(
    trainer,
    resume_checkpoint: Path | None,
    callback: RestartStateCallback,
):
    resume_argument = str(resume_checkpoint) if resume_checkpoint is not None else None
    try:
        return trainer.train(resume_from_checkpoint=resume_argument)
    except KeyboardInterrupt as error:
        callback.mark_interrupted(error)
        raise
    except Exception as error:
        callback.mark_failed(error)
        raise


def load_training_records(path: Path) -> list[dict[str, object]]:
    """按文件顺序加载训练记录并保留包括 sample_id 在内的全部字段。"""
    with path.open("r", encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    return load_training_records(path)


def build_chat_training_record(
    record: Mapping[str, object],
    tokenizer,
) -> dict[str, object]:
    """构造单条聊天样本；sample_id 仅作为不可见元数据保留。"""
    prompt = tokenizer.apply_chat_template(
        [{"role": "user", "content": record["prompt"]}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    formatted: dict[str, object] = {
        "prompt": prompt,
        "completion": str(record["completion"]) + tokenizer.eos_token,
    }
    if "sample_id" in record:
        formatted["sample_id"] = record["sample_id"]
    return formatted


def build_chat_training_records(
    records: Iterable[Mapping[str, object]],
    tokenizer,
) -> list[dict[str, object]]:
    """按输入顺序构造普通 Qwen 聊天样本。"""
    return [build_chat_training_record(record, tokenizer) for record in records]


def build_chat_dataset(
    records: Iterable[Mapping[str, object]],
    tokenizer,
):
    """构造供 SFTTrainer 使用的聊天数据集。"""
    from datasets import Dataset

    return Dataset.from_list(build_chat_training_records(records, tokenizer))


def _chat_dataset(records, tokenizer):
    return build_chat_dataset(records, tokenizer)


def build_qwen_model_and_tokenizer(
    probe: ProbeConfig,
    settings: TrainingSettings,
    torch_module,
) -> tuple[object, object]:
    """按普通 Qwen 路径加载分词器与量化模型。"""
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(probe.model_id, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        **build_quantization_config_kwargs(torch_module.bfloat16)
    )
    model = AutoModelForCausalLM.from_pretrained(
        probe.model_id,
        **build_model_load_kwargs(settings, quantization, torch_module.bfloat16),
    )
    return model, tokenizer


def build_lora_config(probe: ProbeConfig):
    """构造由普通 SFTTrainer 挂载的 LoRA 配置。"""
    from peft import LoraConfig

    return LoraConfig(**build_lora_config_kwargs(probe))


def build_sft_trainer(
    probe: ProbeConfig,
    settings: TrainingSettings,
    *,
    model: object,
    tokenizer: object,
    train_dataset: object,
    validation_dataset: object,
    tracking_enabled: bool,
    callbacks: list[object],
):
    """以普通入口的 LoRA 挂载和训练参数构造 SFTTrainer。"""
    from trl import SFTConfig, SFTTrainer

    config_kwargs = build_sft_config_kwargs(settings, tracking_enabled)
    config_kwargs.update({"seed": probe.seed, "data_seed": probe.seed})
    return SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        peft_config=build_lora_config(probe),
        args=SFTConfig(**config_kwargs),
        callbacks=callbacks,
    )


def _train_impl(
    probe: ProbeConfig,
    settings: TrainingSettings,
    tracking_enabled: bool,
    prepared: _PreparedTrainingRun,
    state_callback: RestartStateCallback,
) -> dict[str, object]:
    """在 CUDA 环境执行 QLoRA 监督微调并保存运行摘要。"""
    import torch
    from transformers import TrainerCallback

    class _RestartCallbackAdapter(TrainerCallback):
        def on_train_begin(self, args, state, control, **kwargs):
            return state_callback.on_train_begin(args, state, control, **kwargs)

        def on_save(self, args, state, control, **kwargs):
            return state_callback.on_save(args, state, control, **kwargs)

        def on_train_end(self, args, state, control, **kwargs):
            return state_callback.on_train_end(args, state, control, **kwargs)

    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动大模型训练")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("当前 GPU 不支持 BF16")

    model, tokenizer = build_qwen_model_and_tokenizer(probe, settings, torch)
    train_dataset = build_chat_dataset(
        load_training_records(settings.train_file),
        tokenizer,
    )
    validation_dataset = build_chat_dataset(
        load_training_records(settings.validation_file),
        tokenizer,
    )
    trainer = build_sft_trainer(
        probe,
        settings,
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        validation_dataset=validation_dataset,
        tracking_enabled=tracking_enabled,
        callbacks=[_RestartCallbackAdapter()],
    )
    train_result = _run_trainer_with_resume(
        trainer,
        prepared.resume_checkpoint,
        state_callback,
    )
    final_dir = settings.output_dir / "final_adapter"
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(final_dir)
    summary = {
        "model_id": probe.model_id,
        "seed": probe.seed,
        "effective_batch_size": settings.effective_batch_size,
        "train_samples": len(train_dataset),
        "validation_samples": len(validation_dataset),
        "metrics": train_result.metrics,
        "trainer_log_history": trainer.state.log_history,
        "model_load_spec": build_model_load_spec(probe, settings),
        "binding_sha256": prepared.binding_sha256,
        "resumed_from_checkpoint": (
            str(prepared.resume_checkpoint) if prepared.resume_checkpoint is not None else None
        ),
    }
    _atomic_write_json(settings.output_dir / "training_summary.json", summary)
    state_callback.mark_finished(int(trainer.state.global_step))
    return summary


def train(
    probe: ProbeConfig,
    settings: TrainingSettings,
    tracking: TrackingSettings | None = None,
) -> dict[str, object]:
    """验证恢复边界后执行训练，并按配置写入 SwanLab。"""
    prepared = _prepare_training_run(probe, settings, Path(probe.model_id))
    state_callback = RestartStateCallback(prepared.state_path, prepared.state)
    try:
        if tracking is None:
            with capture_console_log(settings.output_dir / "console.log"):
                return _train_impl(
                    probe,
                    settings,
                    tracking_enabled=False,
                    prepared=prepared,
                    state_callback=state_callback,
                )

        tracking_config = build_training_tracking_config(probe, settings)
        tracked_metrics_path = settings.output_dir / "swanlab_metrics.json"
        data_files = {
            "final_adapter": settings.output_dir / "final_adapter",
            "run_state": prepared.state_path,
            "swanlab_metrics": tracked_metrics_path,
            "train_file": settings.train_file,
            "training_binding": settings.output_dir / "training_binding.json",
            "training_config": settings.output_dir / "training_config.json",
            "training_summary": settings.output_dir / "training_summary.json",
            "validation_file": settings.validation_file,
        }
        with (
            capture_console_log(settings.output_dir / "console.log"),
            swanlab_run(
                tracking,
                phase="train",
                config=tracking_config,
                artifact_dir=settings.output_dir,
                data_files=data_files,
            ) as swanlab,
        ):
            summary = _train_impl(
                probe,
                settings,
                tracking_enabled=True,
                prepared=prepared,
                state_callback=state_callback,
            )
            tracked_metrics = flatten_scalar_metrics(summary, prefix="training/final")
            _atomic_write_json(tracked_metrics_path, tracked_metrics)
            swanlab.log(tracked_metrics)
            return summary
    except KeyboardInterrupt as error:
        if state_callback.status != "interrupted":
            state_callback.mark_interrupted(error)
        raise
    except Exception as error:
        if state_callback.status != "failed":
            state_callback.mark_failed(error)
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qwen3-1.7B 恶意流量 QLoRA 训练")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    probe = ProbeConfig.from_mapping(raw["probe"])
    if args.model_path is not None:
        probe = override_model_id(probe, str(args.model_path))
    settings = build_training_settings(probe, raw["training"])
    tracking = TrackingSettings.from_mapping(raw["tracking"])
    summary = train(probe, settings, tracking)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
