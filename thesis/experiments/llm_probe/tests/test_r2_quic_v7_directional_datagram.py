#!/usr/bin/env python3
"""验证 QUIC v7 按实际发送端冻结方向级数据报上限。"""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块：{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


collector = load_module("r2_quic_v7_collector_test", SCRIPTS_ROOT / "r2_quic_controlled_collect.py")
proxy_module = load_module("r2_quic_v7_proxy_test", SCRIPTS_ROOT / "r2_quic_udp_proxy.py")
auditor = load_module("r2_quic_v7_auditor_test", SCRIPTS_ROOT / "audit_r2_quic_determinism_gate.py")

V7_CONFIG_PATH = PROJECT_ROOT / "configs/r2_quic_controlled_directional_datagram_v7.json"
V6_CONFIG_PATH = PROJECT_ROOT / "configs/r2_quic_controlled_binary_overlay_v6.json"


def make_direction(name: str, maximum: int):
    return proxy_module.DirectionState(
        name=name,
        seed=43,
        delay_seconds=0.05,
        jitter_seconds=0.0,
        loss_probability=0.0,
        rate_bits_per_second=20_000_000.0,
        queue_limit_packets=1000,
        queue_capacity_bytes=2_097_152,
        queue_margin_max_bytes=1_677_721,
        max_datagram_bytes=maximum,
    )


def make_proxy(directions):
    proxy = object.__new__(proxy_module.DeterministicUdpProxy)
    proxy.args = SimpleNamespace(schedule_mode="work_conserving_byte_service_delay_v1")
    proxy.started_monotonic = 100.0
    proxy.last_activity = 100.0
    proxy.sequence = 0
    proxy.schedule = []
    proxy.event_stream = io.StringIO()
    proxy.directions = directions
    proxy.contract_error = None
    return proxy


class R2QuicV7DirectionalDatagramTest(unittest.TestCase):
    def test_aioquic_client_and_quiche_server_use_distinct_direction_limits(self) -> None:
        config = {
            "determinism_contract": {
                "contract_version": "flow_probe_r2_quic_four_tuple_contract_v7",
                "schedule_mode": "work_conserving_byte_service_delay_v1",
            },
            "reference_server": {"implementation": "quiche"},
            "network_contract": {
                "queue_capacity_unit": "bytes",
                "queue_limit_packets": 1000,
                "queue_capacity_bytes": 2_097_152,
                "queue_margin_ratio": 0.8,
                "queue_margin_max_bytes": 1_677_721,
                "queue_margin_role": "diagnostic_only",
                "max_datagram_bytes_by_implementation": {"aioquic": 1_200, "quiche": 1_350},
                "directional_max_datagram_rule": "actual_sender_implementation_v1",
                "udp_receive_buffer_bytes": 65_535,
                "serialization_rounding_tolerance_us_per_packet": 1,
            },
        }
        contract = collector.proxy_queue_contract(config, "aioquic")
        expected = {"client_to_server": 1_200, "server_to_client": 1_350}
        self.assertEqual(contract["max_datagram_bytes_by_direction"], expected)

        directions = {name: make_direction(name, maximum) for name, maximum in expected.items()}
        proxy = make_proxy(directions)
        proxy.schedule_datagram(
            direction_name="server_to_client",
            payload=b"s" * 1_350,
            destination=("127.0.0.1", 21012),
        )
        with self.assertRaisesRegex(RuntimeError, "1201 > 1200"):
            proxy.schedule_datagram(
                direction_name="client_to_server",
                payload=b"c" * 1_201,
                destination=("127.0.0.1", 4433),
            )

    def test_real_v7_config_and_auditor_derive_both_client_mappings(self) -> None:
        config = json.loads(V7_CONFIG_PATH.read_text(encoding="utf-8"))
        expected_by_client = {
            "aioquic": {"client_to_server": 1_200, "server_to_client": 1_350},
            "quiche": {"client_to_server": 1_350, "server_to_client": 1_350},
        }
        for implementation, expected in expected_by_client.items():
            with self.subTest(implementation=implementation):
                contract = collector.proxy_queue_contract(config, implementation)
                self.assertEqual(contract["max_datagram_bytes_by_direction"], expected)
                self.assertEqual(
                    auditor.expected_directional_max_datagram_bytes(config, implementation),
                    expected,
                )

    def test_incomplete_directional_contract_is_rejected(self) -> None:
        args = SimpleNamespace(
            max_datagram_bytes=1_200,
            client_to_server_max_datagram_bytes=1_200,
            server_to_client_max_datagram_bytes=None,
        )
        with self.assertRaisesRegex(ValueError, "必须同时提供"):
            proxy_module.resolve_directional_datagram_limits(args)

    def test_v6_contract_keeps_legacy_single_value_behavior(self) -> None:
        config = json.loads(V6_CONFIG_PATH.read_text(encoding="utf-8"))
        contract = collector.proxy_queue_contract(config, "aioquic")
        self.assertEqual(contract["max_datagram_bytes"], 1_200)
        self.assertNotIn("max_datagram_bytes_by_direction", contract)

    def test_directional_receipts_and_event_limits_are_bound_to_frozen_config(self) -> None:
        config = json.loads(V7_CONFIG_PATH.read_text(encoding="utf-8"))
        expected = {"client_to_server": 1_200, "server_to_client": 1_350}
        impairment = {"max_datagram_bytes_by_direction": expected}
        ready = {"max_datagram_bytes_by_direction": expected}
        stats = {
            "parameters": {"max_datagram_bytes_by_direction": expected},
            "directions": {
                name: {"max_datagram_bytes": maximum} for name, maximum in expected.items()
            },
        }
        audit = auditor.audit_directional_datagram_binding(
            config, "aioquic", impairment, ready, stats
        )
        self.assertTrue(audit["valid"], audit)
        self.assertEqual(
            auditor.max_datagram_for_direction(stats["parameters"], "server_to_client"),
            1_350,
        )
        self.assertEqual(
            auditor.max_datagram_for_direction(stats["parameters"], "client_to_server"),
            1_200,
        )

        for receipt_name in ("impairment", "ready", "stats"):
            with self.subTest(receipt=receipt_name):
                changed_impairment = copy.deepcopy(impairment)
                changed_ready = copy.deepcopy(ready)
                changed_stats = copy.deepcopy(stats)
                target = {
                    "impairment": changed_impairment,
                    "ready": changed_ready,
                    "stats": changed_stats["parameters"],
                }[receipt_name]
                target["max_datagram_bytes_by_direction"]["server_to_client"] = 1_200
                changed = auditor.audit_directional_datagram_binding(
                    config,
                    "aioquic",
                    changed_impairment,
                    changed_ready,
                    changed_stats,
                )
                self.assertFalse(changed["valid"], changed)


if __name__ == "__main__":
    unittest.main()
