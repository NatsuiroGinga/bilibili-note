"""E2 困难域共享数值编码器与物理辅助训练的正式入口。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import shutil
import sys
import time
import traceback
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import torch
import yaml

from flow_probe.e2_hard_domain_data import (
    E2_FEATURE_FIELDS,
    E2Panel,
    E2Sample,
    build_e2_panel,
    load_e2_development_view,
    samples_to_model_matrix,
)
from flow_probe.e2_hard_domain_metrics import compute_e2_metrics
from flow_probe.e2_shared_pinn import (
    E2_PINN_VARIANTS,
    E2DetectionSourceBinding,
    E2NumericEncoder,
    E2PermutationRecord,
    E2PhysicsFeatureBinding,
    E2PhysicsSupervision,
    E2PinnBudget,
    E2SharedPinnModel,
    E2SharedPinnTrainer,
    assert_shared_parameter_budget,
    assert_shared_training_budget,
    build_e2_physics_feature_binding,
    build_e2_x_permutation,
    ordered_sample_ids_sha256,
    parameter_budget_signature,
    permute_e2_physics_supervision,
    training_budget_signature,
)

SCHEMA_VERSION = "flow_probe_e2_hard_domain_run_v1"
RUN_STATE_SCHEMA = "flow_probe_e2_hard_domain_run_state_v1"
PHYSICS_BINDING_SCHEMA = "flow_probe_e2_physics_binding_v1"
SWANLAB_GATE_SCHEMA = "flow_probe_e2_swanlab_gate_v1"
LEGACY_SWANLAB_EVIDENCE_SCHEMA = "flow_probe_e2_legacy_swanlab_evidence_v1"
FORMAL_LAUNCHER_PREFIX = "e2-hard-domain-"
SWANLAB_GATE_MAX_AGE_SECONDS = 600.0

_SWANLAB_INIT_ATTEMPTED = False


class E2RunError(RuntimeError):
    """E2 正式入口的结构化失败。"""

    def __init__(self, code: str, message: str, **details: object) -> None:
        super().__init__(message)
        self.code = code
        self.details = details

    def to_record(self) -> dict[str, object]:
        return {"code": self.code, "message": str(self), "details": self.details}


@dataclass(frozen=True)
class StateChannelConfig:
    name: str
    start_column: str
    end_column: str
    arrivals_column: str
    departures_column: str
    loss_columns: tuple[str, ...]


@dataclass(frozen=True)
class TrackingConfig:
    workspace: str
    project: str
    mode: str
    run_name: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class DistilBertBindingConfig:
    source: Path
    revision: str
    manifest_path: Path
    checksums_path: Path
    allowed_architectures: tuple[str, ...]


@dataclass(frozen=True)
class E2RunConfig:
    config_path: Path
    seed: int
    panel: str
    variants: tuple[str, ...]
    protocol_dir: Path
    feature_fields: tuple[str, ...]
    physics_root: Path
    physics_table: Path
    physics_sample_key: tuple[str, ...]
    physics_split_column: str
    allowed_physics_splits: tuple[str, ...]
    physics_protocol_column: str
    physics_scene_column: str
    physics_source_domain: str
    physics_feature_columns: tuple[str, ...]
    state_channels: tuple[StateChannelConfig, ...]
    state_supervised_points: tuple[int, ...]
    state_evaluation_points: tuple[int, ...]
    boundary_upper_policy: str
    hidden_size: int
    max_steps: int
    batch_size: int
    evaluation_batch_size: int
    learning_rate: float
    weight_decay: float
    lambda_state: float
    lambda_conservation: float
    lambda_boundary: float
    constraint_tolerance: float
    log_steps: int
    save_steps: int
    device: str
    precision: str
    tracking: TrackingConfig
    distilbert: DistilBertBindingConfig


@dataclass(frozen=True)
class RuntimeSelection:
    device: str
    precision: str
    autocast_enabled: bool


@dataclass(frozen=True)
class DetectionArrays:
    train_features: np.ndarray
    train_labels: np.ndarray
    calibration_features: np.ndarray
    target_features: np.ndarray
    mean: np.ndarray
    scale: np.ndarray


@dataclass(frozen=True)
class PhysicsPool:
    sample_ids: tuple[str, ...]
    features: np.ndarray
    supervision: E2PhysicsSupervision
    records: tuple[E2PermutationRecord, ...]
    binding_sha256: str
    scale_by_channel: tuple[float, ...]
    source_rows: int


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise E2RunError("invalid_config", f"{name} 必须是映射")
    return value


def _require_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise E2RunError("invalid_config", f"{name} 必须是非空字符串")
    return value.strip()


def _require_string_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise E2RunError("invalid_config", f"{name} 必须是非空字符串列表")
    result = tuple(_require_string(item, name) for item in value)
    if len(result) != len(set(result)):
        raise E2RunError("invalid_config", f"{name} 不得包含重复项")
    return result


def _require_positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise E2RunError("invalid_config", f"{name} 必须是正整数")
    return value


def _require_nonnegative_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise E2RunError("invalid_config", f"{name} 必须是非负有限数")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise E2RunError("invalid_config", f"{name} 必须是非负有限数")
    return number


def _resolve_path(value: object, root: Path, name: str) -> Path:
    path = Path(_require_string(value, name)).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _state_channels(value: object) -> tuple[StateChannelConfig, ...]:
    if not isinstance(value, list) or not value:
        raise E2RunError("invalid_config", "physics.state_channels 必须是非空列表")
    result: list[StateChannelConfig] = []
    for index, item in enumerate(value):
        raw = _require_mapping(item, f"physics.state_channels[{index}]")
        result.append(
            StateChannelConfig(
                name=_require_string(raw.get("name"), f"状态通道 {index}.name"),
                start_column=_require_string(
                    raw.get("start_column"), f"状态通道 {index}.start_column"
                ),
                end_column=_require_string(
                    raw.get("end_column"), f"状态通道 {index}.end_column"
                ),
                arrivals_column=_require_string(
                    raw.get("arrivals_column"), f"状态通道 {index}.arrivals_column"
                ),
                departures_column=_require_string(
                    raw.get("departures_column"), f"状态通道 {index}.departures_column"
                ),
                loss_columns=_require_string_tuple(
                    raw.get("loss_columns"), f"状态通道 {index}.loss_columns"
                ),
            )
        )
    names = [item.name for item in result]
    if len(names) != len(set(names)):
        raise E2RunError("invalid_config", "物理状态通道名称不得重复")
    return tuple(result)


def load_config(path: Path, *, project_root: Path) -> E2RunConfig:
    """读取并验证冻结的 E2 运行配置。"""
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = _require_mapping(raw, "配置根")
    if root.get("schema_version") != SCHEMA_VERSION:
        raise E2RunError("invalid_config", "E2 配置模式版本不一致")
    experiment = _require_mapping(root.get("experiment"), "experiment")
    data = _require_mapping(root.get("data"), "data")
    physics = _require_mapping(root.get("physics"), "physics")
    training = _require_mapping(root.get("training"), "training")
    tracking = _require_mapping(root.get("tracking"), "tracking")
    distilbert = _require_mapping(
        root.get("external_distilbert_baseline"), "external_distilbert_baseline"
    )

    seed = _require_positive_int(experiment.get("seed"), "experiment.seed")
    panel = _require_string(experiment.get("panel"), "experiment.panel")
    if panel != "abd_to_c":
        raise E2RunError("invalid_config", "E2 首轮只允许主面板 abd_to_c")
    variants = _require_string_tuple(experiment.get("variants"), "experiment.variants")
    if variants != E2_PINN_VARIANTS:
        raise E2RunError("invalid_config", "四组顺序必须固定为 E2-A/S/P/X")
    feature_fields = _require_string_tuple(data.get("feature_fields"), "data.feature_fields")
    if feature_fields != E2_FEATURE_FIELDS:
        raise E2RunError("invalid_config", "检测输入必须精确使用冻结七字段")
    physics_feature_columns = _require_string_tuple(
        physics.get("feature_columns"), "physics.feature_columns"
    )
    if physics_feature_columns != E2_FEATURE_FIELDS:
        raise E2RunError("invalid_config", "物理批必须使用相同语义和顺序的冻结七字段")

    supervised_points = tuple(
        int(value)
        for value in _require_mapping(physics.get("state_masks"), "physics.state_masks").get(
            "supervised_points", []
        )
    )
    evaluated_points = tuple(
        int(value)
        for value in _require_mapping(physics.get("state_masks"), "physics.state_masks").get(
            "evaluation_points", []
        )
    )
    if supervised_points != (0,) or evaluated_points != (0, 1):
        raise E2RunError(
            "invalid_config",
            "首轮状态掩码必须只监督起点并评价起点与终点",
        )

    boundary_policy = _require_string(
        physics.get("boundary_upper_policy"), "physics.boundary_upper_policy"
    )
    if boundary_policy != "source_physics_train_observed_max":
        raise E2RunError("invalid_config", "物理边界上限策略与冻结合同不一致")
    device = _require_string(training.get("device"), "training.device")
    precision = _require_string(training.get("precision"), "training.precision")
    if device not in {"auto", "cuda", "cpu"}:
        raise E2RunError("invalid_config", "device 只允许 auto、cuda 或 cpu")
    if precision not in {"auto", "float32", "bfloat16"}:
        raise E2RunError("invalid_config", "precision 只允许 auto、float32 或 bfloat16")

    track = TrackingConfig(
        workspace=_require_string(tracking.get("workspace"), "tracking.workspace"),
        project=_require_string(tracking.get("project"), "tracking.project"),
        mode=_require_string(tracking.get("mode"), "tracking.mode"),
        run_name=_require_string(tracking.get("run_name"), "tracking.run_name"),
        tags=_require_string_tuple(tracking.get("tags"), "tracking.tags"),
    )
    if track.mode != "online":
        raise E2RunError("invalid_config", "E2 正式实验必须使用 SwanLab 在线模式")
    if any(len(tag) > 20 for tag in track.tags):
        raise E2RunError("invalid_config", "SwanLab 标签长度不得超过 20 个字符")

    base_binding = DistilBertBindingConfig(
        source=_resolve_path(distilbert.get("source"), project_root, "DistilBERT source"),
        revision=_require_string(distilbert.get("revision"), "DistilBERT revision"),
        manifest_path=_resolve_path(
            distilbert.get("manifest_path"), project_root, "DistilBERT manifest_path"
        ),
        checksums_path=_resolve_path(
            distilbert.get("checksums_path"), project_root, "DistilBERT checksums_path"
        ),
        allowed_architectures=_require_string_tuple(
            distilbert.get("allowed_architectures"), "DistilBERT allowed_architectures"
        ),
    )

    learning_rate = _require_nonnegative_number(
        training.get("learning_rate"), "training.learning_rate"
    )
    if learning_rate <= 0.0:
        raise E2RunError("invalid_config", "learning_rate 必须为正数")
    tolerance = _require_nonnegative_number(
        training.get("constraint_tolerance"), "training.constraint_tolerance"
    )
    if tolerance <= 0.0:
        raise E2RunError("invalid_config", "constraint_tolerance 必须为正数")

    return E2RunConfig(
        config_path=config_path,
        seed=seed,
        panel=panel,
        variants=variants,
        protocol_dir=_resolve_path(data.get("protocol_dir"), project_root, "protocol_dir"),
        feature_fields=feature_fields,
        physics_root=_resolve_path(physics.get("root"), project_root, "physics.root"),
        physics_table=_resolve_path(physics.get("table"), project_root, "physics.table"),
        physics_sample_key=_require_string_tuple(
            physics.get("sample_key"), "physics.sample_key"
        ),
        physics_split_column=_require_string(
            physics.get("split_column"), "physics.split_column"
        ),
        allowed_physics_splits=_require_string_tuple(
            physics.get("allowed_splits"), "physics.allowed_splits"
        ),
        physics_protocol_column=_require_string(
            physics.get("protocol_column"), "physics.protocol_column"
        ),
        physics_scene_column=_require_string(
            physics.get("scene_column"), "physics.scene_column"
        ),
        physics_source_domain=_require_string(
            physics.get("source_domain"), "physics.source_domain"
        ),
        physics_feature_columns=physics_feature_columns,
        state_channels=_state_channels(physics.get("state_channels")),
        state_supervised_points=supervised_points,
        state_evaluation_points=evaluated_points,
        boundary_upper_policy=boundary_policy,
        hidden_size=_require_positive_int(training.get("hidden_size"), "training.hidden_size"),
        max_steps=_require_positive_int(training.get("max_steps"), "training.max_steps"),
        batch_size=_require_positive_int(training.get("batch_size"), "training.batch_size"),
        evaluation_batch_size=_require_positive_int(
            training.get("evaluation_batch_size"), "training.evaluation_batch_size"
        ),
        learning_rate=learning_rate,
        weight_decay=_require_nonnegative_number(
            training.get("weight_decay"), "training.weight_decay"
        ),
        lambda_state=_require_nonnegative_number(
            training.get("lambda_state"), "training.lambda_state"
        ),
        lambda_conservation=_require_nonnegative_number(
            training.get("lambda_conservation"), "training.lambda_conservation"
        ),
        lambda_boundary=_require_nonnegative_number(
            training.get("lambda_boundary"), "training.lambda_boundary"
        ),
        constraint_tolerance=tolerance,
        log_steps=_require_positive_int(training.get("log_steps"), "training.log_steps"),
        save_steps=_require_positive_int(training.get("save_steps"), "training.save_steps"),
        device=device,
        precision=precision,
        tracking=track,
        distilbert=base_binding,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _read_json_mapping(path: Path, *, code: str, label: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise E2RunError(code, f"{label}不存在或不是普通文件", path=str(path))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise E2RunError(code, f"{label}无法解析", path=str(path)) from error
    if not isinstance(value, dict):
        raise E2RunError(code, f"{label}必须是 JSON 对象", path=str(path))
    return value


def _validate_swanlab_gate_receipt(
    path: Path,
    *,
    variant: str,
    attempt: int,
) -> dict[str, object]:
    receipt = _read_json_mapping(
        path,
        code="invalid_swanlab_gate",
        label="SwanLab 门禁收据",
    )
    expected = {
        "schema_version": SWANLAB_GATE_SCHEMA,
        "status": "passed",
        "variant": variant,
        "attempt": attempt,
        "ping_exit": 0,
        "verify_exit": 0,
    }
    mismatches = {
        key: {"expected": expected_value, "actual": receipt.get(key)}
        for key, expected_value in expected.items()
        if receipt.get(key) != expected_value
    }
    checked_at = receipt.get("checked_at")
    if isinstance(checked_at, bool) or not isinstance(checked_at, (int, float)):
        mismatches["checked_at"] = {"expected": "有限时间戳", "actual": checked_at}
    else:
        age_seconds = time.time() - float(checked_at)
        if not math.isfinite(age_seconds) or not (-30.0 <= age_seconds <= SWANLAB_GATE_MAX_AGE_SECONDS):
            mismatches["checked_at"] = {
                "expected": f"最近 {int(SWANLAB_GATE_MAX_AGE_SECONDS)} 秒内",
                "actual_age_seconds": age_seconds,
            }
    if mismatches:
        raise E2RunError(
            "invalid_swanlab_gate",
            "SwanLab 凭据或连通性门禁收据不满足正式运行合同",
            mismatches=mismatches,
        )
    return receipt


def _is_http_unauthorized(error: BaseException) -> bool:
    current: BaseException | None = error
    visited: set[int] = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        response = getattr(current, "response", None)
        if getattr(response, "status_code", None) == 401:
            return True
        status_code = getattr(current, "status_code", None)
        if status_code == 401:
            return True
        message = str(current).lower()
        if "401" in message and ("unauthorized" in message or "未经授权" in message):
            return True
        current = current.__cause__ or current.__context__
    return False


def _append_jsonl(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as target:
        target.write(json.dumps(dict(value), ensure_ascii=False, sort_keys=True) + "\n")
        target.flush()
        os.fsync(target.fileno())


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as target:
        for row in rows:
            target.write(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _resolve_runtime(config: E2RunConfig) -> RuntimeSelection:
    cuda_available = torch.cuda.is_available()
    if config.device == "cuda" and not cuda_available:
        raise E2RunError("cuda_unavailable", "配置要求 CUDA，但当前环境没有可用 CUDA")
    device = "cuda" if config.device == "cuda" or (config.device == "auto" and cuda_available) else "cpu"
    if config.precision == "bfloat16" and device != "cuda":
        precision = "float32"
    elif config.precision == "bfloat16" and not torch.cuda.is_bf16_supported():
        precision = "float32"
    elif config.precision == "auto" and device == "cuda" and torch.cuda.is_bf16_supported():
        precision = "bfloat16"
    else:
        precision = "float32"
    return RuntimeSelection(
        device=device,
        precision=precision,
        autocast_enabled=device == "cuda" and precision == "bfloat16",
    )


def _validate_distilbert_base(binding: DistilBertBindingConfig) -> dict[str, object]:
    """核验外部普通 DistilBERT 基线没有继承旧分类头。"""
    required = (binding.source, binding.manifest_path, binding.checksums_path)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise E2RunError("missing_distilbert_binding", "缺少 DistilBERT 基础模型绑定", paths=missing)
    config_path = binding.source / "config.json"
    if not config_path.is_file():
        raise E2RunError("missing_distilbert_config", "DistilBERT 基础目录缺少 config.json")
    model_config = json.loads(config_path.read_text(encoding="utf-8"))
    architectures = tuple(str(value) for value in model_config.get("architectures", []))
    if not architectures or not set(architectures).issubset(binding.allowed_architectures):
        raise E2RunError(
            "distilbert_classifier_head_detected",
            "DistilBERT 架构不是冻结的基础模型架构",
            architectures=list(architectures),
        )
    forbidden_names = {
        "adapter_config.json",
        "adapter_model.safetensors",
        "optimizer.pt",
        "scheduler.pt",
        "trainer_state.json",
        "training_args.bin",
    }
    discovered = [
        path.name
        for path in binding.source.rglob("*")
        if path.is_file() and (path.name in forbidden_names or "checkpoint-" in str(path))
    ]
    if discovered:
        raise E2RunError(
            "distilbert_finetuned_artifacts_detected",
            "DistilBERT 基础目录含旧微调制品",
            artifacts=sorted(set(discovered)),
        )
    weight_files = tuple(
        path
        for path in sorted(binding.source.iterdir())
        if path.is_file() and path.suffix in {".safetensors", ".bin"}
    )
    if not weight_files:
        raise E2RunError("missing_distilbert_weights", "DistilBERT 基础目录没有权重文件")
    if any(path.suffix == ".bin" for path in weight_files):
        raise E2RunError(
            "uninspectable_distilbert_weights",
            "正式 E2 只接受可检查键名的 safetensors 基础权重",
        )
    try:
        from safetensors import safe_open
    except ImportError as error:
        raise E2RunError("missing_safetensors", "无法检查 DistilBERT 权重键名") from error
    forbidden_keys: list[str] = []
    for weight_path in weight_files:
        with safe_open(weight_path, framework="pt", device="cpu") as handle:
            forbidden_keys.extend(
                key
                for key in handle.keys()
                if key.startswith("classifier.") or key.startswith("pre_classifier.")
            )
    if forbidden_keys:
        raise E2RunError(
            "distilbert_classifier_head_detected",
            "DistilBERT 权重含旧分类头参数",
            keys=forbidden_keys,
        )
    manifest_text = binding.manifest_path.read_text(encoding="utf-8")
    if binding.revision not in manifest_text:
        raise E2RunError("distilbert_revision_mismatch", "模型清单未绑定冻结修订")
    weight_hashes = {path.name: _sha256_file(path) for path in weight_files}
    checksum_text = binding.checksums_path.read_text(encoding="utf-8")
    for name, digest in weight_hashes.items():
        if digest not in checksum_text or name not in checksum_text:
            raise E2RunError(
                "distilbert_weight_hash_mismatch",
                "基础模型权重与校验清单不一致",
                weight=name,
            )
    return {
        "source": str(binding.source),
        "revision": binding.revision,
        "architectures": list(architectures),
        "manifest_sha256": _sha256_file(binding.manifest_path),
        "checksums_sha256": _sha256_file(binding.checksums_path),
        "weight_sha256": weight_hashes,
        "inherited_classifier_head": False,
    }


def _normalise_detection(panel: E2Panel) -> DetectionArrays:
    train = samples_to_model_matrix(panel.train).astype(np.float32)
    calibration = samples_to_model_matrix(panel.calibration).astype(np.float32)
    target = samples_to_model_matrix(panel.target).astype(np.float32)
    mean = train.mean(axis=0, dtype=np.float64).astype(np.float32)
    scale = train.std(axis=0, dtype=np.float64).astype(np.float32)
    scale[scale < 1e-8] = 1.0
    return DetectionArrays(
        train_features=(train - mean) / scale,
        train_labels=np.asarray([sample.label for sample in panel.train], dtype=np.int64),
        calibration_features=(calibration - mean) / scale,
        target_features=(target - mean) / scale,
        mean=mean,
        scale=scale,
    )


def _detection_source_binding(panel: E2Panel) -> E2DetectionSourceBinding:
    data_view_sha256 = _canonical_sha256(
        [
            {
                "sample_id": sample.sample_id,
                "profile": sample.profile,
                "split_id": sample.split_id,
                "label": sample.label,
                "features": list(sample.features),
            }
            for sample in panel.train
        ]
    )
    binding = E2DetectionSourceBinding(
        sample_ids=tuple(sample.sample_id for sample in panel.train),
        profiles=tuple(sample.profile for sample in panel.train),
        split_ids=tuple(sample.split_id for sample in panel.train),
        data_view_sha256=data_view_sha256,
    )
    binding.validate()
    return binding


def _physics_required_columns(config: E2RunConfig) -> tuple[str, ...]:
    columns = [
        *config.physics_sample_key,
        config.physics_split_column,
        config.physics_protocol_column,
        config.physics_scene_column,
        *config.physics_feature_columns,
        "final_test_visible",
    ]
    for channel in config.state_channels:
        columns.extend(
            (
                channel.start_column,
                channel.end_column,
                channel.arrivals_column,
                channel.departures_column,
                *channel.loss_columns,
            )
        )
    return tuple(dict.fromkeys(columns))


def _tensor_sha256(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.dtype).encode("ascii"))
        digest.update(json.dumps(list(contiguous.shape)).encode("ascii"))
        digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _load_physics_pool(config: E2RunConfig, detection: DetectionArrays) -> PhysicsPool:
    if not config.physics_table.is_file():
        raise E2RunError(
            "missing_physics_table",
            "缺少物理辅助表",
            path=str(config.physics_table),
        )
    available = tuple(pd.read_parquet(config.physics_table, columns=[]).columns)
    if not available:
        available = tuple(pd.read_parquet(config.physics_table).columns)
    required = _physics_required_columns(config)
    missing = sorted(set(required).difference(available))
    missing_features = sorted(set(config.physics_feature_columns).difference(available))
    if missing:
        raise E2RunError(
            "missing_physics_columns",
            "物理辅助表不能在不伪造字段的情况下映射到冻结输入与监督",
            table=str(config.physics_table),
            missing_columns=missing,
            missing_model_feature_columns=missing_features,
            available_columns=sorted(available),
        )
    frame = pd.read_parquet(config.physics_table, columns=list(required))
    if bool(frame["final_test_visible"].astype(bool).any()):
        raise E2RunError("physics_final_test_visible", "物理辅助表读取了最终测试")
    allowed = set(config.allowed_physics_splits)
    frame = frame[frame[config.physics_split_column].astype(str).isin(allowed)].copy()
    if frame.empty:
        raise E2RunError("empty_physics_pool", "允许的物理训练划分为空")

    keys = frame.loc[:, config.physics_sample_key].astype(str)
    key_rows = [tuple(row) for row in keys.itertuples(index=False, name=None)]
    if len(key_rows) != len(set(key_rows)):
        raise E2RunError("duplicate_physics_sample_key", "物理样本键不唯一")
    sample_ids = tuple(
        f"physics-{_canonical_sha256({'key': list(key)})[:24]}" for key in key_rows
    )
    raw_features = frame.loc[:, config.physics_feature_columns].to_numpy(dtype=np.float64)
    if not np.isfinite(raw_features).all():
        raise E2RunError("invalid_physics_features", "物理批七字段含非有限值")
    features = ((raw_features - detection.mean) / detection.scale).astype(np.float32)

    state_rows: list[np.ndarray] = []
    arrival_rows: list[np.ndarray] = []
    departure_rows: list[np.ndarray] = []
    loss_rows: list[np.ndarray] = []
    channel_scales: list[float] = []
    for channel in config.state_channels:
        start = frame[channel.start_column].to_numpy(dtype=np.float64)
        end = frame[channel.end_column].to_numpy(dtype=np.float64)
        arrivals = frame[channel.arrivals_column].to_numpy(dtype=np.float64)
        departures = frame[channel.departures_column].to_numpy(dtype=np.float64)
        losses = sum(
            (frame[column].to_numpy(dtype=np.float64) for column in channel.loss_columns),
            start=np.zeros(len(frame), dtype=np.float64),
        )
        values = np.concatenate((start, end, arrivals, departures, losses))
        if not np.isfinite(values).all() or np.any(values < 0):
            raise E2RunError(
                "invalid_physics_supervision",
                "物理状态或通量必须是有限非负数",
                channel=channel.name,
            )
        scale = max(float(np.max(values)), 1.0)
        channel_scales.append(scale)
        state_rows.append(np.stack((start / scale, end / scale), axis=1))
        arrival_rows.append(arrivals[:, None])
        departure_rows.append(departures[:, None])
        loss_rows.append(losses[:, None])
    state_targets = np.stack(state_rows, axis=1).astype(np.float32)
    arrivals_array = np.stack(arrival_rows, axis=1).astype(np.float32)
    departures_array = np.stack(departure_rows, axis=1).astype(np.float32)
    losses_array = np.stack(loss_rows, axis=1).astype(np.float32)
    state_mask = np.zeros_like(state_targets, dtype=bool)
    evaluation_mask = np.zeros_like(state_targets, dtype=bool)
    state_mask[:, :, list(config.state_supervised_points)] = True
    evaluation_mask[:, :, list(config.state_evaluation_points)] = True
    physics_feature_binding = build_e2_physics_feature_binding(
        torch.from_numpy(features), sample_ids
    )
    supervision = E2PhysicsSupervision(
        state_targets=torch.from_numpy(state_targets),
        state_supervision_mask=torch.from_numpy(state_mask),
        state_evaluation_mask=torch.from_numpy(evaluation_mask),
        arrivals=torch.from_numpy(arrivals_array),
        departures=torch.from_numpy(departures_array),
        losses=torch.from_numpy(losses_array),
        normalization_scale=torch.from_numpy(
            np.broadcast_to(
                np.asarray(channel_scales, dtype=np.float32),
                (len(frame), len(config.state_channels)),
            ).copy()
        ),
        conservation_mask=torch.ones_like(torch.from_numpy(arrivals_array), dtype=torch.bool),
        lower_bound=torch.zeros_like(torch.from_numpy(state_targets)),
        upper_bound=torch.ones_like(torch.from_numpy(state_targets)),
        boundary_mask=torch.ones_like(torch.from_numpy(state_targets), dtype=torch.bool),
        sample_ids=sample_ids,
        sample_order_sha256=ordered_sample_ids_sha256(sample_ids),
        feature_binding_sha256=physics_feature_binding.binding_sha256,
        provenance="aligned",
    )
    supervision.validate()
    records = tuple(
        E2PermutationRecord(
            sample_id=sample_id,
            source_domain=config.physics_source_domain,
            protocol=str(protocol),
            scene_condition=str(scene),
            missing_pattern=tuple(bool(value) for value in state_mask[index].flatten()),
        )
        for index, (sample_id, protocol, scene) in enumerate(
            zip(
                sample_ids,
                frame[config.physics_protocol_column].astype(str),
                frame[config.physics_scene_column].astype(str),
                strict=True,
            )
        )
    )
    binding_sha256 = _canonical_sha256(
        {
            "sample_ids": sample_ids,
            "feature_binding_sha256": physics_feature_binding.binding_sha256,
            "supervision_sha256": _tensor_sha256(
                state_targets, arrivals_array, departures_array, losses_array
            ),
            "table_sha256": _sha256_file(config.physics_table),
        }
    )
    return PhysicsPool(
        sample_ids=sample_ids,
        features=features,
        supervision=supervision,
        records=records,
        binding_sha256=binding_sha256,
        scale_by_channel=tuple(channel_scales),
        source_rows=len(frame),
    )


def _balanced_schedule(labels: np.ndarray, *, steps: int, batch_size: int, seed: int) -> tuple[np.ndarray, ...]:
    classes = {label: np.flatnonzero(labels == label) for label in (0, 1)}
    if any(len(indices) == 0 for indices in classes.values()):
        raise E2RunError("single_class_source", "源域训练必须同时含良性和恶意样本")
    rng = np.random.default_rng(seed)
    per_class = (batch_size // 2, batch_size - batch_size // 2)
    return tuple(
        rng.permutation(
            np.concatenate(
                [rng.choice(classes[label], size=per_class[label], replace=True) for label in (0, 1)]
            )
        )
        for _ in range(steps)
    )


def _physics_stratum(record: E2PermutationRecord) -> tuple[object, ...]:
    return (
        record.source_domain,
        record.protocol,
        record.scene_condition,
        record.missing_pattern,
    )


def _physics_schedule(
    records: Sequence[E2PermutationRecord],
    *,
    steps: int,
    batch_size: int,
    seed: int,
) -> tuple[np.ndarray, ...]:
    if batch_size % 2:
        raise E2RunError(
            "odd_physics_batch_size",
            "E2-X 分层无固定点置换要求物理批大小为偶数",
            batch_size=batch_size,
        )
    strata: dict[tuple[object, ...], list[int]] = defaultdict(list)
    for index, record in enumerate(records):
        strata[_physics_stratum(record)].append(index)
    usable = {key: indices for key, indices in strata.items() if len(indices) >= 2}
    if sum(len(indices) // 2 for indices in usable.values()) < batch_size // 2:
        raise E2RunError(
            "insufficient_stratified_physics_samples",
            "物理辅助池无法组成完整的分层无固定点批次",
            batch_size=batch_size,
            usable_rows=sum(len(indices) for indices in usable.values()),
            singleton_strata=sum(len(indices) == 1 for indices in strata.values()),
        )
    rng = np.random.default_rng(seed)
    schedules: list[np.ndarray] = []
    for _ in range(steps):
        pairs: list[tuple[int, int]] = []
        for key in sorted(usable, key=repr):
            shuffled = rng.permutation(usable[key])
            pairs.extend(
                (int(shuffled[offset]), int(shuffled[offset + 1]))
                for offset in range(0, len(shuffled) - 1, 2)
            )
        selected = rng.choice(len(pairs), size=batch_size // 2, replace=False)
        indices = np.asarray(
            [index for pair_index in selected for index in pairs[int(pair_index)]],
            dtype=np.int64,
        )
        schedules.append(rng.permutation(indices))
    return tuple(schedules)


def _select_physics_batch(
    physics: PhysicsPool,
    indices: np.ndarray,
    *,
    variant: str,
    seed: int,
    device: str,
) -> tuple[torch.Tensor, E2PhysicsSupervision, E2PhysicsFeatureBinding]:
    selected = np.asarray(indices, dtype=np.int64)
    tensor_index = torch.from_numpy(selected)
    sample_ids = tuple(physics.sample_ids[int(index)] for index in selected)
    physics_features = torch.from_numpy(physics.features[selected]).to(device=device)
    feature_binding = build_e2_physics_feature_binding(physics_features, sample_ids)

    def take(value: torch.Tensor) -> torch.Tensor:
        return value.index_select(0, tensor_index).to(device=device)

    supervision = E2PhysicsSupervision(
        state_targets=take(physics.supervision.state_targets),
        state_supervision_mask=take(physics.supervision.state_supervision_mask),
        state_evaluation_mask=take(physics.supervision.state_evaluation_mask),
        arrivals=take(physics.supervision.arrivals),
        departures=take(physics.supervision.departures),
        losses=take(physics.supervision.losses),
        normalization_scale=take(physics.supervision.normalization_scale),
        conservation_mask=take(physics.supervision.conservation_mask),
        lower_bound=take(physics.supervision.lower_bound),
        upper_bound=take(physics.supervision.upper_bound),
        boundary_mask=take(physics.supervision.boundary_mask),
        sample_ids=sample_ids,
        sample_order_sha256=ordered_sample_ids_sha256(sample_ids),
        feature_binding_sha256=feature_binding.binding_sha256,
        provenance="aligned",
    )
    supervision.validate()
    if variant == "E2-X":
        records = tuple(physics.records[int(index)] for index in selected)
        permutation = build_e2_x_permutation(records, supervision, seed=seed)
        supervision = permute_e2_physics_supervision(
            supervision,
            permutation,
            records=records,
            seed=seed,
        )
    return physics_features, supervision, feature_binding


def _state_dict_sha256(state_dict: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(state_dict.items()):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(json.dumps(list(value.shape)).encode("ascii"))
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _predict(
    model: E2SharedPinnModel,
    features: np.ndarray,
    *,
    runtime: RuntimeSelection,
    batch_size: int,
) -> np.ndarray:
    model.eval()
    values: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(features), batch_size):
            batch = torch.from_numpy(features[start : start + batch_size]).to(runtime.device)
            with torch.autocast(
                device_type="cuda",
                dtype=torch.bfloat16,
                enabled=runtime.autocast_enabled,
            ):
                logits = model(batch).logits
            values.append(torch.softmax(logits.float(), dim=1)[:, 1].cpu().numpy())
    return np.concatenate(values).astype(np.float64)


def _macro_f1_counts(labels: np.ndarray, probabilities: np.ndarray, threshold: float) -> float:
    predictions = probabilities >= threshold
    values: list[float] = []
    for label in (0, 1):
        true_positive = int(np.sum((labels == label) & (predictions == label)))
        false_positive = int(np.sum((labels != label) & (predictions == label)))
        false_negative = int(np.sum((labels == label) & (predictions != label)))
        denominator = 2 * true_positive + false_positive + false_negative
        values.append(2 * true_positive / denominator if denominator else 0.0)
    return float(np.mean(values))


def _select_threshold(labels: np.ndarray, probabilities: np.ndarray) -> float:
    candidates = np.linspace(0.0, 1.0, 1001)
    return float(
        max(
            candidates,
            key=lambda value: (
                _macro_f1_counts(labels, probabilities, float(value)),
                -abs(float(value) - 0.5),
                -float(value),
            ),
        )
    )


def _prediction_rows(
    samples: Sequence[E2Sample], probabilities: np.ndarray, threshold: float
) -> list[dict[str, object]]:
    return [
        {
            "sample_id": sample.sample_id,
            "capture_id": sample.capture_id,
            "profile": sample.profile,
            "stable_order": sample.stable_order,
            "label": sample.label,
            "probability_malicious": float(probability),
            "threshold": threshold,
            "prediction": int(probability >= threshold),
        }
        for sample, probability in zip(samples, probabilities, strict=True)
    ]


class _SwanLabLogger:
    def __init__(
        self,
        tracking: TrackingConfig,
        *,
        variant: str,
        seed: int,
        attempt: int,
        gate_receipt: Path,
        output_dir: Path,
        config: Mapping[str, object],
    ) -> None:
        global _SWANLAB_INIT_ATTEMPTED

        receipt = _validate_swanlab_gate_receipt(
            gate_receipt,
            variant=variant,
            attempt=attempt,
        )
        _atomic_json(output_dir / "swanlab-gate.json", receipt)
        if _SWANLAB_INIT_ATTEMPTED:
            raise E2RunError(
                "multiple_swanlab_runs_in_process",
                "同一 Python 进程禁止创建第二个 SwanLab 运行；每个 E2 变体必须使用独立进程",
                stage="tracking_init",
                retryable=False,
                variant=variant,
                attempt=attempt,
            )
        _SWANLAB_INIT_ATTEMPTED = True
        try:
            import swanlab
        except ImportError as error:
            raise E2RunError("missing_swanlab", "正式 E2 要求安装 SwanLab") from error
        tags = (*tracking.tags, variant.lower())
        if any(len(tag) > 20 for tag in tags):
            raise E2RunError("invalid_swanlab_tags", "动态 SwanLab 标签超过 20 个字符")
        self.metrics_path = output_dir / "metrics.jsonl"
        self.client = swanlab
        try:
            self.run = swanlab.init(
                project=tracking.project,
                workspace=tracking.workspace,
                name=f"{tracking.run_name}-{variant.lower()}",
                mode=tracking.mode,
                config={**dict(config), "attempt": attempt},
                tags=list(tags),
                group=tracking.run_name,
                job_type="e2-hard-domain-pinn",
                log_dir=str(output_dir / "swanlog"),
            )
        except Exception as error:
            if _is_http_unauthorized(error):
                raise E2RunError(
                    "swanlab_init_unauthorized",
                    "SwanLab 初始化返回 HTTP 401；当前进程立即退出，可由包装器在新进程中有界重试",
                    stage="tracking_init",
                    retryable=True,
                    variant=variant,
                    attempt=attempt,
                ) from error
            raise E2RunError(
                "swanlab_init_failed",
                "SwanLab 初始化失败；当前进程不创建第二次在线会话",
                stage="tracking_init",
                retryable=False,
                variant=variant,
                attempt=attempt,
                exception_type=type(error).__name__,
            ) from error

    def log(self, step: int, event: str, values: Mapping[str, float]) -> None:
        metrics = {str(name): float(value) for name, value in values.items()}
        if any(not math.isfinite(value) for value in metrics.values()):
            raise E2RunError("nonfinite_metric", "逐步指标含非有限值", event=event)
        _append_jsonl(
            self.metrics_path,
            {"step": step, "event": event, "time": time.time(), "metrics": metrics},
        )
        self.client.log(metrics, step=step)

    def finish(self) -> None:
        self.client.finish()


def _checkpoint(
    directory: Path,
    *,
    model: E2SharedPinnModel,
    optimizer: torch.optim.Optimizer,
    variant: str,
    seed: int,
    step: int,
    initial_state_sha256: str,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"checkpoint-{step:06d}.pt"
    temporary = destination.with_suffix(destination.suffix + ".partial")
    torch.save(
        {
            "schema_version": "flow_probe_e2_checkpoint_v1",
            "variant": variant,
            "seed": seed,
            "step": step,
            "initial_state_sha256": initial_state_sha256,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "torch_rng_state": torch.get_rng_state(),
            "numpy_rng_state": np.random.get_state(),
            "python_rng_state": random.getstate(),
        },
        temporary,
    )
    os.replace(temporary, destination)
    return destination


def _build_models(config: E2RunConfig) -> tuple[dict[str, E2SharedPinnModel], str]:
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    template = E2SharedPinnModel(
        input_size=len(E2_FEATURE_FIELDS),
        hidden_size=config.hidden_size,
        state_channels=len(config.state_channels),
        state_points=2,
        encoder=E2NumericEncoder(len(E2_FEATURE_FIELDS), config.hidden_size),
    )
    initial = {name: value.detach().clone() for name, value in template.state_dict().items()}
    initial_hash = _state_dict_sha256(initial)
    models: dict[str, E2SharedPinnModel] = {}
    for variant in config.variants:
        model = E2SharedPinnModel(
            input_size=len(E2_FEATURE_FIELDS),
            hidden_size=config.hidden_size,
            state_channels=len(config.state_channels),
            state_points=2,
            encoder=E2NumericEncoder(len(E2_FEATURE_FIELDS), config.hidden_size),
        )
        model.load_state_dict(initial, strict=True)
        if _state_dict_sha256(model.state_dict()) != initial_hash:
            raise E2RunError("initial_weight_mismatch", "四组未加载完全相同的初始权重")
        models[variant] = model
    assert_shared_parameter_budget(models)
    return models, initial_hash


def _shared_budgets(config: E2RunConfig) -> dict[str, E2PinnBudget]:
    return {
        variant: E2PinnBudget(
            max_steps=config.max_steps,
            batch_size=config.batch_size,
            physics_batch_size=config.batch_size,
            lambda_state=config.lambda_state,
            lambda_conservation=config.lambda_conservation,
            lambda_boundary=config.lambda_boundary,
            constraint_tolerance=config.constraint_tolerance,
        )
        for variant in config.variants
    }


def _input_binding(
    config: E2RunConfig,
    panel: E2Panel,
    physics: PhysicsPool,
    detection_source: E2DetectionSourceBinding,
    physics_schedule: Sequence[np.ndarray],
    budget_signatures: Mapping[str, object],
    runtime: RuntimeSelection,
    base_model: Mapping[str, object],
) -> dict[str, object]:
    source_ids = [sample.sample_id for sample in (*panel.train, *panel.calibration)]
    target_ids = [sample.sample_id for sample in panel.target]
    if set(source_ids).intersection(target_ids):
        raise E2RunError("source_target_overlap", "源域和 C 域样本重叠")
    return {
        "schema_version": "flow_probe_e2_input_binding_v1",
        "panel": config.panel,
        "seed": config.seed,
        "feature_fields": list(config.feature_fields),
        "source_sample_count": len(source_ids),
        "target_sample_count": len(target_ids),
        "source_ids_sha256": _canonical_sha256(source_ids),
        "target_ids_sha256": _canonical_sha256(target_ids),
        "physics_sample_count": len(physics.sample_ids),
        "physics_binding_sha256": physics.binding_sha256,
        "physics_sample_ids_sha256": _canonical_sha256(physics.sample_ids),
        "detection_source_binding_sha256": detection_source.binding_sha256,
        "physics_schedule_sha256": _canonical_sha256(
            [indices.tolist() for indices in physics_schedule]
        ),
        "e2_x_permutation_seed": config.seed,
        "e2_x_permutation_receipt_scope": "per_batch",
        "training_budget_signatures": dict(budget_signatures),
        "device": asdict(runtime),
        "distilbert_base_model": dict(base_model),
        "final_test_visible": False,
    }


def _run_variant(
    *,
    config: E2RunConfig,
    variant: str,
    model: E2SharedPinnModel,
    initial_state_sha256: str,
    budget: E2PinnBudget,
    detection_source: E2DetectionSourceBinding,
    detection: DetectionArrays,
    panel: E2Panel,
    physics: PhysicsPool,
    detection_schedule: tuple[np.ndarray, ...],
    physics_schedule: tuple[np.ndarray, ...],
    runtime: RuntimeSelection,
    output_dir: Path,
    attempt: int,
    gate_receipt: Path,
) -> dict[str, object]:
    variant_dir = output_dir / "variants" / variant.lower()
    variant_dir.mkdir(parents=True, exist_ok=False)
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    model = model.to(runtime.device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    trainer = E2SharedPinnTrainer(
        model=model,
        optimizer=optimizer,
        variant=variant,
        budget=budget,
        detection_source_binding=detection_source,
    )
    logger = _SwanLabLogger(
        config.tracking,
        variant=variant,
        seed=config.seed,
        attempt=attempt,
        gate_receipt=gate_receipt,
        output_dir=variant_dir,
        config={
            "seed": config.seed,
            "panel": config.panel,
            "variant": variant,
            "feature_fields": list(config.feature_fields),
            "max_steps": config.max_steps,
            "batch_size": config.batch_size,
            "initial_state_sha256": initial_state_sha256,
        },
    )
    latest_checkpoint: Path | None = None
    last_result: object | None = None
    try:
        for step, (detection_indices, physics_indices) in enumerate(
            zip(detection_schedule, physics_schedule, strict=True), start=1
        ):
            detection_features = torch.from_numpy(
                detection.train_features[detection_indices]
            ).to(runtime.device)
            labels = torch.from_numpy(detection.train_labels[detection_indices]).to(
                runtime.device
            )
            detection_sample_ids = tuple(
                panel.train[int(index)].sample_id for index in detection_indices
            )
            detection_binding = detection_source.bind_batch(detection_sample_ids)
            physics_features, supervision, physics_binding = _select_physics_batch(
                physics,
                physics_indices,
                variant=variant,
                seed=config.seed,
                device=runtime.device,
            )
            should_log = step == 1 or step % config.log_steps == 0 or step == config.max_steps
            with torch.autocast(
                device_type="cuda",
                dtype=torch.bfloat16,
                enabled=runtime.autocast_enabled,
            ):
                result = trainer.train_step(
                    detection_features=detection_features,
                    physics_features=physics_features,
                    labels=labels,
                    supervision=supervision,
                    detection_binding=detection_binding,
                    physics_binding=physics_binding,
                )
            last_result = result
            encoder_gradient = result.diagnostics.shared_encoder_gradient_norm
            state_gradient = result.diagnostics.state_head_gradient_norm
            if variant in {"E2-P", "E2-X"} and (
                encoder_gradient <= 0.0 or state_gradient <= 0.0
            ):
                raise E2RunError(
                    "zero_physics_gradient",
                    "物理损失未同时连接共享编码器与状态头",
                    variant=variant,
                    step=step,
                    encoder_gradient_norm=encoder_gradient,
                    state_head_gradient_norm=state_gradient,
                )
            if variant == "E2-X":
                receipt = supervision.permutation_receipt
                if receipt is None:
                    raise E2RunError(
                        "missing_permutation_receipt",
                        "E2-X 训练批缺少签名置换收据",
                        step=step,
                    )
                _append_jsonl(
                    variant_dir / "permutation_receipts.jsonl",
                    {
                        "step": step,
                        "source_sample_ids": list(receipt.source_sample_ids),
                        "permuted_sample_ids": list(receipt.permuted_sample_ids),
                        "source_order_sha256": receipt.source_order_sha256,
                        "permuted_order_sha256": receipt.permuted_order_sha256,
                        "permutation_sha256": receipt.permutation_sha256,
                        "source_supervision_sha256": receipt.source_supervision_sha256,
                        "permuted_supervision_sha256": receipt.permuted_supervision_sha256,
                        "stratification_fields": list(receipt.stratification_fields),
                        "seed": receipt.seed,
                    },
                )
            if should_log:
                values = {
                    "train/total_loss": result.total_loss,
                    "train/detection_loss": result.detection_loss,
                    "physics/state_nrmse": result.diagnostics.state_normalized_rmse,
                    "physics/residual": result.diagnostics.dimensionless_residual,
                    "physics/constraint_violation_rate": result.diagnostics.constraint_violation_rate,
                    "physics/shared_encoder_gradient_norm": encoder_gradient,
                    "physics/state_head_gradient_norm": state_gradient,
                }
                if result.state_loss is not None:
                    values["train/state_loss"] = result.state_loss
                if result.conservation_loss is not None:
                    values["train/conservation_loss"] = result.conservation_loss
                if result.boundary_loss is not None:
                    values["train/boundary_loss"] = result.boundary_loss
                logger.log(step, "optimizer_step", values)
            if step % config.save_steps == 0 or step == config.max_steps:
                latest_checkpoint = _checkpoint(
                    variant_dir / "checkpoints",
                    model=model,
                    optimizer=optimizer,
                    variant=variant,
                    seed=config.seed,
                    step=step,
                    initial_state_sha256=initial_state_sha256,
                )

        calibration_probabilities = _predict(
            model,
            detection.calibration_features,
            runtime=runtime,
            batch_size=config.evaluation_batch_size,
        )
        target_probabilities = _predict(
            model,
            detection.target_features,
            runtime=runtime,
            batch_size=config.evaluation_batch_size,
        )
        calibration_labels = np.asarray(
            [sample.label for sample in panel.calibration], dtype=np.int64
        )
        threshold = _select_threshold(calibration_labels, calibration_probabilities)
        calibration_metrics = compute_e2_metrics(
            calibration_labels.tolist(),
            calibration_probabilities.tolist(),
            [sample.capture_id for sample in panel.calibration],
            threshold=threshold,
        )
        target_metrics = compute_e2_metrics(
            [sample.label for sample in panel.target],
            target_probabilities.tolist(),
            [sample.capture_id for sample in panel.target],
            threshold=threshold,
        )
        logger.log(
            config.max_steps + 1,
            "target_evaluation",
            {
                "target/macro_f1": float(target_metrics["macro_f1"]),
                "target/group_equal_macro_f1": float(
                    target_metrics["capture_group_equal_weighted_macro_f1"]
                ),
                "target/worst_group_macro_f1": float(
                    target_metrics["worst_capture_group_macro_f1"]
                ),
                "target/malicious_recall": float(target_metrics["malicious_recall"]),
                "target/benign_false_positive_rate": float(
                    target_metrics["benign_false_positive_rate"]
                ),
            },
        )
        _write_jsonl(
            variant_dir / "predictions" / "source_calibration.jsonl",
            _prediction_rows(panel.calibration, calibration_probabilities, threshold),
        )
        _write_jsonl(
            variant_dir / "predictions" / "target_c.jsonl",
            _prediction_rows(panel.target, target_probabilities, threshold),
        )
        summary = {
            "schema_version": "flow_probe_e2_variant_summary_v1",
            "status": "finished",
            "variant": variant,
            "seed": config.seed,
            "panel": config.panel,
            "threshold": threshold,
            "source_calibration_metrics": calibration_metrics,
            "target_metrics": target_metrics,
            "latest_checkpoint": str(latest_checkpoint),
            "initial_state_sha256": initial_state_sha256,
            "parameter_budget": asdict(parameter_budget_signature(model)),
            "training_budget": asdict(trainer.training_budget),
            "optimization_steps": config.max_steps,
            "detection_batch_size": config.batch_size,
            "physics_batch_size": config.batch_size,
            "last_training_step": asdict(last_result) if last_result is not None else None,
        }
        _atomic_json(variant_dir / "summary.json", summary)
        return summary
    finally:
        logger.finish()


def _write_or_validate_json(
    path: Path,
    value: Mapping[str, object],
    *,
    resume: bool,
    label: str,
) -> None:
    if path.exists() or path.is_symlink():
        existing = _read_json_mapping(
            path,
            code="resume_binding_mismatch",
            label=label,
        )
        if existing != dict(value):
            raise E2RunError(
                "resume_binding_mismatch",
                f"已有{label}与当前运行不一致，拒绝覆盖",
                path=str(path),
            )
        return
    if resume:
        raise E2RunError(
            "resume_binding_missing",
            f"恢复运行缺少{label}",
            path=str(path),
        )
    _atomic_json(path, value)


def _write_or_validate_initial_state(
    path: Path,
    *,
    initial_state_sha256: str,
    state_dict: Mapping[str, torch.Tensor],
    resume: bool,
) -> None:
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise E2RunError(
                "resume_initial_state_mismatch",
                "已有初始权重不是普通文件",
                path=str(path),
            )
        try:
            payload = torch.load(path, map_location="cpu", weights_only=False)
            stored_state = payload["model"]
            stored_sha256 = payload["sha256"]
            actual_sha256 = _state_dict_sha256(stored_state)
        except Exception as error:
            raise E2RunError(
                "resume_initial_state_mismatch",
                "已有初始权重无法验证",
                path=str(path),
            ) from error
        if stored_sha256 != initial_state_sha256 or actual_sha256 != initial_state_sha256:
            raise E2RunError(
                "resume_initial_state_mismatch",
                "已有初始权重摘要与当前运行不一致，拒绝恢复",
                expected_sha256=initial_state_sha256,
                stored_sha256=stored_sha256,
                actual_sha256=actual_sha256,
            )
        return
    if resume:
        raise E2RunError(
            "resume_initial_state_missing",
            "恢复运行缺少共同初始权重",
            path=str(path),
        )
    temporary = path.with_suffix(path.suffix + f".partial.{os.getpid()}")
    torch.save({"sha256": initial_state_sha256, "model": state_dict}, temporary)
    os.replace(temporary, path)


def _require_nonempty_artifact(path: Path, *, variant: str) -> None:
    if path.is_symlink() or not path.is_file() or path.stat().st_size <= 0:
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体缺少必要制品，拒绝跳过或覆盖",
            variant=variant,
            path=str(path),
        )


def _read_jsonl_mappings(path: Path, *, variant: str, label: str) -> list[dict[str, object]]:
    _require_nonempty_artifact(path, variant=variant)
    records: list[dict[str, object]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise E2RunError(
            "finished_variant_incomplete",
            f"已完成变体的{label}无法读取",
            variant=variant,
            path=str(path),
        ) from error
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            raise E2RunError(
                "finished_variant_incomplete",
                f"已完成变体的{label}包含空行",
                variant=variant,
                path=str(path),
                line=line_number,
            )
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise E2RunError(
                "finished_variant_incomplete",
                f"已完成变体的{label}不是合法 JSONL",
                variant=variant,
                path=str(path),
                line=line_number,
            ) from error
        if not isinstance(record, dict):
            raise E2RunError(
                "finished_variant_incomplete",
                f"已完成变体的{label}记录必须是对象",
                variant=variant,
                path=str(path),
                line=line_number,
            )
        records.append(record)
    return records


def _validate_finished_checkpoint(
    path: Path,
    *,
    config: E2RunConfig,
    variant: str,
    initial_state_sha256: str,
    expected_model: E2SharedPinnModel,
) -> None:
    _require_nonempty_artifact(path, variant=variant)
    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as error:
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的最终检查点无法反序列化",
            variant=variant,
            path=str(path),
        ) from error
    if not isinstance(payload, Mapping):
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的最终检查点必须是映射",
            variant=variant,
        )
    expected_fields = {
        "schema_version": "flow_probe_e2_checkpoint_v1",
        "variant": variant,
        "seed": config.seed,
        "step": config.max_steps,
        "initial_state_sha256": initial_state_sha256,
    }
    mismatches = {
        key: {"expected": expected, "actual": payload.get(key)}
        for key, expected in expected_fields.items()
        if payload.get(key) != expected
    }
    if mismatches:
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的最终检查点绑定不一致",
            variant=variant,
            mismatches=mismatches,
        )
    expected_state = expected_model.state_dict()
    model_state = payload.get("model")
    if not isinstance(model_state, Mapping) or set(model_state) != set(expected_state):
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的最终模型参数键与冻结结构不一致",
            variant=variant,
        )
    for name, expected_tensor in expected_state.items():
        actual_tensor = model_state.get(name)
        if (
            not isinstance(actual_tensor, torch.Tensor)
            or actual_tensor.shape != expected_tensor.shape
            or actual_tensor.dtype != expected_tensor.dtype
            or (
                (actual_tensor.is_floating_point() or actual_tensor.is_complex())
                and not bool(torch.isfinite(actual_tensor).all().item())
            )
        ):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的最终模型参数形状、类型或有限性不一致",
                variant=variant,
                parameter=name,
            )
    optimizer = payload.get("optimizer")
    if not isinstance(optimizer, Mapping):
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的最终检查点缺少优化器状态",
            variant=variant,
        )
    optimizer_state = optimizer.get("state")
    parameter_groups = optimizer.get("param_groups")
    named_parameters = list(expected_model.named_parameters())
    expected_parameter_ids = list(range(len(named_parameters)))
    actual_state_ids = set(optimizer_state) if isinstance(optimizer_state, Mapping) else set()
    if (
        not isinstance(optimizer_state, Mapping)
        or not actual_state_ids
        or any(
            isinstance(parameter_id, bool) or not isinstance(parameter_id, int)
            for parameter_id in actual_state_ids
        )
        or not actual_state_ids.issubset(set(expected_parameter_ids))
        or not isinstance(parameter_groups, list)
        or len(parameter_groups) != 1
        or not isinstance(parameter_groups[0], Mapping)
    ):
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的优化器参数状态与冻结变体结构不一致",
            variant=variant,
        )
    parameter_group = parameter_groups[0]
    expected_group_values = {
        "params": expected_parameter_ids,
        "lr": config.learning_rate,
        "weight_decay": config.weight_decay,
        "betas": (0.9, 0.999),
        "eps": 1e-8,
        "amsgrad": False,
        "maximize": False,
    }
    if any(parameter_group.get(key) != value for key, value in expected_group_values.items()):
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的优化器参数组与冻结配置不一致",
            variant=variant,
        )
    for parameter_id in sorted(actual_state_ids):
        state = optimizer_state.get(parameter_id)
        parameter = named_parameters[parameter_id][1]
        if not isinstance(state, Mapping):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的优化器参数状态不是映射",
                variant=variant,
                parameter_id=parameter_id,
            )
        step = state.get("step")
        if isinstance(step, torch.Tensor):
            valid_step = (
                step.numel() == 1
                and bool(torch.isfinite(step).all().item())
                and float(step.item()) == float(config.max_steps)
            )
        else:
            valid_step = (
                not isinstance(step, bool)
                and isinstance(step, (int, float))
                and math.isfinite(float(step))
                and float(step) == float(config.max_steps)
            )
        moments_valid = True
        for field in ("exp_avg", "exp_avg_sq"):
            moment = state.get(field)
            if (
                not isinstance(moment, torch.Tensor)
                or moment.shape != parameter.shape
                or moment.dtype != parameter.dtype
                or not bool(torch.isfinite(moment).all().item())
                or (field == "exp_avg_sq" and bool((moment < 0).any().item()))
            ):
                moments_valid = False
                break
        if not valid_step or not moments_valid:
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的优化器步数或动量状态非法",
                variant=variant,
                parameter_id=parameter_id,
            )

    torch_rng_state = payload.get("torch_rng_state")
    numpy_rng_state = payload.get("numpy_rng_state")
    python_rng_state = payload.get("python_rng_state")
    torch_rng_valid = (
        isinstance(torch_rng_state, torch.Tensor)
        and torch_rng_state.dtype == torch.uint8
        and torch_rng_state.ndim == 1
        and torch_rng_state.numel() > 0
    )
    numpy_rng_valid = (
        isinstance(numpy_rng_state, tuple)
        and len(numpy_rng_state) == 5
        and numpy_rng_state[0] == "MT19937"
        and isinstance(numpy_rng_state[1], np.ndarray)
        and numpy_rng_state[1].dtype == np.uint32
        and numpy_rng_state[1].ndim == 1
        and numpy_rng_state[1].size > 0
        and isinstance(numpy_rng_state[2], int)
        and 0 <= numpy_rng_state[2] <= numpy_rng_state[1].size
        and numpy_rng_state[3] in (0, 1)
        and isinstance(numpy_rng_state[4], (int, float))
        and math.isfinite(float(numpy_rng_state[4]))
    )
    python_rng_valid = (
        isinstance(python_rng_state, tuple)
        and len(python_rng_state) == 3
        and python_rng_state[0] == 3
        and isinstance(python_rng_state[1], tuple)
        and len(python_rng_state[1]) == 625
        and all(isinstance(value, int) for value in python_rng_state[1])
        and 0 <= python_rng_state[1][-1] <= 624
        and (
            python_rng_state[2] is None
            or (
                isinstance(python_rng_state[2], (int, float))
                and math.isfinite(float(python_rng_state[2]))
            )
        )
    )
    if not torch_rng_valid or not numpy_rng_valid or not python_rng_valid:
        for field, valid in (
            ("torch_rng_state", torch_rng_valid),
            ("numpy_rng_state", numpy_rng_valid),
            ("python_rng_state", python_rng_valid),
        ):
            if valid:
                continue
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的最终检查点随机状态非法",
                variant=variant,
                field=field,
            )


def _validate_finished_metrics(path: Path, *, config: E2RunConfig, variant: str) -> None:
    records = _read_jsonl_mappings(path, variant=variant, label="指标日志")
    optimizer_steps: list[int] = []
    target_steps: list[int] = []
    previous_step = -1
    for record in records:
        step = record.get("step")
        event = record.get("event")
        timestamp = record.get("time")
        metrics = record.get("metrics")
        if isinstance(step, bool) or not isinstance(step, int) or step <= previous_step:
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的指标步号必须严格递增",
                variant=variant,
            )
        if not isinstance(event, str) or not event:
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的指标事件非法",
                variant=variant,
                step=step,
            )
        if (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, (int, float))
            or not math.isfinite(float(timestamp))
            or not isinstance(metrics, Mapping)
            or not metrics
        ):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的指标记录结构非法",
                variant=variant,
                step=step,
            )
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in metrics.values()
        ):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的指标含非有限数或非数值",
                variant=variant,
                step=step,
            )
        if event == "optimizer_step":
            optimizer_steps.append(step)
        elif event == "target_evaluation":
            target_steps.append(step)
        else:
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体含未知指标事件",
                variant=variant,
                event=event,
            )
        previous_step = step
    expected_optimizer_steps = [
        step
        for step in range(1, config.max_steps + 1)
        if step == 1 or step % config.log_steps == 0 or step == config.max_steps
    ]
    if optimizer_steps != expected_optimizer_steps or target_steps != [config.max_steps + 1]:
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的指标步集合与冻结日志间隔不一致",
            variant=variant,
            optimizer_steps=optimizer_steps,
            expected_optimizer_steps=expected_optimizer_steps,
            target_steps=target_steps,
        )


def _validate_finished_predictions(
    path: Path,
    *,
    variant: str,
    samples: Sequence[E2Sample],
    threshold: float,
) -> None:
    records = _read_jsonl_mappings(path, variant=variant, label="逐样本预测")
    if len(records) != len(samples):
        raise E2RunError(
            "finished_variant_incomplete",
            "已完成变体的预测数量与冻结开发视图不一致",
            variant=variant,
            expected=len(samples),
            actual=len(records),
        )
    for record, sample in zip(records, samples, strict=True):
        expected_fields = {
            "sample_id": sample.sample_id,
            "capture_id": sample.capture_id,
            "profile": sample.profile,
            "stable_order": sample.stable_order,
            "label": sample.label,
            "threshold": threshold,
        }
        if any(record.get(key) != expected for key, expected in expected_fields.items()):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的预测与冻结样本绑定不一致",
                variant=variant,
                sample_id=sample.sample_id,
            )
        probability = record.get("probability_malicious")
        prediction = record.get("prediction")
        if (
            isinstance(probability, bool)
            or not isinstance(probability, (int, float))
            or not math.isfinite(float(probability))
            or not 0.0 <= float(probability) <= 1.0
            or isinstance(prediction, bool)
            or prediction not in (0, 1)
            or prediction != int(float(probability) >= threshold)
        ):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的预测概率或阈值判定非法",
                variant=variant,
                sample_id=sample.sample_id,
            )


def _load_finished_variant_summaries(
    config: E2RunConfig,
    *,
    output_dir: Path,
    initial_state_sha256: str,
    models: Mapping[str, E2SharedPinnModel],
    budget_signatures: Mapping[str, Mapping[str, object]],
    panel: E2Panel,
) -> dict[str, object]:
    summaries: dict[str, object] = {}
    encountered_gap = False
    for variant in config.variants:
        variant_dir = output_dir / "variants" / variant.lower()
        summary_path = variant_dir / "summary.json"
        if not summary_path.exists() and not summary_path.is_symlink():
            encountered_gap = True
            continue
        if encountered_gap:
            raise E2RunError(
                "noncontiguous_finished_variants",
                "已完成变体不是冻结顺序的连续前缀，拒绝恢复",
                variant=variant,
            )
        if variant_dir.is_symlink() or not variant_dir.is_dir():
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体目录不是普通目录",
                variant=variant,
                path=str(variant_dir),
            )
        summary = _read_json_mapping(
            summary_path,
            code="finished_variant_incomplete",
            label=f"{variant} 完成摘要",
        )
        expected_fields = {
            "schema_version": "flow_probe_e2_variant_summary_v1",
            "status": "finished",
            "variant": variant,
            "seed": config.seed,
            "panel": config.panel,
            "initial_state_sha256": initial_state_sha256,
            "optimization_steps": config.max_steps,
            "detection_batch_size": config.batch_size,
            "physics_batch_size": config.batch_size,
            "parameter_budget": budget_signatures[variant]["parameter_budget"],
            "training_budget": budget_signatures[variant],
        }
        mismatches = {
            key: {"expected": expected, "actual": summary.get(key)}
            for key, expected in expected_fields.items()
            if summary.get(key) != expected
        }
        if mismatches:
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体摘要与当前冻结合同不一致",
                variant=variant,
                mismatches=mismatches,
            )
        final_checkpoint = variant_dir / "checkpoints" / f"checkpoint-{config.max_steps:06d}.pt"
        latest_checkpoint = summary.get("latest_checkpoint")
        if not isinstance(latest_checkpoint, str) or Path(latest_checkpoint).resolve() != (
            final_checkpoint.resolve()
        ):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的最终检查点绑定不一致",
                variant=variant,
                expected=str(final_checkpoint.resolve()),
                actual=latest_checkpoint,
            )
        threshold = summary.get("threshold")
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, (int, float))
            or not math.isfinite(float(threshold))
            or not 0.0 <= float(threshold) <= 1.0
            or not isinstance(summary.get("source_calibration_metrics"), Mapping)
            or not summary.get("source_calibration_metrics")
            or not isinstance(summary.get("target_metrics"), Mapping)
            or not summary.get("target_metrics")
            or not isinstance(summary.get("last_training_step"), Mapping)
        ):
            raise E2RunError(
                "finished_variant_incomplete",
                "已完成变体的阈值、评估摘要或末步状态非法",
                variant=variant,
            )
        _validate_finished_checkpoint(
            final_checkpoint,
            config=config,
            variant=variant,
            initial_state_sha256=initial_state_sha256,
            expected_model=models[variant],
        )
        _validate_finished_metrics(
            variant_dir / "metrics.jsonl",
            config=config,
            variant=variant,
        )
        _validate_finished_predictions(
            variant_dir / "predictions" / "source_calibration.jsonl",
            variant=variant,
            samples=panel.calibration,
            threshold=float(threshold),
        )
        _validate_finished_predictions(
            variant_dir / "predictions" / "target_c.jsonl",
            variant=variant,
            samples=panel.target,
            threshold=float(threshold),
        )
        summaries[variant] = summary
    return summaries


def _unique_archive_directory(root: Path, stem: str) -> Path:
    if root.is_symlink():
        raise E2RunError(
            "unsafe_recovery_archive",
            "恢复归档根不得是符号链接",
            path=str(root),
        )
    root.mkdir(parents=True, exist_ok=True)
    for index in range(1, 1000):
        candidate = root / f"{stem}-{index:03d}"
        if not candidate.exists() and not candidate.is_symlink():
            return candidate
    raise E2RunError("recovery_archive_exhausted", "恢复归档身份已耗尽", stem=stem)


def _legacy_zero_step_tracking_failure(
    receipt_path: Path,
    *,
    output_dir: Path,
    project_root: Path,
    variant: str,
) -> bool:
    if variant != "E2-S":
        return False
    receipt = _read_json_mapping(
        receipt_path,
        code="unsafe_zero_step_recovery",
        label="旧 SwanLab 失败证据收据",
    )
    relative_output = output_dir.resolve().relative_to(project_root.resolve()).as_posix()
    formal_launcher = Path("runs/launchers") / f"{FORMAL_LAUNCHER_PREFIX}{output_dir.name}"
    binding_path = project_root / formal_launcher / "binding.txt"
    log_path = project_root / formal_launcher / "launcher.log"
    expected = {
        "schema_version": LEGACY_SWANLAB_EVIDENCE_SCHEMA,
        "status": "captured",
        "output_dir": relative_output,
        "formal_launcher": formal_launcher.as_posix(),
        "binding_path": binding_path.relative_to(project_root).as_posix(),
        "launcher_log_path": log_path.relative_to(project_root).as_posix(),
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        return False
    for path, hash_field in (
        (binding_path, "binding_sha256"),
        (log_path, "launcher_log_sha256"),
    ):
        if (
            path.is_symlink()
            or not path.is_file()
            or receipt.get(hash_field) != _sha256_file(path)
        ):
            return False
    binding_lines = binding_path.read_text(encoding="utf-8").splitlines()
    if any("=" not in line for line in binding_lines):
        return False
    binding_pairs = [line.split("=", 1) for line in binding_lines]
    binding = {key: value for key, value in binding_pairs}
    # 历史 formal 启动器只写四个键，`mode` 是后续版本才加入的字段；
    # 因此 `mode` 缺失时改由启动器目录命名承担 formal 身份判定。
    required_binding_keys = {"config", "output", "screen", "run_id"}
    if (
        len(binding) != len(binding_pairs)
        or not required_binding_keys <= set(binding)
        or not set(binding) <= required_binding_keys | {"mode"}
    ):
        return False
    if binding.get("mode", "formal") != "formal":
        return False
    if formal_launcher.name.startswith(f"{FORMAL_LAUNCHER_PREFIX}resume-"):
        return False
    if binding["output"] != relative_output:
        return False
    matches = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, Mapping):
            continue
        legacy_text = "\n".join(
            str(record.get(field, "")) for field in ("message", "traceback")
        ).lower()
        if (
            record.get("status") == "failed"
            and record.get("code") == "unhandled_exception"
            and ("unauthorized" in legacy_text or "未经授权" in legacy_text)
            and "_swanlablogger" in legacy_text
            and "swanlab.init" in legacy_text
        ):
            matches.append(record)
    return len(matches) == 1


def _is_zero_step_tracking_failure(
    output_dir: Path,
    *,
    variant: str,
    legacy_failure_evidence: Path | None = None,
    project_root: Path | None = None,
) -> bool:
    failure_path = output_dir / "failure.json"
    if failure_path.exists() or failure_path.is_symlink():
        failure = _read_json_mapping(
            failure_path,
            code="unsafe_zero_step_recovery",
            label="历史失败收据",
        )
        code = failure.get("code")
        details = failure.get("details")
        if code == "swanlab_init_unauthorized" and isinstance(details, Mapping):
            if (
                details.get("stage") == "tracking_init"
                and details.get("variant", failure.get("variant")) == variant
            ):
                return True
        if code == "unhandled_exception":
            legacy_text = "\n".join(
                str(failure.get(field, "")) for field in ("message", "traceback")
            ).lower()
            if (
                ("unauthorized" in legacy_text or "未经授权" in legacy_text)
                and "_swanlablogger" in legacy_text
                and "swanlab.init" in legacy_text
            ):
                return True
    if legacy_failure_evidence is None or project_root is None:
        return False
    return _legacy_zero_step_tracking_failure(
        legacy_failure_evidence,
        output_dir=output_dir,
        project_root=project_root,
        variant=variant,
    )


def _prepare_variant_directory(
    output_dir: Path,
    *,
    variant: str,
    legacy_failure_evidence: Path | None = None,
    project_root: Path | None = None,
) -> Path:
    variant_dir = output_dir / "variants" / variant.lower()
    if not variant_dir.exists() and not variant_dir.is_symlink():
        return variant_dir
    if variant_dir.is_symlink() or not variant_dir.is_dir():
        raise E2RunError(
            "unsafe_variant_directory",
            "变体输出不是普通目录，拒绝恢复",
            variant=variant,
            path=str(variant_dir),
        )
    if (variant_dir / "summary.json").exists() or (variant_dir / "summary.json").is_symlink():
        raise E2RunError(
            "finished_variant_not_skipped",
            "完成变体不得进入失败目录恢复路径",
            variant=variant,
        )
    if not _is_zero_step_tracking_failure(
        output_dir,
        variant=variant,
        legacy_failure_evidence=legacy_failure_evidence,
        project_root=project_root,
    ):
        raise E2RunError(
            "unsafe_zero_step_recovery",
            "未完成变体缺少可验证的 SwanLab 零步初始化失败收据，拒绝归档",
            variant=variant,
        )
    protected_paths = (
        variant_dir / "metrics.jsonl",
        variant_dir / "permutation_receipts.jsonl",
    )
    if any(
        path.is_symlink() or (path.exists() and path.stat().st_size > 0)
        for path in protected_paths
    ):
        raise E2RunError(
            "resume_requires_checkpoint_support",
            "变体已经产生训练指标，当前修复不得猜测训练内恢复状态",
            variant=variant,
        )
    for directory in (variant_dir / "checkpoints", variant_dir / "predictions"):
        if directory.exists() and any(path.is_file() or path.is_symlink() for path in directory.rglob("*")):
            raise E2RunError(
                "resume_requires_checkpoint_support",
                "变体已经产生检查点或预测，当前修复不得覆盖训练证据",
                variant=variant,
                path=str(directory),
            )
    for path in variant_dir.rglob("*"):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(variant_dir)
        if relative == Path("swanlab-gate.json") or relative.parts[0] == "swanlog":
            continue
        raise E2RunError(
            "resume_requires_checkpoint_support",
            "零步恢复目录含非 SwanLab 制品，拒绝自动归档",
            variant=variant,
            path=str(path),
        )
    archive = _unique_archive_directory(
        output_dir / "failed-attempts",
        f"{variant.lower()}-zero-step",
    )
    os.replace(variant_dir, archive)
    _atomic_json(
        archive / "archive-receipt.json",
        {
            "schema_version": "flow_probe_e2_failed_variant_archive_v1",
            "status": "archived",
            "variant": variant,
            "reason": "zero_step_incomplete_variant",
            "source": str(variant_dir),
            "destination": str(archive),
            "archived_at": time.time(),
        },
    )
    return variant_dir


def _archive_previous_failure(output_dir: Path, *, variant: str, attempt: int) -> None:
    failure_path = output_dir / "failure.json"
    if not failure_path.exists() and not failure_path.is_symlink():
        return
    sources: list[tuple[str, Path]] = []
    for name in ("failure.json", "run_state.json", "artifact_manifest.json"):
        source = output_dir / name
        if not source.exists() and not source.is_symlink():
            continue
        if source.is_symlink() or not source.is_file():
            raise E2RunError(
                "unsafe_failure_archive",
                "历史失败状态不是普通文件，拒绝恢复",
                path=str(source),
            )
        sources.append((name, source))
    archive = _unique_archive_directory(
        output_dir / "failure-history",
        f"{variant.lower()}-attempt-{attempt}",
    )
    archive.mkdir()
    archived_files: list[str] = []
    for name, source in sources:
        os.replace(source, archive / name)
        archived_files.append(name)
    _atomic_json(
        archive / "archive-receipt.json",
        {
            "schema_version": "flow_probe_e2_failure_archive_v1",
            "status": "archived",
            "variant": variant,
            "attempt": attempt,
            "files": archived_files,
            "archived_at": time.time(),
        },
    )


def _artifact_manifest(output_dir: Path, *, status: str) -> dict[str, object]:
    artifacts: list[dict[str, object]] = []
    for path in sorted(output_dir.rglob("*")):
        if (
            not path.is_file()
            or ".partial" in path.name
            or path == output_dir / "artifact_manifest.json"
        ):
            continue
        artifacts.append(
            {
                "path": str(path.relative_to(output_dir)),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return {
        "schema_version": "flow_probe_e2_artifact_manifest_v1",
        "status": status,
        "artifacts": artifacts,
    }


def run(
    config: E2RunConfig,
    *,
    variant: str,
    attempt: int,
    gate_receipt: Path,
    output_dir: Path,
    project_root: Path,
    resume: bool,
    legacy_failure_evidence: Path | None = None,
) -> dict[str, object]:
    if variant not in config.variants:
        raise E2RunError("invalid_variant", "E2 变体不在冻结四组中", variant=variant)
    if attempt <= 0:
        raise E2RunError("invalid_attempt", "SwanLab 尝试编号必须为正整数")
    runtime = _resolve_runtime(config)
    base_model_binding = _validate_distilbert_base(config.distilbert)
    samples = load_e2_development_view(config.protocol_dir)
    panel = build_e2_panel(samples, panel=config.panel)
    detection = _normalise_detection(panel)
    detection_source = _detection_source_binding(panel)
    physics = _load_physics_pool(config, detection)
    models, initial_state_sha256 = _build_models(config)
    budgets = _shared_budgets(config)
    assert_shared_training_budget(models, budgets)
    budget_signatures = {
        variant: asdict(training_budget_signature(models[variant], budgets[variant]))
        for variant in config.variants
    }
    detection_schedule = _balanced_schedule(
        detection.train_labels,
        steps=config.max_steps,
        batch_size=config.batch_size,
        seed=config.seed,
    )
    physics_schedule = _physics_schedule(
        physics.records,
        steps=config.max_steps,
        batch_size=config.batch_size,
        seed=config.seed + 100_000,
    )
    binding = _input_binding(
        config,
        panel,
        physics,
        detection_source,
        physics_schedule,
        budget_signatures,
        runtime,
        base_model_binding,
    )
    normalization = {
        "feature_fields": list(config.feature_fields),
        "source_train_mean": detection.mean.tolist(),
        "source_train_scale": detection.scale.tolist(),
        "physics_state_channels": [channel.name for channel in config.state_channels],
        "physics_state_scale": list(physics.scale_by_channel),
        "boundary_upper_policy": config.boundary_upper_policy,
    }
    physics_binding = {
        "schema_version": PHYSICS_BINDING_SCHEMA,
        "table": str(config.physics_table),
        "table_sha256": _sha256_file(config.physics_table),
        "sample_key": list(config.physics_sample_key),
        "sample_count": physics.source_rows,
        "sample_ids_sha256": _canonical_sha256(physics.sample_ids),
        "feature_supervision_binding_sha256": physics.binding_sha256,
        "feature_fields": list(config.physics_feature_columns),
        "permutation_seed": config.seed,
        "permutation_receipt_scope": "per_batch",
        "physics_schedule_sha256": _canonical_sha256(
            [indices.tolist() for indices in physics_schedule]
        ),
        "stratification_fields": [
            "source_domain",
            "protocol",
            "scene_condition",
            "missing_pattern",
        ],
        "final_test_visible": False,
    }
    _write_or_validate_json(
        output_dir / "input_binding.json",
        binding,
        resume=resume,
        label="输入绑定",
    )
    _write_or_validate_json(
        output_dir / "normalization.json",
        normalization,
        resume=resume,
        label="归一化收据",
    )
    _write_or_validate_json(
        output_dir / "physics_binding.json",
        physics_binding,
        resume=resume,
        label="物理绑定",
    )
    initial_path = output_dir / "initial_state.pt"
    _write_or_validate_initial_state(
        initial_path,
        initial_state_sha256=initial_state_sha256,
        state_dict=models["E2-A"].state_dict(),
        resume=resume,
    )
    summaries = _load_finished_variant_summaries(
        config,
        output_dir=output_dir,
        initial_state_sha256=initial_state_sha256,
        models=models,
        budget_signatures=budget_signatures,
        panel=panel,
    )
    if variant in summaries:
        return {
            "status": "already_finished",
            "variant": variant,
            "seed": config.seed,
            "finished_variants": list(summaries),
        }
    next_variant = config.variants[len(summaries)]
    if variant != next_variant:
        raise E2RunError(
            "variant_order_violation",
            "恢复只能执行冻结顺序中的首个未完成变体",
            requested_variant=variant,
            next_variant=next_variant,
            finished_variants=list(summaries),
        )
    _prepare_variant_directory(
        output_dir,
        variant=variant,
        legacy_failure_evidence=legacy_failure_evidence,
        project_root=project_root,
    )
    _archive_previous_failure(output_dir, variant=variant, attempt=attempt)
    _atomic_json(
        output_dir / "run_state.json",
        {
            "schema_version": RUN_STATE_SCHEMA,
            "status": "running",
            "seed": config.seed,
            "current_variant": variant,
            "current_attempt": attempt,
            "finished_variants": list(summaries),
            "updated_at": time.time(),
        },
    )
    summaries[variant] = _run_variant(
        config=config,
        variant=variant,
        model=models[variant],
        initial_state_sha256=initial_state_sha256,
        budget=budgets[variant],
        detection_source=detection_source,
        detection=detection,
        panel=panel,
        physics=physics,
        detection_schedule=detection_schedule,
        physics_schedule=physics_schedule,
        runtime=runtime,
        output_dir=output_dir,
        attempt=attempt,
        gate_receipt=gate_receipt,
    )
    if len(summaries) == len(config.variants):
        summary = {
            "schema_version": "flow_probe_e2_run_summary_v1",
            "status": "finished",
            "seed": config.seed,
            "panel": config.panel,
            "variants": summaries,
            "input_binding_sha256": _sha256_file(output_dir / "input_binding.json"),
            "initial_state_sha256": initial_state_sha256,
            "runtime": asdict(runtime),
        }
        _atomic_json(output_dir / "summary.json", summary)
        state = "finished"
        next_unfinished: str | None = None
    else:
        summary = {
            "status": "variant_finished",
            "variant": variant,
            "seed": config.seed,
            "finished_variants": list(summaries),
        }
        state = "partial"
        next_unfinished = config.variants[len(summaries)]
    _atomic_json(
        output_dir / "run_state.json",
        {
            "schema_version": RUN_STATE_SCHEMA,
            "status": state,
            "seed": config.seed,
            "finished_variants": list(summaries),
            "next_variant": next_unfinished,
            "updated_at": time.time(),
        },
    )
    _atomic_json(output_dir / "artifact_manifest.json", _artifact_manifest(output_dir, status=state))
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行单个 E2 困难域共享数值 PINN 变体")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--variant", choices=E2_PINN_VARIANTS, required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--swanlab-gate-receipt", type=Path, required=True)
    parser.add_argument("--legacy-swanlab-evidence-receipt", type=Path)
    parser.add_argument("--resume", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = args.output_dir.resolve()
    config_path = args.config.resolve()
    if args.resume:
        if output_dir.is_symlink() or not output_dir.is_dir():
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "code": "resume_output_missing",
                        "path": str(output_dir),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
    else:
        if output_dir.exists() or output_dir.is_symlink():
            print(
                json.dumps(
                    {"status": "failed", "code": "output_exists", "path": str(output_dir)},
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
        output_dir.mkdir(parents=True)
    config_copy = output_dir / "config.yaml"
    if args.resume:
        if (
            config_copy.is_symlink()
            or not config_copy.is_file()
            or _sha256_file(config_copy) != _sha256_file(config_path)
        ):
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "code": "resume_config_mismatch",
                        "path": str(config_copy),
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
            return 2
    else:
        shutil.copy2(config_path, config_copy)
        _atomic_json(
            output_dir / "run_state.json",
            {
                "schema_version": RUN_STATE_SCHEMA,
                "status": "prepared",
                "config_sha256": _sha256_file(config_copy),
                "started_at": time.time(),
            },
        )
    try:
        project_root = Path.cwd().resolve()
        config = load_config(config_path, project_root=project_root)
        environment_path = output_dir / "environment.json"
        if args.resume:
            environment_path = (
                output_dir
                / "recovery-environments"
                / f"{args.variant.lower()}-attempt-{args.attempt}-{time.time_ns()}.json"
            )
        _atomic_json(
            environment_path,
            {
                "python": sys.version,
                "platform": platform.platform(),
                "torch": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count(),
                "pid": os.getpid(),
                "variant": args.variant,
                "attempt": args.attempt,
                "resume": args.resume,
            },
        )
        summary = run(
            config,
            variant=args.variant,
            attempt=args.attempt,
            gate_receipt=args.swanlab_gate_receipt.resolve(),
            output_dir=output_dir,
            project_root=project_root,
            resume=args.resume,
            legacy_failure_evidence=(
                args.legacy_swanlab_evidence_receipt.resolve()
                if args.legacy_swanlab_evidence_receipt is not None
                else None
            ),
        )
        print(json.dumps({"status": summary["status"], "summary": summary}, ensure_ascii=False))
        return 0
    except Exception as error:
        failure = (
            error.to_record()
            if isinstance(error, E2RunError)
            else {
                "code": "unhandled_exception",
                "message": str(error),
                "details": {"exception_type": type(error).__name__},
            }
        )
        failure["traceback"] = traceback.format_exc()
        failure["variant"] = args.variant
        failure["attempt"] = args.attempt
        failure["failure_stage"] = (
            failure.get("details", {}).get("stage")
            if isinstance(failure.get("details"), Mapping)
            else None
        )
        failure_directory = output_dir
        if args.resume:
            failure_directory = args.swanlab_gate_receipt.resolve().parent
        else:
            _archive_previous_failure(output_dir, variant=args.variant, attempt=args.attempt)
        failure_stem = f"{args.variant.lower()}-attempt-{args.attempt}-" if args.resume else ""
        _atomic_json(failure_directory / f"{failure_stem}failure.json", failure)
        _atomic_json(
            failure_directory / f"{failure_stem}run_state.json",
            {
                "schema_version": RUN_STATE_SCHEMA,
                "status": "failed",
                "failure_code": failure["code"],
                "failure_stage": failure["failure_stage"],
                "current_variant": args.variant,
                "current_attempt": args.attempt,
                "updated_at": time.time(),
            },
        )
        if not args.resume:
            _atomic_json(
                output_dir / "artifact_manifest.json",
                _artifact_manifest(output_dir, status="failed"),
            )
        print(json.dumps({"status": "failed", **failure}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
