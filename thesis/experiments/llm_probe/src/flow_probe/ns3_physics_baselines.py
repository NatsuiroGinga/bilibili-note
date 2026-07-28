"""冻结星型 ns-3 四窗口数据上的同协议物理机理基线。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import resource
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import yaml

from flow_probe.physics_train import (
    MODEL_INPUT_FIELDS,
    PhysicsDataError,
    build_state_supervision_masks,
    masked_state_target_loss,
    prepare_physics_record,
    queue_balance_residual,
)
from flow_probe.tracking import (
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

BASELINES = ("constant_state", "state_supervision", "standard_pinn")
SPLIT_NAMES = ("train", "validation", "test")
EXPECTED_TOPOLOGY = "star-bottleneck-v1"
PHASE = "ns3-physics-baseline"
FORMAL_OUTPUT_ROOT = Path(
    "runs/baselines/theory-selection/ns3-star-physics/review-pending-3393d76e-v1"
)
SMOKE_OUTPUT_ROOT = Path("runs/smoke/ns3-star-physics")


class Ns3PhysicsBaselineError(ValueError):
    """物理基线输入、配置或制品不满足冻结协议。"""


@dataclass(frozen=True)
class PhysicsSplit:
    """单一冻结划分的公共观测、状态与训练期通量。"""

    name: str
    sample_ids: tuple[str, ...]
    group_ids: tuple[str, ...]
    features: np.ndarray
    state_targets: np.ndarray
    scales: np.ndarray
    capacity: np.ndarray
    received: np.ndarray
    dequeued: np.ndarray
    dropped_before: np.ndarray
    dropped_after: np.ndarray


@dataclass(frozen=True)
class SplitIdentity:
    """不保留状态真值与物理通量的划分标识审计结果。"""

    name: str
    sample_ids: tuple[str, ...]
    group_ids: tuple[str, ...]


@dataclass(frozen=True)
class AuditedStarInputs:
    """训练前只完成哈希、字段和隔离审计的冻结输入。"""

    input_paths: Mapping[str, Path]
    identities: Mapping[str, SplitIdentity]
    audit: Mapping[str, object]
    input_manifest: Mapping[str, object]


@dataclass(frozen=True)
class AuditedSplits:
    """通过哈希、字段和组隔离审计的三个星型划分。"""

    splits: Mapping[str, PhysicsSplit]
    audit: Mapping[str, object]
    input_manifest: Mapping[str, object]


@dataclass(frozen=True)
class InputTransform:
    """只由训练集拟合的二十维标准化参数。"""

    mean: np.ndarray
    scale: np.ndarray

    def apply(self, features: np.ndarray) -> np.ndarray:
        values = np.asarray(features, dtype=np.float32)
        if values.ndim != 3 or values.shape[1:] != (4, len(MODEL_INPUT_FIELDS)):
            raise Ns3PhysicsBaselineError("公共观测必须采用[样本,4,5]形状")
        flattened = values.reshape(len(values), -1)
        return ((flattened - self.mean) / self.scale).astype(np.float32, copy=False)


@dataclass(frozen=True)
class BaselineTrainingConfig:
    """状态监督与标准 PINN 共享的固定训练预算。"""

    hidden_size: int
    batch_size: int
    learning_rate: float
    weight_decay: float
    max_epochs: int
    patience: int
    minimum_delta: float
    lambda_state: float
    lambda_physics: float
    state_supervision_mode: str
    selection_metric: str
    device: str
    cpu_threads: int


@dataclass(frozen=True)
class LossTerms:
    """单批次状态与物理目标。"""

    total: torch.Tensor
    state: torch.Tensor
    physics: torch.Tensor | None


@dataclass(frozen=True)
class SplitEvaluation:
    """单一划分的指标和逐样本预测。"""

    metrics: Mapping[str, object]
    predictions: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class SelectedModel:
    """仅由训练与验证集产生的冻结最佳模型。"""

    model: torch.nn.Module
    transform: InputTransform
    best_epoch: int
    history: tuple[Mapping[str, object], ...]
    training_seconds: float
    parameter_count: int
    peak_gpu_memory_bytes: int | None
    selected_device: str


class PublicObservationStateRegressor(torch.nn.Module):
    """只消费四窗口五字段公共观测的五锚点状态回归器。"""

    def __init__(self, hidden_size: int) -> None:
        super().__init__()
        if hidden_size <= 0:
            raise Ns3PhysicsBaselineError("隐藏层宽度必须大于零")
        self.network = torch.nn.Sequential(
            torch.nn.Linear(4 * len(MODEL_INPUT_FIELDS), hidden_size),
            torch.nn.SiLU(),
            torch.nn.Linear(hidden_size, hidden_size),
            torch.nn.SiLU(),
            torch.nn.Linear(hidden_size, 5),
            torch.nn.Softplus(),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        if inputs.ndim != 2 or inputs.shape[1] != 4 * len(MODEL_INPUT_FIELDS):
            raise Ns3PhysicsBaselineError("状态回归器输入必须采用[批量,20]形状")
        return self.network(inputs.float())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _array_sha256(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(json.dumps(contiguous.shape, separators=(",", ":")).encode("ascii"))
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _sample_order_sha256(sample_ids: Sequence[str]) -> str:
    payload = json.dumps(list(sample_ids), separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _iter_jsonl(path: Path) -> Iterator[dict[str, object]]:
    with Path(path).open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise Ns3PhysicsBaselineError(f"JSONL 解析失败：{path}:{line_number}") from error
            if not isinstance(value, dict):
                raise Ns3PhysicsBaselineError(f"JSONL 记录必须为对象：{path}:{line_number}")
            yield value


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = list(_iter_jsonl(path))
    if not rows:
        raise Ns3PhysicsBaselineError(f"冻结划分为空：{path}")
    return rows


def _feature_matrix(record: Mapping[str, object]) -> np.ndarray:
    raw_inputs = record.get("model_inputs")
    if not isinstance(raw_inputs, Mapping) or set(raw_inputs) != set(MODEL_INPUT_FIELDS):
        raise Ns3PhysicsBaselineError("model_inputs 必须且只能包含冻结五字段")
    columns: list[list[float]] = []
    for field in MODEL_INPUT_FIELDS:
        values = raw_inputs[field]
        if not isinstance(values, (list, tuple)) or len(values) != 4:
            raise Ns3PhysicsBaselineError(f"{field} 必须包含四个窗口值")
        numeric = [float(value) for value in values]
        if not all(math.isfinite(value) for value in numeric):
            raise Ns3PhysicsBaselineError(f"{field} 包含非有限数值")
        columns.append(numeric)
    return np.asarray(columns, dtype=np.float32).T


def _record_identity(record: Mapping[str, object], path: Path, split_name: str) -> tuple[str, str]:
    if str(record.get("split", "")) != split_name:
        raise Ns3PhysicsBaselineError(f"{path.name} 含错误 split 字段")
    sample_id = str(record.get("sample_id", "")).strip()
    group_id = str(record.get("group_id", "")).strip()
    if not sample_id or not group_id:
        raise Ns3PhysicsBaselineError("冻结记录缺少 sample_id 或 group_id")
    topology = group_id.split("|", 1)[0]
    if topology != EXPECTED_TOPOLOGY:
        raise Ns3PhysicsBaselineError(f"本轮只接受 {EXPECTED_TOPOLOGY}：{group_id}")
    return sample_id, group_id


def _scan_split_identity(path: Path, split_name: str) -> SplitIdentity:
    """流式扫描测试标识与公共字段，不保留状态真值和通量。"""
    sample_ids: list[str] = []
    group_ids: list[str] = []
    for record in _iter_jsonl(path):
        sample_id, group_id = _record_identity(record, path, split_name)
        _feature_matrix(record)
        sample_ids.append(sample_id)
        group_ids.append(group_id)
    if not sample_ids:
        raise Ns3PhysicsBaselineError(f"冻结划分为空：{path}")
    if len(sample_ids) != len(set(sample_ids)):
        raise Ns3PhysicsBaselineError(f"{split_name} 存在重复 sample_id")
    return SplitIdentity(
        name=split_name,
        sample_ids=tuple(sample_ids),
        group_ids=tuple(group_ids),
    )


def _load_split(path: Path, split_name: str) -> PhysicsSplit:
    rows = _read_jsonl(path)
    sample_ids: list[str] = []
    group_ids: list[str] = []
    features: list[np.ndarray] = []
    state_targets: list[tuple[float, ...]] = []
    scales: list[float] = []
    capacity: list[tuple[float, ...]] = []
    received: list[tuple[float, ...]] = []
    dequeued: list[tuple[float, ...]] = []
    dropped_before: list[tuple[float, ...]] = []
    dropped_after: list[tuple[float, ...]] = []
    for record in rows:
        sample_id, group_id = _record_identity(record, path, split_name)
        try:
            prepared = prepare_physics_record(record)
        except PhysicsDataError as error:
            raise Ns3PhysicsBaselineError(str(error)) from error
        sample_ids.append(sample_id)
        group_ids.append(group_id)
        features.append(_feature_matrix(record))
        state_targets.append(prepared.state_targets)
        scales.append(prepared.scale)
        capacity.append(prepared.capacity)
        received.append(prepared.received)
        dequeued.append(prepared.dequeued)
        dropped_before.append(prepared.dropped_before)
        dropped_after.append(prepared.dropped_after)
    if len(sample_ids) != len(set(sample_ids)):
        raise Ns3PhysicsBaselineError(f"{split_name} 存在重复 sample_id")
    return PhysicsSplit(
        name=split_name,
        sample_ids=tuple(sample_ids),
        group_ids=tuple(group_ids),
        features=np.asarray(features, dtype=np.float32),
        state_targets=np.asarray(state_targets, dtype=np.float32),
        scales=np.asarray(scales, dtype=np.float32),
        capacity=np.asarray(capacity, dtype=np.float32),
        received=np.asarray(received, dtype=np.float32),
        dequeued=np.asarray(dequeued, dtype=np.float32),
        dropped_before=np.asarray(dropped_before, dtype=np.float32),
        dropped_after=np.asarray(dropped_after, dtype=np.float32),
    )


def _intersection_counts(
    values: Mapping[str, set[str]],
) -> dict[str, int]:
    return {
        "train_validation": len(values["train"].intersection(values["validation"])),
        "train_test": len(values["train"].intersection(values["test"])),
        "validation_test": len(values["validation"].intersection(values["test"])),
    }


def audit_star_split_inputs(
    input_dir: Path, expected_hashes: Mapping[str, str]
) -> AuditedStarInputs:
    """训练前流式审计三划分，但不物化测试状态真值与通量。"""
    root = Path(input_dir)
    required_files = tuple(f"{split}.jsonl" for split in SPLIT_NAMES) + ("split_manifest.json",)
    if set(expected_hashes) != set(required_files):
        raise Ns3PhysicsBaselineError("expected_sha256 必须覆盖三个划分和 split_manifest")
    input_files = {name: root / name for name in required_files}
    actual_hashes: dict[str, str] = {}
    for name, path in input_files.items():
        if not path.is_file():
            raise Ns3PhysicsBaselineError(f"冻结输入不存在：{path}")
        actual = _sha256(path)
        expected = str(expected_hashes[name])
        if actual != expected:
            raise Ns3PhysicsBaselineError(f"冻结输入哈希不一致：{name}")
        actual_hashes[name] = actual

    manifest = json.loads(input_files["split_manifest.json"].read_text(encoding="utf-8"))
    if not isinstance(manifest, Mapping) or manifest.get("schema_version") != (
        "flow_probe_ns3_sequence_split_v1"
    ):
        raise Ns3PhysicsBaselineError("split_manifest 模式版本不合法")
    manifest_splits = manifest.get("splits")
    if not isinstance(manifest_splits, Mapping) or set(manifest_splits) != set(SPLIT_NAMES):
        raise Ns3PhysicsBaselineError("split_manifest 必须且只能包含三个固定划分")

    identities = {
        split: _scan_split_identity(input_files[f"{split}.jsonl"], split) for split in SPLIT_NAMES
    }
    for split_name, identity in identities.items():
        manifest_entry = manifest_splits[split_name]
        if not isinstance(manifest_entry, Mapping):
            raise Ns3PhysicsBaselineError(f"split_manifest 缺少 {split_name} 记录")
        if int(manifest_entry.get("sample_count", -1)) != len(identity.sample_ids):
            raise Ns3PhysicsBaselineError(f"{split_name} 样本数与清单不一致")
        expected_groups = tuple(sorted(str(value) for value in manifest_entry.get("group_ids", [])))
        actual_groups = tuple(sorted(set(identity.group_ids)))
        if actual_groups != expected_groups:
            raise Ns3PhysicsBaselineError(f"{split_name} group_id 与清单不一致")

    sample_sets = {name: set(identity.sample_ids) for name, identity in identities.items()}
    group_sets = {name: set(identity.group_ids) for name, identity in identities.items()}
    sample_intersections = _intersection_counts(sample_sets)
    group_intersections = _intersection_counts(group_sets)
    if any(sample_intersections.values()):
        raise Ns3PhysicsBaselineError("三个划分存在 sample_id 泄漏")
    if any(group_intersections.values()):
        raise Ns3PhysicsBaselineError("三个划分存在 group_id 泄漏")
    topologies = sorted(
        {group_id.split("|", 1)[0] for values in group_sets.values() for group_id in values}
    )
    if topologies != [EXPECTED_TOPOLOGY]:
        raise Ns3PhysicsBaselineError("冻结输入包含非星型拓扑")

    audit: dict[str, object] = {
        "schema_version": "flow_probe_ns3_physics_split_audit_v1",
        "status": "passed",
        "sample_intersections": sample_intersections,
        "group_intersections": group_intersections,
        "topologies": topologies,
        "model_input_fields": list(MODEL_INPUT_FIELDS),
        "model_input_field_count": len(MODEL_INPUT_FIELDS),
        "split_counts": {
            name: {"samples": len(identity.sample_ids), "groups": len(set(identity.group_ids))}
            for name, identity in identities.items()
        },
        "test_content_materialized_before_selection": False,
        "test_used_for_fit": False,
        "test_used_for_selection": False,
        "selection_split": "validation",
    }
    input_manifest: dict[str, object] = {
        "schema_version": "flow_probe_ns3_physics_inputs_v1",
        "input_dir": str(root),
        "files": {
            name: {
                "path": str(path),
                "sha256": actual_hashes[name],
                "size_bytes": path.stat().st_size,
                "records": (
                    len(identities[name.removesuffix(".jsonl")].sample_ids)
                    if name.endswith(".jsonl")
                    else None
                ),
            }
            for name, path in input_files.items()
        },
        "sample_order_sha256": {
            name: _sample_order_sha256(identity.sample_ids) for name, identity in identities.items()
        },
    }
    return AuditedStarInputs(
        input_paths=input_files,
        identities=identities,
        audit=audit,
        input_manifest=input_manifest,
    )


def materialize_audited_split(audited: AuditedStarInputs, split_name: str) -> PhysicsSplit:
    """物化一个已审计划分，并再次确认标识顺序未漂移。"""
    if split_name not in SPLIT_NAMES:
        raise Ns3PhysicsBaselineError(f"未知冻结划分：{split_name}")
    split = _load_split(audited.input_paths[f"{split_name}.jsonl"], split_name)
    identity = audited.identities[split_name]
    if split.sample_ids != identity.sample_ids or split.group_ids != identity.group_ids:
        raise Ns3PhysicsBaselineError(f"{split_name} 在审计后发生标识漂移")
    return split


def load_and_audit_star_splits(
    input_dir: Path, expected_hashes: Mapping[str, str]
) -> AuditedSplits:
    """一次性物化三划分；正式运行应使用分阶段接口。"""
    audited = audit_star_split_inputs(input_dir, expected_hashes)
    splits = {
        split_name: materialize_audited_split(audited, split_name) for split_name in SPLIT_NAMES
    }
    return AuditedSplits(
        splits=splits,
        audit=audited.audit,
        input_manifest=audited.input_manifest,
    )


def select_then_materialize_test(
    *,
    audited: AuditedStarInputs,
    train: PhysicsSplit,
    validation: PhysicsSplit,
    selector: Callable[[PhysicsSplit, PhysicsSplit], object],
    selection_validator: Callable[[object], bool],
) -> tuple[object, PhysicsSplit]:
    """确保选择回调返回后才首次物化测试状态和通量。"""
    selection = selector(train, validation)
    if not selection_validator(selection):
        raise Ns3PhysicsBaselineError("选择结果未冻结，不得物化测试集")
    test = materialize_audited_split(audited, "test")
    return selection, test


def fit_train_transform(train: PhysicsSplit) -> InputTransform:
    """只从训练公共观测拟合标准化参数。"""
    flattened = np.asarray(train.features, dtype=np.float32).reshape(len(train.sample_ids), -1)
    mean = flattened.mean(axis=0, dtype=np.float64).astype(np.float32)
    scale = flattened.std(axis=0, dtype=np.float64).astype(np.float32)
    scale = np.where(scale > 1e-8, scale, 1.0).astype(np.float32)
    return InputTransform(mean=mean, scale=scale)


def build_supervision_masks(split: PhysicsSplit, seed: int) -> np.ndarray:
    """复用组级双锚点规则构造稀疏状态监督掩码。"""
    records = [
        {"sample_id": sample_id, "group_id": group_id}
        for sample_id, group_id in zip(split.sample_ids, split.group_ids, strict=True)
    ]
    mapping = build_state_supervision_masks(records, "anchor0_plus_one", seed)
    return np.asarray([mapping[sample_id] for sample_id in split.sample_ids], dtype=bool)


def fit_constant_state(targets: np.ndarray, masks: np.ndarray) -> np.ndarray:
    """逐锚点只使用训练掩码可见真值拟合常数。"""
    target_values = np.asarray(targets, dtype=np.float32)
    visible = np.asarray(masks, dtype=bool)
    if (
        target_values.ndim != 2
        or target_values.shape[1] != 5
        or visible.shape != target_values.shape
    ):
        raise Ns3PhysicsBaselineError("常数拟合要求同形状的[样本,5]目标和掩码")
    means: list[float] = []
    for anchor in range(5):
        selected = target_values[visible[:, anchor], anchor]
        if not len(selected):
            raise Ns3PhysicsBaselineError(f"训练监督未覆盖锚点 q{anchor}")
        means.append(float(selected.mean()))
    return np.asarray(means, dtype=np.float32)


def build_model(seed: int, hidden_size: int, device: torch.device) -> torch.nn.Module:
    """以固定种子构造相同容量和初始权重的状态回归器。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    return PublicObservationStateRegressor(hidden_size).to(device)


