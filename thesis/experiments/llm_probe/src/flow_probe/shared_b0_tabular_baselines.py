"""共享 B0 视图上的严格 HGB 与 XGBoost 基线入口。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import sklearn
from pandas.api.types import is_bool_dtype, is_integer_dtype, is_numeric_dtype

from flow_probe import tabular_baselines
from flow_probe.frozen_protocol import (
    FieldRole,
    FrozenProtocol,
    ModelView,
    SplitManifest,
    THEORY_SELECTION_STAGE,
    TabularSplit,
    sample_order_sha256,
)
from flow_probe.shared_b0_view import (
    ARTIFACT_SCHEMA_VERSION,
    COMMON_FIELDS,
    FEATURE_COLUMNS,
    MASK_FIELDS,
    file_sha256,
)
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    flatten_scalar_metrics,
    swanlab_run,
)

EXPECTED_STAGE = THEORY_SELECTION_STAGE
EXPECTED_STATUS = "review_pending"
SHARED_B0_SUITE_ID = "dataset-v1-shared-b0"
SHARED_B0_VIEW_NAME = "shared_b0_common_numeric_v1"
LABEL_FIELD = "label"
EXPECTED_FEATURE_FIELDS = (*COMMON_FIELDS, *MASK_FIELDS)
MODEL_RUNS_DIRECTORY = "model-runs"
LAUNCHER_EVIDENCE_FILES = MappingProxyType(
    {
        "launcher_log": "launcher.log",
        "launcher_state": "launcher-state.json",
        "launcher_exit_code": "launcher-exit-code.txt",
        "launcher_binding": "launcher-binding.txt",
        "launcher_capabilities": "launcher-capabilities.txt",
    }
)
REQUIRED_SPLITS = MappingProxyType(
    {
        "train": (
            "train",
            "candidate/common_features.parquet",
            "candidate/bert_train.parquet",
        ),
        "genis": (
            "validation",
            "validation/genis_common_features.parquet",
            "validation/genis_bert.parquet",
        ),
        "tqhc2": (
            "validation",
            "validation/tqhc2_common_features.parquet",
            "validation/tqhc2_bert.parquet",
        ),
    }
)


class SharedB0TabularError(tabular_baselines.TabularBaselineError):
    """共享 B0 树模型输入或运行合同不合法。"""


@dataclass(frozen=True)
class SharedB0TabularInputs:
    """严格验证后可直接交给统一树模型执行器的输入及绑定。"""

    prepared: tabular_baselines.PreparedTabularData
    data_manifest: Mapping[str, object]


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SharedB0TabularError(f"{description}必须是对象")
    return value


def _read_json(path: Path, description: str) -> dict[str, object]:
    if not path.is_file():
        raise SharedB0TabularError(f"{description}不存在：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedB0TabularError(f"无法读取{description}：{path}") from error
    if not isinstance(value, dict):
        raise SharedB0TabularError(f"{description}顶层必须是对象")
    return value


def _expected_sha256(value: object, description: str) -> str:
    digest = str(value).strip()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise SharedB0TabularError(f"{description}必须是小写 SHA-256")
    return digest


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _registered_artifact(
    dataset_dir: Path,
    artifacts: Mapping[str, object],
    relative_path: str,
) -> tuple[Path, dict[str, object]]:
    try:
        raw_entry = artifacts[relative_path]
    except KeyError as error:
        raise SharedB0TabularError(f"checksums.json 未登记必需制品：{relative_path}") from error
    entry = _mapping(raw_entry, f"checksums.json 制品 {relative_path}")
    expected_digest = _expected_sha256(entry.get("sha256"), f"{relative_path} 登记哈希")
    expected_size = entry.get("size_bytes")
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size < 0:
        raise SharedB0TabularError(f"{relative_path} 登记大小必须是非负整数")

    path = (dataset_dir / relative_path).resolve()
    try:
        path.relative_to(dataset_dir)
    except ValueError as error:
        raise SharedB0TabularError(f"必需制品越过共享 B0 根目录：{relative_path}") from error
    if not path.is_file():
        raise SharedB0TabularError(f"必需制品不存在：{path}")
    actual_size = path.stat().st_size
    if actual_size != expected_size:
        raise SharedB0TabularError(
            f"{relative_path} 大小不一致：期望 {expected_size}，实际 {actual_size}"
        )
    actual_digest = file_sha256(path)
    if actual_digest != expected_digest:
        raise SharedB0TabularError(
            f"{relative_path} 哈希不一致：期望 {expected_digest}，实际 {actual_digest}"
        )
    return path, {"sha256": actual_digest, "size_bytes": actual_size}


def _validate_publication_contract(
    dataset_dir: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    if not dataset_dir.is_dir():
        raise SharedB0TabularError(f"共享 B0 目录不存在：{dataset_dir}")
    if dataset_dir.name.endswith(".partial") or (dataset_dir / "_INCOMPLETE").exists():
        raise SharedB0TabularError(f"共享 B0 仍处于未完成状态：{dataset_dir}")
    if (dataset_dir / "materialization_state.json").exists():
        raise SharedB0TabularError(f"共享 B0 含运行中状态文件，拒绝读取：{dataset_dir}")

    checksums_path = dataset_dir / "manifests" / "checksums.json"
    freeze_path = dataset_dir / "manifests" / "freeze_manifest.json"
    checksums = _read_json(checksums_path, "共享 B0 checksums.json")
    freeze = _read_json(freeze_path, "共享 B0 freeze_manifest.json")
    if checksums.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise SharedB0TabularError("checksums.json schema_version 不符合共享 B0 合同")
    if freeze.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise SharedB0TabularError("freeze_manifest.json schema_version 不符合共享 B0 合同")
    if freeze.get("stage") != EXPECTED_STAGE or freeze.get("status") != EXPECTED_STATUS:
        raise SharedB0TabularError(
            "共享 B0 正式入口只接受 "
            f"{EXPECTED_STAGE}/{EXPECTED_STATUS}，实际为 "
            f"{freeze.get('stage')}/{freeze.get('status')}"
        )
    if freeze.get("atomic_publication") is not True:
        raise SharedB0TabularError("freeze_manifest.json 未声明原子发布完成")
    expected_checksums_sha = _expected_sha256(
        freeze.get("checksums_sha256"), "freeze_manifest.json.checksums_sha256"
    )
    actual_checksums_sha = file_sha256(checksums_path)
    if actual_checksums_sha != expected_checksums_sha:
        raise SharedB0TabularError(
            "checksums.json 与 freeze_manifest.json 绑定不一致："
            f"{actual_checksums_sha} != {expected_checksums_sha}"
        )

    artifacts = _mapping(checksums.get("artifacts"), "checksums.json.artifacts")
    verified: dict[str, object] = {}
    required_paths = {
        relative
        for _, common_relative, label_relative in REQUIRED_SPLITS.values()
        for relative in (common_relative, label_relative)
    }
    required_paths.update({"manifests/input_binding.json", "manifests/statistics.json"})
    for relative_path in sorted(required_paths):
        _, binding = _registered_artifact(dataset_dir, artifacts, relative_path)
        verified[relative_path] = binding

    input_binding_sha = _expected_sha256(
        freeze.get("input_binding_sha256"), "freeze_manifest.json.input_binding_sha256"
    )
    if verified["manifests/input_binding.json"]["sha256"] != input_binding_sha:
        raise SharedB0TabularError("input_binding.json 与 freeze_manifest.json 绑定不一致")
    statistics = _read_json(dataset_dir / "manifests" / "statistics.json", "共享 B0 statistics")
    if statistics.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise SharedB0TabularError("statistics.json schema_version 不符合共享 B0 合同")
    if statistics.get("stage") != EXPECTED_STAGE or statistics.get("status") != EXPECTED_STATUS:
        raise SharedB0TabularError("statistics.json 的阶段或状态与正式共享 B0 合同不一致")

    contract = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "stage": EXPECTED_STAGE,
        "status": EXPECTED_STATUS,
        "checksums_sha256": actual_checksums_sha,
        "freeze_manifest_sha256": file_sha256(freeze_path),
        "verified_artifacts": verified,
    }
    return contract, statistics


def _parquet_columns(path: Path, description: str) -> tuple[str, ...]:
    try:
        return tuple(pq.ParquetFile(path).schema_arrow.names)
    except Exception as error:
        raise SharedB0TabularError(f"无法读取{description} Parquet schema：{path}") from error


def _validate_key_columns(frame: pd.DataFrame, description: str) -> tuple[str, ...]:
    if frame.empty:
        raise SharedB0TabularError(f"{description}不能为空")
    raw_ids = frame["sample_id"].tolist()
    if any(not isinstance(value, str) or not value or value.strip() != value for value in raw_ids):
        raise SharedB0TabularError(f"{description} sample_id 必须是非空且无首尾空白的字符串")
    sample_ids = tuple(raw_ids)
    if len(sample_ids) != len(set(sample_ids)):
        raise SharedB0TabularError(f"{description} sample_id 必须唯一")

    orders = frame["stable_order"]
    if orders.isna().any() or is_bool_dtype(orders.dtype) or not is_integer_dtype(orders.dtype):
        raise SharedB0TabularError(f"{description} stable_order 必须是整数列")
    observed_orders = tuple(int(value) for value in orders.tolist())
    expected_orders = tuple(range(len(frame)))
    if observed_orders != expected_orders:
        raise SharedB0TabularError(f"{description} stable_order 必须从 0 开始逐行连续且唯一")
    return sample_ids


def _load_common_features(path: Path, description: str) -> tuple[tuple[str, ...], np.ndarray]:
    columns = _parquet_columns(path, description)
    if columns != FEATURE_COLUMNS:
        raise SharedB0TabularError(
            f"{description}列必须严格等于 sample_id、stable_order、8 个公共字段及 8 个掩码；"
            f"实际为 {list(columns)}"
        )
    try:
        frame = pd.read_parquet(path, columns=list(FEATURE_COLUMNS))
    except Exception as error:
        raise SharedB0TabularError(f"无法读取{description}：{path}") from error
    sample_ids = _validate_key_columns(frame, description)

    for field in EXPECTED_FEATURE_FIELDS:
        series = frame[field]
        if is_bool_dtype(series.dtype) or not is_numeric_dtype(series.dtype):
            raise SharedB0TabularError(f"{description}特征 {field} 必须是数值列")
    for field, mask_field in zip(COMMON_FIELDS, MASK_FIELDS, strict=True):
        mask = frame[mask_field]
        if (
            mask.isna().any()
            or not is_integer_dtype(mask.dtype)
            or set(int(value) for value in mask.tolist()) - {0, 1}
        ):
            raise SharedB0TabularError(f"{description}缺失掩码 {mask_field} 只能包含 0 或 1")
        expected_missing = frame[field].isna().to_numpy(dtype=np.int64)
        observed_missing = mask.to_numpy(dtype=np.int64)
        if not np.array_equal(expected_missing, observed_missing):
            raise SharedB0TabularError(f"{description}字段 {field} 与缺失掩码不一致")

    features = np.asarray(frame.loc[:, list(EXPECTED_FEATURE_FIELDS)], dtype=np.float64)
    if np.isinf(features).any():
        raise SharedB0TabularError(f"{description}公共特征包含无穷值")
    features.setflags(write=False)
    return sample_ids, features


def _load_labels(path: Path, description: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    columns = _parquet_columns(path, description)
    required = {"sample_id", "stable_order", LABEL_FIELD}
    missing = sorted(required.difference(columns))
    if missing:
        raise SharedB0TabularError(f"{description}缺少标签合同列：{', '.join(missing)}")
    try:
        # 文本列不进入内存，更不可能进入树模型特征矩阵。
        frame = pd.read_parquet(path, columns=["sample_id", "stable_order", LABEL_FIELD])
    except Exception as error:
        raise SharedB0TabularError(f"无法读取{description}：{path}") from error
    sample_ids = _validate_key_columns(frame, description)
    raw_labels = frame[LABEL_FIELD]
    if (
        raw_labels.isna().any()
        or is_bool_dtype(raw_labels.dtype)
        or not is_integer_dtype(raw_labels.dtype)
    ):
        raise SharedB0TabularError(f"{description} label 必须是只含 0/1 的整数列")
    values = tuple(int(value) for value in raw_labels.tolist())
    if set(values) - {0, 1}:
        raise SharedB0TabularError(f"{description} label 必须是只含 0/1 的整数列")
    labels = tuple("benign" if value == 0 else "malicious" for value in values)
    return sample_ids, labels


def _pair_binding_sha256(
    common_binding: Mapping[str, object], label_binding: Mapping[str, object]
) -> str:
    return _canonical_sha256(
        {
            "common_features_sha256": common_binding["sha256"],
            "label_view_sha256": label_binding["sha256"],
        }
    )


def _load_split(
    *,
    dataset_dir: Path,
    name: str,
    split_id: str,
    common_relative: str,
    label_relative: str,
    verified_artifacts: Mapping[str, object],
) -> tuple[TabularSplit, dict[str, object]]:
    common_ids, features = _load_common_features(dataset_dir / common_relative, f"{name} 公共特征")
    label_ids, labels = _load_labels(dataset_dir / label_relative, f"{name} 标签视图")
    if common_ids != label_ids:
        mismatch_index = next(
            (
                index
                for index, (common_id, label_id) in enumerate(
                    zip(common_ids, label_ids, strict=False)
                )
                if common_id != label_id
            ),
            min(len(common_ids), len(label_ids)),
        )
        raise SharedB0TabularError(
            f"{name} 公共特征与标签视图的 sample_id/stable_order 未逐行完全一致，"
            f"首个错配位置为 {mismatch_index}"
        )

    common_binding = _mapping(verified_artifacts[common_relative], common_relative)
    label_binding = _mapping(verified_artifacts[label_relative], label_relative)
    pair_sha256 = _pair_binding_sha256(common_binding, label_binding)
    manifest = SplitManifest(
        relative_path=common_relative,
        protocol_version=ARTIFACT_SCHEMA_VERSION,
        suite_id=SHARED_B0_SUITE_ID,
        split_id=split_id,
        sample_ids=common_ids,
        sha256=pair_sha256,
        samples_sha256=pair_sha256,
        sample_order_sha256=sample_order_sha256(common_ids),
    )
    split = TabularSplit(
        manifest=manifest,
        sample_ids=common_ids,
        features=features,
        labels=labels,
        feature_fields=EXPECTED_FEATURE_FIELDS,
        label_field=LABEL_FIELD,
    )
    binding = {
        "split_id": split_id,
        "sample_count": len(common_ids),
        "sample_order_sha256": manifest.sample_order_sha256,
        "pair_binding_sha256": pair_sha256,
        "common_features": {"path": common_relative, **dict(common_binding)},
        "label_view": {"path": label_relative, **dict(label_binding)},
        "label_column": LABEL_FIELD,
        "excluded_from_features": ["label", "text", "input_text"],
    }
    return split, binding


def _validate_counts(
    *,
    contract: Mapping[str, object],
    statistics: Mapping[str, object],
    splits: Mapping[str, TabularSplit],
) -> None:
    freeze = _read_json(
        Path(str(contract["dataset_dir"])) / "manifests" / "freeze_manifest.json",
        "共享 B0 freeze_manifest.json",
    )
    candidate_count = len(splits["train"].sample_ids)
    validation_counts = {name: len(splits[name].sample_ids) for name in ("genis", "tqhc2")}
    if freeze.get("candidate_count") != candidate_count:
        raise SharedB0TabularError("freeze_manifest.json 的候选数量与 Parquet 不一致")
    if freeze.get("validation_counts") != validation_counts:
        raise SharedB0TabularError("freeze_manifest.json 的验证数量与 Parquet 不一致")
    if statistics.get("candidate_count") != candidate_count:
        raise SharedB0TabularError("statistics.json 的候选数量与 Parquet 不一致")
    raw_validation = _mapping(statistics.get("validation"), "statistics.json.validation")
    for name, expected_count in validation_counts.items():
        values = _mapping(raw_validation.get(name), f"statistics.json.validation.{name}")
        if values.get("count") != expected_count:
            raise SharedB0TabularError(f"statistics.json 的 {name} 验证数量与 Parquet 不一致")


def prepare_shared_b0_tabular_data(dataset_dir: Path) -> SharedB0TabularInputs:
    """验证共享 B0 哈希、字段、顺序与隔离，并构造统一树模型输入。"""
    root = Path(dataset_dir).expanduser().resolve()
    publication_contract, statistics = _validate_publication_contract(root)
    verified_artifacts = _mapping(publication_contract["verified_artifacts"], "已验证共享 B0 制品")

    splits: dict[str, TabularSplit] = {}
    split_bindings: dict[str, object] = {}
    for name, (split_id, common_relative, label_relative) in REQUIRED_SPLITS.items():
        split, binding = _load_split(
            dataset_dir=root,
            name=name,
            split_id=split_id,
            common_relative=common_relative,
            label_relative=label_relative,
            verified_artifacts=verified_artifacts,
        )
        splits[name] = split
        split_bindings[name] = binding

    train_ids = set(splits["train"].sample_ids)
    evaluation_ids: set[str] = set()
    for name in ("genis", "tqhc2"):
        current_ids = set(splits[name].sample_ids)
        overlap = train_ids.intersection(current_ids)
        if overlap:
            raise SharedB0TabularError(f"训练与 {name} 验证样本重叠：{sorted(overlap)[0]}")
        evaluation_overlap = evaluation_ids.intersection(current_ids)
        if evaluation_overlap:
            raise SharedB0TabularError(
                f"GeNIS 与 TQH-C2 验证样本重叠：{sorted(evaluation_overlap)[0]}"
            )
        evaluation_ids.update(current_ids)

    contract_for_counts = {**publication_contract, "dataset_dir": str(root)}
    _validate_counts(contract=contract_for_counts, statistics=statistics, splits=splits)

    known_labels = tuple(sorted(set(splits["train"].labels)))
    if known_labels != ("benign", "malicious"):
        raise SharedB0TabularError("训练标签必须同时且只包含 benign 与 malicious")
    label_to_index = {label: index for index, label in enumerate(known_labels)}
    encoded_labels = np.asarray(
        [label_to_index[label] for label in splits["train"].labels], dtype=np.int64
    )
    sample_weights = np.asarray(
        tabular_baselines.compute_sample_weight(class_weight="balanced", y=encoded_labels),
        dtype=np.float64,
    )
    encoded_labels.setflags(write=False)
    sample_weights.setflags(write=False)

    artifact_hashes = {
        path: str(_mapping(binding, path)["sha256"]) for path, binding in verified_artifacts.items()
    }
    dataset_binding_sha256 = _canonical_sha256(artifact_hashes)
    field_roles = {
        field: FieldRole(name=field, role="model_input", views=(SHARED_B0_VIEW_NAME,))
        for field in EXPECTED_FEATURE_FIELDS
    }
    field_roles[LABEL_FIELD] = FieldRole(name=LABEL_FIELD, role="label_target", views=())
    field_roles_sha256 = _canonical_sha256(
        {name: {"role": role.role, "views": list(role.views)} for name, role in field_roles.items()}
    )
    protocol = FrozenProtocol(
        root=root,
        protocol_version=ARTIFACT_SCHEMA_VERSION,
        status=EXPECTED_STATUS,
        phase=EXPECTED_STAGE,
        protocol_sha256=str(publication_contract["freeze_manifest_sha256"]),
        samples_sha256=dataset_binding_sha256,
        field_roles_sha256=field_roles_sha256,
        artifact_hashes=MappingProxyType(artifact_hashes),
        field_roles=MappingProxyType(field_roles),
        model_views=MappingProxyType(
            {
                SHARED_B0_VIEW_NAME: ModelView(
                    name=SHARED_B0_VIEW_NAME,
                    feature_fields=EXPECTED_FEATURE_FIELDS,
                )
            }
        ),
        manifests=MappingProxyType(
            {split.manifest.relative_path: split.manifest for split in splits.values()}
        ),
        _samples=pd.DataFrame(),
    )
    prepared = tabular_baselines.PreparedTabularData(
        protocol=protocol,
        view_name=SHARED_B0_VIEW_NAME,
        train=splits["train"],
        evaluations=MappingProxyType({name: splits[name] for name in ("genis", "tqhc2")}),
        known_labels=known_labels,
        encoded_train_labels=encoded_labels,
        train_sample_weights=sample_weights,
        feature_matrix_sha256=tabular_baselines._array_sha256(splits["train"].features),
        train_labels_sha256=tabular_baselines._labels_sha256(splits["train"].labels),
    )
    data_manifest = {
        "schema_version": "flow_probe_shared_b0_tabular_input_v1",
        "dataset_dir": str(root),
        "stage": EXPECTED_STAGE,
        "status": EXPECTED_STATUS,
        "checksums_sha256": publication_contract["checksums_sha256"],
        "freeze_manifest_sha256": publication_contract["freeze_manifest_sha256"],
        "dataset_binding_sha256": dataset_binding_sha256,
        "feature_fields": list(EXPECTED_FEATURE_FIELDS),
        "label_source": "每个 BERT Parquet 的 label 列",
        "splits": split_bindings,
    }
    return SharedB0TabularInputs(
        prepared=prepared,
        data_manifest=MappingProxyType(data_manifest),
    )


def run_shared_b0_tabular_baseline_suite(
    *,
    dataset_dir: Path,
    seed: int,
    model_keys: Sequence[str] = tabular_baselines.SUPPORTED_MODELS,
    predictions_path: Path | None = None,
    tuning_trial_index: int = 0,
) -> tabular_baselines.TabularSuiteResult:
    """以统一执行器运行共享 B0 树模型，不启用在线跟踪。"""
    inputs = prepare_shared_b0_tabular_data(dataset_dir)
    runtime = tabular_baselines.detect_runtime_capabilities()
    return tabular_baselines._execute_prepared_suite(
        prepared=inputs.prepared,
        model_keys=model_keys,
        seed=seed,
        predictions_path=predictions_path,
        runtime_capabilities=runtime,
        stage=EXPECTED_STAGE,
        tuning_trial_index=tuning_trial_index,
    )


def _write_json_atomic(path: Path, value: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.partial")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _artifact_record(path: Path, root: Path) -> dict[str, object]:
    root = Path(root).resolve()
    candidate = Path(path)
    if candidate.is_symlink() or not candidate.is_file():
        raise SharedB0TabularError(f"运行制品必须是普通文件：{candidate}")
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise SharedB0TabularError(f"运行制品越过唯一运行目录：{candidate}") from error
    return {
        "path": relative.as_posix(),
        "size_bytes": resolved.stat().st_size,
        "sha256": file_sha256(resolved),
    }


def _write_worker_state(output: Path, state: str, **extra: object) -> None:
    _write_json_atomic(
        output / "run_state.json",
        {
            "schema_version": "flow_probe_isolated_model_state_v1",
            "state": state,
            "model_process_id": os.getpid(),
            **extra,
        },
    )


def run_isolated_shared_b0_tabular_model(
    *,
    dataset_dir: Path,
    output_dir: Path,
    seed: int,
    model_key: str,
    tuning_trial_index: int = 0,
) -> dict[str, object]:
    """在独立进程中只运行一个模型，并记录端到端进程内存高水位。"""
    keys = tabular_baselines._normalise_model_keys((model_key,))
    model_key = keys[0]
    output = Path(output_dir).expanduser()
    if output.exists() or output.is_symlink():
        raise SharedB0TabularError(f"模型子运行目录已存在，拒绝覆盖：{output}")
    output.mkdir(parents=True)
    _write_worker_state(output, "prepared", model_key=model_key)

    config_path = output / "config_snapshot.json"
    environment_path = output / "environment.json"
    data_manifest_path = output / "data_manifest.json"
    predictions_path = output / "predictions.jsonl.gz"
    summary_path = output / "summary.json"
    cost_path = output / "cost.json"
    console_path = output / "console.log"
    try:
        _write_worker_state(output, "running", model_key=model_key)
        with capture_console_log(console_path):
            inputs = prepare_shared_b0_tabular_data(dataset_dir)
            runtime = tabular_baselines.detect_runtime_capabilities()
            result = tabular_baselines._execute_prepared_suite(
                prepared=inputs.prepared,
                model_keys=(model_key,),
                seed=seed,
                predictions_path=predictions_path,
                runtime_capabilities=runtime,
                stage=EXPECTED_STAGE,
                tuning_trial_index=tuning_trial_index,
            )
            summary = dict(result.summary)
            summary["execution_isolation"] = "single_model_fresh_process"
            summary["model_process_id"] = os.getpid()
            cost = dict(result.cost)
            isolated_model_cost = dict(_mapping(cost["models"], "模型成本")[model_key])
            isolated_model_cost.update(
                {
                    "peak_process_rss_measurement_scope": (
                        "isolated_single_model_process_end_to_end"
                    ),
                    "model_process_id": os.getpid(),
                }
            )
            cost["models"] = {model_key: isolated_model_cost}
            cost["execution_isolation"] = "single_model_fresh_process"
            config = {
                "seed": seed,
                "stage": EXPECTED_STAGE,
                "status": EXPECTED_STATUS,
                "validation_budget": tabular_baselines._validation_budget(tuning_trial_index),
                "model_key": model_key,
                "dataset_dir": str(inputs.prepared.protocol.root),
                "dataset_binding_sha256": inputs.prepared.protocol.samples_sha256,
                "view_name": SHARED_B0_VIEW_NAME,
                "feature_fields": list(EXPECTED_FEATURE_FIELDS),
                "label_field": LABEL_FIELD,
                "execution_isolation": "single_model_fresh_process",
            }
            environment = {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "pyarrow": tabular_baselines._package_version("pyarrow"),
                "scikit_learn": sklearn.__version__,
                "xgboost": (
                    tabular_baselines._package_version("xgboost")
                    if model_key == "xgboost"
                    else None
                ),
                "runtime": runtime,
            }
            tabular_baselines._write_json(config_path, config)
            tabular_baselines._write_json(environment_path, environment)
            tabular_baselines._write_json(data_manifest_path, dict(inputs.data_manifest))
            tabular_baselines._write_json(summary_path, summary)
            tabular_baselines._write_json(cost_path, cost)
            print(
                f"独立模型子运行完成：model={model_key}，pid={os.getpid()}，"
                f"rss={isolated_model_cost['peak_process_rss_bytes_after_model']}"
            )
        _write_worker_state(output, "finished", model_key=model_key, exit_code=0)
    except BaseException as error:
        _write_worker_state(
            output,
            "failed",
            model_key=model_key,
            exit_code=1,
            error_type=type(error).__name__,
        )
        raise

    artifacts = {
        "config_snapshot": config_path,
        "environment": environment_path,
        "data_manifest": data_manifest_path,
        "predictions": predictions_path,
        "summary": summary_path,
        "cost": cost_path,
        "console_log": console_path,
        "run_state": output / "run_state.json",
    }
    manifest = {
        "schema_version": "flow_probe_isolated_model_artifacts_v1",
        "status": "finished",
        "stage": EXPECTED_STAGE,
        "protocol_status": EXPECTED_STATUS,
        "seed": seed,
        "model_key": model_key,
        "model_process_id": os.getpid(),
        "artifacts": {
            name: _artifact_record(path, output) for name, path in sorted(artifacts.items())
        },
    }
    _write_json_atomic(output / "artifact_manifest.json", manifest)
    return manifest


def _launch_isolated_model_process(
    *,
    dataset_dir: Path,
    output_dir: Path,
    seed: int,
    model_key: str,
    tuning_trial_index: int,
) -> dict[str, object]:
    command = [
        sys.executable,
        "-m",
        "flow_probe.shared_b0_tabular_baselines",
        "worker",
        "--dataset-dir",
        str(dataset_dir),
        "--output-dir",
        str(output_dir),
        "--seed",
        str(seed),
        "--model",
        model_key,
        "--tuning-trial-index",
        str(tuning_trial_index),
    ]
    try:
        completed = subprocess.run(command, check=False)
    except OSError as error:
        raise SharedB0TabularError(f"无法启动 {model_key} 独立模型进程") from error
    if completed.returncode != 0:
        raise SharedB0TabularError(f"{model_key} 独立模型进程失败，退出码为 {completed.returncode}")
    manifest = _read_json(Path(output_dir) / "artifact_manifest.json", f"{model_key} 子运行清单")
    if manifest.get("status") != "finished" or manifest.get("model_key") != model_key:
        raise SharedB0TabularError(f"{model_key} 子运行清单状态或模型键不一致")
    process_id = manifest.get("model_process_id")
    if isinstance(process_id, bool) or not isinstance(process_id, int) or process_id == os.getpid():
        raise SharedB0TabularError(f"{model_key} 未在独立模型进程中完成")
    return manifest


def _merge_isolated_model_results(
    *,
    model_keys: Sequence[str],
    model_run_dirs: Mapping[str, Path],
    predictions_path: Path,
) -> tabular_baselines.TabularSuiteResult:
    keys = tabular_baselines._normalise_model_keys(model_keys)
    reference_summary: dict[str, object] | None = None
    reference_cost: dict[str, object] | None = None
    model_results: dict[str, object] = {}
    model_costs: dict[str, object] = {}
    process_ids: dict[str, int] = {}
    stable_summary_fields = (
        "schema_version",
        "seed",
        "stage",
        "validation_budget",
        "runtime",
        "input_contract",
        "train_sample_count",
        "train_label_distribution",
    )
    stable_cost_fields = ("schema_version", "seed", "stage", "validation_budget", "runtime")

    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(predictions_path, "xt", encoding="utf-8") as destination:
        for model_key in keys:
            run_dir = Path(model_run_dirs[model_key])
            summary = _read_json(run_dir / "summary.json", f"{model_key} 子运行摘要")
            cost = _read_json(run_dir / "cost.json", f"{model_key} 子运行成本")
            manifest = _read_json(run_dir / "artifact_manifest.json", f"{model_key} 子运行清单")
            if summary.get("model_keys") != [model_key]:
                raise SharedB0TabularError(f"{model_key} 子运行摘要含其他模型")
            summary_models = _mapping(summary.get("models"), f"{model_key} 子运行摘要模型")
            cost_models = _mapping(cost.get("models"), f"{model_key} 子运行成本模型")
            if set(summary_models) != {model_key} or set(cost_models) != {model_key}:
                raise SharedB0TabularError(f"{model_key} 子运行模型制品不唯一")
            process_id = manifest.get("model_process_id")
            if isinstance(process_id, bool) or not isinstance(process_id, int):
                raise SharedB0TabularError(f"{model_key} 子运行缺少有效进程标识")
            process_ids[model_key] = process_id

            if reference_summary is None:
                reference_summary = summary
                reference_cost = cost
            else:
                for field in stable_summary_fields:
                    if summary.get(field) != reference_summary.get(field):
                        raise SharedB0TabularError(
                            f"{model_key} 子运行摘要字段 {field} 与首个模型不一致"
                        )
                assert reference_cost is not None
                for field in stable_cost_fields:
                    if cost.get(field) != reference_cost.get(field):
                        raise SharedB0TabularError(
                            f"{model_key} 子运行成本字段 {field} 与首个模型不一致"
                        )
            model_results[model_key] = summary_models[model_key]
            model_costs[model_key] = cost_models[model_key]
            with gzip.open(run_dir / "predictions.jsonl.gz", "rt", encoding="utf-8") as source:
                shutil.copyfileobj(source, destination)

    if reference_summary is None or reference_cost is None:
        raise SharedB0TabularError("没有可合并的独立模型结果")
    if len(set(process_ids.values())) != len(process_ids):
        raise SharedB0TabularError("多个模型复用了同一个进程，逐模型内存证据无效")

    merged_summary = {
        **{field: reference_summary[field] for field in stable_summary_fields},
        "model_keys": list(keys),
        "execution_isolation": "one_fresh_process_per_model",
        "model_process_ids": process_ids,
        "models": model_results,
    }
    merged_cost = {
        **{field: reference_cost[field] for field in stable_cost_fields},
        "execution_isolation": "one_fresh_process_per_model",
        "model_process_ids": process_ids,
        "models": model_costs,
    }
    return tabular_baselines.TabularSuiteResult(summary=merged_summary, cost=merged_cost)


def _validate_prepared_run_root(output: Path) -> None:
    if output.is_symlink() or not output.is_dir():
        raise SharedB0TabularError(f"预备运行根目录不是普通目录：{output}")
    allowed = set(LAUNCHER_EVIDENCE_FILES.values()) - {"launcher-exit-code.txt"}
    observed = {path.name for path in output.iterdir()}
    unexpected = sorted(observed.difference(allowed))
    missing = sorted(allowed.difference(observed))
    if unexpected or missing:
        raise SharedB0TabularError(
            f"预备运行根目录文件不符合合同：缺少={missing}，额外={unexpected}"
        )
    state = _read_json(output / LAUNCHER_EVIDENCE_FILES["launcher_state"], "启动器状态")
    if state.get("state") != "running":
        raise SharedB0TabularError("正式 Python 入口只接受 running 启动状态")


def finalize_run_artifact_manifest(run_root: Path) -> dict[str, object]:
    """在启动器写完最终状态和退出码后，登记唯一运行目录内全部普通文件。"""
    root = Path(run_root).expanduser().resolve()
    manifest_path = root / "artifact_manifest.json"
    manifest = _read_json(manifest_path, "运行制品清单")
    if manifest.get("status") != "finished":
        raise SharedB0TabularError("只允许为成功完成的运行补齐最终制品登记")
    state = _read_json(root / LAUNCHER_EVIDENCE_FILES["launcher_state"], "启动器最终状态")
    if state.get("state") != "finished":
        raise SharedB0TabularError("启动器最终状态不是 finished")
    exit_code_text = (root / LAUNCHER_EVIDENCE_FILES["launcher_exit_code"]).read_text(
        encoding="utf-8"
    )
    if exit_code_text.strip() != "0":
        raise SharedB0TabularError("启动器最终退出码不是 0")
    config = _read_json(root / "config_snapshot.json", "正式配置快照")
    model_keys = tabular_baselines._normalise_model_keys(
        tuple(str(key) for key in config.get("model_keys", ()))
    )
    for model_key in model_keys:
        model_root = root / MODEL_RUNS_DIRECTORY / model_key
        model_state = _read_json(model_root / "run_state.json", f"{model_key} 子运行状态")
        model_manifest = _read_json(
            model_root / "artifact_manifest.json", f"{model_key} 子运行制品清单"
        )
        if model_state.get("state") != "finished" or model_manifest.get("status") != "finished":
            raise SharedB0TabularError(f"{model_key} 子运行未完整完成")

    artifact_records: dict[str, object] = {}
    for path in sorted(root.rglob("*")):
        if path == manifest_path:
            continue
        if path.is_symlink():
            raise SharedB0TabularError(f"运行根目录内不允许符号链接：{path}")
        if path.is_file():
            record = _artifact_record(path, root)
            artifact_records[str(record["path"])] = record
    required_relative_paths = set(LAUNCHER_EVIDENCE_FILES.values())
    required_relative_paths.update(
        {f"{MODEL_RUNS_DIRECTORY}/{model_key}/artifact_manifest.json" for model_key in model_keys}
    )
    missing = sorted(required_relative_paths.difference(artifact_records))
    if missing:
        raise SharedB0TabularError(f"最终制品登记缺少必需文件：{missing}")
    final_manifest = {
        **manifest,
        "launcher_state": "finished",
        "launcher_exit_code": 0,
        "artifact_count": len(artifact_records),
        "artifact_records": artifact_records,
    }
    _write_json_atomic(manifest_path, final_manifest)
    return final_manifest


def run_tracked_shared_b0_tabular_baselines(
    *,
    dataset_dir: Path,
    output_dir: Path,
    seed: int,
    run_name: str,
    model_keys: Sequence[str] = tabular_baselines.SUPPORTED_MODELS,
    tuning_trial_index: int = 0,
    allow_prepared_output: bool = False,
) -> dict[str, object]:
    """运行正式共享 B0 基线，并保存在线跟踪和完整输入绑定。"""
    output = Path(output_dir).expanduser()
    if allow_prepared_output:
        _validate_prepared_run_root(output)
    elif output.exists() or output.is_symlink():
        raise SharedB0TabularError(f"运行目录已存在，拒绝覆盖：{output}")
    keys = tabular_baselines._normalise_model_keys(model_keys)
    validation_budget = tabular_baselines._validation_budget(tuning_trial_index)
    if "xgboost" in keys:
        tabular_baselines._import_xgboost()
    inputs = prepare_shared_b0_tabular_data(dataset_dir)
    prepared = inputs.prepared
    runtime = tabular_baselines.detect_runtime_capabilities()

    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "共享 B0 公共数值视图上的 HGB 与 XGBoost 候选基线",
            "mode": "online",
            "tags": ["shared-b0", "theory-selection", "review-pending", "hgb-xgb"],
        }
    )
    config_path = output / "config_snapshot.json"
    environment_path = output / "environment.json"
    data_manifest_path = output / "data_manifest.json"
    predictions_path = output / "predictions.jsonl.gz"
    summary_path = output / "summary.json"
    cost_path = output / "cost.json"
    metrics_path = output / "swanlab_metrics.json"
    metadata_path = output / "swanlab_metadata.json"
    model_run_dirs = {key: output / MODEL_RUNS_DIRECTORY / key for key in keys}
    config: dict[str, object] = {
        "seed": seed,
        "stage": EXPECTED_STAGE,
        "status": EXPECTED_STATUS,
        "validation_budget": validation_budget,
        "model_keys": list(keys),
        "dataset_dir": str(prepared.protocol.root),
        "dataset_binding_sha256": prepared.protocol.samples_sha256,
        "view_name": SHARED_B0_VIEW_NAME,
        "feature_fields": list(EXPECTED_FEATURE_FIELDS),
        "label_field": LABEL_FIELD,
        "runtime": runtime,
        "execution_isolation": "one_fresh_process_per_model",
    }
    metadata: dict[str, object] = {
        "workspace": settings.workspace,
        "project": settings.project,
        "phase": "shared-b0-tabular",
        "data_stage": EXPECTED_STAGE,
        "data_status": EXPECTED_STATUS,
        "validation_budget": validation_budget,
        "tracking_mode": settings.mode,
        "metric_prefix": "tabular",
        "tags": list(settings.tags),
        "runtime": runtime,
        "execution_isolation": "one_fresh_process_per_model",
        "input_manifest_sha256": {
            name: split.manifest.sha256
            for name, split in {"train": prepared.train, **prepared.evaluations}.items()
        },
    }
    data_files: dict[str, Path] = {
        "config_snapshot": config_path,
        "environment": environment_path,
        "data_manifest": data_manifest_path,
        "predictions": predictions_path,
        "summary": summary_path,
        "cost": cost_path,
        "swanlab_metrics": metrics_path,
        "swanlab_metadata": metadata_path,
    }
    if allow_prepared_output:
        data_files.update(
            {name: output / relative for name, relative in LAUNCHER_EVIDENCE_FILES.items()}
        )
    for model_key, model_root in model_run_dirs.items():
        for artifact_name in (
            "artifact_manifest",
            "config_snapshot",
            "environment",
            "data_manifest",
            "predictions",
            "summary",
            "cost",
            "console_log",
            "run_state",
        ):
            filename = {
                "artifact_manifest": "artifact_manifest.json",
                "config_snapshot": "config_snapshot.json",
                "environment": "environment.json",
                "data_manifest": "data_manifest.json",
                "predictions": "predictions.jsonl.gz",
                "summary": "summary.json",
                "cost": "cost.json",
                "console_log": "console.log",
                "run_state": "run_state.json",
            }[artifact_name]
            data_files[f"model_{model_key}_{artifact_name}"] = model_root / filename

    with (
        capture_console_log(output / "console.log"),
        swanlab_run(
            settings=settings,
            phase="shared-b0-tabular",
            config=config,
            artifact_dir=output,
            data_files=data_files,
        ) as swanlab,
    ):
        tabular_baselines._write_json(config_path, config)
        tabular_baselines._write_json(
            environment_path,
            {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "pyarrow": tabular_baselines._package_version("pyarrow"),
                "scikit_learn": sklearn.__version__,
                "xgboost": (
                    tabular_baselines._package_version("xgboost") if "xgboost" in keys else None
                ),
                "runtime": runtime,
            },
        )
        tabular_baselines._write_json(data_manifest_path, dict(inputs.data_manifest))
        tabular_baselines._write_json(metadata_path, metadata)
        print(
            f"开始共享 B0 树模型基线：train={len(prepared.train.sample_ids)}，"
            f"models={','.join(keys)}，status={EXPECTED_STATUS}，每模型独立进程"
        )
        for model_key in keys:
            print(f"启动独立模型进程：{model_key}")
            _launch_isolated_model_process(
                dataset_dir=prepared.protocol.root,
                output_dir=model_run_dirs[model_key],
                seed=seed,
                model_key=model_key,
                tuning_trial_index=tuning_trial_index,
            )
        result = _merge_isolated_model_results(
            model_keys=keys,
            model_run_dirs=model_run_dirs,
            predictions_path=predictions_path,
        )
        tabular_baselines._write_json(summary_path, result.summary)
        tabular_baselines._write_json(cost_path, result.cost)
        scalar_metrics = {
            **flatten_scalar_metrics(result.summary, prefix="tabular"),
            **flatten_scalar_metrics(result.cost, prefix="cost"),
        }
        swanlab.log(scalar_metrics, step=0)
        tabular_baselines._write_json(metrics_path, {"step": 0, "metrics": scalar_metrics})
        print("共享 B0 树模型基线完成，两个模型子运行已合并到唯一运行目录")

    manifest = _read_json(output / "artifact_manifest.json", "运行制品清单")
    with capture_console_log(output / "console.log"):
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行共享 B0 严格 HGB/XGBoost 候选基线")
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--model", action="append", choices=tabular_baselines.SUPPORTED_MODELS)
    parser.add_argument("--tuning-trial-index", type=int, default=0)
    parser.add_argument("--allow-prepared-output", action="store_true")
    return parser


def _build_worker_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行单个共享 B0 树模型子进程")
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--model", choices=tabular_baselines.SUPPORTED_MODELS, required=True)
    parser.add_argument("--tuning-trial-index", type=int, default=0)
    return parser


def _build_finalize_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="补齐共享 B0 正式运行制品登记")
    parser.add_argument("--run-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        if arguments and arguments[0] == "worker":
            args = _build_worker_parser().parse_args(arguments[1:])
            run_isolated_shared_b0_tabular_model(
                dataset_dir=args.dataset_dir,
                output_dir=args.output_dir,
                seed=args.seed,
                model_key=args.model,
                tuning_trial_index=args.tuning_trial_index,
            )
        elif arguments and arguments[0] == "finalize":
            args = _build_finalize_parser().parse_args(arguments[1:])
            finalize_run_artifact_manifest(args.run_root)
        else:
            args = build_parser().parse_args(arguments)
            run_tracked_shared_b0_tabular_baselines(
                dataset_dir=args.dataset_dir,
                output_dir=args.output_dir,
                seed=args.seed,
                run_name=args.run_name,
                model_keys=args.model or tabular_baselines.SUPPORTED_MODELS,
                tuning_trial_index=args.tuning_trial_index,
                allow_prepared_output=args.allow_prepared_output,
            )
    except (
        tabular_baselines.TabularBaselineError,
        tabular_baselines.XGBoostDependencyError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
