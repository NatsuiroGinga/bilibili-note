#!/usr/bin/env python3
"""验证 R2 QUIC v4 字节容量与事件重放合同。"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
CONFIG_PATH = PROJECT_ROOT / "configs/r2_quic_controlled_burst_capacity_v4.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


proxy_module = load_module(
    "r2_quic_udp_proxy_v4_test",
    SCRIPTS_ROOT / "r2_quic_udp_proxy.py",
)
auditor = load_module(
    "audit_r2_quic_determinism_gate_v4_test",
    SCRIPTS_ROOT / "audit_r2_quic_determinism_gate.py",
)


def make_direction(name: str = "server_to_client"):
    return proxy_module.DirectionState(
        name=name,
        seed=43,
        delay_seconds=0.05,
        jitter_seconds=0.0,
        loss_probability=0.0,
        rate_bits_per_second=20_000_000.0,
        queue_limit_packets=1000,
        queue_capacity_bytes=2_400,
        queue_margin_max_bytes=1_920,
        max_datagram_bytes=1_200,
    )


def make_proxy(direction):
    proxy = object.__new__(proxy_module.DeterministicUdpProxy)
    proxy.args = SimpleNamespace(
        schedule_mode="work_conserving_byte_service_delay_v1",
    )
    proxy.started_monotonic = 100.0
    proxy.last_activity = 100.0
    proxy.sequence = 0
    proxy.schedule = []
    proxy.event_stream = io.StringIO()
    proxy.directions = {direction.name: direction}
    return proxy


class R2QuicV4ContractTest(unittest.TestCase):
    def test_byte_capacity_settles_service_before_each_admission(self) -> None:
        direction = make_direction()
        proxy = make_proxy(direction)

        with mock.patch.object(proxy_module.time, "monotonic", return_value=100.0):
            for _ in range(2):
                proxy.schedule_datagram(
                    direction_name=direction.name,
                    payload=b"x" * 1_200,
                    destination=("127.0.0.1", 21012),
                )
            proxy.schedule_datagram(
                direction_name=direction.name,
                payload=b"x",
                destination=("127.0.0.1", 21012),
            )

        self.assertEqual(direction.service_backlog_bytes, 2_400)
        self.assertEqual(direction.peak_service_backlog_bytes, 2_400)
        self.assertEqual(direction.in_service_bytes, 1_200)
        self.assertEqual(direction.waiting_bytes, 1_200)
        self.assertEqual(direction.queue_drop_packets, 1)
        self.assertEqual(direction.queue_drop_bytes, 1)

        first = make_direction("client_to_server")
        second_proxy = make_proxy(first)
        with mock.patch.object(proxy_module.time, "monotonic", return_value=100.0):
            second_proxy.schedule_datagram(
                direction_name=first.name,
                payload=b"x" * 1000,
                destination=None,
            )
        with mock.patch.object(proxy_module.time, "monotonic", return_value=100.0004):
            second_proxy.schedule_datagram(
                direction_name=first.name,
                payload=b"x" * 1000,
                destination=None,
            )

        self.assertEqual(first.delay_inflight_bytes, 1000)
        self.assertEqual(first.service_backlog_bytes, 1000)
        events = [json.loads(line) for line in second_proxy.event_stream.getvalue().splitlines()]
        second_admission = [row for row in events if row["action"] == "scheduled"][-1]
        self.assertEqual(second_admission["service_backlog_before_bytes"], 0)
        self.assertEqual(second_admission["delay_inflight_bytes"], 1000)

    def test_event_replay_recomputes_peaks_conservation_and_serialization(self) -> None:
        rows = [
            {
                "sequence": 1,
                "direction": "client_to_server",
                "action": "scheduled",
                "packet_sequence": 1,
                "bytes": 100,
                "arrival_offset_us": 0,
                "service_backlog_before_bytes": 0,
                "service_backlog_after_bytes": 100,
                "delay_inflight_bytes": 0,
                "waiting_before_bytes": 0,
                "waiting_after_bytes": 0,
                "in_service_before_bytes": 0,
                "in_service_after_bytes": 100,
                "service_classification": "in_service",
                "serialization_start_offset_us": 0,
                "serialization_finish_offset_us": 40,
                "scheduled_release_offset_us": 50_040,
                "serialization_us": 40,
                "admitted": True,
                "reason": None,
            },
            {
                "sequence": 2,
                "direction": "client_to_server",
                "action": "service_completed",
                "packet_sequence": 1,
                "bytes": 100,
                "service_completion_offset_us": 40,
                "service_backlog_before_bytes": 100,
                "service_backlog_after_bytes": 0,
                "waiting_before_bytes": 0,
                "waiting_after_bytes": 0,
                "in_service_before_bytes": 100,
                "in_service_after_bytes": 0,
                "delay_inflight_before_bytes": 0,
                "delay_inflight_after_bytes": 100,
            },
            {
                "sequence": 3,
                "direction": "client_to_server",
                "action": "forwarded",
                "packet_sequence": 1,
                "bytes": 100,
                "scheduled_release_offset_us": 50_040,
                "forwarded_offset_us": 50_040,
                "delay_inflight_before_bytes": 100,
                "delay_inflight_after_bytes": 0,
                "actual_forwarding_lag_us": 0,
            },
        ]
        stats = {
            "parameters": {
                "queue_capacity_unit": "bytes",
                "queue_capacity_bytes": 2_097_152,
                "queue_margin_ratio": 0.8,
                "queue_margin_max_bytes": 1_677_721,
                "queue_margin_role": "diagnostic_only",
                "max_datagram_bytes": 1_200,
                "udp_receive_buffer_bytes": 65_535,
                "rate_bits_per_second": 20_000_000,
                "delay_us": 50_000,
            },
            "directions": {
                "client_to_server": {
                    "received_packets": 1,
                    "received_bytes": 100,
                    "scheduled_packets": 1,
                    "scheduled_bytes": 100,
                    "forwarded_packets": 1,
                    "forwarded_bytes": 100,
                    "random_drop_packets": 0,
                    "random_drop_bytes": 0,
                    "queue_drop_packets": 0,
                    "queue_drop_bytes": 0,
                    "send_error_packets": 0,
                    "send_error_bytes": 0,
                    "peak_service_backlog_bytes": 100,
                    "peak_delay_inflight_bytes": 100,
                    "waiting_bytes_at_shutdown": 0,
                    "in_service_bytes_at_shutdown": 0,
                    "service_backlog_bytes_at_shutdown": 0,
                    "delay_inflight_bytes_at_shutdown": 0,
                    "max_actual_forwarding_lag_us": 0,
                }
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            event_path = Path(temporary) / "proxy-events.jsonl"
            event_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            result = auditor.audit_v4_event_log(event_path, stats)
            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(
                result["directions"]["client_to_server"]["peak_service_backlog_bytes"],
                100,
            )

            stats["directions"]["client_to_server"]["peak_service_backlog_bytes"] = 99
            tampered = auditor.audit_v4_event_log(event_path, stats)
            self.assertFalse(tampered["valid"])

    def test_v4_config_freezes_capacity_and_three_run_identity(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        network = config["network_contract"]
        contract = config["determinism_contract"]

        self.assertEqual(network["queue_capacity_unit"], "bytes")
        self.assertEqual(network["queue_capacity_bytes"], 2_097_152)
        self.assertEqual(network["queue_margin_ratio"], 0.8)
        self.assertEqual(network["queue_margin_max_bytes"], 1_677_721)
        self.assertEqual(network["queue_margin_role"], "diagnostic_only")
        self.assertEqual(
            network["max_datagram_bytes_by_implementation"],
            {"aioquic": 1_200, "quiche": 1_350},
        )
        self.assertEqual(network["udp_receive_buffer_bytes"], 65_535)
        self.assertEqual(network["rate_model"], "work_conserving_byte_service")
        self.assertEqual(contract["schedule_mode"], "work_conserving_byte_service_delay_v1")
        self.assertEqual(
            [
                (row["implementation"], row["target_connection_index"])
                for row in contract["gate_runs"]
            ],
            [("aioquic", 12), ("quiche", 32), ("aioquic", 12)],
        )


if __name__ == "__main__":
    unittest.main()
