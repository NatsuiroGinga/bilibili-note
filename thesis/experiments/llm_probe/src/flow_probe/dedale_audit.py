"""DEDALE orange_dmz 标签与跨工具关联审计。"""

from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

_DATE_PATTERN = re.compile(
    r"^(?P<base>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\.(?P<fraction>\d{1,9}))?$"
)
_PROTOCOLS = {"1": "icmp", "6": "tcp", "17": "udp"}
_VALID_LABELS = frozenset({"0", "1", "2"})
_DAY_PATH_PATTERN = re.compile(r"(?:^|/)D(?P<day>\d+)_(?P<date>\d{4}-\d{2}-\d{2})_")
_DATASET_START = dt.datetime(2024, 12, 23, tzinfo=dt.timezone.utc)
_TEST_START = dt.datetime(2025, 1, 6, tzinfo=dt.timezone.utc)
_ATTACK_END = dt.datetime(2025, 1, 14, tzinfo=dt.timezone.utc)
_DATASET_END = dt.datetime(2025, 1, 20, tzinfo=dt.timezone.utc)
_REQUIRED_FIELDS = frozenset(
    {
        "date",
        "ts",
        "uid",
        "ip_src",
        "port_src",
        "ip_dst",
        "port_dst",
        "proto",
        "duration",
        "label",
        "step",
        "attack_step",
        "tactic",
        "technique",
        "comments",
    }
)


class DEDALEAuditError(ValueError):
    """DEDALE 输入不满足官方字段或时间协议。"""


def normalize_protocol(value: str) -> str:
    """统一 Zeek 文本协议和 CICFlowMeter 数字协议。"""
    normalized = str(value).strip().lower()
    return _PROTOCOLS.get(normalized, normalized)


def parse_utc_date(value: str) -> float:
    """把 DEDALE 的无时区纳秒文本按 UTC 解释为 Unix 时间。"""
    match = _DATE_PATTERN.fullmatch(str(value).strip())
    if match is None:
        raise DEDALEAuditError(f"UTC 时间无法解析：{value}")
    try:
        base = dt.datetime.strptime(match.group("base"), "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=dt.timezone.utc
        )
    except ValueError as error:
        raise DEDALEAuditError(f"UTC 时间无法解析：{value}") from error
    fraction = match.group("fraction") or ""
    return base.timestamp() + int(fraction or "0") / (10 ** len(fraction) if fraction else 1)


def classify_day(day_id: int) -> str:
    """按官方前两周校准、后两周测试协议划分日序。"""
    if 1 <= day_id <= 14:
        return "calibration"
    if 15 <= day_id <= 28:
        return "test"
    raise DEDALEAuditError(f"DEDALE 日序必须位于 D1 至 D28：{day_id}")


def validate_label(value: str) -> str:
    """保留官方 0、1、2 三类标签并拒绝其他值。"""
    label = str(value).strip()
    if label not in _VALID_LABELS:
        raise DEDALEAuditError(f"DEDALE 标签必须是 0、1 或 2：{value}")
    return label


def _normalize_port(value: str) -> str:
    text = str(value).strip()
    try:
        return str(int(float(text)))
    except ValueError:
        return text


@dataclass(frozen=True, slots=True)
class FlowIdentity:
    """规范化后的有向五元组。"""

    protocol: str
    src: str
    src_port: str
    dst: str
    dst_port: str

    @classmethod
    def from_values(
        cls,
        *,
        protocol: str,
        src: str,
        src_port: str,
        dst: str,
        dst_port: str,
    ) -> FlowIdentity:
        return cls(
            protocol=normalize_protocol(protocol),
            src=str(src).strip(),
            src_port=_normalize_port(src_port),
            dst=str(dst).strip(),
            dst_port=_normalize_port(dst_port),
        )

    def reverse(self) -> FlowIdentity:
        return FlowIdentity(
            protocol=self.protocol,
            src=self.dst,
            src_port=self.dst_port,
            dst=self.src,
            dst_port=self.src_port,
        )


@dataclass(frozen=True, slots=True)
class FlowRecord:
    """不保留 UID 的最小跨工具关联记录。"""

    source: str
    day_id: int
    start_ts: float
    end_ts: float
    identity: FlowIdentity
    label: str

    def __post_init__(self) -> None:
        classify_day(self.day_id)
        validate_label(self.label)
        if not math.isfinite(self.start_ts) or not math.isfinite(self.end_ts):
            raise DEDALEAuditError("流起止时间必须是有限数")
        if self.end_ts < self.start_ts:
            raise DEDALEAuditError("流结束时间不能早于起始时间")


