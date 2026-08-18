"""GeNIS corrected Track B v2 同源跨场景并行强基线。"""

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
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np


class CorrectedTrackBError(RuntimeError):
    """表示 corrected Track B v2 的数据或运行合同被破坏。"""


EVIDENCE = {
    "screening_only": True,
    "formal_paper_evidence": False,
    "official_test_accessed": False,
    "final_accessed": False,
}
MODEL_KEYS = ("xgboost", "random_forest")
EXPECTED_MODELS = {
    "xgboost": {
        "n_estimators": 300,
        "max_depth": 8,
        "learning_rate": 0.1,
        "subsample": 1.0,
        "colsample_bytree": 0.9,
        "min_child_weight": 1,
        "reg_lambda": 1.0,
        "nthread": 8,
    },
    "random_forest": {
        "n_estimators": 300,
        "max_depth": None,
        "max_features": "sqrt",
        "min_samples_leaf": 1,
        "n_jobs": 4,
    },
}
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
PERMANENTLY_EXCLUDED_FIELDS = ("IdleTime",)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CorrectedTrackBError(f"无法读取 JSON：{path}：{error}") from error
    if not isinstance(value, dict):
        raise CorrectedTrackBError("JSON 顶层必须是对象")
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
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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
        "feature_gate",
        "feature_budget",
        "partition",
        "parallel",
        "models",
        "evaluation",
        "paths",
        "swanlab",
        "evidence",
    }
    if set(config) < required:
        raise CorrectedTrackBError(f"配置缺少字段：{sorted(required - set(config))}")
    fields = config["feature_budget"]["fields"]
    parallel = config["parallel"]
    partition = config["partition"]
    if (
        config["schema_version"] != "genis-corrected-track-b-config-v2"
        or config["contract_version"] != "corrected-v2"
        or config["seed"] != 42
        or config["evidence"] != EVIDENCE
        or config["models"] != EXPECTED_MODELS
        or len(config["data"]["scenario_members"]) != 8
        or config["evaluation"]["outer_scene_count"] != 8
        or config["evaluation"]["budget_fp_per_10000"] != 10
        or config["feature_gate"]["block_auc_gte"] != 0.98
        or parallel["max_concurrency"] != 3
        or parallel["total_unit_count"] != 16
        or parallel["total_cpu_thread_budget"] != 16
        or partition["modulo"] != 10
        or partition["train_buckets"] != [0, 1, 2, 3, 4, 5]
        or partition["calibration_buckets"] != [6, 7]
        or partition["test_buckets"] != [8, 9]
        or config["feature_budget"]["permanently_excluded_fields"] != ["IdleTime"]
    ):
        raise CorrectedTrackBError("配置身份、并行、分区或评价合同错误")
    forbidden = set(STABLE_FIELDS + LABEL_FIELDS + PERMANENTLY_EXCLUDED_FIELDS)
    if len(fields) != len(set(fields)) or set(fields) & forbidden:
        raise CorrectedTrackBError("字段清单重复或含稳定键、标签、IdleTime")
    if config["models"]["random_forest"]["n_jobs"] * 3 > 16:
        raise CorrectedTrackBError("随机森林并行线程可能超过总 CPU 预算")
    return config


