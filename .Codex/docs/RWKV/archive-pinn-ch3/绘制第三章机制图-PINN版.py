"""生成第三章五张方法机制图。

输出同名 SVG、PDF 和 PNG，不读取任何实验结果。
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

MPL_CACHE = Path("/tmp/chapter3-matplotlib-cache")
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.figure import Figure
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parent

FONT_CANDIDATES = (
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
)


def register_font() -> tuple[str, Path]:
    """显式注册中文字体，避免依赖全局 Fontconfig 缓存。"""

    for path in FONT_CANDIDATES:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            return font_manager.FontProperties(fname=str(path)).get_name(), path
    raise FileNotFoundError("未找到可用的中文字体")


FONT_NAME, FONT_PATH = register_font()

plt.rcParams.update(
    {
        "font.family": FONT_NAME,
        "font.sans-serif": [FONT_NAME],
        "axes.unicode_minus": False,
        "mathtext.fontset": "stix",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.transparent": False,
    }
)


INK = "#24313A"
MUTED = "#65737D"
LIGHT_LINE = "#C8D0D5"
BLUE = "#2F6B9A"
BLUE_LIGHT = "#EAF3FA"
TEAL = "#14866D"
TEAL_LIGHT = "#E7F5F1"
VERMILION = "#C84B31"
VERMILION_LIGHT = "#FBEDEA"
GOLD = "#A66F00"
GOLD_LIGHT = "#FFF4D6"
GRAY = "#7D878E"
GRAY_LIGHT = "#F1F3F4"
WHITE = "#FFFFFF"


@dataclass(frozen=True)
class FigureSpec:
    stem: str
    width_mm: float
    height_mm: float
    draw: Callable[[], Figure]


def mm_to_inch(value: float) -> float:
    return value / 25.4


def canvas(width_mm: float, height_mm: float) -> tuple[Figure, plt.Axes]:
    fig = plt.figure(figsize=(mm_to_inch(width_mm), mm_to_inch(height_mm)), dpi=150)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return fig, ax


def text(
    ax: plt.Axes,
    x: float,
    y: float,
    value: str,
    *,
    size: float = 8.0,
    color: str = INK,
    weight: str = "normal",
    ha: str = "center",
    va: str = "center",
    linespacing: float = 1.2,
    rotation: float = 0,
    zorder: int = 10,
) -> None:
    prop = font_manager.FontProperties(fname=str(FONT_PATH), size=size, weight=weight)
    ax.text(
        x,
        y,
        value,
        color=color,
        fontproperties=prop,
        ha=ha,
        va=va,
        linespacing=linespacing,
        rotation=rotation,
        zorder=zorder,
    )


def rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    *,
    subtitle: str | None = None,
    face: str = WHITE,
    edge: str = INK,
    title_color: str = INK,
    subtitle_color: str = MUTED,
    linewidth: float = 1.0,
    linestyle: str | tuple = "-",
    title_size: float = 7.7,
    subtitle_size: float = 6.2,
    radius: float = 0.012,
    zorder: int = 3,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=f"round,pad=0.006,rounding_size={radius}",
        linewidth=linewidth,
        linestyle=linestyle,
        edgecolor=edge,
        facecolor=face,
        zorder=zorder,
    )
    ax.add_patch(patch)
    if subtitle is None:
        text(
            ax,
            x + width / 2,
            y + height / 2,
            title,
            size=title_size,
            color=title_color,
            weight="bold",
        )
    else:
        text(
            ax,
            x + width / 2,
            y + height * 0.64,
            title,
            size=title_size,
            color=title_color,
            weight="bold",
        )
        text(
            ax,
            x + width / 2,
            y + height * 0.30,
            subtitle,
            size=subtitle_size,
            color=subtitle_color,
        )
    return patch


def pill(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    *,
    face: str,
    edge: str,
    color: str = INK,
    size: float = 6.5,
    weight: str = "bold",
) -> None:
    rounded_box(
        ax,
        x,
        y,
        width,
        height,
        label,
        face=face,
        edge=edge,
        title_color=color,
        title_size=size,
        linewidth=0.9,
        radius=height / 2,
    )


def arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = INK,
    linewidth: float = 1.15,
    linestyle: str | tuple = "-",
    mutation_scale: float = 9,
    connectionstyle: str = "arc3,rad=0",
    zorder: int = 5,
) -> FancyArrowPatch:
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=mutation_scale,
        linewidth=linewidth,
        linestyle=linestyle,
        color=color,
        connectionstyle=connectionstyle,
        shrinkA=1.5,
        shrinkB=1.5,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def line(
    ax: plt.Axes,
    xs: list[float],
    ys: list[float],
    *,
    color: str = INK,
    linewidth: float = 1.0,
    linestyle: str | tuple = "-",
    zorder: int = 4,
) -> None:
    ax.plot(
        xs, ys, color=color, linewidth=linewidth, linestyle=linestyle, zorder=zorder
    )


def panel(
    ax: plt.Axes,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    *,
    face: str = WHITE,
    edge: str = LIGHT_LINE,
    label_width: float = 0.115,
) -> None:
    rounded_box(
        ax, x, y, width, height, "", face=face, edge=edge, linewidth=0.9, radius=0.014
    )
    pill(
        ax,
        x + 0.012,
        y + height - 0.055,
        label_width,
        0.038,
        label,
        face=GRAY_LIGHT,
        edge=GRAY,
        size=6.2,
    )


def legend_item(
    ax: plt.Axes,
    x: float,
    y: float,
    label: str,
    *,
    color: str,
    linestyle: str | tuple = "-",
    width: float = 0.045,
) -> None:
    arrow(
        ax,
        (x, y),
        (x + width, y),
        color=color,
        linewidth=1.1,
        linestyle=linestyle,
        mutation_scale=7,
    )
    text(ax, x + width + 0.008, y, label, size=5.8, color=MUTED, ha="left")


def save_figure(spec: FigureSpec, fig: Figure) -> dict[str, object]:
    outputs: dict[str, str] = {}
    for suffix in ("svg", "pdf", "png"):
        path = ROOT / f"{spec.stem}.{suffix}"
        kwargs: dict[str, object] = {
            "format": suffix,
            "facecolor": WHITE,
            "edgecolor": "none",
            "bbox_inches": None,
            "pad_inches": 0,
        }
        if suffix == "png":
            kwargs["dpi"] = 300
        else:
            kwargs["metadata"] = {"Title": spec.stem, "Creator": "Matplotlib"}
        fig.savefig(path, **kwargs)
        outputs[suffix] = path.name
    plt.close(fig)
    return {
        "stem": spec.stem,
        "width_mm": spec.width_mm,
        "height_mm": spec.height_mm,
        "outputs": outputs,
    }


def draw_overall_framework() -> Figure:
    fig, ax = canvas(180, 108)

    text(
        ax,
        0.018,
        0.905,
        "公共前向与生成任务",
        size=6.7,
        color=BLUE,
        weight="bold",
        ha="left",
    )
    text(
        ax,
        0.018,
        0.255,
        "训练期物理监督",
        size=6.7,
        color=GOLD,
        weight="bold",
        ha="left",
    )

    rounded_box(
        ax,
        0.02,
        0.62,
        0.135,
        0.20,
        "GeNIS",
        subtitle="四窗口公共流量 $x_i$\n分层生成标签 $y_i$",
        face=BLUE_LIGHT,
        edge=BLUE,
        title_color=BLUE,
    )
    rounded_box(
        ax,
        0.02,
        0.06,
        0.165,
        0.15,
        "ns-3 受控序列",
        subtitle="$x_i$ + 双锚点 + 通量/$C_{i,k}$",
        face=GOLD_LIGHT,
        edge=GOLD,
        title_color=GOLD,
    )

    rounded_box(
        ax,
        0.205,
        0.60,
        0.145,
        0.21,
        "Qwen 第 1–13 层",
        subtitle="冻结基座 + S3 适配\n提示末端 $h^{(13)}$",
        face=GRAY_LIGHT,
        edge=GRAY,
        title_color=INK,
    )
    pill(
        ax,
        0.228,
        0.765,
        0.10,
        0.032,
        "冻结",
        face=WHITE,
        edge=GRAY,
        color=GRAY,
        size=5.7,
    )

    rounded_box(
        ax,
        0.395,
        0.70,
        0.125,
        0.14,
        "五维状态头",
        subtitle=r"$\hat q_0,\ldots,\hat q_4$",
        face=TEAL_LIGHT,
        edge=TEAL,
        title_color=TEAL,
    )
    rounded_box(
        ax,
        0.565,
        0.70,
        0.155,
        0.14,
        "九个物理条件词元",
        subtitle="5 状态 + 4 相邻增量\n共享编码器 $Z_i$",
        face=TEAL_LIGHT,
        edge=TEAL,
        title_color=TEAL,
    )

    rounded_box(
        ax,
        0.395,
        0.47,
        0.125,
        0.13,
        "Qwen 第 14–23 层",
        subtitle="冻结前向",
        face=GRAY_LIGHT,
        edge=GRAY,
    )
    rounded_box(
        ax,
        0.565,
        0.45,
        0.155,
        0.17,
        "第 24–27 层",
        subtitle="4 头交叉注意力\n零门 + 单层 0.1 上界",
        face=VERMILION_LIGHT,
        edge=VERMILION,
        title_color=VERMILION,
    )
    rounded_box(
        ax,
        0.765,
        0.47,
        0.115,
        0.13,
        "第 28 层 + LM 头",
        subtitle="冻结前向",
        face=GRAY_LIGHT,
        edge=GRAY,
        title_size=6.8,
    )
    rounded_box(
        ax,
        0.915,
        0.47,
        0.07,
        0.13,
        "结构化\n输出",
        face=BLUE_LIGHT,
        edge=BLUE,
        title_color=BLUE,
        title_size=6.7,
    )

    arrow(ax, (0.155, 0.715), (0.205, 0.705), color=BLUE, linewidth=1.5)
    arrow(ax, (0.35, 0.675), (0.395, 0.535), color=BLUE, linewidth=1.5)
    arrow(ax, (0.52, 0.535), (0.565, 0.535), color=BLUE, linewidth=1.5)
    arrow(ax, (0.72, 0.535), (0.765, 0.535), color=BLUE, linewidth=1.5)
    arrow(ax, (0.88, 0.535), (0.915, 0.535), color=BLUE, linewidth=1.5)

    arrow(ax, (0.35, 0.72), (0.395, 0.77), color=TEAL, linewidth=1.5)
    arrow(ax, (0.52, 0.77), (0.565, 0.77), color=TEAL, linewidth=1.5)
    arrow(ax, (0.645, 0.70), (0.645, 0.62), color=TEAL, linewidth=1.5)

    rounded_box(
        ax,
        0.235,
        0.26,
        0.12,
        0.105,
        r"$\mathcal{L}_{\mathrm{state}}$",
        subtitle="双锚点均方误差",
        face=GOLD_LIGHT,
        edge=GOLD,
        title_color=GOLD,
    )
    rounded_box(
        ax,
        0.405,
        0.26,
        0.12,
        0.105,
        r"$\mathcal{L}_{\mathrm{phy}}$",
        subtitle="四段控制体残差",
        face=GOLD_LIGHT,
        edge=GOLD,
        title_color=GOLD,
    )
    rounded_box(
        ax,
        0.77,
        0.26,
        0.11,
        0.105,
        r"$\mathcal{L}_{\mathrm{gen}}$",
        subtitle="生成词元损失",
        face=VERMILION_LIGHT,
        edge=VERMILION,
        title_color=VERMILION,
    )

    arrow(ax, (0.185, 0.135), (0.235, 0.31), color=GOLD, linestyle=(0, (4, 2)))
    arrow(ax, (0.185, 0.12), (0.405, 0.31), color=GOLD, linestyle=(0, (4, 2)))
    arrow(ax, (0.295, 0.365), (0.435, 0.70), color=GOLD, linestyle=(0, (4, 2)))
    arrow(ax, (0.465, 0.365), (0.475, 0.70), color=TEAL, linestyle=(0, (4, 2)))
    arrow(ax, (0.95, 0.47), (0.85, 0.365), color=VERMILION, linestyle=(0, (4, 2)))
    arrow(
        ax,
        (0.77, 0.31),
        (0.68, 0.45),
        color=VERMILION,
        linestyle=(0, (4, 2)),
        connectionstyle="arc3,rad=-0.1",
    )
    arrow(
        ax,
        (0.77, 0.30),
        (0.50, 0.70),
        color=VERMILION,
        linestyle=(0, (4, 2)),
        connectionstyle="arc3,rad=-0.17",
    )

    text(
        ax,
        0.205,
        0.232,
        "特权真值只进入损失，不进入部署前向",
        size=5.8,
        color=GOLD,
        ha="left",
    )
    legend_item(ax, 0.025, 0.03, "前向路径", color=BLUE)
    legend_item(ax, 0.205, 0.03, "物理状态前向", color=TEAL)
    legend_item(ax, 0.425, 0.03, "生成梯度", color=VERMILION, linestyle=(0, (4, 2)))
    legend_item(ax, 0.60, 0.03, "状态/物理监督", color=GOLD, linestyle=(0, (4, 2)))
    pill(
        ax,
        0.84,
        0.01,
        0.135,
        0.036,
        "冻结参数不更新",
        face=GRAY_LIGHT,
        edge=GRAY,
        color=GRAY,
        size=5.7,
    )

    return fig


def draw_queue_icon(ax: plt.Axes, x: float, y: float, label: str) -> None:
    ax.add_patch(
        Rectangle(
            (x - 0.027, y - 0.055),
            0.054,
            0.11,
            facecolor=WHITE,
            edgecolor=TEAL,
            linewidth=1.0,
            zorder=4,
        )
    )
    for offset in (-0.0275, 0, 0.0275):
        line(
            ax,
            [x - 0.027, x + 0.027],
            [y + offset, y + offset],
            color=LIGHT_LINE,
            linewidth=0.55,
            zorder=5,
        )
    ax.add_patch(
        Rectangle(
            (x - 0.023, y - 0.050),
            0.046,
            0.018,
            facecolor=TEAL_LIGHT,
            edgecolor="none",
            zorder=4,
        )
    )
    text(ax, x, y - 0.077, label, size=6.2, color=TEAL, weight="bold")


def draw_four_window_queue() -> Figure:
    fig, ax = canvas(180, 90)
    xs = [0.08, 0.29, 0.50, 0.71, 0.92]
    window_faces = [BLUE_LIGHT, TEAL_LIGHT, BLUE_LIGHT, TEAL_LIGHT]

    text(
        ax,
        0.025,
        0.93,
        "四个连续时间窗",
        size=7.0,
        color=BLUE,
        weight="bold",
        ha="left",
    )
    text(
        ax,
        0.975,
        0.93,
        "五个边界队列锚点",
        size=7.0,
        color=TEAL,
        weight="bold",
        ha="right",
    )

    for index in range(4):
        left = xs[index]
        right = xs[index + 1]
        ax.add_patch(
            FancyBboxPatch(
                (left + 0.01, 0.31),
                right - left - 0.02,
                0.50,
                boxstyle="round,pad=0.004,rounding_size=0.01",
                facecolor=window_faces[index],
                edgecolor=LIGHT_LINE,
                linewidth=0.75,
                zorder=1,
            )
        )
        text(
            ax,
            (left + right) / 2,
            0.78,
            f"$\\mathcal{{W}}_{index}$",
            size=7.2,
            color=BLUE,
            weight="bold",
        )
        arrow(
            ax,
            ((left + right) / 2 - 0.055, 0.68),
            ((left + right) / 2 - 0.055, 0.60),
            color=BLUE,
            linewidth=1.0,
        )
        text(
            ax, (left + right) / 2 - 0.055, 0.715, f"$A_{index}$", size=6.2, color=BLUE
        )
        arrow(
            ax,
            ((left + right) / 2 + 0.01, 0.56),
            ((left + right) / 2 + 0.075, 0.56),
            color=TEAL,
            linewidth=1.0,
        )
        text(
            ax, (left + right) / 2 + 0.045, 0.605, f"$O_{index}$", size=6.2, color=TEAL
        )
        arrow(
            ax,
            ((left + right) / 2 - 0.02, 0.57),
            ((left + right) / 2 - 0.075, 0.50),
            color=GOLD,
            linewidth=0.9,
            linestyle=(0, (3, 2)),
        )
        text(
            ax,
            (left + right) / 2 - 0.065,
            0.465,
            f"$L^-_{index}$",
            size=6.0,
            color=GOLD,
        )
        rounded_box(
            ax,
            left + 0.03,
            0.345,
            right - left - 0.06,
            0.065,
            f"$C_{index}$  容量字节预算",
            face=WHITE,
            edge=BLUE,
            title_color=BLUE,
            title_size=5.8,
            linewidth=0.7,
        )

    line(ax, [xs[0], xs[-1]], [0.86, 0.86], color=INK, linewidth=1.0)
    for index, x in enumerate(xs):
        ax.add_patch(
            Circle(
                (x, 0.86),
                0.011,
                facecolor=TEAL,
                edgecolor=WHITE,
                linewidth=0.7,
                zorder=7,
            )
        )
        text(ax, x, 0.895, f"$t_{index}$", size=5.8, color=MUTED)
        draw_queue_icon(ax, x, 0.56, f"$q_{index}=Q_{index}/S$")

    rounded_box(
        ax,
        0.07,
        0.10,
        0.42,
        0.12,
        r"$S=\max_k C_k$",
        subtitle="同一序列共享字节尺度，锚点状态无量纲",
        face=GRAY_LIGHT,
        edge=GRAY,
        title_color=INK,
    )
    rounded_box(
        ax,
        0.53,
        0.10,
        0.40,
        0.12,
        "$Q_{k+1}-Q_k=A_k-O_k-L^-_k$",
        subtitle="当前正式矩阵 $L^+=0$；每个窗口独立记账",
        face=GOLD_LIGHT,
        edge=GOLD,
        title_color=GOLD,
        title_size=7.0,
    )
    text(
        ax,
        0.5,
        0.035,
        "图标只表示窗口、边界和事件口径，不表示实验队列数值或轨迹。",
        size=5.7,
        color=MUTED,
    )
    return fig


def draw_dual_anchor_conservation() -> Figure:
    fig, ax = canvas(180, 95)
    panel(
        ax,
        0.025,
        0.08,
        0.455,
        0.84,
        "(a) 只有差分约束",
        face="#FAFBFC",
        label_width=0.15,
    )
    panel(
        ax,
        0.52,
        0.08,
        0.455,
        0.84,
        "(b) 双锚点 + 分段守恒",
        face="#FAFBFC",
        label_width=0.19,
    )

    left_xs = [0.07, 0.16, 0.25, 0.34, 0.43]
    base = [0.33, 0.42, 0.38, 0.54, 0.50]
    trajectories = [
        ([value + 0.16 for value in base], BLUE, r"$\hat q+c_2$"),
        (base, TEAL, r"$\hat q$"),
        ([value - 0.14 for value in base], GRAY, r"$\hat q+c_1$"),
    ]
    for values, color, label in trajectories:
        line(ax, left_xs, values, color=color, linewidth=1.35)
        for x, y in zip(left_xs, values, strict=True):
            ax.add_patch(
                Circle(
                    (x, y),
                    0.0085,
                    facecolor=WHITE,
                    edgecolor=color,
                    linewidth=1.0,
                    zorder=6,
                )
            )
        text(ax, 0.445, values[-1], label, size=5.9, color=color, ha="left")

    for index, x in enumerate(left_xs):
        text(ax, x, 0.205, f"$t_{index}$", size=5.6, color=MUTED)
    arrow(ax, (0.095, 0.34), (0.095, 0.49), color=GRAY, linewidth=0.9, mutation_scale=7)
    text(ax, 0.11, 0.415, "平移 $c$", size=5.7, color=GRAY, ha="left")
    rounded_box(
        ax,
        0.09,
        0.70,
        0.33,
        0.105,
        r"$r_k(\hat q+c)=r_k(\hat q)$",
        subtitle="轨迹绝对位置不可由差分残差单独确定",
        face=GRAY_LIGHT,
        edge=GRAY,
        title_color=INK,
    )
    text(ax, 0.252, 0.135, "相同相邻差分 → 相同四段残差", size=6.1, color=MUTED)

    right_xs = [0.565, 0.66, 0.755, 0.85, 0.945]
    right_ys = [0.34, 0.42, 0.39, 0.57, 0.52]
    line(ax, right_xs, right_ys, color=TEAL, linewidth=1.5)
    for index, (x, y) in enumerate(zip(right_xs, right_ys, strict=True)):
        is_anchor = index in {0, 3}
        face = GOLD if is_anchor else WHITE
        edge = GOLD if is_anchor else TEAL
        ax.add_patch(
            Circle(
                (x, y), 0.012, facecolor=face, edgecolor=edge, linewidth=1.2, zorder=7
            )
        )
        text(
            ax,
            x,
            y + 0.055,
            f"$q_{index}$",
            size=6.0,
            color=edge,
            weight="bold" if is_anchor else "normal",
        )
        text(ax, x, 0.205, f"$t_{index}$", size=5.6, color=MUTED)

    pill(
        ax,
        0.535,
        0.72,
        0.12,
        0.046,
        "初始锚点 $q_0$",
        face=GOLD_LIGHT,
        edge=GOLD,
        color=GOLD,
        size=5.8,
    )
    pill(
        ax,
        0.815,
        0.72,
        0.14,
        0.046,
        "内部锚点 $q_a$",
        face=GOLD_LIGHT,
        edge=GOLD,
        color=GOLD,
        size=5.8,
    )
    arrow(
        ax,
        (0.595, 0.72),
        (0.565, 0.365),
        color=GOLD,
        linewidth=0.9,
        linestyle=(0, (3, 2)),
    )
    arrow(
        ax,
        (0.885, 0.72),
        (0.85, 0.595),
        color=GOLD,
        linewidth=0.9,
        linestyle=(0, (3, 2)),
    )

    for index in range(4):
        midpoint = (right_xs[index] + right_xs[index + 1]) / 2
        pill(
            ax,
            midpoint - 0.025,
            0.27,
            0.05,
            0.04,
            f"$r_{index}$",
            face=TEAL_LIGHT if index < 3 else BLUE_LIGHT,
            edge=TEAL if index < 3 else BLUE,
            color=TEAL if index < 3 else BLUE,
            size=5.8,
        )

    line(ax, [0.565, 0.85], [0.14, 0.14], color=TEAL, linewidth=1.0)
    line(ax, [0.565, 0.565], [0.13, 0.15], color=TEAL, linewidth=1.0)
    line(ax, [0.85, 0.85], [0.13, 0.15], color=TEAL, linewidth=1.0)
    text(ax, 0.7075, 0.11, "前段累计漂移受 $q_0,q_a$ 限制", size=5.5, color=TEAL)
    line(ax, [0.85, 0.945], [0.14, 0.14], color=BLUE, linewidth=1.0)
    line(ax, [0.945, 0.945], [0.13, 0.15], color=BLUE, linewidth=1.0)
    text(ax, 0.8975, 0.11, "后段", size=5.5, color=BLUE)

    rounded_box(
        ax,
        0.57,
        0.785,
        0.37,
        0.065,
        r"$\mathcal{L}_{\mathrm{state}}(q_0,q_a)+\lambda_p\,\mathrm{mean}_k\,r_k^2$",
        face=TEAL_LIGHT,
        edge=TEAL,
        title_color=TEAL,
        title_size=6.3,
    )
    text(
        ax,
        0.75,
        0.045,
        "图中以 $a=3$ 说明机制；实际内部锚点由 seed 与 group_id 固定分配。",
        size=5.6,
        color=MUTED,
    )
    return fig


def draw_bounded_cross_attention() -> Figure:
    fig, ax = canvas(180, 100)

    panel(ax, 0.02, 0.11, 0.21, 0.80, "物理条件", face="#FAFBFC")
    panel(ax, 0.255, 0.11, 0.16, 0.80, "共享编码", face="#FAFBFC")
    panel(ax, 0.44, 0.11, 0.30, 0.80, "单层交叉注意力", face="#FAFBFC")
    panel(ax, 0.765, 0.11, 0.215, 0.80, "有界残差注入", face="#FAFBFC")

    q_xs = [0.035, 0.072, 0.109, 0.146, 0.183]
    for index, x in enumerate(q_xs):
        pill(
            ax,
            x,
            0.69,
            0.032,
            0.07,
            rf"$\hat q_{index}$",
            face=TEAL_LIGHT,
            edge=TEAL,
            color=TEAL,
            size=5.7,
        )
    delta_xs = [0.047, 0.09, 0.133, 0.176]
    for index, x in enumerate(delta_xs):
        pill(
            ax,
            x,
            0.54,
            0.038,
            0.07,
            rf"$\Delta q_{index}$",
            face=BLUE_LIGHT,
            edge=BLUE,
            color=BLUE,
            size=5.4,
        )
    text(ax, 0.125, 0.81, "5 个绝对状态", size=6.2, color=TEAL, weight="bold")
    text(ax, 0.125, 0.655, "4 个有符号增量", size=6.2, color=BLUE, weight="bold")
    rounded_box(
        ax,
        0.05,
        0.27,
        0.15,
        0.13,
        "九个标量 $v_{i,n}$",
        subtitle="无队列真值、无攻击标签",
        face=WHITE,
        edge=TEAL,
        title_color=TEAL,
    )
    arrow(ax, (0.125, 0.54), (0.125, 0.40), color=TEAL, linewidth=1.2)

    rounded_box(
        ax,
        0.28,
        0.61,
        0.11,
        0.17,
        "类型 + 位置嵌入",
        subtitle=r"$e_{\mathrm{type}}$ / $e_n$",
        face=BLUE_LIGHT,
        edge=BLUE,
        title_color=BLUE,
        title_size=6.5,
    )
    rounded_box(
        ax,
        0.28,
        0.37,
        0.11,
        0.15,
        "两层 MLP",
        subtitle="SiLU，跨层共享",
        face=TEAL_LIGHT,
        edge=TEAL,
        title_color=TEAL,
    )
    pill(
        ax,
        0.285,
        0.22,
        0.10,
        0.075,
        r"$Z_i\in\mathbb{R}^{9\times256}$",
        face=WHITE,
        edge=TEAL,
        color=TEAL,
        size=5.9,
    )
    arrow(ax, (0.20, 0.335), (0.28, 0.445), color=TEAL, linewidth=1.2)
    arrow(ax, (0.335, 0.61), (0.335, 0.52), color=BLUE, linewidth=1.0)
    arrow(ax, (0.335, 0.37), (0.335, 0.295), color=TEAL, linewidth=1.0)

    pill(
        ax,
        0.465,
        0.79,
        0.052,
        0.045,
        "$H^{(l)}$",
        face=BLUE_LIGHT,
        edge=BLUE,
        color=BLUE,
        size=6.2,
    )
    pill(
        ax,
        0.535,
        0.79,
        0.052,
        0.045,
        "$W_Q^{(l)}$",
        face=WHITE,
        edge=BLUE,
        color=BLUE,
        size=5.8,
    )
    arrow(ax, (0.517, 0.812), (0.535, 0.812), color=BLUE, mutation_scale=7)
    pill(
        ax,
        0.61,
        0.79,
        0.052,
        0.045,
        "$Q^{(l)}$",
        face=BLUE_LIGHT,
        edge=BLUE,
        color=BLUE,
        size=6.2,
    )
    arrow(ax, (0.587, 0.812), (0.61, 0.812), color=BLUE, mutation_scale=7)

    pill(
        ax,
        0.465,
        0.24,
        0.052,
        0.045,
        "$Z_i$",
        face=TEAL_LIGHT,
        edge=TEAL,
        color=TEAL,
        size=6.2,
    )
    pill(
        ax,
        0.535,
        0.28,
        0.052,
        0.045,
        "$W_K^{(l)}$",
        face=WHITE,
        edge=TEAL,
        color=TEAL,
        size=5.8,
    )
    pill(
        ax,
        0.535,
        0.20,
        0.052,
        0.045,
        "$W_V^{(l)}$",
        face=WHITE,
        edge=TEAL,
        color=TEAL,
        size=5.8,
    )
    arrow(ax, (0.517, 0.262), (0.535, 0.302), color=TEAL, mutation_scale=7)
    arrow(ax, (0.517, 0.262), (0.535, 0.222), color=TEAL, mutation_scale=7)
    pill(
        ax,
        0.61,
        0.28,
        0.052,
        0.045,
        "$K^{(l)}$",
        face=TEAL_LIGHT,
        edge=TEAL,
        color=TEAL,
        size=6.2,
    )
    pill(
        ax,
        0.61,
        0.20,
        0.052,
        0.045,
        "$V^{(l)}$",
        face=TEAL_LIGHT,
        edge=TEAL,
        color=TEAL,
        size=6.2,
    )
    arrow(ax, (0.587, 0.302), (0.61, 0.302), color=TEAL, mutation_scale=7)
    arrow(ax, (0.587, 0.222), (0.61, 0.222), color=TEAL, mutation_scale=7)

    rounded_box(
        ax,
        0.555,
        0.46,
        0.15,
        0.17,
        "4 头缩放点积注意力",
        subtitle="单头维度 64\n查询为生成位置",
        face=VERMILION_LIGHT,
        edge=VERMILION,
        title_color=VERMILION,
        title_size=6.4,
    )
    for head in range(4):
        ax.add_patch(
            Circle(
                (0.578 + head * 0.033, 0.48),
                0.012,
                facecolor=WHITE,
                edgecolor=VERMILION,
                linewidth=0.8,
                zorder=7,
            )
        )
        text(ax, 0.578 + head * 0.033, 0.48, str(head + 1), size=4.7, color=VERMILION)
    arrow(ax, (0.636, 0.79), (0.63, 0.63), color=BLUE, linewidth=1.1)
    arrow(ax, (0.636, 0.325), (0.61, 0.46), color=TEAL, linewidth=1.0)
    arrow(ax, (0.636, 0.245), (0.65, 0.46), color=TEAL, linewidth=1.0)
    pill(
        ax,
        0.605,
        0.675,
        0.06,
        0.045,
        "$W_O^{(l)}$",
        face=WHITE,
        edge=VERMILION,
        color=VERMILION,
        size=5.8,
    )
    arrow(ax, (0.63, 0.63), (0.635, 0.675), color=VERMILION, mutation_scale=7)
    pill(
        ax,
        0.675,
        0.675,
        0.045,
        0.045,
        "$u^{(l)}$",
        face=VERMILION_LIGHT,
        edge=VERMILION,
        color=VERMILION,
        size=6.0,
    )
    arrow(ax, (0.665, 0.697), (0.675, 0.697), color=VERMILION, mutation_scale=7)
    text(ax, 0.59, 0.145, r"$l\in\{24,25,26,27\}$，四层参数独立", size=5.7, color=MUTED)

    rounded_box(
        ax,
        0.79,
        0.66,
        0.165,
        0.12,
        "方向归一化",
        subtitle=r"$u/(\Vert u\Vert_2+\varepsilon)$",
        face=VERMILION_LIGHT,
        edge=VERMILION,
        title_color=VERMILION,
    )
    rounded_box(
        ax,
        0.79,
        0.46,
        0.165,
        0.12,
        "零初始化门",
        subtitle=r"$m\,\rho\tanh(\alpha_l)\,\mathrm{stopgrad}\Vert h\Vert_2$",
        face=GOLD_LIGHT,
        edge=GOLD,
        title_color=GOLD,
        subtitle_size=5.2,
    )
    rounded_box(
        ax,
        0.79,
        0.25,
        0.165,
        0.12,
        "残差相加",
        subtitle=r"$\tilde h^{(l)}=h^{(l)}+\delta^{(l)}$",
        face=BLUE_LIGHT,
        edge=BLUE,
        title_color=BLUE,
    )
    arrow(ax, (0.72, 0.697), (0.79, 0.72), color=VERMILION, linewidth=1.2)
    arrow(ax, (0.872, 0.66), (0.872, 0.58), color=VERMILION, linewidth=1.0)
    arrow(ax, (0.872, 0.46), (0.872, 0.37), color=VERMILION, linewidth=1.0)
    pill(
        ax,
        0.78,
        0.14,
        0.085,
        0.06,
        r"$\alpha_l=0\Rightarrow\delta=0$",
        face=WHITE,
        edge=GOLD,
        color=GOLD,
        size=5.5,
    )
    pill(
        ax,
        0.87,
        0.14,
        0.095,
        0.06,
        r"$\Vert\delta\Vert_2\leq0.1\Vert h\Vert_2$",
        face=WHITE,
        edge=VERMILION,
        color=VERMILION,
        size=5.2,
    )

    return fig


def draw_training_inference_flow() -> Figure:
    fig, ax = canvas(180, 100)
    panel(
        ax,
        0.02,
        0.52,
        0.96,
        0.44,
        "(a) 训练期：公开标签 + 特权物理监督",
        face="#FAFBFC",
        label_width=0.24,
    )
    panel(
        ax,
        0.02,
        0.05,
        0.96,
        0.40,
        "(b) 推理期：仅用部署可观测字段",
        face="#FAFBFC",
        label_width=0.22,
    )

    rounded_box(
        ax,
        0.045,
        0.68,
        0.12,
        0.13,
        "GeNIS 批次",
        subtitle="$x_i,y_i$",
        face=BLUE_LIGHT,
        edge=BLUE,
        title_color=BLUE,
    )
    rounded_box(
        ax,
        0.045,
        0.535,
        0.12,
        0.105,
        "ns-3 批次",
        subtitle="$x_i,q,A,O,L^-,C$",
        face=GOLD_LIGHT,
        edge=GOLD,
        title_color=GOLD,
        subtitle_size=5.4,
    )
    rounded_box(
        ax,
        0.215,
        0.66,
        0.14,
        0.145,
        "冻结 Qwen + S3",
        subtitle="提示前向\n第 13 层状态源",
        face=GRAY_LIGHT,
        edge=GRAY,
    )
    rounded_box(
        ax,
        0.405,
        0.66,
        0.15,
        0.145,
        r"新增结构 $\Psi$",
        subtitle="状态头 + 条件编码\n4 层有界注入",
        face=TEAL_LIGHT,
        edge=TEAL,
        title_color=TEAL,
    )
    rounded_box(
        ax,
        0.61,
        0.70,
        0.10,
        0.095,
        r"$\mathcal{L}_{\mathrm{gen}}$",
        face=VERMILION_LIGHT,
        edge=VERMILION,
        title_color=VERMILION,
    )
    rounded_box(
        ax,
        0.61,
        0.565,
        0.10,
        0.095,
        r"$\mathcal{L}_{\mathrm{state}}+\lambda_p\mathcal{L}_{\mathrm{phy}}$",
        face=GOLD_LIGHT,
        edge=GOLD,
        title_color=GOLD,
        title_size=5.7,
    )
    rounded_box(
        ax,
        0.765,
        0.625,
        0.13,
        0.14,
        "梯度累加与裁剪",
        subtitle=r"AdamW 只更新 $\Psi$" + "\n冻结参数无梯度",
        face=WHITE,
        edge=VERMILION,
        title_color=VERMILION,
    )
    pill(
        ax,
        0.915,
        0.66,
        0.05,
        0.075,
        "202 步",
        face=GRAY_LIGHT,
        edge=GRAY,
        color=INK,
        size=6.0,
    )

    arrow(ax, (0.165, 0.745), (0.215, 0.735), color=BLUE, linewidth=1.35)
    arrow(ax, (0.165, 0.59), (0.215, 0.69), color=BLUE, linewidth=1.0)
    arrow(ax, (0.355, 0.735), (0.405, 0.735), color=TEAL, linewidth=1.35)
    arrow(ax, (0.555, 0.735), (0.61, 0.748), color=VERMILION, linewidth=1.1)
    arrow(
        ax,
        (0.555, 0.69),
        (0.61, 0.612),
        color=GOLD,
        linewidth=1.0,
        linestyle=(0, (3, 2)),
    )
    arrow(
        ax,
        (0.165, 0.585),
        (0.61, 0.612),
        color=GOLD,
        linewidth=1.0,
        linestyle=(0, (3, 2)),
        connectionstyle="arc3,rad=-0.08",
    )
    arrow(ax, (0.71, 0.748), (0.765, 0.72), color=VERMILION, linewidth=1.1)
    arrow(
        ax,
        (0.71, 0.612),
        (0.765, 0.67),
        color=GOLD,
        linewidth=1.0,
        linestyle=(0, (3, 2)),
    )
    arrow(ax, (0.895, 0.695), (0.915, 0.695), color=INK, linewidth=1.0)
    text(
        ax,
        0.47,
        0.545,
        "物理梯度只直达状态头；生成梯度在门离开零点后到达全部新增结构",
        size=5.5,
        color=MUTED,
    )

    rounded_box(
        ax,
        0.045,
        0.19,
        0.115,
        0.12,
        "公共流量 $x_i$",
        subtitle="协议/方向/长度\n间隔/端口/标志位",
        face=BLUE_LIGHT,
        edge=BLUE,
        title_color=BLUE,
        subtitle_size=5.2,
    )
    rounded_box(
        ax,
        0.205,
        0.19,
        0.12,
        0.12,
        "提示预填充",
        subtitle="一次计算 $h^{(13)}$",
        face=GRAY_LIGHT,
        edge=GRAY,
    )
    rounded_box(
        ax,
        0.37,
        0.19,
        0.12,
        0.12,
        "状态与条件",
        subtitle="5 锚点 → 9 词元",
        face=TEAL_LIGHT,
        edge=TEAL,
        title_color=TEAL,
    )
    rounded_box(
        ax,
        0.535,
        0.19,
        0.14,
        0.12,
        "贪心缓存解码",
        subtitle="复用条件 $K/V$\n每新词元执行 4 层注入",
        face=VERMILION_LIGHT,
        edge=VERMILION,
        title_color=VERMILION,
        subtitle_size=5.2,
    )
    rounded_box(
        ax,
        0.72,
        0.19,
        0.12,
        0.12,
        "分层 JSON 输出",
        subtitle="恶意性/家族/子类/证据",
        face=BLUE_LIGHT,
        edge=BLUE,
        title_color=BLUE,
        subtitle_size=5.2,
    )
    rounded_box(
        ax,
        0.865,
        0.16,
        0.10,
        0.17,
        "禁止进入推理",
        subtitle="队列真值\n通量与容量\n场景/攻击真值",
        face=WHITE,
        edge=VERMILION,
        title_color=VERMILION,
        linestyle=(0, (4, 2)),
        subtitle_size=5.1,
    )
    line(ax, [0.875, 0.955], [0.175, 0.315], color=VERMILION, linewidth=1.4)

    for start, end, color in (
        ((0.16, 0.25), (0.205, 0.25), BLUE),
        ((0.325, 0.25), (0.37, 0.25), TEAL),
        ((0.49, 0.25), (0.535, 0.25), TEAL),
        ((0.675, 0.25), (0.72, 0.25), VERMILION),
    ):
        arrow(ax, start, end, color=color, linewidth=1.25)

    pill(
        ax,
        0.20,
        0.085,
        0.18,
        0.055,
        "无真实队列输入",
        face=WHITE,
        edge=TEAL,
        color=TEAL,
        size=5.8,
    )
    pill(
        ax,
        0.405,
        0.085,
        0.18,
        0.055,
        "状态由模型预测",
        face=WHITE,
        edge=TEAL,
        color=TEAL,
        size=5.8,
    )
    pill(
        ax,
        0.61,
        0.085,
        0.18,
        0.055,
        "条件通路不可删除",
        face=WHITE,
        edge=VERMILION,
        color=VERMILION,
        size=5.8,
    )
    return fig


def validate_outputs(entries: list[dict[str, object]]) -> None:
    from xml.etree import ElementTree

    from PIL import Image

    for entry in entries:
        outputs = entry["outputs"]
        assert isinstance(outputs, dict)
        svg_path = ROOT / str(outputs["svg"])
        pdf_path = ROOT / str(outputs["pdf"])
        png_path = ROOT / str(outputs["png"])

        ElementTree.parse(svg_path)
        if not pdf_path.read_bytes().startswith(b"%PDF"):
            raise ValueError(f"PDF 文件头无效: {pdf_path}")
        with Image.open(png_path) as image:
            image.verify()


def main() -> None:
    import PIL

    specs = [
        FigureSpec("图3-1-整体方法框架", 180, 108, draw_overall_framework),
        FigureSpec("图3-2-四窗口五锚点有限队列示意", 180, 90, draw_four_window_queue),
        FigureSpec(
            "图3-3-双锚点与分段守恒机制", 180, 95, draw_dual_anchor_conservation
        ),
        FigureSpec(
            "图3-4-有界物理条件交叉注意力", 180, 100, draw_bounded_cross_attention
        ),
        FigureSpec("图3-5-训练与推理流程", 180, 100, draw_training_inference_flow),
    ]

    entries = [save_figure(spec, spec.draw()) for spec in specs]
    validate_outputs(entries)

    manifest = {
        "generator": Path(__file__).name,
        "python": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
        "matplotlib": matplotlib.__version__,
        "pillow": PIL.__version__,
        "font": {"name": FONT_NAME, "path": str(FONT_PATH)},
        "evidence_mode": "method_schematic_without_experimental_results",
        "figures": entries,
    }
    (ROOT / "图件清单.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for entry in entries:
        print(f"{entry['stem']}: {entry['width_mm']} mm × {entry['height_mm']} mm")


if __name__ == "__main__":
    main()