@dataclass(frozen=True, slots=True)
class AssociationDecision:
    """单条 CICFlowMeter 记录的只读关联裁决。"""

    status: str
    direction: str | None
    basis: str | None
    candidate_count: int
    start_delta_seconds: float | None
    label_conflict: bool


@dataclass(frozen=True, slots=True)
class _FlowBucket:
    records: tuple[FlowRecord, ...]
    starts: tuple[float, ...]
    prefix_max_end: tuple[float, ...]


FlowIndex = dict[FlowIdentity, _FlowBucket]


def build_flow_index(records: Iterable[FlowRecord]) -> FlowIndex:
    """按有向五元组建立按起始时间排序的 Zeek 候选索引。"""
    grouped: defaultdict[FlowIdentity, list[FlowRecord]] = defaultdict(list)
    for record in records:
        grouped[record.identity].append(record)
    index: FlowIndex = {}
    for identity, values in grouped.items():
        ordered = tuple(sorted(values, key=lambda item: (item.start_ts, item.end_ts)))
        prefix_max_end: list[float] = []
        current_max = -math.inf
        for record in ordered:
            current_max = max(current_max, record.end_ts)
            prefix_max_end.append(current_max)
        index[identity] = _FlowBucket(
            records=ordered,
            starts=tuple(record.start_ts for record in ordered),
            prefix_max_end=tuple(prefix_max_end),
        )
    return index


def _intervals_overlap(left: FlowRecord, right: FlowRecord) -> bool:
    return max(left.start_ts, right.start_ts) <= min(left.end_ts, right.end_ts)


def _qualifying_candidates(
    record: FlowRecord,
    bucket: _FlowBucket | None,
    start_tolerance_seconds: float,
) -> list[FlowRecord]:
    if bucket is None:
        return []

    lower = bisect.bisect_left(bucket.starts, record.start_ts - start_tolerance_seconds)
    upper = bisect.bisect_right(bucket.starts, record.start_ts + start_tolerance_seconds)
    near_start = list(bucket.records[lower:upper])
    if near_start:
        return near_start

    overlap: list[FlowRecord] = []
    position = bisect.bisect_right(bucket.starts, record.end_ts) - 1
    while position >= 0:
        if bucket.prefix_max_end[position] < record.start_ts:
            break
        candidate = bucket.records[position]
        if _intervals_overlap(candidate, record):
            overlap.append(candidate)
        position -= 1
    return overlap


def _associate_record_with_candidate(
    record: FlowRecord,
    index: FlowIndex,
    start_tolerance_seconds: float,
) -> tuple[AssociationDecision, FlowRecord | None]:
    """用五元组与时间唯一性裁决关联，不修改任一侧标签。"""
    if not math.isfinite(start_tolerance_seconds) or start_tolerance_seconds < 0:
        raise DEDALEAuditError("起始时间容差必须是非负有限数")

    direction = "direct"
    candidates = _qualifying_candidates(
        record,
        index.get(record.identity),
        start_tolerance_seconds,
    )
    if not candidates:
        direction = "reverse"
        candidates = _qualifying_candidates(
            record,
            index.get(record.identity.reverse()),
            start_tolerance_seconds,
        )
    if not candidates:
        return (
            AssociationDecision(
                status="unmatched",
                direction=None,
                basis=None,
                candidate_count=0,
                start_delta_seconds=None,
                label_conflict=False,
            ),
            None,
        )
    if len(candidates) > 1:
        return (
            AssociationDecision(
                status="ambiguous",
                direction=direction,
                basis=None,
                candidate_count=len(candidates),
                start_delta_seconds=None,
                label_conflict=False,
            ),
            None,
        )

    candidate = candidates[0]
    start_delta = abs(candidate.start_ts - record.start_ts)
    basis = "start_tolerance" if start_delta <= start_tolerance_seconds else "interval_overlap"
    return (
        AssociationDecision(
            status="matched",
            direction=direction,
            basis=basis,
            candidate_count=1,
            start_delta_seconds=start_delta,
            label_conflict=candidate.label != record.label,
        ),
        candidate,
    )


def associate_record(
    record: FlowRecord,
    index: FlowIndex,
    start_tolerance_seconds: float,
) -> AssociationDecision:
    """返回公开裁决，不暴露或持久化匹配到的 Zeek 记录。"""
    decision, _candidate = _associate_record_with_candidate(
        record,
        index,
        start_tolerance_seconds,
    )
    return decision


