"""GeNIS 60 秒跨场景留出无物化强基线。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import resource
import sys
import time
import warnings
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np


class ScenarioHoldoutError(RuntimeError):
    """表示数据合同或实验身份被破坏。"""


EVIDENCE = {
    "screening_only": True,
    "formal_paper_evidence": False,
    "official_test_accessed": False,
    "final_accessed": False,
}
MODEL_KEYS = ("xgboost", "random_forest")
STABLE_FIELDS = (
    "FlowID",
    "Rank",
    "StartTime",
    "LastTime",
    "Proto",
    "SrcAddr",
    "Sport",
    "DstAddr",
    "Dport",
)
LABEL_FIELDS = ("BinaryLabel", "CategoryLabel", "SubCategoryLabel")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ScenarioHoldoutError(f"无法读取配置：{path}：{error}") from error
    if not isinstance(value, dict):
        raise ScenarioHoldoutError("配置顶层必须是对象")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    partial.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    partial.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _resolve(config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (config_path.resolve().parent.parent / path).resolve()


def _load_config(path: Path) -> dict[str, Any]:
    config = _read_json(path)
    required = {
        "schema_version",
        "contract_version",
        "run_id",
        "seed",
        "data",
        "feature_budget",
        "models",
        "evaluation",
        "paths",
        "swanlab",
        "evidence",
    }
    if set(config) < required:
        raise ScenarioHoldoutError(f"配置缺少字段：{sorted(required - set(config))}")
    if (
        config["schema_version"] != "genis-scenario-holdout-baseline-config-v1"
        or config["contract_version"]
        != "attack_scenario_holdout_with_disjoint_benign_pool_v1"
        or config["seed"] != 42
        or config["evidence"] != EVIDENCE
        or len(config["data"]["scenario_members"]) != 8
        or len(config["data"]["benign_members"]) != 3
        or set(config["models"]) != set(MODEL_KEYS)
        or config["evaluation"]["outer_scene_count"] != 8
        or config["evaluation"]["budget_fp_per_10000"] != 10
    ):
        raise ScenarioHoldoutError("配置身份、模型或评价合同错误")
    fields = config["feature_budget"]["fields"]
    if len(fields) != len(set(fields)) or set(fields) & set(STABLE_FIELDS + LABEL_FIELDS):
        raise ScenarioHoldoutError("安全字段清单重复或包含身份、标签字段")
    return config


def _status(root: Path, state: str, stage: str, **extra: Any) -> None:
    _write_json(
        root / "status.json",
        {
            "schema_version": "genis-scenario-holdout-baseline-status-v1",
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


def _length_prefixed_hash(values: Sequence[str]) -> bytes:
    digest = hashlib.sha256()
    for value in values:
        raw = value.encode("utf-8")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.digest()


def _domain_bucket(domain: str, key: bytes, modulo: int) -> int:
    digest = hashlib.sha256(domain.encode("utf-8") + key).digest()
    return int.from_bytes(digest[:8], "big") % modulo


def _rows(path: Path, member: str) -> tuple[list[str], Any]:
    archive = zipfile.ZipFile(path, "r")
    try:
        raw = archive.open(member, "r")
    except KeyError as error:
        archive.close()
        raise ScenarioHoldoutError(f"归档缺少成员：{member}") from error
    text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
    reader = csv.reader(text)
    try:
        header = next(reader)
    except StopIteration as error:
        text.close()
        archive.close()
        raise ScenarioHoldoutError(f"成员为空：{member}") from error

    def iterator() -> Any:
        try:
            yield from reader
        finally:
            text.close()
            archive.close()

    return header, iterator()


def _parse_feature(token: str, row_number: int, field: str) -> float:
    if token == "":
        return math.nan
    try:
        value = float(token)
    except ValueError as error:
        raise ScenarioHoldoutError(
            f"第 {row_number} 行安全数值字段 {field} 无法解析"
        ) from error
    return value if math.isfinite(value) else math.nan


def _validate_archive(path: Path, spec: Mapping[str, Any]) -> None:
    if not path.is_file() or path.stat().st_size != int(spec["bytes"]):
        raise ScenarioHoldoutError(f"原始 ZIP 不存在或字节数错误：{path}")
    if _sha256(path) != spec["sha256"]:
        raise ScenarioHoldoutError(f"原始 ZIP SHA-256 错误：{path}")


def _load_data(
    config: Mapping[str, Any], flows_path: Path, scenarios_path: Path
) -> tuple[dict[int, np.ndarray], np.ndarray, np.ndarray, dict[str, Any]]:
    _validate_archive(flows_path, config["data"]["flows_archive"])
    _validate_archive(scenarios_path, config["data"]["scenarios_archive"])
    fields = list(config["feature_budget"]["fields"])
    reference_header: list[str] | None = None
    scenario_rows: dict[int, list[np.ndarray]] = {scene: [] for scene in range(1, 9)}
    malicious_keys: dict[bytes, tuple[int, bytes]] = {}
    source_rows: dict[str, int] = {}
    for scene_text, member in config["data"]["scenario_members"].items():
        scene = int(scene_text)
        header, rows = _rows(scenarios_path, member)
        if reference_header is None:
            reference_header = header
        if header != reference_header or len(header) != 125 or header[-3:] != list(LABEL_FIELDS):
            raise ScenarioHoldoutError(f"场景成员模式不一致：{member}")
        index = {name: position for position, name in enumerate(header)}
        if any(name not in index for name in fields + list(STABLE_FIELDS)):
            raise ScenarioHoldoutError(f"场景成员缺少冻结字段：{member}")
        feature_positions = [index[name] for name in fields]
        stable_positions = [index[name] for name in STABLE_FIELDS]
        count = 0
        for row_number, row in enumerate(rows, start=2):
            if len(row) != 125 or row[index["BinaryLabel"]] not in {"0", "1"}:
                raise ScenarioHoldoutError(f"{member} 第 {row_number} 行模式或标签错误")
            if row[index["BinaryLabel"]] == "0":
                continue
            if row[index["CategoryLabel"]] == "benign":
                raise ScenarioHoldoutError(f"{member} 第 {row_number} 行三层标签冲突")
            key = _length_prefixed_hash([row[position] for position in stable_positions])
            observation = _length_prefixed_hash(row[:-3])
            previous = malicious_keys.get(key)
            if previous is not None and previous[0] != scene:
                raise ScenarioHoldoutError("恶意稳定键跨两个攻击场景")
            if previous is not None and previous[1] != observation:
                raise ScenarioHoldoutError("同场景恶意稳定键存在观测冲突")
            if previous is not None:
                continue
            malicious_keys[key] = (scene, observation)
            scenario_rows[scene].append(
                np.asarray(
                    [
                        _parse_feature(row[position], row_number, fields[offset])
                        for offset, position in enumerate(feature_positions)
                    ],
                    dtype=np.float32,
                )
            )
            count += 1
        source_rows[member] = count
    benign_rows: dict[bytes, tuple[bytes, np.ndarray]] = {}
    for member in config["data"]["benign_members"]:
        header, rows = _rows(flows_path, member)
        if header != reference_header:
            raise ScenarioHoldoutError(f"良性成员模式不一致：{member}")
        index = {name: position for position, name in enumerate(header)}
        feature_positions = [index[name] for name in fields]
        stable_positions = [index[name] for name in STABLE_FIELDS]
        count = 0
        for row_number, row in enumerate(rows, start=2):
            if len(row) != 125 or row[index["BinaryLabel"]] != "0":
                raise ScenarioHoldoutError(f"{member} 第 {row_number} 行不是合法良性样本")
            if row[index["CategoryLabel"]] != "benign":
                raise ScenarioHoldoutError(f"{member} 第 {row_number} 行三层标签冲突")
            key = _length_prefixed_hash([row[position] for position in stable_positions])
            observation = _length_prefixed_hash(row[:-3])
            feature = np.asarray(
                [
                    _parse_feature(row[position], row_number, fields[offset])
                    for offset, position in enumerate(feature_positions)
                ],
                dtype=np.float32,
            )
            previous = benign_rows.setdefault(key, (observation, feature))
            if previous[0] != observation:
                raise ScenarioHoldoutError("良性稳定键存在观测冲突")
            count += 1
        source_rows[member] = count
    cross_role_keys = set(benign_rows).intersection(malicious_keys)
    if cross_role_keys:
        raise ScenarioHoldoutError("良性池与恶意场景存在稳定键交集")
    if reference_header is None or any(not rows for rows in scenario_rows.values()):
        raise ScenarioHoldoutError("攻击场景缺少恶意样本")
    scenario_features = {
        scene: np.vstack(rows).astype(np.float32, copy=False)
        for scene, rows in scenario_rows.items()
    }
    benign_keys = np.asarray(list(benign_rows), dtype="S32")
    benign_features = np.vstack([value[1] for value in benign_rows.values()]).astype(
        np.float32, copy=False
    )
    test_mask = np.fromiter(
        (_domain_bucket("genis-benign-test-v1", bytes(key), 5) == 0 for key in benign_keys),
        dtype=bool,
        count=len(benign_keys),
    )
    if np.count_nonzero(test_mask) < 1000:
        raise ScenarioHoldoutError("独立良性测试池不足 1000 行")
    summary = {
        "header_sha256": _canonical_sha(reference_header),
        "feature_budget_id": config["feature_budget"]["id"],
        "feature_count": len(fields),
        "feature_fields_sha256": _canonical_sha(fields),
        "source_rows": source_rows,
        "malicious_rows_by_scene": {
            str(scene): len(values) for scene, values in scenario_features.items()
        },
        "unique_malicious_keys": len(malicious_keys),
        "unique_benign_keys": len(benign_keys),
        "benign_development_rows": int(np.count_nonzero(~test_mask)),
        "benign_test_rows": int(np.count_nonzero(test_mask)),
        "persistent_feature_artifacts": False,
        **EVIDENCE,
    }
    return scenario_features, benign_features, benign_keys, summary


def _impute(train: np.ndarray, *others: np.ndarray) -> tuple[np.ndarray, ...]:
    median = np.nanmedian(train, axis=0)
    median = np.where(np.isfinite(median), median, 0.0).astype(np.float32)

    def apply(values: np.ndarray) -> np.ndarray:
        return np.where(np.isfinite(values), values, median).astype(np.float32, copy=False)

    return (apply(train), *(apply(values) for values in others))


def _balanced_weights(labels: np.ndarray) -> np.ndarray:
    counts = np.bincount(labels, minlength=2)
    if np.any(counts == 0):
        raise ScenarioHoldoutError("训练折缺少二分类中的一个类别")
    return np.asarray(len(labels) / (2.0 * counts[labels]), dtype=np.float32)


def _xgb_device(model: Any) -> str:
    config = json.loads(model.save_config())
    devices: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "device" and isinstance(child, str):
                    devices.append(child)
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)

    collect(config)
    if "cuda:0" not in devices:
        raise ScenarioHoldoutError(f"XGBoost 未绑定 cuda:0：{devices}")
    return "cuda:0"


def _fit(
    model_key: str,
    params: Mapping[str, Any],
    train_x: np.ndarray,
    train_y: np.ndarray,
    seed: int,
) -> tuple[Any, str]:
    weights = _balanced_weights(train_y)
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
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = xgb.train(
                xgb_params,
                xgb.DMatrix(train_x, label=train_y, weight=weights),
                num_boost_round=int(params["n_estimators"]),
            )
        messages = [str(item.message) for item in caught]
        if any("fallback" in item.lower() or "cpu" in item.lower() for item in messages):
            raise ScenarioHoldoutError(f"XGBoost 发生设备回退：{messages}")
        return model, _xgb_device(model)
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
    model.fit(train_x, train_y, sample_weight=weights)
    return model, "cpu"


def _predict(model_key: str, model: Any, values: np.ndarray) -> np.ndarray:
    if model_key == "xgboost":
        import xgboost as xgb

        probability = model.predict(xgb.DMatrix(values))
    else:
        probability = model.predict_proba(values)[:, 1]
    result = np.asarray(probability, dtype=np.float64)
    if result.shape != (len(values),) or not np.isfinite(result).all():
        raise ScenarioHoldoutError("预测概率形状错误或含非有限值")
    return result


def _save_model(model_key: str, model: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    if model_key == "xgboost":
        model.save_model(partial)
    else:
        import joblib

        joblib.dump(model, partial, compress=3)
    partial.replace(path)


def _threshold(scores: np.ndarray, budget: int) -> tuple[float, int]:
    if len(scores) == 0 or budget < 0:
        raise ScenarioHoldoutError("良性校准分数或预算无效")
    if budget == 0:
        return math.inf, 0
    unique, counts = np.unique(scores, return_counts=True)
    alarms = np.cumsum(counts[::-1])[::-1]
    valid = np.flatnonzero(alarms <= budget)
    if len(valid) == 0:
        return math.inf, 0
    index = int(valid[0])
    return float(unique[index]), int(alarms[index])


def _metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    from sklearn.metrics import (
        average_precision_score,
        confusion_matrix,
        f1_score,
        precision_score,
        recall_score,
    )

    prediction = np.asarray(scores >= 0.5, dtype=np.uint8)
    alarm = scores >= threshold
    benign = labels == 0
    malicious = labels == 1
    false_positive = int(np.count_nonzero(alarm & benign))
    true_positive = int(np.count_nonzero(alarm & malicious))
    return {
        "average_precision": float(average_precision_score(labels, scores)),
        "macro_f1": float(f1_score(labels, prediction, average="macro")),
        "malicious_f1": float(f1_score(labels, prediction, pos_label=1)),
        "malicious_precision": float(precision_score(labels, prediction, zero_division=0)),
        "malicious_recall": float(recall_score(labels, prediction, zero_division=0)),
        "recall_at_fixed_budget": true_positive / int(np.count_nonzero(malicious)),
        "false_alerts_per_10000_benign": (
            false_positive * 10000.0 / int(np.count_nonzero(benign))
        ),
        "threshold": threshold,
        "false_positives": false_positive,
        "true_positives": true_positive,
        "benign_rows": int(np.count_nonzero(benign)),
        "malicious_rows": int(np.count_nonzero(malicious)),
        "confusion_matrix_at_0.5": confusion_matrix(labels, prediction).astype(int).tolist(),
    }


def _aggregate(cells: Sequence[Mapping[str, Any]], metric: str) -> dict[str, float]:
    values = np.asarray([cell["metrics"][metric] for cell in cells], dtype=np.float64)
    return {
        "mean": float(values.mean()),
        "std": float(values.std(ddof=1)),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
    }


def run(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    flows_path = _resolve(config_path, config["data"]["flows_archive"]["path"])
    scenarios_path = _resolve(config_path, config["data"]["scenarios_archive"]["path"])
    output_root = _resolve(config_path, config["paths"]["run_root"])
    if output_root.exists():
        raise ScenarioHoldoutError("唯一运行根已存在，拒绝覆盖")
    output_root.mkdir(parents=True)
    _write_json(
        output_root / "run_binding.json",
        {
            "config_sha256": _sha256(config_path),
            "code_sha256": _sha256(Path(__file__).resolve()),
            "flows_archive_sha256": config["data"]["flows_archive"]["sha256"],
            "scenarios_archive_sha256": config["data"]["scenarios_archive"]["sha256"],
            "persistent_feature_artifacts": False,
            **EVIDENCE,
        },
    )
    _status(output_root, "RUNNING", "load-raw-zips", completed_fits=0, total_fits=16)
    started = time.monotonic()
    try:
        scenarios, benign, benign_keys, data_summary = _load_data(
            config, flows_path, scenarios_path
        )
        benign_test = np.fromiter(
            (
                _domain_bucket("genis-benign-test-v1", bytes(key), 5) == 0
                for key in benign_keys
            ),
            dtype=bool,
            count=len(benign_keys),
        )
        benign_cf = np.fromiter(
            (
                _domain_bucket("genis-benign-cf-v1", bytes(key), 7)
                for key in benign_keys
            ),
            dtype=np.uint8,
            count=len(benign_keys),
        )
        cells: list[dict[str, Any]] = []
        completed = 0
        for outer_scene in range(1, 9):
            calibration_fold = (outer_scene - 1) % 7
            train_benign_mask = (~benign_test) & (benign_cf != calibration_fold)
            calibration_mask = (~benign_test) & (benign_cf == calibration_fold)
            train_malicious = np.vstack(
                [values for scene, values in scenarios.items() if scene != outer_scene]
            )
            train_x_raw = np.vstack([benign[train_benign_mask], train_malicious])
            train_y = np.concatenate(
                [
                    np.zeros(np.count_nonzero(train_benign_mask), dtype=np.uint8),
                    np.ones(len(train_malicious), dtype=np.uint8),
                ]
            )
            calibration_x_raw = benign[calibration_mask]
            test_x_raw = np.vstack([benign[benign_test], scenarios[outer_scene]])
            test_y = np.concatenate(
                [
                    np.zeros(np.count_nonzero(benign_test), dtype=np.uint8),
                    np.ones(len(scenarios[outer_scene]), dtype=np.uint8),
                ]
            )
            for model_key in MODEL_KEYS:
                if model_key == "random_forest":
                    train_x, calibration_x, test_x = _impute(
                        train_x_raw, calibration_x_raw, test_x_raw
                    )
                else:
                    train_x, calibration_x, test_x = (
                        train_x_raw,
                        calibration_x_raw,
                        test_x_raw,
                    )
                fit_started = time.monotonic()
                model, device = _fit(
                    model_key,
                    config["models"][model_key],
                    train_x,
                    train_y,
                    int(config["seed"]) + outer_scene,
                )
                fit_seconds = time.monotonic() - fit_started
                calibration_scores = _predict(model_key, model, calibration_x)
                allowed = math.floor(
                    len(calibration_scores)
                    * int(config["evaluation"]["budget_fp_per_10000"])
                    / 10000
                )
                threshold, actual = _threshold(calibration_scores, allowed)
                predict_started = time.monotonic()
                test_scores = _predict(model_key, model, test_x)
                predict_seconds = time.monotonic() - predict_started
                extension = "ubj" if model_key == "xgboost" else "joblib"
                model_path = (
                    output_root
                    / "models"
                    / f"scene-{outer_scene}-{model_key}.{extension}"
                )
                _save_model(model_key, model, model_path)
                cell = {
                    "outer_test_scene": outer_scene,
                    "model": model_key,
                    "device": device,
                    "train_rows": len(train_y),
                    "train_benign_rows": int(np.count_nonzero(train_y == 0)),
                    "train_malicious_rows": int(np.count_nonzero(train_y == 1)),
                    "calibration_benign_rows": len(calibration_scores),
                    "calibration_allowed_false_positives": allowed,
                    "calibration_actual_false_positives": actual,
                    "fit_seconds": fit_seconds,
                    "predict_seconds": predict_seconds,
                    "model_sha256": _sha256(model_path),
                    "metrics": _metrics(test_y, test_scores, threshold),
                }
                cells.append(cell)
                completed += 1
                _write_json(
                    output_root / "cells" / f"scene-{outer_scene}-{model_key}.json",
                    cell,
                )
                _status(
                    output_root,
                    "RUNNING",
                    "scenario-holdout-baselines",
                    completed_fits=completed,
                    total_fits=16,
                    current_scene=outer_scene,
                    current_model=model_key,
                )
                print(
                    f"CELL_FINISHED scene={outer_scene} model={model_key} "
                    f"completed={completed}/16 elapsed={time.monotonic() - started:.3f}",
                    flush=True,
                )
        summary = {
            model_key: {
                metric: _aggregate(
                    [cell for cell in cells if cell["model"] == model_key], metric
                )
                for metric in (
                    "average_precision",
                    "macro_f1",
                    "malicious_recall",
                    "recall_at_fixed_budget",
                    "false_alerts_per_10000_benign",
                )
            }
            for model_key in MODEL_KEYS
        }
        results = {
            "schema_version": "genis-scenario-holdout-baseline-results-v1",
            "run_id": config["run_id"],
            "protocol_id": config["contract_version"],
            "data_summary": data_summary,
            "cells": cells,
            "model_summary": summary,
            "runtime": {
                "elapsed_seconds": time.monotonic() - started,
                "fit_count": completed,
                "peak_rss_gib": _peak_rss_gib(),
            },
            "persistence_audit": {
                "feature_matrices_written": False,
                "labels_written": False,
                "stable_keys_written": False,
                "fold_memberships_written": False,
                "per_sample_probabilities_written": False,
            },
            **EVIDENCE,
        }
        _write_json(output_root / "results.json", results)
        _status(
            output_root,
            "FINISHED",
            "scenario-holdout-baselines-complete",
            completed_fits=completed,
            total_fits=16,
        )
        return results
    except Exception as error:
        _status(
            output_root,
            "FAILED",
            "scenario-holdout-baselines",
            failure_type=type(error).__name__,
            detail=str(error),
        )
        raise


def swanlab_publish(
    config_path: Path, authorized_workspace: str, authorized_project: str
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    output_root = _resolve(config_path, config["paths"]["run_root"])
    destination = config["swanlab"]
    if (
        authorized_workspace != destination["workspace"]
        or authorized_project != destination["project"]
    ):
        raise ScenarioHoldoutError("SwanLab 目的地未获授权")
    status = _read_json(output_root / "status.json")
    results = _read_json(output_root / "results.json")
    if status.get("state") != "FINISHED" or results.get("final_accessed") is not False:
        raise ScenarioHoldoutError("只允许发布已完成的聚合结果")
    upload: dict[str, float] = {}
    for cell in results["cells"]:
        prefix = f"scene-{cell['outer_test_scene']}/{cell['model']}"
        for name, value in cell["metrics"].items():
            if isinstance(value, (int, float)):
                upload[f"{prefix}/{name}"] = float(value)
        upload[f"{prefix}/fit_seconds"] = float(cell["fit_seconds"])
        upload[f"{prefix}/predict_seconds"] = float(cell["predict_seconds"])
    import swanlab

    swanlab.init(
        workspace=authorized_workspace,
        project=authorized_project,
        experiment_name=destination["run_name"],
        mode="online",
        config={
            "dataset": "GeNIS-v1.0.0",
            "protocol_id": config["contract_version"],
            "seed": config["seed"],
            **EVIDENCE,
        },
    )
    swanlab.log(upload)
    swanlab.finish()
    receipt = {
        "workspace": authorized_workspace,
        "project": authorized_project,
        "uploaded_scalar_count": len(upload),
        **EVIDENCE,
    }
    _write_json(output_root / "swanlab_publish_receipt.json", receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="运行跨场景留出强基线")
    run_parser.add_argument("--config", type=Path, required=True)
    publish = subparsers.add_parser("swanlab-publish", help="上传白名单聚合指标")
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
            swanlab_publish(
                args.config, args.authorized_workspace, args.authorized_project
            )
    except ScenarioHoldoutError as error:
        print(f"跨场景基线失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
