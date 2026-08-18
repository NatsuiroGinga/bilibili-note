"""跨年度实体级评价 Q0：冻结有界缓存的分批读取、校验与收据。

只读消费 `runs/data-prepared/lspr23-lspr24-bounded-quick-q0-v1/`，**不重新物化**。

内存纪律（2026-08-12 三进程内存耗尽事故根因）：
- 按 Parquet row group 再按批读取，禁止整表 Arrow 与 NumPy 副本同时驻留；
- 每个角色读完立即释放 Arrow 对象，只保留预分配的 NumPy 结果；
- 固定长度列表用 `pyarrow.compute.list_flatten` 展平，避免直接取 `array.values`
  全缓冲区造成的批次长度漂移（局部规则已登记该事故）。

时间无关特征筛选（M1，Gehri 2023）属于阶段二任务，本模块暂不实现；阶段一只需要
`B0` 所需的共同 155 维输入。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from flow_probe.crossyear_entity_eval_contract import (
    ENTITY_KEY_BYTES,
    ENTITY_KEY_COLUMN,
    EntityEvalError,
    FEATURE_DEFINITION,
    FEATURE_DIMENSION,
    FEATURE_FIELD_COUNT,
    ROLES,
    assert_entity_key_not_in_features,
    binary_label_mask,
    entity_codes,
    memory_snapshot,
    read_json,
    sha256_array,
    sha256_file,
)

logger = logging.getLogger(__name__)

BATCH_ROWS = 32768
SAMPLE_ID_BYTES = 32

FEATURE_COLUMNS: tuple[str, ...] = (
    "sample_id",
    "sequence_id",
    ENTITY_KEY_COLUMN,
    "available_ns",
    "delta_t_us",
    "padding_mask",
    "x_value",
    "x_missing",
)


#: 标签装载模式。`defer` 用于目标开发区：分数封存完成后才允许打开标签。
LABEL_MODES: tuple[str, ...] = ("load", "defer", "forbid")


@dataclass(frozen=True)
class RoleData:
    """单个角色的冻结输入。实体键只保存组码，不进入特征矩阵。"""

    role: str
    features: np.ndarray
    labels: np.ndarray | None
    entity_code: np.ndarray
    entity_unique_count: int
    available_ns: np.ndarray
    sample_id: np.ndarray
    sample_id_sha256: str
    row_count: int
    dropped_non_binary_label_rows: int
    label_mode: str
    feature_paths: tuple[str, ...]


def _fixed_list_to_matrix(array: pa.Array, list_size: int, dtype: Any) -> np.ndarray:
    """把 `fixed_size_list` 批次安全展平为 `(n, list_size)` 矩阵。"""
    if not pa.types.is_fixed_size_list(array.type):
        raise EntityEvalError(f"期望 fixed_size_list，实际 {array.type}")
    if array.type.list_size != list_size:
        raise EntityEvalError(f"list_size 不匹配：期望 {list_size}，实际 {array.type.list_size}")
    flat = pc.list_flatten(array)
    values = np.asarray(flat.to_numpy(zero_copy_only=False))
    expected = len(array) * list_size
    if values.shape[0] != expected:
        raise EntityEvalError(f"展平长度漂移：期望 {expected}，实际 {values.shape[0]}")
    return values.reshape(len(array), list_size).astype(dtype, copy=False)


def _fixed_binary_to_matrix(array: pa.Array, width: int) -> np.ndarray:
    """把 `fixed_size_binary[width]` 批次按父数组 offset 安全切成 `(n, width)` uint8。"""
    if not pa.types.is_fixed_size_binary(array.type):
        raise EntityEvalError(f"期望 fixed_size_binary，实际 {array.type}")
    if array.type.byte_width != width:
        raise EntityEvalError(f"byte_width 不匹配：期望 {width}，实际 {array.type.byte_width}")
    if array.null_count:
        raise EntityEvalError("固定二进制列不允许空值")
    buffer = array.buffers()[1]
    if buffer is None:
        raise EntityEvalError("固定二进制列缺少数据缓冲区")
    raw = np.frombuffer(buffer, dtype=np.uint8, count=len(array) * width, offset=array.offset * width)
    return raw.reshape(len(array), width)


def _column(batch: pa.RecordBatch, name: str) -> pa.Array:
    index = batch.schema.get_field_index(name)
    if index < 0:
        raise EntityEvalError(f"缓存批次缺少列：{name}")
    return batch.column(index)


def _load_labels(path: Path, expected_sample_id: np.ndarray) -> np.ndarray:
    """读取标签旁车并按 `sample_id` 逐行核对顺序，禁止依赖行数相等的隐式假设。"""
    handle = pq.ParquetFile(path)
    labels = np.empty(handle.metadata.num_rows, dtype=np.uint8)
    sample_ids = np.empty((handle.metadata.num_rows, SAMPLE_ID_BYTES), dtype=np.uint8)
    offset = 0
    for group in range(handle.num_row_groups):
        for batch in handle.iter_batches(batch_size=BATCH_ROWS, row_groups=[group], columns=["sample_id", "label"]):
            count = batch.num_rows
            labels[offset : offset + count] = np.asarray(_column(batch, "label").to_numpy(zero_copy_only=False), dtype=np.uint8)
            sample_ids[offset : offset + count] = _fixed_binary_to_matrix(_column(batch, "sample_id"), SAMPLE_ID_BYTES)
            offset += count
    if offset != labels.shape[0]:
        raise EntityEvalError(f"标签旁车行数不一致：{path}")
    if sample_ids.shape != expected_sample_id.shape or not np.array_equal(sample_ids, expected_sample_id):
        raise EntityEvalError(f"标签旁车 sample_id 顺序与特征不一致：{path}")
    return labels


def load_role(cache_root: Path, role: str, *, label_mode: str) -> RoleData:
    """分批读取单个角色，产出共同 155 维输入、实体组码与可观测时间。

    Args:
        cache_root: 冻结实验缓存根。
        role: 四个合法角色之一。
        label_mode: `load` 立即读取标签（源年度）；`defer` 推迟到分数封存之后
            （目标开发区）；`forbid` 断言该角色没有标签旁车（目标前缀）。
    """
    if role not in ROLES:
        raise EntityEvalError(f"未知角色：{role}")
    if label_mode not in LABEL_MODES:
        raise EntityEvalError(f"未知标签装载模式：{label_mode}")
    role_dir = Path(cache_root) / f"role={role}"
    feature_path = role_dir / "part-00000.parquet"
    if not feature_path.is_file():
        raise EntityEvalError(f"缺少角色缓存：{feature_path}")
    handle = pq.ParquetFile(feature_path)
    rows = handle.metadata.num_rows

    features = np.empty((rows, FEATURE_DIMENSION), dtype=np.float32)
    entity_raw = np.empty((rows, ENTITY_KEY_BYTES), dtype=np.uint8)
    sample_id = np.empty((rows, SAMPLE_ID_BYTES), dtype=np.uint8)
    available_ns = np.empty(rows, dtype=np.int64)

    offset = 0
    for group in range(handle.num_row_groups):
        for batch in handle.iter_batches(batch_size=BATCH_ROWS, row_groups=[group], columns=list(FEATURE_COLUMNS)):
            count = batch.num_rows
            padding = np.asarray(_column(batch, "padding_mask").to_numpy(zero_copy_only=False), dtype=np.uint8)
            if not bool((padding == 1).all()):
                raise EntityEvalError(f"{role} 存在填充位，冻结缓存应只含有效流")
            value = _fixed_list_to_matrix(_column(batch, "x_value"), FEATURE_FIELD_COUNT, np.float32)
            missing = _fixed_list_to_matrix(_column(batch, "x_missing"), FEATURE_FIELD_COUNT, np.float32)
            delta = np.asarray(_column(batch, "delta_t_us").to_numpy(zero_copy_only=False), dtype=np.float64)
            delta = np.log1p(np.maximum(delta, 0.0)).astype(np.float32)
            features[offset : offset + count, :FEATURE_FIELD_COUNT] = value
            features[offset : offset + count, FEATURE_FIELD_COUNT : 2 * FEATURE_FIELD_COUNT] = missing
            features[offset : offset + count, 2 * FEATURE_FIELD_COUNT] = delta
            entity_raw[offset : offset + count] = _fixed_binary_to_matrix(_column(batch, ENTITY_KEY_COLUMN), ENTITY_KEY_BYTES)
            sample_id[offset : offset + count] = _fixed_binary_to_matrix(_column(batch, "sample_id"), SAMPLE_ID_BYTES)
            available_ns[offset : offset + count] = np.asarray(
                _column(batch, "available_ns").to_numpy(zero_copy_only=False), dtype=np.int64
            )
            offset += count
            del batch, value, missing, delta, padding
    if offset != rows:
        raise EntityEvalError(f"{role} 读取行数 {offset} 与元数据 {rows} 不一致")
    if not np.isfinite(features).all():
        raise EntityEvalError(f"{role} 共同输入含非有限数值")
    assert_entity_key_not_in_features(features, FEATURE_DEFINITION)

    labels: np.ndarray | None = None
    dropped = 0
    label_path = role_dir / "labels.parquet"
    if label_mode == "load":
        if not label_path.is_file():
            raise EntityEvalError(f"缺少标签旁车：{label_path}")
        labels = _load_labels(label_path, sample_id)
        keep = binary_label_mask(labels)
        dropped = int((~keep).sum())
        if dropped:
            features = features[keep]
            entity_raw = entity_raw[keep]
            sample_id = sample_id[keep]
            available_ns = available_ns[keep]
            labels = labels[keep]
        logger.info("[数据] %s 强制 np.isin(label,(0,1)) 过滤，剔除 %d 行", role, dropped)
    elif label_mode == "forbid" and label_path.is_file():
        raise EntityEvalError(f"{role} 不应存在标签旁车：{label_path}")

    codes, unique = entity_codes(entity_raw)
    snapshot = memory_snapshot(f"load:{role}")
    logger.info(
        "[数据] %s 行数=%d 实体数=%d 剔除非二元标签=%d VmRSS=%s GiB",
        role,
        features.shape[0],
        len(unique),
        dropped,
        snapshot["vmrss_gib"],
    )
    return RoleData(
        role=role,
        features=features,
        labels=labels,
        entity_code=codes,
        entity_unique_count=int(len(unique)),
        available_ns=available_ns,
        sample_id=sample_id,
        sample_id_sha256=sha256_array(sample_id),
        row_count=int(features.shape[0]),
        dropped_non_binary_label_rows=dropped,
        label_mode=label_mode,
        feature_paths=(str(feature_path),) + ((str(label_path),) if label_mode == "load" else ()),
    )


def open_deferred_labels(cache_root: Path, data: RoleData) -> tuple[np.ndarray, np.ndarray, int]:
    """分数封存完成后才调用：打开目标开发区标签并执行强制二元过滤。

    Returns:
        `(labels, keep_mask, dropped)`；`keep_mask` 对齐已封存的逐流分数顺序。
    """
    if data.label_mode != "defer":
        raise EntityEvalError(f"{data.role} 不是推迟装载模式，禁止在此打开标签")
    label_path = Path(cache_root) / f"role={data.role}" / "labels.parquet"
    if not label_path.is_file():
        raise EntityEvalError(f"缺少标签旁车：{label_path}")
    labels = _load_labels(label_path, data.sample_id)
    keep = binary_label_mask(labels)
    dropped = int((~keep).sum())
    logger.info("[数据] %s 封存后打开标签，强制 np.isin(label,(0,1)) 过滤，剔除 %d 行", data.role, dropped)
    return labels, keep, dropped


def dataset_receipts(dataset_root: Path) -> tuple[Mapping[str, Any], Mapping[str, Any], Path]:
    """读取数据集与实验收据，返回 `(dataset_manifest, experiment_manifest, cache_root)`。"""
    dataset_root = Path(dataset_root)
    dataset_manifest = read_json(dataset_root / "dataset-manifest.json")
    artifacts = dataset_manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise EntityEvalError("数据集收据缺少 artifacts")
    cache_entry = artifacts.get("target-development:cache")
    if not isinstance(cache_entry, dict):
        raise EntityEvalError("数据集收据缺少 target-development:cache")
    cache_root = Path(str(cache_entry["path"])).parent.parent
    experiment_manifest = read_json(cache_root / "experiment-manifest.json")
    if experiment_manifest.get("labels_outside_features") is not True:
        raise EntityEvalError("实验收据未声明 labels_outside_features=true")
    if experiment_manifest.get("group_key_outside_features") is not True:
        raise EntityEvalError("实验收据未声明 group_key_outside_features=true")
    return dataset_manifest, experiment_manifest, cache_root


def verify_artifact_hashes(dataset_manifest: Mapping[str, Any], keys: Sequence[str]) -> dict[str, str]:
    """核验消费到的制品 SHA-256 与数据集收据一致。"""
    artifacts = dataset_manifest["artifacts"]
    verified: dict[str, str] = {}
    for key in keys:
        record = artifacts.get(key)
        if not isinstance(record, dict):
            raise EntityEvalError(f"数据集收据缺少制品：{key}")
        path = Path(str(record["path"]))
        digest = sha256_file(path)
        if digest != record.get("sha256"):
            raise EntityEvalError(f"制品 SHA-256 不匹配：{key} -> {path}")
        verified[key] = digest
    return verified


def input_receipt(dataset_manifest: Mapping[str, Any], roles: Mapping[str, RoleData], verified: Mapping[str, str]) -> dict[str, Any]:
    """输入收据：哈希、行数、实体数、标签分布与时间范围。"""
    detail: dict[str, Any] = {}
    for role, data in roles.items():
        entry: dict[str, Any] = {
            "row_count": data.row_count,
            "entity_count": data.entity_unique_count,
            "sample_id_sha256": data.sample_id_sha256,
            "dropped_non_binary_label_rows": data.dropped_non_binary_label_rows,
            "available_ns_min": int(data.available_ns.min()),
            "available_ns_max": int(data.available_ns.max()),
            "paths": list(data.feature_paths),
        }
        if data.labels is not None:
            positives = int((data.labels == 1).sum())
            entry["positive_flow_count"] = positives
            entry["flow_positive_rate"] = positives / max(data.row_count, 1)
        detail[role] = entry
    return {
        "contract_version": dataset_manifest.get("contract_version"),
        "materialization_mode": dataset_manifest.get("materialization_mode"),
        "budget_tier": dataset_manifest.get("budget_tier"),
        "pair_hash_keep_thresholds": dataset_manifest.get("pair_hash_keep_thresholds"),
        "isolated_rows": dataset_manifest.get("isolated_rows"),
        "splits": dataset_manifest.get("splits"),
        "verified_artifact_sha256": dict(verified),
        "roles": detail,
        "final_accessed": False,
    }
