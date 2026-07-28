from __future__ import annotations

from pathlib import Path

import pytest
import torch

from flow_probe.physics_train import (
    STEP_METRIC_KEYS,
    ContinuousQueueStateHead,
    PhysicsDataError,
    PhysicsTrainingError,
    apply_m2p_gradients,
    build_physics_prompt,
    build_state_supervision_masks,
    build_variant_contract,
    compose_variant_loss,
    create_run_layout,
    masked_state_target_loss,
    physics_sample_schedule,
    prepare_physics_record,
    project_physics_gradients,
    queue_balance_residual,
    record_step_metrics,
    resolve_lambda_physics,
    state_target_loss,
    validate_completed_artifacts,
)


def _mask_record(sample_id: str, group_id: str) -> dict[str, str]:
    return {"sample_id": sample_id, "group_id": group_id}


def test_anchor0_only_masks_every_record_at_boundary_only() -> None:
    records = [_mask_record("sample-1", "group-a"), _mask_record("sample-2", "group-b")]

    masks = build_state_supervision_masks(records, "anchor0_only", 42)

    assert masks == {
        "sample-1": (True, False, False, False, False),
        "sample-2": (True, False, False, False, False),
    }


def test_anchor0_plus_one_balances_unique_groups_and_reuses_group_position() -> None:
    records = [_mask_record(f"sample-{index}", f"group-{index}") for index in range(11)]
    records.append(_mask_record("sample-duplicate", "group-3"))

    masks = build_state_supervision_masks(records, "anchor0_plus_one", 42)

    assert masks["sample-3"] == masks["sample-duplicate"]
    assert all(mask[0] and sum(mask) == 2 for mask in masks.values())
    group_masks = {records[index]["group_id"]: masks[f"sample-{index}"] for index in range(11)}
    counts = [sum(mask[position] for mask in group_masks.values()) for position in range(1, 5)]
    assert max(counts) - min(counts) <= 1
    assert masks == build_state_supervision_masks(list(reversed(records)), "anchor0_plus_one", 42)


def test_masked_state_loss_ignores_unobserved_errors_and_dense_matches_existing_loss() -> None:
    target = torch.zeros((1, 5))
    predicted = torch.tensor([[2.0, 10.0, 20.0, 30.0, 40.0]])
    anchor0 = torch.tensor([[True, False, False, False, False]])
    dense = torch.ones((1, 5), dtype=torch.bool)

    assert masked_state_target_loss(predicted, target, anchor0).item() == pytest.approx(4.0)
    predicted[:, 1:] = 1000.0
    assert masked_state_target_loss(predicted, target, anchor0).item() == pytest.approx(4.0)
    assert masked_state_target_loss(predicted, target, dense) == pytest.approx(
        state_target_loss(predicted, target)
    )


@pytest.mark.parametrize("override", [0.001, 0.01, 0.03])
def test_lambda_physics_override_supports_sensitivity_values(override: float) -> None:
    assert resolve_lambda_physics(0.1, override) == override


def test_lambda_physics_override_preserves_default_and_rejects_negative() -> None:
    assert resolve_lambda_physics(0.1, None) == 0.1
    with pytest.raises(PhysicsTrainingError, match="不得为负"):
        resolve_lambda_physics(0.1, -0.001)


def test_negative_physics_gradient_is_projected_orthogonal_per_tensor() -> None:
    generation = (torch.tensor([1.0, 0.0]), torch.tensor([0.0, 2.0]))
    physics = (torch.tensor([-1.0, 0.0]), torch.tensor([0.0, 0.0]))

    projection = project_physics_gradients(generation, physics)

    reference_generation = torch.cat(generation)
    reference_physics = torch.cat(physics)
    coefficient = torch.dot(reference_physics, reference_generation) / torch.dot(
        reference_generation, reference_generation
    )
    reference = reference_physics - coefficient * reference_generation
    actual = torch.cat([gradient for gradient in projection.gradients if gradient is not None])
    assert projection.triggered
    assert actual == pytest.approx(reference)
    assert projection.cosine_before < 0
    assert projection.cosine_after == pytest.approx(0.0, abs=1e-6)


