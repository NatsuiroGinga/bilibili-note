from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
import yaml

import flow_probe.shared_b0_physics_evaluation as shared_eval
from flow_probe.evaluate_model import EvaluationSettings, build_evaluation_binding
from flow_probe.shared_b0_physics_evaluation import (
    EVALUATION_SCOPE,
    SharedB0PhysicsEvaluationError,
    TrainingArtifactPaths,
    build_public_evaluation_wrapper_binding,
    load_shared_b0_physics_evaluation_config,
    run_physics_fit_diagnostic,
    run_public_detection_evaluation,
    summarize_physics_diagnostic_rows,
    validate_physics_diagnostic_claims,
    validate_training_artifacts,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_CASES = (
    (
        "configs/shared_b0_state_supervision_seed42_genis_batch16_v1.yaml",
        "state_supervision",
        "genis",
    ),
    (
        "configs/shared_b0_state_supervision_seed42_tqhc2_batch16_v1.yaml",
        "state_supervision",
        "tqhc2",
    ),
    (
        "configs/shared_b0_standard_pinn_seed42_genis_batch16_v1.yaml",
        "standard_pinn",
        "genis",
    ),
    (
        "configs/shared_b0_standard_pinn_seed42_tqhc2_batch16_v1.yaml",
        "standard_pinn",
        "tqhc2",
    ),
)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def _public_records() -> list[dict[str, object]]:
    return [
        {
            "sample_id": "eval-0",
            "prompt": "普通共同字段样本0",
            "completion": '{"label":"benign"}',
        },
        {
            "sample_id": "eval-1",
            "prompt": "普通共同字段样本1",
            "completion": '{"label":"malicious"}',
        },
    ]


def _artifact_entry(run_dir: Path, relative: str) -> dict[str, object]:
    path = run_dir / relative
    return {
        "path": relative,
        "bytes": path.stat().st_size,
        "sha256": shared_eval._file_sha256(path),
    }


def _build_completed_artifacts(
    tmp_path: Path,
    baseline: str,
) -> tuple[TrainingArtifactPaths, dict[str, Path]]:
    run_dir = tmp_path / f"run-{baseline}"
    adapter = run_dir / "adapter"
    adapter.mkdir(parents=True)
    (adapter / "adapter_config.json").write_text(
        '{"peft_type":"LORA"}\n',
        encoding="utf-8",
    )
    state_file = run_dir / "state_head/state_head.pt"
    state_file.parent.mkdir(parents=True)
    state_file.write_bytes(b"state-head-fixture")

    data_dir = tmp_path / "data"
    classification = data_dir / "qwen_train.jsonl"
    validation = data_dir / "genis_qwen.jsonl"
    sidecar = data_dir / "ns3_physics_train.jsonl"
    sidecar_manifest = data_dir / "dataset_manifest.json"
    _write_jsonl(
        classification,
        [{"sample_id": "physics-0", "prompt": "共同字段", "completion": "{}"}],
    )
    _write_jsonl(validation, _public_records())
    _write_jsonl(sidecar, [{"sample_id": "physics-0"}])
    _write_json(sidecar_manifest, {"record_count": 2421})

    base_binding = {
        "train_file": str(classification),
        "validation_file": str(validation),
        "seed": 42,
    }
    binding_value: dict[str, object] = {
        "schema_version": "flow_probe_shared_b0_physics_binding_v1",
        "base_training_binding": base_binding,
        "baseline": baseline,
        "lambda_state": 1.0,
        "lambda_physics": 0.0 if baseline == "state_supervision" else 0.01,
        "max_steps": 200,
        "physics_records": 2421,
        "physics_usage": EVALUATION_SCOPE,
        "state_head_initialization_sha256": "a" * 64,
        "classification_train_sha256": shared_eval._file_sha256(classification),
        "classification_validation_sha256": shared_eval._file_sha256(validation),
        "physics_sidecar_sha256": shared_eval._file_sha256(sidecar),
        "physics_dataset_manifest_sha256": shared_eval._file_sha256(
            sidecar_manifest
        ),
    }
    binding_value["binding_sha256"] = shared_eval._canonical_sha256(binding_value)
    _write_json(run_dir / "training_binding.json", binding_value)
    _write_json(
        run_dir / "state_head/metadata.json",
        {
            "binding_sha256": binding_value["binding_sha256"],
            "initialization_sha256": "a" * 64,
            "final_parameter_tree_sha256": "b" * 64,
        },
    )
    _write_json(
        run_dir / "run_state.json",
        {
            "status": "completed",
            "binding_sha256": binding_value["binding_sha256"],
            "optimization_step": 200,
        },
    )
    _write_json(
        run_dir / "train_summary.json",
        {
            "status": "completed",
            "binding_sha256": binding_value["binding_sha256"],
            "optimization_step": 200,
            "generation_records": 800,
            "physics_records": 2421,
            "nonfinite_count": 0,
        },
    )
    manifest = {
        "status": "completed",
        "binding_sha256": binding_value["binding_sha256"],
        "artifacts": [
            _artifact_entry(run_dir, "training_binding.json"),
            _artifact_entry(run_dir, "state_head/state_head.pt"),
            _artifact_entry(run_dir, "state_head/metadata.json"),
            _artifact_entry(run_dir, "adapter/adapter_config.json"),
        ],
    }
    _write_json(run_dir / "artifact_manifest.json", manifest)
    return TrainingArtifactPaths(run_dir), {
        "classification": classification,
        "validation": validation,
        "sidecar": sidecar,
        "sidecar_manifest": sidecar_manifest,
    }


def _runtime_config(tmp_path: Path, baseline: str = "state_supervision"):
    config_name = (
        "shared_b0_state_supervision_seed42_genis_batch16_v1.yaml"
        if baseline == "state_supervision"
        else "shared_b0_standard_pinn_seed42_genis_batch16_v1.yaml"
    )
    config = load_shared_b0_physics_evaluation_config(
        PROJECT_ROOT / "configs" / config_name
    )
    artifacts, data = _build_completed_artifacts(tmp_path, baseline)
    test_file = tmp_path / "evaluation.jsonl"
    _write_jsonl(test_file, _public_records())
    physics = replace(
        config.physics,
        classification_train_file=data["classification"],
        sidecar_root=tmp_path / "sidecar-root",
        sidecar_file=data["sidecar"],
        dataset_manifest=data["sidecar_manifest"],
        output_file=artifacts.run_dir / "physics_train_fit_diagnostic.json",
    )
    return replace(
        config,
        config_sha256="c" * 64,
        artifacts=artifacts,
        test_file=test_file,
        output_dir=tmp_path / "public-output",
        physics=physics,
    )


@pytest.mark.parametrize("relative,baseline,dataset", CONFIG_CASES)
def test_four_real_configs_freeze_public_and_physics_contracts(
    relative: str,
    baseline: str,
    dataset: str,
) -> None:
    config = load_shared_b0_physics_evaluation_config(PROJECT_ROOT / relative)

    assert config.baseline == baseline
    assert config.dataset == dataset
    assert config.evaluation_settings.batch_size == 16
    assert config.evaluation_settings.length_bucket is False
    assert config.evaluation_settings.attention_backend == "sdpa"
    assert config.evaluation_settings.resume is True
    assert config.physics.evaluation_scope == EVALUATION_SCOPE
    assert config.physics.batch_size == 16


def test_config_rejects_non_sdpa_or_non_training_fit_scope(tmp_path: Path) -> None:
    source = PROJECT_ROOT / CONFIG_CASES[0][0]
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    raw["public_evaluation"]["attention_backend"] = "auto"
    target = tmp_path / "invalid.yaml"
    target.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    with pytest.raises(SharedB0PhysicsEvaluationError, match="批量16"):
        load_shared_b0_physics_evaluation_config(target)

    raw["public_evaluation"]["attention_backend"] = "sdpa"
    raw["physics_diagnostic"]["evaluation_scope"] = "external"
    target.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    with pytest.raises(SharedB0PhysicsEvaluationError, match="训练拟合集"):
        load_shared_b0_physics_evaluation_config(target)


def test_training_artifact_validation_covers_adapter_head_binding_and_data(
    tmp_path: Path,
) -> None:
    config = _runtime_config(tmp_path)
    result = validate_training_artifacts(config)

    assert result.training_binding["baseline"] == "state_supervision"
    assert len(result.adapter_tree_sha256) == 64
    assert len(result.state_head_file_sha256) == 64
    assert len(result.training_binding_file_sha256) == 64


def test_training_artifact_validation_rejects_tampered_state_head(
    tmp_path: Path,
) -> None:
    config = _runtime_config(tmp_path)
    config.artifacts.state_head_file.write_bytes(b"tampered")

    with pytest.raises(SharedB0PhysicsEvaluationError, match="哈希或字节数变化"):
        validate_training_artifacts(config)


def test_public_wrapper_binding_contains_all_required_hashes(tmp_path: Path) -> None:
    config = _runtime_config(tmp_path)
    artifacts = validate_training_artifacts(config)
    records = _public_records()
    binding = build_public_evaluation_wrapper_binding(config, artifacts, records)

    required = {
        "training_binding_sha256",
        "training_binding_file_sha256",
        "artifact_manifest_file_sha256",
        "adapter_tree_sha256",
        "state_head_file_sha256",
        "classification_train_sha256",
        "evaluation_test_file_sha256",
        "public_evaluation_binding_sha256",
        "binding_sha256",
    }
    assert required.issubset(binding)
    assert binding["binding_sha256"] == shared_eval._canonical_sha256(
        {key: value for key, value in binding.items() if key != "binding_sha256"}
    )


def _successful_public_evaluator(calls: list[dict[str, object]]):
    def evaluator(**kwargs: Any) -> dict[str, object]:
        calls.append(dict(kwargs))
        output_dir = Path(str(kwargs["output_dir"]))
        records = _public_records()
        public_binding = build_evaluation_binding(
            kwargs["probe"],
            kwargs["settings"],
            kwargs["test_file"],
            records,
            kwargs["adapter_path"],
        )
        _write_json(output_dir / "evaluation_binding.json", public_binding)
        _write_json(output_dir / "evaluation_progress.json", {"status": "finished"})
        _write_json(output_dir / "evaluation_summary.json", {"accuracy": 1.0})
        (output_dir / "predictions.jsonl").write_text("{}\n", encoding="utf-8")
        return {"accuracy": 1.0}

    return evaluator


def test_public_wrapper_calls_existing_evaluator_without_changing_protocol(
    tmp_path: Path,
) -> None:
    config = _runtime_config(tmp_path)
    calls: list[dict[str, object]] = []

    result = run_public_detection_evaluation(
        config,
        evaluator=_successful_public_evaluator(calls),
    )

    assert result["status"] == "completed"
    assert len(calls) == 1
    call = calls[0]
    assert call["probe"] == config.probe
    assert call["test_file"] == config.test_file
    assert call["adapter_path"] == config.artifacts.adapter_dir
    assert call["settings"] == config.evaluation_settings
    assert config.evaluation_settings.batch_size == 16
    assert config.evaluation_settings.length_bucket is False
    assert config.evaluation_settings.attention_backend == "sdpa"
    assert config.probe.max_new_tokens == 16


def test_completed_public_evaluation_returns_idempotently_without_model_call(
    tmp_path: Path,
) -> None:
    config = _runtime_config(tmp_path)
    run_public_detection_evaluation(
        config,
        evaluator=_successful_public_evaluator([]),
    )

    def forbidden(**kwargs: object) -> dict[str, object]:
        raise AssertionError(f"完成评估不得再次调用模型：{kwargs}")

    result = run_public_detection_evaluation(config, evaluator=forbidden)

    assert result["status"] == "completed"
    assert result["idempotent"] is True


def test_incomplete_public_evaluation_keeps_binding_and_can_resume(
    tmp_path: Path,
) -> None:
    config = _runtime_config(tmp_path)

    def interrupted(**kwargs: object) -> dict[str, object]:
        raise RuntimeError("模拟中断")

    with pytest.raises(RuntimeError, match="模拟中断"):
        run_public_detection_evaluation(config, evaluator=interrupted)
    binding_before = (
        config.output_dir / "shared_b0_evaluation_binding.json"
    ).read_bytes()

    calls: list[dict[str, object]] = []
    result = run_public_detection_evaluation(
        config,
        evaluator=_successful_public_evaluator(calls),
    )

    assert result["status"] == "completed"
    assert len(calls) == 1
    resumed_settings = calls[0]["settings"]
    assert isinstance(resumed_settings, EvaluationSettings)
    assert resumed_settings.resume is True
    assert (
        config.output_dir / "shared_b0_evaluation_binding.json"
    ).read_bytes() == binding_before


def _diagnostic_row(index: int, error: float = 0.0) -> dict[str, object]:
    return {
        "sample_id": f"physics-{index}",
        "group_id": f"group-{index % 2}",
        "predicted_state": [error, 1.0, 2.0, 3.0, 4.0],
        "state_targets": [0.0, 1.0, 2.0, 3.0, 4.0],
        "state_mask_inputs": [True, False, False, False, True],
        "queue_balance_residual": [error, 0.0, 0.0, 0.0],
    }


def test_physics_summary_reports_required_training_fit_metrics_and_groups() -> None:
    summary = summarize_physics_diagnostic_rows(
        [_diagnostic_row(0, 1.0), _diagnostic_row(1, 0.0)]
    )

    assert summary["evaluation_scope"] == EVALUATION_SCOPE
    assert summary["sample_count"] == 2
    assert summary["state_mse"] == pytest.approx(0.1)
    assert summary["state_mae"] == pytest.approx(0.1)
    assert summary["mask_coverage"] == pytest.approx(0.4)
    assert summary["valid_state_elements"] == 4
    assert summary["queue_balance_residual_mse"] == pytest.approx(0.125)
    assert summary["nonfinite_count"] == 0
    groups = summary["groups"]
    state_by_anchor = summary["state_by_anchor"]
    assert isinstance(groups, dict)
    assert isinstance(state_by_anchor, list)
    assert set(groups) == {"group-0", "group-1"}
    assert len(state_by_anchor) == 5


@pytest.mark.parametrize("phrase", shared_eval.FORBIDDEN_PHYSICS_CLAIMS)
def test_training_fit_diagnostic_rejects_external_generalization_claims(
    phrase: str,
) -> None:
    with pytest.raises(SharedB0PhysicsEvaluationError, match="禁止表述"):
        validate_physics_diagnostic_claims({"claim": phrase})


def test_physics_fit_is_batch_resumable_then_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _runtime_config(tmp_path)
    config = replace(config, physics=replace(config.physics, batch_size=2))
    sidecar = [
        {
            "sample_id": f"physics-{index}",
            "group_id": f"group-{index % 2}",
            "stable_order": index,
        }
        for index in range(3)
    ]
    classification = [
        {"sample_id": f"physics-{index}", "prompt": f"共同字段{index}"}
        for index in range(3)
    ]
    monkeypatch.setattr(
        shared_eval,
        "_prepare_physics_records",
        lambda current: (classification, sidecar),
    )
    calls = 0

    def interrupted_predictor(
        classification_records: Sequence[Mapping[str, object]],
        sidecar_records: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("模拟物理批次中断")
        return [_diagnostic_row(index) for index in range(2)]

    with pytest.raises(RuntimeError, match="模拟物理批次中断"):
        run_physics_fit_diagnostic(config, predictor=interrupted_predictor)
    assert len(shared_eval._read_jsonl(config.physics.partial_file, "部分预测")) == 2

    def resumed_predictor(
        classification_records: Sequence[Mapping[str, object]],
        sidecar_records: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        return [_diagnostic_row(2)]

    completed = run_physics_fit_diagnostic(config, predictor=resumed_predictor)
    assert completed["status"] == "completed"
    assert completed["evaluation_scope"] == EVALUATION_SCOPE
    metrics = completed["metrics"]
    assert isinstance(metrics, dict)
    assert metrics["sample_count"] == 3

    def forbidden_predictor(
        classification_records: Sequence[Mapping[str, object]],
        sidecar_records: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        raise AssertionError("完成诊断不得再次加载模型")

    repeated = run_physics_fit_diagnostic(config, predictor=forbidden_predictor)
    assert repeated["idempotent"] is True


def test_physics_binding_is_independent_of_public_dataset_config(
    tmp_path: Path,
) -> None:
    config = _runtime_config(tmp_path)
    validated = validate_training_artifacts(config)
    sidecar = [
        {"sample_id": "physics-0", "stable_order": 0},
        {"sample_id": "physics-1", "stable_order": 1},
    ]
    first = shared_eval._physics_binding(config, validated, sidecar)
    second = shared_eval._physics_binding(
        replace(config, dataset="tqhc2"),
        validated,
        sidecar,
    )

    assert first == second
