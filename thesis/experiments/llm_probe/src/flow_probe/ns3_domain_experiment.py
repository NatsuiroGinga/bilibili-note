"""执行任务十七冻结的 210 组 ns-3 域随机化矩阵。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import shlex
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from flow_probe.ns3_domain_randomization import (
    DomainConfig,
    SCHEMA_VERSION,
    SPLIT_COUNTS,
)
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    swanlab_run,
)

PHASE = "ns3-domain-v5"
PROGRAM_NAME = "scratch/flow-probe-domain-randomized"
CSV_SCHEMA_VERSION = "flow_probe_ns3_domain_randomization_v5"
REQUIRED_COLUMNS = {
    "schema_version",
    "config_id",
    "split",
    "group_id",
    "seed",
    "run",
    "window_index",
    "window_start_s",
    "window_end_s",
    "public_total_packets",
    "public_total_l3_bytes",
    "public_packet_length_mean_l3_bytes",
    "public_packet_length_min_l3_bytes",
    "public_packet_length_max_l3_bytes",
    "public_iat_mean_ms",
    "public_packet_rate_pps",
    "public_byte_rate_Bps",
    "supervision_measurement_noise_std_ratio",
    "supervision_capacity_start_bps",
    "supervision_capacity_end_bps",
    "supervision_capacity_integral_link_bytes",
    "supervision_queue_start_l3_bytes",
    "supervision_queue_end_l3_bytes",
    "supervision_qdisc_received_l3_bytes",
    "supervision_qdisc_dequeued_l3_bytes",
    "supervision_qdisc_dropped_before_enqueue_l3_bytes",
    "supervision_qdisc_dropped_after_dequeue_l3_bytes",
    "supervision_queue_start_packets",
    "supervision_queue_end_packets",
    "supervision_qdisc_received_packets",
    "supervision_qdisc_dequeued_packets",
    "supervision_qdisc_dropped_before_enqueue_packets",
    "supervision_qdisc_dropped_after_dequeue_packets",
    "supervision_queue_balance_residual_l3_bytes",
    "supervision_queue_balance_residual_packets",
}
PUBLIC_PREFIX = "public_"
SUPERVISION_PREFIX = "supervision_"


class DomainExperimentError(RuntimeError):
    """v5 配置、执行结果或制品不满足冻结契约。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_new_output(path: Path) -> Path:
    normalized = path.expanduser().resolve()
    if normalized.exists() or normalized.is_symlink():
        raise DomainExperimentError(f"输出目录已存在，不得覆盖：{normalized}")
    return normalized


def _load_manifest(path: Path) -> tuple[DomainConfig, ...]:
    normalized = path.expanduser().resolve()
    if not normalized.is_file():
        raise DomainExperimentError(f"配置清单不存在：{normalized}")
    configs: list[DomainConfig] = []
    with normalized.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                config = DomainConfig(**record)
            except (json.JSONDecodeError, TypeError) as error:
                raise DomainExperimentError(
                    f"配置清单第 {line_number} 行无法解析：{error}"
                ) from error
            if config.schema_version != SCHEMA_VERSION:
                raise DomainExperimentError(
                    f"配置 {config.config_id} 的模式版本不正确：{config.schema_version}"
                )
            configs.append(config)
    expected_total = sum(SPLIT_COUNTS.values())
    if len(configs) != expected_total:
        raise DomainExperimentError(
            f"冻结清单必须包含 {expected_total} 个配置，实际为 {len(configs)}"
        )
    counts = Counter(config.split for config in configs)
    if dict(counts) != SPLIT_COUNTS:
        raise DomainExperimentError(f"四类切分数量不正确：{dict(counts)}")
    config_ids = [config.config_id for config in configs]
    if len(config_ids) != len(set(config_ids)):
        raise DomainExperimentError("配置清单包含重复 config_id")
    environment_keys = [config.environment_key for config in configs]
    if len(environment_keys) != len(set(environment_keys)):
        raise DomainExperimentError("配置清单包含重复环境参数元组")
    if any(
        config.queue_model != "red"
        for config in configs
        if config.split == "out_of_range"
    ):
        raise DomainExperimentError("范围外切分必须全部使用训练未见的 RED 队列")
    if any(
        config.queue_model == "red"
        for config in configs
        if config.split != "out_of_range"
    ):
        raise DomainExperimentError("RED 队列泄漏到范围内切分")
    return tuple(configs)


def _program_arguments(config: DomainConfig, output_path: Path) -> tuple[str, ...]:
    values: tuple[tuple[str, object], ...] = (
        ("configId", config.config_id),
        ("split", config.split),
        ("seed", config.seed),
        ("run", config.run),
        ("duration", config.duration_seconds),
        ("window", config.window_seconds),
        ("trafficMode", config.traffic_mode),
        ("transport", config.transport),
        ("queueModel", config.queue_model),
        ("arrivalModel", config.arrival_model),
        ("initialCapacityMbps", config.initial_capacity_mbps),
        ("shiftedCapacityMbps", config.shifted_capacity_mbps),
        ("capacityShiftSeconds", config.capacity_shift_seconds),
        ("accessDelayMs", config.access_delay_ms),
        ("bottleneckDelayMs", config.bottleneck_delay_ms),
        ("queueLimitPackets", config.queue_limit_packets),
        ("downstreamLossRate", config.downstream_loss_rate),
        ("senderCount", config.sender_count),
        ("benignRateMbps", config.benign_rate_mbps),
        ("attackRateMbps", config.attack_rate_mbps),
        ("attackStartSeconds", config.attack_start_seconds),
        ("packetSizeBytes", config.packet_size_bytes),
        ("jitterMaxMs", config.jitter_max_ms),
        ("burstOnMeanSeconds", config.burst_on_mean_seconds),
        ("burstOffMeanSeconds", config.burst_off_mean_seconds),
        ("measurementNoiseStdRatio", config.measurement_noise_std_ratio),
        ("output", output_path),
    )
    return (PROGRAM_NAME, *(f"--{key}={value}" for key, value in values))


def _command(ns3_root: Path, config: DomainConfig, output_path: Path) -> tuple[str, ...]:
    arguments = _program_arguments(config, output_path)
    return (
        "env",
        "USER=ns3builder",
        str(ns3_root / "ns3"),
        "run",
        " ".join(shlex.quote(argument) for argument in arguments),
    )


def _validate_csv(path: Path, config: DomainConfig) -> dict[str, int | float | str]:
    if not path.is_file():
        raise DomainExperimentError(f"配置 {config.config_id} 未生成 CSV：{path}")
    with path.open("r", encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or ())
        missing = sorted(REQUIRED_COLUMNS.difference(columns))
        if missing:
            raise DomainExperimentError(
                f"配置 {config.config_id} 结果缺少字段：{', '.join(missing)}"
            )
        public_columns = {column for column in columns if column.startswith(PUBLIC_PREFIX)}
        supervision_columns = {
            column for column in columns if column.startswith(SUPERVISION_PREFIX)
        }
        if not public_columns or not supervision_columns:
            raise DomainExperimentError("公共观测与监督真值未按前缀隔离")
        rows = list(reader)
    expected_windows = int(round(config.duration_seconds / config.window_seconds))
    if len(rows) != expected_windows:
        raise DomainExperimentError(
            f"配置 {config.config_id} 应有 {expected_windows} 个窗口，实际为 {len(rows)}"
        )
    residual_violations = 0
    nonfinite_public = 0
    negative_public = 0
    for expected_index, row in enumerate(rows):
        if row["schema_version"] != CSV_SCHEMA_VERSION:
            raise DomainExperimentError(f"配置 {config.config_id} 的 CSV 模式版本不正确")
        if row["config_id"] != config.config_id or row["split"] != config.split:
            raise DomainExperimentError(f"配置 {config.config_id} 的参数标识未正确落盘")
        if int(row["window_index"]) != expected_index:
            raise DomainExperimentError(f"配置 {config.config_id} 的窗口序号不连续")
        residual_violations += int(
            int(row["supervision_queue_balance_residual_l3_bytes"]) != 0
            or int(row["supervision_queue_balance_residual_packets"]) != 0
        )
        for column in public_columns:
            value = float(row[column])
            nonfinite_public += int(not math.isfinite(value))
            negative_public += int(value < 0.0)
    if residual_violations:
        raise DomainExperimentError(
            f"配置 {config.config_id} 有 {residual_violations} 个窗口违反双守恒"
        )
    if nonfinite_public or negative_public:
        raise DomainExperimentError(
            f"配置 {config.config_id} 公共观测非法："
            f"非有限={nonfinite_public}，负数={negative_public}"
        )
    return {
        "config_id": config.config_id,
        "split": config.split,
        "window_count": len(rows),
        "public_field_count": len(public_columns),
        "supervision_field_count": len(supervision_columns),
        "residual_violation_count": residual_violations,
    }


