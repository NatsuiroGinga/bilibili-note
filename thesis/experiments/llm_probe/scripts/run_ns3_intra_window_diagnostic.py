"""ns-3 窗内观测诊断批量驱动。

设计背景见
``.superpowers/sdd/2026-08-07-ns3窗内观测诊断-task_plan/task-3.5-brief.md``：
正式 v3 冻结矩阵并行运行器
``flow_probe.r2_ns3_protocol_dynamics_v2_parallel_runner`` 硬绑定 v3 输出
目录身份、v2 编译源与可执行文件名、以及绑定 v3 场景哈希的字段闭合校验，
无法转指向诊断场景使用，且用户已裁定不得为此改动该正式运行器（它正是
产出 v3 冻结矩阵的代码）。

因此本驱动是一份独立的薄编排脚本，只负责：加载冻结清单、按 G-diag
子集条件筛选、并发调度单次运行、汇总运行状态。单次运行职责（写
``config.json``、调用诊断可执行文件、写 ``main.csv``/
``tcp-sender-windows.csv``、目录命名与防覆盖）完全复用
``flow_probe.r2_ns3_tcp_truth_v2_runner._run_one``，本驱动不重新实现
ns-3 命令行构造或清单字段语义解析。

诊断产物不进入任何正式冻结矩阵，因此本驱动不做字段闭合校验、不写正式
收据、不支持续跑；单个运行失败也不得中断整批，失败原因记入根级
``run-state.json`` 的失败清单。
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Final

from flow_probe.r2_ns3_protocol_matrix import ProtocolRunConfig
from flow_probe.r2_ns3_protocol_runner import _load_manifest
from flow_probe.r2_ns3_tcp_truth_v2_runner import (
    TcpTruthV2Error,
    _file_sha256,
    _run_one,
    _utc_now,
    _write_json_atomic,
)

logger = logging.getLogger(__name__)

# analyze_ns3_intra_window_diagnostic.py 与本脚本同在 scripts/ 目录，不是
# 已安装包的一部分，需要显式把 scripts/ 加入 sys.path 才能按模块名导入。
_SCRIPTS_ROOT = Path(__file__).resolve().parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from analyze_ns3_intra_window_diagnostic import MIN_LOAD_RATIO  # noqa: E402

PROJECT_ROOT: Final = _SCRIPTS_ROOT.parent
DEFAULT_MANIFEST_PATH: Final = (
    PROJECT_ROOT / "runs/data-freeze-configs/r2-protocol-v1/ns3-config-manifest.jsonl"
)
DEFAULT_CONTRACT_PATH: Final = PROJECT_ROOT / "configs/r2_ns3_tcp_truth_v2_contract.json"
DEFAULT_SCENARIO_SOURCE_PATH: Final = (
    PROJECT_ROOT / "scripts/ns3/r2_protocol_dynamics_v3_diag_scenario.cc"
)
DEFAULT_WORKERS: Final = 8
DRIVER_STATE_SCHEMA: Final = "flow_probe_r2_ns3_intra_window_diagnostic_driver_state_v1"


def select_runs(
    runs: Sequence[ProtocolRunConfig], *, only_gdiag_subset: bool
) -> list[tuple[int, ProtocolRunConfig]]:
    """按 G-diag 子集条件筛选清单运行，保留原始清单序号。

    G-diag 子集阈值直接复用
    ``analyze_ns3_intra_window_diagnostic.MIN_LOAD_RATIO``，不在本模块
    独立定义，避免分析脚本与本驱动的判据阈值发生漂移。

    Args:
        runs: 冻结清单加载后的完整运行序列。
        only_gdiag_subset: 为真时只保留 ``traffic_mode == "dos"`` 且
            ``offered_load_ratio`` 达到 MIN_LOAD_RATIO（含等号）的运行；
            为假时原样返回全部运行。

    Returns:
        ``(原始清单序号, 运行配置)`` 元组列表，按清单原始顺序排列。序号
        用于驱动生成稳定、可追溯的运行目录标识（``{index:04d}-{transport}``），
        与 physics_group_sha256 一起唯一定位运行目录，避免同一物理组的
        TCP/UDP 配对争用同一目录。
    """
    indexed = list(enumerate(runs))
    if not only_gdiag_subset:
        return indexed
    return [
        (index, run)
        for index, run in indexed
        if run.traffic_mode == "dos" and run.offered_load_ratio >= MIN_LOAD_RATIO
    ]


def _execute_one(
    ns3_root: Path,
    runs_root: Path,
    manifest_index: int,
    run: ProtocolRunConfig,
    contract_sha: str,
    source_sha: str,
    executable: Path,
) -> tuple[int, str, ProtocolRunConfig, dict[str, object] | None, str | None]:
    """执行单个诊断运行，把失败转换为可序列化记录而不向上抛出。

    诊断矩阵包含多达数百个独立 ns-3 运行，任一运行的场景断言失败、
    subprocess 启动失败或收据校验失败都不得中断其余运行，因此这里捕获
    ``_run_one`` 已知会抛出的异常类型：``TcpTruthV2Error`` 覆盖目录冲突、
    收据/CSV 校验失败与非零退出码；``OSError`` 覆盖进程启动或磁盘写入
    失败；``subprocess.SubprocessError`` 覆盖子进程调度异常。除此之外的
    异常视为驱动自身的编程错误，不吞掉，交给调用方直接崩溃暴露。

    Args:
        ns3_root: 已安装 ns-3 的根目录。
        runs_root: 本次批量运行的运行目录根（``<output_root>/runs``）。
        manifest_index: 该运行在冻结清单中的原始位置。
        run: 该运行的协议配置。
        contract_sha: TCP 真值 v2 合同文件的 SHA-256。
        source_sha: 诊断场景源文件的 SHA-256，仅作收据留痕。
        executable: 已编译的诊断场景可执行文件。

    Returns:
        ``(清单序号, coverage 标识, 运行配置, 成功收据或None, 失败原因或None)``。
    """
    coverage = f"{manifest_index:04d}-{run.transport_family.lower()}"
    try:
        receipt = _run_one(
            ns3_root, runs_root, coverage, run, contract_sha, source_sha, executable
        )
    except (TcpTruthV2Error, OSError, subprocess.SubprocessError) as error:
        logger.error("运行 %s（清单第%d项）失败：%s", coverage, manifest_index, error)
        return manifest_index, coverage, run, None, str(error)
    return manifest_index, coverage, run, receipt, None


def run_diagnostic_matrix(
    *,
    ns3_root: Path,
    executable: Path,
    output_root: Path,
    manifest_path: Path,
    contract_path: Path,
    scenario_source_path: Path,
    workers: int,
    only_gdiag_subset: bool,
    queue_trace_interval_ms: int,
) -> dict[str, object]:
    """加载清单、按 G-diag 子集筛选、并发调度 ``_run_one``、写出诊断运行状态。

    本函数只负责编排：清单加载复用
    ``flow_probe.r2_ns3_protocol_runner._load_manifest``，单次运行复用
    ``flow_probe.r2_ns3_tcp_truth_v2_runner._run_one``，不重新解析清单
    字段语义或重写 ns-3 命令行构造。诊断产物不进入任何正式冻结矩阵，
    因此本函数不做字段闭合校验、不写正式收据、不支持续跑。

    Args:
        ns3_root: 已安装 ns-3 3.48 的根目录。
        executable: 已编译的诊断场景可执行文件，须位于 ns3_root 内且
            可执行（由 ``_run_one`` 逐运行校验）。
        output_root: 诊断输出根目录；不得已存在。
        manifest_path: 冻结协议清单 JSONL 路径。
        contract_path: TCP 真值 v2 合同 JSON 路径，用于派生
            ``contract_sha256``（写入每个运行的窗口 CSV 并被
            ``_run_one`` 内部校验）。
        scenario_source_path: 诊断场景 C++ 源文件路径，用于派生
            ``scenario_source_sha256``（仅作收据留痕，不参与校验）。
        workers: 线程池并发度，必须为正整数。
        only_gdiag_subset: 是否只运行 G-diag 子集。
        queue_trace_interval_ms: 队列轨迹采样间隔毫秒；当前只接受0，
            非零值需要向诊断场景透传 ``_run_one`` 未暴露的额外 ns-3
            CLI 参数，属于已知遗留限制（见任务报告）。

    Returns:
        写入根级 ``run-state.json`` 的同一份状态字典。

    Raises:
        ValueError: workers 非正整数，或 queue_trace_interval_ms 非零。
        TcpTruthV2Error: 输出根已存在，或 G-diag 子集筛选结果为空。
        OSError: 清单、合同或场景源文件不可读，或输出根无法创建。
    """
    if workers <= 0:
        raise ValueError("workers 必须为正整数")
    if queue_trace_interval_ms != 0:
        raise ValueError(
            "queue_trace_interval_ms 当前只接受默认值0；"
            "_run_one 是冻结代码，不接受额外 ns-3 CLI 透传，"
            "如需队列轨迹请对单个运行直接调用诊断可执行文件"
        )
    if output_root.exists() or output_root.is_symlink():
        raise TcpTruthV2Error(f"诊断输出根已存在，禁止覆盖：{output_root}")

    contract_sha = _file_sha256(contract_path)
    source_sha = _file_sha256(scenario_source_path)
    runs = _load_manifest(manifest_path)
    selected = select_runs(runs, only_gdiag_subset=only_gdiag_subset)
    if not selected:
        raise TcpTruthV2Error("G-diag 子集筛选结果为空，无法调度任何运行")

    output_root.mkdir(parents=True)
    runs_root = output_root / "runs"
    runs_root.mkdir()

    state: dict[str, object] = {
        "schema_version": DRIVER_STATE_SCHEMA,
        "status": "running",
        "only_gdiag_subset": only_gdiag_subset,
        "min_load_ratio_threshold": MIN_LOAD_RATIO,
        "worker_count": workers,
        "planned_run_count": len(selected),
        "completed_run_count": 0,
        "failed_run_count": 0,
        "manifest_path": str(manifest_path),
        "manifest_run_count": len(runs),
        "contract_path": str(contract_path),
        "contract_sha256": contract_sha,
        "scenario_source_path": str(scenario_source_path),
        "scenario_source_sha256": source_sha,
        "ns3_root": str(ns3_root),
        "executable": str(executable),
        "queue_trace_interval_ms": queue_trace_interval_ms,
        "failures": [],
        "started_at": _utc_now(),
    }
    _write_json_atomic(output_root / "run-state.json", state)

    completed = 0
    failures: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="ns3-diag") as executor:
        futures = [
            executor.submit(
                _execute_one,
                ns3_root,
                runs_root,
                manifest_index,
                run,
                contract_sha,
                source_sha,
                executable,
            )
            for manifest_index, run in selected
        ]
        for future in as_completed(futures):
            manifest_index, coverage, run, receipt, error = future.result()
            if error is None:
                completed += 1
            else:
                failures.append(
                    {
                        "manifest_index": manifest_index,
                        "coverage": coverage,
                        "physics_group_sha256": run.physics_group_sha256,
                        "transport_family": run.transport_family,
                        "error": error,
                    }
                )
            state["completed_run_count"] = completed
            state["failed_run_count"] = len(failures)
            state["failures"] = sorted(
                failures, key=lambda item: int(item["manifest_index"])
            )
            state["updated_at"] = _utc_now()
            _write_json_atomic(output_root / "run-state.json", state)

    state["status"] = "finished" if not failures else "partial"
    state["finished_at"] = _utc_now()
    _write_json_atomic(output_root / "run-state.json", state)
    return state


def _resolve_path(value: Path) -> Path:
    """展开用户目录并解析为绝对路径，不对存在性做假设。"""
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    """构造诊断驱动命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="独立调度 ns-3 窗内观测诊断场景的批量运行驱动，"
        "不复用也不修改正式 v3 冻结矩阵并行运行器"
    )
    parser.add_argument(
        "--ns3-root", type=Path, required=True, help="已安装 ns-3 3.48 的根目录"
    )
    parser.add_argument(
        "--executable",
        type=Path,
        required=True,
        help="已编译的诊断场景可执行文件路径（须位于 ns3-root 内）",
    )
    parser.add_argument(
        "--output-root", type=Path, required=True, help="诊断输出根目录，不得已存在"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="冻结协议清单 JSONL 路径，默认正式冻结清单",
    )
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
        help="TCP 真值 v2 合同 JSON 路径",
    )
    parser.add_argument(
        "--scenario-source",
        type=Path,
        default=DEFAULT_SCENARIO_SOURCE_PATH,
        help="诊断场景 C++ 源文件路径，仅用于收据留痕的来源哈希",
    )
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS, help="线程池并发度，默认8"
    )
    parser.add_argument(
        "--only-gdiag-subset",
        action="store_true",
        help="只运行 G-diag 子集（dos 且 offered_load_ratio 达到冻结阈值），"
        "默认不开启（运行全部清单）",
    )
    parser.add_argument(
        "--queue-trace-interval-ms",
        type=int,
        default=0,
        help="队列轨迹采样间隔毫秒；当前只接受默认值0",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """命令行入口：解析参数、调度诊断矩阵、打印并返回退出码。

    Args:
        argv: 命令行参数；为 ``None`` 时使用 ``sys.argv``。

    Returns:
        全部运行成功时为0；出现任一失败运行或前置校验失败时为非零。
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    try:
        state = run_diagnostic_matrix(
            ns3_root=_resolve_path(args.ns3_root),
            executable=_resolve_path(args.executable),
            output_root=_resolve_path(args.output_root),
            manifest_path=_resolve_path(args.manifest),
            contract_path=_resolve_path(args.contract_path),
            scenario_source_path=_resolve_path(args.scenario_source),
            workers=args.workers,
            only_gdiag_subset=args.only_gdiag_subset,
            queue_trace_interval_ms=args.queue_trace_interval_ms,
        )
    except (ValueError, OSError, TcpTruthV2Error) as error:
        logger.error("ns-3 窗内观测诊断驱动失败：%s", error)
        return 1
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if state.get("status") == "finished" else 1


if __name__ == "__main__":
    raise SystemExit(main())
