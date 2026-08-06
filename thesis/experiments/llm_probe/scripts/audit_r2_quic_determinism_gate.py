#!/usr/bin/env python3
"""审计恰好三个 R2 QUIC 确定性修复输出根。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Any


GO_STATUS = "GO_TO_INDEPENDENT_REVIEW"
NO_GO_STATUS = "NO-GO_KEEP_QUIC_UNKNOWN"
EXPECTED_RESPONSE_BYTES = 67_108_864
EXPECTED_DIRECTION_SEEDS = {
    "client_to_server": 373387841787797959,
    "server_to_client": 7996260466250834367,
}
EXPECTED_ENDPOINTS = {
    "client": ["127.0.0.1", 21012],
    "proxy_listen": ["127.0.0.1", 20012],
    "proxy_upstream": ["127.0.0.1", 22012],
    "reference_server": ["127.0.0.1", 4433],
}
EXPECTED_SCHEDULE_MODE = "fixed_sequence_epoch_v1"
EXPECTED_V4_SCHEDULE_MODE = "work_conserving_byte_service_delay_v1"
EXPECTED_V4_QUEUE_CAPACITY_BYTES = 2_097_152
EXPECTED_V4_QUEUE_MARGIN_MAX_BYTES = 1_677_721
EXPECTED_V4_MAX_DATAGRAM_BYTES = {1_200, 1_350}


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON 顶层必须为对象：{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def audit_artifact_manifest(
    connection_root: Path,
    manifest: Any,
) -> dict[str, Any]:
    errors: list[str] = []
    checked_count = 0
    seen_paths: set[str] = set()
    if not isinstance(manifest, list) or not manifest:
        return {
            "valid": False,
            "checked_count": 0,
            "errors": ["制品清单必须是非空列表"],
        }
    resolved_root = connection_root.resolve()
    for index, item in enumerate(manifest):
        try:
            if not isinstance(item, dict):
                raise TypeError("清单项必须为对象")
            relative_path = item["path"]
            if not isinstance(relative_path, str) or not relative_path:
                raise TypeError("path 必须为非空字符串")
            candidate_relative = Path(relative_path)
            if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
                raise ValueError("path 必须是连接根内的相对路径")
            if relative_path in seen_paths:
                raise ValueError("path 重复")
            seen_paths.add(relative_path)
            candidate = (connection_root / candidate_relative).resolve()
            if candidate.parent != resolved_root and resolved_root not in candidate.parents:
                raise ValueError("path 逃逸连接根")
            if not candidate.is_file():
                raise FileNotFoundError(f"制品不存在：{relative_path}")
            expected_bytes = int(item["bytes"])
            expected_sha256 = str(item["sha256"])
            if candidate.stat().st_size != expected_bytes:
                raise ValueError(f"制品大小不一致：{relative_path}")
            if sha256_file(candidate) != expected_sha256:
                raise ValueError(f"制品 SHA-256 不一致：{relative_path}")
            checked_count += 1
        except (KeyError, OSError, TypeError, ValueError) as error:
            errors.append(f"item[{index}]: {type(error).__name__}: {error}")
    return {
        "valid": checked_count == len(manifest) and not errors,
        "checked_count": checked_count,
        "errors": errors,
    }


def parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("时间戳必须为非空字符串")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def timestamp_is_valid(value: Any) -> bool:
    try:
        parse_timestamp(value)
    except (TypeError, ValueError):
        return False
    return True


def audit_launcher_contract(
    launcher_states: list[dict[str, Any]],
    output_roots: list[Path],
    expected_run_ids: list[str],
    discovered_run_ids: list[str] | None = None,
    expected_schema_version: str = "flow_probe_r2_quic_launcher_v3",
) -> dict[str, Any]:
    errors: list[str] = []
    exactly_three = (
        len(launcher_states) == 3
        and len(output_roots) == 3
        and len(expected_run_ids) == 3
        and len(set(expected_run_ids)) == 3
    )
    run_ids = [str(state.get("run_id", "")) for state in launcher_states]
    discovered_identities_exact = sorted(
        run_ids if discovered_run_ids is None else discovered_run_ids
    ) == sorted(expected_run_ids)
    outputs_match = all(
        str(Path(str(state.get("output_root", ""))).resolve()) == str(root.resolve())
        for state, root in zip(launcher_states, output_roots)
    )
    statuses_finished = all(
        state.get("schema_version") == expected_schema_version
        and state.get("status") == "finished"
        and state.get("driver_exit") == 0
        and state.get("tee_exit") == 0
        for state in launcher_states
    )
    intervals: list[tuple[datetime, datetime]] = []
    try:
        for state in launcher_states:
            started = parse_timestamp(state.get("started_at"))
            finished = parse_timestamp(state.get("finished_at"))
            if finished < started:
                raise ValueError(f"结束时间早于开始时间：{state.get('run_id')}")
            intervals.append((started, finished))
    except (TypeError, ValueError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    strictly_serial = len(intervals) == 3 and all(
        previous[1] <= current[0] for previous, current in zip(intervals, intervals[1:])
    )
    identities_exact = exactly_three and run_ids == expected_run_ids
    return {
        "valid": (
            exactly_three
            and identities_exact
            and discovered_identities_exact
            and outputs_match
            and statuses_finished
            and strictly_serial
            and not errors
        ),
        "exactly_three_run_identities": identities_exact,
        "discovered_run_identities_exact": discovered_identities_exact,
        "output_roots_match": outputs_match,
        "launcher_statuses_finished": statuses_finished,
        "strictly_serial": strictly_serial,
        "run_ids": run_ids,
        "errors": errors,
    }


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def count_exact_payload_decrypt_error(value: Any) -> int:
    if isinstance(value, dict):
        return sum(count_exact_payload_decrypt_error(child) for child in value.values())
    if isinstance(value, list):
        return sum(count_exact_payload_decrypt_error(child) for child in value)
    return int(isinstance(value, str) and value == "payload_decrypt_error")


def scan_qlog_payload_decrypt_errors(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        try:
            total += count_exact_payload_decrypt_error(json.loads(raw))
            continue
        except json.JSONDecodeError:
            pass
        parsed_lines = 0
        for line in raw.splitlines():
            candidate = line.lstrip("\x1e").strip()
            if not candidate:
                continue
            try:
                total += count_exact_payload_decrypt_error(json.loads(candidate))
                parsed_lines += 1
            except json.JSONDecodeError:
                continue
        if parsed_lines == 0:
            raise RuntimeError(f"qlog 无法解析：{path}")
    return total


def stable_four_tuple(
    connection_id: str,
    contract_version: str,
    schedule_mode: str = EXPECTED_SCHEDULE_MODE,
) -> dict[str, Any]:
    return {
        "contract_version": contract_version,
        "connection_id": connection_id,
        "schedule_mode": schedule_mode,
        "client_to_proxy": {
            "source_host": EXPECTED_ENDPOINTS["client"][0],
            "source_port": EXPECTED_ENDPOINTS["client"][1],
            "destination_host": EXPECTED_ENDPOINTS["proxy_listen"][0],
            "destination_port": EXPECTED_ENDPOINTS["proxy_listen"][1],
        },
        "proxy_to_server": {
            "source_host": EXPECTED_ENDPOINTS["proxy_upstream"][0],
            "source_port": EXPECTED_ENDPOINTS["proxy_upstream"][1],
            "destination_host": EXPECTED_ENDPOINTS["reference_server"][0],
            "destination_port": EXPECTED_ENDPOINTS["reference_server"][1],
        },
    }


def expected_directional_max_datagram_bytes(
    collection_config: dict[str, Any], implementation: str
) -> dict[str, int]:
    deterministic = collection_config.get("determinism_contract")
    network = collection_config.get("network_contract")
    reference_server = collection_config.get("reference_server")
    if not isinstance(deterministic, dict) or not isinstance(network, dict):
        raise ValueError("v7 确定性或网络合同缺失")
    if deterministic.get("contract_version") != "flow_probe_r2_quic_four_tuple_contract_v7":
        raise ValueError("方向级数据报审计只适用于 v7 合同")
    if network.get("directional_max_datagram_rule") != "actual_sender_implementation_v1":
        raise ValueError("v7 方向级数据报规则不符合冻结值")
    if not isinstance(reference_server, dict):
        raise ValueError("v7 参考服务端合同缺失")
    limits = network.get("max_datagram_bytes_by_implementation")
    if limits != {"aioquic": 1_200, "quiche": 1_350}:
        raise ValueError("v7 实现级数据报上限不符合冻结值")
    server_implementation = str(reference_server.get("implementation", ""))
    if implementation not in limits or server_implementation not in limits:
        raise ValueError("v7 实际发送端实现不在冻结映射中")
    return {
        "client_to_server": int(limits[implementation]),
        "server_to_client": int(limits[server_implementation]),
    }


def max_datagram_for_direction(parameters: dict[str, Any], direction_name: str) -> int:
    directional = parameters.get("max_datagram_bytes_by_direction")
    if directional is None:
        return int(parameters["max_datagram_bytes"])
    if not isinstance(directional, dict) or set(directional) != {
        "client_to_server",
        "server_to_client",
    }:
        raise ValueError("方向级最大数据报统计缺失或不完整")
    maximum = int(directional[direction_name])
    if not 1 <= maximum <= 65_535:
        raise ValueError("方向级最大数据报统计超出范围")
    return maximum


def audit_directional_datagram_binding(
    collection_config: dict[str, Any],
    implementation: str,
    impairment: dict[str, Any],
    proxy_ready: dict[str, Any],
    proxy_stats: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    expected: dict[str, int] = {}
    try:
        expected = expected_directional_max_datagram_bytes(collection_config, implementation)
        parameters = proxy_stats.get("parameters")
        directions = proxy_stats.get("directions")
        if not isinstance(parameters, dict) or not isinstance(directions, dict):
            raise ValueError("代理方向级统计缺失")
        checks = {
            "impairment_exact": impairment.get("max_datagram_bytes_by_direction") == expected,
            "ready_exact": proxy_ready.get("max_datagram_bytes_by_direction") == expected,
            "stats_parameters_exact": parameters.get("max_datagram_bytes_by_direction") == expected,
            "direction_stats_exact": all(
                isinstance(directions.get(name), dict)
                and directions[name].get("max_datagram_bytes") == maximum
                for name, maximum in expected.items()
            ),
        }
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "expected": expected,
        "checks": checks,
        "errors": errors,
    }


def audit_v4_event_log(
    event_path: Path,
    proxy_stats: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    results: dict[str, dict[str, Any]] = {}
    try:
        parameters = proxy_stats["parameters"]
        rate_bits_per_second = int(parameters["rate_bits_per_second"])
        delay_us = int(parameters["delay_us"])
        capacity = int(parameters["queue_capacity_bytes"])
        margin = int(parameters["queue_margin_max_bytes"])
        max_datagram = int(parameters["max_datagram_bytes"])
        rounding_per_packet = int(
            parameters.get("serialization_rounding_tolerance_us_per_packet", 1)
        )
        if (
            parameters.get("queue_capacity_unit") != "bytes"
            or capacity != EXPECTED_V4_QUEUE_CAPACITY_BYTES
            or float(parameters.get("queue_margin_ratio")) != 0.8
            or margin != EXPECTED_V4_QUEUE_MARGIN_MAX_BYTES
            or parameters.get("queue_margin_role") != "diagnostic_only"
            or max_datagram not in EXPECTED_V4_MAX_DATAGRAM_BYTES
            or int(parameters.get("udp_receive_buffer_bytes")) != 65_535
            or rate_bits_per_second != 20_000_000
            or delay_us != 50_000
        ):
            raise ValueError("v4 代理参数不符合冻结字节容量合同")
        rows = []
        for line_number, raw in enumerate(
            event_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not raw.strip():
                continue
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise TypeError(f"事件行不是对象：{line_number}")
            rows.append(row)
        sequences = [int(row["sequence"]) for row in rows]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("事件全局序号不连续")

        direction_stats = proxy_stats["directions"]
        for direction_name, reported in direction_stats.items():
            max_datagram = max_datagram_for_direction(parameters, direction_name)
            service_backlog = 0
            waiting_bytes = 0
            in_service_bytes = 0
            delay_inflight = 0
            peak_service = 0
            peak_delay = 0
            max_batch_packets = 0
            max_batch_bytes = 0
            max_lag = 0
            scheduled_packets = 0
            scheduled_bytes = 0
            forwarded_packets = 0
            forwarded_bytes = 0
            random_drop_packets = 0
            random_drop_bytes = 0
            queue_drop_packets = 0
            queue_drop_bytes = 0
            send_error_packets = 0
            send_error_bytes = 0
            serialization_sum_us = 0
            previous_finish_us: int | None = None
            pending: dict[int, dict[str, int | bool]] = {}
            direction_rows = [row for row in rows if row.get("direction") == direction_name]
            for row in direction_rows:
                action = str(row.get("action"))
                if action == "receive_batch_completed":
                    max_batch_packets = max(max_batch_packets, int(row["batch_packets"]))
                    max_batch_bytes = max(max_batch_bytes, int(row["batch_bytes"]))
                    continue
                if action == "contract_failed":
                    raise ValueError(f"{direction_name} 出现合同失败事件：{row.get('reason')}")
                datagram_bytes = int(row["bytes"])
                if datagram_bytes <= 0 or datagram_bytes > max_datagram:
                    raise ValueError(f"{direction_name} 数据报字节超出冻结范围")
                packet_sequence = int(row["packet_sequence"])
                if action == "scheduled":
                    before = int(row["service_backlog_before_bytes"])
                    after = int(row["service_backlog_after_bytes"])
                    waiting_before = int(row["waiting_before_bytes"])
                    waiting_after = int(row["waiting_after_bytes"])
                    in_service_before = int(row["in_service_before_bytes"])
                    in_service_after = int(row["in_service_after_bytes"])
                    if before != service_backlog or after != before + datagram_bytes:
                        raise ValueError(f"{direction_name} 待服务字节准入收据不闭合")
                    if waiting_before != waiting_bytes or in_service_before != in_service_bytes:
                        raise ValueError(f"{direction_name} 服务分类准入前收据不闭合")
                    classification = row.get("service_classification")
                    if classification == "in_service":
                        expected_waiting = waiting_bytes
                        expected_in_service = in_service_bytes + datagram_bytes
                    elif classification == "waiting":
                        expected_waiting = waiting_bytes + datagram_bytes
                        expected_in_service = in_service_bytes
                    else:
                        raise ValueError(f"{direction_name} 服务分类缺失")
                    if waiting_after != expected_waiting or in_service_after != expected_in_service:
                        raise ValueError(f"{direction_name} 服务分类准入后收据不闭合")
                    if after > capacity or row.get("admitted") is not True:
                        raise ValueError(f"{direction_name} 字节容量准入非法")
                    arrival_us = int(row["arrival_offset_us"])
                    start_us = int(row["serialization_start_offset_us"])
                    finish_us = int(row["serialization_finish_offset_us"])
                    release_us = int(row["scheduled_release_offset_us"])
                    expected_start = max(arrival_us, previous_finish_us or arrival_us)
                    if abs(start_us - expected_start) > rounding_per_packet:
                        raise ValueError(f"{direction_name} 不是工作保守服务时间线")
                    expected_serialization_us = datagram_bytes * 8_000_000 / rate_bits_per_second
                    if (
                        abs((finish_us - start_us) - expected_serialization_us)
                        > rounding_per_packet
                    ):
                        raise ValueError(f"{direction_name} 单报文序列化时长不闭合")
                    jitter_us = int(row.get("jitter_us", 0))
                    if abs((release_us - finish_us) - (delay_us + jitter_us)) > 1:
                        raise ValueError(f"{direction_name} 服务与传播阶段未分离")
                    service_backlog = after
                    waiting_bytes = waiting_after
                    in_service_bytes = in_service_after
                    peak_service = max(peak_service, service_backlog)
                    previous_finish_us = finish_us
                    scheduled_packets += 1
                    scheduled_bytes += datagram_bytes
                    serialization_sum_us += int(row["serialization_us"])
                    pending[packet_sequence] = {
                        "bytes": datagram_bytes,
                        "start_us": start_us,
                        "finish_us": finish_us,
                        "release_us": release_us,
                        "service_completed": False,
                        "forwarded": False,
                    }
                elif action == "service_completed":
                    item = pending.get(packet_sequence)
                    if item is None or item["service_completed"]:
                        raise ValueError(f"{direction_name} 服务完成事件无对应准入")
                    if int(row["service_completion_offset_us"]) != int(item["finish_us"]):
                        raise ValueError(f"{direction_name} 服务完成节奏收据不一致")
                    service_before = int(row["service_backlog_before_bytes"])
                    service_after = int(row["service_backlog_after_bytes"])
                    waiting_before = int(row["waiting_before_bytes"])
                    waiting_after = int(row["waiting_after_bytes"])
                    in_service_before = int(row["in_service_before_bytes"])
                    in_service_after = int(row["in_service_after_bytes"])
                    delay_before = int(row["delay_inflight_before_bytes"])
                    delay_after = int(row["delay_inflight_after_bytes"])
                    if (
                        service_before != service_backlog
                        or service_after != service_before - datagram_bytes
                        or waiting_before != waiting_bytes
                        or waiting_after != waiting_bytes
                        or in_service_before != in_service_bytes
                        or in_service_after != 0
                        or delay_before != delay_inflight
                        or delay_after != delay_before + datagram_bytes
                    ):
                        raise ValueError(f"{direction_name} 服务完成收据不闭合")
                    service_backlog = service_after
                    waiting_bytes = waiting_after
                    in_service_bytes = in_service_after
                    delay_inflight = delay_after
                    peak_delay = max(peak_delay, delay_inflight)
                    item["service_completed"] = True
                elif action == "service_started":
                    item = pending.get(packet_sequence)
                    if item is None or item["service_completed"] or item["forwarded"]:
                        raise ValueError(f"{direction_name} 服务开始事件无等待报文")
                    if int(row["service_start_offset_us"]) != int(item["start_us"]):
                        raise ValueError(f"{direction_name} 服务开始节奏收据不一致")
                    service_before = int(row["service_backlog_before_bytes"])
                    service_after = int(row["service_backlog_after_bytes"])
                    waiting_before = int(row["waiting_before_bytes"])
                    waiting_after = int(row["waiting_after_bytes"])
                    in_service_before = int(row["in_service_before_bytes"])
                    in_service_after = int(row["in_service_after_bytes"])
                    if (
                        service_before != service_backlog
                        or service_after != service_backlog
                        or waiting_before != waiting_bytes
                        or waiting_after != waiting_before - datagram_bytes
                        or in_service_before != in_service_bytes
                        or in_service_after != datagram_bytes
                    ):
                        raise ValueError(f"{direction_name} 等待到服务转换收据不闭合")
                    waiting_bytes = waiting_after
                    in_service_bytes = in_service_after
                elif action in {"forwarded", "send_failed"}:
                    item = pending.get(packet_sequence)
                    if item is None or not item["service_completed"] or item["forwarded"]:
                        raise ValueError(f"{direction_name} 转发事件无已完成服务报文")
                    if int(row["scheduled_release_offset_us"]) != int(item["release_us"]):
                        raise ValueError(f"{direction_name} 计划释放节奏收据不一致")
                    delay_before = int(row["delay_inflight_before_bytes"])
                    delay_after = int(row["delay_inflight_after_bytes"])
                    if (
                        delay_before != delay_inflight
                        or delay_after != delay_before - datagram_bytes
                    ):
                        raise ValueError(f"{direction_name} 传播阶段出队收据不闭合")
                    delay_inflight = delay_after
                    lag_us = int(row["actual_forwarding_lag_us"])
                    if (
                        int(row["forwarded_offset_us"]) - int(row["scheduled_release_offset_us"])
                        != lag_us
                    ):
                        raise ValueError(f"{direction_name} 实际转发滞后收据不一致")
                    if lag_us < 0:
                        raise ValueError(f"{direction_name} 实际转发早于计划释放")
                    max_lag = max(max_lag, lag_us)
                    if action == "forwarded":
                        forwarded_packets += 1
                        forwarded_bytes += datagram_bytes
                    else:
                        send_error_packets += 1
                        send_error_bytes += datagram_bytes
                    item["forwarded"] = True
                elif action == "dropped":
                    if (
                        int(row["service_backlog_before_bytes"]) != service_backlog
                        or int(row["service_backlog_after_bytes"]) != service_backlog
                        or int(row["waiting_before_bytes"]) != waiting_bytes
                        or int(row["waiting_after_bytes"]) != waiting_bytes
                        or int(row["in_service_before_bytes"]) != in_service_bytes
                        or int(row["in_service_after_bytes"]) != in_service_bytes
                        or row.get("admitted") is not False
                    ):
                        raise ValueError(f"{direction_name} 丢弃收据改变了待服务字节")
                    reason = row.get("reason")
                    if reason == "deterministic_random_loss":
                        random_drop_packets += 1
                        random_drop_bytes += datagram_bytes
                    elif reason == "userspace_queue_limit_bytes":
                        if service_backlog + datagram_bytes <= capacity:
                            raise ValueError(f"{direction_name} 未超过容量却发生队列丢弃")
                        queue_drop_packets += 1
                        queue_drop_bytes += datagram_bytes
                    else:
                        raise ValueError(f"{direction_name} 存在非预期丢弃原因：{reason}")
                else:
                    raise ValueError(f"{direction_name} 未知事件动作：{action}")

            received_packets = scheduled_packets + random_drop_packets + queue_drop_packets
            received_bytes = scheduled_bytes + random_drop_bytes + queue_drop_bytes
            expected_serialization_sum_us = scheduled_bytes * 8_000_000 / rate_bits_per_second
            serialization_tolerance = scheduled_packets * rounding_per_packet
            recomputed = {
                "received_packets": received_packets,
                "received_bytes": received_bytes,
                "scheduled_packets": scheduled_packets,
                "scheduled_bytes": scheduled_bytes,
                "forwarded_packets": forwarded_packets,
                "forwarded_bytes": forwarded_bytes,
                "random_drop_packets": random_drop_packets,
                "random_drop_bytes": random_drop_bytes,
                "queue_drop_packets": queue_drop_packets,
                "queue_drop_bytes": queue_drop_bytes,
                "send_error_packets": send_error_packets,
                "send_error_bytes": send_error_bytes,
                "peak_service_backlog_bytes": peak_service,
                "peak_delay_inflight_bytes": peak_delay,
                "waiting_bytes_at_shutdown": waiting_bytes,
                "in_service_bytes_at_shutdown": in_service_bytes,
                "service_backlog_bytes_at_shutdown": service_backlog,
                "delay_inflight_bytes_at_shutdown": delay_inflight,
                "max_receive_batch_packets": max_batch_packets,
                "max_receive_batch_bytes": max_batch_bytes,
                "max_actual_forwarding_lag_us": max_lag,
                "serialization_sum_us": serialization_sum_us,
                "serialization_expected_us": expected_serialization_sum_us,
            }
            compared_fields = [
                key
                for key in recomputed
                if key in reported and not key.startswith("serialization_")
            ]
            mismatches = [
                key for key in compared_fields if int(reported[key]) != int(recomputed[key])
            ]
            if mismatches:
                raise ValueError(f"{direction_name} 代理摘要与事件重放不一致：{mismatches}")
            if abs(serialization_sum_us - expected_serialization_sum_us) > serialization_tolerance:
                raise ValueError(f"{direction_name} 序列化积分不闭合")
            if received_packets != int(reported["received_packets"]) or received_bytes != int(
                reported["received_bytes"]
            ):
                raise ValueError(f"{direction_name} 接收包/字节守恒不闭合")
            if scheduled_packets != forwarded_packets + send_error_packets + int(
                reported.get("queued_packets_at_shutdown", 0)
            ):
                raise ValueError(f"{direction_name} 调度包守恒不闭合")
            recomputed["queue_diagnostic_threshold_bytes"] = margin
            recomputed["queue_diagnostic_passed"] = peak_service <= margin
            results[direction_name] = recomputed
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(results) and not errors,
        "directions": results,
        "errors": errors,
    }


def audit_run(output_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    evidence: dict[str, Any] = {}
    result = {
        "output_root": str(output_root),
        "checks": checks,
        "evidence": evidence,
        "errors": errors,
    }
    try:
        if not output_root.is_dir():
            raise FileNotFoundError(f"输出根不存在：{output_root}")
        run_state = read_json(output_root / "run-state.json")
        collection_config_path = output_root / "collection-config.json"
        collection_config = read_json(collection_config_path)
        collection_config_sha256 = sha256_file(collection_config_path)

        connections_root = output_root / "connections"
        if not connections_root.is_dir():
            raise FileNotFoundError(f"连接目录不存在：{connections_root}")
        connection_roots = sorted(path for path in connections_root.iterdir() if path.is_dir())
        if len(connection_roots) != 1:
            raise RuntimeError(f"连接目录必须恰好一个：{len(connection_roots)}")
        connection_root = connection_roots[0]
        state = read_json(connection_root / "status.json")
        impairment_path = connection_root / "impairment-config.json"
        four_tuple_path = connection_root / "four-tuple-contract.json"
        endpoint_path = connection_root / "endpoint-contract.json"
        proxy_ready_path = connection_root / "proxy-ready.json"
        proxy_stats_path = connection_root / "proxy-stats.json"
        proxy_event_path = connection_root / "proxy-events.jsonl"
        exit_path = connection_root / "exit-code.json"
        impairment = read_json(impairment_path)
        four_tuple = read_json(four_tuple_path)
        endpoint = read_json(endpoint_path)
        proxy_ready = read_json(proxy_ready_path)
        proxy_stats = read_json(proxy_stats_path)
        exit_codes = read_json(exit_path)
        artifact_audit = audit_artifact_manifest(
            connection_root,
            state.get("artifacts"),
        )

        impairment_sha256 = sha256_file(impairment_path)
        four_tuple_sha256 = sha256_file(four_tuple_path)
        connection_id = str(state.get("connection_id", ""))
        response_root = connection_root / "response"
        responses = sorted(path for path in response_root.iterdir() if path.is_file())
        if len(responses) != 1:
            raise RuntimeError(f"响应文件必须恰好一个：{len(responses)}")
        response = responses[0]
        response_sha256 = sha256_file(response)
        qlog_root = connection_root / "qlog"
        qlogs = sorted(
            path for path in qlog_root.iterdir() if path.is_file() and path.stat().st_size > 0
        )
        if not qlogs:
            raise RuntimeError("qlog 文件缺失")
        payload_decrypt_error = scan_qlog_payload_decrypt_errors(qlogs)

        directions = proxy_stats.get("directions")
        if not isinstance(directions, dict):
            raise TypeError("代理方向统计缺失")
        direction_rows = [
            directions["client_to_server"],
            directions["server_to_client"],
        ]
        random_drop_packets = sum(int(row["random_drop_packets"]) for row in direction_rows)
        queue_drop_packets = sum(int(row["queue_drop_packets"]) for row in direction_rows)
        send_error_packets = sum(int(row["send_error_packets"]) for row in direction_rows)
        random_drop_bytes = sum(int(row.get("random_drop_bytes", 0)) for row in direction_rows)
        queue_drop_bytes = sum(int(row.get("queue_drop_bytes", 0)) for row in direction_rows)
        send_error_bytes = sum(int(row.get("send_error_bytes", 0)) for row in direction_rows)
        queued_packets_at_shutdown = sum(
            int(row["queued_packets_at_shutdown"]) for row in direction_rows
        )
        service_backlog_bytes_at_shutdown = sum(
            int(row.get("service_backlog_bytes_at_shutdown", 0)) for row in direction_rows
        )
        waiting_bytes_at_shutdown = sum(
            int(row.get("waiting_bytes_at_shutdown", 0)) for row in direction_rows
        )
        in_service_bytes_at_shutdown = sum(
            int(row.get("in_service_bytes_at_shutdown", 0)) for row in direction_rows
        )
        delay_inflight_bytes_at_shutdown = sum(
            int(row.get("delay_inflight_bytes_at_shutdown", 0)) for row in direction_rows
        )
        scheduled_packets_at_shutdown = int(proxy_stats["scheduled_packets_at_shutdown"])
        scheduled_bytes_at_shutdown = int(proxy_stats.get("scheduled_bytes_at_shutdown", 0))

        deterministic_contract = collection_config.get("determinism_contract")
        if not isinstance(deterministic_contract, dict):
            raise TypeError("确定性合同缺失")
        expected_schedule_mode = str(deterministic_contract["schedule_mode"])
        is_v4 = expected_schedule_mode == EXPECTED_V4_SCHEDULE_MODE
        is_v7 = (
            deterministic_contract.get("contract_version")
            == "flow_probe_r2_quic_four_tuple_contract_v7"
        )
        expected_four_tuple = stable_four_tuple(
            connection_id,
            str(deterministic_contract["contract_version"]),
            expected_schedule_mode,
        )
        v4_event_audit = (
            audit_v4_event_log(proxy_event_path, proxy_stats)
            if is_v4
            else {"valid": True, "directions": {}, "errors": []}
        )
        fixed_endpoints = state.get("fixed_endpoints")
        direction_seeds = state.get("direction_seeds")
        direction_seed_contracts = deterministic_contract.get("direction_seeds_by_target_index")
        if not isinstance(direction_seed_contracts, dict):
            expected_direction_seeds = EXPECTED_DIRECTION_SEEDS
        else:
            implementation_targets = {
                str(item["implementation"]): str(item["target_connection_index"])
                for item in deterministic_contract["gate_runs"]
            }
            expected_direction_seeds = direction_seed_contracts[
                implementation_targets[str(state.get("implementation"))]
            ]
        exit_code_values = {
            name: int(exit_codes[name])
            for name in (
                "client_exit",
                "capture_exit",
                "proxy_exit",
                "server_exit",
            )
        }
        server_raw_exit = int(exit_codes["server_raw_exit"])
        server_stop_receipt = exit_codes.get("server_stop_receipt")
        if not isinstance(server_stop_receipt, dict):
            raise TypeError("服务端停止收据缺失")
        controlled_server_sigterm = (
            server_raw_exit in (-signal.SIGTERM, 128 + signal.SIGTERM)
            and exit_code_values["server_exit"] == server_raw_exit
            and server_stop_receipt.get("raw_exit") == server_raw_exit
            and server_stop_receipt.get("controller_sent_signal") is True
            and server_stop_receipt.get("poll_before_controller_signal") is None
            and server_stop_receipt.get("controller_signal") == signal.SIGTERM
            and timestamp_is_valid(server_stop_receipt.get("controller_signal_sent_at"))
        )
        natural_server_exit = (
            server_raw_exit == 0
            and exit_code_values["server_exit"] == 0
            and server_stop_receipt.get("raw_exit") == 0
            and server_stop_receipt.get("controller_sent_signal") is False
            and server_stop_receipt.get("controller_signal_sent_at") is None
        )
        network_contract = collection_config.get("network_contract", {})
        expected_max_datagram = 1_200 if state.get("implementation") == "aioquic" else 1_350
        directional_datagram_audit = (
            audit_directional_datagram_binding(
                collection_config,
                str(state.get("implementation")),
                impairment,
                proxy_ready,
                proxy_stats,
            )
            if is_v7
            else {"valid": True, "expected": {}, "checks": {}, "errors": []}
        )
        if is_v4:
            frozen_network_contract = (
                network_contract.get("queue_capacity_unit") == "bytes"
                and network_contract.get("queue_capacity_bytes") == EXPECTED_V4_QUEUE_CAPACITY_BYTES
                and network_contract.get("queue_margin_ratio") == 0.8
                and network_contract.get("queue_margin_max_bytes")
                == EXPECTED_V4_QUEUE_MARGIN_MAX_BYTES
                and network_contract.get("queue_margin_role") == "diagnostic_only"
                and network_contract.get("max_datagram_bytes_by_implementation")
                == {"aioquic": 1_200, "quiche": 1_350}
                and network_contract.get("udp_receive_buffer_bytes") == 65_535
                and proxy_stats.get("parameters", {}).get("max_datagram_bytes")
                == expected_max_datagram
                and directional_datagram_audit["valid"]
            )
        else:
            frozen_network_contract = network_contract.get("queue_limit_packets") == 1000
        checks.update(
            {
                "natural_completion": (
                    run_state.get("status") == "finished"
                    and state.get("status") == "finished"
                    and state.get("client_natural_completion") is True
                ),
                "frozen_scientific_parameters": (
                    state.get("implementation") in {"aioquic", "quiche"}
                    and state.get("profile")
                    == {
                        "id": "p03",
                        "delay_ms": 50,
                        "jitter_ms": 0.0,
                        "loss_percent": 0.0,
                        "rate_mbit": 20,
                        "seed": 43,
                    }
                    and state.get("payload") == {"id": "bulk", "bytes": EXPECTED_RESPONSE_BYTES}
                    and state.get("seed") == 43
                    and collection_config.get("client_timeout_seconds") == 240
                    and frozen_network_contract
                ),
                "response_bytes": response.stat().st_size == EXPECTED_RESPONSE_BYTES,
                "response_state_receipt": (
                    state.get("response", {}).get("bytes") == EXPECTED_RESPONSE_BYTES
                    and state.get("response", {}).get("sha256") == response_sha256
                ),
                "payload_decrypt_error_zero": payload_decrypt_error == 0,
                "qlog_state_receipt": (
                    state.get("qlog_field_audit", {}).get("payload_decrypt_error")
                    == payload_decrypt_error
                ),
                "non_server_exit_codes_zero": all(
                    exit_code_values[name] == 0
                    for name in ("client_exit", "capture_exit", "proxy_exit")
                ),
                "server_exit_contract_valid": (natural_server_exit or controlled_server_sigterm),
                "server_exit_receipt_bound": (
                    state.get("server_stop_receipt") == server_stop_receipt
                    and state.get("exit_codes", {}).get("server_exit") == server_raw_exit
                    and state.get("exit_codes", {}).get("server_raw_exit") == server_raw_exit
                ),
                "artifact_manifest_exact": artifact_audit["valid"],
                "random_drop_zero": random_drop_packets == 0,
                "queue_drop_zero": queue_drop_packets == 0,
                "send_error_zero": send_error_packets == 0,
                "drop_and_send_error_bytes_zero": (
                    not is_v4
                    or (random_drop_bytes == 0 and queue_drop_bytes == 0 and send_error_bytes == 0)
                ),
                "shutdown_queue_zero": (
                    queued_packets_at_shutdown == 0
                    and scheduled_packets_at_shutdown == 0
                    and scheduled_bytes_at_shutdown == 0
                    and service_backlog_bytes_at_shutdown == 0
                    and waiting_bytes_at_shutdown == 0
                    and in_service_bytes_at_shutdown == 0
                    and delay_inflight_bytes_at_shutdown == 0
                ),
                "v4_event_replay_exact": v4_event_audit["valid"],
                "directional_datagram_binding_exact": directional_datagram_audit["valid"],
                "collection_config_hash_bound": (
                    state.get("collection_config_sha256") == collection_config_sha256
                    and impairment.get("collection_config_sha256") == collection_config_sha256
                    and endpoint.get("collection_config_sha256") == collection_config_sha256
                ),
                "impairment_config_hash_bound": (
                    state.get("impairment_config_sha256") == impairment_sha256
                    and endpoint.get("impairment_config_sha256") == impairment_sha256
                    and proxy_ready.get("config_sha256") == impairment_sha256
                    and proxy_stats.get("config_sha256") == impairment_sha256
                ),
                "four_tuple_hash_bound": (
                    state.get("four_tuple_contract_sha256") == four_tuple_sha256
                    and impairment.get("four_tuple_contract_sha256") == four_tuple_sha256
                    and endpoint.get("four_tuple_contract_sha256") == four_tuple_sha256
                ),
                "four_tuple_exact": four_tuple == expected_four_tuple,
                "direction_seeds_exact": (
                    direction_seeds == expected_direction_seeds
                    and impairment.get("direction_seeds") == expected_direction_seeds
                    and {
                        name: proxy_stats["directions"][name]["seed"]
                        for name in expected_direction_seeds
                    }
                    == expected_direction_seeds
                ),
                "fixed_endpoints_exact": fixed_endpoints == EXPECTED_ENDPOINTS,
                "observed_endpoints_exact": (
                    endpoint.get("expected_client_endpoint") == EXPECTED_ENDPOINTS["client"]
                    and endpoint.get("observed_client_endpoint") == EXPECTED_ENDPOINTS["client"]
                    and endpoint.get("expected_proxy_listen_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_listen"]
                    and endpoint.get("observed_proxy_listen_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_listen"]
                    and endpoint.get("expected_proxy_upstream_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_upstream"]
                    and endpoint.get("observed_proxy_upstream_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_upstream"]
                    and endpoint.get("expected_reference_server_endpoint")
                    == EXPECTED_ENDPOINTS["reference_server"]
                    and endpoint.get("observed_reference_server_endpoint")
                    == EXPECTED_ENDPOINTS["reference_server"]
                ),
                "schedule_mode_exact": all(
                    value == expected_schedule_mode
                    for value in (
                        state.get("schedule_mode"),
                        impairment.get("schedule_mode"),
                        four_tuple.get("schedule_mode"),
                        endpoint.get("schedule_mode"),
                        proxy_ready.get("schedule_mode"),
                        proxy_stats.get("schedule_mode"),
                    )
                ),
                "port_exclusivity_receipts": (
                    endpoint.get("port_availability_before", {}).get("exclusive_bind_succeeded")
                    is True
                    and endpoint.get("port_availability_after", {}).get("exclusive_bind_succeeded")
                    is True
                ),
                "proxy_finished_without_contract_error": (
                    proxy_stats.get("status") == "finished"
                    and proxy_stats.get("contract_error") is None
                ),
            }
        )
        endpoint_schedule_value = {
            "four_tuple": four_tuple,
            "fixed_endpoints": fixed_endpoints,
            "direction_seeds": direction_seeds,
            "schedule_mode": state.get("schedule_mode"),
        }
        evidence.update(
            {
                "connection_id": connection_id,
                "collection_config_sha256": collection_config_sha256,
                "impairment_config_sha256": impairment_sha256,
                "four_tuple_contract_sha256": four_tuple_sha256,
                "direction_seeds_sha256": canonical_sha256(direction_seeds),
                "endpoint_schedule_sha256": canonical_sha256(endpoint_schedule_value),
                "response_bytes": response.stat().st_size,
                "response_sha256": response_sha256,
                "payload_decrypt_error": payload_decrypt_error,
                "exit_codes": exit_code_values,
                "server_raw_exit": server_raw_exit,
                "server_stop_receipt": server_stop_receipt,
                "artifact_manifest_audit": artifact_audit,
                "implementation": state.get("implementation"),
                "directional_datagram_audit": directional_datagram_audit,
                "random_drop_packets": random_drop_packets,
                "random_drop_bytes": random_drop_bytes,
                "queue_drop_packets": queue_drop_packets,
                "queue_drop_bytes": queue_drop_bytes,
                "send_error_packets": send_error_packets,
                "send_error_bytes": send_error_bytes,
                "queued_packets_at_shutdown": queued_packets_at_shutdown,
                "scheduled_packets_at_shutdown": scheduled_packets_at_shutdown,
                "scheduled_bytes_at_shutdown": scheduled_bytes_at_shutdown,
                "service_backlog_bytes_at_shutdown": (service_backlog_bytes_at_shutdown),
                "waiting_bytes_at_shutdown": waiting_bytes_at_shutdown,
                "in_service_bytes_at_shutdown": in_service_bytes_at_shutdown,
                "delay_inflight_bytes_at_shutdown": delay_inflight_bytes_at_shutdown,
                "v4_event_audit": v4_event_audit,
                "schedule_mode": state.get("schedule_mode"),
            }
        )
    except (KeyError, IndexError, OSError, TypeError, ValueError, RuntimeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    result["all_checks_passed"] = bool(checks) and all(checks.values()) and not errors
    return result


def cross_run_checks(runs: list[dict[str, Any]]) -> dict[str, bool]:
    evidence_rows = [run["evidence"] for run in runs]

    def one_value(field: str) -> bool:
        values = [row.get(field) for row in evidence_rows]
        return all(value is not None for value in values) and len(set(values)) == 1

    return {
        "collection_config_sha256_consistent": one_value("collection_config_sha256"),
        "schedule_mode_consistent": one_value("schedule_mode"),
        "response_sha256_consistent": one_value("response_sha256"),
        "aioquic_and_quiche_covered": {row.get("implementation") for row in evidence_rows}
        == {"aioquic", "quiche"},
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-roots",
        type=Path,
        nargs=3,
        required=True,
        metavar=("RUN1", "RUN2", "RUN3"),
    )
    parser.add_argument("--summary-path", type=Path, required=True)
    parser.add_argument(
        "--launcher-status-paths",
        type=Path,
        nargs=3,
        required=True,
        metavar=("LAUNCHER1", "LAUNCHER2", "LAUNCHER3"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    summary_path = args.summary_path.resolve()
    if summary_path.exists() or summary_path.with_suffix(summary_path.suffix + ".tmp").exists():
        print(NO_GO_STATUS, flush=True)
        return 2
    roots = [path.resolve() for path in args.output_roots]
    distinct_roots = len(set(roots)) == 3
    runs = [audit_run(root) for root in roots]
    launcher_states = [read_json(path.resolve()) for path in args.launcher_status_paths]
    expected_run_ids: list[str] = []
    expected_implementations: list[str] = []
    run_id_prefix = ""
    launcher_schema_version = "flow_probe_r2_quic_launcher_v3"
    summary_schema_version = "flow_probe_r2_quic_determinism_gate_v3"
    try:
        first_config = read_json(roots[0] / "collection-config.json")
        gate_runs = first_config["determinism_contract"]["gate_runs"]
        expected_run_ids = [str(item["run_id"]) for item in gate_runs]
        expected_implementations = [str(item["implementation"]) for item in gate_runs]
        run_id_prefix = str(first_config["determinism_contract"]["run_id_prefix"])
        launcher_schema_version = str(
            first_config["determinism_contract"].get(
                "launcher_schema_version",
                "flow_probe_r2_quic_launcher_v3",
            )
        )
        if first_config["determinism_contract"].get("schedule_mode") == EXPECTED_V4_SCHEDULE_MODE:
            summary_schema_version = "flow_probe_r2_quic_determinism_gate_v4"
    except (KeyError, OSError, TypeError, ValueError):
        expected_run_ids = []
        expected_implementations = []
        run_id_prefix = ""
        launcher_schema_version = "flow_probe_r2_quic_launcher_v3"
    launcher_status_paths = [path.resolve() for path in args.launcher_status_paths]
    launcher_status_paths_exact = [
        path.parent.name for path in launcher_status_paths
    ] == expected_run_ids
    launcher_parents = {path.parent.parent for path in launcher_status_paths}
    discovered_run_ids: list[str] = []
    if len(launcher_parents) == 1 and run_id_prefix:
        launcher_parent = next(iter(launcher_parents))
        discovered_run_ids = sorted(
            child.name
            for child in launcher_parent.iterdir()
            if child.is_dir()
            and child.name.startswith(run_id_prefix)
            and (child / "status.json").is_file()
        )
    launcher_audit = audit_launcher_contract(
        launcher_states,
        roots,
        expected_run_ids,
        discovered_run_ids,
        launcher_schema_version,
    )
    cross_checks = cross_run_checks(runs)
    run_contract_implementations_exact = [
        run["evidence"].get("implementation") for run in runs
    ] == expected_implementations
    all_conditions = (
        distinct_roots
        and launcher_audit["valid"]
        and launcher_status_paths_exact
        and run_contract_implementations_exact
        and all(run["all_checks_passed"] for run in runs)
        and all(cross_checks.values())
    )
    status = GO_STATUS if all_conditions else NO_GO_STATUS
    summary = {
        "schema_version": summary_schema_version,
        "status": status,
        "output_roots": [str(root) for root in roots],
        "three_distinct_output_roots": distinct_roots,
        "runs": runs,
        "launcher_audit": launcher_audit,
        "launcher_status_paths_exact": launcher_status_paths_exact,
        "run_contract_implementations_exact": run_contract_implementations_exact,
        "cross_run_checks": cross_checks,
        "all_conditions_passed": all_conditions,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(summary_path, summary)
    print(status, flush=True)
    return 0 if all_conditions else 1


if __name__ == "__main__":
    raise SystemExit(main())
