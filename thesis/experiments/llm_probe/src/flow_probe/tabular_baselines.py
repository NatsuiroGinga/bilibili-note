"""冻结协议上共享数值视图的 HGB 与 XGBoost 基线。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import resource
import sys
import time
from collections import Counter
from collections.abc import Mapping, MutableMapping, Sequence
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, TextIO

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from flow_probe.frozen_protocol import (
    CANDIDATE_PROTOCOL_VERSION,
    FINAL_TUNING_STAGE,
    FROZEN_PROTOCOL_VERSION,
    THEORY_SELECTION_STAGE,
    TREE_VIEW_NAME,
    FrozenProtocol,
    TabularSplit,
    load_frozen_protocol,
)
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

SUPPORTED_MODELS = ("hgb", "xgboost")
RUN_STAGES = (THEORY_SELECTION_STAGE, FINAL_TUNING_STAGE)
MAX_VALIDATION_TUNING_TRIALS = 10


class TabularBaselineError(ValueError):
    """统一树模型基线的输入、配置或输出不合法。"""


class XGBoostDependencyError(RuntimeError):
    """请求 XGBoost 时项目环境缺少可用依赖。"""


class ProbabilisticClassifier(Protocol):
    """统一入口所需的最小分类器接口。"""

    classes_: np.ndarray

    def fit(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        *,
        sample_weight: np.ndarray,
    ) -> object: ...

    def predict(self, features: np.ndarray) -> np.ndarray: ...

    def predict_proba(self, features: np.ndarray) -> np.ndarray: ...

    def get_params(self, deep: bool = True) -> Mapping[str, object]: ...


@dataclass(frozen=True)
class PreparedTabularData:
    """所有模型共享且只由训练清单派生拟合项的输入。"""

    protocol: FrozenProtocol
    view_name: str
    train: TabularSplit
    evaluations: Mapping[str, TabularSplit]
    known_labels: tuple[str, ...]
    encoded_train_labels: np.ndarray
    train_sample_weights: np.ndarray
    feature_matrix_sha256: str
    train_labels_sha256: str


@dataclass(frozen=True)
class TabularSuiteResult:
    """可直接落盘的指标摘要与成本记录。"""

    summary: Mapping[str, object]
    cost: Mapping[str, object]


def parse_named_manifests(specs: Sequence[str]) -> dict[str, str]:
    """解析可重复的“名称=协议内清单路径”参数。"""
    manifests: dict[str, str] = {}
    for spec in specs:
        if "=" not in spec:
            raise TabularBaselineError("评估清单必须使用 名称=相对路径 格式")
        name, path = (part.strip() for part in spec.split("=", 1))
        if not name or not path:
            raise TabularBaselineError("评估清单必须使用 名称=相对路径 格式")
        if name in manifests:
            raise TabularBaselineError(f"评估名称重复：{name}")
        if path in manifests.values():
            raise TabularBaselineError(f"评估清单路径重复：{path}")
        manifests[name] = path
    if not manifests:
        raise TabularBaselineError("至少需要一个评估清单")
    return manifests


def _normalise_model_keys(model_keys: Sequence[str]) -> tuple[str, ...]:
    keys = tuple(str(key).strip() for key in model_keys)
    if not keys or any(not key for key in keys):
        raise TabularBaselineError("至少需要一个非空模型键")
    if len(keys) != len(set(keys)):
        raise TabularBaselineError("模型键不得重复")
    unsupported = sorted(set(keys).difference(SUPPORTED_MODELS))
    if unsupported:
        raise TabularBaselineError(f"不支持的模型键：{', '.join(unsupported)}")
    return keys


def _stage_contract(stage: str, expected_protocol_version: str) -> tuple[str, str]:
    if stage == THEORY_SELECTION_STAGE:
        required_version = CANDIDATE_PROTOCOL_VERSION
        expected_status = "provisional"
    elif stage == FINAL_TUNING_STAGE:
        required_version = FROZEN_PROTOCOL_VERSION
        expected_status = "frozen"
    else:
        raise TabularBaselineError(f"未知运行阶段：{stage}")
    if expected_protocol_version != required_version:
        raise TabularBaselineError(
            f"阶段 {stage} 必须使用协议版本 {required_version}，实际为 "
            f"{expected_protocol_version}"
        )
    return expected_status, stage


def _validation_budget(trial_index: int) -> dict[str, object]:
    if isinstance(trial_index, bool) or not 0 <= trial_index <= MAX_VALIDATION_TUNING_TRIALS:
        raise TabularBaselineError(
            f"验证调参试次必须位于 0..{MAX_VALIDATION_TUNING_TRIALS}；" "0 表示公开默认配置"
        )
    return {
        "public_default_configuration_count": 1,
        "maximum_validation_tuning_trials": MAX_VALIDATION_TUNING_TRIALS,
        "trial_index": trial_index,
        "configuration_origin": "public_default" if trial_index == 0 else "validation_tuning",
        "test_manifest_visible": False,
    }


def _array_sha256(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(json.dumps(contiguous.shape, separators=(",", ":")).encode("ascii"))
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _labels_sha256(labels: Sequence[str]) -> str:
    payload = json.dumps(list(labels), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prepare_tabular_data(
    *,
    protocol_dir: Path,
    train_manifest: str | Path,
    evaluation_manifests: Mapping[str, str | Path],
    label_field: str,
    view_name: str = TREE_VIEW_NAME,
    stage: str = FINAL_TUNING_STAGE,
    expected_protocol_version: str = FROZEN_PROTOCOL_VERSION,
) -> PreparedTabularData:
    """完成协议预检，并从训练清单唯一派生标签编码与样本权重。"""
    if not evaluation_manifests:
        raise TabularBaselineError("至少需要一个评估清单")
    expected_status, expected_phase = _stage_contract(stage, expected_protocol_version)
    protocol = load_frozen_protocol(
        protocol_dir,
        expected_protocol_version=expected_protocol_version,
        expected_status=expected_status,
        expected_phase=expected_phase,
    )
    train = protocol.load_tabular_split(
        train_manifest, view_name=view_name, label_field=label_field
    )
    if train.manifest.split_id != "train":
        raise TabularBaselineError(
            f"训练入口只接受 split_id=train 的清单：{train.manifest.relative_path}"
        )

    evaluations: dict[str, TabularSplit] = {}
    seen_paths: set[str] = set()
    for name, manifest_path in sorted(evaluation_manifests.items()):
        cleaned_name = str(name).strip()
        if not cleaned_name:
            raise TabularBaselineError("评估名称不能为空")
        split = protocol.load_tabular_split(
            manifest_path, view_name=view_name, label_field=label_field
        )
        if split.manifest.relative_path in seen_paths:
            raise TabularBaselineError(f"评估清单路径重复：{split.manifest.relative_path}")
        seen_paths.add(split.manifest.relative_path)
        if split.manifest.suite_id != train.manifest.suite_id:
            raise TabularBaselineError(
                "一次运行的训练与评估必须属于同一 suite_id："
                f"{train.manifest.suite_id} != {split.manifest.suite_id}"
            )
        if split.manifest.split_id != "validation":
            raise TabularBaselineError(
                "调参与路线选择入口只允许读取 split_id=validation 的清单，"
                f"拒绝 {split.manifest.split_id}：{split.manifest.relative_path}"
            )
        evaluations[cleaned_name] = split

    known_labels = tuple(sorted(set(train.labels)))
    if len(known_labels) < 2:
        raise TabularBaselineError("训练清单必须至少包含两个标签")
    label_to_index = {label: index for index, label in enumerate(known_labels)}
    encoded_labels = np.asarray([label_to_index[label] for label in train.labels], dtype=np.int64)
    sample_weights = np.asarray(
        compute_sample_weight(class_weight="balanced", y=encoded_labels), dtype=np.float64
    )
    encoded_labels.setflags(write=False)
    sample_weights.setflags(write=False)
    return PreparedTabularData(
        protocol=protocol,
        view_name=view_name,
        train=train,
        evaluations=MappingProxyType(evaluations),
        known_labels=known_labels,
        encoded_train_labels=encoded_labels,
        train_sample_weights=sample_weights,
        feature_matrix_sha256=_array_sha256(train.features),
        train_labels_sha256=_labels_sha256(train.labels),
    )


def _import_xgboost() -> object:
    try:
        return importlib.import_module("xgboost")
    except (ImportError, OSError) as error:
        raise XGBoostDependencyError(
            "请求了 xgboost，但当前环境无法导入该依赖。请先执行 "
            "`uv sync --locked --extra gpu --dry-run`，确认不会移除训练依赖后，"
            "再执行 `uv sync --locked --extra gpu`。"
        ) from error


def _build_model(model_key: str, *, seed: int, class_count: int) -> ProbabilisticClassifier:
    if model_key == "hgb":
        return HistGradientBoostingClassifier(
            learning_rate=0.1,
            max_iter=100,
            max_leaf_nodes=31,
            early_stopping=False,
            random_state=seed,
        )
    if model_key == "xgboost":
        xgboost = _import_xgboost()
        objective = "binary:logistic" if class_count == 2 else "multi:softprob"
        parameters: dict[str, object] = {
            "colsample_bytree": 1.0,
            "eval_metric": "logloss" if class_count == 2 else "mlogloss",
            "learning_rate": 0.1,
            "max_depth": 6,
            "n_estimators": 100,
            "n_jobs": 1,
            "objective": objective,
            "random_state": seed,
            "subsample": 1.0,
            "tree_method": "hist",
            "verbosity": 0,
            "device": "cpu",
        }
        if class_count > 2:
            parameters["num_class"] = class_count
        classifier = getattr(xgboost, "XGBClassifier", None)
        if classifier is None:
            raise XGBoostDependencyError("xgboost 模块缺少 XGBClassifier，依赖安装不完整")
        return classifier(**parameters)
    raise TabularBaselineError(f"不支持的模型键：{model_key}")


def _expected_calibration_error(
    truth: Sequence[str], predictions: Sequence[str], confidences: np.ndarray, bins: int = 15
) -> float:
    truth_array = np.asarray(truth)
    prediction_array = np.asarray(predictions)
    correctness = (truth_array == prediction_array).astype(np.float64)
    edges = np.linspace(0.0, 1.0, bins + 1)
    error = 0.0
    for index in range(bins):
        if index == 0:
            mask = (confidences >= edges[index]) & (confidences <= edges[index + 1])
        else:
            mask = (confidences > edges[index]) & (confidences <= edges[index + 1])
        if np.any(mask):
            error += float(np.mean(mask)) * abs(
                float(np.mean(correctness[mask])) - float(np.mean(confidences[mask]))
            )
    return error


def _normalise_probability_rows(
    values: object,
    *,
    sample_count: int,
    class_count: int,
) -> np.ndarray:
    probabilities = np.asarray(values, dtype=np.float64)
    if probabilities.ndim != 2 or probabilities.shape != (sample_count, class_count):
        raise TabularBaselineError("分类器概率矩阵形状与样本或训练标签不一致")
    if not np.isfinite(probabilities).all():
        raise TabularBaselineError("分类器输出了非有限概率")
    if np.any(probabilities < 0.0) or np.any(probabilities > 1.0):
        raise TabularBaselineError("分类器输出了 [0, 1] 范围外的概率")
    row_sums = np.sum(probabilities, axis=1, keepdims=True)
    if np.any(row_sums <= 0.0):
        raise TabularBaselineError("分类器输出了概率和不为正的样本")
    probabilities = probabilities / row_sums
    probabilities.setflags(write=False)
    return probabilities


def _evaluate(
    *,
    dataset: TabularSplit,
    encoded_predictions: np.ndarray,
    probabilities: np.ndarray,
    known_labels: Sequence[str],
    inference_seconds: float,
) -> tuple[dict[str, object], list[str], np.ndarray]:
    if probabilities.ndim != 2 or probabilities.shape != (
        len(dataset.sample_ids),
        len(known_labels),
    ):
        raise TabularBaselineError("分类器概率矩阵形状与样本或训练标签不一致")
    if not np.isfinite(probabilities).all():
        raise TabularBaselineError("分类器输出了非有限概率")
    if np.any(encoded_predictions < 0) or np.any(encoded_predictions >= len(known_labels)):
        raise TabularBaselineError("分类器输出了训练标签空间外的类别索引")

    predictions = [known_labels[int(index)] for index in encoded_predictions]
    truth = list(dataset.labels)
    metric_labels = sorted(set(known_labels) | set(truth))
    precision, recall, class_f1, support = precision_recall_fscore_support(
        truth,
        predictions,
        labels=metric_labels,
        zero_division=0,
    )
    present_recalls = [
        float(value) for value, count in zip(recall, support, strict=True) if int(count) > 0
    ]
    confidences = np.max(probabilities, axis=1)
    truth_array = np.asarray(truth)
    prediction_array = np.asarray(predictions)
    known_mask = np.isin(truth_array, known_labels)
    unseen_mask = ~known_mask
    benign_mask = truth_array == "benign"
    known_label_to_index = {label: index for index, label in enumerate(known_labels)}
    if np.any(known_mask):
        known_truth = np.asarray(
            [known_label_to_index[label] for label in truth_array[known_mask]], dtype=np.int64
        )
        known_log_loss = float(
            log_loss(
                known_truth,
                probabilities[known_mask],
                labels=list(range(len(known_labels))),
            )
        )
    else:
        known_log_loss = None

    metrics: dict[str, object] = {
        "sample_count": len(truth),
        "accuracy": float(accuracy_score(truth, predictions)),
        "balanced_accuracy": float(np.mean(present_recalls)),
        "macro_f1": float(
            f1_score(truth, predictions, labels=metric_labels, average="macro", zero_division=0)
        ),
        "expected_calibration_error": _expected_calibration_error(truth, predictions, confidences),
        "known_log_loss": known_log_loss,
        "benign_false_positive_rate": (
            float(np.mean(prediction_array[benign_mask] != "benign"))
            if np.any(benign_mask)
            else None
        ),
        "unseen_truth_sample_count": int(np.sum(unseen_mask)),
        "unseen_truth_recall": (
            float(np.mean(prediction_array[unseen_mask] == truth_array[unseen_mask]))
            if np.any(unseen_mask)
            else None
        ),
        "per_class": {
            label: {
                "precision": float(label_precision),
                "recall": float(label_recall),
                "f1": float(label_f1),
                "support": int(label_support),
            }
            for label, label_precision, label_recall, label_f1, label_support in zip(
                metric_labels, precision, recall, class_f1, support, strict=True
            )
        },
        "confusion_matrix": confusion_matrix(truth, predictions, labels=metric_labels).tolist(),
        "label_order": metric_labels,
        "inference_seconds": inference_seconds,
        "samples_per_second": len(truth) / max(inference_seconds, 1e-12),
        "structured_output_validity": None,
    }
    return metrics, predictions, confidences


def _write_predictions(
    output: TextIO | None,
    *,
    model_key: str,
    evaluation_name: str,
    dataset: TabularSplit,
    predictions: Sequence[str],
    confidences: np.ndarray,
    probabilities: np.ndarray,
    known_labels: Sequence[str],
) -> None:
    if output is None:
        return
    for sample_id, truth, prediction, confidence, row_probabilities in zip(
        dataset.sample_ids,
        dataset.labels,
        predictions,
        confidences,
        probabilities,
        strict=True,
    ):
        output.write(
            json.dumps(
                {
                    "confidence": float(confidence),
                    "evaluation": evaluation_name,
                    "manifest_sha256": dataset.manifest.sha256,
                    "model": model_key,
                    "prediction": prediction,
                    "probabilities": {
                        label: float(probability)
                        for label, probability in zip(known_labels, row_probabilities, strict=True)
                    },
                    "sample_id": sample_id,
                    "truth": truth,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )


def _json_safe(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def _peak_process_rss_bytes() -> int:
    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _total_system_memory_bytes() -> int | None:
    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        page_count = int(os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None
    total = page_size * page_count
    return total if total > 0 else None


def _cpu_model() -> str:
    candidates = [platform.processor(), platform.uname().processor]
    cpuinfo_path = Path("/proc/cpuinfo")
    if cpuinfo_path.is_file():
        try:
            for line in cpuinfo_path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith(("model name", "Hardware")) and ":" in line:
                    candidates.append(line.split(":", 1)[1].strip())
                    break
        except OSError:
            pass
    candidates.extend([platform.machine(), "unknown"])
    return next(value for value in candidates if str(value).strip())


def _gpu_capabilities() -> dict[str, object]:
    if importlib.util.find_spec("torch") is None:
        return {
            "available": False,
            "backend": None,
            "device_count": 0,
            "devices": [],
            "probe_error": None,
        }
    try:
        torch = importlib.import_module("torch")
        cuda = torch.cuda
        available = bool(cuda.is_available())
        device_count = int(cuda.device_count()) if available else 0
        devices = []
        for index in range(device_count):
            properties = cuda.get_device_properties(index)
            devices.append(
                {
                    "index": index,
                    "name": str(cuda.get_device_name(index)),
                    "total_memory_bytes": int(properties.total_memory),
                }
            )
        return {
            "available": available,
            "backend": "cuda" if available else None,
            "device_count": device_count,
            "devices": devices,
            "probe_error": None,
        }
    except Exception as error:
        return {
            "available": False,
            "backend": None,
            "device_count": 0,
            "devices": [],
            "probe_error": type(error).__name__,
        }


def detect_runtime_capabilities() -> dict[str, object]:
    """不依赖 nvidia-smi 地记录 CPU 运行选择与可选 GPU 能力。"""
    return {
        "selected_device": "cpu",
        "cpu": {
            "model": _cpu_model(),
            "architecture": platform.machine(),
            "logical_threads": os.cpu_count(),
            "execution_thread_limit": 1,
            "total_memory_bytes": _total_system_memory_bytes(),
        },
        "gpu": _gpu_capabilities(),
    }


def _execute_prepared_suite(
    *,
    prepared: PreparedTabularData,
    model_keys: Sequence[str],
    seed: int,
    predictions_path: Path | None,
    runtime_capabilities: Mapping[str, object] | None = None,
    stage: str = FINAL_TUNING_STAGE,
    tuning_trial_index: int = 0,
    fitted_models: Mapping[str, ProbabilisticClassifier] | None = None,
    model_state_output: MutableMapping[str, ProbabilisticClassifier] | None = None,
) -> TabularSuiteResult:
    keys = _normalise_model_keys(model_keys)
    if fitted_models is not None and set(fitted_models) != set(keys):
        raise TabularBaselineError("复用的已拟合模型必须与请求模型键完全一致")
    if fitted_models is not None and model_state_output is not None:
        raise TabularBaselineError("复用已拟合模型时不得再次捕获模型状态")
    validation_budget = _validation_budget(tuning_trial_index)
    runtime = dict(runtime_capabilities or detect_runtime_capabilities())
    model_results: dict[str, object] = {}
    model_costs: dict[str, object] = {}
    with ExitStack() as stack:
        prediction_output = None
        if predictions_path is not None:
            predictions_path = Path(predictions_path)
            predictions_path.parent.mkdir(parents=True, exist_ok=True)
            prediction_output = stack.enter_context(
                gzip.open(predictions_path, "xt", encoding="utf-8")
            )

        for model_key in keys:
            if fitted_models is None:
                model = _build_model(model_key, seed=seed, class_count=len(prepared.known_labels))
                fit_started = time.perf_counter()
                with threadpool_limits(limits=1):
                    model.fit(
                        prepared.train.features,
                        prepared.encoded_train_labels,
                        sample_weight=prepared.train_sample_weights,
                    )
                fit_seconds = time.perf_counter() - fit_started
                if model_state_output is not None:
                    model_state_output[model_key] = model
            else:
                model = fitted_models[model_key]
                fit_seconds = 0.0
            fitted_classes = tuple(int(value) for value in np.asarray(model.classes_).tolist())
            expected_classes = tuple(range(len(prepared.known_labels)))
            if fitted_classes != expected_classes:
                raise TabularBaselineError(
                    f"分类器标签顺序不一致：{fitted_classes} != {expected_classes}"
                )
            evaluations: dict[str, object] = {}
            evaluation_costs: dict[str, object] = {}
            for evaluation_name, dataset in prepared.evaluations.items():
                inference_started = time.perf_counter()
                with threadpool_limits(limits=1):
                    encoded_predictions = np.asarray(
                        model.predict(dataset.features), dtype=np.int64
                    )
                    probabilities = _normalise_probability_rows(
                        model.predict_proba(dataset.features),
                        sample_count=len(dataset.sample_ids),
                        class_count=len(prepared.known_labels),
                    )
                inference_seconds = time.perf_counter() - inference_started
                metrics, predictions, confidences = _evaluate(
                    dataset=dataset,
                    encoded_predictions=encoded_predictions,
                    probabilities=probabilities,
                    known_labels=prepared.known_labels,
                    inference_seconds=inference_seconds,
                )
                evaluations[evaluation_name] = {
                    "manifest": dataset.manifest.relative_path,
                    "manifest_sha256": dataset.manifest.sha256,
                    "sample_order_sha256": dataset.manifest.sample_order_sha256,
                    "metrics": metrics,
                }
                evaluation_costs[evaluation_name] = {
                    "sample_count": len(dataset.sample_ids),
                    "inference_seconds": inference_seconds,
                    "samples_per_second": len(dataset.sample_ids) / max(inference_seconds, 1e-12),
                }
                _write_predictions(
                    prediction_output,
                    model_key=model_key,
                    evaluation_name=evaluation_name,
                    dataset=dataset,
                    predictions=predictions,
                    confidences=confidences,
                    probabilities=probabilities,
                    known_labels=prepared.known_labels,
                )

            model_results[model_key] = {
                "parameters": _json_safe(model.get_params(deep=True)),
                "fit_seconds": fit_seconds,
                "reused_fitted_model": fitted_models is not None,
                "validation_trial_index": tuning_trial_index,
                "training_input": {
                    "manifest": prepared.train.manifest.relative_path,
                    "manifest_sha256": prepared.train.manifest.sha256,
                    "sample_order_sha256": prepared.train.manifest.sample_order_sha256,
                    "feature_matrix_sha256": prepared.feature_matrix_sha256,
                    "labels_sha256": prepared.train_labels_sha256,
                    "sample_weight_source": "train_manifest_only",
                },
                "evaluations": evaluations,
            }
            model_costs[model_key] = {
                "fit_seconds": fit_seconds,
                "train_sample_count": len(prepared.train.sample_ids),
                "execution_thread_limit": 1,
                "peak_process_rss_bytes_after_model": _peak_process_rss_bytes(),
                "peak_gpu_memory_bytes": None,
                "evaluations": evaluation_costs,
            }

    input_contract = {
        "protocol_version": prepared.protocol.protocol_version,
        "protocol_status": prepared.protocol.status,
        "protocol_phase": prepared.protocol.phase,
        "protocol_sha256": prepared.protocol.protocol_sha256,
        "samples_sha256": prepared.protocol.samples_sha256,
        "field_roles_sha256": prepared.protocol.field_roles_sha256,
        "suite_id": prepared.train.manifest.suite_id,
        "view_name": prepared.view_name,
        "feature_fields": list(prepared.train.feature_fields),
        "label_field": prepared.train.label_field,
        "known_labels": list(prepared.known_labels),
        "train_manifest_sha256": prepared.train.manifest.sha256,
        "train_sample_order_sha256": prepared.train.manifest.sample_order_sha256,
        "train_feature_matrix_sha256": prepared.feature_matrix_sha256,
        "train_labels_sha256": prepared.train_labels_sha256,
    }
    summary = {
        "schema_version": "flow_probe_tabular_baselines_v1",
        "seed": seed,
        "stage": stage,
        "validation_budget": validation_budget,
        "model_keys": list(keys),
        "runtime": runtime,
        "input_contract": input_contract,
        "train_sample_count": len(prepared.train.sample_ids),
        "train_label_distribution": dict(sorted(Counter(prepared.train.labels).items())),
        "models": model_results,
    }
    cost = {
        "schema_version": "flow_probe_tabular_cost_v1",
        "seed": seed,
        "stage": stage,
        "validation_budget": validation_budget,
        "runtime": runtime,
        "models": model_costs,
    }
    return TabularSuiteResult(summary=summary, cost=cost)


def run_tabular_baseline_suite(
    *,
    protocol_dir: Path,
    train_manifest: str | Path,
    evaluation_manifests: Mapping[str, str | Path],
    label_field: str,
    seed: int,
    model_keys: Sequence[str] = SUPPORTED_MODELS,
    view_name: str = TREE_VIEW_NAME,
    predictions_path: Path | None = None,
    stage: str = FINAL_TUNING_STAGE,
    expected_protocol_version: str = FROZEN_PROTOCOL_VERSION,
    tuning_trial_index: int = 0,
) -> TabularSuiteResult:
    """以相同输入、顺序、标签和评价函数运行所选树模型。"""
    _validation_budget(tuning_trial_index)
    prepared = prepare_tabular_data(
        protocol_dir=protocol_dir,
        train_manifest=train_manifest,
        evaluation_manifests=evaluation_manifests,
        label_field=label_field,
        view_name=view_name,
        stage=stage,
        expected_protocol_version=expected_protocol_version,
    )
    runtime = detect_runtime_capabilities()
    return _execute_prepared_suite(
        prepared=prepared,
        model_keys=model_keys,
        seed=seed,
        predictions_path=predictions_path,
        runtime_capabilities=runtime,
        stage=stage,
        tuning_trial_index=tuning_trial_index,
    )


def run_prepared_tabular_baseline_suite(
    *,
    prepared: PreparedTabularData,
    model_keys: Sequence[str],
    seed: int,
    predictions_path: Path | None = None,
    runtime_capabilities: Mapping[str, object] | None = None,
    stage: str = "prepared_external_data",
    tuning_trial_index: int = 0,
    fitted_models: Mapping[str, ProbabilisticClassifier] | None = None,
    model_state_output: MutableMapping[str, ProbabilisticClassifier] | None = None,
) -> TabularSuiteResult:
    """执行已经由外部适配器验证的共享树模型输入，不读取任何数据路径。"""
    return _execute_prepared_suite(
        prepared=prepared,
        model_keys=model_keys,
        seed=seed,
        predictions_path=predictions_path,
        runtime_capabilities=runtime_capabilities,
        stage=stage,
        tuning_trial_index=tuning_trial_index,
        fitted_models=fitted_models,
        model_state_output=model_state_output,
    )


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_tracked_tabular_baselines(
    *,
    protocol_dir: Path,
    train_manifest: str | Path,
    evaluation_manifests: Mapping[str, str | Path],
    label_field: str,
    output_dir: Path,
    seed: int,
    run_name: str,
    model_keys: Sequence[str] = SUPPORTED_MODELS,
    view_name: str = TREE_VIEW_NAME,
    stage: str = FINAL_TUNING_STAGE,
    expected_protocol_version: str = FROZEN_PROTOCOL_VERSION,
    tuning_trial_index: int = 0,
) -> dict[str, object]:
    """运行正式在线跟踪入口并保存全部基线制品。"""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise TabularBaselineError(f"运行目录已存在，不得复用：{output_dir}")
    keys = _normalise_model_keys(model_keys)
    validation_budget = _validation_budget(tuning_trial_index)
    if "xgboost" in keys:
        _import_xgboost()
    prepared = prepare_tabular_data(
        protocol_dir=protocol_dir,
        train_manifest=train_manifest,
        evaluation_manifests=evaluation_manifests,
        label_field=label_field,
        view_name=view_name,
        stage=stage,
        expected_protocol_version=expected_protocol_version,
    )
    runtime = detect_runtime_capabilities()

    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "冻结数据协议上的统一 HGB 与 XGBoost 恶意流量基线",
            "mode": "online",
            "tags": ["llm-probe", stage.replace("_", "-"), "tabular", "hgb-xgb"],
        }
    )
    config_path = output_dir / "config_snapshot.json"
    environment_path = output_dir / "environment.json"
    predictions_path = output_dir / "predictions.jsonl.gz"
    summary_path = output_dir / "summary.json"
    cost_path = output_dir / "cost.json"
    metrics_path = output_dir / "swanlab_metrics.json"
    metadata_path = output_dir / "swanlab_metadata.json"
    config: dict[str, object] = {
        "seed": seed,
        "stage": stage,
        "validation_budget": validation_budget,
        "model_keys": list(keys),
        "protocol_dir": str(prepared.protocol.root),
        "protocol_version": prepared.protocol.protocol_version,
        "protocol_status": prepared.protocol.status,
        "protocol_phase": prepared.protocol.phase,
        "protocol_sha256": prepared.protocol.protocol_sha256,
        "samples_sha256": prepared.protocol.samples_sha256,
        "field_roles_sha256": prepared.protocol.field_roles_sha256,
        "view_name": view_name,
        "feature_fields": list(prepared.train.feature_fields),
        "label_field": label_field,
        "train_manifest": {
            "path": prepared.train.manifest.relative_path,
            "sha256": prepared.train.manifest.sha256,
            "sample_order_sha256": prepared.train.manifest.sample_order_sha256,
        },
        "evaluation_manifests": {
            name: {
                "path": split.manifest.relative_path,
                "sha256": split.manifest.sha256,
                "sample_order_sha256": split.manifest.sample_order_sha256,
            }
            for name, split in prepared.evaluations.items()
        },
        "runtime": runtime,
    }
    metadata: dict[str, object] = {
        "workspace": settings.workspace,
        "project": settings.project,
        "phase": "tabular-baselines",
        "data_stage": stage,
        "validation_budget": validation_budget,
        "tracking_mode": settings.mode,
        "metric_prefix": "tabular",
        "tags": list(settings.tags),
        "runtime": runtime,
        "input_manifest_sha256": {
            "train": prepared.train.manifest.sha256,
            **{name: split.manifest.sha256 for name, split in prepared.evaluations.items()},
        },
    }
    data_files = {
        "config_snapshot": config_path,
        "environment": environment_path,
        "predictions": predictions_path,
        "summary": summary_path,
        "cost": cost_path,
        "swanlab_metrics": metrics_path,
        "swanlab_metadata": metadata_path,
    }

    with (
        capture_console_log(output_dir / "console.log"),
        swanlab_run(
            settings=settings,
            phase="tabular-baselines",
            config=config,
            artifact_dir=output_dir,
            data_files=data_files,
        ) as swanlab,
    ):
        _write_json(config_path, config)
        _write_json(
            environment_path,
            {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
                "pyarrow": _package_version("pyarrow"),
                "xgboost": _package_version("xgboost") if "xgboost" in keys else None,
                "runtime": runtime,
            },
        )
        _write_json(metadata_path, metadata)
        print(
            f"开始统一树模型基线：suite={prepared.train.manifest.suite_id}，"
            f"train={len(prepared.train.sample_ids)}，models={','.join(keys)}"
        )
        result = _execute_prepared_suite(
            prepared=prepared,
            model_keys=keys,
            seed=seed,
            predictions_path=predictions_path,
            runtime_capabilities=runtime,
            stage=stage,
            tuning_trial_index=tuning_trial_index,
        )
        _write_json(summary_path, result.summary)
        _write_json(cost_path, result.cost)
        scalar_metrics = {
            **flatten_scalar_metrics(result.summary, prefix="tabular"),
            **flatten_scalar_metrics(result.cost, prefix="cost"),
        }
        swanlab.log(scalar_metrics, step=0)
        _write_json(metrics_path, {"step": 0, "metrics": scalar_metrics})
        print("统一树模型基线完成，摘要、预测和成本制品已写入运行目录")

    manifest = json.loads((output_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    with capture_console_log(output_dir / "console.log"):
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行冻结协议上的统一 HGB/XGBoost 基线")
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--train-manifest", required=True)
    parser.add_argument("--evaluation", action="append", required=True)
    parser.add_argument("--label-field", required=True)
    parser.add_argument("--stage", choices=RUN_STAGES, default=FINAL_TUNING_STAGE)
    parser.add_argument("--expected-protocol-version", default=FROZEN_PROTOCOL_VERSION)
    parser.add_argument("--tuning-trial-index", type=int, default=0)
    parser.add_argument("--view-name", default=TREE_VIEW_NAME)
    parser.add_argument("--model", action="append", choices=SUPPORTED_MODELS)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-name", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_tracked_tabular_baselines(
        protocol_dir=args.protocol_dir,
        train_manifest=args.train_manifest,
        evaluation_manifests=parse_named_manifests(args.evaluation),
        label_field=args.label_field,
        stage=args.stage,
        expected_protocol_version=args.expected_protocol_version,
        tuning_trial_index=args.tuning_trial_index,
        output_dir=args.output_dir,
        seed=args.seed,
        run_name=args.run_name,
        model_keys=args.model or SUPPORTED_MODELS,
        view_name=args.view_name,
    )
