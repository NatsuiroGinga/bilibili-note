#!/usr/bin/env python3
"""审计 R2 QUIC v5 配置、端点节奏工具和唯一三轮门禁。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import audit_r2_quic_determinism_gate as common


GO_STATUS = "GO_TO_NEW_FIELD_MATRIX_QUIC_SEED_ONLY"
NO_GO_STATUS = "NO-GO_KEEP_QUIC_UNKNOWN"
RECEIPT_PREFIX = "R2_QUIC_V5_PACING "
RECEIPT_SCHEMA = "flow_probe_r2_quic_endpoint_pacing_v5"
EXPECTED_RUNS = [
    ("r2-quic-endpoint-pacing-v5-run1-aioquic", "aioquic", 12),
    ("r2-quic-endpoint-pacing-v5-run2-quiche", "quiche", 32),
    ("r2-quic-endpoint-pacing-v5-run3-aioquic", "aioquic", 12),
]
EXPECTED_SOURCE_HASHES = {
    "quiche_client_source_sha256": (
        "0030292e29c0d58d3a864f3a621c1162be9ed92d6452cb99a6064e45d70f0f96"
    ),
    "quiche_sendto_source_sha256": (
        "76330f02a1fbf917333edb4a59687221980e31422782d5ede17d83d4ec910be0"
    ),
    "quiche_server_source_sha256": (
        "fba619a474aa51c1f1ccce8d43dd7da5792af850ea2aedaecbf8c990ff873e72"
    ),
    "aioquic_protocol_source_sha256": (
        "d87759d24c3bba979d2e27e6d4ff3dcdaa1a9395280a32352c38c1d352bab936"
    ),
}
EXPECTED_PATCH_SHA256 = "7a605aa9916c162f32d883d201ca5cd8c43435d500cba5725703d4f0d4656d25"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON 顶层必须为对象：{path}")
    return value


def contract_checks(config_path: Path, project_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    try:
        config = read_json(config_path)
        deterministic = config["determinism_contract"]
        endpoint_pacing = deterministic["endpoint_pacing"]
        tool_binding = config["tool_binding"]
        network = config["network_contract"]
        gate_runs = [
            (
                str(item["run_id"]),
                str(item["implementation"]),
                int(item["target_connection_index"]),
            )
            for item in deterministic["gate_runs"]
        ]
        checks = {
            "schema_exact": config.get("schema_version")
            == "flow_probe_r2_quic_controlled_collection_userspace_v5",
            "status_frozen": config.get("status") == "endpoint_pacing_v5_frozen",
            "contract_version_exact": deterministic.get("contract_version")
            == "flow_probe_r2_quic_four_tuple_contract_v5",
            "launcher_reuse_explicit": deterministic.get("launcher_schema_version")
            == "flow_probe_r2_quic_launcher_v4"
            and deterministic.get("launcher_implementation_reused") is True,
            "schedule_exact": deterministic.get("schedule_mode")
            == "work_conserving_byte_service_delay_v1",
            "three_runs_exact": gate_runs == EXPECTED_RUNS,
            "timeout_exact": config.get("client_timeout_seconds") == 240,
            "tool_root_is_v5": config.get("tool_root") == "runs/tools/r2-quic-controlled-v5",
            "versions_exact": (
                tool_binding.get("quiche_version") == "0.24.5"
                and tool_binding.get("aioquic_version") == "1.3.0"
            ),
            "source_hashes_exact": all(
                tool_binding.get(name) == expected
                for name, expected in EXPECTED_SOURCE_HASHES.items()
            ),
            "patch_hash_bound": tool_binding.get("pacing_patch_sha256") == EXPECTED_PATCH_SHA256,
            "patch_file_exact": sha256_file(project_root / str(tool_binding["pacing_patch_path"]))
            == EXPECTED_PATCH_SHA256,
            "endpoint_receipt_exact": (
                endpoint_pacing.get("receipt_prefix") == RECEIPT_PREFIX
                and endpoint_pacing.get("receipt_schema_version") == RECEIPT_SCHEMA
                and endpoint_pacing.get("early_send_tolerance_ns") == 0
                and endpoint_pacing.get("late_send_role") == "diagnostic_only"
                and endpoint_pacing.get("require_client_receipt") is True
                and endpoint_pacing.get("require_server_receipt") is True
            ),
            "queue_contract_exact": (
                network.get("queue_capacity_unit") == "bytes"
                and network.get("queue_capacity_bytes") == 2_097_152
                and network.get("queue_margin_max_bytes") == 1_677_721
                and network.get("queue_margin_role") == "diagnostic_only"
                and network.get("max_datagram_bytes_by_implementation")
                == {"aioquic": 1_200, "quiche": 1_350}
                and network.get("udp_receive_buffer_bytes") == 65_535
            ),
        }
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "checks": checks,
        "errors": errors,
        "config_sha256": sha256_file(config_path) if config_path.is_file() else None,
    }


def toolchain_checks(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    tool_root = project_root / str(config["tool_root"])
    versions_path = tool_root / "versions.txt"
    errors: list[str] = []
    checks: dict[str, bool] = {}
    try:
        versions = versions_path.read_text(encoding="utf-8")
        expected_markers = [
            "aioquic=1.3.0",
            "quiche=0.24.5",
            "v5_tool_binding=flow_probe_r2_quic_tool_binding_v5",
            f"v5_pacing_patch_sha256={EXPECTED_PATCH_SHA256}",
        ]
        checks = {
            "tool_root_exists": tool_root.is_dir(),
            "version_markers_exact": all(marker in versions for marker in expected_markers),
            "aioquic_python_executable": (tool_root / "aioquic-venv/bin/python").is_file(),
            "quiche_client_executable": (
                tool_root / "sources/quiche-0.24.5/target/release/quiche-client"
            ).is_file(),
            "quiche_server_executable": (
                tool_root / "sources/quiche-0.24.5/target/release/quiche-server"
            ).is_file(),
            "patched_aioquic_source": "R2_QUIC_V5_PACING"
            in (tool_root / "sources/aioquic-1.3.0/src/aioquic/asyncio/protocol.py").read_text(
                encoding="utf-8"
            ),
            "patched_quiche_source": "R2_QUIC_V5_PACING"
            in (tool_root / "sources/quiche-0.24.5/apps/src/sendto.rs").read_text(encoding="utf-8"),
        }
    except (OSError, TypeError, ValueError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": bool(checks) and all(checks.values()) and not errors,
        "checks": checks,
        "errors": errors,
        "tool_root": str(tool_root),
    }


def pacing_receipts(path: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        marker = raw.find(RECEIPT_PREFIX)
        if marker < 0:
            continue
        value = json.loads(raw[marker + len(RECEIPT_PREFIX) :])
        if not isinstance(value, dict):
            raise TypeError("节奏收据必须为 JSON 对象")
        receipts.append(value)
    return receipts


def audit_receipt_stream(
    receipts: list[dict[str, Any]],
    *,
    implementation: str,
    endpoint_role: str,
    expected_packets: int,
    expected_bytes: int,
    max_datagram_bytes: int,
    require_any_pacing_requested: bool,
) -> dict[str, Any]:
    errors: list[str] = []
    lateness: list[int] = []
    try:
        if not receipts:
            raise ValueError("节奏收据为空")
        for index, receipt in enumerate(receipts):
            if receipt.get("schema_version") != RECEIPT_SCHEMA:
                raise ValueError(f"第 {index} 条收据模式错误")
            if receipt.get("implementation") != implementation:
                raise ValueError(f"第 {index} 条实现身份错误")
            if receipt.get("endpoint_role") != endpoint_role:
                raise ValueError(f"第 {index} 条端点角色错误")
            if int(receipt.get("sequence", -1)) != index:
                raise ValueError(f"第 {index} 条序号不连续")
            planned = int(receipt["planned_monotonic_ns"])
            actual = int(receipt["actual_monotonic_ns"])
            reported_lateness = int(receipt["lateness_ns"])
            packet_bytes = int(receipt["packet_bytes"])
            if planned <= 0 or actual < planned:
                raise ValueError(f"第 {index} 条出现提前发送或无效时刻")
            if reported_lateness != actual - planned:
                raise ValueError(f"第 {index} 条迟发量不闭合")
            if not 0 < packet_bytes <= max_datagram_bytes:
                raise ValueError(f"第 {index} 条数据报大小越界")
            lateness.append(reported_lateness)
        if require_any_pacing_requested and not any(
            receipt.get("pacing_requested") is True for receipt in receipts
        ):
            raise ValueError("端点没有产生任何带 SendInfo.at 的节奏收据")
        if len(receipts) != expected_packets:
            raise ValueError("节奏收据包数与代理输入不一致")
        if sum(int(receipt["packet_bytes"]) for receipt in receipts) != expected_bytes:
            raise ValueError("节奏收据字节数与代理输入不一致")
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return {
        "valid": not errors,
        "receipt_count": len(receipts),
        "receipt_bytes": sum(int(item.get("packet_bytes", 0)) for item in receipts),
        "pacing_requested_count": sum(
            int(item.get("pacing_requested") is True) for item in receipts
        ),
        "max_lateness_ns": max(lateness, default=None),
        "mean_lateness_ns": (sum(lateness) / len(lateness) if lateness else None),
        "errors": errors,
    }


def audit_pacing(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    result: dict[str, Any] = {"valid": False, "errors": errors}
    try:
        connection_roots = [
            path.parent
            for path in (root / "connections").glob("*/status.json")
            if read_json(path).get("status") == "finished"
        ]
        if len(connection_roots) != 1:
            raise ValueError("门禁输出必须恰有一个完成连接")
        connection_root = connection_roots[0]
        state = read_json(connection_root / "status.json")
        stats = read_json(connection_root / "proxy-stats.json")
        client_implementation = str(state["implementation"])
        max_client_datagram = 1_200 if client_implementation == "aioquic" else 1_350
        directions = stats["directions"]
        client = audit_receipt_stream(
            pacing_receipts(connection_root / "client.log"),
            implementation=client_implementation,
            endpoint_role="client",
            expected_packets=int(directions["client_to_server"]["received_packets"]),
            expected_bytes=int(directions["client_to_server"]["received_bytes"]),
            max_datagram_bytes=max_client_datagram,
            require_any_pacing_requested=client_implementation == "quiche",
        )
        server = audit_receipt_stream(
            pacing_receipts(connection_root / "server.log"),
            implementation="quiche",
            endpoint_role="server",
            expected_packets=int(directions["server_to_client"]["received_packets"]),
            expected_bytes=int(directions["server_to_client"]["received_bytes"]),
            max_datagram_bytes=1_350,
            require_any_pacing_requested=True,
        )
        result.update(
            {
                "valid": client["valid"] and server["valid"],
                "connection_id": state["connection_id"],
                "client": client,
                "server": server,
            }
        )
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    return result


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
    toolchain = toolchain_checks(read_json(config_path), project_root)
    expected_config_sha256 = sha256_file(config_path)
    common_runs = [common.audit_run(root) for root in roots]
    pacing_runs = [audit_pacing(root) for root in roots]
    launcher_states = [read_json(path) for path in launcher_paths]
    expected_ids = [item[0] for item in EXPECTED_RUNS]
    launcher_parent = launcher_paths[0].parent.parent
    discovered_ids = sorted(
        path.name
        for path in launcher_parent.iterdir()
        if path.is_dir()
        and path.name.startswith("r2-quic-endpoint-pacing-v5-run")
        and (path / "status.json").is_file()
    )
    launcher = common.audit_launcher_contract(
        launcher_states,
        roots,
        expected_ids,
        discovered_ids,
        "flow_probe_r2_quic_launcher_v4",
    )
    copied_config_exact = all(
        sha256_file(root / "collection-config.json") == expected_config_sha256 for root in roots
    )
    implementation_order_exact = [run["evidence"].get("implementation") for run in common_runs] == [
        item[1] for item in EXPECTED_RUNS
    ]
    cross = common.cross_run_checks(common_runs)
    all_conditions = (
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
    status = GO_STATUS if all_conditions else NO_GO_STATUS
    summary = {
        "schema_version": "flow_probe_r2_quic_determinism_gate_v5",
        "status": status,
        "config_path": str(config_path),
        "config_sha256": expected_config_sha256,
        "output_roots": [str(root) for root in roots],
        "contract_audit": contract,
        "toolchain_audit": toolchain,
        "copied_config_exact": copied_config_exact,
        "launcher_audit": launcher,
        "implementation_order_exact": implementation_order_exact,
        "common_runs": common_runs,
        "pacing_runs": pacing_runs,
        "cross_run_checks": cross,
        "all_conditions_passed": all_conditions,
    }
    common.atomic_json(summary_path, summary)
    print(status, flush=True)
    return 0 if all_conditions else 1


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check-contract-only", action="store_true")
    parser.add_argument("--check-toolchain", action="store_true")
    parser.add_argument("--output-roots", type=Path, nargs=3)
    parser.add_argument("--launcher-status-paths", type=Path, nargs=3)
    parser.add_argument("--summary-path", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    contract = contract_checks(args.config.resolve(), args.project_root.resolve())
    if args.check_contract_only:
        print(json.dumps(contract, ensure_ascii=False, sort_keys=True))
        return 0 if contract["valid"] else 1
    if args.check_toolchain:
        toolchain = toolchain_checks(read_json(args.config.resolve()), args.project_root.resolve())
        result = {"contract": contract, "toolchain": toolchain}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if contract["valid"] and toolchain["valid"] else 1
    if not args.output_roots or not args.launcher_status_paths or not args.summary_path:
        raise SystemExit("正式审计必须提供三轮输出、三份启动器状态和唯一摘要路径")
    return formal_audit(args)


if __name__ == "__main__":
    raise SystemExit(main())
