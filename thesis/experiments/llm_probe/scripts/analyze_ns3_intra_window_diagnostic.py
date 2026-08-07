"""ns-3 窗内观测诊断分析脚本。

按预注册判据 G-diag 裁决研究假设：
「99% 的窗口边界队列为零，是因为队列在 0.1 秒窗口内涨起又排空、
被首尾采样抹平」。

判据阈值与候选采样点数 K 在计划评审阶段冻结为本模块的模块级常量
（见下方常量区），严禁在看到真实诊断数据后调整，也不提供命令行覆盖
入口，防止事后调参。详见
``.Codex/docs/2026-08-07-ns3窗内观测诊断-task_plan.md`` 的「预注册判据」小节。

数据来源：

- 诊断主 CSV（ns-3 诊断场景 ``m_mainOutput`` 落盘产物，惯例命名为
  ``result.csv``），逐窗口一行，列含 ``physics_group_sha256``、
  ``window_index``、``transport_family`` 及四个诊断专用列
  （``diag_queue_peak_l3_bytes``、``diag_queue_peak_packets``、
  ``diag_queue_nonzero_seconds``、``diag_queue_time_avg_l3_bytes``）。
- 每个运行目录下的 ``config.json``，形如
  ``{"run": {"physics_group_sha256": ..., "traffic_mode": "dos",
  "offered_load_ratio": 1.05, ...}}``，携带主 CSV 缺失的运行级参数
  （``traffic_mode``、``offered_load_ratio``）。

诊断主 CSV 本身不带 ``traffic_mode``/``offered_load_ratio``（这两个字段
是运行级配置，不是窗口级真值），因此本脚本按 ``physics_group_sha256``
把两者关联后，再交给 ``evaluate_g_diag``/``suggest_k`` 计算。
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 预注册判据 G-diag 的冻结常量。
#
# 全部取值在计划评审阶段随判据一起冻结，不得在看到诊断数据后修改，
# 也不提供命令行覆盖入口，作为防止事后调参的机制保障。
# ---------------------------------------------------------------------------

#: G-diag 子集筛选条件：仅纳入 DoS 流量、且过载比达到该阈值（含等号）的窗口。
MIN_LOAD_RATIO: float = 1.05

#: G-diag 通过阈值：子集内峰值队列非零窗口占比下限，恰好等于该值判为通过。
PEAK_NONZERO_FRACTION_THRESHOLD: float = 0.50

#: ns-3 诊断场景固定窗口时长（秒），与 config.json 中 run.window_seconds
#: 的预注册取值一致；suggest_k 按该窗口时长切分候选子区间。
WINDOW_SECONDS: float = 0.1

#: suggest_k 的候选子区间数 K，按升序排列，取满足颗粒度要求的最小值。
SUGGEST_K_CANDIDATES: tuple[int, ...] = (6, 11, 21)


class GDiagError(ValueError):
    """G-diag 判据在子集为空等前置条件不满足时抛出。"""


class GDiagDataError(RuntimeError):
    """诊断主 CSV 与 config.json 的读取或关联阶段出现的数据错误。"""


def evaluate_g_diag(frame: pd.DataFrame) -> dict[str, object]:
    """按预注册 G-diag 判据裁决窗口粒度假设。

    在 ``traffic_mode == "dos"`` 且 ``offered_load_ratio >= MIN_LOAD_RATIO``
    的窗口子集上，计算峰值队列非零占比与非零占用时长中位数，并给出唯一裁决。

    Args:
        frame: 已按 physics_group_sha256 关联 traffic_mode、
            offered_load_ratio 两列的诊断主 DataFrame，须含
            diag_queue_peak_l3_bytes 与 diag_queue_nonzero_seconds 两列。

    Returns:
        字典，键为：

        - ``subset_rows``：子集行数；
        - ``peak_nonzero_fraction``：峰值队列非零的窗口占比；
        - ``nonzero_seconds_median``：非零占用时长中位数；
        - ``passed``：是否通过 G-diag（峰值占比达标且中位数严格为正）。

    Raises:
        GDiagError: 子集为空时抛出，不得静默返回通过或不通过。
    """
    subset = frame[
        (frame["traffic_mode"] == "dos") & (frame["offered_load_ratio"] >= MIN_LOAD_RATIO)
    ]
    if subset.empty:
        raise GDiagError("G-diag 子集为空，无法裁决")
    peak_fraction = float((subset["diag_queue_peak_l3_bytes"] > 0).mean())
    nonzero_median = float(subset["diag_queue_nonzero_seconds"].median())
    return {
        "subset_rows": int(len(subset)),
        "peak_nonzero_fraction": peak_fraction,
        "nonzero_seconds_median": nonzero_median,
        "passed": peak_fraction >= PEAK_NONZERO_FRACTION_THRESHOLD and nonzero_median > 0.0,
    }


def suggest_k(frame: pd.DataFrame) -> dict[str, object]:
    """依据 G-diag 子集的非零占用时长中位数，选出满足颗粒度要求的最小候选 K。

    可行条件为 ``WINDOW_SECONDS / (K - 1) <= nonzero_seconds_median``：
    把 ``WINDOW_SECONDS`` 秒窗口等分为 ``K - 1`` 个子区间后，子区间长度
    不超过实测非零占用时长中位数。按 ``SUGGEST_K_CANDIDATES`` 升序取最小
    可行值。

    Args:
        frame: 语义同 evaluate_g_diag 的入参。

    Returns:
        字典，键为 ``nonzero_seconds_median``、``suggested_k``；候选集中
        无一满足时 ``suggested_k`` 为 ``None``，表示需要扩大候选集。

    Raises:
        GDiagError: 由内部调用的 evaluate_g_diag 在子集为空时抛出。
    """
    verdict = evaluate_g_diag(frame)
    nonzero_median = verdict["nonzero_seconds_median"]
    suggested: int | None = None
    for candidate in SUGGEST_K_CANDIDATES:
        if WINDOW_SECONDS / (candidate - 1) <= nonzero_median:
            suggested = candidate
            break
    return {
        "nonzero_seconds_median": nonzero_median,
        "suggested_k": suggested,
    }


# ---------------------------------------------------------------------------
# 诊断主 CSV 与 config.json 的装载、关联。
# ---------------------------------------------------------------------------


def _load_run_record(config_path: Path) -> dict[str, object]:
    """读取单个运行目录下的 config.json，抽取 G-diag 需要的运行级字段。

    Args:
        config_path: 运行目录下的 config.json 路径。

    Returns:
        字典，键为 physics_group_sha256、traffic_mode、offered_load_ratio。

    Raises:
        GDiagDataError: 文件不可读、不是合法 JSON、缺少 run 字段或缺少
            必需子字段时抛出。
    """
    try:
        raw_text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GDiagDataError(f"读取运行配置失败：{config_path}") from exc
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GDiagDataError(f"运行配置不是合法 JSON：{config_path}") from exc
    run = raw.get("run")
    if not isinstance(run, dict):
        raise GDiagDataError(f"运行配置缺少 run 字段：{config_path}")
    try:
        physics_group_sha256 = str(run["physics_group_sha256"])
        traffic_mode = str(run["traffic_mode"])
        offered_load_ratio = float(run["offered_load_ratio"])
    except KeyError as exc:
        raise GDiagDataError(f"运行配置缺少必需字段 {exc}：{config_path}") from exc
    except (TypeError, ValueError) as exc:
        raise GDiagDataError(f"运行配置字段类型不合法：{config_path}") from exc
    return {
        "physics_group_sha256": physics_group_sha256,
        "traffic_mode": traffic_mode,
        "offered_load_ratio": offered_load_ratio,
    }


def build_run_metadata_index(runs_root: Path) -> dict[str, dict[str, object]]:
    """遍历诊断输出根目录下全部 config.json，建立按 physics_group_sha256 的运行级字段索引。

    已核实的数据事实：512 个运行对应 256 个唯一 physics_group_sha256、
    无重复键，即同一 key 唯一确定一组 (traffic_mode, offered_load_ratio)
    （例如同一物理组下的 TCP/UDP 配对运行共享该组参数）。本函数据此按
    字典建立索引，并显式校验冲突，不静默接受不一致数据。

    Args:
        runs_root: 诊断矩阵输出根目录，递归搜索其下全部 config.json。

    Returns:
        physics_group_sha256 到
        ``{"traffic_mode": ..., "offered_load_ratio": ...}`` 的字典。

    Raises:
        GDiagDataError: 未发现任何 config.json，或同一
            physics_group_sha256 在不同运行配置间取值不一致时抛出。
    """
    index: dict[str, dict[str, object]] = {}
    config_paths = sorted(runs_root.glob("**/config.json"))
    if not config_paths:
        raise GDiagDataError(f"运行根目录下未发现 config.json：{runs_root}")
    for config_path in config_paths:
        record = _load_run_record(config_path)
        key = str(record["physics_group_sha256"])
        fields = {
            "traffic_mode": record["traffic_mode"],
            "offered_load_ratio": record["offered_load_ratio"],
        }
        existing = index.get(key)
        if existing is not None and existing != fields:
            raise GDiagDataError(
                f"physics_group_sha256={key} 在多个运行配置间不一致："
                f"{existing} vs {fields}（{config_path}）"
            )
        index[key] = fields
    return index


def load_diagnostic_frame(runs_root: Path, *, csv_name: str = "result.csv") -> pd.DataFrame:
    """读取诊断输出根目录下全部运行的主 CSV，并按 physics_group_sha256 关联运行级字段。

    Args:
        runs_root: 诊断矩阵输出根目录；其下每个运行目录都含 config.json，
            部分目录另含主 CSV（默认文件名 ``result.csv``，与
            ``r2_ns3_protocol_runner.py`` 落盘的
            ``pairs/<physics_group_sha256>/<transport_family>/`` 目录
            结构一致）。
        csv_name: 主 CSV 文件名，默认 ``"result.csv"``。

    Returns:
        拼接全部运行窗口行、并已补齐 traffic_mode、offered_load_ratio
        两列的 DataFrame，可直接传给 evaluate_g_diag / suggest_k。

    Raises:
        GDiagDataError: 未发现任何主 CSV，或某一行的
            physics_group_sha256 无法在运行配置索引中找到对应记录时抛出。
    """
    metadata_index = build_run_metadata_index(runs_root)
    csv_paths = sorted(runs_root.glob(f"**/{csv_name}"))
    if not csv_paths:
        raise GDiagDataError(f"运行根目录下未发现主 CSV：{runs_root}")
    frames: list[pd.DataFrame] = []
    for csv_path in csv_paths:
        frame = pd.read_csv(csv_path)
        if "physics_group_sha256" not in frame.columns:
            raise GDiagDataError(f"主 CSV 缺少 physics_group_sha256 列：{csv_path}")
        sha_column = frame["physics_group_sha256"].astype(str)
        unknown_keys = set(sha_column.unique()) - metadata_index.keys()
        if unknown_keys:
            raise GDiagDataError(
                f"主 CSV 中的 physics_group_sha256 未在运行配置中找到："
                f"{csv_path} {sorted(unknown_keys)}"
            )
        traffic_mode_map = {key: value["traffic_mode"] for key, value in metadata_index.items()}
        offered_load_ratio_map = {
            key: value["offered_load_ratio"] for key, value in metadata_index.items()
        }
        frame = frame.assign(
            traffic_mode=sha_column.map(traffic_mode_map),
            offered_load_ratio=sha_column.map(offered_load_ratio_map),
        )
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# 命令行入口。
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。

    仅暴露数据路径参数；G-diag 判据阈值与 suggest_k 候选集均为模块级
    冻结常量，不提供命令行覆盖入口。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-root",
        type=Path,
        required=True,
        help="诊断矩阵输出根目录，其下每个运行目录含 config.json 与主 CSV",
    )
    parser.add_argument(
        "--csv-name",
        default="result.csv",
        help="主 CSV 文件名，默认 result.csv",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="裁决结果写出路径；缺省时只打印到日志",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """命令行入口：装载诊断数据、运行 G-diag 裁决与 K 选型建议。

    Args:
        argv: 命令行参数；为 ``None`` 时使用 ``sys.argv``。

    Returns:
        退出码。``0`` 表示裁决流程本身成功执行（不代表 G-diag 通过，
        通过与否记录在输出结果的 ``passed`` 字段中）；非零表示数据装载
        或裁决前置条件失败。
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_arg_parser().parse_args(argv)
    try:
        frame = load_diagnostic_frame(args.runs_root, csv_name=args.csv_name)
        verdict = evaluate_g_diag(frame)
        k_suggestion = suggest_k(frame)
    except GDiagDataError as exc:
        logger.error("G-diag 数据装载失败：%s", exc)
        return 1
    except GDiagError as exc:
        logger.error("G-diag 裁决前置条件不满足：%s", exc)
        return 1
    result: dict[str, object] = {
        "runs_root": str(args.runs_root),
        **verdict,
        "suggested_k": k_suggestion["suggested_k"],
    }
    logger.info("G-diag 裁决结果：%s", json.dumps(result, ensure_ascii=False))
    if args.output_json is not None:
        args.output_json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
