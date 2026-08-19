"""生成第三章骨干对照图（图3-12：骨干 × 有无机制）。

本脚本同时充当第三章结果图的**渲染管线模板**：数据只从结果 JSON 读取，脚本内不
写死任何实验数值；JSON 带 `placeholder: true` 时强制进入预览模式，产物落独立预览
目录，不覆盖任何既有正式图件，也不改写 `图件清单.json`。

规格来源：仓库根 `AGENTS.md`「学位论文图件合同」（2026-08-13 重定，实测自所对标
学位论文原件）。与 `thesis/chapters/AGENTS.md` 第 31 行的 `155 mm` / `600 dpi` 冲突，
判定与理由见 `.Codex/docs/RWKV/2026-08-18-第三章图件重绘方案.md`。

执行（预览，占位数据）：
    uv run --project thesis/figures/第三章 \
        python thesis/figures/第三章/绘制第三章骨干对照图.py

执行（真数据，产出正式图件）：
    uv run --project thesis/figures/第三章 \
        python thesis/figures/第三章/绘制第三章骨干对照图.py --data <结果JSON路径>
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent

# 在导入 figstyle 之前占位 MPLCONFIGDIR，指向图件目录下的本地缓存。
# figstyle 自 2026-08-19 起默认也指向同一路径，此处保留为防御性设置，两者取值一致。
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplcache"))
(ROOT / ".mplcache").mkdir(parents=True, exist_ok=True)

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import figstyle as fs  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SCHEMA = "ch3-backbone-matrix/v1"
PLACEHOLDER_JSON = ROOT / "占位数据/图3-12-骨干对照-占位.json"
PREVIEW_DIR = ROOT / "预览-占位"
STEM = "图3-12-骨干对照"

WIDTH_MM = 150.0
HEIGHT_MM = 92.0

# 灰度可读：两个系列靠填充明度 + 填充图案 + 边框线型三重区分，颜色只作辅助。
SERIES = (
    {
        "field": "off",
        "display": "无机制参照",
        "face": "#FFFFFF",
        "gray": 1.00,
        "hatch": "",
        "edge": fs.INK,
        "linestyle": "-",
    },
    {
        "field": "on",
        "display": "CPA-ELP",
        "face": "#7C8B95",
        "gray": 0.55,
        "hatch": "///",
        "edge": fs.INK,
        "linestyle": "-",
    },
)

PANELS = (
    {"field": "entity_ap", "title": "(a) 实体平均精确率", "random": "entity_ap_random"},
    {"field": "dr_at_4fpr", "title": "(b) DR@4%FPR", "random": "dr_at_4fpr_random"},
)


# ---------------------------------------------------------------- 数据契约


@dataclass(frozen=True)
class Backbone:
    """一行骨干的两格取值。全部取值为 0 至 1 的比例，不是百分数。"""

    key: str
    display: str
    values: dict[str, dict[str, float]]


@dataclass(frozen=True)
class Payload:
    placeholder: bool
    baselines: dict[str, float]
    provenance: dict[str, Any]
    backbones: tuple[Backbone, ...]
    source: Path


def load_payload(path: Path) -> Payload:
    """读取结果 JSON 并逐项校验契约，缺字段直接报错，不做默认填充。"""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error("结果 JSON 不存在：%s", path)
        raise
    except json.JSONDecodeError:
        logger.error("结果 JSON 解析失败：%s", path)
        raise

    if raw.get("schema") != SCHEMA:
        raise ValueError(f"schema 必须为 {SCHEMA}，实得 {raw.get('schema')!r}：{path}")
    if raw.get("metric_scale") != "ratio":
        raise ValueError(f"metric_scale 必须为 ratio（0 至 1），实得 {raw.get('metric_scale')!r}")

    entries = raw.get("backbones")
    if not isinstance(entries, list) or len(entries) != 5:
        raise ValueError(f"backbones 必须为 5 行，实得 {len(entries) if entries else 0} 行")

    backbones: list[Backbone] = []
    for entry in entries:
        values: dict[str, dict[str, float]] = {}
        for panel in PANELS:
            field = str(panel["field"])
            cell = entry.get(field)
            if not isinstance(cell, dict):
                raise ValueError(f"骨干 {entry.get('key')!r} 缺字段 {field}")
            pair: dict[str, float] = {}
            for series in SERIES:
                name = str(series["field"])
                if name not in cell:
                    raise ValueError(f"骨干 {entry.get('key')!r} 的 {field} 缺 {name} 格")
                value = float(cell[name])
                if not 0.0 <= value <= 1.0:
                    raise ValueError(f"{entry.get('key')}.{field}.{name} = {value} 越出 [0, 1]")
                pair[name] = value
            values[field] = pair
        backbones.append(
            Backbone(key=str(entry["key"]), display=str(entry["display"]), values=values)
        )

    baselines = {k: float(v) for k, v in (raw.get("baselines") or {}).items()}
    for panel in PANELS:
        key = str(panel["random"])
        if key not in baselines:
            raise ValueError(f"baselines 缺随机基线 {key}")

    return Payload(
        placeholder=bool(raw.get("placeholder", False)),
        baselines=baselines,
        provenance=raw.get("provenance") or {},
        backbones=tuple(backbones),
        source=path,
    )


# ---------------------------------------------------------------- 绘图


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def draw_panel(ax, payload: Payload, panel: dict[str, Any]) -> None:
    """一块面板：五行骨干、每行两条水平条，右侧标注机制增益。"""

    field = str(panel["field"])
    # barh 自下而上排列，反转后 JSON 中的第一行落在图的最上方，与表的行序一致。
    rows = list(reversed(payload.backbones))
    n = len(rows)
    y_base = np.arange(n, dtype=float)
    height = 0.34

    peak = max(row.values[field][str(s["field"])] for row in rows for s in SERIES)
    limit = min(1.0, peak * 1.42)

    for offset, series in zip((height / 2.0, -height / 2.0), SERIES, strict=True):
        name = str(series["field"])
        widths = [row.values[field][name] for row in rows]
        ax.barh(
            y_base + offset,
            widths,
            height=height,
            facecolor=str(series["face"]),
            edgecolor=str(series["edge"]),
            linewidth=fs.AUX_LINE_PT + 0.2,
            linestyle=str(series["linestyle"]),
            hatch=str(series["hatch"]) or None,
            label=fs.checked(str(series["display"]), fs.MIN_FONT_PT),
            zorder=3,
        )
        for y, width in zip(y_base + offset, widths, strict=True):
            ax.text(
                width + limit * 0.012,
                y,
                fs.checked(_pct(width), fs.MIN_FONT_PT),
                va="center",
                ha="left",
                size=fs.MIN_FONT_PT,
                color=fs.INK,
                zorder=5,
            )

    # 机制增益：正为提升，负为下降；灰度下靠三角朝向而非颜色区分。
    for y, row in zip(y_base, rows, strict=True):
        delta = row.values[field]["on"] - row.values[field]["off"]
        marker = "▲" if delta > 0 else ("▼" if delta < 0 else "＝")
        ax.text(
            limit * 0.995,
            y,
            fs.checked(f"{marker} {abs(delta) * 100:.2f}", fs.MIN_FONT_PT),
            va="center",
            ha="right",
            size=fs.MIN_FONT_PT,
            color=fs.MUTED,
            zorder=5,
        )

    random_value = payload.baselines[str(panel["random"])]
    ax.axvline(
        random_value,
        color=fs.MUTED,
        linewidth=fs.AUX_LINE_PT + 0.2,
        linestyle=(0, (4, 2)),
        zorder=2,
    )
    # 基线标注贴底放置：竖排放在顶端会压到第一行的骨干名。
    ax.text(
        random_value + limit * 0.015,
        -0.56,
        fs.checked(f"随机基线 {_pct(random_value)}", fs.MIN_FONT_PT),
        va="bottom",
        ha="left",
        size=fs.MIN_FONT_PT,
        color=fs.MUTED,
        zorder=5,
    )

    ax.set_yticks(y_base)
    ax.set_yticklabels([fs.checked(row.display, fs.MIN_FONT_PT) for row in rows])
    ax.set_ylim(-0.62, n - 0.38)
    ax.set_xlim(0.0, limit)
    ax.set_xlabel(fs.checked("取值", fs.MIN_FONT_PT), size=fs.MIN_FONT_PT, labelpad=2.0)
    ax.set_title(
        fs.checked(str(panel["title"]), fs.MAIN_FONT_PT),
        size=fs.MAIN_FONT_PT,
        color=fs.INK,
        pad=4.0,
    )
    ax.xaxis.set_major_formatter(lambda v, _pos: f"{v * 100:.0f}%")
    ax.tick_params(labelsize=fs.MIN_FONT_PT, length=2.0, pad=1.5)
    ax.grid(axis="x", color=fs.HAIRLINE, linewidth=fs.AUX_LINE_PT, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(fs.RULE)


def render(payload: Payload, out_dir: Path, stem: str) -> dict[str, Path]:
    fig = plt.figure(
        figsize=(fs.mm_to_inch(WIDTH_MM), fs.mm_to_inch(HEIGHT_MM)),
        dpi=200,
    )
    axes = fig.subplots(1, 2)
    for ax, panel in zip(axes, PANELS, strict=True):
        draw_panel(ax, payload, panel)
    axes[1].set_ylabel("")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncols=len(SERIES),
        frameon=False,
        fontsize=fs.MIN_FONT_PT,
        bbox_to_anchor=(0.5, 0.005),
        handlelength=2.0,
        columnspacing=2.4,
    )
    fig.subplots_adjust(left=0.10, right=0.985, top=0.92, bottom=0.16, wspace=0.30)

    if payload.placeholder:
        fig.text(
            0.5,
            0.5,
            "占位数据",
            size=34.0,
            color="#C8C8C8",
            ha="center",
            va="center",
            rotation=28.0,
            alpha=0.55,
            zorder=20,
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for suffix in ("svg", "pdf", "png"):
        path = out_dir / f"{stem}.{suffix}"
        kwargs: dict[str, Any] = {"format": suffix, "facecolor": fs.WHITE, "edgecolor": "none"}
        if suffix == "png":
            kwargs["dpi"] = fs.PNG_DPI
        fig.savefig(path, **kwargs)
        written[suffix] = path
    plt.close(fig)
    return written


# ---------------------------------------------------------------- 自检


def check_contract(written: dict[str, Path]) -> list[str]:
    """尺寸、分辨率、字体、灰度可读性的机器自检，任何一项不过直接报错。"""

    from PIL import Image

    report: list[str] = []

    if WIDTH_MM > fs.MAX_WIDTH_MM:
        raise ValueError(f"宽度 {WIDTH_MM} mm 超过合同上限 {fs.MAX_WIDTH_MM} mm")
    if HEIGHT_MM > fs.MAX_HEIGHT_MM:
        raise ValueError(f"高度 {HEIGHT_MM} mm 超过合同上限 {fs.MAX_HEIGHT_MM} mm")
    report.append(f"版面：{WIDTH_MM:g} mm × {HEIGHT_MM:g} mm（上限 165 × 140 mm）")

    with Image.open(written["png"]) as image:
        px_w, px_h = image.size
        gray = image.convert("L")
    ppi_w = px_w / (WIDTH_MM / 25.4)
    ppi_h = px_h / (HEIGHT_MM / 25.4)
    if min(ppi_w, ppi_h) < 300.0 - 1e-6:
        raise ValueError(f"实测 ppi {min(ppi_w, ppi_h):.1f} 低于合同下限 300")
    report.append(f"PNG：{px_w}×{px_h} px，实测 {ppi_w:.1f}×{ppi_h:.1f} ppi（下限 300，推荐 400）")

    if not written["pdf"].read_bytes().startswith(b"%PDF"):
        raise ValueError("PDF 文件头无效")
    from xml.etree import ElementTree

    ElementTree.parse(written["svg"])
    report.append("矢量：PDF 文件头有效，SVG 可解析")

    report.append(
        f"中文字体：请求 {fs.CJK_FONT.requested}，实用 {fs.CJK_FONT.family}"
        f"（{fs.CJK_FONT.path}#{fs.CJK_FONT.face_index}）"
    )
    report.append(f"西文字体：{fs.LATIN_FONT.family}（{fs.LATIN_FONT.path}）")
    report.append(f"数学字体：mathtext.fontset = {plt.rcParams['mathtext.fontset']}")
    report.append(f"字号：最小 {fs.MIN_FONT_PT:g} pt，主标注 {fs.MAIN_FONT_PT:g} pt（逐条标签已断言）")

    # 灰度可读性：两个系列的填充明度差与填充图案必须同时可区分。
    grays = [float(s["gray"]) for s in SERIES]
    hatches = [str(s["hatch"]) for s in SERIES]
    span = max(grays) - min(grays)
    if span < 0.25:
        raise ValueError(f"两系列填充明度差 {span:.2f} 不足 0.25，灰度下不可区分")
    if len(set(hatches)) != len(hatches):
        raise ValueError("两系列填充图案相同，灰度下不可区分")
    report.append(
        f"灰度：填充明度差 {span:.2f}（≥0.25），填充图案 {hatches!r} 互不相同，"
        "增益方向另用 ▲▼ 标出，不依赖颜色"
    )

    gray_path = written["png"].with_name(written["png"].stem + "-灰度.png")
    gray.save(gray_path, dpi=(fs.PNG_DPI, fs.PNG_DPI))
    report.append(f"灰度自检副本：{gray_path}（肉眼核对用，不作正式交付）")

    return report


# ---------------------------------------------------------------- 入口


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="绘制第三章图3-12 骨干对照图")
    parser.add_argument(
        "--data",
        type=Path,
        default=PLACEHOLDER_JSON,
        help="结果 JSON 路径，默认使用占位数据",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="输出目录，默认由数据是否为占位自动决定",
    )
    args = parser.parse_args(argv)

    payload = load_payload(args.data)
    out_dir = args.out or (PREVIEW_DIR if payload.placeholder else ROOT)

    if payload.placeholder and out_dir == ROOT:
        raise ValueError("占位数据不得写入正式图件目录")

    written = render(payload, out_dir, STEM)
    for line in check_contract(written):
        logger.info("  %s", line)

    logger.info("数据来源：%s（placeholder=%s）", payload.source, payload.placeholder)
    for key, value in payload.provenance.items():
        logger.info("  溯源 %s：%s", key, value)
    for suffix, path in written.items():
        logger.info("产物 %s：%s", suffix, path)
    if payload.placeholder:
        logger.warning(
            "占位模式：图内已打「占位数据」水印，产物只落 %s，未写 图件清单.json，"
            "不得引用进正文。",
            out_dir,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
