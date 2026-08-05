from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import secrets
import stat
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from flow_probe.r2_final_experts import (
    EXPERT_QUIC,
    EXPERT_SHARED,
    EXPERT_TCP,
    EXPERT_UDP,
    EXPERT_UNKNOWN,
    ROUTE_NAMES,
    ROUTE_TO_INDEX,
    ExpertConfig,
    PhysicsSupervisionBatch,
    ProtocolAdaptivePhysicsSystem,
    UnifiedPhysicsControlSystem,
    count_parameters,
    expert_state_supervision_loss,
    fixed_residual_zero_collapse_receipt,
)


SCHEMA_VERSION = "flow_probe_r2_final_physics_fit_v1"
FIT_MODES = ("formal", "quic-seed-validation")
SPLITS = ("train-fit", "calibration", "validation")


class R2FinalPhysicsFitError(ValueError):
    """表示最终 R2 物理预训练合同被违反。"""


@dataclass(frozen=True)
class ArtifactSpec:
    path: Path
    sha256: str


@dataclass(frozen=True)
class RoleManifestSpec:
    path: Path
    sha256: str
    artifact_id: str
    expected_role: str
    allowed_splits: tuple[str, ...]


@dataclass(frozen=True)
class TruthSpec:
    fields: tuple[str, ...]
    observed_fields: tuple[str, ...]
    scales: tuple[float, ...]


@dataclass(frozen=True)
class DataSpec:
    artifact: ArtifactSpec
    companion_artifacts: Mapping[str, ArtifactSpec]
    artifact_payload_merkle_sha256: str
    role_manifest: RoleManifestSpec
    sequence_id: str
    evaluation_cluster_id: str
    window_index: str
    split_id: str
    route_id: str
    route_confidence: str
    quic_applicable: str
    qlog_truth_available: str
    window_valid: str
    observation_fields: tuple[str, ...]
    observation_scales: tuple[float, ...]
    truths: Mapping[str, TruthSpec]
    window_count: int


@dataclass(frozen=True)
class ModelSpec:
    hidden_dimension: int
    representation_dimension: int
    layer_count: int
    dropout: float
    residual_dimensions: Mapping[str, int]


@dataclass(frozen=True)
class TrainingSpec:
    batch_size: int
    epochs: int
    learning_rate: float
    weight_decay: float
    state_weight: float
    residual_weight: float
    max_grad_norm: float
    save_steps: int
    num_workers: int
    device: str


@dataclass(frozen=True)
class TrackingSpec:
    project: str
    workspace: str
    run_name: str
    mode: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class PhysicsFitConfig:
    mode: str
    seed: int
    data: DataSpec
    model: ModelSpec
    training: TrainingSpec
    tracking: TrackingSpec
    output_dir: Path
    quic_expert_ready_after_fit: bool
    config_path: Path
    file_sha256: str
    project_root: Path


@dataclass(frozen=True)
class PhysicsSplit:
    sequence_ids: tuple[str, ...]
    evaluation_cluster_ids: tuple[str, ...]
    observations: np.ndarray
    valid_mask: np.ndarray
    route_index: np.ndarray
    route_confidence: np.ndarray
    quic_applicable: np.ndarray
    qlog_truth_available: np.ndarray
    truths: Mapping[str, np.ndarray]
    truth_masks: Mapping[str, np.ndarray]

    def __len__(self) -> int:
        return len(self.sequence_ids)


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise R2FinalPhysicsFitError(f"{description} 必须是映射")
    return value


