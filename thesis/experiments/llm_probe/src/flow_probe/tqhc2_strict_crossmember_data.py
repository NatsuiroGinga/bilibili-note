"""TQH-C2 v1.2.0 严格跨成员 Q0 原始 ZIP 数据接口。"""

from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq


class StrictCrossMemberDataError(RuntimeError):
    """表示原始输入、模式、连接、划分或目标隔离合同被破坏。"""


FEATURE_FIELDS = (
    "duration",
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "resp_pkts",
    "orig_ip_bytes",
    "resp_ip_bytes",
)
KEY_FIELDS = ("capture_id", "uid")
FEATURE_READ_FIELDS = (*KEY_FIELDS, *FEATURE_FIELDS, "interval_s", "jitter_pct", "label_raw", "y")
MEMBERS = ("A", "B", "C", "D")
SOURCE_MEMBERS = ("A", "B", "D")
INTERVALS = (30, 300, 1800, 3600)
JITTERS = (0, 30, 70)
CONDITION_KEYS = tuple(f"{interval}|{jitter}" for interval in INTERVALS for jitter in JITTERS)
SPLIT_DOMAIN = "tqh-c2-v1.2.0|seed=42|source-condition-split-v1|"
SCHEMA_VERSION = "tqhc2-strict-crossmember-raw-zip-v1"

EXPECTED_INPUTS = {
    "TQH-C2_features_v110.zip": {
        "bytes": 12_082_324,
        "sha256": "c68ab96cd429bf2b999be9d1b6467cf9860b7292e9fc3ead5e79680215723617",
    },
    "TQH-C2_labels_v110.zip": {
        "bytes": 31_023_638,
        "sha256": "9a76cf80d1e9b920b3758df8e8c117da0ee0df6fa5dd81a8c7bb53c9d388ef58",
    },
    "TQH-C2_features_D.zip": {
        "bytes": 1_222_048,
        "sha256": "5f1c6c26329f2d68079514b3cfc926931f4fcfe34284862b2681bf213d11a412",
    },
    "TQH-C2_labels_D.zip": {
        "bytes": 791_480,
        "sha256": "b91e9ebe36a94cf8ffc5b4209a2670443e1e0b45b0215147f20487f60f1777e6",
    },
    "README_v120.md": {
        "bytes": None,
        "sha256": "aa0dd75211670ca87b17d0097a39f52bca0aa849deb494600b20843f182f23f5",
    },
}

_ABC_LABEL_MEMBER = re.compile(
    r"^[ABC]/[ABC]_i(?:30|300|1800|3600)_j(?:0|30|70)/"
    r"(?:conn\.log|dns\.log|files\.log|gate\.json|http\.log|ja4ssh\.log|"
    r"labeled\.jsonl|labeled\.jsonl\.counts\.json|manifest\.json|ntp\.log|"
    r"quic\.log|ssh\.log|ssl\.log|weird\.log)$"
)


@dataclass(frozen=True)
class CaptureDescriptor:
    """仅由 ZIP 中央目录推导的捕获描述，不读取捕获内容。"""

    capture_key: str
    member: str
    interval_s: int
    jitter_pct: int
    condition_key: str
    role: str
    fold: int | None
    feature_archive: str
    feature_member: str
    label_archive: str
    label_member: str


@dataclass
class CaptureBatch:
    """只驻留内存的完整捕获。"""

    descriptor: CaptureDescriptor
    x: np.ndarray
    y: np.ndarray
    label_raw: np.ndarray
    uids: np.ndarray

    @property
    def row_count(self) -> int:
        return int(self.y.size)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _capture_key(member: str, interval: int, jitter: int) -> str:
    return f"{member}_i{interval}_j{jitter}"


def condition_assignment() -> dict[str, tuple[str, int | None]]:
    ranked = sorted(
        CONDITION_KEYS,
        key=lambda key: hashlib.sha256(f"{SPLIT_DOMAIN}{key}".encode()).hexdigest(),
    )
    assignment: dict[str, tuple[str, int | None]] = {}
    for rank, key in enumerate(ranked):
        assignment[key] = (
            ("source_train", rank % 4) if rank < 8 else ("source_calibration", None)
        )
    return assignment


def role_digest() -> str:
    assignment = condition_assignment()
    ordered = [f"{key}|{assignment[key][0]}|{assignment[key][1]}" for key in sorted(assignment)]
    return hashlib.sha256("\n".join(ordered).encode()).hexdigest()


def _expected_feature_members(prefix: str, members: Sequence[str]) -> set[str]:
    expected = {f"{prefix}/"}
    for member in members:
        expected.add(f"{prefix}/testbed_{member}.parquet")
        for interval in INTERVALS:
            for jitter in JITTERS:
                expected.add(f"{prefix}/{_capture_key(member, interval, jitter)}.parquet")
    return expected


