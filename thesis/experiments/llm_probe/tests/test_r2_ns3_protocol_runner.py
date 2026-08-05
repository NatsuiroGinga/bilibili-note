"""任务05运行器的后置回归合同。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from flow_probe.r2_ns3_protocol_matrix import ProtocolRunConfig
from flow_probe.r2_ns3_protocol_runner import (
    CSV_COLUMNS,
    CSV_SCHEMA_VERSION,
    EXPECTED_MANIFEST_SHA256,
    EXPECTED_MATRIX_CONFIG_SHA256,
    EXPECTED_R2_CONTRACT_SHA256,
    R2NS3RunnerError,
    _artifacts_if_present,
    _load_manifest,
    _validate_csv,
    audit_ns3_trace_contract,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_ROOT / "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl"


def test_real_task04_manifest_remains_exact_and_paired() -> None:
    runs = _load_manifest(MANIFEST)
    assert len(runs) == 512
    assert {item.transport_family for item in runs} == {"TCP", "UDP"}
    assert EXPECTED_MANIFEST_SHA256 == "d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111"
    assert EXPECTED_MATRIX_CONFIG_SHA256 == (
        "0adcb49e52a1df156eddf4a3d01dfd51d00fa57752bcc0d04189073ace2edeeb"
    )
    assert EXPECTED_R2_CONTRACT_SHA256 == (
        "aa390129e239aa59d1c6963471e1268498a16740a5f11a916f489fa6a7292566"
    )


def test_csv_contract_separates_tcp_and_udp_state() -> None:
    assert CSV_COLUMNS[-17:] == (
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


def test_trace_audit_rejects_missing_ns3_launcher(tmp_path: Path) -> None:
    scenario = tmp_path / "scenario.cc"
    scenario.write_text("TcpNewReno::GetTypeId()", encoding="utf-8")
    with pytest.raises(R2NS3RunnerError, match="启动器"):
        audit_ns3_trace_contract(tmp_path / "ns-3.48", scenario)


def _write_trace_audit_fixture(tmp_path: Path, ppp_header_bytes: int = 2) -> Path:
    root = tmp_path / "ns-3.48"
    files = {
        "VERSION": "3.48\n",
        "src/internet/model/tcp-socket-base.cc": "CongestionWindow m_cWndTrace\n",
        "src/internet/model/tcp-socket-base.h": "\n",
        "src/traffic-control/model/queue-disc.cc": (
            "Enqueue Dequeue DropBeforeEnqueue DropAfterDequeue\n"
        ),
        "src/traffic-control/model/queue-disc.h": "\n",
        "src/internet/model/ipv4-queue-disc-item.cc": (
            "Ipv4QueueDiscItem::GetSize m_header.GetSerializedSize() "
            "GetPacket() ->GetSize()\n"
        ),
        "src/internet/model/ipv4-queue-disc-item.h": "\n",
        "src/point-to-point/model/point-to-point-net-device.cc": (
            "PhyRxDrop MacTxDrop\n"
            "bool PointToPointNetDevice::ProcessHeader(Ptr<Packet> p, uint16_t& param) {\n"
            "  PppHeader ppp; p->RemoveHeader(ppp); return true;\n"
            "}\n"
            "void PointToPointNetDevice::Receive(Ptr<Packet> packet) {\n"
            "  uint16_t protocol = 0;\n"
            "  if (m_receiveErrorModel && m_receiveErrorModel->IsCorrupt(packet)) {\n"
            "    m_phyRxDropTrace(packet);\n"
            "  } else {\n"
            "    ProcessHeader(packet, protocol);\n"
            "  }\n"
            "}\n"
        ),
        "src/point-to-point/model/point-to-point-net-device.h": "\n",
        "src/point-to-point/model/ppp-header.cc": (
            "uint32_t PppHeader::GetSerializedSize() const { "
            f"return {ppp_header_bytes}; }}\n"
        ),
        "src/point-to-point/model/ppp-header.h": "\n",
        "src/network/model/packet.cc": (
            "uint32_t Packet::PeekHeader(Header& header) const {\n"
            "  uint32_t deserialized = header.Deserialize(m_buffer.Begin());\n"
            "  return deserialized;\n"
            "}\n"
        ),
        "src/network/model/packet.h": "\n",
        "src/internet/model/ipv4-l3-protocol.cc": "LocalDeliver\n",
        "src/internet/model/ipv4-l3-protocol.h": "\n",
    }
    for relative, payload in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    launcher = root / "ns3"
    launcher.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
    launcher.chmod(0o755)
    return root


def test_trace_audit_binds_pre_remove_ppp_header_semantics(tmp_path: Path) -> None:
    root = _write_trace_audit_fixture(tmp_path)
    scenario = PROJECT_ROOT / "ns3/r2_protocol_queue_scenario.cc"
    contract = audit_ns3_trace_contract(root, scenario)
    assert contract.schema_version == "flow_probe_r2_ns3_trace_contract_v2"
    assert (
        contract.downstream_loss_l3_semantics
        == "PhyRxDrop_packet_minus_verified_PppHeader_2_bytes"
    )
    artifact_paths = {item.logical_path for item in contract.source_artifacts}
    assert "src/point-to-point/model/ppp-header.cc" in artifact_paths
    assert "src/network/model/packet.cc" in artifact_paths


def test_trace_audit_rejects_changed_ppp_header_size(tmp_path: Path) -> None:
    root = _write_trace_audit_fixture(tmp_path, ppp_header_bytes=4)
    scenario = PROJECT_ROOT / "ns3/r2_protocol_queue_scenario.cc"
    with pytest.raises(R2NS3RunnerError, match="PPP 头声明长度为 2 字节"):
        audit_ns3_trace_contract(root, scenario)


def test_manifest_records_do_not_gain_runtime_fields() -> None:
    first = json.loads(MANIFEST.read_text(encoding="ascii").splitlines()[0])
    assert "command" not in first
    assert "output" not in first
    assert "scenario_path" not in first


def _bps(value: float) -> int:
    return int(value * 1_000_000.0 + 0.5)


def _synthetic_row(config: ProtocolRunConfig, index: int) -> dict[str, str]:
    start = index * config.window_seconds
    end = (index + 1) * config.window_seconds
    initial_capacity = _bps(config.initial_capacity_mbps)
    shifted_capacity = _bps(config.shifted_capacity_mbps)
    change = config.capacity_change_time_seconds
    capacity_start = shifted_capacity if start >= change - 1e-8 else initial_capacity
    capacity_end = shifted_capacity if end >= change - 1e-8 else initial_capacity
    before_change = max(0.0, min(end, change) - start)
    after_change = max(0.0, end - max(start, change))
    capacity_integral = (
        initial_capacity * before_change + shifted_capacity * after_change
    ) / 8.0
    row = {column: "0" for column in CSV_COLUMNS}
    row.update(
        {
            "schema_version": CSV_SCHEMA_VERSION,
            "physics_group_sha256": config.physics_group_sha256,
            "matrix_config_sha256": config.matrix_config_sha256,
            "r2_contract_sha256": config.r2_contract_sha256,
            "split": config.split,
            "run_seed": str(config.run_seed),
            "transport_family": config.transport_family,
            "window_index": str(index),
            "window_start_s": f"{start:.9f}",
            "window_end_s": f"{end:.9f}",
            "truth_traffic_mode": config.traffic_mode,
            "truth_binary_label": str(config.binary_label),
            "truth_arrival_model": config.arrival_model,
            "truth_queue_model": config.queue_model,
            "truth_ns3_version": config.ns3_version,
            "truth_tcp_congestion_control": config.tcp_congestion_control,
            "truth_offered_load_ratio": str(config.offered_load_ratio),
            "truth_initial_capacity_bps": str(initial_capacity),
            "truth_shifted_capacity_bps": str(shifted_capacity),
            "truth_capacity_change_s": str(change),
            "truth_access_delay_ms": str(config.access_delay_ms),
            "truth_bottleneck_delay_ms": str(config.bottleneck_delay_ms),
            "truth_queue_limit_packets": str(config.queue_limit_packets),
            "truth_downstream_loss_rate": str(config.downstream_loss_rate),
            "truth_sender_count": str(config.sender_count),
            "truth_benign_sender_count": str(config.benign_sender_count),
            "truth_attack_sender_count": str(config.attack_sender_count),
            "truth_total_offered_load_bps": str(_bps(config.total_offered_load_mbps)),
            "truth_packet_size_app_payload_bytes": str(config.packet_size_bytes),
            "truth_capacity_start_bps": str(capacity_start),
            "truth_capacity_end_bps": str(capacity_end),
            "truth_capacity_integral_link_bytes": f"{capacity_integral:.9f}",
        }
    )
    if config.transport_family == "TCP":
        row.update(
            {
                "truth_tcp_cwnd_applicable": "1",
                "truth_tcp_cwnd_observed": "1",
                "truth_tcp_cwnd_trace_connected_senders": str(config.sender_count),
                "truth_tcp_cwnd_observed_senders": str(config.sender_count),
                "truth_tcp_cwnd_mean_bytes": "12000.000000000",
                "truth_tcp_cwnd_min_bytes": "12000",
                "truth_tcp_cwnd_max_bytes": "12000",
                "truth_tcp_cwnd_trace_name": "CongestionWindow",
                "truth_tcp_cwnd_aggregation": "time_weighted_mean_over_observed_senders",
                "truth_udp_applicable": "0",
            }
        )
    else:
        row.update(
            {
                "truth_tcp_cwnd_applicable": "0",
                "truth_tcp_cwnd_observed": "0",
                "truth_tcp_cwnd_trace_name": "NONE",
                "truth_tcp_cwnd_aggregation": "not_applicable",
                "truth_udp_applicable": "1",
                "truth_udp_target_rate_bps": str(_bps(config.total_offered_load_mbps)),
                "truth_udp_burst_mode": str(int(config.arrival_model == "bursty")),
                "truth_udp_burst_active": "0",
            }
        )
    return row


def _write_synthetic_csv(
    path: Path,
    config: ProtocolRunConfig,
    row_count: int = 120,
) -> None:
    rows = [_synthetic_row(config, index) for index in range(row_count)]
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize("transport_family", ["TCP", "UDP"])
def test_synthetic_csv_satisfies_strict_runtime_contract(
    tmp_path: Path,
    transport_family: str,
) -> None:
    config = next(
        item
        for item in _load_manifest(MANIFEST)
        if item.transport_family == transport_family
    )
    path = tmp_path / f"{transport_family}.csv"
    _write_synthetic_csv(path, config)
    validation = _validate_csv(path, config)
    assert validation.window_count == 120
    assert validation.residual_violation_count == 0


def test_csv_validation_recomputes_queue_residual(tmp_path: Path) -> None:
    config = next(item for item in _load_manifest(MANIFEST) if item.transport_family == "UDP")
    path = tmp_path / "tampered.csv"
    rows = [_synthetic_row(config, index) for index in range(120)]
    rows[0]["truth_queue_end_packets"] = "1"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(R2NS3RunnerError, match="守恒残差"):
        _validate_csv(path, config)


def test_csv_validation_rejects_119_windows(tmp_path: Path) -> None:
    config = next(item for item in _load_manifest(MANIFEST) if item.transport_family == "UDP")
    path = tmp_path / "short.csv"
    _write_synthetic_csv(path, config, row_count=119)
    with pytest.raises(R2NS3RunnerError, match="120"):
        _validate_csv(path, config)


def test_udp_csv_rejects_tcp_cwnd_state(tmp_path: Path) -> None:
    config = next(item for item in _load_manifest(MANIFEST) if item.transport_family == "UDP")
    path = tmp_path / "udp-with-cwnd.csv"
    rows = [_synthetic_row(config, index) for index in range(120)]
    rows[0]["truth_tcp_cwnd_applicable"] = "1"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(R2NS3RunnerError, match="适用掩码"):
        _validate_csv(path, config)


def test_tcp_csv_requires_cwnd_window_coverage(tmp_path: Path) -> None:
    config = next(item for item in _load_manifest(MANIFEST) if item.transport_family == "TCP")
    path = tmp_path / "tcp-without-cwnd.csv"
    rows = [_synthetic_row(config, index) for index in range(120)]
    for row in rows:
        row["truth_tcp_cwnd_observed"] = "0"
        row["truth_tcp_cwnd_observed_senders"] = "0"
        row["truth_tcp_cwnd_mean_bytes"] = "0.000000000"
        row["truth_tcp_cwnd_min_bytes"] = "0"
        row["truth_tcp_cwnd_max_bytes"] = "0"
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    with pytest.raises(R2NS3RunnerError, match="覆盖率"):
        _validate_csv(path, config)


def test_success_receipt_artifacts_use_published_paths(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    partial = output_root / "pairs" / ("a" * 64) / ".TCP.partial"
    final = partial.parent / "TCP"
    partial.mkdir(parents=True)
    (partial / "config.json").write_text("{}\n", encoding="utf-8")
    (partial / "result.csv").write_text("header\n", encoding="utf-8")
    artifacts = _artifacts_if_present(
        partial,
        output_root,
        published_directory=final,
    )
    assert {item["logical_path"] for item in artifacts} == {
        f"pairs/{'a' * 64}/TCP/config.json",
        f"pairs/{'a' * 64}/TCP/result.csv",
    }