def compute_training_loss(
    baseline: str,
    predicted: torch.Tensor,
    target: torch.Tensor,
    mask: torch.Tensor,
    fluxes: Mapping[str, torch.Tensor],
    lambda_physics: float,
) -> LossTerms:
    """让标准 PINN 相对状态监督只增加一个可微守恒残差。"""
    if baseline not in {"state_supervision", "standard_pinn"}:
        raise Ns3PhysicsBaselineError(f"神经训练不支持基线：{baseline}")
    if lambda_physics < 0:
        raise Ns3PhysicsBaselineError("lambda_physics 不得为负")
    state = masked_state_target_loss(predicted, target, mask)
    if baseline == "state_supervision":
        return LossTerms(total=state, state=state, physics=None)
    required = {
        "scale",
        "capacity",
        "received",
        "dequeued",
        "dropped_before",
        "dropped_after",
    }
    if set(fluxes) != required:
        raise Ns3PhysicsBaselineError("标准 PINN 通量字段不完整")
    residual = queue_balance_residual(
        predicted,
        fluxes["scale"],
        fluxes["capacity"],
        fluxes["received"],
        fluxes["dequeued"],
        fluxes["dropped_before"],
        fluxes["dropped_after"],
    )
    physics = residual.square().mean()
    return LossTerms(total=state + lambda_physics * physics, state=state, physics=physics)