def _validate_archive_members(filename: str, names: Sequence[str]) -> dict[str, Any]:
    actual = set(names)
    if len(actual) != len(names):
        raise StrictCrossMemberDataError(f"ZIP 中央目录含重复成员：{filename}")
    if filename == "TQH-C2_features_v110.zip":
        expected = _expected_feature_members("features", ("A", "B", "C"))
        if actual != expected:
            raise StrictCrossMemberDataError(f"A/B/C 特征 ZIP 成员白名单不匹配：{filename}")
    elif filename == "TQH-C2_features_D.zip":
        expected = _expected_feature_members("features_D", ("D",))
        if actual != expected:
            raise StrictCrossMemberDataError(f"D 特征 ZIP 成员白名单不匹配：{filename}")
    elif filename == "TQH-C2_labels_D.zip":
        expected = {
            f"{_capture_key('D', interval, jitter)}/{leaf}"
            for interval in INTERVALS
            for jitter in JITTERS
            for leaf in ("labeled.jsonl", "manifest.json")
        }
        if actual != expected:
            raise StrictCrossMemberDataError(f"D 标签 ZIP 成员白名单不匹配：{filename}")
    elif filename == "TQH-C2_labels_v110.zip":
        labeled = set()
        for name in names:
            if name.endswith("/"):
                if not re.fullmatch(
                    r"[ABC]/|[ABC]/[ABC]_i(?:30|300|1800|3600)_j(?:0|30|70)/", name
                ):
                    raise StrictCrossMemberDataError(f"A/B/C 标签 ZIP 出现非白名单目录：{name}")
                continue
            if not _ABC_LABEL_MEMBER.fullmatch(name):
                raise StrictCrossMemberDataError(f"A/B/C 标签 ZIP 出现非白名单成员：{name}")
            if name.endswith("/labeled.jsonl"):
                labeled.add(name)
        expected_labeled = {
            f"{member}/{_capture_key(member, interval, jitter)}/labeled.jsonl"
            for member in ("A", "B", "C")
            for interval in INTERVALS
            for jitter in JITTERS
        }
        if labeled != expected_labeled:
            raise StrictCrossMemberDataError("A/B/C 标签 ZIP 的逐捕获标签清单不完整")
    else:
        raise StrictCrossMemberDataError(f"未注册的 ZIP 输入：{filename}")
    return {
        "member_count": len(names),
        "member_names_sha256": canonical_sha256(sorted(names)),
    }


def audit_inputs(raw_root: Path) -> dict[str, Any]:
    files: dict[str, Any] = {}
    for filename, expected in EXPECTED_INPUTS.items():
        path = raw_root / filename
        if not path.is_file():
            raise StrictCrossMemberDataError(f"缺少受控输入：{path}")
        size = path.stat().st_size
        if expected["bytes"] is not None and size != expected["bytes"]:
            raise StrictCrossMemberDataError(f"输入字节数不匹配：{filename}")
        digest = sha256_file(path)
        if digest != expected["sha256"]:
            raise StrictCrossMemberDataError(f"输入 SHA-256 不匹配：{filename}")
        receipt: dict[str, Any] = {"bytes": size, "sha256": digest}
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                receipt.update(_validate_archive_members(filename, names))
                failed_member = archive.testzip()
                if failed_member is not None:
                    raise StrictCrossMemberDataError(
                        f"ZIP CRC 校验失败：{filename}：{failed_member}"
                    )
                receipt["crc_passed"] = True
        files[filename] = receipt
    return {
        "schema_version": "tqhc2-strict-crossmember-input-receipt-v1",
        "data_schema_version": SCHEMA_VERSION,
        "files": files,
        "feature_fields": list(FEATURE_FIELDS),
        "feature_field_count": len(FEATURE_FIELDS),
        "capture_count": 48,
        "role_rule": "source-condition-split-v1",
        "role_digest_sha256": role_digest(),
        "aggregated_parquet_read": False,
    }


def descriptors() -> tuple[CaptureDescriptor, ...]:
    assignment = condition_assignment()
    result = []
    for member in MEMBERS:
        for interval in INTERVALS:
            for jitter in JITTERS:
                capture_key = _capture_key(member, interval, jitter)
                condition_key = f"{interval}|{jitter}"
                if member == "C":
                    role, fold = "target_development_once", None
                else:
                    role, fold = assignment[condition_key]
                if member == "D":
                    feature_archive = "TQH-C2_features_D.zip"
                    feature_member = f"features_D/{capture_key}.parquet"
                    label_archive = "TQH-C2_labels_D.zip"
                    label_member = f"{capture_key}/labeled.jsonl"
                else:
                    feature_archive = "TQH-C2_features_v110.zip"
                    feature_member = f"features/{capture_key}.parquet"
                    label_archive = "TQH-C2_labels_v110.zip"
                    label_member = f"{member}/{capture_key}/labeled.jsonl"
                result.append(
                    CaptureDescriptor(
                        capture_key=capture_key,
                        member=member,
                        interval_s=interval,
                        jitter_pct=jitter,
                        condition_key=condition_key,
                        role=role,
                        fold=fold,
                        feature_archive=feature_archive,
                        feature_member=feature_member,
                        label_archive=label_archive,
                        label_member=label_member,
                    )
                )
    return tuple(result)


