"""Protocol A Raw83 共享事实源与权限分离加载器。"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Literal, Mapping, Sequence

import numpy as np

from dijk2026_replication.dijk_fields import (
    DIJK_FEATURES,
    LABEL_COLUMN,
    RANDOM_SEED,
    SEQUENCE_LENGTH,
    TIME_START_COLUMN,
)

SCHEMA_VERSION = "ch3-protocol-a-raw83-shared-v1"
FINITE_NEGATIVE_POLICY = "preserve_and_count-v1"
SOURCE_YEAR = "LSPR23"
TARGET_YEAR = "LSPR24"
SOURCE_ROW_COUNT = 16_353_511
SOURCE_SEQUENCE_COUNT = 271_815
SOURCE_ENTITY_COUNT = 150_680
TRAIN_SEQUENCE_COUNT = 208_598
VALIDATION_SEQUENCE_COUNT = 22_444
PORT_INDICES = (0, 1)
PROTOCOL_INDICES = (2, 79)
BINARY_INDICES = (80, 81, 82)
QUANTILE_INDICES = tuple(range(3, 79))
SPECIAL_INDICES = PORT_INDICES + PROTOCOL_INDICES + BINARY_INDICES
IP_COLUMNS = ("SrcIP", "DstIP")
PURPOSES = ("fit", "train", "validate", "target-evaluate")
FORBIDDEN_ARTIFACT_NAMES = {
    "y23.npy",
    "y24.npy",
    "labels.parquet",
    "predictions.npy",
    "flow_predictions.npy",
    "entity_predictions.npy",
}


class ProtocolARaw83Error(RuntimeError):
    """Raw83 合同、数据或权限门失败。"""


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path, *, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk_bytes):
            digest.update(block)
    return digest.hexdigest()


def md5_file(path: Path, *, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        while block := handle.read(chunk_bytes):
            digest.update(block)
    return digest.hexdigest()


def atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_bytes(canonical_json_bytes(value) + b"\n")
    os.replace(temporary, path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProtocolARaw83Error(f"JSON 顶层必须为对象：{path}")
    return value


def schema_contract() -> dict[str, Any]:
    fields = []
    for index, name in enumerate(DIJK_FEATURES):
        if index in PORT_INDICES:
            role = "port-integer-0-65535"
        elif index in PROTOCOL_INDICES:
            role = "protocol-integer"
        elif index in BINARY_INDICES:
            role = "binary-0-1"
        else:
            role = "finite-numeric-preserve-negative"
        fields.append(
            {
                "index": index,
                "name": name,
                "canonical_dtype": "<f4",
                "role": role,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "field_count": len(DIJK_FEATURES),
        "fields": fields,
        "finite_negative_policy": FINITE_NEGATIVE_POLICY,
        "missing_policy": "canonical-little-endian-float32-nan-v1",
        "raw_ip_policy": "entity-grouping-only-not-model-feature-v1",
        "source_record_key": "sha256(source_sha256||year||raw_row_index)-v1",
    }


FIELD_LIST_SHA256 = canonical_sha256(list(DIJK_FEATURES))
SCHEMA_SHA256 = canonical_sha256(schema_contract())


def validate_config(config: Mapping[str, Any]) -> None:
    required_top = {
        "schema_version",
        "run_id",
        "display_name",
        "dependencies",
        "source",
        "target",
        "protocol_a",
        "preprocessing",
        "paths",
        "resources",
        "vendor",
    }
    missing = sorted(required_top - set(config))
    if missing:
        raise ProtocolARaw83Error(f"配置缺少顶层键：{missing}")
    if config["schema_version"] != SCHEMA_VERSION:
        raise ProtocolARaw83Error("配置模式版本不匹配")
    if config["source"]["year"] != SOURCE_YEAR:
        raise ProtocolARaw83Error("默认生产入口只允许 LSPR23")
    if config["source"]["expected_rows"] != SOURCE_ROW_COUNT:
        raise ProtocolARaw83Error("LSPR23 预期行数不匹配")
    if config["source"]["inner_csv"] != "ls23pr_v1.csv":
        raise ProtocolARaw83Error("LSPR23 ZIP 内部成员名不匹配")
    if config["target"]["default_enabled"] is not False:
        raise ProtocolARaw83Error("目标年默认必须禁用")
    if config["target"]["required_purpose"] != "target-evaluate":
        raise ProtocolARaw83Error("目标年用途合同不匹配")
    if tuple(config["protocol_a"]["feature_names"]) != DIJK_FEATURES:
        raise ProtocolARaw83Error("字段顺序必须逐字等于 DIJK_FEATURES")
    if config["protocol_a"]["field_list_sha256"] != FIELD_LIST_SHA256:
        raise ProtocolARaw83Error("字段清单 SHA-256 不匹配")
    if config["protocol_a"]["sequence_length"] != SEQUENCE_LENGTH:
        raise ProtocolARaw83Error("Protocol A 序列长度必须为 128")
    if config["protocol_a"]["seed"] != RANDOM_SEED:
        raise ProtocolARaw83Error("Protocol A 种子必须为 42")
    if config["protocol_a"]["finite_negative_policy"] != FINITE_NEGATIVE_POLICY:
        raise ProtocolARaw83Error("有限负值策略不匹配")
    if config["protocol_a"]["expected_counts"] != {
        "entities": SOURCE_ENTITY_COUNT,
        "sequences": SOURCE_SEQUENCE_COUNT,
        "train_sequences": TRAIN_SEQUENCE_COUNT,
        "validation_sequences": VALIDATION_SEQUENCE_COUNT,
    }:
        raise ProtocolARaw83Error("Protocol A 冻结计数不匹配")
    paths = config["paths"]
    if not Path(paths["output_root"]).is_absolute():
        raise ProtocolARaw83Error("输出根必须为绝对路径")
    if Path(paths["dataset_manifest"]).name != "dataset-manifest.json":
        raise ProtocolARaw83Error("唯一发现入口必须名为 dataset-manifest.json")
    forbidden = set(config["protocol_a"].get("forbidden_artifact_names", []))
    if forbidden != FORBIDDEN_ARTIFACT_NAMES:
        raise ProtocolARaw83Error("禁止制品清单不完整")


@dataclass(frozen=True)
class SourceBatch:
    batch_index: int
    start_row: int
    end_row: int
    raw83: np.ndarray
    src_ip: tuple[str, ...]
    dst_ip: tuple[str, ...]
    start_time_ns: np.ndarray
    labels: np.ndarray
    nonfinite_counts: np.ndarray
    structural_invalid_counts: np.ndarray


def _arrow_to_float64(column: Any) -> np.ndarray:
    return np.asarray(column.to_numpy(zero_copy_only=False), dtype=np.float64)


def _arrow_to_int64(column: Any) -> np.ndarray:
    return np.asarray(column.to_numpy(zero_copy_only=False), dtype=np.int64)


def _canonicalize_raw83(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if values.ndim != 2 or values.shape[1] != len(DIJK_FEATURES):
        raise ProtocolARaw83Error(f"Raw83 批形状非法：{values.shape}")
    finite = np.isfinite(values)
    valid = finite.copy()
    for index in PORT_INDICES:
        column = values[:, index]
        valid[:, index] &= (column == np.rint(column)) & (column >= 0) & (column <= 65_535)
    for index in PROTOCOL_INDICES:
        column = values[:, index]
        valid[:, index] &= column == np.rint(column)
    for index in BINARY_INDICES:
        column = values[:, index]
        valid[:, index] &= (column == 0) | (column == 1)
    normalized = np.asarray(values, dtype="<f4", order="C")
    normalized[~valid] = np.array(np.nan, dtype="<f4")
    return (
        normalized,
        np.count_nonzero(~finite, axis=0).astype("<i8"),
        np.count_nonzero(finite & ~valid, axis=0).astype("<i8"),
    )


def _parse_binary_labels(values: Sequence[Any]) -> np.ndarray:
    parsed = np.empty(len(values), dtype=np.uint8)
    for index, value in enumerate(values):
        text = str(value).strip()
        if text in {"0", "0.0", "False", "false", "BENIGN", "Benign", "benign"}:
            parsed[index] = 0
        elif text in {"1", "1.0", "True", "true", "MALICIOUS", "Malicious", "malicious"}:
            parsed[index] = 1
        else:
            raise ProtocolARaw83Error(f"遇到非二元标签：{text!r}")
    return parsed


def iter_lspr23_batches(
    zip_path: Path,
    *,
    inner_csv: str,
    block_size: int,
) -> Iterator[SourceBatch]:
    """PyArrow 单线程流式读取 ZIP 内 CSV，不构造全量表。"""

    import pyarrow as pa
    import pyarrow.csv as pacsv

    selected = list(DIJK_FEATURES) + [*IP_COLUMNS, TIME_START_COLUMN, LABEL_COLUMN]
    column_types = {name: pa.float64() for name in DIJK_FEATURES}
    column_types.update(
        {
            IP_COLUMNS[0]: pa.string(),
            IP_COLUMNS[1]: pa.string(),
            TIME_START_COLUMN: pa.int64(),
            LABEL_COLUMN: pa.string(),
        }
    )
    convert_options = pacsv.ConvertOptions(
        include_columns=selected,
        column_types=column_types,
        strings_can_be_null=False,
    )
    read_options = pacsv.ReadOptions(use_threads=False, block_size=block_size)
    with zipfile.ZipFile(zip_path) as archive:
        csv_members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if csv_members != [inner_csv]:
            raise ProtocolARaw83Error(f"ZIP CSV 成员不匹配：{csv_members}")
        with archive.open(inner_csv, "r") as source:
            reader = pacsv.open_csv(
                source,
                read_options=read_options,
                convert_options=convert_options,
            )
            offset = 0
            for batch_index, batch in enumerate(reader):
                count = batch.num_rows
                values = np.empty((count, len(DIJK_FEATURES)), dtype=np.float64)
                for feature_index, name in enumerate(DIJK_FEATURES):
                    values[:, feature_index] = _arrow_to_float64(batch.column(name))
                raw83, nonfinite_counts, structural_invalid_counts = _canonicalize_raw83(values)
                del values
                src_ip = tuple(str(value) for value in batch.column(IP_COLUMNS[0]).to_pylist())
                dst_ip = tuple(str(value) for value in batch.column(IP_COLUMNS[1]).to_pylist())
                start_time = _arrow_to_int64(batch.column(TIME_START_COLUMN))
                labels = _parse_binary_labels(batch.column(LABEL_COLUMN).to_pylist())
                yield SourceBatch(
                    batch_index=batch_index,
                    start_row=offset,
                    end_row=offset + count,
                    raw83=raw83,
                    src_ip=src_ip,
                    dst_ip=dst_ip,
                    start_time_ns=start_time,
                    labels=labels,
                    nonfinite_counts=nonfinite_counts,
                    structural_invalid_counts=structural_invalid_counts,
                )
                offset += count


def entity_digest(src_ip: str, dst_ip: str) -> bytes:
    left, right = sorted((src_ip, dst_ip))
    digest = hashlib.sha256()
    for value in (left, right):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "little"))
        digest.update(encoded)
    return digest.digest()


class FeatureStatistics:
    """83 列固定上界统计，用 Kahan 补偿累加。"""

    def __init__(self) -> None:
        width = len(DIJK_FEATURES)
        self.total = np.zeros(width, dtype=np.int64)
        self.nonfinite = np.zeros(width, dtype=np.int64)
        self.structural_invalid = np.zeros(width, dtype=np.int64)
        self.finite = np.zeros(width, dtype=np.int64)
        self.negative = np.zeros(width, dtype=np.int64)
        self.zero = np.zeros(width, dtype=np.int64)
        self.positive = np.zeros(width, dtype=np.int64)
        self.minimum = np.full(width, np.inf, dtype=np.float64)
        self.maximum = np.full(width, -np.inf, dtype=np.float64)
        self.sums = np.zeros(width, dtype=np.float64)
        self.compensation = np.zeros(width, dtype=np.float64)

    def update(
        self,
        raw83: np.ndarray,
        *,
        nonfinite_counts: np.ndarray,
        structural_invalid_counts: np.ndarray,
    ) -> None:
        count = raw83.shape[0]
        self.total += count
        self.nonfinite += nonfinite_counts
        self.structural_invalid += structural_invalid_counts
        for index in range(raw83.shape[1]):
            column = raw83[:, index].astype(np.float64, copy=False)
            mask = np.isfinite(column)
            valid = column[mask]
            self.finite[index] += valid.size
            if valid.size == 0:
                continue
            self.negative[index] += np.count_nonzero(valid < 0)
            self.zero[index] += np.count_nonzero(valid == 0)
            self.positive[index] += np.count_nonzero(valid > 0)
            self.minimum[index] = min(self.minimum[index], float(valid.min()))
            self.maximum[index] = max(self.maximum[index], float(valid.max()))
            batch_sum = float(valid.sum(dtype=np.float64))
            corrected = batch_sum - self.compensation[index]
            updated = self.sums[index] + corrected
            self.compensation[index] = (updated - self.sums[index]) - corrected
            self.sums[index] = updated

    def receipt(self) -> dict[str, Any]:
        fields = []
        for index, name in enumerate(DIJK_FEATURES):
            finite = int(self.finite[index])
            fields.append(
                {
                    "index": index,
                    "name": name,
                    "total": int(self.total[index]),
                    "nonfinite_or_missing": int(self.nonfinite[index]),
                    "structural_invalid": int(self.structural_invalid[index]),
                    "finite": finite,
                    "negative": int(self.negative[index]),
                    "zero": int(self.zero[index]),
                    "positive": int(self.positive[index]),
                    "minimum": None if finite == 0 else float(self.minimum[index]),
                    "maximum": None if finite == 0 else float(self.maximum[index]),
                    "sum": float(self.sums[index]),
                    "sum_compensation": float(self.compensation[index]),
                }
            )
        return {"finite_negative_policy": FINITE_NEGATIVE_POLICY, "fields": fields}


def _batch_content_sha(batch: SourceBatch, entity_ids: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(batch.raw83.tobytes(order="C"))
    digest.update(np.asarray(entity_ids, dtype="<u4").tobytes(order="C"))
    digest.update(np.asarray(batch.start_time_ns, dtype="<i8").tobytes(order="C"))
    return digest.hexdigest()


def _label_batch_sha(labels: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(labels, dtype=np.uint8).tobytes(order="C")).hexdigest()


def _open_partial_npy(path: Path, *, dtype: str, shape: tuple[int, ...]) -> np.memmap:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        array = np.load(path, mmap_mode="r+")
        if array.dtype != np.dtype(dtype) or array.shape != shape:
            raise ProtocolARaw83Error(f"断点文件形状或 dtype 不匹配：{path}")
        return array
    return np.lib.format.open_memmap(path, mode="w+", dtype=dtype, shape=shape)


def materialize_source_raw83(
    config: Mapping[str, Any],
    *,
    block_size: int,
) -> dict[str, Any]:
    validate_config(config)
    source_path = Path(config["source"]["zip_path"])
    output_root = Path(config["paths"]["output_root"])
    run_id = str(config["run_id"])
    expected_rows = int(config["source"]["expected_rows"])
    raw_final = output_root / "raw" / "lspr23-raw83.npy"
    entity_final = output_root / "sidecars" / "lspr23-flow-entity-id.npy"
    time_final = output_root / "sidecars" / "lspr23-start-time-ns.npy"
    raw_partial = raw_final.with_name(f"{raw_final.name}.partial.{run_id}")
    entity_partial = entity_final.with_name(f"{entity_final.name}.partial.{run_id}")
    time_partial = time_final.with_name(f"{time_final.name}.partial.{run_id}")
    receipts_root = output_root / "receipts" / "p1-batches"
    receipts_root.mkdir(parents=True, exist_ok=True)
    final_set = (raw_final, entity_final, time_final)
    partial_set = (raw_partial, entity_partial, time_partial)
    if all(path.exists() for path in final_set) and not any(path.exists() for path in partial_set):
        work_paths = final_set
        publish_partials = False
    elif any(receipts_root.iterdir()) and not all(path.exists() for path in partial_set):
        raise ProtocolARaw83Error("P1 批收据存在，但部分文件不完整")
    else:
        work_paths = partial_set
        publish_partials = True
    raw = _open_partial_npy(work_paths[0], dtype="<f4", shape=(expected_rows, len(DIJK_FEATURES)))
    entities = _open_partial_npy(work_paths[1], dtype="<u4", shape=(expected_rows,))
    times = _open_partial_npy(work_paths[2], dtype="<i8", shape=(expected_rows,))
    entity_ids: dict[bytes, int] = {}
    entity_summaries: list[str] = []
    feature_stats = FeatureStatistics()
    raw_digest = hashlib.sha256()
    entity_digest_full = hashlib.sha256()
    time_digest = hashlib.sha256()
    label_digest = hashlib.sha256()
    label_counts = np.zeros(2, dtype=np.int64)
    observed_rows = 0
    for batch in iter_lspr23_batches(
        source_path,
        inner_csv=str(config["source"]["inner_csv"]),
        block_size=block_size,
    ):
        ids = np.empty(batch.end_row - batch.start_row, dtype="<u4")
        for index, (src_ip, dst_ip) in enumerate(zip(batch.src_ip, batch.dst_ip)):
            digest = entity_digest(src_ip, dst_ip)
            entity_id = entity_ids.get(digest)
            if entity_id is None:
                entity_id = len(entity_summaries)
                if entity_id >= np.iinfo(np.uint32).max:
                    raise ProtocolARaw83Error("实体数超出 uint32 范围")
                entity_ids[digest] = entity_id
                entity_summaries.append(digest.hex())
            ids[index] = entity_id
        batch_sha = _batch_content_sha(batch, ids)
        feature_stats.update(
            batch.raw83,
            nonfinite_counts=batch.nonfinite_counts,
            structural_invalid_counts=batch.structural_invalid_counts,
        )
        raw_digest.update(batch.raw83.tobytes(order="C"))
        entity_bytes = ids.tobytes(order="C")
        time_bytes = np.asarray(batch.start_time_ns, dtype="<i8").tobytes(order="C")
        entity_digest_full.update(entity_bytes)
        time_digest.update(time_bytes)
        label_bytes = batch.labels.tobytes(order="C")
        label_digest.update(label_bytes)
        label_counts += np.bincount(batch.labels, minlength=2)
        cumulative_statistics_sha256 = canonical_sha256(feature_stats.receipt())
        receipt_path = receipts_root / f"batch-{batch.batch_index:06d}.json"
        if receipt_path.exists():
            receipt = load_json(receipt_path)
            expected = {
                "start_row": batch.start_row,
                "end_row": batch.end_row,
                "content_sha256": batch_sha,
                "label_sha256": _label_batch_sha(batch.labels),
                "cumulative_statistics_sha256": cumulative_statistics_sha256,
                "cumulative_raw_content_sha256": raw_digest.hexdigest(),
                "cumulative_label_content_sha256": label_digest.hexdigest(),
            }
            for key, value in expected.items():
                if receipt.get(key) != value:
                    raise ProtocolARaw83Error(f"断点批收据不匹配：{receipt_path}::{key}")
        else:
            raw[batch.start_row : batch.end_row] = batch.raw83
            entities[batch.start_row : batch.end_row] = ids
            times[batch.start_row : batch.end_row] = batch.start_time_ns
            raw.flush()
            entities.flush()
            times.flush()
            atomic_write_json(
                receipt_path,
                {
                    "schema_version": f"{SCHEMA_VERSION}-p1-batch-receipt-v1",
                    "batch_index": batch.batch_index,
                    "start_row": batch.start_row,
                    "end_row": batch.end_row,
                    "content_sha256": batch_sha,
                    "label_sha256": _label_batch_sha(batch.labels),
                    "cumulative_statistics_sha256": cumulative_statistics_sha256,
                    "cumulative_raw_content_sha256": raw_digest.hexdigest(),
                    "cumulative_label_content_sha256": label_digest.hexdigest(),
                },
            )
        observed_rows = batch.end_row
    if observed_rows != expected_rows:
        raise ProtocolARaw83Error(f"LSPR23 行数不匹配：{observed_rows} != {expected_rows}")
    if len(entity_summaries) != SOURCE_ENTITY_COUNT:
        raise ProtocolARaw83Error(
            f"LSPR23 实体数不匹配：{len(entity_summaries)} != {SOURCE_ENTITY_COUNT}"
        )
    stats = feature_stats.receipt()
    empty_fields = [field["name"] for field in stats["fields"] if field["finite"] == 0]
    if empty_fields:
        raise ProtocolARaw83Error(f"训练年出现无任何有限值的字段：{empty_fields}")
    del raw, entities, times
    if publish_partials:
        os.replace(raw_partial, raw_final)
        os.replace(entity_partial, entity_final)
        os.replace(time_partial, time_final)
    entity_summary_path = output_root / "sidecars" / "lspr23-entity-summaries.json"
    atomic_write_json(
        entity_summary_path,
        {
            "schema_version": f"{SCHEMA_VERSION}-entity-summaries-v1",
            "entity_count": len(entity_summaries),
            "summaries_sha256": canonical_sha256(entity_summaries),
            "summaries": entity_summaries,
        },
    )
    receipt = {
        "schema_version": f"{SCHEMA_VERSION}-p1-receipt-v1",
        "row_count": observed_rows,
        "entity_count": len(entity_summaries),
        "raw_content_sha256": raw_digest.hexdigest(),
        "entity_content_sha256": entity_digest_full.hexdigest(),
        "start_time_content_sha256": time_digest.hexdigest(),
        "label_content_sha256": label_digest.hexdigest(),
        "label_aggregate": {"negative": int(label_counts[0]), "positive": int(label_counts[1])},
        "label_rows_persisted": 0,
        "feature_statistics": stats,
        "artifacts": {
            "raw83": _artifact(raw_final),
            "flow_entity_id": _artifact(entity_final),
            "start_time_ns": _artifact(time_final),
            "entity_summaries": _artifact(entity_summary_path),
        },
    }
    atomic_write_json(output_root / "receipts" / "p1-source-raw83.json", receipt)
    return receipt


def _artifact(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if path.is_symlink():
        raise ProtocolARaw83Error(f"制品不允许是符号链接：{path}")
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def _save_npy_atomic(path: Path, values: np.ndarray, run_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{run_id}")
    with temporary.open("wb") as handle:
        np.save(handle, values, allow_pickle=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def bind_protocol_a_split(config: Mapping[str, Any]) -> dict[str, Any]:
    validate_config(config)
    output_root = Path(config["paths"]["output_root"])
    cache_root = Path(config["paths"]["legacy_protocol_a_cache"])
    run_id = str(config["run_id"])
    arrays: dict[str, np.ndarray] = {}
    identities: dict[str, Any] = {}
    for name in ("I23", "M23", "E23", "T23"):
        path = cache_root / f"{name}.npy"
        if not path.is_file() or path.is_symlink():
            raise ProtocolARaw83Error(f"Protocol A 原数组缺失或为符号链接：{path}")
        arrays[name] = np.load(path, mmap_mode="r", allow_pickle=False)
        identities[name] = _artifact(path)
    I = arrays["I23"]
    M = arrays["M23"]
    E = np.asarray(arrays["E23"])
    T = np.asarray(arrays["T23"])
    if I.shape != (SOURCE_SEQUENCE_COUNT, SEQUENCE_LENGTH) or M.shape != I.shape:
        raise ProtocolARaw83Error(f"I23/M23 形状不匹配：{I.shape}/{M.shape}")
    if E.shape != (SOURCE_SEQUENCE_COUNT,) or T.shape != E.shape:
        raise ProtocolARaw83Error("E23/T23 形状不匹配")
    if not np.all((M == 0) | (M == 1)):
        raise ProtocolARaw83Error("M23 存在非二元掩码")
    entity_sidecar = np.load(
        output_root / "sidecars" / "lspr23-flow-entity-id.npy",
        mmap_mode="r",
        allow_pickle=False,
    )
    time_sidecar = np.load(
        output_root / "sidecars" / "lspr23-start-time-ns.npy",
        mmap_mode="r",
        allow_pickle=False,
    )
    coverage = np.zeros(SOURCE_ROW_COUNT, dtype=np.uint8)
    e_to_sidecar: dict[int, int] = {}
    sidecar_to_e: dict[int, int] = {}
    for start in range(0, SOURCE_SEQUENCE_COUNT, 8_192):
        stop = min(start + 8_192, SOURCE_SEQUENCE_COUNT)
        batch_i = np.asarray(I[start:stop])
        batch_m = np.asarray(M[start:stop], dtype=bool)
        if np.any(batch_i[batch_m] < 0) or np.any(batch_i[batch_m] >= SOURCE_ROW_COUNT):
            raise ProtocolARaw83Error("I23 有效位置存在越界行号")
        flat = batch_i[batch_m]
        if np.any(coverage[flat] != 0):
            raise ProtocolARaw83Error("Protocol A 序列中存在重复流覆盖")
        coverage[flat] = 1
        for local in range(stop - start):
            mask = batch_m[local]
            indices = batch_i[local, mask]
            if indices.size == 0:
                raise ProtocolARaw83Error("Protocol A 序列不得为空")
            if np.any(~mask[: indices.size]) or np.any(mask[indices.size :]):
                raise ProtocolARaw83Error("填充掩码必须尾置")
            entity_values = np.unique(entity_sidecar[indices])
            if entity_values.size != 1:
                raise ProtocolARaw83Error("单序列跨越多个无向 IP 实体")
            old_entity = int(E[start + local])
            new_entity = int(entity_values[0])
            if old_entity in e_to_sidecar and e_to_sidecar[old_entity] != new_entity:
                raise ProtocolARaw83Error("E23 实体与流侧车非函数映射")
            if new_entity in sidecar_to_e and sidecar_to_e[new_entity] != old_entity:
                raise ProtocolARaw83Error("流侧车实体与 E23 非一一映射")
            e_to_sidecar[old_entity] = new_entity
            sidecar_to_e[new_entity] = old_entity
            sequence_times = np.asarray(time_sidecar[indices])
            if np.any(sequence_times[1:] < sequence_times[:-1]):
                raise ProtocolARaw83Error("序列内开始时间不单调")
            if np.float64(sequence_times[0]) != np.float64(T[start + local]):
                raise ProtocolARaw83Error("T23 不等于序列首流开始时间")
    if np.count_nonzero(coverage) != SOURCE_ROW_COUNT:
        raise ProtocolARaw83Error("Protocol A I/M 未完整覆盖 LSPR23 流")
    unique_entities = np.unique(E)
    if unique_entities.size != SOURCE_ENTITY_COUNT:
        raise ProtocolARaw83Error("E23 实体数不匹配")
    random_state = np.random.RandomState(RANDOM_SEED)
    permutation = random_state.permutation(unique_entities.size)
    validation_entity_count = max(
        1,
        int(unique_entities.size * float(config["protocol_a"]["validation_entity_fraction"])),
    )
    validation_entities = unique_entities[permutation[:validation_entity_count]]
    entity_mask = np.isin(E, validation_entities)
    time_cut = np.quantile(T, 1.0 - float(config["protocol_a"]["time_tail_fraction"]))
    time_mask = T >= time_cut
    train_rows = np.flatnonzero(~(entity_mask | time_mask)).astype("<i8", copy=False)
    validation_rows = np.flatnonzero(entity_mask & ~time_mask).astype("<i8", copy=False)
    if train_rows.size != TRAIN_SEQUENCE_COUNT or validation_rows.size != VALIDATION_SEQUENCE_COUNT:
        raise ProtocolARaw83Error(
            f"切分计数不匹配：{train_rows.size}/{validation_rows.size}"
        )
    if np.intersect1d(train_rows, validation_rows).size:
        raise ProtocolARaw83Error("训练与验证序列交叠")
    training_flow_bitmap = np.zeros(SOURCE_ROW_COUNT, dtype=np.uint8)
    for start in range(0, train_rows.size, 8_192):
        rows = train_rows[start : start + 8_192]
        indices = np.asarray(I[rows])
        masks = np.asarray(M[rows], dtype=bool)
        training_flow_bitmap[indices[masks]] = 1
    split_root = output_root / "split"
    _save_npy_atomic(split_root / "train_rows.npy", train_rows, run_id)
    _save_npy_atomic(split_root / "validation_rows.npy", validation_rows, run_id)
    _save_npy_atomic(split_root / "training-valid-flow-bitmap.npy", training_flow_bitmap, run_id)
    for name in ("I23", "M23", "E23", "T23"):
        destination = split_root / f"{name}.npy"
        source = cache_root / f"{name}.npy"
        if destination.exists():
            if sha256_file(destination) != identities[name]["sha256"]:
                raise ProtocolARaw83Error(f"已存在的 {name} 副本哈希不匹配")
        else:
            temporary = destination.with_name(f"{destination.name}.partial.{run_id}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, temporary)
            if sha256_file(temporary) != identities[name]["sha256"]:
                raise ProtocolARaw83Error(f"{name} 复制后哈希不匹配")
            os.replace(temporary, destination)
    artifacts = {
        "train_rows": _artifact(split_root / "train_rows.npy"),
        "validation_rows": _artifact(split_root / "validation_rows.npy"),
        "training_valid_flow_bitmap": _artifact(
            split_root / "training-valid-flow-bitmap.npy"
        ),
    }
    artifacts.update({name: _artifact(split_root / f"{name}.npy") for name in arrays})
    split_identity = {
        "algorithm": "verbatim-select-signal-entity-and-time-exclusion-v1",
        "seed": RANDOM_SEED,
        "validation_entity_fraction": float(
            config["protocol_a"]["validation_entity_fraction"]
        ),
        "time_tail_fraction": float(config["protocol_a"]["time_tail_fraction"]),
        "entity_count": int(unique_entities.size),
        "train_sequences": int(train_rows.size),
        "validation_sequences": int(validation_rows.size),
        "training_valid_flows": int(np.count_nonzero(training_flow_bitmap)),
        "time_cut": float(time_cut),
        "artifacts": artifacts,
    }
    split_identity["sequence_split_state_hash"] = canonical_sha256(split_identity)
    atomic_write_json(output_root / "receipts" / "p2-protocol-a-binding.json", split_identity)
    return split_identity


def validate_source_qualification_seal(
    seal_path: Path,
    *,
    expected_input_arm_sha256: str,
) -> dict[str, Any]:
    """Target 任何路径打开前的唯一外部资格门。"""

    if not seal_path.is_file() or seal_path.is_symlink():
        raise ProtocolARaw83Error("目标年需要独立源资格封印")
    seal = load_json(seal_path)
    required = {
        "schema_version",
        "seal_sha256",
        "source_input_arm_sha256",
        "recipe_sha256",
        "capacity_sha256",
        "checkpoint_sha256",
        "mechanism_sha256",
        "evaluation_code_sha256",
        "target_feature_rows_read",
        "target_label_rows_read",
    }
    if required - set(seal):
        raise ProtocolARaw83Error("源资格封印缺少必需键")
    unsigned = {key: value for key, value in seal.items() if key != "seal_sha256"}
    if seal["seal_sha256"] != canonical_sha256(unsigned):
        raise ProtocolARaw83Error("源资格封印内容哈希无效")
    if seal["target_feature_rows_read"] != 0 or seal["target_label_rows_read"] != 0:
        raise ProtocolARaw83Error("源资格封印已接触目标年")
    hash_keys = (
        "source_input_arm_sha256",
        "recipe_sha256",
        "capacity_sha256",
        "checkpoint_sha256",
        "mechanism_sha256",
        "evaluation_code_sha256",
    )
    if not isinstance(expected_input_arm_sha256, str) or len(expected_input_arm_sha256) != 64:
        raise ProtocolARaw83Error("当前源产品尚未封印唯一输入臂")
    if any(
        not isinstance(seal[key], str)
        or len(seal[key]) != 64
        or any(character not in "0123456789abcdef" for character in seal[key])
        for key in hash_keys
    ):
        raise ProtocolARaw83Error("源资格封印含非法 SHA-256 字段")
    if seal["source_input_arm_sha256"] != expected_input_arm_sha256:
        raise ProtocolARaw83Error("源资格封印与输入臂封印不匹配")
    return seal


def open_lspr24_parquet_after_seal(
    parquet_path: Path,
    *,
    source_qualification_seal: Path,
    expected_input_arm_sha256: str,
) -> Any:
    """P6 专用：先验封印，后创建 ParquetFile 句柄。"""

    validate_source_qualification_seal(
        source_qualification_seal,
        expected_input_arm_sha256=expected_input_arm_sha256,
    )
    import pyarrow.parquet as pq

    return pq.ParquetFile(parquet_path)


class ProtocolADataset:
    def __init__(
        self,
        manifest_path: Path,
        *,
        year: Literal["LSPR23", "LSPR24"],
        purpose: Literal["fit", "train", "validate", "target-evaluate"],
        arm: Literal["A", "B"] | None,
        source_qualification_seal: Path | None,
    ) -> None:
        if manifest_path.name != "dataset-manifest.json":
            raise ProtocolARaw83Error("只接受 dataset-manifest.json 作为发现入口")
        self.manifest_path = manifest_path.resolve(strict=True)
        self.manifest = load_json(self.manifest_path)
        if self.manifest.get("schema_version") != SCHEMA_VERSION:
            raise ProtocolARaw83Error("数据清单模式不匹配")
        if purpose not in PURPOSES:
            raise ProtocolARaw83Error(f"未知用途：{purpose}")
        if year == TARGET_YEAR:
            if purpose != "target-evaluate" or source_qualification_seal is None:
                raise ProtocolARaw83Error("目标年只允许封印后描述性评价")
            validate_source_qualification_seal(
                source_qualification_seal,
                expected_input_arm_sha256=self.manifest.get("source_input_arm_sha256"),
            )
        elif year != SOURCE_YEAR or purpose == "target-evaluate":
            raise ProtocolARaw83Error("年度与用途组合非法")
        if purpose in {"train", "validate", "target-evaluate"} and arm not in {"A", "B"}:
            raise ProtocolARaw83Error("视图消费者必须显式指定 A 或 B 臂")
        if purpose == "fit" and arm is not None:
            raise ProtocolARaw83Error("fit 只读 Raw83，不接受视图臂")
        self.year = year
        self.purpose = purpose
        self.arm = arm
        self.root = self.manifest_path.parent.resolve(strict=True)
        self._verify_manifest_artifacts()

    def _artifact_path(self, key: str) -> Path:
        item = self.manifest["artifacts"].get(key)
        if not isinstance(item, dict):
            raise ProtocolARaw83Error(f"清单缺少制品：{key}")
        path = Path(item["path"])
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not resolved.is_relative_to(self.root):
            raise ProtocolARaw83Error(f"制品路径越界或为符号链接：{key}")
        if resolved.stat().st_size != int(item["bytes"]) or sha256_file(resolved) != item["sha256"]:
            raise ProtocolARaw83Error(f"制品字节数或 SHA-256 不匹配：{key}")
        return resolved

    def _verify_manifest_artifacts(self) -> None:
        if self.manifest.get("field_list_sha256") != FIELD_LIST_SHA256:
            raise ProtocolARaw83Error("清单字段 SHA-256 不匹配")
        if self.manifest.get("schema_sha256") != SCHEMA_SHA256:
            raise ProtocolARaw83Error("清单模式 SHA-256 不匹配")
        names = {Path(item["path"]).name for item in self.manifest["artifacts"].values()}
        forbidden = names & FORBIDDEN_ARTIFACT_NAMES
        if forbidden:
            raise ProtocolARaw83Error(f"清单含禁止制品：{sorted(forbidden)}")

    def _allowed_sequence_rows(self) -> np.ndarray:
        if self.purpose == "train":
            return np.load(self._artifact_path("train_rows"), mmap_mode="r", allow_pickle=False)
        if self.purpose == "validate":
            return np.load(
                self._artifact_path("validation_rows"), mmap_mode="r", allow_pickle=False
            )
        raise ProtocolARaw83Error(f"{self.purpose} 不允许请求序列行")

    def gather_sequences(
        self,
        sequence_rows: Sequence[int] | np.ndarray,
        *,
        columns: Literal["all83"] = "all83",
    ) -> dict[str, np.ndarray]:
        if columns != "all83":
            raise ProtocolARaw83Error("序列加载只允许 all83")
        requested = np.asarray(sequence_rows, dtype=np.int64)
        allowed = self._allowed_sequence_rows()
        if requested.ndim != 1 or np.setdiff1d(requested, allowed).size:
            raise ProtocolARaw83Error("序列行越出当前 purpose 的能力集")
        I = np.load(self._artifact_path("I23"), mmap_mode="r", allow_pickle=False)
        M = np.load(self._artifact_path("M23"), mmap_mode="r", allow_pickle=False)
        view = np.load(
            self._artifact_path(f"source_view_{str(self.arm).lower()}"),
            mmap_mode="r",
            allow_pickle=False,
        )
        indices = np.asarray(I[requested])
        mask = np.asarray(M[requested], dtype=bool)
        return {
            "features": np.asarray(view[indices]),
            "valid_mask": mask,
            "raw_row_indices": indices,
        }

    def gather_raw_fields(
        self,
        raw_row_indices: Sequence[int] | np.ndarray,
        field_names: Sequence[str],
    ) -> np.ndarray:
        requested = np.asarray(raw_row_indices, dtype=np.int64)
        if self.purpose != "fit":
            raise ProtocolARaw83Error("只有 fit 可读 Raw83 字段")
        bitmap = np.load(
            self._artifact_path("training_valid_flow_bitmap"),
            mmap_mode="r",
            allow_pickle=False,
        )
        if requested.ndim != 1 or np.any(requested < 0) or np.any(requested >= bitmap.size):
            raise ProtocolARaw83Error("Raw83 行号越界")
        if np.any(bitmap[requested] != 1):
            raise ProtocolARaw83Error("fit 试图读取非训练有效流")
        unknown = sorted(set(field_names) - set(DIJK_FEATURES))
        if unknown:
            raise ProtocolARaw83Error(f"请求了未授权字段：{unknown}")
        columns = [DIJK_FEATURES.index(name) for name in field_names]
        raw = np.load(self._artifact_path("source_raw83"), mmap_mode="r", allow_pickle=False)
        return np.asarray(raw[np.ix_(requested, columns)])

    def iter_feature_batches(self, *, batch_rows: int) -> Iterator[np.ndarray]:
        if batch_rows <= 0:
            raise ProtocolARaw83Error("batch_rows 必须为正整数")
        if self.purpose == "fit":
            values = np.load(
                self._artifact_path("source_raw83"), mmap_mode="r", allow_pickle=False
            )
            bitmap = np.load(
                self._artifact_path("training_valid_flow_bitmap"),
                mmap_mode="r",
                allow_pickle=False,
            )
            indices = np.flatnonzero(bitmap)
        else:
            values = np.load(
                self._artifact_path(f"source_view_{str(self.arm).lower()}"),
                mmap_mode="r",
                allow_pickle=False,
            )
            rows = self._allowed_sequence_rows()
            I = np.load(self._artifact_path("I23"), mmap_mode="r", allow_pickle=False)
            M = np.load(self._artifact_path("M23"), mmap_mode="r", allow_pickle=False)
            indices = np.asarray(I[rows])[np.asarray(M[rows], dtype=bool)]
        for start in range(0, indices.size, batch_rows):
            yield np.asarray(values[indices[start : start + batch_rows]])

    def open_label_resolver(self, stage_token: str) -> "StreamingLabelResolver":
        if self.purpose not in {"train", "validate", "target-evaluate"}:
            raise ProtocolARaw83Error("fit 没有标签能力")
        expected_token = self.manifest["label_stage_tokens"].get(self.purpose)
        if not expected_token or not hashlib.sha256(stage_token.encode()).hexdigest() == expected_token:
            raise ProtocolARaw83Error("标签阶段令牌无效")
        if self.year != SOURCE_YEAR:
            raise ProtocolARaw83Error("目标年标签解析器未在源产品中实现")
        rows = self._allowed_sequence_rows()
        sequence_indices = np.load(
            self._artifact_path("I23"), mmap_mode="r", allow_pickle=False
        )
        sequence_masks = np.load(
            self._artifact_path("M23"), mmap_mode="r", allow_pickle=False
        )
        allowed_bitmap = np.zeros(SOURCE_ROW_COUNT, dtype=np.uint8)
        allowed_bitmap[np.asarray(sequence_indices[rows])[np.asarray(sequence_masks[rows], dtype=bool)]] = 1
        return StreamingLabelResolver(
            zip_path=Path(self.manifest["source"]["zip_path"]),
            inner_csv=self.manifest["source"]["inner_csv"],
            expected_content_sha256=self.manifest["source"]["label_content_sha256"],
            block_size=int(self.manifest["runtime"]["arrow_block_size"]),
            allowed_bitmap=allowed_bitmap,
        )

    def receipt(self) -> dict[str, Any]:
        return {
            "schema_version": f"{SCHEMA_VERSION}-consumer-receipt-v1",
            "manifest_sha256": sha256_file(self.manifest_path),
            "year": self.year,
            "purpose": self.purpose,
            "arm": self.arm,
            "field_list_sha256": self.manifest["field_list_sha256"],
            "raw_content_sha256": self.manifest["raw_content_sha256"],
            "sequence_split_state_hash": self.manifest["sequence_split_state_hash"],
            "transform_state_hash": (
                None if self.arm is None else self.manifest["transform_state_hashes"][self.arm]
            ),
        }


class StreamingLabelResolver:
    def __init__(
        self,
        *,
        zip_path: Path,
        inner_csv: str,
        expected_content_sha256: str,
        block_size: int,
        allowed_bitmap: np.ndarray,
    ) -> None:
        self.zip_path = zip_path
        self.inner_csv = inner_csv
        self.expected_content_sha256 = expected_content_sha256
        self.block_size = block_size
        self.allowed_bitmap = allowed_bitmap

    def resolve(self, raw_row_indices: Sequence[int] | np.ndarray) -> np.ndarray:
        import pyarrow as pa
        import pyarrow.csv as pacsv

        requested = np.asarray(raw_row_indices, dtype=np.int64)
        if requested.ndim != 1 or np.any(requested < 0):
            raise ProtocolARaw83Error("标签行号非法")
        if np.any(requested >= self.allowed_bitmap.size) or np.any(
            self.allowed_bitmap[requested] != 1
        ):
            raise ProtocolARaw83Error("标签行越出当前 purpose 能力集")
        order = np.argsort(requested, kind="stable")
        sorted_rows = requested[order]
        values = np.empty(requested.size, dtype=np.uint8)
        digest = hashlib.sha256()
        row_offset = 0
        cursor = 0
        with zipfile.ZipFile(self.zip_path) as archive:
            with archive.open(self.inner_csv, "r") as source:
                reader = pacsv.open_csv(
                    source,
                    read_options=pacsv.ReadOptions(use_threads=False, block_size=self.block_size),
                    convert_options=pacsv.ConvertOptions(
                        include_columns=[LABEL_COLUMN],
                        column_types={LABEL_COLUMN: pa.string()},
                        strings_can_be_null=False,
                    ),
                )
                for batch in reader:
                    labels = _parse_binary_labels(batch.column(LABEL_COLUMN).to_pylist())
                    digest.update(labels.tobytes(order="C"))
                    stop = row_offset + labels.size
                    while cursor < sorted_rows.size and sorted_rows[cursor] < stop:
                        if sorted_rows[cursor] < row_offset:
                            raise ProtocolARaw83Error("标签行号非单调解析")
                        values[order[cursor]] = labels[sorted_rows[cursor] - row_offset]
                        cursor += 1
                    row_offset = stop
        if digest.hexdigest() != self.expected_content_sha256:
            raise ProtocolARaw83Error("运行内标签内容 SHA-256 不匹配")
        if cursor != sorted_rows.size:
            raise ProtocolARaw83Error("标签行号越出源数据")
        return values


def open_protocol_a_dataset(
    manifest_path: str | Path,
    year: Literal["LSPR23", "LSPR24"],
    purpose: Literal["fit", "train", "validate", "target-evaluate"],
    arm: Literal["A", "B"] | None = None,
    source_qualification_seal: str | Path | None = None,
) -> ProtocolADataset:
    seal_path = None if source_qualification_seal is None else Path(source_qualification_seal)
    return ProtocolADataset(
        Path(manifest_path),
        year=year,
        purpose=purpose,
        arm=arm,
        source_qualification_seal=seal_path,
    )


def publish_dataset_manifest(
    config: Mapping[str, Any],
    *,
    p1_receipt: Mapping[str, Any],
    p2_receipt: Mapping[str, Any],
    preprocessing_receipt: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> dict[str, Any]:
    output_root = Path(config["paths"]["output_root"]).resolve(strict=True)
    artifacts: dict[str, Any] = {
        "source_raw83": p1_receipt["artifacts"]["raw83"],
        "source_flow_entity_id": p1_receipt["artifacts"]["flow_entity_id"],
        "source_start_time_ns": p1_receipt["artifacts"]["start_time_ns"],
        "source_entity_summaries": p1_receipt["artifacts"]["entity_summaries"],
    }
    artifacts.update(p2_receipt["artifacts"])
    artifacts.update(preprocessing_receipt["artifacts"])
    for key, item in artifacts.items():
        path = Path(item["path"])
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not resolved.is_relative_to(output_root):
            raise ProtocolARaw83Error(f"清单制品越界：{key}")
        if _artifact(resolved) != item:
            raise ProtocolARaw83Error(f"清单发布前制品哈希变化：{key}")
    names = {Path(item["path"]).name for item in artifacts.values()}
    if names & FORBIDDEN_ARTIFACT_NAMES:
        raise ProtocolARaw83Error("发布清单含禁止制品")
    forbidden_on_disk = sorted(
        str(path)
        for path in output_root.rglob("*")
        if path.is_file() and path.name in FORBIDDEN_ARTIFACT_NAMES
    )
    if forbidden_on_disk:
        raise ProtocolARaw83Error(f"数据根存在禁止制品：{forbidden_on_disk}")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": config["run_id"],
        "display_name": config["display_name"],
        "field_list": list(DIJK_FEATURES),
        "field_list_sha256": FIELD_LIST_SHA256,
        "schema": schema_contract(),
        "schema_sha256": SCHEMA_SHA256,
        "finite_negative_policy": FINITE_NEGATIVE_POLICY,
        "source": {
            "year": SOURCE_YEAR,
            "zip_path": str(Path(config["source"]["zip_path"]).resolve(strict=True)),
            "inner_csv": config["source"]["inner_csv"],
            "source_sha256": p1_receipt["source_sha256"],
            "label_content_sha256": p1_receipt["label_content_sha256"],
            "label_aggregate": p1_receipt["label_aggregate"],
            "label_rows_persisted": 0,
        },
        "raw_content_sha256": p1_receipt["raw_content_sha256"],
        "sequence_split_state_hash": p2_receipt["sequence_split_state_hash"],
        "transform_state_hashes": preprocessing_receipt["transform_state_hashes"],
        "view_content_sha256": preprocessing_receipt["view_content_sha256"],
        "target_feature_rows_read": 0,
        "target_label_rows_read": 0,
        "source_input_arm_sha256": None,
        "label_stage_tokens": config["protocol_a"]["label_stage_token_sha256"],
        "runtime": dict(runtime),
        "artifacts": artifacts,
    }
    manifest["manifest_content_sha256"] = canonical_sha256(manifest)
    manifest_path = Path(config["paths"]["dataset_manifest"])
    atomic_write_json(manifest_path, manifest)
    if sha256_file(manifest_path) == "":
        raise ProtocolARaw83Error("清单文件 SHA-256 不得为空")
    return manifest
