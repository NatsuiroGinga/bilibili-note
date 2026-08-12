"""LSPR24 RWKV 候选种子 42 快速消融入口。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
import torch
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch import nn

from flow_probe.lspr24_rwkv_screen_models import (
    SCREEN_VARIANTS,
    VARIANT_NAMES,
    ScreenModelConfig,
    TrainNormalizer,
    build_screen_model,
    parameter_budget,
    reshape_history,
)
from flow_probe.lspr24_screen_dataset import Lspr24ScreenDataset
from flow_probe.tracking import REQUIRED_SWANLAB_PROJECT, REQUIRED_SWANLAB_WORKSPACE


CACHE_SCHEMA_VERSION = "lspr24-rwkv-screen-cache-v1"
RUN_SCHEMA_VERSION = "lspr24-rwkv-screen-run-v1"
HISTORY_LENGTH = 4
DEFAULT_TRAIN_LIMIT = 100_000
DEFAULT_VALIDATION_LIMIT = 20_000
DEFAULT_EPOCHS = 5
DEFAULT_BATCH_SIZE = 512
CHECKPOINT_INTERVAL_STEPS = 20
VARIANT_DISPLAY_NAMES = {
    "B1": "基础因果Transformer",
    "B1F": "字段注意力Transformer",
    "A2": "RWKV状态条件字段Transformer（主候选）",
    "B3": "RWKV时间混合模型",
}


class Lspr24RwkvScreenError(ValueError):
    """缓存、训练或运行参数不满足候选筛选合同。"""


@dataclass(frozen=True)
class CacheArrays:
    """四个独立训练进程共享的只读内存映射数组。"""

    train_sequence: np.ndarray
    train_labels: np.ndarray
    train_sample_ids: np.ndarray
    validation_sequence: np.ndarray
    validation_labels: np.ndarray
    validation_sample_ids: np.ndarray
    metadata: dict[str, Any]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_npy(path: Path, value: np.ndarray) -> None:
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)
    os.replace(temporary, path)


def _fixed_string_array(values: tuple[str, ...]) -> np.ndarray:
    width = max((len(value) for value in values), default=1)
    return np.asarray(values, dtype=f"<U{width}")


def _field_groups(dataset: Lspr24ScreenDataset) -> tuple[tuple[str, ...], tuple[int, ...]]:
    group_names = tuple(dataset.field_groups)
    field_to_group: dict[str, int] = {}
    for group_index, group_name in enumerate(group_names):
        for field_name in dataset.field_groups[group_name]:
            field_to_group[field_name] = group_index
    try:
        group_ids = tuple(field_to_group[field] for field in dataset.allowed_fields)
    except KeyError as error:
        raise Lspr24RwkvScreenError(f"字段缺少语义组：{error.args[0]}") from error
    return group_names, group_ids


def prepare_cache(
    manifest_path: Path,
    cache_dir: Path,
    seed: int,
    train_limit: int,
    validation_limit: int,
) -> dict[str, Any]:
    """单次扫描真实清单并原子发布四进程共享数组缓存。"""
    manifest_path = Path(manifest_path).resolve()
    cache_dir = Path(cache_dir).resolve()
    if cache_dir.exists():
        raise Lspr24RwkvScreenError(f"共享缓存目录已存在，不得复用：{cache_dir}")
    if train_limit <= 0 or validation_limit <= 0:
        raise Lspr24RwkvScreenError("训练与验证样本上限必须为正整数")
    staging = cache_dir.with_name(cache_dir.name + f".partial.{os.getpid()}")
    if staging.exists():
        raise Lspr24RwkvScreenError(f"共享缓存暂存目录已存在：{staging}")
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir()

    started = time.perf_counter()
    dataset = Lspr24ScreenDataset(manifest_path)
    train = dataset.load(
        split_name="train",
        history_length=HISTORY_LENGTH,
        sample_limit=train_limit,
    )
    validation = dataset.load(
        split_name="validation",
        history_length=HISTORY_LENGTH,
        sample_limit=validation_limit,
    )
    if train.feature_columns != validation.feature_columns:
        raise Lspr24RwkvScreenError("训练与验证字段顺序不一致")
    if len(np.unique(train.labels)) != 2 or len(np.unique(validation.labels)) != 2:
        raise Lspr24RwkvScreenError("训练与验证样本都必须同时包含两类")

    feature_count = len(dataset.allowed_fields)
    train_raw = reshape_history(train.features, HISTORY_LENGTH, feature_count)
    validation_raw = reshape_history(validation.features, HISTORY_LENGTH, feature_count)
    normalizer = TrainNormalizer.fit(train_raw)
    train_sequence = normalizer.transform(train_raw)
    validation_sequence = normalizer.transform(validation_raw)
    group_names, group_ids = _field_groups(dataset)
    model_config = ScreenModelConfig()
    parameter_counts = parameter_budget(feature_count, group_ids, model_config)

    arrays: dict[str, np.ndarray] = {
        "train_sequence.npy": train_sequence,
        "train_labels.npy": train.labels.astype(np.int64, copy=False),
        "train_sample_ids.npy": _fixed_string_array(train.sample_ids),
        "validation_sequence.npy": validation_sequence,
        "validation_labels.npy": validation.labels.astype(np.int64, copy=False),
        "validation_sample_ids.npy": _fixed_string_array(validation.sample_ids),
        "normalizer_replacement.npy": normalizer.replacement.astype(np.float64, copy=False),
        "normalizer_mean.npy": normalizer.mean.astype(np.float64, copy=False),
        "normalizer_std.npy": normalizer.std.astype(np.float64, copy=False),
    }
    for file_name, value in arrays.items():
        _write_npy(staging / file_name, value)

    manifest_sha256 = _sha256(manifest_path)
    metadata: dict[str, Any] = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "dataset_manifest": str(manifest_path),
        "dataset_manifest_sha256": manifest_sha256,
        "history_length": HISTORY_LENGTH,
        "time_steps": HISTORY_LENGTH + 1,
        "seed": seed,
        "train_limit": train_limit,
        "validation_limit": validation_limit,
        "train_sample_count": int(len(train.labels)),
        "validation_sample_count": int(len(validation.labels)),
        "feature_count": feature_count,
        "feature_names": list(dataset.allowed_fields),
        "flattened_feature_columns": list(train.feature_columns),
        "field_group_names": list(group_names),
        "field_group_ids": list(group_ids),
        "normalizer": {
            "source_split": "train",
            "non_finite_replacement": "per-field-train-median",
            "clip_range": [-10.0, 10.0],
        },
        "model_config": model_config.to_dict(),
        "parameter_counts": parameter_counts,
        "parameter_ratio": max(parameter_counts.values()) / min(parameter_counts.values()),
        "array_files": {
            file_name: {
                "shape": list(value.shape),
                "dtype": str(value.dtype),
                "sha256": _sha256(staging / file_name),
            }
            for file_name, value in arrays.items()
        },
        "preparation_seconds": time.perf_counter() - started,
        "immutable_read_only": True,
        "labels_separate_from_features": True,
    }
    _write_json(staging / "cache-manifest.json", metadata)
    os.replace(staging, cache_dir)
    for path in cache_dir.iterdir():
        path.chmod(0o444)
    cache_dir.chmod(0o555)
    return metadata


def _load_cache(manifest_path: Path, cache_dir: Path) -> CacheArrays:
    manifest_path = Path(manifest_path).resolve()
    cache_dir = Path(cache_dir).resolve()
    metadata_path = cache_dir / "cache-manifest.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Lspr24RwkvScreenError(f"无法读取共享缓存清单：{metadata_path}") from error
    if metadata.get("schema_version") != CACHE_SCHEMA_VERSION:
        raise Lspr24RwkvScreenError("共享缓存版本不匹配")
    if metadata.get("dataset_manifest") != str(manifest_path):
        raise Lspr24RwkvScreenError("共享缓存绑定的数据清单路径不匹配")
    if metadata.get("dataset_manifest_sha256") != _sha256(manifest_path):
        raise Lspr24RwkvScreenError("共享缓存绑定的数据清单哈希不匹配")
    if metadata.get("history_length") != HISTORY_LENGTH:
        raise Lspr24RwkvScreenError("共享缓存历史长度不是 H=4")
    if metadata.get("labels_separate_from_features") is not True:
        raise Lspr24RwkvScreenError("共享缓存未声明标签与特征物理分离")

    loaded: dict[str, np.ndarray] = {}
    registered = metadata.get("array_files")
    if not isinstance(registered, dict):
        raise Lspr24RwkvScreenError("共享缓存缺少数组登记")
    for file_name, receipt in registered.items():
        if not isinstance(file_name, str) or not isinstance(receipt, dict):
            raise Lspr24RwkvScreenError("共享缓存数组登记格式错误")
        path = cache_dir / file_name
        if not path.is_file():
            raise Lspr24RwkvScreenError(f"共享缓存数组不存在：{path}")
        value = np.load(path, mmap_mode="r", allow_pickle=False)
        if list(value.shape) != receipt.get("shape") or str(value.dtype) != receipt.get("dtype"):
            raise Lspr24RwkvScreenError(f"共享缓存数组模式不匹配：{file_name}")
        loaded[file_name] = value

    required = {
        "train_sequence.npy",
        "train_labels.npy",
        "train_sample_ids.npy",
        "validation_sequence.npy",
        "validation_labels.npy",
        "validation_sample_ids.npy",
    }
    missing = required.difference(loaded)
    if missing:
        raise Lspr24RwkvScreenError(f"共享缓存缺少数组：{', '.join(sorted(missing))}")
    train_sequence = loaded["train_sequence.npy"]
    validation_sequence = loaded["validation_sequence.npy"]
    if train_sequence.ndim != 3 or validation_sequence.ndim != 3:
        raise Lspr24RwkvScreenError("共享特征数组必须是 [N,5,F]")
    if train_sequence.shape[1:] != validation_sequence.shape[1:]:
        raise Lspr24RwkvScreenError("训练与验证共享数组形状不兼容")
    if train_sequence.shape[1] != HISTORY_LENGTH + 1:
        raise Lspr24RwkvScreenError("共享特征数组时间步不是五步")
    return CacheArrays(
        train_sequence=train_sequence,
        train_labels=loaded["train_labels.npy"],
        train_sample_ids=loaded["train_sample_ids.npy"],
        validation_sequence=validation_sequence,
        validation_labels=loaded["validation_labels.npy"],
        validation_sample_ids=loaded["validation_sample_ids.npy"],
        metadata=metadata,
    )


def _model_config(metadata: dict[str, Any]) -> ScreenModelConfig:
    raw = metadata.get("model_config")
    if not isinstance(raw, dict):
        raise Lspr24RwkvScreenError("共享缓存缺少模型配置")
    return ScreenModelConfig(**raw)


def _group_ids(metadata: dict[str, Any]) -> tuple[int, ...]:
    raw = metadata.get("field_group_ids")
    if not isinstance(raw, list) or not raw:
        raise Lspr24RwkvScreenError("共享缓存缺少字段语义组编号")
    return tuple(int(value) for value in raw)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def _classification_metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    predictions = (probabilities >= 0.5).astype(np.int64)
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    return {
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "benign_false_positive_rate": float(matrix[0, 1] / max(matrix[0].sum(), 1)),
    }


def _save_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    variant: str,
    seed: int,
    epoch: int,
    global_step: int,
    best_pr_auc: float,
) -> None:
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    torch.save(
        {
            "schema_version": RUN_SCHEMA_VERSION,
            "variant": variant,
            "seed": seed,
            "epoch": epoch,
            "global_step": global_step,
            "best_pr_auc": best_pr_auc,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
            "torch_rng_state": torch.get_rng_state(),
            "cuda_rng_state": torch.cuda.get_rng_state_all(),
        },
        temporary,
    )
    os.replace(temporary, path)


def _evaluate(
    model: nn.Module,
    features: np.ndarray,
    labels: np.ndarray,
    batch_size: int,
    device: torch.device,
) -> tuple[dict[str, float], np.ndarray, float, float]:
    model.eval()
    probabilities: list[np.ndarray] = []
    started = time.perf_counter()
    with torch.no_grad():
        for start in range(0, len(features), batch_size):
            batch = torch.from_numpy(np.asarray(features[start : start + batch_size])).to(
                device,
                non_blocking=True,
            )
            with torch.autocast(
                device_type="cuda",
                dtype=torch.bfloat16,
                enabled=device.type == "cuda",
            ):
                logits = model(batch)
            probabilities.append(torch.sigmoid(logits.float()).cpu().numpy())
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    inference_seconds = time.perf_counter() - started
    probability_array = np.concatenate(probabilities).astype(np.float64, copy=False)
    metrics = _classification_metrics(np.asarray(labels, dtype=np.int64), probability_array)
    throughput = len(labels) / max(inference_seconds, 1e-9)
    return metrics, probability_array, inference_seconds, throughput


class _SwanLabTracker:
    """在线跟踪失败时保留本地训练和失败记录。"""

    def __init__(self, output_dir: Path, run_name: str, variant: str, config: dict[str, Any]) -> None:
        self.output_dir = output_dir
        self.run_name = run_name
        self.variant = variant
        self.client: Any | None = None
        self.run: Any | None = None
        self.logging_enabled = True
        self.status: dict[str, Any] = {"status": "not_started"}
        try:
            import swanlab

            self.client = swanlab
            self.run = swanlab.init(
                project=REQUIRED_SWANLAB_PROJECT,
                workspace=REQUIRED_SWANLAB_WORKSPACE,
                name=f"{run_name}-{VARIANT_DISPLAY_NAMES[variant]}",
                description="LSPR24 RWKV 候选种子42快速消融",
                config=config,
                mode="online",
                tags=["lspr24", "rwkv", "screen", variant.lower()],
                log_dir=str(output_dir / "swanlog"),
            )
            self.status = {"status": "running", "run_id": str(self.run.id)}
        except Exception as error:
            self.status = {"status": "initialization_failed", "error": str(error)}
            _write_json(output_dir / "swanlab-status.json", self.status)

    def log(self, values: dict[str, int | float], step: int) -> None:
        if self.client is None or not self.logging_enabled:
            return
        try:
            self.client.log(values, step=step)
        except Exception as error:
            self.status = {
                "status": "logging_failed",
                "run_id": str(self.run.id) if self.run is not None else "",
                "error": str(error),
            }
            _write_json(self.output_dir / "swanlab-status.json", self.status)
            self.logging_enabled = False

    def finish(self) -> None:
        if self.client is not None:
            try:
                self.client.finish()
                self.status = {
                    "status": "finished",
                    "run_id": str(self.run.id) if self.run is not None else "",
                }
            except Exception as error:
                self.status = {
                    "status": "finish_failed",
                    "run_id": str(self.run.id) if self.run is not None else "",
                    "error": str(error),
                }
        _write_json(self.output_dir / "swanlab-status.json", self.status)

    def fail(self, error: BaseException) -> None:
        if self.client is not None:
            try:
                self.client.finish(state="crashed", error=str(error))
            except Exception:
                pass
        self.status = {
            "status": "crashed",
            "run_id": str(self.run.id) if self.run is not None else "",
            "error_type": type(error).__name__,
            "error": str(error),
        }
        _write_json(self.output_dir / "swanlab-status.json", self.status)


def _write_predictions(
    path: Path,
    variant: str,
    sample_ids: np.ndarray,
    labels: np.ndarray,
    probabilities: np.ndarray,
) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for sample_id, label, probability in zip(
            sample_ids,
            labels,
            probabilities,
            strict=True,
        ):
            handle.write(
                json.dumps(
                    {
                        "variant": variant,
                        "sample_id": str(sample_id),
                        "truth": int(label),
                        "malicious_probability": float(probability),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )


def train_variant(
    manifest_path: Path,
    cache_dir: Path,
    output_dir: Path,
    run_name: str,
    variant: str,
    seed: int,
    batch_size: int,
    epochs: int,
) -> dict[str, Any]:
    """在隔离进程中训练一个变体，并只读共享内存映射缓存。"""
    variant = variant.upper()
    if variant not in SCREEN_VARIANTS:
        raise Lspr24RwkvScreenError(f"未知变体：{variant}")
    if seed != 42 or epochs != DEFAULT_EPOCHS:
        raise Lspr24RwkvScreenError("快速消融固定种子 42 和最多 5 轮")
    if batch_size not in (256, 512):
        raise Lspr24RwkvScreenError("并行快速消融批量只能统一为 512 或 256")
    if not torch.cuda.is_available():
        raise Lspr24RwkvScreenError("正式快速消融必须使用可用 CUDA GPU")
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise Lspr24RwkvScreenError(f"变体输出目录已存在，不得复用：{output_dir}")
    output_dir.mkdir(parents=True)
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir()
    _write_json(output_dir / "status.json", {"status": "running", "variant": variant})
    tracker: _SwanLabTracker | None = None

    try:
        cache = _load_cache(manifest_path, cache_dir)
        if cache.metadata.get("seed") != seed:
            raise Lspr24RwkvScreenError("共享缓存种子绑定不匹配")
        if cache.metadata.get("train_limit") != DEFAULT_TRAIN_LIMIT:
            raise Lspr24RwkvScreenError("共享缓存训练样本上限不是 100000")
        if cache.metadata.get("validation_limit") != DEFAULT_VALIDATION_LIMIT:
            raise Lspr24RwkvScreenError("共享缓存验证样本上限不是 20000")
        _seed_everything(seed)
        device = torch.device("cuda")
        model_config = _model_config(cache.metadata)
        group_ids = _group_ids(cache.metadata)
        feature_count = int(cache.metadata["feature_count"])
        counts = parameter_budget(feature_count, group_ids, model_config)
        model = build_screen_model(variant, feature_count, group_ids, model_config).to(device)
        parameter_count = counts[variant]
        negatives = max(int((np.asarray(cache.train_labels) == 0).sum()), 1)
        positives = max(int((np.asarray(cache.train_labels) == 1).sum()), 1)
        criterion = nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor(negatives / positives, device=device, dtype=torch.float32)
        )
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=3e-4,
            weight_decay=1e-2,
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
        config: dict[str, Any] = {
            "schema_version": RUN_SCHEMA_VERSION,
            "dataset_manifest": str(Path(manifest_path).resolve()),
            "dataset_manifest_sha256": cache.metadata["dataset_manifest_sha256"],
            "cache_dir": str(Path(cache_dir).resolve()),
            "cache_schema_version": cache.metadata["schema_version"],
            "cache_manifest_sha256": _sha256(Path(cache_dir) / "cache-manifest.json"),
            "variant": variant,
            "variant_name": VARIANT_NAMES[variant],
            "display_name": VARIANT_DISPLAY_NAMES[variant],
            "run_name": run_name,
            "seed": seed,
            "history_length": HISTORY_LENGTH,
            "train_limit": DEFAULT_TRAIN_LIMIT,
            "validation_limit": DEFAULT_VALIDATION_LIMIT,
            "epochs": epochs,
            "batch_size": batch_size,
            "optimizer": "AdamW",
            "learning_rate": 3e-4,
            "weight_decay": 1e-2,
            "scheduler": "CosineAnnealingLR",
            "positive_class_weight": negatives / positives,
            "parameter_count": parameter_count,
            "parameter_counts_all_variants": counts,
            "model_config": model_config.to_dict(),
            "parallel_efficiency_comparable": False,
            "efficiency_note": "四进程并行耗时与吞吐不用于公平效率结论，胜出模型需单进程复测",
        }
        _write_json(output_dir / "config.json", config)
        _write_json(
            output_dir / "environment.json",
            {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "scikit_learn": sklearn.__version__,
                "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "gpu": torch.cuda.get_device_name(device),
                "gpu_count_visible": torch.cuda.device_count(),
            },
        )
        tracker = _SwanLabTracker(output_dir, run_name, variant, config)
        history_path = output_dir / "training_history.jsonl"
        best_pr_auc = float("-inf")
        best_epoch = 0
        best_probabilities: np.ndarray | None = None
        best_metrics: dict[str, float] | None = None
        best_inference_seconds = 0.0
        best_inference_throughput = 0.0
        global_step = 0
        training_started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)

        for epoch in range(1, epochs + 1):
            model.train()
            epoch_started = time.perf_counter()
            epoch_loss_sum = 0.0
            epoch_samples = 0
            indices = np.random.default_rng(seed + epoch).permutation(len(cache.train_labels))
            for start in range(0, len(indices), batch_size):
                batch_indices = indices[start : start + batch_size]
                features = torch.from_numpy(
                    np.asarray(cache.train_sequence[batch_indices])
                ).to(device, non_blocking=True)
                labels = torch.from_numpy(
                    np.asarray(cache.train_labels[batch_indices], dtype=np.float32)
                ).to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits = model(features)
                    loss = criterion(logits, labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()
                global_step += 1
                epoch_loss_sum += float(loss.detach().cpu()) * len(batch_indices)
                epoch_samples += len(batch_indices)
                if global_step % CHECKPOINT_INTERVAL_STEPS == 0:
                    _save_checkpoint(
                        checkpoints_dir / "latest.pt",
                        model,
                        optimizer,
                        scheduler,
                        variant,
                        seed,
                        epoch,
                        global_step,
                        best_pr_auc,
                    )
                if global_step == 1 or global_step % 50 == 0:
                    elapsed = time.perf_counter() - training_started
                    throughput = epoch_samples / max(time.perf_counter() - epoch_started, 1e-9)
                    print(
                        f"进度：变体={variant}（{VARIANT_DISPLAY_NAMES[variant]}） "
                        f"轮次={epoch}/{epochs} 步数={global_step} "
                        f"已处理={epoch_samples}/{len(indices)} 吞吐={throughput:.1f}样本/秒 "
                        f"累计耗时={elapsed:.1f}秒",
                        flush=True,
                    )
            scheduler.step()
            torch.cuda.synchronize(device)
            epoch_seconds = time.perf_counter() - epoch_started
            train_loss = epoch_loss_sum / max(epoch_samples, 1)
            validation_metrics, probabilities, inference_seconds, inference_throughput = _evaluate(
                model,
                cache.validation_sequence,
                cache.validation_labels,
                batch_size,
                device,
            )
            elapsed = time.perf_counter() - training_started
            remaining = (elapsed / epoch) * (epochs - epoch)
            peak_memory = int(torch.cuda.max_memory_allocated(device))
            record: dict[str, int | float | str] = {
                "variant": variant,
                "display_name": VARIANT_DISPLAY_NAMES[variant],
                "epoch": epoch,
                "train_loss": train_loss,
                **validation_metrics,
                "epoch_seconds": epoch_seconds,
                "cumulative_seconds": elapsed,
                "inference_seconds": inference_seconds,
                "inference_throughput_samples_per_second": inference_throughput,
                "peak_gpu_memory_bytes": peak_memory,
                "estimated_remaining_seconds": remaining,
            }
            with history_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            tracker.log(
                {
                    "epoch": epoch,
                    "train/loss": train_loss,
                    "validation/pr_auc": validation_metrics["pr_auc"],
                    "validation/macro_f1": validation_metrics["macro_f1"],
                    "validation/balanced_accuracy": validation_metrics["balanced_accuracy"],
                    "validation/precision": validation_metrics["precision"],
                    "validation/recall": validation_metrics["recall"],
                    "validation/benign_false_positive_rate": validation_metrics[
                        "benign_false_positive_rate"
                    ],
                    "runtime/cumulative_seconds": elapsed,
                    "runtime/inference_throughput": inference_throughput,
                    "runtime/peak_gpu_memory_bytes": peak_memory,
                },
                step=epoch,
            )
            print(
                f"轮次完成：变体={variant}（{VARIANT_DISPLAY_NAMES[variant]}） "
                f"轮次={epoch}/{epochs} 训练损失={train_loss:.6f} "
                f"验证PR-AUC={validation_metrics['pr_auc']:.6f} "
                f"宏平均F1={validation_metrics['macro_f1']:.6f} 累计耗时={elapsed:.1f}秒 "
                f"推理吞吐={inference_throughput:.1f}样本/秒 峰值显存={peak_memory}字节 "
                f"预计剩余={remaining:.1f}秒",
                flush=True,
            )
            if validation_metrics["pr_auc"] > best_pr_auc:
                best_pr_auc = validation_metrics["pr_auc"]
                best_epoch = epoch
                best_probabilities = probabilities.copy()
                best_metrics = validation_metrics.copy()
                best_inference_seconds = inference_seconds
                best_inference_throughput = inference_throughput
                _save_checkpoint(
                    checkpoints_dir / "best.pt",
                    model,
                    optimizer,
                    scheduler,
                    variant,
                    seed,
                    epoch,
                    global_step,
                    best_pr_auc,
                )

        _save_checkpoint(
            checkpoints_dir / "latest.pt",
            model,
            optimizer,
            scheduler,
            variant,
            seed,
            epochs,
            global_step,
            best_pr_auc,
        )
        if best_probabilities is None or best_metrics is None:
            raise Lspr24RwkvScreenError("训练结束但没有产生最佳验证结果")
        total_seconds = time.perf_counter() - training_started
        summary: dict[str, Any] = {
            "schema_version": RUN_SCHEMA_VERSION,
            "status": "finished",
            "variant": variant,
            "variant_name": VARIANT_NAMES[variant],
            "display_name": VARIANT_DISPLAY_NAMES[variant],
            "best_epoch": best_epoch,
            "validation": best_metrics,
            "train_sample_count": int(len(cache.train_labels)),
            "validation_sample_count": int(len(cache.validation_labels)),
            "parameter_count": parameter_count,
            "training_seconds": total_seconds,
            "best_inference_seconds": best_inference_seconds,
            "best_inference_throughput_samples_per_second": best_inference_throughput,
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "parallel_efficiency_comparable": False,
        }
        _write_json(output_dir / f"metrics_{variant}.json", summary)
        _write_predictions(
            output_dir / f"predictions_{variant}.jsonl.gz",
            variant,
            cache.validation_sample_ids,
            cache.validation_labels,
            best_probabilities,
        )
        tracker.log(
            {
                "best/epoch": best_epoch,
                "best/validation_pr_auc": best_pr_auc,
                "best/training_seconds": total_seconds,
            },
            step=epochs + 1,
        )
        tracker.finish()
        summary["swanlab"] = tracker.status
        _write_json(output_dir / "summary.json", summary)
        _write_json(output_dir / "status.json", {"status": "finished", "variant": variant})
        return summary
    except BaseException as error:
        if tracker is not None:
            tracker.fail(error)
        _write_json(
            output_dir / "status.json",
            {"status": "failed", "variant": variant, "error_type": type(error).__name__, "error": str(error)},
        )
        raise


def probe_cache(manifest_path: Path, cache_dir: Path, batch_size: int, device_name: str) -> dict[str, Any]:
    """使用真实共享缓存执行一个小批的四变体前向入口。"""
    cache = _load_cache(manifest_path, cache_dir)
    if batch_size <= 0 or batch_size > len(cache.validation_sequence):
        raise Lspr24RwkvScreenError("真实前向小批大小不合法")
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise Lspr24RwkvScreenError("真实前向要求 CUDA，但当前不可用")
    model_config = _model_config(cache.metadata)
    group_ids = _group_ids(cache.metadata)
    feature_count = int(cache.metadata["feature_count"])
    counts = parameter_budget(feature_count, group_ids, model_config)
    batch = torch.from_numpy(np.asarray(cache.validation_sequence[:batch_size])).to(device)
    results: dict[str, Any] = {}
    with torch.no_grad():
        for variant in SCREEN_VARIANTS:
            model = build_screen_model(variant, feature_count, group_ids, model_config).to(device)
            model.eval()
            logits = model(batch)
            if logits.shape != (batch_size,) or not torch.isfinite(logits).all():
                raise Lspr24RwkvScreenError(f"变体 {variant} 真实小批前向输出不合法")
            results[variant] = {
                "parameter_count": counts[variant],
                "logit_shape": list(logits.shape),
                "finite": True,
            }
    return {"status": "passed", "batch_size": batch_size, "device": str(device), "variants": results}


def select_parallel_batch_size(
    manifest_path: Path,
    cache_dir: Path,
    output_path: Path,
    process_count: int,
) -> dict[str, Any]:
    """短暂实测单模型峰值并为四进程统一选择 512 或 256。"""
    if process_count != 4:
        raise Lspr24RwkvScreenError("候选矩阵固定并行四个变体")
    if not torch.cuda.is_available():
        raise Lspr24RwkvScreenError("显存门禁要求 CUDA GPU")
    cache = _load_cache(manifest_path, cache_dir)
    device = torch.device("cuda")
    model_config = _model_config(cache.metadata)
    group_ids = _group_ids(cache.metadata)
    feature_count = int(cache.metadata["feature_count"])
    counts = parameter_budget(feature_count, group_ids, model_config)
    total_memory = int(torch.cuda.get_device_properties(device).total_memory)
    attempts: list[dict[str, Any]] = []
    selected: int | None = None
    for batch_size in (512, 256):
        peaks: dict[str, int] = {}
        failed: str | None = None
        for variant in SCREEN_VARIANTS:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)
            try:
                model = build_screen_model(variant, feature_count, group_ids, model_config).to(device)
                optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
                sample = torch.zeros(
                    batch_size,
                    HISTORY_LENGTH + 1,
                    feature_count,
                    device=device,
                    dtype=torch.float32,
                )
                target = torch.zeros(batch_size, device=device)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    loss = nn.functional.binary_cross_entropy_with_logits(model(sample), target)
                loss.backward()
                optimizer.step()
                torch.cuda.synchronize(device)
                peaks[variant] = int(torch.cuda.max_memory_allocated(device))
                del loss, target, sample, optimizer, model
            except torch.OutOfMemoryError as error:
                failed = str(error)
                torch.cuda.empty_cache()
                break
        maximum_peak = max(peaks.values(), default=0)
        context_allowance = 512 * 1024**2
        reserve = max(4 * 1024**3, int(total_memory * 0.20))
        estimated_total = process_count * (maximum_peak + context_allowance) + reserve
        passed = failed is None and estimated_total <= int(total_memory * 0.90)
        attempts.append(
            {
                "batch_size": batch_size,
                "variant_peak_bytes": peaks,
                "estimated_four_process_bytes": estimated_total,
                "total_gpu_memory_bytes": total_memory,
                "passed": passed,
                "failure": failed,
            }
        )
        if passed:
            selected = batch_size
            break
    if selected is None:
        result = {
            "status": "failed",
            "selected_batch_size": None,
            "process_count": process_count,
            "parameter_counts": counts,
            "attempts": attempts,
        }
        _write_json(output_path, result)
        raise Lspr24RwkvScreenError("统一批量 512 和 256 均未通过四进程显存门禁")
    result = {
        "status": "passed",
        "selected_batch_size": selected,
        "process_count": process_count,
        "parameter_counts": counts,
        "attempts": attempts,
        "efficiency_note": "显存门禁与四进程并行指标不作为公平效率结论",
    }
    _write_json(output_path, result)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 LSPR24 RWKV 候选快速消融")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-cache", help="单次准备只读共享数组缓存")
    prepare.add_argument("--dataset-manifest", type=Path, required=True)
    prepare.add_argument("--cache-dir", type=Path, required=True)
    prepare.add_argument("--seed", type=int, default=42)
    prepare.add_argument("--train-limit", type=int, default=DEFAULT_TRAIN_LIMIT)
    prepare.add_argument("--validation-limit", type=int, default=DEFAULT_VALIDATION_LIMIT)

    train = subparsers.add_parser("train", help="训练一个隔离变体")
    train.add_argument("--dataset-manifest", type=Path, required=True)
    train.add_argument("--cache-dir", type=Path, required=True)
    train.add_argument("--output-dir", type=Path, required=True)
    train.add_argument("--run-name", required=True)
    train.add_argument("--variant", choices=SCREEN_VARIANTS, required=True)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    train.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)

    probe = subparsers.add_parser("probe-cache", help="真实共享缓存小批前向")
    probe.add_argument("--dataset-manifest", type=Path, required=True)
    probe.add_argument("--cache-dir", type=Path, required=True)
    probe.add_argument("--batch-size", type=int, default=8)
    probe.add_argument("--device", choices=("cpu", "cuda"), default="cuda")

    gate = subparsers.add_parser("gpu-gate", help="统一四进程批量显存门禁")
    gate.add_argument("--dataset-manifest", type=Path, required=True)
    gate.add_argument("--cache-dir", type=Path, required=True)
    gate.add_argument("--output", type=Path, required=True)
    gate.add_argument("--process-count", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "prepare-cache":
        result = prepare_cache(
            args.dataset_manifest,
            args.cache_dir,
            args.seed,
            args.train_limit,
            args.validation_limit,
        )
    elif args.command == "train":
        result = train_variant(
            args.dataset_manifest,
            args.cache_dir,
            args.output_dir,
            args.run_name,
            args.variant,
            args.seed,
            args.batch_size,
            args.epochs,
        )
    elif args.command == "probe-cache":
        result = probe_cache(
            args.dataset_manifest,
            args.cache_dir,
            args.batch_size,
            args.device,
        )
    elif args.command == "gpu-gate":
        result = select_parallel_batch_size(
            args.dataset_manifest,
            args.cache_dir,
            args.output,
            args.process_count,
        )
    else:
        raise AssertionError(f"未处理命令：{args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
