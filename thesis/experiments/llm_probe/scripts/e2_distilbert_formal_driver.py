"""运行 E2 DistilBERT 正式基线并保存完整实验制品。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

from flow_probe.e2_distilbert import (
    E2DistilBertTrainingAdapter,
    E2DistilBertTrainingSettings,
)
from flow_probe.e2_hard_domain_baselines import (
    E2BaselineBudget,
    E2TextSample,
    _write_suite,
    run_e2_baseline_suite,
)
from flow_probe.e2_hard_domain_data import (
    E2_FEATURE_FIELDS,
    build_e2_panel,
    load_e2_development_view,
)
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)


MODEL_SOURCE = Path("/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased")
PANEL = "abd_to_c"
SEED = 42


class _RecordingAdapter:
    """保留已拟合预测器，以便原子保存最终检查点。"""

    def __init__(self, settings: E2DistilBertTrainingSettings) -> None:
        self.inner = E2DistilBertTrainingAdapter(settings)
        self.predictor: Any | None = None

    @property
    def last_training_summary(self):
        return self.inner.last_training_summary

    def fit_source_only(
        self,
        *,
        train: Sequence[E2TextSample],
        calibration: Sequence[E2TextSample],
        budget: E2BaselineBudget,
    ):
        self.predictor = self.inner.fit_source_only(
            train=train,
            calibration=calibration,
            budget=budget,
        )
        return self.predictor


def _atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.partial")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_state(output_dir: Path, status: str, **extra: object) -> None:
    _atomic_write_json(
        output_dir / "run_state.json",
        {
            "schema_version": "flow_probe_e2_distilbert_formal_state_v1",
            "status": status,
            "panel": PANEL,
            "seed": SEED,
            "pid": os.getpid(),
            **extra,
        },
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _save_checkpoint(adapter: _RecordingAdapter, output_dir: Path) -> Path:
    if adapter.predictor is None:
        raise RuntimeError("训练结束后没有可保存的 DistilBERT 预测器")
    target = output_dir / "checkpoint-final"
    temporary = output_dir / f".checkpoint-final.{os.getpid()}.partial"
    if target.exists() or temporary.exists():
        raise RuntimeError("最终检查点路径已存在，拒绝覆盖")
    temporary.mkdir()
    try:
        adapter.predictor.model.save_pretrained(temporary, safe_serialization=True)
        adapter.predictor.tokenizer.save_pretrained(temporary)
        records = []
        for path in sorted(path for path in temporary.rglob("*") if path.is_file()):
            records.append(
                {
                    "path": str(path.relative_to(temporary)),
                    "sha256": _sha256(path),
                    "size_bytes": path.stat().st_size,
                }
            )
        _atomic_write_json(
            temporary / "checkpoint_manifest.json",
            {
                "schema_version": "flow_probe_e2_distilbert_checkpoint_v1",
                "kind": "final_selected_model",
                "source_only_fit": True,
                "panel": PANEL,
                "seed": SEED,
                "restart_policy": "fail_explicitly",
                "resume_supported": False,
                "resume_limitation": "当前适配器不暴露优化器、调度器和随机状态",
                "artifacts": records,
            },
        )
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target


def _tracking_settings(run_name: str) -> TrackingSettings:
    return TrackingSettings(
        project=REQUIRED_SWANLAB_PROJECT,
        workspace=REQUIRED_SWANLAB_WORKSPACE,
        run_name=run_name,
        description="TQH-C2 v1.2.0 共同七字段 A+B+D 到 C 的普通 DistilBERT 正式基线",
        mode="online",
        tags=("e2", "distilbert", "abd-to-c", "seed42", "seven-fields"),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 E2 DistilBERT 正式基线")
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-source", type=Path, required=True)
    parser.add_argument("--model-binding-sha256", required=True)
    parser.add_argument("--run-name", required=True)
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    if args.model_source.resolve() != MODEL_SOURCE:
        raise ValueError(f"模型来源必须固定为 {MODEL_SOURCE}")
    binding = args.model_binding_sha256
    if len(binding) != 64 or any(character not in "0123456789abcdef" for character in binding):
        raise ValueError("模型绑定必须是 64 位小写 SHA-256")
    if not args.protocol_dir.is_dir():
        raise ValueError(f"冻结协议目录不存在：{args.protocol_dir}")
    if args.output_dir.exists():
        raise ValueError(f"唯一运行目录已存在，拒绝覆盖：{args.output_dir}")
    if not args.run_name.strip():
        raise ValueError("SwanLab 运行名不能为空")


def run(args: argparse.Namespace) -> int:
    _validate_args(args)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True)
    settings = E2DistilBertTrainingSettings(
        model_source=str(args.model_source.resolve()),
        expected_model_binding_sha256=args.model_binding_sha256,
        device="cuda",
        precision="auto",
        per_device_train_batch_size=16,
        per_device_eval_batch_size=64,
        gradient_accumulation_steps=2,
        max_length=128,
        learning_rate=2e-5,
        weight_decay=0.01,
        num_train_epochs=3,
        warmup_ratio=0.1,
        max_grad_norm=1.0,
        num_workers=0,
        early_stopping_patience=2,
    )
    budget = E2BaselineBudget(
        seed=SEED,
        max_iterations=100,
        threshold_source="source_calibration",
    )
    configuration = {
        "schema_version": "flow_probe_e2_distilbert_formal_config_v1",
        "panel": PANEL,
        "seed": SEED,
        "protocol_dir": str(args.protocol_dir.resolve()),
        "source_domains": ["A", "B", "D"],
        "target_domain": "C",
        "feature_fields": list(E2_FEATURE_FIELDS),
        "threshold_source": "source_calibration",
        "model_source": str(args.model_source.resolve()),
        "model_binding_sha256": args.model_binding_sha256,
        "training": asdict(settings),
        "common_budget": asdict(budget),
        "swanlab_mode": "online",
        "restart_policy": "fail_explicitly_without_optimizer_checkpoint",
    }
    _atomic_write_json(output_dir / "config_snapshot.json", configuration)
    _write_state(output_dir, "prepared")

    adapter = _RecordingAdapter(settings)
    results_dir = output_dir / "results"
    metrics_path = output_dir / "metrics.jsonl"
    checkpoint_dir = output_dir / "checkpoint-final"
    tracking = _tracking_settings(args.run_name)
    data_files = {
        "config_snapshot": output_dir / "config_snapshot.json",
        "run_state": output_dir / "run_state.json",
        "training_summary": output_dir / "distilbert_training.json",
        "metrics": metrics_path,
        "summary": results_dir / "summary.json",
        "predictions": results_dir / "predictions.jsonl",
        "checkpoint": checkpoint_dir,
    }

    try:
        with capture_console_log(output_dir / "console.log"):
            with swanlab_run(
                settings=tracking,
                phase="e2-distilbert-baseline",
                config=configuration,
                artifact_dir=output_dir,
                data_files=data_files,
            ) as swanlab:
                _write_state(output_dir, "running")
                start_metrics = {"run/started": 1, "run/seed": SEED}
                swanlab.log(start_metrics, step=0)
                metrics_path.write_text(
                    json.dumps(
                        {"step": 0, "event": "started", "metrics": start_metrics},
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                samples = load_e2_development_view(args.protocol_dir)
                panel = build_e2_panel(samples, panel=PANEL)
                suite = run_e2_baseline_suite(
                    panel,
                    models=("distilbert",),
                    budget=budget,
                    distilbert_adapter=adapter,
                )
                _write_suite(results_dir, suite)
                if adapter.last_training_summary is None:
                    raise RuntimeError("训练结束后缺少 DistilBERT 训练摘要")
                training_summary = dict(adapter.last_training_summary)
                _atomic_write_json(output_dir / "distilbert_training.json", training_summary)
                _save_checkpoint(adapter, output_dir)

                final_metrics = flatten_scalar_metrics(
                    suite.results["distilbert"].metrics,
                    prefix="target_c",
                )
                final_metrics["training/optimizer_steps"] = int(
                    training_summary["optimizer_steps"]
                )
                final_metrics["training/best_source_calibration_macro_f1"] = float(
                    training_summary["best_source_calibration_macro_f1"]
                )
                final_step = int(training_summary["optimizer_steps"])
                swanlab.log(final_metrics, step=max(1, final_step))
                with metrics_path.open("a", encoding="utf-8") as target:
                    target.write(
                        json.dumps(
                            {
                                "step": max(1, final_step),
                                "event": "finished",
                                "metrics": final_metrics,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n"
                    )
        _write_state(
            output_dir,
            "finished",
            optimizer_steps=int(training_summary["optimizer_steps"]),
            checkpoint=str(checkpoint_dir),
        )
        print(
            json.dumps(
                {
                    "status": "finished",
                    "output_dir": str(output_dir),
                    "panel": PANEL,
                    "seed": SEED,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except KeyboardInterrupt:
        _write_state(output_dir, "interrupted", resume_supported=False)
        raise
    except BaseException as error:
        _write_state(
            output_dir,
            "failed",
            failure_type=type(error).__name__,
            failure=str(error),
            resume_supported=False,
        )
        raise


def main(argv: Sequence[str] | None = None) -> int:
    return run(_build_parser().parse_args(argv))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(
            json.dumps(
                {"status": "failed", "reason": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise
