"""对 S3/S4 同协议检测结果执行只读比较与配对统计。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import sys
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path


DOMAIN_SPLITS = ("family_test", "subtype_validation", "subtype_test")
PRIMARY_SPLITS = ("family_test", "subtype_test")
OOD_SPLITS = ("ood_dos_udp", "ood_dos_icmp", "ood_dos_pushack")
CALIBRATION_SPLITS = ("family_test", "subtype_validation", "subtype_test")
UNKNOWN_LABEL = "unknown_attack"


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON 顶层必须是对象：{path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL 第 {line_number} 行不是对象：{path}")
            rows.append(payload)
    if not rows:
        raise ValueError(f"预测文件为空：{path}")
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _nested(mapping: Mapping[str, object], *keys: str) -> object:
    current: object = mapping
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            raise KeyError(".".join(keys))
        current = current[key]
    return current


def _paired_rows(
    s3_path: Path,
    s4_path: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    s3_rows = _read_jsonl(s3_path)
    s4_rows = _read_jsonl(s4_path)
    if len(s3_rows) != len(s4_rows):
        raise ValueError(f"配对预测数量不一致：{s3_path} 与 {s4_path}")
    for index, (s3_row, s4_row) in enumerate(zip(s3_rows, s4_rows, strict=True)):
        s3_key = (s3_row.get("sample_id"), s3_row.get("true_label"))
        s4_key = (s4_row.get("sample_id"), s4_row.get("true_label"))
        if s3_key != s4_key:
            raise ValueError(f"第 {index} 个配对样本不一致：{s3_key!r} != {s4_key!r}")
    return s3_rows, s4_rows


def _label_order(rows: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    labels = sorted({str(row["true_label"]) for row in rows})
    if "benign" in labels:
        labels.remove("benign")
        labels.insert(0, "benign")
    return tuple(labels)


def _macro_f1(
    truth: Sequence[str],
    predictions: Sequence[str | None],
    labels: Sequence[str],
) -> float:
    scores = []
    for label in labels:
        true_positive = sum(
            actual == label and predicted == label
            for actual, predicted in zip(truth, predictions, strict=True)
        )
        false_positive = sum(
            actual != label and predicted == label
            for actual, predicted in zip(truth, predictions, strict=True)
        )
        false_negative = sum(
            actual == label and predicted != label
            for actual, predicted in zip(truth, predictions, strict=True)
        )
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(2 * true_positive / denominator if denominator else 0.0)
    return sum(scores) / len(scores)


def _rate(
    truth: Sequence[str],
    predictions: Sequence[str | None],
    condition: Callable[[str, str | None], bool],
    denominator: Callable[[str], bool],
) -> float:
    eligible = sum(denominator(actual) for actual in truth)
    if not eligible:
        return 0.0
    return (
        sum(
            condition(actual, predicted)
            for actual, predicted in zip(truth, predictions, strict=True)
            if denominator(actual)
        )
        / eligible
    )


def _stratified_indices(truth: Sequence[str], rng: random.Random) -> list[int]:
    groups: dict[str, list[int]] = defaultdict(list)
    for index, label in enumerate(truth):
        groups[label].append(index)
    sampled: list[int] = []
    for label in sorted(groups):
        indices = groups[label]
        sampled.extend(rng.choice(indices) for _ in indices)
    return sampled


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _bootstrap_delta(
    truth: Sequence[str],
    s3_predictions: Sequence[str | None],
    s4_predictions: Sequence[str | None],
    metric: Callable[[Sequence[str], Sequence[str | None]], float],
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    point = metric(truth, s4_predictions) - metric(truth, s3_predictions)
    rng = random.Random(seed)
    deltas = []
    for _ in range(repetitions):
        indices = _stratified_indices(truth, rng)
        sampled_truth = [truth[index] for index in indices]
        sampled_s3 = [s3_predictions[index] for index in indices]
        sampled_s4 = [s4_predictions[index] for index in indices]
        deltas.append(metric(sampled_truth, sampled_s4) - metric(sampled_truth, sampled_s3))
    return {
        "point_delta": point,
        "ci95": [_quantile(deltas, 0.025), _quantile(deltas, 0.975)],
        "repetitions": repetitions,
        "seed": seed,
    }


def _calibration(rows: Sequence[Mapping[str, object]], bins: int = 15) -> dict[str, float]:
    bucket_confidences: list[list[float]] = [[] for _ in range(bins)]
    bucket_correctness: list[list[float]] = [[] for _ in range(bins)]
    brier_values = []
    negative_log_likelihoods = []
    for row in rows:
        probabilities = row.get("candidate_probabilities")
        if not isinstance(probabilities, Mapping):
            raise ValueError("候选预测缺少 candidate_probabilities")
        true_label = str(row["true_label"])
        if true_label not in probabilities:
            raise ValueError(f"真实标签不属于候选类，不能计算校准：{true_label}")
        numeric = {str(label): float(value) for label, value in probabilities.items()}
        confidence = max(numeric.values())
        prediction = str(row["raw_prediction"])
        bucket = min(int(confidence * bins), bins - 1)
        bucket_confidences[bucket].append(confidence)
        bucket_correctness[bucket].append(float(prediction == true_label))
        brier_values.append(
            sum(
                (probability - float(label == true_label)) ** 2
                for label, probability in numeric.items()
            )
        )
        negative_log_likelihoods.append(-math.log(max(numeric[true_label], 1e-12)))

    sample_count = len(rows)
    expected_calibration_error = 0.0
    for confidences, correctness in zip(bucket_confidences, bucket_correctness, strict=True):
        if not confidences:
            continue
        expected_calibration_error += (
            len(confidences)
            / sample_count
            * abs(sum(correctness) / len(correctness) - sum(confidences) / len(confidences))
        )
    return {
        "expected_calibration_error": expected_calibration_error,
        "brier_score": sum(brier_values) / sample_count,
        "negative_log_likelihood": sum(negative_log_likelihoods) / sample_count,
        "sample_count": float(sample_count),
    }


def _prediction_values(
    rows: Sequence[Mapping[str, object]], field: str
) -> tuple[list[str], list[str | None]]:
    truth = [str(row["true_label"]) for row in rows]
    predictions = [None if row.get(field) is None else str(row[field]) for row in rows]
    return truth, predictions


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _open_set_bootstrap(
    paired_ood: Mapping[str, tuple[list[dict[str, object]], list[dict[str, object]]]],
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    point_unknown = []
    point_false_positive = []
    prepared: dict[str, tuple[list[str], list[str | None], list[str | None]]] = {}
    for split, (s3_rows, s4_rows) in paired_ood.items():
        truth, s3_predictions = _prediction_values(s3_rows, "prediction")
        _, s4_predictions = _prediction_values(s4_rows, "prediction")
        prepared[split] = (truth, s3_predictions, s4_predictions)
        unknown_metric = lambda actual, predicted: _rate(  # noqa: E731
            actual,
            predicted,
            lambda label, guess: label == UNKNOWN_LABEL and guess == UNKNOWN_LABEL,
            lambda label: label == UNKNOWN_LABEL,
        )
        benign_metric = lambda actual, predicted: _rate(  # noqa: E731
            actual,
            predicted,
            lambda label, guess: label == "benign" and guess != "benign",
            lambda label: label == "benign",
        )
        point_unknown.append(
            unknown_metric(truth, s4_predictions) - unknown_metric(truth, s3_predictions)
        )
        point_false_positive.append(
            benign_metric(truth, s4_predictions) - benign_metric(truth, s3_predictions)
        )

    rng = random.Random(seed)
    unknown_deltas = []
    false_positive_deltas = []
    for _ in range(repetitions):
        split_unknown = []
        split_false_positive = []
        for truth, s3_predictions, s4_predictions in prepared.values():
            indices = _stratified_indices(truth, rng)
            sampled_truth = [truth[index] for index in indices]
            sampled_s3 = [s3_predictions[index] for index in indices]
            sampled_s4 = [s4_predictions[index] for index in indices]
            split_unknown.append(
                _rate(
                    sampled_truth,
                    sampled_s4,
                    lambda label, guess: label == UNKNOWN_LABEL and guess == UNKNOWN_LABEL,
                    lambda label: label == UNKNOWN_LABEL,
                )
                - _rate(
                    sampled_truth,
                    sampled_s3,
                    lambda label, guess: label == UNKNOWN_LABEL and guess == UNKNOWN_LABEL,
                    lambda label: label == UNKNOWN_LABEL,
                )
            )
            split_false_positive.append(
                _rate(
                    sampled_truth,
                    sampled_s4,
                    lambda label, guess: label == "benign" and guess != "benign",
                    lambda label: label == "benign",
                )
                - _rate(
                    sampled_truth,
                    sampled_s3,
                    lambda label, guess: label == "benign" and guess != "benign",
                    lambda label: label == "benign",
                )
            )
        unknown_deltas.append(_mean(split_unknown))
        false_positive_deltas.append(_mean(split_false_positive))
    return {
        "unknown_recall_mean_delta": {
            "point_delta": _mean(point_unknown),
            "ci95": [_quantile(unknown_deltas, 0.025), _quantile(unknown_deltas, 0.975)],
        },
        "benign_false_positive_rate_mean_delta": {
            "point_delta": _mean(point_false_positive),
            "ci95": [
                _quantile(false_positive_deltas, 0.025),
                _quantile(false_positive_deltas, 0.975),
            ],
        },
        "repetitions": repetitions,
        "seed": seed,
    }


def _summary_metric(summary: Mapping[str, object], split: str, mode: str, metric: str) -> float:
    return float(_nested(summary, "results", split, mode, "metrics", metric))


def _percent_improvement(reference: float, candidate: float) -> float:
    return (reference - candidate) / reference


def analyze(
    s3_output: Path,
    s4_output: Path,
    s3_training: Path,
    s4_training: Path,
    output: Path,
    repetitions: int,
    seed: int,
) -> dict[str, object]:
    if output.exists():
        raise ValueError(f"输出目录已存在，拒绝复用：{output}")
    output.mkdir(parents=True)
    s3_summary_path = s3_output / "evaluation_summary.json"
    s4_summary_path = s4_output / "evaluation_summary.json"
    s3_summary = _read_json(s3_summary_path)
    s4_summary = _read_json(s4_summary_path)
    s3_training_summary = _read_json(s3_training / "training_summary.json")
    s4_training_summary = _read_json(s4_training / "training_summary.json")

    paired: dict[str, dict[str, tuple[list[dict[str, object]], list[dict[str, object]]]]] = {
        "free": {},
        "candidate": {},
    }
    input_paths = [
        s3_summary_path,
        s4_summary_path,
        s3_training / "training_summary.json",
        s4_training / "training_summary.json",
        s3_output / "selected_samples_manifest.json",
        s4_output / "selected_samples_manifest.json",
    ]
    for split in (*DOMAIN_SPLITS, *OOD_SPLITS):
        for mode in ("free", "candidate"):
            s3_path = s3_output / "predictions" / f"{split}_{mode}.jsonl"
            s4_path = s4_output / "predictions" / f"{split}_{mode}.jsonl"
            paired[mode][split] = _paired_rows(s3_path, s4_path)
            input_paths.extend((s3_path, s4_path))

    s3_selected = _read_json(s3_output / "selected_samples_manifest.json")
    s4_selected = _read_json(s4_output / "selected_samples_manifest.json")
    if s3_selected != s4_selected:
        raise ValueError("S3/S4 选择样本清单不一致，不能执行同协议比较")

    calibration: dict[str, object] = {}
    for split in CALIBRATION_SPLITS:
        s3_rows, s4_rows = paired["candidate"][split]
        s3_metrics = _calibration(s3_rows)
        s4_metrics = _calibration(s4_rows)
        calibration[split] = {
            "s3": s3_metrics,
            "s4": s4_metrics,
            "delta_s4_minus_s3": {
                key: s4_metrics[key] - s3_metrics[key]
                for key in (
                    "expected_calibration_error",
                    "brier_score",
                    "negative_log_likelihood",
                )
            },
        }

    bootstrap: dict[str, object] = {"free_generation": {}, "candidate_scoring": {}}
    for split in PRIMARY_SPLITS:
        for mode, field in (("free", "parsed_label"), ("candidate", "prediction")):
            s3_rows, s4_rows = paired[mode][split]
            truth, s3_predictions = _prediction_values(s3_rows, field)
            _, s4_predictions = _prediction_values(s4_rows, field)
            labels = _label_order(s3_rows)
            bootstrap_key = "free_generation" if mode == "free" else "candidate_scoring"
            bootstrap[bootstrap_key][split] = {
                "macro_f1_delta": _bootstrap_delta(
                    truth,
                    s3_predictions,
                    s4_predictions,
                    lambda actual, predicted, labels=labels: _macro_f1(actual, predicted, labels),
                    repetitions,
                    seed,
                )
            }

    s3_subtype_rows, s4_subtype_rows = paired["candidate"]["subtype_test"]
    subtype_truth, s3_subtype_predictions = _prediction_values(s3_subtype_rows, "prediction")
    _, s4_subtype_predictions = _prediction_values(s4_subtype_rows, "prediction")
    bootstrap["candidate_scoring"]["subtype_test"]["known_rejection_rate_delta"] = _bootstrap_delta(
        subtype_truth,
        s3_subtype_predictions,
        s4_subtype_predictions,
        lambda actual, predicted: _rate(
            actual,
            predicted,
            lambda _label, guess: guess == UNKNOWN_LABEL,
            lambda label: label != UNKNOWN_LABEL,
        ),
        repetitions,
        seed,
    )
    bootstrap["open_set_aggregate"] = _open_set_bootstrap(
        {split: paired["candidate"][split] for split in OOD_SPLITS}, repetitions, seed
    )

    primary = {
        split: {
            "s3": _summary_metric(s3_summary, split, "free_generation", "macro_f1"),
            "s4": _summary_metric(s4_summary, split, "free_generation", "macro_f1"),
        }
        for split in PRIMARY_SPLITS
    }
    for values in primary.values():
        values["delta_s4_minus_s3"] = values["s4"] - values["s3"]

    candidate_domain = {
        split: {
            "s3": _summary_metric(s3_summary, split, "candidate_scoring", "macro_f1"),
            "s4": _summary_metric(s4_summary, split, "candidate_scoring", "macro_f1"),
        }
        for split in PRIMARY_SPLITS
    }
    for values in candidate_domain.values():
        values["delta_s4_minus_s3"] = values["s4"] - values["s3"]

    open_set = {}
    for split in OOD_SPLITS:
        open_set[split] = {}
        for metric in ("unknown_recall", "benign_false_positive_rate", "known_rejection_rate"):
            s3_value = _summary_metric(s3_summary, split, "candidate_scoring", metric)
            s4_value = _summary_metric(s4_summary, split, "candidate_scoring", metric)
            open_set[split][metric] = {
                "s3": s3_value,
                "s4": s4_value,
                "delta_s4_minus_s3": s4_value - s3_value,
            }
    open_unknown_delta = _mean(
        [open_set[split]["unknown_recall"]["delta_s4_minus_s3"] for split in OOD_SPLITS]
    )
    open_false_positive_delta = _mean(
        [open_set[split]["benign_false_positive_rate"]["delta_s4_minus_s3"] for split in OOD_SPLITS]
    )

    s3_known_rejection = _summary_metric(
        s3_summary, "subtype_test", "candidate_scoring", "known_rejection_rate"
    )
    s4_known_rejection = _summary_metric(
        s4_summary, "subtype_test", "candidate_scoring", "known_rejection_rate"
    )
    s3_unobserved = float(_nested(s3_training_summary, "validation", "state_mse_unobserved"))
    s4_unobserved = float(_nested(s4_training_summary, "validation", "state_mse_unobserved"))
    s3_residual = float(_nested(s3_training_summary, "validation", "physics_residual_mse"))
    s4_residual = float(_nested(s4_training_summary, "validation", "physics_residual_mse"))
    mechanism = {
        "unobserved_state_mse": {
            "s3": s3_unobserved,
            "s4": s4_unobserved,
            "relative_improvement": _percent_improvement(s3_unobserved, s4_unobserved),
        },
        "physics_residual_mse": {
            "s3": s3_residual,
            "s4": s4_residual,
            "relative_improvement": _percent_improvement(s3_residual, s4_residual),
        },
    }
    valid_rates = {
        variant: min(
            _summary_metric(summary, split, "free_generation", "json_valid_rate")
            for split in (*DOMAIN_SPLITS, *OOD_SPLITS)
        )
        for variant, summary in (("s3", s3_summary), ("s4", s4_summary))
    }
    subtype_ece_delta = float(
        _nested(
            calibration,
            "subtype_test",
            "delta_s4_minus_s3",
            "expected_calibration_error",
        )
    )
    criteria = {
        "family_free_macro_f1": primary["family_test"]["delta_s4_minus_s3"] >= -0.01,
        "subtype_free_macro_f1": primary["subtype_test"]["delta_s4_minus_s3"] >= -0.01,
        "structured_output_validity": min(valid_rates.values()) >= 0.95,
        "unknown_recall_mean": open_unknown_delta >= -0.05,
        "benign_false_positive_rate_mean": open_false_positive_delta <= 0.02,
        "known_rejection_rate": s4_known_rejection - s3_known_rejection <= 0.02,
        "subtype_test_expected_calibration_error": subtype_ece_delta <= 0.02,
        "unobserved_state_mse": mechanism["unobserved_state_mse"]["relative_improvement"] >= 0.10,
        "physics_residual_mse": mechanism["physics_residual_mse"]["relative_improvement"] >= 0.10,
    }
    criteria["overall_pass"] = all(criteria.values())

    comparison = {
        "schema_version": "flow_probe_s3_s4_detection_comparison_v1",
        "protocol": {
            "bootstrap_repetitions": repetitions,
            "bootstrap_seed": seed,
            "bootstrap_sampling": "paired_stratified_by_true_label",
            "calibration_bins": 15,
            "calibration_bin_type": "equal_width",
            "delta_direction": "s4_minus_s3",
        },
        "primary_free_generation": primary,
        "candidate_domain": candidate_domain,
        "open_set": open_set,
        "open_set_aggregate": {
            "unknown_recall_mean_delta": open_unknown_delta,
            "benign_false_positive_rate_mean_delta": open_false_positive_delta,
            "subtype_test_known_rejection_rate": {
                "s3": s3_known_rejection,
                "s4": s4_known_rejection,
                "delta_s4_minus_s3": s4_known_rejection - s3_known_rejection,
            },
        },
        "minimum_free_generation_json_valid_rate": valid_rates,
        "mechanism": mechanism,
        "training": {"s3": s3_training_summary, "s4": s4_training_summary},
        "evaluation_efficiency": {
            variant: {
                split: {
                    mode: _nested(summary, "results", split, mode, "efficiency")
                    for mode in ("free_generation", "candidate_scoring")
                }
                for split in (*DOMAIN_SPLITS, *OOD_SPLITS)
            }
            for variant, summary in (("s3", s3_summary), ("s4", s4_summary))
        },
        "criteria": criteria,
    }

    input_manifest = {
        "schema_version": "flow_probe_s3_s4_detection_inputs_v1",
        "files": {str(path.resolve()): _sha256(path) for path in input_paths},
        "selected_samples_identical": True,
    }
    analysis_config = {
        "s3_output": str(s3_output.resolve()),
        "s4_output": str(s4_output.resolve()),
        "s3_training": str(s3_training.resolve()),
        "s4_training": str(s4_training.resolve()),
        "output": str(output.resolve()),
        "bootstrap_repetitions": repetitions,
        "seed": seed,
    }
    environment = {"python": sys.version, "platform": platform.platform()}
    _write_json(output / "analysis_config.json", analysis_config)
    _write_json(output / "environment.json", environment)
    _write_json(output / "input_manifest.json", input_manifest)
    _write_json(output / "calibration_metrics.json", calibration)
    _write_json(output / "paired_bootstrap.json", bootstrap)
    _write_json(output / "comparison_summary.json", comparison)
    artifact_paths = [
        output / "analysis_config.json",
        output / "environment.json",
        output / "input_manifest.json",
        output / "calibration_metrics.json",
        output / "paired_bootstrap.json",
        output / "comparison_summary.json",
    ]
    artifact_manifest = {
        "schema_version": "flow_probe_s3_s4_detection_artifacts_v1",
        "status": "finished",
        "files": {
            path.name: {"sha256": _sha256(path), "size": path.stat().st_size}
            for path in artifact_paths
        },
    }
    _write_json(output / "artifact_manifest.json", artifact_manifest)
    print(json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True))
    return comparison


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="S3/S4 同协议检测结果与配对统计分析")
    parser.add_argument("--s3-output", type=Path, required=True)
    parser.add_argument("--s4-output", type=Path, required=True)
    parser.add_argument("--s3-training", type=Path, required=True)
    parser.add_argument("--s4-training", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-repetitions", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.bootstrap_repetitions <= 0:
        raise ValueError("自助法重复次数必须为正整数")
    analyze(
        s3_output=args.s3_output,
        s4_output=args.s4_output,
        s3_training=args.s3_training,
        s4_training=args.s4_training,
        output=args.output,
        repetitions=args.bootstrap_repetitions,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
