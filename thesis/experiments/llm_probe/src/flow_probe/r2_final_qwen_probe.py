from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import yaml

from flow_probe import r2_final_distilbert_probe as r2
from flow_probe import shared_b0_distilbert_baseline as metrics
from flow_probe.r2_final_views import PreparedVariantViews, VariantSplit, build_variant_views


SCHEMA_VERSION = "flow_probe_r2_final_qwen_probe_v1"
OFFICIAL_MODEL_ID = "Qwen/Qwen3-0.6B"
CANDIDATE_DETECTION_ROWS = 7_579
CANDIDATE_PHYSICS_ROWS = 2_421
CANDIDATE_TOTAL_ROWS = 10_000
FUSION_LIMIT = 0.1
ALLOWED_VARIANTS = ("F-A", "F-P", "F-S")
LABEL_TEXT = {0: '{"label":"benign"}', 1: '{"label":"malicious"}'}


class QwenR2ProbeError(ValueError):
    """表示 Qwen3-0.6B R2 开发候选合同被违反。"""


@dataclass(frozen=True)
class ModelSettings:
    identifier: str
    source: Path
    max_length: int
    max_new_tokens: int
    attention_backend: str
    lora_rank: int
    lora_alpha: int
    lora_dropout: float


@dataclass(frozen=True)
class TrainingSettings:
    per_device_train_batch_size: int
    per_device_eval_batch_size: int
    gradient_accumulation_steps: int
    max_steps: int
    learning_rate: float
    weight_decay: float
    warmup_ratio: float
    max_grad_norm: float
    save_steps: int
    resume_from_checkpoint: str


@dataclass(frozen=True)
class EvaluationSettings:
    threshold: float
    calibration_bins: int
    protocol: str


@dataclass(frozen=True)
class TrackingSettings:
    project: str
    workspace: str
    run_name: str
    mode: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ProbeConfig:
    variant: str
    seed: int
    model: ModelSettings
    training: TrainingSettings
    evaluation: EvaluationSettings
    tracking: TrackingSettings
    output_root: Path
    r2_contract: r2.ProbeConfig
    r2_contract_sha256: str
    quic_training_weight: float
    file_sha256: str
    project_root: Path


def bounded_fusion_strength(logit: float, *, limit: float = FUSION_LIMIT) -> float:
    """返回不超过固定幅度的旁路融合强度。"""

    if not math.isfinite(logit) or not math.isfinite(limit) or limit <= 0:
        raise QwenR2ProbeError("融合强度参数必须是有限数且上界大于零")
    return limit * math.tanh(logit)


def validate_candidate_role_counts(
    *,
    detection_rows: int,
    physics_rows: int,
    total_rows: int,
) -> dict[str, int | bool]:
    """冻结开发候选的检测监督与物理辅助职责。"""

    actual = (detection_rows, physics_rows, total_rows)
    expected = (
        CANDIDATE_DETECTION_ROWS,
        CANDIDATE_PHYSICS_ROWS,
        CANDIDATE_TOTAL_ROWS,
    )
    if actual != expected or detection_rows + physics_rows != total_rows:
        raise QwenR2ProbeError("检测监督与物理辅助样本数不符合冻结开发合同")
    return {
        "detection_supervision_rows": detection_rows,
        "physics_auxiliary_rows": physics_rows,
        "total_rows": total_rows,
        "ns3_detection_label_training": False,
    }


def validate_model_contract(
    *,
    identifier: str,
    source: str,
    quic_expert_ready: bool,
    quic_training_weight: float,
) -> None:
    """拒绝错误基座、历史目录和未放行 QUIC 训练。"""

    if identifier != OFFICIAL_MODEL_ID:
        raise QwenR2ProbeError(f"模型必须是官方后训练版 {OFFICIAL_MODEL_ID}")
    normalized = source.replace("\\", "/").lower()
    if "qwen3-0.6b" not in normalized or "distilbert" in normalized:
        raise QwenR2ProbeError("模型来源必须是独立的 Qwen3-0.6B 快照")
    if quic_expert_ready or quic_training_weight != 0.0:
        raise QwenR2ProbeError("QUIC v8 放行前必须保持 UNKNOWN 回退且训练权重为零")


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QwenR2ProbeError(f"{description} 必须是映射")
    return value


