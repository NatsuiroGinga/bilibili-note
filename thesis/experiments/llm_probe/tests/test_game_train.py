from __future__ import annotations

import json
from pathlib import Path

import pytest
import torch

from flow_probe.game_coordination import CoordinationSolution
from flow_probe.game_train import (
    GAME_STEP_METRIC_KEYS,
    G5_STEP_METRIC_KEYS,
    GameTrainingError,
    _build_settings,
    _step_metrics,
    _write_state_mask,
    apply_coordinated_lora_gradients,
    apply_private_state_head_gradients,
    build_g5_follower_gradients,
    commit_functional_adamw_step,
    create_game_run_layout,
    differentiable_clip_grad_norm,
    functional_adamw_step,
    physics_batch_valid_fraction,
    record_game_step_metrics,
    validate_game_artifacts,
)
from flow_probe.physics_train import build_state_supervision_masks


def _training_mapping(
    state_supervision_mode: str = "anchor0_only",
) -> dict[str, object]:
    return {
        "training": {
            "generation_train_file": "generation-train.jsonl",
            "generation_validation_file": "generation-validation.jsonl",
            "physics_train_file": "physics-train.jsonl",
            "physics_validation_file": "physics-validation.jsonl",
            "physics_test_file": "physics-test.jsonl",
            "learning_rate": 0.0002,
            "generation_batch_size": 4,
            "gradient_accumulation_steps": 4,
            "physics_batch_size": 4,
            "validation_batch_size": 8,
            "state_supervision_mode": state_supervision_mode,
            "lambda_state": 1.0,
            "lambda_physics": 0.01,
            "max_grad_norm": 1.0,
        }
    }


def _physics_sample() -> dict[str, object]:
    return {
        "sample_id": "sample-1",
        "group_id": "group-1",
        "model_inputs": {
            "capacity_start_bps": [80.0, 80.0, 80.0, 80.0],
            "capacity_end_bps": [80.0, 80.0, 80.0, 80.0],
            "configured_capacity_integral_link_bytes": [10.0, 10.0, 10.0, 10.0],
            "qdisc_received_l3_bytes": [1.0, 1.0, 1.0, 1.0],
            "qdisc_received_packets": [1.0, 1.0, 1.0, 1.0],
        },
        "queue_boundary_anchors_l3_bytes": [0.0, 1.0, 2.0, 3.0, 4.0],
        "state_supervision": {
            "qdisc_dequeued_l3_bytes": [0.0, 0.0, 0.0, 0.0],
            "qdisc_dropped_before_enqueue_l3_bytes": [0.0, 0.0, 0.0, 0.0],
            "qdisc_dropped_after_dequeue_l3_bytes": [0.0, 0.0, 0.0, 0.0],
        },
    }


def test_g2_writes_normalized_direction_at_generation_scale() -> None:
    parameter = torch.nn.Parameter(torch.zeros(3))

    diagnostics = apply_coordinated_lora_gradients(
        (parameter,),
        generation_gradients=(torch.tensor([3.0, 0.0, 0.0]),),
        state_gradients=(torch.tensor([0.0, 4.0, 0.0]),),
        physics_gradients=(torch.tensor([0.0, 0.0, 5.0]),),
        variant="G2",
        physics_valid_fraction=1.0,
    )

    assert diagnostics.solution.weights == pytest.approx((0.34, 0.34, 0.32))
    assert parameter.grad == pytest.approx(3.0 * torch.tensor([0.34, 0.34, 0.32]))
    assert diagnostics.generation_norm == pytest.approx(3.0)


def test_zero_auxiliary_gradient_is_rejected_without_fake_direction() -> None:
    parameter = torch.nn.Parameter(torch.zeros(2))
    generation = torch.tensor([2.0, -1.0])

    diagnostics = apply_coordinated_lora_gradients(
        (parameter,),
        generation_gradients=(generation,),
        state_gradients=(torch.zeros(2),),
        physics_gradients=(torch.tensor([0.0, 1.0]),),
        variant="G2",
        physics_valid_fraction=1.0,
    )

    assert diagnostics.solution.fallback_to_generation
    assert diagnostics.solution.weights == (1.0, 0.0, 0.0)
    assert parameter.grad == pytest.approx(generation)


