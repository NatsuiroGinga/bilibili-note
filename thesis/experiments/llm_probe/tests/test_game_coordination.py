from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
import torch

from flow_probe.game_coordination import (
    CoordinationSolution,
    G5Coordinator,
    GameCoordinationError,
    build_g5_diagnostics,
    coordinate_g5_response,
    g5_projection_jacobian_norm,
    solve_asymmetric_bargaining,
    solve_reliability_protected,
    solve_symmetric_bargaining,
)


IDENTITY_GRAM = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def test_coordination_solution_is_immutable_and_exposes_acceptance() -> None:
    solution = CoordinationSolution(
        weights=(0.6, 0.2, 0.2),
        margins=(0.6, 0.2, 0.2),
        objective=-1.0,
        active_auxiliaries=("state", "physics"),
        fallback_to_generation=False,
    )

    assert solution.accepts_state and solution.accepts_physics
    with pytest.raises(FrozenInstanceError):
        solution.objective = 0.0  # type: ignore[misc]


def test_g2_maximizes_equal_log_margins_on_deterministic_grid() -> None:
    solution = solve_symmetric_bargaining(IDENTITY_GRAM, 0.02)

    assert solution.weights == pytest.approx((0.34, 0.34, 0.32))
    assert solution.margins == pytest.approx(solution.weights)
    assert solution.accepts_state and solution.accepts_physics
    assert not solution.fallback_to_generation


def test_g3_recovers_fixed_asymmetric_powers_for_orthogonal_objectives() -> None:
    solution = solve_asymmetric_bargaining(IDENTITY_GRAM, (0.6, 0.2, 0.2), 0.02)

    assert solution.weights == pytest.approx((0.6, 0.2, 0.2))
    assert solution.margins == pytest.approx(solution.weights)


def test_g2_and_g3_fall_back_when_strict_common_improvement_is_impossible() -> None:
    conflicting = ((1.0, -1.0, 0.0), (-1.0, 1.0, 0.0), (0.0, 0.0, 1.0))

    symmetric = solve_symmetric_bargaining(conflicting, 0.02)
    asymmetric = solve_asymmetric_bargaining(conflicting, (0.6, 0.2, 0.2), 0.02)

    assert symmetric.weights == asymmetric.weights == (1.0, 0.0, 0.0)
    assert symmetric.fallback_to_generation and asymmetric.fallback_to_generation


def test_g4_enforces_generation_floor_and_records_veto() -> None:
    solution = solve_reliability_protected(IDENTITY_GRAM, 1.0, 0.95, 0.02)

    assert solution.margins[0] >= 0.95
    assert solution.generation_vetoed
    assert solution.accepts_state or solution.accepts_physics
    assert not solution.fallback_to_generation


def test_g4_reliability_zero_rejects_physics_but_can_accept_state() -> None:
    aligned = ((1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))

    solution = solve_reliability_protected(aligned, 0.0, 0.95, 0.02)

    assert solution.accepts_state
    assert not solution.accepts_physics
    assert solution.weights == pytest.approx((0.98, 0.02, 0.0))


def test_g4_can_keep_both_auxiliaries_when_all_directions_are_aligned() -> None:
    aligned = ((1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))

    solution = solve_reliability_protected(aligned, 1.0, 0.95, 0.02)

    assert solution.active_auxiliaries == ("state", "physics")
    assert solution.weights == pytest.approx((0.96, 0.02, 0.02))


def test_g4_falls_back_to_pure_generation_when_no_auxiliary_is_feasible() -> None:
    opposing = ((1.0, -1.0, -1.0), (-1.0, 1.0, 1.0), (-1.0, 1.0, 1.0))

    solution = solve_reliability_protected(opposing, 1.0, 0.95, 0.02)

    assert solution.weights == (1.0, 0.0, 0.0)
    assert solution.fallback_to_generation
    assert not solution.accepts_state and not solution.accepts_physics


@pytest.mark.parametrize(
    ("powers", "message"),
    [
        ((0.6, 0.4), "三个分量"),
        ((0.6, 0.2, 0.1), "之和"),
        ((0.6, 0.4, 0.0), "有限正数"),
    ],
)
def test_g3_rejects_invalid_bargaining_powers(powers: tuple[float, ...], message: str) -> None:
    with pytest.raises(GameCoordinationError, match=message):
        solve_asymmetric_bargaining(IDENTITY_GRAM, powers, 0.02)


@pytest.mark.parametrize("reliability", [-0.1, 1.1, float("nan")])
def test_g4_rejects_invalid_reliability(reliability: float) -> None:
    with pytest.raises(GameCoordinationError, match="可靠性"):
        solve_reliability_protected(IDENTITY_GRAM, reliability, 0.95, 0.02)


def _g5_base_solution() -> CoordinationSolution:
    return CoordinationSolution(
        weights=(0.96, 0.02, 0.02),
        margins=(0.96, 0.02, 0.02),
        objective=-1.0,
        active_auxiliaries=("state", "physics"),
        fallback_to_generation=False,
        generation_vetoed=True,
    )


def test_g5_coordinator_has_fixed_zero_initialized_parameter_blocks() -> None:
    coordinator = G5Coordinator()

    assert coordinator.A.shape == (2, 7)
    assert coordinator.b.shape == (2,)
    assert coordinator.A.dtype == coordinator.b.dtype == torch.float32
    assert torch.count_nonzero(coordinator.A) == 0
    assert torch.count_nonzero(coordinator.b) == 0


def test_g5_zero_response_returns_g4_weights_with_nonzero_projection_jacobian() -> None:
    coordinator = G5Coordinator()
    base = _g5_base_solution()
    diagnostics = build_g5_diagnostics(
        IDENTITY_GRAM,
        physics_valid_fraction=1.0,
        physics_reliability=1.0,
        base_solution=base,
        device=torch.device("cpu"),
    )
    response = coordinator(diagnostics)

    result = coordinate_g5_response(
        IDENTITY_GRAM,
        physics_reliability=1.0,
        base_solution=base,
        diagnostics=diagnostics,
        response=response,
    )

    assert torch.equal(
        result.coordinated_weights,
        torch.tensor(base.weights, dtype=torch.float64),
    )
    assert result.selected_auxiliary_subset == (1, 2)
    assert result.coordinated_margins[0] >= 0.95
    assert g5_projection_jacobian_norm(result) > 0.0


def test_g5_stop_response_is_exact_g4_value_and_has_zero_jacobian() -> None:
    coordinator = G5Coordinator()
    base = _g5_base_solution()
    diagnostics = build_g5_diagnostics(
        IDENTITY_GRAM,
        physics_valid_fraction=1.0,
        physics_reliability=1.0,
        base_solution=base,
        device=torch.device("cpu"),
    )
    result = coordinate_g5_response(
        IDENTITY_GRAM,
        physics_reliability=1.0,
        base_solution=base,
        diagnostics=diagnostics,
        response=coordinator(diagnostics),
        stop_response=True,
    )

    assert torch.equal(
        result.coordinated_weights,
        torch.tensor(base.weights, dtype=torch.float64),
    )
    assert g5_projection_jacobian_norm(result) == 0.0
