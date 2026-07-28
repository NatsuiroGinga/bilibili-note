"""运行任务十七固定的常数、单窗口和四窗口可辨识性诊断。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import swanlab
import torch
import yaml
from sklearn.metrics import roc_auc_score
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, TensorDataset

from flow_probe.ns3_observability_sequences import MODEL_INPUT_FIELDS, SPLITS
from flow_probe.tracking import TrackingSettings, capture_console_log, swanlab_run

PHASE = "observability-diagnostic"
VARIANTS = ("single_window", "history_h4")


class ObservabilityDiagnosticError(RuntimeError):
    """可辨识性配置、数据或结果不满足固定协议。"""


@dataclass(frozen=True)
class DiagnosticConfig:
    seed: int
    batch_size: int
    hidden_size: int
    learning_rate: float
    weight_decay: float
    max_epochs: int
    patience: int
    minimum_delta: float
    bootstrap_repetitions: int
    constant_improvement_threshold: float
    history_vs_single_ci_upper_threshold: float
    ood_auc_ci_lower_threshold: float
    device: str
    tracking: TrackingSettings


@dataclass(frozen=True)
class SplitArrays:
    values: np.ndarray
    masks: np.ndarray
    state_targets: np.ndarray
    environment_targets: np.ndarray
    sample_ids: tuple[str, ...]
    group_ids: tuple[str, ...]


class HistoricalEnvironmentStateEstimator(nn.Module):
    """同一容量的循环编码器，同时预测状态、容量和异方差。"""

    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        self.encoder = nn.GRU(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.normalization = nn.LayerNorm(hidden_size)
        self.state_mean = nn.Linear(hidden_size, 5)
        self.state_log_variance = nn.Linear(hidden_size, 5)
        self.environment_mean = nn.Linear(hidden_size, 2)
        self.environment_log_variance = nn.Linear(hidden_size, 2)

    def forward(
        self, inputs: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        encoded, _ = self.encoder(inputs)
        hidden = self.normalization(encoded[:, -1, :])
        state_mean = F.softplus(self.state_mean(hidden))
        state_log_variance = self.state_log_variance(hidden).clamp(-8.0, 4.0)
        environment_mean = self.environment_mean(hidden)
        environment_log_variance = self.environment_log_variance(hidden).clamp(-8.0, 4.0)
        return state_mean, state_log_variance, environment_mean, environment_log_variance


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_config(path: Path) -> tuple[DiagnosticConfig, dict[str, object]]:
    normalized = path.expanduser().resolve()
    if not normalized.is_file():
        raise ObservabilityDiagnosticError(f"诊断配置不存在：{normalized}")
    loaded = yaml.safe_load(normalized.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ObservabilityDiagnosticError("诊断配置必须是映射")
    tracking = loaded.get("tracking")
    if not isinstance(tracking, Mapping):
        raise ObservabilityDiagnosticError("tracking 配置必须是映射")
    config = DiagnosticConfig(
        seed=int(loaded["seed"]),
        batch_size=int(loaded["batch_size"]),
        hidden_size=int(loaded["hidden_size"]),
        learning_rate=float(loaded["learning_rate"]),
        weight_decay=float(loaded["weight_decay"]),
        max_epochs=int(loaded["max_epochs"]),
        patience=int(loaded["patience"]),
        minimum_delta=float(loaded["minimum_delta"]),
        bootstrap_repetitions=int(loaded["bootstrap_repetitions"]),
        constant_improvement_threshold=float(loaded["constant_improvement_threshold"]),
        history_vs_single_ci_upper_threshold=float(loaded["history_vs_single_ci_upper_threshold"]),
        ood_auc_ci_lower_threshold=float(loaded["ood_auc_ci_lower_threshold"]),
        device=str(loaded["device"]),
        tracking=TrackingSettings.from_mapping(tracking),
    )
    if config.seed <= 0 or config.batch_size <= 0 or config.hidden_size <= 0:
        raise ObservabilityDiagnosticError("种子、批量大小和隐藏维度必须为正数")
    if config.max_epochs <= 0 or config.patience <= 0:
        raise ObservabilityDiagnosticError("训练轮数与早停耐心值必须为正数")
    if config.bootstrap_repetitions < 1000:
        raise ObservabilityDiagnosticError("区组自助重复次数不得少于 1000")
    return config, loaded


def _load_split(path: Path) -> SplitArrays:
    values: list[list[list[float]]] = []
    masks: list[list[list[float]]] = []
    states: list[list[float]] = []
    environments: list[list[float]] = []
    sample_ids: list[str] = []
    group_ids: list[str] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            model_inputs = record["model_inputs"]
            observation_mask = record["observation_mask"]
            window_values = [
                [float(model_inputs[field][index]) for field in MODEL_INPUT_FIELDS]
                for index in range(4)
            ]
            window_masks = [
                [float(bool(observation_mask[field][index])) for field in MODEL_INPUT_FIELDS]
                for index in range(4)
            ]
            state_target = [
                float(value)
                for value in record["state_targets"]["normalized_queue_boundary_anchors"]
            ]
            physics = record["physics_supervision"]
            environment_target = [
                math.log1p(float(physics["supervision_capacity_start_bps"][-1])),
                math.log1p(float(physics["supervision_capacity_end_bps"][-1])),
            ]
            if len(state_target) != 5:
                raise ObservabilityDiagnosticError(
                    f"{path.name} 第 {line_number} 行的状态锚点不是 5 个"
                )
            values.append(window_values)
            masks.append(window_masks)
            states.append(state_target)
            environments.append(environment_target)
            sample_ids.append(str(record["sample_id"]))
            group_ids.append(str(record["group_id"]))
    arrays = SplitArrays(
        values=np.asarray(values, dtype=np.float32),
        masks=np.asarray(masks, dtype=np.float32),
        state_targets=np.asarray(states, dtype=np.float32),
        environment_targets=np.asarray(environments, dtype=np.float32),
        sample_ids=tuple(sample_ids),
        group_ids=tuple(group_ids),
    )
    expected_shape = (len(sample_ids), 4, len(MODEL_INPUT_FIELDS))
    if arrays.values.shape != expected_shape or arrays.masks.shape != expected_shape:
        raise ObservabilityDiagnosticError(f"{path.name} 的公共观测形状不正确")
    if not np.isfinite(arrays.values).all() or not np.isfinite(arrays.state_targets).all():
        raise ObservabilityDiagnosticError(f"{path.name} 包含非有限值")
    return arrays


def _fit_transforms(train: SplitArrays) -> dict[str, np.ndarray]:
    logged = np.log1p(train.values)
    feature_mean = logged.reshape(-1, logged.shape[-1]).mean(axis=0)
    feature_std = logged.reshape(-1, logged.shape[-1]).std(axis=0)
    feature_std = np.maximum(feature_std, 1e-6)
    environment_mean = train.environment_targets.mean(axis=0)
    environment_std = np.maximum(train.environment_targets.std(axis=0), 1e-6)
    return {
        "feature_mean": feature_mean,
        "feature_std": feature_std,
        "environment_mean": environment_mean,
        "environment_std": environment_std,
    }


def _transform(split: SplitArrays, transforms: Mapping[str, np.ndarray]) -> tuple[np.ndarray, ...]:
    normalized = (np.log1p(split.values) - transforms["feature_mean"]) / transforms["feature_std"]
    normalized = normalized * split.masks
    inputs = np.concatenate([normalized, split.masks], axis=-1).astype(np.float32)
    environment = (
        (split.environment_targets - transforms["environment_mean"]) / transforms["environment_std"]
    ).astype(np.float32)
    return inputs, split.state_targets.astype(np.float32), environment


def _loader(
    tensors: tuple[np.ndarray, np.ndarray, np.ndarray],
    config: DiagnosticConfig,
    *,
    shuffle: bool,
) -> DataLoader:
    dataset = TensorDataset(*(torch.from_numpy(value) for value in tensors))
    generator = torch.Generator().manual_seed(config.seed)
    return DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=shuffle,
        generator=generator if shuffle else None,
        num_workers=0,
    )


def _view(inputs: torch.Tensor, variant: str) -> torch.Tensor:
    if variant == "single_window":
        return inputs[:, -1:, :]
    if variant == "history_h4":
        return inputs
    raise ObservabilityDiagnosticError(f"未知变体：{variant}")


def _heteroscedastic_loss(
    mean: torch.Tensor, log_variance: torch.Tensor, target: torch.Tensor
) -> torch.Tensor:
    return 0.5 * (torch.exp(-log_variance) * (mean - target).square() + log_variance).mean()


def _epoch(
    model: HistoricalEnvironmentStateEstimator,
    loader: DataLoader,
    device: torch.device,
    variant: str,
    optimizer: torch.optim.Optimizer | None,
) -> float:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    sample_count = 0
    for inputs, state_target, environment_target in loader:
        inputs = _view(inputs.to(device), variant)
        state_target = state_target.to(device)
        environment_target = environment_target.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            state_mean, state_log_variance, environment_mean, environment_log_variance = model(
                inputs
            )
            state_loss = _heteroscedastic_loss(state_mean, state_log_variance, state_target)
            environment_loss = _heteroscedastic_loss(
                environment_mean, environment_log_variance, environment_target
            )
            loss = state_loss + 0.25 * environment_loss
            if training:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
        batch_size = inputs.shape[0]
        total_loss += float(loss.detach()) * batch_size
        sample_count += batch_size
    return total_loss / sample_count


def _predict(
    model: HistoricalEnvironmentStateEstimator,
    loader: DataLoader,
    device: torch.device,
    variant: str,
) -> dict[str, np.ndarray]:
    model.eval()
    collected: dict[str, list[np.ndarray]] = {
        "state_mean": [],
        "state_variance": [],
        "environment_mean": [],
        "environment_variance": [],
        "state_target": [],
        "environment_target": [],
    }
    with torch.no_grad():
        for inputs, state_target, environment_target in loader:
            outputs = model(_view(inputs.to(device), variant))
            state_mean, state_log_variance, environment_mean, environment_log_variance = outputs
            payloads = {
                "state_mean": state_mean,
                "state_variance": state_log_variance.exp(),
                "environment_mean": environment_mean,
                "environment_variance": environment_log_variance.exp(),
                "state_target": state_target,
                "environment_target": environment_target,
            }
            for key, value in payloads.items():
                collected[key].append(value.detach().cpu().numpy())
    return {key: np.concatenate(value, axis=0) for key, value in collected.items()}


def _group_mse(
    prediction: np.ndarray, target: np.ndarray, group_ids: Sequence[str]
) -> dict[str, float]:
    sample_error = np.mean((prediction - target) ** 2, axis=1)
    grouped: dict[str, list[float]] = {}
    for group_id, error in zip(group_ids, sample_error, strict=True):
        grouped.setdefault(group_id, []).append(float(error))
    return {group_id: float(np.mean(errors)) for group_id, errors in grouped.items()}


def _paired_bootstrap_ci(
    history: Mapping[str, float],
    single: Mapping[str, float],
    repetitions: int,
    seed: int,
) -> tuple[float, float, float]:
    groups = sorted(set(history).intersection(single))
    if len(groups) < 2:
        raise ObservabilityDiagnosticError("配对区组数量不足")
    differences = np.asarray([history[group] - single[group] for group in groups])
    generator = np.random.default_rng(seed)
    bootstrapped = np.empty(repetitions, dtype=np.float64)
    for index in range(repetitions):
        sampled = generator.integers(0, len(groups), size=len(groups))
        bootstrapped[index] = differences[sampled].mean()
    lower, upper = np.quantile(bootstrapped, [0.025, 0.975])
    return float(differences.mean()), float(lower), float(upper)


def _group_scores(scores: np.ndarray, group_ids: Sequence[str]) -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for group_id, score in zip(group_ids, scores, strict=True):
        grouped.setdefault(group_id, []).append(float(score))
    return {group_id: float(np.mean(values)) for group_id, values in grouped.items()}


def _ood_auc_ci(
    in_range: Mapping[str, float],
    out_of_range: Mapping[str, float],
    repetitions: int,
    seed: int,
) -> tuple[float, float, float]:
    in_scores = np.asarray(list(in_range.values()), dtype=np.float64)
    out_scores = np.asarray(list(out_of_range.values()), dtype=np.float64)
    labels = np.concatenate([np.zeros(len(in_scores)), np.ones(len(out_scores))])
    scores = np.concatenate([in_scores, out_scores])
    point = float(roc_auc_score(labels, scores))
    generator = np.random.default_rng(seed)
    bootstrapped = np.empty(repetitions, dtype=np.float64)
    for index in range(repetitions):
        in_sample = in_scores[generator.integers(0, len(in_scores), size=len(in_scores))]
        out_sample = out_scores[generator.integers(0, len(out_scores), size=len(out_scores))]
        sampled_labels = np.concatenate([np.zeros(len(in_sample)), np.ones(len(out_sample))])
        sampled_scores = np.concatenate([in_sample, out_sample])
        bootstrapped[index] = roc_auc_score(sampled_labels, sampled_scores)
    lower, upper = np.quantile(bootstrapped, [0.025, 0.975])
    return point, float(lower), float(upper)


def _fit_uncertainty_scale(prediction: Mapping[str, np.ndarray]) -> float:
    errors = np.mean((prediction["state_mean"] - prediction["state_target"]) ** 2, axis=1)
    scores = np.mean(prediction["state_variance"], axis=1)
    denominator = float(np.dot(scores, scores))
    return float(np.dot(scores, errors) / denominator) if denominator > 0.0 else 1.0


def _model_metrics(
    prediction: Mapping[str, np.ndarray], uncertainty_scale: float
) -> dict[str, object]:
    errors = (prediction["state_mean"] - prediction["state_target"]) ** 2
    environment_errors = (prediction["environment_mean"] - prediction["environment_target"]) ** 2
    uncertainty = uncertainty_scale * np.mean(prediction["state_variance"], axis=1)
    sample_error = errors.mean(axis=1)
    correlation = float(np.corrcoef(uncertainty, sample_error)[0, 1])
    if not math.isfinite(correlation):
        correlation = 0.0
    return {
        "state_mse": float(errors.mean()),
        "state_anchor_mse": [float(value) for value in errors.mean(axis=0)],
        "environment_standardized_mse": float(environment_errors.mean()),
        "uncertainty_scale": uncertainty_scale,
        "uncertainty_error_mae": float(np.mean(np.abs(uncertainty - sample_error))),
        "uncertainty_error_correlation": correlation,
        "uncertainty_mean": float(uncertainty.mean()),
    }


def _write_predictions(
    path: Path,
    splits: Mapping[str, SplitArrays],
    predictions: Mapping[str, Mapping[str, Mapping[str, np.ndarray]]],
    scales: Mapping[str, float],
) -> None:
    with path.open("w", encoding="utf-8") as destination:
        for split_name in ("unseen_configuration", "out_of_range"):
            split = splits[split_name]
            for index, (sample_id, group_id) in enumerate(
                zip(split.sample_ids, split.group_ids, strict=True)
            ):
                variants = {}
                for variant in VARIANTS:
                    prediction = predictions[variant][split_name]
                    variants[variant] = {
                        "state_mean": prediction["state_mean"][index].tolist(),
                        "state_variance": prediction["state_variance"][index].tolist(),
                        "calibrated_uncertainty": float(
                            scales[variant] * np.mean(prediction["state_variance"][index])
                        ),
                    }
                destination.write(
                    json.dumps(
                        {
                            "sample_id": sample_id,
                            "group_id": group_id,
                            "split": split_name,
                            "state_target": split.state_targets[index].tolist(),
                            "variants": variants,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n"
                )


def run_diagnostic(*, config_path: Path, input_dir: Path, output_dir: Path) -> dict[str, object]:
    config, raw_config = _load_config(config_path)
    normalized_input = input_dir.expanduser().resolve()
    normalized_output = output_dir.expanduser().resolve()
    if normalized_output.exists() or normalized_output.is_symlink():
        raise ObservabilityDiagnosticError(f"输出目录已存在，不得覆盖：{normalized_output}")
    normalized_output.mkdir(parents=True)
    config_snapshot = normalized_output / "config_snapshot.json"
    input_manifest = normalized_output / "input_manifest.json"
    environment_snapshot = normalized_output / "environment_snapshot.json"
    run_status_path = normalized_output / "run_status.json"
    training_history_path = normalized_output / "training_history.json"
    metrics_path = normalized_output / "metrics.json"
    calibration_path = normalized_output / "calibration.json"
    predictions_path = normalized_output / "predictions.jsonl"
    file_hashes_path = normalized_output / "file_sha256_manifest.json"
    source_files = {split: normalized_input / f"{split}.jsonl" for split in SPLITS}
    if any(not path.is_file() for path in source_files.values()):
        raise ObservabilityDiagnosticError("四个冻结切分文件不完整")
    _write_json(config_snapshot, raw_config)
    _write_json(
        input_manifest,
        {
            "input_dir": str(normalized_input),
            "model_input_fields": list(MODEL_INPUT_FIELDS),
            "splits": {
                split: {
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                }
                for split, path in source_files.items()
            },
        },
    )
    _write_json(
        environment_snapshot,
        {
            "captured_at": _utc_now(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "pid": os.getpid(),
        },
    )
    run_status: dict[str, object] = {
        "status": "running",
        "stage": "loading-data",
        "started_at": _utc_now(),
        "updated_at": _utc_now(),
    }
    _write_json(run_status_path, run_status)
    data_files = {
        "config_snapshot": config_snapshot,
        "input_manifest": input_manifest,
        "environment_snapshot": environment_snapshot,
        "run_status": run_status_path,
        "training_history": training_history_path,
        "metrics": metrics_path,
        "calibration": calibration_path,
        "predictions": predictions_path,
        "file_sha256_manifest": file_hashes_path,
    }

    with capture_console_log(normalized_output / "console.log"):
        print(f"加载任务十七四窗口数据：{normalized_input}")
        try:
            random.seed(config.seed)
            np.random.seed(config.seed)
            torch.manual_seed(config.seed)
            if config.device == "cuda" and not torch.cuda.is_available():
                raise ObservabilityDiagnosticError("配置要求 CUDA，但服务器不可用")
            device = torch.device(config.device)
            if device.type == "cuda":
                torch.cuda.manual_seed_all(config.seed)
                torch.set_float32_matmul_precision("high")
            splits = {split: _load_split(path) for split, path in source_files.items()}
            transforms = _fit_transforms(splits["train"])
            transformed = {
                split: _transform(split_arrays, transforms)
                for split, split_arrays in splits.items()
            }
            train_loaders = {
                variant: _loader(transformed["train"], config, shuffle=True) for variant in VARIANTS
            }
            evaluation_loaders = {
                split: _loader(transformed[split], config, shuffle=False)
                for split in SPLITS
                if split != "train"
            }
            prototype = HistoricalEnvironmentStateEstimator(
                input_size=2 * len(MODEL_INPUT_FIELDS),
                hidden_size=config.hidden_size,
            ).to(device)
            initial_state = {
                name: tensor.detach().clone() for name, tensor in prototype.state_dict().items()
            }
            models = {
                variant: HistoricalEnvironmentStateEstimator(
                    input_size=2 * len(MODEL_INPUT_FIELDS),
                    hidden_size=config.hidden_size,
                ).to(device)
                for variant in VARIANTS
            }
            for model in models.values():
                model.load_state_dict(initial_state)
            del prototype
            parameter_counts = {
                variant: sum(parameter.numel() for parameter in model.parameters())
                for variant, model in models.items()
            }
            if len(set(parameter_counts.values())) != 1:
                raise ObservabilityDiagnosticError("单窗口与四窗口估计器容量不一致")
            optimizers = {
                variant: torch.optim.AdamW(
                    model.parameters(),
                    lr=config.learning_rate,
                    weight_decay=config.weight_decay,
                )
                for variant, model in models.items()
            }
            best_losses = {variant: math.inf for variant in VARIANTS}
            best_states: dict[str, dict[str, torch.Tensor]] = {}
            stale_epochs = {variant: 0 for variant in VARIANTS}
            stopped = {variant: False for variant in VARIANTS}
            histories: dict[str, list[dict[str, float | int]]] = {
                variant: [] for variant in VARIANTS
            }
            run_status.update(stage="training", updated_at=_utc_now())
            _write_json(run_status_path, run_status)
            with swanlab_run(
                config.tracking,
                phase=PHASE,
                config=raw_config,
                artifact_dir=normalized_output,
                data_files=data_files,
            ):
                for epoch in range(1, config.max_epochs + 1):
                    logged: dict[str, float | int] = {"diagnostic/epoch": epoch}
                    for variant in VARIANTS:
                        if stopped[variant]:
                            continue
                        train_loss = _epoch(
                            models[variant],
                            train_loaders[variant],
                            device,
                            variant,
                            optimizers[variant],
                        )
                        calibration_loss = _epoch(
                            models[variant],
                            evaluation_loaders["calibration"],
                            device,
                            variant,
                            None,
                        )
                        histories[variant].append(
                            {
                                "epoch": epoch,
                                "train_loss": train_loss,
                                "calibration_loss": calibration_loss,
                            }
                        )
                        logged[f"diagnostic/{variant}/train_loss"] = train_loss
                        logged[f"diagnostic/{variant}/calibration_loss"] = calibration_loss
                        if calibration_loss < best_losses[variant] - config.minimum_delta:
                            best_losses[variant] = calibration_loss
                            best_states[variant] = {
                                name: tensor.detach().cpu().clone()
                                for name, tensor in models[variant].state_dict().items()
                            }
                            stale_epochs[variant] = 0
                        else:
                            stale_epochs[variant] += 1
                            if stale_epochs[variant] >= config.patience:
                                stopped[variant] = True
                    swanlab.log(logged, step=epoch)
                    _write_json(training_history_path, histories)
                    print(
                        f"epoch={epoch} "
                        + " ".join(f"{variant}={best_losses[variant]:.6f}" for variant in VARIANTS)
                    )
                    if all(stopped.values()):
                        break
                if set(best_states) != set(VARIANTS):
                    raise ObservabilityDiagnosticError("两个估计器未产生有效最佳权重")
                for variant in VARIANTS:
                    models[variant].load_state_dict(best_states[variant])
                    torch.save(
                        {
                            "variant": variant,
                            "state_dict": best_states[variant],
                            "hidden_size": config.hidden_size,
                            "model_input_fields": MODEL_INPUT_FIELDS,
                            "transforms": {
                                key: value.tolist() for key, value in transforms.items()
                            },
                        },
                        normalized_output / f"{variant}.pt",
                    )

                predictions = {
                    variant: {
                        split: _predict(models[variant], evaluation_loaders[split], device, variant)
                        for split in ("calibration", "unseen_configuration", "out_of_range")
                    }
                    for variant in VARIANTS
                }
                uncertainty_scales = {
                    variant: _fit_uncertainty_scale(predictions[variant]["calibration"])
                    for variant in VARIANTS
                }
                constant_mean = splits["train"].state_targets.mean(axis=0)
                constant_errors = (
                    splits["unseen_configuration"].state_targets - constant_mean
                ) ** 2
                constant_mse = float(constant_errors.mean())
                model_metrics = {
                    variant: {
                        split: _model_metrics(
                            predictions[variant][split], uncertainty_scales[variant]
                        )
                        for split in ("calibration", "unseen_configuration", "out_of_range")
                    }
                    for variant in VARIANTS
                }
                group_mse = {
                    variant: _group_mse(
                        predictions[variant]["unseen_configuration"]["state_mean"],
                        predictions[variant]["unseen_configuration"]["state_target"],
                        splits["unseen_configuration"].group_ids,
                    )
                    for variant in VARIANTS
                }
                difference, difference_lower, difference_upper = _paired_bootstrap_ci(
                    group_mse["history_h4"],
                    group_mse["single_window"],
                    config.bootstrap_repetitions,
                    config.seed,
                )
                history_unseen_mse = float(
                    model_metrics["history_h4"]["unseen_configuration"]["state_mse"]
                )
                improvement = (constant_mse - history_unseen_mse) / constant_mse
                uncertainty_scores = {}
                ood_results = {}
                for variant in VARIANTS:
                    uncertainty_scores[variant] = {
                        split: _group_scores(
                            uncertainty_scales[variant]
                            * np.mean(predictions[variant][split]["state_variance"], axis=1),
                            splits[split].group_ids,
                        )
                        for split in ("unseen_configuration", "out_of_range")
                    }
                    auc, auc_lower, auc_upper = _ood_auc_ci(
                        uncertainty_scores[variant]["unseen_configuration"],
                        uncertainty_scores[variant]["out_of_range"],
                        config.bootstrap_repetitions,
                        config.seed,
                    )
                    ood_results[variant] = {
                        "auc": auc,
                        "ci95_lower": auc_lower,
                        "ci95_upper": auc_upper,
                    }
                gates = {
                    "history_beats_constant_by_10_percent": improvement
                    >= config.constant_improvement_threshold,
                    "history_beats_single_group_ci": difference_upper
                    < config.history_vs_single_ci_upper_threshold,
                    "history_uncertainty_identifies_ood": ood_results["history_h4"]["ci95_lower"]
                    > config.ood_auc_ci_lower_threshold,
                }
                metrics = {
                    "constant": {
                        "unseen_configuration_state_mse": constant_mse,
                        "unseen_configuration_state_anchor_mse": [
                            float(value) for value in constant_errors.mean(axis=0)
                        ],
                        "train_state_mean": constant_mean.tolist(),
                    },
                    "models": model_metrics,
                    "parameter_counts": parameter_counts,
                    "history_vs_constant_improvement_fraction": improvement,
                    "history_minus_single_group_mse": {
                        "point": difference,
                        "ci95_lower": difference_lower,
                        "ci95_upper": difference_upper,
                    },
                    "ood_uncertainty": ood_results,
                    "gates": gates,
                    "overall_pass": all(gates.values()),
                }
                calibration = {
                    "fitted_on_split": "calibration",
                    "uncertainty_scales": uncertainty_scales,
                    "bootstrap_unit": "group_id",
                    "bootstrap_repetitions": config.bootstrap_repetitions,
                    "test_splits_not_used_for_fit": [
                        "unseen_configuration",
                        "out_of_range",
                    ],
                }
                _write_json(metrics_path, metrics)
                _write_json(calibration_path, calibration)
                _write_predictions(predictions_path, splits, predictions, uncertainty_scales)
                final_cloud_metrics = {
                    "final/constant_state_mse": constant_mse,
                    "final/single_state_mse": float(
                        model_metrics["single_window"]["unseen_configuration"]["state_mse"]
                    ),
                    "final/history_state_mse": history_unseen_mse,
                    "final/history_constant_improvement": improvement,
                    "final/history_minus_single_ci_upper": difference_upper,
                    "final/history_ood_auc": float(ood_results["history_h4"]["auc"]),
                    "final/history_ood_auc_ci_lower": float(
                        ood_results["history_h4"]["ci95_lower"]
                    ),
                    "final/overall_pass": int(all(gates.values())),
                }
                swanlab.log(final_cloud_metrics, step=config.max_epochs + 1)
                run_status.update(
                    {
                        "status": "finished",
                        "stage": "completed",
                        "finished_at": _utc_now(),
                        "updated_at": _utc_now(),
                        "overall_pass": all(gates.values()),
                    }
                )
                _write_json(run_status_path, run_status)
            artifact_names = [
                *data_files.values(),
                normalized_output / "single_window.pt",
                normalized_output / "history_h4.pt",
                normalized_output / "artifact_manifest.json",
                normalized_output / "console.log",
            ]
            _write_json(
                file_hashes_path,
                {
                    "files": [
                        {
                            "path": str(path),
                            "size_bytes": path.stat().st_size,
                            "sha256": _sha256(path),
                        }
                        for path in artifact_names
                        if path.is_file() and path != file_hashes_path
                    ]
                },
            )
            print(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True))
            return metrics
        except BaseException as error:
            run_status.update(
                {
                    "status": "crashed",
                    "stage": "crashed",
                    "error": str(error),
                    "finished_at": _utc_now(),
                    "updated_at": _utc_now(),
                }
            )
            _write_json(run_status_path, run_status)
            raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行任务十七可辨识性固定诊断")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_diagnostic(
            config_path=args.config,
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
    except (ObservabilityDiagnosticError, OSError, KeyError, ValueError) as error:
        print(f"任务十七可辨识性诊断失败：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
