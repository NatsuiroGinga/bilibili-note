import gzip
import hashlib
import importlib
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import pyarrow.parquet as pq


CONTRACT_VERSION = "lspr24-g0-v5-staged"
DEVELOPMENT_SPLITS = (
    "train-fit",
    "architecture-selection",
    "dev-validation",
    "calibration",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _stable_order_sha256(rows: list[dict[str, object]]) -> str:
    payload = [
        {"sample_id": row["sample_id"], "stable_order": row["stable_order"]} for row in rows
    ]
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _adapter_module() -> object:
    return importlib.import_module("flow_probe.lspr24_g0_tabular_adapter")


# G0-D 制品的生产者是 Rust 侧 development_router.rs，消费者是本 Python 适配器；
# 两侧合同版本常量必须逐字一致，否则第二遍产出的制品会被适配器整体拒绝。
_RUST_DEVELOPMENT_ROUTER = (
    Path(__file__).resolve().parents[1] / "tools" / "lspr24_g0" / "src" / "development_router.rs"
)


def _rust_contract_version() -> str:
    source = _RUST_DEVELOPMENT_ROUTER.read_text(encoding="utf-8")
    match = re.search(r'LSPR24_G0_CONTRACT_VERSION:\s*&str\s*=\s*"([^"]+)"', source)
    assert match is not None, f"未在 {_RUST_DEVELOPMENT_ROUTER} 找到 LSPR24_G0_CONTRACT_VERSION"
    return match.group(1)


def test_python_adapter_contract_version_matches_rust_producer_constant() -> None:
    """跨语言合同版本一致性：Python 适配器常量必须等于 Rust 生产者常量。"""

    adapter = _adapter_module()
    rust_version = _rust_contract_version()

    assert rust_version == adapter.G0_D_CONTRACT_VERSION
    assert rust_version == CONTRACT_VERSION


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _write_fixture(
    tmp_path: Path,
    *,
    forbidden_field: str | None = None,
    corrupt_sidecar: bool = False,
    final_history_path: bool = False,
    extra_window_field: str | None = None,
) -> tuple[Path, Path, Path]:
    run_root = tmp_path / "g0-d-run"
    restricted_root = tmp_path / "restricted-development-labels"
    output_dir = tmp_path / "new-output"
    for directory in (
        run_root / "views",
        run_root / "manifests",
        run_root / "receipts",
        restricted_root,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    fields = [
        {"output_name": "bytes_total", "semantic": "traffic-volume"},
        {"output_name": "packet_count", "semantic": "flow-completion-statistics"},
    ]
    if forbidden_field is not None:
        fields.append({"output_name": forbidden_field, "semantic": "traffic-volume"})
    field_path = run_root / "manifests" / "field-manifest.json"
    _write_json(
        field_path,
        {
            "contract_version": CONTRACT_VERSION,
            "fields": fields,
        },
    )
    lineage_path = run_root / "receipts" / "field-lineage.json"
    _write_json(
        lineage_path,
        {
            "contract_version": CONTRACT_VERSION,
            "field_manifest_sha256": _sha256(field_path),
            "fields": [
                {
                    "output_name": field["output_name"],
                    "recursive_ancestors": [f"raw_{field['output_name']}"],
                }
                for field in fields
            ],
        },
    )

    window_rows: list[dict[str, object]] = []
    history_rows: list[dict[str, object]] = []
    label_rows: list[dict[str, object]] = []
    cluster_rows: list[dict[str, object]] = []
    stable_order = 0
    window_order = 0
    for history_length in (1, 4, 16, 32):
        for split_index, split_name in enumerate(DEVELOPMENT_SPLITS):
            for class_index, label in enumerate((0, 1)):
                sample_id = f"h{history_length}-{split_name}-{class_index}"
                endpoint_id = f"endpoint-{split_index}-{class_index}"
                segment_id = f"segment-{history_length}-{split_index}-{class_index}"
                window_ids: list[str] = []
                window_orders: list[int] = []
                for time_index in range(history_length):
                    window_id = f"{sample_id}-window-{time_index}"
                    window_ids.append(window_id)
                    window_orders.append(window_order)
                    row: dict[str, object] = {
                        "window_id": window_id,
                        "bytes_total": float(stable_order * 100 + time_index),
                        "packet_count": float(class_index + time_index),
                    }
                    if extra_window_field is not None:
                        row[extra_window_field] = float(time_index)
                    window_rows.append(row)
                    window_order += 1
                history_rows.append(
                    {
                        "sample_id": sample_id,
                        "stable_order": stable_order,
                        "split_name": split_name,
                        "history_length": history_length,
                        "history_window_ids": json.dumps(window_ids),
                        "protected_endpoint_id": endpoint_id,
                        "segment_id": segment_id,
                        "history_endpoint_ids": json.dumps([endpoint_id] * history_length),
                        "history_segment_ids": json.dumps([segment_id] * history_length),
                        "history_split_names": json.dumps([split_name] * history_length),
                        "history_stable_orders": json.dumps(window_orders),
                    }
                )
                label_rows.append(
                    {"sample_id": sample_id, "stable_order": stable_order, "label": label}
                )
                cluster_rows.append(
                    {
                        "sample_id": sample_id,
                        "stable_order": stable_order,
                        "evaluation_cluster_id": f"cluster-{split_index}",
                    }
                )
                stable_order += 1

    windows_path = run_root / "views" / "development-windows.parquet"
    history_path = run_root / "views" / "history-samples.parquet"
    labels_path = restricted_root / "development-labels.parquet"
    clusters_path = run_root / "manifests" / "evaluation-clusters.parquet"
    pd.DataFrame(window_rows).to_parquet(windows_path, index=False)
    pd.DataFrame(history_rows).to_parquet(history_path, index=False)
    pd.DataFrame(label_rows).to_parquet(labels_path, index=False)
    pd.DataFrame(cluster_rows).to_parquet(clusters_path, index=False)
    registered_history_path = history_path
    if final_history_path:
        registered_history_path = run_root / "views" / "final-test-history-samples.parquet"
        registered_history_path.write_bytes(history_path.read_bytes())
    if corrupt_sidecar:
        label_rows[0], label_rows[1] = label_rows[1], label_rows[0]
        pd.DataFrame(label_rows).to_parquet(labels_path, index=False)

    history_receipt_path = run_root / "receipts" / "history-invariants.json"
    _write_json(
        history_receipt_path,
        {
            "contract_version": CONTRACT_VERSION,
            "history_samples_sha256": _sha256(registered_history_path),
            "same_endpoint": True,
            "same_contiguous_segment": True,
            "same_partition": True,
            "old_to_new": True,
        },
    )
    artifact_paths = {
        "development_windows": windows_path,
        "history_samples": registered_history_path,
        "field_manifest": field_path,
        "field_lineage": lineage_path,
        "evaluation_clusters": clusters_path,
        "history_invariants": history_receipt_path,
    }
    semantic_path = run_root / "receipts" / "semantic-hashes.json"
    _write_json(
        semantic_path,
        {
            "contract_version": CONTRACT_VERSION,
            "artifacts": {
                name: {
                    "path": str(path.relative_to(run_root)),
                    "sha256": _sha256(path),
                }
                for name, path in artifact_paths.items()
            },
        },
    )
    decision_path = run_root / "receipts" / "g0-a-decision.json"
    _write_json(
        decision_path,
        {
            "phase": "G0-D",
            "development_baseline_release": True,
            "phase_assignment": "G0-F",
            "final_status": "NOT_READY",
            "G0-A12": "NOT_READY",
            "final_feature_artifacts": [],
            "final_label_artifacts": [],
            "final_row_selection_artifacts": [],
            "final_member_artifacts": [],
            "final_specific_statistics": [],
        },
    )
    _write_json(
        restricted_root / "development-labels-receipt.json",
        {
            "router_version": "lspr24-dev-router-v1",
            "sidecar_sha256": _sha256(labels_path),
            "sample_order_sha256": _stable_order_sha256(history_rows),
            "g0_d_decision_sha256": _sha256(decision_path),
        },
    )
    return run_root, restricted_root, output_dir


def _rewrite_semantic_hashes(run_root: Path) -> None:
    semantic_path = run_root / "receipts" / "semantic-hashes.json"
    semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
    for artifact in semantic["artifacts"].values():
        path = run_root / artifact["path"]
        artifact["sha256"] = _sha256(path)
    _write_json(semantic_path, semantic)


def _rewrite_sidecar_receipt(run_root: Path, restricted_root: Path) -> None:
    history = pd.read_parquet(run_root / "views" / "history-samples.parquet").to_dict(
        orient="records"
    )
    receipt_path = restricted_root / "development-labels-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["sidecar_sha256"] = _sha256(restricted_root / "development-labels.parquet")
    receipt["sample_order_sha256"] = _stable_order_sha256(history)
    _write_json(receipt_path, receipt)


def _prepare(adapter: object, run_root: Path, restricted_root: Path, output_dir: Path) -> object:
    return adapter.prepare_lspr24_g0_tabular_data(
        g0_run_root=run_root,
        restricted_root=restricted_root,
        output_dir=output_dir,
        history_lengths=(1, 4, 16, 32),
        model_keys=("hgb", "xgboost"),
    )


def test_development_adapter_constructs_identical_hgb_xgboost_input_and_keeps_history_budget(
    tmp_path: Path,
) -> None:
    adapter = _adapter_module()
    run_root, restricted_root, output_dir = _write_fixture(tmp_path)

    prepared = _prepare(adapter, run_root, restricted_root, output_dir)

    assert prepared.model_inputs["hgb"] is prepared.model_inputs["xgboost"]
    assert prepared.shared_hashes["field_lineage_sha256"]
    assert prepared.shared_hashes["history_invariants_sha256"]
    for history_length, data in prepared.by_history_length.items():
        assert data.train.features.shape[1] == history_length * 2
        assert data.train.sample_ids == (
            f"h{history_length}-train-fit-0",
            f"h{history_length}-train-fit-1",
        )
    assert all(attempt["fit_count"] == 1 for attempt in prepared.fair_budget_plan["attempts"])
    assert all(
        attempt["evaluation_count"] == 1 for attempt in prepared.fair_budget_plan["attempts"]
    )
    assert not output_dir.exists()


def test_cli_enforces_selection_validation_calibration_state_machine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = _adapter_module()
    run_root, restricted_root, output_dir = _write_fixture(tmp_path)
    calls: list[dict[str, object]] = []

    def fake_run_prepared(**kwargs: object) -> object:
        calls.append(kwargs)
        predictions_path = Path(kwargs["predictions_path"])
        predictions_path.parent.mkdir(parents=True, exist_ok=True)
        prepared = kwargs["prepared"]
        evaluation_names = tuple(prepared.evaluations)
        history_length = prepared.train.features.shape[1] // 2
        scores = {1: 0.61, 4: 0.94, 16: 0.78, 32: 0.72}
        with gzip.open(predictions_path, "wt", encoding="utf-8") as output:
            for evaluation_name, split in prepared.evaluations.items():
                for model_key in kwargs["model_keys"]:
                    for sample_id, truth in zip(split.sample_ids, split.labels, strict=True):
                        malicious_probability = 0.8 if truth == "malicious" else 0.2
                        output.write(
                            json.dumps(
                                {
                                    "evaluation": evaluation_name,
                                    "model": model_key,
                                    "probabilities": {
                                        "benign": 1.0 - malicious_probability,
                                        "malicious": malicious_probability,
                                    },
                                    "sample_id": sample_id,
                                    "truth": truth,
                                }
                            )
                            + "\n"
                        )
        model_state_output = kwargs.get("model_state_output")
        if model_state_output is not None:
            for model_key in kwargs["model_keys"]:
                model_state_output[model_key] = object()
        return SimpleNamespace(
            summary={
                "history_length": history_length,
                "models": {
                    model_key: {
                        "evaluations": {
                            evaluation_name: {"metrics": {"macro_f1": scores[history_length]}}
                            for evaluation_name in evaluation_names
                        }
                    }
                    for model_key in kwargs["model_keys"]
                },
            },
            cost={"history_length": history_length, "models": {}},
        )

    monkeypatch.setattr(
        adapter, "run_prepared_tabular_baseline_suite", fake_run_prepared, raising=False
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lspr24_g0_tabular_adapter",
            "--g0-run-root",
            str(run_root),
            "--restricted-root",
            str(restricted_root),
            "--output-dir",
            str(output_dir),
            "--model",
            "hgb",
            "--model",
            "xgboost",
            "--seed",
            "42",
        ],
    )

    adapter.main()

    assert len(calls) == 6
    assert all(call["model_keys"] == ("hgb", "xgboost") for call in calls)
    assert [tuple(call["prepared"].evaluations) for call in calls] == [
        ("architecture-selection",),
        ("architecture-selection",),
        ("architecture-selection",),
        ("architecture-selection",),
        ("dev-validation",),
        ("calibration",),
    ]
    assert [call["stage"] for call in calls] == [
        "lspr24_g0_d_architecture_selection",
        "lspr24_g0_d_architecture_selection",
        "lspr24_g0_d_architecture_selection",
        "lspr24_g0_d_architecture_selection",
        "lspr24_g0_d_dev_validation",
        "lspr24_g0_d_calibration",
    ]
    selected_models = calls[4]["fitted_models"]
    assert selected_models is calls[5]["fitted_models"]
    assert selected_models is calls[1]["model_state_output"]
    assert {
        "config_snapshot.json",
        "environment.json",
        "data_binding.json",
        "fair-budget-plan-receipt.json",
        "fair-budget-execution-receipt.json",
        "architecture_selection.json",
        "dev_validation.json",
        "calibration.json",
        "threshold_freeze.json",
        "summary.json",
        "cost.json",
        "predictions.jsonl.gz",
        "console.log",
        "artifact_manifest.json",
    }.issubset({path.name for path in output_dir.iterdir()})
    architecture = json.loads(
        (output_dir / "architecture_selection.json").read_text(encoding="utf-8")
    )
    dev_validation = json.loads(
        (output_dir / "dev_validation.json").read_text(encoding="utf-8")
    )
    calibration = json.loads((output_dir / "calibration.json").read_text(encoding="utf-8"))
    threshold = json.loads((output_dir / "threshold_freeze.json").read_text(encoding="utf-8"))
    assert architecture["phase"] == "architecture-selection"
    assert architecture["selected_candidate"] == {
        "configuration_id": "default-h4",
        "history_length": 4,
    }
    assert dev_validation["phase"] == "dev-validation"
    assert dev_validation["selected_candidate"] == architecture["selected_candidate"]
    assert dev_validation["architecture_selection_sha256"] == _sha256(
        output_dir / "architecture_selection.json"
    )
    assert calibration["phase"] == "calibration"
    assert calibration["selected_candidate"] == architecture["selected_candidate"]
    assert calibration["dev_validation_sha256"] == _sha256(
        output_dir / "dev_validation.json"
    )
    assert calibration["frozen_calibrators"]
    assert threshold["calibration_sha256"] == _sha256(output_dir / "calibration.json")
    assert threshold["frozen_thresholds"]
    assert len(
        {
            _sha256(output_dir / "architecture_selection.json"),
            _sha256(output_dir / "dev_validation.json"),
            _sha256(output_dir / "calibration.json"),
        }
    ) == 3


@pytest.mark.parametrize("source", ["history", "sidecar", "clusters"])
def test_adapter_rejects_duplicate_sample_id_before_label_dictionary(
    tmp_path: Path, source: str
) -> None:
    adapter = _adapter_module()
    run_root, restricted_root, output_dir = _write_fixture(tmp_path)
    paths = {
        "history": run_root / "views" / "history-samples.parquet",
        "sidecar": restricted_root / "development-labels.parquet",
        "clusters": run_root / "manifests" / "evaluation-clusters.parquet",
    }
    path = paths[source]
    frame = pd.read_parquet(path)
    frame.loc[1, "sample_id"] = frame.loc[0, "sample_id"]
    if source == "sidecar":
        frame.loc[1, "label"] = 1 - int(frame.loc[0, "label"])
    frame.to_parquet(path, index=False)
    if source == "sidecar":
        _rewrite_sidecar_receipt(run_root, restricted_root)
    else:
        _rewrite_semantic_hashes(run_root)
    if source == "history":
        history_receipt_path = run_root / "receipts" / "history-invariants.json"
        receipt = json.loads(history_receipt_path.read_text(encoding="utf-8"))
        receipt["history_samples_sha256"] = _sha256(path)
        _write_json(history_receipt_path, receipt)
        _rewrite_semantic_hashes(run_root)
        _rewrite_sidecar_receipt(run_root, restricted_root)

    with pytest.raises(adapter.Lspr24G0TabularAdapterError, match="重复 sample_id"):
        _prepare(adapter, run_root, restricted_root, output_dir)
    assert not output_dir.exists()


@pytest.mark.parametrize("extra_field", ["Label", "SrcIP", "DstPort", "unknown_feature"])
def test_adapter_rejects_unregistered_window_schema_before_projection(
    tmp_path: Path, extra_field: str
) -> None:
    adapter = _adapter_module()
    run_root, restricted_root, output_dir = _write_fixture(
        tmp_path, extra_window_field=extra_field
    )

    with pytest.raises(adapter.Lspr24G0TabularAdapterError, match="开发窗口全模式"):
        _prepare(adapter, run_root, restricted_root, output_dir)
    assert not output_dir.exists()


@pytest.mark.parametrize(
    "violation",
    ["forbidden_lineage", "lineage_hash", "different_endpoint", "different_segment", "different_split", "reverse_time", "history_receipt_hash"],
)
def test_adapter_verifies_lineage_and_history_invariants(
    tmp_path: Path, violation: str
) -> None:
    adapter = _adapter_module()
    run_root, restricted_root, output_dir = _write_fixture(tmp_path)
    lineage_path = run_root / "receipts" / "field-lineage.json"
    history_path = run_root / "views" / "history-samples.parquet"
    if violation == "forbidden_lineage":
        lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
        lineage["fields"][0]["recursive_ancestors"] = ["SrcIP"]
        _write_json(lineage_path, lineage)
        _rewrite_semantic_hashes(run_root)
    elif violation == "lineage_hash":
        semantic_path = run_root / "receipts" / "semantic-hashes.json"
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic["artifacts"]["field_lineage"]["sha256"] = "0" * 64
        _write_json(semantic_path, semantic)
    elif violation == "history_receipt_hash":
        semantic_path = run_root / "receipts" / "semantic-hashes.json"
        semantic = json.loads(semantic_path.read_text(encoding="utf-8"))
        semantic["artifacts"]["history_invariants"]["sha256"] = "0" * 64
        _write_json(semantic_path, semantic)
    else:
        history = pd.read_parquet(history_path)
        row_index = int(history.index[history["history_length"] == 4][0])
        if violation == "different_endpoint":
            history.loc[row_index, "history_endpoint_ids"] = json.dumps(
                ["endpoint-a", "endpoint-b", "endpoint-a", "endpoint-a"]
            )
        elif violation == "different_segment":
            history.loc[row_index, "history_segment_ids"] = json.dumps(
                ["segment-a", "segment-b", "segment-a", "segment-a"]
            )
        elif violation == "different_split":
            history.loc[row_index, "history_split_names"] = json.dumps(
                ["train-fit", "dev-validation", "train-fit", "train-fit"]
            )
        else:
            history.loc[row_index, "history_stable_orders"] = json.dumps([4, 3, 2, 1])
        history.to_parquet(history_path, index=False)
        history_receipt_path = run_root / "receipts" / "history-invariants.json"
        receipt = json.loads(history_receipt_path.read_text(encoding="utf-8"))
        receipt["history_samples_sha256"] = _sha256(history_path)
        _write_json(history_receipt_path, receipt)
        _rewrite_semantic_hashes(run_root)

    with pytest.raises(adapter.Lspr24G0TabularAdapterError):
        _prepare(adapter, run_root, restricted_root, output_dir)
    assert not output_dir.exists()


def test_adapter_rejects_registered_final_test_path_before_any_parquet_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = _adapter_module()
    run_root, restricted_root, output_dir = _write_fixture(tmp_path, final_history_path=True)
    parquet_opens: list[str] = []
    original_parquet_file = pq.ParquetFile
    original_read_parquet = adapter.pd.read_parquet

    def record_parquet_file(path: object, *args: object, **kwargs: object) -> object:
        parquet_opens.append(str(path))
        return original_parquet_file(path, *args, **kwargs)

    def record_read_parquet(path: object, *args: object, **kwargs: object) -> object:
        parquet_opens.append(str(path))
        return original_read_parquet(path, *args, **kwargs)

    monkeypatch.setattr(pq, "ParquetFile", record_parquet_file)
    monkeypatch.setattr(adapter.pd, "read_parquet", record_read_parquet)

    with pytest.raises(adapter.Lspr24G0TabularAdapterError, match="最终区"):
        _prepare(adapter, run_root, restricted_root, output_dir)
    assert parquet_opens == []
    assert not output_dir.exists()


@pytest.mark.parametrize(
    ("forbidden_field", "corrupt_sidecar"),
    [(None, True), ("SrcPort", False), ("Label", False)],
)
def test_development_adapter_rejects_unbound_or_forbidden_sidecar(
    tmp_path: Path, forbidden_field: str | None, corrupt_sidecar: bool
) -> None:
    adapter = _adapter_module()
    run_root, restricted_root, output_dir = _write_fixture(
        tmp_path,
        forbidden_field=forbidden_field,
        corrupt_sidecar=corrupt_sidecar,
    )

    with pytest.raises(adapter.Lspr24G0TabularAdapterError):
        _prepare(adapter, run_root, restricted_root, output_dir)
    assert not output_dir.exists()