def _string(value: object, description: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise QwenR2ProbeError(f"{description} 必须是无首尾空白的非空字符串")
    return value


def _integer(value: object, description: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise QwenR2ProbeError(f"{description} 必须是不小于 {minimum} 的整数")
    return value


def _number(value: object, description: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise QwenR2ProbeError(f"{description} 必须是数值")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise QwenR2ProbeError(f"{description} 必须是不小于 {minimum} 的有限数")
    return result


def _resolve_path(value: object, root: Path, description: str) -> Path:
    raw = Path(_string(value, description)).expanduser()
    return Path(os.path.abspath(os.fspath(raw if raw.is_absolute() else root / raw)))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: Path, *, trusted_root: Path) -> ProbeConfig:
    root = Path(os.path.abspath(os.fspath(trusted_root.expanduser())))
    config_path = Path(os.path.abspath(os.fspath(path.expanduser())))
    try:
        config_path.relative_to(root / "configs")
    except ValueError as error:
        raise QwenR2ProbeError("Qwen 配置必须位于受信任 configs 目录") from error
    snapshot = config_path.read_bytes()
    raw = _mapping(yaml.safe_load(snapshot.decode("utf-8")), "Qwen 配置")
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise QwenR2ProbeError("Qwen 配置 schema_version 不一致")
    variant = _string(raw.get("variant"), "variant")
    if variant not in ALLOWED_VARIANTS:
        raise QwenR2ProbeError(f"首批开发候选只允许 {ALLOWED_VARIANTS}")
    seed = _integer(raw.get("seed"), "seed")
    if seed != 42:
        raise QwenR2ProbeError("首批 Qwen 开发候选只允许种子 42")

    candidate = _mapping(raw.get("candidate_contract"), "candidate_contract")
    validate_candidate_role_counts(
        detection_rows=_integer(
            candidate.get("detection_supervision_rows"),
            "candidate_contract.detection_supervision_rows",
        ),
        physics_rows=_integer(
            candidate.get("physics_auxiliary_rows"),
            "candidate_contract.physics_auxiliary_rows",
        ),
        total_rows=_integer(candidate.get("total_rows"), "candidate_contract.total_rows"),
    )
    if candidate.get("final_test_visible") is not False:
        raise QwenR2ProbeError("开发候选必须保持最终测试不可见")

    contract_raw = _mapping(raw.get("r2_contract"), "r2_contract")
    contract_path = _resolve_path(contract_raw.get("path"), root, "r2_contract.path")
    expected_contract_sha = _string(contract_raw.get("sha256"), "r2_contract.sha256")
    actual_contract_sha = _sha256(contract_path)
    if actual_contract_sha != expected_contract_sha:
        raise QwenR2ProbeError("冻结 R2 数据与物理合同 SHA-256 不一致")
    base_contract = r2.load_config(contract_path, trusted_root=root)
    if base_contract.variant != variant or base_contract.seed != seed:
        raise QwenR2ProbeError("Qwen 组别或种子与冻结 R2 合同不一致")

    model_raw = _mapping(raw.get("model"), "model")
    model = ModelSettings(
        identifier=_string(model_raw.get("identifier"), "model.identifier"),
        source=_resolve_path(model_raw.get("source"), root, "model.source"),
        max_length=_integer(model_raw.get("max_length"), "model.max_length", minimum=1),
        max_new_tokens=_integer(
            model_raw.get("max_new_tokens"), "model.max_new_tokens", minimum=1
        ),
        attention_backend=_string(
            model_raw.get("attention_backend"), "model.attention_backend"
        ),
        lora_rank=_integer(model_raw.get("lora_rank"), "model.lora_rank", minimum=1),
        lora_alpha=_integer(model_raw.get("lora_alpha"), "model.lora_alpha", minimum=1),
        lora_dropout=_number(model_raw.get("lora_dropout"), "model.lora_dropout"),
    )
    quic_weight = _number(raw.get("quic_training_weight"), "quic_training_weight")
    validate_model_contract(
        identifier=model.identifier,
        source=str(model.source),
        quic_expert_ready=base_contract.physics.quic_expert_ready,
        quic_training_weight=quic_weight,
    )
    if model.attention_backend not in {"sdpa", "flash_attention_2"}:
        raise QwenR2ProbeError("注意力后端只允许 sdpa 或 flash_attention_2")

    training_raw = _mapping(raw.get("training"), "training")
    training = TrainingSettings(
        per_device_train_batch_size=_integer(
            training_raw.get("per_device_train_batch_size"),
            "training.per_device_train_batch_size",
            minimum=1,
        ),
        per_device_eval_batch_size=_integer(
            training_raw.get("per_device_eval_batch_size"),
            "training.per_device_eval_batch_size",
            minimum=1,
        ),
        gradient_accumulation_steps=_integer(
            training_raw.get("gradient_accumulation_steps"),
            "training.gradient_accumulation_steps",
            minimum=1,
        ),
        max_steps=_integer(training_raw.get("max_steps"), "training.max_steps", minimum=1),
        learning_rate=_number(
            training_raw.get("learning_rate"), "training.learning_rate", minimum=1e-12
        ),
        weight_decay=_number(training_raw.get("weight_decay"), "training.weight_decay"),
        warmup_ratio=_number(training_raw.get("warmup_ratio"), "training.warmup_ratio"),
        max_grad_norm=_number(
            training_raw.get("max_grad_norm"), "training.max_grad_norm", minimum=1e-12
        ),
        save_steps=_integer(training_raw.get("save_steps"), "training.save_steps", minimum=1),
        resume_from_checkpoint=_string(
            training_raw.get("resume_from_checkpoint"),
            "training.resume_from_checkpoint",
        ),
    )
    if (
        training.per_device_train_batch_size * training.gradient_accumulation_steps != 4
        or training.max_steps != 200
        or training.save_steps > 20
    ):
        raise QwenR2ProbeError("Qwen 首批必须保持有效批量 4、200 步和至多 20 步检查点")

    evaluation_raw = _mapping(raw.get("evaluation"), "evaluation")
    evaluation = EvaluationSettings(
        threshold=_number(evaluation_raw.get("threshold"), "evaluation.threshold"),
        calibration_bins=_integer(
            evaluation_raw.get("calibration_bins"),
            "evaluation.calibration_bins",
            minimum=1,
        ),
        protocol=_string(evaluation_raw.get("protocol"), "evaluation.protocol"),
    )
    if evaluation.threshold != 0.5:
        raise QwenR2ProbeError("开发候选阈值必须固定为 0.5")
    if evaluation.protocol != "constrained_json_label_likelihood_v1":
        raise QwenR2ProbeError("生成评价协议不是冻结版本")

    tracking_raw = _mapping(raw.get("tracking"), "tracking")
    tags = tracking_raw.get("tags")
    if not isinstance(tags, list) or not tags:
        raise QwenR2ProbeError("tracking.tags 必须是非空列表")
    if any(not isinstance(value, str) or len(value) > 20 for value in tags):
        raise QwenR2ProbeError("每个 SwanLab 标签必须是至多 20 字符的字符串")
    tracking = TrackingSettings(
        project=_string(tracking_raw.get("project"), "tracking.project"),
        workspace=_string(tracking_raw.get("workspace"), "tracking.workspace"),
        run_name=_string(tracking_raw.get("run_name"), "tracking.run_name"),
        mode=_string(tracking_raw.get("mode"), "tracking.mode"),
        tags=tuple(_string(value, "tracking.tags") for value in tags),
    )
    if (
        tracking.project != "malicious-traffic-llm"
        or tracking.workspace != "mortiswang"
        or tracking.mode != "online"
    ):
        raise QwenR2ProbeError("正式开发候选必须使用冻结 SwanLab 在线项目")

    output_root = _resolve_path(raw.get("output_root"), root, "output_root")
    if "distilbert" in str(output_root).lower():
        raise QwenR2ProbeError("Qwen 输出不得写入 DistilBERT 历史目录")
    return ProbeConfig(
        variant=variant,
        seed=seed,
        model=model,
        training=training,
        evaluation=evaluation,
        tracking=tracking,
        output_root=output_root,
        r2_contract=base_contract,
        r2_contract_sha256=actual_contract_sha,
        quic_training_weight=quic_weight,
        file_sha256=hashlib.sha256(snapshot).hexdigest(),
        project_root=root,
    )


def _prompt(tokenizer: Any, text: str) -> str:
    instruction = (
        "判断以下网络流量是否恶意。只允许输出单键 JSON："
        '{"label":"benign"} 或 {"label":"malicious"}。\n'
        f"流量特征：{text}"
    )
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": instruction}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )


class _Dataset:
    def __init__(self, split: VariantSplit, tokenizer: Any, max_length: int) -> None:
        self.split = split
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, index: int) -> dict[str, object]:
        prompt_ids = self.tokenizer(
            _prompt(self.tokenizer, self.split.texts[index]),
            add_special_tokens=False,
        )["input_ids"]
        completion_ids = self.tokenizer(
            LABEL_TEXT[int(self.split.labels[index])] + self.tokenizer.eos_token,
            add_special_tokens=False,
        )["input_ids"]
        available = self.max_length - len(completion_ids)
        if available <= 0:
            raise QwenR2ProbeError("生成标签长度超过最大上下文")
        prompt_ids = prompt_ids[-available:]
        return {
            "input_ids": [*prompt_ids, *completion_ids],
            "labels": [-100] * len(prompt_ids) + list(completion_ids),
            "sidecar_sequence": self.split.sidecar_sequence[index],
            "sidecar_valid_mask": self.split.sidecar_valid_mask[index],
            "sidecar_gate": float(self.split.sidecar_gate[index]),
            "sample_id": self.split.sample_ids[index],
        }


def _collate(items: Sequence[Mapping[str, object]], tokenizer: Any, torch: Any) -> dict[str, Any]:
    width = max(len(item["input_ids"]) for item in items)  # type: ignore[arg-type]
    input_ids = []
    labels = []
    attention = []
    for item in items:
        ids = list(item["input_ids"])  # type: ignore[arg-type]
        target = list(item["labels"])  # type: ignore[arg-type]
        padding = width - len(ids)
        input_ids.append(ids + [tokenizer.pad_token_id] * padding)
        labels.append(target + [-100] * padding)
        attention.append([1] * len(ids) + [0] * padding)
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
        "sidecar_sequence": torch.tensor(
            np.stack([item["sidecar_sequence"] for item in items]),
            dtype=torch.float32,
        ),
        "sidecar_valid_mask": torch.tensor(
            np.stack([item["sidecar_valid_mask"] for item in items]),
            dtype=torch.bool,
        ),
        "sidecar_gate": torch.tensor(
            [item["sidecar_gate"] for item in items],
            dtype=torch.float32,
        ),
        "sample_ids": [str(item["sample_id"]) for item in items],
    }


