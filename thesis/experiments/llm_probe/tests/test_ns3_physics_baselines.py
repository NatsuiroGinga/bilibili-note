from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np
import pytest
import torch
import yaml

import flow_probe.ns3_physics_baselines as baseline_module
from flow_probe.ns3_physics_baselines import (
    BASELINES,
    BaselineTrainingConfig,
    Ns3PhysicsBaselineError,
    PhysicsSplit,
    audit_star_split_inputs,
    build_model,
    build_run_identity,
    build_supervision_masks,
    compute_training_loss,
    evaluate_predictions,
    final_tracking_step,
    fit_constant_state,
    fit_train_transform,
    load_and_audit_star_splits,
    load_baseline_config,
    materialize_audited_split,
    required_artifact_names,
    run_status_payload,
    select_then_materialize_test,
    train_selected_model,
    validate_output_location,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "ns3_physics_baselines_star_v1.yaml"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "run_ns3_physics_baseline.sh"


def _sample(split: str, group_id: str, index: int) -> dict[str, object]:
    offset = float(index)
    anchors = [10.0 + offset, 20.0 + offset, 30.0 + offset, 40.0 + offset, 50.0 + offset]
    return {
        "sample_id": f"{split}-sample-{index}",
        "group_id": group_id,
        "split": split,
        "model_inputs": {
            "capacity_start_bps": [8000.0] * 4,
            "capacity_end_bps": [8000.0] * 4,
            "configured_capacity_integral_link_bytes": [100.0] * 4,
            "qdisc_received_l3_bytes": [10.0] * 4,
            "qdisc_received_packets": [1.0] * 4,
        },
        "queue_boundary_anchors_l3_bytes": anchors,
        "state_supervision": {
            "queue_start_l3_bytes": anchors[:-1],
            "queue_end_l3_bytes": anchors[1:],
            "qdisc_enqueued_l3_bytes": [10.0] * 4,
            "qdisc_dequeued_l3_bytes": [0.0] * 4,
            "qdisc_dropped_before_enqueue_l3_bytes": [0.0] * 4,
            "qdisc_dropped_after_dequeue_l3_bytes": [0.0] * 4,
            "queue_start_packets": [0.0] * 4,
            "queue_end_packets": [0.0] * 4,
            "qdisc_enqueued_packets": [0.0] * 4,
            "qdisc_dequeued_packets": [0.0] * 4,
            "qdisc_dropped_before_enqueue_packets": [0.0] * 4,
            "qdisc_dropped_after_dequeue_packets": [0.0] * 4,
        },
        "label_targets": {"is_attack": [0, 0, 0, 0]},
        "metadata": {"scenario_id": "fixture", "source_csv_path": "/禁止进入模型.csv"},
    }


def _write_fixture(root: Path) -> dict[str, str]:
    groups = {
        "train": "star-bottleneck-v1|fixture-train|seed42|run1",
        "validation": "star-bottleneck-v1|fixture-validation|seed43|run1",
        "test": "star-bottleneck-v1|fixture-test|seed44|run1",
    }
    hashes: dict[str, str] = {}
    split_entries: dict[str, object] = {}
    for split, group_id in groups.items():
        path = root / f"{split}.jsonl"
        rows = [_sample(split, group_id, index) for index in range(4)]
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        hashes[f"{split}.jsonl"] = _sha256(path)
        split_entries[split] = {
            "seed": {"train": 42, "validation": 43, "test": 44}[split],
            "sample_count": len(rows),
            "group_ids": [group_id],
        }
    manifest_path = root / "split_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "flow_probe_ns3_sequence_split_v1",
                "horizon": 4,
                "splits": split_entries,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    hashes["split_manifest.json"] = _sha256(manifest_path)
    return hashes


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_first_record(path: Path, mutate: object) -> None:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    mutate(rows[0])
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _split(targets: np.ndarray) -> PhysicsSplit:
    sample_count = len(targets)
    features = np.arange(sample_count * 20, dtype=np.float32).reshape(sample_count, 4, 5)
    return PhysicsSplit(
        name="train",
        sample_ids=tuple(f"sample-{index}" for index in range(sample_count)),
        group_ids=tuple(f"star-bottleneck-v1|group-{index}" for index in range(sample_count)),
        features=features,
        state_targets=np.asarray(targets, dtype=np.float32),
        scales=np.full(sample_count, 100.0, dtype=np.float32),
        capacity=np.full((sample_count, 4), 100.0, dtype=np.float32),
        received=np.full((sample_count, 4), 10.0, dtype=np.float32),
        dequeued=np.zeros((sample_count, 4), dtype=np.float32),
        dropped_before=np.zeros((sample_count, 4), dtype=np.float32),
        dropped_after=np.zeros((sample_count, 4), dtype=np.float32),
    )


def test_load_and_audit_accepts_only_disjoint_star_splits(tmp_path: Path) -> None:
    hashes = _write_fixture(tmp_path)

    audited = load_and_audit_star_splits(tmp_path, hashes)

    assert tuple(audited.splits) == ("train", "validation", "test")
    assert audited.audit["sample_intersections"] == {
        "train_validation": 0,
        "train_test": 0,
        "validation_test": 0,
    }
    assert audited.audit["group_intersections"] == {
        "train_validation": 0,
        "train_test": 0,
        "validation_test": 0,
    }
    assert audited.audit["topologies"] == ["star-bottleneck-v1"]
    assert audited.splits["train"].features.shape == (4, 4, 5)


@pytest.mark.parametrize("defect", ["group_overlap", "non_star", "extra_input"])
def test_load_and_audit_rejects_leakage_and_input_budget_defects(
    tmp_path: Path, defect: str
) -> None:
    hashes = _write_fixture(tmp_path)
    validation_path = tmp_path / "validation.jsonl"
    if defect == "group_overlap":
        _replace_first_record(
            validation_path,
            lambda row: row.update(group_id="star-bottleneck-v1|fixture-train|seed42|run1"),
        )
        manifest_path = tmp_path / "split_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["splits"]["validation"]["group_ids"] = [
            "star-bottleneck-v1|fixture-train|seed42|run1",
            "star-bottleneck-v1|fixture-validation|seed43|run1",
        ]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False) + "\n", encoding="utf-8")
        hashes["split_manifest.json"] = _sha256(manifest_path)
    elif defect == "non_star":
        _replace_first_record(
            validation_path,
            lambda row: row.update(group_id="dumbbell-v1|fixture|seed43|run1"),
        )
    else:
        _replace_first_record(
            validation_path,
            lambda row: row["model_inputs"].update(label_family=["benign"] * 4),
        )
    hashes["validation.jsonl"] = _sha256(validation_path)

    expected = "group_id 泄漏" if defect == "group_overlap" else None
    with pytest.raises(Ns3PhysicsBaselineError, match=expected):
        load_and_audit_star_splits(tmp_path, hashes)


