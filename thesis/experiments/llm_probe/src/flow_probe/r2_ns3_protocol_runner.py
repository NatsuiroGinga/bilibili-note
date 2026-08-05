"""运行并恢复 R2 ns-3 TCP/普通 UDP 严格配对矩阵。"""

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
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Final

from flow_probe.r2_ns3_protocol_matrix import MANIFEST_FIELD_ORDER, ProtocolRunConfig

PROGRAM_NAME: Final = "scratch/flow-probe-r2-protocol"
COMPILED_SOURCE_RELATIVE: Final = PurePosixPath("scratch/flow-probe-r2-protocol.cc")
CSV_SCHEMA_VERSION: Final = "flow_probe_r2_ns3_protocol_windows_v1"
TRACE_SCHEMA_VERSION: Final = "flow_probe_r2_ns3_trace_contract_v2"
WRAPPER_SCHEMA_VERSION: Final = "flow_probe_r2_ns3_wrapper_params_v1"
RUN_BINDING_SCHEMA_VERSION: Final = "flow_probe_r2_ns3_run_binding_v1"
SOURCE_LOCK_SCHEMA_VERSION: Final = "flow_probe_r2_ns3_source_lock_v1"
EXPECTED_MANIFEST_SHA256: Final = (
    "d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111"
)
EXPECTED_MATRIX_CONFIG_SHA256: Final = (
    "0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb"
)
EXPECTED_R2_CONTRACT_SHA256: Final = (
    "aa390129e239aa59d1c6963471e1268498a16740a5f11a916f489fa6a7292566"
)
EXPECTED_BASE_COUNTS: Final = {
    "train-fit": 128,
    "calibration": 32,
    "validation": 32,
    "test": 32,
    "unseen-configuration": 32,
}
CSV_COLUMNS: Final = (
    "schema_version",
    "physics_group_sha256",
    "matrix_config_sha256",
    "r2_contract_sha256",
    "split",
    "run_seed",
    "transport_family",
    "window_index",
    "window_start_s",
    "window_end_s",
    "public_total_packets",
    "public_total_l3_bytes",
    "public_packet_length_mean_l3_bytes",
    "public_packet_length_min_l3_bytes",
    "public_packet_length_max_l3_bytes",
    "public_iat_mean_ms",
    "public_packet_rate_pps",
    "public_byte_rate_Bps",
    "truth_traffic_mode",
    "truth_binary_label",
    "truth_arrival_model",
    "truth_queue_model",
    "truth_ns3_version",
    "truth_tcp_congestion_control",
    "truth_offered_load_ratio",
    "truth_initial_capacity_bps",
    "truth_shifted_capacity_bps",
    "truth_capacity_change_s",
    "truth_access_delay_ms",
    "truth_bottleneck_delay_ms",
    "truth_queue_limit_packets",
    "truth_downstream_loss_rate",
    "truth_sender_count",
    "truth_benign_sender_count",
    "truth_attack_sender_count",
    "truth_total_offered_load_bps",
    "truth_packet_size_app_payload_bytes",
    "truth_capacity_start_bps",
    "truth_capacity_end_bps",
    "truth_capacity_integral_link_bytes",
    "truth_queue_start_l3_bytes",
    "truth_queue_end_l3_bytes",
    "truth_qdisc_received_l3_bytes",
    "truth_qdisc_enqueued_l3_bytes",
    "truth_qdisc_dequeued_l3_bytes",
    "truth_qdisc_drop_before_enqueue_l3_bytes",
    "truth_qdisc_drop_after_dequeue_l3_bytes",
    "truth_downstream_error_loss_l3_bytes",
    "truth_receiver_local_deliver_l3_bytes",
    "truth_device_tx_drop_l3_bytes",
    "truth_queue_start_packets",
    "truth_queue_end_packets",
    "truth_qdisc_received_packets",
    "truth_qdisc_enqueued_packets",
    "truth_qdisc_dequeued_packets",
    "truth_qdisc_drop_before_enqueue_packets",
    "truth_qdisc_drop_after_dequeue_packets",
    "truth_downstream_error_loss_packets",
    "truth_receiver_local_deliver_packets",
    "truth_device_tx_drop_packets",
    "truth_queue_balance_residual_l3_bytes",
    "truth_queue_balance_residual_packets",
    "truth_tcp_cwnd_applicable",
    "truth_tcp_cwnd_observed",
    "truth_tcp_cwnd_trace_connected_senders",
    "truth_tcp_cwnd_observed_senders",
    "truth_tcp_cwnd_mean_bytes",
    "truth_tcp_cwnd_min_bytes",
    "truth_tcp_cwnd_max_bytes",
    "truth_tcp_cwnd_trace_name",
    "truth_tcp_cwnd_aggregation",
    "truth_udp_applicable",
    "truth_udp_planned_app_payload_packets",
    "truth_udp_planned_app_payload_bytes",
    "truth_udp_actual_send_events",
    "truth_udp_actual_send_bytes",
    "truth_udp_target_rate_bps",
    "truth_udp_burst_mode",
    "truth_udp_burst_active",
)
PUBLIC_COLUMNS: Final = tuple(column for column in CSV_COLUMNS if column.startswith("public_"))


class R2NS3RunnerError(RuntimeError):
    """trace、配置、运行制品或恢复状态违反 R2 合同。"""


@dataclass(frozen=True)
class ArtifactRecord:
    """只使用逻辑相对路径的制品绑定。"""

    logical_path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class NS3TraceContract:
    """服务器 ns-3.48 与任务05场景的只读 trace 证据。"""

    schema_version: str
    status: str
    ns3_version: str
    tcp_congestion_control: str
    tcp_cwnd_trace_name: str
    tcp_cwnd_aggregation: str
    queue_trace_names: tuple[str, ...]
    downstream_loss_trace_name: str
    receiver_trace_name: str
    queue_l3_size_semantics: str
    downstream_loss_l3_semantics: str
    scenario_source_sha256: str
    source_artifacts: tuple[ArtifactRecord, ...]

    def to_record(self) -> dict[str, object]:
        record = asdict(self)
        record["queue_trace_names"] = list(self.queue_trace_names)
        record["source_artifacts"] = [asdict(item) for item in self.source_artifacts]
        return record


