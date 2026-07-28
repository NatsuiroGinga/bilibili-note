from flow_probe.swanlab_artifact_smoke import build_metric_series


def test_tracking_smoke_uses_visible_grouped_metrics() -> None:
    series = build_metric_series()

    assert [step for step, _ in series] == [0, 1, 2]
    assert [metrics["diagnostic/loss"] for _, metrics in series] == [1.0, 0.5, 0.25]
    assert [metrics["diagnostic/accuracy"] for _, metrics in series] == [0.5, 0.75, 1.0]
