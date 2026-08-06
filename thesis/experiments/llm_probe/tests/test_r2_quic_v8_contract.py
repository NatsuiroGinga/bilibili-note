#!/usr/bin/env python3
"""验证 QUIC v8 有限队列丢包与单轮机器收据合同。"""

from __future__ import annotations

import copy
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import audit_r2_quic_v8_gate as auditor  # noqa: E402


V7_CONFIG = PROJECT_ROOT / "configs/r2_quic_controlled_directional_datagram_v7.json"
V8_CONFIG = PROJECT_ROOT / "configs/r2_quic_controlled_deterministic_queue_drop_v8.json"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def valid_events() -> list[dict[str, object]]:
    return [
        {
            "sequence": 1,
            "direction": "server_to_client",
            "action": "scheduled",
            "receive_batch_id": 1,
            "packet_sequence": 1,
            "bytes": 90,
            "arrival_offset_us": 0,
            "service_backlog_before_bytes": 0,
            "service_backlog_after_bytes": 90,
            "waiting_before_bytes": 0,
            "waiting_after_bytes": 0,
            "in_service_before_bytes": 0,
            "in_service_after_bytes": 90,
            "delay_inflight_bytes": 0,
            "service_classification": "in_service",
            "serialization_start_offset_us": 0,
            "serialization_finish_offset_us": 36,
            "scheduled_release_offset_us": 50_036,
            "serialization_us": 36,
            "admitted": True,
            "reason": None,
        },
        {
            "sequence": 2,
            "direction": "server_to_client",
            "action": "dropped",
            "receive_batch_id": 1,
            "packet_sequence": 2,
            "bytes": 20,
            "arrival_offset_us": 1,
            "service_backlog_before_bytes": 90,
            "service_backlog_after_bytes": 90,
            "waiting_before_bytes": 0,
            "waiting_after_bytes": 0,
            "in_service_before_bytes": 90,
            "in_service_after_bytes": 90,
            "delay_inflight_bytes": 0,
            "serialization_start_offset_us": None,
            "serialization_finish_offset_us": None,
            "scheduled_release_offset_us": None,
            "admitted": False,
            "reason": "userspace_queue_limit_bytes",
        },
        {
            "sequence": 3,
            "direction": "server_to_client",
            "action": "receive_batch_completed",
            "receive_batch_id": 1,
            "batch_packets": 2,
            "batch_bytes": 110,
        },
        {
            "sequence": 4,
            "direction": "server_to_client",
            "action": "service_completed",
            "packet_sequence": 1,
            "bytes": 90,
            "service_completion_offset_us": 36,
            "service_backlog_before_bytes": 90,
            "service_backlog_after_bytes": 0,
            "waiting_before_bytes": 0,
            "waiting_after_bytes": 0,
            "in_service_before_bytes": 90,
            "in_service_after_bytes": 0,
            "delay_inflight_before_bytes": 0,
            "delay_inflight_after_bytes": 90,
        },
        {
            "sequence": 5,
            "direction": "server_to_client",
            "action": "forwarded",
            "packet_sequence": 1,
            "bytes": 90,
            "scheduled_release_offset_us": 50_036,
            "forwarded_offset_us": 50_036,
            "delay_inflight_before_bytes": 90,
            "delay_inflight_after_bytes": 0,
            "actual_forwarding_lag_us": 0,
        },
    ]


def valid_stats() -> dict[str, object]:
    return {
        "status": "finished",
        "contract_error": None,
        "scheduled_packets_at_shutdown": 0,
        "scheduled_bytes_at_shutdown": 0,
        "parameters": {
            "queue_capacity_bytes": 100,
            "serialization_rounding_tolerance_us_per_packet": 1,
            "max_datagram_bytes_by_direction": {
                "client_to_server": 100,
                "server_to_client": 100,
            },
        },
        "directions": {
            "server_to_client": {
                "received_packets": 2,
                "received_bytes": 110,
                "scheduled_packets": 1,
                "scheduled_bytes": 90,
                "forwarded_packets": 1,
                "forwarded_bytes": 90,
                "random_drop_packets": 0,
                "random_drop_bytes": 0,
                "queue_drop_packets": 1,
                "queue_drop_bytes": 20,
                "send_error_packets": 0,
                "send_error_bytes": 0,
                "queued_packets_at_shutdown": 0,
                "service_backlog_bytes_at_shutdown": 0,
                "waiting_bytes_at_shutdown": 0,
                "in_service_bytes_at_shutdown": 0,
                "delay_inflight_bytes_at_shutdown": 0,
                "peak_service_backlog_bytes": 90,
            }
        },
    }