def test_nonnegative_physics_gradient_is_not_changed() -> None:
    generation = (torch.tensor([1.0, 0.0]), torch.tensor([0.0, 2.0]))
    physics = (torch.tensor([1.0, 0.0]), torch.tensor([0.0, 0.0]))

    projection = project_physics_gradients(generation, physics)

    assert not projection.triggered
    assert all(
        torch.equal(actual, expected)
        for actual, expected in zip(projection.gradients, physics, strict=True)
        if actual is not None
    )


def test_m2p_combines_only_trainable_targets_and_preserves_state_head_rule() -> None:
    lora = [torch.nn.Parameter(torch.zeros(1)), torch.nn.Parameter(torch.zeros(1))]
    state_head = [torch.nn.Parameter(torch.zeros(1))]
    frozen = torch.nn.Parameter(torch.ones(1), requires_grad=False)
    generation = (torch.tensor([2.0]), torch.tensor([1.0]))
    state = (torch.tensor([3.0]), torch.tensor([4.0]))
    physics = (torch.tensor([-1.0]), torch.tensor([-1.0]))

    diagnostics = apply_m2p_gradients(
        lora,
        state_head,
        generation_gradients=generation,
        state_lora_gradients=state,
        physics_lora_gradients=physics,
        state_head_state_gradients=(torch.tensor([5.0]),),
        state_head_physics_gradients=(torch.tensor([7.0]),),
        lambda_state=1.0,
        lambda_physics=0.01,
    )

    expected_lora = [
        generation[index] + state[index] + 0.01 * diagnostics.projection.gradients[index]
        for index in range(2)
    ]
    assert all(
        parameter.grad == pytest.approx(expected)
        for parameter, expected in zip(lora, expected_lora, strict=True)
    )
    assert state_head[0].grad == pytest.approx(torch.tensor([5.07]))
    assert frozen.grad is None


def test_m2p_is_the_only_variant_that_enables_projection() -> None:
    m2 = build_variant_contract("M2", lambda_state=1.0, lambda_physics=0.01)
    m2p = build_variant_contract("M2P", lambda_state=1.0, lambda_physics=0.01)

    assert m2.uses_physics and not m2.uses_projection
    assert m2p.uses_physics and m2p.uses_projection


def _physics_sample() -> dict[str, object]:
    return {
        "sample_id": "sample-1",
        "group_id": "forbidden-group",
        "split": "train",
        "model_inputs": {
            "capacity_start_bps": [80, 160, 240, 320],
            "capacity_end_bps": [80, 160, 240, 320],
            "configured_capacity_integral_link_bytes": [10.0, 20.0, 30.0, 40.0],
            "qdisc_received_l3_bytes": [8.0, 13.0, 18.0, 23.0],
            "qdisc_received_packets": [1, 2, 3, 4],
        },
        "queue_boundary_anchors_l3_bytes": [2.0, 5.0, 10.0, 15.0, 20.0],
        "state_supervision": {
            "qdisc_dequeued_l3_bytes": [5.0, 8.0, 13.0, 18.0],
            "qdisc_dropped_before_enqueue_l3_bytes": [0.0, 0.0, 0.0, 0.0],
            "qdisc_dropped_after_dequeue_l3_bytes": [0.0, 0.0, 0.0, 0.0],
        },
        "label_targets": {"label_primary": ["benign"] * 4},
        "metadata": {"scenario_id": "forbidden", "seed": 42, "run": 1},
    }


