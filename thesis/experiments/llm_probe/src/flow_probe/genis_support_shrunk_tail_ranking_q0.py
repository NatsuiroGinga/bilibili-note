"""GeNIS 支持量收缩跨场景极端尾部排序 Q0。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import sys
import threading
import time
import warnings
from collections.abc import Mapping, Sequence
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

from flow_probe import genis_scenario_holdout_corrected_v2 as corrected


class TailRankingQ0Error(RuntimeError):
    """表示 Q0 数据、统计或运行合同被破坏。"""


EVIDENCE = {
    "screening_only": True,
    "formal_paper_evidence": False,
    "official_test_accessed": False,
    "final_accessed": False,
}
EXPECTED_CORRECTED_MODULE_SHA256 = (
    "e734f78c87d515eea53ad35c47ef41268e651cb74b732681c51122d1a3afa5c9"
)
EXPECTED_CORRECTED_CONFIG_SHA256 = (
    "45a5d3e94b41c20fe95da9e488cce1f47b13a81f9267e7e35c0c40af96f8aca7"
)
MODEL_KEYS = ("xgboost", "random_forest")
METHOD_KEYS = (
    "uniform-balanced",
    "sample-cvar-tail",
    "groupdro-max-scene",
    "sagawa-small-group-adjusted",
    "unshrunk-scene-tail",
    "support-shrunk-scene-tail",
    "shuffled-scene-support-tail",
)
SINGLE_MECHANISM_KEYS = (
    "sample-cvar-tail",
    "groupdro-max-scene",
    "sagawa-small-group-adjusted",
)
SCENE_FAMILY = {
    1: "disrupt",
    2: "disrupt",
    3: "disrupt",
    4: "disrupt",
    5: "disrupt",
    6: "authtest",
    7: "authtest",
    8: "authtest",
}
XGB_SEMAPHORE = threading.Semaphore(1)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}.{threading.get_ident()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partial.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TailRankingQ0Error(f"无法读取 JSON：{path}：{error}") from error
    if not isinstance(value, dict):
        raise TailRankingQ0Error("JSON 顶层必须是对象")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _array_sha(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _resolve(config_path: Path, value: str) -> Path:
    return corrected._resolve(config_path, value)


def _load_config(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    config = _read_json(path)
    required = {
        "schema_version",
        "contract_version",
        "run_id",
        "seed",
        "corrected_v2",
        "oof",
        "tail",
        "methods",
        "parallel",
        "evaluation",
        "paths",
        "swanlab",
        "evidence",
    }
    missing = required - set(config)
    if missing:
        raise TailRankingQ0Error(f"配置缺少字段：{sorted(missing)}")
    source = config["corrected_v2"]
    module_path = _resolve(path, str(source["module_path"]))
    corrected_config_path = _resolve(path, str(source["config_path"]))
    imported_path = Path(corrected.__file__).resolve()
    if module_path != imported_path:
        raise TailRankingQ0Error("导入的 corrected-v2 模块路径与冻结路径不一致")
    module_sha = _sha256(module_path)
    corrected_config_sha = _sha256(corrected_config_path)
    if (
        source.get("module_sha256") != EXPECTED_CORRECTED_MODULE_SHA256
        or source.get("config_sha256") != EXPECTED_CORRECTED_CONFIG_SHA256
        or module_sha != EXPECTED_CORRECTED_MODULE_SHA256
        or corrected_config_sha != EXPECTED_CORRECTED_CONFIG_SHA256
    ):
        raise TailRankingQ0Error("corrected-v2 模块或配置 SHA-256 漂移")
    corrected_config = corrected._load_config(corrected_config_path)
    tail = config["tail"]
    parallel = config["parallel"]
    evaluation = config["evaluation"]
    oof = config["oof"]
    if (
        config["schema_version"] != "genis-support-shrunk-tail-ranking-q0-config-v1"
        or config["contract_version"] != "support-shrunk-tail-ranking-q0-v1"
        or config["seed"] != 42
        or config["evidence"] != EVIDENCE
        or tuple(config["methods"]) != METHOD_KEYS
        or oof["fold_count"] != 2
        or oof["stable_key_atomic"] is not True
        or parallel["max_outer_concurrency"] != 2
        or parallel["max_xgboost_concurrency"] != 1
        or parallel["total_evaluation_units"] != 112
        or parallel["random_forest_n_jobs"] != 4
        or evaluation["outer_scene_count"] != 8
        or evaluation["budget_fp_per_10000"] != 10
        or evaluation["partial_auc_max_fpr"] != 0.001
        or tail["tau_score"] != 1.0
        or tail["alpha_group"] != 0.25
        or tail["tau_group"] != 0.1
        or tail["alpha_sample"] != 0.25
        or tail["tau_sample"] != 0.25
        or corrected_config["models"]["random_forest"]["n_jobs"] != 4
    ):
        raise TailRankingQ0Error("Q0 身份、OOF、尾部、并行或评价合同错误")
    return config, corrected_config


def _status(root: Path, state: str, stage: str, **extra: Any) -> None:
    _write_json(
        root / "status.json",
        {
            "schema_version": "genis-support-shrunk-tail-ranking-q0-status-v1",
            "state": state,
            "stage": stage,
            "updated_at_epoch": time.time(),
            **EVIDENCE,
            **extra,
        },
    )


def _peak_rss_gib() -> float:
    maximum = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    divisor = 1024**3 if sys.platform == "darwin" else 1024**2
    return float(maximum / divisor)


def _fit_weighted(
    model_key: str,
    params: Mapping[str, Any],
    train_x: np.ndarray,
    train_y: np.ndarray,
    sample_weight: np.ndarray,
    seed: int,
) -> tuple[Any, str]:
    if (
        sample_weight.shape != (len(train_y),)
        or not np.isfinite(sample_weight).all()
        or np.any(sample_weight < 0.0)
        or float(sample_weight.sum()) <= 0.0
    ):
        raise TailRankingQ0Error("训练权重形状错误、非有限、为负或全零")
    if model_key == "xgboost":
        import xgboost as xgb

        xgb_params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": params["max_depth"],
            "eta": params["learning_rate"],
            "subsample": params["subsample"],
            "colsample_bytree": params["colsample_bytree"],
            "min_child_weight": params["min_child_weight"],
            "lambda": params["reg_lambda"],
            "tree_method": "hist",
            "device": "cuda",
            "nthread": params["nthread"],
            "seed": seed,
        }
        with XGB_SEMAPHORE, warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = xgb.train(
                xgb_params,
                xgb.DMatrix(train_x, label=train_y, weight=sample_weight),
                num_boost_round=int(params["n_estimators"]),
            )
        messages = [str(item.message) for item in caught]
        if any("fallback" in item.lower() or "cpu" in item.lower() for item in messages):
            raise TailRankingQ0Error(f"XGBoost 发生设备回退：{messages}")
        return model, corrected._xgb_device(model)

    from sklearn.ensemble import RandomForestClassifier

    model = RandomForestClassifier(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        max_features=params["max_features"],
        min_samples_leaf=params["min_samples_leaf"],
        bootstrap=True,
        n_jobs=params["n_jobs"],
        random_state=seed,
    )
    model.fit(train_x, train_y, sample_weight=sample_weight)
    return model, "cpu"


def _fit_oof_base(
    model_key: str,
    params: Mapping[str, Any],
    train_x: np.ndarray,
    train_y: np.ndarray,
    seed: int,
) -> tuple[Any, str]:
    if model_key == "xgboost":
        with XGB_SEMAPHORE:
            return corrected._fit(model_key, params, train_x, train_y, seed)
    return corrected._fit(model_key, params, train_x, train_y, seed)


def _predict(model_key: str, model: Any, values: np.ndarray) -> np.ndarray:
    return corrected._predict(model_key, model, values)


def _oof_scores(
    config: Mapping[str, Any],
    corrected_config: Mapping[str, Any],
    outer_scene: int,
    model_key: str,
    train_x_raw: np.ndarray,
    train_y: np.ndarray,
    train_keys: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    fold_domain = str(config["oof"]["hash_domain"])
    folds = np.fromiter(
        (
            corrected._partition_bucket(fold_domain, bytes(key), 2)
            for key in train_keys
        ),
        dtype=np.uint8,
        count=len(train_keys),
    )
    scores = np.full(len(train_y), np.nan, dtype=np.float64)
    fold_summary: list[dict[str, Any]] = []
    for fold in (0, 1):
        fit_mask = folds != fold
        predict_mask = folds == fold
        if (
            len(np.unique(train_y[fit_mask])) != 2
            or len(np.unique(train_y[predict_mask])) != 2
        ):
            raise TailRankingQ0Error("两折 OOF 的拟合侧或预测侧缺少二分类类别")
        fit_raw = train_x_raw[fit_mask]
        predict_raw = train_x_raw[predict_mask]
        if model_key == "random_forest":
            fit_x, predict_x = corrected._impute(fit_raw, predict_raw)
        else:
            fit_x, predict_x = fit_raw, predict_raw
        model, device = _fit_oof_base(
            model_key,
            corrected_config["models"][model_key],
            fit_x,
            train_y[fit_mask],
            int(config["seed"]),
        )
        scores[predict_mask] = _predict(model_key, model, predict_x)
        fold_summary.append(
            {
                "fold": fold,
                "fit_rows": int(np.count_nonzero(fit_mask)),
                "predict_rows": int(np.count_nonzero(predict_mask)),
                "fit_benign_rows": int(np.count_nonzero(train_y[fit_mask] == 0)),
                "fit_malicious_rows": int(np.count_nonzero(train_y[fit_mask] == 1)),
                "predict_benign_rows": int(np.count_nonzero(train_y[predict_mask] == 0)),
                "predict_malicious_rows": int(np.count_nonzero(train_y[predict_mask] == 1)),
                "device": device,
            }
        )
        del model
    if not np.isfinite(scores).all():
        raise TailRankingQ0Error("两折 OOF 分数未完整覆盖或含非有限值")
    return scores, {
        "outer_test_scene": outer_scene,
        "model": model_key,
        "fold_count": 2,
        "fold_assignment_sha256": _array_sha(folds),
        "oof_scores_sha256": _array_sha(scores),
        "folds": fold_summary,
        "scores_persisted": False,
    }


def _smooth_cvar_weights(
    values: np.ndarray, alpha: float, tau: float
) -> tuple[np.ndarray, float]:
    if (
        values.ndim != 1
        or len(values) == 0
        or not np.isfinite(values).all()
        or not 0.0 < alpha < 1.0
        or tau <= 0.0
    ):
        raise TailRankingQ0Error("平滑 CVaR 输入无效")

    def mean_sigmoid(eta: float) -> float:
        scaled = np.clip((values - eta) / tau, -60.0, 60.0)
        return float(np.mean(1.0 / (1.0 + np.exp(-scaled))))

    low = float(values.min() - 80.0 * tau)
    high = float(values.max() + 80.0 * tau)
    for _ in range(100):
        midpoint = (low + high) / 2.0
        if mean_sigmoid(midpoint) > alpha:
            low = midpoint
        else:
            high = midpoint
    eta = (low + high) / 2.0
    scaled = np.clip((values - eta) / tau, -60.0, 60.0)
    weights = 1.0 / (1.0 + np.exp(-scaled)) / alpha
    weights /= float(weights.mean())
    if not np.isfinite(weights).all() or np.any(weights <= 0.0):
        raise TailRankingQ0Error("平滑 CVaR 权重非有限或非正")
    return weights.astype(np.float64, copy=False), eta


def _risk_summary(
    malicious_scores: np.ndarray,
    benign_scores: np.ndarray,
    scene_ids: np.ndarray,
    config: Mapping[str, Any],
) -> tuple[np.ndarray, dict[int, float], dict[int, float], dict[int, int], dict[str, Any]]:
    epsilon = float(config["tail"]["probability_clip"])
    tau_score = float(config["tail"]["tau_score"])
    malicious_logits = np.log(
        np.clip(malicious_scores, epsilon, 1.0 - epsilon)
        / (1.0 - np.clip(malicious_scores, epsilon, 1.0 - epsilon))
    )
    benign_logits = np.log(
        np.clip(benign_scores, epsilon, 1.0 - epsilon)
        / (1.0 - np.clip(benign_scores, epsilon, 1.0 - epsilon))
    )
    q = float(np.quantile(benign_logits, float(config["tail"]["benign_logit_quantile"])))
    losses = np.logaddexp(0.0, (q - malicious_logits) / tau_score) / math.log(2.0)
    scenes = sorted(int(value) for value in np.unique(scene_ids))
    support = {scene: int(np.count_nonzero(scene_ids == scene)) for scene in scenes}
    risks = {scene: float(np.mean(losses[scene_ids == scene])) for scene in scenes}
    lambda_s = float(np.median(np.asarray(list(support.values()), dtype=np.float64)))
    parent_risks: dict[str, float] = {}
    for family in sorted(set(SCENE_FAMILY[scene] for scene in scenes)):
        mask = np.asarray([SCENE_FAMILY[int(scene)] == family for scene in scene_ids])
        parent_risks[family] = float(np.mean(losses[mask]))
    shrunk = {
        scene: (
            support[scene] / (support[scene] + lambda_s) * risks[scene]
            + lambda_s
            / (support[scene] + lambda_s)
            * parent_risks[SCENE_FAMILY[scene]]
        )
        for scene in scenes
    }
    summary = {
        "benign_logit_quantile": q,
        "lambda_support": lambda_s,
        "support": {str(key): value for key, value in support.items()},
        "raw_risk": {str(key): value for key, value in risks.items()},
        "parent_risk": parent_risks,
        "shrunk_risk": {str(key): value for key, value in shrunk.items()},
        "shrinkage_coefficient": {
            str(scene): support[scene] / (support[scene] + lambda_s) for scene in scenes
        },
        "loss_summary": _distribution_summary(losses),
        "losses_sha256": _array_sha(losses),
        "per_sample_losses_persisted": False,
    }
    return losses, risks, shrunk, support, summary


def _distribution_summary(values: np.ndarray) -> dict[str, float]:
    return {
        "minimum": float(np.min(values)),
        "q25": float(np.quantile(values, 0.25)),
        "median": float(np.median(values)),
        "q75": float(np.quantile(values, 0.75)),
        "maximum": float(np.max(values)),
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
    }


def _scene_tail_multiplier(
    scene_ids: np.ndarray,
    risks: Mapping[int, float],
    config: Mapping[str, Any],
) -> tuple[np.ndarray, dict[str, Any]]:
    scenes = sorted(risks)
    values = np.asarray([risks[scene] for scene in scenes], dtype=np.float64)
    group_weights, eta = _smooth_cvar_weights(
        values,
        float(config["tail"]["alpha_group"]),
        float(config["tail"]["tau_group"]),
    )
    lookup = {scene: float(group_weights[index]) for index, scene in enumerate(scenes)}
    multiplier = np.asarray([lookup[int(scene)] for scene in scene_ids], dtype=np.float64)
    return multiplier, {
        "eta": eta,
        "scene_weights": {str(key): value for key, value in lookup.items()},
    }


def _one_group_multiplier(
    scene_ids: np.ndarray, selection_scores: Mapping[int, float]
) -> tuple[np.ndarray, dict[str, Any]]:
    selected = max(sorted(selection_scores), key=lambda scene: selection_scores[scene])
    multiplier = np.asarray(scene_ids == selected, dtype=np.float64)
    multiplier /= float(multiplier.mean())
    return multiplier, {
        "selected_scene": selected,
        "selection_scores": {
            str(key): float(value) for key, value in selection_scores.items()
        },
    }


def _method_multipliers(
    losses: np.ndarray,
    scene_ids: np.ndarray,
    risks: Mapping[int, float],
    shrunk: Mapping[int, float],
    support: Mapping[int, int],
    config: Mapping[str, Any],
    outer_scene: int,
    model_key: str,
) -> dict[str, tuple[np.ndarray, dict[str, Any]]]:
    sample_weights, sample_eta = _smooth_cvar_weights(
        losses,
        float(config["tail"]["alpha_sample"]),
        float(config["tail"]["tau_sample"]),
    )
    raw_group, raw_group_summary = _scene_tail_multiplier(scene_ids, risks, config)
    shrunk_group, shrunk_group_summary = _scene_tail_multiplier(scene_ids, shrunk, config)
    groupdro, groupdro_summary = _one_group_multiplier(scene_ids, risks)
    sagawa_c = math.sqrt(float(np.median(np.asarray(list(support.values())))))
    sagawa_scores = {
        scene: risks[scene] + sagawa_c / math.sqrt(support[scene]) for scene in risks
    }
    sagawa, sagawa_summary = _one_group_multiplier(scene_ids, sagawa_scores)
    shuffled_ids = scene_ids.copy()
    shuffle_seed = int(config["seed"])
    np.random.default_rng(shuffle_seed).shuffle(shuffled_ids)
    shuffled_losses, shuffled_risks, shuffled_shrunk, shuffled_support, shuffled_summary = (
        _risk_summary_from_losses(losses, shuffled_ids)
    )
    if not np.array_equal(np.sort(shuffled_ids), np.sort(scene_ids)):
        raise TailRankingQ0Error("打乱场景身份未保持支持量")
    shuffled_group, shuffled_group_summary = _scene_tail_multiplier(
        shuffled_ids, shuffled_shrunk, config
    )
    del shuffled_losses
    methods: dict[str, tuple[np.ndarray, dict[str, Any]]] = {
        "uniform-balanced": (np.ones(len(losses)), {"mechanism": "none"}),
        "sample-cvar-tail": (
            sample_weights,
            {"sample_eta": sample_eta, "sample_tail": _distribution_summary(sample_weights)},
        ),
        "groupdro-max-scene": (groupdro, groupdro_summary),
        "sagawa-small-group-adjusted": (
            sagawa,
            {"adjustment_c": sagawa_c, **sagawa_summary},
        ),
        "unshrunk-scene-tail": (
            raw_group * sample_weights,
            {"sample_eta": sample_eta, "group_tail": raw_group_summary},
        ),
        "support-shrunk-scene-tail": (
            shrunk_group * sample_weights,
            {"sample_eta": sample_eta, "group_tail": shrunk_group_summary},
        ),
        "shuffled-scene-support-tail": (
            shuffled_group * sample_weights,
            {
                "sample_eta": sample_eta,
                "shuffle_seed": shuffle_seed,
                "shuffled_support": {str(key): value for key, value in shuffled_support.items()},
                "shuffled_raw_risk": {
                    str(key): value for key, value in shuffled_risks.items()
                },
                "shuffled_shrunk_risk": {
                    str(key): value for key, value in shuffled_shrunk.items()
                },
                "shuffled_parent_risk": shuffled_summary["parent_risk"],
                "group_tail": shuffled_group_summary,
            },
        ),
    }
    for method, (multiplier, summary) in methods.items():
        normalized = np.asarray(multiplier, dtype=np.float64)
        normalized /= float(normalized.mean())
        if not np.isfinite(normalized).all() or np.any(normalized < 0.0):
            raise TailRankingQ0Error(f"方法 {method} 的恶意乘子无效")
        summary["multiplier_summary"] = _distribution_summary(normalized)
        summary["multiplier_sha256"] = _array_sha(normalized)
        summary["per_sample_weights_persisted"] = False
        methods[method] = normalized, summary
    return methods


def _risk_summary_from_losses(
    losses: np.ndarray, scene_ids: np.ndarray
) -> tuple[np.ndarray, dict[int, float], dict[int, float], dict[int, int], dict[str, Any]]:
    scenes = sorted(int(value) for value in np.unique(scene_ids))
    support = {scene: int(np.count_nonzero(scene_ids == scene)) for scene in scenes}
    risks = {scene: float(np.mean(losses[scene_ids == scene])) for scene in scenes}
    lambda_s = float(np.median(np.asarray(list(support.values()), dtype=np.float64)))
    parent_risk: dict[str, float] = {}
    for family in sorted(set(SCENE_FAMILY[scene] for scene in scenes)):
        mask = np.asarray([SCENE_FAMILY[int(scene)] == family for scene in scene_ids])
        parent_risk[family] = float(np.mean(losses[mask]))
    shrunk = {
        scene: (
            support[scene] / (support[scene] + lambda_s) * risks[scene]
            + lambda_s
            / (support[scene] + lambda_s)
            * parent_risk[SCENE_FAMILY[scene]]
        )
        for scene in scenes
    }
    return losses, risks, shrunk, support, {
        "lambda_support": lambda_s,
        "parent_risk": parent_risk,
    }


def _metrics(
    labels: np.ndarray, scores: np.ndarray, threshold: float, max_fpr: float
) -> dict[str, Any]:
    from sklearn.metrics import average_precision_score, f1_score, roc_auc_score

    alarms = scores >= threshold
    benign = labels == 0
    malicious = labels == 1
    false_positives = int(np.count_nonzero(alarms & benign))
    true_positives = int(np.count_nonzero(alarms & malicious))
    return {
        "average_precision": float(average_precision_score(labels, scores)),
        "standardized_partial_roc_auc": float(
            roc_auc_score(labels, scores, max_fpr=max_fpr)
        ),
        "macro_f1_at_fixed_budget": float(f1_score(labels, alarms, average="macro")),
        "recall_at_fixed_budget": true_positives / int(np.count_nonzero(malicious)),
        "false_alerts_per_10000_benign": (
            false_positives * 10000.0 / int(np.count_nonzero(benign))
        ),
        "threshold": threshold,
        "false_positives": false_positives,
        "true_positives": true_positives,
        "benign_rows": int(np.count_nonzero(benign)),
        "malicious_rows": int(np.count_nonzero(malicious)),
    }


def _run_scene_model(
    config: Mapping[str, Any],
    corrected_config: Mapping[str, Any],
    output_root: Path,
    outer_scene: int,
    model_key: str,
    scenarios: Mapping[int, np.ndarray],
    scenario_keys: Mapping[int, np.ndarray],
    benign: np.ndarray,
    benign_keys: np.ndarray,
    benign_train: np.ndarray,
    benign_calibration: np.ndarray,
    benign_test: np.ndarray,
    split_receipt_sha256: str,
) -> list[dict[str, Any]]:
    unit_root = output_root / "outer_units" / f"scene-{outer_scene}" / model_key
    unit_root.mkdir(parents=True, exist_ok=False)
    _write_json(
        unit_root / "status.json",
        {"state": "RUNNING", "outer_test_scene": outer_scene, "model": model_key},
    )
    log_path = unit_root / "unit.log"
    started = time.monotonic()
    try:
        visible_scenes = [scene for scene in range(1, 9) if scene != outer_scene]
        train_malicious = np.vstack([scenarios[scene] for scene in visible_scenes])
        malicious_keys = np.concatenate([scenario_keys[scene] for scene in visible_scenes])
        malicious_scene_ids = np.concatenate(
            [np.full(len(scenarios[scene]), scene, dtype=np.uint8) for scene in visible_scenes]
        )
        benign_train_count = int(np.count_nonzero(benign_train))
        train_x_raw = np.vstack([benign[benign_train], train_malicious])
        train_y = np.concatenate(
            [
                np.zeros(benign_train_count, dtype=np.uint8),
                np.ones(len(train_malicious), dtype=np.uint8),
            ]
        )
        train_keys = np.concatenate([benign_keys[benign_train], malicious_keys])
        oof, oof_summary = _oof_scores(
            config,
            corrected_config,
            outer_scene,
            model_key,
            train_x_raw,
            train_y,
            train_keys,
        )
        losses, risks, shrunk, support, risk_summary = _risk_summary(
            oof[benign_train_count:],
            oof[:benign_train_count],
            malicious_scene_ids,
            config,
        )
        multipliers = _method_multipliers(
            losses,
            malicious_scene_ids,
            risks,
            shrunk,
            support,
            config,
            outer_scene,
            model_key,
        )
        calibration_raw = benign[benign_calibration]
        test_raw = np.vstack([benign[benign_test], scenarios[outer_scene]])
        test_y = np.concatenate(
            [
                np.zeros(np.count_nonzero(benign_test), dtype=np.uint8),
                np.ones(len(scenarios[outer_scene]), dtype=np.uint8),
            ]
        )
        if model_key == "random_forest":
            train_x, calibration_x, test_x = corrected._impute(
                train_x_raw, calibration_raw, test_raw
            )
        else:
            train_x, calibration_x, test_x = train_x_raw, calibration_raw, test_raw
        base_weights = corrected._balanced_weights(train_y).astype(np.float64)
        cells: list[dict[str, Any]] = []
        for method_index, method in enumerate(METHOD_KEYS):
            malicious_multiplier, weight_summary = multipliers[method]
            sample_weight = base_weights.copy()
            sample_weight[benign_train_count:] *= malicious_multiplier
            fit_started = time.monotonic()
            model, device = _fit_weighted(
                model_key,
                corrected_config["models"][model_key],
                train_x,
                train_y,
                sample_weight,
                int(config["seed"]),
            )
            fit_seconds = time.monotonic() - fit_started
            calibration_scores = _predict(model_key, model, calibration_x)
            allowed = math.floor(
                len(calibration_scores)
                * int(config["evaluation"]["budget_fp_per_10000"])
                / 10000
            )
            threshold, calibration_actual = corrected._threshold(
                calibration_scores, allowed
            )
            predict_started = time.monotonic()
            test_scores = _predict(model_key, model, test_x)
            predict_seconds = time.monotonic() - predict_started
            cell = {
                "outer_test_scene": outer_scene,
                "model": model_key,
                "method": method,
                "evaluation_unit_index_within_outer_model": method_index,
                "device": device,
                "train_rows": len(train_y),
                "calibration_benign_rows": len(calibration_scores),
                "test_rows": len(test_y),
                "split_receipt_sha256": split_receipt_sha256,
                "shared_oof_summary_sha256": _canonical_sha(oof_summary),
                "calibration_allowed_false_positives": allowed,
                "calibration_actual_false_positives": calibration_actual,
                "fit_seconds": fit_seconds,
                "predict_seconds": predict_seconds,
                "peak_rss_gib": _peak_rss_gib(),
                "model_summary": {
                    "parameters_sha256": _canonical_sha(
                        corrected_config["models"][model_key]
                    ),
                    "configured_estimators": corrected_config["models"][model_key][
                        "n_estimators"
                    ],
                    "persisted": False,
                },
                "weight_summary": weight_summary,
                "metrics": _metrics(
                    test_y,
                    test_scores,
                    threshold,
                    float(config["evaluation"]["partial_auc_max_fpr"]),
                ),
            }
            _write_json(unit_root / f"cell-{method}.json", cell)
            cells.append(cell)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    f"METHOD_FINISHED scene={outer_scene} model={model_key} "
                    f"method={method} fit_seconds={fit_seconds:.3f} "
                    f"elapsed_seconds={time.monotonic() - started:.3f}\n"
                )
            print(
                f"METHOD_FINISHED scene={outer_scene} model={model_key} "
                f"method={method} completed={len(cells)}/7 "
                f"elapsed_seconds={time.monotonic() - started:.3f}",
                flush=True,
            )
            del model, sample_weight, calibration_scores, test_scores
        shared_summary = {
            "outer_test_scene": outer_scene,
            "model": model_key,
            "oof": oof_summary,
            "risk": risk_summary,
            "method_count": len(cells),
            "oof_reused_by_all_methods": True,
            "persistent_features": False,
            "persistent_labels": False,
            "persistent_stable_keys": False,
            "persistent_fold_memberships": False,
            "persistent_sample_weights": False,
            "persistent_probabilities": False,
        }
        _write_json(unit_root / "shared_summary.json", shared_summary)
        _write_json(
            unit_root / "status.json",
            {
                "state": "FINISHED",
                "outer_test_scene": outer_scene,
                "model": model_key,
                "completed_methods": len(cells),
            },
        )
        return cells
    except Exception as error:
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(
                f"FAILED scene={outer_scene} model={model_key} "
                f"type={type(error).__name__} detail={error}\n"
            )
        _write_json(
            unit_root / "status.json",
            {
                "state": "FAILED",
                "outer_test_scene": outer_scene,
                "model": model_key,
                "failure_type": type(error).__name__,
                "detail": str(error),
            },
        )
        raise


def _run_outer_scene(
    config: Mapping[str, Any],
    corrected_config: Mapping[str, Any],
    output_root: Path,
    outer_scene: int,
    scenarios: Mapping[int, np.ndarray],
    scenario_keys: Mapping[int, np.ndarray],
    benign: np.ndarray,
    benign_keys: np.ndarray,
    train_mask: np.ndarray,
    calibration_mask: np.ndarray,
    test_mask: np.ndarray,
    split_receipt_sha256: str,
) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for model_key in MODEL_KEYS:
        cells.extend(
            _run_scene_model(
                config,
                corrected_config,
                output_root,
                outer_scene,
                model_key,
                scenarios,
                scenario_keys,
                benign,
                benign_keys,
                train_mask,
                calibration_mask,
                test_mask,
                split_receipt_sha256,
            )
        )
    return cells


def _aggregate_cells(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    metric_names = (
        "recall_at_fixed_budget",
        "standardized_partial_roc_auc",
        "macro_f1_at_fixed_budget",
        "average_precision",
        "false_alerts_per_10000_benign",
    )
    for model_key in MODEL_KEYS:
        summary[model_key] = {}
        for method in METHOD_KEYS:
            selected = [
                cell
                for cell in cells
                if cell["model"] == model_key and cell["method"] == method
            ]
            if len(selected) != 8:
                raise TailRankingQ0Error(
                    f"聚合缺少场景：model={model_key} method={method} count={len(selected)}"
                )
            summary[model_key][method] = {}
            for metric in metric_names:
                values = np.asarray(
                    [cell["metrics"][metric] for cell in selected], dtype=np.float64
                )
                summary[model_key][method][metric] = {
                    "mean": float(values.mean()),
                    "minimum": float(values.min()),
                    "maximum": float(values.max()),
                    "worst_scene": int(
                        selected[int(np.argmin(values))]["outer_test_scene"]
                    ),
                }
    return summary


def _decision(summary: Mapping[str, Any]) -> dict[str, Any]:
    candidate = "support-shrunk-scene-tail"
    shuffled = "shuffled-scene-support-tail"
    checks: list[dict[str, Any]] = []
    best_single_by_model: dict[str, str] = {}
    single_improvements: dict[str, float] = {}
    for model_key in MODEL_KEYS:
        model_summary = summary[model_key]
        baseline = model_summary["uniform-balanced"]
        complete = model_summary[candidate]
        best_single = max(
            SINGLE_MECHANISM_KEYS,
            key=lambda method: model_summary[method]["recall_at_fixed_budget"]["minimum"],
        )
        best_single_by_model[model_key] = best_single
        single_improvements[model_key] = (
            complete["recall_at_fixed_budget"]["minimum"]
            - model_summary[best_single]["recall_at_fixed_budget"]["minimum"]
        )
        model_checks = {
            "budget_within_limit": complete["false_alerts_per_10000_benign"]["maximum"]
            <= 10.0,
            "worst_recall_gain_gte_0_02": complete["recall_at_fixed_budget"]["minimum"]
            - baseline["recall_at_fixed_budget"]["minimum"]
            >= 0.02,
            "worst_partial_auc_gain_gte_0_005": complete[
                "standardized_partial_roc_auc"
            ]["minimum"]
            - baseline["standardized_partial_roc_auc"]["minimum"]
            >= 0.005,
            "worst_budget_macro_f1_drop_le_0_01": complete[
                "macro_f1_at_fixed_budget"
            ]["minimum"]
            - baseline["macro_f1_at_fixed_budget"]["minimum"]
            >= -0.01,
            "minimum_average_precision_drop_le_0_001": complete["average_precision"][
                "minimum"
            ]
            - baseline["average_precision"]["minimum"]
            >= -0.001,
            "not_worse_than_best_single_by_0_005": single_improvements[model_key]
            >= -0.005,
            "shuffled_recall_drop_gte_0_01": complete["recall_at_fixed_budget"][
                "minimum"
            ]
            - model_summary[shuffled]["recall_at_fixed_budget"]["minimum"]
            >= 0.01,
        }
        checks.append(
            {
                "model": model_key,
                "best_single_mechanism": best_single,
                "single_mechanism_recall_improvement": single_improvements[model_key],
                "checks": model_checks,
            }
        )
    cross_model_single_gate = max(single_improvements.values()) >= 0.01
    all_model_checks = all(all(item["checks"].values()) for item in checks)
    return {
        "candidate": candidate,
        "advanced": bool(all_model_checks and cross_model_single_gate),
        "model_checks": checks,
        "cross_model_best_single_gain_gte_0_01": cross_model_single_gate,
        "failure_action": "否决候选，不修改测试数据、指标、阈值或基线",
    }


def run(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config, corrected_config = _load_config(config_path)
    output_root = _resolve(config_path, str(config["paths"]["run_root"]))
    archive_path = _resolve(
        config_path, str(corrected_config["data"]["scenarios_archive"]["path"])
    )
    if output_root.exists():
        raise TailRankingQ0Error("Q0 唯一运行根已存在，拒绝覆盖")
    output_root.mkdir(parents=True)
    started = time.monotonic()
    _write_json(
        output_root / "run_binding.json",
        {
            "config_sha256": _sha256(config_path),
            "code_sha256": _sha256(Path(__file__).resolve()),
            "corrected_v2_module_sha256": EXPECTED_CORRECTED_MODULE_SHA256,
            "corrected_v2_config_sha256": EXPECTED_CORRECTED_CONFIG_SHA256,
            "archive_sha256": corrected_config["data"]["scenarios_archive"]["sha256"],
            "contract_version": config["contract_version"],
            "total_evaluation_units": 112,
            "max_outer_concurrency": 2,
            "max_xgboost_concurrency": 1,
            "unrelated_gpu_processes_allowed": True,
            "memory_admission_gate": False,
            **EVIDENCE,
        },
    )
    _status(
        output_root,
        "RUNNING",
        "load-corrected-v2-same-source-data",
        completed_evaluation_units=0,
        total_evaluation_units=112,
    )
    try:
        (
            scenarios,
            scenario_keys,
            benign,
            benign_keys,
            benign_sources,
            data_summary,
        ) = corrected._load_same_source_data(corrected_config, archive_path)
        _write_json(output_root / "data_summary.json", data_summary)
        partition = corrected_config["partition"]
        buckets = np.fromiter(
            (
                corrected._partition_bucket(
                    str(partition["hash_domain"]), bytes(key), int(partition["modulo"])
                )
                for key in benign_keys
            ),
            dtype=np.uint8,
            count=len(benign_keys),
        )
        train_mask = np.isin(buckets, partition["train_buckets"])
        calibration_mask = np.isin(buckets, partition["calibration_buckets"])
        test_mask = np.isin(buckets, partition["test_buckets"])
        if not np.all(train_mask | calibration_mask | test_mask):
            raise TailRankingQ0Error("良性稳定键存在未归属分区")
        train_keys = {bytes(key) for key in benign_keys[train_mask]}
        calibration_keys = {bytes(key) for key in benign_keys[calibration_mask]}
        test_keys = {bytes(key) for key in benign_keys[test_mask]}
        intersections = {
            "train_calibration": len(train_keys & calibration_keys),
            "train_test": len(train_keys & test_keys),
            "calibration_test": len(calibration_keys & test_keys),
        }
        malicious_all = {bytes(key) for values in scenario_keys.values() for key in values}
        if (
            any(intersections.values())
            or malicious_all & (train_keys | calibration_keys | test_keys)
            or len(test_keys) < 1000
        ):
            raise TailRankingQ0Error("稳定键分区交叠或测试良性不足")
        outer_intersections: dict[str, dict[str, int]] = {}
        for outer_scene in range(1, 9):
            visible = train_keys | {
                bytes(key)
                for scene, keys in scenario_keys.items()
                if scene != outer_scene
                for key in keys
            }
            outer_test = test_keys | {bytes(key) for key in scenario_keys[outer_scene]}
            counts = {
                "train_calibration": len(visible & calibration_keys),
                "train_test": len(visible & outer_test),
                "calibration_test": len(calibration_keys & outer_test),
            }
            if any(counts.values()):
                raise TailRankingQ0Error(f"外层场景 {outer_scene} 稳定键交叠")
            outer_intersections[str(outer_scene)] = counts
        split_receipt = {
            "hash_domain": partition["hash_domain"],
            "modulo": partition["modulo"],
            "train_count": len(train_keys),
            "calibration_count": len(calibration_keys),
            "test_count": len(test_keys),
            "train_keyset_sha256": corrected._keyset_sha(list(train_keys)),
            "calibration_keyset_sha256": corrected._keyset_sha(list(calibration_keys)),
            "test_keyset_sha256": corrected._keyset_sha(list(test_keys)),
            "pairwise_intersections": intersections,
            "outer_fold_pairwise_intersections": outer_intersections,
            "stable_key_is_atomic": True,
        }
        _write_json(output_root / "split_receipt.json", split_receipt)
        _status(
            output_root,
            "RUNNING",
            "corrected-v2-training-visible-feature-gate",
            completed_evaluation_units=0,
            total_evaluation_units=112,
        )
        gate = corrected._feature_gate(
            corrected_config, scenarios, benign, benign_sources, train_mask
        )
        _write_json(output_root / "feature_gate.json", gate)
        if gate["blocked"]:
            raise TailRankingQ0Error(
                f"训练侧单字段 AUC 门禁阻断，训练单元为 0：{gate['blocked_fields']}"
            )
        cells: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        futures: dict[Future[list[dict[str, Any]]], int] = {}
        with ThreadPoolExecutor(
            max_workers=int(config["parallel"]["max_outer_concurrency"]),
            thread_name_prefix="genis-tail-q0",
        ) as executor:
            for outer_scene in range(1, 9):
                future = executor.submit(
                    _run_outer_scene,
                    config,
                    corrected_config,
                    output_root,
                    outer_scene,
                    scenarios,
                    scenario_keys,
                    benign,
                    benign_keys,
                    train_mask,
                    calibration_mask,
                    test_mask,
                    _canonical_sha(split_receipt),
                )
                futures[future] = outer_scene
            for future in as_completed(futures):
                outer_scene = futures[future]
                try:
                    cells.extend(future.result())
                except Exception as error:
                    failures.append(
                        {
                            "outer_test_scene": outer_scene,
                            "failure_type": type(error).__name__,
                            "detail": str(error),
                        }
                    )
                _status(
                    output_root,
                    "RUNNING",
                    "parallel-outer-scenes",
                    completed_evaluation_units=len(cells),
                    failed_outer_scenes=len(failures),
                    settled_outer_scenes=len(cells) // 14 + len(failures),
                    total_evaluation_units=112,
                )
                print(
                    f"OUTER_SETTLED scene={outer_scene} completed_units={len(cells)} "
                    f"failed_outer_scenes={len(failures)} total_units=112",
                    flush=True,
                )
        if failures:
            raise TailRankingQ0Error(f"外层场景任务失败：{failures}")
        cells.sort(
            key=lambda cell: (
                int(cell["outer_test_scene"]),
                MODEL_KEYS.index(str(cell["model"])),
                METHOD_KEYS.index(str(cell["method"])),
            )
        )
        if len(cells) != 112:
            raise TailRankingQ0Error(f"评价单元数错误：{len(cells)} != 112")
        summary = _aggregate_cells(cells)
        decision = _decision(summary)
        results = {
            "schema_version": "genis-support-shrunk-tail-ranking-q0-results-v1",
            "run_id": config["run_id"],
            "protocol_id": config["contract_version"],
            "data_summary": data_summary,
            "split_receipt": split_receipt,
            "feature_gate_summary": {
                "blocked": False,
                "diagnostics_sha256": gate["diagnostics_sha256"],
                "threshold": gate["threshold"],
            },
            "parallel_execution": {
                "max_outer_concurrency": 2,
                "max_xgboost_concurrency": 1,
                "random_forest_n_jobs": 4,
                "total_evaluation_units": 112,
                "unrelated_gpu_processes_allowed": True,
                "memory_admission_gate": False,
            },
            "cells": cells,
            "model_method_summary": summary,
            "mechanical_decision": decision,
            "runtime": {
                "elapsed_seconds": time.monotonic() - started,
                "completed_evaluation_units": len(cells),
                "peak_rss_gib": _peak_rss_gib(),
            },
            "persistence_audit": {
                "feature_matrices_written": False,
                "labels_written": False,
                "stable_keys_written": False,
                "fold_memberships_written": False,
                "sample_weights_written": False,
                "per_sample_probabilities_written": False,
                "complete_models_written": False,
                "aggregate_metrics_written": True,
                "model_summaries_written": True,
                "status_logs_and_hashes_written": True,
            },
            **EVIDENCE,
        }
        _write_json(output_root / "results.json", results)
        _status(
            output_root,
            "FINISHED",
            "support-shrunk-tail-ranking-q0-complete",
            completed_evaluation_units=112,
            total_evaluation_units=112,
            candidate_advanced=decision["advanced"],
        )
        return results
    except Exception as error:
        _status(
            output_root,
            "FAILED",
            "support-shrunk-tail-ranking-q0",
            failure_type=type(error).__name__,
            detail=str(error),
        )
        raise


def swanlab_publish(
    config_path: Path, authorized_workspace: str, authorized_project: str
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config, _ = _load_config(config_path)
    output_root = _resolve(config_path, str(config["paths"]["run_root"]))
    destination = config["swanlab"]
    if (
        authorized_workspace != destination["workspace"]
        or authorized_project != destination["project"]
    ):
        raise TailRankingQ0Error("SwanLab 目的地未获授权")
    status = _read_json(output_root / "status.json")
    results = _read_json(output_root / "results.json")
    if status.get("state") != "FINISHED" or len(results.get("cells", [])) != 112:
        raise TailRankingQ0Error("只允许发布 112 单元全部完成的聚合结果")
    upload: dict[str, float] = {}
    for model_key in MODEL_KEYS:
        for method in METHOD_KEYS:
            prefix = f"{model_key}/{method}"
            method_summary = results["model_method_summary"][model_key][method]
            for metric, aggregates in method_summary.items():
                for aggregate, value in aggregates.items():
                    if isinstance(value, (int, float)):
                        upload[f"{prefix}/{metric}/{aggregate}"] = float(value)
    upload["decision/candidate_advanced"] = float(
        results["mechanical_decision"]["advanced"]
    )
    import swanlab

    swanlab.init(
        workspace=authorized_workspace,
        project=authorized_project,
        experiment_name=destination["run_name"],
        mode="online",
        config={
            "dataset": "GeNIS-v1.0.0",
            "protocol_id": config["contract_version"],
            "total_evaluation_units": 112,
            "max_outer_concurrency": 2,
            "max_xgboost_concurrency": 1,
            "seed": 42,
            **EVIDENCE,
        },
    )
    swanlab.log(upload)
    swanlab.finish()
    receipt = {
        "workspace": authorized_workspace,
        "project": authorized_project,
        "run_name": destination["run_name"],
        "uploaded_scalar_count": len(upload),
        "aggregate_only": True,
        **EVIDENCE,
    }
    _write_json(output_root / "swanlab_publish_receipt.json", receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="运行 Q0 的 112 个评价单元")
    run_parser.add_argument("--config", type=Path, required=True)
    publish = subparsers.add_parser("swanlab-publish", help="上传聚合指标与协议元数据")
    publish.add_argument("--config", type=Path, required=True)
    publish.add_argument("--authorized-workspace", required=True)
    publish.add_argument("--authorized-project", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            run(args.config)
        else:
            swanlab_publish(args.config, args.authorized_workspace, args.authorized_project)
    except (TailRankingQ0Error, corrected.CorrectedTrackBError) as error:
        print(f"GeNIS 支持量收缩尾部排序 Q0 失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