class StrictCrossMemberLoader:
    """强制源侧与目标一次性评价隔离的只读加载器。"""

    def __init__(self, raw_root: Path) -> None:
        self.raw_root = raw_root.resolve()
        self._target_session_open = False
        self._target_session_closed = False
        self._target_opened: set[str] = set()
        self.c_read_count = 0

    def source_captures(
        self, members: Sequence[str], role: str
    ) -> Iterator[CaptureBatch]:
        if role not in {"source_train", "source_calibration"}:
            raise StrictCrossMemberDataError(f"非法源角色：{role}")
        requested = tuple(members)
        if not requested or any(member not in SOURCE_MEMBERS for member in requested):
            raise StrictCrossMemberDataError("源加载器只允许 A、B、D")
        if self.c_read_count != 0 or self._target_session_open or self._target_session_closed:
            raise StrictCrossMemberDataError("目标会话开始后禁止回到源侧加载")
        for descriptor in descriptors():
            if descriptor.member in requested and descriptor.role == role:
                yield self._read_capture(descriptor, allow_target=False)

    def target_once(self) -> Iterator[CaptureBatch]:
        if self._target_session_open or self._target_session_closed or self.c_read_count != 0:
            raise StrictCrossMemberDataError("C 目标评价会话只能创建一次")
        self._target_session_open = True
        try:
            target_descriptors = [item for item in descriptors() if item.member == "C"]
            for descriptor in target_descriptors:
                if descriptor.capture_key in self._target_opened:
                    raise StrictCrossMemberDataError("同一 C 捕获被重复打开")
                self._target_opened.add(descriptor.capture_key)
                yield self._read_capture(descriptor, allow_target=True)
            if len(self._target_opened) != 12:
                raise StrictCrossMemberDataError("C 评价未恰好覆盖 12 个完整捕获")
            self.c_read_count = 1
        finally:
            self._target_session_open = False
            self._target_session_closed = True

    def _read_capture(
        self, descriptor: CaptureDescriptor, *, allow_target: bool
    ) -> CaptureBatch:
        if descriptor.member == "C" and not allow_target:
            raise StrictCrossMemberDataError("冻结前硬拒绝打开 C 捕获")
        if descriptor.member != "C" and allow_target:
            raise StrictCrossMemberDataError("目标会话不得读取源成员")
        feature_path = self.raw_root / descriptor.feature_archive
        label_path = self.raw_root / descriptor.label_archive
        with zipfile.ZipFile(feature_path) as feature_zip:
            if descriptor.feature_member not in feature_zip.namelist():
                raise StrictCrossMemberDataError(f"缺少逐捕获特征：{descriptor.capture_key}")
            payload = feature_zip.read(descriptor.feature_member)
        table = pq.read_table(io.BytesIO(payload), columns=list(FEATURE_READ_FIELDS))
        frame = table.to_pandas()
        if tuple(frame.columns) != FEATURE_READ_FIELDS:
            raise StrictCrossMemberDataError(f"七字段读取模式漂移：{descriptor.capture_key}")
        if frame.empty:
            raise StrictCrossMemberDataError(f"捕获为空：{descriptor.capture_key}")
        if frame[list(KEY_FIELDS)].isna().any().any():
            raise StrictCrossMemberDataError(f"连接主键为空：{descriptor.capture_key}")
        if frame.duplicated(list(KEY_FIELDS)).any():
            raise StrictCrossMemberDataError(f"特征主键重复：{descriptor.capture_key}")
        if set(frame["interval_s"].astype(int)) != {descriptor.interval_s} or set(
            frame["jitter_pct"].astype(int)
        ) != {descriptor.jitter_pct}:
            raise StrictCrossMemberDataError(f"捕获条件字段不一致：{descriptor.capture_key}")
        labels = self._read_labels(label_path, descriptor)
        keys = list(zip(frame["capture_id"].astype(str), frame["uid"].astype(str), strict=True))
        if len(set(keys)) != len(keys) or set(keys) != set(labels):
            raise StrictCrossMemberDataError(
                f"标签连接不是一对一完整连接：{descriptor.capture_key}"
            )
        joined_raw = np.asarray([labels[key] for key in keys], dtype=object)
        feature_raw = frame["label_raw"].astype(str).to_numpy(dtype=object)
        expected_y = (joined_raw == "malicious_c2").astype(np.uint8)
        feature_y = frame["y"].to_numpy(dtype=np.uint8)
        if not np.array_equal(joined_raw, feature_raw) or not np.array_equal(expected_y, feature_y):
            raise StrictCrossMemberDataError(f"特征与标签真值不一致：{descriptor.capture_key}")
        values = frame[list(FEATURE_FIELDS)].to_numpy(dtype=np.float32, copy=True)
        if not np.isfinite(values).all() or np.any(values < 0):
            raise StrictCrossMemberDataError(f"七字段含非有限或负值：{descriptor.capture_key}")
        return CaptureBatch(
            descriptor=descriptor,
            x=values,
            y=expected_y,
            label_raw=joined_raw,
            uids=frame["uid"].astype(str).to_numpy(dtype=object),
        )

    @staticmethod
    def _read_labels(
        label_path: Path, descriptor: CaptureDescriptor
    ) -> dict[tuple[str, str], str]:
        labels: dict[tuple[str, str], str] = {}
        with zipfile.ZipFile(label_path) as label_zip, label_zip.open(
            descriptor.label_member
        ) as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                try:
                    row = json.loads(raw_line)
                    capture_id = str(row["capture_id"])
                    uid = str(row["uid"])
                    label_raw = str(row["label"])
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    raise StrictCrossMemberDataError(
                        f"标签 JSONL 非法：{descriptor.capture_key} 行 {line_number}"
                    ) from error
                key = (capture_id, uid)
                if key in labels:
                    raise StrictCrossMemberDataError(f"标签主键重复：{descriptor.capture_key}")
                labels[key] = label_raw
        if not labels:
            raise StrictCrossMemberDataError(f"标签捕获为空：{descriptor.capture_key}")
        return labels