def _flux_tensors(
    split: PhysicsSplit, indices: np.ndarray, device: torch.device
) -> dict[str, torch.Tensor]:
    return {
        "scale": torch.as_tensor(split.scales[indices], dtype=torch.float32, device=device),
        "capacity": torch.as_tensor(split.capacity[indices], dtype=torch.float32, device=device),
        "received": torch.as_tensor(split.received[indices], dtype=torch.float32, device=device),
        "dequeued": torch.as_tensor(split.dequeued[indices], dtype=torch.float32, device=device),
        "dropped_before": torch.as_tensor(
            split.dropped_before[indices], dtype=torch.float32, device=device
        ),
        "dropped_after": torch.as_tensor(
            split.dropped_after[indices], dtype=torch.float32, device=device
        ),
    }


def _resolve_device(configured: str) -> torch.device:
    normalized = str(configured).lower()
    if normalized == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if normalized not in {"cpu", "cuda"}:
        raise Ns3PhysicsBaselineError("device 只允许 auto、cpu 或 cuda")
    if normalized == "cuda" and not torch.cuda.is_available():
        raise Ns3PhysicsBaselineError("配置要求 CUDA，但当前环境不可用")
    return torch.device(normalized)


def _predict_model(
    model: torch.nn.Module,
    transformed: np.ndarray,
    batch_size: int,
    device: torch.device,
) -> tuple[np.ndarray, float]:
    predictions: list[np.ndarray] = []
    started = time.perf_counter()
    model.eval()
    with torch.no_grad():
        for offset in range(0, len(transformed), batch_size):
            batch = torch.as_tensor(
                transformed[offset : offset + batch_size], dtype=torch.float32, device=device
            )
            predictions.append(model(batch).detach().cpu().numpy())
    elapsed = time.perf_counter() - started
    return np.concatenate(predictions, axis=0).astype(np.float32, copy=False), elapsed


