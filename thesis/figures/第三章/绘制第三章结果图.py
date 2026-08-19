"""生成第三章五张实验结果图（图3-6、图3-8、图3-9、图3-11、图3-12）。

2026-08-18 重绘。原图3-5 ~ 图3-11 七幅与正文冲突，已裁决以正文为准重绘图件：正文
数字是基准，一个不许改；图跟数据走，不得为对齐图面改动任何数值。本脚本据此只保留
承担论证增量、且数据能追溯到本机制品的四幅重绘图，加上不在冲突之列的图3-12。撤下
三幅的理由见 WITHDRAWN 常量，同时写进 图件清单.json：
  图3-5  六方法三指标共 18 个数与表 3-7 逐格重复，且随机森林、发表配置一维卷积网络
         与发表配置门控循环网络三行在本机没有结果制品，无法记录数据来源键路径。
  图3-7  全图只承载六个标量，正文已逐一写出；其完整方法一组与图3-9 第 128 档同源。
  图3-10 七行两指标共 14 个点估计全部落在表 3-6 内，且该子集只占全部正例的 0.164%，
         正文自身两度限定其读法，单独配图会抬高它在读者视觉里的权重。

每幅图绘制前先用本机制品复现正文印刷读数，任何一项超差立即报错停止，不画图。

各图数据源（互相独立，不得混用）：
  图3-6  五个骨干的 2×2 实体平均精确率
         diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json          （多层感知机）
         diagnostics/ch3-backbone-protocolA-v2/{cnn,transformer,gru}/
           ch3_backbone_protocolA_results.json                             （三个神经骨干）
         diagnostics/ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2/
           xgb_cpa_elp_results.json                                        （树集成）
         判读带宽由 diagnostics/ch3-full/ch3_full_results.json 的 stability.C11 极差算出
  图3-8  diagnostics/ch3-2x2-fairsel/ch3_2x2_fairsel_results.json 的 selection.*.val_ap_history
  图3-9  四档长度的逐流读数取自 .Codex/docs/RWKV/2026-08-17-第三章XGBoost基线对照与门槛
         测算.md 第九节（产出该实验的运行目录未同步到本机）；第 128 档与 ch3-full 的
         stability.C11 交叉核对，核对不过即报错
  图3-11 diagnostics/ch3-full/ch3_full_results.json 的 curve.C11
  图3-12 diagnostics/dijk-repro/cache/{ent24_local.npy,y24.npy} 与
         diagnostics/ch3-alert-budget-curve/{entity_scores.npy,entity_scores_rows.json,
         alert_budget_curves.json}，详见 load_alert_budget_curve()

字体、版面上限、导出与实测 ppi 自检一律由 figstyle 提供，本文件不硬编码字体路径。
输出 PNG(400 ppi) + PDF + SVG，落 thesis/figures/第三章/，条目合并进 图件清单.json。
执行：uv run --no-sync --project thesis/figures/第三章 python thesis/figures/第三章/绘制第三章结果图.py
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# figstyle 负责字体解析（SimHei / Times New Roman / Cambria Math）、合同常量与交付自检。
# 导入即完成 matplotlib 后端与字体链设置，本文件不得再覆盖 font.family 与 mathtext.*。
import figstyle as fs
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REPO = ROOT.parents[2]
DIAG = REPO / "thesis/experiments/llm_probe/runs/diagnostics"
MANIFEST_PATH = ROOT / "图件清单.json"

# 旧协议运行：图3-11 的受限观测曲线、图3-9 的第 128 档交叉核对、图3-6 的判读带宽都取自这里
FULL_PATH = DIAG / "ch3-full/ch3_full_results.json"
# 图3-6、图3-8 的主口径运行：公平选择协议下的 2×2 四格（多层感知机骨干）
FAIRSEL_PATH = DIAG / "ch3-2x2-fairsel/ch3_2x2_fairsel_results.json"
# 图3-6 的另外三个神经骨干（协议 A 第二版）与树集成
BACKBONE_DIR = DIAG / "ch3-backbone-protocolA-v2"
XGB_CPAELP_PATH = DIAG / "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2/xgb_cpa_elp_results.json"
# 图3-9 四档长度逐流读数的落盘出处（运行目录未同步到本机，读数以本文件第九节为准）
LENGTH_LEDGER = REPO / ".Codex/docs/RWKV/2026-08-17-第三章XGBoost基线对照与门槛测算.md"

# 图3-12 独立数据源：告警预算曲线专项复算产物
ALERT_RUN_DIR = DIAG / "ch3-alert-budget-curve"
ALERT_JSON_PATH = ALERT_RUN_DIR / "alert_budget_curves.json"
ALERT_SCORES_PATH = ALERT_RUN_DIR / "entity_scores.npy"
ALERT_ROWS_PATH = ALERT_RUN_DIR / "entity_scores_rows.json"
DIJK_CACHE_DIR = DIAG / "dijk-repro/cache"
ALERT_ENT24_PATH = DIJK_CACHE_DIR / "ent24_local.npy"
ALERT_Y24_PATH = DIJK_CACHE_DIR / "y24.npy"

# ---------------------------------------------------------------------------
# 正文冻结数值。每一项对应正文 3.6 节的印刷读数，绘图前逐项复现，超差直接报错。
# ---------------------------------------------------------------------------

# 表 3-2：五个骨干的无机制格、两机制并用格与增益（实体平均精确率百分数、增量个百分点）
BACKBONE_FROZEN: tuple[tuple[str, float, float, float], ...] = (
    ("多层感知机", 33.50, 51.84, 18.34),
    ("沿流序列因果卷积", 27.94, 43.52, 15.58),
    ("全注意力", 9.17, 21.68, 12.51),
    ("树集成", 51.32, 56.51, 5.19),
    ("门控循环", 16.48, 19.21, 2.73),
)
# 表 3-2 表注：四个神经骨干的可训练参数量都落在 90,242 的正负 2% 以内
NPAR_ANCHOR = 90242
NPAR_TOL = 0.02
# 3.6.2 第二段：判读带宽 11.59 个百分点，取自 3.6.3 完整方法三次重复训练的极差
BAND_FROZEN = 11.59
# 表 3-7 表头：目标年度评价实体数
N_ENT_FROZEN = 47115

# 表 3-4 与 3.6.5：两个启用可学池化的配置，选中轮次与该轮的指数取值
LP_FROZEN: dict[str, tuple[int, float]] = {"C01": (14, 0.5233), "C11": (10, 1.0562)}
LP_INIT = 2.0  # 式 (3-11) 的初值

# 表 3-5：四档序列长度的逐流平均精确率三次取值、均值与取值波动（百分数与个百分点）
LENGTH_FROZEN: tuple[tuple[int, tuple[float, float, float], float, float], ...] = (
    (16, (0.241938, 0.260196, 0.183522), 22.86, 4.01),
    (32, (0.406520, 0.273421, 0.207112), 29.57, 10.16),
    (64, (0.313038, 0.294242, 0.403543), 33.69, 5.84),
    (128, (0.231571, 0.189229, 0.305084), 24.20, 5.86),
)

# 3.6.8：受限观测曲线的三处印刷读数与前 50 条时的流读取占比
TOPK_FROZEN = {"k1": 29.9964, "k50": 45.7276, "full": 46.2988, "cov50": 2.27}
ENTITY_FLOW_MEDIAN = 2  # 3.6.6 与 3.6.8：实体流数中位数

# 图3-12 冻结数值（正文 3.6.2 节图题与相邻两段，2026-08-18 版）
ALERT_FROZEN = {
    "crossing_nominal_fpr": 0.025020,  # 正文「假阳率 2.50% 处相交」
    "ours_wins_fraction": 0.872204,  # 正文「87.22% 的点上检出率更高」
    "dr_at_010pct": (0.264628, 0.118351),  # 正文「0.10% 处…14.63 个百分点」
    "dr_at_050pct": (0.497340, 0.207447),  # 正文「0.50% 处…28.99 个百分点」
    "transformer_lead_span": (0.025236, 0.128529),  # 正文「假阳率 2.52% 至 12.85%」
    "transformer_max_lead": 0.045213,  # 正文「最大领先 4.52 个百分点」
}

# 撤下的三幅：不重绘，理由随清单一起交付，是否另行处置由正文一侧裁决
WITHDRAWN: tuple[dict[str, str], ...] = (
    {
        "stem": "图3-5-跨年度主性能对比",
        "reason": (
            "图题所述的六方法三指标共 18 个数与表 3-7 逐格一一对应，条形图不增加信息；"
            "且随机森林、发表配置一维卷积网络与发表配置门控循环网络三行在本机没有结果 JSON，"
            "只有印刷两位小数，无法按图件合同记录数据来源键路径。"
        ),
        "unblock": "同步 diagnostics/ch3-baselines-full/{trees_results.json,neural_results.json} 后可改画位次连线图；无需新实验。",
    },
    {
        "stem": "图3-7-训练稳定性",
        "reason": (
            "全图只承载六个逐流读数，正文已连同两个取值波动逐一写出；"
            "其中完整方法的三次取值与表 3-5 第 128 档是同一组数，已由图3-9 呈现。"
        ),
        "unblock": "如需保留，最省的做法是并入图3-9，在第 128 档旁另画一组无机制参照的三点。",
    },
    {
        "stem": "图3-10-攻击类别分面",
        "reason": (
            "七行两指标共 14 个点估计全部在表 3-6 内，区间按图件体例不进图，图只能复述表格；"
            "正文另已写明该子集只占全部正例的 0.164%、且三行正例数少于 50 不参与比较，"
            "单独配图会把它抬到与主结果同级。"
        ),
        "unblock": "如裁决保留，需同步 diagnostics/ch3-e6-v2/e6_v2.json 及其三个输入数组；无需新实验。",
    },
)

# ---------------------------------------------------------------------------
# 版面
# ---------------------------------------------------------------------------

INK = fs.INK
MUTED = fs.MUTED
RULE = fs.RULE
HAIRLINE = fs.HAIRLINE
SHADE = fs.SHADE
ACCENT = fs.M2_EDGE
SERIES_A_FACE = fs.M1_FACE
SERIES_A_EDGE = fs.M1_EDGE
SERIES_B_FACE = fs.M2_FACE
FS_MIN = fs.MIN_FONT_PT
FS_MAIN = fs.MAIN_FONT_PT
PNG_DPI = fs.PNG_DPI

plt.rcParams.update(
    {
        "axes.labelsize": FS_MAIN,
        "axes.titlesize": FS_MAIN,
        "legend.fontsize": FS_MIN,
        "grid.linewidth": fs.AUX_LINE_PT,
        "lines.linewidth": 1.4,
        "axes.edgecolor": INK,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
    }
)

CELL_NAMES = {
    "C00": "无机制参照",
    "C01": "仅可学池化",
    "C10": "仅因果前缀聚合",
    "C11": "双机制并用",
}


@dataclass(frozen=True)
class FigureSpec:
    """一张结果图的尺寸、绘制入口与溯源信息。"""

    stem: str
    width_mm: float
    height_mm: float
    draw: Callable[[dict[str, Any]], Figure]
    data_sources: tuple[str, ...]
    caption: str
    check_group: str = ""


@dataclass
class Check:
    """一项正文一致性自检的记录。"""

    item: str
    reproduced: float
    thesis: float
    tolerance: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "项": self.item,
            "复现": round(self.reproduced, 8),
            "正文": self.thesis,
            "容差": self.tolerance,
            "差": round(abs(self.reproduced - self.thesis), 8),
        }


def expect(bucket: list[Check], item: str, got: float, want: float, tol: float) -> None:
    """复现值与正文印刷值比对；超差立刻报错停止，不得改图迁就。"""

    if not np.isfinite(got):
        raise ValueError(f"正文一致性自检失败：{item} 复现值非有限数，停止")
    if abs(got - want) > tol:
        raise ValueError(
            f"正文一致性自检失败：{item} 复现={got:.6f} 正文={want:.6f} "
            f"差={abs(got - want):.3e} 超出容差 {tol:g}；停止，不得改图迁就"
        )
    bucket.append(Check(item, float(got), float(want), tol))


def mm_to_inch(value: float) -> float:
    return value / 25.4


def new_figure(width_mm: float, height_mm: float) -> Figure:
    if width_mm > fs.MAX_WIDTH_MM:
        raise ValueError(f"宽度 {width_mm} mm 超过图件合同上限 {fs.MAX_WIDTH_MM} mm")
    if height_mm > fs.MAX_HEIGHT_MM:
        raise ValueError(f"高度 {height_mm} mm 超过图件合同上限 {fs.MAX_HEIGHT_MM} mm")
    return plt.figure(figsize=(mm_to_inch(width_mm), mm_to_inch(height_mm)), dpi=200)


def style_axes(ax: Axes, *, grid_axis: str = "y") -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, axis=grid_axis, color=HAIRLINE, linewidth=fs.AUX_LINE_PT, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, pad=1.5)


def pct_formatter(decimals: int = 0) -> Callable[[float, int], str]:
    return lambda value, _pos: f"{value:.{decimals}f}%"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"数据源不存在：{path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


# ---------------------------------------------------------------------------
# 遮挡自检：任何数据元素都不得落在图例框或注记框这类不透明矩形内
# ---------------------------------------------------------------------------

# 承载数据的绘图对象统一打这个标记，自检据此枚举，不靠猜测区分数据线与网格线、参考线。
DATA_GID = "data-element"


def mark_data(artist: Any) -> Any:
    """把一个绘图返回值标记为数据元素。接受 Line2D、Rectangle 或它们的列表。"""

    if isinstance(artist, (list, tuple)):
        for item in artist:
            mark_data(item)
        return artist
    artist.set_gid(DATA_GID)
    return artist


def _is_opaque(patch: Any) -> bool:
    """判断一个补片是否不透明到足以遮住其下方的数据。"""

    face = patch.get_facecolor()
    if face is None or len(face) < 4:
        return False
    alpha = patch.get_alpha()
    value = float(face[3]) if alpha is None else float(alpha)
    return value > 0.99


def _opaque_boxes(fig: Figure, renderer: Any) -> list[tuple[str, Any]]:
    """收集全部不透明矩形：图例边框与带底色的文字注记框。"""

    boxes: list[tuple[str, Any]] = []
    legends = list(fig.legends)
    for ax in fig.axes:
        legend = ax.get_legend()
        if legend is not None:
            legends.append(legend)
    for legend in legends:
        if not legend.get_frame_on():
            continue
        frame = legend.get_frame()
        if _is_opaque(frame):
            boxes.append(("图例框", frame.get_window_extent(renderer)))

    texts = list(fig.texts)
    for ax in fig.axes:
        texts.extend(ax.texts)
    for item in texts:
        patch = item.get_bbox_patch()
        if patch is None or not _is_opaque(patch):
            continue
        head = item.get_text().splitlines()[0]
        boxes.append((f"注记框「{head}」", patch.get_window_extent(renderer)))
    return boxes


def _point_gap_px(x: float, y: float, bbox: Any) -> float:
    """点到矩形的最短距离，单位为显示像素；点落在矩形内时为 0。"""

    dx = max(bbox.x0 - x, 0.0, x - bbox.x1)
    dy = max(bbox.y0 - y, 0.0, y - bbox.y1)
    return float(np.hypot(dx, dy))


@dataclass
class Occlusion:
    """一幅图的遮挡判定结果。"""

    stem: str
    n_boxes: int
    n_points: int
    n_distinct: int
    n_inside: int
    n_inside_distinct: int
    min_gap_pt: float
    marker_pt: float
    offenders: list[str]
    per_series: list[str]


def check_occlusion(stem: str, fig: Figure) -> Occlusion:
    """逐点判定：把每个数据标记与曲线折点的显示坐标同每个不透明矩形做包含判定。

    判定在实际渲染后的显示坐标系上做，不依赖数据坐标或人工估算的版面尺寸。
    只统计落在坐标区可视范围内的点——被坐标范围裁掉的点本来就不在页面上。
    除包含判定外还报告最近间隙，用来说明数据元素连边缘都没有被压到。
    """

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = _opaque_boxes(fig, renderer)

    n_points = 0
    n_distinct = 0
    n_inside = 0
    n_inside_distinct = 0
    min_gap = float("inf")
    marker_pt = 0.0
    offenders: list[str] = []
    per_series: list[str] = []

    for ax in fig.axes:
        clip = ax.get_window_extent(renderer)
        for line in ax.get_lines():
            if line.get_gid() != DATA_GID:
                continue
            xy = np.asarray(line.get_transform().transform(line.get_xydata()), dtype=float)
            if xy.size == 0:
                continue
            keep = np.isfinite(xy).all(axis=1)
            keep &= (xy[:, 0] >= clip.x0) & (xy[:, 0] <= clip.x1)
            keep &= (xy[:, 1] >= clip.y0) & (xy[:, 1] <= clip.y1)
            xy = xy[keep]
            if xy.size == 0:
                continue
            rounded = np.round(xy, 0)
            distinct = np.unique(rounded, axis=0)
            n_points += int(xy.shape[0])
            n_distinct += int(distinct.shape[0])
            marker = line.get_marker()
            if marker not in (None, "none", "None", " ", ""):
                marker_pt = max(marker_pt, float(line.get_markersize()))
            hit = 0
            hit_distinct = 0
            for px, py in xy:
                for name, bbox in boxes:
                    gap = _point_gap_px(px, py, bbox)
                    min_gap = min(min_gap, gap)
                    if gap <= 0.0:
                        hit += 1
                        if len(offenders) < 6:
                            offenders.append(
                                f"{name} 盖住 {line.get_label()} 的显示坐标 ({px:.1f}, {py:.1f})"
                            )
            for px, py in distinct:
                if any(_point_gap_px(px, py, bbox) <= 0.0 for _name, bbox in boxes):
                    hit_distinct += 1
            n_inside += hit
            n_inside_distinct += hit_distinct
            per_series.append(
                f"{line.get_label()}：可视折点 {xy.shape[0]} 个（去重 {distinct.shape[0]} 个），"
                f"落在框内 {hit} 个（去重 {hit_distinct} 个）"
            )
        for patch in ax.patches:
            if patch.get_gid() != DATA_GID:
                continue
            bar = patch.get_window_extent(renderer)
            n_points += 1
            n_distinct += 1
            hit = 0
            for name, bbox in boxes:
                overlap_x = min(bar.x1, bbox.x1) - max(bar.x0, bbox.x0)
                overlap_y = min(bar.y1, bbox.y1) - max(bar.y0, bbox.y0)
                gap = 0.0 if (overlap_x > 0 and overlap_y > 0) else max(-overlap_x, -overlap_y, 0.0)
                min_gap = min(min_gap, gap)
                if overlap_x > 0 and overlap_y > 0:
                    hit += 1
                    if len(offenders) < 6:
                        offenders.append(f"{name} 与条形重叠，重叠 {overlap_x:.1f}×{overlap_y:.1f} 像素")
            n_inside += hit
            n_inside_distinct += hit
            per_series.append(f"条形 {patch.get_label()}：落在框内 {hit} 个")

    gap_pt = min_gap / fig.dpi * 72.0 if np.isfinite(min_gap) else float("inf")
    return Occlusion(
        stem,
        len(boxes),
        n_points,
        n_distinct,
        n_inside,
        n_inside_distinct,
        gap_pt,
        marker_pt,
        offenders,
        per_series,
    )


# ---------------------------------------------------------------------------
# 数据加载与正文一致性自检
# ---------------------------------------------------------------------------


def load_full_results() -> dict[str, Any]:
    return read_json(FULL_PATH)


def load_backbone_gains(full: dict[str, Any]) -> dict[str, Any]:
    """图3-6：五个骨干的两机制增量与判读带宽，逐行复现表 3-2 的印刷值。

    骨干运行的取用不作猜测：卷积行必须取 ch3-backbone-protocolA-v2/cnn（通道 92、
    核宽 3、3 层、感受野 7），不是等总参数量版的 ch3-cnn-backbone-2x2-same-run-c00-v2；
    两者是不同的四格读数。此处以可训练参数量与评价实体数作为取用是否正确的断言。
    """
    checks: list[Check] = []

    fair = read_json(FAIRSEL_PATH)
    raw: dict[str, dict[str, float]] = {
        "多层感知机": {
            "C00": float(fair["cells"]["C00"]["e_lp"]),
            "C11": float(fair["cells"]["C11"]["e_lp"]),
            "npar": float(fair["cells"]["C11"]["npar"]),
            "n_ent": float(fair["cells"]["C11"]["n_ent_scored"]),
        }
    }
    for name, tag in (("沿流序列因果卷积", "cnn"), ("全注意力", "transformer"), ("门控循环", "gru")):
        data = read_json(BACKBONE_DIR / tag / "ch3_backbone_protocolA_results.json")
        cells = data["cells"]
        raw[name] = {
            "C00": float(cells[f"{tag}-C00"]["e_lp"]),
            "C11": float(cells[f"{tag}-C11"]["e_lp"]),
            "npar": float(cells[f"{tag}-C11"]["npar"]),
            "n_ent": float(cells[f"{tag}-C11"].get("n_ent_scored", N_ENT_FROZEN)),
        }
    xgb = read_json(XGB_CPAELP_PATH)
    raw["树集成"] = {
        "C00": float(xgb["cells"]["C00"]["ent_ap"]),
        "C11": float(xgb["cells"]["C11"]["ent_ap"]),
        "npar": float("nan"),
        "n_ent": float(xgb["cells"]["C11"]["n_ent_scored"]),
    }

    rows: list[dict[str, Any]] = []
    for name, c00_txt, c11_txt, gain_txt in BACKBONE_FROZEN:
        item = raw[name]
        c00, c11 = item["C00"] * 100.0, item["C11"] * 100.0
        gain = c11 - c00
        expect(checks, f"表3-2 {name} 无机制", c00, c00_txt, 5e-3)
        expect(checks, f"表3-2 {name} 两机制并用", c11, c11_txt, 5e-3)
        expect(checks, f"表3-2 {name} 增益", gain, gain_txt, 5e-3)
        expect(checks, f"{name} 评价实体数", item["n_ent"], float(N_ENT_FROZEN), 0.5)
        if np.isfinite(item["npar"]):
            deviation = abs(item["npar"] - NPAR_ANCHOR) / NPAR_ANCHOR
            if deviation > NPAR_TOL:
                raise ValueError(
                    f"{name} 可训练参数量 {item['npar']:.0f} 偏离锚点 {NPAR_ANCHOR} 达 "
                    f"{deviation * 100:.2f}%，超过表 3-2 表注的 2%；可能取错运行目录，停止"
                )
        rows.append({"name": name, "c00": c00, "c11": c11, "gain": gain})

    stability = np.asarray(full["stability"]["C11"], dtype=float)
    band = float(stability.max() - stability.min()) * 100.0
    expect(checks, "3.6.2 判读带宽", band, BAND_FROZEN, 5e-3)
    for row in rows:
        row["over_band"] = bool(row["gain"] > band)

    over = [row["name"] for row in rows if row["over_band"]]
    if over != ["多层感知机", "沿流序列因果卷积", "全注意力"]:
        raise ValueError(f"超出带宽的骨干集合 {over} 与正文所述三行不符，停止")

    return {"rows": rows, "band": band, "checks": checks}


def load_lp_trajectory() -> dict[str, Any]:
    """图3-8：两个启用可学池化的配置在 20 个训练轮次上的指数取值。

    selection.{C01,C11}.val_ap_history 的每一项为 [轮次, 源年度验证平均精确率, 指数]。
    自检两条：选中轮次与表 3-3 行序所记一致；该轮的指数等于 cells.*.p 的终值。
    """
    checks: list[Check] = []
    fair = read_json(FAIRSEL_PATH)
    series: dict[str, dict[str, Any]] = {}
    for cell, (sel_epoch_txt, sel_p_txt) in LP_FROZEN.items():
        history = fair["selection"][cell]["val_ap_history"]
        epochs = [int(row[0]) for row in history]
        values = [float(row[2]) for row in history]
        sel_epoch = int(fair["cells"][cell]["sel_epoch"])
        sel_p = float(fair["cells"][cell]["p"])
        expect(checks, f"{CELL_NAMES[cell]} 选中轮次", float(sel_epoch), float(sel_epoch_txt), 0.0)
        expect(checks, f"{CELL_NAMES[cell]} 选中轮次的指数", sel_p, sel_p_txt, 5e-5)
        at_sel = values[epochs.index(sel_epoch)]
        expect(checks, f"{CELL_NAMES[cell]} 轨迹与终值一致", at_sel, sel_p, 1e-9)
        if max(values) > LP_INIT:
            raise ValueError(f"{CELL_NAMES[cell]} 轨迹出现高于初值 {LP_INIT} 的取值，与正文不符，停止")
        series[cell] = {"epochs": epochs, "values": values, "sel_epoch": sel_epoch, "sel_p": sel_p}
    return {"series": series, "checks": checks}


def load_length_flow(full: dict[str, Any]) -> dict[str, Any]:
    """图3-9：四档序列长度的逐流平均精确率三次取值与均值。

    产出该实验的运行目录未同步到本机，逐次读数取自 LENGTH_LEDGER 第九节；
    第 128 档与 ch3-full 的 stability.C11 同源，此处逐值交叉核对，不一致即停止。
    """
    checks: list[Check] = []
    anchor = np.asarray(full["stability"]["C11"], dtype=float)
    rows: list[dict[str, Any]] = []
    for length, triple, mean_txt, spread_txt in LENGTH_FROZEN:
        values = np.asarray(triple, dtype=float) * 100.0
        mean = float(values.mean())
        spread = float(values.std(ddof=1))
        expect(checks, f"表3-5 长度 {length} 均值", mean, mean_txt, 5e-3)
        expect(checks, f"表3-5 长度 {length} 取值波动", spread, spread_txt, 5e-3)
        if length == 128:
            for idx, (got, want) in enumerate(zip(triple, anchor.tolist(), strict=True), start=1):
                expect(checks, f"长度 128 第 {idx} 次与 stability.C11 交叉核对", got, want, 5e-7)
        rows.append({"length": length, "values": values, "mean": mean, "spread": spread})

    means = [row["mean"] for row in rows]
    spreads = [row["spread"] for row in rows]
    expect(checks, "3.6.6 档内波动下界", min(spreads), 4.01, 5e-3)
    expect(checks, "3.6.6 档内波动上界", max(spreads), 10.16, 5e-3)
    return {"rows": rows, "mean_span": (min(means), max(means)), "checks": checks}


def load_topk_curve(full: dict[str, Any]) -> dict[str, Any]:
    """图3-11：每实体只用按时间最早的前 k 条流时的实体平均精确率。

    curve.C11 的每一项为 [k, 实体平均精确率, 假阳率 4% 工作点检出率, 已评实体数, 被读取流占比]，
    末项的 k 为空表示使用全部流。正文只引用实体平均精确率一列，检出率一列不入图。
    """
    checks: list[Check] = []
    curve = full["curve"]["C11"]
    finite = [row for row in curve if row[0] is not None]
    ks = [int(row[0]) for row in finite]
    aps = [float(row[1]) * 100.0 for row in finite]
    coverage = [float(row[4]) * 100.0 for row in finite]
    full_ap = float(curve[-1][1]) * 100.0
    if curve[-1][0] is not None:
        raise ValueError("curve.C11 末项不是使用全部流的取值，停止")

    idx50 = ks.index(50)
    expect(checks, "3.6.8 只看第一条流", aps[0], TOPK_FROZEN["k1"], 5e-4)
    expect(checks, "3.6.8 前 50 条", aps[idx50], TOPK_FROZEN["k50"], 5e-4)
    expect(checks, "3.6.8 使用全部流", full_ap, TOPK_FROZEN["full"], 5e-4)
    expect(checks, "3.6.8 前 50 条的流读取占比", coverage[idx50], TOPK_FROZEN["cov50"], 5e-3)
    expect(checks, "评价实体数", float(finite[0][3]), float(N_ENT_FROZEN), 0.5)
    if aps[idx50] / full_ap < 0.95:
        raise ValueError("前 50 条未达到使用全部流取值的 95%，与正文不符，停止")
    return {
        "ks": ks,
        "aps": aps,
        "coverage": coverage,
        "full_ap": full_ap,
        "idx50": idx50,
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# 图3-12：告警预算曲线（数据源与其余四幅独立）
# ---------------------------------------------------------------------------


def _average_precision(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """sklearn.metrics.average_precision_score 的等价实现（按唯一阈值分组处理并列）。

    只用于图3-12 数据加载阶段核验 entity_scores.npy 的列序与实体标签重建是否对齐，
    不作为任何结果表的指标来源——正式实体级读数以 alert_budget_curves.json 内的冻结值为准。
    """
    order = np.argsort(y_score, kind="mergesort")[::-1]
    yt = y_true[order]
    ys = y_score[order]
    distinct = np.where(np.diff(ys))[0]
    thr_idx = np.r_[distinct, len(yt) - 1]
    tps = np.cumsum(yt)[thr_idx]
    fps = 1 + thr_idx - tps
    precision = tps / (tps + fps)
    recall = tps / tps[-1]
    precision = np.r_[precision[::-1], 1.0]
    recall = np.r_[recall[::-1], 0.0]
    return float(-np.sum(np.diff(recall) * precision[:-1]))


def _budget_curve(es: np.ndarray, ent_lab: np.ndarray) -> dict[str, np.ndarray]:
    """按实体分数与标签构造告警预算曲线。

    算法逐字复用 thesis/experiments/llm_probe/tools/ch3_alert_budget_curves.py 的
    budget_curve() 函数（该脚本是 entity_scores.npy 与 alert_budget_curves.json 的
    生成源）：阈值取自负实体分数降序序列，第 j 个（0 起）阈值对应名义假阳率 j/n_neg。
    """
    ok = np.isfinite(es)
    v, lab = es[ok], ent_lab[ok]
    pos = np.sort(v[lab == 1])
    neg = np.sort(v[lab == 0])[::-1]
    n_pos, n_neg = len(pos), len(neg)
    dr = (n_pos - np.searchsorted(pos, neg, side="left")) / n_pos
    return {"dr": dr, "nominal_fpr": np.arange(n_neg) / n_neg, "n_pos": n_pos, "n_neg": n_neg}


def _find_crossings(dr_a: np.ndarray, dr_b: np.ndarray) -> list[dict[str, int]]:
    """在共同的假阳预算网格上找两条检出率曲线的符号变化点，语义同源脚本 find_crossings。"""

    diff = dr_a - dr_b
    sign = np.sign(diff)
    nz_idx = np.flatnonzero(sign != 0)
    crossings: list[dict[str, int]] = []
    if len(nz_idx) == 0:
        return crossings
    prev = int(nz_idx[0])
    for i in nz_idx[1:]:
        i = int(i)
        if sign[i] != sign[prev]:
            crossings.append({"j_before": prev, "j_after": i})
        prev = i
    return crossings


def load_alert_budget_curve() -> dict[str, Any]:
    """加载图3-12所需数据并复现正文冻结数值；任何一项复现不过直接报错，不画图。

    实体顺序核验：entity_scores.npy 的列序对应 ent24_local.npy——即
    thesis/experiments/llm_probe/tools/ch3_alert_budget_curves.py::build_entity_mapping
    用 pd.factorize 编码地址后再对整数无向对 np.unique 得到的实体编号，
    不是对字符串键直接排序的结果（两种编号给出相同的实体划分，但索引顺序不同）。
    本函数用实体级读数与 alert_budget_curves.json 内的冻结值比对，显式核验列序对齐，
    不对列序做任何假设；核验失败直接抛错，不允许静默按其他顺序对齐。
    """
    for path in (ALERT_JSON_PATH, ALERT_SCORES_PATH, ALERT_ROWS_PATH, ALERT_ENT24_PATH, ALERT_Y24_PATH):
        if not path.exists():
            raise FileNotFoundError(f"图3-12 数据源缺失：{path}")

    y24 = np.load(ALERT_Y24_PATH)
    ent24 = np.load(ALERT_ENT24_PATH)
    n_ent = int(ent24.max()) + 1
    ent_lab = np.zeros(n_ent, np.float32)
    np.maximum.at(ent_lab, ent24, y24)

    with ALERT_ROWS_PATH.open(encoding="utf-8") as handle:
        rows = json.load(handle)["rows"]
    scores = np.load(ALERT_SCORES_PATH)
    if scores.shape != (len(rows), n_ent):
        raise ValueError(f"图3-12 entity_scores.npy 形状 {scores.shape} 与实体数 {n_ent} 不符，停止")

    i_ours, i_trans = rows.index("ours_c11"), rows.index("transformer_full")
    es_ours = scores[i_ours].astype(np.float64)
    es_trans = scores[i_trans].astype(np.float64)

    with ALERT_JSON_PATH.open(encoding="utf-8") as handle:
        meta = json.load(handle)
    ap_frozen_ours = float(meta["methods"]["ours_c11"]["lp"]["entity_ap"])
    ap_frozen_trans = float(meta["methods"]["transformer_full"]["max"]["entity_ap"])
    ap_ours = _average_precision(ent_lab.astype(np.float64), es_ours)
    ap_trans = _average_precision(ent_lab.astype(np.float64), es_trans)
    if abs(ap_ours - ap_frozen_ours) > 1e-6:
        raise ValueError(
            f"图3-12 列序核验失败：ours_c11 复现={ap_ours:.10f} 冻结={ap_frozen_ours:.10f}，"
            "entity_scores.npy 列序可能与 ent24_local.npy 不一致，停止，不得猜测对齐方式"
        )
    if abs(ap_trans - ap_frozen_trans) > 1e-6:
        raise ValueError(
            f"图3-12 列序核验失败：transformer_full 复现={ap_trans:.10f} 冻结={ap_frozen_trans:.10f}，"
            "entity_scores.npy 列序可能与 ent24_local.npy 不一致，停止，不得猜测对齐方式"
        )

    curve_ours = _budget_curve(es_ours, ent_lab)
    curve_trans = _budget_curve(es_trans, ent_lab)
    n = min(curve_ours["n_neg"], curve_trans["n_neg"])
    if n != 46363 or curve_ours["n_pos"] != 752:
        raise ValueError(
            f"图3-12 实体规模与正文冻结的 46,363 负实体 / 752 正实体不符："
            f"n_neg={n} n_pos={curve_ours['n_pos']}，停止"
        )

    dr_ours, dr_trans = curve_ours["dr"][:n], curve_trans["dr"][:n]
    fpr = curve_ours["nominal_fpr"][:n]
    diff = dr_ours - dr_trans

    crossings = _find_crossings(dr_ours, dr_trans)
    if len(crossings) < 3:
        raise ValueError(f"图3-12 交叉点数 {len(crossings)} 少于预期的 3 个，停止")
    # 第 1 个交叉点是 j=0 附近的单点边界效应（负实体最高分处，样本量为 1），
    # 正文所指「假阳率 2.50% 处相交」与「2.52% 至 12.85% 区间」是第 2、3 个交叉点。
    main_cross, span_end_cross = crossings[1], crossings[2]
    crossing_fpr = float(fpr[main_cross["j_before"]])
    span_lo = float(fpr[main_cross["j_after"]])
    span_hi = float(fpr[span_end_cross["j_after"]])

    lead_lo_idx, lead_hi_idx = main_cross["j_after"], span_end_cross["j_before"]
    lead_slice = diff[lead_lo_idx : lead_hi_idx + 1]
    max_lead = float(-lead_slice.min()) if lead_slice.size else 0.0

    def _dr_at(target: float) -> tuple[float, float]:
        j = min(int(n * target), n - 1)
        return float(dr_ours[j]), float(dr_trans[j])

    dr010 = _dr_at(0.001)
    dr050 = _dr_at(0.005)
    win_frac = float(np.mean(diff > 0))

    checks: list[Check] = []
    for item, got, want in (
        ("交叉点名义假阳率", crossing_fpr, ALERT_FROZEN["crossing_nominal_fpr"]),
        ("本方法领先点占比", win_frac, ALERT_FROZEN["ours_wins_fraction"]),
        ("假阳率 0.10% 本方法检出率", dr010[0], ALERT_FROZEN["dr_at_010pct"][0]),
        ("假阳率 0.10% 全注意力检出率", dr010[1], ALERT_FROZEN["dr_at_010pct"][1]),
        ("假阳率 0.50% 本方法检出率", dr050[0], ALERT_FROZEN["dr_at_050pct"][0]),
        ("假阳率 0.50% 全注意力检出率", dr050[1], ALERT_FROZEN["dr_at_050pct"][1]),
        ("全注意力领先区间左端", span_lo, ALERT_FROZEN["transformer_lead_span"][0]),
        ("全注意力领先区间右端", span_hi, ALERT_FROZEN["transformer_lead_span"][1]),
        ("全注意力最大领先", max_lead, ALERT_FROZEN["transformer_max_lead"]),
    ):
        expect(checks, item, got, want, 2e-4)

    return {
        "fpr": fpr,
        "dr_ours": dr_ours,
        "dr_trans": dr_trans,
        "crossing_fpr": crossing_fpr,
        "win_frac": win_frac,
        "dr010": dr010,
        "dr050": dr050,
        "lead_span": (span_lo, span_hi),
        "max_lead": max_lead,
        "n_neg": n,
        "n_pos": curve_ours["n_pos"],
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# 绘图
# ---------------------------------------------------------------------------


def draw_backbone_gain(ctx: dict[str, Any]) -> Figure:
    """图3-6 两个机制在五个骨干上的实体平均精确率增量与判读带宽。

    只画表 3-2 的增益列与那条带宽线：四格柱面与交互项都已在表 3-3、表 3-2 内，
    图内不再复述，也不出现任何判据框。
    """
    payload = ctx["backbone"]
    rows, band = payload["rows"], payload["band"]

    fig = new_figure(132, 78)
    ax = fig.add_axes((0.245, 0.255, 0.720, 0.665))
    style_axes(ax, grid_axis="x")

    ypos = np.arange(len(rows))[::-1]
    for y, row in zip(ypos, rows, strict=True):
        over = row["over_band"]
        ax.barh(
            y,
            row["gain"],
            height=0.60,
            facecolor=SERIES_A_FACE if over else "white",
            edgecolor=SERIES_A_EDGE if over else MUTED,
            linewidth=1.0,
            hatch="///" if over else "..",
            zorder=3,
        )
        ax.text(
            row["gain"] + 0.35,
            y,
            fs.checked(f"+{row['gain']:.2f}", FS_MIN),
            va="center",
            ha="left",
            fontsize=FS_MIN,
            color=INK,
            zorder=4,
        )

    ax.axvline(band, color=ACCENT, linestyle=(0, (4, 2)), linewidth=1.1, zorder=5)
    ax.text(
        band + 0.35,
        len(rows) - 0.42,
        fs.checked(f"判读带宽 {band:.2f} 个百分点", FS_MIN),
        fontsize=FS_MIN,
        color=ACCENT,
        va="center",
        ha="left",
        zorder=6,
    )

    ax.set_yticks(ypos)
    ax.set_yticklabels([fs.checked(row["name"], FS_MIN) for row in rows], fontsize=FS_MIN)
    ax.set_ylim(-0.62, len(rows) - 0.20)
    ax.set_xlim(0, 21.6)
    ax.set_xlabel(
        fs.checked("两机制并用相对无机制的实体平均精确率增量（个百分点）", FS_MAIN),
        fontsize=FS_MAIN,
        labelpad=3,
    )

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=SERIES_A_FACE, edgecolor=SERIES_A_EDGE, linewidth=1.0, hatch="///"),
        plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=MUTED, linewidth=1.0, hatch=".."),
    ]
    fig.legend(
        handles,
        [fs.checked("增量超出判读带宽", FS_MIN), fs.checked("增量落在判读带宽之内", FS_MIN)],
        loc="lower center",
        bbox_to_anchor=(0.60, 0.015),
        ncol=2,
        frameon=True,
        framealpha=1.0,
        edgecolor=HAIRLINE,
        fontsize=FS_MIN,
        borderpad=0.4,
        handlelength=1.8,
        handleheight=1.0,
        columnspacing=1.2,
    )
    return fig


def draw_lp_trajectory(ctx: dict[str, Any]) -> Figure:
    """图3-8 可学指数在训练过程中的取值变化。"""

    series = ctx["lp"]["series"]
    fig = new_figure(132, 84)
    ax = fig.add_axes((0.135, 0.215, 0.835, 0.715))
    style_axes(ax)

    styles = {
        "C01": {"linestyle": "-", "color": INK, "marker": "o"},
        "C11": {"linestyle": (0, (5, 2)), "color": MUTED, "marker": "s"},
    }
    for cell in ("C01", "C11"):
        item = series[cell]
        style = styles[cell]
        ax.plot(
            item["epochs"],
            item["values"],
            linestyle=style["linestyle"],
            color=style["color"],
            linewidth=1.3,
            marker=style["marker"],
            markersize=3.6,
            markerfacecolor="white",
            markeredgewidth=0.9,
            markeredgecolor=style["color"],
            zorder=5,
            label=fs.checked(CELL_NAMES[cell], FS_MIN),
        )
        ax.plot(
            [item["sel_epoch"]],
            [item["sel_p"]],
            linestyle="none",
            marker=style["marker"],
            markersize=6.4,
            markerfacecolor=style["color"],
            markeredgecolor=style["color"],
            zorder=6,
        )

    ax.axhline(LP_INIT, color=RULE, linestyle=(0, (1, 1.8)), linewidth=fs.AUX_LINE_PT + 0.3, zorder=3)
    ax.text(
        1.0,
        LP_INIT - 0.045,
        fs.checked("式 (3-11) 的初值 2.0000", FS_MIN),
        ha="left",
        va="top",
        fontsize=FS_MIN,
        color=RULE,
    )
    ax.axhline(1.0, color=ACCENT, linestyle=(0, (4, 2)), linewidth=1.1, zorder=3)
    ax.text(
        20.4,
        1.045,
        fs.checked("指数为 1，聚合为算术平均", FS_MIN),
        ha="right",
        va="bottom",
        fontsize=FS_MIN,
        color=ACCENT,
    )

    ax.annotate(
        fs.checked(f"选中第 {series['C11']['sel_epoch']} 轮\n取值 {series['C11']['sel_p']:.4f}", FS_MIN),
        xy=(series["C11"]["sel_epoch"], series["C11"]["sel_p"]),
        xytext=(13.2, 1.62),
        fontsize=FS_MIN,
        color=INK,
        linespacing=1.35,
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.9, "shrinkB": 4},
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": MUTED, "linewidth": 0.7},
        zorder=8,
    )
    ax.annotate(
        fs.checked(f"选中第 {series['C01']['sel_epoch']} 轮\n取值 {series['C01']['sel_p']:.4f}", FS_MIN),
        xy=(series["C01"]["sel_epoch"], series["C01"]["sel_p"]),
        xytext=(9.0, 0.60),
        fontsize=FS_MIN,
        color=INK,
        linespacing=1.35,
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.9, "shrinkB": 4},
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": MUTED, "linewidth": 0.7},
        zorder=8,
    )

    ax.set_xlim(0.4, 20.6)
    ax.set_ylim(0.35, 2.18)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.set_xlabel(fs.checked("训练轮次", FS_MAIN), fontsize=FS_MAIN)
    ax.set_ylabel(fs.checked("可学池化的指数取值", FS_MAIN), fontsize=FS_MAIN)
    ax.legend(
        loc="upper right",
        frameon=True,
        framealpha=1.0,
        edgecolor=HAIRLINE,
        fontsize=FS_MIN,
        borderpad=0.4,
        handlelength=2.4,
        labelspacing=0.35,
    )
    return fig


def draw_length_flow(ctx: dict[str, Any]) -> Figure:
    """图3-9 四档序列长度在等真实流预算下的逐流平均精确率分布。"""

    payload = ctx["length"]
    rows = payload["rows"]
    lo, hi = payload["mean_span"]

    fig = new_figure(124, 82)
    ax = fig.add_axes((0.155, 0.215, 0.805, 0.715))
    style_axes(ax)

    ax.axhspan(lo, hi, facecolor=SHADE, edgecolor="none", zorder=1)
    xs = np.arange(len(rows))
    for x, row in zip(xs, rows, strict=True):
        mark_data(
            ax.plot(
                [x] * len(row["values"]),
                row["values"],
                linestyle="none",
                marker="o",
                markersize=5.0,
                markerfacecolor="white",
                markeredgecolor=INK,
                markeredgewidth=1.0,
                zorder=5,
                label=f"长度 {row['length']} 的三次取值",
            )
        )
        # 均值横线用 plot 画而不用 hlines：Line2D 才能进遮挡自检的逐点枚举。
        mark_data(
            ax.plot(
                [x - 0.24, x + 0.24],
                [row["mean"], row["mean"]],
                linestyle="-",
                color=INK,
                linewidth=1.4,
                solid_capstyle="butt",
                zorder=6,
                label=f"长度 {row['length']} 的均值",
            )
        )
        ax.text(
            x + 0.28,
            row["mean"],
            fs.checked(f"{row['mean']:.2f}%", FS_MIN),
            ha="left",
            va="center",
            fontsize=FS_MIN,
            color=INK,
            bbox={"boxstyle": "square,pad=0.12", "facecolor": "white", "edgecolor": "none"},
            zorder=7,
        )

    ax.set_xticks(xs)
    ax.set_xticklabels([fs.checked(str(row["length"]), FS_MIN) for row in rows], fontsize=FS_MIN)
    ax.set_xlim(-0.58, len(rows) - 0.10)
    ax.set_ylim(15.0, 44.0)
    ax.yaxis.set_major_formatter(pct_formatter(0))
    ax.set_xlabel(fs.checked("序列长度（四档的真实流访问数相同）", FS_MAIN), fontsize=FS_MAIN)
    ax.set_ylabel(fs.checked("跨年度逐流平均精确率", FS_MAIN), fontsize=FS_MAIN)

    handles = [
        plt.Line2D([], [], linestyle="none", marker="o", markersize=5.0, markerfacecolor="white", markeredgecolor=INK),
        plt.Line2D([], [], linestyle="-", color=INK, linewidth=1.4),
        plt.Rectangle((0, 0), 1, 1, facecolor=SHADE, edgecolor=HAIRLINE, linewidth=fs.AUX_LINE_PT),
    ]
    ax.legend(
        handles,
        [
            fs.checked("三次重复训练的取值", FS_MIN),
            fs.checked("该档均值", FS_MIN),
            fs.checked("四档均值的跨度", FS_MIN),
        ],
        loc="upper left",
        frameon=True,
        framealpha=1.0,
        edgecolor=HAIRLINE,
        fontsize=FS_MIN,
        borderpad=0.4,
        handlelength=1.8,
        labelspacing=0.35,
    )
    return fig


def draw_topk_curve(ctx: dict[str, Any]) -> Figure:
    """图3-11 受限观测下的实体平均精确率随可用流条数的变化。"""

    payload = ctx["topk"]
    ks, aps = payload["ks"], payload["aps"]
    full_ap, idx50 = payload["full_ap"], payload["idx50"]

    fig = new_figure(132, 86)
    ax = fig.add_axes((0.145, 0.205, 0.825, 0.725))
    style_axes(ax)
    ax.set_xscale("log")

    ax.axhline(full_ap, color=MUTED, linestyle=(0, (5, 2)), linewidth=1.1, zorder=3)
    ax.text(
        118.0,
        full_ap + 0.28,
        fs.checked(f"使用全部流 {full_ap:.4f}%", FS_MIN),
        ha="right",
        va="bottom",
        fontsize=FS_MIN,
        color=MUTED,
    )
    ax.axvline(ENTITY_FLOW_MEDIAN, color=ACCENT, linestyle=(0, (1, 1.8)), linewidth=1.1, zorder=3)
    ax.text(
        ENTITY_FLOW_MEDIAN * 1.14,
        29.1,
        fs.checked(f"实体流数中位数 {ENTITY_FLOW_MEDIAN}", FS_MIN),
        ha="left",
        va="bottom",
        fontsize=FS_MIN,
        color=ACCENT,
    )

    mark_data(
        ax.plot(
            ks,
            aps,
            linestyle="-",
            color=INK,
            linewidth=1.4,
            marker="o",
            markersize=4.4,
            markerfacecolor="white",
            markeredgewidth=1.0,
            zorder=6,
            label="受限观测曲线",
        )
    )

    ax.annotate(
        fs.checked(f"只看第一条流 {aps[0]:.4f}%", FS_MIN),
        xy=(ks[0], aps[0]),
        xytext=(1.35, 32.3),
        fontsize=FS_MIN,
        color=INK,
        ha="left",
        va="center",
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.9, "shrinkB": 4},
        bbox={"boxstyle": "round,pad=0.26", "facecolor": "white", "edgecolor": MUTED, "linewidth": 0.7},
        zorder=8,
    )
    ax.annotate(
        fs.checked(
            f"前 50 条 {aps[idx50]:.4f}%\n读取的流占全部流的 {payload['coverage'][idx50]:.2f}%",
            FS_MIN,
        ),
        xy=(ks[idx50], aps[idx50]),
        xytext=(19.0, 33.6),
        fontsize=FS_MIN,
        color=INK,
        linespacing=1.35,
        ha="center",
        va="center",
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 0.9, "shrinkB": 4},
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": MUTED, "linewidth": 0.7},
        zorder=8,
    )

    ax.set_xticks(ks)
    ax.set_xticklabels([fs.checked(str(k), FS_MIN) for k in ks], fontsize=FS_MIN)
    ax.minorticks_off()
    ax.set_xlim(0.85, 135.0)
    ax.set_ylim(28.0, 48.5)
    ax.set_yticks([30, 35, 40, 45])
    ax.yaxis.set_major_formatter(pct_formatter(0))
    ax.set_xlabel(
        fs.checked("每个实体按时间使用的前若干条流（对数刻度）", FS_MAIN), fontsize=FS_MAIN, labelpad=3
    )
    ax.set_ylabel(fs.checked("实体平均精确率", FS_MAIN), fontsize=FS_MAIN)
    return fig


def draw_alert_budget_curve(ctx: dict[str, Any]) -> Figure:
    """图3-12 检出率随告警预算的变化（LSPR23 训练、LSPR24 测试）。

    数据源与其余四幅独立，见 load_alert_budget_curve()；绘图前已完成冻结数值复现自检。
    """
    c = ctx["alert"]
    fpr_pct = c["fpr"] * 100.0
    dr_ours_pct = c["dr_ours"] * 100.0
    dr_trans_pct = c["dr_trans"] * 100.0

    fig = new_figure(140, 95)
    ax = fig.add_axes((0.130, 0.360, 0.750, 0.560))
    style_axes(ax, grid_axis="both")
    ax.set_xscale("log")

    mark_idx = sorted(set(np.round(np.geomspace(2, c["n_neg"] - 2, 9)).astype(int).tolist()))
    mark_data(
        ax.plot(
            fpr_pct,
            dr_ours_pct,
            linestyle="-",
            linewidth=1.4,
            color=INK,
            marker="o",
            markersize=4.2,
            markerfacecolor="white",
            markeredgewidth=0.9,
            markevery=mark_idx,
            zorder=5,
            label=fs.checked("本章方法 CPA-ELP（学到的指数）", FS_MIN),
        )
    )
    mark_data(
        ax.plot(
            fpr_pct,
            dr_trans_pct,
            linestyle=(0, (5, 2)),
            linewidth=1.4,
            color=MUTED,
            marker="s",
            markersize=4.2,
            markerfacecolor="white",
            markeredgewidth=0.9,
            markevery=mark_idx,
            zorder=5,
            label=fs.checked("发表配置全注意力网络（取最大）", FS_MIN),
        )
    )

    ax.axvspan(c["lead_span"][0] * 100.0, c["lead_span"][1] * 100.0, color=MUTED, alpha=0.14, zorder=1)

    crossing_x = c["crossing_fpr"] * 100.0
    cross_dr = float(np.interp(c["crossing_fpr"], c["fpr"], c["dr_ours"])) * 100.0
    ax.axvline(crossing_x, color=ACCENT, linestyle=(0, (1, 1.6)), linewidth=1.1, zorder=3)
    ax.annotate(
        fs.checked(f"交叉点\n假阳率 {crossing_x:.2f}%", FS_MIN),
        xy=(crossing_x, cross_dr),
        xytext=(0.008, 92.0),
        fontsize=FS_MIN,
        color=ACCENT,
        linespacing=1.3,
        ha="left",
        va="top",
        arrowprops={"arrowstyle": "->", "color": ACCENT, "linewidth": 0.9, "shrinkB": 3},
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": ACCENT, "linewidth": 0.7},
        zorder=6,
    )

    ax.set_xlim(0.0018, 130)
    ax.set_ylim(0, 108)
    ticks = [0.01, 0.1, 1, 10, 100]
    ax.set_xticks(ticks)
    ax.set_xticklabels([fs.checked(f"{t:g}%", FS_MIN) for t in ticks], fontsize=FS_MIN)
    ax.minorticks_off()
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel(fs.checked("实体级假阳率（对数刻度）", FS_MAIN), fontsize=FS_MAIN, labelpad=4)
    ax.set_ylabel(fs.checked("实体级检出率", FS_MAIN), fontsize=FS_MAIN)
    ax.yaxis.set_major_formatter(pct_formatter(0))

    ax.legend(
        loc="lower right",
        frameon=True,
        framealpha=1.0,
        edgecolor=HAIRLINE,
        fontsize=FS_MIN,
        borderpad=0.4,
        handlelength=2.2,
        labelspacing=0.4,
    )

    lead_lo, lead_hi = c["lead_span"]
    fig.text(
        0.5,
        0.250,
        fs.checked(
            f"46,363 个负实体、752 个正实体，全部可达预算点逐点相减：本方法在 {c['win_frac'] * 100:.2f}%\n"
            f"的点上检出率更高；全注意力网络仅在假阳率 {lead_lo * 100:.2f}% 至 {lead_hi * 100:.2f}% 区间\n"
            f"领先（阴影区间），最大领先 {c['max_lead'] * 100:.2f} 个百分点。",
            FS_MIN,
        ),
        ha="center",
        va="top",
        fontsize=FS_MIN,
        linespacing=1.4,
        color=MUTED,
    )
    fig.text(
        0.5,
        0.100,
        fs.checked(
            f"假阳率 0.10% 处本方法高 {(c['dr010'][0] - c['dr010'][1]) * 100:.2f} 个百分点"
            f"（{c['dr010'][0] * 100:.2f}% 对 {c['dr010'][1] * 100:.2f}%）；\n"
            f"0.50% 处高 {(c['dr050'][0] - c['dr050'][1]) * 100:.2f} 个百分点"
            f"（{c['dr050'][0] * 100:.2f}% 对 {c['dr050'][1] * 100:.2f}%）。",
            FS_MIN,
        ),
        ha="center",
        va="top",
        fontsize=FS_MIN,
        linespacing=1.35,
        color=MUTED,
    )
    return fig


# ---------------------------------------------------------------------------
# 图件登记
# ---------------------------------------------------------------------------

SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        stem="图3-6-跨骨干机制增益与判读带宽",
        width_mm=132,
        height_mm=78,
        draw=draw_backbone_gain,
        check_group="backbone",
        data_sources=(
            "ch3-2x2-fairsel/ch3_2x2_fairsel_results.json :: cells.{C00,C11}.e_lp",
            "ch3-backbone-protocolA-v2/cnn/ch3_backbone_protocolA_results.json :: cells.{cnn-C00,cnn-C11}.e_lp",
            (
                "ch3-backbone-protocolA-v2/transformer/ch3_backbone_protocolA_results.json :: "
                "cells.{transformer-C00,transformer-C11}.e_lp"
            ),
            "ch3-backbone-protocolA-v2/gru/ch3_backbone_protocolA_results.json :: cells.{gru-C00,gru-C11}.e_lp",
            (
                "ch3-xgb-cpa-elp-gpu-oof-seed42-v1-rerun1-eval-continuation2/xgb_cpa_elp_results.json :: "
                "cells.{C00,C11}.ent_ap"
            ),
            "ch3-full/ch3_full_results.json :: stability.C11（判读带宽）",
        ),
        caption=(
            "图3-6 两个机制在五个骨干上的实体平均精确率增量与判读带宽（LSPR23 训练、LSPR24 测试）。"
            "横轴为两机制并用相对无机制的增量，以个百分点计；竖直虚线为 11.59 个百分点的判读带宽，"
            "取自完整方法三次重复训练中逐流平均精确率的最高与最低之差。多层感知机 18.34、"
            "沿流序列因果卷积 15.58 与全注意力 12.51 超出带宽，树集成 5.19 与门控循环 2.73 "
            "落在带宽之内。五行的增量方向一致，各行为单次运行。"
        ),
    ),
    FigureSpec(
        stem="图3-8-Lp指数收敛轨迹",
        width_mm=132,
        height_mm=84,
        draw=draw_lp_trajectory,
        check_group="lp",
        data_sources=(
            "ch3-2x2-fairsel/ch3_2x2_fairsel_results.json :: selection.{C01,C11}.val_ap_history",
            "ch3-2x2-fairsel/ch3_2x2_fairsel_results.json :: cells.{C01,C11}.{sel_epoch,p}",
        ),
        caption=(
            "图3-8 可学指数在训练过程中的取值变化（仅可学池化与双机制并用两个配置，LSPR23 训练）。"
            "横轴为训练轮次，纵轴为该轮结束时的指数取值。由式 (3-11) 初值为 2，两个配置都把它压低，"
            "都没有推向取最大一端。实心标记为按源年度检查点选择标准选中的轮次：仅可学池化选中第 14 轮，"
            "取值 0.5233；双机制并用选中第 10 轮，取值 1.0562。水平虚线标出指数为 1 的算术均值。"
        ),
    ),
    FigureSpec(
        stem="图3-9-序列长度敏感性",
        width_mm=124,
        height_mm=82,
        draw=draw_length_flow,
        check_group="length",
        data_sources=(
            ".Codex/docs/RWKV/2026-08-17-第三章XGBoost基线对照与门槛测算.md :: 第九节四档逐流三次取值",
            "ch3-full/ch3_full_results.json :: stability.C11（长度 128 档的交叉核对）",
        ),
        caption=(
            "图3-9 四档序列长度在等真实流预算下的跨年度逐流平均精确率（LSPR23 训练、LSPR24 测试）。"
            "每档三个空心圆为三次重复训练的取值，横线为该档均值，四档依次为 22.86%、29.57%、"
            "33.69% 与 24.20%，阴影为四档均值的跨度。档内三次取值的波动在 4.01 至 10.16 个百分点之间，"
            "与档间均值之差处在同一量级，本图不对四档排序。"
        ),
    ),
    FigureSpec(
        stem="图3-11-受限观测下的检测能力",
        width_mm=132,
        height_mm=86,
        draw=draw_topk_curve,
        check_group="topk",
        data_sources=("ch3-full/ch3_full_results.json :: curve.C11 的第 1、2、5 列",),
        caption=(
            "图3-11 每个实体只使用按时间最早的前若干条流时的实体平均精确率，横轴为对数刻度"
            "（LSPR23 训练、LSPR24 测试）。只看第一条流时为 29.9964%，取前 50 条时升到 45.7276%，"
            "达到使用全部流的 46.2988% 的 95% 以上，此时读取的流只占全部流的 2.27%。"
            "水平虚线为使用全部流的取值，竖直点线标出实体流数中位数 2。"
        ),
    ),
    FigureSpec(
        stem="图3-12-告警预算曲线",
        width_mm=140,
        height_mm=95,
        draw=draw_alert_budget_curve,
        check_group="alert",
        data_sources=(
            "dijk-repro/cache/ent24_local.npy",
            "dijk-repro/cache/y24.npy",
            "ch3-alert-budget-curve/entity_scores.npy",
            "ch3-alert-budget-curve/entity_scores_rows.json",
            "ch3-alert-budget-curve/alert_budget_curves.json :: methods.{ours_c11.lp,transformer_full.max}.entity_ap",
        ),
        caption=(
            "图3-12 检出率随告警预算的变化（LSPR23 训练、LSPR24 测试，比较本方法 CPA-ELP 与"
            "发表配置全注意力网络，横轴为实体级假阳率、纵轴为实体级检出率，46,363 个负实体与 "
            "752 个正实体）。两条曲线在假阳率 2.50% 处相交；在全部 46,363 个可达预算点中，"
            "本方法在 87.22% 的点上检出率更高。假阳率 0.10% 处本方法高 14.63 个百分点"
            "（26.46% 对 11.84%），0.50% 处高 28.99 个百分点（49.73% 对 20.74%）。"
            "全注意力网络仅在假阳率 2.52% 至 12.85% 区间领先（图中阴影），最大领先 4.52 个百分点。"
            "正文所引的预算点占比与各预算点上的差值由两条曲线在全部可达预算点上逐点相减得到，"
            "非按图目视读取。"
        ),
    ),
)


def build_context() -> dict[str, Any]:
    """加载全部数据源并完成正文一致性自检；任何一项不过在此报错，绝不进入绘图。"""

    full = load_full_results()
    ctx: dict[str, Any] = {
        "full": full,
        "backbone": load_backbone_gains(full),
        "lp": load_lp_trajectory(),
        "length": load_length_flow(full),
        "topk": load_topk_curve(full),
        "alert": load_alert_budget_curve(),
    }
    return ctx


def report_context(ctx: dict[str, Any], specs: tuple[FigureSpec, ...] = ()) -> None:
    """逐图打印数据来源键路径与自检结果，供人工核对。"""

    specs = specs or SPECS
    logger.info("=" * 96)
    logger.info("字体：中文 %s（%s）", fs.CJK_FONT.family, fs.CJK_FONT.path)
    logger.info("字体：西文 %s；数学 %s", fs.LATIN_FONT.family, fs.MATH_FONT.family if fs.MATH_FONT else "stix 回退")
    logger.info("=" * 96)
    for spec in specs:
        logger.info("[%s]", spec.stem)
        for source in spec.data_sources:
            logger.info("  数据来源 %s", source)
        for check in ctx[spec.check_group]["checks"]:
            logger.info(
                "  自检 %-38s 复现=%.6f 正文=%.6f 差=%.2e 容差=%g 通过",
                check.item,
                check.reproduced,
                check.thesis,
                abs(check.reproduced - check.thesis),
                check.tolerance,
            )
    logger.info("=" * 96)
    for item in WITHDRAWN:
        logger.info("[未重绘] %s：%s", item["stem"], item["reason"])
    logger.info("=" * 96)


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


def write_manifest(entries: list[dict[str, Any]]) -> None:
    """把本脚本的条目合并进 图件清单.json，保留仍有输出文件的其他图件条目。"""

    import PIL

    manifest: dict[str, Any] = {}
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open(encoding="utf-8") as handle:
            manifest = json.load(handle)

    mine = {entry["stem"] for entry in entries}
    # 旧名条目：图3-6 由「双机制消融交互」改绘为「跨骨干机制增益与判读带宽」，旧条目不得留存
    superseded = {"图3-6-双机制消融交互"}
    withdrawn = {item["stem"] for item in WITHDRAWN}
    kept: list[dict[str, Any]] = []
    for entry in manifest.get("figures", []):
        stem = entry.get("stem")
        if stem in mine or stem in withdrawn or stem in superseded:
            continue
        outputs = entry.get("outputs", {})
        if outputs and all((ROOT / name).exists() for name in outputs.values()):
            kept.append(entry)

    manifest = {
        "contract": "AGENTS.md 学位论文图件合同（2026-08-13 重定）",
        "environment": {
            "generator": "绘制第三章结果图.py（图3-6/3-8/3-9/3-11/3-12）与 绘制第三章机制图.py（图3-1~图3-4）",
            "python": ".".join(str(v) for v in sys.version_info[:3]),
            "matplotlib": matplotlib.__version__,
            "pillow": PIL.__version__,
        },
        "typography": {
            "resolver": "figstyle.py（字体由解析得到，不在绘图脚本内硬编码）",
            "cjk_font_requested": fs.CJK_FONT.requested,
            "cjk_font_used": fs.CJK_FONT.family,
            "cjk_font_path": fs.CJK_FONT.path,
            "cjk_face_index": fs.CJK_FONT.face_index,
            "latin_font_used": fs.LATIN_FONT.family,
            "latin_font_path": fs.LATIN_FONT.path,
            "math_font_used": fs.MATH_FONT.family if fs.MATH_FONT else "stix 回退",
            "min_font_pt": fs.MIN_FONT_PT,
            "main_font_pt": fs.MAIN_FONT_PT,
            "main_line_pt": fs.MAIN_LINE_PT,
            "aux_line_pt": fs.AUX_LINE_PT,
        },
        "grayscale_readable": True,
        "figures": sorted(kept + entries, key=_figure_sort_key),
        "withdrawn": [
            {
                **item,
                "note": "2026-08-18 以正文为准的重绘中撤下，未生成图件；是否另行处置由正文一侧裁决。",
            }
            for item in WITHDRAWN
        ],
    }

    with MANIFEST_PATH.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _figure_sort_key(entry: dict[str, Any]) -> tuple[int, str]:
    stem = str(entry.get("stem", ""))
    head = stem.split("-", 2)
    try:
        return (int(head[1]), stem)
    except (IndexError, ValueError):
        return (999, stem)


def select_specs(names: list[str]) -> tuple[FigureSpec, ...]:
    """按落盘名筛选要生成的图件。给空表则生成全部。"""

    if not names:
        return SPECS
    known = {spec.stem: spec for spec in SPECS}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise SystemExit(f"未登记的图件名：{unknown}；可选 {sorted(known)}")
    return tuple(known[name] for name in names)


def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(description="生成第三章实验结果图")
    parser.add_argument(
        "--only",
        nargs="+",
        default=[],
        metavar="落盘名",
        help="只生成指定图件；其余图件的文件与清单条目原样保留",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="只绘制并跑遮挡自检，不落盘、不改清单",
    )
    args = parser.parse_args(argv)
    specs = select_specs(args.only)

    ctx = build_context()
    report_context(ctx, specs)

    entries: list[dict[str, Any]] = []
    for spec in specs:
        fig = spec.draw(ctx)
        occ = check_occlusion(spec.stem, fig)
        logger.info(
            "遮挡自检 %s：不透明框 %d 个，可视数据点 %d 个（去重后 %d 个），"
            "落在框内 %d 个，最近间隙 %.2f pt，最大标记直径 %.1f pt",
            occ.stem,
            occ.n_boxes,
            occ.n_points,
            occ.n_distinct,
            occ.n_inside,
            occ.min_gap_pt,
            occ.marker_pt,
        )
        for line in occ.offenders:
            logger.info("    被遮挡 %s", line)
        if occ.n_inside and not args.check_only:
            raise ValueError(
                f"遮挡自检失败：{spec.stem} 有 {occ.n_inside} 个数据元素落在不透明框内，"
                "停止，须改图例或注记的位置，不得删点或改坐标范围"
            )
        if args.check_only:
            plt.close(fig)
            continue
        outputs = save_figure(spec, fig)
        entries.append(
            {
                "stem": spec.stem,
                "caption": spec.caption,
                "width_mm": round(spec.width_mm, 2),
                "height_mm": round(spec.height_mm, 2),
                "png_dpi": PNG_DPI,
                "outputs": outputs,
                "generator": "绘制第三章结果图.py",
                "evidence_mode": "frozen_experiment_results",
                "data_sources": list(spec.data_sources),
                "consistency_checks": [check.as_dict() for check in ctx[spec.check_group]["checks"]],
                "occlusion_check": {
                    "不透明框数": occ.n_boxes,
                    "可视数据点数": occ.n_points,
                    "落在框内的数据点数": occ.n_inside,
                    "最近间隙_pt": round(occ.min_gap_pt, 2),
                },
            }
        )

    if args.check_only:
        logger.info("只跑自检，未落盘")
        return

    for line in fs.verify_outputs(ROOT, entries):
        logger.info("已生成 %s", line)

    write_manifest(entries)
    logger.info("图件清单已更新：%s", MANIFEST_PATH)


if __name__ == "__main__":
    main()