def test_test_split_is_materialized_only_after_selection_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hashes = _write_fixture(tmp_path)
    audited = audit_star_split_inputs(tmp_path, hashes)
    events: list[str] = []
    original_load_split = baseline_module._load_split

    def traced_load_split(path: Path, split_name: str) -> PhysicsSplit:
        events.append(f"load:{split_name}")
        return original_load_split(path, split_name)

    monkeypatch.setattr(baseline_module, "_load_split", traced_load_split)
    train = materialize_audited_split(audited, "train")
    validation = materialize_audited_split(audited, "validation")

    def selector(_train: PhysicsSplit, _validation: PhysicsSplit) -> object:
        events.append("selection:return")
        return object()

    _selection, test = select_then_materialize_test(
        audited=audited,
        train=train,
        validation=validation,
        selector=selector,
        selection_validator=lambda _selection: True,
    )

    assert test.name == "test"
    assert events == ["load:train", "load:validation", "selection:return", "load:test"]

    events.clear()

    def invalid_selector(_train: PhysicsSplit, _validation: PhysicsSplit) -> object:
        events.append("selection:invalid")
        return object()

    with pytest.raises(Ns3PhysicsBaselineError, match="未冻结"):
        select_then_materialize_test(
            audited=audited,
            train=train,
            validation=validation,
            selector=invalid_selector,
            selection_validator=lambda _selection: False,
        )
    assert events == ["selection:invalid"]


