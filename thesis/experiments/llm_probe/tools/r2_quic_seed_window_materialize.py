#!/usr/bin/env python3
"""将通过审计的 QUIC qlog 物化为零权重的固定因果窗种子真值。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Sequence

import pyarrow as pa
import pyarrow.parquet as pq
import yaml


class MaterializationError(RuntimeError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
                raise MaterializationError(f"JSONL 末行缺少换行：{path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise MaterializationError(f"JSONL 行不是对象：{path}:{line_number}")
            rows.append(value)
    return rows


def _resolve_input(
    item: Mapping[str, Any], project_root: Path, repository_root: Path
) -> Path:
    roots = {"project": project_root, "repository": repository_root}
    root_name = str(item["root"])
    if root_name not in roots:
        raise MaterializationError(f"未知输入根：{root_name}")
    path = (roots[root_name] / str(item["path"])).resolve()
    expected_root = roots[root_name].resolve()
    if path != expected_root and expected_root not in path.parents:
        raise MaterializationError(f"输入路径越界：{path}")
    return path


def _validate_file(path: Path, expected_sha256: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise MaterializationError(f"输入不是普通文件：{path}")
    actual = _sha256_file(path)
    if actual != expected_sha256:
        raise MaterializationError(
            f"输入哈希不一致：{path}，期望 {expected_sha256}，实际 {actual}"
        )


def _milliseconds_to_nanoseconds(value: object, field: str) -> int:
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
        scaled = decimal_value * Decimal(1_000_000)
    except (InvalidOperation, ValueError) as error:
        raise MaterializationError(f"{field} 不是合法十进制毫秒值：{value}") from error
    integral = scaled.to_integral_value()
    if scaled != integral:
        raise MaterializationError(f"{field} 无法无损转换为整数纳秒：{value}")
    result = int(integral)
    if result < 0:
        raise MaterializationError(f"{field} 不得为负数：{value}")
    return result


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool):
        raise MaterializationError(f"{field} 不得为布尔值")
    try:
        result = int(value)
    except (TypeError, ValueError) as error:
        raise MaterializationError(f"{field} 不是整数：{value}") from error
    if str(result) != str(value) and not isinstance(value, int):
        raise MaterializationError(f"{field} 不是无损整数：{value}")
    if result < 0:
        raise MaterializationError(f"{field} 不得为负数：{value}")
    return result


def _schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("trace_id", pa.string(), nullable=False),
            pa.field("connection_stable_order", pa.int32(), nullable=False),
            pa.field("physics_group_sha256", pa.string(), nullable=False),
            pa.field("source_qlog_sha256", pa.string(), nullable=False),
            pa.field("split_id", pa.string(), nullable=False),
            pa.field("transport_family", pa.string(), nullable=False),
            pa.field("effective_route_id", pa.string(), nullable=False),
            pa.field("window_index", pa.int32(), nullable=False),
            pa.field("window_start_offset_ns", pa.int64(), nullable=False),
            pa.field("window_end_offset_ns", pa.int64(), nullable=False),
            pa.field("window_duration_ns", pa.int64(), nullable=False),
            pa.field("window_valid", pa.bool_(), nullable=False),
            pa.field("public_history_available", pa.bool_(), nullable=False),
            pa.field("public_packet_count", pa.int64(), nullable=False),
            pa.field("public_byte_count", pa.int64(), nullable=False),
            pa.field("public_sent_packet_count", pa.int64(), nullable=False),
            pa.field("public_sent_byte_count", pa.int64(), nullable=False),
            pa.field("public_received_packet_count", pa.int64(), nullable=False),
            pa.field("public_received_byte_count", pa.int64(), nullable=False),
            pa.field("public_packet_length_mean_bytes", pa.float64(), nullable=True),
            pa.field("public_packet_length_mean_missing", pa.bool_(), nullable=False),
            pa.field("public_iat_mean_ms", pa.float64(), nullable=True),
            pa.field("public_iat_mean_missing", pa.bool_(), nullable=False),
            pa.field("public_packet_rate_pps", pa.float64(), nullable=False),
            pa.field("public_byte_rate_Bps", pa.float64(), nullable=False),
            pa.field("truth_quic_rtt_applicable", pa.bool_(), nullable=False),
            pa.field("truth_quic_rtt_observed", pa.bool_(), nullable=False),
            pa.field("truth_quic_latest_rtt_ns", pa.int64(), nullable=True),
            pa.field("truth_quic_min_rtt_ns", pa.int64(), nullable=True),
            pa.field("truth_quic_smoothed_rtt_ns", pa.int64(), nullable=True),
            pa.field(
                "truth_quic_bytes_in_flight_applicable", pa.bool_(), nullable=False
            ),
            pa.field(
                "truth_quic_bytes_in_flight_observed", pa.bool_(), nullable=False
            ),
            pa.field("truth_quic_bytes_in_flight_bytes", pa.int64(), nullable=True),
            pa.field(
                "truth_quic_congestion_window_applicable", pa.bool_(), nullable=False
            ),
            pa.field(
                "truth_quic_congestion_window_observed", pa.bool_(), nullable=False
            ),
            pa.field("truth_quic_congestion_window_bytes", pa.int64(), nullable=True),
            pa.field("truth_quic_metrics_events_in_window", pa.int32(), nullable=False),
            pa.field("truth_quic_state_age_ns", pa.int64(), nullable=True),
            pa.field(
                "truth_quic_endpoint_loss_applicable", pa.bool_(), nullable=False
            ),
            pa.field("truth_quic_endpoint_loss_observed", pa.bool_(), nullable=False),
            pa.field(
                "truth_quic_endpoint_packet_lost_count", pa.int32(), nullable=False
            ),
            pa.field("truth_quic_pto_applicable", pa.bool_(), nullable=False),
            pa.field("truth_quic_pto_observed", pa.bool_(), nullable=False),
            pa.field("truth_quic_pto_event_count", pa.int32(), nullable=True),
            pa.field("qlog_truth_available", pa.bool_(), nullable=False),
            pa.field("seed_validation_only", pa.bool_(), nullable=False),
            pa.field("formal_training_weight", pa.float32(), nullable=False),
            pa.field("quic_formal_training_enabled", pa.bool_(), nullable=False),
            pa.field("quic_model_applicable", pa.bool_(), nullable=False),
            pa.field("quic_expert_ready", pa.bool_(), nullable=False),
            pa.field("stop_gradient_route", pa.bool_(), nullable=False),
            pa.field("final_test_visible", pa.bool_(), nullable=False),
        ]
    )


def _schema_document(schema: pa.Schema) -> list[dict[str, Any]]:
    return [
        {"name": field.name, "type": str(field.type), "nullable": field.nullable}
        for field in schema
    ]


def _schema_sha256(schema: pa.Schema) -> str:
    return _sha256_bytes(_canonical_json(_schema_document(schema)).encode("utf-8"))


def _load_qlog(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle, parse_float=Decimal)
    if not isinstance(value, dict):
        raise MaterializationError(f"qlog 顶层不是对象：{path}")
    return value


def _materialize_trace(
    manifest_row: Mapping[str, Any],
    connection_stable_order: int,
    raw_root: Path,
    window_ns: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, int]]:
    canonical_path = str(manifest_row["canonical_path"])
    qlog_path = (raw_root / canonical_path).resolve()
    if raw_root.resolve() not in qlog_path.parents:
        raise MaterializationError(f"qlog 路径越界：{qlog_path}")
    expected_sha = str(manifest_row["content_sha256"])
    _validate_file(qlog_path, expected_sha)

    qlog = _load_qlog(qlog_path)
    if qlog.get("qlog_version") != "draft-02-wip":
        raise MaterializationError(f"qlog 版本不符合合同：{qlog_path}")
    traces = qlog.get("traces")
    if not isinstance(traces, list) or len(traces) != 1:
        raise MaterializationError(f"qlog 必须且只能含一条轨迹：{qlog_path}")
    trace = traces[0]
    if not isinstance(trace, dict):
        raise MaterializationError(f"qlog 轨迹不是对象：{qlog_path}")
    vantage = trace.get("vantage_point")
    if not isinstance(vantage, dict) or vantage.get("type") != "server":
        raise MaterializationError(f"qlog 观察点不是服务器：{qlog_path}")
    events = trace.get("events")
    if not isinstance(events, list) or not events:
        raise MaterializationError(f"qlog 事件为空：{qlog_path}")

    first_ns = int(manifest_row["first_event_time_ns"])
    last_ns = int(manifest_row["last_event_time_ns"])
    duration_ns = int(manifest_row["duration_ns"])
    if last_ns - first_ns != duration_ns:
        raise MaterializationError(f"qlog 清单持续时间不守恒：{qlog_path}")
    full_windows = duration_ns // window_ns
    if full_windows <= 0:
        raise MaterializationError(f"qlog 不含完整固定窗：{qlog_path}")

    packet_count = [0] * full_windows
    byte_count = [0] * full_windows
    sent_packet_count = [0] * full_windows
    sent_byte_count = [0] * full_windows
    received_packet_count = [0] * full_windows
    received_byte_count = [0] * full_windows
    first_packet_time: list[int | None] = [None] * full_windows
    last_packet_time: list[int | None] = [None] * full_windows
    metric_count = [0] * full_windows
    metric_state: list[tuple[int, int, int, int, int, int] | None] = [
        None
    ] * full_windows
    loss_count = [0] * full_windows

    total_sent = 0
    total_received = 0
    total_metrics = 0
    total_loss = 0
    previous_time_ns: int | None = None
    observed_first_ns: int | None = None
    observed_last_ns: int | None = None

    for event_index, event in enumerate(events, start=1):
        if not isinstance(event, list) or len(event) != 4:
            raise MaterializationError(
                f"qlog 事件不符合四字段合同：{qlog_path}:{event_index}"
            )
        event_time_ns = _milliseconds_to_nanoseconds(
            event[0], f"event_time:{canonical_path}:{event_index}"
        )
        if previous_time_ns is not None and event_time_ns < previous_time_ns:
            raise MaterializationError(f"qlog 事件时间回退：{qlog_path}:{event_index}")
        previous_time_ns = event_time_ns
        observed_first_ns = event_time_ns if observed_first_ns is None else observed_first_ns
        observed_last_ns = event_time_ns
        offset_ns = event_time_ns - first_ns
        if offset_ns < 0:
            raise MaterializationError(f"qlog 事件早于清单起点：{qlog_path}:{event_index}")
        window_index = offset_ns // window_ns
        in_full_window = window_index < full_windows

        category = event[1]
        name = event[2]
        data = event[3]
        if not isinstance(data, dict):
            raise MaterializationError(f"qlog 事件数据不是对象：{qlog_path}:{event_index}")

        if category == "transport" and name in {"packet_sent", "packet_received"}:
            header = data.get("header")
            if not isinstance(header, dict):
                raise MaterializationError(f"qlog 包事件缺少 header：{qlog_path}:{event_index}")
            packet_size = _nonnegative_int(
                header.get("packet_size"),
                f"packet_size:{canonical_path}:{event_index}",
            )
            is_sent = name == "packet_sent"
            total_sent += int(is_sent)
            total_received += int(not is_sent)
            if in_full_window:
                index = int(window_index)
                packet_count[index] += 1
                byte_count[index] += packet_size
                if is_sent:
                    sent_packet_count[index] += 1
                    sent_byte_count[index] += packet_size
                else:
                    received_packet_count[index] += 1
                    received_byte_count[index] += packet_size
                if first_packet_time[index] is None:
                    first_packet_time[index] = event_time_ns
                last_packet_time[index] = event_time_ns
        elif category == "recovery" and name == "metrics_updated":
            total_metrics += 1
            latest_rtt_ns = _milliseconds_to_nanoseconds(
                data.get("latest_rtt"),
                f"latest_rtt:{canonical_path}:{event_index}",
            )
            min_rtt_ns = _milliseconds_to_nanoseconds(
                data.get("min_rtt"), f"min_rtt:{canonical_path}:{event_index}"
            )
            smoothed_rtt_ns = _milliseconds_to_nanoseconds(
                data.get("smoothed_rtt"),
                f"smoothed_rtt:{canonical_path}:{event_index}",
            )
            bytes_in_flight = _nonnegative_int(
                data.get("bytes_in_flight"),
                f"bytes_in_flight:{canonical_path}:{event_index}",
            )
            congestion_window = _nonnegative_int(
                data.get("congestion_window"),
                f"congestion_window:{canonical_path}:{event_index}",
            )
            if congestion_window <= 0:
                raise MaterializationError(
                    f"congestion_window 必须为正数：{qlog_path}:{event_index}"
                )
            if in_full_window:
                index = int(window_index)
                metric_count[index] += 1
                metric_state[index] = (
                    event_time_ns,
                    latest_rtt_ns,
                    min_rtt_ns,
                    smoothed_rtt_ns,
                    bytes_in_flight,
                    congestion_window,
                )
        elif category == "recovery" and name == "packet_lost":
            total_loss += 1
            if in_full_window:
                loss_count[int(window_index)] += 1

    if observed_first_ns != first_ns or observed_last_ns != last_ns:
        raise MaterializationError(f"qlog 起止时间与审计清单不一致：{qlog_path}")
    expected_counts = manifest_row["event_counts"]
    observed_counts = {
        "packet_sent": total_sent,
        "packet_received": total_received,
        "metrics_updated": total_metrics,
        "packet_lost": total_loss,
    }
    for key, actual in observed_counts.items():
        expected = int(expected_counts[key])
        if actual != expected:
            raise MaterializationError(
                f"qlog 事件计数不一致：{canonical_path}:{key}，期望 {expected}，实际 {actual}"
            )

    rows: list[dict[str, Any]] = []
    current_state: tuple[int, int, int, int, int, int] | None = None
    window_seconds = window_ns / 1_000_000_000
    for index in range(full_windows):
        if metric_state[index] is not None:
            current_state = metric_state[index]
        state_observed = current_state is not None
        count = packet_count[index]
        packet_length_mean = byte_count[index] / count if count else None
        first_packet = first_packet_time[index]
        last_packet = last_packet_time[index]
        iat_mean_ms = None
        if count >= 2 and first_packet is not None and last_packet is not None:
            iat_mean_ms = (last_packet - first_packet) / (count - 1) / 1_000_000
        window_end_offset_ns = (index + 1) * window_ns
        if current_state is None:
            latest_rtt_ns = None
            min_rtt_ns = None
            smoothed_rtt_ns = None
            bytes_in_flight = None
            congestion_window = None
            state_age_ns = None
        else:
            state_time_ns = current_state[0]
            latest_rtt_ns = current_state[1]
            min_rtt_ns = current_state[2]
            smoothed_rtt_ns = current_state[3]
            bytes_in_flight = current_state[4]
            congestion_window = current_state[5]
            state_age_ns = first_ns + window_end_offset_ns - state_time_ns
            if state_age_ns < 0:
                raise MaterializationError(f"窗末状态发生未来泄漏：{qlog_path}:{index}")
        rows.append(
            {
                "trace_id": str(manifest_row["trace_id"]),
                "connection_stable_order": connection_stable_order,
                "physics_group_sha256": str(manifest_row["group_id_sha256"]),
                "source_qlog_sha256": expected_sha,
                "split_id": "seed-validation-only",
                "transport_family": "QUIC",
                "effective_route_id": "UNKNOWN",
                "window_index": index,
                "window_start_offset_ns": index * window_ns,
                "window_end_offset_ns": window_end_offset_ns,
                "window_duration_ns": window_ns,
                "window_valid": True,
                "public_history_available": True,
                "public_packet_count": count,
                "public_byte_count": byte_count[index],
                "public_sent_packet_count": sent_packet_count[index],
                "public_sent_byte_count": sent_byte_count[index],
                "public_received_packet_count": received_packet_count[index],
                "public_received_byte_count": received_byte_count[index],
                "public_packet_length_mean_bytes": packet_length_mean,
                "public_packet_length_mean_missing": packet_length_mean is None,
                "public_iat_mean_ms": iat_mean_ms,
                "public_iat_mean_missing": iat_mean_ms is None,
                "public_packet_rate_pps": count / window_seconds,
                "public_byte_rate_Bps": byte_count[index] / window_seconds,
                "truth_quic_rtt_applicable": True,
                "truth_quic_rtt_observed": state_observed,
                "truth_quic_latest_rtt_ns": latest_rtt_ns,
                "truth_quic_min_rtt_ns": min_rtt_ns,
                "truth_quic_smoothed_rtt_ns": smoothed_rtt_ns,
                "truth_quic_bytes_in_flight_applicable": True,
                "truth_quic_bytes_in_flight_observed": state_observed,
                "truth_quic_bytes_in_flight_bytes": bytes_in_flight,
                "truth_quic_congestion_window_applicable": True,
                "truth_quic_congestion_window_observed": state_observed,
                "truth_quic_congestion_window_bytes": congestion_window,
                "truth_quic_metrics_events_in_window": metric_count[index],
                "truth_quic_state_age_ns": state_age_ns,
                "truth_quic_endpoint_loss_applicable": True,
                "truth_quic_endpoint_loss_observed": True,
                "truth_quic_endpoint_packet_lost_count": loss_count[index],
                "truth_quic_pto_applicable": True,
                "truth_quic_pto_observed": False,
                "truth_quic_pto_event_count": None,
                "qlog_truth_available": True,
                "seed_validation_only": True,
                "formal_training_weight": 0.0,
                "quic_formal_training_enabled": False,
                "quic_model_applicable": False,
                "quic_expert_ready": False,
                "stop_gradient_route": True,
                "final_test_visible": False,
            }
        )

    connection_row = {
        "trace_id": str(manifest_row["trace_id"]),
        "connection_stable_order": connection_stable_order,
        "physics_group_sha256": str(manifest_row["group_id_sha256"]),
        "canonical_path": canonical_path,
        "source_qlog_sha256": expected_sha,
        "duration_ns": duration_ns,
        "full_window_rows": full_windows,
        "partial_tail_ns": duration_ns % window_ns,
        "seed_validation_only": True,
        "formal_training_weight": 0.0,
        "final_test_visible": False,
    }
    counts = {
        "packet_sent": total_sent,
        "packet_received": total_received,
        "metrics_updated": total_metrics,
        "packet_lost": total_loss,
    }
    return rows, connection_row, counts


def _artifact_entry(
    path: Path,
    root: Path,
    *,
    row_count: int | None,
    schema_sha256: str | None,
    semantic_sha256: str,
) -> dict[str, Any]:
    return {
        "relative_path": path.relative_to(root).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "row_count": row_count,
        "schema_sha256": schema_sha256,
        "semantic_sha256": semantic_sha256,
    }


def materialize(config_path: Path, project_root: Path) -> Path:
    project_root = project_root.resolve()
    repository_root = project_root.parents[2]
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise MaterializationError("配置顶层不是对象")

    resolved_inputs: dict[str, Path] = {}
    for name in [
        "trace_manifest",
        "field_coverage",
        "unit_contract",
        "audit_source_lock",
    ]:
        item = config["inputs"][name]
        path = _resolve_input(item, project_root, repository_root)
        _validate_file(path, str(item["sha256"]))
        resolved_inputs[name] = path
    raw_item = config["inputs"]["raw_qlog_root"]
    raw_root = _resolve_input(raw_item, project_root, repository_root)
    if not raw_root.is_dir() or raw_root.is_symlink():
        raise MaterializationError(f"原始 qlog 根不是普通目录：{raw_root}")

    trace_rows = _load_jsonl(resolved_inputs["trace_manifest"])
    expected = config["expected"]
    if len(trace_rows) != int(expected["independent_connections"]):
        raise MaterializationError("qlog 独立连接数不符合配置")
    trace_rows.sort(key=lambda row: str(row["trace_id"]))
    group_ids = [str(row["group_id_sha256"]) for row in trace_rows]
    if len(set(group_ids)) != len(group_ids):
        raise MaterializationError("qlog 物理分组不是逐连接唯一")

    output_root = project_root / str(config["output_root"])
    partial_root = output_root.with_name(f"{output_root.name}.partial")
    if output_root.exists() or partial_root.exists():
        raise MaterializationError("输出根或阶段根已存在，拒绝覆盖")
    partial_root.mkdir(parents=True)

    schema = _schema()
    parquet_path = partial_root / "physics-targets-quic-seed.parquet"
    semantic_digest = hashlib.sha256()
    connection_rows: list[dict[str, Any]] = []
    aggregate_counts = {
        "packet_sent": 0,
        "packet_received": 0,
        "metrics_updated": 0,
        "packet_lost": 0,
    }
    total_rows = 0
    window_ns = int(config["window_contract"]["duration_ns"])
    writer = pq.ParquetWriter(
        parquet_path,
        schema,
        version="2.6",
        compression="zstd",
        compression_level=9,
        use_dictionary=False,
        write_statistics=True,
        data_page_version="1.0",
    )
    try:
        for stable_order, manifest_row in enumerate(trace_rows):
            rows, connection_row, counts = _materialize_trace(
                manifest_row, stable_order, raw_root, window_ns
            )
            for row in rows:
                semantic_digest.update(_canonical_json(row).encode("utf-8"))
                semantic_digest.update(b"\n")
            writer.write_table(pa.Table.from_pylist(rows, schema=schema))
            total_rows += len(rows)
            connection_rows.append(connection_row)
            for key, value in counts.items():
                aggregate_counts[key] += value
    finally:
        writer.close()

    expected_counts = {
        "packet_sent": int(expected["packet_sent_events"]),
        "packet_received": int(expected["packet_received_events"]),
        "metrics_updated": int(expected["metrics_events"]),
        "packet_lost": int(expected["endpoint_packet_lost_events"]),
    }
    if aggregate_counts != expected_counts:
        raise MaterializationError(
            f"qlog 汇总事件计数不符合合同：{aggregate_counts} != {expected_counts}"
        )
    if total_rows != int(expected["full_window_rows"]):
        raise MaterializationError(
            f"qlog 完整窗数量不符合合同：{total_rows} != {expected['full_window_rows']}"
        )

    connection_path = partial_root / "quic-seed-connection-manifest.jsonl"
    connection_semantic = _write_jsonl(connection_path, connection_rows)
    contract_path = partial_root / "contract.json"
    contract_semantic = _write_json(contract_path, config)
    source_lock = {
        "schema_version": "flow_probe_r2_final_quic_seed_source_lock_v1",
        "dataset_version": str(config["dataset_version"]),
        "upstream_commit": str(raw_item["upstream_commit"]),
        "raw_manifest_sha256": str(raw_item["manifest_sha256"]),
        "trace_manifest_sha256": str(config["inputs"]["trace_manifest"]["sha256"]),
        "field_coverage_sha256": str(config["inputs"]["field_coverage"]["sha256"]),
        "unit_contract_sha256": str(config["inputs"]["unit_contract"]["sha256"]),
        "audit_source_lock_sha256": str(
            config["inputs"]["audit_source_lock"]["sha256"]
        ),
        "candidate_qlog_content_sha256": [
            str(row["content_sha256"]) for row in trace_rows
        ],
    }
    source_lock_path = partial_root / "source-lock.json"
    source_lock_semantic = _write_json(source_lock_path, source_lock)
    schema_doc = {
        "schema_version": "flow_probe_r2_final_quic_seed_schema_v1",
        "physics_targets_quic_seed": _schema_document(schema),
        "ordering": ["connection_stable_order", "window_index"],
        "deployment_feature_columns": [
            field.name for field in schema if field.name.startswith("public_")
        ],
        "privileged_truth_columns": [
            field.name for field in schema if field.name.startswith("truth_")
        ],
    }
    schema_path = partial_root / "schema.json"
    schema_semantic = _write_json(schema_path, schema_doc)
    summary = {
        "schema_version": "flow_probe_r2_final_quic_seed_summary_v1",
        "dataset_version": str(config["dataset_version"]),
        "status": "review_pending",
        "independent_connections": len(connection_rows),
        "full_window_rows": total_rows,
        "window_duration_ns": window_ns,
        "aggregate_events": aggregate_counts,
        "seed_validation_only": True,
        "formal_training_weight": 0.0,
        "quic_formal_training_enabled": False,
        "effective_route_id": "UNKNOWN",
        "quic_expert_ready": False,
        "pto_observed": False,
        "final_test_visible": False,
    }
    summary_path = partial_root / "input-summary.json"
    summary_semantic = _write_json(summary_path, summary)

    parquet_semantic = semantic_digest.hexdigest()
    schema_sha = _schema_sha256(schema)
    artifacts = [
        _artifact_entry(
            parquet_path,
            partial_root,
            row_count=total_rows,
            schema_sha256=schema_sha,
            semantic_sha256=parquet_semantic,
        ),
        _artifact_entry(
            connection_path,
            partial_root,
            row_count=len(connection_rows),
            schema_sha256=None,
            semantic_sha256=connection_semantic,
        ),
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
        _artifact_entry(
            schema_path,
            partial_root,
            row_count=None,
            schema_sha256=None,
            semantic_sha256=schema_semantic,
        ),
        _artifact_entry(
            summary_path,
            partial_root,
            row_count=None,
            schema_sha256=None,
            semantic_sha256=summary_semantic,
        ),
    ]
    artifacts.sort(key=lambda item: str(item["relative_path"]))
    manifest = {
        "schema_version": "flow_probe_r2_final_quic_seed_artifact_manifest_v1",
        "dataset_version": str(config["dataset_version"]),
        "status": "review_pending",
        "seed_validation_only": True,
        "formal_training_weight": 0.0,
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
