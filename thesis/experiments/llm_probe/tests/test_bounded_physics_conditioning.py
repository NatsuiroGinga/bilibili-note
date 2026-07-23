from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import pytest
import torch

from flow_probe.bounded_physics_conditioning import (
    PhysicsConditionedGeneration,
    PhysicsConditionedRuntime,
)


@dataclass
class _FakeOutput:
    loss: torch.Tensor | None
    logits: torch.Tensor
    hidden_states: torch.Tensor


class _FakeStateHead(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(2048, 5)
        self.activation = torch.nn.Softplus()
        self.call_count = 0
        self.return_nonfinite = False

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        self.call_count += 1
        if self.return_nonfinite:
            return torch.full(
                (hidden.shape[0], 5),
                float("inf"),
                device=hidden.device,
                dtype=hidden.dtype,
            )
        return self.activation(self.linear(hidden.to(dtype=self.linear.weight.dtype)))


class _FakeDecoderLayer(torch.nn.Module):
    def __init__(self, layer_index: int) -> None:
        super().__init__()
        self.bias = torch.nn.Parameter(torch.tensor((layer_index + 1) / 1000.0))
        self.raise_error = False
        self.forward_calls = 0

    def forward(
        self,
        hidden_states: torch.Tensor,
        **_kwargs: Any,
    ) -> tuple[torch.Tensor]:
        self.forward_calls += 1
        if self.raise_error:
            raise RuntimeError("伪层故障")
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
        self.forward_lengths: list[int] = []
        self.before_forward: Any = None
        self.skip_source = False

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
        **kwargs: Any,
    ) -> _FakeOutput:
        self.forward_lengths.append(input_ids.shape[1])
        if self.before_forward is not None:
            callback = self.before_forward
            self.before_forward = None
            callback()

        hidden = self.embedding(input_ids)
        for index, layer in enumerate(self.model.layers):
            if self.skip_source and index == 13:
                continue
            if index % 2:
                layer_output = layer(
                    hidden_states=hidden,
                    attention_mask=attention_mask,
                    **kwargs,
                )
            else:
                layer_output = layer(hidden, attention_mask=attention_mask, **kwargs)
            hidden = layer_output[0]
        loss = hidden.float().square().mean() if labels is not None else None
        return _FakeOutput(loss=loss, logits=hidden, hidden_states=hidden)

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        max_new_tokens: int = 3,
        num_beams: int = 1,
        **kwargs: Any,
    ) -> torch.Tensor:
        if num_beams != 1:
            raise RuntimeError("伪模型不支持多束")
        sequences = input_ids
        running_mask = attention_mask
        for step in range(max_new_tokens):
            model_input = sequences if step == 0 else sequences[:, -1:]
            output = self.forward(
                input_ids=model_input,
                attention_mask=running_mask,
                use_cache=True,
                **kwargs,
            )
            next_token = output.logits[:, -1, 0].abs().to(dtype=torch.long).remainder(64)
            sequences = torch.cat((sequences, next_token.unsqueeze(1)), dim=1)
            running_mask = torch.cat(
                (
                    running_mask,
                    torch.ones(
                        (running_mask.shape[0], 1),
                        dtype=running_mask.dtype,
                        device=running_mask.device,
                    ),
                ),
                dim=1,
            )
        return sequences


class _FakePeftBase(torch.nn.Module):
    def __init__(self, model: _FakeQwen) -> None:
        super().__init__()
        self.model = model