def _set_seed(torch: Any, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def _build_model(config: ProbeConfig, sidecar_dimension: int) -> tuple[Any, Any, Any]:
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    tokenizer = AutoTokenizer.from_pretrained(config.model.source, use_fast=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    backbone = AutoModelForCausalLM.from_pretrained(
        config.model.source,
        quantization_config=quantization,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation=config.model.attention_backend,
    )
    backbone = prepare_model_for_kbit_training(
        backbone,
        use_gradient_checkpointing=True,
    )
    backbone = get_peft_model(
        backbone,
        LoraConfig(
            r=config.model.lora_rank,
            lora_alpha=config.model.lora_alpha,
            lora_dropout=config.model.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules="all-linear",
        ),
    )
    backbone.config.use_cache = False
    hidden_size = int(backbone.config.hidden_size)

    class QwenSidecarModel(torch.nn.Module):
        def __init__(self, base: Any) -> None:
            super().__init__()
            self.backbone = base
            self.sidecar_encoder = torch.nn.GRU(
                input_size=sidecar_dimension,
                hidden_size=128,
                batch_first=True,
            )
            self.sidecar_projection = torch.nn.Linear(128, hidden_size, bias=False)
            self.fusion_logit = torch.nn.Parameter(torch.tensor(0.0))

        def forward(
            self,
            *,
            input_ids: Any,
            attention_mask: Any,
            sidecar_sequence: Any,
            sidecar_valid_mask: Any,
            sidecar_gate: Any,
            labels: Any | None = None,
        ) -> Any:
            lengths = sidecar_valid_mask.to(torch.int64).sum(dim=1)
            encoded, _ = self.sidecar_encoder(sidecar_sequence.float())
            indices = torch.arange(encoded.shape[0], device=encoded.device)
            state = encoded[indices, torch.clamp(lengths - 1, min=0)]
            state = state * (lengths > 0).unsqueeze(1).to(state.dtype)
            projected = self.sidecar_projection(state)
            embeddings = self.backbone.get_input_embeddings()(input_ids)
            strength = FUSION_LIMIT * torch.tanh(self.fusion_logit)
            gate = sidecar_gate.detach().to(projected.dtype)
            residual = strength * gate[:, None] * projected
            fused = embeddings + residual[:, None, :].to(embeddings.dtype)
            return self.backbone(
                inputs_embeds=fused,
                attention_mask=attention_mask,
                labels=labels,
                use_cache=False,
                return_dict=True,
            )

    model = QwenSidecarModel(backbone)
    device = next(backbone.parameters()).device
    model.sidecar_encoder.to(device)
    model.sidecar_projection.to(device)
    model.fusion_logit.data = model.fusion_logit.data.to(device)
    return tokenizer, model, device


def _loader(
    split: VariantSplit,
    config: ProbeConfig,
    tokenizer: Any,
    torch: Any,
    *,
    shuffle: bool,
) -> Any:
    generator = torch.Generator()
    generator.manual_seed(config.seed)
    return torch.utils.data.DataLoader(
        _Dataset(split, tokenizer, config.model.max_length),
        batch_size=(
            config.training.per_device_train_batch_size
            if shuffle
            else config.training.per_device_eval_batch_size
        ),
        shuffle=shuffle,
        generator=generator,
        num_workers=0,
        collate_fn=lambda values: _collate(values, tokenizer, torch),
    )


def _move_batch(batch: Mapping[str, Any], device: Any) -> dict[str, Any]:
    return {
        key: value.to(device) if hasattr(value, "to") else value
        for key, value in batch.items()
        if key != "sample_ids"
    }


def _trainable_state(model: Any) -> dict[str, Any]:
    return {
        name: parameter.detach().cpu()
        for name, parameter in model.named_parameters()
        if parameter.requires_grad
    }


def _load_trainable_state(model: Any, state: Mapping[str, Any]) -> None:
    parameters = {
        name: parameter for name, parameter in model.named_parameters() if parameter.requires_grad
    }
    if set(parameters) != set(state):
        raise QwenR2ProbeError("恢复检查点的可训练参数集合不一致")
    for name, parameter in parameters.items():
        parameter.data.copy_(state[name].to(parameter.device, dtype=parameter.dtype))


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as target:
        for row in rows:
            target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


class _Logger:
    def __init__(self, config: ProbeConfig, output: Path) -> None:
        import swanlab

        self.output = output
        self.client = swanlab
        run = swanlab.init(
            project=config.tracking.project,
            workspace=config.tracking.workspace,
            experiment_name=f"{config.tracking.run_name}-{config.variant.lower()}",
            mode=config.tracking.mode,
            config={
                "model": config.model.identifier,
                "variant": config.variant,
                "seed": config.seed,
                "steps": config.training.max_steps,
                "candidate_rows": CANDIDATE_TOTAL_ROWS,
                "final_test_visible": False,
            },
            tags=[*config.tracking.tags, config.variant.lower()],
        )
        run_id = str(getattr(run, "id", getattr(run, "run_id", "")))
        _atomic_json(output / "swanlab-run.json", {"run_id": run_id, "mode": "online"})

    def log(self, values: Mapping[str, float], step: int, event: str) -> None:
        row = {"step": step, "event": event, "time": time.time(), **values}
        with (self.output / "metrics.jsonl").open("a", encoding="utf-8") as target:
            target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self.client.log(dict(values), step=step)

    def finish(self) -> None:
        self.client.finish()


def _score_completion_batch(
    model: Any,
    tokenizer: Any,
    texts: Sequence[str],
    completion: str,
    sequences: np.ndarray,
    valid_masks: np.ndarray,
    gates: np.ndarray,
    max_length: int,
    torch: Any,
    device: Any,
) -> Any:
    items = []
    for index, text in enumerate(texts):
        prompt_ids = tokenizer(_prompt(tokenizer, text), add_special_tokens=False)["input_ids"]
        completion_ids = tokenizer(
            completion + tokenizer.eos_token,
            add_special_tokens=False,
        )["input_ids"]
        available = max_length - len(completion_ids)
        prompt_ids = prompt_ids[-available:]
        items.append(
            {
                "input_ids": [*prompt_ids, *completion_ids],
                "labels": [-100] * len(prompt_ids) + list(completion_ids),
                "sidecar_sequence": sequences[index],
                "sidecar_valid_mask": valid_masks[index],
                "sidecar_gate": float(gates[index]),
                "sample_id": str(index),
            }
        )
    batch = _move_batch(_collate(items, tokenizer, torch), device)
    labels = batch["labels"]
    output = model(**batch)
    logits = output.logits[:, :-1].float()
    targets = labels[:, 1:]
    mask = targets.ne(-100)
    safe_targets = targets.masked_fill(~mask, 0)
    token_log_probability = torch.nn.functional.log_softmax(logits, dim=-1).gather(
        -1,
        safe_targets.unsqueeze(-1),
    ).squeeze(-1)
    return (token_log_probability * mask).sum(dim=-1) / mask.sum(dim=-1).clamp_min(1)


def _evaluate(
    model: Any,
    tokenizer: Any,
    split: VariantSplit,
    config: ProbeConfig,
    torch: Any,
    device: Any,
    logger: _Logger,
    step: int,
    prefix: str,
) -> tuple[dict[str, int | float], tuple[Mapping[str, object], ...]]:
    probabilities: list[float] = []
    model.eval()
    started = time.perf_counter()
    size = config.training.per_device_eval_batch_size
    with torch.inference_mode():
        for start in range(0, len(split), size):
            stop = min(start + size, len(split))
            texts = split.texts[start:stop]
            sequences = split.sidecar_sequence[start:stop]
            valid = split.sidecar_valid_mask[start:stop]
            gates = split.sidecar_gate[start:stop]
            benign = _score_completion_batch(
                model,
                tokenizer,
                texts,
                LABEL_TEXT[0],
                sequences,
                valid,
                gates,
                config.model.max_length,
                torch,
                device,
            )
            malicious = _score_completion_batch(
                model,
                tokenizer,
                texts,
                LABEL_TEXT[1],
                sequences,
                valid,
                gates,
                config.model.max_length,
                torch,
                device,
            )
            values = torch.softmax(torch.stack((benign, malicious), dim=-1), dim=-1)[:, 1]
            probabilities.extend(float(value) for value in values.cpu().tolist())
            batch_index = start // size + 1
            if batch_index == 1 or batch_index % 25 == 0 or stop == len(split):
                elapsed = time.perf_counter() - started
                logger.log(
                    {
                        f"{prefix}/completed_samples": float(stop),
                        f"{prefix}/samples_per_second": stop / max(elapsed, 1e-12),
                    },
                    step,
                    f"{prefix}_progress",
                )
    result = metrics.compute_binary_metrics(
        split.labels,
        probabilities,
        threshold=config.evaluation.threshold,
        calibration_bins=config.evaluation.calibration_bins,
    )
    result["inference_seconds"] = time.perf_counter() - started
    result["samples_per_second"] = len(split) / max(float(result["inference_seconds"]), 1e-12)
    rows = tuple(
        {
            "sample_id": sample_id,
            "stable_order": int(stable_order),
            "label": int(label),
            "probability_malicious": probability,
            "prediction": int(probability >= config.evaluation.threshold),
            "generated_text": LABEL_TEXT[int(probability >= config.evaluation.threshold)],
            "generation_protocol": config.evaluation.protocol,
        }
        for sample_id, stable_order, label, probability in zip(
            split.sample_ids,
            split.stable_orders,
            split.labels,
            probabilities,
            strict=True,
        )
    )
    return result, rows


def _binding(
    config: ProbeConfig,
    views: PreparedVariantViews,
    checkpoint_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "development_candidate",
        "variant": config.variant,
        "seed": config.seed,
        "model_identifier": config.model.identifier,
        "model_source": str(config.model.source),
        "model_config_sha256": _sha256(config.model.source / "config.json"),
        "model_weights_sha256": _sha256(config.model.source / "model.safetensors"),
        "config_sha256": config.file_sha256,
        "r2_contract_sha256": config.r2_contract_sha256,
        "physics_checkpoint_sha256": checkpoint_sha256,
        "views": dict(views.binding),
        "candidate_roles": validate_candidate_role_counts(
            detection_rows=CANDIDATE_DETECTION_ROWS,
            physics_rows=CANDIDATE_PHYSICS_ROWS,
            total_rows=CANDIDATE_TOTAL_ROWS,
        ),
        "effective_batch_size": (
            config.training.per_device_train_batch_size
            * config.training.gradient_accumulation_steps
        ),
        "max_steps": config.training.max_steps,
        "quic_expert_ready": False,
        "quic_training_weight": 0.0,
        "final_test_visible": False,
    }


def _save_checkpoint(
    path: Path,
    *,
    model: Any,
    optimizer: Any,
    scheduler: Any,
    binding: Mapping[str, object],
    step: int,
    micro_step: int,
    torch: Any,
) -> None:
    temporary = path.with_suffix(".pt.tmp")
    torch.save(
        {
            "binding": dict(binding),
            "trainable_state": _trainable_state(model),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "step": step,
            "micro_step": micro_step,
            "python_random_state": random.getstate(),
            "numpy_random_state": np.random.get_state(),
            "torch_random_state": torch.get_rng_state(),
            "cuda_random_state": torch.cuda.get_rng_state_all(),
        },
        temporary,
    )
    os.replace(temporary, path)


def _train(
    config: ProbeConfig,
    views: PreparedVariantViews,
    checkpoint_sha256: str,
    physical_rows: Sequence[Mapping[str, object]],
    physical_metrics: Mapping[str, object],
) -> Mapping[str, object]:
    import torch
    from transformers import get_linear_schedule_with_warmup

    output = config.output_root / f"seed-{config.seed}" / config.variant.lower()
    output.mkdir(parents=True, exist_ok=True)
    binding = _binding(config, views, checkpoint_sha256)
    binding_path = output / "run-binding.json"
    if binding_path.exists() and json.loads(binding_path.read_text(encoding="utf-8")) != binding:
        raise QwenR2ProbeError("已有 Qwen 输出绑定与当前运行不一致")
    if not binding_path.exists():
        _atomic_json(binding_path, binding)
    _atomic_jsonl(output / "physical-validation-clusters.jsonl", physical_rows)
    _atomic_json(output / "physical-validation-metrics.json", physical_metrics)

    _set_seed(torch, config.seed)
    tokenizer, model, device = _build_model(
        config,
        int(views.train.sidecar_sequence.shape[-1]),
    )
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable,
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )
    warmup_steps = int(config.training.max_steps * config.training.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=config.training.max_steps,
    )
    checkpoint = output / "checkpoint-latest.pt"
    step = 0
    micro_step = 0
    if checkpoint.is_file() and config.training.resume_from_checkpoint == "auto":
        saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if saved.get("binding") != binding:
            raise QwenR2ProbeError("恢复检查点绑定不一致")
        _load_trainable_state(model, saved["trainable_state"])
        optimizer.load_state_dict(saved["optimizer"])
        scheduler.load_state_dict(saved["scheduler"])
        step = int(saved["step"])
        micro_step = int(saved["micro_step"])
        random.setstate(saved["python_random_state"])
        np.random.set_state(saved["numpy_random_state"])
        torch.set_rng_state(saved["torch_random_state"])
        torch.cuda.set_rng_state_all(saved["cuda_random_state"])

    logger = _Logger(config, output)
    protocol_metrics = physical_metrics["by_protocol"]
    logger.log(
        {
            "physical/equal_protocol_state_mse": float(
                physical_metrics["equal_protocol_state_mse"]
            ),
            "physical/equal_protocol_residual_mse": float(
                physical_metrics["equal_protocol_physics_residual_mse"]
            ),
            "physical/tcp_state_mse": float(protocol_metrics["TCP"]["state_mse"]),
            "physical/udp_state_mse": float(protocol_metrics["UDP"]["state_mse"]),
        },
        step,
        "physical_validation",
    )
    started = time.perf_counter()
    try:
        loader = _loader(views.train, config, tokenizer, torch, shuffle=True)
        iterator = iter(loader)
        optimizer.zero_grad(set_to_none=True)
        while step < config.training.max_steps:
            try:
                batch = next(iterator)
            except StopIteration:
                iterator = iter(loader)
                batch = next(iterator)
            micro_step += 1
            model.train()
            values = _move_batch(batch, device)
            output_value = model(**values)
            loss = output_value.loss
            if loss is None or not bool(torch.isfinite(loss).item()):
                raise QwenR2ProbeError("Qwen 生成训练损失不是有限数")
            (loss / config.training.gradient_accumulation_steps).backward()
            if micro_step % config.training.gradient_accumulation_steps != 0:
                continue
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                trainable,
                config.training.max_grad_norm,
            )
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            step += 1
            logger.log(
                {
                    "train/loss": float(loss.detach().float().item()),
                    "train/learning_rate": float(optimizer.param_groups[0]["lr"]),
                    "train/gradient_norm": float(gradient_norm.detach().float().item()),
                    "train/fusion_strength": float(
                        FUSION_LIMIT * torch.tanh(model.fusion_logit).detach().float().item()
                    ),
                    "resource/gpu_memory_allocated_mib": float(
                        torch.cuda.memory_allocated() / (1024**2)
                    ),
                    "resource/gpu_memory_reserved_mib": float(
                        torch.cuda.memory_reserved() / (1024**2)
                    ),
                },
                step,
                "optimizer_step",
            )
            _atomic_json(
                output / "run_state.json",
                {
                    "status": "running",
                    "step": step,
                    "micro_step": micro_step,
                    "updated_at": time.time(),
                },
            )
            if step % config.training.save_steps == 0:
                _save_checkpoint(
                    checkpoint,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    binding=binding,
                    step=step,
                    micro_step=micro_step,
                    torch=torch,
                )

        calibration_metrics, _ = _evaluate(
            model,
            tokenizer,
            views.calibration,
            config,
            torch,
            device,
            logger,
            step,
            "calibration",
        )
        logger.log(
            {
                f"calibration/{name}": float(value)
                for name, value in calibration_metrics.items()
                if isinstance(value, (int, float))
            },
            step,
            "calibration",
        )
        validation_metrics, predictions = _evaluate(
            model,
            tokenizer,
            views.validation,
            config,
            torch,
            device,
            logger,
            step,
            "validation",
        )
        adapter = output / "adapter"
        model.backbone.save_pretrained(adapter)
        tokenizer.save_pretrained(adapter)
        torch.save(
            {
                "sidecar_encoder": model.sidecar_encoder.state_dict(),
                "sidecar_projection": model.sidecar_projection.state_dict(),
                "fusion_logit": model.fusion_logit.detach().cpu(),
            },
            output / "sidecar-adapter.pt",
        )
        _atomic_jsonl(output / "validation-predictions.jsonl", predictions)
        result = {
            "status": "finished",
            "stage": "development_candidate",
            "variant": config.variant,
            "seed": config.seed,
            "steps": step,
            "calibration_metrics": calibration_metrics,
            "validation_metrics": validation_metrics,
            "physical_validation_metrics": physical_metrics,
            "elapsed_seconds": time.perf_counter() - started,
            "peak_gpu_memory_mib": torch.cuda.max_memory_allocated() / (1024**2),
            "quic_expert_ready": False,
            "final_test_visible": False,
        }
        _atomic_json(output / "result.json", result)
        _atomic_json(
            output / "run_state.json",
            {"status": "finished", "step": step, "updated_at": time.time()},
        )
        return result
    except BaseException as error:
        _atomic_json(
            output / "run_state.json",
            {
                "status": "interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                "step": step,
                "micro_step": micro_step,
                "error_type": type(error).__name__,
                "error": str(error),
                "updated_at": time.time(),
            },
        )
        raise
    finally:
        logger.finish()


