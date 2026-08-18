"""生成第三章四张方法机制示意图（图3-1 ~ 图3-4）。

本脚本不读取任何实验结果、日志或运行制品，图中一切数值均为方法规格或示意取值，
对应图件清单中的 `evidence_mode = method_schematic_without_experimental_results`。

生成命令：
    uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章机制图.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

import figstyle as fs
from figstyle import Canvas, FigureSpec, Line

ROOT = Path(__file__).resolve().parent

EVIDENCE_MODE = "method_schematic_without_experimental_results"
NO_DATA_NOTE = "本图为方法机制示意，不含任何实验结果数值。"


# ================================================================ 图3-1


def draw_overall_framework() -> Canvas:
    """整体方法框架：从原始流到实体级告警的两机制流水线。"""

    cv = fs.canvas(150.0, 95.0)

    left = 0.145
    right = 0.995
    span = right - left
    channel_x = 0.113
    band_h = 0.185

    band_y = {"input": 0.775, "repr": 0.475, "decide": 0.175}
    band_label = (
        ("input", "输入与序列构造", fs.MUTED),
        ("repr", "表示层 · 计算侧", fs.M1_EDGE),
        ("decide", "决策层 · 汇聚侧", fs.M2_EDGE),
    )
    for key, label, color in band_label:
        fs.box(
            cv,
            0.018,
            band_y[key],
            0.058,
            band_h,
            face=fs.SHADE,
            edge=fs.HAIRLINE,
            linewidth=0.7,
            radius=0.010,
            zorder=2,
        )
        fs.text(
            cv,
            0.047,
            band_y[key] + band_h / 2.0,
            label,
            size=fs.MAIN_FONT_PT,
            color=color,            rotation=90.0,
        )

    def row(count: int, gap: float) -> tuple[float, list[float]]:
        width = (span - gap * (count - 1)) / count
        centers = [left + width / 2.0 + i * (width + gap) for i in range(count)]
        return width, centers

    w4, c4 = row(4, 0.036)
    w3, c3 = row(3, 0.050)

    # --- 第一带：输入与序列构造
    input_boxes = (
        (
            Line("原始流记录", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line("83 维 CICFlowMeter 特征", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        (
            Line("按 2-IP 无向对分组", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line(r"$e=\chi(a,b)$", fs.MIN_FONT_PT, "math", fs.MUTED),
        ),
        (
            Line("组内按时间升序", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line(r"$t_1<t_2<\cdots<t_n$", fs.MIN_FONT_PT, "math", fs.MUTED),
        ),
        (
            Line("切分非重叠序列", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line("尾块补零并掩码", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            Line(r"$L=128$", fs.MIN_FONT_PT, "math", fs.MUTED),
        ),
    )
    for cx, lines in zip(c4, input_boxes, strict=True):
        fs.box(cv, cx - w4 / 2.0, band_y["input"], w4, band_h, lines)

    # --- 第二带：表示层
    repr_boxes = (
        (
            (
                Line("逐流编码器", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line(r"$f:\ x_t\mapsto h_t$", fs.MIN_FONT_PT, "math", fs.MUTED),
            ),
            None,
        ),
        (
            (
                Line("因果前缀跨流聚合", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
                Line(r"$\mathrm{ctx}_t$", fs.MIN_FONT_PT, "math", fs.M1_EDGE),
            ),
            "机制一",
        ),
        (
            (
                Line("表示拼接", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line(r"$[\,h_t,\ \mathrm{ctx}_t\,]$", fs.MIN_FONT_PT, "math", fs.MUTED),
            ),
            None,
        ),
        (
            (
                Line("输出头", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line("逐流分数", fs.MIN_FONT_PT, "cjk", fs.MUTED),
                Line(r"$s_f$", fs.MIN_FONT_PT, "math", fs.MUTED),
            ),
            None,
        ),
    )
    for cx, (lines, tag) in zip(c4, repr_boxes, strict=True):
        highlight = tag is not None
        fs.box(
            cv,
            cx - w4 / 2.0,
            band_y["repr"],
            w4,
            band_h,
            lines,
            face=fs.M1_FACE if highlight else fs.WHITE,
            edge=fs.M1_EDGE if highlight else fs.MUTED,
            linewidth=1.4 if highlight else fs.MAIN_LINE_PT,
            hatch=fs.M1_HATCH if highlight else None,
        )
        if tag:
            fs.pill(
                cv,
                cx,
                band_y["repr"] + band_h,
                0.098,
                0.052,
                tag,
                face=fs.WHITE,
                edge=fs.M1_EDGE,
                color=fs.M1_EDGE,
            )

    # --- 第三带：决策层
    decide_boxes = (
        (
            (
                Line("实体内分数集合", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line(r"$\{s_f\}_{f\in e}$", fs.MIN_FONT_PT, "math", fs.MUTED),
            ),
            None,
        ),
        (
            (
                Line("实体级可学 Lp 池化", fs.MAIN_FONT_PT, "cjk", fs.M2_EDGE),
                Line(
                    r"$S_e=\left(\frac{1}{n}\sum_f s_f^{\,p}\right)^{1/p}$",
                    fs.MIN_FONT_PT,
                    "math",
                    fs.M2_EDGE,
                ),
            ),
            "机制二",
        ),
        (
            (
                Line("实体级告警", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line("按实体分数排序输出", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
            None,
        ),
    )
    for cx, (lines, tag) in zip(c3, decide_boxes, strict=True):
        highlight = tag is not None
        fs.box(
            cv,
            cx - w3 / 2.0,
            band_y["decide"],
            w3,
            band_h,
            lines,
            face=fs.M2_FACE if highlight else fs.WHITE,
            edge=fs.M2_EDGE if highlight else fs.MUTED,
            linewidth=1.4 if highlight else fs.MAIN_LINE_PT,
            hatch=fs.M2_HATCH if highlight else None,
        )
        if tag:
            fs.pill(
                cv,
                cx,
                band_y["decide"] + band_h,
                0.098,
                0.052,
                tag,
                face=fs.WHITE,
                edge=fs.M2_EDGE,
                color=fs.M2_EDGE,
            )

    # --- 带内箭头
    for key, centers, width in (
        ("input", c4, w4),
        ("repr", c4, w4),
        ("decide", c3, w3),
    ):
        cy = band_y[key] + band_h / 2.0
        for a, b in zip(centers, centers[1:], strict=False):
            fs.arrow(cv, (a + width / 2.0 + 0.004, cy), (b - width / 2.0 - 0.004, cy))

    # --- 跨带换行走线
    for upper, lower in (("input", "repr"), ("repr", "decide")):
        y_top = band_y[upper]
        y_mid = (band_y[upper] + band_y[lower] + band_h) / 2.0
        y_bot = band_y[lower] + band_h / 2.0
        fs.routed_arrow(
            cv,
            [
                (c4[-1], y_top),
                (c4[-1], y_mid),
                (channel_x, y_mid),
                (channel_x, y_bot),
                (left - 0.004, y_bot),
            ],
            color=fs.RULE,
        )

    fs.footnote(cv, NO_DATA_NOTE, y=0.075)
    return cv


# ================================================================ 图3-2


def draw_entity_key_sequence() -> Canvas:
    """二 IP 无向对序列构造：归并、排序、非重叠切分与掩码。"""

    cv = fs.canvas(150.0, 80.0)

    panel_top = 0.115
    panel_h = 0.79
    fs.panel(cv, 0.012, panel_top, 0.245, panel_h, "(a) 原始流记录")
    fs.panel(cv, 0.277, panel_top, 0.345, panel_h, "(b) 无向对实体键")
    fs.panel(cv, 0.642, panel_top, 0.346, panel_h, "(c) 排序与非重叠切分")

    # --- (a) 五条原始流，源宿方向与时间顺序均无序
    flows = (
        (r"$f_1:\ A\rightarrow B,\ t=1.2$", "e1"),
        (r"$f_2:\ B\rightarrow A,\ t=0.8$", "e1"),
        (r"$f_3:\ B\rightarrow C,\ t=1.9$", "e2"),
        (r"$f_4:\ A\rightarrow B,\ t=2.7$", "e1"),
        (r"$f_5:\ B\rightarrow A,\ t=3.5$", "e1"),
    )
    row_h = 0.098
    row_top = 0.735
    row_y: list[float] = []
    for index, (label, group) in enumerate(flows):
        cy = row_top - index * (row_h + 0.020)
        row_y.append(cy)
        fs.box(
            cv,
            0.026,
            cy - row_h / 2.0,
            0.218,
            row_h,
            (Line(label, fs.MIN_FONT_PT, "math", fs.INK),),
            edge=fs.M1_EDGE if group == "e1" else fs.RULE,
            linewidth=fs.MAIN_LINE_PT,
        )
    fs.text(
        cv,
        0.026,
        0.155,
        "A、B、C 表示主机 IP",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )

    # --- (b) 归并规则与两个实体键
    fs.box(
        cv,
        0.288,
        0.700,
        0.322,
        0.105,
        (
            Line(
                r"$\chi(a,b)=\mathrm{sortlex}\{\mathrm{srcIP},\,\mathrm{dstIP}\}$",
                fs.MIN_FONT_PT,
                "math",
                fs.INK,
            ),
        ),
        face=fs.SHADE,
        edge=fs.MUTED,
    )
    fs.text(
        cv,
        0.449,
        0.646,
        "取字典序较小者在前，方向被抹去",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )
    fs.box(
        cv,
        0.288,
        0.385,
        0.322,
        0.150,
        (
            Line(r"$e_1=\{A,\ B\}$", fs.MAIN_FONT_PT, "math", fs.M1_EDGE),
            Line("A→B 与 B→A 归为同一键", fs.MIN_FONT_PT, "cjk", fs.M1_EDGE),
        ),
        face=fs.M1_FACE,
        edge=fs.M1_EDGE,
        linewidth=1.4,
    )
    fs.box(
        cv,
        0.288,
        0.205,
        0.322,
        0.115,
        (Line(r"$e_2=\{B,\ C\}$", fs.MAIN_FONT_PT, "math", fs.MUTED),),
        edge=fs.RULE,
    )
    for cy, (_, group) in zip(row_y, flows, strict=True):
        target = 0.460 if group == "e1" else 0.2625
        fs.arrow(
            cv,
            (0.248, cy),
            (0.284, target),
            color=fs.M1_EDGE if group == "e1" else fs.RULE,
            linewidth=0.8,
            head=6.0,
            connectionstyle="arc3,rad=0.08",
        )

    # --- (c) 同键内按时间升序，再切成非重叠块
    fs.text(
        cv,
        0.660,
        0.760,
        "同一实体键内按时间升序",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )
    chip_w = 0.070
    chip_x = [0.660 + i * (chip_w + 0.014) for i in range(4)]
    for x, label in zip(chip_x, ("0.8", "1.2", "2.7", "3.5"), strict=True):
        fs.box(
            cv,
            x,
            0.630,
            chip_w,
            0.088,
            (Line(rf"$t={label}$", fs.MIN_FONT_PT, "math", fs.INK),),
            edge=fs.M1_EDGE,
        )
    fs.arrow(cv, (0.660, 0.596), (0.976, 0.596), color=fs.RULE, linewidth=0.8, head=6.0)
    fs.text(cv, 0.818, 0.560, "时间升序", size=fs.MIN_FONT_PT, color=fs.MUTED)

    fs.text(
        cv,
        0.660,
        0.487,
        "切成长度 L 的非重叠块",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )
    grid_x = 0.660
    grid_w = 0.316
    cw = grid_w / 8.0
    ch = cv.square_dy(cw)
    grid_y = 0.335
    for index in range(8):
        padded = index >= 6
        fs.cell(
            cv,
            grid_x + index * cw,
            grid_y,
            cw,
            ch,
            face=fs.WHITE if padded else fs.M1_FACE,
            edge=fs.RULE if padded else fs.M1_EDGE,
            linewidth=0.7,
            hatch=None if padded else fs.M1_HATCH,
        )
        fs.text(
            cv,
            grid_x + (index + 0.5) * cw,
            grid_y - 0.062,
            "0" if padded else "1",
            size=fs.MIN_FONT_PT,
            color=fs.MUTED,
        )
    fs.polyline(
        cv,
        [(grid_x + 4 * cw, grid_y - 0.028), (grid_x + 4 * cw, grid_y + ch + 0.028)],
        color=fs.INK,
        linewidth=fs.MAIN_LINE_PT,
    )
    fs.text(
        cv,
        grid_x + 2 * cw,
        grid_y + ch + 0.052,
        "块 1",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
    )
    fs.text(
        cv,
        grid_x + 6 * cw,
        grid_y + ch + 0.052,
        "块 2（尾块补零）",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )
    fs.text(
        cv,
        grid_x - 0.008,
        grid_y - 0.062,
        "掩码",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="right",
    )
    fs.text(
        cv,
        0.818,
        0.175,
        "正文取 L = 128，图中缩略为 4",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )

    fs.footnote(cv, NO_DATA_NOTE, y=0.048)
    return cv


# ================================================================ 图3-3


def draw_causal_prefix_aggregation() -> Canvas:
    """因果前缀跨流聚合：下三角掩码、非因果整窗对照与增量更新。"""

    cv = fs.canvas(140.0, 95.0)

    steps = 8
    grid_w = 0.245
    cw = grid_w / steps
    ch = cv.square_dy(cw)
    grid_x = 0.105

    def draw_matrix(bottom: float, causal: bool) -> None:
        for r in range(steps):  # r 自上而下，对应查询位置 t
            t = r + 1
            y = bottom + (steps - 1 - r) * ch
            for c in range(steps):
                i = c + 1
                active = (i <= t) if causal else True
                fs.cell(
                    cv,
                    grid_x + c * cw,
                    y,
                    cw,
                    ch,
                    face=(fs.M1_FACE if causal else fs.SHADE) if active else fs.WHITE,
                    edge=fs.RULE,
                    linewidth=0.5,
                    hatch=(fs.M1_HATCH if causal else fs.M2_HATCH) if active else None,
                )
            fs.text(
                cv,
                grid_x - 0.012,
                y + ch / 2.0,
                str(t),
                size=fs.MIN_FONT_PT,
                color=fs.MUTED,
                ha="right",
            )
        for c in range(steps):
            fs.text(
                cv,
                grid_x + (c + 0.5) * cw,
                bottom + steps * ch + 0.022,
                str(c + 1),
                size=fs.MIN_FONT_PT,
                color=fs.MUTED,
            )
        fs.text(
            cv,
            grid_x - 0.050,
            bottom + steps * ch / 2.0,
            "查询位置 t",
            size=fs.MIN_FONT_PT,
            color=fs.INK,
            rotation=90.0,
        )
        fs.text(
            cv,
            grid_x + grid_w / 2.0,
            bottom + steps * ch + 0.058,
            "被聚合位置 i",
            size=fs.MIN_FONT_PT,
            color=fs.INK,
        )

    upper_bottom = 0.545
    lower_bottom = 0.110
    draw_matrix(upper_bottom, causal=True)
    draw_matrix(lower_bottom, causal=False)

    fs.text(
        cv,
        0.050,
        upper_bottom + steps * ch + 0.104,
        "(a) 因果前缀掩码：仅 i ≤ t 参与",
        size=fs.MAIN_FONT_PT,
        color=fs.INK,        ha="left",
    )
    fs.text(
        cv,
        0.050,
        lower_bottom + steps * ch + 0.104,
        "(b) 非因果整窗聚合（对照）",
        size=fs.MAIN_FONT_PT,
        color=fs.INK,        ha="left",
    )
    fs.pill(
        cv,
        grid_x + grid_w - 0.052,
        upper_bottom - 0.042,
        0.108,
        0.050,
        "本章采用",
        face=fs.WHITE,
        edge=fs.M1_EDGE,
        color=fs.M1_EDGE,
    )
    fs.pill(
        cv,
        grid_x + grid_w - 0.044,
        lower_bottom - 0.042,
        0.124,
        0.050,
        "本章不采用",
        face=fs.WHITE,
        edge=fs.M2_EDGE,
        color=fs.M2_EDGE,
    )

    # --- 右栏：定义式、增量更新、与双向聚合的分界
    col_x = 0.435
    col_w = 0.552
    fs.box(
        cv,
        col_x,
        0.640,
        col_w,
        0.290,
        (
            Line("前缀聚合的定义", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
            Line(
                r"$\mathrm{ctx}_t=\dfrac{\sum_{i\leq t} h_i}{\sum_{i\leq t} m_i}$",
                fs.MAIN_FONT_PT,
                "math",
                fs.INK,
            ),
            Line("按前缀内有效流数归一化", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            Line("掩码标记补零位置，不参与计数", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        face=fs.M1_FACE,
        edge=fs.M1_EDGE,
        linewidth=1.4,
    )

    fs.box(cv, col_x, 0.330, col_w, 0.272, face=fs.WHITE, edge=fs.MUTED)
    fs.text(
        cv,
        col_x + 0.018,
        0.560,
        "增量更新：单步只需常数次向量运算",
        size=fs.MIN_FONT_PT,
        color=fs.INK,        ha="left",
    )
    node_w = 0.128
    node_h = 0.082
    node_y = 0.442
    fs.box(
        cv,
        col_x + 0.022,
        node_y,
        node_w,
        node_h,
        (Line(r"$\mathrm{ctx}_{t-1}$", fs.MIN_FONT_PT, "math", fs.INK),),
        edge=fs.RULE,
    )
    fs.box(
        cv,
        col_x + 0.212,
        node_y,
        node_w,
        node_h,
        (Line(r"$+\,h_t,\ +\,m_t$", fs.MIN_FONT_PT, "math", fs.INK),),
        edge=fs.M1_EDGE,
    )
    fs.box(
        cv,
        col_x + 0.402,
        node_y,
        node_w,
        node_h,
        (Line(r"$\mathrm{ctx}_t$", fs.MIN_FONT_PT, "math", fs.INK),),
        edge=fs.RULE,
    )
    fs.arrow(
        cv,
        (col_x + 0.022 + node_w + 0.006, node_y + node_h / 2.0),
        (col_x + 0.212 - 0.006, node_y + node_h / 2.0),
        head=6.0,
    )
    fs.arrow(
        cv,
        (col_x + 0.212 + node_w + 0.006, node_y + node_h / 2.0),
        (col_x + 0.402 - 0.006, node_y + node_h / 2.0),
        head=6.0,
    )
    fs.text(
        cv,
        col_x + 0.022,
        0.386,
        "无需重扫历史，单步计算量为",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )
    fs.text(
        cv,
        col_x + 0.418,
        0.386,
        r"$O(D)$",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )

    fs.box(
        cv,
        col_x,
        0.108,
        col_w,
        0.186,
        (
            Line("与双向整窗聚合的分界", fs.MAIN_FONT_PT, "cjk", fs.M2_EDGE),
            Line(
                "Vision-RWKV（ICLR 2025）式 (5) 对整窗双向归一化；",
                fs.MIN_FONT_PT,
                "cjk",
                fs.MUTED,
            ),
            Line(
                "本章限制为严格因果，位置 t 不可见任何 i > t。",
                fs.MIN_FONT_PT,
                "cjk",
                fs.MUTED,
            ),
        ),
        face=fs.M2_FACE,
        edge=fs.M2_EDGE,
        linewidth=fs.MAIN_LINE_PT,
        linestyle=(0, (4, 2)),
    )

    fs.footnote(cv, NO_DATA_NOTE, y=0.040)
    return cv


# ================================================================ 图3-4


def _power_mean(scores: np.ndarray, p: np.ndarray) -> np.ndarray:
    """广义幂平均 M_p，在对数域计算以避免大指数下的数值溢出。"""

    log_s = np.log(scores)[None, :]
    weighted = np.exp(p[:, None] * log_s).mean(axis=1)
    return np.exp(np.log(weighted) / p)


def draw_learnable_lp_pooling() -> Canvas:
    """实体级可学 Lp 池化：幂平均关于 p 的单调性与三个特例。"""

    cv = fs.canvas(140.0, 95.0)

    # 示意分数，仅用于画出单调曲线形状，与任何实验结果无关。
    scores = np.array([0.10, 0.25, 0.40, 0.85])
    geo = float(np.exp(np.log(scores).mean()))
    ari = float(scores.mean())
    top = float(scores.max())

    chip_w = 0.086
    chip_h = 0.078
    chip_y = 0.885
    for index, cx in enumerate((0.075, 0.175, 0.275, 0.375)):
        fs.box(
            cv,
            cx,
            chip_y,
            chip_w,
            chip_h,
            (Line(rf"$s_{index + 1}$", fs.MIN_FONT_PT, "math", fs.INK),),
            edge=fs.RULE,
        )
    fs.text(
        cv,
        0.075,
        0.838,
        "实体内逐流分数（示意取值）",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )
    fs.arrow(
        cv, (0.470, chip_y + chip_h / 2.0), (0.524, chip_y + chip_h / 2.0), head=6.0
    )
    fs.box(
        cv,
        0.530,
        chip_y - 0.014,
        0.245,
        chip_h + 0.028,
        (
            Line(
                r"$M_p(s)=\left(\frac{1}{n}\sum_f s_f^{\,p}\right)^{1/p}$",
                fs.MIN_FONT_PT,
                "math",
                fs.M2_EDGE,
            ),
        ),
        face=fs.M2_FACE,
        edge=fs.M2_EDGE,
        linewidth=1.4,
    )
    fs.arrow(
        cv, (0.781, chip_y + chip_h / 2.0), (0.835, chip_y + chip_h / 2.0), head=6.0
    )
    fs.box(
        cv,
        0.841,
        chip_y,
        0.118,
        chip_h,
        (Line(r"$S_e$", fs.MIN_FONT_PT, "math", fs.INK),),
        edge=fs.M2_EDGE,
    )

    ax = cv.fig.add_axes((0.115, 0.175, 0.845, 0.570))
    p = np.geomspace(0.04, 120.0, 900)
    ax.plot(p, _power_mean(scores, p), color=fs.M2_EDGE, linewidth=1.6, zorder=6)
    ax.axhline(geo, color=fs.INK, linewidth=0.8, linestyle=(0, (1, 2)), zorder=4)
    ax.axhline(top, color=fs.INK, linewidth=0.8, linestyle=(0, (5, 3)), zorder=4)
    ax.axvline(1.0, color=fs.RULE, linewidth=0.8, linestyle=(0, (4, 2, 1, 2)), zorder=3)
    ax.plot(
        [1.0],
        [ari],
        marker="o",
        markersize=4.5,
        markerfacecolor=fs.WHITE,
        markeredgecolor=fs.INK,
        markeredgewidth=1.0,
        zorder=7,
    )

    ax.set_xscale("log")
    ax.set_xlim(0.04, 120.0)
    ax.set_ylim(geo - 0.10, top + 0.10)
    ax.set_xticks([0.1, 1.0, 10.0, 100.0])
    ax.set_xticklabels(["0.1", "1", "10", "100"])
    ax.set_yticks([])
    ax.set_xlabel(
        fs.checked("池化指数 p（对数刻度）", fs.MAIN_FONT_PT),
        fontsize=fs.MAIN_FONT_PT,
        color=fs.INK,
    )
    ax.set_ylabel(
        fs.checked("实体级聚合分数（示意）", fs.MAIN_FONT_PT),
        fontsize=fs.MAIN_FONT_PT,
        color=fs.INK,
    )
    ax.tick_params(axis="x", labelsize=fs.MIN_FONT_PT, colors=fs.MUTED)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(fs.RULE)

    marks = (
        ("几何平均", r"$p\to 0$", 0.050, geo, "left", 0.022, -0.058),
        ("算术平均", r"$p=1$", 1.30, ari, "left", -0.052, -0.112),
        ("上界 max", r"$p\to\infty$", 108.0, top, "right", 0.030, -0.062),
    )
    for cn_label, math_label, x, y, ha, dy_cn, dy_math in marks:
        ax.annotate(
            fs.checked(cn_label),
            xy=(x, y + dy_cn),
            fontsize=fs.MIN_FONT_PT,
            color=fs.INK,
            ha=ha,
            va="center",
        )
        ax.annotate(
            fs.checked(math_label),
            xy=(x, y + dy_math),
            fontsize=fs.MIN_FONT_PT,
            color=fs.MUTED,
            ha=ha,
            va="center",
        )
    ax.annotate(
        fs.checked("单调不减"),
        xy=(6.0, 0.5 * (ari + top)),
        xytext=(2.6, geo - 0.045),
        fontsize=fs.MIN_FONT_PT,
        color=fs.M2_EDGE,
        ha="left",
        arrowprops={
            "arrowstyle": "-|>",
            "color": fs.M2_EDGE,
            "linewidth": 0.8,
            "shrinkA": 2.0,
            "shrinkB": 2.0,
        },
    )

    fs.box(
        cv,
        0.556,
        0.212,
        0.396,
        0.152,
        (
            Line("指数的参数化与学习", fs.MIN_FONT_PT, "cjk", fs.M2_EDGE),
            Line(
                r"$p=\exp(p_{\log}),\quad p\in(0,\infty)$",
                fs.MIN_FONT_PT,
                "math",
                fs.INK,
            ),
            Line("由序列级辅助损失驱动学习", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        face=fs.WHITE,
        edge=fs.M2_EDGE,
        linewidth=fs.MAIN_LINE_PT,
    )

    fs.footnote(
        cv,
        "曲线由示意分数 0.10 / 0.25 / 0.40 / 0.85 生成，纵轴无实验数值。",
        y=0.038,
    )
    return cv


# ================================================================ 入口


SPECS = (
    FigureSpec(
        "图3-1-整体方法框架",
        150.0,
        95.0,
        draw_overall_framework,
        "逐流特征到实体级告警的整体流程；表示层机制一与决策层机制二分别以斜线、反斜线填充标出。",
    ),
    FigureSpec(
        "图3-2-二IP无向对序列构造",
        150.0,
        80.0,
        draw_entity_key_sequence,
        "双向流经无向对键归并到同一实体，键内按时间升序后切成长度 L 的非重叠块，尾块补零并以掩码标记。",
    ),
    FigureSpec(
        "图3-3-因果前缀跨流聚合",
        140.0,
        95.0,
        draw_causal_prefix_aggregation,
        "下三角因果掩码与非因果整窗聚合的对照，以及前缀聚合的常数代价增量更新。",
    ),
    FigureSpec(
        "图3-4-实体级可学Lp池化",
        140.0,
        95.0,
        draw_learnable_lp_pooling,
        "广义幂平均关于池化指数的单调曲线，标出几何平均、算术平均与上界三个特例。",
    ),
)


def main() -> None:
    entries = [fs.save_figure(ROOT, spec, spec.draw()) for spec in SPECS]
    report = fs.verify_outputs(ROOT, entries)
    manifest = fs.write_manifest(
        ROOT,
        Path(__file__).name,
        entries,
        evidence_mode=EVIDENCE_MODE,
    )
    print(
        f"中文字体：{fs.CJK_FONT.family}"
        f"（{fs.CJK_FONT.path}，face {fs.CJK_FONT.face_index}）"
    )
    print(f"西文字体：{fs.LATIN_FONT.family}（{fs.LATIN_FONT.path}）")
    for line in report:
        print(line)
    print(f"图件清单：{manifest}")


if __name__ == "__main__":
    main()
