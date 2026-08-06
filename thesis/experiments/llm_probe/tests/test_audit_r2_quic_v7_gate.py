#!/usr/bin/env python3
"""验证 QUIC v7 单轮机器审计不会越过冻结门禁。"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import audit_r2_quic_v7_gate as auditor  # noqa: E402


EXPECTED_RUNS = [
    {
        "run_id": "r2-quic-directional-datagram-v7-run1-aioquic",
        "implementation": "aioquic",
        "target_connection_index": 12,
    },
    {
        "run_id": "r2-quic-directional-datagram-v7-run2-quiche",
        "implementation": "quiche",
        "target_connection_index": 32,
    },
    {
        "run_id": "r2-quic-directional-datagram-v7-run3-aioquic",
        "implementation": "aioquic",
        "target_connection_index": 12,
    },
]


class R2QuicV7SingleRunGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config_path = self.root / "configs/v7.json"
        self.output_root = self.root / "runs/data-raw" / EXPECTED_RUNS[0]["run_id"]
        self.launcher_path = (
            self.root / "runs/launchers" / EXPECTED_RUNS[0]["run_id"] / "status.json"
        )
        self.summary_path = self.root / "runs/audits/v7-run1-summary.json"
        self.config = {
            "determinism_contract": {
                "contract_version": "flow_probe_r2_quic_four_tuple_contract_v7",
                "gate_runs": EXPECTED_RUNS,
            },
            "network_contract": {
                "directional_max_datagram_rule": "actual_sender_implementation_v1",
                "max_datagram_bytes_by_implementation": {
                    "aioquic": 1_200,
                    "quiche": 1_350,
                },
            },
            "reference_server": {"implementation": "quiche"},
        }
        self.config_path.parent.mkdir(parents=True)
        self.output_root.mkdir(parents=True)
        self.launcher_path.parent.mkdir(parents=True)
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        (self.output_root / "collection-config.json").write_text(
            json.dumps(self.config), encoding="utf-8"
        )
        self.launcher_state = {
            "schema_version": "flow_probe_r2_quic_launcher_v4",
            "status": "finished",
            "phase": "field",
            "run_id": EXPECTED_RUNS[0]["run_id"],
            "output_root": str(self.output_root),
            "config_path": str(self.config_path),
            "driver_exit": 0,
            "tee_exit": 0,
            "started_at": "2026-08-06T10:00:00+08:00",
            "finished_at": "2026-08-06T10:01:00+08:00",
        }
        self._write_launcher_state()
        directional = {
            "valid": True,
            "expected": {"client_to_server": 1_200, "server_to_client": 1_350},
            "checks": {
                "impairment_exact": True,
                "ready_exact": True,
                "stats_parameters_exact": True,
                "direction_stats_exact": True,
            },
            "errors": [],
        }
        self.common_run = {
            "all_checks_passed": True,
            "checks": {"directional_datagram_binding_exact": True},
            "evidence": {
                "implementation": "aioquic",
                "directional_datagram_audit": directional,
            },
            "errors": [],
        }
        self.pacing_run = {"valid": True, "errors": []}

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write_launcher_state(self) -> None:
        self.launcher_path.write_text(json.dumps(self.launcher_state), encoding="utf-8")

    def _args(self, summary_path: Path | None = None) -> SimpleNamespace:
        return SimpleNamespace(
            project_root=self.root,
            config=self.config_path,
            run_index=1,
            output_root=self.output_root,
            launcher_status_path=self.launcher_path,
            summary_path=summary_path or self.summary_path,
        )

    def _invoke(
        self,
        *,
        summary_path: Path | None = None,
        contract_valid: bool = True,
        toolchain_valid: bool = True,
        common_run: dict[str, object] | None = None,
        pacing_run: dict[str, object] | None = None,
    ) -> int:
        with (
            mock.patch.object(
                auditor,
                "contract_checks",
                return_value={"valid": contract_valid, "checks": {}, "errors": []},
            ),
            mock.patch.object(
                auditor,
                "toolchain_checks",
                return_value={"valid": toolchain_valid, "checks": {}, "errors": []},
            ),
            mock.patch.object(
                auditor.common,
                "audit_run",
                return_value=common_run or copy.deepcopy(self.common_run),
            ),
            mock.patch.object(
                auditor.v5,
                "audit_pacing",
                return_value=pacing_run or copy.deepcopy(self.pacing_run),
            ),
        ):
            return auditor.audit_single_run(self._args(summary_path))

    def test_single_run_passes_and_summary_cannot_be_overwritten(self) -> None:
        self.assertEqual(self._invoke(), 0)
        first_bytes = self.summary_path.read_bytes()
        summary = json.loads(first_bytes)

        self.assertEqual(summary["schema_version"], "flow_probe_r2_quic_v7_single_run_gate_v1")
        self.assertEqual(summary["status"], "PASS_R2_QUIC_V7_SINGLE_RUN_GATE_ONLY")
        self.assertEqual(summary["run_index"], 1)
        self.assertEqual(summary["expected_run"], EXPECTED_RUNS[0])
        self.assertTrue(summary["launcher_audit"]["valid"])
        self.assertTrue(summary["copied_config_exact"])
        self.assertTrue(summary["toolchain_audit"]["valid"])
        self.assertTrue(summary["directional_mapping_audit"]["valid"])
        self.assertTrue(summary["common_run_audit"]["all_checks_passed"])
        self.assertTrue(summary["pacing_audit"]["valid"])
        self.assertTrue(summary["all_conditions_passed"])

        self.assertEqual(self._invoke(), 2)
        self.assertEqual(self.summary_path.read_bytes(), first_bytes)

    def test_each_required_gate_fails_closed_with_nonzero_exit(self) -> None:
        cases: list[tuple[str, object]] = [
            ("contract", {"contract_valid": False}),
            ("toolchain", {"toolchain_valid": False}),
            (
                "common",
                {
                    "common_run": {
                        **copy.deepcopy(self.common_run),
                        "all_checks_passed": False,
                    }
                },
            ),
            ("pacing", {"pacing_run": {"valid": False, "errors": ["节奏失败"]}}),
            (
                "directional",
                {
                    "common_run": {
                        **copy.deepcopy(self.common_run),
                        "evidence": {
                            "implementation": "aioquic",
                            "directional_datagram_audit": {
                                "valid": False,
                                "expected": {
                                    "client_to_server": 1_200,
                                    "server_to_client": 1_350,
                                },
                                "checks": {},
                                "errors": ["方向映射失败"],
                            },
                        },
                    }
                },
            ),
        ]

        for name, raw_kwargs in cases:
            with self.subTest(name=name):
                summary_path = self.summary_path.with_name(f"{name}.json")
                kwargs = dict(raw_kwargs)
                self.assertEqual(self._invoke(summary_path=summary_path, **kwargs), 1)
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                self.assertEqual(summary["status"], auditor.NO_GO_STATUS)
                self.assertFalse(summary["all_conditions_passed"])

        self.launcher_state["run_id"] = EXPECTED_RUNS[1]["run_id"]
        self._write_launcher_state()
        identity_summary = self.summary_path.with_name("identity.json")
        self.assertEqual(self._invoke(summary_path=identity_summary), 1)
        self.assertFalse(
            json.loads(identity_summary.read_text(encoding="utf-8"))["launcher_audit"]["valid"]
        )

        self.launcher_state["run_id"] = EXPECTED_RUNS[0]["run_id"]
        self.launcher_state["status"] = "failed"
        self._write_launcher_state()
        launcher_summary = self.summary_path.with_name("launcher.json")
        self.assertEqual(self._invoke(summary_path=launcher_summary), 1)

        (self.output_root / "collection-config.json").write_text("{}", encoding="utf-8")
        copied_summary = self.summary_path.with_name("copied.json")
        self.assertEqual(self._invoke(summary_path=copied_summary), 1)
        self.assertFalse(
            json.loads(copied_summary.read_text(encoding="utf-8"))["copied_config_exact"]
        )


if __name__ == "__main__":
    unittest.main()