def execute(config: ProbeConfig, variant: str) -> Mapping[str, object]:
    if os.environ.get("R2_QWEN_CANDIDATE_REQUIRED") != "1":
        raise QwenR2ProbeError("Qwen 开发候选必须经正式包装器启动")
    if variant != config.variant:
        raise QwenR2ProbeError("命令组别与配置冻结组别不一致")
    if not config.model.source.is_dir():
        raise QwenR2ProbeError("Qwen3-0.6B 本地模型目录不存在")
    for name in ("config.json", "model.safetensors", "tokenizer.json"):
        if not (config.model.source / name).is_file():
            raise QwenR2ProbeError(f"Qwen3-0.6B 模型快照缺少 {name}")
    if not config.r2_contract.data.ready:
        raise QwenR2ProbeError(config.r2_contract.data.not_ready_reason)

    import torch

    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise QwenR2ProbeError("Qwen 正式开发候选要求 CUDA 与 BF16")
    (
        fit_config,
        system,
        unified_control,
        history_control,
        checkpoint_sha256,
        capacity_receipt,
        checkpoint_binding_sha256,
    ) = r2._physics_system(config.r2_contract, torch)
    mapped_history = tuple(
        r2.HISTORY_TO_PHYSICS.get(field, "")
        for field in config.r2_contract.data.contract.columns.history_fields
    )
    if mapped_history != fit_config.data.observation_fields:
        raise QwenR2ProbeError("检测公共历史与物理专家输入语义或顺序不一致")
    base = r2.load_base_views(config.r2_contract.data.contract)
    device = torch.device("cuda:0")
    unified, physics = r2._produce_bound_sequences(
        system=system,
        unified_control=unified_control,
        base=base,
        checkpoint_sha256=checkpoint_sha256,
        capacity_receipt=capacity_receipt,
        checkpoint_binding_sha256=checkpoint_binding_sha256,
        quic_expert_ready=False,
        batch_size=config.r2_contract.physics.production_batch_size,
        torch=torch,
        device=device,
    )
    views = build_variant_views(
        base,
        variant=variant,
        seed=config.seed,
        unified_sequences=unified,
        physics_sequences=physics,
        representation_dimension=fit_config.model.representation_dimension,
        quic_expert_ready=False,
    )
    physical_rows, physical_metrics = r2._physical_validation_artifacts(
        variant=variant,
        fit_config=fit_config,
        system=system,
        unified_control=unified_control,
        history_control=history_control,
        checkpoint_sha256=checkpoint_sha256,
        checkpoint_binding_sha256=checkpoint_binding_sha256,
        seed=config.seed,
        batch_size=config.r2_contract.physics.production_batch_size,
        torch=torch,
        device=device,
    )
    return _train(
        config,
        views,
        checkpoint_sha256,
        physical_rows,
        physical_metrics,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 Qwen3-0.6B R2 单组开发候选")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--trusted-root", type=Path, required=True)
    parser.add_argument("--variant", choices=ALLOWED_VARIANTS, required=True)
    parser.add_argument("--validate-config-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config, trusted_root=args.trusted_root)
    if args.validate_config_only:
        print(
            json.dumps(
                {
                    "status": "config-valid",
                    "model": config.model.identifier,
                    "variant": config.variant,
                    "seed": config.seed,
                    "candidate_rows": CANDIDATE_TOTAL_ROWS,
                    "quic_expert_ready": False,
                    "final_test_visible": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    result = execute(config, args.variant)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
