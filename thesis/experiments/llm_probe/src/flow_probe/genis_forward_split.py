"""GeNIS 会话级前向时间划分。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal, TextIO

from flow_probe.adapters.base import parse_binary_label
from flow_probe.adapters.genis import adapt_row as adapt_genis
from flow_probe.schemas import FlowSample
from flow_probe.serialize import serialize_flow

BinaryLabel = Literal["benign", "malicious"]
Assignment = Literal["train", "validation", "test", "purged"] | str


class GeNISForwardSplitError(ValueError):
    """GeNIS 会话不能满足无泄漏前向划分条件。"""


@dataclass(frozen=True)
class GeNISSession:
    """不包含原始 FlowID 的会话级划分元数据。"""

    session_id: str
    subtype: str
    binary_label: BinaryLabel
    start_time: float
    last_time: float
    row_count: int


@dataclass(frozen=True)
class GeNISHybridSplitPlan:
    """域内前向划分、清除会话与完整域外场景。"""

    assignments: dict[str, Assignment]
    train: tuple[GeNISSession, ...]
    validation: tuple[GeNISSession, ...]
    test: tuple[GeNISSession, ...]
    purged: tuple[GeNISSession, ...]
    ood: dict[str, tuple[GeNISSession, ...]]


@dataclass
class _SessionAccumulator:
    session_id: str
    subtype: str
    binary_label: BinaryLabel
    start_time: float
    last_time: float
    row_count: int = 1

    def update(
        self,
        subtype: str,
        binary_label: BinaryLabel,
        start_time: float,
        last_time: float,
    ) -> None:
        if subtype != self.subtype or binary_label != self.binary_label:
            raise GeNISForwardSplitError("同一会话包含冲突标签或攻击子类")
        self.start_time = min(self.start_time, start_time)
        self.last_time = max(self.last_time, last_time)
        self.row_count += 1

    def freeze(self) -> GeNISSession:
        return GeNISSession(
            session_id=self.session_id,
            subtype=self.subtype,
            binary_label=self.binary_label,
            start_time=self.start_time,
            last_time=self.last_time,
            row_count=self.row_count,
        )


def _parse_time(value: object, field_name: str, path: Path, row_number: int) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError) as error:
        raise GeNISForwardSplitError(
            f"时间戳无法解析：{path.name}:{row_number}:{field_name}"
        ) from error
    if not math.isfinite(parsed):
        raise GeNISForwardSplitError(f"时间戳不是有限数：{path.name}:{row_number}:{field_name}")
    return parsed


def _hashed_session_id(path: Path, flow_id: str) -> str:
    digest = hashlib.blake2b(digest_size=16)
    digest.update(path.name.encode("utf-8"))
    digest.update(b"\0")
    digest.update(flow_id.encode("utf-8"))
    return digest.hexdigest()


def load_genis_sessions(input_paths: Sequence[Path]) -> tuple[GeNISSession, ...]:
    """读取会话级元数据，输出不可逆哈希标识而非原始 FlowID。"""
    paths = sorted(Path(path) for path in input_paths)
    if not paths:
        raise GeNISForwardSplitError("至少需要一个 GeNIS CSV")
    names = [path.name for path in paths]
    if len(names) != len(set(names)):
        raise GeNISForwardSplitError("输入文件名必须唯一，以保证会话哈希稳定")

    required_fields = {
        "FlowID",
        "StartTime",
        "LastTime",
        "BinaryLabel",
        "SubCategoryLabel",
    }
    accumulators: dict[str, _SessionAccumulator] = {}
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            missing = sorted(required_fields.difference(reader.fieldnames or ()))
            if missing:
                raise GeNISForwardSplitError(f"{path.name} 缺少划分字段：{', '.join(missing)}")
            for row_number, row in enumerate(reader, start=2):
                flow_id = str(row["FlowID"]).strip()
                subtype = str(row["SubCategoryLabel"]).strip()
                if not flow_id or not subtype:
                    raise GeNISForwardSplitError(
                        f"FlowID 或攻击子类不能为空：{path.name}:{row_number}"
                    )
                binary_label = parse_binary_label("genis", row["BinaryLabel"])
                start_time = _parse_time(row["StartTime"], "StartTime", path, row_number)
                last_time = _parse_time(row["LastTime"], "LastTime", path, row_number)
                if last_time < start_time:
                    raise GeNISForwardSplitError(
                        f"LastTime 早于 StartTime：{path.name}:{row_number}"
                    )
                session_id = _hashed_session_id(path, flow_id)
                accumulator = accumulators.get(session_id)
                if accumulator is None:
                    accumulators[session_id] = _SessionAccumulator(
                        session_id=session_id,
                        subtype=subtype,
                        binary_label=binary_label,
                        start_time=start_time,
                        last_time=last_time,
                    )
                else:
                    accumulator.update(subtype, binary_label, start_time, last_time)

    return tuple(
        sorted(
            (item.freeze() for item in accumulators.values()),
            key=lambda item: (item.subtype, item.start_time, item.session_id),
        )
    )


def _partition_summary(items: Sequence[GeNISSession]) -> dict[str, object]:
    label_rows: Counter[str] = Counter()
    subtype_rows: Counter[str] = Counter()
    for item in items:
        label_rows[item.binary_label] += item.row_count
        subtype_rows[item.subtype] += item.row_count
    return {
        "row_count": sum(item.row_count for item in items),
        "session_count": len(items),
        "binary_label_rows": dict(sorted(label_rows.items())),
        "subtype_rows": dict(sorted(subtype_rows.items())),
    }


def summarize_hybrid_plan(
    plan: GeNISHybridSplitPlan,
    ratios: tuple[float, float, float],
    ood_subtypes: frozenset[str],
) -> dict[str, object]:
    """生成不包含原始标识的机器可读划分摘要。"""
    partition_summaries = {
        "train": _partition_summary(plan.train),
        "validation": _partition_summary(plan.validation),
        "test": _partition_summary(plan.test),
        "purged": _partition_summary(plan.purged),
    }
    kept_row_count = sum(
        int(partition_summaries[name]["row_count"]) for name in ("train", "validation", "test")
    )
    purged_row_count = int(partition_summaries["purged"]["row_count"])
    domain_row_count = kept_row_count + purged_row_count
    _assert_temporal_order(plan)
    return {
        "schema_version": "genis_hybrid_forward_split_v1",
        "ratios": list(ratios),
        "domain_row_count": domain_row_count,
        "kept_row_count": kept_row_count,
        "kept_ratios": {
            name: int(partition_summaries[name]["row_count"]) / kept_row_count
            for name in ("train", "validation", "test")
        },
        "purged_row_rate": purged_row_count / domain_row_count,
        "temporal_order_verified": True,
        "ood_subtypes": sorted(ood_subtypes),
        "partitions": partition_summaries,
        "ood": {subtype: _partition_summary(items) for subtype, items in sorted(plan.ood.items())},
        "privacy": {
            "raw_flow_ids_written": False,
            "addresses_written": False,
            "ports_written": False,
        },
    }


def _assert_temporal_order(plan: GeNISHybridSplitPlan) -> None:
    for subtype in sorted({item.subtype for item in plan.train}):
        train = [item for item in plan.train if item.subtype == subtype]
        validation = [item for item in plan.validation if item.subtype == subtype]
        test = [item for item in plan.test if item.subtype == subtype]
        if not train or not validation or not test:
            raise GeNISForwardSplitError(f"{subtype} 未覆盖全部域内集合")
        if max(item.last_time for item in train) >= min(item.start_time for item in validation):
            raise GeNISForwardSplitError(f"{subtype} 的训练集和验证集时间重叠")
        if max(item.last_time for item in validation) >= min(item.start_time for item in test):
            raise GeNISForwardSplitError(f"{subtype} 的验证集和测试集时间重叠")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_hybrid_forward_split(
    input_paths: Sequence[Path],
    output_dir: Path,
    ratios: tuple[float, float, float],
    ood_subtypes: frozenset[str],
) -> dict[str, object]:
    """从原始 CSV 生成可复现且不含原始 FlowID 的会话划分制品。"""
    paths = sorted(Path(path) for path in input_paths)
    sessions = load_genis_sessions(paths)
    plan = plan_hybrid_forward_split(sessions, ratios, ood_subtypes)
    summary = summarize_hybrid_plan(plan, ratios, ood_subtypes)
    summary["source_files"] = [
        {
            "name": path.name,
            "sha256": _file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in paths
    ]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "plan_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "session_assignments.jsonl").open("w", encoding="utf-8") as output:
        for item in sorted(sessions, key=lambda value: (value.subtype, value.session_id)):
            record = {
                "assignment": plan.assignments[item.session_id],
                "binary_label": item.binary_label,
                "last_time": item.last_time,
                "row_count": item.row_count,
                "session_id": item.session_id,
                "start_time": item.start_time,
                "subtype": item.subtype,
            }
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return summary


def _load_assignments(
    assignments_path: Path,
) -> tuple[dict[str, str], dict[str, int]]:
    assignments: dict[str, str] = {}
    expected_rows: dict[str, int] = {}
    with Path(assignments_path).open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            value = json.loads(line)
            if not isinstance(value, Mapping):
                raise GeNISForwardSplitError(f"会话分配第 {line_number} 行不是对象")
            session_id = str(value.get("session_id", ""))
            assignment = str(value.get("assignment", ""))
            row_count = int(value.get("row_count", 0))
            if not re.fullmatch(r"[0-9a-f]{32}", session_id):
                raise GeNISForwardSplitError(f"会话分配第 {line_number} 行标识不合法")
            if assignment not in {"train", "validation", "test", "purged"} and not re.fullmatch(
                r"ood:[a-z0-9_-]+", assignment
            ):
                raise GeNISForwardSplitError(f"会话分配第 {line_number} 行集合不合法")
            if row_count <= 0:
                raise GeNISForwardSplitError(f"会话分配第 {line_number} 行计数不合法")
            if session_id in assignments:
                raise GeNISForwardSplitError("会话分配包含重复标识")
            assignments[session_id] = assignment
            expected_rows[session_id] = row_count
    if not assignments:
        raise GeNISForwardSplitError("会话分配文件不能为空")
    return assignments, expected_rows


def _training_record(sample: FlowSample) -> dict[str, object]:
    return {
        "sample_id": sample.sample_id,
        "group_id": sample.group_id,
        "source_dataset": sample.source_dataset,
        "binary_label": sample.binary_label,
        "attack_family": sample.attack_family,
        "attack_subtype": sample.original_label,
        "features": dict(sample.features),
        "prompt": serialize_flow(sample),
        "completion": json.dumps(
            {"label": sample.binary_label}, ensure_ascii=False, separators=(",", ":")
        ),
    }


def _assignment_filename(assignment: str) -> str:
    if assignment.startswith("ood:"):
        return f"ood_{assignment.removeprefix('ood:')}.jsonl"
    return f"{assignment}.jsonl"


def materialize_genis_split(
    input_paths: Sequence[Path],
    assignments_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """按哈希会话清单生成域内与独立域外训练 JSONL。"""
    paths = sorted(Path(path) for path in input_paths)
    assignments, expected_rows = _load_assignments(Path(assignments_path))
    assignments_to_write = sorted(
        {assignment for assignment in assignments.values() if assignment != "purged"}
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    seen_rows: Counter[str] = Counter()
    output_rows: Counter[str] = Counter()

    with ExitStack() as stack:
        writers: dict[str, TextIO] = {
            assignment: stack.enter_context(
                (output_dir / _assignment_filename(assignment)).open("w", encoding="utf-8")
            )
            for assignment in assignments_to_write
        }
        for path in paths:
            with path.open("r", encoding="utf-8-sig", newline="") as source:
                reader = csv.DictReader(source)
                for row_number, row in enumerate(reader, start=1):
                    flow_id = str(row.get("FlowID", "")).strip()
                    if not flow_id:
                        raise GeNISForwardSplitError(
                            f"FlowID 不能为空：{path.name}:{row_number + 1}"
                        )
                    session_id = _hashed_session_id(path, flow_id)
                    try:
                        assignment = assignments[session_id]
                    except KeyError as error:
                        raise GeNISForwardSplitError(
                            f"原始数据包含未分配会话：{path.name}:{row_number + 1}"
                        ) from error
                    seen_rows[session_id] += 1
                    if assignment == "purged":
                        continue
                    sample = replace(adapt_genis(row, str(path), row_number), group_id=session_id)
                    writers[assignment].write(
                        json.dumps(_training_record(sample), ensure_ascii=False, sort_keys=True)
                        + "\n"
                    )
                    output_rows[assignment] += 1

    if dict(seen_rows) != expected_rows:
        missing = len(set(expected_rows).difference(seen_rows))
        mismatched = sum(
            seen_rows.get(session_id, 0) != row_count
            for session_id, row_count in expected_rows.items()
        )
        raise GeNISForwardSplitError(
            f"物化行数与会话清单不一致：缺失会话 {missing}，计数不符 {mismatched}"
        )

    purged_row_count = sum(
        row_count
        for session_id, row_count in expected_rows.items()
        if assignments[session_id] == "purged"
    )
    summary = {
        "schema_version": "genis_materialized_split_v2",
        "written_row_count": sum(output_rows.values()),
        "purged_row_count": purged_row_count,
        "output_rows": dict(sorted(output_rows.items())),
        "assignment_sha256": _file_sha256(Path(assignments_path)),
        "source_files": [
            {
                "name": path.name,
                "sha256": _file_sha256(path),
                "size_bytes": path.stat().st_size,
            }
            for path in paths
        ],
        "privacy": {
            "raw_flow_ids_written": False,
            "addresses_written": False,
            "ports_written": False,
        },
    }
    (output_dir / "materialization_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="规划 GeNIS 混合防泄漏前向划分")
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ratios", nargs=3, type=float, default=(0.8, 0.1, 0.1))
    parser.add_argument("--ood-subtype", action="append", default=[])
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    summary = create_hybrid_forward_split(
        input_paths=args.input,
        output_dir=args.output_dir,
        ratios=tuple(args.ratios),
        ood_subtypes=frozenset(args.ood_subtype),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def _parse_materialize_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="物化 GeNIS 混合防泄漏划分")
    parser.add_argument("--input", action="append", type=Path, required=True)
    parser.add_argument("--assignments", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def materialize_main() -> None:
    args = _parse_materialize_args()
    summary = materialize_genis_split(
        input_paths=args.input,
        assignments_path=args.assignments,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


def plan_hybrid_forward_split(
    sessions: Sequence[GeNISSession],
    ratios: tuple[float, float, float],
    ood_subtypes: frozenset[str],
) -> GeNISHybridSplitPlan:
    """规划 GeNIS 域内前向划分和完整场景域外测试。"""
    _validate_inputs(sessions, ratios)
    by_subtype: dict[str, list[GeNISSession]] = defaultdict(list)
    for item in sessions:
        by_subtype[item.subtype].append(item)

    assignments: dict[str, Assignment] = {}
    partitions: dict[str, list[GeNISSession]] = {
        "train": [],
        "validation": [],
        "test": [],
        "purged": [],
    }
    ood: dict[str, tuple[GeNISSession, ...]] = {}

    for subtype in sorted(by_subtype):
        subtype_sessions = sorted(
            by_subtype[subtype], key=lambda item: (item.start_time, item.session_id)
        )
        if subtype in ood_subtypes:
            assignment = f"ood:{subtype}"
            for item in subtype_sessions:
                assignments[item.session_id] = assignment
            ood[subtype] = tuple(subtype_sessions)
            continue

        subtype_partitions = _split_subtype(subtype, subtype_sessions, ratios)
        for partition_name, items in subtype_partitions.items():
            partitions[partition_name].extend(items)
            for item in items:
                assignments[item.session_id] = partition_name

    def sort_key(item: GeNISSession) -> tuple[str, float, str]:
        return item.subtype, item.start_time, item.session_id

    return GeNISHybridSplitPlan(
        assignments=assignments,
        train=tuple(sorted(partitions["train"], key=sort_key)),
        validation=tuple(sorted(partitions["validation"], key=sort_key)),
        test=tuple(sorted(partitions["test"], key=sort_key)),
        purged=tuple(sorted(partitions["purged"], key=sort_key)),
        ood=ood,
    )


def _validate_inputs(sessions: Sequence[GeNISSession], ratios: tuple[float, float, float]) -> None:
    if not sessions:
        raise GeNISForwardSplitError("至少需要一个 GeNIS 会话")
    if len(ratios) != 3 or any(ratio <= 0 for ratio in ratios):
        raise GeNISForwardSplitError("ratios 必须包含三个正数")
    if abs(sum(ratios) - 1.0) > 1e-9:
        raise GeNISForwardSplitError("ratios 之和必须为 1")

    session_ids = [item.session_id for item in sessions]
    if len(session_ids) != len(set(session_ids)):
        raise GeNISForwardSplitError("会话标识重复")
    for item in sessions:
        if not item.session_id or not item.subtype:
            raise GeNISForwardSplitError("会话标识和攻击子类不能为空")
        if not math.isfinite(item.start_time) or not math.isfinite(item.last_time):
            raise GeNISForwardSplitError("会话时间必须是有限数")
        if item.last_time < item.start_time:
            raise GeNISForwardSplitError("会话结束时间早于起始时间")
        if item.row_count <= 0:
            raise GeNISForwardSplitError("会话行数必须为正数")


def _nearest_cut(
    start_groups: list[list[GeNISSession]],
    target_rows: float,
    lower: int,
    upper: int,
) -> int:
    cumulative_rows = 0
    candidates: list[tuple[float, int]] = []
    for index, group in enumerate(start_groups, start=1):
        cumulative_rows += sum(item.row_count for item in group)
        if lower <= index <= upper:
            candidates.append((abs(cumulative_rows - target_rows), index))
    if not candidates:
        raise AssertionError("前向时间切分点不存在")
    return min(candidates)[1]


def _split_subtype(
    subtype: str,
    sessions: list[GeNISSession],
    ratios: tuple[float, float, float],
) -> dict[str, list[GeNISSession]]:
    grouped_by_start: dict[float, list[GeNISSession]] = defaultdict(list)
    for item in sessions:
        grouped_by_start[item.start_time].append(item)
    start_groups = [grouped_by_start[start] for start in sorted(grouped_by_start)]
    if len(start_groups) < 3:
        raise GeNISForwardSplitError(f"{subtype} 至少 3 个会话起始时刻")

    total_rows = sum(item.row_count for item in sessions)
    first_cut = _nearest_cut(
        start_groups,
        target_rows=total_rows * ratios[0],
        lower=1,
        upper=len(start_groups) - 2,
    )
    second_cut = _nearest_cut(
        start_groups,
        target_rows=total_rows * (ratios[0] + ratios[1]),
        lower=first_cut + 1,
        upper=len(start_groups) - 1,
    )
    validation_start = min(item.start_time for item in start_groups[first_cut])
    test_start = min(item.start_time for item in start_groups[second_cut])

    candidates = {
        "train": [item for group in start_groups[:first_cut] for item in group],
        "validation": [item for group in start_groups[first_cut:second_cut] for item in group],
        "test": [item for group in start_groups[second_cut:] for item in group],
    }
    partitions = {
        "train": [item for item in candidates["train"] if item.last_time < validation_start],
        "validation": [item for item in candidates["validation"] if item.last_time < test_start],
        "test": candidates["test"],
        "purged": [item for item in candidates["train"] if item.last_time >= validation_start]
        + [item for item in candidates["validation"] if item.last_time >= test_start],
    }
    for partition_name in ("train", "validation", "test"):
        if not partitions[partition_name]:
            raise GeNISForwardSplitError(f"{subtype} 的 {partition_name} 在清除跨边界会话后为空")
    return partitions
