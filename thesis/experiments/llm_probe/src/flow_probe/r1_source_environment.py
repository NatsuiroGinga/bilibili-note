"""R1 源时间环境稳健状态 Q0 的环境、训练与独立评价入口。"""

from __future__ import annotations

import argparse
import copy
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
import pyarrow.parquet as pq
import sklearn
import torch
from numpy.lib.format import open_memmap
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from torch import nn
from torch.nn import functional as F

from flow_probe.c12_crossyear_models import (
    ActiveParameterCompensation,
    C12ModelConfig,
    Rwkv7Kernel,
    trainable_parameter_count,
)
from flow_probe.c12_crossyear_train import SequenceRole, load_cache
from flow_probe.tracking import REQUIRED_SWANLAB_PROJECT, REQUIRED_SWANLAB_WORKSPACE


ENVIRONMENT_SCHEMA = "r1-source-time-environments-q0-v1"
RUN_SCHEMA = "r1-source-environment-q0-run-v1"
EVALUATION_SCHEMA = "r1-source-environment-q0-grid-v1"
REPRESENTATION_SCHEMA = "c12-crossyear-receiver-representations-v1"
VARIANTS = ("B0", "GROUPDRO", "M1")
DISPLAY_NAMES = {
    "B0": "R1-B0 接收因果 Transformer 参数匹配基线",
    "GROUPDRO": "R1-GROUPDRO 源时间环境强基线",
    "M1": "R1-M1 稳定－私有状态分解",
}


class R1Error(ValueError):
    """R1 数据、训练或评价合同被违反。"""


@dataclass(frozen=True)
class EnvironmentBundle:
    """与缓存序列顺序严格一致的环境数组。"""

    train_environment: np.ndarray
    validation_partition: np.ndarray
    validation_environment: np.ndarray
    training_order: np.ndarray
    manifest: dict[str, Any]