def evaluate_predictions(
    split: PhysicsSplit, predictions: np.ndarray, masks: np.ndarray
) -> SplitEvaluation:
    """在冻结样本顺序上计算状态和独立物理残差。"""
    predicted = np.asarray(predictions, dtype=np.float32)
    visible = np.asarray(masks, dtype=bool)
    if predicted.shape != split.state_targets.shape or visible.shape != predicted.shape:
        raise Ns3PhysicsBaselineError("预测、状态目标与掩码形状必须一致")
    squared = np.square(predicted - split.state_targets, dtype=np.float32)
    unobserved = ~visible
    if not visible.any() or not unobserved.any():
        raise Ns3PhysicsBaselineError("评价必须同时包含已观测和未观测锚点")
    with torch.no_grad():
        residual = queue_balance_residual(
            torch.from_numpy(predicted),
            torch.from_numpy(split.scales),
            torch.from_numpy(split.capacity),
            torch.from_numpy(split.received),
            torch.from_numpy(split.dequeued),
            torch.from_numpy(split.dropped_before),
            torch.from_numpy(split.dropped_after),
        ).numpy()
    metrics: dict[str, object] = {
        "sample_count": len(split.sample_ids),
        "state_mse": float(squared.mean()),
        "state_mae": float(np.abs(predicted - split.state_targets).mean()),
        "state_mse_observed": float(squared[visible].mean()),
        "state_mse_unobserved": float(squared[unobserved].mean()),
        "state_anchor_mse": [float(value) for value in squared.mean(axis=0)],
        "physics_residual_mse": float(np.square(residual).mean()),
    }
    records = tuple(
        {
            "sample_id": sample_id,
            "group_id": group_id,
            "split": split.name,
            "prediction": [float(value) for value in predicted[index]],
            "target": [float(value) for value in split.state_targets[index]],
            "observed_mask": [bool(value) for value in visible[index]],
            "physics_residual": [float(value) for value in residual[index]],
        }
        for index, (sample_id, group_id) in enumerate(
            zip(split.sample_ids, split.group_ids, strict=True)
        )
    )
    return SplitEvaluation(metrics=metrics, predictions=records)