@dataclass(frozen=True)
class RunValidation:
    """单条协议运行的窗口与状态验收结果。"""

    physics_group_sha256: str
    transport_family: str
    window_count: int
    csv_sha256: str
    csv_size_bytes: int
    residual_violation_count: int
    device_tx_drop_count: int
    tcp_cwnd_coverage: float
    tcp_cwnd_observed_windows: int

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PairValidation:
    """一个基础配置的 TCP/UDP 双侧联合验收。"""

    schema_version: str
    physics_group_sha256: str
    status: str
    base_config_sha256: str
    manifest_sha256: str
    scenario_source_sha256: str
    trace_contract_sha256: str
    tcp_config_sha256: str
    udp_config_sha256: str
    tcp_csv_sha256: str
    udp_csv_sha256: str
    tcp_window_count: int
    udp_window_count: int
    tcp_cwnd_coverage: float

    def to_record(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MatrixRunSummary:
    """全部512条运行与256个有效配对的正式汇总。"""

    status: str
    base_configuration_count: int
    protocol_run_count: int
    completed_run_count: int
    skipped_run_count: int
    failed_run_count: int
    valid_pair_count: int
    manifest_sha256: str
    scenario_source_sha256: str
    trace_contract_sha256: str
    source_lock_sha256: str

    def to_record(self) -> dict[str, object]:
        return asdict(self)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _object_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("ascii")).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial")
    if temporary.exists() or temporary.is_symlink():
        raise R2NS3RunnerError(f"原子写临时文件已存在：{temporary}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _read_json(path: Path, name: str) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise R2NS3RunnerError(f"{name} 不存在、不是文件或是符号链接：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise R2NS3RunnerError(f"{name} 无法解析：{error}") from error
    if not isinstance(value, Mapping):
        raise R2NS3RunnerError(f"{name} 必须是 JSON 对象")
    return value


def _artifact(path: Path, logical_root: Path) -> ArtifactRecord:
    normalized = path.resolve()
    root = logical_root.resolve()
    try:
        relative = normalized.relative_to(root)
    except ValueError as error:
        raise R2NS3RunnerError(f"制品不在逻辑根内：{normalized}") from error
    if not normalized.is_file() or normalized.is_symlink():
        raise R2NS3RunnerError(f"制品不存在、不是文件或是符号链接：{normalized}")
    return ArtifactRecord(relative.as_posix(), normalized.stat().st_size, _file_sha256(normalized))


def _require_token(text: str, token: str, name: str) -> None:
    if token not in text:
        raise R2NS3RunnerError(f"{name} 缺少冻结 token：{token}")


def _read_required_sources(ns3_root: Path, relative_paths: Sequence[str]) -> tuple[str, tuple[ArtifactRecord, ...]]:
    payloads: list[str] = []
    artifacts: list[ArtifactRecord] = []
    for relative in relative_paths:
        path = ns3_root / relative
        if not path.is_file() or path.is_symlink():
            raise R2NS3RunnerError(f"ns-3 trace 源文件缺失或是符号链接：{relative}")
        payloads.append(path.read_text(encoding="utf-8"))
        artifacts.append(_artifact(path, ns3_root))
    return "\n".join(payloads), tuple(artifacts)


def audit_ns3_trace_contract(ns3_root: Path, scenario_source: Path) -> NS3TraceContract:
    """只读核验 ns-3.48 trace 名称及下游丢失的网络层字节语义。"""
    root = Path(ns3_root).expanduser().resolve()
    launcher = root / "ns3"
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise R2NS3RunnerError(f"ns-3 启动器不存在或不可执行：{launcher}")
    version_path = root / "VERSION"
    if not version_path.is_file() or version_path.is_symlink():
        raise R2NS3RunnerError("ns-3 VERSION 文件缺失或是符号链接")
    version_text = version_path.read_text(encoding="utf-8").strip()
    if re.search(r"(^|[^0-9])3\.48([^0-9]|$)", version_text) is None:
        raise R2NS3RunnerError(f"服务器 ns-3 版本不是 3.48：{version_text}")

    tcp_text, tcp_artifacts = _read_required_sources(
        root,
        (
            "src/internet/model/tcp-socket-base.cc",
            "src/internet/model/tcp-socket-base.h",
        ),
    )
    queue_text, queue_artifacts = _read_required_sources(
        root,
        (
            "src/traffic-control/model/queue-disc.cc",
            "src/traffic-control/model/queue-disc.h",
        ),
    )
    queue_item_text, queue_item_artifacts = _read_required_sources(
        root,
        (
            "src/internet/model/ipv4-queue-disc-item.cc",
            "src/internet/model/ipv4-queue-disc-item.h",
        ),
    )
    p2p_text, p2p_artifacts = _read_required_sources(
        root,
        (
            "src/point-to-point/model/point-to-point-net-device.cc",
            "src/point-to-point/model/point-to-point-net-device.h",
        ),
    )
    ppp_text, ppp_artifacts = _read_required_sources(
        root,
        (
            "src/point-to-point/model/ppp-header.cc",
            "src/point-to-point/model/ppp-header.h",
        ),
    )
    packet_text, packet_artifacts = _read_required_sources(
        root,
        (
            "src/network/model/packet.cc",
            "src/network/model/packet.h",
        ),
    )
    ipv4_text, ipv4_artifacts = _read_required_sources(
        root,
        (
            "src/internet/model/ipv4-l3-protocol.cc",
            "src/internet/model/ipv4-l3-protocol.h",
        ),
    )
    _require_token(tcp_text, "CongestionWindow", "TcpSocketBase")
    _require_token(tcp_text, "m_cWndTrace", "TcpSocketBase")
    for trace_name in ("Enqueue", "Dequeue", "DropBeforeEnqueue", "DropAfterDequeue"):
        _require_token(queue_text, trace_name, "QueueDisc")
    _require_token(
        queue_item_text,
        "Ipv4QueueDiscItem::GetSize",
        "Ipv4QueueDiscItem",
    )
    _require_token(
        queue_item_text,
        "m_header.GetSerializedSize()",
        "Ipv4QueueDiscItem",
    )
    _require_token(
        queue_item_text,
        "GetPacket()",
        "Ipv4QueueDiscItem",
    )
    _require_token(
        queue_item_text,
        "->GetSize()",
        "Ipv4QueueDiscItem",
    )
    _require_token(p2p_text, "PhyRxDrop", "PointToPointNetDevice")
    _require_token(p2p_text, "MacTxDrop", "PointToPointNetDevice")
    _require_token(ipv4_text, "LocalDeliver", "Ipv4L3Protocol")

    p2p_without_comments = re.sub(
        r"//[^\n]*|/\*.*?\*/", "", p2p_text, flags=re.DOTALL
    )
    normalized_p2p = "".join(p2p_without_comments.split())
    process_header_definition_position = normalized_p2p.find(
        "PointToPointNetDevice::ProcessHeader(Ptr<Packet>p,uint16_t&param)"
    )
    remove_header_position = normalized_p2p.find(
        "p->RemoveHeader(ppp)", process_header_definition_position
    )
    receive_position = normalized_p2p.find(
        "PointToPointNetDevice::Receive(Ptr<Packet>packet)"
    )
    corrupt_branch_position = normalized_p2p.find(
        "if(m_receiveErrorModel&&m_receiveErrorModel->IsCorrupt(packet))",
        receive_position,
    )
    rx_drop_position = normalized_p2p.find(
        "m_phyRxDropTrace(packet)", corrupt_branch_position
    )
    success_branch_position = normalized_p2p.find("}else{", rx_drop_position)
    process_header_position = normalized_p2p.find(
        "ProcessHeader(packet,protocol)", success_branch_position
    )
    if not (
        0 <= process_header_definition_position
        < remove_header_position
        < receive_position
        < corrupt_branch_position
        < rx_drop_position
        < success_branch_position
        < process_header_position
    ):
        raise R2NS3RunnerError(
            "无法证明 PhyRxDrop 位于 PPP 头移除前的错误分支"
        )

    normalized_ppp = "".join(ppp_text.split())
    if "PppHeader::GetSerializedSize()const{return2;}" not in normalized_ppp:
        raise R2NS3RunnerError("无法证明 ns-3.48 PPP 头声明长度为 2 字节")
    _require_token(
        packet_text,
        "Packet::PeekHeader(Header& header) const",
        "Packet",
    )
    _require_token(
        packet_text,
        "header.Deserialize(m_buffer.Begin())",
        "Packet::PeekHeader",
    )

    scenario = Path(scenario_source).expanduser().resolve()
    if not scenario.is_file() or scenario.is_symlink():
        raise R2NS3RunnerError(f"任务05 C++ 场景不存在或是符号链接：{scenario}")
    scenario_text = scenario.read_text(encoding="utf-8")
    for token in (
        'kNs3Version = "3.48"',
        'kTcpCongestionControl = "ns3::TcpNewReno"',
        "TcpNewReno::GetTypeId()",
        'kCwndTraceName = "CongestionWindow"',
        '#include "ns3/ppp-header.h"',
        "kPppIpv4Protocol = 0x0021",
        '"DropBeforeEnqueue"',
        '"DropAfterDequeue"',
        '"PhyRxDrop"',
        '"LocalDeliver"',
        "PppHeader pppHeader",
        "pppHeader.GetSerializedSize()",
        "packet->PeekHeader(pppHeader)",
        "pppHeader.GetProtocol() != kPppIpv4Protocol",
        "packet->GetSize() - parsedPppHeaderBytes",
    ):
        _require_token(scenario_text, token, "任务05 C++ 场景")
    if "m_downstreamErrorLossBytes += packet->GetSize();" in scenario_text:
        raise R2NS3RunnerError("下游错误丢失仍把含 PPP 头整包计为网络层字节")

    artifacts = (
        _artifact(version_path, root),
        *tcp_artifacts,
        *queue_artifacts,
        *queue_item_artifacts,
        *p2p_artifacts,
        *ppp_artifacts,
        *packet_artifacts,
        *ipv4_artifacts,
    )
    return NS3TraceContract(
        schema_version=TRACE_SCHEMA_VERSION,
        status="pass",
        ns3_version="3.48",
        tcp_congestion_control="ns3::TcpNewReno",
        tcp_cwnd_trace_name="CongestionWindow",
        tcp_cwnd_aggregation="time_weighted_mean_over_observed_senders",
        queue_trace_names=(
            "Enqueue",
            "Dequeue",
            "DropBeforeEnqueue",
            "DropAfterDequeue",
        ),
        downstream_loss_trace_name="PhyRxDrop",
        receiver_trace_name="LocalDeliver",
        queue_l3_size_semantics="packet_plus_ipv4_header",
        downstream_loss_l3_semantics="PhyRxDrop_packet_minus_verified_PppHeader_2_bytes",
        scenario_source_sha256=_file_sha256(scenario),
        source_artifacts=artifacts,
    )


def _load_manifest(path: Path) -> tuple[ProtocolRunConfig, ...]:
    manifest = Path(path).expanduser().resolve()
    if not manifest.is_file() or manifest.is_symlink():
        raise R2NS3RunnerError(f"任务04冻结清单不存在或是符号链接：{manifest}")
    manifest_sha256 = _file_sha256(manifest)
    if manifest_sha256 != EXPECTED_MANIFEST_SHA256:
        raise R2NS3RunnerError(
            f"任务04冻结清单 SHA-256 不符：{manifest_sha256}"
        )
    checksum_path = manifest.with_name("ns3-config-manifest.sha256")
    expected_checksum = f"{manifest_sha256}  {manifest.name}\n"
    if not checksum_path.is_file() or checksum_path.read_text(encoding="ascii") != expected_checksum:
        raise R2NS3RunnerError("任务04清单校验文件缺失或内容不符")

    runs: list[ProtocolRunConfig] = []
    with manifest.open("r", encoding="ascii") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.endswith("\n") or not line.strip():
                raise R2NS3RunnerError(f"任务04清单第 {line_number} 行不是规范 JSONL")
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise R2NS3RunnerError(
                    f"任务04清单第 {line_number} 行无法解析：{error}"
                ) from error
            if not isinstance(record, dict) or tuple(record) != MANIFEST_FIELD_ORDER:
                raise R2NS3RunnerError(f"任务04清单第 {line_number} 行字段顺序不符")
            try:
                run = ProtocolRunConfig(**record)
            except TypeError as error:
                raise R2NS3RunnerError(
                    f"任务04清单第 {line_number} 行字段无法构造运行配置：{error}"
                ) from error
            runs.append(run)
    if len(runs) != 512:
        raise R2NS3RunnerError(f"任务04清单必须恰含512条运行，实际为 {len(runs)}")
    if Counter(run.transport_family for run in runs) != Counter({"TCP": 256, "UDP": 256}):
        raise R2NS3RunnerError("任务04清单的 TCP/UDP 数量不配平")
    if {run.matrix_config_sha256 for run in runs} != {EXPECTED_MATRIX_CONFIG_SHA256}:
        raise R2NS3RunnerError("任务04清单绑定的矩阵配置哈希不符")
    if {run.r2_contract_sha256 for run in runs} != {EXPECTED_R2_CONTRACT_SHA256}:
        raise R2NS3RunnerError("任务04清单绑定的任务01配置哈希不符")
    groups: dict[str, list[ProtocolRunConfig]] = defaultdict(list)
    for run in runs:
        groups[run.physics_group_sha256].append(run)
    if len(groups) != 256:
        raise R2NS3RunnerError("任务04清单未形成256个基础配对组")
    split_counts = Counter(pair[0].split for pair in groups.values())
    if dict(split_counts) != EXPECTED_BASE_COUNTS:
        raise R2NS3RunnerError(f"任务04基础配对组划分数量不符：{dict(split_counts)}")
    for group_id, pair in groups.items():
        if len(pair) != 2 or {run.transport_family for run in pair} != {"TCP", "UDP"}:
            raise R2NS3RunnerError(f"配对组 {group_id} 未恰含 TCP/UDP 两侧")
        if pair[0].to_base_record() != pair[1].to_base_record():
            raise R2NS3RunnerError(f"配对组 {group_id} 除协议外仍有配置差异")
    return tuple(runs)


def _parse_int(row: Mapping[str, str], column: str) -> int:
    raw = row.get(column)
    if raw is None or re.fullmatch(r"-?(?:0|[1-9][0-9]*)", raw) is None:
        raise R2NS3RunnerError(f"CSV 字段 {column} 不是规范整数")
    try:
        return int(raw)
    except ValueError as error:
        raise R2NS3RunnerError(f"CSV 字段 {column} 不是规范整数") from error


def _parse_float(row: Mapping[str, str], column: str) -> float:
    try:
        value = float(row[column])
    except (KeyError, ValueError) as error:
        raise R2NS3RunnerError(f"CSV 字段 {column} 不是规范数值") from error
    if not math.isfinite(value):
        raise R2NS3RunnerError(f"CSV 字段 {column} 包含非有限值")
    return value


def _mbps_to_bps(value: float) -> int:
    return math.floor(value * 1_000_000.0 + 0.5)


def _require_float_close(
    row: Mapping[str, str],
    column: str,
    expected: float,
    *,
    absolute_tolerance: float = 1e-8,
) -> float:
    actual = _parse_float(row, column)
    if not math.isclose(
        actual,
        expected,
        rel_tol=1e-12,
        abs_tol=absolute_tolerance,
    ):
        raise R2NS3RunnerError(
            f"运行 CSV 的 {column} 与冻结配置或独立重算值不一致"
        )
    return actual


def _validate_csv(path: Path, config: ProtocolRunConfig) -> RunValidation:
    if not path.is_file() or path.is_symlink():
        raise R2NS3RunnerError(f"运行 CSV 不存在、不是文件或是符号链接：{path}")
    residual_violations = 0
    device_tx_drop_count = 0
    device_tx_drop_bytes = 0
    cwnd_observed_windows = 0
    row_count = 0
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != CSV_COLUMNS:
            raise R2NS3RunnerError("运行 CSV 字段名称或顺序偏离冻结合同")
        for expected_index, row in enumerate(reader):
            row_count += 1
            if None in row or any(value is None for value in row.values()):
                raise R2NS3RunnerError("运行 CSV 行存在多余或缺失字段")
            if row["schema_version"] != CSV_SCHEMA_VERSION:
                raise R2NS3RunnerError("运行 CSV 模式版本不符")
            identity = {
                "physics_group_sha256": config.physics_group_sha256,
                "matrix_config_sha256": config.matrix_config_sha256,
                "r2_contract_sha256": config.r2_contract_sha256,
                "split": config.split,
                "run_seed": str(config.run_seed),
                "transport_family": config.transport_family,
                "truth_traffic_mode": config.traffic_mode,
                "truth_binary_label": str(config.binary_label),
                "truth_arrival_model": config.arrival_model,
                "truth_queue_model": config.queue_model,
                "truth_ns3_version": config.ns3_version,
                "truth_tcp_congestion_control": config.tcp_congestion_control,
            }
            for column, expected in identity.items():
                if row[column] != expected:
                    raise R2NS3RunnerError(
                        f"运行 CSV 的 {column} 与冻结配置不一致"
                    )
            if _parse_int(row, "window_index") != expected_index:
                raise R2NS3RunnerError("运行 CSV 窗口序号不连续")
            expected_start = expected_index * config.window_seconds
            expected_end = (expected_index + 1) * config.window_seconds
            if not math.isclose(_parse_float(row, "window_start_s"), expected_start, abs_tol=1e-8):
                raise R2NS3RunnerError("运行 CSV 窗口起点不连续")
            if not math.isclose(_parse_float(row, "window_end_s"), expected_end, abs_tol=1e-8):
                raise R2NS3RunnerError("运行 CSV 窗口终点不连续")

            expected_integer_truth = {
                "truth_initial_capacity_bps": _mbps_to_bps(config.initial_capacity_mbps),
                "truth_shifted_capacity_bps": _mbps_to_bps(config.shifted_capacity_mbps),
                "truth_queue_limit_packets": config.queue_limit_packets,
                "truth_sender_count": config.sender_count,
                "truth_benign_sender_count": config.benign_sender_count,
                "truth_attack_sender_count": config.attack_sender_count,
                "truth_total_offered_load_bps": _mbps_to_bps(config.total_offered_load_mbps),
                "truth_packet_size_app_payload_bytes": config.packet_size_bytes,
            }
            for column, expected in expected_integer_truth.items():
                if _parse_int(row, column) != expected:
                    raise R2NS3RunnerError(
                        f"运行 CSV 的 {column} 与冻结配置不一致"
                    )
            expected_float_truth = {
                "truth_offered_load_ratio": config.offered_load_ratio,
                "truth_capacity_change_s": config.capacity_change_time_seconds,
                "truth_access_delay_ms": config.access_delay_ms,
                "truth_bottleneck_delay_ms": config.bottleneck_delay_ms,
                "truth_downstream_loss_rate": config.downstream_loss_rate,
            }
            for column, expected in expected_float_truth.items():
                _require_float_close(row, column, expected)

            initial_capacity_bps = expected_integer_truth["truth_initial_capacity_bps"]
            shifted_capacity_bps = expected_integer_truth["truth_shifted_capacity_bps"]
            change_time = config.capacity_change_time_seconds
            expected_capacity_start = (
                shifted_capacity_bps
                if expected_start >= change_time - 1e-8
                else initial_capacity_bps
            )
            expected_capacity_end = (
                shifted_capacity_bps
                if expected_end >= change_time - 1e-8
                else initial_capacity_bps
            )
            before_change_seconds = max(
                0.0,
                min(expected_end, change_time) - expected_start,
            )
            after_change_seconds = max(
                0.0,
                expected_end - max(expected_start, change_time),
            )
            expected_capacity_integral = (
                initial_capacity_bps * before_change_seconds
                + shifted_capacity_bps * after_change_seconds
            ) / 8.0
            if _parse_int(row, "truth_capacity_start_bps") != expected_capacity_start:
                raise R2NS3RunnerError("窗口起始容量与冻结容量轨迹不一致")
            if _parse_int(row, "truth_capacity_end_bps") != expected_capacity_end:
                raise R2NS3RunnerError("窗口结束容量与冻结容量轨迹不一致")
            _require_float_close(
                row,
                "truth_capacity_integral_link_bytes",
                expected_capacity_integral,
                absolute_tolerance=1e-6,
            )

            for column in PUBLIC_COLUMNS:
                if _parse_float(row, column) < 0.0:
                    raise R2NS3RunnerError(f"公共观测 {column} 出现负数")

            nonnegative_integer_columns = (
                "public_total_packets",
                "public_total_l3_bytes",
                "public_packet_length_min_l3_bytes",
                "public_packet_length_max_l3_bytes",
                "truth_queue_start_l3_bytes",
                "truth_queue_end_l3_bytes",
                "truth_qdisc_received_l3_bytes",
                "truth_qdisc_enqueued_l3_bytes",
                "truth_qdisc_dequeued_l3_bytes",
                "truth_qdisc_drop_before_enqueue_l3_bytes",
                "truth_qdisc_drop_after_dequeue_l3_bytes",
                "truth_downstream_error_loss_l3_bytes",
                "truth_receiver_local_deliver_l3_bytes",
                "truth_device_tx_drop_l3_bytes",
                "truth_queue_start_packets",
                "truth_queue_end_packets",
                "truth_qdisc_received_packets",
                "truth_qdisc_enqueued_packets",
                "truth_qdisc_dequeued_packets",
                "truth_qdisc_drop_before_enqueue_packets",
                "truth_qdisc_drop_after_dequeue_packets",
                "truth_downstream_error_loss_packets",
                "truth_receiver_local_deliver_packets",
                "truth_device_tx_drop_packets",
                "truth_tcp_cwnd_applicable",
                "truth_tcp_cwnd_observed",
                "truth_tcp_cwnd_trace_connected_senders",
                "truth_tcp_cwnd_observed_senders",
                "truth_tcp_cwnd_min_bytes",
                "truth_tcp_cwnd_max_bytes",
                "truth_udp_applicable",
                "truth_udp_planned_app_payload_packets",
                "truth_udp_planned_app_payload_bytes",
                "truth_udp_actual_send_events",
                "truth_udp_actual_send_bytes",
                "truth_udp_target_rate_bps",
                "truth_udp_burst_mode",
                "truth_udp_burst_active",
            )
            for column in nonnegative_integer_columns:
                if _parse_int(row, column) < 0:
                    raise R2NS3RunnerError(f"运行 CSV 的 {column} 不得为负")

            enqueued_bytes = _parse_int(row, "truth_qdisc_enqueued_l3_bytes")
            drop_before_bytes = _parse_int(
                row, "truth_qdisc_drop_before_enqueue_l3_bytes"
            )
            received_bytes = _parse_int(row, "truth_qdisc_received_l3_bytes")
            enqueued_packets = _parse_int(row, "truth_qdisc_enqueued_packets")
            drop_before_packets = _parse_int(
                row, "truth_qdisc_drop_before_enqueue_packets"
            )
            received_packets = _parse_int(row, "truth_qdisc_received_packets")
            if received_bytes != enqueued_bytes + drop_before_bytes:
                raise R2NS3RunnerError("队列收到的网络层字节与入队/入队前丢弃不闭合")
            if received_packets != enqueued_packets + drop_before_packets:
                raise R2NS3RunnerError("队列收到的包数与入队/入队前丢弃不闭合")
            declared_residual_bytes = _parse_int(
                row, "truth_queue_balance_residual_l3_bytes"
            )
            declared_residual_packets = _parse_int(
                row, "truth_queue_balance_residual_packets"
            )
            recomputed_residual_bytes = (
                _parse_int(row, "truth_queue_end_l3_bytes")
                - _parse_int(row, "truth_queue_start_l3_bytes")
                - enqueued_bytes
                + _parse_int(row, "truth_qdisc_dequeued_l3_bytes")
            )
            recomputed_residual_packets = (
                _parse_int(row, "truth_queue_end_packets")
                - _parse_int(row, "truth_queue_start_packets")
                - enqueued_packets
                + _parse_int(row, "truth_qdisc_dequeued_packets")
            )
            residual_violations += int(
                declared_residual_bytes != recomputed_residual_bytes
                or declared_residual_packets != recomputed_residual_packets
                or recomputed_residual_bytes != 0
                or recomputed_residual_packets != 0
            )
            tx_drops = _parse_int(row, "truth_device_tx_drop_packets")
            device_tx_drop_count += tx_drops
            device_tx_drop_bytes += _parse_int(row, "truth_device_tx_drop_l3_bytes")

            public_packets = _parse_int(row, "public_total_packets")
            public_bytes = _parse_int(row, "public_total_l3_bytes")
            if public_packets != received_packets or public_bytes != received_bytes:
                raise R2NS3RunnerError("公共包/字节观测与队列直接到达 trace 不一致")
            expected_packet_mean = (
                received_bytes / received_packets if received_packets else 0.0
            )
            public_mean = _require_float_close(
                row,
                "public_packet_length_mean_l3_bytes",
                expected_packet_mean,
                absolute_tolerance=1e-6,
            )
            public_min = _parse_int(row, "public_packet_length_min_l3_bytes")
            public_max = _parse_int(row, "public_packet_length_max_l3_bytes")
            if received_packets == 0 and (public_min != 0 or public_max != 0):
                raise R2NS3RunnerError("空窗口的公共包长边界必须为零")
            if received_packets > 0 and not public_min <= public_mean <= public_max:
                raise R2NS3RunnerError("公共包长最小值、均值与最大值次序不合法")
            _require_float_close(
                row,
                "public_packet_rate_pps",
                received_packets / config.window_seconds,
                absolute_tolerance=1e-6,
            )
            _require_float_close(
                row,
                "public_byte_rate_Bps",
                received_bytes / config.window_seconds,
                absolute_tolerance=1e-6,
            )

            tcp_applicable = _parse_int(row, "truth_tcp_cwnd_applicable")
            tcp_observed = _parse_int(row, "truth_tcp_cwnd_observed")
            udp_applicable = _parse_int(row, "truth_udp_applicable")
            if config.transport_family == "TCP":
                if tcp_applicable != 1 or udp_applicable != 0:
                    raise R2NS3RunnerError("TCP 运行的 TCP/UDP 状态适用掩码不符")
                if row["truth_tcp_cwnd_trace_name"] != "CongestionWindow":
                    raise R2NS3RunnerError("TCP 运行未声明直接 CongestionWindow trace")
                if row["truth_tcp_cwnd_aggregation"] != "time_weighted_mean_over_observed_senders":
                    raise R2NS3RunnerError("TCP cwnd 聚合规则不符")
                if _parse_int(row, "truth_tcp_cwnd_trace_connected_senders") != config.sender_count:
                    raise R2NS3RunnerError("TCP socket 未全部连接 CongestionWindow trace")
                observed_senders = _parse_int(
                    row, "truth_tcp_cwnd_observed_senders"
                )
                if observed_senders > config.sender_count:
                    raise R2NS3RunnerError("TCP cwnd 观测发送者数量超过配置")
                if tcp_observed != int(observed_senders > 0):
                    raise R2NS3RunnerError("TCP cwnd 观测掩码与观测发送者数量不一致")
                cwnd_mean = _parse_float(row, "truth_tcp_cwnd_mean_bytes")
                cwnd_min = _parse_int(row, "truth_tcp_cwnd_min_bytes")
                cwnd_max = _parse_int(row, "truth_tcp_cwnd_max_bytes")
                if tcp_observed and not 0 < cwnd_min <= cwnd_mean <= cwnd_max:
                    raise R2NS3RunnerError("TCP cwnd 最小值、均值与最大值不合法")
                if not tcp_observed and (cwnd_min != 0 or cwnd_mean != 0.0 or cwnd_max != 0):
                    raise R2NS3RunnerError("未观测 TCP cwnd 的窗口携带了伪状态")
                cwnd_observed_windows += int(tcp_observed == 1)
                for column in (
                    "truth_udp_planned_app_payload_packets",
                    "truth_udp_planned_app_payload_bytes",
                    "truth_udp_actual_send_events",
                    "truth_udp_actual_send_bytes",
                    "truth_udp_target_rate_bps",
                    "truth_udp_burst_mode",
                    "truth_udp_burst_active",
                ):
                    if _parse_int(row, column) != 0:
                        raise R2NS3RunnerError("TCP 运行携带了伪 UDP 应用状态")
            else:
                if tcp_applicable != 0 or tcp_observed != 0 or udp_applicable != 1:
                    raise R2NS3RunnerError("UDP 运行的 TCP/UDP 状态适用掩码不符")
                for column in (
                    "truth_tcp_cwnd_trace_connected_senders",
                    "truth_tcp_cwnd_observed_senders",
                    "truth_tcp_cwnd_mean_bytes",
                    "truth_tcp_cwnd_min_bytes",
                    "truth_tcp_cwnd_max_bytes",
                ):
                    if _parse_float(row, column) != 0.0:
                        raise R2NS3RunnerError("UDP 运行携带了伪 TCP cwnd 状态")
                if row["truth_tcp_cwnd_trace_name"] != "NONE" or row[
                    "truth_tcp_cwnd_aggregation"
                ] != "not_applicable":
                    raise R2NS3RunnerError("UDP 运行的 TCP trace 文本适用性不符")
                planned_packets = _parse_int(
                    row, "truth_udp_planned_app_payload_packets"
                )
                planned_bytes = _parse_int(
                    row, "truth_udp_planned_app_payload_bytes"
                )
                actual_events = _parse_int(row, "truth_udp_actual_send_events")
                actual_bytes = _parse_int(row, "truth_udp_actual_send_bytes")
                if planned_bytes != planned_packets * config.packet_size_bytes:
                    raise R2NS3RunnerError("UDP 计划应用载荷包数与字节数不一致")
                if actual_events > planned_packets or actual_bytes > planned_bytes:
                    raise R2NS3RunnerError("UDP 实际发送状态超过计划发送状态")
                if actual_bytes != actual_events * config.packet_size_bytes:
                    raise R2NS3RunnerError("UDP 实际发送事件与应用载荷字节不一致")
                if _parse_int(row, "truth_udp_target_rate_bps") != _mbps_to_bps(
                    config.total_offered_load_mbps
                ):
                    raise R2NS3RunnerError("UDP 目标发送速率与冻结配置不一致")
                expected_burst_mode = int(config.arrival_model == "bursty")
                if _parse_int(row, "truth_udp_burst_mode") != expected_burst_mode:
                    raise R2NS3RunnerError("UDP 突发模式与冻结到达过程不一致")
                if _parse_int(row, "truth_udp_burst_active") != int(
                    planned_packets > 0
                ):
                    raise R2NS3RunnerError("UDP 突发活动状态与直接计划事件不一致")

    if row_count != 120:
        raise R2NS3RunnerError(f"每条正式运行必须恰有120个窗口，实际为 {row_count}")
    if residual_violations:
        raise R2NS3RunnerError(f"运行存在 {residual_violations} 个双守恒残差窗口")
    if device_tx_drop_count or device_tx_drop_bytes:
        raise R2NS3RunnerError(
            "运行存在未纳入口径的设备发送丢弃："
            f"{device_tx_drop_count} 包/{device_tx_drop_bytes} 网络层字节"
        )
    cwnd_coverage = (
        cwnd_observed_windows / row_count if config.transport_family == "TCP" else 0.0
    )
    if config.transport_family == "TCP" and cwnd_coverage < 0.95:
        raise R2NS3RunnerError(
            f"TCP cwnd 窗口覆盖率 {cwnd_coverage:.6f} 低于0.95"
        )
    return RunValidation(
        physics_group_sha256=config.physics_group_sha256,
        transport_family=config.transport_family,
        window_count=row_count,
        csv_sha256=_file_sha256(path),
        csv_size_bytes=path.stat().st_size,
        residual_violation_count=residual_violations,
        device_tx_drop_count=device_tx_drop_count,
        tcp_cwnd_coverage=cwnd_coverage,
        tcp_cwnd_observed_windows=cwnd_observed_windows,
    )


def _load_run_config(path: Path) -> ProtocolRunConfig:
    value = _read_json(path, "单运行配置")
    if tuple(value) != MANIFEST_FIELD_ORDER:
        raise R2NS3RunnerError("单运行配置字段顺序偏离任务04合同")
    try:
        return ProtocolRunConfig(**value)
    except TypeError as error:
        raise R2NS3RunnerError(f"单运行配置字段不合法：{error}") from error


def _validate_success_receipt(
    run_dir: Path,
    config: ProtocolRunConfig,
    validation: RunValidation,
    trace_contract: NS3TraceContract,
) -> Mapping[str, object]:
    receipt = _read_json(run_dir / "receipt.json", "单运行成功回执")
    if receipt.get("status") != "pass" or receipt.get("validation_status") != "pass":
        raise R2NS3RunnerError("已发布单运行缺少通过状态")
    output_root = run_dir.parents[2]
    config_path = run_dir / "config.json"
    csv_path = run_dir / "result.csv"
    expected_config_sha256 = _file_sha256(config_path)
    canonical_config_sha256 = hashlib.sha256(_config_bytes(config)).hexdigest()
    if expected_config_sha256 != canonical_config_sha256:
        raise R2NS3RunnerError("单运行配置 JSON 不是任务04规范字节表示")
    expected_trace_sha256 = _object_sha256(trace_contract.to_record())
    expected_bindings = {
        "scenario_source_sha256": trace_contract.scenario_source_sha256,
        "trace_contract_sha256": expected_trace_sha256,
        "config_sha256": expected_config_sha256,
        "csv_sha256": validation.csv_sha256,
        "csv_size_bytes": validation.csv_size_bytes,
    }
    for key, expected in expected_bindings.items():
        if receipt.get(key) != expected:
            raise R2NS3RunnerError(f"单运行成功回执的 {key} 与已发布制品不一致")
    manifest_sha256 = receipt.get("manifest_sha256")
    if manifest_sha256 != EXPECTED_MANIFEST_SHA256:
        raise R2NS3RunnerError("单运行成功回执未绑定任务04冻结清单")

    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list):
        raise R2NS3RunnerError("单运行成功回执缺少制品列表")
    artifact_by_path: dict[str, Mapping[str, object]] = {}
    for value in artifacts:
        if not isinstance(value, Mapping) or not isinstance(
            value.get("logical_path"), str
        ):
            raise R2NS3RunnerError("单运行成功回执包含非法制品记录")
        logical_path = str(value["logical_path"])
        if logical_path in artifact_by_path:
            raise R2NS3RunnerError("单运行成功回执包含重复逻辑路径")
        artifact_by_path[logical_path] = value
    for artifact_path in (config_path, csv_path):
        expected_artifact = asdict(_artifact(artifact_path, output_root))
        if artifact_by_path.get(expected_artifact["logical_path"]) != expected_artifact:
            raise R2NS3RunnerError("单运行成功回执未精确绑定配置 JSON 或 CSV")
    return receipt


