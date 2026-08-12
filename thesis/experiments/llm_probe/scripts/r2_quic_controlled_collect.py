#!/usr/bin/env python3
"""采集带客户端 qlog 和双向 PCAP 的受控 QUIC 独立连接。"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ConnectionSpec:
    index: int
    implementation: str
    profile: dict[str, Any]
    seed: int
    payload: dict[str, Any]

    @property
    def connection_id(self) -> str:
        payload = json.dumps(
            {
                "implementation": self.implementation,
                "profile": self.profile,
                "seed": self.seed,
                "payload": self.payload,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("ascii")).hexdigest()[:24]

    @property
    def group_id(self) -> str:
        client_version = "1.3.0" if self.implementation == "aioquic" else "0.24.5"
        return (
            f"client={self.implementation}-{client_version}|role=client_under_test|"
            f"server=quiche-0.24.5|role=fixed_reference_server|profile={self.profile['id']}"
        )


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def scan_qlog_events(paths: list[Path]) -> dict[str, Any]:
    event_counts: dict[str, int] = {}
    ack_frames = 0
    pto_evidence = 0
    payload_decrypt_error = 0

    def visit(value: Any) -> None:
        nonlocal ack_frames, payload_decrypt_error, pto_evidence
        if isinstance(value, dict):
            name = value.get("name")
            if isinstance(name, str):
                event_counts[name] = event_counts.get(name, 0) + 1
                if "pto" in name.lower():
                    pto_evidence += 1
            frame_type = value.get("frame_type")
            if isinstance(frame_type, str) and frame_type.lower() == "ack":
                ack_frames += 1
            for key, child in value.items():
                if "pto" in str(key).lower() and child not in (None, False, 0, 0.0, "", "0"):
                    pto_evidence += 1
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and value == "payload_decrypt_error":
            payload_decrypt_error += 1

    for path in paths:
        raw = path.read_text(encoding="utf-8")
        try:
            visit(json.loads(raw))
            continue
        except json.JSONDecodeError:
            pass
        parsed_lines = 0
        for line in raw.splitlines():
            candidate = line.lstrip("\x1e").strip()
            if not candidate:
                continue
            try:
                visit(json.loads(candidate))
                parsed_lines += 1
            except json.JSONDecodeError:
                continue
        if parsed_lines == 0:
            raise RuntimeError(f"qlog 不是可识别的 JSON 或 JSON 文本序列：{path}")
    packet_events = sum(
        count
        for name, count in event_counts.items()
        if name.endswith("packet_sent") or name.endswith("packet_received")
    )
    metrics_events = sum(
        count for name, count in event_counts.items() if name.endswith("metrics_updated")
    )
    if packet_events == 0 or metrics_events == 0 or ack_frames == 0:
        raise RuntimeError(
            f"qlog 字段未闭合：packet={packet_events}, metrics={metrics_events}, ack={ack_frames}"
        )
    return {
        "event_counts": dict(sorted(event_counts.items())),
        "ack_frames": ack_frames,
        "packet_events": packet_events,
        "metrics_events": metrics_events,
        "pto_evidence": pto_evidence,
        "payload_decrypt_error": payload_decrypt_error,
    }


def run_checked(command: list[str], *, log_path: Path | None = None) -> None:
    if log_path is None:
        subprocess.run(command, check=True)
        return
    with log_path.open("ab") as log_stream:
        subprocess.run(command, stdout=log_stream, stderr=subprocess.STDOUT, check=True)


def build_specs(config: dict[str, Any], phase: str) -> list[ConnectionSpec]:
    implementations = [item["id"] for item in config["implementations"]]
    if phase == "field":
        profiles = config["field_profiles"]
        seeds = config["field_seeds"]
    else:
        explicit_profiles = config.get("formal_profiles")
        if explicit_profiles is not None:
            profiles = explicit_profiles
        else:
            grid = config["formal_grid"]
            profiles = []
            profile_index = 0
            for delay_ms, jitter_ms, loss_percent, rate_mbit in itertools.product(
                grid["delay_ms"], grid["jitter_ms"], grid["loss_percent"], grid["rate_mbit"]
            ):
                profile_index += 1
                profiles.append(
                    {
                        "id": f"p{profile_index:02d}",
                        "delay_ms": delay_ms,
                        "jitter_ms": jitter_ms,
                        "loss_percent": loss_percent,
                        "rate_mbit": rate_mbit,
                    }
                )
        seeds = config["formal_seeds"]
    combinations: Iterable[tuple[str, dict[str, Any], int, dict[str, Any]]]
    combinations = itertools.product(implementations, profiles, seeds, config["payloads"])
    return [
        ConnectionSpec(
            index=index, implementation=implementation, profile=profile, seed=seed, payload=payload
        )
        for index, (implementation, profile, seed, payload) in enumerate(combinations, start=1)
    ]


def free_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def ensure_payload(path: Path, size: int) -> None:
    if path.is_file() and path.stat().st_size == size:
        return
    temporary = path.with_suffix(path.suffix + ".partial")
    block = hashlib.sha256(path.name.encode("ascii")).digest() * 32768
    with temporary.open("wb") as stream:
        remaining = size
        while remaining:
            chunk = block[: min(len(block), remaining)]
            stream.write(chunk)
            remaining -= len(chunk)
    os.replace(temporary, path)


def derive_direction_seed(connection_id: str, seed: int, direction: str) -> int:
    material = f"{connection_id}|{seed}|{direction}".encode("ascii")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big") & ((1 << 63) - 1)


def wait_for_json(path: Path, process: subprocess.Popen[bytes], timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        if process.poll() is not None:
            raise RuntimeError(f"进程在生成就绪文件前退出：exit={process.returncode}")
        time.sleep(0.05)
    raise TimeoutError(f"等待就绪文件超时：{path}")


def stop_process(
    process: subprocess.Popen[bytes] | None, *, signal_number: int, timeout: float
) -> int:
    if process is None:
        return 255
    if process.poll() is None:
        process.send_signal(signal_number)
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        return process.wait()


def stop_process_with_receipt(
    process: subprocess.Popen[bytes] | None,
    *,
    signal_number: int,
    timeout: float,
) -> dict[str, Any]:
    if process is None:
        return {
            "controller_sent_signal": False,
            "controller_signal_sent_at": None,
            "poll_before_controller_signal": 255,
            "controller_signal": signal_number,
            "raw_exit": 255,
        }
    poll_before_signal = process.poll()
    signal_sent_at = None
    controller_sent_signal = poll_before_signal is None
    if controller_sent_signal:
        signal_sent_at = datetime.now(timezone.utc).isoformat()
        process.send_signal(signal_number)
    try:
        raw_exit = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        raw_exit = process.wait()
    return {
        "controller_sent_signal": controller_sent_signal,
        "controller_signal_sent_at": signal_sent_at,
        "poll_before_controller_signal": poll_before_signal,
        "controller_signal": signal_number,
        "raw_exit": raw_exit,
    }


def client_timeout_seconds(config: dict[str, Any]) -> float:
    timeout = float(config.get("client_timeout_seconds", 900))
    if timeout <= 0:
        raise ValueError("客户端硬超时必须为正数")
    return timeout


def proxy_queue_contract(
    config: dict[str, Any], implementation: str | None = None
) -> dict[str, Any]:
    network = config["network_contract"]
    deterministic = config.get("determinism_contract")
    schedule_mode = (
        str(deterministic["schedule_mode"])
        if isinstance(deterministic, dict)
        else "fixed_sequence_epoch_v1"
    )
    contract_version = (
        str(deterministic.get("contract_version", "")) if isinstance(deterministic, dict) else ""
    )
    if schedule_mode != "work_conserving_byte_service_delay_v1":
        return {
            "queue_capacity_unit": "packets",
            "queue_limit_packets": int(network["queue_limit_packets"]),
            "queue_capacity_bytes": None,
            "queue_margin_ratio": None,
            "queue_margin_max_bytes": None,
            "max_datagram_bytes": int(network.get("max_datagram_bytes", 65_535)),
            "serialization_rounding_tolerance_us_per_packet": int(
                network.get("serialization_rounding_tolerance_us_per_packet", 1)
            ),
        }
    max_by_implementation = network["max_datagram_bytes_by_implementation"]
    if max_by_implementation != {"aioquic": 1_200, "quiche": 1_350}:
        raise RuntimeError("v4 实现级最大数据报合同不符合冻结值")
    if implementation not in max_by_implementation:
        raise RuntimeError(f"v4 未知 QUIC 实现：{implementation}")
    contract = {
        "queue_capacity_unit": str(network["queue_capacity_unit"]),
        "queue_limit_packets": int(network.get("queue_limit_packets", 1000)),
        "queue_capacity_bytes": int(network["queue_capacity_bytes"]),
        "queue_margin_ratio": float(network["queue_margin_ratio"]),
        "queue_margin_max_bytes": int(network["queue_margin_max_bytes"]),
        "queue_margin_role": str(network["queue_margin_role"]),
        "max_datagram_bytes": int(max_by_implementation[implementation]),
        "udp_receive_buffer_bytes": int(network["udp_receive_buffer_bytes"]),
        "serialization_rounding_tolerance_us_per_packet": int(
            network["serialization_rounding_tolerance_us_per_packet"]
        ),
    }
    expected = {
        "queue_capacity_unit": "bytes",
        "queue_limit_packets": 1000,
        "queue_capacity_bytes": 2_097_152,
        "queue_margin_ratio": 0.8,
        "queue_margin_max_bytes": 1_677_721,
        "queue_margin_role": "diagnostic_only",
        "max_datagram_bytes": 1_200 if implementation == "aioquic" else 1_350,
        "udp_receive_buffer_bytes": 65_535,
        "serialization_rounding_tolerance_us_per_packet": 1,
    }
    if contract != expected:
        raise RuntimeError(f"v4 字节容量合同不符合冻结值：{contract}")
    if contract_version in {
        "flow_probe_r2_quic_four_tuple_contract_v7",
        "flow_probe_r2_quic_four_tuple_contract_v8",
    }:
        if network.get("directional_max_datagram_rule") != "actual_sender_implementation_v1":
            raise RuntimeError("v7/v8 方向级数据报规则不符合冻结值")
        reference_server = config.get("reference_server")
        if not isinstance(reference_server, dict):
            raise RuntimeError("v7/v8 固定参考服务端合同缺失")
        server_implementation = str(reference_server.get("implementation", ""))
        if server_implementation not in max_by_implementation:
            raise RuntimeError(f"v7/v8 未知参考服务端实现：{server_implementation}")
        contract["max_datagram_bytes_by_direction"] = {
            "client_to_server": int(max_by_implementation[implementation]),
            "server_to_client": int(max_by_implementation[server_implementation]),
        }
    if contract_version == "flow_probe_r2_quic_four_tuple_contract_v8":
        queue_drop_acceptance = network.get("queue_drop_acceptance")
        if queue_drop_acceptance != "deterministic_capacity_causal_replay_v1":
            raise RuntimeError("v8 队列丢包接受合同不符合冻结值")
        contract["queue_drop_acceptance"] = str(queue_drop_acceptance)
    return contract


def validate_work_conserving_direction(
    direction_stats: dict[str, Any],
    *,
    direction_name: str,
    loss_percent: float,
    is_v8: bool,
) -> None:
    zero_loss_requires_no_random_drop = float(loss_percent) == 0.0
    if (
        direction_stats["received_packets"]
        != direction_stats["scheduled_packets"]
        + direction_stats["random_drop_packets"]
        + direction_stats["queue_drop_packets"]
        or direction_stats["received_bytes"]
        != direction_stats["scheduled_bytes"]
        + direction_stats["random_drop_bytes"]
        + direction_stats["queue_drop_bytes"]
        or (
            zero_loss_requires_no_random_drop
            and direction_stats["random_drop_packets"] != 0
        )
        or (
            zero_loss_requires_no_random_drop
            and direction_stats["random_drop_bytes"] != 0
        )
        or (not is_v8 and direction_stats["queue_drop_packets"] != 0)
        or (not is_v8 and direction_stats["queue_drop_bytes"] != 0)
        or direction_stats["send_error_bytes"] != 0
        or direction_stats["waiting_bytes_at_shutdown"] != 0
        or direction_stats["in_service_bytes_at_shutdown"] != 0
        or direction_stats["service_backlog_bytes_at_shutdown"] != 0
        or direction_stats["delay_inflight_bytes_at_shutdown"] != 0
    ):
        raise RuntimeError(f"代理 v4 字节守恒或关停门禁失败：{direction_name}")


def fixed_endpoint_contract(config: dict[str, Any], spec: ConnectionSpec) -> dict[str, Any]:
    deterministic = config.get("determinism_contract")
    if isinstance(deterministic, dict):
        client = deterministic["client_endpoint"]
        proxy_listen = deterministic["proxy_listen_endpoint"]
        proxy_upstream = deterministic["proxy_upstream_endpoint"]
        server = deterministic["reference_server_endpoint"]
        return {
            "contract_version": str(deterministic["contract_version"]),
            "connection_id": spec.connection_id,
            "schedule_mode": str(deterministic["schedule_mode"]),
            "client_to_proxy": {
                "source_host": str(client["host"]),
                "source_port": int(client["port"]),
                "destination_host": str(proxy_listen["host"]),
                "destination_port": int(proxy_listen["port"]),
            },
            "proxy_to_server": {
                "source_host": str(proxy_upstream["host"]),
                "source_port": int(proxy_upstream["port"]),
                "destination_host": str(server["host"]),
                "destination_port": int(server["port"]),
            },
        }

    proxy_host = str(config["network_contract"]["proxy_host"])
    proxy_port = int(config["network_contract"]["proxy_port_base"]) + spec.index
    server_host = str(config["network_contract"]["reference_server_host"])
    server_port = int(config["reference_server"]["listen_port"])
    return {
        "contract_version": "flow_probe_r2_quic_four_tuple_contract_legacy_v1",
        "connection_id": spec.connection_id,
        "schedule_mode": "fixed_sequence_epoch_v1",
        "client_to_proxy": {
            "source_host": proxy_host,
            "source_port": 21000 + spec.index,
            "destination_host": proxy_host,
            "destination_port": proxy_port,
        },
        "proxy_to_server": {
            "source_host": proxy_host,
            "source_port": 22000 + spec.index,
            "destination_host": server_host,
            "destination_port": server_port,
        },
    }


def endpoint_pair(contract: dict[str, Any], leg: str, side: str) -> list[Any]:
    return [contract[leg][f"{side}_host"], contract[leg][f"{side}_port"]]


def assert_udp_ports_exclusively_bindable(
    contract: dict[str, Any], *, stage: str
) -> dict[str, Any]:
    endpoints = [
        {"role": "client", "endpoint": endpoint_pair(contract, "client_to_proxy", "source")},
        {
            "role": "proxy_listen",
            "endpoint": endpoint_pair(contract, "client_to_proxy", "destination"),
        },
        {
            "role": "proxy_upstream",
            "endpoint": endpoint_pair(contract, "proxy_to_server", "source"),
        },
        {
            "role": "reference_server",
            "endpoint": endpoint_pair(contract, "proxy_to_server", "destination"),
        },
    ]
    probes: list[socket.socket] = []
    try:
        for item in endpoints:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probes.append(probe)
            host, port = item["endpoint"]
            probe.bind((str(host), int(port)))
    except OSError as error:
        raise RuntimeError(
            f"{stage} UDP 端口不可独占绑定：{item['role']}={item['endpoint']}"
        ) from error
    finally:
        for probe in reversed(probes):
            probe.close()
    return {
        "stage": stage,
        "exclusive_bind_succeeded": True,
        "endpoints": endpoints,
    }


def client_command(
    *,
    spec: ConnectionSpec,
    tools_root: Path,
    qlog_dir: Path,
    response_dir: Path,
    server_ip: str,
    port: int,
    local_port: int,
    payload_name: str,
) -> tuple[list[str], dict[str, str]]:
    url = f"https://{server_ip}:{port}/{payload_name}"
    environment = os.environ.copy()
    if spec.implementation == "aioquic":
        python = tools_root / "aioquic-venv/bin/python"
        client = tools_root / "sources/aioquic-1.3.0/examples/http3_client.py"
        command = [
            str(python),
            str(client),
            "--insecure",
            "--local-port",
            str(local_port),
            "--quic-log",
            str(qlog_dir),
            "--output-dir",
            str(response_dir),
            url,
        ]
    else:
        client = tools_root / "sources/quiche-0.24.5/target/release/quiche-client"
        environment["QLOGDIR"] = str(qlog_dir)
        command = [
            str(client),
            "--no-verify",
            "--source-port",
            str(local_port),
            "--dump-responses",
            str(response_dir),
            url,
        ]
    return command, environment


def collect_connection(
    *,
    phase: str,
    project_root: Path,
    spec: ConnectionSpec,
    config: dict[str, Any],
    collection_config_sha256: str,
    tools_root: Path,
    output_root: Path,
    payload_root: Path,
    certificate: Path,
    private_key: Path,
    server_binary: Path,
) -> dict[str, Any]:
    connection_root = output_root / "connections" / spec.connection_id
    finished_state = connection_root / "status.json"
    if finished_state.is_file():
        state = json.loads(finished_state.read_text(encoding="utf-8"))
        if state.get("status") == "finished":
            return state
        raise RuntimeError(f"连接目录已有非完成状态，禁止自动覆盖：{connection_root}")

    connection_root.mkdir(parents=True, exist_ok=False)
    qlog_dir = connection_root / "qlog"
    response_dir = connection_root / "response"
    qlog_dir.mkdir()
    response_dir.mkdir()
    pcap_path = connection_root / "deployment-observation.pcap"
    client_log = connection_root / "client.log"
    capture_log = connection_root / "capture.log"
    server_log = connection_root / "reference-server.log"
    impairment_path = connection_root / "impairment-config.json"
    four_tuple_path = connection_root / "four-tuple-contract.json"
    endpoint_path = connection_root / "endpoint-contract.json"
    proxy_ready_path = connection_root / "proxy-ready.json"
    proxy_stats_path = connection_root / "proxy-stats.json"
    proxy_event_path = connection_root / "proxy-events.jsonl"
    proxy_log = connection_root / "proxy.log"
    exit_path = connection_root / "exit-code.json"

    tcpdump = tools_root / "apt-root/usr/bin/tcpdump"
    proxy_program = project_root / "scripts/r2_quic_udp_proxy.py"
    proxy_python = project_root / ".venv/bin/python"
    four_tuple_contract = fixed_endpoint_contract(config, spec)
    client_endpoint = endpoint_pair(four_tuple_contract, "client_to_proxy", "source")
    proxy_endpoint = endpoint_pair(four_tuple_contract, "client_to_proxy", "destination")
    upstream_endpoint = endpoint_pair(four_tuple_contract, "proxy_to_server", "source")
    server_endpoint = endpoint_pair(four_tuple_contract, "proxy_to_server", "destination")
    schedule_mode = str(four_tuple_contract["schedule_mode"])
    contract_version = str(four_tuple_contract["contract_version"])
    is_v8 = contract_version == "flow_probe_r2_quic_four_tuple_contract_v8"
    timeout_seconds = client_timeout_seconds(config)
    profile = dict(spec.profile)
    profile["seed"] = spec.seed
    profile["jitter_ms"] = float(profile.get("jitter_ms", 0.0))
    queue_contract = proxy_queue_contract(config, spec.implementation)
    queue_limit = queue_contract["queue_limit_packets"]
    direction_seeds = {
        direction: derive_direction_seed(spec.connection_id, spec.seed, direction)
        for direction in ("client_to_server", "server_to_client")
    }
    deterministic = config.get("determinism_contract")
    if isinstance(deterministic, dict) and phase == "field":
        direction_seeds_by_target = deterministic.get("direction_seeds_by_target_index")
        frozen_direction_seeds = (
            direction_seeds_by_target[str(spec.index)]
            if isinstance(direction_seeds_by_target, dict)
            else deterministic["direction_seeds"]
        )
        expected_direction_seeds = {
            name: int(value) for name, value in frozen_direction_seeds.items()
        }
        if direction_seeds != expected_direction_seeds:
            raise RuntimeError(
                f"方向种子不符合冻结合同：{direction_seeds} != {expected_direction_seeds}"
            )
    atomic_json(four_tuple_path, four_tuple_contract)
    four_tuple_contract_sha256 = sha256_file(four_tuple_path)
    impairment_payload = {
        "schema_version": "flow_probe_r2_quic_userspace_impairment_v1",
        "backend": "deterministic_userspace_udp_proxy",
        "implementation_layer": "userspace",
        "connection_id": spec.connection_id,
        "group_id": spec.group_id,
        "collection_config_sha256": collection_config_sha256,
        "profile": profile,
        "queue_limit_packets": queue_limit,
        "queue_capacity_unit": queue_contract["queue_capacity_unit"],
        "queue_capacity_bytes": queue_contract["queue_capacity_bytes"],
        "queue_margin_ratio": queue_contract["queue_margin_ratio"],
        "queue_margin_max_bytes": queue_contract["queue_margin_max_bytes"],
        "queue_margin_role": queue_contract.get("queue_margin_role"),
        "max_datagram_bytes": queue_contract["max_datagram_bytes"],
        "udp_receive_buffer_bytes": queue_contract.get("udp_receive_buffer_bytes"),
        "serialization_rounding_tolerance_us_per_packet": queue_contract[
            "serialization_rounding_tolerance_us_per_packet"
        ],
        "directions": ["client_to_server", "server_to_client"],
        "direction_seeds": direction_seeds,
        "schedule_mode": schedule_mode,
        "four_tuple_contract_sha256": four_tuple_contract_sha256,
        "jitter_distribution": "deterministic_uniform_symmetric",
        "rate_model": config["network_contract"]["rate_model"],
        "propagation_model": config["network_contract"].get("propagation_model"),
        "kernel_netem_truth": False,
        "network_namespace_truth": False,
        "kernel_queue_truth": False,
    }
    directional_maximums = queue_contract.get("max_datagram_bytes_by_direction")
    if isinstance(directional_maximums, dict):
        impairment_payload["max_datagram_bytes_by_direction"] = directional_maximums
    if queue_contract.get("queue_drop_acceptance") is not None:
        impairment_payload["queue_drop_acceptance"] = queue_contract["queue_drop_acceptance"]
    atomic_json(impairment_path, impairment_payload)
    impairment_config_sha256 = sha256_file(impairment_path)
    atomic_json(
        finished_state,
        {
            "status": "prepared",
            "connection_id": spec.connection_id,
            "group_id": spec.group_id,
            "client_timeout_seconds": timeout_seconds,
            "four_tuple_contract_sha256": four_tuple_contract_sha256,
        },
    )

    client_process: subprocess.Popen[bytes] | None = None
    capture_process: subprocess.Popen[bytes] | None = None
    proxy_process: subprocess.Popen[bytes] | None = None
    server_process: subprocess.Popen[bytes] | None = None
    started_at = time.time()
    client_exit = 255
    capture_exit = 255
    proxy_exit = 255
    server_exit = 255
    server_raw_exit = 255
    server_stop_receipt: dict[str, Any] = {
        "controller_sent_signal": False,
        "controller_signal_sent_at": None,
        "poll_before_controller_signal": 255,
        "controller_signal": signal.SIGTERM,
        "raw_exit": 255,
    }
    client_natural_completion = False
    proxy_ready: dict[str, Any] | None = None
    port_availability_before: dict[str, Any] | None = None
    port_availability_after: dict[str, Any] | None = None
    endpoint_contract: dict[str, Any] = {
        "schema_version": "flow_probe_r2_quic_endpoint_contract_v2",
        "connection_id": spec.connection_id,
        "four_tuple_contract_sha256": four_tuple_contract_sha256,
        "schedule_mode": schedule_mode,
        "expected_client_endpoint": client_endpoint,
        "expected_proxy_listen_endpoint": proxy_endpoint,
        "expected_proxy_upstream_endpoint": upstream_endpoint,
        "expected_reference_server_endpoint": server_endpoint,
        "observed_client_endpoint": None,
        "observed_proxy_listen_endpoint": None,
        "observed_proxy_upstream_endpoint": None,
        "observed_reference_server_endpoint": None,
        "client_pid": None,
        "capture_pid": None,
        "proxy_pid": None,
        "reference_server_pid": None,
        "capture_interface": "lo",
        "capture_filter": f"udp port {proxy_endpoint[1]}",
        "capture_leg": "client_proxy_only",
        "port_availability_before": None,
        "port_availability_after": None,
    }
    atomic_json(endpoint_path, endpoint_contract)

    try:
        process_error: BaseException | None = None
        cleanup_errors: list[str] = []
        try:
            port_availability_before = assert_udp_ports_exclusively_bindable(
                four_tuple_contract, stage="before_connection"
            )
            endpoint_contract["port_availability_before"] = port_availability_before

            server_command = [
                str(server_binary),
                "--listen",
                f"{server_endpoint[0]}:{server_endpoint[1]}",
                "--cert",
                str(certificate),
                "--key",
                str(private_key),
                "--root",
                str(payload_root),
            ]
            with server_log.open("ab") as server_stream:
                server_process = subprocess.Popen(
                    server_command,
                    stdout=server_stream,
                    stderr=subprocess.STDOUT,
                )
            endpoint_contract["reference_server_pid"] = server_process.pid
            time.sleep(1.0)
            if server_process.poll() is not None:
                raise RuntimeError(f"单连接参考服务端启动失败：{server_process.returncode}")

            proxy_command = [
                str(proxy_python),
                str(proxy_program),
                "--listen-host",
                str(proxy_endpoint[0]),
                "--listen-port",
                str(proxy_endpoint[1]),
                "--upstream-bind-host",
                str(upstream_endpoint[0]),
                "--upstream-bind-port",
                str(upstream_endpoint[1]),
                "--upstream-host",
                str(server_endpoint[0]),
                "--upstream-port",
                str(server_endpoint[1]),
                "--expected-client-host",
                str(client_endpoint[0]),
                "--expected-client-port",
                str(client_endpoint[1]),
                "--schedule-mode",
                schedule_mode,
                "--delay-ms",
                str(profile["delay_ms"]),
                "--jitter-ms",
                str(profile["jitter_ms"]),
                "--loss-percent",
                str(profile["loss_percent"]),
                "--rate-mbit",
                str(profile["rate_mbit"]),
                "--queue-limit-packets",
                str(queue_limit),
                "--client-to-server-seed",
                str(direction_seeds["client_to_server"]),
                "--server-to-client-seed",
                str(direction_seeds["server_to_client"]),
                "--config-sha256",
                impairment_config_sha256,
                "--ready-file",
                str(proxy_ready_path),
                "--stats-file",
                str(proxy_stats_path),
                "--event-log",
                str(proxy_event_path),
            ]
            if schedule_mode == "work_conserving_byte_service_delay_v1":
                proxy_command.extend(
                    [
                        "--queue-capacity-bytes",
                        str(queue_contract["queue_capacity_bytes"]),
                        "--queue-margin-ratio",
                        str(queue_contract["queue_margin_ratio"]),
                        "--queue-margin-max-bytes",
                        str(queue_contract["queue_margin_max_bytes"]),
                        "--max-datagram-bytes",
                        str(queue_contract["max_datagram_bytes"]),
                        "--udp-receive-buffer-bytes",
                        str(queue_contract["udp_receive_buffer_bytes"]),
                        "--serialization-rounding-tolerance-us-per-packet",
                        str(queue_contract["serialization_rounding_tolerance_us_per_packet"]),
                    ]
                )
                if isinstance(directional_maximums, dict):
                    proxy_command.extend(
                        [
                            "--client-to-server-max-datagram-bytes",
                            str(directional_maximums["client_to_server"]),
                            "--server-to-client-max-datagram-bytes",
                            str(directional_maximums["server_to_client"]),
                        ]
                    )
                if queue_contract.get("queue_drop_acceptance") is not None:
                    proxy_command.extend(
                        [
                            "--queue-drop-acceptance",
                            str(queue_contract["queue_drop_acceptance"]),
                        ]
                    )
            with proxy_log.open("ab") as proxy_stream:
                proxy_process = subprocess.Popen(
                    proxy_command, stdout=proxy_stream, stderr=subprocess.STDOUT
                )
            endpoint_contract["proxy_pid"] = proxy_process.pid
            proxy_ready = wait_for_json(proxy_ready_path, proxy_process, timeout=10.0)
            if (
                proxy_ready.get("status") != "ready"
                or proxy_ready.get("config_sha256") != impairment_config_sha256
                or proxy_ready.get("schedule_mode") != schedule_mode
                or proxy_ready.get("listen_endpoint") != proxy_endpoint
                or proxy_ready.get("upstream_local_endpoint") != upstream_endpoint
                or proxy_ready.get("upstream_server_endpoint") != server_endpoint
                or proxy_ready.get("expected_client_endpoint") != client_endpoint
            ):
                raise RuntimeError("用户态 UDP 代理就绪合同不符合冻结四元组")
            if schedule_mode == "work_conserving_byte_service_delay_v1" and (
                proxy_ready.get("queue_capacity_unit") != "bytes"
                or proxy_ready.get("queue_capacity_bytes") != queue_contract["queue_capacity_bytes"]
                or proxy_ready.get("queue_margin_ratio") != queue_contract["queue_margin_ratio"]
                or proxy_ready.get("queue_margin_max_bytes")
                != queue_contract["queue_margin_max_bytes"]
                or proxy_ready.get("queue_margin_role") != "diagnostic_only"
                or proxy_ready.get("max_datagram_bytes") != queue_contract["max_datagram_bytes"]
                or proxy_ready.get("udp_receive_buffer_bytes")
                != queue_contract["udp_receive_buffer_bytes"]
            ):
                raise RuntimeError("用户态 UDP 代理就绪合同不符合 v4 字节容量")
            if isinstance(directional_maximums, dict) and (
                proxy_ready.get("max_datagram_bytes_by_direction") != directional_maximums
            ):
                raise RuntimeError("用户态 UDP 代理就绪合同不符合 v7 方向级数据报上限")
            if is_v8 and (
                proxy_ready.get("queue_drop_acceptance")
                != queue_contract["queue_drop_acceptance"]
            ):
                raise RuntimeError("用户态 UDP 代理就绪合同不符合 v8 队列丢包合同")
            endpoint_contract["observed_proxy_listen_endpoint"] = proxy_ready["listen_endpoint"]
            endpoint_contract["observed_proxy_upstream_endpoint"] = proxy_ready[
                "upstream_local_endpoint"
            ]
            endpoint_contract["observed_reference_server_endpoint"] = proxy_ready[
                "upstream_server_endpoint"
            ]

            with capture_log.open("ab") as capture_stream:
                capture_process = subprocess.Popen(
                    [
                        str(tcpdump),
                        "-Z",
                        "root",
                        "-i",
                        "lo",
                        "-s",
                        "0",
                        "-U",
                        "-w",
                        str(pcap_path),
                        "udp",
                        "port",
                        str(proxy_endpoint[1]),
                    ],
                    stdout=capture_stream,
                    stderr=subprocess.STDOUT,
                )
            endpoint_contract["capture_pid"] = capture_process.pid
            time.sleep(0.5)
            if capture_process.poll() is not None:
                raise RuntimeError(f"loopback 抓包进程提前退出：{capture_process.returncode}")

            payload_name = f"payload-{spec.payload['id']}.bin"
            command, environment = client_command(
                spec=spec,
                tools_root=tools_root,
                qlog_dir=qlog_dir,
                response_dir=response_dir,
                server_ip=str(proxy_endpoint[0]),
                port=int(proxy_endpoint[1]),
                local_port=int(client_endpoint[1]),
                payload_name=payload_name,
            )
            with client_log.open("ab") as client_stream:
                client_process = subprocess.Popen(
                    command,
                    stdout=client_stream,
                    stderr=subprocess.STDOUT,
                    env=environment,
                )
                endpoint_contract["client_pid"] = client_process.pid
                atomic_json(endpoint_path, endpoint_contract)
                client_exit = client_process.wait(timeout=timeout_seconds)
            client_natural_completion = True
            if client_exit != 0:
                raise RuntimeError(f"客户端自然退出码非零：{client_exit}")
            time.sleep(float(config["network_contract"]["post_client_drain_seconds"]))
        except BaseException as error:
            process_error = error
        finally:
            try:
                if client_process is not None:
                    if client_process.poll() is None:
                        client_exit = stop_process(
                            client_process,
                            signal_number=signal.SIGTERM,
                            timeout=30,
                        )
                    elif client_exit == 255:
                        client_exit = client_process.wait()
            except BaseException as error:
                cleanup_errors.append(f"client:{type(error).__name__}:{error}")

            try:
                proxy_exit = stop_process(proxy_process, signal_number=signal.SIGINT, timeout=30)
            except BaseException as error:
                cleanup_errors.append(f"proxy:{type(error).__name__}:{error}")

            try:
                capture_exit = stop_process(
                    capture_process, signal_number=signal.SIGINT, timeout=30
                )
            except BaseException as error:
                cleanup_errors.append(f"capture:{type(error).__name__}:{error}")

            try:
                server_stop_receipt = stop_process_with_receipt(
                    server_process, signal_number=signal.SIGTERM, timeout=30
                )
                server_raw_exit = int(server_stop_receipt["raw_exit"])
                server_exit = server_raw_exit
            except BaseException as error:
                cleanup_errors.append(f"server:{type(error).__name__}:{error}")

            try:
                port_availability_after = assert_udp_ports_exclusively_bindable(
                    four_tuple_contract, stage="after_connection"
                )
                endpoint_contract["port_availability_after"] = port_availability_after
            except BaseException as error:
                cleanup_errors.append(f"ports:{type(error).__name__}:{error}")

            if proxy_stats_path.is_file():
                try:
                    observed_proxy_stats = json.loads(proxy_stats_path.read_text(encoding="utf-8"))
                    endpoint_contract["observed_client_endpoint"] = observed_proxy_stats.get(
                        "observed_client_endpoint"
                    )
                except (OSError, json.JSONDecodeError) as error:
                    cleanup_errors.append(f"proxy_stats:{type(error).__name__}:{error}")
            try:
                atomic_json(endpoint_path, endpoint_contract)
            except BaseException as error:
                cleanup_errors.append(f"endpoint:{type(error).__name__}:{error}")
            atomic_json(
                exit_path,
                {
                    "client_exit": client_exit,
                    "capture_exit": capture_exit,
                    "proxy_exit": proxy_exit,
                    "server_exit": server_exit,
                    "server_raw_exit": server_raw_exit,
                    "server_exit_policy": "raw_zero_or_controller_sigterm_receipt_v1",
                    "server_stop_receipt": server_stop_receipt,
                },
            )

        if process_error is not None:
            if cleanup_errors:
                raise RuntimeError(
                    f"连接运行失败且清理不闭合：{process_error}; " + "; ".join(cleanup_errors)
                ) from process_error
            raise process_error
        if cleanup_errors:
            raise RuntimeError("连接清理不闭合：" + "; ".join(cleanup_errors))
        if not client_natural_completion:
            raise RuntimeError("客户端没有自然完成")
        controlled_server_sigterm = (
            server_raw_exit in (-signal.SIGTERM, 128 + signal.SIGTERM)
            and server_stop_receipt.get("controller_sent_signal") is True
            and server_stop_receipt.get("controller_signal") == signal.SIGTERM
            and server_stop_receipt.get("poll_before_controller_signal") is None
            and isinstance(server_stop_receipt.get("controller_signal_sent_at"), str)
        )
        if (
            client_exit != 0
            or capture_exit != 0
            or proxy_exit != 0
            or (server_raw_exit != 0 and not controlled_server_sigterm)
        ):
            raise RuntimeError(
                "连接命令失败："
                f"client={client_exit}, capture={capture_exit}, "
                f"proxy={proxy_exit}, server={server_exit}"
            )

        qlogs = sorted(
            path for path in qlog_dir.iterdir() if path.is_file() and path.stat().st_size > 0
        )
        if not qlogs:
            raise RuntimeError("客户端没有生成非空 qlog")
        qlog_audit = scan_qlog_events(qlogs)
        if not pcap_path.is_file() or pcap_path.stat().st_size <= 24:
            raise RuntimeError("PCAP 缺失或为空")
        if not proxy_event_path.is_file() or proxy_event_path.stat().st_size == 0:
            raise RuntimeError("用户态 UDP 代理事件日志缺失或为空")
        if not proxy_stats_path.is_file():
            raise RuntimeError("用户态 UDP 代理统计缺失")
        proxy_stats = json.loads(proxy_stats_path.read_text(encoding="utf-8"))
        if (
            proxy_stats.get("status") != "finished"
            or proxy_stats.get("config_sha256") != impairment_config_sha256
            or proxy_stats.get("schedule_mode") != schedule_mode
            or proxy_stats.get("scheduled_packets_at_shutdown") != 0
            or proxy_stats.get("observed_client_endpoint") != client_endpoint
            or proxy_stats.get("listen_endpoint") != proxy_endpoint
            or proxy_stats.get("upstream_local_endpoint") != upstream_endpoint
            or proxy_stats.get("upstream_server_endpoint") != server_endpoint
        ):
            raise RuntimeError("用户态 UDP 代理统计与冻结四元组合同不闭合")
        if is_v8 and (
            "contract_error" not in proxy_stats or proxy_stats["contract_error"] is not None
        ):
            raise RuntimeError("用户态 UDP 代理统计缺少显式空合同错误")
        if schedule_mode == "work_conserving_byte_service_delay_v1":
            parameters = proxy_stats.get("parameters", {})
            expected_parameters = {
                "queue_capacity_unit": "bytes",
                "queue_capacity_bytes": queue_contract["queue_capacity_bytes"],
                "queue_margin_ratio": queue_contract["queue_margin_ratio"],
                "queue_margin_max_bytes": queue_contract["queue_margin_max_bytes"],
                "max_datagram_bytes": queue_contract["max_datagram_bytes"],
                "udp_receive_buffer_bytes": queue_contract["udp_receive_buffer_bytes"],
                "rate_bits_per_second": round(profile["rate_mbit"] * 1_000_000),
                "delay_us": round(profile["delay_ms"] * 1000),
            }
            if any(parameters.get(name) != value for name, value in expected_parameters.items()):
                raise RuntimeError("用户态 UDP 代理统计不符合 v4 冻结参数")
            if isinstance(directional_maximums, dict) and (
                parameters.get("max_datagram_bytes_by_direction") != directional_maximums
            ):
                raise RuntimeError("用户态 UDP 代理统计不符合 v7 方向级数据报上限")
            if is_v8 and (
                parameters.get("queue_drop_acceptance")
                != queue_contract["queue_drop_acceptance"]
            ):
                raise RuntimeError("用户态 UDP 代理统计不符合 v8 队列丢包合同")
        for direction_name in ("client_to_server", "server_to_client"):
            direction_stats = proxy_stats["directions"][direction_name]
            if (
                direction_stats["received_packets"] <= 0
                or direction_stats["forwarded_packets"] <= 0
                or direction_stats["send_error_packets"] != 0
                or direction_stats["queued_packets_at_shutdown"] != 0
                or direction_stats["scheduled_packets"] != direction_stats["forwarded_packets"]
            ):
                raise RuntimeError(f"代理方向统计不闭合：{direction_name}")
            if isinstance(directional_maximums, dict) and (
                direction_stats.get("max_datagram_bytes") != directional_maximums[direction_name]
            ):
                raise RuntimeError(f"代理方向上限不符合 v7 合同：{direction_name}")
            if schedule_mode == "work_conserving_byte_service_delay_v1":
                validate_work_conserving_direction(
                    direction_stats,
                    direction_name=direction_name,
                    loss_percent=float(profile["loss_percent"]),
                    is_v8=is_v8,
                )
        if phase == "field" and is_v8 and spec.implementation == "aioquic" and spec.index == 12:
            server_to_client_stats = proxy_stats["directions"]["server_to_client"]
            if (
                server_to_client_stats["queue_drop_packets"] <= 0
                or server_to_client_stats["queue_drop_bytes"] <= 0
            ):
                raise RuntimeError("v8 aioquic 固定目标缺少服务端到客户端容量因果丢包")
        response_candidates = [path for path in response_dir.iterdir() if path.is_file()]
        if (
            len(response_candidates) != 1
            or response_candidates[0].stat().st_size != spec.payload["bytes"]
        ):
            raise RuntimeError(f"{spec.implementation} 响应负载大小不符合合同")
        if (
            endpoint_contract["observed_client_endpoint"] != client_endpoint
            or endpoint_contract["observed_proxy_upstream_endpoint"] != upstream_endpoint
            or port_availability_before is None
            or port_availability_after is None
        ):
            raise RuntimeError("运行态端点观察或端口独占收据不符合冻结合同")
        endpoint_contract["collection_config_sha256"] = collection_config_sha256
        endpoint_contract["impairment_config_sha256"] = impairment_config_sha256
        atomic_json(endpoint_path, endpoint_contract)
        response_sha256 = sha256_file(response_candidates[0])

        artifacts = []
        for path in [
            pcap_path,
            client_log,
            capture_log,
            server_log,
            impairment_path,
            four_tuple_path,
            endpoint_path,
            proxy_ready_path,
            proxy_stats_path,
            proxy_event_path,
            proxy_log,
            exit_path,
            *qlogs,
            *response_candidates,
        ]:
            artifacts.append(
                {
                    "path": path.relative_to(connection_root).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
        state = {
            "schema_version": "flow_probe_r2_quic_connection_state_v1",
            "status": "finished",
            "connection_id": spec.connection_id,
            "group_id": spec.group_id,
            "implementation": spec.implementation,
            "reference_server": config["reference_server"],
            "profile": profile,
            "payload": spec.payload,
            "seed": spec.seed,
            "collection_config_sha256": collection_config_sha256,
            "impairment_config_sha256": impairment_config_sha256,
            "four_tuple_contract_sha256": four_tuple_contract_sha256,
            "direction_seeds": direction_seeds,
            "schedule_mode": schedule_mode,
            "fixed_endpoints": {
                "client": client_endpoint,
                "proxy_listen": proxy_endpoint,
                "proxy_upstream": upstream_endpoint,
                "reference_server": server_endpoint,
            },
            "client_timeout_seconds": timeout_seconds,
            "client_natural_completion": client_natural_completion,
            "exit_codes": {
                "client_exit": client_exit,
                "capture_exit": capture_exit,
                "proxy_exit": proxy_exit,
                "server_exit": server_exit,
                "server_raw_exit": server_raw_exit,
            },
            "server_stop_receipt": server_stop_receipt,
            "response": {
                "path": response_candidates[0].relative_to(connection_root).as_posix(),
                "bytes": response_candidates[0].stat().st_size,
                "sha256": response_sha256,
            },
            "impairment_backend": "deterministic_userspace_udp_proxy",
            "userspace_queue_and_drop_audit_truth": True,
            "kernel_netem_truth": False,
            "network_namespace_truth": False,
            "kernel_queue_truth": False,
            "client_qlog_training_truth": True,
            "pcap_deployment_observation": True,
            "qlog_field_audit": qlog_audit,
            "pto_observed": True if qlog_audit["pto_evidence"] > 0 else None,
            "pto_observed_mask": qlog_audit["pto_evidence"] > 0,
            "final_test_visible": False,
            "elapsed_seconds": round(time.time() - started_at, 3),
            "artifacts": artifacts,
        }
        atomic_json(finished_state, state)
        return state
    except BaseException as error:
        atomic_json(
            finished_state,
            {
                "status": "failed",
                "connection_id": spec.connection_id,
                "group_id": spec.group_id,
                "error_type": type(error).__name__,
                "error": str(error),
                "collection_config_sha256": collection_config_sha256,
                "impairment_config_sha256": impairment_config_sha256,
                "four_tuple_contract_sha256": four_tuple_contract_sha256,
                "client_timeout_seconds": timeout_seconds,
                "client_natural_completion": client_natural_completion,
                "exit_codes": {
                    "client_exit": client_exit,
                    "capture_exit": capture_exit,
                    "proxy_exit": proxy_exit,
                    "server_exit": server_exit,
                    "server_raw_exit": server_raw_exit,
                },
                "server_stop_receipt": server_stop_receipt,
                "elapsed_seconds": round(time.time() - started_at, 3),
            },
        )
        raise


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--phase", choices=("field", "formal"), required=True)
    parser.add_argument("--stop-after", type=int)
    parser.add_argument("--only-index", type=int)
    parser.add_argument("--output-root", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    project_root = args.project_root.resolve()
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    collection_config_sha256 = sha256_file(config_path)
    tools_root = project_root / config["tool_root"]
    apt_library_path = str(tools_root / "apt-root/usr/lib/x86_64-linux-gnu")
    inherited_library_path = os.environ.get("LD_LIBRARY_PATH")
    os.environ["LD_LIBRARY_PATH"] = (
        f"{apt_library_path}:{inherited_library_path}"
        if inherited_library_path
        else apt_library_path
    )
    if args.output_root is None:
        output_root = project_root / config[f"{args.phase}_output_root"]
    else:
        output_root = args.output_root
        if not output_root.is_absolute():
            output_root = project_root / output_root
        output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "connections").mkdir(exist_ok=True)
    minimum_free = config["storage"][f"minimum_free_bytes_before_{args.phase}"]
    if free_bytes(project_root) < minimum_free:
        raise RuntimeError("磁盘可用空间低于当前阶段硬门禁")

    matrix_specs = build_specs(config, args.phase)
    default_expected = 40 if args.phase == "field" else 600
    matrix_contract = config.get("matrix_contract", {})
    expected = int(matrix_contract.get(f"{args.phase}_expected_connections", default_expected))
    if len(matrix_specs) != expected:
        raise RuntimeError(f"连接矩阵规模错误：{len(matrix_specs)} != {expected}")
    deterministic = config.get("determinism_contract")
    if isinstance(deterministic, dict) and args.phase == "field":
        gate_runs = deterministic.get("gate_runs")
        if gate_runs is None:
            allowed_targets = [int(deterministic["target_connection_index"])]
        else:
            if not isinstance(gate_runs, list) or len(gate_runs) != 3:
                raise RuntimeError("确定性门禁运行身份必须恰好三份")
            allowed_targets = [int(item["target_connection_index"]) for item in gate_runs]
            run_ids = [str(item["run_id"]) for item in gate_runs]
            if len(set(run_ids)) != 3 or {
                int(item["target_connection_index"]) for item in gate_runs
            } != {12, 32}:
                raise RuntimeError("确定性门禁必须使用三个唯一身份并覆盖 aioquic/quiche")
        if args.only_index not in allowed_targets:
            raise RuntimeError("定向连接不属于冻结的三轮门禁")
        target = matrix_specs[int(args.only_index) - 1]
        frozen_target = (
            target.profile["id"],
            target.profile["delay_ms"],
            target.profile.get("jitter_ms", 0.0),
            target.profile["loss_percent"],
            target.profile["rate_mbit"],
            target.seed,
            target.payload["id"],
            target.payload["bytes"],
        )
        expected_target = ("p03", 50, 0.0, 0.0, 20, 43, "bulk", 67108864)
        if frozen_target != expected_target or target.implementation not in {"aioquic", "quiche"}:
            raise RuntimeError(f"确定性修复目标不符合冻结科学参数：{frozen_target}")
        schedule_mode = str(deterministic["schedule_mode"])
        if args.phase != "field" or float(config.get("client_timeout_seconds", 0)) != 240:
            raise RuntimeError("确定性修复配置只允许 field 与 240 秒硬超时")
        queue_contract = proxy_queue_contract(config, target.implementation)
        if schedule_mode == "fixed_sequence_epoch_v1":
            if int(queue_contract["queue_limit_packets"]) != 1000:
                raise RuntimeError("v3 确定性修复必须使用 1000 包上限")
        elif schedule_mode == "work_conserving_byte_service_delay_v1":
            implementations = [str(item["implementation"]) for item in gate_runs]
            indices = [int(item["target_connection_index"]) for item in gate_runs]
            if implementations != ["aioquic", "quiche", "aioquic"] or indices != [
                12,
                32,
                12,
            ]:
                raise RuntimeError("v4 三轮身份必须为 aioquic/quiche/aioquic 与 12/32/12")
        else:
            raise RuntimeError(f"未知确定性调度模式：{schedule_mode}")
    if args.only_index is None:
        specs = matrix_specs
    else:
        if not 1 <= args.only_index <= expected:
            raise ValueError(f"定向连接序号超出矩阵：{args.only_index}")
        specs = [matrix_specs[args.only_index - 1]]
    run_expected = len(specs)
    print(
        f"阶段={args.phase}，计划连接={run_expected}，矩阵连接={expected}，输出={output_root}",
        flush=True,
    )
    shutil.copy2(config_path, output_root / "collection-config.json")
    shutil.copy2(tools_root / "versions.txt", output_root / "tool-versions.txt")
    payload_root = output_root / "reference-server-root"
    payload_root.mkdir(exist_ok=True)
    for payload in config["payloads"]:
        ensure_payload(payload_root / f"payload-{payload['id']}.bin", payload["bytes"])

    certificate = output_root / "reference-server.crt"
    private_key = output_root / "reference-server.key"
    if not certificate.is_file() or not private_key.is_file():
        run_checked(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-keyout",
                str(private_key),
                "-out",
                str(certificate),
                "-days",
                "2",
                "-subj",
                "/CN=r2-quic-reference.invalid",
            ]
        )

    server_binary = tools_root / "sources/quiche-0.24.5/target/release/quiche-server"
    completed = 0
    for spec in specs:
        if args.stop_after is not None and completed >= args.stop_after:
            break
        available_bytes = free_bytes(project_root)
        if args.phase == "formal" and available_bytes < minimum_free:
            atomic_json(
                output_root / "run-state.json",
                {
                    "status": "storage_gate_stopped",
                    "phase": args.phase,
                    "finished_connections": completed,
                    "expected_connections": run_expected,
                    "matrix_expected_connections": expected,
                    "available_bytes": available_bytes,
                    "minimum_free_bytes": minimum_free,
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                },
            )
            raise RuntimeError("磁盘可用空间低于正式阶段硬门禁，队列已停止")
        collect_connection(
            phase=args.phase,
            project_root=project_root,
            spec=spec,
            config=config,
            collection_config_sha256=collection_config_sha256,
            tools_root=tools_root,
            output_root=output_root,
            payload_root=payload_root,
            certificate=certificate,
            private_key=private_key,
            server_binary=server_binary,
        )
        completed += 1
        print(
            f"连接完成 {completed}/{run_expected}: {spec.connection_id} "
            f"{spec.implementation} {spec.profile['id']} seed={spec.seed} payload={spec.payload['id']}",
            flush=True,
        )
        atomic_json(
            output_root / "run-state.json",
            {
                "status": "running",
                "phase": args.phase,
                "completed_in_this_process": completed,
                "expected_connections": run_expected,
                "matrix_expected_connections": expected,
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            },
        )

    finished_count = 0
    for state_path in (output_root / "connections").glob("*/status.json"):
        state = json.loads(state_path.read_text(encoding="utf-8"))
        finished_count += int(state.get("status") == "finished")
    final_status = "finished" if finished_count == run_expected else "interrupted"
    atomic_json(
        output_root / "run-state.json",
        {
            "status": final_status,
            "phase": args.phase,
            "finished_connections": finished_count,
            "expected_connections": run_expected,
            "matrix_expected_connections": expected,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
