#!/usr/bin/env python3
"""审计 R2 QUIC v7 方向级数据报上限和唯一三轮门禁。"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import audit_r2_quic_determinism_gate as common
import audit_r2_quic_v5_gate as v5
import verify_r2_quic_v6_aioquic_overlay as overlay


GO_STATUS = "GO_TO_NEW_FIELD_MATRIX_QUIC_SEED_ONLY"
NO_GO_STATUS = "NO-GO_KEEP_QUIC_UNKNOWN"
SINGLE_RUN_PASS_STATUS = "PASS_R2_QUIC_V7_SINGLE_RUN_GATE_ONLY"
SINGLE_RUN_SCHEMA = "flow_probe_r2_quic_v7_single_run_gate_v1"
EXPECTED_RUNS = [
    ("r2-quic-directional-datagram-v7-run1-aioquic", "aioquic", 12),
    ("r2-quic-directional-datagram-v7-run2-quiche", "quiche", 32),
    ("r2-quic-directional-datagram-v7-run3-aioquic", "aioquic", 12),
]


def expected_run(run_index: int) -> dict[str, Any]:
    if not 1 <= run_index <= len(EXPECTED_RUNS):
        raise ValueError("单轮门禁序号必须为 1、2 或 3")
    run_id, implementation, target_connection_index = EXPECTED_RUNS[run_index - 1]
    return {
        "run_id": run_id,
        "implementation": implementation,
        "target_connection_index": target_connection_index,
    }


def audit_single_launcher(
    launcher_status_path: Path,
    output_root: Path,
    config_path: Path,
    frozen_run: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    state: dict[str, Any] = {}
    try:
        state = v5.read_json(launcher_status_path)
        started = common.parse_timestamp(state.get("started_at"))
        finished = common.parse_timestamp(state.get("finished_at"))
        checks = {
            "status_path_identity_exact": launcher_status_path.parent.name == frozen_run["run_id"],
            "schema_exact": state.get("schema_version") == "flow_probe_r2_quic_launcher_v4",
            "run_id_exact": state.get("run_id") == frozen_run["run_id"],
            "phase_exact": state.get("phase") == "field",
            "finished_successfully": state.get("status") == "finished"
            and state.get("driver_exit") == 0
            and state.get("tee_exit") == 0,
            "output_root_exact": Path(str(state.get("output_root", ""))).resolve() == output_root,
            "config_path_exact": Path(str(state.get("config_path", ""))).resolve() == config_path,
            "timestamps_ordered": finished >= started,
        }
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "path": str(launcher_status_path),
        "sha256": v5.sha256_file(launcher_status_path) if launcher_status_path.is_file() else None,
        "checks": checks,
        "state_identity": {
            "run_id": state.get("run_id"),
            "phase": state.get("phase"),
            "status": state.get("status"),
            "started_at": state.get("started_at"),
            "finished_at": state.get("finished_at"),
        },
        "errors": errors,
    }


def audit_single_directional_mapping(
    config: dict[str, Any],
    frozen_run: dict[str, Any],
    common_run: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    derived: dict[str, int] = {}
    reported: dict[str, Any] = {}
    try:
        implementation = str(frozen_run["implementation"])
        derived = common.expected_directional_max_datagram_bytes(config, implementation)
        evidence = common_run.get("evidence")
        run_checks = common_run.get("checks")
        if not isinstance(evidence, dict) or not isinstance(run_checks, dict):
            raise TypeError("公共审计缺少方向级证据")
        raw_reported = evidence.get("directional_datagram_audit")
        if not isinstance(raw_reported, dict):
            raise TypeError("公共审计缺少方向级映射审计")
        reported = raw_reported
        checks = {
            "implementation_exact": evidence.get("implementation") == implementation,
            "reported_audit_valid": reported.get("valid") is True,
            "reported_mapping_exact": reported.get("expected") == derived,
            "public_check_exact": run_checks.get("directional_datagram_binding_exact") is True,
        }
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "derived_from_frozen_config": derived,
        "reported": reported,
        "checks": checks,
        "errors": errors,
    }


def contract_checks(config_path: Path, project_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    try:
        config = v5.read_json(config_path)
        deterministic = config["determinism_contract"]
        endpoint = deterministic["endpoint_pacing"]
        binding = config["tool_binding"]
        network = config["network_contract"]
        runs = [
            (str(item["run_id"]), str(item["implementation"]), int(item["target_connection_index"]))
            for item in deterministic["gate_runs"]
        ]
        checks = {
            "schema_exact": config.get("schema_version")
            == "flow_probe_r2_quic_controlled_collection_userspace_v7",
            "status_frozen": config.get("status") == "directional_datagram_v7_frozen",
            "contract_version_exact": deterministic.get("contract_version")
            == "flow_probe_r2_quic_four_tuple_contract_v7",
            "launcher_exact": deterministic.get("launcher_schema_version")
            == "flow_probe_r2_quic_launcher_v4"
            and deterministic.get("launcher_implementation_reused") is True,
            "three_runs_exact": runs == EXPECTED_RUNS,
            "schedule_exact": deterministic.get("schedule_mode")
            == "work_conserving_byte_service_delay_v1",
            "timeout_exact": config.get("client_timeout_seconds") == 240,
            "tool_root_exact": config.get("tool_root") == "runs/tools/r2-quic-controlled-v6",
            "binding_exact": binding.get("binding_version") == "flow_probe_r2_quic_tool_binding_v6",
            "patch_exact": binding.get("pacing_patch_sha256") == v5.EXPECTED_PATCH_SHA256
            and v5.sha256_file(project_root / str(binding["pacing_patch_path"]))
            == v5.EXPECTED_PATCH_SHA256,
            "source_hashes_exact": all(
                binding.get(name) == value for name, value in v5.EXPECTED_SOURCE_HASHES.items()
            ),
            "package_hashes_exact": binding.get("aioquic_installed_package_tree_sha256")
            == "0b3fc8d7768afe5238ddf30a025031a614205d115eaadeb2589759bb5e9d7610"
            and binding.get("aioquic_overlay_tree_sha256")
            == "3ac9ca7dee525024ae8fad1eb63b347abfb52888ffd5f83b014d5cf47bd0e4ea"
            and binding.get("aioquic_buffer_sha256")
            == "1300527251f5be7d9a001c32a452597740dc7d619b9245e11e2a677cdd5fcf62"
            and binding.get("aioquic_crypto_sha256")
            == "64c07c18ad6a3189a770d53a847b950a6a72495157d7d8a55fe187955d9dd369"
            and binding.get("aioquic_patched_protocol_sha256")
            == "d70c3457cae59122ce5ca20a77dabf2c6e08c4074a9077aa754f24c9263ad034",
            "endpoint_exact": endpoint.get("receipt_prefix") == v5.RECEIPT_PREFIX
            and endpoint.get("receipt_schema_version") == v5.RECEIPT_SCHEMA
            and endpoint.get("aioquic_packaging") == "complete_binary_package_overlay_v1"
            and endpoint.get("early_send_tolerance_ns") == 0,
            "queue_exact": network.get("queue_capacity_bytes") == 2_097_152
            and network.get("queue_margin_max_bytes") == 1_677_721
            and network.get("queue_margin_role") == "diagnostic_only"
            and network.get("max_datagram_bytes_by_implementation")
            == {"aioquic": 1_200, "quiche": 1_350},
        }
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "checks": checks,
        "errors": errors,
        "config_sha256": v5.sha256_file(config_path) if config_path.is_file() else None,
    }


def toolchain_checks(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    tool_root = project_root / str(config["tool_root"])
    binding = config["tool_binding"]
    source_root = project_root / str(binding["binary_package_source_root"])
    verify_script = project_root / "scripts/verify_r2_quic_v6_aioquic_overlay.py"
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
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
        live = json.loads(completed.stdout)
        versions = (tool_root / "versions.txt").read_text(encoding="utf-8")
        overlay_count, overlay_sha = overlay.tree_sha256(tool_root / "aioquic-overlay/aioquic")
        checks = {
            "live_overlay_verification": completed.returncode == 0 and live.get("valid") is True,
            "overlay_tree_exact": overlay_count == 36
            and overlay_sha == binding["aioquic_overlay_tree_sha256"],
            "version_markers_exact": "v6_tool_binding=flow_probe_r2_quic_tool_binding_v6"
            in versions
            and f"v6_overlay_tree_sha256={overlay_sha}" in versions,
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
    temporary_summary = summary_path.with_suffix(summary_path.suffix + ".tmp")
    if summary_path.exists() or temporary_summary.exists():
        print(NO_GO_STATUS, flush=True)
        return 2

    setup_errors: list[str] = []
    config: dict[str, Any] = {}
    config_sha256: str | None = None
    copied_config_sha256: str | None = None
    frozen_run = expected_run(args.run_index)
    try:
        config = v5.read_json(config_path)
        config_sha256 = v5.sha256_file(config_path)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        setup_errors.append(f"配置读取失败：{type(error).__name__}: {error}")

    contract = contract_checks(config_path, project_root)
    toolchain = toolchain_checks(config, project_root)
    copied_config_path = output_root / "collection-config.json"
    try:
        copied_config_sha256 = v5.sha256_file(copied_config_path)
    except OSError as error:
        setup_errors.append(f"复制配置读取失败：{type(error).__name__}: {error}")
    copied_config_exact = (
        config_sha256 is not None
        and copied_config_sha256 is not None
        and copied_config_sha256 == config_sha256
    )

    configured_run_exact = False
    try:
        configured = config["determinism_contract"]["gate_runs"][args.run_index - 1]
        configured_run_exact = (
            configured.get("run_id") == frozen_run["run_id"]
            and configured.get("implementation") == frozen_run["implementation"]
            and int(configured.get("target_connection_index"))
            == frozen_run["target_connection_index"]
        )
    except (KeyError, IndexError, TypeError, ValueError) as error:
        setup_errors.append(f"运行身份读取失败：{type(error).__name__}: {error}")

    launcher = audit_single_launcher(
        launcher_status_path,
        output_root,
        config_path,
        frozen_run,
    )
    common_run = common.audit_run(output_root)
    pacing = v5.audit_pacing(output_root)
    directional = audit_single_directional_mapping(config, frozen_run, common_run)
    identity_checks = {
        "configured_gate_entry_exact": configured_run_exact,
        "output_root_name_exact": output_root.name == frozen_run["run_id"],
        "common_implementation_exact": common_run.get("evidence", {}).get("implementation")
        == frozen_run["implementation"],
    }
    identity = {
        "valid": all(identity_checks.values()),
        "checks": identity_checks,
        "errors": [],
    }
    passed = (
        not setup_errors
        and contract.get("valid") is True
        and toolchain.get("valid") is True
        and copied_config_exact
        and launcher.get("valid") is True
        and identity["valid"]
        and common_run.get("all_checks_passed") is True
        and pacing.get("valid") is True
        and directional.get("valid") is True
    )
    status = SINGLE_RUN_PASS_STATUS if passed else NO_GO_STATUS
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    common.atomic_json(
        summary_path,
        {
            "schema_version": SINGLE_RUN_SCHEMA,
            "status": status,
            "run_index": args.run_index,
            "expected_run": frozen_run,
            "project_root": str(project_root),
            "config_path": str(config_path),
            "config_sha256": config_sha256,
            "output_root": str(output_root),
            "launcher_status_path": str(launcher_status_path),
            "copied_config_path": str(copied_config_path),
            "copied_config_sha256": copied_config_sha256,
            "copied_config_exact": copied_config_exact,
            "contract_audit": contract,
            "toolchain_audit": toolchain,
            "identity_audit": identity,
            "launcher_audit": launcher,
            "directional_mapping_audit": directional,
            "common_run_audit": common_run,
            "pacing_audit": pacing,
            "setup_errors": setup_errors,
            "all_conditions_passed": passed,
        },
    )
    print(status, flush=True)
    return 0 if passed else 1


def formal_audit(args: argparse.Namespace) -> int:
    config_path = args.config.resolve()
    project_root = args.project_root.resolve()
    summary_path = args.summary_path.resolve()
    if summary_path.exists() or summary_path.with_suffix(summary_path.suffix + ".tmp").exists():
        print(NO_GO_STATUS, flush=True)
        return 2
    roots = [path.resolve() for path in args.output_roots]
    launcher_paths = [path.resolve() for path in args.launcher_status_paths]
    contract = contract_checks(config_path, project_root)
    toolchain = toolchain_checks(v5.read_json(config_path), project_root)
    config_sha = v5.sha256_file(config_path)
    common_runs = [common.audit_run(root) for root in roots]
    pacing_runs = [v5.audit_pacing(root) for root in roots]
    launcher_states = [v5.read_json(path) for path in launcher_paths]
    expected_ids = [item[0] for item in EXPECTED_RUNS]
    launcher_parent = launcher_paths[0].parent.parent
    discovered = sorted(
        path.name
        for path in launcher_parent.iterdir()
        if path.is_dir()
        and path.name.startswith("r2-quic-directional-datagram-v7-run")
        and (path / "status.json").is_file()
    )
    launcher = common.audit_launcher_contract(
        launcher_states, roots, expected_ids, discovered, "flow_probe_r2_quic_launcher_v4"
    )
    copied_config_exact = all(
        v5.sha256_file(root / "collection-config.json") == config_sha for root in roots
    )
    implementation_order_exact = [run["evidence"].get("implementation") for run in common_runs] == [
        item[1] for item in EXPECTED_RUNS
    ]
    cross = common.cross_run_checks(common_runs)
    passed = (
        len(set(roots)) == 3
        and contract["valid"]
        and toolchain["valid"]
        and copied_config_exact
        and launcher["valid"]
        and implementation_order_exact
        and all(run["all_checks_passed"] for run in common_runs)
        and all(run["valid"] for run in pacing_runs)
        and all(cross.values())
    )
    status = GO_STATUS if passed else NO_GO_STATUS
    common.atomic_json(
        summary_path,
        {
            "schema_version": "flow_probe_r2_quic_determinism_gate_v7",
            "status": status,
            "config_path": str(config_path),
            "config_sha256": config_sha,
            "output_roots": [str(root) for root in roots],
            "contract_audit": contract,
            "toolchain_audit": toolchain,
            "copied_config_exact": copied_config_exact,
            "launcher_audit": launcher,
            "implementation_order_exact": implementation_order_exact,
            "common_runs": common_runs,
            "pacing_runs": pacing_runs,
            "cross_run_checks": cross,
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
    if args.single_run:
        if (
            args.run_index is None
            or args.output_root is None
            or args.launcher_status_path is None
            or args.summary_path is None
        ):
            raise SystemExit(
                "单轮审计必须提供 --run-index、--output-root、"
                "--launcher-status-path 和 --summary-path"
            )
        if args.output_roots or args.launcher_status_paths:
            raise SystemExit("单轮审计不得混用三轮输入参数")
        return audit_single_run(args)
    contract = contract_checks(args.config.resolve(), args.project_root.resolve())
    if args.check_contract_only:
        print(json.dumps(contract, ensure_ascii=False, sort_keys=True))
        return 0 if contract["valid"] else 1
    if args.check_toolchain:
        toolchain = toolchain_checks(
            v5.read_json(args.config.resolve()), args.project_root.resolve()
        )
        print(
            json.dumps(
                {"contract": contract, "toolchain": toolchain}, ensure_ascii=False, sort_keys=True
            )
        )
        return 0 if contract["valid"] and toolchain["valid"] else 1
    if not args.output_roots or not args.launcher_status_paths or not args.summary_path:
        raise SystemExit("正式审计必须提供三轮输出、三份启动器状态和唯一摘要路径")
    return formal_audit(args)


if __name__ == "__main__":
    raise SystemExit(main())
