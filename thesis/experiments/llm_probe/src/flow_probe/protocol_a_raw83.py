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
TARGET_CONFIG_SCHEMA_VERSION = "ch3-protocol-a-raw83-target-v1"
YEAR_CONFIG_SCHEMA_VERSION = TARGET_CONFIG_SCHEMA_VERSION
TARGET_MANIFEST_SCHEMA_VERSION = "ch3-protocol-a-raw83-year-product-v1"
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
_FILE_SHA256_CACHE: dict[tuple[str, int, int, int, int, int], str] = {}
_PROCESS_LABEL_CACHE: dict[tuple[str, str, int, int], np.ndarray] = {}


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
    stat = path.stat()
    identity = (
        str(path.resolve(strict=True)),
        stat.st_dev,
        stat.st_ino,
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
    )
    cached = _FILE_SHA256_CACHE.get(identity)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk_bytes):
            digest.update(block)
    value = digest.hexdigest()
    _FILE_SHA256_CACHE[identity] = value
    return value


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
    frozen = config["protocol_a"].get("frozen_identity")
    required_hash_keys = {
        "I23_sha256",
        "M23_sha256",
        "E23_sha256",
        "T23_sha256",
        "train_rows_sha256",
        "validation_rows_sha256",
        "validation_entities_sha256",
        "train_entities_sha256",
        "training_flow_bitmap_sha256",
        "validation_flow_bitmap_sha256",
    }
    if not isinstance(frozen, dict) or required_hash_keys - set(frozen):
        raise ProtocolARaw83Error("Protocol A 冻结 SHA 合同不完整")
    for key in required_hash_keys:
        value = frozen[key]
        if not isinstance(value, str) or len(value) != 64 or any(
            character not in "0123456789abcdef" for character in value
        ):
            raise ProtocolARaw83Error(f"Protocol A 冻结 SHA 非法：{key}")
    frozen_scalars = {
        "legacy_array_hash_scope": "npy-file-bytes-sha256-v1",
        "derived_int64_hash_scope": "little-endian-int64-c-contiguous-raw-bytes-v1",
        "bitmap_content_hash_scope": "uint8-length-16353511-raw-bytes-v1",
        "train_rows_count": TRAIN_SEQUENCE_COUNT,
        "validation_rows_count": VALIDATION_SEQUENCE_COUNT,
        "validation_entities_count": 15_068,
        "training_flow_bitmap_count": 11_991_315,
        "validation_flow_bitmap_count": 1_238_500,
        "time_cut": 1_678_365_316_588_433.5,
    }
    for key, value in frozen_scalars.items():
        if frozen.get(key) != value:
            raise ProtocolARaw83Error(f"Protocol A 冻结标量不匹配：{key}")
    paths = config["paths"]
    if not Path(paths["output_root"]).is_absolute():
        raise ProtocolARaw83Error("输出根必须为绝对路径")
    if Path(paths["dataset_manifest"]).name != "dataset-manifest.json":
        raise ProtocolARaw83Error("唯一发现入口必须名为 dataset-manifest.json")


