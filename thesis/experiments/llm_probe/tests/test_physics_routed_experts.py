from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import torch

from flow_probe.physics_routed_experts import (
    PhysicsRoutedExpertRuntime,
    RouteThresholds,
    SharedBasisStateExpert,
    calibrate_route_thresholds,
    hadamard_expert_codes,
    route_predicted_state,
)
from flow_probe.physics_routed_experts_analysis import (
    RoutedExpertAnalysisError,
    analyze_physics_routed_experts,
)


def test_threshold_calibration_and_growth_precedence() -> None:
    predicted = torch.tensor(
        [
            [1.0, 1.0, 1.0, 1.0, 1.0],
            [1.0, 1.0, 1.0, 1.0, 4.0],
            [9.0, 9.0, 9.0, 9.0, 9.0],
        ]
    )
    thresholds = calibrate_route_thresholds(predicted)
    expected_growth = float(torch.quantile(predicted[:, 4] - predicted[:, 0], 2.0 / 3.0))
    expected_pressure = float(torch.quantile(predicted.mean(dim=1), 2.0 / 3.0))
    assert thresholds == RouteThresholds(expected_growth, expected_pressure)

    routed = route_predicted_state(
        torch.tensor(
            [
                [1.0, 1.0, 1.0, 1.0, 1.0],
                [1.0, 1.0, 1.0, 1.0, 3.0],
                [8.0, 8.0, 8.0, 8.0, 8.0],
                [8.0, 8.0, 8.0, 8.0, 11.0],
            ]
        ),
        RouteThresholds(growth=2.0, pressure=5.0),
    )
    assert routed.tolist() == [0, 1, 2, 1]


@pytest.mark.parametrize(
    "predicted",
    [
        torch.ones(5),
        torch.ones(2, 4),
        torch.tensor([[1.0, 1.0, float("nan"), 1.0, 1.0]]),
        torch.tensor([[1.0, 1.0, -1.0, 1.0, 1.0]]),
    ],
)
def test_router_rejects_invalid_predicted_state(predicted: torch.Tensor) -> None:
    with pytest.raises(ValueError):
        calibrate_route_thresholds(predicted)


def test_hadamard_codes_are_fixed_full_support_and_orthogonal() -> None:
    codes = hadamard_expert_codes()
    assert codes.shape == (3, 16)
    assert torch.all(codes.abs() == 1)
    assert torch.equal(codes @ codes.T, 16 * torch.eye(3))
    assert torch.equal(codes, hadamard_expert_codes())
    with pytest.raises(ValueError, match="rank"):
        hadamard_expert_codes(8)


def test_shared_basis_expert_has_fixed_budget_zero_gate_and_bounded_gradient_path() -> None:
    torch.manual_seed(1)
    expert = SharedBasisStateExpert()
    hidden = torch.randn(3, 4, 2048)
    codes = hadamard_expert_codes()
    selected_codes = codes.index_select(0, torch.tensor([0, 1, 2]))
    mask = torch.ones(3, 4, dtype=torch.bool)

    zero_output, zero_ratio = expert(hidden, selected_codes, mask)
    assert torch.equal(zero_output, hidden)
    assert float(zero_ratio) == 0.0
    assert sum(parameter.numel() for parameter in expert.parameters()) == 2 * 2048 * 16 + 1

    expert.alpha.data.fill_(1.0)
    output, ratio = expert(hidden, selected_codes, mask)
    assert not torch.equal(output, hidden)
    assert 0.0 < float(ratio) <= 0.1 + 1e-6
    output.square().mean().backward()
    assert expert.down.weight.grad is not None
    assert expert.up.weight.grad is not None
    assert bool((expert.down.weight.grad != 0).any())
    assert bool((expert.up.weight.grad != 0).any())


@dataclass
class _FakeOutput:
    loss: torch.Tensor | None
    logits: torch.Tensor


