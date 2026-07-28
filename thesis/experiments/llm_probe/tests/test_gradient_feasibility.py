from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
import torch

from flow_probe.gradient_feasibility import (
    DirectionSolution,
    GradientFeasibilityError,
    _create_layout,
    build_feasibility_schedule,
    direction_margins,
    g5_response_proxy,
    gradient_gram_matrix,
    has_dual_auxiliary_participation,
    has_strict_common_descent,
    is_generation_vetoed,
    solve_common_descent,
    solve_generation_protected_direction,
    validate_gram_matrix,
)


def test_direction_solution_is_immutable() -> None:
    solution = DirectionSolution(
        weights=(1.0, 0.0, 0.0),
        margins=(1.0, 0.0, 0.0),
        objective=0.0,
    )

    with pytest.raises(FrozenInstanceError):
        solution.objective = 1.0  # type: ignore[misc]


def test_common_and_protected_solvers_use_deterministic_integer_simplex() -> None:
    gram = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    common = solve_common_descent(gram, resolution=0.02)
    protected = solve_generation_protected_direction(
        gram,
        generation_floor=0.95,
        resolution=0.02,
    )

    assert common.weights == pytest.approx((0.36, 0.32, 0.32))
    assert common.margins == pytest.approx(common.weights)
    assert common.objective == pytest.approx(0.32)
    assert has_strict_common_descent(common)
    assert is_generation_vetoed(common, generation_floor=0.95)
    assert protected.weights == pytest.approx((0.96, 0.02, 0.02))
    assert protected.margins == pytest.approx(protected.weights)
    assert protected.objective == pytest.approx(0.02)
    assert has_dual_auxiliary_participation(protected)


def test_conflicting_gram_has_no_strict_common_descent() -> None:
    gram = ((1.0, -1.0, 0.0), (-1.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    solution = solve_common_descent(gram, resolution=0.02)

    assert solution.objective == pytest.approx(0.0)
    assert not has_strict_common_descent(solution)


@pytest.mark.parametrize(
    ("gram", "message"),
    [
        (((1.0, 0.0), (0.0, 1.0)), "3x3"),
        (
            ((1.0, 0.2, 0.0), (0.1, 1.0, 0.0), (0.0, 0.0, 1.0)),
            "对称",
        ),
        (
            ((1.0, 0.0, 0.0), (0.0, 0.9, 0.0), (0.0, 0.0, 1.0)),
            "对角线",
        ),
        (
            ((1.0, 0.9, 0.9), (0.9, 1.0, -0.9), (0.9, -0.9, 1.0)),
            "半正定",
        ),
    ],
)
def test_validate_gram_matrix_rejects_invalid_contract(
    gram: tuple[tuple[float, ...], ...], message: str
) -> None:
    with pytest.raises(GradientFeasibilityError, match=message):
        validate_gram_matrix(gram)


def test_solver_rejects_resolution_that_does_not_partition_one() -> None:
    gram = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    with pytest.raises(GradientFeasibilityError, match="整数划分"):
        solve_common_descent(gram, resolution=0.03)


def test_gradient_gram_and_g5_response_use_per_parameter_tensors() -> None:
    generation = (torch.tensor([1.0, 0.0]), torch.tensor([0.0, 2.0]))
    state = (torch.tensor([1.0, 0.0]), torch.tensor([0.0, -2.0]))
    physics = (torch.tensor([0.0, 1.0]), torch.tensor([0.0, 0.0]))

    gram = gradient_gram_matrix(generation, state, physics)

    assert gram[0][1] == pytest.approx(-0.6)
    assert gram[0][2] == pytest.approx(0.0)
    assert gram[1][2] == pytest.approx(0.0)
    assert g5_response_proxy(generation, state) == pytest.approx(-0.6)
    assert g5_response_proxy(generation, physics) == pytest.approx(0.0)


def test_direction_margins_rejects_non_simplex_weights() -> None:
    gram = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    with pytest.raises(GradientFeasibilityError, match="单位单纯形"):
        direction_margins(gram, (0.5, 0.5, 0.5))


def test_feasibility_schedule_is_deterministic_and_uses_three_independent_streams() -> None:
    first = build_feasibility_schedule(
        generation_train_sample_count=15_000,
        generation_validation_sample_count=2_700,
        physics_sample_count=807,
        paired_batches=2,
        generation_batch_size=4,
        generation_accumulation_steps=4,
        physics_batch_size=4,
        seed=42,
    )
    repeated = build_feasibility_schedule(
        generation_train_sample_count=15_000,
        generation_validation_sample_count=2_700,
        physics_sample_count=807,
        paired_batches=2,
        generation_batch_size=4,
        generation_accumulation_steps=4,
        physics_batch_size=4,
        seed=42,
    )

    assert first == repeated
    assert len(first) == 2
    assert all(len(batch.generation_train_microbatches) == 4 for batch in first)
    assert all(len(batch.generation_validation_microbatches) == 4 for batch in first)
    assert all(len(batch.physics_indices) == 4 for batch in first)
    train_order = tuple(
        index
        for batch in first
        for indices in batch.generation_train_microbatches
        for index in indices
    )
    validation_order = tuple(
        index
        for batch in first
        for indices in batch.generation_validation_microbatches
        for index in indices
    )
    assert train_order != validation_order


def test_layout_declares_exact_ten_artifact_classes(tmp_path) -> None:
    layout = _create_layout(tmp_path / "diagnostic")

    assert len(layout.required_paths) == 10
    assert layout.config_snapshot.name == "config.snapshot.yaml"
    assert layout.state_mask.name == "state_mask.json"
    assert layout.required_paths[-2] == layout.output_dir / "swanlog" / "gradient-feasibility"
    assert layout.artifact_manifest.name == "artifact_manifest.json"
