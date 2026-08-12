from __future__ import annotations

from dataclasses import replace

import pytest
import torch

from flow_probe.e2_shared_pinn import (
    E2DetectionSourceBinding,
    E2ModelOutput,
    E2ParameterBudgetSignature,
    E2PermutationRecord,
    E2PhysicsFeatureBinding,
    E2PhysicsSupervision,
    E2PinnBudget,
    E2SharedPinnError,
    E2SharedPinnModel,
    E2SharedPinnTrainer,
    assert_shared_parameter_budget,
    assert_shared_training_budget,
    build_e2_physics_feature_binding,
    build_e2_variant_contract,
    build_e2_x_permutation,
    compose_e2_variant_loss,
    compute_e2_physics_diagnostics,
    e2_x_stratification_fields,
    module_gradient_norm,
    ordered_sample_ids_sha256,
    parameter_budget_signature,
    permute_e2_physics_supervision,
    shared_conservation_residual,
)


def _physics_bundle(
    batch_size: int = 4,
) -> tuple[E2PhysicsSupervision, torch.Tensor, E2PhysicsFeatureBinding]:
    features = torch.arange(batch_size * 7, dtype=torch.float32).reshape(batch_size, 7) / 10.0
    sample_ids = tuple(f"physics-{index}" for index in range(batch_size))
    binding = build_e2_physics_feature_binding(features, sample_ids)
    targets = torch.stack(
        [
            torch.tensor(
                [[0.1 + index * 0.01, 0.2 + index * 0.01, 0.3 + index * 0.01]]
            )
            for index in range(batch_size)
        ]
    )
    supervision_mask = torch.tensor([[[True, False, True]]]).repeat(batch_size, 1, 1)
    evaluation_mask = torch.ones_like(supervision_mask)
    transition_shape = (batch_size, 1, 2)
    supervision = E2PhysicsSupervision(
        state_targets=targets,
        state_supervision_mask=supervision_mask,
        state_evaluation_mask=evaluation_mask,
        arrivals=torch.ones(transition_shape),
        departures=torch.zeros(transition_shape),
        losses=torch.zeros(transition_shape),
        normalization_scale=torch.full((batch_size, 1), 10.0),
        conservation_mask=torch.ones(transition_shape, dtype=torch.bool),
        lower_bound=torch.zeros_like(targets),
        upper_bound=torch.ones_like(targets),
        boundary_mask=torch.ones_like(targets, dtype=torch.bool),
        sample_ids=sample_ids,
        sample_order_sha256=ordered_sample_ids_sha256(sample_ids),
        feature_binding_sha256=binding.binding_sha256,
    )
    supervision.validate()
    return supervision, features, binding


def _records(supervision: E2PhysicsSupervision) -> tuple[E2PermutationRecord, ...]:
    missing_pattern = tuple(
        bool(value) for value in supervision.state_supervision_mask[0].flatten().tolist()
    )
    return tuple(
        E2PermutationRecord(
            sample_id=sample_id,
            source_domain="ns3",
            protocol="tcp",
            scene_condition="queue-low",
            label=1,
            capture_id="capture-a",
            missing_pattern=missing_pattern,
        )
        for sample_id in supervision.sample_ids
    )


def _model(seed: int = 42) -> E2SharedPinnModel:
    torch.manual_seed(seed)
    return E2SharedPinnModel(
        input_size=7,
        hidden_size=8,
        state_channels=1,
        state_points=3,
    )


def _source_binding() -> E2DetectionSourceBinding:
    return E2DetectionSourceBinding(
        sample_ids=("source-0", "source-1", "source-2", "source-3"),
        profiles=("A", "B", "D", "A"),
        split_ids=("train", "train", "train", "train"),
        data_view_sha256="a" * 64,
    )


def test_all_variants_share_structure_initial_weights_and_actual_budget() -> None:
    models = {variant: _model() for variant in ("E2-A", "E2-S", "E2-P", "E2-X")}
    budgets = {
        variant: E2PinnBudget(max_steps=2, batch_size=4, physics_batch_size=4)
        for variant in models
    }

    assert_shared_parameter_budget(models)
    assert_shared_training_budget(models, budgets)
    signatures = [parameter_budget_signature(model) for model in models.values()]
    assert all(isinstance(value, E2ParameterBudgetSignature) for value in signatures)
    assert len(set(signatures)) == 1
    assert build_e2_variant_contract("E2-A").uses_state_supervision is False
    assert build_e2_variant_contract("E2-X").requires_permuted_physics is True

    mismatched_budgets = dict(budgets)
    mismatched_budgets["E2-X"] = E2PinnBudget(
        max_steps=3, batch_size=4, physics_batch_size=2
    )
    with pytest.raises(E2SharedPinnError, match="训练预算"):
        assert_shared_training_budget(models, mismatched_budgets)

    mismatched_models = dict(models)
    mismatched_models["E2-X"] = _model(seed=43)
    with pytest.raises(E2SharedPinnError, match="初始权重"):
        assert_shared_training_budget(mismatched_models, budgets)


def test_model_and_detection_binding_reject_nonseven_fields_and_target_domain() -> None:
    with pytest.raises(E2SharedPinnError, match="七字段"):
        E2SharedPinnModel(
            input_size=8,
            hidden_size=8,
            state_channels=1,
            state_points=3,
        )
    with pytest.raises(E2SharedPinnError, match="\[批量, 7\]"):
        _model()(torch.randn(4, 8))

    source_binding = _source_binding()
    batch_binding = source_binding.bind_batch(("source-0", "source-1"))
    source_binding.validate_batch(batch_binding, torch.randn(2, 7))
    target_binding = replace(_source_binding(), profiles=("A", "B", "C", "A"))
    with pytest.raises(E2SharedPinnError, match="C 目标域"):
        target_binding.validate()
    with pytest.raises(E2SharedPinnError, match="未绑定"):
        _source_binding().bind_batch(("source-0", "target-c"))


def test_x_requires_verified_derangement_and_changed_supervision() -> None:
    supervision, _, _ = _physics_bundle()
    records = _records(supervision)
    permutation = build_e2_x_permutation(records, supervision, seed=42)

    assert e2_x_stratification_fields(records) == (
        "source_domain",
        "protocol",
        "scene_condition",
        "missing_pattern",
        "label",
        "capture_id",
    )
    assert permutation == build_e2_x_permutation(records, supervision, seed=42)
    assert all(source != destination for destination, source in enumerate(permutation))
    with pytest.raises(E2SharedPinnError, match="固定点"):
        permute_e2_physics_supervision(
            supervision,
            tuple(range(supervision.batch_size)),
            records=records,
            seed=42,
        )

    shuffled = permute_e2_physics_supervision(
        supervision,
        permutation,
        records=records,
        seed=42,
    )
    assert shuffled.provenance == "stratified_permuted"
    assert shuffled.permutation_receipt is not None
    assert shuffled.permutation_receipt.source_supervision_sha256 != (
        shuffled.permutation_receipt.permuted_supervision_sha256
    )
    assert not torch.equal(shuffled.state_targets, supervision.state_targets)

    forged = replace(supervision, provenance="stratified_permuted")
    with pytest.raises(E2SharedPinnError, match="可验证收据"):
        forged.validate()

    compose_e2_variant_loss(
        variant="E2-X",
        detection_output=E2ModelOutput(
            logits=torch.zeros(4, 2),
            state=shuffled.state_targets.clone(),
        ),
        physics_state=shuffled.state_targets.clone(),
        labels=torch.tensor([0, 1, 0, 1], dtype=torch.long),
        supervision=shuffled,
        budget=E2PinnBudget(max_steps=2, batch_size=4),
    )


