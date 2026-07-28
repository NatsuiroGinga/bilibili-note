from __future__ import annotations

import math

import pytest

from flow_probe.asymmetric_physics_train import (
    D3_MIN_LEARNING_RATE,
    D3_PEAK_LEARNING_RATE,
    D3_WARMUP_STEPS,
    FORMAL_DIAGNOSTIC_STEPS,
    diagnostic_learning_rate,
    resolve_diagnostic_mode,
)
from flow_probe.physics_train import PhysicsTrainingError


def test_pre_registered_modes_have_exact_loss_switches() -> None:
    expected = {
        "joint_constant": (True, True, True, "constant"),
        "generation_only": (True, False, False, "constant"),
        "physics_only": (False, True, True, "constant"),
        "joint_warmup_cosine": (
            True,
            True,
            True,
            "linear_warmup_cosine_decay",
        ),
    }

    actual = {
        name: (
            contract.generation_loss_enabled,
            contract.state_loss_enabled,
            contract.physics_loss_enabled,
            contract.learning_rate_schedule,
        )
        for name in expected
        for contract in (resolve_diagnostic_mode(name),)
    }

    assert actual == expected


def test_unknown_diagnostic_mode_is_rejected() -> None:
    with pytest.raises(PhysicsTrainingError, match="未知诊断模式"):
        resolve_diagnostic_mode("temporary_variant")


def test_d3_learning_rate_has_fixed_key_points_and_is_monotonic() -> None:
    expected_step_21 = D3_MIN_LEARNING_RATE + 0.5 * (
        D3_PEAK_LEARNING_RATE - D3_MIN_LEARNING_RATE
    ) * (
        1.0
        + math.cos(math.pi * (21 - D3_WARMUP_STEPS) / (FORMAL_DIAGNOSTIC_STEPS - D3_WARMUP_STEPS))
    )
    assert diagnostic_learning_rate("joint_warmup_cosine", 1) == pytest.approx(D3_MIN_LEARNING_RATE)
    assert diagnostic_learning_rate("joint_warmup_cosine", D3_WARMUP_STEPS) == pytest.approx(
        D3_PEAK_LEARNING_RATE
    )
    assert diagnostic_learning_rate("joint_warmup_cosine", 21) == pytest.approx(expected_step_21)
    assert diagnostic_learning_rate(
        "joint_warmup_cosine", FORMAL_DIAGNOSTIC_STEPS
    ) == pytest.approx(D3_MIN_LEARNING_RATE)

    values = [
        diagnostic_learning_rate("joint_warmup_cosine", step)
        for step in range(1, FORMAL_DIAGNOSTIC_STEPS + 1)
    ]
    assert all(left <= right for left, right in zip(values[:19], values[1:20], strict=True))
    assert all(left >= right for left, right in zip(values[19:-1], values[20:], strict=True))


@pytest.mark.parametrize("mode", ("joint_constant", "generation_only", "physics_only"))
def test_constant_modes_keep_peak_learning_rate(mode: str) -> None:
    assert diagnostic_learning_rate(mode, 1) == pytest.approx(D3_PEAK_LEARNING_RATE)
    assert diagnostic_learning_rate(mode, FORMAL_DIAGNOSTIC_STEPS) == pytest.approx(
        D3_PEAK_LEARNING_RATE
    )