def _status(root: Path, state: str, stage: str, **extra: Any) -> None:
    _write_json(
        root / "status.json",
        {
            "schema_version": "genis-corrected-track-b-status-v2",
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


def _partition_bucket(domain: str, key: bytes, modulo: int) -> int:
    digest = hashlib.sha256(domain.encode("utf-8") + key).digest()
    return int.from_bytes(digest[:8], "big") % modulo


def _keyset_sha(keys: Sequence[bytes]) -> str:
    digest = hashlib.sha256()
    for key in sorted(keys):
        digest.update(key)
    return digest.hexdigest()


def _rows(path: Path, member: str) -> tuple[list[str], Any]:
    archive = zipfile.ZipFile(path, "r")
    try:
        raw = archive.open(member, "r")
    except KeyError as error:
        archive.close()
        raise CorrectedTrackBError(f"归档缺少成员：{member}") from error
    text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
    reader = csv.reader(text)
    try:
        header = next(reader)
    except StopIteration as error:
        text.close()
        archive.close()
        raise CorrectedTrackBError(f"成员为空：{member}") from error

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
        raise CorrectedTrackBError(
            f"第 {row_number} 行数值字段 {field} 无法解析"
        ) from error
    return value if math.isfinite(value) else math.nan


def _validate_archive(path: Path, spec: Mapping[str, Any]) -> None:
    if not path.is_file() or path.stat().st_size != int(spec["bytes"]):
        raise CorrectedTrackBError(f"原始 ZIP 不存在或字节数错误：{path}")
    if _sha256(path) != spec["sha256"]:
        raise CorrectedTrackBError(f"原始 ZIP SHA-256 错误：{path}")


def _representative_key(observation: bytes, member: str) -> tuple[bytes, str]:
    return observation, member


def _load_same_source_data(
    config: Mapping[str, Any], archive_path: Path
) -> tuple[
    dict[int, np.ndarray],
    dict[int, np.ndarray],
    np.ndarray,
    np.ndarray,
    np.ndarray,
    dict[str, Any],
]:
    _validate_archive(archive_path, config["data"]["scenarios_archive"])
    fields = list(config["feature_budget"]["fields"])
    reference_header: list[str] | None = None
    # stable_key -> (label, scene, observation, member, feature, observation_count)
    representatives: dict[bytes, tuple[int, int, bytes, str, np.ndarray, int]] = {}
    source_rows: dict[str, dict[str, int]] = {}
    duplicate_observations = 0
    variant_observations = 0
    for scene_text, member in sorted(
        config["data"]["scenario_members"].items(), key=lambda item: int(item[0])
    ):
        scene = int(scene_text)
        header, rows = _rows(archive_path, member)
        if reference_header is None:
            reference_header = header
        if header != reference_header or len(header) != 125 or header[-3:] != list(LABEL_FIELDS):
            raise CorrectedTrackBError(f"场景成员模式不一致：{member}")
        index = {name: position for position, name in enumerate(header)}
        required = fields + list(STABLE_FIELDS) + list(LABEL_FIELDS)
        if any(name not in index for name in required):
            raise CorrectedTrackBError(f"场景成员缺少冻结字段：{member}")
        positions = [index[name] for name in fields]
        stable_positions = [index[name] for name in STABLE_FIELDS]
        counts = {"rows": 0, "benign": 0, "malicious": 0}
        for row_number, row in enumerate(rows, start=2):
            if len(row) != 125 or row[index["BinaryLabel"]] not in {"0", "1"}:
                raise CorrectedTrackBError(f"{member} 第 {row_number} 行模式或标签错误")
            label = int(row[index["BinaryLabel"]])
            category = row[index["CategoryLabel"]]
            if (label == 0 and category != "benign") or (label == 1 and category == "benign"):
                raise CorrectedTrackBError(f"{member} 第 {row_number} 行三层标签冲突")
            key = _length_prefixed_hash([row[position] for position in stable_positions])
            observation = _length_prefixed_hash(row[:-3])
            feature = np.asarray(
                [
                    _parse_feature(row[position], row_number, fields[offset])
                    for offset, position in enumerate(positions)
                ],
                dtype=np.float32,
            )
            previous = representatives.get(key)
            if previous is not None:
                if previous[0] != label:
                    raise CorrectedTrackBError("同一稳定键存在标签冲突")
                if label == 1 and previous[1] != scene:
                    raise CorrectedTrackBError("恶意稳定键跨两个攻击场景")
                duplicate_observations += 1
                if previous[2] != observation:
                    variant_observations += 1
                if _representative_key(observation, member) < _representative_key(
                    previous[2], previous[3]
                ):
                    representatives[key] = (
                        label,
                        scene,
                        observation,
                        member,
                        feature,
                        previous[5] + 1,
                    )
                else:
                    representatives[key] = (*previous[:5], previous[5] + 1)
            else:
                representatives[key] = (label, scene, observation, member, feature, 1)
            counts["rows"] += 1
            counts["malicious" if label else "benign"] += 1
        if counts["benign"] == 0 or counts["malicious"] == 0:
            raise CorrectedTrackBError(f"场景成员未同时包含良性与恶意标签：{member}")
        source_rows[member] = counts
    if reference_header is None:
        raise CorrectedTrackBError("没有读取任何场景成员")
    benign_items = sorted(
        ((key, value) for key, value in representatives.items() if value[0] == 0),
        key=lambda item: item[0],
    )
    malicious_by_scene: dict[int, list[tuple[bytes, tuple[Any, ...]]]] = {
        scene: [] for scene in range(1, 9)
    }
    for key, value in representatives.items():
        if value[0] == 1:
            malicious_by_scene[value[1]].append((key, value))
    if not benign_items or any(not malicious_by_scene[scene] for scene in range(1, 9)):
        raise CorrectedTrackBError("同源数据缺少良性或某个恶意场景")
    for scene in malicious_by_scene:
        malicious_by_scene[scene].sort(key=lambda item: item[0])
    benign_keys = np.asarray([item[0] for item in benign_items], dtype="S32")
    benign_features = np.vstack([item[1][4] for item in benign_items]).astype(
        np.float32, copy=False
    )
    benign_sources = np.asarray([item[1][3] for item in benign_items], dtype=object)
    scenario_features = {
        scene: np.vstack([item[1][4] for item in items]).astype(np.float32, copy=False)
        for scene, items in malicious_by_scene.items()
    }
    scenario_keys = {
        scene: np.asarray([item[0] for item in items], dtype="S32")
        for scene, items in malicious_by_scene.items()
    }
    summary = {
        "archive_sha256": config["data"]["scenarios_archive"]["sha256"],
        "header_sha256": _canonical_sha(reference_header),
        "source_rows": source_rows,
        "raw_row_count": int(sum(value["rows"] for value in source_rows.values())),
        "unique_stable_key_count": len(representatives),
        "unique_benign_key_count": len(benign_items),
        "unique_malicious_key_count": int(sum(len(value) for value in scenario_keys.values())),
        "duplicate_observation_count": duplicate_observations,
        "variant_observation_count": variant_observations,
        "representative_policy": "每个稳定键选择(observation_sha256,source_member)字典序最小观测",
        "duplicate_weighting": "one_stable_key_one_row",
        "feature_count": len(fields),
        "feature_fields_sha256": _canonical_sha(fields),
        "permanently_excluded_fields": list(PERMANENTLY_EXCLUDED_FIELDS),
        "persistent_derived_data": False,
        **EVIDENCE,
    }
    return (
        scenario_features,
        scenario_keys,
        benign_features,
        benign_keys,
        benign_sources,
        summary,
    )


def _directionless_auc(labels: np.ndarray, values: np.ndarray) -> float | None:
    finite = np.isfinite(values)
    if np.count_nonzero(finite) < 2 or len(np.unique(labels[finite])) != 2:
        return None
    from sklearn.metrics import roc_auc_score

    score = float(roc_auc_score(labels[finite], values[finite]))
    return max(score, 1.0 - score)


def _feature_gate(
    config: Mapping[str, Any],
    scenarios: Mapping[int, np.ndarray],
    benign: np.ndarray,
    benign_sources: np.ndarray,
    benign_train: np.ndarray,
) -> dict[str, Any]:
    fields = list(config["feature_budget"]["fields"])
    threshold = float(config["feature_gate"]["block_auc_gte"])
    diagnostics: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for outer_scene in range(1, 9):
        train_parts = [benign[benign_train]] + [
            scenarios[scene] for scene in range(1, 9) if scene != outer_scene
        ]
        labels = np.concatenate(
            [
                np.zeros(np.count_nonzero(benign_train), dtype=np.uint8),
                *[
                    np.ones(len(scenarios[scene]), dtype=np.uint8)
                    for scene in range(1, 9)
                    if scene != outer_scene
                ],
            ]
        )
        source_names = np.concatenate(
            [
                benign_sources[benign_train],
                *[
                    np.full(len(scenarios[scene]), f"scenario-{scene}", dtype=object)
                    for scene in range(1, 9)
                    if scene != outer_scene
                ],
            ]
        )
        values = np.vstack(train_parts)
        for field_index, field in enumerate(fields):
            column = values[:, field_index].astype(np.float64, copy=False)
            value_auc = _directionless_auc(labels, column)
            missing_auc = _directionless_auc(
                labels, np.asarray(~np.isfinite(column), dtype=np.float64)
            )
            available_aucs = [auc for auc in (value_auc, missing_auc) if auc is not None]
            auc = max(available_aucs) if available_aucs else None
            source_summary: dict[str, Any] = {}
            for source in sorted(set(source_names.tolist())):
                mask = source_names == source
                source_summary[str(source)] = {
                    "rows": int(np.count_nonzero(mask)),
                    "benign_rows": int(np.count_nonzero(mask & (labels == 0))),
                    "malicious_rows": int(np.count_nonzero(mask & (labels == 1))),
                    "finite_rate": float(np.mean(np.isfinite(column[mask]))),
                    "label_auc_directionless": _directionless_auc(labels[mask], column[mask]),
                }
            item = {
                "outer_test_scene": outer_scene,
                "field": field,
                "training_rows": len(labels),
                "label_auc_directionless": auc,
                "finite_value_auc_directionless": value_auc,
                "missing_indicator_auc_directionless": missing_auc,
                "benign_finite_rate": float(np.mean(np.isfinite(column[labels == 0]))),
                "malicious_finite_rate": float(np.mean(np.isfinite(column[labels == 1]))),
                "source_diagnostics": source_summary,
            }
            diagnostics.append(item)
            if auc is not None and auc >= threshold:
                blocked.append(
                    {
                        "outer_test_scene": outer_scene,
                        "field": field,
                        "label_auc_directionless": auc,
                    }
                )
    return {
        "schema_version": "genis-corrected-track-b-feature-gate-v2",
        "threshold": threshold,
        "permanently_excluded_fields": list(PERMANENTLY_EXCLUDED_FIELDS),
        "blocked": bool(blocked),
        "blocked_fields": blocked,
        "diagnostics": diagnostics,
        "diagnostics_sha256": _canonical_sha(diagnostics),
        "training_units_started": 0 if blocked else 16,
        **EVIDENCE,
    }


def _impute(train: np.ndarray, *others: np.ndarray) -> tuple[np.ndarray, ...]:
    median = np.nanmedian(train, axis=0)
    median = np.where(np.isfinite(median), median, 0.0).astype(np.float32)

    def apply(values: np.ndarray) -> np.ndarray:
        return np.where(np.isfinite(values), values, median).astype(np.float32, copy=False)

    return (apply(train), *(apply(values) for values in others))


def _balanced_weights(labels: np.ndarray) -> np.ndarray:
    counts = np.bincount(labels, minlength=2)
    if np.any(counts == 0):
        raise CorrectedTrackBError("训练单元缺少一个二分类类别")
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
        raise CorrectedTrackBError(f"XGBoost 未绑定 cuda:0：{devices}")
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
            raise CorrectedTrackBError(f"XGBoost 发生设备回退：{messages}")
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
        raise CorrectedTrackBError("预测概率形状错误或含非有限值")
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
        raise CorrectedTrackBError("良性校准分数或预算无效")
    unique, counts = np.unique(scores, return_counts=True)
    alarms = np.cumsum(counts[::-1])[::-1]
    valid = np.flatnonzero(alarms <= budget)
    if len(valid) == 0:
        return math.inf, 0
    index = int(valid[0])
    return float(unique[index]), int(alarms[index])


def _metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, recall_score

    prediction = np.asarray(scores >= 0.5, dtype=np.uint8)
    alarm = scores >= threshold
    benign = labels == 0
    malicious = labels == 1
    false_positive = int(np.count_nonzero(alarm & benign))
    true_positive = int(np.count_nonzero(alarm & malicious))
    return {
        "average_precision": float(average_precision_score(labels, scores)),
        "macro_f1": float(f1_score(labels, prediction, average="macro")),
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


def _run_unit(
    config: Mapping[str, Any],
    output_root: Path,
    outer_scene: int,
    model_key: str,
    scenarios: Mapping[int, np.ndarray],
    benign: np.ndarray,
    benign_train: np.ndarray,
    benign_calibration: np.ndarray,
    benign_test: np.ndarray,
    split_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    unit_root = output_root / "units" / f"scene-{outer_scene}" / model_key
    unit_root.mkdir(parents=True, exist_ok=False)
    _write_json(
        unit_root / "status.json",
        {"state": "RUNNING", "scene": outer_scene, "model": model_key},
    )
    log_path = unit_root / "unit.log"
    started = time.monotonic()
    try:
        train_malicious = np.vstack(
            [scenarios[scene] for scene in range(1, 9) if scene != outer_scene]
        )
        train_x_raw = np.vstack([benign[benign_train], train_malicious])
        train_y = np.concatenate(
            [
                np.zeros(np.count_nonzero(benign_train), dtype=np.uint8),
                np.ones(len(train_malicious), dtype=np.uint8),
            ]
        )
        calibration_x_raw = benign[benign_calibration]
        test_x_raw = np.vstack([benign[benign_test], scenarios[outer_scene]])
        test_y = np.concatenate(
            [
                np.zeros(np.count_nonzero(benign_test), dtype=np.uint8),
                np.ones(len(scenarios[outer_scene]), dtype=np.uint8),
            ]
        )
        if model_key == "random_forest":
            train_x, calibration_x, test_x = _impute(
                train_x_raw, calibration_x_raw, test_x_raw
            )
        else:
            train_x, calibration_x, test_x = train_x_raw, calibration_x_raw, test_x_raw
        model, device = _fit(
            model_key,
            config["models"][model_key],
            train_x,
            train_y,
            int(config["seed"]),
        )
        fit_seconds = time.monotonic() - started
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
        model_path = unit_root / f"model.{extension}"
        _save_model(model_key, model, model_path)
        cell = {
            "outer_test_scene": outer_scene,
            "model": model_key,
            "device": device,
            "unit_cpu_threads": int(
                config["models"][model_key].get(
                    "n_jobs", config["models"][model_key].get("nthread", 1)
                )
            ),
            "max_concurrency": int(config["parallel"]["max_concurrency"]),
            "total_cpu_thread_budget": int(config["parallel"]["total_cpu_thread_budget"]),
            "train_rows": len(train_y),
            "calibration_benign_rows": len(calibration_scores),
            "test_rows": len(test_y),
            "split_receipt_sha256": _canonical_sha(split_receipt),
            "calibration_allowed_false_positives": allowed,
            "calibration_actual_false_positives": actual,
            "fit_seconds": fit_seconds,
            "predict_seconds": predict_seconds,
            "model_sha256": _sha256(model_path),
            "metrics": _metrics(test_y, test_scores, threshold),
        }
        _write_json(unit_root / "cell.json", cell)
        log_path.write_text(
            f"完成 scene={outer_scene} model={model_key} "
            f"elapsed={time.monotonic() - started:.3f}\n",
            encoding="utf-8",
        )
        _write_json(
            unit_root / "status.json",
            {"state": "FINISHED", "scene": outer_scene, "model": model_key},
        )
        return cell
    except Exception as error:
        log_path.write_text(
            f"失败 scene={outer_scene} model={model_key} "
            f"type={type(error).__name__} detail={error}\n",
            encoding="utf-8",
        )
        _write_json(
            unit_root / "status.json",
            {
                "state": "FAILED",
                "scene": outer_scene,
                "model": model_key,
                "failure_type": type(error).__name__,
                "detail": str(error),
            },
        )
        raise


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
    archive_path = _resolve(config_path, config["data"]["scenarios_archive"]["path"])
    output_root = _resolve(config_path, config["paths"]["run_root"])
    if output_root.exists():
        raise CorrectedTrackBError("corrected-v2 唯一运行根已存在，拒绝覆盖")
    output_root.mkdir(parents=True)
    _write_json(
        output_root / "run_binding.json",
        {
            "config_sha256": _sha256(config_path),
            "code_sha256": _sha256(Path(__file__).resolve()),
            "archive_sha256": config["data"]["scenarios_archive"]["sha256"],
            "contract_version": "corrected-v2",
            "parallel_execution": True,
            "max_concurrency": 3,
            "persistent_derived_data": False,
            **EVIDENCE,
        },
    )
    _status(
        output_root,
        "RUNNING",
        "load-same-source-scenarios",
        completed_units=0,
        total_units=16,
    )
    started = time.monotonic()
    try:
        (
            scenarios,
            scenario_keys,
            benign,
            benign_keys,
            benign_sources,
            data_summary,
        ) = _load_same_source_data(config, archive_path)
        _write_json(output_root / "data_summary.json", data_summary)
        modulo = int(config["partition"]["modulo"])
        domain = str(config["partition"]["hash_domain"])
        buckets = np.fromiter(
            (_partition_bucket(domain, bytes(key), modulo) for key in benign_keys),
            dtype=np.uint8,
            count=len(benign_keys),
        )
        train_mask = np.isin(buckets, config["partition"]["train_buckets"])
        calibration_mask = np.isin(buckets, config["partition"]["calibration_buckets"])
        test_mask = np.isin(buckets, config["partition"]["test_buckets"])
        if not np.all(train_mask | calibration_mask | test_mask):
            raise CorrectedTrackBError("良性稳定键存在未归属分区")
        train_keys = {bytes(key) for key in benign_keys[train_mask]}
        calibration_keys = {bytes(key) for key in benign_keys[calibration_mask]}
        test_keys = {bytes(key) for key in benign_keys[test_mask]}
        intersections = {
            "train_calibration": len(train_keys & calibration_keys),
            "train_test": len(train_keys & test_keys),
            "calibration_test": len(calibration_keys & test_keys),
        }
        if any(intersections.values()) or np.count_nonzero(test_mask) < 1000:
            raise CorrectedTrackBError("训练、校准、测试稳定键交集非零或测试良性不足")
        malicious_all = {bytes(key) for values in scenario_keys.values() for key in values}
        if malicious_all & (train_keys | calibration_keys | test_keys):
            raise CorrectedTrackBError("良性与恶意稳定键交叠")
        fold_intersections: dict[str, dict[str, int]] = {}
        for outer_scene in range(1, 9):
            fold_train_keys = train_keys | {
                bytes(key)
                for scene, values in scenario_keys.items()
                if scene != outer_scene
                for key in values
            }
            fold_test_keys = test_keys | {
                bytes(key) for key in scenario_keys[outer_scene]
            }
            fold_counts = {
                "train_calibration": len(fold_train_keys & calibration_keys),
                "train_test": len(fold_train_keys & fold_test_keys),
                "calibration_test": len(calibration_keys & fold_test_keys),
            }
            if any(fold_counts.values()):
                raise CorrectedTrackBError(
                    f"外层场景 {outer_scene} 的训练、校准、测试稳定键交集非零"
                )
            fold_intersections[str(outer_scene)] = fold_counts
        split_receipt = {
            "hash_domain": domain,
            "modulo": modulo,
            "train_count": len(train_keys),
            "calibration_count": len(calibration_keys),
            "test_count": len(test_keys),
            "train_keyset_sha256": _keyset_sha(list(train_keys)),
            "calibration_keyset_sha256": _keyset_sha(list(calibration_keys)),
            "test_keyset_sha256": _keyset_sha(list(test_keys)),
            "pairwise_intersections": intersections,
            "outer_fold_pairwise_intersections": fold_intersections,
            "stable_key_is_atomic": True,
        }
        _write_json(output_root / "split_receipt.json", split_receipt)
        _status(
            output_root,
            "RUNNING",
            "training-visible-univariate-gate",
            completed_units=0,
            total_units=16,
        )
        gate = _feature_gate(config, scenarios, benign, benign_sources, train_mask)
        _write_json(output_root / "feature_gate.json", gate)
        if gate["blocked"]:
            raise CorrectedTrackBError(
                f"训练侧单字段 AUC 门禁阻断，训练单元为 0：{gate['blocked_fields']}"
            )
        futures: dict[Future[dict[str, Any]], tuple[int, str]] = {}
        cells: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        with ThreadPoolExecutor(
            max_workers=int(config["parallel"]["max_concurrency"]),
            thread_name_prefix="genis-corrected-v2",
        ) as executor:
            for outer_scene in range(1, 9):
                for model_key in MODEL_KEYS:
                    future = executor.submit(
                        _run_unit,
                        config,
                        output_root,
                        outer_scene,
                        model_key,
                        scenarios,
                        benign,
                        train_mask,
                        calibration_mask,
                        test_mask,
                        split_receipt,
                    )
                    futures[future] = (outer_scene, model_key)
            for future in as_completed(futures):
                outer_scene, model_key = futures[future]
                try:
                    cells.append(future.result())
                except Exception as error:
                    failures.append(
                        {
                            "outer_test_scene": outer_scene,
                            "model": model_key,
                            "failure_type": type(error).__name__,
                            "detail": str(error),
                        }
                    )
                _status(
                    output_root,
                    "RUNNING",
                    "parallel-scenario-model-units",
                    completed_units=len(cells),
                    failed_units=len(failures),
                    settled_units=len(cells) + len(failures),
                    total_units=16,
                )
                print(
                    f"UNIT_SETTLED scene={outer_scene} model={model_key} "
                    f"finished={len(cells)} failed={len(failures)} total=16",
                    flush=True,
                )
        if failures:
            raise CorrectedTrackBError(f"并行单元失败：{failures}")
        cells.sort(key=lambda cell: (int(cell["outer_test_scene"]), str(cell["model"])))
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
            "schema_version": "genis-corrected-track-b-results-v2",
            "run_id": config["run_id"],
            "protocol_id": "corrected-v2",
            "data_summary": data_summary,
            "split_receipt": split_receipt,
            "feature_gate_summary": {
                "blocked": False,
                "diagnostics_sha256": gate["diagnostics_sha256"],
                "threshold": gate["threshold"],
            },
            "parallel_execution": {
                "enabled": True,
                "max_concurrency": 3,
                "total_unit_count": 16,
                "stable_result_order": "outer_test_scene,model",
                "total_cpu_thread_budget": 16,
                "random_forest_n_jobs_per_unit": config["models"]["random_forest"]["n_jobs"],
            },
            "cells": cells,
            "model_summary": summary,
            "runtime": {
                "elapsed_seconds": time.monotonic() - started,
                "completed_units": len(cells),
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
            "parallel-corrected-v2-complete",
            completed_units=16,
            total_units=16,
        )
        return results
    except Exception as error:
        _status(
            output_root,
            "FAILED",
            "corrected-v2",
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
        raise CorrectedTrackBError("SwanLab 目的地未获授权")
    status = _read_json(output_root / "status.json")
    results = _read_json(output_root / "results.json")
    if status.get("state") != "FINISHED" or len(results.get("cells", [])) != 16:
        raise CorrectedTrackBError("只允许发布 16 单元全部完成的聚合结果")
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
            "protocol_id": "corrected-v2",
            "parallel": True,
            "max_concurrency": 3,
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
        "parallel": True,
        **EVIDENCE,
    }
    _write_json(output_root / "swanlab_publish_receipt.json", receipt)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="运行 corrected-v2 并行强基线")
    run_parser.add_argument("--config", type=Path, required=True)
    publish = subparsers.add_parser("swanlab-publish", help="上传并行运行聚合指标")
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
    except CorrectedTrackBError as error:
        print(f"GeNIS corrected Track B v2 失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
