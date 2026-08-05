from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zipfile import ZipFile

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import yaml


SCHEMA_VERSION = "flow_probe_r2_final_sidecar_candidate_v1"
GENIS_NAMESPACE = "dataset-candidate-genis-v0"
INCLUDED_NS3_SPLITS = ("train-fit", "calibration", "validation")
WITHHELD_NS3_SPLITS = ("test", "unseen-configuration")
VALUE_FIELDS = (
    "total_packets",
    "total_bytes",
    "packet_length_mean",
    "packet_length_min",
    "packet_length_max",
    "iat_mean_ms",
    "packet_rate",
    "byte_rate",
)


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


def _validate_input(path: Path, expected_sha256: str) -> None:
    if not path.is_file() or path.is_symlink():
        raise MaterializationError(f"输入不是普通文件：{path}")
    actual = _sha256_file(path)
    if actual != expected_sha256:
        raise MaterializationError(
            f"输入 SHA-256 不一致：{path}，期望 {expected_sha256}，实际 {actual}"
        )


def _resolve_input(
    project_root: Path, repository_root: Path, spec: Mapping[str, Any]
) -> Path:
    root_name = str(spec["root"])
    if root_name == "project":
        root = project_root
    elif root_name == "repository":
        root = repository_root
    else:
        raise MaterializationError(f"未知输入根：{root_name}")
    relative = Path(str(spec["path"]))
    if relative.is_absolute() or ".." in relative.parts:
        raise MaterializationError(f"输入逻辑路径不合法：{relative}")
    return root / relative


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise MaterializationError(f"JSONL 含空行：{path}:{line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise MaterializationError(f"JSONL 行不是对象：{path}:{line_number}")
            rows.append(value)
    return rows


def _write_json(path: Path, value: object) -> str:
    payload = (_canonical_json(value) + "\n").encode("utf-8")
    path.write_bytes(payload)
    return _sha256_bytes(payload)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    payload = "".join(_canonical_json(dict(row)) + "\n" for row in rows).encode(
        "utf-8"
    )
    path.write_bytes(payload)
    return _sha256_bytes(payload)


def _semantic_sha256(rows: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(_canonical_json(dict(row)).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _schema_sha256(schema: pa.Schema) -> str:
    fields = [{"name": field.name, "type": str(field.type)} for field in schema]
    return _sha256_bytes(_canonical_json(fields).encode("utf-8"))


def _write_parquet(path: Path, rows: list[dict[str, Any]], schema: pa.Schema) -> None:
    table = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(
        table,
        path,
        version="2.6",
        compression="zstd",
        compression_level=9,
        use_dictionary=False,
        write_statistics=True,
        data_page_version="1.0",
        row_group_size=65536,
    )


def _candidate_detection_rows(
    candidate_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    stable_orders: set[int] = set()
    sample_ids: set[str] = set()
    for row in candidate_rows:
        stable_order = int(row["stable_order"])
        if stable_order in stable_orders:
            raise MaterializationError("候选稳定顺序重复")
        stable_orders.add(stable_order)
        source = str(row["source_dataset"])
        if source not in {"genis", "tqhc2"}:
            continue
        sample_id = str(row["sample_id"])
        if sample_id in sample_ids:
            raise MaterializationError("检测候选 sample_id 重复")
        sample_ids.add(sample_id)
        selected.append(
            {
                "schema_version": SCHEMA_VERSION,
                "sample_id": sample_id,
                "stable_order": stable_order,
                "split_id": "train-fit",
                "source_dataset": source,
                "task_role": "classification_candidate",
                "classifier_view_source": "dataset-v1-shared-b0",
                "final_test_visible": False,
            }
        )
    selected.sort(key=lambda row: int(row["stable_order"]))
    counts = Counter(str(row["source_dataset"]) for row in selected)
    if counts != Counter({"genis": 3973, "tqhc2": 3606}):
        raise MaterializationError(f"检测候选数量不符合合同：{dict(counts)}")
    if len(selected) != 7579:
        raise MaterializationError("检测候选总数不是 7,579")
    return selected


def _genis_candidate_id(member_basename: str, row_number: int) -> str:
    old_sample_id = f"genis:{member_basename}:{row_number}"
    digest = hashlib.sha256(
        f"{GENIS_NAMESPACE}\0{old_sample_id}".encode("utf-8")
    ).hexdigest()
    return f"genis:{digest}"


def _normalise_transport(value: str) -> str:
    candidate = value.strip().upper()
    if candidate in {"TCP", "UDP", "ICMP", "SCTP", "DCCP", "ESP"}:
        return candidate
    return "UNKNOWN"


def _route_record(
    detection: Mapping[str, Any],
    *,
    transport_family: str,
    protocol_target: str,
    observed: bool,
) -> dict[str, Any]:
    if protocol_target == "TCP":
        route_id = "TCP"
    elif protocol_target == "UDP":
        route_id = "UDP"
    else:
        route_id = "UNKNOWN"
    return {
        "sample_id": str(detection["sample_id"]),
        "stable_order": int(detection["stable_order"]),
        "source_dataset": str(detection["source_dataset"]),
        "split_id": str(detection["split_id"]),
        "transport_family": transport_family,
        "transport_family_observed": observed,
        "protocol_target": protocol_target,
        "route_id": route_id,
        "route_confidence": 1.0 if observed else 0.0,
        "route_confidence_observed": observed,
        "shared_expert_applicable": True,
        "tcp_expert_applicable": route_id == "TCP",
        "udp_expert_applicable": route_id == "UDP",
        "quic_expert_applicable": False,
        "qlog_truth_available": False,
        "quic_formal_training_enabled": False,
        "stop_gradient_route": True,
        "final_test_visible": False,
    }


def _build_route_assignments(
    detection_rows: Sequence[Mapping[str, Any]],
    genis_archive: Path,
    tqhc2_protocol_path: Path,
) -> list[dict[str, Any]]:
    by_id = {str(row["sample_id"]): row for row in detection_rows}
    genis_ids = {
        sample_id for sample_id, row in by_id.items() if row["source_dataset"] == "genis"
    }
    tqhc2_ids = {
        sample_id for sample_id, row in by_id.items() if row["source_dataset"] == "tqhc2"
    }
    routes: dict[str, dict[str, Any]] = {}

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
        if sample_id in routes:
            raise MaterializationError("TQH 路由记录重复")
        routes[sample_id] = _route_record(
            by_id[sample_id],
            transport_family=_normalise_transport(str(row["transport_family"])),
            protocol_target=_normalise_transport(str(row["protocol_target"])),
            observed=bool(row["transport_family_observed"]),
        )
    if set(routes) != tqhc2_ids:
        missing = len(tqhc2_ids.difference(routes))
        raise MaterializationError(f"TQH 路由缺失 {missing} 条")

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
                        raise MaterializationError("GeNIS 候选连接重复")
                    found_genis.add(sample_id)
                    transport = _normalise_transport(values[proto_index])
                    protocol_target = transport if transport in {"TCP", "UDP"} else "UNKNOWN"
                    routes[sample_id] = _route_record(
                        by_id[sample_id],
                        transport_family=transport,
                        protocol_target=protocol_target,
                        observed=transport != "UNKNOWN",
                    )
    if found_genis != genis_ids:
        missing = len(genis_ids.difference(found_genis))
        raise MaterializationError(f"GeNIS 路由缺失 {missing} 条")

    ordered = [routes[str(row["sample_id"])] for row in detection_rows]
    if len(ordered) != 7579:
        raise MaterializationError("路由记录总数不正确")
    return ordered


def _empty_history_row(
    detection: Mapping[str, Any], window_index: int
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "sample_id": str(detection["sample_id"]),
        "stable_order": int(detection["stable_order"]),
        "source_dataset": str(detection["source_dataset"]),
        "split_id": str(detection["split_id"]),
        "window_index": window_index,
        "packet_start_index": (0, 2, 4, 8)[window_index],
        "packet_stop_index": (0, 2, 4, 8)[window_index],
        "window_valid": False,
        "history_available": False,
        "final_test_visible": False,
    }
    for field in VALUE_FIELDS:
        row[field] = None
        row[f"{field}_missing"] = True
    return row


def _window_history_row(
    detection: Mapping[str, Any],
    window_index: int,
    packets: Sequence[tuple[int, int, int]],
    start: int,
    stop: int,
) -> dict[str, Any]:
    selected = packets[start:stop]
    if not selected:
        return _empty_history_row(detection, window_index)
    delta_us = [packet[1] for packet in selected]
    lengths = [packet[2] for packet in selected]
    duration_seconds = sum(delta_us) / 1_000_000.0
    packet_count = len(selected)
    total_bytes = sum(lengths)
    row: dict[str, Any] = {
        "sample_id": str(detection["sample_id"]),
        "stable_order": int(detection["stable_order"]),
        "source_dataset": str(detection["source_dataset"]),
        "split_id": str(detection["split_id"]),
        "window_index": window_index,
        "packet_start_index": start,
        "packet_stop_index": stop,
        "window_valid": True,
        "history_available": True,
        "total_packets": float(packet_count),
        "total_bytes": float(total_bytes),
        "packet_length_mean": total_bytes / packet_count,
        "packet_length_min": float(min(lengths)),
        "packet_length_max": float(max(lengths)),
        "iat_mean_ms": sum(delta_us) / packet_count / 1000.0,
        "packet_rate": packet_count / duration_seconds
        if duration_seconds > 0
        else None,
        "byte_rate": total_bytes / duration_seconds
        if duration_seconds > 0
        else None,
        "final_test_visible": False,
    }
    for field in VALUE_FIELDS:
        row[f"{field}_missing"] = row[field] is None
    return row


def _build_common_history(
    detection_rows: Sequence[Mapping[str, Any]], packet_path: Path
) -> tuple[list[dict[str, Any]], int]:
    tqhc2_detection = [
        row for row in detection_rows if row["source_dataset"] == "tqhc2"
    ]
    selected_ids = {str(row["sample_id"]) for row in tqhc2_detection}
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
    packet_groups: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for row in table.to_pylist():
        packet_groups[str(row["sample_id"])].append(
            (
                int(row["packet_index"]),
                int(row["delta_time_us"]),
                int(row["network_length_bytes"]),
            )
        )
    if set(packet_groups) != selected_ids:
        raise MaterializationError("TQH 候选包历史未完全命中")
    for sample_id, packets in packet_groups.items():
        indexes = [packet[0] for packet in packets]
        if indexes != list(range(len(indexes))):
            raise MaterializationError(f"TQH packet_index 不连续：{sample_id}")
        if any(packet[1] < 0 or packet[2] < 0 for packet in packets):
            raise MaterializationError(f"TQH 包历史出现负值：{sample_id}")

    output: list[dict[str, Any]] = []
    for detection in detection_rows:
        if detection["source_dataset"] == "genis":
            output.extend(_empty_history_row(detection, index) for index in range(4))
            continue
        packets = packet_groups[str(detection["sample_id"])]
        count = len(packets)
        bounds = ((0, min(2, count)), (2, min(4, count)), (4, min(8, count)), (8, count))
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
    if len(output) != 7579 * 4:
        raise MaterializationError("共同历史行数不正确")
    expected_order = [
        (int(row["stable_order"]), int(row["window_index"])) for row in output
    ]
    if expected_order != sorted(expected_order):
        raise MaterializationError("共同历史顺序不稳定")
    return output, table.num_rows


def _parse_bool(value: str) -> bool:
    if value not in {"0", "1"}:
        raise MaterializationError(f"布尔字段不是 0/1：{value}")
    return value == "1"


def _ns3_window_row(
    manifest_row: Mapping[str, Any],
    csv_row: Mapping[str, str],
    *,
    run_stable_order: int,
    sequence_stable_order: int,
    sequence_index: int,
    window_index_in_sequence: int,
    source_csv_sha256: str,
) -> dict[str, Any]:
    transport = str(manifest_row["transport_family"])
    tcp = transport == "TCP"
    udp = transport == "UDP"
    return {
        "sequence_id": f"ns3-r2:{manifest_row['physics_group_sha256']}:{transport}:{sequence_index:02d}",
        "sequence_stable_order": sequence_stable_order,
        "run_stable_order": run_stable_order,
        "physics_group_sha256": str(manifest_row["physics_group_sha256"]),
        "split_id": str(manifest_row["split"]),
        "transport_family": transport,
        "route_id": transport,
        "route_confidence": 1.0,
        "stop_gradient_route": True,
        "sequence_index": sequence_index,
        "window_index_in_sequence": window_index_in_sequence,
        "source_window_index": int(csv_row["window_index"]),
        "window_start_s": float(csv_row["window_start_s"]),
        "window_end_s": float(csv_row["window_end_s"]),
        "public_total_packets": int(csv_row["public_total_packets"]),
        "public_total_l3_bytes": int(csv_row["public_total_l3_bytes"]),
        "public_packet_length_mean_l3_bytes": float(
            csv_row["public_packet_length_mean_l3_bytes"]
        ),
        "public_packet_length_min_l3_bytes": int(
            csv_row["public_packet_length_min_l3_bytes"]
        ),
        "public_packet_length_max_l3_bytes": int(
            csv_row["public_packet_length_max_l3_bytes"]
        ),
        "public_iat_mean_ms": float(csv_row["public_iat_mean_ms"]),
        "public_packet_rate_pps": float(csv_row["public_packet_rate_pps"]),
        "public_byte_rate_Bps": float(csv_row["public_byte_rate_Bps"]),
        "truth_shared_applicable": True,
        "truth_shared_observed": True,
        "truth_capacity_integral_link_bytes": float(
            csv_row["truth_capacity_integral_link_bytes"]
        ),
        "truth_queue_start_l3_bytes": int(csv_row["truth_queue_start_l3_bytes"]),
        "truth_queue_end_l3_bytes": int(csv_row["truth_queue_end_l3_bytes"]),
        "truth_qdisc_received_l3_bytes": int(
            csv_row["truth_qdisc_received_l3_bytes"]
        ),
        "truth_qdisc_enqueued_l3_bytes": int(
            csv_row["truth_qdisc_enqueued_l3_bytes"]
        ),
        "truth_qdisc_dequeued_l3_bytes": int(
            csv_row["truth_qdisc_dequeued_l3_bytes"]
        ),
        "truth_qdisc_drop_before_enqueue_l3_bytes": int(
            csv_row["truth_qdisc_drop_before_enqueue_l3_bytes"]
        ),
        "truth_qdisc_drop_after_dequeue_l3_bytes": int(
            csv_row["truth_qdisc_drop_after_dequeue_l3_bytes"]
        ),
        "truth_downstream_error_loss_l3_bytes": int(
            csv_row["truth_downstream_error_loss_l3_bytes"]
        ),
        "truth_receiver_local_deliver_l3_bytes": int(
            csv_row["truth_receiver_local_deliver_l3_bytes"]
        ),
        "truth_queue_start_packets": int(csv_row["truth_queue_start_packets"]),
        "truth_queue_end_packets": int(csv_row["truth_queue_end_packets"]),
        "truth_qdisc_received_packets": int(csv_row["truth_qdisc_received_packets"]),
        "truth_qdisc_enqueued_packets": int(csv_row["truth_qdisc_enqueued_packets"]),
        "truth_qdisc_dequeued_packets": int(csv_row["truth_qdisc_dequeued_packets"]),
        "truth_qdisc_drop_before_enqueue_packets": int(
            csv_row["truth_qdisc_drop_before_enqueue_packets"]
        ),
        "truth_qdisc_drop_after_dequeue_packets": int(
            csv_row["truth_qdisc_drop_after_dequeue_packets"]
        ),
        "truth_downstream_error_loss_packets": int(
            csv_row["truth_downstream_error_loss_packets"]
        ),
        "truth_receiver_local_deliver_packets": int(
            csv_row["truth_receiver_local_deliver_packets"]
        ),
        "truth_queue_balance_residual_l3_bytes": int(
            csv_row["truth_queue_balance_residual_l3_bytes"]
        ),
        "truth_queue_balance_residual_packets": int(
            csv_row["truth_queue_balance_residual_packets"]
        ),
        "truth_tcp_cwnd_applicable": tcp,
        "truth_tcp_cwnd_observed": _parse_bool(csv_row["truth_tcp_cwnd_observed"]),
        "truth_tcp_cwnd_mean_bytes": float(csv_row["truth_tcp_cwnd_mean_bytes"])
        if tcp
        else None,
        "truth_tcp_cwnd_min_bytes": int(csv_row["truth_tcp_cwnd_min_bytes"])
        if tcp
        else None,
        "truth_tcp_cwnd_max_bytes": int(csv_row["truth_tcp_cwnd_max_bytes"])
        if tcp
        else None,
        "truth_tcp_rtt_applicable": tcp,
        "truth_tcp_rtt_observed": False,
        "truth_tcp_bytes_in_flight_applicable": tcp,
        "truth_tcp_bytes_in_flight_observed": False,
        "truth_tcp_ack_applicable": tcp,
        "truth_tcp_ack_observed": False,
        "truth_tcp_retrans_applicable": tcp,
        "truth_tcp_retrans_observed": False,
        "truth_udp_applicable": udp,
        "truth_udp_observed": udp,
        "truth_udp_planned_app_payload_packets": int(
            csv_row["truth_udp_planned_app_payload_packets"]
        )
        if udp
        else None,
        "truth_udp_planned_app_payload_bytes": int(
            csv_row["truth_udp_planned_app_payload_bytes"]
        )
        if udp
        else None,
        "truth_udp_actual_send_events": int(csv_row["truth_udp_actual_send_events"])
        if udp
        else None,
        "truth_udp_actual_send_bytes": int(csv_row["truth_udp_actual_send_bytes"])
        if udp
        else None,
        "truth_udp_target_rate_bps": int(csv_row["truth_udp_target_rate_bps"])
        if udp
        else None,
        "truth_udp_burst_mode": _parse_bool(csv_row["truth_udp_burst_mode"])
        if udp
        else None,
        "truth_udp_burst_active": _parse_bool(csv_row["truth_udp_burst_active"])
        if udp
        else None,
        "source_csv_sha256": source_csv_sha256,
        "final_test_visible": False,
    }


def _build_ns3_physics(
    manifest_rows: Sequence[Mapping[str, Any]], ns3_root: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    window_rows: list[dict[str, Any]] = []
    sequence_rows: list[dict[str, Any]] = []
    included_runs = 0
    withheld_runs = 0
    sequence_stable_order = 0
    for run_stable_order, manifest_row in enumerate(manifest_rows):
        split = str(manifest_row["split"])
        if split in WITHHELD_NS3_SPLITS:
            withheld_runs += 1
            continue
        if split not in INCLUDED_NS3_SPLITS:
            raise MaterializationError(f"未知 ns-3 划分：{split}")
        included_runs += 1
        group = str(manifest_row["physics_group_sha256"])
        transport = str(manifest_row["transport_family"])
        run_root = ns3_root / "pairs" / group / transport
        csv_path = run_root / "result.csv"
        receipt_path = run_root / "receipt.json"
        pair_receipt_path = ns3_root / "pairs" / group / "pair-receipt.json"
        if not csv_path.is_file() or not receipt_path.is_file() or not pair_receipt_path.is_file():
            raise MaterializationError(f"ns-3 运行制品缺失：{group}/{transport}")
        pair_receipt = json.loads(pair_receipt_path.read_text(encoding="utf-8"))
        expected_csv_sha = str(pair_receipt[f"{transport.lower()}_csv_sha256"])
        actual_csv_sha = _sha256_file(csv_path)
        if actual_csv_sha != expected_csv_sha:
            raise MaterializationError(f"ns-3 CSV 摘要不一致：{group}/{transport}")
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            csv_rows = list(csv.DictReader(handle))
        if len(csv_rows) != 120:
            raise MaterializationError(f"ns-3 窗口数不是 120：{group}/{transport}")
        if [int(row["window_index"]) for row in csv_rows] != list(range(120)):
            raise MaterializationError(f"ns-3 窗口顺序错误：{group}/{transport}")
        for sequence_index in range(30):
            sequence_id = f"ns3-r2:{group}:{transport}:{sequence_index:02d}"
            sequence_rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "sequence_id": sequence_id,
                    "sequence_stable_order": sequence_stable_order,
                    "run_stable_order": run_stable_order,
                    "physics_group_sha256": group,
                    "split_id": split,
                    "transport_family": transport,
                    "route_id": transport,
                    "window_start_index": sequence_index * 4,
                    "window_stop_index": sequence_index * 4 + 4,
                    "window_count": 4,
                    "source_csv_sha256": actual_csv_sha,
                    "final_test_visible": False,
                }
            )
            for offset in range(4):
                source_window_index = sequence_index * 4 + offset
                window_rows.append(
                    _ns3_window_row(
                        manifest_row,
                        csv_rows[source_window_index],
                        run_stable_order=run_stable_order,
                        sequence_stable_order=sequence_stable_order,
                        sequence_index=sequence_index,
                        window_index_in_sequence=offset,
                        source_csv_sha256=actual_csv_sha,
                    )
                )
            sequence_stable_order += 1
    counts = {
        "included_runs": included_runs,
        "withheld_runs": withheld_runs,
        "window_rows": len(window_rows),
        "sequence_rows": len(sequence_rows),
    }
    expected = {
        "included_runs": 384,
        "withheld_runs": 128,
        "window_rows": 46080,
        "sequence_rows": 11520,
    }
    if counts != expected:
        raise MaterializationError(f"ns-3 候选数量不符合合同：{counts}")
    if any(
        row["truth_queue_balance_residual_l3_bytes"] != 0
        or row["truth_queue_balance_residual_packets"] != 0
        for row in window_rows
    ):
        raise MaterializationError("ns-3 物理目标存在非零守恒残差")
    return window_rows, sequence_rows, counts


def _build_quic_seed_rows(
    trace_rows: Sequence[Mapping[str, Any]], source_manifest_sha256: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    ordered = sorted(trace_rows, key=lambda row: str(row["content_sha256"]))
    output: list[dict[str, Any]] = []
    environments: Counter[str] = Counter()
    full_windows = 0
    full_sequences = 0
    for stable_order, row in enumerate(ordered):
        path_parts = str(row["canonical_path"]).split("/")
        environment = "/".join(path_parts[:2])
        environments[environment] += 1
        duration_ns = int(row["duration_ns"])
        trace_windows = duration_ns // 100_000_000
        trace_sequences = trace_windows // 4
        full_windows += trace_windows
        full_sequences += trace_sequences
        truth_mask = dict(row["privileged_truth_mask"])
        required_true = (
            "sent_packet_number",
            "ack_ranges",
            "latest_min_smoothed_rtt",
            "endpoint_packet_loss",
            "bytes_in_flight",
            "congestion_window",
        )
        if not all(bool(truth_mask[field]) for field in required_true):
            raise MaterializationError("QUIC qlog 核心真值掩码不完整")
        if bool(truth_mask["pto_event"]):
            raise MaterializationError("QUIC PTO 状态与冻结审计不一致")
        output.append(
            {
                "schema_version": SCHEMA_VERSION,
                "trace_id": str(row["trace_id"]),
                "stable_order": stable_order,
                "group_id_sha256": str(row["group_id_sha256"]),
                "content_sha256": str(row["content_sha256"]),
                "size_bytes": int(row["size_bytes"]),
                "split_id": "seed-validation-only",
                "protocol_target": "QUIC",
                "effective_route_id": "UNKNOWN",
                "shared_expert_applicable": True,
                "quic_expert_applicable": False,
                "qlog_truth_available": True,
                "quic_seed_validation_only": True,
                "quic_formal_training_enabled": False,
                "observer_vantage_point": str(row["observer_vantage_point"]),
                "qlog_version": str(row["qlog_version"]),
                "quic_versions": list(row["quic_versions"]),
                "duration_ns": duration_ns,
                "potential_full_100ms_windows": trace_windows,
                "potential_nonoverlap_four_window_sequences": trace_sequences,
                "valid_ack_relations": int(
                    row["event_counts"]["valid_ack_relations"]
                ),
                "valid_packet_lost_relations": int(
                    row["event_counts"]["valid_packet_lost_relations"]
                ),
                "complete_rtt_states": int(row["event_counts"]["complete_rtt"]),
                "bytes_in_flight_states": int(
                    row["event_counts"]["bytes_in_flight"]
                ),
                "congestion_window_states": int(
                    row["event_counts"]["congestion_window"]
                ),
                "pto_observed": False,
                "malicious_label_available": False,
                "source_trace_manifest_sha256": source_manifest_sha256,
                "final_test_visible": False,
            }
        )
    if len(output) != 59:
        raise MaterializationError("QUIC qlog 候选数不是 59")
    if len({row["group_id_sha256"] for row in output}) != 59:
        raise MaterializationError("QUIC qlog 独立组数不是 59")
    summary = {
        "trace_count": len(output),
        "independent_group_count": len({row["group_id_sha256"] for row in output}),
        "environment_path_counts": dict(sorted(environments.items())),
        "potential_full_100ms_windows": full_windows,
        "potential_nonoverlap_four_window_sequences": full_sequences,
        "formal_training_eligible": False,
    }
    return output, summary


def _route_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("sample_id", pa.string(), nullable=False),
            pa.field("stable_order", pa.int64(), nullable=False),
            pa.field("source_dataset", pa.string(), nullable=False),
            pa.field("split_id", pa.string(), nullable=False),
            pa.field("transport_family", pa.string(), nullable=False),
            pa.field("transport_family_observed", pa.bool_(), nullable=False),
            pa.field("protocol_target", pa.string(), nullable=False),
            pa.field("route_id", pa.string(), nullable=False),
            pa.field("route_confidence", pa.float32(), nullable=False),
            pa.field("route_confidence_observed", pa.bool_(), nullable=False),
            pa.field("shared_expert_applicable", pa.bool_(), nullable=False),
            pa.field("tcp_expert_applicable", pa.bool_(), nullable=False),
            pa.field("udp_expert_applicable", pa.bool_(), nullable=False),
            pa.field("quic_expert_applicable", pa.bool_(), nullable=False),
            pa.field("qlog_truth_available", pa.bool_(), nullable=False),
            pa.field("quic_formal_training_enabled", pa.bool_(), nullable=False),
            pa.field("stop_gradient_route", pa.bool_(), nullable=False),
            pa.field("final_test_visible", pa.bool_(), nullable=False),
        ]
    )


def _history_schema() -> pa.Schema:
    fields = [
        pa.field("sample_id", pa.string(), nullable=False),
        pa.field("stable_order", pa.int64(), nullable=False),
        pa.field("source_dataset", pa.string(), nullable=False),
        pa.field("split_id", pa.string(), nullable=False),
        pa.field("window_index", pa.int8(), nullable=False),
        pa.field("packet_start_index", pa.int32(), nullable=False),
        pa.field("packet_stop_index", pa.int32(), nullable=False),
        pa.field("window_valid", pa.bool_(), nullable=False),
        pa.field("history_available", pa.bool_(), nullable=False),
    ]
    fields.extend(pa.field(field, pa.float64(), nullable=True) for field in VALUE_FIELDS)
    fields.extend(
        pa.field(f"{field}_missing", pa.bool_(), nullable=False)
        for field in VALUE_FIELDS
    )
    fields.append(pa.field("final_test_visible", pa.bool_(), nullable=False))
    return pa.schema(fields)


def _ns3_schema(rows: Sequence[Mapping[str, Any]]) -> pa.Schema:
    if not rows:
        raise MaterializationError("ns-3 物理目标为空")
    # TCP 和 UDP 的专属真值互为空值，必须基于全部路由推断列类型。
    sample_table = pa.Table.from_pylist([dict(row) for row in rows])
    fields: list[pa.Field] = []
    nullable_names = {
        "truth_tcp_cwnd_mean_bytes",
        "truth_tcp_cwnd_min_bytes",
        "truth_tcp_cwnd_max_bytes",
        "truth_udp_planned_app_payload_packets",
        "truth_udp_planned_app_payload_bytes",
        "truth_udp_actual_send_events",
        "truth_udp_actual_send_bytes",
        "truth_udp_target_rate_bps",
        "truth_udp_burst_mode",
        "truth_udp_burst_active",
    }
    for field in sample_table.schema:
        fields.append(
            pa.field(field.name, field.type, nullable=field.name in nullable_names)
        )
    return pa.schema(fields)


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
    config_path = config_path.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise MaterializationError("配置顶层不是对象")
    if config.get("schema_version") != "flow_probe_r2_final_sidecar_data_contract_v1":
        raise MaterializationError("配置模式版本不正确")
    if config.get("final_test_visible") is not False:
        raise MaterializationError("最终测试可见性必须为 false")

    input_paths: dict[str, Path] = {}
    for name, raw_spec in dict(config["inputs"]).items():
        spec = dict(raw_spec)
        path = _resolve_input(project_root, repository_root, spec)
        input_paths[name] = path
        if "sha256" in spec:
            _validate_input(path, str(spec["sha256"]))
    ns3_root = _resolve_input(
        project_root, repository_root, dict(config["inputs"]["ns3_root"])
    )
    if not ns3_root.is_dir() or ns3_root.is_symlink():
        raise MaterializationError("ns-3 输入根不是普通目录")

    output_root = project_root / str(config["output_root"])
    partial_root = output_root.with_name(f"{output_root.name}.partial")
    if output_root.exists() or partial_root.exists():
        raise MaterializationError("输出根或阶段根已存在，拒绝覆盖")
    partial_root.mkdir(parents=True)

    try:
        candidate_rows = _load_jsonl(input_paths["candidate_manifest"])
        if len(candidate_rows) != 10000:
            raise MaterializationError("共同候选清单不是 10,000 行")
        detection_rows = _candidate_detection_rows(candidate_rows)
        detection_path = partial_root / "detection-pool-manifest.jsonl"
        detection_semantic = _write_jsonl(detection_path, detection_rows)

        route_rows = _build_route_assignments(
            detection_rows,
            input_paths["genis_flows"],
            input_paths["tqhc2_protocol"],
        )
        route_schema = _route_schema()
        route_path = partial_root / "route-assignments.parquet"
        _write_parquet(route_path, route_rows, route_schema)
        route_semantic = _semantic_sha256(route_rows)

        history_rows, tqhc2_packet_rows = _build_common_history(
            detection_rows, input_paths["tqhc2_packets"]
        )
        history_schema = _history_schema()
        history_path = partial_root / "common-history.parquet"
        _write_parquet(history_path, history_rows, history_schema)
        history_semantic = _semantic_sha256(history_rows)

        ns3_manifest_rows = _load_jsonl(input_paths["ns3_manifest"])
        if len(ns3_manifest_rows) != 512:
            raise MaterializationError("ns-3 清单不是 512 行")
        ns3_rows, ns3_sequences, ns3_counts = _build_ns3_physics(
            ns3_manifest_rows, ns3_root
        )
        ns3_schema = _ns3_schema(ns3_rows)
        ns3_path = partial_root / "physics-targets-ns3.parquet"
        _write_parquet(ns3_path, ns3_rows, ns3_schema)
        ns3_semantic = _semantic_sha256(ns3_rows)
        ns3_sequence_path = partial_root / "ns3-sequence-manifest.jsonl"
        ns3_sequence_semantic = _write_jsonl(ns3_sequence_path, ns3_sequences)

        quic_source_sha = str(config["inputs"]["quic_trace_manifest"]["sha256"])
        quic_rows, quic_summary = _build_quic_seed_rows(
            _load_jsonl(input_paths["quic_trace_manifest"]), quic_source_sha
        )
        quic_path = partial_root / "quic-seed-traces.jsonl"
        quic_semantic = _write_jsonl(quic_path, quic_rows)

        contract_path = partial_root / "contract.json"
        contract_semantic = _write_json(contract_path, config)

        source_lock = {
            "schema_version": "flow_probe_r2_final_sidecar_source_lock_v1",
            "config_sha256": _sha256_file(config_path),
            "final_test_visible": False,
            "inputs": [
                {
                    "role": name,
                    "logical_path": dict(config["inputs"])[name]["path"],
                    "size_bytes": path.stat().st_size
                    if path.is_file()
                    else None,
                    "sha256": _sha256_file(path) if path.is_file() else None,
                }
                for name, path in sorted(input_paths.items())
            ],
            "ns3_directory_role": "paired_tcp_udp_physics_source",
            "ns3_source_lock_sha256": str(
                config["inputs"]["ns3_source_lock"]["sha256"]
            ),
        }
        source_lock_path = partial_root / "source-lock.json"
        source_lock_semantic = _write_json(source_lock_path, source_lock)

        route_counts = Counter(str(row["route_id"]) for row in route_rows)
        route_counts_by_source: dict[str, dict[str, int]] = {}
        for source in ("genis", "tqhc2"):
            route_counts_by_source[source] = dict(
                sorted(
                    Counter(
                        str(row["route_id"])
                        for row in route_rows
                        if row["source_dataset"] == source
                    ).items()
                )
            )
        history_counts = Counter(
            str(row["source_dataset"])
            for row in history_rows
            if bool(row["history_available"])
        )
        input_summary = {
            "schema_version": "flow_probe_r2_final_sidecar_input_summary_v1",
            "dataset_version": config["dataset_version"],
            "stage": config["stage"],
            "status": config["status"],
            "final_test_visible": False,
            "detection_pool": {
                "rows": len(detection_rows),
                "source_counts": dict(
                    sorted(
                        Counter(
                            str(row["source_dataset"]) for row in detection_rows
                        ).items()
                    )
                ),
                "candidate_order_semantic_sha256": detection_semantic,
                "classifier_view_materialized_locally": False,
            },
            "route_assignments": {
                "rows": len(route_rows),
                "route_counts": dict(sorted(route_counts.items())),
                "route_counts_by_source": route_counts_by_source,
                "quic_formal_training_enabled": False,
            },
            "common_history": {
                "rows": len(history_rows),
                "window_count_per_sample": 4,
                "tqhc2_source_packet_rows": tqhc2_packet_rows,
                "history_available_window_counts": dict(sorted(history_counts.items())),
                "genis_history_policy": "explicit_missing",
            },
            "ns3_physics": ns3_counts,
            "quic_seed_validation": quic_summary,
            "blocked_or_withheld": {
                "genis_network_layer_history": "TotBytes 已证明至少一条为二层口径",
                "ns3_splits": list(WITHHELD_NS3_SPLITS),
                "tcp_truth_fields_missing": [
                    "rtt",
                    "bytes_in_flight",
                    "ack",
                    "retransmission",
                ],
                "quic_formal_training": "59 个单实现单草案连接不足以正式训练",
                "local_classifier_view": "服务器冻结 shared-b0 视图未在本机落盘",
            },
        }
        input_summary_path = partial_root / "input-summary.json"
        input_summary_semantic = _write_json(input_summary_path, input_summary)

        schema_document = {
            "schema_version": "flow_probe_r2_final_sidecar_schema_v1",
            "route_assignments": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in route_schema
            ],
            "common_history": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in history_schema
            ],
            "physics_targets_ns3": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in ns3_schema
            ],
            "ordering": {
                "detection_pool": ["stable_order"],
                "route_assignments": ["stable_order"],
                "common_history": ["stable_order", "window_index"],
                "physics_targets_ns3": [
                    "sequence_stable_order",
                    "window_index_in_sequence",
                ],
                "quic_seed_traces": ["stable_order"],
            },
        }
        schema_path = partial_root / "schema.json"
        schema_semantic = _write_json(schema_path, schema_document)

        artifacts = [
            _artifact_entry(
                detection_path,
                partial_root,
                row_count=len(detection_rows),
                schema_sha256=None,
                semantic_sha256=detection_semantic,
            ),
            _artifact_entry(
                route_path,
                partial_root,
                row_count=len(route_rows),
                schema_sha256=_schema_sha256(route_schema),
                semantic_sha256=route_semantic,
            ),
            _artifact_entry(
                history_path,
                partial_root,
                row_count=len(history_rows),
                schema_sha256=_schema_sha256(history_schema),
                semantic_sha256=history_semantic,
            ),
            _artifact_entry(
                ns3_path,
                partial_root,
                row_count=len(ns3_rows),
                schema_sha256=_schema_sha256(ns3_schema),
                semantic_sha256=ns3_semantic,
            ),
            _artifact_entry(
                ns3_sequence_path,
                partial_root,
                row_count=len(ns3_sequences),
                schema_sha256=None,
                semantic_sha256=ns3_sequence_semantic,
            ),
            _artifact_entry(
                quic_path,
                partial_root,
                row_count=len(quic_rows),
                schema_sha256=None,
                semantic_sha256=quic_semantic,
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
                input_summary_path,
                partial_root,
                row_count=None,
                schema_sha256=None,
                semantic_sha256=input_summary_semantic,
            ),
            _artifact_entry(
                schema_path,
                partial_root,
                row_count=None,
                schema_sha256=None,
                semantic_sha256=schema_semantic,
            ),
        ]
        artifacts.sort(key=lambda item: str(item["relative_path"]))
        manifest = {
            "schema_version": "flow_probe_r2_final_sidecar_artifact_manifest_v1",
            "dataset_version": config["dataset_version"],
            "stage": config["stage"],
            "status": config["status"],
            "final_test_visible": False,
            "artifacts": artifacts,
            "artifact_payload_merkle_sha256": _sha256_bytes(
                _canonical_json(artifacts).encode("utf-8")
            ),
        }
        _write_json(partial_root / "artifact-manifest.json", manifest)

        os.rename(partial_root, output_root)
        return output_root
    except BaseException:
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
