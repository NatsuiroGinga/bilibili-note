"""LSPR24 G0-D 开发区 HGB/XGBoost 共享输入适配器。"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import platform
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import sklearn
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import f1_score
from sklearn.utils.class_weight import compute_sample_weight

from flow_probe.frozen_protocol import FrozenProtocol, SplitManifest, TabularSplit
from flow_probe.tabular_baselines import (
    PreparedTabularData,
    SUPPORTED_MODELS,
    run_prepared_tabular_baseline_suite,
)


G0_D_CONTRACT_VERSION = "lspr24-g0-v4-staged"
DEVELOPMENT_SPLITS = (
    "train-fit",
    "architecture-selection",
    "dev-validation",
    "calibration",
)
ALLOWED_HISTORY_LENGTHS = frozenset((1, 4, 16, 32))
ALLOWED_SEMANTICS = frozenset(
    (
        "traffic-volume",
        "directional-behavior",
        "flow-completion-statistics",
        "coarse-protocol-connection-state",
        "quality-information",
        "explicit-missingness-mask",
    )
)
FORBIDDEN_PATH_PARTS = (
    "final-test",
    "sealed",
    "final-test-features",
    "final-test-labels",
    "final-test-row-selection",
    "<lspr24_g0_sealed_root>",
)
REQUIRED_ARTIFACTS = MappingProxyType(
    {
        "development_windows": "开发窗口",
        "history_samples": "历史样本",
        "field_manifest": "字段清单",
        "field_lineage": "字段谱系收据",
        "evaluation_clusters": "评价簇清单",
        "history_invariants": "历史不变量收据",
    }
)
HISTORY_COLUMNS = (
    "sample_id",
    "stable_order",
    "split_name",
    "history_length",
    "history_window_ids",
    "protected_endpoint_id",
    "segment_id",
    "history_endpoint_ids",
    "history_segment_ids",
    "history_split_names",
    "history_stable_orders",
)


class Lspr24G0TabularAdapterError(ValueError):
    """LSPR24 G0-D 表格数据适配输入不满足隔离合同。"""


@dataclass(frozen=True)
class Lspr24G0PreparedTabularData:
    """已验证的四段开发区树模型输入及共享绑定哈希。"""

    by_history_length: Mapping[int, PreparedTabularData]
    model_inputs: Mapping[str, Mapping[int, PreparedTabularData]]
    shared_hashes: Mapping[str, str]
    fair_budget_plan: Mapping[str, object]
    data_binding: Mapping[str, object]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def _array_sha256(values: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("ascii"))
    digest.update(json.dumps(contiguous.shape, separators=(",", ":")).encode("ascii"))
    digest.update(contiguous.tobytes(order="C"))
    return digest.hexdigest()


def _json_safe(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(_json_safe(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path, description: str) -> dict[str, object]:
    if not path.is_file():
        raise Lspr24G0TabularAdapterError(f"缺少{description}：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Lspr24G0TabularAdapterError(f"无法读取{description}：{path}") from error
    if not isinstance(value, dict):
        raise Lspr24G0TabularAdapterError(f"{description}顶层必须是对象")
    return value


def _require_mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Lspr24G0TabularAdapterError(f"{description}必须是对象")
    return value


def _expected_sha256(value: object, description: str) -> str:
    digest = str(value).strip()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise Lspr24G0TabularAdapterError(f"{description}必须是小写 SHA-256")
    return digest


def _reject_sealed_path(path: Path, description: str) -> None:
    lowered = str(path).replace("\\", "/").lower()
    if any(part in lowered for part in FORBIDDEN_PATH_PARTS):
        raise Lspr24G0TabularAdapterError(f"{description}不得指向最终区或封存区：{path}")


def _registered_path(root: Path, relative_path: object, description: str) -> Path:
    raw_path = str(relative_path).strip()
    if not raw_path:
        raise Lspr24G0TabularAdapterError(f"{description}缺少登记路径")
    path = (root / raw_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise Lspr24G0TabularAdapterError(f"{description}越过 G0-D 运行根：{raw_path}") from error
    _reject_sealed_path(path, description)
    if not path.is_file():
        raise Lspr24G0TabularAdapterError(f"缺少{description}：{path}")
    return path


def _load_artifact_paths(
    root: Path, semantic: Mapping[str, object]
) -> tuple[dict[str, Path], dict[str, str]]:
    artifacts = _require_mapping(semantic.get("artifacts"), "语义哈希收据 artifacts")
    paths: dict[str, Path] = {}
    expected_hashes: dict[str, str] = {}
    for name, description in REQUIRED_ARTIFACTS.items():
        entry = _require_mapping(artifacts.get(name), f"语义哈希收据制品 {name}")
        paths[name] = _registered_path(root, entry.get("path"), description)
        expected_hashes[name] = _expected_sha256(entry.get("sha256"), f"{description}登记哈希")
    for name, path in paths.items():
        actual_digest = _sha256(path)
        if actual_digest != expected_hashes[name]:
            raise Lspr24G0TabularAdapterError(
                f"{REQUIRED_ARTIFACTS[name]}哈希不匹配：{actual_digest} != {expected_hashes[name]}"
            )
    return paths, expected_hashes


def _validate_decision(decision: Mapping[str, object]) -> None:
    if decision.get("phase") != "G0-D":
        raise Lspr24G0TabularAdapterError("G0 决策收据未处于 G0-D")
    if decision.get("development_baseline_release") is not True:
        raise Lspr24G0TabularAdapterError("G0-D 未放行开发区表格基线")
    if decision.get("phase_assignment") != "G0-F":
        raise Lspr24G0TabularAdapterError("最终区阶段分配必须保持 G0-F")
    if decision.get("final_status") != "NOT_READY" or decision.get("G0-A12") != "NOT_READY":
        raise Lspr24G0TabularAdapterError("最终区状态必须保持 NOT_READY")
    for key in (
        "final_feature_artifacts",
        "final_label_artifacts",
        "final_row_selection_artifacts",
        "final_member_artifacts",
        "final_specific_statistics",
    ):
        if decision.get(key) != []:
            raise Lspr24G0TabularAdapterError(f"G0-D 决策收据的 {key} 必须为空数组")


def _forbidden_field(name: str) -> bool:
    normalized = name.strip().lower().replace("_", "").replace(" ", "")
    return (
        normalized.startswith("label")
        or "ip" in normalized
        or "port" in normalized
        or normalized in {"sampleid", "windowid", "segmentid", "protectedendpointid"}
        or "evaluationcluster" in normalized
        or "time" in normalized
        or "flowid" in normalized
        or normalized == "service"
        or "split" in normalized
        or "path" in normalized
        or "ids" in normalized
    )


def _load_field_order(path: Path) -> tuple[str, ...]:
    manifest = _read_json(path, "字段清单")
    if manifest.get("contract_version") != G0_D_CONTRACT_VERSION:
        raise Lspr24G0TabularAdapterError("字段清单合同版本不匹配")
    raw_fields = manifest.get("fields")
    if not isinstance(raw_fields, list) or not raw_fields:
        raise Lspr24G0TabularAdapterError("字段清单 fields 必须是非空数组")
    fields: list[str] = []
    for index, raw_field in enumerate(raw_fields):
        field = _require_mapping(raw_field, f"字段清单 fields[{index}]")
        name = str(field.get("output_name", "")).strip()
        semantic = str(field.get("semantic", "")).strip()
        if not name or _forbidden_field(name):
            raise Lspr24G0TabularAdapterError(f"字段清单包含禁入字段：{name or index}")
        if semantic not in ALLOWED_SEMANTICS:
            raise Lspr24G0TabularAdapterError(f"字段 {name} 的语义不在允许范围：{semantic}")
        if name in fields:
            raise Lspr24G0TabularAdapterError(f"字段清单 output_name 重复：{name}")
        fields.append(name)
    return tuple(fields)


def _validate_field_lineage(
    path: Path, field_manifest_path: Path, field_order: tuple[str, ...]
) -> None:
    receipt = _read_json(path, "字段谱系收据")
    if receipt.get("contract_version") != G0_D_CONTRACT_VERSION:
        raise Lspr24G0TabularAdapterError("字段谱系收据合同版本不匹配")
    if receipt.get("field_manifest_sha256") != _sha256(field_manifest_path):
        raise Lspr24G0TabularAdapterError("字段谱系收据未绑定当前字段清单")
    raw_fields = receipt.get("fields")
    if not isinstance(raw_fields, list):
        raise Lspr24G0TabularAdapterError("字段谱系收据 fields 必须是数组")
    lineage_names: list[str] = []
    for index, raw_field in enumerate(raw_fields):
        field = _require_mapping(raw_field, f"字段谱系 fields[{index}]")
        name = str(field.get("output_name", "")).strip()
        ancestors = field.get("recursive_ancestors")
        if not isinstance(ancestors, list) or not ancestors:
            raise Lspr24G0TabularAdapterError(f"字段 {name or index} 缺少递归祖先")
        for ancestor in ancestors:
            ancestor_name = str(ancestor).strip()
            if not ancestor_name or _forbidden_field(ancestor_name):
                raise Lspr24G0TabularAdapterError(
                    f"字段 {name or index} 的谱系命中禁入祖先：{ancestor_name}"
                )
        lineage_names.append(name)
    if tuple(lineage_names) != field_order:
        raise Lspr24G0TabularAdapterError("字段谱系顺序与字段清单不一致")


def _validate_history_receipt(path: Path, history_path: Path) -> None:
    receipt = _read_json(path, "历史不变量收据")
    if receipt.get("contract_version") != G0_D_CONTRACT_VERSION:
        raise Lspr24G0TabularAdapterError("历史不变量收据合同版本不匹配")
    if receipt.get("history_samples_sha256") != _sha256(history_path):
        raise Lspr24G0TabularAdapterError("历史不变量收据未绑定当前历史样本")
    for key in ("same_endpoint", "same_contiguous_segment", "same_partition", "old_to_new"):
        if receipt.get(key) is not True:
            raise Lspr24G0TabularAdapterError(f"历史不变量收据未证明 {key}")


def _parquet_columns(path: Path, description: str) -> tuple[str, ...]:
    try:
        return tuple(pq.ParquetFile(path).schema_arrow.names)
    except Exception as error:
        raise Lspr24G0TabularAdapterError(f"无法读取{description}全模式：{path}") from error


def _validate_window_schema(path: Path, field_order: tuple[str, ...]) -> None:
    actual = _parquet_columns(path, "开发窗口")
    expected = ("window_id", *field_order)
    if actual != expected:
        raise Lspr24G0TabularAdapterError(
            f"开发窗口全模式必须严格等于 window_id 加字段清单：{actual} != {expected}"
        )


def _stable_order_rows(frame: pd.DataFrame, description: str) -> tuple[tuple[str, int], ...]:
    required = {"sample_id", "stable_order"}
    if not required.issubset(frame.columns):
        raise Lspr24G0TabularAdapterError(f"{description}缺少样本绑定列")
    rows: list[tuple[str, int]] = []
    sample_ids: list[str] = []
    for sample_id, stable_order in zip(
        frame["sample_id"].tolist(), frame["stable_order"].tolist(), strict=True
    ):
        if not isinstance(sample_id, str) or not sample_id or sample_id.strip() != sample_id:
            raise Lspr24G0TabularAdapterError(f"{description} sample_id 必须是非空字符串")
        if isinstance(stable_order, bool) or not isinstance(stable_order, (int, np.integer)):
            raise Lspr24G0TabularAdapterError(f"{description} stable_order 必须是整数")
        sample_ids.append(sample_id)
        rows.append((sample_id, int(stable_order)))
    if len(sample_ids) != len(set(sample_ids)):
        raise Lspr24G0TabularAdapterError(f"{description}包含重复 sample_id")
    if len(rows) != len(set(rows)):
        raise Lspr24G0TabularAdapterError(f"{description}的 (sample_id, stable_order) 不得重复")
    return tuple(rows)


def _sample_order_sha256(rows: Sequence[tuple[str, int]]) -> str:
    return _canonical_sha256(
        [{"sample_id": sample_id, "stable_order": stable_order} for sample_id, stable_order in rows]
    )


def _parse_list(value: object, expected_length: int, description: str) -> list[object]:
    try:
        decoded = json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError as error:
        raise Lspr24G0TabularAdapterError(f"{description}不是合法 JSON") from error
    if not isinstance(decoded, list) or len(decoded) != expected_length:
        raise Lspr24G0TabularAdapterError(f"{description}长度不等于 H")
    return decoded


def _parse_history_ids(value: object, history_length: int, sample_id: str) -> tuple[str, ...]:
    decoded = _parse_list(value, history_length, f"样本 {sample_id} 的历史窗口列表")
    window_ids = tuple(str(item).strip() for item in decoded)
    if not all(window_ids) or len(window_ids) != len(set(window_ids)):
        raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的历史窗口标识不合法")
    return window_ids


def _validate_history_rows(history: pd.DataFrame) -> None:
    missing = sorted(set(HISTORY_COLUMNS).difference(history.columns))
    if missing:
        raise Lspr24G0TabularAdapterError(f"历史样本缺少不变量列：{', '.join(missing)}")
    for row in history.to_dict(orient="records"):
        sample_id = str(row["sample_id"])
        raw_length = row["history_length"]
        if isinstance(raw_length, bool) or not isinstance(raw_length, (int, np.integer)):
            raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的 history_length 必须是整数")
        history_length = int(raw_length)
        if history_length not in ALLOWED_HISTORY_LENGTHS:
            raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的历史长度不受支持")
        _parse_history_ids(row["history_window_ids"], history_length, sample_id)
        endpoints = [
            str(value)
            for value in _parse_list(
                row["history_endpoint_ids"], history_length, f"样本 {sample_id} 的端点列表"
            )
        ]
        segments = [
            str(value)
            for value in _parse_list(
                row["history_segment_ids"], history_length, f"样本 {sample_id} 的连续段列表"
            )
        ]
        splits = [
            str(value)
            for value in _parse_list(
                row["history_split_names"], history_length, f"样本 {sample_id} 的分区列表"
            )
        ]
        raw_orders = _parse_list(
            row["history_stable_orders"], history_length, f"样本 {sample_id} 的历史顺序"
        )
        if any(value != str(row["protected_endpoint_id"]) for value in endpoints):
            raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的历史窗口不是同端点")
        if any(value != str(row["segment_id"]) for value in segments):
            raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的历史窗口不是同连续段")
        if any(value != str(row["split_name"]) for value in splits):
            raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的历史窗口不是同分区")
        if any(isinstance(value, bool) or not isinstance(value, (int, np.integer)) for value in raw_orders):
            raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的历史顺序必须是整数")
        orders = [int(value) for value in raw_orders]
        if any(previous >= current for previous, current in zip(orders, orders[1:])):
            raise Lspr24G0TabularAdapterError(f"样本 {sample_id} 的历史窗口未按旧到新排列")


def _tabular_split(
    *,
    split_name: str,
    sample_ids: tuple[str, ...],
    features: np.ndarray,
    labels: tuple[str, ...],
    feature_fields: tuple[str, ...],
    suite_id: str,
) -> TabularSplit:
    order_sha = _canonical_sha256(list(sample_ids))
    manifest = SplitManifest(
        relative_path=f"g0-d/{split_name}.jsonl",
        protocol_version=G0_D_CONTRACT_VERSION,
        suite_id=suite_id,
        split_id="train" if split_name == "train-fit" else "development",
        sample_ids=sample_ids,
        sha256=_canonical_sha256({"split": split_name, "sample_order_sha256": order_sha}),
        samples_sha256=order_sha,
        sample_order_sha256=order_sha,
    )
    features.setflags(write=False)
    return TabularSplit(
        manifest=manifest,
        sample_ids=sample_ids,
        features=features,
        labels=labels,
        feature_fields=feature_fields,
        label_field="development_sidecar_label",
    )


def _protocol(root: Path, field_order: tuple[str, ...], binding_sha: str) -> FrozenProtocol:
    return FrozenProtocol(
        root=root,
        protocol_version=G0_D_CONTRACT_VERSION,
        status="development-released",
        phase="G0-D",
        protocol_sha256=binding_sha,
        samples_sha256=binding_sha,
        field_roles_sha256=_canonical_sha256(list(field_order)),
        artifact_hashes=MappingProxyType({}),
        field_roles=MappingProxyType({}),
        model_views=MappingProxyType({}),
        manifests=MappingProxyType({}),
        _samples=pd.DataFrame(),
    )


def prepare_lspr24_g0_tabular_data(
    *,
    g0_run_root: Path,
    restricted_root: Path,
    output_dir: Path,
    history_lengths: Sequence[int] = (1, 4, 16, 32),
    model_keys: Sequence[str] = SUPPORTED_MODELS,
) -> Lspr24G0PreparedTabularData:
    """拒绝最终区后，从 G0-D 开发制品构造共享且只读的 H×F 输入。"""
    root = Path(g0_run_root).resolve()
    restricted = Path(restricted_root).resolve()
    output = Path(output_dir).resolve()
    _reject_sealed_path(root, "G0-D 运行根")
    _reject_sealed_path(restricted, "开发标签受限根")
    _reject_sealed_path(output, "输出目录")
    if output.exists():
        raise Lspr24G0TabularAdapterError(f"输出目录已存在，不得复用：{output}")
    if not root.is_dir() or not restricted.is_dir():
        raise Lspr24G0TabularAdapterError("G0-D 运行根和开发标签受限根必须存在")
    requested_lengths = tuple(int(value) for value in history_lengths)
    if not requested_lengths or len(requested_lengths) != len(set(requested_lengths)):
        raise Lspr24G0TabularAdapterError("历史长度必须非空且不得重复")
    if not set(requested_lengths).issubset(ALLOWED_HISTORY_LENGTHS):
        raise Lspr24G0TabularAdapterError("历史长度只允许 1、4、16、32")
    keys = tuple(str(key).strip() for key in model_keys)
    if set(keys) != {"hgb", "xgboost"} or len(keys) != 2:
        raise Lspr24G0TabularAdapterError("LSPR24 入口必须同时使用且只使用 hgb、xgboost")

    decision_path = _registered_path(root, "receipts/g0-a-decision.json", "G0-D 决策收据")
    decision = _read_json(decision_path, "G0-D 决策收据")
    _validate_decision(decision)
    semantic_path = _registered_path(root, "receipts/semantic-hashes.json", "语义哈希收据")
    semantic = _read_json(semantic_path, "语义哈希收据")
    if semantic.get("contract_version") != G0_D_CONTRACT_VERSION:
        raise Lspr24G0TabularAdapterError("语义哈希收据合同版本不匹配")
    artifact_paths, artifact_hashes = _load_artifact_paths(root, semantic)
    field_path = artifact_paths["field_manifest"]
    windows_path = artifact_paths["development_windows"]
    history_path = artifact_paths["history_samples"]
    clusters_path = artifact_paths["evaluation_clusters"]
    lineage_path = artifact_paths["field_lineage"]
    history_receipt_path = artifact_paths["history_invariants"]
    field_order = _load_field_order(field_path)
    _validate_field_lineage(lineage_path, field_path, field_order)
    _validate_history_receipt(history_receipt_path, history_path)
    _validate_window_schema(windows_path, field_order)

    labels_path = (restricted / "development-labels.parquet").resolve()
    _reject_sealed_path(labels_path, "开发标签侧车")
    if not labels_path.is_file():
        raise Lspr24G0TabularAdapterError(f"缺少开发标签侧车：{labels_path}")
    sidecar_receipt_path = restricted / "development-labels-receipt.json"
    sidecar_receipt = _read_json(sidecar_receipt_path, "开发标签侧车收据")
    if sidecar_receipt.get("router_version") != "lspr24-dev-router-v1":
        raise Lspr24G0TabularAdapterError("开发标签侧车路由器版本不匹配")
    if sidecar_receipt.get("sidecar_sha256") != _sha256(labels_path):
        raise Lspr24G0TabularAdapterError("开发标签侧车哈希不匹配")
    if sidecar_receipt.get("g0_d_decision_sha256") != _sha256(decision_path):
        raise Lspr24G0TabularAdapterError("开发标签侧车未绑定当前 G0-D 决策收据")

    history = pd.read_parquet(history_path, columns=list(HISTORY_COLUMNS))
    history_order = _stable_order_rows(history, "历史样本")
    _validate_history_rows(history)
    if sidecar_receipt.get("sample_order_sha256") != _sample_order_sha256(history_order):
        raise Lspr24G0TabularAdapterError("开发标签侧车样本顺序哈希不匹配")
    labels = pd.read_parquet(labels_path, columns=["sample_id", "stable_order", "label"])
    label_order = _stable_order_rows(labels, "开发标签侧车")
    if not bool(labels["label"].isin([0, 1]).all()):
        raise Lspr24G0TabularAdapterError("开发标签侧车标签只能为 0 或 1")
    clusters = pd.read_parquet(clusters_path, columns=["sample_id", "stable_order"])
    cluster_order = _stable_order_rows(clusters, "评价簇清单")
    if label_order != history_order:
        raise Lspr24G0TabularAdapterError("开发标签侧车未与历史样本逐行一对一绑定")
    if cluster_order != history_order:
        raise Lspr24G0TabularAdapterError("评价簇清单未与历史样本逐行绑定")
    if set(history["split_name"].tolist()) != set(DEVELOPMENT_SPLITS):
        raise Lspr24G0TabularAdapterError("历史样本必须且只能包含四段开发区")
    if (history["split_name"] == "final-test").any():
        raise Lspr24G0TabularAdapterError("历史样本不得包含 final-test")

    windows = pd.read_parquet(windows_path, columns=["window_id", *field_order])
    if windows["window_id"].duplicated().any():
        raise Lspr24G0TabularAdapterError("开发窗口 window_id 不得重复")
    for field in field_order:
        if not pd.api.types.is_numeric_dtype(windows[field].dtype):
            raise Lspr24G0TabularAdapterError(f"开发窗口字段必须为数值：{field}")
    window_features = {
        str(row["window_id"]): np.asarray([row[field] for field in field_order], dtype=np.float64)
        for _, row in windows.iterrows()
    }
    if any(np.isinf(values).any() for values in window_features.values()):
        raise Lspr24G0TabularAdapterError("开发窗口特征不得包含无穷值")
    labels_by_sample = {
        str(row["sample_id"]): "malicious" if int(row["label"]) == 1 else "benign"
        for _, row in labels.iterrows()
    }

    binding_sha = _canonical_sha256(
        {
            "decision": _sha256(decision_path),
            "semantic": _sha256(semantic_path),
            "artifacts": artifact_hashes,
            "labels": _sha256(labels_path),
        }
    )
    protocol = _protocol(root, field_order, binding_sha)
    by_history_length: dict[int, PreparedTabularData] = {}
    all_matrix_hashes: dict[str, str] = {}
    for history_length in requested_lengths:
        subset = history.loc[history["history_length"] == history_length].copy()
        if subset.empty:
            raise Lspr24G0TabularAdapterError(f"缺少 H={history_length} 的历史样本")
        subset = subset.sort_values("stable_order", kind="stable")
        split_data: dict[str, TabularSplit] = {}
        for split_name in DEVELOPMENT_SPLITS:
            split_rows = subset.loc[subset["split_name"] == split_name]
            if split_rows.empty:
                raise Lspr24G0TabularAdapterError(f"H={history_length} 缺少分区：{split_name}")
            sample_ids = tuple(str(value) for value in split_rows["sample_id"].tolist())
            vectors: list[np.ndarray] = []
            for row in split_rows.to_dict(orient="records"):
                sample_id = str(row["sample_id"])
                window_ids = _parse_history_ids(row["history_window_ids"], history_length, sample_id)
                try:
                    vectors.append(np.concatenate([window_features[window_id] for window_id in window_ids]))
                except KeyError as error:
                    raise Lspr24G0TabularAdapterError(
                        f"样本 {sample_id} 引用未登记的开发窗口：{error.args[0]}"
                    ) from error
            features = np.asarray(vectors, dtype=np.float64)
            if features.shape[1] != history_length * len(field_order):
                raise Lspr24G0TabularAdapterError("树模型输入不是 H×F 展平向量")
            split_data[split_name] = _tabular_split(
                split_name=split_name,
                sample_ids=sample_ids,
                features=features,
                labels=tuple(labels_by_sample[sample_id] for sample_id in sample_ids),
                feature_fields=tuple(
                    f"t{step}_{field}" for step in range(history_length) for field in field_order
                ),
                suite_id="lspr24-g0-d-development",
            )
            all_matrix_hashes[f"H{history_length}:{split_name}"] = _array_sha256(features)
        train = split_data["train-fit"]
        known_labels = ("benign", "malicious")
        encoded = np.asarray([known_labels.index(label) for label in train.labels], dtype=np.int64)
        weights = np.asarray(compute_sample_weight(class_weight="balanced", y=encoded), dtype=np.float64)
        encoded.setflags(write=False)
        weights.setflags(write=False)
        by_history_length[history_length] = PreparedTabularData(
            protocol=protocol,
            view_name="lspr24_g0_hxf_development",
            train=train,
            evaluations=MappingProxyType(
                {name: split_data[name] for name in DEVELOPMENT_SPLITS[1:]}
            ),
            known_labels=known_labels,
            encoded_train_labels=encoded,
            train_sample_weights=weights,
            feature_matrix_sha256=_array_sha256(train.features),
            train_labels_sha256=_canonical_sha256(list(train.labels)),
        )

    shared_hashes = MappingProxyType(
        {
            "field_order_sha256": _canonical_sha256(list(field_order)),
            "field_lineage_sha256": artifact_hashes["field_lineage"],
            "history_invariants_sha256": artifact_hashes["history_invariants"],
            "sample_order_sha256": _sample_order_sha256(history_order),
            "feature_matrix_sha256": _canonical_sha256(all_matrix_hashes),
            "label_binding_sha256": _sha256(labels_path),
            "binding_sha256": binding_sha,
        }
    )
    attempts = [
        {
            "model": model_key,
            "configuration_id": f"default-h{history_length}",
            "history_length": history_length,
            "fit_count": 1,
            "evaluation_count": 1,
            "evaluation_split": "architecture-selection",
            "shared_hashes": dict(shared_hashes),
        }
        for model_key in keys
        for history_length in requested_lengths
    ]
    fair_budget_plan = MappingProxyType(
        {
            "maximum_configurations_per_model": 12,
            "attempts": attempts,
            "status": "frozen-before-execution",
        }
    )
    data_binding = MappingProxyType(
        {
            "contract_version": G0_D_CONTRACT_VERSION,
            "g0_d_decision_sha256": _sha256(decision_path),
            "semantic_hashes_sha256": _sha256(semantic_path),
            "paths": {
                **{name: str(path) for name, path in artifact_paths.items()},
                "development_labels": str(labels_path),
            },
            "artifact_hashes": artifact_hashes,
            "shared_hashes": dict(shared_hashes),
        }
    )
    shared_inputs = MappingProxyType(by_history_length)
    return Lspr24G0PreparedTabularData(
        by_history_length=shared_inputs,
        model_inputs=MappingProxyType({model_key: shared_inputs for model_key in keys}),
        shared_hashes=shared_hashes,
        fair_budget_plan=fair_budget_plan,
        data_binding=data_binding,
    )


def _merge_predictions(paths: Sequence[Path], output_path: Path) -> None:
    with gzip.open(output_path, "wt", encoding="utf-8") as destination:
        for path in paths:
            if not path.is_file():
                continue
            with gzip.open(path, "rt", encoding="utf-8") as source:
                for line in source:
                    destination.write(line)


def _artifact_manifest(output_dir: Path, names: Sequence[str]) -> dict[str, object]:
    artifacts: dict[str, object] = {}
    for name in names:
        path = output_dir / name
        artifacts[name] = {"sha256": _sha256(path), "size_bytes": path.stat().st_size}
    return {
        "schema_version": "lspr24-g0-d-tabular-artifacts-v1",
        "artifacts": artifacts,
    }


def _stage_prepared_data(
    prepared: PreparedTabularData, evaluation_name: str
) -> PreparedTabularData:
    try:
        evaluation = prepared.evaluations[evaluation_name]
    except KeyError as error:
        raise Lspr24G0TabularAdapterError(f"缺少状态机分区：{evaluation_name}") from error
    return replace(
        prepared,
        evaluations=MappingProxyType({evaluation_name: evaluation}),
    )


def _selection_score(
    summary: Mapping[str, object], model_keys: Sequence[str]
) -> float:
    models = _require_mapping(summary.get("models"), "架构选择结果 models")
    scores: list[float] = []
    for model_key in model_keys:
        model = _require_mapping(models.get(model_key), f"架构选择模型 {model_key}")
        evaluations = _require_mapping(
            model.get("evaluations"), f"架构选择模型 {model_key} evaluations"
        )
        evaluation = _require_mapping(
            evaluations.get("architecture-selection"),
            f"架构选择模型 {model_key} architecture-selection",
        )
        metrics = _require_mapping(evaluation.get("metrics"), f"架构选择模型 {model_key} metrics")
        raw_score = metrics.get("macro_f1")
        if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float, np.number)):
            raise Lspr24G0TabularAdapterError(f"架构选择模型 {model_key} 缺少数值 macro_f1")
        score = float(raw_score)
        if not np.isfinite(score):
            raise Lspr24G0TabularAdapterError(f"架构选择模型 {model_key} macro_f1 非有限")
        scores.append(score)
    return float(np.mean(scores))


def _fit_calibration(
    predictions_path: Path, model_keys: Sequence[str]
) -> tuple[dict[str, object], dict[str, object]]:
    rows_by_model: dict[str, list[dict[str, object]]] = {model_key: [] for model_key in model_keys}
    with gzip.open(predictions_path, "rt", encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("evaluation") != "calibration":
                raise Lspr24G0TabularAdapterError("校准预测文件包含非 calibration 分区")
            model_key = str(row.get("model", ""))
            if model_key not in rows_by_model:
                raise Lspr24G0TabularAdapterError(f"校准预测包含未请求模型：{model_key}")
            rows_by_model[model_key].append(row)

    calibrators: dict[str, object] = {}
    thresholds: dict[str, object] = {}
    for model_key in model_keys:
        rows = rows_by_model[model_key]
        if not rows:
            raise Lspr24G0TabularAdapterError(f"模型 {model_key} 缺少校准预测")
        truth = np.asarray([1 if row.get("truth") == "malicious" else 0 for row in rows])
        if set(truth.tolist()) != {0, 1}:
            raise Lspr24G0TabularAdapterError(f"模型 {model_key} 的校准分区必须含两个标签")
        probabilities: list[float] = []
        for row in rows:
            probability_mapping = _require_mapping(
                row.get("probabilities"), f"模型 {model_key} 校准概率"
            )
            raw_probability = probability_mapping.get("malicious")
            if isinstance(raw_probability, bool) or not isinstance(
                raw_probability, (int, float, np.number)
            ):
                raise Lspr24G0TabularAdapterError(f"模型 {model_key} 缺少恶意类概率")
            probability = float(raw_probability)
            if not 0.0 <= probability <= 1.0:
                raise Lspr24G0TabularAdapterError(f"模型 {model_key} 的恶意类概率越界")
            probabilities.append(probability)
        raw_probabilities = np.asarray(probabilities, dtype=np.float64)
        calibrator = IsotonicRegression(y_min=0.0, y_max=1.0, increasing=True, out_of_bounds="clip")
        calibrated = np.asarray(calibrator.fit_transform(raw_probabilities, truth), dtype=np.float64)
        threshold_candidates = sorted({0.0, 0.5, 1.0, *calibrated.tolist()})
        scored_thresholds = [
            (
                float(
                    f1_score(
                        truth,
                        (calibrated >= threshold).astype(np.int64),
                        average="macro",
                        zero_division=0,
                    )
                ),
                float(threshold),
            )
            for threshold in threshold_candidates
        ]
        best_score, best_threshold = max(scored_thresholds, key=lambda item: (item[0], item[1]))
        calibrators[model_key] = {
            "method": "isotonic-regression-v1",
            "monotonic_direction": "increasing",
            "x_thresholds": [float(value) for value in calibrator.X_thresholds_.tolist()],
            "y_thresholds": [float(value) for value in calibrator.y_thresholds_.tolist()],
        }
        thresholds[model_key] = {
            "value": best_threshold,
            "selection_metric": "calibration_macro_f1",
            "selection_rule": "maximum_macro_f1_then_highest_threshold",
            "metric_value": best_score,
        }
    return calibrators, thresholds


def run_lspr24_g0_tabular_baselines(
    *,
    g0_run_root: Path,
    restricted_root: Path,
    output_dir: Path,
    model_keys: Sequence[str],
    seed: int,
) -> dict[str, object]:
    """按架构选择、开发验证、校准三阶段状态机执行开发区基线。"""
    keys = tuple(str(key).strip() for key in model_keys)
    prepared = prepare_lspr24_g0_tabular_data(
        g0_run_root=g0_run_root,
        restricted_root=restricted_root,
        output_dir=output_dir,
        model_keys=keys,
    )
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    model_runs = output / "model-runs"
    model_runs.mkdir()
    _write_json(
        output / "config_snapshot.json",
        {
            "seed": seed,
            "model_keys": list(keys),
            "history_lengths": list(prepared.by_history_length),
            "thread_limit": 1,
        },
    )
    _write_json(
        output / "environment.json",
        {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "selected_device": "cpu",
            "execution_thread_limit": 1,
        },
    )
    _write_json(output / "data_binding.json", prepared.data_binding)
    _write_json(output / "fair-budget-plan-receipt.json", prepared.fair_budget_plan)
    (output / "console.log").write_text("开始 LSPR24 G0-D HGB/XGBoost 开发区运行\n", encoding="utf-8")

    architecture_summaries: dict[str, object] = {}
    architecture_costs: dict[str, object] = {}
    fitted_models_by_history: dict[int, dict[str, object]] = {}
    prediction_paths: list[Path] = []
    execution_attempts: list[dict[str, object]] = []
    for history_length, data in prepared.by_history_length.items():
        stage_data = _stage_prepared_data(data, "architecture-selection")
        predictions_path = model_runs / f"h{history_length}-architecture-selection.jsonl.gz"
        fitted_models: dict[str, object] = {}
        result = run_prepared_tabular_baseline_suite(
            prepared=stage_data,
            model_keys=keys,
            seed=seed,
            predictions_path=predictions_path,
            stage="lspr24_g0_d_architecture_selection",
            tuning_trial_index=0,
            model_state_output=fitted_models,
        )
        if set(fitted_models) != set(keys):
            raise Lspr24G0TabularAdapterError(
                f"H={history_length} 未捕获完整的已拟合模型状态"
            )
        architecture_summaries[str(history_length)] = result.summary
        architecture_costs[str(history_length)] = result.cost
        fitted_models_by_history[history_length] = fitted_models
        prediction_paths.append(predictions_path)
        execution_attempts.extend(
            {
                "model": model_key,
                "history_length": history_length,
                "fit_count": 1,
                "architecture_selection_evaluation_count": 1,
                "shared_hashes": dict(prepared.shared_hashes),
            }
            for model_key in keys
        )

    candidates = [
        {
            "configuration_id": f"default-h{history_length}",
            "history_length": history_length,
            "primary_score": _selection_score(architecture_summaries[str(history_length)], keys),
        }
        for history_length in prepared.by_history_length
    ]
    selected = min(
        candidates,
        key=lambda candidate: (
            -float(candidate["primary_score"]),
            int(candidate["history_length"]),
            str(candidate["configuration_id"]),
        ),
    )
    selected_candidate = {
        "configuration_id": selected["configuration_id"],
        "history_length": selected["history_length"],
    }
    selected_history_length = int(selected["history_length"])
    architecture_receipt = {
        "schema_version": "lspr24-g0-d-architecture-selection-v1",
        "phase": "architecture-selection",
        "status": "frozen",
        "selection_rule": "maximum_mean_model_macro_f1_then_shortest_history",
        "fair_budget_plan_sha256": _sha256(output / "fair-budget-plan-receipt.json"),
        "candidates": candidates,
        "selected_candidate": selected_candidate,
        "runs": architecture_summaries,
    }
    architecture_path = output / "architecture_selection.json"
    _write_json(architecture_path, architecture_receipt)

    selected_data = prepared.by_history_length[selected_history_length]
    selected_models = fitted_models_by_history[selected_history_length]
    dev_predictions_path = model_runs / f"h{selected_history_length}-dev-validation.jsonl.gz"
    dev_result = run_prepared_tabular_baseline_suite(
        prepared=_stage_prepared_data(selected_data, "dev-validation"),
        model_keys=keys,
        seed=seed,
        predictions_path=dev_predictions_path,
        stage="lspr24_g0_d_dev_validation",
        tuning_trial_index=0,
        fitted_models=selected_models,
    )
    prediction_paths.append(dev_predictions_path)
    execution_attempts.extend(
        {
            "model": model_key,
            "history_length": selected_history_length,
            "fit_count": 0,
            "dev_validation_evaluation_count": 1,
            "architecture_selection_sha256": _sha256(architecture_path),
            "shared_hashes": dict(prepared.shared_hashes),
        }
        for model_key in keys
    )
    dev_receipt = {
        "schema_version": "lspr24-g0-d-dev-validation-v1",
        "phase": "dev-validation",
        "status": "completed",
        "architecture_selection_sha256": _sha256(architecture_path),
        "selected_candidate": selected_candidate,
        "result": dev_result.summary,
        "cost": dev_result.cost,
    }
    dev_path = output / "dev_validation.json"
    _write_json(dev_path, dev_receipt)

    calibration_predictions_path = model_runs / f"h{selected_history_length}-calibration.jsonl.gz"
    calibration_result = run_prepared_tabular_baseline_suite(
        prepared=_stage_prepared_data(selected_data, "calibration"),
        model_keys=keys,
        seed=seed,
        predictions_path=calibration_predictions_path,
        stage="lspr24_g0_d_calibration",
        tuning_trial_index=0,
        fitted_models=selected_models,
    )
    prediction_paths.append(calibration_predictions_path)
    calibrators, thresholds = _fit_calibration(calibration_predictions_path, keys)
    calibration_receipt = {
        "schema_version": "lspr24-g0-d-calibration-v1",
        "phase": "calibration",
        "status": "frozen",
        "architecture_selection_sha256": _sha256(architecture_path),
        "dev_validation_sha256": _sha256(dev_path),
        "selected_candidate": selected_candidate,
        "frozen_calibrators": calibrators,
        "result": calibration_result.summary,
        "cost": calibration_result.cost,
    }
    calibration_path = output / "calibration.json"
    _write_json(calibration_path, calibration_receipt)
    execution_attempts.extend(
        {
            "model": model_key,
            "history_length": selected_history_length,
            "fit_count": 0,
            "calibration_evaluation_count": 1,
            "dev_validation_sha256": _sha256(dev_path),
            "shared_hashes": dict(prepared.shared_hashes),
        }
        for model_key in keys
    )

    _merge_predictions(prediction_paths, output / "predictions.jsonl.gz")
    _write_json(
        output / "fair-budget-execution-receipt.json",
        {"status": "completed", "attempts": execution_attempts},
    )
    _write_json(
        output / "threshold_freeze.json",
        {
            "schema_version": "lspr24-g0-d-threshold-freeze-v1",
            "status": "frozen",
            "calibration_sha256": _sha256(calibration_path),
            "selected_candidate": selected_candidate,
            "frozen_thresholds": thresholds,
        },
    )
    _write_json(
        output / "summary.json",
        {
            "schema_version": "lspr24-g0-d-tabular-summary-v1",
            "selected_candidate": selected_candidate,
            "architecture_selection_sha256": _sha256(architecture_path),
            "dev_validation_sha256": _sha256(dev_path),
            "calibration_sha256": _sha256(calibration_path),
        },
    )
    _write_json(
        output / "cost.json",
        {
            "schema_version": "lspr24-g0-d-tabular-cost-v1",
            "architecture_selection": architecture_costs,
            "dev_validation": dev_result.cost,
            "calibration": calibration_result.cost,
        },
    )
    with (output / "console.log").open("a", encoding="utf-8") as console:
        console.write("LSPR24 G0-D HGB/XGBoost 开发区运行完成\n")
    artifact_names = (
        "config_snapshot.json",
        "environment.json",
        "data_binding.json",
        "fair-budget-plan-receipt.json",
        "fair-budget-execution-receipt.json",
        "architecture_selection.json",
        "dev_validation.json",
        "calibration.json",
        "threshold_freeze.json",
        "summary.json",
        "cost.json",
        "predictions.jsonl.gz",
        "console.log",
    )
    manifest = _artifact_manifest(output, artifact_names)
    _write_json(output / "artifact_manifest.json", manifest)
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行 LSPR24 G0-D HGB/XGBoost 开发区基线")
    parser.add_argument("--g0-run-root", type=Path, required=True)
    parser.add_argument("--restricted-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", action="append", choices=SUPPORTED_MODELS, required=True)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = run_lspr24_g0_tabular_baselines(
        g0_run_root=args.g0_run_root,
        restricted_root=args.restricted_root,
        output_dir=args.output_dir,
        model_keys=args.model,
        seed=args.seed,
    )
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