def test_generation_zero_gradient_is_a_hard_error() -> None:
    parameter = torch.nn.Parameter(torch.zeros(2))

    with pytest.raises(GameTrainingError, match="生成梯度严格为零"):
        apply_coordinated_lora_gradients(
            (parameter,),
            generation_gradients=(torch.zeros(2),),
            state_gradients=(torch.ones(2),),
            physics_gradients=(torch.ones(2),),
            variant="G4",
            physics_valid_fraction=1.0,
        )


def test_g4_reliability_combines_valid_fraction_and_state_physics_cosine() -> None:
    parameter = torch.nn.Parameter(torch.zeros(3))

    diagnostics = apply_coordinated_lora_gradients(
        (parameter,),
        generation_gradients=(torch.tensor([1.0, 0.0, 0.0]),),
        state_gradients=(torch.tensor([0.0, 1.0, 0.0]),),
        physics_gradients=(torch.tensor([0.0, 2.0, 0.0]),),
        variant="G4",
        physics_valid_fraction=0.5,
    )

    assert diagnostics.gram[1][2] == pytest.approx(1.0)
    assert diagnostics.physics_reliability == pytest.approx(0.5)
    assert diagnostics.solution.margins[0] >= 0.95


def _physics_only_solution() -> CoordinationSolution:
    return CoordinationSolution(
        weights=(0.98, 0.0, 0.02),
        margins=(0.98, 0.0, 0.02),
        objective=-1.0,
        active_auxiliaries=("physics",),
        fallback_to_generation=False,
    )


def test_g4_rejected_state_keeps_private_state_gradient_empty() -> None:
    parameter = torch.nn.Parameter(torch.zeros(1))

    apply_private_state_head_gradients(
        (parameter,),
        state_gradients=(torch.tensor([2.0]),),
        physics_gradients=(None,),
        solution=_physics_only_solution(),
        lambda_state=1.0,
        lambda_physics=0.01,
        physics_reliability=0.5,
        variant="G4",
    )

    assert parameter.grad is None


def test_g4r_forces_private_state_anchor_when_shared_state_is_rejected() -> None:
    parameter = torch.nn.Parameter(torch.zeros(1))

    apply_private_state_head_gradients(
        (parameter,),
        state_gradients=(torch.tensor([2.0]),),
        physics_gradients=(None,),
        solution=_physics_only_solution(),
        lambda_state=1.0,
        lambda_physics=0.01,
        physics_reliability=0.5,
        variant="G4R",
    )

    assert parameter.grad == pytest.approx(torch.tensor([2.0]))


def test_g4r_private_physics_remains_accepted_and_reliability_scaled() -> None:
    parameter = torch.nn.Parameter(torch.zeros(1))

    apply_private_state_head_gradients(
        (parameter,),
        state_gradients=(torch.tensor([2.0]),),
        physics_gradients=(torch.tensor([100.0]),),
        solution=_physics_only_solution(),
        lambda_state=1.0,
        lambda_physics=0.01,
        physics_reliability=0.5,
        variant="G4R",
    )

    assert parameter.grad == pytest.approx(torch.tensor([2.5]))


def test_g4r_private_physics_remains_rejected_when_solution_rejects_it() -> None:
    parameter = torch.nn.Parameter(torch.zeros(1))
    generation_only = CoordinationSolution(
        weights=(1.0, 0.0, 0.0),
        margins=(1.0, 0.0, 0.0),
        objective=0.0,
        active_auxiliaries=(),
        fallback_to_generation=True,
    )

    apply_private_state_head_gradients(
        (parameter,),
        state_gradients=(torch.tensor([2.0]),),
        physics_gradients=(torch.tensor([100.0]),),
        solution=generation_only,
        lambda_state=1.0,
        lambda_physics=0.01,
        physics_reliability=0.5,
        variant="G4R",
    )

    assert parameter.grad == pytest.approx(torch.tensor([2.0]))


def test_g4r_and_g4_share_exact_lora_coordination_solution() -> None:
    g4_parameter = torch.nn.Parameter(torch.zeros(3))
    g4r_parameter = torch.nn.Parameter(torch.zeros(3))
    gradients = {
        "generation_gradients": (torch.tensor([1.0, 0.0, 0.0]),),
        "state_gradients": (torch.tensor([0.0, 1.0, 0.0]),),
        "physics_gradients": (torch.tensor([0.0, 0.0, 1.0]),),
    }

    g4 = apply_coordinated_lora_gradients(
        (g4_parameter,),
        **gradients,
        variant="G4",
        physics_valid_fraction=0.5,
    )
    g4r = apply_coordinated_lora_gradients(
        (g4r_parameter,),
        **gradients,
        variant="G4R",
        physics_valid_fraction=0.5,
    )

    assert g4r == g4
    assert torch.equal(g4r_parameter.grad, g4_parameter.grad)


