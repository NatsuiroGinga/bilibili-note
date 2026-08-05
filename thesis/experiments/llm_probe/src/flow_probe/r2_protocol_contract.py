"""R2 协议数据合同、冻结输入预检和官方 GeNIS 恢复。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
import zlib
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

import yaml

CONFIG_SCHEMA_VERSION = "flow_probe_r2_protocol_contract_v1"
DATASET_VERSION = "flow_probe_r2_protocol_dataset_v0"
DATASET_STAGE = "theory_selection"
DATASET_STATUS = "review_pending"
IMPLEMENTATION_BASE_COMMIT = "acdf98ba5cc776f7c19495fc53b1164e916eb33c"
PUBLISH_ROOT = "runs/data-frozen/dataset-candidate-r2-protocol-v0"
SOURCE_LOCK_ROOT = "runs/data-freeze-configs/r2-protocol-v1/source-locks-v1"
EXECUTION_CODE_REQUIRED_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "configs/r2_protocol_data_v1.yaml",
    "src/flow_probe/__init__.py",
    "src/flow_probe/r2_protocol_contract.py",
    "src/flow_probe/r2_protocol_tqhc2.py",
    "src/flow_probe/tqh_c2.py",
)
OFFICIAL_GENIS_URL = (
    "https://zenodo.org/api/records/14919237/files/2-flows.zip/content"
)
OFFICIAL_GENIS_SIZE = 380755720
OFFICIAL_GENIS_MD5 = "063b7a2ec6e6b73cc302151d2b3ba6d7"

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
COMMON_UNITS = {
    "total_packets": "packets",
    "total_bytes": "network_layer_bytes",
    "packet_length_mean": "network_layer_bytes_per_packet",
    "packet_length_min": "network_layer_bytes",
    "packet_length_max": "network_layer_bytes",
    "iat_mean_ms": "milliseconds",
    "packet_rate": "packets_per_second",
    "byte_rate": "bytes_per_second",
}
RECORD_ROLES = (
    "classification_candidate",
    "evaluation_reference",
    "physics_auxiliary",
    "open_protocol",
)
TRANSPORT_FAMILIES = ("TCP", "UDP", "ICMP", "SCTP", "DCCP", "ESP", "OTHER", "UNKNOWN")
PROTOCOL_TARGETS = (*TRANSPORT_FAMILIES, "QUIC")
QUIC_EVIDENCE_CLASSES = (
    "NONE",
    "V1_LONG_HEADER",
    "CONTEXT_BOUND_SHORT_HEADER",
    "AMBIGUOUS",
)
QUIC_EVIDENCE_PRIORITY = (
    "AMBIGUOUS",
    "V1_LONG_HEADER",
    "CONTEXT_BOUND_SHORT_HEADER",
    "NONE",
)
FIELD_ROLES = ("router_or_physics_input", "audit_only", "blocked_pending_semantics")
AGGREGATE_FRACTION_FIELDS = (
    "tcp_packet_fraction",
    "udp_packet_fraction",
    "icmp_packet_fraction",
    "other_transport_packet_fraction",
    "tcp_syn_packet_fraction",
    "tcp_ack_packet_fraction",
    "tcp_fin_packet_fraction",
    "tcp_rst_packet_fraction",
    "tcp_psh_packet_fraction",
    "payload_observed_fraction",
    "tcp_flags_applicable_fraction",
    "truncation_fraction",
)
QUIC_AGGREGATE_FIELDS = (
    "quic_observed_packet_fraction",
    "quic_v1_long_packet_fraction",
    "quic_context_short_packet_fraction",
    "quic_ambiguous_packet_fraction",
    "quic_fixed_bit_one_fraction",
    "quic_spin_bit_one_fraction",
    "quic_cid_changed_packet_fraction",
    "quic_src_cid_length_mean",
    "quic_dst_cid_length_mean",
)
BLOCKED_PROTOCOL_FIELDS = (
    "tcp_rtt_ms",
    "tcp_rtt_ms_missing",
    "tcp_rtt_ms_applicable",
    "src_window_bytes",
    "src_window_bytes_missing",
    "src_window_bytes_applicable",
    "dst_window_bytes",
    "dst_window_bytes_missing",
    "dst_window_bytes_applicable",
)
_BASE_ROUTER_FIELDS = (
    "transport_family",
    "transport_family_observed",
    "quic_evidence_class",
    "protocol_confidence",
    "shared_expert_mask",
    "tcp_expert_mask",
    "udp_expert_mask",
    "loss_packets",
    "loss_packets_missing",
    "loss_packets_applicable",
    "retrans_packets",
    "retrans_packets_missing",
    "retrans_packets_applicable",
)
EXPECTED_FIELD_ROLE_MAP = {
    **{
        name: "router_or_physics_input"
        for name in (
            *(
                item
                for field_name in COMMON_FIELDS
                for item in (field_name, f"{field_name}_missing")
            ),
            *_BASE_ROUTER_FIELDS,
            *AGGREGATE_FRACTION_FIELDS,
            *(
                item
                for field_name in QUIC_AGGREGATE_FIELDS
                for item in (field_name, f"{field_name}_missing", f"{field_name}_applicable")
            ),
        )
    },
    "sample_id": "audit_only",
    "protocol_target": "audit_only",
    **{name: "blocked_pending_semantics" for name in BLOCKED_PROTOCOL_FIELDS},
}
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MD5_RE = re.compile(r"[0-9a-f]{32}")
_GIT_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:$")
_CONTENT_RANGE_RE = re.compile(r"bytes (\d+)-(\d+)/(\d+)")
_EXTRACTOR_EVIDENCE_MODES = frozenset(
    {"verified_snapshot", "approved_manifest_only_blocked"}
)
_TQH_REQUIRED_ARTIFACTS = frozenset(
    {
        "audit/cell-audit.json",
        "audit/label-coverage.json",
        "audit/leakage-audit.json",
        "master_records.parquet",
        "run_manifest.provisional.json",
        "schema.provisional.json",
        "source_checksums.json",
        "views/packet_observations.parquet",
    }
)


class R2ProtocolContractError(ValueError):
    """R2 配置、源制品或恢复下载不满足冻结合同。"""


@dataclass(frozen=True)
class ParquetWriteSpec:
    version: str
    compression: str
    compression_level: int
    use_dictionary: bool
    write_statistics: bool
    data_page_version: str
    row_group_size: int


@dataclass(frozen=True)
class FrozenArtifactSpec:
    role: str
    root: str
    logical_path: str
    sha256: str | None = None
    row_count: int | None = None
    checksum_manifest: str | None = None
    checksum_key: str | None = None
    source_counts: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class TQHPathMappingSpec:
    source_prefix: str
    root: str
    logical_root: str


@dataclass(frozen=True)
class TQHProfileSpec:
    profile: str
    logical_root: str
    input_id: str
    artifact_manifest_sha256: str
    extractor_contract_sha256: str
    extractor_evidence_mode: str
    master_sha256: str
    master_rows: int
    packets_sha256: str
    packet_rows: int


@dataclass(frozen=True)
class GeNISArtifactSpec:
    logical_path: str
    record_id: str
    doi: str
    version: str
    url: str
    size_bytes: int
    md5: str
    scales_seconds: tuple[int, ...]
    csv_per_scale: int
    materialization_scale_seconds: int
    member_directory_template: str = "flows-{scale}-sec"


@dataclass(frozen=True)
class NS3MatrixSpec:
    seed: int
    run_duration_seconds: int
    window_seconds: float
    windows_per_run: int
    sequence_length_windows: int
    sequences_per_run: int
    split_base_configuration_counts: Mapping[str, int]
    base_configuration_count: int
    protocol_run_count: int
    window_count: int
    sequence_count: int
    paired_completion_minimum: float
    tcp_cwnd_window_coverage_minimum: float
    factor_cell_minimums: Mapping[str, int]
    sequence_minimums_per_transport_and_label: Mapping[str, int]


@dataclass(frozen=True)
class R2ProtocolConfig:
    config_path: Path
    config_sha256: str
    schema_version: str
    dataset_version: str
    stage: str
    status: str
    implementation_base_commit: str
    publish_root: str
    source_lock_root: str
    common_fields: tuple[str, ...]
    common_units: Mapping[str, str]
    enum_values: Mapping[str, tuple[str, ...]]
    aggregate_fraction_fields: tuple[str, ...]
    quic_aggregate_fields: tuple[str, ...]
    quic_parser_version: str
    field_roles: Mapping[str, str]
    semantic_gates: Mapping[str, Mapping[str, str]]
    parquet: ParquetWriteSpec
    frozen_inputs: tuple[FrozenArtifactSpec, ...]
    tqhc2_profiles: Mapping[str, TQHProfileSpec]
    tqhc2_approved_inputs_path: str
    tqhc2_approved_inputs_sha256: str
    tqhc2_artifact_manifest_path: str
    tqhc2_source_manifest_path: str
    tqhc2_expected_artifact_paths: tuple[str, ...]
    tqhc2_raw_source_role_counts: Mapping[str, int]
    tqhc2_historical_path_mappings: tuple[TQHPathMappingSpec, ...]
    genis: GeNISArtifactSpec
    ns3_matrix: NS3MatrixSpec
    information_budgets: Mapping[str, object]


@dataclass(frozen=True)
class ExternalSourceRoots:
    """运行时绝对源路径；这些值永远不会进入冻结源锁。"""

    genis_archive: Path | None = None
    repository_root: Path | None = None
    project_data_root: Path | None = None
    tqhc2_profile_roots: Mapping[str, Path] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceArtifactLock:
    logical_path: str
    role: str
    sha256: str
    size_bytes: int
    row_count: int | None = None
    profile: str | None = None
    evidence_mode: str | None = None
    evidence_status: str | None = None

    def as_dict(self) -> dict[str, object]:
        row: dict[str, object] = {
            "logical_path": self.logical_path,
            "role": self.role,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }
        if self.profile is not None:
            row["profile"] = self.profile
        if self.row_count is not None:
            row["row_count"] = self.row_count
        if self.evidence_mode is not None:
            row["evidence_mode"] = self.evidence_mode
        if self.evidence_status is not None:
            row["evidence_status"] = self.evidence_status
        return row


@dataclass(frozen=True)
class GeNISMemberLock:
    logical_path: str
    member_path: str
    scale_seconds: int
    size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "logical_path": self.logical_path,
            "member_path": self.member_path,
            "scale_seconds": self.scale_seconds,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class GeNISArchiveInventory:
    logical_path: str
    record_id: str
    version: str
    size_bytes: int
    md5: str
    sha256: str
    scale_member_counts: tuple[tuple[int, int], ...]
    materialization_members: tuple[GeNISMemberLock, ...]

    def summary_dict(self) -> dict[str, object]:
        return {
            "logical_path": self.logical_path,
            "record_id": self.record_id,
            "version": self.version,
            "size_bytes": self.size_bytes,
            "md5": self.md5,
            "sha256": self.sha256,
            "scale_member_counts": {
                str(scale): count for scale, count in self.scale_member_counts
            },
            "materialization_member_count": len(self.materialization_members),
        }


@dataclass(frozen=True)
class SourceLock:
    schema_version: str
    dataset_version: str
    stage: str
    status: str
    config_sha256: str
    code_commit: str
    frozen_inputs: tuple[SourceArtifactLock, ...]
    tqhc2_artifacts: tuple[SourceArtifactLock, ...]
    genis: GeNISArchiveInventory
    candidate_source_counts: tuple[tuple[str, int], ...]
    execution_code_lock_sha256: str | None = None


@dataclass(frozen=True)
class ExecutionCodeArtifactLock:
    logical_path: str
    size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "logical_path": self.logical_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class ExecutionCodeLock:
    schema_version: str
    code_commit: str
    worktree_clean: bool
    python_version: str
    pyarrow_version: str
    artifacts: tuple[ExecutionCodeArtifactLock, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "code_commit": self.code_commit,
            "worktree_clean": self.worktree_clean,
            "python_version": self.python_version,
            "pyarrow_version": self.pyarrow_version,
            "artifacts": [item.as_dict() for item in self.artifacts],
        }


@dataclass(frozen=True)
class DownloadReceipt:
    destination: Path
    url: str
    version: str
    size_bytes: int
    md5: str
    sha256: str
    resumed_from_bytes: int
    range_requested: bool
    inventory: GeNISArchiveInventory


def _canonical_json_bytes(value: object) -> bytes:
    try:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise R2ProtocolContractError("值不能编码为规范 JSON") from error
    return payload.encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    """计算 UTF-8、键排序、紧凑分隔符且禁止非有限值的 JSON 哈希。"""

    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_hashes(path: Path) -> tuple[int, str, str]:
    sha256 = hashlib.sha256()
    md5 = hashlib.md5(usedforsecurity=False)
    size_bytes = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size_bytes += len(chunk)
            sha256.update(chunk)
            md5.update(chunk)
    return size_bytes, sha256.hexdigest(), md5.hexdigest()


def _safe_logical_path(value: object, description: str) -> str:
    raw = str(value).strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if (
        not raw
        or raw == "."
        or "://" in raw
        or path.is_absolute()
        or ".." in path.parts
        or any(_WINDOWS_DRIVE_RE.fullmatch(part) for part in path.parts)
    ):
        raise R2ProtocolContractError(f"{description}必须是安全逻辑相对路径：{value}")
    return path.as_posix()


def _mapping(value: object, description: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise R2ProtocolContractError(f"{description}必须是对象")
    return value


def _sequence(value: object, description: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise R2ProtocolContractError(f"{description}必须是列表")
    return value


def _string(mapping: Mapping[str, object], key: str, description: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise R2ProtocolContractError(f"{description}.{key}必须是非空字符串")
    return value.strip()


def _integer(mapping: Mapping[str, object], key: str, description: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise R2ProtocolContractError(f"{description}.{key}必须是整数")
    return value


def _number(mapping: Mapping[str, object], key: str, description: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise R2ProtocolContractError(f"{description}.{key}必须是数值")
    return float(value)


def _boolean(mapping: Mapping[str, object], key: str, description: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise R2ProtocolContractError(f"{description}.{key}必须是布尔值")
    return value


def _sha256(value: object, description: str) -> str:
    digest = str(value).strip()
    if _SHA256_RE.fullmatch(digest) is None:
        raise R2ProtocolContractError(f"{description}必须是小写 SHA-256")
    return digest


def _md5(value: object, description: str) -> str:
    digest = str(value).strip()
    if _MD5_RE.fullmatch(digest) is None:
        raise R2ProtocolContractError(f"{description}必须是小写 MD5")
    return digest


def _git_commit(value: object, description: str) -> str:
    commit = str(value).strip()
    if _GIT_COMMIT_RE.fullmatch(commit) is None:
        raise R2ProtocolContractError(f"{description}必须是 40 位小写 Git 提交哈希")
    return commit


def _expect(actual: object, expected: object, description: str) -> None:
    if actual != expected:
        raise R2ProtocolContractError(
            f"{description}偏离冻结合同：期望 {expected!r}，实际 {actual!r}"
        )


def _string_tuple(value: object, description: str) -> tuple[str, ...]:
    items: list[str] = []
    for index, item in enumerate(_sequence(value, description)):
        if not isinstance(item, str) or not item.strip():
            raise R2ProtocolContractError(f"{description}[{index}]必须是非空字符串")
        items.append(item.strip())
    return tuple(items)


def _int_mapping(value: object, description: str) -> dict[str, int]:
    raw = _mapping(value, description)
    result: dict[str, int] = {}
    for key, item in raw.items():
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            raise R2ProtocolContractError(f"{description}.{key}必须是非负整数")
        result[str(key)] = item
    return result


def _parse_frozen_inputs(value: object) -> tuple[FrozenArtifactSpec, ...]:
    specs: list[FrozenArtifactSpec] = []
    for index, raw_spec in enumerate(_sequence(value, "sources.frozen_inputs")):
        spec = _mapping(raw_spec, f"sources.frozen_inputs[{index}]")
        allowed_fields = {
            "role",
            "root",
            "path",
            "sha256",
            "row_count",
            "checksum_manifest",
            "checksum_key",
            "source_counts",
        }
        if not set(spec).issubset(allowed_fields):
            raise R2ProtocolContractError(
                f"sources.frozen_inputs[{index}] 含未知字段：{sorted(set(spec) - allowed_fields)}"
            )
        logical_path = _safe_logical_path(
            _string(spec, "path", f"sources.frozen_inputs[{index}]"),
            f"sources.frozen_inputs[{index}].path",
        )
        root = _string(spec, "root", f"sources.frozen_inputs[{index}]")
        if root not in {"project", "repository"}:
            raise R2ProtocolContractError(f"冻结输入根类型非法：{logical_path}:{root}")
        digest = None
        if spec.get("sha256") is not None:
            digest = _sha256(spec["sha256"], f"{logical_path}.sha256")
        row_count = None
        if spec.get("row_count") is not None:
            row_count = _integer(spec, "row_count", logical_path)
            if row_count < 0:
                raise R2ProtocolContractError(f"冻结输入行数不能为负：{logical_path}")
        checksum_manifest = None
        checksum_key = None
        if spec.get("checksum_manifest") is not None:
            checksum_manifest = _safe_logical_path(
                _string(spec, "checksum_manifest", logical_path),
                f"{logical_path}.checksum_manifest",
            )
            checksum_key = _safe_logical_path(
                _string(spec, "checksum_key", logical_path), f"{logical_path}.checksum_key"
            )
        if (digest is None) == (checksum_manifest is None):
            raise R2ProtocolContractError(
                f"冻结输入必须且只能使用直接哈希或已冻结清单绑定：{logical_path}"
            )
        source_counts: tuple[tuple[str, int], ...] = ()
        if spec.get("source_counts") is not None:
            source_counts = tuple(
                sorted(_int_mapping(spec["source_counts"], f"{logical_path}.source_counts").items())
            )
        specs.append(
            FrozenArtifactSpec(
                role=_string(spec, "role", f"sources.frozen_inputs[{index}]"),
                root=root,
                logical_path=logical_path,
                sha256=digest,
                row_count=row_count,
                checksum_manifest=checksum_manifest,
                checksum_key=checksum_key,
                source_counts=source_counts,
            )
        )
    paths = [spec.logical_path for spec in specs]
    if len(paths) != len(set(paths)):
        raise R2ProtocolContractError("sources.frozen_inputs 含重复逻辑路径")
    return tuple(specs)


def _parse_tqh_path_mappings(value: object) -> tuple[TQHPathMappingSpec, ...]:
    mappings: list[TQHPathMappingSpec] = []
    for index, raw_mapping in enumerate(
        _sequence(value, "sources.tqhc2.historical_path_mappings")
    ):
        description = f"sources.tqhc2.historical_path_mappings[{index}]"
        mapping = _mapping(raw_mapping, description)
        _expect(
            set(mapping),
            {"source_prefix", "root", "logical_root"},
            f"{description} 字段",
        )
        source_prefix = _string(mapping, "source_prefix", description).replace("\\", "/")
        if (
            source_prefix in {".", "/"}
            or source_prefix.endswith("/")
            or "\x00" in source_prefix
            or PurePosixPath(source_prefix).as_posix() != source_prefix
        ):
            raise R2ProtocolContractError(f"{description}.source_prefix 不是规范完整前缀")
        root = _string(mapping, "root", description)
        if root not in {"project", "repository"}:
            raise R2ProtocolContractError(f"{description}.root 非法：{root}")
        mappings.append(
            TQHPathMappingSpec(
                source_prefix=source_prefix,
                root=root,
                logical_root=_safe_logical_path(
                    _string(mapping, "logical_root", description),
                    f"{description}.logical_root",
                ),
            )
        )
    prefixes = [mapping.source_prefix for mapping in mappings]
    if not mappings or len(prefixes) != len(set(prefixes)):
        raise R2ProtocolContractError("TQH 历史路径前缀映射为空或含重复前缀")
    return tuple(mappings)


def _parse_tqhc2(value: object) -> tuple[
    str,
    str,
    str,
    str,
    tuple[str, ...],
    Mapping[str, int],
    tuple[TQHPathMappingSpec, ...],
    Mapping[str, TQHProfileSpec],
]:
    tqh = _mapping(value, "sources.tqhc2")
    _expect(
        set(tqh),
        {
            "approved_inputs_path",
            "approved_inputs_sha256",
            "artifact_manifest_path",
            "source_manifest_path",
            "expected_artifact_paths",
            "raw_source_role_counts",
            "historical_path_mappings",
            "profiles",
        },
        "sources.tqhc2 字段",
    )
    approved_path = _safe_logical_path(
        _string(tqh, "approved_inputs_path", "sources.tqhc2"),
        "sources.tqhc2.approved_inputs_path",
    )
    approved_sha = _sha256(
        tqh.get("approved_inputs_sha256"), "sources.tqhc2.approved_inputs_sha256"
    )
    artifact_manifest = _safe_logical_path(
        _string(tqh, "artifact_manifest_path", "sources.tqhc2"),
        "sources.tqhc2.artifact_manifest_path",
    )
    source_manifest = _safe_logical_path(
        _string(tqh, "source_manifest_path", "sources.tqhc2"),
        "sources.tqhc2.source_manifest_path",
    )
    expected_artifacts = tuple(
        sorted(
            _safe_logical_path(item, "sources.tqhc2.expected_artifact_paths")
            for item in _sequence(
                tqh.get("expected_artifact_paths"), "sources.tqhc2.expected_artifact_paths"
            )
        )
    )
    _expect(frozenset(expected_artifacts), _TQH_REQUIRED_ARTIFACTS, "TQH 上游制品集合")
    raw_role_counts = _int_mapping(
        tqh.get("raw_source_role_counts"), "sources.tqhc2.raw_source_role_counts"
    )
    historical_path_mappings = _parse_tqh_path_mappings(
        tqh.get("historical_path_mappings")
    )
    profiles: dict[str, TQHProfileSpec] = {}
    for profile, raw_profile in _mapping(tqh.get("profiles"), "sources.tqhc2.profiles").items():
        key = str(profile)
        spec = _mapping(raw_profile, f"sources.tqhc2.profiles.{key}")
        _expect(
            set(spec),
            {
                "logical_root",
                "input_id",
                "artifact_manifest_sha256",
                "extractor_contract_sha256",
                "extractor_evidence_mode",
                "master_sha256",
                "master_rows",
                "packets_sha256",
                "packet_rows",
            },
            f"sources.tqhc2.profiles.{key} 字段",
        )
        extractor_evidence_mode = _string(
            spec, "extractor_evidence_mode", f"sources.tqhc2.profiles.{key}"
        )
        if extractor_evidence_mode not in _EXTRACTOR_EVIDENCE_MODES:
            raise R2ProtocolContractError(
                f"TQH {key} 提取器证据模式非法：{extractor_evidence_mode}"
            )
        profiles[key] = TQHProfileSpec(
            profile=key,
            logical_root=_safe_logical_path(
                _string(spec, "logical_root", f"sources.tqhc2.profiles.{key}"),
                f"sources.tqhc2.profiles.{key}.logical_root",
            ),
            input_id=_string(spec, "input_id", f"sources.tqhc2.profiles.{key}"),
            artifact_manifest_sha256=_sha256(
                spec.get("artifact_manifest_sha256"), f"{key}.artifact_manifest_sha256"
            ),
            extractor_contract_sha256=_sha256(
                spec.get("extractor_contract_sha256"), f"{key}.extractor_contract_sha256"
            ),
            extractor_evidence_mode=extractor_evidence_mode,
            master_sha256=_sha256(spec.get("master_sha256"), f"{key}.master_sha256"),
            master_rows=_integer(spec, "master_rows", key),
            packets_sha256=_sha256(spec.get("packets_sha256"), f"{key}.packets_sha256"),
            packet_rows=_integer(spec, "packet_rows", key),
        )
    _expect(set(profiles), {"A", "B", "C"}, "TQH profile 集合")
    return (
        approved_path,
        approved_sha,
        artifact_manifest,
        source_manifest,
        expected_artifacts,
        raw_role_counts,
        historical_path_mappings,
        profiles,
    )


def _parse_genis(value: object) -> GeNISArtifactSpec:
    spec = _mapping(value, "sources.genis")
    _expect(
        set(spec),
        {
            "logical_path",
            "record_id",
            "doi",
            "version",
            "url",
            "size_bytes",
            "md5",
            "scales_seconds",
            "csv_per_scale",
            "materialization_scale_seconds",
            "member_directory_template",
        },
        "sources.genis 字段",
    )
    raw_scales = _sequence(spec.get("scales_seconds"), "sources.genis.scales_seconds")
    scales: list[int] = []
    for index, item in enumerate(raw_scales):
        if isinstance(item, bool) or not isinstance(item, int):
            raise R2ProtocolContractError(
                f"sources.genis.scales_seconds[{index}]必须是整数"
            )
        scales.append(item)
    return GeNISArtifactSpec(
        logical_path=_safe_logical_path(
            _string(spec, "logical_path", "sources.genis"), "sources.genis.logical_path"
        ),
        record_id=_string(spec, "record_id", "sources.genis"),
        doi=_string(spec, "doi", "sources.genis"),
        version=_string(spec, "version", "sources.genis"),
        url=_string(spec, "url", "sources.genis"),
        size_bytes=_integer(spec, "size_bytes", "sources.genis"),
        md5=_md5(spec.get("md5"), "sources.genis.md5"),
        scales_seconds=tuple(scales),
        csv_per_scale=_integer(spec, "csv_per_scale", "sources.genis"),
        materialization_scale_seconds=_integer(
            spec, "materialization_scale_seconds", "sources.genis"
        ),
        member_directory_template=_string(
            spec, "member_directory_template", "sources.genis"
        ),
    )


def _parse_ns3(value: object) -> NS3MatrixSpec:
    spec = _mapping(value, "ns3_matrix")
    _expect(
        set(spec),
        {
            "seed",
            "run_duration_seconds",
            "window_seconds",
            "windows_per_run",
            "sequence_length_windows",
            "sequences_per_run",
            "split_base_configuration_counts",
            "base_configuration_count",
            "protocol_run_count",
            "window_count",
            "sequence_count",
            "paired_completion_minimum",
            "tcp_cwnd_window_coverage_minimum",
            "factor_cell_minimums",
            "sequence_minimums_per_transport_and_label",
        },
        "ns3_matrix 字段",
    )
    return NS3MatrixSpec(
        seed=_integer(spec, "seed", "ns3_matrix"),
        run_duration_seconds=_integer(spec, "run_duration_seconds", "ns3_matrix"),
        window_seconds=_number(spec, "window_seconds", "ns3_matrix"),
        windows_per_run=_integer(spec, "windows_per_run", "ns3_matrix"),
        sequence_length_windows=_integer(spec, "sequence_length_windows", "ns3_matrix"),
        sequences_per_run=_integer(spec, "sequences_per_run", "ns3_matrix"),
        split_base_configuration_counts=_int_mapping(
            spec.get("split_base_configuration_counts"),
            "ns3_matrix.split_base_configuration_counts",
        ),
        base_configuration_count=_integer(spec, "base_configuration_count", "ns3_matrix"),
        protocol_run_count=_integer(spec, "protocol_run_count", "ns3_matrix"),
        window_count=_integer(spec, "window_count", "ns3_matrix"),
        sequence_count=_integer(spec, "sequence_count", "ns3_matrix"),
        paired_completion_minimum=_number(spec, "paired_completion_minimum", "ns3_matrix"),
        tcp_cwnd_window_coverage_minimum=_number(
            spec, "tcp_cwnd_window_coverage_minimum", "ns3_matrix"
        ),
        factor_cell_minimums=_int_mapping(
            spec.get("factor_cell_minimums"), "ns3_matrix.factor_cell_minimums"
        ),
        sequence_minimums_per_transport_and_label=_int_mapping(
            spec.get("sequence_minimums_per_transport_and_label"),
            "ns3_matrix.sequence_minimums_per_transport_and_label",
        ),
    )


def _validate_exact_contract(config: R2ProtocolConfig) -> None:
    _expect(config.schema_version, CONFIG_SCHEMA_VERSION, "schema_version")
    _expect(config.dataset_version, DATASET_VERSION, "dataset.version")
    _expect(config.stage, DATASET_STAGE, "dataset.stage")
    _expect(config.status, DATASET_STATUS, "dataset.status")
    _expect(
        config.implementation_base_commit,
        IMPLEMENTATION_BASE_COMMIT,
        "dataset.implementation_base_commit",
    )
    _expect(config.publish_root, PUBLISH_ROOT, "dataset.publish_root")
    _expect(config.source_lock_root, SOURCE_LOCK_ROOT, "dataset.source_lock_root")
    _expect(config.common_fields, COMMON_FIELDS, "common_view.fields")
    _expect(dict(config.common_units), COMMON_UNITS, "common_view.units")
    expected_enums = {
        "record_role": RECORD_ROLES,
        "transport_family": TRANSPORT_FAMILIES,
        "protocol_target": PROTOCOL_TARGETS,
        "quic_evidence_class": QUIC_EVIDENCE_CLASSES,
        "quic_evidence_priority": QUIC_EVIDENCE_PRIORITY,
        "field_role": FIELD_ROLES,
    }
    _expect(dict(config.enum_values), expected_enums, "protocol.enums")
    _expect(
        config.aggregate_fraction_fields,
        AGGREGATE_FRACTION_FIELDS,
        "protocol.aggregate_fraction_fields",
    )
    _expect(config.quic_aggregate_fields, QUIC_AGGREGATE_FIELDS, "protocol.quic_aggregate_fields")
    _expect(config.quic_parser_version, "flow_probe_quic_wire_image_v1", "QUIC 解析器版本")
    _expect(dict(config.field_roles), EXPECTED_FIELD_ROLE_MAP, "协议字段角色")
    _expect(
        {name: dict(value) for name, value in config.semantic_gates.items()},
        {
            "TotBytes": {
                "status": "blocked_pending_semantics",
                "required_evidence": "hera_source_or_network_layer_packet_recalculation",
            },
            "TcpRtt": {
                "status": "blocked_pending_semantics",
                "required_evidence": "primary_unit_and_aggregation_evidence",
            },
            "SrcWin": {
                "status": "blocked_pending_semantics",
                "required_evidence": "primary_unit_scaling_and_aggregation_evidence",
            },
            "DstWin": {
                "status": "blocked_pending_semantics",
                "required_evidence": "primary_unit_scaling_and_aggregation_evidence",
            },
        },
        "未闭合语义门禁",
    )
    _expect(
        config.parquet,
        ParquetWriteSpec("2.6", "zstd", 9, False, True, "1.0", 65536),
        "Parquet 参数",
    )
    actual_frozen_inputs = tuple(
        (
            spec.role,
            spec.root,
            spec.logical_path,
            spec.sha256,
            spec.row_count,
            spec.checksum_manifest,
            spec.checksum_key,
            spec.source_counts,
        )
        for spec in config.frozen_inputs
    )
    expected_frozen_inputs = (
        (
            "master_records",
            "project",
            "runs/data-frozen/dataset-v1/master_records.parquet",
            "16458a4a191c51eefc58717e16609790b9914936a2470ef29099bdfbc70af703",
            None,
            None,
            None,
            (),
        ),
        (
            "budget_checksums",
            "project",
            "runs/data-frozen/dataset-v1/manifests/budgets/budget_checksums.json",
            "38883c7ef8b1e47ebd218514e71f95474cebaa8637df6b5203326802546a6c2e",
            None,
            None,
            None,
            (),
        ),
        (
            "classification_candidate",
            "project",
            "runs/data-frozen/dataset-v1/manifests/budgets/train_candidate_approx10000.jsonl",
            None,
            10000,
            "runs/data-frozen/dataset-v1/manifests/budgets/budget_checksums.json",
            "manifests/budgets/train_candidate_approx10000.jsonl",
            (("genis", 3973), ("ns3", 2421), ("tqhc2", 3606)),
        ),
        (
            "genis_candidate",
            "project",
            "runs/data-frozen/dataset-candidate-genis-v0/protocol/samples.parquet",
            "2b0d8b49ef81db3a9f9338dfbabe185bab54c02512786c9f64f52718ee8c55a0",
            None,
            None,
            None,
            (),
        ),
        (
            "genis_validation",
            "project",
            "runs/data-frozen/dataset-candidate-genis-v0/protocol/splits/genis-family-development-validation.jsonl",
            "52cce0c3b36273542e1fb05956e30876a8add1f6defd769ffa69b43bfaf19fca",
            10399,
            None,
            None,
            (),
        ),
        (
            "genis_dictionary",
            "repository",
            "raw/datasets/GeNIS-2025/0-info.zip",
            "7ef636cc758586f18a5d9958e68eede9b85925610331283cce802f45542701bc",
            None,
            None,
            None,
            (),
        ),
        (
            "tqhc2_candidate",
            "project",
            "runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/samples.parquet",
            "05cb0774f8197f07d842a21d3c22ce07c111289b7cabe6950023b689c6b51dac",
            None,
            None,
            None,
            (),
        ),
        (
            "tqhc2_validation",
            "project",
            "runs/data-frozen/dataset-candidate-tqhc2-abc-v0/protocol/splits/tqhc2_cell_indomain-validation.jsonl",
            "729860d24f6e6a400ec061077f0111d2fc8504eeb3c3700e21ab6641869d5997",
            4000,
            None,
            None,
            (),
        ),
        (
            "historical_ns3_train",
            "project",
            "runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/train.jsonl",
            "d6a6ca23a985223401e1d650d619c2a50b255d2066769e2478cef72cc6239fa0",
            None,
            None,
            None,
            (),
        ),
        (
            "historical_ns3_validation",
            "project",
            "runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/validation.jsonl",
            "0bbbb4ea483867561c329c896cb4e7745a102cb90024c464654e0b7d673c8723",
            None,
            None,
            None,
            (),
        ),
        (
            "historical_ns3_test",
            "project",
            "runs/ns3-data/ns3-queue-sequences-h4-seed-split-20260721-v2/test.jsonl",
            "6e64d2ab290813a246ed8efcefd1bb19f1026c2de7b7904d111af67b4465ef94",
            None,
            None,
            None,
            (),
        ),
    )
    _expect(actual_frozen_inputs, expected_frozen_inputs, "旧冻结输入合同")
    _expect(
        (
            config.tqhc2_approved_inputs_path,
            config.tqhc2_approved_inputs_sha256,
            config.tqhc2_artifact_manifest_path,
            config.tqhc2_source_manifest_path,
            config.tqhc2_expected_artifact_paths,
            dict(config.tqhc2_raw_source_role_counts),
            tuple(
                (mapping.source_prefix, mapping.root, mapping.logical_root)
                for mapping in config.tqhc2_historical_path_mappings
            ),
        ),
        (
            "runs/data-freeze-configs/tqhc2-abc-v0/approved-inputs.json",
            "191f737ae18eec982b8031b1ced2e6f74b3f122e6c1fa0bc97596ab3cdada610",
            "artifact_checksums.provisional.json",
            "source_checksums.json",
            tuple(sorted(_TQH_REQUIRED_ARTIFACTS)),
            {"extractor_source": 1, "label_or_audit_source": 60, "source_pcap": 12},
            (
                ("/Users/bilibili/personal/note/raw", "repository", "raw"),
                ("../../../raw", "repository", "raw"),
                (
                    "/Users/bilibili/personal/note/thesis/experiments/llm_probe/src",
                    "project",
                    "src",
                ),
            ),
        ),
        "TQH 公共源合同",
    )
    actual_tqh_profiles = {
        profile: (
            spec.logical_root,
            spec.input_id,
            spec.artifact_manifest_sha256,
            spec.extractor_contract_sha256,
            spec.extractor_evidence_mode,
            spec.master_sha256,
            spec.master_rows,
            spec.packets_sha256,
            spec.packet_rows,
        )
        for profile, spec in config.tqhc2_profiles.items()
    }
    expected_tqh_profiles = {
        "A": (
            "runs/data-frozen/dataset-v1-provisional/tqh-c2-A-20260728-v1",
            "tqh-c2-A-20260728-v1",
            "f26723b0a10deb383aff9f7f9fa5893d30b883f1f602cbbc633e4e1846015a68",
            "7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617",
            "approved_manifest_only_blocked",
            "8dcbce77d18f785c1712f525807aab7f4ddf1c53ce1fc559cb59765487280799",
            181556,
            "2366a25dc3a3c847ecb3549c4d79d131e172a17aa53b709dd65949a26647a32f",
            15761376,
        ),
        "B": (
            "runs/data-prepared/tqh-c2-b-v101-provisional-20260728",
            "tqh-c2-B-20260728-v1",
            "44900a6bee08f0d339693524a42975d1ad9e47721f38bb70c1a6c886ce17a6f5",
            "c681639af7de97bf4902341e0e51066455492df968769be8d1e6cfaefb4fcdc0",
            "verified_snapshot",
            "bac856cfbae0aa9a31faeaead635b3852bb68765209c0769eaee42b5cb5eb6ba",
            115734,
            "97e736d28920702c3fab72cf86040a3258d4f0dcd8ea6a2c9db31d4b60a2f108",
            9857089,
        ),
        "C": (
            "runs/data-frozen/dataset-v1-provisional/tqh-c2-C-20260724-v8",
            "tqh-c2-C-20260724-v8",
            "2203113a7cf198de5b393923a20cba22ad06127545123471f033cccb8a3e925e",
            "7daa2b2de3878660bb02860f416892d5a64aba3cc7edf5de561faa575047a617",
            "approved_manifest_only_blocked",
            "fbbfaaae1a8bc27fb658700f53ad3af371c968f3c9c143c6b6928c40d155ceba",
            36671,
            "44547ce8421015ebfe5efead5fac4638ad5169137db735955e550c800fd4ef86",
            396271,
        ),
    }
    _expect(actual_tqh_profiles, expected_tqh_profiles, "TQH A/B/C 源合同")
    _expect(
        (
            config.genis.logical_path,
            config.genis.record_id,
            config.genis.doi,
            config.genis.version,
            config.genis.url,
            config.genis.size_bytes,
            config.genis.md5,
            config.genis.scales_seconds,
            config.genis.csv_per_scale,
            config.genis.materialization_scale_seconds,
            config.genis.member_directory_template,
        ),
        (
            "zenodo:14919237/2-flows.zip",
            "14919237",
            "10.5281/zenodo.14919237",
            "1.0.0",
            OFFICIAL_GENIS_URL,
            OFFICIAL_GENIS_SIZE,
            OFFICIAL_GENIS_MD5,
            (5, 10, 30, 60),
            11,
            10,
            "flows-{scale}-sec",
        ),
        "GeNIS 官方元数据",
    )
    ns3 = config.ns3_matrix
    _expect(
        dict(ns3.split_base_configuration_counts),
        {"train-fit": 128, "calibration": 32, "validation": 32, "test": 32, "unseen-configuration": 32},
        "ns-3 划分数量",
    )
    _expect(
        (
            ns3.seed,
            ns3.run_duration_seconds,
            ns3.window_seconds,
            ns3.windows_per_run,
            ns3.sequence_length_windows,
            ns3.sequences_per_run,
            ns3.base_configuration_count,
            ns3.protocol_run_count,
            ns3.window_count,
            ns3.sequence_count,
            ns3.paired_completion_minimum,
            ns3.tcp_cwnd_window_coverage_minimum,
        ),
        (20260731, 12, 0.1, 120, 4, 30, 256, 512, 61440, 15360, 0.95, 0.95),
        "ns-3 数量和覆盖合同",
    )
    _expect(
        dict(ns3.factor_cell_minimums),
        {"train-fit": 15, "calibration": 3, "validation": 3, "test": 3, "unseen-configuration": 3},
        "ns-3 因子单元门槛",
    )
    _expect(
        dict(ns3.sequence_minimums_per_transport_and_label),
        {"train-fit": 1728, "calibration": 432, "validation": 432, "test": 432, "unseen-configuration": 432},
        "ns-3 序列覆盖门槛",
    )
    _expect(
        dict(config.information_budgets),
        {
            "shared_invariants": {
                "candidate_count": 10000,
                "candidate_order": "identical",
                "labels": "identical",
                "splits": "identical",
                "common_features": "identical",
                "physics_auxiliary": "identical",
            },
            "groups": {
                "A": {
                    "classification_inputs": ["x_common"],
                    "physics_branch": "unified_without_protocol",
                    "physics_inputs": [],
                    "physics_truth_equal_to": "C",
                },
                "B": {
                    "classification_inputs": ["x_common", "x_proto"],
                    "physics_branch": "unified_without_protocol",
                    "physics_inputs": [],
                    "physics_truth_equal_to": "D",
                },
                "C": {
                    "classification_inputs": ["x_common"],
                    "physics_branch": "protocol_experts",
                    "physics_inputs": [
                        "x_proto",
                        "fixed_hard_masks",
                        "stop_gradient_calibrated_confidence",
                    ],
                    "physics_truth_equal_to": "A",
                },
                "D": {
                    "classification_inputs": ["x_common", "x_proto"],
                    "physics_branch": "protocol_experts",
                    "physics_inputs": [
                        "x_proto",
                        "fixed_hard_masks",
                        "stop_gradient_calibrated_confidence",
                    ],
                    "physics_truth_equal_to": "B",
                },
            },
            "manifest_hash_fields": [
                "candidate_order_sha256",
                "label_sha256",
                "split_sha256",
                "x_common_sha256",
                "x_proto_sha256",
                "physics_auxiliary_sha256",
            ],
        },
        "A/B/C/D 信息预算",
    )


def load_r2_config(path: Path) -> R2ProtocolConfig:
    """加载并严格核对 R2 静态配置，任何合同漂移立即失败。"""

    path = Path(path)
    if not path.is_file():
        raise R2ProtocolContractError(f"R2 配置不存在：{path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise R2ProtocolContractError(f"R2 配置无法读取：{path}") from error
    document = _mapping(raw, "R2 配置")
    _expect(
        set(document),
        {
            "schema_version",
            "dataset",
            "common_view",
            "protocol",
            "parquet",
            "sources",
            "ns3_matrix",
            "information_budgets",
        },
        "R2 配置顶层字段",
    )
    dataset = _mapping(document.get("dataset"), "dataset")
    common = _mapping(document.get("common_view"), "common_view")
    protocol = _mapping(document.get("protocol"), "protocol")
    _expect(
        set(dataset),
        {
            "version",
            "stage",
            "status",
            "implementation_base_commit",
            "publish_root",
            "source_lock_root",
        },
        "dataset 字段",
    )
    _expect(set(common), {"fields", "units", "missing_suffix"}, "common_view 字段")
    _expect(_string(common, "missing_suffix", "common_view"), "_missing", "共同字段缺失后缀")
    _expect(
        set(protocol),
        {
            "quic_parser_version",
            "enums",
            "aggregate_fraction_fields",
            "quic_aggregate_fields",
            "field_roles",
            "semantic_gates",
        },
        "protocol 字段",
    )
    raw_enums = _mapping(protocol.get("enums"), "protocol.enums")
    enum_values = {
        str(name): _string_tuple(values, f"protocol.enums.{name}")
        for name, values in raw_enums.items()
    }
    roles: dict[str, str] = {}
    for role, raw_fields in _mapping(protocol.get("field_roles"), "protocol.field_roles").items():
        role_name = str(role)
        if role_name not in FIELD_ROLES:
            raise R2ProtocolContractError(f"未知字段角色：{role_name}")
        for field_name in _string_tuple(raw_fields, f"protocol.field_roles.{role_name}"):
            if field_name in roles:
                raise R2ProtocolContractError(f"字段重复登记角色：{field_name}")
            roles[field_name] = role_name
    semantic_gates = {
        str(name): {
            str(key): str(item)
            for key, item in _mapping(value, f"protocol.semantic_gates.{name}").items()
        }
        for name, value in _mapping(
            protocol.get("semantic_gates"), "protocol.semantic_gates"
        ).items()
    }
    _expect(set(semantic_gates), {"TotBytes", "TcpRtt", "SrcWin", "DstWin"}, "语义门禁字段")
    if any(gate.get("status") != "blocked_pending_semantics" for gate in semantic_gates.values()):
        raise R2ProtocolContractError("四个未闭合语义门禁必须保持 blocked_pending_semantics")
    parquet_raw = _mapping(document.get("parquet"), "parquet")
    _expect(
        set(parquet_raw),
        {
            "version",
            "compression",
            "compression_level",
            "use_dictionary",
            "write_statistics",
            "data_page_version",
            "row_group_size",
        },
        "parquet 字段",
    )
    parquet = ParquetWriteSpec(
        version=_string(parquet_raw, "version", "parquet"),
        compression=_string(parquet_raw, "compression", "parquet"),
        compression_level=_integer(parquet_raw, "compression_level", "parquet"),
        use_dictionary=_boolean(parquet_raw, "use_dictionary", "parquet"),
        write_statistics=_boolean(parquet_raw, "write_statistics", "parquet"),
        data_page_version=_string(parquet_raw, "data_page_version", "parquet"),
        row_group_size=_integer(parquet_raw, "row_group_size", "parquet"),
    )
    sources = _mapping(document.get("sources"), "sources")
    _expect(set(sources), {"frozen_inputs", "tqhc2", "genis"}, "sources 字段")
    frozen_inputs = _parse_frozen_inputs(sources.get("frozen_inputs"))
    (
        approved_path,
        approved_sha,
        tqh_artifact_manifest,
        tqh_source_manifest,
        tqh_expected_artifacts,
        tqh_raw_role_counts,
        tqh_historical_path_mappings,
        tqh_profiles,
    ) = _parse_tqhc2(sources.get("tqhc2"))
    config = R2ProtocolConfig(
        config_path=path.resolve(),
        config_sha256=_sha256_file(path),
        schema_version=_string(document, "schema_version", "R2 配置"),
        dataset_version=_string(dataset, "version", "dataset"),
        stage=_string(dataset, "stage", "dataset"),
        status=_string(dataset, "status", "dataset"),
        implementation_base_commit=_git_commit(
            dataset.get("implementation_base_commit"), "dataset.implementation_base_commit"
        ),
        publish_root=_safe_logical_path(
            _string(dataset, "publish_root", "dataset"), "dataset.publish_root"
        ),
        source_lock_root=_safe_logical_path(
            _string(dataset, "source_lock_root", "dataset"), "dataset.source_lock_root"
        ),
        common_fields=_string_tuple(common.get("fields"), "common_view.fields"),
        common_units={
            str(name): str(value)
            for name, value in _mapping(common.get("units"), "common_view.units").items()
        },
        enum_values=enum_values,
        aggregate_fraction_fields=_string_tuple(
            protocol.get("aggregate_fraction_fields"), "protocol.aggregate_fraction_fields"
        ),
        quic_aggregate_fields=_string_tuple(
            protocol.get("quic_aggregate_fields"), "protocol.quic_aggregate_fields"
        ),
        quic_parser_version=_string(protocol, "quic_parser_version", "protocol"),
        field_roles=roles,
        semantic_gates=semantic_gates,
        parquet=parquet,
        frozen_inputs=frozen_inputs,
        tqhc2_profiles=tqh_profiles,
        tqhc2_approved_inputs_path=approved_path,
        tqhc2_approved_inputs_sha256=approved_sha,
        tqhc2_artifact_manifest_path=tqh_artifact_manifest,
        tqhc2_source_manifest_path=tqh_source_manifest,
        tqhc2_expected_artifact_paths=tqh_expected_artifacts,
        tqhc2_raw_source_role_counts=tqh_raw_role_counts,
        tqhc2_historical_path_mappings=tqh_historical_path_mappings,
        genis=_parse_genis(sources.get("genis")),
        ns3_matrix=_parse_ns3(document.get("ns3_matrix")),
        information_budgets=dict(
            _mapping(document.get("information_budgets"), "information_budgets")
        ),
    )
    _validate_exact_contract(config)
    return config


def _json_object(path: Path, description: str) -> Mapping[str, object]:
    if not path.is_file():
        raise R2ProtocolContractError(f"缺少{description}：{path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise R2ProtocolContractError(f"{description}不是合法 JSON：{path}") from error
    return _mapping(value, description)


def _parquet_rows(path: Path) -> int:
    try:
        import pyarrow.parquet as pq

        return pq.ParquetFile(path).metadata.num_rows
    except Exception as error:
        raise R2ProtocolContractError(f"无法读取 Parquet 元数据：{path}") from error


def _jsonl_rows_and_sources(
    path: Path, expected_sources: Mapping[str, int]
) -> tuple[int, Counter[str]]:
    row_count = 0
    source_counts: Counter[str] = Counter()
    try:
        with path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    raise R2ProtocolContractError(f"JSONL 含空行：{path}:{line_number}")
                row_count += 1
                if expected_sources:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise R2ProtocolContractError(
                            f"JSONL 行不是合法 JSON：{path}:{line_number}"
                        ) from error
                    if not isinstance(row, Mapping) or not isinstance(row.get("source_dataset"), str):
                        raise R2ProtocolContractError(
                            f"候选清单缺少 source_dataset：{path}:{line_number}"
                        )
                    source_counts[str(row["source_dataset"])] += 1
    except OSError as error:
        raise R2ProtocolContractError(f"无法读取 JSONL：{path}") from error
    return row_count, source_counts


def _resolve_frozen_path(
    project_root: Path,
    repository_root: Path | None,
    spec: FrozenArtifactSpec,
) -> Path:
    if spec.root == "project":
        return project_root / spec.logical_path
    if repository_root is None:
        raise R2ProtocolContractError(
            f"核验仓库级冻结输入必须显式提供 repository_root：{spec.logical_path}"
        )
    return repository_root / spec.logical_path


def _verify_file(
    path: Path,
    logical_path: str,
    role: str,
    expected_sha256: str,
    *,
    expected_size_bytes: int | None = None,
    row_count: int | None = None,
    source_counts: Mapping[str, int] | None = None,
    profile: str | None = None,
    evidence_mode: str | None = None,
    evidence_status: str | None = None,
) -> SourceArtifactLock:
    if not path.is_file():
        raise R2ProtocolContractError(f"冻结输入不存在：{logical_path}")
    actual_sha256 = _sha256_file(path)
    if actual_sha256 != expected_sha256:
        raise R2ProtocolContractError(
            f"冻结输入 SHA-256 变化：{logical_path}，期望 {expected_sha256}，实际 {actual_sha256}"
        )
    actual_size_bytes = path.stat().st_size
    if expected_size_bytes is not None and actual_size_bytes != expected_size_bytes:
        raise R2ProtocolContractError(
            f"冻结输入大小变化：{logical_path}，"
            f"期望 {expected_size_bytes}，实际 {actual_size_bytes}"
        )
    actual_rows = None
    if row_count is not None:
        if path.suffix == ".parquet":
            actual_rows = _parquet_rows(path)
        elif path.suffix == ".jsonl":
            actual_rows, actual_sources = _jsonl_rows_and_sources(path, source_counts or {})
            if source_counts is not None and actual_sources != Counter(source_counts):
                raise R2ProtocolContractError(
                    f"冻结候选来源数量变化：{logical_path}，"
                    f"期望 {dict(source_counts)}，实际 {dict(actual_sources)}"
                )
        else:
            raise R2ProtocolContractError(f"不支持对该格式核对行数：{logical_path}")
        if actual_rows != row_count:
            raise R2ProtocolContractError(
                f"冻结输入行数变化：{logical_path}，期望 {row_count}，实际 {actual_rows}"
            )
    return SourceArtifactLock(
        logical_path=logical_path,
        role=role,
        sha256=actual_sha256,
        size_bytes=actual_size_bytes,
        row_count=actual_rows,
        profile=profile,
        evidence_mode=evidence_mode,
        evidence_status=evidence_status,
    )


def _normalise_tqh_source_path(
    raw_path: object, mappings: Sequence[TQHPathMappingSpec]
) -> tuple[str, str]:
    raw_text = str(raw_path).strip()
    if (
        re.match(r"^[A-Za-z]:[\\/]", raw_text)
        or raw_text.startswith("\\\\")
        or raw_text.startswith("//")
    ):
        raise R2ProtocolContractError(f"TQH 来源路径不接受 Windows 或 UNC 形式：{raw_path}")
    text = raw_text.replace("\\", "/")
    path = PurePosixPath(text)
    if not text or path.as_posix() != text:
        raise R2ProtocolContractError(f"TQH 来源路径不是规范的完整历史路径：{raw_path}")
    path_parts = path.parts
    matches: list[tuple[TQHPathMappingSpec, tuple[str, ...]]] = []
    for mapping in mappings:
        prefix_parts = PurePosixPath(mapping.source_prefix).parts
        if (
            len(path_parts) > len(prefix_parts)
            and path_parts[: len(prefix_parts)] == prefix_parts
        ):
            matches.append((mapping, path_parts[len(prefix_parts) :]))
    if not matches:
        raise R2ProtocolContractError(f"TQH 来源路径未命中批准的完整历史前缀：{raw_path}")
    if len(matches) != 1:
        raise R2ProtocolContractError(f"TQH 来源路径命中多个历史前缀：{raw_path}")
    mapping, suffix = matches[0]
    if any(part in {"", ".", ".."} for part in suffix):
        raise R2ProtocolContractError(f"TQH 来源路径重锚定结果越界：{raw_path}")
    logical_path = _safe_logical_path(
        PurePosixPath(mapping.logical_root, *suffix).as_posix(),
        "TQH 来源路径重锚定结果",
    )
    return mapping.root, logical_path


def _resolve_tqh_source_path(
    root_kind: str,
    logical_path: str,
    project_root: Path,
    repository_root: Path | None,
) -> Path:
    if root_kind == "repository":
        if repository_root is None:
            raise R2ProtocolContractError(
                f"核验 TQH 原始来源必须显式提供 repository_root：{logical_path}"
            )
        root = Path(repository_root)
    elif root_kind == "project":
        root = Path(project_root)
    else:
        raise R2ProtocolContractError(f"TQH 来源根类型非法：{root_kind}")
    resolved_root = root.resolve()
    resolved_path = (root / logical_path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as error:
        raise R2ProtocolContractError(f"TQH 来源路径重锚定结果越界：{logical_path}") from error
    return resolved_path


def _current_git_commit(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise R2ProtocolContractError("无法取得源锁所需的当前 Git 提交") from error
    return _git_commit(result.stdout.strip(), "当前 Git 提交")


def _git_output(project_root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(project_root), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise R2ProtocolContractError(
            f"Git 合同命令失败：{' '.join(arguments)}"
        ) from error
    return result.stdout


def _execution_code_lock_bytes(lock: ExecutionCodeLock) -> bytes:
    return _canonical_json_bytes(lock.as_dict()) + b"\n"


def build_execution_code_lock(
    project_root: Path, required_paths: Sequence[str]
) -> ExecutionCodeLock:
    """锁定已提交、全仓干净且实际参与 R2 源派生的生产代码。"""

    project_root = Path(project_root).resolve()
    if not project_root.is_dir() or project_root.is_symlink():
        raise R2ProtocolContractError(f"代码锁项目根不是普通目录：{project_root}")
    logical_paths = tuple(
        sorted(_safe_logical_path(path, "代码锁路径") for path in required_paths)
    )
    if len(logical_paths) != len(set(logical_paths)):
        raise R2ProtocolContractError("代码锁路径含重复项")
    if logical_paths != tuple(sorted(EXECUTION_CODE_REQUIRED_PATHS)):
        raise R2ProtocolContractError(
            "代码锁路径集合不完整或含未批准项："
            f"期望 {list(EXECUTION_CODE_REQUIRED_PATHS)}，实际 {list(logical_paths)}"
        )
    repository_root = Path(
        _git_output(project_root, "rev-parse", "--show-toplevel").strip()
    ).resolve()
    try:
        project_prefix = project_root.relative_to(repository_root)
    except ValueError as error:
        raise R2ProtocolContractError("代码锁项目根不在当前 Git 仓库内") from error
    status = _git_output(
        project_root, "status", "--porcelain=v1", "--untracked-files=all"
    )
    if status:
        raise R2ProtocolContractError("代码锁要求整个 Git 工作树干净")
    artifacts: list[ExecutionCodeArtifactLock] = []
    for logical_path in logical_paths:
        path = project_root / logical_path
        try:
            path.resolve().relative_to(project_root)
        except ValueError as error:
            raise R2ProtocolContractError(f"代码锁路径越界：{logical_path}") from error
        if path.is_symlink() or not path.is_file():
            raise R2ProtocolContractError(f"代码锁制品不是普通文件：{logical_path}")
        repository_path = (project_prefix / logical_path).as_posix()
        tracked = _git_output(
            repository_root,
            "ls-files",
            "--error-unmatch",
            "--",
            repository_path,
        ).splitlines()
        if tracked != [repository_path]:
            raise R2ProtocolContractError(f"代码锁制品未被 Git 唯一跟踪：{logical_path}")
        artifacts.append(
            ExecutionCodeArtifactLock(
                logical_path=logical_path,
                size_bytes=path.stat().st_size,
                sha256=_sha256_file(path),
            )
        )
    try:
        import pyarrow
    except ImportError as error:
        raise R2ProtocolContractError("正式代码锁运行时缺少 PyArrow") from error
    return ExecutionCodeLock(
        schema_version="flow_probe_r2_execution_code_lock_v1",
        code_commit=_current_git_commit(project_root),
        worktree_clean=True,
        python_version=platform.python_version(),
        pyarrow_version=str(pyarrow.__version__),
        artifacts=tuple(artifacts),
    )


def load_execution_code_lock(path: Path) -> ExecutionCodeLock:
    """严格读取规范执行代码锁。"""

    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise R2ProtocolContractError(f"执行代码锁不是普通文件：{path}")
    document = _json_object(path, "执行代码锁")
    expected_keys = {
        "schema_version",
        "code_commit",
        "worktree_clean",
        "python_version",
        "pyarrow_version",
        "artifacts",
    }
    if set(document) != expected_keys:
        raise R2ProtocolContractError("执行代码锁字段集合变化")
    if document.get("schema_version") != "flow_probe_r2_execution_code_lock_v1":
        raise R2ProtocolContractError("执行代码锁模式版本变化")
    if document.get("worktree_clean") is not True:
        raise R2ProtocolContractError("执行代码锁未声明干净工作树")
    artifacts: list[ExecutionCodeArtifactLock] = []
    raw_artifacts = _sequence(document.get("artifacts"), "执行代码锁 artifacts")
    for index, raw_artifact in enumerate(raw_artifacts):
        artifact = _mapping(raw_artifact, f"执行代码锁 artifacts[{index}]")
        if set(artifact) != {"logical_path", "sha256", "size_bytes"}:
            raise R2ProtocolContractError("执行代码锁制品字段集合变化")
        size_bytes = _integer(artifact, "size_bytes", "执行代码锁制品")
        if size_bytes < 0:
            raise R2ProtocolContractError("执行代码锁制品大小不能为负")
        artifacts.append(
            ExecutionCodeArtifactLock(
                logical_path=_safe_logical_path(
                    artifact.get("logical_path"), "执行代码锁制品路径"
                ),
                size_bytes=size_bytes,
                sha256=_sha256(artifact.get("sha256"), "执行代码锁制品 SHA-256"),
            )
        )
    if tuple(item.logical_path for item in artifacts) != tuple(
        sorted(EXECUTION_CODE_REQUIRED_PATHS)
    ):
        raise R2ProtocolContractError("执行代码锁制品顺序或集合变化")
    return ExecutionCodeLock(
        schema_version="flow_probe_r2_execution_code_lock_v1",
        code_commit=_git_commit(document.get("code_commit"), "执行代码锁提交"),
        worktree_clean=True,
        python_version=str(document.get("python_version", "")),
        pyarrow_version=str(document.get("pyarrow_version", "")),
        artifacts=tuple(artifacts),
    )


def write_execution_code_lock(lock: ExecutionCodeLock, output_root: Path) -> Path:
    """稳定写出正式执行代码锁，已有不同内容时拒绝覆盖。"""

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / "execution-code-lock.json"
    _write_stable_file(target, _execution_code_lock_bytes(lock))
    return target


def verify_execution_code_lock(project_root: Path, lock: ExecutionCodeLock) -> None:
    """以当前提交、全仓状态、文件哈希和运行时版本重建并核对代码锁。"""

    rebuilt = build_execution_code_lock(
        project_root, [item.logical_path for item in lock.artifacts]
    )
    if rebuilt != lock:
        raise R2ProtocolContractError("当前代码、提交或运行时版本与执行代码锁不一致")


def _verify_tqhc2(
    project_root: Path,
    project_data_root: Path,
    external_sources: ExternalSourceRoots,
    config: R2ProtocolConfig,
) -> tuple[SourceArtifactLock, ...]:
    approved_path = project_data_root / config.tqhc2_approved_inputs_path
    approved = _verify_file(
        approved_path,
        config.tqhc2_approved_inputs_path,
        "approved_inputs",
        config.tqhc2_approved_inputs_sha256,
    )
    approved_document = _json_object(approved_path, "TQH 批准输入")
    approved_profiles = _mapping(approved_document.get("profiles"), "TQH 批准输入 profiles")
    if set(approved_profiles) != set(config.tqhc2_profiles):
        raise R2ProtocolContractError("TQH 批准输入 profile 集合变化")
    locks: list[SourceArtifactLock] = [approved]
    for profile in sorted(config.tqhc2_profiles):
        spec = config.tqhc2_profiles[profile]
        runtime_root = Path(
            external_sources.tqhc2_profile_roots.get(
                profile, project_data_root / spec.logical_root
            )
        )
        approval = _mapping(approved_profiles[profile], f"TQH 批准输入 {profile}")
        expected_approval = {
            "input_id": spec.input_id,
            "artifact_checksums_sha256": spec.artifact_manifest_sha256,
            "extractor_contract_sha256": spec.extractor_contract_sha256,
            "master_record_count": spec.master_rows,
            "packet_record_count": spec.packet_rows,
        }
        _expect(dict(approval), expected_approval, f"TQH {profile} 批准输入")
        artifact_manifest_path = runtime_root / config.tqhc2_artifact_manifest_path
        manifest_lock = _verify_file(
            artifact_manifest_path,
            f"{spec.logical_root}/{config.tqhc2_artifact_manifest_path}",
            "artifact_manifest",
            spec.artifact_manifest_sha256,
            profile=profile,
        )
        locks.append(manifest_lock)
        artifact_manifest = _json_object(artifact_manifest_path, f"TQH {profile} 制品清单")
        if artifact_manifest.get("status") != "provisional":
            raise R2ProtocolContractError(f"TQH {profile} 制品清单状态变化")
        raw_artifacts = _sequence(artifact_manifest.get("files"), f"TQH {profile} 制品清单 files")
        registered: dict[str, tuple[str, int]] = {}
        for index, raw_row in enumerate(raw_artifacts):
            row = _mapping(raw_row, f"TQH {profile} 制品清单行 {index}")
            relative_path = _safe_logical_path(row.get("path"), f"TQH {profile} 制品路径")
            if relative_path in registered:
                raise R2ProtocolContractError(f"TQH {profile} 制品清单含重复路径：{relative_path}")
            registered[relative_path] = (
                _sha256(row.get("sha256"), f"TQH {profile}:{relative_path}"),
                _integer(row, "size_bytes", f"TQH {profile}:{relative_path}"),
            )
        _expect(set(registered), set(config.tqhc2_expected_artifact_paths), f"TQH {profile} 制品集合")
        derived_locks: dict[str, SourceArtifactLock] = {}
        for relative_path in sorted(registered):
            digest, size_bytes = registered[relative_path]
            logical_path = f"{spec.logical_root}/{relative_path}"
            lock = _verify_file(
                runtime_root / relative_path,
                logical_path,
                "tqhc2_upstream",
                digest,
                profile=profile,
            )
            if lock.size_bytes != size_bytes:
                raise R2ProtocolContractError(
                    f"TQH {profile} 制品大小变化：{relative_path}，"
                    f"期望 {size_bytes}，实际 {lock.size_bytes}"
                )
            derived_locks[relative_path] = lock
            locks.append(lock)
        master = derived_locks["master_records.parquet"]
        packets = derived_locks["views/packet_observations.parquet"]
        if master.sha256 != spec.master_sha256 or packets.sha256 != spec.packets_sha256:
            raise R2ProtocolContractError(f"TQH {profile} 主记录或包表未绑定固定哈希")
        actual_master_rows = _parquet_rows(runtime_root / "master_records.parquet")
        actual_packet_rows = _parquet_rows(runtime_root / "views/packet_observations.parquet")
        if actual_master_rows != spec.master_rows or actual_packet_rows != spec.packet_rows:
            raise R2ProtocolContractError(
                f"TQH {profile} 行数变化：主记录 {actual_master_rows}/{spec.master_rows}，"
                f"包 {actual_packet_rows}/{spec.packet_rows}"
            )
        locks[locks.index(master)] = SourceArtifactLock(
            **{**master.as_dict(), "row_count": actual_master_rows}
        )
        locks[locks.index(packets)] = SourceArtifactLock(
            **{**packets.as_dict(), "row_count": actual_packet_rows}
        )
        source_manifest_path = runtime_root / config.tqhc2_source_manifest_path
        source_manifest = _json_object(source_manifest_path, f"TQH {profile} 来源清单")
        source_rows = _sequence(source_manifest.get("files"), f"TQH {profile} 来源清单 files")
        role_counts: Counter[str] = Counter()
        seen_source_paths: set[tuple[str, str]] = set()
        for index, raw_row in enumerate(source_rows):
            row = _mapping(raw_row, f"TQH {profile} 来源清单行 {index}")
            role = _string(row, "role", f"TQH {profile} 来源清单行 {index}")
            root_kind, logical_path = _normalise_tqh_source_path(
                row.get("path"), config.tqhc2_historical_path_mappings
            )
            key = (role, logical_path)
            if key in seen_source_paths:
                raise R2ProtocolContractError(
                    f"TQH {profile} 来源清单含重复逻辑路径：{role}:{logical_path}"
                )
            seen_source_paths.add(key)
            digest = _sha256(row.get("sha256"), f"TQH {profile}:{logical_path}")
            size_bytes = _integer(row, "size_bytes", f"TQH {profile}:{logical_path}")
            if size_bytes < 0:
                raise R2ProtocolContractError(f"TQH 来源大小不能为负：{logical_path}")
            if role == "extractor_source":
                if digest != spec.extractor_contract_sha256:
                    raise R2ProtocolContractError(
                        f"TQH {profile} 提取器来源未绑定批准合同哈希"
                    )
                if spec.extractor_evidence_mode == "verified_snapshot":
                    actual_path = _resolve_tqh_source_path(
                        root_kind,
                        logical_path,
                        project_root,
                        external_sources.repository_root,
                    )
                    raw_lock = _verify_file(
                        actual_path,
                        logical_path,
                        role,
                        digest,
                        expected_size_bytes=size_bytes,
                        profile=profile,
                        evidence_mode=spec.extractor_evidence_mode,
                        evidence_status="verified",
                    )
                else:
                    raw_lock = SourceArtifactLock(
                        logical_path=logical_path,
                        role=role,
                        sha256=digest,
                        size_bytes=size_bytes,
                        profile=profile,
                        evidence_mode=spec.extractor_evidence_mode,
                        evidence_status="blocked",
                    )
            else:
                actual_path = _resolve_tqh_source_path(
                    root_kind,
                    logical_path,
                    project_root,
                    external_sources.repository_root,
                )
                raw_lock = _verify_file(
                    actual_path,
                    logical_path,
                    role,
                    digest,
                    profile=profile,
                )
                if raw_lock.size_bytes != size_bytes:
                    raise R2ProtocolContractError(
                        f"TQH 原始来源大小变化：{profile}:{logical_path}"
                    )
            locks.append(raw_lock)
            role_counts[role] += 1
        if role_counts != Counter(config.tqhc2_raw_source_role_counts):
            raise R2ProtocolContractError(
                f"TQH {profile} 来源角色数量变化："
                f"期望 {dict(config.tqhc2_raw_source_role_counts)}，实际 {dict(role_counts)}"
            )
    return tuple(
        sorted(locks, key=lambda item: (item.logical_path, item.profile or "", item.role))
    )


def _zip_member_path(raw_name: str) -> str:
    if "\x00" in raw_name:
        raise R2ProtocolContractError("GeNIS ZIP 成员名含空字节")
    normalised = raw_name.replace("\\", "/")
    path = PurePosixPath(normalised)
    if (
        not normalised
        or normalised == "."
        or path.is_absolute()
        or ".." in path.parts
        or any(_WINDOWS_DRIVE_RE.fullmatch(part) for part in path.parts)
    ):
        raise R2ProtocolContractError(f"GeNIS ZIP 成员路径不安全：{raw_name}")
    return path.as_posix()


def _member_scale(member_path: str, spec: GeNISArtifactSpec) -> int | None:
    parts = set(PurePosixPath(member_path).parts)
    matches = [
        scale
        for scale in spec.scales_seconds
        if spec.member_directory_template.format(scale=scale) in parts
    ]
    if len(matches) > 1:
        raise R2ProtocolContractError(f"GeNIS ZIP 成员同时命中多个尺度：{member_path}")
    return matches[0] if matches else None


def verify_genis_archive(path: Path, spec: GeNISArtifactSpec) -> GeNISArchiveInventory:
    """核对官方 ZIP 的大小、MD5、中央目录、安全成员与四尺度清单。"""

    path = Path(path)
    if not path.is_file():
        raise R2ProtocolContractError(f"GeNIS 归档不存在：{path}")
    size_bytes, archive_sha256, archive_md5 = _file_hashes(path)
    if size_bytes != spec.size_bytes:
        raise R2ProtocolContractError(
            f"GeNIS 归档大小错误：期望 {spec.size_bytes}，实际 {size_bytes}"
        )
    if archive_md5 != spec.md5:
        raise R2ProtocolContractError(
            f"GeNIS 归档 MD5 错误：期望 {spec.md5}，实际 {archive_md5}"
        )
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as error:
        raise R2ProtocolContractError("GeNIS ZIP 中央目录损坏或缺失") from error
    materialization_members: list[GeNISMemberLock] = []
    scale_counts: Counter[int] = Counter()
    seen_names: set[str] = set()
    try:
        with archive:
            infos = archive.infolist()
            for info in infos:
                member_path = _zip_member_path(info.filename)
                if member_path in seen_names:
                    raise R2ProtocolContractError(f"GeNIS ZIP 含重复成员：{member_path}")
                seen_names.add(member_path)
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise R2ProtocolContractError(f"GeNIS ZIP 含符号链接：{member_path}")
                if info.is_dir():
                    continue
                scale = _member_scale(member_path, spec)
                is_scale_csv = scale is not None and member_path.lower().endswith(".csv")
                if is_scale_csv:
                    scale_counts[scale] += 1
                digest = hashlib.sha256() if scale == spec.materialization_scale_seconds and is_scale_csv else None
                consumed = 0
                try:
                    with archive.open(info, "r") as member:
                        for chunk in iter(lambda: member.read(1024 * 1024), b""):
                            consumed += len(chunk)
                            if digest is not None:
                                digest.update(chunk)
                except (OSError, RuntimeError, zipfile.BadZipFile, zlib.error) as error:
                    raise R2ProtocolContractError(
                        f"GeNIS ZIP 成员 CRC 或内容读取失败：{member_path}"
                    ) from error
                if consumed != info.file_size:
                    raise R2ProtocolContractError(f"GeNIS ZIP 成员大小不一致：{member_path}")
                if digest is not None:
                    materialization_members.append(
                        GeNISMemberLock(
                            logical_path=f"{spec.logical_path}!/{member_path}",
                            member_path=member_path,
                            scale_seconds=scale,
                            size_bytes=consumed,
                            sha256=digest.hexdigest(),
                        )
                    )
    except zipfile.BadZipFile as error:
        raise R2ProtocolContractError("GeNIS ZIP 中央目录或成员数据损坏") from error
    expected_counts = {scale: spec.csv_per_scale for scale in spec.scales_seconds}
    actual_counts = {scale: scale_counts[scale] for scale in spec.scales_seconds}
    if actual_counts != expected_counts:
        raise R2ProtocolContractError(
            f"GeNIS 四尺度 CSV 数量错误：期望 {expected_counts}，实际 {actual_counts}"
        )
    materialization_members.sort(key=lambda item: item.logical_path)
    return GeNISArchiveInventory(
        logical_path=spec.logical_path,
        record_id=spec.record_id,
        version=spec.version,
        size_bytes=size_bytes,
        md5=archive_md5,
        sha256=archive_sha256,
        scale_member_counts=tuple(sorted(actual_counts.items())),
        materialization_members=tuple(materialization_members),
    )


def verify_frozen_inputs(
    project_root: Path,
    external_sources: ExternalSourceRoots,
    config: R2ProtocolConfig,
    execution_code_lock: ExecutionCodeLock | None = None,
) -> SourceLock:
    """逐项核对旧冻结制品、TQH 上游和官方 GeNIS 归档。"""

    project_root = Path(project_root)
    if not project_root.is_dir():
        raise R2ProtocolContractError(f"项目根目录不存在：{project_root}")
    project_data_root = (
        Path(external_sources.project_data_root)
        if external_sources.project_data_root is not None
        else project_root
    )
    if not project_data_root.is_dir() or project_data_root.is_symlink():
        raise R2ProtocolContractError(
            f"冻结数据项目根不是普通目录：{project_data_root}"
        )
    repository_root = (
        Path(external_sources.repository_root)
        if external_sources.repository_root is not None
        else None
    )
    direct_specs = {spec.logical_path: spec for spec in config.frozen_inputs if spec.sha256}
    locks: list[SourceArtifactLock] = []
    for spec in config.frozen_inputs:
        expected_sha = spec.sha256
        expected_size_bytes = None
        if expected_sha is None:
            manifest_spec = direct_specs.get(spec.checksum_manifest or "")
            if manifest_spec is None or manifest_spec.sha256 is None:
                raise R2ProtocolContractError(
                    f"冻结输入引用了未直接绑定的校验清单：{spec.logical_path}"
                )
            manifest_path = _resolve_frozen_path(
                project_data_root, repository_root, manifest_spec
            )
            manifest = _json_object(manifest_path, "冻结预算校验清单")
            artifacts = _mapping(manifest.get("artifacts"), "冻结预算校验清单 artifacts")
            row = _mapping(
                artifacts.get(spec.checksum_key or ""),
                f"冻结预算校验项 {spec.checksum_key}",
            )
            expected_sha = _sha256(row.get("sha256"), f"{spec.logical_path} 间接哈希")
            expected_size_bytes = _integer(row, "size_bytes", f"{spec.logical_path} 间接清单")
        locks.append(
            _verify_file(
                _resolve_frozen_path(project_data_root, repository_root, spec),
                spec.logical_path,
                spec.role,
                expected_sha,
                expected_size_bytes=expected_size_bytes,
                row_count=spec.row_count,
                source_counts=dict(spec.source_counts),
            )
        )
    tqhc2_locks = _verify_tqhc2(
        project_root, project_data_root, external_sources, config
    )
    if external_sources.genis_archive is None:
        raise R2ProtocolContractError("必须通过命令参数提供服务器 GeNIS 官方归档路径")
    genis = verify_genis_archive(Path(external_sources.genis_archive), config.genis)
    candidate_spec = next(
        (spec for spec in config.frozen_inputs if spec.role == "classification_candidate"), None
    )
    if candidate_spec is None:
        raise R2ProtocolContractError("配置缺少共同分类候选清单")
    execution_code_lock_sha256: str | None = None
    if execution_code_lock is not None:
        verify_execution_code_lock(project_root, execution_code_lock)
        if execution_code_lock.code_commit != _current_git_commit(project_root):
            raise R2ProtocolContractError("源锁提交与执行代码锁提交不一致")
        code_artifacts = {
            item.logical_path: item for item in execution_code_lock.artifacts
        }
        config_artifact = code_artifacts.get("configs/r2_protocol_data_v1.yaml")
        if config_artifact is None or config_artifact.sha256 != config.config_sha256:
            raise R2ProtocolContractError("源锁配置与执行代码锁配置不一致")
        execution_code_lock_sha256 = hashlib.sha256(
            _execution_code_lock_bytes(execution_code_lock)
        ).hexdigest()
    return SourceLock(
        schema_version="flow_probe_r2_source_lock_v1",
        dataset_version=config.dataset_version,
        stage=config.stage,
        status=config.status,
        config_sha256=config.config_sha256,
        code_commit=_current_git_commit(project_root),
        frozen_inputs=tuple(sorted(locks, key=lambda item: item.logical_path)),
        tqhc2_artifacts=tqhc2_locks,
        genis=genis,
        candidate_source_counts=candidate_spec.source_counts,
        execution_code_lock_sha256=execution_code_lock_sha256,
    )


def _jsonl_bytes(rows: Sequence[Mapping[str, object]]) -> bytes:
    return b"".join(_canonical_json_bytes(row) + b"\n" for row in rows)


def _assert_lock_paths(lock: SourceLock) -> None:
    for artifact in (*lock.frozen_inputs, *lock.tqhc2_artifacts):
        _safe_logical_path(artifact.logical_path, "源锁逻辑路径")
    _safe_logical_path(lock.genis.logical_path, "GeNIS 源锁逻辑路径")
    for member in lock.genis.materialization_members:
        _safe_logical_path(member.logical_path, "GeNIS 成员逻辑路径")
        _safe_logical_path(member.member_path, "GeNIS ZIP 成员路径")


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _publish_no_replace(partial: Path, target: Path, description: str) -> None:
    if partial.parent.resolve() != target.parent.resolve():
        raise R2ProtocolContractError(f"{description}临时文件必须与目标位于同一目录")
    if not _lexists(partial) or partial.is_symlink() or not partial.is_file():
        raise R2ProtocolContractError(f"{description}临时文件不是普通文件：{partial}")
    try:
        os.link(partial, target)
    except FileExistsError as error:
        raise R2ProtocolContractError(f"{description}目标已存在，拒绝覆盖：{target}") from error
    except OSError as error:
        raise R2ProtocolContractError(f"{description}原子发布失败：{target}") from error
    try:
        partial.unlink()
    except OSError:
        # 目标已原子发布；残留临时硬链接可安全重试清理，不能把成功发布报告为失败。
        pass


def _write_stable_file(path: Path, payload: bytes) -> None:
    if _lexists(path):
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise R2ProtocolContractError(f"拒绝覆盖已有且内容不同的源锁：{path}")
        return
    partial = path.with_name(f"{path.name}.partial")
    if _lexists(partial):
        raise R2ProtocolContractError(f"源锁临时文件已存在：{partial}")
    try:
        with partial.open("xb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        _publish_no_replace(partial, path, "源锁")
    except Exception:
        if _lexists(partial):
            try:
                partial.unlink()
            except OSError:
                pass
        raise


def write_source_lock(lock: SourceLock, output_root: Path) -> None:
    """以稳定排序和规范 JSON 写出三份源锁；相同内容可重复执行。"""

    _assert_lock_paths(lock)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    execution_code_lock_reference: dict[str, object] | None = None
    if lock.execution_code_lock_sha256 is not None:
        execution_path = output_root / "execution-code-lock.json"
        if execution_path.is_symlink() or not execution_path.is_file():
            raise R2ProtocolContractError("正式源锁缺少普通文件形式的执行代码锁")
        actual_execution_sha256 = _sha256_file(execution_path)
        if actual_execution_sha256 != lock.execution_code_lock_sha256:
            raise R2ProtocolContractError("执行代码锁在源锁写出前发生变化")
        execution_code_lock_reference = {
            "logical_path": "execution-code-lock.json",
            "sha256": actual_execution_sha256,
        }
    genis_rows = [
        member.as_dict()
        for member in sorted(lock.genis.materialization_members, key=lambda item: item.logical_path)
    ]
    tqh_rows = [
        artifact.as_dict()
        for artifact in sorted(
            lock.tqhc2_artifacts,
            key=lambda item: (item.logical_path, item.profile or "", item.role),
        )
    ]
    genis_payload = _jsonl_bytes(genis_rows)
    tqh_payload = _jsonl_bytes(tqh_rows)
    main_document = {
        "schema_version": lock.schema_version,
        "dataset_version": lock.dataset_version,
        "stage": lock.stage,
        "status": lock.status,
        "config_sha256": lock.config_sha256,
        "code_commit": lock.code_commit,
        "candidate_source_counts": dict(lock.candidate_source_counts),
        "frozen_inputs": [
            artifact.as_dict()
            for artifact in sorted(lock.frozen_inputs, key=lambda item: item.logical_path)
        ],
        "genis_archive": lock.genis.summary_dict(),
        "genis_member_lock": {
            "logical_path": "genis-member-lock.jsonl",
            "row_count": len(genis_rows),
            "sha256": hashlib.sha256(genis_payload).hexdigest(),
        },
        "tqhc2_source_lock": {
            "logical_path": "tqhc2-source-lock.jsonl",
            "row_count": len(tqh_rows),
            "sha256": hashlib.sha256(tqh_payload).hexdigest(),
        },
    }
    if execution_code_lock_reference is not None:
        main_document["execution_code_lock"] = execution_code_lock_reference
    main_payload = _canonical_json_bytes(main_document) + b"\n"
    targets = {
        "genis-member-lock.jsonl": genis_payload,
        "tqhc2-source-lock.jsonl": tqh_payload,
        "source-lock.json": main_payload,
    }
    for name, payload in targets.items():
        target = output_root / name
        if _lexists(target) and (
            target.is_symlink() or not target.is_file() or target.read_bytes() != payload
        ):
            raise R2ProtocolContractError(f"拒绝覆盖已有且内容不同的源锁：{target}")
    for name in ("genis-member-lock.jsonl", "tqhc2-source-lock.jsonl", "source-lock.json"):
        _write_stable_file(output_root / name, targets[name])


def _download_paths(destination: Path) -> tuple[Path, Path]:
    partial = destination.with_name(f"{destination.name}.download.partial")
    sidecar = partial.with_name(f"{partial.name}.lock.json")
    return partial, sidecar


def _discard_download_state(partial: Path, sidecar: Path) -> None:
    cleanup_errors: list[OSError] = []
    for path in (partial, sidecar):
        if _lexists(path):
            try:
                path.unlink()
            except OSError as error:
                cleanup_errors.append(error)
    if cleanup_errors:
        raise R2ProtocolContractError("GeNIS 不可续传临时状态清理失败") from cleanup_errors[0]


def _download_lock_document(spec: GeNISArtifactSpec) -> dict[str, object]:
    return {
        "url": spec.url,
        "version": spec.version,
        "size_bytes": spec.size_bytes,
        "md5": spec.md5,
    }


def _validate_download_spec(spec: GeNISArtifactSpec) -> None:
    parsed = urlparse(spec.url)
    if (
        spec.url != OFFICIAL_GENIS_URL
        or parsed.scheme != "https"
        or parsed.hostname != "zenodo.org"
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise R2ProtocolContractError("官方恢复只允许配置登记的 Zenodo HTTPS 地址")
    _md5(spec.md5, "GeNIS 下载 MD5")
    if spec.size_bytes <= 0:
        raise R2ProtocolContractError("GeNIS 下载期望大小必须为正整数")


def _open_download(request: urllib.request.Request) -> Any:
    try:
        return urllib.request.urlopen(request, timeout=120)
    except (OSError, urllib.error.URLError) as error:
        raise R2ProtocolContractError("GeNIS 官方下载请求失败") from error


def _response_status(response: Any) -> int:
    status = getattr(response, "status", None)
    if status is None:
        status = response.getcode()
    return int(status)


def _stream_response(response: Any, partial: Path, mode: str) -> None:
    try:
        with partial.open(mode) as output:
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
    except OSError as error:
        raise R2ProtocolContractError("GeNIS 下载临时文件写入失败") from error


def resume_official_download(
    spec: GeNISArtifactSpec, destination: Path
) -> DownloadReceipt:
    """在旁路锁完全匹配时续传，校验成功后原子且不覆盖地发布新目标。"""

    _validate_download_spec(spec)
    destination = Path(destination)
    partial, sidecar = _download_paths(destination)
    if _lexists(destination):
        raise R2ProtocolContractError(f"拒绝覆盖已有 GeNIS 目标：{destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected_lock = _download_lock_document(spec)
    if _lexists(partial):
        if (
            partial.is_symlink()
            or not partial.is_file()
            or not _lexists(sidecar)
            or sidecar.is_symlink()
            or not sidecar.is_file()
        ):
            raise R2ProtocolContractError("已有下载临时文件缺少匹配旁路锁")
        actual_lock = _json_object(sidecar, "GeNIS 下载旁路锁")
        if dict(actual_lock) != expected_lock:
            raise R2ProtocolContractError("GeNIS 下载旁路锁与 URL、版本、大小或 MD5 不一致")
    else:
        if _lexists(sidecar):
            raise R2ProtocolContractError("GeNIS 下载旁路锁存在但临时文件缺失")
        _write_stable_file(sidecar, _canonical_json_bytes(expected_lock) + b"\n")
        partial.touch(exist_ok=False)
    resumed_from = partial.stat().st_size
    if resumed_from > spec.size_bytes:
        _discard_download_state(partial, sidecar)
        raise R2ProtocolContractError("GeNIS 下载临时文件大于官方登记大小")
    range_requested = resumed_from > 0 and resumed_from < spec.size_bytes
    if resumed_from < spec.size_bytes:
        headers = {"Accept-Encoding": "identity"}
        if range_requested:
            headers["Range"] = f"bytes={resumed_from}-"
        request = urllib.request.Request(spec.url, headers=headers, method="GET")
        response = _open_download(request)
        try:
            status_code = _response_status(response)
            if range_requested and status_code == 206:
                content_range = response.headers.get("Content-Range", "")
                match = _CONTENT_RANGE_RE.fullmatch(content_range.strip())
                expected_range = (resumed_from, spec.size_bytes - 1, spec.size_bytes)
                actual_range = tuple(int(value) for value in match.groups()) if match else None
                if actual_range != expected_range:
                    raise R2ProtocolContractError(
                        f"GeNIS 续传 Content-Range 不匹配：{content_range!r}"
                    )
                _stream_response(response, partial, "ab")
            elif range_requested and status_code == 200:
                response.close()
                partial.write_bytes(b"")
                fresh_request = urllib.request.Request(
                    spec.url, headers={"Accept-Encoding": "identity"}, method="GET"
                )
                fresh_response = _open_download(fresh_request)
                try:
                    if _response_status(fresh_response) != 200:
                        raise R2ProtocolContractError("GeNIS 从零重启下载未返回 200")
                    _stream_response(fresh_response, partial, "wb")
                finally:
                    fresh_response.close()
            elif not range_requested and status_code == 200:
                _stream_response(response, partial, "wb")
            else:
                raise R2ProtocolContractError(
                    f"GeNIS 下载响应状态不符合合同：{status_code}"
                )
        finally:
            response.close()
    actual_size = partial.stat().st_size
    if actual_size != spec.size_bytes:
        if actual_size > spec.size_bytes:
            _discard_download_state(partial, sidecar)
        raise R2ProtocolContractError(
            f"GeNIS 下载大小错误：期望 {spec.size_bytes}，实际 {actual_size}"
        )
    try:
        inventory = verify_genis_archive(partial, spec)
    except R2ProtocolContractError as error:
        try:
            _discard_download_state(partial, sidecar)
        except R2ProtocolContractError as cleanup_error:
            raise cleanup_error from error
        raise
    try:
        sidecar.unlink()
    except OSError as error:
        raise R2ProtocolContractError("GeNIS 发布前旁路锁清理失败") from error
    try:
        _publish_no_replace(partial, destination, "GeNIS 下载")
    except R2ProtocolContractError:
        if _lexists(partial):
            try:
                partial.unlink()
            except OSError:
                pass
        raise
    return DownloadReceipt(
        destination=destination,
        url=spec.url,
        version=spec.version,
        size_bytes=inventory.size_bytes,
        md5=inventory.md5,
        sha256=inventory.sha256,
        resumed_from_bytes=resumed_from,
        range_requested=range_requested,
        inventory=inventory,
    )


def _absolute_parameter_path(
    parameters: Mapping[str, object], key: str, description: str
) -> Path:
    raw_value = parameters.get(key)
    if not isinstance(raw_value, str) or not raw_value:
        raise R2ProtocolContractError(f"{description}必须是非空绝对路径")
    path = Path(raw_value)
    if not path.is_absolute():
        raise R2ProtocolContractError(f"{description}必须是绝对路径")
    return path


def _assert_regular_file_set(root: Path, expected_names: Sequence[str]) -> None:
    if root.is_symlink() or not root.is_dir():
        raise R2ProtocolContractError(f"锁定根不是普通目录：{root}")
    actual_names = sorted(path.name for path in root.iterdir())
    if actual_names != sorted(expected_names):
        raise R2ProtocolContractError(
            f"锁定根文件集合变化：期望 {sorted(expected_names)}，实际 {actual_names}"
        )
    for name in expected_names:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise R2ProtocolContractError(f"锁定制品不是普通文件：{name}")


def run_formal_source_preflight(parameters_path: Path) -> Mapping[str, object]:
    """在一次正式运行内完成磁盘、代码、源数据、哈希和文件集合门禁。"""

    parameters_path = Path(parameters_path)
    if parameters_path.is_symlink() or not parameters_path.is_file():
        raise R2ProtocolContractError(f"源预检参数不是普通文件：{parameters_path}")
    parameters = _json_object(parameters_path, "R2 正式源预检参数")
    expected_parameter_keys = {
        "schema_version",
        "host_role",
        "project_root",
        "project_data_root",
        "python_executable",
        "repository_root",
        "config_path",
        "genis_archive",
        "required_code_paths",
        "expected_handoff_bytes",
        "optional_genis_staging_bytes",
        "receipt_path",
    }
    if set(parameters) != expected_parameter_keys:
        raise R2ProtocolContractError("R2 正式源预检参数字段集合变化")
    if parameters.get("schema_version") != "flow_probe_r2_source_preflight_params_v1":
        raise R2ProtocolContractError("R2 正式源预检参数模式版本变化")
    if parameters.get("host_role") != "local_producer":
        raise R2ProtocolContractError("正式源预检只允许 local_producer 主机角色")
    project_root = _absolute_parameter_path(parameters, "project_root", "代码项目根")
    project_data_root = _absolute_parameter_path(
        parameters, "project_data_root", "冻结数据项目根"
    )
    python_executable = _absolute_parameter_path(
        parameters, "python_executable", "正式 Python 解释器"
    )
    if Path(sys.executable).resolve() != python_executable.resolve():
        raise R2ProtocolContractError("正式源预检 Python 解释器与参数不一致")
    repository_root = _absolute_parameter_path(parameters, "repository_root", "仓库数据根")
    genis_archive = _absolute_parameter_path(parameters, "genis_archive", "GeNIS 正式归档")
    receipt_path = _absolute_parameter_path(parameters, "receipt_path", "源预检回执")
    config_path_value = parameters.get("config_path")
    if config_path_value != "configs/r2_protocol_data_v1.yaml":
        raise R2ProtocolContractError("正式源预检配置路径不符合固定合同")
    required_paths = _sequence(parameters.get("required_code_paths"), "required_code_paths")
    if any(not isinstance(path, str) for path in required_paths):
        raise R2ProtocolContractError("required_code_paths 只能包含字符串")
    expected_handoff_bytes = _integer(
        parameters, "expected_handoff_bytes", "正式源预检参数"
    )
    optional_genis_staging_bytes = _integer(
        parameters, "optional_genis_staging_bytes", "正式源预检参数"
    )
    if expected_handoff_bytes != 858_993_460:
        raise R2ProtocolContractError("本机移交制品上界必须固定为 858,993,460 字节")
    if optional_genis_staging_bytes not in {0, OFFICIAL_GENIS_SIZE}:
        raise R2ProtocolContractError("GeNIS 暂存空间只能为零或正式归档精确大小")
    required_free_bytes = max(
        3_221_225_472,
        3 * expected_handoff_bytes + optional_genis_staging_bytes,
    )
    available_bytes = shutil.disk_usage(project_data_root).free
    if available_bytes < required_free_bytes:
        raise R2ProtocolContractError(
            f"本机正式源预检磁盘不足：需要 {required_free_bytes}，可用 {available_bytes}"
        )
    config = load_r2_config(project_root / str(config_path_value))
    source_lock_root = project_data_root / config.source_lock_root
    stage_root = source_lock_root.with_name(f"{source_lock_root.name}.partial")
    if _lexists(source_lock_root) or _lexists(stage_root):
        raise R2ProtocolContractError("正式源锁根或阶段根已存在，拒绝覆盖")
    execution_code_lock = build_execution_code_lock(
        project_root, [str(path) for path in required_paths]
    )
    external_sources = ExternalSourceRoots(
        genis_archive=genis_archive,
        repository_root=repository_root,
        project_data_root=project_data_root,
    )
    source_lock = verify_frozen_inputs(
        project_root,
        external_sources,
        config,
        execution_code_lock=execution_code_lock,
    )
    stage_root.mkdir(parents=True)
    write_execution_code_lock(execution_code_lock, stage_root)
    write_source_lock(source_lock, stage_root)
    expected_lock_names = (
        "execution-code-lock.json",
        "genis-member-lock.jsonl",
        "source-lock.json",
        "tqhc2-source-lock.jsonl",
    )
    _assert_regular_file_set(stage_root, expected_lock_names)
    loaded_code_lock = load_execution_code_lock(stage_root / "execution-code-lock.json")
    verify_execution_code_lock(project_root, loaded_code_lock)
    extractor_status = {
        artifact.profile: {
            "evidence_mode": artifact.evidence_mode,
            "evidence_status": artifact.evidence_status,
        }
        for artifact in source_lock.tqhc2_artifacts
        if artifact.role == "extractor_source"
    }
    expected_extractor_status = {
        "A": {
            "evidence_mode": "approved_manifest_only_blocked",
            "evidence_status": "blocked",
        },
        "B": {"evidence_mode": "verified_snapshot", "evidence_status": "verified"},
        "C": {
            "evidence_mode": "approved_manifest_only_blocked",
            "evidence_status": "blocked",
        },
    }
    if extractor_status != expected_extractor_status:
        raise R2ProtocolContractError("A/B/C 提取器证据状态不符合正式源锁合同")
    if source_lock_root.parent.stat().st_dev != stage_root.stat().st_dev:
        raise R2ProtocolContractError("正式源锁阶段根与发布根不在同一文件系统")
    if _lexists(source_lock_root):
        raise R2ProtocolContractError("正式源锁发布根并发出现，拒绝覆盖")
    os.rename(stage_root, source_lock_root)
    _assert_regular_file_set(source_lock_root, expected_lock_names)
    lock_artifacts = {
        name: {
            "size_bytes": (source_lock_root / name).stat().st_size,
            "sha256": _sha256_file(source_lock_root / name),
        }
        for name in expected_lock_names
    }
    receipt = {
        "schema_version": "flow_probe_r2_source_preflight_receipt_v1",
        "status": "pass",
        "host_role": "local_producer",
        "params_sha256": _sha256_file(parameters_path),
        "code_commit": execution_code_lock.code_commit,
        "python_version": execution_code_lock.python_version,
        "pyarrow_version": execution_code_lock.pyarrow_version,
        "required_free_bytes": required_free_bytes,
        "available_bytes": available_bytes,
        "source_lock_root": str(source_lock_root),
        "lock_artifacts": lock_artifacts,
        "genis_archive": source_lock.genis.summary_dict(),
        "extractor_evidence": extractor_status,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    _write_stable_file(receipt_path, _canonical_json_bytes(receipt) + b"\n")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="R2 正式源锁与执行代码锁")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--params", required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command != "preflight":
        raise R2ProtocolContractError(f"未知命令：{args.command}")
    receipt = run_formal_source_preflight(Path(args.params))
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
