"""C12 Q0 跨年度共同表格输入上的 CPU 强基线。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, f1_score, precision_score, recall_score

PROJECT = "malicious-traffic-llm"
WORKSPACE = "mortiswang"
ROLES = ("source-train", "source-validation", "target-prefix", "target-development")
FEATURE_ARRAYS = ("x_value", "x_missing", "delta_t_us")
MODELS = ("hgb", "random_forest", "xgboost")


class CrossyearTabularError(ValueError):
    """缓存或运行状态不符合跨年度 Q0 合同。"""


def _json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CrossyearTabularError(f"JSON 顶层必须是对象：{path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _load_cache(cache_manifest: Path) -> tuple[Path, Mapping[str, Any], dict[str, dict[str, np.ndarray]]]:
    manifest = _json(cache_manifest)
    if manifest.get("final_accessed") is not False:
        raise CrossyearTabularError("缓存收据必须声明 final_accessed=false")
    root = Path(str(manifest.get("formal_cache_root", ""))).resolve()
    if cache_manifest.resolve().parent != root:
        raise CrossyearTabularError("缓存收据不在 formal_cache_root 内")
    raw_arrays = manifest.get("arrays")
    if not isinstance(raw_arrays, dict) or set(raw_arrays) != set(ROLES):
        raise CrossyearTabularError("缓存收据必须含四个角色的 arrays 清单")
    loaded: dict[str, dict[str, np.ndarray]] = {}
    for role in ROLES:
        entries = raw_arrays[role]
        if not isinstance(entries, dict):
            raise CrossyearTabularError(f"{role} arrays 清单不合法")
        required = set(FEATURE_ARRAYS)
        if role in ("source-train", "source-validation"):
            required.add("labels")
        if role == "target-development":
            required.add("sample_id")
        if not required.issubset(entries):
            raise CrossyearTabularError(f"{role} 缺少必要数组：{sorted(required.difference(entries))}")
        role_arrays: dict[str, np.ndarray] = {}
        expected_rows: int | None = None
        for name, record in entries.items():
            if not isinstance(record, dict):
                raise CrossyearTabularError(f"{role}.{name} 清单不合法")
            path = Path(str(record.get("path", ""))).resolve()
            if not _within(path, root) or path.is_symlink() or not path.is_file():
                raise CrossyearTabularError(f"{role}.{name} 不在正式缓存根或不是普通文件")
            if _sha256(path) != record.get("sha256"):
                raise CrossyearTabularError(f"{role}.{name} SHA-256 不匹配")
            array = np.load(path, mmap_mode="r", allow_pickle=False)
            if list(array.shape) != record.get("shape") or str(array.dtype) != record.get("dtype"):
                raise CrossyearTabularError(f"{role}.{name} shape 或 dtype 不匹配")
            if expected_rows is None:
                expected_rows = int(array.shape[0])
            elif int(array.shape[0]) != expected_rows:
                raise CrossyearTabularError(f"{role} 数组行数不一致")
            role_arrays[name] = array
        loaded[role] = role_arrays
    target_evaluation = manifest.get("target_development_evaluation")
    if not isinstance(target_evaluation, dict) or not isinstance(target_evaluation.get("labels"), dict):
        raise CrossyearTabularError("缓存收据缺少目标开发标签旁车登记")
    label_record = target_evaluation["labels"]
    label_path = Path(str(label_record.get("path", ""))).resolve()
    if not _within(label_path, root) or label_path.is_symlink() or not label_path.is_file():
        raise CrossyearTabularError("目标开发标签旁车不在正式缓存根或不是普通文件")
    if _sha256(label_path) != label_record.get("sha256"):
        raise CrossyearTabularError("目标开发标签旁车 SHA-256 不匹配")
    return root, manifest, loaded


def _features(arrays: Mapping[str, np.ndarray]) -> np.ndarray:
    values = np.asarray(arrays["x_value"], dtype=np.float32)
    missing = np.asarray(arrays["x_missing"], dtype=np.float32)
    delta = np.log1p(np.maximum(np.asarray(arrays["delta_t_us"], dtype=np.float64), 0.0)).astype(np.float32)[:, None]
    if values.ndim != 2 or values.shape[1] != 77 or missing.shape != values.shape:
        raise CrossyearTabularError("共同输入必须为 x_value(77)+x_missing(77)+log1p(delta_t_us)")
    result = np.concatenate((values, missing, delta), axis=1)
    if result.shape[1] != 155 or not np.isfinite(result).all():
        raise CrossyearTabularError("155 维共同输入含非法数值")
    return result


def _model(name: str, seed: int) -> Any:
    if name == "hgb":
        return HistGradientBoostingClassifier(learning_rate=0.08, max_iter=200, max_leaf_nodes=63, l2_regularization=0.1, early_stopping=False, random_state=seed)
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=128, max_depth=10, bootstrap=True, n_jobs=4, class_weight="balanced_subsample", random_state=seed)
    if name == "xgboost":
        try:
            from xgboost import XGBClassifier
        except (ImportError, OSError) as error:
            raise CrossyearTabularError(f"XGBoost 不可用，已跳过：{error}") from error
        return XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.08, subsample=0.8, colsample_bytree=0.9, objective="binary:logistic", eval_metric="logloss", n_jobs=4, random_state=seed, tree_method="hist", device="cpu", verbosity=0)
    raise CrossyearTabularError(f"未知模型：{name}")


def _ece(y: np.ndarray, probability: np.ndarray, bins: int = 15) -> float:
    total = len(y)
    value = 0.0
    for lower, upper in zip(np.linspace(0, 1, bins, endpoint=False), np.linspace(1 / bins, 1, bins)):
        mask = (probability >= lower) & (probability < upper if upper < 1 else probability <= upper)
        if mask.any():
            value += float(mask.mean()) * abs(float(probability[mask].mean()) - float(y[mask].mean()))
    return value


def _metrics(y: np.ndarray, probability: np.ndarray, threshold: float) -> dict[str, Any]:
    predicted = (probability >= threshold).astype(np.uint8)
    return {
        "threshold": threshold,
        "pr_auc": float(average_precision_score(y, probability)),
        "macro_f1": float(f1_score(y, predicted, average="macro", zero_division=0)),
        "malicious_f1": float(f1_score(y, predicted, pos_label=1, zero_division=0)),
        "precision": float(precision_score(y, predicted, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y, predicted, pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
        "brier": float(brier_score_loss(y, probability)),
        "ece": _ece(y, probability),
    }


def _thresholds(y: np.ndarray, probability: np.ndarray) -> dict[str, Any]:
    labels = np.asarray(y, dtype=np.uint8)
    scores = np.asarray(probability, dtype=np.float64)
    if labels.ndim != 1 or scores.ndim != 1 or labels.shape != scores.shape or not len(labels):
        raise CrossyearTabularError("阈值扫描要求非空且等长的一维标签与概率")
    if not np.isfinite(scores).all() or bool((scores < 0.0).any()) or bool((scores > 1.0).any()):
        raise CrossyearTabularError("阈值扫描概率必须位于 [0, 1]")
    if not np.isin(labels, (0, 1)).all():
        raise CrossyearTabularError("阈值扫描标签必须为二元 0/1")

    # 稳定排序后按同分概率整体累加，避免逐个阈值重复扫描全部样本。
    order = np.argsort(-scores, kind="stable")
    sorted_scores = scores[order]
    sorted_labels = labels[order]
    positives = int(sorted_labels.sum())
    negatives = len(sorted_labels) - positives
    true_positive = 0
    false_positive = 0
    offset = 0
    best_score = -1.0
    best_threshold = 0.0

    def consider(threshold: float) -> None:
        nonlocal best_score, best_threshold
        false_negative = positives - true_positive
        true_negative = negatives - false_positive
        positive_denominator = 2 * true_positive + false_positive + false_negative
        negative_denominator = 2 * true_negative + false_positive + false_negative
        positive_f1 = 0.0 if positive_denominator == 0 else 2 * true_positive / positive_denominator
        negative_f1 = 0.0 if negative_denominator == 0 else 2 * true_negative / negative_denominator
        macro_f1 = (positive_f1 + negative_f1) / 2.0
        if macro_f1 > best_score or (macro_f1 == best_score and threshold > best_threshold):
            best_score = macro_f1
            best_threshold = threshold

    endpoints = (1.0, 0.5, 0.0)
    endpoint_offset = 0
    while offset < len(sorted_scores):
        threshold = float(sorted_scores[offset])
        while endpoint_offset < len(endpoints) and endpoints[endpoint_offset] > threshold:
            consider(endpoints[endpoint_offset])
            endpoint_offset += 1
        group_end = offset + 1
        while group_end < len(sorted_scores) and sorted_scores[group_end] == sorted_scores[offset]:
            group_end += 1
        group_labels = sorted_labels[offset:group_end]
        group_positive = int(group_labels.sum())
        true_positive += group_positive
        false_positive += (group_end - offset) - group_positive
        consider(threshold)
        while endpoint_offset < len(endpoints) and endpoints[endpoint_offset] == threshold:
            consider(endpoints[endpoint_offset])
            endpoint_offset += 1
        offset = group_end
    while endpoint_offset < len(endpoints):
        consider(endpoints[endpoint_offset])
        endpoint_offset += 1
    benign = int((y == 0).sum())
    return {"0.5": 0.5, "source_validation_macro_f1_optimal": best_threshold, "source_validation_macro_f1": best_score, "per_million_100_false_positive": {"status": "diagnostic_not_adjudicable" if benign < 10_000 else "diagnostic", "benign_count": benign, "reason": "源验证良性样本不足以稳定估计每百万 100 误报阈值" if benign < 10_000 else "仅诊断，不用于 Q0 模型选择"}}


def _swanlab_log(run_name: str, config: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    try:
        import swanlab

        run = swanlab.init(project=PROJECT, workspace=WORKSPACE, name=run_name, config=dict(config), mode="online")
        swanlab.log({key: value for key, value in metrics.items() if isinstance(value, (int, float))})
        run.finish()
        return "online"
    except Exception as error:  # 在线跟踪不能丢失本地证据。
        return f"failed:{type(error).__name__}:{error}"


def run(*, cache_manifest: Path, output_dir: Path, seed: int, model_name: str) -> Mapping[str, Any]:
    if output_dir.exists():
        raise CrossyearTabularError(f"输出目录已存在，拒绝覆盖：{output_dir}")
    cache_root, manifest, arrays = _load_cache(cache_manifest)
    output_dir.mkdir(parents=True)
    _write_json(output_dir / "run_state.json", {"state": "running", "model": model_name, "seed": seed, "final_accessed": False})
    train_x, validation_x, target_x = (_features(arrays[role]) for role in ("source-train", "source-validation", "target-development"))
    train_y = np.asarray(arrays["source-train"]["labels"], dtype=np.uint8)
    validation_y = np.asarray(arrays["source-validation"]["labels"], dtype=np.uint8)
    if set(np.unique(train_y)) != {0, 1}:
        raise CrossyearTabularError("source-train 必须同时含良性与恶意标签")
    model = _model(model_name, seed)
    started = time.perf_counter()
    model.fit(train_x, train_y)
    training_seconds = time.perf_counter() - started
    validation_probability = model.predict_proba(validation_x)[:, 1]
    thresholds = _thresholds(validation_y, validation_probability)
    inference_started = time.perf_counter()
    target_probability = model.predict_proba(target_x)[:, 1].astype(np.float32)
    inference_seconds = time.perf_counter() - inference_started
    np.save(output_dir / "target_development_probability.npy", target_probability, allow_pickle=False)
    sample_hash = hashlib.sha256(np.asarray(arrays["target-development"]["sample_id"]).tobytes()).hexdigest()
    probability_hash = _sha256(output_dir / "target_development_probability.npy")
    _write_json(output_dir / "probability_seal.json", {"sample_id_sha256": sample_hash, "probability_sha256": probability_hash, "row_count": int(target_probability.shape[0]), "target_labels_opened_after_seal": True})
    target_label_record = manifest["target_development_evaluation"]["labels"]
    target_labels = np.load(Path(str(target_label_record["path"])), mmap_mode="r", allow_pickle=False)
    if list(target_labels.shape) != target_label_record.get("shape") or str(target_labels.dtype) != target_label_record.get("dtype"):
        raise CrossyearTabularError("目标开发标签旁车 shape 或 dtype 不匹配")
    target_labels = np.asarray(target_labels, dtype=np.uint8)
    if target_labels.shape[0] != target_probability.shape[0]:
        raise CrossyearTabularError("目标开发标签旁车与已封存概率行数不一致")
    report = {"model": model_name, "seed": seed, "workspace": WORKSPACE, "project": PROJECT, "cache_manifest_sha256": _sha256(cache_manifest), "formal_cache_root": str(cache_root), "input_dimension": 155, "input_definition": "x_value(77)+x_missing(77)+log1p(delta_t_us)", "row_counts": {role: int(arrays[role]["x_value"].shape[0]) for role in ROLES}, "thresholds": thresholds, "source_validation": {key: _metrics(validation_y, validation_probability, value) for key, value in thresholds.items() if isinstance(value, float)}, "target_development": {key: _metrics(target_labels, target_probability, value) for key, value in thresholds.items() if isinstance(value, float)}, "resource": {"training_seconds": training_seconds, "inference_seconds": inference_seconds, "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, "platform": platform.platform()}, "probability_seal": {"sample_id_sha256": sample_hash, "probability_sha256": probability_hash}, "final_accessed": False}
    run_name = f"c12-q0-crossyear-{model_name}-seed{seed}"
    tracking = _swanlab_log(run_name, {"model": model_name, "seed": seed, "data_counts": report["row_counts"], "input_dimension": 155}, {"target_pr_auc": report["target_development"]["0.5"]["pr_auc"], "target_macro_f1": report["target_development"]["source_validation_macro_f1_optimal"]["macro_f1"], "training_seconds": training_seconds, "inference_seconds": inference_seconds})
    report["swanlab"] = {"workspace": WORKSPACE, "project": PROJECT, "run_name": run_name, "status": tracking}
    _write_json(output_dir / "metrics.json", report)
    _write_json(output_dir / "run_state.json", {"state": "finished", "model": model_name, "seed": seed, "final_accessed": False, "metrics": "metrics.json"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 C12 Q0 跨年度表格强基线")
    parser.add_argument("--cache-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    try:
        result = run(cache_manifest=args.cache_manifest, output_dir=args.output_dir, seed=args.seed, model_name=args.model)
    except CrossyearTabularError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
