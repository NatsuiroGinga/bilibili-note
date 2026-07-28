"""把完整 ns-3 队列真值组转换为无泄漏的四窗口物理序列。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from flow_probe.ns3_field_roles import (
    load_ns3_field_roles,
    validate_group_disjoint_splits,
)
from flow_probe.ns3_truth import (
    INTEGER_FIELDS,
    TEXT_FIELDS,
    NS3TruthValidationError,
    validate_ns3_truth_paths,
)

HORIZON = 4
SPLITS = ("train", "validation", "test")
SEED_SPLITS = {42: "train", 43: "validation", 44: "test"}
FIELD_ROLES_PATH = (
    Path(__file__).resolve().parents[2] / "configs" / "ns3_queue_truth_field_roles.json"
)
NORMALIZED_FIELDS = (
    "queue_start_l3_bytes",
    "queue_end_l3_bytes",
    "qdisc_received_l3_bytes",
    "qdisc_enqueued_l3_bytes",
    "qdisc_dequeued_l3_bytes",
    "qdisc_dropped_before_enqueue_l3_bytes",
    "qdisc_dropped_after_dequeue_l3_bytes",
)


class NS3SequenceBuildError(RuntimeError):
    """ns-3 物理序列构造失败。"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Sequence[dict[str, object]]) -> None:
    rendered = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(rendered, encoding="utf-8")


def _typed_value(field: str, raw_value: str) -> object:
    if field in TEXT_FIELDS:
        return raw_value
    number = Decimal(raw_value)
    if field in INTEGER_FIELDS:
        return int(number)
    return float(number)


def _load_groups(
    csv_paths: Sequence[Path],
) -> tuple[dict[str, list[dict[str, object]]], dict[str, Path], dict[Path, str]]:
    groups: dict[str, list[dict[str, object]]] = {}
    group_sources: dict[str, Path] = {}
    source_groups: dict[Path, set[str]] = {}
    for path in csv_paths:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            for raw_row in reader:
                row = {field: _typed_value(field, value) for field, value in raw_row.items()}
                group_id = str(row["group_id"])
                groups.setdefault(group_id, []).append(row)
                group_sources[group_id] = path
                source_groups.setdefault(path, set()).add(group_id)
    invalid_sources = {
        path: group_ids for path, group_ids in source_groups.items() if len(group_ids) != 1
    }
    if invalid_sources:
        details = ", ".join(
            f"{path}={sorted(group_ids)}" for path, group_ids in sorted(invalid_sources.items())
        )
        raise NS3SequenceBuildError(f"每个源 CSV 必须精确包含一个完整 group_id：{details}")
    return (
        groups,
        group_sources,
        {path: next(iter(group_ids)) for path, group_ids in source_groups.items()},
    )


def _verify_source_hash_manifests(csv_paths: Sequence[Path], hashes: dict[Path, str]) -> None:
    cached_manifests: dict[Path, dict[str, object]] = {}
    for path in csv_paths:
        candidates = (path.parent / "csv_sha256.json", path.parent.parent / "csv_sha256.json")
        manifest_path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if manifest_path is None:
            continue
        if manifest_path not in cached_manifests:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(loaded, dict) or not isinstance(loaded.get("files"), list):
                raise NS3SequenceBuildError(f"源哈希清单 {manifest_path} 的 files 必须是数组")
            cached_manifests[manifest_path] = loaded
        entries = [
            entry
            for entry in cached_manifests[manifest_path]["files"]
            if isinstance(entry, dict) and Path(str(entry.get("path", ""))).name == path.name
        ]
        if len(entries) != 1:
            raise NS3SequenceBuildError(f"源哈希清单 {manifest_path} 中无法唯一定位 {path.name}")
        expected_hash = entries[0].get("sha256")
        if expected_hash != hashes[path]:
            raise NS3SequenceBuildError(
                f"源 CSV {path.name} 的 SHA-256 与 {manifest_path} 不匹配："
                f"清单={expected_hash}，实际={hashes[path]}"
            )


def _empty_counts() -> dict[str, int]:
    return {
        "candidate_count": 0,
        "retained_count": 0,
        "excluded_transition_count": 0,
    }