def source_generation_roots(config: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    run_root = Path(config["paths"]["output_root"])
    generations_root = run_root / "generations"
    final_root = generations_root / "source-v1"
    partial_root = generations_root / f"source-v1.partial.{config['run_id']}"
    if final_root.exists() and partial_root.exists():
        raise ProtocolARaw83Error("源产品同时存在 sealed 与 partial 世代")
    return run_root, partial_root, final_root


def source_data_root(config: Mapping[str, Any], *, create: bool = True) -> Path:
    _, partial_root, final_root = source_generation_roots(config)
    root = final_root if final_root.exists() else partial_root
    if create:
        root.mkdir(parents=True, exist_ok=True)
    return root


def validate_target_config(config: Mapping[str, Any]) -> None:
    required = {
        "schema_version",
        "run_id",
        "display_name",
        "qualification_status",
        "winning_arm",
        "dependencies",
        "source_product",
        "year_product",
        "paths",
        "resources",
    }
    if required - set(config) or config["schema_version"] != TARGET_CONFIG_SCHEMA_VERSION:
        raise ProtocolARaw83Error("封印后年度产品配置不完整")
    product = config["year_product"]
    if product["expected_bytes"] != 2_775_972_952:
        raise ProtocolARaw83Error("年度 Parquet 字节数不匹配")
    expected = {
        "expected_sha256": "1d96f0a023de583397cc300143ba98b84b9e9bd2270f0b8b61346ca19963057a",
        "expected_rows": 20_227_356,
        "expected_row_groups": 21,
        "expected_field_count": 101,
        "expected_schema_sha256": "540be446500aa3a9dd1268115ff9fd8d0328b40694fc65247746aa4c0e2143c1",
    }
    for key, value in expected.items():
        if product[key] != value:
            raise ProtocolARaw83Error(f"年度产品冻结值不匹配：{key}")
    arrays = product["sequence_arrays"]
    if arrays["I24_sha256"] != "420993e83512adb5878470d5e95a77e1cc5548b20c281eb7d44468a37b23c37d":
        raise ProtocolARaw83Error("年度 I 数组 SHA-256 不匹配")
    if arrays["M24_sha256"] != "1300a42273c8fdd386b0d5569a3c5023d2bcde3f6534c1e20d3570c31cd1ff6c":
        raise ProtocolARaw83Error("年度 M 数组 SHA-256 不匹配")
    status = config["qualification_status"]
    winner = config["winning_arm"]
    seal_sha = config["source_product"]["qualification_seal_sha256"]
    if status == "blocked-until-source-arm-seal":
        if winner is not None or seal_sha is not None:
            raise ProtocolARaw83Error("阻断态不得预设胜出臂或封印 SHA")
    elif status == "qualified-source-arm-sealed":
        if winner not in {"A", "B"} or not isinstance(seal_sha, str) or len(seal_sha) != 64:
            raise ProtocolARaw83Error("可运行状态必须冻结胜出臂和封印 SHA")
    else:
        raise ProtocolARaw83Error("未知年度资格状态")


def target_generation_roots(config: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    run_root = Path(config["paths"]["output_root"])
    generations_root = run_root / "generations"
    final_root = generations_root / "year-v1"
    partial_root = generations_root / f"year-v1.partial.{config['run_id']}"
    if final_root.exists() and partial_root.exists():
        raise ProtocolARaw83Error("年度产品同时存在 sealed 与 partial 世代")
    return run_root, partial_root, final_root


validate_year_config = validate_target_config


def array_content_sha256(values: np.ndarray, dtype: str) -> str:
    canonical = np.asarray(values, dtype=np.dtype(dtype), order="C")
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


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
    float32_overflow_counts: np.ndarray


def _arrow_to_float64(column: Any) -> np.ndarray:
    return np.asarray(column.to_numpy(zero_copy_only=False), dtype=np.float64)


def _arrow_to_int64(column: Any) -> np.ndarray:
    return np.asarray(column.to_numpy(zero_copy_only=False), dtype=np.int64)


def _batch_column(batch: Any, name: str) -> Any:
    index = batch.schema.get_field_index(name)
    if index < 0:
        raise ProtocolARaw83Error(f"Arrow 批缺少字段：{name}")
    return batch.column(index)


def _canonicalize_raw83(
    values: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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
    structural_invalid = finite & ~valid
    with np.errstate(over="ignore", invalid="ignore"):
        normalized = np.asarray(values, dtype="<f4", order="C")
    float32_overflow = valid & ~np.isfinite(normalized)
    valid &= ~float32_overflow
    normalized[~valid] = np.array(np.nan, dtype="<f4")
    return (
        normalized,
        np.count_nonzero(~finite, axis=0).astype("<i8"),
        np.count_nonzero(structural_invalid, axis=0).astype("<i8"),
        np.count_nonzero(float32_overflow, axis=0).astype("<i8"),
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
                    values[:, feature_index] = _arrow_to_float64(_batch_column(batch, name))
                (
                    raw83,
                    nonfinite_counts,
                    structural_invalid_counts,
                    float32_overflow_counts,
                ) = _canonicalize_raw83(values)
                del values
                src_ip = tuple(str(value) for value in _batch_column(batch, IP_COLUMNS[0]).to_pylist())
                dst_ip = tuple(str(value) for value in _batch_column(batch, IP_COLUMNS[1]).to_pylist())
                start_time = _arrow_to_int64(_batch_column(batch, TIME_START_COLUMN))
                labels = _parse_binary_labels(_batch_column(batch, LABEL_COLUMN).to_pylist())
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
                    float32_overflow_counts=float32_overflow_counts,
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
        self.float32_overflow = np.zeros(width, dtype=np.int64)
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
        float32_overflow_counts: np.ndarray,
    ) -> None:
        count = raw83.shape[0]
        self.total += count
        self.nonfinite += nonfinite_counts
        self.structural_invalid += structural_invalid_counts
        self.float32_overflow += float32_overflow_counts
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
                    "float32_overflow": int(self.float32_overflow[index]),
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
    run_root = Path(config["paths"]["output_root"])
    output_root = source_data_root(config)
    run_id = str(config["run_id"])
    expected_rows = int(config["source"]["expected_rows"])
    raw_final = output_root / "raw" / "lspr23-raw83.npy"
    entity_final = output_root / "sidecars" / "lspr23-flow-entity-id.npy"
    time_final = output_root / "sidecars" / "lspr23-start-time-ns.npy"
    raw_partial = raw_final.with_name(f"{raw_final.name}.partial.{run_id}")
    entity_partial = entity_final.with_name(f"{entity_final.name}.partial.{run_id}")
    time_partial = time_final.with_name(f"{time_final.name}.partial.{run_id}")
    receipts_root = run_root / "receipts" / "p1-batches"
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
    process_labels = np.empty(expected_rows, dtype=np.int8)
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
            float32_overflow_counts=batch.float32_overflow_counts,
        )
        raw_digest.update(batch.raw83.tobytes(order="C"))
        entity_bytes = ids.tobytes(order="C")
        time_bytes = np.asarray(batch.start_time_ns, dtype="<i8").tobytes(order="C")
        entity_digest_full.update(entity_bytes)
        time_digest.update(time_bytes)
        label_bytes = batch.labels.tobytes(order="C")
        label_digest.update(label_bytes)
        label_counts += np.bincount(batch.labels, minlength=2)
        process_labels[batch.start_row : batch.end_row] = batch.labels
        cumulative_statistics_sha256 = canonical_sha256(feature_stats.receipt())
        receipt_path = receipts_root / f"batch-{batch.batch_index:06d}.json"
        if receipt_path.exists():
            receipt = load_json(receipt_path)
            written_digest = hashlib.sha256()
            written_digest.update(
                np.asarray(raw[batch.start_row : batch.end_row], dtype="<f4").tobytes(order="C")
            )
            written_digest.update(
                np.asarray(
                    entities[batch.start_row : batch.end_row], dtype="<u4"
                ).tobytes(order="C")
            )
            written_digest.update(
                np.asarray(times[batch.start_row : batch.end_row], dtype="<i8").tobytes(order="C")
            )
            expected = {
                "start_row": batch.start_row,
                "end_row": batch.end_row,
                "content_sha256": batch_sha,
                "label_sha256": _label_batch_sha(batch.labels),
                "cumulative_statistics_sha256": cumulative_statistics_sha256,
                "cumulative_raw_content_sha256": raw_digest.hexdigest(),
                "cumulative_label_content_sha256": label_digest.hexdigest(),
                "written_slice_sha256": written_digest.hexdigest(),
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
                    "written_slice_sha256": batch_sha,
                },
            )
        observed_rows = batch.end_row
    if observed_rows != expected_rows:
        raise ProtocolARaw83Error(f"LSPR23 行数不匹配：{observed_rows} != {expected_rows}")
    if len(entity_summaries) != SOURCE_ENTITY_COUNT:
        raise ProtocolARaw83Error(
            f"LSPR23 实体数不匹配：{len(entity_summaries)} != {SOURCE_ENTITY_COUNT}"
        )
    source_stat = source_path.stat()
    label_cache_key = (
        str(source_path.resolve(strict=True)),
        label_digest.hexdigest(),
        source_stat.st_size,
        source_stat.st_mtime_ns,
    )
    process_labels.setflags(write=False)
    _PROCESS_LABEL_CACHE[label_cache_key] = process_labels
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
    atomic_write_json(run_root / "receipts" / "p1-source-raw83.json", receipt)
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
    run_root = Path(config["paths"]["output_root"])
    output_root = source_data_root(config)
    cache_root = Path(config["paths"]["legacy_protocol_a_cache"])
    run_id = str(config["run_id"])
    frozen = config["protocol_a"]["frozen_identity"]
    arrays: dict[str, np.ndarray] = {}
    identities: dict[str, Any] = {}
    for name in ("I23", "M23", "E23", "T23"):
        path = cache_root / f"{name}.npy"
        if not path.is_file() or path.is_symlink():
            raise ProtocolARaw83Error(f"Protocol A 原数组缺失或为符号链接：{path}")
        arrays[name] = np.load(path, mmap_mode="r", allow_pickle=False)
        identities[name] = _artifact(path)
        if identities[name]["sha256"] != frozen[f"{name}_sha256"]:
            raise ProtocolARaw83Error(f"{name} 文件 SHA-256 与冻结值不匹配")
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
    cumulative_valid_positions = 0
    e_to_sidecar: dict[int, int] = {}
    sidecar_to_e: dict[int, int] = {}
    for start in range(0, SOURCE_SEQUENCE_COUNT, 8_192):
        stop = min(start + 8_192, SOURCE_SEQUENCE_COUNT)
        batch_i = np.asarray(I[start:stop])
        batch_m = np.asarray(M[start:stop], dtype=bool)
        if np.any(batch_i[batch_m] < 0) or np.any(batch_i[batch_m] >= SOURCE_ROW_COUNT):
            raise ProtocolARaw83Error("I23 有效位置存在越界行号")
        flat = batch_i[batch_m]
        unique_flat = np.unique(flat)
        if unique_flat.size != flat.size:
            raise ProtocolARaw83Error("Protocol A 单批有效行号存在重复")
        if np.any(coverage[flat] != 0):
            raise ProtocolARaw83Error("Protocol A 序列中存在重复流覆盖")
        coverage[flat] = 1
        cumulative_valid_positions += int(flat.size)
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
    if cumulative_valid_positions != SOURCE_ROW_COUNT or np.count_nonzero(coverage) != SOURCE_ROW_COUNT:
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
    validation_flow_bitmap = np.zeros(SOURCE_ROW_COUNT, dtype=np.uint8)
    for start in range(0, train_rows.size, 8_192):
        rows = train_rows[start : start + 8_192]
        indices = np.asarray(I[rows])
        masks = np.asarray(M[rows], dtype=bool)
        training_flow_bitmap[indices[masks]] = 1
    for start in range(0, validation_rows.size, 8_192):
        rows = validation_rows[start : start + 8_192]
        indices = np.asarray(I[rows])
        masks = np.asarray(M[rows], dtype=bool)
        validation_flow_bitmap[indices[masks]] = 1
    train_entities = np.unique(E[train_rows]).astype("<i8", copy=False)
    validation_entities = np.sort(validation_entities).astype("<i8", copy=False)
    if np.intersect1d(train_entities, validation_entities).size:
        raise ProtocolARaw83Error("训练与验证实体成员交叠")
    if np.any((training_flow_bitmap == 1) & (validation_flow_bitmap == 1)):
        raise ProtocolARaw83Error("训练与验证流位图交叠")
    expected_derived = {
        "train_rows": (
            train_rows,
            int(frozen["train_rows_count"]),
            frozen["train_rows_sha256"],
            "<i8",
        ),
        "validation_rows": (
            validation_rows,
            int(frozen["validation_rows_count"]),
            frozen["validation_rows_sha256"],
            "<i8",
        ),
        "validation_entities": (
            validation_entities,
            int(frozen["validation_entities_count"]),
            frozen["validation_entities_sha256"],
            "<i8",
        ),
        "train_entities": (
            train_entities,
            train_entities.size,
            frozen["train_entities_sha256"],
            "<i8",
        ),
        "training_flow_bitmap": (
            training_flow_bitmap,
            int(frozen["training_flow_bitmap_count"]),
            frozen["training_flow_bitmap_sha256"],
            "u1",
        ),
        "validation_flow_bitmap": (
            validation_flow_bitmap,
            int(frozen["validation_flow_bitmap_count"]),
            frozen["validation_flow_bitmap_sha256"],
            "u1",
        ),
    }
    derived_hashes: dict[str, str] = {}
    for key, (values, expected_count, expected_sha, dtype) in expected_derived.items():
        observed_count = int(np.count_nonzero(values)) if dtype == "u1" else int(values.size)
        observed_sha = array_content_sha256(values, dtype)
        if observed_count != expected_count or observed_sha != expected_sha:
            raise ProtocolARaw83Error(
                f"{key} 冻结身份不匹配：{observed_count}/{observed_sha}"
            )
        derived_hashes[key] = observed_sha
    if float(time_cut) != float(frozen["time_cut"]):
        raise ProtocolARaw83Error("Protocol A 时间切点与冻结值不匹配")
    split_root = output_root / "split"
    _save_npy_atomic(split_root / "train_rows.npy", train_rows, run_id)
    _save_npy_atomic(split_root / "validation_rows.npy", validation_rows, run_id)
    _save_npy_atomic(split_root / "validation_entities.npy", validation_entities, run_id)
    _save_npy_atomic(split_root / "train_entities.npy", train_entities, run_id)
    _save_npy_atomic(split_root / "training-valid-flow-bitmap.npy", training_flow_bitmap, run_id)
    _save_npy_atomic(
        split_root / "validation-flow-bitmap.npy", validation_flow_bitmap, run_id
    )
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
        "validation_entities": _artifact(split_root / "validation_entities.npy"),
        "train_entities": _artifact(split_root / "train_entities.npy"),
        "training_valid_flow_bitmap": _artifact(
            split_root / "training-valid-flow-bitmap.npy"
        ),
        "validation_flow_bitmap": _artifact(split_root / "validation-flow-bitmap.npy"),
    }
    artifacts.update({name: _artifact(split_root / f"{name}.npy") for name in arrays})
    p1_receipt = load_json(run_root / "receipts" / "p1-source-raw83.json")
    labels = load_source_labels_once(
        Path(config["source"]["zip_path"]),
        inner_csv=config["source"]["inner_csv"],
        expected_content_sha256=p1_receipt["label_content_sha256"],
        block_size=int(config["resources"]["maximum_arrow_block_bytes"]),
    )
    train_flow_indices = np.flatnonzero(training_flow_bitmap)
    train_flow_labels = labels[train_flow_indices]
    train_flow_positive = int(np.count_nonzero(train_flow_labels))
    train_flow_negative = int(train_flow_labels.size - train_flow_positive)
    train_sequence_positive = 0
    train_sequence_valid_flows = 0
    for start in range(0, train_rows.size, 8_192):
        rows = train_rows[start : start + 8_192]
        indices = np.asarray(I[rows])
        masks = np.asarray(M[rows], dtype=bool)
        sequence_labels = np.max(labels[indices] * masks, axis=1)
        train_sequence_positive += int(np.count_nonzero(sequence_labels))
        train_sequence_valid_flows += int(np.count_nonzero(masks))
    train_sequence_negative = int(train_rows.size - train_sequence_positive)
    if train_sequence_valid_flows != int(np.count_nonzero(training_flow_bitmap)):
        raise ProtocolARaw83Error("训练序列有效位聚合与流位图不一致")
    weight_aggregate = {
        "label_content_sha256": p1_receipt["label_content_sha256"],
        "persisted_label_rows": 0,
        "train_flow_count": int(train_flow_labels.size),
        "train_flow_positive": train_flow_positive,
        "train_flow_negative": train_flow_negative,
        "train_flow_positive_weight": (
            None if train_flow_positive == 0 else train_flow_negative / train_flow_positive
        ),
        "train_sequence_count": int(train_rows.size),
        "train_sequence_valid_flow_positions": train_sequence_valid_flows,
        "train_sequence_positive": train_sequence_positive,
        "train_sequence_negative": train_sequence_negative,
        "train_sequence_positive_weight": (
            None
            if train_sequence_positive == 0
            else train_sequence_negative / train_sequence_positive
        ),
    }
    hash_payload = {
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
        "legacy_file_sha256": {name: identities[name]["sha256"] for name in arrays},
        "derived_content_sha256": derived_hashes,
        "weight_aggregate": weight_aggregate,
    }
    split_identity = {
        **hash_payload,
        "sequence_split_state_hash": canonical_sha256(hash_payload),
        "artifacts": artifacts,
    }
    atomic_write_json(run_root / "receipts" / "p2-protocol-a-binding.json", split_identity)
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