def test_private_state_anchor_metric_only_marks_g4r() -> None:
    parameter = torch.nn.Parameter(torch.zeros(3))
    diagnostics = apply_coordinated_lora_gradients(
        (parameter,),
        generation_gradients=(torch.tensor([1.0, 0.0, 0.0]),),
        state_gradients=(torch.tensor([0.0, 1.0, 0.0]),),
        physics_gradients=(torch.tensor([0.0, 0.0, 1.0]),),
        variant="G4R",
        physics_valid_fraction=1.0,
    )
    common = {
        "generation_loss": 1.0,
        "state_loss": 2.0,
        "physics_loss": 3.0,
        "diagnostics": diagnostics,
        "lora_gradient_norm": 1.0,
        "state_head_gradient_norm": 1.0,
        "learning_rate": 2e-4,
        "throughput": 1.0,
        "peak_memory_mib": 1.0,
    }

    g4r = _step_metrics(variant="G4R", **common)

    for variant in ("G2", "G3", "G4", "G5", "G5-STOP-RESPONSE"):
        metrics = _step_metrics(variant=variant, **common)
        assert metrics["coordination/private_state_anchor_forced"] == 0.0
    assert g4r["coordination/private_state_anchor_forced"] == 1.0


def test_state_head_uses_only_accepted_private_targets() -> None:
    parameter = torch.nn.Parameter(torch.zeros(1))
    state_only = CoordinationSolution(
        weights=(0.98, 0.02, 0.0),
        margins=(0.98, 0.02, 0.0),
        objective=-1.0,
        active_auxiliaries=("state",),
        fallback_to_generation=False,
    )

    apply_private_state_head_gradients(
        (parameter,),
        state_gradients=(torch.tensor([2.0]),),
        physics_gradients=(torch.tensor([100.0]),),
        solution=state_only,
        lambda_state=1.0,
        lambda_physics=0.01,
        physics_reliability=1.0,
        variant="G4",
    )

    assert parameter.grad == pytest.approx(torch.tensor([2.0]))


def test_physics_valid_fraction_uses_existing_record_contract() -> None:
    valid = _physics_sample()
    invalid = _physics_sample()
    invalid["sample_id"] = "sample-invalid"
    invalid["model_inputs"] = {
        **invalid["model_inputs"],  # type: ignore[dict-item]
        "configured_capacity_integral_link_bytes": [0.0, 10.0, 10.0, 10.0],
    }

    assert physics_batch_valid_fraction((valid, invalid)) == pytest.approx(0.5)


def test_settings_fix_batch_state_mode_and_g3_powers(tmp_path: Path) -> None:
    settings = _build_settings(
        _training_mapping(),
        variant="g3",
        output_dir=tmp_path / "run",
        max_steps=202,
        validation_limit=None,
    )

    assert settings.variant == "G3"
    assert settings.effective_generation_batch_size == 16
    assert settings.physics_batch_size == 4
    assert settings.state_supervision_mode == "anchor0_only"
    assert settings.asymmetric_powers == (0.6, 0.2, 0.2)


def test_settings_accept_independent_g4r_variant(tmp_path: Path) -> None:
    settings = _build_settings(
        _training_mapping(),
        variant="g4r",
        output_dir=tmp_path / "run",
        max_steps=2,
        validation_limit=8,
    )

    assert settings.variant == "G4R"
    assert not settings.uses_g5_response


def test_settings_accept_g4r_dual_anchor_state_mode(tmp_path: Path) -> None:
    settings = _build_settings(
        _training_mapping("anchor0_plus_one"),
        variant="g4r",
        output_dir=tmp_path / "run",
        max_steps=2,
        validation_limit=8,
    )

    assert settings.variant == "G4R"
    assert settings.state_supervision_mode == "anchor0_plus_one"


@pytest.mark.parametrize("variant", ("G2", "G3", "G4", "G5", "G5-STOP-RESPONSE"))
def test_settings_reject_dual_anchor_for_other_variants(tmp_path: Path, variant: str) -> None:
    with pytest.raises(GameTrainingError, match="必须使用 anchor0_only"):
        _build_settings(
            _training_mapping("anchor0_plus_one"),
            variant=variant,
            output_dir=tmp_path / "run",
            max_steps=2,
            validation_limit=8,
        )


