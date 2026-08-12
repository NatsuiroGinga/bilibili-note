from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from flow_probe.r2_ns3_protocol_dynamics_v2_parallel_runner import (
    _load_reused,
)
from flow_probe.r2_ns3_protocol_dynamics_v2_runner import FormalMatrixError
from flow_probe.r2_ns3_tcp_truth_v2_runner import (
    DIRECTIONAL_COLUMNS,
    MAIN_COLUMNS,
    MAIN_SCHEMA,
    RECEIPT_SCHEMA,
    TCP_FIELD_CLOSURE_SCHEMA,
    TCP_PARAMS_SCHEMA,
    UDP_SINGLE_FIELD_CLOSURE_SCHEMA,
    UDP_PARAMS_SCHEMA,
    TcpTruthV2Error,
    _load_manifest,
    _load_selection,
    _validate_params_closure_schema,
    _validate_directional_row,
    _validate_main,
)


def test_directional_contract_accepts_tcp_ack_direction_and_unidirectional_udp() -> None:
    tcp = {
        "orig_bytes": "1200",
        "resp_bytes": "0",
        "orig_pkts": "1",
        "resp_pkts": "1",
        "orig_ip_bytes": "1240",
        "resp_ip_bytes": "40",
    }
    udp = {
        "orig_bytes": "1200",
        "resp_bytes": "0",
        "orig_pkts": "1",
        "resp_pkts": "0",
        "orig_ip_bytes": "1228",
        "resp_ip_bytes": "0",
    }

    assert _validate_directional_row(tcp, "TCP") == {
        name: int(tcp[name]) for name in DIRECTIONAL_COLUMNS
    }
    assert _validate_directional_row(udp, "UDP") == {
        name: int(udp[name]) for name in DIRECTIONAL_COLUMNS
    }


def test_directional_contract_rejects_fabricated_udp_response() -> None:
    row = {
        "orig_bytes": "1200",
        "resp_bytes": "0",
        "orig_pkts": "1",
        "resp_pkts": "1",
        "orig_ip_bytes": "1228",
        "resp_ip_bytes": "28",
    }

    with pytest.raises(TcpTruthV2Error, match="不得伪造响应方向流量"):
        _validate_directional_row(row, "UDP")


def test_legacy_main_header_is_rejected_before_row_parsing(tmp_path: Path) -> None:
    legacy_columns = [name for name in MAIN_COLUMNS if name not in DIRECTIONAL_COLUMNS]
    path = tmp_path / "legacy-main.csv"
    path.write_text(",".join(legacy_columns) + "\n", encoding="utf-8")

    with pytest.raises(TcpTruthV2Error, match="字段名称或顺序不符"):
        _validate_main(path, cast(Any, object()), "a" * 64)


def test_parallel_reuse_rejects_legacy_receipt(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    run = SimpleNamespace(
        transport_family="TCP",
        physics_group_sha256="b" * 64,
    )
    run_dir = root / "runs" / f"0000-tcp-{run.physics_group_sha256[:12]}"
    run_dir.mkdir(parents=True)
    (root / "matrix-state.json").write_text(
        json.dumps({"status": "failed", "completed_run_count": 1}),
        encoding="utf-8",
    )
    (run_dir / "receipt.json").write_text(
        json.dumps(
            {
                "schema_version": RECEIPT_SCHEMA.removesuffix("v2") + "v1",
                "status": "pass",
                "coverage": "0000-tcp",
                "physics_group_sha256": run.physics_group_sha256,
                "scenario_source_sha256": "c" * 64,
                "contract_sha256": "d" * 64,
                "main_schema_version": MAIN_SCHEMA.removesuffix("v3") + "v2",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(FormalMatrixError, match="不是六方向主模式"):
        _load_reused([root], [cast(Any, run)], "c" * 64, "d" * 64)


def test_udp_single_selection_requires_exact_frozen_manifest_row() -> None:
    project_root = Path(__file__).resolve().parents[1]
    manifest = _load_manifest(
        project_root
        / "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl"
    )
    manifest_index, udp_run = next(
        (index, run)
        for index, run in enumerate(manifest)
        if run.transport_family == "UDP"
    )
    legacy_closure = {
        "schema_version": TCP_FIELD_CLOSURE_SCHEMA,
        "expected_manifest_sha256": (
            "d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111"
        ),
        "selected_runs": [
            {
                "coverage": "legacy_udp_probe",
                "physics_group_sha256": udp_run.physics_group_sha256,
            }
        ],
    }
    with pytest.raises(TcpTruthV2Error, match="必须恰选5个 TCP"):
        _load_selection(legacy_closure, manifest)

    item = {
        "coverage": "frozen_udp_probe",
        "manifest_index": manifest_index,
        "physics_group_sha256": udp_run.physics_group_sha256,
        "transport_family": "UDP",
    }
    closure = {
        "schema_version": UDP_SINGLE_FIELD_CLOSURE_SCHEMA,
        "expected_manifest_sha256": (
            "d867c05013ff9c566d965ec3115bcefe6c905cca69865b042eb81f56e012a111"
        ),
        "manifest_path": (
            "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl"
        ),
        "selection_policy": "frozen_manifest_exact_udp_row",
        "selected_runs": [item],
    }
    assert _load_selection(closure, manifest) == [("frozen_udp_probe", udp_run)]

    fabricated = {**closure, "selected_runs": [{**item, "physics_group_sha256": "0" * 64}]}
    with pytest.raises(TcpTruthV2Error, match="未精确绑定冻结清单行"):
        _load_selection(fabricated, manifest)

    duplicated = {**closure, "selected_runs": [item, item]}
    with pytest.raises(TcpTruthV2Error, match="必须恰选1个运行"):
        _load_selection(duplicated, manifest)


def test_params_schema_is_bound_to_same_protocol_closure() -> None:
    _validate_params_closure_schema(
        UDP_PARAMS_SCHEMA, UDP_SINGLE_FIELD_CLOSURE_SCHEMA
    )
    _validate_params_closure_schema(TCP_PARAMS_SCHEMA, TCP_FIELD_CLOSURE_SCHEMA)

    with pytest.raises(TcpTruthV2Error, match="协议不一致"):
        _validate_params_closure_schema(
            UDP_PARAMS_SCHEMA, TCP_FIELD_CLOSURE_SCHEMA
        )
    with pytest.raises(TcpTruthV2Error, match="协议不一致"):
        _validate_params_closure_schema(
            TCP_PARAMS_SCHEMA, UDP_SINGLE_FIELD_CLOSURE_SCHEMA
        )
