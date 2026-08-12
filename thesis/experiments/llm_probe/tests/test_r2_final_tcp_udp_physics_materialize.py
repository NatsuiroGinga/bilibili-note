from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import r2_final_tcp_udp_physics_v2_materialize as materializer


def _write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_v3_summary_binding_does_not_weaken_v2_source_lock(tmp_path: Path) -> None:
    scenario_sha256 = "1" * 64
    contract_sha256 = "2" * 64
    manifest_sha256 = "3" * 64
    counts = {
        "planned_run_count": 512,
        "completed_run_count": 512,
        "failed_run_count": 0,
        "reused_run_count": 0,
    }
    contract = {
        **counts,
        "valid_pair_count": 256,
        "scenario_source_sha256": scenario_sha256,
        "tcp_truth_contract_sha256": contract_sha256,
    }
    config = {
        "dataset_version": materializer.V3_DATASET_VERSION,
        "inputs": {"ns3_manifest": {"sha256": manifest_sha256}},
        "source_contract": contract,
    }
    state_path = _write_json(tmp_path / "matrix-state.json", {"status": "review_pending", **counts})
    summary = {
        "schema_version": materializer.V3_MATRIX_SUMMARY_SCHEMA,
        "status": "review_pending",
        "main_schema_version": materializer.MAIN_SOURCE_SCHEMA,
        "directional_semantics_version": materializer.DIRECTIONAL_SEMANTICS_VERSION,
        "directional_fields": list(materializer.DIRECTIONAL_COLUMNS),
        "valid_pair_count": 256,
        "scenario_source_sha256": scenario_sha256,
        "contract_sha256": contract_sha256,
        "manifest_sha256": manifest_sha256,
        **counts,
    }
    summary_path = _write_json(tmp_path / "matrix-summary.json", summary)
    v3_paths = {"matrix_state": state_path, "matrix_summary": summary_path}

    materializer._validate_top_contract(config, v3_paths)

    for field_name in ("scenario_source_sha256", "contract_sha256", "manifest_sha256"):
        invalid_summary = copy.deepcopy(summary)
        invalid_summary.pop(field_name)
        invalid_path = _write_json(tmp_path / f"missing-{field_name}.json", invalid_summary)
        with pytest.raises(materializer.MaterializationError, match="v3 矩阵摘要来源绑定"):
            materializer._validate_top_contract(
                config,
                {"matrix_state": state_path, "matrix_summary": invalid_path},
            )
        invalid_summary[field_name] = "f" * 64
        invalid_path = _write_json(tmp_path / f"wrong-{field_name}.json", invalid_summary)
        with pytest.raises(materializer.MaterializationError, match="v3 矩阵摘要来源绑定"):
            materializer._validate_top_contract(
                config,
                {"matrix_state": state_path, "matrix_summary": invalid_path},
            )
        invalid_summary[field_name] = "f" * 64
        invalid_path = _write_json(tmp_path / f"wrong-{field_name}.json", invalid_summary)
        with pytest.raises(materializer.MaterializationError, match="v3 矩阵摘要来源绑定"):
            materializer._validate_top_contract(
                config,
                {"matrix_state": state_path, "matrix_summary": invalid_path},
            )

    wrong_mode = copy.deepcopy(summary)
    wrong_mode["schema_version"] = "flow_probe_wrong_summary_mode"
    wrong_mode_path = _write_json(tmp_path / "wrong-mode.json", wrong_mode)
    with pytest.raises(materializer.MaterializationError, match="v3 矩阵摘要模式"):
        materializer._validate_top_contract(
            config,
            {"matrix_state": state_path, "matrix_summary": wrong_mode_path},
        )

    v2_config = copy.deepcopy(config)
    v2_config["dataset_version"] = materializer.V2_DATASET_VERSION
    v2_config["inputs"]["ns3_source_lock"] = {"sha256": "4" * 64}
    source_lock_path = _write_json(
        tmp_path / "source-lock.json",
        {
            "scenario_source_sha256": scenario_sha256,
            "contract_sha256": contract_sha256,
            "manifest_sha256": manifest_sha256,
        },
    )
    materializer._validate_top_contract(
        v2_config,
        {
            "matrix_state": state_path,
            "matrix_summary": summary_path,
            "ns3_source_lock": source_lock_path,
        },
    )
    with pytest.raises(materializer.MaterializationError, match="矩阵摘要不得冒充 v2 来源锁"):
        materializer._validate_top_contract(
            v2_config,
            {
                "matrix_state": state_path,
                "matrix_summary": summary_path,
                "ns3_source_lock": summary_path,
            },
        )
