"""消融①：无监督操作点估计的生死判据。

裁决命题 H1——目标域得分是可辨识的双成分混合，因此排序信号加混合分解
足以在**不使用任何目标域标签**的条件下恢复操作点。

判据在运行前冻结为模块级常量，不可由命令行覆盖。真标签只用于事后评估
恢复效果，绝不参与估计过程。
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

import numpy as np
from sklearn.metrics import f1_score

logger = logging.getLogger(__name__)

# ---- 预注册判据（冻结，不可由 CLI 覆盖）----
PASS_MACRO_F1: Final[float] = 0.60
REJECT_MACRO_F1: Final[float] = 0.55
PRIOR_LOW: Final[float] = 0.60
PRIOR_HIGH: Final[float] = 0.95
DEGENERATE_LOW: Final[float] = 0.05
DEGENERATE_HIGH: Final[float] = 0.99
TRIVIAL_ALL_POSITIVE_MACRO_F1: Final[float] = 0.453029
NEGATIVE_CONTROL_MAX_PRIOR_ERROR: Final[float] = 0.10
BOOTSTRAP_ROUNDS: Final[int] = 100
BOOTSTRAP_SEED: Final[int] = 42
EM_MAX_ITERS: Final[int] = 500
EM_TOL: Final[float] = 1e-10


@dataclass(frozen=True)
class Predictions:
    """一个变体在一个域上的逐样本预测。"""

    labels: np.ndarray
    scores: np.ndarray
    groups: np.ndarray


def load_predictions(path: Path) -> Predictions:
    """读取逐样本预测 JSONL。"""
    labels: list[int] = []
    scores: list[float] = []
    groups: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        logger.error("无法读取预测文件：%s", path)
        raise
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            logger.error("预测文件含非法 JSON 行：%s", path)
            raise
        labels.append(int(record["label"]))
        scores.append(float(record["probability_malicious"]))
        groups.append(str(record["capture_id"]))
    return Predictions(np.array(labels), np.array(scores), np.array(groups))


def _to_logit(scores: np.ndarray) -> np.ndarray:
    """把概率映射到 logit 域，供高斯混合使用。"""
    clipped = np.clip(scores, 1e-9, 1 - 1e-9)
    return np.log(clipped / (1 - clipped))


def fit_two_component_gaussian(values: np.ndarray) -> tuple[float, np.ndarray]:
    """在一维值上拟合两成分高斯混合，返回高分成分权重与其后验。

    完全不使用标签。以分位点初始化，保证高分成分对应恶意方向。
    """
    # 以中位数硬划分做初始化，各成分用簇内统计量。
    # 不可用全局 std 初始化：目标域得分高度集中时两个高斯会立即重合，
    # EM 在第一轮就退化为 responsibility 恒等于 0.5 的平凡解。
    split = float(np.median(values))
    low_mask = values <= split
    high_mask = ~low_mask
    if low_mask.sum() < 2 or high_mask.sum() < 2:
        low_mask = values <= float(np.quantile(values, 0.5))
        high_mask = ~low_mask
    mu = np.array([values[low_mask].mean(), values[high_mask].mean()], dtype=np.float64)
    sigma = np.array(
        [
            max(float(values[low_mask].std()), 1e-6),
            max(float(values[high_mask].std()), 1e-6),
        ],
        dtype=np.float64,
    )
    weight = np.array(
        [float(low_mask.mean()), float(high_mask.mean())], dtype=np.float64
    )
    responsibility = np.zeros((values.size, 2), dtype=np.float64)
    for _ in range(EM_MAX_ITERS):
        for component in (0, 1):
            density = np.exp(
                -0.5 * ((values - mu[component]) / sigma[component]) ** 2
            ) / (sigma[component] * np.sqrt(2 * np.pi))
            responsibility[:, component] = weight[component] * density
        total = responsibility.sum(axis=1, keepdims=True) + 1e-300
        responsibility /= total
        new_weight = responsibility.mean(axis=0)
        new_mu = (responsibility * values[:, None]).sum(axis=0) / (
            responsibility.sum(axis=0) + 1e-300
        )
        new_sigma = np.sqrt(
            (responsibility * (values[:, None] - new_mu) ** 2).sum(axis=0)
            / (responsibility.sum(axis=0) + 1e-300)
        )
        new_sigma = np.maximum(new_sigma, 1e-6)
        shift = float(np.abs(new_weight - weight).max())
        weight, mu, sigma = new_weight, new_mu, new_sigma
        if shift < EM_TOL:
            break
    high = int(np.argmax(mu))
    return float(weight[high]), responsibility[:, high]


def threshold_from_prior(scores: np.ndarray, prior: float) -> float:
    """把估计先验映射为阈值：使预测正例率等于估计先验。"""
    return float(np.quantile(scores, 1.0 - prior))


def macro_f1_at_prior(predictions: Predictions, prior: float) -> float:
    """按估计先验切分后的宏平均 F1；标签只在此处用于事后评估。"""
    threshold = threshold_from_prior(predictions.scores, prior)
    return float(
        f1_score(
            predictions.labels,
            (predictions.scores >= threshold).astype(int),
            average="macro",
        )
    )


def group_bootstrap_lower_bound(
    predictions: Predictions, prior: float
) -> float:
    """按 capture 组重采样，返回宏平均 F1 的 5% 分位下界。"""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    unique_groups = np.unique(predictions.groups)
    values: list[float] = []
    for _ in range(BOOTSTRAP_ROUNDS):
        sampled = rng.choice(unique_groups, size=unique_groups.size, replace=True)
        mask = np.concatenate(
            [np.flatnonzero(predictions.groups == group) for group in sampled]
        )
        subset = Predictions(
            predictions.labels[mask], predictions.scores[mask], predictions.groups[mask]
        )
        if subset.labels.min() == subset.labels.max():
            continue
        values.append(macro_f1_at_prior(subset, prior))
    if not values:
        return float("nan")
    return float(np.quantile(values, 0.05))


def evaluate_variant(target: Predictions, source: Predictions) -> dict[str, object]:
    """对单个变体运行完整判据，含源域负对照。"""
    prior_hat, _ = fit_two_component_gaussian(_to_logit(target.scores))
    recovered = macro_f1_at_prior(target, prior_hat)
    lower = group_bootstrap_lower_bound(target, prior_hat)
    source_prior_hat, _ = fit_two_component_gaussian(_to_logit(source.scores))
    source_error = abs(source_prior_hat - float(source.labels.mean()))
    negative_control_passed = source_error <= NEGATIVE_CONTROL_MAX_PRIOR_ERROR
    degenerate = prior_hat < DEGENERATE_LOW or prior_hat > DEGENERATE_HIGH
    passed = (
        recovered >= PASS_MACRO_F1
        and PRIOR_LOW <= prior_hat <= PRIOR_HIGH
        and lower > TRIVIAL_ALL_POSITIVE_MACRO_F1
        and negative_control_passed
    )
    rejected = recovered < REJECT_MACRO_F1 or degenerate
    return {
        "true_prior": float(target.labels.mean()),
        "estimated_prior": prior_hat,
        "recovered_macro_f1": recovered,
        "bootstrap_lower_5pct": lower,
        "oracle_macro_f1": macro_f1_at_prior(target, float(target.labels.mean())),
        "source_true_prior": float(source.labels.mean()),
        "source_estimated_prior": source_prior_hat,
        "negative_control_error": source_error,
        "negative_control_passed": negative_control_passed,
        "degenerate": degenerate,
        "passed": passed,
        "rejected": rejected,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument(
        "--variants", nargs="+", default=["e2-a", "e2-s", "e2-p", "e2-x"]
    )
    parser.add_argument("--output-json", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_arg_parser().parse_args(argv)
    results: dict[str, object] = {
        "thresholds": {
            "pass_macro_f1": PASS_MACRO_F1,
            "reject_macro_f1": REJECT_MACRO_F1,
            "prior_range": [PRIOR_LOW, PRIOR_HIGH],
            "trivial_all_positive_macro_f1": TRIVIAL_ALL_POSITIVE_MACRO_F1,
            "negative_control_max_prior_error": NEGATIVE_CONTROL_MAX_PRIOR_ERROR,
        },
        "variants": {},
    }
    for variant in args.variants:
        base = args.run_root / "variants" / variant / "predictions"
        target = load_predictions(base / "target_c.jsonl")
        source = load_predictions(base / "source_calibration.jsonl")
        outcome = evaluate_variant(target, source)
        results["variants"][variant] = outcome
        logger.info("%s -> %s", variant, json.dumps(outcome, ensure_ascii=False))
    if args.output_json is not None:
        args.output_json.write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