def train_selected_model(
    *,
    train: PhysicsSplit,
    validation: PhysicsSplit,
    baseline: str,
    seed: int,
    config: BaselineTrainingConfig,
    metric_logger: Callable[[Mapping[str, float], int], None] | None = None,
) -> SelectedModel:
    """只用训练与验证集拟合，并按验证完整状态误差选择权重。"""
    if baseline not in {"state_supervision", "standard_pinn"}:
        raise Ns3PhysicsBaselineError("train_selected_model 只接受两个神经基线")
    if config.selection_metric != "validation_state_mse":
        raise Ns3PhysicsBaselineError("模型选择指标必须固定为 validation_state_mse")
    torch.set_num_threads(config.cpu_threads)
    device = _resolve_device(config.device)
    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.set_float32_matmul_precision("high")
    transform = fit_train_transform(train)
    train_features = transform.apply(train.features)
    validation_features = transform.apply(validation.features)
    train_masks = build_supervision_masks(train, seed)
    validation_masks = build_supervision_masks(validation, seed)
    model = build_model(seed, config.hidden_size, device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    generator = np.random.default_rng(seed)
    best_metric = math.inf
    best_epoch = 0
    best_state: dict[str, torch.Tensor] | None = None
    stale_epochs = 0
    history: list[Mapping[str, object]] = []
    started = time.perf_counter()

    for epoch in range(1, config.max_epochs + 1):
        model.train()
        order = generator.permutation(len(train.sample_ids))
        total_state = 0.0
        total_physics = 0.0
        total_examples = 0
        for offset in range(0, len(order), config.batch_size):
            indices = order[offset : offset + config.batch_size]
            features = torch.as_tensor(train_features[indices], dtype=torch.float32, device=device)
            targets = torch.as_tensor(
                train.state_targets[indices], dtype=torch.float32, device=device
            )
            masks = torch.as_tensor(train_masks[indices], dtype=torch.bool, device=device)
            optimizer.zero_grad(set_to_none=True)
            predicted = model(features)
            terms = compute_training_loss(
                baseline,
                predicted,
                targets,
                masks,
                _flux_tensors(train, indices, device),
                config.lambda_physics,
            )
            (config.lambda_state * terms.total).backward()
            optimizer.step()
            batch_count = len(indices)
            total_state += float(terms.state.detach().item()) * batch_count
            total_physics += (
                float(terms.physics.detach().item()) * batch_count
                if terms.physics is not None
                else 0.0
            )
            total_examples += batch_count

        validation_predictions, _ = _predict_model(
            model, validation_features, config.batch_size, device
        )
        validation_result = evaluate_predictions(
            validation, validation_predictions, validation_masks
        )
        validation_metric = float(validation_result.metrics["state_mse"])
        record: dict[str, object] = {
            "epoch": epoch,
            "train_state_loss": total_state / total_examples,
            "train_physics_loss": total_physics / total_examples,
            "validation_state_mse": validation_metric,
            "validation_state_mse_observed": float(validation_result.metrics["state_mse_observed"]),
            "validation_state_mse_unobserved": float(
                validation_result.metrics["state_mse_unobserved"]
            ),
            "validation_physics_residual_mse": float(
                validation_result.metrics["physics_residual_mse"]
            ),
        }
        history.append(record)
        if metric_logger is not None:
            metric_logger(
                {
                    f"{PHASE}/train_state_loss": float(record["train_state_loss"]),
                    f"{PHASE}/train_physics_loss": float(record["train_physics_loss"]),
                    f"{PHASE}/validation_state_mse": validation_metric,
                    f"{PHASE}/validation_state_mse_unobserved": float(
                        record["validation_state_mse_unobserved"]
                    ),
                    f"{PHASE}/validation_physics_residual_mse": float(
                        record["validation_physics_residual_mse"]
                    ),
                },
                epoch,
            )
        if validation_metric < best_metric - config.minimum_delta:
            best_metric = validation_metric
            best_epoch = epoch
            best_state = {
                name: value.detach().cpu().clone() for name, value in model.state_dict().items()
            }
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= config.patience:
                break

    if best_state is None or best_epoch <= 0:
        raise Ns3PhysicsBaselineError("验证集未产生可选择的最佳权重")
    model.load_state_dict(best_state)
    model.to(device)
    peak_gpu_memory = int(torch.cuda.max_memory_allocated()) if device.type == "cuda" else None
    return SelectedModel(
        model=model,
        transform=transform,
        best_epoch=best_epoch,
        history=tuple(history),
        training_seconds=time.perf_counter() - started,
        parameter_count=sum(parameter.numel() for parameter in model.parameters()),
        peak_gpu_memory_bytes=peak_gpu_memory,
        selected_device=device.type,
    )


def build_run_identity(
    run_kind: str,
    config: BaselineTrainingConfig,
    smoke_max_epochs: int | None,
) -> dict[str, object]:
    """构造正式与冒烟运行不可混淆的机器身份。"""
    normalized = str(run_kind).lower()
    if normalized not in {"formal", "smoke"}:
        raise Ns3PhysicsBaselineError("run_kind 只允许 formal 或 smoke")
    if normalized == "formal" and smoke_max_epochs is not None:
        raise Ns3PhysicsBaselineError("formal 运行不得覆盖最大训练轮数")
    if normalized == "smoke" and smoke_max_epochs is None:
        raise Ns3PhysicsBaselineError("smoke 运行必须显式给出冒烟训练轮数")
    if smoke_max_epochs is not None and not 1 <= smoke_max_epochs <= 2:
        raise Ns3PhysicsBaselineError("冒烟训练最多允许两个 epoch")
    return {
        "run_kind": normalized,
        "effective_max_epochs": (
            int(config.max_epochs) if smoke_max_epochs is None else int(smoke_max_epochs)
        ),
        "protocol_complete": normalized == "formal",
    }


def validate_output_location(
    *,
    output_dir: Path,
    project_root: Path,
    baseline: str,
    seed: int,
    run_identity: Mapping[str, object],
) -> Path:
    """拒绝把冒烟结果写入正式矩阵，或把正式结果写到任意目录。"""
    candidate = Path(output_dir)
    if not candidate.is_absolute():
        candidate = Path(project_root) / candidate
    candidate = candidate.resolve()
    normalized_root = Path(project_root).resolve()
    if run_identity["run_kind"] == "formal":
        expected = (normalized_root / FORMAL_OUTPUT_ROOT / f"{baseline}-seed{seed}").resolve()
        if candidate != expected:
            raise Ns3PhysicsBaselineError(f"formal 输出目录必须固定为：{expected}")
    else:
        smoke_root = (normalized_root / SMOKE_OUTPUT_ROOT).resolve()
        try:
            relative = candidate.relative_to(smoke_root)
        except ValueError as error:
            raise Ns3PhysicsBaselineError(f"smoke 输出目录必须位于：{smoke_root}") from error
        if not relative.parts:
            raise Ns3PhysicsBaselineError("smoke 输出目录必须是冒烟根目录的唯一子目录")
    return candidate


def final_tracking_step(history: Sequence[Mapping[str, object]], best_epoch: int | None) -> int:
    """返回严格晚于全部训练轮次的最终指标步骤。"""
    if not history:
        if best_epoch is not None:
            raise Ns3PhysicsBaselineError("无训练历史时最佳轮次必须为空")
        return 1
    if best_epoch is None or not 1 <= best_epoch <= len(history):
        raise Ns3PhysicsBaselineError("最佳轮次必须位于训练历史范围内")
    return len(history) + 1


def run_status_payload(
    *,
    status: str,
    stage: str,
    baseline: str,
    seed: int,
    run_identity: Mapping[str, object],
    tracking_verified: bool = False,
) -> dict[str, object]:
    """禁止在云端指标和图表复核前把运行标记为完成。"""
    if status == "finished" and not tracking_verified:
        raise Ns3PhysicsBaselineError("SwanLab 云端核验前不得标记运行完成")
    required_identity = {"run_kind", "effective_max_epochs", "protocol_complete"}
    if set(run_identity) != required_identity:
        raise Ns3PhysicsBaselineError("运行身份字段不完整")
    return {
        "schema_version": "flow_probe_ns3_physics_run_status_v1",
        "status": status,
        "stage": stage,
        "baseline": baseline,
        "seed": seed,
        **dict(run_identity),
        "tracking_verified": bool(tracking_verified),
    }


def load_baseline_config(path: Path) -> tuple[dict[str, object], BaselineTrainingConfig]:
    """读取并校验冻结物理基线配置。"""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise Ns3PhysicsBaselineError("物理基线配置根节点必须为映射")
    if raw.get("stage") != "theory_selection" or raw.get("status") != "review_pending":
        raise Ns3PhysicsBaselineError("本轮配置必须标记为 theory_selection/review_pending")
    training = raw.get("training")
    if not isinstance(training, Mapping):
        raise Ns3PhysicsBaselineError("物理基线配置缺少 training")
    required = {
        "hidden_size",
        "batch_size",
        "learning_rate",
        "weight_decay",
        "max_epochs",
        "patience",
        "minimum_delta",
        "lambda_state",
        "lambda_physics",
        "state_supervision_mode",
        "selection_metric",
        "device",
        "cpu_threads",
    }
    missing = sorted(required.difference(training))
    if missing:
        raise Ns3PhysicsBaselineError("训练配置缺失：" + ", ".join(missing))
    config = BaselineTrainingConfig(
        hidden_size=int(training["hidden_size"]),
        batch_size=int(training["batch_size"]),
        learning_rate=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
        max_epochs=int(training["max_epochs"]),
        patience=int(training["patience"]),
        minimum_delta=float(training["minimum_delta"]),
        lambda_state=float(training["lambda_state"]),
        lambda_physics=float(training["lambda_physics"]),
        state_supervision_mode=str(training["state_supervision_mode"]),
        selection_metric=str(training["selection_metric"]),
        device=str(training["device"]),
        cpu_threads=int(training["cpu_threads"]),
    )
    positive = (
        config.hidden_size,
        config.batch_size,
        config.learning_rate,
        config.max_epochs,
        config.patience,
        config.lambda_state,
        config.cpu_threads,
    )
    if any(value <= 0 for value in positive):
        raise Ns3PhysicsBaselineError("固定训练预算中的正值字段必须大于零")
    if config.weight_decay < 0 or config.minimum_delta < 0 or config.lambda_physics < 0:
        raise Ns3PhysicsBaselineError("权重衰减、最小改进量和物理权重不得为负")
    if config.lambda_state != 1.0 or config.state_supervision_mode != "anchor0_plus_one":
        raise Ns3PhysicsBaselineError("状态监督必须固定为 lambda_state=1 和 anchor0_plus_one")
    if config.selection_metric != "validation_state_mse":
        raise Ns3PhysicsBaselineError("选择指标必须固定为 validation_state_mse")
    _resolve_device(config.device)
    return raw, config


def required_artifact_names(baseline: str) -> set[str]:
    """返回单次运行必须生成的全部制品。"""
    if baseline not in BASELINES:
        raise Ns3PhysicsBaselineError(f"未知物理基线：{baseline}")
    names = {
        "artifact_manifest.json",
        "config_snapshot.yaml",
        "environment.json",
        "input_manifest.json",
        "split_audit.json",
        "training_history.jsonl",
        "predictions.jsonl.gz",
        "summary.json",
        "cost.json",
        "swanlab_metrics.json",
        "swanlab_metadata.json",
        "tracking_verification.json",
        "file_sha256_manifest.json",
        "run_status.json",
        "console.log",
    }
    names.add("constant_state.json" if baseline == "constant_state" else "best_model.pt")
    return names


def _environment(device: torch.device, config: BaselineTrainingConfig) -> dict[str, object]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "cpu_model": platform.processor() or None,
        "logical_threads": os.cpu_count(),
        "execution_thread_limit": config.cpu_threads,
        "torch": torch.__version__,
        "numpy": np.__version__,
        "pyyaml": _package_version("pyyaml"),
        "swanlab": _package_version("swanlab"),
        "cuda_available": torch.cuda.is_available(),
        "cuda_runtime": torch.version.cuda,
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "selected_device": device.type,
        "precision": "float32",
        "quantization": None,
        "batch_size": config.batch_size,
    }


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value * 1024 if sys.platform != "darwin" else value)