def test_variants_only_construct_their_declared_losses() -> None:
    calls = {"state": 0, "physics": 0}

    def state_factory() -> torch.Tensor:
        calls["state"] += 1
        return torch.tensor(2.0)

    def physics_factory() -> torch.Tensor:
        calls["physics"] += 1
        return torch.tensor(3.0)

    m0 = compose_variant_loss("M0", torch.tensor(1.0), state_factory, physics_factory, 1.0, 0.1)
    assert float(m0.total) == pytest.approx(1.0)
    assert m0.state is None and m0.physics is None
    assert calls == {"state": 0, "physics": 0}

    m1 = compose_variant_loss("M1", torch.tensor(1.0), state_factory, physics_factory, 1.0, 0.1)
    assert float(m1.total) == pytest.approx(3.0)
    assert m1.state is not None and m1.physics is None
    assert calls == {"state": 1, "physics": 0}

    m2 = compose_variant_loss("M2", torch.tensor(1.0), state_factory, physics_factory, 1.0, 0.1)
    assert float(m2.total) == pytest.approx(3.3)
    assert m2.state is not None and m2.physics is not None
    assert calls == {"state": 2, "physics": 1}


def test_capacity_shift_uses_one_scale_for_five_continuous_anchors() -> None:
    prepared = prepare_physics_record(_physics_sample())

    assert prepared.scale == 40.0
    assert prepared.state_targets == pytest.approx((0.05, 0.125, 0.25, 0.375, 0.5))
    assert len(prepared.state_targets) == 5


def test_truth_anchors_have_zero_residual_and_perturbation_is_nonzero() -> None:
    prepared = prepare_physics_record(_physics_sample())
    predicted = torch.tensor([prepared.state_targets])
    residual = queue_balance_residual(
        predicted,
        torch.tensor([prepared.scale]),
        torch.tensor([prepared.capacity]),
        torch.tensor([prepared.received]),
        torch.tensor([prepared.dequeued]),
        torch.tensor([prepared.dropped_before]),
        torch.tensor([prepared.dropped_after]),
    )
    assert torch.max(torch.abs(residual)).item() <= 1e-12

    perturbed = predicted.clone()
    perturbed[0, 2] += 0.1
    changed = queue_balance_residual(
        perturbed,
        torch.tensor([prepared.scale]),
        torch.tensor([prepared.capacity]),
        torch.tensor([prepared.received]),
        torch.tensor([prepared.dequeued]),
        torch.tensor([prepared.dropped_before]),
        torch.tensor([prepared.dropped_after]),
    )
    assert torch.max(torch.abs(changed)).item() > 0.0


def test_physics_loss_reaches_shared_and_state_head_but_not_frozen_parameters() -> None:
    shared = torch.nn.Linear(3, 4)
    frozen = torch.nn.Linear(3, 4)
    frozen.requires_grad_(False)
    state_head = ContinuousQueueStateHead(4)
    predicted = state_head(shared(torch.ones((2, 3))) + frozen(torch.ones((2, 3))))
    residual = queue_balance_residual(
        predicted,
        torch.tensor([40.0, 40.0]),
        torch.full((2, 4), 10.0),
        torch.zeros((2, 4)),
        torch.zeros((2, 4)),
        torch.zeros((2, 4)),
        torch.zeros((2, 4)),
    )
    residual.square().mean().backward()

    assert any(
        parameter.grad is not None and parameter.grad.norm() > 1e-12
        for parameter in shared.parameters()
    )
    assert any(
        parameter.grad is not None and parameter.grad.norm() > 1e-12
        for parameter in state_head.parameters()
    )
    assert all(parameter.grad is None for parameter in frozen.parameters())


def test_state_head_accepts_float_hidden_with_bfloat16_weights() -> None:
    state_head = ContinuousQueueStateHead(4).to(dtype=torch.bfloat16)
    hidden = torch.ones((2, 4), dtype=torch.float32, requires_grad=True)

    predicted = state_head(hidden)
    predicted.float().sum().backward()

    assert predicted.dtype == torch.bfloat16
    assert hidden.grad is not None and hidden.grad.norm() > 0