def test_state_mask_persists_dual_anchor_mode_and_each_mask_structure(
    tmp_path: Path,
) -> None:
    records = [{"sample_id": f"sample-{index}", "group_id": f"group-{index}"} for index in range(8)]
    masks = build_state_supervision_masks(records, "anchor0_plus_one", 42)
    path = tmp_path / "state_mask.json"

    _write_state_mask(path, masks, mode="anchor0_plus_one")

    artifact = json.loads(path.read_text(encoding="utf-8"))
    persisted_masks = {sample["sample_id"]: tuple(sample["mask"]) for sample in artifact["samples"]}
    assert artifact["mode"] == "anchor0_plus_one"
    assert persisted_masks == masks
    assert all(
        mask[0] and sum(mask) == 2 and sum(mask[1:]) == 1 for mask in persisted_masks.values()
    )


def test_step_metrics_are_persisted_and_logged_online(tmp_path: Path) -> None:
    class Recorder:
        def __init__(self) -> None:
            self.calls: list[tuple[dict[str, float], int]] = []

        def log(self, metrics: dict[str, float], step: int) -> None:
            self.calls.append((metrics, step))

    recorder = Recorder()
    metrics = {name: float(index) for index, name in enumerate(GAME_STEP_METRIC_KEYS)}
    path = tmp_path / "step_metrics.jsonl"

    record_game_step_metrics(path, recorder, step=1, metrics=metrics)

    record = json.loads(path.read_text(encoding="utf-8"))
    assert record == {"step": 1, "metrics": metrics}
    assert recorder.calls == [(metrics, 1)]


def test_layout_requires_local_online_and_model_artifacts(tmp_path: Path) -> None:
    layout = create_game_run_layout(tmp_path / "run")

    assert layout.sample_order.name == "sample_order.json"
    assert layout.state_mask.name == "state_mask.json"
    assert layout.required_paths[-1] == layout.output_dir / "swanlog" / "game-train"
    with pytest.raises(GameTrainingError, match="制品不完整"):
        validate_game_artifacts(layout)


def test_g5_settings_keep_fixed_budget_and_enable_stop_response(tmp_path: Path) -> None:
    settings = _build_settings(
        _training_mapping(),
        variant="g5-stop-response",
        output_dir=tmp_path / "run",
        max_steps=2,
        validation_limit=8,
    )

    assert settings.variant == "G5-STOP-RESPONSE"
    assert settings.uses_g5_response
    assert settings.stops_g5_response
    assert settings.coordinator_learning_rate == pytest.approx(2e-4)


def test_functional_adamw_matches_real_single_step_tensor_by_tensor() -> None:
    parameter = torch.nn.Parameter(torch.tensor([1.5, -0.5], dtype=torch.float64))
    optimizer = torch.optim.AdamW(
        (parameter,),
        lr=0.01,
        betas=(0.8, 0.9),
        eps=1e-7,
        weight_decay=0.1,
    )
    gradient = torch.tensor([0.25, -0.75], dtype=torch.float64)

    response = functional_adamw_step((parameter,), (gradient,), optimizer)
    parameter.grad = gradient.clone()
    optimizer.step()

    assert parameter.detach() == pytest.approx(response.parameters[0].detach())
    assert optimizer.state[parameter]["exp_avg"] == pytest.approx(response.exp_avgs[0].detach())
    assert optimizer.state[parameter]["exp_avg_sq"] == pytest.approx(
        response.exp_avg_sqs[0].detach()
    )
    assert int(optimizer.state[parameter]["step"].item()) == response.steps[0] == 1


