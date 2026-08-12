#!/usr/bin/env python3
"""将已完成的 QUIC v8.1 分层先导物化为正式训练期物理真值。"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pyarrow as pa
import pyarrow.parquet as pq
import yaml


CONFIG_SCHEMA = "flow_probe_r2_quic_formal_materialization_v1"
OUTPUT_SCHEMA = "flow_probe_r2_quic_formal_physics_v1"
WINDOW_NS = 100_000_000
WINDOW_US = 100_000
SEQUENCE_WINDOWS = 4
SPLITS = ("train-fit", "calibration", "validation")
QUIC_FIELDS = (
    "truth_quic_cwnd_start_bytes",
    "truth_quic_cwnd_end_bytes",
    "truth_quic_bytes_in_flight_start_bytes",
    "truth_quic_bytes_in_flight_end_bytes",
    "truth_quic_sent_bytes",
    "truth_quic_acked_bytes",
    "truth_quic_lost_bytes",
    "truth_quic_latest_rtt_ms",
    "truth_quic_smoothed_rtt_ms",
    "truth_quic_min_rtt_ms",
)


class MaterializationError(RuntimeError):
    """输入采集收据或物化合同不满足时终止。"""


@dataclass(frozen=True)
class Packet:
    relative_ns: int
    l3_bytes: int


@dataclass(frozen=True)
class QlogEvent:
    relative_us: int
    name: str
    data: Mapping[str, Any]


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> str:
    payload = (_canonical_json(value) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return _sha256_bytes(payload)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    payload = "".join(_canonical_json(row) + "\n" for row in rows).encode("utf-8")
    path.write_bytes(payload)
    return _sha256_bytes(payload)


def _semantic_sha256(rows: Iterable[Mapping[str, Any]]) -> str:
    return _sha256_bytes(
        "".join(_canonical_json(row) + "\n" for row in rows).encode("utf-8")
    )


def _required_mapping(value: object, description: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise MaterializationError(f"{description} 必须是对象")
    return value


def _read_json(path: Path, description: str) -> Mapping[str, Any]:
    if not path.is_file():
        raise MaterializationError(f"{description}不存在：{path}")
    try:
        return _required_mapping(json.loads(path.read_text(encoding="utf-8")), description)
    except json.JSONDecodeError as error:
        raise MaterializationError(f"{description}不是有效 JSON：{path}") from error


def _resolve(project_root: Path, value: object, description: str) -> Path:
    if not isinstance(value, str) or not value:
        raise MaterializationError(f"{description}必须是非空路径")
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _artifact_path(state: Mapping[str, Any], connection_root: Path, basename: str) -> Path:
    matches = [
        item
        for item in state.get("artifacts", [])
        if isinstance(item, Mapping)
        and isinstance(item.get("path"), str)
        and Path(str(item["path"])).name == basename
    ]
    if len(matches) != 1:
        raise MaterializationError(f"连接 {state.get('connection_id')} 缺少唯一制品 {basename}")
    item = matches[0]
    path = connection_root / str(item["path"])
    digest = item.get("sha256")
    if not path.is_file() or not isinstance(digest, str) or len(digest) != 64:
        raise MaterializationError(f"连接 {state.get('connection_id')} 的制品收据无效：{basename}")
    if _sha256_file(path) != digest:
        raise MaterializationError(f"连接 {state.get('connection_id')} 的制品哈希不匹配：{basename}")
    return path


def _qlog_paths(state: Mapping[str, Any], connection_root: Path) -> list[Path]:
    artifacts = [
        item
        for item in state.get("artifacts", [])
        if isinstance(item, Mapping)
        and isinstance(item.get("path"), str)
        and str(item["path"]).startswith("qlog/")
    ]
    paths: list[Path] = []
    for item in artifacts:
        path = connection_root / str(item["path"])
        digest = item.get("sha256")
        if not path.is_file() or path.stat().st_size == 0 or not isinstance(digest, str) or len(digest) != 64:
            raise MaterializationError(f"连接 {state.get('connection_id')} 的 qlog 收据无效")
        if _sha256_file(path) != digest:
            raise MaterializationError(f"连接 {state.get('connection_id')} 的 qlog 哈希不匹配")
        paths.append(path)
    if not paths:
        raise MaterializationError(f"连接 {state.get('connection_id')} 缺少有效客户端 qlog")
    return sorted(paths)


def _load_finished_connections(input_root: Path, expected_connections: int) -> list[tuple[Mapping[str, Any], Path]]:
    run_state = _read_json(input_root / "run-state.json", "QUIC 运行状态")
    if (
        run_state.get("status") != "finished"
        or int(run_state.get("expected_connections", -1)) != expected_connections
        or int(run_state.get("finished_connections", -1)) != expected_connections
        or int(run_state.get("matrix_expected_connections", -1)) != expected_connections
    ):
        raise MaterializationError(
            "QUIC v5 采集尚未以 finished/120 完成，拒绝正式物化"
        )
    states: list[tuple[Mapping[str, Any], Path]] = []
    seen: set[str] = set()
    for status_path in sorted((input_root / "connections").glob("*/status.json")):
        state = _read_json(status_path, "连接状态")
        connection_id = state.get("connection_id")
        if not isinstance(connection_id, str) or not connection_id or connection_id in seen:
            raise MaterializationError(f"连接身份无效或重复：{status_path}")
        if state.get("status") != "finished" or state.get("final_test_visible") is not False:
            raise MaterializationError(f"连接未完成或最终测试可见：{connection_id}")
        if state.get("client_qlog_training_truth") is not True or state.get("pcap_deployment_observation") is not True:
            raise MaterializationError(f"连接训练真值或部署观测合同不满足：{connection_id}")
        seen.add(connection_id)
        states.append((state, status_path.parent))
    if len(states) != expected_connections:
        raise MaterializationError(f"完成连接数错误：{len(states)} != {expected_connections}")
    return states


def _partition_connections(
    states: Sequence[tuple[Mapping[str, Any], Path]], config: Mapping[str, Any]
) -> dict[str, str]:
    partition = _required_mapping(config.get("partition"), "partition")
    seed = str(partition.get("seed", ""))
    namespace = str(partition.get("hash_namespace", ""))
    counts = _required_mapping(partition.get("counts"), "partition.counts")
    if tuple(counts) != SPLITS or tuple(int(counts[split]) for split in SPLITS) != (80, 20, 20):
        raise MaterializationError("连接划分必须精确为 train-fit/calibration/validation=80/20/20")
    ordered = sorted(
        (
            _sha256_bytes(f"{namespace}\0{seed}\0{state['connection_id']}".encode("utf-8")),
            str(state["connection_id"]),
        )
        for state, _ in states
    )
    assignment: dict[str, str] = {}
    cursor = 0
    for split in SPLITS:
        for _, connection_id in ordered[cursor : cursor + int(counts[split])]:
            assignment[connection_id] = split
        cursor += int(counts[split])
    if len(assignment) != len(states):
        raise MaterializationError("连接级划分未覆盖全部完成连接")
    return assignment


def _pcap_packets(path: Path) -> list[Packet]:
    raw = path.read_bytes()
    if len(raw) < 24:
        raise MaterializationError(f"PCAP 过短：{path}")
    magic = raw[:4]
    formats = {
        b"\xd4\xc3\xb2\xa1": ("<", 1_000),
        b"\xa1\xb2\xc3\xd4": (">", 1_000),
        b"\x4d\x3c\xb2\xa1": ("<", 1),
        b"\xa1\xb2\x3c\x4d": (">", 1),
    }
    if magic not in formats:
        raise MaterializationError(f"只支持经典 PCAP，收到未知魔数：{path}")
    endian, fraction_to_ns = formats[magic]
    linktype = struct.unpack_from(f"{endian}I", raw, 20)[0]
    offset = 24
    packets: list[tuple[int, int]] = []
    while offset < len(raw):
        if offset + 16 > len(raw):
            raise MaterializationError(f"PCAP 记录头截断：{path}")
        seconds, fraction, captured, _ = struct.unpack_from(f"{endian}IIII", raw, offset)
        offset += 16
        if offset + captured > len(raw):
            raise MaterializationError(f"PCAP 记录截断：{path}")
        payload = raw[offset : offset + captured]
        offset += captured
        l3_bytes = _l3_length(payload, linktype)
        if l3_bytes is not None:
            packets.append((seconds * 1_000_000_000 + fraction * fraction_to_ns, l3_bytes))
    if not packets:
        raise MaterializationError(f"部署 PCAP 没有可解析 L3 数据包：{path}")
    origin = min(timestamp for timestamp, _ in packets)
    return [Packet(timestamp - origin, size) for timestamp, size in packets]


def _l3_length(payload: bytes, linktype: int) -> int | None:
    if linktype == 1:
        if len(payload) < 14:
            return None
        ether_type = int.from_bytes(payload[12:14], "big")
        offset = 14
        while ether_type in {0x8100, 0x88A8, 0x9100}:
            if len(payload) < offset + 4:
                return None
            ether_type = int.from_bytes(payload[offset + 2 : offset + 4], "big")
            offset += 4
    elif linktype == 101:
        offset, ether_type = 0, None
    elif linktype == 113:
        if len(payload) < 16:
            return None
        offset, ether_type = 16, int.from_bytes(payload[14:16], "big")
    elif linktype == 276:
        if len(payload) < 20:
            return None
        offset, ether_type = 20, int.from_bytes(payload[:2], "big")
    elif linktype == 0:
        if len(payload) < 4:
            return None
        offset, ether_type = 4, None
    else:
        raise MaterializationError(f"不支持的 PCAP 链路层类型：{linktype}")
    if len(payload) <= offset:
        return None
    version = payload[offset] >> 4
    if ether_type not in {None, 0x0800, 0x86DD} or version not in {4, 6}:
        return None
    if version == 4:
        if len(payload) < offset + 4:
            return None
        return int.from_bytes(payload[offset + 2 : offset + 4], "big")
    if len(payload) < offset + 6:
        return None
    return 40 + int.from_bytes(payload[offset + 4 : offset + 6], "big")


def _json_values(raw: bytes, path: Path) -> list[object]:
    chunks = raw.split(b"\x1e") if b"\x1e" in raw else [raw]
    values: list[object] = []
    for chunk in chunks:
        text = chunk.decode("utf-8", errors="strict").strip()
        if not text:
            continue
        try:
            values.append(json.loads(text))
            continue
        except json.JSONDecodeError:
            pass
        for line in text.splitlines():
            if line.strip():
                try:
                    values.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise MaterializationError(f"qlog JSON/JSON-SEQ 无法解析：{path}") from error
    if not values:
        raise MaterializationError(f"qlog 为空：{path}")
    return values


def _event_time_us(value: object, unit: str) -> int | None:
    if not isinstance(value, (int, float)):
        return None
    multiplier = {"ns": 0.001, "us": 1.0, "ms": 1_000.0, "s": 1_000_000.0}.get(unit)
    if multiplier is None:
        raise MaterializationError(f"不支持的 qlog 时间单位：{unit}")
    return int(round(float(value) * multiplier))


def _event_from_object(value: object, unit: str) -> QlogEvent | None:
    if isinstance(value, list) and len(value) >= 3:
        time_us = _event_time_us(value[0], unit)
        if time_us is None:
            return None
        name = str(value[2]) if ":" in str(value[2]) else f"{value[1]}:{value[2]}"
        data = value[3] if len(value) > 3 and isinstance(value[3], Mapping) else {}
        return QlogEvent(time_us, name.lower(), data)
    if not isinstance(value, Mapping):
        return None
    time_us = _event_time_us(value.get("time", value.get("relative_time")), unit)
    name = value.get("name", value.get("event_type"))
    if time_us is None or not isinstance(name, str):
        return None
    category = value.get("category")
    full_name = name if ":" in name or not category else f"{category}:{name}"
    data = value.get("data", value.get("event_data", {}))
    return QlogEvent(time_us, full_name.lower(), data if isinstance(data, Mapping) else {})


def _qlog_events(paths: Sequence[Path], default_unit: str) -> list[QlogEvent]:
    events: list[QlogEvent] = []
    for path in paths:
        for value in _json_values(path.read_bytes(), path):
            roots = value.get("traces", []) if isinstance(value, Mapping) and "traces" in value else [value]
            for root in roots:
                if not isinstance(root, Mapping):
                    continue
                unit = str(root.get("time_units", root.get("time_unit", default_unit))).lower()
                raw_events = root.get("events", [])
                if isinstance(raw_events, list):
                    events.extend(
                        event
                        for raw_event in raw_events
                        if (event := _event_from_object(raw_event, unit)) is not None
                    )
                else:
                    event = _event_from_object(root, unit)
                    if event is not None:
                        events.append(event)
    if not events:
        raise MaterializationError("qlog 中未找到可解释事件")
    origin = min(event.relative_us for event in events)
    return sorted(
        (QlogEvent(event.relative_us - origin, event.name, event.data) for event in events),
        key=lambda event: (event.relative_us, event.name),
    )


def _find_numbers(value: object, names: set[str]) -> list[int]:
    result: list[int] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in names and isinstance(nested, (int, float)):
                result.append(int(nested))
            result.extend(_find_numbers(nested, names))
    elif isinstance(value, list):
        for nested in value:
            result.extend(_find_numbers(nested, names))
    return result


def _packet_number(data: Mapping[str, Any]) -> int | None:
    values = _find_numbers(data, {"packet_number", "packet_number_value"})
    return values[0] if values else None


def _packet_bytes(data: Mapping[str, Any]) -> int | None:
    values = _find_numbers(data, {"packet_length", "raw_length", "length", "payload_length"})
    return values[0] if values and values[0] >= 0 else None


def _metric_value(data: Mapping[str, Any], keys: set[str]) -> float | None:
    values = _find_numbers(data, keys)
    return float(values[-1]) if values else None


def _ack_ranges(data: Mapping[str, Any]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    if isinstance(data, Mapping):
        start = data.get("range_start", data.get("smallest_acknowledged"))
        end = data.get("range_end", data.get("largest_acknowledged"))
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            ranges.append((int(start), int(end)))
        for nested in data.values():
            ranges.extend(_ack_ranges(nested))
    elif isinstance(data, list):
        for nested in data:
            ranges.extend(_ack_ranges(nested))
    return ranges


def _truth_windows(events: Sequence[QlogEvent], window_count: int) -> list[dict[str, Any]]:
    metrics: list[dict[str, list[float]]] = [defaultdict(list) for _ in range(window_count)]
    sent: list[list[tuple[int | None, int]]] = [[] for _ in range(window_count)]
    acked: list[list[int]] = [[] for _ in range(window_count)]
    lost: list[list[tuple[int | None, int | None]]] = [[] for _ in range(window_count)]
    known_sent: dict[int, int] = {}
    for event in events:
        index = event.relative_us // WINDOW_US
        if index < 0 or index >= window_count:
            continue
        name = event.name
        data = event.data
        if "metrics_updated" in name or "metrics_update" in name:
            for field, keys in {
                "cwnd": {"congestion_window", "cwnd", "congestion_window_bytes"},
                "bif": {"bytes_in_flight", "bytes_in_flight_bytes"},
                "latest": {"latest_rtt", "latest_rtt_ns"},
                "smoothed": {"smoothed_rtt", "smoothed_rtt_ns"},
                "min": {"min_rtt", "min_rtt_ns"},
            }.items():
                value = _metric_value(data, keys)
                if value is not None:
                    metrics[index][field].append(value)
        if "packet_sent" in name:
            size = _packet_bytes(data)
            if size is not None:
                packet_number = _packet_number(data)
                sent[index].append((packet_number, size))
                if packet_number is not None:
                    known_sent[packet_number] = size
        if "packet_acked" in name or "packets_acked" in name or "ack_received" in name:
            ranges = _ack_ranges(data)
            for start, end in ranges:
                acked[index].extend(range(start, end + 1))
        if "packet_lost" in name or "packets_lost" in name:
            lost[index].append((_packet_number(data), _packet_bytes(data)))
    rows: list[dict[str, Any]] = []
    for index in range(window_count):
        values: dict[str, int | float] = {}
        masks: dict[str, bool] = {}
        for field, metric, edge in (
            ("truth_quic_cwnd_start_bytes", "cwnd", 0),
            ("truth_quic_cwnd_end_bytes", "cwnd", -1),
            ("truth_quic_bytes_in_flight_start_bytes", "bif", 0),
            ("truth_quic_bytes_in_flight_end_bytes", "bif", -1),
            ("truth_quic_latest_rtt_ms", "latest", -1),
            ("truth_quic_smoothed_rtt_ms", "smoothed", -1),
            ("truth_quic_min_rtt_ms", "min", -1),
        ):
            samples = metrics[index].get(metric, [])
            observed = bool(samples)
            value = samples[edge] if observed else 0.0
            if "rtt" in field:
                value /= 1_000_000.0
            values[field] = value
            masks[field] = observed
        sent_sizes = [size for _, size in sent[index]]
        values["truth_quic_sent_bytes"] = sum(sent_sizes) if sent_sizes else 0
        masks["truth_quic_sent_bytes"] = bool(sent_sizes)
        ack_numbers = acked[index]
        resolved_ack = [known_sent[number] for number in ack_numbers if number in known_sent]
        values["truth_quic_acked_bytes"] = sum(resolved_ack) if ack_numbers else 0
        masks["truth_quic_acked_bytes"] = bool(ack_numbers) and len(resolved_ack) == len(ack_numbers)
        resolved_loss: list[int] = []
        for packet_number, size in lost[index]:
            if size is not None:
                resolved_loss.append(size)
            elif packet_number is not None and packet_number in known_sent:
                resolved_loss.append(known_sent[packet_number])
        values["truth_quic_lost_bytes"] = sum(resolved_loss) if lost[index] else 0
        masks["truth_quic_lost_bytes"] = bool(lost[index]) and len(resolved_loss) == len(lost[index])
        row = {field: values[field] for field in QUIC_FIELDS}
        row.update({f"{field}_observed": masks[field] for field in QUIC_FIELDS})
        rows.append(row)
    return rows


def _queue_windows(path: Path, window_count: int) -> list[dict[str, int]]:
    events: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            try:
                events.append(_required_mapping(json.loads(line), f"代理事件第 {line_number} 行"))
            except json.JSONDecodeError as error:
                raise MaterializationError(f"代理事件不是 JSONL：{path}:{line_number}") from error
    if not events:
        raise MaterializationError(f"代理事件为空：{path}")
    rows: list[dict[str, int]] = []
    backlog_bytes = 0
    backlog_packets = 0
    cursor = 0
    events = sorted(events, key=lambda event: int(event.get("arrival_offset_us", event.get("service_completion_offset_us", 0))))
    for index in range(window_count):
        start, stop = index * WINDOW_US, (index + 1) * WINDOW_US
        start_backlog_bytes = backlog_bytes
        start_backlog_packets = backlog_packets
        received_bytes = enqueued_bytes = dequeued_bytes = dropped_bytes = 0
        received_packets = enqueued_packets = dequeued_packets = dropped_packets = 0
        while cursor < len(events):
            event = events[cursor]
            timestamp = int(event.get("arrival_offset_us", event.get("service_completion_offset_us", -1)))
            if timestamp >= stop:
                break
            cursor += 1
            if timestamp < start:
                continue
            action = str(event.get("action", ""))
            size = int(event.get("bytes", 0))
            if size < 0:
                raise MaterializationError("代理事件存在负字节数")
            if action in {"scheduled", "dropped"}:
                received_bytes += size
                received_packets += 1
            if action == "scheduled" and event.get("admitted") is True:
                enqueued_bytes += size
                enqueued_packets += 1
                backlog_bytes += size
                backlog_packets += 1
            elif action == "service_completed":
                dequeued_bytes += size
                dequeued_packets += 1
                backlog_bytes -= size
                backlog_packets -= 1
                if backlog_bytes < 0 or backlog_packets < 0:
                    raise MaterializationError("代理队列守恒产生负积压")
            elif action == "dropped":
                dropped_bytes += size
                dropped_packets += 1
        rows.append(
            {
                "truth_queue_start_l3_bytes": start_backlog_bytes,
                "truth_queue_end_l3_bytes": backlog_bytes,
                "truth_qdisc_received_l3_bytes": received_bytes,
                "truth_qdisc_enqueued_l3_bytes": enqueued_bytes,
                "truth_qdisc_dequeued_l3_bytes": dequeued_bytes,
                "truth_qdisc_drop_before_enqueue_l3_bytes": dropped_bytes,
                "truth_qdisc_drop_after_dequeue_l3_bytes": 0,
                "truth_queue_balance_residual_l3_bytes": start_backlog_bytes + enqueued_bytes - dequeued_bytes - backlog_bytes,
                "truth_queue_start_packets": start_backlog_packets,
                "truth_queue_end_packets": backlog_packets,
                "truth_qdisc_received_packets": received_packets,
                "truth_qdisc_enqueued_packets": enqueued_packets,
                "truth_qdisc_dequeued_packets": dequeued_packets,
                "truth_qdisc_drop_before_enqueue_packets": dropped_packets,
                "truth_qdisc_drop_after_dequeue_packets": 0,
                "truth_queue_balance_residual_packets": start_backlog_packets + enqueued_packets - dequeued_packets - backlog_packets,
            }
        )
    return rows


def _validate_queue_stats(queue_rows: Sequence[Mapping[str, int]], stats: Mapping[str, Any]) -> None:
    """用代理汇总收据校验事件重放，不把统计值替代逐窗口守恒真值。"""
    directions = stats.get("directions")
    if stats.get("status") != "finished" or not isinstance(directions, Mapping):
        raise MaterializationError("代理统计未完成或缺少方向汇总")
    expected = defaultdict(int)
    for direction in directions.values():
        if not isinstance(direction, Mapping):
            raise MaterializationError("代理方向统计格式无效")
        for name in (
            "received_bytes",
            "received_packets",
            "scheduled_bytes",
            "scheduled_packets",
            "forwarded_bytes",
            "forwarded_packets",
            "random_drop_bytes",
            "random_drop_packets",
            "queue_drop_bytes",
            "queue_drop_packets",
        ):
            value = direction.get(name)
            if not isinstance(value, int) or value < 0:
                raise MaterializationError(f"代理统计字段无效：{name}")
            expected[name] += value
    actual = {
        "received_bytes": sum(row["truth_qdisc_received_l3_bytes"] for row in queue_rows),
        "received_packets": sum(row["truth_qdisc_received_packets"] for row in queue_rows),
        "scheduled_bytes": sum(row["truth_qdisc_enqueued_l3_bytes"] for row in queue_rows),
        "scheduled_packets": sum(row["truth_qdisc_enqueued_packets"] for row in queue_rows),
        "forwarded_bytes": sum(row["truth_qdisc_dequeued_l3_bytes"] for row in queue_rows),
        "forwarded_packets": sum(row["truth_qdisc_dequeued_packets"] for row in queue_rows),
        "dropped_bytes": sum(row["truth_qdisc_drop_before_enqueue_l3_bytes"] for row in queue_rows),
        "dropped_packets": sum(row["truth_qdisc_drop_before_enqueue_packets"] for row in queue_rows),
    }
    if actual["received_bytes"] != expected["received_bytes"] or actual["received_packets"] != expected["received_packets"]:
        raise MaterializationError("代理事件与统计的接收总量不一致")
    if actual["scheduled_bytes"] != expected["scheduled_bytes"] or actual["scheduled_packets"] != expected["scheduled_packets"]:
        raise MaterializationError("代理事件与统计的入队总量不一致")
    if actual["forwarded_bytes"] != expected["forwarded_bytes"] or actual["forwarded_packets"] != expected["forwarded_packets"]:
        raise MaterializationError("代理事件与统计的出队总量不一致")
    if actual["dropped_bytes"] != expected["random_drop_bytes"] + expected["queue_drop_bytes"] or actual["dropped_packets"] != expected["random_drop_packets"] + expected["queue_drop_packets"]:
        raise MaterializationError("代理事件与统计的丢弃总量不一致")


def _observation_windows(packets: Sequence[Packet]) -> list[dict[str, int | float]]:
    window_count = max(packet.relative_ns for packet in packets) // WINDOW_NS + 1
    windows = [{"public_total_packets": 0, "public_total_l3_bytes": 0} for _ in range(window_count)]
    for packet in packets:
        row = windows[packet.relative_ns // WINDOW_NS]
        row["public_total_packets"] += 1
        row["public_total_l3_bytes"] += packet.l3_bytes
    for row in windows:
        row["public_packet_rate_pps"] = float(row["public_total_packets"]) * 10.0
        row["public_byte_rate_Bps"] = float(row["public_total_l3_bytes"]) * 10.0
    return windows


def _schema() -> pa.Schema:
    fields = [
        pa.field("schema_version", pa.string()),
        pa.field("sequence_id", pa.string()),
        pa.field("evaluation_cluster_id", pa.string()),
        pa.field("connection_id", pa.string()),
        pa.field("sequence_stable_order", pa.int64()),
        pa.field("sequence_index", pa.int64()),
        pa.field("window_index_in_sequence", pa.int8()),
        pa.field("source_window_index", pa.int64()),
        pa.field("split_id", pa.string()),
        pa.field("implementation", pa.string()),
        pa.field("profile_id", pa.string()),
        pa.field("run_seed", pa.int64()),
        pa.field("payload_id", pa.string()),
        pa.field("route_id", pa.string()),
        pa.field("route_confidence", pa.float64()),
        pa.field("quic_applicable", pa.bool_()),
        pa.field("qlog_truth_available", pa.bool_()),
        pa.field("quic_formal_training_enabled", pa.bool_()),
        pa.field("window_valid", pa.bool_()),
        pa.field("final_test_visible", pa.bool_()),
        pa.field("window_start_s", pa.float64()),
        pa.field("window_end_s", pa.float64()),
        pa.field("window_duration_s", pa.float64()),
        pa.field("public_total_packets", pa.int64()),
        pa.field("public_total_l3_bytes", pa.int64()),
        pa.field("public_packet_rate_pps", pa.float64()),
        pa.field("public_byte_rate_Bps", pa.float64()),
        pa.field("truth_shared_applicable", pa.bool_()),
        pa.field("truth_shared_observed", pa.bool_()),
    ]
    for name in (
        "truth_queue_start_l3_bytes", "truth_queue_end_l3_bytes", "truth_qdisc_received_l3_bytes",
        "truth_qdisc_enqueued_l3_bytes", "truth_qdisc_dequeued_l3_bytes",
        "truth_qdisc_drop_before_enqueue_l3_bytes", "truth_qdisc_drop_after_dequeue_l3_bytes",
        "truth_queue_balance_residual_l3_bytes", "truth_queue_start_packets",
        "truth_queue_end_packets", "truth_qdisc_received_packets", "truth_qdisc_enqueued_packets",
        "truth_qdisc_dequeued_packets", "truth_qdisc_drop_before_enqueue_packets",
        "truth_qdisc_drop_after_dequeue_packets", "truth_queue_balance_residual_packets",
    ):
        fields.append(pa.field(name, pa.int64()))
    for name in QUIC_FIELDS:
        fields.append(pa.field(name, pa.float64()))
        fields.append(pa.field(f"{name}_observed", pa.bool_()))
    return pa.schema(fields)


def _connection_rows(
    state: Mapping[str, Any], connection_root: Path, split_id: str, default_qlog_unit: str, sequence_order: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pcap = _artifact_path(state, connection_root, "deployment-observation.pcap")
    proxy_events = _artifact_path(state, connection_root, "proxy-events.jsonl")
    proxy_stats = _artifact_path(state, connection_root, "proxy-stats.json")
    proxy_stats_payload = _read_json(proxy_stats, "代理统计")
    observations = _observation_windows(_pcap_packets(pcap))
    queue = _queue_windows(proxy_events, len(observations))
    _validate_queue_stats(queue, proxy_stats_payload)
    truth = _truth_windows(_qlog_events(_qlog_paths(state, connection_root), default_qlog_unit), len(observations))
    if not (len(observations) == len(queue) == len(truth)):
        raise MaterializationError(f"连接窗口对齐失败：{state['connection_id']}")
    profile = _required_mapping(state.get("profile"), "连接 profile")
    payload = _required_mapping(state.get("payload"), "连接 payload")
    connection_id = str(state["connection_id"])
    rows: list[dict[str, Any]] = []
    sequence_rows: list[dict[str, Any]] = []
    for sequence_index in range(len(observations) // SEQUENCE_WINDOWS):
        sequence_id = f"r2-quic-v8-1:{connection_id}:{sequence_index:06d}"
        sequence_rows.append(
            {
                "schema_version": OUTPUT_SCHEMA,
                "sequence_id": sequence_id,
                "connection_id": connection_id,
                "split_id": split_id,
                "sequence_stable_order": sequence_order + sequence_index,
                "sequence_index": sequence_index,
                "window_count": SEQUENCE_WINDOWS,
                "final_test_visible": False,
            }
        )
        for local_index in range(SEQUENCE_WINDOWS):
            source_index = sequence_index * SEQUENCE_WINDOWS + local_index
            rows.append(
                {
                    "schema_version": OUTPUT_SCHEMA,
                    "sequence_id": sequence_id,
                    "evaluation_cluster_id": connection_id,
                    "connection_id": connection_id,
                    "sequence_stable_order": sequence_order + sequence_index,
                    "sequence_index": sequence_index,
                    "window_index_in_sequence": local_index,
                    "source_window_index": source_index,
                    "split_id": split_id,
                    "implementation": str(state["implementation"]),
                    "profile_id": str(profile["id"]),
                    "run_seed": int(state["seed"]),
                    "payload_id": str(payload["id"]),
                    "route_id": "QUIC",
                    "route_confidence": 1.0,
                    "quic_applicable": True,
                    "qlog_truth_available": True,
                    "quic_formal_training_enabled": True,
                    "window_valid": True,
                    "final_test_visible": False,
                    "window_start_s": source_index / 10.0,
                    "window_end_s": (source_index + 1) / 10.0,
                    "window_duration_s": 0.1,
                    **observations[source_index],
                    "truth_shared_applicable": True,
                    "truth_shared_observed": True,
                    **queue[source_index],
                    **truth[source_index],
                }
            )
    return rows, sequence_rows


def _artifact_entry(path: Path, schema: pa.Schema, rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    return {
        "path": path.name,
        "sha256": _sha256_file(path),
        "row_count": len(rows),
        "schema_sha256": _sha256_bytes(str(schema).encode("utf-8")),
        "semantic_sha256": _semantic_sha256(rows),
    }


def materialize(config_path: Path, project_root: Path) -> Path:
    config = _required_mapping(yaml.safe_load(config_path.read_text(encoding="utf-8")), "物化配置")
    if config.get("schema_version") != CONFIG_SCHEMA:
        raise MaterializationError("物化配置版本不匹配")
    if config.get("final_test_visible") is not False or config.get("quic_formal_training_enabled") is not True:
        raise MaterializationError("配置必须保持最终测试不可见且启用 QUIC 正式训练制品")
    inputs = _required_mapping(config.get("input"), "input")
    input_root = _resolve(project_root, inputs.get("root"), "input.root")
    expected = int(inputs.get("expected_connections", -1))
    if expected != 120:
        raise MaterializationError("正式分层先导物化器只接受 120 条连接")
    output_root = _resolve(project_root, config.get("output_root"), "output_root")
    if output_root.exists():
        raise MaterializationError(f"输出目录已存在，拒绝覆盖：{output_root}")
    states = _load_finished_connections(input_root, expected)
    partition = _partition_connections(states, config)
    default_qlog_unit = str(config.get("qlog_default_time_unit", "ms"))
    partial_root = output_root.with_name(output_root.name + ".partial")
    if partial_root.exists():
        raise MaterializationError(f"临时输出目录已存在，拒绝覆盖：{partial_root}")
    partial_root.mkdir(parents=True)
    try:
        main_rows: list[dict[str, Any]] = []
        sequence_rows: list[dict[str, Any]] = []
        sequence_order = 0
        for state, connection_root in sorted(states, key=lambda item: str(item[0]["connection_id"])):
            rows, sequences = _connection_rows(
                state, connection_root, partition[str(state["connection_id"])], default_qlog_unit, sequence_order
            )
            main_rows.extend(rows)
            sequence_rows.extend(sequences)
            sequence_order += len(sequences)
        if not main_rows:
            raise MaterializationError("120 条连接均未形成完整四窗口序列")
        split_sequences = defaultdict(int)
        for row in sequence_rows:
            split_sequences[str(row["split_id"])] += 1
        if any(split_sequences[split] == 0 for split in SPLITS):
            raise MaterializationError("至少一个开发划分没有完整 QUIC 序列")
        schema = _schema()
        primary_path = partial_root / "physics-targets-quic-v1.parquet"
        pq.write_table(pa.Table.from_pylist(main_rows, schema=schema), primary_path, compression="zstd")
        companion_columns = [field.name for field in schema if field.name.startswith("truth_quic_") or field.name in {
            "sequence_id", "source_window_index", "connection_id", "split_id", "qlog_truth_available", "final_test_visible"
        }]
        companion_schema = pa.schema([schema.field(name) for name in companion_columns])
        companion_rows = [{name: row[name] for name in companion_columns} for row in main_rows]
        companion_path = partial_root / "quic-window-truth-v1.parquet"
        pq.write_table(pa.Table.from_pylist(companion_rows, schema=companion_schema), companion_path, compression="zstd")
        assignments = [
            {"connection_id": connection_id, "split_id": split_id, "final_test_visible": False}
            for connection_id, split_id in sorted(partition.items())
        ]
        assignments_sha = _write_jsonl(partial_root / "connection-split-assignments.jsonl", assignments)
        sequences_sha = _write_jsonl(partial_root / "quic-sequence-manifest-v1.jsonl", sequence_rows)
        schema_document = {
            "schema_version": OUTPUT_SCHEMA,
            "final_test_visible": False,
            "quic_formal_training_enabled": True,
            "qlog_truth_available": True,
            "window_duration_ns": WINDOW_NS,
            "sequence_length_windows": SEQUENCE_WINDOWS,
            "quic_truth_fields": list(QUIC_FIELDS),
            "missing_truth_policy": "数值置零且逐字段 observed 掩码为 false；训练必须同时读取数值和掩码",
            "residual_contract": [
                "在途字节守恒",
                "起止在途字节不超过拥塞窗口",
                "min_rtt 不超过 latest_rtt 与 smoothed_rtt",
                "确认与丢失字节不超过起始在途字节加本窗发送字节",
            ],
            "columns": [field.name for field in schema],
        }
        schema_sha = _write_json(partial_root / "schema.json", schema_document)
        summary = {
            "schema_version": OUTPUT_SCHEMA,
            "input_root": str(input_root.relative_to(project_root)),
            "input_run_state_sha256": _sha256_file(input_root / "run-state.json"),
            "completed_connections": expected,
            "connection_assignments": {split: sum(1 for value in partition.values() if value == split) for split in SPLITS},
            "sequence_counts": dict(sorted(split_sequences.items())),
            "window_rows": len(main_rows),
            "final_test_visible": False,
            "malicious_labels_present": False,
            "qlog_truth_available": True,
            "quic_formal_training_enabled": True,
            "artifacts": {
                "physics_targets_quic": _artifact_entry(primary_path, schema, main_rows),
                "quic_window_truth": _artifact_entry(companion_path, companion_schema, companion_rows),
                "connection_split_assignments_semantic_sha256": assignments_sha,
                "quic_sequence_manifest_semantic_sha256": sequences_sha,
                "schema_semantic_sha256": schema_sha,
            },
        }
        summary_sha = _write_json(partial_root / "summary.json", summary)
        _write_json(
            partial_root / "artifact-manifest.json",
            {
                "schema_version": "flow_probe_r2_quic_formal_artifact_manifest_v1",
                "summary_sha256": summary_sha,
                "final_test_visible": False,
                "quic_formal_training_enabled": True,
                "artifacts": summary["artifacts"],
            },
        )
        partial_root.rename(output_root)
    except BaseException:
        shutil.rmtree(partial_root, ignore_errors=True)
        raise
    return output_root


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        output = materialize(args.config, args.project_root.resolve())
    except MaterializationError as error:
        parser.error(str(error))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
