from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence
from zipfile import ZipFile

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml

from r2_final_sidecar_candidate_materialize import (
    MaterializationError,
    _artifact_entry,
    _canonical_json,
    _empty_history_row,
    _genis_candidate_id,
    _history_schema,
    _normalise_transport,
    _route_record,
    _route_schema,
    _schema_sha256,
    _semantic_sha256,
    _sha256_file,
    _window_history_row,
    _write_json,
    _write_jsonl,
    _write_parquet,
)


SCHEMA_VERSION = "flow_probe_r2_final_development_views_v1"
SOURCES = ("genis", "tqhc2")
SPLITS = ("calibration", "validation")
ABSOLUTE_INPUT_PREFIX = Path("/root/autodl-tmp/thesis/datasets")


def _resolve_input(project_root: Path, spec: Mapping[str, Any]) -> Path:
    root_name = str(spec["root"])
    raw_path = Path(str(spec["path"]))
    if root_name == "project":
        if raw_path.is_absolute() or ".." in raw_path.parts:
            raise MaterializationError(f"项目输入路径不合法：{raw_path}")
        return project_root / raw_path
    if root_name == "absolute":
        resolved = raw_path.resolve()
        if not raw_path.is_absolute() or not resolved.is_relative_to(
            ABSOLUTE_INPUT_PREFIX
        ):
            raise MaterializationError(f"绝对输入路径不在允许目录：{raw_path}")
        return resolved
    raise MaterializationError(f"未知输入根：{root_name}")


