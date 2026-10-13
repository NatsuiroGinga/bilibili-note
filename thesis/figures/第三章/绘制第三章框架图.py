"""生成第三章方法整体框架图（图 3-1）。

本脚本不读取任何实验结果、日志或运行制品。图内出现的域名、替换字符与轮次预算
全部是示意取值或方法规格，对应图件清单中的
`evidence_mode = method_schematic_without_experimental_results`。

机制内容的来源是
`thesis/methods/第三章-编辑预算课程调度机制方案.md` 与
`thesis/chapters/03-面向离散规避攻击的低误报DGA鲁棒训练方法.md` §3.3。
课程调度臂的判别实验尚未出数，故本图只画方法与数据流，不出现任何增量、
有效性判断或增益表述。

生成命令：
    uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章框架图.py
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
GENERATOR = "绘制第三章框架图.py"
UPDATED_AT = "2026-10-13"

EVIDENCE_MODE = "method_schematic_without_experimental_results"
STEM = "图3-1-方法整体框架"
CAPTION = (
    "图3-1　本章方法整体框架：（a）训练侧由受限编辑算子生成编辑变体、并入批次训练"
    "并更新参数，编辑预算按三轮递增，由 1 候选 × 2 位编辑递进到 4 候选 × 累积 4 位；"
    "（b）编辑核内部在可编辑位做字符替换、冻结点号并保持档间共享前缀，输出若干合法变体；"
    "（c）评价侧用同一族算子生成攻击串，在冻结低误报工作点上测受攻击漏检率并报干净侧误报率；"
    "训练侧与评价侧以虚线连接，为同一算子族的不同采样"
)
FOOTNOTE = "本图为方法框架示意，域名与替换字符为示意取值，不含任何实验结果数值。"

# 细虚线用于「上图的编辑核在此放大」，长虚线用于「训练侧与评价侧同族不同采样」。
DASH_ZOOM = (0, (3, 2))
DASH_FAMILY = (0, (4, 2))
STAGE_ARROW_WIDTHS = (1.2, 2.2)

WIDTH_MM = 150.0
HEIGHT_MM = 132.0

# 版面切分：三带自上而下为训练侧、编辑核内部、评价侧，左侧竖排分区标签。
STRIP_X = 0.014
STRIP_W = 0.046
STRIP_SPANS = (
    (0.556, 0.966, "训练侧"),
    (0.283, 0.512, "编辑核内部"),
    (0.062, 0.236, "评价侧"),
)
CONTENT_LEFT = 0.076
CONTENT_RIGHT = 0.978

# (a) 训练侧：循环三框 + 三轮递增阶梯。
LOOP_Y0 = 0.795
LOOP_H = 0.120
LOOP_GAP = 0.036
LOOP_LABELS = (
    (
        Line("① 受限编辑算子", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
        Line("在可编辑位生成替换变体", fs.MIN_FONT_PT, "cjk", fs.INK),
        Line("冻结点号，保持共享前缀", fs.MIN_FONT_PT, "cjk", fs.MUTED),
    ),
    (
        Line("② 入批训练", fs.MAIN_FONT_PT, "cjk", fs.INK),
        Line("编辑变体与原始样本同批", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        Line("前向与反向传播", fs.MIN_FONT_PT, "cjk", fs.MUTED),
    ),
    (
        Line("③ 参数更新", fs.MAIN_FONT_PT, "cjk", fs.INK),
        Line("更新后的模型进入下一轮", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        Line("重新生成编辑变体", fs.MIN_FONT_PT, "cjk", fs.MUTED),
    ),
)

STAIR_X0, STAIR_X1 = 0.235, 0.978
STAIR_GAP = 0.030
STAIR_BASE = 0.560
STAIR_ARROW_Y = 0.590
STAGES = (
    ("第 1 轮", "1 候选 × 2 位编辑", 0.090),
    ("第 2 轮", "1 候选 × 累积 4 位", 0.130),
    ("第 3 轮", "4 候选 × 累积 4 位", 0.170),
)

# (b) 编辑核内部。
ZOOM_XS = (0.090, 0.185)
ZOOM_Y0 = LOOP_Y0
ZOOM_Y1 = 0.500
RULE_BOX_X0, RULE_BOX_W = 0.258, 0.302
VAR_X0 = 0.602
VAR_GAP = 0.018
VAR_H = 0.094
VARIANTS = (("xbc.dxyz", "q = 1"), ("xyc.dxyz", "q = 2"), ("xyz.dxyz", "q = 3"))

# (c) 评价侧与同族虚线连接。
FAMILY_LINK_X = 0.310
C_Y0, C_H = 0.085, 0.090
C_GAP = 0.040


def draw_method_framework() -> Canvas:
    """本章方法整体框架：训练侧的课程调度、编辑核内部的一次调用与评价侧采样。"""

    cv = fs.canvas(WIDTH_MM, HEIGHT_MM)

    # ------------------------------------------------------------ 分区标签
    for y0, y1, label in STRIP_SPANS:
        fs.box(
            cv,
            STRIP_X,
            y0,
            STRIP_W,
            y1 - y0,
            face=fs.SHADE,
            edge=fs.HAIRLINE,
            linewidth=0.7,
            radius=0.008,
            zorder=2,
        )
        fs.text(
            cv,
            STRIP_X + STRIP_W / 2.0,
            (y0 + y1) / 2.0,
            label,
            size=fs.MIN_FONT_PT,
            color=fs.MUTED,
            rotation=90.0,
        )

    # ------------------------------------------------------------ (a) 训练侧
    fs.text(
        cv,
        CONTENT_LEFT,
        0.936,
        "（a）三轮递增的编辑预算课程调度",
        size=fs.MAIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )

    loop_w = (CONTENT_RIGHT - CONTENT_LEFT - 2 * LOOP_GAP) / 3.0
    loop_cx = [
        CONTENT_LEFT + loop_w / 2.0 + index * (loop_w + LOOP_GAP) for index in range(3)
    ]
    for cx, lines in zip(loop_cx, LOOP_LABELS, strict=True):
        highlight = lines is LOOP_LABELS[0]
        fs.box(
            cv,
            cx - loop_w / 2.0,
            LOOP_Y0,
            loop_w,
            LOOP_H,
            lines,
            face=fs.M1_FACE if highlight else fs.WHITE,
            edge=fs.M1_EDGE if highlight else fs.MUTED,
            linewidth=1.4 if highlight else fs.MAIN_LINE_PT,
            hatch=fs.M1_HATCH if highlight else None,
            hatch_color=fs.HAIRLINE,
        )

    cy_loop = LOOP_Y0 + LOOP_H / 2.0
    for left, right in zip(loop_cx, loop_cx[1:], strict=False):
        fs.arrow(
            cv,
            (left + loop_w / 2.0 + 0.004, cy_loop),
            (right - loop_w / 2.0 - 0.004, cy_loop),
        )

    # 循环回边：更新参数后回到编辑核，进入下一轮。
    fs.routed_arrow(
        cv,
        [
            (loop_cx[2], LOOP_Y0 - 0.002),
            (loop_cx[2], 0.770),
            (loop_cx[0], 0.770),
            (loop_cx[0], LOOP_Y0 - 0.002),
        ],
        color=fs.RULE,
        linewidth=fs.MAIN_LINE_PT,
    )
    fs.text(
        cv,
        0.527,
        0.759,
        "下一轮：按下一阶段的预算重新生成",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )

    # 三轮预算阶梯：卡高递增，卡间箭头线宽同步增粗。
    stair_w = (STAIR_X1 - STAIR_X0 - 2 * STAIR_GAP) / 3.0
    stair_cx = [
        STAIR_X0 + stair_w / 2.0 + index * (stair_w + STAIR_GAP) for index in range(3)
    ]
    for cx, (round_label, budget_label, height) in zip(stair_cx, STAGES, strict=True):
        fs.box(
            cv,
            cx - stair_w / 2.0,
            STAIR_BASE,
            stair_w,
            height,
            (
                Line(round_label, fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line(budget_label, fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
            face=fs.SHADE,
            edge=fs.MUTED,
            linewidth=fs.MAIN_LINE_PT,
        )
    for index, width in enumerate(STAGE_ARROW_WIDTHS):
        fs.arrow(
            cv,
            (stair_cx[index] + stair_w / 2.0 + 0.004, STAIR_ARROW_Y),
            (stair_cx[index + 1] - stair_w / 2.0 - 0.004, STAIR_ARROW_Y),
            color=fs.INK,
            linewidth=width,
            head=6.0 + 2.5 * index,
        )
    fs.text(
        cv,
        (STAIR_X0 + STAIR_X1) / 2.0,
        0.540,
        "预算递增：候选数与编辑位数由弱到强",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )

    # 编辑核放大到 (b)：两条细虚线自编辑核盒底边下行。
    for x in ZOOM_XS:
        fs.polyline(
            cv,
            [(x, ZOOM_Y0), (x, ZOOM_Y1)],
            color=fs.RULE,
            linewidth=fs.AUX_LINE_PT,
            linestyle=DASH_ZOOM,
            zorder=2,
        )
    fs.text(
        cv,
        sum(ZOOM_XS) / 2.0,
        0.700,
        "放大",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )

    # ------------------------------------------------------ (b) 编辑核内部
    fs.text(
        cv,
        CONTENT_LEFT,
        0.470,
        "（b）编辑核内部：受限编辑算子的一次调用",
        size=fs.MAIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )

    row_y0, row_h = 0.296, 0.140
    cy_row = row_y0 + row_h / 2.0
    fs.box(
        cv,
        CONTENT_LEFT,
        row_y0,
        0.140,
        row_h,
        (
            Line("输入", fs.MAIN_FONT_PT, "cjk", fs.INK),
            Line("域名主体", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            Line("abc.dxyz", fs.MIN_FONT_PT, "cjk", fs.INK),
        ),
    )
    fs.arrow(cv, (0.220, cy_row), (RULE_BOX_X0 - 0.004, cy_row))
    fs.box(
        cv,
        RULE_BOX_X0,
        row_y0,
        RULE_BOX_W,
        row_h,
        (
            Line("编辑核：一次编辑调用", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
            Line("在可编辑位做字符替换", fs.MIN_FONT_PT, "cjk", fs.INK),
            Line("冻结点号，保持共享前缀", fs.MIN_FONT_PT, "cjk", fs.MUTED),
        ),
        face=fs.M1_FACE,
        edge=fs.M1_EDGE,
        linewidth=1.4,
        hatch=fs.M1_HATCH,
        hatch_color=fs.HAIRLINE,
    )
    fs.arrow(
        cv,
        (RULE_BOX_X0 + RULE_BOX_W + 0.004, cy_row),
        (VAR_X0 - 0.004, cy_row),
    )

    fs.text(
        cv,
        0.790,
        0.420,
        "输出：合法变体（共享前缀链）",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
    )
    var_w = (CONTENT_RIGHT - VAR_X0 - 2 * VAR_GAP) / 3.0
    var_cx = [VAR_X0 + var_w / 2.0 + index * (var_w + VAR_GAP) for index in range(3)]
    for cx, (variant, tag) in zip(var_cx, VARIANTS, strict=True):
        fs.box(
            cv,
            cx - var_w / 2.0,
            row_y0,
            var_w,
            VAR_H,
            (
                Line(variant, fs.MIN_FONT_PT, "cjk", fs.INK),
                Line(tag, fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
        )

    # 训练侧与评价侧共享同一算子族，采样方式不同：同填充图案、虚线描边。
    for start, end in (
        ((FAMILY_LINK_X, row_y0), (FAMILY_LINK_X, C_Y0 + C_H)),
        ((FAMILY_LINK_X, C_Y0 + C_H), (FAMILY_LINK_X, row_y0)),
    ):
        fs.arrow(
            cv,
            start,
            end,
            color=fs.M1_EDGE,
            linewidth=fs.MAIN_LINE_PT,
            linestyle=DASH_FAMILY,
            head=6.0,
            zorder=2,
        )
    fs.text(
        cv,
        FAMILY_LINK_X + 0.016,
        0.240,
        "同一算子族、不同采样",
        size=fs.MIN_FONT_PT,
        color=fs.M1_EDGE,
        ha="left",
    )

    # ------------------------------------------------------------ (c) 评价侧
    fs.text(
        cv,
        CONTENT_LEFT,
        0.216,
        "（c）攻击串生成与读数",
        size=fs.MAIN_FONT_PT,
        color=fs.INK,
        ha="left",
    )

    c_w = (CONTENT_RIGHT - CONTENT_LEFT - 2 * C_GAP) / 3.0
    c_cx = [CONTENT_LEFT + c_w / 2.0 + index * (c_w + C_GAP) for index in range(3)]
    c_boxes = (
        (
            (
                Line("评价侧编辑算子", fs.MAIN_FONT_PT, "cjk", fs.M1_EDGE),
                Line("同一族，不同采样", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
            True,
        ),
        (
            (
                Line("生成三档攻击串", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line("弱档 · 中档 · 强档", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
            False,
        ),
        (
            (
                Line("测受攻击漏检率", fs.MAIN_FONT_PT, "cjk", fs.INK),
                Line("并报干净侧误报率", fs.MIN_FONT_PT, "cjk", fs.MUTED),
            ),
            False,
        ),
    )
    for cx, (lines, shared_operator) in zip(c_cx, c_boxes, strict=True):
        fs.box(
            cv,
            cx - c_w / 2.0,
            C_Y0,
            c_w,
            C_H,
            lines,
            face=fs.M1_FACE if shared_operator else fs.WHITE,
            edge=fs.M1_EDGE if shared_operator else fs.MUTED,
            linewidth=1.2 if shared_operator else fs.MAIN_LINE_PT,
            linestyle=DASH_FAMILY if shared_operator else "-",
            hatch=fs.M1_HATCH if shared_operator else None,
            hatch_color=fs.HAIRLINE,
        )
    cy_c = C_Y0 + C_H / 2.0
    for left, right in zip(c_cx, c_cx[1:], strict=False):
        fs.arrow(
            cv,
            (left + c_w / 2.0 + 0.004, cy_c),
            (right - c_w / 2.0 - 0.004, cy_c),
        )

    fs.footnote(cv, FOOTNOTE, y=0.030)
    return cv


# ================================================================ 图件清单

GENERATOR_NOTE = (
    "本图为方法框架示意，不含四格读数、增量或有效性表述；"
    "训练侧三阶段预算（1 候选 × 2 位编辑 → 1 候选 × 累积 4 位 → 4 候选 × 累积 4 位）"
    "是课程调度的设计规格，属待验证候选机制，其判别实验尚未出数；"
    "域名字符串与替换字符为示意取值，不取自任何数据成员。"
)


def build_manifest(entries: list[dict[str, Any]]) -> None:
    """把本生成器与图 3-1 登记进图件清单，原样保留其他生成器的分段与条目。

    其他条目（机制图、结果图）各自含数据来源键路径与实测分辨率，只有对应脚本能
    重新测量，故此处不重建它们，也不改动 `withdrawn` 段。
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

    framework_block = {
        "script": GENERATOR,
        "evidence_mode": EVIDENCE_MODE,
        "figures": sorted(entry["stem"] for entry in entries),
        "typography": typography,
        "environment": environment,
        "source_of_truth": (
            "thesis/methods/第三章-编辑预算课程调度机制方案.md；"
            "thesis/chapters/03-面向离散规避攻击的低误报DGA鲁棒训练方法.md §3.3"
        ),
        "note": GENERATOR_NOTE,
    }
    generators = [framework_block]
    for block in previous.get("generators", []):
        if block.get("script") != GENERATOR:
            generators.append(block)

    manifest = {
        "contract": previous.get(
            "contract", "AGENTS.md 学位论文图件合同（2026-08-13 重定）；thesis/figures/AGENTS.md"
        ),
        "updated_at": UPDATED_AT,
        "grayscale_readable": True,
        "generators": generators,
        "withdrawn": previous.get("withdrawn", []),
        "figures": sorted(
            kept + entries,
            key=lambda item: (
                int(str(item["stem"]).split("-")[1]),
                str(item["stem"]),
            ),
        ),
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# ================================================================ 入口

SPECS = (FigureSpec(STEM, WIDTH_MM, HEIGHT_MM, draw_method_framework),)


def main() -> None:
    entries: list[dict[str, Any]] = []
    for spec in SPECS:
        entry = fs.save_figure(ROOT, spec, spec.draw())
        entry["generator"] = GENERATOR
        entry["caption"] = CAPTION
        entry["evidence_mode"] = EVIDENCE_MODE
        entry["data_source"] = "概念示意图，不承载实验数据"
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
