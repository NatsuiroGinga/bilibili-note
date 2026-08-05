#!/usr/bin/env python3
"""以确定性用户态 UDP 代理实施双向 QUIC 链路障碍。"""

from __future__ import annotations

import argparse
import heapq
import json
import os
import random
import selectors
import signal
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


@dataclass
class DirectionState:
    name: str
    seed: int
    delay_seconds: float
    jitter_seconds: float
    loss_probability: float
    rate_bits_per_second: float
    queue_limit_packets: int
    random_source: random.Random = field(init=False)
    packet_sequence: int = 0
    schedule_epoch_monotonic: float | None = None
    cumulative_serialization_seconds: float = 0.0
    previous_frozen_send_offset_seconds: float = 0.0
    queued_packets: int = 0
    peak_queue_packets: int = 0
    received_packets: int = 0
    received_bytes: int = 0
    scheduled_packets: int = 0
    scheduled_bytes: int = 0
    forwarded_packets: int = 0
    forwarded_bytes: int = 0
    random_drop_packets: int = 0
    queue_drop_packets: int = 0
    send_error_packets: int = 0

    def __post_init__(self) -> None:
        self.random_source = random.Random(self.seed)

    def as_dict(self, started_monotonic: float) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "packet_sequence": self.packet_sequence,
            "final_packet_sequence": self.packet_sequence,
            "schedule_epoch_offset_us": (
                round((self.schedule_epoch_monotonic - started_monotonic) * 1_000_000)
                if self.schedule_epoch_monotonic is not None
                else None
            ),
            "cumulative_serialization_us": round(
                self.cumulative_serialization_seconds * 1_000_000
            ),
            "final_frozen_send_offset_us": round(
                self.previous_frozen_send_offset_seconds * 1_000_000
            ),
            "received_packets": self.received_packets,
            "received_bytes": self.received_bytes,
            "scheduled_packets": self.scheduled_packets,
            "scheduled_bytes": self.scheduled_bytes,
            "forwarded_packets": self.forwarded_packets,
            "forwarded_bytes": self.forwarded_bytes,
            "random_drop_packets": self.random_drop_packets,
            "queue_drop_packets": self.queue_drop_packets,
            "send_error_packets": self.send_error_packets,
            "peak_queue_packets": self.peak_queue_packets,
            "queued_packets_at_shutdown": self.queued_packets,
        }


@dataclass(order=True)
class ScheduledDatagram:
    release_time: float
    sequence: int
    direction: str = field(compare=False)
    packet_sequence: int = field(compare=False)
    schedule_epoch_offset_us: int = field(compare=False)
    frozen_send_offset_us: int = field(compare=False)
    payload: bytes = field(compare=False)
    destination: tuple[str, int] | None = field(compare=False)


