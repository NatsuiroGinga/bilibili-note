from types import SimpleNamespace

import pytest
import torch

from flow_probe.representation_coupling import (
    PhysicalRepresentationCoupling,
    RepresentationCouplingError,
    coupled_generation_forward,
    coupled_next_token_forward,
    perturbed_supervised_logit_delta,
    prompt_anchor_positions,
    supervised_prediction_mask,
)


class _FakeDecoder(torch.nn.Module):
    def __init__(self, vocab_size: int, hidden_size: int) -> None:
        super().__init__()
        self.embedding = torch.nn.Embedding(vocab_size, hidden_size)
        self.projection = torch.nn.Linear(hidden_size, hidden_size)

    def forward(self, input_ids, attention_mask, use_cache, return_dict):
        del attention_mask, use_cache, return_dict
        return SimpleNamespace(last_hidden_state=self.projection(self.embedding(input_ids)))


class _FakeCausalLM(torch.nn.Module):
    def __init__(self, vocab_size: int = 17, hidden_size: int = 8) -> None:
        super().__init__()
        self.model = _FakeDecoder(vocab_size, hidden_size)
        self.lm_head = torch.nn.Linear(hidden_size, vocab_size, bias=False)

    def get_output_embeddings(self):
        return self.lm_head


def _batch():
    return {
        "input_ids": torch.tensor([[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]]),
        "attention_mask": torch.ones((2, 5), dtype=torch.long),
        "labels": torch.tensor([[-100, -100, -100, 4, 5], [-100, -100, 4, 5, 6]]),
    }


def test_prompt_anchor_and_prediction_mask_respect_causal_boundary():
    labels = _batch()["labels"]

    assert prompt_anchor_positions(labels).tolist() == [2, 1]
    assert supervised_prediction_mask(labels).tolist() == [
        [False, False, True, True, False],
        [False, True, True, True, False],
    ]


def test_generation_loss_reaches_predicted_state_and_state_perturbs_logits():
    torch.manual_seed(3)
    model = _FakeCausalLM()
    state_head = torch.nn.Sequential(torch.nn.Linear(8, 5), torch.nn.Softplus())
    coupling = PhysicalRepresentationCoupling(8, variant="B0")

    output = coupled_generation_forward(model, state_head, coupling, _batch())
    state_gradient = torch.autograd.grad(output.loss, output.predicted_state, retain_graph=True)[0]

    assert torch.isfinite(state_gradient).all()
    assert torch.linalg.vector_norm(state_gradient).item() > 0
    assert perturbed_supervised_logit_delta(model, coupling, output, delta=0.5) > 0


def test_real_data_inference_contract_needs_no_queue_truth():
    torch.manual_seed(5)
    model = _FakeCausalLM()
    state_head = torch.nn.Sequential(torch.nn.Linear(8, 5), torch.nn.Softplus())
    coupling = PhysicalRepresentationCoupling(8, variant="B0")

    output = coupled_next_token_forward(
        model,
        state_head,
        coupling,
        input_ids=torch.tensor([[1, 2, 3], [4, 5, 0]]),
        attention_mask=torch.tensor([[1, 1, 1], [1, 1, 0]]),
    )

    assert output.logits.shape == (2, 17)
    assert output.predicted_state.shape == (2, 5)
    assert torch.all((output.reliability > 0) & (output.reliability < 1))


def test_b1_only_adds_stiefel_constraint_to_same_initial_projection():
    torch.manual_seed(11)
    b0 = PhysicalRepresentationCoupling(8, variant="B0")
    torch.manual_seed(11)
    b1 = PhysicalRepresentationCoupling(8, variant="B1")

    assert torch.equal(b0.physical_projection, b1.physical_projection)
    assert torch.allclose(b0.effective_projection(), b1.effective_projection(), atol=1e-6)
    with torch.no_grad():
        b0.physical_projection[:, 0].mul_(2.0)
        b1.physical_projection[:, 0].mul_(2.0)

    assert b0.orthogonality_error().item() > 1
    assert b1.orthogonality_error().item() < 1e-5


@pytest.mark.parametrize("variant", ["G4", "M2", "mHC"])
def test_unknown_or_out_of_scope_variants_are_rejected(variant):
    with pytest.raises(RepresentationCouplingError, match="未知物理表征耦合变体"):
        PhysicalRepresentationCoupling(8, variant=variant)