def test_constant_state_uses_only_mask_visible_training_targets() -> None:
    targets = np.asarray(
        [[1.0, 2.0, 30.0, 4.0, 50.0], [3.0, 20.0, 6.0, 40.0, 8.0]],
        dtype=np.float32,
    )
    masks = np.asarray(
        [[True, True, False, True, False], [True, False, True, False, True]],
        dtype=bool,
    )
    changed_hidden = targets.copy()
    changed_hidden[~masks] += 10000.0

    expected = np.asarray([2.0, 2.0, 6.0, 4.0, 8.0], dtype=np.float32)
    np.testing.assert_allclose(fit_constant_state(targets, masks), expected)
    np.testing.assert_allclose(fit_constant_state(changed_hidden, masks), expected)


def test_transform_and_masks_are_fitted_from_training_contract() -> None:
    split = _split(np.zeros((5, 5), dtype=np.float32))

    transform = fit_train_transform(split)
    masks = build_supervision_masks(split, seed=42)

    assert transform.mean.shape == (20,)
    assert transform.scale.shape == (20,)
    assert masks.shape == (5, 5)
    assert np.all(masks[:, 0])
    assert np.all(masks.sum(axis=1) == 2)


def test_state_and_standard_pinn_share_initial_model_for_the_same_seed() -> None:
    state_model = build_model(seed=43, hidden_size=128, device=torch.device("cpu"))
    pinn_model = build_model(seed=43, hidden_size=128, device=torch.device("cpu"))

    assert tuple(state_model.state_dict()) == tuple(pinn_model.state_dict())
    for name, value in state_model.state_dict().items():
        torch.testing.assert_close(value, pinn_model.state_dict()[name])


def test_standard_pinn_only_adds_differentiable_queue_residual() -> None:
    predicted = torch.tensor([[0.1, 0.2, 0.3, 0.4, 0.5]], dtype=torch.float32, requires_grad=True)
    target = torch.zeros_like(predicted)
    mask = torch.tensor([[True, True, False, False, False]])
    fluxes = {
        "scale": torch.tensor([100.0]),
        "capacity": torch.full((1, 4), 100.0),
        "received": torch.full((1, 4), 5.0),
        "dequeued": torch.zeros((1, 4)),
        "dropped_before": torch.zeros((1, 4)),
        "dropped_after": torch.zeros((1, 4)),
    }

    state = compute_training_loss("state_supervision", predicted, target, mask, fluxes, 0.01)
    pinn = compute_training_loss("standard_pinn", predicted, target, mask, fluxes, 0.01)

    torch.testing.assert_close(state.state, pinn.state)
    assert state.physics is None
    assert pinn.physics is not None
    torch.testing.assert_close(pinn.total, pinn.state + 0.01 * pinn.physics)
    pinn.total.backward()
    assert predicted.grad is not None
    assert float(predicted.grad.abs().sum()) > 0.0


def test_model_selection_interface_cannot_receive_test_split() -> None:
    parameters = inspect.signature(train_selected_model).parameters

    assert "test" not in parameters
    assert "test_split" not in parameters
    assert {"train", "validation", "baseline", "seed", "config"}.issubset(parameters)


