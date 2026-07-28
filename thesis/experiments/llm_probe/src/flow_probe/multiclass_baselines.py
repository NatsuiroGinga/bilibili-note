"""分层多分类与未知攻击拒识的传统基线。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

import numpy as np
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from flow_probe.schemas import CANONICAL_CORE_FIELDS
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)


class MulticlassBaselineError(ValueError):
    """多分类基线输入或开放集协议不合法。"""


@dataclass(frozen=True)
class MulticlassNumericDataset:
    """统一数值视图及任务标签。"""

    sample_ids: tuple[str, ...]
    features: np.ndarray
    labels: tuple[str, ...]


def _load_dataset(path: Path, allowed_labels: frozenset[str]) -> MulticlassNumericDataset:
    sample_ids: list[str] = []
    feature_rows: list[list[float]] = []
    labels: list[str] = []
    with Path(path).open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, Mapping):
                raise MulticlassBaselineError(f"JSONL 行必须是对象：{path}:{line_number}")
            sample_id = str(value.get("sample_id", "")).strip()
            label = str(value.get("task_label", "")).strip()
            features = value.get("features")
            if not sample_id:
                raise MulticlassBaselineError(f"样本标识不能为空：{path}:{line_number}")
            if label not in allowed_labels:
                raise MulticlassBaselineError(f"未知任务标签：{path}:{line_number}:{label}")
            if not isinstance(features, Mapping):
                raise MulticlassBaselineError(f"缺少 features：{path}:{line_number}")
            missing = [field for field in CANONICAL_CORE_FIELDS if field not in features]
            if missing:
                raise MulticlassBaselineError(
                    f"features 缺少字段：{path}:{line_number} {', '.join(missing)}"
                )
            row: list[float] = []
            for field in CANONICAL_CORE_FIELDS:
                raw = features[field]
                if raw is None:
                    row.append(float("nan"))
                    continue
                try:
                    row.append(float(raw))
                except (TypeError, ValueError) as error:
                    raise MulticlassBaselineError(
                        f"features 不是数值：{path}:{line_number}:{field}"
                    ) from error
            sample_ids.append(sample_id)
            labels.append(label)
            feature_rows.append(row)
    if not feature_rows:
        raise MulticlassBaselineError(f"多分类数据不能为空：{path}")
    if len(sample_ids) != len(set(sample_ids)):
        raise MulticlassBaselineError(f"样本标识重复：{path}")
    return MulticlassNumericDataset(
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


def _calibrate_threshold(
    confidences: np.ndarray, max_known_rejection_rate: float
) -> tuple[float, float]:
    if not 0 <= max_known_rejection_rate < 1:
        raise MulticlassBaselineError("最大已知类拒识率必须位于 [0, 1)")
    if confidences.ndim != 1 or len(confidences) == 0 or not np.isfinite(confidences).all():
        raise MulticlassBaselineError("验证集置信度必须是一维有限非空数组")
    threshold = float(np.quantile(confidences, max_known_rejection_rate, method="lower"))
    rejection_rate = float(np.mean(confidences < threshold))
    if rejection_rate > max_known_rejection_rate + 1e-12:
        raise AssertionError("验证集拒识率超过校准预算")
    return threshold, rejection_rate


def _apply_rejection(
    predictions: Sequence[str],
    confidences: np.ndarray,
    threshold: float,
    unknown_label: str | None,
) -> list[str]:
    if unknown_label is None:
        return list(predictions)
    return [
        unknown_label if confidence < threshold else prediction
        for prediction, confidence in zip(predictions, confidences, strict=True)
    ]


def _metrics(
    truth: Sequence[str],
    predictions: Sequence[str],
    known_labels: Sequence[str],
    unknown_label: str | None,
) -> dict[str, object]:
    configured_labels = [*known_labels]
    if unknown_label is not None:
        configured_labels.append(unknown_label)
    present_labels = [label for label in configured_labels if label in set(truth)]
    recalls = recall_score(
        truth,
        predictions,
        labels=configured_labels,
        average=None,
        zero_division=0,
    )
    present_recalls = recall_score(
        truth,
        predictions,
        labels=present_labels,
        average=None,
        zero_division=0,
    )
    truth_array = np.asarray(truth)
    prediction_array = np.asarray(predictions)
    benign_mask = truth_array == "benign"
    known_mask = np.isin(truth_array, known_labels)
    return {
        "sample_count": len(truth),
        "accuracy": float(accuracy_score(truth, predictions)),
        "balanced_accuracy": float(np.mean(present_recalls)),
        "macro_f1": float(
            f1_score(
                truth,
                predictions,
                labels=present_labels,
                average="macro",
                zero_division=0,
            )
        ),
        "configured_macro_f1": float(
            f1_score(
                truth,
                predictions,
                labels=configured_labels,
                average="macro",
                zero_division=0,
            )
        ),
        "per_class_recall": {
            label: float(value) for label, value in zip(configured_labels, recalls, strict=True)
        },
        "confusion_matrix": confusion_matrix(truth, predictions, labels=configured_labels).tolist(),
        "label_order": configured_labels,
        "unknown_recall": (
            float(np.mean(prediction_array[truth_array == unknown_label] == unknown_label))
            if unknown_label is not None and np.any(truth_array == unknown_label)
            else None
        ),
        "benign_false_positive_rate": (
            float(np.mean(prediction_array[benign_mask] != "benign"))
            if np.any(benign_mask)
            else None
        ),
        "known_rejection_rate": (
            float(np.mean(prediction_array[known_mask] == unknown_label))
            if unknown_label is not None and np.any(known_mask)
            else None
        ),
    }


def _evaluate(
    dataset: MulticlassNumericDataset,
    raw_predictions: Sequence[str],
    confidences: np.ndarray,
    inference_seconds: float,
    threshold: float,
    known_labels: Sequence[str],
    unknown_label: str | None,
) -> tuple[dict[str, object], list[str]]:
    predictions = _apply_rejection(raw_predictions, confidences, threshold, unknown_label)
    return (
        {
            "metrics": _metrics(dataset.labels, predictions, known_labels, unknown_label),
            "inference_seconds": inference_seconds,
            "samples_per_second": len(dataset.labels) / max(inference_seconds, 1e-12),
        },
        predictions,
    )


def _write_predictions(
    output: TextIO | None,
    model_name: str,
    evaluation_name: str,
    dataset: MulticlassNumericDataset,
    predictions: Sequence[str],
    confidences: np.ndarray,
) -> None:
    if output is None:
        return
    for sample_id, truth, prediction, confidence in zip(
        dataset.sample_ids,
        dataset.labels,
        predictions,
        confidences,
        strict=True,
    ):
        output.write(
            json.dumps(
                {
                    "confidence": float(confidence),
                    "evaluation": evaluation_name,
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


def _model_probabilities(
    model: Pipeline,
    dataset: MulticlassNumericDataset,
) -> tuple[list[str], np.ndarray]:
    probabilities = model.predict_proba(dataset.features)
    classes = [str(label) for label in model.classes_]
    class_indices = np.argmax(probabilities, axis=1)
    predictions = [classes[index] for index in class_indices]
    confidences = np.max(probabilities, axis=1)
    return predictions, confidences


def run_multiclass_baseline_suite(
    train_path: Path,
    validation_path: Path,
    evaluation_paths: Mapping[str, Path],
    known_labels: Sequence[str],
    unknown_label: str | None,
    max_known_rejection_rate: float,
    seed: int,
    predictions_path: Path | None = None,
) -> dict[str, object]:
    """比较三类传统模型，并仅用已知类验证集校准未知拒识。"""
    known_labels = tuple(str(label) for label in known_labels)
    if len(known_labels) < 2 or len(known_labels) != len(set(known_labels)):
        raise MulticlassBaselineError("已知标签必须至少两个且不得重复")
    if unknown_label is not None and unknown_label in known_labels:
        raise MulticlassBaselineError("未知标签不得出现在已知标签中")
    if not evaluation_paths:
        raise MulticlassBaselineError("至少需要一个评估集")
    known_set = frozenset(known_labels)
    evaluation_labels = known_set | ({unknown_label} if unknown_label else set())
    train = _load_dataset(Path(train_path), known_set)
    validation = _load_dataset(Path(validation_path), known_set)
    if set(train.labels) != known_set or set(validation.labels) != known_set:
        raise MulticlassBaselineError("训练集和验证集必须覆盖全部已知标签")
    evaluation_sets = {
        name: _load_dataset(Path(path), frozenset(evaluation_labels))
        for name, path in sorted(evaluation_paths.items())
    }
    train_distribution = Counter(train.labels)
    majority_label = max(known_labels, key=lambda label: (train_distribution[label], label))

    with ExitStack() as stack:
        output = None
        if predictions_path is not None:
            predictions_path = Path(predictions_path)
            predictions_path.parent.mkdir(parents=True, exist_ok=True)
            output = stack.enter_context(gzip.open(predictions_path, "wt", encoding="utf-8"))

        validation_confidences = np.ones(len(validation.labels), dtype=np.float64)
        majority_threshold, majority_rejection = _calibrate_threshold(
            validation_confidences, max_known_rejection_rate
        )
        majority_evaluations: dict[str, object] = {}
        for name, dataset in evaluation_sets.items():
            start = time.perf_counter()
            raw_predictions = [majority_label] * len(dataset.labels)
            confidences = np.ones(len(dataset.labels), dtype=np.float64)
            elapsed = time.perf_counter() - start
            result, predictions = _evaluate(
                dataset,
                raw_predictions,
                confidences,
                elapsed,
                majority_threshold,
                known_labels,
                unknown_label,
            )
            majority_evaluations[name] = result
            _write_predictions(output, "majority", name, dataset, predictions, confidences)
        models: dict[str, object] = {
            "majority": {
                "fit_seconds": 0.0,
                "majority_label": majority_label,
                "calibration": {
                    "confidence_threshold": majority_threshold,
                    "known_rejection_rate": majority_rejection,
                    "max_known_rejection_rate": max_known_rejection_rate,
                    "uses_ood_labels": False,
                },
                "evaluations": majority_evaluations,
            }
        }

        for model_name, model in _model_factories(seed).items():
            start = time.perf_counter()
            model.fit(train.features, train.labels)
            fit_seconds = time.perf_counter() - start
            _, validation_confidences = _model_probabilities(model, validation)
            threshold, rejection_rate = _calibrate_threshold(
                validation_confidences, max_known_rejection_rate
            )
            evaluations: dict[str, object] = {}
            for name, dataset in evaluation_sets.items():
                start = time.perf_counter()
                raw_predictions, confidences = _model_probabilities(model, dataset)
                elapsed = time.perf_counter() - start
                result, predictions = _evaluate(
                    dataset,
                    raw_predictions,
                    confidences,
                    elapsed,
                    threshold,
                    known_labels,
                    unknown_label,
                )
                evaluations[name] = result
                _write_predictions(output, model_name, name, dataset, predictions, confidences)
            models[model_name] = {
                "fit_seconds": fit_seconds,
                "calibration": {
                    "confidence_threshold": threshold,
                    "known_rejection_rate": rejection_rate,
                    "max_known_rejection_rate": max_known_rejection_rate,
                    "uses_ood_labels": False,
                },
                "evaluations": evaluations,
            }

    return {
        "schema_version": "flow_probe_multiclass_baselines_v1",
        "seed": seed,
        "known_labels": list(known_labels),
        "unknown_label": unknown_label,
        "feature_fields": list(CANONICAL_CORE_FIELDS),
        "train_sample_count": len(train.labels),
        "validation_sample_count": len(validation.labels),
        "train_label_distribution": dict(sorted(train_distribution.items())),
        "models": models,
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _required_sample_paths(sample_dir: Path) -> dict[str, Path]:
    paths = {
        "family_train": sample_dir / "family" / "train.jsonl",
        "family_validation": sample_dir / "family" / "validation.jsonl",
        "family_test": sample_dir / "family" / "test.jsonl",
        "subtype_train": sample_dir / "subtype" / "train.jsonl",
        "subtype_validation": sample_dir / "subtype" / "validation.jsonl",
        "subtype_test": sample_dir / "subtype" / "test.jsonl",
        "ood_dos_icmp": sample_dir / "subtype_ood" / "dos-icmp.jsonl",
        "ood_dos_pushack": sample_dir / "subtype_ood" / "dos-pushack.jsonl",
        "ood_dos_udp": sample_dir / "subtype_ood" / "dos-udp.jsonl",
        "sample_manifest": sample_dir / "sample_manifest.json",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise MulticlassBaselineError(f"分层实验集不完整：{', '.join(missing)}")
    return paths


def run_tracked_multiclass_baselines(
    sample_dir: Path,
    output_dir: Path,
    seed: int,
    run_name: str,
    max_known_rejection_rate: float = 0.05,
) -> dict[str, object]:
    """在同一 SwanLab 运行中完成家族和子类开放集传统基线。"""
    sample_dir = Path(sample_dir)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise MulticlassBaselineError(f"运行目录已存在，不得复用：{output_dir}")
    paths = _required_sample_paths(sample_dir)
    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "GeNIS 分层多分类与未知攻击拒识传统基线",
            "mode": "online",
            "tags": [
                "llm-probe",
                "genis-2025",
                "traditional-baseline",
                "multiclass",
                "open-set",
            ],
        }
    )
    results_path = output_dir / "multiclass_baseline_results.json"
    family_predictions_path = output_dir / "family_predictions.jsonl.gz"
    subtype_predictions_path = output_dir / "subtype_predictions.jsonl.gz"
    metrics_path = output_dir / "swanlab_metrics.json"
    config_path = output_dir / "config_snapshot.json"
    environment_path = output_dir / "environment.json"
    config = {
        "seed": seed,
        "sample_dir": str(sample_dir),
        "max_known_rejection_rate": max_known_rejection_rate,
        "family_labels": ["benign", "bruteforce", "dos"],
        "subtype_labels": ["benign", "ftp", "smb", "ssh", "hulk", "slowloris"],
        "unknown_label": "unknown_attack",
        "source_files": {
            name: {"path": str(path), "sha256": _file_sha256(path)}
            for name, path in sorted(paths.items())
        },
        "models": ["majority", "logistic_regression", "hist_gradient_boosting"],
    }
    data_files = {
        "multiclass_baseline_results": results_path,
        "family_predictions": family_predictions_path,
        "subtype_predictions": subtype_predictions_path,
        "swanlab_metrics": metrics_path,
        "config_snapshot": config_path,
        "environment": environment_path,
    }

    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings=settings,
            phase="multiclass-traditional-baselines",
            config=config,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        environment_path.write_text(
            json.dumps(
                {
                    "python": sys.version,
                    "platform": platform.platform(),
                    "numpy": np.__version__,
                    "scikit_learn": sklearn.__version__,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        family_summary = run_multiclass_baseline_suite(
            train_path=paths["family_train"],
            validation_path=paths["family_validation"],
            evaluation_paths={"test": paths["family_test"]},
            known_labels=("benign", "bruteforce", "dos"),
            unknown_label=None,
            max_known_rejection_rate=0.0,
            seed=seed,
            predictions_path=family_predictions_path,
        )
        subtype_summary = run_multiclass_baseline_suite(
            train_path=paths["subtype_train"],
            validation_path=paths["subtype_validation"],
            evaluation_paths={
                "test": paths["subtype_test"],
                "ood-dos-icmp": paths["ood_dos_icmp"],
                "ood-dos-pushack": paths["ood_dos_pushack"],
                "ood-dos-udp": paths["ood_dos_udp"],
            },
            known_labels=("benign", "ftp", "smb", "ssh", "hulk", "slowloris"),
            unknown_label="unknown_attack",
            max_known_rejection_rate=max_known_rejection_rate,
            seed=seed,
            predictions_path=subtype_predictions_path,
        )
        summary = {
            "schema_version": "flow_probe_tracked_multiclass_baselines_v1",
            "seed": seed,
            "family": family_summary,
            "subtype": subtype_summary,
        }
        results_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        scalar_metrics = flatten_scalar_metrics(summary, prefix="multiclass_baseline")
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
    parser = argparse.ArgumentParser(description="运行 GeNIS 分层多分类传统基线")
    parser.add_argument("--sample-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--max-known-rejection-rate", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_tracked_multiclass_baselines(
        sample_dir=args.sample_dir,
        output_dir=args.output_dir,
        seed=args.seed,
        run_name=args.run_name,
        max_known_rejection_rate=args.max_known_rejection_rate,
    )