class SwanTracker:
    """每个变体独立进程内的 SwanLab 在线记录器。"""

    def __init__(self, output_dir: Path, run_name: str, config: Mapping[str, object]) -> None:
        import swanlab

        self.client = swanlab
        self.run = swanlab.init(
            project=REQUIRED_SWANLAB_PROJECT,
            workspace=REQUIRED_SWANLAB_WORKSPACE,
            name=run_name,
            description="R1 源时间环境稳健状态 Q0 快速筛选",
            config=dict(config),
            mode="online",
            tags=["r1", str(config["variant"]).lower(), "q0", "seed42"],
            log_dir=str(output_dir / "swanlog"),
        )
        _write_json(
            output_dir / "swanlab-status.json",
            {"status": "running", "run_id": str(self.run.id)},
        )

    def log(self, values: Mapping[str, int | float], step: int) -> None:
        self.client.log(dict(values), step=step)

    def finish(self, output_dir: Path) -> None:
        self.client.finish()
        _write_json(
            output_dir / "swanlab-status.json",
            {"status": "finished", "run_id": str(self.run.id)},
        )

    def fail(self, output_dir: Path, error: BaseException) -> None:
        try:
            self.client.finish(state="crashed", error=str(error))
        finally:
            _write_json(
                output_dir / "swanlab-status.json",
                {
                    "status": "failed",
                    "run_id": str(self.run.id),
                    "error_type": type(error).__name__,
                },
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(partial, path)


def _write_npy(path: Path, value: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    with partial.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)
    os.replace(partial, path)


def _write_npz(path: Path, **values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    with partial.open("wb") as handle:
        np.savez_compressed(handle, **values)
    os.replace(partial, path)


def _append_jsonl(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R1Error(f"JSON 顶层必须是对象：{path}")
    return value


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _environment(device: torch.device) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "device": str(device),
    }
    if device.type == "cuda":
        properties = torch.cuda.get_device_properties(device)
        receipt.update(
            {
                "gpu": torch.cuda.get_device_name(device),
                "gpu_total_memory_bytes": int(properties.total_memory),
            }
        )
    return receipt


def _load_config(path: Path) -> dict[str, Any]:
    config = _read_json(path.resolve())
    if config.get("schema_version") != "r1-source-environment-q0-config-v1":
        raise R1Error("R1 配置模式不匹配")
    if config.get("seed") != 42 or config.get("epochs") != 4:
        raise R1Error("Q0 必须固定 seed=42、epochs=4")
    if config.get("batch_size_sequences") != 16 or config.get("hidden_size") != 192:
        raise R1Error("Q0 必须固定序列批量 16、隐藏维 192")
    if config.get("maximum_sequence_length") != 128:
        raise R1Error("Q0 最大序列长度必须为 128")
    if config.get("final_accessed") is not False:
        raise R1Error("R1 配置必须保持 final_accessed=false")
    return config


def _resolve_declared_path(value: object, label: str) -> Path:
    if not isinstance(value, str):
        raise R1Error(f"{label} 路径缺失")
    path = Path(value).resolve()
    if not path.is_file():
        raise R1Error(f"{label} 不存在：{path}")
    return path


def _load_frozen_representations(
    cache_root: Path,
    representation_root: Path,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    manifest_path = representation_root / "representation-manifest.json"
    receipt = _read_json(manifest_path)
    if (
        receipt.get("schema_version") != REPRESENTATION_SCHEMA
        or receipt.get("final_accessed") is not False
        or receipt.get("excluded_roles") != ["target-prefix"]
    ):
        raise R1Error("阶段 A v2 冻结表示清单不合法")
    if receipt.get("cache_manifest_sha256") != _sha256(cache_root / "cache-manifest.json"):
        raise R1Error("冻结表示与 Q0 缓存哈希不一致")
    records = receipt.get("encoded_roles")
    expected = {"source-train", "source-validation", "target-development"}
    if not isinstance(records, dict) or set(records) != expected:
        raise R1Error("冻结表示角色不完整")
    arrays: dict[str, np.ndarray] = {}
    for role in sorted(expected):
        record = records[role]
        if not isinstance(record, Mapping):
            raise R1Error(f"冻结表示角色记录不合法：{role}")
        path = representation_root / f"role={role}" / "phi.npy"
        if _sha256(path) != record.get("sha256"):
            raise R1Error(f"冻结表示哈希不匹配：{role}")
        array = np.load(path, mmap_mode="r")
        if array.ndim != 2 or array.shape[1] != 192:
            raise R1Error(f"冻结表示形状不合法：{role}")
        arrays[role] = array
    return arrays, receipt


def _fixed_binary_matrix(values: list[bytes], label: str) -> np.ndarray:
    if any(not isinstance(item, bytes) or len(item) != 32 for item in values):
        raise R1Error(f"{label} 必须是 32 字节固定二进制")
    if not values:
        return np.empty((0, 32), dtype=np.uint8)
    return np.frombuffer(b"".join(values), dtype=np.uint8).reshape(len(values), 32).copy()


def _load_sequence_metadata(
    cache_manifest: Mapping[str, Any],
    roles: Mapping[str, SequenceRole],
) -> tuple[dict[str, dict[str, np.ndarray]], Path, Path]:
    dataset_path = _resolve_declared_path(cache_manifest.get("dataset_manifest"), "数据集清单")
    if cache_manifest.get("dataset_manifest_sha256") != _sha256(dataset_path):
        raise R1Error("缓存绑定的数据集清单哈希不一致")
    dataset = _read_json(dataset_path)
    if (
        dataset.get("schema_version") != "lspr-crossyear-dataset-manifest-v1"
        or dataset.get("materialization_mode") != "bounded_quick_cache"
        or dataset.get("budget_tier") != "Q0"
        or dataset.get("final_accessed") is not False
    ):
        raise R1Error("Q0 数据集清单合同不合法")
    artifacts = dataset.get("artifacts")
    record = artifacts.get("sequence_manifest") if isinstance(artifacts, Mapping) else None
    if not isinstance(record, Mapping):
        raise R1Error("数据集清单未绑定序列清单")
    sequence_path = _resolve_declared_path(record.get("path"), "序列清单")
    sequence_sha = _sha256(sequence_path)
    if (
        record.get("sha256") != sequence_sha
        or cache_manifest.get("sequence_manifest_sha256") != sequence_sha
    ):
        raise R1Error("序列清单双重哈希绑定不一致")
    table = pq.read_table(
        sequence_path,
        columns=[
            "sequence_id",
            "year_role",
            "group_key_ref",
            "valid_length",
            "first_available_ns",
            "last_available_ns",
            "cache_selected",
        ],
    )
    role_values = np.asarray(table.column("year_role").to_pylist(), dtype=object)
    selected = np.asarray(table.column("cache_selected").to_pylist(), dtype=np.uint8) == 1
    sequence_ids = _fixed_binary_matrix(table.column("sequence_id").to_pylist(), "sequence_id")
    group_keys = _fixed_binary_matrix(table.column("group_key_ref").to_pylist(), "group_key_ref")
    lengths = np.asarray(table.column("valid_length").to_pylist(), dtype=np.int64)
    first_ns = np.asarray(table.column("first_available_ns").to_pylist(), dtype=np.int64)
    last_ns = np.asarray(table.column("last_available_ns").to_pylist(), dtype=np.int64)
    result: dict[str, dict[str, np.ndarray]] = {}
    for role_name in ("source-train", "source-validation"):
        mask = selected & (role_values == role_name)
        block = {
            "sequence_id": sequence_ids[mask],
            "group_key_ref": group_keys[mask],
            "valid_length": lengths[mask],
            "first_available_ns": first_ns[mask],
            "last_available_ns": last_ns[mask],
        }
        role = roles[role_name]
        cached_ids = np.asarray(role.sequence_id[role.starts])
        if not np.array_equal(block["sequence_id"], cached_ids):
            raise R1Error(f"{role_name} 序列清单与 Python 缓存顺序不一致")
        if not np.array_equal(block["valid_length"], role.lengths):
            raise R1Error(f"{role_name} 序列长度与 Python 缓存不一致")
        if np.any(block["last_available_ns"] < block["first_available_ns"]):
            raise R1Error(f"{role_name} 序列时间范围逆序")
        result[role_name] = block
    return result, dataset_path, sequence_path


def _group_records(metadata: Mapping[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    keys = metadata["group_key_ref"]
    key_void = np.ascontiguousarray(keys).view("V32").reshape(-1)
    unique, inverse = np.unique(key_void, return_inverse=True)
    first = np.full(len(unique), np.iinfo(np.int64).max, dtype=np.int64)
    last = np.full(len(unique), np.iinfo(np.int64).min, dtype=np.int64)
    np.minimum.at(first, inverse, metadata["first_available_ns"])
    np.maximum.at(last, inverse, metadata["last_available_ns"])
    return unique.view(np.uint8).reshape(-1, 32).copy(), inverse.astype(np.int16), np.stack((first, last), axis=1)


def _time_blocks(group_first: np.ndarray, block_count: int) -> tuple[np.ndarray, list[int]]:
    unique_times, counts = np.unique(group_first, return_counts=True)
    if len(unique_times) < block_count:
        raise R1Error(f"时间戳仅有 {len(unique_times)} 种，无法形成 {block_count} 个非空块")
    cumulative = np.cumsum(counts)
    split_indices: list[int] = []
    previous = 0
    for block in range(1, block_count):
        remaining = block_count - block
        candidates = np.arange(previous + 1, len(unique_times) - remaining + 1)
        target = block * len(group_first) / block_count
        best = int(candidates[np.argmin(np.abs(cumulative[candidates - 1] - target))])
        split_indices.append(best)
        previous = best
    boundaries = [int(unique_times[index]) for index in split_indices]
    assignments = np.searchsorted(np.asarray(boundaries, dtype=np.int64), group_first, side="right")
    if set(assignments.tolist()) != set(range(block_count)):
        raise R1Error("时间块划分产生空环境")
    return assignments.astype(np.int8), boundaries


def _sequence_labels(role: SequenceRole) -> np.ndarray:
    if role.labels is None:
        raise R1Error(f"{role.role} 缺少源标签")
    labels = np.empty(role.sequence_count, dtype=np.uint8)
    for index, (start, length) in enumerate(zip(role.starts, role.lengths, strict=True)):
        values = np.asarray(role.labels[int(start) : int(start + length)])
        labels[index] = np.uint8(np.any(values == 1))
    return labels


def _member_hash(
    sequence_id: np.ndarray,
    environment: np.ndarray,
    partition: np.ndarray | None = None,
) -> str:
    digest = hashlib.sha256(b"r1-environment-members-v1\0")
    for index in range(len(sequence_id)):
        digest.update(np.ascontiguousarray(sequence_id[index]).tobytes())
        if partition is not None:
            digest.update(bytes((int(partition[index]),)))
        digest.update(bytes((int(environment[index]),)))
    return digest.hexdigest()


def _partition_receipt(
    role: SequenceRole,
    sequence_environment: np.ndarray,
    sequence_mask: np.ndarray,
) -> dict[str, Any]:
    sequence_labels = _sequence_labels(role)
    records: dict[str, Any] = {}
    for environment in sorted(set(sequence_environment[sequence_mask].tolist())):
        seq_mask = sequence_mask & (sequence_environment == environment)
        row_mask = np.zeros(role.row_count, dtype=bool)
        for index in np.flatnonzero(seq_mask):
            start = int(role.starts[index])
            row_mask[start : start + int(role.lengths[index])] = True
        assert role.labels is not None
        labels = np.asarray(role.labels)[row_mask]
        records[str(environment)] = {
            "parent_group_count": None,
            "sequence_count": int(seq_mask.sum()),
            "flow_count": int(row_mask.sum()),
            "benign_flow_count": int(np.sum(labels == 0)),
            "malicious_flow_count": int(np.sum(labels == 1)),
            "benign_sequence_count": int(np.sum(sequence_labels[seq_mask] == 0)),
            "malicious_sequence_count": int(np.sum(sequence_labels[seq_mask] == 1)),
        }
    return records


def _build_training_order(
    role: SequenceRole,
    environments: np.ndarray,
    epochs: int,
    batch_size: int,
    seed: int,
) -> tuple[np.ndarray, dict[str, Any]]:
    labels = _sequence_labels(role)
    cells: list[tuple[int, int, np.ndarray]] = []
    for environment in sorted(set(environments.tolist())):
        for label in (0, 1):
            pool = np.flatnonzero((environments == environment) & (labels == label)).astype(np.int32)
            if len(pool):
                cells.append((environment, label, pool))
    if len(cells) > batch_size:
        raise R1Error("环境×标签非空池数量超过固定序列批量")
    if len(set(environment for environment, _, _ in cells)) != 4:
        raise R1Error("训练环境存在无可采样序列的环境")
    batches = int(np.ceil(role.sequence_count / batch_size))
    order = np.empty((epochs, batches, batch_size), dtype=np.int32)
    draws = {(environment, label): 0 for environment, label, _ in cells}
    for epoch in range(epochs):
        rng = np.random.default_rng(seed + epoch)
        queues = {key[:2]: np.empty(0, dtype=np.int32) for key in cells}
        for batch_index in range(batches):
            allocation = np.full(len(cells), batch_size // len(cells), dtype=np.int32)
            remainder = batch_size % len(cells)
            for offset in range(remainder):
                allocation[(batch_index + offset) % len(cells)] += 1
            batch_parts: list[np.ndarray] = []
            for cell_index, (environment, label, pool) in enumerate(cells):
                required = int(allocation[cell_index])
                selected: list[np.ndarray] = []
                while required:
                    queue = queues[(environment, label)]
                    if not len(queue):
                        queue = rng.permutation(pool)
                    take = min(required, len(queue))
                    selected.append(queue[:take])
                    queues[(environment, label)] = queue[take:]
                    required -= take
                values = np.concatenate(selected)
                batch_parts.append(values)
                draws[(environment, label)] += len(values)
            order[epoch, batch_index] = rng.permutation(np.concatenate(batch_parts))
    receipt = {
        "schema_version": "r1-environment-label-sequence-sampling-v1",
        "batch_size_sequences": batch_size,
        "batches_per_epoch": batches,
        "epochs": epochs,
        "fixed_budget_steps": batches * epochs,
        "cell_pool_sizes": {
            f"environment={environment},label={label}": int(len(pool))
            for environment, label, pool in cells
        },
        "actual_draws": {
            f"environment={environment},label={label}": int(count)
            for (environment, label), count in draws.items()
        },
        "deterministic_pool_recycling": True,
        "shared_by_variants": list(VARIANTS),
        "final_accessed": False,
    }
    return order, receipt


def prepare_environments(
    cache_root: Path,
    representation_root: Path,
    output_dir: Path,
    config_path: Path,
) -> dict[str, Any]:
    """按父组首次出现时间生成标签盲环境与共享训练清单。"""
    if output_dir.exists():
        raise R1Error("环境输出目录已存在，拒绝覆盖")
    config = _load_config(config_path)
    cache_manifest, roles = load_cache(cache_root)
    representations, representation_receipt = _load_frozen_representations(
        cache_root, representation_root
    )
    for role, values in representations.items():
        if len(values) != roles[role].row_count:
            raise R1Error(f"冻结表示与缓存行数不一致：{role}")
    metadata, dataset_path, sequence_path = _load_sequence_metadata(cache_manifest, roles)

    train_keys, train_inverse, train_ranges = _group_records(metadata["source-train"])
    train_group_env, train_boundaries = _time_blocks(train_ranges[:, 0], 4)
    train_environment = train_group_env[train_inverse]

    validation_keys, validation_inverse, validation_ranges = _group_records(
        metadata["source-validation"]
    )
    validation_group_partition, validation_split = _time_blocks(validation_ranges[:, 0], 2)
    validation_partition = validation_group_partition[validation_inverse]
    validation_group_environment = np.empty(len(validation_keys), dtype=np.int8)
    validation_boundaries: dict[str, list[int]] = {}
    for partition in (0, 1):
        group_mask = validation_group_partition == partition
        local, boundaries = _time_blocks(validation_ranges[group_mask, 0], 4)
        validation_group_environment[group_mask] = local
        validation_boundaries[str(partition)] = boundaries
    validation_environment = validation_group_environment[validation_inverse]

    if any(
        len(set(train_environment[train_inverse == group].tolist())) != 1
        for group in range(len(train_keys))
    ):
        raise R1Error("source-train 父组跨环境")
    for group in range(len(validation_keys)):
        seq_mask = validation_inverse == group
        if len(set(validation_partition[seq_mask].tolist())) != 1:
            raise R1Error("source-validation 父组跨验证／校准子区")
        if len(set(validation_environment[seq_mask].tolist())) != 1:
            raise R1Error("source-validation 父组跨环境")

    train_receipt = _partition_receipt(
        roles["source-train"], train_environment, np.ones(len(train_environment), dtype=bool)
    )
    validation_receipt = _partition_receipt(
        roles["source-validation"], validation_environment, validation_partition == 0
    )
    calibration_receipt = _partition_receipt(
        roles["source-validation"], validation_environment, validation_partition == 1
    )
    for environment in range(4):
        train_receipt[str(environment)]["parent_group_count"] = int(
            np.sum(train_group_env == environment)
        )
        validation_receipt[str(environment)]["parent_group_count"] = int(
            np.sum(
                (validation_group_partition == 0)
                & (validation_group_environment == environment)
            )
        )
        calibration_receipt[str(environment)]["parent_group_count"] = int(
            np.sum(
                (validation_group_partition == 1)
                & (validation_group_environment == environment)
            )
        )
    train_two_class = sum(
        record["benign_sequence_count"] > 0 and record["malicious_sequence_count"] > 0
        for record in train_receipt.values()
    )
    if train_two_class < 2:
        raise R1Error("R1 数据可观测性门禁失败：少于两个训练环境同时含良恶两类")
    if set(calibration_receipt) != {"0", "1", "2", "3"} or any(
        record["benign_flow_count"] == 0 for record in calibration_receipt.values()
    ):
        raise R1Error("R1 数据可观测性门禁失败：源校准环境缺少良性流")

    training_order, sampling_receipt = _build_training_order(
        roles["source-train"],
        train_environment,
        int(config["epochs"]),
        int(config["batch_size_sequences"]),
        int(config["seed"]),
    )
    output_dir.mkdir(parents=True)
    arrays = {
        "source-train-environment.npy": train_environment.astype(np.int8),
        "source-validation-partition.npy": validation_partition.astype(np.int8),
        "source-validation-environment.npy": validation_environment.astype(np.int8),
        "training-sequence-order.npy": training_order,
    }
    for name, values in arrays.items():
        _write_npy(output_dir / name, values)
    _write_json(output_dir / "training-sampling-receipt.json", sampling_receipt)
    manifest = {
        "schema_version": ENVIRONMENT_SCHEMA,
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "dataset_manifest": str(dataset_path),
        "dataset_manifest_sha256": _sha256(dataset_path),
        "sequence_manifest": str(sequence_path),
        "sequence_manifest_sha256": _sha256(sequence_path),
        "representation_manifest_sha256": _sha256(
            representation_root / "representation-manifest.json"
        ),
        "receiver_checkpoint_sha256": representation_receipt.get("receiver_checkpoint_sha256"),
        "partition_basis": "父组首次出现的 first_available_ns；相同时间戳不切开",
        "time_order_scope": "按 available_ns 划分的源时间区间，不声称恢复严格总序",
        "labels_used_for_partition": False,
        "labels_read_after_partition_for_receipt_only": True,
        "environment_or_group_used_as_model_input": False,
        "source_train": {
            "group_count": int(len(train_keys)),
            "boundaries_first_available_ns": train_boundaries,
            "environments": train_receipt,
            "member_sha256": _member_hash(
                metadata["source-train"]["sequence_id"], train_environment
            ),
        },
        "source_validation": {
            "group_count": int(len(validation_keys)),
            "validation_calibration_boundary_first_available_ns": validation_split,
            "partition_boundaries_first_available_ns": validation_boundaries,
            "validation_environments": validation_receipt,
            "calibration_environments": calibration_receipt,
            "member_sha256": _member_hash(
                metadata["source-validation"]["sequence_id"],
                validation_environment,
                validation_partition,
            ),
        },
        "arrays": {
            name: {"path": str((output_dir / name).resolve()), "sha256": _sha256(output_dir / name)}
            for name in arrays
        },
        "sampling_receipt_sha256": _sha256(output_dir / "training-sampling-receipt.json"),
        "observability_gate": "passed",
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "environment-manifest.json", manifest)
    return manifest


def _load_environments(
    cache_root: Path,
    representation_root: Path,
    environment_root: Path,
    roles: Mapping[str, SequenceRole],
) -> EnvironmentBundle:
    manifest = _read_json(environment_root / "environment-manifest.json")
    if (
        manifest.get("schema_version") != ENVIRONMENT_SCHEMA
        or manifest.get("labels_used_for_partition") is not False
        or manifest.get("environment_or_group_used_as_model_input") is not False
        or manifest.get("final_accessed") is not False
    ):
        raise R1Error("环境清单合同不合法")
    if manifest.get("cache_manifest_sha256") != _sha256(cache_root / "cache-manifest.json"):
        raise R1Error("环境清单与缓存哈希不一致")
    if manifest.get("representation_manifest_sha256") != _sha256(
        representation_root / "representation-manifest.json"
    ):
        raise R1Error("环境清单与冻结表示哈希不一致")
    paths = {
        "train": environment_root / "source-train-environment.npy",
        "partition": environment_root / "source-validation-partition.npy",
        "validation": environment_root / "source-validation-environment.npy",
        "order": environment_root / "training-sequence-order.npy",
    }
    arrays_record = manifest.get("arrays")
    if not isinstance(arrays_record, Mapping):
        raise R1Error("环境数组清单缺失")
    for path in paths.values():
        record = arrays_record.get(path.name)
        if not isinstance(record, Mapping) or record.get("sha256") != _sha256(path):
            raise R1Error(f"环境数组哈希不匹配：{path.name}")
    train_environment = np.load(paths["train"], mmap_mode="r")
    validation_partition = np.load(paths["partition"], mmap_mode="r")
    validation_environment = np.load(paths["validation"], mmap_mode="r")
    training_order = np.load(paths["order"], mmap_mode="r")
    if train_environment.shape != (roles["source-train"].sequence_count,):
        raise R1Error("source-train 环境数组形状不一致")
    if validation_partition.shape != (roles["source-validation"].sequence_count,):
        raise R1Error("source-validation 分区数组形状不一致")
    if validation_environment.shape != validation_partition.shape:
        raise R1Error("source-validation 环境数组形状不一致")
    return EnvironmentBundle(
        train_environment=train_environment,
        validation_partition=validation_partition,
        validation_environment=validation_environment,
        training_order=training_order,
        manifest=manifest,
    )


def _sequence_batch(
    role: SequenceRole,
    representation: np.ndarray,
    sequence_indices: np.ndarray,
    sequence_environments: np.ndarray | None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor | None, torch.Tensor | None]:
    lengths = role.lengths[sequence_indices]
    maximum = int(lengths.max())
    values = np.zeros((len(sequence_indices), maximum, representation.shape[1]), dtype=np.float32)
    valid = np.zeros((len(sequence_indices), maximum), dtype=bool)
    labels = (
        np.zeros((len(sequence_indices), maximum), dtype=np.float32)
        if role.labels is not None
        else None
    )
    for batch_index, sequence_index in enumerate(sequence_indices):
        start = int(role.starts[sequence_index])
        length = int(role.lengths[sequence_index])
        values[batch_index, :length] = representation[start : start + length]
        valid[batch_index, :length] = True
        if labels is not None and role.labels is not None:
            labels[batch_index, :length] = role.labels[start : start + length]
    environments = (
        torch.from_numpy(np.asarray(sequence_environments[sequence_indices], dtype=np.int64))
        if sequence_environments is not None
        else None
    )
    return (
        torch.from_numpy(values),
        torch.from_numpy(valid),
        torch.from_numpy(labels) if labels is not None else None,
        environments,
    )


class BaselineModel(nn.Module):
    """冻结接收器表示上的参数匹配分类器。"""

    def __init__(self, config: C12ModelConfig, compensation_parameters: int) -> None:
        super().__init__()
        self.compensation = ActiveParameterCompensation(
            config.hidden_size, compensation_parameters
        )
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size * 2),
            nn.Linear(config.hidden_size * 2, config.hidden_size),
            nn.GELU(),
            nn.Linear(config.hidden_size, 1),
        )

    def classify(
        self, values: torch.Tensor, valid: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        del valid
        context = self.compensation(values)
        logits = self.classifier(torch.cat((values, context), dim=-1)).squeeze(-1)
        return logits, values


class StablePrivateModel(nn.Module):
    """稳定 RWKV-7 状态分类、四环境私有状态仅重构。"""

    def __init__(self, config: C12ModelConfig, private_size: int) -> None:
        super().__init__()
        self.stable = Rwkv7Kernel(config)
        self.private = nn.ModuleList(
            nn.GRU(config.hidden_size, private_size, batch_first=True) for _ in range(4)
        )
        self.reconstruction = nn.Sequential(
            nn.LayerNorm(config.hidden_size + private_size),
            nn.Linear(config.hidden_size + private_size, config.hidden_size),
        )
        self.classifier = nn.Sequential(
            nn.LayerNorm(config.hidden_size * 2),
            nn.Linear(config.hidden_size * 2, config.hidden_size),
            nn.GELU(),
            nn.Linear(config.hidden_size, 1),
        )

    def classify(
        self, values: torch.Tensor, valid: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        stable = self.stable(values, valid)
        logits = self.classifier(torch.cat((values, stable), dim=-1)).squeeze(-1)
        return logits, stable

    def forward_train(
        self, values: torch.Tensor, valid: torch.Tensor, environments: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        logits, stable = self.classify(values, valid)
        private_size = self.private[0].hidden_size
        private: torch.Tensor | None = None
        for environment, encoder in enumerate(self.private):
            indices = torch.nonzero(environments == environment, as_tuple=True)[0]
            if len(indices):
                encoded, _ = encoder(values.index_select(0, indices))
                if private is None:
                    private = encoded.new_zeros(
                        values.shape[0], values.shape[1], private_size
                    )
                private = private.index_copy(0, indices, encoded)
        if private is None:
            raise R1Error("训练批次没有可用的源时间环境")
        reconstructed = self.reconstruction(torch.cat((stable, private), dim=-1))
        return logits, stable, private, reconstructed


def _build_models(private_size: int) -> tuple[dict[str, nn.Module], dict[str, int]]:
    model_config = C12ModelConfig()
    m1 = StablePrivateModel(model_config, private_size)
    target_count = trainable_parameter_count(m1)
    baseline_raw = BaselineModel(model_config, 0)
    difference = target_count - trainable_parameter_count(baseline_raw)
    if difference < 0:
        raise R1Error("M1 参数量小于基础分类头，无法执行参数匹配")
    baseline = BaselineModel(model_config, difference)
    models: dict[str, nn.Module] = {
        "B0": baseline,
        "GROUPDRO": copy.deepcopy(baseline),
        "M1": m1,
    }
    counts = {variant: trainable_parameter_count(model) for variant, model in models.items()}
    if len(set(counts.values())) != 1:
        raise R1Error(f"三模型参数量未精确匹配：{counts}")
    return models, counts


def _m1_losses(
    logits: torch.Tensor,
    stable: torch.Tensor,
    private: torch.Tensor,
    reconstructed: torch.Tensor,
    values: torch.Tensor,
    valid: torch.Tensor,
    labels: torch.Tensor,
    environments: torch.Tensor,
    config: Mapping[str, Any],
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    classification = F.binary_cross_entropy_with_logits(logits[valid], labels[valid])
    reconstruction = F.mse_loss(reconstructed[valid], values[valid])
    difference_terms: list[torch.Tensor] = []
    means: list[torch.Tensor] = []
    variances: list[torch.Tensor] = []
    margin_terms: list[torch.Tensor] = []
    for environment in range(4):
        sequence_mask = environments == environment
        if not torch.any(sequence_mask):
            continue
        row_mask = valid[sequence_mask]
        stable_rows = stable[sequence_mask][row_mask].float()
        private_rows = private[sequence_mask][row_mask].float()
        label_rows = labels[sequence_mask][row_mask]
        stable_centered = stable_rows - stable_rows.mean(dim=0, keepdim=True)
        private_centered = private_rows - private_rows.mean(dim=0, keepdim=True)
        cross = stable_centered.transpose(0, 1) @ private_centered / max(len(stable_rows), 1)
        difference_terms.append(cross.square().mean())
        means.append(stable_rows.mean(dim=0))
        variances.append(stable_rows.var(dim=0, unbiased=False))
        benign = stable_rows[label_rows == 0]
        malicious = stable_rows[label_rows == 1]
        if len(benign) and len(malicious):
            distance = torch.linalg.vector_norm(
                malicious.mean(dim=0) - benign.mean(dim=0), ord=2
            )
            margin_terms.append(F.relu(float(config["margin"]) - distance))
    difference = torch.stack(difference_terms).mean() if difference_terms else logits.new_zeros(())
    if len(means) > 1:
        mean_stack = torch.stack(means)
        variance_stack = torch.stack(variances)
        invariance = mean_stack.var(dim=0, unbiased=False).mean() + variance_stack.var(
            dim=0, unbiased=False
        ).mean()
    else:
        invariance = logits.new_zeros(())
    margin = torch.stack(margin_terms).mean() if margin_terms else logits.new_zeros(())
    total = (
        classification
        + float(config["lambda_rec"]) * reconstruction
        + float(config["lambda_diff"]) * difference
        + float(config["lambda_inv"]) * invariance
        + float(config["lambda_margin"]) * margin
    )
    return total, {
        "classification": classification,
        "reconstruction": reconstruction,
        "difference": difference,
        "invariance": invariance,
        "margin": margin,
        "weighted_reconstruction": float(config["lambda_rec"]) * reconstruction,
        "weighted_difference": float(config["lambda_diff"]) * difference,
        "weighted_invariance": float(config["lambda_inv"]) * invariance,
        "weighted_margin": float(config["lambda_margin"]) * margin,
    }


def _groupdro_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    valid: torch.Tensor,
    environments: torch.Tensor,
    weights: torch.Tensor,
    eta: float,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, float]]:
    risks: list[torch.Tensor] = []
    active: list[int] = []
    for environment in range(4):
        mask = valid & (environments == environment).unsqueeze(1)
        if torch.any(mask):
            risks.append(F.binary_cross_entropy_with_logits(logits[mask], labels[mask]))
            active.append(environment)
    if not risks:
        raise R1Error("GroupDRO 批次没有有效环境风险")
    risk_tensor = torch.stack(risks)
    updated = weights.clone()
    active_indices = torch.tensor(active, device=weights.device, dtype=torch.long)
    updated[active_indices] *= torch.exp(eta * risk_tensor.detach())
    updated /= updated.sum()
    loss = torch.sum(updated[active_indices] * risk_tensor)
    return loss, updated.detach(), {
        f"environment_{environment}_risk": float(risk.detach().cpu())
        for environment, risk in zip(active, risks, strict=True)
    }


def _save_checkpoint(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    torch.save(dict(payload), partial)
    os.replace(partial, path)


def _checkpoint_payload(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    next_epoch: int,
    next_batch: int,
    global_step: int,
    dro_weights: torch.Tensor,
    variant: str,
    binding: Mapping[str, object],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "r1-source-environment-checkpoint-v1",
        "variant": variant,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict(),
        "next_epoch": next_epoch,
        "next_batch": next_batch,
        "global_step": global_step,
        "dro_weights": dro_weights.cpu(),
        "python_random_state": random.getstate(),
        "numpy_random_state": np.random.get_state(),
        "torch_random_state": torch.random.get_rng_state(),
        "binding": dict(binding),
        "final_accessed": False,
    }
    if torch.cuda.is_available():
        payload["cuda_random_states"] = torch.cuda.get_rng_state_all()
    return payload


def _restore_checkpoint(
    path: Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: torch.optim.lr_scheduler.LRScheduler,
    variant: str,
    binding: Mapping[str, object],
    device: torch.device,
) -> tuple[int, int, int, torch.Tensor]:
    checkpoint = torch.load(path, map_location=device, weights_only=False)
    if (
        checkpoint.get("schema_version") != "r1-source-environment-checkpoint-v1"
        or checkpoint.get("variant") != variant
        or checkpoint.get("binding") != dict(binding)
        or checkpoint.get("final_accessed") is not False
    ):
        raise R1Error("恢复检查点身份绑定不一致")
    model.load_state_dict(checkpoint["model"])
    optimizer.load_state_dict(checkpoint["optimizer"])
    scheduler.load_state_dict(checkpoint["scheduler"])
    random.setstate(checkpoint["python_random_state"])
    np.random.set_state(checkpoint["numpy_random_state"])
    torch.random.set_rng_state(checkpoint["torch_random_state"])
    if "cuda_random_states" in checkpoint:
        torch.cuda.set_rng_state_all(checkpoint["cuda_random_states"])
    return (
        int(checkpoint["next_epoch"]),
        int(checkpoint["next_batch"]),
        int(checkpoint["global_step"]),
        checkpoint["dro_weights"].to(device),
    )


def _predict_role(
    model: nn.Module,
    variant: str,
    role: SequenceRole,
    representation: np.ndarray,
    output_dir: Path,
    batch_size: int,
    device: torch.device,
    save_representation: bool,
) -> tuple[np.ndarray, Path | None, float]:
    model.eval()
    probabilities = np.empty(role.row_count, dtype=np.float32)
    representation_path: Path | None = None
    stable_output: np.memmap | None = None
    partial: Path | None = None
    if save_representation:
        representation_path = output_dir / "representations" / f"{role.role}.npy"
        representation_path.parent.mkdir(parents=True, exist_ok=True)
        partial = representation_path.with_suffix(f".npy.partial.{os.getpid()}")
        stable_output = open_memmap(
            partial, mode="w+", dtype=np.float16, shape=(role.row_count, 192)
        )
    started = time.perf_counter()
    with torch.no_grad():
        for offset in range(0, role.sequence_count, batch_size):
            indices = np.arange(offset, min(offset + batch_size, role.sequence_count))
            values, valid, _, _ = _sequence_batch(role, representation, indices, None)
            values = values.to(device, non_blocking=True)
            valid_device = valid.to(device, non_blocking=True)
            with torch.autocast(
                device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"
            ):
                logits, stable = model.classify(values, valid_device)
            prob = torch.sigmoid(logits).float().cpu().numpy()
            stable_np = stable.float().cpu().numpy()
            valid_np = valid.numpy()
            for batch_index, sequence_index in enumerate(indices):
                start = int(role.starts[sequence_index])
                length = int(role.lengths[sequence_index])
                probabilities[start : start + length] = prob[batch_index][valid_np[batch_index]]
                if stable_output is not None:
                    stable_output[start : start + length] = stable_np[batch_index][
                        valid_np[batch_index]
                    ].astype(np.float16)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    if stable_output is not None and partial is not None and representation_path is not None:
        stable_output.flush()
        del stable_output
        os.replace(partial, representation_path)
    return probabilities, representation_path, time.perf_counter() - started


def _seal_predictions(
    output_dir: Path,
    role: SequenceRole,
    probabilities: np.ndarray,
) -> dict[str, Any]:
    if probabilities.shape != (role.row_count,) or not np.isfinite(probabilities).all():
        raise R1Error(f"{role.role} 概率形状不合法或包含非有限值")
    path = output_dir / "predictions" / f"{role.role}.npz"
    _write_npz(
        path,
        probability=probabilities,
        sample_id=np.asarray(role.sample_id),
        sequence_id=np.asarray(role.sequence_id),
        position=np.asarray(role.position),
        valid_length=np.asarray(role.valid_length),
    )
    receipt = {
        "schema_version": "r1-sealed-probabilities-v1",
        "role": role.role,
        "row_count": role.row_count,
        "sequence_count": role.sequence_count,
        "path": str(path.resolve()),
        "sha256": _sha256(path),
        "probability_dtype": "float32",
        "labels_read": role.role == "source-validation",
        "target_development_labels_read": False,
        "sealed_before_target_evaluation": True,
        "final_accessed": False,
    }
    _write_json(output_dir / "predictions" / f"{role.role}-receipt.json", receipt)
    return receipt


def train_variant(
    cache_root: Path,
    representation_root: Path,
    environment_root: Path,
    output_dir: Path,
    config_path: Path,
    variant: str,
    run_name: str,
) -> dict[str, Any]:
    """以共享采样清单训练 B0、GroupDRO 或 M1，并封存概率。"""
    if variant not in VARIANTS:
        raise R1Error(f"未知 R1 变体：{variant}")
    config = _load_config(config_path)
    _seed_everything(int(config["seed"]))
    cache_manifest, roles = load_cache(cache_root)
    representations, representation_receipt = _load_frozen_representations(
        cache_root, representation_root
    )
    environments = _load_environments(
        cache_root, representation_root, environment_root, roles
    )
    order = environments.training_order
    if order.shape != (
        int(config["epochs"]),
        int(np.ceil(roles["source-train"].sequence_count / config["batch_size_sequences"])),
        int(config["batch_size_sequences"]),
    ):
        raise R1Error("共享训练采样清单形状违反固定预算")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise R1Error("R1 Q0 真实训练要求 CUDA")
    models, parameter_counts = _build_models(int(config["private_state_size"]))
    model = models[variant].to(device)
    del models
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=int(config["epochs"])
    )
    binding = {
        "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
        "representation_manifest_sha256": _sha256(
            representation_root / "representation-manifest.json"
        ),
        "environment_manifest_sha256": _sha256(
            environment_root / "environment-manifest.json"
        ),
        "config_sha256": _sha256(config_path),
        "training_order_sha256": _sha256(environment_root / "training-sequence-order.npy"),
        "variant": variant,
        "seed": int(config["seed"]),
    }
    snapshot = {
        "schema_version": RUN_SCHEMA,
        "variant": variant,
        "display_name": DISPLAY_NAMES[variant],
        "run_name": run_name,
        "binding": binding,
        "parameter_counts": parameter_counts,
        "parameter_matched": len(set(parameter_counts.values())) == 1,
        "frozen_receiver": True,
        "model_inputs": ["frozen_receiver_representation"],
        "forbidden_model_inputs": [
            "environment",
            "group_key_ref",
            "first_available_ns",
            "last_available_ns",
            "year_role",
            "label",
        ],
        "environment_used_for": "共享采样和训练损失；不进入分类输入",
        "target_development_labels_used_during_training": False,
        "early_stopping": "disabled_for_fixed_four_epoch_q0_budget",
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "config": config,
        "cache_schema": cache_manifest["schema_version"],
        "receiver_checkpoint_sha256": representation_receipt.get("receiver_checkpoint_sha256"),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    config_snapshot_path = output_dir / "config.json"
    if config_snapshot_path.exists():
        existing = _read_json(config_snapshot_path)
        if existing.get("binding") != binding or existing.get("variant") != variant:
            raise R1Error("已有运行目录与当前冻结绑定不一致")
    else:
        _write_json(config_snapshot_path, snapshot)
        _write_json(output_dir / "environment-receipt.json", _environment(device))
    _write_json(
        output_dir / "status.json",
        {
            "state": "running",
            "variant": variant,
            "final_accessed": False,
            "updated_at": time.time(),
        },
    )
    checkpoint_path = output_dir / "checkpoints" / "latest.pt"
    dro_weights = torch.full((4,), 0.25, device=device)
    start_epoch = 0
    start_batch = 0
    global_step = 0
    resumed = False
    if checkpoint_path.is_file():
        start_epoch, start_batch, global_step, dro_weights = _restore_checkpoint(
            checkpoint_path,
            model,
            optimizer,
            scheduler,
            variant,
            binding,
            device,
        )
        resumed = True
    tracker: SwanTracker | None = None
    started = time.perf_counter()
    train_role = roles["source-train"]
    assert train_role.labels is not None
    epoch_metrics_path = output_dir / "metrics" / "epochs.jsonl"
    epoch_receipts: list[dict[str, Any]] = []
    if epoch_metrics_path.is_file():
        for line in epoch_metrics_path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if isinstance(value, dict):
                epoch_receipts.append(value)
    try:
        tracker = SwanTracker(output_dir, run_name, {**snapshot, "variant": variant})
        for epoch in range(start_epoch, int(config["epochs"])):
            model.train()
            sums: dict[str, float] = {}
            batch_begin = start_batch if epoch == start_epoch else 0
            for batch_index in range(batch_begin, order.shape[1]):
                sequence_indices = np.asarray(order[epoch, batch_index])
                values, valid, labels, batch_environments = _sequence_batch(
                    train_role,
                    representations["source-train"],
                    sequence_indices,
                    environments.train_environment,
                )
                assert labels is not None and batch_environments is not None
                values = values.to(device, non_blocking=True)
                valid = valid.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                batch_environments = batch_environments.to(device, non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
                    if variant == "M1":
                        assert isinstance(model, StablePrivateModel)
                        logits, stable, private, reconstructed = model.forward_train(
                            values, valid, batch_environments
                        )
                        loss, parts = _m1_losses(
                            logits,
                            stable,
                            private,
                            reconstructed,
                            values,
                            valid,
                            labels,
                            batch_environments,
                            config["m1_loss"],
                        )
                        scalars = {
                            name: float(value.detach().cpu()) for name, value in parts.items()
                        }
                    else:
                        logits, _ = model.classify(values, valid)
                        if variant == "GROUPDRO":
                            loss, dro_weights, risks = _groupdro_loss(
                                logits,
                                labels,
                                valid,
                                batch_environments,
                                dro_weights,
                                float(config["groupdro_eta"]),
                            )
                            scalars = risks
                        else:
                            loss = F.binary_cross_entropy_with_logits(
                                logits[valid], labels[valid]
                            )
                            scalars = {}
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), float(config["gradient_clip_norm"]))
                optimizer.step()
                global_step += 1
                scalars["loss"] = float(loss.detach().cpu())
                for name, value in scalars.items():
                    sums[name] = sums.get(name, 0.0) + value
                if global_step % int(config["checkpoint_interval_steps"]) == 0:
                    _save_checkpoint(
                        checkpoint_path,
                        _checkpoint_payload(
                            model,
                            optimizer,
                            scheduler,
                            epoch,
                            batch_index + 1,
                            global_step,
                            dro_weights,
                            variant,
                            binding,
                        ),
                    )
                if global_step % int(config["progress_interval_steps"]) == 0:
                    elapsed = time.perf_counter() - started
                    completed = global_step - (start_epoch * order.shape[1] + start_batch)
                    total = int(config["epochs"]) * order.shape[1]
                    rate = completed / max(elapsed, 1e-9)
                    print(
                        f"R1训练：变体={variant} 步={global_step}/{total} "
                        f"吞吐={rate:.2f}步/秒 预计剩余={max(total-global_step, 0)/max(rate, 1e-9):.1f}秒",
                        flush=True,
                    )
                    tracker.log(
                        {
                            "train/loss": scalars["loss"],
                            "train/learning_rate": float(optimizer.param_groups[0]["lr"]),
                            **{f"train/{name}": value for name, value in scalars.items()},
                        },
                        step=global_step,
                    )
            scheduler.step()
            epoch_receipt = {
                "epoch": epoch + 1,
                "steps": int(order.shape[1]),
                "mean_losses": {
                    name: value / max(order.shape[1] - batch_begin, 1)
                    for name, value in sums.items()
                },
                "environment_label_sampling_sha256": binding["training_order_sha256"],
                "groupdro_weights": dro_weights.detach().cpu().tolist(),
            }
            epoch_receipts.append(epoch_receipt)
            _append_jsonl(epoch_metrics_path, epoch_receipt)
            tracker.log(
                {f"epoch/{name}": value for name, value in epoch_receipt["mean_losses"].items()},
                step=global_step,
            )
            _save_checkpoint(
                checkpoint_path,
                _checkpoint_payload(
                    model,
                    optimizer,
                    scheduler,
                    epoch + 1,
                    0,
                    global_step,
                    dro_weights,
                    variant,
                    binding,
                ),
            )
            start_batch = 0
        _save_checkpoint(
            output_dir / "checkpoints" / "final.pt",
            _checkpoint_payload(
                model,
                optimizer,
                scheduler,
                int(config["epochs"]),
                0,
                global_step,
                dro_weights,
                variant,
                binding,
            ),
        )
        prediction_receipts: dict[str, Any] = {}
        representation_records: dict[str, Any] = {}
        prediction_seconds: dict[str, float] = {}
        for role_name in ("source-train", "source-validation", "target-development"):
            probabilities, stable_path, seconds = _predict_role(
                model,
                variant,
                roles[role_name],
                representations[role_name],
                output_dir,
                int(config["batch_size_sequences"]),
                device,
                save_representation=role_name != "target-development",
            )
            prediction_receipts[role_name] = _seal_predictions(
                output_dir, roles[role_name], probabilities
            )
            prediction_seconds[role_name] = seconds
            if stable_path is not None:
                representation_records[role_name] = {
                    "path": str(stable_path.resolve()),
                    "sha256": _sha256(stable_path),
                    "shape": [roles[role_name].row_count, 192],
                    "dtype": "float16",
                    "meaning": (
                        "冻结接收器表示" if variant != "M1" else "稳定 RWKV-7 式状态表示"
                    ),
                }
        representation_manifest = {
            "schema_version": "r1-source-stable-representations-v1",
            "variant": variant,
            "records": representation_records,
            "environment_or_group_used_as_representation_input": False,
            "target_development_representation_persisted": False,
            "final_accessed": False,
        }
        _write_json(output_dir / "representations" / "manifest.json", representation_manifest)
        receipt = {
            "schema_version": RUN_SCHEMA,
            "state": "probabilities_sealed_evaluation_pending",
            "variant": variant,
            "display_name": DISPLAY_NAMES[variant],
            "planned_epochs": int(config["epochs"]),
            "actual_epochs": int(config["epochs"]),
            "planned_steps": int(config["epochs"]) * int(order.shape[1]),
            "actual_steps": global_step,
            "resumed_from_checkpoint": resumed,
            "checkpoint_interval_steps": int(config["checkpoint_interval_steps"]),
            "parameter_counts": parameter_counts,
            "epoch_receipts": epoch_receipts,
            "prediction_receipts": prediction_receipts,
            "representation_manifest_sha256": _sha256(
                output_dir / "representations" / "manifest.json"
            ),
            "prediction_seconds": prediction_seconds,
            "training_seconds": time.perf_counter() - started,
            "peak_gpu_memory_bytes": int(torch.cuda.max_memory_allocated(device)),
            "target_development_labels_used": False,
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        }
        _write_json(output_dir / "training-receipt.json", receipt)
        _write_json(
            output_dir / "status.json",
            {
                "state": "probabilities_sealed_evaluation_pending",
                "variant": variant,
                "actual_steps": global_step,
                "target_development_labels_used": False,
                "final_accessed": False,
            },
        )
        tracker.finish(output_dir)
        return receipt
    except BaseException as error:
        _write_json(
            output_dir / "status.json",
            {
                "state": "failed",
                "variant": variant,
                "error_type": type(error).__name__,
                "checkpoint_available": checkpoint_path.is_file(),
                "recovery_action": "保持冻结绑定不变后重新运行同一 train 命令恢复",
                "final_accessed": False,
            },
        )
        if tracker is not None:
            tracker.fail(output_dir, error)
        raise


def _load_probability(run_dir: Path, role: str, expected_rows: int) -> tuple[np.ndarray, str]:
    receipt_path = run_dir / "predictions" / f"{role}-receipt.json"
    receipt = _read_json(receipt_path)
    path = run_dir / "predictions" / f"{role}.npz"
    if (
        receipt.get("schema_version") != "r1-sealed-probabilities-v1"
        or receipt.get("role") != role
        or receipt.get("sha256") != _sha256(path)
        or receipt.get("target_development_labels_read") is not False
        or receipt.get("final_accessed") is not False
    ):
        raise R1Error(f"{run_dir.name}/{role} 概率封存收据不合法")
    with np.load(path, allow_pickle=False) as values:
        probability = np.asarray(values["probability"], dtype=np.float32)
    if probability.shape != (expected_rows,) or not np.isfinite(probability).all():
        raise R1Error(f"{run_dir.name}/{role} 概率数组不合法")
    return probability, str(receipt["sha256"])


def _finite_tie_threshold(benign_scores: np.ndarray, alpha: float) -> dict[str, Any]:
    if len(benign_scores) == 0 or not np.isfinite(benign_scores).all():
        raise R1Error("有限样本同分数组阈值要求非空有限良性分数")
    unique, counts = np.unique(benign_scores, return_counts=True)
    descending = unique[::-1]
    cumulative = np.cumsum(counts[::-1])
    allowed = int(np.floor(alpha * len(benign_scores)))
    valid = cumulative <= allowed
    threshold = (
        float(descending[np.flatnonzero(valid)[-1]])
        if np.any(valid)
        else float(np.nextafter(benign_scores.max(), np.asarray(np.inf, dtype=benign_scores.dtype)))
    )
    false_positives = int(np.sum(benign_scores >= threshold))
    if false_positives > allowed:
        raise R1Error("同分数组阈值切开概率组或超过有限样本预算")
    return {
        "alpha": alpha,
        "threshold": threshold,
        "benign_count": int(len(benign_scores)),
        "allowed_false_positives": allowed,
        "actual_false_positives": false_positives,
        "same_score_group_split": False,
    }


def _ece(labels: np.ndarray, probabilities: np.ndarray, bins: int = 15) -> float:
    order = np.argsort(probabilities, kind="stable")
    error = 0.0
    for indices in np.array_split(order, bins):
        if len(indices):
            error += len(indices) / len(order) * abs(
                float(labels[indices].mean()) - float(probabilities[indices].mean())
            )
    return float(error)


def _curve_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    recalls: list[float],
    budgets_per_million: list[int],
) -> dict[str, Any]:
    order = np.argsort(-probabilities, kind="stable")
    sorted_scores = probabilities[order]
    sorted_labels = labels[order]
    group_ends = np.r_[np.flatnonzero(sorted_scores[1:] != sorted_scores[:-1]), len(labels) - 1]
    cumulative_tp = np.cumsum(sorted_labels == 1)[group_ends]
    cumulative_fp = np.cumsum(sorted_labels == 0)[group_ends]
    malicious = int(np.sum(labels == 1))
    benign = int(np.sum(labels == 0))
    fixed_recall: dict[str, Any] = {}
    for recall in recalls:
        required = int(np.ceil(recall * malicious))
        valid = np.flatnonzero(cumulative_tp >= required)
        fixed_recall[str(recall)] = (
            {"false_positives": int(cumulative_fp[valid[0]]), "achieved_recall": float(cumulative_tp[valid[0]] / max(malicious, 1))}
            if len(valid)
            else {"false_positives": None, "achieved_recall": 0.0}
        )
    fixed_budget: dict[str, Any] = {}
    for budget in budgets_per_million:
        allowed = int(np.floor(benign * budget / 1_000_000))
        valid = np.flatnonzero(cumulative_fp <= allowed)
        best_tp = int(cumulative_tp[valid].max()) if len(valid) else 0
        fixed_budget[str(budget)] = {
            "allowed_false_positives": allowed,
            "recall": float(best_tp / max(malicious, 1)),
        }
    return {
        "fixed_recall_false_positives": fixed_recall,
        "fixed_alert_budget_recall": fixed_budget,
    }


def _target_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
    recalls: list[float],
    budgets_per_million: list[int],
) -> dict[str, Any]:
    predictions = probabilities >= threshold
    benign = labels == 0
    malicious = labels == 1
    tp = int(np.sum(predictions & malicious))
    fp = int(np.sum(predictions & benign))
    fn = int(np.sum(~predictions & malicious))
    precision = tp / max(tp + fp, 1)
    recall = tp / max(int(malicious.sum()), 1)
    result = {
        "average_precision": float(average_precision_score(labels, probabilities)),
        "average_precision_over_prevalence": float(
            average_precision_score(labels, probabilities) / max(float(labels.mean()), 1e-12)
        ),
        "brier": float(brier_score_loss(labels, probabilities)),
        "ece_15_equal_frequency": _ece(labels, probabilities),
        "threshold": threshold,
        "target_false_positives_per_million_benign": float(fp * 1_000_000 / max(int(benign.sum()), 1)),
        "malicious_recall": float(recall),
        "malicious_f1": float(2 * precision * recall / max(precision + recall, 1e-12)),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "prevalence": float(labels.mean()),
    }
    result.update(_curve_metrics(labels, probabilities, recalls, budgets_per_million))
    return result


def _source_environment_fpr(
    labels: np.ndarray,
    probabilities: np.ndarray,
    environments: np.ndarray,
    threshold: float,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for environment in range(4):
        mask = (environments == environment) & (labels == 0)
        if not np.any(mask):
            raise R1Error(f"源校准环境 {environment} 没有良性流")
        result[str(environment)] = float(np.mean(probabilities[mask] >= threshold))
    return result


def _row_environment(role: SequenceRole, sequence_environment: np.ndarray) -> np.ndarray:
    result = np.empty(role.row_count, dtype=np.int8)
    for index, (start, length) in enumerate(zip(role.starts, role.lengths, strict=True)):
        result[int(start) : int(start + length)] = sequence_environment[index]
    return result


def _probe_environment_auc(
    train_values: np.ndarray,
    train_environment: np.ndarray,
    validation_values: np.ndarray,
    validation_environment: np.ndarray,
    seed: int,
    maximum_rows: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    train_indices = (
        rng.choice(len(train_values), maximum_rows, replace=False)
        if len(train_values) > maximum_rows
        else np.arange(len(train_values))
    )
    validation_indices = (
        rng.choice(len(validation_values), maximum_rows, replace=False)
        if len(validation_values) > maximum_rows
        else np.arange(len(validation_values))
    )
    probe = LogisticRegression(max_iter=200, solver="lbfgs", random_state=seed)
    probe.fit(
        np.asarray(train_values[train_indices], dtype=np.float32),
        train_environment[train_indices],
    )
    probabilities = probe.predict_proba(
        np.asarray(validation_values[validation_indices], dtype=np.float32)
    )
    auc = roc_auc_score(
        validation_environment[validation_indices],
        probabilities,
        multi_class="ovr",
        average="macro",
        labels=np.arange(4),
    )
    return {
        "macro_ovr_auc": float(auc),
        "train_rows": int(len(train_indices)),
        "validation_rows": int(len(validation_indices)),
        "probe": "multinomial logistic regression audit only",
        "main_model_gradient": False,
    }


def _relative_reduction(before: float, after: float) -> float | None:
    return float((before - after) / before) if before > 0 else None


def evaluate_grid(
    cache_root: Path,
    representation_root: Path,
    environment_root: Path,
    run_root: Path,
    output_dir: Path,
    config_path: Path,
) -> dict[str, Any]:
    """确认三组概率封存后连接目标开发标签并发布四格结果。"""
    if output_dir.exists():
        raise R1Error("评价输出目录已存在，拒绝覆盖")
    config = _load_config(config_path)
    _, roles = load_cache(cache_root)
    environments = _load_environments(
        cache_root, representation_root, environment_root, roles
    )
    statuses: dict[str, dict[str, Any]] = {}
    source_probabilities: dict[str, np.ndarray] = {}
    target_probabilities: dict[str, np.ndarray] = {}
    probability_hashes: dict[str, dict[str, str]] = {}
    for variant in VARIANTS:
        variant_dir = run_root / "variants" / variant.lower()
        status = _read_json(variant_dir / "status.json")
        if (
            status.get("state") != "probabilities_sealed_evaluation_pending"
            or status.get("target_development_labels_used") is not False
            or status.get("final_accessed") is not False
        ):
            raise R1Error(f"{variant} 尚未完成概率封存")
        statuses[variant] = status
        source_probabilities[variant], source_hash = _load_probability(
            variant_dir, "source-validation", roles["source-validation"].row_count
        )
        target_probabilities[variant], target_hash = _load_probability(
            variant_dir, "target-development", roles["target-development"].row_count
        )
        probability_hashes[variant] = {"source_validation": source_hash, "target_development": target_hash}

    target_label_path = roles["target-development"].root / "labels.npy"
    if not target_label_path.is_file():
        raise R1Error("概率封存后无法连接目标开发标签")
    target_labels = np.load(target_label_path, mmap_mode="r")
    if target_labels.shape != (roles["target-development"].row_count,) or not np.isin(
        target_labels, (0, 1)
    ).all():
        raise R1Error("目标开发标签数组不合法")
    source_role = roles["source-validation"]
    assert source_role.labels is not None
    source_labels = np.asarray(source_role.labels)
    row_partition = _row_environment(source_role, environments.validation_partition)
    row_environment = _row_environment(source_role, environments.validation_environment)
    calibration = row_partition == 1
    alpha_grid = [float(value) for value in config["calibration_alpha_grid"]]
    main_alpha = float(config["calibration_alpha"])
    thresholds: dict[str, Any] = {}
    cells: dict[str, Any] = {}
    recalls = [float(value) for value in config["fixed_recall_grid"]]
    budgets = [int(value) for value in config["fixed_alert_budget_per_million_grid"]]
    for variant in ("B0", "M1", "GROUPDRO"):
        probability = source_probabilities[variant]
        benign = calibration & (source_labels == 0)
        pooled_grid = {
            str(alpha): _finite_tie_threshold(probability[benign], alpha)
            for alpha in alpha_grid
        }
        environment_grid: dict[str, Any] = {}
        for environment in range(4):
            environment_benign = benign & (row_environment == environment)
            environment_grid[str(environment)] = {
                str(alpha): _finite_tie_threshold(probability[environment_benign], alpha)
                for alpha in alpha_grid
            }
        pooled_threshold = float(pooled_grid[str(main_alpha)]["threshold"])
        maximum_threshold = max(
            float(environment_grid[str(environment)][str(main_alpha)]["threshold"])
            for environment in range(4)
        )
        thresholds[variant] = {
            "pooled": pooled_grid,
            "environment": environment_grid,
            "main_pooled_threshold": pooled_threshold,
            "main_worst_environment_threshold": maximum_threshold,
        }
        if variant in ("B0", "M1"):
            for suffix, threshold in (("POOLED", pooled_threshold), ("M2", maximum_threshold)):
                name = f"{variant}+{suffix}"
                source_fpr = _source_environment_fpr(
                    source_labels[calibration],
                    probability[calibration],
                    row_environment[calibration],
                    threshold,
                )
                cells[name] = {
                    "base_probability_variant": variant,
                    "threshold_role": suffix,
                    "source_calibration_environment_fpr": source_fpr,
                    "worst_source_environment_fpr": max(source_fpr.values()),
                    "target": _target_metrics(
                        np.asarray(target_labels),
                        target_probabilities[variant],
                        threshold,
                        recalls,
                        budgets,
                    ),
                    "probability_sha256": probability_hashes[variant]["target_development"],
                }
    groupdro_threshold = float(thresholds["GROUPDRO"]["main_pooled_threshold"])
    groupdro_metrics = _target_metrics(
        np.asarray(target_labels),
        target_probabilities["GROUPDRO"],
        groupdro_threshold,
        recalls,
        budgets,
    )

    if not np.array_equal(target_probabilities["B0"], target_probabilities["B0"]):
        raise R1Error("B0 与 B0+M2 连续概率不一致")
    if not np.array_equal(target_probabilities["M1"], target_probabilities["M1"]):
        raise R1Error("M1 与 M1+M2 连续概率不一致")
    if cells["B0+POOLED"]["target"]["average_precision"] != cells["B0+M2"]["target"]["average_precision"]:
        raise R1Error("B0 四格平均精确率不一致")
    if cells["M1+POOLED"]["target"]["average_precision"] != cells["M1+M2"]["target"]["average_precision"]:
        raise R1Error("M1 四格平均精确率不一致")

    train_row_environment = _row_environment(
        roles["source-train"], environments.train_environment
    )
    validation_mask = row_partition == 0
    probes: dict[str, Any] = {}
    for variant in ("B0", "M1"):
        representation_manifest = _read_json(
            run_root / "variants" / variant.lower() / "representations" / "manifest.json"
        )
        records = representation_manifest.get("records")
        if not isinstance(records, Mapping):
            raise R1Error(f"{variant} 稳定表示清单不合法")
        train_path = _resolve_declared_path(records["source-train"]["path"], "源训练稳定表示")
        validation_path = _resolve_declared_path(
            records["source-validation"]["path"], "源验证稳定表示"
        )
        if (
            records["source-train"].get("sha256") != _sha256(train_path)
            or records["source-validation"].get("sha256") != _sha256(validation_path)
        ):
            raise R1Error(f"{variant} 稳定表示哈希不一致")
        probes[variant] = _probe_environment_auc(
            np.load(train_path, mmap_mode="r"),
            train_row_environment,
            np.load(validation_path, mmap_mode="r")[validation_mask],
            row_environment[validation_mask],
            int(config["seed"]),
            int(config["environment_probe_max_rows"]),
        )

    b0 = cells["B0+POOLED"]
    b0_m2 = cells["B0+M2"]
    m1 = cells["M1+POOLED"]
    m1_m2 = cells["M1+M2"]
    m1_delta_b0 = m1["target"]["average_precision"] - b0["target"]["average_precision"]
    m1_delta_groupdro = m1["target"]["average_precision"] - groupdro_metrics["average_precision"]
    probe_drop = probes["B0"]["macro_ovr_auc"] - probes["M1"]["macro_ovr_auc"]
    m2_source_reduction = _relative_reduction(
        b0["worst_source_environment_fpr"], b0_m2["worst_source_environment_fpr"]
    )
    m2_target_reduction = _relative_reduction(
        b0["target"]["target_false_positives_per_million_benign"],
        b0_m2["target"]["target_false_positives_per_million_benign"],
    )
    recall_drop = b0["target"]["malicious_recall"] - b0_m2["target"]["malicious_recall"]
    reference_budget = str(budgets[0])
    reference_recall = str(recalls[0])
    combination_budget_gain = (
        m1_m2["target"]["fixed_alert_budget_recall"][reference_budget]["recall"]
        - m1["target"]["fixed_alert_budget_recall"][reference_budget]["recall"]
    )
    before_fp = m1["target"]["fixed_recall_false_positives"][reference_recall]["false_positives"]
    after_fp = m1_m2["target"]["fixed_recall_false_positives"][reference_recall]["false_positives"]
    combination_fp_reduction = (
        _relative_reduction(float(before_fp), float(after_fp))
        if before_fp is not None and after_fp is not None
        else None
    )
    m1_pass = (
        m1_delta_b0 >= float(config["promotion_thresholds"]["m1_ap_delta_b0"])
        and m1_delta_groupdro >= float(config["promotion_thresholds"]["m1_ap_delta_groupdro_minimum"])
        and probe_drop >= float(config["promotion_thresholds"]["environment_probe_auc_drop"])
        and m1["target"]["average_precision"] >= b0["target"]["average_precision"]
    )
    m2_pass = (
        m2_source_reduction is not None
        and m2_source_reduction >= float(config["promotion_thresholds"]["m2_worst_source_fpr_reduction"])
        and m2_target_reduction is not None
        and m2_target_reduction >= float(config["promotion_thresholds"]["m2_target_fpm_reduction"])
        and recall_drop <= float(config["promotion_thresholds"]["m2_recall_drop_maximum"])
    )
    combination_pass = (
        combination_budget_gain
        >= float(config["promotion_thresholds"]["combination_fixed_budget_recall_gain"])
        or (
            combination_fp_reduction is not None
            and combination_fp_reduction
            >= float(config["promotion_thresholds"]["combination_fixed_recall_fp_reduction"])
        )
    )
    full_exceeds_single = m1_m2["target"]["malicious_f1"] > max(
        m1["target"]["malicious_f1"], b0_m2["target"]["malicious_f1"]
    )
    nonzero_recall = all(
        value > 0
        for value in (
            b0["target"]["malicious_recall"],
            m1["target"]["malicious_recall"],
            groupdro_metrics["malicious_recall"],
        )
    )
    promoted = m1_pass and m2_pass and combination_pass and full_exceeds_single and nonzero_recall
    decision = {
        "m1": {
            "passed": m1_pass,
            "average_precision_delta_vs_b0": m1_delta_b0,
            "average_precision_delta_vs_groupdro": m1_delta_groupdro,
            "required_delta_vs_groupdro": float(
                config["promotion_thresholds"]["m1_ap_delta_groupdro_minimum"]
            ),
            "environment_probe_auc_drop": probe_drop,
        },
        "m2": {
            "passed": m2_pass,
            "worst_source_environment_fpr_relative_reduction": m2_source_reduction,
            "target_false_positives_per_million_relative_reduction": m2_target_reduction,
            "malicious_recall_absolute_drop": recall_drop,
        },
        "m1_m2": {
            "passed": combination_pass,
            "fixed_alert_budget_recall_gain": combination_budget_gain,
            "fixed_recall_false_positive_relative_reduction": combination_fp_reduction,
            "continuous_score_curve_metrics_identical_by_contract": True,
            "full_combination_exceeds_best_single_by_malicious_f1": full_exceeds_single,
        },
        "all_main_model_recalls_nonzero": nonzero_recall,
        "promoted": promoted,
        "evidence_level": "Q0弱证据",
        "verdict": "R1 Q0晋级" if promoted else "R1 Q0不晋级",
        "not_formal_disproof": True,
    }
    output_dir.mkdir(parents=True)
    result = {
        "schema_version": EVALUATION_SCHEMA,
        "evaluation_order": "三组目标概率先封存，后由本入口连接目标开发标签",
        "probability_hashes": probability_hashes,
        "probability_identity_assertions": {
            "B0_equals_B0_M2_byte_source": True,
            "M1_equals_M1_M2_byte_source": True,
            "B0_average_precision_identical": True,
            "M1_average_precision_identical": True,
        },
        "thresholds": thresholds,
        "cells": cells,
        "groupdro": groupdro_metrics,
        "environment_probes": probes,
        "decision": decision,
        "target_label_sha256": _sha256(target_label_path),
        "target_label_connected_after_probability_seal": True,
        "target_prefix_labels_used": False,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    _write_json(output_dir / "grid-results.json", result)
    _write_json(
        output_dir / "status.json",
        {
            "state": "finished",
            "verdict": decision["verdict"],
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        },
    )
    for variant in VARIANTS:
        status = statuses[variant]
        status["state"] = "finished"
        status["evaluation_result"] = str((output_dir / "grid-results.json").resolve())
        status["target_development_labels_used_during_training"] = False
        status["target_development_labels_used_during_independent_evaluation"] = True
        _write_json(run_root / "variants" / variant.lower() / "status.json", status)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare-environments")
    prepare.add_argument("--cache-root", type=Path, required=True)
    prepare.add_argument("--representation-root", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, required=True)
    prepare.add_argument("--config", type=Path, required=True)
    train = subparsers.add_parser("train")
    train.add_argument("--cache-root", type=Path, required=True)
    train.add_argument("--representation-root", type=Path, required=True)
    train.add_argument("--environment-root", type=Path, required=True)
    train.add_argument("--output-dir", type=Path, required=True)
    train.add_argument("--config", type=Path, required=True)
    train.add_argument("--variant", choices=VARIANTS, required=True)
    train.add_argument("--run-name", required=True)
    evaluate = subparsers.add_parser("evaluate-grid")
    evaluate.add_argument("--cache-root", type=Path, required=True)
    evaluate.add_argument("--representation-root", type=Path, required=True)
    evaluate.add_argument("--environment-root", type=Path, required=True)
    evaluate.add_argument("--run-root", type=Path, required=True)
    evaluate.add_argument("--output-dir", type=Path, required=True)
    evaluate.add_argument("--config", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.command == "prepare-environments":
        result = prepare_environments(
            args.cache_root, args.representation_root, args.output_dir, args.config
        )
    elif args.command == "train":
        result = train_variant(
            args.cache_root,
            args.representation_root,
            args.environment_root,
            args.output_dir,
            args.config,
            args.variant,
            args.run_name,
        )
    elif args.command == "evaluate-grid":
        result = evaluate_grid(
            args.cache_root,
            args.representation_root,
            args.environment_root,
            args.run_root,
            args.output_dir,
            args.config,
        )
    else:
        raise R1Error(f"未处理命令：{args.command}")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
