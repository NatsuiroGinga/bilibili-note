#!/usr/bin/env python3
"""审计 QUIC v8.1 端点收据修复后的三轮确定性有限队列门禁。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import audit_r2_quic_determinism_gate as common
import audit_r2_quic_v5_gate as v5
import audit_r2_quic_v8_gate as v8
import verify_r2_quic_v6_aioquic_overlay as overlay


GO_STATUS = "GO_TO_NEW_FIELD_MATRIX_QUIC_SEED_ONLY"
NO_GO_STATUS = "NO-GO_KEEP_QUIC_UNKNOWN"
INVALID_STATUS = "INVALID"
SINGLE_RUN_PASS_STATUS = "PASS_R2_QUIC_V8_1_SINGLE_RUN_GATE_ONLY"
SINGLE_RUN_SCHEMA = "flow_probe_r2_quic_v8_1_single_run_gate_v1"
THREE_RUN_SCHEMA = "flow_probe_r2_quic_v8_1_three_run_gate_v1"
EXPECTED_RUNS = [
    ("r2-quic-deterministic-queue-drop-v8-1-run1d-aioquic", "aioquic", 12),
    ("r2-quic-deterministic-queue-drop-v8-1-run2-quiche", "quiche", 32),
    ("r2-quic-deterministic-queue-drop-v8-1-run3-aioquic", "aioquic", 12),
]
EXPECTED_PATCH_SHA256 = "a9bf06e77140007ad49bf5d1aac13272e7b3fbfe128c9c2bb7428924b2f0e361"
EXPECTED_OVERLAY_SHA256 = "ca11dfe2195b40d7871a5b5d6643ebb6b3072da378e1859c0ad914ee7738d6f0"
EXPECTED_PROTOCOL_SHA256 = "0cdb314e4fd642b2eae66e13878b7b9df94ccb54f939901e664bda4e8714f077"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def expected_run(run_index: int) -> dict[str, Any]:
    if not 1 <= run_index <= len(EXPECTED_RUNS):
        raise ValueError("单轮门禁序号必须为 1、2 或 3")
    run_id, implementation, target_connection_index = EXPECTED_RUNS[run_index - 1]
    return {
        "run_id": run_id,
        "implementation": implementation,
        "target_connection_index": target_connection_index,
    }


def scientific_projection(config: dict[str, Any]) -> bytes:
    projected = copy.deepcopy(config)
    for name in (
        "schema_version",
        "dataset_version",
        "status",
        "field_output_root",
        "formal_output_root",
        "tool_root",
        "tool_binding",
    ):
        projected.pop(name)
    deterministic = projected["determinism_contract"]
    deterministic.pop("run_id_prefix")
    for run in deterministic["gate_runs"]:
        run.pop("run_id")
    deterministic["endpoint_pacing"].pop("aioquic_mode")
    return json.dumps(
        projected,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def contract_checks(config_path: Path, project_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    projection: dict[str, Any] = {}
    try:
        config = v5.read_json(config_path)
        v8_config = v5.read_json(
            project_root / "configs/r2_quic_controlled_deterministic_queue_drop_v8.json"
        )
        candidate_projection = scientific_projection(config)
        frozen_projection = scientific_projection(v8_config)
        deterministic = config["determinism_contract"]
        pacing = deterministic["endpoint_pacing"]
        binding = config["tool_binding"]
        configured_runs = [
            (
                str(item["run_id"]),
                str(item["implementation"]),
                int(item["target_connection_index"]),
            )
            for item in deterministic["gate_runs"]
        ]
        projection = {
            "v8_bytes": len(frozen_projection),
            "v8_sha256": sha256_bytes(frozen_projection),
            "v8_1_bytes": len(candidate_projection),
            "v8_1_sha256": sha256_bytes(candidate_projection),
        }
        checks = {
            "schema_exact": config.get("schema_version")
            == "flow_probe_r2_quic_controlled_collection_userspace_v8_1",
            "dataset_exact": config.get("dataset_version")
            == "r2-quic-controlled-userspace-v8-1",
            "status_exact": config.get("status")
            == "endpoint_receipt_timestamp_v8_1_frozen",
            "scientific_projection_unchanged": candidate_projection == frozen_projection,
            "contract_version_exact": deterministic.get("contract_version")
            == "flow_probe_r2_quic_four_tuple_contract_v8",
            "run_prefix_exact": deterministic.get("run_id_prefix")
            == "r2-quic-deterministic-queue-drop-v8-1-run",
            "three_runs_exact": configured_runs == EXPECTED_RUNS,
            "aioquic_receipt_mode_exact": pacing.get("aioquic_mode")
            == "asyncio_post_send_same_clock_receipt_v8_1",
            "early_send_tolerance_unchanged": pacing.get("early_send_tolerance_ns") == 0,
            "tool_root_exact": config.get("tool_root")
            == "runs/tools/r2-quic-controlled-v8-1-r2",
            "binding_version_exact": binding.get("binding_version")
            == "flow_probe_r2_quic_tool_binding_v8_1",
            "base_tool_root_exact": binding.get("base_tool_root")
            == "runs/tools/r2-quic-controlled-v6",
            "patch_hash_bound": binding.get("pacing_patch_sha256")
            == EXPECTED_PATCH_SHA256,
            "overlay_hash_bound": binding.get("aioquic_overlay_tree_sha256")
            == EXPECTED_OVERLAY_SHA256,
            "protocol_hash_bound": binding.get("aioquic_patched_protocol_sha256")
            == EXPECTED_PROTOCOL_SHA256,
            "field_root_exact": config.get("field_output_root")
            == "runs/data-raw/r2-quic-controlled-field-userspace-v8-1",
            "formal_root_exact": config.get("formal_output_root")
            == "runs/data-raw/r2-quic-controlled-formal-userspace-v8-1",
            "queue_acceptance_exact": config["network_contract"].get(
                "queue_drop_acceptance"
            )
            == "deterministic_capacity_causal_replay_v1",
        }
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "checks": checks,
        "projection": projection,
        "config_sha256": v5.sha256_file(config_path) if config_path.is_file() else None,
        "errors": errors,
    }


def toolchain_checks(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    tool_root = project_root / str(config["tool_root"])
    binding = config["tool_binding"]
    source_root = project_root / str(binding["binary_package_source_root"])
    verify_script = project_root / "scripts/verify_r2_quic_v6_aioquic_overlay.py"
    patch_path = project_root / str(binding["pacing_patch_path"])
    marker_path = tool_root / "versions-v8-1.txt"
    errors: list[str] = []
    checks: dict[str, bool] = {}
    live: dict[str, Any] = {}
    try:
        command = [
            str(tool_root / "aioquic-venv/bin/python"),
            str(verify_script),
            "--tool-root",
            str(tool_root),
            "--source-package-root",
            str(source_root),
            "--expected-source-tree-sha256",
            str(binding["aioquic_installed_package_tree_sha256"]),
            "--expected-buffer-sha256",
            str(binding["aioquic_buffer_sha256"]),
            "--expected-crypto-sha256",
            str(binding["aioquic_crypto_sha256"]),
            "--expected-protocol-sha256",
            str(binding["aioquic_patched_protocol_sha256"]),
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(tool_root / "aioquic-overlay")
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        )
        live = json.loads(completed.stdout)
        marker = marker_path.read_text(encoding="utf-8")
        overlay_count, overlay_sha = overlay.tree_sha256(tool_root / "aioquic-overlay/aioquic")
        checks = {
            "patch_file_exact": v5.sha256_file(patch_path) == EXPECTED_PATCH_SHA256,
            "live_overlay_verification": completed.returncode == 0
            and live.get("valid") is True,
            "overlay_tree_exact": overlay_count == 36
            and overlay_sha == EXPECTED_OVERLAY_SHA256,
            "protocol_file_exact": v5.sha256_file(
                tool_root / "aioquic-overlay/aioquic/asyncio/protocol.py"
            )
            == EXPECTED_PROTOCOL_SHA256,
            "marker_binding_exact": (
                "v8_1_tool_binding=flow_probe_r2_quic_tool_binding_v8_1" in marker
                and f"v8_1_patch_sha256={EXPECTED_PATCH_SHA256}" in marker
                and f"v8_1_overlay_tree_sha256={EXPECTED_OVERLAY_SHA256}" in marker
                and f"v8_1_protocol_sha256={EXPECTED_PROTOCOL_SHA256}" in marker
            ),
            "quiche_client_executable": (
                tool_root / "sources/quiche-0.24.5/target/release/quiche-client"
            ).is_file(),
            "quiche_server_executable": (
                tool_root / "sources/quiche-0.24.5/target/release/quiche-server"
            ).is_file(),
        }
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "checks": checks,
        "errors": errors,
        "live_overlay_verification": live,
        "tool_root": str(tool_root),
    }


def audit_single_run(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    config_path = args.config.resolve()
    output_root = args.output_root.resolve()
    launcher_status_path = args.launcher_status_path.resolve()
    summary_path = args.summary_path.resolve()
    if summary_path.exists() or summary_path.with_suffix(summary_path.suffix + ".tmp").exists():
        print(NO_GO_STATUS, flush=True)
        return 2

    frozen_run = expected_run(args.run_index)
    expected_output_root = project_root / "runs/data-raw" / frozen_run["run_id"]
    expected_launcher_path = project_root / "runs/launchers" / frozen_run["run_id"] / "status.json"
    expected_summary_path = (
        project_root
        / "runs/audits"
        / f"{frozen_run['run_id']}-single-gate-summary-v2.json"
    )
    expected_config_path = (
        project_root / "configs/r2_quic_controlled_deterministic_queue_drop_v8_1.json"
    )
    identity_checks = {
        "config_path_exact": config_path == expected_config_path,
        "output_root_exact": output_root == expected_output_root,
        "launcher_path_exact": launcher_status_path == expected_launcher_path,
        "summary_path_exact": summary_path == expected_summary_path,
    }
    setup_errors: list[str] = []
    config: dict[str, Any] = {}
    config_sha256: str | None = None
    copied_config_sha256: str | None = None
    try:
        config = v5.read_json(config_path)
        config_sha256 = v5.sha256_file(config_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        setup_errors.append(f"配置读取失败：{type(error).__name__}: {error}")
    copied_path = output_root / "collection-config.json"
    try:
        copied_config_sha256 = v5.sha256_file(copied_path)
    except OSError as error:
        setup_errors.append(f"复制配置读取失败：{type(error).__name__}: {error}")
    copied_config_exact = (
        config_sha256 is not None
        and copied_config_sha256 is not None
        and config_sha256 == copied_config_sha256
    )
    try:
        configured = config["determinism_contract"]["gate_runs"][args.run_index - 1]
        identity_checks["configured_gate_entry_exact"] = (
            configured.get("run_id") == frozen_run["run_id"]
            and configured.get("implementation") == frozen_run["implementation"]
            and int(configured.get("target_connection_index"))
            == frozen_run["target_connection_index"]
        )
    except (KeyError, IndexError, TypeError, ValueError) as error:
        setup_errors.append(f"运行身份读取失败：{type(error).__name__}: {error}")
        identity_checks["configured_gate_entry_exact"] = False

    contract = contract_checks(config_path, project_root)
    toolchain = toolchain_checks(config, project_root) if config else {"valid": False}
    launcher = v8.audit_single_launcher(
        launcher_status_path,
        output_root,
        config_path,
        frozen_run,
    )
    run_audit = v8.audit_v8_run(
        output_root,
        require_server_to_client_drop=args.run_index in {1, 3},
    )
    common_evidence = run_audit.get("common_run", {}).get("evidence", {})
    identity_checks["implementation_exact"] = (
        isinstance(common_evidence, dict)
        and common_evidence.get("implementation") == frozen_run["implementation"]
    )
    identity_valid = all(identity_checks.values())
    passed = (
        not setup_errors
        and identity_valid
        and contract.get("valid") is True
        and toolchain.get("valid") is True
        and copied_config_exact
        and launcher.get("valid") is True
        and run_audit.get("valid") is True
    )
    status = (
        SINGLE_RUN_PASS_STATUS
        if passed
        else (INVALID_STATUS if not identity_valid else NO_GO_STATUS)
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    common.atomic_json(
        summary_path,
        {
            "schema_version": SINGLE_RUN_SCHEMA,
            "status": status,
            "audit_time": datetime.now(timezone.utc).isoformat(),
            "run_index": args.run_index,
            "expected_run": frozen_run,
            "config_path": str(config_path),
            "config_sha256": config_sha256,
            "output_root": str(output_root),
            "launcher_status_path": str(launcher_status_path),
            "copied_config_sha256": copied_config_sha256,
            "copied_config_exact": copied_config_exact,
            "identity_audit": {
                "valid": identity_valid,
                "checks": identity_checks,
                "errors": [],
            },
            "contract_audit": contract,
            "toolchain_audit": toolchain,
            "launcher_audit": launcher,
            "run_audit": run_audit,
            "setup_errors": setup_errors,
            "all_conditions_passed": passed,
        },
    )
    print(status, flush=True)
    return 0 if passed else 1


def formal_audit(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    config_path = args.config.resolve()
    summary_path = args.summary_path.resolve()
    if summary_path.exists() or summary_path.with_suffix(summary_path.suffix + ".tmp").exists():
        print(NO_GO_STATUS, flush=True)
        return 2
    roots = [path.resolve() for path in args.output_roots]
    launcher_paths = [path.resolve() for path in args.launcher_status_paths]
    expected_roots = [project_root / "runs/data-raw" / item[0] for item in EXPECTED_RUNS]
    expected_launchers = [
        project_root / "runs/launchers" / item[0] / "status.json" for item in EXPECTED_RUNS
    ]
    expected_summary = (
        project_root
        / "runs/audits/r2-quic-deterministic-queue-drop-v8-1-three-gate-summary.json"
    )
    config = v5.read_json(config_path)
    contract = contract_checks(config_path, project_root)
    toolchain = toolchain_checks(config, project_root)
    config_sha256 = v5.sha256_file(config_path)
    runs = [
        v8.audit_v8_run(root, require_server_to_client_drop=index in {0, 2})
        for index, root in enumerate(roots)
    ]
    launcher_states = [v5.read_json(path) for path in launcher_paths]
    launcher = common.audit_launcher_contract(
        launcher_states,
        roots,
        [item[0] for item in EXPECTED_RUNS],
        [path.parent.name for path in launcher_paths],
        "flow_probe_r2_quic_launcher_v4",
    )
    copied_config_exact = all(
        v5.sha256_file(root / "collection-config.json") == config_sha256 for root in roots
    )
    implementations = [
        run.get("common_run", {}).get("evidence", {}).get("implementation") for run in runs
    ]
    responses = [
        run.get("common_run", {}).get("evidence", {}).get("response_sha256") for run in runs
    ]
    identity_exact = (
        roots == expected_roots
        and launcher_paths == expected_launchers
        and summary_path == expected_summary
        and implementations == [item[1] for item in EXPECTED_RUNS]
    )
    cross_run = {
        "response_sha256_consistent": all(responses) and len(set(responses)) == 1,
        "implementations_covered": set(implementations) == {"aioquic", "quiche"},
        "run1_and_run3_capacity_drop": all(
            runs[index]
            .get("event_audit", {})
            .get("directions", {})
            .get("server_to_client", {})
            .get("queue_drop_packets", 0)
            >= 1
            for index in (0, 2)
        ),
    }
    passed = (
        identity_exact
        and contract.get("valid") is True
        and toolchain.get("valid") is True
        and copied_config_exact
        and launcher.get("valid") is True
        and all(run.get("valid") is True for run in runs)
        and all(cross_run.values())
    )
    status = GO_STATUS if passed else (INVALID_STATUS if not identity_exact else NO_GO_STATUS)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    common.atomic_json(
        summary_path,
        {
            "schema_version": THREE_RUN_SCHEMA,
            "status": status,
            "audit_time": datetime.now(timezone.utc).isoformat(),
            "config_path": str(config_path),
            "config_sha256": config_sha256,
            "output_roots": [str(path) for path in roots],
            "launcher_status_paths": [str(path) for path in launcher_paths],
            "identity_exact": identity_exact,
            "contract_audit": contract,
            "toolchain_audit": toolchain,
            "copied_config_exact": copied_config_exact,
            "launcher_audit": launcher,
            "runs": runs,
            "cross_run_checks": cross_run,
            "all_conditions_passed": passed,
        },
    )
    print(status, flush=True)
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check-contract-only", action="store_true")
    parser.add_argument("--check-toolchain", action="store_true")
    parser.add_argument("--single-run", action="store_true")
    parser.add_argument("--run-index", type=int, choices=(1, 2, 3))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--launcher-status-path", type=Path)
    parser.add_argument("--output-roots", type=Path, nargs=3)
    parser.add_argument("--launcher-status-paths", type=Path, nargs=3)
    parser.add_argument("--summary-path", type=Path)
    args = parser.parse_args()
    if args.check_contract_only:
        result = contract_checks(args.config.resolve(), args.project_root.resolve())
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["valid"] else 1
    if args.check_toolchain:
        config = v5.read_json(args.config.resolve())
        result = {
            "contract": contract_checks(args.config.resolve(), args.project_root.resolve()),
            "toolchain": toolchain_checks(config, args.project_root.resolve()),
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["contract"]["valid"] and result["toolchain"]["valid"] else 1
    if args.single_run:
        if (
            args.run_index is None
            or args.output_root is None
            or args.launcher_status_path is None
            or args.summary_path is None
        ):
            raise SystemExit("单轮审计缺少运行序号、输出根、启动器状态或摘要路径")
        return audit_single_run(args)
    if not args.output_roots or not args.launcher_status_paths or not args.summary_path:
        raise SystemExit("三轮审计必须提供三份输出根、启动器状态和唯一摘要路径")
    return formal_audit(args)


if __name__ == "__main__":
    raise SystemExit(main())
