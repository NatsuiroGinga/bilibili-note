from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from r2_final_sidecar_candidate_materialize import (
    MaterializationError,
    _artifact_entry,
    _canonical_json,
    _load_jsonl,
    _schema_sha256,
    _sha256_bytes,
    _sha256_file,
    _validate_input,
    _write_json,
    _write_jsonl,
)


CONFIG_SCHEMA_VERSION = "flow_probe_r2_final_tcp_udp_physics_materialization_v1"
POOL_SCHEMA_VERSION = "flow_probe_r2_final_tcp_udp_physics_pool_v2"
MAIN_SOURCE_SCHEMA = "flow_probe_r2_ns3_protocol_windows_v2"
TCP_SOURCE_SCHEMA = "flow_probe_r2_ns3_tcp_sender_windows_v2"
RECEIPT_SCHEMA = "flow_probe_r2_ns3_protocol_dynamics_v2_run_receipt_v1"
RUN_PATH_PATTERN = re.compile(
    r"^shards/shard-\d{2}/runs/(\d{4})-(tcp|udp)-([0-9a-f]{12})/receipt\.json$"
)

MAIN_SOURCE_COLUMNS = (
    "schema_version",
    "physics_group_sha256",
    "matrix_config_sha256",
    "tcp_truth_contract_sha256",
    "split",
    "run_seed",
    "transport_family",
    "window_index",
    "window_start_s",
    "window_end_s",
    "window_duration_s",
    "public_total_packets",
    "public_total_l3_bytes",
    "truth_queue_start_l3_bytes",
    "truth_queue_end_l3_bytes",
    "truth_qdisc_received_l3_bytes",
    "truth_qdisc_enqueued_l3_bytes",
    "truth_qdisc_dequeued_l3_bytes",
    "truth_qdisc_drop_before_enqueue_l3_bytes",
    "truth_qdisc_drop_after_dequeue_l3_bytes",
    "truth_queue_start_packets",
    "truth_queue_end_packets",
    "truth_qdisc_received_packets",
    "truth_qdisc_enqueued_packets",
    "truth_qdisc_dequeued_packets",
    "truth_qdisc_drop_before_enqueue_packets",
    "truth_qdisc_drop_after_dequeue_packets",
    "truth_queue_balance_residual_l3_bytes",
    "truth_queue_balance_residual_packets",
    "truth_udp_applicable",
    "truth_udp_burst_active_duration_s",
    "truth_udp_planned_app_payload_packets",
    "truth_udp_planned_app_payload_bytes",
    "truth_udp_actual_send_packets",
    "truth_udp_actual_send_bytes",
    "truth_udp_app_drop_packets",
    "truth_udp_app_drop_bytes",
    "truth_udp_backlog_applicable",
    "truth_udp_backlog_start_bytes",
    "truth_udp_backlog_end_bytes",
)

TCP_SOURCE_COLUMNS = (
    "schema_version",
    "physics_group_sha256",
    "matrix_config_sha256",
    "tcp_truth_contract_sha256",
    "split",
    "run_seed",
    "transport_family",
    "window_index",
    "window_start_s",
    "window_end_s",
    "window_duration_s",
    "sender_index",
    "trace_connected",
    "segment_size_bytes",
    "cwnd_start_observed",
    "cwnd_start_bytes",
    "cwnd_end_observed",
    "cwnd_end_bytes",
    "ssthresh_start_observed",
    "ssthresh_start_bytes",
    "ssthresh_end_observed",
    "ssthresh_end_bytes",
    "bytes_in_flight_start_observed",
    "bytes_in_flight_start_bytes",
    "bytes_in_flight_end_observed",
    "bytes_in_flight_end_bytes",
    "cong_state_start",
    "cong_state_end",
    "acked_bytes_observed",
    "acked_bytes",
    "acked_segments_observed",
    "acked_segments",
    "rtt_observed",
    "rtt_sample_count",
    "rtt_mean_ms",
    "rtt_min_ms",
    "rtt_max_ms",
    "loss_event_count_observed",
    "loss_event_count",
    "timeout_event_count_observed",
    "timeout_event_count",
    "cwnd_contraction_event_count",
    "ssthresh_contraction_event_count",
    "ack_residual_numerator_sum_bytes",
    "ack_residual_squared_sum_bytes2",
    "ack_residual_scale_squared_sum_bytes2",
    "ack_residual_normalized_squared_sum",
    "ack_residual_valid_terms",
    "ack_residual_mse_bytes2",
    "ack_residual_normalized_mse",
    "loss_residual_numerator_sum_bytes",
    "loss_residual_squared_sum_bytes2",
    "loss_residual_scale_squared_sum_bytes2",
    "loss_residual_normalized_squared_sum",
    "loss_residual_valid_terms",
    "loss_residual_mse_bytes2",
    "loss_residual_normalized_mse",
)


class ParquetSink:
    def __init__(self, path: Path, schema: pa.Schema) -> None:
        self.path = path
        self.schema = schema
        self.row_count = 0
        self._semantic_digest = hashlib.sha256()
        self._order_digest = hashlib.sha256()
        self._writer = pq.ParquetWriter(
            path,
            schema,
            version="2.6",
            compression="zstd",
            compression_level=9,
            use_dictionary=False,
            write_statistics=True,
            data_page_version="1.0",
        )

    def write(self, rows: Sequence[Mapping[str, Any]], order_keys: Sequence[str]) -> None:
        if len(rows) != len(order_keys):
            raise MaterializationError("数据行与顺序键数量不一致")
        if not rows:
            return
        serialised = [dict(row) for row in rows]
        self._writer.write_table(pa.Table.from_pylist(serialised, schema=self.schema))
        for row, order_key in zip(serialised, order_keys, strict=True):
            self._semantic_digest.update(_canonical_json(row).encode("utf-8"))
            self._semantic_digest.update(b"\n")
            self._order_digest.update(order_key.encode("utf-8"))
            self._order_digest.update(b"\n")
        self.row_count += len(serialised)

    def close(self) -> None:
        self._writer.close()

    @property
    def semantic_sha256(self) -> str:
        return self._semantic_digest.hexdigest()

    @property
    def ordering_sha256(self) -> str:
        return self._order_digest.hexdigest()