def _stage_for_timestamp(timestamp: float) -> str:
    if _DATASET_START.timestamp() <= timestamp < _TEST_START.timestamp():
        return "calibration"
    if _TEST_START.timestamp() <= timestamp < _DATASET_END.timestamp():
        return "test"
    return "outside_official_window"


def _event_signature(record: FlowRecord, row: dict[str, str]) -> tuple[object, ...]:
    return (
        round(record.start_ts, 6),
        record.identity,
        record.label,
        str(row["step"]).strip(),
        str(row["attack_step"]).strip(),
        str(row["tactic"]).strip(),
        str(row["technique"]).strip(),
        str(row["comments"]).strip(),
    )


@dataclass(slots=True)
class _SourceAudit:
    duration_unit: str
    file_count: int = 0
    row_count: int = 0
    label_rows: Counter[str] = field(default_factory=Counter)
    day_rows: Counter[int] = field(default_factory=Counter)
    stage_rows: Counter[str] = field(default_factory=Counter)
    directory_stage_rows: Counter[str] = field(default_factory=Counter)
    headers: set[tuple[str, ...]] = field(default_factory=set)
    nonbenign_events: list[dict[str, object]] = field(default_factory=list)
    event_signatures: Counter[tuple[object, ...]] = field(default_factory=Counter)
    utc_mismatch_count: int = 0
    nonbenign_calibration_count: int = 0
    nonbenign_outside_attack_envelope_count: int = 0
    row_date_outside_directory_day_count: int = 0
    crosses_calibration_test_boundary_count: int = 0
    outside_official_window_count: int = 0
    duration_missing_count: int = 0
    time_min: float = math.inf
    time_max: float = -math.inf

    def add(
        self,
        *,
        day_id: int,
        declared_date: dt.date,
        record: FlowRecord,
        row: dict[str, str],
        duration_missing: bool,
    ) -> None:
        stage = _stage_for_timestamp(record.start_ts)
        self.row_count += 1
        self.label_rows[record.label] += 1
        self.day_rows[day_id] += 1
        self.stage_rows[stage] += 1
        self.directory_stage_rows[classify_day(day_id)] += 1
        self.time_min = min(self.time_min, record.start_ts)
        self.time_max = max(self.time_max, record.start_ts)
        self.duration_missing_count += duration_missing
        self.outside_official_window_count += stage == "outside_official_window"
        self.row_date_outside_directory_day_count += (
            dt.datetime.fromtimestamp(record.start_ts, tz=dt.timezone.utc).date() != declared_date
        )
        self.crosses_calibration_test_boundary_count += (
            record.start_ts < _TEST_START.timestamp() <= record.end_ts
        )

        if record.label == "0":
            return
        self.nonbenign_calibration_count += stage == "calibration"
        self.nonbenign_outside_attack_envelope_count += not (
            _TEST_START.timestamp() <= record.start_ts < _ATTACK_END.timestamp()
        )
        self.event_signatures[_event_signature(record, row)] += 1
        self.nonbenign_events.append(
            {
                "attack_step": str(row["attack_step"]).strip(),
                "comments": str(row["comments"]).strip(),
                "date": str(row["date"]).strip(),
                "label": record.label,
                "protocol": record.identity.protocol,
                "step": str(row["step"]).strip(),
                "tactic": str(row["tactic"]).strip(),
                "technique": str(row["technique"]).strip(),
                "ts": record.start_ts,
            }
        )

    def as_dict(self) -> dict[str, object]:
        header = next(iter(self.headers), ())
        return {
            "crosses_calibration_test_boundary_count": (
                self.crosses_calibration_test_boundary_count
            ),
            "day_rows": dict(sorted(self.day_rows.items())),
            "directory_stage_rows": dict(sorted(self.directory_stage_rows.items())),
            "duration_missing_count": self.duration_missing_count,
            "duration_unit": self.duration_unit,
            "field_names": list(header),
            "field_variant_count": len(self.headers),
            "file_count": self.file_count,
            "label_rows": dict(sorted(self.label_rows.items())),
            "nonbenign_calibration_count": self.nonbenign_calibration_count,
            "nonbenign_events": self.nonbenign_events,
            "nonbenign_outside_attack_envelope_count": (
                self.nonbenign_outside_attack_envelope_count
            ),
            "outside_official_window_count": self.outside_official_window_count,
            "row_count": self.row_count,
            "row_date_outside_directory_day_count": (self.row_date_outside_directory_day_count),
            "stage_rows": dict(sorted(self.stage_rows.items())),
            "time_range": {
                "max_ts": self.time_max,
                "min_ts": self.time_min,
            },
            "utc_mismatch_count": self.utc_mismatch_count,
        }


