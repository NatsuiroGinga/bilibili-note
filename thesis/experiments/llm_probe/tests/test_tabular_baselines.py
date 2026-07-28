import gzip
import json
from pathlib import Path

import pytest
from frozen_protocol_fixture import refresh_artifact_hash, write_frozen_protocol_fixture

import flow_probe.tabular_baselines as tabular_baselines
from flow_probe.frozen_protocol import CANDIDATE_PROTOCOL_VERSION, THEORY_SELECTION_STAGE
from flow_probe.tabular_baselines import (
    TabularBaselineError,
    XGBoostDependencyError,
    run_tabular_baseline_suite,
)


def test_hgb_and_xgboost_share_frozen_inputs_order_labels_and_evaluation(
    tmp_path: Path,
) -> None:
    protocol_dir = tmp_path / "protocol"
    expected = write_frozen_protocol_fixture(protocol_dir)
    predictions_path = tmp_path / "predictions.jsonl.gz"

    result = run_tabular_baseline_suite(
        protocol_dir=protocol_dir,
        train_manifest="splits/fixture-train.jsonl",
        evaluation_manifests={"validation": "splits/fixture-validation.jsonl"},
        label_field="binary_label",
        seed=42,
        model_keys=("hgb", "xgboost"),
        predictions_path=predictions_path,
    )

    assert result.summary["model_keys"] == ["hgb", "xgboost"]
    assert result.summary["runtime"]["selected_device"] == "cpu"
    assert result.summary["runtime"]["cpu"]["model"]
    assert result.summary["runtime"]["cpu"]["execution_thread_limit"] == 1
    assert "total_memory_bytes" in result.summary["runtime"]["cpu"]
    assert "available" in result.summary["runtime"]["gpu"]
    hgb_input = result.summary["models"]["hgb"]["training_input"]
    xgboost_input = result.summary["models"]["xgboost"]["training_input"]
    assert hgb_input == xgboost_input
    assert hgb_input["sample_weight_source"] == "train_manifest_only"
    assert result.summary["input_contract"]["feature_fields"] == ["feature_a", "feature_b"]
    for model_key in ("hgb", "xgboost"):
        evaluation = result.summary["models"][model_key]["evaluations"]["validation"]
        assert evaluation["metrics"]["sample_count"] == len(expected["validation"])
        assert evaluation["metrics"]["unseen_truth_sample_count"] == 1
        assert result.cost["models"][model_key]["fit_seconds"] >= 0

    with gzip.open(predictions_path, "rt", encoding="utf-8") as source:
        rows = [json.loads(line) for line in source]
    for model_key in ("hgb", "xgboost"):
        model_rows = [row for row in rows if row["model"] == model_key]
        assert [row["sample_id"] for row in model_rows] == expected["validation"]
        assert {tuple(sorted(row["probabilities"])) for row in model_rows} == {
            ("benign", "malicious")
        }
        for row in model_rows:
            assert sum(row["probabilities"].values()) == pytest.approx(1.0, abs=1e-12, rel=0.0)


def test_runtime_capability_probe_supports_cpu_only_without_torch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_find_spec = tabular_baselines.importlib.util.find_spec

    def hide_torch(name: str, package: str | None = None) -> object:
        if name == "torch":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(tabular_baselines.importlib.util, "find_spec", hide_torch)

    capabilities = tabular_baselines.detect_runtime_capabilities()

    assert capabilities["selected_device"] == "cpu"
    assert capabilities["cpu"]["model"]
    assert (
        capabilities["cpu"]["logical_threads"] is None or capabilities["cpu"]["logical_threads"] > 0
    )
    assert capabilities["cpu"]["execution_thread_limit"] == 1
    assert capabilities["gpu"] == {
        "available": False,
        "backend": None,
        "device_count": 0,
        "devices": [],
        "probe_error": None,
    }


def test_xgboost_selection_reports_actionable_dependency_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(protocol_dir)
    original_import_module = tabular_baselines.importlib.import_module

    def fail_xgboost_import(name: str) -> object:
        if name == "xgboost":
            raise OSError("原生库不可用")
        return original_import_module(name)

    monkeypatch.setattr(tabular_baselines.importlib, "import_module", fail_xgboost_import)

    with pytest.raises(XGBoostDependencyError, match="uv sync --locked --extra gpu"):
        run_tabular_baseline_suite(
            protocol_dir=protocol_dir,
            train_manifest="splits/fixture-train.jsonl",
            evaluation_manifests={"validation": "splits/fixture-validation.jsonl"},
            label_field="binary_label",
            seed=42,
            model_keys=("xgboost",),
        )


def test_theory_selection_requires_explicit_candidate_protocol_contract(
    tmp_path: Path,
) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(
        protocol_dir,
        protocol_version=CANDIDATE_PROTOCOL_VERSION,
        status="provisional",
        phase=THEORY_SELECTION_STAGE,
    )

    result = run_tabular_baseline_suite(
        protocol_dir=protocol_dir,
        train_manifest="splits/fixture-train.jsonl",
        evaluation_manifests={"validation": "splits/fixture-validation.jsonl"},
        label_field="binary_label",
        seed=42,
        model_keys=("hgb",),
        stage=THEORY_SELECTION_STAGE,
        expected_protocol_version=CANDIDATE_PROTOCOL_VERSION,
    )

    assert result.summary["stage"] == THEORY_SELECTION_STAGE
    assert result.summary["input_contract"]["protocol_version"] == (CANDIDATE_PROTOCOL_VERSION)
    assert result.summary["input_contract"]["protocol_status"] == "provisional"
    assert result.summary["validation_budget"]["trial_index"] == 0
    assert result.summary["validation_budget"]["configuration_origin"] == "public_default"


def test_tuning_entry_rejects_test_manifest_even_when_hash_is_registered(
    tmp_path: Path,
) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(protocol_dir)
    manifest_path = protocol_dir / "splits" / "fixture-validation.jsonl"
    rows = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        row["split_id"] = "test"
    manifest_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    refresh_artifact_hash(protocol_dir, "splits/fixture-validation.jsonl")

    with pytest.raises(TabularBaselineError, match="只允许读取 split_id=validation"):
        run_tabular_baseline_suite(
            protocol_dir=protocol_dir,
            train_manifest="splits/fixture-train.jsonl",
            evaluation_manifests={"validation": "splits/fixture-validation.jsonl"},
            label_field="binary_label",
            seed=42,
            model_keys=("hgb",),
        )


def test_tuning_entry_rejects_more_than_ten_validation_trials(tmp_path: Path) -> None:
    protocol_dir = tmp_path / "protocol"
    write_frozen_protocol_fixture(protocol_dir)

    with pytest.raises(TabularBaselineError, match="0..10"):
        run_tabular_baseline_suite(
            protocol_dir=protocol_dir,
            train_manifest="splits/fixture-train.jsonl",
            evaluation_manifests={"validation": "splits/fixture-validation.jsonl"},
            label_field="binary_label",
            seed=42,
            model_keys=("hgb",),
            tuning_trial_index=11,
        )