def validate_protocol_pair(pair_dir: Path, trace_contract: NS3TraceContract) -> PairValidation:
    """联合验证一个基础配置的 TCP/UDP 双侧配置、CSV 和状态适用性。"""
    if trace_contract.status != "pass" or trace_contract.tcp_cwnd_trace_name != "CongestionWindow":
        raise R2NS3RunnerError("ns-3 trace 合同未通过，不能验收协议配对")
    root = Path(pair_dir).expanduser().resolve()
    tcp_dir = root / "TCP"
    udp_dir = root / "UDP"
    if not tcp_dir.is_dir() or tcp_dir.is_symlink() or not udp_dir.is_dir() or udp_dir.is_symlink():
        raise R2NS3RunnerError("配对目录未同时包含已发布 TCP 与 UDP 运行")
    tcp_config = _load_run_config(tcp_dir / "config.json")
    udp_config = _load_run_config(udp_dir / "config.json")
    if tcp_config.transport_family != "TCP" or udp_config.transport_family != "UDP":
        raise R2NS3RunnerError("配对目录协议身份不符")
    if tcp_config.to_base_record() != udp_config.to_base_record():
        raise R2NS3RunnerError("TCP/UDP 配对除协议外仍有配置差异")
    if root.name != tcp_config.physics_group_sha256:
        raise R2NS3RunnerError("配对目录名与 physics_group_sha256 不一致")
    tcp_validation = _validate_csv(tcp_dir / "result.csv", tcp_config)
    udp_validation = _validate_csv(udp_dir / "result.csv", udp_config)
    tcp_receipt = _validate_success_receipt(
        tcp_dir,
        tcp_config,
        tcp_validation,
        trace_contract,
    )
    udp_receipt = _validate_success_receipt(
        udp_dir,
        udp_config,
        udp_validation,
        trace_contract,
    )
    for key in (
        "manifest_sha256",
        "scenario_source_sha256",
        "trace_contract_sha256",
    ):
        if tcp_receipt.get(key) != udp_receipt.get(key):
            raise R2NS3RunnerError(f"TCP/UDP 成功回执的 {key} 不配对")
    base_config_sha256 = _object_sha256(tcp_config.to_base_record())
    return PairValidation(
        schema_version="flow_probe_r2_ns3_pair_receipt_v1",
        physics_group_sha256=tcp_config.physics_group_sha256,
        status="pass",
        base_config_sha256=base_config_sha256,
        manifest_sha256=str(tcp_receipt["manifest_sha256"]),
        scenario_source_sha256=str(tcp_receipt["scenario_source_sha256"]),
        trace_contract_sha256=str(tcp_receipt["trace_contract_sha256"]),
        tcp_config_sha256=str(tcp_receipt["config_sha256"]),
        udp_config_sha256=str(udp_receipt["config_sha256"]),
        tcp_csv_sha256=tcp_validation.csv_sha256,
        udp_csv_sha256=udp_validation.csv_sha256,
        tcp_window_count=tcp_validation.window_count,
        udp_window_count=udp_validation.window_count,
        tcp_cwnd_coverage=tcp_validation.tcp_cwnd_coverage,
    )