def test_constant_offset_is_in_physics_nullspace_but_state_loss_detects_it() -> None:
    prepared = prepare_physics_record(_physics_sample())
    truth = torch.tensor([[0.0, 0.125, 0.25, 0.375, 0.5]], dtype=torch.float64)
    shifted = truth + 0.25
    tensors = (
        torch.tensor([prepared.scale]),
        torch.tensor([prepared.capacity]),
        torch.tensor([prepared.received]),
        torch.tensor([prepared.dequeued]),
        torch.tensor([prepared.dropped_before]),
        torch.tensor([prepared.dropped_after]),
    )
    truth_residual = queue_balance_residual(truth, *tensors)
    shifted_residual = queue_balance_residual(shifted, *tensors)

    assert torch.allclose(truth_residual, shifted_residual, atol=1e-12)
    assert state_target_loss(shifted, truth).item() > 0.0


def test_physics_prompt_contains_only_the_five_allowed_input_fields() -> None:
    prompt = build_physics_prompt(_physics_sample())

    for field in (
        "capacity_start_bps",
        "capacity_end_bps",
        "configured_capacity_integral_link_bytes",
        "qdisc_received_l3_bytes",
        "qdisc_received_packets",
    ):
        assert field in prompt
    for forbidden in (
        "group_id",
        "scenario_id",
        "seed",
        "run",
        "label_primary",
        "queue_boundary_anchors_l3_bytes",
        "qdisc_dequeued_l3_bytes",
        "qdisc_dropped_before_enqueue_l3_bytes",
        "qdisc_dropped_after_dequeue_l3_bytes",
        "queue_balance_residual_l3_bytes",
        "queue_balance_residual_packets",
    ):
        assert forbidden not in prompt


@pytest.mark.parametrize(
    "field", ("queue_balance_residual_l3_bytes", "queue_balance_residual_packets")
)
def test_saved_residual_fields_cannot_enter_training_interface(field: str) -> None:
    sample = _physics_sample()
    sample[field] = [0.0, 0.0, 0.0, 0.0]

    with pytest.raises(PhysicsDataError, match="审计残差"):
        prepare_physics_record(sample)


def test_m1_and_m2_share_schedule_head_and_weights_except_physics_switch() -> None:
    schedule_m1 = physics_sample_schedule(807, batch_size=4, steps=50, seed=42)
    schedule_m2 = physics_sample_schedule(807, batch_size=4, steps=50, seed=42)
    m1 = build_variant_contract("M1", lambda_state=1.0, lambda_physics=0.1)
    m2 = build_variant_contract("M2", lambda_state=1.0, lambda_physics=0.1)

    assert schedule_m1 == schedule_m2
    assert m1.state_head_outputs == m2.state_head_outputs == 5
    assert m1.lambda_state == m2.lambda_state == 1.0
    assert m1.lambda_physics == m2.lambda_physics == 0.1
    assert m1.uses_state and m2.uses_state
    assert not m1.uses_physics and m2.uses_physics


def test_output_directory_is_unique_and_completed_layout_is_checkable(tmp_path: Path) -> None:
    output_dir = tmp_path / "run"
    layout = create_run_layout(output_dir, "M2")
    with pytest.raises(FileExistsError):
        create_run_layout(output_dir, "M2")

    for path in layout.required_paths:
        if path.suffix or path.name == "final_adapter":
            if path.name == "final_adapter":
                path.mkdir(parents=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
    validate_completed_artifacts(layout)


def test_each_step_persists_and_logs_all_required_numeric_metrics(tmp_path: Path) -> None:
    class Recorder:
        def __init__(self) -> None:
            self.calls: list[tuple[dict[str, float], int]] = []

        def log(self, metrics: dict[str, float], step: int) -> None:
            self.calls.append((metrics, step))

    recorder = Recorder()
    metrics = {key: float(index + 1) for index, key in enumerate(STEP_METRIC_KEYS)}
    path = tmp_path / "step_metrics.jsonl"

    record_step_metrics(path, recorder, step=1, metrics=metrics)

    assert recorder.calls == [(metrics, 1)]
    assert path.read_text(encoding="utf-8").count("\n") == 1
