"""同一数值字段上的传统恶意流量分类基线。"""

from __future__ import annotations

import argparse
import gzip
import json
import platform
import sys
import time
from collections import Counter
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from flow_probe.evaluate import compute_detection_metrics
from flow_probe.schemas import CANONICAL_CORE_FIELDS, BinaryLabel
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)


class BaselineDataError(ValueError):
    """传统基线输入不满足统一数值字段契约。"""


@dataclass(frozen=True)
class NumericDataset:
    """同一 JSONL 中供传统分类器使用的数值视图。"""

    sample_ids: tuple[str, ...]
    features: np.ndarray
    labels: tuple[BinaryLabel, ...]


def _load_numeric_dataset(path: Path) -> NumericDataset:
    sample_ids: list[str] = []
    feature_rows: list[list[float]] = []
    labels: list[BinaryLabel] = []
    with Path(path).open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, Mapping):
                raise BaselineDataError(f"JSONL 行必须是对象：{path}:{line_number}")
            features = value.get("features")
            if not isinstance(features, Mapping):
                raise BaselineDataError(f"缺少 features：{path}:{line_number}")
            missing = [field for field in CANONICAL_CORE_FIELDS if field not in features]
            if missing:
                raise BaselineDataError(
                    f"features 缺少字段：{path}:{line_number} {', '.join(missing)}"
                )
            label = str(value.get("binary_label", ""))
            if label not in {"benign", "malicious"}:
                raise BaselineDataError(f"未知标签：{path}:{line_number}")
            sample_id = str(value.get("sample_id", "")).strip()
            if not sample_id:
                raise BaselineDataError(f"样本标识不能为空：{path}:{line_number}")

            row = []
            for field in CANONICAL_CORE_FIELDS:
                raw = features[field]
                if raw is None:
                    row.append(float("nan"))
                    continue
                try:
                    row.append(float(raw))
                except (TypeError, ValueError) as error:
                    raise BaselineDataError(
                        f"features 不是数值：{path}:{line_number}:{field}"
                    ) from error
            sample_ids.append(sample_id)
            feature_rows.append(row)
            labels.append(label)  # type: ignore[arg-type]
    if not feature_rows:
        raise BaselineDataError(f"基线数据不能为空：{path}")
    if len(sample_ids) != len(set(sample_ids)):
        raise BaselineDataError(f"样本标识重复：{path}")
    return NumericDataset(
        sample_ids=tuple(sample_ids),
        features=np.asarray(feature_rows, dtype=np.float64),
        labels=tuple(labels),
    )


def _model_factories(seed: int) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    LogisticRegression(
                        class_weight="balanced",
                        max_iter=1000,
                        random_state=seed,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                (
                    "classifier",
                    HistGradientBoostingClassifier(
                        class_weight="balanced",
                        learning_rate=0.1,
                        max_iter=100,
                        max_leaf_nodes=31,
                        random_state=seed,
                    ),
                ),
            ]
        ),
    }


def _evaluate_predictions(
    dataset: NumericDataset,
    predictions: list[BinaryLabel],
    malicious_probabilities: np.ndarray,
    inference_seconds: float,
) -> dict[str, object]:
    metrics = compute_detection_metrics(
        labels=dataset.labels,
        predictions=predictions,
        valid_mask=[True] * len(dataset.labels),
    )
    binary_truth = np.asarray([label == "malicious" for label in dataset.labels], dtype=int)
    metrics["pr_auc"] = float(average_precision_score(binary_truth, malicious_probabilities))
    metrics["roc_auc"] = (
        float(roc_auc_score(binary_truth, malicious_probabilities))
        if len(set(binary_truth)) == 2
        else None
    )
    return {
        "metrics": metrics,
        "inference_seconds": inference_seconds,
        "samples_per_second": len(dataset.labels) / max(inference_seconds, 1e-12),
    }


