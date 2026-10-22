#!/usr/bin/env python3
"""绘制第五章的两幅数据图/示意图。

- 图 5-1 服务与计算分离的系统架构（依据 5.2、5.4 正文）
- 图 5-2 四格配置的 12 年回看 F1 曲线（数值全部从运行制品 JSON 读取）

规格来源：仓库根 `AGENTS.md`「学位论文图件合同」与
`thesis/figures/AGENTS.md`。样式基础设施复用 `thesis/figures/第三章/figstyle.py`，
本脚本只负责第五章的图件内容、数据断言、导出与清单登记。

运行方式（在仓库根执行）：
    uv run --project "thesis/figures/第五章" python "thesis/figures/第五章/绘制第五章图件.py"
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "第三章"))

import figstyle as fs  # noqa: E402

from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

DATA_DIR = (
    REPO / "thesis/experiments/llm_probe/runs/diagnostics/ch5-system"
)
COMPARISON = DATA_DIR / "system-comparison.json"
BENCHMARK = (
    REPO
    / "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark/benchmark.json"
)
CELLS = ("naive", "replay", "naive_members", "full")
YEARS = (
    "2013",
    "2014",
    "2016",
    "2017",
    "2018",
    "2019",
    "2020",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
)
GENERATOR_REL = "thesis/figures/第五章/绘制第五章图件.py"


# ---------------------------------------------------------------- 数据读取与断言


def load_curves() -> tuple[dict[str, dict[str, float]], dict[str, object]]:
    """读取四格逐年回看 F1，并与汇总文件逐项核对。"""

    comparison = json.loads(COMPARISON.read_text(encoding="utf-8"))
    curves: dict[str, dict[str, float]] = {}
    for cell in CELLS:
        result_path = DATA_DIR / f"{cell}-result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        backward = result["panel"]["backward_f1"]
        if tuple(backward) != YEARS:
            raise ValueError(
                f"{cell} 的年度顺序与预期不一致：{list(backward)}"
            )
        curves[cell] = {year: float(backward[year]) for year in YEARS}

        summary = comparison["cells"][cell]
        for year in ("2023", "2024", "2025"):
            if abs(curves[cell][year] - float(summary[f"f1_{year}"])) > 1e-12:
                raise ValueError(
                    f"{cell} 的 F1-{year} 与 system-comparison.json 不一致"
                )
        mean = sum(curves[cell].values()) / len(YEARS)
        if abs(mean - float(summary["mean_f1_12y"])) > 1e-12:
            raise ValueError(
                f"{cell} 的 12 年平均 F1 与 system-comparison.json 不一致"
            )

    for cell in ("full", "replay"):
        check = comparison["equivalence_checks"][cell]
        if not check["passed"]:
            raise ValueError(f"{cell} 的等价性断言未通过")
        runner = check["runner"]["backward_f1"]
        for year in YEARS:
            if abs(curves[cell][year] - float(runner[year])) > 1e-12:
                raise ValueError(
                    f"{cell} 的 {year} 年回看 F1 与等价性 runner 不一致"
                )

    return curves, comparison


def load_benchmark() -> tuple[dict[str, object], dict[str, object]]:
    """读取评测服务基准的 chart_data，并与第一轮复现汇总逐项核对。"""

    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    chart = benchmark["chart_data"]
    if chart["services"] != ["py", "rs"]:
        raise ValueError(f"服务顺序与预期不一致：{chart['services']}")
    if chart["concurrency"] != [1, 8]:
        raise ValueError(f"并发档位与预期不一致：{chart['concurrency']}")
    if chart["batch"] != 32 or chart["panel_samples"] != 9686:
        raise ValueError(
            f"批次或面板样本量与预期不一致：batch={chart['batch']}, "
            f"panel_samples={chart['panel_samples']}"
        )

    replication = benchmark["replication_summary"]["round1_py_then_rs"]["services"]
    for index, scenario in enumerate(("c1", "c8")):
        for service in ("py", "rs"):
            expected = replication[service]["scenarios"][scenario]
            for key in ("p50_ms", "p95_ms", "p99_ms", "throughput_samples_s"):
                actual = float(chart[key][service][index])
                if abs(actual - float(expected[key])) > 1e-9:
                    raise ValueError(
                        f"{service} {scenario} 的 {key} 与第一轮汇总不一致"
                    )
    return benchmark, chart


# ---------------------------------------------------------------- 图 5-1


def draw_architecture() -> fs.Canvas:
    """服务/计算分离的四层系统架构图。"""

    cv = fs.canvas(165.0, 128.0)

    host_face = "#FCFCFC"
    config_face = "#F7F7F7"
    service_face = "#ECECEC"
    compute_face = "#E2E2E2"
    eval_face = "#F0F0F0"

    # 宿主机边界
    fs.box(
        cv,
        0.005,
        0.020,
        0.810,
        0.970,
        (),
        face=host_face,
        edge="#333333",
        linewidth=0.8,
        linestyle=(0, (5, 3)),
        radius=0.010,
        zorder=1,
    )
    fs.text(
        cv,
        0.020,
        0.975,
        "宿主机（macOS，MPS 加速）",
        size=9.0,
        ha="left",
        color=fs.INK,
    )

    # 四个层带
    bands = (
        (0.055, 0.855, 0.725, 0.100, config_face, "配置层（Vue3 + ECharts 前端）"),
        (0.055, 0.675, 0.725, 0.130, service_face, "服务层（Go/Gin 服务进程）"),
        (0.055, 0.425, 0.725, 0.193, compute_face, "计算层（Python 训练内核）"),
        (0.055, 0.205, 0.725, 0.180, eval_face, "评测层（四格面板）"),
    )
    for x, y, width, height, face, title in bands:
        fs.box(
            cv,
            x,
            y,
            width,
            height,
            (),
            face=face,
            edge=fs.MUTED,
            linewidth=0.9,
            radius=0.010,
            zorder=2,
        )
        fs.text(
            cv,
            x + 0.012,
            y + height - 0.020,
            title,
            size=9.0,
            ha="left",
            color=fs.INK,
        )

    def subbox(
        x: float,
        y: float,
        width: float,
        height: float,
        lines: tuple[str, ...],
    ) -> None:
        fs.box(
            cv,
            x,
            y,
            width,
            height,
            tuple(fs.Line(line, 8.0) for line in lines),
            face=fs.WHITE,
            edge="#666666",
            linewidth=0.8,
            radius=0.008,
            zorder=4,
        )

    # 配置层：三个界面页
    for x, lines in (
        (0.070, ("实验配置页", "双开关选择")),
        (0.305, ("任务提交页", "状态与日志")),
        (0.540, ("结果面板页", "四格与 12 年曲线")),
    ):
        subbox(x, 0.858, 0.220, 0.052, lines)

    # 服务层：四个组成
    for x, lines in (
        (0.070, ("六组 HTTP 接口", "任务提交与结果读取")),
        (0.247, ("任务队列", "单协程串行调度")),
        (0.424, ("日志与静态托管", "按任务编号归档")),
        (0.601, ("任务存储", "GORM 读写 MySQL")),
    ):
        subbox(x, 0.685, 0.163, 0.075, lines)

    # 计算层：三个处理单元
    compute_boxes = (
        (0.070, ("开关映射", "双开关 → 四格", "冻结协议参数")),
        (0.305, ("数据预算层（第三章）", "回放构成器", "年度训练构成")),
        (0.540, ("成员化引擎层（第四章）", "四成员集成", "参数高效训练")),
    )
    for x, lines in compute_boxes:
        subbox(x, 0.438, 0.215, 0.130, lines)
    for x0, x1 in ((0.285, 0.305), (0.520, 0.540)):
        fs.arrow(
            cv,
            (x0, 0.503),
            (x1, 0.503),
            color=fs.INK,
            linewidth=fs.MAIN_LINE_PT,
            head=6.0,
            zorder=6,
        )

    # 评测层：两个面板与三类断言
    for x, lines in (
        (0.070, ("12 年回看面板", "末年模型回评", "历史年度")),
        (0.305, ("当年评价面板", "当年测试分片", "即时评价")),
        (0.540, ("三类断言", "开关映射·模型契约", "评测一致性")),
    ):
        subbox(x, 0.212, 0.215, 0.125, lines)

    # 纵向主数据流
    fs.arrow(cv, (0.300, 0.853), (0.300, 0.807), color=fs.INK, zorder=6)
    fs.text(
        cv,
        0.320,
        0.830,
        "HTTP：提交开关组合 / 读取面板",
        size=8.0,
        ha="left",
        color=fs.MUTED,
    )
    fs.arrow(cv, (0.300, 0.673), (0.300, 0.622), color=fs.INK, zorder=6)
    fs.text(
        cv,
        0.320,
        0.636,
        "子进程调用：开关组合 → 命令行参数",
        size=8.0,
        ha="left",
        color=fs.MUTED,
    )
    fs.arrow(cv, (0.300, 0.423), (0.300, 0.390), color=fs.INK, zorder=6)
    fs.text(
        cv,
        0.320,
        0.405,
        "训练完成：结果写入约定产物目录",
        size=8.0,
        ha="left",
        color=fs.MUTED,
    )

    # 子进程边界（在标签处断开，避免虚线穿过文字）
    for x0, x1 in ((0.055, 0.620), (0.740, 0.815)):
        fs.polyline(
            cv,
            ((x0, 0.648), (x1, 0.648)),
            color=fs.RULE,
            linewidth=0.6,
            linestyle=(0, (4, 2)),
            zorder=3,
        )
    fs.text(
        cv,
        0.680,
        0.648,
        "子进程边界",
        size=8.0,
        ha="center",
        color=fs.MUTED,
    )

    # 结果回写（左侧回路）
    fs.routed_arrow(
        cv,
        ((0.055, 0.300), (0.044, 0.300), (0.044, 0.730), (0.055, 0.730)),
        color=fs.INK,
        linewidth=1.0,
        linestyle=(0, (4, 2)),
    )
    fs.text(
        cv,
        0.028,
        0.515,
        "结果文件核验回写",
        size=8.0,
        rotation=90,
        color=fs.MUTED,
    )

    # Docker 容器与 MySQL
    fs.box(
        cv,
        0.830,
        0.440,
        0.165,
        0.220,
        (),
        face="#F2F2F2",
        edge="#333333",
        linewidth=0.8,
        linestyle=(0, (5, 3)),
        radius=0.010,
        zorder=3,
    )
    fs.text(
        cv,
        0.9125,
        0.646,
        "Docker 容器",
        size=8.0,
        color=fs.INK,
    )
    fs.box(
        cv,
        0.845,
        0.465,
        0.135,
        0.150,
        (fs.Line("MySQL 8.4", 8.0), fs.Line("任务记录", 8.0), fs.Line("具名数据卷", 8.0)),
        face=fs.WHITE,
        edge="#666666",
        linewidth=0.8,
        radius=0.008,
        zorder=4,
    )
    fs.routed_arrow(
        cv,
        ((0.764, 0.728), (0.795, 0.728), (0.795, 0.550), (0.845, 0.550)),
        color=fs.INK,
        linewidth=1.0,
        linestyle=(0, (4, 2)),
    )
    # 部署边界说明
    fs.text(
        cv,
        0.055,
        0.138,
        "部署边界：Go 服务进程与 Python 训练内核运行于宿主机；MySQL 8.4 以容器部署。",
        size=8.0,
        ha="left",
        color=fs.MUTED,
    )
    fs.text(
        cv,
        0.055,
        0.100,
        "内核不访问数据库；服务侧与内核仅经子进程参数与约定产物目录交互。",
        size=8.0,
        ha="left",
        color=fs.MUTED,
    )
    return cv


# ---------------------------------------------------------------- 图 5-2


def draw_curves(curves: dict[str, dict[str, float]]) -> fs.Canvas:
    """四格配置的 12 年回看 F1 曲线。"""

    width_mm, height_mm = 150.0, 100.0
    fig = Figure(
        figsize=(fs.mm_to_inch(width_mm), fs.mm_to_inch(height_mm)),
        dpi=200,
        facecolor=fs.WHITE,
    )
    ax = fig.add_axes((0.095, 0.280, 0.885, 0.665))

    styles = {
        "naive": {
            "label": "朴素（naive）",
            "color": "#7F7F7F",
            "linestyle": (0, (6, 2)),
            "marker": "o",
            "markersize": 4.2,
            "linewidth": 1.1,
            "filled": False,
        },
        "replay": {
            "label": "数据预算（replay）",
            "color": "#2F6B9A",
            "linestyle": (0, (1.2, 1.6)),
            "marker": "s",
            "markersize": 4.0,
            "linewidth": 1.1,
            "filled": False,
        },
        "naive_members": {
            "label": "成员引擎（naive_members）",
            "color": "#B3512E",
            "linestyle": (0, (4, 1.2, 1, 1.2)),
            "marker": "^",
            "markersize": 4.4,
            "linewidth": 1.1,
            "filled": False,
        },
        "full": {
            "label": "完整（full）",
            "color": fs.INK,
            "linestyle": "-",
            "marker": "D",
            "markersize": 5.0,
            "linewidth": 1.9,
            "filled": True,
        },
    }

    x_values = list(range(len(YEARS)))
    ax.axvspan(
        8.5,
        11.5,
        facecolor="#EDEDED",
        edgecolor="none",
        zorder=0,
    )
    ax.axvline(
        8.5,
        color="#BDBDBD",
        linewidth=0.5,
        linestyle=(0, (3, 2)),
        zorder=1,
    )
    for cell in CELLS:
        style = styles[cell]
        y_values = [curves[cell][year] for year in YEARS]
        ax.plot(
            x_values,
            y_values,
            label=style["label"],
            color=style["color"],
            linestyle=style["linestyle"],
            linewidth=style["linewidth"],
            marker=style["marker"],
            markersize=style["markersize"],
            markerfacecolor=style["color"] if style["filled"] else fs.WHITE,
            markeredgecolor=style["color"],
            markeredgewidth=0.9,
            zorder=4 if cell == "full" else 3,
        )

    ax.set_xlim(-0.4, len(YEARS) - 0.6)
    ax.set_ylim(-0.012, 1.0)
    ax.set_xticks(x_values)
    ax.set_xticklabels(YEARS, size=8.0)
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value * 100:.0f}%"))
    ax.tick_params(axis="y", labelsize=8.0)
    ax.tick_params(axis="x", length=2.5, width=0.6, pad=3.0)
    ax.tick_params(axis="y", length=2.5, width=0.6, pad=2.5)
    ax.set_ylabel(fs.checked("回看 F1", 9.0), size=9.0, labelpad=5.0)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(fs.INK)

    fs.text(
        fs.Canvas(fig, ax, width_mm, height_mm),
        10.0,
        0.972,
        "正例稀缺年度",
        size=8.0,
        color=fs.MUTED,
        va="top",
        zorder=5,
    )

    legend = ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.155),
        ncol=2,
        frameon=False,
        fontsize=8.0,
        handlelength=3.2,
        columnspacing=1.8,
        labelspacing=0.7,
        borderaxespad=0.0,
    )
    for text_item in legend.get_texts():
        text_item.set_color(fs.INK)

    fig.text(
        0.5,
        0.022,
        fs.checked("注：2025 年测试分片仅含 5 条正例，四格 F1 均为 0。", 8.0),
        ha="center",
        va="bottom",
        size=8.0,
        color=fs.MUTED,
    )
    return fs.Canvas(fig, ax, width_mm, height_mm)


def _draw_grouped_bars(
    *,
    width_mm: float,
    height_mm: float,
    group_labels: tuple[str, ...],
    values: dict[str, list[float]],
    ylabel: str,
    xlabel: str,
    ylim: float,
    yticks: list[float],
    value_formatter: Callable[[float], str],
    footnote: str,
    ratio_labels: tuple[str, ...],
    ratio_gap: float = 0.075,
) -> fs.Canvas:
    """分组柱状图：Python 与 Rust 两柱一组，灰度下以填充图案区分。"""

    fig = Figure(
        figsize=(fs.mm_to_inch(width_mm), fs.mm_to_inch(height_mm)),
        dpi=200,
        facecolor=fs.WHITE,
    )
    ax = fig.add_axes((0.105, 0.315, 0.865, 0.605))

    x_positions = list(range(len(group_labels)))
    bar_width = 0.32
    offset = 0.17
    style = {
        "py": {"face": "#D9D9D9", "edge": "#444444", "hatch": "///"},
        "rs": {"face": "#8C8C8C", "edge": "#1F1F1F", "hatch": "\\\\\\\\\\\\"},
    }
    bars = {}
    for service in ("py", "rs"):
        positions = [
            position + (-offset if service == "py" else offset)
            for position in x_positions
        ]
        bars[service] = ax.bar(
            positions,
            values[service],
            width=bar_width,
            color=style[service]["face"],
            edgecolor=style[service]["edge"],
            linewidth=0.8,
            hatch=style[service]["hatch"],
            zorder=3,
        )
        for position, value in zip(positions, values[service]):
            ax.text(
                position,
                value + ylim * 0.018,
                fs.checked(value_formatter(value), 8.0),
                ha="center",
                va="bottom",
                size=8.0,
                color=fs.INK,
                zorder=5,
            )

    for position, ratio in zip(x_positions, ratio_labels):
        peak = max(values["py"][position], values["rs"][position])
        ax.text(
            position,
            peak + ylim * ratio_gap,
            fs.checked(ratio, 8.0),
            ha="center",
            va="bottom",
            size=8.0,
            color=fs.MUTED,
            zorder=5,
        )

    ax.set_xlim(-0.6, len(x_positions) - 0.4)
    ax.set_ylim(0.0, ylim)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(group_labels, size=8.0)
    ax.set_yticks(yticks)
    ax.tick_params(axis="y", labelsize=8.0)
    ax.tick_params(axis="x", length=2.5, width=0.6, pad=3.0)
    ax.tick_params(axis="y", length=2.5, width=0.6, pad=2.5)
    ax.set_ylabel(fs.checked(ylabel, 9.0), size=9.0, labelpad=5.0)
    ax.set_xlabel(fs.checked(xlabel, 9.0), size=9.0, labelpad=5.0)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(fs.INK)

    legend_labels = [
        fs.checked("Python（FastAPI）", 8.0),
        fs.checked("Rust（axum）", 8.0),
    ]
    fig.legend(
        [bars["py"], bars["rs"]],
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.105),
        ncol=2,
        frameon=False,
        fontsize=8.0,
        handlelength=2.4,
        columnspacing=2.0,
        borderaxespad=0.0,
    )
    fig.text(
        0.5,
        0.022,
        fs.checked(footnote, 8.0),
        ha="center",
        va="bottom",
        size=8.0,
        color=fs.MUTED,
    )
    return fs.Canvas(fig, ax, width_mm, height_mm)


def draw_throughput(chart: dict[str, object]) -> fs.Canvas:
    """图 5-3：两档并发下的吞吐对照。"""

    py_values = [float(value) for value in chart["throughput_samples_s"]["py"]]
    rs_values = [float(value) for value in chart["throughput_samples_s"]["rs"]]
    ratios = [rs / py for py, rs in zip(py_values, rs_values)]
    cv = _draw_grouped_bars(
        width_mm=150.0,
        height_mm=90.0,
        group_labels=("1", "8"),
        values={"py": py_values, "rs": rs_values},
        ylabel="吞吐（样本/秒）",
        xlabel="并发数",
        ylim=14000.0,
        yticks=[0, 3000, 6000, 9000, 12000],
        value_formatter=lambda value: f"{value:,.0f}",
        footnote="第一轮 3 遍完整面板的中位吞吐；面板 9,686 样本，批大小 32。",
        ratio_labels=tuple(
            f"Rust/Python {ratio:.2f} 倍" for ratio in ratios
        ),
    )
    cv.ax.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:,.0f}")
    )
    return cv


def draw_latency(chart: dict[str, object]) -> fs.Canvas:
    """图 5-4：八并发下三种延迟分位的对照。"""

    py_values = [
        float(chart["p50_ms"]["py"][1]),
        float(chart["p95_ms"]["py"][1]),
        float(chart["p99_ms"]["py"][1]),
    ]
    rs_values = [
        float(chart["p50_ms"]["rs"][1]),
        float(chart["p95_ms"]["rs"][1]),
        float(chart["p99_ms"]["rs"][1]),
    ]
    ratios = [rs / py for py, rs in zip(py_values, rs_values)]
    return _draw_grouped_bars(
        width_mm=150.0,
        height_mm=90.0,
        group_labels=("p50", "p95", "p99"),
        values={"py": py_values, "rs": rs_values},
        ylabel="延迟（ms）",
        xlabel="延迟分位",
        ylim=88.0,
        yticks=[0, 20, 40, 60, 80],
        value_formatter=lambda value: f"{value:.2f}",
        footnote=(
            "第一轮 3 遍完整面板的中位延迟；Rust/Python 延迟比 p50 "
            f"{ratios[0]:.2f}、p95 {ratios[1]:.2f}、p99 {ratios[2]:.2f}。"
        ),
        ratio_labels=tuple(
            f"Rust/Python {ratio:.2f} 倍" for ratio in ratios
        ),
        ratio_gap=0.085,
    )


# ---------------------------------------------------------------- 清单登记


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stem_key(stem: str) -> tuple[int, int, str]:
    match = re.search(r"图(\d+)-(\d+)", stem)
    if match:
        return (int(match.group(1)), int(match.group(2)), stem)
    return (99, 99, stem)


def build_entry(
    stem: str,
    caption: str,
    spec_width: float,
    spec_height: float,
    canvas: fs.Canvas,
    evidence_mode: str,
    data_keys: list[str],
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    outputs: dict[str, str] = {}
    sizes: dict[str, int] = {}
    hashes: dict[str, str] = {}
    for suffix in ("png", "pdf", "svg"):
        path = HERE / f"{stem}.{suffix}"
        if not path.exists():
            raise FileNotFoundError(f"缺少输出文件：{path}")
        outputs[suffix] = path.name
        sizes[suffix] = path.stat().st_size
        hashes[suffix] = sha256(path)

    from PIL import Image

    with Image.open(HERE / outputs["png"]) as image:
        px_w, px_h = image.size
    ppi_w = px_w / (spec_width / 25.4)
    ppi_h = px_h / (spec_height / 25.4)
    if min(ppi_w, ppi_h) < 300.0 - 1e-6:
        raise ValueError(f"{stem} 实测 ppi 低于 300：{ppi_w:.1f}×{ppi_h:.1f}")

    entry: dict[str, object] = {
        "stem": stem,
        "caption": caption,
        "generator": GENERATOR_REL,
        "environment_ref": "matplotlib_environment",
        "typography_ref": "matplotlib_typography",
        "width_mm": round(spec_width, 2),
        "height_mm": round(spec_height, 2),
        "png_dpi": fs.PNG_DPI,
        "png_pixels": [px_w, px_h],
        "png_ppi_measured": [round(ppi_w, 1), round(ppi_h, 1)],
        "bytes": sizes["png"],
        "bytes_by_format": sizes,
        "sha256": hashes["png"],
        "sha256_by_format": hashes,
        "outputs": outputs,
        "evidence_mode": evidence_mode,
        "data_keys": data_keys,
    }
    if extra:
        entry.update(extra)
    return entry


def update_manifest(entries: list[dict[str, object]]) -> Path:
    path = HERE / "图件清单.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    new_stems = {entry["stem"] for entry in entries}
    figures = [
        figure
        for figure in manifest.get("figures", [])
        if figure.get("stem") not in new_stems
    ]
    figures.extend(entries)
    manifest["figures"] = sorted(figures, key=lambda item: stem_key(str(item["stem"])))

    import matplotlib
    import numpy
    import PIL

    manifest["figure_mode"] = (
        "Web 平台界面截图（真实端到端运行）+ matplotlib 数据图/示意图"
    )
    manifest["contract"] = (
        "AGENTS.md 学位论文图件合同（2026-08-13 重定）；界面截图按用户 "
        "2026-10-22 指定的 1920×1080 PNG 产出；数据图按合同 300 dpi 下限、"
        "实际 400 dpi 导出 PNG+PDF+SVG"
    )
    executable = Path(sys.executable)
    try:
        executable_label = str(executable.relative_to(HERE))
    except ValueError:
        executable_label = executable.name
    manifest["matplotlib_environment"] = {
        "generator": GENERATOR_REL,
        "style_module": "thesis/figures/第三章/figstyle.py",
        "uv_project": "thesis/figures/第五章",
        "uv_lock_sha256": sha256(HERE / "uv.lock"),
        "command": (
            'uv run --project "thesis/figures/第五章" --locked python '
            '"thesis/figures/第五章/绘制第五章图件.py"'
        ),
        "python": ".".join(str(v) for v in sys.version_info[:3]),
        "python_executable": executable_label,
        "matplotlib": matplotlib.__version__,
        "numpy": numpy.__version__,
        "pillow": PIL.__version__,
        "os": platform.platform(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    manifest["matplotlib_typography"] = {
        "cjk_font_requested": fs.CJK_FONT.requested,
        "cjk_font_used": fs.CJK_FONT.family,
        "cjk_font_path": fs.CJK_FONT.path,
        "cjk_face_index": fs.CJK_FONT.face_index,
        "latin_font_used": fs.LATIN_FONT.family,
        "latin_font_path": fs.LATIN_FONT.path,
        "math_fontset": (
            "stix" if fs.MATH_FONT is None else f"custom ({fs.MATH_FONT.family})"
        ),
        "min_font_pt": fs.MIN_FONT_PT,
        "main_font_pt": fs.MAIN_FONT_PT,
        "main_line_pt": fs.MAIN_LINE_PT,
        "aux_line_pt": fs.AUX_LINE_PT,
        "png_dpi": fs.PNG_DPI,
    }
    manifest["matplotlib_data_mode"] = (
        "图 5-2 由四格结果 JSON 的 panel.backward_f1 读取并断言；"
        "图 5-3 与图 5-4 由 benchmark.json 的 chart_data 读取并断言；"
        "图 5-1 依据 5.2、5.4 正文绘制"
    )
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------- 主流程


def main() -> None:
    curves, _ = load_curves()
    _, chart = load_benchmark()

    architecture = draw_architecture()
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图5-1-服务与计算分离的系统架构",
            width_mm=165.0,
            height_mm=128.0,
            draw=None,
        ),
        architecture,
    )

    curve_figure = draw_curves(curves)
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图5-2-四格配置的12年回看F1曲线",
            width_mm=150.0,
            height_mm=100.0,
            draw=None,
        ),
        curve_figure,
    )

    throughput_figure = draw_throughput(chart)
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图5-3-两种评测服务的吞吐对照",
            width_mm=150.0,
            height_mm=90.0,
            draw=None,
        ),
        throughput_figure,
    )

    latency_figure = draw_latency(chart)
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图5-4-八并发下的延迟分位对照",
            width_mm=150.0,
            height_mm=90.0,
            draw=None,
        ),
        latency_figure,
    )

    py_tp = [float(value) for value in chart["throughput_samples_s"]["py"]]
    rs_tp = [float(value) for value in chart["throughput_samples_s"]["rs"]]
    tp_ratios = [rs / py for py, rs in zip(py_tp, rs_tp)]
    py_latency = {
        key: float(chart[key]["py"][1]) for key in ("p50_ms", "p95_ms", "p99_ms")
    }
    rs_latency = {
        key: float(chart[key]["rs"][1]) for key in ("p50_ms", "p95_ms", "p99_ms")
    }
    latency_ratios = {
        key: rs_latency[key] / py_latency[key] for key in py_latency
    }

    entries = [
        build_entry(
            "图5-1-服务与计算分离的系统架构",
            "服务与计算分离的系统架构。配置层由 Vue3 与 ECharts 实现，提交双开关组合"
            "并展示四格结果；服务层为 Go/Gin 服务进程，含六组接口、单协程任务队列、"
            "日志与静态托管，任务记录经 GORM 写入 MySQL；计算层为宿主机 Python 训练内核，"
            "由子进程调用，依次完成开关映射、第三章回放构成与第四章成员化引擎；评测层"
            "产出 12 年回看面板、当年评价面板与三类断言。MySQL 8.4 运行于 Docker 容器，"
            "Go 服务进程与 Python 训练内核运行于宿主机。",
            165.0,
            128.0,
            architecture,
            "架构示意（依据 5.2、5.4 正文）",
            [
                "thesis/chapters/第五章-LAMDA/5.2-系统架构设计.md §5.2.1–§5.2.3",
                "thesis/chapters/第五章-LAMDA/5.4-系统部署与运行环境.md §5.4.1–§5.4.3",
                "platform/docker-compose.yml（MySQL 8.4 容器边界）",
            ],
        ),
        build_entry(
            "图5-2-四格配置的12年回看F1曲线",
            "四格配置在 12 个测试年度上的回看 F1。横轴为测试年度（12 个年度），"
            "纵轴为末年经验模型对历史年度统一回评的 F1；四条曲线分别为朴素（naive）、"
            "数据预算（replay）、成员引擎（naive_members）与完整（full），完整格以加粗"
            "实线突出。灰色底纹标出 2023–2025 三个正例稀缺年度。",
            150.0,
            100.0,
            curve_figure,
            "真实数据：四格统一入口重跑结果 JSON",
            [
                "thesis/experiments/llm_probe/runs/diagnostics/ch5-system/"
                "system-comparison.json.cells.<cell>.{f1_2023,f1_2024,f1_2025,mean_f1_12y}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch5-system/"
                "<cell>-result.json.panel.backward_f1",
                "thesis/experiments/llm_probe/runs/diagnostics/ch5-system/"
                "system-comparison.json.equivalence_checks.{full,replay}.runner.backward_f1",
            ],
            {
                "years": list(YEARS),
                "series_2023": {
                    cell: curves[cell]["2023"] for cell in CELLS
                },
                "verification": {
                    "years_order": "panel.backward_f1 键序与图件年度顺序逐位一致",
                    "summary_match": "四格 2023/2024/2025 与 mean_f1_12y 逐位一致（容差 1e-12）",
                    "equivalence_runner_match": "full 与 replay 逐年与 equivalence_checks.runner 逐位一致",
                },
            },
        ),
        build_entry(
            "图5-3-两种评测服务的吞吐对照",
            "两种评测服务在并发 1 与并发 8 下的吞吐对照。柱为第一轮 3 遍完整 2024 年测试"
            "面板（9,686 样本，批大小 32）的中位吞吐；Python 为 FastAPI 实现，Rust 为 "
            "axum 实现。并发 1 时 Rust/Python 吞吐比为 1.11，并发 8 时为 1.72。",
            150.0,
            90.0,
            throughput_figure,
            "真实数据：ch5-eval-benchmark/benchmark.json.chart_data",
            [
                "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark/"
                "benchmark.json.chart_data.{services,concurrency,batch,panel_samples,"
                "throughput_samples_s}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark/"
                "benchmark.json.replication_summary.round1_py_then_rs.services."
                "{py,rs}.scenarios.{c1,c8}.throughput_samples_s",
                "thesis/chapters/第五章-LAMDA/5.6-评测服务的多语言实现对比.md 表 5-10",
            ],
            {
                "concurrency": [1, 8],
                "throughput_samples_s": {
                    "py": py_tp,
                    "rs": rs_tp,
                },
                "rust_over_python": {
                    "c1": tp_ratios[0],
                    "c8": tp_ratios[1],
                },
                "verification": {
                    "source": "chart_data.throughput_samples_s 与第一轮复现汇总逐位一致（容差 1e-9）",
                    "values": "柱顶数值由 chart_data 直接格式化，未手抄",
                },
            },
        ),
        build_entry(
            "图5-4-八并发下的延迟分位对照",
            "八并发下两种评测服务的 p50、p95 与 p99 延迟对照。柱为第一轮 3 遍完整"
            "面板的中位延迟；Rust/Python 延迟比分别为 0.62、0.43 与 0.47。",
            150.0,
            90.0,
            latency_figure,
            "真实数据：ch5-eval-benchmark/benchmark.json.chart_data",
            [
                "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark/"
                "benchmark.json.chart_data.{services,concurrency,batch,panel_samples,"
                "p50_ms,p95_ms,p99_ms}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch5-eval-benchmark/"
                "benchmark.json.replication_summary.round1_py_then_rs.services."
                "{py,rs}.scenarios.c8.{p50_ms,p95_ms,p99_ms}",
                "thesis/chapters/第五章-LAMDA/5.6-评测服务的多语言实现对比.md 表 5-10",
            ],
            {
                "concurrency": 8,
                "latency_ms": {
                    "p50": {"py": py_latency["p50_ms"], "rs": rs_latency["p50_ms"]},
                    "p95": {"py": py_latency["p95_ms"], "rs": rs_latency["p95_ms"]},
                    "p99": {"py": py_latency["p99_ms"], "rs": rs_latency["p99_ms"]},
                },
                "rust_over_python": {
                    "p50": latency_ratios["p50_ms"],
                    "p95": latency_ratios["p95_ms"],
                    "p99": latency_ratios["p99_ms"],
                },
                "verification": {
                    "source": "chart_data.p50/p95/p99_ms 与第一轮复现汇总逐位一致（容差 1e-9）",
                    "values": "柱顶数值由 chart_data 直接格式化，未手抄",
                },
            },
        ),
    ]

    manifest = update_manifest(entries)
    for line in fs.verify_outputs(HERE, entries):
        print(line)
    print(f"图件清单：{manifest}")
    print("[数据核对] 图 5-2 的 2023 年回看 F1：")
    for cell in CELLS:
        print(f"  {cell}: {curves[cell]['2023']:.12f}")
    print("[数据核对] 图 5-3 吞吐（样本/秒）：")
    for index, concurrency in enumerate(chart["concurrency"]):
        print(
            f"  并发 {concurrency}: py={py_tp[index]:.6f}, "
            f"rs={rs_tp[index]:.6f}, rust/py={tp_ratios[index]:.6f}"
        )
    print("[数据核对] 图 5-4 八并发延迟（ms）：")
    for key, label in (("p50_ms", "p50"), ("p95_ms", "p95"), ("p99_ms", "p99")):
        print(
            f"  {label}: py={py_latency[key]:.6f}, "
            f"rs={rs_latency[key]:.6f}, rust/py={latency_ratios[key]:.6f}"
        )


if __name__ == "__main__":
    main()
