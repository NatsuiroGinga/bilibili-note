"""验证标准 SwanLab 跟踪层与本地制品归档的最小在线运行。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    swanlab_run,
)


def build_metric_series() -> list[tuple[int, dict[str, float]]]:
    """返回可在网页中直接确认的三步确定性指标。"""
    return [
        (0, {"diagnostic/loss": 1.0, "diagnostic/accuracy": 0.5}),
        (1, {"diagnostic/loss": 0.5, "diagnostic/accuracy": 0.75}),
        (2, {"diagnostic/loss": 0.25, "diagnostic/accuracy": 1.0}),
    ]


def run_smoke(output_dir: Path, run_name: str) -> dict[str, object]:
    """执行最小在线运行并返回标准制品清单。"""
    output_dir = Path(output_dir)
    metrics_path = output_dir / "swanlab_metrics.json"
    result_path = output_dir / "diagnostic_result.json"
    manifest_path = output_dir / "artifact_manifest.json"
    series = build_metric_series()
    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "标准 SwanLab 跟踪层与制品归档在线冒烟验证",
            "mode": "online",
            "tags": ["llm-probe", "swanlab-diagnostic", "artifact-smoke"],
        }
    )
    data_files = {
        "diagnostic_result": result_path,
        "swanlab_metrics": metrics_path,
    }
    tracking_config = {
        "purpose": "tracking_artifact_smoke",
        "expected_steps": len(series),
    }

    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings,
            phase="diagnostic",
            config=tracking_config,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        for step, metrics in series:
            swanlab.log(metrics, step=step)
        metrics_path.write_text(
            json.dumps(
                [{"step": step, "metrics": metrics} for step, metrics in series],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        result_path.write_text(
            json.dumps(
                {"status": "finished", "logged_steps": len(series)},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with capture_console_log(output_dir / "console.log"):
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SwanLab 标准跟踪层在线冒烟验证")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_smoke(args.output_dir, args.run_name)