def _string(value: object, description: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise R2FinalPhysicsFitError(f"{description} 必须是非空字符串")
    return value


def _optional_string(value: object, description: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str) or value != value.strip():
        raise R2FinalPhysicsFitError(f"{description} 必须是无首尾空白的字符串或 null")
    return value


def _integer(value: object, description: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise R2FinalPhysicsFitError(f"{description} 必须是不小于 {minimum} 的整数")
    return value


def _number(value: object, description: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R2FinalPhysicsFitError(f"{description} 必须是数值")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise R2FinalPhysicsFitError(f"{description} 必须是不小于 {minimum} 的有限数")
    return result


def _strings(value: object, description: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise R2FinalPhysicsFitError(f"{description} 必须是非空字符串列表")
    return tuple(_string(item, description) for item in value)


def _sha256_string(value: object, description: str) -> str:
    result = _string(value, description)
    if len(result) != 64 or result != result.lower() or any(
        character not in "0123456789abcdef" for character in result
    ):
        raise R2FinalPhysicsFitError(f"{description} 必须是规范的 64 位 SHA-256")
    return result


def _numbers(value: object, description: str) -> tuple[float, ...]:
    if not isinstance(value, list) or not value:
        raise R2FinalPhysicsFitError(f"{description} 必须是非空数值列表")
    return tuple(_number(item, description, minimum=1e-12) for item in value)


def _truth_spec(value: object, description: str) -> TruthSpec:
    raw = _mapping(value, description)
    fields_raw = raw.get("fields")
    observed_raw = raw.get("observed_fields")
    scales_raw = raw.get("scales")
    if not all(isinstance(item, list) for item in (fields_raw, observed_raw, scales_raw)):
        raise R2FinalPhysicsFitError(f"{description} 的字段、掩码和尺度必须是列表")
    fields = tuple(_string(item, f"{description}.fields") for item in fields_raw)
    observed = tuple(
        _string(item, f"{description}.observed_fields") for item in observed_raw
    )
    scales = tuple(
        _number(item, f"{description}.scales", minimum=1e-12)
        for item in scales_raw
    )
    if not (len(fields) == len(observed) == len(scales)):
        raise R2FinalPhysicsFitError(f"{description} 的字段、掩码和尺度长度不一致")
    return TruthSpec(fields=fields, observed_fields=observed, scales=scales)


def _resolve_path(value: object, root: Path, description: str) -> Path:
    path = Path(_string(value, description)).expanduser()
    combined = path if path.is_absolute() else root / path
    return Path(os.path.abspath(os.fspath(combined)))


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _relative_to_trusted_root(
    path: Path,
    trusted_root: Path,
    description: str,
) -> tuple[Path, Path, Path]:
    lexical_path = _lexical_absolute(path)
    root = _lexical_absolute(trusted_root)
    try:
        relative = lexical_path.relative_to(root)
    except ValueError as error:
        raise R2FinalPhysicsFitError(
            f"{description}超出受信任根：{lexical_path}"
        ) from error
    return lexical_path, root, relative


def _require_fixed_config_path(
    config_path: Path,
    trusted_root: Path,
    description: str,
) -> None:
    configs_root = trusted_root / "configs"
    try:
        relative = config_path.relative_to(configs_root)
    except ValueError as error:
        raise R2FinalPhysicsFitError(
            f"{description}必须位于固定配置目录：{configs_root}"
        ) from error
    if len(relative.parts) != 1:
        raise R2FinalPhysicsFitError(
            f"{description}必须是固定配置目录中的直接文件：{config_path}"
        )


@contextmanager
def _open_anchored_directory(
    path: Path,
    description: str,
    *,
    trusted_root: Path,
) -> Any:
    directory, root, relative = _relative_to_trusted_root(
        path,
        trusted_root,
        description,
    )
    directory_flags = (
        os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
    )
    descriptors: list[int] = []
    component_names: list[str] = []
    try:
        try:
            root_descriptor = os.open(root, directory_flags)
        except OSError as error:
            raise R2FinalPhysicsFitError(
                f"{description}无法固定受信任根：{root}"
            ) from error
        descriptors.append(root_descriptor)
        root_stat = os.fstat(root_descriptor)
        if not stat.S_ISDIR(root_stat.st_mode):
            raise R2FinalPhysicsFitError(f"受信任根不是目录：{root}")
        for component in relative.parts:
            if component in ("", ".", ".."):
                raise R2FinalPhysicsFitError(
                    f"{description}包含非法路径组件：{component}"
                )
            parent_descriptor = descriptors[-1]
            try:
                next_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=parent_descriptor,
                )
            except OSError as error:
                raise R2FinalPhysicsFitError(
                    f"{description}父目录无法安全打开：{directory}"
                ) from error
            try:
                opened_stat = os.fstat(next_descriptor)
                named_stat = os.stat(
                    component,
                    dir_fd=parent_descriptor,
                    follow_symlinks=False,
                )
                if (
                    stat.S_ISLNK(named_stat.st_mode)
                    or not stat.S_ISDIR(opened_stat.st_mode)
                    or not stat.S_ISDIR(named_stat.st_mode)
                    or (opened_stat.st_dev, opened_stat.st_ino)
                    != (named_stat.st_dev, named_stat.st_ino)
                ):
                    raise R2FinalPhysicsFitError(
                        f"{description}父目录身份不稳定：{component}"
                    )
            except BaseException:
                os.close(next_descriptor)
                raise
            descriptors.append(next_descriptor)
            component_names.append(component)

        def verify_chain() -> None:
            current_root_stat = os.fstat(descriptors[0])
            try:
                named_root_stat = os.stat(root, follow_symlinks=False)
            except OSError as error:
                raise R2FinalPhysicsFitError(
                    f"{description}受信任根身份无法复核：{root}"
                ) from error
            if (
                stat.S_ISLNK(named_root_stat.st_mode)
                or not stat.S_ISDIR(current_root_stat.st_mode)
                or not stat.S_ISDIR(named_root_stat.st_mode)
                or (current_root_stat.st_dev, current_root_stat.st_ino)
                != (root_stat.st_dev, root_stat.st_ino)
                or (current_root_stat.st_dev, current_root_stat.st_ino)
                != (named_root_stat.st_dev, named_root_stat.st_ino)
            ):
                raise R2FinalPhysicsFitError(
                    f"{description}受信任根身份发生变化：{root}"
                )
            for index, component in enumerate(component_names, start=1):
                opened_stat = os.fstat(descriptors[index])
                try:
                    named_stat = os.stat(
                        component,
                        dir_fd=descriptors[index - 1],
                        follow_symlinks=False,
                    )
                except OSError as error:
                    raise R2FinalPhysicsFitError(
                        f"{description}父目录身份无法复核：{component}"
                    ) from error
                if (
                    stat.S_ISLNK(named_stat.st_mode)
                    or not stat.S_ISDIR(opened_stat.st_mode)
                    or not stat.S_ISDIR(named_stat.st_mode)
                    or (opened_stat.st_dev, opened_stat.st_ino)
                    != (named_stat.st_dev, named_stat.st_ino)
                ):
                    raise R2FinalPhysicsFitError(
                        f"{description}父目录身份发生变化：{component}"
                    )

        verify_chain()
        yield descriptors[-1], verify_chain
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


@contextmanager
def _open_stable_regular_file(
    path: Path,
    description: str,
    *,
    trusted_root: Path,
) -> Any:
    path, root, relative = _relative_to_trusted_root(
        path,
        trusted_root,
        description,
    )
    if not relative.parts:
        raise R2FinalPhysicsFitError(f"{description}不能是受信任根目录")
    with _open_anchored_directory(
        path.parent,
        description,
        trusted_root=root,
    ) as (parent_descriptor, verify_parent_chain):
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        try:
            descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
        except OSError as error:
            raise R2FinalPhysicsFitError(
                f"{description}无法从固定父目录安全打开：{path}"
            ) from error
        source = os.fdopen(descriptor, "rb")
        try:
            before = os.fstat(source.fileno())
            named_before = os.stat(
                path.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if (
                stat.S_ISLNK(named_before.st_mode)
                or not stat.S_ISREG(before.st_mode)
                or not stat.S_ISREG(named_before.st_mode)
                or (before.st_dev, before.st_ino)
                != (named_before.st_dev, named_before.st_ino)
            ):
                raise R2FinalPhysicsFitError(
                    f"{description}文件身份不稳定：{path}"
                )
            verify_parent_chain()
            yield source
            after = os.fstat(source.fileno())
            named_after = os.stat(
                path.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
            if (
                _stat_identity(before) != _stat_identity(after)
                or stat.S_ISLNK(named_after.st_mode)
                or (after.st_dev, after.st_ino)
                != (named_after.st_dev, named_after.st_ino)
            ):
                raise R2FinalPhysicsFitError(
                    f"{description}在读取期间发生变化：{path}"
                )
            verify_parent_chain()
        finally:
            source.close()


def _read_stable_regular_bytes(
    path: Path, description: str, *, trusted_root: Path
) -> bytes:
    with _open_stable_regular_file(
        path, description, trusted_root=trusted_root
    ) as source:
        return source.read()


def load_config(
    path: Path,
    *,
    trusted_root: Path,
    snapshot: bytes | None = None,
) -> PhysicsFitConfig:
    config_path = _lexical_absolute(path)
    project_root = _lexical_absolute(trusted_root)
    _require_fixed_config_path(config_path, project_root, "物理拟合配置")
    config_bytes = (
        _read_stable_regular_bytes(
            config_path, "物理拟合配置", trusted_root=project_root
        )
        if snapshot is None
        else snapshot
    )
    try:
        raw = _mapping(yaml.safe_load(config_bytes.decode("utf-8")), "配置")
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise R2FinalPhysicsFitError("物理拟合配置无法解析") from error
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise R2FinalPhysicsFitError("配置 schema_version 不符合最终物理预训练合同")
    root = project_root
    mode = _string(raw.get("mode"), "mode")
    if mode not in FIT_MODES:
        raise R2FinalPhysicsFitError(f"mode 必须属于 {FIT_MODES}")
    seed = _integer(raw.get("seed"), "seed")
    if seed not in (42, 43, 44):
        raise R2FinalPhysicsFitError("正式物理预训练只允许种子 42、43、44")

    data_raw = _mapping(raw.get("data"), "data")
    artifact_raw = _mapping(data_raw.get("artifact"), "data.artifact")
    artifact = ArtifactSpec(
        path=_resolve_path(artifact_raw.get("path"), root, "data.artifact.path"),
        sha256=_sha256_string(
            artifact_raw.get("sha256"), "data.artifact.sha256"
        ),
    )
    companion_raw = _mapping(
        data_raw.get("companion_artifacts"), "data.companion_artifacts"
    )
    if set(companion_raw) != {"tcp_sender_truth", "udp_window_truth"}:
        raise R2FinalPhysicsFitError(
            "data.companion_artifacts 必须精确覆盖 TCP 发送者级与 UDP 窗口真值"
        )
    companion_artifacts = {
        name: ArtifactSpec(
            path=_resolve_path(
                _mapping(value, f"data.companion_artifacts.{name}").get("path"),
                root,
                f"data.companion_artifacts.{name}.path",
            ),
            sha256=_sha256_string(
                _mapping(value, f"data.companion_artifacts.{name}").get("sha256"),
                f"data.companion_artifacts.{name}.sha256",
            ),
        )
        for name, value in companion_raw.items()
    }
    role_manifest_raw = _mapping(
        data_raw.get("role_manifest"), "data.role_manifest"
    )
    role_manifest = RoleManifestSpec(
        path=_resolve_path(
            role_manifest_raw.get("path"), root, "data.role_manifest.path"
        ),
        sha256=_sha256_string(
            role_manifest_raw.get("sha256"), "data.role_manifest.sha256"
        ),
        artifact_id=_string(
            role_manifest_raw.get("artifact_id"),
            "data.role_manifest.artifact_id",
        ),
        expected_role=_string(
            role_manifest_raw.get("expected_role"),
            "data.role_manifest.expected_role",
        ),
        allowed_splits=_strings(
            role_manifest_raw.get("allowed_splits"),
            "data.role_manifest.allowed_splits",
        ),
    )
    if role_manifest.allowed_splits != SPLITS:
        raise R2FinalPhysicsFitError(
            "data.role_manifest.allowed_splits 必须精确覆盖三个开发划分"
        )
    observations = _strings(
        data_raw.get("observation_fields"), "data.observation_fields"
    )
    observation_scales = _numbers(
        data_raw.get("observation_scales"), "data.observation_scales"
    )
    if len(observations) != len(observation_scales):
        raise R2FinalPhysicsFitError("观测字段和尺度长度不一致")
    truth_raw = _mapping(data_raw.get("truths"), "data.truths")
    expected_truths = {EXPERT_SHARED, EXPERT_TCP, EXPERT_UDP, EXPERT_QUIC}
    if set(truth_raw) != expected_truths:
        raise R2FinalPhysicsFitError("data.truths 必须精确覆盖共享、TCP、UDP、QUIC")
    truths = {
        name: _truth_spec(truth_raw[name], f"data.truths.{name}")
        for name in sorted(expected_truths)
    }
    data = DataSpec(
        artifact=artifact,
        companion_artifacts=companion_artifacts,
        artifact_payload_merkle_sha256=_sha256_string(
            data_raw.get("artifact_payload_merkle_sha256"),
            "data.artifact_payload_merkle_sha256",
        ),
        role_manifest=role_manifest,
        sequence_id=_string(data_raw.get("sequence_id"), "data.sequence_id"),
        evaluation_cluster_id=_string(
            data_raw.get("evaluation_cluster_id"), "data.evaluation_cluster_id"
        ),
        window_index=_string(data_raw.get("window_index"), "data.window_index"),
        split_id=_string(data_raw.get("split_id"), "data.split_id"),
        route_id=_string(data_raw.get("route_id"), "data.route_id"),
        route_confidence=_string(
            data_raw.get("route_confidence"), "data.route_confidence"
        ),
        quic_applicable=_optional_string(
            data_raw.get("quic_applicable"), "data.quic_applicable"
        ),
        qlog_truth_available=_optional_string(
            data_raw.get("qlog_truth_available"), "data.qlog_truth_available"
        ),
        window_valid=_optional_string(
            data_raw.get("window_valid"), "data.window_valid"
        ),
        observation_fields=observations,
        observation_scales=observation_scales,
        truths=truths,
        window_count=_integer(data_raw.get("window_count"), "data.window_count", minimum=1),
    )

    model_raw = _mapping(raw.get("model"), "model")
    residual_raw = _mapping(model_raw.get("residual_dimensions"), "model.residual_dimensions")
    if set(residual_raw) != expected_truths | {EXPERT_UNKNOWN}:
        raise R2FinalPhysicsFitError("残差维数必须精确覆盖五个专家")
    model = ModelSpec(
        hidden_dimension=_integer(model_raw.get("hidden_dimension"), "model.hidden_dimension", minimum=1),
        representation_dimension=_integer(
            model_raw.get("representation_dimension"),
            "model.representation_dimension",
            minimum=1,
        ),
        layer_count=_integer(model_raw.get("layer_count"), "model.layer_count", minimum=1),
        dropout=_number(model_raw.get("dropout"), "model.dropout"),
        residual_dimensions={
            name: _integer(residual_raw[name], f"model.residual_dimensions.{name}", minimum=1)
            for name in sorted(residual_raw)
        },
    )
    if model.dropout >= 1:
        raise R2FinalPhysicsFitError("model.dropout 必须小于 1")

    training_raw = _mapping(raw.get("training"), "training")
    training = TrainingSpec(
        batch_size=_integer(training_raw.get("batch_size"), "training.batch_size", minimum=1),
        epochs=_integer(training_raw.get("epochs"), "training.epochs", minimum=1),
        learning_rate=_number(
            training_raw.get("learning_rate"), "training.learning_rate", minimum=1e-12
        ),
        weight_decay=_number(training_raw.get("weight_decay"), "training.weight_decay"),
        state_weight=_number(training_raw.get("state_weight"), "training.state_weight"),
        residual_weight=_number(
            training_raw.get("residual_weight"), "training.residual_weight"
        ),
        max_grad_norm=_number(
            training_raw.get("max_grad_norm"), "training.max_grad_norm", minimum=1e-12
        ),
        save_steps=_integer(training_raw.get("save_steps"), "training.save_steps", minimum=1),
        num_workers=_integer(training_raw.get("num_workers"), "training.num_workers"),
        device=_string(training_raw.get("device"), "training.device"),
    )

    tracking_raw = _mapping(raw.get("tracking"), "tracking")
    tracking = TrackingSpec(
        project=_string(tracking_raw.get("project"), "tracking.project"),
        workspace=_string(tracking_raw.get("workspace"), "tracking.workspace"),
        run_name=_string(tracking_raw.get("run_name"), "tracking.run_name"),
        mode=_string(tracking_raw.get("mode"), "tracking.mode"),
        tags=_strings(tracking_raw.get("tags"), "tracking.tags"),
    )
    if len(tracking.tags) > 20:
        raise R2FinalPhysicsFitError("SwanLab 标签数量不得超过 20")
    output_dir = _resolve_path(raw.get("output_dir"), root, "output_dir")
    ready_after = raw.get("quic_expert_ready_after_fit")
    if not isinstance(ready_after, bool):
        raise R2FinalPhysicsFitError("quic_expert_ready_after_fit 必须为布尔值")
    if mode == "quic-seed-validation" and ready_after:
        raise R2FinalPhysicsFitError("QUIC 种子验证不得把专家标记为正式就绪")
    return PhysicsFitConfig(
        mode=mode,
        seed=seed,
        data=data,
        model=model,
        training=training,
        tracking=tracking,
        output_dir=output_dir,
        quic_expert_ready_after_fit=ready_after,
        config_path=config_path,
        file_sha256=hashlib.sha256(config_bytes).hexdigest(),
        project_root=project_root,
    )


def _file_sha256(path: Path, *, trusted_root: Path) -> str:
    with _open_stable_regular_file(
        path, "哈希制品", trusted_root=trusted_root
    ) as source:
        return _open_file_sha256(source)


def _open_file_sha256(source: Any) -> str:
    digest = hashlib.sha256()
    source.seek(0)
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
        digest.update(chunk)
    source.seek(0)
    return digest.hexdigest()


def _config_sha256(config: PhysicsFitConfig) -> str:
    value = asdict(config)
    value.pop("config_path")
    value.pop("file_sha256")
    value.pop("project_root")
    value["data"]["artifact"]["path"] = str(config.data.artifact.path)
    for name, artifact in config.data.companion_artifacts.items():
        value["data"]["companion_artifacts"][name]["path"] = str(artifact.path)
    value["data"]["role_manifest"]["path"] = str(
        config.data.role_manifest.path
    )
    value["output_dir"] = str(config.output_dir)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def config_semantic_sha256(config: PhysicsFitConfig) -> str:
    return _config_sha256(config)


def _verify_physics_role_manifest(config: PhysicsFitConfig) -> None:
    spec = config.data.role_manifest
    manifest_path = _lexical_absolute(spec.path)
    manifest_bytes = _read_stable_regular_bytes(
        manifest_path,
        "物理角色清单",
        trusted_root=config.project_root,
    )
    actual_manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    if actual_manifest_sha256 != spec.sha256:
        raise R2FinalPhysicsFitError(
            "物理角色清单 SHA-256 不一致："
            f"预期 {spec.sha256}，实际 {actual_manifest_sha256}"
        )
    try:
        raw = _mapping(
            json.loads(manifest_bytes.decode("utf-8")),
            "物理角色清单",
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise R2FinalPhysicsFitError("物理角色清单无法解析") from error
    if raw.get("schema_version") != "flow_probe_r2_final_physics_role_manifest_v1":
        raise R2FinalPhysicsFitError("物理角色清单 schema_version 非冻结版本")
    if raw.get("final_test_visible") is not False:
        raise R2FinalPhysicsFitError("物理角色清单不得暴露最终测试")
    if raw.get("config_schema_version") != SCHEMA_VERSION:
        raise R2FinalPhysicsFitError("物理角色清单未绑定当前拟合配置身份")
    allowed_modes = _strings(raw.get("allowed_modes"), "物理角色清单.allowed_modes")
    if config.mode not in allowed_modes:
        raise R2FinalPhysicsFitError("当前拟合模式不在物理角色清单允许范围")
    artifact = _mapping(raw.get("artifact"), "物理角色清单.artifact")
    if artifact.get("artifact_id") != spec.artifact_id:
        raise R2FinalPhysicsFitError("物理角色清单制品身份不一致")
    if artifact.get("role") != spec.expected_role:
        raise R2FinalPhysicsFitError("物理真值角色不符合拟合配置")
    if artifact.get("ready") is not True:
        raise R2FinalPhysicsFitError("物理真值角色尚未就绪")
    if (
        artifact.get("artifact_payload_merkle_sha256")
        != config.data.artifact_payload_merkle_sha256
    ):
        raise R2FinalPhysicsFitError("物理角色清单载荷 Merkle 与配置不一致")
    if artifact.get("split_id_column") != config.data.split_id:
        raise R2FinalPhysicsFitError("物理角色清单划分字段不一致")
    declared_splits = _strings(
        artifact.get("allowed_splits"), "物理角色清单.artifact.allowed_splits"
    )
    if declared_splits != spec.allowed_splits or declared_splits != SPLITS:
        raise R2FinalPhysicsFitError("物理角色清单包含最终测试或未知划分")
    declared_path = _resolve_path(
        artifact.get("path"), config.project_root, "物理角色清单.artifact.path"
    )
    if declared_path != _lexical_absolute(config.data.artifact.path):
        raise R2FinalPhysicsFitError("物理角色清单规范路径与配置不一致")
    declared_sha256 = _sha256_string(
        artifact.get("sha256"), "物理角色清单.artifact.sha256"
    )
    if declared_sha256 != config.data.artifact.sha256:
        raise R2FinalPhysicsFitError("物理角色清单制品哈希与配置不一致")
    companions = _mapping(
        artifact.get("companion_artifacts"),
        "物理角色清单.artifact.companion_artifacts",
    )
    if set(companions) != set(config.data.companion_artifacts):
        raise R2FinalPhysicsFitError("物理角色清单伴随真值角色不完整")
    for name, spec_artifact in config.data.companion_artifacts.items():
        declared = _mapping(
            companions[name], f"物理角色清单.artifact.companion_artifacts.{name}"
        )
        expected_role = {
            "tcp_sender_truth": "training_only_privileged_tcp_sender_truth",
            "udp_window_truth": "training_only_privileged_udp_window_truth",
        }[name]
        if declared.get("role") != expected_role:
            raise R2FinalPhysicsFitError(f"物理角色清单伴随制品 {name} 角色非法")
        declared_companion_path = _resolve_path(
            declared.get("path"),
            config.project_root,
            f"物理角色清单伴随制品 {name}.path",
        )
        if declared_companion_path != _lexical_absolute(spec_artifact.path):
            raise R2FinalPhysicsFitError(f"物理角色清单伴随制品 {name} 路径不一致")
        declared_companion_sha256 = _sha256_string(
            declared.get("sha256"), f"物理角色清单伴随制品 {name}.sha256"
        )
        if declared_companion_sha256 != spec_artifact.sha256:
            raise R2FinalPhysicsFitError(f"物理角色清单伴随制品 {name} 哈希不一致")


def _read_verified_parquet(
    artifact: ArtifactSpec,
    description: str,
    config: PhysicsFitConfig,
) -> pd.DataFrame:
    path = artifact.path
    with _open_stable_regular_file(
        path, description, trusted_root=config.project_root
    ) as source:
        actual = _open_file_sha256(source)
        if actual != artifact.sha256:
            raise R2FinalPhysicsFitError(
                f"{description} SHA-256 不一致：预期 {artifact.sha256}，实际 {actual}"
            )
        return pd.read_parquet(source)


def _load_frame(config: PhysicsFitConfig) -> pd.DataFrame:
    _verify_physics_role_manifest(config)
    frame = _read_verified_parquet(config.data.artifact, "物理公共窗口制品", config)
    tcp_truth = _read_verified_parquet(
        config.data.companion_artifacts["tcp_sender_truth"],
        "TCP 发送者级真值制品",
        config,
    )
    udp_truth = _read_verified_parquet(
        config.data.companion_artifacts["udp_window_truth"],
        "UDP 窗口真值制品",
        config,
    )
    join_keys = [config.data.sequence_id, "source_window_index"]
    for description, companion in (
        ("TCP 发送者级真值", tcp_truth),
        ("UDP 窗口真值", udp_truth),
    ):
        missing_keys = sorted(set(join_keys) - set(companion.columns))
        if missing_keys:
            raise R2FinalPhysicsFitError(f"{description}缺少绑定主键：{missing_keys}")
        if not set(companion[config.data.split_id].astype(str)).issubset(SPLITS):
            raise R2FinalPhysicsFitError(f"{description}包含最终测试或未知划分")
        if "final_test_visible" not in companion or bool(
            companion["final_test_visible"].astype(bool).any()
        ):
            raise R2FinalPhysicsFitError(f"{description}未保持最终测试不可见")

    tcp_fields = config.data.truths[EXPERT_TCP]
    udp_fields = config.data.truths[EXPERT_UDP]
    tcp_columns = [
        *join_keys,
        "sender_index",
        *tcp_fields.fields,
        *tcp_fields.observed_fields,
    ]
    udp_columns = [*join_keys, *udp_fields.fields, *udp_fields.observed_fields]
    tcp_common = frame.loc[frame[config.data.route_id].astype(str) == "TCP"].copy()
    udp_common = frame.loc[frame[config.data.route_id].astype(str) == "UDP"].copy()
    tcp_frame = tcp_common.merge(
        tcp_truth[tcp_columns], on=join_keys, how="inner", validate="one_to_many"
    )
    udp_frame = udp_common.merge(
        udp_truth[udp_columns], on=join_keys, how="inner", validate="one_to_one"
    )
    if len(tcp_frame) != len(tcp_truth) or len(udp_frame) != len(udp_truth):
        raise R2FinalPhysicsFitError("v2 公共窗口与协议真值主键绑定不完整")
    for field, observed_field in zip(
        tcp_fields.fields, tcp_fields.observed_fields, strict=True
    ):
        observed = _strict_bool_series(
            tcp_frame[observed_field], f"TCP 发送者级真值 {observed_field}"
        )
        if bool(tcp_frame.loc[observed, field].isna().any()):
            raise R2FinalPhysicsFitError(f"TCP 已观察字段 {field} 包含空值")
        tcp_frame[field] = tcp_frame[field].fillna(0.0)
    tcp_frame[config.data.sequence_id] = (
        tcp_frame[config.data.sequence_id].astype(str)
        + ":sender-"
        + tcp_frame["sender_index"].astype(int).astype(str)
    )
    for field in (*udp_fields.fields, *udp_fields.observed_fields):
        tcp_frame[field] = False if field in udp_fields.observed_fields else 0.0
    for field in (*tcp_fields.fields, *tcp_fields.observed_fields):
        udp_frame[field] = False if field in tcp_fields.observed_fields else 0.0
    frame = pd.concat((tcp_frame, udp_frame), ignore_index=True, sort=False)
    required = {
        config.data.sequence_id,
        config.data.evaluation_cluster_id,
        config.data.window_index,
        config.data.split_id,
        config.data.route_id,
        config.data.route_confidence,
        *config.data.observation_fields,
    }
    required.update(
        field
        for field in (
            config.data.quic_applicable,
            config.data.qlog_truth_available,
            config.data.window_valid,
        )
        if field
    )
    for truth in config.data.truths.values():
        required.update(truth.fields)
        required.update(truth.observed_fields)
    missing = sorted(required - set(frame.columns))
    if missing:
        raise R2FinalPhysicsFitError(f"物理真值制品缺少字段：{missing}")
    if not set(frame[config.data.split_id].astype(str)).issubset(SPLITS):
        raise R2FinalPhysicsFitError("物理真值制品包含最终测试或未知划分")
    if "final_test_visible" not in frame or bool(
        frame["final_test_visible"].astype(bool).any()
    ):
        raise R2FinalPhysicsFitError("物理真值制品未保持最终测试不可见")
    return frame


def _scaled_matrix(frame: pd.DataFrame, fields: Sequence[str], scales: Sequence[float]) -> np.ndarray:
    values = frame[list(fields)].to_numpy(dtype=np.float32)
    values = values / np.asarray(scales, dtype=np.float32)[None, :]
    if not np.isfinite(values).all():
        raise R2FinalPhysicsFitError("缩放后的物理张量包含非有限值")
    return values


def _strict_bool_series(values: pd.Series, description: str) -> np.ndarray:
    if values.isna().any():
        raise R2FinalPhysicsFitError(f"{description}包含空值")
    if pd.api.types.is_bool_dtype(values.dtype):
        return values.to_numpy(dtype=bool)
    if pd.api.types.is_numeric_dtype(values.dtype):
        numeric = values.to_numpy()
        if np.isin(numeric, (0, 1)).all():
            return numeric == 1
    raise R2FinalPhysicsFitError(f"{description}只允许原生布尔或精确 0/1")


def _build_split(frame: pd.DataFrame, config: PhysicsFitConfig, split: str) -> PhysicsSplit:
    data = config.data
    current = frame.loc[frame[data.split_id].astype(str) == split].copy()
    if current.empty:
        raise R2FinalPhysicsFitError(f"物理划分 {split} 不能为空")
    groups = list(current.groupby(data.sequence_id, sort=True))
    observations: list[np.ndarray] = []
    valid_masks: list[np.ndarray] = []
    routes: list[int] = []
    confidences: list[float] = []
    quic_applicable: list[bool] = []
    qlog_available: list[bool] = []
    truth_values: dict[str, list[np.ndarray]] = {name: [] for name in data.truths}
    truth_masks: dict[str, list[np.ndarray]] = {name: [] for name in data.truths}
    sequence_ids: list[str] = []
    evaluation_cluster_ids: list[str] = []
    for sequence_id, group in groups:
        ordered = group.sort_values(data.window_index, kind="mergesort")
        indices = ordered[data.window_index].astype(int).tolist()
        if indices != list(range(data.window_count)):
            raise R2FinalPhysicsFitError(f"序列 {sequence_id} 的窗口索引不连续")
        route_names = tuple(ordered[data.route_id].astype(str).unique())
        if len(route_names) != 1 or route_names[0] not in ROUTE_TO_INDEX:
            raise R2FinalPhysicsFitError(f"序列 {sequence_id} 的协议路由非法")
        route_name = route_names[0]
        if config.mode == "formal" and route_name == "QUIC":
            raise R2FinalPhysicsFitError("正式物理预训练不得混入种子级 QUIC 数据")
        if config.mode == "quic-seed-validation" and route_name != "QUIC":
            raise R2FinalPhysicsFitError("QUIC 种子验证只允许 QUIC 序列")
        confidence_values = ordered[data.route_confidence].to_numpy(dtype=np.float32)
        if not np.isfinite(confidence_values).all() or np.any(
            (confidence_values < 0) | (confidence_values > 1)
        ):
            raise R2FinalPhysicsFitError(f"序列 {sequence_id} 的路由置信度非法")
        valid = (
            _strict_bool_series(
                ordered[data.window_valid],
                f"序列 {sequence_id} 的有效窗口",
            )
            if data.window_valid
            else np.ones(data.window_count, dtype=bool)
        )
        length = int(valid.sum())
        if length <= 0 or not np.array_equal(
            valid, np.arange(data.window_count) < length
        ):
            raise R2FinalPhysicsFitError(f"序列 {sequence_id} 的有效窗口不是非空前缀")
        observations.append(
            _scaled_matrix(ordered, data.observation_fields, data.observation_scales)
        )
        valid_masks.append(valid)
        routes.append(ROUTE_TO_INDEX[route_name])
        confidences.append(float(confidence_values[-1]))
        quic_applicable.append(
            bool(
                _strict_bool_series(
                    ordered[data.quic_applicable],
                    f"序列 {sequence_id} 的 QUIC 适用掩码",
                ).all()
            )
            if data.quic_applicable
            else False
        )
        qlog_available.append(
            bool(
                _strict_bool_series(
                    ordered[data.qlog_truth_available],
                    f"序列 {sequence_id} 的 qlog 真值掩码",
                ).all()
            )
            if data.qlog_truth_available
            else False
        )
        sequence_ids.append(str(sequence_id))
        cluster_values = tuple(ordered[data.evaluation_cluster_id].astype(str).unique())
        if len(cluster_values) != 1 or not cluster_values[0]:
            raise R2FinalPhysicsFitError(
                f"序列 {sequence_id} 的 evaluation_cluster_id 非法"
            )
        evaluation_cluster_ids.append(cluster_values[0])
        for name, spec in data.truths.items():
            if spec.fields:
                values = _scaled_matrix(ordered, spec.fields, spec.scales)
                observed = np.column_stack(
                    [
                        _strict_bool_series(
                            ordered[field],
                            f"序列 {sequence_id} 的 {field}",
                        )
                        for field in spec.observed_fields
                    ]
                )
            else:
                values = np.zeros((data.window_count, 1), dtype=np.float32)
                observed = np.zeros((data.window_count, 1), dtype=bool)
            truth_values[name].append(values)
            truth_masks[name].append(observed)
    return PhysicsSplit(
        sequence_ids=tuple(sequence_ids),
        evaluation_cluster_ids=tuple(evaluation_cluster_ids),
        observations=np.stack(observations),
        valid_mask=np.stack(valid_masks),
        route_index=np.asarray(routes, dtype=np.int64),
        route_confidence=np.asarray(confidences, dtype=np.float32),
        quic_applicable=np.asarray(quic_applicable, dtype=bool),
        qlog_truth_available=np.asarray(qlog_available, dtype=bool),
        truths={name: np.stack(values) for name, values in truth_values.items()},
        truth_masks={name: np.stack(values) for name, values in truth_masks.items()},
    )


def load_splits(config: PhysicsFitConfig) -> Mapping[str, PhysicsSplit]:
    frame = _load_frame(config)
    return {split: _build_split(frame, config, split) for split in SPLITS}


def _expert_config(config: PhysicsFitConfig, name: str) -> ExpertConfig:
    state_dimension = 1 if name == EXPERT_UNKNOWN else max(
        len(config.data.truths[name].fields),
        5 if name == EXPERT_SHARED else 1,
    )
    return ExpertConfig(
        name=name,
        input_dimension=len(config.data.observation_fields),
        hidden_dimension=config.model.hidden_dimension,
        representation_dimension=config.model.representation_dimension,
        state_dimension=state_dimension,
        residual_dimension=config.model.residual_dimensions[name],
        layer_count=config.model.layer_count,
        dropout=config.model.dropout,
        enabled=True,
        required_truth_fields=(
            tuple() if name == EXPERT_UNKNOWN else config.data.truths[name].fields
        ),
    )


def build_system(config: PhysicsFitConfig) -> Any:
    return ProtocolAdaptivePhysicsSystem(
        shared=_expert_config(config, EXPERT_SHARED),
        tcp=_expert_config(config, EXPERT_TCP),
        udp=_expert_config(config, EXPERT_UDP),
        quic=_expert_config(config, EXPERT_QUIC),
        unknown=_expert_config(config, EXPERT_UNKNOWN),
        quic_expert_ready=False,
    )


def build_unified_control_system(config: PhysicsFitConfig) -> Any:
    """构建与正式 TCP/UDP 活跃支路精确等容量的非路由控制支路。"""

    if config.mode != "formal":
        raise R2FinalPhysicsFitError("统一物理控制支路只用于正式 TCP/UDP 比较")
    return UnifiedPhysicsControlSystem(
        shared=_expert_config(config, EXPERT_SHARED),
        tcp_shape=_expert_config(config, EXPERT_TCP),
        udp_shape=_expert_config(config, EXPERT_UDP),
    )


def build_history_control_system(config: PhysicsFitConfig) -> Any:
    """构建只受状态监督、不最小化物理残差的历史控制支路。"""

    if config.mode != "formal":
        raise R2FinalPhysicsFitError("历史控制支路只用于正式 TCP/UDP 比较")
    return build_system(config)


class _IndexDataset:
    def __init__(self, size: int) -> None:
        self.size = size

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, index: int) -> int:
        return index


def _loader(split: PhysicsSplit, config: PhysicsFitConfig, torch: Any, *, shuffle: bool) -> Any:
    generator = torch.Generator()
    generator.manual_seed(config.seed)
    return torch.utils.data.DataLoader(
        _IndexDataset(len(split)),
        batch_size=config.training.batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=config.training.num_workers,
        pin_memory=bool(torch.cuda.is_available()),
        persistent_workers=bool(config.training.num_workers),
    )


def _tensor_batch(split: PhysicsSplit, indices: Any, torch: Any, device: Any) -> dict[str, Any]:
    values = np.asarray(indices, dtype=np.int64)
    return {
        "observations": torch.tensor(split.observations[values], dtype=torch.float32, device=device),
        "valid": torch.tensor(split.valid_mask[values], dtype=torch.bool, device=device),
        "route": torch.tensor(split.route_index[values], dtype=torch.int64, device=device),
        "qlog": torch.tensor(
            split.qlog_truth_available[values], dtype=torch.bool, device=device
        ),
        "truths": {
            name: torch.tensor(array[values], dtype=torch.float32, device=device)
            for name, array in split.truths.items()
        },
        "masks": {
            name: torch.tensor(array[values], dtype=torch.bool, device=device)
            for name, array in split.truth_masks.items()
        },
    }


def _residual_loss(output: Any, torch: Any) -> Any:
    active = output.valid_mask & output.active_mask[:, None]
    if not bool(active.any().item()):
        return output.physics_residual.sum() * 0.0
    return torch.square(output.physics_residual[active]).mean()


def _component_losses(
    outputs: Mapping[str, Any],
    batch: Mapping[str, Any],
    config: PhysicsFitConfig,
    torch: Any,
    *,
    prefix: str,
    include_residual: bool = True,
) -> tuple[Any, dict[str, float]]:
    total = batch["observations"].sum() * 0.0
    scalars: dict[str, float] = {}
    for name, output in outputs.items():
        supervision = PhysicsSupervisionBatch(
            truth_state=batch["truths"][name],
            truth_mask=batch["masks"][name],
            qlog_truth_available=batch["qlog"],
        )
        state = expert_state_supervision_loss(output, supervision, expert_name=name)
        residual = _residual_loss(output, torch)
        total = total + config.training.state_weight * state
        if include_residual:
            total = total + config.training.residual_weight * residual
        scalars[f"{prefix}/{name}/state_loss"] = float(
            state.detach().float().item()
        )
        scalars[f"{prefix}/{name}/residual_loss"] = float(
            residual.detach().float().item()
        )
    scalars[f"{prefix}/loss"] = float(total.detach().float().item())
    return total, scalars


def _losses(
    system: Any,
    unified_control: Any | None,
    history_control: Any | None,
    batch: Mapping[str, Any],
    config: PhysicsFitConfig,
    torch: Any,
) -> tuple[Any, dict[str, float]]:
    observations = batch["observations"]
    valid = batch["valid"]
    route = batch["route"]
    qlog = batch["qlog"]
    outputs: dict[str, Any] = {}
    if config.mode == "formal":
        outputs[EXPERT_SHARED] = system.shared(observations, valid)
        active_experts = (("TCP", EXPERT_TCP), ("UDP", EXPERT_UDP))
    else:
        active_experts = (("QUIC", EXPERT_QUIC),)
    for route_name, expert_name in active_experts:
        active = route == ROUTE_TO_INDEX[route_name]
        outputs[expert_name] = system.protocol_experts[route_name](
            observations, valid, active
        )
    total, scalars = _component_losses(
        outputs, batch, config, torch, prefix="routed"
    )
    if config.mode == "formal":
        if unified_control is None or history_control is None:
            raise R2FinalPhysicsFitError("正式训练缺少统一或历史控制支路")
        unified_output = unified_control(observations, valid)
        unified_outputs = {
            EXPERT_SHARED: unified_output.shared,
            EXPERT_TCP: unified_output.protocol_outputs["TCP"],
            EXPERT_UDP: unified_output.protocol_outputs["UDP"],
        }
        unified_loss, unified_scalars = _component_losses(
            unified_outputs, batch, config, torch, prefix="unified"
        )
        total = total + unified_loss
        scalars.update(unified_scalars)
        history_outputs = {EXPERT_SHARED: history_control.shared(observations, valid)}
        for route_name, expert_name in (("TCP", EXPERT_TCP), ("UDP", EXPERT_UDP)):
            active = route == ROUTE_TO_INDEX[route_name]
            history_outputs[expert_name] = history_control.protocol_experts[route_name](
                observations, valid, active
            )
        history_loss, history_scalars = _component_losses(
            history_outputs,
            batch,
            config,
            torch,
            prefix="history",
            include_residual=False,
        )
        total = total + history_loss
        scalars.update(history_scalars)
    scalars["loss"] = float(total.detach().float().item())
    return total, scalars


def _evaluate(
    system: Any,
    unified_control: Any | None,
    history_control: Any | None,
    split: PhysicsSplit,
    config: PhysicsFitConfig,
    torch: Any,
    device: Any,
) -> Mapping[str, float]:
    totals: dict[str, float] = {}
    count = 0
    system.eval()
    if unified_control is not None:
        unified_control.eval()
    if history_control is not None:
        history_control.eval()
    with torch.no_grad():
        for indices in _loader(split, config, torch, shuffle=False):
            batch = _tensor_batch(split, indices, torch, device)
            _, scalars = _losses(
                system, unified_control, history_control, batch, config, torch
            )
            weight = len(indices)
            count += weight
            for name, value in scalars.items():
                totals[name] = totals.get(name, 0.0) + value * weight
    return {name: value / count for name, value in totals.items()}


class _MetricLogger:
    def __init__(self, config: PhysicsFitConfig) -> None:
        self.path = config.output_dir / "metrics.jsonl"
        self.run: Any | None = None
        if config.tracking.mode == "online":
            try:
                import swanlab
            except ImportError as error:
                raise R2FinalPhysicsFitError("在线训练要求安装 SwanLab") from error
            self.run = swanlab.init(
                project=config.tracking.project,
                workspace=config.tracking.workspace,
                experiment_name=config.tracking.run_name,
                config={"mode": config.mode, "seed": config.seed},
                tags=list(config.tracking.tags),
            )

    def log(self, values: Mapping[str, float], *, step: int, event: str) -> None:
        row = {"step": step, "event": event, "time": time.time(), **values}
        with self.path.open("a", encoding="utf-8") as target:
            target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        if self.run is not None:
            import swanlab

            swanlab.log(dict(values), step=step)

    def finish(self) -> None:
        if self.run is not None:
            import swanlab

            swanlab.finish()


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _module_parameter_receipt(module: Any) -> Mapping[str, int]:
    total = count_parameters(module)
    trainable = count_parameters(module, trainable_only=True)
    return {"total": total, "trainable": trainable, "frozen": total - trainable}


def _parameter_receipt(
    system: Any,
    unified_control: Any | None,
    history_control: Any | None,
) -> Mapping[str, object]:
    routed_active = (
        system.shared,
        system.protocol_experts["TCP"],
        system.protocol_experts["UDP"],
    )
    routed_total = sum(count_parameters(module) for module in routed_active)
    routed_trainable = sum(
        count_parameters(module, trainable_only=True) for module in routed_active
    )
    routed = {
        "total": routed_total,
        "trainable": routed_trainable,
        "frozen": routed_total - routed_trainable,
    }
    unified = (
        _module_parameter_receipt(unified_control)
        if unified_control is not None
        else {"total": 0, "trainable": 0, "frozen": 0}
    )
    history = (
        {
            "total": sum(
                count_parameters(module)
                for module in (
                    history_control.shared,
                    history_control.protocol_experts["TCP"],
                    history_control.protocol_experts["UDP"],
                )
            ),
            "trainable": sum(
                count_parameters(module, trainable_only=True)
                for module in (
                    history_control.shared,
                    history_control.protocol_experts["TCP"],
                    history_control.protocol_experts["UDP"],
                )
            ),
            "frozen": 0,
        }
        if history_control is not None
        else {"total": 0, "trainable": 0, "frozen": 0}
    )
    history["frozen"] = int(history["total"]) - int(history["trainable"])
    equal = bool(routed == unified)
    if unified_control is not None and not equal:
        raise R2FinalPhysicsFitError(
            f"F-A/F-P 活跃支路容量不相等：routed={routed}, unified={unified}"
        )
    return {
        "comparison_scope": "formal_active_shared_tcp_udp_v1",
        "routed_active": routed,
        "unified_control": unified,
        "history_control": history,
        "equal_total_trainable_frozen": equal,
        "routed_full": _module_parameter_receipt(system),
        "excluded_dormant": {
            "quic": _module_parameter_receipt(system.protocol_experts["QUIC"]),
            "unknown": _module_parameter_receipt(system.protocol_experts["UNKNOWN"]),
        },
    }


def _checkpoint(
    system: Any,
    unified_control: Any | None,
    history_control: Any | None,
    optimizer: Any,
    config: PhysicsFitConfig,
    torch: Any,
    step: int,
    epoch: int,
) -> None:
    capacity = _parameter_receipt(system, unified_control, history_control)
    residual_receipt = fixed_residual_zero_collapse_receipt(system)
    if not bool(residual_receipt["formal_tcp_udp_dynamics_ready"]):
        raise R2FinalPhysicsFitError("未通过固定残差零坍缩门禁，不得写正式检查点")
    fit_config_sha256 = config.file_sha256
    checkpoint_binding = {
        "config_sha256": _config_sha256(config),
        "fit_config_sha256": fit_config_sha256,
        "input_sha256": config.data.artifact_payload_merkle_sha256,
        "seed": config.seed,
        "mode": config.mode,
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "config_sha256": _config_sha256(config),
        "fit_config_sha256": fit_config_sha256,
        "step": step,
        "epoch": epoch,
        "routed_system": system.state_dict(),
        "unified_control": (
            unified_control.state_dict() if unified_control is not None else None
        ),
        "history_control": (
            history_control.state_dict() if history_control is not None else None
        ),
        "optimizer": optimizer.state_dict(),
        "quic_expert_ready": config.quic_expert_ready_after_fit,
        "capacity_receipt": capacity,
        "zero_collapse_receipt": residual_receipt,
        "checkpoint_binding": checkpoint_binding,
    }
    temporary = config.output_dir / "checkpoint-latest.pt.tmp"
    torch.save(payload, temporary)
    temporary.replace(config.output_dir / "checkpoint-latest.pt")


def _write_immutable_json(
    path: Path,
    payload: Mapping[str, object],
    *,
    trusted_root: Path,
) -> str:
    path = _lexical_absolute(path)
    root = _lexical_absolute(trusted_root)
    _relative_to_trusted_root(path, root, "不可变检查点绑定清单")
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    expected_sha256 = hashlib.sha256(encoded).hexdigest()
    temporary_name = f".{path.name}.{secrets.token_hex(16)}.tmp"
    temporary_flags = (
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | os.O_CLOEXEC
        | os.O_NOFOLLOW
    )
    with _open_anchored_directory(
        path.parent,
        "不可变检查点绑定清单",
        trusted_root=root,
    ) as (directory_descriptor, verify_directory_chain):
        published = False
        completed = False
        try:
            descriptor = os.open(
                temporary_name,
                temporary_flags,
                0o600,
                dir_fd=directory_descriptor,
            )
            with os.fdopen(descriptor, "w+b") as destination:
                destination.write(encoded)
                destination.flush()
                os.fsync(destination.fileno())
                destination.seek(0)
                written = destination.read()
                if (
                    written != encoded
                    or hashlib.sha256(written).hexdigest() != expected_sha256
                ):
                    raise R2FinalPhysicsFitError(
                        "不可变检查点绑定清单临时文件校验失败"
                    )
            verify_directory_chain()
            try:
                os.link(
                    temporary_name,
                    path.name,
                    src_dir_fd=directory_descriptor,
                    dst_dir_fd=directory_descriptor,
                    follow_symlinks=False,
                )
                published = True
                verify_directory_chain()
            except FileExistsError:
                verify_directory_chain()
                existing_descriptor = os.open(
                    path.name,
                    os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
                    dir_fd=directory_descriptor,
                )
                with os.fdopen(existing_descriptor, "rb") as existing_source:
                    existing_stat = os.fstat(existing_source.fileno())
                    named_stat = os.stat(
                        path.name,
                        dir_fd=directory_descriptor,
                        follow_symlinks=False,
                    )
                    if (
                        stat.S_ISLNK(named_stat.st_mode)
                        or not stat.S_ISREG(existing_stat.st_mode)
                        or not stat.S_ISREG(named_stat.st_mode)
                        or (existing_stat.st_dev, existing_stat.st_ino)
                        != (named_stat.st_dev, named_stat.st_ino)
                    ):
                        raise R2FinalPhysicsFitError(
                            "既有不可变检查点绑定清单身份不稳定"
                        )
                    existing = existing_source.read()
                verify_directory_chain()
                if existing != encoded:
                    raise R2FinalPhysicsFitError(
                        f"不可变检查点绑定清单已存在且内容不同：{path}"
                    )
            os.fsync(directory_descriptor)
            verify_directory_chain()
            try:
                os.unlink(temporary_name, dir_fd=directory_descriptor)
            except FileNotFoundError:
                pass
            os.fsync(directory_descriptor)
            verify_directory_chain()
            completed = True
        finally:
            if not completed:
                try:
                    try:
                        os.unlink(temporary_name, dir_fd=directory_descriptor)
                    except FileNotFoundError:
                        pass
                    if published:
                        try:
                            os.unlink(path.name, dir_fd=directory_descriptor)
                        except FileNotFoundError:
                            pass
                finally:
                    os.fsync(directory_descriptor)
                    verify_directory_chain()
    return expected_sha256


def _freeze_checkpoint_binding(config: PhysicsFitConfig) -> Mapping[str, object]:
    checkpoint = config.output_dir / "checkpoint-latest.pt"
    checkpoint_sha256 = _file_sha256(
        checkpoint, trusted_root=config.project_root
    )
    fit_config_sha256 = config.file_sha256
    checkpoint_binding = {
        "config_sha256": _config_sha256(config),
        "fit_config_sha256": fit_config_sha256,
        "input_sha256": config.data.artifact_payload_merkle_sha256,
        "seed": config.seed,
        "mode": config.mode,
    }
    payload = {
        "schema_version": "flow_probe_r2_checkpoint_binding_manifest_v1",
        "status": "frozen",
        "immutable": True,
        "checkpoint_path": str(_lexical_absolute(checkpoint)),
        "checkpoint_sha256": checkpoint_sha256,
        "fit_config_path": str(_lexical_absolute(config.config_path)),
        "fit_config_sha256": fit_config_sha256,
        "input_path": str(_lexical_absolute(config.data.artifact.path)),
        "input_sha256": config.data.artifact_payload_merkle_sha256,
        "seed": config.seed,
        "mode": config.mode,
        "checkpoint_binding": checkpoint_binding,
    }
    manifest_path = config.output_dir / "checkpoint-binding-manifest.json"
    manifest_sha256 = _write_immutable_json(
        manifest_path, payload, trusted_root=config.project_root
    )
    return {
        "path": str(manifest_path),
        "sha256": manifest_sha256,
        "checkpoint_sha256": checkpoint_sha256,
    }


def _device(config: PhysicsFitConfig, torch: Any) -> Any:
    requested = config.training.device
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise R2FinalPhysicsFitError("配置要求 CUDA，但当前没有可用显卡")
    if requested not in ("cpu", "cuda"):
        raise R2FinalPhysicsFitError("training.device 只允许 auto/cpu/cuda")
    return torch.device(requested)


def execute(config: PhysicsFitConfig) -> Mapping[str, object]:
    if config.mode == "formal" and os.environ.get("R2_EQUAL_CAPACITY_REQUIRED") != "1":
        raise R2FinalPhysicsFitError("正式物理训练必须经等容量包装器启动")
    if config.mode == "formal" and os.environ.get("R2_ZERO_COLLAPSE_REQUIRED") != "1":
        raise R2FinalPhysicsFitError("正式物理训练必须经固定残差零坍缩包装器启动")
    try:
        import torch
    except ImportError as error:
        raise R2FinalPhysicsFitError("最终物理预训练需要 PyTorch") from error
    random.seed(config.seed)
    np.random.seed(config.seed)
    torch.manual_seed(config.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config.seed)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    frozen_manifest = config.output_dir / "checkpoint-binding-manifest.json"
    if frozen_manifest.exists():
        raise R2FinalPhysicsFitError(
            "输出目录已有不可变检查点绑定清单，禁止继续覆盖训练"
        )
    system = build_system(config)
    residual_receipt = fixed_residual_zero_collapse_receipt(system)
    _atomic_json(config.output_dir / "zero-collapse-receipt.json", residual_receipt)
    if config.mode == "formal" and not bool(
        residual_receipt["formal_tcp_udp_dynamics_ready"]
    ):
        raise R2FinalPhysicsFitError(
            "固定协议动力学残差尚未闭合："
            + str(residual_receipt["blocking_reason"])
        )
    splits = load_splits(config)
    unified_control = (
        build_unified_control_system(config) if config.mode == "formal" else None
    )
    history_control = (
        build_history_control_system(config) if config.mode == "formal" else None
    )
    capacity_receipt = _parameter_receipt(
        system, unified_control, history_control
    )
    binding = {
        "schema_version": SCHEMA_VERSION,
        "config_sha256": _config_sha256(config),
        "input_sha256": config.data.artifact_payload_merkle_sha256,
        "mode": config.mode,
        "seed": config.seed,
        "split_counts": {name: len(split) for name, split in splits.items()},
        "quic_expert_ready_after_fit": config.quic_expert_ready_after_fit,
        "capacity_receipt": capacity_receipt,
        "zero_collapse_receipt": residual_receipt,
    }
    binding_path = config.output_dir / "run-binding.json"
    if binding_path.exists():
        stored = json.loads(binding_path.read_text(encoding="utf-8"))
        if stored != binding:
            raise R2FinalPhysicsFitError("已有输出目录绑定与当前配置不一致")
    else:
        _atomic_json(binding_path, binding)
    device = _device(config, torch)
    system.to(device)
    if unified_control is not None:
        unified_control.to(device)
    if history_control is not None:
        history_control.to(device)
    optimizer_parameters = list(system.parameters())
    if unified_control is not None:
        optimizer_parameters.extend(unified_control.parameters())
    if history_control is not None:
        optimizer_parameters.extend(history_control.parameters())
    optimizer = torch.optim.AdamW(
        optimizer_parameters,
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )
    step = 0
    start_epoch = 0
    checkpoint = config.output_dir / "checkpoint-latest.pt"
    if checkpoint.is_file():
        values = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if values.get("config_sha256") != _config_sha256(config):
            raise R2FinalPhysicsFitError("恢复检查点与当前配置绑定不一致")
        system.load_state_dict(values["routed_system"], strict=True)
        if unified_control is not None:
            stored_unified = values.get("unified_control")
            if not isinstance(stored_unified, Mapping):
                raise R2FinalPhysicsFitError("正式检查点缺少统一控制支路")
            unified_control.load_state_dict(stored_unified, strict=True)
        if history_control is not None:
            stored_history = values.get("history_control")
            if not isinstance(stored_history, Mapping):
                raise R2FinalPhysicsFitError("正式检查点缺少历史控制支路")
            history_control.load_state_dict(stored_history, strict=True)
        if values.get("capacity_receipt") != capacity_receipt:
            raise R2FinalPhysicsFitError("恢复检查点的容量收据不一致")
        optimizer.load_state_dict(values["optimizer"])
        step = int(values["step"])
        start_epoch = int(values["epoch"])
    logger = _MetricLogger(config)
    started = time.perf_counter()
    try:
        for epoch in range(start_epoch, config.training.epochs):
            system.train()
            if unified_control is not None:
                unified_control.train()
            if history_control is not None:
                history_control.train()
            for indices in _loader(splits["train-fit"], config, torch, shuffle=True):
                batch = _tensor_batch(splits["train-fit"], indices, torch, device)
                optimizer.zero_grad(set_to_none=True)
                loss, scalars = _losses(
                    system, unified_control, history_control, batch, config, torch
                )
                if not bool(torch.isfinite(loss).item()):
                    raise R2FinalPhysicsFitError("物理预训练损失不是有限数")
                loss.backward()
                gradient_norm = torch.nn.utils.clip_grad_norm_(
                    optimizer_parameters, config.training.max_grad_norm
                )
                optimizer.step()
                step += 1
                scalars = {
                    **scalars,
                    "gradient_norm": float(gradient_norm.detach().float().item()),
                    "learning_rate": float(optimizer.param_groups[0]["lr"]),
                    "epoch": float(epoch + 1),
                }
                logger.log(scalars, step=step, event="optimizer_step")
                if step % config.training.save_steps == 0:
                    _checkpoint(
                        system,
                        unified_control,
                        history_control,
                        optimizer,
                        config,
                        torch,
                        step,
                        epoch,
                    )
            calibration = _evaluate(
                system,
                unified_control,
                history_control,
                splits["calibration"],
                config,
                torch,
                device,
            )
            logger.log(
                {f"calibration/{name}": value for name, value in calibration.items()},
                step=step,
                event="calibration",
            )
            _checkpoint(
                system,
                unified_control,
                history_control,
                optimizer,
                config,
                torch,
                step,
                epoch + 1,
            )
        validation = _evaluate(
            system,
            unified_control,
            history_control,
            splits["validation"],
            config,
            torch,
            device,
        )
        frozen_checkpoint = _freeze_checkpoint_binding(config)
        result = {
            **binding,
            "status": "finished",
            "steps": step,
            "epochs": config.training.epochs,
            "elapsed_seconds": time.perf_counter() - started,
            "validation": validation,
            "checkpoint": str(checkpoint),
            "checkpoint_binding_manifest": frozen_checkpoint,
        }
        _atomic_json(config.output_dir / "result.json", result)
        return result
    finally:
        logger.finish()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="训练最终 R2 物理专家")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--trusted-root", type=Path, required=True)
    parser.add_argument("--validate-config-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config, trusted_root=args.trusted_root)
    if args.validate_config_only:
        print(
            json.dumps(
                {
                    "status": "config-valid",
                    "mode": config.mode,
                    "seed": config.seed,
                    "output_dir": str(config.output_dir),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    result = execute(config)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
