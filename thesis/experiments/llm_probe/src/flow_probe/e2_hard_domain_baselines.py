"""E2 困难域共同预算强基线的统一调度入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol, Sequence

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from flow_probe.e2_hard_domain_data import (
    E2_FEATURE_FIELDS,
    E2Panel,
    E2Sample,
    build_e2_panel,
    load_e2_development_view,
    samples_to_model_matrix,
)
from flow_probe.e2_hard_domain_metrics import compute_e2_metrics
from flow_probe.tabular_baselines import _build_model as build_existing_tabular_model

SUPPORTED_BASELINES = (
    "logreg",
    "random_forest",
    "hgb",
    "xgboost",
    "mlp",
    "distilbert",
    "groupdro",
)
DEFAULT_BASELINES = tuple(model for model in SUPPORTED_BASELINES if model != "distilbert")


class E2HardDomainBaselineError(ValueError):
    """E2 强基线配置、输入或输出不满足冻结合同时抛出。"""


class DistilBertAdapterRequiredError(E2HardDomainBaselineError):
    """请求普通 DistilBERT，但尚未显式注入 E2 适配器。"""


@dataclass(frozen=True)
class E2BaselineBudget:
    """所有基线共享的随机性、迭代和阈值预算。"""

    seed: int = 42
    max_iterations: int = 100
    threshold_source: str = "source_calibration"
    fixed_threshold: float = 0.5
    groupdro_step_size: float = 0.05
    groupdro_adversary_step_size: float = 0.1
    l2_penalty: float = 1e-4

    def validate(self) -> None:
        if self.max_iterations < 1:
            raise E2HardDomainBaselineError("共同预算 max_iterations 必须为正整数")
        if self.threshold_source not in {"fixed", "source_calibration"}:
            raise E2HardDomainBaselineError("阈值来源只允许 fixed 或 source_calibration")
        if not 0.0 <= self.fixed_threshold <= 1.0:
            raise E2HardDomainBaselineError("固定阈值必须位于 [0, 1]")
        if self.groupdro_step_size <= 0.0 or self.groupdro_adversary_step_size <= 0.0:
            raise E2HardDomainBaselineError("GroupDRO 步长必须为正数")
        if self.l2_penalty < 0.0:
            raise E2HardDomainBaselineError("L2 系数不得为负数")


@dataclass(frozen=True)
class E2TextSample:
    """只由共同七字段构造的 DistilBERT 文本样本。"""

    sample_id: str
    capture_id: str
    text: str
    label: int


class E2DistilBertPredictor(Protocol):
    """已完成源域拟合的普通 DistilBERT 预测器。"""

    def predict_malicious_probabilities(self, texts: Sequence[str]) -> Sequence[float]: ...


class E2DistilBertAdapter(Protocol):
    """普通 DistilBERT 的显式适配边界；拟合阶段不可接收 C 域样本。"""

    def fit_source_only(
        self,
        *,
        train: Sequence[E2TextSample],
        calibration: Sequence[E2TextSample],
        budget: E2BaselineBudget,
    ) -> E2DistilBertPredictor: ...


@dataclass(frozen=True)
class SharedB0DistilBertPredictor:
    """复用共享 B0 概率前向函数的 E2 已拟合模型桥接器。"""

    model: Any
    tokenizer: Any
    torch_module: Any
    device: str
    max_length: int
    batch_size: int = 64

    def predict_malicious_probabilities(self, texts: Sequence[str]) -> Sequence[float]:
        from flow_probe.shared_b0_distilbert_baseline import forward_probability_batch

        if self.batch_size < 1:
            raise E2HardDomainBaselineError("DistilBERT 评价批大小必须为正整数")
        probabilities: list[float] = []
        for start in range(0, len(texts), self.batch_size):
            probabilities.extend(
                forward_probability_batch(
                    model=self.model,
                    tokenizer=self.tokenizer,
                    texts=texts[start : start + self.batch_size],
                    device=self.device,
                    max_length=self.max_length,
                    torch_module=self.torch_module,
                )
            )
        return tuple(probabilities)


@dataclass(frozen=True)
class E2Prediction:
    """所有基线共享的逐样本预测格式。"""

    model: str
    evaluation: str
    sample_id: str
    capture_id: str
    profile: str
    stable_order: int
    label: int
    probability_malicious: float
    threshold: float
    prediction: int


@dataclass(frozen=True)
class E2BaselineResult:
    """单个基线的统一指标、逐样本预测和输入绑定。"""

    model: str
    threshold: float
    source_only_fit: bool
    input_binding_sha256: str
    metrics: Mapping[str, object]
    predictions: tuple[E2Prediction, ...]


@dataclass(frozen=True)
class E2BaselineSuiteResult:
    """共同面板上的一组强基线结果。"""

    panel: str
    budget: E2BaselineBudget
    input_binding_sha256: str
    results: Mapping[str, E2BaselineResult]


@dataclass(frozen=True)
class _SourcePreprocessor:
    imputer: SimpleImputer
    scaler: StandardScaler

    def transform(self, samples: Sequence[E2Sample]) -> np.ndarray:
        matrix = samples_to_model_matrix(samples)
        transformed = self.scaler.transform(self.imputer.transform(matrix))
        if not np.isfinite(transformed).all():
            raise E2HardDomainBaselineError("源域拟合的预处理产生了非有限值")
        return np.asarray(transformed, dtype=np.float64)


class SourceGroupDROClassifier:
    """仅用源域捕获组更新对抗组权重的二分类线性 GroupDRO。"""

    def __init__(
        self,
        *,
        max_iterations: int,
        step_size: float,
        adversary_step_size: float,
        l2_penalty: float,
    ) -> None:
        self.max_iterations = max_iterations
        self.step_size = step_size
        self.adversary_step_size = adversary_step_size
        self.l2_penalty = l2_penalty
        self.classes_ = np.asarray([0, 1], dtype=np.int64)
        self.coef_: np.ndarray | None = None
        self.intercept_: float | None = None
        self.group_weights_: Mapping[str, float] | None = None

    def fit(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        *,
        groups: Sequence[str],
        sample_weight: np.ndarray,
    ) -> "SourceGroupDROClassifier":
        if features.ndim != 2 or len(features) == 0 or len(features) != len(labels):
            raise E2HardDomainBaselineError("GroupDRO 训练矩阵形状非法")
        group_values = np.asarray(tuple(str(group) for group in groups), dtype=object)
        unique_groups = tuple(sorted(set(group_values.tolist())))
        if len(group_values) != len(labels) or any(not group for group in unique_groups):
            raise E2HardDomainBaselineError("GroupDRO 源域捕获组必须与训练样本等长且非空")
        if set(np.asarray(labels, dtype=np.int64).tolist()) != {0, 1}:
            raise E2HardDomainBaselineError("GroupDRO 源域训练必须同时包含良性与恶意样本")
        weights = np.zeros(features.shape[1], dtype=np.float64)
        intercept = 0.0
        adversary = np.full(len(unique_groups), 1.0 / len(unique_groups), dtype=np.float64)
        labels_float = np.asarray(labels, dtype=np.float64)
        base_weights = np.asarray(sample_weight, dtype=np.float64)
        masks = tuple(group_values == group for group in unique_groups)
        for _ in range(self.max_iterations):
            logits = np.clip(features @ weights + intercept, -40.0, 40.0)
            probabilities = 1.0 / (1.0 + np.exp(-logits))
            losses = np.logaddexp(0.0, logits) - labels_float * logits
            group_losses = np.asarray(
                [float(np.average(losses[mask], weights=base_weights[mask])) for mask in masks]
            )
            adversary *= np.exp(
                self.adversary_step_size * (group_losses - float(np.max(group_losses)))
            )
            adversary /= float(np.sum(adversary))
            effective = np.zeros(len(labels), dtype=np.float64)
            for group_index, mask in enumerate(masks):
                normalizer = float(np.sum(base_weights[mask]))
                effective[mask] = adversary[group_index] * base_weights[mask] / normalizer
            residual = probabilities - labels_float
            gradient = features.T @ (effective * residual) + self.l2_penalty * weights
            intercept_gradient = float(np.sum(effective * residual))
            weights -= self.step_size * gradient
            intercept -= self.step_size * intercept_gradient
        self.coef_ = weights
        self.intercept_ = intercept
        self.group_weights_ = MappingProxyType(
            {group: float(adversary[index]) for index, group in enumerate(unique_groups)}
        )
        return self

    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        if self.coef_ is None or self.intercept_ is None:
            raise E2HardDomainBaselineError("GroupDRO 尚未拟合")
        logits = np.clip(features @ self.coef_ + self.intercept_, -40.0, 40.0)
        malicious = 1.0 / (1.0 + np.exp(-logits))
        return np.column_stack((1.0 - malicious, malicious))


def format_e2_text(sample: E2Sample) -> str:
    """仅按固定顺序把共同七字段序列化为普通 DistilBERT 输入。"""
    return " ".join(
        f"{field}={format(value, '.12g')}"
        for field, value in zip(E2_FEATURE_FIELDS, sample.features, strict=True)
    )


def _text_samples(samples: Sequence[E2Sample]) -> tuple[E2TextSample, ...]:
    return tuple(
        E2TextSample(
            sample_id=sample.sample_id,
            capture_id=sample.capture_id,
            text=format_e2_text(sample),
            label=sample.label,
        )
        for sample in samples
    )


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_input_binding(panel: E2Panel) -> dict[str, object]:
    """生成复用 E1 结果时必须逐项相等的输入绑定。"""
    return {
        "schema_version": "flow_probe_e2_baseline_input_binding_v1",
        "panel": panel.panel,
        "feature_fields": list(E2_FEATURE_FIELDS),
        "train_sample_order_sha256": _canonical_sha256(
            [sample.sample_id for sample in panel.train]
        ),
        "calibration_sample_order_sha256": _canonical_sha256(
            [sample.sample_id for sample in panel.calibration]
        ),
        "target_sample_order_sha256": _canonical_sha256(
            [sample.sample_id for sample in panel.target]
        ),
        "train_features_sha256": _canonical_sha256(
            [list(sample.features) for sample in panel.train]
        ),
        "train_labels_sha256": _canonical_sha256([sample.label for sample in panel.train]),
        "calibration_features_sha256": _canonical_sha256(
            [list(sample.features) for sample in panel.calibration]
        ),
        "calibration_labels_sha256": _canonical_sha256(
            [sample.label for sample in panel.calibration]
        ),
        "target_features_sha256": _canonical_sha256(
            [list(sample.features) for sample in panel.target]
        ),
        "target_labels_sha256": _canonical_sha256([sample.label for sample in panel.target]),
    }


def validate_e1_reuse_receipt(
    receipt: Mapping[str, object],
    *,
    expected_model: str,
    expected_input_binding: Mapping[str, object],
    expected_budget: E2BaselineBudget,
) -> None:
    """只允许字段、划分、数据哈希和配置完全相等的 E1 HGB/XGBoost 复用。"""
    if expected_model not in {"hgb", "xgboost"}:
        raise E2HardDomainBaselineError("E1 复用只适用于 HGB 或 XGBoost")
    expected = {
        "model": expected_model,
        "input_binding": dict(expected_input_binding),
        "budget": asdict(expected_budget),
    }
    actual = {key: receipt.get(key) for key in expected}
    if actual != expected:
        raise E2HardDomainBaselineError("E1 结果的数据哈希、字段、划分或配置不一致，必须重跑")


def _validate_panel(panel: E2Panel) -> None:
    if not panel.train or not panel.target:
        raise E2HardDomainBaselineError("E2 面板训练集和 C 目标集不得为空")
    if any(sample.profile == "C" for sample in (*panel.train, *panel.calibration)):
        raise E2HardDomainBaselineError("源域拟合输入不得包含 C 目标域")
    if any(sample.profile != "C" for sample in panel.target):
        raise E2HardDomainBaselineError("目标评价输入必须全部来自 C 域")
    all_samples = (*panel.train, *panel.calibration, *panel.target)
    sample_ids = [sample.sample_id for sample in all_samples]
    if len(sample_ids) != len(set(sample_ids)):
        raise E2HardDomainBaselineError("E2 面板源域与目标域样本必须互斥")


def _fit_source_preprocessor(train: Sequence[E2Sample]) -> _SourcePreprocessor:
    matrix = samples_to_model_matrix(train)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    scaler.fit(imputer.fit_transform(matrix))
    return _SourcePreprocessor(imputer=imputer, scaler=scaler)


def _labels(samples: Sequence[E2Sample]) -> np.ndarray:
    return np.asarray([sample.label for sample in samples], dtype=np.int64)


def _normalise_probabilities(values: Sequence[float], expected_count: int) -> np.ndarray:
    probabilities = np.asarray(values, dtype=np.float64)
    if probabilities.shape != (expected_count,):
        raise E2HardDomainBaselineError("恶意概率数量与样本数不一致")
    if not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1)):
        raise E2HardDomainBaselineError("模型输出了 [0, 1] 之外的恶意概率")
    return probabilities


def _macro_f1(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> float:
    predictions = probabilities >= threshold
    scores: list[float] = []
    for label in (0, 1):
        true_positive = int(np.sum((labels == label) & (predictions == label)))
        false_positive = int(np.sum((labels != label) & (predictions == label)))
        false_negative = int(np.sum((labels == label) & (predictions != label)))
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(2 * true_positive / denominator if denominator else 0.0)
    return float(np.mean(scores))


def _select_threshold(
    budget: E2BaselineBudget,
    calibration: Sequence[E2Sample],
    probabilities: np.ndarray,
) -> float:
    if budget.threshold_source == "fixed" or not calibration:
        return budget.fixed_threshold
    labels = _labels(calibration)
    candidates = sorted(set(probabilities.tolist()) | {budget.fixed_threshold})
    return max(
        candidates,
        key=lambda threshold: (
            _macro_f1(labels, probabilities, threshold),
            -abs(threshold - budget.fixed_threshold),
            -threshold,
        ),
    )


def _build_sklearn_model(model: str, budget: E2BaselineBudget) -> object:
    if model == "logreg":
        return LogisticRegression(max_iter=budget.max_iterations, random_state=budget.seed)
    if model == "random_forest":
        return RandomForestClassifier(
            n_estimators=budget.max_iterations,
            random_state=budget.seed,
            n_jobs=1,
        )
    if model in {"hgb", "xgboost"}:
        # 复用旧统一表格入口的冻结模型构造，不复制其训练逻辑。
        estimator = build_existing_tabular_model(model, seed=budget.seed, class_count=2)
        iteration_parameter = "max_iter" if model == "hgb" else "n_estimators"
        estimator.set_params(**{iteration_parameter: budget.max_iterations})
        return estimator
    if model == "mlp":
        return MLPClassifier(
            hidden_layer_sizes=(64, 32),
            max_iter=budget.max_iterations,
            early_stopping=True,
            random_state=budget.seed,
        )
    raise E2HardDomainBaselineError(f"不支持的表格基线：{model}")


def _fit_tabular_source_only(
    model_name: str,
    panel: E2Panel,
    budget: E2BaselineBudget,
) -> tuple[np.ndarray, np.ndarray]:
    preprocessor = _fit_source_preprocessor(panel.train)
    train_features = preprocessor.transform(panel.train)
    train_labels = _labels(panel.train)
    if set(train_labels.tolist()) != {0, 1}:
        raise E2HardDomainBaselineError("源域训练必须同时包含良性与恶意样本")
    sample_weights = np.asarray(compute_sample_weight("balanced", train_labels), dtype=np.float64)
    if model_name == "groupdro":
        model = SourceGroupDROClassifier(
            max_iterations=budget.max_iterations,
            step_size=budget.groupdro_step_size,
            adversary_step_size=budget.groupdro_adversary_step_size,
            l2_penalty=budget.l2_penalty,
        )
        model.fit(
            train_features,
            train_labels,
            groups=[sample.capture_id for sample in panel.train],
            sample_weight=sample_weights,
        )
    else:
        model = _build_sklearn_model(model_name, budget)
        with threadpool_limits(limits=1):
            if model_name == "mlp":
                model.fit(train_features, train_labels)
            else:
                model.fit(train_features, train_labels, sample_weight=sample_weights)
    calibration_features = (
        preprocessor.transform(panel.calibration)
        if panel.calibration
        else np.empty((0, len(E2_FEATURE_FIELDS)), dtype=np.float64)
    )
    calibration_probabilities = (
        _normalise_probabilities(
            model.predict_proba(calibration_features)[:, 1], len(panel.calibration)
        )
        if panel.calibration
        else np.empty(0, dtype=np.float64)
    )
    target_probabilities = _normalise_probabilities(
        model.predict_proba(preprocessor.transform(panel.target))[:, 1], len(panel.target)
    )
    return calibration_probabilities, target_probabilities


def _fit_distilbert_source_only(
    panel: E2Panel,
    budget: E2BaselineBudget,
    adapter: E2DistilBertAdapter,
) -> tuple[np.ndarray, np.ndarray]:
    predictor = adapter.fit_source_only(
        train=_text_samples(panel.train),
        calibration=_text_samples(panel.calibration),
        budget=budget,
    )
    calibration_probabilities = (
        _normalise_probabilities(
            predictor.predict_malicious_probabilities(
                [format_e2_text(sample) for sample in panel.calibration]
            ),
            len(panel.calibration),
        )
        if panel.calibration
        else np.empty(0, dtype=np.float64)
    )
    target_probabilities = _normalise_probabilities(
        predictor.predict_malicious_probabilities(
            [format_e2_text(sample) for sample in panel.target]
        ),
        len(panel.target),
    )
    return calibration_probabilities, target_probabilities


def _prediction_rows(
    *,
    model: str,
    evaluation: str,
    samples: Sequence[E2Sample],
    probabilities: np.ndarray,
    threshold: float,
) -> tuple[E2Prediction, ...]:
    return tuple(
        E2Prediction(
            model=model,
            evaluation=evaluation,
            sample_id=sample.sample_id,
            capture_id=sample.capture_id,
            profile=sample.profile,
            stable_order=sample.stable_order,
            label=sample.label,
            probability_malicious=float(probability),
            threshold=threshold,
            prediction=int(probability >= threshold),
        )
        for sample, probability in zip(samples, probabilities, strict=True)
    )


def run_e2_baseline_suite(
    panel: E2Panel,
    *,
    models: Sequence[str] = DEFAULT_BASELINES,
    budget: E2BaselineBudget = E2BaselineBudget(),
    distilbert_adapter: E2DistilBertAdapter | None = None,
) -> E2BaselineSuiteResult:
    """在同一面板上拟合基线，并只在模型冻结后评价 C 域。"""
    budget.validate()
    _validate_panel(panel)
    model_keys = tuple(str(model).strip() for model in models)
    if not model_keys or len(model_keys) != len(set(model_keys)):
        raise E2HardDomainBaselineError("基线列表不得为空或重复")
    unsupported = sorted(set(model_keys).difference(SUPPORTED_BASELINES))
    if unsupported:
        raise E2HardDomainBaselineError(f"不支持的基线：{', '.join(unsupported)}")
    if "distilbert" in model_keys and distilbert_adapter is None:
        raise DistilBertAdapterRequiredError(
            "普通 DistilBERT 尚未配置 E2 源域适配器；拒绝调用旧 GeNIS/TQH 训练入口"
        )
    input_binding = build_input_binding(panel)
    input_binding_sha256 = _canonical_sha256(input_binding)
    results: dict[str, E2BaselineResult] = {}
    for model in model_keys:
        if model == "distilbert":
            assert distilbert_adapter is not None
            calibration_probabilities, target_probabilities = _fit_distilbert_source_only(
                panel, budget, distilbert_adapter
            )
        else:
            calibration_probabilities, target_probabilities = _fit_tabular_source_only(
                model, panel, budget
            )
        threshold = _select_threshold(budget, panel.calibration, calibration_probabilities)
        predictions = _prediction_rows(
            model=model,
            evaluation="target_c",
            samples=panel.target,
            probabilities=target_probabilities,
            threshold=threshold,
        )
        metrics = compute_e2_metrics(
            [sample.label for sample in panel.target],
            target_probabilities.tolist(),
            [sample.capture_id for sample in panel.target],
            threshold=threshold,
        )
        results[model] = E2BaselineResult(
            model=model,
            threshold=threshold,
            source_only_fit=True,
            input_binding_sha256=input_binding_sha256,
            metrics=MappingProxyType(metrics),
            predictions=predictions,
        )
    return E2BaselineSuiteResult(
        panel=panel.panel,
        budget=budget,
        input_binding_sha256=input_binding_sha256,
        results=MappingProxyType(results),
    )


def _write_suite(output_dir: Path, suite: E2BaselineSuiteResult) -> None:
    if output_dir.exists():
        raise E2HardDomainBaselineError(f"输出目录已存在，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True)
    summary = {
        "schema_version": "flow_probe_e2_hard_domain_baselines_v1",
        "panel": suite.panel,
        "budget": asdict(suite.budget),
        "input_binding_sha256": suite.input_binding_sha256,
        "models": {
            model: {
                "threshold": result.threshold,
                "source_only_fit": result.source_only_fit,
                "metrics": dict(result.metrics),
            }
            for model, result in suite.results.items()
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    rows = [
        json.dumps(asdict(prediction), ensure_ascii=False, sort_keys=True)
        for result in suite.results.values()
        for prediction in result.predictions
    ]
    (output_dir / "predictions.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 E2 困难域共同预算强基线")
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--panel", choices=("abd_to_c", "ab_to_c"), required=True)
    parser.add_argument("--model", action="append", choices=SUPPORTED_BASELINES)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument(
        "--threshold-source",
        choices=("fixed", "source_calibration"),
        default="source_calibration",
    )
    parser.add_argument(
        "--distilbert-model-source",
        default="/root/autodl-tmp/thesis/models/distilbert-base-multilingual-cased",
    )
    parser.add_argument(
        "--distilbert-model-binding-sha256",
        default="",
        help="预注册的 DistilBERT 基础模型制品绑定摘要",
    )
    parser.add_argument("--distilbert-device", choices=("auto", "cuda", "cpu"), default="auto")
    parser.add_argument(
        "--distilbert-precision",
        choices=("auto", "float32", "float16", "bfloat16"),
        default="auto",
    )
    parser.add_argument("--distilbert-train-batch-size", type=int, default=16)
    parser.add_argument("--distilbert-eval-batch-size", type=int, default=64)
    parser.add_argument("--distilbert-gradient-accumulation-steps", type=int, default=2)
    parser.add_argument("--distilbert-max-length", type=int, default=128)
    parser.add_argument("--distilbert-learning-rate", type=float, default=2e-5)
    parser.add_argument("--distilbert-weight-decay", type=float, default=0.01)
    parser.add_argument("--distilbert-num-train-epochs", type=int, default=3)
    parser.add_argument("--distilbert-warmup-ratio", type=float, default=0.1)
    parser.add_argument("--distilbert-max-grad-norm", type=float, default=1.0)
    parser.add_argument("--distilbert-num-workers", type=int, default=0)
    parser.add_argument("--distilbert-early-stopping-patience", type=int, default=2)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        samples = load_e2_development_view(args.protocol_dir)
        panel = build_e2_panel(samples, panel=args.panel)
        budget = E2BaselineBudget(
            seed=args.seed,
            max_iterations=args.max_iterations,
            threshold_source=args.threshold_source,
        )
        model_keys = tuple(args.model or DEFAULT_BASELINES)
        distilbert_adapter = None
        if "distilbert" in model_keys:
            from flow_probe.e2_distilbert import (
                E2DistilBertTrainingAdapter,
                E2DistilBertTrainingSettings,
            )

            distilbert_adapter = E2DistilBertTrainingAdapter(
                E2DistilBertTrainingSettings(
                    model_source=args.distilbert_model_source,
                    expected_model_binding_sha256=args.distilbert_model_binding_sha256,
                    device=args.distilbert_device,
                    precision=args.distilbert_precision,
                    per_device_train_batch_size=args.distilbert_train_batch_size,
                    per_device_eval_batch_size=args.distilbert_eval_batch_size,
                    gradient_accumulation_steps=args.distilbert_gradient_accumulation_steps,
                    max_length=args.distilbert_max_length,
                    learning_rate=args.distilbert_learning_rate,
                    weight_decay=args.distilbert_weight_decay,
                    num_train_epochs=args.distilbert_num_train_epochs,
                    warmup_ratio=args.distilbert_warmup_ratio,
                    max_grad_norm=args.distilbert_max_grad_norm,
                    num_workers=args.distilbert_num_workers,
                    early_stopping_patience=args.distilbert_early_stopping_patience,
                )
            )
        suite = run_e2_baseline_suite(
            panel,
            models=model_keys,
            budget=budget,
            distilbert_adapter=distilbert_adapter,
        )
        _write_suite(args.output_dir, suite)
        if (
            distilbert_adapter is not None
            and distilbert_adapter.last_training_summary is not None
        ):
            (args.output_dir / "distilbert_training.json").write_text(
                json.dumps(
                    dict(distilbert_adapter.last_training_summary),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        print(
            json.dumps(
                {
                    "status": "finished",
                    "output_dir": str(args.output_dir),
                    "models": list(suite.results),
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except E2HardDomainBaselineError as error:
        print(
            json.dumps({"status": "failed", "reason": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