def aggregate_receipt(captures: Sequence[CaptureBatch]) -> dict[str, Any]:
    aggregate: dict[str, dict[str, dict[str, int]]] = {}
    for capture in captures:
        member = capture.descriptor.member
        role = capture.descriptor.role
        cell = aggregate.setdefault(member, {}).setdefault(
            role,
            {"capture_count": 0, "row_count": 0, "positive_count": 0, "negative_count": 0},
        )
        cell["capture_count"] += 1
        cell["row_count"] += capture.row_count
        cell["positive_count"] += int(np.count_nonzero(capture.y == 1))
        cell["negative_count"] += int(np.count_nonzero(capture.y == 0))
    return {
        "schema_version": "tqhc2-strict-crossmember-split-aggregate-v1",
        "role_rule": "source-condition-split-v1",
        "role_digest_sha256": role_digest(),
        "aggregate": aggregate,
        "condition_role_details_persisted": False,
        "per_sample_manifest_persisted": False,
    }


def assert_source_support(captures: Sequence[CaptureBatch], members: Sequence[str]) -> None:
    for member in members:
        for role, minimum_capture, minimum_positive, minimum_negative in (
            ("source_train", 8, 100, 5_000),
            ("source_calibration", 4, 25, 2_000),
        ):
            selected = [
                capture
                for capture in captures
                if capture.descriptor.member == member and capture.descriptor.role == role
            ]
            positive = sum(int(np.count_nonzero(capture.y == 1)) for capture in selected)
            negative = sum(int(np.count_nonzero(capture.y == 0)) for capture in selected)
            if (
                len(selected) != minimum_capture
                or positive < minimum_positive
                or negative < minimum_negative
            ):
                raise StrictCrossMemberDataError(
                    f"{member} 的 {role} 支持量不足："
                    f"捕获={len(selected)}，正={positive}，负={negative}"
                )


def concatenate(captures: Sequence[CaptureBatch]) -> dict[str, np.ndarray]:
    if not captures:
        raise StrictCrossMemberDataError("不能拼接空捕获集合")
    return {
        "x": np.concatenate([capture.x for capture in captures], axis=0),
        "y": np.concatenate([capture.y for capture in captures], axis=0),
        "member": np.concatenate(
            [
                np.full(capture.row_count, capture.descriptor.member, dtype=object)
                for capture in captures
            ]
        ),
        "capture": np.concatenate(
            [
                np.full(capture.row_count, capture.descriptor.capture_key, dtype=object)
                for capture in captures
            ]
        ),
        "fold": np.concatenate(
            [
                np.full(
                    capture.row_count,
                    -1 if capture.descriptor.fold is None else capture.descriptor.fold,
                    dtype=np.int8,
                )
                for capture in captures
            ]
        ),
        "label_raw": np.concatenate([capture.label_raw for capture in captures]),
        "uid": np.concatenate([capture.uids for capture in captures]),
    }