def _config_bytes(config: ProtocolRunConfig) -> bytes:
    return (
        json.dumps(
            config.to_record(),
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("ascii")


def _program_arguments(config: ProtocolRunConfig, csv_path: Path) -> tuple[str, ...]:
    values: tuple[tuple[str, object], ...] = (
        ("physicsGroupSha256", config.physics_group_sha256),
        ("matrixConfigSha256", config.matrix_config_sha256),
        ("r2ContractSha256", config.r2_contract_sha256),
        ("split", config.split),
        ("runSeed", config.run_seed),
        ("transportFamily", config.transport_family),
        ("duration", config.duration_seconds),
        ("window", config.window_seconds),
        ("trafficMode", config.traffic_mode),
        ("binaryLabel", config.binary_label),
        ("arrivalModel", config.arrival_model),
        ("queueModel", config.queue_model),
        ("offeredLoadRatio", config.offered_load_ratio),
        ("initialCapacityMbps", config.initial_capacity_mbps),
        ("shiftedCapacityMbps", config.shifted_capacity_mbps),
        ("capacityChangeSeconds", config.capacity_change_time_seconds),
        ("accessDelayMs", config.access_delay_ms),
        ("bottleneckDelayMs", config.bottleneck_delay_ms),
        ("queueLimitPackets", config.queue_limit_packets),
        ("downstreamLossRate", config.downstream_loss_rate),
        ("senderCount", config.sender_count),
        ("benignSenderCount", config.benign_sender_count),
        ("attackSenderCount", config.attack_sender_count),
        ("totalOfferedLoadMbps", config.total_offered_load_mbps),
        ("packetSizeBytes", config.packet_size_bytes),
        ("burstOnSeconds", config.burst_on_seconds),
        ("burstOffSeconds", config.burst_off_seconds),
        ("output", csv_path),
    )
    return (PROGRAM_NAME, *(f"--{name}={value}" for name, value in values))


def _command(ns3_root: Path, config: ProtocolRunConfig, csv_path: Path) -> tuple[str, ...]:
    arguments = _program_arguments(config, csv_path)
    return (
        "env",
        "USER=ns3builder",
        str(ns3_root / "ns3"),
        "run",
        " ".join(shlex.quote(argument) for argument in arguments),
    )


def _artifacts_if_present(
    directory: Path,
    logical_root: Path,
    *,
    published_directory: Path | None = None,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for name in ("config.json", "result.csv", "result.csv.partial", "stdout.log", "stderr.log"):
        path = directory / name
        if path.is_file() and not path.is_symlink():
            artifact = _artifact(path, logical_root)
            if published_directory is not None:
                published_relative = published_directory.resolve().relative_to(
                    logical_root.resolve()
                )
                artifact = ArtifactRecord(
                    logical_path=(published_relative / name).as_posix(),
                    size_bytes=artifact.size_bytes,
                    sha256=artifact.sha256,
                )
            result.append(asdict(artifact))
    return result


def _archive_partial(partial_dir: Path, pair_dir: Path, logical_root: Path) -> None:
    if not partial_dir.exists() and not partial_dir.is_symlink():
        return
    if not partial_dir.is_dir() or partial_dir.is_symlink():
        raise R2NS3RunnerError(f"未完成运行路径不是普通目录：{partial_dir}")
    attempt = 1
    while (
        (pair_dir / f"{partial_dir.name}.failed-attempt-{attempt}").exists()
        or (pair_dir / f"{partial_dir.name}.failed-attempt-{attempt}").is_symlink()
    ):
        attempt += 1
    archive_dir = pair_dir / f"{partial_dir.name}.failed-attempt-{attempt}"
    receipt_path = partial_dir / "receipt.json"
    if receipt_path.is_symlink():
        raise R2NS3RunnerError("待归档失败运行回执不得是符号链接")
    if receipt_path.exists():
        receipt = dict(_read_json(receipt_path, "待归档失败运行回执"))
    else:
        receipt = {
            "schema_version": "flow_probe_r2_ns3_run_receipt_v1",
            "status": "interrupted",
            "recorded_at": _utc_now(),
        }
    receipt.update(
        {
            "archived_at": _utc_now(),
            "archived_from": partial_dir.relative_to(logical_root).as_posix(),
            "artifacts": _artifacts_if_present(
                partial_dir,
                logical_root,
                published_directory=archive_dir,
            ),
        }
    )
    _write_json_atomic(receipt_path, receipt)
    partial_dir.rename(archive_dir)


def _completed_run_matches(
    run_dir: Path,
    config: ProtocolRunConfig,
    *,
    manifest_sha256: str,
    scenario_sha256: str,
    trace_contract_sha256: str,
) -> bool:
    if not run_dir.is_dir() or run_dir.is_symlink():
        return False
    receipt_path = run_dir / "receipt.json"
    try:
        receipt = _read_json(receipt_path, "已完成运行回执")
    except R2NS3RunnerError:
        return False
    if receipt.get("status") != "pass" or receipt.get("validation_status") != "pass":
        return False
    expected_bindings = {
        "manifest_sha256": manifest_sha256,
        "scenario_source_sha256": scenario_sha256,
        "trace_contract_sha256": trace_contract_sha256,
        "config_sha256": hashlib.sha256(_config_bytes(config)).hexdigest(),
    }
    if any(receipt.get(key) != value for key, value in expected_bindings.items()):
        return False
    config_path = run_dir / "config.json"
    csv_path = run_dir / "result.csv"
    if not config_path.is_file() or not csv_path.is_file():
        return False
    if _file_sha256(config_path) != expected_bindings["config_sha256"]:
        return False
    return _file_sha256(csv_path) == receipt.get("csv_sha256")


def _run_one(
    ns3_root: Path,
    output_root: Path,
    config: ProtocolRunConfig,
    *,
    manifest_sha256: str,
    scenario_sha256: str,
    trace_contract_sha256: str,
    resume: bool,
) -> RunValidation:
    pairs_root = output_root / "pairs"
    if not pairs_root.is_dir() or pairs_root.is_symlink():
        raise R2NS3RunnerError("运行输出 pairs 路径不是普通目录")
    pair_dir = pairs_root / config.physics_group_sha256
    if pair_dir.exists() or pair_dir.is_symlink():
        if not pair_dir.is_dir() or pair_dir.is_symlink():
            raise R2NS3RunnerError("物理配对组路径不是普通目录")
    else:
        pair_dir.mkdir()
    final_dir = pair_dir / config.transport_family
    partial_dir = pair_dir / f".{config.transport_family}.partial"
    if final_dir.exists() or final_dir.is_symlink():
        if _completed_run_matches(
            final_dir,
            config,
            manifest_sha256=manifest_sha256,
            scenario_sha256=scenario_sha256,
            trace_contract_sha256=trace_contract_sha256,
        ):
            return _validate_csv(final_dir / "result.csv", config)
        raise R2NS3RunnerError(f"已发布运行目录哈希或验收状态不一致：{final_dir}")
    if partial_dir.exists() or partial_dir.is_symlink():
        if not resume:
            raise R2NS3RunnerError(f"未启用恢复但存在未完成运行：{partial_dir}")
        _archive_partial(partial_dir, pair_dir, output_root)
    partial_dir.mkdir()
    config_path = partial_dir / "config.json"
    config_path.write_bytes(_config_bytes(config))
    csv_partial = partial_dir / "result.csv.partial"
    stdout_path = partial_dir / "stdout.log"
    stderr_path = partial_dir / "stderr.log"
    command = _command(ns3_root, config, csv_partial)
    completed = subprocess.run(
        command,
        cwd=ns3_root,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")
    config_sha256 = _file_sha256(config_path)
    common_receipt = {
        "schema_version": "flow_probe_r2_ns3_run_receipt_v1",
        "physics_group_sha256": config.physics_group_sha256,
        "transport_family": config.transport_family,
        "manifest_sha256": manifest_sha256,
        "scenario_source_sha256": scenario_sha256,
        "trace_contract_sha256": trace_contract_sha256,
        "config_sha256": config_sha256,
        "returncode": completed.returncode,
        "recorded_at": _utc_now(),
    }
    if completed.returncode != 0:
        _write_json_atomic(
            partial_dir / "receipt.json",
            {
                **common_receipt,
                "status": "failed",
                "validation_status": "not_run",
                "artifacts": _artifacts_if_present(partial_dir, output_root),
            },
        )
        raise R2NS3RunnerError(
            f"配置 {config.physics_group_sha256}/{config.transport_family} "
            f"退出状态为 {completed.returncode}"
        )
    try:
        validation = _validate_csv(csv_partial, config)
    except Exception as error:
        _write_json_atomic(
            partial_dir / "receipt.json",
            {
                **common_receipt,
                "status": "failed",
                "validation_status": "failed",
                "error": str(error),
                "artifacts": _artifacts_if_present(partial_dir, output_root),
            },
        )
        raise
    csv_path = partial_dir / "result.csv"
    csv_partial.rename(csv_path)
    _write_json_atomic(
        partial_dir / "receipt.json",
        {
            **common_receipt,
            "status": "pass",
            "validation_status": "pass",
            "csv_sha256": validation.csv_sha256,
            "csv_size_bytes": validation.csv_size_bytes,
            "validation": validation.to_record(),
            "artifacts": _artifacts_if_present(
                partial_dir,
                output_root,
                published_directory=final_dir,
            ),
        },
    )
    partial_dir.rename(final_dir)
    return validation


def _run_attempt_directories(pair_dir: Path, transport_family: str) -> tuple[Path, ...]:
    if not pair_dir.is_dir() or pair_dir.is_symlink():
        return ()
    pattern = re.compile(
        rf"(?:{re.escape(transport_family)}|"
        rf"\.{re.escape(transport_family)}\.partial"
        rf"(?:\.failed-attempt-[1-9][0-9]*)?)"
    )
    directories = [
        child
        for child in pair_dir.iterdir()
        if pattern.fullmatch(child.name)
        and child.is_dir()
        and not child.is_symlink()
    ]
    return tuple(sorted(directories, key=lambda child: child.name))


def _runtime_artifacts_for_config(
    output_root: Path,
    config: ProtocolRunConfig,
) -> list[dict[str, object]]:
    pair_dir = output_root / "pairs" / config.physics_group_sha256
    artifacts: list[dict[str, object]] = []
    for directory in _run_attempt_directories(pair_dir, config.transport_family):
        for name in (
            "config.json",
            "result.csv",
            "result.csv.partial",
            "stdout.log",
            "stderr.log",
            "receipt.json",
        ):
            path = directory / name
            if path.is_file() and not path.is_symlink():
                artifacts.append(asdict(_artifact(path, output_root)))
    artifacts.sort(key=lambda item: str(item["logical_path"]))
    return artifacts


def _pair_receipt_artifacts(
    output_root: Path,
    pair_dir: Path,
) -> list[dict[str, object]]:
    if not pair_dir.is_dir() or pair_dir.is_symlink():
        return []
    pattern = re.compile(r"pair-receipt(?:\.failed-attempt-[1-9][0-9]*)?\.json")
    artifacts = [
        asdict(_artifact(path, output_root))
        for path in pair_dir.iterdir()
        if pattern.fullmatch(path.name)
        and path.is_file()
        and not path.is_symlink()
    ]
    artifacts.sort(key=lambda item: str(item["logical_path"]))
    return artifacts


def _write_pair_receipt(pair_dir: Path, record: Mapping[str, object]) -> None:
    path = pair_dir / "pair-receipt.json"
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise R2NS3RunnerError("既有配对回执不是普通文件")
        if _read_json(path, "既有配对回执") == record:
            return
        attempt = 1
        while (
            (pair_dir / f"pair-receipt.failed-attempt-{attempt}.json").exists()
            or (pair_dir / f"pair-receipt.failed-attempt-{attempt}.json").is_symlink()
        ):
            attempt += 1
        path.rename(pair_dir / f"pair-receipt.failed-attempt-{attempt}.json")
    _write_json_atomic(path, dict(record))


def _build_source_lock(
    output_root: Path,
    manifest: Path,
    scenario_source: Path,
    compiled_source: Path,
    trace_contract: NS3TraceContract,
    runs: Sequence[ProtocolRunConfig],
    statuses: Mapping[str, str],
) -> dict[str, object]:
    project_root = scenario_source.parent.parent
    entries = [
        asdict(_artifact(manifest, project_root)),
        asdict(
            _artifact(
                manifest.with_name("ns3-config-manifest.sha256"),
                project_root,
            )
        ),
        asdict(_artifact(scenario_source, project_root)),
        asdict(_artifact(compiled_source, compiled_source.parent.parent)),
    ]
    for artifact in trace_contract.source_artifacts:
        entries.append(asdict(artifact))
    planned_runs: list[dict[str, object]] = []
    pair_receipts: list[dict[str, object]] = []
    seen_pairs: set[str] = set()
    for config in runs:
        key = f"{config.physics_group_sha256}:{config.transport_family}"
        artifacts = _runtime_artifacts_for_config(output_root, config)
        entries.extend(artifacts)
        planned_runs.append(
            {
                "physics_group_sha256": config.physics_group_sha256,
                "transport_family": config.transport_family,
                "config_record_sha256": _object_sha256(config.to_record()),
                "status": statuses.get(key, "pending"),
                "artifacts": artifacts,
            }
        )
        if config.physics_group_sha256 not in seen_pairs:
            seen_pairs.add(config.physics_group_sha256)
            receipts = _pair_receipt_artifacts(
                output_root,
                output_root / "pairs" / config.physics_group_sha256,
            )
            pair_receipts.extend(receipts)
            entries.extend(receipts)
    unique_entries = {
        str(item["logical_path"]): item
        for item in entries
    }
    return {
        "schema_version": SOURCE_LOCK_SCHEMA_VERSION,
        "manifest_sha256": _file_sha256(manifest),
        "scenario_source_sha256": _file_sha256(scenario_source),
        "compiled_source_sha256": _file_sha256(compiled_source),
        "trace_contract_sha256": _object_sha256(trace_contract.to_record()),
        "entries": [unique_entries[key] for key in sorted(unique_entries)],
        "planned_runs": planned_runs,
        "pair_receipts": pair_receipts,
    }


def _persist_runtime_state(
    output_root: Path,
    state: Mapping[str, object],
    source_lock: Mapping[str, object],
) -> None:
    _write_json_atomic(output_root / "matrix-state.json", dict(state))
    _write_json_atomic(output_root / "source-lock.json", dict(source_lock))


def run_protocol_matrix(
    ns3_root: Path,
    manifest: Path,
    output_dir: Path,
    resume: bool,
) -> MatrixRunSummary:
    """按任务04顺序执行512条配置，并只跳过四类哈希均一致的成功运行。"""
    project_root = Path(__file__).resolve().parents[2]
    scenario_source = project_root / "ns3/r2_protocol_queue_scenario.cc"
    normalized_ns3 = Path(ns3_root).expanduser().resolve()
    normalized_manifest = Path(manifest).expanduser().resolve()
    normalized_output = Path(output_dir).expanduser().resolve()
    runs = _load_manifest(normalized_manifest)
    trace_contract = audit_ns3_trace_contract(normalized_ns3, scenario_source)
    trace_record = trace_contract.to_record()
    trace_contract_sha256 = _object_sha256(trace_record)
    scenario_sha256 = trace_contract.scenario_source_sha256
    compiled_source = normalized_ns3 / Path(*COMPILED_SOURCE_RELATIVE.parts)
    if not compiled_source.is_file() or compiled_source.is_symlink():
        raise R2NS3RunnerError(
            f"ns-3 scratch 场景缺失或是符号链接：{compiled_source}"
        )
    if _file_sha256(compiled_source) != scenario_sha256:
        raise R2NS3RunnerError("项目 C++ 场景与 ns-3 scratch 副本 SHA-256 不一致")
    if resume:
        if not normalized_output.is_dir() or normalized_output.is_symlink():
            raise R2NS3RunnerError("恢复模式要求既有普通输出目录")
        pairs_root = normalized_output / "pairs"
        if not pairs_root.is_dir() or pairs_root.is_symlink():
            raise R2NS3RunnerError("恢复模式要求既有普通 pairs 目录")
    elif normalized_output.exists() or normalized_output.is_symlink():
        raise R2NS3RunnerError(f"正式输出已存在且未启用恢复：{normalized_output}")
    else:
        normalized_output.mkdir(parents=True)
        (normalized_output / "pairs").mkdir()

    manifest_sha256 = _file_sha256(normalized_manifest)
    binding = {
        "schema_version": RUN_BINDING_SCHEMA_VERSION,
        "manifest_sha256": manifest_sha256,
        "scenario_source_sha256": scenario_sha256,
        "compiled_source_sha256": _file_sha256(compiled_source),
        "trace_contract_sha256": trace_contract_sha256,
        "matrix_config_sha256": EXPECTED_MATRIX_CONFIG_SHA256,
        "r2_contract_sha256": EXPECTED_R2_CONTRACT_SHA256,
        "program": PROGRAM_NAME,
        "protocol_run_count": 512,
        "base_configuration_count": 256,
    }
    binding_path = normalized_output / "run-binding.json"
    trace_path = normalized_output / "ns3-trace-contract.json"
    if resume:
        if _read_json(binding_path, "既有运行绑定") != binding:
            raise R2NS3RunnerError("恢复运行的输入、代码或 trace 合同发生变化")
        if _read_json(trace_path, "既有 trace 合同") != trace_record:
            raise R2NS3RunnerError("恢复运行的 trace 合同内容发生变化")
    else:
        _write_json_atomic(binding_path, binding)
        _write_json_atomic(trace_path, trace_record)

    statuses: dict[str, str] = {
        f"{run.physics_group_sha256}:{run.transport_family}": "pending" for run in runs
    }
    completed_count = 0
    skipped_count = 0
    failed_count = 0
    failed_pair_count = 0
    valid_pairs: set[str] = set()
    state: dict[str, object] = {
        "schema_version": "flow_probe_r2_ns3_matrix_state_v1",
        "status": "running",
        "stage": "initialized",
        "started_at": _utc_now(),
        "updated_at": _utc_now(),
        "completed_run_count": 0,
        "skipped_run_count": 0,
        "failed_run_count": 0,
        "failed_pair_count": 0,
        "valid_pair_count": 0,
        "active_run": None,
    }

    def persist() -> None:
        state["updated_at"] = _utc_now()
        source_lock = _build_source_lock(
            normalized_output,
            normalized_manifest,
            scenario_source,
            compiled_source,
            trace_contract,
            runs,
            statuses,
        )
        _persist_runtime_state(normalized_output, state, source_lock)

    persist()
    try:
        grouped_runs: dict[str, list[ProtocolRunConfig]] = {}
        for run in runs:
            grouped_runs.setdefault(run.physics_group_sha256, []).append(run)
        for group_id, pair_runs in grouped_runs.items():
            pair_dir = normalized_output / "pairs" / group_id
            pair_errors: list[dict[str, str]] = []
            for run in pair_runs:
                key = f"{run.physics_group_sha256}:{run.transport_family}"
                final_dir = pair_dir / run.transport_family
                was_complete = _completed_run_matches(
                    final_dir,
                    run,
                    manifest_sha256=manifest_sha256,
                    scenario_sha256=scenario_sha256,
                    trace_contract_sha256=trace_contract_sha256,
                )
                state["stage"] = "running"
                state["active_run"] = key
                statuses[key] = "running"
                persist()
                try:
                    _run_one(
                        normalized_ns3,
                        normalized_output,
                        run,
                        manifest_sha256=manifest_sha256,
                        scenario_sha256=scenario_sha256,
                        trace_contract_sha256=trace_contract_sha256,
                        resume=resume,
                    )
                except R2NS3RunnerError as error:
                    statuses[key] = "failed"
                    failed_count += 1
                    pair_errors.append(
                        {
                            "transport_family": run.transport_family,
                            "error": str(error),
                        }
                    )
                else:
                    statuses[key] = "pass"
                    if was_complete:
                        skipped_count += 1
                    else:
                        completed_count += 1
                state["completed_run_count"] = completed_count
                state["skipped_run_count"] = skipped_count
                state["failed_run_count"] = failed_count
                persist()

            if not pair_errors:
                try:
                    pair_validation = validate_protocol_pair(pair_dir, trace_contract)
                except R2NS3RunnerError as error:
                    pair_errors.append(
                        {
                            "transport_family": "PAIR",
                            "error": str(error),
                        }
                    )
                else:
                    _write_pair_receipt(pair_dir, pair_validation.to_record())
                    valid_pairs.add(group_id)
                    state["valid_pair_count"] = len(valid_pairs)

            if pair_errors:
                failed_pair_count += 1
                pair_artifacts: list[dict[str, object]] = []
                for run in pair_runs:
                    pair_artifacts.extend(
                        _runtime_artifacts_for_config(normalized_output, run)
                    )
                _write_pair_receipt(
                    pair_dir,
                    {
                        "schema_version": "flow_probe_r2_ns3_pair_receipt_v1",
                        "physics_group_sha256": group_id,
                        "status": "failed",
                        "recorded_at": _utc_now(),
                        "run_statuses": {
                            run.transport_family: statuses[
                                f"{run.physics_group_sha256}:{run.transport_family}"
                            ]
                            for run in pair_runs
                        },
                        "errors": pair_errors,
                        "artifacts": pair_artifacts,
                    },
                )
                state["failed_pair_count"] = failed_pair_count
                state["active_run"] = None
                persist()
                raise R2NS3RunnerError(
                    f"配对组 {group_id} 未通过；已保留 TCP/UDP 双侧回执并停止矩阵"
                )
            persist()
        if completed_count + skipped_count != 512 or len(valid_pairs) != 256:
            raise R2NS3RunnerError("矩阵结束时未形成512条成功运行和256个有效配对")
        state.update(
            {
                "status": "finished",
                "stage": "completed",
                "finished_at": _utc_now(),
                "active_run": None,
            }
        )
        persist()
    except BaseException as error:
        active = state.get("active_run")
        if (
            isinstance(active, str)
            and active in statuses
            and statuses[active] == "running"
        ):
            statuses[active] = "failed"
        state.update(
            {
                "status": "interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                "stage": "interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                "failed_run_count": failed_count,
                "failed_pair_count": failed_pair_count,
                "error": str(error),
                "finished_at": _utc_now(),
            }
        )
        persist()
        failed_summary = MatrixRunSummary(
            status=str(state["status"]),
            base_configuration_count=256,
            protocol_run_count=512,
            completed_run_count=completed_count,
            skipped_run_count=skipped_count,
            failed_run_count=failed_count,
            valid_pair_count=len(valid_pairs),
            manifest_sha256=manifest_sha256,
            scenario_source_sha256=scenario_sha256,
            trace_contract_sha256=trace_contract_sha256,
            source_lock_sha256=_file_sha256(normalized_output / "source-lock.json"),
        )
        _write_json_atomic(
            normalized_output / "matrix-summary.json",
            failed_summary.to_record(),
        )
        raise

    source_lock_path = normalized_output / "source-lock.json"
    summary = MatrixRunSummary(
        status="finished",
        base_configuration_count=256,
        protocol_run_count=512,
        completed_run_count=completed_count,
        skipped_run_count=skipped_count,
        failed_run_count=0,
        valid_pair_count=len(valid_pairs),
        manifest_sha256=manifest_sha256,
        scenario_source_sha256=scenario_sha256,
        trace_contract_sha256=trace_contract_sha256,
        source_lock_sha256=_file_sha256(source_lock_path),
    )
    _write_json_atomic(normalized_output / "matrix-summary.json", summary.to_record())
    return summary


def _resolve_under(root: Path, value: object, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise R2NS3RunnerError(f"{name} 必须是非空路径字符串")
    candidate = Path(value).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise R2NS3RunnerError(f"{name} 必须位于项目根内") from error
    return resolved


def _run_from_params(path: Path) -> MatrixRunSummary:
    params = _read_json(Path(path).expanduser().resolve(), "任务05受控参数")
    expected_keys = {
        "schema_version",
        "project_root",
        "ns3_root",
        "manifest_path",
        "scenario_source",
        "output_dir",
        "expected_manifest_sha256",
        "expected_scenario_source_sha256",
        "resume",
    }
    if set(params) != expected_keys:
        raise R2NS3RunnerError("任务05受控参数键集合不符")
    if params["schema_version"] != WRAPPER_SCHEMA_VERSION:
        raise R2NS3RunnerError("任务05受控参数模式版本不符")
    if not isinstance(params["project_root"], str):
        raise R2NS3RunnerError("project_root 必须是路径字符串")
    project_root = Path(params["project_root"]).expanduser().resolve()
    if project_root != Path(__file__).resolve().parents[2]:
        raise R2NS3RunnerError("受控参数 project_root 与当前安装代码根不一致")
    if not isinstance(params["ns3_root"], str):
        raise R2NS3RunnerError("ns3_root 必须是路径字符串")
    ns3_root = Path(params["ns3_root"]).expanduser().resolve()
    if ns3_root.as_posix() != "/root/autodl-tmp/thesis/ns3/ns-3.48":
        raise R2NS3RunnerError("正式 ns-3 根必须为固定服务器 ns-3.48 路径")
    manifest = _resolve_under(project_root, params["manifest_path"], "manifest_path")
    scenario = _resolve_under(project_root, params["scenario_source"], "scenario_source")
    output = _resolve_under(project_root, params["output_dir"], "output_dir")
    expected_manifest = project_root / "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl"
    expected_scenario = project_root / "ns3/r2_protocol_queue_scenario.cc"
    expected_output = project_root / "runs/ns3-data/r2-protocol-paired-v0"
    if manifest != expected_manifest or scenario != expected_scenario or output != expected_output:
        raise R2NS3RunnerError("任务05正式输入、场景或输出路径偏离冻结路径")
    if params["expected_manifest_sha256"] != EXPECTED_MANIFEST_SHA256:
        raise R2NS3RunnerError("受控参数中的任务04清单哈希不符")
    if not isinstance(params["expected_scenario_source_sha256"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", params["expected_scenario_source_sha256"]
    ):
        raise R2NS3RunnerError("受控参数中的 C++ 场景哈希格式不符")
    if _file_sha256(scenario) != params["expected_scenario_source_sha256"]:
        raise R2NS3RunnerError("受控参数中的 C++ 场景哈希与项目源码不一致")
    if not isinstance(params["resume"], bool):
        raise R2NS3RunnerError("resume 必须是布尔值")
    return run_protocol_matrix(ns3_root, manifest, output, params["resume"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 R2 ns-3 TCP/普通 UDP 配对矩阵")
    parser.add_argument("--params", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = _run_from_params(args.params)
    except (OSError, R2NS3RunnerError, subprocess.SubprocessError) as error:
        print(f"R2 ns-3 配对矩阵失败：{error}", file=os.sys.stderr)
        return 1
    print(json.dumps(summary.to_record(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
