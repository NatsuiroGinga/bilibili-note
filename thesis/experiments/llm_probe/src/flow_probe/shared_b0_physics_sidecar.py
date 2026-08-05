"""共享 B0 的确定性 ns-3 物理旁路物化与审计。"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import stat
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import yaml

CONFIG_SCHEMA_VERSION = "flow_probe_shared_b0_physics_sidecar_config_v1"
ARTIFACT_SCHEMA_VERSION = "flow_probe_shared_b0_physics_sidecar_v1"
DATASET_NAME = "dataset-v1-shared-b0-physics-v1"
CLASSIFICATION_LOGICAL_PATH = (
    "runs/data-frozen/dataset-v1-shared-b0/candidate/qwen_train.jsonl"
)
OUTPUT_LOGICAL_PATH = "runs/data-frozen/dataset-v1-shared-b0-physics-v1"
RECORD_LOGICAL_PATH = "candidate/ns3_physics_train.jsonl"
EXPECTED_RECORD_COUNT = 2_421
EXPECTED_SOURCE_RECORD_COUNT = 807
EXPECTED_ANCHOR_COUNT = 5
EXPECTED_USAGE = "train_fit_diagnostic"
EXPECTED_NS3_PREFIX = "ns3-h4-"
EXPECTED_SOURCE_SPLITS = ("train", "validation", "test")
EXPECTED_MASK_MODE = "anchor0_plus_one"
EXPECTED_MASK_SEED = 42

REQUIRED_OUTPUT_FILES = (
    RECORD_LOGICAL_PATH,
    "dataset_manifest.json",
    "source_manifest.json",
    "join_audit.json",
    "materialization_audit.json",
)
REQUIRED_RECORD_FIELDS = frozenset(
    {
        "sample_id",
        "group_id",
        "stable_order",
        "source_split",
        "usage",
        "anchor_times",
        "state_targets",
        "state_mask_inputs",
        "capacity_by_anchor",
        "received_bytes_by_anchor",
        "received_packets_by_anchor",
        "dequeued_bytes_by_anchor",
        "dropped_bytes_by_anchor",
        "normalization_scale",
        "source_record_id",
        "source_file_sha256",
    }
)
PHYSICS_ONLY_FIELDS = REQUIRED_RECORD_FIELDS.difference({"sample_id", "stable_order"})
_SHA256_LENGTH = 64


class SharedB0PhysicsSidecarError(ValueError):
    """共享 B0 物理旁路输入、配置或制品不满足冻结合同。"""


@dataclass(frozen=True)
class PhysicsSourceConfig:
    """单个冻结 ns-3 划分的逻辑路径与哈希绑定。"""

    source_split: str
    path: str
    sha256: str
    expected_count: int


@dataclass(frozen=True)
class SharedB0PhysicsSidecarConfig:
    """已验证且只保存逻辑制品路径的物理旁路配置。"""

    project_root: Path
    config_path: str
    config_sha256: str
    schema_version: str
    dataset_name: str
    stage: str
    status: str
    classification_manifest: str
    ns3_sample_id_prefix: str
    expected_record_count: int
    anchor_count: int
    usage: str
    state_mask_mode: str
    state_mask_seed: int
    sources: tuple[PhysicsSourceConfig, ...]
    output_path: str


@dataclass(frozen=True)
class PhysicsSidecarManifest:
    """一次成功物化的运行时返回值。"""

    output_root: Path
    records_path: Path
    record_count: int
    records_sha256: str
    classification_sha256: str
    dataset_manifest_sha256: str
    source_manifest_sha256: str
    join_audit_sha256: str
    materialization_audit_sha256: str


@dataclass(frozen=True)
class PhysicsSidecarAudit:
    """物理旁路与只读分类清单的连接审计结果。"""

    status: str
    record_count: int
    classification_record_count: int
    classification_ns3_count: int
    classification_sha256: str
    records_sha256: str
    sample_id_sha256: str


@dataclass(frozen=True)
class _ClassificationIndex:
    record_count: int
    sha256: str
    ns3_orders: Mapping[str, int]


@dataclass(frozen=True)
class _SourceRecord:
    value: Mapping[str, object]
    source_split: str
    source_file_sha256: str


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SharedB0PhysicsSidecarError(f"{description}必须是对象")
    return value


def _string(mapping: Mapping[str, object], key: str, description: str) -> str:
    value = str(mapping.get(key, "")).strip()
    if not value:
        raise SharedB0PhysicsSidecarError(f"{description}缺少非空字段：{key}")
    return value


def _integer(mapping: Mapping[str, object], key: str, description: str) -> int:
    raw = mapping.get(key)
    if isinstance(raw, bool):
        raise SharedB0PhysicsSidecarError(f"{description}.{key}必须是非负整数")
    try:
        value = int(raw)
    except (TypeError, ValueError) as error:
        raise SharedB0PhysicsSidecarError(
            f"{description}.{key}必须是非负整数"
        ) from error
    if value < 0 or value != raw:
        raise SharedB0PhysicsSidecarError(f"{description}.{key}必须是非负整数")
    return value


def _logical_path(value: object, description: str) -> str:
    raw = str(value).strip().replace("\\", "/")
    logical = PurePosixPath(raw)
    if not raw or logical.is_absolute() or ".." in logical.parts:
        raise SharedB0PhysicsSidecarError(f"{description}必须是项目相对逻辑路径")
    return logical.as_posix()


def _sha256_value(value: object, description: str) -> str:
    digest = str(value).strip()
    if len(digest) != _SHA256_LENGTH or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise SharedB0PhysicsSidecarError(f"{description}必须是小写 SHA-256")
    return digest


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise SharedB0PhysicsSidecarError(f"无法读取文件：{path}") from error
    return digest.hexdigest()


def _read_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise SharedB0PhysicsSidecarError(f"配置不存在：{path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise SharedB0PhysicsSidecarError(f"无法解析配置：{path}") from error
    if not isinstance(value, dict):
        raise SharedB0PhysicsSidecarError("配置根节点必须是对象")
    return value


def _read_json(path: Path, description: str) -> dict[str, object]:
    if not path.is_file():
        raise SharedB0PhysicsSidecarError(f"{description}不存在：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedB0PhysicsSidecarError(f"{description}不是合法 JSON：{path}") from error
    if not isinstance(value, dict):
        raise SharedB0PhysicsSidecarError(f"{description}根节点必须是对象")
    return value


def _read_jsonl(path: Path, description: str) -> list[dict[str, object]]:
    if not path.is_file():
        raise SharedB0PhysicsSidecarError(f"{description}不存在：{path}")
    rows: list[dict[str, object]] = []
    try:
        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as error:
                    raise SharedB0PhysicsSidecarError(
                        f"{description}第 {line_number} 行不是合法 JSON"
                    ) from error
                if not isinstance(value, dict):
                    raise SharedB0PhysicsSidecarError(
                        f"{description}第 {line_number} 行必须是对象"
                    )
                rows.append(value)
    except OSError as error:
        raise SharedB0PhysicsSidecarError(f"无法读取{description}：{path}") from error
    if not rows:
        raise SharedB0PhysicsSidecarError(f"{description}不得为空")
    return rows


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
        newline="\n",
    )


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(
                json.dumps(
                    row,
                    ensure_ascii=False,
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
            count += 1
    return count


def _project_path(project_root: Path, logical_path: str) -> Path:
    root = project_root.resolve()
    resolved = (root / logical_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise SharedB0PhysicsSidecarError(
            f"逻辑路径越出项目根目录：{logical_path}"
        ) from error
    return resolved


def _project_root_from_bound_file(path: Path, logical_path: str) -> Path:
    resolved = path.expanduser().resolve()
    cursor = resolved
    for part in reversed(PurePosixPath(logical_path).parts):
        if cursor.name != part:
            raise SharedB0PhysicsSidecarError(
                f"运行时文件未绑定逻辑路径：{resolved} != {logical_path}"
            )
        cursor = cursor.parent
    return cursor


def load_shared_b0_physics_sidecar_config(
    path: Path,
) -> SharedB0PhysicsSidecarConfig:
    """加载配置并冻结共享 B0 旁路的路径、计数和用途合同。"""
    config_file = path.expanduser().resolve()
    raw = _read_yaml(config_file)
    if config_file.parent.name != "configs":
        raise SharedB0PhysicsSidecarError("旁路配置必须位于项目 configs 目录")
    project_root = config_file.parent.parent.resolve()
    try:
        config_path = config_file.relative_to(project_root).as_posix()
    except ValueError as error:
        raise SharedB0PhysicsSidecarError("配置不在推导出的项目根目录内") from error

    schema_version = _string(raw, "schema_version", "配置")
    if schema_version != CONFIG_SCHEMA_VERSION:
        raise SharedB0PhysicsSidecarError("旁路配置 schema_version 不合法")
    dataset_name = _string(raw, "dataset_name", "配置")
    if dataset_name != DATASET_NAME:
        raise SharedB0PhysicsSidecarError(f"dataset_name 必须固定为 {DATASET_NAME}")

    classification = _mapping(raw.get("classification"), "classification")
    classification_manifest = _logical_path(
        classification.get("manifest"), "classification.manifest"
    )
    if classification_manifest != CLASSIFICATION_LOGICAL_PATH:
        raise SharedB0PhysicsSidecarError(
            f"分类清单必须固定为 {CLASSIFICATION_LOGICAL_PATH}"
        )
    ns3_prefix = _string(classification, "ns3_sample_id_prefix", "classification")
    if ns3_prefix != EXPECTED_NS3_PREFIX:
        raise SharedB0PhysicsSidecarError(
            f"ns-3 标识前缀必须固定为 {EXPECTED_NS3_PREFIX}"
        )

    contract = _mapping(raw.get("contract"), "contract")
    expected_record_count = _integer(contract, "record_count", "contract")
    anchor_count = _integer(contract, "anchor_count", "contract")
    usage = _string(contract, "usage", "contract")
    if expected_record_count != EXPECTED_RECORD_COUNT:
        raise SharedB0PhysicsSidecarError(
            f"物理记录数必须固定为 {EXPECTED_RECORD_COUNT}"
        )
    if anchor_count != EXPECTED_ANCHOR_COUNT:
        raise SharedB0PhysicsSidecarError(
            f"锚点数必须固定为 {EXPECTED_ANCHOR_COUNT}"
        )
    if usage != EXPECTED_USAGE:
        raise SharedB0PhysicsSidecarError(f"usage 必须固定为 {EXPECTED_USAGE}")

    state_mask = _mapping(raw.get("state_mask"), "state_mask")
    state_mask_mode = _string(state_mask, "mode", "state_mask")
    state_mask_seed = _integer(state_mask, "seed", "state_mask")
    if state_mask_mode != EXPECTED_MASK_MODE or state_mask_seed != EXPECTED_MASK_SEED:
        raise SharedB0PhysicsSidecarError(
            "状态掩码必须固定为 anchor0_plus_one 且种子为 42"
        )

    raw_sources = raw.get("sources")
    if not isinstance(raw_sources, list) or len(raw_sources) != len(EXPECTED_SOURCE_SPLITS):
        raise SharedB0PhysicsSidecarError("sources 必须恰好登记三个冻结 ns-3 划分")
    sources: list[PhysicsSourceConfig] = []
    for index, raw_source in enumerate(raw_sources):
        source = _mapping(raw_source, f"sources[{index}]")
        sources.append(
            PhysicsSourceConfig(
                source_split=_string(source, "split", f"sources[{index}]"),
                path=_logical_path(source.get("path"), f"sources[{index}].path"),
                sha256=_sha256_value(
                    source.get("sha256"), f"sources[{index}].sha256"
                ),
                expected_count=_integer(
                    source, "expected_count", f"sources[{index}]"
                ),
            )
        )
    if tuple(source.source_split for source in sources) != EXPECTED_SOURCE_SPLITS:
        raise SharedB0PhysicsSidecarError(
            "sources 必须按 train、validation、test 顺序登记"
        )
    if any(
        source.expected_count != EXPECTED_SOURCE_RECORD_COUNT for source in sources
    ):
        raise SharedB0PhysicsSidecarError("三个冻结来源必须各登记 807 条记录")
    if sum(source.expected_count for source in sources) != EXPECTED_RECORD_COUNT:
        raise SharedB0PhysicsSidecarError("三个来源 expected_count 之和必须为 2421")
    if len({source.path for source in sources}) != len(sources):
        raise SharedB0PhysicsSidecarError("冻结 ns-3 来源路径不得重复")

    publication = _mapping(raw.get("publication"), "publication")
    output_path = _logical_path(publication.get("output"), "publication.output")
    if output_path != OUTPUT_LOGICAL_PATH:
        raise SharedB0PhysicsSidecarError(f"输出逻辑路径必须固定为 {OUTPUT_LOGICAL_PATH}")

    return SharedB0PhysicsSidecarConfig(
        project_root=project_root,
        config_path=config_path,
        config_sha256=_file_sha256(config_file),
        schema_version=schema_version,
        dataset_name=dataset_name,
        stage=_string(raw, "stage", "配置"),
        status=_string(raw, "status", "配置"),
        classification_manifest=classification_manifest,
        ns3_sample_id_prefix=ns3_prefix,
        expected_record_count=expected_record_count,
        anchor_count=anchor_count,
        usage=usage,
        state_mask_mode=state_mask_mode,
        state_mask_seed=state_mask_seed,
        sources=tuple(sources),
        output_path=output_path,
    )


def _classification_index(
    path: Path,
    *,
    ns3_prefix: str,
    expected_ns3_count: int,
) -> _ClassificationIndex:
    digest = _file_sha256(path)
    rows = _read_jsonl(path, "分类清单")
    sample_ids: set[str] = set()
    ns3_orders: dict[str, int] = {}
    for line_index, row in enumerate(rows):
        sample_id = str(row.get("sample_id", "")).strip()
        if not sample_id:
            raise SharedB0PhysicsSidecarError("分类清单包含空 sample_id")
        if sample_id in sample_ids:
            raise SharedB0PhysicsSidecarError(f"分类清单 sample_id 重复：{sample_id}")
        sample_ids.add(sample_id)
        stable_order = _integer(row, "stable_order", f"分类清单第 {line_index + 1} 行")
        if stable_order != line_index:
            raise SharedB0PhysicsSidecarError("分类清单 stable_order 必须与冻结行序一致")
        prompt = row.get("prompt")
        if not isinstance(prompt, str):
            raise SharedB0PhysicsSidecarError("分类清单 prompt 必须是字符串")
        if any(field in row or field in prompt for field in PHYSICS_ONLY_FIELDS):
            raise SharedB0PhysicsSidecarError("分类提示词或记录混入物理旁路字段")
        if sample_id.startswith(ns3_prefix):
            ns3_orders[sample_id] = stable_order
    if len(ns3_orders) != expected_ns3_count:
        raise SharedB0PhysicsSidecarError(
            f"分类清单中的 ns-3 标识数必须为 {expected_ns3_count}，"
            f"实际为 {len(ns3_orders)}"
        )
    return _ClassificationIndex(
        record_count=len(rows),
        sha256=digest,
        ns3_orders=ns3_orders,
    )


def _load_source_records(
    config: SharedB0PhysicsSidecarConfig,
    expected_ids: set[str],
) -> tuple[dict[str, _SourceRecord], list[dict[str, object]]]:
    records: dict[str, _SourceRecord] = {}
    summaries: list[dict[str, object]] = []
    for source in config.sources:
        path = _project_path(config.project_root, source.path)
        if not path.is_file():
            raise SharedB0PhysicsSidecarError(f"冻结 ns-3 来源不存在：{source.path}")
        actual_sha256 = _file_sha256(path)
        if actual_sha256 != source.sha256:
            raise SharedB0PhysicsSidecarError(f"冻结来源哈希变化：{source.path}")
        rows = _read_jsonl(path, f"冻结 ns-3 来源 {source.path}")
        if len(rows) != source.expected_count:
            raise SharedB0PhysicsSidecarError(
                f"冻结来源记录数变化：{source.path}，"
                f"期望 {source.expected_count}，实际 {len(rows)}"
            )
        for row in rows:
            sample_id = str(row.get("sample_id", "")).strip()
            if not sample_id:
                raise SharedB0PhysicsSidecarError("冻结 ns-3 记录缺少 sample_id")
            if sample_id in records:
                raise SharedB0PhysicsSidecarError(f"冻结来源 sample_id 重复：{sample_id}")
            source_split = str(row.get("split", "")).strip()
            if source_split != source.source_split:
                raise SharedB0PhysicsSidecarError(
                    f"冻结来源 source_split 错配：{sample_id}"
                )
            records[sample_id] = _SourceRecord(
                value=row,
                source_split=source.source_split,
                source_file_sha256=actual_sha256,
            )
        summaries.append(
            {
                "path": source.path,
                "record_count": len(rows),
                "selected_record_count": len(rows),
                "sha256": actual_sha256,
                "source_split": source.source_split,
            }
        )
    actual_ids = set(records)
    missing = sorted(expected_ids.difference(actual_ids))
    extra = sorted(actual_ids.difference(expected_ids))
    if missing or extra:
        detail = missing[0] if missing else extra[0]
        raise SharedB0PhysicsSidecarError(
            "分类清单与物理来源 sample_id 集合错配："
            f"missing={len(missing)} extra={len(extra)} example={detail}"
        )
    if len(records) != config.expected_record_count:
        raise SharedB0PhysicsSidecarError(
            f"物理来源记录数必须为 {config.expected_record_count}"
        )
    return records, summaries


def _finite_number(value: object, description: str) -> float:
    if isinstance(value, bool):
        raise SharedB0PhysicsSidecarError(f"{description}必须是有限数值")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise SharedB0PhysicsSidecarError(f"{description}必须是有限数值") from error
    if not math.isfinite(number):
        raise SharedB0PhysicsSidecarError(f"{description}包含非有限数值")
    return number


def _numeric_list(value: object, length: int, description: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise SharedB0PhysicsSidecarError(f"{description}必须是长度为 {length} 的列表")
    return [_finite_number(item, description) for item in value]


def _section_list(
    record: Mapping[str, object],
    section: str,
    field: str,
    length: int,
) -> list[float]:
    values = _mapping(record.get(section), f"ns-3 {section}")
    return _numeric_list(values.get(field), length, f"ns-3 {section}.{field}")


def _cumulative(values: Sequence[float], description: str) -> list[float]:
    cumulative = [0.0]
    total = 0.0
    for value in values:
        total += value
        if not math.isfinite(total):
            raise SharedB0PhysicsSidecarError(f"{description}累计后包含非有限数值")
        cumulative.append(total)
    return cumulative


def _build_state_masks(
    records: Mapping[str, _SourceRecord], seed: int
) -> dict[str, tuple[bool, bool, bool, bool, bool]]:
    masks: dict[str, tuple[bool, bool, bool, bool, bool]] = {}
    for sample_id, source in records.items():
        group_id = str(source.value.get("group_id", "")).strip()
        if not group_id:
            raise SharedB0PhysicsSidecarError(f"物理记录缺少 group_id：{sample_id}")
        digest = hashlib.sha256(f"{seed}:{sample_id}".encode("utf-8")).digest()
        second_anchor = int.from_bytes(digest, "big") % (EXPECTED_ANCHOR_COUNT - 1) + 1
        masks[sample_id] = tuple(
            index in {0, second_anchor} for index in range(EXPECTED_ANCHOR_COUNT)
        )
    return masks


def _physics_record(
    *,
    sample_id: str,
    stable_order: int,
    source: _SourceRecord,
    state_mask: Sequence[bool],
    usage: str,
) -> dict[str, object]:
    record = source.value
    anchor_values = _numeric_list(
        record.get("queue_boundary_anchors_l3_bytes"),
        EXPECTED_ANCHOR_COUNT,
        "ns-3 queue_boundary_anchors_l3_bytes",
    )
    window_starts = _section_list(record, "metadata", "window_start_s", 4)
    window_ends = _section_list(record, "metadata", "window_end_s", 4)
    for index, (start, end) in enumerate(zip(window_starts, window_ends, strict=True)):
        if start >= end:
            raise SharedB0PhysicsSidecarError(
                f"非法锚点区间：{sample_id} window={index}"
            )
        if index and not math.isclose(start, window_ends[index - 1], abs_tol=1e-12):
            raise SharedB0PhysicsSidecarError(f"锚点区间不连续：{sample_id}")
    anchor_times = [window_starts[0], *window_ends]
    if any(
        current >= following
        for current, following in zip(anchor_times, anchor_times[1:], strict=False)
    ):
        raise SharedB0PhysicsSidecarError(f"锚点时间未严格递增：{sample_id}")

    capacity = _section_list(
        record,
        "model_inputs",
        "configured_capacity_integral_link_bytes",
        4,
    )
    if any(value <= 0 for value in capacity):
        raise SharedB0PhysicsSidecarError(f"容量积分必须严格为正：{sample_id}")
    scales = _numeric_list(
        record.get("normalization_scale_configured_capacity_integral_link_bytes"),
        4,
        "ns-3 normalization_scale_configured_capacity_integral_link_bytes",
    )
    if any(value <= 0 for value in scales):
        raise SharedB0PhysicsSidecarError(f"归一化尺度必须严格为正：{sample_id}")
    if scales != capacity:
        raise SharedB0PhysicsSidecarError(f"归一化尺度与容量积分错配：{sample_id}")
    normalization_scale = max(scales)

    received_bytes = _section_list(
        record, "model_inputs", "qdisc_received_l3_bytes", 4
    )
    received_packets = _section_list(
        record, "model_inputs", "qdisc_received_packets", 4
    )
    dequeued_bytes = _section_list(
        record, "state_supervision", "qdisc_dequeued_l3_bytes", 4
    )
    dropped_before = _section_list(
        record,
        "state_supervision",
        "qdisc_dropped_before_enqueue_l3_bytes",
        4,
    )
    dropped_after = _section_list(
        record,
        "state_supervision",
        "qdisc_dropped_after_dequeue_l3_bytes",
        4,
    )
    dropped_bytes = [
        before + after
        for before, after in zip(dropped_before, dropped_after, strict=True)
    ]

    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "sample_id": sample_id,
        "group_id": str(record["group_id"]),
        "stable_order": stable_order,
        "source_split": source.source_split,
        "usage": usage,
        "anchor_times": anchor_times,
        "state_targets": [value / normalization_scale for value in anchor_values],
        "state_mask_inputs": list(state_mask),
        "capacity_by_anchor": _cumulative(capacity, "容量积分"),
        "received_bytes_by_anchor": _cumulative(received_bytes, "接收字节"),
        "received_packets_by_anchor": _cumulative(received_packets, "接收包数"),
        "dequeued_bytes_by_anchor": _cumulative(dequeued_bytes, "出队字节"),
        "dropped_bytes_by_anchor": _cumulative(dropped_bytes, "丢弃字节"),
        "normalization_scale": normalization_scale,
        "source_record_id": sample_id,
        "source_file_sha256": source.source_file_sha256,
    }


def _sample_id_sha256(sample_ids: Sequence[str]) -> str:
    payload = json.dumps(
        list(sample_ids), ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _artifact_entry(path: Path, record_count: int | None = None) -> dict[str, object]:
    entry: dict[str, object] = {
        "sha256": _file_sha256(path),
        "size_bytes": path.stat().st_size,
    }
    if record_count is not None:
        entry["record_count"] = record_count
    return entry


def materialize_shared_b0_physics_sidecar(
    config: SharedB0PhysicsSidecarConfig,
    output_root: Path,
) -> PhysicsSidecarManifest:
    """从冻结分类清单和 ns-3 来源原子物化确定性物理旁路。"""
    runtime_output = output_root.expanduser()
    if not runtime_output.is_absolute():
        raise SharedB0PhysicsSidecarError("运行时输出根必须是绝对路径")
    if runtime_output.is_symlink():
        raise SharedB0PhysicsSidecarError(f"输出根不得是符号链接：{runtime_output}")
    output = runtime_output.resolve()
    partial = output.with_name(output.name + ".partial")
    if output.exists():
        if not output.is_dir() or any(output.iterdir()):
            raise SharedB0PhysicsSidecarError(f"输出目录非空，拒绝覆盖：{output}")
    if partial.exists() or partial.is_symlink():
        raise SharedB0PhysicsSidecarError(f"未完成目录已存在，拒绝覆盖：{partial}")

    classification_path = _project_path(
        config.project_root, config.classification_manifest
    )
    classification_before = _classification_index(
        classification_path,
        ns3_prefix=config.ns3_sample_id_prefix,
        expected_ns3_count=config.expected_record_count,
    )
    sources, source_summaries = _load_source_records(
        config, set(classification_before.ns3_orders)
    )
    state_masks = _build_state_masks(sources, config.state_mask_seed)
    ordered_ids = sorted(
        classification_before.ns3_orders,
        key=classification_before.ns3_orders.__getitem__,
    )
    records = [
        _physics_record(
            sample_id=sample_id,
            stable_order=classification_before.ns3_orders[sample_id],
            source=sources[sample_id],
            state_mask=state_masks[sample_id],
            usage=config.usage,
        )
        for sample_id in ordered_ids
    ]
    if len(records) != config.expected_record_count:
        raise SharedB0PhysicsSidecarError("物理旁路物化记录数不是 2421")

    partial.parent.mkdir(parents=True, exist_ok=True)
    partial.mkdir()
    try:
        records_path = partial / RECORD_LOGICAL_PATH
        written_count = _write_jsonl(records_path, records)
        if written_count != config.expected_record_count:
            raise SharedB0PhysicsSidecarError("物理旁路写入记录数不是 2421")

        source_manifest = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "classification": {
                "path": config.classification_manifest,
                "record_count": classification_before.record_count,
                "ns3_record_count": len(classification_before.ns3_orders),
                "sha256": classification_before.sha256,
            },
            "config": {
                "path": config.config_path,
                "sha256": config.config_sha256,
            },
            "sources": source_summaries,
        }
        _write_json(partial / "source_manifest.json", source_manifest)

        join_audit = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "status": "passed",
            "join_key": "sample_id",
            "classification_record_count": classification_before.record_count,
            "classification_ns3_count": len(classification_before.ns3_orders),
            "source_record_count": len(sources),
            "sidecar_record_count": len(records),
            "missing_id_count": 0,
            "extra_id_count": 0,
            "duplicate_id_count": 0,
            "stable_order_mismatch_count": 0,
            "sample_id_sha256": _sample_id_sha256(ordered_ids),
            "classification_sha256": classification_before.sha256,
            "prohibited_join_keys": [
                "row_number",
                "batch_position",
                "prompt",
                "label",
                "scenario_name",
            ],
        }
        _write_json(partial / "join_audit.json", join_audit)

        candidate_entry = _artifact_entry(records_path, len(records))
        source_entry = _artifact_entry(partial / "source_manifest.json")
        join_entry = _artifact_entry(partial / "join_audit.json")
        dataset_manifest = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "dataset_name": config.dataset_name,
            "stage": config.stage,
            "status": config.status,
            "usage": config.usage,
            "configured_output": config.output_path,
            "classification_manifest": config.classification_manifest,
            "classification_sha256": classification_before.sha256,
            "ns3_sample_id_prefix": config.ns3_sample_id_prefix,
            "record_count": len(records),
            "anchor_count": config.anchor_count,
            "state_mask": {
                "mode": config.state_mask_mode,
                "seed": config.state_mask_seed,
            },
            "field_semantics": {
                "anchor_times": "five_contiguous_window_boundaries_seconds",
                "state_targets": "queue_l3_bytes_divided_by_normalization_scale",
                "state_mask_inputs": "deterministic_anchor0_plus_one_boolean_mask",
                "capacity_by_anchor": "cumulative_configured_capacity_integral_link_bytes",
                "received_bytes_by_anchor": "cumulative_qdisc_received_l3_bytes",
                "received_packets_by_anchor": "cumulative_qdisc_received_packets",
                "dequeued_bytes_by_anchor": "cumulative_qdisc_dequeued_l3_bytes",
                "dropped_bytes_by_anchor": (
                    "cumulative_qdisc_dropped_before_plus_after_l3_bytes"
                ),
            },
            "record_fields": sorted(REQUIRED_RECORD_FIELDS),
            "artifacts": {
                RECORD_LOGICAL_PATH: candidate_entry,
                "source_manifest.json": source_entry,
                "join_audit.json": join_entry,
            },
        }
        _write_json(partial / "dataset_manifest.json", dataset_manifest)

        classification_after_sha256 = _file_sha256(classification_path)
        if classification_after_sha256 != classification_before.sha256:
            raise SharedB0PhysicsSidecarError("物化期间冻结分类清单哈希发生变化")
        materialization_artifacts = {
            relative: _artifact_entry(partial / relative)
            for relative in (
                RECORD_LOGICAL_PATH,
                "dataset_manifest.json",
                "source_manifest.json",
                "join_audit.json",
            )
        }
        materialization_audit = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "status": "passed",
            "classification_sha256_before": classification_before.sha256,
            "classification_sha256_after": classification_after_sha256,
            "classification_unchanged": True,
            "classification_copied": False,
            "physics_fields_added_to_prompt": False,
            "deterministic_serialization": {
                "encoding": "utf-8",
                "json_key_order": "sorted",
                "jsonl_line_ending": "lf",
                "timestamps_embedded": False,
                "absolute_paths_embedded": False,
            },
            "required_files": list(REQUIRED_OUTPUT_FILES),
            "artifacts": materialization_artifacts,
        }
        _write_json(partial / "materialization_audit.json", materialization_audit)

        audit = validate_shared_b0_physics_sidecar(partial, classification_path)
        if audit.status != "passed":
            raise SharedB0PhysicsSidecarError("物化后的旁路审计未通过")
        if output.is_symlink() or (
            output.exists() and (not output.is_dir() or any(output.iterdir()))
        ):
            raise SharedB0PhysicsSidecarError(f"输出路径在物化期间被占用：{output}")
        partial.replace(output)
    except Exception:
        if partial.is_dir() and not partial.is_symlink():
            shutil.rmtree(partial)
        raise

    return PhysicsSidecarManifest(
        output_root=output,
        records_path=output / RECORD_LOGICAL_PATH,
        record_count=len(records),
        records_sha256=_file_sha256(output / RECORD_LOGICAL_PATH),
        classification_sha256=classification_before.sha256,
        dataset_manifest_sha256=_file_sha256(output / "dataset_manifest.json"),
        source_manifest_sha256=_file_sha256(output / "source_manifest.json"),
        join_audit_sha256=_file_sha256(output / "join_audit.json"),
        materialization_audit_sha256=_file_sha256(
            output / "materialization_audit.json"
        ),
    )


def _manifest_artifact(
    artifacts: Mapping[str, object], relative_path: str, path: Path
) -> Mapping[str, object]:
    entry = _mapping(artifacts.get(relative_path), f"制品登记 {relative_path}")
    expected = _sha256_value(entry.get("sha256"), f"制品登记 {relative_path}.sha256")
    actual = _file_sha256(path)
    if actual != expected:
        raise SharedB0PhysicsSidecarError(f"旁路制品哈希不一致：{relative_path}")
    size_bytes = _integer(entry, "size_bytes", f"制品登记 {relative_path}")
    if size_bytes != path.stat().st_size:
        raise SharedB0PhysicsSidecarError(f"旁路制品大小不一致：{relative_path}")
    return entry


def _validate_output_tree(output: Path) -> None:
    try:
        root_status = output.lstat()
    except OSError as error:
        raise SharedB0PhysicsSidecarError(f"旁路输出根不存在：{output}") from error
    if stat.S_ISLNK(root_status.st_mode):
        raise SharedB0PhysicsSidecarError(f"旁路输出根不得是符号链接：{output}")
    if not stat.S_ISDIR(root_status.st_mode):
        raise SharedB0PhysicsSidecarError(f"旁路输出根不是目录：{output}")

    files: set[str] = set()
    directories: set[str] = set()
    pending = [output]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    relative = Path(entry.path).relative_to(output).as_posix()
                    entry_status = entry.stat(follow_symlinks=False)
                    if stat.S_ISLNK(entry_status.st_mode):
                        raise SharedB0PhysicsSidecarError(
                            f"旁路输出不得包含符号链接：{relative}"
                        )
                    if stat.S_ISREG(entry_status.st_mode):
                        files.add(relative)
                    elif stat.S_ISDIR(entry_status.st_mode):
                        directories.add(relative)
                        pending.append(Path(entry.path))
                    else:
                        raise SharedB0PhysicsSidecarError(
                            f"旁路输出包含非普通文件：{relative}"
                        )
        except SharedB0PhysicsSidecarError:
            raise
        except OSError as error:
            raise SharedB0PhysicsSidecarError(
                f"无法检查旁路输出目录：{directory}"
            ) from error

    expected_files = set(REQUIRED_OUTPUT_FILES)
    if files != expected_files:
        missing = sorted(expected_files.difference(files))
        extra = sorted(files.difference(expected_files))
        raise SharedB0PhysicsSidecarError(
            "旁路最终普通文件集合不合法："
            f"missing={len(missing)} extra={len(extra)}"
        )

    expected_directories: set[str] = set()
    for relative in REQUIRED_OUTPUT_FILES:
        parent = PurePosixPath(relative).parent
        while parent != PurePosixPath("."):
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    if directories != expected_directories:
        raise SharedB0PhysicsSidecarError("旁路最终目录集合不合法")


def _validated_output_record(
    row: Mapping[str, object],
    *,
    classification_orders: Mapping[str, int],
    source_hashes: Mapping[str, str],
) -> str:
    missing_fields = REQUIRED_RECORD_FIELDS.difference(row)
    if missing_fields:
        raise SharedB0PhysicsSidecarError(
            f"物理记录缺少字段：{', '.join(sorted(missing_fields))}"
        )
    sample_id = str(row.get("sample_id", "")).strip()
    if not sample_id:
        raise SharedB0PhysicsSidecarError("物理记录 sample_id 不得为空")
    stable_order = _integer(row, "stable_order", f"物理记录 {sample_id}")
    if classification_orders.get(sample_id) != stable_order:
        raise SharedB0PhysicsSidecarError(f"物理记录 stable_order 错配：{sample_id}")
    if str(row.get("source_record_id", "")).strip() != sample_id:
        raise SharedB0PhysicsSidecarError(f"物理记录 source_record_id 错配：{sample_id}")
    if not str(row.get("group_id", "")).strip():
        raise SharedB0PhysicsSidecarError(f"物理记录 group_id 不得为空：{sample_id}")
    if row.get("usage") != EXPECTED_USAGE:
        raise SharedB0PhysicsSidecarError(f"物理记录用途错误：{sample_id}")
    source_split = str(row.get("source_split", "")).strip()
    if source_split not in source_hashes:
        raise SharedB0PhysicsSidecarError(f"物理记录 source_split 非法：{sample_id}")
    if row.get("source_file_sha256") != source_hashes[source_split]:
        raise SharedB0PhysicsSidecarError(f"物理记录来源哈希错配：{sample_id}")

    anchor_times = _numeric_list(
        row.get("anchor_times"), EXPECTED_ANCHOR_COUNT, "anchor_times"
    )
    if any(
        current >= following
        for current, following in zip(anchor_times, anchor_times[1:], strict=False)
    ):
        raise SharedB0PhysicsSidecarError(f"锚点时间未严格递增：{sample_id}")
    for field in (
        "state_targets",
        "capacity_by_anchor",
        "received_bytes_by_anchor",
        "received_packets_by_anchor",
        "dequeued_bytes_by_anchor",
        "dropped_bytes_by_anchor",
    ):
        _numeric_list(row.get(field), EXPECTED_ANCHOR_COUNT, field)
    mask = row.get("state_mask_inputs")
    if (
        not isinstance(mask, list)
        or len(mask) != EXPECTED_ANCHOR_COUNT
        or any(not isinstance(value, bool) for value in mask)
        or mask[0] is not True
        or sum(mask) != 2
    ):
        raise SharedB0PhysicsSidecarError(
            f"state_mask_inputs 必须严格为锚点 0 加一个其他锚点：{sample_id}"
        )
    scale = _finite_number(row.get("normalization_scale"), "normalization_scale")
    if scale <= 0:
        raise SharedB0PhysicsSidecarError(f"normalization_scale 必须严格为正：{sample_id}")
    return sample_id


def _validate_record_semantics(
    row: Mapping[str, object], expected: Mapping[str, object], sample_id: str
) -> None:
    for field in sorted(REQUIRED_RECORD_FIELDS):
        if row.get(field) != expected[field]:
            raise SharedB0PhysicsSidecarError(
                f"物理记录与冻结来源语义错配：{sample_id} field={field}"
            )


def validate_shared_b0_physics_sidecar(
    output_root: Path,
    classification_manifest: Path,
) -> PhysicsSidecarAudit:
    """独立复核旁路、冻结来源与分类清单的 sample_id 连接。"""
    output = Path(os.path.abspath(output_root.expanduser()))
    classification_path = classification_manifest.expanduser().resolve()
    _validate_output_tree(output)
    partial = output.with_name(output.name + ".partial")
    if partial.exists() or partial.is_symlink():
        raise SharedB0PhysicsSidecarError(f"旁路输出存在遗留未完成目录：{partial}")
    if (output / CLASSIFICATION_LOGICAL_PATH).exists() or (
        output / "candidate" / "qwen_train.jsonl"
    ).exists():
        raise SharedB0PhysicsSidecarError("旁路输出不得复制分类清单")

    dataset = _read_json(output / "dataset_manifest.json", "dataset_manifest")
    source_manifest = _read_json(output / "source_manifest.json", "source_manifest")
    join_audit = _read_json(output / "join_audit.json", "join_audit")
    materialization = _read_json(
        output / "materialization_audit.json", "materialization_audit"
    )
    for description, manifest in (
        ("dataset_manifest", dataset),
        ("source_manifest", source_manifest),
        ("join_audit", join_audit),
        ("materialization_audit", materialization),
    ):
        if manifest.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
            raise SharedB0PhysicsSidecarError(f"{description} schema_version 不合法")
    if join_audit.get("status") != "passed" or materialization.get("status") != "passed":
        raise SharedB0PhysicsSidecarError("旁路审计状态不是 passed")
    if dataset.get("dataset_name") != DATASET_NAME:
        raise SharedB0PhysicsSidecarError("dataset_manifest 数据集名称不合法")
    if dataset.get("usage") != EXPECTED_USAGE:
        raise SharedB0PhysicsSidecarError("dataset_manifest 用途不合法")
    if dataset.get("record_count") != EXPECTED_RECORD_COUNT:
        raise SharedB0PhysicsSidecarError("dataset_manifest 记录数不是 2421")
    if dataset.get("anchor_count") != EXPECTED_ANCHOR_COUNT:
        raise SharedB0PhysicsSidecarError("dataset_manifest 锚点数不是 5")

    classification_logical = _logical_path(
        dataset.get("classification_manifest"),
        "dataset_manifest.classification_manifest",
    )
    if classification_logical != CLASSIFICATION_LOGICAL_PATH:
        raise SharedB0PhysicsSidecarError("dataset_manifest 分类清单路径不合法")
    project_root = _project_root_from_bound_file(
        classification_path, classification_logical
    )
    config_entry = _mapping(source_manifest.get("config"), "source_manifest.config")
    config_logical = _logical_path(
        config_entry.get("path"), "source_manifest.config.path"
    )
    config_path = _project_path(project_root, config_logical)
    recorded_config_sha256 = _sha256_value(
        config_entry.get("sha256"), "source_manifest.config.sha256"
    )
    if _file_sha256(config_path) != recorded_config_sha256:
        raise SharedB0PhysicsSidecarError("旁路配置哈希变化")
    config = load_shared_b0_physics_sidecar_config(config_path)
    if (
        config.project_root != project_root
        or config.config_path != config_logical
        or config.config_sha256 != recorded_config_sha256
        or dict(config_entry)
        != {"path": config.config_path, "sha256": config.config_sha256}
    ):
        raise SharedB0PhysicsSidecarError("source_manifest 配置绑定错配")
    if (
        classification_logical != config.classification_manifest
        or dataset.get("configured_output") != config.output_path
        or dataset.get("dataset_name") != config.dataset_name
        or dataset.get("stage") != config.stage
        or dataset.get("status") != config.status
        or dataset.get("usage") != config.usage
        or dataset.get("record_count") != config.expected_record_count
        or dataset.get("anchor_count") != config.anchor_count
        or dataset.get("ns3_sample_id_prefix") != config.ns3_sample_id_prefix
        or dataset.get("state_mask")
        != {"mode": config.state_mask_mode, "seed": config.state_mask_seed}
    ):
        raise SharedB0PhysicsSidecarError("dataset_manifest 与真实配置不一致")

    classification = _classification_index(
        classification_path,
        ns3_prefix=config.ns3_sample_id_prefix,
        expected_ns3_count=config.expected_record_count,
    )
    recorded_classification_sha256 = _sha256_value(
        dataset.get("classification_sha256"),
        "dataset_manifest.classification_sha256",
    )
    if classification.sha256 != recorded_classification_sha256:
        raise SharedB0PhysicsSidecarError("冻结分类清单哈希变化")

    source_classification = _mapping(
        source_manifest.get("classification"), "source_manifest.classification"
    )
    expected_source_classification = {
        "path": config.classification_manifest,
        "record_count": classification.record_count,
        "ns3_record_count": len(classification.ns3_orders),
        "sha256": classification.sha256,
    }
    if dict(source_classification) != expected_source_classification:
        raise SharedB0PhysicsSidecarError("source_manifest 分类绑定错配")

    raw_sources = source_manifest.get("sources")
    if not isinstance(raw_sources, list):
        raise SharedB0PhysicsSidecarError("source_manifest 来源登记不完整")
    source_records, source_summaries = _load_source_records(
        config, set(classification.ns3_orders)
    )
    if raw_sources != source_summaries:
        raise SharedB0PhysicsSidecarError("source_manifest 来源登记与真实配置不一致")
    source_hashes = {
        source.source_split: source.sha256 for source in config.sources
    }
    state_masks = _build_state_masks(source_records, config.state_mask_seed)

    rows = _read_jsonl(output / RECORD_LOGICAL_PATH, "物理旁路记录")
    if len(rows) != EXPECTED_RECORD_COUNT:
        raise SharedB0PhysicsSidecarError("物理旁路记录数不是 2421")
    sample_ids: list[str] = []
    seen: set[str] = set()
    for row in rows:
        sample_id = _validated_output_record(
            row,
            classification_orders=classification.ns3_orders,
            source_hashes=source_hashes,
        )
        if sample_id in seen:
            raise SharedB0PhysicsSidecarError(f"物理旁路 sample_id 重复：{sample_id}")
        expected_record = _physics_record(
            sample_id=sample_id,
            stable_order=classification.ns3_orders[sample_id],
            source=source_records[sample_id],
            state_mask=state_masks[sample_id],
            usage=config.usage,
        )
        _validate_record_semantics(row, expected_record, sample_id)
        seen.add(sample_id)
        sample_ids.append(sample_id)
    expected_ids = set(classification.ns3_orders)
    missing = sorted(expected_ids.difference(seen))
    extra = sorted(seen.difference(expected_ids))
    if missing or extra:
        raise SharedB0PhysicsSidecarError(
            "分类清单与物理旁路 sample_id 集合错配："
            f"missing={len(missing)} extra={len(extra)}"
        )
    expected_order = sorted(
        expected_ids, key=classification.ns3_orders.__getitem__
    )
    if sample_ids != expected_order:
        raise SharedB0PhysicsSidecarError("物理旁路未保持分类清单的 sample_id 顺序")

    dataset_artifacts = _mapping(dataset.get("artifacts"), "dataset_manifest.artifacts")
    candidate_entry = _manifest_artifact(
        dataset_artifacts,
        RECORD_LOGICAL_PATH,
        output / RECORD_LOGICAL_PATH,
    )
    if candidate_entry.get("record_count") != EXPECTED_RECORD_COUNT:
        raise SharedB0PhysicsSidecarError("候选旁路登记记录数不是 2421")
    _manifest_artifact(
        dataset_artifacts, "source_manifest.json", output / "source_manifest.json"
    )
    _manifest_artifact(dataset_artifacts, "join_audit.json", output / "join_audit.json")
    materialization_artifacts = _mapping(
        materialization.get("artifacts"), "materialization_audit.artifacts"
    )
    if materialization.get("required_files") != list(REQUIRED_OUTPUT_FILES):
        raise SharedB0PhysicsSidecarError("物化审计的必要文件集合不合法")
    for relative_path in (
        RECORD_LOGICAL_PATH,
        "dataset_manifest.json",
        "source_manifest.json",
        "join_audit.json",
    ):
        _manifest_artifact(
            materialization_artifacts, relative_path, output / relative_path
        )
    if materialization.get("classification_sha256_before") != classification.sha256 or (
        materialization.get("classification_sha256_after") != classification.sha256
    ):
        raise SharedB0PhysicsSidecarError("物化审计中的分类哈希前后不一致")
    if materialization.get("classification_unchanged") is not True:
        raise SharedB0PhysicsSidecarError("物化审计未证明分类清单保持不变")
    if join_audit.get("join_key") != "sample_id":
        raise SharedB0PhysicsSidecarError("旁路连接键必须严格为 sample_id")
    if join_audit.get("sample_id_sha256") != _sample_id_sha256(sample_ids):
        raise SharedB0PhysicsSidecarError("连接审计的 sample_id 顺序哈希不一致")

    return PhysicsSidecarAudit(
        status="passed",
        record_count=len(rows),
        classification_record_count=classification.record_count,
        classification_ns3_count=len(classification.ns3_orders),
        classification_sha256=classification.sha256,
        records_sha256=_file_sha256(output / RECORD_LOGICAL_PATH),
        sample_id_sha256=_sample_id_sha256(sample_ids),
    )