class R2QuicV8ContractTest(unittest.TestCase):
    def test_v8_replaces_only_legacy_drop_and_exact_lag_checks(self) -> None:
        common_run = {
            "checks": {
                "identity_exact": True,
                "queue_drop_zero": False,
                "drop_and_send_error_bytes_zero": False,
                "v4_event_replay_exact": False,
            },
            "errors": [],
        }
        self.assertTrue(auditor.v8_common_checks_valid(common_run))

        unrelated_failure = copy.deepcopy(common_run)
        unrelated_failure["checks"]["identity_exact"] = False
        self.assertFalse(auditor.v8_common_checks_valid(unrelated_failure))

        within_tolerance = [
            {
                "action": "forwarded",
                "scheduled_release_offset_us": 100,
                "forwarded_offset_us": 111,
                "actual_forwarding_lag_us": 10,
            }
        ]
        normalized = auditor.normalize_forwarding_lag_receipts(
            within_tolerance,
            tolerance_us=1,
        )
        self.assertEqual(normalized[0]["actual_forwarding_lag_us"], 11)
        self.assertEqual(within_tolerance[0]["actual_forwarding_lag_us"], 10)

        outside_tolerance = copy.deepcopy(within_tolerance)
        outside_tolerance[0]["actual_forwarding_lag_us"] = 9
        with self.assertRaises(ValueError):
            auditor.normalize_forwarding_lag_receipts(outside_tolerance, tolerance_us=1)

    def test_real_configs_differ_only_by_frozen_allowlist(self) -> None:
        v7 = json.loads(V7_CONFIG.read_text(encoding="utf-8"))
        v8 = json.loads(V8_CONFIG.read_text(encoding="utf-8"))
        v7_projection = auditor.normalized_config_projection(v7)
        v8_projection = auditor.normalized_config_projection(v8)

        self.assertEqual(len(v7_projection), 5_398)
        self.assertEqual(auditor.sha256_bytes(v7_projection), auditor.EXPECTED_PROJECTION_SHA256)
        self.assertEqual(v8_projection, v7_projection)
        self.assertFalse(auditor.config_enables_v8(v7))
        self.assertTrue(auditor.config_enables_v8(v8))

    def test_capacity_drop_lifecycle_replay_fails_on_any_tampering(self) -> None:
        stats = valid_stats()
        with tempfile.TemporaryDirectory() as temporary:
            event_path = Path(temporary) / "events.jsonl"

            def audit(rows: list[dict[str, object]], current_stats=stats):
                event_path.write_text(
                    "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                    encoding="utf-8",
                )
                with mock.patch.object(
                    auditor.common,
                    "audit_v4_event_log",
                    return_value={"valid": True, "directions": {}, "errors": []},
                ):
                    return auditor.audit_v8_event_log(
                        event_path,
                        current_stats,
                        require_server_to_client_drop=True,
                    )

            accepted = audit(valid_events())
            self.assertTrue(accepted["valid"], accepted)

            mutations = []
            not_over_capacity = copy.deepcopy(valid_events())
            not_over_capacity[1]["service_backlog_before_bytes"] = 80
            not_over_capacity[1]["service_backlog_after_bytes"] = 80
            not_over_capacity[1]["in_service_before_bytes"] = 80
            not_over_capacity[1]["in_service_after_bytes"] = 80
            mutations.append(not_over_capacity)
            missing_packet = copy.deepcopy(valid_events())
            missing_packet[1]["packet_sequence"] = 3
            mutations.append(missing_packet)
            changed_after_drop = copy.deepcopy(valid_events())
            changed_after_drop[1]["service_backlog_after_bytes"] = 89
            mutations.append(changed_after_drop)
            missing_batch_identity = copy.deepcopy(valid_events())
            missing_batch_identity[1].pop("receive_batch_id")
            mutations.append(missing_batch_identity)
            missing_forward = valid_events()[:-1]
            mutations.append(missing_forward)

            for rows in mutations:
                with self.subTest(rows=rows):
                    self.assertFalse(audit(rows)["valid"])

            missing_null = copy.deepcopy(stats)
            missing_null.pop("contract_error")
            self.assertFalse(audit(valid_events(), missing_null)["valid"])

    def test_all_qlogs_pcap_and_capture_log_are_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first_qlog = root / "first.qlog"
            second_qlog = root / "second.qlog"
            first_qlog.write_text(
                json.dumps(
                    {
                        "qlog_version": "0.3",
                        "qlog_format": "JSON",
                        "traces": [
                            {
                                "vantage_point": {"type": "client"},
                                "common_fields": {},
                                "events": [
                                    {"time": 1, "name": "transport:packet_sent", "data": {}}
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            second_qlog.write_text(
                "\x1e"
                + json.dumps(
                    {
                        "qlog_version": "0.3",
                        "qlog_format": "JSON-SEQ",
                        "trace": {
                            "vantage_point": {"type": "client"},
                            "common_fields": {},
                        },
                    }
                )
                + "\n\x1e"
                + json.dumps({"time": 2, "name": "recovery:metrics_updated", "data": {}})
                + "\n",
                encoding="utf-8",
            )
            qlog_audit = auditor.audit_all_qlogs([first_qlog, second_qlog])
            self.assertTrue(qlog_audit["valid"], qlog_audit)
            self.assertEqual(qlog_audit["file_count"], 2)

            second_qlog.write_text(
                "\x1e"
                + json.dumps(
                    {
                        "qlog_version": "0.3",
                        "qlog_format": "JSON-SEQ",
                        "trace": {
                            "vantage_point": {"type": "client"},
                            "common_fields": {},
                        },
                    }
                )
                + "\n\x1e{",
                encoding="utf-8",
            )
            self.assertFalse(auditor.audit_all_qlogs([first_qlog, second_qlog])["valid"])

            pcap_path = root / "capture.pcap"
            global_header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65_535, 1)
            record_header = struct.pack("<IIII", 1, 2, 4, 4)
            pcap_path.write_bytes(global_header + record_header + b"data")
            self.assertTrue(auditor.audit_pcap(pcap_path)["valid"])
            pcap_path.write_bytes(global_header + record_header + b"dat")
            self.assertFalse(auditor.audit_pcap(pcap_path)["valid"])

            capture_log = root / "capture.log"
            capture_log.write_text(
                "2 packets captured\n2 packets received by filter\n0 packets dropped by kernel\n",
                encoding="utf-8",
            )
            self.assertTrue(auditor.audit_capture_log(capture_log)["valid"])
            capture_log.write_text(
                "2 packets captured\n2 packets received by filter\n1 packet dropped by kernel\n",
                encoding="utf-8",
            )
            self.assertFalse(auditor.audit_capture_log(capture_log)["valid"])

    def test_single_run_summary_is_bound_and_cannot_be_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "configs/r2_quic_controlled_deterministic_queue_drop_v8.json"
            output_root = root / "runs/data-raw/r2-quic-deterministic-queue-drop-v8-run1-aioquic"
            launcher_path = (
                root / "runs/launchers/r2-quic-deterministic-queue-drop-v8-run1-aioquic/status.json"
            )
            summary_path = (
                root
                / "runs/audits/r2-quic-deterministic-queue-drop-v8-run1-single-gate-summary.json"
            )
            output_root.mkdir(parents=True)
            config = json.loads(V8_CONFIG.read_text(encoding="utf-8"))
            write_json(config_path, config)
            write_json(output_root / "collection-config.json", config)
            write_json(
                launcher_path, {"run_id": config["determinism_contract"]["gate_runs"][0]["run_id"]}
            )
            args = SimpleNamespace(
                project_root=root,
                config=config_path,
                run_index=1,
                output_root=output_root,
                launcher_status_path=launcher_path,
                summary_path=summary_path,
            )
            passed_run = {
                "valid": True,
                "common_run": {
                    "all_checks_passed": True,
                    "evidence": {"implementation": "aioquic"},
                },
                "pacing": {"valid": True},
                "errors": [],
            }
            with (
                mock.patch.object(auditor, "contract_checks", return_value={"valid": True}),
                mock.patch.object(auditor, "toolchain_checks", return_value={"valid": True}),
                mock.patch.object(auditor, "audit_v8_run", return_value=passed_run),
                mock.patch.object(
                    auditor,
                    "audit_single_launcher",
                    return_value={"valid": True, "sha256": "a" * 64},
                ),
            ):
                self.assertEqual(auditor.audit_single_run(args), 0)
                first_bytes = summary_path.read_bytes()
                summary = json.loads(first_bytes)
                self.assertEqual(summary["status"], auditor.SINGLE_RUN_PASS_STATUS)
                self.assertTrue(summary["all_conditions_passed"])
                self.assertEqual(auditor.audit_single_run(args), 2)
                self.assertEqual(summary_path.read_bytes(), first_bytes)


if __name__ == "__main__":
    unittest.main()