def _arrow_schema_identity(schema: Any) -> dict[str, Any]:
    return {
        "schema_version": "arrow-field-list-v1",
        "fields": [
            {"name": field.name, "type": str(field.type), "nullable": bool(field.nullable)}
            for field in schema
        ],
    }


def materialize_qualified_year_product(
    config: Mapping[str, Any],
    *,
    batch_rows: int,
) -> dict[str, Any]:
    """完整源资格封印后物化单一胜出臂的年度产品。"""

    validate_target_config(config)
    if config["qualification_status"] != "qualified-source-arm-sealed":
        raise ProtocolARaw83Error("源输入臂尚未合法选择，年度产品硬阻断")
    winner = config["winning_arm"]
    source_product = config["source_product"]
    seal_path = Path(source_product["qualification_seal"])
    if sha256_file(seal_path) != source_product["qualification_seal_sha256"]:
        raise ProtocolARaw83Error("源资格封印文件 SHA-256 不匹配")
    source_manifest_path = Path(source_product["dataset_manifest"])
    source_dataset = ProtocolADataset(
        source_manifest_path,
        year=SOURCE_YEAR,
        purpose="fit",
        arm=None,
        source_qualification_seal=None,
    )
    seal_preview = load_json(seal_path)
    source_arm_sha = seal_preview.get("source_input_arm_sha256")
    seal = validate_source_qualification_seal(
        seal_path,
        expected_input_arm_sha256=source_arm_sha,
    )
    if seal.get("winning_arm") != winner:
        raise ProtocolARaw83Error("目标配置胜出臂与源资格封印不匹配")
    product = config["year_product"]
    parquet_path = Path(product["parquet_path"])
    if parquet_path.stat().st_size != product["expected_bytes"]:
        raise ProtocolARaw83Error("年度 Parquet 字节数不匹配")
    if sha256_file(parquet_path) != product["expected_sha256"]:
        raise ProtocolARaw83Error("年度 Parquet SHA-256 不匹配")
    parquet_file = open_lspr24_parquet_after_seal(
        parquet_path,
        source_qualification_seal=seal_path,
        expected_input_arm_sha256=source_arm_sha,
    )
    if (
        parquet_file.metadata.num_rows != product["expected_rows"]
        or parquet_file.metadata.num_row_groups != product["expected_row_groups"]
        or len(parquet_file.schema_arrow) != product["expected_field_count"]
    ):
        raise ProtocolARaw83Error("年度 Parquet 行、行组或字段数不匹配")
    schema_identity = _arrow_schema_identity(parquet_file.schema_arrow)
    if canonical_sha256(schema_identity) != product["expected_schema_sha256"]:
        raise ProtocolARaw83Error("年度 Parquet 物理模式 SHA-256 不匹配")
    required_columns = list(DIJK_FEATURES) + [*IP_COLUMNS, TIME_START_COLUMN, LABEL_COLUMN]
    if not set(required_columns).issubset(parquet_file.schema_arrow.names):
        raise ProtocolARaw83Error("年度 Parquet 缺少合法投影字段")
    run_root, partial_root, final_root = target_generation_roots(config)
    if final_root.exists():
        raise ProtocolARaw83Error("同名年度产品已封印")
    partial_root.mkdir(parents=True, exist_ok=True)
    row_count = int(product["expected_rows"])
    run_id = str(config["run_id"])
    raw_path = partial_root / "raw" / "year-raw83.npy"
    entity_path = partial_root / "sidecars" / "year-flow-entity-id.npy"
    time_path = partial_root / "sidecars" / "year-start-time-ns.npy"
    view_path = partial_root / "views" / f"year-winning-arm-{str(winner).lower()}.npy"
    raw = _open_partial_npy(raw_path, dtype="<f4", shape=(row_count, len(DIJK_FEATURES)))
    flow_entity = _open_partial_npy(entity_path, dtype="<u4", shape=(row_count,))
    start_time = _open_partial_npy(time_path, dtype="<i8", shape=(row_count,))
    view = _open_partial_npy(view_path, dtype="<f4", shape=(row_count, len(DIJK_FEATURES)))
    from flow_probe.protocol_a_preprocessing import (
        _restore_quantile_transformer,
        _transform_a,
        _transform_b,
    )

    a_state_path = source_dataset._artifact_path("candidate_a_state")
    b_state_path = source_dataset._artifact_path("candidate_b_state")
    transformer = None if winner == "A" else _restore_quantile_transformer(b_state_path)
    clip = (-10.0, 10.0)
    entity_ids: dict[bytes, int] = {}
    entity_summaries: list[str] = []
    label_digest = hashlib.sha256()
    label_counts = np.zeros(2, dtype=np.int64)
    receipts_root = run_root / "receipts" / "p6-batches"
    receipts_root.mkdir(parents=True, exist_ok=True)
    offset = 0
    batch_index = 0
    for row_group in range(parquet_file.metadata.num_row_groups):
        for batch in parquet_file.iter_batches(
            batch_size=batch_rows,
            row_groups=[row_group],
            columns=required_columns,
            use_threads=False,
        ):
            count = batch.num_rows
            stop = offset + count
            values = np.empty((count, len(DIJK_FEATURES)), dtype=np.float64)
            for feature_index, name in enumerate(DIJK_FEATURES):
                values[:, feature_index] = _arrow_to_float64(_batch_column(batch, name))
            raw_batch, _, _, _ = _canonicalize_raw83(values)
            del values
            src_values = tuple(str(value) for value in _batch_column(batch, IP_COLUMNS[0]).to_pylist())
            dst_values = tuple(str(value) for value in _batch_column(batch, IP_COLUMNS[1]).to_pylist())
            ids = np.empty(count, dtype="<u4")
            for local_index, (src_ip, dst_ip) in enumerate(zip(src_values, dst_values)):
                digest = entity_digest(src_ip, dst_ip)
                entity_id = entity_ids.get(digest)
                if entity_id is None:
                    entity_id = len(entity_summaries)
                    entity_ids[digest] = entity_id
                    entity_summaries.append(digest.hex())
                ids[local_index] = entity_id
            time_values = _arrow_to_int64(_batch_column(batch, TIME_START_COLUMN))
            labels = _parse_binary_labels(_batch_column(batch, LABEL_COLUMN).to_pylist())
            a_batch = _transform_a(raw_batch, a_state_path, clip)
            winning_batch = (
                a_batch
                if winner == "A"
                else _transform_b(raw_batch, a_batch, b_state_path, transformer)
            )
            content_digest = hashlib.sha256()
            for payload in (raw_batch, ids, time_values, winning_batch):
                content_digest.update(np.asarray(payload).tobytes(order="C"))
            content_sha = content_digest.hexdigest()
            receipt_path = receipts_root / f"batch-{batch_index:06d}.json"
            if receipt_path.exists():
                receipt = load_json(receipt_path)
                written_digest = hashlib.sha256()
                for payload in (
                    raw[offset:stop],
                    flow_entity[offset:stop],
                    start_time[offset:stop],
                    view[offset:stop],
                ):
                    written_digest.update(np.asarray(payload).tobytes(order="C"))
                if (
                    receipt.get("row_group") != row_group
                    or receipt.get("start_row") != offset
                    or receipt.get("end_row") != stop
                    or receipt.get("content_sha256") != content_sha
                    or receipt.get("written_slice_sha256") != written_digest.hexdigest()
                ):
                    raise ProtocolARaw83Error("年度产品批断点不匹配")
            else:
                raw[offset:stop] = raw_batch
                flow_entity[offset:stop] = ids
                start_time[offset:stop] = time_values
                view[offset:stop] = winning_batch
                raw.flush(); flow_entity.flush(); start_time.flush(); view.flush()
                atomic_write_json(
                    receipt_path,
                    {
                        "schema_version": f"{TARGET_MANIFEST_SCHEMA_VERSION}-batch-receipt-v1",
                        "batch_index": batch_index,
                        "row_group": row_group,
                        "start_row": offset,
                        "end_row": stop,
                        "content_sha256": content_sha,
                        "written_slice_sha256": content_sha,
                    },
                )
            label_digest.update(labels.tobytes(order="C"))
            label_counts += np.bincount(labels, minlength=2)
            offset = stop
            batch_index += 1
    if offset != row_count:
        raise ProtocolARaw83Error("年度产品行数不匹配")
    del raw, flow_entity, start_time, view
    entity_summary_path = partial_root / "sidecars" / "year-entity-summaries.json"
    atomic_write_json(
        entity_summary_path,
        {
            "schema_version": f"{TARGET_MANIFEST_SCHEMA_VERSION}-entity-summaries-v1",
            "entity_count": len(entity_summaries),
            "summaries_sha256": canonical_sha256(entity_summaries),
            "summaries": entity_summaries,
        },
    )
    arrays = product["sequence_arrays"]
    sequence_artifacts: dict[str, Any] = {}
    loaded_sequences: dict[str, np.ndarray] = {}
    for name in ("I24", "M24"):
        source = Path(arrays[f"{name}_path"])
        if sha256_file(source) != arrays[f"{name}_sha256"]:
            raise ProtocolARaw83Error(f"年度 {name} SHA-256 不匹配")
        destination = partial_root / "sequences" / f"{name}.npy"
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f"{destination.name}.partial.{run_id}")
        shutil.copyfile(source, temporary)
        if sha256_file(temporary) != arrays[f"{name}_sha256"]:
            raise ProtocolARaw83Error(f"年度 {name} 复制 SHA-256 不匹配")
        os.replace(temporary, destination)
        loaded_sequences[name] = np.load(destination, mmap_mode="r", allow_pickle=False)
        sequence_artifacts[name] = _artifact(destination)
    I = loaded_sequences["I24"]
    M = loaded_sequences["M24"]
    if I.shape != M.shape or I.ndim != 2 or I.shape[1] != SEQUENCE_LENGTH:
        raise ProtocolARaw83Error("年度 I/M 序列形状非法")
    entity_values = np.load(entity_path, mmap_mode="r", allow_pickle=False)
    time_values = np.load(time_path, mmap_mode="r", allow_pickle=False)
    sequence_entities = np.empty(I.shape[0], dtype="<u4")
    sequence_times = np.empty(I.shape[0], dtype="<i8")
    coverage = np.zeros(row_count, dtype=np.uint8)
    cumulative = 0
    for start in range(0, I.shape[0], 8_192):
        stop = min(start + 8_192, I.shape[0])
        batch_i = np.asarray(I[start:stop])
        batch_m = np.asarray(M[start:stop], dtype=bool)
        flat = batch_i[batch_m]
        if np.unique(flat).size != flat.size or np.any(coverage[flat] != 0):
            raise ProtocolARaw83Error("年度序列流覆盖重复")
        coverage[flat] = 1
        cumulative += int(flat.size)
        for local in range(stop - start):
            indices = batch_i[local, batch_m[local]]
            unique_entities = np.unique(entity_values[indices])
            if indices.size == 0 or unique_entities.size != 1:
                raise ProtocolARaw83Error("年度序列实体不唯一")
            sequence_entities[start + local] = unique_entities[0]
            sequence_times[start + local] = time_values[indices[0]]
    if cumulative != row_count or np.count_nonzero(coverage) != row_count:
        raise ProtocolARaw83Error("年度序列未恰好覆盖全部流")
    sequence_entity_path = partial_root / "sequences" / "sequence-entity-id.npy"
    sequence_time_path = partial_root / "sequences" / "sequence-start-time-ns.npy"
    _save_npy_atomic(sequence_entity_path, sequence_entities, run_id)
    _save_npy_atomic(sequence_time_path, sequence_times, run_id)
    artifacts = {
        "raw83": _artifact(raw_path),
        "winning_view": _artifact(view_path),
        "flow_entity_id": _artifact(entity_path),
        "start_time_ns": _artifact(time_path),
        "entity_summaries": _artifact(entity_summary_path),
        **sequence_artifacts,
        "sequence_entity_id": _artifact(sequence_entity_path),
        "sequence_start_time_ns": _artifact(sequence_time_path),
    }
    published = {
        key: {
            **item,
            "path": str(final_root / Path(item["path"]).resolve(strict=True).relative_to(partial_root)),
        }
        for key, item in artifacts.items()
    }
    manifest = {
        "schema_version": TARGET_MANIFEST_SCHEMA_VERSION,
        "run_id": config["run_id"],
        "year": product["year"],
        "winning_arm": winner,
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "source_qualification_seal_sha256": sha256_file(seal_path),
        "source_input_arm_sha256": source_arm_sha,
        "parquet_sha256": product["expected_sha256"],
        "parquet_path": str(parquet_path.resolve(strict=True)),
        "parquet_schema_sha256": product["expected_schema_sha256"],
        "row_count": row_count,
        "label_content_sha256": label_digest.hexdigest(),
        "label_aggregate": {"negative": int(label_counts[0]), "positive": int(label_counts[1])},
        "persisted_label_rows": 0,
        "label_stage_token_sha256": product["label_stage_token_sha256"],
        "artifacts": published,
    }
    manifest["manifest_content_sha256"] = canonical_sha256(manifest)
    manifest_path = partial_root / "dataset-manifest.json"
    atomic_write_json(manifest_path, manifest)
    expected_files = {"dataset-manifest.json"} | {
        str(Path(item["path"]).resolve(strict=True).relative_to(partial_root))
        for item in artifacts.values()
    }
    observed_files = {
        str(path.resolve(strict=True).relative_to(partial_root))
        for path in partial_root.rglob("*")
        if path.is_file()
    }
    if observed_files != expected_files:
        raise ProtocolARaw83Error("年度世代不等于严格制品允许列表")
    os.replace(partial_root, final_root)
    pointer = {
        "schema_version": f"{TARGET_MANIFEST_SCHEMA_VERSION}-current-pointer-v1",
        "generation": "year-v1",
        "manifest_path": str((final_root / "dataset-manifest.json").resolve(strict=True)),
        "manifest_sha256": sha256_file(final_root / "dataset-manifest.json"),
    }
    pointer["pointer_content_sha256"] = canonical_sha256(pointer)
    atomic_write_json(run_root / "current-year.json", pointer)
    return {
        "schema_version": f"{TARGET_MANIFEST_SCHEMA_VERSION}-p6-receipt-v1",
        "manifest_path": pointer["manifest_path"],
        "manifest_sha256": pointer["manifest_sha256"],
        "row_count": row_count,
        "winning_arm": winner,
        "persisted_label_rows": 0,
    }


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
        manifest_hash = self.manifest.get("manifest_content_sha256")
        unsigned_manifest = {
            key: value
            for key, value in self.manifest.items()
            if key != "manifest_content_sha256"
        }
        if manifest_hash != canonical_sha256(unsigned_manifest):
            raise ProtocolARaw83Error("数据清单内容 SHA-256 不匹配")
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
        expected_files = {"dataset-manifest.json"}
        for key in sorted(self.manifest["artifacts"]):
            expected_files.add(str(self._artifact_path(key).relative_to(self.root)))
        observed_files = {
            str(path.resolve(strict=True).relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file()
        }
        if observed_files != expected_files:
            raise ProtocolARaw83Error(
                f"数据世代不等于清单严格制品集："
                f"extra={sorted(observed_files - expected_files)} "
                f"missing={sorted(expected_files - observed_files)}"
            )

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
        requested = np.asarray(raw_row_indices, dtype=np.int64)
        if requested.ndim != 1 or np.any(requested < 0):
            raise ProtocolARaw83Error("标签行号非法")
        if np.any(requested >= self.allowed_bitmap.size) or np.any(
            self.allowed_bitmap[requested] != 1
        ):
            raise ProtocolARaw83Error("标签行越出当前 purpose 能力集")
        labels = load_source_labels_once(
            self.zip_path,
            inner_csv=self.inner_csv,
            expected_content_sha256=self.expected_content_sha256,
            block_size=self.block_size,
        )
        return np.asarray(labels[requested], dtype=np.uint8)


def load_source_labels_once(
    zip_path: Path,
    *,
    inner_csv: str,
    expected_content_sha256: str,
    block_size: int,
) -> np.ndarray:
    """同一进程最多顺序重放一次源 CSV 标签列。"""

    import pyarrow as pa
    import pyarrow.csv as pacsv

    stat = zip_path.stat()
    key = (str(zip_path.resolve(strict=True)), expected_content_sha256, stat.st_size, stat.st_mtime_ns)
    cached = _PROCESS_LABEL_CACHE.get(key)
    if cached is not None:
        return cached
    labels = np.empty(SOURCE_ROW_COUNT, dtype=np.int8)
    digest = hashlib.sha256()
    row_offset = 0
    with zipfile.ZipFile(zip_path) as archive:
        with archive.open(inner_csv, "r") as source:
            reader = pacsv.open_csv(
                source,
                read_options=pacsv.ReadOptions(use_threads=False, block_size=block_size),
                convert_options=pacsv.ConvertOptions(
                    include_columns=[LABEL_COLUMN],
                    column_types={LABEL_COLUMN: pa.string()},
                    strings_can_be_null=False,
                ),
            )
            for batch in reader:
                parsed = _parse_binary_labels(_batch_column(batch, LABEL_COLUMN).to_pylist())
                stop = row_offset + parsed.size
                if stop > SOURCE_ROW_COUNT:
                    raise ProtocolARaw83Error("源标签行数超出冻结上界")
                labels[row_offset:stop] = parsed
                digest.update(parsed.tobytes(order="C"))
                row_offset = stop
    if row_offset != SOURCE_ROW_COUNT:
        raise ProtocolARaw83Error("源标签行数不匹配")
    if digest.hexdigest() != expected_content_sha256:
        raise ProtocolARaw83Error("运行内标签内容 SHA-256 不匹配")
    labels.setflags(write=False)
    _PROCESS_LABEL_CACHE[key] = labels
    return labels


def load_parquet_labels_once(
    parquet_path: Path,
    *,
    expected_file_sha256: str,
    expected_content_sha256: str,
) -> np.ndarray:
    import pyarrow.parquet as pq

    stat = parquet_path.stat()
    key = (
        str(parquet_path.resolve(strict=True)),
        expected_content_sha256,
        stat.st_size,
        stat.st_mtime_ns,
    )
    cached = _PROCESS_LABEL_CACHE.get(key)
    if cached is not None:
        return cached
    if sha256_file(parquet_path) != expected_file_sha256:
        raise ProtocolARaw83Error("年度标签解析源 SHA-256 不匹配")
    parquet_file = pq.ParquetFile(parquet_path)
    labels = np.empty(parquet_file.metadata.num_rows, dtype=np.int8)
    digest = hashlib.sha256()
    offset = 0
    for batch in parquet_file.iter_batches(columns=[LABEL_COLUMN], use_threads=False):
        parsed = _parse_binary_labels(_batch_column(batch, LABEL_COLUMN).to_pylist())
        stop = offset + parsed.size
        labels[offset:stop] = parsed
        digest.update(parsed.tobytes(order="C"))
        offset = stop
    if offset != labels.size or digest.hexdigest() != expected_content_sha256:
        raise ProtocolARaw83Error("年度标签内容 SHA-256 不匹配")
    labels.setflags(write=False)
    _PROCESS_LABEL_CACHE[key] = labels
    return labels


class TargetProtocolADataset:
    """封印后年度产品的只读序列与运行内标签能力。"""

    def __init__(self, manifest_path: Path, seal_path: Path) -> None:
        self.manifest_path = manifest_path.resolve(strict=True)
        self.manifest = load_json(self.manifest_path)
        if self.manifest.get("schema_version") != TARGET_MANIFEST_SCHEMA_VERSION:
            raise ProtocolARaw83Error("年度产品清单模式不匹配")
        unsigned = {
            key: value
            for key, value in self.manifest.items()
            if key != "manifest_content_sha256"
        }
        if self.manifest.get("manifest_content_sha256") != canonical_sha256(unsigned):
            raise ProtocolARaw83Error("年度产品清单内容 SHA-256 不匹配")
        if sha256_file(seal_path) != self.manifest["source_qualification_seal_sha256"]:
            raise ProtocolARaw83Error("年度产品的源资格封印不匹配")
        validate_source_qualification_seal(
            seal_path,
            expected_input_arm_sha256=self.manifest["source_input_arm_sha256"],
        )
        self.root = self.manifest_path.parent
        expected_files = {"dataset-manifest.json"}
        self.artifact_paths: dict[str, Path] = {}
        for key, item in self.manifest["artifacts"].items():
            path = Path(item["path"])
            resolved = path.resolve(strict=True)
            if path.is_symlink() or not resolved.is_relative_to(self.root):
                raise ProtocolARaw83Error(f"年度制品路径越界：{key}")
            if resolved.stat().st_size != item["bytes"] or sha256_file(resolved) != item["sha256"]:
                raise ProtocolARaw83Error(f"年度制品身份不匹配：{key}")
            self.artifact_paths[key] = resolved
            expected_files.add(str(resolved.relative_to(self.root)))
        observed_files = {
            str(path.resolve(strict=True).relative_to(self.root))
            for path in self.root.rglob("*")
            if path.is_file()
        }
        if observed_files != expected_files:
            raise ProtocolARaw83Error("年度世代不等于清单严格制品集")

    def gather_sequences(self, sequence_rows: Sequence[int] | np.ndarray) -> dict[str, np.ndarray]:
        rows = np.asarray(sequence_rows, dtype=np.int64)
        I = np.load(self.artifact_paths["I24"], mmap_mode="r", allow_pickle=False)
        M = np.load(self.artifact_paths["M24"], mmap_mode="r", allow_pickle=False)
        if rows.ndim != 1 or np.any(rows < 0) or np.any(rows >= I.shape[0]):
            raise ProtocolARaw83Error("年度序列行越界")
        indices = np.asarray(I[rows])
        mask = np.asarray(M[rows], dtype=bool)
        view = np.load(self.artifact_paths["winning_view"], mmap_mode="r", allow_pickle=False)
        return {
            "features": np.asarray(view[indices]),
            "valid_mask": mask,
            "raw_row_indices": indices,
        }

    def open_label_resolver(self, stage_token: str) -> "TargetLabelResolver":
        if hashlib.sha256(stage_token.encode()).hexdigest() != self.manifest[
            "label_stage_token_sha256"
        ]:
            raise ProtocolARaw83Error("年度标签阶段令牌无效")
        return TargetLabelResolver(self.manifest)


class TargetLabelResolver:
    def __init__(self, manifest: Mapping[str, Any]) -> None:
        self.manifest = manifest

    def resolve(self, raw_row_indices: Sequence[int] | np.ndarray) -> np.ndarray:
        requested = np.asarray(raw_row_indices, dtype=np.int64)
        if (
            requested.ndim != 1
            or np.any(requested < 0)
            or np.any(requested >= int(self.manifest["row_count"]))
        ):
            raise ProtocolARaw83Error("年度标签行号越界")
        labels = load_parquet_labels_once(
            Path(self.manifest["parquet_path"]),
            expected_file_sha256=self.manifest["parquet_sha256"],
            expected_content_sha256=self.manifest["label_content_sha256"],
        )
        return np.asarray(labels[requested], dtype=np.uint8)


YearProtocolADataset = TargetProtocolADataset


def open_protocol_a_dataset(
    manifest_path: str | Path,
    year: Literal["LSPR23", "LSPR24"],
    purpose: Literal["fit", "train", "validate", "target-evaluate"],
    arm: Literal["A", "B"] | None = None,
    source_qualification_seal: str | Path | None = None,
) -> ProtocolADataset | TargetProtocolADataset:
    seal_path = None if source_qualification_seal is None else Path(source_qualification_seal)
    manifest = load_json(Path(manifest_path))
    if manifest.get("schema_version") == TARGET_MANIFEST_SCHEMA_VERSION:
        if purpose != "target-evaluate" or seal_path is None:
            raise ProtocolARaw83Error("年度产品只允许封印后评价")
        return TargetProtocolADataset(Path(manifest_path), seal_path)
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
    run_root, work_root, final_root = source_generation_roots(config)
    output_root = source_data_root(config).resolve(strict=True)
    if output_root != work_root.resolve(strict=True):
        raise ProtocolARaw83Error("源清单只能在未发布世代内生成")
    artifacts: dict[str, Any] = {
        "source_raw83": p1_receipt["artifacts"]["raw83"],
        "source_flow_entity_id": p1_receipt["artifacts"]["flow_entity_id"],
        "source_start_time_ns": p1_receipt["artifacts"]["start_time_ns"],
        "source_entity_summaries": p1_receipt["artifacts"]["entity_summaries"],
    }
    artifacts.update(p2_receipt["artifacts"])
    artifacts.update(preprocessing_receipt["artifacts"])
    published_artifacts: dict[str, Any] = {}
    for key, item in artifacts.items():
        path = Path(item["path"])
        resolved = path.resolve(strict=True)
        if path.is_symlink() or not resolved.is_relative_to(output_root):
            raise ProtocolARaw83Error(f"清单制品越界：{key}")
        if _artifact(resolved) != item:
            raise ProtocolARaw83Error(f"清单发布前制品哈希变化：{key}")
        relative = resolved.relative_to(output_root)
        published_artifacts[key] = {
            **item,
            "path": str((final_root / relative).resolve(strict=False)),
        }
    allowed_relative_files = {
        str(Path(item["path"]).resolve(strict=True).relative_to(output_root))
        for item in artifacts.values()
    }
    observed_relative_files = {
        str(path.resolve(strict=True).relative_to(output_root))
        for path in output_root.rglob("*")
        if path.is_file()
    }
    observed_relative_files.discard("dataset-manifest.json")
    if observed_relative_files != allowed_relative_files:
        raise ProtocolARaw83Error(
            f"源世代制品不等于严格允许列表："
            f"extra={sorted(observed_relative_files - allowed_relative_files)} "
            f"missing={sorted(allowed_relative_files - observed_relative_files)}"
        )
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
        "source_input_arm_sha256": None,
        "label_stage_tokens": config["protocol_a"]["label_stage_token_sha256"],
        "runtime": dict(runtime),
        "artifacts": published_artifacts,
    }
    manifest["manifest_content_sha256"] = canonical_sha256(manifest)
    manifest_path = output_root / "dataset-manifest.json"
    atomic_write_json(manifest_path, manifest)
    if sha256_file(manifest_path) == "":
        raise ProtocolARaw83Error("清单文件 SHA-256 不得为空")
    return manifest
