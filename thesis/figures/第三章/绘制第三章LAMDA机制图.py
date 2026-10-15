"""生成第三章（LAMDA 线）机制与理论图：图3-1、图3-2、图3-3、图3-4。

本脚本不承载任何实验数据。图3-1 是方法整体框架示意图；图3-2 至图3-4 画的是 3.3.3 与
3.5.4 的解析式，其横纵坐标由公式直接给出，不含拟合值。

字体、版面换算、绘图原语、多格式导出与图件清单全部复用 `figstyle.py`，本脚本不自建
字体解析，也不修改 `figstyle.py`。

两个示意参数在模块顶部集中声明并各有出处：

- `YEAR_SHARD`：3.3.3 节所述「当年度训练分片约 80,000 条」的代表性规模，用于把
  历史权重 λ 从无量纲比例换成横轴 m 上的可比曲线；
- `HOLD_TAU`：保持项的归一化饱和速率。3.5.4 只给出保持项「上升并趋于饱和」与其上界
  ε(N)（式 3.20），未给出封闭形式；本脚本取 R(λ)=1−exp(−λ/τ) 作归一化示意曲线，
  并在图内与图件清单中显式标注该函数为示意、非拟合值，τ 为示意图参数。

执行：uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章LAMDA机制图.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import figstyle as fs
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

# `figstyle` 只把 mathtext 的 rm/it/bf 接到 Cambria Math，未设 `mathtext.cal`。图3-1 的
# 损失符号用 \mathcal{L}，其字形在 Cambria Math 内（U+1D4DB）但默认不被接入，实测会回退到
# macOS 的 Apple-Chancery（2026-10-14 由 pdffonts 核验），违反「数学符号用 Cambria Math」。
# 此处只在本脚本内补设该 rcParam，不修改 figstyle.py。
plt.rcParams["mathtext.cal"] = fs.MATH_FONT.family if fs.MATH_FONT is not None else "stix"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "图件清单.json"
GENERATOR = "绘制第三章LAMDA机制图.py"

INK, MUTED = fs.INK, fs.MUTED
FS_MIN, FS_MAIN = fs.MIN_FONT_PT, fs.MAIN_FONT_PT
GRID = "#D9D9D9"

# 示意图参数（出处见模块 docstring）
YEAR_SHARD = 80_000.0
HOLD_TAU = 0.35
HOLD_EPSILON = 0.6  # 图3-4 中保持项的示意缩放系数（见 docstring）
REPORTED_REUSE = 8  # 3.6.6 实测的最大复用倍数

# 灰度可读的系列约定：颜色只作辅助，区分依靠线型与标记。
SERIES = (
    (fs.M1_EDGE, "-", "o"),
    (fs.M2_EDGE, "--", "s"),
    (INK, "-.", "^"),
    (MUTED, ":", "D"),
)


# ------------------------------------------------------------------ 版面原语


def data_axes(cv: fs.Canvas, rect: tuple[float, float, float, float], grid_axis: str = "y") -> Axes:
    """在归一化画布上叠加一个带刻度的数据坐标区。"""

    ax = cv.fig.add_axes(rect)
    # 数据区背景透明：本画布的浮动标签画在下层背景坐标区上，白色实底会把它盖住。
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


def tag(cv: fs.Canvas, x: float, y: float, value: str, color: str = INK, ha: str = "left") -> None:
    """图内浮动标签：先逐字核验字形，再垫白底以免压住曲线。"""

    fs.check_label(value, FS_MIN)
    cv.ax.text(
        x,
        y,
        value,
        size=FS_MIN,
        color=color,
        ha=ha,
        va="center",
        zorder=9,
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none"},
    )


def note(cv: fs.Canvas, x: float, y: float, value: str, **kw) -> None:
    kw.setdefault("size", FS_MIN)
    kw.setdefault("color", MUTED)
    fs.text(cv, x, y, value, **kw)


def canvas_of(rect: tuple[float, float, float, float], fx: float, fy: float) -> tuple[float, float]:
    """把数据坐标区的轴分数坐标换算为画布归一化坐标。"""

    left, bottom, width, height = rect
    return left + fx * width, bottom + fy * height


# ------------------------------------------------------------------ 图 3-1


def draw_overview(cv: fs.Canvas) -> None:
    """图3-1 方法整体框架：年度循环（模块一）嵌套轮次循环（模块二）的自顶向下流程图。

    与算法 3-1 的循环结构一致：外层为年度循环 ``for t = 1 to T``，模块一（预算切分）
    挂在其内；内层为嵌套其中的轮次循环 ``for r = 1 to R``，模块二（复用配置）挂在其内。
    两个判定菱形分别控制两个循环的终止，「是」分支向右引出跨年评价与模型保存，回边在
    左侧分两层返回各自的循环入口。节点类型以形状与线型区分（椭圆＝起止、矩形＝处理、
    虚线菱形＝判定、粗边灰底框＝模块），颜色只作辅助，灰度下同样可读。
    """

    from matplotlib.patches import Ellipse, Polygon

    # 版面基线（归一化坐标，画布 150 mm × 140 mm）
    cx = 0.289  # 主脊中心线
    bx, bw = 0.072, 0.434  # 主脊处理节点与模块内子框的横向范围
    fx, fw = 0.058, 0.462  # 模块外框的横向范围
    rx0, rx1 = 0.556, 0.868  # 右列（各「是」分支）节点的横向范围
    rcx = (rx0 + rx1) / 2.0
    lane_outer, lane_inner = 0.016, 0.042  # 左侧回边通道：外圈为年度循环，内圈为轮次循环
    lane_right, top_lane = 0.935, 0.975  # 年度循环回边的右侧上行通道与图顶横跨高度
    dhw, dhh = 0.086, 0.025  # 判定菱形的半宽与半高
    band, sub_h, sub_gap = 0.040, 0.046, 0.006  # 模块的标题带高、子框高与子框间距

    def spine(top_from: float, top_to: float) -> None:
        fs.arrow(cv, (cx, top_from), (cx, top_to), head=7.0)

    def plain(top: float, height: float, lines) -> None:
        fs.box(
            cv,
            bx,
            top - height,
            bw,
            height,
            lines,
            face=fs.WHITE,
            edge=fs.MUTED,
            linewidth=0.8,
            radius=0.006,
            zorder=3,
        )

    def terminator(top: float, height: float, half_width: float, lines) -> None:
        center = top - height / 2.0
        cv.ax.add_patch(
            Ellipse(
                (cx, center),
                2.0 * half_width,
                height,
                facecolor=fs.SHADE,
                edgecolor=fs.MUTED,
                linewidth=fs.MAIN_LINE_PT,
                zorder=3,
            )
        )
        fs.stack(cv, cx, center, lines)

    def decision(center: float, label: str) -> None:
        cv.ax.add_patch(
            Polygon(
                ((cx, center + dhh), (cx + dhw, center), (cx, center - dhh), (cx - dhw, center)),
                closed=True,
                facecolor=fs.SHADE,
                edgecolor=fs.MUTED,
                linewidth=fs.MAIN_LINE_PT,
                linestyle=(0.0, (3.0, 2.0)),
                zorder=3,
            )
        )
        fs.text(cv, cx, center, label, size=FS_MIN)

    def module(top: float, title: str, cells) -> None:
        height = band + len(cells) * sub_h + (len(cells) - 1) * sub_gap + 0.010
        fs.box(
            cv,
            fx,
            top - height,
            fw,
            height,
            face=fs.SHADE,
            edge=fs.MUTED,
            linewidth=2.0,
            radius=0.012,
            zorder=1,
        )
        fs.text(cv, fx + 0.012, top - 0.008, title, size=FS_MAIN, color=INK, ha="left", va="top")
        for index, (lines, tag) in enumerate(cells):
            cell_top = top - band - index * (sub_h + sub_gap)
            fs.box(
                cv,
                bx,
                cell_top - sub_h,
                bw,
                sub_h,
                lines,
                face=fs.WHITE,
                edge=fs.MUTED,
                linewidth=0.7,
                radius=0.004,
                zorder=4,
            )
            if tag:
                fs.text(
                    cv,
                    bx + bw - 0.008,
                    cell_top - 0.006,
                    tag,
                    size=FS_MIN,
                    color=MUTED,
                    ha="right",
                    va="top",
                )

    def right_box(top: float, height: float, lines) -> None:
        fs.box(
            cv,
            rx0,
            top - height,
            rx1 - rx0,
            height,
            lines,
            face=fs.WHITE,
            edge=fs.MUTED,
            linewidth=0.8,
            radius=0.006,
            zorder=3,
        )

    # 主干：开始 → 当年度分片 → 年度循环入口 → 模块一 → 轮次循环入口 → 模块二 → 更新
    terminator(
        0.948,
        0.054,
        0.150,
        (
            fs.Line("开始：初始化模型参数", FS_MIN, span=1.1),
            fs.Line(r"$\theta,\ M\leftarrow\varnothing$", FS_MIN, "math", span=1.2),
        ),
    )
    plain(
        0.883,
        0.052,
        (
            fs.Line("当年度训练分片到达（4561 维二值特征）", FS_MIN, span=1.1),
            fs.Line(r"$D_t$", FS_MIN, "math", span=1.3),
        ),
    )
    plain(0.820, 0.038, (fs.Line(r"$t\leftarrow 1$", FS_MIN, "math", span=1.3),))
    decision(0.746, r"$t>T\,?$")
    spine(0.894, 0.883)
    spine(0.831, 0.820)
    spine(0.782, 0.771)
    spine(0.721, 0.697)

    module(
        0.697,
        "模块一：预算切分",
        (
            (
                (
                    fs.Line("按预算切出缓冲条数", FS_MIN, span=1.1),
                    fs.Line(r"$N\leftarrow\lfloor B/d\rfloor$", FS_MIN, "math", span=1.1),
                ),
                "式 3.2",
            ),
            (
                (
                    fs.Line("按已到达年度数均分", FS_MIN, span=1.1),
                    fs.Line(r"$q\leftarrow\lfloor N/(t-1)\rfloor$", FS_MIN, "math", span=1.1),
                ),
                "式 3.3",
            ),
            (
                (
                    fs.Line("年内正负各半填充缓冲 M", FS_MIN, span=1.1),
                    fs.Line("（正例不足由负例补足）", FS_MIN, span=1.1),
                ),
                None,
            ),
        ),
    )

    plain(0.486, 0.038, (fs.Line(r"$r\leftarrow 1$", FS_MIN, "math", span=1.3),))
    decision(0.412, r"$r>R\,?$")
    spine(0.497, 0.486)
    spine(0.448, 0.437)

    module(
        0.363,
        "模块二：复用配置",
        (
            (
                (
                    fs.Line("拼接训练集合", FS_MIN, span=1.1),
                    fs.Line(r"$\tilde{D}\leftarrow D_t\cup(M\times m)$", FS_MIN, "math", span=1.1),
                ),
                "式 3.4",
            ),
            ((fs.Line("全局打乱后按批更新", FS_MIN, span=1.1),), None),
            (
                (
                    fs.Line("历史权重", FS_MIN, span=1.1),
                    fs.Line(r"$\lambda=mN/(n_t+mN)$", FS_MIN, "math", span=1.1),
                ),
                "式 3.5-3.6",
            ),
        ),
    )

    spine(0.387, 0.363)
    spine(0.163, 0.152)
    plain(
        0.152,
        0.046,
        (
            fs.Line("参数更新", FS_MIN, span=1.05),
            fs.Line(r"$\theta$", FS_MIN, "math", span=1.15),
        ),
    )
    spine(0.106, 0.095)
    plain(0.095, 0.038, (fs.Line(r"$r\leftarrow r+1$", FS_MIN, "math", span=1.3),))

    # 右列：两个「是」分支的出口
    right_box(
        0.770,
        0.048,
        (
            fs.Line("保存模型", FS_MIN, span=1.05),
            fs.Line(r"$\theta_T$", FS_MIN, "math", span=1.15),
        ),
    )
    cv.ax.add_patch(
        Ellipse(
            (rcx, 0.658),
            0.200,
            0.046,
            facecolor=fs.SHADE,
            edgecolor=fs.MUTED,
            linewidth=fs.MAIN_LINE_PT,
            zorder=3,
        )
    )
    fs.stack(cv, rcx, 0.658, (fs.Line("结束", FS_MIN),))
    right_box(
        0.447,
        0.070,
        (
            fs.Line("在已到达年度的测试分片", FS_MIN, span=1.0),
            fs.Line(r"$E_1,\ldots,E_t$", FS_MIN, "math", span=1.3),
            fs.Line("上逐片评价并记录 F1", FS_MIN, span=1.0),
        ),
    )
    right_box(0.316, 0.042, (fs.Line(r"$t\leftarrow t+1$", FS_MIN, "math", span=1.3),))

    # 「是」分支：判定 → 右列
    fs.arrow(cv, (cx + dhw, 0.746), (rx0, 0.746), head=7.0)
    fs.arrow(cv, (rcx, 0.722), (rcx, 0.681), head=7.0)
    fs.arrow(cv, (cx + dhw, 0.412), (rx0, 0.412), head=7.0)
    fs.arrow(cv, (rcx, 0.377), (rcx, 0.316), head=7.0)

    # 回边：年度循环沿右侧与图顶绕回（外圈），轮次循环沿左侧绕回（内圈）
    fs.routed_arrow(
        cv,
        (
            (rx1, 0.295),
            (lane_right, 0.295),
            (lane_right, top_lane),
            (lane_outer, top_lane),
            (lane_outer, 0.746),
            (cx - dhw, 0.746),
        ),
    )
    fs.routed_arrow(
        cv,
        ((bx, 0.076), (lane_inner, 0.076), (lane_inner, 0.412), (cx - dhw, 0.412)),
    )

    for label, y in (("是", 0.762), ("是", 0.428)):
        fs.text(cv, (cx + dhw + rx0) / 2.0, y, label, size=FS_MIN)
    for label, y in (("否", 0.709), ("否", 0.375)):
        fs.text(cv, cx + 0.024, y, label, size=FS_MIN, ha="left")

    fs.footnote(
        cv,
        "两个配置量代价性质不同：N 受存储预算约束；m 不改变存储占用，只改变历史信息进入梯度的强度",
        y=0.026,
    )


# ------------------------------------------------------------------ 图 3-2


def draw_weight_curves(cv: fs.Canvas) -> None:
    """图3-2 历史权重 λ(m,N) 随复用倍数 m 的变化（式 3-5）。"""

    rect = (0.150, 0.215, 0.825, 0.645)
    ax = data_axes(cv, rect)
    m = np.logspace(0.0, 3.0, 500)
    capacities = (50, 200, 800, 18854)
    for (color, ls, marker), cap in zip(SERIES, capacities, strict=True):
        lam = m * cap / (YEAR_SHARD + m * cap)
        ax.plot(m, lam, color=color, linestyle=ls, linewidth=fs.MAIN_LINE_PT, zorder=4)
        lam8 = REPORTED_REUSE * cap / (YEAR_SHARD + REPORTED_REUSE * cap)
        ax.plot(
            [REPORTED_REUSE],
            [lam8],
            marker=marker,
            markersize=3.8,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=0.9,
            linestyle="none",
            zorder=5,
        )
    # 曲线标签放在左上空白区，避免高容量曲线在右上方与图注相撞。
    for index, ((color, ls, _), cap) in enumerate(zip(SERIES, capacities, strict=True)):
        y = 0.828 - index * 0.066
        tag(cv, 0.238, y, f"N = {cap:,}", color=color)
        cv.ax.plot([0.172, 0.230], [y, y], color=color, linestyle=ls, linewidth=fs.MAIN_LINE_PT)
    ax.axhline(1.0, color=fs.HAIRLINE, linewidth=fs.AUX_LINE_PT, linestyle=(0, (1, 2)), zorder=1)
    ax.axvline(REPORTED_REUSE, color=fs.HAIRLINE, linewidth=fs.AUX_LINE_PT, zorder=1)
    ax.set_xscale("log")
    ax.set_xlim(1.0, 1000.0)
    ax.set_ylim(0.0, 1.0)
    ax.minorticks_off()
    ax.set_xticks([1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1000])
    tick_labels(ax, "x", ["1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1000"])
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    tick_labels(ax, "y", ["0", "0.25", "0.50", "0.75", "1.00"])
    axis_label(ax, "x", "复用倍数 m（对数刻度）")
    axis_label(ax, "y", "历史权重 λ")
    note(cv, 0.500, 0.955, "空心标记为 m=8 处的历史权重；虚线为 m=8 参考线", ha="left")
    note(cv, 0.500, 0.915, "λ 以 1 为上界，容量越小达到同一权重所需 m 越大", ha="left")


# ------------------------------------------------------------------ 图 3-3


def _hold(lam: np.ndarray) -> np.ndarray:
    """归一化保持项 R(λ)=1−exp(−λ/τ)；示意曲线，非拟合值（见模块 docstring）。"""

    return 1.0 - np.exp(-lam / HOLD_TAU)


def draw_adapt_step(cv: fs.Canvas) -> None:
    """图3-3 有效适应步长 a(λ) 与保持项的交点给出内部最优 λ*。"""

    rect = (0.150, 0.215, 0.825, 0.690)
    ax = data_axes(cv, rect)
    lam = np.linspace(0.0, 1.0, 800)
    ratios = (0.2, 0.5, 0.8)
    for (color, ls, marker), rk in zip(SERIES[: len(ratios)], ratios, strict=True):
        a = (1.0 - lam) + lam * rk
        ax.plot(lam, a, color=color, linestyle=ls, linewidth=fs.MAIN_LINE_PT, zorder=4)
        cross = float(lam[int(np.argmin(np.abs(a - _hold(lam))))])
        ax.plot(
            [cross],
            [float(np.interp(cross, lam, a))],
            marker=marker,
            markersize=4.0,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=0.9,
            linestyle="none",
            zorder=6,
        )
        ax.vlines(
            cross,
            0.0,
            float(np.interp(cross, lam, a)),
            color=color,
            linewidth=fs.AUX_LINE_PT,
            linestyle=(0, (1, 2)),
            zorder=2,
        )
        ax.plot([0.0, 1.0], [rk, rk], color=fs.HAIRLINE, linewidth=fs.AUX_LINE_PT, zorder=1)
    ax.plot(lam, _hold(lam), color=INK, linewidth=1.5, zorder=5)
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.05)
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    tick_labels(ax, "x", ["0", "0.25", "0.50", "0.75", "1.00"])
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0])
    tick_labels(ax, "y", ["0", "0.25", "0.50", "0.75", "1.00"])
    axis_label(ax, "x", "历史权重 λ")
    axis_label(ax, "y", "归一化作用强度")
    for (color, _, _), rk in zip(SERIES[: len(ratios)], ratios, strict=True):
        value = 1.0 - 0.72 * (1.0 - rk)
        tag(cv, 0.150 + 0.72 * 0.825 + 0.012, 0.215 + value * 0.690, f"ρκ = {rk}", color=color)
    note(cv, 0.500, 0.955, "粗线为保持项（归一化示意曲线，非拟合值）", ha="left")
    note(cv, 0.500, 0.917, "空心标记为 a(λ) 与保持项的交点，即内部最优 λ*", ha="left")


# ------------------------------------------------------------------ 图 3-4


def draw_tradeoff(cv: fs.Canvas) -> None:
    """图3-4 保持项与适应项合成出内部最优 λ*。"""

    rect = (0.145, 0.205, 0.825, 0.660)
    ax = data_axes(cv, rect)
    lam = np.linspace(0.0, 1.0, 1200)
    rk = 0.5
    # 保持项按 ε=0.6 作示意缩放，使两项在同一纵轴上可比；ε 为示意图参数（见 docstring）。
    hold = HOLD_EPSILON * _hold(lam)
    adapt = (1.0 - lam) + lam * rk
    composite = hold + adapt
    star = float(lam[int(np.argmax(composite))])
    peak = float(composite.max())

    ax.plot(lam, hold, color=fs.M1_EDGE, linestyle="--", linewidth=fs.MAIN_LINE_PT, zorder=4)
    ax.plot(lam, adapt, color=fs.M2_EDGE, linestyle="-.", linewidth=fs.MAIN_LINE_PT, zorder=4)
    ax.plot(lam, composite, color=INK, linestyle="-", linewidth=1.5, zorder=5)
    ax.vlines(star, 0.0, peak, color=fs.HAIRLINE, linewidth=fs.AUX_LINE_PT, linestyle=(0, (1, 2)), zorder=1)
    ax.plot(
        [star],
        [peak],
        marker="v",
        markersize=4.4,
        markerfacecolor=INK,
        markeredgecolor=INK,
        linestyle="none",
        zorder=7,
    )
    ax.annotate(
        f"λ* = {star:.2f}",
        xy=(star, peak),
        xytext=(0.66, 0.96),
        fontsize=FS_MIN,
        color=INK,
        arrowprops={"arrowstyle": "-|>", "linewidth": 0.7, "color": INK},
        zorder=8,
    )
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.45)
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    tick_labels(ax, "x", ["0", "0.25", "0.50", "0.75", "1.00"])
    ax.set_yticks([0.0, 0.25, 0.5, 0.75, 1.0, 1.25])
    tick_labels(ax, "y", ["0", "0.25", "0.50", "0.75", "1.00", "1.25"])
    axis_label(ax, "x", "历史权重 λ")
    axis_label(ax, "y", "归一化作用强度")

    legend = (
        ("保持项 ε·R(λ)：上升并饱和（ε = 0.6）", fs.M1_EDGE, "--"),
        ("适应项 a(λ)：线性下降（ρκ = 0.5）", fs.M2_EDGE, "-."),
        ("合成目标 ε·R(λ) + a(λ)", INK, "-"),
    )
    for index, (text_value, color, ls) in enumerate(legend):
        y0 = 0.950 - index * 0.062
        cv.ax.plot([0.165, 0.225], [y0, y0], color=color, linestyle=ls, linewidth=fs.MAIN_LINE_PT)
        tag(cv, 0.233, y0, text_value, color=color)


# ------------------------------------------------------------------ 清单


def finalize_manifest(previous: dict[str, object]) -> None:
    """补记 `figstyle.write_manifest` 未覆盖的字段：真实数学字体、生成器清单、其余顶层段。

    `figstyle.write_manifest` 每次都会新建一个只含 `figures` 的顶层字典，其余顶层键
    （撤下段、制品哈希、口径段）与 `environment.generators` 都会被丢弃。本脚本可能先于或
    后于结果图脚本运行，因此必须把上一版清单中的这些键原样恢复，保证清单内容与运行顺序无关。
    """

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for key, value in previous.items():
        data.setdefault(key, value)
    for entry in data["figures"]:
        if entry["stem"] in MECHANISM_STEMS:
            entry["data_keys"] = ["机制与理论示意图，不承载实验数据"]

    typography = data["typography"]
    typography["math_fontset"] = "stix（回退）" if fs.MATH_FONT is None else fs.MATH_FONT.family
    typography["math_font_path"] = None if fs.MATH_FONT is None else fs.MATH_FONT.path

    previous_environment = previous.get("environment", {})
    generators = {
        g for g in (list(previous_environment.get("generators", [])) + [GENERATOR]) if g
    }
    environment = data["environment"]
    environment["generators"] = sorted(generators)
    environment["generator"] = GENERATOR
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ 主流程

SPECS: tuple[tuple[str, str, float, float, object], ...] = (
    (
        "图3-1-方法整体框架",
        "预算约束记忆配置方法的自顶向下流程图，与算法 3-1 的循环结构一致。外层为年度循环"
        "（模块一：预算切分）：按存储预算切出缓冲条数 N=⌊B/d⌋（式 3.2），按已到达年度数"
        "均分单年配额 q=⌊N/(t−1)⌋（式 3.3），并在年内正负各半填充缓冲 M。内层为嵌套在其中的"
        "轮次循环（模块二：复用配置）：每轮把当年度训练分片与重复 m 次的缓冲拼接（式 3.4），"
        "全局打乱后按批更新，历史权重由 λ=mN/(n_t+mN)（式 3.5-3.6）给出。两个判定菱形分别"
        "控制两个循环的终止：「是」分支向右引出模型的保存与在全部已到达年度测试分片上的"
        "评价，「否」分支继续循环。回边在左侧分两层返回各自的循环入口，外圈为年度循环、"
        "内圈为轮次循环。示意图，不承载实验数据。",
        150.0,
        140.0,
        draw_overview,
    ),
    (
        "图3-2-历史权重随复用倍数的变化",
        "历史权重 λ(m,N)=mN/(n_t+mN)（式 3-5）在缓冲容量 N 取 50、200、800 与 18,854 时"
        "随复用倍数 m 的变化，横轴为对数刻度。λ 关于 m 单调递增并以 1 为上界；容量越小，"
        "达到同一历史权重所需的复用倍数越大。n_t 取 3.3.3 节所述代表性当年度训练分片规模"
        "8×10⁴ 条。空心标记为本章实测最大复用倍数 m=8 处。纯解析曲线，不承载实验数据。",
        132.0,
        88.0,
        draw_weight_curves,
    ),
    (
        "图3-3-有效适应步长随历史权重的变化",
        "有效适应步长 a(λ)=(1−λ)+λρκ（式 3-19）在 ρκ 取 0.2、0.5、0.8（均小于 1）时的直线，"
        "粗线为归一化保持项示意曲线，空心标记为二者的交点，即定理 4 的内部最优 λ*。"
        "ρκ 越小，a(λ) 下降越快，λ* 越靠左。保持项取 1−exp(−λ/τ)、τ=0.35，为示意图而非拟合值。"
        "不承载实验数据。",
        132.0,
        88.0,
        draw_adapt_step,
    ),
    (
        "图3-4-复用配置的两个相反作用示意",
        "保持项 ε·R(λ)（上升并饱和）与适应项 a(λ)（ρκ=0.5 时线性下降）方向相反且一者"
        "饱和、一者不饱和，其合成目标在内部取得极大，给出内部最优 λ*（式 3-17）；"
        "对应的最优复用倍数由式 (3-18) 换算。保持项取 1−exp(−λ/τ)、τ=0.35，并按 ε=0.6 作"
        "示意缩放使两项在同一纵轴上可比；τ 与 ε 均为示意图参数而非拟合值。本图只说明内部"
        "最优的存在性与位置，不给出拟合数值。不承载实验数据。",
        140.0,
        90.0,
        draw_tradeoff,
    ),
)


MECHANISM_STEMS = frozenset(spec[0] for spec in SPECS)


def main() -> int:
    previous: dict[str, object] = {}
    if MANIFEST_PATH.exists():
        previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    entries: list[dict[str, object]] = []
    for stem, caption, width_mm, height_mm, draw in SPECS:
        cv = fs.canvas(width_mm, height_mm)
        draw(cv)
        spec = fs.FigureSpec(stem, width_mm, height_mm, None, caption)
        entries.append(fs.save_figure(ROOT, spec, cv))

    for line in fs.verify_outputs(ROOT, entries):
        logger.info(line)

    fs.write_manifest(ROOT, GENERATOR, entries, evidence_mode="机制示意图（不承载实验数据）")
    finalize_manifest(previous)
    logger.info("已写出 %d 张机制图与 %s", len(entries), MANIFEST_PATH.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
