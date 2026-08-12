"""E2 困难域共同预算强基线的最小合同测试。"""

from __future__ import annotations

from dataclasses import replace

import pytest

from flow_probe.e2_hard_domain_data import E2Panel, E2Sample


def _sample(
    sample_id: str,
    *,
    profile: str,
    split_id: str,
    capture_id: str,
    label: int,
    offset: float,
    stable_order: int,
) -> E2Sample:
    return E2Sample(
        sample_id=sample_id,
        capture_id=capture_id,
        profile=profile,
        split_id=split_id,
        label=label,
        features=tuple(offset + index for index in range(7)),
        stable_order=stable_order,
    )


def _panel() -> E2Panel:
    return E2Panel(
        panel="abd_to_c",
        train=(
            _sample(
                "train-a-0",
                profile="A",
                split_id="train",
                capture_id="capture-a",
                label=0,
                offset=0.0,
                stable_order=0,
            ),
            _sample(
                "train-a-1",
                profile="A",
                split_id="train",
                capture_id="capture-a",
                label=1,
                offset=4.0,
                stable_order=1,
            ),
            _sample(
                "train-b-0",
                profile="B",
                split_id="train",
                capture_id="capture-b",
                label=0,
                offset=0.5,
                stable_order=2,
            ),
            _sample(
                "train-d-1",
                profile="D",
                split_id="train",
                capture_id="capture-d",
                label=1,
                offset=4.5,
                stable_order=3,
            ),
        ),
        calibration=(
            _sample(
                "cal-a-0",
                profile="A",
                split_id="calibration",
                capture_id="capture-a",
                label=0,
                offset=1.0,
                stable_order=4,
            ),
            _sample(
                "cal-b-1",
                profile="B",
                split_id="calibration",
                capture_id="capture-b",
                label=1,
                offset=3.5,
                stable_order=5,
            ),
        ),
        target=(
            _sample(
                "target-c-0",
                profile="C",
                split_id="validation",
                capture_id="capture-c1",
                label=0,
                offset=1.5,
                stable_order=6,
            ),
            _sample(
                "target-c-1",
                profile="C",
                split_id="validation",
                capture_id="capture-c2",
                label=1,
                offset=3.0,
                stable_order=7,
            ),
        ),
    )


def test_logreg_and_groupdro_share_prediction_contract_and_only_fit_source() -> None:
    from flow_probe.e2_hard_domain_baselines import E2BaselineBudget, run_e2_baseline_suite

    panel = _panel()
    result = run_e2_baseline_suite(
        panel,
        models=("logreg", "groupdro"),
        budget=E2BaselineBudget(max_iterations=5, threshold_source="fixed"),
    )

    assert tuple(result.results) == ("logreg", "groupdro")
    for model, model_result in result.results.items():
        assert model_result.source_only_fit is True
        assert model_result.threshold == pytest.approx(0.5)
        assert [row.sample_id for row in model_result.predictions] == [
            "target-c-0",
            "target-c-1",
        ]
        assert {row.profile for row in model_result.predictions} == {"C"}
        assert {row.model for row in model_result.predictions} == {model}
        assert "capture_group_equal_weighted_macro_f1" in model_result.metrics


class _FixedPredictor:
    def predict_malicious_probabilities(self, texts: list[str]) -> list[float]:
        return [0.2 if "duration=1" in text else 0.8 for text in texts]


class _RecordingDistilBertAdapter:
    def __init__(self) -> None:
        self.train_ids: list[str] = []
        self.calibration_ids: list[str] = []

    def fit_source_only(self, *, train, calibration, budget):
        del budget
        self.train_ids = [sample.sample_id for sample in train]
        self.calibration_ids = [sample.sample_id for sample in calibration]
        assert all("profile=" not in sample.text for sample in (*train, *calibration))
        return _FixedPredictor()


def test_distilbert_requires_explicit_adapter_and_adapter_fit_never_receives_target() -> None:
    from flow_probe.e2_hard_domain_baselines import (
        DistilBertAdapterRequiredError,
        E2BaselineBudget,
        run_e2_baseline_suite,
    )

    panel = _panel()
    with pytest.raises(DistilBertAdapterRequiredError, match="适配器"):
        run_e2_baseline_suite(panel, models=("distilbert",))

    adapter = _RecordingDistilBertAdapter()
    result = run_e2_baseline_suite(
        panel,
        models=("distilbert",),
        budget=E2BaselineBudget(max_iterations=1, threshold_source="fixed"),
        distilbert_adapter=adapter,
    )

    assert adapter.train_ids == [sample.sample_id for sample in panel.train]
    assert adapter.calibration_ids == [sample.sample_id for sample in panel.calibration]
    assert set(adapter.train_ids + adapter.calibration_ids).isdisjoint(
        sample.sample_id for sample in panel.target
    )
    assert len(result.results["distilbert"].predictions) == len(panel.target)


def test_shared_b0_distilbert_predictor_preserves_order_across_batches(monkeypatch) -> None:
    from flow_probe.e2_hard_domain_baselines import SharedB0DistilBertPredictor
    from flow_probe import shared_b0_distilbert_baseline

    calls: list[list[str]] = []

    def fake_forward_probability_batch(*, texts, **kwargs):
        del kwargs
        calls.append(list(texts))
        return tuple(float(text.rsplit("-", 1)[1]) / 10.0 for text in texts)

    monkeypatch.setattr(
        shared_b0_distilbert_baseline,
        "forward_probability_batch",
        fake_forward_probability_batch,
    )
    predictor = SharedB0DistilBertPredictor(
        model=object(),
        tokenizer=object(),
        torch_module=object(),
        device="cpu",
        max_length=128,
        batch_size=2,
    )

    probabilities = predictor.predict_malicious_probabilities(
        ["sample-1", "sample-2", "sample-3", "sample-4", "sample-5"]
    )

    assert calls == [["sample-1", "sample-2"], ["sample-3", "sample-4"], ["sample-5"]]
    assert probabilities == pytest.approx((0.1, 0.2, 0.3, 0.4, 0.5))


def test_e2_distilbert_settings_reject_non_frozen_model_and_invalid_precision() -> None:
    from flow_probe.e2_distilbert import (
        E2DistilBertTrainingError,
        E2DistilBertTrainingSettings,
    )

    with pytest.raises(E2DistilBertTrainingError, match="必须固定"):
        E2DistilBertTrainingSettings(model_identifier="other-model").validate()
    with pytest.raises(E2DistilBertTrainingError, match="精度只允许"):
        E2DistilBertTrainingSettings(
            expected_model_binding_sha256="a" * 64,
            precision="int8",
        ).validate()


def test_e1_reuse_requires_exact_model_input_and_budget_binding() -> None:
    from flow_probe.e2_hard_domain_baselines import (
        E2BaselineBudget,
        E2HardDomainBaselineError,
        build_input_binding,
        validate_e1_reuse_receipt,
    )

    budget = E2BaselineBudget()
    binding = build_input_binding(_panel())
    receipt = {"model": "hgb", "input_binding": binding, "budget": budget.__dict__}
    validate_e1_reuse_receipt(
        receipt,
        expected_model="hgb",
        expected_input_binding=binding,
        expected_budget=budget,
    )

    changed = replace(budget, seed=43)
    with pytest.raises(E2HardDomainBaselineError, match="必须重跑"):
        validate_e1_reuse_receipt(
            receipt,
            expected_model="hgb",
            expected_input_binding=binding,
            expected_budget=changed,
        )
