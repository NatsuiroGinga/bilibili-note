"""GeNIS 60 秒训练成员内无物化强基线资格矩阵。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import resource
import shutil
import sys
import threading
import time
import warnings
import zipfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import numpy as np


class QualificationError(RuntimeError):
    """表示冻结合同或资格矩阵门禁被破坏。"""


LABEL_COLUMNS = ("BinaryLabel", "CategoryLabel", "SubCategoryLabel")
SPLIT_KEYS = ("row_stratified", "observation_grouped")
FEATURE_KEYS = ("safe76-v1", "paper84-v1")
MODEL_KEYS = ("xgboost", "random_forest")
BENIGN_CLASS_COUNT = 3
TOTAL_FITS = 40
EVIDENCE = {
    "screening_only": True,
    "formal_paper_evidence": False,
    "official_test_accessed": False,
    "final_accessed": False,
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise QualificationError(f"无法读取 JSON：{path}：{error}") from error
    if not isinstance(value, dict):
        raise QualificationError(f"JSON 顶层必须是对象：{path}")
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


def _module_path() -> Path:
    return Path(__file__).resolve()


def _resolve(config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (config_path.resolve().parent.parent / path).resolve()


def _load_config(config_path: Path) -> dict[str, Any]:
    config = _read_json(config_path.resolve())
    required = {
        "schema_version",
        "contract_version",
        "run_id",
        "seed",
        "data",
        "feature_budgets",
        "boolean_one_hot_fields",
        "splits",
        "models",
        "metrics",
        "gates",
        "runtime",
        "paths",
        "evidence",
        "swanlab",
    }
    if set(config) < required:
        raise QualificationError(f"配置缺少字段：{sorted(required - set(config))}")
    paper_fields = config["feature_budgets"]["paper84-v1"]["fields"]
    excluded = set(config["feature_budgets"]["safe76-v1"]["excluded"])
    safe_fields = [name for name in paper_fields if name not in excluded]
    if (
        config["schema_version"] != "genis-inmemory-baseline-qualification-config-v1"
        or config["contract_version"] != "genis-60s-trainonly-inmemory-qualification-v1"
        or config["seed"] != 42
        or config["evidence"] != EVIDENCE
        or len(config["data"]["class_order"]) != 13
        or len(paper_fields) != 84
        or len(set(paper_fields)) != 84
        or len(safe_fields) != 76
        or config["splits"]["fold_count"] != 5
        or config["runtime"]["fit_count"] != TOTAL_FITS
    ):
        raise QualificationError("配置不符合无物化冻结身份、字段或五折合同")
    if set(config["models"]) != set(MODEL_KEYS):
        raise QualificationError("模型矩阵必须恰含 XGBoost 和随机森林")
    xgb = config["models"]["xgboost"]
    forest = config["models"]["random_forest"]
    if xgb["tree_method"] != "hist" or xgb["device"] != "cuda" or xgb["nthread"] != 8:
        raise QualificationError("XGBoost 必须固定 hist/cuda/nthread=8")
    if forest["n_jobs"] != 8 or forest["class_weight"] is not None:
        raise QualificationError("随机森林必须固定 n_jobs=8 且不使用类别权重")
    if set(config["data"]["forbidden_members"]) != {
        "4-preprocessed/genis-60-sec-test.csv",
        "4-preprocessed/genis-5-sec-train.csv",
        "4-preprocessed/genis-5-sec-test.csv",
        "4-preprocessed/genis-10-sec-train.csv",
        "4-preprocessed/genis-10-sec-test.csv",
        "4-preprocessed/genis-30-sec-train.csv",
        "4-preprocessed/genis-30-sec-test.csv",
    }:
        raise QualificationError("禁止成员清单不完整")
    return config


def _status(root: Path, state: str, stage: str, **extra: Any) -> None:
    _write_json(
        root / "status.json",
        {
            "schema_version": "genis-inmemory-baseline-qualification-status-v1",
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


def _progress(stage: str, completed: int, total: int, started: float) -> None:
    elapsed = max(time.monotonic() - started, 1e-9)
    rate = completed / elapsed
    eta = (total - completed) / rate if rate > 0 else None
    print(
        json.dumps(
            {
                "event": "progress",
                "stage": stage,
                "completed": completed,
                "total": total,
                "elapsed_seconds": round(elapsed, 3),
                "throughput_per_second": round(rate, 3),
                "eta_seconds": None if eta is None else round(eta, 3),
                "peak_rss_gib": round(_peak_rss_gib(), 4),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


class _FitHeartbeat(AbstractContextManager["_FitHeartbeat"]):
    def __init__(
        self,
        cell: str,
        fold: int,
        completed_fits: int,
        interval_seconds: int,
        run_started: float,
    ) -> None:
        self.cell = cell
        self.fold = fold
        self.completed_fits = completed_fits
        self.interval_seconds = interval_seconds
        self.run_started = run_started
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self.stop.wait(self.interval_seconds):
            elapsed = time.monotonic() - self.run_started
            average = elapsed / max(self.completed_fits, 1)
            eta = average * (TOTAL_FITS - self.completed_fits)
            print(
                json.dumps(
                    {
                        "event": "heartbeat",
                        "cell": self.cell,
                        "fold": self.fold,
                        "completed_fits": self.completed_fits,
                        "total_fits": TOTAL_FITS,
                        "elapsed_seconds": round(elapsed, 3),
                        "eta_seconds": round(eta, 3),
                        "peak_rss_gib": round(_peak_rss_gib(), 4),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    def __enter__(self) -> _FitHeartbeat:
        self.thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop.set()
        self.thread.join(timeout=2)


class _HashingReader(io.RawIOBase):
    def __init__(self, raw: Any, digest: Any) -> None:
        self.raw = raw
        self.digest = digest

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        size = self.raw.readinto(buffer)
        if size:
            self.digest.update(memoryview(buffer)[:size])
        return size


def _allowed_member_rows(
    archive_path: Path, allowed_member: str, digest: Any
) -> Iterable[list[str]]:
    with zipfile.ZipFile(archive_path, "r") as archive:
        try:
            member = archive.getinfo(allowed_member)
        except KeyError as error:
            raise QualificationError("唯一允许的训练成员不存在") from error
        with archive.open(member, "r") as raw:
            buffered = io.BufferedReader(_HashingReader(raw, digest), buffer_size=1024 * 1024)
            with io.TextIOWrapper(buffered, encoding="utf-8-sig", newline="") as text:
                yield from csv.reader(text)


def _observation_hash(tokens: Sequence[str]) -> bytes:
    digest = hashlib.sha256()
    for token in tokens:
        raw = token.encode("utf-8")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.digest()


def _assignment_hash(domain: str, seed: int, observation_hash: bytes, value: int) -> bytes:
    digest = hashlib.sha256()
    digest.update(domain.encode("utf-8"))
    digest.update(seed.to_bytes(8, "big", signed=False))
    digest.update(observation_hash)
    digest.update(value.to_bytes(8, "big", signed=False))
    return digest.digest()


def _parse_features(row: Sequence[str], boolean_positions: set[int], row_number: int) -> np.ndarray:
    values = np.empty(84, dtype=np.float32)
    for position, token in enumerate(row[:84]):
        if position in boolean_positions:
            if token == "True":
                values[position] = 1.0
            elif token == "False":
                values[position] = 0.0
            else:
                raise QualificationError(f"第 {row_number} 行官方独热字段不是精确 True/False")
        else:
            try:
                values[position] = float(token)
            except ValueError as error:
                raise QualificationError(f"第 {row_number} 行数值字段不可解析") from error
    if not np.isfinite(values).all():
        raise QualificationError(f"第 {row_number} 行含非有限浮点")
    return values


def _load_training_member(
    config: Mapping[str, Any], archive_path: Path
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    expected_size = int(config["data"]["archive_bytes"])
    if not archive_path.is_file() or archive_path.stat().st_size != expected_size:
        raise QualificationError("原始 ZIP 不存在或字节数不符合冻结合同")
    if _sha256(archive_path) != config["data"]["archive_sha256"]:
        raise QualificationError("原始 ZIP SHA-256 不符合冻结合同")
    expected_rows = int(config["data"]["expected_rows"])
    paper_fields = list(config["feature_budgets"]["paper84-v1"]["fields"])
    boolean_positions = {paper_fields.index(name) for name in config["boolean_one_hot_fields"]}
    classes = list(config["data"]["class_order"])
    class_to_index = {name: index for index, name in enumerate(classes)}
    features = np.empty((expected_rows, 84), dtype=np.float32)
    labels = np.empty(expected_rows, dtype=np.uint8)
    observation_hashes = np.empty((expected_rows, 32), dtype=np.uint8)
    member_digest = hashlib.sha256()
    rows = iter(_allowed_member_rows(archive_path, config["data"]["allowed_member"], member_digest))
    try:
        header = next(rows)
    except StopIteration as error:
        raise QualificationError("唯一允许的训练成员为空") from error
    if (
        len(header) != config["data"]["expected_columns"]
        or len(header) != len(set(header))
        or tuple(header[-3:]) != LABEL_COLUMNS
        or header[:-3] != paper_fields
        or hashlib.sha256(",".join(header).encode()).hexdigest() != config["data"]["header_sha256"]
        or _canonical_sha(header) != config["data"]["ordered_fields_sha256"]
    ):
        raise QualificationError("训练成员表头或字段顺序不符合冻结合同")
    started = time.monotonic()
    row_count = 0
    label_position = header.index("SubCategoryLabel")
    for row_count, row in enumerate(rows, start=1):
        if row_count > expected_rows:
            raise QualificationError("训练成员行数超过冻结值")
        if len(row) != len(header):
            raise QualificationError(f"第 {row_count} 行列数不为 87")
        label = row[label_position]
        if label not in class_to_index:
            raise QualificationError(f"第 {row_count} 行标签不在冻结十三类中")
        offset = row_count - 1
        features[offset] = _parse_features(row, boolean_positions, row_count)
        labels[offset] = class_to_index[label]
        observation_hashes[offset] = np.frombuffer(_observation_hash(row[:84]), dtype=np.uint8)
        if row_count % int(config["runtime"]["progress_rows"]) == 0:
            _progress("load-training-member", row_count, expected_rows, started)
    if row_count != expected_rows:
        raise QualificationError(f"训练成员行数不匹配：{row_count}")
    if member_digest.hexdigest() != config["data"]["member_sha256"]:
        raise QualificationError("唯一允许训练成员 SHA-256 不匹配")
    if set(np.unique(labels).tolist()) != set(range(13)):
        raise QualificationError("训练成员标签集合不等于冻结十三类")
    summary = {
        "archive_bytes": expected_size,
        "archive_sha256": config["data"]["archive_sha256"],
        "allowed_member": config["data"]["allowed_member"],
        "member_sha256": member_digest.hexdigest(),
        "rows": row_count,
        "columns": len(header),
        "class_support": {
            classes[index]: int(count)
            for index, count in enumerate(np.bincount(labels, minlength=13))
        },
        "forbidden_members_opened": [],
        **EVIDENCE,
    }
    return features, labels, observation_hashes, summary


def _row_folds(
    labels: np.ndarray, observation_hashes: np.ndarray, config: Mapping[str, Any]
) -> np.ndarray:
    fold_count = int(config["splits"]["fold_count"])
    domain = str(config["splits"]["row_stratified"]["hash_domain"])
    seed = int(config["seed"])
    folds = np.empty(len(labels), dtype=np.uint8)
    for class_index in range(13):
        members = np.flatnonzero(labels == class_index)
        keyed = [
            (
                _assignment_hash(
                    domain,
                    seed,
                    bytes(observation_hashes[index]),
                    int(index) + 1,
                ),
                int(index),
            )
            for index in members
        ]
        keyed.sort(key=lambda item: (item[0], item[1]))
        for offset, (_, row_index) in enumerate(keyed):
            folds[row_index] = offset % fold_count
    return folds


def _group_folds(
    labels: np.ndarray, observation_hashes: np.ndarray, config: Mapping[str, Any]
) -> tuple[np.ndarray, dict[str, Any]]:
    fold_count = int(config["splits"]["fold_count"])
    domain = str(config["splits"]["observation_grouped"]["hash_domain"])
    seed = int(config["seed"])
    group_rows: Counter[bytes] = Counter()
    group_labels: dict[bytes, int] = {}
    for index, raw_hash in enumerate(observation_hashes):
        key = bytes(raw_hash)
        label = int(labels[index])
        previous = group_labels.setdefault(key, label)
        if previous != label:
            raise QualificationError("同一观察哈希存在标签冲突")
        group_rows[key] += 1
    assignments: dict[bytes, int] = {}
    for class_index in range(13):
        groups = [key for key, label in group_labels.items() if label == class_index]
        groups.sort(key=lambda key: _assignment_hash(domain, seed, key, class_index))
        fold_rows = [0] * fold_count
        for key in groups:
            fold = min(range(fold_count), key=lambda value: (fold_rows[value], value))
            assignments[key] = fold
            fold_rows[fold] += group_rows[key]
    folds = np.fromiter(
        (assignments[bytes(raw_hash)] for raw_hash in observation_hashes),
        dtype=np.uint8,
        count=len(labels),
    )
    sets = [
        {bytes(observation_hashes[index]) for index in np.flatnonzero(folds == fold)}
        for fold in range(fold_count)
    ]
    intersections = {
        f"{left}__{right}": len(sets[left] & sets[right])
        for left in range(fold_count)
        for right in range(left + 1, fold_count)
    }
    if any(intersections.values()):
        raise QualificationError("观察哈希分组折存在折间交集")
    return folds, {
        "unique_observations": len(group_rows),
        "duplicate_rows": len(labels) - len(group_rows),
        "label_conflicts": 0,
        "fold_hash_intersections": intersections,
    }


def _validate_folds(
    labels: np.ndarray, folds: np.ndarray, split_name: str, fold_count: int
) -> list[dict[str, Any]]:
    audit = []
    for fold in range(fold_count):
        counts = np.bincount(labels[folds == fold], minlength=13)
        if np.any(counts == 0):
            raise QualificationError(f"{split_name} 的第 {fold} 折缺少冻结类别")
        audit.append(
            {
                "fold": fold,
                "rows": int(np.count_nonzero(folds == fold)),
                "class_support": [int(value) for value in counts],
            }
        )
    return audit


def _xgb_device(booster: Any) -> str:
    def collect(value: Any) -> list[str]:
        devices: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "device" and isinstance(child, str):
                    devices.append(child)
                devices.extend(collect(child))
        elif isinstance(value, list):
            for child in value:
                devices.extend(collect(child))
        return devices

    devices = collect(json.loads(booster.save_config()))
    if "cuda:0" not in devices:
        raise QualificationError(f"XGBoost 完整模型配置未绑定 cuda:0：{devices}")
    return "cuda:0"


def _fit_model(
    model_key: str,
    params: Mapping[str, Any],
    train_x: np.ndarray,
    train_y: np.ndarray,
    seed: int,
) -> tuple[Any, str, list[str]]:
    captured: list[str] = []
    if model_key == "xgboost":
        import xgboost as xgb

        train_params = {
            "objective": "multi:softprob",
            "num_class": 13,
            "eval_metric": "mlogloss",
            "max_depth": params["max_depth"],
            "eta": params["learning_rate"],
            "subsample": params["subsample"],
            "colsample_bytree": params["colsample_bytree"],
            "min_child_weight": params["min_child_weight"],
            "lambda": params["reg_lambda"],
            "tree_method": params["tree_method"],
            "device": params["device"],
            "nthread": params["nthread"],
            "seed": seed,
        }
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            model = xgb.train(
                train_params,
                xgb.DMatrix(train_x, label=train_y),
                num_boost_round=int(params["n_estimators"]),
            )
        captured = [str(item.message) for item in caught]
        if any("fallback" in item.lower() or "cpu" in item.lower() for item in captured):
            raise QualificationError(f"XGBoost 设备警告使单元无效：{captured}")
        return model, _xgb_device(model), captured
    from sklearn.ensemble import RandomForestClassifier

    if int(params["n_jobs"]) > (os.cpu_count() or 1):
        raise QualificationError("随机森林 n_jobs 超过逻辑核数")
    model = RandomForestClassifier(
        n_estimators=params["n_estimators"],
        max_depth=params["max_depth"],
        max_features=params["max_features"],
        min_samples_leaf=params["min_samples_leaf"],
        bootstrap=params["bootstrap"],
        class_weight=params["class_weight"],
        n_jobs=params["n_jobs"],
        random_state=seed,
    )
    model.fit(train_x, train_y)
    if not np.array_equal(model.classes_, np.arange(13)):
        raise QualificationError("随机森林训练折未覆盖冻结十三类")
    return model, "cpu", captured


def _predict(model_key: str, model: Any, features: np.ndarray) -> np.ndarray:
    if model_key == "xgboost":
        import xgboost as xgb

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            probability = model.predict(xgb.DMatrix(features))
        messages = [str(item.message) for item in caught]
        if any("fallback" in item.lower() or "cpu" in item.lower() for item in messages):
            raise QualificationError(f"XGBoost 预测设备警告使单元无效：{messages}")
    else:
        probability = model.predict_proba(features)
    result = np.asarray(probability, dtype=np.float32)
    if result.shape != (len(features), 13) or not np.isfinite(result).all():
        raise QualificationError("模型概率形状错误或含非有限值")
    if not np.allclose(result.sum(axis=1), 1.0, atol=1e-5):
        raise QualificationError("模型概率行和不为 1")
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


def _load_model(model_key: str, path: Path) -> tuple[Any, str]:
    if model_key == "xgboost":
        import xgboost as xgb

        model = xgb.Booster(model_file=str(path))
        return model, _xgb_device(model)
    import joblib

    model = joblib.load(path)
    if not np.array_equal(model.classes_, np.arange(13)):
        raise QualificationError("恢复的随机森林类别顺序无效")
    return model, "cpu"


def _threshold(scores: np.ndarray, labels: np.ndarray, alpha: float) -> tuple[float, int, int]:
    benign = np.sort(scores[labels < BENIGN_CLASS_COUNT], kind="stable")
    if len(benign) == 0:
        raise QualificationError("阈值训练折没有良性样本")
    allowed = math.floor(alpha * len(benign))
    threshold = float(benign[len(benign) - allowed - 1]) if allowed < len(benign) else -math.inf
    actual = int(np.count_nonzero(benign > threshold))
    if actual > allowed:
        raise QualificationError("并列概率组导致训练折 FPR 超预算")
    return threshold, allowed, actual


def _metrics(
    labels: np.ndarray,
    probability: np.ndarray,
    threshold: float,
    minimum_support: int,
    classes: Sequence[str],
) -> dict[str, Any]:
    from sklearn.metrics import (
        average_precision_score,
        confusion_matrix,
        precision_recall_fscore_support,
    )

    prediction = probability.argmax(axis=1)
    precision, recall, f1, support = precision_recall_fscore_support(
        labels, prediction, labels=np.arange(13), zero_division=0
    )
    malicious_score = 1.0 - probability[:, :BENIGN_CLASS_COUNT].sum(axis=1)
    binary = np.asarray(labels >= BENIGN_CLASS_COUNT, dtype=np.uint8)
    alarm = malicious_score > threshold
    benign_count = int(np.count_nonzero(binary == 0))
    malicious_count = int(np.count_nonzero(binary == 1))
    false_positive = int(np.count_nonzero(alarm & (binary == 0)))
    true_positive = int(np.count_nonzero(alarm & (binary == 1)))
    supported = f1[np.asarray(support) >= minimum_support]
    return {
        "macro_f1": float(np.mean(f1)),
        "weighted_f1": float(np.average(f1, weights=support)),
        "macro_recall": float(np.mean(recall)),
        "min_supported_class_f1": float(np.min(supported)),
        "malicious_pr_auc": float(average_precision_score(binary, malicious_score)),
        "recall_at_fpr_0.005": true_positive / malicious_count,
        "fpr_at_threshold": false_positive / benign_count,
        "false_alerts_per_10000_benign": false_positive * 10000.0 / benign_count,
        "threshold": threshold,
        "benign_rows": benign_count,
        "malicious_rows": malicious_count,
        "false_positives": false_positive,
        "true_positives": true_positive,
        "per_class": [
            {
                "class_index": index,
                "class_name": classes[index],
                "support": int(support[index]),
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
            }
            for index in range(13)
        ],
        "confusion_matrix": confusion_matrix(labels, prediction, labels=np.arange(13))
        .astype(int)
        .tolist(),
    }


def _cell_key(split_key: str, feature_key: str, model_key: str) -> str:
    return f"{split_key}__{feature_key}__{model_key}"


def _model_path(cell_root: Path, model_key: str, fold: int) -> Path:
    extension = "ubj" if model_key == "xgboost" else "joblib"
    return cell_root / "models" / f"fold-{fold}.{extension}"


def _restore_finished_fold(
    cell_root: Path, model_key: str, fold: int
) -> tuple[Any, str, dict[str, Any]] | None:
    state_path = cell_root / f"fold-{fold}-status.json"
    if not state_path.is_file():
        return None
    state = _read_json(state_path)
    model_path = _model_path(cell_root, model_key, fold)
    if state.get("state") != "finished":
        return None
    if not model_path.is_file() or _sha256(model_path) != state.get("model_sha256"):
        raise QualificationError(f"第 {fold} 折恢复模型摘要不匹配")
    model, device = _load_model(model_key, model_path)
    if device != state.get("device"):
        raise QualificationError(f"第 {fold} 折恢复模型设备不一致")
    return model, device, state


def _fold_summary(folds: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    scalar_names = (
        "macro_f1",
        "weighted_f1",
        "macro_recall",
        "min_supported_class_f1",
        "malicious_pr_auc",
        "recall_at_fpr_0.005",
        "fpr_at_threshold",
        "false_alerts_per_10000_benign",
    )
    return {
        name: {
            "mean": float(np.mean([fold[name] for fold in folds])),
            "std": float(np.std([fold[name] for fold in folds], ddof=1)),
            "raw": [float(fold[name]) for fold in folds],
        }
        for name in scalar_names
    }


def _decisions(cells: Mapping[str, Any], gates: Mapping[str, float]) -> dict[str, Any]:
    macro = {key: value["overall_oof"]["macro_f1"] for key, value in cells.items()}
    safe_qualification = {
        key: score >= gates["strong_baseline_macro_f1"]
        for key, score in macro.items()
        if "__safe76-v1__" in key
    }
    field_deltas = {
        f"{split}__{model}": macro[_cell_key(split, "paper84-v1", model)]
        - macro[_cell_key(split, "safe76-v1", model)]
        for split in SPLIT_KEYS
        for model in MODEL_KEYS
    }
    split_deltas = {
        f"{feature}__{model}": macro[_cell_key("row_stratified", feature, model)]
        - macro[_cell_key("observation_grouped", feature, model)]
        for feature in FEATURE_KEYS
        for model in MODEL_KEYS
    }
    qualified = any(safe_qualification.values())
    return {
        "decision": "STRONG_BASELINE_QUALIFIED" if qualified else "INVALID_WEAK_BASELINE",
        "baseline_qualified": qualified,
        "safe_model_qualification": safe_qualification,
        "safe_xgboost_and_random_forest_all_below_0.9700": not qualified,
        "field_deltas": field_deltas,
        "material_field_shortcut_present": any(
            value >= gates["material_field_delta"] for value in field_deltas.values()
        ),
        "row_vs_grouped_deltas": split_deltas,
        "material_duplicate_advantage_present": any(
            value >= gates["material_row_split_delta"] for value in split_deltas.values()
        ),
    }


def _initialize_run(
    config_path: Path, archive_path: Path, output_root: Path
) -> tuple[bool, dict[str, Any]]:
    binding = {
        "schema_version": "genis-inmemory-baseline-qualification-run-binding-v1",
        "config_sha256": _sha256(config_path),
        "code_sha256": _sha256(_module_path()),
        "archive_bytes": archive_path.stat().st_size if archive_path.is_file() else None,
        "archive_sha256": _sha256(archive_path) if archive_path.is_file() else None,
        "fit_count": TOTAL_FITS,
        "persistence_policy": {
            "features": False,
            "labels": False,
            "observation_hashes": False,
            "fold_membership": False,
            "per_sample_probabilities": False,
            "models": True,
            "aggregate_results": True,
        },
        **EVIDENCE,
    }
    if not output_root.exists():
        output_root.mkdir(parents=True)
        shutil.copyfile(config_path, output_root / "config.snapshot.json")
        _write_json(output_root / "run_binding.json", binding)
        return False, binding
    status = _read_json(output_root / "status.json")
    previous = _read_json(output_root / "run_binding.json")
    if status.get("state") == "FINISHED":
        raise QualificationError("唯一运行根已经完成，拒绝覆盖")
    if status.get("state") not in {"RUNNING", "FAILED", "INTERRUPTED"} or previous != binding:
        raise QualificationError("唯一运行根不可恢复或输入绑定不一致")
    return True, binding


def run(
    config_path: Path, archive_override: Path | None, output_override: Path | None
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    archive_path = (
        archive_override.resolve()
        if archive_override is not None
        else _resolve(config_path, config["data"]["archive_path"])
    )
    output_root = (
        output_override.resolve()
        if output_override is not None
        else _resolve(config_path, config["paths"]["run_root"])
    )
    resumed, _ = _initialize_run(config_path, archive_path, output_root)
    _status(output_root, "RUNNING", "load-training-member", resumed=resumed)
    run_started = time.monotonic()
    try:
        features, labels, observation_hashes, input_summary = _load_training_member(
            config, archive_path
        )
        row_folds = _row_folds(labels, observation_hashes, config)
        group_folds, group_audit = _group_folds(labels, observation_hashes, config)
        fold_count = int(config["splits"]["fold_count"])
        split_audit = {
            "row_stratified": _validate_folds(labels, row_folds, "row_stratified", fold_count),
            "observation_grouped": _validate_folds(
                labels, group_folds, "observation_grouped", fold_count
            ),
            "observation_group_audit": group_audit,
        }
        safe_indices = np.asarray(
            [
                index
                for index, name in enumerate(config["feature_budgets"]["paper84-v1"]["fields"])
                if name not in set(config["feature_budgets"]["safe76-v1"]["excluded"])
            ],
            dtype=np.int64,
        )
        cells: dict[str, Any] = {}
        completed_fits = 0
        for split_key, folds in (
            ("row_stratified", row_folds),
            ("observation_grouped", group_folds),
        ):
            for feature_key in FEATURE_KEYS:
                columns = safe_indices if feature_key == "safe76-v1" else np.arange(84)
                for model_key in MODEL_KEYS:
                    cell_key = _cell_key(split_key, feature_key, model_key)
                    cell_root = output_root / "cells" / cell_key
                    cell_root.mkdir(parents=True, exist_ok=True)
                    oof_probability = np.empty((len(labels), 13), dtype=np.float32)
                    fold_runtime: list[dict[str, Any]] = []
                    for fold in range(fold_count):
                        validation_mask = folds == fold
                        training_mask = ~validation_mask
                        restored = _restore_finished_fold(cell_root, model_key, fold)
                        if restored is None:
                            state_path = cell_root / f"fold-{fold}-status.json"
                            _write_json(
                                state_path,
                                {
                                    "schema_version": "genis-inmemory-qualification-fold-state-v1",
                                    "state": "running",
                                    "cell": cell_key,
                                    "fold": fold,
                                    "started_at_epoch": time.time(),
                                    **EVIDENCE,
                                },
                            )
                            train_x = features[np.ix_(training_mask, columns)]
                            train_y = labels[training_mask]
                            fit_started = time.monotonic()
                            with _FitHeartbeat(
                                cell_key,
                                fold,
                                completed_fits,
                                int(config["runtime"]["heartbeat_seconds"]),
                                run_started,
                            ):
                                model, device, device_warnings = _fit_model(
                                    model_key,
                                    config["models"][model_key],
                                    train_x,
                                    train_y,
                                    int(config["seed"]) + fold,
                                )
                            fit_seconds = time.monotonic() - fit_started
                            del train_x, train_y
                            model_path = _model_path(cell_root, model_key, fold)
                            _save_model(model_key, model, model_path)
                            restored_runtime: dict[str, Any] = {
                                "cell": cell_key,
                                "fold": fold,
                                "fit_seconds": fit_seconds,
                                "device": device,
                                "device_warnings": device_warnings,
                                "restored": False,
                            }
                        else:
                            model, device, fold_state = restored
                            restored_runtime = {
                                "cell": cell_key,
                                "fold": fold,
                                "fit_seconds": float(fold_state["fit_seconds"]),
                                "device": device,
                                "device_warnings": fold_state.get("device_warnings", []),
                                "restored": True,
                            }
                            model_path = _model_path(cell_root, model_key, fold)
                        valid_x = features[np.ix_(validation_mask, columns)]
                        predict_started = time.monotonic()
                        probability = _predict(model_key, model, valid_x)
                        predict_seconds = time.monotonic() - predict_started
                        del valid_x, model
                        oof_probability[validation_mask] = probability
                        del probability
                        completed_fits += 1
                        runtime_record = {
                            **restored_runtime,
                            "predict_seconds": predict_seconds,
                            "peak_rss_gib": _peak_rss_gib(),
                            "train_rows": int(np.count_nonzero(training_mask)),
                            "validation_rows": int(np.count_nonzero(validation_mask)),
                            "model_sha256": _sha256(model_path),
                        }
                        fold_runtime.append(runtime_record)
                        _write_json(
                            cell_root / f"fold-{fold}-status.json",
                            {
                                "schema_version": "genis-inmemory-qualification-fold-state-v1",
                                "state": "finished",
                                **runtime_record,
                                **EVIDENCE,
                            },
                        )
                        _status(
                            output_root,
                            "RUNNING",
                            "qualification-matrix",
                            current_cell=cell_key,
                            current_fold=fold,
                            completed_fits=completed_fits,
                            total_fits=TOTAL_FITS,
                        )
                        elapsed = time.monotonic() - run_started
                        eta = elapsed / completed_fits * (TOTAL_FITS - completed_fits)
                        print(
                            f"FOLD_FINISHED cell={cell_key} fold={fold} "
                            f"completed={completed_fits}/{TOTAL_FITS} "
                            f"elapsed_seconds={elapsed:.3f} "
                            f"eta_seconds={eta:.3f} device={device}",
                            flush=True,
                        )
                    fold_results: list[dict[str, Any]] = []
                    for fold in range(fold_count):
                        validation_mask = folds == fold
                        training_mask = ~validation_mask
                        training_scores = 1.0 - oof_probability[
                            training_mask, :BENIGN_CLASS_COUNT
                        ].sum(axis=1)
                        threshold, allowed, actual = _threshold(
                            training_scores,
                            labels[training_mask],
                            float(config["metrics"]["alert_fpr"]),
                        )
                        aggregate = _metrics(
                            labels[validation_mask],
                            oof_probability[validation_mask],
                            threshold,
                            int(config["metrics"]["minimum_supported_class_rows"]),
                            config["data"]["class_order"],
                        )
                        fold_results.append(
                            {
                                "fold": fold,
                                **aggregate,
                                "threshold_training_allowed_false_positives": allowed,
                                "threshold_training_actual_false_positives": actual,
                                "runtime": fold_runtime[fold],
                            }
                        )
                    overall_threshold, _, _ = _threshold(
                        1.0 - oof_probability[:, :BENIGN_CLASS_COUNT].sum(axis=1),
                        labels,
                        float(config["metrics"]["alert_fpr"]),
                    )
                    cell_result = {
                        "split": split_key,
                        "feature_budget": feature_key,
                        "model": model_key,
                        "folds": fold_results,
                        "fold_summary": _fold_summary(fold_results),
                        "overall_oof": _metrics(
                            labels,
                            oof_probability,
                            overall_threshold,
                            int(config["metrics"]["minimum_supported_class_rows"]),
                            config["data"]["class_order"],
                        ),
                    }
                    cells[cell_key] = cell_result
                    _write_json(cell_root / "aggregate.json", cell_result)
                    del oof_probability
        results = {
            "schema_version": "genis-inmemory-baseline-qualification-results-v1",
            "run_id": config["run_id"],
            "input_summary": input_summary,
            "split_audit": split_audit,
            "feature_budget_summary": {
                "paper84_columns": 84,
                "safe76_columns": 76,
                "safe76_access": "内存中按冻结列索引访问，不持久化第二份矩阵",
            },
            "cells": cells,
            "decisions": _decisions(cells, config["gates"]),
            "runtime": {
                "elapsed_seconds": time.monotonic() - run_started,
                "fit_count": completed_fits,
                "peak_rss_gib": _peak_rss_gib(),
            },
            "persistence_audit": {
                "feature_matrices_written": False,
                "labels_written": False,
                "observation_hashes_written": False,
                "fold_memberships_written": False,
                "per_sample_probabilities_written": False,
                "threshold_samples_written": False,
            },
            "correlated_fold_warning": (
                "五折来自同一数据集，仅用于资格和根因诊断，不作显著性胜者声明。"
            ),
            **EVIDENCE,
        }
        _write_json(output_root / "results.json", results)
        _status(
            output_root,
            "FINISHED",
            "qualification-matrix-complete",
            completed_fits=completed_fits,
            total_fits=TOTAL_FITS,
            decision=results["decisions"]["decision"],
        )
        print(
            f"QUALIFICATION_MATRIX_FINISHED output={output_root} "
            f"decision={results['decisions']['decision']}",
            flush=True,
        )
        return results
    except KeyboardInterrupt:
        _status(output_root, "INTERRUPTED", "qualification-matrix", detail="收到中断信号")
        raise
    except Exception as error:
        _status(
            output_root,
            "FAILED",
            "qualification-matrix",
            failure_type=type(error).__name__,
            detail=str(error),
        )
        raise


def swanlab_publish(
    config_path: Path,
    output_override: Path | None,
    authorized_workspace: str,
    authorized_project: str,
) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = _load_config(config_path)
    output_root = (
        output_override.resolve()
        if output_override is not None
        else _resolve(config_path, config["paths"]["run_root"])
    )
    destination = config["swanlab"]
    if (
        authorized_workspace != destination["workspace"]
        or authorized_project != destination["project"]
    ):
        raise QualificationError("SwanLab 工作区或项目未获本轮逐字授权")
    status = _read_json(output_root / "status.json")
    results = _read_json(output_root / "results.json")
    if status.get("state") != "FINISHED" or results.get("official_test_accessed") is not False:
        raise QualificationError("只允许发布已完成且未访问官方测试的聚合结果")
    allowed = set(destination["allowed_upload_fields"])
    upload: dict[str, float] = {}
    for cell_key, cell in results["cells"].items():
        for metric_name, summary in cell["fold_summary"].items():
            if metric_name in allowed:
                upload[f"cells/{cell_key}/{metric_name}_mean"] = float(summary["mean"])
                upload[f"cells/{cell_key}/{metric_name}_std"] = float(summary["std"])
        for fold in cell["folds"]:
            for metric_name in ("fit_seconds", "predict_seconds", "peak_rss_gib"):
                if metric_name in allowed:
                    upload[f"runtime/{cell_key}/fold-{fold['fold']}/{metric_name}"] = float(
                        fold["runtime"][metric_name]
                    )
    try:
        import swanlab
    except (ImportError, OSError) as error:
        raise QualificationError("SwanLab 依赖不可用") from error
    run_handle = swanlab.init(
        workspace=authorized_workspace,
        project=authorized_project,
        experiment_name=destination["run_name"],
        mode=destination["mode"],
        config={
            "dataset": config["data"]["version"],
            "seed": config["seed"],
            "fold_count": config["splits"]["fold_count"],
            "fit_count": TOTAL_FITS,
            **EVIDENCE,
        },
    )
    swanlab.log(upload)
    swanlab.finish()
    receipt = {
        "schema_version": "genis-inmemory-qualification-swanlab-receipt-v1",
        "workspace": authorized_workspace,
        "project": authorized_project,
        "run_name": destination["run_name"],
        "uploaded_scalar_count": len(upload),
        "uploaded_fields": sorted(allowed),
        "forbidden_uploads": destination["forbidden_uploads"],
        "run_handle_type": type(run_handle).__name__,
        **EVIDENCE,
    }
    _write_json(output_root / "swanlab_publish_receipt.json", receipt)
    print(f"SWANLAB_PUBLISH_FINISHED scalar_count={len(upload)}", flush=True)
    return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="直接读取原始 ZIP 并运行八格资格矩阵")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--archive-path", type=Path)
    run_parser.add_argument("--output-root", type=Path)
    publish_parser = subparsers.add_parser("swanlab-publish", help="上传白名单聚合指标")
    publish_parser.add_argument("--config", type=Path, required=True)
    publish_parser.add_argument("--output-root", type=Path)
    publish_parser.add_argument("--authorized-workspace", required=True)
    publish_parser.add_argument("--authorized-project", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            run(args.config, args.archive_path, args.output_root)
        else:
            swanlab_publish(
                args.config,
                args.output_root,
                args.authorized_workspace,
                args.authorized_project,
            )
    except QualificationError as error:
        print(f"资格矩阵失败：{error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