def _parse_day_path(value: str) -> tuple[int, dt.date]:
    normalized = str(value).replace("\\", "/")
    match = _DAY_PATH_PATTERN.search(normalized)
    if match is None:
        raise DEDALEAuditError(f"无法从路径解析 DEDALE 日序：{value}")
    day_id = int(match.group("day"))
    classify_day(day_id)
    declared_date = dt.date.fromisoformat(match.group("date"))
    expected_date = (_DATASET_START + dt.timedelta(days=day_id - 1)).date()
    if declared_date != expected_date:
        raise DEDALEAuditError(f"DEDALE 日序与目录日期不一致：D{day_id} 应为 {expected_date}")
    return day_id, declared_date


def _validate_header(
    fieldnames: list[str] | None,
    *,
    source: str,
    location: str,
) -> tuple[str, ...]:
    header = tuple(fieldnames or ())
    missing = sorted(_REQUIRED_FIELDS.difference(header))
    if missing:
        raise DEDALEAuditError(f"{source} 缺少字段 {', '.join(missing)}：{location}")
    return header


def _parse_duration(value: str, *, source: str, location: str) -> tuple[float, bool]:
    text = str(value).strip()
    if text in {"", "-"}:
        return 0.0, True
    try:
        duration = float(text)
    except ValueError as error:
        raise DEDALEAuditError(f"{source} 时长无法解析：{location}") from error
    if not math.isfinite(duration) or duration < 0:
        raise DEDALEAuditError(f"{source} 时长必须是非负有限数：{location}")
    if source == "cicflowmeter":
        duration /= 1_000_000
    return duration, False


def _record_from_row(
    row: dict[str, str],
    *,
    source: str,
    day_id: int,
    location: str,
) -> tuple[FlowRecord, bool]:
    try:
        start_ts = float(str(row["ts"]).strip())
    except ValueError as error:
        raise DEDALEAuditError(f"{source} 时间戳无法解析：{location}") from error
    if not math.isfinite(start_ts):
        raise DEDALEAuditError(f"{source} 时间戳必须是有限数：{location}")
    date_ts = parse_utc_date(row["date"])
    if abs(date_ts - start_ts) > 1e-5:
        raise DEDALEAuditError(f"{source} 的 date 与 ts 不是同一 UTC 时间：{location}")
    duration, duration_missing = _parse_duration(row["duration"], source=source, location=location)
    record = FlowRecord(
        source=source,
        day_id=day_id,
        start_ts=start_ts,
        end_ts=start_ts + duration,
        identity=FlowIdentity.from_values(
            protocol=row["proto"],
            src=row["ip_src"],
            src_port=row["port_src"],
            dst=row["ip_dst"],
            dst_port=row["port_dst"],
        ),
        label=validate_label(row["label"]),
    )
    return record, duration_missing


def _validate_day_coverage(day_locations: dict[int, str], source: str) -> None:
    expected = set(range(1, 29))
    actual = set(day_locations)
    if actual != expected:
        missing = ", ".join(f"D{day}" for day in sorted(expected - actual)) or "无"
        extra = ", ".join(f"D{day}" for day in sorted(actual - expected)) or "无"
        raise DEDALEAuditError(f"{source} 日序不完整，缺少：{missing}；额外：{extra}")


def _zeek_paths(zeek_dir: Path) -> list[tuple[int, dt.date, Path]]:
    paths = list(Path(zeek_dir).glob("D*_*/conn_labeled.csv"))
    day_locations: dict[int, str] = {}
    parsed: list[tuple[int, dt.date, Path]] = []
    for path in paths:
        day_id, declared_date = _parse_day_path(str(path))
        if day_id in day_locations:
            raise DEDALEAuditError(f"Zeek 日序重复：D{day_id}")
        day_locations[day_id] = str(path)
        parsed.append((day_id, declared_date, path))
    _validate_day_coverage(day_locations, "Zeek")
    return sorted(parsed)


