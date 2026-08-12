"""LSPR24 筛选宽表上的 HGB 与 XGBoost 快速表格基线。"""

from __future__ import annotations

import argparse
import gzip
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, balanced_accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

from flow_probe.lspr24_screen_dataset import Lspr24ScreenBatch, Lspr24ScreenDataset
from flow_probe.tracking import REQUIRED_SWANLAB_PROJECT, REQUIRED_SWANLAB_WORKSPACE, TrackingSettings, flatten_scalar_metrics


class Lspr24ScreenBaselineError(ValueError):
    """快速表格基线的参数或运行目录不合法。"""


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_model(name: str, seed: int, labels: np.ndarray) -> object:
    if name == "hgb":
        return HistGradientBoostingClassifier(
            class_weight="balanced", learning_rate=0.1, max_iter=200, max_leaf_nodes=63, random_state=seed
        )
    if name == "xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as error:
            raise Lspr24ScreenBaselineError("项目环境缺少 XGBoost") from error
        negatives = max(int((labels == 0).sum()), 1)
        positives = max(int((labels == 1).sum()), 1)
        return XGBClassifier(
            objective="binary:logistic", eval_metric="logloss", n_estimators=200, max_depth=8,
            learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, random_state=seed,
            n_jobs=0, scale_pos_weight=negatives / positives,
        )
    raise Lspr24ScreenBaselineError(f"未知模型：{name}")


def _metrics(labels: np.ndarray, probabilities: np.ndarray, train_seconds: float, inference_seconds: float) -> dict[str, object]:
    predictions = (probabilities >= 0.5).astype(np.int64)
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    false_positive_rate = float(matrix[0, 1] / max(matrix[0].sum(), 1))
    return {
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "benign_false_positive_rate": false_positive_rate,
        "sample_count": int(len(labels)),
        "train_seconds": train_seconds,
        "inference_seconds": inference_seconds,
    }


def _write_predictions(output: Path, name: str, batch: Lspr24ScreenBatch, probabilities: np.ndarray) -> None:
    with gzip.open(output, "at", encoding="utf-8") as handle:
        for sample_id, label, probability in zip(batch.sample_ids, batch.labels, probabilities, strict=True):
            handle.write(json.dumps({"model": name, "sample_id": sample_id, "truth": int(label), "malicious_probability": float(probability)}, ensure_ascii=False, sort_keys=True) + "\n")


def _record_swanlab(output_dir: Path, config: dict[str, object], summary: dict[str, object]) -> dict[str, object]:
    settings = TrackingSettings.from_mapping({
        "project": REQUIRED_SWANLAB_PROJECT, "workspace": REQUIRED_SWANLAB_WORKSPACE,
        "run_name": str(config["run_name"]), "description": "LSPR24 6:2:2 筛选宽表快速表格基线",
        "mode": "online", "tags": ["lspr24", "screen", "tabular", "baseline"],
    })
    try:
        import swanlab
        run = swanlab.init(project=settings.project, workspace=settings.workspace, name=settings.run_name, description=settings.description, config=config, mode=settings.mode, tags=list(settings.tags))
        scalars = flatten_scalar_metrics(summary, prefix="baseline")
        swanlab.log(scalars, step=0)
        swanlab.finish()
        result = {"status": "finished", "run_id": str(run.id), "metrics": scalars}
    except Exception as error:
        result = {"status": "failed", "error": str(error)}
    _write_json(output_dir / "swanlab_metrics.json", result)
    return result


def run_baselines(manifest_path: Path, output_dir: Path, seed: int, run_name: str) -> dict[str, object]:
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise Lspr24ScreenBaselineError(f"运行目录已存在，不得复用：{output_dir}")
    output_dir.mkdir(parents=True)
    dataset = Lspr24ScreenDataset(manifest_path)
    config: dict[str, object] = {
        "schema_version": "lspr24-screen-tabular-baselines-v1", "manifest_path": str(dataset.manifest_path),
        "contract_version": dataset.manifest["contract_version"], "seed": seed, "run_name": run_name,
        "models": ["hgb", "xgboost"], "history_lengths": [1, 4], "train_limit": 200000, "validation_limit": 50000,
    }
    _write_json(output_dir / "config.json", config)
    _write_json(output_dir / "environment.json", {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__, "scikit_learn": sklearn.__version__})
    predictions_path = output_dir / "predictions.jsonl.gz"
    results: dict[str, object] = {"schema_version": "lspr24-screen-tabular-results-v1", "runs": {}}
    for history_length in (1, 4):
        train = dataset.load(split_name="train", history_length=history_length, sample_limit=200000)
        validation = dataset.load(split_name="validation", history_length=history_length, sample_limit=50000)
        if len(np.unique(train.labels)) != 2 or len(np.unique(validation.labels)) != 2:
            raise Lspr24ScreenBaselineError(f"H={history_length} 的训练或验证样本必须同时包含两类")
        for model_name in ("hgb", "xgboost"):
            model = _build_model(model_name, seed, train.labels)
            started = time.perf_counter()
            model.fit(train.features, train.labels)
            train_seconds = time.perf_counter() - started
            started = time.perf_counter()
            probabilities = model.predict_proba(validation.features)[:, 1]
            inference_seconds = time.perf_counter() - started
            key = f"{model_name}_h{history_length}"
            run_summary = _metrics(validation.labels, probabilities, train_seconds, inference_seconds)
            run_summary.update({"feature_count": len(train.feature_columns), "train_sample_count": len(train.labels), "validation_sample_count": len(validation.labels)})
            results["runs"][key] = run_summary
            _write_json(output_dir / f"metrics_{key}.json", run_summary)
            _write_predictions(predictions_path, key, validation, probabilities)
    _write_json(output_dir / "summary.json", results)
    results["swanlab"] = _record_swanlab(output_dir, config, results)
    _write_json(output_dir / "summary.json", results)
    return results


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 LSPR24 筛选宽表 HGB/XGBoost 基线")
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-name", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = run_baselines(args.dataset_manifest, args.output_dir, args.seed, args.run_name)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
