#!/usr/bin/env python3
"""生成 LSPR23 Protocol A 训练区七个字段的只读基数收据。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from dijk2026_replication.dijk_fields import DIJK_FEATURES


SCHEMA_VERSION = "ch3-lspr23-field-cardinality-receipt-config-v1"
RESULT_SCHEMA_VERSION = "ch3-lspr23-field-cardinality-receipt-v1"
RUN_ID = "ch3-lspr23-field-cardinality-receipt-v1"
SOURCE_ARRAYS = ("X23", "I23", "M23", "E23", "T23")
EXPECTED_FIELDS = (
    "SrcPort",
    "DstPort",
    "Protocol",
    "L3/L4 Protocol",
    "Int/Ext Dst IP",
    "External_src",
    "External_dst",
)
EXPECTED_SPLIT_STATS = {
    "entity_count": 150_680,
    "train_sequences": 208_598,
    "validation_sequences": 22_444,
    "train_validation_row_intersection": 0,
}


def sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial.{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def peak_rss_mib() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value / 1024.0 if sys.platform != "darwin" else value / (1024.0 * 1024.0)


def write_status(output_root: Path, state: str, stage: str, detail: str, exit_code: int | None) -> None:
    atomic_json(
        output_root / "status.json",
        {
            "schema_version": "ch3-lspr23-field-cardinality-receipt-status-v1",
            "run_id": RUN_ID,
            "state": state,
            "stage": stage,
            "detail": detail,
            "exit_code": exit_code,
            "updated_at_unix": time.time(),
            "target_year_arrays_read": 0,
            "source_year_only": True,
        },
    )


def load_config(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("配置顶层必须是对象")
    return value


def validate_config(config: dict[str, Any]) -> None:
    if config.get("schema_version") != SCHEMA_VERSION or config.get("run_id") != RUN_ID:
        raise ValueError("配置模式或运行身份不符")
    if config.get("source_arrays") != list(SOURCE_ARRAYS):
        raise ValueError("只允许读取 X23/I23/M23/E23/T23")
    if any(name == "y23" or "24" in name for name in config["source_arrays"]):
        raise ValueError("禁止标签或 LSPR24 数组")
    if config.get("target_year_arrays_read") != 0 or config.get("source_year_only") is not True:
        raise ValueError("必须冻结为 LSPR23 只读诊断")
    if tuple(config.get("fields", ())) != EXPECTED_FIELDS:
        raise ValueError("字段清单或顺序不符")
    if config.get("training") != {
        "seed": 42,
        "validation_fraction": 0.1,
        "time_tail_fraction": 0.15,
        "source_split_implementation": "verbatim_ch3_resmlp2_tabm_protocol_a_2x2_source_split",
    }:
        raise ValueError("Protocol A 切分合同不符")
    statistics = config.get("statistics")
    if not isinstance(statistics, dict) or statistics.get("chunk_rows") != 131_072:
        raise ValueError("分块统计合同不符")
    if statistics.get("top_k_values") != 20 or statistics.get("coverage_k") != [1, 10, 100, 1000]:
        raise ValueError("字段汇总输出合同不符")
    if statistics.get("one_hot_policy") != "report_facts_only_no_automatic_encoding_decision":
        raise ValueError("不得自动裁决编码")
    if config.get("resource_contract", {}).get("execution_device") != "cpu":
        raise ValueError("本工具必须固定 CPU")
    paths = config.get("paths", {})
    if Path(paths.get("output_root", "")).name != RUN_ID:
        raise ValueError("输出根必须与运行身份一致")


def open_arrays(cache_root: Path) -> tuple[dict[str, np.ndarray], dict[str, dict[str, Any]]]:
    arrays: dict[str, np.ndarray] = {}
    inventory: dict[str, dict[str, Any]] = {}
    for name in SOURCE_ARRAYS:
        if name == "y23" or "24" in name:
            raise RuntimeError("禁止读取标签或 LSPR24 数组")
        path = cache_root / f"{name}.npy"
        if not path.is_file():
            raise FileNotFoundError(f"缺少冻结数组：{path}")
        array = np.load(path, mmap_mode="r", allow_pickle=False)
        arrays[name] = array
        inventory[name] = {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "mmap_mode": "r",
        }
    return arrays, inventory


def protocol_a_split(entity: np.ndarray, timestamp: np.ndarray, training: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    unique_entity = np.unique(entity)
    permutation = np.random.RandomState(training["seed"]).permutation(len(unique_entity))
    count = max(1, int(len(unique_entity) * training["validation_fraction"]))
    validation_entities = set(unique_entity[permutation[:count]].tolist())
    entity_mask = np.fromiter((value in validation_entities for value in entity), bool, len(entity))
    time_cut = np.quantile(timestamp, 1.0 - training["time_tail_fraction"])
    time_mask = timestamp >= time_cut
    train_rows = np.flatnonzero(~(entity_mask | time_mask))
    validation_rows = np.flatnonzero(entity_mask & ~time_mask)
    stats = {
        "entity_count": int(len(unique_entity)),
        "train_sequences": int(len(train_rows)),
        "validation_sequences": int(len(validation_rows)),
        "train_validation_row_intersection": int(np.intersect1d(train_rows, validation_rows).size),
    }
    if stats != EXPECTED_SPLIT_STATS:
        raise RuntimeError(f"Protocol A 切分统计不符：{stats}")
    return train_rows, validation_rows, stats


def entity_identity(entity: np.ndarray, train_rows: np.ndarray, validation_rows: np.ndarray) -> dict[str, Any]:
    train_entities = np.unique(entity[train_rows])
    validation_entities = np.unique(entity[validation_rows])
    intersection = np.intersect1d(train_entities, validation_entities)
    return {
        "all_sequence_entities": int(len(np.unique(entity))),
        "train_entities": int(len(train_entities)),
        "validation_entities": int(len(validation_entities)),
        "train_validation_entity_intersection": int(len(intersection)),
        "zero_intersection": bool(len(intersection) == 0),
        "train_entity_membership_sha256": canonical_sha256(train_entities.tolist()),
        "validation_entity_membership_sha256": canonical_sha256(validation_entities.tolist()),
    }


def build_effective_flow_mask(indices: np.ndarray, mask: np.ndarray, train_rows: np.ndarray, flow_count: int) -> tuple[np.ndarray, dict[str, Any]]:
    if indices.shape != mask.shape or indices.ndim != 2:
        raise RuntimeError("I23/M23 形状不符")
    effective = np.zeros(flow_count, dtype=bool)
    sequence_width = indices.shape[1]
    valid_occurrences = 0
    for start in range(0, len(train_rows), 4096):
        rows = train_rows[start : start + 4096]
        current_mask = np.asarray(mask[rows], dtype=bool)
        current_indices = np.asarray(indices[rows])
        selected = current_indices[current_mask]
        if selected.size:
            if int(selected.min()) < 0 or int(selected.max()) >= flow_count:
                raise RuntimeError("I23 存在越界流索引")
            effective[selected] = True
            valid_occurrences += int(selected.size)
    return effective, {
        "train_sequences": int(len(train_rows)),
        "sequence_length": int(sequence_width),
        "valid_sequence_flow_occurrences": valid_occurrences,
        "effective_flows": int(effective.sum()),
        "deduplicated_flow_mapping": True,
        "effective_flow_mask_sha256": hashlib.sha256(effective.tobytes()).hexdigest(),
    }


def json_scalar(value: Any) -> int | float:
    scalar = np.asarray(value).item()
    return int(scalar) if isinstance(scalar, (np.integer, int)) else float(scalar)


def field_statistics(
    values: np.ndarray,
    effective_flow_mask: np.ndarray,
    chunk_rows: int,
    top_k: int,
    coverage_k: list[int],
) -> dict[str, Any]:
    counts: defaultdict[int | float, int] = defaultdict(int)
    finite_count = 0
    missing_count = 0
    minimum: float | None = None
    maximum: float | None = None
    integer_like = True
    selected_count = int(effective_flow_mask.sum())
    for start in range(0, len(values), chunk_rows):
        stop = min(start + chunk_rows, len(values))
        local_selection = effective_flow_mask[start:stop]
        if not local_selection.any():
            continue
        block = np.asarray(values[start:stop][local_selection])
        finite = np.isfinite(block)
        missing_count += int((~finite).sum())
        if not finite.any():
            continue
        clean = block[finite]
        finite_count += int(clean.size)
        local_min = float(clean.min())
        local_max = float(clean.max())
        minimum = local_min if minimum is None else min(minimum, local_min)
        maximum = local_max if maximum is None else max(maximum, local_max)
        integer_like = integer_like and bool(np.equal(clean, np.floor(clean)).all())
        unique, local_counts = np.unique(clean, return_counts=True)
        for value, count in zip(unique, local_counts, strict=True):
            counts[json_scalar(value)] += int(count)
    if finite_count + missing_count != selected_count:
        raise RuntimeError("字段有限值与缺失值计数未覆盖全部有效流")
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    coverage = {
        str(k): (sum(count for _, count in ordered[:k]) / finite_count if finite_count else 0.0)
        for k in coverage_k
    }
    return {
        "finite_count": finite_count,
        "missing_count": missing_count,
        "missing_fraction": missing_count / selected_count if selected_count else 0.0,
        "unique_count": len(counts),
        "min": minimum,
        "max": maximum,
        "integer_like": integer_like if finite_count else None,
        "top_coverage": coverage,
        "top_values": [{"value": value, "count": count} for value, count in ordered[:top_k]],
        "direct_one_hot_facts": {
            "automatic_encoding_decision": "not_made",
            "observed_basis": "本字段的 unique_count 与 top_coverage 为直接 one-hot 可行性评估的事实输入。",
            "interpretation_limit": "本收据不设置基数阈值、不选择高频 K 或 OOV，也不裁决编码方案。",
        },
        "counting_method": "per_field_chunk_unique_then_exact_aggregate",
    }


def run(config_path: Path) -> Path:
    config = load_config(config_path)
    validate_config(config)
    output_root = Path(config["paths"]["output_root"])
    output_root.mkdir(parents=True, exist_ok=True)
    receipt_path = output_root / "field-cardinality-receipt.json"
    config_sha = sha256_file(config_path)
    code_sha = sha256_file(Path(__file__).resolve())
    if receipt_path.is_file():
        existing = load_config(receipt_path)
        identity = existing.get("identity", {})
        if existing.get("complete") is True and identity.get("config_sha256") == config_sha and identity.get("code_sha256") == code_sha:
            print(f"已存在身份匹配的完整收据：{receipt_path}", flush=True)
            return receipt_path
        raise RuntimeError("同名输出已存在但身份不匹配，拒绝覆盖")
    started = time.time()
    write_status(output_root, "running", "open_arrays", "仅读取冻结 LSPR23 五数组", None)
    arrays, inventory = open_arrays(Path(config["paths"]["cache_root"]))
    X23, I23, M23, E23, T23 = (arrays[name] for name in SOURCE_ARRAYS)
    if X23.shape != (16_353_511, 83) or I23.shape != (271_815, 128):
        raise RuntimeError(f"冻结缓存形状不符：X23={X23.shape}, I23={I23.shape}")
    if M23.shape != I23.shape or len(E23) != len(I23) or len(T23) != len(I23):
        raise RuntimeError("五数组行维度不一致")
    train_rows, validation_rows, split_stats = protocol_a_split(E23, T23, config["training"])
    identities = entity_identity(E23, train_rows, validation_rows)
    if not identities["zero_intersection"]:
        raise RuntimeError("训练与验证实体存在交集")
    write_status(output_root, "running", "map_effective_flows", "用 I23/M23 映射训练有效流", None)
    effective_mask, flow_mapping = build_effective_flow_mask(I23, M23, train_rows, len(X23))
    if flow_mapping["effective_flows"] == 0:
        raise RuntimeError("训练有效流数为零")
    field_positions = {field: DIJK_FEATURES.index(field) for field in EXPECTED_FIELDS}
    fields: dict[str, Any] = {}
    statistics = config["statistics"]
    for position, field in enumerate(EXPECTED_FIELDS, start=1):
        write_status(output_root, "running", "count_fields", f"正在统计 {position}/{len(EXPECTED_FIELDS)}：{field}", None)
        result = field_statistics(
            X23[:, field_positions[field]],
            effective_mask,
            statistics["chunk_rows"],
            statistics["top_k_values"],
            statistics["coverage_k"],
        )
        result["dijk_feature_index"] = field_positions[field]
        fields[field] = result
        print(f"字段完成 {position}/{len(EXPECTED_FIELDS)}：{field}，unique_count={result['unique_count']}", flush=True)
    receipt = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "run_id": RUN_ID,
        "display_name": config["display_name"],
        "complete": True,
        "identity": {
            "config_path": str(config_path),
            "config_sha256": config_sha,
            "code_path": str(Path(__file__).resolve()),
            "code_sha256": code_sha,
            "field_list": list(EXPECTED_FIELDS),
            "field_list_sha256": canonical_sha256(list(EXPECTED_FIELDS)),
            "dijk_feature_list_sha256": canonical_sha256(list(DIJK_FEATURES)),
            "target_year_arrays_read": 0,
            "forbidden_arrays": ["y23", "X24", "y24", "I24", "M24", "s24", "d24", "t24"],
        },
        "arrays": inventory,
        "protocol_a_source_split": {
            "implementation": config["training"]["source_split_implementation"],
            "seed": config["training"]["seed"],
            "validation_fraction": config["training"]["validation_fraction"],
            "time_tail_fraction": config["training"]["time_tail_fraction"],
            "statistics": split_stats,
            "entity_identity": identities,
        },
        "training_effective_flows": flow_mapping,
        "fields": fields,
        "resource": {
            "execution_device": "cpu",
            "x23_mmap_mode": "r",
            "chunk_rows": statistics["chunk_rows"],
            "peak_process_rss_mib": peak_rss_mib(),
            "elapsed_seconds": time.time() - started,
        },
    }
    atomic_json(receipt_path, receipt)
    write_status(output_root, "finished", "complete", "字段基数收据已原子发布", 0)
    return receipt_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 LSPR23 Protocol A 训练区字段基数只读收据")
    parser.add_argument("--config", required=True, help="冻结 JSON 配置路径")
    parser.add_argument("--validate-config", action="store_true", help="只校验配置")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    try:
        config = load_config(config_path)
        validate_config(config)
        if args.validate_config:
            print("配置校验通过", flush=True)
            return 0
        receipt = run(config_path)
        print(f"收据完成：{receipt}", flush=True)
        return 0
    except Exception as error:
        if not args.validate_config:
            try:
                config = load_config(config_path)
                output_root = Path(config.get("paths", {}).get("output_root", ""))
                if output_root.name == RUN_ID:
                    write_status(output_root, "failed", "exception", str(error), 1)
            except Exception:
                pass
        print(f"失败：{error}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
