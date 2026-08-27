"""第三章结果图的取数层：只从当前权威制品读字段，不接受任何手工录入的数值。

职责边界：本模块负责定位制品、登记 SHA-256、按键路径取字段、按合同口径重算派生量，
不含任何绘图代码。绘图由 `绘制第三章结果图.py` 负责。

权威制品（2026-08-26 由 RWKV 第三章恢复卡与研究问题卡指定）：

- 正式 CPA×ELP 四格（BF16 单种子 seed42）
  `runs/diagnostics/ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1/`
  位语义已源码核验：`tools/ch3_full_mlp_complete_entity_lp_protocol_a_q0.py:36-41`，
  `B00`＝双关、`B10`＝仅因果前缀聚合、`O01`＝仅实体级幂平均池化、`O11`＝双开。
- 统一指标总表 `runs/diagnostics/ch3-metrics-table-20260825b/`
- 已发表神经基线完整告警预算曲线
  `runs/diagnostics/ch3-published-neural-operational-backfill-v1/`

口径纪律：检出率一律按「实际可达假阳率不超过名义预算的最接近点」重算，不使用制品里
`dr_at_fpr` 的名义秩位键——该键已被 2026-08-26 审查证伪（并列块全告警的平凡点）。
本模块的重算规则以统一总表读数为准并逐条自校（见 `verify_against_metrics_table`）。
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RUNS = REPO / "thesis/experiments/llm_probe/runs/diagnostics"

BF16_DIR = RUNS / "ch3-full-mlp-complete-entity-lp-protocol-a-q0-seed42-v1-bf16-v1"
TABLE_DIR = RUNS / "ch3-metrics-table-20260825b"
PUBLISHED_DIR = RUNS / "ch3-published-neural-operational-backfill-v1"

BF16_AGGREGATE = BF16_DIR / "aggregate-results.json"
BF16_SELECTION = BF16_DIR / "selection_frozen.json"
BF16_CURVES = BF16_DIR / "complete-alert-budget-curves.npz"
BF16_CURVES_RECEIPT = BF16_DIR / "complete-alert-budget-curves-receipt.json"
TABLE_LSPR24 = TABLE_DIR / "lspr24-evaluation.json"
TABLE_PROVENANCE = TABLE_DIR / "provenance.json"
PUBLISHED_CURVES = PUBLISHED_DIR / "complete-alert-budget-curves.npz"

# 名义告警预算档位；实际工作点由各方法自身曲线的可达点决定。
NOMINAL_BUDGETS: tuple[float, ...] = (0.001, 0.005, 0.01, 0.02, 0.04, 0.08)

# 四格位语义与展示名。展示名直接表达机制，不要求读者查表。
CELL_ORDER: tuple[str, ...] = ("B00", "B10", "O01", "O11")
CELL_NAMES: dict[str, str] = {
    "B00": "无机制基线",
    "B10": "仅因果前缀聚合",
    "O01": "仅实体级幂平均池化",
    "O11": "双机制并用（本章完整方法）",
}
CELL_SHORT: dict[str, str] = {
    "B00": "无机制\n基线",
    "B10": "仅因果\n前缀聚合",
    "O01": "仅实体级\n幂平均池化",
    "O11": "双机制并用\n（本章方法）",
}


class ArtifactMissing(FileNotFoundError):
    """权威制品不在本机时抛出，附带远程拉取提示，不静默降级到旧数据。"""


@dataclass(frozen=True)
class Source:
    """一份被读取的制品文件及其内容哈希。"""

    role: str
    path: str
    sha256: str
    bytes: int


class Registry:
    """记录本次绘图读过的每一个制品文件，供图件清单登记。"""

    def __init__(self) -> None:
        self._items: dict[str, Source] = {}

    def add(self, role: str, path: Path) -> Path:
        if not path.exists():
            raise ArtifactMissing(
                f"权威制品缺失：{path}\n"
                f"请先用 tools/remote_exec/gpu_rsync_pull.exp 从服务器 "
                f"/root/autodl-tmp/thesis/experiments/llm_probe/ 下同名路径拉取。"
            )
        raw = path.read_bytes()
        key = str(path.relative_to(REPO))
        self._items[key] = Source(
            role=role,
            path=key,
            sha256=hashlib.sha256(raw).hexdigest(),
            bytes=len(raw),
        )
        return path

    def dump(self) -> list[dict[str, Any]]:
        return [
            {
                "role": item.role,
                "path": item.path,
                "sha256": item.sha256,
                "bytes": item.bytes,
            }
            for item in sorted(self._items.values(), key=lambda s: s.path)
        ]


def _read_json(registry: Registry, role: str, path: Path) -> Any:
    return json.loads(registry.add(role, path).read_text(encoding="utf-8"))


def budget_readout(
    realized_fpr: np.ndarray, detection_rate: np.ndarray
) -> dict[float, tuple[float, float]]:
    """按合同口径重算六档检出率。

    规则：在完整可达曲线上取实际假阳率不超过名义预算的最后一个点，返回
    （实际假阳率，检出率）。曲线按假阳实体数递增排列，实际假阳率单调不减。
    """

    if not np.all(np.diff(realized_fpr) >= -1e-12):
        raise ValueError("完整告警预算曲线的实际假阳率非单调，取数规则不成立")
    out: dict[float, tuple[float, float]] = {}
    for nominal in NOMINAL_BUDGETS:
        mask = realized_fpr <= nominal + 1e-15
        if not mask.any():
            raise ValueError(f"曲线在名义预算 {nominal} 下没有可达点")
        index = int(np.flatnonzero(mask)[-1])
        out[nominal] = (float(realized_fpr[index]), float(detection_rate[index]))
    return out


@dataclass(frozen=True)
class MethodRow:
    """统一指标总表里的一个方法行。"""

    display_name: str
    config_type: str
    run_id: str
    flow_ap: float
    entity_ap: float
    dr_at_4pct: float
    actual_fpr_at_4pct: float | None
    has_complete_curve: bool


# 图 3-5 采用的六个方法：五个已发表配置基线 ＋ 本章方法。
# 键为总表 display_name，值为图内展示名（本章方法额外标注骨干与精度）。
FIGURE5_METHODS: tuple[tuple[str, str], ...] = (
    ("随机森林", "随机森林"),
    ("XGBoost", "XGBoost"),
    ("一维卷积网络（主干重建）", "一维卷积网络"),
    ("门控循环网络", "门控循环网络"),
    ("全注意力网络", "全注意力网络"),
    (
        "全容量多层感知机＋完整实体幂平均（BF16）",
        "本章方法\n（全容量多层感知机）",
    ),
)


def load_metrics_table(registry: Registry) -> list[MethodRow]:
    """读统一指标总表的 LSPR24 评价行，按图 3-5 的六个方法取子集并保序。"""

    rows = _read_json(registry, "统一指标总表 LSPR24 评价", TABLE_LSPR24)
    _read_json(registry, "统一指标总表溯源", TABLE_PROVENANCE)
    by_name = {row["display_name"]: row for row in rows}

    picked: list[MethodRow] = []
    for source_name, display in FIGURE5_METHODS:
        if source_name not in by_name:
            raise KeyError(f"统一总表缺少方法行：{source_name}")
        row = by_name[source_name]
        for field in ("flow_ap", "entity_ap", "dr_fpr_0.04"):
            if row[field] is None:
                raise ValueError(f"{source_name} 的 {field} 为空，不能进图")
        picked.append(
            MethodRow(
                display_name=display,
                config_type=row["config_type"],
                run_id=row["run_id"],
                flow_ap=float(row["flow_ap"]),
                entity_ap=float(row["entity_ap"]),
                dr_at_4pct=float(row["dr_fpr_0.04"]),
                actual_fpr_at_4pct=(
                    None
                    if row["actual_fpr_fpr_0.04"] is None
                    else float(row["actual_fpr_fpr_0.04"])
                ),
                has_complete_curve=row["dr_curve_artifact"] is not None,
            )
        )
    return picked


@dataclass(frozen=True)
class AblationCell:
    """正式 CPA×ELP 四格中的一格。"""

    key: str
    entity_ap: float
    flow_ap: float
    realized_fpr_at_2pct: float
    dr_at_2pct: float
    learned_p: float | None
    selected_epoch: int
    validation_history: tuple[tuple[int, float, float], ...]
    length_buckets: tuple[dict[str, Any], ...]


def load_ablation(registry: Registry) -> tuple[dict[str, AblationCell], dict[str, Any]]:
    """读正式四格：目标年指标、六档实际可达检出率、逐轮历史与长度分桶。"""

    aggregate = _read_json(registry, "正式 CPA×ELP 四格聚合结果", BF16_AGGREGATE)
    selection = _read_json(registry, "正式 CPA×ELP 四格选轮冻结", BF16_SELECTION)
    _read_json(registry, "正式四格完整告警预算曲线收据", BF16_CURVES_RECEIPT)
    curves = np.load(registry.add("正式四格完整告警预算曲线", BF16_CURVES))

    target = aggregate["target_year_table"]
    cells: dict[str, AblationCell] = {}
    for key in CELL_ORDER:
        readout = budget_readout(
            curves[f"{key}__realized_fpr"], curves[f"{key}__detection_rate"]
        )
        history = tuple(
            (int(item["epoch"]), float(item["validation_flow_ap"]), float(item["p"]))
            for item in selection["cells"][key]["history"]
        )
        cells[key] = AblationCell(
            key=key,
            entity_ap=float(target[key]["entity_average_precision"]),
            flow_ap=float(target[key]["flow_average_precision"]),
            realized_fpr_at_2pct=readout[0.02][0],
            dr_at_2pct=readout[0.02][1],
            learned_p=(None if target[key]["p"] is None else float(target[key]["p"])),
            selected_epoch=int(selection["cells"][key]["selected_epoch"]),
            validation_history=history,
            length_buckets=tuple(target[key]["length_buckets"]),
        )

    meta = {
        "run_id": aggregate["run_id"],
        "entity_count": int(aggregate["target_evaluation"]["entity_count"]),
        "positive_entity_count": int(
            aggregate["target_evaluation"]["positive_entity_count"]
        ),
        "flow_count": int(aggregate["target_evaluation"]["flow_count"]),
        "negative_entity_count": int(
            aggregate["target_evaluation"]["entity_count"]
            - aggregate["target_evaluation"]["positive_entity_count"]
        ),
        "seed": 42,
        "protocol": selection["protocol"],
    }
    return cells, meta


def ablation_effects(cells: dict[str, AblationCell]) -> dict[str, float]:
    """按预注册 2×2 设计算主效应、组合增益与交互项（目标年实体平均精确率）。"""

    v = {key: cells[key].entity_ap for key in CELL_ORDER}
    causal = v["B10"] - v["B00"]
    pooling = v["O01"] - v["B00"]
    return {
        "causal_prefix": causal,
        "entity_pooling": pooling,
        "sum": causal + pooling,
        "combined": v["O11"] - v["B00"],
        "interaction": v["O11"] - v["B10"] - v["O01"] + v["B00"],
    }


@dataclass(frozen=True)
class FirstAlertStep:
    """某个告警预算下，完整方法的首次告警及时检出阶梯。"""

    nominal: float
    realized_fpr: float
    threshold: float
    alerted_positive_entities: int
    positive_unalerted_rate: float
    exposure_index: tuple[int, ...]
    on_time_detection_rate: tuple[float, ...]


def load_first_alert(registry: Registry, cell: str = "O11") -> tuple[FirstAlertStep, ...]:
    """读完整方法在六档预算下的首次告警及时检出阶梯（横轴为实体内暴露序号）。"""

    aggregate = _read_json(registry, "正式 CPA×ELP 四格聚合结果", BF16_AGGREGATE)
    curves = np.load(registry.add("正式四格完整告警预算曲线", BF16_CURVES))
    first_alert = aggregate["target_year_table"][cell]["first_alert"]

    steps: list[FirstAlertStep] = []
    for nominal in NOMINAL_BUDGETS:
        key = f"fpr_{nominal:g}"
        record = first_alert[key]
        steps.append(
            FirstAlertStep(
                nominal=nominal,
                realized_fpr=float(record["realized_first_alert_fpr"]),
                threshold=float(record["threshold"]),
                alerted_positive_entities=int(record["alerted_positive_entities"]),
                positive_unalerted_rate=float(record["positive_unalerted_rate"]),
                exposure_index=tuple(
                    int(v) for v in curves[f"{cell}__first_alert__{key}__exposure_index"]
                ),
                on_time_detection_rate=tuple(
                    float(v)
                    for v in curves[f"{cell}__first_alert__{key}__on_time_detection_rate"]
                ),
            )
        )
    return tuple(steps)


@dataclass(frozen=True)
class BudgetCurve:
    """一条完整的告警预算曲线：实际假阳率对检出率。"""

    display_name: str
    realized_fpr: np.ndarray
    detection_rate: np.ndarray
    readout: dict[float, tuple[float, float]]
    reachable_fpr_ceiling: float
    points_below_8pct: int


# 图 3-12 的曲线集合：本章方法 ＋ 三个有完整曲线的已发表神经基线。
# 随机森林与已发表配置 XGBoost 只持久化 4% 单点，无完整曲线，不能进本图。
def load_budget_curves(registry: Registry) -> tuple[BudgetCurve, ...]:
    """读完整告警预算曲线；ceiling 为 8% 预算内的最大实际可达假阳率。"""

    bf16 = np.load(registry.add("正式四格完整告警预算曲线", BF16_CURVES))
    published = np.load(
        registry.add("已发表神经基线完整告警预算曲线", PUBLISHED_CURVES)
    )
    _read_json(registry, "已发表神经基线运行结果", PUBLISHED_DIR / "aggregate-results.json")

    raw: list[tuple[str, np.ndarray, np.ndarray]] = [
        (
            "本章方法（双机制并用）",
            bf16["O11__realized_fpr"],
            bf16["O11__detection_rate"],
        ),
        (
            "全注意力网络",
            published["transformer__actual_fpr"],
            published["transformer__detection_rate"],
        ),
        (
            "一维卷积网络",
            published["cnn__actual_fpr"],
            published["cnn__detection_rate"],
        ),
        (
            "门控循环网络",
            published["gru__actual_fpr"],
            published["gru__detection_rate"],
        ),
    ]

    out: list[BudgetCurve] = []
    for name, fpr, dr in raw:
        below = fpr <= 0.08 + 1e-15
        out.append(
            BudgetCurve(
                display_name=name,
                realized_fpr=np.asarray(fpr, dtype=float),
                detection_rate=np.asarray(dr, dtype=float),
                readout=budget_readout(fpr, dr),
                reachable_fpr_ceiling=float(fpr[below].max()),
                points_below_8pct=int(below.sum()),
            )
        )
    return tuple(out)


def verify_against_metrics_table(registry: Registry) -> list[str]:
    """自校：曲线重算的六档读数必须与统一指标总表逐位相等，否则取数规则不成立。

    这是本模块唯一的正确性断言——它把「本脚本的重算」钉死在「统一总表的重算」上，
    使图内每个检出率都能指回总表字段，而不是脚本自定义口径。
    """

    rows = {
        row["display_name"]: row
        for row in _read_json(registry, "统一指标总表 LSPR24 评价", TABLE_LSPR24)
    }
    bf16 = np.load(registry.add("正式四格完整告警预算曲线", BF16_CURVES))
    published = np.load(
        registry.add("已发表神经基线完整告警预算曲线", PUBLISHED_CURVES)
    )

    pairs = (
        (
            "全容量多层感知机＋完整实体幂平均（BF16）",
            bf16["O11__realized_fpr"],
            bf16["O11__detection_rate"],
        ),
        (
            "全注意力网络",
            published["transformer__actual_fpr"],
            published["transformer__detection_rate"],
        ),
        (
            "一维卷积网络（主干重建）",
            published["cnn__actual_fpr"],
            published["cnn__detection_rate"],
        ),
        (
            "门控循环网络",
            published["gru__actual_fpr"],
            published["gru__detection_rate"],
        ),
    )

    report: list[str] = []
    for name, fpr, dr in pairs:
        readout = budget_readout(fpr, dr)
        for nominal in NOMINAL_BUDGETS:
            expected_dr = rows[name][f"dr_fpr_{nominal:g}"]
            expected_fpr = rows[name][f"actual_fpr_fpr_{nominal:g}"]
            if expected_dr is None:
                continue
            got_fpr, got_dr = readout[nominal]
            if abs(got_dr - float(expected_dr)) > 1e-12:
                raise ValueError(
                    f"{name} 名义 {nominal} 档检出率重算 {got_dr!r} "
                    f"与统一总表 {expected_dr!r} 不符"
                )
            if expected_fpr is not None and abs(got_fpr - float(expected_fpr)) > 1e-12:
                raise ValueError(
                    f"{name} 名义 {nominal} 档实际假阳率重算 {got_fpr!r} "
                    f"与统一总表 {expected_fpr!r} 不符"
                )
        report.append(f"{name}：六档读数与统一指标总表逐位一致")
    return report
