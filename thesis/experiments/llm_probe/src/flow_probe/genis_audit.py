"""GeNIS 会话、时间和攻击子类的流式审计。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_FIELDS = (
    "FlowID",
    "StartTime",
    "LastTime",
    "BinaryLabel",
    "CategoryLabel",
    "SubCategoryLabel",
)


class GeNISAuditError(ValueError):
    """GeNIS 元数据不能满足正式划分审计要求。"""


@dataclass(slots=True)
class _SessionState:
    """只保留统计所需状态，不持久化原始会话标识。"""

    window_count: int
    first_label: str
    first_subtype: str
    start_min: float
    last_max: float
    labels: set[str] | None = None
    subtypes: set[str] | None = None

    def update(self, label: str, subtype: str, start: float, last: float) -> None:
        self.window_count += 1
        self.start_min = min(self.start_min, start)
        self.last_max = max(self.last_max, last)
        if label != self.first_label:
            if self.labels is None:
                self.labels = {self.first_label}
            self.labels.add(label)
        if subtype != self.first_subtype:
            if self.subtypes is None:
                self.subtypes = {self.first_subtype}
            self.subtypes.add(subtype)

    def label_values(self) -> tuple[str, ...]:
        if self.labels is None:
            return (self.first_label,)
        return tuple(sorted(self.labels))

    def subtype_values(self) -> tuple[str, ...]:
        if self.subtypes is None:
            return (self.first_subtype,)
        return tuple(sorted(self.subtypes))


@dataclass
class _TimeRange:
    start_min: float = field(default=math.inf)
    start_max: float = field(default=-math.inf)
    last_min: float = field(default=math.inf)
    last_max: float = field(default=-math.inf)

    def update(self, start: float, last: float) -> None:
        self.start_min = min(self.start_min, start)
        self.start_max = max(self.start_max, start)
        self.last_min = min(self.last_min, last)
        self.last_max = max(self.last_max, last)

    def as_dict(self) -> dict[str, float]:
        return {
            "last_max": self.last_max,
            "last_min": self.last_min,
            "start_max": self.start_max,
            "start_min": self.start_min,
        }


def _parse_timestamp(value: object, field_name: str, path: Path, row_number: int) -> float:
    try:
        timestamp = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise GeNISAuditError(f"时间戳无法解析：{path.name}:{row_number}:{field_name}") from error
    if not math.isfinite(timestamp):
        raise GeNISAuditError(f"时间戳不是有限数：{path.name}:{row_number}:{field_name}")
    return timestamp


def _session_key(source_index: int, flow_id: str) -> tuple[int, bytes]:
    digest = hashlib.blake2b(flow_id.encode("utf-8"), digest_size=16).digest()
    return source_index, digest


def _percentile_from_counts(counts: Counter[int] | Counter[float], percentile: float) -> float:
    total = sum(counts.values())
    target = max(1, math.ceil(total * percentile))
    cumulative = 0
    for value in sorted(counts):
        cumulative += counts[value]
        if cumulative >= target:
            return float(value)
    raise AssertionError("会话窗口分位数计算失败")


def audit_genis_paths(input_paths: list[Path]) -> dict[str, object]:
    """流式审计 GeNIS CSV，不输出原始会话、地址或端口。"""
    paths = sorted(Path(path) for path in input_paths)
    if not paths:
        raise GeNISAuditError("至少需要一个 GeNIS CSV")

    sessions: dict[tuple[int, bytes], _SessionState] = {}
    binary_label_rows: Counter[str] = Counter()
    subtype_rows: Counter[str] = Counter()
    time_range = _TimeRange()
    input_files: list[dict[str, object]] = []
    row_count = 0

    for source_index, path in enumerate(paths):
        file_rows = 0
        file_sessions = 0
        file_start_times: set[float] = set()
        file_time_range = _TimeRange()
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            columns = set(reader.fieldnames or ())
            missing = sorted(set(REQUIRED_FIELDS).difference(columns))
            if missing:
                raise GeNISAuditError(f"{path.name} 缺少审计字段：{', '.join(missing)}")
            for row_number, row in enumerate(reader, start=2):
                flow_id = str(row["FlowID"]).strip()
                if not flow_id:
                    raise GeNISAuditError(f"FlowID 不能为空：{path.name}:{row_number}")
                label = str(row["BinaryLabel"]).strip()
                subtype = str(row["SubCategoryLabel"]).strip()
                if not label or not subtype:
                    raise GeNISAuditError(f"标签或攻击子类不能为空：{path.name}:{row_number}")
                start = _parse_timestamp(row["StartTime"], "StartTime", path, row_number)
                last = _parse_timestamp(row["LastTime"], "LastTime", path, row_number)
                if last < start:
                    raise GeNISAuditError(f"LastTime 早于 StartTime：{path.name}:{row_number}")

                key = _session_key(source_index, flow_id)
                state = sessions.get(key)
                if state is None:
                    sessions[key] = _SessionState(
                        window_count=1,
                        first_label=label,
                        first_subtype=subtype,
                        start_min=start,
                        last_max=last,
                    )
                    file_sessions += 1
                else:
                    state.update(label, subtype, start, last)

                row_count += 1
                file_rows += 1
                binary_label_rows[label] += 1
                subtype_rows[subtype] += 1
                time_range.update(start, last)
                file_time_range.update(start, last)
                file_start_times.add(start)

        ordered_start_times = sorted(file_start_times)
        start_gaps = Counter(
            right - left
            for left, right in zip(ordered_start_times, ordered_start_times[1:], strict=False)
        )
        gap_summary = None
        if start_gaps:
            gap_summary = {
                "max": max(start_gaps),
                "min": min(start_gaps),
                "p50": _percentile_from_counts(start_gaps, 0.50),
                "p95": _percentile_from_counts(start_gaps, 0.95),
            }

        input_files.append(
            {
                "path": str(path),
                "row_count": file_rows,
                "rows_per_start_time_mean": file_rows / len(file_start_times),
                "session_count": file_sessions,
                "size_bytes": path.stat().st_size,
                "start_gap_seconds": gap_summary,
                "start_time_count": len(file_start_times),
                "time_range": file_time_range.as_dict(),
            }
        )

    if row_count == 0:
        raise GeNISAuditError("GeNIS CSV 不包含数据行")

    subtype_sessions: Counter[str] = Counter()
    window_counts: Counter[int] = Counter()
    label_conflicts = 0
    subtype_conflicts = 0
    session_start_times: list[set[float]] = [set() for _ in paths]
    session_last_times: list[set[float]] = [set() for _ in paths]
    for (source_index, _), state in sessions.items():
        labels = state.label_values()
        subtypes = state.subtype_values()
        label_conflicts += len(labels) > 1
        subtype_conflicts += len(subtypes) > 1
        subtype_sessions["|".join(subtypes)] += 1
        window_counts[state.window_count] += 1
        session_start_times[source_index].add(state.start_min)
        session_last_times[source_index].add(state.last_max)

    for source_index, file_summary in enumerate(input_files):
        file_summary["session_start_time_count"] = len(session_start_times[source_index])
        file_summary["session_last_time_count"] = len(session_last_times[source_index])

    session_count = len(sessions)
    return {
        "schema_version": "genis_session_audit_v1",
        "input_files": input_files,
        "row_count": row_count,
        "session_count": session_count,
        "repeated_window_count": row_count - session_count,
        "binary_label_rows": dict(sorted(binary_label_rows.items())),
        "subtype_rows": dict(sorted(subtype_rows.items())),
        "subtype_sessions": dict(sorted(subtype_sessions.items())),
        "time_range": time_range.as_dict(),
        "session_window_count": {
            "max": max(window_counts),
            "mean": row_count / session_count,
            "p50": _percentile_from_counts(window_counts, 0.50),
            "p95": _percentile_from_counts(window_counts, 0.95),
        },
        "session_label_conflicts": label_conflicts,
        "session_subtype_conflicts": subtype_conflicts,
        "privacy": {
            "raw_flow_ids_written": False,
            "addresses_written": False,
            "ports_written": False,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 GeNIS 会话、时间和攻击子类")
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    audit = audit_genis_paths(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True))
