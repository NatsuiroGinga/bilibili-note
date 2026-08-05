from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from flow_probe.r2_final_experts import ROUTE_NAMES, ROUTE_TO_INDEX, R2FinalExpertError


VARIANTS = ("F-A", "F-H", "F-P", "F-S", "F-R")
ALLOWED_SPLITS = ("train-fit", "calibration", "validation")
FINAL_MARKERS = ("final-test", "final_test", "time-forward-test", "open-set-test")
RANDOM_NAMESPACE = "r2-final-physics-random-v1"
SHUFFLE_NAMESPACE = "r2-final-physics-shuffle-v1"


class R2FinalViewError(ValueError):
    """表示最终 R2 数据视图违反冻结合同。"""


@dataclass(frozen=True)
class ArtifactSpec:
    path: Path
    sha256: str


@dataclass(frozen=True)
class ViewColumnSpec:
    sample_id: str
    stable_order: str
    split_id: str
    text: str
    label: str
    window_index: str
    window_valid: str
    history_fields: tuple[str, ...]
    history_missing_fields: tuple[str, ...]
    route_name: str
    route_confidence: str
    quic_applicable: str
    quic_formal_training_enabled: str
    source_dataset: str


@dataclass(frozen=True)
class DatasetViewContract:
    freeze_manifest: ArtifactSpec
    detection_views: Mapping[str, ArtifactSpec]
    common_histories: Mapping[str, ArtifactSpec]
    route_assignments: Mapping[str, ArtifactSpec]
    columns: ViewColumnSpec
    window_count: int
    final_test_visible: bool
    artifact_payload_merkle_sha256: str
    history_scales: tuple[float, ...]


@dataclass(frozen=True)
class BoundSequence:
    """与样本顺序和生产配置绑定的只读专家序列。"""

    sample_ids: tuple[str, ...]
    stable_orders: np.ndarray
    values: np.ndarray
    checkpoint_sha256: str
    production_sha256: str
    parameter_count: int
    trainable_parameter_count: int
    frozen_parameter_count: int
    checkpoint_trainable_parameter_count: int
    checkpoint_frozen_parameter_count: int
    branch_name: str
    checkpoint_binding_sha256: str
    quic_expert_ready: bool


@dataclass(frozen=True)
class BaseSplit:
    name: str
    sample_ids: tuple[str, ...]
    stable_orders: np.ndarray
    texts: tuple[str, ...]
    labels: np.ndarray
    histories: np.ndarray
    valid_masks: np.ndarray
    route_indices: np.ndarray
    route_confidences: np.ndarray
    quic_applicable: np.ndarray
    source_datasets: tuple[str, ...]

    def __len__(self) -> int:
        return len(self.sample_ids)


@dataclass(frozen=True)
class PreparedBaseViews:
    train: BaseSplit
    calibration: BaseSplit
    validation: BaseSplit
    binding: Mapping[str, object]


@dataclass(frozen=True)
class VariantSplit:
    name: str
    sample_ids: tuple[str, ...]
    stable_orders: np.ndarray
    texts: tuple[str, ...]
    labels: np.ndarray
    sidecar_sequence: np.ndarray
    sidecar_valid_mask: np.ndarray
    sidecar_gate: np.ndarray
    donor_sample_ids: tuple[str | None, ...]

    def __len__(self) -> int:
        return len(self.sample_ids)