def _build_sample(
    windows: Sequence[dict[str, object]],
    *,
    split: str,
    source_path: Path,
    source_sha256: str,
    roles: dict[str, tuple[str, ...]],
) -> dict[str, object]:
    group_id = str(windows[0]["group_id"])
    window_indices = [int(window["window_index"]) for window in windows]
    scales = [float(window["configured_capacity_integral_link_bytes"]) for window in windows]
    if any(scale <= 0 for scale in scales):
        raise NS3SequenceBuildError(f"组 {group_id} 包含小于等于零的配置容量积分")
    digest = hashlib.sha256(
        f"{group_id}|{source_sha256}|h{HORIZON}|{window_indices[0]}".encode()
    ).hexdigest()
    return {
        "sample_id": f"ns3-h4-{digest}",
        "group_id": group_id,
        "split": split,
        "source_csv_sha256": source_sha256,
        "model_inputs": {
            field: [window[field] for window in windows]
            for field in roles["model_input_observable"]
        },
        "queue_boundary_anchors_l3_bytes": [
            windows[0]["queue_start_l3_bytes"],
            *(window["queue_end_l3_bytes"] for window in windows),
        ],
        "state_supervision": {
            field: [window[field] for window in windows] for field in roles["state_supervision"]
        },
        "normalization_scale_configured_capacity_integral_link_bytes": scales,
        "normalized_physics": {
            field: [
                float(window[field]) / scale for window, scale in zip(windows, scales, strict=True)
            ]
            for field in NORMALIZED_FIELDS
        },
        "label_targets": {
            field: [window[field] for window in windows] for field in roles["label_target"]
        },
        "metadata": {
            "scenario_id": windows[0]["scenario_id"],
            "seed": windows[0]["seed"],
            "run": windows[0]["run"],
            "source_csv_path": str(source_path),
            "window_indices": window_indices,
            "window_start_s": [window["window_start_s"] for window in windows],
            "window_end_s": [window["window_end_s"] for window in windows],
        },
    }


def _validate_candidate(windows: Sequence[dict[str, object]]) -> None:
    group_id = str(windows[0]["group_id"])
    if any(window["group_id"] != group_id for window in windows):
        raise NS3SequenceBuildError("候选四窗口跨越 group_id")
    for previous, current in zip(windows, windows[1:], strict=False):
        if int(current["window_index"]) != int(previous["window_index"]) + 1:
            raise NS3SequenceBuildError(f"组 {group_id} 的候选窗口索引不连续")
        if previous["window_end_s"] != current["window_start_s"]:
            raise NS3SequenceBuildError(f"组 {group_id} 的候选时间边界不连续")
        if previous["queue_end_l3_bytes"] != current["queue_start_l3_bytes"]:
            raise NS3SequenceBuildError(f"组 {group_id} 的候选队列状态不连续")


def _create_artifact_manifest(output_dir: Path) -> None:
    artifact_names = sorted(REQUIRED_ARTIFACTS - {"artifact_manifest.json"})
    entries = []
    for name in artifact_names:
        path = output_dir / name
        entries.append(
            {
                "path": name,
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
            }
        )
    _write_json(
        output_dir / "artifact_manifest.json",
        {"schema_version": "flow_probe_ns3_sequence_artifacts_v1", "artifacts": entries},
    )


REQUIRED_ARTIFACTS = {
    "train.jsonl",
    "validation.jsonl",
    "test.jsonl",
    "split_manifest.json",
    "field_roles_snapshot.json",
    "source_csv_sha256.json",
    "sample_statistics.json",
    "artifact_manifest.json",
    "console.log",
}


def build_ns3_sequences(
    csv_paths: Sequence[Path],
    output_dir: Path,
    horizon: int = HORIZON,
) -> dict[str, object]:
    """构造按完整运行组隔离的四窗口 ns-3 物理序列。"""
    if horizon != HORIZON:
        raise NS3SequenceBuildError("horizon 正式固定为 4")
    output_path = Path(output_dir)
    if output_path.exists():
        raise NS3SequenceBuildError(f"输出目录 {output_path} 已存在，不得复用")
    output_path.mkdir(parents=True, exist_ok=False)
    console_path = output_path / "console.log"
    log_lines = [f"开始构造 ns-3 四窗口序列：输出目录={output_path}"]
    try:
        paths = sorted({Path(path).resolve() for path in csv_paths})
        if not paths:
            raise NS3SequenceBuildError("至少需要一个源 CSV")
        hashes = {path: _sha256(path) for path in paths}
        _verify_source_hash_manifests(paths, hashes)
        try:
            validation = validate_ns3_truth_paths(paths)
        except NS3TruthValidationError as exc:
            if "configured_capacity_integral_link_bytes" in str(exc):
                raise NS3SequenceBuildError(f"容量积分校验失败：{exc}") from exc
            raise
        roles = load_ns3_field_roles(FIELD_ROLES_PATH)
        groups, group_sources, source_groups = _load_groups(paths)

        samples_by_split: dict[str, list[dict[str, object]]] = {split: [] for split in SPLITS}
        split_groups: dict[str, list[str]] = {split: [] for split in SPLITS}
        split_counts = {split: _empty_counts() for split in SPLITS}
        scenario_counts: dict[str, dict[str, dict[str, int]]] = {split: {} for split in SPLITS}
        group_counts: dict[str, dict[str, dict[str, object]]] = {split: {} for split in SPLITS}
        total = _empty_counts()

        for group_id, windows in sorted(groups.items()):
            seed = int(windows[0]["seed"])
            if seed not in SEED_SPLITS:
                raise NS3SequenceBuildError(f"组 {group_id} 使用不支持的切分种子 {seed}")
            split = SEED_SPLITS[seed]
            scenario = str(windows[0]["scenario_id"])
            split_groups[split].append(group_id)
            scenario_count = scenario_counts[split].setdefault(scenario, _empty_counts())
            group_count = _empty_counts()
            candidate_count = len(windows) - horizon + 1
            for start in range(candidate_count):
                candidate = windows[start : start + horizon]
                _validate_candidate(candidate)
                total["candidate_count"] += 1
                split_counts[split]["candidate_count"] += 1
                scenario_count["candidate_count"] += 1
                group_count["candidate_count"] += 1
                if any(window["traffic_phase"] == "transition" for window in candidate):
                    total["excluded_transition_count"] += 1
                    split_counts[split]["excluded_transition_count"] += 1
                    scenario_count["excluded_transition_count"] += 1
                    group_count["excluded_transition_count"] += 1
                    continue
                sample = _build_sample(
                    candidate,
                    split=split,
                    source_path=group_sources[group_id],
                    source_sha256=hashes[group_sources[group_id]],
                    roles=roles,
                )
                samples_by_split[split].append(sample)
                total["retained_count"] += 1
                split_counts[split]["retained_count"] += 1
                scenario_count["retained_count"] += 1
                group_count["retained_count"] += 1
            group_counts[split][group_id] = {"scenario_id": scenario, **group_count}

        validate_group_disjoint_splits(split_groups)
        for split in SPLITS:
            _write_jsonl(output_path / f"{split}.jsonl", samples_by_split[split])
        _write_json(
            output_path / "split_manifest.json",
            {
                "schema_version": "flow_probe_ns3_sequence_split_v1",
                "horizon": horizon,
                "splits": {
                    split: {
                        "seed": next(seed for seed, name in SEED_SPLITS.items() if name == split),
                        "group_ids": sorted(split_groups[split]),
                        "sample_count": len(samples_by_split[split]),
                    }
                    for split in SPLITS
                },
            },
        )
        _write_json(
            output_path / "field_roles_snapshot.json",
            {role: list(fields) for role, fields in roles.items()},
        )
        _write_json(
            output_path / "source_csv_sha256.json",
            {
                "schema_version": "flow_probe_ns3_sequence_sources_v1",
                "files": [
                    {
                        "group_id": source_groups[path],
                        "path": str(path),
                        "sha256": hashes[path],
                    }
                    for path in paths
                ],
            },
        )
        _write_json(
            output_path / "sample_statistics.json",
            {
                "schema_version": "flow_probe_ns3_sequence_statistics_v1",
                "horizon": horizon,
                "total": total,
                "splits": {
                    split: {
                        **split_counts[split],
                        "scenarios": scenario_counts[split],
                        "groups": group_counts[split],
                    }
                    for split in SPLITS
                },
            },
        )
        summary = {
            "validation_status": validation["validation_status"],
            "group_count": len(groups),
            "candidate_count": total["candidate_count"],
            "excluded_transition_count": total["excluded_transition_count"],
            "sample_count": total["retained_count"],
            "output_dir": str(output_path.resolve()),
        }
        log_lines.append(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        log_lines.append("ns-3 四窗口序列构造完成")
        console_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        _create_artifact_manifest(output_path)
        return summary
    except Exception as exc:
        message = f"构造 ns-3 四窗口序列失败：{exc}"
        log_lines.append(message)
        console_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        if isinstance(exc, NS3SequenceBuildError):
            raise
        raise NS3SequenceBuildError(message) from exc


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构造无泄漏的 ns-3 四窗口物理序列")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input-dir", type=Path)
    inputs.add_argument("--inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.input_dir is not None:
        csv_dir = args.input_dir / "csv"
        if not csv_dir.is_dir():
            csv_dir = args.input_dir
        csv_paths = sorted(csv_dir.glob("*.csv"))
    else:
        csv_paths = args.inputs
    try:
        summary = build_ns3_sequences(csv_paths, args.output_dir, horizon=args.horizon)
    except NS3SequenceBuildError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
