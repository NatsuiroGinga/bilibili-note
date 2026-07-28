"""生成式多分类与开放集裁决的纯函数。"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass

from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, recall_score


@dataclass(frozen=True)
class ParsedLabelPrediction:
    """严格 JSON 生成结果。"""

    label: str | None
    is_valid: bool
    error: str | None


@dataclass(frozen=True)
class ThresholdCalibration:
    """只由域内验证置信度得到的未知拒识阈值。"""

    threshold: float
    validation_rejection_rate: float
    max_rejection_rate: float


def _validated_labels(allowed_labels: Sequence[str]) -> tuple[str, ...]:
    labels = tuple(str(label).strip() for label in allowed_labels)
    if not labels or any(not label for label in labels) or len(set(labels)) != len(labels):
        raise ValueError("候选标签必须非空且不能重复")
    return labels


def parse_label_prediction(text: str, allowed_labels: Sequence[str]) -> ParsedLabelPrediction:
    """只接受单键 JSON 和当前任务允许的字符串标签。"""
    labels = _validated_labels(allowed_labels)
    try:
        payload = json.loads(text.strip())
    except (AttributeError, json.JSONDecodeError, TypeError) as error:
        message = error.msg if hasattr(error, "msg") else str(error)
        return ParsedLabelPrediction(None, False, f"JSON 解析失败：{message}")
    if not isinstance(payload, dict):
        return ParsedLabelPrediction(None, False, "输出必须是 JSON 对象")
    if set(payload) != {"label"}:
        return ParsedLabelPrediction(None, False, "JSON 对象只能包含 label 键")
    label = payload["label"]
    if not isinstance(label, str) or label not in labels:
        return ParsedLabelPrediction(None, False, f"未知标签：{label!r}")
    return ParsedLabelPrediction(label, True, None)


def mean_candidate_log_probability(token_log_probabilities: Sequence[float]) -> float:
    """用令牌平均对数概率消除候选完成长度偏差。"""
    values = tuple(float(value) for value in token_log_probabilities)
    if not values:
        raise ValueError("候选完成的令牌对数概率不能为空")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("候选完成的令牌对数概率必须有限")
    return sum(values) / len(values)


def normalize_candidate_scores(
    score_rows: Sequence[Sequence[float]],
) -> list[tuple[float, ...]]:
    """对每个样本的候选平均对数似然执行数值稳定 softmax。"""
    rows = [tuple(float(value) for value in row) for row in score_rows]
    if not rows or not rows[0]:
        raise ValueError("候选分数矩阵不能为空")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("候选分数矩阵每行长度必须一致")
    if not all(math.isfinite(value) for row in rows for value in row):
        raise ValueError("候选分数必须是有限数值")
    normalized = []
    for row in rows:
        maximum = max(row)
        exponentials = tuple(math.exp(value - maximum) for value in row)
        denominator = sum(exponentials)
        normalized.append(tuple(value / denominator for value in exponentials))
    return normalized


def calibrate_unknown_threshold(
    confidences: Sequence[float], max_rejection_rate: float
) -> ThresholdCalibration:
    """使用较低分位数校准阈值，并保证验证拒识率不超过预算。"""
    if not 0 <= max_rejection_rate < 1:
        raise ValueError("最大已知类拒识率必须位于 [0, 1)")
    values = sorted(float(value) for value in confidences)
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("验证集置信度必须是有限非空序列")
    index = math.floor((len(values) - 1) * max_rejection_rate)
    threshold = values[index]
    rejection_rate = sum(value < threshold for value in values) / len(values)
    if rejection_rate > max_rejection_rate + 1e-12:
        raise AssertionError("验证集拒识率超过校准预算")
    return ThresholdCalibration(threshold, rejection_rate, max_rejection_rate)


def apply_unknown_rejection(
    predictions: Sequence[str],
    confidences: Sequence[float],
    threshold: float,
    unknown_label: str = "unknown_attack",
) -> list[str]:
    """置信度严格低于域内阈值时才拒识为未知攻击。"""
    if len(predictions) != len(confidences):
        raise ValueError("预测与置信度长度必须一致")
    if not math.isfinite(threshold):
        raise ValueError("拒识阈值必须是有限数值")
    values = tuple(float(value) for value in confidences)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("置信度必须是有限数值")
    if not unknown_label.strip():
        raise ValueError("未知标签不能为空")
    return [
        unknown_label if confidence < threshold else str(prediction)
        for prediction, confidence in zip(predictions, values, strict=True)
    ]


def compute_open_set_metrics(
    truth: Sequence[str],
    predictions: Sequence[str | None],
    known_labels: Sequence[str],
    unknown_label: str | None,
) -> dict[str, object]:
    """计算闭集或开放集指标，并把非法生成确定性映射为错误预测。"""
    labels = _validated_labels(known_labels)
    if "benign" not in labels:
        raise ValueError("候选标签必须包含 benign")
    if unknown_label is not None:
        unknown_label = unknown_label.strip()
        if not unknown_label or unknown_label in labels:
            raise ValueError("未知标签必须非空且不能属于已知标签")
    configured_labels = [*labels]
    if unknown_label is not None:
        configured_labels.append(unknown_label)
    if len(configured_labels) < 2:
        raise ValueError("指标至少需要两个配置标签")
    if len(truth) != len(predictions):
        raise ValueError("真实标签与预测长度必须一致")
    if not truth:
        raise ValueError("指标输入不能为空")

    configured_set = set(configured_labels)
    unknown_truth = [label for label in truth if label not in configured_set]
    if unknown_truth:
        raise ValueError(f"未知真实标签：{unknown_truth[0]!r}")

    valid_mask = [isinstance(value, str) and value in configured_set for value in predictions]
    effective: list[str] = []
    for actual, prediction, is_valid in zip(truth, predictions, valid_mask, strict=True):
        if is_valid:
            effective.append(str(prediction))
        elif actual == "benign":
            fallback = unknown_label or next(label for label in labels if label != "benign")
            effective.append(fallback)
        else:
            effective.append("benign")

    present_labels = [label for label in configured_labels if label in set(truth)]
    recalls = recall_score(
        truth,
        effective,
        labels=configured_labels,
        average=None,
        zero_division=0,
    )
    benign_total = sum(label == "benign" for label in truth)
    benign_false_positives = sum(
        actual == "benign" and prediction != "benign"
        for actual, prediction in zip(truth, effective, strict=True)
    )
    unknown_total = sum(label == unknown_label for label in truth) if unknown_label else 0
    known_total = sum(label in labels for label in truth)
    unknown_true_positives = (
        sum(
            actual == unknown_label and prediction == unknown_label
            for actual, prediction in zip(truth, effective, strict=True)
        )
        if unknown_label
        else 0
    )
    known_rejections = (
        sum(
            actual in labels and prediction == unknown_label
            for actual, prediction in zip(truth, effective, strict=True)
        )
        if unknown_label
        else 0
    )
    invalid_count = len(valid_mask) - sum(valid_mask)
    return {
        "accuracy": float(accuracy_score(truth, effective)),
        "macro_f1": float(
            f1_score(truth, effective, labels=present_labels, average="macro", zero_division=0)
        ),
        "configured_macro_f1": float(
            f1_score(
                truth,
                effective,
                labels=configured_labels,
                average="macro",
                zero_division=0,
            )
        ),
        "per_class_recall": {
            label: float(recall) for label, recall in zip(configured_labels, recalls, strict=True)
        },
        "benign_false_positive_rate": (
            benign_false_positives / benign_total if benign_total else 0.0
        ),
        "unknown_recall": (
            unknown_true_positives / unknown_total if unknown_label and unknown_total else None
        ),
        "known_rejection_rate": (
            known_rejections / known_total if unknown_label and known_total else None
        ),
        "json_valid_rate": sum(valid_mask) / len(valid_mask),
        "invalid_output_count": invalid_count,
        "sample_count": len(truth),
        "label_order": configured_labels,
        "confusion_matrix": confusion_matrix(truth, effective, labels=configured_labels).tolist(),
    }
