from pathlib import Path

from flow_probe.swanlab_diagnostic import (
    build_artifact_manifest,
    diagnostic_series,
    log_diagnostic_series,
)


def test_diagnostic_series_uses_multiple_explicit_steps_and_shallow_keys() -> None:
    series = diagnostic_series()

    assert [step for step, _ in series] == [0, 1, 2]
    assert all(set(metrics) == {"diagnostic/loss", "diagnostic/accuracy"} for _, metrics in series)
    assert [metrics["diagnostic/loss"] for _, metrics in series] == [1.0, 0.5, 0.25]


def test_artifact_manifest_records_all_run_data_locations() -> None:
    manifest = build_artifact_manifest(
        sdk_version="0.9.0",
        run_id="abc123",
        run_url="https://swanlab.cn/@user/project/runs/abc123/chart",
        log_dir=Path("runs/diagnostic/swanlog"),
        console_log=Path("runs/diagnostic/console.log"),
        output_dir=Path("runs/diagnostic"),
    )

    assert manifest["tracking_mode"] == "online"
    assert manifest["run_id"] == "abc123"
    assert manifest["run_url"].endswith("/abc123/chart")
    assert manifest["data_files"] == {
        "console_log": "runs/diagnostic/console.log",
        "output_dir": "runs/diagnostic",
        "swanlab_log_dir": "runs/diagnostic/swanlog",
    }


def test_log_diagnostic_series_uses_only_supported_log_arguments() -> None:
    calls = []

    def record(data, *, step):
        calls.append((data, step))

    log_diagnostic_series(record, nested_keys=False)

    assert [step for _, step in calls] == [0, 1, 2]
    assert calls[0][0] == {"loss": 1.0, "accuracy": 0.5}
