"""E2 共同七字段下的普通 DistilBERT 源域训练适配器。"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from flow_probe.e2_hard_domain_baselines import (
    E2BaselineBudget,
    E2HardDomainBaselineError,
    E2TextSample,
    SharedB0DistilBertPredictor,
)
from flow_probe.e2_hard_domain_data import E2_FEATURE_FIELDS
from flow_probe.shared_b0_distilbert_baseline import (
    FIXED_MODEL_ID,
    ModelSettings,
    RuntimeModules,
    RuntimeSelection,
    SharedB0DistilBertError,
    _autocast,
    _linear_schedule_lambda,
    _new_grad_scaler,
    _set_reproducible_seed,
    compute_binary_metrics,
    load_runtime_modules,
    resolve_runtime,
    validate_model_source,
)


class E2DistilBertTrainingError(E2HardDomainBaselineError):
    """普通 DistilBERT 训练输入或运行状态违反 E2 合同。"""


@dataclass(frozen=True)
class E2DistilBertTrainingSettings:
    """复用共享 B0 默认值的 E2 普通 DistilBERT 训练参数。"""

    model_identifier: str = FIXED_MODEL_ID
    model_source: str = "/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased"
    expected_model_binding_sha256: str = ""
    max_length: int = 128
    device: str = "auto"
    precision: str = "auto"
    per_device_train_batch_size: int = 16
    per_device_eval_batch_size: int = 64
    gradient_accumulation_steps: int = 2
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    num_train_epochs: int = 3
    warmup_ratio: float = 0.1
    max_grad_norm: float = 1.0
    num_workers: int = 0
    early_stopping_patience: int = 2
    early_stopping_min_delta: float = 0.0

    def validate(self) -> None:
        if self.model_identifier != FIXED_MODEL_ID:
            raise E2DistilBertTrainingError(f"普通编码器必须固定为 {FIXED_MODEL_ID}")
        if not self.model_source.strip():
            raise E2DistilBertTrainingError("DistilBERT 模型来源不能为空")
        expected_binding = self.expected_model_binding_sha256
        if len(expected_binding) != 64 or any(
            character not in "0123456789abcdef" for character in expected_binding
        ):
            raise E2DistilBertTrainingError("基础模型绑定摘要必须是预注册的 64 位 SHA-256")
        if self.max_length < 1:
            raise E2DistilBertTrainingError("最大文本长度必须为正整数")
        if self.device not in {"auto", "cuda", "cpu"}:
            raise E2DistilBertTrainingError("设备只允许 auto、cuda 或 cpu")
        if self.precision not in {"auto", "float32", "float16", "bfloat16"}:
            raise E2DistilBertTrainingError(
                "精度只允许 auto、float32、float16 或 bfloat16"
            )
        positive_integers = {
            "训练批大小": self.per_device_train_batch_size,
            "评价批大小": self.per_device_eval_batch_size,
            "梯度累积步数": self.gradient_accumulation_steps,
            "训练轮数": self.num_train_epochs,
            "早停耐心值": self.early_stopping_patience,
        }
        if any(value < 1 for value in positive_integers.values()):
            name = next(name for name, value in positive_integers.items() if value < 1)
            raise E2DistilBertTrainingError(f"{name}必须为正整数")
        if self.learning_rate <= 0.0 or self.max_grad_norm <= 0.0:
            raise E2DistilBertTrainingError("学习率和最大梯度范数必须为正数")
        if self.weight_decay < 0.0 or self.early_stopping_min_delta < 0.0:
            raise E2DistilBertTrainingError("权重衰减和早停最小增量不得为负数")
        if not 0.0 <= self.warmup_ratio < 1.0:
            raise E2DistilBertTrainingError("预热比例必须位于 [0, 1)")
        if self.num_workers < 0:
            raise E2DistilBertTrainingError("数据加载进程数不得为负数")


class _E2TextDataset:
    def __init__(self, samples: Sequence[E2TextSample]) -> None:
        self.samples = tuple(samples)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[str, int]:
        sample = self.samples[index]
        return sample.text, sample.label


def _validate_text_sample(sample: E2TextSample, description: str) -> None:
    if not sample.sample_id or not sample.capture_id:
        raise E2DistilBertTrainingError(f"{description}样本标识与捕获组不得为空")
    if sample.label not in {0, 1}:
        raise E2DistilBertTrainingError(f"{description}标签只允许 0 或 1")
    fields = sample.text.split()
    expected = tuple(f"{name}=" for name in E2_FEATURE_FIELDS)
    if len(fields) != len(expected) or any(
        not token.startswith(prefix) for token, prefix in zip(fields, expected, strict=True)
    ):
        raise E2DistilBertTrainingError(f"{description}文本必须严格由冻结七字段构造")


def _validate_source_inputs(
    train: Sequence[E2TextSample], calibration: Sequence[E2TextSample]
) -> None:
    if not train:
        raise E2DistilBertTrainingError("DistilBERT 源域训练集不得为空")
    for name, samples in (("训练", train), ("校准", calibration)):
        for sample in samples:
            _validate_text_sample(sample, name)
    sample_ids = [sample.sample_id for sample in (*train, *calibration)]
    if len(sample_ids) != len(set(sample_ids)):
        raise E2DistilBertTrainingError("源域训练集与校准集样本必须互斥且唯一")
    if {sample.label for sample in train} != {0, 1}:
        raise E2DistilBertTrainingError("源域训练必须同时包含良性与恶意样本")


def _collate(tokenizer: Any, max_length: int, torch_module: Any):
    def collate(items: Sequence[tuple[str, int]]) -> dict[str, Any]:
        texts, labels = zip(*items, strict=True)
        encoded = tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch_module.tensor(labels, dtype=torch_module.long)
        return encoded

    return collate


def _loader(
    samples: Sequence[E2TextSample],
    *,
    tokenizer: Any,
    batch_size: int,
    max_length: int,
    torch_module: Any,
    runtime: RuntimeSelection,
    shuffle: bool,
    seed: int,
    num_workers: int,
) -> Any:
    generator = torch_module.Generator()
    generator.manual_seed(seed)
    return torch_module.utils.data.DataLoader(
        _E2TextDataset(samples),
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=num_workers,
        collate_fn=_collate(tokenizer, max_length, torch_module),
        pin_memory=runtime.device == "cuda",
        persistent_workers=bool(num_workers),
    )


def _model_settings(settings: E2DistilBertTrainingSettings) -> ModelSettings:
    return ModelSettings(
        identifier=settings.model_identifier,
        source=settings.model_source,
        max_length=settings.max_length,
        device=settings.device,
        precision=settings.precision,
    )


def _resolve_training_runtime(
    modules: RuntimeModules, settings: E2DistilBertTrainingSettings
) -> RuntimeSelection:
    model = _model_settings(settings)
    runtime = resolve_runtime(modules.torch, model, formal_training=False)
    if runtime.device == "cpu" and runtime.precision != "float32":
        runtime = resolve_runtime(
            modules.torch,
            replace(model, precision="float32"),
            formal_training=False,
        )
    return runtime


def _validate_base_model_binding(
    settings: E2DistilBertTrainingSettings,
) -> Mapping[str, object]:
    source = Path(settings.model_source).expanduser().resolve()
    if not source.is_dir():
        raise E2DistilBertTrainingError(f"本地 DistilBERT 基础模型目录不存在：{source}")
    try:
        binding = validate_model_source(_model_settings(settings))
    except SharedB0DistilBertError as error:
        raise E2DistilBertTrainingError(f"DistilBERT 基础模型来源核验失败：{error}") from error
    if binding.get("source_kind") != "local_mirror" or not binding.get(
        "local_files_verified"
    ):
        raise E2DistilBertTrainingError("E2 正式训练只接受已核验并绑定权重哈希的本地基础模型")
    actual_binding = str(binding.get("binding_sha256", ""))
    if actual_binding != settings.expected_model_binding_sha256:
        raise E2DistilBertTrainingError(
            "DistilBERT 基础模型绑定摘要与预注册值不一致"
        )

    config_path = source / "config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise E2DistilBertTrainingError(f"无法读取基础模型配置：{error}") from error
    architectures = config.get("architectures")
    if not isinstance(architectures, list) or not architectures:
        raise E2DistilBertTrainingError("基础模型配置缺少可核验的 architectures")
    allowed_architectures = {"DistilBertForMaskedLM", "DistilBertModel"}
    if any(str(name) not in allowed_architectures for name in architectures):
        raise E2DistilBertTrainingError(
            "模型来源不是允许的基础预训练 DistilBERT，拒绝旧分类检查点"
        )

    artifacts = binding.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise E2DistilBertTrainingError("基础模型绑定缺少制品清单")
    weight_artifacts = {
        str(name): dict(record)
        for name, record in artifacts.items()
        if str(name).endswith(".safetensors")
        or str(name).startswith("pytorch_model")
    }
    if not weight_artifacts or any(
        len(str(record.get("sha256", ""))) != 64 for record in weight_artifacts.values()
    ):
        raise E2DistilBertTrainingError("基础模型绑定缺少完整的权重 SHA-256 清单")
    return MappingProxyType(
        {
            "schema_version": "flow_probe_e2_distilbert_base_binding_v1",
            "identifier": settings.model_identifier,
            "source": str(source),
            "binding_sha256": actual_binding,
            "artifact_count": int(binding.get("artifact_count", 0)),
            "total_size_bytes": int(binding.get("total_size_bytes", 0)),
            "weight_artifacts": weight_artifacts,
        }
    )


def _module_parameters_sha256(modules: Mapping[str, Any]) -> str:
    digest = hashlib.sha256()
    for module_name, module in sorted(modules.items()):
        for parameter_name, parameter in sorted(module.state_dict().items()):
            value = parameter.detach().cpu().contiguous().numpy()
            digest.update(f"{module_name}.{parameter_name}\0".encode("utf-8"))
            digest.update(str(value.dtype).encode("ascii"))
            digest.update(str(tuple(value.shape)).encode("ascii"))
            digest.update(value.tobytes())
    return digest.hexdigest()


def _reset_classification_head(model: Any, torch_module: Any, seed: int) -> Mapping[str, object]:
    head_modules: dict[str, Any] = {}
    for name in ("pre_classifier", "classifier"):
        module = getattr(model, name, None)
        if module is None or not callable(getattr(module, "reset_parameters", None)):
            raise E2DistilBertTrainingError(
                f"DistilBERT 缺少可显式重置的分类头组件：{name}"
            )
        head_modules[name] = module
    loaded_sha256 = _module_parameters_sha256(head_modules)
    torch_module.manual_seed(seed)
    pretrained_initializer = getattr(model, "_init_weights", None)
    for module in head_modules.values():
        if callable(pretrained_initializer):
            pretrained_initializer(module)
        else:
            module.reset_parameters()
    initialized_sha256 = _module_parameters_sha256(head_modules)
    return MappingProxyType(
        {
            "mode": (
                "explicit_seeded_pretrained_initialization"
                if callable(pretrained_initializer)
                else "explicit_seeded_reset"
            ),
            "seed": seed,
            "components": tuple(head_modules),
            "reset_performed": True,
            "parameter_digest_changed": loaded_sha256 != initialized_sha256,
            "loaded_head_sha256": loaded_sha256,
            "initialized_head_sha256": initialized_sha256,
        }
    )


def _load_model(
    modules: RuntimeModules,
    settings: E2DistilBertTrainingSettings,
    runtime: RuntimeSelection,
    *,
    seed: int,
) -> tuple[Any, Any, Mapping[str, object], Mapping[str, object]]:
    model_binding = _validate_base_model_binding(settings)
    source = settings.model_source
    tokenizer = modules.auto_tokenizer.from_pretrained(
        source,
        use_fast=True,
        local_files_only=True,
    )
    model = modules.auto_model.from_pretrained(
        source,
        num_labels=2,
        id2label={0: "benign", 1: "malicious"},
        label2id={"benign": 0, "malicious": 1},
        ignore_mismatched_sizes=True,
        local_files_only=True,
    )
    head_binding = _reset_classification_head(model, modules.torch, seed=seed)
    model.to(runtime.device)
    return tokenizer, model, model_binding, head_binding


def _class_weights(samples: Sequence[E2TextSample], torch_module: Any, device: str) -> Any:
    counts = np.bincount([sample.label for sample in samples], minlength=2).astype(np.float64)
    values = len(samples) / (2.0 * counts)
    return torch_module.tensor(values, dtype=torch_module.float32, device=device)


def _clone_state_to_cpu(model: Any) -> dict[str, Any]:
    return {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}


class E2DistilBertTrainingAdapter:
    """仅接收源域训练与校准样本的普通 DistilBERT 训练实现。"""

    def __init__(self, settings: E2DistilBertTrainingSettings) -> None:
        self.settings = settings
        self.last_training_summary: Mapping[str, object] | None = None

    def fit_source_only(
        self,
        *,
        train: Sequence[E2TextSample],
        calibration: Sequence[E2TextSample],
        budget: E2BaselineBudget,
    ) -> SharedB0DistilBertPredictor:
        self.settings.validate()
        budget.validate()
        _validate_source_inputs(train, calibration)
        try:
            return self._fit(train=train, calibration=calibration, budget=budget)
        except E2DistilBertTrainingError:
            raise
        except Exception as error:
            raise E2DistilBertTrainingError(f"DistilBERT 源域训练失败：{error}") from error

    def _fit(
        self,
        *,
        train: Sequence[E2TextSample],
        calibration: Sequence[E2TextSample],
        budget: E2BaselineBudget,
    ) -> SharedB0DistilBertPredictor:
        modules = load_runtime_modules()
        torch_module = modules.torch
        runtime = _resolve_training_runtime(modules, self.settings)
        _set_reproducible_seed(torch_module, budget.seed)
        tokenizer, model, model_binding, head_binding = _load_model(
            modules, self.settings, runtime, seed=budget.seed
        )
        batches_per_epoch = math.ceil(len(train) / self.settings.per_device_train_batch_size)
        steps_per_epoch = math.ceil(
            batches_per_epoch / self.settings.gradient_accumulation_steps
        )
        total_steps = steps_per_epoch * self.settings.num_train_epochs
        warmup_steps = int(total_steps * self.settings.warmup_ratio)
        optimizer = torch_module.optim.AdamW(
            model.parameters(),
            lr=self.settings.learning_rate,
            weight_decay=self.settings.weight_decay,
        )
        scheduler = torch_module.optim.lr_scheduler.LambdaLR(
            optimizer,
            lr_lambda=_linear_schedule_lambda(total_steps, warmup_steps),
        )
        scaler = _new_grad_scaler(torch_module, runtime.use_grad_scaler)
        class_weights = _class_weights(train, torch_module, runtime.device)
        best_state: dict[str, Any] | None = None
        best_macro_f1 = -1.0
        best_epoch = 0
        stale_epochs = 0
        optimizer_steps = 0
        optimizer.zero_grad(set_to_none=True)
        for epoch in range(self.settings.num_train_epochs):
            loader = _loader(
                train,
                tokenizer=tokenizer,
                batch_size=self.settings.per_device_train_batch_size,
                max_length=self.settings.max_length,
                torch_module=torch_module,
                runtime=runtime,
                shuffle=True,
                seed=budget.seed + epoch,
                num_workers=self.settings.num_workers,
            )
            model.train()
            for batch_index, batch in enumerate(loader):
                batch = {name: value.to(runtime.device) for name, value in batch.items()}
                labels = batch.pop("labels")
                group_start = (
                    batch_index // self.settings.gradient_accumulation_steps
                ) * self.settings.gradient_accumulation_steps
                group_size = min(
                    self.settings.gradient_accumulation_steps,
                    batches_per_epoch - group_start,
                )
                with _autocast(torch_module, runtime):
                    output = model(**batch)
                    loss = torch_module.nn.functional.cross_entropy(
                        output.logits,
                        labels,
                        weight=class_weights.to(dtype=output.logits.dtype),
                    )
                if not bool(torch_module.isfinite(loss).item()):
                    raise E2DistilBertTrainingError("DistilBERT 训练损失不是有限数")
                scaled_loss = loss / group_size
                if runtime.use_grad_scaler:
                    scaler.scale(scaled_loss).backward()
                else:
                    scaled_loss.backward()
                group_end = (
                    (batch_index + 1) % self.settings.gradient_accumulation_steps == 0
                    or batch_index + 1 == batches_per_epoch
                )
                if not group_end:
                    continue
                if runtime.use_grad_scaler:
                    scaler.unscale_(optimizer)
                torch_module.nn.utils.clip_grad_norm_(
                    model.parameters(), self.settings.max_grad_norm
                )
                if runtime.use_grad_scaler:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                optimizer_steps += 1

            predictor = SharedB0DistilBertPredictor(
                model=model,
                tokenizer=tokenizer,
                torch_module=torch_module,
                device=runtime.device,
                max_length=self.settings.max_length,
                batch_size=self.settings.per_device_eval_batch_size,
            )
            if calibration:
                probabilities = predictor.predict_malicious_probabilities(
                    [sample.text for sample in calibration]
                )
                metrics = compute_binary_metrics(
                    [sample.label for sample in calibration], probabilities
                )
                selection_score = float(metrics["macro_f1"])
            else:
                selection_score = float(epoch + 1)
            if selection_score > best_macro_f1 + self.settings.early_stopping_min_delta:
                best_state = _clone_state_to_cpu(model)
                best_macro_f1 = selection_score
                best_epoch = epoch + 1
                stale_epochs = 0
            else:
                stale_epochs += 1
                if calibration and stale_epochs >= self.settings.early_stopping_patience:
                    break

        if best_state is None:
            raise E2DistilBertTrainingError("训练结束后未产生合法的源域选模状态")
        model.load_state_dict(best_state, strict=True)
        model.eval()
        self.last_training_summary = MappingProxyType(
            {
                "schema_version": "flow_probe_e2_distilbert_training_v2",
                "source_only_fit": True,
                "final_test_visible": False,
                "settings": asdict(self.settings),
                "seed": budget.seed,
                "selected_device": runtime.device,
                "selected_precision": runtime.precision,
                "optimizer_steps": optimizer_steps,
                "best_epoch": best_epoch,
                "best_source_calibration_macro_f1": best_macro_f1,
                "base_model_binding": dict(model_binding),
                "classification_head_initialization": dict(head_binding),
            }
        )
        return SharedB0DistilBertPredictor(
            model=model,
            tokenizer=tokenizer,
            torch_module=torch_module,
            device=runtime.device,
            max_length=self.settings.max_length,
            batch_size=self.settings.per_device_eval_batch_size,
        )
