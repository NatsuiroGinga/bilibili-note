import pytest
import torch

from flow_probe.qwen_physics_gradient import GradientProbeError, select_last_token_hidden


def test_select_last_token_hidden_uses_each_sequence_attention_boundary() -> None:
    hidden_states = torch.arange(24, dtype=torch.float32).reshape(2, 4, 3)
    attention_mask = torch.tensor([[1, 1, 0, 0], [1, 1, 1, 1]])

    selected = select_last_token_hidden(hidden_states, attention_mask)

    assert torch.equal(selected[0], hidden_states[0, 1])
    assert torch.equal(selected[1], hidden_states[1, 3])


def test_select_last_token_hidden_rejects_empty_sequence() -> None:
    hidden_states = torch.zeros((1, 3, 2))
    attention_mask = torch.zeros((1, 3), dtype=torch.long)

    with pytest.raises(GradientProbeError, match="有效令牌"):
        select_last_token_hidden(hidden_states, attention_mask)
