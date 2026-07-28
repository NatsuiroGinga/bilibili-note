"""冻结数据协议的只读校验与数值视图加载。"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType

import numpy as np
import pandas as pd
import yaml
from pandas.api.types import is_numeric_dtype

FROZEN_PROTOCOL_VERSION = "data-protocol-v1.0"
CANDIDATE_PROTOCOL_VERSION = "data-protocol-v1.0-rc1"
THEORY_SELECTION_STAGE = "theory_selection"
FINAL_TUNING_STAGE = "final_tuning"
TREE_VIEW_NAME = "tree_flat_view"
ALLOWED_FIELD_ROLES = frozenset(
    {"model_input", "physics_target", "label_target", "split_metadata", "audit_only"}
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class FrozenProtocolError(ValueError):
    """冻结协议缺失、被修改或不满足只读加载契约。"""


@dataclass(frozen=True)
class FieldRole:
    """单个主记录字段的用途和允许进入的模型视图。"""

    name: str
    role: str
    views: tuple[str, ...]


@dataclass(frozen=True)
class ModelView:
    """一个模型可见的有序字段预算。"""

    name: str
    feature_fields: tuple[str, ...]


@dataclass(frozen=True)
class SplitManifest:
    """一个有序划分清单及其冻结哈希。"""

    relative_path: str
    protocol_version: str
    suite_id: str
    split_id: str
    sample_ids: tuple[str, ...]
    sha256: str
    samples_sha256: str
    sample_order_sha256: str


@dataclass(frozen=True)
class TabularSplit:
    """严格按清单顺序加载的只读数值视图。"""

    manifest: SplitManifest
    sample_ids: tuple[str, ...]
    features: np.ndarray
    labels: tuple[str, ...]
    feature_fields: tuple[str, ...]
    label_field: str


@dataclass(frozen=True)
class FrozenProtocol:
    """已经完成制品、字段预算和全部划分校验的协议快照。"""

    root: Path
    protocol_version: str
    status: str
    phase: str
    protocol_sha256: str
    samples_sha256: str
    field_roles_sha256: str
    artifact_hashes: Mapping[str, str]
    field_roles: Mapping[str, FieldRole]
    model_views: Mapping[str, ModelView]
    manifests: Mapping[str, SplitManifest]
    _samples: pd.DataFrame

    def manifest(self, relative_path: str | Path) -> SplitManifest:
        """按协议根目录内的相对路径取得已校验清单。"""
        key = _normalise_relative_path(relative_path)
        try:
            return self.manifests[key]
        except KeyError as error:
            raise FrozenProtocolError(f"划分清单未在冻结协议中登记：{key}") from error

    def load_tabular_split(
        self,
        manifest_path: str | Path,
        *,
        view_name: str = TREE_VIEW_NAME,
        label_field: str = "binary_label",
    ) -> TabularSplit:
        """从主记录中按清单顺序提取一个数值视图，不拟合任何转换。"""
        manifest = self.manifest(manifest_path)
        try:
            view = self.model_views[view_name]
        except KeyError as error:
            raise FrozenProtocolError(f"字段预算未定义模型视图：{view_name}") from error
        try:
            label_role = self.field_roles[label_field]
        except KeyError as error:
            raise FrozenProtocolError(f"字段角色未定义标签字段：{label_field}") from error
        if label_role.role != "label_target":
            raise FrozenProtocolError(
                f"标签字段 {label_field} 的角色必须为 label_target，实际为 {label_role.role}"
            )

        required_columns = [*view.feature_fields, label_field]
        missing_columns = sorted(set(required_columns).difference(self._samples.columns))
        if missing_columns:
            raise FrozenProtocolError(f"samples.parquet 缺少视图字段：{', '.join(missing_columns)}")

        indexed = self._samples.set_index("sample_id", drop=False)
        frame = indexed.loc[list(manifest.sample_ids)]
        labels: list[str] = []
        for sample_id, raw_label in zip(
            manifest.sample_ids, frame[label_field].tolist(), strict=True
        ):
            if pd.isna(raw_label) or not str(raw_label).strip():
                raise FrozenProtocolError(
                    f"清单样本的标签不能为空：{manifest.relative_path}:{sample_id}:{label_field}"
                )
            labels.append(str(raw_label))

        for field in view.feature_fields:
            if not is_numeric_dtype(frame[field].dtype):
                raise FrozenProtocolError(
                    f"数值视图字段必须是 Parquet 数值类型：{field}:{frame[field].dtype}"
                )
        features = np.asarray(frame.loc[:, list(view.feature_fields)], dtype=np.float64)
        if np.isinf(features).any():
            raise FrozenProtocolError(f"数值视图包含无穷值：{manifest.relative_path}:{view_name}")
        features.setflags(write=False)
        return TabularSplit(
            manifest=manifest,
            sample_ids=manifest.sample_ids,
            features=features,
            labels=tuple(labels),
            feature_fields=view.feature_fields,
            label_field=label_field,
        )


def file_sha256(path: Path) -> str:
    """流式计算文件 SHA-256。"""
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sample_order_sha256(sample_ids: Sequence[str]) -> str:
    """计算保留顺序的规范样本清单哈希。"""
    payload = json.dumps(list(sample_ids), ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _normalise_relative_path(path: str | Path) -> str:
    raw = str(path).strip().replace("\\", "/")
    pure_path = PurePosixPath(raw)
    if not raw or pure_path.is_absolute() or ".." in pure_path.parts:
        raise FrozenProtocolError(f"协议制品路径必须是安全相对路径：{path}")
    return pure_path.as_posix()


def _read_yaml_mapping(path: Path, description: str) -> Mapping[str, object]:
    if not path.is_file():
        raise FrozenProtocolError(f"缺少{description}：{path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise FrozenProtocolError(f"{description}不是合法 YAML：{path}") from error
    if not isinstance(value, Mapping):
        raise FrozenProtocolError(f"{description}根节点必须是对象：{path}")
    return value


def _required_string(mapping: Mapping[str, object], key: str, description: str) -> str:
    raw_value = mapping.get(key)
    value = "" if raw_value is None else str(raw_value).strip()
    if not value:
        raise FrozenProtocolError(f"{description}缺少非空字段：{key}")
    return value


def _validate_sha256(value: object, description: str) -> str:
    digest = str(value).strip()
    if _SHA256_PATTERN.fullmatch(digest) is None:
        raise FrozenProtocolError(f"{description}必须是小写 SHA-256：{digest!r}")
    return digest


def _parse_artifact_hashes(protocol: Mapping[str, object]) -> dict[str, str]:
    raw_artifacts = protocol.get("artifacts")
    if not isinstance(raw_artifacts, Mapping):
        raise FrozenProtocolError("protocol.yaml 缺少 artifacts 制品哈希表")
    artifacts: dict[str, str] = {}
    for raw_path, raw_spec in raw_artifacts.items():
        relative_path = _normalise_relative_path(str(raw_path))
        raw_digest = raw_spec.get("sha256") if isinstance(raw_spec, Mapping) else raw_spec
        artifacts[relative_path] = _validate_sha256(
            raw_digest, f"protocol.yaml 制品 {relative_path} 的 sha256"
        )
    for required_path in ("samples.parquet", "field-roles.yaml"):
        if required_path not in artifacts:
            raise FrozenProtocolError(f"protocol.yaml 未登记必需制品：{required_path}")
    return artifacts


def _verify_artifact(root: Path, relative_path: str, expected_sha256: str) -> Path:
    path = root / relative_path
    if not path.is_file():
        raise FrozenProtocolError(f"冻结制品不存在：{relative_path}")
    actual_sha256 = file_sha256(path)
    if actual_sha256 != expected_sha256:
        raise FrozenProtocolError(
            f"冻结制品哈希不一致：{relative_path}，期望 {expected_sha256}，实际 {actual_sha256}"
        )
    return path


def _parse_field_roles(
    path: Path,
    *,
    expected_protocol_version: str,
) -> tuple[dict[str, FieldRole], dict[str, ModelView]]:
    document = _read_yaml_mapping(path, "字段角色文件")
    version = _required_string(document, "protocol_version", "field-roles.yaml")
    if version != expected_protocol_version:
        raise FrozenProtocolError(
            f"field-roles.yaml 协议版本不一致：{version} != {expected_protocol_version}"
        )

    raw_fields = document.get("fields")
    if not isinstance(raw_fields, Mapping) or not raw_fields:
        raise FrozenProtocolError("field-roles.yaml 的 fields 必须是非空对象")
    fields: dict[str, FieldRole] = {}
    for raw_name, raw_spec in raw_fields.items():
        name = str(raw_name).strip()
        if not name:
            raise FrozenProtocolError("field-roles.yaml 不得包含空字段名")
        if isinstance(raw_spec, Mapping):
            role = str(raw_spec.get("role", "")).strip()
            raw_views = raw_spec.get("views", ())
            if not isinstance(raw_views, (list, tuple)):
                raise FrozenProtocolError(f"字段 {name} 的 views 必须是列表")
            views = tuple(str(view).strip() for view in raw_views)
        else:
            role = str(raw_spec).strip()
            views = ()
        if not role:
            raise FrozenProtocolError(f"字段 {name} 缺少非空 role")
        if role not in ALLOWED_FIELD_ROLES:
            raise FrozenProtocolError(f"字段 {name} 使用了未知角色：{role}")
        if any(not view for view in views) or len(views) != len(set(views)):
            raise FrozenProtocolError(f"字段 {name} 的 views 含空值或重复值")
        fields[name] = FieldRole(name=name, role=role, views=views)

    raw_views = document.get("views")
    if not isinstance(raw_views, Mapping) or not raw_views:
        raise FrozenProtocolError("field-roles.yaml 的 views 必须是非空对象")
    model_views: dict[str, ModelView] = {}
    for raw_name, raw_spec in raw_views.items():
        name = str(raw_name).strip()
        if not name or not isinstance(raw_spec, Mapping):
            raise FrozenProtocolError("每个模型视图必须是具名对象")
        raw_feature_fields = raw_spec.get("feature_fields")
        if not isinstance(raw_feature_fields, (list, tuple)) or not raw_feature_fields:
            raise FrozenProtocolError(f"模型视图 {name} 缺少非空 feature_fields")
        feature_fields = tuple(str(field).strip() for field in raw_feature_fields)
        if any(not field for field in feature_fields) or len(feature_fields) != len(
            set(feature_fields)
        ):
            raise FrozenProtocolError(f"模型视图 {name} 的 feature_fields 含空值或重复值")
        for field in feature_fields:
            if field not in fields:
                raise FrozenProtocolError(f"模型视图 {name} 引用了未定义字段：{field}")
            field_role = fields[field]
            if field_role.role != "model_input":
                raise FrozenProtocolError(
                    f"模型视图 {name} 越过字段预算：{field} 的角色为 {field_role.role}"
                )
            if field_role.views and name not in field_role.views:
                raise FrozenProtocolError(f"模型视图 {name} 未获字段 {field} 的显式可见权限")
        model_views[name] = ModelView(name=name, feature_fields=feature_fields)
    if TREE_VIEW_NAME not in model_views:
        raise FrozenProtocolError(f"field-roles.yaml 缺少必需视图：{TREE_VIEW_NAME}")
    return fields, model_views


def _load_samples(path: Path, expected_protocol_version: str) -> pd.DataFrame:
    try:
        samples = pd.read_parquet(path)
    except Exception as error:
        raise FrozenProtocolError(f"无法读取 samples.parquet：{path}") from error
    for required_column in ("protocol_version", "sample_id"):
        if required_column not in samples.columns:
            raise FrozenProtocolError(f"samples.parquet 缺少字段：{required_column}")
    if samples.empty:
        raise FrozenProtocolError("samples.parquet 不能为空")
    versions = {str(value).strip() for value in samples["protocol_version"].tolist()}
    if versions != {expected_protocol_version}:
        raise FrozenProtocolError("samples.parquet 协议版本不一致：" + ", ".join(sorted(versions)))
    raw_sample_ids = samples["sample_id"].tolist()
    if any(pd.isna(value) for value in raw_sample_ids):
        raise FrozenProtocolError("samples.parquet 的 sample_id 不得为空")
    sample_ids = [str(value).strip() for value in raw_sample_ids]
    if any(not sample_id for sample_id in sample_ids):
        raise FrozenProtocolError("samples.parquet 的 sample_id 不得为空")
    if len(sample_ids) != len(set(sample_ids)):
        raise FrozenProtocolError("samples.parquet 的 sample_id 必须全局唯一")
    samples = samples.copy()
    samples["sample_id"] = sample_ids
    return samples


def _load_manifest(
    path: Path,
    *,
    root: Path,
    expected_protocol_version: str,
    expected_samples_sha256: str,
    sample_ids: frozenset[str],
    expected_manifest_sha256: str,
) -> SplitManifest:
    relative_path = path.relative_to(root).as_posix()
    actual_sha256 = file_sha256(path)
    if actual_sha256 != expected_manifest_sha256:
        raise FrozenProtocolError(
            f"划分清单哈希不一致：{relative_path}，"
            f"期望 {expected_manifest_sha256}，实际 {actual_sha256}"
        )

    rows: list[Mapping[str, object]] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise FrozenProtocolError(
                    f"划分清单不是合法 JSONL：{relative_path}:{line_number}"
                ) from error
            if not isinstance(value, Mapping):
                raise FrozenProtocolError(f"划分清单每行必须是对象：{relative_path}:{line_number}")
            rows.append(value)
    if not rows:
        raise FrozenProtocolError(f"划分清单不能为空：{relative_path}")

    versions = {
        _required_string(row, "protocol_version", f"{relative_path} 清单行") for row in rows
    }
    suites = {_required_string(row, "suite_id", f"{relative_path} 清单行") for row in rows}
    splits = {_required_string(row, "split_id", f"{relative_path} 清单行") for row in rows}
    parent_hashes = {
        _validate_sha256(row.get("samples_sha256"), f"{relative_path} 清单行的 samples_sha256")
        for row in rows
    }
    if versions != {expected_protocol_version}:
        raise FrozenProtocolError(f"划分清单协议版本不一致：{relative_path}")
    if len(suites) != 1 or len(splits) != 1:
        raise FrozenProtocolError(f"单个划分清单只能包含一个 suite_id 和 split_id：{relative_path}")
    if parent_hashes != {expected_samples_sha256}:
        raise FrozenProtocolError(f"划分清单未绑定当前 samples.parquet：{relative_path}")

    ordered_sample_ids = tuple(
        _required_string(row, "sample_id", f"{relative_path} 清单行") for row in rows
    )
    if len(ordered_sample_ids) != len(set(ordered_sample_ids)):
        raise FrozenProtocolError(f"划分清单包含重复 sample_id：{relative_path}")
    missing = sorted(set(ordered_sample_ids).difference(sample_ids))
    if missing:
        preview = ", ".join(missing[:5])
        raise FrozenProtocolError(
            f"划分清单引用 samples.parquet 外的样本：{relative_path}:{preview}"
        )

    return SplitManifest(
        relative_path=relative_path,
        protocol_version=expected_protocol_version,
        suite_id=next(iter(suites)),
        split_id=next(iter(splits)),
        sample_ids=ordered_sample_ids,
        sha256=actual_sha256,
        samples_sha256=expected_samples_sha256,
        sample_order_sha256=sample_order_sha256(ordered_sample_ids),
    )


def _validate_split_membership(manifests: Mapping[str, SplitManifest]) -> None:
    memberships: dict[tuple[str, str], str] = {}
    conflicts: defaultdict[tuple[str, str, str], list[str]] = defaultdict(list)
    for manifest in manifests.values():
        for sample_id in manifest.sample_ids:
            key = (manifest.suite_id, sample_id)
            previous_split = memberships.get(key)
            if previous_split is not None and previous_split != manifest.split_id:
                conflicts[(manifest.suite_id, previous_split, manifest.split_id)].append(sample_id)
            memberships[key] = manifest.split_id
    if conflicts:
        (suite_id, first_split, second_split), sample_ids = next(iter(conflicts.items()))
        preview = ", ".join(sample_ids[:5])
        raise FrozenProtocolError(
            "同一套件的样本不得跨划分：" f"{suite_id}:{first_split}/{second_split}:{preview}"
        )


def load_frozen_protocol(
    root: Path,
    *,
    expected_protocol_version: str = FROZEN_PROTOCOL_VERSION,
    expected_status: str = "frozen",
    expected_phase: str = FINAL_TUNING_STAGE,
) -> FrozenProtocol:
    """只读加载并验证冻结协议的全部基础制品与划分清单。"""
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise FrozenProtocolError(f"协议目录不存在：{root}")
    protocol_path = root / "protocol.yaml"
    protocol_document = _read_yaml_mapping(protocol_path, "协议文件")
    protocol_version = _required_string(protocol_document, "protocol_version", "protocol.yaml")
    if protocol_version != expected_protocol_version:
        raise FrozenProtocolError(
            f"协议版本不一致：{protocol_version} != {expected_protocol_version}"
        )
    status = _required_string(protocol_document, "status", "protocol.yaml")
    phase = _required_string(protocol_document, "phase", "protocol.yaml")
    if status != expected_status:
        raise FrozenProtocolError(f"协议状态不一致：{status} != {expected_status}")
    if phase != expected_phase:
        raise FrozenProtocolError(f"协议阶段不一致：{phase} != {expected_phase}")
    artifact_hashes = _parse_artifact_hashes(protocol_document)

    actual_split_paths = {
        path.relative_to(root).as_posix() for path in sorted((root / "splits").glob("*.jsonl"))
    }
    registered_split_paths = {
        path for path in artifact_hashes if path.startswith("splits/") and path.endswith(".jsonl")
    }
    if not actual_split_paths:
        raise FrozenProtocolError("splits/ 至少需要一个 JSONL 划分清单")
    if actual_split_paths != registered_split_paths:
        unregistered = sorted(actual_split_paths.difference(registered_split_paths))
        missing = sorted(registered_split_paths.difference(actual_split_paths))
        details = []
        if unregistered:
            details.append("未登记=" + ",".join(unregistered))
        if missing:
            details.append("不存在=" + ",".join(missing))
        raise FrozenProtocolError("划分清单与 protocol.yaml 不一致：" + "；".join(details))

    samples_path = _verify_artifact(root, "samples.parquet", artifact_hashes["samples.parquet"])
    field_roles_path = _verify_artifact(
        root, "field-roles.yaml", artifact_hashes["field-roles.yaml"]
    )
    fields, model_views = _parse_field_roles(
        field_roles_path, expected_protocol_version=protocol_version
    )
    samples = _load_samples(samples_path, protocol_version)
    unclassified_columns = sorted(set(samples.columns).difference(fields))
    absent_columns = sorted(set(fields).difference(samples.columns))
    if unclassified_columns or absent_columns:
        details = []
        if unclassified_columns:
            details.append("未分类=" + ",".join(unclassified_columns))
        if absent_columns:
            details.append("主记录缺失=" + ",".join(absent_columns))
        raise FrozenProtocolError(
            "samples.parquet 与 field-roles.yaml 字段集合不一致：" + "；".join(details)
        )
    sample_ids = frozenset(samples["sample_id"].tolist())

    manifests = {
        relative_path: _load_manifest(
            root / relative_path,
            root=root,
            expected_protocol_version=protocol_version,
            expected_samples_sha256=artifact_hashes["samples.parquet"],
            sample_ids=sample_ids,
            expected_manifest_sha256=artifact_hashes[relative_path],
        )
        for relative_path in sorted(actual_split_paths)
    }
    _validate_split_membership(manifests)
    return FrozenProtocol(
        root=root,
        protocol_version=protocol_version,
        status=status,
        phase=phase,
        protocol_sha256=file_sha256(protocol_path),
        samples_sha256=artifact_hashes["samples.parquet"],
        field_roles_sha256=artifact_hashes["field-roles.yaml"],
        artifact_hashes=MappingProxyType(dict(artifact_hashes)),
        field_roles=MappingProxyType(fields),
        model_views=MappingProxyType(model_views),
        manifests=MappingProxyType(manifests),
        _samples=samples,
    )
