"""从三类候选协议构建统一索引和确定性训练预算。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path, PurePosixPath

import pandas as pd
import yaml

from flow_probe.frozen_protocol import (
    FrozenProtocol,
    FrozenProtocolError,
    file_sha256,
    load_frozen_protocol,
    sample_order_sha256,
)


CONFIG_SCHEMA_VERSION = "flow_probe_unified_budget_config_v1"
BUDGET_SCHEMA_VERSION = "flow_probe_unified_budget_v1"
REQUIRED_OUTPUT_FILES = (
    "master_records.parquet",
    "train_genis_30000.jsonl",
    "train_tqhc2_cell_cap1000.jsonl",
    "train_ns3_all2421.jsonl",
    "train_unified_formal.jsonl",
    "train_candidate_approx10000.jsonl",
    "eval_genis_open_neural_30000.jsonl",
    "eval_genis_open_full_1179168.jsonl",
    "budget_statistics.json",
    "budget_checksums.json",
    "budget_freeze_manifest.json",
)
NS3_SPLIT_ORDER = ("train", "validation", "test")
MASTER_COLUMNS = (
    "sample_id",
    "source_dataset",
    "source_artifact",
    "source_record_ordinal",
    "source_split",
    "group_id",
    "task_role",
    "tree_view_available",
    "sequence_view_available",
    "physics_view_available",
    "source_binary_label",
    "source_family_label",
    "source_subtype_label",
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class UnifiedBudgetError(ValueError):
    """统一索引或预算输入不满足固定合同。"""


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise UnifiedBudgetError(f"{description}必须是对象")
    return value


def _string(mapping: Mapping[str, object], key: str, description: str) -> str:
    value = str(mapping.get(key, "")).strip()
    if not value:
        raise UnifiedBudgetError(f"{description}缺少非空字段：{key}")
    return value


def _integer(mapping: Mapping[str, object], key: str, description: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool):
        raise UnifiedBudgetError(f"{description}.{key}必须是非负整数")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise UnifiedBudgetError(f"{description}.{key}必须是非负整数") from error
    if parsed < 0:
        raise UnifiedBudgetError(f"{description}.{key}必须是非负整数")
    return parsed


def _boolean(mapping: Mapping[str, object], key: str, description: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise UnifiedBudgetError(f"{description}.{key}必须是布尔值")
    return value


def _string_tuple(
    mapping: Mapping[str, object],
    key: str,
    description: str,
) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value:
        raise UnifiedBudgetError(f"{description}.{key}必须是非空字符串列表")
    parsed = tuple(str(item).strip() for item in value)
    if any(not item for item in parsed):
        raise UnifiedBudgetError(f"{description}.{key}包含空字段")
    return parsed


def _sha256(value: object, description: str) -> str:
    digest = str(value).strip()
    if _SHA256_PATTERN.fullmatch(digest) is None:
        raise UnifiedBudgetError(f"{description}必须是小写 SHA-256")
    return digest


def _normalise_relative_path(value: object, description: str) -> str:
    raw = str(value).strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        raise UnifiedBudgetError(f"{description}必须是安全的项目相对路径：{raw!r}")
    return path.as_posix()


def _project_path(project_root: Path, value: object, description: str) -> tuple[Path, str]:
    relative_path = _normalise_relative_path(value, description)
    path = (project_root / relative_path).resolve()
    try:
        path.relative_to(project_root)
    except ValueError as error:
        raise UnifiedBudgetError(f"{description}越过 project_root：{relative_path}") from error
    return path, relative_path


def _read_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise UnifiedBudgetError(f"固定配置不存在：{path}")
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise UnifiedBudgetError(f"固定配置不是合法 YAML：{path}") from error
    if not isinstance(document, dict):
        raise UnifiedBudgetError("固定配置根节点必须是对象")
    if document.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise UnifiedBudgetError("固定配置 schema_version 不符合合同")
    return document


def _read_jsonl(path: Path, description: str) -> list[dict[str, object]]:
    if not path.is_file():
        raise UnifiedBudgetError(f"缺少{description}：{path}")
    records: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise UnifiedBudgetError(
                    f"{description}不是合法 JSONL：第 {line_number} 行"
                ) from error
            if not isinstance(value, dict):
                raise UnifiedBudgetError(f"{description}第 {line_number} 行必须是对象")
            records.append(value)
    if not records:
        raise UnifiedBudgetError(f"{description}不能为空")
    return records


def _verify_file(path: Path, expected_sha256: object, description: str) -> str:
    expected = _sha256(expected_sha256, f"{description}登记哈希")
    if not path.is_file():
        raise UnifiedBudgetError(f"{description}不存在：{path}")
    actual = file_sha256(path)
    if actual != expected:
        raise UnifiedBudgetError(f"{description}哈希不一致：期望 {expected}，实际 {actual}")
    return actual


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _stable_digest(separator: str, *parts: object) -> str:
    payload = separator.join(str(part) for part in parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _hamilton_allocate(counts: Mapping[str, int], target: int) -> dict[str, int]:
    """按最大余数法分配精确配额，并在可行时给每个非空层至少一条。"""
    if target < 0:
        raise UnifiedBudgetError("Hamilton 目标必须是非负整数")
    normalised: dict[str, int] = {}
    for raw_key, raw_count in counts.items():
        key = str(raw_key)
        if isinstance(raw_count, bool) or int(raw_count) <= 0:
            raise UnifiedBudgetError(f"Hamilton 分层容量必须为正整数：{key}")
        normalised[key] = int(raw_count)
    if not normalised:
        if target == 0:
            return {}
        raise UnifiedBudgetError("Hamilton 不能从空分层分配正目标")
    total = sum(normalised.values())
    if target > total:
        raise UnifiedBudgetError(f"Hamilton 目标 {target} 超过可用样本 {total}")
    if target == total:
        return dict(sorted(normalised.items()))

    minimum = 1 if target >= len(normalised) else 0
    allocation = {key: minimum for key in normalised}
    remaining_target = target - minimum * len(normalised)
    capacities = {key: count - minimum for key, count in normalised.items()}
    total_capacity = sum(capacities.values())
    if remaining_target == 0:
        return dict(sorted(allocation.items()))
    if total_capacity <= 0:
        raise UnifiedBudgetError("Hamilton 剩余容量不足")

    remainders: list[tuple[Fraction, str]] = []
    assigned = 0
    for key in sorted(capacities):
        quota = Fraction(remaining_target * capacities[key], total_capacity)
        floor_value = quota.numerator // quota.denominator
        allocation[key] += floor_value
        assigned += floor_value
        remainders.append((quota - floor_value, key))
    remainder_count = remaining_target - assigned
    for _, key in sorted(remainders, key=lambda item: (-item[0], item[1]))[:remainder_count]:
        allocation[key] += 1
    if sum(allocation.values()) != target:
        raise UnifiedBudgetError("Hamilton 配额未达到精确目标")
    if any(allocation[key] > normalised[key] for key in normalised):
        raise UnifiedBudgetError("Hamilton 配额超过分层容量")
    return dict(sorted(allocation.items()))


def _utc_day(value: object) -> str:
    try:
        timestamp = float(value)
    except (TypeError, ValueError) as error:
        raise UnifiedBudgetError(f"GeNIS start_time 不是 Unix 秒：{value!r}") from error
    if not math.isfinite(timestamp):
        raise UnifiedBudgetError("GeNIS start_time 必须是有限数")
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError) as error:
        raise UnifiedBudgetError(f"GeNIS start_time 超出 UTC 时间范围：{timestamp}") from error


def _load_session_days(
    path: Path,
    *,
    expected_sha256: object,
) -> tuple[dict[str, str], str]:
    digest = _verify_file(path, expected_sha256, "GeNIS 会话分配文件")
    records = _read_jsonl(path, "GeNIS 会话分配文件")
    session_days: dict[str, str] = {}
    for index, record in enumerate(records, start=1):
        session_id = str(record.get("session_id", "")).strip()
        if not session_id:
            raise UnifiedBudgetError(f"GeNIS 会话分配第 {index} 行缺少 session_id")
        if session_id in session_days:
            raise UnifiedBudgetError(f"GeNIS 会话分配包含重复 session_id：{session_id}")
        session_days[session_id] = _utc_day(record.get("start_time"))
    return session_days, digest


def _manifest_relative_path(
    project_root: Path,
    protocol_root: Path,
    value: object,
    description: str,
) -> tuple[Path, str, str]:
    path, project_relative = _project_path(project_root, value, description)
    try:
        protocol_relative = path.relative_to(protocol_root).as_posix()
    except ValueError as error:
        raise UnifiedBudgetError(f"{description}不在对应候选协议目录内") from error
    return path, project_relative, protocol_relative


def _load_candidate_protocol(
    *,
    project_root: Path,
    source: Mapping[str, object],
    contract: Mapping[str, object],
    description: str,
) -> tuple[FrozenProtocol, str, str]:
    protocol_root, protocol_dir_relative = _project_path(
        project_root, source.get("protocol_dir"), f"{description}.protocol_dir"
    )
    protocol_file, protocol_file_relative = _project_path(
        project_root, source.get("protocol_file"), f"{description}.protocol_file"
    )
    samples_file, samples_file_relative = _project_path(
        project_root, source.get("samples_file"), f"{description}.samples_file"
    )
    if protocol_file != protocol_root / "protocol.yaml":
        raise UnifiedBudgetError(f"{description}.protocol_file 未绑定 protocol_dir/protocol.yaml")
    if samples_file != protocol_root / "samples.parquet":
        raise UnifiedBudgetError(f"{description}.samples_file 未绑定 protocol_dir/samples.parquet")
    _verify_file(protocol_file, source.get("protocol_sha256"), f"{description} protocol.yaml")
    _verify_file(samples_file, source.get("samples_sha256"), f"{description} samples.parquet")
    try:
        protocol = load_frozen_protocol(
            protocol_root,
            expected_protocol_version=_string(contract, "version", "protocol_contract"),
            expected_status=_string(contract, "status", "protocol_contract"),
            expected_phase=_string(contract, "phase", "protocol_contract"),
        )
    except FrozenProtocolError as error:
        raise UnifiedBudgetError(f"{description}候选协议加载失败：{error}") from error
    expected_count = _integer(source, "expected_sample_count", description)
    if len(protocol._samples) != expected_count:
        raise UnifiedBudgetError(
            f"{description}样本数不一致：{len(protocol._samples)} != {expected_count}"
        )
    identity = _mapping(source.get("identity"), f"{description}.identity")
    identity_field = _string(identity, "field", f"{description}.identity")
    if identity_field != "sample_id":
        raise UnifiedBudgetError(f"{description}身份字段必须是 sample_id")
    expected_unique = _integer(identity, "expected_unique_count", f"{description}.identity")
    if protocol._samples["sample_id"].nunique() != expected_unique:
        raise UnifiedBudgetError(f"{description} sample_id 唯一数量不符合合同")
    pattern = identity.get("pattern")
    if pattern is not None:
        try:
            compiled = re.compile(str(pattern))
        except re.error as error:
            raise UnifiedBudgetError(f"{description}身份正则无效") from error
        invalid = protocol._samples.loc[
            ~protocol._samples["sample_id"]
            .astype(str)
            .map(lambda sample_id: compiled.fullmatch(sample_id) is not None),
            "sample_id",
        ]
        if not invalid.empty:
            raise UnifiedBudgetError(f"{description} sample_id 不符合身份正则：{invalid.iloc[0]}")
    return protocol, protocol_dir_relative, samples_file_relative


def _load_bound_manifest(
    *,
    project_root: Path,
    protocol: FrozenProtocol,
    pool: Mapping[str, object],
    description: str,
    expected_split_id: str | None = None,
) -> tuple[tuple[str, ...], str, str]:
    path, project_relative, protocol_relative = _manifest_relative_path(
        project_root,
        protocol.root,
        pool.get("manifest"),
        f"{description}.manifest",
    )
    digest = _verify_file(path, pool.get("manifest_sha256"), f"{description}清单")
    try:
        manifest = protocol.manifest(protocol_relative)
    except FrozenProtocolError as error:
        raise UnifiedBudgetError(f"{description}清单未登记到候选协议：{error}") from error
    if expected_split_id is not None and manifest.split_id != expected_split_id:
        raise UnifiedBudgetError(
            f"{description}清单 split_id 不一致：{manifest.split_id} != {expected_split_id}"
        )
    expected_count = _integer(pool, "expected_count", description)
    if len(manifest.sample_ids) != expected_count:
        raise UnifiedBudgetError(
            f"{description}清单样本数不一致：{len(manifest.sample_ids)} != {expected_count}"
        )
    return manifest.sample_ids, project_relative, digest


def _require_columns(frame: pd.DataFrame, fields: Sequence[str], description: str) -> None:
    missing = sorted(set(fields).difference(frame.columns))
    if missing:
        raise UnifiedBudgetError(f"{description}缺少字段：{','.join(missing)}")


def _genis_strata(
    *,
    sample_ids: Sequence[str],
    indexed_samples: pd.DataFrame,
    session_days: Mapping[str, str],
) -> dict[str, list[tuple[str, str]]]:
    _require_columns(
        indexed_samples,
        ("sample_id", "group_id", "family_label", "subtype_label"),
        "GeNIS samples.parquet",
    )
    strata: defaultdict[str, list[tuple[str, str]]] = defaultdict(list)
    for sample_id in sample_ids:
        row = indexed_samples.loc[sample_id]
        group_id = str(row["group_id"]).strip()
        try:
            day = session_days[group_id]
        except KeyError as error:
            raise UnifiedBudgetError(
                f"GeNIS 样本缺少会话时间连接：{sample_id}:{group_id}"
            ) from error
        family = str(row["family_label"]).strip()
        subtype = str(row["subtype_label"]).strip()
        if not group_id or not family or not subtype:
            raise UnifiedBudgetError(f"GeNIS 分层字段不能为空：{sample_id}")
        stratum = f"{day}|{family}|{subtype}"
        strata[stratum].append((group_id, sample_id))
    return dict(strata)


def _round_robin_select(
    rows: Sequence[tuple[str, str]],
    *,
    quota: int,
    namespace: str,
    seed: int,
    stratum: str,
    separator: str,
) -> list[str]:
    by_group: defaultdict[str, list[str]] = defaultdict(list)
    for group_id, sample_id in rows:
        by_group[group_id].append(sample_id)
    ordered_groups = sorted(
        by_group,
        key=lambda group_id: (
            _stable_digest(separator, namespace, seed, stratum, group_id),
            group_id,
        ),
    )
    ordered_samples = {
        group_id: sorted(
            sample_ids,
            key=lambda sample_id: (
                _stable_digest(separator, namespace, seed, stratum, group_id, sample_id),
                sample_id,
            ),
        )
        for group_id, sample_ids in by_group.items()
    }
    selected: list[str] = []
    round_index = 0
    while len(selected) < quota:
        progressed = False
        for group_id in ordered_groups:
            group_samples = ordered_samples[group_id]
            if round_index < len(group_samples):
                selected.append(group_samples[round_index])
                progressed = True
                if len(selected) == quota:
                    break
        if not progressed:
            raise UnifiedBudgetError(f"GeNIS 分层轮转容量不足：{stratum}")
        round_index += 1
    return selected


def _select_genis(
    *,
    sample_ids: Sequence[str],
    indexed_samples: pd.DataFrame,
    session_days: Mapping[str, str],
    target: int,
    namespace: str,
    seed: int,
    separator: str,
) -> tuple[list[str], dict[str, int]]:
    if target > len(sample_ids):
        raise UnifiedBudgetError(f"GeNIS 目标 {target} 超过可用样本 {len(sample_ids)}")
    strata = _genis_strata(
        sample_ids=sample_ids,
        indexed_samples=indexed_samples,
        session_days=session_days,
    )
    allocation = _hamilton_allocate(
        {stratum: len(rows) for stratum, rows in strata.items()}, target
    )
    selected: list[str] = []
    for stratum in sorted(strata):
        selected.extend(
            _round_robin_select(
                strata[stratum],
                quota=allocation[stratum],
                namespace=namespace,
                seed=seed,
                stratum=stratum,
                separator=separator,
            )
        )
    return selected, allocation


def _select_tqhc2_candidate(
    *,
    sample_ids: Sequence[str],
    indexed_samples: pd.DataFrame,
    fields: Sequence[str],
    target: int,
    namespace: str,
    seed: int,
    separator: str,
) -> tuple[list[str], dict[str, int]]:
    if target > len(sample_ids):
        raise UnifiedBudgetError(f"TQH-C2 目标 {target} 超过可用样本 {len(sample_ids)}")
    _require_columns(indexed_samples, ("sample_id", *fields), "TQH-C2 samples.parquet")
    strata: defaultdict[str, list[str]] = defaultdict(list)
    for sample_id in sample_ids:
        row = indexed_samples.loc[sample_id]
        values = [str(row[field]).strip() for field in fields]
        if any(not value for value in values):
            raise UnifiedBudgetError(f"TQH-C2 候选分层字段不能为空：{sample_id}")
        strata["|".join(values)].append(sample_id)
    allocation = _hamilton_allocate({stratum: len(ids) for stratum, ids in strata.items()}, target)
    selected: list[str] = []
    for stratum in sorted(strata):
        ranked = sorted(
            strata[stratum],
            key=lambda sample_id: (
                _stable_digest(separator, namespace, seed, stratum, sample_id),
                sample_id,
            ),
        )
        selected.extend(ranked[: allocation[stratum]])
    return selected, allocation


def _stable_order(
    sample_ids: Sequence[str],
    *,
    source_by_id: Mapping[str, str],
    namespace: str,
    seed: int,
    separator: str,
) -> list[str]:
    return sorted(
        sample_ids,
        key=lambda sample_id: (
            _stable_digest(
                separator,
                namespace,
                seed,
                source_by_id[sample_id],
                sample_id,
            ),
            source_by_id[sample_id],
            sample_id,
        ),
    )


def _optional_string_series(frame: pd.DataFrame, field: str) -> pd.Series:
    if field not in frame.columns:
        return pd.Series([None] * len(frame), dtype="string")
    return frame[field].astype("string")


def _protocol_master_frame(
    *,
    protocol: FrozenProtocol,
    source_dataset: str,
    source_artifact: str,
    formal_ids: frozenset[str],
    open_ids: frozenset[str],
    split_field: str,
    group_field: str,
) -> pd.DataFrame:
    samples = protocol._samples.reset_index(drop=True)
    _require_columns(samples, ("sample_id", group_field), f"{source_dataset} 主索引")
    sample_ids = samples["sample_id"].astype(str)
    if split_field in samples.columns:
        source_split = samples[split_field].astype("string").fillna("source_pool")
    else:
        source_split = pd.Series(
            ["train" if sample_id in formal_ids else "source_pool" for sample_id in sample_ids],
            dtype="string",
        )
    task_role = pd.Series(
        [
            (
                "formal_training"
                if sample_id in formal_ids
                else "open_evaluation" if sample_id in open_ids else "source_pool_only"
            )
            for sample_id in sample_ids
        ],
        dtype="string",
    )
    tree_available = bool(protocol.model_views)
    return pd.DataFrame(
        {
            "sample_id": sample_ids.astype("string"),
            "source_dataset": pd.Series([source_dataset] * len(samples), dtype="string"),
            "source_artifact": pd.Series([source_artifact] * len(samples), dtype="string"),
            "source_record_ordinal": range(len(samples)),
            "source_split": source_split,
            "group_id": samples[group_field].astype("string"),
            "task_role": task_role,
            "tree_view_available": tree_available,
            "sequence_view_available": False,
            "physics_view_available": False,
            "source_binary_label": _optional_string_series(samples, "binary_label"),
            "source_family_label": _optional_string_series(samples, "family_label"),
            "source_subtype_label": _optional_string_series(samples, "subtype_label"),
        },
        columns=list(MASTER_COLUMNS),
    )


def _ns3_master_frame(
    records_by_split: Mapping[str, Sequence[Mapping[str, object]]],
    paths_by_split: Mapping[str, str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split in NS3_SPLIT_ORDER:
        for ordinal, record in enumerate(records_by_split[split]):
            label_targets = record.get("label_targets")
            labels = label_targets if isinstance(label_targets, Mapping) else {}
            group_id = str(record.get("group_id", "")).strip()
            if not group_id:
                metadata = record.get("metadata")
                if isinstance(metadata, Mapping):
                    group_id = str(
                        metadata.get("group_id", metadata.get("scenario_group_id", ""))
                    ).strip()
            if not group_id:
                raise UnifiedBudgetError(f"ns-3 样本缺少分组身份：{record.get('sample_id')}")
            rows.append(
                {
                    "sample_id": str(record["sample_id"]),
                    "source_dataset": "ns3",
                    "source_artifact": paths_by_split[split],
                    "source_record_ordinal": ordinal,
                    "source_split": split,
                    "group_id": group_id,
                    "task_role": "formal_training",
                    "tree_view_available": False,
                    "sequence_view_available": True,
                    "physics_view_available": bool(
                        record.get("normalized_physics") or record.get("state_supervision")
                    ),
                    "source_binary_label": labels.get(
                        "binary_label", labels.get("binary", labels.get("label"))
                    ),
                    "source_family_label": labels.get("family_label", labels.get("family")),
                    "source_subtype_label": labels.get("subtype_label", labels.get("subtype")),
                }
            )
    return pd.DataFrame(rows, columns=list(MASTER_COLUMNS))


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_json_atomic(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".tmp")
    _write_json(temporary, value)
    os.replace(temporary, path)


def _write_budget(
    path: Path,
    *,
    budget_id: str,
    sample_ids: Sequence[str],
    source_by_id: Mapping[str, str],
    split_by_id: Mapping[str, str],
    role: str,
    master_sha256: str,
) -> None:
    with path.open("w", encoding="utf-8") as output:
        for stable_order, sample_id in enumerate(sample_ids):
            row = {
                "schema_version": BUDGET_SCHEMA_VERSION,
                "budget_id": budget_id,
                "stable_order": stable_order,
                "sample_id": sample_id,
                "source_dataset": source_by_id[sample_id],
                "source_split": split_by_id[sample_id],
                "task_role": role,
                "master_records_sha256": master_sha256,
            }
            output.write(_canonical_json(row) + "\n")


def _validate_config_policy(config: Mapping[str, object]) -> tuple[int, str, Mapping[str, str]]:
    path_policy = _mapping(config.get("path_policy"), "path_policy")
    if _string(path_policy, "base", "path_policy") != "project_root":
        raise UnifiedBudgetError("path_policy.base 必须是 project_root")
    if not _boolean(path_policy, "require_project_relative_paths", "path_policy"):
        raise UnifiedBudgetError("必须启用项目相对路径门禁")
    if not _boolean(path_policy, "forbid_absolute_paths", "path_policy"):
        raise UnifiedBudgetError("必须禁止绝对来源路径")
    input_policy = _mapping(config.get("input_policy"), "input_policy")
    if _boolean(input_policy, "allow_raw_source_data", "input_policy"):
        raise UnifiedBudgetError("统一预算禁止读取原始源数据")
    if _boolean(input_policy, "allow_model_outputs", "input_policy"):
        raise UnifiedBudgetError("统一预算禁止读取模型输出")
    if not _boolean(input_policy, "preserve_source_sample_id", "input_policy"):
        raise UnifiedBudgetError("统一预算必须保留来源 sample_id")
    if _boolean(input_policy, "rewrite_labels", "input_policy"):
        raise UnifiedBudgetError("统一预算不得重写来源标签")
    if _boolean(input_policy, "rewrite_source_roles", "input_policy"):
        raise UnifiedBudgetError("统一预算不得重写来源角色")
    if (
        _integer(
            input_policy,
            "cross_source_sample_id_collisions_expected",
            "input_policy",
        )
        != 0
    ):
        raise UnifiedBudgetError("跨来源 sample_id 预期冲突数必须为零")

    determinism = _mapping(config.get("determinism"), "determinism")
    seed = _integer(determinism, "seed", "determinism")
    if _string(determinism, "hash_algorithm", "determinism") != "sha256":
        raise UnifiedBudgetError("确定性哈希算法必须是 sha256")
    if (
        _string(determinism, "quota_algorithm", "determinism")
        != "proportional_largest_remainder_minimum_one_v1"
    ):
        raise UnifiedBudgetError("确定性配额算法不符合统一预算合同")
    if (
        _string(determinism, "unified_order_algorithm", "determinism")
        != "global_sha256_ascending_v1"
    ):
        raise UnifiedBudgetError("统一混排算法不符合统一预算合同")
    if _string_tuple(determinism, "rank_key_fields", "determinism") != (
        "algorithm_namespace",
        "seed",
        "source_dataset",
        "sample_id",
    ):
        raise UnifiedBudgetError("确定性排序键不符合统一预算合同")
    for key in (
        "require_input_order_independence",
        "require_unique_sample_ids",
        "require_byte_identical_rebuilds",
    ):
        if not _boolean(determinism, key, "determinism"):
            raise UnifiedBudgetError(f"determinism.{key} 必须启用")
    separator = _string(determinism, "separator", "determinism")
    if separator == "\\0":
        separator = "\0"
    namespaces_raw = _mapping(
        determinism.get("algorithm_namespaces"), "determinism.algorithm_namespaces"
    )
    required_namespaces = {
        "genis_formal",
        "genis_candidate",
        "genis_open_neural",
        "tqhc2_candidate",
        "unified_formal_order",
        "unified_candidate_order",
    }
    namespaces = {
        key: _string(namespaces_raw, key, "determinism.algorithm_namespaces")
        for key in sorted(required_namespaces)
    }
    if len(set(namespaces.values())) != len(namespaces):
        raise UnifiedBudgetError("各选择阶段必须使用独立算法命名空间")
    return seed, separator, namespaces


def materialize_unified_budget(
    *,
    project_root: Path,
    config_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """构建统一主索引和七份预算清单，并以原子改名发布新目录。"""
    project_root = Path(project_root).expanduser().resolve()
    config_path = Path(config_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if not project_root.is_dir():
        raise UnifiedBudgetError(f"project_root 不存在：{project_root}")
    if output_dir.exists():
        raise UnifiedBudgetError(f"输出目录已存在，拒绝覆盖：{output_dir}")
    config = _read_yaml(config_path)
    seed, separator, namespaces = _validate_config_policy(config)
    publication = _mapping(config.get("publication"), "publication")
    if not _boolean(publication, "refuse_overwrite", "publication"):
        raise UnifiedBudgetError("publication 必须拒绝覆盖")
    if not _boolean(publication, "require_atomic_rename", "publication"):
        raise UnifiedBudgetError("publication 必须要求原子改名")
    build_root, _ = _project_path(
        project_root,
        publication.get("build_root"),
        "publication.build_root",
    )
    independent_builds = publication.get("independent_builds")
    if not isinstance(independent_builds, list) or not independent_builds:
        raise UnifiedBudgetError("publication.independent_builds 必须是非空列表")
    allowed_output_dirs = {
        (build_root / _normalise_relative_path(name, "publication.independent_builds")).resolve()
        for name in independent_builds
    }
    if output_dir not in allowed_output_dirs:
        raise UnifiedBudgetError("输出目录不属于 publication.independent_builds 固定构建目录")
    _project_path(
        project_root,
        publication.get("publish_target"),
        "publication.publish_target",
    )
    partial_suffix = _string(publication, "partial_suffix", "publication")
    partial_dir = output_dir.with_name(output_dir.name + partial_suffix)
    if partial_dir.exists():
        raise UnifiedBudgetError(f"临时输出目录已存在，拒绝覆盖：{partial_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    partial_dir.mkdir()
    incomplete_marker = partial_dir / "_INCOMPLETE"
    incomplete_marker.write_text("incomplete\n", encoding="ascii")
    state_path = partial_dir / "materialization_state.json"
    state = {
        "schema_version": BUDGET_SCHEMA_VERSION,
        "status": "running",
        "config_sha256": file_sha256(config_path),
        "implementation_sha256": file_sha256(Path(__file__)),
        "input_sha256": {},
    }
    _write_json_atomic(state_path, state)
    contract = _mapping(config.get("protocol_contract"), "protocol_contract")
    sources = _mapping(config.get("sources"), "sources")
    genis_source = _mapping(sources.get("genis"), "sources.genis")
    tqh_source = _mapping(sources.get("tqhc2"), "sources.tqhc2")
    ns3_source = _mapping(sources.get("ns3"), "sources.ns3")

    genis, _, genis_samples_relative = _load_candidate_protocol(
        project_root=project_root,
        source=genis_source,
        contract=contract,
        description="GeNIS",
    )
    tqhc2, _, tqh_samples_relative = _load_candidate_protocol(
        project_root=project_root,
        source=tqh_source,
        contract=contract,
        description="TQH-C2",
    )

    genis_formal_pool = _mapping(
        genis_source.get("formal_train_pool"), "sources.genis.formal_train_pool"
    )
    genis_open_pool = _mapping(genis_source.get("open_eval_pool"), "sources.genis.open_eval_pool")
    tqh_formal_pool = _mapping(
        tqh_source.get("formal_train_pool"), "sources.tqhc2.formal_train_pool"
    )
    session_join = _mapping(genis_source.get("session_join"), "sources.genis.session_join")
    if (
        _string(session_join, "sample_field", "sources.genis.session_join") != "group_id"
        or _string(session_join, "assignment_field", "sources.genis.session_join") != "session_id"
        or not _boolean(
            session_join,
            "require_complete_join",
            "sources.genis.session_join",
        )
        or _string(session_join, "on_missing", "sources.genis.session_join") != "fail"
    ):
        raise UnifiedBudgetError("GeNIS 会话连接合同不一致")
    time_stratum = _mapping(genis_source.get("time_stratum"), "sources.genis.time_stratum")
    expected_time_contract = {
        "source_field": "start_time",
        "source_unit": "unix_seconds",
        "timezone": "UTC",
        "derived_field": "utc_day",
        "format": "%Y-%m-%d",
    }
    if any(
        _string(time_stratum, key, "sources.genis.time_stratum") != expected
        for key, expected in expected_time_contract.items()
    ) or _boolean(
        time_stratum,
        "allow_fabricated_fallback",
        "sources.genis.time_stratum",
    ):
        raise UnifiedBudgetError("GeNIS UTC 时间分层合同不一致")
    if (
        _string_tuple(
            genis_formal_pool,
            "stratification_fields",
            "sources.genis.formal_train_pool",
        )
        != ("utc_day", "family_label", "subtype_label")
        or _string(
            genis_formal_pool,
            "session_spread_field",
            "sources.genis.formal_train_pool",
        )
        != "group_id"
        or _string(
            genis_formal_pool,
            "within_stratum_algorithm",
            "sources.genis.formal_train_pool",
        )
        != "group_round_robin_then_sha256_v1"
    ):
        raise UnifiedBudgetError("GeNIS 正式训练分层合同不一致")
    if (
        _string(genis_open_pool, "allowed_use", "sources.genis.open_eval_pool") != "evaluation_only"
        or _string_tuple(
            genis_open_pool,
            "stratification_fields",
            "sources.genis.open_eval_pool",
        )
        != ("utc_day", "family_label", "subtype_label")
        or _string(
            genis_open_pool,
            "session_spread_field",
            "sources.genis.open_eval_pool",
        )
        != "group_id"
        or _string(
            genis_open_pool,
            "within_stratum_algorithm",
            "sources.genis.open_eval_pool",
        )
        != "group_round_robin_then_sha256_v1"
    ):
        raise UnifiedBudgetError("GeNIS 开放集分层合同不一致")
    if (
        _string(
            tqh_formal_pool,
            "formal_selection_algorithm",
            "sources.tqhc2.formal_train_pool",
        )
        != "preserve_manifest_membership_and_order_v1"
        or _string_tuple(
            tqh_formal_pool,
            "candidate_stratification_fields",
            "sources.tqhc2.formal_train_pool",
        )
        != (
            "allocation_group_id",
            "profile",
            "interval_s",
            "jitter_pct",
            "binary_label",
        )
        or _string(
            tqh_formal_pool,
            "candidate_within_stratum_algorithm",
            "sources.tqhc2.formal_train_pool",
        )
        != "sha256_ascending_v1"
    ):
        raise UnifiedBudgetError("TQH-C2 候选分层合同不一致")
    genis_pool_ids, genis_manifest_path, genis_manifest_hash = _load_bound_manifest(
        project_root=project_root,
        protocol=genis,
        pool=genis_formal_pool,
        description="GeNIS 正式训练池",
        expected_split_id=_string(
            genis_formal_pool,
            "required_split_id",
            "sources.genis.formal_train_pool",
        ),
    )
    genis_open_ids, genis_open_path, genis_open_hash = _load_bound_manifest(
        project_root=project_root,
        protocol=genis,
        pool=genis_open_pool,
        description="GeNIS 开放集池",
        expected_split_id="test",
    )
    tqh_formal_ids, tqh_manifest_path, tqh_manifest_hash = _load_bound_manifest(
        project_root=project_root,
        protocol=tqhc2,
        pool=tqh_formal_pool,
        description="TQH-C2 正式训练池",
        expected_split_id="train",
    )
    leakage = set(genis_pool_ids).intersection(genis_open_ids)
    if leakage:
        raise UnifiedBudgetError(f"GeNIS 训练与开放集发生划分泄漏：{sorted(leakage)[0]}")
    required_partition = _string(
        genis_formal_pool,
        "required_source_partition",
        "sources.genis.formal_train_pool",
    )
    genis_indexed = genis._samples.set_index("sample_id", drop=False)
    _require_columns(
        genis._samples,
        ("source_partition", "group_id"),
        "GeNIS samples.parquet",
    )
    train_groups = set(genis_indexed.loc[list(genis_pool_ids), "group_id"].astype(str).tolist())
    open_groups = set(genis_indexed.loc[list(genis_open_ids), "group_id"].astype(str).tolist())
    group_leakage = train_groups.intersection(open_groups)
    if group_leakage:
        raise UnifiedBudgetError(
            f"GeNIS 训练与开放集发生会话级划分泄漏：{sorted(group_leakage)[0]}"
        )
    if len(train_groups) != _integer(
        genis_formal_pool,
        "expected_group_count",
        "sources.genis.formal_train_pool",
    ):
        raise UnifiedBudgetError("GeNIS 正式训练会话数不符合合同")
    invalid_partition = [
        sample_id
        for sample_id in genis_pool_ids
        if str(genis_indexed.loc[sample_id, "source_partition"]) != required_partition
    ]
    if invalid_partition:
        raise UnifiedBudgetError(f"GeNIS 正式训练池混入禁止划分：{invalid_partition[0]}")
    invalid_open_partition = [
        sample_id
        for sample_id in genis_open_ids
        if str(genis_indexed.loc[sample_id, "source_partition"]) == required_partition
    ]
    if invalid_open_partition:
        raise UnifiedBudgetError(f"GeNIS 开放集混入训练来源分区：{invalid_open_partition[0]}")

    session_path, session_relative = _project_path(
        project_root,
        genis_source.get("session_assignments_file"),
        "sources.genis.session_assignments_file",
    )
    session_days, session_hash = _load_session_days(
        session_path,
        expected_sha256=genis_source.get("session_assignments_sha256"),
    )
    missing_session_groups = sorted(
        set(genis._samples["group_id"].astype(str)).difference(session_days)
    )
    if missing_session_groups:
        raise UnifiedBudgetError(f"GeNIS 完整会话连接失败：缺少 {missing_session_groups[0]}")

    budgets = _mapping(config.get("budgets"), "budgets")
    formal_budget = _mapping(budgets.get("formal_training"), "budgets.formal_training")
    candidate_budget = _mapping(budgets.get("candidate_screening"), "budgets.candidate_screening")
    formal_counts = _mapping(
        formal_budget.get("source_counts"), "budgets.formal_training.source_counts"
    )
    candidate_counts = _mapping(
        candidate_budget.get("source_counts"), "budgets.candidate_screening.source_counts"
    )
    expected_budget_manifests = {
        "formal_training": (formal_budget, "train_unified_formal.jsonl"),
        "candidate_screening": (candidate_budget, "train_candidate_approx10000.jsonl"),
        "genis_open_neural": (
            _mapping(budgets.get("genis_open_neural"), "budgets.genis_open_neural"),
            "eval_genis_open_neural_30000.jsonl",
        ),
        "genis_open_full": (
            _mapping(budgets.get("genis_open_full"), "budgets.genis_open_full"),
            "eval_genis_open_full_1179168.jsonl",
        ),
    }
    for budget_name, (budget_spec, expected_manifest) in expected_budget_manifests.items():
        if _string(budget_spec, "output_manifest", f"budgets.{budget_name}") != expected_manifest:
            raise UnifiedBudgetError(f"budgets.{budget_name}.output_manifest 不符合合同")
    genis_formal_target = _integer(formal_counts, "genis", "formal source_counts")
    tqh_formal_target = _integer(formal_counts, "tqhc2", "formal source_counts")
    ns3_formal_target = _integer(formal_counts, "ns3", "formal source_counts")
    genis_candidate_target = _integer(candidate_counts, "genis", "candidate source_counts")
    tqh_candidate_target = _integer(candidate_counts, "tqhc2", "candidate source_counts")
    ns3_candidate_target = _integer(candidate_counts, "ns3", "candidate source_counts")
    if genis_formal_target != _integer(
        genis_formal_pool, "formal_target_count", "GeNIS 正式训练池"
    ) or genis_candidate_target != _integer(
        genis_formal_pool, "candidate_target_count", "GeNIS 正式训练池"
    ):
        raise UnifiedBudgetError("GeNIS 源预算与总预算配置不一致")
    if tqh_formal_target != _integer(
        tqh_formal_pool, "formal_target_count", "TQH-C2 正式训练池"
    ) or tqh_candidate_target != _integer(
        tqh_formal_pool, "candidate_target_count", "TQH-C2 正式训练池"
    ):
        raise UnifiedBudgetError("TQH-C2 源预算与总预算配置不一致")
    if ns3_formal_target != _integer(
        ns3_source, "formal_target_count", "sources.ns3"
    ) or ns3_candidate_target != _integer(ns3_source, "candidate_target_count", "sources.ns3"):
        raise UnifiedBudgetError("ns-3 源预算与总预算配置不一致")
    if sum((genis_formal_target, tqh_formal_target, ns3_formal_target)) != _integer(
        formal_budget, "total_target_count", "budgets.formal_training"
    ):
        raise UnifiedBudgetError("正式训练三源预算之和不等于总目标")
    if sum((genis_candidate_target, tqh_candidate_target, ns3_candidate_target)) != _integer(
        candidate_budget, "total_target_count", "budgets.candidate_screening"
    ):
        raise UnifiedBudgetError("候选筛选三源预算之和不等于总目标")
    if not _boolean(
        candidate_budget,
        "require_subset_of_formal_training",
        "budgets.candidate_screening",
    ):
        raise UnifiedBudgetError("候选筛选必须是正式训练清单的子集")
    candidate_basis = _mapping(
        candidate_budget.get("public_detection_allocation_basis"),
        "budgets.candidate_screening.public_detection_allocation_basis",
    )
    remaining_after_ns3 = _integer(
        candidate_basis,
        "remaining_after_ns3",
        "候选公开检测分配依据",
    )
    if remaining_after_ns3 != genis_candidate_target + tqh_candidate_target:
        raise UnifiedBudgetError("候选公开检测剩余预算不一致")
    if (
        _string(candidate_basis, "allocation_algorithm", "候选公开检测分配依据")
        != "hamilton_largest_remainder_v1"
    ):
        raise UnifiedBudgetError("候选公开检测分配算法不符合合同")
    formal_weights = _mapping(
        candidate_basis.get("formal_weights"),
        "候选公开检测分配依据.formal_weights",
    )
    public_weights = {
        "genis": _integer(formal_weights, "genis", "候选公开检测正式权重"),
        "tqhc2": _integer(formal_weights, "tqhc2", "候选公开检测正式权重"),
    }
    if public_weights != {
        "genis": genis_formal_target,
        "tqhc2": tqh_formal_target,
    }:
        raise UnifiedBudgetError("候选公开检测正式权重与正式预算不一致")
    public_allocation = _hamilton_allocate(public_weights, remaining_after_ns3)
    if public_allocation != {
        "genis": genis_candidate_target,
        "tqhc2": tqh_candidate_target,
    }:
        raise UnifiedBudgetError("候选公开检测三源配额不符合 Hamilton 推导")

    _require_columns(tqhc2._samples, ("split_id",), "TQH-C2 samples.parquet")
    tqh_indexed = tqhc2._samples.set_index("sample_id", drop=False)

    genis_formal_ids, genis_formal_allocation = _select_genis(
        sample_ids=genis_pool_ids,
        indexed_samples=genis_indexed,
        session_days=session_days,
        target=genis_formal_target,
        namespace=namespaces["genis_formal"],
        seed=seed,
        separator=separator,
    )
    genis_candidate_ids, genis_candidate_allocation = _select_genis(
        sample_ids=genis_formal_ids,
        indexed_samples=genis_indexed,
        session_days=session_days,
        target=genis_candidate_target,
        namespace=namespaces["genis_candidate"],
        seed=seed,
        separator=separator,
    )
    open_budget = _mapping(budgets.get("genis_open_neural"), "budgets.genis_open_neural")
    genis_open_neural_target = _integer(
        open_budget, "total_target_count", "budgets.genis_open_neural"
    )
    if genis_open_neural_target != _integer(
        genis_open_pool, "neural_eval_target_count", "GeNIS 开放集池"
    ):
        raise UnifiedBudgetError("GeNIS 开放集神经评价预算配置不一致")
    genis_open_neural_ids, genis_open_allocation = _select_genis(
        sample_ids=genis_open_ids,
        indexed_samples=genis_indexed,
        session_days=session_days,
        target=genis_open_neural_target,
        namespace=namespaces["genis_open_neural"],
        seed=seed,
        separator=separator,
    )
    open_full_budget = _mapping(budgets.get("genis_open_full"), "budgets.genis_open_full")
    if _integer(open_full_budget, "total_target_count", "budgets.genis_open_full") != len(
        genis_open_ids
    ):
        raise UnifiedBudgetError("GeNIS 完整开放集目标必须等于冻结清单样本数")

    if tqh_formal_target != len(tqh_formal_ids):
        raise UnifiedBudgetError("TQH-C2 正式目标必须逐条复用完整训练清单")
    tqh_fields = _string_tuple(
        tqh_formal_pool,
        "candidate_stratification_fields",
        "sources.tqhc2.formal_train_pool",
    )
    tqh_candidate_ids, tqh_candidate_allocation = _select_tqhc2_candidate(
        sample_ids=tqh_formal_ids,
        indexed_samples=tqh_indexed,
        fields=tqh_fields,
        target=tqh_candidate_target,
        namespace=namespaces["tqhc2_candidate"],
        seed=seed,
        separator=separator,
    )
    if len(genis_formal_allocation) != _integer(
        genis_formal_pool,
        "expected_joint_strata",
        "sources.genis.formal_train_pool",
    ):
        raise UnifiedBudgetError("GeNIS 正式训练联合分层数不符合合同")
    tqh_formal_groups = set(
        tqh_indexed.loc[list(tqh_formal_ids), "allocation_group_id"].astype(str).tolist()
    )
    if len(tqh_formal_groups) != _integer(
        tqh_formal_pool,
        "expected_allocation_group_count",
        "sources.tqhc2.formal_train_pool",
    ):
        raise UnifiedBudgetError("TQH-C2 正式训练分配组数不符合合同")
    if len(tqh_candidate_allocation) != _integer(
        tqh_formal_pool,
        "expected_joint_strata",
        "sources.tqhc2.formal_train_pool",
    ):
        raise UnifiedBudgetError("TQH-C2 候选联合分层数不符合合同")

    ns3_files = _mapping(ns3_source.get("files"), "sources.ns3.files")
    records_by_split: dict[str, list[dict[str, object]]] = {}
    ns3_paths: dict[str, str] = {}
    input_hashes: dict[str, str] = {
        _normalise_relative_path(genis_source.get("protocol_file"), "GeNIS protocol_file"): _sha256(
            genis_source.get("protocol_sha256"), "GeNIS protocol_sha256"
        ),
        _normalise_relative_path(genis_source.get("samples_file"), "GeNIS samples_file"): _sha256(
            genis_source.get("samples_sha256"), "GeNIS samples_sha256"
        ),
        genis_manifest_path: genis_manifest_hash,
        genis_open_path: genis_open_hash,
        session_relative: session_hash,
        _normalise_relative_path(tqh_source.get("protocol_file"), "TQH-C2 protocol_file"): _sha256(
            tqh_source.get("protocol_sha256"), "TQH-C2 protocol_sha256"
        ),
        _normalise_relative_path(tqh_source.get("samples_file"), "TQH-C2 samples_file"): _sha256(
            tqh_source.get("samples_sha256"), "TQH-C2 samples_sha256"
        ),
        tqh_manifest_path: tqh_manifest_hash,
    }
    all_ns3_ids: list[str] = []
    ns3_split_by_id: dict[str, str] = {}
    for split in NS3_SPLIT_ORDER:
        spec = _mapping(ns3_files.get(split), f"sources.ns3.files.{split}")
        path, relative_path = _project_path(
            project_root, spec.get("path"), f"sources.ns3.files.{split}.path"
        )
        digest = _verify_file(path, spec.get("sha256"), f"ns-3 {split} 清单")
        rows = _read_jsonl(path, f"ns-3 {split} 清单")
        expected_count = _integer(spec, "expected_count", f"ns-3 {split}")
        if len(rows) != expected_count:
            raise UnifiedBudgetError(f"ns-3 {split} 样本数不一致：{len(rows)} != {expected_count}")
        records_by_split[split] = rows
        ns3_paths[split] = relative_path
        input_hashes[relative_path] = digest
        for row in rows:
            sample_id = str(row.get("sample_id", "")).strip()
            if not sample_id:
                raise UnifiedBudgetError(f"ns-3 {split} 清单包含空 sample_id")
            if sample_id in ns3_split_by_id:
                raise UnifiedBudgetError(f"ns-3 清单包含重复 sample_id：{sample_id}")
            ns3_split_by_id[sample_id] = split
            all_ns3_ids.append(sample_id)
    for raw_name, raw_spec in ns3_files.items():
        name = str(raw_name)
        if name in NS3_SPLIT_ORDER:
            continue
        spec = _mapping(raw_spec, f"sources.ns3.files.{name}")
        path, relative_path = _project_path(
            project_root, spec.get("path"), f"sources.ns3.files.{name}.path"
        )
        input_hashes[relative_path] = _verify_file(path, spec.get("sha256"), f"ns-3 {name} 制品")
    if len(all_ns3_ids) != _integer(
        _mapping(ns3_source.get("identity"), "sources.ns3.identity"),
        "expected_unique_count",
        "sources.ns3.identity",
    ):
        raise UnifiedBudgetError("ns-3 sample_id 唯一数量不符合合同")
    ns3_groups: set[str] = set()
    for rows in records_by_split.values():
        for row in rows:
            group_id = str(row.get("group_id", "")).strip()
            if not group_id and isinstance(row.get("metadata"), Mapping):
                metadata = _mapping(row.get("metadata"), "ns-3 metadata")
                group_id = str(
                    metadata.get("group_id", metadata.get("scenario_group_id", ""))
                ).strip()
            if group_id:
                ns3_groups.add(group_id)
    if len(ns3_groups) != _integer(ns3_source, "expected_group_count", "sources.ns3"):
        raise UnifiedBudgetError("ns-3 分组数量不符合合同")
    if ns3_formal_target != len(all_ns3_ids) or ns3_candidate_target != len(all_ns3_ids):
        raise UnifiedBudgetError("ns-3 正式与候选预算必须各包含三份清单全部样本一次")

    identity_indexes = {
        "genis": pd.Index(genis._samples["sample_id"].astype(str)),
        "tqhc2": pd.Index(tqhc2._samples["sample_id"].astype(str)),
        "ns3": pd.Index(all_ns3_ids),
    }
    for left_name, right_name in (
        ("genis", "tqhc2"),
        ("genis", "ns3"),
        ("tqhc2", "ns3"),
    ):
        overlap = identity_indexes[left_name].intersection(identity_indexes[right_name])
        if not overlap.empty:
            raise UnifiedBudgetError(
                f"跨来源 sample_id 冲突：{overlap[0]}:{left_name}/{right_name}"
            )

    genis_formal_split_by_id = {
        sample_id: str(genis_indexed.at[sample_id, "source_partition"])
        for sample_id in genis_formal_ids
    }
    tqh_formal_split_by_id = {
        sample_id: str(tqh_indexed.at[sample_id, "split_id"]) for sample_id in tqh_formal_ids
    }
    formal_source_by_id = {
        **{sample_id: "genis" for sample_id in genis_formal_ids},
        **{sample_id: "tqhc2" for sample_id in tqh_formal_ids},
        **{sample_id: "ns3" for sample_id in all_ns3_ids},
    }
    formal_split_by_id = {
        **genis_formal_split_by_id,
        **tqh_formal_split_by_id,
        **ns3_split_by_id,
    }
    formal_ids = _stable_order(
        [*genis_formal_ids, *tqh_formal_ids, *all_ns3_ids],
        source_by_id=formal_source_by_id,
        namespace=namespaces["unified_formal_order"],
        seed=seed,
        separator=separator,
    )
    candidate_source_by_id = {
        **{sample_id: "genis" for sample_id in genis_candidate_ids},
        **{sample_id: "tqhc2" for sample_id in tqh_candidate_ids},
        **{sample_id: "ns3" for sample_id in all_ns3_ids},
    }
    candidate_ids = _stable_order(
        [*genis_candidate_ids, *tqh_candidate_ids, *all_ns3_ids],
        source_by_id=candidate_source_by_id,
        namespace=namespaces["unified_candidate_order"],
        seed=seed,
        separator=separator,
    )
    if not set(candidate_ids).issubset(formal_ids):
        raise UnifiedBudgetError("候选预算不是正式训练预算的子集")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise UnifiedBudgetError("候选预算包含重复 sample_id")

    master = pd.concat(
        [
            _protocol_master_frame(
                protocol=genis,
                source_dataset="genis",
                source_artifact=genis_samples_relative,
                formal_ids=frozenset(genis_formal_ids),
                open_ids=frozenset(genis_open_ids),
                split_field="source_partition",
                group_field="group_id",
            ),
            _protocol_master_frame(
                protocol=tqhc2,
                source_dataset="tqhc2",
                source_artifact=tqh_samples_relative,
                formal_ids=frozenset(tqh_formal_ids),
                open_ids=frozenset(),
                split_field="split_id",
                group_field="allocation_group_id",
            ),
            _ns3_master_frame(records_by_split, ns3_paths),
        ],
        ignore_index=True,
    )
    master = master.sort_values(
        ["source_dataset", "source_artifact", "source_record_ordinal", "sample_id"],
        kind="mergesort",
    ).reset_index(drop=True)
    outputs = _mapping(config.get("outputs"), "outputs")
    expected_master_count = _integer(outputs, "master_records_expected_count", "outputs")
    if len(master) != expected_master_count:
        raise UnifiedBudgetError(
            f"统一主索引样本数不一致：{len(master)} != {expected_master_count}"
        )
    if master["sample_id"].duplicated().any():
        duplicate = master.loc[master["sample_id"].duplicated(), "sample_id"].iloc[0]
        raise UnifiedBudgetError(f"统一主索引包含重复 sample_id：{duplicate}")

    configured_outputs = outputs.get("files")
    if not isinstance(configured_outputs, list):
        raise UnifiedBudgetError("outputs.files 必须是列表")
    configured_names = {str(name) for name in configured_outputs}
    if configured_names != set(REQUIRED_OUTPUT_FILES).difference({"master_records.parquet"}):
        raise UnifiedBudgetError("outputs.files 集合不符合统一预算合同")
    if _string(outputs, "master_records", "outputs") != "master_records.parquet":
        raise UnifiedBudgetError("outputs.master_records 文件名不符合合同")
    budgets_relative = _normalise_relative_path(
        outputs.get("budgets_dir"),
        "outputs.budgets_dir",
    )

    state["input_sha256"] = dict(sorted(input_hashes.items()))
    _write_json_atomic(state_path, state)
    budget_dir = partial_dir / budgets_relative

    try:
        budget_dir.mkdir(parents=True)
        master_path = partial_dir / "master_records.parquet"
        master.to_parquet(master_path, index=False, engine="pyarrow", compression="zstd")
        master_hash = file_sha256(master_path)
        genis_source_by_id = {sample_id: "genis" for sample_id in genis_formal_ids}
        tqh_source_by_id = {sample_id: "tqhc2" for sample_id in tqh_formal_ids}
        ns3_source_by_id = {sample_id: "ns3" for sample_id in all_ns3_ids}
        open_source_by_id = {sample_id: "genis" for sample_id in genis_open_ids}
        open_split_by_id = {
            sample_id: str(genis_indexed.at[sample_id, "source_partition"])
            for sample_id in genis_open_ids
        }

        _write_budget(
            budget_dir / "train_genis_30000.jsonl",
            budget_id="train_genis_30000",
            sample_ids=genis_formal_ids,
            source_by_id=genis_source_by_id,
            split_by_id=genis_formal_split_by_id,
            role="formal_training",
            master_sha256=master_hash,
        )
        _write_budget(
            budget_dir / "train_tqhc2_cell_cap1000.jsonl",
            budget_id="train_tqhc2_cell_cap1000",
            sample_ids=tqh_formal_ids,
            source_by_id=tqh_source_by_id,
            split_by_id=tqh_formal_split_by_id,
            role="formal_training",
            master_sha256=master_hash,
        )
        _write_budget(
            budget_dir / "train_ns3_all2421.jsonl",
            budget_id="train_ns3_all2421",
            sample_ids=all_ns3_ids,
            source_by_id=ns3_source_by_id,
            split_by_id=ns3_split_by_id,
            role="formal_training",
            master_sha256=master_hash,
        )
        _write_budget(
            budget_dir / "train_unified_formal.jsonl",
            budget_id="train_unified_formal",
            sample_ids=formal_ids,
            source_by_id=formal_source_by_id,
            split_by_id=formal_split_by_id,
            role="formal_training",
            master_sha256=master_hash,
        )
        _write_budget(
            budget_dir / "train_candidate_approx10000.jsonl",
            budget_id="train_candidate_approx10000",
            sample_ids=candidate_ids,
            source_by_id=candidate_source_by_id,
            split_by_id=formal_split_by_id,
            role="candidate_screening",
            master_sha256=master_hash,
        )
        _write_budget(
            budget_dir / "eval_genis_open_neural_30000.jsonl",
            budget_id="eval_genis_open_neural_30000",
            sample_ids=genis_open_neural_ids,
            source_by_id=open_source_by_id,
            split_by_id=open_split_by_id,
            role="open_evaluation",
            master_sha256=master_hash,
        )
        _write_budget(
            budget_dir / "eval_genis_open_full_1179168.jsonl",
            budget_id="eval_genis_open_full_1179168",
            sample_ids=genis_open_ids,
            source_by_id=open_source_by_id,
            split_by_id=open_split_by_id,
            role="open_evaluation",
            master_sha256=master_hash,
        )

        count_by_filename = {
            "train_genis_30000": len(genis_formal_ids),
            "train_tqhc2_cell_cap1000": len(tqh_formal_ids),
            "train_ns3_all2421": len(all_ns3_ids),
            "train_unified_formal": len(formal_ids),
            "train_candidate_approx10000": len(candidate_ids),
            "eval_genis_open_neural_30000": len(genis_open_neural_ids),
            "eval_genis_open_full_1179168": len(genis_open_ids),
            "master_records": len(master),
        }
        order_hashes = {
            "train_genis_30000": sample_order_sha256(genis_formal_ids),
            "train_tqhc2_cell_cap1000": sample_order_sha256(tqh_formal_ids),
            "train_ns3_all2421": sample_order_sha256(all_ns3_ids),
            "train_unified_formal": sample_order_sha256(formal_ids),
            "train_candidate_approx10000": sample_order_sha256(candidate_ids),
            "eval_genis_open_neural_30000": sample_order_sha256(genis_open_neural_ids),
            "eval_genis_open_full_1179168": sample_order_sha256(genis_open_ids),
        }
        statistics = {
            "schema_version": BUDGET_SCHEMA_VERSION,
            "config_id": _string(config, "config_id", "config"),
            "stage": _string(config, "stage", "config"),
            "status": _string(config, "status", "config"),
            "counts": count_by_filename,
            "source_counts": {
                "formal": dict(
                    sorted((str(key), int(value)) for key, value in formal_counts.items())
                ),
                "candidate": dict(
                    sorted((str(key), int(value)) for key, value in candidate_counts.items())
                ),
            },
            "strata": {
                "genis_formal": genis_formal_allocation,
                "genis_candidate": genis_candidate_allocation,
                "genis_open_neural": genis_open_allocation,
                "tqhc2_candidate": tqh_candidate_allocation,
            },
            "order_sha256": order_hashes,
            "subset_checks": {
                "genis_candidate_is_formal_subset": set(genis_candidate_ids).issubset(
                    genis_formal_ids
                ),
                "tqhc2_candidate_is_formal_subset": set(tqh_candidate_ids).issubset(tqh_formal_ids),
                "unified_candidate_is_formal_subset": set(candidate_ids).issubset(formal_ids),
                "ns3_included_once": len(all_ns3_ids) == len(set(all_ns3_ids)),
            },
            "input_sha256": dict(sorted(input_hashes.items())),
            "config_sha256": file_sha256(config_path),
            "implementation_sha256": file_sha256(Path(__file__)),
        }
        _write_json(budget_dir / "budget_statistics.json", statistics)

        checksum_paths = sorted(
            path
            for path in partial_dir.rglob("*")
            if path.is_file()
            and path.name
            not in {
                "_INCOMPLETE",
                "materialization_state.json",
                "budget_checksums.json",
                "budget_freeze_manifest.json",
            }
        )
        checksums = {
            "schema_version": BUDGET_SCHEMA_VERSION,
            "artifacts": {
                path.relative_to(partial_dir).as_posix(): {
                    "sha256": file_sha256(path),
                    "size_bytes": path.stat().st_size,
                }
                for path in checksum_paths
            },
        }
        _write_json(budget_dir / "budget_checksums.json", checksums)
        for relative_path, artifact in checksums["artifacts"].items():
            artifact_path = partial_dir / relative_path
            if not artifact_path.is_file():
                raise UnifiedBudgetError(f"校验和登记制品不存在：{relative_path}")
            if file_sha256(artifact_path) != artifact["sha256"]:
                raise UnifiedBudgetError(f"校验和登记制品哈希失配：{relative_path}")
        freeze_manifest = {
            "schema_version": BUDGET_SCHEMA_VERSION,
            "config_id": _string(config, "config_id", "config"),
            "stage": _string(config, "stage", "config"),
            "status": _string(publication, "status_before_review", "publication"),
            "config_sha256": file_sha256(config_path),
            "implementation_sha256": file_sha256(Path(__file__)),
            "master_records_sha256": master_hash,
            "budget_checksums_sha256": file_sha256(budget_dir / "budget_checksums.json"),
            "artifact_count": len(checksum_paths),
            "global_sample_id_collision_count": 0,
            "candidate_is_formal_subset": True,
            "atomic_publication": True,
        }
        _write_json(budget_dir / "budget_freeze_manifest.json", freeze_manifest)

        state["status"] = "finished"
        _write_json_atomic(state_path, state)
        incomplete_marker.unlink()
        state_path.unlink()
        actual_paths = {
            path.relative_to(partial_dir).as_posix()
            for path in partial_dir.rglob("*")
            if path.is_file()
        }
        expected_paths = {"master_records.parquet"} | {
            (PurePosixPath(budgets_relative) / name).as_posix()
            for name in set(REQUIRED_OUTPUT_FILES).difference({"master_records.parquet"})
        }
        if actual_paths != expected_paths:
            raise UnifiedBudgetError("统一预算输出文件集合不完整")
        os.replace(partial_dir, output_dir)
    except BaseException as error:
        # 保留带 `.partial` 后缀的失败现场，供重启后审计或确定性重跑。
        if partial_dir.exists():
            state["status"] = (
                "interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed"
            )
            state["error_type"] = type(error).__name__
            try:
                incomplete_marker.write_text("incomplete\n", encoding="ascii")
                _write_json_atomic(state_path, state)
            except OSError:
                pass
        raise

    return {
        "schema_version": BUDGET_SCHEMA_VERSION,
        "status": _string(publication, "status_before_review", "publication"),
        "master_record_count": len(master),
        "formal_count": len(formal_ids),
        "candidate_count": len(candidate_ids),
        "open_neural_count": len(genis_open_neural_ids),
        "open_full_count": len(genis_open_ids),
        "master_records_sha256": file_sha256(output_dir / "master_records.parquet"),
        "budget_checksums_sha256": file_sha256(
            output_dir / budgets_relative / "budget_checksums.json"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建三源统一索引与确定性预算")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = materialize_unified_budget(
        project_root=args.project_root,
        config_path=args.config,
        output_dir=args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
