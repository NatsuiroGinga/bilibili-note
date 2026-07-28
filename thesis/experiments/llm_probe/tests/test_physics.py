import pytest
import torch

from flow_probe.physics import PhysicsConstraintError, multiscale_queue_balance_residual


def _conservative_sequence(scale: float = 1.0) -> dict[str, torch.Tensor]:
    arrivals = torch.tensor([[20.0, 30.0, 80.0, 10.0]]) * scale
    departures = torch.tensor([[10.0, 25.0, 40.0, 25.0]]) * scale
    drops = torch.tensor([[0.0, 0.0, 15.0, 0.0]]) * scale
    consumed = torch.tensor([[0.0, 0.0, 0.0, 0.0]]) * scale
    queues = [torch.tensor([5.0]) * scale]
    for index in range(arrivals.shape[1]):
        queues.append(
            queues[-1]
            + arrivals[:, index]
            - departures[:, index]
            - drops[:, index]
            - consumed[:, index]
        )
    return {
        "predicted_queue": torch.stack(queues, dim=1),
        "arrivals": arrivals,
        "departures": departures,
        "drops": drops,
        "consumed": consumed,
        "capacity": torch.tensor([100.0]) * scale,
    }


def test_multiscale_residual_is_zero_for_conservative_attack_sequence() -> None:
    data = _conservative_sequence()

    residuals = multiscale_queue_balance_residual(
        **data,
        delta_seconds=1.0,
        horizons=(1, 2, 4),
    )

    assert set(residuals) == {1, 2, 4}
    assert residuals[1].shape == (1, 4)
    assert residuals[2].shape == (1, 3)
    assert residuals[4].shape == (1, 1)
    assert all(torch.allclose(value, torch.zeros_like(value)) for value in residuals.values())


def test_capacity_normalization_makes_residual_invariant_to_byte_scale() -> None:
    base = _conservative_sequence()
    scaled = _conservative_sequence(scale=1024.0)
    base["predicted_queue"][:, -1] += 5.0
    scaled["predicted_queue"][:, -1] += 5.0 * 1024.0

    base_residual = multiscale_queue_balance_residual(**base, delta_seconds=1.0, horizons=(4,))[4]
    scaled_residual = multiscale_queue_balance_residual(**scaled, delta_seconds=1.0, horizons=(4,))[
        4
    ]

    assert torch.allclose(base_residual, scaled_residual)


def test_physics_loss_has_nonzero_gradient_to_shared_model_parameters() -> None:
    data = _conservative_sequence()
    model = torch.nn.Linear(1, 5, bias=False)
    predicted_queue = model(torch.ones((1, 1)))

    residuals = multiscale_queue_balance_residual(
        predicted_queue=predicted_queue,
        arrivals=data["arrivals"],
        departures=data["departures"],
        drops=data["drops"],
        consumed=data["consumed"],
        capacity=data["capacity"],
        delta_seconds=1.0,
        horizons=(1, 2, 4),
    )
    loss = sum(value.square().mean() for value in residuals.values())
    loss.backward()

    assert model.weight.grad is not None
    assert torch.linalg.vector_norm(model.weight.grad).item() > 0.0


def test_multiscale_residual_rejects_horizon_beyond_sequence() -> None:
    data = _conservative_sequence()

    with pytest.raises(PhysicsConstraintError, match="时间跨度"):
        multiscale_queue_balance_residual(
            **data,
            delta_seconds=1.0,
            horizons=(5,),
        )