class _FakePeftModel(torch.nn.Module):
    def __init__(self, model: _FakeQwen) -> None:
        super().__init__()
        self.config = model.config
        self.base_model = _FakePeftBase(model)

    def forward(self, *args: Any, **kwargs: Any) -> _FakeOutput:
        return self.base_model.model(*args, **kwargs)

    def generate(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        return self.base_model.model.generate(*args, **kwargs)


def _make_runtime(*, peft: bool = False) -> tuple[PhysicsConditionedRuntime, _FakeQwen]:
    model = _FakeQwen()
    runtime_model: torch.nn.Module = _FakePeftModel(model) if peft else model
    runtime = PhysicsConditionedRuntime(runtime_model, _FakeStateHead())
    return runtime, model


def _candidate_batch() -> tuple[torch.Tensor, torch.Tensor]:
    input_ids = torch.tensor(
        (
            (1, 2, 3, 4, 5),
            (1, 2, 3, 11, 12),
        ),
        dtype=torch.long,
    )
    return input_ids, torch.ones_like(input_ids)


def _has_nonzero_gradient(parameters: list[torch.nn.Parameter]) -> bool:
    return any(
        parameter.grad is not None and bool((parameter.grad != 0).any().item())
        for parameter in parameters
    )


@pytest.mark.parametrize("peft", [False, True])
def test_runtime_only_registers_structure_and_resolves_supported_paths(peft: bool) -> None:
    torch.manual_seed(1)
    runtime, _model = _make_runtime(peft=peft)
    try:
        state_names = tuple(runtime.state_dict())
        assert state_names
        assert all(
            name.startswith(("state_head.", "condition_encoder.", "injectors."))
            for name in state_names
        )
        assert not any("model.layers" in name for name in state_names)
        assert runtime.unexpected_base_parameter_names() == ()
        assert runtime.structure_parameter_names() == tuple(
            name for name, _ in runtime.named_parameters()
        )
        assert runtime.structure_parameter_count() == sum(
            parameter.numel() for parameter in runtime.parameters()
        )

        input_ids, attention_mask = _candidate_batch()
        output = runtime(
            input_ids,
            attention_mask,
            completion_start=3,
        )
        assert output.diagnostics.source_hook_count == 1
        assert output.diagnostics.target_hook_counts == (1, 1, 1, 1)
    finally:
        runtime.close()


def test_zero_gate_bypass_and_bounded_nonzero_injection() -> None:
    torch.manual_seed(2)
    runtime, model = _make_runtime()
    input_ids, attention_mask = _candidate_batch()
    try:
        direct = model(input_ids=input_ids, attention_mask=attention_mask)
        bypass = runtime(input_ids, attention_mask, bypass=True)
        assert torch.equal(bypass.logits, direct.logits)
        zero_gate = runtime(
            input_ids,
            attention_mask,
            completion_start=3,
        )
        assert torch.equal(zero_gate.logits, bypass.logits)
        assert zero_gate["logits"] is zero_gate.logits
        assert zero_gate.hidden_states is zero_gate.model_output.hidden_states
        assert zero_gate.predicted_state is not None
        assert zero_gate.condition_tokens is not None
        assert zero_gate.condition_tokens.shape == (2, 9, 256)

        with torch.no_grad():
            for injector in runtime.injectors:
                injector.alpha.fill_(0.75)
        conditioned = runtime(
            input_ids,
            attention_mask,
            completion_start=3,
        )
        assert not torch.equal(conditioned.logits, bypass.logits)
        assert 0.0 < conditioned.diagnostics.max_residual_ratio <= 0.1
        assert conditioned.diagnostics.source_hook_count == 1
        assert conditioned.diagnostics.target_hook_counts == (1, 1, 1, 1)
    finally:
        runtime.close()


def test_first_step_gradients_only_reach_gates_then_open_structure_path() -> None:
    torch.manual_seed(3)
    runtime, _model = _make_runtime()
    input_ids, attention_mask = _candidate_batch()
    labels = torch.tensor(
        (
            (-100, -100, -100, 4, 5),
            (-100, -100, -100, 11, 12),
        )
    )
    gate_parameters = [injector.alpha for injector in runtime.injectors]
    injector_parameters = [
        parameter
        for name, parameter in runtime.injectors.named_parameters()
        if not name.endswith("alpha")
    ]
    try:
        first = runtime(input_ids, attention_mask, labels=labels)
        assert first.loss is not None
        first.loss.backward()
        assert all(
            parameter.grad is not None and bool((parameter.grad != 0).any().item())
            for parameter in gate_parameters
        )
        assert not _has_nonzero_gradient(list(runtime.state_head.parameters()))
        assert not _has_nonzero_gradient(list(runtime.condition_encoder.parameters()))
        assert not _has_nonzero_gradient(injector_parameters)

        with torch.no_grad():
            for parameter in gate_parameters:
                assert parameter.grad is not None
                parameter.add_(-0.1 * parameter.grad.sign())
        runtime.zero_grad(set_to_none=True)

        second = runtime(input_ids, attention_mask, labels=labels)
        assert second.loss is not None
        second.loss.backward()
        assert _has_nonzero_gradient(list(runtime.state_head.parameters()))
        assert _has_nonzero_gradient(list(runtime.condition_encoder.parameters()))
        assert _has_nonzero_gradient(injector_parameters)
    finally:
        runtime.close()


def test_training_and_candidate_masks_preserve_prompt_anchor() -> None:
    torch.manual_seed(4)
    runtime, _model = _make_runtime()
    input_ids = torch.tensor(((1, 2, 3, 4, 5, 6), (1, 2, 3, 9, 10, 11)))
    attention_mask = torch.ones_like(input_ids)
    labels = torch.tensor(
        (
            (-100, -100, -100, 4, 5, -100),
            (-100, -100, -100, 9, 10, -100),
        )
    )
    try:
        with torch.no_grad():
            for injector in runtime.injectors:
                injector.alpha.fill_(0.6)

        baseline = runtime(input_ids, attention_mask, bypass=True).hidden_states
        training = runtime(input_ids, attention_mask, labels=labels)
        training_changed = (training.hidden_states - baseline).abs().amax(dim=-1) > 0
        expected_training = torch.tensor(((False, False, True, True, False, False),) * 2)
        assert torch.equal(training_changed, expected_training)

        candidate = runtime(
            input_ids,
            attention_mask,
            completion_start=torch.tensor((3, 3)),
        )
        candidate_changed = (candidate.hidden_states - baseline).abs().amax(dim=-1) > 0
        expected_candidate = torch.tensor(((False, False, True, True, True, False),) * 2)
        assert torch.equal(candidate_changed, expected_candidate)
        assert candidate.predicted_state is not None
        assert torch.equal(candidate.predicted_state[0], candidate.predicted_state[1])
    finally:
        runtime.close()


def test_generate_prefills_once_then_reuses_cached_condition() -> None:
    torch.manual_seed(5)
    runtime, model = _make_runtime()
    input_ids, attention_mask = _candidate_batch()
    state_head = runtime.state_head
    assert isinstance(state_head, _FakeStateHead)
    try:
        result = runtime.generate(
            input_ids,
            attention_mask,
            max_new_tokens=3,
        )
        assert isinstance(result, PhysicsConditionedGeneration)
        assert isinstance(result.model_output, torch.Tensor)
        assert result.model_output.shape == (2, 8)
        assert model.forward_lengths == [5, 1, 1]
        assert state_head.call_count == 1
        assert result.diagnostics.source_hook_count == 3
        assert result.diagnostics.target_hook_counts == (3, 3, 3, 3)
        assert result.diagnostics.prefill_count == 1
        assert result.diagnostics.cached_decode_count == 2
    finally:
        runtime.close()


def test_invalid_calls_fail_and_sessions_are_cleaned() -> None:
    torch.manual_seed(6)
    runtime, model = _make_runtime()
    input_ids, attention_mask = _candidate_batch()
    state_head = runtime.state_head
    assert isinstance(state_head, _FakeStateHead)
    try:
        with pytest.raises(ValueError, match="labels 或 completion_start"):
            runtime(input_ids, attention_mask)
        with pytest.raises(ValueError, match="num_beams=1"):
            runtime.generate(input_ids, attention_mask, num_beams=2)

        model.before_forward = lambda: runtime(
            input_ids,
            attention_mask,
            completion_start=3,
        )
        with pytest.raises(RuntimeError, match="嵌套或并发"):
            runtime(input_ids, attention_mask, completion_start=3)

        model.skip_source = True
        with pytest.raises(RuntimeError, match="早于第 13 层"):
            runtime(input_ids, attention_mask, completion_start=3)
        model.skip_source = False

        state_head.return_nonfinite = True
        with pytest.raises(ValueError, match="有限数值"):
            runtime(input_ids, attention_mask, completion_start=3)
        state_head.return_nonfinite = False

        model.model.layers[20].raise_error = True
        with pytest.raises(RuntimeError, match="伪层故障"):
            runtime(input_ids, attention_mask, completion_start=3)
        model.model.layers[20].raise_error = False

        recovered = runtime(input_ids, attention_mask, completion_start=3)
        assert recovered.diagnostics.target_hook_counts == (1, 1, 1, 1)
    finally:
        runtime.close()

    with pytest.raises(RuntimeError, match="已关闭"):
        runtime(input_ids, attention_mask, completion_start=3)
    with pytest.raises(RuntimeError, match="已关闭"):
        runtime.generate(input_ids, attention_mask)
    direct = model(input_ids=input_ids, attention_mask=attention_mask)
    assert direct.logits.shape == (2, 5, 2048)


def test_structure_state_round_trip_and_strict_validation() -> None:
    torch.manual_seed(7)
    runtime_one, model_one = _make_runtime()
    runtime_two, model_two = _make_runtime()
    model_two.load_state_dict(model_one.state_dict())
    input_ids, attention_mask = _candidate_batch()
    try:
        with torch.no_grad():
            for index, injector in enumerate(runtime_one.injectors):
                injector.alpha.fill_(0.2 + index / 10.0)
        state = runtime_one.structure_state_dict()
        runtime_two.load_structure_state_dict(state)

        output_one = runtime_one(input_ids, attention_mask, completion_start=3)
        output_two = runtime_two(input_ids, attention_mask, completion_start=3)
        assert torch.equal(output_one.logits, output_two.logits)
        assert output_one.diagnostics == output_two.diagnostics

        missing = dict(state)
        missing.pop(next(iter(missing)))
        with pytest.raises(ValueError, match="缺失"):
            runtime_two.load_structure_state_dict(missing)

        extra = dict(state)
        extra["model.unexpected"] = torch.zeros(())
        with pytest.raises(ValueError, match="多余"):
            runtime_two.load_structure_state_dict(extra)

        malformed = dict(state)
        malformed["injectors.0.alpha"] = torch.zeros(1)
        with pytest.raises(ValueError, match="形状不匹配"):
            runtime_two.load_structure_state_dict(malformed)

        nonfinite = dict(state)
        nonfinite["injectors.0.alpha"] = torch.tensor(float("nan"))
        with pytest.raises(ValueError, match="有限值"):
            runtime_two.load_structure_state_dict(nonfinite)
    finally:
        runtime_one.close()
        runtime_two.close()
