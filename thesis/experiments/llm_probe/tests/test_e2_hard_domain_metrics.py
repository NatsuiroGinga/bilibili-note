"""E2 困难域统一指标的最小合同测试。"""

from __future__ import annotations

import pytest


def _metrics_api():
    try:
        from flow_probe.e2_hard_domain_metrics import compute_e2_metrics
    except ModuleNotFoundError:
        pytest.fail("缺少 E2 困难域指标模块")
    return compute_e2_metrics


def test_metrics_report_capture_group_equal_weight_and_worst_group() -> None:
    compute_e2_metrics = _metrics_api()

    metrics = compute_e2_metrics(
        labels=[0, 1, 0, 1],
        malicious_probabilities=[0.1, 0.9, 0.9, 0.1],
        capture_groups=["capture-a", "capture-a", "capture-c", "capture-c"],
    )

    assert metrics["macro_f1"] == pytest.approx(0.5)
    assert metrics["capture_group_equal_weighted_macro_f1"] == pytest.approx(0.5)
    assert metrics["worst_capture_group_macro_f1"] == pytest.approx(0.0)
    assert metrics["capture_group_metrics"]["capture-a"]["macro_f1"] == pytest.approx(1.0)
    assert metrics["capture_group_metrics"]["capture-c"]["macro_f1"] == pytest.approx(0.0)
    assert metrics["capture_group_metrics"]["capture-a"]["sample_count"] == 2
    assert metrics["pr_auc"] == pytest.approx(0.5)
    assert metrics["mcc"] == pytest.approx(0.0)
    assert metrics["negative_log_likelihood"] > 0.0
    assert metrics["tpr_at_1pct_fpr"] == pytest.approx(0.0)


def test_pr_auc_is_invariant_to_reordering_tied_scores() -> None:
    compute_e2_metrics = _metrics_api()
    original = compute_e2_metrics(
        labels=[0, 1, 0, 1],
        malicious_probabilities=[0.1, 0.9, 0.9, 0.1],
        capture_groups=["capture-a"] * 4,
    )
    reordered = compute_e2_metrics(
        labels=[0, 0, 1, 1],
        malicious_probabilities=[0.1, 0.9, 0.9, 0.1],
        capture_groups=["capture-a"] * 4,
    )

    assert original["pr_auc"] == pytest.approx(0.5)
    assert reordered["pr_auc"] == pytest.approx(original["pr_auc"])
