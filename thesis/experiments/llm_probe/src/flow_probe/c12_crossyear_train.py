"""C12 跨年度阶段 A 基线与阶段 B 主机制训练、预测和独立评价入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

import numpy as np
import sklearn
import torch
from numpy.lib.format import open_memmap
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch import nn

from flow_probe.c12_crossyear_models import (
    PHASE_A_VARIANTS,
    PHASE_B_VARIANTS,
    TRAINABLE_VARIANTS,
    VARIANT_DISPLAY_NAMES,
    VARIANT_ROLES,
    C12ModelConfig,
    ReceiverSourceScorer,
    PhaseBVariantModel,
    build_parameter_matched_models,
    build_phase_b_parameter_matched_models,
    kernel_equivalence_boundaries,
    trainable_parameter_count,
)
from flow_probe.tracking import REQUIRED_SWANLAB_PROJECT, REQUIRED_SWANLAB_WORKSPACE


RUN_SCHEMA = "c12-crossyear-phase-a-q0-run-v1"
PHASE_B_RUN_SCHEMA = "c12-crossyear-phase-b-q0-run-v1"
REPRESENTATION_SCHEMA = "c12-crossyear-receiver-representations-v1"
TARGET_PREFIX_REPRESENTATION_SCHEMA = "c12-target-prefix-representation-v1"
CACHE_SCHEMA = "lspr-crossyear-python-cache-v1"
CHECKPOINT_INTERVAL_STEPS = 20
LOG_INTERVAL_STEPS = 25
ENCODED_ROLES = ("source-train", "source-validation", "target-development")


@dataclass(frozen=True)
class ControlContract:
    """仅由源训练和源验证冻结的阶段 B 控制与晋升合同。"""

    source_anchor: np.ndarray
    source_variance: np.ndarray
    drift_median: float
    drift_scale: float
    drift_maximum: float
    enter_threshold: float
    full_threshold: float
    rollback_threshold: float
    quality_threshold: float
    step_budget: float
    cumulative_budget: float
    state_norm_maximum: float
    quality_window: int
    cumulative_decay: float
    checkpoint_steps: int
    new_normal_threshold: float
    sample_weight_maximum: float
    reference_step_budget: float
    block_rows: int
    block_mass_maximum: float
    candidate_decay: float
    stability_scale: float
    evidence_threshold: float
    promotion_blocks: int
    candidate_mass_minimum: float
    reference_radius_maximum: float
    promotion_step: float
    promotion_maximum: float
    rescue_weight: float

    def to_json(self) -> dict[str, object]:
        result = dict(self.__dict__)
        result["source_anchor"] = self.source_anchor.tolist()
        result["source_variance"] = self.source_variance.tolist()
        return result


class C12TrainError(ValueError):
    """训练、预测或评价违反阶段 A 合同。"""


@dataclass(frozen=True)
class SequenceRole:
    """只读逐流缓存及由序列元数据确定的完整序列索引。"""

    role: str
    root: Path
    x_value: np.ndarray
    x_missing: np.ndarray
    delta_t_us: np.ndarray
    sample_id: np.ndarray
    sequence_id: np.ndarray
    position: np.ndarray
    valid_length: np.ndarray
    starts: np.ndarray
    lengths: np.ndarray
    labels: np.ndarray | None

    @property
    def row_count(self) -> int:
        return int(self.x_value.shape[0])

    @property
    def sequence_count(self) -> int:
        return int(self.starts.shape[0])


class SwanTracker:
    """在线 SwanLab 记录器；本地训练日志仍是权威证据。"""

    def __init__(
        self,
        output_dir: Path,
        run_name: str,
        config: Mapping[str, object],
        phase: str = "phase-a",
    ) -> None:
        import swanlab

        self.output_dir = output_dir
        self.client = swanlab
        self.run = swanlab.init(
            project=REQUIRED_SWANLAB_PROJECT,
            workspace=REQUIRED_SWANLAB_WORKSPACE,
            name=run_name,
            description=(
                "C12 阶段 B 漂移触发有界状态控制与可信双参照校正"
                if phase == "phase-b"
                else "C12 阶段 A 跨年度神经公平基线"
            ),
            config=dict(config),
            mode="online",
            tags=["c12", phase, "q0", "seed42"],
            log_dir=str(output_dir / "swanlog"),
        )
        self.status = {"status": "running", "run_id": str(self.run.id)}
        _write_json(output_dir / "swanlab-status.json", self.status)

    def log(self, values: Mapping[str, int | float], step: int) -> None:
        self.client.log(dict(values), step=step)

    def finish(self) -> None:
        self.client.finish()
        self.status["status"] = "finished"
        _write_json(self.output_dir / "swanlab-status.json", self.status)

    def fail(self, error: BaseException) -> None:
        try:
            self.client.finish(state="crashed", error=str(error))
        finally:
            self.status.update({"status": "failed", "error_type": type(error).__name__})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _append_jsonl(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n")


def _write_npy(path: Path, value: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)
    os.replace(temporary, path)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise C12TrainError(f"JSON 顶层必须是对象：{path}")
    return value


def _role_array_path(cache_root: Path, role: str, name: str) -> Path:
    path = cache_root / f"role={role}" / f"{name}.npy"
    if not path.is_file():
        raise C12TrainError(f"缓存数组不存在：{path}")
    return path


def _sequence_index(
    role: str,
    sequence_id: np.ndarray,
    position: np.ndarray,
    valid_length: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if sequence_id.ndim != 2 or sequence_id.shape[1] != 32:
        raise C12TrainError(f"{role} sequence_id 必须是 [N,32]")
    starts_mask = np.ones(len(position), dtype=bool)
    starts_mask[1:] = np.any(sequence_id[1:] != sequence_id[:-1], axis=1)
    starts = np.flatnonzero(starts_mask).astype(np.int64, copy=False)
    lengths = valid_length[starts].astype(np.int64, copy=False)
    if len(starts) == 0 or np.any(position[starts] != 0):
        raise C12TrainError(f"{role} 序列起点不合法")
    if np.any(lengths < 1) or np.any(lengths > 128):
        raise C12TrainError(f"{role} 序列长度超出 1 至 128")
    expected_ends = starts + lengths
    actual_ends = np.r_[starts[1:], len(position)]
    if not np.array_equal(expected_ends, actual_ends):
        raise C12TrainError(f"{role} valid_length 与实际连续块不一致")
    for start, length in zip(starts, lengths, strict=True):
        if not np.array_equal(position[start : start + length], np.arange(length)):
            raise C12TrainError(f"{role} position 不连续")
        if not np.all(valid_length[start : start + length] == length):
            raise C12TrainError(f"{role} 序列内 valid_length 漂移")
    return starts, lengths


def load_cache(cache_root: Path) -> tuple[dict[str, Any], dict[str, SequenceRole]]:
    """只按发布目录解析数组，拒绝缓存清单中的历史暂存路径。"""
    cache_root = cache_root.resolve()
    manifest_path = cache_root / "cache-manifest.json"
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") != CACHE_SCHEMA:
        raise C12TrainError("Q0 Python 缓存模式不匹配")
    if manifest.get("final_accessed") is not False:
        raise C12TrainError("阶段 A 拒绝 final_accessed 非 false 的缓存")
    if len(manifest.get("model_fields", [])) != 77:
        raise C12TrainError("模型字段必须恰为 77 个共同字段")
    declared_roles = manifest.get("roles")
    if not isinstance(declared_roles, dict) or set(declared_roles) != {
        "source-train", "source-validation", "target-prefix", "target-development"
    }:
        raise C12TrainError("缓存必须恰有四个冻结角色")
    roles: dict[str, SequenceRole] = {}
    for role, block in declared_roles.items():
        if not isinstance(block, dict):
            raise C12TrainError(f"{role} 清单块不合法")
        arrays = {
            name: np.load(_role_array_path(cache_root, role, name), mmap_mode="r")
            for name in (
                "x_value", "x_missing", "delta_t_us", "sample_id",
                "sequence_id", "position", "valid_length", "padding_mask",
            )
        }
        rows = int(block.get("row_count", -1))
        if any(len(value) != rows for value in arrays.values()):
            raise C12TrainError(f"{role} 数组行数与缓存清单不一致")
        if arrays["x_value"].shape != (rows, 77) or arrays["x_missing"].shape != (rows, 77):
            raise C12TrainError(f"{role} 模型值或缺失位形状不合法")
        if not np.all(arrays["padding_mask"] == 1):
            raise C12TrainError(f"{role} 发布缓存逐流有效位必须全为 1")
        starts, lengths = _sequence_index(
            role,
            arrays["sequence_id"],
            arrays["position"],
            arrays["valid_length"],
        )
        if len(starts) != int(block.get("sequence_count", -1)):
            raise C12TrainError(f"{role} 序列数与缓存清单不一致")
        labels = None
        if role in ("source-train", "source-validation"):
            labels = np.load(_role_array_path(cache_root, role, "labels"), mmap_mode="r")
            if labels.shape != (rows,) or not np.isin(labels, (0, 1)).all():
                raise C12TrainError(f"{role} 源标签数组不合法")
        roles[role] = SequenceRole(
            role=role,
            root=cache_root / f"role={role}",
            x_value=arrays["x_value"],
            x_missing=arrays["x_missing"],
            delta_t_us=arrays["delta_t_us"],
            sample_id=arrays["sample_id"],
            sequence_id=arrays["sequence_id"],
            position=arrays["position"],
            valid_length=arrays["valid_length"],
            starts=starts,
            lengths=lengths,
            labels=labels,
        )
    if roles["target-prefix"].labels is not None:
        raise C12TrainError("阶段 A 的 target-prefix 不得提供标签")
    return manifest, roles


def _sequence_order(sequence_count: int, seed: int, epoch: int) -> np.ndarray:
    return np.random.default_rng(seed + epoch).permutation(sequence_count)


def _training_sequence_pools(role: SequenceRole) -> tuple[np.ndarray, np.ndarray]:
    if role.labels is None:
        raise C12TrainError("训练双池划分要求源标签")
    malicious: list[int] = []
    benign: list[int] = []
    for sequence_index, (row_start, length) in enumerate(
        zip(role.starts, role.lengths, strict=True)
    ):
        labels = role.labels[int(row_start) : int(row_start + length)]
        if np.any(labels == 1):
            malicious.append(sequence_index)
        elif np.all(labels == 0):
            benign.append(sequence_index)
        else:
            raise C12TrainError("源训练序列标签不属于含恶意或全良性双池")
    if not malicious or not benign:
        raise C12TrainError("源训练双池任一为空")
    return np.asarray(malicious, dtype=np.int64), np.asarray(benign, dtype=np.int64)


def _sample_pool(
    pool: np.ndarray,
    count: int,
    random_generator: np.random.Generator,
) -> np.ndarray:
    samples: list[np.ndarray] = []
    remaining = count
    while remaining > 0:
        permutation = random_generator.permutation(pool)
        take = min(remaining, len(permutation))
        samples.append(permutation[:take])
        remaining -= take
    return np.concatenate(samples)


def _balanced_sequence_order(
    role: SequenceRole,
    seed: int,
    epoch: int,
    batch_size: int,
) -> tuple[np.ndarray, dict[str, int | bool | str]]:
    if batch_size <= 0 or batch_size % 2 != 0:
        raise C12TrainError("双池等量采样要求正偶数序列批量")
    malicious_pool, benign_pool = _training_sequence_pools(role)
    batches = int(np.ceil(role.sequence_count / batch_size))
    draws_per_pool = batches * (batch_size // 2)
    random_generator = np.random.default_rng(seed + epoch)
    malicious_draws = _sample_pool(malicious_pool, draws_per_pool, random_generator)
    benign_draws = _sample_pool(benign_pool, draws_per_pool, random_generator)
    order = np.empty(batches * batch_size, dtype=np.int64)
    for batch_index in range(batches):
        start = batch_index * batch_size
        middle = batch_index * (batch_size // 2)
        batch = np.concatenate(
            (
                malicious_draws[middle : middle + batch_size // 2],
                benign_draws[middle : middle + batch_size // 2],
            )
        )
        order[start : start + batch_size] = random_generator.permutation(batch)
    receipt: dict[str, int | bool | str] = {
        "schema_version": "c12-balanced-sequence-pools-v1",
        "malicious_sequence_pool_count": int(len(malicious_pool)),
        "all_benign_sequence_pool_count": int(len(benign_pool)),
        "batches_per_epoch": batches,
        "batch_size_sequences": batch_size,
        "malicious_sequences_per_batch": batch_size // 2,
        "all_benign_sequences_per_batch": batch_size // 2,
        "malicious_draws_per_epoch": draws_per_pool,
        "all_benign_draws_per_epoch": draws_per_pool,
        "sampling_with_deterministic_pool_recycling": True,
        "every_batch_equal_pool_counts": True,
    }
    return order, receipt


def _iter_sequence_batches(
    role: SequenceRole,
    order: np.ndarray,
    batch_size: int,
    start_offset: int = 0,
) -> Iterator[tuple[int, np.ndarray, torch.Tensor, torch.Tensor, torch.Tensor | None]]:
    for offset in range(start_offset, len(order), batch_size):
        indices = order[offset : offset + batch_size]
        lengths = role.lengths[indices]
        maximum = int(lengths.max())
        features = np.zeros((len(indices), maximum, 155), dtype=np.float32)
        valid = np.zeros((len(indices), maximum), dtype=bool)
        labels = np.zeros((len(indices), maximum), dtype=np.float32) if role.labels is not None else None
        for batch_index, sequence_index in enumerate(indices):
            row_start = int(role.starts[sequence_index])
            length = int(role.lengths[sequence_index])
            row_slice = slice(row_start, row_start + length)
            features[batch_index, :length, :77] = role.x_value[row_slice]
            features[batch_index, :length, 77:154] = role.x_missing[row_slice]
            delta_seconds = np.maximum(role.delta_t_us[row_slice], 0).astype(np.float64) / 1_000_000.0
            features[batch_index, :length, 154] = np.log1p(delta_seconds).astype(np.float32)
            valid[batch_index, :length] = True
            if labels is not None and role.labels is not None:
                labels[batch_index, :length] = role.labels[row_slice]
        yield (
            offset,
            indices,
            torch.from_numpy(features),
            torch.from_numpy(valid),
            torch.from_numpy(labels) if labels is not None else None,
        )


def _iter_representation_batches(
    role: SequenceRole,
    representation: np.ndarray,
    order: np.ndarray,
    batch_size: int,
    start_offset: int = 0,
) -> Iterator[tuple[int, np.ndarray, torch.Tensor, torch.Tensor, torch.Tensor | None]]:
    for offset in range(start_offset, len(order), batch_size):
        indices = order[offset : offset + batch_size]
        lengths = role.lengths[indices]
        maximum = int(lengths.max())
        values = np.zeros((len(indices), maximum, representation.shape[1]), dtype=np.float32)
        valid = np.zeros((len(indices), maximum), dtype=bool)
        labels = np.zeros((len(indices), maximum), dtype=np.float32) if role.labels is not None else None
        for batch_index, sequence_index in enumerate(indices):
            row_start = int(role.starts[sequence_index])
            length = int(role.lengths[sequence_index])
            row_slice = slice(row_start, row_start + length)
            values[batch_index, :length] = representation[row_slice]
            valid[batch_index, :length] = True
            if labels is not None and role.labels is not None:
                labels[batch_index, :length] = role.labels[row_slice]
        yield (
            offset,
            indices,
            torch.from_numpy(values),
            torch.from_numpy(valid),
            torch.from_numpy(labels) if labels is not None else None,
        )


def _binary_metrics(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict[str, Any]:
    if labels.shape != probabilities.shape or labels.size == 0:
        raise C12TrainError("指标标签与概率形状不一致或为空")
    predictions = (probabilities >= threshold).astype(np.uint8)
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    return {
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "malicious_f1": float(f1_score(labels, predictions, pos_label=1, zero_division=0)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "brier": float(brier_score_loss(labels, probabilities)),
        "ece_15_equal_frequency": _ece_equal_frequency(labels, probabilities, 15),
        "confusion_matrix": matrix.tolist(),
        "threshold": float(threshold),
        "prevalence": float(labels.mean()),
        "pr_auc_over_prevalence": float(average_precision_score(labels, probabilities) / max(labels.mean(), 1e-12)),
    }


def _ece_equal_frequency(labels: np.ndarray, probabilities: np.ndarray, bins: int) -> float:
    order = np.argsort(probabilities, kind="stable")
    total = len(order)
    error = 0.0
    for indices in np.array_split(order, bins):
        if len(indices):
            error += len(indices) / total * abs(float(labels[indices].mean()) - float(probabilities[indices].mean()))
    return float(error)


def _freeze_threshold(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, Any]:
    if labels.shape != probabilities.shape or labels.size == 0:
        raise C12TrainError("源阈值冻结的标签与概率形状不一致或为空")
    if not np.isfinite(probabilities).all():
        raise C12TrainError("源阈值冻结拒绝非有限概率")
    benign = labels == 0
    malicious = labels == 1
    allowed_false_positives = int(np.floor(int(benign.sum()) * 100 / 1_000_000))
    unique_probabilities, inverse = np.unique(probabilities, return_inverse=True)
    benign_by_group = np.bincount(
        inverse, weights=benign.astype(np.int64), minlength=len(unique_probabilities)
    ).astype(np.int64)
    malicious_by_group = np.bincount(
        inverse, weights=malicious.astype(np.int64), minlength=len(unique_probabilities)
    ).astype(np.int64)
    candidate_thresholds = unique_probabilities[::-1]
    cumulative_false_positives = np.cumsum(benign_by_group[::-1])
    cumulative_true_positives = np.cumsum(malicious_by_group[::-1])
    allowed = cumulative_false_positives <= allowed_false_positives
    if np.any(allowed):
        best_true_positives = cumulative_true_positives[allowed].max()
        best = allowed & (cumulative_true_positives == best_true_positives)
        threshold = float(candidate_thresholds[np.flatnonzero(best)[0]])
    else:
        threshold = float(
            np.nextafter(
                probabilities.max(),
                np.asarray(np.inf, dtype=probabilities.dtype),
            )
        )
    predictions = probabilities >= threshold
    false_positives = int(np.sum(predictions & benign))
    true_positives = int(np.sum(predictions & malicious))
    if false_positives > allowed_false_positives:
        raise C12TrainError(
            "BF16 可观测并列概率组阈值违反源误报预算："
            f"实际={false_positives}，允许={allowed_false_positives}"
        )
    recall = float(np.sum(predictions & malicious) / max(int(malicious.sum()), 1))
    return {
        "schema_version": "c12-source-validation-threshold-v2",
        "selection_role": "source-validation",
        "criterion": "按实际可观测唯一概率组整体扫描；每百万良性流误报不超过100时召回最高，召回并列取更高阈值",
        "threshold": threshold,
        "observable_probability_dtype": str(probabilities.dtype),
        "observable_probability_group_count": int(len(unique_probabilities)),
        "same_probability_group_split": False,
        "allowed_false_positives": allowed_false_positives,
        "actual_false_positives": false_positives,
        "actual_true_positives": true_positives,
        "false_positive_budget_verified": True,
        "recall": recall,
        "target_label_used": False,
        "final_accessed": False,
    }


def _seal_source_validation_predictions(
    output_dir: Path,
    role: SequenceRole,
    probabilities: np.ndarray,
    threshold_receipt: Mapping[str, Any],
) -> tuple[Path, Path]:
    if probabilities.shape != (role.row_count,) or not np.isfinite(probabilities).all():
        raise C12TrainError("源验证逐流概率形状不合法或包含非有限值")
    predictions_dir = output_dir / "predictions"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    path = predictions_dir / "source-validation.npz"
    temporary = path.with_suffix(f".npz.partial.{os.getpid()}")
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            probability=probabilities.astype(np.float32, copy=False),
            sample_id=np.asarray(role.sample_id),
            sequence_id=np.asarray(role.sequence_id),
            position=np.asarray(role.position),
            valid_length=np.asarray(role.valid_length),
        )
    os.replace(temporary, path)
    receipt_path = predictions_dir / "source-validation-receipt.json"
    _write_json(
        receipt_path,
        {
            "schema_version": "c12-source-validation-predictions-v2",
            "row_count": role.row_count,
            "sequence_count": role.sequence_count,
            "prediction_sha256": _sha256(path),
            "probability_dtype": "float32",
            "identity_arrays": [
                "sample_id",
                "sequence_id",
                "position",
                "valid_length",
            ],
            "threshold_receipt_schema": threshold_receipt["schema_version"],
            "threshold_selected_here": True,
            "target_label_used": False,
            "final_accessed": False,
        },
    )
    return path, receipt_path


def _environment(device: torch.device) -> dict[str, Any]:
    result = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "device": str(device),
    }
    if device.type == "cuda":
        result["gpu"] = torch.cuda.get_device_name(device)
        result["gpu_total_memory_bytes"] = int(torch.cuda.get_device_properties(device).total_memory)
    return result


def _save_checkpoint(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    torch.save(dict(payload), temporary)
    os.replace(temporary, path)


def _evaluate_model(
    model: nn.Module,
    batches: Iterator[tuple[int, np.ndarray, torch.Tensor, torch.Tensor, torch.Tensor | None]],
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    model.eval()
    all_labels: list[np.ndarray] = []
    all_probabilities: list[np.ndarray] = []
    sample_count = 0
    started = time.perf_counter()
    with torch.no_grad():
        for _, _, values, valid, labels in batches:
            if labels is None:
                raise C12TrainError("有监督评价缺少标签")
            values = values.to(device, non_blocking=True)
            valid = valid.to(device, non_blocking=True)
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                logits = model(values, valid)
            mask = valid.cpu().numpy()
            all_probabilities.append(torch.sigmoid(logits).float().cpu().numpy()[mask])
            all_labels.append(labels.numpy()[mask].astype(np.uint8))
            sample_count += int(mask.sum())
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    seconds = time.perf_counter() - started
    return (
        np.concatenate(all_labels),
        np.concatenate(all_probabilities),
        seconds,
        sample_count / max(seconds, 1e-9),
    )


def _common_run_config(
    cache_root: Path,
    manifest: Mapping[str, object],
    model_config: C12ModelConfig,
    seed: int,
    batch_size: int,
    epochs: int,
) -> dict[str, Any]:
    return {
        "schema_version": RUN_SCHEMA,
        "cache_root": str(cache_root.resolve()),
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "cache_schema_version": manifest["schema_version"],
        "final_accessed": False,
        "input_fields": ["x_value", "x_missing", "log1p(delta_t_us/1e6)"],
        "forbidden_model_inputs": ["sample_id", "sequence_id", "group_key_ref", "label", "year_role"],
        "maximum_sequence_length": 128,
        "prediction_update_order": "当前位置先预测，后更新状态；填充位不预测也不更新",
        "seed": seed,
        "batch_size_sequences": batch_size,
        "epochs": epochs,
        "optimizer": "AdamW",
        "learning_rate": 3e-4,
        "weight_decay": 1e-2,
        "scheduler": "CosineAnnealingLR",
        "gradient_clip_norm": 1.0,
        "model_config": model_config.to_dict(),
        "swanlab": {
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "project": REQUIRED_SWANLAB_PROJECT,
            "mode": "online",
        },
    }


def train_receiver(
    cache_root: Path,
    output_dir: Path,
    run_name: str,
    batch_size: int,
    epochs: int,
    seed: int,
) -> dict[str, Any]:
    """第一阶段只在 source-train 训练一次共同接收器。"""
    if output_dir.exists():
        raise C12TrainError("共同接收器输出目录已存在，拒绝覆盖")
    output_dir.mkdir(parents=True)
    _seed_everything(seed)
    manifest, roles = load_cache(cache_root)
    train_role = roles["source-train"]
    validation_role = roles["source-validation"]
    if train_role.labels is None:
        raise C12TrainError("source-train 缺少标签")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise C12TrainError("阶段 A 真实训练要求 CUDA")
    model_config = C12ModelConfig()
    model = ReceiverSourceScorer(model_config).to(device)
    criterion = nn.BCEWithLogitsLoss()
    _, pool_receipt = _balanced_sequence_order(train_role, seed, 1, batch_size)
    pool_receipt.update(
        {
            "state": "planned",
            "planned_epochs": epochs,
            "planned_steps": int(pool_receipt["batches_per_epoch"]) * epochs,
            "planned_malicious_draws_total": int(pool_receipt["malicious_draws_per_epoch"])
            * epochs,
            "planned_all_benign_draws_total": int(pool_receipt["all_benign_draws_per_epoch"])
            * epochs,
            "actual_epochs": 0,
            "actual_steps": 0,
            "loss": "unweighted BCEWithLogitsLoss；双池等量批次不以行级pos_weight替代",
            "final_accessed": False,
        }
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    config = _common_run_config(cache_root, manifest, model_config, seed, batch_size, epochs)
    config.update({
        "phase": "共同第一阶段接收器训练",
        "train_role": "source-train",
        "selection_role": "source-validation",
        "target_roles_read": [],
        "trainable_parameters": trainable_parameter_count(model),
        "training_sequence_sampling": pool_receipt,
    })
    _write_json(output_dir / "config.json", config)
    _write_json(output_dir / "environment-receipt.json", _environment(device))
    _write_json(output_dir / "training-pool-receipt.json", pool_receipt)
    _write_json(output_dir / "status.json", {"state": "running", "final_accessed": False})
    tracker: SwanTracker | None = None
    global_step = 0
    completed_epochs = 0
    try:
        tracker = SwanTracker(output_dir, run_name, config)
        tracker.log({
            "data/source_train_rows": train_role.row_count,
            "data/source_train_sequences": train_role.sequence_count,
            "data/source_validation_rows": validation_role.row_count,
            "data/source_validation_sequences": validation_role.sequence_count,
            "optimizer/learning_rate": optimizer.param_groups[0]["lr"],
        }, step=0)
        best_pr_auc = float("-inf")
        best_epoch = 0
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        for epoch in range(1, epochs + 1):
            model.train()
            order, epoch_pool_receipt = _balanced_sequence_order(
                train_role, seed, epoch, batch_size
            )
            if epoch_pool_receipt["every_batch_equal_pool_counts"] is not True:
                raise C12TrainError("共同接收器训练批次未满足双池等量合同")
            epoch_loss = 0.0
            epoch_rows = 0
            epoch_started = time.perf_counter()
            for offset, _, values, valid, labels in _iter_sequence_batches(train_role, order, batch_size):
                assert labels is not None
                values = values.to(device, non_blocking=True)
                valid = valid.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits = model(values, valid)
                    loss = criterion(logits[valid], labels[valid])
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                global_step += 1
                rows = int(valid.sum().item())
                epoch_rows += rows
                epoch_loss += float(loss.detach().cpu()) * rows
                elapsed = time.perf_counter() - epoch_started
                if global_step == 1 or global_step % LOG_INTERVAL_STEPS == 0:
                    tracker.log({
                        "train/loss": float(loss.detach().cpu()),
                        "optimizer/learning_rate": optimizer.param_groups[0]["lr"],
                        "runtime/train_rows_per_second": epoch_rows / max(elapsed, 1e-9),
                        "runtime/peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
                    }, step=global_step)
                    print(
                        f"共同接收器进度：轮次={epoch}/{epochs} 步={global_step} "
                        f"序列偏移={offset}/{len(order)} 行吞吐={epoch_rows / max(elapsed, 1e-9):.1f}/秒",
                        flush=True,
                    )
                if global_step % CHECKPOINT_INTERVAL_STEPS == 0:
                    _save_checkpoint(output_dir / "checkpoints/latest.pt", {
                        "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                        "scheduler": scheduler.state_dict(), "epoch": epoch,
                        "next_sequence_offset": offset + batch_size, "global_step": global_step,
                        "best_pr_auc": best_pr_auc, "seed": seed,
                    })
            scheduler.step()
            labels_np, probabilities, inference_seconds, throughput = _evaluate_model(
                model,
                _iter_sequence_batches(
                    validation_role,
                    np.arange(validation_role.sequence_count),
                    batch_size,
                ),
                device,
            )
            metrics = _binary_metrics(labels_np, probabilities, 0.5)
            record = {
                "epoch": epoch,
                "global_step": global_step,
                "train_loss": epoch_loss / max(epoch_rows, 1),
                "validation": metrics,
                "validation_inference_seconds": inference_seconds,
                "validation_rows_per_second": throughput,
                "learning_rate": optimizer.param_groups[0]["lr"],
                "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            }
            _append_jsonl(output_dir / "training-history.jsonl", record)
            tracker.log({
                "validation/pr_auc": metrics["pr_auc"],
                "validation/macro_f1": metrics["macro_f1"],
                "runtime/validation_rows_per_second": throughput,
                "runtime/peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            }, step=global_step)
            if metrics["pr_auc"] > best_pr_auc:
                best_pr_auc = float(metrics["pr_auc"])
                best_epoch = epoch
                _save_checkpoint(output_dir / "checkpoints/best.pt", {
                    "model": model.state_dict(), "epoch": epoch, "global_step": global_step,
                    "validation_pr_auc": best_pr_auc, "seed": seed,
                    "model_config": model_config.to_dict(),
                })
            completed_epochs = epoch
        if completed_epochs != epochs or global_step != int(pool_receipt["planned_steps"]):
            raise C12TrainError(
                "共同接收器实际训练预算不完整："
                f"轮次={completed_epochs}/{epochs}，步骤={global_step}/{pool_receipt['planned_steps']}"
            )
        completed_pool_receipt = dict(pool_receipt)
        completed_pool_receipt.update(
            {
                "state": "finished",
                "actual_epochs": completed_epochs,
                "actual_steps": global_step,
                "actual_malicious_draws_total": int(
                    pool_receipt["malicious_draws_per_epoch"]
                )
                * completed_epochs,
                "actual_all_benign_draws_total": int(
                    pool_receipt["all_benign_draws_per_epoch"]
                )
                * completed_epochs,
            }
        )
        _write_json(output_dir / "training-pool-receipt.json", completed_pool_receipt)
        summary = {
            "schema_version": RUN_SCHEMA,
            "state": "finished",
            "phase": "共同第一阶段接收器训练",
            "best_epoch": best_epoch,
            "best_validation_pr_auc": best_pr_auc,
            "fixed_budget_steps": global_step,
            "training_seconds": time.perf_counter() - started,
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "final_accessed": False,
        }
        tracker.finish()
        summary["swanlab"] = tracker.status
        _write_json(output_dir / "summary.json", summary)
        _write_json(output_dir / "status.json", {"state": "finished", "final_accessed": False})
        _write_artifact_manifest(output_dir)
        return summary
    except BaseException as error:
        failed_pool_receipt = dict(pool_receipt)
        failed_pool_receipt.update(
            {
                "state": "failed",
                "actual_epochs": completed_epochs,
                "actual_steps": global_step,
            }
        )
        _write_json(output_dir / "training-pool-receipt.json", failed_pool_receipt)
        if tracker is not None:
            tracker.fail(error)
            _write_json(output_dir / "swanlab-status.json", tracker.status)
        _write_json(output_dir / "status.json", {
            "state": "failed", "error_type": type(error).__name__,
            "error": str(error), "final_accessed": False,
        })
        raise


def encode_receiver(
    cache_root: Path,
    receiver_checkpoint: Path,
    output_dir: Path,
    batch_size: int,
) -> dict[str, Any]:
    """把冻结接收表示一次落盘；明确不读取或编码 target-prefix。"""
    if output_dir.exists():
        raise C12TrainError("冻结表示输出目录已存在，拒绝覆盖")
    output_dir.mkdir(parents=True)
    manifest, roles = load_cache(cache_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise C12TrainError("冻结表示编码要求 CUDA")
    config = C12ModelConfig()
    model = ReceiverSourceScorer(config).to(device)
    checkpoint = torch.load(receiver_checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    role_records: dict[str, Any] = {}
    torch.cuda.reset_peak_memory_stats(device)
    started = time.perf_counter()
    with torch.no_grad():
        for role_name in ENCODED_ROLES:
            role = roles[role_name]
            role_dir = output_dir / f"role={role_name}"
            role_dir.mkdir()
            partial = role_dir / "phi.npy.partial"
            representation = open_memmap(
                partial,
                mode="w+",
                dtype=np.float16,
                shape=(role.row_count, config.hidden_size),
            )
            processed = 0
            for _, indices, values, valid, _ in _iter_sequence_batches(
                role,
                np.arange(role.sequence_count),
                batch_size,
            ):
                values = values.to(device, non_blocking=True)
                valid_device = valid.to(device, non_blocking=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    phi = model.receiver(values, valid_device)
                phi_np = phi.float().cpu().numpy()
                valid_np = valid.numpy()
                for batch_index, sequence_index in enumerate(indices):
                    row_start = int(role.starts[sequence_index])
                    length = int(role.lengths[sequence_index])
                    representation[row_start : row_start + length] = phi_np[batch_index][valid_np[batch_index]]
                    processed += length
                if processed == role.row_count or processed % 25_000 < 128:
                    elapsed = time.perf_counter() - started
                    print(
                        f"冻结表示：角色={role_name} 已处理={processed}/{role.row_count} "
                        f"累计吞吐={processed / max(elapsed, 1e-9):.1f}行/秒",
                        flush=True,
                    )
            representation.flush()
            final_path = role_dir / "phi.npy"
            os.replace(partial, final_path)
            role_records[role_name] = {
                "path": str(final_path),
                "shape": [role.row_count, config.hidden_size],
                "dtype": "float16",
                "sha256": _sha256(final_path),
                "row_count": role.row_count,
                "sequence_count": role.sequence_count,
            }
    receipt = {
        "schema_version": REPRESENTATION_SCHEMA,
        "receiver_checkpoint": str(receiver_checkpoint.resolve()),
        "receiver_checkpoint_sha256": _sha256(receiver_checkpoint),
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "encoded_roles": role_records,
        "excluded_roles": ["target-prefix"],
        "target_labels_read": False,
        "model_input_fields": ["x_value", "x_missing", "delta_t_us"],
        "group_key_ref_used_as_model_input": False,
        "sample_id_used_as_model_input": False,
        "final_accessed": False,
        "encoding_seconds": time.perf_counter() - started,
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
        "source_cache_schema": manifest["schema_version"],
    }
    _write_json(output_dir / "representation-manifest.json", receipt)
    _write_artifact_manifest(output_dir)
    return receipt


def encode_target_prefix(
    cache_root: Path,
    receiver_checkpoint: Path,
    output_dir: Path,
    batch_size: int,
) -> dict[str, Any]:
    """使用阶段 A 冻结接收器单独编码无标签目标前缀。"""
    if output_dir.exists():
        raise C12TrainError("目标前缀表示输出目录已存在，拒绝覆盖")
    output_dir.mkdir(parents=True)
    manifest, roles = load_cache(cache_root)
    role = roles["target-prefix"]
    if role.labels is not None:
        raise C12TrainError("目标前缀编码入口拒绝任何标签")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise C12TrainError("目标前缀表示编码要求 CUDA")
    config = C12ModelConfig()
    model = ReceiverSourceScorer(config).to(device)
    checkpoint = torch.load(receiver_checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    partial = output_dir / "phi.npy.partial"
    representation = open_memmap(
        partial,
        mode="w+",
        dtype=np.float16,
        shape=(role.row_count, config.hidden_size),
    )
    processed = 0
    started = time.perf_counter()
    torch.cuda.reset_peak_memory_stats(device)
    with torch.no_grad():
        for _, indices, values, valid, _ in _iter_sequence_batches(
            role,
            np.arange(role.sequence_count),
            batch_size,
        ):
            values = values.to(device, non_blocking=True)
            valid_device = valid.to(device, non_blocking=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                phi = model.receiver(values, valid_device)
            phi_np = phi.float().cpu().numpy()
            valid_np = valid.numpy()
            for batch_index, sequence_index in enumerate(indices):
                row_start = int(role.starts[sequence_index])
                length = int(role.lengths[sequence_index])
                representation[row_start : row_start + length] = phi_np[batch_index][
                    valid_np[batch_index]
                ]
                processed += length
            if processed == role.row_count or processed % 25_000 < 128:
                elapsed = time.perf_counter() - started
                print(
                    f"目标前缀冻结表示：已处理={processed}/{role.row_count} "
                    f"吞吐={processed / max(elapsed, 1e-9):.1f}行/秒",
                    flush=True,
                )
    representation.flush()
    final_path = output_dir / "phi.npy"
    os.replace(partial, final_path)
    receipt = {
        "schema_version": TARGET_PREFIX_REPRESENTATION_SCHEMA,
        "role": "target-prefix",
        "path": str(final_path.resolve()),
        "shape": [role.row_count, config.hidden_size],
        "dtype": "float16",
        "sha256": _sha256(final_path),
        "row_count": role.row_count,
        "sequence_count": role.sequence_count,
        "receiver_checkpoint_sha256": _sha256(receiver_checkpoint),
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "labels_read": False,
        "prediction_update_order": "本制品只编码冻结表示；阶段 B 回放严格先预测后更新",
        "final_accessed": False,
        "encoding_seconds": time.perf_counter() - started,
        "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
        "source_cache_schema": manifest["schema_version"],
    }
    _write_json(output_dir / "target-prefix-representation-manifest.json", receipt)
    _write_artifact_manifest(output_dir)
    return receipt


def _load_representations(
    cache_root: Path,
    representation_root: Path,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    receipt_path = representation_root / "representation-manifest.json"
    receipt = _load_json(receipt_path)
    if receipt.get("schema_version") != REPRESENTATION_SCHEMA or receipt.get("final_accessed") is not False:
        raise C12TrainError("冻结表示清单不合法")
    if receipt.get("cache_manifest_sha256") != _sha256(cache_root / "cache-manifest.json"):
        raise C12TrainError("冻结表示与 Q0 缓存哈希不一致")
    if receipt.get("excluded_roles") != ["target-prefix"]:
        raise C12TrainError("阶段 A 冻结表示必须排除 target-prefix")
    arrays: dict[str, np.ndarray] = {}
    records = receipt.get("encoded_roles")
    if not isinstance(records, dict) or set(records) != set(ENCODED_ROLES):
        raise C12TrainError("冻结表示角色不完整")
    for role, record in records.items():
        if not isinstance(record, dict):
            raise C12TrainError(f"冻结表示角色记录不合法：{role}")
        path = representation_root / f"role={role}" / "phi.npy"
        if _sha256(path) != record.get("sha256"):
            raise C12TrainError(f"冻结表示哈希不匹配：{role}")
        arrays[role] = np.load(path, mmap_mode="r")
    return arrays, receipt


def _load_target_prefix_representation(
    cache_root: Path,
    representation_root: Path,
) -> tuple[np.ndarray, dict[str, Any]]:
    receipt_path = representation_root / "target-prefix-representation-manifest.json"
    receipt = _load_json(receipt_path)
    if (
        receipt.get("schema_version") != TARGET_PREFIX_REPRESENTATION_SCHEMA
        or receipt.get("role") != "target-prefix"
        or receipt.get("labels_read") is not False
        or receipt.get("final_accessed") is not False
    ):
        raise C12TrainError("目标前缀冻结表示清单不合法")
    if receipt.get("cache_manifest_sha256") != _sha256(cache_root / "cache-manifest.json"):
        raise C12TrainError("目标前缀表示与 Q0 缓存哈希不一致")
    path = representation_root / "phi.npy"
    if _sha256(path) != receipt.get("sha256"):
        raise C12TrainError("目标前缀表示哈希不匹配")
    return np.load(path, mmap_mode="r"), receipt


def _source_anchor_and_variance(
    representation: np.ndarray,
    labels: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    normal_indices = np.flatnonzero(labels == 0)
    if len(normal_indices) < 2:
        raise C12TrainError("源训练正常样本不足以冻结源锚")
    total = np.zeros(representation.shape[1], dtype=np.float64)
    total_square = np.zeros(representation.shape[1], dtype=np.float64)
    for start in range(0, len(normal_indices), 16_384):
        values = np.asarray(
            representation[normal_indices[start : start + 16_384]],
            dtype=np.float64,
        )
        total += values.sum(axis=0)
        total_square += np.square(values).sum(axis=0)
    mean = total / len(normal_indices)
    variance = np.maximum(
        (total_square - len(normal_indices) * np.square(mean)) / (len(normal_indices) - 1),
        1e-6,
    )
    return mean.astype(np.float32), variance.astype(np.float32)


def _raw_drift(
    representation: np.ndarray,
    source_anchor: np.ndarray,
    source_variance: np.ndarray,
) -> np.ndarray:
    result = np.empty(len(representation), dtype=np.float32)
    for start in range(0, len(representation), 16_384):
        values = np.asarray(representation[start : start + 16_384], dtype=np.float32)
        squared = np.square(values - source_anchor) / source_variance
        result[start : start + len(values)] = np.log1p(squared.sum(axis=1))
    return result


def _normalized_drift(raw: np.ndarray, contract: ControlContract) -> np.ndarray:
    return np.clip(
        (raw - contract.drift_median) / max(contract.drift_scale, 1e-6),
        0.0,
        contract.drift_maximum,
    ).astype(np.float32, copy=False)


def _source_attack_probabilities(
    representation: np.ndarray,
    scorer: nn.Module,
    device: torch.device,
) -> np.ndarray:
    result = np.empty(len(representation), dtype=np.float32)
    scorer.eval()
    with torch.no_grad():
        for start in range(0, len(representation), 16_384):
            values = torch.from_numpy(
                np.asarray(representation[start : start + 16_384], dtype=np.float32)
            ).to(device)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                logits = scorer(values).squeeze(-1)
            result[start : start + len(values)] = torch.sigmoid(logits).float().cpu().numpy()
    return result


def _trusted_quality(attack_probability: np.ndarray) -> np.ndarray:
    clipped = np.clip(attack_probability.astype(np.float64), 1e-7, 1.0 - 1e-7)
    entropy = -(clipped * np.log(clipped) + (1.0 - clipped) * np.log(1.0 - clipped))
    return ((1.0 - clipped) * np.exp(-entropy)).astype(np.float32)


def _phase_b_validation_diagnostics(
    model: PhaseBVariantModel,
    role: SequenceRole,
    representation: np.ndarray,
    batch_size: int,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    proposal_norms: list[np.ndarray] = []
    state_norms: list[np.ndarray] = []
    cumulative_values: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for _, _, values, valid, _ in _iter_representation_batches(
            role,
            representation,
            np.arange(role.sequence_count),
            batch_size,
        ):
            values = values.to(device)
            valid_device = valid.to(device)
            state = model.empty_state(values)
            cumulative = torch.zeros(values.shape[0], device=device)
            for index in range(values.shape[1]):
                current = values[:, index]
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    proposal = model.propose_step(current, state)
                delta_norm = torch.linalg.vector_norm((proposal - state).flatten(1), dim=1)
                state_norm = torch.linalg.vector_norm(proposal.flatten(1), dim=1)
                cumulative = 0.95 * cumulative + delta_norm
                active = valid_device[:, index]
                proposal_norms.append(delta_norm[active].float().cpu().numpy())
                state_norms.append(state_norm[active].float().cpu().numpy())
                cumulative_values.append(cumulative[active].float().cpu().numpy())
                state = torch.where(active.view(-1, 1, 1, 1), proposal, state)
    return (
        np.concatenate(proposal_norms),
        np.concatenate(state_norms),
        np.concatenate(cumulative_values),
    )


def _freeze_control_contract(
    model: PhaseBVariantModel,
    roles: Mapping[str, SequenceRole],
    representations: Mapping[str, np.ndarray],
    scorer: nn.Module,
    batch_size: int,
    device: torch.device,
) -> tuple[ControlContract, dict[str, Any]]:
    train_role = roles["source-train"]
    validation_role = roles["source-validation"]
    assert train_role.labels is not None and validation_role.labels is not None
    source_anchor, source_variance = _source_anchor_and_variance(
        representations["source-train"],
        train_role.labels,
    )
    validation_raw_drift = _raw_drift(
        representations["source-validation"],
        source_anchor,
        source_variance,
    )
    normal_mask = np.asarray(validation_role.labels) == 0
    normal_raw = validation_raw_drift[normal_mask]
    drift_median = float(np.median(normal_raw))
    q25, q75 = np.quantile(normal_raw, (0.25, 0.75))
    drift_scale = float(max(q75 - q25, 1e-6))
    normalized = np.clip((normal_raw - drift_median) / drift_scale, 0.0, None)
    drift_maximum = float(max(np.quantile(normalized, 0.999), 1.0))
    attack_probability = _source_attack_probabilities(
        representations["source-validation"], scorer, device
    )
    quality = _trusted_quality(attack_probability)
    normal_quality = quality[normal_mask]
    proposal_norms, state_norms, cumulative_values = _phase_b_validation_diagnostics(
        model,
        validation_role,
        representations["source-validation"],
        batch_size,
        device,
    )
    normal_values = np.asarray(
        representations["source-validation"][normal_mask], dtype=np.float32
    )
    reference_distances = np.linalg.norm(normal_values - source_anchor, axis=1)
    quality_window = int(np.clip(np.median(validation_role.lengths), 4, 32))
    block_rows = int(max(512, quality_window * 64))
    block_masses = np.array(
        [quality[start : start + block_rows].sum() for start in range(0, len(quality), block_rows)],
        dtype=np.float64,
    )
    block_mass_maximum = float(max(np.quantile(block_masses, 0.95), 1e-6))
    normalized_block_mass = np.clip(block_masses / block_mass_maximum, 0.0, 1.0)
    contract = ControlContract(
        source_anchor=source_anchor,
        source_variance=source_variance,
        drift_median=drift_median,
        drift_scale=drift_scale,
        drift_maximum=drift_maximum,
        enter_threshold=float(np.quantile(normalized, 0.75)),
        full_threshold=float(np.quantile(normalized, 0.95)),
        rollback_threshold=float(np.quantile(normalized, 0.999)),
        quality_threshold=float(np.quantile(normal_quality, 0.25)),
        step_budget=float(max(np.quantile(proposal_norms, 0.95), 1e-6)),
        cumulative_budget=float(max(np.quantile(cumulative_values, 0.99), 1e-6)),
        state_norm_maximum=float(max(np.quantile(state_norms, 0.999) * 1.05, 1e-6)),
        quality_window=quality_window,
        cumulative_decay=0.95,
        checkpoint_steps=max(3, quality_window // 2),
        new_normal_threshold=float(np.quantile(normalized, 0.95)),
        sample_weight_maximum=float(max(np.quantile(normal_quality, 0.95), 1e-6)),
        reference_step_budget=float(max(np.quantile(reference_distances, 0.50) * 0.10, 1e-6)),
        block_rows=block_rows,
        block_mass_maximum=block_mass_maximum,
        candidate_decay=0.95,
        stability_scale=float(max(np.quantile(reference_distances, 0.50), 1e-6)),
        evidence_threshold=float(np.quantile(normalized_block_mass, 0.25)),
        promotion_blocks=3,
        candidate_mass_minimum=block_mass_maximum * 3.0,
        reference_radius_maximum=float(max(np.quantile(reference_distances, 0.99), 1e-6)),
        promotion_step=0.10,
        promotion_maximum=0.30,
        rescue_weight=0.25,
    )
    receipt = {
        "schema_version": "c12-phase-b-source-frozen-control-contract-v1",
        "selection_roles": ["source-train", "source-validation"],
        "target_prefix_used_for_thresholds": False,
        "target_development_label_used": False,
        "diagonal_covariance_q0": True,
        "threshold_derivation": {
            "drift": "源验证正常漂移的75/95/99.9分位",
            "quality": "源验证正常可信质量25分位",
            "step_budget": "源验证门控Delta提议范数95分位",
            "cumulative_budget": "源验证衰减累计提议范数99分位",
            "state_norm_maximum": "源验证状态范数99.9分位乘1.05",
            "reference": "源验证正常参照距离和块质量分位",
        },
        "contract": contract.to_json(),
        "source_train_normal_rows": int(np.sum(train_role.labels == 0)),
        "source_validation_normal_rows": int(normal_mask.sum()),
        "final_accessed": False,
    }
    return contract, receipt


def _evaluate_phase_b_model(
    model: PhaseBVariantModel,
    role: SequenceRole,
    representation: np.ndarray,
    source_anchor: np.ndarray,
    batch_size: int,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    model.eval()
    labels_all: list[np.ndarray] = []
    probabilities_all: list[np.ndarray] = []
    sample_count = 0
    anchor = torch.from_numpy(source_anchor).to(device)
    started = time.perf_counter()
    with torch.no_grad():
        for _, _, values, valid, labels in _iter_representation_batches(
            role,
            representation,
            np.arange(role.sequence_count),
            batch_size,
        ):
            if labels is None:
                raise C12TrainError("阶段 B 源验证缺少标签")
            values = values.to(device)
            valid_device = valid.to(device)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                logits = model(values, valid_device, anchor)
            mask = valid.numpy()
            probabilities_all.append(torch.sigmoid(logits).float().cpu().numpy()[mask])
            labels_all.append(labels.numpy()[mask].astype(np.uint8))
            sample_count += int(mask.sum())
    torch.cuda.synchronize(device)
    seconds = time.perf_counter() - started
    return (
        np.concatenate(labels_all),
        np.concatenate(probabilities_all),
        seconds,
        sample_count / max(seconds, 1e-9),
    )


def train_variant(
    cache_root: Path,
    representation_root: Path,
    output_dir: Path,
    run_name: str,
    variant: str,
    batch_size: int,
    epochs: int,
    seed: int,
) -> dict[str, Any]:
    """第二阶段固定接收表示，只训练核、融合头或真实补偿头。"""
    if variant not in TRAINABLE_VARIANTS:
        raise C12TrainError(f"未知变体：{variant}")
    if output_dir.exists():
        raise C12TrainError("变体输出目录已存在，拒绝覆盖")
    output_dir.mkdir(parents=True)
    _seed_everything(seed)
    manifest, roles = load_cache(cache_root)
    representations, representation_receipt = _load_representations(cache_root, representation_root)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise C12TrainError("阶段 A 真实训练要求 CUDA")
    model_config = C12ModelConfig()
    models, raw_counts, matched_counts = build_parameter_matched_models(model_config)
    model = models[variant].to(device)
    train_role = roles["source-train"]
    validation_role = roles["source-validation"]
    assert train_role.labels is not None
    criterion = nn.BCEWithLogitsLoss()
    _, pool_receipt = _balanced_sequence_order(train_role, seed, 1, batch_size)
    pool_receipt.update(
        {
            "epochs": epochs,
            "fixed_budget_steps": int(pool_receipt["batches_per_epoch"]) * epochs,
            "malicious_draws_total": int(pool_receipt["malicious_draws_per_epoch"])
            * epochs,
            "all_benign_draws_total": int(pool_receipt["all_benign_draws_per_epoch"])
            * epochs,
            "loss": "unweighted BCEWithLogitsLoss；双池等量批次不以行级pos_weight替代",
            "final_accessed": False,
        }
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    config = _common_run_config(cache_root, manifest, model_config, seed, batch_size, epochs)
    config.update({
        "phase": "阶段 A 第二阶段公平基线",
        "variant": variant,
        "display_name": VARIANT_DISPLAY_NAMES[variant],
        "variant_role": VARIANT_ROLES[variant],
        "phase_a_kernel_matrix_member": variant in PHASE_A_VARIANTS,
        "receiver_frozen": True,
        "representation_manifest_sha256": _sha256(representation_root / "representation-manifest.json"),
        "raw_trainable_parameter_counts": raw_counts,
        "matched_trainable_parameter_counts": matched_counts,
        "trainable_parameter_ratio": max(matched_counts.values()) / min(matched_counts.values()),
        "kernel_equivalence_boundaries": kernel_equivalence_boundaries(),
        "target_prefix_adaptation": False,
        "target_development_label_read_during_training": False,
        "training_sequence_sampling": pool_receipt,
    })
    _write_json(output_dir / "config.json", config)
    _write_json(output_dir / "environment-receipt.json", _environment(device))
    _write_json(output_dir / "training-pool-receipt.json", pool_receipt)
    _write_json(output_dir / "dataset-receipt.json", {
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "representation_manifest_sha256": _sha256(representation_root / "representation-manifest.json"),
        "role_rows": {name: role.row_count for name, role in roles.items()},
        "role_sequences": {name: role.sequence_count for name, role in roles.items()},
        "target_prefix_used": False,
        "target_development_labels_used": False,
        "final_accessed": False,
    })
    _write_json(output_dir / "status.json", {"state": "running", "final_accessed": False})
    tracker: SwanTracker | None = None
    try:
        tracker = SwanTracker(output_dir, run_name, config)
        tracker.log({
            "data/source_train_rows": train_role.row_count,
            "data/source_train_sequences": train_role.sequence_count,
            "data/source_validation_rows": validation_role.row_count,
            "data/source_validation_sequences": validation_role.sequence_count,
            "data/target_development_rows_without_labels": roles["target-development"].row_count,
            "model/trainable_parameters": matched_counts[variant],
            "optimizer/learning_rate": optimizer.param_groups[0]["lr"],
        }, step=0)
        global_step = 0
        best_pr_auc = float("-inf")
        best_epoch = 0
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        for epoch in range(1, epochs + 1):
            model.train()
            order, epoch_pool_receipt = _balanced_sequence_order(
                train_role, seed, epoch, batch_size
            )
            if epoch_pool_receipt["every_batch_equal_pool_counts"] is not True:
                raise C12TrainError(f"{variant} 训练批次未满足双池等量合同")
            epoch_loss = 0.0
            epoch_rows = 0
            epoch_started = time.perf_counter()
            for offset, _, values, valid, labels in _iter_representation_batches(
                train_role,
                representations["source-train"],
                order,
                batch_size,
            ):
                assert labels is not None
                values = values.to(device, non_blocking=True)
                valid = valid.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits = model(values, valid)
                    loss = criterion(logits[valid], labels[valid])
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                global_step += 1
                rows = int(valid.sum().item())
                epoch_rows += rows
                epoch_loss += float(loss.detach().cpu()) * rows
                elapsed = time.perf_counter() - epoch_started
                if global_step == 1 or global_step % LOG_INTERVAL_STEPS == 0:
                    tracker.log({
                        "train/loss": float(loss.detach().cpu()),
                        "optimizer/learning_rate": optimizer.param_groups[0]["lr"],
                        "runtime/train_rows_per_second": epoch_rows / max(elapsed, 1e-9),
                        "runtime/peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
                    }, step=global_step)
                    print(
                        f"阶段A进度：变体={variant}（{VARIANT_DISPLAY_NAMES[variant]}） "
                        f"轮次={epoch}/{epochs} 步={global_step} 序列偏移={offset}/{len(order)} "
                        f"行吞吐={epoch_rows / max(elapsed, 1e-9):.1f}/秒",
                        flush=True,
                    )
                if global_step % CHECKPOINT_INTERVAL_STEPS == 0:
                    _save_checkpoint(output_dir / "checkpoints/latest.pt", {
                        "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                        "scheduler": scheduler.state_dict(), "variant": variant,
                        "epoch": epoch, "next_sequence_offset": offset + batch_size,
                        "global_step": global_step, "best_pr_auc": best_pr_auc, "seed": seed,
                    })
            scheduler.step()
            labels_np, probabilities, inference_seconds, throughput = _evaluate_model(
                model,
                _iter_representation_batches(
                    validation_role,
                    representations["source-validation"],
                    np.arange(validation_role.sequence_count),
                    batch_size,
                ),
                device,
            )
            threshold_receipt = _freeze_threshold(labels_np, probabilities)
            metrics = _binary_metrics(labels_np, probabilities, float(threshold_receipt["threshold"]))
            record = {
                "epoch": epoch,
                "global_step": global_step,
                "train_loss": epoch_loss / max(epoch_rows, 1),
                "validation": metrics,
                "validation_inference_seconds": inference_seconds,
                "validation_rows_per_second": throughput,
                "learning_rate": optimizer.param_groups[0]["lr"],
                "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            }
            _append_jsonl(output_dir / "training-history.jsonl", record)
            tracker.log({
                "validation/pr_auc": metrics["pr_auc"],
                "validation/macro_f1": metrics["macro_f1"],
                "validation/malicious_f1": metrics["malicious_f1"],
                "runtime/validation_rows_per_second": throughput,
                "runtime/peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            }, step=global_step)
            if metrics["pr_auc"] > best_pr_auc:
                best_pr_auc = float(metrics["pr_auc"])
                best_epoch = epoch
                _save_checkpoint(output_dir / "checkpoints/best.pt", {
                    "model": model.state_dict(), "variant": variant,
                    "epoch": epoch, "global_step": global_step,
                    "validation_pr_auc": best_pr_auc, "threshold_receipt": threshold_receipt,
                    "validation_metrics": metrics, "seed": seed,
                    "model_config": model_config.to_dict(),
                })
                _write_json(output_dir / "threshold-receipt.json", threshold_receipt)
                _write_json(output_dir / "metrics/source-validation.json", metrics)
                _seal_source_validation_predictions(
                    output_dir,
                    validation_role,
                    probabilities,
                    threshold_receipt,
                )
        best_checkpoint_path = output_dir / "checkpoints/best.pt"
        best_checkpoint = torch.load(best_checkpoint_path, map_location="cpu", weights_only=False)
        model.load_state_dict(best_checkpoint["model"])
        prediction_path, prediction_receipt = _predict_target_development(
            model,
            roles["target-development"],
            representations["target-development"],
            output_dir,
            batch_size,
            device,
            variant,
        )
        total_seconds = time.perf_counter() - started
        prediction_details = _load_json(prediction_receipt)
        receiver_parameter_count = trainable_parameter_count(
            ReceiverSourceScorer(model_config).receiver
        )
        resource_usage = {
            "schema_version": "c12-phase-a-resource-usage-v1",
            "variant": variant,
            "trainable_variant_parameters": matched_counts[variant],
            "frozen_receiver_parameters": receiver_parameter_count,
            "total_resident_parameters": receiver_parameter_count + matched_counts[variant],
            "training_and_prediction_seconds": total_seconds,
            "target_prediction_seconds": prediction_details["prediction_seconds"],
            "target_prediction_rows_per_second": prediction_details["prediction_rows_per_second"],
            "mean_sequence_latency_seconds": prediction_details["mean_sequence_latency_seconds"],
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "single_gpu_serial_measurement": True,
            "final_accessed": False,
        }
        _write_json(output_dir / "resource-usage.json", resource_usage)
        summary = {
            "schema_version": RUN_SCHEMA,
            "state": "predictions_sealed_evaluation_pending",
            "variant": variant,
            "display_name": VARIANT_DISPLAY_NAMES[variant],
            "variant_role": VARIANT_ROLES[variant],
            "best_epoch": best_epoch,
            "best_validation_pr_auc": best_pr_auc,
            "fixed_budget_steps": global_step,
            "training_and_prediction_seconds": total_seconds,
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "target_prediction_rows_per_second": prediction_details["prediction_rows_per_second"],
            "prediction_path": str(prediction_path),
            "prediction_receipt_sha256": _sha256(prediction_receipt),
            "representation_source": representation_receipt["schema_version"],
            "target_prefix_used": False,
            "target_development_labels_used": False,
            "final_accessed": False,
        }
        tracker.finish()
        summary["swanlab"] = tracker.status
        _write_json(output_dir / "summary.json", summary)
        _write_json(output_dir / "status.json", {
            "state": "predictions_sealed_evaluation_pending",
            "variant": variant,
            "final_accessed": False,
        })
        _write_artifact_manifest(output_dir)
        return summary
    except BaseException as error:
        if tracker is not None:
            tracker.fail(error)
            _write_json(output_dir / "swanlab-status.json", tracker.status)
        _write_json(output_dir / "status.json", {
            "state": "failed", "variant": variant,
            "error_type": type(error).__name__, "error": str(error),
            "final_accessed": False,
        })
        raise


def _flush_reference_block(
    reference: dict[str, Any],
    contract: ControlContract,
) -> None:
    if reference["block_rows"] == 0:
        return
    effective_mass = float(reference["block_effective_mass"])
    capped_mass = min(contract.block_mass_maximum, effective_mass)
    if effective_mass > 0.0:
        center = reference["block_weighted_sum"] / effective_mass
    else:
        center = reference["candidate"].copy()
    previous = reference["candidate"].copy()
    reference["accumulator"] = (
        contract.candidate_decay * reference["accumulator"] + capped_mass * center
    )
    reference["mass"] = contract.candidate_decay * reference["mass"] + capped_mass
    candidate = reference["accumulator"] / max(reference["mass"], 1e-9)
    change = float(np.linalg.norm(candidate - previous))
    raw_mass = float(reference["block_raw_mass"])
    clip_ratio = 1.0 - effective_mass / max(raw_mass, 1e-9)
    evidence = (
        capped_mass
        / contract.block_mass_maximum
        * np.exp(-change / contract.stability_scale)
        * max(0.0, 1.0 - clip_ratio)
        * (1.0 if reference["block_rollbacks"] == 0 else 0.0)
    )
    reference["evidence_history"].append(float(evidence))
    distance = float(np.linalg.norm(candidate - contract.source_anchor))
    if distance > contract.reference_radius_maximum or reference["block_rollbacks"] > 0:
        action = "拒绝"
        reference["accumulator"] = contract.source_anchor.astype(np.float64).copy()
        reference["mass"] = 1.0
        reference["candidate"] = contract.source_anchor.copy()
        reference["checkpoint"] = contract.source_anchor.copy()
        reference["pi"] = 0.0
        reference["rejections"] += 1
    elif (
        reference["mass"] >= contract.candidate_mass_minimum
        and len(reference["evidence_history"]) >= contract.promotion_blocks
        and all(
            value >= contract.evidence_threshold
            for value in reference["evidence_history"][-contract.promotion_blocks :]
        )
    ):
        action = "晋升"
        reference["candidate"] = candidate.astype(np.float32)
        reference["checkpoint"] = reference["candidate"].copy()
        reference["pi"] = min(
            float(reference["pi"]) + contract.promotion_step,
            contract.promotion_maximum,
        )
        reference["promotions"] += 1
    else:
        action = "保留"
        reference["candidate"] = candidate.astype(np.float32)
        reference["retentions"] += 1
    reference["active"] = (
        (1.0 - reference["pi"]) * contract.source_anchor
        + reference["pi"] * reference["checkpoint"]
    ).astype(np.float32)
    reference["events"].append(
        {
            "block_index": len(reference["events"]),
            "rows": int(reference["block_rows"]),
            "raw_mass": raw_mass,
            "effective_mass": effective_mass,
            "capped_mass": capped_mass,
            "clip_ratio": float(np.clip(clip_ratio, 0.0, 1.0)),
            "rollback_count": int(reference["block_rollbacks"]),
            "evidence": float(evidence),
            "candidate_source_distance": distance,
            "action": action,
            "promotion_coefficient": float(reference["pi"]),
        }
    )
    reference["block_weighted_sum"].fill(0.0)
    reference["block_raw_mass"] = 0.0
    reference["block_effective_mass"] = 0.0
    reference["block_rows"] = 0
    reference["block_rollbacks"] = 0


def _new_reference_state(contract: ControlContract) -> dict[str, Any]:
    return {
        "accumulator": contract.source_anchor.astype(np.float64).copy(),
        "mass": 1.0,
        "candidate": contract.source_anchor.copy(),
        "checkpoint": contract.source_anchor.copy(),
        "active": contract.source_anchor.copy(),
        "pi": 0.0,
        "evidence_history": [],
        "events": [],
        "promotions": 0,
        "retentions": 0,
        "rejections": 0,
        "block_weighted_sum": np.zeros_like(contract.source_anchor, dtype=np.float64),
        "block_raw_mass": 0.0,
        "block_effective_mass": 0.0,
        "block_rows": 0,
        "block_rollbacks": 0,
    }


def _run_phase_b_role(
    model: PhaseBVariantModel,
    scorer: nn.Module,
    role: SequenceRole,
    representation: np.ndarray,
    contract: ControlContract,
    variant: str,
    batch_size: int,
    device: torch.device,
    initial_quality: float,
    reference: dict[str, Any],
    update_reference: bool,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, Any]]:
    use_control = variant in ("C12-CTRL", "C12-FULL")
    use_reference = variant in ("C12-DREF", "C12-FULL")
    probabilities = np.empty(role.row_count, dtype=np.float32)
    filled = np.zeros(role.row_count, dtype=bool)
    diagnostics = {
        "drift": np.empty(role.row_count, dtype=np.float32),
        "quality": np.empty(role.row_count, dtype=np.float32),
        "proposal_norm": np.empty(role.row_count, dtype=np.float32),
        "applied_norm": np.empty(role.row_count, dtype=np.float32),
        "cumulative_impact": np.empty(role.row_count, dtype=np.float32),
        "action": np.empty(role.row_count, dtype=np.uint8),
        "reference_distance": np.empty(role.row_count, dtype=np.float32),
        "promotion_coefficient": np.empty(role.row_count, dtype=np.float32),
    }
    quality_total = 0.0
    quality_rows = 0
    action_counts = {"接受": 0, "冻结": 0, "回退": 0}
    source_anchor_tensor = torch.from_numpy(contract.source_anchor).to(device)
    source_variance_tensor = torch.from_numpy(contract.source_variance).to(device)
    model.eval()
    scorer.eval()
    started = time.perf_counter()
    with torch.no_grad():
        for _, indices, values, valid, _ in _iter_representation_batches(
            role,
            representation,
            np.arange(role.sequence_count),
            batch_size,
        ):
            values = values.to(device)
            valid_device = valid.to(device)
            state = model.empty_state(values)
            checkpoint = state.clone()
            cumulative = torch.zeros(values.shape[0], device=device)
            quality_sum = torch.full(
                (values.shape[0],),
                initial_quality * contract.quality_window,
                device=device,
            )
            quality_count = torch.full(
                (values.shape[0],),
                float(contract.quality_window),
                device=device,
            )
            safe_steps = torch.zeros(values.shape[0], device=device, dtype=torch.int64)
            active_reference_np = (
                reference["active"] if use_reference else contract.source_anchor
            )
            active_reference = torch.from_numpy(active_reference_np).to(device)
            for index in range(values.shape[1]):
                current = values[:, index]
                active = valid_device[:, index]
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits, _ = model.predict_step(current, state, active_reference)
                    proposal = model.propose_step(current, state)
                    source_logits = scorer(current).squeeze(-1)
                attack_probability = torch.sigmoid(source_logits.float())
                clipped_probability = attack_probability.clamp(1e-7, 1.0 - 1e-7)
                entropy = -(
                    clipped_probability * torch.log(clipped_probability)
                    + (1.0 - clipped_probability) * torch.log(1.0 - clipped_probability)
                )
                quality = (1.0 - clipped_probability) * torch.exp(-entropy)
                raw_drift = torch.log1p(
                    (
                        (current.float() - source_anchor_tensor) ** 2
                        / source_variance_tensor
                    ).sum(dim=1)
                )
                drift = torch.clamp(
                    (raw_drift - contract.drift_median) / max(contract.drift_scale, 1e-6),
                    0.0,
                    contract.drift_maximum,
                )
                delta = proposal - state
                proposal_norm = torch.linalg.vector_norm(delta.flatten(1), dim=1)
                proposal_state_norm = torch.linalg.vector_norm(proposal.flatten(1), dim=1)
                violation = (~torch.isfinite(proposal.flatten(1)).all(dim=1)) | (
                    proposal_state_norm > contract.state_norm_maximum
                )
                if use_control:
                    quality_sum = quality_sum + torch.where(active, quality, torch.zeros_like(quality))
                    quality_count = quality_count + active.float()
                    rolling_quality = quality_sum / quality_count.clamp_min(1.0)
                    middle = torch.clamp(
                        (drift - contract.enter_threshold)
                        / max(contract.full_threshold - contract.enter_threshold, 1e-6),
                        0.0,
                        1.0,
                    )
                    activation = torch.where(
                        (drift >= contract.enter_threshold)
                        & (drift < contract.rollback_threshold),
                        middle,
                        torch.zeros_like(middle),
                    )
                    step_budget = contract.step_budget * activation * (
                        rolling_quality >= contract.quality_threshold
                    ).float()
                    scale = torch.minimum(
                        torch.ones_like(step_budget),
                        step_budget / proposal_norm.clamp_min(1e-9),
                    )
                    bounded_delta = delta * scale.view(-1, 1, 1, 1)
                    applied_norm = torch.linalg.vector_norm(bounded_delta.flatten(1), dim=1)
                    proposed_cumulative = contract.cumulative_decay * cumulative + applied_norm
                    cumulative_budget = contract.cumulative_budget * activation * (
                        rolling_quality >= contract.quality_threshold
                    ).float()
                    rollback = active & (
                        (drift >= contract.rollback_threshold) | violation
                    )
                    accept = active & (~rollback) & (step_budget > 0.0) & (
                        proposed_cumulative <= cumulative_budget
                    )
                    freeze = active & (~rollback) & (~accept)
                    accepted_state = state + bounded_delta
                    state = torch.where(
                        rollback.view(-1, 1, 1, 1),
                        checkpoint,
                        torch.where(accept.view(-1, 1, 1, 1), accepted_state, state),
                    )
                    cumulative = torch.where(
                        rollback,
                        torch.zeros_like(cumulative),
                        torch.where(
                            accept,
                            proposed_cumulative,
                            contract.cumulative_decay * cumulative,
                        ),
                    )
                    safe_steps = torch.where(
                        accept & (~violation) & (rolling_quality >= contract.quality_threshold),
                        safe_steps + 1,
                        torch.zeros_like(safe_steps),
                    )
                    update_checkpoint = safe_steps >= contract.checkpoint_steps
                    checkpoint = torch.where(
                        update_checkpoint.view(-1, 1, 1, 1), state, checkpoint
                    )
                    action = torch.where(
                        rollback,
                        torch.full_like(safe_steps, 2, dtype=torch.uint8),
                        torch.where(
                            accept,
                            torch.ones_like(safe_steps, dtype=torch.uint8),
                            torch.zeros_like(safe_steps, dtype=torch.uint8),
                        ),
                    )
                    applied = torch.where(accept, applied_norm, torch.zeros_like(applied_norm))
                else:
                    rolling_quality = quality
                    state = torch.where(active.view(-1, 1, 1, 1), proposal, state)
                    cumulative = torch.where(
                        active,
                        contract.cumulative_decay * cumulative + proposal_norm,
                        cumulative,
                    )
                    action = torch.where(
                        active,
                        torch.ones_like(active, dtype=torch.uint8),
                        torch.zeros_like(active, dtype=torch.uint8),
                    )
                    applied = torch.where(active, proposal_norm, torch.zeros_like(proposal_norm))
                    rollback = torch.zeros_like(active)
                active_np = active.cpu().numpy()
                if not active_np.any():
                    continue
                batch_positions = np.flatnonzero(active_np)
                rows = np.array(
                    [int(role.starts[indices[item]]) + index for item in batch_positions],
                    dtype=np.int64,
                )
                probability_np = torch.sigmoid(logits).float().cpu().numpy()[active_np]
                drift_np = drift.float().cpu().numpy()[active_np]
                quality_np = rolling_quality.float().cpu().numpy()[active_np]
                proposal_np = proposal_norm.float().cpu().numpy()[active_np]
                applied_np = applied.float().cpu().numpy()[active_np]
                cumulative_np = cumulative.float().cpu().numpy()[active_np]
                action_np = action.cpu().numpy()[active_np]
                current_np = current.float().cpu().numpy()[active_np]
                probabilities[rows] = probability_np
                diagnostics["drift"][rows] = drift_np
                diagnostics["quality"][rows] = quality_np
                diagnostics["proposal_norm"][rows] = proposal_np
                diagnostics["applied_norm"][rows] = applied_np
                diagnostics["cumulative_impact"][rows] = cumulative_np
                diagnostics["action"][rows] = action_np
                diagnostics["reference_distance"][rows] = np.linalg.norm(
                    current_np - active_reference_np, axis=1
                )
                diagnostics["promotion_coefficient"][rows] = float(reference["pi"])
                filled[rows] = True
                quality_total += float(quality_np.sum())
                quality_rows += len(rows)
                action_counts["接受"] += int(np.sum(action_np == 1))
                action_counts["冻结"] += int(np.sum(action_np == 0))
                action_counts["回退"] += int(np.sum(action_np == 2))
                if update_reference and use_reference:
                    attack_np = attack_probability.float().cpu().numpy()[active_np]
                    entropy_np = entropy.float().cpu().numpy()[active_np]
                    source_quality_np = _trusted_quality(attack_np)
                    rescue = (
                        attack_np
                        * np.exp(-entropy_np)
                        * (drift_np >= contract.new_normal_threshold)
                    )
                    raw_weight = np.minimum(
                        contract.sample_weight_maximum,
                        source_quality_np + contract.rescue_weight * rescue,
                    )
                    candidate_distance = np.linalg.norm(
                        current_np - reference["candidate"], axis=1
                    )
                    influence = np.minimum(
                        1.0,
                        contract.reference_step_budget / np.maximum(candidate_distance, 1e-9),
                    )
                    weight = raw_weight * influence
                    reference["block_weighted_sum"] += (
                        weight[:, None] * current_np
                    ).sum(axis=0)
                    reference["block_raw_mass"] += float(raw_weight.sum())
                    reference["block_effective_mass"] += float(weight.sum())
                    reference["block_rows"] += len(rows)
                    reference["block_rollbacks"] += int(rollback[active].sum().item())
                    if reference["block_rows"] >= contract.block_rows:
                        _flush_reference_block(reference, contract)
                        active_reference_np = reference["active"]
                        active_reference = torch.from_numpy(active_reference_np).to(device)
    if update_reference and use_reference:
        _flush_reference_block(reference, contract)
    if not filled.all() or not np.isfinite(probabilities).all():
        raise C12TrainError(f"{role.role} 阶段 B 概率或诊断未完整封存")
    summary = {
        "role": role.role,
        "rows": role.row_count,
        "sequences": role.sequence_count,
        "mean_quality": quality_total / max(quality_rows, 1),
        "action_counts": action_counts,
        "reference_promotions": int(reference["promotions"]),
        "reference_retentions": int(reference["retentions"]),
        "reference_rejections": int(reference["rejections"]),
        "final_promotion_coefficient": float(reference["pi"]),
        "seconds": time.perf_counter() - started,
        "labels_read": False,
        "prediction_update_order": "当前位置概率先封存，再执行状态与参照更新",
        "final_accessed": False,
    }
    return probabilities, diagnostics, summary


def _seal_phase_b_role(
    output_dir: Path,
    role: SequenceRole,
    role_name: str,
    probabilities: np.ndarray,
    diagnostics: Mapping[str, np.ndarray],
    variant: str,
    summary: Mapping[str, Any],
) -> tuple[Path, Path]:
    predictions_dir = output_dir / "predictions"
    diagnostics_dir = output_dir / "diagnostics"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = predictions_dir / f"{role_name}.npz"
    prediction_partial = prediction_path.with_suffix(f".npz.partial.{os.getpid()}")
    with prediction_partial.open("wb") as handle:
        np.savez_compressed(
            handle,
            probability=probabilities,
            sample_id=np.asarray(role.sample_id),
            sequence_id=np.asarray(role.sequence_id),
            position=np.asarray(role.position),
            valid_length=np.asarray(role.valid_length),
        )
    os.replace(prediction_partial, prediction_path)
    diagnostic_path = diagnostics_dir / f"{role_name}-state-control.npz"
    diagnostic_partial = diagnostic_path.with_suffix(f".npz.partial.{os.getpid()}")
    with diagnostic_partial.open("wb") as handle:
        np.savez_compressed(
            handle,
            sample_id=np.asarray(role.sample_id),
            sequence_id=np.asarray(role.sequence_id),
            position=np.asarray(role.position),
            **diagnostics,
        )
    os.replace(diagnostic_partial, diagnostic_path)
    receipt_path = predictions_dir / f"{role_name}-receipt.json"
    _write_json(
        receipt_path,
        {
            "schema_version": "c12-target-development-predictions-v1"
            if role_name == "target-development"
            else "c12-target-prefix-predictions-v1",
            "variant": variant,
            "role": role_name,
            "row_count": role.row_count,
            "sequence_count": role.sequence_count,
            "prediction_sha256": _sha256(prediction_path),
            "diagnostic_sha256": _sha256(diagnostic_path),
            "summary": dict(summary),
            "labels_connected": False,
            "target_prefix_used": True,
            "final_accessed": False,
        },
    )
    return prediction_path, receipt_path


def train_phase_b_variant(
    cache_root: Path,
    representation_root: Path,
    target_prefix_representation_root: Path,
    receiver_checkpoint: Path,
    output_dir: Path,
    run_name: str,
    variant: str,
    batch_size: int,
    epochs: int,
    seed: int,
    resource_measurement_mode: str,
) -> dict[str, Any]:
    """训练阶段 B 变体，并按无标签前缀适应后封存目标开发概率。"""
    if variant not in PHASE_B_VARIANTS:
        raise C12TrainError(f"未知阶段 B 变体：{variant}")
    if resource_measurement_mode not in {"isolated", "concurrent"}:
        raise C12TrainError(
            f"未知资源测量模式：{resource_measurement_mode}"
        )
    if output_dir.exists():
        raise C12TrainError("阶段 B 变体输出目录已存在，拒绝覆盖")
    output_dir.mkdir(parents=True)
    _seed_everything(seed)
    manifest, roles = load_cache(cache_root)
    representations, representation_receipt = _load_representations(
        cache_root, representation_root
    )
    target_prefix_representation, target_prefix_receipt = (
        _load_target_prefix_representation(cache_root, target_prefix_representation_root)
    )
    receiver_checkpoint_sha256 = _sha256(receiver_checkpoint)
    if (
        target_prefix_receipt.get("receiver_checkpoint_sha256")
        != receiver_checkpoint_sha256
        or representation_receipt.get("receiver_checkpoint_sha256")
        != receiver_checkpoint_sha256
    ):
        raise C12TrainError("目标前缀与源角色冻结表示未使用同一接收器")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise C12TrainError("阶段 B 真实训练要求 CUDA")
    model_config = C12ModelConfig()
    models, raw_counts, matched_counts = build_phase_b_parameter_matched_models(model_config)
    model = models[variant].to(device)
    receiver_model = ReceiverSourceScorer(model_config).to(device)
    receiver_payload = torch.load(receiver_checkpoint, map_location="cpu", weights_only=False)
    receiver_model.load_state_dict(receiver_payload["model"])
    receiver_model.eval()
    scorer = receiver_model.classifier
    for parameter in scorer.parameters():
        parameter.requires_grad_(False)
    train_role = roles["source-train"]
    validation_role = roles["source-validation"]
    assert train_role.labels is not None and validation_role.labels is not None
    source_anchor, _ = _source_anchor_and_variance(
        representations["source-train"], train_role.labels
    )
    anchor_tensor = torch.from_numpy(source_anchor).to(device)
    criterion = nn.BCEWithLogitsLoss()
    _, pool_receipt = _balanced_sequence_order(train_role, seed, 1, batch_size)
    pool_receipt.update(
        {
            "epochs": epochs,
            "fixed_budget_steps": int(pool_receipt["batches_per_epoch"]) * epochs,
            "malicious_draws_total": int(pool_receipt["malicious_draws_per_epoch"])
            * epochs,
            "all_benign_draws_total": int(pool_receipt["all_benign_draws_per_epoch"])
            * epochs,
            "loss": "unweighted BCEWithLogitsLoss；双池等量批次不以行级pos_weight替代",
            "final_accessed": False,
        }
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    config = _common_run_config(
        cache_root, manifest, model_config, seed, batch_size, epochs
    )
    config.update(
        {
            "schema_version": PHASE_B_RUN_SCHEMA,
            "phase": "阶段 B 两个主机制",
            "variant": variant,
            "display_name": VARIANT_DISPLAY_NAMES[variant],
            "variant_role": VARIANT_ROLES[variant],
            "carrier_kernel": "门控 DeltaNet 更新核的纯 PyTorch 顺序参考实现",
            "receiver_frozen": True,
            "source_scorer_frozen": True,
            "representation_manifest_sha256": _sha256(
                representation_root / "representation-manifest.json"
            ),
            "target_prefix_representation_manifest_sha256": _sha256(
                target_prefix_representation_root
                / "target-prefix-representation-manifest.json"
            ),
            "raw_trainable_parameter_counts": raw_counts,
            "matched_trainable_parameter_counts": matched_counts,
            "phase_a_frozen_parameter_budget": matched_counts[variant],
            "target_prefix_adaptation": True,
            "target_prefix_labels_available": False,
            "target_development_label_read_during_training": False,
            "control_threshold_roles": ["source-train", "source-validation"],
            "training_sequence_sampling": pool_receipt,
            "resource_measurement_mode": resource_measurement_mode,
            "single_process_efficiency_metrics_valid": (
                resource_measurement_mode == "isolated"
            ),
        }
    )
    _write_json(output_dir / "config.json", config)
    _write_json(output_dir / "environment-receipt.json", _environment(device))
    _write_json(output_dir / "training-pool-receipt.json", pool_receipt)
    _write_json(
        output_dir / "dataset-receipt.json",
        {
            "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
            "representation_manifest_sha256": _sha256(
                representation_root / "representation-manifest.json"
            ),
            "target_prefix_representation_manifest_sha256": _sha256(
                target_prefix_representation_root
                / "target-prefix-representation-manifest.json"
            ),
            "role_rows": {name: role.row_count for name, role in roles.items()},
            "role_sequences": {name: role.sequence_count for name, role in roles.items()},
            "target_prefix_labels_used": False,
            "target_development_labels_used": False,
            "final_accessed": False,
        },
    )
    _write_json(
        output_dir / "status.json",
        {"state": "running", "variant": variant, "final_accessed": False},
    )
    tracker: SwanTracker | None = None
    try:
        tracker = SwanTracker(output_dir, run_name, config, phase="phase-b")
        tracker.log(
            {
                "data/source_train_rows": train_role.row_count,
                "data/source_validation_rows": validation_role.row_count,
                "data/target_prefix_rows_without_labels": roles["target-prefix"].row_count,
                "data/target_development_rows_without_labels": roles[
                    "target-development"
                ].row_count,
                "model/trainable_parameters": matched_counts[variant],
                "optimizer/learning_rate": optimizer.param_groups[0]["lr"],
            },
            step=0,
        )
        global_step = 0
        best_pr_auc = float("-inf")
        best_epoch = 0
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        for epoch in range(1, epochs + 1):
            model.train()
            order, epoch_pool_receipt = _balanced_sequence_order(
                train_role, seed, epoch, batch_size
            )
            if epoch_pool_receipt["every_batch_equal_pool_counts"] is not True:
                raise C12TrainError(f"{variant} 训练批次未满足双池等量合同")
            epoch_loss = 0.0
            epoch_rows = 0
            epoch_started = time.perf_counter()
            for offset, _, values, valid, labels in _iter_representation_batches(
                train_role,
                representations["source-train"],
                order,
                batch_size,
            ):
                assert labels is not None
                values = values.to(device, non_blocking=True)
                valid = valid.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits = model(values, valid, anchor_tensor)
                    loss = criterion(logits[valid], labels[valid])
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                global_step += 1
                rows = int(valid.sum().item())
                epoch_rows += rows
                epoch_loss += float(loss.detach().cpu()) * rows
                elapsed = time.perf_counter() - epoch_started
                if global_step == 1 or global_step % LOG_INTERVAL_STEPS == 0:
                    tracker.log(
                        {
                            "train/loss": float(loss.detach().cpu()),
                            "optimizer/learning_rate": optimizer.param_groups[0]["lr"],
                            "runtime/train_rows_per_second": epoch_rows
                            / max(elapsed, 1e-9),
                            "runtime/peak_gpu_memory_bytes": int(
                                torch.cuda.max_memory_allocated(device)
                            ),
                        },
                        step=global_step,
                    )
                    print(
                        f"阶段B进度：变体={variant}（{VARIANT_DISPLAY_NAMES[variant]}） "
                        f"轮次={epoch}/{epochs} 步={global_step} "
                        f"序列偏移={offset}/{len(order)} "
                        f"行吞吐={epoch_rows / max(elapsed, 1e-9):.1f}/秒",
                        flush=True,
                    )
                if global_step % CHECKPOINT_INTERVAL_STEPS == 0:
                    _save_checkpoint(
                        output_dir / "checkpoints/latest.pt",
                        {
                            "model": model.state_dict(),
                            "optimizer": optimizer.state_dict(),
                            "scheduler": scheduler.state_dict(),
                            "variant": variant,
                            "epoch": epoch,
                            "next_sequence_offset": offset + batch_size,
                            "global_step": global_step,
                            "best_pr_auc": best_pr_auc,
                            "seed": seed,
                        },
                    )
            scheduler.step()
            labels_np, validation_probability, inference_seconds, throughput = (
                _evaluate_phase_b_model(
                    model,
                    validation_role,
                    representations["source-validation"],
                    source_anchor,
                    batch_size,
                    device,
                )
            )
            threshold_receipt = _freeze_threshold(labels_np, validation_probability)
            metrics = _binary_metrics(
                labels_np,
                validation_probability,
                float(threshold_receipt["threshold"]),
            )
            _append_jsonl(
                output_dir / "training-history.jsonl",
                {
                    "epoch": epoch,
                    "global_step": global_step,
                    "train_loss": epoch_loss / max(epoch_rows, 1),
                    "validation": metrics,
                    "validation_inference_seconds": inference_seconds,
                    "validation_rows_per_second": throughput,
                    "learning_rate": optimizer.param_groups[0]["lr"],
                    "peak_gpu_memory_bytes": int(
                        torch.cuda.max_memory_allocated(device)
                    ),
                },
            )
            tracker.log(
                {
                    "validation/pr_auc": metrics["pr_auc"],
                    "validation/macro_f1": metrics["macro_f1"],
                    "validation/malicious_f1": metrics["malicious_f1"],
                    "runtime/validation_rows_per_second": throughput,
                    "runtime/peak_gpu_memory_bytes": int(
                        torch.cuda.max_memory_allocated(device)
                    ),
                },
                step=global_step,
            )
            if metrics["pr_auc"] > best_pr_auc:
                best_pr_auc = float(metrics["pr_auc"])
                best_epoch = epoch
                _save_checkpoint(
                    output_dir / "checkpoints/best.pt",
                    {
                        "model": model.state_dict(),
                        "variant": variant,
                        "epoch": epoch,
                        "global_step": global_step,
                        "validation_pr_auc": best_pr_auc,
                        "threshold_receipt": threshold_receipt,
                        "validation_metrics": metrics,
                        "seed": seed,
                        "model_config": model_config.to_dict(),
                    },
                )
                _write_json(output_dir / "threshold-receipt.json", threshold_receipt)
                _write_json(output_dir / "metrics/source-validation.json", metrics)
                _seal_source_validation_predictions(
                    output_dir,
                    validation_role,
                    validation_probability,
                    threshold_receipt,
                )
        best_checkpoint = torch.load(
            output_dir / "checkpoints/best.pt", map_location="cpu", weights_only=False
        )
        model.load_state_dict(best_checkpoint["model"])
        control_contract, control_receipt = _freeze_control_contract(
            model,
            roles,
            representations,
            scorer,
            batch_size,
            device,
        )
        _write_json(output_dir / "source-frozen-control-contract.json", control_receipt)
        reference = _new_reference_state(control_contract)
        prefix_probability, prefix_diagnostics, prefix_summary = _run_phase_b_role(
            model,
            scorer,
            roles["target-prefix"],
            target_prefix_representation,
            control_contract,
            variant,
            batch_size,
            device,
            control_contract.quality_threshold,
            reference,
            update_reference=True,
        )
        _, prefix_receipt_path = _seal_phase_b_role(
            output_dir,
            roles["target-prefix"],
            "target-prefix",
            prefix_probability,
            prefix_diagnostics,
            variant,
            prefix_summary,
        )
        _write_json(
            output_dir / "diagnostics/dual-reference.json",
            {
                "schema_version": "c12-phase-b-dual-reference-v1",
                "variant": variant,
                "events": reference["events"],
                "promotions": reference["promotions"],
                "retentions": reference["retentions"],
                "rejections": reference["rejections"],
                "final_promotion_coefficient": reference["pi"],
                "source_anchor_unchanged": True,
                "target_prefix_labels_used": False,
                "final_accessed": False,
            },
        )
        frozen_reference = reference["active"].copy()
        prefix_quality_prior = float(prefix_summary["mean_quality"])
        target_probability, target_diagnostics, target_summary = _run_phase_b_role(
            model,
            scorer,
            roles["target-development"],
            representations["target-development"],
            control_contract,
            variant,
            batch_size,
            device,
            prefix_quality_prior,
            reference,
            update_reference=False,
        )
        if not np.array_equal(frozen_reference, reference["active"]):
            raise C12TrainError("目标开发期间全局激活参照发生改写")
        prediction_path, prediction_receipt = _seal_phase_b_role(
            output_dir,
            roles["target-development"],
            "target-development",
            target_probability,
            target_diagnostics,
            variant,
            target_summary,
        )
        total_seconds = time.perf_counter() - started
        tracker.log(
            {
                "adaptation/prefix_mean_quality": prefix_quality_prior,
                "adaptation/reference_promotions": reference["promotions"],
                "adaptation/reference_rejections": reference["rejections"],
                "adaptation/final_promotion_coefficient": reference["pi"],
                "runtime/peak_gpu_memory_bytes": int(
                    torch.cuda.max_memory_allocated(device)
                ),
            },
            step=global_step + 1,
        )
        resource_usage = {
            "schema_version": "c12-phase-b-resource-usage-v1",
            "variant": variant,
            "trainable_variant_parameters": matched_counts[variant],
            "training_and_prediction_seconds": total_seconds,
            "prefix_adaptation_seconds": prefix_summary["seconds"],
            "target_prediction_seconds": target_summary["seconds"],
            "target_prediction_rows_per_second": roles["target-development"].row_count
            / max(float(target_summary["seconds"]), 1e-9),
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "resource_measurement_mode": resource_measurement_mode,
            "single_gpu_serial_measurement": resource_measurement_mode == "isolated",
            "single_process_efficiency_metrics_valid": (
                resource_measurement_mode == "isolated"
            ),
            "final_accessed": False,
        }
        _write_json(output_dir / "resource-usage.json", resource_usage)
        summary = {
            "schema_version": PHASE_B_RUN_SCHEMA,
            "state": "predictions_sealed_evaluation_pending",
            "variant": variant,
            "display_name": VARIANT_DISPLAY_NAMES[variant],
            "variant_role": VARIANT_ROLES[variant],
            "best_epoch": best_epoch,
            "best_validation_pr_auc": best_pr_auc,
            "fixed_budget_steps": global_step,
            "training_and_prediction_seconds": total_seconds,
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "prediction_path": str(prediction_path),
            "prediction_receipt_sha256": _sha256(prediction_receipt),
            "prefix_prediction_receipt_sha256": _sha256(prefix_receipt_path),
            "representation_source": representation_receipt["schema_version"],
            "target_prefix_used": True,
            "target_prefix_labels_used": False,
            "target_development_labels_used": False,
            "source_anchor_unchanged": True,
            "final_accessed": False,
        }
        tracker.finish()
        summary["swanlab"] = tracker.status
        _write_json(output_dir / "summary.json", summary)
        _write_json(
            output_dir / "status.json",
            {
                "state": "predictions_sealed_evaluation_pending",
                "variant": variant,
                "target_prefix_used": True,
                "target_prefix_labels_used": False,
                "final_accessed": False,
            },
        )
        _write_artifact_manifest(output_dir)
        return summary
    except BaseException as error:
        if tracker is not None:
            tracker.fail(error)
            _write_json(output_dir / "swanlab-status.json", tracker.status)
        _write_json(
            output_dir / "status.json",
            {
                "state": "failed",
                "variant": variant,
                "error_type": type(error).__name__,
                "error": str(error),
                "target_prefix_labels_used": False,
                "final_accessed": False,
            },
        )
        raise


def _predict_target_development(
    model: nn.Module,
    role: SequenceRole,
    representation: np.ndarray,
    output_dir: Path,
    batch_size: int,
    device: torch.device,
    variant: str,
) -> tuple[Path, Path]:
    model.eval()
    probabilities = np.empty(role.row_count, dtype=np.float32)
    filled = np.zeros(role.row_count, dtype=bool)
    started = time.perf_counter()
    with torch.no_grad():
        for _, indices, values, valid, _ in _iter_representation_batches(
            role,
            representation,
            np.arange(role.sequence_count),
            batch_size,
        ):
            values = values.to(device, non_blocking=True)
            valid_device = valid.to(device, non_blocking=True)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                logits = model(values, valid_device)
            batch_probabilities = torch.sigmoid(logits).float().cpu().numpy()
            valid_np = valid.numpy()
            for batch_index, sequence_index in enumerate(indices):
                row_start = int(role.starts[sequence_index])
                length = int(role.lengths[sequence_index])
                probabilities[row_start : row_start + length] = batch_probabilities[batch_index][valid_np[batch_index]]
                filled[row_start : row_start + length] = True
    if not filled.all() or not np.isfinite(probabilities).all():
        raise C12TrainError("目标开发概率未完整封存")
    predictions_dir = output_dir / "predictions"
    predictions_dir.mkdir(parents=True, exist_ok=True)
    path = predictions_dir / "target-development.npz"
    temporary = predictions_dir / f"target-development.npz.partial.{os.getpid()}"
    with temporary.open("wb") as handle:
        np.savez_compressed(
            handle,
            probability=probabilities,
            sample_id=np.asarray(role.sample_id),
            sequence_id=np.asarray(role.sequence_id),
            position=np.asarray(role.position),
            valid_length=np.asarray(role.valid_length),
        )
    os.replace(temporary, path)
    receipt_path = predictions_dir / "target-development-receipt.json"
    _write_json(receipt_path, {
        "schema_version": "c12-target-development-predictions-v1",
        "variant": variant,
        "row_count": role.row_count,
        "sequence_count": role.sequence_count,
        "prediction_sha256": _sha256(path),
        "prediction_seconds": time.perf_counter() - started,
        "prediction_rows_per_second": role.row_count / max(time.perf_counter() - started, 1e-9),
        "mean_sequence_latency_seconds": (time.perf_counter() - started) / role.sequence_count,
        "labels_connected": False,
        "target_prefix_used": False,
        "final_accessed": False,
    })
    return path, receipt_path


def evaluate_target_development(cache_root: Path, run_dir: Path) -> dict[str, Any]:
    """在概率封存后独立连接 target-development 标签旁车。"""
    manifest, roles = load_cache(cache_root)
    status_path = run_dir / "status.json"
    status = _load_json(status_path)
    if status.get("state") != "predictions_sealed_evaluation_pending":
        raise C12TrainError("目标评价只能连接已封存且待评价的概率")
    prediction_path = run_dir / "predictions/target-development.npz"
    receipt_path = run_dir / "predictions/target-development-receipt.json"
    receipt = _load_json(receipt_path)
    if receipt.get("prediction_sha256") != _sha256(prediction_path):
        raise C12TrainError("目标开发预测哈希不匹配")
    target = roles["target-development"]
    label_path = _role_array_path(cache_root, "target-development", "labels")
    labels = np.load(label_path, mmap_mode="r")
    if labels.shape != (target.row_count,) or not np.isin(labels, (0, 1)).all():
        raise C12TrainError("目标开发标签旁车不合法")
    with np.load(prediction_path, allow_pickle=False) as predictions:
        probabilities = predictions["probability"]
        if not np.array_equal(predictions["sample_id"], target.sample_id):
            raise C12TrainError("目标开发概率与标签不能按 sample_id 逐行连接")
        if not np.array_equal(predictions["sequence_id"], target.sequence_id):
            raise C12TrainError("目标开发概率序列顺序漂移")
    threshold_receipt = _load_json(run_dir / "threshold-receipt.json")
    metrics = _binary_metrics(
        np.asarray(labels, dtype=np.uint8),
        np.asarray(probabilities, dtype=np.float64),
        float(threshold_receipt["threshold"]),
    )
    target_prefix_used = bool(receipt.get("target_prefix_used", False))
    target_prefix_labels_used = bool(status.get("target_prefix_labels_used", False))
    if target_prefix_labels_used:
        raise C12TrainError("目标前缀标签曾被使用，阶段 B 运行无效")
    metrics.update({
        "schema_version": "c12-target-development-metrics-v1",
        "variant": status.get("variant"),
        "evaluation_order": "概率与状态先封存，后由本入口连接标签",
        "prediction_sha256": _sha256(prediction_path),
        "label_sha256": _sha256(label_path),
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "target_prefix_used": target_prefix_used,
        "target_prefix_labels_used": target_prefix_labels_used,
        "final_accessed": False,
    })
    metrics_path = run_dir / "metrics/target-development.json"
    _write_json(metrics_path, metrics)
    _write_json(status_path, {
        "state": "finished",
        "variant": status.get("variant"),
        "target_development_evaluated": True,
        "target_prefix_used": target_prefix_used,
        "target_prefix_labels_used": target_prefix_labels_used,
        "final_accessed": False,
    })
    _write_artifact_manifest(run_dir)
    return metrics


def probe(cache_root: Path, batch_size: int, device_name: str) -> dict[str, Any]:
    """一次真实缓存小批导入和所有模型前向检查。"""
    manifest, roles = load_cache(cache_root)
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise C12TrainError("CUDA 探针要求可用 GPU")
    config = C12ModelConfig()
    receiver = ReceiverSourceScorer(config).to(device).eval()
    longest = np.argsort(roles["source-train"].lengths, kind="stable")[-batch_size:]
    _, _, values, valid, _ = next(
        _iter_sequence_batches(
            roles["source-train"],
            longest,
            batch_size,
        )
    )
    values = values.to(device)
    valid = valid.to(device)
    with torch.no_grad():
        with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
            phi = receiver.receiver(values, valid)
        models, raw_counts, matched_counts = build_parameter_matched_models(config)
        results: dict[str, Any] = {}
        for variant, model in models.items():
            model = model.to(device).eval()
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
                logits = model(phi, valid)
            if logits.shape != valid.shape or not torch.isfinite(logits[valid]).all():
                raise C12TrainError(f"{variant} 真实小批输出不合法")
            results[variant] = {
                "display_name": VARIANT_DISPLAY_NAMES[variant],
                "variant_role": VARIANT_ROLES[variant],
                "raw_trainable_parameters": raw_counts[variant],
                "matched_trainable_parameters": matched_counts[variant],
                "valid_logits": int(valid.sum()),
                "finite": True,
            }
    return {
        "status": "passed",
        "cache_schema": manifest["schema_version"],
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "batch_size_sequences": batch_size,
        "maximum_batch_length": int(valid.shape[1]),
        "input_fields": 155,
        "state_shape": [6, 32, 32],
        "parameter_ratio": max(matched_counts.values()) / min(matched_counts.values()),
        "variants": results,
        "target_prefix_read": False,
        "target_development_labels_read": False,
        "final_accessed": False,
    }


def gpu_gate(cache_root: Path, output_path: Path) -> dict[str, Any]:
    """用最长真实序列测量单进程前向、反向峰值并选择共同批量。"""
    if not torch.cuda.is_available():
        raise C12TrainError("显存门禁要求 CUDA")
    manifest, roles = load_cache(cache_root)
    role = roles["source-train"]
    if role.labels is None:
        raise C12TrainError("显存门禁缺少 source-train 标签")
    device = torch.device("cuda")
    config = C12ModelConfig()
    total_memory = int(torch.cuda.get_device_properties(device).total_memory)
    attempts: list[dict[str, Any]] = []
    selected: int | None = None
    for batch_size in (16, 8, 4):
        longest = np.argsort(role.lengths, kind="stable")[-batch_size:]
        _, _, values, valid, labels = next(
            _iter_sequence_batches(role, longest, batch_size)
        )
        assert labels is not None
        values = values.to(device)
        valid = valid.to(device)
        labels = labels.to(device)
        peaks: dict[str, int] = {}
        failure: str | None = None
        try:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats(device)
            receiver = ReceiverSourceScorer(config).to(device)
            with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                phi = receiver.receiver(values, valid)
                receiver_logits = receiver.classifier(phi).squeeze(-1)
                receiver_loss = nn.functional.binary_cross_entropy_with_logits(
                    receiver_logits[valid], labels[valid]
                )
            receiver_loss.backward()
            torch.cuda.synchronize(device)
            peaks["共同接收器"] = int(torch.cuda.max_memory_allocated(device))
            frozen_phi = phi.detach()
            del receiver_loss, receiver_logits, phi, receiver
            models, _, _ = build_parameter_matched_models(config)
            for variant in tuple(models):
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats(device)
                model = models.pop(variant).to(device)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    logits = model(frozen_phi, valid)
                    loss = nn.functional.binary_cross_entropy_with_logits(
                        logits[valid], labels[valid]
                    )
                loss.backward()
                torch.cuda.synchronize(device)
                peaks[variant] = int(torch.cuda.max_memory_allocated(device))
                del loss, logits, model
        except torch.OutOfMemoryError as error:
            failure = str(error)
            torch.cuda.empty_cache()
        maximum_peak = max(peaks.values(), default=0)
        reserve = max(6 * 1024**3, int(total_memory * 0.20))
        passed = failure is None and maximum_peak + reserve <= int(total_memory * 0.90)
        attempts.append({
            "batch_size_sequences": batch_size,
            "sequence_length": int(valid.shape[1]),
            "component_peak_gpu_memory_bytes": peaks,
            "maximum_peak_gpu_memory_bytes": maximum_peak,
            "reserve_bytes": reserve,
            "total_gpu_memory_bytes": total_memory,
            "passed": passed,
            "failure": failure,
        })
        if passed:
            selected = batch_size
            break
    result = {
        "schema_version": "c12-phase-a-gpu-gate-v1",
        "status": "passed" if selected is not None else "failed",
        "selected_batch_size_sequences": selected,
        "single_process_only": True,
        "maximum_sequence_length_checked": 128,
        "attempts": attempts,
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "cache_schema": manifest["schema_version"],
        "target_prefix_read": False,
        "target_development_labels_read": False,
        "final_accessed": False,
    }
    _write_json(output_path, result)
    if selected is None:
        raise C12TrainError("批量 16、8、4 均未通过最长序列单进程显存门禁")
    return result


def _write_artifact_manifest(root: Path) -> None:
    files = sorted(path for path in root.rglob("*") if path.is_file() and path.name != "artifact-manifest.json")
    _write_json(root / "artifact-manifest.json", {
        "schema_version": "c12-phase-a-artifact-manifest-v1",
        "files": {
            str(path.relative_to(root)): {"bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path in files
        },
        "final_accessed": False,
    })


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 C12 跨年度阶段 A 基线与阶段 B 主机制")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe_parser = subparsers.add_parser("probe", help="真实 Q0 缓存和所有变体小批前向")
    probe_parser.add_argument("--cache-root", type=Path, required=True)
    probe_parser.add_argument("--batch-size", type=int, default=2)
    probe_parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")

    gate = subparsers.add_parser("gpu-gate", help="最长真实序列单进程前向反向显存门禁")
    gate.add_argument("--cache-root", type=Path, required=True)
    gate.add_argument("--output", type=Path, required=True)

    receiver = subparsers.add_parser("train-receiver", help="训练一次共同接收器")
    receiver.add_argument("--cache-root", type=Path, required=True)
    receiver.add_argument("--output-dir", type=Path, required=True)
    receiver.add_argument("--run-name", required=True)
    receiver.add_argument("--batch-size", type=int, required=True)
    receiver.add_argument("--epochs", type=int, default=4)
    receiver.add_argument("--seed", type=int, default=42)

    encode = subparsers.add_parser("encode-receiver", help="落盘冻结接收表示")
    encode.add_argument("--cache-root", type=Path, required=True)
    encode.add_argument("--receiver-checkpoint", type=Path, required=True)
    encode.add_argument("--output-dir", type=Path, required=True)
    encode.add_argument("--batch-size", type=int, required=True)

    encode_prefix = subparsers.add_parser(
        "encode-target-prefix", help="用同一冻结接收器编码无标签目标前缀"
    )
    encode_prefix.add_argument("--cache-root", type=Path, required=True)
    encode_prefix.add_argument("--receiver-checkpoint", type=Path, required=True)
    encode_prefix.add_argument("--output-dir", type=Path, required=True)
    encode_prefix.add_argument("--batch-size", type=int, required=True)

    train = subparsers.add_parser("train-variant", help="训练一个阶段 A 或 GRU 变体")
    train.add_argument("--cache-root", type=Path, required=True)
    train.add_argument("--representation-root", type=Path, required=True)
    train.add_argument("--output-dir", type=Path, required=True)
    train.add_argument("--run-name", required=True)
    train.add_argument("--variant", choices=TRAINABLE_VARIANTS, required=True)
    train.add_argument("--batch-size", type=int, required=True)
    train.add_argument("--epochs", type=int, default=4)
    train.add_argument("--seed", type=int, default=42)

    train_phase_b = subparsers.add_parser(
        "train-phase-b-variant", help="训练并回放一个阶段 B 主机制变体"
    )
    train_phase_b.add_argument("--cache-root", type=Path, required=True)
    train_phase_b.add_argument("--representation-root", type=Path, required=True)
    train_phase_b.add_argument(
        "--target-prefix-representation-root", type=Path, required=True
    )
    train_phase_b.add_argument("--receiver-checkpoint", type=Path, required=True)
    train_phase_b.add_argument("--output-dir", type=Path, required=True)
    train_phase_b.add_argument("--run-name", required=True)
    train_phase_b.add_argument("--variant", choices=PHASE_B_VARIANTS, required=True)
    train_phase_b.add_argument("--batch-size", type=int, required=True)
    train_phase_b.add_argument("--epochs", type=int, default=4)
    train_phase_b.add_argument("--seed", type=int, default=42)
    train_phase_b.add_argument(
        "--resource-measurement-mode",
        choices=("isolated", "concurrent"),
        default="isolated",
        help="标记资源效率是否来自隔离的单进程运行",
    )

    evaluate = subparsers.add_parser("evaluate", help="概率封存后独立连接目标开发标签")
    evaluate.add_argument("--cache-root", type=Path, required=True)
    evaluate.add_argument("--run-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "probe":
        result = probe(args.cache_root, args.batch_size, args.device)
    elif args.command == "gpu-gate":
        result = gpu_gate(args.cache_root, args.output)
    elif args.command == "train-receiver":
        result = train_receiver(
            args.cache_root, args.output_dir, args.run_name,
            args.batch_size, args.epochs, args.seed,
        )
    elif args.command == "encode-receiver":
        result = encode_receiver(
            args.cache_root, args.receiver_checkpoint, args.output_dir, args.batch_size,
        )
    elif args.command == "encode-target-prefix":
        result = encode_target_prefix(
            args.cache_root,
            args.receiver_checkpoint,
            args.output_dir,
            args.batch_size,
        )
    elif args.command == "train-variant":
        result = train_variant(
            args.cache_root, args.representation_root, args.output_dir,
            args.run_name, args.variant, args.batch_size, args.epochs, args.seed,
        )
    elif args.command == "train-phase-b-variant":
        result = train_phase_b_variant(
            args.cache_root,
            args.representation_root,
            args.target_prefix_representation_root,
            args.receiver_checkpoint,
            args.output_dir,
            args.run_name,
            args.variant,
            args.batch_size,
            args.epochs,
            args.seed,
            args.resource_measurement_mode,
        )
    elif args.command == "evaluate":
        result = evaluate_target_development(args.cache_root, args.run_dir)
    else:
        raise AssertionError(f"未处理命令：{args.command}")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
