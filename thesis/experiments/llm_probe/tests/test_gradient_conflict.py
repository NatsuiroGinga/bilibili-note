from __future__ import annotations

from types import SimpleNamespace

import pytest
import torch

import flow_probe.gradient_conflict as gradient_conflict
from flow_probe.gradient_conflict import (
    GradientDiagnosticError,
    build_paired_schedule,
    gradient_triplet_summary,
)


def test_gradient_triplet_summary_accumulates_per_parameter_tensor() -> None:
    generation = (torch.tensor([1.0, 0.0]), torch.tensor([0.0, 2.0]))
    state = (torch.tensor([1.0, 0.0]), torch.tensor([0.0, -2.0]))
    physics = (torch.tensor([-1.0, 0.0]), torch.tensor([0.0, 2.0]))

    summary = gradient_triplet_summary(
        generation,
        state,
        physics,
        lambda_physics=(0.001, 0.01, 0.03, 0.1),
    )

    assert summary.generation_norm == pytest.approx(5**0.5)
    assert summary.state_norm == pytest.approx(5**0.5)
    assert summary.physics_norm == pytest.approx(5**0.5)
    assert summary.cosine_generation_state == pytest.approx(-0.6)
    assert summary.cosine_generation_physics == pytest.approx(0.6)
    assert summary.cosine_state_physics == pytest.approx(-1.0)
    assert summary.weighted_physics_to_generation["0.001"] == pytest.approx(0.001)
    assert summary.weighted_physics_to_state["0.1"] == pytest.approx(0.1)


@pytest.mark.parametrize(
    ("generation", "physics", "message"),
    [
        ((torch.zeros(2),), (torch.ones(2),), "生成梯度严格为零"),
        ((torch.ones(2),), (torch.tensor([float("nan")]),), "物理梯度包含非有限值"),
    ],
)
def test_gradient_triplet_summary_rejects_invalid_objective_gradients(
    generation: tuple[torch.Tensor, ...],
    physics: tuple[torch.Tensor, ...],
    message: str,
) -> None:
    with pytest.raises(GradientDiagnosticError, match=message):
        gradient_triplet_summary(
            generation,
            (torch.ones(2),),
            physics,
            lambda_physics=(0.001,),
        )


def test_paired_schedule_preserves_training_batch_sizes_and_seed() -> None:
    first = build_paired_schedule(
        generation_sample_count=15_000,
        physics_sample_count=807,
        paired_batches=20,
        generation_batch_size=4,
        generation_accumulation_steps=4,
        physics_batch_size=4,
        seed=42,
    )
    repeated = build_paired_schedule(
        generation_sample_count=15_000,
        physics_sample_count=807,
        paired_batches=20,
        generation_batch_size=4,
        generation_accumulation_steps=4,
        physics_batch_size=4,
        seed=42,
    )

    assert first == repeated
    assert len(first) == 20
    assert all(len(batch.generation_microbatches) == 4 for batch in first)
    assert all(len(indices) == 4 for batch in first for indices in batch.generation_microbatches)
    assert all(len(batch.physics_indices) == 4 for batch in first)


def test_state_and_physics_gradients_use_optional_sparse_state_mask(monkeypatch) -> None:
    parameter = torch.nn.Parameter(torch.tensor([1.0]))

    class ToyModel:
        def __call__(self, **kwargs):
            batch_size = kwargs["input_ids"].shape[0]
            hidden = parameter.reshape(1, 1, 1).expand(batch_size, 1, 1)
            return SimpleNamespace(hidden_states=(hidden,))

    class ToyStateHead(torch.nn.Module):
        def forward(self, hidden):
            return hidden.expand(-1, 5)

    def fake_state_batch(
        records,
        tokenizer,
        max_length,
        device,
        *,
        include_fluxes,
        state_masks=None,
    ):
        del tokenizer, max_length
        assert include_fluxes
        result = {
            "input_ids": torch.ones((len(records), 1), dtype=torch.long, device=device),
            "attention_mask": torch.ones((len(records), 1), dtype=torch.long, device=device),
            "state_targets": torch.tensor(
                [[0.0, 0.0, 0.0, 0.0, 10.0]], dtype=torch.float32, device=device
            ).expand(len(records), -1),
        }
        for name in (
            "scale",
            "capacity",
            "received",
            "dequeued",
            "dropped_before",
            "dropped_after",
        ):
            result[name] = torch.ones((len(records), 4), device=device)
        if state_masks is not None:
            result["state_mask"] = torch.tensor(
                [state_masks[str(record["sample_id"])] for record in records],
                dtype=torch.bool,
                device=device,
            )
        return result

    monkeypatch.setattr(gradient_conflict, "_state_batch", fake_state_batch)
    monkeypatch.setattr(
        gradient_conflict,
        "queue_balance_residual",
        lambda predicted, *args: predicted.sum(dim=1),
    )
    records = ({"sample_id": "sample-1"},)
    dense = gradient_conflict._state_and_physics_gradients(
        ToyModel(),
        ToyStateHead(),
        object(),
        (parameter,),
        records,
        (0,),
        max_length=8,
        device=torch.device("cpu"),
    )
    sparse = gradient_conflict._state_and_physics_gradients(
        ToyModel(),
        ToyStateHead(),
        object(),
        (parameter,),
        records,
        (0,),
        max_length=8,
        device=torch.device("cpu"),
        state_masks={"sample-1": (True, False, False, False, False)},
    )

    assert dense[0] == pytest.approx(17.0)
    assert sparse[0] == pytest.approx(1.0)
    assert dense[2][0] == pytest.approx(torch.tensor([-2.0]))
    assert sparse[2][0] == pytest.approx(torch.tensor([2.0]))
    assert dense[1] == sparse[1]
    assert dense[3][0] == pytest.approx(sparse[3][0])