def run_domain_experiment(
    *,
    ns3_root: Path,
    source_path: Path,
    manifest_path: Path,
    output_dir: Path,
    run_name: str,
) -> dict[str, object]:
    normalized_root = ns3_root.expanduser().resolve()
    launcher = normalized_root / "ns3"
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise DomainExperimentError(f"ns-3 启动器不可用：{launcher}")
    normalized_source = source_path.expanduser().resolve()
    compiled_source = normalized_root / "scratch" / "flow-probe-domain-randomized.cc"
    if not normalized_source.is_file() or not compiled_source.is_file():
        raise DomainExperimentError("项目源码或 ns-3 scratch 源码不存在")
    source_sha = _sha256(normalized_source)
    compiled_sha = _sha256(compiled_source)
    if source_sha != compiled_sha:
        raise DomainExperimentError(
            "项目源码与 ns-3 scratch 源码 SHA-256 不一致，禁止启动正式矩阵"
        )
    normalized_manifest = manifest_path.expanduser().resolve()
    configs = _load_manifest(normalized_manifest)
    normalized_output = _require_new_output(output_dir)
    normalized_output.mkdir(parents=True)
    csv_dir = normalized_output / "csv"
    log_dir = normalized_output / "logs"
    csv_dir.mkdir()
    log_dir.mkdir()
    copied_manifest = normalized_output / "input_config_manifest.jsonl"
    shutil.copy2(normalized_manifest, copied_manifest)

    paths = {
        "config_snapshot": normalized_output / "config_snapshot.json",
        "environment_snapshot": normalized_output / "environment_snapshot.json",
        "group_status": normalized_output / "group_status.json",
        "run_status": normalized_output / "run_status.json",
        "validation_summary": normalized_output / "validation_summary.json",
        "csv_sha256": normalized_output / "csv_sha256.json",
        "swanlab_metrics": normalized_output / "swanlab_metrics.json",
        "input_config_manifest": copied_manifest,
    }
    statuses: list[dict[str, object]] = []
    data_files: dict[str, Path] = dict(paths)
    for index, config in enumerate(configs, start=1):
        stem = f"{index:03d}-{config.config_id}"
        csv_path = csv_dir / f"{stem}.csv"
        stdout_path = log_dir / f"{stem}.stdout.log"
        stderr_path = log_dir / f"{stem}.stderr.log"
        command = _command(normalized_root, config, csv_path)
        statuses.append(
            {
                "index": index,
                "config_id": config.config_id,
                "split": config.split,
                "status": "pending",
                "returncode": None,
                "csv_path": str(csv_path),
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "command": list(command),
            }
        )
        data_files[f"csv_{index:03d}"] = csv_path
        data_files[f"stdout_{index:03d}"] = stdout_path
        data_files[f"stderr_{index:03d}"] = stderr_path

    config_snapshot = {
        "schema_version": "flow_probe_ns3_domain_experiment_config_v1",
        "run_name": run_name,
        "config_count": len(configs),
        "split_counts": SPLIT_COUNTS,
        "manifest_path": str(normalized_manifest),
        "manifest_sha256": _sha256(normalized_manifest),
        "source_path": str(normalized_source),
        "source_sha256": source_sha,
        "compiled_source_path": str(compiled_source),
        "ns3_root": str(normalized_root),
        "output_dir": str(normalized_output),
        "program": PROGRAM_NAME,
        "public_input_prefix": PUBLIC_PREFIX,
        "supervision_only_prefix": SUPERVISION_PREFIX,
    }
    environment_snapshot = {
        "captured_at": _utc_now(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "working_directory": str(Path.cwd()),
    }
    run_status: dict[str, object] = {
        "status": "running",
        "stage": "initialized",
        "started_at": _utc_now(),
        "updated_at": _utc_now(),
        "completed_config_count": 0,
        "failed_config_count": 0,
    }
    validation_summaries: list[dict[str, int | float | str]] = []
    csv_hashes: list[dict[str, object]] = []
    metric_series: list[dict[str, object]] = []

    def persist() -> None:
        run_status["updated_at"] = _utc_now()
        _write_json(paths["group_status"], {"groups": statuses})
        _write_json(paths["run_status"], run_status)
        _write_json(paths["validation_summary"], {"groups": validation_summaries})
        _write_json(paths["csv_sha256"], {"files": csv_hashes})
        _write_json(paths["swanlab_metrics"], metric_series)

    _write_json(paths["config_snapshot"], config_snapshot)
    _write_json(paths["environment_snapshot"], environment_snapshot)
    persist()
    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": run_name,
            "description": "任务十七唯一一次 ns-3 v5 域随机化正式矩阵",
            "mode": "online",
            "tags": ["task17", "ns3-v5", "observability"],
        }
    )

    with capture_console_log(normalized_output / "console.log"):
        print(f"开始任务十七 v5 矩阵：{len(configs)} 个独立配置")
        with swanlab_run(
            settings,
            phase=PHASE,
            config=config_snapshot,
            artifact_dir=normalized_output,
            data_files=data_files,
        ) as swanlab:
            try:
                for config, status in zip(configs, statuses, strict=True):
                    index = int(status["index"])
                    status["status"] = "running"
                    status["started_at"] = _utc_now()
                    run_status["stage"] = f"running-{index:03d}"
                    persist()
                    print(
                        f"运行 {index}/{len(configs)}：{config.config_id}，"
                        f"{config.queue_model}/{config.transport}/{config.arrival_model}"
                    )
                    completed = subprocess.run(
                        status["command"],
                        cwd=normalized_root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    stdout_path = Path(str(status["stdout_path"]))
                    stderr_path = Path(str(status["stderr_path"]))
                    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
                    stderr_path.write_text(completed.stderr or "", encoding="utf-8")
                    status["returncode"] = completed.returncode
                    if completed.returncode != 0:
                        raise DomainExperimentError(
                            f"配置 {config.config_id} 失败，退出状态 {completed.returncode}"
                        )
                    csv_path = Path(str(status["csv_path"]))
                    validation = _validate_csv(csv_path, config)
                    validation_summaries.append(validation)
                    csv_hashes.append(
                        {
                            "config_id": config.config_id,
                            "path": str(csv_path),
                            "size_bytes": csv_path.stat().st_size,
                            "sha256": _sha256(csv_path),
                        }
                    )
                    status["status"] = "finished"
                    status["finished_at"] = _utc_now()
                    run_status["completed_config_count"] = index
                    metrics = {
                        "ns3_v5/completed_config_count": index,
                        "ns3_v5/failed_config_count": 0,
                        "ns3_v5/total_window_count": sum(
                            int(item["window_count"]) for item in validation_summaries
                        ),
                        "ns3_v5/residual_violation_count": sum(
                            int(item["residual_violation_count"])
                            for item in validation_summaries
                        ),
                    }
                    metric_series.append({"step": index, "metrics": metrics})
                    persist()
                    swanlab.log(metrics, step=index)
                run_status.update(
                    {
                        "status": "finished",
                        "stage": "completed",
                        "finished_at": _utc_now(),
                        "completed_config_count": len(configs),
                    }
                )
                persist()
            except BaseException as error:
                current = int(run_status.get("completed_config_count", 0))
                failed_index = min(current, len(statuses) - 1)
                statuses[failed_index]["status"] = "failed"
                statuses[failed_index]["error"] = str(error)
                statuses[failed_index]["finished_at"] = _utc_now()
                run_status.update(
                    {
                        "status": "crashed",
                        "stage": "crashed",
                        "failed_config_count": 1,
                        "error": str(error),
                        "finished_at": _utc_now(),
                    }
                )
                persist()
                print(f"任务十七 v5 矩阵失败：{error}", file=sys.stderr)
                raise

    manifest = json.loads(
        (normalized_output / "artifact_manifest.json").read_text(encoding="utf-8")
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="运行任务十七 ns-3 v5 域随机化矩阵")
    parser.add_argument("--ns3-root", type=Path, required=True)
    parser.add_argument("--source-path", type=Path, required=True)
    parser.add_argument("--manifest-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        run_domain_experiment(
            ns3_root=args.ns3_root,
            source_path=args.source_path,
            manifest_path=args.manifest_path,
            output_dir=args.output_dir,
            run_name=args.run_name,
        )
    except (DomainExperimentError, OSError) as error:
        print(f"任务十七 v5 运行失败：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
