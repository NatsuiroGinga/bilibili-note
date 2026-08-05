"""共享 B0 树模型严格装载与执行入口测试。"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from flow_probe.shared_b0_tabular_baselines import (
    EXPECTED_FEATURE_FIELDS,
    EXPECTED_STAGE,
    EXPECTED_STATUS,
    LAUNCHER_EVIDENCE_FILES,
    MODEL_RUNS_DIRECTORY,
    REQUIRED_SPLITS,
    SharedB0TabularError,
    _launch_isolated_model_process,
    _validate_prepared_run_root,
    finalize_run_artifact_manifest,
    prepare_shared_b0_tabular_data,
    run_shared_b0_tabular_baseline_suite,
    run_tracked_shared_b0_tabular_baselines,
)
from flow_probe.shared_b0_view import ARTIFACT_SCHEMA_VERSION, FEATURE_COLUMNS


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _common_frame(sample_ids: list[str]) -> pd.DataFrame:
    rows = []
    for stable_order, sample_id in enumerate(sample_ids):
        values = {
            field: float((stable_order + 1) * (field_index + 1))
            for field_index, field in enumerate(EXPECTED_FEATURE_FIELDS[:8])
        }
        rows.append(
            {
                "sample_id": sample_id,
                "stable_order": stable_order,
                **values,
                **{field: 0 for field in EXPECTED_FEATURE_FIELDS[8:]},
            }
        )
    return pd.DataFrame(rows, columns=list(FEATURE_COLUMNS))


def _label_frame(sample_ids: list[str], labels: list[int]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sample_id": sample_id,
                "stable_order": stable_order,
                "text": f"该文本不得进入树模型特征-{stable_order}",
                "label": label,
            }
            for stable_order, (sample_id, label) in enumerate(zip(sample_ids, labels, strict=True))
        ]
    )


def _write_fixture(root: Path) -> None:
    split_rows = {
        "train": (["train-0", "train-1", "train-2", "train-3"], [0, 1, 0, 1]),
        "genis": (["genis-0", "genis-1"], [0, 1]),
        "tqhc2": (["tqhc2-0", "tqhc2-1"], [1, 0]),
    }
    for name, (_, common_relative, label_relative) in REQUIRED_SPLITS.items():
        sample_ids, labels = split_rows[name]
        common_path = root / common_relative
        label_path = root / label_relative
        common_path.parent.mkdir(parents=True, exist_ok=True)
        _common_frame(sample_ids).to_parquet(common_path, index=False, compression="zstd")
        _label_frame(sample_ids, labels).to_parquet(label_path, index=False, compression="zstd")

    _write_json(
        root / "manifests" / "input_binding.json",
        {"schema_version": ARTIFACT_SCHEMA_VERSION, "fixture": True},
    )
    _write_json(
        root / "manifests" / "statistics.json",
        {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "stage": EXPECTED_STAGE,
            "status": EXPECTED_STATUS,
            "candidate_count": 4,
            "validation": {"genis": {"count": 2}, "tqhc2": {"count": 2}},
        },
    )
    _refresh_publication_binding(root)


def _refresh_publication_binding(root: Path) -> None:
    artifact_paths = {
        relative
        for _, common_relative, label_relative in REQUIRED_SPLITS.values()
        for relative in (common_relative, label_relative)
    }
    artifact_paths.update({"manifests/input_binding.json", "manifests/statistics.json"})
    artifacts = {
        relative: {
            "sha256": _sha256(root / relative),
            "size_bytes": (root / relative).stat().st_size,
        }
        for relative in sorted(artifact_paths)
    }
    checksums_path = root / "manifests" / "checksums.json"
    _write_json(
        checksums_path,
        {"schema_version": ARTIFACT_SCHEMA_VERSION, "artifacts": artifacts},
    )
    _write_json(
        root / "manifests" / "freeze_manifest.json",
        {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "stage": EXPECTED_STAGE,
            "status": EXPECTED_STATUS,
            "candidate_count": 4,
            "validation_counts": {"genis": 2, "tqhc2": 2},
            "atomic_publication": True,
            "input_binding_sha256": artifacts["manifests/input_binding.json"]["sha256"],
            "checksums_sha256": _sha256(checksums_path),
        },
    )


def test_prepare_uses_exact_common_features_and_label_only_supervision(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_fixture(dataset_dir)

    inputs = prepare_shared_b0_tabular_data(dataset_dir)
    prepared = inputs.prepared

    assert prepared.protocol.phase == EXPECTED_STAGE
    assert prepared.protocol.status == EXPECTED_STATUS
    assert prepared.train.feature_fields == EXPECTED_FEATURE_FIELDS
    assert prepared.train.features.shape == (4, 16)
    assert prepared.train.labels == ("benign", "malicious", "benign", "malicious")
    assert prepared.known_labels == ("benign", "malicious")
    assert prepared.train_sample_weights.tolist() == [1.0, 1.0, 1.0, 1.0]
    assert tuple(prepared.evaluations) == ("genis", "tqhc2")
    assert not {"label", "text", "input_text"}.intersection(prepared.train.feature_fields)
    assert inputs.data_manifest["label_source"] == "每个 BERT Parquet 的 label 列"
    assert inputs.data_manifest["splits"]["train"]["sample_count"] == 4


def test_prepare_rejects_registered_artifact_hash_mismatch(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_fixture(dataset_dir)
    label_path = dataset_dir / "candidate" / "bert_train.parquet"
    labels = pd.read_parquet(label_path)
    labels.loc[0, "label"] = 1
    labels.to_parquet(label_path, index=False, compression="zstd")

    with pytest.raises(SharedB0TabularError, match="哈希不一致|大小不一致"):
        prepare_shared_b0_tabular_data(dataset_dir)


def test_prepare_rejects_rowwise_sample_id_mismatch_after_hash_refresh(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_fixture(dataset_dir)
    label_path = dataset_dir / "validation" / "genis_bert.parquet"
    labels = pd.read_parquet(label_path)
    labels.loc[:, "sample_id"] = list(reversed(labels["sample_id"].tolist()))
    labels.to_parquet(label_path, index=False, compression="zstd")
    _refresh_publication_binding(dataset_dir)

    with pytest.raises(SharedB0TabularError, match="逐行完全一致"):
        prepare_shared_b0_tabular_data(dataset_dir)


def test_prepare_rejects_duplicate_sample_id_after_hash_refresh(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_fixture(dataset_dir)
    common_path = dataset_dir / "validation" / "tqhc2_common_features.parquet"
    common = pd.read_parquet(common_path)
    common.loc[1, "sample_id"] = common.loc[0, "sample_id"]
    common.to_parquet(common_path, index=False, compression="zstd")
    _refresh_publication_binding(dataset_dir)

    with pytest.raises(SharedB0TabularError, match="sample_id 必须唯一"):
        prepare_shared_b0_tabular_data(dataset_dir)


def test_prepare_rejects_label_or_extra_column_in_common_features(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_fixture(dataset_dir)
    common_path = dataset_dir / "candidate" / "common_features.parquet"
    common = pd.read_parquet(common_path)
    common["label"] = [0, 1, 0, 1]
    common.to_parquet(common_path, index=False, compression="zstd")
    _refresh_publication_binding(dataset_dir)

    with pytest.raises(SharedB0TabularError, match="列必须严格等于"):
        prepare_shared_b0_tabular_data(dataset_dir)


def test_hgb_suite_reuses_unified_execution_evaluation_and_cost(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_fixture(dataset_dir)
    predictions_path = tmp_path / "predictions.jsonl.gz"

    result = run_shared_b0_tabular_baseline_suite(
        dataset_dir=dataset_dir,
        seed=42,
        model_keys=("hgb",),
        predictions_path=predictions_path,
    )

    assert result.summary["schema_version"] == "flow_probe_tabular_baselines_v1"
    assert result.summary["stage"] == EXPECTED_STAGE
    assert result.summary["runtime"]["selected_device"] == "cpu"
    assert result.summary["input_contract"]["feature_fields"] == list(EXPECTED_FEATURE_FIELDS)
    assert result.summary["models"]["hgb"]["training_input"]["sample_weight_source"] == (
        "train_manifest_only"
    )
    assert result.cost["models"]["hgb"]["peak_gpu_memory_bytes"] is None
    with gzip.open(predictions_path, "rt", encoding="utf-8") as source:
        predictions = [json.loads(line) for line in source]
    assert [row["evaluation"] for row in predictions] == [
        "genis",
        "genis",
        "tqhc2",
        "tqhc2",
    ]


def test_tracked_entry_rejects_existing_output_before_loading_data(tmp_path: Path) -> None:
    output_dir = tmp_path / "existing-output"
    output_dir.mkdir()

    with pytest.raises(SharedB0TabularError, match="拒绝覆盖"):
        run_tracked_shared_b0_tabular_baselines(
            dataset_dir=tmp_path / "missing-dataset",
            output_dir=output_dir,
            seed=42,
            run_name="shared-b0-tabular-test",
            model_keys=("hgb",),
        )


def test_model_launcher_uses_fresh_process_and_records_end_to_end_rss(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset-v1-shared-b0"
    _write_fixture(dataset_dir)
    model_output = tmp_path / "model-runs" / "hgb"

    manifest = _launch_isolated_model_process(
        dataset_dir=dataset_dir,
        output_dir=model_output,
        seed=42,
        model_key="hgb",
        tuning_trial_index=0,
    )

    assert manifest["model_process_id"] != os.getpid()
    assert json.loads((model_output / "run_state.json").read_text(encoding="utf-8"))["state"] == (
        "finished"
    )
    cost = json.loads((model_output / "cost.json").read_text(encoding="utf-8"))
    model_cost = cost["models"]["hgb"]
    assert model_cost["peak_process_rss_bytes_after_model"] > 0
    assert (
        model_cost["peak_process_rss_measurement_scope"]
        == "isolated_single_model_process_end_to_end"
    )


def test_prepared_run_root_accepts_only_running_launcher_evidence(tmp_path: Path) -> None:
    run_root = tmp_path / "prepared-run"
    run_root.mkdir()
    for name, relative in LAUNCHER_EVIDENCE_FILES.items():
        if name == "launcher_exit_code":
            continue
        path = run_root / relative
        if name == "launcher_state":
            _write_json(path, {"state": "running"})
        else:
            path.write_text(f"{name}\n", encoding="utf-8")

    _validate_prepared_run_root(run_root)
    (run_root / "unexpected.txt").write_text("不得接受\n", encoding="utf-8")
    with pytest.raises(SharedB0TabularError, match="额外"):
        _validate_prepared_run_root(run_root)


def test_finalizer_registers_launcher_and_both_model_subruns(tmp_path: Path) -> None:
    run_root = tmp_path / "formal-v2"
    run_root.mkdir()
    _write_json(run_root / "artifact_manifest.json", {"status": "finished", "run_id": "unit"})
    _write_json(run_root / "config_snapshot.json", {"model_keys": ["hgb", "xgboost"]})
    for name, relative in LAUNCHER_EVIDENCE_FILES.items():
        path = run_root / relative
        if name == "launcher_state":
            _write_json(path, {"state": "finished"})
        elif name == "launcher_exit_code":
            path.write_text("0\n", encoding="utf-8")
        else:
            path.write_text(f"{name}\n", encoding="utf-8")
    for model_key in ("hgb", "xgboost"):
        model_root = run_root / MODEL_RUNS_DIRECTORY / model_key
        _write_json(model_root / "run_state.json", {"state": "finished"})
        _write_json(
            model_root / "artifact_manifest.json",
            {"status": "finished", "model_key": model_key},
        )
        (model_root / "cost.json").write_text(f"{model_key}\n", encoding="utf-8")

    manifest = finalize_run_artifact_manifest(run_root)

    records = manifest["artifact_records"]
    assert manifest["launcher_state"] == "finished"
    assert manifest["launcher_exit_code"] == 0
    assert "launcher.log" in records
    assert f"{MODEL_RUNS_DIRECTORY}/hgb/artifact_manifest.json" in records
    assert f"{MODEL_RUNS_DIRECTORY}/xgboost/artifact_manifest.json" in records
    assert all(
        record["size_bytes"] >= 0 and len(record["sha256"]) == 64 for record in records.values()
    )


def _launcher_environment(
    *, project_root: Path, dataset_dir: Path, output_dir: Path, python_bin: Path
) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "SHARED_B0_LAUNCHER_TEST_MODE": "1",
            "SHARED_B0_TEST_PROJECT_ROOT": str(project_root),
            "SHARED_B0_TEST_DATASET_DIR": str(dataset_dir),
            "SHARED_B0_TEST_OUTPUT_DIR": str(output_dir),
            "SHARED_B0_TEST_PYTHON_BIN": str(python_bin),
        }
    )
    return environment


def test_launcher_records_preflight_failure_state_and_exit_code(tmp_path: Path) -> None:
    project_root = tmp_path / "missing-input-project"
    project_root.mkdir()
    output_dir = project_root / "runs" / "preflight-failure"
    launcher = Path(__file__).resolve().parents[1] / "scripts/run_shared_b0_tabular_baselines.sh"

    completed = subprocess.run(
        ["bash", str(launcher)],
        check=False,
        capture_output=True,
        text=True,
        env=_launcher_environment(
            project_root=project_root,
            dataset_dir=project_root / "missing-dataset",
            output_dir=output_dir,
            python_bin=project_root / ".venv/bin/python",
        ),
    )

    assert completed.returncode != 0
    assert (
        json.loads((output_dir / "launcher-state.json").read_text(encoding="utf-8"))["state"]
        == "failed"
    )
    assert int((output_dir / "launcher-exit-code.txt").read_text(encoding="utf-8")) != 0
    assert (output_dir / "launcher.log").stat().st_size > 0


def test_launcher_preserves_python_failure_exit_code(tmp_path: Path) -> None:
    project_root = tmp_path / "python-failure-project"
    dataset_dir = project_root / "dataset"
    output_dir = project_root / "runs" / "python-failure"
    launcher = Path(__file__).resolve().parents[1] / "scripts/run_shared_b0_tabular_baselines.sh"
    python_bin = project_root / ".venv/bin/python"
    required_paths = (
        project_root / "src/flow_probe/shared_b0_tabular_baselines.py",
        project_root / "src/flow_probe/tabular_baselines.py",
        project_root / "scripts/run_shared_b0_tabular_baselines.sh",
        dataset_dir / "candidate/common_features.parquet",
        dataset_dir / "candidate/bert_train.parquet",
        dataset_dir / "validation/genis_common_features.parquet",
        dataset_dir / "validation/genis_bert.parquet",
        dataset_dir / "validation/tqhc2_common_features.parquet",
        dataset_dir / "validation/tqhc2_bert.parquet",
        dataset_dir / "manifests/checksums.json",
        dataset_dir / "manifests/freeze_manifest.json",
    )
    for path in required_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")
    shutil.copyfile(launcher, project_root / "scripts/run_shared_b0_tabular_baselines.sh")
    python_bin.parent.mkdir(parents=True, exist_ok=True)
    python_bin.write_text("#!/usr/bin/env bash\nexit 7\n", encoding="utf-8")
    python_bin.chmod(0o755)

    completed = subprocess.run(
        ["bash", str(launcher)],
        check=False,
        capture_output=True,
        text=True,
        env=_launcher_environment(
            project_root=project_root,
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            python_bin=python_bin,
        ),
    )

    assert completed.returncode == 7
    assert (output_dir / "launcher-exit-code.txt").read_text(encoding="utf-8").strip() == "7"
    assert (
        json.loads((output_dir / "launcher-state.json").read_text(encoding="utf-8"))["state"]
        == "failed"
    )