class DeterministicUdpProxy:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.started_monotonic = time.monotonic()
        self.started_wall = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        self.last_activity = self.started_monotonic
        self.running = True
        self.exit_reason = "signal"
        self.failed = False
        self.contract_error: dict[str, Any] | None = None
        self.sequence = 0
        self.client_endpoint: tuple[str, int] | None = None
        self.schedule: list[ScheduledDatagram] = []
        self.selector = selectors.DefaultSelector()
        self.event_stream = args.event_log.open("x", encoding="utf-8", buffering=1024 * 1024)

        self.downstream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.upstream = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for endpoint in (self.downstream, self.upstream):
            endpoint.setblocking(False)
            endpoint.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)
            endpoint.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16 * 1024 * 1024)
        self.downstream.bind((args.listen_host, args.listen_port))
        self.upstream.bind((args.upstream_bind_host, args.upstream_bind_port))
        self.upstream.connect((args.upstream_host, args.upstream_port))
        self.selector.register(self.downstream, selectors.EVENT_READ, "client_to_server")
        self.selector.register(self.upstream, selectors.EVENT_READ, "server_to_client")

        common = {
            "delay_seconds": args.delay_ms / 1000.0,
            "jitter_seconds": args.jitter_ms / 1000.0,
            "loss_probability": args.loss_percent / 100.0,
            "rate_bits_per_second": args.rate_mbit * 1_000_000.0,
            "queue_limit_packets": args.queue_limit_packets,
        }
        self.directions = {
            "client_to_server": DirectionState(
                name="client_to_server", seed=args.client_to_server_seed, **common
            ),
            "server_to_client": DirectionState(
                name="server_to_client", seed=args.server_to_client_seed, **common
            ),
        }

    def offset_microseconds(self, timestamp: float) -> int:
        return round((timestamp - self.started_monotonic) * 1_000_000)

    def write_event(self, payload: dict[str, Any]) -> None:
        self.event_stream.write(
            json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            + "\n"
        )

    def schedule_datagram(
        self,
        *,
        direction_name: str,
        payload: bytes,
        destination: tuple[str, int] | None,
    ) -> None:
        now = time.monotonic()
        self.last_activity = now
        direction = self.directions[direction_name]
        direction.received_packets += 1
        direction.received_bytes += len(payload)
        direction.packet_sequence += 1
        packet_sequence = direction.packet_sequence
        if direction.schedule_epoch_monotonic is None:
            direction.schedule_epoch_monotonic = now
        schedule_epoch = direction.schedule_epoch_monotonic
        schedule_epoch_offset_us = self.offset_microseconds(schedule_epoch)

        loss_draw = direction.random_source.random()
        jitter_seconds = 0.0
        if direction.jitter_seconds > 0.0:
            jitter_seconds = direction.random_source.uniform(
                -direction.jitter_seconds, direction.jitter_seconds
            )
        serialization_seconds = len(payload) * 8.0 / direction.rate_bits_per_second
        direction.cumulative_serialization_seconds += serialization_seconds
        candidate_offset = max(
            0.0,
            direction.delay_seconds
            + direction.cumulative_serialization_seconds
            + jitter_seconds,
        )
        frozen_send_offset = max(
            direction.previous_frozen_send_offset_seconds,
            candidate_offset,
        )
        direction.previous_frozen_send_offset_seconds = frozen_send_offset
        frozen_send_offset_us = round(frozen_send_offset * 1_000_000)
        release_time = schedule_epoch + frozen_send_offset
        event_contract = {
            "packet_sequence": packet_sequence,
            "schedule_epoch_offset_us": schedule_epoch_offset_us,
            "frozen_send_offset_us": frozen_send_offset_us,
            "actual_forwarding_lag_us": None,
        }

        if loss_draw < direction.loss_probability:
            direction.random_drop_packets += 1
            self.sequence += 1
            self.write_event(
                {
                    "sequence": self.sequence,
                    "direction": direction_name,
                    "action": "dropped",
                    "reason": "deterministic_random_loss",
                    "bytes": len(payload),
                    "arrival_offset_us": self.offset_microseconds(now),
                    "queue_depth_packets": direction.queued_packets,
                    **event_contract,
                }
            )
            return

        if direction.queued_packets >= direction.queue_limit_packets:
            direction.queue_drop_packets += 1
            self.sequence += 1
            self.write_event(
                {
                    "sequence": self.sequence,
                    "direction": direction_name,
                    "action": "dropped",
                    "reason": "userspace_queue_limit",
                    "bytes": len(payload),
                    "arrival_offset_us": self.offset_microseconds(now),
                    "queue_depth_packets": direction.queued_packets,
                    **event_contract,
                }
            )
            return

        direction.queued_packets += 1
        direction.peak_queue_packets = max(
            direction.peak_queue_packets, direction.queued_packets
        )
        direction.scheduled_packets += 1
        direction.scheduled_bytes += len(payload)
        self.sequence += 1
        heapq.heappush(
            self.schedule,
            ScheduledDatagram(
                release_time=release_time,
                sequence=self.sequence,
                direction=direction_name,
                packet_sequence=packet_sequence,
                schedule_epoch_offset_us=schedule_epoch_offset_us,
                frozen_send_offset_us=frozen_send_offset_us,
                payload=payload,
                destination=destination,
            ),
        )
        self.write_event(
            {
                "sequence": self.sequence,
                "direction": direction_name,
                "action": "scheduled",
                "bytes": len(payload),
                "arrival_offset_us": self.offset_microseconds(now),
                "release_offset_us": self.offset_microseconds(release_time),
                "serialization_us": round(serialization_seconds * 1_000_000),
                "jitter_us": round(jitter_seconds * 1_000_000),
                "queue_depth_packets": direction.queued_packets,
                **event_contract,
            }
        )

    def receive_ready_datagrams(self, endpoint: socket.socket, direction_name: str) -> None:
        for _ in range(256):
            try:
                if direction_name == "client_to_server":
                    payload, source = endpoint.recvfrom(65535)
                    observed = (str(source[0]), int(source[1]))
                    expected = (
                        self.args.expected_client_host,
                        self.args.expected_client_port,
                    )
                    if observed != expected:
                        self.contract_error = {
                            "reason": "unexpected_client_endpoint",
                            "expected_endpoint": list(expected),
                            "observed_endpoint": list(observed),
                        }
                        self.sequence += 1
                        self.write_event(
                            {
                                "sequence": self.sequence,
                                "direction": direction_name,
                                "action": "contract_failed",
                                "reason": self.contract_error["reason"],
                                "bytes": len(payload),
                                "arrival_offset_us": self.offset_microseconds(
                                    time.monotonic()
                                ),
                                "observed_endpoint": list(observed),
                                "expected_endpoint": list(expected),
                                "packet_sequence": None,
                                "schedule_epoch_offset_us": None,
                                "frozen_send_offset_us": None,
                                "actual_forwarding_lag_us": None,
                            }
                        )
                        raise RuntimeError(
                            "客户端端点不符合冻结四元组合同："
                            f"{observed[0]}:{observed[1]} != {expected[0]}:{expected[1]}"
                        )
                    self.client_endpoint = observed
                    destination = None
                else:
                    payload = endpoint.recv(65535)
                    destination = self.client_endpoint
                    if destination is None:
                        self.sequence += 1
                        self.write_event(
                            {
                                "sequence": self.sequence,
                                "direction": direction_name,
                                "action": "dropped",
                                "reason": "client_endpoint_unknown",
                                "bytes": len(payload),
                                "arrival_offset_us": self.offset_microseconds(
                                    time.monotonic()
                                ),
                                "packet_sequence": None,
                                "schedule_epoch_offset_us": None,
                                "frozen_send_offset_us": None,
                                "actual_forwarding_lag_us": None,
                            }
                        )
                        continue
            except BlockingIOError:
                return
            self.schedule_datagram(
                direction_name=direction_name,
                payload=payload,
                destination=destination,
            )

    def forward_due_datagrams(self) -> None:
        now = time.monotonic()
        while self.schedule and self.schedule[0].release_time <= now:
            datagram = heapq.heappop(self.schedule)
            direction = self.directions[datagram.direction]
            direction.queued_packets -= 1
            try:
                if datagram.direction == "client_to_server":
                    sent = self.upstream.send(datagram.payload)
                else:
                    if datagram.destination is None:
                        raise RuntimeError("服务端到客户端报文缺少目标端点")
                    sent = self.downstream.sendto(datagram.payload, datagram.destination)
                if sent != len(datagram.payload):
                    raise RuntimeError(f"UDP 报文未完整发送：{sent}/{len(datagram.payload)}")
            except (OSError, RuntimeError) as error:
                direction.send_error_packets += 1
                self.sequence += 1
                self.write_event(
                    {
                        "sequence": self.sequence,
                        "direction": datagram.direction,
                        "action": "send_failed",
                        "reason": type(error).__name__,
                        "bytes": len(datagram.payload),
                        "release_offset_us": self.offset_microseconds(now),
                        "queue_depth_packets": direction.queued_packets,
                        "packet_sequence": datagram.packet_sequence,
                        "schedule_epoch_offset_us": datagram.schedule_epoch_offset_us,
                        "frozen_send_offset_us": datagram.frozen_send_offset_us,
                        "actual_forwarding_lag_us": round(
                            (now - datagram.release_time) * 1_000_000
                        ),
                    }
                )
                raise
            direction.forwarded_packets += 1
            direction.forwarded_bytes += sent
            self.last_activity = now
            self.sequence += 1
            self.write_event(
                {
                    "sequence": self.sequence,
                    "direction": datagram.direction,
                    "action": "forwarded",
                    "bytes": sent,
                    "forwarded_offset_us": self.offset_microseconds(now),
                    "scheduled_release_offset_us": self.offset_microseconds(
                        datagram.release_time
                    ),
                    "queue_depth_packets": direction.queued_packets,
                    "packet_sequence": datagram.packet_sequence,
                    "schedule_epoch_offset_us": datagram.schedule_epoch_offset_us,
                    "frozen_send_offset_us": datagram.frozen_send_offset_us,
                    "actual_forwarding_lag_us": round(
                        (now - datagram.release_time) * 1_000_000
                    ),
                }
            )

    def ready_payload(self) -> dict[str, Any]:
        downstream_host, downstream_port = self.downstream.getsockname()
        upstream_host, upstream_port = self.upstream.getsockname()
        return {
            "schema_version": "flow_probe_r2_quic_udp_proxy_ready_v1",
            "status": "ready",
            "backend": "deterministic_userspace_udp_proxy",
            "pid": os.getpid(),
            "listen_endpoint": [downstream_host, downstream_port],
            "upstream_local_endpoint": [upstream_host, upstream_port],
            "upstream_server_endpoint": [
                self.args.upstream_host,
                self.args.upstream_port,
            ],
            "expected_client_endpoint": [
                self.args.expected_client_host,
                self.args.expected_client_port,
            ],
            "schedule_mode": self.args.schedule_mode,
            "process_state_scope": "new_process_empty_state",
            "initial_schedule_packets": 0,
            "initial_direction_packet_sequences": {
                "client_to_server": 0,
                "server_to_client": 0,
            },
            "config_sha256": self.args.config_sha256,
            "started_at": self.started_wall,
        }

    def stats_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "flow_probe_r2_quic_udp_proxy_stats_v1",
            "status": "failed" if self.failed else "finished",
            "backend": "deterministic_userspace_udp_proxy",
            "implementation_layer": "userspace",
            "kernel_netem_truth": False,
            "network_namespace_truth": False,
            "kernel_queue_truth": False,
            "config_sha256": self.args.config_sha256,
            "schedule_mode": self.args.schedule_mode,
            "process_state_scope": "new_process_empty_state",
            "exit_reason": self.exit_reason,
            "contract_error": self.contract_error,
            "started_at": self.started_wall,
            "elapsed_seconds": round(time.monotonic() - self.started_monotonic, 6),
            "listen_endpoint": list(self.downstream.getsockname()),
            "upstream_local_endpoint": list(self.upstream.getsockname()),
            "upstream_server_endpoint": [
                self.args.upstream_host,
                self.args.upstream_port,
            ],
            "observed_client_endpoint": (
                list(self.client_endpoint) if self.client_endpoint is not None else None
            ),
            "expected_client_endpoint": [
                self.args.expected_client_host,
                self.args.expected_client_port,
            ],
            "parameters": {
                "delay_ms": self.args.delay_ms,
                "jitter_ms": self.args.jitter_ms,
                "loss_percent": self.args.loss_percent,
                "rate_mbit": self.args.rate_mbit,
                "queue_limit_packets": self.args.queue_limit_packets,
            },
            "directions": {
                name: direction.as_dict(self.started_monotonic)
                for name, direction in sorted(self.directions.items())
            },
            "scheduled_packets_at_shutdown": len(self.schedule),
        }

    def run(self) -> None:
        atomic_json(self.args.ready_file, self.ready_payload())
        print(
            f"用户态 UDP 代理就绪：{self.args.listen_host}:{self.args.listen_port} -> "
            f"{self.args.upstream_host}:{self.args.upstream_port}",
            flush=True,
        )
        try:
            while self.running:
                self.forward_due_datagrams()
                now = time.monotonic()
                if now - self.last_activity > self.args.idle_timeout_seconds:
                    self.exit_reason = "idle_timeout"
                    raise TimeoutError("用户态 UDP 代理超过空闲时限")
                timeout = 0.2
                if self.schedule:
                    timeout = min(timeout, max(0.0, self.schedule[0].release_time - now))
                for key, _ in self.selector.select(timeout):
                    self.receive_ready_datagrams(key.fileobj, str(key.data))
                self.forward_due_datagrams()
        except BaseException as error:
            self.failed = True
            if self.exit_reason == "signal":
                self.exit_reason = f"error_{type(error).__name__}"
            raise
        finally:
            atomic_json(self.args.stats_file, self.stats_payload())
            self.event_stream.flush()
            self.event_stream.close()
            self.selector.close()
            self.downstream.close()
            self.upstream.close()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, required=True)
    parser.add_argument("--upstream-bind-host", default="127.0.0.1")
    parser.add_argument("--upstream-bind-port", type=int, required=True)
    parser.add_argument("--upstream-host", default="127.0.0.1")
    parser.add_argument("--upstream-port", type=int, required=True)
    parser.add_argument("--expected-client-host", required=True)
    parser.add_argument("--expected-client-port", type=int, required=True)
    parser.add_argument(
        "--schedule-mode",
        choices=("fixed_sequence_epoch_v1",),
        required=True,
    )
    parser.add_argument("--delay-ms", type=float, required=True)
    parser.add_argument("--jitter-ms", type=float, required=True)
    parser.add_argument("--loss-percent", type=float, required=True)
    parser.add_argument("--rate-mbit", type=float, required=True)
    parser.add_argument("--queue-limit-packets", type=int, required=True)
    parser.add_argument("--client-to-server-seed", type=int, required=True)
    parser.add_argument("--server-to-client-seed", type=int, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--ready-file", type=Path, required=True)
    parser.add_argument("--stats-file", type=Path, required=True)
    parser.add_argument("--event-log", type=Path, required=True)
    parser.add_argument("--idle-timeout-seconds", type=float, default=1200.0)
    args = parser.parse_args()
    if not 1024 <= args.listen_port <= 65535:
        parser.error("监听端口必须位于 1024..65535")
    if not 1 <= args.upstream_port <= 65535:
        parser.error("上游端口必须位于 1..65535")
    if not 1024 <= args.upstream_bind_port <= 65535:
        parser.error("上游绑定端口必须位于 1024..65535")
    if not 1024 <= args.expected_client_port <= 65535:
        parser.error("期望客户端端口必须位于 1024..65535")
    if args.delay_ms < 0 or args.jitter_ms < 0:
        parser.error("延迟与抖动不得为负数")
    if not 0 <= args.loss_percent < 100:
        parser.error("丢包率必须位于 [0, 100)")
    if args.rate_mbit <= 0 or args.queue_limit_packets <= 0:
        parser.error("速率与队列上限必须为正数")
    if len(args.config_sha256) != 64:
        parser.error("配置 SHA-256 必须为 64 个十六进制字符")
    for path in (args.ready_file, args.stats_file, args.event_log):
        if path.exists():
            parser.error(f"输出文件已存在，拒绝覆盖：{path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    return args


def main() -> int:
    args = parse_arguments()
    proxy = DeterministicUdpProxy(args)

    def stop_proxy(signum: int, _frame: object) -> None:
        proxy.exit_reason = f"signal_{signum}"
        proxy.running = False

    signal.signal(signal.SIGINT, stop_proxy)
    signal.signal(signal.SIGTERM, stop_proxy)
    proxy.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
