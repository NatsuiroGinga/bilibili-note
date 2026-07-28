"""将 GeNIS 前向时间划分物化为理论筛选候选协议。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yaml

PROTOCOL_VERSION = "data-protocol-v1.0-rc1"
PROTOCOL_STATUS = "provisional"
PROTOCOL_PHASE = "theory_selection"
REVIEW_STATUS = "review_pending"
CANDIDATE_ID = "dataset-candidate-genis-v0"
TREE_VIEW_NAME = "tree_flat_view"
FAMILY_SUITE_ID = "genis_family_development"
SUBTYPE_SUITE_ID = "genis_subtype_development"
OPEN_SET_SUITE_ID = "genis_subtype_open_set"

KNOWN_SUBTYPES = frozenset(
    {
        "benign-admin",
        "benign-background",
        "benign-user",
        "bruteforce-ftp",
        "bruteforce-smb",
        "bruteforce-ssh",
        "dos-hulk",
        "dos-slowloris",
    }
)
UNKNOWN_SUBTYPES = frozenset({"dos-icmp", "dos-pushack", "dos-udp"})
FAMILY_LABELS = frozenset({"benign", "bruteforce", "dos"})

OBSERVATION_FIELDS = (
    "total_packets",
    "total_bytes",
    "packet_length_mean",
    "packet_length_min",
    "packet_length_max",
    "iat_mean_ms",
    "packet_rate",
    "byte_rate",
)
MISSING_MASK_FIELDS = tuple(f"{field}_missing" for field in OBSERVATION_FIELDS)
MODEL_FEATURE_FIELDS = (*OBSERVATION_FIELDS, *MISSING_MASK_FIELDS)

INPUT_FILES = (
    ("train", "train.jsonl", "train", "development"),
    ("validation", "validation.jsonl", "validation", "development"),
    ("test", "test.jsonl", "test", "evaluation_only"),
    ("ood:dos-icmp", "ood_dos-icmp.jsonl", "open_set_test", "evaluation_only"),
    ("ood:dos-pushack", "ood_dos-pushack.jsonl", "open_set_test", "evaluation_only"),
    ("ood:dos-udp", "ood_dos-udp.jsonl", "open_set_test", "evaluation_only"),
)

SPLIT_SPECS = (
    (
        "splits/genis-family-development-train.jsonl",
        FAMILY_SUITE_ID,
        "train",
        "train",
    ),
    (
        "splits/genis-family-development-validation.jsonl",
        FAMILY_SUITE_ID,
        "validation",
        "validation",
    ),
    (
        "splits/genis-family-time-forward-test.jsonl",
        FAMILY_SUITE_ID,
        "test",
        "test",
    ),
    (
        "splits/genis-subtype-development-train.jsonl",
        SUBTYPE_SUITE_ID,
        "train",
        "train",
    ),
    (
        "splits/genis-subtype-development-validation.jsonl",
        SUBTYPE_SUITE_ID,
        "validation",
        "validation",
    ),
    (
        "splits/genis-subtype-time-forward-test.jsonl",
        SUBTYPE_SUITE_ID,
        "test",
        "test",
    ),
    (
        "splits/genis-subtype-open-set-test.jsonl",
        OPEN_SET_SUITE_ID,
        "test",
        "open_set_test",
    ),
)

SAMPLE_METADATA_FIELDS = (
    "protocol_version",
    "protocol_status",
    "protocol_phase",
    "candidate_id",
    "sample_id",
    "candidate_record_sha256",
    "source_record_sha256",
    "observation_sha256",
    "source_dataset",
    "group_id",
    "source_partition",
    "split_id",
    "domain_role",
    "development_eligible",
    "exclusion_reason",
    "binary_label",
    "family_label",
    "subtype_label",
)
SAMPLE_COLUMNS = (*SAMPLE_METADATA_FIELDS, *MODEL_FEATURE_FIELDS)
_SESSION_ID_PATTERN = re.compile(r"[0-9a-f]{32}")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class GeNISCandidateError(ValueError):
    """GeNIS 候选协议输入、标签、划分或制品不满足固定合同。"""


@dataclass(frozen=True)
class _AssignmentRecord:
    session_id: str
    assignment: str
    subtype: str
    binary_label: str
    start_time: float
    last_time: float
    row_count: int


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise GeNISCandidateError("记录包含无法规范化的 JSON 值") from error


def _stable_hash(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as output:
        for row in rows:
            output.write(_canonical_json(row) + "\n")


def _write_yaml(path: Path, value: Mapping[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(dict(value), allow_unicode=True, sort_keys=True),
        encoding="utf-8",
    )


def _read_json_object(path: Path, description: str) -> dict[str, object]:
    if not path.is_file():
        raise GeNISCandidateError(f"缺少{description}：{path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise GeNISCandidateError(f"{description}不是合法 JSON：{path.name}") from error
    if not isinstance(value, dict):
        raise GeNISCandidateError(f"{description}根节点必须是对象：{path.name}")
    return value


def _required_string(value: Mapping[str, object], key: str, description: str) -> str:
    result = str(value.get(key, "")).strip()
    if not result:
        raise GeNISCandidateError(f"{description}缺少非空字段：{key}")
    return result


def _required_finite_float(value: Mapping[str, object], key: str, description: str) -> float:
    raw_value = value.get(key)
    if isinstance(raw_value, bool):
        raise GeNISCandidateError(f"{description}的 {key} 必须是有限数")
    try:
        result = float(raw_value)
    except (TypeError, ValueError) as error:
        raise GeNISCandidateError(f"{description}的 {key} 必须是有限数") from error
    if not math.isfinite(result):
        raise GeNISCandidateError(f"{description}的 {key} 必须是有限数")
    return result


def _family_for_subtype(subtype: str) -> str:
    for prefix, family in (
        ("benign-", "benign"),
        ("bruteforce-", "bruteforce"),
        ("dos-", "dos"),
    ):
        if subtype.startswith(prefix):
            return family
    raise GeNISCandidateError(f"无法从绑定子类确定攻击家族：{subtype}")


def _binary_for_family(family: str) -> str:
    return "benign" if family == "benign" else "malicious"


def _normalise_source_files(
    summary: Mapping[str, object], description: str
) -> tuple[dict[str, object], ...]:
    raw_rows = summary.get("source_files")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise GeNISCandidateError(f"{description}缺少非空 source_files")
    rows: list[dict[str, object]] = []
    names: set[str] = set()
    for index, raw_row in enumerate(raw_rows, start=1):
        if not isinstance(raw_row, Mapping):
            raise GeNISCandidateError(f"{description}的 source_files 第 {index} 行不是对象")
        name = _required_string(raw_row, "name", f"{description}来源行")
        if "/" in name or "\\" in name or name in names:
            raise GeNISCandidateError(f"{description}包含非法或重复来源文件名：{name}")
        digest = _required_string(raw_row, "sha256", f"{description}来源行")
        if _SHA256_PATTERN.fullmatch(digest) is None:
            raise GeNISCandidateError(f"{description}来源 SHA-256 不合法：{name}")
        try:
            size_bytes = int(raw_row.get("size_bytes", -1))
        except (TypeError, ValueError) as error:
            raise GeNISCandidateError(f"{description}来源大小不合法：{name}") from error
        if size_bytes < 0:
            raise GeNISCandidateError(f"{description}来源大小不合法：{name}")
        names.add(name)
        rows.append({"name": name, "sha256": digest, "size_bytes": size_bytes})
    return tuple(sorted(rows, key=lambda row: str(row["name"])))


def _load_assignments(path: Path) -> dict[str, _AssignmentRecord]:
    if not path.is_file():
        raise GeNISCandidateError(f"缺少会话分配文件：{path.name}")
    allowed_assignments = {
        "train",
        "validation",
        "test",
        "purged",
        *(f"ood:{subtype}" for subtype in UNKNOWN_SUBTYPES),
    }
    assignments: dict[str, _AssignmentRecord] = {}
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise GeNISCandidateError(f"会话分配第 {line_number} 行不是合法 JSON") from error
            if not isinstance(value, Mapping):
                raise GeNISCandidateError(f"会话分配第 {line_number} 行不是对象")
            description = f"会话分配第 {line_number} 行"
            session_id = _required_string(value, "session_id", description)
            assignment = _required_string(value, "assignment", description)
            subtype = _required_string(value, "subtype", description)
            binary_label = _required_string(value, "binary_label", description)
            if _SESSION_ID_PATTERN.fullmatch(session_id) is None:
                raise GeNISCandidateError(f"{description}的 session_id 不合法")
            if session_id in assignments:
                raise GeNISCandidateError(f"会话分配包含重复 session_id：{session_id}")
            if assignment not in allowed_assignments:
                raise GeNISCandidateError(f"{description}的 assignment 不合法：{assignment}")
            if subtype not in KNOWN_SUBTYPES | UNKNOWN_SUBTYPES:
                raise GeNISCandidateError(f"{description}包含合同外子类：{subtype}")
            expected_assignment = f"ood:{subtype}" if subtype in UNKNOWN_SUBTYPES else None
            if expected_assignment is not None and assignment != expected_assignment:
                raise GeNISCandidateError(f"未知子类未进入绑定开放集：{subtype}:{assignment}")
            if expected_assignment is None and assignment.startswith("ood:"):
                raise GeNISCandidateError(f"已知子类不得进入开放集：{subtype}:{assignment}")
            family = _family_for_subtype(subtype)
            if binary_label != _binary_for_family(family):
                raise GeNISCandidateError(f"会话分配的二元标签与子类冲突：{session_id}")
            start_time = _required_finite_float(value, "start_time", description)
            last_time = _required_finite_float(value, "last_time", description)
            if last_time < start_time:
                raise GeNISCandidateError(f"会话分配结束时间早于开始时间：{session_id}")
            try:
                row_count = int(value.get("row_count", 0))
            except (TypeError, ValueError) as error:
                raise GeNISCandidateError(f"会话分配行数不合法：{session_id}") from error
            if row_count <= 0:
                raise GeNISCandidateError(f"会话分配行数不合法：{session_id}")
            assignments[session_id] = _AssignmentRecord(
                session_id=session_id,
                assignment=assignment,
                subtype=subtype,
                binary_label=binary_label,
                start_time=start_time,
                last_time=last_time,
                row_count=row_count,
            )
    if not assignments:
        raise GeNISCandidateError("会话分配文件不能为空")
    return assignments


def _assignment_summary(
    assignments: Mapping[str, _AssignmentRecord], assignment: str
) -> dict[str, object]:
    records = [record for record in assignments.values() if record.assignment == assignment]
    binary_rows: Counter[str] = Counter()
    subtype_rows: Counter[str] = Counter()
    for record in records:
        binary_rows[record.binary_label] += record.row_count
        subtype_rows[record.subtype] += record.row_count
    return {
        "row_count": sum(record.row_count for record in records),
        "session_count": len(records),
        "binary_label_rows": dict(sorted(binary_rows.items())),
        "subtype_rows": dict(sorted(subtype_rows.items())),
    }


def _normalise_summary_partition(value: object, description: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise GeNISCandidateError(f"{description}必须是对象")
    try:
        row_count = int(value.get("row_count", -1))
        session_count = int(value.get("session_count", -1))
    except (TypeError, ValueError) as error:
        raise GeNISCandidateError(f"{description}的计数不合法") from error
    if row_count < 0 or session_count < 0:
        raise GeNISCandidateError(f"{description}的计数不合法")

    def normalise_counts(key: str) -> dict[str, int]:
        raw_counts = value.get(key)
        if not isinstance(raw_counts, Mapping):
            raise GeNISCandidateError(f"{description}缺少 {key}")
        try:
            counts = {str(name): int(count) for name, count in raw_counts.items()}
        except (TypeError, ValueError) as error:
            raise GeNISCandidateError(f"{description}的 {key} 计数不合法") from error
        if any(count < 0 for count in counts.values()):
            raise GeNISCandidateError(f"{description}的 {key} 计数不合法")
        return dict(sorted(counts.items()))

    return {
        "row_count": row_count,
        "session_count": session_count,
        "binary_label_rows": normalise_counts("binary_label_rows"),
        "subtype_rows": normalise_counts("subtype_rows"),
    }


def _validate_summaries(
    *,
    prepared_dir: Path,
    assignments_path: Path,
    plan_summary_path: Path,
    assignments: Mapping[str, _AssignmentRecord],
) -> tuple[dict[str, object], dict[str, object], tuple[dict[str, object], ...]]:
    material_summary = _read_json_object(prepared_dir / "materialization_summary.json", "物化摘要")
    plan_summary = _read_json_object(plan_summary_path, "划分计划摘要")
    if material_summary.get("schema_version") != "genis_materialized_split_v1":
        raise GeNISCandidateError("物化摘要模式必须为 genis_materialized_split_v1")
    if plan_summary.get("schema_version") != "genis_hybrid_forward_split_v1":
        raise GeNISCandidateError("划分计划模式必须为 genis_hybrid_forward_split_v1")
    if plan_summary.get("ratios") != [0.8, 0.1, 0.1]:
        raise GeNISCandidateError("划分计划比例必须为 [0.8, 0.1, 0.1]")
    if plan_summary.get("temporal_order_verified") is not True:
        raise GeNISCandidateError("划分计划未声明完成前向时间验证")
    raw_unknown = plan_summary.get("ood_subtypes")
    if not isinstance(raw_unknown, list) or frozenset(map(str, raw_unknown)) != UNKNOWN_SUBTYPES:
        raise GeNISCandidateError("划分计划未知子类集合与固定合同不一致")

    actual_assignment_sha256 = _sha256_file(assignments_path)
    if material_summary.get("assignment_sha256") != actual_assignment_sha256:
        raise GeNISCandidateError("物化摘要绑定的会话分配 SHA-256 不一致")
    material_sources = _normalise_source_files(material_summary, "物化摘要")
    plan_sources = _normalise_source_files(plan_summary, "划分计划摘要")
    if material_sources != plan_sources:
        raise GeNISCandidateError("两个摘要中的原始来源清单不一致")

    partitions = plan_summary.get("partitions")
    if not isinstance(partitions, Mapping):
        raise GeNISCandidateError("划分计划摘要缺少 partitions")
    for partition in ("train", "validation", "test", "purged"):
        actual = _assignment_summary(assignments, partition)
        expected = _normalise_summary_partition(
            partitions.get(partition), f"划分计划 {partition} 摘要"
        )
        if actual != expected:
            raise GeNISCandidateError(f"会话分配与划分计划 {partition} 摘要不一致")

    raw_ood = plan_summary.get("ood")
    if not isinstance(raw_ood, Mapping) or set(map(str, raw_ood)) != set(UNKNOWN_SUBTYPES):
        raise GeNISCandidateError("划分计划开放集摘要不完整")
    for subtype in sorted(UNKNOWN_SUBTYPES):
        actual = _assignment_summary(assignments, f"ood:{subtype}")
        expected = _normalise_summary_partition(
            raw_ood.get(subtype), f"划分计划开放集 {subtype} 摘要"
        )
        if actual != expected:
            raise GeNISCandidateError(f"会话分配与开放集 {subtype} 摘要不一致")

    expected_output_rows = {
        assignment: int(_assignment_summary(assignments, assignment)["row_count"])
        for assignment, _, _, _ in INPUT_FILES
    }
    raw_output_rows = material_summary.get("output_rows")
    if not isinstance(raw_output_rows, Mapping):
        raise GeNISCandidateError("物化摘要缺少 output_rows")
    try:
        output_rows = {str(key): int(value) for key, value in raw_output_rows.items()}
    except (TypeError, ValueError) as error:
        raise GeNISCandidateError("物化摘要 output_rows 计数不合法") from error
    if output_rows != expected_output_rows:
        raise GeNISCandidateError("物化摘要行数与绑定会话分配不一致")
    if int(material_summary.get("written_row_count", -1)) != sum(expected_output_rows.values()):
        raise GeNISCandidateError("物化摘要 written_row_count 不一致")
    purged_rows = int(_assignment_summary(assignments, "purged")["row_count"])
    if int(material_summary.get("purged_row_count", -1)) != purged_rows:
        raise GeNISCandidateError("物化摘要 purged_row_count 不一致")
    return material_summary, plan_summary, material_sources


def _normalise_features(record: Mapping[str, object], description: str) -> dict[str, float | None]:
    raw_features = record.get("features")
    if not isinstance(raw_features, Mapping):
        raise GeNISCandidateError(f"{description}缺少 features 对象")
    if set(map(str, raw_features)) != set(OBSERVATION_FIELDS):
        raise GeNISCandidateError(f"{description}的 features 必须恰含八个公共观测字段")
    features: dict[str, float | None] = {}
    for field in OBSERVATION_FIELDS:
        raw_value = raw_features.get(field)
        if raw_value is None:
            features[field] = None
            continue
        if isinstance(raw_value, bool):
            raise GeNISCandidateError(f"{description}的 {field} 必须是有限数或 null")
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as error:
            raise GeNISCandidateError(f"{description}的 {field} 必须是有限数或 null") from error
        if not math.isfinite(value):
            raise GeNISCandidateError(f"{description}的 {field} 必须是有限数或 null")
        features[field] = value
    return features


def _new_sample_id(old_sample_id: str) -> str:
    digest = hashlib.sha256(f"{CANDIDATE_ID}\0{old_sample_id}".encode("utf-8")).hexdigest()
    return f"genis:{digest}"


def _validate_temporal_order(assignments: Mapping[str, _AssignmentRecord]) -> None:
    for subtype in sorted(KNOWN_SUBTYPES):
        by_partition = {
            partition: [
                record
                for record in assignments.values()
                if record.subtype == subtype and record.assignment == partition
            ]
            for partition in ("train", "validation", "test")
        }
        if any(not records for records in by_partition.values()):
            raise GeNISCandidateError(f"已知子类未覆盖全部域内划分：{subtype}")
        if max(record.last_time for record in by_partition["train"]) >= min(
            record.start_time for record in by_partition["validation"]
        ):
            raise GeNISCandidateError(f"训练与验证时间交叉：{subtype}")
        if max(record.last_time for record in by_partition["validation"]) >= min(
            record.start_time for record in by_partition["test"]
        ):
            raise GeNISCandidateError(f"验证与测试时间交叉：{subtype}")


def _load_candidate_samples(
    *,
    prepared_dir: Path,
    assignments: Mapping[str, _AssignmentRecord],
    expected_output_rows: Mapping[str, int],
) -> tuple[pd.DataFrame, dict[str, object]]:
    columns: dict[str, list[object]] = {field: [] for field in SAMPLE_COLUMNS}
    observed_session_rows: Counter[str] = Counter()
    observed_partition_rows: Counter[str] = Counter()
    source_partition_counts: Counter[str] = Counter()
    old_sample_ids: set[str] = set()
    new_sample_ids: set[str] = set()
    train_observation_hashes: set[str] = set()
    excluded_validation_counts: Counter[str] = Counter()

    for expected_assignment, filename, split_id, domain_role in INPUT_FILES:
        path = prepared_dir / filename
        if not path.is_file():
            raise GeNISCandidateError(f"缺少固定 GeNIS 输入文件：{filename}")
        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                try:
                    raw_record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise GeNISCandidateError(
                        f"输入记录不是合法 JSON：{filename}:{line_number}"
                    ) from error
                if not isinstance(raw_record, Mapping):
                    raise GeNISCandidateError(f"输入记录必须是对象：{filename}:{line_number}")
                description = f"{filename}:{line_number}"
                old_sample_id = _required_string(raw_record, "sample_id", description)
                if old_sample_id in old_sample_ids:
                    raise GeNISCandidateError(f"旧 sample_id 重复：{description}")
                old_sample_ids.add(old_sample_id)
                group_id = _required_string(raw_record, "group_id", description)
                if _SESSION_ID_PATTERN.fullmatch(group_id) is None:
                    raise GeNISCandidateError(f"group_id 必须是 32 位小写十六进制：{description}")
                try:
                    assignment = assignments[group_id]
                except KeyError as error:
                    raise GeNISCandidateError(f"输入包含未分配会话：{description}") from error
                if assignment.assignment != expected_assignment:
                    raise GeNISCandidateError(
                        f"记录所在文件与 assignment 不一致：{description}:"
                        f"{assignment.assignment}"
                    )

                source_dataset = _required_string(raw_record, "source_dataset", description)
                if source_dataset != "genis":
                    raise GeNISCandidateError(f"source_dataset 必须为 genis：{description}")
                binary_label = _required_string(raw_record, "binary_label", description)
                family_label = _required_string(raw_record, "attack_family", description)
                expected_family = _family_for_subtype(assignment.subtype)
                if family_label not in FAMILY_LABELS or family_label != expected_family:
                    raise GeNISCandidateError(f"家族标签与绑定子类不一致：{description}")
                if binary_label != assignment.binary_label:
                    raise GeNISCandidateError(f"二元标签与会话分配不一致：{description}")
                if (
                    "attack_subtype" in raw_record
                    and str(raw_record.get("attack_subtype", "")).strip() != assignment.subtype
                ):
                    raise GeNISCandidateError(f"已有子类字段与会话分配不一致：{description}")

                features = _normalise_features(raw_record, description)
                observation_values = [features[field] for field in OBSERVATION_FIELDS]
                observation_sha256 = _stable_hash(observation_values)
                new_sample_id = _new_sample_id(old_sample_id)
                if new_sample_id in new_sample_ids:
                    raise GeNISCandidateError(f"候选 sample_id 冲突：{description}")
                new_sample_ids.add(new_sample_id)
                is_validation_duplicate = (
                    expected_assignment == "validation"
                    and observation_sha256 in train_observation_hashes
                )
                development_eligible = expected_assignment == "train" or (
                    expected_assignment == "validation" and not is_validation_duplicate
                )
                exclusion_reason = (
                    "exact_observation_seen_in_train" if is_validation_duplicate else ""
                )
                if is_validation_duplicate:
                    excluded_validation_counts[assignment.subtype] += 1

                candidate_record: dict[str, object] = {
                    "protocol_version": PROTOCOL_VERSION,
                    "protocol_status": PROTOCOL_STATUS,
                    "protocol_phase": PROTOCOL_PHASE,
                    "candidate_id": CANDIDATE_ID,
                    "sample_id": new_sample_id,
                    "source_record_sha256": _stable_hash(raw_record),
                    "observation_sha256": observation_sha256,
                    "source_dataset": "genis",
                    "group_id": group_id,
                    "source_partition": expected_assignment,
                    "split_id": split_id,
                    "domain_role": domain_role,
                    "development_eligible": development_eligible,
                    "exclusion_reason": exclusion_reason,
                    "binary_label": binary_label,
                    "family_label": family_label,
                    "subtype_label": assignment.subtype,
                    **features,
                    **{
                        f"{field}_missing": int(features[field] is None)
                        for field in OBSERVATION_FIELDS
                    },
                }
                candidate_record["candidate_record_sha256"] = _stable_hash(candidate_record)
                for field in SAMPLE_COLUMNS:
                    columns[field].append(candidate_record[field])

                if expected_assignment == "train":
                    train_observation_hashes.add(observation_sha256)
                observed_session_rows[group_id] += 1
                observed_partition_rows[expected_assignment] += 1
                source_partition_counts[expected_assignment] += 1

    mismatched_sessions = sorted(
        session_id
        for session_id, assignment in assignments.items()
        if assignment.assignment != "purged"
        and observed_session_rows.get(session_id, 0) != assignment.row_count
    )
    unexpected_sessions = sorted(set(observed_session_rows).difference(assignments))
    if mismatched_sessions or unexpected_sessions:
        raise GeNISCandidateError(
            "物化记录与会话行数不一致："
            f"计数不符 {len(mismatched_sessions)}，未知 {len(unexpected_sessions)}"
        )
    if dict(observed_partition_rows) != dict(expected_output_rows):
        raise GeNISCandidateError("实际输入行数与物化摘要 output_rows 不一致")

    frame = pd.DataFrame(columns, columns=list(SAMPLE_COLUMNS))
    if frame.empty:
        raise GeNISCandidateError("候选主记录不能为空")
    for field in OBSERVATION_FIELDS:
        frame[field] = frame[field].astype("float64")
    for field in MISSING_MASK_FIELDS:
        frame[field] = frame[field].astype("int8")
    frame["development_eligible"] = frame["development_eligible"].astype(bool)
    frame = frame.sort_values("sample_id", kind="mergesort").reset_index(drop=True)
    if frame["sample_id"].duplicated().any():
        raise GeNISCandidateError("候选 sample_id 必须全局唯一")

    strict_validation = frame[
        frame["source_partition"].eq("validation") & frame["development_eligible"]
    ]
    strict_subtypes = set(strict_validation["subtype_label"].astype(str))
    train_subtypes = set(
        frame.loc[frame["source_partition"].eq("train"), "subtype_label"].astype(str)
    )
    if train_subtypes != KNOWN_SUBTYPES or strict_subtypes != KNOWN_SUBTYPES:
        raise GeNISCandidateError("训练或严格验证未覆盖全部已知子类")
    strict_hashes = set(strict_validation["observation_sha256"].astype(str))
    if train_observation_hashes.intersection(strict_hashes):
        raise GeNISCandidateError("严格训练与验证仍存在精确观测交叉")
    observed_unknown = set(
        frame.loc[frame["split_id"].eq("open_set_test"), "subtype_label"].astype(str)
    )
    if observed_unknown != UNKNOWN_SUBTYPES or train_subtypes.intersection(observed_unknown):
        raise GeNISCandidateError("开放集未知子类隔离失败")

    evidence = {
        "source_partition_counts": dict(sorted(source_partition_counts.items())),
        "excluded_validation_count": int(sum(excluded_validation_counts.values())),
        "excluded_validation_counts_by_subtype": dict(sorted(excluded_validation_counts.items())),
        "old_sample_id_count": len(old_sample_ids),
        "candidate_sample_id_count": len(new_sample_ids),
        "strict_train_observation_hash_count": len(train_observation_hashes),
        "strict_validation_observation_hash_count": len(strict_hashes),
    }
    return frame, evidence


def _field_roles() -> dict[str, object]:
    label_fields = {"binary_label", "family_label", "subtype_label"}
    split_fields = {
        "group_id",
        "source_partition",
        "split_id",
        "domain_role",
        "development_eligible",
    }
    fields: dict[str, object] = {}
    for field in SAMPLE_METADATA_FIELDS:
        role = (
            "label_target"
            if field in label_fields
            else "split_metadata" if field in split_fields else "audit_only"
        )
        fields[field] = {"role": role}
    for field in MODEL_FEATURE_FIELDS:
        fields[field] = {"role": "model_input", "views": [TREE_VIEW_NAME]}
    return {
        "protocol_version": PROTOCOL_VERSION,
        "fields": fields,
        "views": {TREE_VIEW_NAME: {"feature_fields": list(MODEL_FEATURE_FIELDS)}},
    }


def _schema_document() -> dict[str, object]:
    units = {
        "total_packets": "packet",
        "total_bytes": "byte",
        "packet_length_mean": "byte",
        "packet_length_min": "byte",
        "packet_length_max": "byte",
        "iat_mean_ms": "millisecond",
        "packet_rate": "packet_per_second",
        "byte_rate": "byte_per_second",
    }
    columns: dict[str, object] = {}
    for field in SAMPLE_METADATA_FIELDS:
        columns[field] = {
            "dtype": "boolean" if field == "development_eligible" else "string",
            "nullable": field == "exclusion_reason",
        }
    for field in OBSERVATION_FIELDS:
        columns[field] = {
            "dtype": "float64",
            "nullable": True,
            "unit": units[field],
            "missing_mask": f"{field}_missing",
        }
    for field in MISSING_MASK_FIELDS:
        columns[field] = {"dtype": "int8", "nullable": False, "values": [0, 1]}
    return {
        "schema_version": "genis_candidate_schema_v1",
        "protocol_version": PROTOCOL_VERSION,
        "candidate_id": CANDIDATE_ID,
        "columns": columns,
        "column_order": list(SAMPLE_COLUMNS),
    }


def _label_contract() -> dict[str, object]:
    return {
        "contract_version": "genis_hierarchical_label_v1",
        "protocol_version": PROTOCOL_VERSION,
        "family": {
            "suite_id": FAMILY_SUITE_ID,
            "labels": sorted(FAMILY_LABELS),
        },
        "subtype": {
            "suite_id": SUBTYPE_SUITE_ID,
            "known_labels": sorted(KNOWN_SUBTYPES),
        },
        "open_set": {
            "suite_id": OPEN_SET_SUITE_ID,
            "unknown_role": "unknown_subtype",
            "unknown_labels": sorted(UNKNOWN_SUBTYPES),
            "family_mapping": {subtype: "dos" for subtype in sorted(UNKNOWN_SUBTYPES)},
            "unknown_family_claim_allowed": False,
        },
        "binary_mapping": {
            "benign": "benign",
            "bruteforce": "malicious",
            "dos": "malicious",
        },
    }


def _source_artifacts(
    *,
    prepared_dir: Path,
    assignments_path: Path,
    plan_summary_path: Path,
    source_files: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for _, filename, _, _ in INPUT_FILES:
        path = prepared_dir / filename
        rows.append(
            {
                "lineage_level": "candidate_input",
                "role": "materialized_partition",
                "source_path": f"prepared/{filename}",
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    material_summary_path = prepared_dir / "materialization_summary.json"
    for path, role in (
        (material_summary_path, "materialization_summary"),
        (assignments_path, "session_assignments"),
        (plan_summary_path, "split_plan_summary"),
    ):
        rows.append(
            {
                "lineage_level": "candidate_input",
                "role": role,
                "source_path": path.name,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    for source_file in source_files:
        rows.append(
            {
                "lineage_level": "upstream_source",
                "role": "original_csv",
                "source_path": str(source_file["name"]),
                "sha256": str(source_file["sha256"]),
                "size_bytes": int(source_file["size_bytes"]),
            }
        )
    module_path = Path(__file__)
    rows.append(
        {
            "lineage_level": "candidate_builder",
            "role": "materializer_source",
            "source_path": "src/flow_probe/genis_candidate.py",
            "sha256": _sha256_file(module_path),
            "size_bytes": module_path.stat().st_size,
        }
    )
    return sorted(
        rows,
        key=lambda row: (
            str(row["lineage_level"]),
            str(row["source_path"]),
            str(row["role"]),
        ),
    )


def _manifest_sample_ids(samples: pd.DataFrame, source_split: str) -> list[str]:
    if source_split == "validation":
        selected = samples[
            samples["source_partition"].eq("validation") & samples["development_eligible"]
        ]
    elif source_split == "open_set_test":
        selected = samples[samples["split_id"].eq("open_set_test")]
    else:
        selected = samples[samples["source_partition"].eq(source_split)]
    sample_ids = sorted(selected["sample_id"].astype(str).tolist())
    if not sample_ids:
        raise GeNISCandidateError(f"候选清单不能为空：{source_split}")
    return sample_ids


def _write_manifests(
    output_dir: Path, samples: pd.DataFrame, samples_sha256: str
) -> dict[str, list[str]]:
    manifest_ids: dict[str, list[str]] = {}
    for relative_path, suite_id, split_id, source_split in SPLIT_SPECS:
        sample_ids = _manifest_sample_ids(samples, source_split)
        rows = [
            {
                "protocol_version": PROTOCOL_VERSION,
                "suite_id": suite_id,
                "split_id": split_id,
                "sample_id": sample_id,
                "samples_sha256": samples_sha256,
            }
            for sample_id in sample_ids
        ]
        _write_jsonl(output_dir / relative_path, rows)
        manifest_ids[relative_path] = sample_ids
    return manifest_ids


def _manifest_membership_conflicts(
    manifest_ids: Mapping[str, Sequence[str]],
) -> tuple[int, int]:
    by_suite: defaultdict[str, dict[str, str]] = defaultdict(dict)
    sample_conflicts = 0
    for relative_path, suite_id, split_id, _ in SPLIT_SPECS:
        for sample_id in manifest_ids[relative_path]:
            previous = by_suite[suite_id].get(sample_id)
            if previous is not None and previous != split_id:
                sample_conflicts += 1
            by_suite[suite_id][sample_id] = split_id
    group_conflicts = 0
    return sample_conflicts, group_conflicts


def _build_audits(
    *,
    samples: pd.DataFrame,
    assignments: Mapping[str, _AssignmentRecord],
    evidence: Mapping[str, object],
    manifest_ids: Mapping[str, Sequence[str]],
    manifest_hashes: Mapping[str, str],
    source_artifacts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    family_counts = Counter(samples["family_label"].astype(str))
    subtype_counts = Counter(samples["subtype_label"].astype(str))
    binary_counts = Counter(samples["binary_label"].astype(str))
    partition_counts = Counter(samples["source_partition"].astype(str))
    split_sample_conflicts, _ = _manifest_membership_conflicts(manifest_ids)

    development = samples[samples["source_partition"].isin(["train", "validation"])]
    group_split_count = development.groupby("group_id")["source_partition"].nunique()
    group_conflicts = int(group_split_count.gt(1).sum())
    train_hashes = set(
        samples.loc[samples["source_partition"].eq("train"), "observation_sha256"].astype(str)
    )
    validation_hashes = set(
        samples.loc[
            samples["source_partition"].eq("validation") & samples["development_eligible"],
            "observation_sha256",
        ].astype(str)
    )
    sensitive_tokens = {
        "address",
        "file",
        "filename",
        "group",
        "label",
        "path",
        "port",
        "scenario",
        "session",
        "source",
        "split",
        "topology",
    }
    sensitive_hits = sorted(
        field
        for field in MODEL_FEATURE_FIELDS
        if set(field.lower().split("_")).intersection(sensitive_tokens)
    )
    train_subtypes = set(
        samples.loc[samples["source_partition"].eq("train"), "subtype_label"].astype(str)
    )
    unknown_subtypes = set(
        samples.loc[samples["split_id"].eq("open_set_test"), "subtype_label"].astype(str)
    )

    label_coverage = {
        "sample_count": int(len(samples)),
        "binary_label_counts": dict(sorted(binary_counts.items())),
        "family_label_counts": dict(sorted(family_counts.items())),
        "subtype_label_counts": dict(sorted(subtype_counts.items())),
        "source_partition_counts": dict(sorted(partition_counts.items())),
        "known_subtypes": sorted(KNOWN_SUBTYPES),
        "unknown_subtypes": sorted(UNKNOWN_SUBTYPES),
        "open_set_is_unknown_subtype_not_unknown_family": True,
        "status": "pass",
    }
    leakage_audit = {
        "old_identifier_persistence": {
            "input_identifier_count": int(evidence["old_sample_id_count"]),
            "persisted_identifier_count": 0,
            "status": "pass",
        },
        "candidate_sample_id_uniqueness": {
            "duplicate_count": int(samples["sample_id"].duplicated().sum()),
            "status": "pass",
        },
        "manifest_cross_split_sample_id": {
            "conflict_count": split_sample_conflicts,
            "status": "pass" if split_sample_conflicts == 0 else "fail",
        },
        "development_group_exclusivity": {
            "cross_split_group_count": group_conflicts,
            "status": "pass" if group_conflicts == 0 else "fail",
        },
        "strict_train_validation_exact_observation": {
            "cross_split_hash_count": len(train_hashes.intersection(validation_hashes)),
            "excluded_validation_record_count": int(evidence["excluded_validation_count"]),
            "excluded_validation_counts_by_subtype": dict(
                evidence["excluded_validation_counts_by_subtype"]
            ),
            "status": "pass",
        },
        "temporal_order": {
            "known_subtype_count": len(KNOWN_SUBTYPES),
            "verified_from_bound_assignments": True,
            "status": "pass",
        },
        "unknown_subtype_isolation": {
            "train_unknown_intersection": sorted(train_subtypes.intersection(unknown_subtypes)),
            "unknown_subtypes": sorted(unknown_subtypes),
            "status": "pass",
        },
        "model_field_budget": {
            "model_input_fields": list(MODEL_FEATURE_FIELDS),
            "sensitive_token_hits": sensitive_hits,
            "label_derived_fields": [],
            "status": "pass" if not sensitive_hits else "fail",
        },
        "overall_status": "pass",
    }
    input_lineage = {
        "assignment_record_count": len(assignments),
        "assignment_sha256": next(
            str(row["sha256"]) for row in source_artifacts if row["role"] == "session_assignments"
        ),
        "sources": list(source_artifacts),
        "absolute_paths_persisted": False,
        "status": "pass",
    }
    p0_subset = {
        "protocol_version": PROTOCOL_VERSION,
        "protocol_status": PROTOCOL_STATUS,
        "protocol_phase": PROTOCOL_PHASE,
        "review_status": REVIEW_STATUS,
        "formal_protocol_gate_complete": False,
        "checks": {
            "identity_and_uniqueness": leakage_audit["candidate_sample_id_uniqueness"],
            "group_exclusivity": leakage_audit["development_group_exclusivity"],
            "exact_duplicate_leakage": leakage_audit["strict_train_validation_exact_observation"],
            "temporal_order": leakage_audit["temporal_order"],
            "unknown_subtype_isolation": leakage_audit["unknown_subtype_isolation"],
            "field_budget": leakage_audit["model_field_budget"],
            "manifest_binding": {
                "artifact_hashes": dict(sorted(manifest_hashes.items())),
                "status": "pass",
            },
            "reproducibility": {
                "status": "pending_external_rerun",
                "required_comparison": "两个新输出目录的全部制品逐字节一致",
            },
        },
        "overall_status": "provisional_candidate",
        "use_restriction": "仅允许 theory_selection，不得读取测试结果调参或形成最终测试结论。",
    }
    return {
        "input-lineage.json": input_lineage,
        "label-coverage.json": label_coverage,
        "leakage-audit.json": leakage_audit,
        "manifest-hashes.json": dict(sorted(manifest_hashes.items())),
        "p0-subset.json": p0_subset,
    }


def materialize_candidate(
    *,
    prepared_dir: Path,
    assignments_path: Path,
    plan_summary_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """生成 GeNIS 理论筛选候选协议；输出目录必须不存在。"""
    prepared_dir = Path(prepared_dir).expanduser().resolve()
    assignments_path = Path(assignments_path).expanduser().resolve()
    plan_summary_path = Path(plan_summary_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise GeNISCandidateError(f"输出目录已存在，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True)
    incomplete_marker = output_dir / "_INCOMPLETE"
    incomplete_marker.write_text('{"status":"incomplete"}\n', encoding="utf-8")
    (output_dir / "splits").mkdir()
    (output_dir / "audit").mkdir()

    assignments = _load_assignments(assignments_path)
    _validate_temporal_order(assignments)
    _, _, source_files = _validate_summaries(
        prepared_dir=prepared_dir,
        assignments_path=assignments_path,
        plan_summary_path=plan_summary_path,
        assignments=assignments,
    )
    expected_output_rows = {
        assignment: int(_assignment_summary(assignments, assignment)["row_count"])
        for assignment, _, _, _ in INPUT_FILES
    }
    samples, evidence = _load_candidate_samples(
        prepared_dir=prepared_dir,
        assignments=assignments,
        expected_output_rows=expected_output_rows,
    )

    samples_path = output_dir / "samples.parquet"
    samples.to_parquet(samples_path, index=False, engine="pyarrow", compression="zstd")
    _write_yaml(output_dir / "field-roles.yaml", _field_roles())
    _write_json(output_dir / "schema.json", _schema_document())
    _write_json(output_dir / "label-contract.json", _label_contract())
    source_artifacts = _source_artifacts(
        prepared_dir=prepared_dir,
        assignments_path=assignments_path,
        plan_summary_path=plan_summary_path,
        source_files=source_files,
    )
    _write_jsonl(output_dir / "source-artifacts.jsonl", source_artifacts)

    samples_sha256 = _sha256_file(samples_path)
    manifest_ids = _write_manifests(output_dir, samples, samples_sha256)
    manifest_hashes = {
        "samples.parquet": samples_sha256,
        **{
            relative_path: _sha256_file(output_dir / relative_path)
            for relative_path, _, _, _ in SPLIT_SPECS
        },
    }
    audits = _build_audits(
        samples=samples,
        assignments=assignments,
        evidence=evidence,
        manifest_ids=manifest_ids,
        manifest_hashes=manifest_hashes,
        source_artifacts=source_artifacts,
    )
    for filename, value in audits.items():
        _write_json(output_dir / "audit" / filename, value)

    candidate_manifest = {
        "manifest_version": "genis_candidate_manifest_v1",
        "protocol_version": PROTOCOL_VERSION,
        "protocol_status": PROTOCOL_STATUS,
        "protocol_phase": PROTOCOL_PHASE,
        "review_status": REVIEW_STATUS,
        "candidate_id": CANDIDATE_ID,
        "sample_count": int(len(samples)),
        "development_eligible_count": int(samples["development_eligible"].sum()),
        "source_partition_counts": dict(
            sorted(Counter(samples["source_partition"].astype(str)).items())
        ),
        "family_label_counts": dict(sorted(Counter(samples["family_label"].astype(str)).items())),
        "subtype_label_counts": dict(sorted(Counter(samples["subtype_label"].astype(str)).items())),
        "excluded_validation_count": int(evidence["excluded_validation_count"]),
        "final_tuning_allowed": False,
        "final_test_claim_allowed": False,
        "test_and_open_set_used_for_route_selection": False,
    }
    _write_json(output_dir / "candidate-manifest.json", candidate_manifest)

    artifact_list_path = output_dir / "audit" / "artifact-sha256.txt"
    artifact_paths = sorted(
        (
            path
            for path in output_dir.rglob("*")
            if path.is_file()
            and path not in {incomplete_marker, artifact_list_path, output_dir / "protocol.yaml"}
        ),
        key=lambda path: path.relative_to(output_dir).as_posix(),
    )
    artifact_list_path.write_text(
        "".join(
            f"{_sha256_file(path)}  {path.relative_to(output_dir).as_posix()}\n"
            for path in artifact_paths
        ),
        encoding="utf-8",
    )
    all_artifact_paths = [*artifact_paths, artifact_list_path]
    artifact_hashes = {
        path.relative_to(output_dir).as_posix(): _sha256_file(path)
        for path in sorted(
            all_artifact_paths,
            key=lambda item: item.relative_to(output_dir).as_posix(),
        )
    }
    protocol = {
        "protocol_version": PROTOCOL_VERSION,
        "status": PROTOCOL_STATUS,
        "phase": PROTOCOL_PHASE,
        "review_status": REVIEW_STATUS,
        "candidate_id": CANDIDATE_ID,
        "scope": "GeNIS 家族、子类、时间前向和未知子类候选协议",
        "final_tuning_allowed": False,
        "final_test_claim_allowed": False,
        "test_and_open_set_used_for_route_selection": False,
        "artifacts": artifact_hashes,
        "limitations": [
            "这是完整 dataset-v1 冻结前的 GeNIS 理论筛选候选组件。",
            "时间前向与开放集清单只冻结，不得用于本轮验证调参。",
            "未知对象是 dos 家族内的新子类，不得表述为未知攻击家族。",
        ],
    }
    _write_yaml(output_dir / "protocol.yaml", protocol)
    incomplete_marker.unlink()
    return {
        "candidate_id": CANDIDATE_ID,
        "protocol_version": PROTOCOL_VERSION,
        "review_status": REVIEW_STATUS,
        "protocol_sha256": _sha256_file(output_dir / "protocol.yaml"),
        "samples_sha256": samples_sha256,
        "sample_count": int(len(samples)),
        "development_eligible_count": int(samples["development_eligible"].sum()),
        "excluded_validation_count": int(evidence["excluded_validation_count"]),
        "output_dir": str(output_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 GeNIS 理论筛选候选协议")
    parser.add_argument("--prepared-dir", type=Path, required=True)
    parser.add_argument("--assignments", type=Path, required=True)
    parser.add_argument("--plan-summary", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = materialize_candidate(
        prepared_dir=args.prepared_dir,
        assignments_path=args.assignments,
        plan_summary_path=args.plan_summary,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
