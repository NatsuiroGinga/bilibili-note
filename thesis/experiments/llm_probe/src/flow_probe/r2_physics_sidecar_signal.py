"""R2 物理旁路增量信号的开发集四组对照实验。"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import yaml
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
)
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from flow_probe import tabular_baselines
from flow_probe.r2_protocol_contract import COMMON_FIELDS
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

CONFIG_SCHEMA_VERSION = "flow_probe_r2_physics_sidecar_signal_config_v1"
RESULT_SCHEMA_VERSION = "flow_probe_r2_physics_sidecar_signal_result_v1"
READINESS_SCHEMA_VERSION = "flow_probe_r2_physics_sidecar_readiness_v1"
DATASET_VERSION = "flow_probe_r2_protocol_dataset_v0"
ALLOWED_SEEDS = (42, 43, 44)
VARIANTS = ("A", "A+P", "A+P_shuffle", "A+P_random")
TRAIN_SPLIT = "train-fit"
EVALUATION_SPLIT = "validation"
ALLOWED_PHYSICS_FIT_SPLITS = ("train-fit", "calibration")
FORBIDDEN_PATH_TOKENS = (
    "test",
    "unseen-configuration",
    "open-protocol",
    "final-test",
    "final_test",
)
COMMON_FEATURE_FIELDS = tuple(
    item for field in COMMON_FIELDS for item in (field, f"{field}_missing")
)
SIDECAR_FIELDS = (
    "estimated_queue_q0",
    "estimated_queue_q1",
    "estimated_queue_q2",
    "estimated_queue_q3",
    "estimated_queue_q4",
    "normalized_queue_residual_w0",
    "normalized_queue_residual_w1",
    "normalized_queue_residual_w2",
    "normalized_queue_residual_w3",
    "state_uncertainty_q0",
    "state_uncertainty_q1",
    "state_uncertainty_q2",
    "state_uncertainty_q3",
    "state_uncertainty_q4",
    "shared_expert_mask",
    "tcp_expert_mask",
    "udp_expert_mask",
    "protocol_confidence",
)


class R2PhysicsSidecarSignalError(ValueError):
    """旁路实验配置、输入或输出违反冻结合同。"""


@dataclass(frozen=True)
class ArtifactSpec:
    """一个项目相对输入及其预注册摘要。"""

    path: str
    sha256: str


@dataclass(frozen=True)
class R2PhysicsSidecarSignalConfig:
    """单个随机种子的冻结旁路实验配置。"""

    status: str
    seed: int
    dataset_version: str
    dataset_stage: str
    dataset_status: str
    bootstrap_repetitions: int
    calibration_bins: int
    common_fields: tuple[str, ...]
    sidecar_fields: tuple[str, ...]
    freeze_manifest: ArtifactSpec
    master_records: ArtifactSpec
    common_features: ArtifactSpec
    protocol_observations: ArtifactSpec
    sidecar: ArtifactSpec
    readiness_receipt: ArtifactSpec
    train_manifest: ArtifactSpec
    evaluation_manifests: Mapping[str, ArtifactSpec]


@dataclass(frozen=True)
class DevelopmentSplit:
    """保持冻结样本顺序的一份开发数据。"""

    name: str
    sample_ids: tuple[str, ...]
    labels: tuple[str, ...]
    source_datasets: tuple[str, ...]
    transport_families: tuple[str, ...]
    common_features: np.ndarray
    sidecar_features: np.ndarray


@dataclass(frozen=True)
class DevelopmentData:
    """训练与全部开发验证分区。"""

    train: DevelopmentSplit
    evaluations: Mapping[str, DevelopmentSplit]
    input_contract: Mapping[str, object]
    physics_diagnostics: Mapping[str, object]


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise R2PhysicsSidecarSignalError(f"{description} 必须是映射")
    return value


def _string(mapping: Mapping[str, object], key: str, description: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise R2PhysicsSidecarSignalError(f"{description}.{key} 必须是非空字符串")
    return value.strip()


def _integer(mapping: Mapping[str, object], key: str, description: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise R2PhysicsSidecarSignalError(f"{description}.{key} 必须是整数")
    return value


def _string_tuple(value: object, description: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise R2PhysicsSidecarSignalError(f"{description} 必须是非空列表")
    values = tuple(str(item).strip() for item in value)
    if any(not item for item in values) or len(set(values)) != len(values):
        raise R2PhysicsSidecarSignalError(f"{description} 含空值或重复值")
    return values


def _project_relative_path(value: object, description: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise R2PhysicsSidecarSignalError(f"{description}.path 必须是非空字符串")
    path = Path(value.strip())
    if path.is_absolute() or ".." in path.parts:
        raise R2PhysicsSidecarSignalError(f"{description}.path 必须是项目内相对路径")
    normalized = path.as_posix()
    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts.intersection(FORBIDDEN_PATH_TOKENS):
        raise R2PhysicsSidecarSignalError(f"{description}.path 指向禁止读取的最终或外部分区")
    return normalized


def _artifact(value: object, description: str) -> ArtifactSpec:
    mapping = _mapping(value, description)
    path = _project_relative_path(mapping.get("path"), description)
    sha256 = _string(mapping, "sha256", description)
    if sha256 != "PENDING" and (
        len(sha256) != 64 or any(char not in "0123456789abcdef" for char in sha256)
    ):
        raise R2PhysicsSidecarSignalError(f"{description}.sha256 必须是小写 SHA-256 或 PENDING")
    return ArtifactSpec(path=path, sha256=sha256)


def load_config(path: Path) -> R2PhysicsSidecarSignalConfig:
    """读取配置，但仅在正式入口检查前置门禁是否已解除。"""
    config_path = Path(path)
    loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    root = _mapping(loaded, "配置")
    if _string(root, "schema_version", "配置") != CONFIG_SCHEMA_VERSION:
        raise R2PhysicsSidecarSignalError("旁路配置模式版本不一致")
    experiment = _mapping(root.get("experiment"), "experiment")
    dataset = _mapping(root.get("dataset"), "dataset")
    inputs = _mapping(root.get("inputs"), "inputs")
    splits = _mapping(root.get("splits"), "splits")
    fields = _mapping(root.get("fields"), "fields")
    seed = _integer(experiment, "seed", "experiment")
    if seed not in ALLOWED_SEEDS:
        raise R2PhysicsSidecarSignalError(f"随机种子必须属于 {ALLOWED_SEEDS}")
    variants = _string_tuple(experiment.get("variants"), "experiment.variants")
    if variants != VARIANTS:
        raise R2PhysicsSidecarSignalError(f"四组对照顺序必须精确为 {VARIANTS}")
    bootstrap_repetitions = _integer(experiment, "bootstrap_repetitions", "experiment")
    if bootstrap_repetitions < 2000:
        raise R2PhysicsSidecarSignalError("配对自助法重复次数不得少于 2000")
    calibration_bins = _integer(experiment, "calibration_bins", "experiment")
    if calibration_bins < 5:
        raise R2PhysicsSidecarSignalError("校准分箱数不得少于 5")
    common_fields = _string_tuple(fields.get("common"), "fields.common")
    sidecar_fields = _string_tuple(fields.get("sidecar"), "fields.sidecar")
    if common_fields != COMMON_FEATURE_FIELDS:
        raise R2PhysicsSidecarSignalError("共同字段顺序与 R2 合同不一致")
    if sidecar_fields != SIDECAR_FIELDS:
        raise R2PhysicsSidecarSignalError("物理旁路字段顺序与冻结合同不一致")
    train_manifest = _artifact(splits.get("train"), "splits.train")
    evaluations_raw = _mapping(splits.get("evaluations"), "splits.evaluations")
    evaluations = {
        str(name): _artifact(value, f"splits.evaluations.{name}")
        for name, value in sorted(evaluations_raw.items())
    }
    if not evaluations or any(not name.strip() for name in evaluations):
        raise R2PhysicsSidecarSignalError("至少需要一个具名开发验证分区")
    return R2PhysicsSidecarSignalConfig(
        status=_string(root, "status", "配置"),
        seed=seed,
        dataset_version=_string(dataset, "version", "dataset"),
        dataset_stage=_string(dataset, "stage", "dataset"),
        dataset_status=_string(dataset, "status", "dataset"),
        bootstrap_repetitions=bootstrap_repetitions,
        calibration_bins=calibration_bins,
        common_fields=common_fields,
        sidecar_fields=sidecar_fields,
        freeze_manifest=_artifact(inputs.get("freeze_manifest"), "inputs.freeze_manifest"),
        master_records=_artifact(inputs.get("master_records"), "inputs.master_records"),
        common_features=_artifact(inputs.get("common_features"), "inputs.common_features"),
        protocol_observations=_artifact(
            inputs.get("protocol_observations"), "inputs.protocol_observations"
        ),
        sidecar=_artifact(inputs.get("sidecar"), "inputs.sidecar"),
        readiness_receipt=_artifact(
            inputs.get("readiness_receipt"), "inputs.readiness_receipt"
        ),
        train_manifest=train_manifest,
        evaluation_manifests=evaluations,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _array_sha256(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(json.dumps(array.shape, separators=(",", ":")).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _resolve_artifact(project_root: Path, spec: ArtifactSpec, description: str) -> Path:
    if spec.sha256 == "PENDING":
        raise R2PhysicsSidecarSignalError(f"{description} 尚未冻结 SHA-256")
    root = Path(project_root).resolve()
    candidate = root / spec.path
    if candidate.is_symlink() or not candidate.is_file():
        raise R2PhysicsSidecarSignalError(f"{description} 必须是现有普通文件：{spec.path}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise R2PhysicsSidecarSignalError(f"{description} 越过项目根：{spec.path}") from error
    actual = _sha256(resolved)
    if actual != spec.sha256:
        raise R2PhysicsSidecarSignalError(
            f"{description} SHA-256 不一致：{actual} != {spec.sha256}"
        )
    return resolved


def _read_json(path: Path, description: str) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return dict(_mapping(value, description))


def _read_split_manifest(path: Path, expected_split: str) -> tuple[str, ...]:
    sample_ids: list[str] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                raise R2PhysicsSidecarSignalError(f"{path} 第 {line_number} 行为空")
            row = _mapping(json.loads(line), f"{path} 第 {line_number} 行")
            sample_id = _string(row, "sample_id", f"{path} 第 {line_number} 行")
            split_id = _string(row, "split_id", f"{path} 第 {line_number} 行")
            if split_id != expected_split:
                raise R2PhysicsSidecarSignalError(
                    f"{path} 只允许 split_id={expected_split}，实际为 {split_id}"
                )
            sample_ids.append(sample_id)
    if not sample_ids or len(set(sample_ids)) != len(sample_ids):
        raise R2PhysicsSidecarSignalError(f"{path} 为空或包含重复 sample_id")
    return tuple(sample_ids)


def _indexed_frame(path: Path, required: Sequence[str], description: str) -> pd.DataFrame:
    frame = pd.read_parquet(path, columns=list(required))
    if tuple(frame.columns) != tuple(required):
        raise R2PhysicsSidecarSignalError(f"{description} 列顺序不符合合同")
    identifiers = frame["sample_id"].astype(str)
    if identifiers.empty or identifiers.duplicated().any() or (identifiers.str.len() == 0).any():
        raise R2PhysicsSidecarSignalError(f"{description} 的 sample_id 为空或重复")
    frame = frame.copy()
    frame["sample_id"] = identifiers
    return frame.set_index("sample_id", drop=False)


def _ordered_rows(frame: pd.DataFrame, sample_ids: Sequence[str], description: str) -> pd.DataFrame:
    missing = [sample_id for sample_id in sample_ids if sample_id not in frame.index]
    if missing:
        raise R2PhysicsSidecarSignalError(f"{description} 缺少样本：{missing[0]}")
    ordered = frame.loc[list(sample_ids)]
    if tuple(ordered.index.astype(str)) != tuple(sample_ids):
        raise R2PhysicsSidecarSignalError(f"{description} 无法保持冻结样本顺序")
    return ordered


def _finite_sidecar(values: np.ndarray, description: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != len(SIDECAR_FIELDS):
        raise R2PhysicsSidecarSignalError(f"{description} 旁路矩阵形状不正确")
    if not np.isfinite(array).all():
        raise R2PhysicsSidecarSignalError(f"{description} 旁路包含非有限值")
    array.setflags(write=False)
    return array


def _common_matrix(frame: pd.DataFrame, description: str) -> np.ndarray:
    values = frame.loc[:, COMMON_FEATURE_FIELDS].to_numpy(dtype=np.float64, copy=True)
    for field in COMMON_FIELDS:
        missing = values[:, COMMON_FEATURE_FIELDS.index(f"{field}_missing")]
        if not np.isin(missing, (0.0, 1.0)).all():
            raise R2PhysicsSidecarSignalError(f"{description} 的 {field}_missing 不是二值")
    values.setflags(write=False)
    return values


def _build_split(
    *,
    name: str,
    sample_ids: tuple[str, ...],
    master: pd.DataFrame,
    common: pd.DataFrame,
    protocol: pd.DataFrame,
    sidecar: pd.DataFrame,
) -> DevelopmentSplit:
    master_rows = _ordered_rows(master, sample_ids, f"{name} 主记录")
    common_rows = _ordered_rows(common, sample_ids, f"{name} 共同字段")
    protocol_rows = _ordered_rows(protocol, sample_ids, f"{name} 协议字段")
    sidecar_rows = _ordered_rows(sidecar, sample_ids, f"{name} 物理旁路")
    if set(master_rows["split_id"].astype(str)) != {name if name == TRAIN_SPLIT else EVALUATION_SPLIT}:
        raise R2PhysicsSidecarSignalError(f"{name} 主记录的 split_id 与清单不一致")
    if set(sidecar_rows["split_id"].astype(str)) != {
        name if name == TRAIN_SPLIT else EVALUATION_SPLIT
    }:
        raise R2PhysicsSidecarSignalError(f"{name} 旁路的 split_id 与清单不一致")
    labels = tuple(master_rows["binary_label"].astype(str))
    if set(labels) != {"benign", "malicious"}:
        raise R2PhysicsSidecarSignalError(f"{name} 必须同时且只含 benign 与 malicious")
    sources = tuple(master_rows["source_dataset"].astype(str))
    transports = tuple(protocol_rows["transport_family"].astype(str))
    if any(not value for value in sources) or any(not value for value in transports):
        raise R2PhysicsSidecarSignalError(f"{name} 的数据源或传输族为空")
    return DevelopmentSplit(
        name=name,
        sample_ids=sample_ids,
        labels=labels,
        source_datasets=sources,
        transport_families=transports,
        common_features=_common_matrix(common_rows, name),
        sidecar_features=_finite_sidecar(sidecar_rows.loc[:, SIDECAR_FIELDS].to_numpy(), name),
    )


def prepare_development_data(
    config: R2PhysicsSidecarSignalConfig, project_root: Path
) -> DevelopmentData:
    """只读取 train-fit 与 validation，并验证物理拟合未接触禁止分区。"""
    if config.status != "ready":
        raise R2PhysicsSidecarSignalError(
            f"配置状态为 {config.status}，前置门禁未通过，禁止启动实验"
        )
    if (
        config.dataset_version != DATASET_VERSION
        or config.dataset_stage != "theory_selection"
        or config.dataset_status != "review_pending"
    ):
        raise R2PhysicsSidecarSignalError("R2 数据版本、阶段或状态与旁路合同不一致")
    specs: dict[str, ArtifactSpec] = {
        "freeze_manifest": config.freeze_manifest,
        "master_records": config.master_records,
        "common_features": config.common_features,
        "protocol_observations": config.protocol_observations,
        "sidecar": config.sidecar,
        "readiness_receipt": config.readiness_receipt,
        "train_manifest": config.train_manifest,
        **{
            f"evaluation_manifest:{name}": spec
            for name, spec in config.evaluation_manifests.items()
        },
    }
    paths = {
        name: _resolve_artifact(project_root, spec, name) for name, spec in specs.items()
    }
    freeze = _read_json(paths["freeze_manifest"], "R2 freeze-manifest")
    if freeze.get("dataset_version", freeze.get("version")) != DATASET_VERSION:
        raise R2PhysicsSidecarSignalError("freeze-manifest 的数据版本不一致")
    if freeze.get("stage") != "theory_selection" or freeze.get("status") != "review_pending":
        raise R2PhysicsSidecarSignalError("freeze-manifest 不是 review_pending 理论筛选数据")
    readiness = _read_json(paths["readiness_receipt"], "物理旁路就绪回执")
    if readiness.get("schema_version") != READINESS_SCHEMA_VERSION:
        raise R2PhysicsSidecarSignalError("物理旁路就绪回执模式版本不一致")
    if readiness.get("status") != "passed":
        raise R2PhysicsSidecarSignalError("物理旁路就绪回执未通过")
    if tuple(readiness.get("physics_fit_splits", ())) != ALLOWED_PHYSICS_FIT_SPLITS:
        raise R2PhysicsSidecarSignalError("状态估计器必须且只能使用 train-fit 与 calibration")
    if readiness.get("forbidden_splits_read") is not False:
        raise R2PhysicsSidecarSignalError("就绪回执未证明最终和外部分区保持未读")
    if tuple(readiness.get("sidecar_fields", ())) != SIDECAR_FIELDS:
        raise R2PhysicsSidecarSignalError("就绪回执的旁路字段顺序不一致")
    if readiness.get("sidecar_sha256") != config.sidecar.sha256:
        raise R2PhysicsSidecarSignalError("就绪回执未绑定当前旁路制品")
    diagnostics = _mapping(readiness.get("calibration_metrics"), "calibration_metrics")
    for key in ("state_mse", "state_mse_unobserved", "physics_residual_mse"):
        value = diagnostics.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not np.isfinite(value):
            raise R2PhysicsSidecarSignalError(f"校准物理指标 {key} 缺失或非有限")

    train_ids = _read_split_manifest(paths["train_manifest"], TRAIN_SPLIT)
    evaluation_ids = {
        name: _read_split_manifest(paths[f"evaluation_manifest:{name}"], EVALUATION_SPLIT)
        for name in config.evaluation_manifests
    }
    train_set = set(train_ids)
    for name, sample_ids in evaluation_ids.items():
        overlap = train_set.intersection(sample_ids)
        if overlap:
            raise R2PhysicsSidecarSignalError(f"训练与 {name} 验证样本重叠：{next(iter(overlap))}")
    allowed_ids = train_set.union(*(set(sample_ids) for sample_ids in evaluation_ids.values()))

    master = _indexed_frame(
        paths["master_records"],
        ("sample_id", "source_dataset", "binary_label", "split_id"),
        "主记录",
    )
    common = _indexed_frame(
        paths["common_features"], ("sample_id", *COMMON_FEATURE_FIELDS), "共同字段"
    )
    protocol = _indexed_frame(
        paths["protocol_observations"], ("sample_id", "transport_family"), "协议字段"
    )
    sidecar_required = ("sample_id", "split_id", *SIDECAR_FIELDS)
    sidecar = _indexed_frame(paths["sidecar"], sidecar_required, "物理旁路")
    if set(sidecar.index) != allowed_ids:
        extra = sorted(set(sidecar.index).difference(allowed_ids))
        missing = sorted(allowed_ids.difference(sidecar.index))
        detail = extra[0] if extra else missing[0]
        raise R2PhysicsSidecarSignalError(
            f"物理旁路必须精确覆盖开发清单，不得包含最终分区：{detail}"
        )

    train = _build_split(
        name=TRAIN_SPLIT,
        sample_ids=train_ids,
        master=master,
        common=common,
        protocol=protocol,
        sidecar=sidecar,
    )
    evaluations = {
        name: _build_split(
            name=name,
            sample_ids=sample_ids,
            master=master,
            common=common,
            protocol=protocol,
            sidecar=sidecar,
        )
        for name, sample_ids in evaluation_ids.items()
    }
    input_contract = {
        "schema_version": "flow_probe_r2_physics_sidecar_input_v1",
        "dataset_version": config.dataset_version,
        "dataset_stage": config.dataset_stage,
        "dataset_status": config.dataset_status,
        "allowed_classification_splits": [TRAIN_SPLIT, EVALUATION_SPLIT],
        "allowed_physics_fit_splits": list(ALLOWED_PHYSICS_FIT_SPLITS),
        "forbidden_splits_read": False,
        "common_fields": list(COMMON_FEATURE_FIELDS),
        "sidecar_fields": list(SIDECAR_FIELDS),
        "artifacts": {
            name: {"path": specs[name].path, "sha256": specs[name].sha256}
            for name in sorted(specs)
        },
        "sample_counts": {
            "train-fit": len(train.sample_ids),
            **{name: len(split.sample_ids) for name, split in evaluations.items()},
        },
        "sample_order_sha256": {
            "train-fit": _canonical_sha256(list(train.sample_ids)),
            **{
                name: _canonical_sha256(list(split.sample_ids))
                for name, split in evaluations.items()
            },
        },
    }
    return DevelopmentData(
        train=train,
        evaluations=evaluations,
        input_contract=input_contract,
        physics_diagnostics=dict(diagnostics),
    )


def _strata(split: DevelopmentSplit) -> tuple[tuple[str, str], ...]:
    return tuple(zip(split.source_datasets, split.transport_families, strict=True))


def _deranged_permutation(indices: np.ndarray, generator: np.random.Generator) -> np.ndarray:
    if len(indices) <= 1:
        return indices.copy()
    permuted = generator.permutation(indices)
    if np.array_equal(permuted, indices):
        permuted = np.roll(permuted, 1)
    return permuted


def shuffled_sidecar(split: DevelopmentSplit, seed: int) -> np.ndarray:
    """在同一数据源、传输族和划分内置换完整旁路，不使用标签。"""
    generator = np.random.default_rng(seed)
    result = np.empty_like(split.sidecar_features)
    strata = _strata(split)
    for key in sorted(set(strata)):
        indices = np.asarray([index for index, value in enumerate(strata) if value == key])
        result[indices] = split.sidecar_features[_deranged_permutation(indices, generator)]
    result.setflags(write=False)
    return result


def random_sidecar(
    target: DevelopmentSplit, train: DevelopmentSplit, seed: int
) -> np.ndarray:
    """逐维从同源同协议训练池独立抽样，保持训练边际但破坏联合结构。"""
    generator = np.random.default_rng(seed)
    train_strata = _strata(train)
    target_strata = _strata(target)
    pools = {
        key: np.asarray([index for index, value in enumerate(train_strata) if value == key])
        for key in sorted(set(train_strata))
    }
    result = np.empty_like(target.sidecar_features)
    target_is_train = target.sample_ids == train.sample_ids
    if target_is_train:
        for key, pool in pools.items():
            for column_index in range(target.sidecar_features.shape[1]):
                result[pool, column_index] = train.sidecar_features[
                    _deranged_permutation(pool, generator), column_index
                ]
        result.setflags(write=False)
        return result
    for row_index, key in enumerate(target_strata):
        pool = pools.get(key)
        if pool is None or not len(pool):
            raise R2PhysicsSidecarSignalError(
                f"训练集缺少随机旁路所需的数据源/传输族层：{key}"
            )
        for column_index in range(target.sidecar_features.shape[1]):
            source_index = int(pool[generator.integers(0, len(pool))])
            result[row_index, column_index] = train.sidecar_features[
                source_index, column_index
            ]
    result.setflags(write=False)
    return result


def build_variant_features(
    data: DevelopmentData, variant: str, seed: int
) -> tuple[np.ndarray, Mapping[str, np.ndarray]]:
    """为四组对照生成训练和验证矩阵。"""
    if variant not in VARIANTS:
        raise R2PhysicsSidecarSignalError(f"未知旁路变体：{variant}")
    if variant == "A":
        return data.train.common_features, {
            name: split.common_features for name, split in data.evaluations.items()
        }
    if variant == "A+P":
        train_sidecar = data.train.sidecar_features
        evaluation_sidecars = {
            name: split.sidecar_features for name, split in data.evaluations.items()
        }
    elif variant == "A+P_shuffle":
        train_sidecar = shuffled_sidecar(data.train, seed)
        evaluation_sidecars = {
            name: shuffled_sidecar(split, seed + 10_000 + index)
            for index, (name, split) in enumerate(data.evaluations.items())
        }
    else:
        train_sidecar = random_sidecar(data.train, data.train, seed)
        evaluation_sidecars = {
            name: random_sidecar(split, data.train, seed + 20_000 + index)
            for index, (name, split) in enumerate(data.evaluations.items())
        }
    train_features = np.concatenate((data.train.common_features, train_sidecar), axis=1)
    evaluation_features = {
        name: np.concatenate((split.common_features, evaluation_sidecars[name]), axis=1)
        for name, split in data.evaluations.items()
    }
    train_features.setflags(write=False)
    for values in evaluation_features.values():
        values.setflags(write=False)
    return train_features, evaluation_features


def _expected_calibration_error(
    truth: np.ndarray, predictions: np.ndarray, confidence: np.ndarray, bins: int
) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    correct = (truth == predictions).astype(np.float64)
    result = 0.0
    for index in range(bins):
        lower, upper = edges[index], edges[index + 1]
        mask = (confidence >= lower) & (confidence <= upper) if index == 0 else (
            (confidence > lower) & (confidence <= upper)
        )
        if mask.any():
            result += float(mask.mean()) * abs(float(correct[mask].mean() - confidence[mask].mean()))
    return result


def _classification_metrics(
    truth: Sequence[str],
    predictions: Sequence[str],
    probabilities: np.ndarray,
    known_labels: Sequence[str],
    calibration_bins: int,
) -> dict[str, object]:
    truth_array = np.asarray(truth)
    prediction_array = np.asarray(predictions)
    label_to_index = {label: index for index, label in enumerate(known_labels)}
    encoded_truth = np.asarray([label_to_index[label] for label in truth], dtype=np.int64)
    one_hot = np.eye(len(known_labels), dtype=np.float64)[encoded_truth]
    confidence = probabilities.max(axis=1)
    benign = truth_array == "benign"
    return {
        "sample_count": len(truth),
        "accuracy": float(accuracy_score(truth_array, prediction_array)),
        "balanced_accuracy": float(balanced_accuracy_score(truth_array, prediction_array)),
        "macro_f1": float(f1_score(truth_array, prediction_array, average="macro", zero_division=0)),
        "benign_false_positive_rate": float(
            np.mean(prediction_array[benign] != "benign")
        ),
        "brier_score": float(np.mean(np.sum(np.square(probabilities - one_hot), axis=1))),
        "expected_calibration_error": _expected_calibration_error(
            truth_array, prediction_array, confidence, calibration_bins
        ),
    }


def paired_bootstrap_macro_f1(
    truth: Sequence[str],
    reference: Sequence[str],
    candidate: Sequence[str],
    *,
    repetitions: int,
    seed: int,
) -> dict[str, float | int]:
    """在相同样本上重采样，估计候选相对参考的宏平均 F1 差值。"""
    truth_array = np.asarray(truth)
    reference_array = np.asarray(reference)
    candidate_array = np.asarray(candidate)
    if not (
        truth_array.ndim == reference_array.ndim == candidate_array.ndim == 1
        and len(truth_array) == len(reference_array) == len(candidate_array)
        and len(truth_array) > 1
    ):
        raise R2PhysicsSidecarSignalError("配对自助法要求同长度非空一维预测")
    generator = np.random.default_rng(seed)
    deltas = np.empty(repetitions, dtype=np.float64)
    for index in range(repetitions):
        selected = generator.integers(0, len(truth_array), size=len(truth_array))
        deltas[index] = f1_score(
            truth_array[selected], candidate_array[selected], average="macro", zero_division=0
        ) - f1_score(
            truth_array[selected], reference_array[selected], average="macro", zero_division=0
        )
    lower, upper = np.quantile(deltas, (0.025, 0.975))
    observed = f1_score(truth_array, candidate_array, average="macro", zero_division=0) - f1_score(
        truth_array, reference_array, average="macro", zero_division=0
    )
    return {
        "repetitions": repetitions,
        "observed_delta": float(observed),
        "mean_delta": float(deltas.mean()),
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
        "positive_fraction": float(np.mean(deltas > 0.0)),
    }


def _run_seed(
    config: R2PhysicsSidecarSignalConfig,
    data: DevelopmentData,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    known_labels = tuple(sorted(set(data.train.labels)))
    label_to_index = {label: index for index, label in enumerate(known_labels)}
    encoded_train = np.asarray([label_to_index[label] for label in data.train.labels])
    weights = np.asarray(
        compute_sample_weight(class_weight="balanced", y=encoded_train), dtype=np.float64
    )
    results: dict[str, object] = {}
    prediction_rows: list[dict[str, object]] = []
    predictions_by_variant: dict[str, dict[str, tuple[str, ...]]] = {}
    for variant in VARIANTS:
        train_features, evaluation_features = build_variant_features(data, variant, config.seed)
        model = tabular_baselines._build_model(
            "hgb", seed=config.seed, class_count=len(known_labels)
        )
        started = time.perf_counter()
        with threadpool_limits(limits=1):
            model.fit(train_features, encoded_train, sample_weight=weights)
        fit_seconds = time.perf_counter() - started
        variant_evaluations: dict[str, object] = {}
        variant_predictions: dict[str, tuple[str, ...]] = {}
        for name, split in data.evaluations.items():
            features = evaluation_features[name]
            with threadpool_limits(limits=1):
                encoded = np.asarray(model.predict(features), dtype=np.int64)
                probabilities = tabular_baselines._normalise_probability_rows(
                    model.predict_proba(features),
                    sample_count=len(split.sample_ids),
                    class_count=len(known_labels),
                )
            predictions = tuple(known_labels[int(index)] for index in encoded)
            metrics = _classification_metrics(
                split.labels,
                predictions,
                probabilities,
                known_labels,
                config.calibration_bins,
            )
            variant_evaluations[name] = {"metrics": metrics}
            variant_predictions[name] = predictions
            for sample_id, truth, prediction, probability in zip(
                split.sample_ids,
                split.labels,
                predictions,
                probabilities,
                strict=True,
            ):
                prediction_rows.append(
                    {
                        "seed": config.seed,
                        "variant": variant,
                        "evaluation": name,
                        "sample_id": sample_id,
                        "truth": truth,
                        "prediction": prediction,
                        "probabilities": {
                            label: float(value)
                            for label, value in zip(known_labels, probability, strict=True)
                        },
                    }
                )
        results[variant] = {
            "hgb_parameters": dict(model.get_params(deep=True)),
            "fit_seconds": fit_seconds,
            "train_sample_count": len(data.train.sample_ids),
            "feature_count": int(train_features.shape[1]),
            "train_feature_matrix_sha256": _array_sha256(train_features),
            "evaluation_feature_matrix_sha256": {
                name: _array_sha256(values) for name, values in evaluation_features.items()
            },
            "evaluations": variant_evaluations,
        }
        predictions_by_variant[variant] = variant_predictions
    comparisons: dict[str, object] = {}
    for name, split in data.evaluations.items():
        reference = predictions_by_variant["A"][name]
        comparisons[name] = {
            "against_A": {
                variant: paired_bootstrap_macro_f1(
                    split.labels,
                    reference,
                    predictions_by_variant[variant][name],
                    repetitions=config.bootstrap_repetitions,
                    seed=config.seed * 1000 + index,
                )
                for index, variant in enumerate(VARIANTS[1:], start=1)
            },
            "A+P_vs_controls": {
                control: paired_bootstrap_macro_f1(
                    split.labels,
                    predictions_by_variant[control][name],
                    predictions_by_variant["A+P"][name],
                    repetitions=config.bootstrap_repetitions,
                    seed=config.seed * 1000 + 100 + index,
                )
                for index, control in enumerate(("A+P_shuffle", "A+P_random"), start=1)
            },
        }
    return (
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "seed": config.seed,
            "variants": results,
            "paired_macro_f1": comparisons,
            "physics_diagnostics": dict(data.physics_diagnostics),
            "control_diagnostics": {
                "shuffle_stratification": ["source_dataset", "transport_family", "split"],
                "shuffle_singleton_strata": {
                    "train-fit": sum(value == 1 for value in Counter(_strata(data.train)).values()),
                    **{
                        name: sum(value == 1 for value in Counter(_strata(split)).values())
                        for name, split in data.evaluations.items()
                    },
                },
                "random_train_marginals_preserved_exactly": True,
                "random_validation_reference": "train-fit_same_source_and_transport",
            },
        },
        prediction_rows,
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    temporary = path.with_name(f"{path.name}.partial")
    with temporary.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(path)


def _artifact_record(path: Path, root: Path) -> dict[str, object]:
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise R2PhysicsSidecarSignalError(f"启动证据必须是普通文件：{candidate}")
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(Path(root).resolve())
    except ValueError as error:
        raise R2PhysicsSidecarSignalError(f"启动证据越过运行根：{candidate}") from error
    return {
        "path": relative.as_posix(),
        "size_bytes": resolved.stat().st_size,
        "sha256": _sha256(resolved),
    }


def finalize_launcher_evidence(run_root: Path) -> dict[str, object]:
    """在包装器结束后登记稳定的日志、状态、退出码和能力清单。"""
    root = Path(run_root)
    manifest_path = root / "artifact_manifest.json"
    manifest = _read_json(manifest_path, "SwanLab 制品清单")
    if manifest.get("status") != "finished":
        raise R2PhysicsSidecarSignalError("SwanLab 运行未完成，不能收口启动证据")
    state = _read_json(root / "launcher-state.json", "启动状态")
    if state.get("state") != "finished" or state.get("exit_code") != 0:
        raise R2PhysicsSidecarSignalError("包装器状态未完成或退出码非零")
    exit_code = (root / "launcher-exit-code.txt").read_text(encoding="utf-8").strip()
    if exit_code != "0":
        raise R2PhysicsSidecarSignalError("包装器退出码文件不是 0")
    evidence_names = (
        "launcher.log",
        "launcher-state.json",
        "launcher-exit-code.txt",
        "launcher-capabilities.txt",
        "launcher-binding.txt",
    )
    launcher_evidence = {
        name: _artifact_record(root / name, root) for name in evidence_names
    }
    finalized = {
        **manifest,
        "launcher_evidence": launcher_evidence,
        "launcher_evidence_status": "finished",
    }
    _write_json(manifest_path, finalized)
    return finalized


def aggregate_three_seed_results(run_root: Path) -> dict[str, object]:
    """汇总三个预注册种子，不进行种子选择或再次读取数据集。"""
    root = Path(run_root)
    seed_results = {
        seed: _read_json(root / f"seed-{seed}" / "results.json", f"种子 {seed} 结果")
        for seed in ALLOWED_SEEDS
    }
    evaluation_names: set[str] | None = None
    for seed, result in seed_results.items():
        if result.get("seed") != seed or result.get("schema_version") != RESULT_SCHEMA_VERSION:
            raise R2PhysicsSidecarSignalError(f"种子 {seed} 结果身份不一致")
        names = set(_mapping(result.get("paired_macro_f1"), "paired_macro_f1"))
        evaluation_names = names if evaluation_names is None else evaluation_names.intersection(names)
    if not evaluation_names:
        raise R2PhysicsSidecarSignalError("三种子没有共同开发验证分区")
    evaluations: dict[str, object] = {}
    for name in sorted(evaluation_names):
        deltas: dict[int, float] = {}
        lowers: dict[int, float] = {}
        control_passes: dict[int, bool] = {}
        for seed, result in seed_results.items():
            comparison = _mapping(
                _mapping(result["paired_macro_f1"], "paired_macro_f1")[name],
                f"种子 {seed} 的 {name}",
            )
            against_a = _mapping(comparison.get("against_A"), "against_A")
            real = _mapping(against_a.get("A+P"), "against_A.A+P")
            deltas[seed] = float(real["observed_delta"])
            lowers[seed] = float(real["ci95_lower"])
            controls = _mapping(comparison.get("A+P_vs_controls"), "A+P_vs_controls")
            control_passes[seed] = all(
                float(_mapping(controls[control], control)["observed_delta"]) > 0.0
                for control in ("A+P_shuffle", "A+P_random")
            )
        evaluations[name] = {
            "A+P_minus_A_by_seed": {str(seed): value for seed, value in deltas.items()},
            "A+P_minus_A_ci95_lower_by_seed": {
                str(seed): value for seed, value in lowers.items()
            },
            "mean_delta": float(np.mean(list(deltas.values()))),
            "minimum_delta": float(min(deltas.values())),
            "all_seed_deltas_positive": all(value > 0.0 for value in deltas.values()),
            "all_seed_ci95_lowers_positive": all(value > 0.0 for value in lowers.values()),
            "A+P_beats_both_controls_by_seed": {
                str(seed): value for seed, value in control_passes.items()
            },
            "all_seeds_beat_both_controls": all(control_passes.values()),
        }
    summary = {
        "schema_version": "flow_probe_r2_physics_sidecar_three_seed_summary_v1",
        "seeds": list(ALLOWED_SEEDS),
        "seed_selection_performed": False,
        "final_test_visible": False,
        "evaluations": evaluations,
    }
    _write_json(root / "three_seed_summary.json", summary)
    return summary


def run_signal_probe(
    *, config_path: Path, project_root: Path, output_dir: Path, run_name: str
) -> dict[str, object]:
    """运行一个种子的正式开发集实验，并在线记录全部标量。"""
    config = load_config(config_path)
    output = Path(output_dir)
    allowed_existing = {
        "launcher.log",
        "launcher-state.json",
        "launcher-capabilities.txt",
        "launcher-binding.txt",
        "launcher-exit-code.txt",
    }
    if not output.is_dir() or any(path.name not in allowed_existing for path in output.iterdir()):
        raise R2PhysicsSidecarSignalError("输出目录必须由正式包装器创建且只含启动回执")
    data = prepare_development_data(config, project_root)
    config_snapshot = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "status": config.status,
        "seed": config.seed,
        "variants": list(VARIANTS),
        "bootstrap_repetitions": config.bootstrap_repetitions,
        "calibration_bins": config.calibration_bins,
        "hgb_configuration_origin": "tabular_baselines._build_model",
        "final_test_visible": False,
    }
    paths = {
        "config_snapshot": output / "config_snapshot.json",
        "input_contract": output / "input_contract.json",
        "environment": output / "environment.json",
        "results": output / "results.json",
        "predictions": output / "predictions.jsonl",
        "swanlab_metrics": output / "swanlab_metrics.json",
        "console_log": output / "console.log",
    }
    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "R2 物理旁路增量信号的冻结开发集四组对照",
            "mode": "online",
            "tags": ["r2-sidecar", "hgb", f"seed-{config.seed}", "dev-only"],
        }
    )
    with (
        capture_console_log(output / "console.log"),
        swanlab_run(
            settings=settings,
            phase="r2-physics-sidecar",
            config=config_snapshot,
            artifact_dir=output,
            data_files=paths,
        ) as swanlab,
    ):
        _write_json(paths["config_snapshot"], config_snapshot)
        _write_json(paths["input_contract"], data.input_contract)
        _write_json(
            paths["environment"],
            {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scikit_learn": sklearn.__version__,
                "runtime": tabular_baselines.detect_runtime_capabilities(),
            },
        )
        results, predictions = _run_seed(config, data)
        _write_json(paths["results"], results)
        _write_jsonl(paths["predictions"], predictions)
        metrics = flatten_scalar_metrics(results, prefix="r2-sidecar")
        swanlab.log(metrics, step=0)
        _write_json(paths["swanlab_metrics"], {"step": 0, "metrics": metrics})
        print(
            f"R2 物理旁路开发集实验完成：seed={config.seed}，"
            f"variants={','.join(VARIANTS)}"
        )
    return _read_json(output / "artifact_manifest.json", "制品清单")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行 R2 物理旁路增量信号开发集实验")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--run-name")
    parser.add_argument("--aggregate-root", type=Path)
    parser.add_argument("--finalize-run-root", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.finalize_run_root is not None:
        if any(
            value is not None
            for value in (
                args.config,
                args.project_root,
                args.output_dir,
                args.run_name,
                args.aggregate_root,
            )
        ):
            raise R2PhysicsSidecarSignalError("启动证据收口不能同时传入其他运行参数")
        finalize_launcher_evidence(args.finalize_run_root)
        return 0
    if args.aggregate_root is not None:
        if any(
            value is not None
            for value in (args.config, args.project_root, args.output_dir, args.run_name)
        ):
            raise R2PhysicsSidecarSignalError("三种子汇总不能同时传入单种子运行参数")
        aggregate_three_seed_results(args.aggregate_root)
        return 0
    if any(value is None for value in (args.config, args.project_root, args.output_dir, args.run_name)):
        raise R2PhysicsSidecarSignalError("单种子运行必须同时提供配置、项目根、输出目录和运行名")
    run_signal_probe(
        config_path=args.config,
        project_root=args.project_root,
        output_dir=args.output_dir,
        run_name=args.run_name,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