@dataclass(frozen=True)
class PreparedVariantViews:
    variant: str
    train: VariantSplit
    calibration: VariantSplit
    validation: VariantSplit
    binding: Mapping[str, object]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def array_sha256(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(str(tuple(contiguous.shape)).encode("ascii"))
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def strings_sha256(values: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _verify_artifact(spec: ArtifactSpec, description: str) -> Path:
    path = spec.path.resolve()
    if not path.is_file() or path.is_symlink():
        raise R2FinalViewError(f"{description}不是普通文件：{path}")
    actual = file_sha256(path)
    if actual != spec.sha256:
        raise R2FinalViewError(
            f"{description} SHA-256 不一致：预期 {spec.sha256}，实际 {actual}"
        )
    return path


def _freeze_array(values: np.ndarray, description: str) -> np.ndarray:
    frozen = np.ascontiguousarray(values)
    if not np.isfinite(frozen).all() and frozen.dtype.kind == "f":
        raise R2FinalViewError(f"{description}包含非有限值")
    frozen.setflags(write=False)
    return frozen


def _binary_labels(values: Sequence[object]) -> np.ndarray:
    labels: list[int] = []
    for value in values:
        if value in (0, "0", "benign", "BENIGN"):
            labels.append(0)
        elif value in (1, "1", "attack", "ATTACK", "malicious", "MALICIOUS"):
            labels.append(1)
        else:
            raise R2FinalViewError(f"无法解释二分类标签：{value!r}")
    return np.asarray(labels, dtype=np.int64)


def _require_columns(frame: pd.DataFrame, required: set[str], description: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise R2FinalViewError(f"{description}缺少字段：{missing}")


def _validate_no_final_split(values: Sequence[str]) -> None:
    for split in values:
        normalized = split.lower().replace("_", "-")
        if any(marker.replace("_", "-") in normalized for marker in FINAL_MARKERS):
            raise R2FinalViewError(f"开发路线不得读取最终测试划分：{split}")
        if split not in ALLOWED_SPLITS:
            raise R2FinalViewError(f"不允许的开发划分：{split}")


def _strict_bool(values: pd.Series, description: str) -> np.ndarray:
    """只接受原生布尔或无空值的精确 0/1，拒绝字符串真值陷阱。"""

    if values.isna().any():
        raise R2FinalViewError(f"{description}包含空值")
    if pd.api.types.is_bool_dtype(values.dtype):
        return values.to_numpy(dtype=bool)
    if pd.api.types.is_numeric_dtype(values.dtype):
        numeric = values.to_numpy()
        if np.isin(numeric, (0, 1)).all():
            return numeric == 1
    raise R2FinalViewError(f"{description}只允许原生布尔或精确 0/1")


def _load_freeze_manifest(contract: DatasetViewContract) -> Mapping[str, object]:
    """在打开任何 Parquet 前验证开发角色、哈希和路由证据来源。"""

    path = _verify_artifact(contract.freeze_manifest, "冻结角色清单")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise R2FinalViewError("冻结角色清单不是合法 JSON") from error
    if not isinstance(manifest, dict):
        raise R2FinalViewError("冻结角色清单顶层必须是对象")
    if manifest.get("final_test_visible") is not False:
        raise R2FinalViewError("冻结角色清单必须声明 final_test_visible=false")
    if manifest.get("allowed_physics_splits") != list(ALLOWED_SPLITS):
        raise R2FinalViewError("冻结角色清单的物理开发划分白名单不一致")
    for description, specs in (
        ("检测视图", contract.detection_views),
        ("公共历史", contract.common_histories),
        ("路由视图", contract.route_assignments),
    ):
        if set(specs) != set(ALLOWED_SPLITS):
            raise R2FinalViewError(f"{description}必须在读前精确覆盖三个开发划分")
    artifacts = manifest.get("roles")
    if not isinstance(artifacts, dict):
        raise R2FinalViewError("冻结角色清单缺少 roles")
    development = artifacts.get("development_materialization_manifest")
    if not isinstance(development, dict) or (
        development.get("artifact_payload_merkle_sha256")
        != contract.artifact_payload_merkle_sha256
    ):
        raise R2FinalViewError("服务器开发视图 Merkle 与运行合同不一致")
    expected: dict[str, tuple[ArtifactSpec, str]] = {}
    expected_role_splits: dict[str, str] = {}
    role_names = {
        "train-fit": (
            "detection_view_train_fit",
            "common_history_train_fit",
            "route_assignments_train_fit",
        ),
        "calibration": (
            "detection_view_calibration",
            "common_history_calibration",
            "route_assignments_calibration",
        ),
        "validation": (
            "detection_view_development_validation",
            "common_history_development_validation",
            "route_assignments_development_validation",
        ),
    }
    for split, (detection_role, history_role, route_role) in role_names.items():
        expected[detection_role] = (
            contract.detection_views[split],
            "detection_supervision",
        )
        expected[history_role] = (
            contract.common_histories[split],
            "deployment_observable_causal_history",
        )
        expected[route_role] = (
            contract.route_assignments[split],
            "stop_gradient_inference_router",
        )
        expected_role_splits[detection_role] = split
        expected_role_splits[history_role] = split
        expected_role_splits[route_role] = split
    for name, (spec, role) in expected.items():
        record = artifacts.get(name)
        if not isinstance(record, dict):
            raise R2FinalViewError(f"冻结角色清单缺少 {name}")
        if record.get("sha256") != spec.sha256 or record.get("role") != role:
            raise R2FinalViewError(f"冻结角色清单的 {name} 哈希或角色不一致")
        if record.get("split_ids") != [expected_role_splits[name]]:
            raise R2FinalViewError(f"冻结角色清单的 {name} 划分角色不一致")
        if record.get("ready", True) is not True:
            raise R2FinalViewError(f"冻结角色清单的 {name} 尚未就绪")
    evidence = manifest.get("quic_inference_gate")
    if not isinstance(evidence, dict):
        raise R2FinalViewError("冻结角色清单缺少 QUIC 推理证据声明")
    fields = evidence.get("visible_evidence_fields")
    if not isinstance(fields, list) or not fields or not all(
        isinstance(field, str) and field for field in fields
    ):
        raise R2FinalViewError("QUIC 推理证据字段必须是非空字符串列表")
    forbidden = ("qlog", "label", "attack", "malicious", "scenario", "profile")
    lowered = tuple(field.lower() for field in fields)
    if evidence.get("uses_qlog") is not False or evidence.get("uses_label") is not False:
        raise R2FinalViewError("QUIC 推理证据不得使用 qlog 或标签")
    if evidence.get("udp_fallback") is not False or evidence.get("stop_gradient") is not True:
        raise R2FinalViewError("QUIC 推理门必须停止梯度且禁止 UDP 回退")
    if any(token in field for field in lowered for token in forbidden):
        raise R2FinalViewError("QUIC 推理证据字段包含训练特权或标签信息")
    return manifest


def _read_parquet(spec: ArtifactSpec, description: str) -> pd.DataFrame:
    path = _verify_artifact(spec, description)
    return pq.read_table(path).to_pandas()


def _read_split_parquets(
    specs: Mapping[str, ArtifactSpec],
    description: str,
) -> pd.DataFrame:
    if set(specs) != set(ALLOWED_SPLITS):
        raise R2FinalViewError(f"{description}必须精确覆盖三个开发划分")
    frames: list[pd.DataFrame] = []
    for split in ALLOWED_SPLITS:
        frame = _read_parquet(specs[split], f"{description}/{split}")
        frames.append(frame)
    return pd.concat(frames, axis=0, ignore_index=True, copy=False)


def _build_split(
    name: str,
    merged: pd.DataFrame,
    contract: DatasetViewContract,
) -> BaseSplit:
    columns = contract.columns
    frame = merged.loc[merged[columns.split_id] == name].copy()
    frame.sort_values(columns.stable_order, kind="mergesort", inplace=True)
    sample_rows = frame.drop_duplicates(columns.sample_id, keep="first")
    if len(sample_rows) == 0:
        raise R2FinalViewError(f"划分 {name} 不能为空")
    if sample_rows[columns.stable_order].duplicated().any():
        raise R2FinalViewError(f"划分 {name} 的 stable_order 必须唯一")
    expected_windows = list(range(contract.window_count))
    histories: list[np.ndarray] = []
    valid_masks: list[np.ndarray] = []
    for sample_id in sample_rows[columns.sample_id].astype(str):
        windows = frame.loc[frame[columns.sample_id].astype(str) == sample_id].copy()
        windows.sort_values(columns.window_index, kind="mergesort", inplace=True)
        if windows[columns.window_index].astype(int).tolist() != expected_windows:
            raise R2FinalViewError(f"样本 {sample_id} 的窗口索引不连续")
        history = windows[list(columns.history_fields)].to_numpy(dtype=np.float32)
        if len(columns.history_missing_fields) != history.shape[1]:
            raise R2FinalViewError("公共历史字段和缺失掩码长度不一致")
        missing = np.column_stack(
            [
                _strict_bool(
                    windows[field],
                    f"样本 {sample_id} 的 {field}",
                )
                for field in columns.history_missing_fields
            ]
        )
        if np.any((~np.isfinite(history)) & (~missing)):
            raise R2FinalViewError(f"样本 {sample_id} 的已观测历史包含非有限值")
        history[missing] = 0.0
        if len(contract.history_scales) != history.shape[1]:
            raise R2FinalViewError("公共历史字段和尺度长度不一致")
        scales = np.asarray(contract.history_scales, dtype=np.float32)
        if not np.isfinite(scales).all() or np.any(scales <= 0):
            raise R2FinalViewError("公共历史尺度必须是有限正数")
        history = history / scales[None, :]
        valid = _strict_bool(
            windows[columns.window_valid],
            f"样本 {sample_id} 的有效窗口掩码",
        )
        if history.shape != (contract.window_count, len(columns.history_fields)):
            raise R2FinalViewError(f"样本 {sample_id} 的公共历史形状非法")
        if not np.isfinite(history).all():
            raise R2FinalViewError(f"样本 {sample_id} 的公共历史包含非有限值")
        length = int(valid.sum())
        expected_valid = np.arange(contract.window_count) < length
        if not np.array_equal(valid, expected_valid):
            raise R2FinalViewError(f"样本 {sample_id} 的有效窗口不是前缀")
        histories.append(history)
        valid_masks.append(valid)
    route_names = sample_rows[columns.route_name].astype(str).tolist()
    invalid_routes = sorted(set(route_names) - set(ROUTE_NAMES))
    if invalid_routes:
        raise R2FinalViewError(f"存在未冻结的协议路由：{invalid_routes}")
    route_indices = np.asarray([ROUTE_TO_INDEX[name] for name in route_names], dtype=np.int64)
    confidences = sample_rows[columns.route_confidence].to_numpy(dtype=np.float32)
    if not np.isfinite(confidences).all() or np.any((confidences < 0) | (confidences > 1)):
        raise R2FinalViewError(f"划分 {name} 的协议置信度不在 [0,1]")
    quic_candidate = _strict_bool(
        sample_rows[columns.quic_applicable],
        f"划分 {name} 的 QUIC 候选适用掩码",
    )
    quic_enabled = _strict_bool(
        sample_rows[columns.quic_formal_training_enabled],
        f"划分 {name} 的 QUIC 正式训练开关",
    )
    quic_applicable = quic_candidate & quic_enabled
    return BaseSplit(
        name=name,
        sample_ids=tuple(sample_rows[columns.sample_id].astype(str)),
        stable_orders=_freeze_array(
            sample_rows[columns.stable_order].to_numpy(dtype=np.int64),
            f"{name} 稳定顺序",
        ),
        texts=tuple(sample_rows[columns.text].astype(str)),
        labels=_freeze_array(
            _binary_labels(sample_rows[columns.label].tolist()),
            f"{name} 标签",
        ),
        histories=_freeze_array(np.stack(histories), f"{name} 公共历史"),
        valid_masks=_freeze_array(np.stack(valid_masks), f"{name} 有效窗口"),
        route_indices=_freeze_array(route_indices, f"{name} 路由"),
        route_confidences=_freeze_array(confidences, f"{name} 路由置信度"),
        quic_applicable=_freeze_array(
            quic_applicable,
            f"{name} QUIC 推理适用掩码",
        ),
        source_datasets=tuple(sample_rows[columns.source_dataset].astype(str)),
    )


def load_base_views(contract: DatasetViewContract) -> PreparedBaseViews:
    """加载共同检测视图、公共历史和停止梯度路由。"""

    if contract.final_test_visible:
        raise R2FinalViewError("最终 R2 路线选择必须保持 final_test_visible=false")
    if contract.window_count <= 0:
        raise R2FinalViewError("window_count 必须为正整数")
    _load_freeze_manifest(contract)
    detection = _read_split_parquets(contract.detection_views, "检测视图")
    history = _read_split_parquets(contract.common_histories, "公共因果历史")
    routes = _read_split_parquets(contract.route_assignments, "协议路由视图")
    columns = contract.columns
    _require_columns(
        detection,
        {
            columns.sample_id,
            columns.stable_order,
            columns.split_id,
            columns.text,
            columns.label,
            columns.source_dataset,
        },
        "检测视图",
    )
    _require_columns(
        history,
        {
            columns.sample_id,
            columns.window_index,
            columns.window_valid,
            *columns.history_fields,
            *columns.history_missing_fields,
        },
        "公共因果历史",
    )
    _require_columns(
        routes,
        {
            columns.sample_id,
            columns.route_name,
            columns.route_confidence,
            columns.quic_applicable,
            columns.quic_formal_training_enabled,
        },
        "协议路由视图",
    )
    if detection[columns.sample_id].duplicated().any():
        raise R2FinalViewError("检测视图 sample_id 不唯一")
    if routes[columns.sample_id].duplicated().any():
        raise R2FinalViewError("协议路由视图 sample_id 不唯一")
    _validate_no_final_split(detection[columns.split_id].astype(str).tolist())
    detection_projection = detection[
        [
            columns.sample_id,
            columns.stable_order,
            columns.split_id,
            columns.text,
            columns.label,
            columns.source_dataset,
        ]
    ]
    route_projection = routes[
        [
            columns.sample_id,
            columns.route_name,
            columns.route_confidence,
            columns.quic_applicable,
            columns.quic_formal_training_enabled,
        ]
    ]
    merged = detection_projection.merge(
        route_projection,
        on=columns.sample_id,
        how="inner",
        validate="one_to_one",
    ).merge(
        history[
            [
                columns.sample_id,
                columns.window_index,
                columns.window_valid,
                *columns.history_fields,
                *columns.history_missing_fields,
            ]
        ],
        on=columns.sample_id,
        how="inner",
        validate="one_to_many",
    )
    expected_rows = len(detection) * contract.window_count
    if len(merged) != expected_rows:
        raise R2FinalViewError(
            f"三视图连接必须得到 {expected_rows} 行，实际 {len(merged)}"
        )
    splits = {
        name: _build_split(name, merged, contract) for name in ALLOWED_SPLITS
    }
    all_ids = [sample_id for split in splits.values() for sample_id in split.sample_ids]
    if len(all_ids) != len(set(all_ids)) or len(all_ids) != len(detection):
        raise R2FinalViewError("开发训练、校准和验证 sample_id 未形成互斥全集")
    binding = {
        "final_test_visible": False,
        "artifact_payload_merkle_sha256": contract.artifact_payload_merkle_sha256,
        "window_count": contract.window_count,
        "history_fields": list(columns.history_fields),
        "history_missing_fields": list(columns.history_missing_fields),
        "history_scales": list(contract.history_scales),
        "artifacts": {
            "freeze_manifest": contract.freeze_manifest.sha256,
            "detection_views": {
                split: contract.detection_views[split].sha256
                for split in ALLOWED_SPLITS
            },
            "common_histories": {
                split: contract.common_histories[split].sha256
                for split in ALLOWED_SPLITS
            },
            "route_assignments": {
                split: contract.route_assignments[split].sha256
                for split in ALLOWED_SPLITS
            },
        },
        "splits": {
            name: {
                "rows": len(split),
                "sample_order_sha256": strings_sha256(split.sample_ids),
                "stable_order_sha256": array_sha256(split.stable_orders),
                "stable_order_min": int(split.stable_orders.min()),
                "stable_order_max": int(split.stable_orders.max()),
                "stable_order_contiguous": bool(
                    np.array_equal(
                        split.stable_orders,
                        np.arange(
                            int(split.stable_orders.min()),
                            int(split.stable_orders.min()) + len(split),
                            dtype=np.int64,
                        ),
                    )
                ),
                "stable_order_renumbered": False,
                "history_sha256": array_sha256(split.histories),
                "labels_sha256": array_sha256(split.labels),
                "route_sha256": array_sha256(split.route_indices),
            }
            for name, split in splits.items()
        },
    }
    return PreparedBaseViews(
        train=splits["train-fit"],
        calibration=splits["calibration"],
        validation=splits["validation"],
        binding=binding,
    )


def _seed(namespace: str, seed: int, split: str) -> int:
    digest = hashlib.sha256(f"{namespace}\0{seed}\0{split}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _pad_raw_history(history: np.ndarray, output_dimension: int) -> np.ndarray:
    if history.shape[-1] > output_dimension:
        raise R2FinalViewError("F-H 原始历史维数大于统一旁路维数，不得静默截断")
    output = np.zeros(
        (*history.shape[:-1], output_dimension),
        dtype=np.float32,
    )
    output[..., : history.shape[-1]] = history
    return output


def _effective_route_name(
    split: BaseSplit,
    index: int,
    *,
    quic_expert_ready: bool,
) -> str:
    route_name = ROUTE_NAMES[int(split.route_indices[index])]
    if route_name == "QUIC" and (
        not bool(split.quic_applicable[index]) or not quic_expert_ready
    ):
        return "UNKNOWN"
    return route_name


def _sample_stratum(
    split: BaseSplit,
    index: int,
    *,
    include_split: bool,
    quic_expert_ready: bool,
) -> tuple[str, ...]:
    route_name = _effective_route_name(
        split,
        index,
        quic_expert_ready=quic_expert_ready,
    )
    values = (
        split.source_datasets[index],
        route_name,
        str(bool(split.quic_applicable[index])),
        str(quic_expert_ready),
    )
    return (*values, split.name) if include_split else values


def _shuffle_indices(
    split: BaseSplit,
    seed: int,
    *,
    quic_expert_ready: bool,
) -> tuple[np.ndarray, tuple[str, ...]]:
    donor_indices = np.full(len(split), -1, dtype=np.int64)
    strata: dict[tuple[str, ...], list[int]] = {}
    for index in range(len(split)):
        strata.setdefault(
            _sample_stratum(
                split,
                index,
                include_split=True,
                quic_expert_ready=quic_expert_ready,
            ),
            [],
        ).append(index)
    for key, indices in sorted(strata.items()):
        if len(indices) < 2:
            raise R2FinalViewError(f"F-S 分层不足两个样本：{key}")
        ordered = sorted(
            indices,
            key=lambda index: hashlib.sha256(
                f"{SHUFFLE_NAMESPACE}\0{seed}\0{key}\0{split.sample_ids[index]}".encode(
                    "utf-8"
                )
            ).hexdigest(),
        )
        rotated = ordered[1:] + ordered[:1]
        for target, donor in zip(ordered, rotated, strict=True):
            donor_indices[target] = donor
    if np.any(donor_indices < 0) or np.any(donor_indices == np.arange(len(split))):
        raise R2FinalViewError("F-S 供体映射不完整或出现自配对")
    donor_ids = tuple(split.sample_ids[int(index)] for index in donor_indices)
    return donor_indices, donor_ids


def _random_sidecar(
    target: BaseSplit,
    train: BaseSplit,
    train_physics: np.ndarray,
    seed: int,
    *,
    quic_expert_ready: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[str, ...]]:
    if train_physics.shape[:2] != train.histories.shape[:2]:
        raise R2FinalViewError("F-R 训练物理历史形状与训练公共历史不一致")
    output = np.zeros(
        (len(target), train_physics.shape[1], train_physics.shape[2]),
        dtype=np.float32,
    )
    output_valid = np.zeros((len(target), train_physics.shape[1]), dtype=bool)
    output_gate = np.zeros(len(target), dtype=np.float32)
    donor_ids: list[str] = []
    train_strata: dict[tuple[str, ...], list[int]] = {}
    for index in range(len(train)):
        train_strata.setdefault(
            _sample_stratum(
                train,
                index,
                include_split=False,
                quic_expert_ready=quic_expert_ready,
            ),
            [],
        ).append(index)
    rng = np.random.Generator(np.random.PCG64(_seed(RANDOM_NAMESPACE, seed, target.name)))
    for target_index in range(len(target)):
        key = _sample_stratum(
            target,
            target_index,
            include_split=False,
            quic_expert_ready=quic_expert_ready,
        )
        donors = train_strata.get(key)
        if not donors:
            raise R2FinalViewError(f"F-R 开发训练池缺少分层：{key}")
        pattern_index = donors[int(rng.integers(0, len(donors)))]
        donor_ids.append(train.sample_ids[pattern_index])
        output_valid[target_index] = train.valid_masks[pattern_index]
        output_gate[target_index] = train.route_confidences[pattern_index]
        for window_index in range(train_physics.shape[1]):
            if not output_valid[target_index, window_index]:
                continue
            eligible = [
                index
                for index in donors
                if train.valid_masks[index, window_index]
            ]
            if not eligible:
                raise R2FinalViewError(
                    f"F-R 分层 {key} 的窗口 {window_index} 无有效训练值池"
                )
            for field_index in range(train_physics.shape[2]):
                value_donor = eligible[int(rng.integers(0, len(eligible)))]
                output[target_index, window_index, field_index] = train_physics[
                    value_donor,
                    window_index,
                    field_index,
                ]
    return output, output_valid, output_gate, tuple(donor_ids)


def _variant_split(
    *,
    variant: str,
    split: BaseSplit,
    train: BaseSplit,
    unified_sequence: np.ndarray,
    physics_sequence: np.ndarray,
    train_physics_sequence: np.ndarray,
    representation_dimension: int,
    seed: int,
    quic_expert_ready: bool,
) -> VariantSplit:
    expected_prefix = split.histories.shape[:2]
    for description, sequence in (
        ("统一分支", unified_sequence),
        ("物理分支", physics_sequence),
    ):
        if sequence.shape != (*expected_prefix, representation_dimension):
            raise R2FinalViewError(
                f"{split.name} {description}输出形状必须为 "
                f"{(*expected_prefix, representation_dimension)}"
            )
        if not np.isfinite(sequence).all():
            raise R2FinalViewError(f"{split.name} {description}输出包含非有限值")
    donor_ids: tuple[str | None, ...] = tuple(None for _ in range(len(split)))
    if variant == "F-A":
        sidecar = unified_sequence
        valid = split.valid_masks
        gate = np.ones(len(split), dtype=np.float32)
    elif variant == "F-H":
        sidecar = _pad_raw_history(split.histories, representation_dimension)
        valid = split.valid_masks
        gate = np.ones(len(split), dtype=np.float32)
    elif variant == "F-P":
        sidecar = physics_sequence
        valid = split.valid_masks
        gate = split.route_confidences
    elif variant == "F-S":
        donors, donor_values = _shuffle_indices(
            split,
            seed,
            quic_expert_ready=quic_expert_ready,
        )
        sidecar = physics_sequence[donors]
        valid = split.valid_masks[donors]
        gate = split.route_confidences[donors]
        donor_ids = donor_values
    elif variant == "F-R":
        sidecar, valid, gate, random_donors = _random_sidecar(
            split,
            train,
            train_physics_sequence,
            seed,
            quic_expert_ready=quic_expert_ready,
        )
        donor_ids = random_donors
    else:
        raise R2FinalViewError(f"未知最终 R2 组别：{variant}")
    sidecar = np.asarray(sidecar, dtype=np.float32)
    valid = np.asarray(valid, dtype=bool)
    gate = np.asarray(gate, dtype=np.float32)
    sidecar[~valid] = 0.0
    if np.any((gate < 0) | (gate > 1)) or not np.isfinite(gate).all():
        raise R2FinalViewError(f"{split.name} {variant} 融合门不在 [0,1]")
    return VariantSplit(
        name=split.name,
        sample_ids=split.sample_ids,
        stable_orders=split.stable_orders,
        texts=split.texts,
        labels=split.labels,
        sidecar_sequence=_freeze_array(sidecar, f"{split.name} {variant} 旁路"),
        sidecar_valid_mask=_freeze_array(valid, f"{split.name} {variant} 有效窗口"),
        sidecar_gate=_freeze_array(gate, f"{split.name} {variant} 融合门"),
        donor_sample_ids=donor_ids,
    )


def build_variant_views(
    base: PreparedBaseViews,
    *,
    variant: str,
    seed: int,
    unified_sequences: Mapping[str, BoundSequence],
    physics_sequences: Mapping[str, BoundSequence],
    representation_dimension: int,
    quic_expert_ready: bool,
) -> PreparedVariantViews:
    """只构造请求的一个 F 组，禁止同进程循环多个组。"""

    if variant not in VARIANTS:
        raise R2FinalViewError(f"variant 必须属于 {VARIANTS}")
    if seed not in (42, 43, 44):
        raise R2FinalViewError("最终 R2 只允许种子 42、43、44")
    required = set(ALLOWED_SPLITS)
    if set(unified_sequences) != required or set(physics_sequences) != required:
        raise R2FinalViewError("统一与物理序列必须精确覆盖三个开发划分")
    split_values = {
        "train-fit": base.train,
        "calibration": base.calibration,
        "validation": base.validation,
    }
    capacity_receipt: dict[str, object] = {}
    for name, split in split_values.items():
        unified = unified_sequences[name]
        physics = physics_sequences[name]
        for description, bound in (("统一", unified), ("物理", physics)):
            if bound.sample_ids != split.sample_ids:
                raise R2FinalViewError(f"{name} {description}序列 sample_id 顺序不一致")
            if not np.array_equal(bound.stable_orders, split.stable_orders):
                raise R2FinalViewError(f"{name} {description}序列 stable_order 不一致")
            if bound.values.shape != (
                len(split),
                split.histories.shape[1],
                representation_dimension,
            ):
                raise R2FinalViewError(f"{name} {description}序列形状不一致")
            if not bound.checkpoint_sha256 or not bound.production_sha256:
                raise R2FinalViewError(f"{name} {description}序列缺少生产绑定哈希")
            if bound.parameter_count <= 0:
                raise R2FinalViewError(f"{name} {description}序列参数量必须为正")
            if bound.trainable_parameter_count != 0:
                raise R2FinalViewError(f"{name} {description}分类序列仍有可训练物理参数")
            if bound.frozen_parameter_count != bound.parameter_count:
                raise R2FinalViewError(f"{name} {description}冻结参数收据不完整")
            if bound.checkpoint_trainable_parameter_count != bound.parameter_count:
                raise R2FinalViewError(f"{name} {description}预训练参数未全部受训练")
            if bound.checkpoint_frozen_parameter_count != 0:
                raise R2FinalViewError(f"{name} {description}检查点含冻结填充参数")
            if not bound.checkpoint_binding_sha256:
                raise R2FinalViewError(f"{name} {description}缺少检查点绑定摘要")
            if bound.quic_expert_ready is not quic_expert_ready:
                raise R2FinalViewError(f"{name} {description}序列的 QUIC 就绪状态不一致")
        if unified.checkpoint_sha256 != physics.checkpoint_sha256:
            raise R2FinalViewError(f"{name} F-A/F-P 必须来自同一物理检查点")
        if unified.parameter_count != physics.parameter_count:
            raise R2FinalViewError(f"{name} F-A/F-P 参数容量不一致")
        if unified.branch_name != "unified_control":
            raise R2FinalViewError(f"{name} F-A 未绑定已训练统一控制支路")
        if physics.branch_name != "routed_active":
            raise R2FinalViewError(f"{name} F-P 未绑定已训练路由活跃支路")
        if unified.checkpoint_binding_sha256 != physics.checkpoint_binding_sha256:
            raise R2FinalViewError(f"{name} F-A/F-P 检查点绑定摘要不一致")
        capacity_receipt[name] = {
            "checkpoint_sha256": unified.checkpoint_sha256,
            "parameter_count": unified.parameter_count,
            "classification_trainable": unified.trainable_parameter_count,
            "classification_frozen": unified.frozen_parameter_count,
            "checkpoint_trainable": unified.checkpoint_trainable_parameter_count,
            "checkpoint_frozen": unified.checkpoint_frozen_parameter_count,
            "checkpoint_binding_sha256": unified.checkpoint_binding_sha256,
            "unified_production_sha256": unified.production_sha256,
            "physics_production_sha256": physics.production_sha256,
        }
    built = {
        name: _variant_split(
            variant=variant,
            split=split,
            train=base.train,
            unified_sequence=unified_sequences[name].values,
            physics_sequence=physics_sequences[name].values,
            train_physics_sequence=physics_sequences["train-fit"].values,
            representation_dimension=representation_dimension,
            seed=seed,
            quic_expert_ready=quic_expert_ready,
        )
        for name, split in split_values.items()
    }
    reference = {
        name: {
            "sample_order_sha256": strings_sha256(split.sample_ids),
            "labels_sha256": array_sha256(split.labels),
            "text_sha256": strings_sha256(split.texts),
        }
        for name, split in split_values.items()
    }
    binding = {
        "variant": variant,
        "seed": seed,
        "representation_dimension": representation_dimension,
        "base_binding": dict(base.binding),
        "shared_inputs": reference,
        "variant_tensors": {
            name: {
                "sidecar_sha256": array_sha256(split.sidecar_sequence),
                "valid_sha256": array_sha256(split.sidecar_valid_mask),
                "gate_sha256": array_sha256(split.sidecar_gate),
            }
            for name, split in built.items()
        },
        "random_namespace": RANDOM_NAMESPACE if variant == "F-R" else None,
        "shuffle_namespace": SHUFFLE_NAMESPACE if variant == "F-S" else None,
        "classification_protocol_fields_visible": False,
        "final_test_visible": False,
        "quic_expert_ready": quic_expert_ready,
        "capacity_receipt": capacity_receipt,
    }
    return PreparedVariantViews(
        variant=variant,
        train=built["train-fit"],
        calibration=built["calibration"],
        validation=built["validation"],
        binding=binding,
    )
