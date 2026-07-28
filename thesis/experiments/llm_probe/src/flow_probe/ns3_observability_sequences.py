"""把 v5 域随机化窗口构造成公共观测四窗口序列。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

HORIZON = 4
SPLITS = ("train", "calibration", "unseen_configuration", "out_of_range")
MODEL_INPUT_FIELDS = (
    "total_packets",
    "total_bytes",
    "packet_length_mean",
    "packet_rate",
    "byte_rate",
)
MODEL_INPUT_SOURCE_FIELDS = {
    "total_packets": "public_total_packets",
    "total_bytes": "public_total_l3_bytes",
    "packet_length_mean": "public_packet_length_mean_l3_bytes",
    "packet_rate": "public_packet_rate_pps",
    "byte_rate": "public_byte_rate_Bps",
}
CANDIDATE_PUBLIC_FIELDS = (
    "public_total_packets",
    "public_total_l3_bytes",
    "public_packet_length_mean_l3_bytes",
    "public_packet_length_min_l3_bytes",
    "public_packet_length_max_l3_bytes",
    "public_iat_mean_ms",
    "public_packet_rate_pps",
    "public_byte_rate_Bps",
)
PHYSICS_FIELDS = (
    "supervision_capacity_start_bps",
    "supervision_capacity_end_bps",
    "supervision_capacity_integral_link_bytes",
    "supervision_qdisc_received_l3_bytes",
    "supervision_qdisc_enqueued_l3_bytes",
    "supervision_qdisc_dequeued_l3_bytes",
    "supervision_qdisc_dropped_before_enqueue_l3_bytes",
    "supervision_qdisc_dropped_after_dequeue_l3_bytes",
    "supervision_qdisc_received_packets",
    "supervision_qdisc_enqueued_packets",
    "supervision_qdisc_dequeued_packets",
    "supervision_qdisc_dropped_before_enqueue_packets",
    "supervision_qdisc_dropped_after_dequeue_packets",
)
ENVIRONMENT_FIELDS = (
    "supervision_initial_capacity_bps",
    "supervision_shifted_capacity_bps",
    "supervision_capacity_shift_s",
    "supervision_access_delay_ms",
    "supervision_bottleneck_delay_ms",
    "supervision_queue_limit_packets",
    "supervision_downstream_loss_rate",
    "supervision_sender_count",
    "supervision_benign_rate_mbps",
    "supervision_attack_rate_mbps",
    "supervision_attack_start_s",
    "supervision_packet_size_bytes",
    "supervision_jitter_max_ms",
    "supervision_burst_on_mean_s",
    "supervision_burst_off_mean_s",
    "supervision_measurement_noise_std_ratio",
    "supervision_traffic_mode",
    "supervision_transport",
    "supervision_queue_model",
    "supervision_arrival_model",
)
EXPECTED_SAMPLES_PER_GROUP = 117
EXPECTED_SPLIT_GROUPS = {
    "train": 120,
    "calibration": 30,
    "unseen_configuration": 30,
    "out_of_range": 30,
}


class ObservabilitySequenceError(RuntimeError):
    """v5 四窗口序列不满足无泄漏构造契约。"""


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


def _write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as destination:
        for row in rows:
            destination.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def _load_expected_hashes(input_dir: Path) -> dict[str, str]:
    manifest_path = input_dir / "csv_sha256.json"
    if not manifest_path.is_file():
        raise ObservabilitySequenceError(f"源 CSV 哈希清单不存在：{manifest_path}")
    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = loaded.get("files") if isinstance(loaded, dict) else None
    if not isinstance(files, list):
        raise ObservabilitySequenceError("源 CSV 哈希清单的 files 必须是数组")
    expected: dict[str, str] = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise ObservabilitySequenceError("源 CSV 哈希记录必须是对象")
        name = Path(str(entry.get("path", ""))).name
        checksum = str(entry.get("sha256", ""))
        if not name or not checksum or name in expected:
            raise ObservabilitySequenceError("源 CSV 哈希记录缺失或重复")
        expected[name] = checksum
    return expected


def _load_group(path: Path, expected_hash: str) -> list[dict[str, str]]:
    actual_hash = _sha256(path)
    if actual_hash != expected_hash:
        raise ObservabilitySequenceError(
            f"源 CSV {path.name} 的 SHA-256 不匹配：{actual_hash} != {expected_hash}"
        )
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or ())
        required = {
            "schema_version",
            "config_id",
            "split",
            "group_id",
            "seed",
            "run",
            "window_index",
            "window_start_s",
            "window_end_s",
            "supervision_queue_start_l3_bytes",
            "supervision_queue_end_l3_bytes",
            *CANDIDATE_PUBLIC_FIELDS,
            *PHYSICS_FIELDS,
            *ENVIRONMENT_FIELDS,
        }
        missing = sorted(required.difference(columns))
        if missing:
            raise ObservabilitySequenceError(f"源 CSV {path.name} 缺少字段：{', '.join(missing)}")
        rows = list(reader)
    if len(rows) != 120:
        raise ObservabilitySequenceError(f"源 CSV {path.name} 必须精确包含 120 个窗口")
    group_ids = {row["group_id"] for row in rows}
    splits = {row["split"] for row in rows}
    config_ids = {row["config_id"] for row in rows}
    if len(group_ids) != 1 or len(splits) != 1 or len(config_ids) != 1:
        raise ObservabilitySequenceError(f"源 CSV {path.name} 跨越配置、组或切分")
    rows.sort(key=lambda row: int(row["window_index"]))
    for expected_index, row in enumerate(rows):
        if int(row["window_index"]) != expected_index:
            raise ObservabilitySequenceError(f"源 CSV {path.name} 的窗口序号不连续")
    return rows


def _float(row: dict[str, str], field: str) -> float:
    value = float(row[field])
    if not math.isfinite(value):
        raise ObservabilitySequenceError(f"字段 {field} 包含非有限值")
    return value


def _validate_candidate(windows: Sequence[dict[str, str]]) -> None:
    group_id = windows[0]["group_id"]
    if any(window["group_id"] != group_id for window in windows):
        raise ObservabilitySequenceError("四窗口候选跨越 group_id")
    for previous, current in zip(windows, windows[1:], strict=False):
        if int(current["window_index"]) != int(previous["window_index"]) + 1:
            raise ObservabilitySequenceError(f"组 {group_id} 的窗口序号不连续")
        if _float(previous, "window_end_s") != _float(current, "window_start_s"):
            raise ObservabilitySequenceError(f"组 {group_id} 的时间边界不连续")
        if int(previous["supervision_queue_end_l3_bytes"]) != int(
            current["supervision_queue_start_l3_bytes"]
        ):
            raise ObservabilitySequenceError(f"组 {group_id} 的队列边界不连续")


def _build_sample(
    windows: Sequence[dict[str, str]],
    source_path: Path,
    source_sha256: str,
) -> dict[str, object]:
    _validate_candidate(windows)
    split = windows[0]["split"]
    group_id = windows[0]["group_id"]
    start_index = int(windows[0]["window_index"])
    digest = hashlib.sha256(
        f"{group_id}|{source_sha256}|h{HORIZON}|{start_index}".encode()
    ).hexdigest()
    scales = [_float(window, "supervision_capacity_integral_link_bytes") for window in windows]
    normalization_scale = max(scales)
    if normalization_scale <= 0.0:
        raise ObservabilitySequenceError(f"组 {group_id} 的容量积分尺度不为正数")
    queue_anchors = [
        int(windows[0]["supervision_queue_start_l3_bytes"]),
        *(int(window["supervision_queue_end_l3_bytes"]) for window in windows),
    ]
    model_inputs = {
        field: [_float(window, MODEL_INPUT_SOURCE_FIELDS[field]) for window in windows]
        for field in MODEL_INPUT_FIELDS
    }
    observation_mask = {
        field: [
            not (field == "packet_length_mean" and _float(window, "public_total_packets") == 0.0)
            for window in windows
        ]
        for field in MODEL_INPUT_FIELDS
    }
    return {
        "schema_version": "flow_probe_ns3_observability_sequence_v1",
        "sample_id": f"ns3-observability-h4-{digest}",
        "group_id": group_id,
        "split": split,
        "model_inputs": model_inputs,
        "observation_mask": observation_mask,
        "candidate_public_observations": {
            field: [_float(window, field) for window in windows]
            for field in CANDIDATE_PUBLIC_FIELDS
        },
        "state_targets": {
            "queue_boundary_anchors_l3_bytes": queue_anchors,
            "normalized_queue_boundary_anchors": [
                value / normalization_scale for value in queue_anchors
            ],
            "normalization_scale_l3_bytes": normalization_scale,
        },
        "environment_targets": {
            field: (
                windows[0][field]
                if field
                in {
                    "supervision_traffic_mode",
                    "supervision_transport",
                    "supervision_queue_model",
                    "supervision_arrival_model",
                }
                else _float(windows[0], field)
            )
            for field in ENVIRONMENT_FIELDS
        },
        "physics_supervision": {
            field: [_float(window, field) for window in windows] for field in PHYSICS_FIELDS
        },
        "metadata": {
            "config_id": windows[0]["config_id"],
            "seed": int(windows[0]["seed"]),
            "run": int(windows[0]["run"]),
            "window_indices": [int(window["window_index"]) for window in windows],
            "window_start_s": [_float(window, "window_start_s") for window in windows],
            "window_end_s": [_float(window, "window_end_s") for window in windows],
            "source_csv_path": str(source_path),
            "source_csv_sha256": source_sha256,
        },
    }


def build_observability_sequences(input_dir: Path, output_dir: Path) -> dict[str, object]:
    """从 210 个完整运行构造按组隔离的四窗口序列。"""
    normalized_input = input_dir.expanduser().resolve()
    csv_dir = normalized_input / "csv"
    if not csv_dir.is_dir():
        raise ObservabilitySequenceError(f"源 CSV 目录不存在：{csv_dir}")
    normalized_output = output_dir.expanduser().resolve()
    if normalized_output.exists() or normalized_output.is_symlink():
        raise ObservabilitySequenceError(f"输出目录已存在，不得覆盖：{normalized_output}")
    normalized_output.mkdir(parents=True)
    console_path = normalized_output / "console.log"
    try:
        expected_hashes = _load_expected_hashes(normalized_input)
        csv_paths = sorted(csv_dir.glob("*.csv"))
        if len(csv_paths) != 210 or set(path.name for path in csv_paths) != set(expected_hashes):
            raise ObservabilitySequenceError("源 CSV 与 210 项哈希清单不一致")

        samples: dict[str, list[dict[str, object]]] = {split: [] for split in SPLITS}
        group_ids: dict[str, list[str]] = {split: [] for split in SPLITS}
        source_records: list[dict[str, object]] = []
        for path in csv_paths:
            source_hash = _sha256(path)
            rows = _load_group(path, expected_hashes[path.name])
            split = rows[0]["split"]
            if split not in samples:
                raise ObservabilitySequenceError(f"未知切分：{split}")
            group_id = rows[0]["group_id"]
            if group_id in {item for values in group_ids.values() for item in values}:
                raise ObservabilitySequenceError(f"group_id 重复：{group_id}")
            group_ids[split].append(group_id)
            source_records.append(
                {
                    "config_id": rows[0]["config_id"],
                    "group_id": group_id,
                    "split": split,
                    "path": str(path),
                    "sha256": source_hash,
                }
            )
            for start in range(len(rows) - HORIZON + 1):
                samples[split].append(
                    _build_sample(rows[start : start + HORIZON], path, source_hash)
                )

        actual_group_counts = {split: len(group_ids[split]) for split in SPLITS}
        if actual_group_counts != EXPECTED_SPLIT_GROUPS:
            raise ObservabilitySequenceError(f"切分组数不满足冻结契约：{actual_group_counts}")
        expected_sample_counts = {
            split: count * EXPECTED_SAMPLES_PER_GROUP
            for split, count in EXPECTED_SPLIT_GROUPS.items()
        }
        actual_sample_counts = {split: len(samples[split]) for split in SPLITS}
        if actual_sample_counts != expected_sample_counts:
            raise ObservabilitySequenceError(f"四窗口样本数不满足冻结契约：{actual_sample_counts}")

        for split in SPLITS:
            _write_jsonl(normalized_output / f"{split}.jsonl", samples[split])
        _write_json(
            normalized_output / "split_manifest.json",
            {
                "schema_version": "flow_probe_ns3_observability_split_v1",
                "horizon": HORIZON,
                "splits": {
                    split: {
                        "group_count": len(group_ids[split]),
                        "sample_count": len(samples[split]),
                        "group_ids": sorted(group_ids[split]),
                    }
                    for split in SPLITS
                },
            },
        )
        _write_json(
            normalized_output / "field_roles.json",
            {
                "schema_version": "flow_probe_ns3_observability_field_roles_v1",
                "model_input_observable": list(MODEL_INPUT_FIELDS),
                "candidate_public_observable": list(CANDIDATE_PUBLIC_FIELDS),
                "state_supervision_only": [
                    "queue_boundary_anchors_l3_bytes",
                    "normalized_queue_boundary_anchors",
                    "normalization_scale_l3_bytes",
                ],
                "environment_supervision_only": list(ENVIRONMENT_FIELDS),
                "physics_supervision_only": list(PHYSICS_FIELDS),
                "prohibited_model_inputs": [
                    "capacity",
                    "queue_truth",
                    "config_id",
                    "group_id",
                    "split",
                    "seed",
                    "run",
                    "attack_label",
                    "measurement_noise_std_ratio",
                ],
            },
        )
        _write_json(
            normalized_output / "source_csv_sha256.json",
            {
                "schema_version": "flow_probe_ns3_observability_sources_v1",
                "files": source_records,
            },
        )
        summary = {
            "schema_version": "flow_probe_ns3_observability_statistics_v1",
            "horizon": HORIZON,
            "group_count": sum(actual_group_counts.values()),
            "sample_count": sum(actual_sample_counts.values()),
            "split_group_counts": actual_group_counts,
            "split_sample_counts": actual_sample_counts,
            "samples_per_group": EXPECTED_SAMPLES_PER_GROUP,
            "model_input_field_count": len(MODEL_INPUT_FIELDS),
            "candidate_public_field_count": len(CANDIDATE_PUBLIC_FIELDS),
        }
        _write_json(normalized_output / "sample_statistics.json", summary)
        console_path.write_text(
            "开始构造任务十七 v5 四窗口公共观测序列\n"
            + json.dumps(summary, ensure_ascii=False, sort_keys=True)
            + "\n构造完成\n",
            encoding="utf-8",
        )
        artifact_names = (
            *(f"{split}.jsonl" for split in SPLITS),
            "split_manifest.json",
            "field_roles.json",
            "source_csv_sha256.json",
            "sample_statistics.json",
            "console.log",
        )
        _write_json(
            normalized_output / "artifact_manifest.json",
            {
                "schema_version": "flow_probe_ns3_observability_artifacts_v1",
                "artifacts": [
                    {
                        "path": name,
                        "size_bytes": (normalized_output / name).stat().st_size,
                        "sha256": _sha256(normalized_output / name),
                    }
                    for name in artifact_names
                ],
            },
        )
        return {**summary, "output_dir": str(normalized_output)}
    except Exception as error:
        console_path.write_text(f"构造失败：{error}\n", encoding="utf-8")
        if isinstance(error, ObservabilitySequenceError):
            raise
        raise ObservabilitySequenceError(f"构造 v5 四窗口序列失败：{error}") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构造任务十七 v5 四窗口公共观测序列")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = build_observability_sequences(args.input_dir, args.output_dir)
    except ObservabilitySequenceError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
