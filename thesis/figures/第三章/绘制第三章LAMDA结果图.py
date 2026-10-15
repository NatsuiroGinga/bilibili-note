"""生成第三章（LAMDA 线）实验结果图：图3-5 至 图3-11。

数据只来自 `resultdata_lamda.py` 登记的权威制品，图内每个数字都可指回 `metrics_*.json`
的 `records` 字段；本脚本不含任何手工录入的实验读数。唯一的例外是图3-9 的缓冲年度构成
审计——它对任何 `metrics_*.json` 都没有对应字段，由 `resultdata_lamda.BUFFER_AUDIT`
以显式常量表登记来源，并在图件清单中标为外部给定常数。

字体、版面换算、绘图原语、多格式导出与图件清单全部复用 `figstyle.py`。

执行：uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章LAMDA结果图.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import figstyle as fs
import numpy as np
import resultdata_lamda as rd
from matplotlib.axes import Axes

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "图件清单.json"
GENERATOR = "绘制第三章LAMDA结果图.py"
MECHANISM_GENERATOR = "绘制第三章LAMDA机制图.py"

INK, MUTED = fs.INK, fs.MUTED
FS_MIN, FS_MAIN = fs.MIN_FONT_PT, fs.MAIN_FONT_PT
GRID = "#D9D9D9"
HAIRLINE = fs.HAIRLINE

# 灰度可读：系列区分依靠线型、标记与填充图案，颜色只作辅助。
STYLE = {
    "solid": ("-", "o", fs.M1_EDGE),
    "dashed": ("--", "s", fs.M2_EDGE),
    "dashdot": ("-.", "^", INK),
    "dotted": (":", "D", MUTED),
}
FILL_LEVELS = ("#F6F6F6", "#E4E4E4", "#D0D0D0", "#B8B8B8")
HATCHES = ("", "//", "..", "xx")


# ------------------------------------------------------------------ 版面原语


def data_axes(cv: fs.Canvas, rect: tuple[float, float, float, float], grid_axis: str = "y") -> Axes:
    ax = cv.fig.add_axes(rect)
    # 数据区背景透明：画布上的浮动标签画在下层背景坐标区，白色实底会把它盖住。
    ax.set_facecolor("none")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=fs.AUX_LINE_PT, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, pad=1.5, width=0.7, labelsize=FS_MIN)
    return ax


def tick_labels(ax: Axes, axis: str, labels: list[str], size: float = FS_MIN) -> None:
    for value in labels:
        fs.check_label(value, size)
    setter = ax.set_xticklabels if axis == "x" else ax.set_yticklabels
    setter(labels, fontsize=size, linespacing=1.2)


def axis_label(ax: Axes, axis: str, value: str) -> None:
    fs.check_label(value, FS_MAIN)
    (ax.set_xlabel if axis == "x" else ax.set_ylabel)(value, fontsize=FS_MAIN, labelpad=3)


def tag(
    cv: fs.Canvas,
    x: float,
    y: float,
    value: str,
    color: str = INK,
    ha: str = "left",
    size: float = FS_MIN,
) -> None:
    """图内浮动标签：逐字核验字形后落笔，垫白底以免压住曲线。"""

    fs.check_label(value, size)
    cv.ax.text(
        x,
        y,
        value,
        size=size,
        color=color,
        ha=ha,
        va="center",
        zorder=9,
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none"},
    )


def note(cv: fs.Canvas, x: float, y: float, value: str, ha: str = "left", color: str = MUTED) -> None:
    fs.text(cv, x, y, value, size=FS_MIN, color=color, ha=ha)


# ------------------------------------------------------------------ 图 3-5


def draw_storage_curve(ctx: dict[str, Any]) -> None:
    """图3-5 存储占用与跨年平均 F1：样本侧曲线、参数侧三点与两个端点。"""

    cv: fs.Canvas = ctx["cv"]
    reads: dict[str, rd.ArmReadout] = ctx["readouts"]
    rect = (0.148, 0.190, 0.830, 0.700)
    ax = data_axes(cv, rect)

    sample_keys = ("m50", "m200", "m400", "m800", "m18854")
    xs = [reads[key].storage_kib for key in sample_keys]
    ys = [reads[key].cross_year_f1 * 100.0 for key in sample_keys]
    ax.plot(xs, ys, color=fs.M1_EDGE, linestyle="-", linewidth=1.4, zorder=5)
    ax.plot(
        xs,
        ys,
        marker="o",
        markersize=4.0,
        markerfacecolor=fs.M1_EDGE,
        markeredgecolor=fs.M1_EDGE,
        linestyle="none",
        zorder=6,
    )

    # 本章方法：同一条容量轴上的第二条曲线，构成方式与复用分配均与默认配置一致。
    # 与官方回放以**线型 + 空心标记**区分，不依赖颜色，满足灰度可读要求。
    quota_keys = ("q_m50", "q_m200", "q_m400", "q_m800", "q_m1600", "q_m18854")
    qxs = [reads[key].storage_kib for key in quota_keys]
    qys = [reads[key].cross_year_f1 * 100.0 for key in quota_keys]
    ax.plot(qxs, qys, color=fs.M2_EDGE, linestyle="--", linewidth=1.4, zorder=5)
    ax.plot(
        qxs,
        qys,
        marker="s",
        markersize=3.6,
        markerfacecolor="white",
        markeredgecolor=fs.M2_EDGE,
        markeredgewidth=1.0,
        linestyle="none",
        zorder=6,
    )

    # 朴素更新与联合训练：存储分别为 0 与 438.6 MB，作为缺口的两端刻度。
    naive_f1 = reads["naive"].cross_year_f1 * 100.0
    ax.axhline(naive_f1, color=MUTED, linewidth=fs.MAIN_LINE_PT, linestyle="--", zorder=3)
    joint = reads["cumulative"]
    ax.plot(
        [joint.storage_kib],
        [joint.cross_year_f1 * 100.0],
        marker="*",
        markersize=7.0,
        markerfacecolor=INK,
        markeredgecolor=INK,
        linestyle="none",
        zorder=7,
    )

    # 参数侧三点与 10.25 MB 等预算竖线。
    param_rows = (
        ("freemoca", "逐参数位移插值", "s"),
        ("lwf", "无遗忘学习", "D"),
        ("ewc", "弹性权重巩固", "^"),
    )
    for key, _, marker in param_rows:
        row = reads[key]
        ax.plot(
            [row.storage_kib],
            [row.cross_year_f1 * 100.0],
            marker=marker,
            markersize=4.2,
            markerfacecolor="white",
            markeredgecolor=MUTED,
            markeredgewidth=0.9,
            linestyle="none",
            zorder=7,
        )
    ax.axvline(rd.param_storage_kib(1.0), color=HAIRLINE, linewidth=fs.AUX_LINE_PT, zorder=1)

    def px(value: float) -> float:
        """数据 x（KiB）换算为画布归一化横坐标。"""

        lo, hi = 20.0, 800_000.0
        return rect[0] + (np.log10(value) - np.log10(lo)) / (np.log10(hi) - np.log10(lo)) * rect[2]

    def py(value: float) -> float:
        lo, hi = 70.0, 90.0
        return rect[1] + (value - lo) / (hi - lo) * rect[3]

    tag(cv, px(30.0), py(naive_f1) - 0.055, "朴素更新（存储 0）", color=MUTED)
    tag(cv, px(30.0), py(79.8), "官方回放", color=fs.M1_EDGE)
    tag(cv, px(270.0), py(84.3), "本章方法", color=fs.M2_EDGE)
    tag(cv, px(1300.0), py(87.4), "参数侧三种形态", color=MUTED)
    tag(cv, px(300_000.0), py(89.0), "联合训练（上界）", color=INK, ha="right")
    tag(cv, px(13_000.0), py(76.5), "无遗忘学习", color=MUTED)
    tag(cv, px(6_500.0), py(74.5), "逐参数位移插值", color=MUTED, ha="right")
    tag(cv, px(24_000.0), py(74.2), "弹性权重巩固", color=MUTED)

    ax.set_xscale("log")
    ax.set_xlim(20.0, 800_000.0)
    ax.set_ylim(70.0, 90.0)
    ax.minorticks_off()
    ax.set_xticks([30, 100, 1000, 10000, 100000, 500000])
    tick_labels(ax, "x", ["30", "100", "1 000", "10 000", "100 000", "500 000"])
    ax.set_yticks([70, 75, 80, 85, 90])
    tick_labels(ax, "y", ["70", "75", "80", "85", "90"])
    axis_label(ax, "x", "存储预算（KB，对数刻度）")
    axis_label(ax, "y", "跨年平均 F1（%）")


# ------------------------------------------------------------------ 图 3-6


def draw_reuse_curve(ctx: dict[str, Any]) -> None:
    """图3-6 复用倍数与跨年平均 F1（容量固定 200 条）。"""

    cv: fs.Canvas = ctx["cv"]
    reads: dict[str, rd.ArmReadout] = ctx["readouts"]
    rect = (0.165, 0.215, 0.800, 0.690)
    ax = data_axes(cv, rect)

    keys = ("m200", "m200_r2", "m200_r4", "m200_r8")
    reuse = [reads[key].reuse for key in keys]
    values = [reads[key].cross_year_f1 * 100.0 for key in keys]
    ax.plot(reuse, values, color=fs.M1_EDGE, linestyle="-", linewidth=1.4, zorder=5)
    ax.plot(
        reuse,
        values,
        marker="o",
        markersize=4.4,
        markerfacecolor="white",
        markeredgecolor=fs.M1_EDGE,
        markeredgewidth=1.0,
        linestyle="none",
        zorder=6,
    )
    for value, x in zip(values, reuse, strict=True):
        ax.plot([x, x], [70.0, value], color=HAIRLINE, linewidth=fs.AUX_LINE_PT, zorder=1)
    peak = int(np.argmax(values))
    ax.plot(
        [reuse[peak]],
        [values[peak]],
        marker="v",
        markersize=4.6,
        markerfacecolor=INK,
        markeredgecolor=INK,
        linestyle="none",
        zorder=7,
    )
    tag(cv, 0.430, 0.845, f"内部最优：复用倍数 {reuse[peak]}", color=INK)
    tag(cv, 0.700, 0.330, f"倍数 8 回落至 {values[3]:.2f}%", color=MUTED)

    ax.set_xscale("log", base=2)
    ax.set_xlim(0.9, 9.0)
    ax.set_ylim(75.0, 88.0)
    ax.minorticks_off()
    ax.set_xticks([1, 2, 4, 8])
    tick_labels(ax, "x", ["1", "2", "4", "8"])
    ax.set_yticks([75, 80, 85])
    tick_labels(ax, "y", ["75", "80", "85"])
    axis_label(ax, "x", "复用倍数 m（对数刻度）")
    axis_label(ax, "y", "跨年平均 F1（%）")


# ------------------------------------------------------------------ 图 3-7


def draw_ablation(ctx: dict[str, Any]) -> None:
    """图3-7 双机制消融：缓冲构成 × 复用倍数的 2×2 对照。"""

    cv: fs.Canvas = ctx["cv"]
    reads: dict[str, rd.ArmReadout] = ctx["readouts"]
    value = {
        ("reservoir", 1): reads["m200"].cross_year_f1 * 100.0,
        ("reservoir", 2): reads["m200_r2"].cross_year_f1 * 100.0,
        ("quota", 1): reads["quota"].cross_year_f1 * 100.0,
        ("quota", 2): reads["quota_r2"].cross_year_f1 * 100.0,
    }
    lo, hi = min(value.values()), max(value.values())

    col_x = (0.315, 0.560)
    row_y = (0.570, 0.290)
    cell_w, cell_h = 0.215, 0.270
    columns = {(1): 0, (2): 1}
    rows = {"reservoir": 0, "quota": 1}
    row_mid = (row_y[0] + cell_h / 2.0, row_y[1] + cell_h / 2.0)

    for reuse, column in columns.items():
        fs.text(cv, col_x[column] + cell_w / 2.0, 0.950, f"复用倍数 {reuse}", size=FS_MAIN, color=INK)
    fs.text(cv, 0.295, row_mid[0], "全局蓄水池", size=FS_MIN, color=INK, ha="right")
    fs.text(cv, 0.295, row_mid[1], "按年度配额", size=FS_MIN, color=INK, ha="right")

    for composition, row in rows.items():
        for reuse, column in columns.items():
            measured = value[(composition, reuse)]
            ratio = (measured - lo) / (hi - lo)
            face = FILL_LEVELS[min(len(FILL_LEVELS) - 1, int(round(ratio * 3)))]
            highlight = composition == "quota" and reuse == 2
            lines = [fs.Line(f"{measured:.2f}%", FS_MAIN, "cjk", INK)]
            if highlight:
                lines.append(fs.Line("本章方法", FS_MIN, "cjk", MUTED))
            fs.box(
                cv,
                col_x[column],
                row_y[row],
                cell_w,
                cell_h,
                tuple(lines),
                face=face,
                edge=INK if highlight else fs.RULE,
                linewidth=1.4 if highlight else 0.7,
                hatch=HATCHES[2] if column else HATCHES[0],
                hatch_color=INK,
                radius=0.012,
            )

    # 边栏：两个配置量各自的增益。
    quota_gain = value[("quota", 1)] - value[("reservoir", 1)]
    reuse_gain = value[("reservoir", 2)] - value[("reservoir", 1)]
    pair = value[("quota", 2)] - value[("reservoir", 2)]
    fs.text(cv, 0.800, 0.950, "复用增益", size=FS_MIN, color=MUTED)
    fs.text(cv, 0.795, row_mid[0], f"+{reuse_gain:.2f}", size=FS_MIN, color=INK, ha="left")
    fs.text(cv, 0.795, row_mid[1], f"+{value[('quota', 2)] - value[('quota', 1)]:.2f}", size=FS_MIN, color=INK, ha="left")
    fs.text(cv, 0.440, 0.215, "配额增益", size=FS_MIN, color=MUTED, ha="right")
    fs.text(cv, 0.420, 0.140, f"+{quota_gain:.2f}", size=FS_MIN, color=INK)
    fs.text(cv, 0.665, 0.140, f"+{pair:.2f}", size=FS_MIN, color=INK)
    note(cv, 0.500, 0.050, "两机制联合增益 +3.23 个百分点，低于两单臂增益之和 +4.65，呈亚可加", ha="center")


# ------------------------------------------------------------------ 图 3-8


def draw_yearly(ctx: dict[str, Any]) -> None:
    """图3-8 12 个测试年度上三种配置的逐年 F1。"""

    cv: fs.Canvas = ctx["cv"]
    reads: dict[str, rd.ArmReadout] = ctx["readouts"]
    rect = (0.150, 0.225, 0.828, 0.610)
    ax = data_axes(cv, rect)

    series = (
        ("m200", "全局蓄水池 复用 1", "dashed"),
        ("quota", "按年度配额 复用 1", "dashdot"),
        ("quota_r2", "按年度配额 复用 2（本章方法）", "solid"),
    )
    xs = list(rd.TEST_YEARS)
    for key, name, style in series:
        ls, marker, color = STYLE[style]
        values = [reads[key].f1_percent()[year] for year in xs]
        ax.plot(xs, values, color=color, linestyle=ls, linewidth=fs.MAIN_LINE_PT, label=name, zorder=4)
        ax.plot(
            xs,
            values,
            marker=marker,
            markersize=3.2,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=0.8,
            linestyle="none",
            zorder=5,
        )

    ax.set_xticks(xs)
    tick_labels(ax, "x", [str(year) for year in xs])
    ax.set_xlim(xs[0] - 0.6, xs[-1] + 0.6)
    ax.set_ylim(0.0, 105.0)
    ax.set_yticks([0, 25, 50, 75, 100])
    tick_labels(ax, "y", ["0", "25", "50", "75", "100"])
    axis_label(ax, "x", "测试年度")
    axis_label(ax, "y", "F1（%）")

    ax.annotate(
        "2025 年测试分片仅 5 条正例，\n该年 F1 恒为 0，不作比较依据",
        xy=(2025, 1.0),
        xytext=(2020.4, 21.0),
        fontsize=FS_MIN,
        color=MUTED,
        ha="center",
        arrowprops={"arrowstyle": "-|>", "linewidth": 0.7, "color": MUTED},
        zorder=8,
    )
    legend_rows = (
        ("全局蓄水池 复用 1", "dashed"),
        ("按年度配额 复用 1", "dashdot"),
        ("按年度配额 复用 2（本章方法）", "solid"),
    )
    for index, (name, style) in enumerate(legend_rows):
        ls, _, color = STYLE[style]
        y = 0.955 - index * 0.058
        cv.ax.plot([0.170, 0.228], [y, y], color=color, linestyle=ls, linewidth=fs.MAIN_LINE_PT)
        tag(cv, 0.236, y, name, color=color)


# ------------------------------------------------------------------ 图 3-9


def draw_buffer_audit(ctx: dict[str, Any]) -> None:
    """图3-9 官方蓄水池的年度构成审计（零训练）：槽位数与其中的正例数。"""

    cv: fs.Canvas = ctx["cv"]
    rect = (0.140, 0.285, 0.840, 0.555)
    ax = data_axes(cv, rect)

    years = [row[0] for row in rd.BUFFER_AUDIT]
    slots = [row[1] for row in rd.BUFFER_AUDIT]
    positives = [row[2] for row in rd.BUFFER_AUDIT]
    xs = np.arange(len(years), dtype=float)

    ax.bar(
        xs,
        slots,
        width=0.54,
        facecolor="#E8E8E8",
        edgecolor=INK,
        linewidth=0.7,
        hatch="",
        zorder=3,
    )
    ax.bar(
        xs,
        positives,
        width=0.54,
        facecolor="#9E9E9E",
        edgecolor=INK,
        linewidth=0.7,
        hatch="//",
        zorder=4,
    )
    # 正例数标注紧贴正例柱顶，避免读者把它误读为槽位数。
    for x, positive in zip(xs, positives, strict=True):
        ax.text(
            x,
            positive + 0.8,
            f"{positive}",
            ha="center",
            va="bottom",
            fontsize=FS_MIN,
            color=INK,
            zorder=6,
        )

    ax.set_xticks(xs)
    tick_labels(ax, "x", [str(year) for year in years])
    ax.set_xlim(-0.6, len(years) - 0.4)
    ax.set_ylim(0.0, 29.0)
    ax.set_yticks([0, 10, 20])
    tick_labels(ax, "y", ["0", "10", "20"])
    axis_label(ax, "x", "年度")
    axis_label(ax, "y", "缓冲槽位数（条）")

    legend_rows = (
        ("缓冲槽位数", "#E8E8E8", ""),
        ("其中的正例数", "#9E9E9E", "//"),
    )
    for index, (name, face, hatch) in enumerate(legend_rows):
        y = 0.930 - index * 0.055
        cv.ax.add_patch(
            fs.Rectangle((0.165, y - 0.020), 0.048, 0.040, facecolor=face, edgecolor=INK, linewidth=0.7)
        )
        cv.ax.add_patch(fs.Rectangle((0.165, y - 0.020), 0.048, 0.040, facecolor="none", hatch=hatch, edgecolor=INK, linewidth=0.7))
        tag(cv, 0.222, y, name, color=INK)
    note(cv, 0.500, 0.160, "2024 与 2025 年度缓冲中正例数为 0；2023 年度 14 个槽位中仅 1 条正例", ha="center")
    note(cv, 0.500, 0.095, "容量 200 条，官方全局蓄水池运行至 12 个年度结束；零训练审计", ha="center")


# ------------------------------------------------------------------ 图 3-10


def draw_gap_channels(ctx: dict[str, Any]) -> None:
    """图3-10 缺口的漂移通道与枯竭通道在若干容量下的对比（式 3-14）。"""

    cv: fs.Canvas = ctx["cv"]
    rows: list[tuple[str, dict[str, float]]] = ctx["gaps"]
    rect = (0.150, 0.285, 0.820, 0.600)
    ax = data_axes(cv, rect)

    xs = np.arange(len(rows), dtype=float)
    drift = [row[1]["drift"] for row in rows]
    depletion = [row[1]["depletion"] for row in rows]
    total = [row[1]["total"] for row in rows]

    ax.plot(xs, drift, color=fs.M1_EDGE, linestyle="-", linewidth=1.4, zorder=5)
    ax.plot(
        xs, drift, marker="o", markersize=3.8, markerfacecolor="white",
        markeredgecolor=fs.M1_EDGE, markeredgewidth=0.9, linestyle="none", zorder=6,
    )
    ax.plot(xs, depletion, color=fs.M2_EDGE, linestyle="--", linewidth=1.4, zorder=5)
    ax.plot(
        xs, depletion, marker="s", markersize=3.8, markerfacecolor="white",
        markeredgecolor=fs.M2_EDGE, markeredgewidth=0.9, linestyle="none", zorder=6,
    )
    ax.plot(xs, total, color=INK, linestyle="-.", linewidth=1.1, zorder=4)
    ax.plot(
        xs, total, marker="^", markersize=3.4, markerfacecolor="white",
        markeredgecolor=INK, markeredgewidth=0.8, linestyle="none", zorder=6,
    )

    ax.set_xticks(xs)
    tick_labels(ax, "x", [row[0] for row in rows])
    ax.set_xlim(-0.5, len(rows) - 0.5)
    ax.set_ylim(0.0, 18.0)
    ax.set_yticks([0, 5, 10, 15])
    tick_labels(ax, "y", ["0", "5", "10", "15"])
    axis_label(ax, "x", "缓冲容量（条）")
    axis_label(ax, "y", "缺口（百分点）")

    legend_rows = (
        ("漂移通道（九年集合，式 3-14 左项）", fs.M1_EDGE, "-"),
        ("枯竭通道（三年集合，式 3-14 右项）", fs.M2_EDGE, "--"),
        ("总缺口", INK, "-."),
    )
    for index, (name, color, ls) in enumerate(legend_rows):
        y = 0.950 - index * 0.058
        cv.ax.plot([0.185, 0.243], [y, y], color=color, linestyle=ls, linewidth=fs.MAIN_LINE_PT)
        tag(cv, 0.251, y, name, color=color)
    note(cv, 0.500, 0.115, "漂移通道在容量 50 条处即大幅收窄；枯竭通道在容量增至 18,854 条时仍仅收窄过半", ha="center")


# ------------------------------------------------------------------ 图 3-11


def draw_positive_rate(ctx: dict[str, Any]) -> None:
    """图3-11 各年度训练分片的正例率（对数纵轴）。"""

    cv: fs.Canvas = ctx["cv"]
    reads: dict[str, rd.ArmReadout] = ctx["readouts"]
    rates = rd.positive_rate_percent(reads["naive"])
    rect = (0.150, 0.285, 0.830, 0.565)
    ax = data_axes(cv, rect)

    years = list(rd.TEST_YEARS)
    values = [rates[year] for year in years]
    xs = np.arange(len(years), dtype=float)
    ax.bar(xs, values, width=0.58, facecolor="#DCDCDC", edgecolor=INK, linewidth=0.7, zorder=3)
    for x, value in zip(xs, values, strict=True):
        ax.text(
            x,
            value * 1.22,
            f"{value:.2f}" if value < 1.0 else f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=FS_MIN,
            color=INK,
            zorder=6,
        )

    ax.set_yscale("log")
    ax.set_xticks(xs)
    tick_labels(ax, "x", [str(year) for year in years])
    ax.set_xlim(-0.6, len(years) - 0.4)
    ax.set_ylim(0.02, 200.0)
    ax.minorticks_off()
    ax.set_yticks([0.1, 1.0, 10.0, 100.0])
    tick_labels(ax, "y", ["0.1", "1", "10", "100"])
    axis_label(ax, "x", "年度")
    axis_label(ax, "y", "正例率（%，对数刻度）")
    note(
        cv,
        0.500,
        0.165,
        "2023 至 2025 三个年度的正例率依次为 14.52%、1.64% 与 0.05%，末期发生先验塌缩",
        ha="center",
    )
    note(cv, 0.500, 0.100, "正例率由各年度测试分片的 n_pos/n 直接给出，与训练分片类别构成一致（3.2.1）", ha="center")


# ------------------------------------------------------------------ 清单

WITHDRAWN_LEGACY: tuple[dict[str, str], ...] = (
    {
        "stem": "图3-10-攻击类别分面",
        "withdrawn_at": "2026-08-26",
        "reason": "旧图取自已作废的 runs/diagnostics/ch3-full 运行；当前权威制品（正式 CPA×ELP 四格 BF16 运行、统一指标总表、共同首次告警预算包络）均不含任何按攻击类别的分面字段，无法换底重绘。",
        "recovery": "若正文保留攻击类别分面，需要新增一次按 Category 字段分面的目标年评价运行；在此之前正文不应引用图 3-10。",
        "files_moved_to": "作废/",
    },
    {
        "stem": "图3-3-因果前缀跨流聚合",
        "withdrawn_at": "2026-08-31",
        "reason": "旧图描述的因果前缀跨流聚合（CPA）已不是第三章的当前机制；第三章重锚到 CEM-BER 后，表示层机制改为因果实体记忆的读写与交叉注意力。",
        "recovery": "若正文重新采用因果前缀聚合，须先恢复对应机制合同再重绘。",
        "files_moved_to": "作废/",
    },
    {
        "stem": "图3-4-实体级可学Lp池化",
        "withdrawn_at": "2026-08-31",
        "reason": "旧图描述的实体级可学幂平均池化（ELP）已不是第三章的当前机制；第三章重锚到 CEM-BER 后，决策层机制改为预算感知实体排序的训练目标。",
        "recovery": "若正文重新采用可学幂平均池化，须先恢复对应机制合同再重绘。",
        "files_moved_to": "作废/",
    },
    {
        "stem": "图3-1-整体方法框架 等 11 幅旧线图件",
        "withdrawn_at": "2026-10-14",
        "reason": "第三章宿主由流量检测数据（LSPR/TQH-C2）重锚到 LAMDA 年度序列，全部机制与实验面板更换：表示层与决策层机制、消融对象、指标口径、数据来源均不再对应。旧图取自已停用的 runs/diagnostics/ch3-* 运行制品，与新章的权威制品（runs/diagnostics/ch3-lamda-domain-il-e4-replication-v1/）无重合。涉及 图3-1-整体方法框架、图3-2-二IP无向对序列构造、图3-3-因果实体记忆的读写与交叉注意力、图3-4-预算感知实体排序的目标构造、图3-5-六个方法在三个指标上的相对位置、图3-6-双机制消融交互、图3-7-训练稳定性、图3-8-Lp指数收敛轨迹、图3-9-实体流数分桶敏感性、图3-11-受限观测下的检测能力、图3-12-检出率随告警预算的变化。图号随之释放，由 LAMDA 线的新图占用。",
        "recovery": "需要恢复旧线图件时，须先在对应工作树恢复流量检测宿主合同与 runs/diagnostics/ch3-* 制品，再重绘；本工作树不承载该路线。",
        "files_moved_to": "作废/",
    },
)


# 每张图的数据来源键路径：图内每个数字指回制品文件与字段，供追溯。
DATA_KEYS: dict[str, list[str]] = {
    "图3-5-存储容量与检测能力的关系": [
        "样本侧曲线：metrics_expreplay_m50.json、metrics_expreplay.json、metrics_expreplay_m400.json、metrics_expreplay_m800.json、metrics_expreplay_m18854.json 的 records[experience=2025, mode=backward].f1 十二年均值；横轴为 N×4561/8/1024 KiB",
        "参数侧三点：metrics_freemoca.json、metrics_lwf.json、metrics_ewc.json 同口径均值；横轴为 2,687,293×4/1024 KiB 与其两倍",
        "朴素端点：metrics_naive.json 同口径均值",
        "联合上界：metrics_cumulative.json 同口径均值；横轴为 806,700 条样本的缓冲存储",
    ],
    "图3-6-复用倍数与检测能力": [
        "metrics_expreplay.json（m=1）、metrics_expreplay_m200_r2.json（m=2）、metrics_expreplay_m200_r4.json（m=4）、metrics_expreplay_m200_r8.json（m=8）的 records[experience=2025, mode=backward].f1 十二年均值",
    ],
    "图3-7-双机制消融": [
        "全局蓄水池×复用1：metrics_expreplay.json；全局蓄水池×复用2：metrics_expreplay_m200_r2.json",
        "按年度配额×复用1：metrics_expreplay_m200_quota.json；按年度配额×复用2：metrics_expreplay_m200_quota_r2.json",
        "四格读数均为 records[experience=2025, mode=backward].f1 的十二年均值；边栏增益由这四处读数作差得到",
    ],
    "图3-8-逐年检测能力分解": [
        "metrics_expreplay.json、metrics_expreplay_m200_quota.json、metrics_expreplay_m200_quota_r2.json 的 records[experience=2025, mode=backward].f1，按 test_year 逐年取值",
        "2025 年度的 n_pos=5 来自同批 records 的 n_pos 字段",
    ],
    "图3-9-缓冲年度构成审计": [
        "缓冲槽位数与其中的正例数：resultdata_lamda.BUFFER_AUDIT 外部给定常数表（无对应制品字段，来源见 external_constants）",
    ],
    "图3-10-缺口的两级分解": [
        "metrics_naive.json、metrics_expreplay_m50.json、metrics_expreplay.json、metrics_expreplay_m400.json、metrics_expreplay_m800.json、metrics_expreplay_m18854.json 与 metrics_cumulative.json 的逐测试年 f1",
        "漂移通道与枯竭通道由 resultdata_lamda.gap_channels_percent 按式 (3-14) 的 9/12 与 3/12 权重重算，并断言与总缺口相等",
    ],
    "图3-11-各年度正例率": [
        "metrics_naive.json 的 records[experience=2025, mode=backward].n_pos 与其同条的 n，按 test_year 取比值",
    ],
}


def finalize_manifest(ctx: dict[str, Any]) -> None:
    """补记 `figstyle.write_manifest` 未覆盖的字段：数学字体、生成器清单、撤下段、制品哈希。

    `figstyle.write_manifest` 会把每条 `entry["evidence_mode"]` 覆写为同一个常量，图3-9 的
    外部给定常数标记因此必须在其之后重新逐图写回；`data_keys` 与逐图证据等级同理。
    """

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    typography = data["typography"]
    typography["math_fontset"] = "stix（回退）" if fs.MATH_FONT is None else fs.MATH_FONT.family
    typography["math_font_path"] = None if fs.MATH_FONT is None else fs.MATH_FONT.path

    environment = data["environment"]
    generators = environment.get("generators")
    if not isinstance(generators, list):
        generators = [environment.get("generator")]
    for name in (MECHANISM_GENERATOR, GENERATOR):
        if name not in generators:
            generators.append(name)
    environment["generators"] = sorted({g for g in generators if g})
    environment["generator"] = GENERATOR

    for entry in data["figures"]:
        stem = str(entry["stem"])
        entry["data_keys"] = DATA_KEYS.get(stem, ["机制示意图，不承载实验数据"])
        if stem in ctx["evidence"]:
            entry["evidence_mode"] = ctx["evidence"][stem]

    data["withdrawn"] = list(WITHDRAWN_LEGACY)
    data["readout_contract"] = {
        "report_experience": rd.REPORT_EXPERIENCE,
        "mode": rd.REPORT_MODE,
        "metric": "12 个测试年度 F1 的算术平均（式 3-21）",
        "note": "forward 与 backward 语义不同，本清单全部读数只取 backward",
    }
    data["artifacts"] = ctx["registry"].dump()
    data["external_constants"] = [
        {
            "figure": "图3-9-缓冲年度构成审计",
            "values": "各年度缓冲槽位数与其中正例数",
            "source": rd.BUFFER_AUDIT_SOURCE,
        }
    ]
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ 主流程


def main() -> int:
    registry = rd.Registry()
    readouts = rd.load_all(registry)

    gaps: list[tuple[str, dict[str, float]]] = []
    for key, label in (
        ("naive", "0"),
        ("m50", "50"),
        ("m200", "200"),
        ("m400", "400"),
        ("m800", "800"),
        ("m18854", "18 854"),
    ):
        gaps.append((label, rd.gap_channels_percent(registry, readouts[key], readouts["cumulative"])))

    specs: tuple[tuple[str, str, float, float, object, dict[str, Any]], ...] = (
        (
            "图3-5-存储容量与检测能力的关系",
            "存储占用（对数刻度）与末年在 12 个测试年度上的平均 F1。实线带实心圆为官方回放的"
            "容量档位 50/200/400/800/18,854 条；虚线带空心方块为本章方法在同一组容量点上的"
            "读数（构成方式与复用分配固定为默认配置，只改变容量）；空心标记为参数侧三种形态；"
            "水平虚线为朴素更新（存储 0）；星号为联合训练上界。"
            "竖细线标出 10.25 MB 处样本侧与参数侧的等预算对照。"
            "两条样本侧曲线以线型与标记填充区分，不依赖颜色，灰度打印下可辨。",
            150.0,
            92.0,
            draw_storage_curve,
            {"readouts": readouts},
        ),
        (
            "图3-6-复用倍数与检测能力",
            "缓冲容量固定 200 条时，复用倍数 1、2、4、8 对应的跨年平均 F1。曲线在倍数 4 处"
            "取得内部最优，倍数 8 回落，与 3.5.4 的保持—适应权衡一致。",
            132.0,
            88.0,
            draw_reuse_curve,
            {"readouts": readouts},
        ),
        (
            "图3-7-双机制消融",
            "缓冲构成方式（全局蓄水池 / 按年度配额）× 复用倍数（1 / 2）的 2×2 对照，"
            "格内为跨年平均 F1。深色高亮格为本章方法。右侧边栏给出复用倍数在两个构成方式"
            "下的增益，下侧边栏给出按年度配额在两个复用倍数下的增益。",
            130.0,
            92.0,
            draw_ablation,
            {"readouts": readouts},
        ),
        (
            "图3-8-逐年检测能力分解",
            "三种配置在 12 个测试年度上的 F1。2025 年度测试分片仅含 5 条正例，任何配置在该"
            "年度的 F1 均为 0，在图内单独标注，不作配置优劣的比较依据。",
            150.0,
            92.0,
            draw_yearly,
            {"readouts": readouts},
        ),
        (
            "图3-9-缓冲年度构成审计",
            "官方全局蓄水池在容量 200 条下运行至 12 个年度结束时，六个代表年度的缓冲槽位数"
            "与其中正例数（零训练审计）。2024 与 2025 年度的正例数为 0。该组数值无对应制品"
            "字段，来源为外部给定常数，登记于图件清单的 external_constants 段。",
            140.0,
            90.0,
            draw_buffer_audit,
            {},
        ),
        (
            "图3-10-缺口的两级分解",
            "按式 (3-14) 把联合上界与有限容量配置之间的总缺口分解为漂移通道（九年集合）与"
            "枯竭通道（三年集合），横轴为缓冲容量档位。漂移通道在容量 50 条处即大幅收窄，"
            "枯竭通道收窄缓慢。总缺口为两条通道按 9/12 与 3/12 权重的合成。",
            140.0,
            92.0,
            draw_gap_channels,
            {"gaps": gaps},
        ),
        (
            "图3-11-各年度正例率",
            "12 个年度训练分片的恶意样本占比（对数纵轴），由各年度测试分片的 n_pos/n 直接"
            "给出（3.2.1 规定两个分片类别构成一致）。2023 至 2025 三个年度依次为 14.52%、"
            "1.64% 与 0.05%，末期发生先验塌缩。",
            150.0,
            90.0,
            draw_positive_rate,
            {"readouts": readouts},
        ),
    )

    evidence = {
        "图3-9-缓冲年度构成审计": "外部给定常数（零训练审计）",
    }
    entries: list[dict[str, Any]] = []
    for stem, caption, width_mm, height_mm, draw, context in specs:
        cv = fs.canvas(width_mm, height_mm)
        context = dict(context)
        context["cv"] = cv
        draw(context)
        spec = fs.FigureSpec(stem, width_mm, height_mm, None, caption)
        entry = fs.save_figure(ROOT, spec, cv)
        entry["evidence_mode"] = evidence.get(stem, "权威制品重算（ch3-lamda-domain-il-e4-replication-v1）")
        entries.append(entry)

    for line in fs.verify_outputs(ROOT, entries):
        logger.info(line)

    fs.write_manifest(
        ROOT,
        GENERATOR,
        entries,
        evidence_mode="权威制品重算（ch3-lamda-domain-il-e4-replication-v1）",
    )
    finalize_manifest({"registry": registry, "evidence": evidence})
    logger.info("已写出 %d 张结果图与 %s", len(entries), MANIFEST_PATH.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