def test_evaluation_reports_full_observed_unobserved_anchor_and_physics_metrics() -> None:
    split = _split(
        np.asarray(
            [[0.1, 0.2, 0.3, 0.4, 0.5], [0.2, 0.3, 0.4, 0.5, 0.6]],
            dtype=np.float32,
        )
    )
    masks = np.asarray(
        [[True, True, False, False, False], [True, False, True, False, False]],
        dtype=bool,
    )
    predictions = split.state_targets.copy()

    evaluation = evaluate_predictions(split, predictions, masks)

    assert evaluation.metrics["state_mse"] == pytest.approx(0.0)
    assert evaluation.metrics["state_mse_observed"] == pytest.approx(0.0)
    assert evaluation.metrics["state_mse_unobserved"] == pytest.approx(0.0)
    assert evaluation.metrics["state_anchor_mse"] == pytest.approx([0.0] * 5)
    assert evaluation.metrics["physics_residual_mse"] == pytest.approx(0.0)
    assert len(evaluation.predictions) == 2


def test_config_freezes_protocol_budget_and_online_tracking() -> None:
    raw, config = load_baseline_config(CONFIG_PATH)

    assert tuple(BASELINES) == ("constant_state", "state_supervision", "standard_pinn")
    assert config == BaselineTrainingConfig(
        hidden_size=128,
        batch_size=64,
        learning_rate=0.001,
        weight_decay=0.0001,
        max_epochs=300,
        patience=30,
        minimum_delta=1e-7,
        lambda_state=1.0,
        lambda_physics=0.01,
        state_supervision_mode="anchor0_plus_one",
        selection_metric="validation_state_mse",
        device="auto",
        cpu_threads=4,
    )
    assert raw["stage"] == "theory_selection"
    assert raw["status"] == "review_pending"
    assert raw["tracking"]["mode"] == "online"
    assert raw["tracking"]["project"] == "malicious-traffic-llm"
    assert raw["tracking"]["workspace"] == "mortiswang"
    assert raw["data"]["expected_topology"] == "star-bottleneck-v1"
    assert raw["data"]["expected_sha256"] == {
        "train.jsonl": "d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0",
        "validation.jsonl": "0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723",
        "test.jsonl": "6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94",
        "split_manifest.json": ("3393d76e96b9104ea78a8a52bc73e72e2298798a4a4db29dbf76ef412eb88785"),
    }


def test_run_identity_separates_formal_and_smoke_protocols() -> None:
    _raw, config = load_baseline_config(CONFIG_PATH)

    formal = build_run_identity("formal", config, smoke_max_epochs=None)
    smoke = build_run_identity("smoke", config, smoke_max_epochs=2)

    assert formal == {
        "run_kind": "formal",
        "effective_max_epochs": 300,
        "protocol_complete": True,
    }
    assert smoke == {
        "run_kind": "smoke",
        "effective_max_epochs": 2,
        "protocol_complete": False,
    }
    with pytest.raises(Ns3PhysicsBaselineError, match="formal"):
        build_run_identity("formal", config, smoke_max_epochs=2)
    with pytest.raises(Ns3PhysicsBaselineError, match="smoke"):
        build_run_identity("smoke", config, smoke_max_epochs=None)


def test_tracking_identity_tags_fit_swanlab_limit() -> None:
    raw, config = load_baseline_config(CONFIG_PATH)
    formal = build_run_identity("formal", config, smoke_max_epochs=None)
    smoke = build_run_identity("smoke", config, smoke_max_epochs=2)

    formal_settings = baseline_module._tracking_settings(raw, "formal-run", formal)
    smoke_settings = baseline_module._tracking_settings(raw, "smoke-run", smoke)

    assert {"run-formal", "epochs-300", "protocol-complete"} <= set(formal_settings.tags)
    assert {"run-smoke", "epochs-2", "protocol-partial"} <= set(smoke_settings.tags)
    assert all(len(tag) <= 20 for tag in (*formal_settings.tags, *smoke_settings.tags))