def _cic_members(archive: zipfile.ZipFile) -> list[tuple[int, dt.date, str]]:
    names = [name for name in archive.namelist() if name.endswith("_Flow_labeled.csv")]
    day_locations: dict[int, str] = {}
    parsed: list[tuple[int, dt.date, str]] = []
    for name in names:
        day_id, declared_date = _parse_day_path(name)
        if day_id in day_locations:
            raise DEDALEAuditError(f"CICFlowMeter 日序重复：D{day_id}")
        day_locations[day_id] = name
        parsed.append((day_id, declared_date, name))
    _validate_day_coverage(day_locations, "CICFlowMeter")
    return sorted(parsed)


def _read_zeek(zeek_dir: Path) -> tuple[list[FlowRecord], _SourceAudit]:
    records: list[FlowRecord] = []
    audit = _SourceAudit(duration_unit="seconds")
    for day_id, declared_date, path in _zeek_paths(zeek_dir):
        audit.file_count += 1
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source, delimiter=";")
            audit.headers.add(
                _validate_header(
                    reader.fieldnames,
                    source="Zeek",
                    location=str(path),
                )
            )
            for row_number, row in enumerate(reader, start=2):
                record, duration_missing = _record_from_row(
                    row,
                    source="zeek",
                    day_id=day_id,
                    location=f"{path}:{row_number}",
                )
                records.append(record)
                audit.add(
                    day_id=day_id,
                    declared_date=declared_date,
                    record=record,
                    row=row,
                    duration_missing=duration_missing,
                )
    if len(audit.headers) != 1:
        raise DEDALEAuditError("Zeek 字段在 28 天内发生漂移")
    return records, audit