def test_g5_stop_response_follower_gradients_equal_g4() -> None:
    lora = torch.nn.Parameter(torch.zeros(3))
    state_head = torch.nn.Parameter(torch.zeros(1))
    generation = (torch.tensor([1.0, 0.0, 0.0]),)
    state = (torch.tensor([0.0, 1.0, 0.0]),)
    physics = (torch.tensor([0.0, 0.0, 1.0]),)
    head_state = (torch.tensor([2.0]),)
    head_physics = (torch.tensor([3.0]),)
    diagnostics = apply_coordinated_lora_gradients(
        (lora,),
        generation_gradients=generation,
        state_gradients=state,
        physics_gradients=physics,
        variant="G4",
        physics_valid_fraction=1.0,
    )
    apply_private_state_head_gradients(
        (state_head,),
        state_gradients=head_state,
        physics_gradients=head_physics,
        solution=diagnostics.solution,
        lambda_state=1.0,
        lambda_physics=0.01,
        physics_reliability=diagnostics.physics_reliability,
        variant="G4",
    )
    base_lora = (lora.grad.detach().float().clone(),)
    base_head = (state_head.grad.detach().float().clone(),)

    follower_lora, follower_head = build_g5_follower_gradients(
        (lora,),
        (state_head,),
        generation_gradients=generation,
        state_lora_gradients=state,
        physics_lora_gradients=physics,
        state_head_state_gradients=head_state,
        state_head_physics_gradients=head_physics,
        base_lora_gradients=base_lora,
        base_state_head_gradients=base_head,
        base_diagnostics=diagnostics,
        coordinated_weights=torch.tensor(diagnostics.solution.weights, dtype=torch.float64),
        lambda_state=1.0,
        lambda_physics=0.01,
        stop_response=True,
    )

    assert torch.equal(follower_lora[0], base_lora[0])
    assert torch.equal(follower_head[0], base_head[0])


def test_differentiable_global_clip_preserves_weight_gradient() -> None:
    parameter = torch.nn.Parameter(torch.zeros(2))
    weight = torch.tensor(2.0, requires_grad=True)
    gradients, total_norm, coefficient = differentiable_clip_grad_norm(
        (parameter,),
        (weight * torch.tensor([3.0, 4.0]),),
        1.0,
    )
    derivative = torch.autograd.grad(gradients[0].sum(), weight)[0]

    assert total_norm.detach().item() == pytest.approx(10.0)
    assert coefficient < 1.0
    assert torch.isfinite(derivative)


def test_two_step_functional_commit_matches_real_adamw_stop_baseline() -> None:
    real_parameters = (
        torch.nn.Parameter(torch.tensor([1.0, -2.0], dtype=torch.float64)),
        torch.nn.Parameter(torch.tensor([0.5], dtype=torch.float64)),
    )
    virtual_parameters = tuple(
        torch.nn.Parameter(parameter.detach().clone()) for parameter in real_parameters
    )
    real_optimizer = torch.optim.AdamW(real_parameters, lr=2e-4)
    virtual_optimizer = torch.optim.AdamW(virtual_parameters, lr=2e-4)
    gradients = (
        torch.tensor([3.0, 4.0], dtype=torch.float64),
        torch.tensor([2.0], dtype=torch.float64),
    )

    for _ in range(2):
        real_optimizer.zero_grad(set_to_none=True)
        for parameter, gradient in zip(real_parameters, gradients, strict=True):
            parameter.grad = gradient.clone()
        torch.nn.utils.clip_grad_norm_(real_parameters, 1.0)
        real_optimizer.step()

        clipped, _, _ = differentiable_clip_grad_norm(
            virtual_parameters,
            gradients,
            1.0,
        )
        response = functional_adamw_step(
            virtual_parameters,
            clipped,
            virtual_optimizer,
        )
        commit_functional_adamw_step(
            virtual_parameters,
            virtual_optimizer,
            response,
        )

    for real, virtual in zip(real_parameters, virtual_parameters, strict=True):
        assert torch.equal(real.detach(), virtual.detach())
        assert torch.equal(
            real_optimizer.state[real]["exp_avg"],
            virtual_optimizer.state[virtual]["exp_avg"],
        )
        assert torch.equal(
            real_optimizer.state[real]["exp_avg_sq"],
            virtual_optimizer.state[virtual]["exp_avg_sq"],
        )


def test_g5_step_metrics_require_complete_reaction_fields(tmp_path: Path) -> None:
    class Recorder:
        def log(self, metrics: dict[str, float], step: int) -> None:
            assert step == 1
            assert set(G5_STEP_METRIC_KEYS).issubset(metrics)

    metrics = {name: float(index) for index, name in enumerate(GAME_STEP_METRIC_KEYS)}
    metrics.update({name: float(index) for index, name in enumerate(G5_STEP_METRIC_KEYS)})

    record_game_step_metrics(
        tmp_path / "g5-step.jsonl",
        Recorder(),
        step=1,
        metrics=metrics,
    )
