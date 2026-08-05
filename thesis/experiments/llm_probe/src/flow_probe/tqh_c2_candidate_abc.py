"""将 TQH-C2 A/B/C 暂定制品物化为统一理论筛选候选协议。"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from fractions import Fraction
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from flow_probe.tqh_c2_candidate import (
    LABEL_CONTRACT,
    MODEL_FEATURE_FIELDS,
    REQUIRED_MASTER_COLUMNS,
    REQUIRED_PACKET_COLUMNS,
    SAMPLE_METADATA_FIELDS,
    SENSITIVE_FIELD_TOKENS,
    TREE_VIEW_NAME,
    TQHC2CandidateError,
    _aggregate_features,
    _field_roles,
    _json_scalar,
    _require_columns,
    _sha256_file,
    _stable_hash,
    _write_json,
    _write_jsonl,
    _write_yaml,
)

PROTOCOL_VERSION = "data-protocol-v1.0-rc1"
PROTOCOL_STATUS = "provisional"
PROTOCOL_PHASE = "theory_selection"
REVIEW_STATUS = "review_pending"
DATASET_VERSION = "1.0.1"
CANDIDATE_ID = "dataset-candidate-tqhc2-abc-v0"
EXPECTED_PROFILES = ("A", "B", "C")
EXPECTED_INTERVALS = (30, 300, 1800, 3600)
EXPECTED_JITTERS = (0, 30, 70)
APPROVED_INPUT_IDS = {
    "A": "tqh-c2-A-20260728-v1",
    "B": "tqh-c2-B-20260728-v1",
    "C": "tqh-c2-C-20260724-v8",
}
SPLIT_IDS = ("train", "validation", "test")
SUITE_IDS = (
    "tqhc2_cell_indomain",
    "tqhc2_leave_one_profile_out_A",
    "tqhc2_leave_one_profile_out_B",
    "tqhc2_leave_one_profile_out_C",
)
EXPECTED_CELL_COUNTS = {
    "tqhc2_cell_indomain": {"train": 28, "validation": 4, "test": 4},
    "tqhc2_leave_one_profile_out_A": {"train": 20, "validation": 4, "test": 12},
    "tqhc2_leave_one_profile_out_B": {"train": 20, "validation": 4, "test": 12},
    "tqhc2_leave_one_profile_out_C": {"train": 20, "validation": 4, "test": 12},
}
SPLIT_FILENAMES = {
    (suite_id, split_id): f"splits/{suite_id}-{split_id}.jsonl"
    for suite_id in SUITE_IDS
    for split_id in SPLIT_IDS
}
_SHA256_LENGTH = 64
_REQUIRED_UPSTREAM_ARTIFACTS = frozenset(
    {
        "master_records.parquet",
        "views/packet_observations.parquet",
        "source_checksums.json",
        "run_manifest.provisional.json",
        "schema.provisional.json",
        "audit/cell-audit.json",
        "audit/label-coverage.json",
        "audit/leakage-audit.json",
    }
)


class TQHC2ABCCandidateError(TQHC2CandidateError):
    """A/B/C 候选输入、划分或输出不满足合同。"""


def _read_json_object(path: Path, description: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise TQHC2ABCCandidateError(f"无法读取{description}：{path}") from error
    if not isinstance(value, dict):
        raise TQHC2ABCCandidateError(f"{description}必须是对象：{path}")
    return value


def _strict_nonnegative_int(value: object, description: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TQHC2ABCCandidateError(f"{description}必须是非负整数")
    return value


def _validate_sha256(value: object, description: str) -> str:
    digest = str(value)
    if len(digest) != _SHA256_LENGTH or digest.lower() != digest:
        raise TQHC2ABCCandidateError(f"{description}必须是小写 SHA-256")
    try:
        int(digest, 16)
    except ValueError as error:
        raise TQHC2ABCCandidateError(f"{description}必须是小写 SHA-256") from error
    return digest


def _validate_upstream_artifacts(
    input_dir: Path,
    expected_profile: str,
    approval: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    required_approval_fields = {
        "input_id",
        "artifact_checksums_sha256",
        "extractor_contract_sha256",
        "master_record_count",
        "packet_record_count",
    }
    if set(approval) != required_approval_fields:
        raise TQHC2ABCCandidateError(
            f"批准输入配置字段不完整：{expected_profile}:{sorted(approval)}"
        )
    if approval["input_id"] != APPROVED_INPUT_IDS[expected_profile]:
        raise TQHC2ABCCandidateError(f"批准输入标识不符合冻结设计：{expected_profile}")
    approved_artifact_sha256 = _validate_sha256(
        approval["artifact_checksums_sha256"], f"{expected_profile} 批准制品清单哈希"
    )
    approved_extractor_sha256 = _validate_sha256(
        approval["extractor_contract_sha256"], f"{expected_profile} 批准提取器哈希"
    )
    approved_master_count = _strict_nonnegative_int(
        approval["master_record_count"], f"{expected_profile} 批准主记录数"
    )
    approved_packet_count = _strict_nonnegative_int(
        approval["packet_record_count"], f"{expected_profile} 批准包记录数"
    )

    checksum_path = input_dir / "artifact_checksums.provisional.json"
    if not checksum_path.is_file():
        raise TQHC2ABCCandidateError(f"缺少上游制品校验清单：{checksum_path}")
    actual_manifest_sha256 = _sha256_file(checksum_path)
    if actual_manifest_sha256 != approved_artifact_sha256:
        raise TQHC2ABCCandidateError(f"上游制品清单未绑定批准哈希：{expected_profile}")
    checksum_document = _read_json_object(checksum_path, "上游制品校验清单")
    if checksum_document.get("status") != "provisional":
        raise TQHC2ABCCandidateError(f"上游制品校验清单状态错误：{expected_profile}")
    raw_files = checksum_document.get("files")
    if not isinstance(raw_files, list):
        raise TQHC2ABCCandidateError(f"上游制品校验清单 files 必须是列表：{expected_profile}")
    registered: dict[str, dict[str, object]] = {}
    for index, raw_row in enumerate(raw_files):
        if not isinstance(raw_row, Mapping):
            raise TQHC2ABCCandidateError(
                f"上游制品校验清单行必须是对象：{expected_profile}:{index}"
            )
        relative_path = str(raw_row.get("path", ""))
        relative = Path(relative_path)
        if (
            not relative_path
            or relative.is_absolute()
            or ".." in relative.parts
            or relative_path in registered
        ):
            raise TQHC2ABCCandidateError(
                f"上游制品路径非法或重复：{expected_profile}:{relative_path}"
            )
        digest = _validate_sha256(
            raw_row.get("sha256"), f"{expected_profile}:{relative_path} 登记哈希"
        )
        size_bytes = _strict_nonnegative_int(
            raw_row.get("size_bytes"), f"{expected_profile}:{relative_path} 登记大小"
        )
        path = input_dir / relative
        if not path.is_file():
            raise TQHC2ABCCandidateError(f"上游登记制品不存在：{expected_profile}:{relative_path}")
        if path.stat().st_size != size_bytes or _sha256_file(path) != digest:
            raise TQHC2ABCCandidateError(
                f"上游登记制品大小或 SHA-256 不一致：{expected_profile}:{relative_path}"
            )
        registered[relative_path] = {"sha256": digest, "size_bytes": size_bytes}
    if set(registered) != _REQUIRED_UPSTREAM_ARTIFACTS:
        missing = sorted(_REQUIRED_UPSTREAM_ARTIFACTS.difference(registered))
        extra = sorted(set(registered).difference(_REQUIRED_UPSTREAM_ARTIFACTS))
        raise TQHC2ABCCandidateError(
            f"上游制品集合不符合固定合同：{expected_profile}:缺失={missing}:多余={extra}"
        )

    run_manifest = _read_json_object(input_dir / "run_manifest.provisional.json", "暂定运行清单")
    expected = {
        "dataset_id": "TQH-C2",
        "dataset_version": DATASET_VERSION,
        "profile": expected_profile,
        "cell_count": 12,
        "status": "provisional",
    }
    mismatches = {
        key: (run_manifest.get(key), expected_value)
        for key, expected_value in expected.items()
        if run_manifest.get(key) != expected_value
    }
    if mismatches:
        raise TQHC2ABCCandidateError(
            f"暂定运行清单与 A/B/C 合同不一致：{expected_profile}:{mismatches}"
        )
    if run_manifest.get("extractor_contract_sha256") != approved_extractor_sha256:
        raise TQHC2ABCCandidateError(f"运行清单提取器未绑定批准配置：{expected_profile}")
    if run_manifest.get("master_record_count") != approved_master_count:
        raise TQHC2ABCCandidateError(f"运行清单主记录数未绑定批准配置：{expected_profile}")
    if run_manifest.get("packet_record_count") != approved_packet_count:
        raise TQHC2ABCCandidateError(f"运行清单包记录数未绑定批准配置：{expected_profile}")

    cell_audit = _read_json_object(input_dir / "audit" / "cell-audit.json", "cell 审计")
    if cell_audit.get("profile") != expected_profile or not isinstance(
        cell_audit.get("cells"), list
    ):
        raise TQHC2ABCCandidateError(f"上游 cell 审计结构错误：{expected_profile}")
    if len(cell_audit["cells"]) != 12:
        raise TQHC2ABCCandidateError(f"上游 cell 审计必须包含 12 个 cell：{expected_profile}")
    label_coverage = _read_json_object(input_dir / "audit" / "label-coverage.json", "标签覆盖审计")
    leakage_audit = _read_json_object(input_dir / "audit" / "leakage-audit.json", "字段泄漏审计")
    source_checksums = _read_json_object(input_dir / "source_checksums.json", "来源校验清单")
    schema = _read_json_object(input_dir / "schema.provisional.json", "暂定字段模式")
    if not isinstance(source_checksums.get("files"), list):
        raise TQHC2ABCCandidateError(f"来源校验清单 files 必须是列表：{expected_profile}")
    if leakage_audit.get("status") != "pass" or schema.get("status") != "provisional":
        raise TQHC2ABCCandidateError(f"上游字段或泄漏审计未通过：{expected_profile}")
    return run_manifest, {
        "input_id": APPROVED_INPUT_IDS[expected_profile],
        "artifact_checksums_sha256": actual_manifest_sha256,
        "registered_artifacts": registered,
        "label_coverage": label_coverage,
    }


def _validate_label_contract(master: pd.DataFrame) -> None:
    for sample_id, native_label, binary_label, label_status in master.loc[
        :, ["sample_id", "native_label", "binary_label", "label_status"]
    ].itertuples(index=False, name=None):
        native_label = str(native_label)
        if native_label not in LABEL_CONTRACT:
            raise TQHC2ABCCandidateError(f"标签映射包含未知原生标签：{sample_id}:{native_label}")
        expected_binary, expected_status = LABEL_CONTRACT[native_label]
        actual_binary = None if pd.isna(binary_label) else str(binary_label)
        actual_status = str(label_status)
        if (actual_binary, actual_status) != (expected_binary, expected_status):
            raise TQHC2ABCCandidateError(
                "标签映射不符合固定契约："
                f"{sample_id}:{native_label}:"
                f"{actual_binary}/{actual_status} != {expected_binary}/{expected_status}"
            )


def _load_masters(
    profile_dirs: Mapping[str, Path],
    approved_inputs: Mapping[str, Mapping[str, object]],
) -> tuple[pd.DataFrame, dict[str, Path], list[dict[str, object]]]:
    if set(profile_dirs) != set(EXPECTED_PROFILES):
        raise TQHC2ABCCandidateError(f"必须显式提供 A/B/C 三个 profile：{sorted(profile_dirs)}")
    if set(approved_inputs) != set(EXPECTED_PROFILES):
        raise TQHC2ABCCandidateError(
            f"必须显式提供 A/B/C 三份批准输入配置：{sorted(approved_inputs)}"
        )
    frames: list[pd.DataFrame] = []
    resolved_dirs: dict[str, Path] = {}
    input_audits: list[dict[str, object]] = []
    for profile in EXPECTED_PROFILES:
        input_dir = Path(profile_dirs[profile]).expanduser().resolve()
        resolved_dirs[profile] = input_dir
        run_manifest, upstream_audit = _validate_upstream_artifacts(
            input_dir, profile, approved_inputs[profile]
        )
        master_path = input_dir / "master_records.parquet"
        packet_path = input_dir / "views" / "packet_observations.parquet"
        if not master_path.is_file() or not packet_path.is_file():
            raise TQHC2ABCCandidateError(f"缺少 {profile} 暂定主记录或包观测：{input_dir}")
        try:
            master = pd.read_parquet(master_path)
        except Exception as error:
            raise TQHC2ABCCandidateError(f"无法读取 {profile} 暂定主记录：{master_path}") from error
        _require_columns(master, REQUIRED_MASTER_COLUMNS, f"{profile} 主记录")
        if master.empty:
            raise TQHC2ABCCandidateError(f"{profile} 主记录不得为空")
        if set(master["dataset_id"].astype(str)) != {"TQH-C2"}:
            raise TQHC2ABCCandidateError(f"{profile} 主记录数据集标识错误")
        if set(master["dataset_version"].astype(str)) != {DATASET_VERSION}:
            raise TQHC2ABCCandidateError(f"{profile} 主记录版本必须为 {DATASET_VERSION}")
        if set(master["profile"].astype(str)) != {profile}:
            raise TQHC2ABCCandidateError(f"{profile} 输入目录混入其他 profile")
        if master["sample_id"].isna().any() or master["sample_id"].duplicated().any():
            raise TQHC2ABCCandidateError(f"{profile} 主记录 sample_id 必须非空且唯一")
        if len(master) != run_manifest["master_record_count"]:
            raise TQHC2ABCCandidateError(f"主记录实际行数与运行清单不一致：{profile}")
        try:
            import pyarrow.parquet as pq
        except ImportError as error:
            raise TQHC2ABCCandidateError("核验 Parquet 元数据需要项目依赖 pyarrow") from error
        packet_record_count = pq.ParquetFile(packet_path).metadata.num_rows
        if packet_record_count != run_manifest["packet_record_count"]:
            raise TQHC2ABCCandidateError(f"包记录实际行数与运行清单不一致：{profile}")
        extractor_hashes = set(master["extractor_contract_sha256"].astype(str))
        if extractor_hashes != {run_manifest["extractor_contract_sha256"]}:
            raise TQHC2ABCCandidateError(f"主记录提取器哈希与运行清单不一致：{profile}")
        if upstream_audit["label_coverage"].get("record_count") != len(master):
            raise TQHC2ABCCandidateError(f"标签覆盖审计记录数不一致：{profile}")
        _validate_label_contract(master)
        frames.append(master)
        input_audits.append(
            {
                "profile": profile,
                "input_id": upstream_audit["input_id"],
                "artifact_checksums_sha256": upstream_audit["artifact_checksums_sha256"],
                "extractor_contract_sha256": run_manifest["extractor_contract_sha256"],
                "master_record_count": len(master),
                "packet_record_count": packet_record_count,
            }
        )

    master = pd.concat(frames, ignore_index=True)
    if master["sample_id"].duplicated().any():
        duplicate = str(master.loc[master["sample_id"].duplicated(), "sample_id"].iloc[0])
        raise TQHC2ABCCandidateError(f"A/B/C 主记录 sample_id 冲突：{duplicate}")
    versions = set(master["dataset_version"].astype(str))
    if versions != {DATASET_VERSION}:
        raise TQHC2ABCCandidateError(f"A/B/C 数据版本不一致：{sorted(versions)}")
    return master.sort_values("sample_id", kind="mergesort"), resolved_dirs, input_audits


def _build_base_groups(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for capture_group_id, frame in master.groupby("capture_group_id", sort=True, observed=True):
        unique_fields = (
            "allocation_group_id",
            "profile",
            "interval_s",
            "jitter_pct",
            "source_capture_sha256",
        )
        for field_name in unique_fields:
            if frame[field_name].nunique(dropna=False) != 1:
                raise TQHC2ABCCandidateError(
                    f"完整 cell 的 {field_name} 不唯一：{capture_group_id}"
                )
        mapped = frame[frame["label_status"].eq("mapped")]
        label_counts = Counter(mapped["binary_label"].astype(str))
        if set(label_counts) != {"benign", "malicious"}:
            raise TQHC2ABCCandidateError(f"完整 cell 缺少二分类标签覆盖：{capture_group_id}")
        status_counts = Counter(frame["label_status"].astype(str))
        rows.append(
            {
                "allocation_group_id": str(frame["allocation_group_id"].iloc[0]),
                "capture_group_id": str(capture_group_id),
                "profile": str(frame["profile"].iloc[0]),
                "interval_s": int(frame["interval_s"].iloc[0]),
                "jitter_pct": int(frame["jitter_pct"].iloc[0]),
                "source_capture_sha256": str(frame["source_capture_sha256"].iloc[0]),
                "record_count": int(len(frame)),
                "mapped_count": int(status_counts["mapped"]),
                "auxiliary_count": int(status_counts["auxiliary"]),
                "unresolved_count": int(status_counts["unresolved"]),
                "benign_count": int(label_counts["benign"]),
                "malicious_count": int(label_counts["malicious"]),
            }
        )
    groups = pd.DataFrame(rows).sort_values(["profile", "capture_group_id"], kind="mergesort")
    profile_counts = Counter(groups["profile"].astype(str))
    if profile_counts != Counter({"A": 12, "B": 12, "C": 12}):
        raise TQHC2ABCCandidateError(f"每个 profile 必须恰有 12 个 cell：{dict(profile_counts)}")
    expected_grid = set(product(EXPECTED_INTERVALS, EXPECTED_JITTERS))
    for profile, frame in groups.groupby("profile", sort=True, observed=True):
        actual_grid = set(
            zip(frame["interval_s"].astype(int), frame["jitter_pct"].astype(int), strict=True)
        )
        if actual_grid != expected_grid:
            missing = sorted(expected_grid.difference(actual_grid))
            extra = sorted(actual_grid.difference(expected_grid))
            raise TQHC2ABCCandidateError(
                f"profile 不满足固定 4×3 cell 网格：{profile}:缺失={missing}:多余={extra}"
            )
    if groups["allocation_group_id"].duplicated().any():
        raise TQHC2ABCCandidateError("A/B/C allocation_group_id 必须全局唯一")
    return groups.reset_index(drop=True)


def _coverage_candidates(
    groups: pd.DataFrame, required_profiles: frozenset[str]
) -> list[dict[str, object]]:
    choices = [
        groups[groups["interval_s"].eq(interval_s)].to_dict(orient="records")
        for interval_s in EXPECTED_INTERVALS
    ]
    candidates: list[dict[str, object]] = []
    for selected in product(*choices):
        profiles = {str(row["profile"]) for row in selected}
        if profiles != required_profiles:
            continue
        group_ids = tuple(sorted(str(row["capture_group_id"]) for row in selected))
        candidates.append(
            {
                "group_ids": group_ids,
                "group_id_set": frozenset(group_ids),
                "mapped_count": sum(int(row["mapped_count"]) for row in selected),
                "jitter_count": len({int(row["jitter_pct"]) for row in selected}),
            }
        )
    if not candidates:
        raise TQHC2ABCCandidateError(
            f"无法构造满足 profile/interval 硬覆盖的 4-cell 组合：{sorted(required_profiles)}"
        )
    return candidates


def _fraction_audit(
    counts: Mapping[str, int], targets: Mapping[str, Fraction]
) -> tuple[Fraction, dict[str, float]]:
    total = sum(counts.values())
    fractions = {split_id: Fraction(count, total) for split_id, count in counts.items()}
    deviation = sum(abs(fractions[split_id] - targets[split_id]) for split_id in SPLIT_IDS)
    return deviation, {split_id: float(fractions[split_id]) for split_id in SPLIT_IDS}


def _select_indomain_groups(
    base_groups: pd.DataFrame, suite_id: str
) -> tuple[dict[str, str], dict[str, object]]:
    candidates = _coverage_candidates(base_groups, frozenset(EXPECTED_PROFILES))
    total = int(base_groups["mapped_count"].sum())
    targets = {
        "train": Fraction(8, 10),
        "validation": Fraction(1, 10),
        "test": Fraction(1, 10),
    }
    best_key: tuple[Fraction, int, int, str] | None = None
    best: tuple[dict[str, object], dict[str, object], dict[str, int], dict[str, float]] | None = (
        None
    )
    for validation in candidates:
        for test in candidates:
            if validation["group_id_set"] & test["group_id_set"]:
                continue
            counts = {
                "validation": int(validation["mapped_count"]),
                "test": int(test["mapped_count"]),
            }
            counts["train"] = total - counts["validation"] - counts["test"]
            deviation, fractions = _fraction_audit(counts, targets)
            min_jitter = min(int(validation["jitter_count"]), int(test["jitter_count"]))
            total_jitter = int(validation["jitter_count"]) + int(test["jitter_count"])
            primary = (deviation, -min_jitter, -total_jitter)
            if best_key is not None and primary > best_key[:3]:
                continue
            tie = hashlib.sha256(
                (
                    f"{CANDIDATE_ID}|{suite_id}|"
                    f"{'|'.join(validation['group_ids'])}|{'|'.join(test['group_ids'])}"
                ).encode("ascii")
            ).hexdigest()
            key = (*primary, tie)
            if best_key is None or key < best_key:
                best_key = key
                best = (validation, test, counts, fractions)
    if best is None or best_key is None:
        raise TQHC2ABCCandidateError("无法构造互斥的域内验证与测试硬覆盖组合")
    validation, test, counts, fractions = best
    validation_ids = validation["group_id_set"]
    test_ids = test["group_id_set"]
    split_by_group = {
        str(group_id): (
            "validation"
            if str(group_id) in validation_ids
            else "test" if str(group_id) in test_ids else "train"
        )
        for group_id in base_groups["capture_group_id"]
    }
    return split_by_group, {
        "selection_method": "硬覆盖组合穷举后最小化样本比例偏差，再扩大 jitter 覆盖",
        "candidate_count": len(candidates),
        "sample_counts": counts,
        "sample_fractions": fractions,
        "target_sample_fractions": {key: float(value) for key, value in targets.items()},
        "l1_sample_fraction_deviation": float(best_key[0]),
        "validation_jitter_count": int(validation["jitter_count"]),
        "test_jitter_count": int(test["jitter_count"]),
        "deterministic_tie_break": best_key[3],
    }


def _select_leave_one_groups(
    base_groups: pd.DataFrame, suite_id: str, held_out: str
) -> tuple[dict[str, str], dict[str, object]]:
    source_profiles = frozenset(set(EXPECTED_PROFILES).difference({held_out}))
    source_groups = base_groups[base_groups["profile"].isin(source_profiles)]
    candidates = _coverage_candidates(source_groups, source_profiles)
    total = int(base_groups["mapped_count"].sum())
    test_count = int(base_groups.loc[base_groups["profile"].eq(held_out), "mapped_count"].sum())
    targets = {
        "train": Fraction(20, 36),
        "validation": Fraction(4, 36),
        "test": Fraction(12, 36),
    }
    ranked: list[
        tuple[tuple[Fraction, int, str], dict[str, object], dict[str, int], dict[str, float]]
    ] = []
    for validation in candidates:
        counts = {
            "validation": int(validation["mapped_count"]),
            "test": test_count,
        }
        counts["train"] = total - counts["validation"] - counts["test"]
        deviation, fractions = _fraction_audit(counts, targets)
        tie = hashlib.sha256(
            f"{CANDIDATE_ID}|{suite_id}|{'|'.join(validation['group_ids'])}".encode("ascii")
        ).hexdigest()
        ranked.append(
            ((deviation, -int(validation["jitter_count"]), tie), validation, counts, fractions)
        )
    key, validation, counts, fractions = min(ranked, key=lambda row: row[0])
    validation_ids = validation["group_id_set"]
    split_by_group = {
        str(row.capture_group_id): (
            "test"
            if str(row.profile) == held_out
            else "validation" if str(row.capture_group_id) in validation_ids else "train"
        )
        for row in base_groups.itertuples(index=False)
    }
    return split_by_group, {
        "selection_method": (
            "留一 profile 固定测试；源域硬覆盖组合中最小化样本比例偏差，" "再扩大 jitter 覆盖"
        ),
        "held_out_profile": held_out,
        "candidate_count": len(candidates),
        "sample_counts": counts,
        "sample_fractions": fractions,
        "target_sample_fractions": {name: float(value) for name, value in targets.items()},
        "l1_sample_fraction_deviation": float(key[0]),
        "validation_jitter_count": int(validation["jitter_count"]),
        "deterministic_tie_break": key[2],
    }


def _build_suite_groups(
    base_groups: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, dict[str, object]]]:
    assignments: list[dict[str, object]] = []
    selection_audits: dict[str, dict[str, object]] = {}
    for suite_id in SUITE_IDS:
        if suite_id == "tqhc2_cell_indomain":
            held_out = ""
            split_by_group, selection_audits[suite_id] = _select_indomain_groups(
                base_groups, suite_id
            )
        else:
            held_out = suite_id.rsplit("_", 1)[-1]
            split_by_group, selection_audits[suite_id] = _select_leave_one_groups(
                base_groups, suite_id, held_out
            )
        for row in base_groups.to_dict(orient="records"):
            split_id = split_by_group[str(row["capture_group_id"])]
            assignments.append(
                {
                    **row,
                    "suite_id": suite_id,
                    "split_id": split_id,
                    "domain_role": (
                        "held_out_profile"
                        if held_out and str(row["profile"]) == held_out
                        else "source_profile" if held_out else "in_domain"
                    ),
                }
            )
    suite_groups = pd.DataFrame(assignments)
    for suite_id, frame in suite_groups.groupby("suite_id", sort=True, observed=True):
        counts = Counter(frame["split_id"].astype(str))
        if counts != Counter(EXPECTED_CELL_COUNTS[str(suite_id)]):
            raise TQHC2ABCCandidateError(f"套件 cell 数量不符合合同：{suite_id}:{dict(counts)}")
        if frame["capture_group_id"].duplicated().any() or len(frame) != 36:
            raise TQHC2ABCCandidateError(f"套件未恰好覆盖 36 个互异 cell：{suite_id}")
    return (
        suite_groups.sort_values(
            ["suite_id", "split_id", "profile", "capture_group_id"], kind="mergesort"
        ).reset_index(drop=True),
        selection_audits,
    )


def _validate_packet_frame(frame: pd.DataFrame, location: str) -> None:
    _require_columns(frame, REQUIRED_PACKET_COLUMNS, f"{location} 包观测")
    if frame.empty:
        raise TQHC2ABCCandidateError(f"包观测行组不得为空：{location}")
    numeric_fields = (
        "packet_index",
        "relative_time_ns",
        "delta_time_us",
        "direction",
        "network_length_bytes",
        "burst_id",
    )
    numeric = frame.loc[:, list(numeric_fields)].to_numpy(dtype=np.float64)
    if not np.isfinite(numeric).all():
        raise TQHC2ABCCandidateError(f"包观测数值字段含空值或非有限值：{location}")
    if not set(frame["direction"].astype(int)).issubset({-1, 1}):
        raise TQHC2ABCCandidateError(f"包方向只能为 -1 或 1：{location}")
    if (frame["packet_index"] < 0).any() or (frame["delta_time_us"] < 0).any():
        raise TQHC2ABCCandidateError(f"包序号和相邻间隔不得为负：{location}")
    if (frame["payload_length_bytes"].isna() & frame["payload_length_observed"]).any():
        raise TQHC2ABCCandidateError(f"载荷掩码声明可用时观测不得为空：{location}")
    if (frame["tcp_flags"].isna() & frame["tcp_flags_applicable"]).any():
        raise TQHC2ABCCandidateError(f"TCP 标志掩码声明可用时观测不得为空：{location}")
    if frame["payload_length_bytes"].dropna().lt(0).any():
        raise TQHC2ABCCandidateError(f"载荷长度不得为负：{location}")
    mask_fields = ("payload_length_observed", "tcp_flags_applicable", "truncation_mask")
    if frame.loc[:, list(mask_fields)].isna().any().any():
        raise TQHC2ABCCandidateError(f"包观测适用掩码不得为空：{location}")
    transport = frame["transport_family"].astype(str).str.upper()
    if not set(transport).issubset({"TCP", "UDP", "ICMP"}):
        raise TQHC2ABCCandidateError(f"包观测包含未知传输族：{location}")
    flags_applicable = frame["tcp_flags_applicable"].astype(bool)
    if not flags_applicable.eq(transport.eq("TCP")).all():
        raise TQHC2ABCCandidateError(f"TCP 标志适用掩码与传输族不一致：{location}")
    flags = frame["tcp_flags"]
    if flags.dropna().lt(0).any() or flags.dropna().gt(0x1FF).any():
        raise TQHC2ABCCandidateError(f"TCP 标志超出 9 位字段范围：{location}")
    if ((~flags_applicable) & flags.fillna(0).ne(0)).any():
        raise TQHC2ABCCandidateError(f"TCP 标志掩码为假时不得携带非零值：{location}")


def _sequence_hash(frame: pd.DataFrame) -> str:
    fields = (
        "relative_time_ns",
        "delta_time_us",
        "direction",
        "network_length_bytes",
        "payload_length_bytes",
        "transport_family",
        "tcp_flags",
        "burst_id",
        "is_first_packet",
        "payload_length_observed",
        "tcp_flags_applicable",
        "truncation_mask",
    )
    digest = hashlib.sha256()
    for row in frame.loc[:, list(fields)].itertuples(index=False, name=None):
        values = [_json_scalar(value) for value in row]
        digest.update(
            json.dumps(
                values,
                allow_nan=False,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("ascii")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _stream_packet_features(
    master: pd.DataFrame,
    profile_dirs: Mapping[str, Path],
) -> tuple[pd.DataFrame, dict[str, str], list[dict[str, object]]]:
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise TQHC2ABCCandidateError("流式读取 Parquet 需要项目依赖 pyarrow") from error

    master_by_id = master.set_index("sample_id", drop=False)
    cell_by_sample = master_by_id["capture_group_id"].astype(str).to_dict()
    mapped_ids = set(master.loc[master["label_status"].eq("mapped"), "sample_id"].astype(str))
    expected_counts = master_by_id["packet_count_kept"].astype("int64").to_dict()
    feature_rows: list[pd.DataFrame] = []
    sequence_hashes: dict[str, str] = {}
    row_group_audit: list[dict[str, object]] = []
    closed_samples: set[str] = set()
    pending_id: str | None = None
    pending_frames: list[pd.DataFrame] = []

    def flush_pending() -> None:
        nonlocal pending_id, pending_frames
        if pending_id is None:
            return
        frame = pd.concat(pending_frames, ignore_index=True)
        indexes = frame["packet_index"].to_numpy(dtype=np.int64)
        expected = int(expected_counts[pending_id])
        if len(frame) != expected or not np.array_equal(indexes, np.arange(expected)):
            raise TQHC2ABCCandidateError(f"包观测计数或序号未绑定主记录：{pending_id}")
        if pending_id in mapped_ids:
            try:
                features = _aggregate_features(frame)
            except TQHC2CandidateError as error:
                raise TQHC2ABCCandidateError(str(error)) from error
            feature_rows.append(features)
            sequence_hashes[pending_id] = _sequence_hash(frame)
        closed_samples.add(pending_id)
        pending_id = None
        pending_frames = []

    for profile in EXPECTED_PROFILES:
        packet_path = profile_dirs[profile] / "views" / "packet_observations.parquet"
        parquet = pq.ParquetFile(packet_path)
        current_cell: str | None = None
        closed_cells: set[str] = set()
        missing = sorted(REQUIRED_PACKET_COLUMNS.difference(parquet.schema_arrow.names))
        if missing:
            raise TQHC2ABCCandidateError(f"{profile} 包观测缺少字段：{','.join(missing)}")
        for row_group_index in range(parquet.num_row_groups):
            location = f"{profile}:row_group={row_group_index}"
            frame = parquet.read_row_group(
                row_group_index, columns=sorted(REQUIRED_PACKET_COLUMNS)
            ).to_pandas()
            _validate_packet_frame(frame, location)
            sample_ids = frame["sample_id"].astype(str)
            unknown_ids = sorted(set(sample_ids).difference(cell_by_sample))
            if unknown_ids:
                raise TQHC2ABCCandidateError(
                    f"包观测包含主记录外 sample_id：{location}:{unknown_ids[0]}"
                )
            cells = {cell_by_sample[sample_id] for sample_id in sample_ids}
            if len(cells) != 1:
                raise TQHC2ABCCandidateError(
                    f"Parquet 行组混入多个 cell：{location}:{sorted(cells)}"
                )
            cell_id = next(iter(cells))
            cell_profile = str(master_by_id.loc[sample_ids.iloc[0], "profile"])
            if cell_profile != profile:
                raise TQHC2ABCCandidateError(f"Parquet 行组 profile 绑定错误：{location}")
            if cell_id != current_cell:
                if current_cell is not None:
                    closed_cells.add(current_cell)
                if cell_id in closed_cells:
                    raise TQHC2ABCCandidateError(
                        f"cell_order_fallback：已关闭 cell 再次出现：{location}:{cell_id}"
                    )
                current_cell = cell_id
            row_group_audit.append(
                {
                    "profile": profile,
                    "row_group_index": row_group_index,
                    "capture_group_id": cell_id,
                    "row_count": int(len(frame)),
                    "first_sample_id": str(sample_ids.iloc[0]),
                    "last_sample_id": str(sample_ids.iloc[-1]),
                }
            )

            run_ids = sample_ids.ne(sample_ids.shift()).cumsum()
            segments = [segment for _, segment in frame.groupby(run_ids, sort=False)]
            segment_ids = [str(segment["sample_id"].iloc[0]) for segment in segments]
            if len(segment_ids) != len(set(segment_ids)):
                raise TQHC2ABCCandidateError(f"单个行组内 sample_id 非连续：{location}")
            for segment_id, segment in zip(segment_ids, segments, strict=True):
                if segment_id == pending_id:
                    pending_frames.append(segment)
                    continue
                flush_pending()
                if segment_id in closed_samples:
                    raise TQHC2ABCCandidateError(f"sample_id 在包表中非连续重现：{segment_id}")
                pending_id = segment_id
                pending_frames = [segment]
        flush_pending()

    if closed_samples != set(master_by_id.index.astype(str)):
        missing = sorted(set(master_by_id.index.astype(str)).difference(closed_samples))
        extra = sorted(closed_samples.difference(master_by_id.index.astype(str)))
        raise TQHC2ABCCandidateError(
            f"包观测与主记录样本集合不一致：缺失 {len(missing)}，独有 {len(extra)}"
        )
    if set(sequence_hashes) != mapped_ids:
        raise TQHC2ABCCandidateError("序列哈希未覆盖全部映射样本")
    features = pd.concat(feature_rows).sort_index(kind="mergesort")
    if set(features.index.astype(str)) != mapped_ids:
        raise TQHC2ABCCandidateError("聚合字段未覆盖全部映射样本")
    return features, sequence_hashes, row_group_audit


def _build_samples(
    master: pd.DataFrame,
    features: pd.DataFrame,
    sequence_hashes: Mapping[str, str],
) -> pd.DataFrame:
    mapped = master[master["label_status"].eq("mapped")].copy()
    mapped = mapped.rename(columns={"record_sha256": "source_record_sha256"})
    mapped["protocol_version"] = PROTOCOL_VERSION
    mapped["protocol_status"] = PROTOCOL_STATUS
    mapped["protocol_phase"] = PROTOCOL_PHASE
    mapped["candidate_id"] = CANDIDATE_ID
    mapped["suite_id"] = "multiple_tqhc2_suites"
    mapped["split_id"] = "defined_by_manifest"
    mapped["domain_role"] = "suite_specific"
    mapped["scenario_group_id"] = "tqhc2_profile_" + mapped["profile"].astype(str).str.lower()
    mapped["topology_group_id"] = mapped["scenario_group_id"] + "_source_topology"
    mapped["time_block_id"] = mapped["capture_group_id"].astype(str)
    mapped["label_schema_version"] = "tqhc2-label-v1"
    mapped["observation_sequence_sha256"] = mapped["sample_id"].map(sequence_hashes)
    mapped["family_label"] = mapped["family_label"].fillna("").astype(str)
    mapped["subtype_label"] = mapped["subtype_label"].fillna("").astype(str)
    mapped["unknown_role"] = mapped["unknown_role"].fillna("").astype(str)
    samples = mapped.merge(
        features.reset_index(), on="sample_id", how="left", validate="one_to_one"
    )
    samples["candidate_record_sha256"] = ""
    samples = samples.loc[:, [*SAMPLE_METADATA_FIELDS, *MODEL_FEATURE_FIELDS]]

    integer_fields = {
        "window_start_ns",
        "window_end_ns",
        "window_ordinal",
        "packet_count_raw",
        "packet_count_kept",
        "interval_s",
        "jitter_pct",
        "packet_count",
        "direction_change_count",
        "burst_count",
    }
    for field_name in SAMPLE_METADATA_FIELDS:
        if field_name in integer_fields:
            samples[field_name] = samples[field_name].astype("int64")
        else:
            samples[field_name] = samples[field_name].fillna("").astype(str)
    for field_name in MODEL_FEATURE_FIELDS:
        if field_name in integer_fields:
            samples[field_name] = samples[field_name].astype("int64")
        else:
            samples[field_name] = samples[field_name].astype("float64")
    samples = samples.sort_values("sample_id", kind="mergesort").reset_index(drop=True)
    record_fields = [field for field in samples.columns if field != "candidate_record_sha256"]
    samples["candidate_record_sha256"] = [
        _stable_hash(row) for row in samples.loc[:, record_fields].to_dict(orient="records")
    ]
    samples = samples.loc[:, [*SAMPLE_METADATA_FIELDS, *MODEL_FEATURE_FIELDS]]
    if samples["sample_id"].duplicated().any():
        raise TQHC2ABCCandidateError("候选主记录 sample_id 不唯一")
    numeric = samples.loc[:, list(MODEL_FEATURE_FIELDS)].to_numpy(dtype=np.float64)
    if not np.isfinite(numeric).all():
        raise TQHC2ABCCandidateError("候选模型字段含非有限值")
    return samples


def _source_artifacts(profile_dirs: Mapping[str, Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    derived_paths = (
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
        input_dir = profile_dirs[profile]
        for relative_path in derived_paths:
            path = input_dir / relative_path
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
    module_path = Path(__file__)
    rows.append(
        {
            "profile": "ABC",
            "lineage_level": "candidate_builder",
            "role": "materializer_source",
            "source_path": "src/flow_probe/tqh_c2_candidate_abc.py",
            "sha256": _sha256_file(module_path),
            "size_bytes": module_path.stat().st_size,
        }
    )
    return sorted(rows, key=lambda row: (str(row["profile"]), str(row["source_path"])))


def _duplicate_screen(samples: pd.DataFrame, split_by_cell: Mapping[str, str]) -> dict[str, object]:
    frame = samples.loc[
        :,
        [
            "sample_id",
            "capture_group_id",
            "binary_label",
            "observation_sequence_sha256",
            *MODEL_FEATURE_FIELDS,
        ],
    ].copy()
    frame["split_id"] = frame["capture_group_id"].map(split_by_cell)
    exact = frame.groupby("observation_sequence_sha256", sort=True).agg(
        split_count=("split_id", "nunique"),
        sample_count=("sample_id", "size"),
        label_count=("binary_label", "nunique"),
    )
    exact_cross = exact[exact["split_count"] > 1]
    coarse_hashes: list[str] = []
    for row in frame.loc[:, list(MODEL_FEATURE_FIELDS)].itertuples(index=False, name=None):
        payload = json.dumps(
            [round(float(value), 3) for value in row], separators=(",", ":")
        ).encode("ascii")
        coarse_hashes.append(hashlib.sha256(payload).hexdigest())
    frame["coarse_signature"] = coarse_hashes
    coarse = frame.groupby("coarse_signature", sort=True).agg(
        split_count=("split_id", "nunique"),
        sample_count=("sample_id", "size"),
        label_count=("binary_label", "nunique"),
    )
    coarse_cross = coarse[coarse["split_count"] > 1]
    return {
        "exact_observation_sequence": {
            "cross_split_hash_count": int(len(exact_cross)),
            "cross_split_sample_count": int(exact_cross["sample_count"].sum()),
            "conflicting_label_hash_count": int(exact_cross["label_count"].gt(1).sum()),
            "example_hashes": list(exact_cross.index[:10]),
            "status": "documented_residual" if len(exact_cross) else "pass",
        },
        "coarse_aggregate_signature": {
            "rounding_decimals": 3,
            "cross_split_hash_count": int(len(coarse_cross)),
            "cross_split_sample_count": int(coarse_cross["sample_count"].sum()),
            "conflicting_label_hash_count": int(coarse_cross["label_count"].gt(1).sum()),
            "example_hashes": list(coarse_cross.index[:10]),
            "status": "screen_only",
        },
        "policy": "完整 cell 不因残余重复而被静默删除或移动。",
    }


def _suite_audits(
    samples: pd.DataFrame,
    suite_groups: pd.DataFrame,
    manifest_hashes: Mapping[str, str],
    selection_audits: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    suite_audits: dict[str, object] = {}
    duplicate_audits: dict[str, object] = {}
    p0_audits: dict[str, object] = {}
    all_sample_ids = set(samples["sample_id"].astype(str))
    for suite_id in SUITE_IDS:
        groups = suite_groups[suite_groups["suite_id"].eq(suite_id)]
        split_by_cell = dict(
            zip(groups["capture_group_id"].astype(str), groups["split_id"].astype(str), strict=True)
        )
        sample_frame = samples.loc[:, ["sample_id", "capture_group_id", "binary_label"]].copy()
        sample_frame["split_id"] = sample_frame["capture_group_id"].map(split_by_cell)
        memberships = sample_frame.groupby("sample_id")["split_id"].nunique()
        split_sample_counts = Counter(sample_frame["split_id"].astype(str))
        split_label_counts = {
            split_id: dict(sorted(Counter(frame["binary_label"].astype(str)).items()))
            for split_id, frame in sample_frame.groupby("split_id", sort=True, observed=True)
        }
        total_samples = len(sample_frame)
        split_conditions = {
            split_id: {
                "cell_count": int(len(frame)),
                "sample_count": int(split_sample_counts[split_id]),
                "sample_fraction": float(split_sample_counts[split_id] / total_samples),
                "profiles": sorted(set(frame["profile"].astype(str))),
                "intervals": sorted(set(frame["interval_s"].astype(int))),
                "jitters": sorted(set(frame["jitter_pct"].astype(int))),
            }
            for split_id, frame in groups.groupby("split_id", sort=True, observed=True)
        }
        expected_counts = EXPECTED_CELL_COUNTS[suite_id]
        cell_counts_valid = Counter(groups["split_id"].astype(str)) == Counter(expected_counts)
        if suite_id == "tqhc2_cell_indomain":
            hard_coverage = all(
                split_conditions[split_id]["profiles"] == list(EXPECTED_PROFILES)
                and split_conditions[split_id]["intervals"] == list(EXPECTED_INTERVALS)
                for split_id in ("validation", "test")
            )
        else:
            held_out = suite_id.rsplit("_", 1)[-1]
            source_profiles = sorted(set(EXPECTED_PROFILES).difference({held_out}))
            hard_coverage = (
                split_conditions["validation"]["profiles"] == source_profiles
                and split_conditions["validation"]["intervals"] == list(EXPECTED_INTERVALS)
                and split_conditions["test"]["profiles"] == [held_out]
                and split_conditions["test"]["cell_count"] == 12
            )
        targets = selection_audits[suite_id]["target_sample_fractions"]
        measured_deviation = sum(
            abs(split_conditions[split_id]["sample_fraction"] - float(targets[split_id]))
            for split_id in SPLIT_IDS
        )
        ratio_bound = (
            abs(
                measured_deviation
                - float(selection_audits[suite_id]["l1_sample_fraction_deviation"])
            )
            < 1e-12
        )
        covered = set(sample_frame["sample_id"].astype(str))
        suite_manifest_hashes = {
            path: digest
            for path, digest in manifest_hashes.items()
            if path.startswith(f"splits/{suite_id}-")
        }
        valid = (
            covered == all_sample_ids
            and memberships.eq(1).all()
            and all(
                set(counts) == {"benign", "malicious"} for counts in split_label_counts.values()
            )
            and len(suite_manifest_hashes) == 3
            and cell_counts_valid
            and hard_coverage
            and ratio_bound
        )
        suite_audits[suite_id] = {
            "cell_counts": dict(sorted(Counter(groups["split_id"].astype(str)).items())),
            "sample_counts": dict(sorted(split_sample_counts.items())),
            "binary_label_counts": split_label_counts,
            "split_conditions": split_conditions,
            "target_sample_fractions": targets,
            "l1_sample_fraction_deviation": measured_deviation,
            "selection": dict(selection_audits[suite_id]),
            "cross_split_sample_count": int(memberships.gt(1).sum()),
            "covered_sample_count": len(covered),
            "manifest_hashes": dict(sorted(suite_manifest_hashes.items())),
            "status": "pass" if valid else "fail",
        }
        duplicate_audits[suite_id] = _duplicate_screen(samples, split_by_cell)
        p0_audits[suite_id] = {
            "checks": {
                "sample_identity": "pass" if covered == all_sample_ids else "fail",
                "group_exclusivity": "pass" if memberships.eq(1).all() else "fail",
                "label_coverage": (
                    "pass"
                    if all(
                        set(counts) == {"benign", "malicious"}
                        for counts in split_label_counts.values()
                    )
                    else "fail"
                ),
                "manifest_binding": "pass" if len(suite_manifest_hashes) == 3 else "fail",
                "cell_count_contract": "pass" if cell_counts_valid else "fail",
                "profile_interval_coverage": "pass" if hard_coverage else "fail",
                "sample_ratio_objective": "pass" if ratio_bound else "fail",
            },
            "overall_status": "provisional_candidate" if valid else "fail",
        }
        if not valid:
            raise TQHC2ABCCandidateError(f"套件审计失败：{suite_id}")
    return suite_audits, duplicate_audits, p0_audits


def materialize_candidate_abc(
    *,
    profile_dirs: Mapping[str, Path],
    approved_inputs: Mapping[str, Mapping[str, object]],
    output_dir: Path,
) -> dict[str, object]:
    """生成 TQH-C2 A/B/C 的统一候选协议，不覆盖历史 C-only 制品。"""
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise TQHC2ABCCandidateError(f"输出目录已存在，拒绝覆盖：{output_dir}")
    output_dir.mkdir(parents=True)
    incomplete_marker = output_dir / "_INCOMPLETE"
    incomplete_marker.write_text('{"status":"incomplete"}\n', encoding="utf-8")
    (output_dir / "splits").mkdir()
    (output_dir / "audit").mkdir()

    master, resolved_dirs, input_audits = _load_masters(profile_dirs, approved_inputs)
    base_groups = _build_base_groups(master)
    suite_groups, selection_audits = _build_suite_groups(base_groups)
    features, sequence_hashes, row_group_audit = _stream_packet_features(master, resolved_dirs)
    samples = _build_samples(master, features, sequence_hashes)

    samples_path = output_dir / "samples.parquet"
    groups_path = output_dir / "groups.parquet"
    samples.to_parquet(samples_path, index=False, engine="pyarrow", compression="zstd")
    suite_groups.to_parquet(groups_path, index=False, engine="pyarrow", compression="zstd")
    _write_yaml(output_dir / "field-roles.yaml", _field_roles())
    _write_jsonl(output_dir / "source-artifacts.jsonl", _source_artifacts(resolved_dirs))
    _write_jsonl(output_dir / "audit" / "row-groups.jsonl", row_group_audit)

    samples_sha256 = _sha256_file(samples_path)
    split_by_suite_cell = {
        (str(row.suite_id), str(row.capture_group_id)): str(row.split_id)
        for row in suite_groups.itertuples(index=False)
    }
    for (suite_id, split_id), relative_path in SPLIT_FILENAMES.items():
        cell_splits = {
            capture_group_id: assigned_split
            for (assigned_suite, capture_group_id), assigned_split in split_by_suite_cell.items()
            if assigned_suite == suite_id
        }
        split_samples = samples[
            samples["capture_group_id"].map(cell_splits).eq(split_id)
        ].sort_values("sample_id", kind="mergesort")
        if split_samples.empty:
            raise TQHC2ABCCandidateError(f"套件划分不得为空：{suite_id}:{split_id}")
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

    manifest_hashes = {
        "samples.parquet": samples_sha256,
        **{
            relative_path: _sha256_file(output_dir / relative_path)
            for relative_path in SPLIT_FILENAMES.values()
        },
    }
    _write_json(output_dir / "audit" / "manifest-hashes.json", manifest_hashes)
    suite_audits, duplicate_audits, p0_audits = _suite_audits(
        samples, suite_groups, manifest_hashes, selection_audits
    )
    _write_json(output_dir / "audit" / "suite-audits.json", suite_audits)
    _write_json(output_dir / "audit" / "duplicate-signatures.json", duplicate_audits)
    _write_json(output_dir / "audit" / "p0-subsets.json", p0_audits)
    _write_json(
        output_dir / "audit" / "label-coverage.json",
        {
            "source_record_count": int(len(master)),
            "candidate_record_count": int(len(samples)),
            "excluded_record_count": int(len(master) - len(samples)),
            "source_label_status_counts": dict(sorted(Counter(master["label_status"]).items())),
            "candidate_binary_label_counts": dict(sorted(Counter(samples["binary_label"]).items())),
            "status": "pass",
        },
    )
    sensitive_hits = [
        field
        for field in MODEL_FEATURE_FIELDS
        if set(field.lower().split("_")).intersection(SENSITIVE_FIELD_TOKENS)
    ]
    _write_json(
        output_dir / "audit" / "field-budget.json",
        {
            "view_name": TREE_VIEW_NAME,
            "model_input_fields": list(MODEL_FEATURE_FIELDS),
            "model_input_field_count": len(MODEL_FEATURE_FIELDS),
            "sensitive_field_hits": sensitive_hits,
            "training_fitted_transformations": [],
            "status": "pass" if not sensitive_hits else "fail",
        },
    )
    _write_json(
        output_dir / "audit" / "streaming-audit.json",
        {
            "reader": "pyarrow.parquet.ParquetFile.read_row_group",
            "packet_table_loaded_whole": False,
            "row_group_count": len(row_group_audit),
            "profiles": list(EXPECTED_PROFILES),
            "all_row_groups_single_cell": True,
            "all_cell_row_groups_contiguous": True,
            "cell_order_fallback_detected": False,
            "status": "pass",
        },
    )
    _write_json(
        output_dir / "audit" / "input-contract.json",
        {
            "dataset_version": DATASET_VERSION,
            "profiles": list(EXPECTED_PROFILES),
            "cells_per_profile": 12,
            "approved_inputs": input_audits,
            "sample_id_unique": True,
            "status": "pass",
        },
    )

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
    artifact_hashes = {
        path.relative_to(output_dir).as_posix(): _sha256_file(path)
        for path in [*artifact_paths, artifact_list_path]
    }
    protocol = {
        "protocol_version": PROTOCOL_VERSION,
        "status": PROTOCOL_STATUS,
        "phase": PROTOCOL_PHASE,
        "review_status": REVIEW_STATUS,
        "candidate_id": CANDIDATE_ID,
        "scope": "TQH-C2 profiles A/B/C, 36 complete cells, four suites",
        "suite_ids": list(SUITE_IDS),
        "final_tuning_allowed": False,
        "final_test_claim_allowed": False,
        "artifacts": dict(sorted(artifact_hashes.items())),
        "limitations": [
            "这是统一数据冻结前的理论筛选候选，不是最终 dataset-v1。",
            "最终测试 cell 和留一 profile 测试域不得参与调参或归一化统计。",
            "残余重复只记录并进行敏感性分析，不移动或拆分完整 cell。",
        ],
    }
    _write_yaml(output_dir / "protocol.yaml", protocol)
    incomplete_marker.unlink()
    return {
        "candidate_id": CANDIDATE_ID,
        "protocol_version": PROTOCOL_VERSION,
        "review_status": REVIEW_STATUS,
        "protocol_sha256": _sha256_file(output_dir / "protocol.yaml"),
        "sample_count": int(len(samples)),
        "cell_count": int(len(base_groups)),
        "suite_count": len(SUITE_IDS),
        "manifest_count": len(SPLIT_FILENAMES),
        "row_group_count": len(row_group_audit),
        "output_dir": str(output_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="物化 TQH-C2 A/B/C 统一候选协议")
    parser.add_argument("--profile-a-dir", type=Path, required=True)
    parser.add_argument("--profile-b-dir", type=Path, required=True)
    parser.add_argument("--profile-c-dir", type=Path, required=True)
    parser.add_argument("--approved-inputs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    approved_document = _read_json_object(args.approved_inputs, "批准输入配置")
    raw_approved_inputs = approved_document.get("profiles")
    if not isinstance(raw_approved_inputs, Mapping):
        raise TQHC2ABCCandidateError("批准输入配置必须包含 profiles 对象")
    result = materialize_candidate_abc(
        profile_dirs={
            "A": args.profile_a_dir,
            "B": args.profile_b_dir,
            "C": args.profile_c_dir,
        },
        approved_inputs=raw_approved_inputs,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
