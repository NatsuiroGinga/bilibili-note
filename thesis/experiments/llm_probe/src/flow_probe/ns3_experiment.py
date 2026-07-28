"""运行可复现的 ns-3 队列真值矩阵并记录 SwanLab 制品。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from flow_probe.ns3_truth import DEFAULT_WINDOW_COUNT, TOPOLOGY_ID, validate_ns3_truth_paths
from flow_probe.tracking import (
    REQUIRED_SWANLAB_PROJECT,
    REQUIRED_SWANLAB_WORKSPACE,
    TrackingSettings,
    capture_console_log,
    swanlab_run,
)

FORMAL_SCENARIOS = (
    "benign-low",
    "benign-high",
    "benign-capacity-shift",
    "benign-random-loss",
    "dos-udp-medium",
    "dos-udp-high",
    "dos-udp-capacity-shift",
)
DEFAULT_SEEDS = (42, 43, 44)
RUN_NUMBER = 1
PHASE = "ns3-matrix"
_RUN_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")

Executor = Callable[..., subprocess.CompletedProcess[str]]
Validator = Callable[[Sequence[Path]], dict[str, object]]


class MatrixConfigError(ValueError):
    """矩阵参数或路径不满足正式运行约束。"""


class NS3MatrixRunError(RuntimeError):
    """矩阵运行期间发生不可恢复错误。"""


class NS3GroupExecutionError(NS3MatrixRunError):
    """单个 ns-3 组以非零状态退出。"""

    def __init__(self, group_id: str, returncode: int) -> None:
        self.group_id = group_id
        self.returncode = returncode
        super().__init__(f"ns-3 组 {group_id} 执行失败，退出状态为 {returncode}")


@dataclass(frozen=True)
class MatrixGroup:
    """一个场景和随机种子的可追溯执行计划。"""

    index: int
    scenario: str
    seed: int
    run: int
    group_id: str
    csv_path: Path
    stdout_path: Path
    stderr_path: Path
    command: tuple[str, ...]


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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_scenarios(scenarios: Sequence[str]) -> tuple[str, ...]:
    requested = tuple(scenarios)
    if not requested:
        raise MatrixConfigError("场景列表不能为空")
    if any(not isinstance(scenario, str) or not scenario.strip() for scenario in requested):
        raise MatrixConfigError("场景名必须为非空字符串")
    cleaned = tuple(scenario.strip() for scenario in requested)
    if len(cleaned) != len(set(cleaned)):
        raise MatrixConfigError("场景列表包含重复值")
    unknown = sorted(set(cleaned).difference(FORMAL_SCENARIOS))
    if unknown:
        raise MatrixConfigError(f"场景名无效：{', '.join(unknown)}")
    requested_set = set(cleaned)
    return tuple(scenario for scenario in FORMAL_SCENARIOS if scenario in requested_set)


def _normalize_seeds(seeds: Sequence[int]) -> tuple[int, ...]:
    requested = tuple(seeds)
    if not requested:
        raise MatrixConfigError("随机种子列表不能为空")
    if any(isinstance(seed, bool) or not isinstance(seed, int) for seed in requested):
        raise MatrixConfigError("随机种子必须为整数")
    if any(seed <= 0 or seed > 4_294_967_295 for seed in requested):
        raise MatrixConfigError("随机种子必须位于 1 至 4294967295")
    if len(requested) != len(set(requested)):
        raise MatrixConfigError("随机种子列表包含重复值")
    return requested


def _normalize_ns3_root(ns3_root: Path) -> Path:
    normalized = Path(ns3_root).expanduser().resolve()
    if not normalized.is_dir():
        raise MatrixConfigError(f"ns-3 根目录不存在或不是目录：{normalized}")
    launcher = normalized / "ns3"
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise MatrixConfigError(f"ns-3 启动器不存在或不可执行：{launcher}")
    return normalized


def _normalize_run_name(run_name: str) -> str:
    cleaned = str(run_name).strip()
    if not _RUN_NAME_PATTERN.fullmatch(cleaned):
        raise MatrixConfigError(
            "运行名称必须以字母或数字开头，且只能包含字母、数字、点、下划线和连字符"
        )
    return cleaned


def build_matrix_plan(
    ns3_root: Path,
    output_dir: Path,
    scenarios: Sequence[str] = FORMAL_SCENARIOS,
    seeds: Sequence[int] = DEFAULT_SEEDS,
) -> tuple[MatrixGroup, ...]:
    """按固定场景顺序展开稳定且唯一的执行计划。"""
    normalized_root = _normalize_ns3_root(ns3_root)
    normalized_output = Path(output_dir).expanduser().resolve()
    normalized_scenarios = _normalize_scenarios(scenarios)
    normalized_seeds = _normalize_seeds(seeds)
    groups: list[MatrixGroup] = []
    for scenario in normalized_scenarios:
        for seed in normalized_seeds:
            index = len(groups) + 1
            stem = f"{index:02d}-{scenario}-seed{seed}-run{RUN_NUMBER}"
            csv_path = normalized_output / "csv" / f"{stem}.csv"
            program_arguments = (
                "scratch/flow-probe-queue-truth",
                f"--scenario={scenario}",
                f"--output={csv_path}",
                f"--seed={seed}",
                f"--run={RUN_NUMBER}",
            )
            groups.append(
                MatrixGroup(
                    index=index,
                    scenario=scenario,
                    seed=seed,
                    run=RUN_NUMBER,
                    group_id=(f"{TOPOLOGY_ID}|{scenario}|seed{seed}|run{RUN_NUMBER}"),
                    csv_path=csv_path,
                    stdout_path=normalized_output / "logs" / f"{stem}.stdout.log",
                    stderr_path=normalized_output / "logs" / f"{stem}.stderr.log",
                    command=(
                        "env",
                        "USER=ns3builder",
                        str(normalized_root / "ns3"),
                        "run",
                        " ".join(shlex.quote(argument) for argument in program_arguments),
                    ),
                )
            )
    return tuple(groups)


def _summary_metrics(
    summaries: Sequence[dict[str, object]],
    *,
    completed_group_count: int,
    failed_group_count: int,
) -> dict[str, int | float]:
    def total(field: str) -> int:
        return sum(int(summary.get(field, 0)) for summary in summaries)

    return {
        "ns3/completed_group_count": completed_group_count,
        "ns3/failed_group_count": failed_group_count,
        "ns3/total_window_count": total("total_window_count"),
        "ns3/qdisc_drop_l3_bytes": total("qdisc_drop_l3_bytes"),
        "ns3/downstream_error_loss_ppp_frame_bytes": total("downstream_error_loss_ppp_frame_bytes"),
        "ns3/nonzero_residual_window_count": total("nonzero_l3_residual_count")
        + total("nonzero_packet_residual_count"),
    }


def _validate_aggregate(summary: dict[str, object], group_count: int) -> None:
    expected_windows = group_count * DEFAULT_WINDOW_COUNT
    actual_groups = int(summary.get("group_count", -1))
    actual_windows = int(summary.get("total_window_count", -1))
    if actual_groups != group_count or actual_windows != expected_windows:
        raise NS3MatrixRunError(
            "矩阵验证汇总不完整："
            f"应有 {group_count} 个组和 {expected_windows} 个窗口，"
            f"实际为 {actual_groups} 个组和 {actual_windows} 个窗口"
        )
    nonzero_l3 = int(summary.get("nonzero_l3_residual_count", -1))
    nonzero_packets = int(summary.get("nonzero_packet_residual_count", -1))
    if nonzero_l3 != 0 or nonzero_packets != 0:
        raise NS3MatrixRunError(f"矩阵双残差审计失败：L3={nonzero_l3}，包={nonzero_packets}")


def run_ns3_matrix(
    *,
    ns3_root: Path,
    source_path: Path,
    output_dir: Path,
    run_name: str,
    scenarios: Sequence[str] = FORMAL_SCENARIOS,
    seeds: Sequence[int] = DEFAULT_SEEDS,
    executor: Executor = subprocess.run,
    validator: Validator = validate_ns3_truth_paths,
) -> dict[str, object]:
    """执行矩阵，并在成功或失败时保存完整的本地追溯制品。"""
    normalized_root = _normalize_ns3_root(ns3_root)
    normalized_source = Path(source_path).expanduser().resolve()
    if not normalized_source.is_file():
        raise MatrixConfigError(f"queue_truth_scenario.cc 源码不存在：{normalized_source}")
    normalized_output = Path(output_dir).expanduser().resolve()
    if normalized_output.exists() or normalized_output.is_symlink():
        raise MatrixConfigError(f"输出目录已存在，不得覆盖或复用：{normalized_output}")
    normalized_run_name = _normalize_run_name(run_name)
    groups = build_matrix_plan(
        normalized_root,
        normalized_output,
        scenarios=scenarios,
        seeds=seeds,
    )

    normalized_output.mkdir(parents=True)
    (normalized_output / "csv").mkdir()
    (normalized_output / "logs").mkdir()
    (normalized_output / "swanlog" / PHASE).mkdir(parents=True)

    paths = {
        "config_snapshot": normalized_output / "config_snapshot.json",
        "environment_snapshot": normalized_output / "environment_snapshot.json",
        "source_sha256": normalized_output / "source_sha256.json",
        "csv_sha256": normalized_output / "csv_sha256.json",
        "group_status": normalized_output / "group_status.json",
        "run_status": normalized_output / "run_status.json",
        "validation_summary": normalized_output / "validation_summary.json",
        "swanlab_metrics": normalized_output / "swanlab_metrics.json",
    }
    data_files = dict(paths)
    for group in groups:
        suffix = f"{group.index:02d}"
        data_files[f"csv_{suffix}"] = group.csv_path
        data_files[f"stdout_log_{suffix}"] = group.stdout_path
        data_files[f"stderr_log_{suffix}"] = group.stderr_path

    config_snapshot = {
        "schema_version": "flow_probe_ns3_matrix_config_v1",
        "run_name": normalized_run_name,
        "ns3_root": str(normalized_root),
        "source_path": str(normalized_source),
        "output_dir": str(normalized_output),
        "scenarios": list(_normalize_scenarios(scenarios)),
        "seeds": list(_normalize_seeds(seeds)),
        "run": RUN_NUMBER,
        "expected_windows_per_group": DEFAULT_WINDOW_COUNT,
        "groups": [
            {
                "index": group.index,
                "scenario": group.scenario,
                "seed": group.seed,
                "run": group.run,
                "group_id": group.group_id,
                "csv_path": str(group.csv_path),
                "command": list(group.command),
            }
            for group in groups
        ],
    }
    environment_snapshot = {
        "schema_version": "flow_probe_ns3_matrix_environment_v1",
        "captured_at": _utc_now(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "working_directory": str(Path.cwd()),
        "ns3_root": str(normalized_root),
        "ns3_launcher": str(normalized_root / "ns3"),
        "enforced_ns3_user": "ns3builder",
    }
    source_hash = {
        "schema_version": "flow_probe_ns3_source_sha256_v1",
        "path": str(normalized_source),
        "size_bytes": normalized_source.stat().st_size,
        "sha256": _file_sha256(normalized_source),
    }
    csv_hashes: dict[str, object] = {
        "schema_version": "flow_probe_ns3_csv_sha256_v1",
        "files": [],
    }
    group_status: dict[str, object] = {
        "schema_version": "flow_probe_ns3_group_status_v1",
        "groups": [
            {
                "index": group.index,
                "group_id": group.group_id,
                "scenario": group.scenario,
                "seed": group.seed,
                "run": group.run,
                "status": "pending",
                "returncode": None,
                "csv_path": str(group.csv_path),
                "stdout_path": str(group.stdout_path),
                "stderr_path": str(group.stderr_path),
                "command": list(group.command),
            }
            for group in groups
        ],
    }
    run_status: dict[str, object] = {
        "schema_version": "flow_probe_ns3_run_status_v1",
        "status": "running",
        "stage": "initialized",
        "started_at": _utc_now(),
        "updated_at": _utc_now(),
        "completed_group_count": 0,
        "failed_group_count": 0,
    }
    validation_summary: dict[str, object] = {
        "schema_version": "flow_probe_ns3_matrix_validation_v1",
        "groups": [],
        "aggregate": None,
    }
    metric_series: list[dict[str, object]] = []

    _write_json(paths["config_snapshot"], config_snapshot)
    _write_json(paths["environment_snapshot"], environment_snapshot)
    _write_json(paths["source_sha256"], source_hash)
    _write_json(paths["csv_sha256"], csv_hashes)
    _write_json(paths["group_status"], group_status)
    _write_json(paths["run_status"], run_status)
    _write_json(paths["validation_summary"], validation_summary)
    _write_json(paths["swanlab_metrics"], metric_series)

    settings = TrackingSettings.from_mapping(
        {
            "project": REQUIRED_SWANLAB_PROJECT,
            "workspace": REQUIRED_SWANLAB_WORKSPACE,
            "run_name": normalized_run_name,
            "description": "正式 ns-3 队列真值矩阵与逐组验证",
            "mode": "online",
            "tags": ["ns3-truth", "queue-matrix", "pinn-data"],
        }
    )
    summaries: list[dict[str, object]] = []

    def persist_runtime_state() -> None:
        run_status["updated_at"] = _utc_now()
        _write_json(paths["csv_sha256"], csv_hashes)
        _write_json(paths["group_status"], group_status)
        _write_json(paths["run_status"], run_status)
        _write_json(paths["validation_summary"], validation_summary)
        _write_json(paths["swanlab_metrics"], metric_series)

    with capture_console_log(normalized_output / "console.log"):
        print(f"开始 ns-3 矩阵：{len(groups)} 个组，输出目录 {normalized_output}")
        with swanlab_run(
            settings,
            phase=PHASE,
            config=config_snapshot,
            artifact_dir=normalized_output,
            data_files=data_files,
        ) as swanlab:
            try:
                records = group_status["groups"]
                assert isinstance(records, list)
                for group, record in zip(groups, records, strict=True):
                    assert isinstance(record, dict)
                    record["status"] = "running"
                    record["started_at"] = _utc_now()
                    run_status["stage"] = f"running-group-{group.index:02d}"
                    persist_runtime_state()
                    print(
                        f"运行组 {group.index}/{len(groups)}："
                        f"{group.scenario}，seed={group.seed}，run={group.run}"
                    )
                    try:
                        completed = executor(
                            list(group.command),
                            cwd=normalized_root,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                    except OSError as error:
                        group.stdout_path.write_text("", encoding="utf-8")
                        group.stderr_path.write_text(
                            f"无法启动 ns-3 子进程：{error}\n", encoding="utf-8"
                        )
                        failure = NS3MatrixRunError(f"无法启动 ns-3 组 {group.group_id}：{error}")
                        record["status"] = "failed"
                        record["error"] = str(failure)
                        record["finished_at"] = _utc_now()
                        run_status["failed_group_count"] = 1
                        run_status["failed_group_id"] = group.group_id
                        metrics = _summary_metrics(
                            summaries,
                            completed_group_count=len(summaries),
                            failed_group_count=1,
                        )
                        metric_series.append({"step": group.index, "metrics": metrics})
                        persist_runtime_state()
                        swanlab.log(metrics, step=group.index)
                        raise failure from error

                    stdout = completed.stdout or ""
                    stderr = completed.stderr or ""
                    group.stdout_path.write_text(stdout, encoding="utf-8")
                    group.stderr_path.write_text(stderr, encoding="utf-8")
                    record["returncode"] = int(completed.returncode)
                    if group.csv_path.is_file():
                        files = csv_hashes["files"]
                        assert isinstance(files, list)
                        files.append(
                            {
                                "group_id": group.group_id,
                                "path": str(group.csv_path),
                                "size_bytes": group.csv_path.stat().st_size,
                                "sha256": _file_sha256(group.csv_path),
                            }
                        )
                    if completed.returncode != 0:
                        failure = NS3GroupExecutionError(group.group_id, int(completed.returncode))
                        record["status"] = "failed"
                        record["error"] = str(failure)
                        record["finished_at"] = _utc_now()
                        run_status["failed_group_count"] = 1
                        run_status["failed_group_id"] = group.group_id
                        metrics = _summary_metrics(
                            summaries,
                            completed_group_count=len(summaries),
                            failed_group_count=1,
                        )
                        metric_series.append({"step": group.index, "metrics": metrics})
                        persist_runtime_state()
                        swanlab.log(metrics, step=group.index)
                        raise failure
                    if not group.csv_path.is_file():
                        raise NS3MatrixRunError(
                            f"ns-3 组 {group.group_id} 未生成预期 CSV：{group.csv_path}"
                        )

                    summary = validator([group.csv_path])
                    summaries.append(summary)
                    validation_groups = validation_summary["groups"]
                    assert isinstance(validation_groups, list)
                    validation_groups.append({"group_id": group.group_id, "summary": summary})
                    record["status"] = "finished"
                    record["validation_status"] = summary.get("validation_status")
                    record["finished_at"] = _utc_now()
                    run_status["completed_group_count"] = len(summaries)
                    metrics = _summary_metrics(
                        summaries,
                        completed_group_count=len(summaries),
                        failed_group_count=0,
                    )
                    metric_series.append({"step": group.index, "metrics": metrics})
                    persist_runtime_state()
                    swanlab.log(metrics, step=group.index)

                aggregate = validator([group.csv_path for group in groups])
                _validate_aggregate(aggregate, len(groups))
                validation_summary["aggregate"] = aggregate
                final_metrics = _summary_metrics(
                    [aggregate],
                    completed_group_count=len(groups),
                    failed_group_count=0,
                )
                final_step = len(groups) + 1
                metric_series.append({"step": final_step, "metrics": final_metrics})
                persist_runtime_state()
                swanlab.log(final_metrics, step=final_step)
                run_status.update(
                    {
                        "status": "finished",
                        "stage": "completed",
                        "completed_group_count": len(groups),
                        "failed_group_count": 0,
                        "finished_at": _utc_now(),
                    }
                )
                persist_runtime_state()
            except BaseException as error:
                run_status["status"] = "crashed"
                run_status["stage"] = "crashed"
                run_status["error"] = str(error)
                run_status["finished_at"] = _utc_now()
                persist_runtime_state()
                print(f"ns-3 矩阵失败：{error}", file=sys.stderr)
                raise

        manifest_path = normalized_output / "artifact_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        return manifest


def _parse_csv_seeds(raw: str) -> tuple[int, ...]:
    parts = tuple(part.strip() for part in raw.split(","))
    if not parts or any(not part for part in parts):
        raise MatrixConfigError("随机种子列表必须是逗号分隔的非空整数")
    try:
        return _normalize_seeds(tuple(int(part) for part in parts))
    except ValueError as error:
        raise MatrixConfigError("随机种子列表包含非整数值") from error


def _parse_csv_scenarios(raw: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for part in raw.split(","))
    if not parts or any(not part for part in parts):
        raise MatrixConfigError("场景列表必须是逗号分隔的非空名称")
    return _normalize_scenarios(parts)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行正式 ns-3 队列真值矩阵")
    parser.add_argument("--ns3-root", type=Path, required=True)
    parser.add_argument("--source-path", type=Path, default=Path("ns3/queue_truth_scenario.cc"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--scenarios", default=",".join(FORMAL_SCENARIOS))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        run_ns3_matrix(
            ns3_root=args.ns3_root,
            source_path=args.source_path,
            output_dir=args.output_dir,
            run_name=args.run_name,
            seeds=_parse_csv_seeds(args.seeds),
            scenarios=_parse_csv_scenarios(args.scenarios),
        )
    except MatrixConfigError as error:
        print(f"ns-3 矩阵参数无效：{error}", file=sys.stderr)
        return 2
    except NS3GroupExecutionError as error:
        print(f"ns-3 矩阵运行失败：{error}", file=sys.stderr)
        return error.returncode if 0 < error.returncode <= 255 else 1
    except (NS3MatrixRunError, OSError) as error:
        print(f"ns-3 矩阵运行失败：{error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