def _validate_input(path: Path, expected_sha256: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise MaterializationError(f"输入不是普通文件：{path}")
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise MaterializationError(
            f"输入 SHA-256 不一致：{path}，期望 {expected_sha256}，实际 {actual_sha256}"
        )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise MaterializationError(f"JSONL 含空行：{path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise MaterializationError(
                    f"JSONL 行不是对象：{path}:{line_number}"
                )
            rows.append(value)
    return rows


def _sample_order_sha256(sample_ids: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(sample_ids).encode("utf-8")).hexdigest()


def _atomic_write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    _write_json(temporary, value)
    os.replace(temporary, path)


def _validate_row_count(
    rows: Sequence[Mapping[str, Any]], spec: Mapping[str, Any], description: str
) -> None:
    expected = int(spec["row_count"])
    if len(rows) != expected:
        raise MaterializationError(
            f"{description}行数不一致：期望 {expected}，实际 {len(rows)}"
        )


def _read_identity_view(
    path: Path, spec: Mapping[str, Any], description: str
) -> list[dict[str, Any]]:
    table = pq.read_table(path, columns=["sample_id", "stable_order"])
    rows = table.to_pylist()
    _validate_row_count(rows, spec, description)
    sample_ids = [str(row["sample_id"]) for row in rows]
    stable_orders = [int(row["stable_order"]) for row in rows]
    if len(set(sample_ids)) != len(sample_ids):
        raise MaterializationError(f"{description}含重复 sample_id")
    if len(set(stable_orders)) != len(stable_orders):
        raise MaterializationError(f"{description}含重复 stable_order")
    if stable_orders != sorted(stable_orders):
        raise MaterializationError(f"{description}未按 stable_order 排序")
    actual_order_sha256 = _sample_order_sha256(sample_ids)
    expected_order_sha256 = str(spec["sample_order_sha256"])
    if actual_order_sha256 != expected_order_sha256:
        raise MaterializationError(
            f"{description}样本顺序哈希不一致：期望 {expected_order_sha256}，实际 {actual_order_sha256}"
        )
    return [
        {"sample_id": sample_id, "source_stable_order": stable_order}
        for sample_id, stable_order in zip(sample_ids, stable_orders, strict=True)
    ]


def _read_supervision_view(
    path: Path,
    identity_rows: Sequence[Mapping[str, Any]],
    description: str,
) -> list[dict[str, Any]]:
    table = pq.read_table(path, columns=["sample_id", "stable_order", "text", "label"])
    rows = table.to_pylist()
    identities = [
        (str(row["sample_id"]), int(row["source_stable_order"]))
        for row in identity_rows
    ]
    actual_identities = [
        (str(row["sample_id"]), int(row["stable_order"])) for row in rows
    ]
    if actual_identities != identities:
        raise MaterializationError(f"{description}监督视图与预先锁定的身份顺序不一致")
    output: list[dict[str, Any]] = []
    for row in rows:
        label = int(row["label"])
        if label not in {0, 1}:
            raise MaterializationError(f"{description}二分类标签不是 0/1")
        text = row["text"]
        if not isinstance(text, str) or not text:
            raise MaterializationError(f"{description}含空文本")
        output.append(
            {
                "sample_id": str(row["sample_id"]),
                "source_stable_order": int(row["stable_order"]),
                "text": text,
                "binary_label": label,
            }
        )
    return output


def _validation_ids(
    path: Path, spec: Mapping[str, Any], source: str
) -> list[str]:
    rows = _load_jsonl(path)
    _validate_row_count(rows, spec, f"{source} 冻结开发清单")
    sample_ids: list[str] = []
    for row in rows:
        if row.get("split_id") != "validation":
            raise MaterializationError(f"{source} 冻结开发清单出现非 validation 行")
        sample_ids.append(str(row["sample_id"]))
    if len(set(sample_ids)) != len(sample_ids):
        raise MaterializationError(f"{source} 冻结开发清单含重复 sample_id")
    return sample_ids


def _group_mapping(
    samples_path: Path,
    group_key: str,
    validation_ids: Sequence[str],
    source: str,
) -> dict[str, str]:
    selected_ids = set(validation_ids)
    table = pq.read_table(samples_path, columns=["sample_id", group_key])
    table = table.filter(
        pc.is_in(table["sample_id"], value_set=pa.array(sorted(selected_ids)))
    )
    mapping: dict[str, str] = {}
    for row in table.to_pylist():
        sample_id = str(row["sample_id"])
        if sample_id in mapping:
            raise MaterializationError(f"{source} samples 含重复开发 sample_id")
        raw_group_id = row[group_key]
        if raw_group_id is None or not str(raw_group_id):
            raise MaterializationError(f"{source} samples 含空分组键")
        mapping[sample_id] = str(raw_group_id)
    if set(mapping) != selected_ids:
        missing = len(selected_ids.difference(mapping))
        extra = len(set(mapping).difference(selected_ids))
        raise MaterializationError(
            f"{source} 分组映射不完整：缺失 {missing}，额外 {extra}"
        )
    return mapping


def _partition_source_groups(
    *,
    source: str,
    identity_rows: Sequence[Mapping[str, Any]],
    validation_ids: Sequence[str],
    group_by_sample: Mapping[str, str],
    seed: int,
    tie_hash_namespace: str,
    group_hash_namespace: str,
) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, Any]]:
    ordered_ids = [str(row["sample_id"]) for row in identity_rows]
    if set(ordered_ids) != set(validation_ids):
        raise MaterializationError(f"{source} BERT 视图与冻结开发清单成员不一致")

    group_counts = Counter(group_by_sample[sample_id] for sample_id in ordered_ids)

    def tie_hash(group_id: str) -> str:
        payload = f"{tie_hash_namespace}\0{seed}\0{source}\0{group_id}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    ordered_groups = sorted(
        group_counts,
        key=lambda group_id: (-group_counts[group_id], tie_hash(group_id)),
    )
    group_split: dict[str, str] = {}
    row_counts = {"calibration": 0, "validation": 0}
    group_counts_by_split = {"calibration": 0, "validation": 0}
    audit_rows: list[dict[str, Any]] = []
    for group_id in ordered_groups:
        split_id = (
            "calibration"
            if row_counts["calibration"] <= row_counts["validation"]
            else "validation"
        )
        group_split[group_id] = split_id
        row_count = int(group_counts[group_id])
        row_counts[split_id] += row_count
        group_counts_by_split[split_id] += 1
        group_sha256 = hashlib.sha256(
            f"{group_hash_namespace}\0{source}\0{group_id}".encode("utf-8")
        ).hexdigest()
        audit_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "source_dataset": source,
                "group_id_sha256": group_sha256,
                "tie_break_sha256": tie_hash(group_id),
                "row_count": row_count,
                "split_id": split_id,
                "final_test_visible": False,
            }
        )

    sample_split = {
        sample_id: group_split[group_by_sample[sample_id]]
        for sample_id in ordered_ids
    }
    if dict(Counter(sample_split.values())) != row_counts:
        raise MaterializationError(f"{source} 分组贪心计数与样本分配不一致")
    summary = {
        "input_rows": len(ordered_ids),
        "group_count": len(group_counts),
        "rows_by_split": row_counts,
        "groups_by_split": group_counts_by_split,
        "absolute_row_imbalance": abs(
            row_counts["calibration"] - row_counts["validation"]
        ),
    }
    return sample_split, audit_rows, summary


