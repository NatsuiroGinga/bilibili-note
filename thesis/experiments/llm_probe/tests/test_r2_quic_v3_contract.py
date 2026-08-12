#!/usr/bin/env python3
"""验证 R2 QUIC v3 复审阻断项的最小行为合同。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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


collector = load_module(
    "r2_quic_controlled_collect",
    SCRIPTS_ROOT / "r2_quic_controlled_collect.py",
)
auditor = load_module(
    "audit_r2_quic_determinism_gate",
    SCRIPTS_ROOT / "audit_r2_quic_determinism_gate.py",
)


class R2QuicV3ContractTest(unittest.TestCase):
    @staticmethod
    def _closed_direction_stats() -> dict[str, int]:
        return {
            "received_packets": 1093,
            "scheduled_packets": 1092,
            "random_drop_packets": 1,
            "queue_drop_packets": 0,
            "received_bytes": 57281,
            "scheduled_bytes": 57235,
            "random_drop_bytes": 46,
            "queue_drop_bytes": 0,
            "send_error_bytes": 0,
            "waiting_bytes_at_shutdown": 0,
            "in_service_bytes_at_shutdown": 0,
            "service_backlog_bytes_at_shutdown": 0,
            "delay_inflight_bytes_at_shutdown": 0,
        }

    def test_nonzero_loss_accepts_closed_random_drop_statistics(self) -> None:
        validator = getattr(collector, "validate_work_conserving_direction", None)
        self.assertIsNotNone(validator, "采集器缺少方向级守恒验证入口")
        assert validator is not None

        validator(
            self._closed_direction_stats(),
            direction_name="client_to_server",
            loss_percent=0.5,
            is_v8=True,
        )

    def test_zero_loss_rejects_random_drop_statistics(self) -> None:
        validator = getattr(collector, "validate_work_conserving_direction", None)
        self.assertIsNotNone(validator, "采集器缺少方向级守恒验证入口")
        assert validator is not None

        with self.assertRaisesRegex(RuntimeError, "字节守恒或关停门禁失败"):
            validator(
                self._closed_direction_stats(),
                direction_name="client_to_server",
                loss_percent=0.0,
                is_v8=True,
            )

    def test_nonzero_loss_still_rejects_byte_imbalance(self) -> None:
        validator = getattr(collector, "validate_work_conserving_direction", None)
        self.assertIsNotNone(validator, "采集器缺少方向级守恒验证入口")
        assert validator is not None
        stats = self._closed_direction_stats()
        stats["received_bytes"] += 1

        with self.assertRaisesRegex(RuntimeError, "字节守恒或关停门禁失败"):
            validator(
                stats,
                direction_name="client_to_server",
                loss_percent=0.5,
                is_v8=True,
            )

    def test_controller_sigterm_receipt_preserves_raw_exit(self) -> None:
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"]
        )

        def stop_leftover_process() -> None:
            if process.poll() is None:
                process.kill()
            process.wait()

        self.addCleanup(stop_leftover_process)

        receipt = collector.stop_process_with_receipt(
            process,
            signal_number=signal.SIGTERM,
            timeout=5,
        )

        self.assertTrue(receipt["controller_sent_signal"])
        self.assertIsNone(receipt["poll_before_controller_signal"])
        self.assertEqual(receipt["controller_signal"], signal.SIGTERM)
        self.assertIsInstance(receipt["controller_signal_sent_at"], str)
        self.assertEqual(receipt["raw_exit"], -signal.SIGTERM)

    def test_quiche_command_binds_frozen_source_port(self) -> None:
        spec = collector.ConnectionSpec(
            index=32,
            implementation="quiche",
            profile={"id": "p03"},
            seed=43,
            payload={"id": "bulk", "bytes": 67_108_864},
        )

        command, _ = collector.client_command(
            spec=spec,
            tools_root=Path("/tmp/tools"),
            qlog_dir=Path("/tmp/qlog"),
            response_dir=Path("/tmp/response"),
            server_ip="127.0.0.1",
            port=20012,
            local_port=21012,
            payload_name="payload-bulk.bin",
        )

        option_index = command.index("--source-port")
        self.assertEqual(command[option_index + 1], "21012")

    def test_missing_timeout_keeps_v1_default(self) -> None:
        self.assertEqual(collector.client_timeout_seconds({}), 900.0)
        self.assertEqual(
            collector.client_timeout_seconds({"client_timeout_seconds": 240}),
            240.0,
        )

    def test_auditor_checks_three_serial_launchers_and_artifact_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            connection_root = root / "connection"
            connection_root.mkdir()
            artifact = connection_root / "receipt.json"
            artifact.write_text('{"status":"finished"}\n', encoding="utf-8")
            manifest = [
                {
                    "path": "receipt.json",
                    "bytes": artifact.stat().st_size,
                    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                }
            ]
            artifact_audit = auditor.audit_artifact_manifest(
                connection_root,
                manifest,
            )
            self.assertTrue(artifact_audit["valid"])
            self.assertEqual(artifact_audit["checked_count"], 1)

            launchers = [
                {
                    "schema_version": "flow_probe_r2_quic_launcher_v3",
                    "status": "finished",
                    "run_id": f"r2-quic-v3-run{index}",
                    "output_root": f"/runs/v3-run{index}",
                    "driver_exit": 0,
                    "tee_exit": 0,
                    "started_at": f"2026-08-05T0{index}:00:00+00:00",
                    "finished_at": f"2026-08-05T0{index}:01:00+00:00",
                }
                for index in (1, 2, 3)
            ]
            launcher_audit = auditor.audit_launcher_contract(
                launchers,
                [Path(f"/runs/v3-run{index}") for index in (1, 2, 3)],
                [
                    "r2-quic-v3-run1",
                    "r2-quic-v3-run2",
                    "r2-quic-v3-run3",
                ],
            )
            self.assertTrue(launcher_audit["valid"])
            self.assertTrue(launcher_audit["exactly_three_run_identities"])
            self.assertTrue(launcher_audit["strictly_serial"])

            artifact.write_text('{"status":"tampered"}\n', encoding="utf-8")
            self.assertFalse(
                auditor.audit_artifact_manifest(connection_root, manifest)["valid"]
            )


if __name__ == "__main__":
    unittest.main()
