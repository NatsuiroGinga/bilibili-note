"""第三章图件的样式与工程基础设施。

职责边界：本模块只提供字体解析、版面换算、绘图原语、多格式导出、图件清单写出
和交付自检，不含任何图件内容与实验数据。

规格来源：仓库根 `AGENTS.md`「学位论文图件合同」（2026-08-13 重定，实测自朱焱雷
学位论文原件）。
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Sequence
from xml.etree import ElementTree

MPL_CACHE = Path("/tmp/chapter3-matplotlib-cache")
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib import font_manager, ft2font
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

# ---------------------------------------------------------------- 图件合同常量

MAX_WIDTH_MM = 165.0
MAX_HEIGHT_MM = 140.0
PNG_DPI = 400
MIN_FONT_PT = 8.0
MAIN_FONT_PT = 9.0
MAIN_LINE_PT = 1.0
AUX_LINE_PT = 0.5

# 灰度可读配色：区分依靠填充图案与线型，颜色只作辅助。
INK = "#1F1F1F"
MUTED = "#555555"
RULE = "#8C8C8C"
HAIRLINE = "#BFBFBF"
WHITE = "#FFFFFF"
SHADE = "#F1F1F1"
M1_EDGE = "#2F6B9A"
M1_FACE = "#EDF3F8"
M1_HATCH = "///"
M2_EDGE = "#B3512E"
M2_FACE = "#FAEFEA"
M2_HATCH = "\\\\\\"

# ---------------------------------------------------------------- 字体解析

# Office 随附字体目录。本机装有 Microsoft Office，SimHei、Cambria（含 Cambria Math）
# 与 Simsun 均在此，不在 /Library/Fonts 等系统目录下。2026-08-18 实测：只查系统三处
# 会误判为「未安装」并静默回退到 Heiti SC 与 stix，故把该目录置于候选首位。
# 这些字体随 Office 授权在本机可用，此处只按路径注册，不复制、不安装、不改系统设置。
_OFFICE_FONTS = Path("/Applications/Microsoft Word.app/Contents/Resources/DFonts")

# 中文黑体候选：合同要求 SimHei，取不到时按顺序回退。
# 每项为 (展示名, 文件路径)；实际可用性由 `_font_covers` 逐字核验，不做假设。
CJK_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("SimHei", str(_OFFICE_FONTS / "SimHei.ttf")),
    ("SimHei", "/Library/Fonts/SimHei.ttf"),
    ("SimHei", str(Path.home() / "Library/Fonts/SimHei.ttf")),
    ("Heiti SC", "/System/Library/Fonts/STHeiti Medium.ttc"),
    ("PingFang SC", "/System/Library/Fonts/PingFang.ttc"),
    ("Hiragino Sans GB", "/System/Library/Fonts/Hiragino Sans GB.ttc"),
)

LATIN_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("Times New Roman", "/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
    ("Times New Roman", str(_OFFICE_FONTS / "Times New Roman.ttf")),
    ("Times New Roman", "/Library/Fonts/Times New Roman.ttf"),
    ("Times", "/System/Library/Fonts/Times.ttc"),
)

# 数学字体候选：合同要求 Cambria Math，它在 Office 的 Cambria.ttc 内。
MATH_CANDIDATES: tuple[tuple[str, str], ...] = (
    ("Cambria Math", str(_OFFICE_FONTS / "Cambria.ttc")),
    ("Cambria Math", "/Library/Fonts/Cambria.ttc"),
)

# 字体筛选探针：简体常用字加全角标点，逐字核验，不做假设。
# 更强的完整性由 `check_label` 对每一条实际标签逐字断言保证。
CJK_PROBE = "实体级可学池化因果前缀聚合掩码构造归并示意骨化分聚层侧机制流序列键（）、"

_CJK_RANGE = re.compile(
    r"[⺀-〿㈀-鿿豈-﫿︰-﹏＀-￯]"
)


def _iter_faces(path: str):
    """遍历集合字体（.ttc）内的每一个子字体面。"""

    if not Path(path).exists():
        return
    index = 0
    while True:
        try:
            face = ft2font.FT2Font(path, face_index=index)
        except (RuntimeError, OSError, TypeError):
            return
        yield index, face
        index += 1
        if index >= face.num_faces:
            return


def _covers(face: ft2font.FT2Font, probe: str) -> list[str]:
    charmap = face.get_charmap()
    return sorted({c for c in probe if ord(c) not in charmap})


@dataclass(frozen=True)
class FontChoice:
    family: str
    path: str
    face_index: int
    requested: str


def resolve_cjk_font() -> FontChoice:
    """选出确实存在且覆盖全部用字的中文黑体，失败即报错，不静默降级。"""

    tried: list[str] = []
    for requested, path in CJK_CANDIDATES:
        if not Path(path).exists():
            tried.append(f"{path}（文件不存在）")
            continue
        for index, face in _iter_faces(path):
            family = face.family_name
            if requested == "Heiti SC" and family != "Heiti SC":
                continue
            if requested == "PingFang SC" and family != "PingFang SC":
                continue
            missing = _covers(face, CJK_PROBE)
            if missing:
                tried.append(f"{path}#{index}（{family} 缺字 {len(missing)} 个）")
                continue
            font_manager.fontManager.addfont(path)
            return FontChoice(family, path, index, requested)
    raise FileNotFoundError("未找到覆盖全部用字的中文黑体，尝试过：" + "；".join(tried))


def resolve_latin_font() -> FontChoice:
    tried: list[str] = []
    for requested, path in LATIN_CANDIDATES:
        if not Path(path).exists():
            tried.append(f"{path}（文件不存在）")
            continue
        for index, face in _iter_faces(path):
            family = face.family_name
            if family != requested:
                continue
            font_manager.fontManager.addfont(path)
            return FontChoice(family, path, index, requested)
    raise FileNotFoundError("未找到西文正文字体，尝试过：" + "；".join(tried))


def resolve_math_font() -> FontChoice | None:
    """解析数学字体。取不到时返回 None，由调用方回退到 mathtext 内置字集。"""

    for requested, path in MATH_CANDIDATES:
        if not Path(path).exists():
            continue
        for index, face in _iter_faces(path):
            if face.family_name != requested:
                continue
            font_manager.fontManager.addfont(path)
            return FontChoice(face.family_name, path, index, requested)
    return None


CJK_FONT = resolve_cjk_font()
LATIN_FONT = resolve_latin_font()
MATH_FONT = resolve_math_font()


def _coverage() -> frozenset[int]:
    """两种正文字体的码位并集，用于逐字断言标签可渲染。"""

    codes: set[int] = set()
    for choice in (CJK_FONT, LATIN_FONT):
        face = ft2font.FT2Font(choice.path, face_index=choice.face_index)
        codes.update(face.get_charmap().keys())
    return frozenset(codes)


COVERAGE = _coverage()

# 字体回退链：西文与数字取 Times New Roman，汉字回退到黑体。
plt.rcParams.update(
    {
        "font.family": [LATIN_FONT.family, CJK_FONT.family],
        "font.size": MIN_FONT_PT,
        "axes.unicode_minus": False,
        # 合同要求数学符号用 Cambria Math。取到则走 custom 字集把它接进来，
        # 取不到才回退 stix；回退情形由 describe_fonts 显式记录，不静默替换。
        **(
            {
                "mathtext.fontset": "custom",
                "mathtext.rm": MATH_FONT.family,
                "mathtext.it": f"{MATH_FONT.family}:italic",
                "mathtext.bf": f"{MATH_FONT.family}:bold",
                "mathtext.default": "it",
            }
            if MATH_FONT is not None
            else {"mathtext.fontset": "stix"}
        ),
        "hatch.linewidth": AUX_LINE_PT,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.facecolor": WHITE,
        "savefig.facecolor": WHITE,
        "savefig.transparent": False,
        "axes.linewidth": 0.7,
        "xtick.labelsize": MIN_FONT_PT,
        "ytick.labelsize": MIN_FONT_PT,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
    }
)


# ---------------------------------------------------------------- 版面换算


def mm_to_inch(value: float) -> float:
    return value / 25.4


@dataclass
class Canvas:
    """归一化坐标画布：x 覆盖整幅宽度，y 覆盖整幅高度。"""

    fig: Figure
    ax: Axes
    width_mm: float
    height_mm: float

    def pt_x(self, pt: float) -> float:
        """磅值换算为横向归一化长度。"""
        return pt / 72.0 * 25.4 / self.width_mm

    def pt_y(self, pt: float) -> float:
        """磅值换算为纵向归一化长度。"""
        return pt / 72.0 * 25.4 / self.height_mm

    def square_dy(self, dx: float) -> float:
        """给定横向长度，返回等物理长度的纵向长度。"""
        return dx * self.width_mm / self.height_mm


def canvas(width_mm: float, height_mm: float) -> Canvas:
    if width_mm > MAX_WIDTH_MM:
        raise ValueError(f"宽度 {width_mm} mm 超过合同上限 {MAX_WIDTH_MM} mm")
    if height_mm > MAX_HEIGHT_MM:
        raise ValueError(f"高度 {height_mm} mm 超过合同上限 {MAX_HEIGHT_MM} mm")
    fig = plt.figure(figsize=(mm_to_inch(width_mm), mm_to_inch(height_mm)), dpi=200)
    ax = fig.add_axes((0.0, 0.0, 1.0, 1.0))
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")
    return Canvas(fig, ax, width_mm, height_mm)


# ---------------------------------------------------------------- 文本原语


def check_label(value: str, size: float) -> None:
    """交付前置断言：字号下限、数学模式隔离、逐字字形覆盖。

    matplotlib 会把含有成对 `$` 的整条字符串交给 mathtext 解析，而 STIX 数学
    字体不含汉字，混排必然产生豆腐块。数学串因此限定为纯 ASCII；非数学串逐字
    核对两种正文字体的码位并集，任何缺字直接报错，不等到出图后肉眼发现。
    """

    if size < MIN_FONT_PT - 1e-9:
        raise ValueError(f"字号 {size} pt 低于合同下限 {MIN_FONT_PT} pt：{value!r}")
    if "$" in value:
        if _CJK_RANGE.search(value) or not value.isascii():
            raise ValueError(f"数学模式串必须为纯 ASCII，不得混入汉字：{value!r}")
        return
    missing = sorted({c for c in value if c not in " \n" and ord(c) not in COVERAGE})
    if missing:
        raise ValueError(f"字体缺少字形 {missing}，会渲染成豆腐块：{value!r}")


def checked(value: str, size: float = MIN_FONT_PT) -> str:
    """直接调用 matplotlib 坐标轴接口时，用它套一层同样的断言。"""

    check_label(value, size)
    return value


def text(
    cv: Canvas,
    x: float,
    y: float,
    value: str,
    *,
    size: float = MIN_FONT_PT,
    color: str = INK,
    ha: str = "center",
    va: str = "center",
    rotation: float = 0.0,
    linespacing: float = 1.45,
    zorder: int = 10,
) -> None:
    check_label(value, size)
    cv.ax.text(
        x,
        y,
        value,
        size=size,
        color=color,
        ha=ha,
        va=va,
        rotation=rotation,
        linespacing=linespacing,
        zorder=zorder,
    )


@dataclass(frozen=True)
class Line:
    """盒内一行文字。`kind` 为 `cjk` 时按正文族排版，为 `math` 时走 mathtext。

    这里不提供加粗：SimHei 与其 macOS 回退 Heiti SC 均无粗体字面，请求加粗只会
    退回常规字重并产生 findfont 警告。层级改由字号（主标注 9 pt、次级 8 pt）与
    颜色区分，与图件合同的字号规定一致。
    """

    value: str
    size: float = MIN_FONT_PT
    kind: Literal["cjk", "math"] = "cjk"
    color: str = INK
    # 行高倍数。分式、求和号等高身公式必须显式加大，否则会压到相邻行。
    span: float | None = None


def stack(cv: Canvas, cx: float, cy: float, lines: Sequence[Line]) -> None:
    """把若干行文字在给定中心处垂直居中堆叠。"""

    heights = [
        cv.pt_y(
            line.size
            * (line.span if line.span is not None else (1.9 if line.kind == "math" else 1.55))
        )
        for line in lines
    ]
    total = sum(heights)
    top = cy + total / 2.0
    for line, height in zip(lines, heights, strict=True):
        text(
            cv,
            cx,
            top - height / 2.0,
            line.value,
            size=line.size,
            color=line.color,
        )
        top -= height


# ---------------------------------------------------------------- 形状原语


def box(
    cv: Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    lines: Sequence[Line] = (),
    *,
    face: str = WHITE,
    edge: str = MUTED,
    linewidth: float = MAIN_LINE_PT,
    linestyle: str | tuple = "-",
    hatch: str | None = None,
    hatch_color: str | None = None,
    radius: float = 0.010,
    zorder: int = 3,
) -> None:
    """圆角盒。给出 `hatch` 时，填充图案与描边分层绘制。

    matplotlib 的填充图案与描边共用 `edgecolor`，直接开图案会让盒线颜色的斜线
    压住盒内文字。这里先用浅色画一层图案填充，再单独画描边，保证灰度下仍有纹理
    区分，同时不牺牲文字可读性。
    """

    style = f"round,pad=0.004,rounding_size={radius}"
    if hatch:
        cv.ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle=style,
                linewidth=0.0,
                edgecolor=hatch_color or edge,
                facecolor=face,
                hatch=hatch,
                zorder=zorder,
            )
        )
    cv.ax.add_patch(
        FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle=style,
            linewidth=linewidth,
            linestyle=linestyle,
            edgecolor=edge,
            facecolor="none" if hatch else face,
            zorder=zorder + 1,
        )
    )
    if lines:
        stack(cv, x + width / 2.0, y + height / 2.0, lines)


def cell(
    cv: Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    face: str = WHITE,
    edge: str = RULE,
    linewidth: float = AUX_LINE_PT,
    hatch: str | None = None,
    zorder: int = 3,
) -> None:
    cv.ax.add_patch(
        Rectangle(
            (x, y),
            width,
            height,
            facecolor=face,
            edgecolor=edge,
            linewidth=linewidth,
            hatch=hatch,
            zorder=zorder,
        )
    )


def pill(
    cv: Canvas,
    cx: float,
    cy: float,
    width: float,
    height: float,
    label: str,
    *,
    face: str = SHADE,
    edge: str = RULE,
    color: str = INK,
    size: float = MIN_FONT_PT,
) -> None:
    box(
        cv,
        cx - width / 2.0,
        cy - height / 2.0,
        width,
        height,
        (Line(label, size, "cjk", color),),
        face=face,
        edge=edge,
        linewidth=0.8,
        radius=height / 2.0,
        zorder=6,
    )


def arrow(
    cv: Canvas,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = INK,
    linewidth: float = MAIN_LINE_PT,
    linestyle: str | tuple = "-",
    head: float = 7.0,
    connectionstyle: str = "arc3,rad=0",
    zorder: int = 5,
) -> None:
    cv.ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=head,
            linewidth=linewidth,
            linestyle=linestyle,
            color=color,
            connectionstyle=connectionstyle,
            shrinkA=0.0,
            shrinkB=0.0,
            zorder=zorder,
        )
    )


def polyline(
    cv: Canvas,
    points: Sequence[tuple[float, float]],
    *,
    color: str = INK,
    linewidth: float = MAIN_LINE_PT,
    linestyle: str | tuple = "-",
    zorder: int = 4,
) -> None:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    cv.ax.plot(
        xs,
        ys,
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
        solid_capstyle="round",
        zorder=zorder,
    )


def routed_arrow(
    cv: Canvas,
    points: Sequence[tuple[float, float]],
    *,
    color: str = INK,
    linewidth: float = MAIN_LINE_PT,
    linestyle: str | tuple = "-",
) -> None:
    """折线走线，末段带箭头。用于跨行换行的数据流。"""

    polyline(cv, points[:-1], color=color, linewidth=linewidth, linestyle=linestyle)
    arrow(
        cv,
        points[-2],
        points[-1],
        color=color,
        linewidth=linewidth,
        linestyle=linestyle,
    )


def panel(
    cv: Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    *,
    title_size: float = MAIN_FONT_PT,
) -> None:
    box(
        cv,
        x,
        y,
        width,
        height,
        face="#FBFBFB",
        edge=HAIRLINE,
        linewidth=0.7,
        radius=0.012,
        zorder=1,
    )
    text(
        cv,
        x + 0.014,
        y + height - cv.pt_y(title_size * 1.3),
        title,
        size=title_size,
        color=INK,
        ha="left",
    )


def footnote(cv: Canvas, value: str, y: float = 0.028) -> None:
    text(cv, 0.5, y, value, size=MIN_FONT_PT, color=MUTED)


# ---------------------------------------------------------------- 导出与自检


@dataclass
class FigureSpec:
    stem: str
    width_mm: float
    height_mm: float
    draw: object
    caption: str = ""
    outputs: dict[str, str] = field(default_factory=dict)


def save_figure(root: Path, spec: FigureSpec, cv: Canvas) -> dict[str, object]:
    outputs: dict[str, str] = {}
    for suffix in ("svg", "pdf", "png"):
        path = root / f"{spec.stem}.{suffix}"
        kwargs: dict[str, object] = {
            "format": suffix,
            "facecolor": WHITE,
            "edgecolor": "none",
            "bbox_inches": None,
            "pad_inches": 0,
        }
        if suffix == "png":
            kwargs["dpi"] = PNG_DPI
        else:
            kwargs["metadata"] = {"Title": spec.stem, "Creator": "Matplotlib"}
        cv.fig.savefig(path, **kwargs)
        outputs[suffix] = path.name
    plt.close(cv.fig)
    return {
        "stem": spec.stem,
        "caption": spec.caption,
        "width_mm": round(spec.width_mm, 2),
        "height_mm": round(spec.height_mm, 2),
        "png_dpi": PNG_DPI,
        "outputs": outputs,
    }


def verify_outputs(root: Path, entries: list[dict[str, object]]) -> list[str]:
    """核对三种格式可解析，并回报 PNG 实测像素与实测 ppi。"""

    from PIL import Image

    report: list[str] = []
    for entry in entries:
        outputs = entry["outputs"]
        assert isinstance(outputs, dict)
        ElementTree.parse(root / outputs["svg"])
        pdf_path = root / outputs["pdf"]
        if not pdf_path.read_bytes().startswith(b"%PDF"):
            raise ValueError(f"PDF 文件头无效：{pdf_path}")
        png_path = root / outputs["png"]
        with Image.open(png_path) as image:
            image.verify()
        with Image.open(png_path) as image:
            px_w, px_h = image.size
        width_mm = float(entry["width_mm"])
        height_mm = float(entry["height_mm"])
        ppi_w = px_w / (width_mm / 25.4)
        ppi_h = px_h / (height_mm / 25.4)
        if min(ppi_w, ppi_h) < 300.0 - 1e-6:
            raise ValueError(f"{entry['stem']} 实测 ppi {ppi_w:.1f} 低于 300")
        entry["png_pixels"] = [px_w, px_h]
        entry["png_ppi_measured"] = [round(ppi_w, 1), round(ppi_h, 1)]
        report.append(
            f"{entry['stem']}: {width_mm:g} mm × {height_mm:g} mm, "
            f"PNG {px_w}×{px_h} px, 实测 {ppi_w:.1f}×{ppi_h:.1f} ppi"
        )
    return report


def write_manifest(
    root: Path,
    generator: str,
    entries: list[dict[str, object]],
    *,
    evidence_mode: str,
) -> Path:
    """重写图件清单：保留仍然存在的其他图件条目，替换本次生成的条目。"""

    path = root / "图件清单.json"
    kept: list[dict[str, object]] = []
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        stems = {entry["stem"] for entry in entries}
        for entry in previous.get("figures", []):
            if entry.get("stem") in stems:
                continue
            outputs = entry.get("outputs", {})
            if outputs and all((root / name).exists() for name in outputs.values()):
                kept.append(entry)

    import PIL

    for entry in entries:
        entry["evidence_mode"] = evidence_mode

    manifest = {
        "contract": "AGENTS.md 学位论文图件合同（2026-08-13 重定）",
        "environment": {
            "generator": generator,
            "python": ".".join(str(v) for v in sys.version_info[:3]),
            "matplotlib": matplotlib.__version__,
            "pillow": PIL.__version__,
        },
        "typography": {
            "cjk_font_requested": CJK_FONT.requested,
            "cjk_font_used": CJK_FONT.family,
            "cjk_font_path": CJK_FONT.path,
            "cjk_face_index": CJK_FONT.face_index,
            "latin_font_used": LATIN_FONT.family,
            "latin_font_path": LATIN_FONT.path,
            "math_fontset": "stix",
            "min_font_pt": MIN_FONT_PT,
            "main_font_pt": MAIN_FONT_PT,
            "main_line_pt": MAIN_LINE_PT,
            "aux_line_pt": AUX_LINE_PT,
        },
        "grayscale_readable": True,
        "figures": sorted(kept + entries, key=lambda item: str(item["stem"])),
    }
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path
