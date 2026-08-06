from __future__ import annotations

import pytest

from flow_probe.r2_final_qwen_probe import (
    CANDIDATE_DETECTION_ROWS,
    CANDIDATE_PHYSICS_ROWS,
    OFFICIAL_MODEL_ID,
    QwenR2ProbeError,
    bounded_fusion_strength,
    validate_candidate_role_counts,
    validate_model_contract,
)


def test_qwen_candidate_contract_separates_detection_and_physics_roles() -> None:
    receipt = validate_candidate_role_counts(
        detection_rows=CANDIDATE_DETECTION_ROWS,
        physics_rows=CANDIDATE_PHYSICS_ROWS,
        total_rows=10_000,
    )

    assert receipt == {
        "detection_supervision_rows": 7_579,
        "physics_auxiliary_rows": 2_421,
        "total_rows": 10_000,
        "ns3_detection_label_training": False,
    }

    with pytest.raises(QwenR2ProbeError, match="检测监督与物理辅助"):
        validate_candidate_role_counts(
            detection_rows=7_580,
            physics_rows=2_420,
            total_rows=10_000,
        )


def test_qwen_model_contract_rejects_nonofficial_identity_and_quic_weight() -> None:
    validate_model_contract(
        identifier=OFFICIAL_MODEL_ID,
        source="/root/autodl-tmp/thesis/models/Qwen3-0.6B",
        quic_expert_ready=False,
        quic_training_weight=0.0,
    )

    with pytest.raises(QwenR2ProbeError, match="官方后训练版"):
        validate_model_contract(
            identifier="Qwen/Qwen3-1.7B",
            source="/root/autodl-tmp/thesis/models/Qwen3-1.7B",
            quic_expert_ready=False,
            quic_training_weight=0.0,
        )

    with pytest.raises(QwenR2ProbeError, match="QUIC"):
        validate_model_contract(
            identifier=OFFICIAL_MODEL_ID,
            source="/root/autodl-tmp/thesis/models/Qwen3-0.6B",
            quic_expert_ready=False,
            quic_training_weight=0.01,
        )


@pytest.mark.parametrize(
    ("logit", "expected_sign"),
    [(-100.0, -1), (0.0, 0), (100.0, 1)],
)
def test_bounded_fusion_strength_never_exceeds_limit(
    logit: float,
    expected_sign: int,
) -> None:
    value = bounded_fusion_strength(logit, limit=0.1)

    assert -0.1 <= value <= 0.1
    assert (value > 0) - (value < 0) == expected_sign
