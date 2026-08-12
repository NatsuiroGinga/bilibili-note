"""E2 困难域共同预算的二分类与捕获组指标。"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from sklearn.metrics import average_precision_score


class E2HardDomainMetricsError(ValueError):
    """E2 指标输入不满足二分类概率合同时抛出。"""


def _validate_inputs(
    labels: Sequence[int], probabilities: Sequence[float], capture_groups: Sequence[str]
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...]]:
    if not labels or len(labels) != len(probabilities) or len(labels) != len(capture_groups):
        raise E2HardDomainMetricsError("标签、概率和捕获组必须等长且非空")
    truth = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(probabilities, dtype=np.float64)
    groups = tuple(str(group) for group in capture_groups)
    if set(truth.tolist()).difference({0, 1}):
        raise E2HardDomainMetricsError("标签必须只包含 0 和 1")
    if not np.isfinite(scores).all() or np.any(scores < 0.0) or np.any(scores > 1.0):
        raise E2HardDomainMetricsError("恶意概率必须是 [0, 1] 内的有限数")
    if any(not group for group in groups):
        raise E2HardDomainMetricsError("捕获组不得为空")
    return truth, scores, groups


def _safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def _binary_metrics(
    truth: np.ndarray,
    scores: np.ndarray,
    *,
    threshold: float,
    calibration_bins: int,
) -> dict[str, int | float]:
    predicted = (scores >= threshold).astype(np.int64)
    true_positive = int(np.sum((truth == 1) & (predicted == 1)))
    true_negative = int(np.sum((truth == 0) & (predicted == 0)))
    false_positive = int(np.sum((truth == 0) & (predicted == 1)))
    false_negative = int(np.sum((truth == 1) & (predicted == 0)))
    malicious_precision = _safe_divide(true_positive, true_positive + false_positive)
    malicious_recall = _safe_divide(true_positive, true_positive + false_negative)
    benign_precision = _safe_divide(true_negative, true_negative + false_negative)
    benign_recall = _safe_divide(true_negative, true_negative + false_positive)
    malicious_f1 = _safe_divide(
        2.0 * malicious_precision * malicious_recall, malicious_precision + malicious_recall
    )
    benign_f1 = _safe_divide(2.0 * benign_precision * benign_recall, benign_precision + benign_recall)
    confidences = np.maximum(scores, 1.0 - scores)
    correctness = (truth == predicted).astype(np.float64)
    ece = 0.0
    edges = np.linspace(0.0, 1.0, calibration_bins + 1)
    for index in range(calibration_bins):
        lower, upper = edges[index], edges[index + 1]
        mask = (confidences >= lower) & (confidences <= upper)
        if index:
            mask = (confidences > lower) & (confidences <= upper)
        if np.any(mask):
            ece += float(np.mean(mask)) * abs(
                float(np.mean(correctness[mask])) - float(np.mean(confidences[mask]))
            )
    positives = int(np.sum(truth == 1))
    # 标准平均精度按唯一分数阈值聚合同分样本，不依赖同分样本的输入顺序。
    average_precision = (
        float(average_precision_score(truth, scores)) if positives else 0.0
    )
    mcc_denominator = math.sqrt(
        (true_positive + false_positive)
        * (true_positive + false_negative)
        * (true_negative + false_positive)
        * (true_negative + false_negative)
    )
    mcc = _safe_divide(
        true_positive * true_negative - false_positive * false_negative, mcc_denominator
    )
    thresholds = np.unique(scores)[::-1]
    tpr_at_limit = 0.0
    for candidate in thresholds:
        candidate_predicted = scores >= candidate
        candidate_fpr = _safe_divide(
            float(np.sum((truth == 0) & candidate_predicted)), float(np.sum(truth == 0))
        )
        if candidate_fpr <= 0.01:
            tpr_at_limit = max(
                tpr_at_limit,
                _safe_divide(
                    float(np.sum((truth == 1) & candidate_predicted)), float(np.sum(truth == 1))
                ),
            )
    clipped = np.clip(scores, 1e-15, 1.0 - 1e-15)
    return {
        "sample_count": int(len(truth)),
        "macro_f1": (benign_f1 + malicious_f1) / 2.0,
        "balanced_accuracy": (benign_recall + malicious_recall) / 2.0,
        "malicious_recall": malicious_recall,
        "benign_false_positive_rate": _safe_divide(
            false_positive, true_negative + false_positive
        ),
        "pr_auc": average_precision,
        "mcc": mcc,
        "expected_calibration_error": ece,
        "brier_score": float(np.mean(np.square(scores - truth))),
        "negative_log_likelihood": float(
            -np.mean(truth * np.log(clipped) + (1 - truth) * np.log(1.0 - clipped))
        ),
        "tpr_at_1pct_fpr": tpr_at_limit,
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def compute_e2_metrics(
    labels: Sequence[int],
    malicious_probabilities: Sequence[float],
    capture_groups: Sequence[str],
    *,
    threshold: float = 0.5,
    calibration_bins: int = 15,
) -> dict[str, object]:
    """计算 E2 统一指标及捕获组等权、最差组和逐组原始值。"""
    if not 0.0 <= threshold <= 1.0 or calibration_bins < 2:
        raise E2HardDomainMetricsError("阈值或校准分箱参数非法")
    truth, scores, groups = _validate_inputs(labels, malicious_probabilities, capture_groups)
    metrics: dict[str, object] = _binary_metrics(
        truth, scores, threshold=threshold, calibration_bins=calibration_bins
    )
    group_metrics: dict[str, dict[str, int | float]] = {}
    for group in sorted(set(groups)):
        mask = np.asarray([item == group for item in groups], dtype=bool)
        group_metrics[group] = _binary_metrics(
            truth[mask], scores[mask], threshold=threshold, calibration_bins=calibration_bins
        )
    group_macro_f1 = [values["macro_f1"] for values in group_metrics.values()]
    metrics["capture_group_equal_weighted_macro_f1"] = float(np.mean(group_macro_f1))
    metrics["worst_capture_group_macro_f1"] = float(np.min(group_macro_f1))
    metrics["capture_group_metrics"] = group_metrics
    return metrics
