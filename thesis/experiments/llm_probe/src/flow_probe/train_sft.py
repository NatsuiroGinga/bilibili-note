"""Qwen3-1.7B QLoRA 监督微调入口。"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from flow_probe.config import ProbeConfig, override_model_id
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)


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

    @property
    def effective_batch_size(self) -> int:
        return self.per_device_train_batch_size * self.gradient_accumulation_steps


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
    )


def build_model_load_spec(probe: ProbeConfig) -> dict[str, object]:
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
        "quantization": "NF4",
        "compute_dtype": "BF16",
    }


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def _chat_dataset(records, tokenizer):
    from datasets import Dataset

    formatted = []
    for record in records:
        prompt = tokenizer.apply_chat_template(
            [{"role": "user", "content": record["prompt"]}],
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        formatted.append(
            {
                "prompt": prompt,
                "completion": str(record["completion"]) + tokenizer.eos_token,
            }
        )
    return Dataset.from_list(formatted)


def _train_impl(
    probe: ProbeConfig,
    settings: TrainingSettings,
    tracking_enabled: bool,
) -> dict[str, object]:
    """在 CUDA 环境执行 QLoRA 监督微调并保存运行摘要。"""
    import torch
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise RuntimeError("未检测到 CUDA，拒绝启动大模型训练")
    if not torch.cuda.is_bf16_supported():
        raise RuntimeError("当前 GPU 不支持 BF16")

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(probe.model_id, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        probe.model_id,
        quantization_config=quantization,
        dtype=torch.bfloat16,
        device_map="auto",
    )
    train_dataset = _chat_dataset(_load_jsonl(settings.train_file), tokenizer)
    validation_dataset = _chat_dataset(_load_jsonl(settings.validation_file), tokenizer)
    peft_config = LoraConfig(
        r=probe.lora_rank,
        lora_alpha=probe.lora_alpha,
        lora_dropout=probe.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        peft_config=peft_config,
        args=SFTConfig(
            output_dir=str(settings.output_dir),
            max_length=settings.max_length,
            completion_only_loss=True,
            per_device_train_batch_size=settings.per_device_train_batch_size,
            per_device_eval_batch_size=settings.per_device_train_batch_size,
            gradient_accumulation_steps=settings.gradient_accumulation_steps,
            learning_rate=settings.learning_rate,
            num_train_epochs=settings.num_train_epochs,
            max_steps=settings.max_steps,
            bf16=True,
            gradient_checkpointing=True,
            gradient_checkpointing_kwargs={"use_reentrant": False},
            optim="paged_adamw_8bit",
            eval_strategy="epoch",
            save_strategy="epoch",
            save_total_limit=3,
            logging_steps=1,
            report_to="swanlab" if tracking_enabled else "none",
            seed=probe.seed,
            data_seed=probe.seed,
        ),
    )
    train_result = trainer.train()
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
        "model_load_spec": build_model_load_spec(probe),
    }
    (settings.output_dir / "training_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def train(
    probe: ProbeConfig,
    settings: TrainingSettings,
    tracking: TrackingSettings | None = None,
) -> dict[str, object]:
    """执行训练，并在配置跟踪时强制写入 SwanLab 在线项目。"""
    if tracking is None:
        with capture_console_log(settings.output_dir / "console.log"):
            return _train_impl(probe, settings, tracking_enabled=False)

    tracking_config = build_training_tracking_config(probe, settings)
    tracked_metrics_path = settings.output_dir / "swanlab_metrics.json"
    data_files = {
        "final_adapter": settings.output_dir / "final_adapter",
        "swanlab_metrics": tracked_metrics_path,
        "train_file": settings.train_file,
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
        summary = _train_impl(probe, settings, tracking_enabled=True)
        tracked_metrics = flatten_scalar_metrics(summary, prefix="training/final")
        tracked_metrics_path.write_text(
            json.dumps(tracked_metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        swanlab.log(tracked_metrics)
        return summary


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
