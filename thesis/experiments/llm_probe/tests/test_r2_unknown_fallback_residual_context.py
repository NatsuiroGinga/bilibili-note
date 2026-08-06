import torch

from flow_probe.r2_final_experts import (
    EXPERT_UNKNOWN,
    ExpertConfig,
    ResidualObservationContext,
    create_physics_expert,
)


def test_unknown_fallback_accepts_and_ignores_residual_context() -> None:
    expert = create_physics_expert(
        ExpertConfig(
            name=EXPERT_UNKNOWN,
            input_dimension=3,
            hidden_dimension=4,
            representation_dimension=4,
            state_dimension=2,
            residual_dimension=2,
            layer_count=1,
            dropout=0.0,
            enabled=True,
            required_truth_fields=(),
        )
    )
    observations = torch.ones((2, 4, 3), dtype=torch.float32)
    valid_mask = torch.tensor([[True, True, False, False], [True, True, True, True]])
    active_mask = torch.tensor([True, False])
    residual_context = ResidualObservationContext(
        observed_state=torch.ones((2, 4, 2), dtype=torch.float32),
        observed_mask=torch.ones((2, 4, 2), dtype=torch.bool),
    )

    output = expert(
        observations,
        valid_mask,
        active_mask=active_mask,
        residual_context=residual_context,
    )

    assert torch.count_nonzero(output.representation) == 0
    assert torch.count_nonzero(output.predicted_state) == 0
    assert torch.count_nonzero(output.physics_residual) == 0
