#!/usr/bin/env python3
"""封印后 CUDA-RWKV 四格在 LSPR24 上的只读描述性评价（零训练、零物化）。

本入口不训练、不改阈值、不改模型、不碰源年封印，也不写任何数据制品：
它读取冻结的 LSPR24 Parquet 与 `runs/diagnostics/dijk-repro/cache/` 中已被
目标物化配置登记哈希的 `I24.npy` / `M24.npy`，在内存中按冻结的候选 B 变换
重建 arm-B 视图与序列侧车，然后复用 `flow_probe.cuda_rwkv_evaluation` 的
聚合与整数假阳曲线实现给出实体级指标。

为什么不能只读缓存里的 `X24.npy`：实测该数组不是 Dijk 83 字段原值，而是
dijk 复现管线自己标准化后的特征矩阵（见 `verify` 动作的披露项），把它送进
按 raw83→候选 B 拟合的模型会得到模型从未见过的输入分布。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping, Sequence


os.environ.setdefault("OMP_NUM_THREADS", "1")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
TOOLS_ROOT = PROJECT_ROOT / "tools"
for candidate in (SRC_ROOT, TOOLS_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

SCHEMA_VERSION = "ch3-cuda-rwkv-lspr24-inmemory-descriptive-eval-v1"
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / f"{SCHEMA_VERSION}.json"

T0 = time.time()
_LAST_BEAT = [T0]


def log(message: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {message}", flush=True)


def beat(stage: str, done: int, total: int, started: float, every: float = 30.0) -> None:
    now = time.time()
    if now - _LAST_BEAT[0] < every and done < total:
        return
    _LAST_BEAT[0] = now
    elapsed = now - started
    rate = done / max(elapsed, 1e-9)
    remaining = (total - done) / max(rate, 1e-9)
    log(
        f"[{stage}] {done:,}/{total:,} ({done / max(total, 1):.1%}) "
        f"吞吐 {rate:,.0f}/s 累计 {elapsed:.0f}s 预计剩余 {remaining:.0f}s"
    )


def sha256_file(path: Path, *, chunk_bytes: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def _source_artifacts(config: Mapping[str, Any]) -> dict[str, Any]:
    manifest = load_json(Path(config["source_product"]["dataset_manifest"]))
    return manifest["artifacts"]


def _transform_state_paths(config: Mapping[str, Any]) -> tuple[Path, Path]:
    artifacts = _source_artifacts(config)
    a_state = Path(artifacts["candidate_a_state"]["path"])
    b_state = Path(artifacts["candidate_b_state"]["path"])
    for path, key in ((a_state, "candidate_a_state"), (b_state, "candidate_b_state")):
        if sha256_file(path) != artifacts[key]["sha256"]:
            raise SystemExit(f"冻结变换状态 SHA-256 不符：{key}")
    return a_state, b_state


# --------------------------------------------------------------------------
# 数据身份核验：只读比对，不写入任何冻结目录
# --------------------------------------------------------------------------


def verify_data_identity(config: Mapping[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pyarrow.parquet as pq

    from flow_probe.protocol_a_raw83 import _arrow_schema_identity

    cache_root = Path(config["cache"]["root"])
    contract = config["contract"]
    target_config = load_json(Path(config["target_materialization_config"]))
    source_manifest_path = Path(config["source_product"]["dataset_manifest"])
    source_manifest = load_json(source_manifest_path)
    artifacts = source_manifest["artifacts"]
    checks: list[dict[str, Any]] = []

    def record(
        name: str, observed: Any, expected: Any, note: str, *, blocking: bool
    ) -> None:
        checks.append(
            {
                "check": name,
                "observed": observed,
                "expected": expected,
                "passed": observed == expected,
                "blocking": blocking,
                "note": note,
            }
        )

    log("核验：LSPR24 序列数组对目标物化配置的冻结哈希")
    product = target_config["year_product"]
    sequence_arrays = product["sequence_arrays"]
    for name in ("I24", "M24"):
        declared = Path(sequence_arrays[f"{name}_path"])
        local = cache_root / f"{name}.npy"
        if declared.resolve() != local.resolve():
            raise SystemExit(f"{name} 缓存路径与目标物化配置声明不一致：{declared}")
        record(
            f"frozen_{name}_sha256",
            sha256_file(local),
            str(sequence_arrays[f"{name}_sha256"]),
            "目标年物化配置直接把该缓存文件登记为冻结序列数组",
            blocking=True,
        )

    log("核验：LSPR24 Parquet 的字节数、摘要、行数、行组、字段与物理模式")
    parquet_path = Path(product["parquet_path"])
    record(
        "frozen_parquet_bytes",
        int(parquet_path.stat().st_size),
        int(product["expected_bytes"]),
        "冻结年度 Parquet 字节数",
        blocking=True,
    )
    record(
        "frozen_parquet_sha256",
        sha256_file(parquet_path),
        str(product["expected_sha256"]),
        "冻结年度 Parquet 内容摘要",
        blocking=True,
    )
    parquet_file = pq.ParquetFile(parquet_path)
    record(
        "frozen_parquet_rows",
        int(parquet_file.metadata.num_rows),
        int(product["expected_rows"]),
        "冻结年度 Parquet 行数",
        blocking=True,
    )
    record(
        "frozen_parquet_row_groups",
        int(parquet_file.metadata.num_row_groups),
        int(product["expected_row_groups"]),
        "冻结年度 Parquet 行组数",
        blocking=True,
    )
    record(
        "frozen_parquet_field_count",
        int(len(parquet_file.schema_arrow)),
        int(product["expected_field_count"]),
        "冻结年度 Parquet 字段数",
        blocking=True,
    )
    record(
        "frozen_parquet_schema_sha256",
        canonical_sha256(_arrow_schema_identity(parquet_file.schema_arrow)),
        str(product["expected_schema_sha256"]),
        "冻结年度 Parquet 物理模式摘要",
        blocking=True,
    )

    log("核验：源年冻结 raw83 与两份变换状态")
    for key in ("source_raw83", "candidate_a_state", "candidate_b_state", "source_view_b"):
        record(
            f"source_{key}_sha256",
            sha256_file(Path(artifacts[key]["path"])),
            str(artifacts[key]["sha256"]),
            f"源年冻结制品 {key} 的内容摘要",
            blocking=True,
        )

    log("披露：dijk-repro 缓存 X 数组与协议A raw83 的关系")
    cache_x23 = sha256_file(cache_root / "X23.npy")
    record(
        "cache_X23_is_protocol_a_raw83",
        cache_x23,
        str(artifacts["source_raw83"]["sha256"]),
        (
            "实测不相等：缓存 X23/X24 是 dijk 复现管线自己标准化后的特征矩阵，"
            "不是 Dijk 83 字段原值，故本入口从冻结 Parquet 读原值"
        ),
        blocking=False,
    )
    record(
        "cache_I23_matches_source_product",
        sha256_file(cache_root / "I23.npy"),
        str(artifacts["I23"]["sha256"]),
        "缓存序列索引与源年冻结制品一致，说明两条管线的流行序相同",
        blocking=False,
    )

    log("核验：LSPR24 缓存形状")
    shapes: dict[str, list[int]] = {}
    for name, expected_shape in (
        ("I24", (int(contract["n_sequence"]), int(contract["sequence_width"]))),
        ("M24", (int(contract["n_sequence"]), int(contract["sequence_width"]))),
        ("y24", (int(contract["n_flow"]),)),
        ("t24", (int(contract["n_flow"]),)),
    ):
        values = np.load(cache_root / f"{name}.npy", mmap_mode="r", allow_pickle=False)
        shapes[name] = list(values.shape)
        if tuple(values.shape) != expected_shape:
            raise SystemExit(f"{name} 形状不符：{values.shape} != {expected_shape}")

    receipt = {
        "schema_version": f"{SCHEMA_VERSION}-data-verification-v1",
        "cache_root": str(cache_root),
        "parquet_path": str(parquet_path),
        "source_manifest_path": str(source_manifest_path),
        "source_manifest_file_sha256": sha256_file(source_manifest_path),
        "target_materialization_config_sha256": sha256_file(
            Path(config["target_materialization_config"])
        ),
        "checks": checks,
        "blocking_passed": all(item["passed"] for item in checks if item["blocking"]),
        "disclosures": [
            {"check": item["check"], "passed": item["passed"], "note": item["note"]}
            for item in checks
            if not item["blocking"]
        ],
        "observed_shapes": shapes,
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    for item in checks:
        state = "通过" if item["passed"] else "不通过"
        level = "阻断项" if item["blocking"] else "披露项"
        log(f"  {item['check']}（{level}）: {state}")
    return receipt


# --------------------------------------------------------------------------
# 冻结候选 B 视图在内存中的重建
# --------------------------------------------------------------------------


def build_arm_b_view_from_raw(
    raw_path: Path,
    *,
    config: Mapping[str, Any],
    row_count: int,
    stage: str,
) -> "Any":
    """从已冻结的 raw83 数组按候选 B 变换重建视图，只驻内存。"""

    import numpy as np

    from flow_probe.protocol_a_preprocessing import (
        _restore_quantile_transformer,
        _transform_a,
        _transform_b,
    )

    a_state, b_state = _transform_state_paths(config)
    transformer = _restore_quantile_transformer(b_state)
    clip = tuple(float(value) for value in config["contract"]["transform_clip"])
    raw = np.load(raw_path, mmap_mode="r", allow_pickle=False)
    if raw.shape != (row_count, int(config["contract"]["raw_feature"])):
        raise SystemExit(f"{Path(raw_path).name} 形状不符：{raw.shape}")
    view = np.empty(raw.shape, dtype="<f4")
    batch_rows = int(config["evaluation"]["transform_batch_rows"])
    started = time.time()
    for start in range(0, row_count, batch_rows):
        stop = min(start + batch_rows, row_count)
        raw_batch = np.asarray(raw[start:stop])
        a_batch = _transform_a(raw_batch, a_state, clip)
        view[start:stop] = _transform_b(raw_batch, a_batch, b_state, transformer)
        beat(stage, stop, row_count, started)
    return view


def compare_view_with_source_product(
    view: "Any", config: Mapping[str, Any]
) -> dict[str, Any]:
    """把重建的 LSPR23 视图与源年已封印候选 B 视图逐字节比对。"""

    import numpy as np

    artifact = _source_artifacts(config)["source_view_b"]
    published = np.load(Path(artifact["path"]), mmap_mode="r", allow_pickle=False)
    if published.shape != view.shape:
        raise SystemExit(f"源年候选 B 视图形状不符：{published.shape}")
    block = 1_048_576
    mismatched = 0
    started = time.time()
    for start in range(0, view.shape[0], block):
        stop = min(start + block, view.shape[0])
        chunk = np.asarray(published[start:stop])
        mismatched += int(np.count_nonzero(chunk != view[start:stop]))
        beat("LSPR23/视图逐字节比对", stop, view.shape[0], started)
    return {
        "published_view_path": str(artifact["path"]),
        "published_view_sha256": artifact["sha256"],
        "mismatched_cells": mismatched,
        "passed": mismatched == 0,
    }


# --------------------------------------------------------------------------
# 目标年：直读冻结 Parquet，在内存内重建视图、实体、开始时刻与标签
# --------------------------------------------------------------------------


def read_target_year(config: Mapping[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pyarrow.parquet as pq

    from dijk2026_replication.dijk_fields import DIJK_FEATURES
    from flow_probe.protocol_a_preprocessing import (
        _restore_quantile_transformer,
        _transform_a,
        _transform_b,
    )
    from flow_probe.protocol_a_raw83 import (
        IP_COLUMNS,
        LABEL_COLUMN,
        TIME_START_COLUMN,
        _arrow_to_float64,
        _arrow_to_int64,
        _batch_column,
        _canonicalize_raw83,
        _parse_binary_labels,
    )

    contract = config["contract"]
    n_flow = int(contract["n_flow"])
    width = int(contract["raw_feature"])
    if len(DIJK_FEATURES) != width:
        raise SystemExit("Dijk 字段数与冻结宽度不符")
    target_config = load_json(Path(config["target_materialization_config"]))
    product = target_config["year_product"]
    parquet_path = Path(product["parquet_path"])
    if sha256_file(parquet_path) != product["expected_sha256"]:
        raise SystemExit("冻结年度 Parquet SHA-256 不符")
    a_state, b_state = _transform_state_paths(config)
    transformer = _restore_quantile_transformer(b_state)
    clip = tuple(float(value) for value in contract["transform_clip"])

    view = np.empty((n_flow, width), dtype="<f4")
    entity_key = np.empty(n_flow, dtype=object)
    flow_time = np.empty(n_flow, dtype=np.int64)
    flow_labels = np.empty(n_flow, dtype=np.uint8)
    raw_content_digest = hashlib.sha256()
    view_content_digest = hashlib.sha256()
    label_digest = hashlib.sha256()

    parquet_file = pq.ParquetFile(parquet_path)
    required = list(DIJK_FEATURES) + [*IP_COLUMNS, TIME_START_COLUMN, LABEL_COLUMN]
    if not set(required).issubset(parquet_file.schema_arrow.names):
        raise SystemExit("冻结年度 Parquet 缺少合法投影字段")
    batch_rows = int(config["evaluation"]["parquet_batch_rows"])
    offset = 0
    started = time.time()
    for row_group in range(parquet_file.metadata.num_row_groups):
        for batch in parquet_file.iter_batches(
            batch_size=batch_rows,
            row_groups=[row_group],
            columns=required,
            use_threads=False,
        ):
            count = batch.num_rows
            stop = offset + count
            values = np.empty((count, width), dtype=np.float64)
            for feature_index, name in enumerate(DIJK_FEATURES):
                values[:, feature_index] = _arrow_to_float64(_batch_column(batch, name))
            raw_batch, _, _, _ = _canonicalize_raw83(values)
            del values
            a_batch = _transform_a(raw_batch, a_state, clip)
            winning_batch = _transform_b(raw_batch, a_batch, b_state, transformer)
            view[offset:stop] = winning_batch
            raw_content_digest.update(raw_batch.tobytes(order="C"))
            view_content_digest.update(winning_batch.tobytes(order="C"))
            source_ip = tuple(
                str(value) for value in _batch_column(batch, IP_COLUMNS[0]).to_pylist()
            )
            destination_ip = tuple(
                str(value) for value in _batch_column(batch, IP_COLUMNS[1]).to_pylist()
            )
            entity_key[offset:stop] = np.fromiter(
                (
                    f"{left}|{right}" if left <= right else f"{right}|{left}"
                    for left, right in zip(source_ip, destination_ip, strict=True)
                ),
                dtype=object,
                count=count,
            )
            flow_time[offset:stop] = _arrow_to_int64(
                _batch_column(batch, TIME_START_COLUMN)
            )
            labels = _parse_binary_labels(_batch_column(batch, LABEL_COLUMN).to_pylist())
            flow_labels[offset:stop] = labels
            label_digest.update(labels.tobytes(order="C"))
            offset = stop
            beat("LSPR24/Parquet直读与视图重建", offset, n_flow, started)
    if offset != n_flow:
        raise SystemExit(f"冻结年度 Parquet 行数不符：{offset:,}")
    if not np.isfinite(view).all():
        raise SystemExit("重建的 LSPR24 候选 B 视图含非有限值")

    log("LSPR24：按无向地址对口径归并实体")
    _, entity = np.unique(entity_key, return_inverse=True)
    entity = entity.astype(np.int64, copy=False)
    del entity_key
    entity_count = int(entity.max()) + 1
    if entity_count != int(contract["n_entity"]):
        raise SystemExit(
            f"LSPR24 实体数应为 {int(contract['n_entity']):,}，实为 {entity_count:,}"
        )
    entity_labels = np.zeros(entity_count, dtype=np.int8)
    np.maximum.at(entity_labels, entity, flow_labels.astype(np.int8, copy=False))
    positive_entities = int(entity_labels.sum())
    if positive_entities != int(contract["n_positive_entity"]):
        raise SystemExit(
            f"LSPR24 正实体数应为 {int(contract['n_positive_entity'])}，实为 {positive_entities}"
        )
    flow_positive_rate = float(np.mean(flow_labels, dtype=np.float64))
    if abs(flow_positive_rate - float(contract["flow_positive_rate"])) >= 1e-9:
        raise SystemExit(f"LSPR24 逐流正例率不符：{flow_positive_rate:.12f}")

    cache_root = Path(config["cache"]["root"])
    cache_labels = np.asarray(
        np.load(cache_root / "y24.npy", mmap_mode="r", allow_pickle=False)
    )
    cache_times = np.asarray(
        np.load(cache_root / "t24.npy", mmap_mode="r", allow_pickle=False)
    )
    label_alignment = bool(np.array_equal(cache_labels.astype(np.uint8), flow_labels))
    time_alignment = bool(np.all(cache_times == flow_time))
    del cache_labels, cache_times
    if not (label_alignment and time_alignment):
        raise SystemExit(
            "冻结 Parquet 与缓存的标签或开始时刻不对齐，I24/M24 无法用于索引 Parquet 行"
        )

    receipt = {
        "parquet_path": str(parquet_path),
        "parquet_sha256": str(product["expected_sha256"]),
        "row_count": n_flow,
        "raw_content_sha256": raw_content_digest.hexdigest(),
        "winning_view_content_sha256": view_content_digest.hexdigest(),
        "label_content_sha256": label_digest.hexdigest(),
        "entity_key_recipe": contract["entity_key_recipe"],
        "entity_count": entity_count,
        "positive_entity_count": positive_entities,
        "flow_positive_rate": flow_positive_rate,
        "cache_y24_matches_parquet_labels": label_alignment,
        "cache_t24_matches_parquet_start_time": time_alignment,
        "persisted_rows": 0,
    }
    log(
        f"LSPR24：实体 {entity_count:,}，正实体 {positive_entities}，"
        f"逐流正例率 {flow_positive_rate:.10f}"
    )
    return {
        "view": view,
        "flow_entity": entity,
        "flow_time": flow_time,
        "flow_labels": flow_labels,
        "receipt": receipt,
    }


def derive_sequence_sidecars(
    indices: "Any",
    masks: "Any",
    flow_entity: "Any",
    flow_time: "Any",
    *,
    config: Mapping[str, Any],
    n_flow: int,
) -> tuple["Any", "Any", dict[str, Any]]:
    """按 `materialize_qualified_year_product` 的语义在内存派生序列实体与开始时刻。"""

    import numpy as np

    sequence_count = int(indices.shape[0])
    sequence_entities = np.empty(sequence_count, dtype=np.int64)
    sequence_times = np.empty(sequence_count, dtype=np.int64)
    coverage = np.zeros(n_flow, dtype=np.uint8)
    batch = int(config["evaluation"]["sidecar_batch_sequences"])
    started = time.time()
    for start in range(0, sequence_count, batch):
        stop = min(start + batch, sequence_count)
        batch_indices = np.asarray(indices[start:stop], dtype=np.int64)
        batch_mask = np.asarray(masks[start:stop]) > 0
        if not batch_mask.any(axis=1).all():
            raise SystemExit("存在没有任何有效流的序列")
        if batch_indices.min() < 0 or batch_indices.max() >= n_flow:
            raise SystemExit("序列索引矩阵（含补位）存在越界行号")
        flat = batch_indices[batch_mask]
        np.add.at(coverage, flat, 1)
        entities = flow_entity[batch_indices]
        first_position = np.argmax(batch_mask, axis=1)
        local_rows = np.arange(stop - start)
        first_index = batch_indices[local_rows, first_position]
        first_entity = entities[local_rows, first_position]
        if not np.all((entities == first_entity[:, None]) | ~batch_mask):
            raise SystemExit("同一序列内出现多个实体")
        sequence_entities[start:stop] = first_entity
        sequence_times[start:stop] = flow_time[first_index]
        beat("LSPR24/序列侧车", stop, sequence_count, started)
    covered = int(np.count_nonzero(coverage))
    if covered != n_flow or int(coverage.max()) != 1:
        raise SystemExit(
            f"序列未恰好覆盖全部流：覆盖 {covered:,}/{n_flow:,}，最大重复 {int(coverage.max())}"
        )
    receipt = {
        "sequence_count": sequence_count,
        "covered_flow_count": covered,
        "maximum_flow_multiplicity": int(coverage.max()),
        "distinct_sequence_entities": int(np.unique(sequence_entities).size),
        "semantics": "materialize_qualified_year_product 的序列实体唯一性与首个有效流开始时刻",
    }
    return sequence_entities, sequence_times, receipt


# --------------------------------------------------------------------------
# 打分与聚合：批循环逐句对齐 `flow_probe.cuda_rwkv_evaluation.evaluate_dataset`
# --------------------------------------------------------------------------


def score_and_aggregate(
    *,
    model: Any,
    view: "Any",
    indices: "Any",
    masks: "Any",
    flow_labels: "Any",
    sequence_entities: "Any",
    sequence_times: "Any",
    rows: "Any",
    batch_sequences: int,
    device: Any,
    purpose: str,
    stage: str,
) -> dict[str, Any]:
    import numpy as np
    import torch

    from flow_probe.cuda_rwkv_evaluation import (
        _entity_aggregates,
        canonical_sha256 as evaluation_canonical_sha256,
        complete_integer_fp_curve,
    )
    from sklearn.metrics import average_precision_score

    if batch_sequences <= 0:
        raise ValueError("评价序列批量必须为正")
    order = np.argsort(np.asarray(sequence_times[rows]), kind="stable")
    rows = rows[order]
    probability_parts: list[Any] = []
    label_parts: list[Any] = []
    entity_parts: list[Any] = []
    exposure_parts: list[Any] = []
    exposure_counts: dict[int, int] = {}
    model.eval()
    started = time.time()
    with torch.inference_mode():
        for start in range(0, rows.size, batch_sequences):
            batch_rows = rows[start : start + batch_sequences]
            batch_indices = np.asarray(indices[batch_rows], dtype=np.int64)
            mask = np.asarray(masks[batch_rows]) > 0
            features = torch.as_tensor(
                view[batch_indices], dtype=torch.float32, device=device
            )
            valid_mask = torch.as_tensor(mask, dtype=torch.bool, device=device)
            logits = model(features, valid_mask)
            probabilities = torch.sigmoid(logits.float()).cpu().numpy()
            flat_raw_rows = batch_indices[mask]
            flat_labels = np.asarray(flow_labels[flat_raw_rows], dtype=np.uint8)
            flat_probabilities = probabilities[mask].astype(np.float64, copy=False)
            batch_entity_values: list[Any] = []
            batch_exposure_values: list[Any] = []
            for local_index, sequence_row in enumerate(batch_rows):
                count = int(np.count_nonzero(mask[local_index]))
                entity = int(sequence_entities[sequence_row])
                previous = exposure_counts.get(entity, 0)
                batch_entity_values.append(np.full(count, entity, dtype=np.int64))
                batch_exposure_values.append(
                    np.arange(previous + 1, previous + count + 1, dtype=np.int64)
                )
                exposure_counts[entity] = previous + count
            probability_parts.append(flat_probabilities)
            label_parts.append(flat_labels)
            entity_parts.append(np.concatenate(batch_entity_values))
            exposure_parts.append(np.concatenate(batch_exposure_values))
            beat(stage, min(start + batch_sequences, int(rows.size)), int(rows.size), started)
    probabilities = np.concatenate(probability_parts)
    labels = np.concatenate(label_parts)
    entity_ids = np.concatenate(entity_parts)
    exposure_indices = np.concatenate(exposure_parts)
    if not (
        probabilities.size == labels.size == entity_ids.size == exposure_indices.size
    ):
        raise RuntimeError("CUDA-RWKV 评价聚合数组行数不一致")
    power = float(model.pooling_power.detach().cpu().item())
    log(f"{stage}：进入实体聚合，逐流 {labels.size:,} 条，池化幂 {power:.6f}")
    aggregates = _entity_aggregates(
        probabilities, labels, entity_ids, exposure_indices, power
    )
    entity_labels = aggregates["labels"]
    entity_scores = aggregates["scores"]
    maximum_scores = aggregates["maximum_scores"]
    terminal_curve = complete_integer_fp_curve(entity_scores, entity_labels)
    first_alert_curve = complete_integer_fp_curve(
        aggregates["operational_scores"],
        entity_labels,
        positive_paths=aggregates["positive_paths"],
    )
    result = {
        "schema_version": "cuda-rwkv-aggregate-evaluation-v1",
        "purpose": purpose,
        "flow_count": int(labels.size),
        "entity_count": int(entity_labels.size),
        "positive_flow_count": int(labels.sum()),
        "positive_entity_count": int(entity_labels.sum()),
        "pooling_power": power,
        "flow_average_precision": float(average_precision_score(labels, probabilities)),
        "entity_average_precision": float(
            average_precision_score(entity_labels, entity_scores)
        ),
        "maximum_entity_average_precision": float(
            average_precision_score(entity_labels, maximum_scores)
        ),
        "terminal_common_integer_fp": terminal_curve,
        "first_alert_common_integer_fp": first_alert_curve,
        "persisted_score_rows": 0,
        "persisted_label_rows": 0,
        "persisted_member_rows": 0,
    }
    result["result_sha256"] = evaluation_canonical_sha256(result)
    return result


def budget_readouts(curve: Mapping[str, Any]) -> list[dict[str, Any]]:
    """六档名义 FPR 预算的实际可达 FPR 与检出率。"""

    readouts: list[dict[str, Any]] = []
    for anchor in curve["anchors"]:
        readouts.append(
            {
                "nominal_fpr": anchor["nominal_fpr"],
                "budget_false_positive_entities": anchor["budget_fp"],
                "achievable_fpr": anchor["actual_fpr"],
                "detection_rate": anchor["detection_rate"],
                "detected_positive_entities": anchor["tp"],
                "false_positive_entities": anchor["fp"],
                "threshold": anchor["threshold"],
                "next_reachable_fp": anchor["next_reachable_fp"],
                "tie_group_size": anchor["tie_group_size"],
            }
        )
    return readouts


def compact_cell_summary(cell: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cell": cell,
        "flow_count": metrics["flow_count"],
        "entity_count": metrics["entity_count"],
        "positive_entity_count": metrics["positive_entity_count"],
        "pooling_power": metrics["pooling_power"],
        "entity_average_precision": metrics["entity_average_precision"],
        "maximum_entity_average_precision": metrics["maximum_entity_average_precision"],
        "flow_average_precision": metrics["flow_average_precision"],
        "terminal_budget_readouts": budget_readouts(
            metrics["terminal_common_integer_fp"]
        ),
        "first_alert_budget_readouts": budget_readouts(
            metrics["first_alert_common_integer_fp"]
        ),
        "result_sha256": metrics["result_sha256"],
    }


# --------------------------------------------------------------------------
# 冻结四格模型加载：复用资格入口的身份门
# --------------------------------------------------------------------------


def load_qualification(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """校验源年资格封印的内容哈希、输入臂绑定与目标年零接触声明。"""

    from flow_probe.protocol_a_raw83 import validate_source_qualification_seal

    seal_path = Path(config["qualification"]["source_seal"])
    # 源年数据产品尚未执行输入臂封印（清单 source_input_arm_sha256 为 null，
    # 目标物化配置因此停在 blocked-until-source-arm-seal）。这里用资格封印
    # 自带的输入臂摘要过校验，真正的防漂移门是下面对内容哈希的定值断言。
    declared_arm = str(load_json(seal_path)["source_input_arm_sha256"])
    seal = validate_source_qualification_seal(
        seal_path, expected_input_arm_sha256=declared_arm
    )
    expected_content = str(config["qualification"]["source_seal_content_sha256"])
    if str(seal["seal_sha256"]) != expected_content:
        raise SystemExit(f"源年资格封印内容 SHA-256 漂移：{seal['seal_sha256']}")
    expected_file = config["qualification"].get("source_seal_file_sha256")
    observed_file = sha256_file(seal_path)
    if expected_file is not None and observed_file != str(expected_file):
        raise SystemExit(f"源年资格封印文件 SHA-256 漂移：{observed_file}")
    qualification_config = load_json(Path(config["qualification"]["config_path"]))
    return qualification_config, seal


def load_cell_model(
    qualification_config: Mapping[str, Any],
    seal: Mapping[str, Any],
    cell: str,
) -> Any:
    from ch3_cuda_rwkv_raw83_qualification import _load_frozen_cell_model

    return _load_frozen_cell_model(qualification_config, seal["cells"][cell], seal)


# --------------------------------------------------------------------------
# 动作
# --------------------------------------------------------------------------


def action_selfcheck(config: Mapping[str, Any]) -> dict[str, Any]:
    """用源年验证区复算四格指标，与已封印 `source-metrics.json` 对表。"""

    import numpy as np
    import torch

    contract = config["contract"]
    qualification_config, seal = load_qualification(config)
    artifacts = _source_artifacts(config)

    log("自检：从源年冻结 raw83 重建候选 B 视图")
    view = build_arm_b_view_from_raw(
        Path(artifacts["source_raw83"]["path"]),
        config=config,
        row_count=int(contract["source_row_count"]),
        stage="LSPR23/视图重建",
    )
    view_comparison = compare_view_with_source_product(view, config)
    log(f"自检：视图逐字节比对 mismatched_cells={view_comparison['mismatched_cells']}")
    if not view_comparison["passed"]:
        raise SystemExit("重建的源年候选 B 视图与封印视图不一致，停止自检")

    indices = np.load(Path(artifacts["I23"]["path"]), mmap_mode="r", allow_pickle=False)
    masks = np.load(Path(artifacts["M23"]["path"]), mmap_mode="r", allow_pickle=False)
    sequence_entities = np.asarray(
        np.load(Path(artifacts["E23"]["path"]), allow_pickle=False), dtype=np.int64
    )
    sequence_times = np.asarray(
        np.load(Path(artifacts["T23"]["path"]), allow_pickle=False), dtype=np.int64
    )
    rows = np.asarray(
        np.load(Path(artifacts["validation_rows"]["path"]), allow_pickle=False),
        dtype=np.int64,
    )
    if rows.size != int(contract["validation_sequence_count"]):
        raise SystemExit(f"源年验证序列数不符：{rows.size}")
    cache_root = Path(config["cache"]["root"])
    flow_labels = np.asarray(
        np.load(cache_root / "y23.npy", mmap_mode="r", allow_pickle=False)
    ).astype(np.uint8, copy=False)

    device = torch.device("cuda")
    comparisons: list[dict[str, Any]] = []
    tolerance = float(config["evaluation"]["selfcheck_metric_tolerance"])
    for cell in config["evaluation"]["cells"]:
        log(f"自检：加载冻结 {cell} 并在源年验证区复算")
        model = load_cell_model(qualification_config, seal, cell)
        metrics = score_and_aggregate(
            model=model,
            view=view,
            indices=indices,
            masks=masks,
            flow_labels=flow_labels,
            sequence_entities=sequence_entities,
            sequence_times=sequence_times,
            rows=rows,
            batch_sequences=int(config["evaluation"]["batch_sequences"]),
            device=device,
            purpose="validate",
            stage=f"LSPR23/{cell}打分",
        )
        sealed = load_json(Path(seal["cells"][cell]["source_metrics_path"]))
        entry: dict[str, Any] = {"cell": cell, "metrics": {}}
        for key in (
            "flow_average_precision",
            "entity_average_precision",
            "maximum_entity_average_precision",
            "flow_count",
            "entity_count",
            "positive_entity_count",
            "pooling_power",
        ):
            recomputed = metrics[key]
            published = sealed[key]
            difference = abs(float(recomputed) - float(published))
            entry["metrics"][key] = {
                "recomputed": recomputed,
                "sealed": published,
                "absolute_difference": difference,
                "within_tolerance": difference <= tolerance,
            }
        entry["result_sha256_match"] = metrics["result_sha256"] == sealed.get(
            "result_sha256"
        )
        entry["all_within_tolerance"] = all(
            item["within_tolerance"] for item in entry["metrics"].values()
        )
        comparisons.append(entry)
        log(
            f"自检：{cell} 实体AP 复算 {metrics['entity_average_precision']:.12f} "
            f"对封印 {sealed['entity_average_precision']:.12f}，"
            f"result_sha256 一致={entry['result_sha256_match']}"
        )
        del model
        torch.cuda.empty_cache()
    receipt = {
        "schema_version": f"{SCHEMA_VERSION}-selfcheck-v1",
        "view_comparison": view_comparison,
        "metric_tolerance": tolerance,
        "cells": comparisons,
        "all_passed": all(item["all_within_tolerance"] for item in comparisons),
        "all_result_sha256_match": all(item["result_sha256_match"] for item in comparisons),
    }
    receipt["receipt_sha256"] = canonical_sha256(receipt)
    return receipt


def action_evaluate(config: Mapping[str, Any]) -> dict[str, Any]:
    """四格各在 LSPR24 上评价恰好一次。"""

    import numpy as np
    import torch

    cache_root = Path(config["cache"]["root"])
    contract = config["contract"]
    output_root = Path(config["paths"]["output_root"])
    qualification_config, seal = load_qualification(config)

    target = read_target_year(config)
    view = target["view"]
    indices = np.load(cache_root / "I24.npy", mmap_mode="r", allow_pickle=False)
    masks = np.load(cache_root / "M24.npy", mmap_mode="r", allow_pickle=False)
    sequence_entities, sequence_times, sidecar_receipt = derive_sequence_sidecars(
        indices,
        masks,
        target["flow_entity"],
        target["flow_time"],
        config=config,
        n_flow=int(contract["n_flow"]),
    )
    flow_labels = target["flow_labels"]
    rows = np.arange(int(indices.shape[0]), dtype=np.int64)
    device = torch.device("cuda")
    cells: dict[str, Any] = {}
    summaries: list[dict[str, Any]] = []
    for cell in config["evaluation"]["cells"]:
        cell_path = output_root / "target-cells" / f"{cell}.json"
        if cell_path.is_file():
            log(f"{cell}：已有完成收据，跳过重复评价")
            metrics = load_json(cell_path)
        else:
            log(f"{cell}：加载冻结检查点并开始唯一一次目标年评价")
            model = load_cell_model(qualification_config, seal, cell)
            torch.cuda.reset_peak_memory_stats()
            started = time.time()
            metrics = score_and_aggregate(
                model=model,
                view=view,
                indices=indices,
                masks=masks,
                flow_labels=flow_labels,
                sequence_entities=sequence_entities,
                sequence_times=sequence_times,
                rows=rows,
                batch_sequences=int(config["evaluation"]["batch_sequences"]),
                device=device,
                purpose="target-evaluate",
                stage=f"LSPR24/{cell}打分",
            )
            elapsed = max(time.time() - started, 0.0)
            metrics.update(
                {
                    "cell": cell,
                    "independent_test": False,
                    "target_previously_accessed": True,
                    "evaluation_call": 1,
                    "best_checkpoint": seal["cells"][cell]["best_checkpoint"],
                    "best_checkpoint_sha256": seal["cells"][cell]["best_checkpoint_sha256"],
                    "resource": {
                        "evaluation_seconds": elapsed,
                        "flow_throughput_per_second": (
                            None if elapsed <= 0 else int(metrics["flow_count"]) / elapsed
                        ),
                        "cuda_max_memory_allocated_bytes": int(
                            torch.cuda.max_memory_allocated()
                        ),
                        "cuda_max_memory_reserved_bytes": int(
                            torch.cuda.max_memory_reserved()
                        ),
                        "resource_contention": True,
                        "resource_contention_note": (
                            "同卡存在其他进程，时间与显存为并发条件实测"
                        ),
                    },
                }
            )
            atomic_json(cell_path, metrics)
            del model
            torch.cuda.empty_cache()
        cells[cell] = {
            "cell_result_path": str(cell_path),
            "result_sha256": metrics["result_sha256"],
        }
        summary = compact_cell_summary(cell, metrics)
        summaries.append(summary)
        log(
            f"{cell}：实体AP {summary['entity_average_precision']:.12f}，"
            f"最大池化实体AP {summary['maximum_entity_average_precision']:.12f}，"
            f"逐流AP {summary['flow_average_precision']:.12f}"
        )
    result = {
        "schema_version": f"{SCHEMA_VERSION}-target-descriptive-evaluation-v1",
        "run_id": config["run_id"],
        "display_name": config["display_name"],
        "boundary": config["boundary"],
        "source_seal_content_sha256": config["qualification"]["source_seal_content_sha256"],
        "source_seal_file_sha256": sha256_file(
            Path(config["qualification"]["source_seal"])
        ),
        "target_year_read": target["receipt"],
        "sequence_sidecars": sidecar_receipt,
        "cells": cells,
        "summaries": summaries,
        "persisted_score_rows": 0,
        "persisted_label_rows": 0,
        "persisted_member_rows": 0,
    }
    result["result_sha256"] = canonical_sha256(result)
    return result


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--action",
        choices=("verify", "selfcheck", "evaluate", "all"),
        default="all",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_args(argv)
    config = load_json(arguments.config)
    if config.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit("配置模式不符")
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    actions = (
        ("verify", "selfcheck", "evaluate")
        if arguments.action == "all"
        else (arguments.action,)
    )
    for action in actions:
        log(f"==== 动作 {action} 开始 ====")
        if action == "verify":
            receipt = verify_data_identity(config)
            atomic_json(output_root / "data-verification.json", receipt)
            if not receipt["blocking_passed"]:
                failed = [
                    item["check"]
                    for item in receipt["checks"]
                    if not item["passed"] and item["blocking"]
                ]
                raise SystemExit(f"数据身份阻断核验不通过：{failed}")
        elif action == "selfcheck":
            receipt = action_selfcheck(config)
            atomic_json(output_root / "source-selfcheck.json", receipt)
            if not receipt["all_passed"]:
                raise SystemExit("源年复算与封印指标不一致，拒绝进入目标年评价")
        else:
            result = action_evaluate(config)
            atomic_json(output_root / "target-results.json", result)
            atomic_json(
                output_root / "target-summary.json",
                {
                    "schema_version": f"{SCHEMA_VERSION}-summary-v1",
                    "target_year_read": result["target_year_read"],
                    "summaries": result["summaries"],
                    "result_sha256": result["result_sha256"],
                },
            )
        log(f"==== 动作 {action} 完成 ====")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
