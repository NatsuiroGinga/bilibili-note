"""C12 跨年度正式缓存加载器。

本模块只消费 Rust 物化器发布的两份正式清单，不从原始数据或最终区发现制品。
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow.dataset as pds
from numpy.lib.format import open_memmap


DATASET_SCHEMA = "lspr-crossyear-dataset-manifest-v1"
EXPERIMENT_SCHEMA = "lspr-crossyear-experiment-manifest-v1"
NORMALIZER_SCHEMA = "lspr-crossyear-normalizer-v1"
CACHE_SCHEMA = "lspr-crossyear-python-cache-v1"
BOUNDED_QUICK_CACHE_MODE = "bounded_quick_cache"
ROLES = ("source-train", "source-validation", "target-prefix", "target-development")
CACHE_COLUMNS = (
    "sample_id", "year_role", "sequence_id", "position", "valid_length", "available_ns",
    "delta_t_us", "x_value", "x_missing", "padding_mask", "group_key_ref",
)
MODEL_ARRAYS = ("x_value", "x_missing", "delta_t_us", "padding_mask")
SCAN_BATCH_SIZE = 65_536


def _bounded_artifact_names() -> set[str]:
    names = {
        "field_manifest",
        "normalizer",
        "sample_manifest",
        "sequence_manifest",
        "selection_receipt",
        "final_isolation_receipt",
    }
    for role in ROLES:
        names.add(f"{role}:cache")
        if role != "target-prefix":
            names.add(f"{role}:labels")
    return names


class CrossyearDatasetError(ValueError):
    """正式跨年度制品不符合冻结合同。"""


@dataclass(frozen=True)
class CrossyearFeatureRole:
    """预测阶段可见的只读特征角色，不含标签接口。"""

    name: str
    cache_dir: Path
    row_count: int
    sequence_count: int
    arrays: Mapping[str, Path]


@dataclass(frozen=True)
class CrossyearLabeledRole(CrossyearFeatureRole):
    """源年度训练或验证角色的独立标签旁车。"""

    labels: Path


@dataclass(frozen=True)
class TargetDevelopmentEvaluation:
    """预测冻结后才由评价器显式打开的目标开发标签旁车。"""

    labels: Path
    row_count: int


def _read_json(path: Path, description: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CrossyearDatasetError(f"无法读取{description}") from error
    if not isinstance(value, dict):
        raise CrossyearDatasetError(f"{description}必须是对象")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _required_string(document: Mapping[str, object], key: str, description: str) -> str:
    value = document.get(key)
    if not isinstance(value, str) or not value:
        raise CrossyearDatasetError(f"{description}缺少 {key}")
    return value


def _checked_path(raw: object, roots: tuple[Path, ...], description: str, *, file: bool = True) -> Path:
    if not isinstance(raw, str) or not raw:
        raise CrossyearDatasetError(f"{description}缺少绝对路径")
    path = Path(raw)
    if not path.is_absolute():
        raise CrossyearDatasetError(f"{description}必须是绝对路径")
    resolved = path.resolve()
    if not any(resolved.is_relative_to(root) for root in roots):
        raise CrossyearDatasetError(f"{description}越出项目或正式输出根")
    if file and not resolved.is_file():
        raise CrossyearDatasetError(f"{description}不存在或不是文件")
    return resolved


def _artifact_path(
    artifacts: Mapping[str, object], name: str, roots: tuple[Path, ...]
) -> Path:
    entry = artifacts.get(name)
    if not isinstance(entry, Mapping):
        raise CrossyearDatasetError(f"数据清单缺少制品 {name}")
    path = _checked_path(entry.get("path"), roots, f"制品 {name}")
    expected = _required_string(entry, "sha256", f"制品 {name}")
    if _sha256(path) != expected:
        raise CrossyearDatasetError(f"制品 {name} 的 SHA-256 不匹配")
    return path


def _fixed_binary(array: object, description: str) -> np.ndarray:
    values = array.to_pylist()
    if any(not isinstance(value, bytes) or len(value) != 32 for value in values):
        raise CrossyearDatasetError(f"{description}必须是 32 字节固定二进制标识")
    return np.frombuffer(b"".join(values), dtype=np.uint8).reshape(len(values), 32)


def _fixed_list(array: object, dtype: np.dtype, rows: int, description: str) -> np.ndarray:
    list_size = getattr(array.type, "list_size", None)
    if list_size != 77:
        raise CrossyearDatasetError(f"{description}的固定列表宽度不是 77")
    start = int(array.offset) * list_size
    values = array.values.slice(start, rows * list_size).to_numpy(zero_copy_only=False)
    result = np.asarray(values, dtype=dtype)
    if result.size != rows * list_size:
        raise CrossyearDatasetError(f"{description}长度不是 77")
    return result.reshape(rows, list_size)


def _write_array(path: Path, value: np.ndarray) -> None:
    with path.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)


def _array_record(path: Path, value: np.ndarray, published_path: Path | None = None) -> dict[str, object]:
    return {
        "path": str(published_path or path),
        "shape": list(value.shape),
        "dtype": str(value.dtype),
        "sha256": _sha256(path),
    }


def _role_counts(document: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = document.get(key)
    if not isinstance(value, Mapping) or set(value) != set(ROLES):
        raise CrossyearDatasetError(f"数据清单 {key} 必须恰有四个角色")
    return value


def _iter_label_rows(path: Path) -> Iterator[tuple[bytes, int]]:
    scanner = pds.dataset(path, format="parquet").scanner(
        columns=["sample_id", "label"], batch_size=SCAN_BATCH_SIZE, use_threads=False
    )
    for batch in scanner.to_batches():
        identifiers = batch.column(0).to_pylist()
        labels = batch.column(1).to_numpy(zero_copy_only=False)
        for identifier, label in zip(identifiers, labels, strict=True):
            if not isinstance(identifier, bytes) or len(identifier) != 32 or int(label) not in (0, 1):
                raise CrossyearDatasetError("标签旁车模式或取值不合法")
            yield identifier, int(label)


def _require_parquet_columns(path: Path, columns: tuple[str, ...], description: str) -> None:
    actual = tuple(pds.dataset(path, format="parquet").schema.names)
    if actual != columns:
        raise CrossyearDatasetError(f"{description}列模式不符合冻结合同")


def _validate_manifest_pair(
    config: Mapping[str, object], roots: tuple[Path, ...]
) -> tuple[
    Path,
    Path,
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
    tuple[str, ...],
    Path,
    bool,
]:
    outputs = config.get("outputs")
    if not isinstance(outputs, Mapping):
        raise CrossyearDatasetError("配置缺少 outputs")
    dataset_path = _checked_path(outputs.get("dataset_manifest"), roots, "数据集清单")
    experiment_path = _checked_path(outputs.get("experiment_manifest"), roots, "实验清单")
    dataset = _read_json(dataset_path, "数据集清单")
    experiment = _read_json(experiment_path, "实验清单")
    if dataset.get("schema_version") != DATASET_SCHEMA or experiment.get("schema_version") != EXPERIMENT_SCHEMA:
        raise CrossyearDatasetError("正式清单模式版本漂移")
    declared_modes = (
        config.get("materialization_mode"),
        dataset.get("materialization_mode"),
        experiment.get("materialization_mode"),
    )
    bounded_quick_cache = all(mode == BOUNDED_QUICK_CACHE_MODE for mode in declared_modes)
    if BOUNDED_QUICK_CACHE_MODE in declared_modes and not bounded_quick_cache:
        raise CrossyearDatasetError("有界快速缓存要求配置、数据集清单和实验清单的 materialization_mode 一致")
    if bounded_quick_cache and (
        dataset.get("budget_tier") != experiment.get("budget_tier")
        or dataset.get("cache_rows") != experiment.get("cache_rows")
    ):
        raise CrossyearDatasetError("有界快速缓存的数据集清单与实验清单预算或 cache_rows 不一致")
    if dataset.get("final_accessed") is not False or experiment.get("final_accessed") is not False:
        raise CrossyearDatasetError("开发加载器拒绝 final_accessed 非 false 的制品")
    reference = experiment.get("dataset_manifest")
    if not isinstance(reference, Mapping) or reference.get("path") != str(dataset_path):
        raise CrossyearDatasetError("实验清单未精确引用数据集清单")
    if reference.get("sha256") != _sha256(dataset_path):
        raise CrossyearDatasetError("实验清单的数据集清单哈希不匹配")
    fields = experiment.get("model_fields")
    if not isinstance(fields, list) or len(fields) != 77 or any(not isinstance(item, str) for item in fields):
        raise CrossyearDatasetError("实验清单模型字段必须为 77 个有序字符串")
    if experiment.get("field_count") != 77 or experiment.get("max_sequence_length") != 128:
        raise CrossyearDatasetError("实验清单字段数或最大序列长度不匹配")
    if experiment.get("labels_outside_features") is not True or experiment.get("group_key_outside_features") is not True:
        raise CrossyearDatasetError("实验清单未声明标签和分组键隔离")
    artifacts = dataset.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise CrossyearDatasetError("数据清单 artifacts 必须是对象")
    if bounded_quick_cache:
        expected_artifacts = _bounded_artifact_names()
        missing_artifacts = sorted(expected_artifacts - set(artifacts))
        unexpected_artifacts = sorted(set(artifacts) - expected_artifacts)
        if missing_artifacts:
            raise CrossyearDatasetError(f"有界快速缓存清单缺少制品：{', '.join(missing_artifacts)}")
        if unexpected_artifacts:
            raise CrossyearDatasetError(f"有界快速缓存清单含未授权制品：{', '.join(unexpected_artifacts)}")
    for name in artifacts:
        _artifact_path(artifacts, str(name), roots)
    field_manifest = _read_json(_artifact_path(artifacts, "field_manifest", roots), "字段清单")
    if field_manifest.get("schema_version") != "lspr-crossyear-field-manifest-v1":
        raise CrossyearDatasetError("字段清单模式版本漂移")
    if field_manifest.get("common_model_fields") != fields:
        raise CrossyearDatasetError("字段清单与实验清单字段顺序不一致")
    normalizer_path = _artifact_path(artifacts, "normalizer", roots)
    normalizer = _read_json(normalizer_path, "归一化器")
    if normalizer.get("schema_version") != NORMALIZER_SCHEMA or normalizer.get("fitted_role") != "source-train":
        raise CrossyearDatasetError("归一化器不是冻结的 source-train 制品")
    normalizer_ref = experiment.get("normalizer")
    if not isinstance(normalizer_ref, Mapping) or normalizer_ref.get("path") != str(normalizer_path):
        raise CrossyearDatasetError("实验清单归一化器引用不匹配")
    return (
        dataset_path,
        experiment_path,
        dataset,
        experiment,
        artifacts,
        tuple(fields),
        normalizer_path,
        bounded_quick_cache,
    )


def _validate_role_block(
    role: str,
    cache_path: Path,
    expected_rows: int,
    expected_sequences: int,
    staging: Path,
    label_path: Path | None,
    *,
    include_group_key_ref: bool = False,
) -> tuple[dict[str, Path], int]:
    role_dir = staging / f"role={role}"
    role_dir.mkdir()
    arrays = {
        "x_value": open_memmap(role_dir / "x_value.npy", mode="w+", dtype=np.float32, shape=(expected_rows, 77)),
        "x_missing": open_memmap(role_dir / "x_missing.npy", mode="w+", dtype=np.uint8, shape=(expected_rows, 77)),
        "delta_t_us": open_memmap(role_dir / "delta_t_us.npy", mode="w+", dtype=np.int64, shape=(expected_rows,)),
        "padding_mask": open_memmap(role_dir / "padding_mask.npy", mode="w+", dtype=np.uint8, shape=(expected_rows,)),
        "sample_id": open_memmap(role_dir / "sample_id.npy", mode="w+", dtype=np.uint8, shape=(expected_rows, 32)),
        "sequence_id": open_memmap(role_dir / "sequence_id.npy", mode="w+", dtype=np.uint8, shape=(expected_rows, 32)),
        "position": open_memmap(role_dir / "position.npy", mode="w+", dtype=np.uint16, shape=(expected_rows,)),
        "valid_length": open_memmap(role_dir / "valid_length.npy", mode="w+", dtype=np.uint16, shape=(expected_rows,)),
    }
    if include_group_key_ref:
        arrays["group_key_ref"] = open_memmap(
            role_dir / "group_key_ref.npy", mode="w+", dtype=np.uint8, shape=(expected_rows, 32)
        )
    labels = open_memmap(role_dir / "labels.npy", mode="w+", dtype=np.uint8, shape=(expected_rows,)) if label_path else None
    label_rows = _iter_label_rows(label_path) if label_path else None
    scanner = pds.dataset(cache_path, format="parquet").scanner(columns=list(CACHE_COLUMNS), batch_size=SCAN_BATCH_SIZE, use_threads=False)
    offset = 0
    started = time.perf_counter()
    for batch in scanner.to_batches():
        count = batch.num_rows
        if offset + count > expected_rows:
            raise CrossyearDatasetError(f"{role} 缓存行数超过清单")
        roles = batch.column(1).to_pylist()
        if any(value != role for value in roles):
            raise CrossyearDatasetError(f"{role} 缓存出现未知或跨角色行")
        arrays["sample_id"][offset : offset + count] = _fixed_binary(batch.column(0), f"{role} sample_id")
        arrays["sequence_id"][offset : offset + count] = _fixed_binary(batch.column(2), f"{role} sequence_id")
        arrays["position"][offset : offset + count] = batch.column(3).to_numpy(zero_copy_only=False)
        arrays["valid_length"][offset : offset + count] = batch.column(4).to_numpy(zero_copy_only=False)
        arrays["delta_t_us"][offset : offset + count] = batch.column(6).to_numpy(zero_copy_only=False)
        arrays["x_value"][offset : offset + count] = _fixed_list(batch.column(7), np.float32, count, f"{role} x_value")
        arrays["x_missing"][offset : offset + count] = _fixed_list(batch.column(8), np.uint8, count, f"{role} x_missing")
        masks = batch.column(9).to_numpy(zero_copy_only=False)
        if not np.all(masks == 1):
            raise CrossyearDatasetError(f"{role} padding_mask 必须全为 1")
        arrays["padding_mask"][offset : offset + count] = masks
        if include_group_key_ref:
            arrays["group_key_ref"][offset : offset + count] = _fixed_binary(
                batch.column(10), f"{role} group_key_ref"
            )
        if label_rows is not None and labels is not None:
            for index, identifier in enumerate(batch.column(0).to_pylist()):
                label_identifier, label = next(label_rows, (None, None))
                if identifier != label_identifier:
                    raise CrossyearDatasetError(f"{role} 标签旁车无法按 sample_id 一对一连接")
                labels[offset + index] = label
        offset += count
        if offset and offset % (SCAN_BATCH_SIZE * 16) == 0:
            elapsed = max(time.perf_counter() - started, 1e-6)
            rate = offset / elapsed
            remaining = (expected_rows - offset) / rate
            print(f"跨年度缓存 {role}：{offset}/{expected_rows} 行，{rate:.0f} 行/秒，剩余约 {remaining:.0f} 秒")
    if offset != expected_rows:
        raise CrossyearDatasetError(f"{role} 缓存行数与清单不一致")
    if label_rows is not None and next(label_rows, None) is not None:
        raise CrossyearDatasetError(f"{role} 标签旁车行数与缓存不一致")
    for array in arrays.values():
        array.flush()
    if labels is not None:
        labels.flush()
    sample_ids = np.load(role_dir / "sample_id.npy", mmap_mode="r")
    sequence_ids = np.load(role_dir / "sequence_id.npy", mmap_mode="r")
    positions = np.load(role_dir / "position.npy", mmap_mode="r")
    lengths = np.load(role_dir / "valid_length.npy", mmap_mode="r")
    if np.unique(sample_ids, axis=0).shape[0] != expected_rows:
        raise CrossyearDatasetError(f"{role} sample_id 不唯一")
    starts = np.empty(expected_rows, dtype=bool)
    starts[0] = True
    starts[1:] = np.any(sequence_ids[1:] != sequence_ids[:-1], axis=1)
    if not np.all(positions[starts] == 0) or np.any(lengths == 0) or np.any(lengths > 128):
        raise CrossyearDatasetError(f"{role} 序列首位置或有效长度不合法")
    same = ~starts[1:]
    if np.any(positions[1:][same] != positions[:-1][same] + 1) or np.any(lengths[1:][same] != lengths[:-1][same]):
        raise CrossyearDatasetError(f"{role} 序列位置不连续")
    sequence_starts = np.flatnonzero(starts)
    sequence_lengths = np.diff(np.append(sequence_starts, expected_rows))
    sequence_values = np.unique(sequence_ids, axis=0)
    if (
        sequence_values.shape[0] != expected_sequences
        or np.any(sequence_lengths != lengths[starts])
    ):
        raise CrossyearDatasetError(f"{role} 序列数量、连续性或有效长度与清单不一致")
    published = {name: role_dir / f"{name}.npy" for name in arrays}
    if labels is not None:
        published["labels"] = role_dir / "labels.npy"
    return published, int(sequence_values.shape[0])


def _iter_rows(path: Path, columns: tuple[str, ...], filter_expression: object | None = None) -> Iterator[tuple[object, ...]]:
    scanner = pds.dataset(path, format="parquet").scanner(
        columns=list(columns), filter=filter_expression, batch_size=SCAN_BATCH_SIZE, use_threads=False
    )
    for batch in scanner.to_batches():
        values = [column.to_pylist() for column in batch.columns]
        yield from zip(*values, strict=True)


def _validate_bounded_role_manifests(
    role: str,
    cache_path: Path,
    sample_manifest: Path,
    sequence_manifest: Path,
    expected_rows: int,
    expected_sequences: int,
) -> None:
    """确认有界缓存与两份清单逐行一致，不发现或扩大缓存成员。"""
    cache_columns = (
        "sample_id",
        "year_role",
        "sequence_id",
        "position",
        "valid_length",
        "available_ns",
        "group_key_ref",
    )
    sample_columns = (
        "sample_id",
        "year_role",
        "sequence_id",
        "position",
        "valid_length",
        "available_ns",
        "cache_selected",
    )
    sequence_columns = (
        "sequence_id",
        "year_role",
        "group_key_ref",
        "valid_length",
        "first_available_ns",
        "last_available_ns",
        "cache_selected",
    )
    sample_rows = _iter_rows(sample_manifest, sample_columns, pds.field("year_role") == role)
    sequence_rows = _iter_rows(sequence_manifest, sequence_columns, pds.field("year_role") == role)
    missing = object()
    row_count = 0
    sequence_count = 0
    current_sequence: bytes | None = None
    current_group_key: bytes | None = None
    current_last_available_ns: int | None = None
    for cache_row in _iter_rows(cache_path, cache_columns):
        sample_row = next(sample_rows, missing)
        if sample_row is missing:
            raise CrossyearDatasetError(f"{role} 样本清单少于有界缓存")
        sample_id, cache_role, sequence_id, position, valid_length, available_ns, group_key_ref = cache_row
        (
            manifest_sample_id,
            manifest_role,
            manifest_sequence_id,
            manifest_position,
            manifest_valid_length,
            manifest_available_ns,
            cache_selected,
        ) = sample_row
        if (
            sample_id,
            cache_role,
            sequence_id,
            position,
            valid_length,
            available_ns,
        ) != (
            manifest_sample_id,
            manifest_role,
            manifest_sequence_id,
            manifest_position,
            manifest_valid_length,
            manifest_available_ns,
        ):
            raise CrossyearDatasetError(f"{role} 有界缓存与样本清单无法逐行连接")
        if cache_role != role or cache_selected != 1:
            raise CrossyearDatasetError(f"{role} 样本清单角色或 cache_selected 不合法")
        if not isinstance(group_key_ref, bytes) or len(group_key_ref) != 32:
            raise CrossyearDatasetError(f"{role} 有界缓存 group_key_ref 必须是 32 字节固定二进制标识")
        if int(position) == 0:
            sequence_row = next(sequence_rows, missing)
            if sequence_row is missing:
                raise CrossyearDatasetError(f"{role} 序列清单少于有界缓存")
            (
                manifest_sequence_id,
                manifest_sequence_role,
                manifest_group_key,
                manifest_sequence_length,
                first_available_ns,
                last_available_ns,
                sequence_selected,
            ) = sequence_row
            if (
                sequence_id != manifest_sequence_id
                or manifest_sequence_role != role
                or group_key_ref != manifest_group_key
                or int(valid_length) != int(manifest_sequence_length)
                or int(available_ns) != int(first_available_ns)
                or sequence_selected != 1
            ):
                raise CrossyearDatasetError(f"{role} 有界缓存与序列清单无法按 sequence_id 连接")
            current_sequence = sequence_id
            current_group_key = group_key_ref
            current_last_available_ns = int(last_available_ns)
            sequence_count += 1
        elif sequence_id != current_sequence or group_key_ref != current_group_key:
            raise CrossyearDatasetError(f"{role} 有界缓存序列内的 sequence_id 或 group_key_ref 漂移")
        if int(position) == int(valid_length) - 1:
            if int(available_ns) != current_last_available_ns:
                raise CrossyearDatasetError(f"{role} 有界缓存序列末时刻与序列清单不一致")
            current_sequence = None
            current_group_key = None
            current_last_available_ns = None
        row_count += 1
    if next(sample_rows, missing) is not missing:
        raise CrossyearDatasetError(f"{role} 样本清单多于有界缓存")
    if next(sequence_rows, missing) is not missing:
        raise CrossyearDatasetError(f"{role} 序列清单多于有界缓存")
    if current_sequence is not None:
        raise CrossyearDatasetError(f"{role} 有界缓存末尾序列不完整")
    if row_count != expected_rows or sequence_count != expected_sequences:
        raise CrossyearDatasetError(f"{role} 有界缓存与样本／序列清单计数不一致")


def _validate_bounded_receipts(
    artifacts: Mapping[str, object],
    roots: tuple[Path, ...],
    role_rows: Mapping[str, object],
    role_sequences: Mapping[str, object],
    role_row_limits: object,
    pair_hash_keep_thresholds: object,
) -> tuple[Path, Mapping[str, object]]:
    receipt_path = _artifact_path(artifacts, "selection_receipt", roots)
    receipt = _read_json(receipt_path, "有界缓存选择收据")
    if receipt.get("schema_version") != "lspr-crossyear-sequence-selection-v1":
        raise CrossyearDatasetError("有界缓存选择收据 schema_version 不匹配")
    if receipt.get("materialization_mode") != BOUNDED_QUICK_CACHE_MODE:
        raise CrossyearDatasetError("有界缓存选择收据缺少 materialization_mode=bounded_quick_cache")
    if receipt.get("target_label_used_for_selection") is not False:
        raise CrossyearDatasetError("有界缓存选择收据未证明目标标签不参与选择")
    if receipt.get("sequence_split_allowed") is not False or receipt.get("final_accessed") is not False:
        raise CrossyearDatasetError("有界缓存选择收据允许拆分序列或访问最终区")
    if not isinstance(role_row_limits, Mapping) or set(role_row_limits) != set(ROLES):
        raise CrossyearDatasetError("有界快速缓存数据清单 role_row_limits 必须恰有四个角色")
    if receipt.get("role_row_limits") != role_row_limits:
        raise CrossyearDatasetError("有界缓存选择收据与数据清单的 role_row_limits 不一致")
    if not isinstance(pair_hash_keep_thresholds, Mapping) or set(pair_hash_keep_thresholds) != set(ROLES):
        raise CrossyearDatasetError("有界快速缓存数据清单 pair_hash_keep_thresholds 必须恰有四个角色")
    prescreen = receipt.get("pair_hash_prescreen")
    if (
        not isinstance(prescreen, Mapping)
        or prescreen.get("algorithm") != "label-blind-pair-key-sha256-leading-byte-v1"
        or prescreen.get("denominator") != 256
        or not isinstance(prescreen.get("role_thresholds"), Mapping)
        or prescreen.get("role_thresholds") != pair_hash_keep_thresholds
    ):
        raise CrossyearDatasetError("有界缓存选择收据缺少四角色无标签 pair_hash_prescreen 合同")
    receipt_roles = receipt.get("roles")
    if not isinstance(receipt_roles, Mapping) or set(receipt_roles) != set(ROLES):
        raise CrossyearDatasetError("有界缓存选择收据 roles 必须恰有四个角色")
    for role in ROLES:
        role_receipt = receipt_roles.get(role)
        if not isinstance(role_receipt, Mapping):
            raise CrossyearDatasetError(f"有界缓存选择收据缺少角色 {role}")
        if role_receipt.get("selected_row_count") != role_rows[role]:
            raise CrossyearDatasetError(f"有界缓存选择收据 {role} 的 selected_row_count 不匹配")
        if role_receipt.get("selected_sequence_count") != role_sequences[role]:
            raise CrossyearDatasetError(f"有界缓存选择收据 {role} 的 selected_sequence_count 不匹配")
        if not isinstance(role_row_limits[role], int) or int(role_rows[role]) > int(role_row_limits[role]):
            raise CrossyearDatasetError(f"有界缓存角色 {role} 的行数超过 role_row_limits")
        selected_sha256 = role_receipt.get("selected_sequence_sha256")
        if not isinstance(selected_sha256, str) or len(selected_sha256) != 64:
            raise CrossyearDatasetError(f"有界缓存选择收据 {role} 缺少 selected_sequence_sha256")
    final_receipt_path = _artifact_path(artifacts, "final_isolation_receipt", roots)
    final_receipt = _read_json(final_receipt_path, "最终区隔离收据")
    if final_receipt.get("schema_version") != "lspr-crossyear-final-isolation-v1":
        raise CrossyearDatasetError("最终区隔离收据 schema_version 不匹配")
    if final_receipt.get("final_accessed") is not False:
        raise CrossyearDatasetError("最终区隔离收据的 final_accessed 必须为 false")
    for key in (
        "final_feature_artifacts",
        "final_label_artifacts",
        "final_member_artifacts",
        "final_specific_statistics",
    ):
        if final_receipt.get(key) != []:
            raise CrossyearDatasetError(f"最终区隔离收据字段 {key} 必须为空列表")
    return receipt_path, receipt


def _full_source_validation_inventory(sample_manifest: Path, sequence_manifest: Path) -> tuple[int, int, str]:
    """以两个正式清单确认完整源验证成员，不根据标签选择成员。"""
    sample_columns = ("sample_id", "year_role", "sequence_id", "position", "valid_length", "available_ns", "cache_selected")
    sample_rows = 0
    sample_sequences = 0
    sample_hash = hashlib.sha256()
    current_id: bytes | None = None
    current_length = 0
    current_valid_length = 0
    previous_position = -1
    for _sample_id, role, sequence_id, position, valid_length, _available_ns, _cache_selected in _iter_rows(
        sample_manifest, sample_columns, pds.field("year_role") == "source-validation"
    ):
        if role != "source-validation" or not isinstance(sequence_id, bytes) or len(sequence_id) != 32:
            raise CrossyearDatasetError("源验证样本清单角色或序列标识不合法")
        if current_id != sequence_id:
            if current_id is not None and current_length != current_valid_length:
                raise CrossyearDatasetError("源验证样本清单序列长度不连续")
            current_id = sequence_id
            current_length = 0
            current_valid_length = int(valid_length)
            previous_position = -1
            sample_sequences += 1
            sample_hash.update(sequence_id)
        if int(valid_length) != current_valid_length or int(position) != previous_position + 1:
            raise CrossyearDatasetError("源验证样本清单含拆分或不连续序列")
        current_length += 1
        sample_rows += 1
        previous_position = int(position)
    if current_id is None or current_length != current_valid_length:
        raise CrossyearDatasetError("源验证样本清单末尾序列长度不连续")
    columns = (
        "sequence_id", "year_role", "group_key_ref", "valid_length", "first_available_ns",
        "last_available_ns", "cache_selected",
    )
    sequence_rows = 0
    sequence_hash = hashlib.sha256()
    for sequence_id, role, _group_key, valid_length, first, last, cache_selected in _iter_rows(
        sequence_manifest, columns, pds.field("year_role") == "source-validation"
    ):
        if role != "source-validation" or not isinstance(sequence_id, bytes) or len(sequence_id) != 32:
            raise CrossyearDatasetError("源验证序列清单角色或序列标识不合法")
        if not 1 <= int(valid_length) <= 128 or int(first) > int(last) or int(cache_selected) not in (0, 1):
            raise CrossyearDatasetError("源验证序列清单语义不合法")
        sequence_rows += 1
        sequence_hash.update(sequence_id)
    if sample_sequences != sequence_rows or sample_hash.digest() != sequence_hash.digest():
        raise CrossyearDatasetError("源验证样本清单与序列清单成员不一致")
    return sample_rows, sample_sequences, sequence_hash.hexdigest()


def _expand_source_validation(
    role_dir: Path,
    main_path: Path,
    sample_manifest: Path,
    sequence_manifest: Path,
    labels_path: Path,
    fields: tuple[str, ...],
    normalizer: Mapping[str, object],
    staging: Path,
) -> tuple[dict[str, Path], int, Path | None]:
    labels = np.load(role_dir / "labels.npy", mmap_mode="r")
    existing_malicious = int(np.count_nonzero(labels))
    existing_rows = int(labels.shape[0])
    existing_sequence_ids = np.load(role_dir / "sequence_id.npy", mmap_mode="r")
    existing_sequences = int(np.unique(existing_sequence_ids, axis=0).shape[0])
    if existing_malicious >= 200:
        return {path.stem: path for path in role_dir.glob("*.npy")}, existing_sequences, None
    full_rows, full_sequences, member_sha256 = _full_source_validation_inventory(
        sample_manifest, sequence_manifest
    )
    if full_rows < existing_rows or full_sequences < existing_sequences:
        raise CrossyearDatasetError("完整 source-validation 清单小于快速缓存")
    statistics = normalizer.get("statistics")
    vocabulary = normalizer.get("protocol_vocabulary")
    clip = normalizer.get("clip")
    if (
        not isinstance(statistics, list)
        or len(statistics) != 76
        or not isinstance(vocabulary, list)
        or not isinstance(clip, (int, float))
        or normalizer.get("protocol_missing_index") != 0
        or normalizer.get("protocol_unknown_index") != 1
        or normalizer.get("protocol_vocabulary_start_index") != 2
    ):
        raise CrossyearDatasetError("归一化器缺少精确复现扩展缓存的字段")
    medians: list[float] = []
    iqrs: list[float] = []
    for field, statistic in zip(fields[1:], statistics, strict=True):
        if not isinstance(statistic, Mapping) or statistic.get("field") != field:
            raise CrossyearDatasetError("归一化器统计字段顺序与实验字段不一致")
        median, iqr = statistic.get("median"), statistic.get("iqr")
        if not isinstance(median, (int, float)) or not isinstance(iqr, (int, float)) or iqr <= 0:
            raise CrossyearDatasetError("归一化器中位数或 IQR 不合法")
        medians.append(float(median))
        iqrs.append(float(iqr))
    protocol_index = {int(value): index + 2 for index, value in enumerate(vocabulary) if isinstance(value, int)}
    if len(protocol_index) != len(vocabulary):
        raise CrossyearDatasetError("归一化器协议词表不合法")
    main_columns = (
        "sample_id", "year_role", "Protocol", "Protocol__is_missing",
        *(name for field in fields[1:] for name in (field, f"{field}__is_missing")),
        "Conn_state", "Conn_state__is_missing",
    )
    sample_columns = ("sample_id", "year_role", "sequence_id", "position", "valid_length", "available_ns", "cache_selected")
    _require_parquet_columns(main_path, main_columns, "完整 source-validation 主产品")
    expanded = role_dir.with_name(role_dir.name + ".expanded")
    expanded.mkdir()
    old_arrays = {path.stem: np.load(path, mmap_mode="r") for path in role_dir.glob("*.npy")}
    new_arrays = {
        name: open_memmap(expanded / f"{name}.npy", mode="w+", dtype=value.dtype, shape=(full_rows, *value.shape[1:]))
        for name, value in old_arrays.items()
    }
    sample_rows = _iter_rows(sample_manifest, sample_columns, pds.field("year_role") == "source-validation")
    main_rows = _iter_rows(main_path, main_columns)
    label_rows = _iter_label_rows(labels_path)
    offset = 0
    previous_sequence: bytes | None = None
    previous_available: int | None = None
    for sample, main, label in zip(sample_rows, main_rows, label_rows, strict=True):
        sample_id, role, sequence_id, position, valid_length, available_ns, _cache_selected = sample
        main_id, main_role, protocol, protocol_missing, *numeric_and_conn_state = main
        *numeric, conn_state, conn_state_missing = numeric_and_conn_state
        label_id, label_value = label
        if sample_id != main_id or sample_id != label_id or role != "source-validation" or main_role != role:
            raise CrossyearDatasetError("完整主产品、样本清单和标签旁车无法一对一连接")
        if int(position) == 0:
            delta_t_us = 0
            previous_sequence = sequence_id
            previous_available = int(available_ns)
        else:
            if previous_sequence != sequence_id or previous_available is None or int(available_ns) < previous_available:
                raise CrossyearDatasetError("扩展序列可用时刻不连续")
            delta_t_us = (int(available_ns) - previous_available) // 1_000
            previous_available = int(available_ns)
        values = np.empty(77, dtype=np.float32)
        missing = np.empty(77, dtype=np.uint8)
        if int(protocol_missing) != 0 or protocol is None:
            values[0], missing[0] = 0.0, 1
        else:
            values[0], missing[0] = float(protocol_index.get(int(protocol), 1)), 0
        if len(numeric) != 152:
            raise CrossyearDatasetError("完整主产品数值字段模式不完整")
        if conn_state is not None and not isinstance(conn_state, str):
            raise CrossyearDatasetError("完整主产品 Conn_state 模式不合法")
        if int(conn_state_missing) not in (0, 1):
            raise CrossyearDatasetError("完整主产品 Conn_state 缺失掩码不合法")
        for index, (raw, raw_missing) in enumerate(zip(numeric[::2], numeric[1::2], strict=True), start=1):
            if int(raw_missing) != 0 or raw is None:
                value, is_missing = medians[index - 1], 1
            else:
                value, is_missing = float(raw), 0
                if not np.isfinite(value) or value < 0:
                    raise CrossyearDatasetError("完整主产品包含 Rust 未隔离的非法数值")
            values[index] = np.float32(np.clip((value - medians[index - 1]) / iqrs[index - 1], -float(clip), float(clip)))
            missing[index] = is_missing
        new_arrays["sample_id"][offset] = np.frombuffer(sample_id, dtype=np.uint8)
        new_arrays["sequence_id"][offset] = np.frombuffer(sequence_id, dtype=np.uint8)
        new_arrays["position"][offset] = int(position)
        new_arrays["valid_length"][offset] = int(valid_length)
        new_arrays["delta_t_us"][offset] = delta_t_us
        new_arrays["x_value"][offset] = values
        new_arrays["x_missing"][offset] = missing
        new_arrays["padding_mask"][offset] = 1
        new_arrays["labels"][offset] = label_value
        offset += 1
    if offset != full_rows:
        raise CrossyearDatasetError("完整 source-validation 主产品行数与清单不一致")
    for array in new_arrays.values():
        array.flush()
    receipt = {
        "schema_version": "lspr-crossyear-source-validation-extension-v1",
        "trigger_malicious_flow_count": existing_malicious,
        "minimum_malicious_flow_count": 200,
        "before_rows": existing_rows,
        "before_sequences": existing_sequences,
        "after_rows": offset,
        "after_sequences": full_sequences,
        "member_sha256": member_sha256,
        "member_scope": "complete-source-validation",
        "selection_algorithm": "complete-source-validation-manifest-order-v1",
        "source_labels_used_for_selection": False,
        "target_label_used": False,
    }
    receipt_path = expanded / "source-validation-extension-receipt.json"
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shutil.rmtree(role_dir)
    os.replace(expanded, role_dir)
    return {
        path.stem: path for path in role_dir.glob("*.npy")
    }, full_sequences, role_dir / receipt_path.name


def prepare_crossyear_cache(config_path: Path, output_dir: Path) -> dict[str, object]:
    """校验 Rust 正式制品并发布四角色只读训练缓存。"""
    config_path = Path(config_path).resolve()
    config = _read_json(config_path, "跨年度配置")
    project_root_raw = _required_string(config, "project_root", "跨年度配置")
    output_root_raw = _required_string(config, "output_root", "跨年度配置")
    project_root_path = Path(project_root_raw)
    output_root_path = Path(output_root_raw)
    if not project_root_path.is_absolute() or not output_root_path.is_absolute():
        raise CrossyearDatasetError("项目根和正式输出根必须是绝对路径")
    project_root = project_root_path.resolve()
    output_root = output_root_path.resolve()
    if not output_root.is_relative_to(project_root):
        raise CrossyearDatasetError("正式输出根必须位于项目根内")
    roots = (project_root, output_root)
    output_dir = _checked_path(str(output_dir), roots, "Python 缓存输出目录", file=False)
    if output_dir.exists():
        raise CrossyearDatasetError("已有完整输出拒绝覆盖")
    (
        dataset_path,
        experiment_path,
        dataset,
        experiment,
        artifacts,
        fields,
        normalizer_path,
        bounded_quick_cache,
    ) = _validate_manifest_pair(config, roots)
    role_rows = _role_counts(dataset, "cache_rows")
    role_sequences = _role_counts(dataset, "role_sequences")
    semantic_key = "prescreen_role_semantic_sha256" if bounded_quick_cache else "role_semantic_sha256"
    semantic = _role_counts(dataset, semantic_key)
    if dataset.get("final_feature_artifacts") or dataset.get("final_label_artifacts") or dataset.get("final_member_artifacts") or dataset.get("final_specific_statistics"):
        raise CrossyearDatasetError("开发清单含最终区制品或统计")
    staging = output_dir.with_name(output_dir.name + f".partial.{os.getpid()}")
    if staging.exists():
        raise CrossyearDatasetError("缓存暂存目录已存在")
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir()
    try:
        roles: dict[str, CrossyearFeatureRole] = {}
        target_evaluation: TargetDevelopmentEvaluation | None = None
        extension_receipt_path: Path | None = None
        for role in ROLES:
            expected_rows = role_rows[role]
            expected_sequences = role_sequences[role]
            if not isinstance(expected_rows, int) or not isinstance(expected_sequences, int) or expected_rows <= 0 or expected_sequences <= 0:
                raise CrossyearDatasetError(f"{role} 清单行数或序列数不合法")
            if not isinstance(semantic[role], str) or len(semantic[role]) != 64:
                raise CrossyearDatasetError(f"{role} 缺少语义哈希")
            cache_path = _artifact_path(artifacts, f"{role}:cache", roots)
            label_path = None if role == "target-prefix" else _artifact_path(artifacts, f"{role}:labels", roots)
            _require_parquet_columns(cache_path, CACHE_COLUMNS, f"{role} 缓存")
            if not bounded_quick_cache:
                group_path = _artifact_path(artifacts, f"{role}:group_keys", roots)
                _require_parquet_columns(group_path, ("sample_id", "pair_key"), f"{role} 分组旁车")
            if label_path is not None:
                _require_parquet_columns(label_path, ("sample_id", "label"), f"{role} 标签旁车")
            elif f"{role}:labels" in artifacts:
                raise CrossyearDatasetError("target-prefix 不得登记标签制品")
            arrays, sequence_count = _validate_role_block(
                role,
                cache_path,
                expected_rows,
                expected_sequences,
                staging,
                label_path,
                include_group_key_ref=bounded_quick_cache,
            )
            public_arrays = {name: path for name, path in arrays.items() if name != "labels"}
            if role in ("source-train", "source-validation"):
                roles[role] = CrossyearLabeledRole(role, staging / f"role={role}", expected_rows, sequence_count, public_arrays, arrays["labels"])
            else:
                roles[role] = CrossyearFeatureRole(role, staging / f"role={role}", expected_rows, sequence_count, public_arrays)
            if role == "target-development":
                target_evaluation = TargetDevelopmentEvaluation(arrays["labels"], expected_rows)
        source_validation = roles["source-validation"]
        if not isinstance(source_validation, CrossyearLabeledRole):
            raise CrossyearDatasetError("source-validation 必须具有源年度标签旁车")
        sample_manifest = _artifact_path(artifacts, "sample_manifest", roots)
        sequence_manifest = _artifact_path(artifacts, "sequence_manifest", roots)
        _require_parquet_columns(
            sample_manifest,
            ("sample_id", "year_role", "sequence_id", "position", "valid_length", "available_ns", "cache_selected"),
            "样本清单",
        )
        _require_parquet_columns(
            sequence_manifest,
            ("sequence_id", "year_role", "group_key_ref", "valid_length", "first_available_ns", "last_available_ns", "cache_selected"),
            "序列清单",
        )
        if bounded_quick_cache:
            for role in ROLES:
                _validate_bounded_role_manifests(
                    role,
                    _artifact_path(artifacts, f"{role}:cache", roots),
                    sample_manifest,
                    sequence_manifest,
                    int(role_rows[role]),
                    int(role_sequences[role]),
                )
            receipt_path, receipt = _validate_bounded_receipts(
                artifacts,
                roots,
                role_rows,
                role_sequences,
                dataset.get("role_row_limits"),
                dataset.get("pair_hash_keep_thresholds"),
            )
        else:
            main_path = _artifact_path(artifacts, "source-validation:main_product", roots)
            normalizer = _read_json(normalizer_path, "归一化器")
            source_arrays, source_sequences, extension_receipt_path = _expand_source_validation(
                source_validation.cache_dir,
                main_path,
                sample_manifest,
                sequence_manifest,
                source_validation.labels,
                fields,
                normalizer,
                staging,
            )
            if extension_receipt_path is not None:
                public_arrays = {name: path for name, path in source_arrays.items() if name != "labels"}
                roles["source-validation"] = CrossyearLabeledRole(
                    "source-validation",
                    source_validation.cache_dir,
                    int(np.load(source_arrays["labels"], mmap_mode="r").shape[0]),
                    source_sequences,
                    public_arrays,
                    source_arrays["labels"],
                )
            receipt_path = _artifact_path(artifacts, "selection_receipt", roots)
            receipt = _read_json(receipt_path, "选择收据")
        if target_evaluation is None:
            raise CrossyearDatasetError("目标开发评价标签未发布")
        source_receipt = receipt.get("roles", {}).get("source-train") if isinstance(receipt.get("roles"), Mapping) else None
        if not isinstance(source_receipt, Mapping):
            raise CrossyearDatasetError("选择收据缺少 source-train 池信息")
        selection_hash = _sha256(receipt_path)
        array_manifest = {
            name: {
                key: _array_record(
                    path,
                    np.load(path, mmap_mode="r"),
                    output_dir / path.relative_to(staging),
                )
                for key, path in item.arrays.items()
            }
            | (
                {
                    "labels": _array_record(
                        item.labels,
                        np.load(item.labels, mmap_mode="r"),
                        output_dir / item.labels.relative_to(staging),
                    )
                }
                if isinstance(item, CrossyearLabeledRole)
                else {}
            )
            for name, item in roles.items()
        }
        metadata: dict[str, object] = {
            "schema_version": CACHE_SCHEMA,
            "formal_cache_root": str(output_dir),
            "dataset_manifest": str(dataset_path),
            "dataset_manifest_sha256": _sha256(dataset_path),
            "experiment_manifest": str(experiment_path),
            "experiment_manifest_sha256": _sha256(experiment_path),
            "model_fields": list(fields),
            "normalizer": {"path": str(normalizer_path), "sha256": _sha256(normalizer_path), "metadata": _read_json(normalizer_path, "归一化器")},
            "roles": {name: {"row_count": item.row_count, "sequence_count": item.sequence_count, "arrays": {key: str(value) for key, value in item.arrays.items()}} for name, item in roles.items()},
            "target_development_evaluation": {
                "labels": _array_record(
                    target_evaluation.labels,
                    np.load(target_evaluation.labels, mmap_mode="r"),
                    output_dir / target_evaluation.labels.relative_to(staging),
                ),
                "row_count": target_evaluation.row_count,
            },
            "arrays": array_manifest,
            "source_train_selection": dict(source_receipt),
            "selection_receipt_sha256": selection_hash,
            "source_validation_extension_receipt_sha256": _sha256(extension_receipt_path) if extension_receipt_path else None,
            "final_accessed": False,
        }
        if bounded_quick_cache:
            metadata["materialization_mode"] = BOUNDED_QUICK_CACHE_MODE
            metadata["sample_manifest_sha256"] = _sha256(sample_manifest)
            metadata["sequence_manifest_sha256"] = _sha256(sequence_manifest)
        manifest_path = staging / "cache-manifest.json"
        manifest_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        metadata["cache_manifest_sha256"] = _sha256(manifest_path)
        os.replace(staging, output_dir)
        for path in output_dir.rglob("*"):
            if path.is_file():
                path.chmod(0o444)
            elif path.is_dir():
                path.chmod(0o555)
        output_dir.chmod(0o555)
        return {**metadata, "formal_cache_root": output_dir, "roles": roles, "target_development_evaluation": target_evaluation}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
