from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml

from flow_probe import shared_b0_distilbert_baseline as baseline
from flow_probe.r2_final_experts import (
    EXPERT_SHARED,
    EXPERT_TCP,
    EXPERT_UDP,
    ROUTE_NAMES,
    ResidualObservationContext,
    RouteBatch,
    fixed_residual_zero_collapse_receipt,
)
from flow_probe.r2_final_physics_fit import (
    PhysicsFitConfig,
    PhysicsSplit,
    build_history_control_system,
    build_system,
    build_unified_control_system,
    checkpoint_binding,
    config_semantic_sha256,
    load_config as load_physics_fit_config,
    load_splits as load_physics_splits,
)
from flow_probe.r2_final_views import (
    ALLOWED_SPLITS,
    VARIANTS,
    ArtifactSpec,
    BoundSequence,
    DatasetViewContract,
    PreparedVariantViews,
    VariantSplit,
    ViewColumnSpec,
    array_sha256,
    build_variant_views,
    file_sha256,
    load_base_views,
    strings_sha256,
)


SCHEMA_VERSION = "flow_probe_r2_final_distilbert_probe_v1"
STAGE = "theory_selection"
STATUS = "review_pending"
FUSION_LIMIT = 0.1
HISTORY_TO_PHYSICS = {
    "total_packets": "public_total_packets",
    "total_bytes": "public_total_l3_bytes",
    "packet_length_mean": "public_packet_length_mean_l3_bytes",
    "packet_length_min": "public_packet_length_min_l3_bytes",
    "packet_length_max": "public_packet_length_max_l3_bytes",
    "iat_mean_ms": "public_iat_mean_ms",
    "packet_rate": "public_packet_rate_pps",
    "byte_rate": "public_byte_rate_Bps",
}


def _bounded_residual_strength(parameter: Any, tensor_ops: Any) -> Any:
    """以零为初值，在有界区间内学习物理旁路残差强度。"""

    return FUSION_LIMIT * tensor_ops.tanh(parameter)


class R2FinalProbeError(ValueError):
    """表示最终 R2 单组探针合同被违反。"""


class R2FinalDataNotReady(R2FinalProbeError):
    """表示冻结数据尚未满足正式启动门禁。"""


@dataclass(frozen=True)
class DataSettings:
    ready: bool
    not_ready_reason: str
    contract: DatasetViewContract


@dataclass(frozen=True)
class CheckpointSpec:
    ready: bool
    not_ready_reason: str
    path: Path
    sha256: str | None
    binding_manifest_path: Path
    binding_manifest_sha256: str | None


@dataclass(frozen=True)
class PhysicsSettings:
    fit_config: ArtifactSpec
    checkpoint: CheckpointSpec
    quic_expert_ready: bool
    production_batch_size: int
    capacity_contract: str
    physical_evaluation_split: str
    physical_evaluation_cluster_id: str
    physical_state_metric: str
    physical_residual_metric: str
    physical_aggregation: str
    comparison_variants: tuple[str, ...]


@dataclass(frozen=True)
class TrackingSettings:
    project: str
    workspace: str
    run_name: str
    mode: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ProbeConfig:
    variant: str
    data: DataSettings
    physics: PhysicsSettings
    model: baseline.ModelSettings
    training: baseline.TrainingSettings
    evaluation: baseline.EvaluationSettings
    output_root: Path
    seed: int
    tracking: TrackingSettings
    config_path: Path
    file_sha256: str
    project_root: Path


@dataclass(frozen=True)
class ProbeOutput:
    logits: Any
    loss: Any | None


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise R2FinalProbeError(f"{description} 必须是映射")
    return value


def _string(value: object, description: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise R2FinalProbeError(f"{description} 必须是无首尾空白的字符串")
    if not allow_empty and not value:
        raise R2FinalProbeError(f"{description} 不能为空")
    return value


def _integer(value: object, description: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise R2FinalProbeError(f"{description} 必须是不小于 {minimum} 的整数")
    return value


def _number(value: object, description: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R2FinalProbeError(f"{description} 必须是数值")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise R2FinalProbeError(f"{description} 必须是不小于 {minimum} 的有限数")
    return result


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
        raise R2FinalProbeError(f"{description}超出受信任根：{lexical_path}") from error
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
        raise R2FinalProbeError(f"{description}必须位于固定配置目录：{configs_root}") from error
    if len(relative.parts) != 1:
        raise R2FinalProbeError(f"{description}必须是固定配置目录中的直接文件：{config_path}")


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
    directory_flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors: list[int] = []
    component_names: list[str] = []
    try:
        try:
            root_descriptor = os.open(root, directory_flags)
        except OSError as error:
            raise R2FinalProbeError(f"{description}无法固定受信任根：{root}") from error
        descriptors.append(root_descriptor)
        root_stat = os.fstat(root_descriptor)
        if not stat.S_ISDIR(root_stat.st_mode):
            raise R2FinalProbeError(f"受信任根不是目录：{root}")
        for component in relative.parts:
            if component in ("", ".", ".."):
                raise R2FinalProbeError(f"{description}包含非法路径组件：{component}")
            parent_descriptor = descriptors[-1]
            try:
                next_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=parent_descriptor,
                )
            except OSError as error:
                raise R2FinalProbeError(f"{description}父目录无法安全打开：{directory}") from error
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
                    raise R2FinalProbeError(f"{description}父目录身份不稳定：{component}")
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
                raise R2FinalProbeError(f"{description}受信任根身份无法复核：{root}") from error
            if (
                stat.S_ISLNK(named_root_stat.st_mode)
                or not stat.S_ISDIR(current_root_stat.st_mode)
                or not stat.S_ISDIR(named_root_stat.st_mode)
                or (current_root_stat.st_dev, current_root_stat.st_ino)
                != (root_stat.st_dev, root_stat.st_ino)
                or (current_root_stat.st_dev, current_root_stat.st_ino)
                != (named_root_stat.st_dev, named_root_stat.st_ino)
            ):
                raise R2FinalProbeError(f"{description}受信任根身份发生变化：{root}")
            for index, component in enumerate(component_names, start=1):
                opened_stat = os.fstat(descriptors[index])
                try:
                    named_stat = os.stat(
                        component,
                        dir_fd=descriptors[index - 1],
                        follow_symlinks=False,
                    )
                except OSError as error:
                    raise R2FinalProbeError(
                        f"{description}父目录身份无法复核：{component}"
                    ) from error
                if (
                    stat.S_ISLNK(named_stat.st_mode)
                    or not stat.S_ISDIR(opened_stat.st_mode)
                    or not stat.S_ISDIR(named_stat.st_mode)
                    or (opened_stat.st_dev, opened_stat.st_ino)
                    != (named_stat.st_dev, named_stat.st_ino)
                ):
                    raise R2FinalProbeError(f"{description}父目录身份发生变化：{component}")

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
        raise R2FinalProbeError(f"{description}不能是受信任根目录")
    with _open_anchored_directory(
        path.parent,
        description,
        trusted_root=root,
    ) as (parent_descriptor, verify_parent_chain):
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
        try:
            descriptor = os.open(path.name, flags, dir_fd=parent_descriptor)
        except OSError as error:
            raise R2FinalProbeError(f"{description}无法从固定父目录安全打开：{path}") from error
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
                or (before.st_dev, before.st_ino) != (named_before.st_dev, named_before.st_ino)
            ):
                raise R2FinalProbeError(f"{description}文件身份不稳定：{path}")
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
                or (after.st_dev, after.st_ino) != (named_after.st_dev, named_after.st_ino)
            ):
                raise R2FinalProbeError(f"{description}在读取期间发生变化：{path}")
            verify_parent_chain()
        finally:
            source.close()


def _open_file_sha256(source: Any) -> str:
    digest = hashlib.sha256()
    source.seek(0)
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
        digest.update(chunk)
    source.seek(0)
    return digest.hexdigest()


def _read_verified_artifact_bytes(
    spec: ArtifactSpec,
    description: str,
    *,
    trusted_root: Path,
) -> bytes:
    path = _lexical_absolute(spec.path)
    with _open_stable_regular_file(path, description, trusted_root=trusted_root) as source:
        payload = source.read()
    actual = hashlib.sha256(payload).hexdigest()
    if actual != spec.sha256:
        raise R2FinalProbeError(f"{description} SHA-256 不一致：预期 {spec.sha256}，实际 {actual}")
    return payload


def _sha256_string(value: object, description: str) -> str:
    result = _string(value, description)
    if (
        len(result) != 64
        or result != result.lower()
        or any(character not in "0123456789abcdef" for character in result)
    ):
        raise R2FinalProbeError(f"{description} 必须是规范的 64 位 SHA-256")
    return result


def _artifact(value: object, root: Path, description: str) -> ArtifactSpec:
    raw = _mapping(value, description)
    return ArtifactSpec(
        path=_resolve_path(raw.get("path"), root, f"{description}.path"),
        sha256=_sha256_string(raw.get("sha256"), f"{description}.sha256"),
    )


def _checkpoint_spec(value: object, root: Path) -> CheckpointSpec:
    raw = _mapping(value, "physics.checkpoint")
    ready = raw.get("ready")
    if not isinstance(ready, bool):
        raise R2FinalProbeError("physics.checkpoint.ready 必须是布尔值")
    not_ready_reason = _string(
        raw.get("not_ready_reason", ""),
        "physics.checkpoint.not_ready_reason",
        allow_empty=True,
    )
    binding = _mapping(raw.get("binding_manifest"), "physics.checkpoint.binding_manifest")
    checkpoint_sha256 = raw.get("sha256")
    manifest_sha256 = binding.get("sha256")
    if ready:
        checkpoint_sha256 = _sha256_string(checkpoint_sha256, "physics.checkpoint.sha256")
        manifest_sha256 = _sha256_string(
            manifest_sha256, "physics.checkpoint.binding_manifest.sha256"
        )
        if not_ready_reason:
            raise R2FinalProbeError("检查点就绪时 not_ready_reason 必须为空")
    else:
        if not not_ready_reason:
            raise R2FinalProbeError("检查点未就绪时必须填写 not_ready_reason")
        if checkpoint_sha256 is not None or manifest_sha256 is not None:
            raise R2FinalProbeError("检查点未就绪时不得伪造检查点或清单哈希")
    return CheckpointSpec(
        ready=ready,
        not_ready_reason=not_ready_reason,
        path=_resolve_path(raw.get("path"), root, "physics.checkpoint.path"),
        sha256=checkpoint_sha256,
        binding_manifest_path=_resolve_path(
            binding.get("path"), root, "physics.checkpoint.binding_manifest.path"
        ),
        binding_manifest_sha256=manifest_sha256,
    )


def _verify_seed_checkpoint_consistency(
    config_path: Path,
    seed: int,
    physics: PhysicsSettings,
    *,
    trusted_root: Path,
) -> None:
    expected = (
        str(physics.fit_config.path),
        physics.fit_config.sha256,
        physics.checkpoint.ready,
        str(physics.checkpoint.path),
        physics.checkpoint.sha256,
        str(physics.checkpoint.binding_manifest_path),
        physics.checkpoint.binding_manifest_sha256,
    )
    root = _lexical_absolute(trusted_root)
    reference_science_contract: str | None = None
    for variant in physics.comparison_variants:
        suffix = variant.removeprefix("F-").lower()
        sibling = config_path.parent / f"r2_final_distilbert_f-{suffix}_seed{seed}.yaml"
        with _open_stable_regular_file(
            sibling,
            f"同种子配置 {sibling.name}",
            trusted_root=root,
        ) as source:
            sibling_snapshot = source.read()
        try:
            sibling_raw = _mapping(
                yaml.safe_load(sibling_snapshot.decode("utf-8")),
                f"同种子配置 {sibling.name}",
            )
        except (UnicodeDecodeError, yaml.YAMLError) as error:
            raise R2FinalProbeError(f"同种子配置无法解析：{sibling.name}") from error
        if sibling_raw.get("seed") != seed:
            raise R2FinalProbeError(f"同种子配置种子不一致：{sibling.name}")
        if sibling_raw.get("variant") != variant:
            raise R2FinalProbeError(f"同种子配置组别身份不一致：{sibling.name}")
        science_contract = json.dumps(
            {
                name: sibling_raw.get(name)
                for name in (
                    "data",
                    "model",
                    "training",
                    "evaluation",
                    "output_root",
                    "tracking",
                )
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if reference_science_contract is None:
            reference_science_contract = science_contract
        elif science_contract != reference_science_contract:
            raise R2FinalProbeError(
                f"种子 {seed} 的冻结比较组模型、训练预算或评价协议不一致：{sibling.name}"
            )
        sibling_physics = _mapping(sibling_raw.get("physics"), f"同种子配置 {sibling.name}.physics")
        fit = _mapping(
            sibling_physics.get("fit_config"),
            f"同种子配置 {sibling.name}.physics.fit_config",
        )
        checkpoint = _mapping(
            sibling_physics.get("checkpoint"),
            f"同种子配置 {sibling.name}.physics.checkpoint",
        )
        manifest = _mapping(
            checkpoint.get("binding_manifest"),
            f"同种子配置 {sibling.name}.physics.checkpoint.binding_manifest",
        )
        identity = (
            str(_resolve_path(fit.get("path"), root, "同种子物理配置路径")),
            fit.get("sha256"),
            checkpoint.get("ready"),
            str(_resolve_path(checkpoint.get("path"), root, "同种子检查点路径")),
            checkpoint.get("sha256"),
            str(_resolve_path(manifest.get("path"), root, "同种子绑定清单路径")),
            manifest.get("sha256"),
        )
        if identity != expected:
            raise R2FinalProbeError(f"种子 {seed} 的五组未绑定同一物理检查点：{sibling.name}")


def _split_artifacts(
    value: object,
    root: Path,
    description: str,
) -> Mapping[str, ArtifactSpec]:
    raw = _mapping(value, description)
    if set(raw) != set(ALLOWED_SPLITS):
        raise R2FinalProbeError(f"{description} 必须精确覆盖三个开发划分")
    return {
        split: _artifact(raw[split], root, f"{description}.{split}") for split in ALLOWED_SPLITS
    }


def _training(value: object) -> baseline.TrainingSettings:
    raw = _mapping(value, "training")
    return baseline.TrainingSettings(
        per_device_train_batch_size=_integer(
            raw.get("per_device_train_batch_size"),
            "training.per_device_train_batch_size",
            minimum=1,
        ),
        per_device_eval_batch_size=_integer(
            raw.get("per_device_eval_batch_size"),
            "training.per_device_eval_batch_size",
            minimum=1,
        ),
        gradient_accumulation_steps=_integer(
            raw.get("gradient_accumulation_steps"),
            "training.gradient_accumulation_steps",
            minimum=1,
        ),
        learning_rate=_number(raw.get("learning_rate"), "training.learning_rate", minimum=1e-12),
        weight_decay=_number(raw.get("weight_decay"), "training.weight_decay"),
        num_train_epochs=_integer(
            raw.get("num_train_epochs"), "training.num_train_epochs", minimum=1
        ),
        warmup_ratio=_number(raw.get("warmup_ratio"), "training.warmup_ratio"),
        max_grad_norm=_number(raw.get("max_grad_norm"), "training.max_grad_norm", minimum=1e-12),
        save_steps=_integer(raw.get("save_steps"), "training.save_steps", minimum=1),
        save_total_limit=_integer(
            raw.get("save_total_limit"), "training.save_total_limit", minimum=1
        ),
        num_workers=_integer(raw.get("num_workers"), "training.num_workers"),
        resume_from_checkpoint=_string(
            raw.get("resume_from_checkpoint"), "training.resume_from_checkpoint"
        ),
    )


def load_config(path: Path, *, trusted_root: Path) -> ProbeConfig:
    config_path = _lexical_absolute(path)
    root = _lexical_absolute(trusted_root)
    _require_fixed_config_path(config_path, root, "正式探针配置")
    with _open_stable_regular_file(config_path, "正式探针配置", trusted_root=root) as source:
        config_snapshot = source.read()
    try:
        raw = _mapping(yaml.safe_load(config_snapshot.decode("utf-8")), "配置")
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise R2FinalProbeError("正式探针配置无法解析") from error
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise R2FinalProbeError("配置 schema_version 不符合最终单组探针合同")
    seed = _integer(raw.get("seed"), "seed")
    if seed not in (42, 43, 44):
        raise R2FinalProbeError("最终探针只允许种子 42、43、44")
    variant = _string(raw.get("variant"), "variant")
    if variant not in VARIANTS:
        raise R2FinalProbeError(f"variant 必须属于 {VARIANTS}")

    data_raw = _mapping(raw.get("data"), "data")
    ready = data_raw.get("ready")
    if not isinstance(ready, bool):
        raise R2FinalProbeError("data.ready 必须是布尔值")
    not_ready_reason = _string(
        data_raw.get("not_ready_reason", ""),
        "data.not_ready_reason",
        allow_empty=True,
    )
    if not ready and not not_ready_reason:
        raise R2FinalProbeError("数据未就绪时必须填写 not_ready_reason")
    columns_raw = _mapping(data_raw.get("columns"), "data.columns")
    history_fields = columns_raw.get("history_fields")
    if not isinstance(history_fields, list) or not history_fields:
        raise R2FinalProbeError("data.columns.history_fields 必须是非空列表")
    history_missing_fields = columns_raw.get("history_missing_fields")
    if history_missing_fields is None:
        history_missing_fields = [f"{field}_missing" for field in history_fields]
    if not isinstance(history_missing_fields, list) or len(history_missing_fields) != len(
        history_fields
    ):
        raise R2FinalProbeError("data.columns.history_missing_fields 必须与历史字段等长")
    columns = ViewColumnSpec(
        sample_id=_string(columns_raw.get("sample_id"), "data.columns.sample_id"),
        stable_order=_string(columns_raw.get("stable_order"), "data.columns.stable_order"),
        split_id=_string(columns_raw.get("split_id"), "data.columns.split_id"),
        text=_string(columns_raw.get("text"), "data.columns.text"),
        label=_string(columns_raw.get("label"), "data.columns.label"),
        window_index=_string(columns_raw.get("window_index"), "data.columns.window_index"),
        window_valid=_string(columns_raw.get("window_valid"), "data.columns.window_valid"),
        history_fields=tuple(
            _string(field, "data.columns.history_fields") for field in history_fields
        ),
        history_missing_fields=tuple(
            _string(field, "data.columns.history_missing_fields")
            for field in history_missing_fields
        ),
        route_name=_string(columns_raw.get("route_name"), "data.columns.route_name"),
        route_confidence=_string(
            columns_raw.get("route_confidence"), "data.columns.route_confidence"
        ),
        quic_applicable=_string(columns_raw.get("quic_applicable"), "data.columns.quic_applicable"),
        quic_formal_training_enabled=_string(
            columns_raw.get("quic_formal_training_enabled"),
            "data.columns.quic_formal_training_enabled",
        ),
        source_dataset=_string(columns_raw.get("source_dataset"), "data.columns.source_dataset"),
    )
    history_scales_raw = data_raw.get("history_scales")
    if not isinstance(history_scales_raw, list) or len(history_scales_raw) != len(history_fields):
        raise R2FinalProbeError("data.history_scales 必须与历史字段等长")
    history_scales = tuple(
        _number(value, "data.history_scales", minimum=1e-12) for value in history_scales_raw
    )
    data = DataSettings(
        ready=ready,
        not_ready_reason=not_ready_reason,
        contract=DatasetViewContract(
            freeze_manifest=_artifact(
                data_raw.get("freeze_manifest"), root, "data.freeze_manifest"
            ),
            detection_views=_split_artifacts(
                data_raw.get("detection_views"), root, "data.detection_views"
            ),
            common_histories=_split_artifacts(
                data_raw.get("common_histories"), root, "data.common_histories"
            ),
            route_assignments=_split_artifacts(
                data_raw.get("route_assignments"), root, "data.route_assignments"
            ),
            columns=columns,
            window_count=_integer(data_raw.get("window_count"), "data.window_count", minimum=1),
            final_test_visible=False,
            artifact_payload_merkle_sha256=_string(
                data_raw.get("artifact_payload_merkle_sha256"),
                "data.artifact_payload_merkle_sha256",
            ),
            history_scales=history_scales,
        ),
    )

    physics_raw = _mapping(raw.get("physics"), "physics")
    quic_ready = physics_raw.get("quic_expert_ready")
    if not isinstance(quic_ready, bool):
        raise R2FinalProbeError("physics.quic_expert_ready 必须是布尔值")
    comparison_variants_raw = physics_raw.get("comparison_variants")
    if not isinstance(comparison_variants_raw, list) or not comparison_variants_raw:
        raise R2FinalProbeError("physics.comparison_variants 必须是非空组别列表")
    comparison_variants = tuple(
        _string(item, "physics.comparison_variants") for item in comparison_variants_raw
    )
    if len(set(comparison_variants)) != len(comparison_variants) or not set(
        comparison_variants
    ).issubset(VARIANTS):
        raise R2FinalProbeError("physics.comparison_variants 包含重复或非法组别")
    if variant not in comparison_variants:
        raise R2FinalProbeError("当前组别未包含在冻结比较集合")
    physics = PhysicsSettings(
        fit_config=_artifact(physics_raw.get("fit_config"), root, "physics.fit_config"),
        checkpoint=_checkpoint_spec(physics_raw.get("checkpoint"), root),
        quic_expert_ready=quic_ready,
        production_batch_size=_integer(
            physics_raw.get("production_batch_size"),
            "physics.production_batch_size",
            minimum=1,
        ),
        capacity_contract=_string(
            physics_raw.get("capacity_contract"), "physics.capacity_contract"
        ),
        physical_evaluation_split=_string(
            physics_raw.get("physical_evaluation_split"),
            "physics.physical_evaluation_split",
        ),
        physical_evaluation_cluster_id=_string(
            physics_raw.get("physical_evaluation_cluster_id"),
            "physics.physical_evaluation_cluster_id",
        ),
        physical_state_metric=_string(
            physics_raw.get("physical_state_metric"),
            "physics.physical_state_metric",
        ),
        physical_residual_metric=_string(
            physics_raw.get("physical_residual_metric"),
            "physics.physical_residual_metric",
        ),
        physical_aggregation=_string(
            physics_raw.get("physical_aggregation"),
            "physics.physical_aggregation",
        ),
        comparison_variants=comparison_variants,
    )
    if physics.capacity_contract != "trained_equal_active_branch_v1":
        raise R2FinalProbeError("physics.capacity_contract 非冻结版本")
    if physics.physical_evaluation_split != "validation":
        raise R2FinalProbeError("G3 物理评价只允许冻结 validation 划分")
    if physics.physical_state_metric != "training_standardized_state_mse_v1":
        raise R2FinalProbeError("G3 状态主指标必须为训练区标准化状态 MSE")
    if physics.physical_residual_metric != "dimensionless_residual_mse_v1":
        raise R2FinalProbeError("G3 残差主指标必须为无量纲物理残差 MSE")
    if physics.physical_aggregation != "equal_state_equation_protocol_v1":
        raise R2FinalProbeError("G3 物理指标等权聚合合同不一致")
    _verify_seed_checkpoint_consistency(
        config_path,
        seed,
        physics,
        trusted_root=root,
    )

    model_raw = _mapping(raw.get("model"), "model")
    model = baseline.ModelSettings(
        identifier=_string(model_raw.get("identifier"), "model.identifier"),
        source=_string(model_raw.get("source"), "model.source"),
        max_length=_integer(model_raw.get("max_length"), "model.max_length", minimum=1),
        device=_string(model_raw.get("device"), "model.device"),
        precision=_string(model_raw.get("precision"), "model.precision"),
    )
    if model.identifier != baseline.FIXED_MODEL_ID:
        raise R2FinalProbeError(f"模型必须固定为 {baseline.FIXED_MODEL_ID}")
    training = _training(raw.get("training"))
    evaluation_raw = _mapping(raw.get("evaluation"), "evaluation")
    evaluation = baseline.EvaluationSettings(
        threshold=_number(evaluation_raw.get("threshold"), "evaluation.threshold"),
        calibration_bins=_integer(
            evaluation_raw.get("calibration_bins"),
            "evaluation.calibration_bins",
            minimum=1,
        ),
    )
    if evaluation.threshold > 1:
        raise R2FinalProbeError("evaluation.threshold 必须位于 [0,1]")
    output_root = _resolve_path(raw.get("output_root"), root, "output_root")
    tracking_raw = _mapping(raw.get("tracking"), "tracking")
    tags_raw = tracking_raw.get("tags")
    if not isinstance(tags_raw, list) or not tags_raw:
        raise R2FinalProbeError("tracking.tags 必须是非空列表")
    tracking = TrackingSettings(
        project=_string(tracking_raw.get("project"), "tracking.project"),
        workspace=_string(tracking_raw.get("workspace"), "tracking.workspace"),
        run_name=_string(tracking_raw.get("run_name"), "tracking.run_name"),
        mode=_string(tracking_raw.get("mode"), "tracking.mode"),
        tags=tuple(_string(tag, "tracking.tags") for tag in tags_raw),
    )
    if len(tracking.tags) > 20:
        raise R2FinalProbeError("SwanLab 标签数量不得超过 20")
    return ProbeConfig(
        variant=variant,
        data=data,
        physics=physics,
        model=model,
        training=training,
        evaluation=evaluation,
        output_root=output_root,
        seed=seed,
        tracking=tracking,
        config_path=config_path,
        file_sha256=hashlib.sha256(config_snapshot).hexdigest(),
        project_root=root,
    )


def _verify_artifact(
    spec: ArtifactSpec,
    description: str,
    *,
    trusted_root: Path,
) -> tuple[Path, bytes]:
    path = _lexical_absolute(spec.path)
    return path, _read_verified_artifact_bytes(spec, description, trusted_root=trusted_root)


def _physics_system(
    config: ProbeConfig,
    torch: Any,
) -> tuple[PhysicsFitConfig, Any, Any, Any, str, Mapping[str, object], str]:
    checkpoint_spec = config.physics.checkpoint
    if not checkpoint_spec.ready:
        raise R2FinalDataNotReady(checkpoint_spec.not_ready_reason)
    fit_path, fit_snapshot = _verify_artifact(
        config.physics.fit_config,
        "物理预训练配置",
        trusted_root=config.project_root,
    )
    fit_config = load_physics_fit_config(
        fit_path,
        trusted_root=config.project_root,
        snapshot=fit_snapshot,
    )
    expected_binding = dict(checkpoint_binding(fit_config))
    if expected_binding["config_sha256"] != config_semantic_sha256(fit_config):
        raise R2FinalProbeError("物理拟合配置语义摘要生成不一致")
    if expected_binding["fit_config_sha256"] != config.physics.fit_config.sha256:
        raise R2FinalProbeError("当前实现绑定的拟合配置文件摘要不一致")
    if fit_config.seed != config.seed or fit_config.mode != "formal":
        raise R2FinalProbeError("物理拟合配置的种子或模式与探针不一致")
    manifest_path = _lexical_absolute(checkpoint_spec.binding_manifest_path)
    with _open_stable_regular_file(
        manifest_path,
        "检查点绑定清单",
        trusted_root=config.project_root,
    ) as source:
        manifest_snapshot = source.read()
    manifest_sha256 = hashlib.sha256(manifest_snapshot).hexdigest()
    if manifest_sha256 != checkpoint_spec.binding_manifest_sha256:
        raise R2FinalProbeError("检查点绑定清单 SHA-256 与冻结配置不一致")
    try:
        manifest = _mapping(
            json.loads(manifest_snapshot.decode("utf-8")),
            "检查点绑定清单",
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise R2FinalProbeError("检查点绑定清单无法解析") from error
    if (
        manifest.get("schema_version") != "flow_probe_r2_checkpoint_binding_manifest_v1"
        or manifest.get("status") != "frozen"
        or manifest.get("immutable") is not True
    ):
        raise R2FinalProbeError("检查点绑定清单未处于不可变冻结状态")
    checkpoint_path = _lexical_absolute(checkpoint_spec.path)
    if (
        _lexical_absolute(Path(_string(manifest.get("checkpoint_path"), "检查点清单路径")))
        != checkpoint_path
    ):
        raise R2FinalProbeError("检查点绑定清单的规范路径与运行配置不一致")
    if (
        _lexical_absolute(Path(_string(manifest.get("fit_config_path"), "拟合配置清单路径")))
        != fit_path
    ):
        raise R2FinalProbeError("检查点绑定清单的拟合配置路径不一致")
    if _lexical_absolute(
        Path(_string(manifest.get("input_path"), "物理输入清单路径"))
    ) != _lexical_absolute(fit_config.data.artifact.path):
        raise R2FinalProbeError("检查点绑定清单的物理输入路径不一致")
    if manifest.get("fit_config_sha256") != config.physics.fit_config.sha256:
        raise R2FinalProbeError("检查点绑定清单的拟合配置哈希不一致")
    if manifest.get("input_sha256") != fit_config.data.artifact_payload_merkle_sha256:
        raise R2FinalProbeError("检查点绑定清单的物理输入哈希不一致")
    if manifest.get("seed") != config.seed or manifest.get("mode") != fit_config.mode:
        raise R2FinalProbeError("检查点绑定清单的种子或模式不一致")
    if manifest.get("checkpoint_binding") != expected_binding:
        raise R2FinalProbeError("检查点绑定清单的训练绑定不一致")
    system = build_system(fit_config)
    unified_control = build_unified_control_system(fit_config)
    history_control = build_history_control_system(fit_config)
    with _open_stable_regular_file(
        checkpoint_path,
        "物理检查点",
        trusted_root=config.project_root,
    ) as source:
        checkpoint_sha256 = _open_file_sha256(source)
        if checkpoint_spec.sha256 != checkpoint_sha256:
            raise R2FinalProbeError(
                "物理检查点 SHA-256 不一致："
                f"预期 {checkpoint_spec.sha256}，实际 {checkpoint_sha256}"
            )
        if manifest.get("checkpoint_sha256") != checkpoint_sha256:
            raise R2FinalProbeError("检查点内容哈希与不可变绑定清单不一致")
        values = torch.load(source, map_location="cpu", weights_only=False)
    if not isinstance(values, dict) or values.get("schema_version") is None:
        raise R2FinalProbeError("物理检查点顶层结构非法")
    if values.get("config_sha256") != expected_binding["config_sha256"]:
        raise R2FinalProbeError("物理检查点顶层配置语义哈希不一致")
    if values.get("fit_config_sha256") != expected_binding["fit_config_sha256"]:
        raise R2FinalProbeError("物理检查点顶层拟合配置文件哈希不一致")
    if values.get("quic_expert_ready") is not config.physics.quic_expert_ready:
        raise R2FinalProbeError("物理检查点与运行配置的 QUIC 就绪状态不一致")
    capacity = values.get("capacity_receipt")
    if not isinstance(capacity, Mapping):
        raise R2FinalProbeError("物理检查点缺少容量收据")
    if capacity.get("equal_total_trainable_frozen") is not True:
        raise R2FinalProbeError("F-A/F-P 检查点容量不相等")
    routed_capacity = capacity.get("routed_active")
    unified_capacity = capacity.get("unified_control")
    history_capacity = capacity.get("history_control")
    if (
        not isinstance(routed_capacity, Mapping)
        or not isinstance(unified_capacity, Mapping)
        or not isinstance(history_capacity, Mapping)
    ):
        raise R2FinalProbeError("物理检查点缺少三条比较支路的参数收据")
    expected_capacity_keys = {"total", "trainable", "frozen"}
    if (
        set(routed_capacity) != expected_capacity_keys
        or set(unified_capacity) != expected_capacity_keys
    ):
        raise R2FinalProbeError("物理检查点参数收据字段不完整")
    if dict(routed_capacity) != dict(unified_capacity):
        raise R2FinalProbeError("物理检查点两条支路容量收据不一致")
    if dict(routed_capacity) != dict(history_capacity):
        raise R2FinalProbeError("历史控制与路由物理支路容量收据不一致")
    if int(routed_capacity["trainable"]) != int(routed_capacity["total"]):
        raise R2FinalProbeError("物理检查点活跃支路未全部参与训练")
    if int(routed_capacity["frozen"]) != 0:
        raise R2FinalProbeError("物理检查点活跃支路含冻结填充参数")
    stored_residual_receipt = values.get("zero_collapse_receipt")
    current_residual_receipt = fixed_residual_zero_collapse_receipt(system)
    if stored_residual_receipt != current_residual_receipt:
        raise R2FinalProbeError("物理检查点固定残差零坍缩收据与当前实现不一致")
    if not bool(current_residual_receipt["formal_tcp_udp_dynamics_ready"]):
        raise R2FinalProbeError("物理检查点未通过固定协议动力学门禁")
    checkpoint_binding_payload = values.get("checkpoint_binding")
    if not isinstance(checkpoint_binding_payload, Mapping):
        raise R2FinalProbeError("物理检查点缺少训练绑定")
    if dict(checkpoint_binding_payload) != expected_binding:
        raise R2FinalProbeError("物理检查点内部训练绑定与当前运行不一致")
    binding_sha256 = hashlib.sha256(
        json.dumps(dict(checkpoint_binding_payload), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    system.load_state_dict(values["routed_system"], strict=True)
    unified_state = values.get("unified_control")
    if not isinstance(unified_state, Mapping):
        raise R2FinalProbeError("物理检查点缺少已训练统一控制支路")
    unified_control.load_state_dict(unified_state, strict=True)
    history_state = values.get("history_control")
    if not isinstance(history_state, Mapping):
        raise R2FinalProbeError("物理检查点缺少已训练历史控制支路")
    history_control.load_state_dict(history_state, strict=True)
    system.quic_expert_ready = config.physics.quic_expert_ready
    system.freeze_for_classification()
    unified_control.freeze_for_classification()
    history_control.freeze_for_classification()
    system.assert_classification_isolation()
    unified_control.assert_classification_isolation()
    history_control.assert_classification_isolation()
    return (
        fit_config,
        system,
        unified_control,
        history_control,
        checkpoint_sha256,
        capacity,
        binding_sha256,
    )


def _production_sha256(
    *,
    mode: str,
    split: Any,
    checkpoint_sha256: str,
    quic_expert_ready: bool,
) -> str:
    payload = {
        "mode": mode,
        "sample_order_sha256": strings_sha256(split.sample_ids),
        "stable_order_sha256": array_sha256(split.stable_orders),
        "history_sha256": array_sha256(split.histories),
        "route_sha256": array_sha256(split.route_indices),
        "checkpoint_sha256": checkpoint_sha256,
        "quic_expert_ready": quic_expert_ready,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _produce_bound_sequences(
    *,
    system: Any,
    unified_control: Any,
    base: Any,
    checkpoint_sha256: str,
    capacity_receipt: Mapping[str, object],
    checkpoint_binding_sha256: str,
    quic_expert_ready: bool,
    batch_size: int,
    torch: Any,
    device: Any,
) -> tuple[Mapping[str, BoundSequence], Mapping[str, BoundSequence]]:
    system.to(device)
    unified_control.to(device)
    system.eval()
    unified_control.eval()
    routed_capacity = capacity_receipt["routed_active"]
    unified_capacity = capacity_receipt["unified_control"]
    if not isinstance(routed_capacity, Mapping) or not isinstance(unified_capacity, Mapping):
        raise R2FinalProbeError("参数容量收据非法")
    unified: dict[str, BoundSequence] = {}
    physics: dict[str, BoundSequence] = {}
    for name, split in (
        ("train-fit", base.train),
        ("calibration", base.calibration),
        ("validation", base.validation),
    ):
        unified_parts: list[np.ndarray] = []
        physics_parts: list[np.ndarray] = []
        with torch.no_grad():
            for start in range(0, len(split), batch_size):
                stop = min(start + batch_size, len(split))
                observations = torch.tensor(
                    split.histories[start:stop], dtype=torch.float32, device=device
                )
                valid = torch.tensor(split.valid_masks[start:stop], dtype=torch.bool, device=device)
                actual_route = RouteBatch(
                    route_index=torch.tensor(
                        split.route_indices[start:stop], dtype=torch.int64, device=device
                    ),
                    confidence=torch.tensor(
                        split.route_confidences[start:stop],
                        dtype=torch.float32,
                        device=device,
                    ),
                    quic_applicable=torch.tensor(
                        split.quic_applicable[start:stop], dtype=torch.bool, device=device
                    ),
                )
                unified_parts.append(
                    unified_control(observations, valid)
                    .sidecar_sequence.detach()
                    .float()
                    .cpu()
                    .numpy()
                )
                physics_parts.append(
                    system(observations, valid, actual_route)
                    .sidecar_sequence.detach()
                    .float()
                    .cpu()
                    .numpy()
                )
        values = {
            "unified": np.concatenate(unified_parts),
            "physics": np.concatenate(physics_parts),
        }
        for mode, target, branch_capacity, branch_name in (
            ("unified", unified, unified_capacity, "unified_control"),
            ("physics", physics, routed_capacity, "routed_active"),
        ):
            parameter_count = int(branch_capacity["total"])
            target[name] = BoundSequence(
                sample_ids=split.sample_ids,
                stable_orders=split.stable_orders,
                values=values[mode],
                checkpoint_sha256=checkpoint_sha256,
                production_sha256=_production_sha256(
                    mode=mode,
                    split=split,
                    checkpoint_sha256=checkpoint_sha256,
                    quic_expert_ready=quic_expert_ready,
                ),
                parameter_count=parameter_count,
                trainable_parameter_count=0,
                frozen_parameter_count=parameter_count,
                checkpoint_trainable_parameter_count=int(branch_capacity["trainable"]),
                checkpoint_frozen_parameter_count=int(branch_capacity["frozen"]),
                branch_name=branch_name,
                checkpoint_binding_sha256=checkpoint_binding_sha256,
                quic_expert_ready=quic_expert_ready,
            )
    system.to("cpu")
    unified_control.to("cpu")
    return unified, physics


def _physical_donor_indices(
    variant: str,
    validation: Any,
    train: Any,
    seed: int,
) -> tuple[np.ndarray, Any, tuple[str, ...]]:
    if variant not in ("F-S", "F-R"):
        indices = np.arange(len(validation), dtype=np.int64)
        return indices, validation, validation.sequence_ids
    if variant == "F-S":
        donors = np.full(len(validation), -1, dtype=np.int64)
        for route_index in sorted(set(validation.route_index.tolist())):
            members = np.flatnonzero(validation.route_index == route_index).tolist()
            if len(members) < 2:
                raise R2FinalProbeError("F-S 物理验证分层不足两个序列")
            ordered = sorted(
                members,
                key=lambda index: hashlib.sha256(
                    f"r2-g3-shuffle-v1\0{seed}\0{validation.sequence_ids[index]}".encode("utf-8")
                ).hexdigest(),
            )
            rotated = ordered[1:] + ordered[:1]
            for target, donor in zip(ordered, rotated, strict=True):
                donors[target] = donor
        if np.any(donors < 0) or np.any(donors == np.arange(len(validation))):
            raise R2FinalProbeError("F-S 物理验证供体不完整或出现自配对")
        return donors, validation, tuple(validation.sequence_ids[int(index)] for index in donors)
    donors = np.full(len(validation), -1, dtype=np.int64)
    for target in range(len(validation)):
        eligible = np.flatnonzero(train.route_index == validation.route_index[target]).tolist()
        if not eligible:
            raise R2FinalProbeError("F-R 物理训练池缺少同协议供体")
        digest = hashlib.sha256(
            f"r2-g3-random-v1\0{seed}\0{validation.sequence_ids[target]}".encode("utf-8")
        ).digest()
        donors[target] = eligible[int.from_bytes(digest[:8], "big") % len(eligible)]
    return donors, train, tuple(train.sequence_ids[int(index)] for index in donors)


def _masked_state_statistics(
    prediction: np.ndarray,
    truth: np.ndarray,
    mask: np.ndarray,
    normalization: Mapping[str, object],
) -> Mapping[str, object]:
    if prediction.shape != truth.shape or mask.shape != truth.shape:
        raise R2FinalProbeError("G3 状态预测、真值和掩码形状不一致")
    mean = np.asarray(normalization["mean"], dtype=np.float64)
    scale = np.asarray(normalization["scale"], dtype=np.float64)
    raw_scale = np.asarray(normalization["raw_scale"], dtype=np.float64)
    metric_state_mask = np.asarray(normalization["metric_state_mask"], dtype=bool)
    degenerate_state_indices = np.asarray(normalization["degenerate_state_indices"], dtype=np.int64)
    if (
        mean.shape != prediction.shape[-1:]
        or scale.shape != prediction.shape[-1:]
        or raw_scale.shape != prediction.shape[-1:]
        or metric_state_mask.shape != prediction.shape[-1:]
    ):
        raise R2FinalProbeError("G3 状态训练区归一化统计量维数不一致")
    if not np.isfinite(scale).all() or np.any(scale <= 0):
        raise R2FinalProbeError("G3 状态训练区归一化尺度必须为有限正数")
    if not np.array_equal(np.flatnonzero(~metric_state_mask), degenerate_state_indices):
        raise R2FinalProbeError("G3 状态退化维索引与指标掩码不一致")
    counts = mask.sum(axis=(0, 1)).astype(np.int64)
    cluster_metric_state_mask = metric_state_mask & (counts > 0)
    if not np.any(cluster_metric_state_mask):
        raise R2FinalProbeError("G3 当前评价簇缺少可观测的正式状态维度")
    prediction_sum = np.where(mask, prediction, 0.0).sum(axis=(0, 1))
    truth_sum = np.where(mask, truth, 0.0).sum(axis=(0, 1))
    normalized_error = (prediction.astype(np.float64) - truth.astype(np.float64)) / scale
    squared_error = np.where(mask, np.square(normalized_error), 0.0)
    squared_sum = squared_error.sum(axis=(0, 1))
    mse_by_state = np.divide(
        squared_sum,
        counts,
        out=np.zeros_like(squared_sum, dtype=np.float64),
        where=counts > 0,
    )
    raw_squared_error = np.where(
        mask, np.square(prediction.astype(np.float64) - truth.astype(np.float64)), 0.0
    )
    raw_squared_sum = raw_squared_error.sum(axis=(0, 1))
    raw_mse_by_state = np.divide(
        raw_squared_sum,
        counts,
        out=np.zeros_like(raw_squared_sum, dtype=np.float64),
        where=counts > 0,
    )
    metric_mse_by_state = mse_by_state[cluster_metric_state_mask]
    return {
        "prediction_mean": np.divide(
            prediction_sum,
            counts,
            out=np.zeros_like(prediction_sum, dtype=np.float64),
            where=counts > 0,
        ).tolist(),
        "truth_mean": np.divide(
            truth_sum,
            counts,
            out=np.zeros_like(truth_sum, dtype=np.float64),
            where=counts > 0,
        ).tolist(),
        "mask_count_by_state": counts.tolist(),
        "mask_sha256": array_sha256(mask.astype(bool, copy=False)),
        "normalization_mean": mean.tolist(),
        "normalization_scale": scale.tolist(),
        "normalization_raw_scale": raw_scale.tolist(),
        "metric_state_mask": metric_state_mask.tolist(),
        "cluster_metric_state_mask": cluster_metric_state_mask.tolist(),
        "missing_metric_state_indices": np.flatnonzero(
            metric_state_mask & ~cluster_metric_state_mask
        ).tolist(),
        "degenerate_state_indices": degenerate_state_indices.tolist(),
        "squared_error_sum_by_state": squared_sum.tolist(),
        "observed_count_by_state": counts.tolist(),
        "mse_by_state": mse_by_state.tolist(),
        "metric_squared_error_sum_by_state": squared_sum[metric_state_mask].tolist(),
        "metric_observed_count_by_state": counts[metric_state_mask].tolist(),
        "metric_mse_by_state": metric_mse_by_state.tolist(),
        "degenerate_raw_mse_by_state": raw_mse_by_state[~metric_state_mask].tolist(),
        "equal_state_mse_numerator": float(metric_mse_by_state.sum()),
        "equal_state_mse_denominator": int(metric_mse_by_state.size),
        "state_mse": float(metric_mse_by_state.mean()),
        "unit": "squared_training_standardized_state",
        "aggregation": "masked_time_mean_per_observed_non_degenerate_state_then_equal_observed_state_mean",
    }


def _residual_statistics(residual: np.ndarray, mask: np.ndarray) -> Mapping[str, object]:
    if residual.shape[:2] != mask.shape:
        raise R2FinalProbeError("G3 物理残差与有效掩码形状不一致")
    expanded = np.broadcast_to(mask[..., None], residual.shape)
    counts = expanded.sum(axis=(0, 1)).astype(np.int64)
    if np.any(counts <= 0):
        raise R2FinalProbeError("G3 逐簇物理方程缺少有效时间点")
    squared_sum = np.where(expanded, np.square(residual), 0.0).sum(axis=(0, 1))
    mse_by_equation = squared_sum / counts
    return {
        "squared_residual_sum_by_equation": squared_sum.tolist(),
        "observed_count_by_equation": counts.tolist(),
        "mse_by_equation": mse_by_equation.tolist(),
        "equal_equation_mse_numerator": float(mse_by_equation.sum()),
        "equal_equation_mse_denominator": int(len(mse_by_equation)),
        "physics_residual_mse": float(mse_by_equation.mean()),
        "unit": "dimensionless_squared_physics_residual",
        "aggregation": "masked_time_mean_per_equation_then_equal_equation_mean",
        "mask_sha256": array_sha256(mask.astype(bool, copy=False)),
    }


def _training_state_normalization(
    split: PhysicsSplit,
    expert_name: str,
) -> Mapping[str, object]:
    truth = split.truths[expert_name].astype(np.float64)
    mask = split.truth_masks[expert_name] & split.valid_mask[..., None]
    counts = mask.sum(axis=(0, 1)).astype(np.int64)
    if np.any(counts < 2):
        raise R2FinalProbeError(f"G3 训练区 {expert_name} 状态归一化观测不足")
    sums = np.where(mask, truth, 0.0).sum(axis=(0, 1))
    mean = sums / counts
    centered = np.where(mask, truth - mean, 0.0)
    raw_scale = np.sqrt(np.square(centered).sum(axis=(0, 1)) / counts)
    degenerate_state_mask = np.zeros_like(raw_scale, dtype=bool)
    if (
        expert_name == EXPERT_UDP
        and raw_scale.shape == (6,)
        and np.array_equal(raw_scale[4:6], np.zeros(2, dtype=np.float64))
        and np.array_equal(mean[4:6], np.zeros(2, dtype=np.float64))
    ):
        degenerate_state_mask[4:6] = True
    if (
        not np.isfinite(mean).all()
        or not np.isfinite(raw_scale).all()
        or np.any((raw_scale <= 0) & ~degenerate_state_mask)
    ):
        raise R2FinalProbeError(f"G3 训练区 {expert_name} 存在零方差或非有限状态维度")
    scale = np.where(degenerate_state_mask, 1.0, raw_scale)
    return {
        "mean": mean.tolist(),
        "scale": scale.tolist(),
        "raw_scale": raw_scale.tolist(),
        "metric_state_mask": (~degenerate_state_mask).tolist(),
        "degenerate_state_indices": np.flatnonzero(degenerate_state_mask).tolist(),
        "observed_count_by_state": counts.tolist(),
        "fit_split": "train-fit",
        "estimator": "population_standard_deviation",
    }


def _combine_equal_component_metric(
    statistics: Sequence[Mapping[str, object]],
    component_key: str,
) -> Mapping[str, object]:
    components = [
        np.asarray(statistic[component_key], dtype=np.float64) for statistic in statistics
    ]
    if not components or any(component.size == 0 for component in components):
        raise R2FinalProbeError("G3 等权指标缺少状态或方程分量")
    values = np.concatenate(components)
    return {
        "numerator": float(values.sum()),
        "denominator": int(values.size),
        "value": float(values.mean()),
    }


def _pooled_protocol_metric(
    rows: Sequence[Mapping[str, object]],
    components: Sequence[tuple[str, str]],
) -> Mapping[str, object]:
    values: list[np.ndarray] = []
    for numerator_key, denominator_key in components:
        numerators = np.stack([np.asarray(row[numerator_key], dtype=np.float64) for row in rows])
        denominators = np.stack([np.asarray(row[denominator_key], dtype=np.int64) for row in rows])
        pooled_denominator = denominators.sum(axis=0)
        if np.any(pooled_denominator <= 0):
            raise R2FinalProbeError("G3 分协议汇总存在无有效观测的分量")
        values.append(numerators.sum(axis=0) / pooled_denominator)
    merged = np.concatenate(values)
    return {
        "numerator": float(merged.sum()),
        "denominator": int(merged.size),
        "value": float(merged.mean()),
    }


def _physical_validation_artifacts(
    *,
    variant: str,
    fit_config: PhysicsFitConfig,
    system: Any,
    unified_control: Any,
    history_control: Any,
    checkpoint_sha256: str,
    checkpoint_binding_sha256: str,
    seed: int,
    batch_size: int,
    torch: Any,
    device: Any,
) -> tuple[list[Mapping[str, object]], Mapping[str, object]]:
    splits = load_physics_splits(fit_config)
    train = splits["train-fit"]
    validation = splits["validation"]
    state_normalization = {
        name: _training_state_normalization(train, name)
        for name in (EXPERT_SHARED, EXPERT_TCP, EXPERT_UDP)
    }
    donors, donor_split, donor_ids = _physical_donor_indices(variant, validation, train, seed)
    system.to(device).eval()
    unified_control.to(device).eval()
    history_control.to(device).eval()
    fragments: list[Mapping[str, object]] = []
    with torch.no_grad():
        for start in range(0, len(validation), batch_size):
            stop = min(start + batch_size, len(validation))
            target_indices = np.arange(start, stop, dtype=np.int64)
            source_indices = donors[target_indices]
            observations = torch.tensor(
                donor_split.observations[source_indices],
                dtype=torch.float32,
                device=device,
            )
            valid = torch.tensor(
                donor_split.valid_mask[source_indices], dtype=torch.bool, device=device
            )
            route = RouteBatch(
                route_index=torch.tensor(
                    validation.route_index[target_indices],
                    dtype=torch.int64,
                    device=device,
                ),
                confidence=torch.tensor(
                    validation.route_confidence[target_indices],
                    dtype=torch.float32,
                    device=device,
                ),
                quic_applicable=torch.tensor(
                    validation.quic_applicable[target_indices],
                    dtype=torch.bool,
                    device=device,
                ),
            )
            residual_contexts = {
                name: ResidualObservationContext(
                    observed_state=torch.tensor(
                        validation.truths[name][target_indices],
                        dtype=torch.float32,
                        device=device,
                    ),
                    observed_mask=torch.tensor(
                        validation.truth_masks[name][target_indices],
                        dtype=torch.bool,
                        device=device,
                    ),
                )
                for name in (EXPERT_SHARED, EXPERT_TCP, EXPERT_UDP)
            }
            if variant == "F-A":
                output = unified_control(observations, valid, residual_contexts=residual_contexts)
            elif variant == "F-H":
                output = history_control(
                    observations,
                    valid,
                    route,
                    residual_contexts=residual_contexts,
                )
            else:
                output = system(
                    observations,
                    valid,
                    route,
                    residual_contexts=residual_contexts,
                )
            shared = output.shared
            shared_prediction = shared.predicted_state.detach().float().cpu().numpy()
            shared_residual = shared.physics_residual.detach().float().cpu().numpy()
            for local, target_index in enumerate(target_indices.tolist()):
                evaluation_protocol = ROUTE_NAMES[int(validation.route_index[target_index])]
                if evaluation_protocol not in ("TCP", "UDP"):
                    raise R2FinalProbeError("正式 G3 物理验证只允许 TCP/UDP")
                protocol_output = output.protocol_outputs[evaluation_protocol]
                effective_route = ROUTE_NAMES[
                    int(output.effective_route_index[local].detach().cpu().item())
                ]
                actual_branch = "UNIFIED_NON_ROUTED" if variant == "F-A" else effective_route
                fragments.append(
                    {
                        "evaluation_cluster_id": validation.evaluation_cluster_ids[target_index],
                        "sequence_id": validation.sequence_ids[target_index],
                        "donor_sequence_id": donor_ids[target_index],
                        "evaluation_protocol": evaluation_protocol,
                        "effective_route": effective_route,
                        "actual_branch": actual_branch,
                        "shared_prediction": shared_prediction[local : local + 1],
                        "shared_residual": shared_residual[local : local + 1],
                        "protocol_prediction": protocol_output.predicted_state[local : local + 1]
                        .detach()
                        .float()
                        .cpu()
                        .numpy(),
                        "protocol_residual": protocol_output.physics_residual[local : local + 1]
                        .detach()
                        .float()
                        .cpu()
                        .numpy(),
                        "shared_truth": validation.truths[EXPERT_SHARED][
                            target_index : target_index + 1
                        ],
                        "shared_mask": validation.truth_masks[EXPERT_SHARED][
                            target_index : target_index + 1
                        ]
                        & donor_split.valid_mask[
                            source_indices[local] : source_indices[local] + 1, :, None
                        ],
                        "protocol_truth": validation.truths[
                            EXPERT_TCP if evaluation_protocol == "TCP" else EXPERT_UDP
                        ][target_index : target_index + 1],
                        "protocol_mask": validation.truth_masks[
                            EXPERT_TCP if evaluation_protocol == "TCP" else EXPERT_UDP
                        ][target_index : target_index + 1]
                        & donor_split.valid_mask[
                            source_indices[local] : source_indices[local] + 1, :, None
                        ],
                        "residual_mask": donor_split.valid_mask[
                            source_indices[local] : source_indices[local] + 1
                        ],
                    }
                )
    grouped: dict[tuple[str, str], list[Mapping[str, object]]] = {}
    for fragment in fragments:
        key = (
            str(fragment["evaluation_cluster_id"]),
            str(fragment["evaluation_protocol"]),
        )
        grouped.setdefault(key, []).append(fragment)
    rows: list[Mapping[str, object]] = []
    for (cluster_id, protocol), members in sorted(grouped.items()):
        effective_routes = {str(item["effective_route"]) for item in members}
        actual_branches = {str(item["actual_branch"]) for item in members}
        if len(effective_routes) != 1 or len(actual_branches) != 1:
            raise R2FinalProbeError("同一 G3 评价簇的实际执行支路不唯一")
        shared_prediction = np.concatenate(
            [np.asarray(item["shared_prediction"]) for item in members]
        )
        shared_truth = np.concatenate([np.asarray(item["shared_truth"]) for item in members])
        shared_mask = np.concatenate(
            [np.asarray(item["shared_mask"], dtype=bool) for item in members]
        )
        protocol_prediction = np.concatenate(
            [np.asarray(item["protocol_prediction"]) for item in members]
        )
        protocol_truth = np.concatenate([np.asarray(item["protocol_truth"]) for item in members])
        protocol_mask = np.concatenate(
            [np.asarray(item["protocol_mask"], dtype=bool) for item in members]
        )
        residual_mask = np.concatenate(
            [np.asarray(item["residual_mask"], dtype=bool) for item in members]
        )
        shared_state = _masked_state_statistics(
            shared_prediction,
            shared_truth,
            shared_mask,
            state_normalization[EXPERT_SHARED],
        )
        protocol_state = _masked_state_statistics(
            protocol_prediction,
            protocol_truth,
            protocol_mask,
            state_normalization[EXPERT_TCP if protocol == "TCP" else EXPERT_UDP],
        )
        shared_residual = _residual_statistics(
            np.concatenate([np.asarray(item["shared_residual"]) for item in members]),
            residual_mask,
        )
        protocol_residual = _residual_statistics(
            np.concatenate([np.asarray(item["protocol_residual"]) for item in members]),
            residual_mask,
        )
        state_metric = _combine_equal_component_metric(
            (shared_state, protocol_state), "metric_mse_by_state"
        )
        residual_metric = _combine_equal_component_metric(
            (shared_residual, protocol_residual), "mse_by_equation"
        )
        rows.append(
            {
                "variant": variant,
                "seed": seed,
                "evaluation_cluster_id": cluster_id,
                "evaluation_protocol": protocol,
                "effective_route": next(iter(effective_routes)),
                "actual_branch": next(iter(actual_branches)),
                "sequence_count": len(members),
                "sequence_ids_sha256": strings_sha256(
                    tuple(str(item["sequence_id"]) for item in members)
                ),
                "sequence_ids": [str(item["sequence_id"]) for item in members],
                "donor_sequence_ids_sha256": strings_sha256(
                    tuple(str(item["donor_sequence_id"]) for item in members)
                ),
                "donor_sequence_ids": [str(item["donor_sequence_id"]) for item in members],
                "checkpoint_sha256": checkpoint_sha256,
                "checkpoint_binding_sha256": checkpoint_binding_sha256,
                "shared_state_prediction": shared_prediction.tolist(),
                "shared_state_truth": shared_truth.tolist(),
                "shared_state_mask": shared_mask.tolist(),
                "shared_state_prediction_mean": shared_state["prediction_mean"],
                "shared_state_truth_mean": shared_state["truth_mean"],
                "shared_state_mask_count": shared_state["mask_count_by_state"],
                "shared_state_mask_sha256": shared_state["mask_sha256"],
                "shared_state_normalization_mean": shared_state["normalization_mean"],
                "shared_state_normalization_scale": shared_state["normalization_scale"],
                "shared_state_normalization_raw_scale": shared_state["normalization_raw_scale"],
                "shared_state_metric_mask": shared_state["metric_state_mask"],
                "shared_state_degenerate_indices": shared_state["degenerate_state_indices"],
                "shared_state_squared_error_sum_by_state": shared_state[
                    "squared_error_sum_by_state"
                ],
                "shared_state_observed_count_by_state": shared_state["observed_count_by_state"],
                "shared_state_mse_by_state": shared_state["mse_by_state"],
                "shared_state_metric_squared_error_sum_by_state": shared_state[
                    "metric_squared_error_sum_by_state"
                ],
                "shared_state_metric_observed_count_by_state": shared_state[
                    "metric_observed_count_by_state"
                ],
                "shared_state_metric_mse_by_state": shared_state["metric_mse_by_state"],
                "shared_state_degenerate_raw_mse_by_state": shared_state[
                    "degenerate_raw_mse_by_state"
                ],
                "protocol_state_prediction": protocol_prediction.tolist(),
                "protocol_state_truth": protocol_truth.tolist(),
                "protocol_state_mask": protocol_mask.tolist(),
                "protocol_state_prediction_mean": protocol_state["prediction_mean"],
                "protocol_state_truth_mean": protocol_state["truth_mean"],
                "protocol_state_mask_count": protocol_state["mask_count_by_state"],
                "protocol_state_mask_sha256": protocol_state["mask_sha256"],
                "protocol_state_normalization_mean": protocol_state["normalization_mean"],
                "protocol_state_normalization_scale": protocol_state["normalization_scale"],
                "protocol_state_normalization_raw_scale": protocol_state["normalization_raw_scale"],
                "protocol_state_metric_mask": protocol_state["metric_state_mask"],
                "protocol_state_degenerate_indices": protocol_state["degenerate_state_indices"],
                "protocol_state_squared_error_sum_by_state": protocol_state[
                    "squared_error_sum_by_state"
                ],
                "protocol_state_observed_count_by_state": protocol_state["observed_count_by_state"],
                "protocol_state_mse_by_state": protocol_state["mse_by_state"],
                "protocol_state_metric_squared_error_sum_by_state": protocol_state[
                    "metric_squared_error_sum_by_state"
                ],
                "protocol_state_metric_observed_count_by_state": protocol_state[
                    "metric_observed_count_by_state"
                ],
                "protocol_state_metric_mse_by_state": protocol_state["metric_mse_by_state"],
                "protocol_state_degenerate_raw_mse_by_state": protocol_state[
                    "degenerate_raw_mse_by_state"
                ],
                "shared_physics_residual": np.concatenate(
                    [np.asarray(item["shared_residual"]) for item in members]
                ).tolist(),
                "protocol_physics_residual": np.concatenate(
                    [np.asarray(item["protocol_residual"]) for item in members]
                ).tolist(),
                "physics_residual_mask": residual_mask.tolist(),
                "shared_residual_mask_sha256": shared_residual["mask_sha256"],
                "protocol_residual_mask_sha256": protocol_residual["mask_sha256"],
                "shared_residual_squared_sum_by_equation": shared_residual[
                    "squared_residual_sum_by_equation"
                ],
                "shared_residual_observed_count_by_equation": shared_residual[
                    "observed_count_by_equation"
                ],
                "shared_residual_mse_by_equation": shared_residual["mse_by_equation"],
                "protocol_residual_squared_sum_by_equation": protocol_residual[
                    "squared_residual_sum_by_equation"
                ],
                "protocol_residual_observed_count_by_equation": protocol_residual[
                    "observed_count_by_equation"
                ],
                "protocol_residual_mse_by_equation": protocol_residual["mse_by_equation"],
                "state_mse_numerator": state_metric["numerator"],
                "state_mse_denominator": state_metric["denominator"],
                "state_mse": state_metric["value"],
                "state_mse_unit": "squared_training_standardized_state",
                "state_mse_aggregation": (
                    "masked_time_mean_per_state_then_equal_shared_and_protocol_state_mean"
                ),
                "physics_residual_mse_numerator": residual_metric["numerator"],
                "physics_residual_mse_denominator": residual_metric["denominator"],
                "physics_residual_mse": residual_metric["value"],
                "physics_residual_mse_unit": ("dimensionless_squared_physics_residual"),
                "physics_residual_mse_aggregation": (
                    "masked_time_mean_per_equation_then_equal_shared_and_protocol_equation_mean"
                ),
            }
        )
    expected_clusters = set(validation.evaluation_cluster_ids)
    expected_pairs = {
        (cluster, protocol) for cluster in expected_clusters for protocol in ("TCP", "UDP")
    }
    observed_pairs = {
        (str(row["evaluation_cluster_id"]), str(row["evaluation_protocol"])) for row in rows
    }
    if observed_pairs != expected_pairs:
        raise R2FinalProbeError("G3 逐簇输出未覆盖完整验证簇与协议")
    by_protocol: dict[str, Mapping[str, object]] = {}
    for protocol in ("TCP", "UDP"):
        selected = [row for row in rows if row["evaluation_protocol"] == protocol]
        if not selected:
            raise R2FinalProbeError(f"G3 缺少 {protocol} 验证簇")
        state_metric = _pooled_protocol_metric(
            selected,
            (
                (
                    "shared_state_metric_squared_error_sum_by_state",
                    "shared_state_metric_observed_count_by_state",
                ),
                (
                    "protocol_state_metric_squared_error_sum_by_state",
                    "protocol_state_metric_observed_count_by_state",
                ),
            ),
        )
        residual_metric = _pooled_protocol_metric(
            selected,
            (
                (
                    "shared_residual_squared_sum_by_equation",
                    "shared_residual_observed_count_by_equation",
                ),
                (
                    "protocol_residual_squared_sum_by_equation",
                    "protocol_residual_observed_count_by_equation",
                ),
            ),
        )
        by_protocol[protocol] = {
            "cluster_count": len(selected),
            "state_mse_numerator": state_metric["numerator"],
            "state_mse_denominator": state_metric["denominator"],
            "state_mse": state_metric["value"],
            "state_mse_unit": "squared_training_standardized_state",
            "physics_residual_mse_numerator": residual_metric["numerator"],
            "physics_residual_mse_denominator": residual_metric["denominator"],
            "physics_residual_mse": residual_metric["value"],
            "physics_residual_mse_unit": "dimensionless_squared_physics_residual",
        }
    aggregate = {
        "variant": variant,
        "seed": seed,
        "checkpoint_sha256": checkpoint_sha256,
        "checkpoint_binding_sha256": checkpoint_binding_sha256,
        "cluster_protocol_row_count": len(rows),
        "by_protocol": by_protocol,
        "state_training_normalization": state_normalization,
        "equal_protocol_state_mse_numerator": float(
            sum(float(by_protocol[name]["state_mse"]) for name in ("TCP", "UDP"))
        ),
        "equal_protocol_state_mse_denominator": 2,
        "equal_protocol_state_mse": float(
            np.mean([by_protocol[name]["state_mse"] for name in ("TCP", "UDP")])
        ),
        "equal_protocol_physics_residual_mse_numerator": float(
            sum(float(by_protocol[name]["physics_residual_mse"]) for name in ("TCP", "UDP"))
        ),
        "equal_protocol_physics_residual_mse_denominator": 2,
        "equal_protocol_physics_residual_mse": float(
            np.mean([by_protocol[name]["physics_residual_mse"] for name in ("TCP", "UDP")])
        ),
        "state_mse_unit": "squared_training_standardized_state",
        "physics_residual_mse_unit": "dimensionless_squared_physics_residual",
        "aggregation": (
            "masked_time_mean_per_component_then_equal_component_mean_then_equal_protocol_mean"
        ),
        "final_test_visible": False,
    }
    system.to("cpu")
    unified_control.to("cpu")
    history_control.to("cpu")
    return rows, aggregate


class _VariantDataset:
    def __init__(self, split: VariantSplit) -> None:
        self.split = split

    def __len__(self) -> int:
        return len(self.split)

    def __getitem__(self, index: int) -> tuple[object, ...]:
        return (
            self.split.texts[index],
            int(self.split.labels[index]),
            self.split.sidecar_sequence[index],
            self.split.sidecar_valid_mask[index],
            float(self.split.sidecar_gate[index]),
        )


def _collate(tokenizer: Any, max_length: int, torch: Any):
    def collate(items: Sequence[tuple[object, ...]]) -> dict[str, Any]:
        texts, labels, sequences, valid, gates = zip(*items, strict=True)
        encoded = tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch.tensor(labels, dtype=torch.long)
        encoded["sidecar_sequence"] = torch.tensor(np.stack(sequences), dtype=torch.float32)
        encoded["sidecar_valid_mask"] = torch.tensor(np.stack(valid), dtype=torch.bool)
        encoded["sidecar_gate"] = torch.tensor(gates, dtype=torch.float32)
        return encoded

    return collate


def _loader(
    split: VariantSplit,
    config: ProbeConfig,
    tokenizer: Any,
    torch: Any,
    *,
    shuffle: bool,
    seed: int,
) -> Any:
    generator = torch.Generator()
    generator.manual_seed(seed)
    return torch.utils.data.DataLoader(
        _VariantDataset(split),
        batch_size=(
            config.training.per_device_train_batch_size
            if shuffle
            else config.training.per_device_eval_batch_size
        ),
        shuffle=shuffle,
        generator=generator,
        num_workers=config.training.num_workers,
        collate_fn=_collate(tokenizer, config.model.max_length, torch),
        pin_memory=bool(torch.cuda.is_available()),
        persistent_workers=bool(config.training.num_workers),
    )


def _build_model(
    modules: baseline.RuntimeModules,
    config: ProbeConfig,
    runtime: baseline.RuntimeSelection,
    sidecar_dimension: int,
) -> tuple[Any, Any]:
    tokenizer, backbone = baseline._load_tokenizer_and_model(
        modules,
        config,  # type: ignore[arg-type]
        runtime,
        source=config.model.source,
    )
    if not all(
        hasattr(backbone, name)
        for name in ("distilbert", "pre_classifier", "dropout", "classifier")
    ):
        raise R2FinalProbeError("本地模型不是可融合的 DistilBERT 分类结构")
    torch = modules.torch
    hidden_size = int(backbone.pre_classifier.in_features)

    class SequenceSidecarClassifier(torch.nn.Module):
        def __init__(self, base: Any) -> None:
            super().__init__()
            self.backbone = base
            self.sidecar_encoder = torch.nn.GRU(
                input_size=sidecar_dimension,
                hidden_size=128,
                batch_first=True,
            )
            self.sidecar_projection = torch.nn.Linear(128, hidden_size, bias=False)
            self.fusion_logit = torch.nn.Parameter(torch.tensor(0.0))

        def forward(
            self,
            *,
            input_ids: Any,
            attention_mask: Any,
            sidecar_sequence: Any,
            sidecar_valid_mask: Any,
            sidecar_gate: Any,
            labels: Any | None = None,
        ) -> ProbeOutput:
            if sidecar_sequence.ndim != 3:
                raise R2FinalProbeError("旁路序列必须为 [批量,窗口,字段]")
            if sidecar_valid_mask.shape != sidecar_sequence.shape[:2]:
                raise R2FinalProbeError("旁路有效窗口掩码形状不一致")
            if sidecar_gate.shape != sidecar_sequence.shape[:1]:
                raise R2FinalProbeError("旁路融合门形状不一致")
            lengths = sidecar_valid_mask.to(torch.int64).sum(dim=1)
            text_hidden = self.backbone.distilbert(
                input_ids=input_ids,
                attention_mask=attention_mask,
                return_dict=True,
            ).last_hidden_state[:, 0]
            text_representation = torch.nn.functional.relu(
                self.backbone.pre_classifier(text_hidden)
            )
            encoded, _ = self.sidecar_encoder(sidecar_sequence.to(dtype=text_representation.dtype))
            batch_index = torch.arange(encoded.shape[0], device=encoded.device)
            sidecar = encoded[batch_index, torch.clamp(lengths - 1, min=0)]
            sidecar = sidecar * (lengths > 0).unsqueeze(1).to(sidecar.dtype)
            projected = self.sidecar_projection(sidecar)
            bounded_strength = _bounded_residual_strength(self.fusion_logit, torch)
            gate = sidecar_gate.detach().to(dtype=projected.dtype)
            fused = text_representation + bounded_strength * gate[:, None] * projected
            logits = self.backbone.classifier(self.backbone.dropout(fused))
            loss = None if labels is None else torch.nn.functional.cross_entropy(logits, labels)
            return ProbeOutput(logits=logits, loss=loss)

    model = SequenceSidecarClassifier(backbone)
    model.to(runtime.device)
    return tokenizer, model


def _evaluate(
    model: Any,
    tokenizer: Any,
    split: VariantSplit,
    config: ProbeConfig,
    runtime: baseline.RuntimeSelection,
    torch: Any,
) -> tuple[dict[str, int | float], tuple[Mapping[str, object], ...]]:
    probabilities: list[float] = []
    model.eval()
    started = time.perf_counter()
    with torch.no_grad():
        for batch in _loader(split, config, tokenizer, torch, shuffle=False, seed=config.seed):
            batch = {name: value.to(runtime.device) for name, value in batch.items()}
            labels = batch.pop("labels")
            with baseline._autocast(torch, runtime):
                output = model(**batch)
            values = torch.softmax(output.logits.float(), dim=-1)[:, 1]
            probabilities.extend(float(value) for value in values.cpu().tolist())
            if len(probabilities) > len(split):
                raise R2FinalProbeError("评价概率数量超过冻结样本数")
            del labels
    metrics = baseline.compute_binary_metrics(
        split.labels,
        probabilities,
        threshold=config.evaluation.threshold,
        calibration_bins=config.evaluation.calibration_bins,
    )
    elapsed = time.perf_counter() - started
    metrics["inference_seconds"] = elapsed
    metrics["samples_per_second"] = len(split) / max(elapsed, 1e-12)
    rows = tuple(
        {
            "sample_id": sample_id,
            "stable_order": int(stable_order),
            "label": int(label),
            "probability_malicious": probability,
            "prediction": int(probability >= config.evaluation.threshold),
        }
        for sample_id, stable_order, label, probability in zip(
            split.sample_ids,
            split.stable_orders,
            split.labels,
            probabilities,
            strict=True,
        )
    )
    return metrics, rows


class _Logger:
    def __init__(self, config: ProbeConfig, variant: str, output: Path) -> None:
        self.path = output / "metrics.jsonl"
        self.online = config.tracking.mode == "online"
        if self.online:
            try:
                import swanlab
            except ImportError as error:
                raise R2FinalProbeError("在线正式实验要求安装 SwanLab") from error
            swanlab.init(
                project=config.tracking.project,
                workspace=config.tracking.workspace,
                experiment_name=f"{config.tracking.run_name}-{variant.lower()}",
                config={"variant": variant, "seed": config.seed},
                tags=[*config.tracking.tags, variant.lower()],
            )

    def log(self, values: Mapping[str, float], step: int, event: str) -> None:
        row = {"step": step, "event": event, "time": time.time(), **values}
        with self.path.open("a", encoding="utf-8") as target:
            target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        if self.online:
            import swanlab

            swanlab.log(dict(values), step=step)

    def finish(self) -> None:
        if self.online:
            import swanlab

            swanlab.finish()


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as target:
        for row in rows:
            target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _atomic_parquet(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    pd.DataFrame(rows).to_parquet(temporary, index=False)
    os.replace(temporary, path)


def _binding(
    config: ProbeConfig,
    variant: str,
    views: PreparedVariantViews,
    checkpoint_sha256: str,
) -> Mapping[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "variant": variant,
        "seed": config.seed,
        "stage": STAGE,
        "status": STATUS,
        "config_sha256": config.file_sha256,
        "physics_checkpoint_sha256": checkpoint_sha256,
        "quic_expert_ready": config.physics.quic_expert_ready,
        "views": dict(views.binding),
        "final_test_visible": False,
    }


def _train(
    config: ProbeConfig,
    variant: str,
    views: PreparedVariantViews,
    modules: baseline.RuntimeModules,
    runtime: baseline.RuntimeSelection,
    checkpoint_sha256: str,
    physical_rows: Sequence[Mapping[str, object]],
    physical_metrics: Mapping[str, object],
) -> Mapping[str, object]:
    torch = modules.torch
    output = config.output_root / f"seed-{config.seed}" / variant.lower()
    output.mkdir(parents=True, exist_ok=True)
    binding = _binding(config, variant, views, checkpoint_sha256)
    binding_path = output / "run-binding.json"
    if binding_path.exists():
        if json.loads(binding_path.read_text(encoding="utf-8")) != binding:
            raise R2FinalProbeError("已有单组输出绑定与当前运行不一致")
    else:
        _atomic_json(binding_path, binding)
    baseline._set_reproducible_seed(torch, config.seed)
    tokenizer, model = _build_model(
        modules,
        config,
        runtime,
        views.train.sidecar_sequence.shape[-1],
    )
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )
    batches_per_epoch = math.ceil(len(views.train) / config.training.per_device_train_batch_size)
    steps_per_epoch = math.ceil(batches_per_epoch / config.training.gradient_accumulation_steps)
    total_steps = steps_per_epoch * config.training.num_train_epochs
    warmup_steps = int(total_steps * config.training.warmup_ratio)
    scheduler = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda=baseline._linear_schedule_lambda(total_steps, warmup_steps),
    )
    scaler = baseline._new_grad_scaler(torch, runtime.use_grad_scaler)
    checkpoint = output / "checkpoint-latest.pt"
    best = output / "best-model.pt"
    start_epoch = 0
    start_batch = 0
    step = 0
    best_macro_f1 = -1.0
    if checkpoint.is_file() and config.training.resume_from_checkpoint == "auto":
        values = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if values.get("binding") != binding:
            raise R2FinalProbeError("恢复检查点绑定不一致")
        model.load_state_dict(values["model"], strict=True)
        optimizer.load_state_dict(values["optimizer"])
        scheduler.load_state_dict(values["scheduler"])
        scaler.load_state_dict(values["scaler"])
        start_epoch = int(values["next_epoch"])
        start_batch = int(values["next_batch"])
        step = int(values["step"])
        best_macro_f1 = float(values["best_macro_f1"])
    logger = _Logger(config, variant, output)
    _atomic_jsonl(output / "physical-validation-clusters.jsonl", physical_rows)
    _atomic_parquet(output / "physical-validation-clusters.parquet", physical_rows)
    _atomic_json(output / "physical-validation-metrics.json", physical_metrics)
    protocol_metrics = physical_metrics["by_protocol"]
    if not isinstance(protocol_metrics, Mapping):
        raise R2FinalProbeError("G3 分协议汇总指标结构非法")
    logger.log(
        {
            "physical/equal_protocol_state_mse": float(
                physical_metrics["equal_protocol_state_mse"]
            ),
            "physical/equal_protocol_residual_mse": float(
                physical_metrics["equal_protocol_physics_residual_mse"]
            ),
            "physical/tcp_state_mse": float(protocol_metrics["TCP"]["state_mse"]),
            "physical/tcp_residual_mse": float(protocol_metrics["TCP"]["physics_residual_mse"]),
            "physical/udp_state_mse": float(protocol_metrics["UDP"]["state_mse"]),
            "physical/udp_residual_mse": float(protocol_metrics["UDP"]["physics_residual_mse"]),
        },
        0,
        "physical_validation",
    )
    started = time.perf_counter()

    def save(next_epoch: int, next_batch: int) -> None:
        temporary = checkpoint.with_suffix(".pt.tmp")
        torch.save(
            {
                "binding": binding,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "scaler": scaler.state_dict(),
                "next_epoch": next_epoch,
                "next_batch": next_batch,
                "step": step,
                "best_macro_f1": best_macro_f1,
            },
            temporary,
        )
        os.replace(temporary, checkpoint)

    try:
        optimizer.zero_grad(set_to_none=True)
        for epoch in range(start_epoch, config.training.num_train_epochs):
            loader = _loader(
                views.train,
                config,
                tokenizer,
                torch,
                shuffle=True,
                seed=config.seed + epoch,
            )
            model.train()
            group_loss = 0.0
            group_batches = 0
            for batch_index, batch in enumerate(loader):
                if epoch == start_epoch and batch_index < start_batch:
                    continue
                batch = {name: value.to(runtime.device) for name, value in batch.items()}
                with baseline._autocast(torch, runtime):
                    model_output = model(**batch)
                loss = model_output.loss
                if loss is None or not bool(torch.isfinite(loss).item()):
                    raise R2FinalProbeError("分类训练损失不是有限数")
                group_start = (
                    batch_index // config.training.gradient_accumulation_steps
                ) * config.training.gradient_accumulation_steps
                group_size = min(
                    config.training.gradient_accumulation_steps,
                    batches_per_epoch - group_start,
                )
                scaled = loss / group_size
                if runtime.use_grad_scaler:
                    scaler.scale(scaled).backward()
                else:
                    scaled.backward()
                group_loss += float(loss.detach().float().item())
                group_batches += 1
                group_end = (
                    (batch_index + 1) % config.training.gradient_accumulation_steps == 0
                    or batch_index + 1 == batches_per_epoch
                )
                if not group_end:
                    continue
                if runtime.use_grad_scaler:
                    scaler.unscale_(optimizer)
                gradient_norm = torch.nn.utils.clip_grad_norm_(
                    model.parameters(), config.training.max_grad_norm
                )
                if runtime.use_grad_scaler:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                step += 1
                logger.log(
                    {
                        "train/loss": group_loss / group_batches,
                        "train/learning_rate": float(optimizer.param_groups[0]["lr"]),
                        "train/gradient_norm": float(gradient_norm.detach().float().item()),
                        "train/epoch": float(epoch + 1),
                    },
                    step,
                    "optimizer_step",
                )
                group_loss = 0.0
                group_batches = 0
                if step % config.training.save_steps == 0:
                    save(epoch, batch_index + 1)
            calibration_metrics, _ = _evaluate(
                model,
                tokenizer,
                views.calibration,
                config,
                runtime,
                torch,
            )
            logger.log(
                {
                    f"calibration/{name}": float(value)
                    for name, value in calibration_metrics.items()
                    if isinstance(value, (int, float))
                },
                step,
                "calibration",
            )
            if float(calibration_metrics["macro_f1"]) > best_macro_f1:
                best_macro_f1 = float(calibration_metrics["macro_f1"])
                temporary = best.with_suffix(".pt.tmp")
                torch.save(
                    {"binding": binding, "model": model.state_dict()},
                    temporary,
                )
                os.replace(temporary, best)
            save(epoch + 1, 0)
            start_batch = 0
        if not best.is_file():
            raise R2FinalProbeError("训练结束后缺少校准集最佳模型")
        selected = torch.load(best, map_location="cpu", weights_only=False)
        if selected.get("binding") != binding:
            raise R2FinalProbeError("最佳模型绑定不一致")
        model.load_state_dict(selected["model"], strict=True)
        validation_metrics, predictions = _evaluate(
            model,
            tokenizer,
            views.validation,
            config,
            runtime,
            torch,
        )
        result = {
            "status": "finished",
            "variant": variant,
            "seed": config.seed,
            "steps": step,
            "best_calibration_macro_f1": best_macro_f1,
            "validation_metrics": validation_metrics,
            "physical_validation_metrics": physical_metrics,
            "elapsed_seconds": time.perf_counter() - started,
            "quic_expert_ready": config.physics.quic_expert_ready,
            "final_test_visible": False,
        }
        _atomic_json(output / "result.json", result)
        _atomic_jsonl(output / "validation-predictions.jsonl", predictions)
        return result
    finally:
        logger.finish()


def execute(config: ProbeConfig, variant: str) -> Mapping[str, object]:
    if os.environ.get("R2_G3_REQUIRED") != "1":
        raise R2FinalProbeError("正式五组运行必须经 G3 制品包装器启动")
    if os.environ.get("R2_ZERO_COLLAPSE_REQUIRED") != "1":
        raise R2FinalProbeError("正式五组运行必须经固定残差零坍缩包装器启动")
    if variant not in VARIANTS:
        raise R2FinalProbeError(f"variant 必须属于 {VARIANTS}")
    if variant != config.variant:
        raise R2FinalProbeError(f"命令组别 {variant} 与配置冻结组别 {config.variant} 不一致")
    if not config.data.ready:
        raise R2FinalDataNotReady(config.data.not_ready_reason)
    if not config.physics.checkpoint.ready:
        raise R2FinalDataNotReady(config.physics.checkpoint.not_ready_reason)
    modules = baseline.load_runtime_modules()
    runtime = baseline.resolve_runtime(modules.torch, config.model, formal_training=True)
    (
        fit_config,
        system,
        unified_control,
        history_control,
        checkpoint_sha256,
        capacity_receipt,
        checkpoint_binding_sha256,
    ) = _physics_system(config, modules.torch)
    mapped_history = tuple(
        HISTORY_TO_PHYSICS.get(field, "") for field in config.data.contract.columns.history_fields
    )
    if mapped_history != fit_config.data.observation_fields:
        raise R2FinalProbeError("检测公共历史与物理专家输入语义或顺序不一致")
    if config.data.contract.history_scales != fit_config.data.observation_scales:
        raise R2FinalProbeError("检测公共历史与物理预训练尺度不一致")
    if config.physics.physical_evaluation_cluster_id != fit_config.data.evaluation_cluster_id:
        raise R2FinalProbeError("G3 评价簇字段与物理预训练配置不一致")
    base = load_base_views(config.data.contract)
    device = modules.torch.device(runtime.device)
    unified, physics = _produce_bound_sequences(
        system=system,
        unified_control=unified_control,
        base=base,
        checkpoint_sha256=checkpoint_sha256,
        capacity_receipt=capacity_receipt,
        checkpoint_binding_sha256=checkpoint_binding_sha256,
        quic_expert_ready=config.physics.quic_expert_ready,
        batch_size=config.physics.production_batch_size,
        torch=modules.torch,
        device=device,
    )
    views = build_variant_views(
        base,
        variant=variant,
        seed=config.seed,
        unified_sequences=unified,
        physics_sequences=physics,
        representation_dimension=fit_config.model.representation_dimension,
        quic_expert_ready=config.physics.quic_expert_ready,
    )
    physical_rows, physical_metrics = _physical_validation_artifacts(
        variant=variant,
        fit_config=fit_config,
        system=system,
        unified_control=unified_control,
        history_control=history_control,
        checkpoint_sha256=checkpoint_sha256,
        checkpoint_binding_sha256=checkpoint_binding_sha256,
        seed=config.seed,
        batch_size=config.physics.production_batch_size,
        torch=modules.torch,
        device=device,
    )
    return _train(
        config,
        variant,
        views,
        modules,
        runtime,
        checkpoint_sha256,
        physical_rows,
        physical_metrics,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行最终 R2 单组 DistilBERT 探针")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--trusted-root", type=Path, required=True)
    parser.add_argument("--variant", choices=VARIANTS, required=True)
    parser.add_argument("--validate-config-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config, trusted_root=args.trusted_root)
        if args.validate_config_only:
            print(
                json.dumps(
                    {
                        "status": "config-valid",
                        "seed": config.seed,
                        "variant": args.variant,
                        "data_ready": config.data.ready,
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        result = execute(config, args.variant)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except R2FinalDataNotReady as error:
        print(
            json.dumps(
                {"status": "data-not-ready", "reason": str(error)},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