class _FakeStateHead(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(2048, 5)
        with torch.no_grad():
            self.linear.weight.zero_()
            self.linear.bias.copy_(torch.tensor([0.0, 0.1, 0.2, 0.3, 1.0]))
        self.activation = torch.nn.Softplus()

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        return self.activation(self.linear(hidden.to(dtype=self.linear.weight.dtype)))


class _FakeDecoderLayer(torch.nn.Module):
    def __init__(self, index: int) -> None:
        super().__init__()
        self.bias = torch.nn.Parameter(torch.tensor((index + 1) / 1000.0))

    def forward(self, hidden_states: torch.Tensor, **_kwargs: Any) -> tuple[torch.Tensor]:
        return (hidden_states + self.bias.to(dtype=hidden_states.dtype),)


class _FakeBackbone(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.ModuleList(_FakeDecoderLayer(index) for index in range(28))


class _FakeQwen(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.config = SimpleNamespace(num_hidden_layers=28, hidden_size=2048)
        self.embedding = torch.nn.Embedding(64, 2048)
        self.model = _FakeBackbone()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
        **kwargs: Any,
    ) -> _FakeOutput:
        hidden = self.embedding(input_ids)
        for index, layer in enumerate(self.model.layers):
            if index % 2:
                hidden = layer(
                    hidden_states=hidden,
                    attention_mask=attention_mask,
                    **kwargs,
                )[0]
            else:
                hidden = layer(hidden, attention_mask=attention_mask, **kwargs)[0]
        loss = hidden.float().square().mean() if labels is not None else None
        return _FakeOutput(loss=loss, logits=hidden)

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        max_new_tokens: int = 2,
        num_beams: int = 1,
        **kwargs: Any,
    ) -> torch.Tensor:
        assert num_beams == 1
        sequences = input_ids
        running_attention = attention_mask
        for step in range(max_new_tokens):
            current = sequences if step == 0 else sequences[:, -1:]
            output = self.forward(
                current,
                running_attention,
                use_cache=True,
                **kwargs,
            )
            token = output.logits[:, -1, 0].abs().long().remainder(64)
            sequences = torch.cat((sequences, token.unsqueeze(1)), dim=1)
            running_attention = torch.cat(
                (
                    running_attention,
                    torch.ones(
                        (running_attention.shape[0], 1),
                        dtype=running_attention.dtype,
                    ),
                ),
                dim=1,
            )
        return sequences


def _runtime() -> tuple[PhysicsRoutedExpertRuntime, _FakeQwen]:
    torch.manual_seed(3)
    model = _FakeQwen()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    runtime = PhysicsRoutedExpertRuntime(
        model,
        _FakeStateHead(),
        RouteThresholds(growth=0.1, pressure=100.0),
        variant="routed",
    )
    return runtime, model


def _training_batch() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    input_ids = torch.tensor([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]])
    attention = torch.ones_like(input_ids)
    labels = torch.tensor([[-100, -100, -100, 4, 5], [-100, -100, -100, 2, 1]])
    return input_ids, attention, labels


def test_runtime_freezes_router_and_trains_outcome_and_shared_basis() -> None:
    runtime, model = _runtime()
    input_ids, attention, labels = _training_batch()
    try:
        assert all(
            not parameter.requires_grad for parameter in runtime.router_state_head.parameters()
        )
        assert all(parameter.requires_grad for parameter in runtime.outcome_state_head.parameters())
        assert runtime.unexpected_base_parameter_names() == ()
        assert all(
            name.startswith(("outcome_state_head.", "experts."))
            for name in runtime.trainable_parameter_names()
        )
        for expert in runtime.experts:
            expert.alpha.data.fill_(0.5)

        direct = model(input_ids=input_ids, attention_mask=attention, labels=labels)
        family = runtime(
            input_ids,
            attention,
            labels=labels,
            expert_row_mask=torch.zeros(2, dtype=torch.bool),
        )
        assert torch.equal(family.logits, direct.logits)

        output = runtime(
            input_ids,
            attention,
            labels=labels,
            expert_row_mask=torch.ones(2, dtype=torch.bool),
            fixed_expert=1,
        )
        assert output.route_ids is not None
        assert output.route_ids.tolist() == [1, 1]
        assert output.predicted_router_state is not None
        assert output.predicted_outcome_state is not None
        loss = output.logits.float().square().mean() + output.predicted_outcome_state.mean()
        loss.backward()
        assert any(
            parameter.grad is not None and bool((parameter.grad != 0).any())
            for parameter in runtime.shared_basis_parameters()
        )
        assert any(
            parameter.grad is not None and bool((parameter.grad != 0).any())
            for parameter in runtime.outcome_state_head.parameters()
        )
        assert all(parameter.grad is None for parameter in runtime.router_state_head.parameters())
        assert all(parameter.grad is None for parameter in model.parameters())
    finally:
        runtime.close()


