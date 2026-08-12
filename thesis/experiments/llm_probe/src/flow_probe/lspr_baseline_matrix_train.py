"""LSPR 完整基线双轨训练、概率封存与独立评价入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import resource
import sys
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np
import sklearn
import torch
from joblib import dump
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from torch import nn

from flow_probe.lspr_baseline_matrix_models import (
    NEURAL_MODELS,
    SequenceModelConfig,
    build_neural_model,
    trainable_parameter_count,
)

SCHEMA: Final = "lspr-baseline-matrix-v1"
CACHE_SCHEMA: Final = "lspr-crossyear-python-cache-v1"
ROLES: Final = (
    "source-train",
    "source-validation",
    "target-prefix",
    "target-development",
)
TABULAR_MODELS: Final = (
    "dijk2024_rf_visible_full_extension",
    "leoste2025_rf_with_iat",
    "leoste2025_rf_without_iat",
    "dijk2026_xgboost",
)
MODELS: Final = TABULAR_MODELS + NEURAL_MODELS
REQUIRED_WORKSPACE: Final = "mortiswang"
REQUIRED_PROJECT: Final = "malicious-traffic-llm"


class BaselineMatrixError(ValueError):
    """双轨配置、缓存或运行违反冻结合同。"""


@dataclass(frozen=True)
class Role:
    name: str
    root: Path
    x_value: np.ndarray
    x_missing: np.ndarray
    delta_t_us: np.ndarray
    sample_id: np.ndarray
    sequence_id: np.ndarray
    position: np.ndarray
    valid_length: np.ndarray
    starts: np.ndarray
    lengths: np.ndarray
    labels_path: Path | None

    @property
    def row_count(self) -> int:
        return int(len(self.x_value))

    @property
    def sequence_count(self) -> int:
        return int(len(self.starts))

    def open_labels(self) -> np.ndarray:
        if self.labels_path is None:
            raise BaselineMatrixError(f"{self.name} 没有标签权限")
        labels = np.load(self.labels_path, mmap_mode="r")
        if labels.shape != (self.row_count,) or not np.isin(labels, (0, 1)).all():
            raise BaselineMatrixError(f"{self.name} 标签数组不合法")
        return labels


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BaselineMatrixError(f"JSON 顶层必须是对象：{path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _assert_tracking_destination(config: Mapping[str, Any]) -> None:
    tracking = config.get("swanlab")
    if not isinstance(tracking, Mapping):
        raise BaselineMatrixError("配置缺少 SwanLab 目的地")
    if tracking.get("workspace") != REQUIRED_WORKSPACE:
        raise BaselineMatrixError("SwanLab workspace 与本轮授权不一致")
    if tracking.get("project") != REQUIRED_PROJECT:
        raise BaselineMatrixError("SwanLab project 与本轮授权不一致")
    if tracking.get("mode") != "online":
        raise BaselineMatrixError("正式矩阵要求 SwanLab online 模式")


def _array_path(cache_root: Path, role: str, name: str) -> Path:
    path = cache_root / f"role={role}" / f"{name}.npy"
    if not path.is_file():
        raise BaselineMatrixError(f"缓存数组不存在：{path}")
    return path


def _sequence_index(
    role: str, sequence_id: np.ndarray, position: np.ndarray, valid_length: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    starts_mask = np.ones(len(position), dtype=bool)
    starts_mask[1:] = np.any(sequence_id[1:] != sequence_id[:-1], axis=1)
    starts = np.flatnonzero(starts_mask).astype(np.int64, copy=False)
    lengths = valid_length[starts].astype(np.int64, copy=False)
    if (
        not len(starts)
        or np.any(position[starts] != 0)
        or np.any(lengths < 1)
        or np.any(lengths > 128)
    ):
        raise BaselineMatrixError(f"{role} 序列起点或长度不合法")
    if not np.array_equal(starts + lengths, np.r_[starts[1:], len(position)]):
        raise BaselineMatrixError(f"{role} 序列块与 valid_length 不一致")
    return starts, lengths


def load_cache(cache_root: Path) -> tuple[dict[str, Any], dict[str, Role]]:
    cache_root = cache_root.resolve()
    manifest_path = cache_root / "cache-manifest.json"
    manifest = _load_json(manifest_path)
    if manifest.get("schema_version") != CACHE_SCHEMA:
        raise BaselineMatrixError("缓存模式版本不匹配")
    if manifest.get("final_accessed") is not False:
        raise BaselineMatrixError("基线矩阵拒绝 final_accessed 非 false 的缓存")
    fields = manifest.get("model_fields")
    if not isinstance(fields, list) or len(fields) != 77:
        raise BaselineMatrixError("缓存必须恰有 77 个有序合法字段")
    blocks = manifest.get("roles")
    if not isinstance(blocks, Mapping) or set(blocks) != set(ROLES):
        raise BaselineMatrixError("缓存必须恰有四个冻结角色")
    roles: dict[str, Role] = {}
    for role in ROLES:
        block = blocks[role]
        if not isinstance(block, Mapping):
            raise BaselineMatrixError(f"{role} 清单块不合法")
        arrays = {
            name: np.load(_array_path(cache_root, role, name), mmap_mode="r")
            for name in (
                "x_value",
                "x_missing",
                "delta_t_us",
                "sample_id",
                "sequence_id",
                "position",
                "valid_length",
                "padding_mask",
            )
        }
        rows = int(block.get("row_count", -1))
        if any(len(array) != rows for array in arrays.values()):
            raise BaselineMatrixError(f"{role} 数组行数与清单不一致")
        if arrays["x_value"].shape != (rows, 77) or arrays["x_missing"].shape != (rows, 77):
            raise BaselineMatrixError(f"{role} 字段形状不合法")
        if not np.all(arrays["padding_mask"] == 1):
            raise BaselineMatrixError(f"{role} padding_mask 必须全为 1")
        starts, lengths = _sequence_index(
            role, arrays["sequence_id"], arrays["position"], arrays["valid_length"]
        )
        if len(starts) != int(block.get("sequence_count", -1)):
            raise BaselineMatrixError(f"{role} 序列数与清单不一致")
        labels_path = None
        if role in ("source-train", "source-validation", "target-development"):
            labels_path = _array_path(cache_root, role, "labels")
        roles[role] = Role(
            name=role,
            root=cache_root / f"role={role}",
            x_value=arrays["x_value"],
            x_missing=arrays["x_missing"],
            delta_t_us=arrays["delta_t_us"],
            sample_id=arrays["sample_id"],
            sequence_id=arrays["sequence_id"],
            position=arrays["position"],
            valid_length=arrays["valid_length"],
            starts=starts,
            lengths=lengths,
            labels_path=labels_path,
        )
    if (cache_root / "role=target-prefix" / "labels.npy").exists():
        raise BaselineMatrixError("target-prefix 不得发布标签")
    return manifest, roles


def _tabular_features(role: Role, selected_fields: np.ndarray | None = None) -> np.ndarray:
    values = np.asarray(role.x_value, dtype=np.float32)
    missing = np.asarray(role.x_missing, dtype=np.float32)
    if selected_fields is not None:
        values = values[:, selected_fields]
        missing = missing[:, selected_fields]
    seconds = np.maximum(np.asarray(role.delta_t_us), 0).astype(np.float64) / 1_000_000.0
    return np.concatenate((values, missing, np.log1p(seconds).astype(np.float32)[:, None]), axis=1)


def _without_iat_indices(fields: list[str], iat_fields: list[str]) -> np.ndarray:
    missing = sorted(set(iat_fields) - set(fields))
    if missing:
        raise BaselineMatrixError(f"IAT 字段不在 77 字段清单：{', '.join(missing)}")
    indices = np.asarray(
        [index for index, field in enumerate(fields) if field not in set(iat_fields)]
    )
    if len(indices) != 63:
        raise BaselineMatrixError("无 IAT 视图必须从 77 字段精确移除 14 项")
    return indices


def _fit_tabular_model(model_name: str, config: Mapping[str, Any], seed: int) -> object:
    params = config["models"][model_name]["parameters"]
    if model_name == "dijk2026_xgboost":
        try:
            from xgboost import XGBClassifier
        except ImportError as error:
            raise BaselineMatrixError("Dijk 2026 XGBoost 需要正式环境中的 xgboost") from error
        return XGBClassifier(
            objective="binary:logistic",
            eval_metric="aucpr",
            tree_method="hist",
            random_state=seed,
            n_jobs=int(params["n_jobs"]),
            n_estimators=int(params["n_estimators"]),
            learning_rate=float(params["learning_rate"]),
            max_depth=int(params["max_depth"]),
            subsample=float(params["subsample"]),
            colsample_bytree=float(params["colsample_bytree"]),
            reg_lambda=float(params["reg_lambda"]),
            min_child_weight=float(params["min_child_weight"]),
            max_bin=int(params["max_bin"]),
        )
    return RandomForestClassifier(
        n_estimators=int(params["n_estimators"]),
        max_depth=params.get("max_depth"),
        bootstrap=bool(params["bootstrap"]),
        class_weight=params.get("class_weight"),
        n_jobs=int(params["n_jobs"]),
        random_state=seed,
    )


def _predict_probability(model: object, features: np.ndarray) -> np.ndarray:
    probabilities = np.asarray(model.predict_proba(features))[:, 1].astype(np.float32)
    if probabilities.shape != (len(features),) or not np.isfinite(probabilities).all():
        raise BaselineMatrixError("表格模型概率形状不合法或含非有限值")
    return probabilities


def _ece(labels: np.ndarray, probabilities: np.ndarray, bins: int = 15) -> float:
    order = np.argsort(probabilities, kind="stable")
    total = len(order)
    return float(
        sum(
            len(indices)
            / total
            * abs(float(labels[indices].mean()) - float(probabilities[indices].mean()))
            for indices in np.array_split(order, bins)
            if len(indices)
        )
    )


def _fixed_alert_recall(labels: np.ndarray, probabilities: np.ndarray, budget: int) -> float:
    count = min(int(budget), len(labels))
    selected = np.argpartition(probabilities, -count)[-count:]
    positives = int(np.sum(labels == 1))
    return float(np.sum(labels[selected] == 1) / max(positives, 1))


def _metrics(
    labels: np.ndarray, probabilities: np.ndarray, threshold: float, budgets: list[int]
) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(np.uint8)
    return {
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "malicious_f1": float(f1_score(labels, predictions, pos_label=1, zero_division=0)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "brier": float(brier_score_loss(labels, probabilities)),
        "ece_15_equal_frequency": _ece(labels, probabilities),
        "fixed_alert_budget_recall": {
            str(budget): _fixed_alert_recall(labels, probabilities, budget) for budget in budgets
        },
        "confusion_matrix": confusion_matrix(labels, predictions, labels=[0, 1]).tolist(),
        "threshold": float(threshold),
        "prevalence": float(labels.mean()),
    }


def _freeze_threshold(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, Any]:
    benign = labels == 0
    malicious = labels == 1
    allowed = int(np.floor(int(benign.sum()) * 100 / 1_000_000))
    values, inverse = np.unique(probabilities, return_inverse=True)
    benign_counts = np.bincount(inverse, weights=benign.astype(np.int64), minlength=len(values))[
        ::-1
    ]
    malicious_counts = np.bincount(
        inverse, weights=malicious.astype(np.int64), minlength=len(values)
    )[::-1]
    false_positives = np.cumsum(benign_counts)
    true_positives = np.cumsum(malicious_counts)
    permitted = false_positives <= allowed
    if np.any(permitted):
        best_true = true_positives[permitted].max()
        index = int(np.flatnonzero(permitted & (true_positives == best_true))[0])
        threshold = float(values[::-1][index])
    else:
        threshold = float(np.nextafter(probabilities.max(), np.inf))
    return {
        "schema_version": "lspr-baseline-source-threshold-v1",
        "selection_role": "source-validation",
        "criterion": "每百万良性流误报不超过100时召回最高，同分取更高阈值",
        "threshold": threshold,
        "target_label_used": False,
        "final_accessed": False,
    }


def _save_probability_seal(output_dir: Path, role: Role, probabilities: np.ndarray) -> Path:
    predictions = output_dir / "predictions"
    predictions.mkdir(parents=True, exist_ok=True)
    probability_path = predictions / "target-development-probability.npy"
    with probability_path.open("wb") as handle:
        np.save(handle, probabilities.astype(np.float32, copy=False), allow_pickle=False)
    sample_hash = hashlib.sha256(np.asarray(role.sample_id).tobytes()).hexdigest()
    seal = predictions / "target-development-probability-seal.json"
    _write_json(
        seal,
        {
            "schema_version": "lspr-baseline-probability-seal-v1",
            "row_count": role.row_count,
            "sample_id_sha256": sample_hash,
            "probability_sha256": _sha256(probability_path),
            "labels_opened": False,
            "final_accessed": False,
        },
    )
    return seal


def _iter_batches(
    role: Role,
    order: np.ndarray,
    batch_size: int,
    *,
    include_labels: bool,
) -> Iterator[tuple[torch.Tensor, torch.Tensor, torch.Tensor | None]]:
    labels_array = role.open_labels() if include_labels else None
    for offset in range(0, len(order), batch_size):
        indices = order[offset : offset + batch_size]
        lengths = role.lengths[indices]
        maximum = int(lengths.max())
        values = np.zeros((len(indices), maximum, 155), dtype=np.float32)
        valid = np.zeros((len(indices), maximum), dtype=bool)
        labels = (
            np.zeros((len(indices), maximum), dtype=np.float32)
            if labels_array is not None
            else None
        )
        for batch_index, sequence_index in enumerate(indices):
            start = int(role.starts[sequence_index])
            length = int(role.lengths[sequence_index])
            row_slice = slice(start, start + length)
            values[batch_index, :length, :77] = role.x_value[row_slice]
            values[batch_index, :length, 77:154] = role.x_missing[row_slice]
            seconds = np.maximum(role.delta_t_us[row_slice], 0).astype(np.float64) / 1_000_000.0
            values[batch_index, :length, 154] = np.log1p(seconds).astype(np.float32)
            valid[batch_index, :length] = True
            if labels is not None and labels_array is not None:
                labels[batch_index, :length] = labels_array[row_slice]
        yield torch.from_numpy(values), torch.from_numpy(valid), (
            torch.from_numpy(labels) if labels is not None else None
        )


def _evaluate_neural(
    model: nn.Module, role: Role, batch_size: int, device: torch.device
) -> np.ndarray:
    model.eval()
    results: list[np.ndarray] = []
    order = np.arange(role.sequence_count, dtype=np.int64)
    with torch.no_grad():
        for values, valid, _ in _iter_batches(role, order, batch_size, include_labels=False):
            values = values.to(device, non_blocking=True)
            valid_device = valid.to(device, non_blocking=True)
            with torch.autocast(
                device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"
            ):
                logits = model(values, valid_device)
            results.append(torch.sigmoid(logits).float().cpu().numpy()[valid.numpy()])
    return np.concatenate(results).astype(np.float32, copy=False)


def _train_neural(
    model_name: str,
    config: Mapping[str, Any],
    roles: Mapping[str, Role],
    output_dir: Path,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    block = config["models"][model_name]
    common = config["neural_budget"]
    model_config = SequenceModelConfig(**config["sequence_model"])
    model = build_neural_model(model_name, model_config).to(device)
    learning_rate = float(block.get("learning_rate", common["learning_rate"]))
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=float(common["weight_decay"])
    )
    epochs = int(common["epochs"])
    steps_per_epoch = int(common["steps_per_epoch"])
    batch_size = int(common["batch_size_sequences"])
    source = roles["source-train"]
    source_labels = source.open_labels()
    positive = max(int(np.sum(source_labels == 1)), 1)
    negative = max(int(np.sum(source_labels == 0)), 1)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(negative / positive, device=device))
    started = time.perf_counter()
    global_step = 0
    for epoch in range(epochs):
        model.train()
        order = np.random.default_rng(int(config["seed"]) + epoch).permutation(
            source.sequence_count
        )
        for values, valid, labels in _iter_batches(source, order, batch_size, include_labels=True):
            if labels is None:
                raise BaselineMatrixError("源训练缺少标签")
            values = values.to(device, non_blocking=True)
            valid_device = valid.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(
                device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"
            ):
                logits = model(values, valid_device)
                loss = criterion(logits[valid_device], labels[valid_device])
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), float(common["gradient_clip_norm"]))
            optimizer.step()
            global_step += 1
            if global_step % int(common["checkpoint_interval_steps"]) == 0:
                checkpoint = output_dir / "checkpoints" / f"step-{global_step}.pt"
                checkpoint.parent.mkdir(parents=True, exist_ok=True)
                torch.save(
                    {
                        "model": model.state_dict(),
                        "optimizer": optimizer.state_dict(),
                        "step": global_step,
                    },
                    checkpoint,
                )
            if global_step % int(common["heartbeat_steps"]) == 0:
                print(
                    f"{model_name} 训练：epoch={epoch + 1}/{epochs}，"
                    f"step={global_step}，loss={float(loss):.6f}",
                    flush=True,
                )
            if global_step >= (epoch + 1) * steps_per_epoch:
                break
    training_seconds = time.perf_counter() - started
    validation_probability = _evaluate_neural(model, roles["source-validation"], batch_size, device)
    target_probability = _evaluate_neural(model, roles["target-development"], batch_size, device)
    checkpoint = output_dir / "checkpoints" / "final.pt"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model": model.state_dict(), "step": global_step, "model_config": model_config.to_dict()},
        checkpoint,
    )
    return (
        validation_probability,
        target_probability,
        {
            "training_seconds": training_seconds,
            "global_steps": global_step,
            "trainable_parameters": trainable_parameter_count(model),
            "checkpoint_sha256": _sha256(checkpoint),
        },
    )


def _run_tabular(
    model_name: str,
    config: Mapping[str, Any],
    manifest: Mapping[str, Any],
    roles: Mapping[str, Role],
    output_dir: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    fields = list(manifest["model_fields"])
    selected = None
    if model_name == "leoste2025_rf_without_iat":
        selected = _without_iat_indices(fields, list(config["packet_interarrival_fields"]))
    model = _fit_tabular_model(model_name, config, int(config["seed"]))
    started = time.perf_counter()
    same_year: dict[str, Any] = {}
    if model_name == "dijk2024_rf_visible_full_extension":
        full_x = np.concatenate(
            (
                _tabular_features(roles["source-train"]),
                _tabular_features(roles["source-validation"]),
            ),
            axis=0,
        )
        full_y = np.concatenate(
            (roles["source-train"].open_labels(), roles["source-validation"].open_labels())
        )
        train_x, validation_x, train_y, validation_y = train_test_split(
            full_x, full_y, test_size=0.2, random_state=int(config["seed"]), stratify=None
        )
        model.fit(train_x, train_y)
        validation_probability = _predict_probability(model, validation_x)
        same_year = {
            "labels": validation_y,
            "probabilities": validation_probability,
            "member_count": len(full_y),
            "split": "random 4:1, random_state=42, no stratification/group/time isolation",
        }
        threshold_labels = validation_y
    else:
        train_x = _tabular_features(roles["source-train"], selected)
        train_y = roles["source-train"].open_labels()
        model.fit(train_x, train_y)
        validation_x = _tabular_features(roles["source-validation"], selected)
        threshold_labels = roles["source-validation"].open_labels()
        validation_probability = _predict_probability(model, validation_x)
    training_seconds = time.perf_counter() - started
    inference_started = time.perf_counter()
    target_probability = _predict_probability(
        model, _tabular_features(roles["target-development"], selected)
    )
    model_path = output_dir / "model.joblib"
    dump(model, model_path)
    return (
        threshold_labels,
        validation_probability,
        target_probability,
        {
            "training_seconds": training_seconds,
            "target_inference_seconds": time.perf_counter() - inference_started,
            "input_dimension": int(train_x.shape[1]),
            "model_sha256": _sha256(model_path),
            "same_year": same_year,
        },
    )


def _tracking(
    model_name: str, config: Mapping[str, Any], metrics: Mapping[str, Any], output_dir: Path
) -> dict[str, Any]:
    try:
        import swanlab

        run = swanlab.init(
            workspace=REQUIRED_WORKSPACE,
            project=REQUIRED_PROJECT,
            experiment_name=f"lspr-baseline-{config['track'].lower()}-{model_name}-seed{config['seed']}",
            mode="online",
            config={"track": config["track"], "model": model_name, "seed": config["seed"]},
        )
        swanlab.log(
            {
                "target/pr_auc": metrics["pr_auc"],
                "target/malicious_f1": metrics["malicious_f1"],
                "target/brier": metrics["brier"],
            }
        )
        swanlab.finish()
        return {"status": "finished", "run_id": getattr(run, "id", None)}
    except Exception as error:  # SwanLab 不得破坏本地证据。
        status = {"status": "failed-local-evidence-preserved", "error_type": type(error).__name__}
        _write_json(output_dir / "swanlab-status.json", status)
        return status


def audit(config_path: Path) -> dict[str, Any]:
    config = _load_json(config_path)
    if config.get("schema_version") != SCHEMA or config.get("track") not in ("A", "B"):
        raise BaselineMatrixError("双轨配置模式或轨道不合法")
    _assert_tracking_destination(config)
    configured = tuple(config.get("model_order", []))
    if not configured or any(model not in MODELS for model in configured):
        raise BaselineMatrixError("model_order 含未知模型或为空")
    if set(configured) != set(config.get("models", {})):
        raise BaselineMatrixError("model_order 与 models 必须一一对应")
    model_config = SequenceModelConfig(**config["sequence_model"])
    model_receipts = {}
    for model_name in configured:
        if model_name in NEURAL_MODELS:
            model = build_neural_model(model_name, model_config)
            model_receipts[model_name] = {"trainable_parameters": trainable_parameter_count(model)}
        else:
            model_receipts[model_name] = {
                "constructor": type(
                    _fit_tabular_model(model_name, config, int(config["seed"]))
                ).__name__
            }
    return {
        "schema_version": "lspr-baseline-matrix-audit-v1",
        "track": config["track"],
        "models": model_receipts,
        "probability_before_target_labels": True,
        "target_labels_for_tuning": False,
        "final_accessed": False,
    }


def run(config_path: Path, cache_root: Path, output_dir: Path, model_name: str) -> dict[str, Any]:
    config = _load_json(config_path)
    _assert_tracking_destination(config)
    if model_name not in config.get("model_order", []):
        raise BaselineMatrixError(f"模型不在当前轨道配置中：{model_name}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise BaselineMatrixError(f"输出目录非空，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    _seed_everything(int(config["seed"]))
    manifest, roles = load_cache(cache_root)
    _write_json(
        output_dir / "run-config.json",
        {
            "config": config,
            "config_sha256": _sha256(config_path),
            "cache_manifest_sha256": _sha256(cache_root / "cache-manifest.json"),
            "model": model_name,
            "final_accessed": False,
        },
    )
    started = time.perf_counter()
    if model_name in TABULAR_MODELS:
        validation_labels, validation_probability, target_probability, resources = _run_tabular(
            model_name, config, manifest, roles, output_dir
        )
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        validation_probability, target_probability, resources = _train_neural(
            model_name, config, roles, output_dir, device
        )
        validation_labels = roles["source-validation"].open_labels()
    threshold = _freeze_threshold(validation_labels, validation_probability)
    _write_json(output_dir / "source-validation-threshold.json", threshold)
    seal_path = _save_probability_seal(output_dir, roles["target-development"], target_probability)
    target_labels = roles["target-development"].open_labels()
    metrics = _metrics(
        target_labels,
        target_probability,
        float(threshold["threshold"]),
        list(config["fixed_alert_budgets"]),
    )
    same_year = resources.pop("same_year", {})
    if same_year:
        metrics["source_same_year_random_4_to_1"] = _metrics(
            same_year.pop("labels"),
            same_year.pop("probabilities"),
            0.5,
            list(config["fixed_alert_budgets"]),
        )
        metrics["source_same_year_random_4_to_1"].update(same_year)
    receipt = {
        "schema_version": "lspr-baseline-matrix-result-v1",
        "track": config["track"],
        "model": model_name,
        "display_name": config["models"][model_name]["display_name"],
        "replication_class": config["models"][model_name]["replication_class"],
        "implementation_differences": config["models"][model_name]["implementation_differences"],
        "paper_reported_experiment_reproduced": False,
        "screening_only": bool(config["evidence_identity"]["screening_only"]),
        "formal_paper_evidence": False,
        "probability_seal_sha256": _sha256(seal_path),
        "target_labels_opened_after_probability_seal": True,
        "target_labels_used_for_tuning": False,
        "target_prefix_labels_available": False,
        "final_accessed": False,
        "target_development": metrics,
        "resource": {
            **resources,
            "total_seconds": time.perf_counter() - started,
            "peak_rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
        },
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
        },
    }
    receipt["swanlab"] = _tracking(model_name, config, metrics, output_dir)
    _write_json(output_dir / "metrics.json", receipt)
    _write_json(
        output_dir / "run-state.json",
        {"state": "finished", "model": model_name, "final_accessed": False},
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--config", type=Path, required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--cache-root", type=Path, required=True)
    run_parser.add_argument("--output-dir", type=Path, required=True)
    run_parser.add_argument("--model", choices=MODELS, required=True)
    args = parser.parse_args()
    if args.command == "audit":
        print(json.dumps(audit(args.config), ensure_ascii=False, indent=2))
    else:
        print(
            json.dumps(
                run(args.config, args.cache_root, args.output_dir, args.model),
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
