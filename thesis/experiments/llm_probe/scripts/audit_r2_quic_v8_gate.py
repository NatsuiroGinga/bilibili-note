#!/usr/bin/env python3
"""审计 R2 QUIC v8 确定性有限队列丢包门禁。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import struct
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import audit_r2_quic_determinism_gate as common
import audit_r2_quic_v5_gate as v5
import audit_r2_quic_v7_gate as v7


GO_STATUS = "GO_TO_NEW_FIELD_MATRIX_QUIC_SEED_ONLY"
NO_GO_STATUS = "NO-GO_KEEP_QUIC_UNKNOWN"
INVALID_STATUS = "INVALID"
SINGLE_RUN_PASS_STATUS = "PASS_R2_QUIC_V8_SINGLE_RUN_GATE_ONLY"
SINGLE_RUN_SCHEMA = "flow_probe_r2_quic_v8_single_run_gate_v1"
THREE_RUN_SCHEMA = "flow_probe_r2_quic_v8_three_run_gate_v1"
EXPECTED_PROJECTION_BYTES = 5_398
EXPECTED_PROJECTION_SHA256 = "933d82e530200a7bd0dabd12d25a809aec4a14a9888e62a3b210b6c0295c44ef"
EXPECTED_RUNS = [
    ("r2-quic-deterministic-queue-drop-v8-run1-aioquic", "aioquic", 12),
    ("r2-quic-deterministic-queue-drop-v8-run2-quiche", "quiche", 32),
    ("r2-quic-deterministic-queue-drop-v8-run3-aioquic", "aioquic", 12),
]
V8_REPLACED_COMMON_CHECKS = frozenset(
    {
        "queue_drop_zero",
        "drop_and_send_error_bytes_zero",
        "v4_event_replay_exact",
    }
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def expected_run(run_index: int) -> dict[str, Any]:
    if not 1 <= run_index <= len(EXPECTED_RUNS):
        raise ValueError("单轮门禁序号必须为 1、2 或 3")
    run_id, implementation, target_connection_index = EXPECTED_RUNS[run_index - 1]
    return {
        "run_id": run_id,
        "implementation": implementation,
        "target_connection_index": target_connection_index,
    }


def config_enables_v8(config: dict[str, Any]) -> bool:
    deterministic = config.get("determinism_contract")
    network = config.get("network_contract")
    return (
        isinstance(deterministic, dict)
        and isinstance(network, dict)
        and deterministic.get("contract_version") == "flow_probe_r2_quic_four_tuple_contract_v8"
        and network.get("queue_drop_acceptance") == "deterministic_capacity_causal_replay_v1"
    )


def normalized_config_projection(config: dict[str, Any]) -> bytes:
    projected = copy.deepcopy(config)
    for name in (
        "schema_version",
        "dataset_version",
        "status",
        "field_output_root",
        "formal_output_root",
    ):
        projected.pop(name)
    deterministic = projected["determinism_contract"]
    deterministic.pop("contract_version")
    deterministic.pop("run_id_prefix")
    gate_runs = deterministic["gate_runs"]
    if not isinstance(gate_runs, list) or len(gate_runs) != 3:
        raise ValueError("规范化投影要求恰好三个运行身份")
    for run in gate_runs:
        run.pop("run_id")
    projected["network_contract"].pop("queue_drop_acceptance", None)
    return json.dumps(
        projected,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def contract_checks(config_path: Path, project_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    projection: dict[str, Any] = {}
    try:
        config = v5.read_json(config_path)
        v7_config = v5.read_json(
            project_root / "configs/r2_quic_controlled_directional_datagram_v7.json"
        )
        v7_projection = normalized_config_projection(v7_config)
        v8_projection = normalized_config_projection(config)
        deterministic = config["determinism_contract"]
        network = config["network_contract"]
        configured_runs = [
            (
                str(item["run_id"]),
                str(item["implementation"]),
                int(item["target_connection_index"]),
            )
            for item in deterministic["gate_runs"]
        ]
        projection = {
            "v7_bytes": len(v7_projection),
            "v7_sha256": sha256_bytes(v7_projection),
            "v8_bytes": len(v8_projection),
            "v8_sha256": sha256_bytes(v8_projection),
        }
        checks = {
            "schema_exact": config.get("schema_version")
            == "flow_probe_r2_quic_controlled_collection_userspace_v8",
            "dataset_exact": config.get("dataset_version") == "r2-quic-controlled-userspace-v8",
            "status_exact": config.get("status") == "deterministic_queue_drop_v8_frozen",
            "contract_exact": config_enables_v8(config),
            "run_prefix_exact": deterministic.get("run_id_prefix")
            == "r2-quic-deterministic-queue-drop-v8-run",
            "three_runs_exact": configured_runs == EXPECTED_RUNS,
            "field_root_exact": config.get("field_output_root")
            == "runs/data-raw/r2-quic-controlled-field-userspace-v8",
            "formal_root_exact": config.get("formal_output_root")
            == "runs/data-raw/r2-quic-controlled-formal-userspace-v8",
            "v7_projection_frozen": len(v7_projection) == EXPECTED_PROJECTION_BYTES
            and sha256_bytes(v7_projection) == EXPECTED_PROJECTION_SHA256,
            "v8_projection_exact": v8_projection == v7_projection
            and len(v8_projection) == EXPECTED_PROJECTION_BYTES
            and sha256_bytes(v8_projection) == EXPECTED_PROJECTION_SHA256,
            "queue_acceptance_exact": network.get("queue_drop_acceptance")
            == "deterministic_capacity_causal_replay_v1",
        }
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "checks": checks,
        "projection": projection,
        "config_sha256": v5.sha256_file(config_path) if config_path.is_file() else None,
        "errors": errors,
    }


def toolchain_checks(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    try:
        return v7.toolchain_checks(config, project_root)
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        return {
            "valid": False,
            "checks": {},
            "errors": [f"{type(error).__name__}: {error}"],
            "tool_root": None,
        }


def _read_event_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            raise ValueError(f"事件日志存在空行：{line_number}")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise TypeError(f"事件行不是对象：{line_number}")
        rows.append(value)
    if not rows:
        raise ValueError("事件日志为空")
    return rows


def _integer(row: dict[str, Any], name: str) -> int:
    value = row[name]
    if isinstance(value, bool):
        raise TypeError(f"{name} 不能是布尔值")
    return int(value)


def v8_common_checks_valid(common_run: dict[str, Any]) -> bool:
    checks = common_run.get("checks")
    errors = common_run.get("errors")
    return (
        isinstance(checks, dict)
        and V8_REPLACED_COMMON_CHECKS.issubset(checks)
        and isinstance(errors, list)
        and not errors
        and all(
            value is True
            for name, value in checks.items()
            if name not in V8_REPLACED_COMMON_CHECKS
        )
    )


def normalize_forwarding_lag_receipts(
    rows: list[dict[str, Any]],
    *,
    tolerance_us: int,
) -> list[dict[str, Any]]:
    if tolerance_us < 0:
        raise ValueError("实际转发滞后取整容差不得为负数")
    normalized = copy.deepcopy(rows)
    for row in normalized:
        if row.get("action") != "forwarded":
            continue
        exact_lag_us = _integer(row, "forwarded_offset_us") - _integer(
            row, "scheduled_release_offset_us"
        )
        observed_lag_us = _integer(row, "actual_forwarding_lag_us")
        if exact_lag_us < 0:
            raise ValueError("实际转发早于计划释放")
        if abs(exact_lag_us - observed_lag_us) > tolerance_us:
            raise ValueError("实际转发滞后超过冻结取整容差")
        row["actual_forwarding_lag_us"] = exact_lag_us
    return normalized


def audit_v8_event_log(
    event_path: Path,
    proxy_stats: dict[str, Any],
    *,
    require_server_to_client_drop: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    directions_result: dict[str, Any] = {}
    base_audit: dict[str, Any] = {}
    try:
        rows = _read_event_rows(event_path)
        sequences = [_integer(row, "sequence") for row in rows]
        parameters = proxy_stats["parameters"]
        capacity = int(parameters["queue_capacity_bytes"])
        rounding_tolerance_us = int(
            parameters["serialization_rounding_tolerance_us_per_packet"]
        )
        limits = parameters["max_datagram_bytes_by_direction"]
        directions = proxy_stats["directions"]
        if not isinstance(limits, dict) or not isinstance(directions, dict):
            raise TypeError("代理统计缺少方向级参数")
        if "contract_error" not in proxy_stats or proxy_stats["contract_error"] is not None:
            raise ValueError("contract_error 必须存在且严格为 JSON null")
        if any(row.get("action") == "contract_failed" for row in rows):
            raise ValueError("事件日志出现 contract_failed")
        if sequences != list(range(1, len(rows) + 1)):
            raise ValueError("事件全局序号不连续")

        normalized_rows = normalize_forwarding_lag_receipts(
            rows,
            tolerance_us=rounding_tolerance_us,
        )
        normalized_stats = copy.deepcopy(proxy_stats)
        for direction_name in directions:
            exact_lags = [
                _integer(row, "actual_forwarding_lag_us")
                for row in normalized_rows
                if row.get("direction") == direction_name
                and row.get("action") == "forwarded"
            ]
            normalized_stats["directions"][direction_name][
                "max_actual_forwarding_lag_us"
            ] = max(exact_lags, default=0)
        with tempfile.TemporaryDirectory(prefix="r2-quic-v8-audit-") as temporary:
            normalized_event_path = Path(temporary) / "proxy-events-normalized.jsonl"
            normalized_event_path.write_text(
                "".join(
                    json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                    for row in normalized_rows
                ),
                encoding="utf-8",
            )
            base_audit = common.audit_v4_event_log(normalized_event_path, normalized_stats)
        if base_audit.get("valid") is not True:
            raise ValueError(f"公共事件重放失败：{base_audit.get('errors')}")

        for direction_name, stats in directions.items():
            if direction_name not in limits or not isinstance(stats, dict):
                raise ValueError(f"方向统计非法：{direction_name}")
            direction_rows = [row for row in rows if row.get("direction") == direction_name]
            decisions = [
                row for row in direction_rows if row.get("action") in {"scheduled", "dropped"}
            ]
            received_packets = int(stats["received_packets"])
            received_bytes = int(stats["received_bytes"])
            if len(decisions) != received_packets:
                raise ValueError(f"{direction_name} 准入决策数量不闭合")
            packet_sequences = [_integer(row, "packet_sequence") for row in decisions]
            if packet_sequences != list(range(1, received_packets + 1)):
                raise ValueError(f"{direction_name} 准入决策包序号不连续")
            decisions_by_batch: dict[int, list[dict[str, Any]]] = {}
            for decision in decisions:
                decisions_by_batch.setdefault(_integer(decision, "receive_batch_id"), []).append(
                    decision
                )

            batches = [
                row for row in direction_rows if row.get("action") == "receive_batch_completed"
            ]
            batch_ids = [_integer(row, "receive_batch_id") for row in batches]
            if batch_ids != list(range(1, len(batches) + 1)):
                raise ValueError(f"{direction_name} 接收批次序号不连续")
            for decision in decisions:
                batch_id = _integer(decision, "receive_batch_id")
                if batch_id not in batch_ids:
                    raise ValueError(f"{direction_name} 决策引用未知接收批次")
            for batch in batches:
                batch_id = _integer(batch, "receive_batch_id")
                members = decisions_by_batch.get(batch_id, [])
                if len(members) != _integer(batch, "batch_packets") or sum(
                    _integer(row, "bytes") for row in members
                ) != _integer(batch, "batch_bytes"):
                    raise ValueError(f"{direction_name} 接收批次包/字节不闭合")
            if (
                sum(_integer(row, "batch_packets") for row in batches) != received_packets
                or sum(_integer(row, "batch_bytes") for row in batches) != received_bytes
            ):
                raise ValueError(f"{direction_name} 接收批次总量不闭合")

            scheduled = {
                int(row["packet_sequence"]): row
                for row in decisions
                if row["action"] == "scheduled"
            }
            dropped = {
                int(row["packet_sequence"]): row for row in decisions if row["action"] == "dropped"
            }
            service_completed = [
                row for row in direction_rows if row.get("action") == "service_completed"
            ]
            forwarded = [row for row in direction_rows if row.get("action") == "forwarded"]
            send_failed = [row for row in direction_rows if row.get("action") == "send_failed"]
            completions_by_packet: dict[int, list[dict[str, Any]]] = {}
            for item in service_completed:
                completions_by_packet.setdefault(_integer(item, "packet_sequence"), []).append(item)
            terminals_by_packet: dict[int, list[dict[str, Any]]] = {}
            for item in forwarded + send_failed:
                terminals_by_packet.setdefault(_integer(item, "packet_sequence"), []).append(item)
            lifecycle_packet_sequences = set(completions_by_packet) | set(terminals_by_packet)
            delay_inflight = 0
            for row in direction_rows:
                action = row.get("action")
                if action == "service_completed":
                    if _integer(row, "delay_inflight_before_bytes") != delay_inflight:
                        raise ValueError(f"{direction_name} 传播账本服务完成前不闭合")
                    delay_inflight = _integer(row, "delay_inflight_after_bytes")
                elif action in {"forwarded", "send_failed"}:
                    if _integer(row, "delay_inflight_before_bytes") != delay_inflight:
                        raise ValueError(f"{direction_name} 传播账本转发前不闭合")
                    delay_inflight = _integer(row, "delay_inflight_after_bytes")
                elif (
                    action == "dropped" and _integer(row, "delay_inflight_bytes") != delay_inflight
                ):
                    raise ValueError(f"{direction_name} 丢弃改变了传播账本")

            for packet_sequence, row in scheduled.items():
                completions = completions_by_packet.get(packet_sequence, [])
                terminals = terminals_by_packet.get(packet_sequence, [])
                if len(completions) != 1 or len(terminals) != 1:
                    raise ValueError(f"{direction_name} 准入包生命周期不唯一")
                completion = completions[0]
                terminal = terminals[0]
                times = [
                    _integer(row, "arrival_offset_us"),
                    _integer(row, "serialization_start_offset_us"),
                    _integer(row, "serialization_finish_offset_us"),
                    _integer(row, "scheduled_release_offset_us"),
                    _integer(terminal, "forwarded_offset_us"),
                ]
                if times != sorted(times):
                    raise ValueError(f"{direction_name} 准入包时间关系错误")
                if _integer(completion, "service_completion_offset_us") != times[2]:
                    raise ValueError(f"{direction_name} 服务完成时间不等于序列化结束")

            queue_drop_packets = 0
            queue_drop_bytes = 0
            for packet_sequence, row in dropped.items():
                if packet_sequence in lifecycle_packet_sequences:
                    raise ValueError(f"{direction_name} 丢弃包仍有生命周期事件")
                datagram_bytes = _integer(row, "bytes")
                before = _integer(row, "service_backlog_before_bytes")
                after = _integer(row, "service_backlog_after_bytes")
                waiting_before = _integer(row, "waiting_before_bytes")
                waiting_after = _integer(row, "waiting_after_bytes")
                in_service_before = _integer(row, "in_service_before_bytes")
                in_service_after = _integer(row, "in_service_after_bytes")
                if (
                    row.get("reason") != "userspace_queue_limit_bytes"
                    or row.get("admitted") is not False
                    or not 0 < datagram_bytes <= int(limits[direction_name])
                    or before + datagram_bytes <= capacity
                    or after != before
                    or waiting_after != waiting_before
                    or in_service_after != in_service_before
                    or before != waiting_before + in_service_before
                    or after != waiting_after + in_service_after
                    or min(
                        before,
                        after,
                        waiting_before,
                        waiting_after,
                        in_service_before,
                        in_service_after,
                    )
                    < 0
                    or any(
                        row.get(name) is not None
                        for name in (
                            "serialization_start_offset_us",
                            "serialization_finish_offset_us",
                            "scheduled_release_offset_us",
                        )
                    )
                ):
                    raise ValueError(f"{direction_name} 容量丢弃因果或账本错误")
                queue_drop_packets += 1
                queue_drop_bytes += datagram_bytes

            zero_fields = (
                "random_drop_packets",
                "random_drop_bytes",
                "send_error_packets",
                "send_error_bytes",
                "queued_packets_at_shutdown",
                "service_backlog_bytes_at_shutdown",
                "waiting_bytes_at_shutdown",
                "in_service_bytes_at_shutdown",
                "delay_inflight_bytes_at_shutdown",
            )
            if any(int(stats.get(name, -1)) != 0 for name in zero_fields):
                raise ValueError(f"{direction_name} 零容忍计数非零或缺失")
            if (
                received_packets
                != int(stats["scheduled_packets"])
                + int(stats["random_drop_packets"])
                + int(stats["queue_drop_packets"])
                or received_bytes
                != int(stats["scheduled_bytes"])
                + int(stats["random_drop_bytes"])
                + int(stats["queue_drop_bytes"])
                or int(stats["scheduled_packets"])
                != int(stats["forwarded_packets"])
                + int(stats["send_error_packets"])
                + int(stats["queued_packets_at_shutdown"])
                or int(stats["scheduled_bytes"])
                != int(stats["forwarded_bytes"]) + int(stats["send_error_bytes"])
                or queue_drop_packets != int(stats["queue_drop_packets"])
                or queue_drop_bytes != int(stats["queue_drop_bytes"])
                or int(stats["peak_service_backlog_bytes"]) > capacity
            ):
                raise ValueError(f"{direction_name} 包/字节守恒或容量统计不闭合")
            directions_result[direction_name] = {
                "received_packets": received_packets,
                "received_bytes": received_bytes,
                "decision_count": len(decisions),
                "batch_count": len(batches),
                "queue_drop_packets": queue_drop_packets,
                "queue_drop_bytes": queue_drop_bytes,
                "lifecycle_complete": True,
            }

        if (
            int(proxy_stats.get("scheduled_packets_at_shutdown", -1)) != 0
            or int(proxy_stats.get("scheduled_bytes_at_shutdown", -1)) != 0
        ):
            raise ValueError("顶层关停调度计数非零或缺失")
        if (
            require_server_to_client_drop
            and directions_result.get("server_to_client", {}).get("queue_drop_packets", 0) < 1
        ):
            raise ValueError("server_to_client 未触发容量丢弃分支")
        checks = {
            "global_sequence_exact": True,
            "contract_error_strict_null": True,
            "public_replay_valid": True,
            "direction_lifecycle_valid": True,
            "required_capacity_drop_observed": not require_server_to_client_drop
            or directions_result["server_to_client"]["queue_drop_packets"] >= 1,
        }
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "checks": checks,
        "directions": directions_result,
        "base_audit": base_audit,
        "errors": errors,
    }


def _validate_qlog_event(value: Any, *, context: str) -> None:
    if not isinstance(value, dict):
        raise TypeError(f"qlog 事件不是对象：{context}")
    timestamp = value.get("time")
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)):
        raise ValueError(f"qlog 事件时间非法：{context}")
    if not isinstance(value.get("name"), str) or not value["name"]:
        raise ValueError(f"qlog 事件名称非法：{context}")
    if not isinstance(value.get("data"), dict):
        raise ValueError(f"qlog 事件数据非法：{context}")


def _validate_qlog_document(value: Any, *, context: str) -> int:
    if not isinstance(value, dict):
        raise TypeError(f"qlog 文档不是对象：{context}")
    if not isinstance(value.get("qlog_version"), str) or not value["qlog_version"]:
        raise ValueError(f"qlog_version 非法：{context}")
    if value.get("qlog_format") != "JSON":
        raise ValueError(f"整体 qlog 的 qlog_format 必须为 JSON：{context}")
    traces = value.get("traces")
    if not isinstance(traces, list) or not traces:
        raise ValueError(f"整体 qlog 缺少非空 traces：{context}")
    event_count = 0
    for trace_index, trace in enumerate(traces):
        trace_context = f"{context}:trace={trace_index}"
        if (
            not isinstance(trace, dict)
            or not isinstance(trace.get("vantage_point"), dict)
            or not isinstance(trace.get("common_fields"), dict)
            or not isinstance(trace.get("events"), list)
            or not trace["events"]
        ):
            raise ValueError(f"qlog trace 结构非法：{trace_context}")
        for event_index, event in enumerate(trace["events"]):
            _validate_qlog_event(event, context=f"{trace_context}:event={event_index}")
            event_count += 1
    return event_count


def _validate_qlog_sequence(values: list[Any], *, context: str) -> int:
    if len(values) < 2 or not isinstance(values[0], dict):
        raise ValueError(f"JSON-SEQ qlog 缺少头记录或事件：{context}")
    header = values[0]
    trace = header.get("trace")
    configuration = trace.get("configuration") if isinstance(trace, dict) else None
    time_offset = configuration.get("time_offset") if isinstance(configuration, dict) else None
    if (
        not isinstance(header.get("qlog_version"), str)
        or not header["qlog_version"]
        or header.get("qlog_format") != "JSON-SEQ"
        or not isinstance(trace, dict)
        or not isinstance(trace.get("vantage_point"), dict)
        or (
            "common_fields" in trace
            and not isinstance(trace.get("common_fields"), dict)
        )
        or not isinstance(configuration, dict)
        or isinstance(time_offset, bool)
        or not isinstance(time_offset, (int, float))
    ):
        raise ValueError(f"JSON-SEQ qlog 头记录非法：{context}")
    for event_index, event in enumerate(values[1:], start=1):
        _validate_qlog_event(event, context=f"{context}:record={event_index}")
    return len(values) - 1


def audit_all_qlogs(paths: list[Path]) -> dict[str, Any]:
    errors: list[str] = []
    file_results: list[dict[str, Any]] = []
    total_payload_decrypt_error = 0
    try:
        if not paths:
            raise ValueError("qlog 文件为空")
        for path in sorted(paths):
            raw = path.read_text(encoding="utf-8")
            if not raw:
                raise ValueError(f"qlog 为空：{path}")
            values: list[Any]
            qlog_format: str
            event_count: int
            try:
                document = json.loads(raw)
                values = [document]
                qlog_format = "JSON"
                event_count = _validate_qlog_document(document, context=str(path))
            except json.JSONDecodeError:
                values = []
                records = raw.split("\n")
                if records[-1] == "":
                    records = records[:-1]
                for line_number, line in enumerate(records, start=1):
                    if not line.startswith("\x1e"):
                        raise ValueError(f"JSON-SEQ qlog 记录缺少分隔符：{path}:{line_number}")
                    candidate = line[1:].strip()
                    if not candidate:
                        raise ValueError(f"qlog 存在空行：{path}:{line_number}")
                    try:
                        values.append(json.loads(candidate))
                    except json.JSONDecodeError as error:
                        raise ValueError(
                            f"qlog 无法完整解析：{path}:{line_number}: {error}"
                        ) from error
                qlog_format = "JSON-SEQ"
                event_count = _validate_qlog_sequence(values, context=str(path))
            if not values:
                raise ValueError(f"qlog 没有可解析记录：{path}")
            payload_decrypt_error = sum(
                common.count_exact_payload_decrypt_error(value) for value in values
            )
            total_payload_decrypt_error += payload_decrypt_error
            file_results.append(
                {
                    "path": str(path),
                    "sha256": v5.sha256_file(path),
                    "bytes": path.stat().st_size,
                    "record_count": len(values),
                    "event_count": event_count,
                    "qlog_format": qlog_format,
                    "payload_decrypt_error": payload_decrypt_error,
                }
            )
        if total_payload_decrypt_error != 0:
            raise ValueError("qlog 出现 payload_decrypt_error")
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(file_results) and not errors,
        "file_count": len(file_results),
        "files": file_results,
        "payload_decrypt_error": total_payload_decrypt_error,
        "errors": errors,
    }


def audit_pcap(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    packet_count = 0
    snaplen: int | None = None
    try:
        raw = path.read_bytes()
        if len(raw) <= 24:
            raise ValueError("PCAP 缺失有效记录")
        formats = {
            b"\xd4\xc3\xb2\xa1": ("<", 1_000_000),
            b"\xa1\xb2\xc3\xd4": (">", 1_000_000),
            b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000),
            b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000),
        }
        if raw[:4] not in formats:
            raise ValueError("PCAP 魔数不受支持")
        endian, timestamp_limit = formats[raw[:4]]
        _, major, minor, _, _, snaplen, _ = struct.unpack(f"{endian}IHHIIII", raw[:24])
        if (major, minor) != (2, 4) or snaplen <= 0:
            raise ValueError("PCAP 全局头非法")
        offset = 24
        while offset < len(raw):
            if len(raw) - offset < 16:
                raise ValueError("PCAP 尾部记录头截断")
            _, fraction, captured_length, original_length = struct.unpack(
                f"{endian}IIII", raw[offset : offset + 16]
            )
            offset += 16
            if fraction >= timestamp_limit or not 0 < captured_length <= original_length <= snaplen:
                raise ValueError("PCAP 记录长度或时间戳非法")
            if len(raw) - offset < captured_length:
                raise ValueError("PCAP 数据记录截断")
            offset += captured_length
            packet_count += 1
        if offset != len(raw) or packet_count == 0:
            raise ValueError("PCAP 未完整解析至文件结尾")
    except (OSError, struct.error, TypeError, ValueError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": packet_count > 0 and not errors,
        "path": str(path),
        "sha256": v5.sha256_file(path) if path.is_file() else None,
        "bytes": path.stat().st_size if path.is_file() else None,
        "packet_count": packet_count,
        "snaplen": snaplen,
        "errors": errors,
    }


def audit_capture_log(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    counts: dict[str, int] = {}
    try:
        raw = path.read_text(encoding="utf-8", errors="strict")
        patterns = {
            "captured": r"(?m)^(\d+)\s+packets? captured\s*$",
            "received_by_filter": r"(?m)^(\d+)\s+packets? received by filter\s*$",
            "dropped_by_kernel": r"(?m)^(\d+)\s+packets? dropped by kernel\s*$",
        }
        for name, pattern in patterns.items():
            matches = re.findall(pattern, raw)
            if len(matches) != 1:
                raise ValueError(f"捕获日志字段缺失或重复：{name}")
            counts[name] = int(matches[0])
        if counts["captured"] <= 0 or counts["received_by_filter"] <= 0:
            raise ValueError("捕获日志没有有效数据包")
        if counts["dropped_by_kernel"] != 0:
            raise ValueError("捕获发生内核丢包")
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {"valid": bool(counts) and not errors, "counts": counts, "errors": errors}


def audit_v8_pacing(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"valid": False, "errors": errors}
    try:
        connection_roots = [
            path.parent
            for path in (root / "connections").glob("*/status.json")
            if v5.read_json(path).get("status") == "finished"
        ]
        if len(connection_roots) != 1:
            raise ValueError("v8 门禁输出必须恰有一个完成连接")
        connection_root = connection_roots[0]
        state = v5.read_json(connection_root / "status.json")
        stats = v5.read_json(connection_root / "proxy-stats.json")
        client_implementation = str(state["implementation"])
        max_client_datagram = 1_200 if client_implementation == "aioquic" else 1_350
        directions = stats["directions"]
        client = v5.audit_receipt_stream(
            v5.pacing_receipts(connection_root / "client.log"),
            implementation=client_implementation,
            endpoint_role="client",
            expected_packets=int(directions["client_to_server"]["received_packets"]),
            expected_bytes=int(directions["client_to_server"]["received_bytes"]),
            max_datagram_bytes=max_client_datagram,
            require_any_pacing_requested=client_implementation == "quiche",
        )
        server = v5.audit_receipt_stream(
            v5.pacing_receipts(connection_root / "reference-server.log"),
            implementation="quiche",
            endpoint_role="server",
            expected_packets=int(directions["server_to_client"]["received_packets"]),
            expected_bytes=int(directions["server_to_client"]["received_bytes"]),
            max_datagram_bytes=1_350,
            require_any_pacing_requested=True,
        )
        result.update(
            {
                "valid": client["valid"] and server["valid"],
                "connection_id": state["connection_id"],
                "client_log": str(connection_root / "client.log"),
                "server_log": str(connection_root / "reference-server.log"),
                "client": client,
                "server": server,
            }
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return result


def audit_v8_run(
    output_root: Path,
    *,
    require_server_to_client_drop: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"valid": False, "output_root": str(output_root), "errors": errors}
    common_run = common.audit_run(output_root)
    common_checks_valid = v8_common_checks_valid(common_run)
    pacing = audit_v8_pacing(output_root)
    try:
        config = v5.read_json(output_root / "collection-config.json")
        if not config_enables_v8(config):
            raise ValueError("运行根不是 v8 容量丢包合同")
        connection_roots = sorted(
            path for path in (output_root / "connections").iterdir() if path.is_dir()
        )
        if len(connection_roots) != 1:
            raise ValueError("v8 门禁运行必须恰有一个连接目录")
        connection_root = connection_roots[0]
        proxy_stats_path = connection_root / "proxy-stats.json"
        event_path = connection_root / "proxy-events.jsonl"
        pcap_path = connection_root / "deployment-observation.pcap"
        capture_log_path = connection_root / "capture.log"
        exit_codes = v5.read_json(connection_root / "exit-code.json")
        proxy_stats = v5.read_json(proxy_stats_path)
        event_audit = audit_v8_event_log(
            event_path,
            proxy_stats,
            require_server_to_client_drop=require_server_to_client_drop,
        )
        qlog_paths = sorted(path for path in (connection_root / "qlog").iterdir() if path.is_file())
        qlog_audit = audit_all_qlogs(qlog_paths)
        pcap_audit = audit_pcap(pcap_path)
        capture_audit = audit_capture_log(capture_log_path)
        capture_exit_exact = exit_codes.get("capture_exit") == 0
        valid = (
            common_checks_valid
            and pacing.get("valid") is True
            and event_audit["valid"]
            and qlog_audit["valid"]
            and pcap_audit["valid"]
            and capture_audit["valid"]
            and capture_exit_exact
        )
        result.update(
            {
                "valid": valid,
                "common_run": common_run,
                "v8_common_checks_valid": common_checks_valid,
                "pacing": pacing,
                "event_audit": event_audit,
                "qlog_audit": qlog_audit,
                "pcap_audit": pcap_audit,
                "capture_log_audit": capture_audit,
                "capture_exit_exact": capture_exit_exact,
                "artifact_hashes": {
                    "proxy_stats": v5.sha256_file(proxy_stats_path),
                    "proxy_events": v5.sha256_file(event_path),
                    "capture_log": v5.sha256_file(capture_log_path),
                },
            }
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
        result.update({"common_run": common_run, "pacing": pacing})
    return result


def audit_single_launcher(
    launcher_status_path: Path,
    output_root: Path,
    config_path: Path,
    frozen_run: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    state: dict[str, Any] = {}
    try:
        state = v5.read_json(launcher_status_path)
        started = common.parse_timestamp(state.get("started_at"))
        finished = common.parse_timestamp(state.get("finished_at"))
        checks = {
            "status_path_identity_exact": launcher_status_path.parent.name == frozen_run["run_id"],
            "schema_exact": state.get("schema_version") == "flow_probe_r2_quic_launcher_v4",
            "run_id_exact": state.get("run_id") == frozen_run["run_id"],
            "phase_exact": state.get("phase") == "field",
            "finished_successfully": state.get("status") == "finished"
            and state.get("driver_exit") == 0
            and state.get("tee_exit") == 0,
            "output_root_exact": Path(str(state.get("output_root", ""))).resolve() == output_root,
            "config_path_exact": Path(str(state.get("config_path", ""))).resolve() == config_path,
            "timestamps_ordered": finished >= started,
        }
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "path": str(launcher_status_path),
        "sha256": v5.sha256_file(launcher_status_path) if launcher_status_path.is_file() else None,
        "checks": checks,
        "state_identity": {
            "run_id": state.get("run_id"),
            "status": state.get("status"),
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
        },
        "errors": errors,
    }


def audit_single_run(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    config_path = args.config.resolve()
    output_root = args.output_root.resolve()
    launcher_status_path = args.launcher_status_path.resolve()
    summary_path = args.summary_path.resolve()
    temporary_summary = summary_path.with_suffix(summary_path.suffix + ".tmp")
    if summary_path.exists() or temporary_summary.exists():
        print(NO_GO_STATUS, flush=True)
        return 2

    frozen_run = expected_run(args.run_index)
    expected_output_root = project_root / "runs/data-raw" / frozen_run["run_id"]
    expected_launcher_path = project_root / "runs/launchers" / frozen_run["run_id"] / "status.json"
    expected_summary_path = (
        project_root
        / "runs/audits"
        / f"r2-quic-deterministic-queue-drop-v8-run{args.run_index}-single-gate-summary.json"
    )
    expected_config_path = (
        project_root / "configs/r2_quic_controlled_deterministic_queue_drop_v8.json"
    )
    identity_checks = {
        "config_path_exact": config_path == expected_config_path,
        "output_root_exact": output_root == expected_output_root,
        "launcher_path_exact": launcher_status_path == expected_launcher_path,
        "summary_path_exact": summary_path == expected_summary_path,
    }
    setup_errors: list[str] = []
    config: dict[str, Any] = {}
    config_sha256: str | None = None
    copied_config_sha256: str | None = None
    try:
        config = v5.read_json(config_path)
        config_sha256 = v5.sha256_file(config_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        setup_errors.append(f"配置读取失败：{type(error).__name__}: {error}")
    copied_path = output_root / "collection-config.json"
    try:
        copied_config_sha256 = v5.sha256_file(copied_path)
    except OSError as error:
        setup_errors.append(f"复制配置读取失败：{type(error).__name__}: {error}")
    copied_config_exact = (
        config_sha256 is not None
        and copied_config_sha256 is not None
        and config_sha256 == copied_config_sha256
    )
    configured_run_exact = False
    try:
        configured = config["determinism_contract"]["gate_runs"][args.run_index - 1]
        configured_run_exact = (
            configured.get("run_id") == frozen_run["run_id"]
            and configured.get("implementation") == frozen_run["implementation"]
            and int(configured.get("target_connection_index"))
            == frozen_run["target_connection_index"]
        )
    except (KeyError, IndexError, TypeError, ValueError) as error:
        setup_errors.append(f"运行身份读取失败：{type(error).__name__}: {error}")
    identity_checks["configured_gate_entry_exact"] = configured_run_exact

    contract = contract_checks(config_path, project_root)
    toolchain = toolchain_checks(config, project_root)
    launcher = audit_single_launcher(
        launcher_status_path,
        output_root,
        config_path,
        frozen_run,
    )
    run_audit = audit_v8_run(
        output_root,
        require_server_to_client_drop=args.run_index in {1, 3},
    )
    common_evidence = run_audit.get("common_run", {}).get("evidence", {})
    identity_checks["implementation_exact"] = (
        isinstance(common_evidence, dict)
        and common_evidence.get("implementation") == frozen_run["implementation"]
    )
    identity_valid = all(identity_checks.values())
    passed = (
        not setup_errors
        and identity_valid
        and contract.get("valid") is True
        and toolchain.get("valid") is True
        and copied_config_exact
        and launcher.get("valid") is True
        and run_audit.get("valid") is True
    )
    status = (
        SINGLE_RUN_PASS_STATUS
        if passed
        else (INVALID_STATUS if not identity_valid else NO_GO_STATUS)
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    common.atomic_json(
        summary_path,
        {
            "schema_version": SINGLE_RUN_SCHEMA,
            "status": status,
            "audit_time": datetime.now(timezone.utc).isoformat(),
            "run_index": args.run_index,
            "expected_run": frozen_run,
            "project_root": str(project_root),
            "config_path": str(config_path),
            "config_sha256": config_sha256,
            "output_root": str(output_root),
            "launcher_status_path": str(launcher_status_path),
            "copied_config_path": str(copied_path),
            "copied_config_sha256": copied_config_sha256,
            "copied_config_exact": copied_config_exact,
            "identity_audit": {
                "valid": identity_valid,
                "checks": identity_checks,
                "errors": [],
            },
            "contract_audit": contract,
            "toolchain_audit": toolchain,
            "launcher_audit": launcher,
            "run_audit": run_audit,
            "setup_errors": setup_errors,
            "all_conditions_passed": passed,
        },
    )
    print(status, flush=True)
    return 0 if passed else 1


def formal_audit(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    config_path = args.config.resolve()
    summary_path = args.summary_path.resolve()
    if summary_path.exists() or summary_path.with_suffix(summary_path.suffix + ".tmp").exists():
        print(NO_GO_STATUS, flush=True)
        return 2
    roots = [path.resolve() for path in args.output_roots]
    launcher_paths = [path.resolve() for path in args.launcher_status_paths]
    expected_roots = [project_root / "runs/data-raw" / item[0] for item in EXPECTED_RUNS]
    expected_launchers = [
        project_root / "runs/launchers" / item[0] / "status.json" for item in EXPECTED_RUNS
    ]
    expected_summary = (
        project_root / "runs/audits/r2-quic-deterministic-queue-drop-v8-three-gate-summary.json"
    )
    config = v5.read_json(config_path)
    contract = contract_checks(config_path, project_root)
    toolchain = toolchain_checks(config, project_root)
    config_sha256 = v5.sha256_file(config_path)
    runs = [
        audit_v8_run(root, require_server_to_client_drop=index in {0, 2})
        for index, root in enumerate(roots)
    ]
    launcher_states = [v5.read_json(path) for path in launcher_paths]
    launcher = common.audit_launcher_contract(
        launcher_states,
        roots,
        [item[0] for item in EXPECTED_RUNS],
        [path.parent.name for path in launcher_paths],
        "flow_probe_r2_quic_launcher_v4",
    )
    copied_config_exact = all(
        v5.sha256_file(root / "collection-config.json") == config_sha256 for root in roots
    )
    implementations = [
        run.get("common_run", {}).get("evidence", {}).get("implementation") for run in runs
    ]
    responses = [
        run.get("common_run", {}).get("evidence", {}).get("response_sha256") for run in runs
    ]
    identity_exact = (
        roots == expected_roots
        and launcher_paths == expected_launchers
        and summary_path == expected_summary
        and implementations == [item[1] for item in EXPECTED_RUNS]
    )
    cross_run = {
        "response_sha256_consistent": all(responses) and len(set(responses)) == 1,
        "implementations_covered": set(implementations) == {"aioquic", "quiche"},
        "run1_and_run3_capacity_drop": all(
            runs[index]
            .get("event_audit", {})
            .get("directions", {})
            .get("server_to_client", {})
            .get("queue_drop_packets", 0)
            >= 1
            for index in (0, 2)
        ),
    }
    passed = (
        identity_exact
        and contract.get("valid") is True
        and toolchain.get("valid") is True
        and copied_config_exact
        and launcher.get("valid") is True
        and all(run.get("valid") is True for run in runs)
        and all(cross_run.values())
    )
    status = GO_STATUS if passed else (INVALID_STATUS if not identity_exact else NO_GO_STATUS)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    common.atomic_json(
        summary_path,
        {
            "schema_version": THREE_RUN_SCHEMA,
            "status": status,
            "audit_time": datetime.now(timezone.utc).isoformat(),
            "config_path": str(config_path),
            "config_sha256": config_sha256,
            "output_roots": [str(path) for path in roots],
            "launcher_status_paths": [str(path) for path in launcher_paths],
            "identity_exact": identity_exact,
            "contract_audit": contract,
            "toolchain_audit": toolchain,
            "copied_config_exact": copied_config_exact,
            "launcher_audit": launcher,
            "runs": runs,
            "cross_run_checks": cross_run,
            "all_conditions_passed": passed,
        },
    )
    print(status, flush=True)
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check-contract-only", action="store_true")
    parser.add_argument("--check-toolchain", action="store_true")
    parser.add_argument("--single-run", action="store_true")
    parser.add_argument("--run-index", type=int, choices=(1, 2, 3))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--launcher-status-path", type=Path)
    parser.add_argument("--output-roots", type=Path, nargs=3)
    parser.add_argument("--launcher-status-paths", type=Path, nargs=3)
    parser.add_argument("--summary-path", type=Path)
    args = parser.parse_args()
    if args.check_contract_only:
        result = contract_checks(args.config.resolve(), args.project_root.resolve())
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.check_toolchain:
        config = v5.read_json(args.config.resolve())
        result = {
            "contract": contract_checks(args.config.resolve(), args.project_root.resolve()),
            "toolchain": toolchain_checks(config, args.project_root.resolve()),
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["contract"]["valid"] and result["toolchain"]["valid"] else 1
    if args.single_run:
        if (
            args.run_index is None
            or args.output_root is None
            or args.launcher_status_path is None
            or args.summary_path is None
        ):
            raise SystemExit("单轮审计缺少运行序号、输出根、启动器状态或摘要路径")
        if args.output_roots or args.launcher_status_paths:
            raise SystemExit("单轮审计不得混用三轮输入")
        return audit_single_run(args)
    if not args.output_roots or not args.launcher_status_paths or not args.summary_path:
        raise SystemExit("三轮审计必须提供三份输出根、启动器状态和唯一摘要路径")
    return formal_audit(args)


if __name__ == "__main__":
    raise SystemExit(main())
