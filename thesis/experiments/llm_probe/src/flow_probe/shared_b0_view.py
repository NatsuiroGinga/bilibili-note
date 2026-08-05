"""从冻结的三源统一预算派生无泄漏的共享 B0 视图。"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath

import pandas as pd
import yaml


CONFIG_SCHEMA_VERSION = "flow_probe_shared_b0_view_config_v1"
ARTIFACT_SCHEMA_VERSION = "flow_probe_shared_b0_view_v1"
COMMON_FIELDS = (
    "total_packets",
    "total_bytes",
    "packet_length_mean",
    "packet_length_min",
    "packet_length_max",
    "iat_mean_ms",
    "packet_rate",
    "byte_rate",
)
MASK_FIELDS = tuple(f"{field}_missing" for field in COMMON_FIELDS)
FEATURE_COLUMNS = ("sample_id", "stable_order", *COMMON_FIELDS, *MASK_FIELDS)
EXPECTED_SOURCE_NAMES = ("genis", "tqhc2", "ns3")
FORBIDDEN_INPUT_TOKENS = frozenset(
    {
        "label",
        "source",
        "dataset",
        "scenario",
        "topology",
        "address",
        "ip",
        "port",
        "path",
        "capture",
        "profile",
        "interval",
        "jitter",
        "capacity",
        "queue",
        "physics",
        "truth",
        "split",
        "group",
        "seed",
        "run",
    }
)


class SharedB0ViewError(ValueError):
    """共享 B0 视图输入或输出不满足冻结合同。"""


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SharedB0ViewError(f"{description}必须是对象")
    return value


def _string(mapping: Mapping[str, object], key: str, description: str) -> str:
    value = str(mapping.get(key, "")).strip()
    if not value:
        raise SharedB0ViewError(f"{description}缺少非空字段：{key}")
    return value


def _integer(mapping: Mapping[str, object], key: str, description: str) -> int:
    raw = mapping.get(key)
    if isinstance(raw, bool):
        raise SharedB0ViewError(f"{description}.{key}必须是非负整数")
    try:
        value = int(raw)
    except (TypeError, ValueError) as error:
        raise SharedB0ViewError(f"{description}.{key}必须是非负整数") from error
    if value < 0:
        raise SharedB0ViewError(f"{description}.{key}必须是非负整数")
    return value


def _boolean(mapping: Mapping[str, object], key: str, description: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise SharedB0ViewError(f"{description}.{key}必须是布尔值")
    return value


def _normalise_relative_path(value: object, description: str) -> str:
    raw = str(value).strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        raise SharedB0ViewError(f"{description}必须是安全的项目相对路径：{raw!r}")
    return path.as_posix()


def _project_path(project_root: Path, value: object, description: str) -> tuple[Path, str]:
    relative = _normalise_relative_path(value, description)
    path = (project_root / relative).resolve()
    try:
        path.relative_to(project_root)
    except ValueError as error:
        raise SharedB0ViewError(f"{description}越过项目根目录：{relative}") from error
    return path, relative


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_sha256(value: object, description: str) -> str:
    digest = str(value).strip()
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise SharedB0ViewError(f"{description}必须是小写 SHA-256")
    return digest


def _verify_file(path: Path, expected: object, description: str) -> str:
    expected_digest = _expected_sha256(expected, f"{description}登记哈希")
    if not path.is_file():
        raise SharedB0ViewError(f"{description}不存在：{path}")
    actual = file_sha256(path)
    if actual != expected_digest:
        raise SharedB0ViewError(f"{description}哈希不一致：期望 {expected_digest}，实际 {actual}")
    return actual


def _read_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise SharedB0ViewError(f"配置不存在：{path}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise SharedB0ViewError(f"配置不是合法 YAML：{path}") from error
    if not isinstance(value, dict) or value.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise SharedB0ViewError("共享视图配置 schema_version 不符合合同")
    configured_fields = value.get("common_fields")
    if configured_fields != list(COMMON_FIELDS):
        raise SharedB0ViewError("common_fields 必须精确等于固定公共观测字段并保持顺序")
    return value


def _read_json(path: Path, description: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SharedB0ViewError(f"无法读取{description}：{path}") from error
    if not isinstance(value, dict):
        raise SharedB0ViewError(f"{description}顶层必须是对象")
    return value


def _read_jsonl(path: Path, description: str) -> list[dict[str, object]]:
    if not path.is_file():
        raise SharedB0ViewError(f"{description}不存在：{path}")
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as error:
                raise SharedB0ViewError(f"{description}第 {line_number} 行不是合法 JSON") from error
            if not isinstance(value, dict):
                raise SharedB0ViewError(f"{description}第 {line_number} 行必须是对象")
            rows.append(value)
    if not rows:
        raise SharedB0ViewError(f"{description}不能为空")
    return rows


def _finite_or_none(value: object, field: str) -> float | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, bool):
        raise SharedB0ViewError(f"字段 {field} 不得是布尔值")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise SharedB0ViewError(f"字段 {field} 必须是有限数或空值") from error
    if not math.isfinite(number):
        raise SharedB0ViewError(f"字段 {field} 必须是有限数或空值")
    if number < 0:
        raise SharedB0ViewError(f"字段 {field} 不得为负数")
    return number


def _common_record(
    values: Mapping[str, object],
    masks: Mapping[str, object] | None = None,
) -> dict[str, float | int | None]:
    output: dict[str, float | int | None] = {}
    for field in COMMON_FIELDS:
        value = _finite_or_none(values.get(field), field)
        configured_mask = None if masks is None else masks.get(f"{field}_missing")
        if configured_mask is None:
            missing = int(value is None)
        else:
            if isinstance(configured_mask, bool):
                missing = int(configured_mask)
            else:
                try:
                    missing = int(configured_mask)
                except (TypeError, ValueError) as error:
                    raise SharedB0ViewError(f"{field} 缺失掩码必须是 0 或 1") from error
            if missing not in {0, 1}:
                raise SharedB0ViewError(f"{field} 缺失掩码必须是 0 或 1")
        if missing != int(value is None):
            raise SharedB0ViewError(f"{field} 的数值与缺失掩码不一致")
        output[field] = value
        output[f"{field}_missing"] = missing
    return output


def map_genis_row(row: Mapping[str, object]) -> dict[str, float | int | None]:
    """直接复用 GeNIS 已统一单位的八个公共观测及其掩码。"""
    return _common_record(row, row)


def map_tqhc2_row(row: Mapping[str, object]) -> dict[str, float | int | None]:
    """把 TQH-C2 包序列聚合字段换算到公共单位。"""
    duration_us = _finite_or_none(row.get("flow_duration_us"), "flow_duration_us")
    packet_count = _finite_or_none(row.get("packet_count"), "packet_count")
    total_bytes = _finite_or_none(row.get("network_bytes_total"), "network_bytes_total")
    duration_s = None if duration_us is None or duration_us <= 0 else duration_us / 1_000_000.0
    values = {
        "total_packets": packet_count,
        "total_bytes": total_bytes,
        "packet_length_mean": row.get("network_bytes_mean"),
        "packet_length_min": row.get("network_bytes_min"),
        "packet_length_max": row.get("network_bytes_max"),
        "iat_mean_ms": (
            None
            if row.get("delta_time_us_mean") is None
            else _finite_or_none(row.get("delta_time_us_mean"), "delta_time_us_mean") / 1_000.0
        ),
        "packet_rate": None if duration_s is None else packet_count / duration_s,
        "byte_rate": None if duration_s is None else total_bytes / duration_s,
    }
    return _common_record(values)


def _numeric_sequence(record: Mapping[str, object], section: str, field: str) -> list[float]:
    container = _mapping(record.get(section), f"ns-3 {section}")
    raw_values = container.get(field)
    if not isinstance(raw_values, list) or len(raw_values) != 4:
        raise SharedB0ViewError(f"ns-3 {section}.{field} 必须是四窗口列表")
    values = [_finite_or_none(value, f"ns-3 {field}") for value in raw_values]
    if any(value is None for value in values):
        raise SharedB0ViewError(f"ns-3 {section}.{field} 不得缺失")
    return [float(value) for value in values if value is not None]


def map_ns3_record(record: Mapping[str, object]) -> dict[str, float | int | None]:
    """只从 ns-3 四窗口公开接收量和时间跨度构造可观测公共字段。"""
    packets = _numeric_sequence(record, "model_inputs", "qdisc_received_packets")
    byte_counts = _numeric_sequence(record, "model_inputs", "qdisc_received_l3_bytes")
    metadata = _mapping(record.get("metadata"), "ns-3 metadata")
    starts = metadata.get("window_start_s")
    ends = metadata.get("window_end_s")
    if (
        not isinstance(starts, list)
        or not isinstance(ends, list)
        or len(starts) != 4
        or len(ends) != 4
    ):
        raise SharedB0ViewError("ns-3 metadata 必须包含四窗口起止时间")
    start = _finite_or_none(starts[0], "ns-3 window_start_s")
    end = _finite_or_none(ends[-1], "ns-3 window_end_s")
    if start is None or end is None or end <= start:
        raise SharedB0ViewError("ns-3 四窗口时间跨度必须为正")
    duration_s = end - start
    total_packets = sum(packets)
    total_bytes = sum(byte_counts)
    values = {
        "total_packets": total_packets,
        "total_bytes": total_bytes,
        "packet_length_mean": None if total_packets <= 0 else total_bytes / total_packets,
        "packet_length_min": None,
        "packet_length_max": None,
        "iat_mean_ms": None,
        "packet_rate": total_packets / duration_s,
        "byte_rate": total_bytes / duration_s,
    }
    return _common_record(values)


def _normalise_binary_label(value: object, description: str) -> str:
    label = str(value).strip().lower()
    aliases = {
        "benign": "benign",
        "normal": "benign",
        "0": "benign",
        "malicious": "malicious",
        "attack": "malicious",
        "1": "malicious",
    }
    if label not in aliases:
        raise SharedB0ViewError(f"{description}二分类标签非法：{value!r}")
    return aliases[label]


def _ns3_binary_label(record: Mapping[str, object]) -> str:
    targets = _mapping(record.get("label_targets"), "ns-3 label_targets")
    raw = targets.get("is_attack")
    if not isinstance(raw, list) or len(raw) != 4:
        raise SharedB0ViewError("ns-3 is_attack 必须是四窗口列表")
    labels = {_normalise_binary_label(value, "ns-3 ") for value in raw}
    if len(labels) != 1:
        raise SharedB0ViewError("ns-3 保留样本不得跨越攻击标签变化")
    return labels.pop()


def render_input_text(common: Mapping[str, object]) -> str:
    """生成不含来源与标签信息的确定性中文文本。"""
    labels = {
        "total_packets": "包数",
        "total_bytes": "总字节",
        "packet_length_mean": "包长均值",
        "packet_length_min": "包长最小值",
        "packet_length_max": "包长最大值",
        "iat_mean_ms": "平均到达间隔毫秒",
        "packet_rate": "每秒包数",
        "byte_rate": "每秒字节数",
    }
    parts = []
    for field in COMMON_FIELDS:
        missing = int(common[f"{field}_missing"])
        value = "缺失" if missing else format(float(common[field]), ".12g")
        parts.append(f"{labels[field]}={value}")
    return "；".join(parts)


def _qwen_prompt(input_text: str) -> str:
    return (
        "根据以下流量统计判断该流量是良性还是恶意。"
        "只输出包含 binary_label 的 JSON 对象，取值只能是 benign 或 malicious。\n"
        f"{input_text}"
    )


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(_canonical_json(row) + "\n")
            count += 1
    return count


def _candidate_contract(
    rows: Sequence[Mapping[str, object]],
    candidate_config: Mapping[str, object],
    master_sha256: str,
) -> tuple[list[str], dict[str, str]]:
    expected_count = _integer(candidate_config, "expected_count", "candidate_manifest")
    if len(rows) != expected_count:
        raise SharedB0ViewError(f"候选清单数量不一致：{len(rows)} != {expected_count}")
    sample_ids: list[str] = []
    source_by_id: dict[str, str] = {}
    observed_counts: Counter[str] = Counter()
    for expected_order, row in enumerate(rows):
        if _integer(row, "stable_order", f"候选清单第 {expected_order} 行") != expected_order:
            raise SharedB0ViewError(f"候选清单 stable_order 在 {expected_order} 处不连续")
        sample_id = str(row.get("sample_id", "")).strip()
        source = str(row.get("source_dataset", "")).strip()
        if not sample_id or source not in EXPECTED_SOURCE_NAMES:
            raise SharedB0ViewError(f"候选清单第 {expected_order} 行主键或来源非法")
        if sample_id in source_by_id:
            raise SharedB0ViewError(f"候选清单 sample_id 重复：{sample_id}")
        if row.get("task_role") != "candidate_screening":
            raise SharedB0ViewError(f"候选清单任务角色非法：{sample_id}")
        if row.get("master_records_sha256") != master_sha256:
            raise SharedB0ViewError(f"候选清单主索引绑定失配：{sample_id}")
        sample_ids.append(sample_id)
        source_by_id[sample_id] = source
        observed_counts[source] += 1
    raw_expected_counts = _mapping(candidate_config.get("source_counts"), "candidate source_counts")
    expected_counts = {
        source: _integer(raw_expected_counts, source, "candidate source_counts")
        for source in EXPECTED_SOURCE_NAMES
    }
    if dict(observed_counts) != expected_counts:
        raise SharedB0ViewError(f"候选来源配额不一致：{dict(observed_counts)} != {expected_counts}")
    return sample_ids, source_by_id


def _validation_contract(
    project_root: Path,
    source_config: Mapping[str, object],
    source_name: str,
    samples_sha256: str,
    candidate_ids: set[str],
    input_hashes: dict[str, str],
) -> tuple[list[str], str]:
    validation = _mapping(source_config.get("validation_manifest"), f"{source_name} validation")
    path, relative = _project_path(
        project_root, validation.get("path"), f"{source_name} validation.path"
    )
    input_hashes[relative] = _verify_file(path, validation.get("sha256"), f"{source_name} 验证清单")
    rows = _read_jsonl(path, f"{source_name} 验证清单")
    expected_count = _integer(validation, "expected_count", f"{source_name} validation")
    if len(rows) != expected_count:
        raise SharedB0ViewError(
            f"{source_name} 验证清单数量不一致：{len(rows)} != {expected_count}"
        )
    expected_suite = _string(validation, "suite_id", f"{source_name} validation")
    expected_split = _string(validation, "split_id", f"{source_name} validation")
    validation_ids: list[str] = []
    seen: set[str] = set()
    for order, row in enumerate(rows):
        sample_id = str(row.get("sample_id", "")).strip()
        if not sample_id:
            raise SharedB0ViewError(f"{source_name} 验证清单第 {order} 行缺少 sample_id")
        if sample_id in seen:
            raise SharedB0ViewError(f"{source_name} 验证清单 sample_id 重复：{sample_id}")
        if row.get("suite_id") != expected_suite or row.get("split_id") != expected_split:
            raise SharedB0ViewError(f"{source_name} 验证清单套件或划分不一致：{sample_id}")
        if row.get("samples_sha256") != samples_sha256:
            raise SharedB0ViewError(f"{source_name} 验证清单样本表绑定失配：{sample_id}")
        if sample_id in candidate_ids:
            raise SharedB0ViewError(f"{source_name} 训练与验证样本重叠：{sample_id}")
        seen.add(sample_id)
        validation_ids.append(sample_id)
    return validation_ids, _string(validation, "group_field", f"{source_name} validation")


def _load_parquet_source(
    path: Path,
    sample_ids: set[str],
    columns: Sequence[str],
    description: str,
) -> dict[str, dict[str, object]]:
    try:
        frame = pd.read_parquet(path, columns=list(columns))
    except Exception as error:
        raise SharedB0ViewError(f"无法读取{description} Parquet：{path}") from error
    frame["sample_id"] = frame["sample_id"].astype(str)
    selected = frame[frame["sample_id"].isin(sample_ids)].copy()
    if selected["sample_id"].duplicated().any():
        raise SharedB0ViewError(f"{description}候选 sample_id 重复")
    observed = set(selected["sample_id"])
    if observed != sample_ids:
        missing = sorted(sample_ids.difference(observed))
        raise SharedB0ViewError(f"{description}缺少选定样本：{missing[0] if missing else ''}")
    return {str(row["sample_id"]): row for row in selected.to_dict(orient="records")}


def _assert_group_disjoint(
    records: Mapping[str, Mapping[str, object]],
    candidate_ids: set[str],
    validation_ids: set[str],
    group_field: str,
    description: str,
) -> None:
    def groups(sample_ids: set[str]) -> set[str]:
        values: set[str] = set()
        for sample_id in sample_ids:
            value = str(records[sample_id].get(group_field, "")).strip()
            if not value:
                raise SharedB0ViewError(f"{description}样本缺少分组字段 {group_field}：{sample_id}")
            values.add(value)
        return values

    overlap = groups(candidate_ids).intersection(groups(validation_ids))
    if overlap:
        raise SharedB0ViewError(f"{description}训练与验证分组重叠：{sorted(overlap)[0]}")


def _public_validation_views(
    sample_ids: Sequence[str],
    records: Mapping[str, Mapping[str, object]],
    mapper,
    description: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    common_records: list[dict[str, object]] = []
    qwen_records: list[dict[str, object]] = []
    bert_records: list[dict[str, object]] = []
    for stable_order, sample_id in enumerate(sample_ids):
        source_record = records[sample_id]
        common = mapper(source_record)
        label = _normalise_binary_label(source_record.get("binary_label"), f"{description} ")
        input_text = render_input_text(common)
        common_records.append({"sample_id": sample_id, "stable_order": stable_order, **common})
        qwen_records.append(
            {
                "sample_id": sample_id,
                "stable_order": stable_order,
                "prompt": _qwen_prompt(input_text),
                "completion": _canonical_json({"binary_label": label}),
            }
        )
        bert_records.append(
            {
                "sample_id": sample_id,
                "stable_order": stable_order,
                "text": input_text,
                "label": 0 if label == "benign" else 1,
            }
        )
    _assert_no_input_leakage(common_records)
    if [record["sample_id"] for record in common_records] != list(sample_ids):
        raise SharedB0ViewError(f"{description}验证视图没有保持冻结清单顺序")
    return common_records, qwen_records, bert_records


def _load_ns3_sources(
    project_root: Path,
    source_config: Mapping[str, object],
    sample_ids: set[str],
    input_hashes: dict[str, str],
) -> dict[str, dict[str, object]]:
    files = source_config.get("files")
    if not isinstance(files, list) or not files:
        raise SharedB0ViewError("ns-3 files 必须是非空列表")
    records: dict[str, dict[str, object]] = {}
    for index, raw_file in enumerate(files):
        file_config = _mapping(raw_file, f"ns-3 files[{index}]")
        path, relative = _project_path(project_root, file_config.get("path"), "ns-3 文件")
        input_hashes[relative] = _verify_file(
            path, file_config.get("sha256"), f"ns-3 文件 {relative}"
        )
        for row in _read_jsonl(path, f"ns-3 文件 {relative}"):
            sample_id = str(row.get("sample_id", "")).strip()
            if sample_id not in sample_ids:
                continue
            if sample_id in records:
                raise SharedB0ViewError(f"ns-3 候选 sample_id 重复：{sample_id}")
            records[sample_id] = row
    if set(records) != sample_ids:
        missing = sorted(sample_ids.difference(records))
        raise SharedB0ViewError(f"ns-3 缺少候选样本：{missing[0] if missing else ''}")
    return records


def _verify_budget_binding(
    project_root: Path,
    dataset_config: Mapping[str, object],
    input_hashes: dict[str, str],
) -> tuple[Path, str, Path, str]:
    master_config = _mapping(dataset_config.get("master_records"), "master_records")
    master_path, master_relative = _project_path(
        project_root, master_config.get("path"), "master_records.path"
    )
    master_sha = _verify_file(master_path, master_config.get("sha256"), "统一主索引")
    input_hashes[master_relative] = master_sha

    checksums_config = _mapping(dataset_config.get("budget_checksums"), "budget_checksums")
    checksums_path, checksums_relative = _project_path(
        project_root, checksums_config.get("path"), "budget_checksums.path"
    )
    checksums_sha = _verify_file(
        checksums_path, checksums_config.get("sha256"), "统一预算校验和清单"
    )
    input_hashes[checksums_relative] = checksums_sha
    checksums = _read_json(checksums_path, "统一预算校验和清单")
    artifacts = _mapping(checksums.get("artifacts"), "budget_checksums.artifacts")

    candidate_config = _mapping(dataset_config.get("candidate_manifest"), "candidate_manifest")
    candidate_path, candidate_relative = _project_path(
        project_root, candidate_config.get("path"), "candidate_manifest.path"
    )
    checksum_entry = _string(candidate_config, "checksum_entry", "candidate_manifest")
    artifact = _mapping(artifacts.get(checksum_entry), f"预算制品 {checksum_entry}")
    candidate_sha = _verify_file(candidate_path, artifact.get("sha256"), "统一候选预算清单")
    input_hashes[candidate_relative] = candidate_sha
    return master_path, master_sha, candidate_path, candidate_sha


def _validate_master_membership(
    master_path: Path,
    sample_ids: Sequence[str],
    source_by_id: Mapping[str, str],
) -> None:
    try:
        master = pd.read_parquet(master_path, columns=["sample_id", "source_dataset"])
    except Exception as error:
        raise SharedB0ViewError("无法读取统一主索引成员字段") from error
    candidate_ids = set(sample_ids)
    selected = master[master["sample_id"].astype(str).isin(candidate_ids)].copy()
    selected["sample_id"] = selected["sample_id"].astype(str)
    if selected["sample_id"].duplicated().any() or set(selected["sample_id"]) != candidate_ids:
        raise SharedB0ViewError("统一主索引未唯一覆盖候选清单")
    actual = selected.set_index("sample_id")["source_dataset"].astype(str).to_dict()
    mismatched = [
        sample_id for sample_id in sample_ids if actual[sample_id] != source_by_id[sample_id]
    ]
    if mismatched:
        raise SharedB0ViewError(f"统一主索引来源绑定失配：{mismatched[0]}")


def _validated_numeric_list(value: object, length: int, description: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise SharedB0ViewError(f"{description}必须是长度为 {length} 的列表")
    numbers = [_finite_or_none(item, description) for item in value]
    if any(number is None for number in numbers):
        raise SharedB0ViewError(f"{description}不得缺失")
    return [float(number) for number in numbers if number is not None]


def _validated_physics_mapping(
    source_record: Mapping[str, object], key: str, expected_length: int
) -> dict[str, list[float]]:
    mapping = _mapping(source_record.get(key), f"ns-3 {key}")
    if not mapping:
        raise SharedB0ViewError(f"ns-3 {key}不得为空")
    return {
        str(field): _validated_numeric_list(values, expected_length, f"ns-3 {key}.{field}")
        for field, values in mapping.items()
    }


def _physics_record(
    sample_id: str,
    stable_order: int,
    common: Mapping[str, object],
    source_record: Mapping[str, object],
    label: str,
) -> dict[str, object]:
    state_supervision = _validated_physics_mapping(source_record, "state_supervision", 4)
    anchors = _validated_numeric_list(
        source_record.get("queue_boundary_anchors_l3_bytes"),
        5,
        "ns-3 queue_boundary_anchors_l3_bytes",
    )
    normalized_physics = _validated_physics_mapping(source_record, "normalized_physics", 4)
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "sample_id": sample_id,
        "stable_order": stable_order,
        "model_input": {field: common[field] for field in (*COMMON_FIELDS, *MASK_FIELDS)},
        "target": {"binary_label": label},
        "state_supervision": state_supervision,
        "queue_boundary_anchors_l3_bytes": anchors,
        "normalized_physics": normalized_physics,
    }


def _assert_no_input_leakage(records: Sequence[Mapping[str, object]]) -> None:
    allowed_keys = {"sample_id", "stable_order", *COMMON_FIELDS, *MASK_FIELDS}
    for record in records:
        unexpected = set(record).difference(allowed_keys)
        if unexpected:
            raise SharedB0ViewError(f"公共特征包含未授权字段：{', '.join(sorted(unexpected))}")
    input_key_tokens = {
        token for key in (*COMMON_FIELDS, *MASK_FIELDS) for token in key.lower().split("_")
    }
    forbidden = input_key_tokens.intersection(FORBIDDEN_INPUT_TOKENS)
    if forbidden:
        raise SharedB0ViewError(f"公共字段命中泄漏词：{', '.join(sorted(forbidden))}")


def _artifact_checksums(output_dir: Path) -> dict[str, object]:
    excluded = {
        "_INCOMPLETE",
        "materialization_state.json",
        "checksums.json",
        "freeze_manifest.json",
    }
    paths = sorted(
        path for path in output_dir.rglob("*") if path.is_file() and path.name not in excluded
    )
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "artifacts": {
            path.relative_to(output_dir).as_posix(): {
                "sha256": file_sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in paths
        },
    }


def materialize_shared_b0_view(
    project_root: Path,
    config_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """物化候选共享视图并在全部门禁通过后原子发布。"""
    root = project_root.expanduser().resolve()
    if not root.is_dir():
        raise SharedB0ViewError(f"项目根目录不存在：{root}")
    config_file = config_path.expanduser().resolve()
    config = _read_yaml(config_file)
    publication = _mapping(config.get("publication"), "publication")
    configured_output, output_relative = _project_path(
        root, publication.get("output"), "publication.output"
    )
    output = output_dir.expanduser().resolve()
    if output != configured_output:
        raise SharedB0ViewError(
            f"命令输出目录必须与 publication.output 一致：{output} != {configured_output}"
        )
    partial_suffix = _string(publication, "partial_suffix", "publication")
    if partial_suffix != ".partial":
        raise SharedB0ViewError("publication.partial_suffix 必须固定为 .partial")
    if not _boolean(publication, "refuse_overwrite", "publication"):
        raise SharedB0ViewError("publication.refuse_overwrite 必须为 true")
    if not _boolean(publication, "require_atomic_rename", "publication"):
        raise SharedB0ViewError("publication.require_atomic_rename 必须为 true")
    partial = output.with_name(output.name + partial_suffix)
    if output.exists() or output.is_symlink():
        raise SharedB0ViewError(f"输出目录已存在，拒绝覆盖：{output}")
    if partial.exists() or partial.is_symlink():
        raise SharedB0ViewError(f"未完成目录已存在，拒绝覆盖：{partial}")
    partial.mkdir(parents=True)
    marker = partial / "_INCOMPLETE"
    marker.write_text("incomplete\n", encoding="ascii")
    state_path = partial / "materialization_state.json"
    state: dict[str, object] = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "status": "running",
        "config_sha256": file_sha256(config_file),
        "output_relative": output_relative,
    }
    _write_json(state_path, state)

    try:
        dataset_config = _mapping(config.get("dataset"), "dataset")
        input_hashes: dict[str, str] = {}
        master_path, master_sha, candidate_path, candidate_sha = _verify_budget_binding(
            root, dataset_config, input_hashes
        )
        candidate_config = _mapping(dataset_config.get("candidate_manifest"), "candidate_manifest")
        candidate_rows = _read_jsonl(candidate_path, "统一候选预算清单")
        sample_ids, source_by_id = _candidate_contract(candidate_rows, candidate_config, master_sha)
        _validate_master_membership(master_path, sample_ids, source_by_id)

        source_configs = _mapping(config.get("sources"), "sources")
        if set(source_configs) != set(EXPECTED_SOURCE_NAMES):
            raise SharedB0ViewError("sources 必须恰好包含 genis、tqhc2、ns3")
        genis_ids = {sample_id for sample_id in sample_ids if source_by_id[sample_id] == "genis"}
        tqh_ids = {sample_id for sample_id in sample_ids if source_by_id[sample_id] == "tqhc2"}
        ns3_ids = {sample_id for sample_id in sample_ids if source_by_id[sample_id] == "ns3"}

        genis_config = _mapping(source_configs.get("genis"), "sources.genis")
        genis_path, genis_relative = _project_path(
            root, genis_config.get("samples_path"), "sources.genis.samples_path"
        )
        genis_samples_sha = _verify_file(
            genis_path, genis_config.get("samples_sha256"), "GeNIS 样本表"
        )
        input_hashes[genis_relative] = genis_samples_sha
        genis_validation_ids, genis_group_field = _validation_contract(
            root,
            genis_config,
            "GeNIS",
            genis_samples_sha,
            genis_ids,
            input_hashes,
        )
        genis_all_ids = genis_ids | set(genis_validation_ids)
        genis_columns = [
            "sample_id",
            "binary_label",
            genis_group_field,
            *COMMON_FIELDS,
            *MASK_FIELDS,
        ]
        genis_records = _load_parquet_source(genis_path, genis_all_ids, genis_columns, "GeNIS")
        _assert_group_disjoint(
            genis_records,
            genis_ids,
            set(genis_validation_ids),
            genis_group_field,
            "GeNIS ",
        )

        tqh_config = _mapping(source_configs.get("tqhc2"), "sources.tqhc2")
        tqh_path, tqh_relative = _project_path(
            root, tqh_config.get("samples_path"), "sources.tqhc2.samples_path"
        )
        tqh_samples_sha = _verify_file(tqh_path, tqh_config.get("samples_sha256"), "TQH-C2 样本表")
        input_hashes[tqh_relative] = tqh_samples_sha
        tqh_validation_ids, tqh_group_field = _validation_contract(
            root,
            tqh_config,
            "TQH-C2",
            tqh_samples_sha,
            tqh_ids,
            input_hashes,
        )
        tqh_all_ids = tqh_ids | set(tqh_validation_ids)
        tqh_columns = [
            "sample_id",
            "binary_label",
            tqh_group_field,
            "packet_count",
            "flow_duration_us",
            "network_bytes_total",
            "network_bytes_mean",
            "network_bytes_min",
            "network_bytes_max",
            "delta_time_us_mean",
        ]
        tqh_records = _load_parquet_source(tqh_path, tqh_all_ids, tqh_columns, "TQH-C2")
        _assert_group_disjoint(
            tqh_records,
            tqh_ids,
            set(tqh_validation_ids),
            tqh_group_field,
            "TQH-C2 ",
        )

        ns3_config = _mapping(source_configs.get("ns3"), "sources.ns3")
        ns3_records = _load_ns3_sources(root, ns3_config, ns3_ids, input_hashes)

        genis_validation_common, genis_validation_qwen, genis_validation_bert = (
            _public_validation_views(
                genis_validation_ids,
                genis_records,
                map_genis_row,
                "GeNIS",
            )
        )
        tqh_validation_common, tqh_validation_qwen, tqh_validation_bert = _public_validation_views(
            tqh_validation_ids,
            tqh_records,
            map_tqhc2_row,
            "TQH-C2",
        )

        common_records: list[dict[str, object]] = []
        qwen_records: list[dict[str, object]] = []
        bert_records: list[dict[str, object]] = []
        physics_records: list[dict[str, object]] = []
        label_counts: Counter[str] = Counter()
        missing_counts: Counter[str] = Counter()
        for stable_order, sample_id in enumerate(sample_ids):
            source = source_by_id[sample_id]
            if source == "genis":
                source_record = genis_records[sample_id]
                common = map_genis_row(source_record)
                label = _normalise_binary_label(source_record.get("binary_label"), "GeNIS ")
            elif source == "tqhc2":
                source_record = tqh_records[sample_id]
                common = map_tqhc2_row(source_record)
                label = _normalise_binary_label(source_record.get("binary_label"), "TQH-C2 ")
            else:
                source_record = ns3_records[sample_id]
                common = map_ns3_record(source_record)
                label = _ns3_binary_label(source_record)
                physics_records.append(
                    _physics_record(sample_id, stable_order, common, source_record, label)
                )
            feature_record: dict[str, object] = {
                "sample_id": sample_id,
                "stable_order": stable_order,
                **common,
            }
            input_text = render_input_text(common)
            common_records.append(feature_record)
            qwen_records.append(
                {
                    "sample_id": sample_id,
                    "stable_order": stable_order,
                    "prompt": _qwen_prompt(input_text),
                    "completion": _canonical_json({"binary_label": label}),
                }
            )
            bert_records.append(
                {
                    "sample_id": sample_id,
                    "stable_order": stable_order,
                    "text": input_text,
                    "label": 0 if label == "benign" else 1,
                }
            )
            label_counts[label] += 1
            for field in COMMON_FIELDS:
                missing_counts[field] += int(common[f"{field}_missing"])

        _assert_no_input_leakage(common_records)
        if [record["sample_id"] for record in common_records] != sample_ids:
            raise SharedB0ViewError("公共视图没有保持候选清单顺序")
        if len(physics_records) != len(ns3_ids):
            raise SharedB0ViewError("ns-3 物理视图数量与候选清单不一致")

        candidate_dir = partial / "candidate"
        validation_dir = partial / "validation"
        physics_dir = partial / "physics"
        manifests_dir = partial / "manifests"
        candidate_dir.mkdir(parents=True)
        validation_dir.mkdir(parents=True)
        physics_dir.mkdir(parents=True)
        manifests_dir.mkdir(parents=True)
        common_frame = pd.DataFrame(common_records, columns=list(FEATURE_COLUMNS))
        common_frame.to_parquet(
            candidate_dir / "common_features.parquet",
            index=False,
            engine="pyarrow",
            compression="zstd",
        )
        _write_jsonl(candidate_dir / "qwen_train.jsonl", qwen_records)
        pd.DataFrame(bert_records).to_parquet(
            candidate_dir / "bert_train.parquet",
            index=False,
            engine="pyarrow",
            compression="zstd",
        )
        _write_jsonl(physics_dir / "ns3_candidate.jsonl", physics_records)
        for source_name, validation_common, validation_qwen, validation_bert in (
            (
                "genis",
                genis_validation_common,
                genis_validation_qwen,
                genis_validation_bert,
            ),
            (
                "tqhc2",
                tqh_validation_common,
                tqh_validation_qwen,
                tqh_validation_bert,
            ),
        ):
            pd.DataFrame(validation_common, columns=list(FEATURE_COLUMNS)).to_parquet(
                validation_dir / f"{source_name}_common_features.parquet",
                index=False,
                engine="pyarrow",
                compression="zstd",
            )
            _write_jsonl(validation_dir / f"{source_name}_qwen.jsonl", validation_qwen)
            pd.DataFrame(validation_bert).to_parquet(
                validation_dir / f"{source_name}_bert.parquet",
                index=False,
                engine="pyarrow",
                compression="zstd",
            )

        input_binding = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "config_sha256": file_sha256(config_file),
            "master_records_sha256": master_sha,
            "candidate_manifest_sha256": candidate_sha,
            "validation_manifest_sha256": {
                "genis": input_hashes[
                    _normalise_relative_path(
                        _mapping(genis_config.get("validation_manifest"), "GeNIS validation").get(
                            "path"
                        ),
                        "GeNIS validation.path",
                    )
                ],
                "tqhc2": input_hashes[
                    _normalise_relative_path(
                        _mapping(tqh_config.get("validation_manifest"), "TQH-C2 validation").get(
                            "path"
                        ),
                        "TQH-C2 validation.path",
                    )
                ],
            },
            "input_sha256": dict(sorted(input_hashes.items())),
        }
        _write_json(manifests_dir / "input_binding.json", input_binding)
        statistics = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "stage": _string(config, "stage", "config"),
            "status": _string(config, "status", "config"),
            "candidate_count": len(common_records),
            "source_counts": dict(sorted(Counter(source_by_id.values()).items())),
            "label_counts": dict(sorted(label_counts.items())),
            "missing_counts": dict(sorted(missing_counts.items())),
            "physics_count": len(physics_records),
            "stable_order_sha256": hashlib.sha256(
                "\n".join(sample_ids).encode("utf-8")
            ).hexdigest(),
            "validation": {
                "genis": {
                    "count": len(genis_validation_ids),
                    "stable_order_sha256": hashlib.sha256(
                        "\n".join(genis_validation_ids).encode("utf-8")
                    ).hexdigest(),
                    "sample_overlap_count": len(genis_ids.intersection(genis_validation_ids)),
                    "group_overlap_count": 0,
                },
                "tqhc2": {
                    "count": len(tqh_validation_ids),
                    "stable_order_sha256": hashlib.sha256(
                        "\n".join(tqh_validation_ids).encode("utf-8")
                    ).hexdigest(),
                    "sample_overlap_count": len(tqh_ids.intersection(tqh_validation_ids)),
                    "group_overlap_count": 0,
                },
            },
        }
        _write_json(manifests_dir / "statistics.json", statistics)
        checksums = _artifact_checksums(partial)
        _write_json(manifests_dir / "checksums.json", checksums)
        for relative, artifact in checksums["artifacts"].items():
            artifact_path = partial / relative
            if file_sha256(artifact_path) != artifact["sha256"]:
                raise SharedB0ViewError(f"派生制品哈希复核失败：{relative}")
        freeze_manifest = {
            "schema_version": ARTIFACT_SCHEMA_VERSION,
            "stage": _string(config, "stage", "config"),
            "status": _string(config, "status", "config"),
            "candidate_count": len(common_records),
            "validation_counts": {
                "genis": len(genis_validation_ids),
                "tqhc2": len(tqh_validation_ids),
            },
            "atomic_publication": True,
            "output_relative": output_relative,
            "partial_suffix": partial_suffix,
            "input_binding_sha256": file_sha256(manifests_dir / "input_binding.json"),
            "checksums_sha256": file_sha256(manifests_dir / "checksums.json"),
            "implementation_sha256": file_sha256(Path(__file__)),
        }
        _write_json(manifests_dir / "freeze_manifest.json", freeze_manifest)

        state["status"] = "finished"
        _write_json(state_path, state)
        marker.unlink()
        state_path.unlink()
        os.replace(partial, output)
    except BaseException as error:
        if partial.exists():
            state["status"] = (
                "interrupted" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "failed"
            )
            state["error_type"] = type(error).__name__
            try:
                marker.write_text("incomplete\n", encoding="ascii")
                _write_json(state_path, state)
            except OSError:
                pass
        raise

    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "status": _string(config, "status", "config"),
        "candidate_count": len(common_records),
        "source_counts": dict(sorted(Counter(source_by_id.values()).items())),
        "physics_count": len(physics_records),
        "validation_counts": {
            "genis": len(genis_validation_ids),
            "tqhc2": len(tqh_validation_ids),
        },
        "output_dir": str(output),
        "freeze_manifest_sha256": file_sha256(output / "manifests" / "freeze_manifest.json"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建三源共享预算 B0 派生视图")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = materialize_shared_b0_view(
            project_root=args.project_root,
            config_path=args.config,
            output_dir=args.output,
        )
    except SharedB0ViewError as error:
        print(str(error))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