def _detection_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("sample_id", pa.string(), nullable=False),
            pa.field("stable_order", pa.int64(), nullable=False),
            pa.field("source_stable_order", pa.int64(), nullable=False),
            pa.field("split_id", pa.string(), nullable=False),
            pa.field("text", pa.string(), nullable=False),
            pa.field("binary_label", pa.int8(), nullable=False),
            pa.field("source_dataset", pa.string(), nullable=False),
            pa.field("final_test_visible", pa.bool_(), nullable=False),
        ]
    )


def _train_detection_rows(
    allowlist_rows: Sequence[Mapping[str, Any]],
    supervision_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    allowlist_by_id: dict[str, Mapping[str, Any]] = {}
    for row in allowlist_rows:
        sample_id = str(row["sample_id"])
        if sample_id in allowlist_by_id:
            raise MaterializationError("训练候选清单含重复 sample_id")
        if row.get("split_id") != "train-fit" or row.get("final_test_visible") is not False:
            raise MaterializationError("训练候选清单违反 split 或最终测试可见性合同")
        if row.get("source_dataset") not in SOURCES:
            raise MaterializationError("训练候选清单含未知来源")
        allowlist_by_id[sample_id] = row

    supervision_by_id = {
        str(row["sample_id"]): row for row in supervision_rows
    }
    if not set(allowlist_by_id).issubset(supervision_by_id):
        raise MaterializationError("训练候选未完全命中冻结 BERT 视图")
    output: list[dict[str, Any]] = []
    for supervision in supervision_rows:
        sample_id = str(supervision["sample_id"])
        if sample_id not in allowlist_by_id:
            continue
        allowlist = allowlist_by_id[sample_id]
        source_stable_order = int(supervision["source_stable_order"])
        if int(allowlist["stable_order"]) != source_stable_order:
            raise MaterializationError("训练候选 stable_order 与冻结 BERT 视图不一致")
        output.append(
            {
                "sample_id": sample_id,
                "stable_order": source_stable_order,
                "source_stable_order": source_stable_order,
                "split_id": "train-fit",
                "text": str(supervision["text"]),
                "binary_label": int(supervision["binary_label"]),
                "source_dataset": str(allowlist["source_dataset"]),
                "final_test_visible": False,
            }
        )
    if len(output) != len(allowlist_rows):
        raise MaterializationError("训练检测视图行数与候选清单不一致")
    if [int(row["stable_order"]) for row in output] != sorted(
        int(row["stable_order"]) for row in output
    ):
        raise MaterializationError("训练检测视图未保留冻结 stable_order")
    return output


def _development_detection_rows(
    supervision_by_source: Mapping[str, Sequence[Mapping[str, Any]]],
    assignment_by_source: Mapping[str, Mapping[str, str]],
) -> dict[str, list[dict[str, Any]]]:
    output = {split_id: [] for split_id in SPLITS}
    for source in SOURCES:
        for supervision in supervision_by_source[source]:
            sample_id = str(supervision["sample_id"])
            split_id = assignment_by_source[source][sample_id]
            split_rows = output[split_id]
            split_rows.append(
                {
                    "sample_id": sample_id,
                    "stable_order": len(split_rows),
                    "source_stable_order": int(
                        supervision["source_stable_order"]
                    ),
                    "split_id": split_id,
                    "text": str(supervision["text"]),
                    "binary_label": int(supervision["binary_label"]),
                    "source_dataset": source,
                    "final_test_visible": False,
                }
            )
    return output


def _assignment_rows(
    identity_by_source: Mapping[str, Sequence[Mapping[str, Any]]],
    assignment_by_source: Mapping[str, Mapping[str, str]],
    group_by_source: Mapping[str, Mapping[str, str]],
    group_hash_namespace: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source in SOURCES:
        for identity in identity_by_source[source]:
            sample_id = str(identity["sample_id"])
            group_id = group_by_source[source][sample_id]
            output.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "sample_id": sample_id,
                    "source_dataset": source,
                    "source_stable_order": int(identity["source_stable_order"]),
                    "group_id_sha256": hashlib.sha256(
                        f"{group_hash_namespace}\0{source}\0{group_id}".encode(
                            "utf-8"
                        )
                    ).hexdigest(),
                    "split_id": assignment_by_source[source][sample_id],
                    "assignment_uses_label": False,
                    "final_test_visible": False,
                }
            )
    return output


