"""R2 物理旁路的 DistilBERT 结构适配开发集探针。"""

from __future__ import annotations

import argparse
import fcntl
import gc
import hashlib
import json
import math
import os
import random
import shutil
import time
import uuid
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

from flow_probe import shared_b0_distilbert_baseline as baseline
from flow_probe.r2_physics_sidecar_signal import (
    COMMON_FEATURE_FIELDS,
    SIDECAR_FIELDS,
    DevelopmentSplit,
    random_sidecar,
    shuffled_sidecar,
)
from flow_probe.shared_b0_view import COMMON_FIELDS, render_input_text
from flow_probe.tracking import TrackingSettings


CONFIG_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_probe_config_v2"
INPUT_BINDING_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_input_v1"
RUN_BINDING_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_run_binding_v2"
RUN_STATE_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_run_state_v1"
CHECKPOINT_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_checkpoint_v1"
SELECTION_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_selection_v1"
ARTIFACT_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_artifacts_v1"
FINALIZATION_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_finalization_v1"
BEST_MODEL_RECEIPT_SCHEMA_VERSION = "flow_probe_r2_distilbert_best_model_receipt_v1"
SUMMARY_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_seed_summary_v1"
STRUCTURE_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_structure_v1"
FUSION_SCHEMA_VERSION = "flow_probe_r2_distilbert_sidecar_fusion_v1"

TRAIN_SPLIT = "train-fit"
VALIDATION_SPLIT = "validation"
EXPECTED_DATASET_STATUS = "ns3_tqhc2_ready_quic_pending"
EXPECTED_VIEW_SCHEMA = "flow_probe_r2_physics_pilot_detection_view_v1"
EXPECTED_STAGE = "theory_selection"
EXPECTED_PROTOCOL_STATUS = "review_pending"
EXPECTED_SOURCE = "TQH-C2"
EXPECTED_SAMPLE_COUNTS = MappingProxyType({TRAIN_SPLIT: 2048, VALIDATION_SPLIT: 512})
ALLOWED_SEEDS = (42, 43, 44)
VARIANTS = ("T-A", "T-P", "T-S", "T-R")
VARIANT_SLUGS = MappingProxyType(
    {"T-A": "t-a", "T-P": "t-p", "T-S": "t-s", "T-R": "t-r"}
)
UNCERTAINTY_START = 9
UNCERTAINTY_STOP = 14
FIXED_TOTAL_OPTIMIZER_STEPS = 192
PROJECTION_OUTPUT_DIMENSION = 768
RUN_STATUSES = frozenset(
    {"prepared", "running", "interrupted", "failed", "finalizing", "finished"}
)
RESUMABLE_STATUSES = frozenset({"prepared", "running", "interrupted"})
EXPECTED_SEED_EXECUTION = "serial"
MINIMUM_FREE_BYTES = 5 * 1024**3
ARTIFACT_WRITE_RESERVE_BYTES = 2 * 1024**3
SEMANTIC_DEPENDENCY_FILES = (
    "r2_physics_sidecar_signal.py",
    "r2_protocol_contract.py",
    "shared_b0_view.py",
    "shared_b0_distilbert_baseline.py",
    "tracking.py",
)

DETECTION_VIEW_COLUMNS = (
    "schema_version",
    "sample_id",
    "source_dataset",
    "split_id",
    "binary_label",
    "profile",
    "transport_family",
    "shared_expert_mask",
    "tcp_expert_mask",
    "udp_expert_mask",
    "quic_expert_mask",
    "protocol_confidence",
    *COMMON_FEATURE_FIELDS,
)
SIDECAR_SOURCE_COLUMNS = (
    "sample_id",
    "split_id",
    "transport_family",
    *SIDECAR_FIELDS,
)
SIDECAR_PROJECTION_COLUMNS = ("sample_id", *SIDECAR_FIELDS)
FIXED_TRAINING_CONTRACT = MappingProxyType(
    {
        "per_device_train_batch_size": 16,
        "per_device_eval_batch_size": 64,
        "gradient_accumulation_steps": 2,
        "learning_rate": 0.00002,
        "weight_decay": 0.01,
        "num_train_epochs": 3,
        "warmup_ratio": 0.1,
        "max_grad_norm": 1.0,
        "save_steps": 20,
        "save_total_limit": 1,
        "num_workers": 2,
        "resume_from_checkpoint": "auto",
    }
)


class R2DistilBertSidecarProbeError(ValueError):
    """探针配置、输入、计算图或运行制品不符合冻结合同。"""


@dataclass(frozen=True)
class ArtifactSpec:
    path: Path
    sha256: str


@dataclass(frozen=True)
class ProbeDatasetSettings:
    input_summary: ArtifactSpec
    detection_view: ArtifactSpec
    sidecar: ArtifactSpec


@dataclass(frozen=True)
class ProbeStorageSettings:
    seed_execution: str
    minimum_free_bytes: int
    artifact_write_reserve_bytes: int


@dataclass(frozen=True)
class ProbeConfig:
    dataset: ProbeDatasetSettings
    model: baseline.ModelSettings
    training: baseline.TrainingSettings
    evaluation: baseline.EvaluationSettings
    run: baseline.RunSettings
    storage: ProbeStorageSettings
    tracking: TrackingSettings
    config_path: Path
    project_root: Path


@dataclass(frozen=True)
class ProbeSplit:
    name: str
    sample_ids: tuple[str, ...]
    stable_orders: tuple[int, ...]
    texts: tuple[str, ...]
    labels: tuple[int, ...]
    source_datasets: tuple[str, ...]
    transport_families: tuple[str, ...]
    sidecar_features: np.ndarray
    sidecar_masks: np.ndarray

    def __len__(self) -> int:
        return len(self.sample_ids)


@dataclass(frozen=True)
class VariantInputs:
    variant: str
    train: ProbeSplit
    validation: ProbeSplit
    binding: Mapping[str, object]


@dataclass(frozen=True)
class PreparedProbeInputs:
    variants: Mapping[str, VariantInputs]
    binding: Mapping[str, object]
    binding_sha256: str


@dataclass(frozen=True)
class PreparedVariantRun:
    config: ProbeConfig
    inputs: VariantInputs
    model_binding: Mapping[str, object]
    run_binding: Mapping[str, object]
    binding_sha256: str
    output_dir: Path
    state_path: Path
    resume_checkpoint: Path | None
    resume_finalization: bool


@dataclass(frozen=True)
class ProbeModelOutput:
    logits: Any
    loss: Any | None


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise R2DistilBertSidecarProbeError(f"{description}必须是对象")
    return value


def _exact_keys(
    value: Mapping[str, object], required: set[str], description: str
) -> None:
    missing = sorted(required.difference(value))
    unexpected = sorted(set(value).difference(required))
    if missing or unexpected:
        raise R2DistilBertSidecarProbeError(
            f"{description}字段不符合合同：缺少={missing}，额外={unexpected}"
        )


