"""共享 B0 冻结文本视图上的 DistilBERT 判别式二分类基线。"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import random
import re
import resource
import shutil
import sys
import time
import uuid
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, nullcontext, redirect_stderr, redirect_stdout
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, TextIO

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from pandas.api.types import is_bool_dtype, is_integer_dtype

from flow_probe.shared_b0_view import ARTIFACT_SCHEMA_VERSION, file_sha256
from flow_probe.tracking import TrackingSettings


CONFIG_SCHEMA_VERSION = "flow_probe_shared_b0_distilbert_config_v1"
INPUT_BINDING_SCHEMA_VERSION = "flow_probe_shared_b0_distilbert_input_v1"
MODEL_BINDING_SCHEMA_VERSION = "flow_probe_distilbert_model_binding_v1"
RUN_BINDING_SCHEMA_VERSION = "flow_probe_shared_b0_distilbert_run_binding_v1"
RUN_STATE_SCHEMA_VERSION = "flow_probe_shared_b0_distilbert_run_state_v1"
CHECKPOINT_SCHEMA_VERSION = "flow_probe_shared_b0_distilbert_checkpoint_v1"
ARTIFACT_MANIFEST_SCHEMA_VERSION = "flow_probe_shared_b0_distilbert_artifacts_v1"
SMOKE_ARTIFACT_MANIFEST_SCHEMA_VERSION = "flow_probe_shared_b0_distilbert_smoke16_artifacts_v1"

FIXED_MODEL_ID = "distilbert/distilbert-base-multilingual-cased"
FIXED_LABEL_MAPPING = MappingProxyType({0: "benign", 1: "malicious"})
INPUT_COLUMNS = ("sample_id", "stable_order", "text", "label")
EXPECTED_STAGE = "theory_selection"
EXPECTED_PROTOCOL_STATUS = "review_pending"
EXPECTED_DATASET_NAME = "dataset-v1-shared-b0"
SELECTION_SPLIT = "genis"
EXTERNAL_EVALUATION_SPLIT = "tqhc2"
FIXED_THRESHOLD = 0.5
SMOKE_SAMPLE_COUNT = 16
REQUIRED_SPLITS = MappingProxyType(
    {
        "train": "candidate/bert_train.parquet",
        SELECTION_SPLIT: "validation/genis_bert.parquet",
        EXTERNAL_EVALUATION_SPLIT: "validation/tqhc2_bert.parquet",
    }
)
SMOKE_REQUIRED_SPLITS = MappingProxyType(
    {
        "train": REQUIRED_SPLITS["train"],
        SELECTION_SPLIT: REQUIRED_SPLITS[SELECTION_SPLIT],
    }
)
RUN_STATUSES = frozenset({"prepared", "running", "interrupted", "failed", "finished"})
RESUMABLE_STATUSES = frozenset({"prepared", "running", "interrupted"})
TQHC2_EVALUATION_STATUSES = frozenset({"not_started", "running", "finished"})
CHECKPOINT_PATTERN = re.compile(r"checkpoint-(\d+)")
MODEL_WEIGHT_PATTERNS = ("*.safetensors", "pytorch_model*.bin")
MODEL_FINGERPRINT = MappingProxyType(
    {
        "model_type": "distilbert",
        "vocab_size": 119547,
        "dim": 768,
        "hidden_dim": 3072,
        "n_layers": 6,
        "n_heads": 12,
        "max_position_embeddings": 512,
    }
)


class SharedB0DistilBertError(ValueError):
    """共享 B0 DistilBERT 配置、输入或运行合同不合法。"""


class UnsupportedRuntimeError(SharedB0DistilBertError):
    """运行环境可完成预检，但不支持正式训练档位。"""


@dataclass(frozen=True)
class DatasetSettings:
    root: Path


@dataclass(frozen=True)
class ModelSettings:
    identifier: str
    source: str
    max_length: int
    device: str
    precision: str


@dataclass(frozen=True)
class TrainingSettings:
    per_device_train_batch_size: int
    per_device_eval_batch_size: int
    gradient_accumulation_steps: int
    learning_rate: float
    weight_decay: float
    num_train_epochs: int
    warmup_ratio: float
    max_grad_norm: float
    save_steps: int
    save_total_limit: int
    num_workers: int
    resume_from_checkpoint: str

    @property
    def effective_batch_size(self) -> int:
        return self.per_device_train_batch_size * self.gradient_accumulation_steps


@dataclass(frozen=True)
class EvaluationSettings:
    threshold: float
    calibration_bins: int


@dataclass(frozen=True)
class RunSettings:
    output_dir: Path
    seed: int
    stage: str
    status: str


@dataclass(frozen=True)
class DistilBertBaselineConfig:
    dataset: DatasetSettings
    model: ModelSettings
    training: TrainingSettings
    evaluation: EvaluationSettings
    run: RunSettings
    tracking: TrackingSettings
    config_path: Path


@dataclass(frozen=True)
class FrozenTextSplit:
    name: str
    relative_path: str
    sample_ids: tuple[str, ...]
    stable_orders: tuple[int, ...]
    texts: tuple[str, ...]
    labels: tuple[int, ...]
    sha256: str
    size_bytes: int
    sample_order_sha256: str

    def __len__(self) -> int:
        return len(self.sample_ids)


@dataclass(frozen=True)
class PreparedFrozenInputs:
    root: Path
    splits: Mapping[str, FrozenTextSplit]
    binding: Mapping[str, object]
    binding_sha256: str


@dataclass(frozen=True)
class PreparedRun:
    config: DistilBertBaselineConfig
    inputs: PreparedFrozenInputs
    model_binding: Mapping[str, object]
    run_binding: Mapping[str, object]
    binding_sha256: str
    state_path: Path
    resume_checkpoint: Path | None


@dataclass(frozen=True)
class RuntimeSelection:
    device: str
    precision: str
    torch_dtype: object | None
    use_grad_scaler: bool


@dataclass(frozen=True)
class RuntimeModules:
    torch: Any
    auto_tokenizer: Any
    auto_model: Any


@dataclass(frozen=True)
class EvaluationResult:
    metrics: Mapping[str, int | float]
    predictions: tuple[Mapping[str, object], ...]


class _TeeStream:
    def __init__(self, terminal: TextIO, log_file: TextIO) -> None:
        self.terminal = terminal
        self.log_file = log_file

    @property
    def encoding(self) -> str | None:
        return self.terminal.encoding

    def write(self, text: str) -> int:
        self.terminal.write(text)
        self.log_file.write(text)
        return len(text)

    def flush(self) -> None:
        self.terminal.flush()
        self.log_file.flush()

    def isatty(self) -> bool:
        return self.terminal.isatty()


@contextmanager
def _capture_console(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with (
        path.open("a", encoding="utf-8") as log_file,
        redirect_stdout(_TeeStream(sys.stdout, log_file)),
        redirect_stderr(_TeeStream(sys.stderr, log_file)),
    ):
        yield


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SharedB0DistilBertError(f"{description}必须是对象")
    return value


def _exact_keys(
    value: Mapping[str, object],
    *,
    required: set[str],
    optional: set[str] | None = None,
    description: str,
) -> None:
    allowed = required | (optional or set())
    missing = sorted(required.difference(value))
    unexpected = sorted(set(value).difference(allowed))
    details = []
    if missing:
        details.append(f"缺少字段：{', '.join(missing)}")
    if unexpected:
        details.append(f"额外字段：{', '.join(unexpected)}")
    if details:
        raise SharedB0DistilBertError(f"{description}字段不符合合同：{'；'.join(details)}")


def _nonempty_string(value: object, description: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise SharedB0DistilBertError(f"{description}必须是无首尾空白的非空字符串")
    return value


def _integer(value: object, description: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise SharedB0DistilBertError(f"{description}必须是不小于 {minimum} 的整数")
    return value


def _number(
    value: object,
    description: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SharedB0DistilBertError(f"{description}必须是有限数")
    result = float(value)
    if not math.isfinite(result):
        raise SharedB0DistilBertError(f"{description}必须是有限数")
    if minimum is not None and result < minimum:
        raise SharedB0DistilBertError(f"{description}不得小于 {minimum}")
    if maximum is not None and result > maximum:
        raise SharedB0DistilBertError(f"{description}不得大于 {maximum}")
    return result


def _resolve_path(value: object, project_root: Path, description: str) -> Path:
    raw = _nonempty_string(value, description)
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else project_root / path).resolve()


def _read_json(path: Path, description: str) -> dict[str, object]:
    if not path.is_file():
        raise SharedB0DistilBertError(f"{description}不存在：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedB0DistilBertError(f"无法读取{description}：{path}") from error
    if not isinstance(value, dict):
        raise SharedB0DistilBertError(f"{description}顶层必须是对象")
    return value


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _canonical_json(value: object) -> str:
    return json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _expected_sha256(value: object, description: str) -> str:
    digest = str(value).strip()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise SharedB0DistilBertError(f"{description}必须是小写 SHA-256")
    return digest


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as target:
            json.dump(
                value,
                target,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            target.write("\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _append_jsonl(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as target:
        target.write(_canonical_json(value) + "\n")
        target.flush()
        os.fsync(target.fileno())


def _atomic_write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as target:
            for row in rows:
                target.write(_canonical_json(row) + "\n")
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def config_snapshot(config: DistilBertBaselineConfig) -> dict[str, object]:
    """返回不含隐式默认值、可直接持久化的规范配置。"""
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "dataset": {"root": str(config.dataset.root)},
        "model": {
            "identifier": config.model.identifier,
            "source": config.model.source,
            "max_length": config.model.max_length,
            "device": config.model.device,
            "precision": config.model.precision,
        },
        "training": {
            "per_device_train_batch_size": config.training.per_device_train_batch_size,
            "per_device_eval_batch_size": config.training.per_device_eval_batch_size,
            "gradient_accumulation_steps": config.training.gradient_accumulation_steps,
            "effective_batch_size": config.training.effective_batch_size,
            "learning_rate": config.training.learning_rate,
            "weight_decay": config.training.weight_decay,
            "num_train_epochs": config.training.num_train_epochs,
            "warmup_ratio": config.training.warmup_ratio,
            "max_grad_norm": config.training.max_grad_norm,
            "save_steps": config.training.save_steps,
            "save_total_limit": config.training.save_total_limit,
            "num_workers": config.training.num_workers,
            "resume_from_checkpoint": config.training.resume_from_checkpoint,
        },
        "evaluation": {
            "threshold": config.evaluation.threshold,
            "calibration_bins": config.evaluation.calibration_bins,
            "selection_split": SELECTION_SPLIT,
            "external_evaluation_split": EXTERNAL_EVALUATION_SPLIT,
        },
        "run": {
            "output_dir": str(config.run.output_dir),
            "seed": config.run.seed,
            "stage": config.run.stage,
            "status": config.run.status,
        },
        "tracking": {
            "project": config.tracking.project,
            "workspace": config.tracking.workspace,
            "run_name": config.tracking.run_name,
            "description": config.tracking.description,
            "mode": config.tracking.mode,
            "tags": list(config.tracking.tags),
        },
    }


def load_config(path: Path) -> DistilBertBaselineConfig:
    """在导入任何模型运行时依赖前解析并严格校验真实配置。"""
    config_path = Path(path).expanduser().resolve()
    if not config_path.is_file():
        raise SharedB0DistilBertError(f"配置不存在：{config_path}")
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise SharedB0DistilBertError(f"配置不是合法 YAML：{config_path}") from error
    root = _mapping(raw, "配置")
    _exact_keys(
        root,
        required={
            "schema_version",
            "dataset",
            "model",
            "training",
            "evaluation",
            "run",
            "tracking",
        },
        description="配置",
    )
    if root["schema_version"] != CONFIG_SCHEMA_VERSION:
        raise SharedB0DistilBertError("配置 schema_version 不符合合同")
    project_root = config_path.parent.parent

    dataset_raw = _mapping(root["dataset"], "dataset")
    _exact_keys(dataset_raw, required={"root"}, description="dataset")
    dataset = DatasetSettings(root=_resolve_path(dataset_raw["root"], project_root, "dataset.root"))

    model_raw = _mapping(root["model"], "model")
    _exact_keys(
        model_raw,
        required={"identifier", "source", "max_length", "device", "precision"},
        description="model",
    )
    identifier = _nonempty_string(model_raw["identifier"], "model.identifier")
    if identifier != FIXED_MODEL_ID:
        raise SharedB0DistilBertError(f"model.identifier 必须固定为 {FIXED_MODEL_ID}")
    source_raw = _nonempty_string(model_raw["source"], "model.source")
    source = source_raw
    if source_raw != FIXED_MODEL_ID:
        source = str(_resolve_path(source_raw, project_root, "model.source"))
    max_length = _integer(model_raw["max_length"], "model.max_length", minimum=1)
    if max_length > int(MODEL_FINGERPRINT["max_position_embeddings"]):
        raise SharedB0DistilBertError("model.max_length 超过 DistilBERT 位置编码上限")
    device = _nonempty_string(model_raw["device"], "model.device")
    if device not in {"auto", "cpu", "cuda"}:
        raise SharedB0DistilBertError("model.device 只允许 auto、cpu 或 cuda")
    precision = _nonempty_string(model_raw["precision"], "model.precision")
    if precision not in {"auto", "float32", "float16", "bfloat16"}:
        raise SharedB0DistilBertError("model.precision 只允许 auto、float32、float16 或 bfloat16")
    model = ModelSettings(
        identifier=identifier,
        source=source,
        max_length=max_length,
        device=device,
        precision=precision,
    )

    training_raw = _mapping(root["training"], "training")
    _exact_keys(
        training_raw,
        required={
            "per_device_train_batch_size",
            "per_device_eval_batch_size",
            "gradient_accumulation_steps",
            "learning_rate",
            "weight_decay",
            "num_train_epochs",
            "warmup_ratio",
            "max_grad_norm",
            "save_steps",
            "save_total_limit",
            "num_workers",
            "resume_from_checkpoint",
        },
        description="training",
    )
    resume = _nonempty_string(
        training_raw["resume_from_checkpoint"], "training.resume_from_checkpoint"
    )
    if resume not in {"auto", "never"}:
        raise SharedB0DistilBertError("resume_from_checkpoint 只允许 auto 或 never")
    save_steps = _integer(training_raw["save_steps"], "training.save_steps", minimum=1)
    if save_steps > 20:
        raise SharedB0DistilBertError("training.save_steps 不得超过 20 个优化步")
    training = TrainingSettings(
        per_device_train_batch_size=_integer(
            training_raw["per_device_train_batch_size"],
            "training.per_device_train_batch_size",
            minimum=1,
        ),
        per_device_eval_batch_size=_integer(
            training_raw["per_device_eval_batch_size"],
            "training.per_device_eval_batch_size",
            minimum=1,
        ),
        gradient_accumulation_steps=_integer(
            training_raw["gradient_accumulation_steps"],
            "training.gradient_accumulation_steps",
            minimum=1,
        ),
        learning_rate=_number(
            training_raw["learning_rate"], "training.learning_rate", minimum=1e-12
        ),
        weight_decay=_number(training_raw["weight_decay"], "training.weight_decay", minimum=0.0),
        num_train_epochs=_integer(
            training_raw["num_train_epochs"], "training.num_train_epochs", minimum=1
        ),
        warmup_ratio=_number(
            training_raw["warmup_ratio"],
            "training.warmup_ratio",
            minimum=0.0,
            maximum=1.0,
        ),
        max_grad_norm=_number(
            training_raw["max_grad_norm"], "training.max_grad_norm", minimum=1e-12
        ),
        save_steps=save_steps,
        save_total_limit=_integer(
            training_raw["save_total_limit"], "training.save_total_limit", minimum=1
        ),
        num_workers=_integer(training_raw["num_workers"], "training.num_workers"),
        resume_from_checkpoint=resume,
    )

    evaluation_raw = _mapping(root["evaluation"], "evaluation")
    _exact_keys(
        evaluation_raw,
        required={"threshold", "calibration_bins"},
        description="evaluation",
    )
    threshold = _number(
        evaluation_raw["threshold"], "evaluation.threshold", minimum=0.0, maximum=1.0
    )
    if threshold != FIXED_THRESHOLD:
        raise SharedB0DistilBertError(f"evaluation.threshold 必须固定为 {FIXED_THRESHOLD}")
    evaluation = EvaluationSettings(
        threshold=threshold,
        calibration_bins=_integer(
            evaluation_raw["calibration_bins"], "evaluation.calibration_bins", minimum=2
        ),
    )

    run_raw = _mapping(root["run"], "run")
    _exact_keys(
        run_raw,
        required={"output_dir", "seed", "stage", "status"},
        description="run",
    )
    seed = _integer(run_raw["seed"], "run.seed")
    if seed != 42:
        raise SharedB0DistilBertError("共享 B0 DistilBERT 正式配置的种子必须为 42")
    stage = _nonempty_string(run_raw["stage"], "run.stage")
    status = _nonempty_string(run_raw["status"], "run.status")
    if stage != EXPECTED_STAGE or status != EXPECTED_PROTOCOL_STATUS:
        raise SharedB0DistilBertError(
            f"运行协议必须固定为 {EXPECTED_STAGE}/{EXPECTED_PROTOCOL_STATUS}"
        )
    run = RunSettings(
        output_dir=_resolve_path(run_raw["output_dir"], project_root, "run.output_dir"),
        seed=seed,
        stage=stage,
        status=status,
    )

    tracking_raw = _mapping(root["tracking"], "tracking")
    try:
        tracking = TrackingSettings.from_mapping(tracking_raw)
    except ValueError as error:
        raise SharedB0DistilBertError(str(error)) from error
    required_dynamic_tags = {
        f"epochs-{training.num_train_epochs}",
        "run-baseline",
        "protocol-partial",
    }
    missing_dynamic_tags = sorted(required_dynamic_tags.difference(tracking.tags))
    if missing_dynamic_tags:
        raise SharedB0DistilBertError(
            "tracking.tags 缺少最终动态标签：" + ", ".join(missing_dynamic_tags)
        )
    return DistilBertBaselineConfig(
        dataset=dataset,
        model=model,
        training=training,
        evaluation=evaluation,
        run=run,
        tracking=tracking,
        config_path=config_path,
    )


def with_model_source(
    config: DistilBertBaselineConfig, source: Path | str
) -> DistilBertBaselineConfig:
    """显式覆盖服务器本地镜像，同时保留固定模型标识。"""
    raw = str(source)
    resolved = raw if raw == FIXED_MODEL_ID else str(Path(raw).expanduser().resolve())
    return replace(config, model=replace(config.model, source=resolved))


def _registered_artifact(
    dataset_root: Path,
    artifacts: Mapping[str, object],
    relative_path: str,
) -> tuple[Path, dict[str, object]]:
    entry = _mapping(artifacts.get(relative_path), f"checksums.json 制品 {relative_path}")
    expected_hash = _expected_sha256(entry.get("sha256"), f"{relative_path} 登记哈希")
    expected_size = _integer(entry.get("size_bytes"), f"{relative_path} 登记大小")
    path = (dataset_root / relative_path).resolve()
    try:
        path.relative_to(dataset_root)
    except ValueError as error:
        raise SharedB0DistilBertError(f"冻结制品越过数据根目录：{relative_path}") from error
    if not path.is_file():
        raise SharedB0DistilBertError(f"冻结制品不存在：{path}")
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise SharedB0DistilBertError(
            f"{relative_path} 大小不一致：期望 {expected_size}，实际 {actual_size}"
        )
    actual_hash = file_sha256(path)
    if actual_hash != expected_hash:
        raise SharedB0DistilBertError(
            f"{relative_path} 哈希不一致：期望 {expected_hash}，实际 {actual_hash}"
        )
    return path, {"sha256": actual_hash, "size_bytes": actual_size}


def _validate_publication(
    dataset_root: Path,
    required_splits: Mapping[str, str] = REQUIRED_SPLITS,
) -> tuple[dict[str, object], dict[str, object]]:
    if not dataset_root.is_dir():
        raise SharedB0DistilBertError(f"共享 B0 数据目录不存在：{dataset_root}")
    if dataset_root.name != EXPECTED_DATASET_NAME:
        raise SharedB0DistilBertError(f"共享 B0 数据根目录名必须为 {EXPECTED_DATASET_NAME}")
    if dataset_root.name.endswith(".partial") or (dataset_root / "_INCOMPLETE").exists():
        raise SharedB0DistilBertError("共享 B0 数据仍处于未完成状态")
    if (dataset_root / "materialization_state.json").exists():
        raise SharedB0DistilBertError("共享 B0 数据含物化运行状态，拒绝读取")

    checksums_path = dataset_root / "manifests/checksums.json"
    freeze_path = dataset_root / "manifests/freeze_manifest.json"
    checksums = _read_json(checksums_path, "共享 B0 checksums.json")
    freeze = _read_json(freeze_path, "共享 B0 freeze_manifest.json")
    if checksums.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise SharedB0DistilBertError("checksums.json schema_version 不符合共享 B0 合同")
    if freeze.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise SharedB0DistilBertError("freeze_manifest.json schema_version 不符合共享 B0 合同")
    if freeze.get("stage") != EXPECTED_STAGE or freeze.get("status") != EXPECTED_PROTOCOL_STATUS:
        raise SharedB0DistilBertError("冻结数据阶段或状态不符合共享 B0 正式入口")
    if freeze.get("atomic_publication") is not True:
        raise SharedB0DistilBertError("freeze_manifest.json 未声明原子发布完成")
    expected_checksums_hash = _expected_sha256(
        freeze.get("checksums_sha256"), "freeze_manifest.json.checksums_sha256"
    )
    actual_checksums_hash = file_sha256(checksums_path)
    if actual_checksums_hash != expected_checksums_hash:
        raise SharedB0DistilBertError("checksums.json 与 freeze_manifest.json 绑定不一致")

    artifacts = _mapping(checksums.get("artifacts"), "checksums.json.artifacts")
    required_paths = {
        *required_splits.values(),
        "manifests/input_binding.json",
        "manifests/statistics.json",
    }
    verified: dict[str, object] = {}
    for relative_path in sorted(required_paths):
        _, binding = _registered_artifact(dataset_root, artifacts, relative_path)
        verified[relative_path] = binding
    input_binding_hash = _expected_sha256(
        freeze.get("input_binding_sha256"), "freeze_manifest.json.input_binding_sha256"
    )
    if verified["manifests/input_binding.json"]["sha256"] != input_binding_hash:
        raise SharedB0DistilBertError("input_binding.json 与 freeze_manifest.json 绑定不一致")
    statistics = _read_json(dataset_root / "manifests/statistics.json", "共享 B0 statistics")
    if statistics.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise SharedB0DistilBertError("statistics.json schema_version 不符合共享 B0 合同")
    if (
        statistics.get("stage") != EXPECTED_STAGE
        or statistics.get("status") != EXPECTED_PROTOCOL_STATUS
    ):
        raise SharedB0DistilBertError("statistics.json 阶段或状态不符合共享 B0 合同")
    return (
        {
            "checksums_sha256": actual_checksums_hash,
            "freeze_manifest_sha256": file_sha256(freeze_path),
            "verified_artifacts": verified,
            "freeze": freeze,
        },
        statistics,
    )


def _parquet_columns(path: Path, description: str) -> tuple[str, ...]:
    try:
        return tuple(pq.ParquetFile(path).schema_arrow.names)
    except Exception as error:
        raise SharedB0DistilBertError(f"无法读取{description} Parquet schema：{path}") from error


def _sample_order_sha256(sample_ids: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(sample_ids).encode("utf-8")).hexdigest()


def _load_text_split(
    *,
    dataset_root: Path,
    name: str,
    relative_path: str,
    artifact_binding: Mapping[str, object],
) -> FrozenTextSplit:
    path = dataset_root / relative_path
    columns = _parquet_columns(path, f"{name} DistilBERT 输入")
    if columns != INPUT_COLUMNS:
        raise SharedB0DistilBertError(
            f"{name} 输入列必须严格等于 {list(INPUT_COLUMNS)}，实际为 {list(columns)}"
        )
    try:
        frame = pd.read_parquet(path, columns=list(INPUT_COLUMNS))
    except Exception as error:
        raise SharedB0DistilBertError(f"无法读取{name} DistilBERT 输入：{path}") from error
    if frame.empty:
        raise SharedB0DistilBertError(f"{name} DistilBERT 输入不能为空")

    raw_ids = frame["sample_id"].tolist()
    if any(
        not isinstance(sample_id, str) or not sample_id or sample_id != sample_id.strip()
        for sample_id in raw_ids
    ):
        raise SharedB0DistilBertError(f"{name} sample_id 必须是无首尾空白的非空字符串")
    sample_ids = tuple(raw_ids)
    if len(sample_ids) != len(set(sample_ids)):
        raise SharedB0DistilBertError(f"{name} sample_id 必须唯一")

    order_series = frame["stable_order"]
    if (
        order_series.isna().any()
        or is_bool_dtype(order_series.dtype)
        or not is_integer_dtype(order_series.dtype)
    ):
        raise SharedB0DistilBertError(f"{name} stable_order 必须是整数列")
    stable_orders = tuple(int(value) for value in order_series.tolist())
    if stable_orders != tuple(range(len(frame))):
        raise SharedB0DistilBertError(f"{name} stable_order 必须按文件行顺序从 0 连续递增且唯一")

    raw_texts = frame["text"].tolist()
    if any(
        not isinstance(text, str) or not text.strip() or text != text.strip() for text in raw_texts
    ):
        raise SharedB0DistilBertError(f"{name} text 必须是无首尾空白的非空字符串")
    texts = tuple(raw_texts)

    label_series = frame["label"]
    if (
        label_series.isna().any()
        or is_bool_dtype(label_series.dtype)
        or not is_integer_dtype(label_series.dtype)
    ):
        raise SharedB0DistilBertError(f"{name} label 必须是只含 0/1 的整数列")
    labels = tuple(int(value) for value in label_series.tolist())
    if set(labels).difference(FIXED_LABEL_MAPPING):
        raise SharedB0DistilBertError(f"{name} label 必须是只含 0/1 的整数列")

    return FrozenTextSplit(
        name=name,
        relative_path=relative_path,
        sample_ids=sample_ids,
        stable_orders=stable_orders,
        texts=texts,
        labels=labels,
        sha256=str(artifact_binding["sha256"]),
        size_bytes=int(artifact_binding["size_bytes"]),
        sample_order_sha256=_sample_order_sha256(sample_ids),
    )


def prepare_frozen_inputs(dataset_root: Path) -> PreparedFrozenInputs:
    """核验发布、哈希、四列合同、顺序、标签和三划分互斥。"""
    root = Path(dataset_root).expanduser().resolve()
    publication, statistics = _validate_publication(root)
    verified = _mapping(publication["verified_artifacts"], "已验证冻结制品")
    splits: dict[str, FrozenTextSplit] = {}
    for name, relative_path in REQUIRED_SPLITS.items():
        splits[name] = _load_text_split(
            dataset_root=root,
            name=name,
            relative_path=relative_path,
            artifact_binding=_mapping(verified[relative_path], relative_path),
        )

    seen: set[str] = set()
    for name in ("train", SELECTION_SPLIT, EXTERNAL_EVALUATION_SPLIT):
        current = set(splits[name].sample_ids)
        overlap = seen.intersection(current)
        if overlap:
            raise SharedB0DistilBertError(f"冻结划分之间 sample_id 重叠：{sorted(overlap)[0]}")
        seen.update(current)
    if set(splits["train"].labels) != set(FIXED_LABEL_MAPPING):
        raise SharedB0DistilBertError("训练集必须同时且只包含标签 0 与 1")

    freeze = _mapping(publication["freeze"], "freeze_manifest.json")
    if freeze.get("candidate_count") != len(splits["train"]):
        raise SharedB0DistilBertError("freeze_manifest.json 候选数量与训练输入不一致")
    expected_validation_counts = {
        SELECTION_SPLIT: len(splits[SELECTION_SPLIT]),
        EXTERNAL_EVALUATION_SPLIT: len(splits[EXTERNAL_EVALUATION_SPLIT]),
    }
    if freeze.get("validation_counts") != expected_validation_counts:
        raise SharedB0DistilBertError("freeze_manifest.json 验证数量与输入不一致")
    if statistics.get("candidate_count") != len(splits["train"]):
        raise SharedB0DistilBertError("statistics.json 候选数量与训练输入不一致")
    validation_statistics = _mapping(statistics.get("validation"), "statistics.json.validation")
    for name, expected_count in expected_validation_counts.items():
        values = _mapping(validation_statistics.get(name), f"statistics.json.validation.{name}")
        if values.get("count") != expected_count:
            raise SharedB0DistilBertError(f"statistics.json 的 {name} 数量与输入不一致")

    split_bindings = {
        name: {
            "path": split.relative_path,
            "sha256": split.sha256,
            "size_bytes": split.size_bytes,
            "sample_count": len(split),
            "sample_order_sha256": split.sample_order_sha256,
            "label_counts": {
                FIXED_LABEL_MAPPING[label]: Counter(split.labels).get(label, 0)
                for label in FIXED_LABEL_MAPPING
            },
        }
        for name, split in splits.items()
    }
    binding = {
        "schema_version": INPUT_BINDING_SCHEMA_VERSION,
        "dataset_schema_version": ARTIFACT_SCHEMA_VERSION,
        "dataset_name": EXPECTED_DATASET_NAME,
        "dataset_root": str(root),
        "stage": EXPECTED_STAGE,
        "status": EXPECTED_PROTOCOL_STATUS,
        "checksums_sha256": publication["checksums_sha256"],
        "freeze_manifest_sha256": publication["freeze_manifest_sha256"],
        "input_binding_sha256": verified["manifests/input_binding.json"]["sha256"],
        "statistics_sha256": verified["manifests/statistics.json"]["sha256"],
        "allowed_columns": list(INPUT_COLUMNS),
        "label_mapping": {str(key): value for key, value in FIXED_LABEL_MAPPING.items()},
        "selection_split": SELECTION_SPLIT,
        "external_evaluation_split": EXTERNAL_EVALUATION_SPLIT,
        "splits": split_bindings,
    }
    return PreparedFrozenInputs(
        root=root,
        splits=MappingProxyType(splits),
        binding=MappingProxyType(binding),
        binding_sha256=_canonical_sha256(binding),
    )


def _slice_smoke_split(split: FrozenTextSplit) -> FrozenTextSplit:
    if len(split) < SMOKE_SAMPLE_COUNT:
        raise SharedB0DistilBertError(f"{split.name} 冒烟输入不足 {SMOKE_SAMPLE_COUNT} 条")
    return replace(
        split,
        sample_ids=split.sample_ids[:SMOKE_SAMPLE_COUNT],
        stable_orders=split.stable_orders[:SMOKE_SAMPLE_COUNT],
        texts=split.texts[:SMOKE_SAMPLE_COUNT],
        labels=split.labels[:SMOKE_SAMPLE_COUNT],
        sample_order_sha256=_sample_order_sha256(split.sample_ids[:SMOKE_SAMPLE_COUNT]),
    )


def prepare_smoke_inputs(dataset_root: Path) -> PreparedFrozenInputs:
    """只读取候选训练和 GeNIS 开发输入，并固定截取前 16 条。"""
    root = Path(dataset_root).expanduser().resolve()
    publication, statistics = _validate_publication(root, SMOKE_REQUIRED_SPLITS)
    verified = _mapping(publication["verified_artifacts"], "已验证冻结制品")
    full_splits = {
        name: _load_text_split(
            dataset_root=root,
            name=name,
            relative_path=relative_path,
            artifact_binding=_mapping(verified[relative_path], relative_path),
        )
        for name, relative_path in SMOKE_REQUIRED_SPLITS.items()
    }
    if set(full_splits["train"].labels) != set(FIXED_LABEL_MAPPING):
        raise SharedB0DistilBertError("训练集必须同时且只包含标签 0 与 1")
    overlap = set(full_splits["train"].sample_ids).intersection(
        full_splits[SELECTION_SPLIT].sample_ids
    )
    if overlap:
        raise SharedB0DistilBertError(f"冻结划分之间 sample_id 重叠：{sorted(overlap)[0]}")

    freeze = _mapping(publication["freeze"], "freeze_manifest.json")
    if freeze.get("candidate_count") != len(full_splits["train"]):
        raise SharedB0DistilBertError("freeze_manifest.json 候选数量与训练输入不一致")
    validation_counts = _mapping(
        freeze.get("validation_counts"), "freeze_manifest.json.validation_counts"
    )
    if validation_counts.get(SELECTION_SPLIT) != len(full_splits[SELECTION_SPLIT]):
        raise SharedB0DistilBertError("freeze_manifest.json GeNIS 数量与输入不一致")
    if statistics.get("candidate_count") != len(full_splits["train"]):
        raise SharedB0DistilBertError("statistics.json 候选数量与训练输入不一致")
    validation_statistics = _mapping(statistics.get("validation"), "statistics.json.validation")
    genis_statistics = _mapping(
        validation_statistics.get(SELECTION_SPLIT),
        f"statistics.json.validation.{SELECTION_SPLIT}",
    )
    if genis_statistics.get("count") != len(full_splits[SELECTION_SPLIT]):
        raise SharedB0DistilBertError("statistics.json GeNIS 数量与输入不一致")

    splits = {name: _slice_smoke_split(split) for name, split in full_splits.items()}
    split_bindings = {
        name: {
            "path": split.relative_path,
            "sha256": split.sha256,
            "size_bytes": split.size_bytes,
            "source_sample_count": len(full_splits[name]),
            "sample_count": len(split),
            "sample_order_sha256": split.sample_order_sha256,
            "label_counts": {
                FIXED_LABEL_MAPPING[label]: Counter(split.labels).get(label, 0)
                for label in FIXED_LABEL_MAPPING
            },
        }
        for name, split in splits.items()
    }
    binding = {
        "schema_version": INPUT_BINDING_SCHEMA_VERSION,
        "dataset_schema_version": ARTIFACT_SCHEMA_VERSION,
        "dataset_name": EXPECTED_DATASET_NAME,
        "dataset_root": str(root),
        "stage": EXPECTED_STAGE,
        "status": EXPECTED_PROTOCOL_STATUS,
        "mode": "smoke16",
        "smoke_sample_count": SMOKE_SAMPLE_COUNT,
        "tqhc2_access": "forbidden",
        "checksums_sha256": publication["checksums_sha256"],
        "freeze_manifest_sha256": publication["freeze_manifest_sha256"],
        "input_binding_sha256": verified["manifests/input_binding.json"]["sha256"],
        "statistics_sha256": verified["manifests/statistics.json"]["sha256"],
        "allowed_columns": list(INPUT_COLUMNS),
        "label_mapping": {str(key): value for key, value in FIXED_LABEL_MAPPING.items()},
        "selection_split": SELECTION_SPLIT,
        "external_evaluation_split": None,
        "splits": split_bindings,
    }
    return PreparedFrozenInputs(
        root=root,
        splits=MappingProxyType(splits),
        binding=MappingProxyType(binding),
        binding_sha256=_canonical_sha256(binding),
    )


def _model_artifact_paths(source: Path) -> list[Path]:
    paths = [source / "config.json"]
    for filename in (
        "tokenizer_config.json",
        "tokenizer.json",
        "vocab.txt",
        "special_tokens_map.json",
    ):
        path = source / filename
        if path.is_file():
            paths.append(path)
    for pattern in MODEL_WEIGHT_PATTERNS:
        paths.extend(path for path in source.glob(pattern) if path.is_file())
    return sorted(set(paths))


def validate_model_source(model: ModelSettings) -> Mapping[str, object]:
    """在导入 Transformers 前核验固定标识或严格对应的本地镜像。"""
    if model.identifier != FIXED_MODEL_ID:
        raise SharedB0DistilBertError(f"模型标识必须固定为 {FIXED_MODEL_ID}")
    if model.source == FIXED_MODEL_ID:
        return MappingProxyType(
            {
                "schema_version": MODEL_BINDING_SCHEMA_VERSION,
                "identifier": FIXED_MODEL_ID,
                "upstream_source": FIXED_MODEL_ID,
                "source_kind": "huggingface_identifier",
                "source": FIXED_MODEL_ID,
                "fingerprint": dict(MODEL_FINGERPRINT),
                "local_files_verified": False,
            }
        )

    source = Path(model.source).expanduser().resolve()
    if not source.is_dir():
        raise SharedB0DistilBertError(f"DistilBERT 本地镜像不存在：{source}")
    config = _read_json(source / "config.json", "DistilBERT 本地镜像 config.json")
    mismatches = {
        field: {"expected": expected, "actual": config.get(field)}
        for field, expected in MODEL_FINGERPRINT.items()
        if config.get(field) != expected
    }
    if mismatches:
        raise SharedB0DistilBertError(
            "本地镜像不是 distilbert-base-multilingual-cased：" + _canonical_json(mismatches)
        )
    tokenizer_exists = any(
        (source / filename).is_file() for filename in ("tokenizer.json", "vocab.txt")
    )
    if not tokenizer_exists:
        raise SharedB0DistilBertError("DistilBERT 本地镜像缺少 tokenizer.json 或 vocab.txt")
    weight_paths = sorted(
        {
            path
            for pattern in MODEL_WEIGHT_PATTERNS
            for path in source.glob(pattern)
            if path.is_file()
        }
    )
    if not weight_paths:
        raise SharedB0DistilBertError("DistilBERT 本地镜像缺少模型权重")
    artifacts = {}
    total_size = 0
    for path in _model_artifact_paths(source):
        relative = path.relative_to(source).as_posix()
        size = path.stat().st_size
        artifacts[relative] = {"sha256": file_sha256(path), "size_bytes": size}
        total_size += size
    return MappingProxyType(
        {
            "schema_version": MODEL_BINDING_SCHEMA_VERSION,
            "identifier": FIXED_MODEL_ID,
            "upstream_source": FIXED_MODEL_ID,
            "source_kind": "local_mirror",
            "source": str(source),
            "fingerprint": dict(MODEL_FINGERPRINT),
            "local_files_verified": True,
            "artifact_count": len(artifacts),
            "total_size_bytes": total_size,
            "artifacts": artifacts,
            "binding_sha256": _canonical_sha256(artifacts),
        }
    )


def _new_run_state(binding_sha256: str) -> dict[str, object]:
    timestamp = _utc_now()
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
        "tqhc2_evaluation_status": "not_started",
        "swanlab_attempts": [],
        "started_at": timestamp,
        "updated_at": timestamp,
        "failure": None,
    }


def _validate_run_state(value: Mapping[str, object], path: Path) -> dict[str, object]:
    required = set(_new_run_state("0" * 64))
    if set(value) != required:
        missing = sorted(required.difference(value))
        unexpected = sorted(set(value).difference(required))
        raise SharedB0DistilBertError(
            f"运行状态字段非法：{path}：缺少={missing}，额外={unexpected}"
        )
    if value.get("schema_version") != RUN_STATE_SCHEMA_VERSION:
        raise SharedB0DistilBertError(f"运行状态 schema_version 非法：{path}")
    if value.get("status") not in RUN_STATUSES:
        raise SharedB0DistilBertError(f"运行状态 status 非法：{path}")
    _expected_sha256(value.get("binding_sha256"), "运行状态 binding_sha256")
    for field in ("current_step", "current_epoch", "next_batch_index"):
        _integer(value.get(field), f"运行状态 {field}")
    if value.get("tqhc2_evaluation_status") not in TQHC2_EVALUATION_STATUSES:
        raise SharedB0DistilBertError("运行状态 tqhc2_evaluation_status 非法")
    for field in ("run_id", "started_at", "updated_at"):
        _nonempty_string(value.get(field), f"运行状态 {field}")
    for field in ("latest_checkpoint", "best_model", "failure"):
        raw = value.get(field)
        if raw is not None and not isinstance(raw, str):
            raise SharedB0DistilBertError(f"运行状态 {field} 必须是字符串或空值")
    best_epoch = value.get("best_epoch")
    if best_epoch is not None:
        _integer(best_epoch, "运行状态 best_epoch")
    best_macro_f1 = value.get("best_macro_f1")
    if best_macro_f1 is not None:
        _number(best_macro_f1, "运行状态 best_macro_f1", minimum=0.0, maximum=1.0)
    attempts = value.get("swanlab_attempts")
    if not isinstance(attempts, list) or any(not isinstance(item, dict) for item in attempts):
        raise SharedB0DistilBertError("运行状态 swanlab_attempts 必须是对象列表")
    return dict(value)


class RunStateController:
    """通过原子 JSON 转换维护训练、恢复和外部评价状态。"""

    def __init__(self, path: Path, initial_state: Mapping[str, object] | None = None) -> None:
        self.path = Path(path)
        source = _read_json(self.path, "运行状态") if initial_state is None else dict(initial_state)
        self._state = _validate_run_state(source, self.path)

    @property
    def state(self) -> Mapping[str, object]:
        return MappingProxyType(dict(self._state))

    @property
    def status(self) -> str:
        return str(self._state["status"])

    def transition(self, status: str, **updates: object) -> None:
        if status not in RUN_STATUSES:
            raise SharedB0DistilBertError(f"非法运行状态：{status}")
        unknown = sorted(set(updates).difference(self._state))
        if unknown:
            raise SharedB0DistilBertError(f"运行状态更新含未知字段：{', '.join(unknown)}")
        next_state = {**self._state, **updates, "status": status, "updated_at": _utc_now()}
        self._state = _validate_run_state(next_state, self.path)
        _atomic_write_json(self.path, self._state)

    def update(self, **updates: object) -> None:
        self.transition(self.status, **updates)

    def mark_interrupted(self, error: BaseException) -> None:
        self.transition("interrupted", failure=f"{type(error).__name__}: {error}")

    def mark_failed(self, error: BaseException) -> None:
        self.transition("failed", failure=f"{type(error).__name__}: {error}")


def _artifact_records(root: Path, *, excluded: set[Path] | None = None) -> dict[str, object]:
    excluded_resolved = {path.resolve() for path in (excluded or set())}
    records: dict[str, object] = {}
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        if path.resolve() in excluded_resolved:
            continue
        relative = path.relative_to(root).as_posix()
        records[relative] = {"sha256": file_sha256(path), "size_bytes": path.stat().st_size}
    return records


def _validate_checkpoint(path: Path, binding_sha256: str) -> dict[str, object] | None:
    match = CHECKPOINT_PATTERN.fullmatch(path.name)
    if match is None or not path.is_dir():
        return None
    manifest_path = path / "checkpoint_manifest.json"
    try:
        manifest = _read_json(manifest_path, "检查点清单")
        if manifest.get("schema_version") != CHECKPOINT_SCHEMA_VERSION:
            return None
        if manifest.get("binding_sha256") != binding_sha256:
            return None
        if manifest.get("global_step") != int(match.group(1)):
            return None
        if not {"best_model", "best_epoch", "best_macro_f1"}.issubset(manifest):
            return None
        _integer(manifest.get("next_epoch"), "检查点 next_epoch")
        _integer(manifest.get("next_batch_index"), "检查点 next_batch_index")
        best_model = manifest.get("best_model")
        if best_model is not None and not isinstance(best_model, str):
            return None
        if best_model is not None:
            selected_path = Path(best_model)
            selection_manifest = _read_json(
                selected_path / "selection_manifest.json", "检查点绑定的选模清单"
            )
            if selection_manifest.get("binding_sha256") != binding_sha256:
                return None
        best_epoch = manifest.get("best_epoch")
        if best_epoch is not None:
            _integer(best_epoch, "检查点 best_epoch")
        best_macro_f1 = manifest.get("best_macro_f1")
        if best_macro_f1 is not None:
            _number(
                best_macro_f1,
                "检查点 best_macro_f1",
                minimum=0.0,
                maximum=1.0,
            )
        artifacts = _mapping(manifest.get("artifacts"), "检查点 artifacts")
        required = {"training_state.pt", "config.json"}
        if not required.issubset(artifacts):
            return None
        if not any(
            name.endswith(".safetensors") or name.startswith("pytorch_model") for name in artifacts
        ):
            return None
        for relative, raw_record in artifacts.items():
            record = _mapping(raw_record, f"检查点制品 {relative}")
            artifact_path = (path / relative).resolve()
            artifact_path.relative_to(path.resolve())
            expected_size = _integer(record.get("size_bytes"), f"检查点 {relative} 大小")
            expected_hash = _expected_sha256(record.get("sha256"), f"检查点 {relative} 哈希")
            if (
                not artifact_path.is_file()
                or artifact_path.stat().st_size != expected_size
                or file_sha256(artifact_path) != expected_hash
            ):
                return None
    except (OSError, ValueError, SharedB0DistilBertError):
        return None
    return manifest


def resolve_latest_legal_checkpoint(output_dir: Path, binding_sha256: str) -> Path | None:
    """选择步数最大的绑定一致且所有登记文件完整的检查点。"""
    root = Path(output_dir)
    if not root.is_dir():
        return None
    candidates = []
    for path in root.iterdir():
        match = CHECKPOINT_PATTERN.fullmatch(path.name)
        if match is not None and path.is_dir():
            candidates.append((int(match.group(1)), path))
    for _, path in sorted(candidates, reverse=True):
        if _validate_checkpoint(path, binding_sha256) is not None:
            return path
    return None


def _build_run_binding(
    config: DistilBertBaselineConfig,
    inputs: PreparedFrozenInputs,
    model_binding: Mapping[str, object],
) -> dict[str, object]:
    has_external_evaluation = EXTERNAL_EVALUATION_SPLIT in inputs.splits
    return {
        "schema_version": RUN_BINDING_SCHEMA_VERSION,
        "config": config_snapshot(config),
        "config_file_sha256": file_sha256(config.config_path),
        "input_binding_sha256": inputs.binding_sha256,
        "model_binding_sha256": _canonical_sha256(model_binding),
        "implementation_sha256": file_sha256(Path(__file__)),
        "seed": config.run.seed,
        "threshold": FIXED_THRESHOLD,
        "label_mapping": {str(key): value for key, value in FIXED_LABEL_MAPPING.items()},
        "selection_split": SELECTION_SPLIT,
        "external_evaluation_split": (
            EXTERNAL_EVALUATION_SPLIT if has_external_evaluation else None
        ),
        "external_evaluation_use": (
            "模型冻结后仅评价一次" if has_external_evaluation else "冒烟模式禁止读取"
        ),
    }


def prepare_run(
    config: DistilBertBaselineConfig,
    inputs: PreparedFrozenInputs,
    model_binding: Mapping[str, object],
) -> PreparedRun:
    """在加载模型前创建新运行，或绑定到最新合法检查点。"""
    run_binding = _build_run_binding(config, inputs, model_binding)
    binding_sha256 = _canonical_sha256(run_binding)
    output = config.run.output_dir
    state_path = output / "run_state.json"
    binding_path = output / "run_binding.json"
    if not output.exists():
        output.mkdir(parents=True)
        _atomic_write_json(output / "config_snapshot.json", config_snapshot(config))
        _atomic_write_json(output / "input_binding.json", dict(inputs.binding))
        _atomic_write_json(output / "model_binding.json", dict(model_binding))
        _atomic_write_json(binding_path, run_binding)
        state = _new_run_state(binding_sha256)
        _atomic_write_json(state_path, state)
        return PreparedRun(
            config=config,
            inputs=inputs,
            model_binding=model_binding,
            run_binding=MappingProxyType(run_binding),
            binding_sha256=binding_sha256,
            state_path=state_path,
            resume_checkpoint=None,
        )
    if output.is_symlink() or not output.is_dir():
        raise SharedB0DistilBertError(f"运行输出路径不是普通目录：{output}")
    if config.training.resume_from_checkpoint == "never":
        raise SharedB0DistilBertError("运行目录已存在且禁止恢复，拒绝覆盖")
    for required in (binding_path, state_path):
        if not required.is_file():
            raise SharedB0DistilBertError(f"已有运行缺少恢复元数据：{required.name}")
    stored_binding = _read_json(binding_path, "已有运行绑定")
    if stored_binding != run_binding:
        mismatches = sorted(
            key
            for key in set(stored_binding) | set(run_binding)
            if stored_binding.get(key) != run_binding.get(key)
        )
        raise SharedB0DistilBertError("已有运行绑定不一致，拒绝恢复：" + ", ".join(mismatches))
    state = _validate_run_state(_read_json(state_path, "已有运行状态"), state_path)
    if state["binding_sha256"] != binding_sha256:
        raise SharedB0DistilBertError("已有运行状态与运行绑定哈希不一致")
    if state["status"] not in RESUMABLE_STATUSES:
        raise SharedB0DistilBertError(f"运行状态为 {state['status']}，拒绝覆盖或恢复")
    if state["tqhc2_evaluation_status"] != "not_started":
        raise SharedB0DistilBertError("TQH-C2 外部评价已经开始，禁止自动重复评价或继续调参")
    checkpoint = resolve_latest_legal_checkpoint(output, binding_sha256)
    if int(state["current_step"]) > 0 and checkpoint is None:
        raise SharedB0DistilBertError("已有训练进度但不存在合法检查点，拒绝恢复")
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
                "best_model": manifest["best_model"],
                "best_epoch": manifest["best_epoch"],
                "best_macro_f1": manifest["best_macro_f1"],
                "failure": None,
                "updated_at": _utc_now(),
            }
        )
        _atomic_write_json(state_path, _validate_run_state(state, state_path))
    return PreparedRun(
        config=config,
        inputs=inputs,
        model_binding=model_binding,
        run_binding=MappingProxyType(run_binding),
        binding_sha256=binding_sha256,
        state_path=state_path,
        resume_checkpoint=checkpoint,
    )


def prepare_smoke_run(
    config: DistilBertBaselineConfig,
    inputs: PreparedFrozenInputs,
    model_binding: Mapping[str, object],
    output_dir: Path,
) -> PreparedRun:
    """构造独立且不可恢复覆盖的单步 16 条 GPU 冒烟运行。"""
    if tuple(inputs.splits) != ("train", SELECTION_SPLIT):
        raise SharedB0DistilBertError("冒烟输入只能包含训练与 GeNIS 开发划分")
    if any(len(split) != SMOKE_SAMPLE_COUNT for split in inputs.splits.values()):
        raise SharedB0DistilBertError(f"冒烟训练与 GeNIS 开发划分必须各为 {SMOKE_SAMPLE_COUNT} 条")
    smoke_output = Path(output_dir).expanduser().resolve()
    formal_output = config.run.output_dir.resolve()
    if smoke_output == formal_output or formal_output in smoke_output.parents:
        raise SharedB0DistilBertError("冒烟输出必须与正式输出目录隔离")
    smoke_training = replace(
        config.training,
        per_device_train_batch_size=SMOKE_SAMPLE_COUNT,
        per_device_eval_batch_size=SMOKE_SAMPLE_COUNT,
        gradient_accumulation_steps=1,
        num_train_epochs=1,
        save_steps=1,
        save_total_limit=1,
        num_workers=0,
        resume_from_checkpoint="never",
    )
    smoke_tracking = replace(
        config.tracking,
        run_name=f"{config.tracking.run_name}-smoke16",
        description="共享 B0 DistilBERT 的 16 条非最终训练与 GeNIS 开发冒烟",
        tags=(
            "shared-b0",
            "distilbert",
            "seed-42",
            "epochs-1",
            "run-smoke",
            "protocol-partial",
        ),
    )
    smoke_config = replace(
        config,
        training=smoke_training,
        run=replace(config.run, output_dir=smoke_output),
        tracking=smoke_tracking,
    )
    return prepare_run(smoke_config, inputs, model_binding)


def load_runtime_modules() -> RuntimeModules:
    """仅在全部配置、输入、模型镜像和恢复检查通过后导入运行时。"""
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as error:
        raise UnsupportedRuntimeError(f"缺少 DistilBERT 运行依赖：{error}") from error
    return RuntimeModules(
        torch=torch,
        auto_tokenizer=AutoTokenizer,
        auto_model=AutoModelForSequenceClassification,
    )


def resolve_runtime(
    torch_module: Any,
    model: ModelSettings,
    *,
    formal_training: bool,
) -> RuntimeSelection:
    cuda_available = bool(torch_module.cuda.is_available())
    if model.device == "cuda" and not cuda_available:
        raise UnsupportedRuntimeError("配置要求 CUDA，但当前环境未检测到可用 GPU")
    device = (
        "cuda" if model.device == "cuda" or (model.device == "auto" and cuda_available) else "cpu"
    )
    if formal_training and device != "cuda":
        raise UnsupportedRuntimeError(
            "当前环境仅支持数据合同和 CPU 前向冒烟，不支持正式 DistilBERT 训练"
        )
    if model.precision == "auto":
        if device == "cuda" and bool(torch_module.cuda.is_bf16_supported()):
            precision = "bfloat16"
        elif device == "cuda":
            precision = "float16"
        else:
            precision = "float32"
    else:
        precision = model.precision
    if device == "cpu" and precision == "float16":
        raise UnsupportedRuntimeError("CPU 前向冒烟不支持 float16，请使用 auto 或 float32")
    dtype = {
        "float32": torch_module.float32,
        "float16": torch_module.float16,
        "bfloat16": torch_module.bfloat16,
    }[precision]
    return RuntimeSelection(
        device=device,
        precision=precision,
        torch_dtype=dtype,
        use_grad_scaler=device == "cuda" and precision == "float16",
    )


def _local_files_only(model: ModelSettings) -> bool:
    return model.source != FIXED_MODEL_ID


def _set_reproducible_seed(torch_module: Any, seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch_module.manual_seed(seed)
    if torch_module.cuda.is_available():
        torch_module.cuda.manual_seed_all(seed)
    torch_module.use_deterministic_algorithms(True, warn_only=True)
    if hasattr(torch_module.backends, "cudnn"):
        torch_module.backends.cudnn.benchmark = False
        torch_module.backends.cudnn.deterministic = True


def _load_tokenizer_and_model(
    modules: RuntimeModules,
    config: DistilBertBaselineConfig,
    runtime: RuntimeSelection,
    *,
    source: str | Path,
) -> tuple[Any, Any]:
    source_text = str(source)
    local_only = source_text != FIXED_MODEL_ID
    tokenizer = modules.auto_tokenizer.from_pretrained(
        source_text,
        use_fast=True,
        local_files_only=local_only,
    )
    model = modules.auto_model.from_pretrained(
        source_text,
        num_labels=2,
        id2label={0: "benign", 1: "malicious"},
        label2id={"benign": 0, "malicious": 1},
        ignore_mismatched_sizes=True,
        local_files_only=local_only,
    )
    model.to(runtime.device)
    return tokenizer, model


def forward_probability_batch(
    *,
    model: Any,
    tokenizer: Any,
    texts: Sequence[str],
    device: str,
    max_length: int,
    torch_module: Any,
) -> tuple[float, ...]:
    """执行一个保持输入顺序的二分类前向批次，供正式评价和 CPU 冒烟共用。"""
    if not texts:
        raise SharedB0DistilBertError("前向批次不能为空")
    encoded = tokenizer(
        list(texts),
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    encoded = {key: value.to(device) for key, value in encoded.items()}
    model.eval()
    with torch_module.no_grad():
        output = model(**encoded)
        logits = output.logits
        if logits.ndim != 2 or tuple(logits.shape) != (len(texts), 2):
            raise SharedB0DistilBertError("模型前向 logits 形状必须为 [batch, 2]")
        probabilities = torch_module.softmax(logits.float(), dim=-1)[:, 1]
    values = tuple(float(value) for value in probabilities.detach().cpu().tolist())
    if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in values):
        raise SharedB0DistilBertError("模型输出了非法恶意概率")
    return values


def compute_binary_metrics(
    labels: Sequence[int],
    malicious_probabilities: Sequence[float],
    *,
    threshold: float = FIXED_THRESHOLD,
    calibration_bins: int = 15,
) -> dict[str, int | float]:
    """计算固定标签映射下的效果与概率校准指标。"""
    if not labels or len(labels) != len(malicious_probabilities):
        raise SharedB0DistilBertError("指标标签与概率必须等长且非空")
    if threshold != FIXED_THRESHOLD:
        raise SharedB0DistilBertError(f"评价阈值必须固定为 {FIXED_THRESHOLD}")
    _integer(calibration_bins, "calibration_bins", minimum=2)
    truth = np.asarray(labels, dtype=np.int64)
    probabilities = np.asarray(malicious_probabilities, dtype=np.float64)
    if set(int(value) for value in truth.tolist()).difference(FIXED_LABEL_MAPPING):
        raise SharedB0DistilBertError("指标标签必须只含 0/1")
    if (
        not np.isfinite(probabilities).all()
        or np.any(probabilities < 0.0)
        or np.any(probabilities > 1.0)
    ):
        raise SharedB0DistilBertError("指标概率必须是 [0, 1] 内的有限数")
    predictions = (probabilities >= threshold).astype(np.int64)
    true_positive = int(np.sum((truth == 1) & (predictions == 1)))
    true_negative = int(np.sum((truth == 0) & (predictions == 0)))
    false_positive = int(np.sum((truth == 0) & (predictions == 1)))
    false_negative = int(np.sum((truth == 1) & (predictions == 0)))

    def safe_divide(numerator: int | float, denominator: int | float) -> float:
        return float(numerator / denominator) if denominator else 0.0

    malicious_precision = safe_divide(true_positive, true_positive + false_positive)
    malicious_recall = safe_divide(true_positive, true_positive + false_negative)
    malicious_f1 = safe_divide(
        2.0 * malicious_precision * malicious_recall,
        malicious_precision + malicious_recall,
    )
    benign_precision = safe_divide(true_negative, true_negative + false_negative)
    benign_recall = safe_divide(true_negative, true_negative + false_positive)
    benign_f1 = safe_divide(
        2.0 * benign_precision * benign_recall,
        benign_precision + benign_recall,
    )
    confidences = np.maximum(probabilities, 1.0 - probabilities)
    correctness = (truth == predictions).astype(np.float64)
    edges = np.linspace(0.0, 1.0, calibration_bins + 1)
    calibration_error = 0.0
    for index in range(calibration_bins):
        if index == 0:
            mask = (confidences >= edges[index]) & (confidences <= edges[index + 1])
        else:
            mask = (confidences > edges[index]) & (confidences <= edges[index + 1])
        if np.any(mask):
            calibration_error += float(np.mean(mask)) * abs(
                float(np.mean(correctness[mask])) - float(np.mean(confidences[mask]))
            )
    return {
        "sample_count": len(labels),
        "accuracy": safe_divide(true_positive + true_negative, len(labels)),
        "macro_f1": (benign_f1 + malicious_f1) / 2.0,
        "benign_f1": benign_f1,
        "malicious_f1": malicious_f1,
        "malicious_recall": malicious_recall,
        "benign_false_positive_rate": safe_divide(false_positive, true_negative + false_positive),
        "balanced_accuracy": (benign_recall + malicious_recall) / 2.0,
        "expected_calibration_error": calibration_error,
        "brier_score": float(np.mean(np.square(probabilities - truth))),
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def build_training_step_scalars(
    *,
    loss: float,
    learning_rate: float,
    epoch: int,
    optimizer_step: int,
) -> dict[str, int | float]:
    values: dict[str, int | float] = {
        "train/loss": float(loss),
        "train/learning_rate": float(learning_rate),
        "train/epoch": int(epoch),
        "train/optimizer_step": int(optimizer_step),
    }
    _validate_scalar_metrics(values)
    return values


def build_development_scalars(
    metrics: Mapping[str, int | float], *, epoch: int
) -> dict[str, int | float]:
    values: dict[str, int | float] = {"dev/epoch": int(epoch)}
    values.update({f"dev/{key}": value for key, value in metrics.items()})
    _validate_scalar_metrics(values)
    return values


def _validate_scalar_metrics(metrics: Mapping[str, object]) -> None:
    if not metrics:
        raise SharedB0DistilBertError("SwanLab 标量事件不能为空")
    for key, value in metrics.items():
        if (
            not isinstance(key, str)
            or not key
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
        ):
            raise SharedB0DistilBertError("SwanLab 事件只能包含非空键和数值标量")
        if not math.isfinite(float(value)):
            raise SharedB0DistilBertError(f"SwanLab 标量不是有限数：{key}")


class ScalarLogger:
    def __init__(self, swanlab_module: Any, path: Path) -> None:
        self.swanlab = swanlab_module
        self.path = path

    def log(self, metrics: Mapping[str, int | float], *, step: int, event: str) -> None:
        _validate_scalar_metrics(metrics)
        payload = {"event": event, "step": int(step), "metrics": dict(metrics)}
        _append_jsonl(self.path, payload)
        self.swanlab.log(dict(metrics), step=int(step))


@contextmanager
def _swanlab_attempt(
    prepared: PreparedRun,
    state: RunStateController,
    config_for_tracking: Mapping[str, object],
    swanlab_module: Any | None,
) -> Iterator[ScalarLogger]:
    if swanlab_module is None:
        try:
            import swanlab as swanlab_module
        except ImportError as error:
            raise UnsupportedRuntimeError("缺少 SwanLab 在线跟踪依赖") from error
    attempts = [dict(item) for item in state.state["swanlab_attempts"]]
    attempt_number = len(attempts) + 1
    attempt_dir = prepared.config.run.output_dir / "swanlog" / f"attempt-{attempt_number}"
    run = swanlab_module.init(
        project=prepared.config.tracking.project,
        workspace=prepared.config.tracking.workspace,
        name=f"{prepared.config.tracking.run_name}-attempt-{attempt_number}",
        description=prepared.config.tracking.description,
        config=dict(config_for_tracking),
        mode=prepared.config.tracking.mode,
        tags=list(prepared.config.tracking.tags),
        group=prepared.config.tracking.run_name,
        job_type="shared-b0-distilbert",
        log_dir=str(attempt_dir),
    )
    attempt = {
        "attempt": attempt_number,
        "run_id": str(run.id),
        "status": "running",
        "started_at": _utc_now(),
        "finished_at": None,
    }
    attempts.append(attempt)
    state.update(swanlab_attempts=attempts)
    logger = ScalarLogger(
        swanlab_module,
        prepared.config.run.output_dir / "swanlab_metrics.jsonl",
    )
    try:
        yield logger
    except BaseException as error:
        swanlab_module.finish(state="crashed", error=str(error))
        attempt.update({"status": "crashed", "finished_at": _utc_now()})
        attempts[-1] = attempt
        state.update(swanlab_attempts=attempts)
        raise
    else:
        swanlab_module.finish()
        attempt.update({"status": "finished", "finished_at": _utc_now()})
        attempts[-1] = attempt
        state.update(swanlab_attempts=attempts)


class _IndexedTextDataset:
    def __init__(self, split: FrozenTextSplit) -> None:
        self.split = split

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, index: int) -> tuple[str, int]:
        return self.split.texts[index], self.split.labels[index]


def _collate_batch(tokenizer: Any, max_length: int, torch_module: Any):
    def collate(items: Sequence[tuple[str, int]]) -> dict[str, Any]:
        texts, labels = zip(*items, strict=True)
        encoded = tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch_module.tensor(labels, dtype=torch_module.long)
        return encoded

    return collate


def _data_loader(
    *,
    split: FrozenTextSplit,
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
        _IndexedTextDataset(split),
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=num_workers,
        collate_fn=_collate_batch(tokenizer, max_length, torch_module),
        pin_memory=bool(torch_module.cuda.is_available()),
        persistent_workers=bool(num_workers),
    )


@contextmanager
def _autocast(torch_module: Any, runtime: RuntimeSelection) -> Iterator[None]:
    if runtime.device == "cuda" and runtime.precision != "float32":
        with torch_module.autocast(device_type="cuda", dtype=runtime.torch_dtype, enabled=True):
            yield
    else:
        with nullcontext():
            yield


def _synchronize(torch_module: Any, runtime: RuntimeSelection) -> None:
    if runtime.device == "cuda":
        torch_module.cuda.synchronize()


def evaluate_split(
    *,
    model: Any,
    tokenizer: Any,
    split: FrozenTextSplit,
    config: DistilBertBaselineConfig,
    runtime: RuntimeSelection,
    torch_module: Any,
    incremental_prediction_path: Path | None = None,
) -> EvaluationResult:
    """保持冻结顺序评价一个划分，并返回概率级逐样本记录。"""
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
    batch_latencies: list[float] = []
    prediction_path = (
        Path(incremental_prediction_path) if incremental_prediction_path is not None else None
    )
    if prediction_path is not None:
        if prediction_path.exists() or prediction_path.is_symlink():
            raise SharedB0DistilBertError(f"增量预测路径已存在：{prediction_path}")
        prediction_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_offset = 0
    _synchronize(torch_module, runtime)
    started = time.perf_counter()
    with torch_module.no_grad():
        for batch in loader:
            batch_started = time.perf_counter()
            batch = {key: value.to(runtime.device) for key, value in batch.items()}
            labels = batch.pop("labels")
            with _autocast(torch_module, runtime):
                output = model(**batch)
            logits = output.logits
            if logits.ndim != 2 or logits.shape[1] != 2 or logits.shape[0] != labels.shape[0]:
                raise SharedB0DistilBertError("评价 logits 形状必须为 [batch, 2]")
            values = torch_module.softmax(logits.float(), dim=-1)[:, 1]
            batch_probabilities = tuple(float(value) for value in values.detach().cpu().tolist())
            if any(
                not math.isfinite(value) or value < 0.0 or value > 1.0
                for value in batch_probabilities
            ):
                raise SharedB0DistilBertError("模型输出了非法恶意概率")
            probabilities.extend(batch_probabilities)
            if prediction_path is not None:
                for relative_index, probability in enumerate(batch_probabilities):
                    index = prediction_offset + relative_index
                    prediction = int(probability >= FIXED_THRESHOLD)
                    _append_jsonl(
                        prediction_path,
                        {
                            "sample_id": split.sample_ids[index],
                            "stable_order": split.stable_orders[index],
                            "probability_malicious": probability,
                            "prediction": prediction,
                            "prediction_label": FIXED_LABEL_MAPPING[prediction],
                            "label": split.labels[index],
                            "label_name": FIXED_LABEL_MAPPING[split.labels[index]],
                        },
                    )
                prediction_offset += len(batch_probabilities)
            _synchronize(torch_module, runtime)
            elapsed = time.perf_counter() - batch_started
            batch_latencies.extend([elapsed / int(labels.shape[0])] * int(labels.shape[0]))
    _synchronize(torch_module, runtime)
    inference_seconds = time.perf_counter() - started
    if prediction_path is not None and prediction_offset != len(split):
        raise SharedB0DistilBertError("增量预测行数与冒烟输入不一致")
    metrics = compute_binary_metrics(
        split.labels,
        probabilities,
        threshold=config.evaluation.threshold,
        calibration_bins=config.evaluation.calibration_bins,
    )
    latency_array = np.asarray(batch_latencies, dtype=np.float64) * 1000.0
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
            "prediction": int(probability >= FIXED_THRESHOLD),
            "prediction_label": FIXED_LABEL_MAPPING[int(probability >= FIXED_THRESHOLD)],
            "label": label,
            "label_name": FIXED_LABEL_MAPPING[label],
        }
        for sample_id, stable_order, probability, label in zip(
            split.sample_ids,
            split.stable_orders,
            probabilities,
            split.labels,
            strict=True,
        )
    )
    return EvaluationResult(metrics=MappingProxyType(metrics), predictions=rows)


def _linear_schedule_lambda(total_steps: int, warmup_steps: int):
    def schedule(current_step: int) -> float:
        if warmup_steps and current_step < warmup_steps:
            return float(current_step + 1) / float(warmup_steps)
        remaining = max(total_steps - current_step, 0)
        decay_steps = max(total_steps - warmup_steps, 1)
        return float(remaining) / float(decay_steps)

    return schedule


def _new_grad_scaler(torch_module: Any, enabled: bool) -> Any:
    try:
        return torch_module.amp.GradScaler("cuda", enabled=enabled)
    except TypeError:
        return torch_module.cuda.amp.GradScaler(enabled=enabled)


def _capture_rng_state(torch_module: Any) -> dict[str, object]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch_module.get_rng_state(),
        "cuda": torch_module.cuda.get_rng_state_all() if torch_module.cuda.is_available() else None,
    }


def _restore_rng_state(torch_module: Any, values: Mapping[str, object]) -> None:
    random.setstate(values["python"])
    np.random.set_state(values["numpy"])
    torch_module.set_rng_state(values["torch"])
    if torch_module.cuda.is_available() and values.get("cuda") is not None:
        torch_module.cuda.set_rng_state_all(values["cuda"])


def _save_training_checkpoint(
    *,
    prepared: PreparedRun,
    state: RunStateController,
    model: Any,
    tokenizer: Any,
    optimizer: Any,
    scheduler: Any,
    scaler: Any,
    torch_module: Any,
    global_step: int,
    next_epoch: int,
    next_batch_index: int,
) -> Path:
    output = prepared.config.run.output_dir
    target = output / f"checkpoint-{global_step}"
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
            _prune_checkpoints(output, prepared.config.training.save_total_limit, target)
            return target
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            raise SharedB0DistilBertError(f"同名检查点不是可替换的普通目录：{target}")
    temporary = output / f".checkpoint-{global_step}.{uuid.uuid4().hex}.partial"
    temporary.mkdir(parents=True)
    try:
        model.save_pretrained(temporary, safe_serialization=True)
        tokenizer.save_pretrained(temporary)
        torch_module.save(
            {
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "scaler": scaler.state_dict(),
                "rng": _capture_rng_state(torch_module),
                "global_step": global_step,
                "next_epoch": next_epoch,
                "next_batch_index": next_batch_index,
            },
            temporary / "training_state.pt",
        )
        artifacts = _artifact_records(temporary)
        manifest = {
            "schema_version": CHECKPOINT_SCHEMA_VERSION,
            "binding_sha256": prepared.binding_sha256,
            "global_step": global_step,
            "next_epoch": next_epoch,
            "next_batch_index": next_batch_index,
            "best_model": state.state["best_model"],
            "best_epoch": state.state["best_epoch"],
            "best_macro_f1": state.state["best_macro_f1"],
            "created_at": _utc_now(),
            "artifacts": artifacts,
        }
        _atomic_write_json(temporary / "checkpoint_manifest.json", manifest)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    if _validate_checkpoint(target, prepared.binding_sha256) is None:
        raise SharedB0DistilBertError(f"新检查点完整性复核失败：{target}")
    state.update(
        current_step=global_step,
        current_epoch=next_epoch,
        next_batch_index=next_batch_index,
        latest_checkpoint=str(target),
        failure=None,
    )
    _prune_checkpoints(output, prepared.config.training.save_total_limit, target)
    return target


def _prune_checkpoints(output: Path, limit: int, current: Path) -> None:
    candidates = []
    for path in output.iterdir():
        match = CHECKPOINT_PATTERN.fullmatch(path.name)
        if match is not None and path.is_dir():
            candidates.append((int(match.group(1)), path))
    for _, path in sorted(candidates)[: max(0, len(candidates) - limit)]:
        if path != current:
            shutil.rmtree(path)


def _save_selected_model(
    *,
    prepared: PreparedRun,
    model: Any,
    tokenizer: Any,
    epoch: int,
    global_step: int,
    metrics: Mapping[str, int | float],
) -> Path:
    root = prepared.config.run.output_dir / "model-selection"
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"epoch-{epoch:03d}-step-{global_step:08d}"
    if target.exists():
        raise SharedB0DistilBertError(f"选模制品目录已存在：{target}")
    temporary = root / f".{target.name}.{uuid.uuid4().hex}.partial"
    temporary.mkdir()
    try:
        model.save_pretrained(temporary, safe_serialization=True)
        tokenizer.save_pretrained(temporary)
        artifacts = _artifact_records(temporary)
        _atomic_write_json(
            temporary / "selection_manifest.json",
            {
                "schema_version": "flow_probe_shared_b0_distilbert_selection_v1",
                "binding_sha256": prepared.binding_sha256,
                "selection_split": SELECTION_SPLIT,
                "epoch": epoch,
                "global_step": global_step,
                "threshold": FIXED_THRESHOLD,
                "metrics": dict(metrics),
                "artifacts": artifacts,
            },
        )
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return target


def _restore_training_state(
    checkpoint: Path,
    *,
    optimizer: Any,
    scheduler: Any,
    scaler: Any,
    torch_module: Any,
) -> dict[str, object]:
    try:
        values = torch_module.load(
            checkpoint / "training_state.pt",
            map_location="cpu",
            weights_only=False,
        )
    except Exception as error:
        raise SharedB0DistilBertError(f"无法恢复训练状态：{checkpoint}") from error
    if not isinstance(values, dict):
        raise SharedB0DistilBertError("检查点 training_state.pt 顶层必须是对象")
    optimizer.load_state_dict(values["optimizer"])
    scheduler.load_state_dict(values["scheduler"])
    scaler.load_state_dict(values["scaler"])
    _restore_rng_state(torch_module, _mapping(values["rng"], "检查点 rng"))
    return values


def _is_better_selection(metrics: Mapping[str, int | float], state: Mapping[str, object]) -> bool:
    current = float(metrics["macro_f1"])
    best = state["best_macro_f1"]
    return best is None or current > float(best)


def _runtime_environment(
    torch_module: Any,
    runtime: RuntimeSelection,
    config: DistilBertBaselineConfig,
) -> dict[str, object]:
    total_memory = None
    try:
        total_memory = int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    except (AttributeError, OSError, ValueError):
        pass
    gpu = None
    if runtime.device == "cuda":
        properties = torch_module.cuda.get_device_properties(0)
        gpu = {"name": properties.name, "total_memory_bytes": int(properties.total_memory)}
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "cpu_model": platform.processor() or "不可用",
        "logical_cpu_count": os.cpu_count(),
        "system_memory_bytes": total_memory,
        "torch_version": str(torch_module.__version__),
        "cuda_available": bool(torch_module.cuda.is_available()),
        "cuda_version": getattr(torch_module.version, "cuda", None),
        "gpu": gpu,
        "selected_device": runtime.device,
        "precision": runtime.precision,
        "per_device_train_batch_size": config.training.per_device_train_batch_size,
        "gradient_accumulation_steps": config.training.gradient_accumulation_steps,
        "effective_batch_size": config.training.effective_batch_size,
    }


def _peak_process_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _train_model(
    *,
    prepared: PreparedRun,
    modules: RuntimeModules,
    runtime: RuntimeSelection,
    state: RunStateController,
    logger: ScalarLogger,
) -> tuple[Path, dict[str, object]]:
    config = prepared.config
    torch_module = modules.torch
    _set_reproducible_seed(torch_module, config.run.seed)
    source: str | Path = prepared.resume_checkpoint or config.model.source
    tokenizer, model = _load_tokenizer_and_model(
        modules,
        config,
        runtime,
        source=source,
    )
    train_split = prepared.inputs.splits["train"]
    batches_per_epoch = math.ceil(len(train_split) / config.training.per_device_train_batch_size)
    optimizer_steps_per_epoch = math.ceil(
        batches_per_epoch / config.training.gradient_accumulation_steps
    )
    total_optimizer_steps = optimizer_steps_per_epoch * config.training.num_train_epochs
    warmup_steps = int(total_optimizer_steps * config.training.warmup_ratio)
    optimizer = torch_module.optim.AdamW(
        model.parameters(),
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )
    scheduler = torch_module.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda=_linear_schedule_lambda(total_optimizer_steps, warmup_steps),
    )
    scaler = _new_grad_scaler(torch_module, runtime.use_grad_scaler)
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
            split=train_split,
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
            with _autocast(torch_module, runtime):
                output = model(**batch)
                loss = output.loss
            if loss is None or not bool(torch_module.isfinite(loss).item()):
                raise SharedB0DistilBertError("训练损失不是有限数")
            unscaled_loss = float(loss.detach().float().item())
            group_loss += unscaled_loss
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
            torch_module.nn.utils.clip_grad_norm_(model.parameters(), config.training.max_grad_norm)
            if runtime.use_grad_scaler:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)
            global_step += 1
            logger.log(
                build_training_step_scalars(
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
                _save_training_checkpoint(
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
                )

        development = evaluate_split(
            model=model,
            tokenizer=tokenizer,
            split=prepared.inputs.splits[SELECTION_SPLIT],
            config=config,
            runtime=runtime,
            torch_module=torch_module,
        )
        development_metrics = dict(development.metrics)
        logger.log(
            build_development_scalars(development_metrics, epoch=epoch_index + 1),
            step=global_step,
            event="development_evaluation",
        )
        selected_path = state.state["best_model"]
        if _is_better_selection(development_metrics, state.state):
            selected = _save_selected_model(
                prepared=prepared,
                model=model,
                tokenizer=tokenizer,
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
        _append_jsonl(
            config.run.output_dir / "development_history.jsonl",
            {
                "epoch": epoch_index + 1,
                "global_step": global_step,
                "selection_split": SELECTION_SPLIT,
                "selected_model": selected_path,
                "metrics": development_metrics,
            },
        )
        _save_training_checkpoint(
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
        )
        start_batch = 0

    training_seconds = time.perf_counter() - training_started
    selected_model = state.state["best_model"]
    if not isinstance(selected_model, str) or not Path(selected_model).is_dir():
        raise SharedB0DistilBertError("GeNIS 选模结束后缺少合法冻结模型")
    summary = {
        "training_seconds": training_seconds,
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
    return Path(selected_model), summary


def _final_evaluations(
    *,
    prepared: PreparedRun,
    selected_model: Path,
    modules: RuntimeModules,
    runtime: RuntimeSelection,
    state: RunStateController,
    logger: ScalarLogger,
) -> dict[str, object]:
    config = prepared.config
    tokenizer, model = _load_tokenizer_and_model(
        modules,
        config,
        runtime,
        source=selected_model,
    )
    predictions_dir = config.run.output_dir / "predictions"
    metrics_dir = config.run.output_dir / "metrics"
    genis_result = evaluate_split(
        model=model,
        tokenizer=tokenizer,
        split=prepared.inputs.splits[SELECTION_SPLIT],
        config=config,
        runtime=runtime,
        torch_module=modules.torch,
    )
    _atomic_write_jsonl(predictions_dir / "genis_predictions.jsonl", genis_result.predictions)
    _atomic_write_json(metrics_dir / "genis_metrics.json", dict(genis_result.metrics))
    logger.log(
        {f"final/genis/{key}": value for key, value in genis_result.metrics.items()},
        step=int(state.state["current_step"]),
        event="final_genis_evaluation",
    )

    state.update(tqhc2_evaluation_status="running")
    tqhc2_result = evaluate_split(
        model=model,
        tokenizer=tokenizer,
        split=prepared.inputs.splits[EXTERNAL_EVALUATION_SPLIT],
        config=config,
        runtime=runtime,
        torch_module=modules.torch,
    )
    _atomic_write_jsonl(predictions_dir / "tqhc2_predictions.jsonl", tqhc2_result.predictions)
    _atomic_write_json(metrics_dir / "tqhc2_metrics.json", dict(tqhc2_result.metrics))
    logger.log(
        {f"final/tqhc2/{key}": value for key, value in tqhc2_result.metrics.items()},
        step=int(state.state["current_step"]),
        event="final_tqhc2_evaluation",
    )
    state.update(tqhc2_evaluation_status="finished")
    return {
        SELECTION_SPLIT: dict(genis_result.metrics),
        EXTERNAL_EVALUATION_SPLIT: dict(tqhc2_result.metrics),
    }


def _write_final_artifact_manifest(
    prepared: PreparedRun,
    state: RunStateController,
) -> Mapping[str, object]:
    output = prepared.config.run.output_dir
    manifest_path = output / "artifact_manifest.json"
    records = _artifact_records(output, excluded={manifest_path})
    manifest = {
        "schema_version": ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "status": "finished",
        "stage": EXPECTED_STAGE,
        "protocol_status": EXPECTED_PROTOCOL_STATUS,
        "seed": prepared.config.run.seed,
        "binding_sha256": prepared.binding_sha256,
        "run_id": state.state["run_id"],
        "selection_split": SELECTION_SPLIT,
        "external_evaluation_split": EXTERNAL_EVALUATION_SPLIT,
        "threshold": FIXED_THRESHOLD,
        "tqhc2_evaluation_status": state.state["tqhc2_evaluation_status"],
        "artifact_count": len(records),
        "artifacts": records,
    }
    _atomic_write_json(manifest_path, manifest)
    return MappingProxyType(manifest)


def _last_training_loss(path: Path) -> float:
    if not path.is_file():
        raise SharedB0DistilBertError("冒烟缺少 SwanLab 本地逐步指标")
    last_loss: float | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise SharedB0DistilBertError("冒烟 SwanLab 本地指标不是合法 JSONL") from error
        metrics = event.get("metrics") if isinstance(event, dict) else None
        if isinstance(metrics, dict) and "train/loss" in metrics:
            last_loss = float(metrics["train/loss"])
    if last_loss is None or not math.isfinite(last_loss):
        raise SharedB0DistilBertError("冒烟未产生有限训练损失")
    return last_loss


def _write_smoke_artifact_manifest(
    prepared: PreparedRun,
    state: RunStateController,
) -> Mapping[str, object]:
    output = prepared.config.run.output_dir
    manifest_path = output / "artifact_manifest.json"
    records = _artifact_records(output, excluded={manifest_path})
    manifest = {
        "schema_version": SMOKE_ARTIFACT_MANIFEST_SCHEMA_VERSION,
        "status": "finished",
        "stage": EXPECTED_STAGE,
        "protocol_status": EXPECTED_PROTOCOL_STATUS,
        "mode": "smoke16",
        "seed": prepared.config.run.seed,
        "binding_sha256": prepared.binding_sha256,
        "run_id": state.state["run_id"],
        "sample_counts": {name: len(split) for name, split in prepared.inputs.splits.items()},
        "selection_split": SELECTION_SPLIT,
        "external_evaluation_split": None,
        "tqhc2_access": "forbidden",
        "artifact_count": len(records),
        "artifacts": records,
    }
    _atomic_write_json(manifest_path, manifest)
    return MappingProxyType(manifest)


def execute_smoke_run(
    prepared: PreparedRun,
    *,
    modules: RuntimeModules | None = None,
    swanlab_module: Any | None = None,
) -> Mapping[str, object]:
    """执行单步 16 条训练与 GeNIS 开发评价，绝不触达 TQH-C2。"""
    if tuple(prepared.inputs.splits) != ("train", SELECTION_SPLIT):
        raise SharedB0DistilBertError("冒烟运行包含了非许可划分")
    if any(len(split) != SMOKE_SAMPLE_COUNT for split in prepared.inputs.splits.values()):
        raise SharedB0DistilBertError("冒烟运行样本数不是固定 16 条")
    runtime_modules = modules or load_runtime_modules()
    runtime = resolve_runtime(
        runtime_modules.torch,
        prepared.config.model,
        formal_training=True,
    )
    state = RunStateController(prepared.state_path)
    output = prepared.config.run.output_dir
    if runtime.device == "cuda":
        runtime_modules.torch.cuda.reset_peak_memory_stats()
    environment = _runtime_environment(runtime_modules.torch, runtime, prepared.config)
    _atomic_write_json(output / "environment.json", environment)
    tracking_config = {
        **config_snapshot(prepared.config),
        "mode": "smoke16",
        "smoke_sample_count": SMOKE_SAMPLE_COUNT,
        "tqhc2_access": "forbidden",
        "run_binding_sha256": prepared.binding_sha256,
        "runtime": environment,
    }
    total_started = time.perf_counter()
    try:
        with (
            _capture_console(output / "console.log"),
            _swanlab_attempt(prepared, state, tracking_config, swanlab_module) as logger,
        ):
            _, training_summary = _train_model(
                prepared=prepared,
                modules=runtime_modules,
                runtime=runtime,
                state=state,
                logger=logger,
            )
            prediction_path = output / "predictions" / "genis_predictions.jsonl"
            smoke_tokenizer, smoke_model = _load_tokenizer_and_model(
                runtime_modules,
                prepared.config,
                runtime,
                source=Path(str(training_summary["best_model"])),
            )
            development = evaluate_split(
                model=smoke_model,
                tokenizer=smoke_tokenizer,
                split=prepared.inputs.splits[SELECTION_SPLIT],
                config=prepared.config,
                runtime=runtime,
                torch_module=runtime_modules.torch,
                incremental_prediction_path=prediction_path,
            )
            _atomic_write_json(output / "metrics" / "genis_metrics.json", dict(development.metrics))
            logger.log(
                {f"smoke/genis/{key}": value for key, value in development.metrics.items()},
                step=int(state.state["current_step"]),
                event="smoke_genis_evaluation",
            )
            training_loss = _last_training_loss(output / "swanlab_metrics.jsonl")
            summary = {
                "schema_version": "flow_probe_shared_b0_distilbert_smoke16_summary_v1",
                "stage": EXPECTED_STAGE,
                "status": EXPECTED_PROTOCOL_STATUS,
                "mode": "smoke16",
                "seed": prepared.config.run.seed,
                "model_id": FIXED_MODEL_ID,
                "sample_counts": {"train": SMOKE_SAMPLE_COUNT, "genis": SMOKE_SAMPLE_COUNT},
                "optimizer_steps": int(training_summary["global_step"]),
                "training_loss": training_loss,
                "genis_metrics": dict(development.metrics),
                "prediction_path": str(prediction_path),
                "tqhc2_access": "forbidden",
            }
            _atomic_write_json(output / "summary.json", summary)
            _atomic_write_json(
                output / "cost.json",
                {
                    "schema_version": "flow_probe_shared_b0_distilbert_smoke16_cost_v1",
                    "total_seconds": time.perf_counter() - total_started,
                    "training_seconds": training_summary["training_seconds"],
                    "peak_process_rss_bytes": _peak_process_rss_bytes(),
                    "peak_gpu_memory_allocated_bytes": int(
                        runtime_modules.torch.cuda.max_memory_allocated()
                    ),
                    "peak_gpu_memory_reserved_bytes": int(
                        runtime_modules.torch.cuda.max_memory_reserved()
                    ),
                    "runtime": environment,
                },
            )
        state.transition("finished", failure=None)
        return _write_smoke_artifact_manifest(prepared, state)
    except KeyboardInterrupt as error:
        if state.status not in {"interrupted", "finished"}:
            state.mark_interrupted(error)
        raise
    except Exception as error:
        if state.status not in {"failed", "finished"}:
            state.mark_failed(error)
        raise


def execute_prepared_run(
    prepared: PreparedRun,
    *,
    modules: RuntimeModules | None = None,
    swanlab_module: Any | None = None,
) -> Mapping[str, object]:
    """执行正式训练、GeNIS 选模和一次性 TQH-C2 外部评价。"""
    runtime_modules = modules or load_runtime_modules()
    runtime = resolve_runtime(
        runtime_modules.torch,
        prepared.config.model,
        formal_training=True,
    )
    state = RunStateController(prepared.state_path)
    output = prepared.config.run.output_dir
    if runtime.device == "cuda":
        runtime_modules.torch.cuda.reset_peak_memory_stats()
    environment = _runtime_environment(runtime_modules.torch, runtime, prepared.config)
    _atomic_write_json(output / "environment.json", environment)
    tracking_config = {
        **config_snapshot(prepared.config),
        "run_binding_sha256": prepared.binding_sha256,
        "runtime": environment,
    }
    total_started = time.perf_counter()
    try:
        with (
            _capture_console(output / "console.log"),
            _swanlab_attempt(
                prepared,
                state,
                tracking_config,
                swanlab_module,
            ) as logger,
        ):
            selected_model, training_summary = _train_model(
                prepared=prepared,
                modules=runtime_modules,
                runtime=runtime,
                state=state,
                logger=logger,
            )
            evaluations = _final_evaluations(
                prepared=prepared,
                selected_model=selected_model,
                modules=runtime_modules,
                runtime=runtime,
                state=state,
                logger=logger,
            )
            summary = {
                "schema_version": "flow_probe_shared_b0_distilbert_summary_v1",
                "stage": EXPECTED_STAGE,
                "status": EXPECTED_PROTOCOL_STATUS,
                "seed": prepared.config.run.seed,
                "model_id": FIXED_MODEL_ID,
                "threshold": FIXED_THRESHOLD,
                "selection_split": SELECTION_SPLIT,
                "external_evaluation_split": EXTERNAL_EVALUATION_SPLIT,
                "training": training_summary,
                "evaluations": evaluations,
            }
            _atomic_write_json(output / "summary.json", summary)
            cost = {
                "schema_version": "flow_probe_shared_b0_distilbert_cost_v1",
                "total_seconds": time.perf_counter() - total_started,
                "training_seconds": training_summary["training_seconds"],
                "peak_process_rss_bytes": _peak_process_rss_bytes(),
                "peak_gpu_memory_allocated_bytes": (
                    int(runtime_modules.torch.cuda.max_memory_allocated())
                    if runtime.device == "cuda"
                    else None
                ),
                "peak_gpu_memory_reserved_bytes": (
                    int(runtime_modules.torch.cuda.max_memory_reserved())
                    if runtime.device == "cuda"
                    else None
                ),
                "runtime": environment,
                "evaluation": {
                    name: {
                        key: metrics[key]
                        for key in (
                            "inference_seconds",
                            "samples_per_second",
                            "latency_mean_ms",
                            "latency_p50_ms",
                            "latency_p95_ms",
                        )
                    }
                    for name, metrics in evaluations.items()
                },
            }
            _atomic_write_json(output / "cost.json", cost)
        state.transition("finished", failure=None)
        return _write_final_artifact_manifest(prepared, state)
    except KeyboardInterrupt as error:
        if state.status not in {"interrupted", "finished"}:
            state.mark_interrupted(error)
        raise
    except Exception as error:
        if state.status not in {"failed", "finished"}:
            state.mark_failed(error)
        raise


def run_cpu_forward_smoke(
    config: DistilBertBaselineConfig,
    inputs: PreparedFrozenInputs,
    *,
    modules: RuntimeModules | None = None,
) -> dict[str, object]:
    """在 CPU 上加载固定模型并对非最终 GeNIS 样本执行最小前向。"""
    runtime_modules = modules or load_runtime_modules()
    cpu_model = replace(config.model, device="cpu", precision="float32")
    runtime = resolve_runtime(runtime_modules.torch, cpu_model, formal_training=False)
    _set_reproducible_seed(runtime_modules.torch, config.run.seed)
    tokenizer, model = _load_tokenizer_and_model(
        runtime_modules,
        replace(config, model=cpu_model),
        runtime,
        source=cpu_model.source,
    )
    split = inputs.splits[SELECTION_SPLIT]
    sample_count = min(2, len(split))
    probabilities = forward_probability_batch(
        model=model,
        tokenizer=tokenizer,
        texts=split.texts[:sample_count],
        device="cpu",
        max_length=cpu_model.max_length,
        torch_module=runtime_modules.torch,
    )
    return {
        "status": "cpu_forward_smoke_passed",
        "sample_count": sample_count,
        "sample_ids": list(split.sample_ids[:sample_count]),
        "probabilities": list(probabilities),
    }


def _preflight(
    config_path: Path,
    model_path: Path | None,
) -> tuple[DistilBertBaselineConfig, PreparedFrozenInputs, Mapping[str, object]]:
    config = load_config(config_path)
    if model_path is not None:
        config = with_model_source(config, model_path)
    inputs = prepare_frozen_inputs(config.dataset.root)
    model_binding = validate_model_source(config.model)
    return config, inputs, model_binding


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行共享 B0 DistilBERT 判别式二分类基线")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--model-path", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight-only", action="store_true")
    mode.add_argument("--cpu-forward-smoke", action="store_true")
    mode.add_argument(
        "--gpu-smoke16-output",
        type=Path,
        metavar="DIR",
        help="只读取候选训练与 GeNIS 开发各前 16 条，在独立目录执行单步 GPU 冒烟",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.gpu_smoke16_output is not None:
            config = load_config(args.config)
            if args.model_path is not None:
                config = with_model_source(config, args.model_path)
            inputs = prepare_smoke_inputs(config.dataset.root)
            model_binding = validate_model_source(config.model)
            prepared = prepare_smoke_run(
                config,
                inputs,
                model_binding,
                args.gpu_smoke16_output,
            )
            manifest = execute_smoke_run(prepared)
            print(json.dumps(dict(manifest), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        config, inputs, model_binding = _preflight(args.config, args.model_path)
        if args.preflight_only:
            print(
                json.dumps(
                    {
                        "status": "prepared",
                        "input_binding_sha256": inputs.binding_sha256,
                        "model_binding_sha256": _canonical_sha256(model_binding),
                        "model_runtime_imported": False,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        if args.cpu_forward_smoke:
            print(
                json.dumps(
                    run_cpu_forward_smoke(config, inputs),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        prepared = prepare_run(config, inputs, model_binding)
        manifest = execute_prepared_run(prepared)
        print(json.dumps(dict(manifest), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except UnsupportedRuntimeError as error:
        print(
            json.dumps(
                {"status": "unsupported", "reason": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    except KeyboardInterrupt:
        print(
            json.dumps(
                {"status": "interrupted", "reason": "KeyboardInterrupt"},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 130
    except SharedB0DistilBertError as error:
        print(
            json.dumps(
                {"status": "failed", "reason": str(error)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