def _read_cic_and_associate(
    cic_zip: Path,
    index: FlowIndex,
    start_tolerance_seconds: float,
) -> tuple[_SourceAudit, dict[str, object]]:
    audit = _SourceAudit(duration_unit="microseconds")
    statuses: Counter[str] = Counter()
    directions: Counter[str] = Counter()
    bases: Counter[str] = Counter()
    target_counts: Counter[int] = Counter()
    label_conflicts = 0
    with zipfile.ZipFile(cic_zip) as archive:
        members = _cic_members(archive)
        for day_id, declared_date, member in members:
            audit.file_count += 1
            with archive.open(member) as raw_source:
                source = io.TextIOWrapper(raw_source, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(source)
                audit.headers.add(
                    _validate_header(
                        reader.fieldnames,
                        source="CICFlowMeter",
                        location=member,
                    )
                )
                for row_number, row in enumerate(reader, start=2):
                    record, duration_missing = _record_from_row(
                        row,
                        source="cicflowmeter",
                        day_id=day_id,
                        location=f"{member}:{row_number}",
                    )
                    audit.add(
                        day_id=day_id,
                        declared_date=declared_date,
                        record=record,
                        row=row,
                        duration_missing=duration_missing,
                    )
                    decision, candidate = _associate_record_with_candidate(
                        record,
                        index,
                        start_tolerance_seconds,
                    )
                    statuses[decision.status] += 1
                    if decision.status == "matched" and decision.direction is not None:
                        directions[decision.direction] += 1
                    if decision.status == "matched" and decision.basis is not None:
                        bases[decision.basis] += 1
                    label_conflicts += decision.label_conflict
                    if candidate is not None:
                        target_counts[id(candidate)] += 1
    if len(audit.headers) != 1:
        raise DEDALEAuditError("CICFlowMeter 字段在 28 天内发生漂移")
    if sum(statuses.values()) != audit.row_count:
        raise AssertionError("关联分类总数与 CICFlowMeter 行数不一致")
    matched = statuses["matched"]
    target_reuse = tuple(target_counts.values())
    association = {
        "ambiguous": statuses["ambiguous"],
        "cic_records_on_reused_zeek_targets": sum(count for count in target_reuse if count > 1),
        "direct": directions["direct"],
        "interval_overlap": bases["interval_overlap"],
        "label_conflicts": label_conflicts,
        "matched": matched,
        "matched_unique_zeek_records": len(target_counts),
        "match_rate": matched / audit.row_count if audit.row_count else 0.0,
        "max_cic_records_per_zeek_target": max(target_reuse, default=0),
        "one_to_one_cic_records": sum(count == 1 for count in target_reuse),
        "reverse": directions["reverse"],
        "start_tolerance": bases["start_tolerance"],
        "start_tolerance_seconds": start_tolerance_seconds,
        "total_cicflowmeter_rows": audit.row_count,
        "unmatched": statuses["unmatched"],
        "zeek_targets_reused": sum(count > 1 for count in target_reuse),
    }
    return audit, association


def audit_dedale(
    zeek_dir: Path,
    cic_zip: Path,
    start_tolerance_seconds: float,
) -> dict[str, object]:
    """只读审计 DEDALE 两类 orange_dmz 流并汇总关联覆盖范围。"""
    zeek_dir = Path(zeek_dir)
    cic_zip = Path(cic_zip)
    if not zeek_dir.is_dir():
        raise DEDALEAuditError(f"Zeek 目录不存在：{zeek_dir}")
    if not cic_zip.is_file():
        raise DEDALEAuditError(f"CICFlowMeter ZIP 不存在：{cic_zip}")

    zeek_records, zeek_audit = _read_zeek(zeek_dir)
    cic_audit, association = _read_cic_and_associate(
        cic_zip,
        build_flow_index(zeek_records),
        start_tolerance_seconds,
    )
    for source_name, source_audit in (
        ("Zeek", zeek_audit),
        ("CICFlowMeter", cic_audit),
    ):
        if source_audit.nonbenign_calibration_count:
            raise DEDALEAuditError(f"{source_name} 前两周出现非良性标签")
        if source_audit.nonbenign_outside_attack_envelope_count:
            raise DEDALEAuditError(f"{source_name} 非良性标签越出官方八天攻击包络")

    shared_events = sum((zeek_audit.event_signatures & cic_audit.event_signatures).values())
    zeek_only_events = sum((zeek_audit.event_signatures - cic_audit.event_signatures).values())
    cic_only_events = sum((cic_audit.event_signatures - zeek_audit.event_signatures).values())
    return {
        "association": association,
        "nonbenign_event_alignment": {
            "cicflowmeter_only": cic_only_events,
            "exact_shared": shared_events,
            "zeek_only": zeek_only_events,
        },
        "privacy": {
            "addresses_written": False,
            "inferred_labels_written": False,
            "ports_written": False,
            "raw_uids_written": False,
        },
        "schema_version": "dedale_orange_dmz_audit_v1",
        "sources": {
            "cicflowmeter": cic_audit.as_dict(),
            "zeek": zeek_audit.as_dict(),
        },
        "temporal_protocol": {
            "attack_end_exclusive": _ATTACK_END.isoformat(),
            "attack_start_inclusive": _TEST_START.isoformat(),
            "calibration_days": [1, 14],
            "dataset_end_exclusive": _DATASET_END.isoformat(),
            "dataset_start_inclusive": _DATASET_START.isoformat(),
            "test_days": [15, 28],
            "timezone": "UTC",
        },
    }


def _file_hashes(path: Path) -> tuple[str, str]:
    md5 = hashlib.md5(usedforsecurity=False)
    sha256 = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def build_input_manifest(zeek_dir: Path, cic_zip: Path) -> dict[str, object]:
    """生成可复核但不含连接级内容的输入文件清单。"""
    zeek_files: list[dict[str, object]] = []
    for day_id, _declared_date, path in _zeek_paths(Path(zeek_dir)):
        md5, sha256 = _file_hashes(path)
        zeek_files.append(
            {
                "day_id": day_id,
                "md5": md5,
                "path": str(path),
                "sha256": sha256,
                "size_bytes": path.stat().st_size,
            }
        )
    cic_zip = Path(cic_zip)
    md5, sha256 = _file_hashes(cic_zip)
    return {
        "cicflowmeter_zip": {
            "md5": md5,
            "path": str(cic_zip),
            "sha256": sha256,
            "size_bytes": cic_zip.stat().st_size,
        },
        "schema_version": "dedale_orange_dmz_input_manifest_v1",
        "zeek": {
            "file_count": len(zeek_files),
            "files": zeek_files,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 DEDALE orange_dmz 标签与跨工具关联")
    parser.add_argument("--zeek-dir", type=Path, required=True)
    parser.add_argument("--cic-zip", type=Path, required=True)
    parser.add_argument("--start-tolerance-seconds", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    for path in (args.output, args.manifest_output):
        if path.exists():
            raise DEDALEAuditError(f"拒绝覆盖已有审计制品：{path}")
    audit = audit_dedale(
        args.zeek_dir,
        args.cic_zip,
        start_tolerance_seconds=args.start_tolerance_seconds,
    )
    manifest = build_input_manifest(args.zeek_dir, args.cic_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