def _write_predictions(path: Path, evaluations: Mapping[str, SplitEvaluation]) -> None:
    with gzip.open(path, "xt", encoding="utf-8") as target:
        for split_name in ("validation", "test"):
            for record in evaluations[split_name].predictions:
                target.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _write_history(path: Path, history: Sequence[Mapping[str, object]]) -> None:
    with Path(path).open("w", encoding="utf-8") as target:
        for record in history:
            target.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _file_hash_manifest(output_dir: Path, names: set[str]) -> dict[str, object]:
    entries = []
    for name in sorted(names.difference({"file_sha256_manifest.json"})):
        path = output_dir / name
        if path.is_file():
            entries.append(
                {"path": name, "size_bytes": path.stat().st_size, "sha256": _sha256(path)}
            )
    swanlog_dir = output_dir / "swanlog" / PHASE
    if swanlog_dir.is_dir():
        for path in sorted(swanlog_dir.rglob("*")):
            if path.is_file():
                entries.append(
                    {
                        "path": str(path.relative_to(output_dir)),
                        "size_bytes": path.stat().st_size,
                        "sha256": _sha256(path),
                    }
                )
    return {"schema_version": "flow_probe_ns3_physics_file_hashes_v1", "files": entries}


def _validate_local_run_artifacts(
    output_dir: Path,
    baseline: str,
    expected_verification_status: str,
) -> dict[str, object]:
    missing = sorted(
        name for name in required_artifact_names(baseline) if not (output_dir / name).is_file()
    )
    if missing:
        raise Ns3PhysicsBaselineError("运行制品不完整：" + ", ".join(missing))
    swanlog_dir = output_dir / "swanlog" / PHASE
    if not swanlog_dir.is_dir() or not any(path.is_file() for path in swanlog_dir.rglob("*")):
        raise Ns3PhysicsBaselineError("运行缺少 SwanLab 原始日志")
    manifest = json.loads((output_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, Mapping)
        or manifest.get("status") != "finished"
        or manifest.get("phase") != PHASE
        or not str(manifest.get("run_id", "")).strip()
        or not str(manifest.get("run_url", "")).strip()
    ):
        raise Ns3PhysicsBaselineError("SwanLab 制品清单未记录成功运行")
    verification = json.loads(
        (output_dir / "tracking_verification.json").read_text(encoding="utf-8")
    )
    if (
        not isinstance(verification, Mapping)
        or verification.get("status") != expected_verification_status
        or verification.get("run_id") != manifest["run_id"]
    ):
        raise Ns3PhysicsBaselineError("SwanLab 复核记录与运行清单不一致")
    return dict(manifest)


