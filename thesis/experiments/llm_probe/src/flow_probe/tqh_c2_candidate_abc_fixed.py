"""按固定 36-cell 清单物化 TQH-C2 A/B/C 预算候选协议。"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from flow_probe.tqh_c2_candidate import (
    MODEL_FEATURE_FIELDS,
    REQUIRED_PACKET_COLUMNS,
    SENSITIVE_FIELD_TOKENS,
    TREE_VIEW_NAME,
    TQHC2CandidateError,
    _aggregate_features,
    _field_roles,
    _sha256_file,
    _write_json,
    _write_jsonl,
    _write_yaml,
)
from flow_probe.tqh_c2_candidate_abc import (
    CANDIDATE_ID,
    DATASET_VERSION,
    EXPECTED_CELL_COUNTS,
    EXPECTED_INTERVALS,
    EXPECTED_JITTERS,
    EXPECTED_PROFILES,
    PROTOCOL_PHASE,
    PROTOCOL_STATUS,
    PROTOCOL_VERSION,
    REVIEW_STATUS,
    SPLIT_FILENAMES,
    SPLIT_IDS,
    SUITE_IDS,
    TQHC2ABCCandidateError,
    _build_base_groups,
    _build_samples,
    _load_masters,
    _sequence_hash,
    _validate_packet_frame,
)

BUDGET_SAMPLING_ALGORITHM = "tqhc2-abc-budget-v1"
FIXED_ASSIGNMENT_SCHEMA_VERSION = "tqhc2-abc-fixed-assignment-v1"
EXPECTED_BUDGET_SAMPLE_COUNT = 35_235
EXPECTED_BUDGET_PACKET_COUNT = 2_475_729
_ASSIGNMENT_CELL_FIELDS = (
    "allocation_group_id",
    "capture_group_id",
    "profile",
    "interval_s",
    "jitter_pct",
    "source_capture_sha256",
    "mapped_count",
    "benign_count",
    "malicious_count",
)
_PACKET_MASTER_FIELDS = (
    "sample_id",
    "profile",
    "capture_group_id",
    "packet_count_kept",
)


class TQHC2ABCFixedError(TQHC2ABCCandidateError):
    """固定预算物化输入、清单或输出不满足合同。"""


def _read_assignment(path: Path) -> tuple[dict[str, object], str]:
    path = Path(path).expanduser().resolve()
    try:
        payload = path.read_bytes()
        document = json.loads(payload)
    except (OSError, json.JSONDecodeError) as error:
        raise TQHC2ABCFixedError(f"无法读取固定分配清单：{path}") from error
    if not isinstance(document, dict):
        raise TQHC2ABCFixedError("固定分配清单必须是 JSON 对象")
    if document.get("schema_version") != FIXED_ASSIGNMENT_SCHEMA_VERSION:
        raise TQHC2ABCFixedError("固定分配清单版本不符合合同")
    return document, hashlib.sha256(payload).hexdigest()


def _require_sequence(value: object, description: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise TQHC2ABCFixedError(f"{description}必须是列表")
    return value


def _normalised_cell_records(base_groups: pd.DataFrame) -> list[dict[str, object]]:
    missing = sorted(set(_ASSIGNMENT_CELL_FIELDS).difference(base_groups.columns))
    if missing:
        raise TQHC2ABCFixedError(f"36-cell 基表缺少字段：{','.join(missing)}")
    if len(base_groups) != 36 or base_groups["capture_group_id"].duplicated().any():
        raise TQHC2ABCFixedError("36-cell 基表必须恰好包含 36 个互异 cell")
    return (
        base_groups.loc[:, list(_ASSIGNMENT_CELL_FIELDS)]
        .sort_values("capture_group_id", kind="mergesort")
        .to_dict(orient="records")
    )


def _validate_cell_binding(document: Mapping[str, object], base_groups: pd.DataFrame) -> None:
    raw_cells = _require_sequence(document.get("cells"), "固定清单 cells")
    if not all(isinstance(row, Mapping) for row in raw_cells):
        raise TQHC2ABCFixedError("固定清单 cells 每行必须是对象")
    expected_rows = _normalised_cell_records(base_groups)
    expected_by_id = {str(row["capture_group_id"]): row for row in expected_rows}
    actual_ids = [str(row.get("capture_group_id", "")) for row in raw_cells]
    if len(actual_ids) != len(set(actual_ids)):
        raise TQHC2ABCFixedError("固定清单 cells 包含重复 cell")
    if set(actual_ids) != set(expected_by_id):
        raise TQHC2ABCFixedError("固定清单与基表的 cell 集合不一致")
    for raw_row in raw_cells:
        cell_id = str(raw_row["capture_group_id"])
        expected = expected_by_id[cell_id]
        for field_name in _ASSIGNMENT_CELL_FIELDS:
            actual_value = raw_row.get(field_name)
            expected_value = expected[field_name]
            if field_name in {
                "interval_s",
                "jitter_pct",
                "mapped_count",
                "benign_count",
                "malicious_count",
            }:
                try:
                    matches = int(actual_value) == int(expected_value)
                except (TypeError, ValueError):
                    matches = False
            else:
                matches = str(actual_value) == str(expected_value)
            if not matches:
                raise TQHC2ABCFixedError(f"固定清单 cell 绑定字段不一致：{cell_id}:{field_name}")


def _coverage_is_valid(suite_id: str, assignments: pd.DataFrame, held_out: str | None) -> bool:
    conditions = {
        split_id: {
            "profiles": set(frame["profile"].astype(str)),
            "intervals": set(frame["interval_s"].astype(int)),
            "jitters": set(frame["jitter_pct"].astype(int)),
            "cell_count": len(frame),
        }
        for split_id, frame in assignments.groupby("split_id", sort=True, observed=True)
    }
    if set(conditions) != set(SPLIT_IDS):
        return False
    expected_counts = EXPECTED_CELL_COUNTS[suite_id]
    if any(
        conditions[split_id]["cell_count"] != expected_counts[split_id] for split_id in SPLIT_IDS
    ):
        return False
    expected_intervals = set(EXPECTED_INTERVALS)
    expected_jitters = set(EXPECTED_JITTERS)
    if suite_id == "tqhc2_cell_indomain":
        return all(
            conditions[split_id]["profiles"] == set(EXPECTED_PROFILES)
            and conditions[split_id]["intervals"] == expected_intervals
            and conditions[split_id]["jitters"] == expected_jitters
            for split_id in ("validation", "test")
        )
    if held_out is None:
        return False
    source_profiles = set(EXPECTED_PROFILES).difference({held_out})
    validation = conditions["validation"]
    test = conditions["test"]
    return (
        validation["profiles"] == source_profiles
        and validation["intervals"] == expected_intervals
        and len(validation["jitters"]) >= 2
        and test["profiles"] == {held_out}
        and test["cell_count"] == 12
    )


def load_fixed_suite_groups(
    path: Path, base_groups: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """只读加载固定四套 cell 分配，并绑定到当前 36-cell 基表。"""
    document, assignment_sha256 = _read_assignment(path)
    _validate_cell_binding(document, base_groups)
    raw_suites = _require_sequence(document.get("suites"), "固定清单 suites")
    if not all(isinstance(row, Mapping) for row in raw_suites):
        raise TQHC2ABCFixedError("固定清单 suites 每项必须是对象")
    suite_ids = [str(row.get("suite_id", "")) for row in raw_suites]
    if len(suite_ids) != len(set(suite_ids)):
        raise TQHC2ABCFixedError("固定清单包含重复套件")
    if set(suite_ids) != set(SUITE_IDS):
        raise TQHC2ABCFixedError("固定清单套件集合不符合合同")

    cell_metadata = base_groups.set_index("capture_group_id", drop=False)
    expected_cell_ids = set(cell_metadata.index.astype(str))
    output_rows: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    for raw_suite in raw_suites:
        suite_id = str(raw_suite["suite_id"])
        expected_held_out = (
            None if suite_id == "tqhc2_cell_indomain" else suite_id.rsplit("_", 1)[-1]
        )
        raw_held_out = raw_suite.get("held_out_profile")
        held_out = None if raw_held_out is None else str(raw_held_out)
        if held_out != expected_held_out:
            raise TQHC2ABCFixedError(f"固定套件留出 profile 错误：{suite_id}")
        raw_assignments = _require_sequence(raw_suite.get("assignments"), f"{suite_id} assignments")
        if not all(isinstance(row, Mapping) for row in raw_assignments):
            raise TQHC2ABCFixedError(f"{suite_id} assignments 每项必须是对象")
        assignment_ids = [str(row.get("capture_group_id", "")) for row in raw_assignments]
        if len(assignment_ids) != len(set(assignment_ids)):
            raise TQHC2ABCFixedError(f"固定套件包含重复 cell：{suite_id}")
        if set(assignment_ids) != expected_cell_ids:
            raise TQHC2ABCFixedError(f"固定套件 cell 集合不一致：{suite_id}")

        rows: list[dict[str, object]] = []
        for raw_assignment in raw_assignments:
            cell_id = str(raw_assignment["capture_group_id"])
            split_id = str(raw_assignment.get("split_id", ""))
            if split_id not in SPLIT_IDS:
                raise TQHC2ABCFixedError(f"固定套件包含未知 split：{suite_id}:{split_id}")
            profile = str(cell_metadata.loc[cell_id, "profile"])
            expected_role = (
                "in_domain"
                if held_out is None
                else "held_out_profile" if profile == held_out else "source_profile"
            )
            if str(raw_assignment.get("domain_role", "")) != expected_role:
                raise TQHC2ABCFixedError(f"固定套件 domain_role 错误：{suite_id}:{cell_id}")
            rows.append(
                {
                    **cell_metadata.loc[cell_id].to_dict(),
                    "suite_id": suite_id,
                    "split_id": split_id,
                    "domain_role": expected_role,
                }
            )
        suite_frame = pd.DataFrame(rows)
        if not _coverage_is_valid(suite_id, suite_frame, held_out):
            raise TQHC2ABCFixedError(f"固定套件硬覆盖或 cell 数量不符合合同：{suite_id}")
        output_rows.extend(rows)
        audits.append(
            {
                "suite_id": suite_id,
                "assignment_sha256": assignment_sha256,
                "cell_counts": dict(sorted(Counter(suite_frame["split_id"].astype(str)).items())),
                "status": "pass",
            }
        )
    groups = pd.DataFrame(output_rows).sort_values(
        ["suite_id", "split_id", "profile", "capture_group_id"], kind="mergesort"
    )
    return groups.reset_index(drop=True), sorted(audits, key=lambda row: str(row["suite_id"]))


def _sample_manifest_sha256(samples: pd.DataFrame) -> str:
    fields = ("sample_id", "capture_group_id", "binary_label", "packet_count_kept")
    digest = hashlib.sha256()
    for row in samples.loc[:, list(fields)].to_dict(orient="records"):
        digest.update(
            json.dumps(
                row, ensure_ascii=True, allow_nan=False, separators=(",", ":"), sort_keys=True
            ).encode("ascii")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def select_budget_samples(
    master: pd.DataFrame, cap_per_cell: int = 1000
) -> tuple[pd.DataFrame, dict[str, object]]:
    """按 cell 的自然二分类比例确定性选取最多 ``cap_per_cell`` 条映射样本。"""
    if isinstance(cap_per_cell, bool) or not isinstance(cap_per_cell, int) or cap_per_cell <= 0:
        raise TQHC2ABCFixedError("cap_per_cell 必须是正整数")
    required = {
        "sample_id",
        "capture_group_id",
        "profile",
        "binary_label",
        "label_status",
        "packet_count_kept",
    }
    missing = sorted(required.difference(master.columns))
    if missing:
        raise TQHC2ABCFixedError(f"预算主记录缺少字段：{','.join(missing)}")
    mapped = master[master["label_status"].eq("mapped")].copy()
    if mapped.empty:
        raise TQHC2ABCFixedError("预算主记录没有映射样本")
    sample_ids = mapped["sample_id"].astype(str)
    if sample_ids.str.len().eq(0).any() or sample_ids.duplicated().any():
        raise TQHC2ABCFixedError("预算主记录 sample_id 必须非空且全局唯一")
    mapped["sample_id"] = sample_ids

    selected_frames: list[pd.DataFrame] = []
    cell_audits: list[dict[str, object]] = []
    for cell_id, cell in mapped.groupby("capture_group_id", sort=True, observed=True):
        counts = Counter(cell["binary_label"].astype(str))
        if set(counts) != {"benign", "malicious"}:
            raise TQHC2ABCFixedError(f"预算 cell 缺少二分类覆盖：{cell_id}")
        selected_count = min(cap_per_cell, len(cell))
        quotients = {
            label: divmod(selected_count * count, len(cell)) for label, count in counts.items()
        }
        quotas = {label: quotient for label, (quotient, _) in quotients.items()}
        remainder_count = selected_count - sum(quotas.values())
        remainder_order = sorted(counts, key=lambda label: (-quotients[label][1], label))
        for label in remainder_order[:remainder_count]:
            quotas[label] += 1
        if any(quota <= 0 for quota in quotas.values()):
            raise TQHC2ABCFixedError(f"预算 cell 抽样后丢失二分类覆盖：{cell_id}")

        chosen_labels: list[pd.DataFrame] = []
        for label in sorted(counts):
            candidates = cell[cell["binary_label"].astype(str).eq(label)].copy()
            candidates["_budget_order"] = candidates["sample_id"].map(
                lambda sample_id: hashlib.sha256(
                    f"{BUDGET_SAMPLING_ALGORITHM}|{sample_id}".encode("ascii")
                ).hexdigest()
            )
            candidates = candidates.sort_values(
                ["_budget_order", "sample_id"], kind="mergesort"
            ).head(quotas[label])
            chosen_labels.append(candidates.drop(columns="_budget_order"))
        chosen = pd.concat(chosen_labels, ignore_index=True)
        selected_frames.append(chosen)
        cell_audits.append(
            {
                "capture_group_id": str(cell_id),
                "input_count": int(len(cell)),
                "selected_count": int(len(chosen)),
                "input_label_counts": dict(sorted(counts.items())),
                "quotas": dict(sorted(quotas.items())),
            }
        )

    selected = pd.concat(selected_frames, ignore_index=True).sort_values(
        "sample_id", kind="mergesort"
    )
    selected = selected.reset_index(drop=True)
    audit: dict[str, object] = {
        "sampling_algorithm": BUDGET_SAMPLING_ALGORITHM,
        "cap_per_cell": cap_per_cell,
        "source_mapped_sample_count": int(len(mapped)),
        "selected_sample_count": int(len(selected)),
        "selected_packet_count": int(selected["packet_count_kept"].astype("int64").sum()),
        "sample_manifest_sha256": _sample_manifest_sha256(selected),
        "cells": cell_audits,
        "status": "pass",
    }
    return selected, audit


def _validate_target_binding(
    profile: str, target: pd.DataFrame, upstream_master: pd.DataFrame
) -> tuple[set[str], dict[str, str], dict[str, int]]:
    if upstream_master.empty:
        raise TQHC2ABCFixedError(f"上游主记录不得为空：{profile}")
    missing = sorted(set(_PACKET_MASTER_FIELDS).difference(upstream_master.columns))
    if missing:
        raise TQHC2ABCFixedError(f"上游主记录缺少字段：{profile}:{','.join(missing)}")
    upstream_master = upstream_master.copy()
    upstream_master["sample_id"] = upstream_master["sample_id"].astype(str)
    if upstream_master["sample_id"].duplicated().any():
        raise TQHC2ABCFixedError(f"上游主记录 sample_id 重复：{profile}")
    if set(upstream_master["profile"].astype(str)) != {profile}:
        raise TQHC2ABCFixedError(f"上游主记录 profile 绑定错误：{profile}")
    upstream_by_id = upstream_master.set_index("sample_id", drop=False)
    target_ids = set(target["sample_id"].astype(str))
    if not target_ids.issubset(set(upstream_by_id.index.astype(str))):
        raise TQHC2ABCFixedError(f"预算样本不在上游主记录中：{profile}")
    for row in target.loc[:, list(_PACKET_MASTER_FIELDS)].itertuples(index=False):
        upstream = upstream_by_id.loc[str(row.sample_id)]
        if (
            str(row.profile) != profile
            or str(row.capture_group_id) != str(upstream["capture_group_id"])
            or int(row.packet_count_kept) != int(upstream["packet_count_kept"])
        ):
            raise TQHC2ABCFixedError(f"预算样本与上游主记录绑定不一致：{row.sample_id}")
    cell_by_sample = upstream_by_id["capture_group_id"].astype(str).to_dict()
    expected_counts = target.set_index("sample_id")["packet_count_kept"].astype("int64").to_dict()
    return target_ids, cell_by_sample, expected_counts


def filter_and_aggregate_budget_packets(
    master: pd.DataFrame, profile_dirs: Mapping[str, Path]
) -> tuple[pd.DataFrame, dict[str, str], list[dict[str, object]]]:
    """顺序扫描完整包表，只聚合冻结预算清单中的目标样本。"""
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise TQHC2ABCFixedError("过滤读取 Parquet 需要项目依赖 pyarrow") from error

    missing = sorted(set(_PACKET_MASTER_FIELDS).difference(master.columns))
    if missing:
        raise TQHC2ABCFixedError(f"预算主记录缺少包绑定字段：{','.join(missing)}")
    budget = master.copy()
    budget["sample_id"] = budget["sample_id"].astype(str)
    if budget["sample_id"].duplicated().any():
        raise TQHC2ABCFixedError("预算主记录 sample_id 重复")
    if set(profile_dirs) != set(EXPECTED_PROFILES):
        raise TQHC2ABCFixedError("profile 目录必须恰好包含 A/B/C")

    feature_frames: list[pd.DataFrame] = []
    sequence_hashes: dict[str, str] = {}
    profile_audits: list[dict[str, object]] = []
    for profile in EXPECTED_PROFILES:
        profile_dir = Path(profile_dirs[profile]).expanduser().resolve()
        master_path = profile_dir / "master_records.parquet"
        packet_path = profile_dir / "views" / "packet_observations.parquet"
        try:
            upstream_master = pd.read_parquet(master_path, columns=list(_PACKET_MASTER_FIELDS))
            parquet = pq.ParquetFile(packet_path)
        except Exception as error:
            raise TQHC2ABCFixedError(f"无法读取 {profile} 主记录或包表") from error
        target = budget[budget["profile"].astype(str).eq(profile)]
        if target.empty:
            raise TQHC2ABCFixedError(f"预算清单缺少 profile：{profile}")
        target_ids, cell_by_sample, expected_counts = _validate_target_binding(
            profile, target, upstream_master
        )
        missing_columns = sorted(REQUIRED_PACKET_COLUMNS.difference(parquet.schema_arrow.names))
        if missing_columns:
            raise TQHC2ABCFixedError(f"{profile} 包观测缺少字段：{','.join(missing_columns)}")

        retained_frames: list[pd.DataFrame] = []
        scanned_count = 0
        retained_count = 0
        current_cell: str | None = None
        closed_cells: set[str] = set()
        last_packet_index: dict[str, int] = {}
        for row_group_index in range(parquet.num_row_groups):
            location = f"{profile}:row_group={row_group_index}"
            frame = parquet.read_row_group(
                row_group_index, columns=sorted(REQUIRED_PACKET_COLUMNS)
            ).to_pandas()
            try:
                _validate_packet_frame(frame, location)
            except TQHC2CandidateError as error:
                raise TQHC2ABCFixedError(str(error)) from error
            scanned_count += len(frame)
            sample_ids = frame["sample_id"].astype(str)
            unknown_ids = sorted(set(sample_ids).difference(cell_by_sample))
            if unknown_ids:
                raise TQHC2ABCFixedError(f"包观测包含未知 sample_id：{location}:{unknown_ids[0]}")
            cells = {cell_by_sample[sample_id] for sample_id in sample_ids}
            if len(cells) != 1:
                raise TQHC2ABCFixedError(f"Parquet 行组混入多个 cell：{location}")
            cell_id = next(iter(cells))
            if cell_id != current_cell:
                if current_cell is not None:
                    closed_cells.add(current_cell)
                if cell_id in closed_cells:
                    raise TQHC2ABCFixedError(f"cell 顺序回退：{location}:{cell_id}")
                current_cell = cell_id

            retained = frame[sample_ids.isin(target_ids)].copy()
            if retained.empty:
                continue
            retained["sample_id"] = retained["sample_id"].astype(str)
            for sample_id, raw_index in retained.loc[:, ["sample_id", "packet_index"]].itertuples(
                index=False, name=None
            ):
                packet_index = int(raw_index)
                previous = last_packet_index.get(sample_id)
                if previous is not None and packet_index == previous:
                    raise TQHC2ABCFixedError(f"包序号重复：{sample_id}:{packet_index}")
                if previous is not None and packet_index < previous:
                    raise TQHC2ABCFixedError(f"包序号回退：{sample_id}:{previous}->{packet_index}")
                last_packet_index[sample_id] = packet_index
            retained_count += len(retained)
            retained_frames.append(retained)

        if not retained_frames:
            raise TQHC2ABCFixedError(f"包表未命中预算样本：{profile}")
        retained_packets = pd.concat(retained_frames, ignore_index=True).sort_values(
            ["sample_id", "packet_index"], kind="mergesort"
        )
        observed_ids = set(retained_packets["sample_id"].astype(str))
        if observed_ids != target_ids:
            missing_ids = sorted(target_ids.difference(observed_ids))
            raise TQHC2ABCFixedError(
                f"预算样本缺少包观测：{profile}:{missing_ids[0] if missing_ids else ''}"
            )
        profile_features: list[pd.DataFrame] = []
        for sample_id, frame in retained_packets.groupby("sample_id", sort=True, observed=True):
            indexes = frame["packet_index"].to_numpy(dtype=np.int64)
            if len(indexes) != len(np.unique(indexes)):
                raise TQHC2ABCFixedError(f"包序号重复：{sample_id}")
            if (
                len(indexes) == 0
                or indexes[0] != 0
                or not np.array_equal(indexes, np.arange(len(indexes), dtype=np.int64))
            ):
                raise TQHC2ABCFixedError(f"包序号存在缺口：{sample_id}")
            expected = int(expected_counts[str(sample_id)])
            if len(frame) != expected:
                raise TQHC2ABCFixedError(
                    f"包观测与主记录计数不一致：{sample_id}:{len(frame)}!={expected}"
                )
            try:
                profile_features.append(_aggregate_features(frame))
                sequence_hashes[str(sample_id)] = _sequence_hash(frame)
            except TQHC2CandidateError as error:
                raise TQHC2ABCFixedError(str(error)) from error
        features = pd.concat(profile_features).sort_index(kind="mergesort")
        if tuple(features.columns) != MODEL_FEATURE_FIELDS:
            raise TQHC2ABCFixedError(f"聚合模型字段不符合合同：{profile}")
        numeric = features.loc[:, list(MODEL_FEATURE_FIELDS)].to_numpy(dtype=np.float64)
        if not np.isfinite(numeric).all():
            raise TQHC2ABCFixedError(f"聚合模型字段含非有限值：{profile}")
        feature_frames.append(features)
        profile_audits.append(
            {
                "profile": profile,
                "reader": "pyarrow.parquet.ParquetFile.read_row_group",
                "row_group_count": parquet.num_row_groups,
                "scanned_row_count": int(scanned_count),
                "retained_row_count": int(retained_count),
                "retained_fraction": float(retained_count / scanned_count),
                "packet_table_loaded_whole": False,
                "status": "pass",
            }
        )
        del retained_packets, retained_frames, upstream_master, parquet
        gc.collect()

    all_features = pd.concat(feature_frames).sort_index(kind="mergesort")
    expected_ids = set(budget["sample_id"].astype(str))
    if set(all_features.index.astype(str)) != expected_ids or set(sequence_hashes) != expected_ids:
        raise TQHC2ABCFixedError("聚合特征或序列哈希未覆盖全部预算样本")
    return all_features, sequence_hashes, profile_audits


def _source_artifacts(
    profile_dirs: Mapping[str, Path], assignment_path: Path
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    relative_paths = (
        "master_records.parquet",
        "views/packet_observations.parquet",
        "source_checksums.json",
        "run_manifest.provisional.json",
        "schema.provisional.json",
        "artifact_checksums.provisional.json",
        "audit/cell-audit.json",
        "audit/label-coverage.json",
        "audit/leakage-audit.json",
    )
    for profile in EXPECTED_PROFILES:
        for relative_path in relative_paths:
            path = Path(profile_dirs[profile]) / relative_path
            if path.is_file():
                rows.append(
                    {
                        "profile": profile,
                        "lineage_level": "candidate_input",
                        "role": "derived_input",
                        "source_path": f"{profile}/{relative_path}",
                        "sha256": _sha256_file(path),
                        "size_bytes": path.stat().st_size,
                    }
                )
    for role, path, source_path in (
        ("fixed_assignment", Path(assignment_path), "configs/tqhc2_abc_fixed_assignment_v1.json"),
        ("materializer_source", Path(__file__), "src/flow_probe/tqh_c2_candidate_abc_fixed.py"),
    ):
        rows.append(
            {
                "profile": "ABC",
                "lineage_level": "candidate_builder",
                "role": role,
                "source_path": source_path,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return sorted(rows, key=lambda row: (str(row["profile"]), str(row["source_path"])))


def _write_manifests(
    output_dir: Path, samples: pd.DataFrame, suite_groups: pd.DataFrame
) -> dict[str, str]:
    samples_sha256 = _sha256_file(output_dir / "samples.parquet")
    split_by_suite_cell = {
        (str(row.suite_id), str(row.capture_group_id)): str(row.split_id)
        for row in suite_groups.itertuples(index=False)
    }
    for (suite_id, split_id), relative_path in SPLIT_FILENAMES.items():
        split_by_cell = {
            cell_id: assigned_split
            for (assigned_suite, cell_id), assigned_split in split_by_suite_cell.items()
            if assigned_suite == suite_id
        }
        split_samples = samples[
            samples["capture_group_id"].astype(str).map(split_by_cell).eq(split_id)
        ].sort_values("sample_id", kind="mergesort")
        if split_samples.empty:
            raise TQHC2ABCFixedError(f"套件划分不得为空：{suite_id}:{split_id}")
        _write_jsonl(
            output_dir / relative_path,
            [
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "suite_id": suite_id,
                    "split_id": split_id,
                    "sample_id": str(sample_id),
                    "samples_sha256": samples_sha256,
                }
                for sample_id in split_samples["sample_id"]
            ],
        )
    return {
        "samples.parquet": samples_sha256,
        **{
            relative_path: _sha256_file(output_dir / relative_path)
            for relative_path in SPLIT_FILENAMES.values()
        },
    }


def _suite_audit(samples: pd.DataFrame, suite_groups: pd.DataFrame) -> dict[str, object]:
    audits: dict[str, object] = {}
    for suite_id in SUITE_IDS:
        groups = suite_groups[suite_groups["suite_id"].eq(suite_id)]
        split_by_cell = dict(
            zip(groups["capture_group_id"].astype(str), groups["split_id"].astype(str), strict=True)
        )
        memberships = samples.loc[:, ["sample_id", "capture_group_id", "binary_label"]].copy()
        memberships["split_id"] = memberships["capture_group_id"].astype(str).map(split_by_cell)
        split_counts = Counter(memberships["split_id"].astype(str))
        total = len(memberships)
        target_fractions = {
            split_id: EXPECTED_CELL_COUNTS[suite_id][split_id] / 36 for split_id in SPLIT_IDS
        }
        split_conditions = {
            split_id: {
                "cell_count": int(len(frame)),
                "sample_count": int(split_counts[split_id]),
                "sample_fraction": float(split_counts[split_id] / total),
                "profiles": sorted(set(frame["profile"].astype(str))),
                "intervals": sorted(set(frame["interval_s"].astype(int))),
                "jitters": sorted(set(frame["jitter_pct"].astype(int))),
            }
            for split_id, frame in groups.groupby("split_id", sort=True, observed=True)
        }
        label_coverage = all(
            set(frame["binary_label"].astype(str)) == {"benign", "malicious"}
            for _, frame in memberships.groupby("split_id", sort=True, observed=True)
        )
        if not label_coverage:
            raise TQHC2ABCFixedError(f"套件划分缺少二分类覆盖：{suite_id}")
        audits[suite_id] = {
            "target_sample_fractions": target_fractions,
            "l1_sample_fraction_deviation": float(
                sum(
                    abs(split_conditions[split_id]["sample_fraction"] - target_fractions[split_id])
                    for split_id in SPLIT_IDS
                )
            ),
            "split_conditions": split_conditions,
            "status": "pass",
        }
    return audits


def _artifact_hashes(output_dir: Path, incomplete_marker: Path) -> dict[str, str]:
    artifact_list_path = output_dir / "audit" / "artifact-sha256.txt"
    protocol_path = output_dir / "protocol.yaml"
    paths = sorted(
        (
            path
            for path in output_dir.rglob("*")
            if path.is_file() and path not in {incomplete_marker, artifact_list_path, protocol_path}
        ),
        key=lambda path: path.relative_to(output_dir).as_posix(),
    )
    artifact_list_path.write_text(
        "".join(
            f"{_sha256_file(path)}  {path.relative_to(output_dir).as_posix()}\n" for path in paths
        ),
        encoding="utf-8",
    )
    return {
        path.relative_to(output_dir).as_posix(): _sha256_file(path)
        for path in [*paths, artifact_list_path]
    }


def materialize_candidate_abc_budget(
    *,
    profile_dirs: Mapping[str, Path],
    approved_inputs: Mapping[str, Mapping[str, object]],
    assignment_path: Path,
    cap_per_cell: int = 1000,
    output_dir: Path,
) -> dict[str, object]:
    """使用固定分配和预算样本清单生成兼容 ``FrozenProtocol`` 的候选协议。"""
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise TQHC2ABCFixedError(f"输出目录已存在，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True)
    incomplete_marker = output_dir / "_INCOMPLETE"
    incomplete_marker.write_text('{"status":"incomplete"}\n', encoding="utf-8")
    (output_dir / "splits").mkdir()
    (output_dir / "audit").mkdir()

    try:
        master, resolved_dirs, input_audits = _load_masters(profile_dirs, approved_inputs)
        base_groups = _build_base_groups(master)
        suite_groups, assignment_audits = load_fixed_suite_groups(assignment_path, base_groups)
        budget_master, budget_audit = select_budget_samples(master, cap_per_cell)
        assignment_document, assignment_sha256 = _read_assignment(assignment_path)
        budget_contract = assignment_document.get("budget")
        if not isinstance(budget_contract, Mapping):
            raise TQHC2ABCFixedError("固定分配清单缺少 budget 合同")
        if budget_contract.get("sampling_algorithm") != BUDGET_SAMPLING_ALGORITHM:
            raise TQHC2ABCFixedError("预算抽样算法不符合固定合同")
        try:
            expected_source_samples = int(budget_contract["source_mapped_sample_count"])
        except (KeyError, TypeError, ValueError) as error:
            raise TQHC2ABCFixedError("预算源样本总数合同无效") from error
        if expected_source_samples != int(budget_audit["source_mapped_sample_count"]):
            raise TQHC2ABCFixedError("预算源样本总数不符合固定合同")
        if cap_per_cell == int(budget_contract.get("cap_per_cell", -1)):
            expected_samples = budget_contract.get("expected_sample_count")
            expected_packets = budget_contract.get("expected_packet_count")
            if expected_samples is not None and int(expected_samples) != int(
                budget_audit["selected_sample_count"]
            ):
                raise TQHC2ABCFixedError("预算样本总数不符合固定合同")
            if expected_packets is not None and int(expected_packets) != int(
                budget_audit["selected_packet_count"]
            ):
                raise TQHC2ABCFixedError("预算包总数不符合固定合同")

        features, sequence_hashes, packet_audits = filter_and_aggregate_budget_packets(
            budget_master, resolved_dirs
        )
        samples = _build_samples(budget_master, features, sequence_hashes)
        samples.to_parquet(
            output_dir / "samples.parquet", index=False, engine="pyarrow", compression="zstd"
        )
        suite_groups.to_parquet(
            output_dir / "groups.parquet", index=False, engine="pyarrow", compression="zstd"
        )
        _write_yaml(output_dir / "field-roles.yaml", _field_roles())
        _write_jsonl(
            output_dir / "source-artifacts.jsonl",
            _source_artifacts(resolved_dirs, Path(assignment_path).expanduser().resolve()),
        )
        manifest_hashes = _write_manifests(output_dir, samples, suite_groups)
        _write_json(output_dir / "audit" / "manifest-hashes.json", manifest_hashes)
        _write_json(output_dir / "audit" / "fixed-assignment.json", assignment_audits)
        _write_json(output_dir / "audit" / "budget-sampling.json", budget_audit)
        _write_jsonl(output_dir / "audit" / "packet-filtering.jsonl", packet_audits)
        _write_json(output_dir / "audit" / "suite-audits.json", _suite_audit(samples, suite_groups))
        _write_json(
            output_dir / "audit" / "input-contract.json",
            {
                "dataset_version": DATASET_VERSION,
                "profiles": list(EXPECTED_PROFILES),
                "cells_per_profile": 12,
                "approved_inputs": input_audits,
                "fixed_assignment_sha256": assignment_sha256,
                "sample_manifest_sha256": budget_audit["sample_manifest_sha256"],
                "status": "pass",
            },
        )
        sensitive_hits = [
            field
            for field in MODEL_FEATURE_FIELDS
            if set(field.lower().split("_")).intersection(SENSITIVE_FIELD_TOKENS)
        ]
        if sensitive_hits:
            raise TQHC2ABCFixedError("模型字段包含敏感标签字段")
        _write_json(
            output_dir / "audit" / "field-budget.json",
            {
                "view_name": TREE_VIEW_NAME,
                "model_input_fields": list(MODEL_FEATURE_FIELDS),
                "model_input_field_count": len(MODEL_FEATURE_FIELDS),
                "sensitive_field_hits": sensitive_hits,
                "training_fitted_transformations": [],
                "status": "pass",
            },
        )
        _write_json(
            output_dir / "audit" / "streaming-audit.json",
            {
                "reader": "pyarrow.parquet.ParquetFile.read_row_group",
                "packet_table_loaded_whole": False,
                "profiles": list(EXPECTED_PROFILES),
                "scanned_row_count": int(sum(row["scanned_row_count"] for row in packet_audits)),
                "retained_row_count": int(sum(row["retained_row_count"] for row in packet_audits)),
                "all_row_groups_single_cell": True,
                "all_cell_row_groups_contiguous": True,
                "cell_order_fallback_detected": False,
                "status": "pass",
            },
        )
        artifact_hashes = _artifact_hashes(output_dir, incomplete_marker)
        source_sha256 = _sha256_file(Path(__file__))
        protocol = {
            "protocol_version": PROTOCOL_VERSION,
            "status": PROTOCOL_STATUS,
            "phase": PROTOCOL_PHASE,
            "review_status": REVIEW_STATUS,
            "candidate_id": CANDIDATE_ID,
            "scope": "TQH-C2 profiles A/B/C, fixed 36-cell assignment, capped budget",
            "suite_ids": list(SUITE_IDS),
            "fixed_assignment_sha256": assignment_sha256,
            "sample_manifest_sha256": budget_audit["sample_manifest_sha256"],
            "sampling_algorithm": BUDGET_SAMPLING_ALGORITHM,
            "cap_per_cell": cap_per_cell,
            "materializer_source_sha256": source_sha256,
            "peak_rss_recording_required": True,
            "final_tuning_allowed": False,
            "final_test_claim_allowed": False,
            "artifacts": dict(sorted(artifact_hashes.items())),
            "limitations": [
                "独立审查与双物化完成前保持 review_pending。",
                "最终测试 cell 和留一 profile 测试域不得参与调参或归一化统计。",
            ],
        }
        _write_yaml(output_dir / "protocol.yaml", protocol)
        incomplete_marker.unlink()
        return {
            "candidate_id": CANDIDATE_ID,
            "protocol_version": PROTOCOL_VERSION,
            "review_status": REVIEW_STATUS,
            "protocol_sha256": _sha256_file(output_dir / "protocol.yaml"),
            "fixed_assignment_sha256": assignment_sha256,
            "sample_manifest_sha256": budget_audit["sample_manifest_sha256"],
            "sample_count": int(len(samples)),
            "packet_count": int(budget_audit["selected_packet_count"]),
            "cell_count": int(len(base_groups)),
            "suite_count": len(SUITE_IDS),
            "manifest_count": len(SPLIT_FILENAMES),
            "row_group_count": int(sum(row["row_group_count"] for row in packet_audits)),
            "output_dir": str(output_dir),
        }
    except TQHC2ABCFixedError:
        raise
    except TQHC2ABCCandidateError as error:
        raise TQHC2ABCFixedError(str(error)) from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按固定清单物化 TQH-C2 A/B/C 预算候选协议")
    parser.add_argument("--profile-a-dir", type=Path, required=True)
    parser.add_argument("--profile-b-dir", type=Path, required=True)
    parser.add_argument("--profile-c-dir", type=Path, required=True)
    parser.add_argument("--approved-inputs", type=Path, required=True)
    parser.add_argument("--assignment", type=Path, required=True)
    parser.add_argument("--cap-per-cell", type=int, default=1000)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        approved_document = json.loads(args.approved_inputs.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TQHC2ABCFixedError("无法读取批准输入配置") from error
    raw_approved_inputs = approved_document.get("profiles")
    if not isinstance(raw_approved_inputs, Mapping):
        raise TQHC2ABCFixedError("批准输入配置必须包含 profiles 对象")
    result = materialize_candidate_abc_budget(
        profile_dirs={
            "A": args.profile_a_dir,
            "B": args.profile_b_dir,
            "C": args.profile_c_dir,
        },
        approved_inputs=raw_approved_inputs,
        assignment_path=args.assignment,
        cap_per_cell=args.cap_per_cell,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
