from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from flow_probe import r2_final_distilbert_probe as probe


class CheckpointBindingReached(Exception):
    pass


def test_physics_system_resolves_imported_checkpoint_binding_before_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fit_config = object()
    config = SimpleNamespace(
        physics=SimpleNamespace(
            checkpoint=SimpleNamespace(ready=True),
            fit_config=object(),
        ),
        project_root=Path("."),
    )

    monkeypatch.setattr(
        probe,
        "_verify_artifact",
        lambda *args, **kwargs: (Path("fit-config.yaml"), b"{}"),
    )
    monkeypatch.setattr(
        probe,
        "load_physics_fit_config",
        lambda *args, **kwargs: fit_config,
    )

    def stop_after_binding(value: object) -> object:
        assert value is fit_config
        raise CheckpointBindingReached

    monkeypatch.setattr(probe, "checkpoint_binding", stop_after_binding)

    with pytest.raises(CheckpointBindingReached):
        probe._physics_system(config, object())


def test_udp_only_allows_paired_zero_state_degeneracy_outside_g3_metric() -> None:
    truth = np.asarray(
        [
            [[1.0, 2.0, 3.0, 4.0, 0.0, 0.0], [2.0, 4.0, 6.0, 8.0, 0.0, 0.0]],
            [[3.0, 6.0, 9.0, 12.0, 0.0, 0.0], [4.0, 8.0, 12.0, 16.0, 0.0, 0.0]],
        ]
    )
    split = SimpleNamespace(
        truths={probe.EXPERT_UDP: truth},
        truth_masks={probe.EXPERT_UDP: np.ones_like(truth, dtype=bool)},
        valid_mask=np.ones(truth.shape[:2], dtype=bool),
    )

    normalization = probe._training_state_normalization(split, probe.EXPERT_UDP)

    assert normalization["scale"] == pytest.approx(
        [np.sqrt(1.25), np.sqrt(5.0), np.sqrt(11.25), np.sqrt(20.0), 1.0, 1.0]
    )
    assert normalization["raw_scale"] == pytest.approx(
        [np.sqrt(1.25), np.sqrt(5.0), np.sqrt(11.25), np.sqrt(20.0), 0.0, 0.0]
    )
    assert normalization["metric_state_mask"] == [True, True, True, True, False, False]
    assert normalization["degenerate_state_indices"] == [4, 5]

    prediction = truth + np.asarray([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    statistics = probe._masked_state_statistics(
        prediction,
        truth,
        np.ones_like(truth, dtype=bool),
        normalization,
    )
    aggregate = probe._combine_equal_component_metric(
        (statistics,), "metric_mse_by_state"
    )

    assert statistics["mse_by_state"] == pytest.approx([0.8, 0.8, 0.8, 0.8, 25.0, 36.0])
    assert statistics["metric_mse_by_state"] == pytest.approx([0.8, 0.8, 0.8, 0.8])
    assert statistics["degenerate_raw_mse_by_state"] == pytest.approx([25.0, 36.0])
    assert aggregate == {"numerator": pytest.approx(3.2), "denominator": 4, "value": pytest.approx(0.8)}

    invalid_truth = truth.copy()
    invalid_truth[..., 3] = 7.0
    invalid_split = SimpleNamespace(
        truths={probe.EXPERT_UDP: invalid_truth},
        truth_masks={probe.EXPERT_UDP: np.ones_like(invalid_truth, dtype=bool)},
        valid_mask=np.ones(invalid_truth.shape[:2], dtype=bool),
    )
    with pytest.raises(probe.R2FinalProbeError, match="零方差或非有限"):
        probe._training_state_normalization(invalid_split, probe.EXPERT_UDP)


def test_cluster_state_statistics_exclude_only_locally_unobserved_metric_dimensions() -> None:
    truth = np.asarray([[[1.0, 10.0, 100.0], [2.0, 20.0, 200.0]]])
    normalization = {
        "mean": [0.0, 0.0, 0.0],
        "scale": [1.0, 2.0, 4.0],
        "raw_scale": [1.0, 2.0, 4.0],
        "metric_state_mask": [True, True, True],
        "degenerate_state_indices": [],
    }
    first_mask = np.asarray([[[True, True, False], [True, True, False]]])
    first = probe._masked_state_statistics(
        truth + np.asarray([1.0, 2.0, 40.0]),
        truth,
        first_mask,
        normalization,
    )

    assert first["mask_count_by_state"] == [2, 2, 0]
    assert first["cluster_metric_state_mask"] == [True, True, False]
    assert first["missing_metric_state_indices"] == [2]
    assert first["metric_squared_error_sum_by_state"] == pytest.approx([2.0, 2.0, 0.0])
    assert first["metric_observed_count_by_state"] == [2, 2, 0]
    assert first["metric_mse_by_state"] == pytest.approx([1.0, 1.0])
    assert first["equal_state_mse_denominator"] == 2

    with pytest.raises(probe.R2FinalProbeError, match="分协议汇总存在无有效观测"):
        probe._pooled_protocol_metric(
            (first,),
            (("metric_squared_error_sum_by_state", "metric_observed_count_by_state"),),
        )

    second_mask = np.asarray([[[False, False, True], [False, False, True]]])
    second = probe._masked_state_statistics(
        truth + np.asarray([1.0, 2.0, 4.0]),
        truth,
        second_mask,
        normalization,
    )
    pooled = probe._pooled_protocol_metric(
        (first, second),
        (("metric_squared_error_sum_by_state", "metric_observed_count_by_state"),),
    )

    assert pooled == {
        "numerator": pytest.approx(3.0),
        "denominator": 3,
        "value": pytest.approx(1.0),
    }