def _load_route_truth(
    development_rows: Sequence[Mapping[str, Any]],
    genis_archive: Path,
    tqhc2_protocol_path: Path,
) -> dict[str, tuple[str, str, bool]]:
    by_id = {str(row["sample_id"]): row for row in development_rows}
    if len(by_id) != len(development_rows):
        raise MaterializationError("开发检测视图跨分区含重复 sample_id")
    genis_ids = {
        sample_id
        for sample_id, row in by_id.items()
        if row["source_dataset"] == "genis"
    }
    tqhc2_ids = {
        sample_id
        for sample_id, row in by_id.items()
        if row["source_dataset"] == "tqhc2"
    }
    truth: dict[str, tuple[str, str, bool]] = {}

    table = pq.read_table(
        tqhc2_protocol_path,
        columns=[
            "sample_id",
            "transport_family",
            "transport_family_observed",
            "protocol_target",
        ],
    )
    filtered = table.filter(
        pc.is_in(table["sample_id"], value_set=pa.array(sorted(tqhc2_ids)))
    )
    for row in filtered.to_pylist():
        sample_id = str(row["sample_id"])
        if sample_id in truth:
            raise MaterializationError("TQH 开发路由记录重复")
        truth[sample_id] = (
            _normalise_transport(str(row["transport_family"])),
            _normalise_transport(str(row["protocol_target"])),
            bool(row["transport_family_observed"]),
        )
    if set(truth) != tqhc2_ids:
        raise MaterializationError(
            f"TQH 开发路由缺失 {len(tqhc2_ids.difference(truth))} 条"
        )

    found_genis: set[str] = set()
    with ZipFile(genis_archive) as archive:
        members = sorted(
            name
            for name in archive.namelist()
            if "/flows-10-sec/" in name and name.endswith(".csv")
        )
        if len(members) != 11:
            raise MaterializationError("GeNIS 10 秒 CSV 成员数不是 11")
        for member in members:
            basename = Path(member).name
            with archive.open(member) as raw_handle:
                text_handle = io.TextIOWrapper(
                    raw_handle, encoding="utf-8-sig", newline=""
                )
                reader = csv.reader(text_handle)
                header = next(reader)
                try:
                    proto_index = header.index("Proto")
                except ValueError as error:
                    raise MaterializationError("GeNIS CSV 缺少 Proto") from error
                for row_number, values in enumerate(reader, start=1):
                    sample_id = _genis_candidate_id(basename, row_number)
                    if sample_id not in genis_ids:
                        continue
                    if sample_id in found_genis:
                        raise MaterializationError("GeNIS 开发路由记录重复")
                    found_genis.add(sample_id)
                    transport = _normalise_transport(values[proto_index])
                    protocol_target = (
                        transport if transport in {"TCP", "UDP"} else "UNKNOWN"
                    )
                    truth[sample_id] = (
                        transport,
                        protocol_target,
                        transport != "UNKNOWN",
                    )
    if found_genis != genis_ids:
        raise MaterializationError(
            f"GeNIS 开发路由缺失 {len(genis_ids.difference(found_genis))} 条"
        )
    if set(truth) != set(by_id):
        raise MaterializationError("开发路由真值未覆盖全部样本")
    return truth