def _field(name: str, data_type: pa.DataType, nullable: bool = False) -> pa.Field:
    return pa.field(name, data_type, nullable=nullable)


def _window_schema() -> pa.Schema:
    fields = [
        _field("schema_version", pa.string()),
        _field("sequence_id", pa.string()),
        _field("evaluation_cluster_id", pa.string()),
        _field("sequence_stable_order", pa.int64()),
        _field("run_stable_order", pa.int64()),
        _field("physics_group_sha256", pa.string()),
        _field("matrix_config_sha256", pa.string()),
        _field("tcp_truth_contract_sha256", pa.string()),
        _field("split_id", pa.string()),
        _field("run_seed", pa.int64()),
        _field("transport_family", pa.string()),
        _field("route_id", pa.string()),
        _field("route_confidence", pa.float64()),
        _field("stop_gradient_route", pa.bool_()),
        _field("sequence_index", pa.int64()),
        _field("window_index_in_sequence", pa.int64()),
        _field("source_window_index", pa.int64()),
        _field("window_start_s", pa.float64()),
        _field("window_end_s", pa.float64()),
        _field("truth_window_duration_s", pa.float64()),
        _field("public_total_packets", pa.int64()),
        _field("public_total_l3_bytes", pa.int64()),
        _field("public_packet_rate_pps", pa.float64()),
        _field("public_byte_rate_Bps", pa.float64()),
        _field("truth_shared_applicable", pa.bool_()),
        _field("truth_shared_observed", pa.bool_()),
    ]
    for name in (
        "truth_queue_start_l3_bytes",
        "truth_queue_end_l3_bytes",
        "truth_qdisc_received_l3_bytes",
        "truth_qdisc_enqueued_l3_bytes",
        "truth_qdisc_dequeued_l3_bytes",
        "truth_qdisc_drop_before_enqueue_l3_bytes",
        "truth_qdisc_drop_after_dequeue_l3_bytes",
        "truth_queue_start_packets",
        "truth_queue_end_packets",
        "truth_qdisc_received_packets",
        "truth_qdisc_enqueued_packets",
        "truth_qdisc_dequeued_packets",
        "truth_qdisc_drop_before_enqueue_packets",
        "truth_qdisc_drop_after_dequeue_packets",
        "truth_queue_balance_residual_l3_bytes",
        "truth_queue_balance_residual_packets",
    ):
        fields.append(_field(name, pa.int64()))
    fields.extend(
        [
            _field("truth_tcp_applicable", pa.bool_()),
            _field("truth_tcp_sender_truth_available", pa.bool_()),
            _field("truth_udp_applicable", pa.bool_()),
            _field("truth_udp_observed", pa.bool_()),
            _field("truth_udp_burst_active_duration_s", pa.float64(), True),
            _field("truth_udp_planned_app_payload_packets", pa.int64(), True),
            _field("truth_udp_planned_app_payload_bytes", pa.int64(), True),
            _field("truth_udp_actual_send_packets", pa.int64(), True),
            _field("truth_udp_actual_send_bytes", pa.int64(), True),
            _field("truth_udp_app_drop_packets", pa.int64(), True),
            _field("truth_udp_app_drop_bytes", pa.int64(), True),
            _field("truth_udp_backlog_applicable", pa.bool_()),
            _field("truth_udp_backlog_start_bytes", pa.int64(), True),
            _field("truth_udp_backlog_end_bytes", pa.int64(), True),
            _field("source_main_csv_sha256", pa.string()),
            _field("source_receipt_sha256", pa.string()),
            _field("review_status", pa.string()),
            _field("final_test_visible", pa.bool_()),
        ]
    )
    return pa.schema(fields)


def _tcp_schema() -> pa.Schema:
    fields = [
        _field("schema_version", pa.string()),
        _field("sequence_id", pa.string()),
        _field("evaluation_cluster_id", pa.string()),
        _field("sequence_stable_order", pa.int64()),
        _field("run_stable_order", pa.int64()),
        _field("physics_group_sha256", pa.string()),
        _field("matrix_config_sha256", pa.string()),
        _field("tcp_truth_contract_sha256", pa.string()),
        _field("split_id", pa.string()),
        _field("run_seed", pa.int64()),
        _field("transport_family", pa.string()),
        _field("sequence_index", pa.int64()),
        _field("window_index_in_sequence", pa.int64()),
        _field("source_window_index", pa.int64()),
        _field("window_start_s", pa.float64()),
        _field("window_end_s", pa.float64()),
        _field("truth_window_duration_s", pa.float64()),
        _field("sender_index", pa.int64()),
        _field("trace_connected", pa.bool_()),
        _field("segment_size_bytes", pa.int64()),
    ]
    observed_value_pairs = (
        ("cwnd_start_observed", "truth_tcp_cwnd_start_bytes", pa.int64()),
        ("cwnd_end_observed", "truth_tcp_cwnd_end_bytes", pa.int64()),
        ("ssthresh_start_observed", "truth_tcp_ssthresh_start_bytes", pa.int64()),
        ("ssthresh_end_observed", "truth_tcp_ssthresh_end_bytes", pa.int64()),
        (
            "bytes_in_flight_start_observed",
            "truth_tcp_bytes_in_flight_start_bytes",
            pa.int64(),
        ),
        (
            "bytes_in_flight_end_observed",
            "truth_tcp_bytes_in_flight_end_bytes",
            pa.int64(),
        ),
        ("acked_bytes_observed", "truth_tcp_acked_bytes", pa.int64()),
        ("acked_segments_observed", "truth_tcp_acked_segments", pa.int64()),
        ("loss_event_count_observed", "truth_tcp_loss_event_count", pa.int64()),
        (
            "timeout_event_count_observed",
            "truth_tcp_timeout_event_count",
            pa.int64(),
        ),
    )
    for observed, value, data_type in observed_value_pairs:
        fields.append(_field(observed, pa.bool_()))
        fields.append(_field(value, data_type, True))
    fields.extend(
        [
            _field("truth_tcp_cong_state_start", pa.int64(), True),
            _field("truth_tcp_cong_state_end", pa.int64(), True),
            _field("rtt_observed", pa.bool_()),
            _field("truth_tcp_rtt_sample_count", pa.int64()),
            _field("truth_tcp_rtt_mean_ms", pa.float64(), True),
            _field("truth_tcp_rtt_min_ms", pa.float64(), True),
            _field("truth_tcp_rtt_max_ms", pa.float64(), True),
            _field("truth_tcp_cwnd_contraction_event_count", pa.int64()),
            _field("truth_tcp_ssthresh_contraction_event_count", pa.int64()),
        ]
    )
    for prefix in ("ack", "loss"):
        fields.extend(
            [
                _field(f"truth_tcp_{prefix}_residual_numerator_sum_bytes", pa.float64()),
                _field(f"truth_tcp_{prefix}_residual_squared_sum_bytes2", pa.float64()),
                _field(f"truth_tcp_{prefix}_residual_scale_squared_sum_bytes2", pa.float64()),
                _field(f"truth_tcp_{prefix}_residual_normalized_squared_sum", pa.float64()),
                _field(f"truth_tcp_{prefix}_residual_valid_terms", pa.int64()),
                _field(f"truth_tcp_{prefix}_residual_mse_bytes2", pa.float64(), True),
                _field(f"truth_tcp_{prefix}_residual_normalized_mse", pa.float64(), True),
            ]
        )
    fields.extend(
        [
            _field("source_tcp_csv_sha256", pa.string()),
            _field("source_receipt_sha256", pa.string()),
            _field("review_status", pa.string()),
            _field("final_test_visible", pa.bool_()),
        ]
    )
    return pa.schema(fields)


