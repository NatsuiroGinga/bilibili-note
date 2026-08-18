"""跨年度稀有恶意质量保护非对称部分最优传输 Q0。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import sys
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
from scipy.special import expit, logsumexp
from scipy.stats import rankdata, spearmanr
from sklearn.cluster import MiniBatchKMeans
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


ROLES = ("source-train", "source-validation", "target-prefix", "target-development")
FEATURE_ARRAYS = ("x_value", "x_missing", "delta_t_us")
IDENTITY_ARRAYS = ("sample_id",)
SOURCE_ROLES = ("source-train", "source-validation")
VARIANTS = (
    "B0_XGB_ANCHOR",
    "U1_FULL_OT",
    "U2_ASYM_POT_NO_FLOOR",
    "M1_PROTECTED_ASYM_POT",
    "M1_M2_SAFE_ROLLBACK",
)
SCHEMA = "crossyear-protected-asymmetric-pot-q0-config-v1"
EPS = 1e-12


class ProtectedPartialOTError(RuntimeError):
    """P0 输入、阶段或数值结果违反冻结合同。"""


@dataclass(frozen=True)
class CacheView:
    root: Path
    manifest_path: Path
    manifest: Mapping[str, Any]
    arrays: Mapping[str, Mapping[str, Path]]
    target_label_record: Mapping[str, Any]


@dataclass(frozen=True)
class PrototypeSet:
    embedding: np.ndarray
    leaf: np.ndarray
    score: np.ndarray
    weight: np.ndarray
    label: np.ndarray | None


@dataclass(frozen=True)
class TransportResult:
    plan: np.ndarray
    converged: bool
    iterations: int
    marginal_error: float
    objective: float
    total_mass: float
    malicious_mass: float
    malicious_required: float
    slack_ratio: float
    effective_malicious_prototypes: float
    unmatched_target_mass: float
    maximum_coupling_concentration: float


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProtectedPartialOTError(f"无法读取 JSON：{path}") from error
    if not isinstance(value, dict):
        raise ProtectedPartialOTError(f"JSON 顶层必须是对象：{path}")
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
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _array_sha256(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    return hashlib.sha256(value.view(np.uint8)).hexdigest()


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _load_config(path: Path) -> dict[str, Any]:
    config = _json(path)
    if config.get("schema_version") != SCHEMA:
        raise ProtectedPartialOTError("配置模式版本不匹配")
    required_false = (
        "target_prefix_labels_available",
        "target_labels_used_for_tuning",
        "formal_paper_evidence",
        "final_accessed",
    )
    if any(config.get(key) is not False for key in required_false):
        raise ProtectedPartialOTError("配置未冻结标签隔离或筛选证据边界")
    if config.get("target_labels_opened_after_all_probability_seals") is not True:
        raise ProtectedPartialOTError("目标开发标签必须在全部概率封存后打开")
    if config.get("screening_only") is not True:
        raise ProtectedPartialOTError("本入口只允许 Q0 筛选")
    variants = config.get("variants")
    if not isinstance(variants, list) or tuple(item.get("key") for item in variants) != VARIANTS:
        raise ProtectedPartialOTError("五格变体集合或顺序不匹配")
    xgb = config.get("xgboost")
    if (
        not isinstance(xgb, Mapping)
        or xgb.get("tree_method") != "hist"
        or xgb.get("device") != "cuda"
    ):
        raise ProtectedPartialOTError("XGBoost 强锚必须固定 hist/cuda")
    return config


def _manifest_array(
    raw: object,
    cache_root: Path,
    description: str,
    *,
    verify_hash: bool = True,
) -> Path:
    if not isinstance(raw, Mapping):
        raise ProtectedPartialOTError(f"数组清单缺失：{description}")
    path = Path(str(raw.get("path", ""))).resolve()
    if not _within(path, cache_root) or path.is_symlink() or not path.is_file():
        raise ProtectedPartialOTError(f"数组不在只读缓存根或不是普通文件：{description}")
    if verify_hash and _sha256(path) != raw.get("sha256"):
        raise ProtectedPartialOTError(f"数组 SHA-256 不匹配：{description}")
    value = np.load(path, mmap_mode="r", allow_pickle=False)
    if list(value.shape) != raw.get("shape") or str(value.dtype) != raw.get("dtype"):
        raise ProtectedPartialOTError(f"数组形状或类型漂移：{description}")
    return path


def load_cache(cache_manifest: Path, *, verify_all_hashes: bool = True) -> CacheView:
    """只读取缓存清单；不打开目标开发标签数组。"""
    manifest = _json(cache_manifest)
    if manifest.get("schema_version") != "lspr-crossyear-python-cache-v1":
        raise ProtectedPartialOTError("缓存清单模式版本漂移")
    if manifest.get("final_accessed") is not False:
        raise ProtectedPartialOTError("缓存清单必须声明 final_accessed=false")
    fields = manifest.get("model_fields")
    if not isinstance(fields, list) or len(fields) != 77 or len(set(fields)) != 77:
        raise ProtectedPartialOTError("缓存必须含 77 个有序合法字段")
    root = Path(str(manifest.get("formal_cache_root", ""))).resolve()
    if cache_manifest.resolve().parent != root or not root.is_dir():
        raise ProtectedPartialOTError("缓存清单不在 formal_cache_root 内")
    raw_arrays = manifest.get("arrays")
    if not isinstance(raw_arrays, Mapping) or set(raw_arrays) != set(ROLES):
        raise ProtectedPartialOTError("缓存必须恰有四个角色")
    arrays: dict[str, dict[str, Path]] = {}
    for role in ROLES:
        entries = raw_arrays[role]
        if not isinstance(entries, Mapping):
            raise ProtectedPartialOTError(f"角色数组清单不合法：{role}")
        required = set(FEATURE_ARRAYS) | set(IDENTITY_ARRAYS)
        if role in SOURCE_ROLES:
            required.add("labels")
        if role == "target-prefix" and "labels" in entries:
            raise ProtectedPartialOTError("target-prefix 禁止存在标签数组")
        if not required.issubset(entries):
            raise ProtectedPartialOTError(f"角色缺少必要数组：{role}")
        resolved: dict[str, Path] = {}
        expected_rows: int | None = None
        for name, record in entries.items():
            path = _manifest_array(
                record,
                root,
                f"{role}.{name}",
                verify_hash=verify_all_hashes,
            )
            value = np.load(path, mmap_mode="r", allow_pickle=False)
            rows = int(value.shape[0])
            if expected_rows is None:
                expected_rows = rows
            elif rows != expected_rows:
                raise ProtectedPartialOTError(f"角色数组行数不一致：{role}")
            resolved[str(name)] = path
        arrays[role] = resolved
    target_evaluation = manifest.get("target_development_evaluation")
    if not isinstance(target_evaluation, Mapping):
        raise ProtectedPartialOTError("缓存未登记独立目标开发评价旁车")
    label_record = target_evaluation.get("labels")
    if not isinstance(label_record, Mapping):
        raise ProtectedPartialOTError("缓存未登记目标开发标签旁车")
    # 审计阶段只检查路径边界和声明，不打开、哈希或统计标签文件。
    label_path = Path(str(label_record.get("path", ""))).resolve()
    if not _within(label_path, root) or label_path.is_symlink():
        raise ProtectedPartialOTError("目标开发标签旁车越出缓存根或为符号链接")
    return CacheView(root, cache_manifest.resolve(), manifest, arrays, dict(label_record))


def _load_role_arrays(cache: CacheView, role: str, names: Sequence[str]) -> dict[str, np.ndarray]:
    if role not in ROLES:
        raise ProtectedPartialOTError(f"未知缓存角色：{role}")
    result: dict[str, np.ndarray] = {}
    for name in names:
        path = cache.arrays[role].get(name)
        if path is None:
            raise ProtectedPartialOTError(f"缓存角色缺少数组：{role}.{name}")
        result[name] = np.load(path, mmap_mode="r", allow_pickle=False)
    return result


def _features(cache: CacheView, role: str) -> np.ndarray:
    arrays = _load_role_arrays(cache, role, FEATURE_ARRAYS)
    value = np.asarray(arrays["x_value"], dtype=np.float32)
    missing = np.asarray(arrays["x_missing"], dtype=np.float32)
    delta = np.log1p(np.maximum(np.asarray(arrays["delta_t_us"], dtype=np.float64), 0.0)).astype(
        np.float32
    )[:, None]
    if value.ndim != 2 or value.shape[1] != 77 or missing.shape != value.shape:
        raise ProtectedPartialOTError(f"{role} 不符合 77+77+1 输入合同")
    result = np.concatenate((value, missing, delta), axis=1)
    if result.shape[1] != 155 or not np.isfinite(result).all():
        raise ProtectedPartialOTError(f"{role} 的 155 维输入含非有限值")
    return result


def _sample_ids(cache: CacheView, role: str) -> np.ndarray:
    return np.asarray(_load_role_arrays(cache, role, ("sample_id",))["sample_id"])


def _labels(cache: CacheView, role: str) -> np.ndarray:
    if role not in SOURCE_ROLES:
        raise ProtectedPartialOTError("训练/适应阶段只允许读取源标签")
    labels = np.asarray(_load_role_arrays(cache, role, ("labels",))["labels"], dtype=np.uint8)
    if not np.isin(labels, (0, 1)).all():
        raise ProtectedPartialOTError(f"{role} 标签不是二元 0/1")
    return labels


def audit(config_path: Path, cache_manifest: Path | None) -> dict[str, Any]:
    config = _load_config(config_path)
    manifest_path = cache_manifest or Path(config["paths"]["cache_manifest"])
    cache = load_cache(manifest_path)
    rows = {
        role: int(np.load(cache.arrays[role]["x_value"], mmap_mode="r").shape[0]) for role in ROLES
    }
    result = {
        "schema_version": "crossyear-protected-pot-cache-audit-v1",
        "state": "passed",
        "cache_manifest": str(cache.manifest_path),
        "cache_manifest_sha256": _sha256(cache.manifest_path),
        "roles": list(ROLES),
        "row_counts": rows,
        "model_field_count": 77,
        "input_dimension": 155,
        "target_prefix_labels_discoverable": False,
        "target_development_label_file_opened": False,
        "final_accessed": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def _xgboost_model(config: Mapping[str, Any]) -> Any:
    try:
        from xgboost import XGBClassifier
    except (ImportError, OSError) as error:
        raise ProtectedPartialOTError(f"XGBoost 依赖不可用：{error}") from error
    params = dict(config["xgboost"])
    params["random_state"] = int(config["seed"])
    return XGBClassifier(**params)


def _booster_device(booster: Any) -> tuple[str, Mapping[str, Any]]:
    booster_config = json.loads(booster.save_config())
    try:
        device = booster_config["learner"]["generic_param"]["device"]
    except (KeyError, TypeError) as error:
        raise ProtectedPartialOTError("XGBoost Booster 配置缺少设备字段") from error
    if not isinstance(device, str):
        raise ProtectedPartialOTError("XGBoost Booster 设备字段不是字符串")
    return device, booster_config


def _booster_predict(model: Any, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """显式 DMatrix 预测，避免 sklearn inplace_predict 的跨设备路径。"""
    try:
        from xgboost import DMatrix
    except (ImportError, OSError) as error:
        raise ProtectedPartialOTError("XGBoost DMatrix 接口不可用") from error
    params = model.get_xgb_params()
    matrix = DMatrix(x, nthread=int(params.get("n_jobs", 1)))
    booster = model.get_booster()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        score = np.asarray(booster.predict(matrix), dtype=np.float32)
        leaf = np.asarray(booster.predict(matrix, pred_leaf=True), dtype=np.int32)
    messages = [str(item.message) for item in caught]
    if "mismatched devices" in " ".join(messages).lower():
        raise ProtectedPartialOTError(f"显式 DMatrix 预测仍出现设备不匹配：{messages}")
    return score, leaf


def _save_array(path: Path, value: np.ndarray) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(f"{path.name}.partial.{os.getpid()}")
    with partial.open("wb") as handle:
        np.save(handle, value, allow_pickle=False)
    partial.replace(path)
    return {
        "path": str(path.resolve()),
        "shape": list(value.shape),
        "dtype": str(value.dtype),
        "sha256": _sha256(path),
    }


def _predict_representations(
    model: Any,
    cache: CacheView,
    role: str,
    representation_root: Path,
) -> dict[str, Any]:
    x = _features(cache, role)
    score, leaf = _booster_predict(model, x)
    sample_id = _sample_ids(cache, role)
    if not np.isfinite(score).all() or score.shape != (len(x),):
        raise ProtectedPartialOTError(f"{role} 强锚概率无效")
    if leaf.ndim != 2 or leaf.shape[0] != len(x):
        raise ProtectedPartialOTError(f"{role} 叶表示无效")
    role_root = representation_root / role
    return {
        "score": _save_array(role_root / "score.npy", score),
        "leaf": _save_array(role_root / "leaf.npy", leaf),
        "sample_id_sha256": _array_sha256(sample_id),
        "row_count": int(len(x)),
        "labels_read": role in SOURCE_ROLES,
    }


def fit_anchor(config_path: Path, output_root: Path, cache_manifest: Path | None) -> dict[str, Any]:
    config = _load_config(config_path)
    cache = load_cache(cache_manifest or Path(config["paths"]["cache_manifest"]))
    anchor_root = output_root / "anchor"
    if anchor_root.exists():
        raise ProtectedPartialOTError(f"强锚目录已存在，拒绝覆盖：{anchor_root}")
    anchor_root.mkdir(parents=True)
    x = _features(cache, "source-train")
    y = _labels(cache, "source-train")
    if set(np.unique(y)) != {0, 1}:
        raise ProtectedPartialOTError("source-train 必须同时含良性和恶意")
    model = _xgboost_model(config)
    started = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(x, y)
    warning_text = [str(item.message) for item in caught]
    params = model.get_xgb_params()
    if params.get("device") != "cuda" or params.get("tree_method") != "hist":
        raise ProtectedPartialOTError("XGBoost 强锚配置回读不是 hist/cuda")
    booster = model.get_booster()
    booster_device, booster_config = _booster_device(booster)
    if booster_device != "cuda:0":
        raise ProtectedPartialOTError(
            f"完整 source-train 拟合后的 Booster 设备不是 cuda:0：{booster_device}"
        )
    lowered_warnings = " ".join(warning_text).lower()
    if "training on cpu" in lowered_warnings or "device=cpu" in lowered_warnings:
        raise ProtectedPartialOTError(f"完整 source-train 拟合出现 CPU 训练警告：{warning_text}")
    model_path = anchor_root / "anchor-model.joblib"
    joblib.dump(model, model_path, compress=3)
    booster_path = anchor_root / "anchor-model.ubj"
    booster.save_model(booster_path)
    representation_root = output_root / "representations"
    records = {
        role: _predict_representations(model, cache, role, representation_root) for role in ROLES
    }
    cpu_root = Path(config["paths"]["shared_cpu_xgboost_root"])
    cpu_seal = _json(cpu_root / "probability_seal.json")
    target_sample_hash = records["target-development"]["sample_id_sha256"]
    if cpu_seal.get("sample_id_sha256") != target_sample_hash:
        raise ProtectedPartialOTError("GPU 强锚与共享 CPU v2 的目标开发样本顺序不一致")
    cpu_probability_path = cpu_root / "target_development_probability.npy"
    if _sha256(cpu_probability_path) != cpu_seal.get("probability_sha256"):
        raise ProtectedPartialOTError("共享 CPU v2 概率封存 SHA-256 不匹配")
    cpu_probability = np.asarray(
        np.load(cpu_probability_path, allow_pickle=False), dtype=np.float64
    )
    gpu_probability = np.asarray(
        np.load(representation_root / "target-development" / "score.npy", allow_pickle=False),
        dtype=np.float64,
    )
    if cpu_probability.shape != gpu_probability.shape or not np.isfinite(cpu_probability).all():
        raise ProtectedPartialOTError("GPU 强锚与共享 CPU v2 概率行数或有限值不一致")
    cpu_gpu_diagnostic = {
        "row_count": int(len(gpu_probability)),
        "sample_id_sha256": target_sample_hash,
        "pearson_correlation": float(np.corrcoef(cpu_probability, gpu_probability)[0, 1]),
        "spearman_correlation": float(spearmanr(cpu_probability, gpu_probability).statistic),
        "maximum_absolute_difference": float(np.max(np.abs(cpu_probability - gpu_probability))),
        "failure_gate": False,
    }
    import xgboost

    result = {
        "schema_version": "crossyear-protected-pot-anchor-receipt-v1",
        "state": "finished",
        "model": {
            "joblib_path": str(model_path.resolve()),
            "joblib_sha256": _sha256(model_path),
            "booster_path": str(booster_path.resolve()),
            "booster_sha256": _sha256(booster_path),
            "xgboost_version": xgboost.__version__,
            "parameters": params,
            "booster_device": booster_device,
            "booster_config": booster_config,
            "prediction_interface": "Booster.predict(DMatrix)",
        },
        "representations": records,
        "shared_cpu_v2_diagnostic": cpu_gpu_diagnostic,
        "cache_manifest_sha256": _sha256(cache.manifest_path),
        "config_sha256": _sha256(config_path),
        "training_seconds": time.perf_counter() - started,
        "warnings": warning_text,
        "target_development_labels_opened": False,
        "target_prefix_labels_used": False,
        "final_accessed": False,
    }
    _write_json(anchor_root / "anchor-model-receipt.json", result)
    return result


def _load_representation(output_root: Path, role: str) -> tuple[np.ndarray, np.ndarray]:
    leaf = np.load(output_root / "representations" / role / "leaf.npy", mmap_mode="r")
    score = np.load(output_root / "representations" / role / "score.npy", mmap_mode="r")
    return np.asarray(leaf), np.asarray(score, dtype=np.float64)


def _leaf_embedding(leaf: np.ndarray, dimension: int, seed: int) -> np.ndarray:
    rows, trees = leaf.shape
    output = np.zeros((rows, dimension), dtype=np.float32)
    row_index = np.arange(rows)
    # 按树累加，避免构造 rows×trees 的重复行索引和哈希临时数组。
    for tree in range(trees):
        value = leaf[:, tree].astype(np.uint64, copy=False)
        hashed = (
            value * np.uint64(11400714819323198485)
            + np.uint64(tree) * np.uint64(7046029254386353131)
            + np.uint64(seed)
        )
        buckets = (hashed % np.uint64(dimension)).astype(np.int64)
        signs = np.where(((hashed >> np.uint64(13)) & np.uint64(1)) == 0, 1.0, -1.0).astype(
            np.float32
        )
        np.add.at(output, (row_index, buckets), signs)
    output /= math.sqrt(max(trees, 1))
    return output


def _deterministic_limit(indices: np.ndarray, maximum: int, seed: int) -> np.ndarray:
    if len(indices) <= maximum:
        return indices
    generator = np.random.default_rng(seed)
    return np.sort(generator.choice(indices, size=maximum, replace=False))


def _prototype_set(
    leaf: np.ndarray,
    score: np.ndarray,
    label: np.ndarray | None,
    maximum: int,
    config: Mapping[str, Any],
    seed: int,
) -> PrototypeSet:
    dimension = int(config["prototypes"]["leaf_hash_dimension"])
    fit_maximum = int(
        config["prototypes"]["target_fit_maximum"]
        if label is None
        else config["prototypes"]["source_fit_maximum_per_class"]
    )
    all_indices = np.arange(len(score))
    fit_indices = _deterministic_limit(all_indices, fit_maximum, seed)
    embedding_seed = int(config["seed"])
    fit_embedding = _leaf_embedding(leaf[fit_indices], dimension, embedding_seed)
    clusters = min(maximum, len(fit_indices))
    if clusters < 1:
        raise ProtectedPartialOTError("原型输入为空")
    kmeans = MiniBatchKMeans(
        n_clusters=clusters,
        batch_size=int(config["prototypes"]["cluster_batch_size"]),
        random_state=seed,
        n_init=3,
        max_iter=100,
        reassignment_ratio=0.0,
    )
    kmeans.fit(fit_embedding)
    full_embedding = _leaf_embedding(leaf, dimension, embedding_seed)
    assignment = kmeans.predict(full_embedding)
    centers = np.asarray(kmeans.cluster_centers_, dtype=np.float32)
    representative: list[int] = []
    weights: list[float] = []
    for cluster in range(clusters):
        members = np.flatnonzero(assignment == cluster)
        if not len(members):
            continue
        distance = np.sum((full_embedding[members] - centers[cluster]) ** 2, axis=1)
        representative.append(int(members[int(np.argmin(distance))]))
        weights.append(float(len(members) / len(score)))
    chosen = np.asarray(representative, dtype=np.int64)
    return PrototypeSet(
        embedding=full_embedding[chosen],
        leaf=np.asarray(leaf[chosen]),
        score=np.asarray(score[chosen], dtype=np.float64),
        weight=np.asarray(weights, dtype=np.float64),
        label=None if label is None else np.asarray(label[chosen], dtype=np.uint8),
    )


def _source_prototypes(
    leaf: np.ndarray,
    score: np.ndarray,
    labels: np.ndarray,
    config: Mapping[str, Any],
    seed: int,
) -> PrototypeSet:
    sets: list[PrototypeSet] = []
    for value, key in ((0, "benign_maximum"), (1, "malicious_maximum")):
        indices = np.flatnonzero(labels == value)
        part = _prototype_set(
            leaf[indices],
            score[indices],
            np.full(len(indices), value, dtype=np.uint8),
            int(config["prototypes"][key]),
            config,
            seed + value,
        )
        # 恢复该类在未平衡源分布中的原始质量。
        prior = len(indices) / len(labels)
        sets.append(
            PrototypeSet(
                part.embedding,
                part.leaf,
                part.score,
                part.weight * prior,
                part.label,
            )
        )
    return PrototypeSet(
        embedding=np.concatenate([item.embedding for item in sets]),
        leaf=np.concatenate([item.leaf for item in sets]),
        score=np.concatenate([item.score for item in sets]),
        weight=np.concatenate([item.weight for item in sets]),
        label=np.concatenate([item.label for item in sets if item.label is not None]),
    )


def _logit(probability: np.ndarray) -> np.ndarray:
    return np.log(np.clip(probability, 1e-6, 1 - 1e-6)) - np.log1p(
        -np.clip(probability, 1e-6, 1 - 1e-6)
    )


def _cost(source: PrototypeSet, target: PrototypeSet, config: Mapping[str, Any]) -> np.ndarray:
    leaf_distance = np.mean(source.leaf[:, None, :] != target.leaf[None, :, :], axis=2)
    source_logit = _logit(source.score)
    target_logit = _logit(target.score)
    sampled = np.abs(source_logit[:, None] - source_logit[None, :])
    q95 = float(np.quantile(sampled, 0.95))
    score_distance = np.abs(source_logit[:, None] - target_logit[None, :]) / (q95 + 1e-6)
    transport = config["transport"]
    result = (
        float(transport["cost_leaf_weight"]) * leaf_distance
        + float(transport["cost_score_weight"]) * score_distance
    )
    if not np.isfinite(result).all():
        raise ProtectedPartialOTError("原型传输成本含非有限值")
    return result


def _sinkhorn(
    cost: np.ndarray,
    source_weight: np.ndarray,
    target_weight: np.ndarray,
    mass: float,
    epsilon: float,
    tau_source: float,
    tau_target: float,
    maximum_iterations: int,
    tolerance: float,
    source_bias: np.ndarray | None = None,
) -> tuple[np.ndarray, bool, int, float]:
    if not 0 < mass <= 1:
        raise ProtectedPartialOTError("传输质量必须位于 (0,1]")
    a = np.clip(source_weight / source_weight.sum(), EPS, None)
    b = np.clip(target_weight / target_weight.sum(), EPS, None)
    adjusted = cost if source_bias is None else cost - source_bias[:, None]
    log_kernel = -adjusted / epsilon
    alpha_s = tau_source / (tau_source + epsilon)
    alpha_t = tau_target / (tau_target + epsilon)
    log_u = np.zeros(len(a), dtype=np.float64)
    log_v = np.zeros(len(b), dtype=np.float64)
    converged = False
    error = math.inf
    for iteration in range(1, maximum_iterations + 1):
        old_u = log_u.copy()
        old_v = log_v.copy()
        log_u = alpha_s * (np.log(a) - logsumexp(log_kernel + log_v[None, :], axis=1))
        log_v = alpha_t * (np.log(b) - logsumexp(log_kernel + log_u[:, None], axis=0))
        error = max(float(np.max(np.abs(log_u - old_u))), float(np.max(np.abs(log_v - old_v))))
        if error <= tolerance:
            converged = True
            break
    log_plan = log_u[:, None] + log_kernel + log_v[None, :]
    log_plan -= logsumexp(log_plan)
    plan = np.exp(log_plan) * mass
    if not np.isfinite(plan).all():
        raise ProtectedPartialOTError("Sinkhorn 产生非有限耦合")
    return plan, converged, iteration, error


def solve_transport(
    source: PrototypeSet,
    target: PrototypeSet,
    config: Mapping[str, Any],
    parameters: Mapping[str, float],
    *,
    protect_malicious: bool,
) -> TransportResult:
    if source.label is None:
        raise ProtectedPartialOTError("源原型缺少标签")
    transport = config["transport"]
    cost = _cost(source, target, config)
    mass = float(parameters["mass"])
    epsilon = float(parameters["epsilon"])
    tau_target = float(transport["tau_target"])
    tau_source = tau_target * float(parameters["tau_ratio"])
    malicious_prior = float(source.weight[source.label == 1].sum() / source.weight.sum())
    required = float(parameters["rho_plus"]) * malicious_prior if protect_malicious else 0.0
    bias = np.zeros(len(source.weight), dtype=np.float64)
    best: tuple[np.ndarray, bool, int, float] | None = None
    if protect_malicious and required > mass + EPS:
        raise ProtectedPartialOTError("恶意质量下限超过传输总质量，配置不可行")
    lower = 0.0
    upper = 64.0
    dual_iterations = int(transport["malicious_dual_iterations"])
    for _ in range(dual_iterations if protect_malicious else 1):
        multiplier = (lower + upper) / 2 if protect_malicious else 0.0
        bias[:] = 0.0
        bias[source.label == 1] = multiplier
        best = _sinkhorn(
            cost,
            source.weight,
            target.weight,
            mass,
            epsilon,
            tau_source,
            tau_target,
            int(transport["maximum_iterations"]),
            float(transport["convergence_tolerance"]),
            bias,
        )
        malicious_mass = float(best[0][source.label == 1].sum())
        if not protect_malicious or malicious_mass >= required:
            upper = multiplier
        else:
            lower = multiplier
    assert best is not None
    plan, converged, iterations, error = best
    row_mass = plan.sum(axis=1)
    column_mass = plan.sum(axis=0)
    malicious_mass = float(row_mass[source.label == 1].sum())
    slack = max(required - malicious_mass, 0.0)
    malicious_weights = row_mass[source.label == 1]
    effective = (
        float(malicious_weights.sum() ** 2 / max(float(np.square(malicious_weights).sum()), EPS))
        if malicious_weights.size
        else 0.0
    )
    normalized = plan / max(float(plan.sum()), EPS)
    entropy = -float(np.sum(normalized * np.log(np.clip(normalized, EPS, None))))
    objective = float(np.sum(plan * cost) - epsilon * entropy)
    return TransportResult(
        plan=plan,
        converged=converged,
        iterations=iterations,
        marginal_error=error,
        objective=objective,
        total_mass=float(plan.sum()),
        malicious_mass=malicious_mass,
        malicious_required=required,
        slack_ratio=slack / max(required, EPS),
        effective_malicious_prototypes=effective,
        unmatched_target_mass=max(1.0 - float(column_mass.sum()), 0.0),
        maximum_coupling_concentration=float(plan.max() / max(float(plan.sum()), EPS)),
    )


def _transport_receipt(result: TransportResult) -> dict[str, Any]:
    return {
        "converged": result.converged,
        "iterations": result.iterations,
        "marginal_error": result.marginal_error,
        "objective": result.objective,
        "total_mass": result.total_mass,
        "malicious_mass": result.malicious_mass,
        "malicious_required": result.malicious_required,
        "slack_ratio": result.slack_ratio,
        "effective_malicious_prototypes": result.effective_malicious_prototypes,
        "unmatched_target_mass": result.unmatched_target_mass,
        "maximum_coupling_concentration": result.maximum_coupling_concentration,
    }


def _prototype_correction(
    source: PrototypeSet,
    target: PrototypeSet,
    result: TransportResult,
    config: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    if source.label is None:
        raise ProtectedPartialOTError("源原型缺少标签")
    q = result.plan.sum(axis=0)
    malicious = result.plan[source.label == 1].sum(axis=0)
    probability = malicious / (q + EPS)
    support = np.minimum(1.0, q / (target.weight + EPS))
    bound = float(config["transport"]["correction_logit_bound"])
    correction = np.clip(_logit(probability) - _logit(target.score), -bound, bound)
    return correction, support


def _apply_correction(
    source: PrototypeSet,
    target: PrototypeSet,
    result: TransportResult,
    leaf: np.ndarray,
    anchor_score: np.ndarray,
    config: Mapping[str, Any],
    support_radius: float,
    assignment: tuple[np.ndarray, np.ndarray] | None = None,
) -> tuple[np.ndarray, dict[str, Any]]:
    correction, support = _prototype_correction(source, target, result, config)
    if assignment is None:
        assignment = _nearest_target_prototypes(leaf, target, config)
    nearest, distance = assignment
    accepted = distance <= support_radius
    delta = np.zeros(len(anchor_score), dtype=np.float64)
    delta[accepted] = (
        float(config["transport"]["correction_weight"])
        * support[nearest[accepted]]
        * correction[nearest[accepted]]
    )
    probability = expit(_logit(anchor_score) + delta).astype(np.float32)
    return probability, {
        "support_outside_rate": float((~accepted).mean()),
        "corrected_count": int(accepted.sum()),
        "correction_abs_p95": float(np.quantile(np.abs(delta), 0.95)),
        "correction_abs_p99": float(np.quantile(np.abs(delta), 0.99)),
    }


def _nearest_target_prototypes(
    leaf: np.ndarray,
    target: PrototypeSet,
    config: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    embedding = _leaf_embedding(
        leaf,
        int(config["prototypes"]["leaf_hash_dimension"]),
        int(config["seed"]),
    )
    nearest = np.empty(len(embedding), dtype=np.int32)
    distance = np.empty(len(embedding), dtype=np.float32)
    # 固定分块避免 26 万目标样本与 1024 原型形成超过内存上限的三维广播。
    for start in range(0, len(embedding), 2048):
        stop = min(start + 2048, len(embedding))
        squared = np.sum(
            (embedding[start:stop, None, :] - target.embedding[None, :, :]) ** 2,
            axis=2,
        )
        nearest[start:stop] = np.argmin(squared, axis=1)
        distance[start:stop] = np.sqrt(np.min(squared, axis=1))
    return nearest, distance


def _source_rounds(rows: int, count: int) -> list[tuple[np.ndarray, np.ndarray]]:
    blocks = np.array_split(np.arange(rows), count)
    rounds: list[tuple[np.ndarray, np.ndarray]] = []
    for block in blocks:
        boundary = len(block) // 2
        prefix = block[:boundary]
        development = block[boundary:]
        if not len(prefix) or not len(development):
            raise ProtectedPartialOTError("源验证连续时间块不足")
        rounds.append((prefix, development))
    return rounds


def _fixed_budget_recall(
    labels: np.ndarray, probability: np.ndarray, budgets: Sequence[int]
) -> dict[str, float]:
    positives = int(labels.sum())
    result: dict[str, float] = {}
    for budget in budgets:
        requested = max(1, int(math.floor(len(labels) * int(budget) / 1_000_000)))
        order = np.argsort(-probability, kind="stable")
        cutoff = probability[order[min(requested, len(labels)) - 1]]
        selected = probability >= cutoff
        result[str(budget)] = float(labels[selected].sum() / max(positives, 1))
    return result


def _gate_observations(
    result: TransportResult,
    anchor: np.ndarray,
    adapted: np.ndarray,
    budgets: Sequence[int],
) -> dict[str, float]:
    anchor_rank = rankdata(anchor, method="average")
    adapted_rank = rankdata(adapted, method="average")
    flips = (
        np.mean(
            (anchor_rank[:, None] - anchor_rank[None, :])
            * (adapted_rank[:, None] - adapted_rank[None, :])
            < 0
        )
        if len(anchor) <= 4096
        else np.mean(np.sign(np.diff(anchor)) != np.sign(np.diff(adapted)))
    )
    observations = {
        "slack_ratio": result.slack_ratio,
        "effective_malicious_prototypes": result.effective_malicious_prototypes,
        "unmatched_target_mass": result.unmatched_target_mass,
        "maximum_coupling_concentration": result.maximum_coupling_concentration,
        "spearman": float(spearmanr(anchor, adapted).statistic),
        "logit_change_p95": float(np.quantile(np.abs(_logit(adapted) - _logit(anchor)), 0.95)),
        "logit_change_p99": float(np.quantile(np.abs(_logit(adapted) - _logit(anchor)), 0.99)),
        "ranking_flip_rate": float(flips),
    }
    for budget in budgets:
        count = max(1, int(math.floor(len(anchor) * int(budget) / 1_000_000)))
        left = set(np.argsort(-anchor, kind="stable")[:count].tolist())
        right = set(np.argsort(-adapted, kind="stable")[:count].tolist())
        observations[f"topk_jaccard_{budget}"] = len(left & right) / max(len(left | right), 1)
    return observations


def source_freeze(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    cache = load_cache(Path(config["paths"]["cache_manifest"]))
    anchor_receipt = _json(output_root / "anchor" / "anchor-model-receipt.json")
    if anchor_receipt.get("target_development_labels_opened") is not False:
        raise ProtectedPartialOTError("强锚收据违反目标标签隔离")
    train_leaf, train_score = _load_representation(output_root, "source-train")
    validation_leaf, validation_score = _load_representation(output_root, "source-validation")
    train_labels = _labels(cache, "source-train")
    validation_labels = _labels(cache, "source-validation")
    source = _source_prototypes(train_leaf, train_score, train_labels, config, int(config["seed"]))
    parameters: list[dict[str, float]] = []
    transport = config["transport"]
    for mass in transport["mass_grid"]:
        for epsilon in transport["epsilon_grid"]:
            for ratio in transport["tau_ratio_grid"]:
                for rho in transport["rho_plus_grid"]:
                    parameters.append(
                        {
                            "mass": float(mass),
                            "epsilon": float(epsilon),
                            "tau_ratio": float(ratio),
                            "rho_plus": float(rho),
                        }
                    )
    rounds = _source_rounds(
        len(validation_labels), int(config["source_selection"]["chronological_rounds"])
    )
    candidates: list[dict[str, Any]] = []
    harmless_observations: list[dict[str, float]] = []
    harmful_cases: list[dict[str, Any]] = []
    budgets = [int(value) for value in config["evaluation"]["alert_budgets_per_million"]]
    round_contexts: list[
        tuple[np.ndarray, np.ndarray, PrototypeSet, float, tuple[np.ndarray, np.ndarray]]
    ] = []
    for round_index, (prefix_indices, development_indices) in enumerate(rounds):
        target = _prototype_set(
            validation_leaf[prefix_indices],
            validation_score[prefix_indices],
            None,
            int(config["prototypes"]["target_maximum"]),
            config,
            int(config["seed"]) + 1000 + round_index,
        )
        training_embedding = _leaf_embedding(
            validation_leaf[prefix_indices],
            int(config["prototypes"]["leaf_hash_dimension"]),
            int(config["seed"]),
        )
        nearest_parts: list[np.ndarray] = []
        for start in range(0, len(training_embedding), 2048):
            stop = min(start + 2048, len(training_embedding))
            squared = np.sum(
                (training_embedding[start:stop, None, :] - target.embedding[None, :, :]) ** 2,
                axis=2,
            )
            nearest_parts.append(np.min(squared, axis=1))
        support_radius = float(
            np.sqrt(
                np.quantile(
                    np.concatenate(nearest_parts),
                    float(config["transport"]["support_radius_quantile"]),
                )
            )
        )
        development_assignment = _nearest_target_prototypes(
            validation_leaf[development_indices], target, config
        )
        round_contexts.append(
            (prefix_indices, development_indices, target, support_radius, development_assignment)
        )
    for parameter_index, parameter in enumerate(parameters):
        round_metrics: list[dict[str, Any]] = []
        for round_index, (
            _,
            development_indices,
            target,
            support_radius,
            development_assignment,
        ) in enumerate(round_contexts):
            solved = solve_transport(source, target, config, parameter, protect_malicious=True)
            if not solved.converged:
                round_metrics.append({"round": round_index, "converged": False})
                continue
            adapted, _ = _apply_correction(
                source,
                target,
                solved,
                validation_leaf[development_indices],
                validation_score[development_indices],
                config,
                support_radius,
                development_assignment,
            )
            labels = validation_labels[development_indices]
            ap = float(average_precision_score(labels, adapted))
            recall = _fixed_budget_recall(labels, adapted, budgets)
            observations = _gate_observations(
                solved, validation_score[development_indices], adapted, budgets
            )
            round_metrics.append(
                {
                    "round": round_index,
                    "converged": True,
                    "pr_auc": ap,
                    "budget_recall": recall,
                    "transport": _transport_receipt(solved),
                    "gate_observations": observations,
                    "support_radius": support_radius,
                }
            )
        valid = [item for item in round_metrics if item.get("converged")]
        candidates.append(
            {
                "parameter_index": parameter_index,
                "parameters": parameter,
                "rounds": round_metrics,
                "valid_round_count": len(valid),
                "median_pr_auc": (
                    float(np.median([item["pr_auc"] for item in valid])) if valid else -math.inf
                ),
                "worst_budget_recall": min(
                    (min(item["budget_recall"].values()) for item in valid), default=-math.inf
                ),
                "maximum_slack_ratio": max(
                    (item["transport"]["slack_ratio"] for item in valid), default=math.inf
                ),
            }
        )
    eligible = [
        item
        for item in candidates
        if item["valid_round_count"] == len(rounds)
        and item["maximum_slack_ratio"] <= float(transport["maximum_slack_ratio"])
    ]
    if not eligible:
        raise ProtectedPartialOTError("源域网格没有收敛且满足恶意质量松弛的配置")
    eligible.sort(
        key=lambda item: (
            -item["median_pr_auc"],
            -item["worst_budget_recall"],
            item["parameters"]["mass"],
            -item["parameters"]["epsilon"],
        )
    )
    selected = eligible[0]
    for round_index, (
        _,
        development_indices,
        target,
        support_radius,
        development_assignment,
    ) in enumerate(round_contexts):
        solved = solve_transport(
            source, target, config, selected["parameters"], protect_malicious=True
        )
        harmless_probability, _ = _apply_correction(
            source,
            target,
            solved,
            validation_leaf[development_indices],
            validation_score[development_indices],
            config,
            support_radius,
            development_assignment,
        )
        harmless_observations.append(
            _gate_observations(
                solved,
                validation_score[development_indices],
                harmless_probability,
                budgets,
            )
        )
        labels = validation_labels[development_indices]
        anchor_ap = float(average_precision_score(labels, validation_score[development_indices]))
        parameter = selected["parameters"]
        harmful_specs = (
            ("remove_floor", False, parameter, 1.0),
            (
                "swap_asymmetry",
                True,
                {**parameter, "tau_ratio": 1.0 / parameter["tau_ratio"]},
                1.0,
            ),
            ("full_mass", True, {**parameter, "mass": 1.0}, 1.0),
            ("double_correction", True, parameter, 2.0),
        )
        for name, protected, harmful_parameter, multiplier in harmful_specs:
            harmful = solve_transport(
                source,
                target,
                config,
                harmful_parameter,
                protect_malicious=protected,
            )
            if not harmful.converged:
                continue
            harmful_probability, _ = _apply_correction(
                source,
                target,
                harmful,
                validation_leaf[development_indices],
                validation_score[development_indices],
                config,
                support_radius,
                development_assignment,
            )
            if multiplier != 1.0:
                harmful_probability = expit(
                    _logit(validation_score[development_indices])
                    + multiplier
                    * (_logit(harmful_probability) - _logit(validation_score[development_indices]))
                )
            harmful_ap = float(average_precision_score(labels, harmful_probability))
            harmful_cases.append(
                {
                    "name": name,
                    "parameter_index": selected["parameter_index"],
                    "round": round_index,
                    "harmful": anchor_ap - harmful_ap
                    >= float(config["source_selection"]["harmful_ap_drop"]),
                    "anchor_pr_auc": anchor_ap,
                    "adapted_pr_auc": harmful_ap,
                    "observations": _gate_observations(
                        harmful,
                        validation_score[development_indices],
                        harmful_probability,
                        budgets,
                    ),
                }
            )
    selection = {
        "schema_version": "crossyear-protected-pot-source-selection-v1",
        "selected_parameters": selected["parameters"],
        "selected_parameter_index": selected["parameter_index"],
        "selection_order": "median_pr_auc,worst_budget_recall,smaller_mass,larger_entropy",
        "candidates": candidates,
        "source_roles": list(SOURCE_ROLES),
        "target_roles_read": [],
        "target_labels_used": False,
        "final_accessed": False,
    }
    source_root = output_root / "source-freeze"
    _write_json(source_root / "source-only-selection.json", selection)
    keys = sorted(harmless_observations[0])
    envelope = {
        key: {
            "lower": float(
                np.quantile(
                    [item[key] for item in harmless_observations],
                    float(config["source_selection"]["gate_quantile_lower"]),
                )
            ),
            "upper": float(
                np.quantile(
                    [item[key] for item in harmless_observations],
                    float(config["source_selection"]["gate_quantile_upper"]),
                )
            ),
        }
        for key in keys
    }
    decisions: list[dict[str, Any]] = []
    for case in harmful_cases:
        outside = [
            key
            for key, value in case["observations"].items()
            if value < envelope[key]["lower"] or value > envelope[key]["upper"]
        ]
        decisions.append({**case, "rollback": bool(outside), "triggered_observations": outside})
    harmful = [item for item in decisions if item["harmful"]]
    harmless = [item for item in decisions if not item["harmful"]]
    detection = sum(item["rollback"] for item in harmful) / max(len(harmful), 1)
    false_rollback = sum(item["rollback"] for item in harmless) / max(len(harmless), 1)
    never_rollback_regret = sum(
        max(float(item["anchor_pr_auc"]) - float(item["adapted_pr_auc"]), 0.0) for item in decisions
    )
    gated_regret = sum(
        (
            0.0
            if item["rollback"]
            else max(float(item["anchor_pr_auc"]) - float(item["adapted_pr_auc"]), 0.0)
        )
        for item in decisions
    )
    regret_reduction = 1.0 - gated_regret / max(never_rollback_regret, EPS)
    m2_source_gate_passed = (
        detection >= float(config["source_selection"]["harmful_detection_minimum"])
        and false_rollback <= float(config["source_selection"]["false_rollback_maximum"])
        and regret_reduction >= float(config["source_selection"]["regret_reduction_minimum"])
    )
    gate = {
        "schema_version": "crossyear-protected-pot-source-gate-v1",
        "envelope": envelope,
        "hard_limits": {
            "slack_ratio_maximum": float(transport["maximum_slack_ratio"]),
            "effective_malicious_prototypes_minimum": float(
                transport["minimum_effective_malicious_prototypes"]
            ),
        },
        "harmful_grid": decisions,
        "harmful_detection_rate": detection,
        "false_rollback_rate": false_rollback,
        "never_rollback_regret": never_rollback_regret,
        "gated_regret": gated_regret,
        "regret_reduction": regret_reduction,
        "m2_source_gate_passed": m2_source_gate_passed,
        "target_roles_read": [],
        "target_labels_used": False,
        "final_accessed": False,
    }
    _write_json(source_root / "source-only-gate.json", gate)
    prototype_path = source_root / "source-prototypes.npz"
    np.savez_compressed(
        prototype_path,
        embedding=source.embedding,
        leaf=source.leaf,
        score=source.score,
        weight=source.weight,
        label=source.label,
    )
    receipt = {
        "schema_version": "crossyear-protected-pot-source-freeze-receipt-v1",
        "state": "finished",
        "selection_sha256": _sha256(source_root / "source-only-selection.json"),
        "gate_sha256": _sha256(source_root / "source-only-gate.json"),
        "source_prototypes_sha256": _sha256(prototype_path),
        "source_prototype_count": int(len(source.weight)),
        "source_malicious_prototype_count": int(np.sum(source.label == 1)),
        "target_roles_read": [],
        "target_labels_used": False,
        "final_accessed": False,
    }
    _write_json(source_root / "receipt.json", receipt)
    return receipt


def _load_source_prototypes(output_root: Path) -> PrototypeSet:
    with np.load(
        output_root / "source-freeze" / "source-prototypes.npz", allow_pickle=False
    ) as data:
        return PrototypeSet(
            data["embedding"], data["leaf"], data["score"], data["weight"], data["label"]
        )


def _seal_probability(
    output_root: Path,
    variant: str,
    probability: np.ndarray,
    sample_ids: np.ndarray,
    diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    root = output_root / "predictions" / variant
    record = _save_array(
        root / "target-development-probability.npy", probability.astype(np.float32)
    )
    seal = {
        "schema_version": "crossyear-protected-pot-probability-seal-v1",
        "variant": variant,
        "probability": record,
        "sample_id_sha256": _array_sha256(sample_ids),
        "row_count": int(len(probability)),
        "diagnostics": dict(diagnostics),
        "target_development_labels_opened": False,
        "target_prefix_labels_used": False,
        "final_accessed": False,
    }
    _write_json(root / "seal.json", seal)
    return seal


def adapt_seal(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    cache = load_cache(Path(config["paths"]["cache_manifest"]))
    selection = _json(output_root / "source-freeze" / "source-only-selection.json")
    gate = _json(output_root / "source-freeze" / "source-only-gate.json")
    source = _load_source_prototypes(output_root)
    prefix_leaf, prefix_score = _load_representation(output_root, "target-prefix")
    development_leaf, development_score = _load_representation(output_root, "target-development")
    target = _prototype_set(
        prefix_leaf,
        prefix_score,
        None,
        int(config["prototypes"]["target_maximum"]),
        config,
        int(config["seed"]) + 2000,
    )
    prefix_assignment = _nearest_target_prototypes(prefix_leaf, target, config)
    nearest = np.square(prefix_assignment[1])
    support_radius = float(
        np.sqrt(np.quantile(nearest, float(config["transport"]["support_radius_quantile"])))
    )
    development_assignment = _nearest_target_prototypes(development_leaf, target, config)
    selected = dict(selection["selected_parameters"])
    full = {**selected, "mass": 1.0, "tau_ratio": 1.0, "rho_plus": 0.0}
    no_floor = {**selected, "rho_plus": 0.0}
    results = {
        "U1_FULL_OT": solve_transport(source, target, config, full, protect_malicious=False),
        "U2_ASYM_POT_NO_FLOOR": solve_transport(
            source, target, config, no_floor, protect_malicious=False
        ),
        "M1_PROTECTED_ASYM_POT": solve_transport(
            source, target, config, selected, protect_malicious=True
        ),
    }
    for key, result in results.items():
        if not result.converged:
            raise ProtectedPartialOTError(f"{key} 求解器不收敛，拒绝封存候选概率")
    adapted: dict[str, tuple[np.ndarray, dict[str, Any]]] = {}
    for key, result in results.items():
        probability, diagnostics = _apply_correction(
            source,
            target,
            result,
            development_leaf,
            development_score,
            config,
            support_radius,
            development_assignment,
        )
        adapted[key] = (
            probability,
            {**diagnostics, "transport": _transport_receipt(result)},
        )
    protected_prefix, _ = _apply_correction(
        source,
        target,
        results["M1_PROTECTED_ASYM_POT"],
        prefix_leaf,
        prefix_score,
        config,
        support_radius,
        prefix_assignment,
    )
    observations = _gate_observations(
        results["M1_PROTECTED_ASYM_POT"],
        prefix_score,
        protected_prefix,
        [int(value) for value in config["evaluation"]["alert_budgets_per_million"]],
    )
    triggered = [
        key
        for key, value in observations.items()
        if key in gate["envelope"]
        and (value < gate["envelope"][key]["lower"] or value > gate["envelope"][key]["upper"])
    ]
    hard = gate["hard_limits"]
    protected_result = results["M1_PROTECTED_ASYM_POT"]
    if protected_result.slack_ratio > float(hard["slack_ratio_maximum"]):
        triggered.append("hard_slack_ratio")
    if protected_result.effective_malicious_prototypes < float(
        hard["effective_malicious_prototypes_minimum"]
    ):
        triggered.append("hard_effective_malicious_prototypes")
    if gate.get("m2_source_gate_passed") is not True:
        triggered.append("source_harmful_grid_gate")
    rollback = bool(triggered)
    safe = development_score.astype(np.float32) if rollback else adapted["M1_PROTECTED_ASYM_POT"][0]
    sample_ids = _sample_ids(cache, "target-development")
    seals = {
        "B0_XGB_ANCHOR": _seal_probability(
            output_root, "B0_XGB_ANCHOR", development_score.astype(np.float32), sample_ids, {}
        ),
        "U1_FULL_OT": _seal_probability(
            output_root,
            "U1_FULL_OT",
            adapted["U1_FULL_OT"][0],
            sample_ids,
            adapted["U1_FULL_OT"][1],
        ),
        "U2_ASYM_POT_NO_FLOOR": _seal_probability(
            output_root,
            "U2_ASYM_POT_NO_FLOOR",
            adapted["U2_ASYM_POT_NO_FLOOR"][0],
            sample_ids,
            adapted["U2_ASYM_POT_NO_FLOOR"][1],
        ),
        "M1_PROTECTED_ASYM_POT": _seal_probability(
            output_root,
            "M1_PROTECTED_ASYM_POT",
            adapted["M1_PROTECTED_ASYM_POT"][0],
            sample_ids,
            adapted["M1_PROTECTED_ASYM_POT"][1],
        ),
        "M1_M2_SAFE_ROLLBACK": _seal_probability(
            output_root,
            "M1_M2_SAFE_ROLLBACK",
            safe,
            sample_ids,
            {
                "rollback": rollback,
                "triggered_reasons": sorted(set(triggered)),
                "gate_observations": observations,
            },
        ),
    }
    decision = {
        "schema_version": "crossyear-protected-pot-target-prefix-decision-v1",
        "rollback": rollback,
        "triggered_reasons": sorted(set(triggered)),
        "gate_observations": observations,
        "support_radius": support_radius,
        "target_prefix_labels_used": False,
        "target_development_labels_opened": False,
        "final_accessed": False,
    }
    _write_json(output_root / "transport" / "target-prefix-decision.json", decision)
    receipt = {
        "schema_version": "crossyear-protected-pot-adaptation-receipt-v1",
        "state": "predictions_sealed_evaluation_pending",
        "variant_seals": {
            key: _sha256(output_root / "predictions" / key / "seal.json") for key in seals
        },
        "all_probability_seals_written": set(seals) == set(VARIANTS),
        "target_prefix_labels_used": False,
        "target_development_labels_opened": False,
        "final_accessed": False,
    }
    _write_json(output_root / "adaptation-receipt.json", receipt)
    return receipt


def _open_target_labels(cache: CacheView) -> np.ndarray:
    record = cache.target_label_record
    path = _manifest_array(record, cache.root, "target-development.labels", verify_hash=True)
    labels = np.asarray(np.load(path, mmap_mode="r", allow_pickle=False), dtype=np.uint8)
    if not np.isin(labels, (0, 1)).all():
        raise ProtectedPartialOTError("目标开发标签不是二元 0/1")
    return labels


def _threshold(labels: np.ndarray, probability: np.ndarray) -> float:
    order = np.argsort(-probability, kind="stable")
    y = labels[order]
    score = probability[order]
    positive_total = int(y.sum())
    negative_total = len(y) - positive_total
    tp = fp = 0
    best_value = -1.0
    best_threshold = 0.5
    offset = 0
    while offset < len(score):
        end = offset + 1
        while end < len(score) and score[end] == score[offset]:
            end += 1
        group_positive = int(y[offset:end].sum())
        tp += group_positive
        fp += end - offset - group_positive
        fn = positive_total - tp
        tn = negative_total - fp
        positive_f1 = 2 * tp / max(2 * tp + fp + fn, 1)
        negative_f1 = 2 * tn / max(2 * tn + fp + fn, 1)
        value = (positive_f1 + negative_f1) / 2
        if value > best_value:
            best_value = value
            best_threshold = float(score[offset])
        offset = end
    return best_threshold


def _ece(labels: np.ndarray, probability: np.ndarray, bins: int) -> float:
    result = 0.0
    edges = np.linspace(0, 1, bins + 1)
    for index in range(bins):
        mask = (probability >= edges[index]) & (
            probability <= edges[index + 1] if index == bins - 1 else probability < edges[index + 1]
        )
        if mask.any():
            result += float(mask.mean()) * abs(
                float(probability[mask].mean()) - float(labels[mask].mean())
            )
    return result


def _metrics(
    labels: np.ndarray,
    probability: np.ndarray,
    threshold: float,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    predicted = (probability >= threshold).astype(np.uint8)
    return {
        "pr_auc": float(average_precision_score(labels, probability)),
        "threshold": threshold,
        "malicious_f1": float(f1_score(labels, predicted, pos_label=1, zero_division=0)),
        "malicious_precision": float(
            precision_score(labels, predicted, pos_label=1, zero_division=0)
        ),
        "malicious_recall": float(recall_score(labels, predicted, pos_label=1, zero_division=0)),
        "macro_f1": float(f1_score(labels, predicted, average="macro", zero_division=0)),
        "confusion_matrix": confusion_matrix(labels, predicted, labels=[0, 1]).tolist(),
        "brier": float(brier_score_loss(labels, probability)),
        "ece": _ece(labels, probability, int(config["evaluation"]["ece_bins"])),
        "fixed_alert_budget_recall_per_million": _fixed_budget_recall(
            labels,
            probability,
            [int(value) for value in config["evaluation"]["alert_budgets_per_million"]],
        ),
    }


def _ranking_diagnostics(
    anchor: np.ndarray, probability: np.ndarray, budgets: Sequence[int]
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "spearman": float(spearmanr(anchor, probability).statistic),
        "raised_count": int(np.sum(probability > anchor)),
        "lowered_count": int(np.sum(probability < anchor)),
        "identical_ranking": bool(np.array_equal(np.argsort(anchor), np.argsort(probability))),
    }
    for budget in budgets:
        count = max(1, int(math.floor(len(anchor) * int(budget) / 1_000_000)))
        a = set(np.argsort(-anchor, kind="stable")[:count].tolist())
        b = set(np.argsort(-probability, kind="stable")[:count].tolist())
        result[f"topk_jaccard_{budget}"] = len(a & b) / max(len(a | b), 1)
    return result


def evaluate(config_path: Path, output_root: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    cache = load_cache(Path(config["paths"]["cache_manifest"]))
    adaptation = _json(output_root / "adaptation-receipt.json")
    if adaptation.get("all_probability_seals_written") is not True:
        raise ProtectedPartialOTError("五格概率尚未全部封存，拒绝打开目标标签")
    probabilities: dict[str, np.ndarray] = {}
    expected_sample_hash = _array_sha256(_sample_ids(cache, "target-development"))
    for variant in VARIANTS:
        seal_path = output_root / "predictions" / variant / "seal.json"
        seal = _json(seal_path)
        if seal.get("target_development_labels_opened") is not False:
            raise ProtectedPartialOTError(f"概率封存收据已提前打开标签：{variant}")
        if seal.get("sample_id_sha256") != expected_sample_hash:
            raise ProtectedPartialOTError(f"概率封存样本顺序漂移：{variant}")
        path = Path(seal["probability"]["path"])
        if _sha256(path) != seal["probability"]["sha256"]:
            raise ProtectedPartialOTError(f"概率封存 SHA-256 不匹配：{variant}")
        probability = np.asarray(np.load(path, allow_pickle=False), dtype=np.float64)
        if not np.isfinite(probability).all() or np.any((probability < 0) | (probability > 1)):
            raise ProtectedPartialOTError(f"概率封存值无效：{variant}")
        probabilities[variant] = probability
    labels = _open_target_labels(cache)
    if any(len(value) != len(labels) for value in probabilities.values()):
        raise ProtectedPartialOTError("目标标签与五格概率行数不一致")
    source_labels = _labels(cache, "source-validation")
    source_probability = np.load(
        output_root / "representations" / "source-validation" / "score.npy", allow_pickle=False
    )
    threshold = _threshold(source_labels, np.asarray(source_probability, dtype=np.float64))
    budgets = [int(value) for value in config["evaluation"]["alert_budgets_per_million"]]
    metrics = {
        variant: {
            **_metrics(labels, probability, threshold, config),
            "ranking_vs_gpu_anchor": _ranking_diagnostics(
                probabilities["B0_XGB_ANCHOR"], probability, budgets
            ),
        }
        for variant, probability in probabilities.items()
    }
    metrics_root = output_root / "metrics"
    for variant, values in metrics.items():
        _write_json(metrics_root / f"{variant}.json", values)
    anchor = metrics["B0_XGB_ANCHOR"]
    protected = metrics["M1_PROTECTED_ASYM_POT"]
    safe = metrics["M1_M2_SAFE_ROLLBACK"]
    no_floor = metrics["U2_ASYM_POT_NO_FLOOR"]
    evaluation = config["evaluation"]
    safe_gain = safe["pr_auc"] - anchor["pr_auc"]
    floor_gain = protected["pr_auc"] - no_floor["pr_auc"]
    budget_differences = {
        key: safe["fixed_alert_budget_recall_per_million"][key]
        - anchor["fixed_alert_budget_recall_per_million"][key]
        for key in anchor["fixed_alert_budget_recall_per_million"]
    }
    budget_pass = (
        sum(value >= 0 for value in budget_differences.values()) >= 2
        and min(budget_differences.values()) >= -float(evaluation["maximum_budget_recall_drop"])
        and max(budget_differences.values()) >= float(evaluation["minimum_budget_recall_gain"])
    )
    non_monotonic = not safe["ranking_vs_gpu_anchor"]["identical_ranking"] and any(
        safe["ranking_vs_gpu_anchor"][f"topk_jaccard_{budget}"] < 1 for budget in budgets
    )
    promoted = (
        safe["pr_auc"] >= float(evaluation["promotion_absolute_pr_auc"])
        and safe_gain >= float(evaluation["promotion_relative_to_gpu_anchor"])
        and budget_pass
        and non_monotonic
    )
    if promoted:
        outcome = "申请多种子正式验证"
    elif safe_gain > 0:
        outcome = "弱正信号/不晋级"
    else:
        outcome = "不晋级"
    decision = {
        "schema_version": "crossyear-protected-pot-q0-decision-v1",
        "state": "finished",
        "outcome": outcome,
        "gpu_anchor_pr_auc": anchor["pr_auc"],
        "safe_pr_auc": safe["pr_auc"],
        "safe_pr_auc_gain": safe_gain,
        "quality_floor_pr_auc_gain": floor_gain,
        "quality_floor_independent_mechanism_passed": floor_gain
        >= float(evaluation["mechanism_minimum_pr_auc_gain"]),
        "budget_recall_differences": budget_differences,
        "budget_gate_passed": budget_pass,
        "non_monotonic_ranking_change": non_monotonic,
        "target_labels_used_for_tuning": False,
        "target_labels_opened_after_all_probability_seals": True,
        "target_prefix_labels_used": False,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    _write_json(output_root / "decision.json", decision)
    _write_json(
        output_root / "status.json",
        {
            "schema_version": "crossyear-protected-pot-status-v1",
            "state": "finished",
            "exit_code": 0,
            "decision": outcome,
            "target_labels_opened_after_all_probability_seals": True,
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        },
    )
    return decision


def swanlab_publish(config_path: Path, output_root: Path, variant: str) -> dict[str, Any]:
    """在独立进程中只上传单个变体的聚合指标与协议元数据。"""
    config = _load_config(config_path)
    if variant not in VARIANTS:
        raise ProtectedPartialOTError(f"未知 SwanLab 变体：{variant}")
    decision = _json(output_root / "decision.json")
    if (
        decision.get("target_labels_opened_after_all_probability_seals") is not True
        or decision.get("target_labels_used_for_tuning") is not False
        or decision.get("final_accessed") is not False
    ):
        raise ProtectedPartialOTError("SwanLab 上传前的评价隔离收据无效")
    metrics = _json(output_root / "metrics" / f"{variant}.json")
    variant_config = next(item for item in config["variants"] if item["key"] == variant)
    swanlab_config = config["swanlab"]
    if (
        swanlab_config.get("workspace") != "mortiswang"
        or swanlab_config.get("project") != "malicious-traffic-llm"
    ):
        raise ProtectedPartialOTError("SwanLab 授权目的地不匹配")
    try:
        import swanlab
    except ImportError as error:
        raise ProtectedPartialOTError("SwanLab 依赖不可导入") from error
    run = swanlab.init(
        workspace=swanlab_config["workspace"],
        project=swanlab_config["project"],
        name=variant_config["run_name"],
        mode=swanlab_config["mode"],
        config={
            "run_id": config["run_id"],
            "variant": variant,
            "display_name": variant_config["display_name"],
            "seed": config["seed"],
            "budget_tier": config["budget_tier"],
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        },
    )
    scalar_metrics: dict[str, float] = {}
    for key in (
        "pr_auc",
        "malicious_f1",
        "malicious_precision",
        "malicious_recall",
        "macro_f1",
        "brier",
        "ece",
    ):
        value = metrics.get(key)
        if isinstance(value, (int, float)):
            scalar_metrics[key] = float(value)
    for budget, value in metrics["fixed_alert_budget_recall_per_million"].items():
        scalar_metrics[f"recall_at_{budget}_alerts_per_million"] = float(value)
    swanlab.log(scalar_metrics)
    run.finish()
    receipt = {
        "schema_version": "crossyear-protected-pot-swanlab-receipt-v1",
        "workspace": swanlab_config["workspace"],
        "project": swanlab_config["project"],
        "run_name": variant_config["run_name"],
        "variant": variant,
        "uploaded_keys": sorted(scalar_metrics),
        "upload_policy": swanlab_config["upload_policy"],
        "final_accessed": False,
    }
    _write_json(output_root / "swanlab" / f"{variant}.json", receipt)
    return receipt


def _resource_usage(started: float) -> dict[str, Any]:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_mib = peak / 1024 if platform.system() != "Darwin" else peak / 1024**2
    gpu_peak = None
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_peak = int(pynvml.nvmlDeviceGetMemoryInfo(handle).used)
    except (ImportError, RuntimeError, OSError):
        gpu_peak = None
    return {
        "wall_clock_seconds": time.perf_counter() - started,
        "peak_rss_mib": peak_mib,
        "observed_gpu_memory_bytes_at_finish": gpu_peak,
        "platform": platform.platform(),
        "final_accessed": False,
    }


def run(config_path: Path) -> dict[str, Any]:
    config = _load_config(config_path)
    output_root = Path(config["paths"]["output_root"])
    if output_root.exists():
        status = output_root / "status.json"
        if status.is_file() and _json(status).get("state") == "finished":
            print(json.dumps(_json(status), ensure_ascii=False, sort_keys=True))
            return _json(status)
        raise ProtectedPartialOTError(f"运行根已存在且未合法完成，拒绝覆盖：{output_root}")
    output_root.mkdir(parents=True)
    started = time.perf_counter()
    _write_json(
        output_root / "status.json",
        {
            "schema_version": "crossyear-protected-pot-status-v1",
            "state": "running",
            "stage": "audit",
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
        },
    )
    _write_json(output_root / "config.json", config)
    audit_result = audit(config_path, None)
    _write_json(output_root / "dataset-receipt.json", audit_result)
    fit_anchor(config_path, output_root, None)
    source_freeze(config_path, output_root)
    adapt_seal(config_path, output_root)
    decision = evaluate(config_path, output_root)
    _write_json(output_root / "resource-usage.json", _resource_usage(started))
    return decision


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="运行 LSPR23 到 LSPR24 稀有恶意质量保护非对称部分传输 Q0"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit", help="只读核验缓存，不打开目标开发标签")
    audit_parser.add_argument("--config", type=Path, required=True)
    audit_parser.add_argument("--cache-root", type=Path)
    run_parser = subparsers.add_parser("run", help="执行 Q0-A 到 Q0-D 完整流水线")
    run_parser.add_argument("--config", type=Path, required=True)
    swanlab_parser = subparsers.add_parser("swanlab-publish", help="独立进程上传单个变体的聚合指标")
    swanlab_parser.add_argument("--config", type=Path, required=True)
    swanlab_parser.add_argument("--output-root", type=Path, required=True)
    swanlab_parser.add_argument("--variant", choices=VARIANTS, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.command == "audit":
            cache_manifest = None
            if args.cache_root is not None:
                cache_manifest = (
                    args.cache_root / "cache-manifest.json"
                    if args.cache_root.is_dir()
                    else args.cache_root
                )
            audit(args.config, cache_manifest)
        elif args.command == "run":
            print(json.dumps(run(args.config), ensure_ascii=False, sort_keys=True))
        elif args.command == "swanlab-publish":
            print(
                json.dumps(
                    swanlab_publish(args.config, args.output_root, args.variant),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        else:
            raise ProtectedPartialOTError(f"未知命令：{args.command}")
    except ProtectedPartialOTError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