def finalize_tracking_verification(
    *,
    output_dir: Path,
    run_id: str,
    observed_metrics: Sequence[str],
    observed_charts: Sequence[str],
    evidence_note: str,
) -> dict[str, object]:
    """记录人工云端复核，并在全部证据齐备后标记运行完成。"""
    output_dir = Path(output_dir)
    status_path = output_dir / "run_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if not isinstance(status, Mapping) or status.get("status") != (
        "awaiting_tracking_verification"
    ):
        raise Ns3PhysicsBaselineError("只能核验等待 SwanLab 复核的运行")
    manifest = json.loads((output_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    normalized_run_id = str(run_id).strip()
    if not normalized_run_id or normalized_run_id != str(manifest.get("run_id", "")):
        raise Ns3PhysicsBaselineError("复核运行编号与制品清单不一致")
    metrics = json.loads((output_dir / "swanlab_metrics.json").read_text(encoding="utf-8"))
    local_metric_names = set(metrics.get("metrics", {})) if isinstance(metrics, Mapping) else set()
    metric_names = tuple(
        dict.fromkeys(str(value).strip() for value in observed_metrics if str(value).strip())
    )
    chart_names = tuple(
        dict.fromkeys(str(value).strip() for value in observed_charts if str(value).strip())
    )
    if not metric_names or not set(metric_names).issubset(local_metric_names):
        raise Ns3PhysicsBaselineError("云端可见指标必须来自本地最终指标清单")
    if not chart_names:
        raise Ns3PhysicsBaselineError("必须记录至少一个云端可见图表")
    note = str(evidence_note).strip()
    if not note:
        raise Ns3PhysicsBaselineError("SwanLab 复核必须包含证据说明")

    baseline = str(status["baseline"])
    seed = int(status["seed"])
    _validate_local_run_artifacts(
        output_dir,
        baseline,
        expected_verification_status="awaiting_manual_verification",
    )

    verification = {
        "schema_version": "flow_probe_ns3_physics_tracking_verification_v1",
        "status": "verified",
        "run_id": normalized_run_id,
        "run_url": manifest["run_url"],
        "metrics_visible": True,
        "charts_visible": True,
        "observed_metrics": list(metric_names),
        "observed_charts": list(chart_names),
        "evidence_note": note,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    run_identity = {
        name: status[name] for name in ("run_kind", "effective_max_epochs", "protocol_complete")
    }
    try:
        _write_json(output_dir / "tracking_verification.json", verification)
        metadata_path = output_dir / "swanlab_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise Ns3PhysicsBaselineError("SwanLab 元数据不是对象")
        metadata["tracking_verification_status"] = "verified"
        metadata["tracking_verified_at_utc"] = verification["verified_at_utc"]
        _write_json(metadata_path, metadata)
        _write_json(
            status_path,
            run_status_payload(
                status="finalizing",
                stage="tracking_verified",
                baseline=baseline,
                seed=seed,
                run_identity=run_identity,
                tracking_verified=True,
            ),
        )
        _write_json(
            output_dir / "file_sha256_manifest.json",
            _file_hash_manifest(output_dir, required_artifact_names(baseline)),
        )
        _validate_local_run_artifacts(
            output_dir,
            baseline,
            expected_verification_status="verified",
        )
        _write_json(
            status_path,
            run_status_payload(
                status="finished",
                stage="completed",
                baseline=baseline,
                seed=seed,
                run_identity=run_identity,
                tracking_verified=True,
            ),
        )
        _write_json(
            output_dir / "file_sha256_manifest.json",
            _file_hash_manifest(output_dir, required_artifact_names(baseline)),
        )
        _validate_local_run_artifacts(
            output_dir,
            baseline,
            expected_verification_status="verified",
        )
        return verification
    except BaseException:
        _write_json(
            status_path,
            run_status_payload(
                status="crashed",
                stage="tracking_verification_failed",
                baseline=baseline,
                seed=seed,
                run_identity=run_identity,
            ),
        )
        raise


def _tracking_settings(
    raw: Mapping[str, object],
    run_name: str,
    run_identity: Mapping[str, object],
) -> TrackingSettings:
    tracking = raw.get("tracking")
    if not isinstance(tracking, Mapping):
        raise Ns3PhysicsBaselineError("物理基线配置缺少 tracking")
    existing_tags = tracking.get("tags", ())
    if not isinstance(existing_tags, (list, tuple)):
        raise Ns3PhysicsBaselineError("SwanLab 标签必须为列表")
    identity_tags = (
        f"run-{run_identity['run_kind']}",
        f"epochs-{run_identity['effective_max_epochs']}",
        "protocol-complete" if run_identity["protocol_complete"] else "protocol-partial",
    )
    return TrackingSettings.from_mapping(
        {
            **tracking,
            "run_name": run_name,
            "tags": [*existing_tags, *identity_tags],
        }
    )


def run_tracked_ns3_physics_baseline(
    *,
    config_path: Path,
    baseline: str,
    seed: int,
    output_dir: Path,
    run_name: str,
    run_kind: str,
    smoke_max_epochs: int | None = None,
) -> dict[str, object]:
    """运行一个在线跟踪的星型物理基线并等待云端复核。"""
    if baseline not in BASELINES:
        raise Ns3PhysicsBaselineError(f"未知物理基线：{baseline}")
    if seed not in {42, 43, 44}:
        raise Ns3PhysicsBaselineError("模型随机种子只允许 42、43、44")
    raw, config = load_baseline_config(config_path)
    run_identity = build_run_identity(run_kind, config, smoke_max_epochs)
    if smoke_max_epochs is not None:
        config = BaselineTrainingConfig(**{**asdict(config), "max_epochs": smoke_max_epochs})
    data = raw.get("data")
    if not isinstance(data, Mapping) or not isinstance(data.get("expected_sha256"), Mapping):
        raise Ns3PhysicsBaselineError("物理基线配置缺少数据路径或哈希")
    if data.get("expected_topology") != EXPECTED_TOPOLOGY:
        raise Ns3PhysicsBaselineError("物理基线配置拓扑不是冻结星型拓扑")
    project_root = Path(config_path).resolve().parent.parent
    input_dir = Path(str(data["input_dir"]))
    if not input_dir.is_absolute():
        input_dir = project_root / input_dir
    audited = audit_star_split_inputs(input_dir, data["expected_sha256"])
    train = materialize_audited_split(audited, "train")
    validation = materialize_audited_split(audited, "validation")
    output_dir = validate_output_location(
        output_dir=output_dir,
        project_root=project_root,
        baseline=baseline,
        seed=seed,
        run_identity=run_identity,
    )
    output_dir.mkdir(parents=True, exist_ok=False)
    settings = _tracking_settings(raw, run_name, run_identity)
    device = torch.device("cpu") if baseline == "constant_state" else _resolve_device(config.device)

    paths = {name: output_dir / name for name in required_artifact_names(baseline)}
    snapshot = {
        **raw,
        "runtime": {
            "baseline": baseline,
            "seed": seed,
            "run_name": run_name,
            "smoke_max_epochs": smoke_max_epochs,
            **run_identity,
            "effective_training": asdict(config),
        },
    }
    paths["config_snapshot.yaml"].write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    _write_json(paths["environment.json"], _environment(device, config))
    _write_json(paths["input_manifest.json"], audited.input_manifest)
    _write_json(paths["split_audit.json"], audited.audit)
    _write_json(
        paths["run_status.json"],
        run_status_payload(
            status="running",
            stage="initialised",
            baseline=baseline,
            seed=seed,
            run_identity=run_identity,
        ),
    )
    metadata: dict[str, object] = {
        "workspace": settings.workspace,
        "project": settings.project,
        "phase": PHASE,
        "tracking_mode": settings.mode,
        "stage": raw["stage"],
        "status": raw["status"],
        "baseline": baseline,
        "seed": seed,
        "selection_split": "validation",
        "test_used_for_fit": False,
        "test_used_for_selection": False,
        "test_materialized_after_selection": False,
        **run_identity,
        "tracking_verification_status": "pending",
        "input_sha256": dict(data["expected_sha256"]),
    }
    _write_json(paths["swanlab_metadata.json"], metadata)
    data_files = {
        name.removesuffix(".json").removesuffix(".yaml").removesuffix(".gz"): path
        for name, path in paths.items()
        if name not in {"artifact_manifest.json", "console.log"}
    }

    try:
        with (
            capture_console_log(paths["console.log"]),
            swanlab_run(
                settings=settings,
                phase=PHASE,
                config=snapshot,
                artifact_dir=output_dir,
                data_files=data_files,
            ) as swanlab,
        ):
            print(f"开始星型 ns-3 物理基线：baseline={baseline} seed={seed}")
            train_masks = build_supervision_masks(train, seed)
            validation_masks = build_supervision_masks(validation, seed)
            history: tuple[Mapping[str, object], ...] = ()
            training_seconds = 0.0
            parameter_count = 0
            peak_gpu_memory: int | None = None
            selected_device = device.type
            best_epoch: int | None = None

            if baseline == "constant_state":

                def freeze_constant(
                    selected_train: PhysicsSplit, _selected_validation: PhysicsSplit
                ) -> object:
                    nonlocal training_seconds
                    started = time.perf_counter()
                    value = fit_constant_state(selected_train.state_targets, train_masks)
                    training_seconds = time.perf_counter() - started
                    return value

                selection, test = select_then_materialize_test(
                    audited=audited,
                    train=train,
                    validation=validation,
                    selector=freeze_constant,
                    selection_validator=lambda value: isinstance(value, np.ndarray)
                    and value.shape == (5,),
                )
                constant = np.asarray(selection, dtype=np.float32)
                _write_json(
                    paths["constant_state.json"],
                    {
                        "state": [float(value) for value in constant],
                        "fit_source": "masked_train_targets_only",
                        "train_mask_sha256": _array_sha256(train_masks),
                    },
                )
                started = time.perf_counter()
                validation_predictions = np.repeat(
                    constant[None, :], len(validation.sample_ids), axis=0
                )
                validation_inference_seconds = time.perf_counter() - started
                started = time.perf_counter()
                test_predictions = np.repeat(constant[None, :], len(test.sample_ids), axis=0)
                test_inference_seconds = time.perf_counter() - started
            else:
                selection, test = select_then_materialize_test(
                    audited=audited,
                    train=train,
                    validation=validation,
                    selector=lambda selected_train, selected_validation: train_selected_model(
                        train=selected_train,
                        validation=selected_validation,
                        baseline=baseline,
                        seed=seed,
                        config=config,
                        metric_logger=lambda values, step: swanlab.log(dict(values), step=step),
                    ),
                    selection_validator=lambda value: isinstance(value, SelectedModel),
                )
                if not isinstance(selection, SelectedModel):
                    raise Ns3PhysicsBaselineError("神经基线选择结果类型不合法")
                selected = selection
                history = selected.history
                training_seconds = selected.training_seconds
                parameter_count = selected.parameter_count
                peak_gpu_memory = selected.peak_gpu_memory_bytes
                selected_device = selected.selected_device
                best_epoch = selected.best_epoch
                torch.save(
                    {
                        "baseline": baseline,
                        "seed": seed,
                        "best_epoch": selected.best_epoch,
                        "state_dict": {
                            name: value.detach().cpu()
                            for name, value in selected.model.state_dict().items()
                        },
                        "input_transform": {
                            "mean": selected.transform.mean.tolist(),
                            "scale": selected.transform.scale.tolist(),
                        },
                        "model_input_fields": MODEL_INPUT_FIELDS,
                        "hidden_size": config.hidden_size,
                    },
                    paths["best_model.pt"],
                )
                validation_predictions, validation_inference_seconds = _predict_model(
                    selected.model,
                    selected.transform.apply(validation.features),
                    config.batch_size,
                    _resolve_device(selected.selected_device),
                )
                test_predictions, test_inference_seconds = _predict_model(
                    selected.model,
                    selected.transform.apply(test.features),
                    config.batch_size,
                    _resolve_device(selected.selected_device),
                )

            test_masks = build_supervision_masks(test, seed)
            metadata["test_materialized_after_selection"] = True
            _write_json(paths["swanlab_metadata.json"], metadata)
            _write_history(paths["training_history.jsonl"], history)
            evaluations = {
                "validation": evaluate_predictions(
                    validation, validation_predictions, validation_masks
                ),
                "test": evaluate_predictions(test, test_predictions, test_masks),
            }
            _write_predictions(paths["predictions.jsonl.gz"], evaluations)
            summary: dict[str, object] = {
                "schema_version": "flow_probe_ns3_physics_baseline_v1",
                "stage": raw["stage"],
                "status": raw["status"],
                "baseline": baseline,
                "seed": seed,
                **run_identity,
                "input_view": "four_windows_five_public_observations",
                "model_input_fields": list(MODEL_INPUT_FIELDS),
                "state_supervision_mode": config.state_supervision_mode,
                "lambda_state": config.lambda_state,
                "lambda_physics": config.lambda_physics if baseline == "standard_pinn" else 0.0,
                "physics_formula": (
                    "(scale*(q_hat_t1-q_hat_t0)-received+dequeued+"
                    "dropped_before+dropped_after)/configured_capacity_integral"
                ),
                "selection": {
                    "split": "validation",
                    "metric": config.selection_metric,
                    "best_epoch": best_epoch,
                    "test_used_for_fit": False,
                    "test_used_for_selection": False,
                    "test_materialized_after_selection": True,
                    "test_evaluated_once_after_selection": True,
                },
                "train_samples": len(train.sample_ids),
                "validation_samples": len(validation.sample_ids),
                "test_samples": len(test.sample_ids),
                "train_mask_sha256": _array_sha256(train_masks),
                "validation_mask_sha256": _array_sha256(validation_masks),
                "test_mask_sha256": _array_sha256(test_masks),
                "evaluations": {
                    name: dict(evaluation.metrics) for name, evaluation in evaluations.items()
                },
            }
            cost: dict[str, object] = {
                "schema_version": "flow_probe_ns3_physics_cost_v1",
                "baseline": baseline,
                "seed": seed,
                **run_identity,
                "selected_device": selected_device,
                "training_seconds": training_seconds,
                "training_samples_per_second": len(train.sample_ids)
                * max(len(history), 1)
                / max(training_seconds, 1e-12),
                "parameter_count": parameter_count,
                "peak_gpu_memory_bytes": peak_gpu_memory,
                "peak_process_rss_bytes": _peak_rss_bytes(),
                "validation_inference_seconds": validation_inference_seconds,
                "validation_samples_per_second": len(validation.sample_ids)
                / max(validation_inference_seconds, 1e-12),
                "test_inference_seconds": test_inference_seconds,
                "test_samples_per_second": len(test.sample_ids)
                / max(test_inference_seconds, 1e-12),
            }
            _write_json(paths["summary.json"], summary)
            _write_json(paths["cost.json"], cost)
            final_metrics = {
                **flatten_scalar_metrics(summary, prefix=PHASE),
                **flatten_scalar_metrics(cost, prefix="cost"),
            }
            final_step = final_tracking_step(history, best_epoch)
            swanlab.log(final_metrics, step=final_step)
            _write_json(
                paths["swanlab_metrics.json"], {"step": final_step, "metrics": final_metrics}
            )
            _write_json(
                paths["run_status.json"],
                run_status_payload(
                    status="finalizing",
                    stage="local_artifacts_written",
                    baseline=baseline,
                    seed=seed,
                    run_identity=run_identity,
                ),
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        manifest_path = paths["artifact_manifest.json"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata.update(
            {
                "run_id": manifest["run_id"],
                "run_url": manifest["run_url"],
                "tracking_verification_status": "awaiting_manual_verification",
            }
        )
        _write_json(paths["swanlab_metadata.json"], metadata)
        _write_json(
            paths["tracking_verification.json"],
            {
                "schema_version": "flow_probe_ns3_physics_tracking_verification_v1",
                "status": "awaiting_manual_verification",
                "run_id": manifest["run_id"],
                "run_url": manifest["run_url"],
                "metrics_visible": False,
                "charts_visible": False,
                "observed_metrics": [],
                "observed_charts": [],
                "evidence_note": None,
                "verified_at_utc": None,
            },
        )
        _write_json(
            paths["run_status.json"],
            run_status_payload(
                status="awaiting_tracking_verification",
                stage="tracking_pending",
                baseline=baseline,
                seed=seed,
                run_identity=run_identity,
            ),
        )
        _write_json(
            paths["file_sha256_manifest.json"],
            _file_hash_manifest(output_dir, required_artifact_names(baseline)),
        )
        _validate_local_run_artifacts(
            output_dir,
            baseline,
            expected_verification_status="awaiting_manual_verification",
        )
        return dict(manifest)
    except BaseException:
        _write_json(
            paths["run_status.json"],
            run_status_payload(
                status="crashed",
                stage="crashed",
                baseline=baseline,
                seed=seed,
                run_identity=run_identity,
            ),
        )
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行并核验星型 ns-3 同协议物理机理基线")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="运行单个物理基线")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--baseline", choices=BASELINES, required=True)
    run_parser.add_argument("--seed", choices=(42, 43, 44), type=int, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    run_parser.add_argument("--run-name", required=True)
    run_parser.add_argument("--run-kind", choices=("formal", "smoke"), required=True)
    run_parser.add_argument("--smoke-max-epochs", type=int)
    verify_parser = commands.add_parser("verify-tracking", help="记录 SwanLab 指标与图表人工复核")
    verify_parser.add_argument("--output-dir", type=Path, required=True)
    verify_parser.add_argument("--run-id", required=True)
    verify_parser.add_argument("--observed-metric", action="append", required=True)
    verify_parser.add_argument("--observed-chart", action="append", required=True)
    verify_parser.add_argument("--evidence-note", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        run_tracked_ns3_physics_baseline(
            config_path=args.config,
            baseline=args.baseline,
            seed=args.seed,
            output_dir=args.output_dir,
            run_name=args.run_name,
            run_kind=args.run_kind,
            smoke_max_epochs=args.smoke_max_epochs,
        )
    else:
        verification = finalize_tracking_verification(
            output_dir=args.output_dir,
            run_id=args.run_id,
            observed_metrics=args.observed_metric,
            observed_charts=args.observed_chart,
            evidence_note=args.evidence_note,
        )
        print(json.dumps(verification, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