def test_runtime_candidate_generation_bypass_override_and_removal_paths() -> None:
    runtime, model = _runtime()
    input_ids, attention, labels = _training_batch()
    try:
        for expert in runtime.experts:
            expert.alpha.data.fill_(0.75)
        bypass = runtime(input_ids, attention, labels=labels, bypass=True)
        direct = model(input_ids=input_ids, attention_mask=attention, labels=labels)
        assert torch.equal(bypass.logits, direct.logits)

        candidate = runtime.score_candidates(
            input_ids,
            attention,
            completion_start=torch.tensor([3, 3]),
            fixed_expert=2,
        )
        assert candidate.route_ids is not None
        assert candidate.route_ids.tolist() == [2, 2]
        removed = runtime(
            input_ids,
            attention,
            labels=labels,
            fixed_expert=2,
            removed_expert=2,
        )
        assert torch.equal(removed.logits, direct.logits)

        generated = runtime.generate(
            input_ids[:, :3],
            attention[:, :3],
            max_new_tokens=2,
            fixed_expert=0,
        )
        assert generated.route_ids is not None
        assert generated.route_ids.tolist() == [0, 0]
        assert generated.diagnostics.prefill_count == 1
        assert generated.diagnostics.cached_decode_count == 1
    finally:
        runtime.close()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def _analysis_run(root: Path, variant: str) -> None:
    root.mkdir()
    budget = {
        "target_layers": [24, 25, 26, 27],
        "rank_per_layer": 16,
        "rank_sum": 64,
        "full_rank_channels_activated_per_forward": 16,
        "shared_basis_parameter_count": 262144,
        "gate_parameter_count": 4,
        "outcome_state_head_parameter_count": 10245,
        "frozen_router_state_head_parameter_count": 10245,
        "trainable_parameter_count": 272393,
        "expected_trainable_parameter_count": 272393,
        "codes_are_parameters": False,
        "three_independent_lora_experts": False,
    }
    summary = {
        "variant": variant,
        "seed": 42,
        "max_steps": 50,
        "formal_probe": True,
        "budget": budget,
        "sample_order": {"generation_sha256": "g", "physics_sha256": "p"},
        "validation": {
            "subtype_generation_loss": 0.8 if variant == "routed" else 1.0,
            "state_mse_unobserved": 0.9 if variant == "routed" else 1.0,
            "physics_residual_mse": 1.0,
        },
    }
    calibration = {
        "calibration_source": "frozen_router_state_head_predictions_only",
        "unknown_attack_labels_used": False,
        "saved_raw_predictions": False,
    }
    contract = {
        "allowed_fields": [
            "predicted_state.q4_minus_q0",
            "predicted_state.mean_q0_to_q4",
        ],
        "rejected_fields": [
            "state_target",
            "queue_capacity",
            "received_throughput",
            "dequeued_throughput",
            "dropped_throughput",
            "attack_label",
            "dataset_source",
            "scenario_id",
            "unknown_attack_label",
        ],
        "family_expert_mask_fixed_false": True,
        "unknown_attack_labels_in_training_or_calibration": False,
    }
    codes = hadamard_expert_codes()
    usage = {
        split: {
            "rates": [0.3, 0.3, 0.4],
            "normalized_entropy": 0.99,
        }
        for split in ("subtype_generation_validation", "physics_validation")
    }
    specialization = {
        "joint_loss_matrix": [[1.0, 2.0, 3.0], [2.0, 1.0, 3.0], [3.0, 2.0, 1.0]],
        "diagonal_margins": [1.0, 1.0, 1.0],
        "corresponding_expert_removal_state_loss_degradation": [0.1, 0.1, 0.1],
        "all_conditions_present": True,
        "all_diagonal_best": True,
        "all_removals_degrade": True,
    }
    gradients = {
        "evidence_name": "expert_condition_gradient",
        "parameter_scope": "four_layer_shared_A_B",
        "independent_expert_parameter_updates_claimed": False,
        "gradient_norms": [0.1, 0.2, 0.3],
    }
    family = {
        "maximum_difference": 0.0,
        "expert_row_mask": False,
        "detection_adapter_sha256_before": "a",
        "detection_adapter_sha256_after": "a",
        "router_state_head_sha256_before": "b",
        "router_state_head_sha256_after": "b",
    }
    _write_json(root / "training_summary.json", summary)
    _write_json(
        root / "route_thresholds.json",
        {"growth": 1.0, "pressure": 2.0, "calibration": calibration},
    )
    _write_json(root / "routing_contract.json", contract)
    _write_json(
        root / "expert_codes.json",
        {
            "single_code": [1.0] * 16,
            "pairwise_inner_products": (codes @ codes.T).tolist(),
            "full_support": True,
            "codes_are_parameters": False,
        },
    )
    _write_json(root / "route_usage.json", usage)
    _write_json(root / "specialization.json", specialization)
    _write_json(root / "expert_condition_gradients.json", gradients)
    _write_json(root / "family_equivalence.json", family)
    _write_json(root / "structure_config.json", {})


def test_analysis_requires_every_gate_and_refuses_overwrite(tmp_path: Path) -> None:
    single = tmp_path / "single"
    routed = tmp_path / "routed"
    _analysis_run(single, "single")
    _analysis_run(routed, "routed")
    output = tmp_path / "comparison.json"
    result = analyze_physics_routed_experts(single, routed, output)
    assert result["overall_pass"] is True
    assert result["failed_gates"] == []
    with pytest.raises(RoutedExpertAnalysisError, match="拒绝覆盖"):
        analyze_physics_routed_experts(single, routed, output)

    usage_path = routed / "route_usage.json"
    usage = json.loads(usage_path.read_text(encoding="utf-8"))
    usage["physics_validation"]["rates"] = [0.0, 0.5, 0.5]
    _write_json(usage_path, usage)
    failed = analyze_physics_routed_experts(single, routed, tmp_path / "failed.json")
    assert failed["overall_pass"] is False
    assert "usage" in failed["failed_gates"]
