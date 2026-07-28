"""聚合 H1 三随机种子的生成式模型与传统基线结果。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path


class H1AnalysisError(ValueError):
    """H1 输入制品不完整或不可比较。"""


_T_CRITICAL_95 = {
    1: 12.706204736432095,
    2: 4.302652729696142,
    3: 3.182446305284263,
    4: 2.7764451051977987,
    5: 2.570581835636305,
    6: 2.4469118487916806,
    7: 2.3646242510102993,
    8: 2.306004135204166,
    9: 2.2621571628540993,
    10: 2.2281388519649385,
}


def summarize_values(values: Sequence[float]) -> dict[str, float | int]:
    """返回均值、样本标准差和基于 t 分布的双侧 95% 置信区间。"""
    numeric = [float(value) for value in values]
    if not numeric:
        raise H1AnalysisError("统计值不能为空")
    if not all(math.isfinite(value) for value in numeric):
        raise H1AnalysisError("统计值必须全部为有限数")
    mean = statistics.fmean(numeric)
    if len(numeric) == 1:
        sample_std = 0.0
        half_width = 0.0
    else:
        sample_std = statistics.stdev(numeric)
        degrees_of_freedom = len(numeric) - 1
        critical = _T_CRITICAL_95.get(degrees_of_freedom, 1.959963984540054)
        half_width = critical * sample_std / math.sqrt(len(numeric))
    return {
        "n": len(numeric),
        "mean": mean,
        "sample_std": sample_std,
        "ci95_low": mean - half_width,
        "ci95_high": mean + half_width,
    }


def _load_object(path: Path) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise H1AnalysisError(f"无法读取 JSON 制品：{path}") from error
    if not isinstance(value, dict):
        raise H1AnalysisError(f"JSON 制品根节点必须是对象：{path}")
    return value


def _nested(mapping: Mapping[str, object], *keys: str) -> object:
    value: object = mapping
    for key in keys:
        if not isinstance(value, Mapping) or key not in value:
            raise H1AnalysisError(f"制品缺少字段：{'.'.join(keys)}")
        value = value[key]
    return value


def _number(mapping: Mapping[str, object], *keys: str) -> float:
    value = _nested(mapping, *keys)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise H1AnalysisError(f"制品字段不是数值：{'.'.join(keys)}")
    result = float(value)
    if not math.isfinite(result):
        raise H1AnalysisError(f"制品字段不是有限数：{'.'.join(keys)}")
    return result


def _seed(mapping: Mapping[str, object]) -> int:
    value = _nested(mapping, "seed")
    if isinstance(value, bool) or not isinstance(value, int):
        raise H1AnalysisError("制品 seed 必须是整数")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values)


def _qwen_metrics(
    summary: Mapping[str, object], training: Mapping[str, object]
) -> dict[str, float]:
    ood_names = ("ood_dos_icmp", "ood_dos_pushack", "ood_dos_udp")
    recalls = [
        _number(summary, "results", name, "candidate_scoring", "metrics", "unknown_recall")
        for name in ood_names
    ]
    false_positive_rates = [
        _number(
            summary,
            "results",
            name,
            "candidate_scoring",
            "metrics",
            "benign_false_positive_rate",
        )
        for name in ood_names
    ]
    return {
        "family_macro_f1": _number(
            summary, "results", "family_test", "free_generation", "metrics", "macro_f1"
        ),
        "subtype_free_macro_f1": _number(
            summary, "results", "subtype_test", "free_generation", "metrics", "macro_f1"
        ),
        "subtype_candidate_macro_f1": _number(
            summary, "results", "subtype_test", "candidate_scoring", "metrics", "macro_f1"
        ),
        "known_rejection_rate": _number(
            summary,
            "results",
            "subtype_test",
            "candidate_scoring",
            "metrics",
            "known_rejection_rate",
        ),
        "ood_unknown_recall_mean": _mean(recalls),
        "ood_benign_false_positive_rate_mean": _mean(false_positive_rates),
        "ood_icmp_unknown_recall": recalls[0],
        "ood_pushack_unknown_recall": recalls[1],
        "ood_udp_unknown_recall": recalls[2],
        "ood_icmp_benign_false_positive_rate": false_positive_rates[0],
        "ood_pushack_benign_false_positive_rate": false_positive_rates[1],
        "ood_udp_benign_false_positive_rate": false_positive_rates[2],
        "threshold": _number(summary, "threshold_calibration", "threshold"),
        "train_runtime_seconds": _number(training, "metrics", "train_runtime"),
        "train_samples_per_second": _number(training, "metrics", "train_samples_per_second"),
        "subtype_free_samples_per_second": _number(
            summary,
            "results",
            "subtype_test",
            "free_generation",
            "efficiency",
            "samples_per_second",
        ),
        "subtype_candidate_samples_per_second": _number(
            summary,
            "results",
            "subtype_test",
            "candidate_scoring",
            "efficiency",
            "samples_per_second",
        ),
        "candidate_peak_gpu_memory_mib": _number(
            summary,
            "results",
            "subtype_test",
            "candidate_scoring",
            "efficiency",
            "peak_gpu_memory_mib",
        ),
    }


def _baseline_metrics(summary: Mapping[str, object]) -> dict[str, float]:
    prefix = ("subtype", "models", "hist_gradient_boosting")
    ood_names = ("ood-dos-icmp", "ood-dos-pushack", "ood-dos-udp")
    recalls = [
        _number(summary, *prefix, "evaluations", name, "metrics", "unknown_recall")
        for name in ood_names
    ]
    false_positive_rates = [
        _number(
            summary,
            *prefix,
            "evaluations",
            name,
            "metrics",
            "benign_false_positive_rate",
        )
        for name in ood_names
    ]
    return {
        "family_macro_f1": _number(
            summary,
            "family",
            "models",
            "hist_gradient_boosting",
            "evaluations",
            "test",
            "metrics",
            "macro_f1",
        ),
        "subtype_candidate_macro_f1": _number(
            summary, *prefix, "evaluations", "test", "metrics", "macro_f1"
        ),
        "known_rejection_rate": _number(
            summary,
            *prefix,
            "evaluations",
            "test",
            "metrics",
            "known_rejection_rate",
        ),
        "ood_unknown_recall_mean": _mean(recalls),
        "ood_benign_false_positive_rate_mean": _mean(false_positive_rates),
        "ood_icmp_unknown_recall": recalls[0],
        "ood_pushack_unknown_recall": recalls[1],
        "ood_udp_unknown_recall": recalls[2],
        "ood_icmp_benign_false_positive_rate": false_positive_rates[0],
        "ood_pushack_benign_false_positive_rate": false_positive_rates[1],
        "ood_udp_benign_false_positive_rate": false_positive_rates[2],
        "fit_runtime_seconds": _number(summary, *prefix, "fit_seconds")
        + _number(summary, "family", "models", "hist_gradient_boosting", "fit_seconds"),
    }


def _index_by_seed(paths: Sequence[Path], label: str) -> dict[int, tuple[Path, dict[str, object]]]:
    indexed: dict[int, tuple[Path, dict[str, object]]] = {}
    for raw_path in paths:
        path = Path(raw_path)
        value = _load_object(path)
        seed = _seed(value)
        if seed in indexed:
            raise H1AnalysisError(f"{label}包含重复随机种子：{seed}")
        indexed[seed] = (path, value)
    if not indexed:
        raise H1AnalysisError(f"{label}输入不能为空")
    return indexed


def aggregate_h1_files(
    qwen_evaluation_paths: Sequence[Path],
    qwen_training_paths: Sequence[Path],
    baseline_paths: Sequence[Path],
) -> dict[str, object]:
    """按随机种子配对 H1 制品并生成可复核的描述统计。"""
    qwen_evaluations = _index_by_seed(qwen_evaluation_paths, "Qwen 评估")
    qwen_training = _index_by_seed(qwen_training_paths, "Qwen 训练")
    baselines = _index_by_seed(baseline_paths, "传统基线")
    seed_sets = (set(qwen_evaluations), set(qwen_training), set(baselines))
    if not all(seed_set == seed_sets[0] for seed_set in seed_sets[1:]):
        raise H1AnalysisError(
            "Qwen 评估、Qwen 训练与传统基线的随机种子不一致："
            f"{sorted(seed_sets[0])}、{sorted(seed_sets[1])}、{sorted(seed_sets[2])}"
        )

    per_seed: list[dict[str, object]] = []
    input_files: list[dict[str, object]] = []
    for seed in sorted(seed_sets[0]):
        evaluation_path, evaluation = qwen_evaluations[seed]
        training_path, training = qwen_training[seed]
        baseline_path, baseline = baselines[seed]
        qwen = _qwen_metrics(evaluation, training)
        baseline_metrics = _baseline_metrics(baseline)
        comparable_metrics = (
            "family_macro_f1",
            "subtype_candidate_macro_f1",
            "known_rejection_rate",
            "ood_unknown_recall_mean",
            "ood_benign_false_positive_rate_mean",
        )
        per_seed.append(
            {
                "seed": seed,
                "qwen": qwen,
                "baseline": baseline_metrics,
                "paired_difference": {
                    metric: qwen[metric] - baseline_metrics[metric] for metric in comparable_metrics
                },
            }
        )
        for role, path in (
            ("qwen_evaluation", evaluation_path),
            ("qwen_training", training_path),
            ("baseline", baseline_path),
        ):
            input_files.append(
                {"seed": seed, "role": role, "path": str(path), "sha256": _sha256(path)}
            )

    qwen_fields = tuple(per_seed[0]["qwen"])
    baseline_fields = tuple(per_seed[0]["baseline"])
    difference_fields = tuple(per_seed[0]["paired_difference"])
    return {
        "schema_version": "flow_probe_h1_analysis_v1",
        "seeds": sorted(seed_sets[0]),
        "inference_policy": (
            "随机种子数较少，只报告描述统计和配对差值；不据此进行显著性或优越性声明。"
        ),
        "per_seed": per_seed,
        "aggregate": {
            "qwen": {
                field: summarize_values([row["qwen"][field] for row in per_seed])
                for field in qwen_fields
            },
            "baseline": {
                field: summarize_values([row["baseline"][field] for row in per_seed])
                for field in baseline_fields
            },
            "paired_difference": {
                field: summarize_values([row["paired_difference"][field] for row in per_seed])
                for field in difference_fields
            },
        },
        "input_files": input_files,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="聚合 H1 三随机种子实验结果")
    parser.add_argument("--qwen-evaluation", type=Path, action="append", required=True)
    parser.add_argument("--qwen-training", type=Path, action="append", required=True)
    parser.add_argument("--baseline", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = aggregate_h1_files(args.qwen_evaluation, args.qwen_training, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
