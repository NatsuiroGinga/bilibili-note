import pytest

from flow_probe.efficiency import RunTimer
from flow_probe.evaluate import compute_detection_metrics


def test_metrics_count_invalid_output_as_wrong_prediction() -> None:
    metrics = compute_detection_metrics(
        labels=["benign", "benign", "malicious", "malicious"],
        predictions=["benign", "malicious", "malicious", None],
        valid_mask=[True, True, True, False],
    )

    assert metrics["macro_f1"] == pytest.approx(0.5)
    assert metrics["malicious_recall"] == pytest.approx(0.5)
    assert metrics["false_positive_rate"] == pytest.approx(0.5)
    assert metrics["json_valid_rate"] == pytest.approx(0.75)
    assert metrics["invalid_output_count"] == 1


def test_metrics_reject_length_mismatch() -> None:
    with pytest.raises(ValueError, match="长度"):
        compute_detection_metrics(
            labels=["benign"], predictions=["benign", "malicious"], valid_mask=[True]
        )


def test_run_timer_reports_wall_time_and_token_counts() -> None:
    with RunTimer(sample_count=2) as timer:
        timer.record_tokens(input_tokens=20, generated_tokens=4)

    summary = timer.summary()

    assert summary["sample_count"] == 2
    assert summary["input_tokens"] == 20
    assert summary["generated_tokens"] == 4
    assert summary["wall_seconds"] >= 0
    assert summary["samples_per_second"] > 0
