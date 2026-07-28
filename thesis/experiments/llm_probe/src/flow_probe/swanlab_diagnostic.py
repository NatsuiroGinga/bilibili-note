"""生成可审计的 SwanLab 在线图表最小诊断运行。"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path


def diagnostic_series(prefix: str | None = "diagnostic") -> list[tuple[int, dict[str, float]]]:
    """返回三个显式步的确定性标量序列。"""
    loss_key = f"{prefix}/loss" if prefix else "loss"
    accuracy_key = f"{prefix}/accuracy" if prefix else "accuracy"
    return [
        (0, {loss_key: 1.0, accuracy_key: 0.5}),
        (1, {loss_key: 0.5, accuracy_key: 0.75}),
        (2, {loss_key: 0.25, accuracy_key: 1.0}),
    ]


def log_diagnostic_series(log_function: Callable[..., object], nested_keys: bool) -> None:
    """使用 SwanLab 0.9.0 实际支持的参数记录诊断序列。"""
    prefix = "diagnostic" if nested_keys else None
    for step, metrics in diagnostic_series(prefix):
        log_function(metrics, step=step)


def build_artifact_manifest(
    sdk_version: str,
    run_id: str,
    run_url: str,
    log_dir: Path,
    console_log: Path,
    output_dir: Path,
) -> dict[str, object]:
    """记录诊断运行的云端标识与全部本地数据位置。"""
    return {
        "schema_version": "flow_probe_run_artifacts_v1",
        "tracking_mode": "online",
        "sdk_version": sdk_version,
        "run_id": run_id,
        "run_url": run_url,
        "data_files": {
            "console_log": str(console_log),
            "output_dir": str(output_dir),
            "swanlab_log_dir": str(log_dir),
        },
    }


def run_diagnostic(
    project: str,
    workspace: str,
    name: str,
    output_dir: Path,
    nested_keys: bool,
    with_metadata: bool,
) -> dict[str, object]:
    """执行在线诊断并保存运行制品清单。"""
    import swanlab

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = output_dir / "swanlog"
    console_log = output_dir / "console.log"
    init_kwargs: dict[str, object] = {
        "project": project,
        "workspace": workspace,
        "name": name,
        "description": "SwanLab 图表可见性最小诊断",
        "config": {
            "nested_keys": nested_keys,
            "with_metadata": with_metadata,
        },
        "mode": "online",
        "log_dir": str(log_dir),
    }
    if with_metadata:
        init_kwargs.update(
            {
                "tags": ["llm-probe", "swanlab-diagnostic"],
                "group": "llm-probe-swanlab-diagnostic",
                "job_type": "diagnostic",
            }
        )

    run = swanlab.init(**init_kwargs)
    try:
        log_diagnostic_series(swanlab.log, nested_keys=nested_keys)
        run_id = str(run.id)
    except Exception as exc:
        swanlab.finish(state="crashed", error=str(exc))
        raise
    else:
        swanlab.finish()

    run_url = f"https://swanlab.cn/@{workspace}/{project}/runs/{run_id}/chart"
    manifest = build_artifact_manifest(
        sdk_version=str(swanlab.__version__),
        run_id=run_id,
        run_url=run_url,
        log_dir=log_dir,
        console_log=console_log,
        output_dir=output_dir,
    )
    manifest["logged_series"] = [
        {"step": step, "metrics": metrics}
        for step, metrics in diagnostic_series("diagnostic" if nested_keys else None)
    ]
    (output_dir / "artifact_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SwanLab 在线图表最小诊断")
    parser.add_argument("--project", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--root-keys", action="store_true")
    parser.add_argument("--with-metadata", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = run_diagnostic(
        project=args.project,
        workspace=args.workspace,
        name=args.name,
        output_dir=args.output_dir,
        nested_keys=not args.root_keys,
        with_metadata=args.with_metadata,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
