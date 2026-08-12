"""运行 R2 ns-3 TCP 物理真值 v2 最小字段闭合矩阵。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shlex
import subprocess
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from flow_probe.r2_ns3_protocol_matrix import MANIFEST_FIELD_ORDER, ProtocolRunConfig

PROGRAM_NAME: Final = "scratch/flow-probe-r2-dynamics-v2"
COMPILED_SOURCE: Final = "scratch/flow-probe-r2-dynamics-v2.cc"
TCP_PARAMS_SCHEMA: Final = "flow_probe_r2_ns3_tcp_truth_v2_params_v3"
UDP_PARAMS_SCHEMA: Final = "flow_probe_r2_ns3_udp_truth_v2_params_v3"
EXPECTED_MANIFEST_SHA256: Final = (
    "d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111"
)
MAIN_SCHEMA: Final = "flow_probe_r2_ns3_protocol_windows_v3"
TCP_SCHEMA: Final = "flow_probe_r2_ns3_tcp_sender_windows_v2"
RECEIPT_SCHEMA: Final = "flow_probe_r2_ns3_protocol_dynamics_v2_run_receipt_v2"
DIRECTIONAL_SEMANTICS_VERSION: Final = "flow_probe_e2_zeek_directional_windows_v1"
TCP_FIELD_CLOSURE_SCHEMA: Final = "flow_probe_r2_ns3_tcp_truth_v2_field_closure_v1"
UDP_SINGLE_FIELD_CLOSURE_SCHEMA: Final = (
    "flow_probe_r2_ns3_udp_truth_v2_field_closure_v1"
)
REGISTERED_PARAMS_CLOSURE_SCHEMAS: Final = {
    TCP_PARAMS_SCHEMA: TCP_FIELD_CLOSURE_SCHEMA,
    UDP_PARAMS_SCHEMA: UDP_SINGLE_FIELD_CLOSURE_SCHEMA,
}
DIRECTIONAL_COLUMNS: Final = (
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "resp_pkts",
    "orig_ip_bytes",
    "resp_ip_bytes",
)
MAIN_COLUMNS: Final = (
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
    *DIRECTIONAL_COLUMNS,
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
MAIN_HEADER_SHA256: Final = hashlib.sha256(
    (",".join(MAIN_COLUMNS) + "\n").encode("utf-8")
).hexdigest()
TCP_COLUMNS: Final = (
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


class TcpTruthV2Error(RuntimeError):
    """字段闭合输入、运行或制品违反冻结合同。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial")
    if temporary.exists() or temporary.is_symlink():
        raise TcpTruthV2Error(f"原子写临时文件已存在：{temporary}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _read_json(path: Path, name: str) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise TcpTruthV2Error(f"{name} 不存在、不是普通文件或是符号链接：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TcpTruthV2Error(f"{name} 无法解析：{error}") from error
    if not isinstance(value, Mapping):
        raise TcpTruthV2Error(f"{name} 必须是 JSON 对象")
    return value


def _resolve_under(root: Path, value: object, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise TcpTruthV2Error(f"{name} 必须是非空路径字符串")
    candidate = Path(value).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise TcpTruthV2Error(f"{name} 必须位于项目根内") from error
    return resolved


def _require_sha(value: object, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise TcpTruthV2Error(f"{name} 必须是小写 SHA-256")
    return value


def _load_manifest(path: Path) -> tuple[ProtocolRunConfig, ...]:
    if _file_sha256(path) != EXPECTED_MANIFEST_SHA256:
        raise TcpTruthV2Error("冻结清单 SHA-256 不一致")
    runs: list[ProtocolRunConfig] = []
    with path.open("r", encoding="ascii") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.endswith("\n") or not line.strip():
                raise TcpTruthV2Error(f"清单第{line_number}行不是规范 JSONL")
            value = json.loads(line)
            if not isinstance(value, dict) or tuple(value) != MANIFEST_FIELD_ORDER:
                raise TcpTruthV2Error(f"清单第{line_number}行字段顺序不符")
            run = ProtocolRunConfig(**value)
            runs.append(run)
    if len(runs) != 512:
        raise TcpTruthV2Error("冻结清单未恰含512个运行")
    if Counter(run.transport_family for run in runs) != Counter(
        {"TCP": 256, "UDP": 256}
    ):
        raise TcpTruthV2Error("冻结清单未恰含256个 TCP 和256个 UDP 运行")
    groups: dict[str, list[ProtocolRunConfig]] = defaultdict(list)
    for run in runs:
        groups[run.physics_group_sha256].append(run)
    if len(groups) != 256:
        raise TcpTruthV2Error("冻结清单未形成256个物理配对组")
    for group, pair in groups.items():
        if len(pair) != 2 or {run.transport_family for run in pair} != {"TCP", "UDP"}:
            raise TcpTruthV2Error(f"冻结物理组 {group} 未恰含 TCP/UDP 两侧")
        if pair[0].to_base_record() != pair[1].to_base_record():
            raise TcpTruthV2Error(f"冻结物理组 {group} 除协议外存在配置差异")
    return tuple(runs)


def _load_selection(
    closure: Mapping[str, object], manifest: Sequence[ProtocolRunConfig]
) -> list[tuple[str, ProtocolRunConfig]]:
    schema = closure.get("schema_version")
    if schema not in {TCP_FIELD_CLOSURE_SCHEMA, UDP_SINGLE_FIELD_CLOSURE_SCHEMA}:
        raise TcpTruthV2Error("字段闭合配置模式版本不符")
    if closure.get("expected_manifest_sha256") != EXPECTED_MANIFEST_SHA256:
        raise TcpTruthV2Error("字段闭合配置未绑定冻结清单")
    values = closure.get("selected_runs")
    if schema == UDP_SINGLE_FIELD_CLOSURE_SCHEMA:
        expected_keys = {
            "schema_version",
            "expected_manifest_sha256",
            "manifest_path",
            "selection_policy",
            "selected_runs",
        }
        if set(closure) != expected_keys:
            raise TcpTruthV2Error("UDP单项闭合配置键集合不符")
        if closure.get("selection_policy") != "frozen_manifest_exact_udp_row":
            raise TcpTruthV2Error("UDP单项闭合未使用冻结清单精确行策略")
        if not isinstance(values, list) or len(values) != 1:
            raise TcpTruthV2Error("UDP单项闭合必须恰选1个运行")
        item = values[0]
        if not isinstance(item, Mapping) or set(item) != {
            "coverage",
            "manifest_index",
            "physics_group_sha256",
            "transport_family",
        }:
            raise TcpTruthV2Error("UDP单项选择项键集合不符")
        coverage = item["coverage"]
        index = item["manifest_index"]
        group = item["physics_group_sha256"]
        if (
            not isinstance(coverage, str)
            or not coverage
            or isinstance(index, bool)
            or not isinstance(index, int)
            or not isinstance(group, str)
            or item["transport_family"] != "UDP"
        ):
            raise TcpTruthV2Error("UDP单项选择字段类型或协议身份不符")
        if index < 0 or index >= len(manifest):
            raise TcpTruthV2Error("UDP单项选择的冻结清单行号越界")
        run = manifest[index]
        if run.transport_family != "UDP" or run.physics_group_sha256 != group:
            raise TcpTruthV2Error("UDP单项选择未精确绑定冻结清单行")
        return [(coverage, run)]

    if not isinstance(values, list) or len(values) != 5:
        raise TcpTruthV2Error("字段闭合必须恰选5个 TCP 运行")
    tcp_manifest = {
        run.physics_group_sha256: run
        for run in manifest
        if run.transport_family == "TCP"
    }
    if len(tcp_manifest) != 256:
        raise TcpTruthV2Error("冻结清单未形成256个唯一 TCP 运行")
    result: list[tuple[str, ProtocolRunConfig]] = []
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, Mapping) or set(item) != {"coverage", "physics_group_sha256"}:
            raise TcpTruthV2Error("字段闭合选择项键集合不符")
        coverage = item["coverage"]
        group = item["physics_group_sha256"]
        if not isinstance(coverage, str) or not isinstance(group, str):
            raise TcpTruthV2Error("字段闭合覆盖名和物理组必须是字符串")
        if group in seen or group not in tcp_manifest:
            raise TcpTruthV2Error("字段闭合物理组重复或不在冻结清单")
        seen.add(group)
        result.append((coverage, tcp_manifest[group]))
    compositions = {(run.benign_sender_count, run.attack_sender_count) for _, run in result}
    if compositions != {(8, 0), (4, 4)}:
        raise TcpTruthV2Error("字段闭合未覆盖8+0和4+4两种发送者组成")
    if {run.sender_count for _, run in result} != {8}:
        raise TcpTruthV2Error("冻结清单的发送者总数限制发生变化")
    return result


def _validate_params_closure_schema(
    params_schema: object, closure_schema: object
) -> None:
    expected_closure = REGISTERED_PARAMS_CLOSURE_SCHEMAS.get(params_schema)
    if expected_closure is None:
        raise TcpTruthV2Error("受控参数模式未注册")
    if closure_schema != expected_closure:
        raise TcpTruthV2Error("参数模式与字段闭合模式协议不一致")


def _load_reused_receipts(
    resume_root: Path,
    selected: list[tuple[str, ProtocolRunConfig]],
    contract_sha: str,
) -> dict[str, Mapping[str, object]]:
    if not resume_root.is_dir() or resume_root.is_symlink():
        raise TcpTruthV2Error("续跑来源不存在、不是目录或是符号链接")
    state = _read_json(resume_root / "run-state.json", "续跑来源状态")
    completed_count = state.get("completed_run_count")
    if state.get("status") not in {"failed", "finished"} or not isinstance(
        completed_count, int
    ):
        raise TcpTruthV2Error("续跑来源状态不允许复用")
    reused: dict[str, Mapping[str, object]] = {}
    for coverage, run in selected:
        run_dir = resume_root / "runs" / f"{coverage}-{run.physics_group_sha256[:12]}"
        receipt_path = run_dir / "receipt.json"
        if not receipt_path.exists():
            continue
        if not run_dir.is_dir() or run_dir.is_symlink():
            raise TcpTruthV2Error("续跑来源的已完成运行目录不安全")
        receipt = _read_json(receipt_path, "续跑来源收据")
        if (
            receipt.get("schema_version") != RECEIPT_SCHEMA
            or receipt.get("status") != "pass"
            or receipt.get("coverage") != coverage
            or receipt.get("physics_group_sha256") != run.physics_group_sha256
            or receipt.get("contract_sha256") != contract_sha
            or receipt.get("main_schema_version") != MAIN_SCHEMA
            or receipt.get("directional_semantics_version")
            != DIRECTIONAL_SEMANTICS_VERSION
            or receipt.get("directional_fields") != list(DIRECTIONAL_COLUMNS)
            or receipt.get("main_header_sha256") != MAIN_HEADER_SHA256
            or not isinstance(receipt.get("metrics"), Mapping)
        ):
            raise TcpTruthV2Error("续跑来源收据与当前闭合选择不一致")
        _require_sha(receipt.get("scenario_source_sha256"), "续跑场景哈希")
        for filename, hash_key in (
            ("main.csv", "main_csv_sha256"),
            ("tcp-sender-windows.csv", "tcp_csv_sha256"),
        ):
            artifact = run_dir / filename
            expected = _require_sha(receipt.get(hash_key), f"续跑{filename}哈希")
            if not artifact.is_file() or artifact.is_symlink() or _file_sha256(artifact) != expected:
                raise TcpTruthV2Error(f"续跑来源制品不完整或哈希不一致：{filename}")
        reused[run.physics_group_sha256] = receipt
    if len(reused) != completed_count or not reused:
        raise TcpTruthV2Error("续跑来源的完成计数与可复用收据不一致")
    return reused


def _parse_int(row: Mapping[str, str], column: str, *, allow_empty: bool = False) -> int | None:
    raw = row.get(column)
    if allow_empty and raw == "":
        return None
    if raw is None or re.fullmatch(r"-?(?:0|[1-9][0-9]*)", raw) is None:
        raise TcpTruthV2Error(f"字段 {column} 不是规范整数")
    return int(raw)


def _parse_float(
    row: Mapping[str, str], column: str, *, allow_empty: bool = False
) -> float | None:
    raw = row.get(column)
    if allow_empty and raw == "":
        return None
    try:
        value = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise TcpTruthV2Error(f"字段 {column} 不是规范数值") from error
    if not math.isfinite(value):
        raise TcpTruthV2Error(f"字段 {column} 包含非有限值")
    return value


def _validate_optional(
    row: Mapping[str, str], mask_column: str, value_columns: Sequence[str]
) -> None:
    mask = _parse_int(row, mask_column)
    if mask not in (0, 1):
        raise TcpTruthV2Error(f"观测掩码 {mask_column} 必须为0或1")
    for column in value_columns:
        if mask == 0 and row[column] != "":
            raise TcpTruthV2Error(f"未观测字段 {column} 携带了伪值")
        if mask == 1 and row[column] == "":
            raise TcpTruthV2Error(f"已观测字段 {column} 缺值")


def _validate_directional_row(
    row: Mapping[str, str], transport_family: str
) -> dict[str, int]:
    directional = {
        column: int(_parse_int(row, column)) for column in DIRECTIONAL_COLUMNS
    }
    if min(directional.values()) < 0:
        raise TcpTruthV2Error("主窗口方向字段不得为负")
    for prefix in ("orig", "resp"):
        payload = directional[f"{prefix}_bytes"]
        packets = directional[f"{prefix}_pkts"]
        ip_bytes = directional[f"{prefix}_ip_bytes"]
        if ip_bytes < payload:
            raise TcpTruthV2Error("方向IP字节不得小于传输层有效载荷字节")
        if packets == 0 and (payload != 0 or ip_bytes != 0):
            raise TcpTruthV2Error("零包方向不得携带字节计数")
        if packets > 0 and ip_bytes == 0:
            raise TcpTruthV2Error("非零包方向必须携带IP字节")
    if transport_family == "UDP" and any(
        directional[column] != 0
        for column in ("resp_bytes", "resp_pkts", "resp_ip_bytes")
    ):
        raise TcpTruthV2Error("当前单向UDP场景不得伪造响应方向流量")
    return directional


def _validate_main(
    path: Path, run: ProtocolRunConfig, contract_sha: str
) -> dict[str, float | int]:
    rows = 0
    totals: Counter[str] = Counter()
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != MAIN_COLUMNS:
            raise TcpTruthV2Error("主窗口 CSV 字段名称或顺序不符")
        for expected_index, row in enumerate(reader):
            rows += 1
            if row["schema_version"] != MAIN_SCHEMA:
                raise TcpTruthV2Error("主窗口 CSV 模式版本不符")
            if row["physics_group_sha256"] != run.physics_group_sha256:
                raise TcpTruthV2Error("主窗口物理组身份不符")
            if row["matrix_config_sha256"] != run.matrix_config_sha256:
                raise TcpTruthV2Error("主窗口矩阵配置身份不符")
            if row["tcp_truth_contract_sha256"] != contract_sha:
                raise TcpTruthV2Error("主窗口未绑定 TCP 真值合同")
            if (
                row["split"] != run.split
                or _parse_int(row, "run_seed") != run.run_seed
                or row["transport_family"] != run.transport_family
            ):
                raise TcpTruthV2Error("主窗口划分、种子或协议身份不符")
            if _parse_int(row, "window_index") != expected_index:
                raise TcpTruthV2Error("主窗口序号不连续")
            start = _parse_float(row, "window_start_s")
            end = _parse_float(row, "window_end_s")
            if not math.isclose(float(start), expected_index * 0.1, abs_tol=1e-8):
                raise TcpTruthV2Error("主窗口起点不连续")
            if not math.isclose(float(end), (expected_index + 1) * 0.1, abs_tol=1e-8):
                raise TcpTruthV2Error("主窗口终点不连续")
            if not math.isclose(float(_parse_float(row, "window_duration_s")), 0.1):
                raise TcpTruthV2Error("主窗口时长不符")
            directional = _validate_directional_row(row, run.transport_family)
            for column, value in directional.items():
                totals[column] += value
            if _parse_int(row, "truth_queue_balance_residual_l3_bytes") != 0:
                raise TcpTruthV2Error("主窗口字节守恒残差非零")
            if _parse_int(row, "truth_queue_balance_residual_packets") != 0:
                raise TcpTruthV2Error("主窗口包守恒残差非零")
            if run.transport_family == "TCP":
                if _parse_int(row, "truth_udp_applicable") != 0:
                    raise TcpTruthV2Error("TCP主窗口不得携带UDP适用状态")
                for column in (
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
                ):
                    if row[column] != "":
                        raise TcpTruthV2Error("TCP主窗口携带了伪UDP真值")
            else:
                if _parse_int(row, "truth_udp_applicable") != 1:
                    raise TcpTruthV2Error("UDP主窗口未标记适用")
                active_duration = float(
                    _parse_float(row, "truth_udp_burst_active_duration_s")
                )
                if not 0.0 <= active_duration <= 0.1 + 1e-12:
                    raise TcpTruthV2Error("UDP突发活跃时长越界")
                if run.arrival_model == "constant" and not math.isclose(
                    active_duration, 0.1, abs_tol=1e-9
                ):
                    raise TcpTruthV2Error("UDP常量到达窗口的活跃时长不等于窗口时长")
                planned_packets = int(
                    _parse_int(row, "truth_udp_planned_app_payload_packets")
                )
                planned_bytes = int(
                    _parse_int(row, "truth_udp_planned_app_payload_bytes")
                )
                actual_packets = int(
                    _parse_int(row, "truth_udp_actual_send_packets")
                )
                actual_bytes = int(_parse_int(row, "truth_udp_actual_send_bytes"))
                drop_packets = int(_parse_int(row, "truth_udp_app_drop_packets"))
                drop_bytes = int(_parse_int(row, "truth_udp_app_drop_bytes"))
                if min(
                    planned_packets,
                    planned_bytes,
                    actual_packets,
                    actual_bytes,
                    drop_packets,
                    drop_bytes,
                ) < 0:
                    raise TcpTruthV2Error("UDP应用观测不得为负")
                if planned_bytes != planned_packets * run.packet_size_bytes:
                    raise TcpTruthV2Error("UDP计划包数与计划应用载荷字节不一致")
                if actual_packets > planned_packets or drop_packets > planned_packets:
                    raise TcpTruthV2Error("UDP实际发送或应用丢包数超过计划包数")
                if actual_bytes + drop_bytes != planned_bytes:
                    raise TcpTruthV2Error("UDP实际发送与应用丢弃字节不守恒")
                if _parse_int(row, "truth_udp_backlog_applicable") != 0:
                    raise TcpTruthV2Error("无应用内部队列时不得伪造UDP积压适用性")
                if (
                    row["truth_udp_backlog_start_bytes"] != ""
                    or row["truth_udp_backlog_end_bytes"] != ""
                ):
                    raise TcpTruthV2Error("无应用内部队列时不得填充UDP积压值")
                totals["udp_planned_packets"] += planned_packets
                totals["udp_planned_bytes"] += planned_bytes
                totals["udp_actual_packets"] += actual_packets
                totals["udp_actual_bytes"] += actual_bytes
                totals["udp_app_drop_packets"] += drop_packets
                totals["udp_app_drop_bytes"] += drop_bytes
            if _parse_int(row, "truth_qdisc_received_l3_bytes") != (
                _parse_int(row, "truth_qdisc_enqueued_l3_bytes")
                + _parse_int(row, "truth_qdisc_drop_before_enqueue_l3_bytes")
            ):
                raise TcpTruthV2Error("主窗口队列收到字节不闭合")
            if directional["orig_pkts"] != _parse_int(
                row, "truth_qdisc_received_packets"
            ) or directional["orig_ip_bytes"] != _parse_int(
                row, "truth_qdisc_received_l3_bytes"
            ):
                raise TcpTruthV2Error("发起方向IPv4观测与瓶颈队列入口不一致")
    if rows != 120:
        raise TcpTruthV2Error(f"主窗口必须恰有120行，实际为{rows}")
    return {"main_window_count": rows, **totals}


def _validate_udp_sidecar(path: Path) -> dict[str, int]:
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != TCP_COLUMNS:
            raise TcpTruthV2Error("UDP运行的TCP伴随CSV字段名称或顺序不符")
        if next(reader, None) is not None:
            raise TcpTruthV2Error("UDP运行不得携带TCP发送者真值行")
    return {"tcp_window_count": 0}


def _validate_tcp(path: Path, run: ProtocolRunConfig, contract_sha: str) -> dict[str, float | int]:
    rows_by_sender: dict[int, list[Mapping[str, str]]] = defaultdict(list)
    totals: Counter[str] = Counter()
    ack_residual_max = 0.0
    loss_residual_max = 0.0
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != TCP_COLUMNS:
            raise TcpTruthV2Error("TCP 伴随 CSV 字段名称或顺序不符")
        seen_keys: set[tuple[str, int, int]] = set()
        for row in reader:
            if row["schema_version"] != TCP_SCHEMA or row["transport_family"] != "TCP":
                raise TcpTruthV2Error("TCP 伴随 CSV 模式或协议身份不符")
            if row["physics_group_sha256"] != run.physics_group_sha256:
                raise TcpTruthV2Error("TCP 伴随 CSV 物理组身份不符")
            if row["tcp_truth_contract_sha256"] != contract_sha:
                raise TcpTruthV2Error("TCP 伴随 CSV 未绑定真值合同")
            window = _parse_int(row, "window_index")
            sender = _parse_int(row, "sender_index")
            assert window is not None and sender is not None
            key = (run.physics_group_sha256, window, sender)
            if key in seen_keys:
                raise TcpTruthV2Error("TCP 伴随 CSV 主键重复")
            seen_keys.add(key)
            if sender < 0 or sender >= run.sender_count:
                raise TcpTruthV2Error("TCP 发送者索引越界")
            if _parse_int(row, "trace_connected") != 1:
                raise TcpTruthV2Error("TCP 发送者跟踪源未完整连接")
            if _parse_int(row, "segment_size_bytes") is None or int(row["segment_size_bytes"]) <= 0:
                raise TcpTruthV2Error("TCP MSS 不合法")
            for mask, values in (
                ("cwnd_start_observed", ("cwnd_start_bytes",)),
                ("cwnd_end_observed", ("cwnd_end_bytes",)),
                ("ssthresh_start_observed", ("ssthresh_start_bytes",)),
                ("ssthresh_end_observed", ("ssthresh_end_bytes",)),
                ("bytes_in_flight_start_observed", ("bytes_in_flight_start_bytes",)),
                ("bytes_in_flight_end_observed", ("bytes_in_flight_end_bytes",)),
                ("acked_bytes_observed", ("acked_bytes",)),
                ("acked_segments_observed", ("acked_segments",)),
                ("rtt_observed", ("rtt_mean_ms", "rtt_min_ms", "rtt_max_ms")),
            ):
                _validate_optional(row, mask, values)
            if row["acked_bytes_observed"] != row["acked_segments_observed"]:
                raise TcpTruthV2Error("ACK 字节和段数观测掩码不一致")
            rtt_samples = _parse_int(row, "rtt_sample_count")
            if (rtt_samples > 0) != (row["rtt_observed"] == "1"):
                raise TcpTruthV2Error("RTT 样本数与观测掩码不一致")
            if rtt_samples > 0:
                rtt_min = _parse_float(row, "rtt_min_ms")
                rtt_mean = _parse_float(row, "rtt_mean_ms")
                rtt_max = _parse_float(row, "rtt_max_ms")
                if not 0 < float(rtt_min) <= float(rtt_mean) <= float(rtt_max):
                    raise TcpTruthV2Error("RTT 最小值、均值和最大值不合法")
            for column in (
                "acked_bytes",
                "acked_segments",
                "loss_event_count",
                "timeout_event_count",
                "cwnd_contraction_event_count",
                "ssthresh_contraction_event_count",
                "ack_residual_valid_terms",
                "loss_residual_valid_terms",
            ):
                value = _parse_int(row, column, allow_empty=True)
                if value is not None:
                    if value < 0:
                        raise TcpTruthV2Error(f"字段 {column} 不得为负")
                    totals[column] += value
            totals["rtt_sample_count"] += rtt_samples
            for prefix in ("ack", "loss"):
                terms = int(row[f"{prefix}_residual_valid_terms"])
                squared = float(row[f"{prefix}_residual_squared_sum_bytes2"])
                normalized = float(row[f"{prefix}_residual_normalized_squared_sum"])
                mse_raw = row[f"{prefix}_residual_mse_bytes2"]
                normalized_mse_raw = row[f"{prefix}_residual_normalized_mse"]
                if terms == 0:
                    if mse_raw != "" or normalized_mse_raw != "":
                        raise TcpTruthV2Error("零残差项携带了伪均方误差")
                else:
                    if not math.isclose(float(mse_raw), squared / terms, abs_tol=1e-12):
                        raise TcpTruthV2Error("残差均方误差口径不符")
                    if not math.isclose(
                        float(normalized_mse_raw), normalized / terms, abs_tol=1e-12
                    ):
                        raise TcpTruthV2Error("归一化残差均方误差口径不符")
                    if prefix == "ack":
                        ack_residual_max = max(ack_residual_max, float(normalized_mse_raw))
                    else:
                        loss_residual_max = max(loss_residual_max, float(normalized_mse_raw))
            rows_by_sender[sender].append(row)

    if set(rows_by_sender) != set(range(run.sender_count)):
        raise TcpTruthV2Error("TCP 伴随 CSV 未覆盖全部发送者")
    for sender, rows in rows_by_sender.items():
        if len(rows) != 120:
            raise TcpTruthV2Error(f"发送者{sender}不是120个窗口")
        rows.sort(key=lambda row: int(row["window_index"]))
        for expected_index, row in enumerate(rows):
            if int(row["window_index"]) != expected_index:
                raise TcpTruthV2Error("TCP 窗口序号不连续")
            if expected_index == 0:
                continue
            previous = rows[expected_index - 1]
            for prefix in ("cwnd", "ssthresh", "bytes_in_flight"):
                if row[f"{prefix}_start_observed"] != previous[f"{prefix}_end_observed"]:
                    raise TcpTruthV2Error("TCP 状态窗口掩码不连续")
                if row[f"{prefix}_start_bytes"] != previous[f"{prefix}_end_bytes"]:
                    raise TcpTruthV2Error("TCP 状态窗口起点不等于上一终点")
            if row["cong_state_start"] != previous["cong_state_end"]:
                raise TcpTruthV2Error("拥塞状态窗口不连续")
    if ack_residual_max > 1e-18 or loss_residual_max > 1e-18:
        raise TcpTruthV2Error("事件级固定 NewReno 残差非零")
    return {
        "tcp_window_count": sum(len(rows) for rows in rows_by_sender.values()),
        "acked_bytes": totals["acked_bytes"],
        "acked_segments": totals["acked_segments"],
        "rtt_sample_count": totals["rtt_sample_count"],
        "loss_event_count": totals["loss_event_count"],
        "timeout_event_count": totals["timeout_event_count"],
        "contraction_event_count": totals["cwnd_contraction_event_count"]
        + totals["ssthresh_contraction_event_count"],
        "ack_residual_valid_terms": totals["ack_residual_valid_terms"],
        "loss_residual_valid_terms": totals["loss_residual_valid_terms"],
        "ack_residual_normalized_mse_max": ack_residual_max,
        "loss_residual_normalized_mse_max": loss_residual_max,
    }


def _program_arguments(
    run: ProtocolRunConfig, contract_sha: str, main_path: Path, tcp_path: Path
) -> tuple[str, ...]:
    values: tuple[tuple[str, object], ...] = (
        ("physicsGroupSha256", run.physics_group_sha256),
        ("matrixConfigSha256", run.matrix_config_sha256),
        ("tcpTruthContractSha256", contract_sha),
        ("split", run.split),
        ("runSeed", run.run_seed),
        ("transportFamily", run.transport_family),
        ("duration", run.duration_seconds),
        ("window", run.window_seconds),
        ("trafficMode", run.traffic_mode),
        ("binaryLabel", run.binary_label),
        ("arrivalModel", run.arrival_model),
        ("queueModel", run.queue_model),
        ("offeredLoadRatio", run.offered_load_ratio),
        ("initialCapacityMbps", run.initial_capacity_mbps),
        ("shiftedCapacityMbps", run.shifted_capacity_mbps),
        ("capacityChangeSeconds", run.capacity_change_time_seconds),
        ("accessDelayMs", run.access_delay_ms),
        ("bottleneckDelayMs", run.bottleneck_delay_ms),
        ("queueLimitPackets", run.queue_limit_packets),
        ("downstreamLossRate", run.downstream_loss_rate),
        ("senderCount", run.sender_count),
        ("benignSenderCount", run.benign_sender_count),
        ("attackSenderCount", run.attack_sender_count),
        ("totalOfferedLoadMbps", run.total_offered_load_mbps),
        ("packetSizeBytes", run.packet_size_bytes),
        ("burstOnSeconds", run.burst_on_seconds),
        ("burstOffSeconds", run.burst_off_seconds),
        ("output", main_path),
        ("tcpOutput", tcp_path),
    )
    return (PROGRAM_NAME, *(f"--{name}={value}" for name, value in values))


def _run_one(
    ns3_root: Path,
    runs_root: Path,
    coverage: str,
    run: ProtocolRunConfig,
    contract_sha: str,
    source_sha: str,
    executable: Path | None = None,
) -> dict[str, object]:
    final_dir = runs_root / f"{coverage}-{run.physics_group_sha256[:12]}"
    partial_dir = runs_root / f".{final_dir.name}.partial"
    if final_dir.exists() or partial_dir.exists() or final_dir.is_symlink() or partial_dir.is_symlink():
        raise TcpTruthV2Error(f"运行目录已存在，禁止覆盖：{final_dir}")
    partial_dir.mkdir()
    config_snapshot = {"coverage": coverage, "run": run.to_record()}
    (partial_dir / "config.json").write_bytes(_canonical_json_bytes(config_snapshot))
    main_partial = partial_dir / "main.csv.partial"
    tcp_partial = partial_dir / "tcp-sender-windows.csv.partial"
    arguments = _program_arguments(run, contract_sha, main_partial, tcp_partial)
    if executable is None:
        command = (
            "env",
            "USER=ns3builder",
            str(ns3_root / "ns3"),
            "run",
            " ".join(shlex.quote(argument) for argument in arguments),
        )
    else:
        normalized_executable = executable.resolve()
        try:
            normalized_executable.relative_to(ns3_root.resolve())
        except ValueError as error:
            raise TcpTruthV2Error("直接执行文件必须位于固定ns-3根内") from error
        if not normalized_executable.is_file() or not os.access(normalized_executable, os.X_OK):
            raise TcpTruthV2Error("直接执行文件不存在、不是普通文件或不可执行")
        command = (str(normalized_executable), *arguments[1:])
    completed = subprocess.run(
        command,
        cwd=ns3_root,
        capture_output=True,
        text=True,
        check=False,
    )
    (partial_dir / "stdout.log").write_text(completed.stdout or "", encoding="utf-8")
    (partial_dir / "stderr.log").write_text(completed.stderr or "", encoding="utf-8")
    if completed.returncode != 0:
        _write_json_atomic(
            partial_dir / "receipt.json",
            {
                "schema_version": RECEIPT_SCHEMA,
                "status": "failed",
                "returncode": completed.returncode,
                "coverage": coverage,
                "physics_group_sha256": run.physics_group_sha256,
                "main_schema_version": MAIN_SCHEMA,
                "directional_semantics_version": DIRECTIONAL_SEMANTICS_VERSION,
                "recorded_at": _utc_now(),
            },
        )
        raise TcpTruthV2Error(f"ns-3 v2运行退出状态为{completed.returncode}")
    main_metrics = _validate_main(main_partial, run, contract_sha)
    tcp_metrics = (
        _validate_tcp(tcp_partial, run, contract_sha)
        if run.transport_family == "TCP"
        else _validate_udp_sidecar(tcp_partial)
    )
    main_path = partial_dir / "main.csv"
    tcp_path = partial_dir / "tcp-sender-windows.csv"
    main_partial.rename(main_path)
    tcp_partial.rename(tcp_path)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "pass",
        "coverage": coverage,
        "physics_group_sha256": run.physics_group_sha256,
        "scenario_source_sha256": source_sha,
        "contract_sha256": contract_sha,
        "main_schema_version": MAIN_SCHEMA,
        "directional_semantics_version": DIRECTIONAL_SEMANTICS_VERSION,
        "directional_fields": list(DIRECTIONAL_COLUMNS),
        "main_header_sha256": MAIN_HEADER_SHA256,
        "main_csv_sha256": _file_sha256(main_path),
        "tcp_csv_sha256": _file_sha256(tcp_path),
        "metrics": {**main_metrics, **tcp_metrics},
        "recorded_at": _utc_now(),
    }
    _write_json_atomic(partial_dir / "receipt.json", receipt)
    partial_dir.rename(final_dir)
    return receipt


def _artifact_manifest(root: Path) -> list[dict[str, object]]:
    artifacts: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink() and path.name != "artifact-manifest.json":
            artifacts.append(
                {
                    "logical_path": path.relative_to(root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _file_sha256(path),
                }
            )
    return artifacts


def _run_from_params(path: Path) -> Mapping[str, object]:
    params = _read_json(path.resolve(), "TCP真值v2受控参数")
    expected_keys = {
        "schema_version",
        "project_root",
        "ns3_root",
        "manifest_path",
        "scenario_source",
        "contract_path",
        "closure_path",
        "resume_from_output_dir",
        "output_dir",
        "expected_manifest_sha256",
        "expected_scenario_source_sha256",
        "expected_contract_sha256",
        "expected_closure_sha256",
    }
    params_schema = params.get("schema_version")
    if set(params) != expected_keys or params_schema not in REGISTERED_PARAMS_CLOSURE_SCHEMAS:
        raise TcpTruthV2Error("受控参数键集合或模式版本不符")
    project_root = Path(str(params["project_root"])).resolve()
    if project_root != Path(__file__).resolve().parents[2]:
        raise TcpTruthV2Error("project_root 与当前安装代码根不一致")
    ns3_root = Path(str(params["ns3_root"])).resolve()
    if ns3_root.as_posix() != "/root/autodl-tmp/thesis/ns3/ns-3.48":
        raise TcpTruthV2Error("ns-3 根不是固定服务器路径")
    manifest_path = _resolve_under(project_root, params["manifest_path"], "manifest_path")
    scenario_path = _resolve_under(project_root, params["scenario_source"], "scenario_source")
    contract_path = _resolve_under(project_root, params["contract_path"], "contract_path")
    closure_path = _resolve_under(project_root, params["closure_path"], "closure_path")
    resume_value = params["resume_from_output_dir"]
    resume_root = (
        None
        if resume_value is None
        else _resolve_under(project_root, resume_value, "resume_from_output_dir")
    )
    output_root = _resolve_under(project_root, params["output_dir"], "output_dir")
    if manifest_path != project_root / "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl":
        raise TcpTruthV2Error("清单路径偏离冻结路径")
    if scenario_path != project_root / "ns3/r2_protocol_dynamics_v2_scenario.cc":
        raise TcpTruthV2Error("场景路径偏离 v2 独立路径")
    if output_root == project_root / "runs/ns3-data/r2-protocol-paired-v0":
        raise TcpTruthV2Error("v2 禁止复用 attempt5 输出根")
    if resume_root is not None and output_root == resume_root:
        raise TcpTruthV2Error("续跑输出根不得等于来源根")
    expected_hashes = {
        manifest_path: _require_sha(params["expected_manifest_sha256"], "清单哈希"),
        scenario_path: _require_sha(params["expected_scenario_source_sha256"], "场景哈希"),
        contract_path: _require_sha(params["expected_contract_sha256"], "合同哈希"),
        closure_path: _require_sha(params["expected_closure_sha256"], "闭合配置哈希"),
    }
    for artifact, expected in expected_hashes.items():
        if _file_sha256(artifact) != expected:
            raise TcpTruthV2Error(f"输入制品 SHA-256 不一致：{artifact.name}")
    if expected_hashes[manifest_path] != EXPECTED_MANIFEST_SHA256:
        raise TcpTruthV2Error("参数未绑定冻结清单哈希")
    compiled_source = ns3_root / COMPILED_SOURCE
    if not compiled_source.is_file() or compiled_source.is_symlink():
        raise TcpTruthV2Error("ns-3 scratch v2 场景不存在或是符号链接")
    if _file_sha256(compiled_source) != expected_hashes[scenario_path]:
        raise TcpTruthV2Error("项目场景与 ns-3 scratch 副本 SHA-256 不一致")
    version_path = ns3_root / "VERSION"
    if "3.48" not in version_path.read_text(encoding="utf-8"):
        raise TcpTruthV2Error("服务器 ns-3 版本不是3.48")
    contract = _read_json(contract_path, "TCP真值v2合同")
    if contract.get("schema_version") != "flow_probe_r2_ns3_tcp_truth_v2_contract_v1":
        raise TcpTruthV2Error("TCP真值v2合同模式不符")
    if contract.get("fixed_tcp_options") != {
        "BetaLoss": 0.5,
        "Sack": False,
        "Timestamp": False,
        "UseEcn": "Off",
    }:
        raise TcpTruthV2Error("TCP可辨识选项未冻结")
    source_text = scenario_path.read_text(encoding="utf-8")
    for token in (
        '"CongestionWindow"',
        '"SlowStartThreshold"',
        '"BytesInFlight"',
        '"CongState"',
        '"HighestRxAck"',
        '"RTT"',
        '"LastRTT"',
        '"RTO"',
        '"Retransmission"',
        'Config::SetDefault("ns3::TcpSocketBase::Sack", BooleanValue(false))',
        'Config::SetDefault("ns3::TcpSocketBase::Timestamp", BooleanValue(false))',
        '"flow_probe_r2_ns3_protocol_windows_v3"',
        '"Tx", MakeCallback(&WindowCollector::OnIpv4Tx',
        '"Rx", MakeCallback(&WindowCollector::OnIpv4Rx',
        "RecordUniqueTcpRange",
    ):
        if token not in source_text:
            raise TcpTruthV2Error(f"v2场景缺少冻结标记：{token}")
    manifest = _load_manifest(manifest_path)
    closure = _read_json(closure_path, "字段闭合配置")
    _validate_params_closure_schema(params_schema, closure.get("schema_version"))
    selected = _load_selection(closure, manifest)
    reused = (
        _load_reused_receipts(resume_root, selected, expected_hashes[contract_path])
        if resume_root is not None
        else {}
    )
    pending = [
        item for item in selected if item[1].physics_group_sha256 not in reused
    ]
    if not pending:
        raise TcpTruthV2Error("续跑来源已包含全部选择，不应再次运行")
    if output_root.exists() or output_root.is_symlink():
        raise TcpTruthV2Error("字段闭合输出根已存在，禁止覆盖或复用")
    output_root.mkdir(parents=True)
    runs_root = output_root / "runs"
    runs_root.mkdir()
    state = {
        "schema_version": "flow_probe_r2_ns3_tcp_truth_v2_state_v1",
        "status": "running",
        "started_at": _utc_now(),
        "completed_run_count": len(reused),
        "planned_run_count": len(selected),
        "executed_completed_run_count": 0,
        "planned_execution_count": len(pending),
        "reused_run_count": len(reused),
        "resume_from_output_dir": (
            resume_root.relative_to(project_root).as_posix()
            if resume_root is not None
            else None
        ),
    }
    _write_json_atomic(output_root / "run-state.json", state)
    _write_json_atomic(
        output_root / "reused-receipts.json",
        [
            {
                "physics_group_sha256": group,
                "receipt": reused[group],
            }
            for _, run in selected
            if (group := run.physics_group_sha256) in reused
        ],
    )
    receipts: list[Mapping[str, object]] = []
    try:
        for coverage, run in pending:
            receipt = _run_one(
                ns3_root,
                runs_root,
                coverage,
                run,
                expected_hashes[contract_path],
                expected_hashes[scenario_path],
            )
            receipts.append(receipt)
            state["completed_run_count"] = len(reused) + len(receipts)
            state["executed_completed_run_count"] = len(receipts)
            state["updated_at"] = _utc_now()
            _write_json_atomic(output_root / "run-state.json", state)
        aggregate: Counter[str] = Counter()
        transport_families = {run.transport_family for _, run in selected}
        all_receipts = [
            reused[run.physics_group_sha256]
            for _, run in selected
            if run.physics_group_sha256 in reused
        ] + receipts
        for receipt in all_receipts:
            metrics = receipt["metrics"]
            assert isinstance(metrics, Mapping)
            aggregate_keys = list(DIRECTIONAL_COLUMNS)
            if transport_families == {"TCP"}:
                aggregate_keys.extend(
                    (
                        "acked_bytes",
                        "acked_segments",
                        "rtt_sample_count",
                        "loss_event_count",
                        "timeout_event_count",
                        "contraction_event_count",
                        "ack_residual_valid_terms",
                        "loss_residual_valid_terms",
                    )
                )
            for key in aggregate_keys:
                aggregate[key] += int(metrics[key])
        failures: list[str] = []
        if transport_families == {"TCP"}:
            if aggregate["acked_bytes"] <= 0 or aggregate["acked_segments"] <= 0:
                failures.append("未出现非零累计ACK驱动")
            if aggregate["rtt_sample_count"] <= 0:
                failures.append("未出现有效RTT样本")
            if aggregate["loss_event_count"] + aggregate["timeout_event_count"] <= 0:
                failures.append("未出现快速恢复或重传超时事件")
            if aggregate["contraction_event_count"] <= 0:
                failures.append("未出现拥塞窗口或慢启动阈值收缩")
            if aggregate["ack_residual_valid_terms"] <= 0:
                failures.append("ACK NewReno残差没有有效项")
            if aggregate["loss_residual_valid_terms"] <= 0:
                failures.append("拥塞收缩NewReno残差没有有效项")
            if min(
                aggregate["orig_bytes"],
                aggregate["orig_pkts"],
                aggregate["orig_ip_bytes"],
                aggregate["resp_pkts"],
                aggregate["resp_ip_bytes"],
            ) <= 0:
                failures.append("TCP六方向观测未形成有效发起流量或反向ACK流量")
            if aggregate["resp_bytes"] != 0:
                failures.append("当前单向TCP场景出现非零响应有效载荷")
        elif transport_families == {"UDP"} and len(selected) == 1:
            if min(
                aggregate["orig_bytes"],
                aggregate["orig_pkts"],
                aggregate["orig_ip_bytes"],
            ) <= 0:
                failures.append("UDP六方向观测未形成有效发起流量")
            if any(aggregate[key] != 0 for key in ("resp_bytes", "resp_pkts", "resp_ip_bytes")):
                failures.append("当前单向UDP场景出现非零响应方向流量")
        else:
            failures.append("字段闭合选择混合协议或数量超出冻结入口")
        if failures:
            raise TcpTruthV2Error("；".join(failures))
        summary: dict[str, object] = {
            "schema_version": "flow_probe_r2_ns3_tcp_truth_v2_summary_v1",
            "status": "pass",
            "planned_run_count": len(selected),
            "completed_run_count": len(all_receipts),
            "executed_run_count": len(receipts),
            "reused_run_count": len(reused),
            "transport_families": sorted(transport_families),
            "resume_from_output_dir": (
                resume_root.relative_to(project_root).as_posix()
                if resume_root is not None
                else None
            ),
            "sender_count_values": sorted({run.sender_count for _, run in selected}),
            "sender_compositions": sorted(
                {
                    f"{run.benign_sender_count}+{run.attack_sender_count}"
                    for _, run in selected
                }
            ),
            "aggregate": dict(aggregate),
            "scenario_source_sha256": expected_hashes[scenario_path],
            "scenario_source_sha256_values": sorted(
                {
                    str(receipt["scenario_source_sha256"])
                    for receipt in all_receipts
                }
            ),
            "contract_sha256": expected_hashes[contract_path],
            "closure_sha256": expected_hashes[closure_path],
            "manifest_sha256": expected_hashes[manifest_path],
            "run_receipt_schema_version": RECEIPT_SCHEMA,
            "main_schema_version": MAIN_SCHEMA,
            "directional_semantics_version": DIRECTIONAL_SEMANTICS_VERSION,
            "directional_fields": list(DIRECTIONAL_COLUMNS),
            "main_header_sha256": MAIN_HEADER_SHA256,
            "finished_at": _utc_now(),
        }
        _write_json_atomic(output_root / "summary.json", summary)
        state.update({"status": "finished", "finished_at": _utc_now()})
        _write_json_atomic(output_root / "run-state.json", state)
        _write_json_atomic(output_root / "artifact-manifest.json", _artifact_manifest(output_root))
        return summary
    except BaseException as error:
        state.update(
            {
                "status": "failed",
                "error": str(error),
                "finished_at": _utc_now(),
            }
        )
        _write_json_atomic(output_root / "run-state.json", state)
        _write_json_atomic(output_root / "artifact-manifest.json", _artifact_manifest(output_root))
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行R2 ns-3 TCP真值v2字段闭合")
    parser.add_argument("--params", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = _run_from_params(args.params)
    except (OSError, TcpTruthV2Error, subprocess.SubprocessError) as error:
        print(f"R2 ns-3 TCP真值v2字段闭合失败：{error}", file=os.sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
