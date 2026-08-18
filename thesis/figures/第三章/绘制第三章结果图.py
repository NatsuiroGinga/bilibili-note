"""生成第三章七张实验结果图（图3-5 ~ 图3-11）。

唯一数据源（不得从别处取数）：
  thesis/experiments/llm_probe/runs/diagnostics/ch3-full/ch3_full_results.json
  thesis/experiments/llm_probe/runs/diagnostics/ch3-full/run.log

外部参照常量（Dijk 2026 表 5、XGBoost、逐流 MLP、随机先验）来自同族冻结脚本
thesis/experiments/llm_probe/tools/ch3_main.py 第 282、302-304 行，在图内与清单中显式标注来源。

输出 PNG(400 ppi) + PDF + SVG，落 thesis/figures/第三章/，并把本脚本负责的条目合并进 图件清单.json。
执行：uv run --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章结果图.py
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.axes import Axes
from matplotlib.figure import Figure

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RUN_DIR = REPO / "thesis/experiments/llm_probe/runs/diagnostics/ch3-full"
JSON_PATH = RUN_DIR / "ch3_full_results.json"
LOG_PATH = RUN_DIR / "run.log"
MANIFEST_PATH = ROOT / "图件清单.json"

# 学位论文图件合同：中文黑体。macOS 无 SimHei，按黑体族优先级回退到华文黑体。
CJK_FONT_CANDIDATES = (
    Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/Library/Fonts/Arial Unicode.ttf"),
)
LATIN_FONT_CANDIDATES = (Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf"),)

PNG_DPI = 400
FS_MIN = 8.0  # 图内最小字号
FS_MAIN = 9.0  # 主标注字号

INK = "#1F2A30"
MUTED = "#5C6A73"
GRID = "#D5DCE0"
ACCENT = "#B03A2E"
FILL_C00 = "#E6EBEE"
FILL_C01 = "#B7C3CB"
FILL_C10 = "#7C8B95"
FILL_C11 = "#3B4E5A"
FILL_OWN_BASE = "#FFFFFF"
FILL_EXTERNAL = "#FFFFFF"

# 外部参照常量，来源 tools/ch3_main.py:282 与 302-304（同一冻结评价池）
FLOW_PRIOR = 0.0257073138
EXTERNAL_REFS = {
    "XGBoost全量": 0.224442,
    "逐流MLP": 0.159013,
    "Dijk表5-XGB": 0.2416,
    "Dijk表5-GRU+SesH": 0.1758,
    "Dijk表5-Transformer+2-H": 0.0742,
}
ENTITY_FLOW_MEDIAN = 2  # run.log 第 5 行：实体内时序秩已建，实体流数中位=2

CELL_NAMES = {
    "C00": "基线序列编码器",
    "C01": "仅实体级Lp池化",
    "C10": "仅因果前缀聚合",
    "C11": "完整方法",
}
CELL_TAGS = {"C00": "A-,B-", "C01": "A-,B+", "C10": "A+,B-", "C11": "A+,B+"}
CELL_FILLS = {"C00": FILL_C00, "C01": FILL_C01, "C10": FILL_C10, "C11": FILL_C11}
CELL_HATCH = {"C00": "", "C01": "//", "C10": "..", "C11": "xx"}
CELL_ORDER = ("C00", "C01", "C10", "C11")


def register_fonts() -> dict[str, str]:
    """注册中文黑体与西文 Times New Roman，返回实际生效的字体名。"""

    def pick(candidates: tuple[Path, ...], kind: str) -> str:
        for path in candidates:
            if path.exists():
                font_manager.fontManager.addfont(str(path))
                return font_manager.FontProperties(fname=str(path)).get_name()
        raise FileNotFoundError(f"未找到可用的{kind}字体，候选={candidates}")

    cjk = pick(CJK_FONT_CANDIDATES, "中文黑体")
    latin = pick(LATIN_FONT_CANDIDATES, "西文")
    return {"cjk": cjk, "latin": latin}


FONTS = register_fonts()

plt.rcParams.update(
    {
        # 西文优先 Times New Roman，中文逐字形回退到黑体
        "font.family": [FONTS["latin"], FONTS["cjk"]],
        "axes.unicode_minus": False,
        "mathtext.fontset": "stix",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.transparent": False,
        "font.size": FS_MIN,
        "axes.labelsize": FS_MAIN,
        "axes.titlesize": FS_MAIN,
        "xtick.labelsize": FS_MIN,
        "ytick.labelsize": FS_MIN,
        "legend.fontsize": FS_MIN,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "grid.linewidth": 0.5,
        "lines.linewidth": 1.4,
        "hatch.linewidth": 0.6,
        "axes.edgecolor": INK,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
    }
)


@dataclass(frozen=True)
class FigureSpec:
    """一张结果图的尺寸、绘制入口与溯源信息。"""

    stem: str
    width_mm: float
    height_mm: float
    draw: Callable[[dict[str, Any], dict[str, Any]], Figure]
    json_keys: tuple[str, ...]
    caption: str


def mm_to_inch(value: float) -> float:
    return value / 25.4


def new_figure(width_mm: float, height_mm: float) -> Figure:
    return plt.figure(figsize=(mm_to_inch(width_mm), mm_to_inch(height_mm)), dpi=150)


def style_axes(ax: Axes, *, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, pad=1.5)


def warning_box(fig: Figure, text: str, *, y: float = 0.015) -> None:
    """把已知缺陷说明直接钉在图面上，保证与图件不可分离。"""

    fig.text(
        0.5,
        y,
        text,
        ha="center",
        va="bottom",
        fontsize=FS_MIN,
        color=ACCENT,
        linespacing=1.35,
        bbox={"boxstyle": "round,pad=0.32", "facecolor": "#FDF2F0", "edgecolor": ACCENT, "linewidth": 0.7},
    )


def load_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    """读取冻结 JSON 与 run.log，解析 Lp 指数逐 epoch 轨迹（若存在）。"""

    if not JSON_PATH.exists():
        raise FileNotFoundError(f"冻结结果不存在：{JSON_PATH}")
    with JSON_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)

    log_text = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""
    # 逐 epoch 轨迹须同时含 epoch/step 标记与 p 值；本次为顺序执行，预期无匹配。
    traj_pattern = re.compile(
        r"(?:epoch|ep|step)\s*[=: ]\s*(\d+)[^\n]*?\b(C\d{2})\b[^\n]*?p=([0-9.]+)", re.IGNORECASE
    )
    trajectory: dict[str, list[tuple[int, float]]] = {}
    for step, cell, value in traj_pattern.findall(log_text):
        trajectory.setdefault(cell, []).append((int(step), float(value)))
    has_trajectory = any(len(v) >= 2 for v in trajectory.values())

    # 终值 p（无 epoch 标记的行），用于回退柱状图的三种子标注
    seed_pattern = re.compile(r"(C\d{2})-s(\d+)[^\n]*?p=([0-9.]+)")
    seed_p: dict[str, dict[int, float]] = {}
    for cell, seed, value in seed_pattern.findall(log_text):
        seed_p.setdefault(cell, {})[int(seed)] = float(value)

    log_facts = {"trajectory": trajectory, "has_trajectory": has_trajectory, "seed_p": seed_p}
    return data, log_facts


def interaction(cells: dict[str, Any], key: str) -> dict[str, float]:
    """按预注册设计计算 2x2 主效应与交互项。"""

    v = {c: float(cells[c][key]) for c in CELL_ORDER}
    a_main = v["C10"] - v["C00"]
    b_main = v["C01"] - v["C00"]
    combo = v["C11"] - v["C00"]
    delta = v["C11"] - v["C10"] - v["C01"] + v["C00"]
    return {
        **v,
        "A": a_main,
        "B": b_main,
        "sum": a_main + b_main,
        "combo": combo,
        "delta": delta,
        "crit1": float(delta > 0.0),
        "crit2": float(v["C11"] > max(v["C01"], v["C10"])),
    }


def draw_main_comparison(data: dict[str, Any], _log: dict[str, Any]) -> Figure:
    """图3-5 跨年度主性能对比（逐流 AP 横向条形）。"""

    cells = data["cells"]
    rows = [
        (f"本章 {CELL_NAMES['C11']}（前缀聚合+Lp池化）", float(cells["C11"]["fap"]), "own_cell", "C11"),
        (f"本章 {CELL_NAMES['C10']}", float(cells["C10"]["fap"]), "own_cell", "C10"),
        (f"本章 {CELL_NAMES['C01']}", float(cells["C01"]["fap"]), "own_cell", "C01"),
        (f"本章 {CELL_NAMES['C00']}", float(cells["C00"]["fap"]), "own_cell", "C00"),
        ("本课题 XGBoost 全量字段", EXTERNAL_REFS["XGBoost全量"], "own_base", None),
        ("本课题 逐流 MLP", EXTERNAL_REFS["逐流MLP"], "own_base", None),
        ("Dijk 2026 表5 XGBoost", EXTERNAL_REFS["Dijk表5-XGB"], "external", None),
        ("Dijk 2026 表5 GRU + SesH", EXTERNAL_REFS["Dijk表5-GRU+SesH"], "external", None),
        ("Dijk 2026 表5 Transformer + 2-H", EXTERNAL_REFS["Dijk表5-Transformer+2-H"], "external", None),
    ]

    fig = new_figure(150, 95)
    ax = fig.add_axes((0.335, 0.335, 0.635, 0.615))
    style_axes(ax, grid_axis="x")

    ypos = np.arange(len(rows))[::-1]
    for y, (label, value, kind, cell) in zip(ypos, rows, strict=True):
        if kind == "own_cell" and cell is not None:
            face, hatch, edge = CELL_FILLS[cell], CELL_HATCH[cell], INK
        elif kind == "own_base":
            face, hatch, edge = FILL_OWN_BASE, "\\\\", MUTED
        else:
            face, hatch, edge = FILL_EXTERNAL, "///", ACCENT
        ax.barh(y, value, height=0.66, facecolor=face, edgecolor=edge, linewidth=0.9, hatch=hatch, zorder=3)
        ax.text(value + 0.006, y, f"{value:.4f}", va="center", ha="left", fontsize=FS_MIN, color=INK, zorder=4)

    ax.vlines(FLOW_PRIOR, -0.7, len(rows) - 0.52, color=ACCENT, linestyle=(0, (4, 2)), linewidth=1.1, zorder=5)
    ax.text(
        FLOW_PRIOR + 0.008,
        len(rows) - 0.35,
        f"随机先验 {FLOW_PRIOR:.6f}",
        fontsize=FS_MIN,
        color=ACCENT,
        va="center",
        ha="left",
    )

    ax.set_yticks(ypos)
    ax.set_yticklabels([r[0] for r in rows], fontsize=FS_MIN)
    ax.set_xlim(0, 0.50)
    ax.set_xlabel("跨年度逐流平均精确率 AP（LSPR23 训练 → LSPR24 评价）", fontsize=FS_MAIN, labelpad=4)
    ax.set_ylim(-0.7, len(rows) + 0.1)

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=FILL_C11, edgecolor=INK, linewidth=0.9, hatch="xx"),
        plt.Rectangle((0, 0), 1, 1, facecolor=FILL_OWN_BASE, edgecolor=MUTED, linewidth=0.9, hatch="\\\\"),
        plt.Rectangle((0, 0), 1, 1, facecolor=FILL_EXTERNAL, edgecolor=ACCENT, linewidth=0.9, hatch="///"),
    ]
    labels = [
        "本章 2×2 四格（同一冻结评价池）",
        "本课题同协议基线",
        "Dijk 2026 表5 论文原始数字，协议不完全等同",
    ]
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.012),
        frameon=True,
        framealpha=1.0,
        edgecolor=GRID,
        fontsize=FS_MIN,
        borderpad=0.4,
        handlelength=1.6,
        handleheight=1.0,
        labelspacing=0.35,
    )
    return fig


def draw_interaction(data: dict[str, Any], _log: dict[str, Any]) -> Figure:
    """图3-6 双机制消融交互（三个口径并列，结论不一致如实呈现）。"""

    cells = data["cells"]
    panels = [
        ("(a) 逐流 AP", "fap", "逐流 AP"),
        ("(b) 实体 AP（Lp 池化）", "e_lp", "实体 AP"),
        ("(c) DR@4%FPR", "dr", "DR@4%FPR"),
    ]

    fig = new_figure(150, 100)
    axes = [fig.add_axes((0.085 + i * 0.315, 0.545, 0.235, 0.365)) for i in range(3)]

    for idx, (ax, (title, key, ylabel)) in enumerate(zip(axes, panels, strict=True)):
        stat = interaction(cells, key)
        style_axes(ax)
        xs = np.arange(4)
        for x, cell in zip(xs, CELL_ORDER, strict=True):
            ax.bar(
                x,
                stat[cell],
                width=0.68,
                facecolor=CELL_FILLS[cell],
                edgecolor=INK,
                linewidth=0.9,
                hatch=CELL_HATCH[cell],
                zorder=3,
            )
            ax.text(x, stat[cell] + 0.006, f"{stat[cell]:.3f}", ha="center", va="bottom", fontsize=FS_MIN)

        top = max(stat[c] for c in CELL_ORDER)
        ax.set_ylim(0, top * 1.20)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{c}\n{CELL_TAGS[c]}" for c in CELL_ORDER], fontsize=FS_MIN, linespacing=1.2)
        ax.set_ylabel(ylabel, fontsize=FS_MAIN, labelpad=2)
        ax.set_title(title, fontsize=FS_MAIN, pad=3)

        mark1 = "通过" if stat["crit1"] > 0 else "不通过"
        mark2 = "通过" if stat["crit2"] > 0 else "不通过"
        color = INK if stat["crit1"] > 0 and stat["crit2"] > 0 else ACCENT
        note = (
            f"A 主效应 {stat['A']:+.4f}\n"
            f"B 主效应 {stat['B']:+.4f}\n"
            f"之和      {stat['sum']:+.4f}\n"
            f"组合      {stat['combo']:+.4f}\n"
            f"交互 Δ    {stat['delta']:+.4f}\n"
            f"判据一 {mark1}／二 {mark2}"
        )
        fig.text(
            0.085 + idx * 0.315 + 0.1175,
            0.462,
            note,
            ha="center",
            va="top",
            fontsize=FS_MIN,
            linespacing=1.28,
            color=color,
            bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": color, "linewidth": 0.7},
        )

    fig.text(
        0.5,
        0.222,
        "C00 基线序列编码器　C01 仅实体级 Lp 池化　C10 仅因果前缀聚合　C11 完整方法\n"
        "A = 因果前缀聚合，B = 实体级 Lp 池化；Δ = C11 - C10 - C01 + C00；"
        "判据一 Δ > 0；判据二 C11 > max(C01, C10)",
        ha="center",
        va="top",
        fontsize=FS_MIN,
        linespacing=1.3,
        color=MUTED,
    )
    warning_box(
        fig,
        "三个评价口径结论不一致：实体 AP 与 DR@4%FPR 两条判据均通过，\n逐流 AP 判据一、判据二均不通过。此处如实并列呈现，不作取舍。",
        y=0.012,
    )
    return fig


def draw_stability(data: dict[str, Any], _log: dict[str, Any]) -> Figure:
    """图3-7 训练稳定性（三种子逐流 AP）。"""

    stab = data["stability"]
    groups = [("C00", f"{CELL_NAMES['C00']}\nC00"), ("C11", f"{CELL_NAMES['C11']}\nC11")]
    seeds = (42, 43, 44)
    markers = ("o", "s", "^")

    fig = new_figure(110, 85)
    ax = fig.add_axes((0.185, 0.215, 0.775, 0.70))
    style_axes(ax)

    for gi, (cell, label) in enumerate(groups):
        vals = np.asarray(stab[cell], dtype=float)
        mean, sd = float(vals.mean()), float(vals.std(ddof=1))
        ax.add_patch(
            plt.Rectangle(
                (gi - 0.26, mean - sd),
                0.52,
                2 * sd,
                facecolor="#EEF2F4",
                edgecolor=MUTED,
                linewidth=0.6,
                hatch=CELL_HATCH[cell] or None,
                zorder=2,
            )
        )
        ax.hlines(mean, gi - 0.28, gi + 0.28, color=INK, linewidth=1.4, zorder=4)
        for si, (seed, marker) in enumerate(zip(seeds, markers, strict=True)):
            ax.plot(
                gi,
                vals[si],
                marker=marker,
                markersize=5.0,
                markerfacecolor="white",
                markeredgecolor=INK,
                markeredgewidth=1.0,
                linestyle="none",
                zorder=5,
                label=f"种子 {seed}" if gi == 0 else None,
            )
            ax.text(
                gi + 0.30,
                vals[si],
                f"{vals[si]:.4f}",
                ha="left",
                va="center",
                fontsize=FS_MIN,
                zorder=6,
            )
        ax.text(
            gi,
            mean - sd - 0.008,
            f"均值 {mean:.4f}\nσ {sd:.6f}",
            ha="center",
            va="top",
            fontsize=FS_MIN,
            color=ACCENT,
            linespacing=1.3,
            zorder=6,
        )

    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([g[1] for g in groups], fontsize=FS_MIN)
    ax.set_xlim(-0.60, len(groups) - 0.40)
    ax.set_ylim(0.138, 0.335)
    ax.set_ylabel("跨年度逐流 AP", fontsize=FS_MAIN)
    ax.legend(loc="upper left", frameon=True, framealpha=1.0, edgecolor=GRID, fontsize=FS_MIN, borderpad=0.35)
    fig.text(
        0.5,
        0.045,
        "阴影为 ±1σ（σ 按 ddof=1 计），协议：20000 步、末 5 检查点平均、顺序执行",
        ha="center",
        va="bottom",
        fontsize=FS_MIN,
        color=MUTED,
    )
    return fig


def draw_lp_exponent(data: dict[str, Any], log_facts: dict[str, Any]) -> Figure:
    """图3-8 Lp 指数：有逐 epoch 轨迹则画轨迹，否则画四格终值柱状图。"""

    cells = data["cells"]
    fig = new_figure(130, 85)
    ax = fig.add_axes((0.135, 0.215, 0.83, 0.70))
    style_axes(ax)

    if log_facts["has_trajectory"]:
        for cell, points in sorted(log_facts["trajectory"].items()):
            if len(points) < 2:
                continue
            pts = sorted(points)
            ax.plot(
                [p[0] for p in pts],
                [p[1] for p in pts],
                marker="o",
                markersize=3.5,
                label=f"{CELL_NAMES.get(cell, cell)} {cell}",
            )
        ax.set_xlabel("训练轮次", fontsize=FS_MAIN)
    else:
        xs = np.arange(4)
        trained = {"C01", "C11"}
        for x, cell in zip(xs, CELL_ORDER, strict=True):
            value = float(cells[cell]["p"])
            is_trained = cell in trained
            ax.bar(
                x,
                value,
                width=0.62,
                facecolor=CELL_FILLS[cell] if is_trained else "white",
                edgecolor=INK if is_trained else MUTED,
                linewidth=0.9,
                hatch=CELL_HATCH[cell] if is_trained else "..",
                zorder=3,
            )
            tail = "" if is_trained else "\n(未参与训练，初值)"
            ax.text(
                x,
                value + 0.045,
                f"p = {value:.4f}{tail}",
                ha="center",
                va="bottom",
                fontsize=FS_MIN,
                color=INK if is_trained else MUTED,
                linespacing=1.25,
            )
        ax.set_xticks(xs)
        ax.set_xticklabels([f"{CELL_NAMES[c]}\n{c}" for c in CELL_ORDER], fontsize=FS_MIN)
        ax.set_xlim(-0.65, 4.15)
        ax.set_ylim(0, 2.62)

    ax.axhline(1.0, color=ACCENT, linestyle=(0, (4, 2)), linewidth=1.1, zorder=5)
    ax.text(4.10, 1.04, "p = 1（算术平均）", ha="right", va="bottom", fontsize=FS_MIN, color=ACCENT)
    ax.set_ylabel("学到的 Lp 池化指数 p", fontsize=FS_MAIN)

    seed_p = log_facts["seed_p"].get("C11", {})
    extra = ""
    if seed_p:
        joined = " / ".join(f"{seed_p[s]:.4f}" for s in sorted(seed_p))
        extra = f"\nC11 另两种子（43／44）终值 p = {joined}，同样落在 p = 1 与 p → ∞ 之间（run.log）"
    fig.text(
        0.5,
        0.035,
        f"run.log 未记录逐 epoch 轨迹（本次为顺序执行），故本图只画各格终值{extra}",
        ha="center",
        va="bottom",
        fontsize=FS_MIN,
        color=MUTED,
        linespacing=1.35,
    )
    return fig


def draw_length(data: dict[str, Any], _log: dict[str, Any]) -> Figure:
    """图3-9 序列长度敏感性（实验已知有缺陷，仅作趋势参考）。"""

    lengths = sorted(int(k) for k in data["length"])
    flow_ap = [float(data["length"][str(L)][0]) for L in lengths]
    ent_ap = [float(data["length"][str(L)][1]) for L in lengths]

    fig = new_figure(130, 85)
    ax = fig.add_axes((0.135, 0.365, 0.72, 0.545))
    style_axes(ax)
    ax2 = ax.twinx()
    ax2.spines["top"].set_visible(False)

    xs = np.arange(len(lengths))
    ax.plot(xs, flow_ap, marker="o", markersize=4.5, linestyle="-", color=INK, markerfacecolor="white", zorder=4)
    ax2.plot(
        xs, ent_ap, marker="s", markersize=4.5, linestyle=(0, (5, 2)), color=MUTED, markerfacecolor="white", zorder=4
    )
    # 两条曲线在 L=64、128 处的像素位置接近，标签左右分置并加白底避免叠压
    label_bg = {"boxstyle": "square,pad=0.12", "facecolor": "white", "edgecolor": "none"}
    for x, v in zip(xs, flow_ap, strict=True):
        ax.text(x - 0.09, v, f"{v:.4f}", ha="right", va="center", fontsize=FS_MIN, color=INK, bbox=label_bg)
    for x, v in zip(xs, ent_ap, strict=True):
        ax2.text(x + 0.09, v, f"{v:.4f}", ha="left", va="center", fontsize=FS_MIN, color=MUTED, bbox=label_bg)

    ax.set_xticks(xs)
    ax.set_xticklabels([str(L) for L in lengths])
    ax.set_xlim(-0.62, len(lengths) - 0.38)
    ax.set_xlabel("序列长度 L（8000 步固定步数预算）", fontsize=FS_MAIN)
    ax.set_ylabel("逐流 AP（实线圆点）", fontsize=FS_MAIN)
    ax2.set_ylabel("实体 AP（虚线方点）", fontsize=FS_MAIN, color=MUTED)
    ax.set_ylim(0.165, 0.222)
    ax2.set_ylim(0.325, 0.435)
    ax2.tick_params(axis="y", colors=MUTED, length=2.5, pad=1.5)

    warning_box(
        fig,
        "本实验已知存在缺陷，仅作趋势参考，不支持「长上下文更好」的结论：\n"
        "(1) 截断取固定 L=128 块的前 L 个位置，逐流覆盖率约 L/128（L=16 时仅约 12.5% 的流被打分）；\n"
        "(2) 评价集正类基率随 L 改变，四点分母不同不可直接比较；\n"
        "(3) 8000 步固定预算下各 L 的训练流量预算最多相差 8 倍。",
        y=0.02,
    )
    return fig


def draw_facet(data: dict[str, Any], _log: dict[str, Any]) -> Figure:
    """图3-10 攻击类别分面（AP 与 AP/基率 lift 并列，标注每类正例数）。"""

    facet = data["facet"]
    items = sorted(facet.items(), key=lambda kv: kv[1][1], reverse=True)
    names = [k for k, _ in items]
    aps = np.array([float(v[0]) for _, v in items])
    pos = np.array([int(v[1]) for _, v in items])

    # 负例池由冻结逐流先验反推：所有类别共享同一负例集合（见 tools/ch3_full.py E6 掩码构造）
    pos_total = int(pos.sum())
    n_neg = pos_total * (1.0 - FLOW_PRIOR) / FLOW_PRIOR
    base = pos / (pos + n_neg)
    lift = aps / base

    short = [n if len(n) <= 22 else n[:21] + "…" for n in names]
    labels = [f"{s}\n正例 {p:,}" for s, p in zip(short, pos, strict=True)]

    fig = new_figure(130, 90)
    ax1 = fig.add_axes((0.335, 0.395, 0.285, 0.485))
    ax2 = fig.add_axes((0.700, 0.395, 0.270, 0.485))
    ypos = np.arange(len(names))[::-1]
    hatches = ["xx", "//", "..", "\\\\", "++"]

    def fmt_lift(value: float) -> str:
        return f"{value:.1f}×" if value < 100 else f"{value:,.0f}×"

    for ax, values, title, fmt, log_scale in (
        (ax1, aps, "(a) 类内 AP（跨类不可比）", lambda v: f"{v:.4f}", False),
        (ax2, lift, "(b) AP / 基率 lift（可比口径）", fmt_lift, True),
    ):
        style_axes(ax, grid_axis="x")
        left = 1.0 if log_scale else 0.0
        for y, value, hatch in zip(ypos, values, hatches, strict=True):
            ax.barh(
                y,
                value - left,
                left=left,
                height=0.62,
                facecolor=FILL_C01,
                edgecolor=INK,
                linewidth=0.9,
                hatch=hatch,
                zorder=3,
            )
            ax.text(value * 1.12, y, fmt(value), va="center", ha="left", fontsize=FS_MIN)
        ax.set_yticks(ypos)
        ax.set_ylim(-0.65, len(names) - 0.35)
        ax.set_title(title, fontsize=FS_MAIN, pad=3)
        if log_scale:
            ax.set_xscale("log")
            ax.set_xlim(1.0, 4.0e5)
            ax.set_xticks([1e1, 1e3, 1e5])
            ax.set_xlabel("对数刻度", fontsize=FS_MIN, labelpad=1)
        else:
            ax.set_xlim(0, float(values.max()) * 1.45)

    ax1.set_yticklabels(labels, fontsize=FS_MIN, linespacing=1.25)
    ax2.set_yticklabels([])

    warning_box(
        fig,
        "本实验已知存在缺陷，只作定性参考：\n"
        f"(1) Category 字段对恶意流几乎全空：「(空)」类含 {pos[0]:,} 个正例，占五类\n"
        f"　　正例合计的 {pos[0] / pos_total * 100:.2f}%，其余四类各仅 {pos.min()}～{sorted(pos)[-2]} 例；\n"
        "(2) 各类按「该类正例 + 全部负例」构造，评价基率相差数个数量级，故\n"
        "　　(a) 的类内 AP 跨类不可比；\n"
        f"(3) (b) 的基率按共享负例池 {n_neg:,.0f} 折算（冻结逐流先验 {FLOW_PRIOR:.6f}\n"
        f"　　与五类正例合计 {pos_total:,} 反推）；正例 ≤ {sorted(pos)[-2]} 的四类 lift 方差极大。",
        y=0.014,
    )
    return fig


def draw_latency_curve(data: dict[str, Any], _log: dict[str, Any]) -> Figure:
    """图3-11 受限观测下的检测能力（每实体只用按时间的前 k 条流）。"""

    curve = data["curve"]["C11"]
    full_x = 260.0
    xs = [float(row[0]) if row[0] is not None else full_x for row in curve]
    aps = [float(row[1]) for row in curve]
    drs = [float(row[2]) for row in curve]
    covs = [float(row[4]) for row in curve]
    full_ap = aps[-1]

    fig = new_figure(140, 95)
    ax = fig.add_axes((0.135, 0.315, 0.735, 0.595))
    style_axes(ax)
    ax2 = ax.twinx()
    ax2.spines["top"].set_visible(False)

    ax.set_xscale("log")
    ax.plot(xs, aps, marker="o", markersize=4.5, linestyle="-", color=INK, markerfacecolor="white", zorder=5)
    ax2.plot(
        xs, drs, marker="s", markersize=4.5, linestyle=(0, (5, 2)), color=MUTED, markerfacecolor="white", zorder=5
    )

    ax.axvline(ENTITY_FLOW_MEDIAN, color=ACCENT, linestyle=(0, (1, 1.6)), linewidth=1.1, zorder=3)
    ax.text(
        ENTITY_FLOW_MEDIAN * 1.10,
        0.4965,
        f"实体流数中位 = {ENTITY_FLOW_MEDIAN}",
        fontsize=FS_MIN,
        color=ACCENT,
        va="top",
        ha="left",
    )

    idx50 = next(i for i, row in enumerate(curve) if row[0] == 50)
    ax.annotate(
        f"k = 50：用 {covs[idx50] * 100:.2f}% 的流达到\n"
        f"全量 AP 的 {aps[idx50] / full_ap * 100:.1f}%（≥95%）\n"
        f"实体 AP {aps[idx50]:.6f} / {full_ap:.6f}",
        xy=(xs[idx50], aps[idx50]),
        xytext=(9.0, 0.3115),
        fontsize=FS_MIN,
        color=INK,
        linespacing=1.3,
        va="center",
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.9, "shrinkB": 3},
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": INK, "linewidth": 0.7},
    )

    ticks = [1, 2, 3, 5, 10, 20, 50, 100, full_x]
    ax.set_xticks(ticks)
    ax.set_xticklabels(["1", "2", "3", "5", "10", "20", "50", "100", "全部"], fontsize=FS_MIN)
    ax.minorticks_off()
    ax.set_xlim(0.82, 400)
    ax.set_ylim(0.28, 0.50)
    ax2.set_ylim(0.46, 0.74)
    ax.set_xlabel("每实体按时间使用的前 k 条流（对数刻度）", fontsize=FS_MAIN)
    ax.set_ylabel("实体 AP（实线圆点）", fontsize=FS_MAIN)
    ax2.set_ylabel("DR@4%FPR（虚线方点）", fontsize=FS_MAIN, color=MUTED)
    ax2.tick_params(axis="y", colors=MUTED, length=2.5, pad=1.5)

    ax.text(xs[0] * 1.14, aps[0] - 0.007, f"{aps[0]:.4f}（{covs[0] * 100:.2f}% 流）", ha="left", va="top", fontsize=FS_MIN)
    ax.text(xs[-1] * 1.35, aps[-1] - 0.020, f"{aps[-1]:.4f}（全部流）", ha="right", va="top", fontsize=FS_MIN)

    fig.text(
        0.5,
        0.035,
        "C11 完整方法，末 5 检查点平均；增益主要来自长尾实体——半数实体仅含 2 条流，\n"
        "k > 2 的收益只作用于流数更多的实体",
        ha="center",
        va="bottom",
        fontsize=FS_MIN,
        color=MUTED,
        linespacing=1.35,
    )
    return fig


SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        stem="图3-5-跨年度主性能对比",
        width_mm=150,
        height_mm=95,
        draw=draw_main_comparison,
        json_keys=("cells.C00.fap", "cells.C01.fap", "cells.C10.fap", "cells.C11.fap"),
        caption=(
            "图3-5 LSPR23 训练、LSPR24 零样本评价下的跨年度逐流平均精确率对比。"
            "本章 2×2 四格与本课题 XGBoost、逐流 MLP 基线在同一冻结评价池上测得；"
            "Dijk 2026 表 5 三行为论文原始数字，协议不完全等同，仅作背景参照，"
            "以不同填充图案标出。竖直虚线为随机先验 0.025707。"
        ),
    ),
    FigureSpec(
        stem="图3-6-双机制消融交互",
        width_mm=150,
        height_mm=100,
        draw=draw_interaction,
        json_keys=(
            "cells.*.fap",
            "cells.*.e_lp",
            "cells.*.dr",
        ),
        caption=(
            "图3-6 因果前缀聚合（A）与实体级 Lp 池化（B）的 2×2 消融，在逐流 AP、实体 AP（Lp 池化）与 "
            "DR@4%FPR 三个口径下并列呈现。交互项 Δ = C11 − C10 − C01 + C00；判据一为 Δ > 0（超可加），"
            "判据二为 C11 > max(C01, C10)（组合优于最佳单机制）。三个口径结论不一致："
            "实体 AP（Δ = +0.091268）与 DR@4%FPR（Δ = +0.017287）两条判据均通过，"
            "逐流 AP（Δ = −0.182777）两条判据均不通过。此处如实并列，不作取舍。"
        ),
    ),
    FigureSpec(
        stem="图3-7-训练稳定性",
        width_mm=110,
        height_mm=85,
        draw=draw_stability,
        json_keys=("stability.C00", "stability.C11"),
        caption=(
            "图3-7 基线序列编码器（C00）与完整方法（C11）在种子 42/43/44 下的跨年度逐流 AP。"
            "横线为三种子均值，阴影为 ±1σ（ddof=1）。σ 是协议的属性："
            "本图协议为 20000 步、末 5 检查点平均、顺序执行，σ(C00) = 0.023248、σ(C11) = 0.058622。"
        ),
    ),
    FigureSpec(
        stem="图3-8-Lp指数收敛轨迹",
        width_mm=130,
        height_mm=85,
        draw=draw_lp_exponent,
        json_keys=("cells.C00.p", "cells.C01.p", "cells.C10.p", "cells.C11.p"),
        caption=(
            "图3-8 四格学到的 Lp 池化指数 p 终值。run.log 为顺序执行日志，未记录逐 epoch 轨迹，"
            "故本图只有各格终值，不呈现收敛过程。C00 与 C10 未启用 Lp 池化，p 保持初值 2.0，不参与训练；"
            "C01 收敛到 0.6069、C11 收敛到 1.2236，均落在 p = 1（算术平均）与 p → ∞（上界）之间的内部值。"
        ),
    ),
    FigureSpec(
        stem="图3-9-序列长度敏感性",
        width_mm=130,
        height_mm=85,
        draw=draw_length,
        json_keys=("length.16", "length.32", "length.64", "length.128"),
        caption=(
            "图3-9 序列长度 L 的逐流与实体级 AP（本实验已知存在缺陷，仅作趋势参考，"
            "不支持「长上下文更好」的结论）。缺陷有三：其一，截断实现取固定 L=128 块的前 L 个位置，"
            "逐流覆盖率约 L/128，L=16 时仅约 12.5% 的流被打分；其二，评价集正类基率随 L 改变，"
            "四点分母不同不可直接比较；其三，8000 步固定步数预算下各 L 的训练流量预算最多相差 8 倍。"
        ),
    ),
    FigureSpec(
        stem="图3-10-攻击类别分面",
        width_mm=130,
        height_mm=90,
        draw=draw_facet,
        json_keys=("facet.*",),
        caption=(
            "图3-10 按 Category 字段的攻击类别分面（本实验已知存在缺陷，只作定性参考）。"
            "缺陷有三：其一，Category 字段对恶意流几乎全空，「(空)」类含 519,138 个正例，"
            "占五类正例总数的 99.84%，其余四类各仅 81～452 例；其二，各类按「该类正例 + 全部负例」构造，"
            "评价基率相差数个数量级，(a) 的类内 AP 跨类不可比；其三，(b) 给出 AP / 基率 lift 作为可比口径，"
            "基率按共享负例池折算，负例池由冻结逐流先验 0.025707 与五类正例合计反推。"
            "每类条形上同时标注该类正例数。"
        ),
    ),
    FigureSpec(
        stem="图3-11-受限观测下的检测能力",
        width_mm=140,
        height_mm=95,
        draw=draw_latency_curve,
        json_keys=("curve.C11",),
        caption=(
            "图3-11 完整方法（C11）在每实体只使用按时间前 k 条流时的实体 AP 与 DR@4%FPR，横轴为对数刻度。"
            "实体 AP 从 k=1 的 0.299964 升到使用全部流的 0.462988，DR@4%FPR 从 0.4973 升到 0.6955。"
            "k=50 时用 2.27% 的流即达到全量 AP 的 98.8%（≥95%）。竖直点线标出实体流数中位 = 2："
            "半数实体仅含 2 条流，故 k > 2 的增益主要来自长尾实体。"
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
            kwargs["dpi"] = PNG_DPI
        else:
            kwargs["metadata"] = {"Title": spec.stem, "Creator": "Matplotlib"}
        fig.savefig(path, **kwargs)
        outputs[suffix] = path.name
    plt.close(fig)
    return outputs


def report_values(data: dict[str, Any], log_facts: dict[str, Any]) -> None:
    """逐图打印所用数值与 JSON 键路径，供人工核对。"""

    cells = data["cells"]
    logger.info("=" * 88)
    logger.info("数据源 JSON：%s", JSON_PATH)
    logger.info("数据源 日志：%s", LOG_PATH)
    logger.info("=" * 88)

    logger.info("[图3-5] 键路径 cells.{C00,C01,C10,C11}.fap")
    for cell in CELL_ORDER:
        logger.info("  cells.%s.fap = %.10f  (%s)", cell, cells[cell]["fap"], CELL_NAMES[cell])
    for name, value in EXTERNAL_REFS.items():
        logger.info("  外部参照 %s = %.6f  (来源 tools/ch3_main.py:302-304)", name, value)
    logger.info("  随机先验 = %.10f  (来源 tools/ch3_main.py:282)", FLOW_PRIOR)

    logger.info("[图3-6] 键路径 cells.*.fap / cells.*.e_lp / cells.*.dr")
    for key, label in (("fap", "逐流AP"), ("e_lp", "实体AP(Lp)"), ("dr", "DR@4%FPR")):
        stat = interaction(cells, key)
        logger.info(
            "  %-11s C00=%.6f C01=%.6f C10=%.6f C11=%.6f | A=%+.6f B=%+.6f 和=%+.6f 组合=%+.6f 交互=%+.6f "
            "| 判据一=%s 判据二=%s",
            label,
            stat["C00"],
            stat["C01"],
            stat["C10"],
            stat["C11"],
            stat["A"],
            stat["B"],
            stat["sum"],
            stat["combo"],
            stat["delta"],
            "通过" if stat["crit1"] > 0 else "不通过",
            "通过" if stat["crit2"] > 0 else "不通过",
        )

    logger.info("[图3-7] 键路径 stability.C00 / stability.C11")
    for cell, vals in data["stability"].items():
        arr = np.asarray(vals, dtype=float)
        logger.info(
            "  stability.%s = %s | 均值=%.6f σ(ddof=1)=%.6f",
            cell,
            " ".join(f"{v:.6f}" for v in arr),
            arr.mean(),
            arr.std(ddof=1),
        )

    logger.info("[图3-8] 键路径 cells.*.p；run.log 逐 epoch 轨迹=%s", log_facts["has_trajectory"])
    for cell in CELL_ORDER:
        logger.info("  cells.%s.p = %.10f", cell, cells[cell]["p"])
    for cell, seeds in log_facts["seed_p"].items():
        logger.info("  run.log %s 其他种子 p = %s", cell, {k: f"{v:.4f}" for k, v in sorted(seeds.items())})

    logger.info("[图3-9] 键路径 length.{16,32,64,128} = [逐流AP, 实体AP, p]")
    for key in sorted(data["length"], key=int):
        flow, ent, p = data["length"][key]
        logger.info("  length.%-3s 逐流AP=%.6f 实体AP=%.6f p=%.6f", key, flow, ent, p)

    logger.info("[图3-10] 键路径 facet.* = [AP, 正例数]")
    pos_total = sum(int(v[1]) for v in data["facet"].values())
    n_neg = pos_total * (1.0 - FLOW_PRIOR) / FLOW_PRIOR
    logger.info("  五类正例合计=%d 反推共享负例池=%.0f（由 FLOW_PRIOR=%.10f 折算）", pos_total, n_neg, FLOW_PRIOR)
    for name, (ap, n) in sorted(data["facet"].items(), key=lambda kv: kv[1][1], reverse=True):
        base = n / (n + n_neg)
        logger.info("  facet['%s'] AP=%.8f 正例=%d 基率=%.8f lift=%.3f", name, ap, n, base, ap / base)
    logger.info(
        "  一致性核对：整体 C11 逐流 AP/先验 = %.3f，(空) 类 lift = %.3f",
        cells["C11"]["fap"] / FLOW_PRIOR,
        data["facet"]["(空)"][0] / (data["facet"]["(空)"][1] / (data["facet"]["(空)"][1] + n_neg)),
    )

    logger.info("[图3-11] 键路径 curve.C11 = [k, 实体AP, DR@4%%FPR, 覆盖实体数, 用流占比]")
    full_ap = float(data["curve"]["C11"][-1][1])
    for k, ap, dr, n_ent, cov in data["curve"]["C11"]:
        logger.info(
            "  k=%-5s 实体AP=%.6f DR@4%%FPR=%.4f 覆盖实体=%d 用流占比=%.6f 占全量AP=%.1f%%",
            "全部" if k is None else k,
            ap,
            dr,
            n_ent,
            cov,
            ap / full_ap * 100,
        )
    logger.info("  run.log 第 5 行：实体流数中位=%d", ENTITY_FLOW_MEDIAN)
    logger.info("=" * 88)


def write_manifest(entries: list[dict[str, Any]]) -> None:
    """把本脚本的条目合并进 图件清单.json，保留机制图脚本的既有条目。"""

    manifest: dict[str, Any] = {}
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open(encoding="utf-8") as handle:
            manifest = json.load(handle)

    mine = {e["stem"] for e in entries}
    kept = [e for e in manifest.get("figures", []) if e.get("stem") not in mine and not _is_result_stem(e.get("stem"))]

    generators = manifest.get("generators", [])
    if isinstance(generators, list):
        generators = [g for g in generators if g.get("script") != "绘制第三章结果图.py"]
    else:
        generators = []
    if manifest.get("generator") and manifest["generator"] != "绘制第三章结果图.py":
        generators = [g for g in generators if g.get("script") != manifest["generator"]] + [
            {"script": manifest["generator"], "evidence_mode": manifest.get("evidence_mode", "unknown")}
        ]
    generators.append(
        {
            "script": "绘制第三章结果图.py",
            "evidence_mode": "frozen_experiment_results",
            "data_source_json": str(JSON_PATH.relative_to(REPO)),
            "data_source_log": str(LOG_PATH.relative_to(REPO)),
            "external_reference_source": "thesis/experiments/llm_probe/tools/ch3_main.py:282,302-304",
            "figures": sorted(mine),
        }
    )

    manifest["generators"] = generators
    manifest["python"] = f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}." + str(
        __import__("sys").version_info.micro
    )
    manifest["matplotlib"] = matplotlib.__version__
    manifest["font"] = {"cjk": FONTS["cjk"], "latin": FONTS["latin"], "math": "STIX (mathtext.fontset=stix)"}
    manifest["png_dpi"] = PNG_DPI
    manifest["figures"] = sorted(kept + entries, key=_figure_sort_key)

    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _is_result_stem(stem: str | None) -> bool:
    """判定条目是否落在本脚本负责的 图3-5 ~ 图3-11 编号区间。"""

    if not stem:
        return False
    match = re.match(r"图3-(\d+)-", stem)
    return bool(match) and 5 <= int(match.group(1)) <= 11


def _figure_sort_key(entry: dict[str, Any]) -> tuple[int, str]:
    match = re.match(r"图3-(\d+)-", str(entry.get("stem", "")))
    return (int(match.group(1)) if match else 999, str(entry.get("stem", "")))


def main() -> None:
    data, log_facts = load_sources()
    report_values(data, log_facts)

    entries: list[dict[str, Any]] = []
    for spec in SPECS:
        fig = spec.draw(data, log_facts)
        outputs = save_figure(spec, fig)
        png = ROOT / outputs["png"]
        px_w, px_h = _png_pixels(png)
        entries.append(
            {
                "stem": spec.stem,
                "width_mm": spec.width_mm,
                "height_mm": spec.height_mm,
                "png_dpi": PNG_DPI,
                "png_pixels": [px_w, px_h],
                "json_keys": list(spec.json_keys),
                "caption": spec.caption,
                "outputs": outputs,
            }
        )
        logger.info(
            "已生成 %s：%.0f×%.0f mm，PNG %d×%d px @ %d ppi，键路径 %s",
            spec.stem,
            spec.width_mm,
            spec.height_mm,
            px_w,
            px_h,
            PNG_DPI,
            ", ".join(spec.json_keys),
        )

    write_manifest(entries)
    logger.info("图件清单已更新：%s", MANIFEST_PATH)


def _png_pixels(path: Path) -> tuple[int, int]:
    """读取 PNG 头部的像素尺寸，不引入额外依赖。"""

    raw = path.read_bytes()[16:24]
    return int.from_bytes(raw[0:4], "big"), int.from_bytes(raw[4:8], "big")


if __name__ == "__main__":
    main()
