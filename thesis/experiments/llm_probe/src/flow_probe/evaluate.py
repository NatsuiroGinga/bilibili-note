"""生成式二分类探针的效果指标。"""

from __future__ import annotations

from collections.abc import Sequence

from flow_probe.schemas import BinaryLabel

LABELS = ("benign", "malicious")


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def compute_detection_metrics(
    labels: Sequence[BinaryLabel],
    predictions: Sequence[BinaryLabel | None],
    valid_mask: Sequence[bool],
) -> dict[str, float | int]:
    """计算二分类指标，并把非法生成按必然错误预测处理。"""
    if not (len(labels) == len(predictions) == len(valid_mask)):
        raise ValueError("labels、predictions 与 valid_mask 长度必须一致")
    if not labels:
        raise ValueError("指标输入不能为空")

    effective: list[BinaryLabel] = []
    actual_valid: list[bool] = []
    for label, prediction, marked_valid in zip(labels, predictions, valid_mask, strict=True):
        if label not in LABELS:
            raise ValueError(f"未知真实标签：{label!r}")
        is_valid = bool(marked_valid and prediction in LABELS)
        actual_valid.append(is_valid)
        if is_valid:
            effective.append(prediction)
        else:
            effective.append("malicious" if label == "benign" else "benign")

    class_metrics: dict[str, dict[str, float]] = {}
    for positive in LABELS:
        true_positive = sum(
            truth == positive and prediction == positive
            for truth, prediction in zip(labels, effective, strict=True)
        )
        false_positive = sum(
            truth != positive and prediction == positive
            for truth, prediction in zip(labels, effective, strict=True)
        )
        false_negative = sum(
            truth == positive and prediction != positive
            for truth, prediction in zip(labels, effective, strict=True)
        )
        precision = _safe_divide(true_positive, true_positive + false_positive)
        recall = _safe_divide(true_positive, true_positive + false_negative)
        f1 = _safe_divide(2 * precision * recall, precision + recall)
        class_metrics[positive] = {"precision": precision, "recall": recall, "f1": f1}

    benign_total = sum(label == "benign" for label in labels)
    false_positives = sum(
        truth == "benign" and prediction == "malicious"
        for truth, prediction in zip(labels, effective, strict=True)
    )
    invalid_count = len(actual_valid) - sum(actual_valid)
    return {
        "macro_f1": sum(class_metrics[label]["f1"] for label in LABELS) / len(LABELS),
        "benign_precision": class_metrics["benign"]["precision"],
        "benign_recall": class_metrics["benign"]["recall"],
        "benign_f1": class_metrics["benign"]["f1"],
        "malicious_precision": class_metrics["malicious"]["precision"],
        "malicious_recall": class_metrics["malicious"]["recall"],
        "malicious_f1": class_metrics["malicious"]["f1"],
        "false_positive_rate": _safe_divide(false_positives, benign_total),
        "json_valid_rate": _safe_divide(sum(actual_valid), len(actual_valid)),
        "invalid_output_count": invalid_count,
        "sample_count": len(labels),
    }
