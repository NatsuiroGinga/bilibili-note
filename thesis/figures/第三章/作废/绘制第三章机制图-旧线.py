"""生成第三章四张方法机制示意图（图3-1 ~ 图3-4）。

本脚本不读取任何实验结果、日志或运行制品，图中一切数值均为方法规格常量或示意取值，
对应图件清单中的 `evidence_mode = method_schematic_without_experimental_results`。

机制内容的唯一权威来源是
`.Codex/docs/RWKV/2026-08-31-CEM-BER机制形式化与复杂度规约.md`；
图中不出现四格读数、增量、有效性判断或任何机制优劣表述——四格未齐（C11 缺），
机制有效性一律未裁决。

生成命令：
    uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章机制图.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import figstyle as fs
from figstyle import Canvas, FigureSpec, Line

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "图件清单.json"
GENERATOR = "绘制第三章机制图.py"
RESULT_GENERATOR = "绘制第三章结果图.py"
UPDATED_AT = "2026-08-31"

EVIDENCE_MODE = "method_schematic_without_experimental_results"
NO_DATA_NOTE = "本图为方法机制示意，不含任何实验结果数值。"

# 记忆槽数、宽度、Token 数与预算网格都是已冻结的方法规格常量，不是实验读数。
SLOTS = 8
WIDTH = 192
TOKEN_COUNT = 84
SEQUENCE_LENGTH = 128
BUDGET_RATIOS = ("0.1%", "0.5%", "1%", "2%", "4%", "8%")
BUDGET_VALUES = ("121", "606", "1213", "2426", "4853", "9706")

# 均值槽用点阵图案、队列槽用斜线图案，二者与决策层的反斜线图案在灰度下互不混淆。
MEAN_HATCH = "..."


# ================================================================ 图3-1


def draw_overall_framework() -> Canvas:
    """整体方法框架：CEM-BER 两机制流水线与八步在线算法顺序。"""

    cv = fs.canvas(150.0, 115.0)

    left = 0.088
    right = 0.992
    span = right - left
    channel_x = 0.079

    # 带标签竖排。单行 7 字在最矮的一带里放不下（实测溢出带框），故拆成两行；
    # 旋转 90° 后两行沿横向并列，行距压到 1.15 才不超出 0.052 的带框宽度。
    band = {
        "input": (0.795, 0.175, "输入与\n序列构造", fs.MUTED),
        "repr": (0.395, 0.355, "表示层\n计算侧", fs.M1_EDGE),
        "decide": (0.150, 0.190, "决策层\n汇聚侧", fs.M2_EDGE),
    }
    for y0, height, label, color in band.values():
        fs.box(
            cv,
            0.018,
            y0,
            0.052,
            height,
            face=fs.SHADE,
            edge=fs.HAIRLINE,
            linewidth=0.7,
            radius=0.010,
            zorder=2,
        )
        fs.text(
            cv,
            0.044,
            y0 + height / 2.0,
            label,
            size=fs.MIN_FONT_PT,
            color=color,
            rotation=90.0,
            linespacing=1.15,
        )

    def row(count: int, gap: float) -> tuple[float, list[float]]:
        width = (span - gap * (count - 1)) / count
        centers = [left + width / 2.0 + i * (width + gap) for i in range(count)]
        return width, centers

    # --- 第一带：输入与序列构造
    w_in, c_in = row(4, 0.032)
    y_in = band["input"][0]
    h_in = band["input"][1]
    input_boxes = (
        (
            Line("原始流记录", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line("83 个合法字段", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            Line("各成一个 Token", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        (
            Line("按 2-IP 无向对分组", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line(r"$e=\chi(a,b)$", fs.MIN_FONT_PT, "math", fs.MUTED, span=1.55),
        ),
        (
            Line("组内按时间升序", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line(r"$t_1<t_2<\cdots<t_n$", fs.MIN_FONT_PT, "math", fs.MUTED, span=1.55),
        ),
        (
            Line("切分非重叠片段", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line("尾部补零并掩码", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            Line(rf"$L={SEQUENCE_LENGTH}$", fs.MIN_FONT_PT, "math", fs.MUTED, span=1.55),
        ),
    )
    for cx, lines in zip(c_in, input_boxes, strict=True):
        fs.box(cv, cx - w_in / 2.0, y_in, w_in, h_in, lines)
    cy_in = y_in + h_in / 2.0
    for a, b in zip(c_in, c_in[1:], strict=False):
        fs.arrow(cv, (a + w_in / 2.0 + 0.004, cy_in), (b - w_in / 2.0 - 0.004, cy_in))

    # --- 第二带：表示层（记忆库在上，逐流通路在下）
    bank_x, bank_w = 0.188, 0.700
    bank_y, bank_h = 0.640, 0.100
    fs.box(
        cv,
        bank_x,
        bank_y,
        bank_w,
        bank_h,
        (
            Line("因果实体记忆（机制一）", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
            Line(
                f"每实体 {SLOTS} 个记忆槽，只保存该实体在片段 t 之前的写入",
                fs.MIN_FONT_PT,
                "cjk",
                fs.MUTED,
            ),
        ),
        face=fs.M1_FACE,
        edge=fs.M1_EDGE,
        linewidth=1.4,
        hatch=fs.M1_HATCH,
        hatch_color=fs.HAIRLINE,
    )

    w_rp, c_rp = row(3, 0.040)
    y_rp, h_rp = 0.415, 0.145
    repr_boxes = (
        (
            (
                Line("② 骨干前向", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line("FT-Transformer", fs.MIN_FONT_PT, "cjk", fs.MUTED),
                Line(
                    rf"${TOKEN_COUNT}$ Token, $d={WIDTH}$",
                    fs.MIN_FONT_PT,
                    "math",
                    fs.MUTED,
                    span=1.55,
                ),
            ),
            False,
        ),
        (
            (
                Line("③ 交叉注意力门控注入", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
                Line(r"$h'=h+g\cdot c$", fs.MIN_FONT_PT, "math", fs.INK, span=1.55),
                Line("无历史时上下文置零", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
            True,
        ),
        (
            (
                Line("④ 出分", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line("逐流 logit", fs.MIN_FONT_PT, "cjk", fs.MUTED),
                Line(r"$l_{e,t}$", fs.MIN_FONT_PT, "math", fs.MUTED, span=1.55),
            ),
            False,
        ),
    )
    for cx, (lines, highlight) in zip(c_rp, repr_boxes, strict=True):
        fs.box(
            cv,
            cx - w_rp / 2.0,
            y_rp,
            w_rp,
            h_rp,
            lines,
            face=fs.M1_FACE if highlight else fs.WHITE,
            edge=fs.M1_EDGE if highlight else fs.MUTED,
            linewidth=1.4 if highlight else fs.MAIN_LINE_PT,
            hatch=fs.M1_HATCH if highlight else None,
            hatch_color=fs.HAIRLINE,
        )
    cy_rp = y_rp + h_rp / 2.0
    for a, b in zip(c_rp, c_rp[1:], strict=False):
        fs.arrow(cv, (a + w_rp / 2.0 + 0.004, cy_rp), (b - w_rp / 2.0 - 0.004, cy_rp))

    # 读在前：记忆库向注入盒的实线箭头；写在后：出分盒向记忆库的虚线箭头。
    read_x = 0.470
    write_x = 0.815
    fs.arrow(cv, (read_x, bank_y - 0.004), (read_x, y_rp + h_rp + 0.004), color=fs.M1_EDGE)
    fs.text(
        cv,
        read_x + 0.014,
        0.600,
        "① 读\n仅含 t 之前的片段",
        size=fs.MIN_FONT_PT,
        color=fs.M1_EDGE,
        ha="left",
    )
    fs.arrow(
        cv,
        (write_x, y_rp + h_rp + 0.004),
        (write_x, bank_y - 0.004),
        color=fs.M1_EDGE,
        linestyle=(0, (4, 2)),
    )
    fs.text(
        cv,
        write_x - 0.014,
        0.600,
        "⑧ 写\n出分之后",
        size=fs.MIN_FONT_PT,
        color=fs.M1_EDGE,
        ha="right",
    )

    # --- 第三带：决策层
    w_de, c_de = row(3, 0.045)
    y_de, h_de = band["decide"][0], band["decide"][1]
    decide_boxes = (
        (
            (
                Line("⑤ 实体路径分数", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line(r"$S_e=\max_t\,l_{e,t}$", fs.MIN_FONT_PT, "math", fs.MUTED, span=1.8),
            ),
            False,
        ),
        (
            (
                Line("⑥ 预算感知实体排序（机制二）", fs.MIN_FONT_PT, "cjk", fs.M2_EDGE),
                Line("多预算 CVaR-pAUC 训练目标", fs.MIN_FONT_PT, "cjk", fs.INK),
                Line(r"$L_{\mathrm{rank}}=\mathrm{mean}_K R_K$", fs.MIN_FONT_PT, "math", fs.MUTED, span=1.7),
            ),
            True,
        ),
        (
            (
                Line("⑦ 参数更新与实体级告警", fs.MIN_FONT_PT, "cjk", fs.INK),
                Line("按实体路径分数在预算内排序输出", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
            False,
        ),
    )
    for cx, (lines, highlight) in zip(c_de, decide_boxes, strict=True):
        fs.box(
            cv,
            cx - w_de / 2.0,
            y_de,
            w_de,
            h_de,
            lines,
            face=fs.M2_FACE if highlight else fs.WHITE,
            edge=fs.M2_EDGE if highlight else fs.MUTED,
            linewidth=1.4 if highlight else fs.MAIN_LINE_PT,
            hatch=fs.M2_HATCH if highlight else None,
            hatch_color=fs.HAIRLINE,
        )
    cy_de = y_de + h_de / 2.0
    for a, b in zip(c_de, c_de[1:], strict=False):
        fs.arrow(cv, (a + w_de / 2.0 + 0.004, cy_de), (b - w_de / 2.0 - 0.004, cy_de))

    # --- 跨带换行走线
    fs.routed_arrow(
        cv,
        [
            (c_in[-1], y_in),
            (c_in[-1], 0.7725),
            (channel_x, 0.7725),
            (channel_x, cy_rp),
            (c_rp[0] - w_rp / 2.0 - 0.004, cy_rp),
        ],
        color=fs.RULE,
    )
    fs.routed_arrow(
        cv,
        [
            (c_rp[-1], y_rp),
            (c_rp[-1], 0.3775),
            (channel_x, 0.3775),
            (channel_x, cy_de),
            (c_de[0] - w_de / 2.0 - 0.004, cy_de),
        ],
        color=fs.RULE,
    )

    fs.text(
        cv,
        0.5,
        0.108,
        "在线单步顺序：① 读记忆 → ② 骨干前向 → ③ 注入 → ④ 出分",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
    )
    fs.text(
        cv,
        0.5,
        0.078,
        "→ ⑤ 实体路径分数 → ⑥ 排序目标 → ⑦ 更新参数 → ⑧ 写记忆（故片段 t 只可见 t 之前）",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
    )
    fs.footnote(cv, NO_DATA_NOTE, y=0.038)
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

    # --- (c) 同键内按时间升序，再切成非重叠片段
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
        "切成长度 L 的非重叠片段",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )
    grid_x = 0.660
    grid_w = 0.316
    cw = grid_w / 8.0
    ch = cv.square_dy(cw)
    # 片段块下移，给「切成长度 L 的非重叠片段」与两个片段标注留出不重叠的净空。
    grid_y = 0.308
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
        "片段 1",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
    )
    fs.text(
        cv,
        grid_x + 6 * cw,
        grid_y + ch + 0.052,
        "片段 2（尾部补零）",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )
    # 掩码行改由下方文字说明。原来放在格阵左侧的「掩码」二字会越出 (c) 面板左边界、
    # 压到 (b) 面板上，是旧稿遗留的版面缺陷。
    fs.text(
        cv,
        0.818,
        0.200,
        "格下的 0 / 1 为有效掩码",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )
    fs.text(
        cv,
        0.818,
        0.163,
        f"正文取 L = {SEQUENCE_LENGTH}，图中缩略为 4",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )

    fs.footnote(cv, NO_DATA_NOTE, y=0.048)
    return cv


# ================================================================ 图3-3


def draw_causal_entity_memory() -> Canvas:
    """因果实体记忆：读写时序、槽位语义、单向查询与门控注入。"""

    cv = fs.canvas(150.0, 132.0)

    fs.panel(cv, 0.010, 0.630, 0.980, 0.350, "(a) 严格过去记忆的读写时序")
    fs.panel(cv, 0.010, 0.300, 0.470, 0.305, "(b) 记忆槽语义与有效掩码")
    fs.panel(cv, 0.520, 0.300, 0.470, 0.305, "(c) 单向查询与门控残差注入")
    fs.panel(cv, 0.010, 0.085, 0.980, 0.190, "(d) 零门退化与状态隔离")

    # ---------------- (a) 读写时序
    seg_y, seg_h, seg_w = 0.845, 0.075, 0.155
    segments = (
        (0.14, r"$t-2$", False),
        (0.34, r"$t-1$", False),
        (0.58, r"$t$", True),
        (0.82, r"$t+1$", False),
    )
    for cx, tag, current in segments:
        future = tag == r"$t+1$"
        fs.box(
            cv,
            cx - seg_w / 2.0,
            seg_y,
            seg_w,
            seg_h,
            (
                Line("片段", fs.MIN_FONT_PT, "cjk", fs.MUTED if future else fs.INK),
                Line(tag, fs.MAIN_FONT_PT, "math", fs.MUTED if future else fs.INK, span=1.55),
            ),
            face=fs.M1_FACE if current else fs.WHITE,
            edge=fs.M1_EDGE if current else (fs.HAIRLINE if future else fs.MUTED),
            linewidth=1.4 if current else fs.MAIN_LINE_PT,
            linestyle=(0, (3, 2)) if future else "-",
        )
    fs.text(cv, 0.82, 0.822, "尚未发生", size=fs.MIN_FONT_PT, color=fs.MUTED)
    fs.text(cv, 0.58, 0.822, "当前片段", size=fs.MIN_FONT_PT, color=fs.M1_EDGE)

    bank_x, bank_w, bank_y, bank_h = 0.075, 0.370, 0.712, 0.082
    fs.box(
        cv,
        bank_x,
        bank_y,
        bank_w,
        bank_h,
        (
            Line("因果实体记忆", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
            Line(rf"$M_e\in R^{{{SLOTS}\times{WIDTH}}}$", fs.MIN_FONT_PT, "math", fs.INK, span=1.55),
        ),
        face=fs.M1_FACE,
        edge=fs.M1_EDGE,
        linewidth=1.4,
        hatch=fs.M1_HATCH,
        hatch_color=fs.HAIRLINE,
    )

    for cx in (0.14, 0.34):
        fs.arrow(
            cv,
            (cx, seg_y - 0.004),
            (cx, bank_y + bank_h + 0.004),
            color=fs.M1_EDGE,
            linestyle=(0, (4, 2)),
            head=6.0,
        )
    fs.text(cv, 0.24, 0.826, "前序片段的写入", size=fs.MIN_FONT_PT, color=fs.MUTED)

    fs.routed_arrow(
        cv,
        [
            (bank_x + bank_w + 0.004, bank_y + bank_h / 2.0),
            (0.520, bank_y + bank_h / 2.0),
            (0.520, seg_y - 0.004),
        ],
        color=fs.M1_EDGE,
    )
    fs.text(cv, 0.462, 0.775, "① 读", size=fs.MIN_FONT_PT, color=fs.M1_EDGE, ha="left")

    fs.routed_arrow(
        cv,
        [
            (0.640, seg_y - 0.004),
            (0.640, 0.678),
            (0.300, 0.678),
            (0.300, bank_y - 0.004),
        ],
        color=fs.M1_EDGE,
        linestyle=(0, (4, 2)),
    )
    fs.text(
        cv,
        0.656,
        0.690,
        "⑧ 写：出分之后",
        size=fs.MIN_FONT_PT,
        color=fs.M1_EDGE,
        ha="left",
    )
    fs.text(
        cv,
        0.656,
        0.660,
        "故本次读取不含片段 t 自身",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )

    # ---------------- (b) 记忆槽语义
    fs.text(
        cv,
        0.022,
        0.545,
        "槽 0：跨片段 Welford 在线均值",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )
    fs.text(
        cv,
        0.022,
        0.518,
        f"槽 1 至 {SLOTS - 1}：最近表示的有界队列，右侧最新",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )
    slot_x, slot_w = 0.060, 0.046
    slot_h = cv.square_dy(slot_w)
    slot_y = 0.428
    filled = 3
    for index in range(SLOTS):
        is_mean = index == 0
        valid = is_mean or index >= SLOTS - filled
        fs.cell(
            cv,
            slot_x + index * slot_w,
            slot_y,
            slot_w,
            slot_h,
            face=fs.SHADE if is_mean else (fs.M1_FACE if valid else fs.WHITE),
            edge=fs.MUTED if is_mean else (fs.M1_EDGE if valid else fs.HAIRLINE),
            linewidth=0.7,
            hatch=MEAN_HATCH if is_mean else (fs.M1_HATCH if valid else None),
        )
        fs.text(
            cv,
            slot_x + (index + 0.5) * slot_w,
            slot_y - 0.026,
            str(index),
            size=fs.MIN_FONT_PT,
            color=fs.MUTED,
        )
        fs.text(
            cv,
            slot_x + (index + 0.5) * slot_w,
            slot_y - 0.058,
            "1" if valid else "0",
            size=fs.MIN_FONT_PT,
            color=fs.INK if valid else fs.MUTED,
        )
    fs.text(cv, slot_x - 0.006, slot_y - 0.026, "槽", size=fs.MIN_FONT_PT, color=fs.MUTED, ha="right")
    fs.text(cv, slot_x - 0.006, slot_y - 0.056, "掩码", size=fs.MIN_FONT_PT, color=fs.MUTED, ha="right")
    fs.text(
        cv,
        0.022,
        0.330,
        f"图中示意队列已写入 {filled} 条，未写满的位置置无效",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )

    # ---------------- (c) 单向查询与门控
    # 本图四个面板全属机制一，没有需要靠填充图案区分的第二类对象，故此处不加图案，
    # 把可读性留给公式；灰度下的机制归属由面板标题与深色描边给出。
    fs.box(
        cv,
        0.532,
        0.312,
        0.446,
        0.240,
        (
            Line("当前表示只查询记忆，记忆不反查当前", fs.MIN_FONT_PT, "cjk", fs.M1_EDGE),
            Line(r"$q=W_Q\,\mathrm{LN}(h)$", fs.MIN_FONT_PT, "math", fs.INK, span=1.55),
            Line(
                r"$K,V=W_K,W_V\,(\mathrm{LN}(M_e)+P_R)$",
                fs.MIN_FONT_PT,
                "math",
                fs.INK,
                span=1.55,
            ),
            Line(r"$c=W_o\,\mathrm{Attn}(q,K,V)$", fs.MIN_FONT_PT, "math", fs.INK, span=1.55),
            Line(r"$g=\sigma(W_g[h;c]+b)$", fs.MIN_FONT_PT, "math", fs.INK, span=1.55),
            Line(r"$h'=h+g\cdot c$", fs.MAIN_FONT_PT, "math", fs.M1_EDGE, span=1.7),
            Line("8 头，每头 24 维；角色嵌入区分两类槽", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        face=fs.M1_FACE,
        edge=fs.M1_EDGE,
        linewidth=1.4,
    )

    # ---------------- (d) 零门退化与状态隔离
    fs.box(
        cv,
        0.022,
        0.098,
        0.470,
        0.115,
        (
            Line("零门退化", fs.MIN_FONT_PT, "cjk", fs.M1_EDGE),
            Line(r"$c=0,\quad h'=h$", fs.MAIN_FONT_PT, "math", fs.INK, span=1.55),
            Line("无严格过去可读时上下文直接置零，不做全掩码归一", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        edge=fs.MUTED,
    )
    fs.box(
        cv,
        0.512,
        0.098,
        0.470,
        0.115,
        (
            Line("状态隔离", fs.MIN_FONT_PT, "cjk", fs.M1_EDGE),
            Line("每轮评价前按数据角色重置，链首片段先清零", fs.MIN_FONT_PT, "cjk", fs.INK),
            Line("目标年评价的记忆从零开始重新累积", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        edge=fs.MUTED,
    )

    fs.footnote(cv, NO_DATA_NOTE, y=0.032)
    return cv


# ================================================================ 图3-4


def draw_budget_aware_ranking() -> Canvas:
    """预算感知实体排序：路径分数、CVaR 尾部、多预算折算与推理边界。"""

    cv = fs.canvas(150.0, 128.0)

    fs.panel(cv, 0.010, 0.600, 0.470, 0.375, "(a) 实体路径分数")
    fs.panel(cv, 0.520, 0.600, 0.470, 0.375, "(b) 成对损失与 CVaR 尾部")
    fs.panel(cv, 0.010, 0.300, 0.470, 0.275, "(c) 冻结预算网格与有效预算折算")
    fs.panel(cv, 0.520, 0.300, 0.470, 0.275, "(d) 训练私有阈值与推理边界")

    # ---------------- (a) 逐流 logit 取最大
    cell_x, cell_w = 0.085, 0.036
    cell_h = cv.square_dy(cell_w)
    rows = ((0.855, 5), (0.800, 2), (0.745, 6))
    for row_index, (row_y, peak) in enumerate(rows):
        fs.text(
            cv,
            cell_x - 0.008,
            row_y + cell_h / 2.0,
            rf"$t={row_index + 1}$",
            size=fs.MIN_FONT_PT,
            color=fs.MUTED,
            ha="right",
        )
        for index in range(8):
            hit = index == peak
            fs.cell(
                cv,
                cell_x + index * cell_w,
                row_y,
                cell_w,
                cell_h,
                face=fs.M2_FACE if hit else fs.WHITE,
                edge=fs.M2_EDGE if hit else fs.RULE,
                linewidth=1.0 if hit else 0.5,
                hatch=fs.M2_HATCH if hit else None,
            )
    grid_right = cell_x + 8 * cell_w
    brace_x = grid_right + 0.012
    top_y = rows[0][0] + cell_h
    bottom_y = rows[-1][0]
    mid_y = (top_y + bottom_y) / 2.0
    fs.polyline(
        cv,
        [
            (brace_x - 0.008, top_y),
            (brace_x, top_y),
            (brace_x, bottom_y),
            (brace_x - 0.008, bottom_y),
        ],
        color=fs.MUTED,
        linewidth=0.8,
    )
    fs.arrow(cv, (brace_x, mid_y), (brace_x + 0.024, mid_y), head=6.0)
    fs.box(
        cv,
        brace_x + 0.028,
        mid_y - 0.030,
        0.062,
        0.060,
        (Line(r"$S_e$", fs.MAIN_FONT_PT, "math", fs.M2_EDGE),),
        face=fs.M2_FACE,
        edge=fs.M2_EDGE,
        linewidth=1.4,
    )
    fs.text(
        cv,
        0.022,
        0.700,
        "每格为一条流的 logit，深色格为该片段最大值",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )
    fs.text(cv, 0.245, 0.662, r"$S_e=\max_t\,l_{e,t}$", size=fs.MAIN_FONT_PT, color=fs.INK)
    fs.text(
        cv,
        0.022,
        0.624,
        "梯度只回到取得最大 logit 的那一条流",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )

    # ---------------- (b) 排序后的成对损失与 CVaR 尾部
    bar_values = (1.00, 0.88, 0.76, 0.66, 0.55, 0.46, 0.37, 0.28, 0.19, 0.10)
    base_y, bar_span = 0.715, 0.170
    bar_x, bar_w, pitch = 0.585, 0.030, 0.038
    threshold = 0.50
    xi_y = base_y + threshold * bar_span
    for index, value in enumerate(bar_values):
        x = bar_x + index * pitch
        low = min(value, threshold) * bar_span
        fs.cell(cv, x, base_y, bar_w, low, face=fs.SHADE, edge=fs.RULE, linewidth=0.5)
        if value > threshold:
            fs.cell(
                cv,
                x,
                xi_y,
                bar_w,
                (value - threshold) * bar_span,
                face=fs.M2_FACE,
                edge=fs.M2_EDGE,
                linewidth=0.8,
                hatch=fs.M2_HATCH,
            )
    fs.polyline(
        cv,
        [(0.570, xi_y), (0.975, xi_y)],
        color=fs.INK,
        linewidth=0.8,
        linestyle=(0, (4, 2)),
    )
    fs.text(cv, 0.566, xi_y, r"$\xi$", size=fs.MAIN_FONT_PT, color=fs.INK, ha="right")
    fs.polyline(cv, [(0.578, base_y), (0.975, base_y)], color=fs.RULE, linewidth=0.7)
    fs.text(
        cv,
        0.775,
        0.688,
        "负实体（按成对损失降序）",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )
    fs.text(
        cv,
        0.755,
        0.652,
        r"$L_{pn}=\mathrm{softplus}(S_n-S_p)$",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
    )
    fs.text(
        cv,
        0.532,
        0.620,
        "只有越过阈值的困难负实体进入排序梯度",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )

    # ---------------- (c) 冻结预算网格
    grid_x, grid_cw = 0.024, 0.074
    for index, (ratio, value) in enumerate(zip(BUDGET_RATIOS, BUDGET_VALUES, strict=True)):
        x = grid_x + index * grid_cw
        fs.cell(cv, x, 0.462, grid_cw, 0.042, face=fs.SHADE, edge=fs.RULE, linewidth=0.5)
        fs.text(cv, x + grid_cw / 2.0, 0.483, ratio, size=fs.MIN_FONT_PT, color=fs.INK)
        fs.cell(cv, x, 0.418, grid_cw, 0.042, face=fs.M2_FACE, edge=fs.M2_EDGE, linewidth=0.8)
        fs.text(cv, x + grid_cw / 2.0, 0.439, value, size=fs.MIN_FONT_PT, color=fs.INK)
    fs.text(
        cv,
        0.024,
        0.386,
        "上行为名义误报预算比例，下行为冻结预算",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )
    fs.text(
        cv,
        0.024,
        0.356,
        "由训练角色负实体池按名义比例投影得到",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        ha="left",
    )
    fs.text(
        cv,
        0.245,
        0.322,
        r"$K_{\mathrm{eff}}=K\,n_{\mathrm{sampled}}/N_{-}$",
        size=fs.MAIN_FONT_PT,
        color=fs.INK,
    )

    # ---------------- (d) 训练私有阈值
    fs.box(
        cv,
        0.545,
        0.415,
        0.190,
        0.090,
        (
            Line("训练计算图", fs.MIN_FONT_PT, "cjk", fs.M2_EDGE),
            Line(r"$\theta,\ \xi_{p,K}$", fs.MAIN_FONT_PT, "math", fs.INK, span=1.55),
        ),
        face=fs.M2_FACE,
        edge=fs.M2_EDGE,
        linewidth=1.4,
        hatch=fs.M2_HATCH,
        hatch_color=fs.HAIRLINE,
    )
    fs.box(
        cv,
        0.775,
        0.415,
        0.190,
        0.090,
        (
            Line("推理计算图", fs.MIN_FONT_PT, "cjk", fs.INK),
            Line(r"$\theta$", fs.MAIN_FONT_PT, "math", fs.INK, span=1.55),
        ),
        edge=fs.MUTED,
    )
    fs.arrow(cv, (0.739, 0.460), (0.771, 0.460), head=6.0)
    fs.text(
        cv,
        0.755,
        0.386,
        "每个正实体在每档预算上各有一个阈值",
        size=fs.MIN_FONT_PT,
        color=fs.INK,
    )
    fs.text(
        cv,
        0.755,
        0.356,
        "阈值只在损失侧参与反向传播",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )
    fs.text(
        cv,
        0.755,
        0.322,
        "不进入推理图，推理期结构与裸主干相同",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )

    # ---------------- 目标式
    # 本框只承载公式，去掉填充图案以免斜线压住上下标；机制归属由描边与浅底给出，
    # 灰度下与图内其余中性框仍可区分。
    fs.box(
        cv,
        0.010,
        0.090,
        0.980,
        0.180,
        (
            Line("多预算 CVaR-pAUC 训练目标", fs.MAIN_FONT_PT, "cjk", fs.M2_EDGE),
            Line(
                r"$R_K(\theta,\xi)=\mathrm{mean}_p\,[\,\xi_{p,K}"
                r"+\frac{1}{K}\sum_n\,(L_{pn}-\xi_{p,K})_+\,]$,"
                r"$\quad L_{\mathrm{rank}}=\mathrm{mean}_K\,R_K(\theta,\xi)$",
                fs.MAIN_FONT_PT,
                "math",
                fs.INK,
                span=2.4,
            ),
            Line(
                "p 遍历正实体，n 遍历负实体，K 遍历六档预算",
                fs.MIN_FONT_PT,
                "cjk",
                fs.MUTED,
            ),
        ),
        face=fs.M2_FACE,
        edge=fs.M2_EDGE,
        linewidth=1.4,
    )

    fs.footnote(
        cv,
        "本图为方法机制示意；(a) 的格值与 (b) 的柱高为示意取值，不含任何实验结果数值。",
        y=0.036,
    )
    return cv


# ================================================================ 图件清单


CAPTIONS: dict[str, str] = {
    "图3-1-整体方法框架": (
        "图3-1　CEM-BER 的整体方法框架：逐流片段经因果实体记忆读入严格过去表示、"
        "门控注入后出分，实体路径分数在决策层进入多预算排序目标；"
        "表示层机制与决策层机制分别以斜线、反斜线填充标出，"
        "圈码为在线单步的八步顺序，写记忆在出分之后"
    ),
    "图3-2-二IP无向对序列构造": (
        "图3-2　二 IP 无向对序列构造：双向流经无向对键归并到同一实体，"
        "键内按时间升序后切成长度 L 的非重叠片段，尾部补零并以掩码标记"
    ),
    "图3-3-因果实体记忆的读写与交叉注意力": (
        "图3-3　因果实体记忆的读写与交叉注意力：记忆只保存当前片段之前的写入，"
        "槽 0 为跨片段在线均值、槽 1 至 7 为最近表示的有界队列，"
        "当前表示单向查询记忆并以标量门控残差注入，无严格过去可读时上下文置零"
    ),
    "图3-4-预算感知实体排序的目标构造": (
        "图3-4　预算感知实体排序的目标构造：实体路径分数取该实体全部片段逐流 logit 的最大值，"
        "成对损失中只有越过阈值的困难负实体进入 CVaR 尾部，"
        "六档冻结预算按抽样规模折算为有效预算；阈值是训练私有状态，不进入推理图"
    ),
}

WITHDRAWN: tuple[dict[str, Any], ...] = (
    {
        "stem": "图3-3-因果前缀跨流聚合",
        "withdrawn_at": UPDATED_AT,
        "reason": (
            "旧图描述的因果前缀跨流聚合（CPA）已不是第三章的当前机制；"
            "第三章重锚到 CEM-BER 后，表示层机制改为因果实体记忆的读写与交叉注意力。"
        ),
        "recovery": "若正文重新采用因果前缀聚合，须先恢复对应机制合同再重绘。",
        "files_moved_to": "作废/",
    },
    {
        "stem": "图3-4-实体级可学Lp池化",
        "withdrawn_at": UPDATED_AT,
        "reason": (
            "旧图描述的实体级可学幂平均池化（ELP）已不是第三章的当前机制；"
            "第三章重锚到 CEM-BER 后，决策层机制改为预算感知实体排序的训练目标。"
        ),
        "recovery": "若正文重新采用可学幂平均池化，须先恢复对应机制合同再重绘。",
        "files_moved_to": "作废/",
    },
)


def build_manifest(entries: list[dict[str, Any]]) -> None:
    """重写图件清单：替换机制图分段与条目，原样保留结果图分段与条目。

    结果图条目含数据来源键路径，只有 `绘制第三章结果图.py` 能重新测量与登记，
    故本脚本不重建它们，只在机制图重锚时同步 `withdrawn` 段与本脚本的分段登记。
    """

    import matplotlib
    import PIL

    previous: dict[str, Any] = {}
    if MANIFEST_PATH.exists():
        previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    kept: list[dict[str, Any]] = []
    for item in previous.get("figures", []):
        if item.get("generator") == GENERATOR:
            continue
        outputs = item.get("outputs", {})
        if outputs and all((ROOT / name).exists() for name in outputs.values()):
            kept.append(item)

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
        "matplotlib": matplotlib.__version__,
        "pillow": PIL.__version__,
    }

    mechanism_block = {
        "script": GENERATOR,
        "evidence_mode": EVIDENCE_MODE,
        "figures": sorted(entry["stem"] for entry in entries),
        "typography": typography,
        "environment": environment,
        "source_of_truth": (
            ".Codex/docs/RWKV/2026-08-31-CEM-BER机制形式化与复杂度规约.md"
        ),
        "note": (
            "四张机制图只画方法结构，不含四格读数、增量或有效性表述；"
            "图内出现的数值全部是已冻结的方法规格常量或标注为示意的取值。"
        ),
    }
    generators = [mechanism_block]
    for block in previous.get("generators", []):
        if block.get("script") != GENERATOR:
            generators.append(block)

    withdrawn: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in list(previous.get("withdrawn", [])) + list(WITHDRAWN):
        stem = str(item.get("stem"))
        if stem in seen:
            continue
        seen.add(stem)
        withdrawn.append(item)

    manifest = {
        "contract": "AGENTS.md 学位论文图件合同（2026-08-13 重定）；thesis/figures/AGENTS.md",
        "updated_at": UPDATED_AT,
        "grayscale_readable": True,
        "generators": generators,
        "withdrawn": sorted(withdrawn, key=lambda item: str(item["stem"])),
        "figures": sorted(
            kept + entries,
            key=lambda item: int(str(item["stem"]).split("-")[1]),
        ),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ================================================================ 入口


SPECS = (
    FigureSpec("图3-1-整体方法框架", 150.0, 115.0, draw_overall_framework),
    FigureSpec("图3-2-二IP无向对序列构造", 150.0, 80.0, draw_entity_key_sequence),
    FigureSpec("图3-3-因果实体记忆的读写与交叉注意力", 150.0, 132.0, draw_causal_entity_memory),
    FigureSpec("图3-4-预算感知实体排序的目标构造", 150.0, 128.0, draw_budget_aware_ranking),
)


def main() -> None:
    entries: list[dict[str, Any]] = []
    for spec in SPECS:
        entry = fs.save_figure(ROOT, spec, spec.draw())
        entry["generator"] = GENERATOR
        entry["caption"] = CAPTIONS[spec.stem]
        entry["evidence_mode"] = EVIDENCE_MODE
        entry["data_source"] = "不承载实验数据"
        entry["data_keys"] = []
        entries.append(entry)
    report = fs.verify_outputs(ROOT, entries)
    build_manifest(entries)
    print(
        f"中文字体：{fs.CJK_FONT.family}"
        f"（{fs.CJK_FONT.path}，face {fs.CJK_FONT.face_index}）"
    )
    print(f"西文字体：{fs.LATIN_FONT.family}（{fs.LATIN_FONT.path}）")
    print(
        "数学字体："
        + ("未解析，回退 stix" if fs.MATH_FONT is None else fs.MATH_FONT.family)
    )
    for line in report:
        print(line)
    print(f"图件清单：{MANIFEST_PATH}")


if __name__ == "__main__":
    main()