def _udp_schema() -> pa.Schema:
    fields = [
        _field("schema_version", pa.string()),
        _field("sequence_id", pa.string()),
        _field("evaluation_cluster_id", pa.string()),
        _field("sequence_stable_order", pa.int64()),
        _field("run_stable_order", pa.int64()),
        _field("physics_group_sha256", pa.string()),
        _field("matrix_config_sha256", pa.string()),
        _field("tcp_truth_contract_sha256", pa.string()),
        _field("split_id", pa.string()),
        _field("run_seed", pa.int64()),
        _field("transport_family", pa.string()),
        _field("sequence_index", pa.int64()),
        _field("window_index_in_sequence", pa.int64()),
        _field("source_window_index", pa.int64()),
        _field("window_start_s", pa.float64()),
        _field("window_end_s", pa.float64()),
        _field("truth_window_duration_s", pa.float64()),
        _field("truth_udp_applicable", pa.bool_()),
        _field("truth_udp_observed", pa.bool_()),
        _field("truth_udp_burst_active_duration_s", pa.float64()),
        _field("truth_udp_planned_app_payload_packets", pa.int64()),
        _field("truth_udp_planned_app_payload_bytes", pa.int64()),
        _field("truth_udp_actual_send_packets", pa.int64()),
        _field("truth_udp_actual_send_bytes", pa.int64()),
        _field("truth_udp_app_drop_packets", pa.int64()),
        _field("truth_udp_app_drop_bytes", pa.int64()),
        _field("truth_udp_backlog_applicable", pa.bool_()),
        _field("truth_udp_backlog_start_bytes", pa.int64(), True),
        _field("truth_udp_backlog_end_bytes", pa.int64(), True),
        _field("truth_udp_packet_balance_residual", pa.int64()),
        _field("truth_udp_byte_balance_residual", pa.int64()),
        _field("source_main_csv_sha256", pa.string()),
        _field("source_receipt_sha256", pa.string()),
        _field("review_status", pa.string()),
        _field("final_test_visible", pa.bool_()),
    ]
    return pa.schema(fields)


def _parse_bool(value: str, field_name: str) -> bool:
    if value not in {"0", "1"}:
        raise MaterializationError(f"{field_name} 不是 0/1：{value}")
    return value == "1"


def _optional_int(value: str) -> int | None:
    return int(value) if value != "" else None


def _optional_float(value: str) -> float | None:
    return float(value) if value != "" else None


