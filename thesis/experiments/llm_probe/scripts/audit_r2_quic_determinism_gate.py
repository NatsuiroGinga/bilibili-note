#!/usr/bin/env python3
"""审计恰好三个 R2 QUIC 确定性修复输出根。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


GO_STATUS = "GO_TO_INDEPENDENT_REVIEW"
NO_GO_STATUS = "NO-GO_KEEP_QUIC_UNKNOWN"
EXPECTED_RESPONSE_BYTES = 67_108_864
EXPECTED_DIRECTION_SEEDS = {
    "client_to_server": 373387841787797959,
    "server_to_client": 7996260466250834367,
}
EXPECTED_ENDPOINTS = {
    "client": ["127.0.0.1", 21012],
    "proxy_listen": ["127.0.0.1", 20012],
    "proxy_upstream": ["127.0.0.1", 22012],
    "reference_server": ["127.0.0.1", 4433],
}
EXPECTED_SCHEDULE_MODE = "fixed_sequence_epoch_v1"


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON 顶层必须为对象：{path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def count_exact_payload_decrypt_error(value: Any) -> int:
    if isinstance(value, dict):
        return sum(count_exact_payload_decrypt_error(child) for child in value.values())
    if isinstance(value, list):
        return sum(count_exact_payload_decrypt_error(child) for child in value)
    return int(isinstance(value, str) and value == "payload_decrypt_error")


def scan_qlog_payload_decrypt_errors(paths: list[Path]) -> int:
    total = 0
    for path in paths:
        raw = path.read_text(encoding="utf-8")
        try:
            total += count_exact_payload_decrypt_error(json.loads(raw))
            continue
        except json.JSONDecodeError:
            pass
        parsed_lines = 0
        for line in raw.splitlines():
            candidate = line.lstrip("\x1e").strip()
            if not candidate:
                continue
            try:
                total += count_exact_payload_decrypt_error(json.loads(candidate))
                parsed_lines += 1
            except json.JSONDecodeError:
                continue
        if parsed_lines == 0:
            raise RuntimeError(f"qlog 无法解析：{path}")
    return total


def stable_four_tuple(connection_id: str) -> dict[str, Any]:
    return {
        "contract_version": "flow_probe_r2_quic_four_tuple_contract_v1",
        "connection_id": connection_id,
        "schedule_mode": EXPECTED_SCHEDULE_MODE,
        "client_to_proxy": {
            "source_host": EXPECTED_ENDPOINTS["client"][0],
            "source_port": EXPECTED_ENDPOINTS["client"][1],
            "destination_host": EXPECTED_ENDPOINTS["proxy_listen"][0],
            "destination_port": EXPECTED_ENDPOINTS["proxy_listen"][1],
        },
        "proxy_to_server": {
            "source_host": EXPECTED_ENDPOINTS["proxy_upstream"][0],
            "source_port": EXPECTED_ENDPOINTS["proxy_upstream"][1],
            "destination_host": EXPECTED_ENDPOINTS["reference_server"][0],
            "destination_port": EXPECTED_ENDPOINTS["reference_server"][1],
        },
    }


def audit_run(output_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    checks: dict[str, bool] = {}
    evidence: dict[str, Any] = {}
    result = {
        "output_root": str(output_root),
        "checks": checks,
        "evidence": evidence,
        "errors": errors,
    }
    try:
        if not output_root.is_dir():
            raise FileNotFoundError(f"输出根不存在：{output_root}")
        run_state = read_json(output_root / "run-state.json")
        collection_config_path = output_root / "collection-config.json"
        collection_config = read_json(collection_config_path)
        collection_config_sha256 = sha256_file(collection_config_path)

        connections_root = output_root / "connections"
        if not connections_root.is_dir():
            raise FileNotFoundError(f"连接目录不存在：{connections_root}")
        connection_roots = sorted(
            path for path in connections_root.iterdir() if path.is_dir()
        )
        if len(connection_roots) != 1:
            raise RuntimeError(f"连接目录必须恰好一个：{len(connection_roots)}")
        connection_root = connection_roots[0]
        state = read_json(connection_root / "status.json")
        impairment_path = connection_root / "impairment-config.json"
        four_tuple_path = connection_root / "four-tuple-contract.json"
        endpoint_path = connection_root / "endpoint-contract.json"
        proxy_ready_path = connection_root / "proxy-ready.json"
        proxy_stats_path = connection_root / "proxy-stats.json"
        exit_path = connection_root / "exit-code.json"
        impairment = read_json(impairment_path)
        four_tuple = read_json(four_tuple_path)
        endpoint = read_json(endpoint_path)
        proxy_ready = read_json(proxy_ready_path)
        proxy_stats = read_json(proxy_stats_path)
        exit_codes = read_json(exit_path)

        impairment_sha256 = sha256_file(impairment_path)
        four_tuple_sha256 = sha256_file(four_tuple_path)
        connection_id = str(state.get("connection_id", ""))
        response_root = connection_root / "response"
        responses = sorted(path for path in response_root.iterdir() if path.is_file())
        if len(responses) != 1:
            raise RuntimeError(f"响应文件必须恰好一个：{len(responses)}")
        response = responses[0]
        response_sha256 = sha256_file(response)
        qlog_root = connection_root / "qlog"
        qlogs = sorted(
            path
            for path in qlog_root.iterdir()
            if path.is_file() and path.stat().st_size > 0
        )
        if not qlogs:
            raise RuntimeError("qlog 文件缺失")
        payload_decrypt_error = scan_qlog_payload_decrypt_errors(qlogs)

        directions = proxy_stats.get("directions")
        if not isinstance(directions, dict):
            raise TypeError("代理方向统计缺失")
        direction_rows = [
            directions["client_to_server"],
            directions["server_to_client"],
        ]
        random_drop_packets = sum(int(row["random_drop_packets"]) for row in direction_rows)
        queue_drop_packets = sum(int(row["queue_drop_packets"]) for row in direction_rows)
        send_error_packets = sum(int(row["send_error_packets"]) for row in direction_rows)
        queued_packets_at_shutdown = sum(
            int(row["queued_packets_at_shutdown"]) for row in direction_rows
        )
        scheduled_packets_at_shutdown = int(
            proxy_stats["scheduled_packets_at_shutdown"]
        )

        expected_four_tuple = stable_four_tuple(connection_id)
        fixed_endpoints = state.get("fixed_endpoints")
        direction_seeds = state.get("direction_seeds")
        exit_code_values = {
            name: int(exit_codes[name])
            for name in (
                "client_exit",
                "capture_exit",
                "proxy_exit",
                "server_exit",
            )
        }
        checks.update(
            {
                "natural_completion": (
                    run_state.get("status") == "finished"
                    and state.get("status") == "finished"
                    and state.get("client_natural_completion") is True
                ),
                "frozen_scientific_parameters": (
                    state.get("implementation") == "aioquic"
                    and state.get("profile")
                    == {
                        "id": "p03",
                        "delay_ms": 50,
                        "jitter_ms": 0.0,
                        "loss_percent": 0.0,
                        "rate_mbit": 20,
                        "seed": 43,
                    }
                    and state.get("payload")
                    == {"id": "bulk", "bytes": EXPECTED_RESPONSE_BYTES}
                    and state.get("seed") == 43
                    and collection_config.get("client_timeout_seconds") == 240
                    and collection_config.get("network_contract", {}).get(
                        "queue_limit_packets"
                    )
                    == 1000
                ),
                "response_bytes": response.stat().st_size == EXPECTED_RESPONSE_BYTES,
                "response_state_receipt": (
                    state.get("response", {}).get("bytes") == EXPECTED_RESPONSE_BYTES
                    and state.get("response", {}).get("sha256") == response_sha256
                ),
                "payload_decrypt_error_zero": payload_decrypt_error == 0,
                "qlog_state_receipt": (
                    state.get("qlog_field_audit", {}).get("payload_decrypt_error")
                    == payload_decrypt_error
                ),
                "all_exit_codes_zero": all(
                    value == 0 for value in exit_code_values.values()
                ),
                "random_drop_zero": random_drop_packets == 0,
                "queue_drop_zero": queue_drop_packets == 0,
                "send_error_zero": send_error_packets == 0,
                "shutdown_queue_zero": (
                    queued_packets_at_shutdown == 0
                    and scheduled_packets_at_shutdown == 0
                ),
                "collection_config_hash_bound": (
                    state.get("collection_config_sha256")
                    == collection_config_sha256
                    and impairment.get("collection_config_sha256")
                    == collection_config_sha256
                    and endpoint.get("collection_config_sha256")
                    == collection_config_sha256
                ),
                "impairment_config_hash_bound": (
                    state.get("impairment_config_sha256") == impairment_sha256
                    and endpoint.get("impairment_config_sha256")
                    == impairment_sha256
                    and proxy_ready.get("config_sha256") == impairment_sha256
                    and proxy_stats.get("config_sha256") == impairment_sha256
                ),
                "four_tuple_hash_bound": (
                    state.get("four_tuple_contract_sha256") == four_tuple_sha256
                    and impairment.get("four_tuple_contract_sha256")
                    == four_tuple_sha256
                    and endpoint.get("four_tuple_contract_sha256")
                    == four_tuple_sha256
                ),
                "four_tuple_exact": four_tuple == expected_four_tuple,
                "direction_seeds_exact": (
                    direction_seeds == EXPECTED_DIRECTION_SEEDS
                    and impairment.get("direction_seeds") == EXPECTED_DIRECTION_SEEDS
                    and {
                        name: proxy_stats["directions"][name]["seed"]
                        for name in EXPECTED_DIRECTION_SEEDS
                    }
                    == EXPECTED_DIRECTION_SEEDS
                ),
                "fixed_endpoints_exact": fixed_endpoints == EXPECTED_ENDPOINTS,
                "observed_endpoints_exact": (
                    endpoint.get("expected_client_endpoint")
                    == EXPECTED_ENDPOINTS["client"]
                    and endpoint.get("observed_client_endpoint")
                    == EXPECTED_ENDPOINTS["client"]
                    and endpoint.get("expected_proxy_listen_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_listen"]
                    and endpoint.get("observed_proxy_listen_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_listen"]
                    and endpoint.get("expected_proxy_upstream_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_upstream"]
                    and endpoint.get("observed_proxy_upstream_endpoint")
                    == EXPECTED_ENDPOINTS["proxy_upstream"]
                    and endpoint.get("expected_reference_server_endpoint")
                    == EXPECTED_ENDPOINTS["reference_server"]
                    and endpoint.get("observed_reference_server_endpoint")
                    == EXPECTED_ENDPOINTS["reference_server"]
                ),
                "schedule_mode_exact": all(
                    value == EXPECTED_SCHEDULE_MODE
                    for value in (
                        state.get("schedule_mode"),
                        impairment.get("schedule_mode"),
                        four_tuple.get("schedule_mode"),
                        endpoint.get("schedule_mode"),
                        proxy_ready.get("schedule_mode"),
                        proxy_stats.get("schedule_mode"),
                    )
                ),
                "port_exclusivity_receipts": (
                    endpoint.get("port_availability_before", {}).get(
                        "exclusive_bind_succeeded"
                    )
                    is True
                    and endpoint.get("port_availability_after", {}).get(
                        "exclusive_bind_succeeded"
                    )
                    is True
                ),
                "proxy_finished_without_contract_error": (
                    proxy_stats.get("status") == "finished"
                    and proxy_stats.get("contract_error") is None
                ),
            }
        )
        endpoint_schedule_value = {
            "four_tuple": four_tuple,
            "fixed_endpoints": fixed_endpoints,
            "direction_seeds": direction_seeds,
            "schedule_mode": state.get("schedule_mode"),
        }
        evidence.update(
            {
                "connection_id": connection_id,
                "collection_config_sha256": collection_config_sha256,
                "impairment_config_sha256": impairment_sha256,
                "four_tuple_contract_sha256": four_tuple_sha256,
                "direction_seeds_sha256": canonical_sha256(direction_seeds),
                "endpoint_schedule_sha256": canonical_sha256(
                    endpoint_schedule_value
                ),
                "response_bytes": response.stat().st_size,
                "response_sha256": response_sha256,
                "payload_decrypt_error": payload_decrypt_error,
                "exit_codes": exit_code_values,
                "random_drop_packets": random_drop_packets,
                "queue_drop_packets": queue_drop_packets,
                "send_error_packets": send_error_packets,
                "queued_packets_at_shutdown": queued_packets_at_shutdown,
                "scheduled_packets_at_shutdown": scheduled_packets_at_shutdown,
                "schedule_mode": state.get("schedule_mode"),
            }
        )
    except (KeyError, IndexError, OSError, TypeError, ValueError, RuntimeError) as error:
        errors.append(f"{type(error).__name__}: {error}")
    result["all_checks_passed"] = bool(checks) and all(checks.values()) and not errors
    return result


def cross_run_checks(runs: list[dict[str, Any]]) -> dict[str, bool]:
    evidence_rows = [run["evidence"] for run in runs]

    def one_value(field: str) -> bool:
        values = [row.get(field) for row in evidence_rows]
        return all(value is not None for value in values) and len(set(values)) == 1

    return {
        "connection_id_consistent": one_value("connection_id"),
        "collection_config_sha256_consistent": one_value(
            "collection_config_sha256"
        ),
        "impairment_config_sha256_consistent": one_value(
            "impairment_config_sha256"
        ),
        "four_tuple_contract_sha256_consistent": one_value(
            "four_tuple_contract_sha256"
        ),
        "direction_seeds_sha256_consistent": one_value("direction_seeds_sha256"),
        "endpoint_schedule_sha256_consistent": one_value(
            "endpoint_schedule_sha256"
        ),
        "schedule_mode_consistent": one_value("schedule_mode"),
        "response_sha256_consistent": one_value("response_sha256"),
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-roots",
        type=Path,
        nargs=3,
        required=True,
        metavar=("RUN1", "RUN2", "RUN3"),
    )
    parser.add_argument("--summary-path", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    summary_path = args.summary_path.resolve()
    if summary_path.exists() or summary_path.with_suffix(
        summary_path.suffix + ".tmp"
    ).exists():
        print(NO_GO_STATUS, flush=True)
        return 2
    roots = [path.resolve() for path in args.output_roots]
    distinct_roots = len(set(roots)) == 3
    runs = [audit_run(root) for root in roots]
    cross_checks = cross_run_checks(runs)
    all_conditions = (
        distinct_roots
        and all(run["all_checks_passed"] for run in runs)
        and all(cross_checks.values())
    )
    status = GO_STATUS if all_conditions else NO_GO_STATUS
    summary = {
        "schema_version": "flow_probe_r2_quic_determinism_gate_v1",
        "status": status,
        "output_roots": [str(root) for root in roots],
        "three_distinct_output_roots": distinct_roots,
        "runs": runs,
        "cross_run_checks": cross_checks,
        "all_conditions_passed": all_conditions,
        "automatic_run_or_retry_performed": False,
        "artifacts_deleted": False,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(summary_path, summary)
    print(status, flush=True)
    return 0 if all_conditions else 1


if __name__ == "__main__":
    raise SystemExit(main())