def test_output_location_rejects_formal_and_smoke_identity_mixing(tmp_path: Path) -> None:
    _raw, config = load_baseline_config(CONFIG_PATH)
    formal = build_run_identity("formal", config, smoke_max_epochs=None)
    smoke = build_run_identity("smoke", config, smoke_max_epochs=2)
    formal_output = (
        tmp_path
        / "runs/baselines/theory-selection/ns3-star-physics/review-pending-3393d76e-v1"
        / "standard_pinn-seed42"
    )
    smoke_output = tmp_path / "runs/smoke/ns3-star-physics/standard_pinn-seed42-smoke2"

    assert (
        validate_output_location(
            output_dir=formal_output,
            project_root=tmp_path,
            baseline="standard_pinn",
            seed=42,
            run_identity=formal,
        )
        == formal_output
    )
    assert (
        validate_output_location(
            output_dir=smoke_output,
            project_root=tmp_path,
            baseline="standard_pinn",
            seed=42,
            run_identity=smoke,
        )
        == smoke_output
    )
    with pytest.raises(Ns3PhysicsBaselineError, match="formal"):
        validate_output_location(
            output_dir=smoke_output,
            project_root=tmp_path,
            baseline="standard_pinn",
            seed=42,
            run_identity=formal,
        )
    with pytest.raises(Ns3PhysicsBaselineError, match="smoke"):
        validate_output_location(
            output_dir=formal_output,
            project_root=tmp_path,
            baseline="standard_pinn",
            seed=42,
            run_identity=smoke,
        )


def test_tracking_step_and_completion_status_cannot_regress_or_finish_early() -> None:
    history = tuple({"epoch": epoch} for epoch in range(1, 6))
    identity = {
        "run_kind": "formal",
        "effective_max_epochs": 300,
        "protocol_complete": True,
    }

    assert final_tracking_step(history, best_epoch=1) == 6
    awaiting = run_status_payload(
        status="awaiting_tracking_verification",
        stage="tracking_pending",
        baseline="standard_pinn",
        seed=42,
        run_identity=identity,
    )
    finished = run_status_payload(
        status="finished",
        stage="completed",
        baseline="standard_pinn",
        seed=42,
        run_identity=identity,
        tracking_verified=True,
    )
    assert awaiting["status"] == "awaiting_tracking_verification"
    assert awaiting["tracking_verified"] is False
    assert finished["status"] == "finished"
    assert finished["tracking_verified"] is True
    with pytest.raises(Ns3PhysicsBaselineError, match="核验"):
        run_status_payload(
            status="finished",
            stage="completed",
            baseline="standard_pinn",
            seed=42,
            run_identity=identity,
        )


def test_wrapper_uses_semantic_keys_fixed_seeds_and_no_other_data_roots() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")

    for baseline in BASELINES:
        assert baseline in script
    assert "42|43|44" in script
    assert "flow-probe-ns3-physics-baseline" in script
    assert "ns3-queue-sequences-h4-seed-split-20260721-v2" in script
    assert "review-pending-3393d76e-v1" in script
    assert "runs/smoke/ns3-star-physics" in script
    assert "--run-kind" in script
    assert "tqh" not in script.lower()
    assert "genis" not in script.lower()
    assert "dumbbell" not in script.lower()
    assert "parking" not in script.lower()


def test_required_artifacts_cover_predictions_cost_tracking_and_hashes() -> None:
    common = required_artifact_names("state_supervision")

    assert {
        "artifact_manifest.json",
        "config_snapshot.yaml",
        "environment.json",
        "input_manifest.json",
        "split_audit.json",
        "training_history.jsonl",
        "best_model.pt",
        "predictions.jsonl.gz",
        "summary.json",
        "cost.json",
        "swanlab_metrics.json",
        "swanlab_metadata.json",
        "tracking_verification.json",
        "file_sha256_manifest.json",
        "run_status.json",
        "console.log",
    }.issubset(common)
    assert "constant_state.json" in required_artifact_names("constant_state")
    assert "best_model.pt" not in required_artifact_names("constant_state")


def test_yaml_is_parseable_before_shell_launch() -> None:
    assert isinstance(yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")), dict)