def _load_csv(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(expected_columns):
            raise MaterializationError(f"CSV 模式不符合 v2 合同：{path}")
        return list(reader)


def _sequence_values(
    manifest_row: Mapping[str, Any], run_order: int, window_index: int
) -> dict[str, Any]:
    group = str(manifest_row["physics_group_sha256"])
    transport = str(manifest_row["transport_family"])
    sequence_index = window_index // 4
    sequence_order = run_order * 30 + sequence_index
    return {
        "sequence_id": f"ns3-r2-v2:{group}:{transport}:{sequence_index:02d}",
        "evaluation_cluster_id": f"ns3-r2-v2:{group}:{transport}",
        "sequence_stable_order": sequence_order,
        "sequence_index": sequence_index,
        "window_index_in_sequence": window_index % 4,
    }


def _validate_identity(
    source_row: Mapping[str, str], manifest_row: Mapping[str, Any], source_schema: str
) -> None:
    expected = {
        "schema_version": source_schema,
        "physics_group_sha256": str(manifest_row["physics_group_sha256"]),
        "matrix_config_sha256": str(manifest_row["matrix_config_sha256"]),
        "split": str(manifest_row["split"]),
        "run_seed": str(manifest_row["run_seed"]),
        "transport_family": str(manifest_row["transport_family"]),
    }
    mismatches = {
        key: (source_row.get(key), value)
        for key, value in expected.items()
        if source_row.get(key) != value
    }
    if mismatches:
        raise MaterializationError(f"CSV 身份与冻结清单不一致：{mismatches}")


def _window_row(
    manifest_row: Mapping[str, Any],
    source_row: Mapping[str, str],
    *,
    run_order: int,
    main_sha256: str,
    receipt_sha256: str,
) -> dict[str, Any]:
    _validate_identity(source_row, manifest_row, MAIN_SOURCE_SCHEMA)
    window_index = int(source_row["window_index"])
    sequence = _sequence_values(manifest_row, run_order, window_index)
    duration = float(source_row["window_duration_s"])
    packets = int(source_row["public_total_packets"])
    bytes_count = int(source_row["public_total_l3_bytes"])
    transport = str(manifest_row["transport_family"])
    udp_applicable = _parse_bool(source_row["truth_udp_applicable"], "truth_udp_applicable")
    udp = transport == "UDP"
    if udp_applicable != udp:
        raise MaterializationError("UDP 适用掩码与协议不一致")
    backlog_raw = source_row["truth_udp_backlog_applicable"]
    if udp:
        backlog_applicable = _parse_bool(backlog_raw, "truth_udp_backlog_applicable")
    else:
        if backlog_raw != "":
            raise MaterializationError("TCP 行不得携带 UDP 积压适用状态")
        backlog_applicable = False
    row: dict[str, Any] = {
        "schema_version": POOL_SCHEMA_VERSION,
        **sequence,
        "run_stable_order": run_order,
        "physics_group_sha256": str(manifest_row["physics_group_sha256"]),
        "matrix_config_sha256": str(manifest_row["matrix_config_sha256"]),
        "tcp_truth_contract_sha256": source_row["tcp_truth_contract_sha256"],
        "split_id": str(manifest_row["split"]),
        "run_seed": int(manifest_row["run_seed"]),
        "transport_family": transport,
        "route_id": transport,
        "route_confidence": 1.0,
        "stop_gradient_route": True,
        "source_window_index": window_index,
        "window_start_s": float(source_row["window_start_s"]),
        "window_end_s": float(source_row["window_end_s"]),
        "truth_window_duration_s": duration,
        "public_total_packets": packets,
        "public_total_l3_bytes": bytes_count,
        "public_packet_rate_pps": packets / duration,
        "public_byte_rate_Bps": bytes_count / duration,
        "truth_shared_applicable": True,
        "truth_shared_observed": True,
        "truth_tcp_applicable": transport == "TCP",
        "truth_tcp_sender_truth_available": transport == "TCP",
        "truth_udp_applicable": udp,
        "truth_udp_observed": udp,
        "truth_udp_burst_active_duration_s": _optional_float(
            source_row["truth_udp_burst_active_duration_s"]
        ),
        "truth_udp_planned_app_payload_packets": _optional_int(
            source_row["truth_udp_planned_app_payload_packets"]
        ),
        "truth_udp_planned_app_payload_bytes": _optional_int(
            source_row["truth_udp_planned_app_payload_bytes"]
        ),
        "truth_udp_actual_send_packets": _optional_int(
            source_row["truth_udp_actual_send_packets"]
        ),
        "truth_udp_actual_send_bytes": _optional_int(
            source_row["truth_udp_actual_send_bytes"]
        ),
        "truth_udp_app_drop_packets": _optional_int(
            source_row["truth_udp_app_drop_packets"]
        ),
        "truth_udp_app_drop_bytes": _optional_int(source_row["truth_udp_app_drop_bytes"]),
        "truth_udp_backlog_applicable": backlog_applicable,
        "truth_udp_backlog_start_bytes": _optional_int(
            source_row["truth_udp_backlog_start_bytes"]
        ),
        "truth_udp_backlog_end_bytes": _optional_int(
            source_row["truth_udp_backlog_end_bytes"]
        ),
        "source_main_csv_sha256": main_sha256,
        "source_receipt_sha256": receipt_sha256,
        "review_status": "review_pending",
        "final_test_visible": False,
    }
    for name in (
        "truth_queue_start_l3_bytes",
        "truth_queue_end_l3_bytes",
        "truth_qdisc_received_l3_bytes",
        "truth_qdisc_enqueued_l3_bytes",
        "truth_qdisc_dequeued_l3_bytes",
        "truth_qdisc_drop_before_enqueue_l3_bytes",
        "truth_qdisc_drop_after_dequeue_l3_bytes",
        "truth_queue_start_packets",
        "truth_queue_end_packets",
        "truth_qdisc_received_packets",
        "truth_qdisc_enqueued_packets",
        "truth_qdisc_dequeued_packets",
        "truth_qdisc_drop_before_enqueue_packets",
        "truth_qdisc_drop_after_dequeue_packets",
        "truth_queue_balance_residual_l3_bytes",
        "truth_queue_balance_residual_packets",
    ):
        row[name] = int(source_row[name])
    if row["truth_queue_balance_residual_l3_bytes"] != 0:
        raise MaterializationError("队列字节守恒残差不为零")
    if row["truth_queue_balance_residual_packets"] != 0:
        raise MaterializationError("队列包守恒残差不为零")
    return row


def _udp_row(window_row: Mapping[str, Any]) -> dict[str, Any]:
    planned_packets = int(window_row["truth_udp_planned_app_payload_packets"])
    planned_bytes = int(window_row["truth_udp_planned_app_payload_bytes"])
    actual_packets = int(window_row["truth_udp_actual_send_packets"])
    actual_bytes = int(window_row["truth_udp_actual_send_bytes"])
    drop_packets = int(window_row["truth_udp_app_drop_packets"])
    drop_bytes = int(window_row["truth_udp_app_drop_bytes"])
    return {
        key: window_row[key]
        for key in (
            "schema_version",
            "sequence_id",
            "evaluation_cluster_id",
            "sequence_stable_order",
            "run_stable_order",
            "physics_group_sha256",
            "matrix_config_sha256",
            "tcp_truth_contract_sha256",
            "split_id",
            "run_seed",
            "transport_family",
            "sequence_index",
            "window_index_in_sequence",
            "source_window_index",
            "window_start_s",
            "window_end_s",
            "truth_window_duration_s",
            "truth_udp_applicable",
            "truth_udp_observed",
            "truth_udp_burst_active_duration_s",
            "truth_udp_planned_app_payload_packets",
            "truth_udp_planned_app_payload_bytes",
            "truth_udp_actual_send_packets",
            "truth_udp_actual_send_bytes",
            "truth_udp_app_drop_packets",
            "truth_udp_app_drop_bytes",
            "truth_udp_backlog_applicable",
            "truth_udp_backlog_start_bytes",
            "truth_udp_backlog_end_bytes",
            "source_main_csv_sha256",
            "source_receipt_sha256",
            "review_status",
            "final_test_visible",
        )
    } | {
        "truth_udp_packet_balance_residual": planned_packets
        - actual_packets
        - drop_packets,
        "truth_udp_byte_balance_residual": planned_bytes - actual_bytes - drop_bytes,
    }


def _tcp_row(
    manifest_row: Mapping[str, Any],
    source_row: Mapping[str, str],
    *,
    run_order: int,
    tcp_sha256: str,
    receipt_sha256: str,
) -> dict[str, Any]:
    _validate_identity(source_row, manifest_row, TCP_SOURCE_SCHEMA)
    window_index = int(source_row["window_index"])
    sequence = _sequence_values(manifest_row, run_order, window_index)
    row: dict[str, Any] = {
        "schema_version": POOL_SCHEMA_VERSION,
        **sequence,
        "run_stable_order": run_order,
        "physics_group_sha256": str(manifest_row["physics_group_sha256"]),
        "matrix_config_sha256": str(manifest_row["matrix_config_sha256"]),
        "tcp_truth_contract_sha256": source_row["tcp_truth_contract_sha256"],
        "split_id": str(manifest_row["split"]),
        "run_seed": int(manifest_row["run_seed"]),
        "transport_family": "TCP",
        "source_window_index": window_index,
        "window_start_s": float(source_row["window_start_s"]),
        "window_end_s": float(source_row["window_end_s"]),
        "truth_window_duration_s": float(source_row["window_duration_s"]),
        "sender_index": int(source_row["sender_index"]),
        "trace_connected": _parse_bool(source_row["trace_connected"], "trace_connected"),
        "segment_size_bytes": int(source_row["segment_size_bytes"]),
        "truth_tcp_cong_state_start": _optional_int(source_row["cong_state_start"]),
        "truth_tcp_cong_state_end": _optional_int(source_row["cong_state_end"]),
        "rtt_observed": _parse_bool(source_row["rtt_observed"], "rtt_observed"),
        "truth_tcp_rtt_sample_count": int(source_row["rtt_sample_count"]),
        "truth_tcp_rtt_mean_ms": _optional_float(source_row["rtt_mean_ms"]),
        "truth_tcp_rtt_min_ms": _optional_float(source_row["rtt_min_ms"]),
        "truth_tcp_rtt_max_ms": _optional_float(source_row["rtt_max_ms"]),
        "truth_tcp_cwnd_contraction_event_count": int(
            source_row["cwnd_contraction_event_count"]
        ),
        "truth_tcp_ssthresh_contraction_event_count": int(
            source_row["ssthresh_contraction_event_count"]
        ),
        "source_tcp_csv_sha256": tcp_sha256,
        "source_receipt_sha256": receipt_sha256,
        "review_status": "review_pending",
        "final_test_visible": False,
    }
    observed_value_pairs = (
        ("cwnd_start_observed", "cwnd_start_bytes", "truth_tcp_cwnd_start_bytes"),
        ("cwnd_end_observed", "cwnd_end_bytes", "truth_tcp_cwnd_end_bytes"),
        (
            "ssthresh_start_observed",
            "ssthresh_start_bytes",
            "truth_tcp_ssthresh_start_bytes",
        ),
        (
            "ssthresh_end_observed",
            "ssthresh_end_bytes",
            "truth_tcp_ssthresh_end_bytes",
        ),
        (
            "bytes_in_flight_start_observed",
            "bytes_in_flight_start_bytes",
            "truth_tcp_bytes_in_flight_start_bytes",
        ),
        (
            "bytes_in_flight_end_observed",
            "bytes_in_flight_end_bytes",
            "truth_tcp_bytes_in_flight_end_bytes",
        ),
        ("acked_bytes_observed", "acked_bytes", "truth_tcp_acked_bytes"),
        ("acked_segments_observed", "acked_segments", "truth_tcp_acked_segments"),
        (
            "loss_event_count_observed",
            "loss_event_count",
            "truth_tcp_loss_event_count",
        ),
        (
            "timeout_event_count_observed",
            "timeout_event_count",
            "truth_tcp_timeout_event_count",
        ),
    )
    for observed_name, source_name, target_name in observed_value_pairs:
        observed = _parse_bool(source_row[observed_name], observed_name)
        value = _optional_int(source_row[source_name])
        if observed != (value is not None):
            raise MaterializationError(f"TCP 掩码和值不一致：{observed_name}/{source_name}")
        row[observed_name] = observed
        row[target_name] = value
    for prefix in ("ack", "loss"):
        for suffix in (
            "residual_numerator_sum_bytes",
            "residual_squared_sum_bytes2",
            "residual_scale_squared_sum_bytes2",
            "residual_normalized_squared_sum",
        ):
            row[f"truth_tcp_{prefix}_{suffix}"] = float(source_row[f"{prefix}_{suffix}"])
        row[f"truth_tcp_{prefix}_residual_valid_terms"] = int(
            source_row[f"{prefix}_residual_valid_terms"]
        )
        row[f"truth_tcp_{prefix}_residual_mse_bytes2"] = _optional_float(
            source_row[f"{prefix}_residual_mse_bytes2"]
        )
        row[f"truth_tcp_{prefix}_residual_normalized_mse"] = _optional_float(
            source_row[f"{prefix}_residual_normalized_mse"]
        )
    return row


def _artifact_index(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise MaterializationError("ns-3 制品清单不是数组")
    index: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict) or "logical_path" not in item:
            raise MaterializationError("ns-3 制品清单含非法项")
        logical_path = str(item["logical_path"])
        if logical_path in index:
            raise MaterializationError(f"ns-3 制品清单路径重复：{logical_path}")
        index[logical_path] = item
    return index


def _run_roots(index: Mapping[str, Mapping[str, Any]]) -> dict[int, str]:
    roots: dict[int, str] = {}
    for logical_path in index:
        match = RUN_PATH_PATTERN.fullmatch(logical_path)
        if not match:
            continue
        run_index = int(match.group(1))
        root = logical_path.removesuffix("/receipt.json")
        if run_index in roots:
            raise MaterializationError(f"运行序号重复：{run_index}")
        roots[run_index] = root
    if sorted(roots) != list(range(512)):
        raise MaterializationError("运行制品未覆盖固定 0000..0511")
    return roots


def _validate_top_contract(config: Mapping[str, Any], paths: Mapping[str, Path]) -> None:
    state = json.loads(paths["matrix_state"].read_text(encoding="utf-8"))
    summary = json.loads(paths["matrix_summary"].read_text(encoding="utf-8"))
    source_lock = json.loads(paths["ns3_source_lock"].read_text(encoding="utf-8"))
    contract = dict(config["source_contract"])
    for name in ("planned_run_count", "completed_run_count", "failed_run_count", "reused_run_count"):
        if int(state[name]) != int(contract[name]):
            raise MaterializationError(f"矩阵状态不符合冻结合同：{name}")
    if state.get("status") != "review_pending" or summary.get("status") != "review_pending":
        raise MaterializationError("attempt4 未保持 review_pending")
    if int(summary["valid_pair_count"]) != int(contract["valid_pair_count"]):
        raise MaterializationError("严格配对数量不符合冻结合同")
    for field_name in ("scenario_source_sha256", "tcp_truth_contract_sha256"):
        source_name = "contract_sha256" if field_name == "tcp_truth_contract_sha256" else field_name
        if source_lock[source_name] != contract[field_name]:
            raise MaterializationError(f"来源锁不符合冻结合同：{field_name}")
    if source_lock["manifest_sha256"] != config["inputs"]["ns3_manifest"]["sha256"]:
        raise MaterializationError("来源锁未绑定冻结 ns-3 清单")


def _input_paths(config: Mapping[str, Any], project_root: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, spec_value in dict(config["inputs"]).items():
        spec = dict(spec_value)
        relative = Path(str(spec["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            raise MaterializationError(f"输入路径非法：{relative}")
        path = project_root / relative
        paths[name] = path
        if name == "ns3_root":
            if not path.is_dir() or path.is_symlink():
                raise MaterializationError("attempt4 输入根不是普通目录")
        else:
            _validate_input(path, str(spec["sha256"]))
    return paths


def _mask_contract() -> dict[str, Any]:
    return {
        "schema_version": "flow_probe_r2_final_tcp_udp_mask_contract_v2",
        "review_status": "review_pending",
        "final_test_visible": False,
        "shared": {
            "applicable": "truth_shared_applicable",
            "observed": "truth_shared_observed",
        },
        "tcp": {
            "applicable": "truth_tcp_applicable",
            "sender_truth_available": "truth_tcp_sender_truth_available",
            "sender_level_masks": [
                "trace_connected",
                "cwnd_start_observed",
                "cwnd_end_observed",
                "ssthresh_start_observed",
                "ssthresh_end_observed",
                "bytes_in_flight_start_observed",
                "bytes_in_flight_end_observed",
                "acked_bytes_observed",
                "acked_segments_observed",
                "rtt_observed",
                "loss_event_count_observed",
                "timeout_event_count_observed",
            ],
            "aggregation_policy": "no_cross_sender_equation_aggregation",
        },
        "udp": {
            "applicable": "truth_udp_applicable",
            "observed": "truth_udp_observed",
            "backlog_applicable": "truth_udp_backlog_applicable",
            "backlog_policy": "null_when_application_has_no_internal_queue",
        },
    }


def materialize(config_path: Path, project_root: Path) -> Path:
    project_root = project_root.resolve()
    config_path = config_path.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise MaterializationError("v2 物化配置模式版本不正确")
    if config.get("status") != "review_pending" or config.get("final_test_visible") is not False:
        raise MaterializationError("v2 正式池必须保持 review_pending 且最终测试不可见")
    paths = _input_paths(config, project_root)
    _validate_top_contract(config, paths)

    publication = dict(config["publication"])
    included_splits = tuple(str(value) for value in publication["included_splits"])
    withheld_splits = tuple(str(value) for value in publication["withheld_splits"])
    manifest_rows = _load_jsonl(paths["ns3_manifest"])
    if len(manifest_rows) != int(config["source_contract"]["planned_run_count"]):
        raise MaterializationError("冻结 ns-3 清单不是 512 行")

    artifact_index = _artifact_index(paths["ns3_artifact_manifest"])
    run_roots = _run_roots(artifact_index)
    output_root = project_root / str(publication["output_root"])
    partial_root = output_root.with_name(f"{output_root.name}.partial")
    if output_root.exists() or partial_root.exists():
        raise MaterializationError("输出根或阶段根已存在，拒绝覆盖")
    partial_root.mkdir(parents=True)
    _write_json(
        partial_root / "_INCOMPLETE.json",
        {
            "schema_version": POOL_SCHEMA_VERSION,
            "status": "materializing",
            "review_status": "review_pending",
        },
    )

    window_sink = ParquetSink(partial_root / "physics-targets-ns3-v2.parquet", _window_schema())
    tcp_sink = ParquetSink(partial_root / "tcp-sender-truth-v2.parquet", _tcp_schema())
    udp_sink = ParquetSink(partial_root / "udp-window-truth-v2.parquet", _udp_schema())
    sequence_rows: list[dict[str, Any]] = []
    included_runs = 0
    withheld_runs = 0
    included_transports: Counter[str] = Counter()
    included_groups: dict[str, set[str]] = defaultdict(set)
    verified_receipts = 0
    verified_files = 0

    try:
        for run_order, manifest_row in enumerate(manifest_rows):
            split = str(manifest_row["split"])
            transport = str(manifest_row["transport_family"])
            group = str(manifest_row["physics_group_sha256"])
            run_root_relative = run_roots[run_order]
            expected_suffix = f"{run_order:04d}-{transport.lower()}-{group[:12]}"
            if not run_root_relative.endswith(expected_suffix):
                raise MaterializationError(f"运行目录身份错误：{run_root_relative}")
            run_root = paths["ns3_root"] / run_root_relative
            receipt_path = run_root / "receipt.json"
            main_path = run_root / "main.csv"
            tcp_path = run_root / "tcp-sender-windows.csv"
            receipt_logical = f"{run_root_relative}/receipt.json"
            main_logical = f"{run_root_relative}/main.csv"
            tcp_logical = f"{run_root_relative}/tcp-sender-windows.csv"
            for logical_path, actual_path in (
                (receipt_logical, receipt_path),
                (main_logical, main_path),
                (tcp_logical, tcp_path),
            ):
                if logical_path not in artifact_index:
                    raise MaterializationError(f"制品清单缺少：{logical_path}")
                _validate_input(actual_path, str(artifact_index[logical_path]["sha256"]))
                verified_files += 1
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt_sha = _sha256_file(receipt_path)
            main_sha = _sha256_file(main_path)
            tcp_sha = _sha256_file(tcp_path)
            expected_receipt = {
                "schema_version": RECEIPT_SCHEMA,
                "status": "pass",
                "coverage": f"{run_order:04d}-{transport.lower()}",
                "physics_group_sha256": group,
                "scenario_source_sha256": config["source_contract"]["scenario_source_sha256"],
                "contract_sha256": config["source_contract"]["tcp_truth_contract_sha256"],
                "main_csv_sha256": main_sha,
                "tcp_csv_sha256": tcp_sha,
            }
            if any(receipt.get(key) != value for key, value in expected_receipt.items()):
                raise MaterializationError(f"逐运行收据不符合冻结合同：{run_order:04d}")
            verified_receipts += 1

            if split in withheld_splits:
                withheld_runs += 1
                continue
            if split not in included_splits:
                raise MaterializationError(f"未知 ns-3 划分：{split}")
            included_runs += 1
            included_transports[transport] += 1
            included_groups[group].add(transport)

            main_rows = _load_csv(main_path, MAIN_SOURCE_COLUMNS)
            if len(main_rows) != 120:
                raise MaterializationError(f"主窗口数不是 120：{run_order:04d}")
            if [int(row["window_index"]) for row in main_rows] != list(range(120)):
                raise MaterializationError(f"主窗口顺序错误：{run_order:04d}")
            window_rows = [
                _window_row(
                    manifest_row,
                    source_row,
                    run_order=run_order,
                    main_sha256=main_sha,
                    receipt_sha256=receipt_sha,
                )
                for source_row in main_rows
            ]
            window_keys = [
                f"{row['sequence_id']}\0{row['window_index_in_sequence']:02d}"
                for row in window_rows
            ]
            window_sink.write(window_rows, window_keys)

            for sequence_index in range(30):
                sequence = _sequence_values(manifest_row, run_order, sequence_index * 4)
                sequence_rows.append(
                    {
                        "schema_version": POOL_SCHEMA_VERSION,
                        **sequence,
                        "run_stable_order": run_order,
                        "physics_group_sha256": group,
                        "split_id": split,
                        "transport_family": transport,
                        "route_id": transport,
                        "route_confidence": 1.0,
                        "stop_gradient_route": True,
                        "window_start_index": sequence_index * 4,
                        "window_stop_index": sequence_index * 4 + 4,
                        "window_count": 4,
                        "source_main_csv_sha256": main_sha,
                        "source_tcp_csv_sha256": tcp_sha,
                        "source_receipt_sha256": receipt_sha,
                        "review_status": "review_pending",
                        "final_test_visible": False,
                    }
                )

            if transport == "TCP":
                tcp_source_rows = _load_csv(tcp_path, TCP_SOURCE_COLUMNS)
                expected_tcp_rows = int(manifest_row["sender_count"]) * 120
                if len(tcp_source_rows) != expected_tcp_rows:
                    raise MaterializationError(f"TCP 发送者窗口数错误：{run_order:04d}")
                primary_keys = [
                    (int(row["window_index"]), int(row["sender_index"]))
                    for row in tcp_source_rows
                ]
                if primary_keys != sorted(primary_keys) or len(set(primary_keys)) != len(primary_keys):
                    raise MaterializationError(f"TCP 主键顺序或唯一性错误：{run_order:04d}")
                tcp_rows = [
                    _tcp_row(
                        manifest_row,
                        source_row,
                        run_order=run_order,
                        tcp_sha256=tcp_sha,
                        receipt_sha256=receipt_sha,
                    )
                    for source_row in tcp_source_rows
                ]
                tcp_keys = [
                    f"{row['sequence_id']}\0{row['window_index_in_sequence']:02d}\0{row['sender_index']:04d}"
                    for row in tcp_rows
                ]
                tcp_sink.write(tcp_rows, tcp_keys)
            else:
                udp_rows = [_udp_row(row) for row in window_rows]
                if any(
                    row["truth_udp_packet_balance_residual"] != 0
                    or row["truth_udp_byte_balance_residual"] != 0
                    for row in udp_rows
                ):
                    raise MaterializationError(f"UDP 应用发送守恒残差不为零：{run_order:04d}")
                udp_keys = [
                    f"{row['sequence_id']}\0{row['window_index_in_sequence']:02d}"
                    for row in udp_rows
                ]
                udp_sink.write(udp_rows, udp_keys)

        window_sink.close()
        tcp_sink.close()
        udp_sink.close()

        expected_counts = {
            "included_runs": int(publication["expected_included_runs"]),
            "withheld_runs": int(publication["expected_withheld_runs"]),
            "window_rows": int(publication["expected_window_rows"]),
            "sequence_rows": int(publication["expected_sequence_rows"]),
        }
        actual_counts = {
            "included_runs": included_runs,
            "withheld_runs": withheld_runs,
            "window_rows": window_sink.row_count,
            "sequence_rows": len(sequence_rows),
        }
        if actual_counts != expected_counts:
            raise MaterializationError(f"正式池数量不符合合同：{actual_counts}")
        if included_transports != Counter({"TCP": 192, "UDP": 192}):
            raise MaterializationError(f"正式池协议数量不对称：{included_transports}")
        if len(included_groups) != 192 or any(value != {"TCP", "UDP"} for value in included_groups.values()):
            raise MaterializationError("正式池未形成 192 个严格 TCP/UDP 开发配对")

        sequence_path = partial_root / "ns3-sequence-manifest-v2.jsonl"
        sequence_semantic = _write_jsonl(sequence_path, sequence_rows)
        sequence_ordering = _sha256_bytes(
            "".join(f"{row['sequence_id']}\n" for row in sequence_rows).encode("utf-8")
        )
        mask_path = partial_root / "mask-contract.json"
        mask_semantic = _write_json(mask_path, _mask_contract())
        contract_path = partial_root / "contract.json"
        contract_semantic = _write_json(contract_path, config)

        source_lock = {
            "schema_version": "flow_probe_r2_final_tcp_udp_physics_source_lock_v2",
            "dataset_version": config["dataset_version"],
            "stage": config["stage"],
            "status": "review_pending",
            "review_status": "review_pending",
            "final_test_visible": False,
            "config_sha256": _sha256_file(config_path),
            "input_identity": config["inputs"]["ns3_root"]["identity"],
            "input_root": config["inputs"]["ns3_root"]["path"],
            "input_hashes": {
                name: spec["sha256"]
                for name, spec in config["inputs"].items()
                if "sha256" in spec
            },
            "source_contract": config["source_contract"],
            "verified_receipts": verified_receipts,
            "verified_files": verified_files,
            "included_splits": list(included_splits),
            "withheld_splits": list(withheld_splits),
            "withheld_csv_rows_materialized": 0,
            "public_detection_final_test_read": False,
        }
        source_lock_path = partial_root / "source-lock.json"
        source_lock_semantic = _write_json(source_lock_path, source_lock)

        schemas = {
            "physics_targets_ns3_v2": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in window_sink.schema
            ],
            "tcp_sender_truth_v2": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in tcp_sink.schema
            ],
            "udp_window_truth_v2": [
                {"name": field.name, "type": str(field.type), "nullable": field.nullable}
                for field in udp_sink.schema
            ],
        }
        schema_document = {
            "schema_version": "flow_probe_r2_final_tcp_udp_physics_schema_v2",
            "review_status": "review_pending",
            "final_test_visible": False,
            **schemas,
            "ordering": {
                "physics_targets_ns3_v2": [
                    "run_stable_order",
                    "sequence_index",
                    "window_index_in_sequence",
                ],
                "tcp_sender_truth_v2": [
                    "run_stable_order",
                    "source_window_index",
                    "sender_index",
                ],
                "udp_window_truth_v2": [
                    "run_stable_order",
                    "source_window_index",
                ],
                "ns3_sequence_manifest_v2": ["sequence_stable_order"],
            },
        }
        schema_path = partial_root / "schema.json"
        schema_semantic = _write_json(schema_path, schema_document)

        summary = {
            "schema_version": "flow_probe_r2_final_tcp_udp_physics_summary_v2",
            "dataset_version": config["dataset_version"],
            "stage": config["stage"],
            "status": "review_pending",
            "review_status": "review_pending",
            "final_test_visible": False,
            **actual_counts,
            "verified_receipts": verified_receipts,
            "verified_files": verified_files,
            "included_transport_counts": dict(sorted(included_transports.items())),
            "included_pair_count": len(included_groups),
            "tcp_sender_truth_rows": tcp_sink.row_count,
            "udp_window_truth_rows": udp_sink.row_count,
            "schema_sha256": {
                "physics_targets_ns3_v2": _schema_sha256(window_sink.schema),
                "tcp_sender_truth_v2": _schema_sha256(tcp_sink.schema),
                "udp_window_truth_v2": _schema_sha256(udp_sink.schema),
            },
            "ordering_sha256": {
                "physics_targets_ns3_v2": window_sink.ordering_sha256,
                "tcp_sender_truth_v2": tcp_sink.ordering_sha256,
                "udp_window_truth_v2": udp_sink.ordering_sha256,
                "ns3_sequence_manifest_v2": sequence_ordering,
            },
            "semantic_sha256": {
                "physics_targets_ns3_v2": window_sink.semantic_sha256,
                "tcp_sender_truth_v2": tcp_sink.semantic_sha256,
                "udp_window_truth_v2": udp_sink.semantic_sha256,
                "ns3_sequence_manifest_v2": sequence_semantic,
            },
            "public_detection_final_test_read": False,
        }
        summary_path = partial_root / "input-summary.json"
        summary_semantic = _write_json(summary_path, summary)
        state_path = partial_root / "run-state.json"
        state_semantic = _write_json(
            state_path,
            {
                "schema_version": "flow_probe_r2_final_tcp_udp_physics_state_v2",
                "status": "review_pending",
                "review_status": "review_pending",
                "materialization_completed": True,
                "atomic_publication_ready": True,
                "atomic_publication_method": "same_filesystem_rename_no_overwrite",
                "final_test_visible": False,
            },
        )

        artifacts = [
            _artifact_entry(
                window_sink.path,
                partial_root,
                row_count=window_sink.row_count,
                schema_sha256=_schema_sha256(window_sink.schema),
                semantic_sha256=window_sink.semantic_sha256,
            ),
            _artifact_entry(
                tcp_sink.path,
                partial_root,
                row_count=tcp_sink.row_count,
                schema_sha256=_schema_sha256(tcp_sink.schema),
                semantic_sha256=tcp_sink.semantic_sha256,
            ),
            _artifact_entry(
                udp_sink.path,
                partial_root,
                row_count=udp_sink.row_count,
                schema_sha256=_schema_sha256(udp_sink.schema),
                semantic_sha256=udp_sink.semantic_sha256,
            ),
            _artifact_entry(
                sequence_path,
                partial_root,
                row_count=len(sequence_rows),
                schema_sha256=None,
                semantic_sha256=sequence_semantic,
            ),
        ]
        for path, semantic in (
            (mask_path, mask_semantic),
            (contract_path, contract_semantic),
            (source_lock_path, source_lock_semantic),
            (schema_path, schema_semantic),
            (summary_path, summary_semantic),
            (state_path, state_semantic),
        ):
            artifacts.append(
                _artifact_entry(
                    path,
                    partial_root,
                    row_count=None,
                    schema_sha256=None,
                    semantic_sha256=semantic,
                )
            )
        artifacts.sort(key=lambda item: str(item["relative_path"]))
        artifact_manifest = {
            "schema_version": "flow_probe_r2_final_tcp_udp_physics_artifact_manifest_v2",
            "dataset_version": config["dataset_version"],
            "stage": config["stage"],
            "status": "review_pending",
            "review_status": "review_pending",
            "final_test_visible": False,
            "atomic_publication": "same_filesystem_rename_no_overwrite",
            "artifacts": artifacts,
            "artifact_payload_merkle_sha256": _sha256_bytes(
                _canonical_json(artifacts).encode("utf-8")
            ),
        }
        _write_json(partial_root / "artifact-manifest.json", artifact_manifest)
        (partial_root / "_INCOMPLETE.json").unlink()
        os.rename(partial_root, output_root)
        return output_root
    except BaseException:
        for sink in (window_sink, tcp_sink, udp_sink):
            try:
                sink.close()
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