def _write_predictions(
    output: TextIO | None,
    model_name: str,
    evaluation_name: str,
    dataset: NumericDataset,
    predictions: list[str],
    malicious_probabilities: np.ndarray,
) -> None:
    if output is None:
        return
    for sample_id, truth, prediction, probability in zip(
        dataset.sample_ids,
        dataset.labels,
        predictions,
        malicious_probabilities,
        strict=True,
    ):
        output.write(
            json.dumps(
                {
                    "evaluation": evaluation_name,
                    "malicious_probability": float(probability),
                    "model": model_name,
                    "prediction": prediction,
                    "sample_id": sample_id,
                    "truth": truth,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )


def run_baseline_suite(
    train_path: Path,
    evaluation_paths: Mapping[str, Path],
    seed: int,
    predictions_path: Path | None = None,
) -> dict[str, object]:
    """训练多数类、逻辑回归和梯度提升树并在相同样本上评估。"""
    if not evaluation_paths:
        raise BaselineDataError("至少需要一个评估集")
    train = _load_numeric_dataset(Path(train_path))
    evaluation_sets = {
        name: _load_numeric_dataset(Path(path)) for name, path in sorted(evaluation_paths.items())
    }
    train_distribution = Counter(train.labels)
    majority_label: BinaryLabel = max(
        ("benign", "malicious"), key=lambda label: (train_distribution[label], label)
    )
    majority_probability = 1.0 if majority_label == "malicious" else 0.0
    with ExitStack() as stack:
        prediction_output = None
        if predictions_path is not None:
            predictions_path = Path(predictions_path)
            predictions_path.parent.mkdir(parents=True, exist_ok=True)
            prediction_output = stack.enter_context(
                gzip.open(predictions_path, "xt", encoding="utf-8")
            )
        majority_evaluations: dict[str, object] = {}
        for name, dataset in evaluation_sets.items():
            start = time.perf_counter()
            predictions = [majority_label] * len(dataset.labels)
            probabilities = np.full(len(dataset.labels), majority_probability)
            elapsed = time.perf_counter() - start
            majority_evaluations[name] = _evaluate_predictions(
                dataset, predictions, probabilities, elapsed
            )
            _write_predictions(
                prediction_output,
                "majority",
                name,
                dataset,
                predictions,
                probabilities,
            )
        models: dict[str, object] = {
            "majority": {
                "fit_seconds": 0.0,
                "majority_label": majority_label,
                "evaluations": majority_evaluations,
            }
        }

        for model_name, model in _model_factories(seed).items():
            start = time.perf_counter()
            model.fit(train.features, train.labels)
            fit_seconds = time.perf_counter() - start
            evaluations: dict[str, object] = {}
            malicious_index = list(model.classes_).index("malicious")
            for name, dataset in evaluation_sets.items():
                start = time.perf_counter()
                raw_predictions = model.predict(dataset.features)
                probabilities = model.predict_proba(dataset.features)[:, malicious_index]
                elapsed = time.perf_counter() - start
                predictions = [str(value) for value in raw_predictions]
                evaluations[name] = _evaluate_predictions(  # type: ignore[arg-type]
                    dataset, predictions, probabilities, elapsed
                )
                _write_predictions(
                    prediction_output,
                    model_name,
                    name,
                    dataset,
                    predictions,
                    probabilities,
                )
            models[model_name] = {
                "fit_seconds": fit_seconds,
                "evaluations": evaluations,
            }
    return {
        "schema_version": "flow_probe_traditional_baselines_v1",
        "seed": seed,
        "feature_fields": list(CANONICAL_CORE_FIELDS),
        "train_sample_count": len(train.labels),
        "train_label_distribution": dict(sorted(train_distribution.items())),
        "models": models,
    }


def parse_evaluation_specs(specs: list[str]) -> dict[str, Path]:
    """解析可重复的“名称=路径”评估集参数。"""
    evaluations: dict[str, Path] = {}
    for spec in specs:
        if "=" not in spec:
            raise BaselineDataError("评估集必须使用 名称=路径 格式")
        name, raw_path = spec.split("=", 1)
        name = name.strip()
        raw_path = raw_path.strip()
        if not name or not raw_path:
            raise BaselineDataError("评估集必须使用 名称=路径 格式")
        if name in evaluations:
            raise BaselineDataError(f"评估集名称重复：{name}")
        evaluations[name] = Path(raw_path)
    if not evaluations:
        raise BaselineDataError("至少需要一个评估集")
    return evaluations


def _file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_tracked_baselines(
    train_path: Path,
    evaluation_paths: Mapping[str, Path],
    output_dir: Path,
    seed: int,
    run_name: str,
) -> dict[str, object]:
    """执行带 SwanLab 在线跟踪和完整制品清单的传统基线。"""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise BaselineDataError(f"运行目录已存在，不得复用：{output_dir}")
    train_path = Path(train_path)
    evaluation_paths = {name: Path(path) for name, path in evaluation_paths.items()}
    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "GeNIS 混合防泄漏划分上的传统恶意流量分类基线",
            "mode": "online",
            "tags": ["llm-probe", "genis-2025", "traditional-baseline", "natural-distribution"],
        }
    )
    results_path = output_dir / "baseline_results.json"
    predictions_path = output_dir / "predictions.jsonl.gz"
    metrics_path = output_dir / "swanlab_metrics.json"
    config_path = output_dir / "config_snapshot.json"
    environment_path = output_dir / "environment.json"
    config = {
        "seed": seed,
        "feature_fields": list(CANONICAL_CORE_FIELDS),
        "train": {
            "path": str(train_path),
            "sha256": _file_sha256(train_path),
        },
        "evaluations": {
            name: {"path": str(path), "sha256": _file_sha256(path)}
            for name, path in sorted(evaluation_paths.items())
        },
        "models": ["majority", "logistic_regression", "hist_gradient_boosting"],
    }
    data_files = {
        "baseline_results": results_path,
        "predictions": predictions_path,
        "swanlab_metrics": metrics_path,
        "config_snapshot": config_path,
        "environment": environment_path,
    }

    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings=settings,
            phase="traditional-baselines",
            config=config,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        environment = {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        }
        environment_path.write_text(
            json.dumps(environment, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        summary = run_baseline_suite(
            train_path=train_path,
            evaluation_paths=evaluation_paths,
            seed=seed,
            predictions_path=predictions_path,
        )
        results_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        scalar_metrics = flatten_scalar_metrics(summary["models"], prefix="baseline")
        swanlab.log(scalar_metrics, step=0)
        metrics_path.write_text(
            json.dumps(
                {"step": 0, "metrics": scalar_metrics},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    manifest = json.loads((output_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    with capture_console_log(output_dir / "console.log"):
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行传统恶意流量分类基线")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--evaluation", action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-name", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_tracked_baselines(
        train_path=args.train,
        evaluation_paths=parse_evaluation_specs(args.evaluation),
        output_dir=args.output_dir,
        seed=args.seed,
        run_name=args.run_name,
    )
