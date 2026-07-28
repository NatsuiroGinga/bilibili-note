import pytest


def test_parse_label_prediction_accepts_only_strict_allowed_json() -> None:
    from flow_probe.generative_multiclass import parse_label_prediction

    allowed = ("benign", "ftp", "smb")

    valid = parse_label_prediction('{"label":"ftp"}', allowed)
    assert valid.label == "ftp"
    assert valid.is_valid is True
    assert valid.error is None

    invalid_texts = (
        '```json\n{"label":"ftp"}\n```',
        '{"label":"ftp","confidence":0.9}',
        '{"label":"unknown_attack"}',
        '{"label":1}',
        '["ftp"]',
    )
    for text in invalid_texts:
        parsed = parse_label_prediction(text, allowed)
        assert parsed.label is None
        assert parsed.is_valid is False
        assert parsed.error


def test_parse_label_prediction_rejects_invalid_label_space() -> None:
    from flow_probe.generative_multiclass import parse_label_prediction

    with pytest.raises(ValueError, match="候选标签"):
        parse_label_prediction('{"label":"ftp"}', ())
    with pytest.raises(ValueError, match="候选标签"):
        parse_label_prediction('{"label":"ftp"}', ("ftp", "ftp"))


def test_candidate_scores_are_length_normalized_and_numerically_stable() -> None:
    from flow_probe.generative_multiclass import (
        mean_candidate_log_probability,
        normalize_candidate_scores,
    )

    assert mean_candidate_log_probability((-2.0, -2.0)) == pytest.approx(-2.0)
    assert mean_candidate_log_probability((-2.0, -2.0, -2.0)) == pytest.approx(-2.0)
    probabilities = normalize_candidate_scores(((1000.0, 1000.0), (-1000.0, -1001.0)))
    assert probabilities[0] == pytest.approx((0.5, 0.5))
    assert sum(probabilities[1]) == pytest.approx(1.0)
    assert probabilities[1][0] > probabilities[1][1]

    with pytest.raises(ValueError, match="对数概率"):
        mean_candidate_log_probability(())
    with pytest.raises(ValueError, match="有限"):
        normalize_candidate_scores(((0.0, float("nan")),))


def test_unknown_threshold_uses_only_lower_quantile_and_strict_rejection() -> None:
    from flow_probe.generative_multiclass import (
        apply_unknown_rejection,
        calibrate_unknown_threshold,
    )

    confidences = tuple(index / 10 for index in range(1, 11))
    calibration = calibrate_unknown_threshold(confidences, max_rejection_rate=0.2)

    assert calibration.threshold == pytest.approx(0.2)
    assert calibration.validation_rejection_rate == pytest.approx(0.1)
    assert calibration.max_rejection_rate == pytest.approx(0.2)
    predictions = apply_unknown_rejection(
        ("ftp", "smb", "ssh"),
        (0.19, 0.2, 0.21),
        threshold=calibration.threshold,
    )
    assert predictions == ["unknown_attack", "smb", "ssh"]

    with pytest.raises(ValueError, match="拒识率"):
        calibrate_unknown_threshold(confidences, max_rejection_rate=1.0)
    with pytest.raises(ValueError, match="长度"):
        apply_unknown_rejection(("ftp",), (0.1, 0.2), threshold=0.2)


def test_open_set_metrics_count_invalid_generation_as_guaranteed_error() -> None:
    from flow_probe.generative_multiclass import compute_open_set_metrics

    metrics = compute_open_set_metrics(
        truth=("benign", "ftp", "smb", "unknown_attack", "benign"),
        predictions=("benign", "ftp", None, "unknown_attack", "unknown_attack"),
        known_labels=("benign", "ftp", "smb"),
        unknown_label="unknown_attack",
    )

    assert metrics["accuracy"] == pytest.approx(0.6)
    assert metrics["json_valid_rate"] == pytest.approx(0.8)
    assert metrics["invalid_output_count"] == 1
    assert metrics["benign_false_positive_rate"] == pytest.approx(0.5)
    assert metrics["unknown_recall"] == pytest.approx(1.0)
    assert metrics["known_rejection_rate"] == pytest.approx(0.25)
    assert metrics["per_class_recall"] == {
        "benign": 0.5,
        "ftp": 1.0,
        "smb": 0.0,
        "unknown_attack": 1.0,
    }
    assert metrics["label_order"] == ["benign", "ftp", "smb", "unknown_attack"]
    assert metrics["sample_count"] == 5


def test_closed_set_metrics_penalize_invalid_benign_as_false_positive() -> None:
    from flow_probe.generative_multiclass import compute_open_set_metrics

    metrics = compute_open_set_metrics(
        truth=("benign", "ftp"),
        predictions=(None, "ftp"),
        known_labels=("benign", "ftp"),
        unknown_label=None,
    )

    assert metrics["accuracy"] == pytest.approx(0.5)
    assert metrics["benign_false_positive_rate"] == pytest.approx(1.0)
    assert metrics["unknown_recall"] is None
    assert metrics["known_rejection_rate"] is None


def test_open_set_metrics_reject_unknown_truth_or_length_mismatch() -> None:
    from flow_probe.generative_multiclass import compute_open_set_metrics

    with pytest.raises(ValueError, match="真实标签"):
        compute_open_set_metrics(
            truth=("dos-udp",),
            predictions=("unknown_attack",),
            known_labels=("benign", "ftp"),
            unknown_label="unknown_attack",
        )
    with pytest.raises(ValueError, match="长度"):
        compute_open_set_metrics(
            truth=("benign",),
            predictions=("benign", "ftp"),
            known_labels=("benign", "ftp"),
            unknown_label=None,
        )