def test_physics_objective_reaches_shared_encoder_and_state_head() -> None:
    model = _model()
    supervision, features, _ = _physics_bundle()
    output = model(features)
    budget = E2PinnBudget(max_steps=2, batch_size=4)
    losses = compose_e2_variant_loss(
        variant="E2-P",
        detection_output=output,
        physics_state=output.state,
        labels=torch.tensor([0, 1, 0, 1], dtype=torch.long),
        supervision=supervision,
        budget=budget,
    )
    assert losses.state is not None
    assert losses.conservation is not None
    assert losses.boundary is not None
    physics_objective = (
        budget.lambda_state * losses.state
        + budget.lambda_conservation * losses.conservation
        + budget.lambda_boundary * losses.boundary
    )
    assert module_gradient_norm(
        physics_objective,
        model.encoder,
        module_name="共享编码器",
        require_nonzero=True,
    ) > 0.0
    assert module_gradient_norm(
        physics_objective,
        model.state_head,
        module_name="状态头",
        require_nonzero=True,
    ) > 0.0


def test_training_step_enforces_bindings_and_reports_both_gradient_norms() -> None:
    supervision, physics_features, physics_binding = _physics_bundle()
    exact_residual = shared_conservation_residual(supervision.state_targets, supervision)
    assert torch.allclose(exact_residual, torch.zeros_like(exact_residual), atol=1e-7)
    diagnostics = compute_e2_physics_diagnostics(
        supervision.state_targets,
        supervision,
        state_head_gradient_norm=0.25,
        shared_encoder_gradient_norm=0.5,
        constraint_tolerance=0.05,
    )
    assert diagnostics.state_normalized_rmse == pytest.approx(0.0)
    assert diagnostics.shared_encoder_gradient_norm == pytest.approx(0.5)
    assert diagnostics.state_head_gradient_norm == pytest.approx(0.25)

    model = _model()
    trainer = E2SharedPinnTrainer(
        model=model,
        optimizer=torch.optim.AdamW(model.parameters(), lr=1e-3),
        variant="E2-P",
        budget=E2PinnBudget(max_steps=1, batch_size=4, physics_batch_size=4),
        detection_source_binding=_source_binding(),
    )
    result = trainer.train_step(
        detection_features=torch.randn(4, 7),
        physics_features=physics_features,
        labels=torch.tensor([0, 1, 0, 1], dtype=torch.long),
        supervision=supervision,
        detection_binding=_source_binding().bind_batch(_source_binding().sample_ids),
        physics_binding=physics_binding,
    )
    assert result.diagnostics.shared_encoder_gradient_norm > 0.0
    assert result.diagnostics.state_head_gradient_norm > 0.0
    with pytest.raises(E2SharedPinnError, match="max_steps"):
        trainer.train_step(
            detection_features=torch.randn(4, 7),
            physics_features=physics_features,
            labels=torch.tensor([0, 1, 0, 1], dtype=torch.long),
            supervision=supervision,
            detection_binding=_source_binding().bind_batch(_source_binding().sample_ids),
            physics_binding=physics_binding,
        )

    mismatched_ids = tuple(reversed(supervision.sample_ids))
    mismatched_supervision = replace(
        supervision,
        sample_ids=mismatched_ids,
        sample_order_sha256=ordered_sample_ids_sha256(mismatched_ids),
    )
    other_model = _model()
    other_trainer = E2SharedPinnTrainer(
        model=other_model,
        optimizer=torch.optim.AdamW(other_model.parameters(), lr=1e-3),
        variant="E2-P",
        budget=E2PinnBudget(max_steps=1, batch_size=4),
        detection_source_binding=_source_binding(),
    )
    with pytest.raises(E2SharedPinnError, match="sample_id 顺序"):
        other_trainer.train_step(
            detection_features=torch.randn(4, 7),
            physics_features=physics_features,
            labels=torch.tensor([0, 1, 0, 1], dtype=torch.long),
            supervision=mismatched_supervision,
            detection_binding=_source_binding().bind_batch(_source_binding().sample_ids),
            physics_binding=physics_binding,
        )