def _nonempty_string(value: object, description: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise R2DistilBertSidecarProbeError(
            f"{description}必须是无首尾空白的非空字符串"
        )
    return value


def _integer(value: object, description: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise R2DistilBertSidecarProbeError(
            f"{description}必须是不小于 {minimum} 的整数"
        )
    return value


def _number(value: object, description: str, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R2DistilBertSidecarProbeError(f"{description}必须是有限数")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise R2DistilBertSidecarProbeError(
            f"{description}必须是不小于 {minimum} 的有限数"
        )
    return result


def _expected_sha256(value: object, description: str) -> str:
    digest = _nonempty_string(value, description)
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise R2DistilBertSidecarProbeError(f"{description}必须是小写 SHA-256")
    return digest


def _resolve_path(value: object, project_root: Path, description: str) -> Path:
    raw = _nonempty_string(value, description)
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else project_root / path).resolve()


def _artifact(
    value: object, project_root: Path, description: str
) -> ArtifactSpec:
    raw = _mapping(value, description)
    _exact_keys(raw, {"path", "sha256"}, description)
    return ArtifactSpec(
        path=_resolve_path(raw["path"], project_root, f"{description}.path"),
        sha256=_expected_sha256(raw["sha256"], f"{description}.sha256"),
    )


def _training_from_mapping(value: object) -> baseline.TrainingSettings:
    raw = _mapping(value, "training")
    _exact_keys(raw, set(FIXED_TRAINING_CONTRACT), "training")
    observed = {
        "per_device_train_batch_size": _integer(
            raw["per_device_train_batch_size"],
            "training.per_device_train_batch_size",
            1,
        ),
        "per_device_eval_batch_size": _integer(
            raw["per_device_eval_batch_size"],
            "training.per_device_eval_batch_size",
            1,
        ),
        "gradient_accumulation_steps": _integer(
            raw["gradient_accumulation_steps"],
            "training.gradient_accumulation_steps",
            1,
        ),
        "learning_rate": _number(raw["learning_rate"], "training.learning_rate", 1e-12),
        "weight_decay": _number(raw["weight_decay"], "training.weight_decay"),
        "num_train_epochs": _integer(raw["num_train_epochs"], "training.num_train_epochs", 1),
        "warmup_ratio": _number(raw["warmup_ratio"], "training.warmup_ratio"),
        "max_grad_norm": _number(raw["max_grad_norm"], "training.max_grad_norm", 1e-12),
        "save_steps": _integer(raw["save_steps"], "training.save_steps", 1),
        "save_total_limit": _integer(
            raw["save_total_limit"], "training.save_total_limit", 1
        ),
        "num_workers": _integer(raw["num_workers"], "training.num_workers"),
        "resume_from_checkpoint": _nonempty_string(
            raw["resume_from_checkpoint"], "training.resume_from_checkpoint"
        ),
    }
    if observed != dict(FIXED_TRAINING_CONTRACT):
        raise R2DistilBertSidecarProbeError(
            "training 必须与冻结 DistilBERT 探针预算逐项一致"
        )
    return baseline.TrainingSettings(**observed)


def load_config(path: Path) -> ProbeConfig:
    """在导入模型运行时前严格解析一个固定种子配置。"""
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise R2DistilBertSidecarProbeError(f"配置不存在：{config_path}")
    try:
        raw_value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise R2DistilBertSidecarProbeError("配置不是合法 YAML") from error
    raw = _mapping(raw_value, "配置")
    _exact_keys(
        raw,
        {
            "schema_version",
            "dataset",
            "model",
            "training",
            "evaluation",
            "run",
            "storage",
            "tracking",
        },
        "配置",
    )
    if raw["schema_version"] != CONFIG_SCHEMA_VERSION:
        raise R2DistilBertSidecarProbeError("配置 schema_version 不符合探针合同")
    project_root = config_path.parent.parent.resolve()

    dataset_raw = _mapping(raw["dataset"], "dataset")
    _exact_keys(dataset_raw, {"input_summary", "detection_view", "sidecar"}, "dataset")
    dataset = ProbeDatasetSettings(
        input_summary=_artifact(dataset_raw["input_summary"], project_root, "dataset.input_summary"),
        detection_view=_artifact(dataset_raw["detection_view"], project_root, "dataset.detection_view"),
        sidecar=_artifact(dataset_raw["sidecar"], project_root, "dataset.sidecar"),
    )

    model_raw = _mapping(raw["model"], "model")
    _exact_keys(model_raw, {"identifier", "source", "max_length", "device", "precision"}, "model")
    identifier = _nonempty_string(model_raw["identifier"], "model.identifier")
    if identifier != baseline.FIXED_MODEL_ID:
        raise R2DistilBertSidecarProbeError(
            f"model.identifier 必须固定为 {baseline.FIXED_MODEL_ID}"
        )
    source = _resolve_path(model_raw["source"], project_root, "model.source")
    if str(source) == baseline.FIXED_MODEL_ID:
        raise R2DistilBertSidecarProbeError("探针只允许已存在的本地模型镜像，禁止运行时下载")
    max_length = _integer(model_raw["max_length"], "model.max_length", 1)
    if max_length != 128:
        raise R2DistilBertSidecarProbeError("model.max_length 必须与已有基线固定为 128")
    device = _nonempty_string(model_raw["device"], "model.device")
    precision = _nonempty_string(model_raw["precision"], "model.precision")
    if device != "auto" or precision != "auto":
        raise R2DistilBertSidecarProbeError("探针设备和精度必须固定为 auto/auto")
    model = baseline.ModelSettings(
        identifier=identifier,
        source=str(source),
        max_length=max_length,
        device=device,
        precision=precision,
    )
    training = _training_from_mapping(raw["training"])

    evaluation_raw = _mapping(raw["evaluation"], "evaluation")
    _exact_keys(evaluation_raw, {"threshold", "calibration_bins"}, "evaluation")
    threshold = _number(evaluation_raw["threshold"], "evaluation.threshold")
    calibration_bins = _integer(
        evaluation_raw["calibration_bins"], "evaluation.calibration_bins", 2
    )
    if threshold != baseline.FIXED_THRESHOLD or calibration_bins != 15:
        raise R2DistilBertSidecarProbeError("评价阈值和校准箱数必须固定为 0.5/15")
    evaluation = baseline.EvaluationSettings(
        threshold=threshold,
        calibration_bins=calibration_bins,
    )

    run_raw = _mapping(raw["run"], "run")
    _exact_keys(run_raw, {"output_dir", "seed", "stage", "status"}, "run")
    seed = _integer(run_raw["seed"], "run.seed")
    if seed not in ALLOWED_SEEDS:
        raise R2DistilBertSidecarProbeError("run.seed 只允许 42、43、44")
    stage = _nonempty_string(run_raw["stage"], "run.stage")
    status = _nonempty_string(run_raw["status"], "run.status")
    if stage != EXPECTED_STAGE or status != EXPECTED_PROTOCOL_STATUS:
        raise R2DistilBertSidecarProbeError(
            f"运行协议必须固定为 {EXPECTED_STAGE}/{EXPECTED_PROTOCOL_STATUS}"
        )
    output_dir = _resolve_path(run_raw["output_dir"], project_root, "run.output_dir")
    expected_output = (
        project_root
        / "runs/r2-transformer-sidecar-probe/distilbert-v0"
        / f"seed-{seed}"
    ).resolve()
    if output_dir != expected_output:
        raise R2DistilBertSidecarProbeError(
            f"run.output_dir 必须固定为 {expected_output}"
        )
    run = baseline.RunSettings(
        output_dir=output_dir,
        seed=seed,
        stage=stage,
        status=status,
    )

    storage_raw = _mapping(raw["storage"], "storage")
    _exact_keys(
        storage_raw,
        {
            "seed_execution",
            "minimum_free_bytes",
            "artifact_write_reserve_bytes",
        },
        "storage",
    )
    seed_execution = _nonempty_string(
        storage_raw["seed_execution"], "storage.seed_execution"
    )
    minimum_free_bytes = _integer(
        storage_raw["minimum_free_bytes"], "storage.minimum_free_bytes", 1
    )
    artifact_write_reserve_bytes = _integer(
        storage_raw["artifact_write_reserve_bytes"],
        "storage.artifact_write_reserve_bytes",
        1,
    )
    if (
        seed_execution != EXPECTED_SEED_EXECUTION
        or minimum_free_bytes != MINIMUM_FREE_BYTES
        or artifact_write_reserve_bytes != ARTIFACT_WRITE_RESERVE_BYTES
    ):
        raise R2DistilBertSidecarProbeError(
            "storage 必须固定为三种子串行、5 GiB 安全余量和 2 GiB 单次制品写入预留"
        )
    storage = ProbeStorageSettings(
        seed_execution=seed_execution,
        minimum_free_bytes=minimum_free_bytes,
        artifact_write_reserve_bytes=artifact_write_reserve_bytes,
    )

    tracking_raw = _mapping(raw["tracking"], "tracking")
    try:
        tracking = TrackingSettings.from_mapping(tracking_raw)
    except ValueError as error:
        raise R2DistilBertSidecarProbeError(str(error)) from error
    required_tags = {
        "r2-sidecar",
        "distilbert",
        f"seed-{seed}",
        "epochs-3",
        "run-probe",
        "protocol-partial",
    }
    if not required_tags.issubset(tracking.tags):
        raise R2DistilBertSidecarProbeError(
            "tracking.tags 缺少冻结动态标签："
            + ", ".join(sorted(required_tags.difference(tracking.tags)))
        )
    return ProbeConfig(
        dataset=dataset,
        model=model,
        training=training,
        evaluation=evaluation,
        run=run,
        storage=storage,
        tracking=tracking,
        config_path=config_path,
        project_root=project_root,
    )


def config_snapshot(config: ProbeConfig) -> dict[str, object]:
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "dataset": {
            "input_summary": {
                "path": str(config.dataset.input_summary.path),
                "sha256": config.dataset.input_summary.sha256,
            },
            "detection_view": {
                "path": str(config.dataset.detection_view.path),
                "sha256": config.dataset.detection_view.sha256,
            },
            "sidecar": {
                "path": str(config.dataset.sidecar.path),
                "sha256": config.dataset.sidecar.sha256,
            },
        },
        "model": {
            "identifier": config.model.identifier,
            "source": config.model.source,
            "max_length": config.model.max_length,
            "device": config.model.device,
            "precision": config.model.precision,
        },
        "training": dict(FIXED_TRAINING_CONTRACT),
        "evaluation": {
            "threshold": config.evaluation.threshold,
            "calibration_bins": config.evaluation.calibration_bins,
        },
        "run": {
            "output_dir": str(config.run.output_dir),
            "seed": config.run.seed,
            "stage": config.run.stage,
            "status": config.run.status,
        },
        "storage": {
            "seed_execution": config.storage.seed_execution,
            "minimum_free_bytes": config.storage.minimum_free_bytes,
            "artifact_write_reserve_bytes": config.storage.artifact_write_reserve_bytes,
        },
        "tracking": {
            "project": config.tracking.project,
            "workspace": config.tracking.workspace,
            "run_name": config.tracking.run_name,
            "description": config.tracking.description,
            "mode": config.tracking.mode,
            "tags": list(config.tracking.tags),
        },
        "probe": {
            "variants": list(VARIANTS),
            "sidecar_fields": list(SIDECAR_FIELDS),
            "projection": {
                "input_dimension": len(SIDECAR_FIELDS),
                "output_dimension": PROJECTION_OUTPUT_DIMENSION,
                "bias": False,
            },
            "uncertainty_gate": {
                "fields": list(SIDECAR_FIELDS[UNCERTAINTY_START:UNCERTAINTY_STOP]),
                "formula": "sidecar_mask * clamp(1 - mean(uncertainty), 0, 1)",
            },
        },
    }


def _verify_artifact(spec: ArtifactSpec, project_root: Path, description: str) -> Path:
    try:
        spec.path.relative_to(project_root)
    except ValueError as error:
        raise R2DistilBertSidecarProbeError(
            f"{description}必须位于项目根目录内：{spec.path}"
        ) from error
    if not spec.path.is_file() or spec.path.is_symlink():
        raise R2DistilBertSidecarProbeError(f"{description}不是普通文件：{spec.path}")
    actual = baseline.file_sha256(spec.path)
    if actual != spec.sha256:
        raise R2DistilBertSidecarProbeError(
            f"{description} SHA-256 不一致：期望 {spec.sha256}，实际 {actual}"
        )
    return spec.path


def _parquet_columns(path: Path, description: str) -> tuple[str, ...]:
    try:
        return tuple(pq.ParquetFile(path).schema_arrow.names)
    except Exception as error:
        raise R2DistilBertSidecarProbeError(
            f"无法读取{description}的 Parquet 模式：{path}"
        ) from error


def _array_sha256(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _strings_sha256(values: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


def _labels_sha256(values: Sequence[int]) -> str:
    return hashlib.sha256(bytes(values)).hexdigest()


def _read_json(path: Path, description: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise R2DistilBertSidecarProbeError(f"无法读取{description}：{path}") from error
    if not isinstance(value, dict):
        raise R2DistilBertSidecarProbeError(f"{description}顶层必须是对象")
    return value


def _validate_detection_view(frame: pd.DataFrame) -> None:
    if len(frame) != sum(EXPECTED_SAMPLE_COUNTS.values()):
        raise R2DistilBertSidecarProbeError("检测视图必须精确包含 2,560 条开发样本")
    if set(frame["schema_version"].astype(str)) != {EXPECTED_VIEW_SCHEMA}:
        raise R2DistilBertSidecarProbeError("检测视图 schema_version 不符合当前先导合同")
    sample_ids = frame["sample_id"].astype(str)
    if sample_ids.str.len().eq(0).any() or sample_ids.duplicated().any():
        raise R2DistilBertSidecarProbeError("检测视图 sample_id 为空或重复")
    if set(frame["source_dataset"].astype(str)) != {EXPECTED_SOURCE}:
        raise R2DistilBertSidecarProbeError("检测视图只能包含 TQH-C2")
    counts = frame.groupby("split_id", sort=True).size().to_dict()
    if counts != dict(EXPECTED_SAMPLE_COUNTS):
        raise R2DistilBertSidecarProbeError(f"检测视图划分规模不符合合同：{counts}")
    if set(frame["binary_label"].astype(str)) != {"benign", "malicious"}:
        raise R2DistilBertSidecarProbeError("检测视图必须同时且只含二分类标签")
    if frame["transport_family"].astype(str).str.len().eq(0).any():
        raise R2DistilBertSidecarProbeError("检测视图 transport_family 不能为空")
    for field in COMMON_FIELDS:
        missing = frame[f"{field}_missing"].to_numpy(dtype=np.float64)
        if not np.isin(missing, (0.0, 1.0)).all():
            raise R2DistilBertSidecarProbeError(f"{field}_missing 必须是二值")
        observed = missing == 0.0
        values = frame[field].to_numpy(dtype=np.float64)
        if not np.isfinite(values[observed]).all():
            raise R2DistilBertSidecarProbeError(f"{field} 的已观测值包含非有限数")


def _assert_sidecar_metadata(
    detection: pd.DataFrame, sidecar: pd.DataFrame
) -> pd.DataFrame:
    if len(sidecar) != len(detection):
        raise R2DistilBertSidecarProbeError("旁路行数必须与检测视图一致")
    sidecar = sidecar.copy()
    sidecar["sample_id"] = sidecar["sample_id"].astype(str)
    if sidecar["sample_id"].duplicated().any():
        raise R2DistilBertSidecarProbeError("旁路 sample_id 必须唯一")
    detection_indexed = detection.set_index("sample_id", drop=False)
    sidecar_indexed = sidecar.set_index("sample_id", drop=False)
    if set(detection_indexed.index) != set(sidecar_indexed.index):
        raise R2DistilBertSidecarProbeError("旁路 sample_id 与检测视图不一致")
    aligned_detection = detection_indexed.reindex(sidecar_indexed.index)
    for field in ("split_id", "transport_family"):
        expected = aligned_detection[field].astype(str).to_numpy()
        observed = sidecar_indexed[field].astype(str).to_numpy()
        mismatch = np.flatnonzero(expected != observed)
        if mismatch.size:
            sample_id = str(sidecar_indexed.index[int(mismatch[0])])
            raise R2DistilBertSidecarProbeError(
                f"旁路原元数据与检测视图不一致：{sample_id}/{field}"
            )
    projected = sidecar.loc[:, SIDECAR_PROJECTION_COLUMNS].copy()
    projected = projected.set_index("sample_id", drop=False).reindex(detection_indexed.index)
    if tuple(projected.index.astype(str)) != tuple(detection_indexed.index.astype(str)):
        raise R2DistilBertSidecarProbeError("旁路投影无法保持检测视图样本顺序")
    values = projected.loc[:, SIDECAR_FIELDS].to_numpy(dtype=np.float64, copy=True)
    if values.shape != (len(detection), len(SIDECAR_FIELDS)) or not np.isfinite(values).all():
        raise R2DistilBertSidecarProbeError("旁路严格投影后不是有限的 18 维矩阵")
    if np.any(values[:, UNCERTAINTY_START:UNCERTAINTY_STOP] < 0.0):
        raise R2DistilBertSidecarProbeError("旁路不确定性不得为负数")
    for field in ("shared_expert_mask", "tcp_expert_mask", "udp_expert_mask"):
        column = values[:, SIDECAR_FIELDS.index(field)]
        if not np.isin(column, (0.0, 1.0)).all():
            raise R2DistilBertSidecarProbeError(f"{field} 必须是二值")
    confidence = values[:, SIDECAR_FIELDS.index("protocol_confidence")]
    if np.any(confidence < 0.0) or np.any(confidence > 1.0):
        raise R2DistilBertSidecarProbeError("protocol_confidence 必须位于 [0,1]")
    return projected.reset_index(drop=True)


def _development_split(
    name: str, frame: pd.DataFrame, sidecar_values: np.ndarray
) -> DevelopmentSplit:
    labels = tuple(frame["binary_label"].astype(str))
    return DevelopmentSplit(
        name=name,
        sample_ids=tuple(frame["sample_id"].astype(str)),
        labels=labels,
        source_datasets=tuple(frame["source_dataset"].astype(str)),
        transport_families=tuple(frame["transport_family"].astype(str)),
        common_features=np.empty((len(frame), 0), dtype=np.float64),
        sidecar_features=sidecar_values,
    )


def _freeze_array(values: np.ndarray, description: str) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64)
    if result.ndim != 2 or result.shape[1] != len(SIDECAR_FIELDS):
        raise R2DistilBertSidecarProbeError(f"{description}不是 18 维旁路矩阵")
    if not np.isfinite(result).all():
        raise R2DistilBertSidecarProbeError(f"{description}包含非有限数")
    result.setflags(write=False)
    return result


def _probe_split(
    name: str,
    frame: pd.DataFrame,
    sidecar_values: np.ndarray,
    sidecar_mask: float,
) -> ProbeSplit:
    labels = tuple(0 if value == "benign" else 1 for value in frame["binary_label"].astype(str))
    texts = tuple(
        render_input_text({field: row[field] for field in COMMON_FEATURE_FIELDS})
        for row in frame.loc[:, COMMON_FEATURE_FIELDS].to_dict(orient="records")
    )
    if any(not text or text != text.strip() for text in texts):
        raise R2DistilBertSidecarProbeError(f"{name} 基础文本渲染结果非法")
    masks = np.full(len(frame), sidecar_mask, dtype=np.float64)
    masks.setflags(write=False)
    return ProbeSplit(
        name=name,
        sample_ids=tuple(frame["sample_id"].astype(str)),
        stable_orders=tuple(range(len(frame))),
        texts=texts,
        labels=labels,
        source_datasets=tuple(frame["source_dataset"].astype(str)),
        transport_families=tuple(frame["transport_family"].astype(str)),
        sidecar_features=_freeze_array(sidecar_values, f"{name} 旁路"),
        sidecar_masks=masks,
    )


def _variant_sidecars(
    train: DevelopmentSplit,
    validation: DevelopmentSplit,
    variant: str,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, float]:
    if variant == "T-A":
        return (
            np.zeros_like(train.sidecar_features),
            np.zeros_like(validation.sidecar_features),
            0.0,
        )
    if variant == "T-P":
        return train.sidecar_features, validation.sidecar_features, 1.0
    if variant == "T-S":
        return (
            shuffled_sidecar(train, seed),
            shuffled_sidecar(validation, seed + 10_000),
            1.0,
        )
    if variant == "T-R":
        return (
            random_sidecar(train, train, seed),
            random_sidecar(validation, train, seed + 20_000),
            1.0,
        )
    raise R2DistilBertSidecarProbeError(f"未知探针组：{variant}")


def _split_binding(split: ProbeSplit) -> dict[str, object]:
    return {
        "sample_count": len(split),
        "sample_order_sha256": _strings_sha256(split.sample_ids),
        "text_sha256": _strings_sha256(split.texts),
        "label_sha256": _labels_sha256(split.labels),
        "label_counts": {
            baseline.FIXED_LABEL_MAPPING[label]: Counter(split.labels).get(label, 0)
            for label in baseline.FIXED_LABEL_MAPPING
        },
        "sidecar_sha256": _array_sha256(split.sidecar_features),
        "sidecar_mask_sha256": _array_sha256(split.sidecar_masks),
        "sidecar_mask_active_count": int(np.count_nonzero(split.sidecar_masks)),
    }


def prepare_probe_inputs(config: ProbeConfig) -> PreparedProbeInputs:
    """只从冻结开发输入构造文本和四组旁路，并在加载模型前完成装订。"""
    summary_path = _verify_artifact(
        config.dataset.input_summary, config.project_root, "先导输入摘要"
    )
    detection_path = _verify_artifact(
        config.dataset.detection_view, config.project_root, "TQH-C2 检测视图"
    )
    sidecar_path = _verify_artifact(
        config.dataset.sidecar, config.project_root, "TQH-C2 18 维旁路"
    )
    summary = _read_json(summary_path, "先导输入摘要")
    if summary.get("status") != EXPECTED_DATASET_STATUS:
        raise R2DistilBertSidecarProbeError("先导输入摘要状态不符合当前 TCP/UDP 探针合同")
    tqhc2 = _mapping(summary.get("tqhc2"), "先导输入摘要.tqhc2")
    if tqhc2.get("sample_counts") != dict(EXPECTED_SAMPLE_COUNTS):
        raise R2DistilBertSidecarProbeError("先导输入摘要中的 TQH-C2 样本数不一致")
    artifacts = _mapping(tqhc2.get("artifacts"), "先导输入摘要.tqhc2.artifacts")
    view_record = _mapping(
        artifacts.get(detection_path.name), "先导输入摘要中的检测视图记录"
    )
    if view_record.get("sha256") != config.dataset.detection_view.sha256:
        raise R2DistilBertSidecarProbeError("检测视图未与先导输入摘要绑定")

    if _parquet_columns(detection_path, "检测视图") != DETECTION_VIEW_COLUMNS:
        raise R2DistilBertSidecarProbeError("检测视图列顺序不符合当前先导合同")
    if _parquet_columns(sidecar_path, "旁路") != SIDECAR_SOURCE_COLUMNS:
        raise R2DistilBertSidecarProbeError("旁路源列必须严格等于元数据加 18 维合同")
    try:
        detection = pd.read_parquet(detection_path, columns=list(DETECTION_VIEW_COLUMNS))
        sidecar_raw = pd.read_parquet(sidecar_path, columns=list(SIDECAR_SOURCE_COLUMNS))
    except Exception as error:
        raise R2DistilBertSidecarProbeError("无法读取 TQH-C2 探针 Parquet 输入") from error
    detection = detection.copy()
    detection["sample_id"] = detection["sample_id"].astype(str)
    _validate_detection_view(detection)
    projected_sidecar = _assert_sidecar_metadata(detection, sidecar_raw)
    real_values = projected_sidecar.loc[:, SIDECAR_FIELDS].to_numpy(dtype=np.float64, copy=True)

    split_frames = {
        name: detection.loc[detection["split_id"] == name].copy()
        for name in (TRAIN_SPLIT, VALIDATION_SPLIT)
    }
    split_values = {
        name: real_values[detection["split_id"].astype(str).to_numpy() == name]
        for name in (TRAIN_SPLIT, VALIDATION_SPLIT)
    }
    train_development = _development_split(
        TRAIN_SPLIT, split_frames[TRAIN_SPLIT], split_values[TRAIN_SPLIT]
    )
    validation_development = _development_split(
        VALIDATION_SPLIT,
        split_frames[VALIDATION_SPLIT],
        split_values[VALIDATION_SPLIT],
    )

    variants: dict[str, VariantInputs] = {}
    common_hashes: dict[str, dict[str, str]] = {}
    for variant in VARIANTS:
        train_sidecar, validation_sidecar, active_mask = _variant_sidecars(
            train_development,
            validation_development,
            variant,
            config.run.seed,
        )
        train_split = _probe_split(
            TRAIN_SPLIT,
            split_frames[TRAIN_SPLIT],
            train_sidecar,
            active_mask,
        )
        validation_split = _probe_split(
            VALIDATION_SPLIT,
            split_frames[VALIDATION_SPLIT],
            validation_sidecar,
            active_mask,
        )
        split_bindings = {
            TRAIN_SPLIT: _split_binding(train_split),
            VALIDATION_SPLIT: _split_binding(validation_split),
        }
        for name, binding in split_bindings.items():
            current = {
                key: str(binding[key])
                for key in ("sample_order_sha256", "text_sha256", "label_sha256")
            }
            if name in common_hashes and common_hashes[name] != current:
                raise R2DistilBertSidecarProbeError(
                    f"{variant} 改变了{name}的样本、文本或标签"
                )
            common_hashes[name] = current
        variant_binding = {
            "variant": variant,
            "seed": config.run.seed,
            "transformation": {
                "T-A": "全零 18 维旁路且 sidecar_mask=0",
                "T-P": "真实 18 维旁路且 sidecar_mask=1",
                "T-S": "同来源、同传输族、同划分内完整向量置换",
                "T-R": "逐维仅从同来源、同传输族训练池抽样",
            }[variant],
            "label_used_for_transformation": False,
            "splits": split_bindings,
        }
        variants[variant] = VariantInputs(
            variant=variant,
            train=train_split,
            validation=validation_split,
            binding=MappingProxyType(variant_binding),
        )

    binding = {
        "schema_version": INPUT_BINDING_SCHEMA_VERSION,
        "stage": EXPECTED_STAGE,
        "status": EXPECTED_PROTOCOL_STATUS,
        "final_test_visible": False,
        "source_dataset": EXPECTED_SOURCE,
        "input_summary": {
            "path": str(summary_path),
            "sha256": config.dataset.input_summary.sha256,
            "size_bytes": summary_path.stat().st_size,
        },
        "detection_view": {
            "path": str(detection_path),
            "sha256": config.dataset.detection_view.sha256,
            "size_bytes": detection_path.stat().st_size,
            "metadata_source": True,
            "classification_text_fields": list(COMMON_FEATURE_FIELDS),
            "forbidden_text_fields": [
                "binary_label",
                "source_dataset",
                "split_id",
                "profile",
                "transport_family",
                "protocol_confidence",
            ],
        },
        "sidecar": {
            "path": str(sidecar_path),
            "sha256": config.dataset.sidecar.sha256,
            "size_bytes": sidecar_path.stat().st_size,
            "source_columns": list(SIDECAR_SOURCE_COLUMNS),
            "metadata_asserted": ["split_id", "transport_family"],
            "join_projection": list(SIDECAR_PROJECTION_COLUMNS),
            "metadata_used_after_assertion": False,
        },
        "variants": {variant: dict(values.binding) for variant, values in variants.items()},
    }
    return PreparedProbeInputs(
        variants=MappingProxyType(variants),
        binding=MappingProxyType(binding),
        binding_sha256=baseline._canonical_sha256(binding),
    )


def _new_run_state(binding_sha256: str) -> dict[str, object]:
    timestamp = baseline._utc_now()
    return {
        "schema_version": RUN_STATE_SCHEMA_VERSION,
        "run_id": uuid.uuid4().hex,
        "status": "prepared",
        "binding_sha256": binding_sha256,
        "current_step": 0,
        "current_epoch": 0,
        "next_batch_index": 0,
        "latest_checkpoint": None,
        "best_model": None,
        "best_epoch": None,
        "best_macro_f1": None,
        "swanlab_attempts": [],
        "started_at": timestamp,
        "updated_at": timestamp,
        "failure": None,
    }


def _validate_run_state(value: Mapping[str, object], path: Path) -> dict[str, object]:
    required = set(_new_run_state("0" * 64))
    if set(value) != required:
        raise R2DistilBertSidecarProbeError(
            f"运行状态字段不符合合同：{path}"
        )
    if value.get("schema_version") != RUN_STATE_SCHEMA_VERSION:
        raise R2DistilBertSidecarProbeError("运行状态 schema_version 非法")
    if value.get("status") not in RUN_STATUSES:
        raise R2DistilBertSidecarProbeError("运行状态 status 非法")
    _expected_sha256(value.get("binding_sha256"), "运行状态 binding_sha256")
    for field in ("current_step", "current_epoch", "next_batch_index"):
        _integer(value.get(field), f"运行状态 {field}")
    for field in ("run_id", "started_at", "updated_at"):
        _nonempty_string(value.get(field), f"运行状态 {field}")
    for field in ("latest_checkpoint", "best_model", "failure"):
        raw = value.get(field)
        if raw is not None and not isinstance(raw, str):
            raise R2DistilBertSidecarProbeError(
                f"运行状态 {field} 必须是字符串或空值"
            )
    if value.get("best_epoch") is not None:
        _integer(value.get("best_epoch"), "运行状态 best_epoch")
    if value.get("best_macro_f1") is not None:
        metric = _number(value.get("best_macro_f1"), "运行状态 best_macro_f1")
        if metric > 1.0:
            raise R2DistilBertSidecarProbeError("运行状态 best_macro_f1 不得超过 1")
    attempts = value.get("swanlab_attempts")
    if not isinstance(attempts, list) or any(not isinstance(item, dict) for item in attempts):
        raise R2DistilBertSidecarProbeError("运行状态 swanlab_attempts 必须是对象列表")
    return dict(value)


class ProbeRunStateController:
    """以原子 JSON 转换维护单个探针组的运行状态。"""

    def __init__(self, path: Path, initial: Mapping[str, object] | None = None) -> None:
        self.path = path
        source = _read_json(path, "运行状态") if initial is None else dict(initial)
        self._state = _validate_run_state(source, path)

    @property
    def state(self) -> Mapping[str, object]:
        return MappingProxyType(dict(self._state))

    @property
    def status(self) -> str:
        return str(self._state["status"])

    def transition(self, status: str, **updates: object) -> None:
        if status not in RUN_STATUSES:
            raise R2DistilBertSidecarProbeError(f"非法运行状态：{status}")
        unknown = sorted(set(updates).difference(self._state))
        if unknown:
            raise R2DistilBertSidecarProbeError(
                "运行状态更新含未知字段：" + ", ".join(unknown)
            )
        next_state = {
            **self._state,
            **updates,
            "status": status,
            "updated_at": baseline._utc_now(),
        }
        self._state = _validate_run_state(next_state, self.path)
        baseline._atomic_write_json(self.path, self._state)

    def update(self, **updates: object) -> None:
        self.transition(self.status, **updates)

    def mark_interrupted(self, error: BaseException) -> None:
        self.transition("interrupted", failure=f"{type(error).__name__}: {error}")

    def mark_failed(self, error: BaseException) -> None:
        self.transition("failed", failure=f"{type(error).__name__}: {error}")


def _semantic_dependency_sha256() -> dict[str, str]:
    module_root = Path(__file__).resolve().parent
    bindings: dict[str, str] = {}
    for filename in SEMANTIC_DEPENDENCY_FILES:
        path = module_root / filename
        if not path.is_file() or path.is_symlink():
            raise R2DistilBertSidecarProbeError(f"运行语义依赖不是普通文件：{path}")
        bindings[filename] = baseline.file_sha256(path)
    return bindings


def _assert_disk_capacity(config: ProbeConfig, operation: str) -> None:
    available_bytes = shutil.disk_usage(config.project_root).free
    required_bytes = (
        config.storage.minimum_free_bytes
        + config.storage.artifact_write_reserve_bytes
    )
    if available_bytes < required_bytes:
        raise R2DistilBertSidecarProbeError(
            f"{operation}磁盘门禁失败：至少需要 {required_bytes} 字节（含 "
            f"{config.storage.minimum_free_bytes} 字节安全余量），当前可用 "
            f"{available_bytes} 字节"
        )


@contextmanager
def _serial_seed_execution(config: ProbeConfig) -> Iterator[None]:
    lock_root = config.run.output_dir.parent
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / ".seed-execution.lock"
    if lock_path.is_symlink():
        raise R2DistilBertSidecarProbeError(f"串行种子锁不得为符号链接：{lock_path}")
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise R2DistilBertSidecarProbeError(
                "已有另一个 DistilBERT 种子正在运行，拒绝并发启动"
            ) from error
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _build_run_binding(
    config: ProbeConfig,
    prepared_inputs: PreparedProbeInputs,
    variant_inputs: VariantInputs,
    model_binding: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": RUN_BINDING_SCHEMA_VERSION,
        "config": config_snapshot(config),
        "config_file_sha256": baseline.file_sha256(config.config_path),
        "implementation_sha256": baseline.file_sha256(Path(__file__)),
        "semantic_dependency_sha256": _semantic_dependency_sha256(),
        "input_binding_sha256": prepared_inputs.binding_sha256,
        "variant_binding_sha256": baseline._canonical_sha256(variant_inputs.binding),
        "model_binding_sha256": baseline._canonical_sha256(model_binding),
        "seed": config.run.seed,
        "variant": variant_inputs.variant,
        "sample_counts": {
            TRAIN_SPLIT: len(variant_inputs.train),
            VALIDATION_SPLIT: len(variant_inputs.validation),
        },
        "model_structure": {
            "base_model": baseline.FIXED_MODEL_ID,
            "sidecar_projection": {
                "in_features": len(SIDECAR_FIELDS),
                "out_features": PROJECTION_OUTPUT_DIMENSION,
                "bias": False,
            },
            "uncertainty_gate": "sidecar_mask * clamp(1 - mean(q0:q4 uncertainty), 0, 1)",
        },
        "optimizer": {
            "name": "AdamW",
            **{
                key: FIXED_TRAINING_CONTRACT[key]
                for key in ("learning_rate", "weight_decay", "max_grad_norm")
            },
        },
        "training_budget": dict(FIXED_TRAINING_CONTRACT),
        "expected_optimizer_steps": FIXED_TOTAL_OPTIMIZER_STEPS,
        "final_test_visible": False,
    }


def _variant_output(config: ProbeConfig, variant: str) -> Path:
    return config.run.output_dir / VARIANT_SLUGS[variant]


def _validate_checkpoint(
    path: Path, binding_sha256: str
) -> dict[str, object] | None:
    match = baseline.CHECKPOINT_PATTERN.fullmatch(path.name)
    if match is None or not path.is_dir() or path.is_symlink():
        return None
    try:
        manifest = _read_json(path / "checkpoint_manifest.json", "检查点清单")
        if manifest.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
            return None
        if manifest.get("binding_sha256") != binding_sha256:
            return None
        if manifest.get("global_step") != int(match.group(1)):
            return None
        for field in ("next_epoch", "next_batch_index"):
            _integer(manifest.get(field), f"检查点 {field}")
        artifacts = _mapping(manifest.get("artifacts"), "检查点 artifacts")
        required = {
            "training_state.pt",
            "sidecar_projection.pt",
            "fusion_config.json",
            "config.json",
        }
        if not required.issubset(artifacts):
            return None
        if not any(
            name.endswith(".safetensors") or name.startswith("pytorch_model")
            for name in artifacts
        ):
            return None
        for relative, raw_record in artifacts.items():
            record = _mapping(raw_record, f"检查点制品 {relative}")
            artifact_path = (path / relative).resolve()
            artifact_path.relative_to(path.resolve())
            expected_size = _integer(record.get("size_bytes"), f"{relative} 大小")
            expected_hash = _expected_sha256(record.get("sha256"), f"{relative} 哈希")
            if (
                not artifact_path.is_file()
                or artifact_path.stat().st_size != expected_size
                or baseline.file_sha256(artifact_path) != expected_hash
            ):
                return None
        best_model = manifest.get("best_model")
        if best_model is not None:
            selection_path = Path(str(best_model)).resolve()
            selection_manifest = _read_json(
                selection_path / "selection_manifest.json", "选模清单"
            )
            if selection_manifest.get("binding_sha256") != binding_sha256:
                return None
    except (OSError, ValueError, R2DistilBertSidecarProbeError):
        return None
    return manifest


def _latest_checkpoint(output: Path, binding_sha256: str) -> Path | None:
    if not output.is_dir():
        return None
    candidates: list[tuple[int, Path]] = []
    for path in output.iterdir():
        match = baseline.CHECKPOINT_PATTERN.fullmatch(path.name)
        if match is not None and path.is_dir():
            candidates.append((int(match.group(1)), path))
    for _, path in sorted(candidates, reverse=True):
        if _validate_checkpoint(path, binding_sha256) is not None:
            return path
    return None


def prepare_variant_run(
    config: ProbeConfig,
    prepared_inputs: PreparedProbeInputs,
    model_binding: Mapping[str, object],
    variant: str,
) -> PreparedVariantRun:
    inputs = prepared_inputs.variants[variant]
    run_binding = _build_run_binding(config, prepared_inputs, inputs, model_binding)
    binding_sha256 = baseline._canonical_sha256(run_binding)
    output = _variant_output(config, variant)
    state_path = output / "run_state.json"
    binding_path = output / "run_binding.json"
    if not output.exists():
        output.mkdir(parents=True)
        baseline._atomic_write_json(output / "config_snapshot.json", config_snapshot(config))
        baseline._atomic_write_json(output / "input_binding.json", dict(prepared_inputs.binding))
        baseline._atomic_write_json(output / "model_binding.json", dict(model_binding))
        baseline._atomic_write_json(binding_path, run_binding)
        state = _new_run_state(binding_sha256)
        baseline._atomic_write_json(state_path, state)
        return PreparedVariantRun(
            config=config,
            inputs=inputs,
            model_binding=model_binding,
            run_binding=MappingProxyType(run_binding),
            binding_sha256=binding_sha256,
            output_dir=output,
            state_path=state_path,
            resume_checkpoint=None,
            resume_finalization=False,
        )
    if output.is_symlink() or not output.is_dir():
        raise R2DistilBertSidecarProbeError(f"探针组输出不是普通目录：{output}")
    for required in (binding_path, state_path):
        if not required.is_file():
            raise R2DistilBertSidecarProbeError(f"已有运行缺少恢复制品：{required}")
    stored_binding = _read_json(binding_path, "已有运行绑定")
    if stored_binding != run_binding:
        raise R2DistilBertSidecarProbeError(f"{variant} 已有运行绑定不一致")
    state = _validate_run_state(_read_json(state_path, "已有运行状态"), state_path)
    if state["binding_sha256"] != binding_sha256:
        raise R2DistilBertSidecarProbeError(f"{variant} 状态与绑定哈希不一致")
    finalization_path = output / "finalization_receipt.json"
    if state["status"] in {"finalizing", "failed", "interrupted"} and finalization_path.is_file():
        _validate_finalization_receipt(output, binding_sha256, state["run_id"])
        state.update(
            {
                "status": "finalizing",
                "updated_at": baseline._utc_now(),
            }
        )
        baseline._atomic_write_json(state_path, _validate_run_state(state, state_path))
        return PreparedVariantRun(
            config=config,
            inputs=inputs,
            model_binding=model_binding,
            run_binding=MappingProxyType(run_binding),
            binding_sha256=binding_sha256,
            output_dir=output,
            state_path=state_path,
            resume_checkpoint=None,
            resume_finalization=True,
        )
    checkpoint = _latest_checkpoint(output, binding_sha256)
    failed_auto_resume = (
        state["status"] == "failed"
        and config.training.resume_from_checkpoint == "auto"
        and checkpoint is not None
    )
    if state["status"] not in RESUMABLE_STATUSES and not failed_auto_resume:
        raise R2DistilBertSidecarProbeError(
            f"{variant} 运行状态为 {state['status']}，拒绝覆盖"
        )
    if int(state["current_step"]) > 0 and checkpoint is None:
        raise R2DistilBertSidecarProbeError(f"{variant} 有训练进度但没有合法检查点")
    if checkpoint is not None:
        manifest = _validate_checkpoint(checkpoint, binding_sha256)
        assert manifest is not None
        state.update(
            {
                "status": "prepared",
                "current_step": int(manifest["global_step"]),
                "current_epoch": int(manifest["next_epoch"]),
                "next_batch_index": int(manifest["next_batch_index"]),
                "latest_checkpoint": str(checkpoint),
                "best_model": manifest.get("best_model"),
                "best_epoch": manifest.get("best_epoch"),
                "best_macro_f1": manifest.get("best_macro_f1"),
                "updated_at": baseline._utc_now(),
            }
        )
        baseline._atomic_write_json(state_path, _validate_run_state(state, state_path))
    return PreparedVariantRun(
        config=config,
        inputs=inputs,
        model_binding=model_binding,
        run_binding=MappingProxyType(run_binding),
        binding_sha256=binding_sha256,
        output_dir=output,
        state_path=state_path,
        resume_checkpoint=checkpoint,
        resume_finalization=False,
    )


def _build_sidecar_model(
    modules: baseline.RuntimeModules,
    config: ProbeConfig,
    runtime: baseline.RuntimeSelection,
    source: str | Path,
) -> tuple[Any, Any]:
    tokenizer, backbone = baseline._load_tokenizer_and_model(
        modules,
        config,
        runtime,
        source=source,
    )
    if not all(
        hasattr(backbone, attribute)
        for attribute in ("distilbert", "pre_classifier", "dropout", "classifier")
    ):
        raise R2DistilBertSidecarProbeError("本地模型不是可融合的 DistilBERT 分类结构")

    torch_module = modules.torch

    class SidecarClassifier(torch_module.nn.Module):
        def __init__(self, base: Any) -> None:
            super().__init__()
            self.backbone = base
            self.sidecar_projection = torch_module.nn.Linear(
                len(SIDECAR_FIELDS),
                PROJECTION_OUTPUT_DIMENSION,
                bias=False,
            )

        def forward(
            self,
            *,
            input_ids: Any,
            attention_mask: Any,
            sidecar_features: Any,
            sidecar_mask: Any,
            labels: Any | None = None,
        ) -> ProbeModelOutput:
            if sidecar_features.ndim != 2 or sidecar_features.shape[1] != len(SIDECAR_FIELDS):
                raise R2DistilBertSidecarProbeError("模型收到的旁路张量必须为 [batch,18]")
            if sidecar_mask.ndim != 1 or sidecar_mask.shape[0] != sidecar_features.shape[0]:
                raise R2DistilBertSidecarProbeError("模型收到的旁路掩码形状非法")
            hidden = self.backbone.distilbert(
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_dict=True,
            ).last_hidden_state[:, 0]
            representation = self.backbone.pre_classifier(hidden)
            representation = torch_module.nn.functional.relu(representation)
            sidecar = sidecar_features.to(dtype=representation.dtype)
            uncertainty = sidecar[:, UNCERTAINTY_START:UNCERTAINTY_STOP].mean(dim=1)
            confidence = torch_module.clamp(1.0 - uncertainty, min=0.0, max=1.0)
            gate = sidecar_mask.to(dtype=representation.dtype) * confidence
            projected = self.sidecar_projection(sidecar)
            fused = representation + gate.unsqueeze(1) * projected
            logits = self.backbone.classifier(self.backbone.dropout(fused))
            if logits.ndim != 2 or logits.shape[1] != 2:
                raise R2DistilBertSidecarProbeError("融合模型 logits 必须为 [batch,2]")
            loss = None
            if labels is not None:
                loss = torch_module.nn.functional.cross_entropy(logits, labels)
            return ProbeModelOutput(logits=logits, loss=loss)

    model = SidecarClassifier(backbone)
    model.to(runtime.device)
    projection_path = Path(source) / "sidecar_projection.pt"
    fusion_path = Path(source) / "fusion_config.json"
    if projection_path.is_file() or fusion_path.is_file():
        if not projection_path.is_file() or not fusion_path.is_file():
            raise R2DistilBertSidecarProbeError("融合模型制品不完整")
        fusion = _read_json(fusion_path, "融合配置")
        if fusion != {
            "schema_version": FUSION_SCHEMA_VERSION,
            "input_dimension": len(SIDECAR_FIELDS),
            "output_dimension": PROJECTION_OUTPUT_DIMENSION,
            "bias": False,
            "uncertainty_indices": list(range(UNCERTAINTY_START, UNCERTAINTY_STOP)),
        }:
            raise R2DistilBertSidecarProbeError("融合配置与当前计算图不一致")
        try:
            projection_state = torch_module.load(
                projection_path,
                map_location="cpu",
                weights_only=True,
            )
        except TypeError:
            projection_state = torch_module.load(projection_path, map_location="cpu")
        model.sidecar_projection.load_state_dict(projection_state, strict=True)
    if model.sidecar_projection.bias is not None:
        raise R2DistilBertSidecarProbeError("18 维旁路投影不得含偏置")
    if (
        model.sidecar_projection.in_features != len(SIDECAR_FIELDS)
        or model.sidecar_projection.out_features != PROJECTION_OUTPUT_DIMENSION
    ):
        raise R2DistilBertSidecarProbeError("旁路投影维度不符合 18→768 合同")
    return tokenizer, model


def _save_model_bundle(
    model: Any,
    tokenizer: Any,
    target: Path,
    torch_module: Any,
) -> None:
    model.backbone.save_pretrained(target, safe_serialization=True)
    tokenizer.save_pretrained(target)
    torch_module.save(model.sidecar_projection.state_dict(), target / "sidecar_projection.pt")
    baseline._atomic_write_json(
        target / "fusion_config.json",
        {
            "schema_version": FUSION_SCHEMA_VERSION,
            "input_dimension": len(SIDECAR_FIELDS),
            "output_dimension": PROJECTION_OUTPUT_DIMENSION,
            "bias": False,
            "uncertainty_indices": list(range(UNCERTAINTY_START, UNCERTAINTY_STOP)),
        },
    )


def _parameter_contract(model: Any) -> dict[str, object]:
    parameters = []
    total = 0
    trainable = 0
    for name, parameter in model.named_parameters():
        count = int(parameter.numel())
        total += count
        if parameter.requires_grad:
            trainable += count
        parameters.append(
            {
                "name": name,
                "shape": list(parameter.shape),
                "count": count,
                "trainable": bool(parameter.requires_grad),
            }
        )
    return {
        "parameter_count": total,
        "trainable_parameter_count": trainable,
        "structure_sha256": baseline._canonical_sha256(parameters),
        "projection_parameter_count": int(model.sidecar_projection.weight.numel()),
        "projection_bias": model.sidecar_projection.bias is not None,
    }


def _head_initialization_sha256(model: Any) -> str:
    digest = hashlib.sha256()
    modules = (
        ("pre_classifier", model.backbone.pre_classifier),
        ("classifier", model.backbone.classifier),
        ("sidecar_projection", model.sidecar_projection),
    )
    for prefix, module in modules:
        for name, value in sorted(module.state_dict().items()):
            array = value.detach().cpu().contiguous().numpy()
            digest.update(f"{prefix}.{name}".encode("utf-8"))
            digest.update(str(array.dtype).encode("ascii"))
            digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _optimizer_contract(optimizer: Any, model: Any, config: ProbeConfig) -> dict[str, object]:
    trainable_ids = {id(parameter) for parameter in model.parameters() if parameter.requires_grad}
    optimizer_parameters = [
        parameter for group in optimizer.param_groups for parameter in group["params"]
    ]
    optimizer_ids = [id(parameter) for parameter in optimizer_parameters]
    if len(optimizer_ids) != len(set(optimizer_ids)) or set(optimizer_ids) != trainable_ids:
        raise R2DistilBertSidecarProbeError("优化器必须精确覆盖全部可训练参数且不得重复")
    return {
        "name": type(optimizer).__name__,
        "parameter_group_count": len(optimizer.param_groups),
        "parameter_tensor_count": len(optimizer_parameters),
        "parameter_count": sum(int(parameter.numel()) for parameter in optimizer_parameters),
        "learning_rate": config.training.learning_rate,
        "weight_decay": config.training.weight_decay,
    }


def _assert_shared_structure(
    prepared: PreparedVariantRun,
    parameter_contract: Mapping[str, object],
    optimizer_contract: Mapping[str, object],
    initial_head_sha256: str | None,
) -> None:
    path = prepared.config.run.output_dir / "shared_structure_contract.json"
    current = {
        "schema_version": STRUCTURE_SCHEMA_VERSION,
        "seed": prepared.config.run.seed,
        "model_id": baseline.FIXED_MODEL_ID,
        "parameter_contract": dict(parameter_contract),
        "optimizer_contract": dict(optimizer_contract),
        "training_budget": dict(FIXED_TRAINING_CONTRACT),
        "expected_optimizer_steps": FIXED_TOTAL_OPTIMIZER_STEPS,
        "initial_head_sha256": initial_head_sha256,
    }
    if not path.exists():
        if initial_head_sha256 is None:
            raise R2DistilBertSidecarProbeError("恢复运行缺少共享结构合同")
        baseline._atomic_write_json(path, current)
        return
    stored = _read_json(path, "共享结构合同")
    comparable = dict(current)
    if initial_head_sha256 is None:
        comparable["initial_head_sha256"] = stored.get("initial_head_sha256")
    if stored != comparable:
        raise R2DistilBertSidecarProbeError(
            f"{prepared.inputs.variant} 与其他探针组的模型、优化器或预算不一致"
        )


class _ProbeDataset:
    def __init__(self, split: ProbeSplit) -> None:
        self.split = split

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, index: int) -> tuple[str, int, np.ndarray, float]:
        return (
            self.split.texts[index],
            self.split.labels[index],
            self.split.sidecar_features[index],
            float(self.split.sidecar_masks[index]),
        )


def _collate_batch(tokenizer: Any, max_length: int, torch_module: Any):
    def collate(items: Sequence[tuple[str, int, np.ndarray, float]]) -> dict[str, Any]:
        texts, labels, sidecars, masks = zip(*items, strict=True)
        encoded = tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch_module.tensor(labels, dtype=torch_module.long)
        encoded["sidecar_features"] = torch_module.tensor(
            np.stack(sidecars), dtype=torch_module.float32
        )
        encoded["sidecar_mask"] = torch_module.tensor(masks, dtype=torch_module.float32)
        return encoded

    return collate


def _data_loader(
    *,
    split: ProbeSplit,
    tokenizer: Any,
    batch_size: int,
    max_length: int,
    torch_module: Any,
    shuffle: bool,
    seed: int,
    num_workers: int,
) -> Any:
    generator = torch_module.Generator()
    generator.manual_seed(seed)
    return torch_module.utils.data.DataLoader(
        _ProbeDataset(split),
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=num_workers,
        collate_fn=_collate_batch(tokenizer, max_length, torch_module),
        pin_memory=bool(torch_module.cuda.is_available()),
        persistent_workers=bool(num_workers),
    )


def _evaluate_split(
    *,
    model: Any,
    tokenizer: Any,
    split: ProbeSplit,
    config: ProbeConfig,
    runtime: baseline.RuntimeSelection,
    torch_module: Any,
) -> tuple[dict[str, int | float], tuple[Mapping[str, object], ...]]:
    loader = _data_loader(
        split=split,
        tokenizer=tokenizer,
        batch_size=config.training.per_device_eval_batch_size,
        max_length=config.model.max_length,
        torch_module=torch_module,
        shuffle=False,
        seed=config.run.seed,
        num_workers=config.training.num_workers,
    )
    model.eval()
    probabilities: list[float] = []
    latencies: list[float] = []
    baseline._synchronize(torch_module, runtime)
    started = time.perf_counter()
    with torch_module.no_grad():
        for batch in loader:
            batch_started = time.perf_counter()
            batch = {key: value.to(runtime.device) for key, value in batch.items()}
            labels = batch.pop("labels")
            with baseline._autocast(torch_module, runtime):
                output = model(**batch)
            logits = output.logits
            if logits.shape != (int(labels.shape[0]), 2):
                raise R2DistilBertSidecarProbeError("评价 logits 形状非法")
            values = torch_module.softmax(logits.float(), dim=-1)[:, 1]
            batch_probabilities = tuple(
                float(value) for value in values.detach().cpu().tolist()
            )
            if any(
                not math.isfinite(value) or value < 0.0 or value > 1.0
                for value in batch_probabilities
            ):
                raise R2DistilBertSidecarProbeError("模型输出了非法恶意概率")
            probabilities.extend(batch_probabilities)
            baseline._synchronize(torch_module, runtime)
            elapsed = time.perf_counter() - batch_started
            latencies.extend([elapsed / int(labels.shape[0])] * int(labels.shape[0]))
    baseline._synchronize(torch_module, runtime)
    inference_seconds = time.perf_counter() - started
    metrics = baseline.compute_binary_metrics(
        split.labels,
        probabilities,
        threshold=config.evaluation.threshold,
        calibration_bins=config.evaluation.calibration_bins,
    )
    latency_array = np.asarray(latencies, dtype=np.float64) * 1000.0
    metrics.update(
        {
            "inference_seconds": inference_seconds,
            "samples_per_second": len(split) / max(inference_seconds, 1e-12),
            "latency_mean_ms": float(np.mean(latency_array)),
            "latency_p50_ms": float(np.percentile(latency_array, 50)),
            "latency_p95_ms": float(np.percentile(latency_array, 95)),
        }
    )
    rows = tuple(
        {
            "sample_id": sample_id,
            "stable_order": stable_order,
            "probability_malicious": probability,
            "prediction": int(probability >= baseline.FIXED_THRESHOLD),
            "prediction_label": baseline.FIXED_LABEL_MAPPING[
                int(probability >= baseline.FIXED_THRESHOLD)
            ],
            "label": label,
            "label_name": baseline.FIXED_LABEL_MAPPING[label],
        }
        for sample_id, stable_order, probability, label in zip(
            split.sample_ids,
            split.stable_orders,
            probabilities,
            split.labels,
            strict=True,
        )
    )
    return metrics, rows


def _save_selected_model(
    *,
    prepared: PreparedVariantRun,
    model: Any,
    tokenizer: Any,
    torch_module: Any,
    epoch: int,
    global_step: int,
    metrics: Mapping[str, int | float],
) -> Path:
    _assert_disk_capacity(prepared.config, "保存开发验证最佳模型前")
    root = prepared.output_dir / "model-selection"
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"epoch-{epoch:03d}-step-{global_step:08d}"
    if target.exists():
        raise R2DistilBertSidecarProbeError(f"选模目录已存在：{target}")
    temporary = root / f".{target.name}.{uuid.uuid4().hex}.partial"
    temporary.mkdir()
    try:
        _save_model_bundle(model, tokenizer, temporary, torch_module)
        artifacts = baseline._artifact_records(temporary)
        baseline._atomic_write_json(
            temporary / "selection_manifest.json",
            {
                "schema_version": SELECTION_SCHEMA_VERSION,
                "binding_sha256": prepared.binding_sha256,
                "selection_split": VALIDATION_SPLIT,
                "epoch": epoch,
                "global_step": global_step,
                "threshold": baseline.FIXED_THRESHOLD,
                "metrics": dict(metrics),
                "artifacts": artifacts,
            },
        )
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target


def _is_selection_directory(path: Path) -> bool:
    parts = path.name.split("-")
    return (
        len(parts) == 4
        and parts[0] == "epoch"
        and len(parts[1]) == 3
        and parts[1].isdigit()
        and parts[2] == "step"
        and len(parts[3]) == 8
        and parts[3].isdigit()
    )


def _is_controlled_partial_directory(path: Path, prefix: str) -> bool:
    parts = path.name.split(".")
    if len(parts) != 4 or parts[0] or parts[3] != "partial":
        return False
    identifier = parts[2]
    stem = parts[1]
    if prefix == "checkpoint-":
        controlled_stem = stem.startswith(prefix) and stem[len(prefix) :].isdigit()
    elif prefix == "epoch-":
        controlled_stem = _is_selection_directory(Path(stem))
    else:
        controlled_stem = False
    return (
        controlled_stem
        and len(identifier) == 32
        and all(character in "0123456789abcdef" for character in identifier)
    )


def _remove_owned_directory(path: Path, variant_root: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise R2DistilBertSidecarProbeError(f"拒绝删除非普通运行目录：{path}")
    resolved_root = variant_root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise R2DistilBertSidecarProbeError(
            f"拒绝删除当前组目录之外的路径：{path}"
        ) from error
    if resolved_path == resolved_root:
        raise R2DistilBertSidecarProbeError("拒绝删除当前组根目录")
    shutil.rmtree(path)


def _prune_selected_models(prepared: PreparedVariantRun, current: Path) -> None:
    selection_root = prepared.output_dir / "model-selection"
    if selection_root.is_symlink() or not selection_root.is_dir():
        raise R2DistilBertSidecarProbeError(f"选模根目录非法：{selection_root}")
    current_resolved = current.resolve()
    if current.is_symlink() or not current.is_dir():
        raise R2DistilBertSidecarProbeError(f"当前最佳模型目录非法：{current}")
    if current_resolved.parent != selection_root.resolve():
        raise R2DistilBertSidecarProbeError("当前最佳模型不在本组选模根目录内")
    selection_manifest = _read_json(
        current / "selection_manifest.json", "当前最佳模型清单"
    )
    if selection_manifest.get("binding_sha256") != prepared.binding_sha256:
        raise R2DistilBertSidecarProbeError("当前最佳模型与运行绑定不一致")
    for path in selection_root.iterdir():
        if path.resolve() == current_resolved:
            continue
        if _is_selection_directory(path):
            _remove_owned_directory(path, prepared.output_dir)


def _prune_checkpoints(output: Path, limit: int, current: Path) -> None:
    candidates: list[tuple[int, Path]] = []
    for path in output.iterdir():
        match = baseline.CHECKPOINT_PATTERN.fullmatch(path.name)
        if match is not None and path.is_dir():
            candidates.append((int(match.group(1)), path))
    for _, path in sorted(candidates)[: max(0, len(candidates) - limit)]:
        if path != current:
            _remove_owned_directory(path, output)


def _compact_successful_variant(
    prepared: PreparedVariantRun, state: ProbeRunStateController
) -> None:
    selected_model = state.state["best_model"]
    if not isinstance(selected_model, str):
        raise R2DistilBertSidecarProbeError("成功清理前缺少最佳模型路径")
    _prune_selected_models(prepared, Path(selected_model))
    for path in prepared.output_dir.iterdir():
        if (
            baseline.CHECKPOINT_PATTERN.fullmatch(path.name) is not None
            or _is_controlled_partial_directory(path, "checkpoint-")
        ):
            _remove_owned_directory(path, prepared.output_dir)
    selection_root = prepared.output_dir / "model-selection"
    for path in selection_root.iterdir():
        if _is_controlled_partial_directory(path, "epoch-"):
            _remove_owned_directory(path, prepared.output_dir)


def _save_checkpoint(
    *,
    prepared: PreparedVariantRun,
    state: ProbeRunStateController,
    model: Any,
    tokenizer: Any,
    optimizer: Any,
    scheduler: Any,
    scaler: Any,
    torch_module: Any,
    global_step: int,
    next_epoch: int,
    next_batch_index: int,
    parameter_contract: Mapping[str, object],
) -> Path:
    target = prepared.output_dir / f"checkpoint-{global_step}"
    if target.exists():
        manifest = _validate_checkpoint(target, prepared.binding_sha256)
        if manifest is not None:
            state.update(
                current_step=global_step,
                current_epoch=next_epoch,
                next_batch_index=next_batch_index,
                latest_checkpoint=str(target),
                failure=None,
            )
            _prune_checkpoints(
                prepared.output_dir,
                prepared.config.training.save_total_limit,
                target,
            )
            return target
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            raise R2DistilBertSidecarProbeError(f"同名检查点不可替换：{target}")
    _assert_disk_capacity(prepared.config, "保存训练检查点前")
    temporary = prepared.output_dir / f".checkpoint-{global_step}.{uuid.uuid4().hex}.partial"
    temporary.mkdir()
    try:
        _save_model_bundle(model, tokenizer, temporary, torch_module)
        torch_module.save(
            {
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "scaler": scaler.state_dict(),
                "rng": baseline._capture_rng_state(torch_module),
                "global_step": global_step,
                "next_epoch": next_epoch,
                "next_batch_index": next_batch_index,
            },
            temporary / "training_state.pt",
        )
        artifacts = baseline._artifact_records(temporary)
        baseline._atomic_write_json(
            temporary / "checkpoint_manifest.json",
            {
                "schema_version": CHECKPOINT_SCHEMA_VERSION,
                "binding_sha256": prepared.binding_sha256,
                "global_step": global_step,
                "next_epoch": next_epoch,
                "next_batch_index": next_batch_index,
                "best_model": state.state["best_model"],
                "best_epoch": state.state["best_epoch"],
                "best_macro_f1": state.state["best_macro_f1"],
                "parameter_contract": dict(parameter_contract),
                "created_at": baseline._utc_now(),
                "artifacts": artifacts,
            },
        )
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    if _validate_checkpoint(target, prepared.binding_sha256) is None:
        raise R2DistilBertSidecarProbeError(f"新检查点完整性复核失败：{target}")
    state.update(
        current_step=global_step,
        current_epoch=next_epoch,
        next_batch_index=next_batch_index,
        latest_checkpoint=str(target),
        failure=None,
    )
    _prune_checkpoints(
        prepared.output_dir,
        prepared.config.training.save_total_limit,
        target,
    )
    return target


def _restore_training_state(
    checkpoint: Path,
    *,
    optimizer: Any,
    scheduler: Any,
    scaler: Any,
    torch_module: Any,
) -> Mapping[str, object]:
    try:
        values = torch_module.load(
            checkpoint / "training_state.pt",
            map_location="cpu",
            weights_only=False,
        )
    except Exception as error:
        raise R2DistilBertSidecarProbeError(f"无法恢复训练状态：{checkpoint}") from error
    if not isinstance(values, dict):
        raise R2DistilBertSidecarProbeError("training_state.pt 顶层必须是对象")
    optimizer.load_state_dict(values["optimizer"])
    scheduler.load_state_dict(values["scheduler"])
    scaler.load_state_dict(values["scaler"])
    baseline._restore_rng_state(torch_module, _mapping(values["rng"], "检查点 rng"))
    return values


def _tracking_settings(config: ProbeConfig, variant: str) -> TrackingSettings:
    slug = VARIANT_SLUGS[variant]
    settings = replace(
        config.tracking,
        run_name=f"{config.tracking.run_name}-{slug}",
        description=f"{config.tracking.description}；实验组 {variant}",
        tags=(*config.tracking.tags, f"v-{slug}"),
    )
    if any(len(tag) > 20 for tag in settings.tags):
        raise R2DistilBertSidecarProbeError("动态 SwanLab 标签超过 20 个字符")
    return settings


@contextmanager
def _swanlab_attempt(
    prepared: PreparedVariantRun,
    state: ProbeRunStateController,
    tracking_config: Mapping[str, object],
) -> Iterator[baseline.ScalarLogger]:
    try:
        import swanlab
    except ImportError as error:
        raise baseline.UnsupportedRuntimeError("缺少 SwanLab 在线跟踪依赖") from error
    settings = _tracking_settings(prepared.config, prepared.inputs.variant)
    attempts = [dict(item) for item in state.state["swanlab_attempts"]]
    previous_failure = state.state["failure"]
    if previous_failure is not None and attempts:
        attempts[-1].setdefault("failure", previous_failure)
    attempt_number = len(attempts) + 1
    attempt_dir = prepared.output_dir / "swanlog" / f"attempt-{attempt_number}"
    run = swanlab.init(
        project=settings.project,
        workspace=settings.workspace,
        name=f"{settings.run_name}-attempt-{attempt_number}",
        description=settings.description,
        config=dict(tracking_config),
        mode=settings.mode,
        tags=list(settings.tags),
        group=prepared.config.tracking.run_name,
        job_type="r2-distilbert-sidecar",
        log_dir=str(attempt_dir),
    )
    attempt = {
        "attempt": attempt_number,
        "run_id": str(run.id),
        "status": "running",
        "started_at": baseline._utc_now(),
        "finished_at": None,
        "resumed_from_failure": previous_failure,
        "resume_checkpoint": (
            str(prepared.resume_checkpoint)
            if prepared.resume_checkpoint is not None
            else None
        ),
    }
    attempts.append(attempt)
    state.update(swanlab_attempts=attempts)
    logger = baseline.ScalarLogger(
        swanlab,
        prepared.output_dir / "swanlab_metrics.jsonl",
    )
    try:
        yield logger
    except BaseException as error:
        swanlab.finish(state="crashed", error=str(error))
        attempt.update(
            {
                "status": "crashed",
                "finished_at": baseline._utc_now(),
                "failure": f"{type(error).__name__}: {error}",
            }
        )
        attempts[-1] = attempt
        state.update(swanlab_attempts=attempts)
        raise
    else:
        swanlab.finish()
        attempt.update({"status": "finished", "finished_at": baseline._utc_now()})
        attempts[-1] = attempt
        state.update(swanlab_attempts=attempts)


def _train_variant(
    *,
    prepared: PreparedVariantRun,
    modules: baseline.RuntimeModules,
    runtime: baseline.RuntimeSelection,
    state: ProbeRunStateController,
    logger: baseline.ScalarLogger,
) -> tuple[Path, dict[str, object], dict[str, object]]:
    config = prepared.config
    torch_module = modules.torch
    baseline._set_reproducible_seed(torch_module, config.run.seed)
    source: str | Path = prepared.resume_checkpoint or config.model.source
    tokenizer, model = _build_sidecar_model(modules, config, runtime, source)
    parameter_contract = _parameter_contract(model)
    initial_head_sha256 = (
        _head_initialization_sha256(model)
        if prepared.resume_checkpoint is None
        else None
    )
    batches_per_epoch = math.ceil(
        len(prepared.inputs.train) / config.training.per_device_train_batch_size
    )
    optimizer_steps_per_epoch = math.ceil(
        batches_per_epoch / config.training.gradient_accumulation_steps
    )
    total_optimizer_steps = optimizer_steps_per_epoch * config.training.num_train_epochs
    if total_optimizer_steps != FIXED_TOTAL_OPTIMIZER_STEPS:
        raise R2DistilBertSidecarProbeError(
            f"优化步预算必须固定为 {FIXED_TOTAL_OPTIMIZER_STEPS}，实际为 {total_optimizer_steps}"
        )
    warmup_steps = int(total_optimizer_steps * config.training.warmup_ratio)
    optimizer = torch_module.optim.AdamW(
        model.parameters(),
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )
    optimizer_contract = _optimizer_contract(optimizer, model, config)
    _assert_shared_structure(
        prepared,
        parameter_contract,
        optimizer_contract,
        initial_head_sha256,
    )
    scheduler = torch_module.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda=baseline._linear_schedule_lambda(
            total_optimizer_steps,
            warmup_steps,
        ),
    )
    scaler = baseline._new_grad_scaler(torch_module, runtime.use_grad_scaler)
    start_epoch = 0
    start_batch = 0
    global_step = 0
    if prepared.resume_checkpoint is not None:
        restored = _restore_training_state(
            prepared.resume_checkpoint,
            optimizer=optimizer,
            scheduler=scheduler,
            scaler=scaler,
            torch_module=torch_module,
        )
        start_epoch = int(restored["next_epoch"])
        start_batch = int(restored["next_batch_index"])
        global_step = int(restored["global_step"])

    state.transition("running", failure=None)
    training_started = time.perf_counter()
    optimizer.zero_grad(set_to_none=True)
    for epoch_index in range(start_epoch, config.training.num_train_epochs):
        loader = _data_loader(
            split=prepared.inputs.train,
            tokenizer=tokenizer,
            batch_size=config.training.per_device_train_batch_size,
            max_length=config.model.max_length,
            torch_module=torch_module,
            shuffle=True,
            seed=config.run.seed + epoch_index,
            num_workers=config.training.num_workers,
        )
        model.train()
        group_loss = 0.0
        group_batches = 0
        for batch_index, batch in enumerate(loader):
            if epoch_index == start_epoch and batch_index < start_batch:
                continue
            batch = {key: value.to(runtime.device) for key, value in batch.items()}
            group_start = (
                batch_index // config.training.gradient_accumulation_steps
            ) * config.training.gradient_accumulation_steps
            group_size = min(
                config.training.gradient_accumulation_steps,
                batches_per_epoch - group_start,
            )
            with baseline._autocast(torch_module, runtime):
                output = model(**batch)
                loss = output.loss
            if loss is None or not bool(torch_module.isfinite(loss).item()):
                raise R2DistilBertSidecarProbeError("训练损失不是有限数")
            group_loss += float(loss.detach().float().item())
            group_batches += 1
            scaled_loss = loss / group_size
            if runtime.use_grad_scaler:
                scaler.scale(scaled_loss).backward()
            else:
                scaled_loss.backward()
            is_group_end = (
                (batch_index + 1) % config.training.gradient_accumulation_steps == 0
                or batch_index + 1 == batches_per_epoch
            )
            if not is_group_end:
                continue
            current_lr = float(optimizer.param_groups[0]["lr"])
            if runtime.use_grad_scaler:
                scaler.unscale_(optimizer)
            torch_module.nn.utils.clip_grad_norm_(
                model.parameters(), config.training.max_grad_norm
            )
            if runtime.use_grad_scaler:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            global_step += 1
            logger.log(
                baseline.build_training_step_scalars(
                    loss=group_loss / group_batches,
                    learning_rate=current_lr,
                    epoch=epoch_index + 1,
                    optimizer_step=global_step,
                ),
                step=global_step,
                event="optimizer_step",
            )
            group_loss = 0.0
            group_batches = 0
            is_epoch_end = batch_index + 1 == batches_per_epoch
            if global_step % config.training.save_steps == 0 and not is_epoch_end:
                _save_checkpoint(
                    prepared=prepared,
                    state=state,
                    model=model,
                    tokenizer=tokenizer,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    scaler=scaler,
                    torch_module=torch_module,
                    global_step=global_step,
                    next_epoch=epoch_index,
                    next_batch_index=batch_index + 1,
                    parameter_contract=parameter_contract,
                )

        development_metrics, _ = _evaluate_split(
            model=model,
            tokenizer=tokenizer,
            split=prepared.inputs.validation,
            config=config,
            runtime=runtime,
            torch_module=torch_module,
        )
        logger.log(
            baseline.build_development_scalars(
                development_metrics,
                epoch=epoch_index + 1,
            ),
            step=global_step,
            event="development_evaluation",
        )
        selected_path = state.state["best_model"]
        best = state.state["best_macro_f1"]
        if best is None or float(development_metrics["macro_f1"]) > float(best):
            selected = _save_selected_model(
                prepared=prepared,
                model=model,
                tokenizer=tokenizer,
                torch_module=torch_module,
                epoch=epoch_index + 1,
                global_step=global_step,
                metrics=development_metrics,
            )
            selected_path = str(selected)
            state.update(
                best_model=selected_path,
                best_epoch=epoch_index + 1,
                best_macro_f1=float(development_metrics["macro_f1"]),
            )
            _prune_selected_models(prepared, selected)
        baseline._append_jsonl(
            prepared.output_dir / "development_history.jsonl",
            {
                "epoch": epoch_index + 1,
                "global_step": global_step,
                "selection_split": VALIDATION_SPLIT,
                "selected_model": selected_path,
                "metrics": development_metrics,
            },
        )
        _save_checkpoint(
            prepared=prepared,
            state=state,
            model=model,
            tokenizer=tokenizer,
            optimizer=optimizer,
            scheduler=scheduler,
            scaler=scaler,
            torch_module=torch_module,
            global_step=global_step,
            next_epoch=epoch_index + 1,
            next_batch_index=0,
            parameter_contract=parameter_contract,
        )
        start_batch = 0

    if global_step != FIXED_TOTAL_OPTIMIZER_STEPS:
        raise R2DistilBertSidecarProbeError(
            f"训练结束步数不是固定 {FIXED_TOTAL_OPTIMIZER_STEPS}：{global_step}"
        )
    selected_model = state.state["best_model"]
    if not isinstance(selected_model, str) or not Path(selected_model).is_dir():
        raise R2DistilBertSidecarProbeError("开发验证选模后缺少合法模型")
    training_summary = {
        "training_seconds": time.perf_counter() - training_started,
        "global_step": global_step,
        "total_optimizer_steps": total_optimizer_steps,
        "best_model": selected_model,
        "best_epoch": state.state["best_epoch"],
        "best_macro_f1": state.state["best_macro_f1"],
    }
    model.to("cpu")
    del model
    gc.collect()
    if runtime.device == "cuda":
        torch_module.cuda.empty_cache()
    return Path(selected_model), training_summary, parameter_contract


def _artifact_record(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise R2DistilBertSidecarProbeError(f"最终制品不是普通文件：{path}")
    return {
        "size_bytes": path.stat().st_size,
        "sha256": baseline.file_sha256(path),
    }


def _validate_artifact_records(
    root: Path, records: Mapping[str, object], description: str
) -> None:
    resolved_root = root.resolve()
    for relative, raw_record in records.items():
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise R2DistilBertSidecarProbeError(f"{description}路径非法：{relative}")
        path = (root / relative_path).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError as error:
            raise R2DistilBertSidecarProbeError(
                f"{description}路径越出当前组：{relative}"
            ) from error
        record = _mapping(raw_record, f"{description} {relative}")
        if _artifact_record(path) != {
            "size_bytes": _integer(record.get("size_bytes"), f"{relative} 大小"),
            "sha256": _expected_sha256(record.get("sha256"), f"{relative} 哈希"),
        }:
            raise R2DistilBertSidecarProbeError(f"{description}校验失败：{relative}")


def _best_model_path(prepared: PreparedVariantRun, raw_path: object) -> Path:
    relative = Path(_nonempty_string(raw_path, "最佳模型相对路径"))
    if relative.is_absolute() or ".." in relative.parts:
        raise R2DistilBertSidecarProbeError("最佳模型路径必须是当前组内相对路径")
    candidate = prepared.output_dir / relative
    if candidate.is_symlink():
        raise R2DistilBertSidecarProbeError("最佳模型目录不得为符号链接")
    path = candidate.resolve()
    if path.parent != (prepared.output_dir / "model-selection").resolve():
        raise R2DistilBertSidecarProbeError("最佳模型路径不在本组选模根目录内")
    if not path.is_dir() or not _is_selection_directory(path):
        raise R2DistilBertSidecarProbeError("最佳模型目录非法")
    return path


def _write_finalization_receipt(
    prepared: PreparedVariantRun,
    state: ProbeRunStateController,
    parameter_contract: Mapping[str, object],
) -> Mapping[str, object]:
    path = prepared.output_dir / "finalization_receipt.json"
    if path.exists():
        receipt = _validate_finalization_receipt(
            prepared.output_dir, prepared.binding_sha256, state.state["run_id"]
        )
        if receipt.get("parameter_contract") != dict(parameter_contract):
            raise R2DistilBertSidecarProbeError("既有收尾收据的参数合同不一致")
        return MappingProxyType(receipt)
    selected_raw = state.state["best_model"]
    if not isinstance(selected_raw, str):
        raise R2DistilBertSidecarProbeError("收尾前缺少最佳模型")
    selected = Path(selected_raw).resolve()
    try:
        selected_relative = selected.relative_to(prepared.output_dir.resolve())
    except ValueError as error:
        raise R2DistilBertSidecarProbeError("最佳模型越出当前组目录") from error
    _best_model_path(prepared, selected_relative.as_posix())
    completion_paths = (
        "summary.json",
        "cost.json",
        "metrics/validation_metrics.json",
        "predictions/validation_predictions.jsonl",
        "development_history.jsonl",
    )
    completion_artifacts = {
        relative: _artifact_record(prepared.output_dir / relative)
        for relative in completion_paths
    }
    receipt = {
        "schema_version": FINALIZATION_SCHEMA_VERSION,
        "status": "finalizing",
        "binding_sha256": prepared.binding_sha256,
        "run_id": state.state["run_id"],
        "best_model": selected_relative.as_posix(),
        "parameter_contract": dict(parameter_contract),
        "completion_artifacts": completion_artifacts,
        "created_at": baseline._utc_now(),
    }
    baseline._atomic_write_json(path, receipt)
    return MappingProxyType(
        _validate_finalization_receipt(
            prepared.output_dir, prepared.binding_sha256, state.state["run_id"]
        )
    )


def _validate_finalization_receipt(
    output: Path, binding_sha256: str, run_id: object
) -> dict[str, object]:
    receipt = _read_json(output / "finalization_receipt.json", "收尾收据")
    if (
        receipt.get("schema_version") != FINALIZATION_SCHEMA_VERSION
        or receipt.get("status") != "finalizing"
        or receipt.get("binding_sha256") != binding_sha256
        or receipt.get("run_id") != run_id
    ):
        raise R2DistilBertSidecarProbeError("收尾收据与当前运行不一致")
    _mapping(receipt.get("parameter_contract"), "收尾收据 parameter_contract")
    completion = _mapping(
        receipt.get("completion_artifacts"), "收尾收据 completion_artifacts"
    )
    _validate_artifact_records(output, completion, "收尾完成制品")
    relative = Path(_nonempty_string(receipt.get("best_model"), "收尾收据 best_model"))
    if relative.is_absolute() or ".." in relative.parts:
        raise R2DistilBertSidecarProbeError("收尾收据最佳模型路径非法")
    candidate = output / relative
    if candidate.is_symlink():
        raise R2DistilBertSidecarProbeError("收尾收据最佳模型不得为符号链接")
    selected = candidate.resolve()
    if selected.parent != (output / "model-selection").resolve():
        raise R2DistilBertSidecarProbeError("收尾收据最佳模型越出选模根目录")
    selection = _read_json(selected / "selection_manifest.json", "最佳模型选模清单")
    if selection.get("binding_sha256") != binding_sha256:
        raise R2DistilBertSidecarProbeError("最佳模型选模清单与运行绑定不一致")
    return receipt


def _write_best_model_receipt(
    prepared: PreparedVariantRun, finalization: Mapping[str, object]
) -> Mapping[str, object]:
    selected = _best_model_path(prepared, finalization["best_model"])
    records = baseline._artifact_records(selected)
    receipt = {
        "schema_version": BEST_MODEL_RECEIPT_SCHEMA_VERSION,
        "binding_sha256": prepared.binding_sha256,
        "best_model": str(finalization["best_model"]),
        "selection_manifest_sha256": baseline.file_sha256(
            selected / "selection_manifest.json"
        ),
        "artifact_count": len(records),
        "artifacts": records,
    }
    path = prepared.output_dir / "best_model_receipt.json"
    baseline._atomic_write_json(path, receipt)
    stored = _read_json(path, "最佳模型收据")
    if stored != receipt:
        raise R2DistilBertSidecarProbeError("最佳模型收据原子写回不一致")
    _validate_artifact_records(selected, records, "最佳模型制品")
    return MappingProxyType(stored)


def _is_transient_artifact(prepared: PreparedVariantRun, path: Path, best: Path) -> bool:
    relative = path.relative_to(prepared.output_dir)
    first = prepared.output_dir / relative.parts[0]
    if baseline.CHECKPOINT_PATTERN.fullmatch(relative.parts[0]) is not None:
        return True
    if _is_controlled_partial_directory(first, "checkpoint-"):
        return True
    if len(relative.parts) >= 2 and relative.parts[0] == "model-selection":
        candidate = prepared.output_dir / "model-selection" / relative.parts[1]
        if _is_controlled_partial_directory(candidate, "epoch-"):
            return True
        if _is_selection_directory(candidate) and candidate.resolve() != best.resolve():
            return True
    return False


def _persistent_artifact_records(
    prepared: PreparedVariantRun, best: Path
) -> dict[str, object]:
    records: dict[str, object] = {}
    excluded = {"artifact_manifest.json", "run_state.json"}
    for path in sorted(prepared.output_dir.rglob("*")):
        if path.is_symlink():
            raise R2DistilBertSidecarProbeError(f"最终制品路径不得为符号链接：{path}")
        if not path.is_file():
            continue
        relative = path.relative_to(prepared.output_dir).as_posix()
        if relative in excluded or _is_transient_artifact(prepared, path, best):
            continue
        records[relative] = _artifact_record(path)
    return records


def _write_artifact_manifest(
    prepared: PreparedVariantRun,
    state: ProbeRunStateController,
    parameter_contract: Mapping[str, object],
    best: Path,
) -> Mapping[str, object]:
    path = prepared.output_dir / "artifact_manifest.json"
    records = _persistent_artifact_records(prepared, best)
    manifest = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "status": "finished",
        "stage": EXPECTED_STAGE,
        "protocol_status": EXPECTED_PROTOCOL_STATUS,
        "seed": prepared.config.run.seed,
        "variant": prepared.inputs.variant,
        "binding_sha256": prepared.binding_sha256,
        "run_id": state.state["run_id"],
        "selection_split": VALIDATION_SPLIT,
        "final_test_visible": False,
        "parameter_contract": dict(parameter_contract),
        "artifact_count": len(records),
        "artifacts": records,
    }
    baseline._atomic_write_json(path, manifest)
    stored = _read_json(path, "最终制品清单")
    if stored != manifest:
        raise R2DistilBertSidecarProbeError("最终制品清单原子写回不一致")
    _validate_artifact_records(prepared.output_dir, records, "最终制品")
    return MappingProxyType(stored)


def _finalize_variant(
    prepared: PreparedVariantRun,
    state: ProbeRunStateController,
    parameter_contract: Mapping[str, object] | None,
) -> Mapping[str, object]:
    if parameter_contract is None:
        finalization = _validate_finalization_receipt(
            prepared.output_dir, prepared.binding_sha256, state.state["run_id"]
        )
        parameter_contract = _mapping(
            finalization["parameter_contract"], "收尾收据 parameter_contract"
        )
    else:
        finalization = _write_finalization_receipt(
            prepared, state, parameter_contract
        )
    if state.status != "finalizing":
        state.transition("finalizing", failure=None)
    _write_best_model_receipt(prepared, finalization)
    best = _best_model_path(prepared, finalization["best_model"])
    manifest = _write_artifact_manifest(
        prepared, state, parameter_contract, best
    )
    _compact_successful_variant(prepared, state)
    _validate_artifact_records(
        prepared.output_dir,
        _mapping(manifest["artifacts"], "最终制品清单 artifacts"),
        "清理后最终制品",
    )
    state.transition("finished", latest_checkpoint=None, failure=None)
    return manifest


def execute_variant(
    prepared: PreparedVariantRun,
    *,
    modules: baseline.RuntimeModules,
    runtime: baseline.RuntimeSelection,
) -> Mapping[str, object]:
    state = ProbeRunStateController(prepared.state_path)
    config = prepared.config
    output = prepared.output_dir
    if prepared.resume_finalization:
        try:
            return _finalize_variant(prepared, state, None)
        except BaseException as error:
            state.update(failure=f"{type(error).__name__}: {error}")
            raise
    if runtime.device == "cuda":
        modules.torch.cuda.reset_peak_memory_stats()
    environment = baseline._runtime_environment(modules.torch, runtime, config)
    baseline._atomic_write_json(output / "environment.json", environment)
    tracking_config = {
        **config_snapshot(config),
        "variant": prepared.inputs.variant,
        "run_binding_sha256": prepared.binding_sha256,
        "runtime": environment,
    }
    total_started = time.perf_counter()
    try:
        with (
            baseline._capture_console(output / "console.log"),
            _swanlab_attempt(prepared, state, tracking_config) as logger,
        ):
            selected_model, training_summary, parameter_contract = _train_variant(
                prepared=prepared,
                modules=modules,
                runtime=runtime,
                state=state,
                logger=logger,
            )
            tokenizer, model = _build_sidecar_model(
                modules,
                config,
                runtime,
                selected_model,
            )
            final_metrics, predictions = _evaluate_split(
                model=model,
                tokenizer=tokenizer,
                split=prepared.inputs.validation,
                config=config,
                runtime=runtime,
                torch_module=modules.torch,
            )
            baseline._atomic_write_jsonl(
                output / "predictions" / "validation_predictions.jsonl",
                predictions,
            )
            baseline._atomic_write_json(
                output / "metrics" / "validation_metrics.json",
                final_metrics,
            )
            logger.log(
                {f"final/validation/{key}": value for key, value in final_metrics.items()},
                step=int(state.state["current_step"]),
                event="final_validation_evaluation",
            )
            summary = {
                "schema_version": "flow_probe_r2_distilbert_sidecar_variant_summary_v1",
                "stage": EXPECTED_STAGE,
                "status": EXPECTED_PROTOCOL_STATUS,
                "seed": config.run.seed,
                "variant": prepared.inputs.variant,
                "model_id": baseline.FIXED_MODEL_ID,
                "sample_counts": {
                    TRAIN_SPLIT: len(prepared.inputs.train),
                    VALIDATION_SPLIT: len(prepared.inputs.validation),
                },
                "parameter_contract": dict(parameter_contract),
                "training": training_summary,
                "validation_metrics": final_metrics,
                "final_test_visible": False,
            }
            baseline._atomic_write_json(output / "summary.json", summary)
            baseline._atomic_write_json(
                output / "cost.json",
                {
                    "schema_version": "flow_probe_r2_distilbert_sidecar_cost_v1",
                    "total_seconds": time.perf_counter() - total_started,
                    "training_seconds": training_summary["training_seconds"],
                    "peak_process_rss_bytes": baseline._peak_process_rss_bytes(),
                    "peak_gpu_memory_allocated_bytes": int(
                        modules.torch.cuda.max_memory_allocated()
                    ),
                    "peak_gpu_memory_reserved_bytes": int(
                        modules.torch.cuda.max_memory_reserved()
                    ),
                    "runtime": environment,
                },
            )
        return _finalize_variant(prepared, state, parameter_contract)
    except KeyboardInterrupt as error:
        if state.status == "finalizing":
            state.update(failure=f"{type(error).__name__}: {error}")
        elif state.status not in {"interrupted", "finished"}:
            state.mark_interrupted(error)
        raise
    except Exception as error:
        if state.status == "finalizing":
            state.update(failure=f"{type(error).__name__}: {error}")
        elif state.status not in {"failed", "finished"}:
            state.mark_failed(error)
        raise


def _completed_variant_summary(
    config: ProbeConfig,
    prepared_inputs: PreparedProbeInputs,
    model_binding: Mapping[str, object],
    variant: str,
) -> dict[str, object] | None:
    output = _variant_output(config, variant)
    state_path = output / "run_state.json"
    if not state_path.is_file():
        return None
    state = _validate_run_state(_read_json(state_path, "已有运行状态"), state_path)
    if state["status"] != "finished":
        return None
    expected_binding = _build_run_binding(
        config,
        prepared_inputs,
        prepared_inputs.variants[variant],
        model_binding,
    )
    binding_sha256 = baseline._canonical_sha256(expected_binding)
    if _read_json(output / "run_binding.json", "已有运行绑定") != expected_binding:
        raise R2DistilBertSidecarProbeError(f"{variant} 已完成运行绑定不一致")
    manifest = _read_json(output / "artifact_manifest.json", "已完成制品清单")
    if (
        manifest.get("schema_version") != ARTIFACT_SCHEMA_VERSION
        or manifest.get("status") != "finished"
        or manifest.get("binding_sha256") != binding_sha256
    ):
        raise R2DistilBertSidecarProbeError(f"{variant} 已完成制品清单非法")
    records = _mapping(manifest.get("artifacts"), "已完成制品清单.artifacts")
    if len(records) != manifest.get("artifact_count"):
        raise R2DistilBertSidecarProbeError(f"{variant} 制品数量不一致")
    for relative, raw_record in records.items():
        record = _mapping(raw_record, f"{variant} 制品 {relative}")
        path = (output / relative).resolve()
        path.relative_to(output.resolve())
        if (
            not path.is_file()
            or path.stat().st_size != _integer(record.get("size_bytes"), f"{relative} 大小")
            or baseline.file_sha256(path)
            != _expected_sha256(record.get("sha256"), f"{relative} 哈希")
        ):
            raise R2DistilBertSidecarProbeError(f"{variant} 已完成制品损坏：{relative}")
    return _read_json(output / "summary.json", f"{variant} 汇总")


def _write_seed_summary(config: ProbeConfig, summaries: Mapping[str, Mapping[str, object]]) -> None:
    if tuple(summaries) != VARIANTS:
        raise R2DistilBertSidecarProbeError("种子汇总必须精确包含四个冻结组")
    parameter_contracts = [summary.get("parameter_contract") for summary in summaries.values()]
    if any(contract != parameter_contracts[0] for contract in parameter_contracts[1:]):
        raise R2DistilBertSidecarProbeError("四组最终参数合同不一致")
    if any(
        _mapping(summary.get("training"), "组训练汇总").get("global_step")
        != FIXED_TOTAL_OPTIMIZER_STEPS
        for summary in summaries.values()
    ):
        raise R2DistilBertSidecarProbeError("四组并非都完成固定优化步预算")
    baseline._atomic_write_json(
        config.run.output_dir / "seed_summary.json",
        {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "stage": EXPECTED_STAGE,
            "status": EXPECTED_PROTOCOL_STATUS,
            "seed": config.run.seed,
            "variant_order": list(VARIANTS),
            "parameter_contract": parameter_contracts[0],
            "same_model_structure": True,
            "same_optimizer": True,
            "same_samples_and_budget": True,
            "final_test_visible": False,
            "variants": {
                variant: {
                    "training": summary["training"],
                    "validation_metrics": summary["validation_metrics"],
                }
                for variant, summary in summaries.items()
            },
        },
    )


def _execute_probe_serial(
    config: ProbeConfig, prepared_inputs: PreparedProbeInputs
) -> None:
    _assert_disk_capacity(config, "启动串行种子探针前")
    model_binding = baseline.validate_model_source(config.model)
    if model_binding.get("local_files_verified") is not True:
        raise R2DistilBertSidecarProbeError("探针禁止使用未核验或需下载的模型来源")
    modules = baseline.load_runtime_modules()
    runtime = baseline.resolve_runtime(modules.torch, config.model, formal_training=True)
    summaries: dict[str, Mapping[str, object]] = {}
    for variant in VARIANTS:
        completed = _completed_variant_summary(
            config,
            prepared_inputs,
            model_binding,
            variant,
        )
        if completed is not None:
            summaries[variant] = completed
            continue
        _assert_disk_capacity(config, f"启动 {variant} 组前")
        prepared = prepare_variant_run(
            config,
            prepared_inputs,
            model_binding,
            variant,
        )
        execute_variant(prepared, modules=modules, runtime=runtime)
        completed = _completed_variant_summary(
            config,
            prepared_inputs,
            model_binding,
            variant,
        )
        if completed is None:
            raise R2DistilBertSidecarProbeError(f"{variant} 结束后未形成完整制品")
        summaries[variant] = completed
    _write_seed_summary(config, summaries)


def execute_probe(config: ProbeConfig, prepared_inputs: PreparedProbeInputs) -> None:
    with _serial_seed_execution(config):
        _execute_probe_serial(config, prepared_inputs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="运行 R2 物理旁路 DistilBERT 四组结构适配探针"
    )
    parser.add_argument("--config", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        prepared_inputs = prepare_probe_inputs(config)
        execute_probe(config, prepared_inputs)
        print(
            json.dumps(
                {
                    "status": "finished",
                    "seed": config.run.seed,
                    "variants": list(VARIANTS),
                    "output_dir": str(config.run.output_dir),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    except baseline.UnsupportedRuntimeError as error:
        print(
            json.dumps(
                {"status": "unsupported", "reason": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=os.sys.stderr,
        )
        return 2
    except KeyboardInterrupt:
        print(
            json.dumps(
                {"status": "interrupted", "reason": "KeyboardInterrupt"},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=os.sys.stderr,
        )
        return 130
    except R2DistilBertSidecarProbeError as error:
        print(
            json.dumps(
                {"status": "failed", "reason": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=os.sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
