#!/usr/bin/env python3
"""冻结 QUIC 种子连接分区及连续四窗构造合同。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


class PartitionError(RuntimeError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> str:
    payload = (_canonical_json(value) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return _sha256_bytes(payload)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    payload = "".join(
        _canonical_json(dict(row)) + "\n" for row in rows
    ).encode("utf-8")
    path.write_bytes(payload)
    return _sha256_bytes(payload)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.endswith("\n"):
                raise PartitionError(f"JSONL 末行缺少换行：{path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PartitionError(f"JSONL 行不是对象：{path}:{line_number}")
            rows.append(value)
    return rows


def materialize(config_path: Path, project_root: Path) -> Path:
    project_root = project_root.resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise PartitionError("配置顶层不是对象")

    input_path = (project_root / str(config["input"]["path"])).resolve()
    if project_root not in input_path.parents:
        raise PartitionError(f"输入路径越界：{input_path}")
    if not input_path.is_file() or input_path.is_symlink():
        raise PartitionError(f"输入不是普通文件：{input_path}")
    input_sha = _sha256_file(input_path)
    if input_sha != str(config["input"]["sha256"]):
        raise PartitionError("输入连接清单哈希不一致")
    input_rows = _load_jsonl(input_path)
    if len(input_rows) != int(config["input"]["row_count"]):
        raise PartitionError("输入连接清单行数不一致")

    source_hashes = [str(row["source_qlog_sha256"]) for row in input_rows]
    group_ids = [str(row["physics_group_sha256"]) for row in input_rows]
    trace_ids = [str(row["trace_id"]) for row in input_rows]
    if len(set(source_hashes)) != len(input_rows):
        raise PartitionError("qlog 内容哈希不是逐连接唯一")
    if len(set(group_ids)) != len(input_rows) or len(set(trace_ids)) != len(input_rows):
        raise PartitionError("qlog 连接分组或轨迹标识重复")

    seed = int(config["partition"]["seed"])
    ranked = sorted(
        input_rows,
        key=lambda row: _sha256_bytes(
            (
                "r2-quic-seed-split-v1\0"
                f"{seed}\0{row['source_qlog_sha256']}"
            ).encode("utf-8")
        ),
    )
    split_counts = {
        str(name): int(value)
        for name, value in config["partition"]["ordered_counts"].items()
    }
    if sum(split_counts.values()) != len(ranked):
        raise PartitionError("连接分区目标数之和与输入不一致")
    split_by_trace: dict[str, str] = {}
    cursor = 0
    for split_id, count in split_counts.items():
        for row in ranked[cursor : cursor + count]:
            split_by_trace[str(row["trace_id"])] = split_id
        cursor += count

    rows: list[dict[str, Any]] = []
    total_sequences = 0
    sequence_counts = Counter()
    for row in sorted(input_rows, key=lambda item: int(item["connection_stable_order"])):
        full_windows = int(row["full_window_rows"])
        sequence_count = full_windows // int(config["sequence"]["window_count"])
        dropped_windows = full_windows % int(config["sequence"]["window_count"])
        split_id = split_by_trace[str(row["trace_id"])]
        total_sequences += sequence_count
        sequence_counts[split_id] += sequence_count
        rows.append(
            {
                "schema_version": "flow_probe_r2_final_quic_seed_connection_split_v1",
                "trace_id": str(row["trace_id"]),
                "connection_stable_order": int(row["connection_stable_order"]),
                "physics_group_sha256": str(row["physics_group_sha256"]),
                "source_qlog_sha256": str(row["source_qlog_sha256"]),
                "split_id": split_id,
                "full_window_rows": full_windows,
                "sequence_count": sequence_count,
                "dropped_tail_windows": dropped_windows,
                "sequence_window_count": int(config["sequence"]["window_count"]),
                "sequence_stride_windows": int(config["sequence"]["stride_windows"]),
                "seed_validation_only": True,
                "formal_training_weight": 0.0,
                "quic_formal_training_enabled": False,
                "quic_expert_ready": False,
                "final_test_visible": False,
            }
        )
    if total_sequences != int(config["sequence"]["expected_sequence_count"]):
        raise PartitionError(
            f"四窗序列数不符合合同：{total_sequences} != "
            f"{config['sequence']['expected_sequence_count']}"
        )

    output_root = project_root / str(config["output_root"])
    partial_root = output_root.with_name(f"{output_root.name}.partial")
    if output_root.exists() or partial_root.exists():
        raise PartitionError("输出根或阶段根已存在，拒绝覆盖")
    partial_root.mkdir(parents=True)

    splits_path = partial_root / "quic-seed-connection-splits.jsonl"
    splits_sha = _write_jsonl(splits_path, rows)
    construction = {
        "schema_version": "flow_probe_r2_final_quic_seed_sequence_contract_v1",
        "dataset_version": str(config["dataset_version"]),
        "connection_split_counts": Counter(row["split_id"] for row in rows),
        "sequence_counts": dict(sorted(sequence_counts.items())),
        "total_sequences": total_sequences,
        "construction": {
            "window_count": int(config["sequence"]["window_count"]),
            "window_duration_ns": int(config["sequence"]["window_duration_ns"]),
            "stride_windows": int(config["sequence"]["stride_windows"]),
            "window_indices": "[4*i,4*i+1,4*i+2,4*i+3]",
            "cross_connection": False,
            "partial_tail_policy": "drop",
        },
        "seed_validation_only": True,
        "formal_training_weight": 0.0,
        "quic_formal_training_enabled": False,
        "quic_expert_ready": False,
        "final_test_visible": False,
    }
    construction_path = partial_root / "sequence-construction.json"
    construction_sha = _write_json(construction_path, construction)
    contract_path = partial_root / "contract.json"
    contract_sha = _write_json(contract_path, config)
    artifacts = [
        {
            "relative_path": splits_path.name,
            "row_count": len(rows),
            "size_bytes": splits_path.stat().st_size,
            "sha256": splits_sha,
        },
        {
            "relative_path": construction_path.name,
            "row_count": None,
            "size_bytes": construction_path.stat().st_size,
            "sha256": construction_sha,
        },
        {
            "relative_path": contract_path.name,
            "row_count": None,
            "size_bytes": contract_path.stat().st_size,
            "sha256": contract_sha,
        },
    ]
    artifacts.sort(key=lambda item: str(item["relative_path"]))
    manifest = {
        "schema_version": "flow_probe_r2_final_quic_seed_partition_artifact_manifest_v1",
        "dataset_version": str(config["dataset_version"]),
        "status": "review_pending",
        "seed_validation_only": True,
        "formal_training_weight": 0.0,
        "quic_formal_training_enabled": False,
        "quic_expert_ready": False,
        "final_test_visible": False,
        "artifacts": artifacts,
        "artifact_payload_merkle_sha256": _sha256_bytes(
            _canonical_json(artifacts).encode("utf-8")
        ),
    }
    _write_json(partial_root / "artifact-manifest.json", manifest)
    os.rename(partial_root, output_root)
    return output_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    arguments = parser.parse_args()
    output = materialize(arguments.config.resolve(), arguments.project_root.resolve())
    print(output)


if __name__ == "__main__":
    main()
