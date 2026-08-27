"""生成第三章实验结果图（图3-5、图3-6、图3-7、图3-8、图3-9、图3-11、图3-12）。

数据只来自 `resultdata.py` 登记的权威制品，图内每个数字都可指回制品字段；本脚本不含
任何手工录入的实验数值。字体、尺寸与灰度可读规格来自 `figstyle.py`，与机制图同源，
不再自建字体解析——`.ttc` 未指定 face_index 曾使图 3-5 至图 3-11 内嵌繁体 STHeitiTC，
该根因已由改用 `figstyle.resolve_cjk_font()` 关闭。

图 3-10（攻击类别分面）在当前权威制品中没有任何按攻击类别的分面字段，已随本次改造
撤下，理由与恢复路径写在 `图件清单.json` 的 `withdrawn` 段。

执行：uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章结果图.py
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))

import figstyle as fs
import numpy as np
import resultdata as rd
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "图件清单.json"
GENERATOR = "绘制第三章结果图.py"
MECHANISM_GENERATOR = "绘制第三章机制图.py"

INK, MUTED, HAIRLINE = fs.INK, fs.MUTED, fs.HAIRLINE
GRID = "#D9D9D9"
ACCENT = fs.M2_EDGE
FS_MIN, FS_MAIN = fs.MIN_FONT_PT, fs.MAIN_FONT_PT

# 四格填充：明度单调递增，配合填充图案，灰度打印仍可区分。
CELL_FILL = {"B00": "#F2F2F2", "B10": "#C9C9C9", "O01": "#8F8F8F", "O11": "#4A4A4A"}
CELL_HATCH = {"B00": "", "B10": "//", "O01": "..", "O11": "xx"}

plt.rcParams.update(
    {
        "axes.labelsize": FS_MAIN,
        "axes.titlesize": FS_MAIN,
        "legend.fontsize": FS_MIN,
        "font.size": FS_MIN,
        "grid.linewidth": fs.AUX_LINE_PT,
        "lines.linewidth": fs.MAIN_LINE_PT,
        "hatch.linewidth": fs.AUX_LINE_PT,
        "axes.edgecolor": INK,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
    }
)


# ------------------------------------------------------------------ 版面原语


def new_figure(width_mm: float, height_mm: float) -> Figure:
    if width_mm > fs.MAX_WIDTH_MM:
        raise ValueError(f"宽度 {width_mm} mm 超过合同上限 {fs.MAX_WIDTH_MM} mm")
    if height_mm > fs.MAX_HEIGHT_MM:
        raise ValueError(f"高度 {height_mm} mm 超过合同上限 {fs.MAX_HEIGHT_MM} mm")
    return plt.figure(figsize=(width_mm / 25.4, height_mm / 25.4), dpi=200)


def style_axes(ax: Axes, *, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=fs.AUX_LINE_PT, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, pad=1.5, width=0.7)


def say(
    fig: Figure,
    x: float,
    y: float,
    value: str,
    *,
    size: float = FS_MIN,
    color: str = INK,
    ha: str = "center",
    va: str = "bottom",
    box: str | None = None,
) -> None:
    """图面文字，逐字核验字形覆盖后再落笔。"""

    fs.check_label(value, size)
    kwargs: dict[str, Any] = {
        "ha": ha,
        "va": va,
        "fontsize": size,
        "color": color,
        "linespacing": 1.32,
    }
    if box is not None:
        kwargs["bbox"] = {
            "boxstyle": "round,pad=0.3",
            "facecolor": "white",
            "edgecolor": box,
            "linewidth": 0.7,
        }
    fig.text(x, y, value, **kwargs)


def ticks(ax: Axes, axis: str, labels: list[str], size: float = FS_MIN) -> None:
    for label in labels:
        fs.check_label(label, size)
    setter = ax.set_xticklabels if axis == "x" else ax.set_yticklabels
    setter(labels, fontsize=size, linespacing=1.2)


def label(ax: Axes, axis: str, value: str) -> None:
    fs.check_label(value, FS_MAIN)
    (ax.set_xlabel if axis == "x" else ax.set_ylabel)(value, fontsize=FS_MAIN, labelpad=3)


def title(ax: Axes, value: str) -> None:
    fs.check_label(value, FS_MAIN)
    ax.set_title(value, fontsize=FS_MAIN, pad=3)


# ------------------------------------------------------------------ 图 3-5


def draw_method_positions(ctx: dict[str, Any]) -> Figure:
    """图 3-5 六个方法在三个指标上的相对位置。"""

    rows = sorted(ctx["methods"], key=lambda m: m.entity_ap, reverse=True)
    fig = new_figure(165, 95)
    panels = (
        ("(a) 逐流\n平均精确率", [m.flow_ap for m in rows], 0.40),
        ("(b) 实体\n平均精确率", [m.entity_ap for m in rows], 0.70),
        ("(c) 检出率\n（4% 假阳率预算）", [m.dr_at_4pct for m in rows], 1.00),
    )
    # 面板之间留 9 mm 空档，避免相邻面板的首尾刻度标签相撞。
    lefts = (0.265, 0.505, 0.745)
    ypos = np.arange(len(rows))[::-1]

    for (name, values, upper), left in zip(panels, lefts, strict=True):
        ax = fig.add_axes((left, 0.335, 0.185, 0.545))
        style_axes(ax, grid_axis="x")
        for y, row, value in zip(ypos, rows, values, strict=True):
            own = row.config_type == "骨干专属全容量配方"
            face = CELL_FILL["O11"] if own else "white"
            hatch = "xx" if own else ("///" if row.has_complete_curve else "\\\\")
            edge = INK if own else MUTED
            ax.barh(
                y,
                value,
                height=0.64,
                facecolor=face,
                edgecolor=edge,
                linewidth=0.9,
                hatch=hatch,
                zorder=3,
            )
            ax.text(
                value + upper * 0.035,
                y,
                f"{value:.4f}",
                va="center",
                ha="left",
                fontsize=FS_MIN,
                color=INK,
                zorder=4,
            )
        ax.set_yticks(ypos)
        ax.set_ylim(-0.66, len(rows) - 0.34)
        ax.set_xlim(0.0, upper)
        ax.set_xticks(np.linspace(0.0, upper, 3))
        ticks(ax, "x", [f"{v:.2f}" for v in np.linspace(0.0, upper, 3)])
        title(ax, name)
        if left == lefts[0]:
            ticks(ax, "y", [m.display_name for m in rows])
        else:
            ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=CELL_FILL["O11"], edgecolor=INK, hatch="xx", linewidth=0.9),
        plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=MUTED, hatch="///", linewidth=0.9),
        plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=MUTED, hatch="\\\\", linewidth=0.9),
    ]
    labels = [
        "本章方法",
        "已发表配置基线，有完整告警预算曲线，(c) 取实际可达工作点",
        "已发表配置基线，只持久化名义 4% 单点，(c) 无实际假阳率收据",
    ]
    for item in labels:
        fs.check_label(item, FS_MIN)
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.108),
        frameon=True,
        framealpha=1.0,
        edgecolor=GRID,
        fontsize=FS_MIN,
        borderpad=0.4,
        handlelength=1.6,
        handleheight=1.0,
        labelspacing=0.34,
    )
    meta = ctx["meta"]
    say(
        fig,
        0.5,
        0.030,
        f"LSPR23 训练、LSPR24 评价；{meta['entity_count']:,} 个实体，其中正实体 "
        f"{meta['positive_entity_count']:,} 个\n"
        "各方法实体分数按其自身设计的聚合算子得到，均为单次运行",
        color=MUTED,
    )
    return fig


# ------------------------------------------------------------------ 图 3-6


def draw_ablation(ctx: dict[str, Any]) -> Figure:
    """图 3-6 因果前缀聚合与实体级幂平均池化的 2×2 消融。"""

    cells = ctx["cells"]
    effects = ctx["effects"]
    fig = new_figure(150, 90)
    panels = (
        ("(a) 实体平均精确率", lambda c: c.entity_ap, "实体平均精确率"),
        ("(b) 逐流平均精确率", lambda c: c.flow_ap, "逐流平均精确率"),
        ("(c) 检出率（实际假阳率 2%）", lambda c: c.dr_at_2pct, "检出率"),
    )
    lefts = (0.085, 0.400, 0.715)
    xs = np.arange(len(rd.CELL_ORDER))

    for (name, pick, ylabel), left in zip(panels, lefts, strict=True):
        ax = fig.add_axes((left, 0.400, 0.245, 0.485))
        style_axes(ax)
        values = [pick(cells[key]) for key in rd.CELL_ORDER]
        for x, key, value in zip(xs, rd.CELL_ORDER, values, strict=True):
            ax.bar(
                x,
                value,
                width=0.66,
                facecolor=CELL_FILL[key],
                edgecolor=INK,
                linewidth=0.9,
                hatch=CELL_HATCH[key],
                zorder=3,
            )
            ax.text(
                x,
                value + max(values) * 0.035,
                f"{value:.4f}",
                ha="center",
                va="bottom",
                fontsize=FS_MIN,
            )
        ax.set_ylim(0.0, max(values) * 1.30)
        ax.set_xticks(xs)
        ticks(ax, "x", ["基线", "仅 A", "仅 B", "A+B"])
        ax.set_xlim(-0.66, len(xs) - 0.34)
        label(ax, "y", ylabel)
        title(ax, name)

    say(
        fig,
        0.5,
        0.250,
        "A = 因果前缀跨流聚合，B = 实体级幂平均池化\n"
        "基线＝两个机制都不启用，A+B＝双机制并用（本章完整方法）",
        color=MUTED,
    )
    say(
        fig,
        0.5,
        0.112,
        f"以实体平均精确率计：A 单开 {effects['causal_prefix']:+.4f}，"
        f"B 单开 {effects['entity_pooling']:+.4f}，两者之和 {effects['sum']:+.4f}；"
        f"并用 {effects['combined']:+.4f}，交互项 {effects['interaction']:+.4f}\n"
        "两个单机制对基线均为正贡献，并用格在目标年四格中最高；交互项只作描述性读数",
        box=INK,
    )
    say(
        fig,
        0.5,
        0.024,
        "(c) 的四格实际假阳率依次为 "
        + "、".join(f"{cells[k].realized_fpr_at_2pct:.6f}" for k in rd.CELL_ORDER)
        + "；单种子 seed42",
        color=MUTED,
    )
    return fig


# ------------------------------------------------------------------ 图 3-7


def draw_training_stability(ctx: dict[str, Any]) -> Figure:
    """图 3-7 四格的逐轮源年验证表现与选中轮次。"""

    cells = ctx["cells"]
    fig = new_figure(140, 90)
    ax = fig.add_axes((0.130, 0.395, 0.845, 0.545))
    style_axes(ax, grid_axis="both")

    styles = {
        "B00": ("-", "o"),
        "B10": ((0, (5, 2)), "s"),
        "O01": ((0, (1, 1.6)), "^"),
        "O11": ((0, (5, 1.4, 1, 1.4)), "D"),
    }
    shades = {"B00": "#B0B0B0", "B10": "#8A8A8A", "O01": "#5A5A5A", "O11": INK}
    for key in rd.CELL_ORDER:
        cell = cells[key]
        epochs = [item[0] for item in cell.validation_history]
        values = [item[1] for item in cell.validation_history]
        style, marker = styles[key]
        name = rd.CELL_NAMES[key]
        fs.check_label(name, FS_MIN)
        ax.plot(
            epochs,
            values,
            linestyle=style,
            linewidth=fs.MAIN_LINE_PT,
            color=shades[key],
            marker=marker,
            markersize=2.8,
            markerfacecolor="white",
            markeredgewidth=0.7,
            label=name,
            zorder=3,
        )
        selected = cell.selected_epoch
        picked = values[epochs.index(selected)]
        ax.plot(
            selected,
            picked,
            marker=marker,
            markersize=5.4,
            markerfacecolor=shades[key],
            markeredgecolor=INK,
            markeredgewidth=0.8,
            linestyle="none",
            zorder=5,
        )

    ax.set_xlim(0.4, 20.6)
    ax.set_xticks([1, 5, 10, 15, 20])
    ticks(ax, "x", ["1", "5", "10", "15", "20"])
    ax.set_ylim(0.870, 1.004)
    ax.set_yticks([0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00])
    ticks(ax, "y", ["0.88", "0.90", "0.92", "0.94", "0.96", "0.98", "1.00"])
    label(ax, "x", "训练轮次")
    label(ax, "y", "源年验证逐流平均精确率")
    handles, texts = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        texts,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.115),
        ncol=2,
        frameon=True,
        framealpha=1.0,
        edgecolor=GRID,
        fontsize=FS_MIN,
        borderpad=0.4,
        labelspacing=0.32,
        columnspacing=1.4,
        handlelength=2.4,
    )
    spans = {
        key: max(v for _, v, _ in cells[key].validation_history)
        - min(v for _, v, _ in cells[key].validation_history)
        for key in rd.CELL_ORDER
    }
    say(
        fig,
        0.5,
        0.028,
        "实心大标记为按「验证逐流平均精确率最早最大」选中的轮次，依次为第 "
        + "、".join(str(cells[k].selected_epoch) for k in rd.CELL_ORDER)
        + " 轮\n二十轮取值的极差依次为 "
        + "、".join(f"{spans[k]:.4f}" for k in rd.CELL_ORDER)
        + "；20 轮跑满不早停，单种子 seed42",
        color=MUTED,
    )
    return fig


# ------------------------------------------------------------------ 图 3-8


def draw_pooling_exponent(ctx: dict[str, Any]) -> Figure:
    """图 3-8 实体级幂平均池化指数的逐轮轨迹。"""

    cells = ctx["cells"]
    fig = new_figure(130, 85)
    ax = fig.add_axes((0.135, 0.290, 0.825, 0.630))
    style_axes(ax, grid_axis="both")

    learnable = [key for key in rd.CELL_ORDER if cells[key].learned_p is not None]
    styles = {"O01": ((0, (1, 1.6)), "^", "#5A5A5A"), "O11": ("-", "D", INK)}
    # 标注落点：并用格向右上、单机制格向右下，避开 p = 1 参考线与图例。
    annotate_at = {"O11": (7.4, 1.94), "O01": (16.4, 0.70)}
    for key in learnable:
        cell = cells[key]
        epochs = [item[0] for item in cell.validation_history]
        values = [item[2] for item in cell.validation_history]
        style, marker, color = styles[key]
        name = rd.CELL_NAMES[key]
        fs.check_label(name, FS_MIN)
        ax.plot(
            epochs,
            values,
            linestyle=style,
            linewidth=fs.MAIN_LINE_PT,
            color=color,
            marker=marker,
            markersize=2.8,
            markerfacecolor="white",
            markeredgewidth=0.7,
            label=name,
            zorder=4,
        )
        selected = cell.selected_epoch
        ax.plot(
            selected,
            values[epochs.index(selected)],
            marker=marker,
            markersize=5.4,
            markerfacecolor=color,
            markeredgecolor=INK,
            markeredgewidth=0.8,
            linestyle="none",
            zorder=5,
        )
        note = f"选中第 {selected} 轮，p = {cell.learned_p:.4f}"
        fs.check_label(note, FS_MIN)
        ax.annotate(
            note,
            xy=(selected, values[epochs.index(selected)]),
            xytext=annotate_at[key],
            fontsize=FS_MIN,
            color=INK,
            ha="center",
            va="center",
            arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.8, "shrinkB": 3},
            bbox={"boxstyle": "round,pad=0.26", "facecolor": "white", "edgecolor": color, "linewidth": 0.7},
            zorder=6,
        )

    frozen = [key for key in rd.CELL_ORDER if cells[key].learned_p is None]
    ax.axhline(2.0, color=MUTED, linestyle=(0, (4, 2)), linewidth=fs.AUX_LINE_PT, zorder=2)
    ax.text(20.4, 2.04, "p = 2（未启用池化两格的初值）", ha="right", va="bottom", fontsize=FS_MIN, color=MUTED)
    ax.axhline(1.0, color=ACCENT, linestyle=(0, (4, 2)), linewidth=fs.MAIN_LINE_PT, zorder=2)
    ax.text(1.0, 1.03, "p = 1（算术平均）", ha="left", va="bottom", fontsize=FS_MIN, color=ACCENT)

    ax.set_xlim(0.4, 20.6)
    ax.set_xticks([1, 5, 10, 15, 20])
    ticks(ax, "x", ["1", "5", "10", "15", "20"])
    ax.set_ylim(0.55, 2.30)
    label(ax, "x", "训练轮次")
    label(ax, "y", "实体级幂平均池化指数 p")
    handles, texts = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        texts,
        loc="lower left",
        bbox_to_anchor=(0.02, 0.02),
        frameon=True,
        framealpha=1.0,
        edgecolor=GRID,
        fontsize=FS_MIN,
        borderpad=0.35,
        labelspacing=0.3,
        handlelength=2.4,
    )
    say(
        fig,
        0.5,
        0.040,
        "两条可学轨迹都从初值 p = 2 单调下行\n"
        + "未启用池化的"
        + "、".join(rd.CELL_NAMES[k] for k in frozen)
        + "两格 p 恒为 2 且不参与训练，未画线",
        color=MUTED,
    )
    return fig


# ------------------------------------------------------------------ 图 3-9


def draw_length_buckets(ctx: dict[str, Any]) -> Figure:
    """图 3-9 按实体流数分桶的四格检测能力。"""

    cells = ctx["cells"]
    buckets = [item["bucket"] for item in cells["B00"].length_buckets]
    fig = new_figure(150, 90)
    ax = fig.add_axes((0.095, 0.400, 0.885, 0.560))
    style_axes(ax)

    xs = np.arange(len(buckets))
    width = 0.20
    for offset, key in zip(np.linspace(-1.5, 1.5, 4) * width, rd.CELL_ORDER, strict=True):
        values = [float(item["entity_average_precision"]) for item in cells[key].length_buckets]
        name = rd.CELL_NAMES[key]
        fs.check_label(name, FS_MIN)
        ax.bar(
            xs + offset,
            values,
            width=width,
            facecolor=CELL_FILL[key],
            edgecolor=INK,
            linewidth=0.8,
            hatch=CELL_HATCH[key],
            label=name,
            zorder=3,
        )

    def bucket_label(raw: str) -> str:
        """把制品里的桶名转成中文区间；开区间桶写成「条以上」。"""

        low, _, high = raw.partition("-")
        return f"{low} 条以上" if high == "+" else f"{low}～{high} 条流"

    ax.set_xticks(xs)
    ticks(
        ax,
        "x",
        [
            f"{bucket_label(item['bucket'])}\n正实体 {item['positive_entities']:,}"
            for item in cells["B00"].length_buckets
        ],
    )
    ax.set_xlim(-0.58, len(buckets) - 0.42)
    ax.set_ylim(0.0, 0.80)
    label(ax, "x", "实体内流数分桶")
    label(ax, "y", "目标年实体平均精确率")
    handles, texts = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        texts,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.115),
        ncol=2,
        frameon=True,
        framealpha=1.0,
        edgecolor=GRID,
        fontsize=FS_MIN,
        borderpad=0.4,
        labelspacing=0.32,
        columnspacing=1.2,
        handlelength=1.6,
        handleheight=1.0,
    )
    say(
        fig,
        0.5,
        0.030,
        "分桶按实体在目标年的流数划分，五桶的实体与正实体数对四格相同\n"
        "最右两桶正实体分别只有 84 与 40 个，桶内取值不支持排序结论",
        color=MUTED,
    )
    return fig


# ------------------------------------------------------------------ 图 3-11


def draw_first_alert(ctx: dict[str, Any]) -> Figure:
    """图 3-11 完整方法在受限观测下的首次告警及时检出。"""

    steps = [s for s in ctx["first_alert"] if s.realized_fpr <= 0.08]
    dropped = [s for s in ctx["first_alert"] if s.realized_fpr > 0.08]
    fig = new_figure(140, 90)
    ax = fig.add_axes((0.125, 0.320, 0.845, 0.600))
    style_axes(ax, grid_axis="both")
    ax.set_xscale("log")

    styles = [("-", "o", INK), ((0, (5, 2)), "s", "#3F3F3F"), ((0, (1, 1.6)), "^", "#6E6E6E"), ((0, (5, 1.4, 1, 1.4)), "D", "#9A9A9A")]
    for step, (style, marker, color) in zip(steps, styles, strict=True):
        xs = np.asarray(step.exposure_index, dtype=float)
        ys = np.asarray(step.on_time_detection_rate, dtype=float)
        keep = xs >= 1
        name = f"实际首次告警假阳率 {step.realized_fpr * 100:.2f}%"
        fs.check_label(name, FS_MIN)
        ax.step(
            xs[keep],
            ys[keep],
            where="post",
            linestyle=style,
            linewidth=fs.MAIN_LINE_PT,
            color=color,
            marker=marker,
            markersize=2.8,
            markerfacecolor="white",
            markeredgewidth=0.7,
            label=name,
            zorder=4,
        )
        ax.text(
            1.0,
            ys[keep][0] + 0.014,
            f"{ys[keep][0]:.4f}",
            ha="left",
            va="bottom",
            fontsize=FS_MIN,
            color=color,
            zorder=6,
            bbox={"boxstyle": "square,pad=0.10", "facecolor": "white", "edgecolor": "none"},
        )

    ax.set_xlim(0.85, 2.4e4)
    ax.set_xticks([1, 10, 100, 1000, 10000])
    ticks(ax, "x", ["1", "10", "100", "1000", "10000"])
    ax.minorticks_off()
    ax.set_ylim(0.0, 0.82)
    label(ax, "x", "实体内已观测到的流数（对数刻度）")
    label(ax, "y", "及时检出率（分母为全部正实体）")
    handles, texts = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        texts,
        loc="lower right",
        frameon=True,
        framealpha=1.0,
        edgecolor=GRID,
        fontsize=FS_MIN,
        borderpad=0.35,
        labelspacing=0.3,
        handlelength=2.4,
    )
    say(
        fig,
        0.5,
        0.038,
        "每条阶梯为「在实体的前若干条流之内已经首次告警」的正实体占比，分母固定为 "
        f"{ctx['meta']['positive_entity_count']:,} 个正实体\n"
        f"名义 4% 与 8% 两档的首次告警阈值落进并列块，实际假阳率达 "
        f"{dropped[0].realized_fpr * 100:.2f}%，预算不成立，故未画",
        color=MUTED,
    )
    return fig


# ------------------------------------------------------------------ 图 3-12


def draw_budget_curves(ctx: dict[str, Any]) -> Figure:
    """图 3-12 检出率随告警预算的变化。"""

    curves = ctx["budget_curves"]
    fig = new_figure(150, 95)
    ax = fig.add_axes((0.115, 0.300, 0.860, 0.625))
    style_axes(ax, grid_axis="both")
    ax.set_xscale("log")

    styles = [
        ("-", "o", INK),
        ((0, (5, 2)), "s", "#4A4A4A"),
        ((0, (1, 1.6)), "^", "#787878"),
        ((0, (5, 1.4, 1, 1.4)), "D", "#A6A6A6"),
    ]
    own = curves[0]
    for curve, (style, marker, color) in zip(curves, styles, strict=True):
        keep = (curve.realized_fpr >= 8e-5) & (curve.realized_fpr <= 0.08)
        fs.check_label(curve.display_name, FS_MIN)
        ax.plot(
            curve.realized_fpr[keep],
            curve.detection_rate[keep],
            linestyle=style,
            linewidth=fs.MAIN_LINE_PT,
            color=color,
            label=curve.display_name,
            zorder=4,
        )
        points = [curve.readout[n] for n in rd.NOMINAL_BUDGETS if curve.readout[n][0] <= 0.08]
        ax.plot(
            [p[0] for p in points],
            [p[1] for p in points],
            linestyle="none",
            marker=marker,
            markersize=4.0,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=0.9,
            zorder=5,
        )

    ceiling = own.reachable_fpr_ceiling
    ax.axvline(ceiling, color=ACCENT, linestyle=(0, (4, 2)), linewidth=fs.MAIN_LINE_PT, zorder=3)
    say(
        fig,
        0.795,
        0.345,
        f"本章方法可达上限\n实际假阳率 {ceiling * 100:.2f}%",
        color=ACCENT,
        ha="center",
    )

    ax.set_xlim(8e-5, 0.085)
    ax.set_xticks([1e-4, 1e-3, 1e-2, 0.08])
    ticks(ax, "x", ["0.01%", "0.1%", "1%", "8%"])
    ax.minorticks_off()
    ax.set_ylim(0.0, 0.92)
    label(ax, "x", "实体级实际假阳率（对数刻度）")
    label(ax, "y", "实体级检出率")
    handles, texts = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        texts,
        loc="upper left",
        frameon=True,
        framealpha=1.0,
        edgecolor=GRID,
        fontsize=FS_MIN,
        borderpad=0.35,
        labelspacing=0.3,
        handlelength=2.4,
    )
    meta = ctx["meta"]
    say(
        fig,
        0.5,
        0.038,
        "空心标记为名义 0.1%、0.5%、1%、2%、4%、8% 六档预算上的实际可达工作点；"
        f"{meta['negative_entity_count']:,} 个负实体、{meta['positive_entity_count']:,} 个正实体\n"
        f"本章方法曲线在实际假阳率 {ceiling * 100:.2f}% 之后落进并列块，"
        "下一可达点即为全告警，故 4% 与 8% 取同一工作点",
        color=MUTED,
    )
    return fig


# ------------------------------------------------------------------ 规格与产出


@dataclass(frozen=True)
class FigureSpec:
    stem: str
    width_mm: float
    height_mm: float
    draw: Callable[[dict[str, Any]], Figure]
    data_keys: tuple[str, ...]
    caption: str


SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        stem="图3-5-六个方法在三个指标上的相对位置",
        width_mm=165,
        height_mm=95,
        draw=draw_method_positions,
        data_keys=(
            "ch3-metrics-table-20260825b/lspr24-evaluation.json[].flow_ap",
            "ch3-metrics-table-20260825b/lspr24-evaluation.json[].entity_ap",
            "ch3-metrics-table-20260825b/lspr24-evaluation.json[].dr_fpr_0.04",
            "ch3-metrics-table-20260825b/lspr24-evaluation.json[].actual_fpr_fpr_0.04",
        ),
        caption=(
            "图3-5　六个方法在三个指标上的相对位置（LSPR23 训练、LSPR24 评价，47,115 个实体、"
            "其中正实体 752 个，三个面板依次为逐流平均精确率、实体平均精确率与假阳率 4% 预算下的检出率，"
            "各方法实体分数按其自身设计的聚合算子得到，各点为单次运行；随机森林与已发表配置 XGBoost "
            "只持久化名义 4% 单点，没有实际假阳率收据，以不同填充图案标出）"
        ),
    ),
    FigureSpec(
        stem="图3-6-双机制消融交互",
        width_mm=150,
        height_mm=90,
        draw=draw_ablation,
        data_keys=(
            "bf16/aggregate-results.json target_year_table.{B00,B10,O01,O11}.entity_average_precision",
            "bf16/aggregate-results.json target_year_table.{B00,B10,O01,O11}.flow_average_precision",
            "bf16/complete-alert-budget-curves.npz {B00,B10,O01,O11}__{realized_fpr,detection_rate}",
        ),
        caption=(
            "图3-6　因果前缀跨流聚合（A）与实体级幂平均池化（B）的 2×2 消融（LSPR23 训练、LSPR24 评价，"
            "单种子 seed42，三个面板依次为实体平均精确率、逐流平均精确率与实际假阳率 2% 预算下的检出率）。"
            "以实体平均精确率计，A 单开 +0.0829、B 单开 +0.0994，两者之和 +0.1823，双机制并用 +0.2209，"
            "交互项 +0.0385。两个单机制对基线均为正贡献，并用格在目标年四格中最高；交互项只作描述性读数。"
            "逐流平均精确率的次序与实体级两个口径相反，此处如实并列，不作取舍"
        ),
    ),
    FigureSpec(
        stem="图3-7-训练稳定性",
        width_mm=140,
        height_mm=90,
        draw=draw_training_stability,
        data_keys=(
            "bf16/selection_frozen.json cells.{B00,B10,O01,O11}.history[].epoch",
            "bf16/selection_frozen.json cells.{B00,B10,O01,O11}.history[].validation_flow_ap",
            "bf16/selection_frozen.json cells.{B00,B10,O01,O11}.selected_epoch",
        ),
        caption=(
            "图3-7　四格在 LSPR23 源年验证集上的逐轮表现与选中轮次（20 轮跑满不早停，单种子 seed42，"
            "选择准则为验证逐流平均精确率最早最大，实心大标记为选中轮）。无机制基线、仅因果前缀聚合与"
            "仅实体级幂平均池化三格二十轮取值的极差分别为 0.0056、0.0075 与 0.0077，双机制并用格为 0.1158，"
            "约为前三者的 15 至 21 倍；该格在第 7、12 两轮跌到 0.89 以下，选轮结果对轮次高度敏感"
        ),
    ),
    FigureSpec(
        stem="图3-8-Lp指数收敛轨迹",
        width_mm=130,
        height_mm=85,
        draw=draw_pooling_exponent,
        data_keys=(
            "bf16/selection_frozen.json cells.{O01,O11}.history[].p",
            "bf16/aggregate-results.json target_year_table.{O01,O11}.p",
        ),
        caption=(
            "图3-8　实体级幂平均池化指数 p 的逐轮轨迹（单种子 seed42，横轴为训练轮次）。两格都由初值 "
            "p = 2 单调下行：仅实体级幂平均池化格在选中的第 14 轮取 p = 0.8759，双机制并用格在选中的第 5 轮取 "
            "p = 1.6777，两者都落在 p = 1（算术平均）与 p 趋于正无穷（取最大）之间。无机制基线与仅因果前缀聚合"
            "两格未启用池化，p 恒为初值 2 且不参与训练"
        ),
    ),
    FigureSpec(
        stem="图3-9-实体流数分桶敏感性",
        width_mm=150,
        height_mm=90,
        draw=draw_length_buckets,
        data_keys=(
            "bf16/aggregate-results.json target_year_table.{B00,B10,O01,O11}.length_buckets[].bucket",
            "bf16/aggregate-results.json target_year_table.{B00,B10,O01,O11}.length_buckets[].entity_average_precision",
            "bf16/aggregate-results.json target_year_table.{B00,B10,O01,O11}.length_buckets[].positive_entities",
        ),
        caption=(
            "图3-9　按实体内流数分桶的四格检测能力（LSPR24 评价，单种子 seed42，五个桶的实体与正实体数对四格相同）。"
            "双机制并用格在 3～10 与 11～100 两桶上取得四格最高值；101～1000 与 1001 条流以上两桶的正实体分别只有 "
            "84 与 40 个，桶内取值不支持排序结论"
        ),
    ),
    FigureSpec(
        stem="图3-11-受限观测下的检测能力",
        width_mm=140,
        height_mm=90,
        draw=draw_first_alert,
        data_keys=(
            "bf16/complete-alert-budget-curves.npz O11__first_alert__fpr_*__exposure_index",
            "bf16/complete-alert-budget-curves.npz O11__first_alert__fpr_*__on_time_detection_rate",
            "bf16/aggregate-results.json target_year_table.O11.first_alert.*.realized_first_alert_fpr",
        ),
        caption=(
            "图3-11　本章完整方法在受限观测下的首次告警及时检出（LSPR24 评价，横轴为实体内已观测到的流数，"
            "对数刻度，分母固定为 752 个正实体）。四条阶梯对应四档可用的告警预算；在实际首次告警假阳率 2.18% 一档，"
            "只看每个实体的第一条流即可及时检出 61.84% 的正实体，前 10 条流内升到 72.07%，"
            "读完全部流为 75.27%——增量主要落在前两条流上。"
            "名义 4% 与 8% 两档的首次告警阈值落进并列块，实际首次告警假阳率达 79.05%，预算不成立，未画入"
        ),
    ),
    FigureSpec(
        stem="图3-12-检出率随告警预算的变化",
        width_mm=150,
        height_mm=95,
        draw=draw_budget_curves,
        data_keys=(
            "bf16/complete-alert-budget-curves.npz O11__{realized_fpr,detection_rate}",
            "published-neural/complete-alert-budget-curves.npz {transformer,cnn,gru}__{actual_fpr,detection_rate}",
            "ch3-metrics-table-20260825b/lspr24-evaluation.json[].dr_fpr_*（六档自校基准）",
        ),
        caption=(
            "图3-12　检出率随告警预算的变化（LSPR23 训练、LSPR24 评价，46,363 个负实体与 752 个正实体，"
            "横轴为实体级实际假阳率，对数刻度；空心标记为名义 0.1%、0.5%、1%、2%、4%、8% 六档预算上的实际可达工作点）。"
            "在本章方法可达区间内的 1,721 个共同预算点上，本章方法的检出率全部高于发表配置的全注意力网络，"
            "二者在该区间内不相交；与一维卷积网络只在实际假阳率 0.0539% 处相交一次，交点之后本章方法在 98.84% 的点上更高。"
            "本章方法的完整曲线在实际假阳率 3.72% 之后落进一个并列块，下一个可达点即为全告警，"
            "故名义 4% 与 8% 两档取同一工作点"
        ),
    ),
)


def save_figure(spec: FigureSpec, fig: Figure) -> dict[str, str]:
    outputs: dict[str, str] = {}
    for suffix in ("svg", "pdf", "png"):
        path = ROOT / f"{spec.stem}.{suffix}"
        kwargs: dict[str, Any] = {
            "format": suffix,
            "facecolor": "white",
            "edgecolor": "none",
            "bbox_inches": None,
            "pad_inches": 0,
        }
        if suffix == "png":
            kwargs["dpi"] = fs.PNG_DPI
        else:
            kwargs["metadata"] = {"Title": spec.stem, "Creator": "Matplotlib"}
        fig.savefig(path, **kwargs)
        outputs[suffix] = path.name
    plt.close(fig)
    return outputs


def measure(stem: str, outputs: dict[str, str], width_mm: float, height_mm: float) -> dict[str, Any]:
    """核对三种格式可解析，回报 PNG 实测像素与实测 ppi，低于 300 直接报错。"""

    from xml.etree import ElementTree

    from PIL import Image

    ElementTree.parse(ROOT / outputs["svg"])
    if not (ROOT / outputs["pdf"]).read_bytes().startswith(b"%PDF"):
        raise ValueError(f"PDF 文件头无效：{stem}")
    with Image.open(ROOT / outputs["png"]) as image:
        image.verify()
    with Image.open(ROOT / outputs["png"]) as image:
        px_w, px_h = image.size
    ppi_w = px_w / (width_mm / 25.4)
    ppi_h = px_h / (height_mm / 25.4)
    if min(ppi_w, ppi_h) < 300.0 - 1e-6:
        raise ValueError(f"{stem} 实测 {ppi_w:.1f} ppi 低于合同下限 300 ppi")
    return {"png_pixels": [px_w, px_h], "png_ppi_measured": [round(ppi_w, 1), round(ppi_h, 1)]}


# 图 3-1 至图 3-4 由机制图脚本产出，本脚本不重绘，只在清单中沿用并补全题注行。
MECHANISM_CAPTIONS: dict[str, str] = {
    "图3-1-整体方法框架": (
        "图3-1　本章方法的整体框架：逐流特征经因果前缀跨流聚合进入表示层，"
        "实体级幂平均池化在决策层把同一实体的逐流分数汇成实体分数；"
        "表示层机制与决策层机制分别以斜线、反斜线填充标出"
    ),
    "图3-2-二IP无向对序列构造": (
        "图3-2　二 IP 无向对序列构造：双向流经无向对键归并到同一实体，"
        "键内按时间升序后切成长度 L 的非重叠块，尾块补零并以掩码标记"
    ),
    "图3-3-因果前缀跨流聚合": (
        "图3-3　因果前缀跨流聚合：下三角因果掩码与非因果整窗聚合的对照，"
        "以及前缀聚合的常数代价增量更新"
    ),
    "图3-4-实体级可学Lp池化": (
        "图3-4　实体级可学幂平均池化：广义幂平均关于池化指数的单调曲线，"
        "标出几何平均、算术平均与上界三个特例"
    ),
}

WITHDRAWN: tuple[dict[str, Any], ...] = (
    {
        "stem": "图3-10-攻击类别分面",
        "withdrawn_at": "2026-08-26",
        "reason": (
            "旧图取自已作废的 runs/diagnostics/ch3-full 运行；当前权威制品"
            "（正式 CPA×ELP 四格 BF16 运行、统一指标总表、共同首次告警预算包络）"
            "均不含任何按攻击类别的分面字段，无法换底重绘。"
        ),
        "recovery": (
            "若正文保留攻击类别分面，需要新增一次按 Category 字段分面的目标年评价运行；"
            "在此之前正文不应引用图 3-10。"
        ),
        "files_moved_to": "作废/",
    },
)


def build_manifest(entries: list[dict[str, Any]], sources: list[dict[str, Any]]) -> None:
    """重写图件清单：按生成器分段登记环境与字体，逐图登记数据来源键路径。"""

    import PIL

    previous: dict[str, Any] = {}
    if MANIFEST_PATH.exists():
        previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    prior = {item.get("stem"): item for item in previous.get("figures", [])}

    mechanism_entries: list[dict[str, Any]] = []
    for stem, caption in MECHANISM_CAPTIONS.items():
        old = prior.get(stem)
        if old is None:
            raise KeyError(f"图件清单缺少机制图条目：{stem}")
        outputs = old["outputs"]
        if not all((ROOT / name).exists() for name in outputs.values()):
            raise FileNotFoundError(f"机制图输出缺失：{stem}")
        entry = {
            "stem": stem,
            "generator": MECHANISM_GENERATOR,
            "caption": caption,
            "width_mm": old["width_mm"],
            "height_mm": old["height_mm"],
            "png_dpi": old["png_dpi"],
            "evidence_mode": "method_schematic_without_experimental_results",
            "data_source": "不承载实验数据",
            "data_keys": [],
            "outputs": outputs,
        }
        entry.update(measure(stem, outputs, float(old["width_mm"]), float(old["height_mm"])))
        mechanism_entries.append(entry)

    typography = {
        "cjk_font_requested": fs.CJK_FONT.requested,
        "cjk_font_used": fs.CJK_FONT.family,
        "cjk_font_path": fs.CJK_FONT.path,
        "cjk_face_index": fs.CJK_FONT.face_index,
        "latin_font_used": fs.LATIN_FONT.family,
        "latin_font_path": fs.LATIN_FONT.path,
        "math_font_used": None if fs.MATH_FONT is None else fs.MATH_FONT.family,
        "min_font_pt": fs.MIN_FONT_PT,
        "main_font_pt": fs.MAIN_FONT_PT,
        "main_line_pt": fs.MAIN_LINE_PT,
        "aux_line_pt": fs.AUX_LINE_PT,
    }
    environment = {
        "python": ".".join(str(v) for v in sys.version_info[:3]),
        "matplotlib": __import__("matplotlib").__version__,
        "numpy": np.__version__,
        "pillow": PIL.__version__,
    }

    manifest = {
        "contract": "AGENTS.md 学位论文图件合同（2026-08-13 重定）；thesis/figures/AGENTS.md",
        "updated_at": "2026-08-26",
        "grayscale_readable": True,
        "generators": [
            {
                "script": MECHANISM_GENERATOR,
                "evidence_mode": "method_schematic_without_experimental_results",
                "figures": sorted(MECHANISM_CAPTIONS),
                "typography": typography,
                "environment": environment,
                "note": (
                    "两个生成脚本共用 figstyle.py 的字体解析，故字体登记相同；"
                    "本条的尺寸与分辨率由本轮 PIL 实测复核，题注行在本轮补全。"
                ),
            },
            {
                "script": GENERATOR,
                "evidence_mode": "frozen_experiment_artifacts",
                "figures": sorted(entry["stem"] for entry in entries),
                "typography": typography,
                "environment": environment,
                "data_sources": sources,
                "readout_rule": (
                    "检出率一律在完整可达告警预算曲线上取实际假阳率不超过名义预算的最后一个点；"
                    "制品中 dr_at_fpr 的名义秩位键不使用。该规则已对四个方法、六档预算与"
                    "统一指标总表逐位自校一致。"
                ),
            },
        ],
        "withdrawn": list(WITHDRAWN),
        "figures": sorted(
            mechanism_entries + entries,
            key=lambda item: int(str(item["stem"]).split("-")[1]),
        ),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    registry = rd.Registry()
    for line in rd.verify_against_metrics_table(registry):
        logger.info("自校　%s", line)

    cells, meta = rd.load_ablation(registry)
    ctx: dict[str, Any] = {
        "methods": rd.load_metrics_table(registry),
        "cells": cells,
        "meta": meta,
        "effects": rd.ablation_effects(cells),
        "first_alert": rd.load_first_alert(registry),
        "budget_curves": rd.load_budget_curves(registry),
    }

    entries: list[dict[str, Any]] = []
    for spec in SPECS:
        outputs = save_figure(spec, spec.draw(ctx))
        entry: dict[str, Any] = {
            "stem": spec.stem,
            "generator": GENERATOR,
            "caption": spec.caption,
            "width_mm": spec.width_mm,
            "height_mm": spec.height_mm,
            "png_dpi": fs.PNG_DPI,
            "evidence_mode": "frozen_experiment_artifacts",
            "data_source": meta["run_id"],
            "data_keys": list(spec.data_keys),
            "outputs": outputs,
        }
        entry.update(measure(spec.stem, outputs, spec.width_mm, spec.height_mm))
        entries.append(entry)
        logger.info(
            "已生成 %s：%g×%g mm，PNG %d×%d px，实测 %.1f ppi",
            spec.stem,
            spec.width_mm,
            spec.height_mm,
            entry["png_pixels"][0],
            entry["png_pixels"][1],
            entry["png_ppi_measured"][0],
        )

    build_manifest(entries, registry.dump())
    logger.info("图件清单已重写：%s", MANIFEST_PATH)
    logger.info(
        "字体　中文 %s（%s#%d）／西文 %s",
        fs.CJK_FONT.family,
        fs.CJK_FONT.path,
        fs.CJK_FONT.face_index,
        fs.LATIN_FONT.family,
    )


if __name__ == "__main__":
    main()