def _route_rows(
    detection_rows: Sequence[Mapping[str, Any]],
    route_truth: Mapping[str, tuple[str, str, bool]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for detection in detection_rows:
        transport, protocol_target, observed = route_truth[str(detection["sample_id"])]
        output.append(
            _route_record(
                detection,
                transport_family=transport,
                protocol_target=protocol_target,
                observed=observed,
            )
        )
    if len(output) != len(detection_rows):
        raise MaterializationError("开发路由行数不正确")
    return output


def _load_packet_groups(
    sample_ids: Sequence[str], packet_path: Path
) -> tuple[dict[str, list[tuple[int, int, int]]], int]:
    selected_ids = set(sample_ids)
    table = pq.read_table(
        packet_path,
        columns=[
            "sample_id",
            "packet_index",
            "delta_time_us",
            "network_length_bytes",
        ],
    )
    table = table.filter(
        pc.is_in(table["sample_id"], value_set=pa.array(sorted(selected_ids)))
    ).sort_by((("sample_id", "ascending"), ("packet_index", "ascending")))
    groups: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for row in table.to_pylist():
        groups[str(row["sample_id"])].append(
            (
                int(row["packet_index"]),
                int(row["delta_time_us"]),
                int(row["network_length_bytes"]),
            )
        )
    if set(groups) != selected_ids:
        raise MaterializationError(
            f"TQH 开发包历史缺失 {len(selected_ids.difference(groups))} 条"
        )
    for sample_id, packets in groups.items():
        indexes = [packet[0] for packet in packets]
        if indexes != list(range(len(indexes))):
            raise MaterializationError(f"TQH packet_index 不连续：{sample_id}")
        if any(packet[1] < 0 or packet[2] < 0 for packet in packets):
            raise MaterializationError(f"TQH 包历史出现负值：{sample_id}")
    return dict(groups), table.num_rows


def _history_rows(
    detection_rows: Sequence[Mapping[str, Any]],
    packet_groups: Mapping[str, Sequence[tuple[int, int, int]]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for detection in detection_rows:
        if detection["source_dataset"] == "genis":
            output.extend(_empty_history_row(detection, index) for index in range(4))
            continue
        packets = packet_groups[str(detection["sample_id"])]
        count = len(packets)
        bounds = (
            (0, min(2, count)),
            (2, min(4, count)),
            (4, min(8, count)),
            (8, count),
        )
        for window_index, (start, stop) in enumerate(bounds):
            output.append(
                _window_history_row(
                    detection,
                    window_index,
                    packets,
                    min(start, count),
                    min(stop, count),
                )
            )
    if len(output) != len(detection_rows) * 4:
        raise MaterializationError("开发共同历史行数不正确")
    actual_order = [
        (str(row["sample_id"]), int(row["window_index"])) for row in output
    ]
    expected_order = [
        (str(row["sample_id"]), window_index)
        for row in detection_rows
        for window_index in range(4)
    ]
    if actual_order != expected_order:
        raise MaterializationError("开发共同历史顺序不稳定")
    return output


def _write_parquet_artifact(
    partial_root: Path,
    filename: str,
    rows: list[dict[str, Any]],
    schema: pa.Schema,
) -> tuple[Path, dict[str, Any]]:
    path = partial_root / filename
    _write_parquet(path, rows, schema)
    semantic_sha256 = _semantic_sha256(rows)
    return path, _artifact_entry(
        path,
        partial_root,
        row_count=len(rows),
        schema_sha256=_schema_sha256(schema),
        semantic_sha256=semantic_sha256,
    )


def materialize(config_path: Path, project_root: Path) -> Path:
    project_root = project_root.resolve()
    config_path = config_path.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise MaterializationError("配置顶层不是对象")
    if config.get("schema_version") != (
        "flow_probe_r2_final_development_views_materialization_v1"
    ):
        raise MaterializationError("配置模式版本不正确")
    if config.get("final_test_visible") is not False:
        raise MaterializationError("最终测试可见性必须为 false")

    input_specs = {
        name: dict(raw_spec) for name, raw_spec in dict(config["inputs"]).items()
    }
    input_paths = {
        name: _resolve_input(project_root, spec)
        for name, spec in input_specs.items()
    }
    for name, path in input_paths.items():
        _validate_input(path, str(input_specs[name]["sha256"]))

    split_contract = yaml.safe_load(
        input_paths["split_contract"].read_text(encoding="utf-8")
    )
    if split_contract.get("final_test_visible") is not False:
        raise MaterializationError("开发拆分合同暴露最终测试")
    if int(split_contract["group_partition"]["seed"]) != int(
        config["group_partition"]["seed"]
    ):
        raise MaterializationError("开发拆分合同与物化配置种子不一致")

    output_relative = Path(str(config["output_root"]))
    if output_relative.is_absolute() or ".." in output_relative.parts:
        raise MaterializationError("输出逻辑路径不合法")
    output_root = project_root / output_relative
    partial_root = output_root.with_name(f"{output_root.name}.partial")
    if output_root.exists() or partial_root.exists():
        raise MaterializationError("输出根或阶段根已存在，拒绝覆盖")
    partial_root.mkdir(parents=True)

    source_lock = {
        "schema_version": "flow_probe_r2_final_development_source_lock_v1",
        "config_sha256": _sha256_file(config_path),
        "materializer_sha256": _sha256_file(Path(__file__).resolve()),
        "helper_script_sha256": _sha256_file(input_paths["helper_script"]),
        "final_test_visible": False,
        "inputs": [
            {
                "role": name,
                "logical_path": str(input_specs[name]["path"]),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
            for name, path in sorted(input_paths.items())
        ],
    }
    contract_path = partial_root / "materialization-contract.json"
    contract_semantic = _write_json(contract_path, config)
    source_lock_path = partial_root / "source-lock.json"
    source_lock_semantic = _write_json(source_lock_path, source_lock)
    run_state_path = partial_root / "run-state.json"
    _atomic_write_json(
        run_state_path,
        {
            "schema_version": SCHEMA_VERSION,
            "status": "prepared",
            "final_test_visible": False,
        },
    )

    try:
        _atomic_write_json(
            run_state_path,
            {
                "schema_version": SCHEMA_VERSION,
                "status": "running",
                "final_test_visible": False,
            },
        )

        train_allowlist = _load_jsonl(input_paths["train_allowlist"])
        _validate_row_count(
            train_allowlist, input_specs["train_allowlist"], "训练候选清单"
        )
        train_identity = _read_identity_view(
            input_paths["train_bert"], input_specs["train_bert"], "训练 BERT 视图"
        )
        train_supervision = _read_supervision_view(
            input_paths["train_bert"], train_identity, "训练 BERT 视图"
        )
        train_detection = _train_detection_rows(train_allowlist, train_supervision)

        identity_by_source: dict[str, list[dict[str, Any]]] = {}
        validation_ids_by_source: dict[str, list[str]] = {}
        group_by_source: dict[str, dict[str, str]] = {}
        assignment_by_source: dict[str, dict[str, str]] = {}
        group_audit_rows: list[dict[str, Any]] = []
        partition_summary: dict[str, dict[str, Any]] = {}
        partition_config = dict(config["group_partition"])

        for source in SOURCES:
            identity_by_source[source] = _read_identity_view(
                input_paths[f"{source}_bert"],
                input_specs[f"{source}_bert"],
                f"{source} 开发 BERT 视图",
            )
            validation_ids_by_source[source] = _validation_ids(
                input_paths[f"{source}_validation_manifest"],
                input_specs[f"{source}_validation_manifest"],
                source,
            )
            group_key = str(input_specs[f"{source}_samples"]["group_key"])
            group_by_source[source] = _group_mapping(
                input_paths[f"{source}_samples"],
                group_key,
                validation_ids_by_source[source],
                source,
            )
            assignments, audit_rows, source_summary = _partition_source_groups(
                source=source,
                identity_rows=identity_by_source[source],
                validation_ids=validation_ids_by_source[source],
                group_by_sample=group_by_source[source],
                seed=int(partition_config["seed"]),
                tie_hash_namespace=str(partition_config["tie_hash_namespace"]),
                group_hash_namespace=str(partition_config["group_hash_namespace"]),
            )
            assignment_by_source[source] = assignments
            group_audit_rows.extend(audit_rows)
            partition_summary[source] = source_summary

        # 分组分配锁定后才读取文本与标签，防止标签参与拆分。
        supervision_by_source = {
            source: _read_supervision_view(
                input_paths[f"{source}_bert"],
                identity_by_source[source],
                f"{source} 开发 BERT 视图",
            )
            for source in SOURCES
        }
        development_detection = _development_detection_rows(
            supervision_by_source, assignment_by_source
        )
        assignment_rows = _assignment_rows(
            identity_by_source,
            assignment_by_source,
            group_by_source,
            str(partition_config["group_hash_namespace"]),
        )

        all_development_rows = [
            row
            for split_id in SPLITS
            for row in development_detection[split_id]
        ]
        train_ids = {str(row["sample_id"]) for row in train_detection}
        development_ids = {
            str(row["sample_id"]) for row in all_development_rows
        }
        if train_ids.intersection(development_ids):
            raise MaterializationError("训练与开发校准/验证出现样本交叉")
        if len(development_ids) != int(config["expected"]["development_rows"]):
            raise MaterializationError("开发检测视图总样本数不正确")
        calibration_ids = {
            str(row["sample_id"])
            for row in development_detection["calibration"]
        }
        validation_ids = {
            str(row["sample_id"])
            for row in development_detection["validation"]
        }
        if calibration_ids.intersection(validation_ids):
            raise MaterializationError("校准与开发验证出现样本交叉")

        route_truth = _load_route_truth(
            all_development_rows,
            input_paths["genis_flows"],
            input_paths["tqhc2_protocol"],
        )
        route_by_split = {
            split_id: _route_rows(development_detection[split_id], route_truth)
            for split_id in SPLITS
        }
        tqhc2_development_ids = [
            str(row["sample_id"])
            for row in all_development_rows
            if row["source_dataset"] == "tqhc2"
        ]
        packet_groups, selected_packet_rows = _load_packet_groups(
            tqhc2_development_ids, input_paths["tqhc2_packets"]
        )
        history_by_split = {
            split_id: _history_rows(
                development_detection[split_id], packet_groups
            )
            for split_id in SPLITS
        }

        detection_schema = _detection_schema()
        route_schema = _route_schema()
        history_schema = _history_schema()
        artifacts: list[dict[str, Any]] = []

        _, artifact = _write_parquet_artifact(
            partial_root,
            "detection-view-train-fit.parquet",
            train_detection,
            detection_schema,
        )
        artifacts.append(artifact)
        for split_id, filename in (
            ("calibration", "detection-view-calibration.parquet"),
            ("validation", "detection-view-development-validation.parquet"),
        ):
            _, artifact = _write_parquet_artifact(
                partial_root,
                filename,
                development_detection[split_id],
                detection_schema,
            )
            artifacts.append(artifact)
        for split_id, filename in (
            ("calibration", "common-history-calibration.parquet"),
            ("validation", "common-history-development-validation.parquet"),
        ):
            _, artifact = _write_parquet_artifact(
                partial_root,
                filename,
                history_by_split[split_id],
                history_schema,
            )
            artifacts.append(artifact)
        for split_id, filename in (
            ("calibration", "route-assignments-calibration.parquet"),
            ("validation", "route-assignments-development-validation.parquet"),
        ):
            _, artifact = _write_parquet_artifact(
                partial_root,
                filename,
                route_by_split[split_id],
                route_schema,
            )
            artifacts.append(artifact)

        assignments_path = partial_root / "development-split-assignments.jsonl"
        assignments_semantic = _write_jsonl(assignments_path, assignment_rows)
        artifacts.append(
            _artifact_entry(
                assignments_path,
                partial_root,
                row_count=len(assignment_rows),
                schema_sha256=None,
                semantic_sha256=assignments_semantic,
            )
        )
        group_audit_path = partial_root / "development-group-audit.jsonl"
        group_audit_semantic = _write_jsonl(group_audit_path, group_audit_rows)
        artifacts.append(
            _artifact_entry(
                group_audit_path,
                partial_root,
                row_count=len(group_audit_rows),
                schema_sha256=None,
                semantic_sha256=group_audit_semantic,
            )
        )

        route_counts = {
            split_id: dict(
                sorted(Counter(row["route_id"] for row in rows).items())
            )
            for split_id, rows in route_by_split.items()
        }
        summary = {
            "schema_version": "flow_probe_r2_final_development_summary_v1",
            "dataset_version": config["dataset_version"],
            "stage": config["stage"],
            "status": config["status"],
            "final_test_visible": False,
            "train_fit": {
                "rows": len(train_detection),
                "source_counts": dict(
                    sorted(Counter(row["source_dataset"] for row in train_detection).items())
                ),
                "stable_order_min": min(row["stable_order"] for row in train_detection),
                "stable_order_max": max(row["stable_order"] for row in train_detection),
                "stable_order_contiguous": False,
            },
            "development_partition": partition_summary,
            "development_rows_by_split": {
                split_id: len(rows)
                for split_id, rows in development_detection.items()
            },
            "development_source_rows_by_split": {
                split_id: dict(
                    sorted(Counter(row["source_dataset"] for row in rows).items())
                )
                for split_id, rows in development_detection.items()
            },
            "development_label_counts_by_split": {
                split_id: {
                    str(label): count
                    for label, count in sorted(
                        Counter(row["binary_label"] for row in rows).items()
                    )
                }
                for split_id, rows in development_detection.items()
            },
            "routes_by_split": route_counts,
            "history_rows_by_split": {
                split_id: len(rows) for split_id, rows in history_by_split.items()
            },
            "tqhc2_selected_packet_rows": selected_packet_rows,
            "audits": {
                "train_development_sample_overlap": 0,
                "calibration_validation_sample_overlap": 0,
                "calibration_validation_group_overlap": 0,
                "assignment_uses_label": False,
                "final_test_visible": False,
                "quic_formal_training_enabled": False,
            },
        }
        summary_path = partial_root / "input-summary.json"
        summary_semantic = _write_json(summary_path, summary)
        artifacts.append(
            _artifact_entry(
                summary_path,
                partial_root,
                row_count=None,
                schema_sha256=None,
                semantic_sha256=summary_semantic,
            )
        )

        schema_document = {
            "schema_version": "flow_probe_r2_final_development_schema_v1",
            "detection": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in detection_schema
            ],
            "common_history": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in history_schema
            ],
            "route_assignments": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in route_schema
            ],
            "ordering": {
                "train_detection": ["stable_order"],
                "development_detection": ["stable_order"],
                "common_history": ["stable_order", "window_index"],
                "route_assignments": ["stable_order"],
            },
        }
        schema_path = partial_root / "schema.json"
        schema_semantic = _write_json(schema_path, schema_document)
        artifacts.append(
            _artifact_entry(
                schema_path,
                partial_root,
                row_count=None,
                schema_sha256=None,
                semantic_sha256=schema_semantic,
            )
        )
        artifacts.extend(
            [
                _artifact_entry(
                    contract_path,
                    partial_root,
                    row_count=None,
                    schema_sha256=None,
                    semantic_sha256=contract_semantic,
                ),
                _artifact_entry(
                    source_lock_path,
                    partial_root,
                    row_count=None,
                    schema_sha256=None,
                    semantic_sha256=source_lock_semantic,
                ),
            ]
        )

        _atomic_write_json(
            run_state_path,
            {
                "schema_version": SCHEMA_VERSION,
                "status": "finished",
                "final_test_visible": False,
            },
        )
        run_state_semantic = _semantic_sha256(
            [
                {
                    "schema_version": SCHEMA_VERSION,
                    "status": "finished",
                    "final_test_visible": False,
                }
            ]
        )
        artifacts.append(
            _artifact_entry(
                run_state_path,
                partial_root,
                row_count=None,
                schema_sha256=None,
                semantic_sha256=run_state_semantic,
            )
        )
        artifacts.sort(key=lambda item: str(item["relative_path"]))
        manifest = {
            "schema_version": "flow_probe_r2_final_development_artifact_manifest_v1",
            "dataset_version": config["dataset_version"],
            "stage": config["stage"],
            "status": config["status"],
            "final_test_visible": False,
            "artifacts": artifacts,
            "artifact_payload_merkle_sha256": hashlib.sha256(
                _canonical_json(artifacts).encode("utf-8")
            ).hexdigest(),
        }
        _write_json(partial_root / "artifact-manifest.json", manifest)
        os.rename(partial_root, output_root)
        return output_root
    except BaseException:
        try:
            _atomic_write_json(
                run_state_path,
                {
                    "schema_version": SCHEMA_VERSION,
                    "status": "failed",
                    "final_test_visible": False,
                },
            )
        except BaseException:
            pass
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, required=True)
    arguments = parser.parse_args()
    output = materialize(arguments.config, arguments.project_root)
    print(output)


if __name__ == "__main__":
    main()
