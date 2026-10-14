"""第三章（LAMDA 线）结果图的取数层：只从权威制品读字段，不接受手工录入的读数。

职责边界：本模块负责定位制品、登记 SHA-256、按报告口径取数与重算派生量，不含任何
绘图代码。绘图由 `绘制第三章LAMDA结果图.py` 负责。

唯一权威制品目录（第三章 LAMDA 线）：

    thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-domain-il-e4-replication-v1/

该目录受 Git 忽略。本机缺失时由 `ArtifactMissing` 报出精确路径，不静默改用旧数据。

报告口径（3.2.1）：取最后一个 experience（2025）的 `backward` 记录，覆盖 12 个测试
年度，主指标为这 12 个 F1 的算术平均。`forward` 记录与 `backward` 语义不同，本模块
只读 `backward`，两者不混用。

本模块只登记两类外部给定常数，且均在下方以常量表与来源说明显式标注：其一是官方
协议的默认容量与容量档位配置（运行身份元数据，不是测量结果）；其二是零训练缓冲
构成审计的逐年度槽位与正例数（主代理实测、无对应制品字段）。其余一切数字都由
`metrics_*.json` 的 `records` 现场重算。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
ARTIFACT_DIR = (
    REPO
    / "thesis/experiments/llm_probe/runs/diagnostics/ch3-lamda-domain-il-e4-replication-v1"
)

# ---------------------------------------------------------------- 口径与常数

REPORT_EXPERIENCE = 2025
REPORT_MODE = "backward"
TEST_YEARS: tuple[int, ...] = (
    2013,
    2014,
    2016,
    2017,
    2018,
    2019,
    2020,
    2021,
    2022,
    2023,
    2024,
    2025,
)
# 定理 3（式 3.14）的两个集合：九年漂移集合与三年枯竭集合。
NINE_YEARS: tuple[int, ...] = TEST_YEARS[:9]
THREE_YEARS: tuple[int, ...] = TEST_YEARS[9:]

# 特征与模型常数（3.2.1、3.3.1）：4561 维二值特征按整字节存储，模型 2,687,293 个
# 单精度参数。缓冲与参数侧的存储全部由这两个常数推出，不另设数值。
BITS_PER_SAMPLE = 4561
MODEL_PARAMS = 2_687_293
FLOAT_BYTES = 4
# 全部已到达年度训练分片合计（3.6.1），用于联合训练的存储刻度。
TRAIN_TOTAL = 806_700


def sample_storage_kib(capacity: int) -> float:
    """N 条二值样本的缓冲存储（KiB），由式 (3-2) 的编码长度推出。"""

    return capacity * BITS_PER_SAMPLE / 8.0 / 1024.0


def param_storage_kib(copies: float) -> float:
    """参数侧存储（KiB）：copies 份单精度模型体积。"""

    return copies * MODEL_PARAMS * FLOAT_BYTES / 1024.0


# ---------------------------------------------------------------- 制品登记


class ArtifactMissing(FileNotFoundError):
    """权威制品不在本机时抛出，附带拉取提示，不静默降级到旧数据。"""


class Registry:
    """记录本次绘图读过的每一个制品文件，供图件清单登记。"""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def add(self, role: str, path: Path) -> Path:
        if not path.exists():
            raise ArtifactMissing(
                f"权威制品缺失：{path}\n"
                f"请先用 tools/remote_exec/gpu_rsync_pull.exp 从服务器 "
                f"/root/autodl-tmp/thesis/experiments/llm_probe/ 下同名路径拉取。"
            )
        raw = path.read_bytes()
        key = str(path.relative_to(REPO))
        self._items[key] = {
            "role": role,
            "path": key,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
        return path

    def dump(self) -> list[dict[str, Any]]:
        return [self._items[k] for k in sorted(self._items)]


# ---------------------------------------------------------------- 实验臂登记


@dataclass(frozen=True)
class Arm:
    """一条实验臂：制品文件、缓冲容量、复用倍数、缓冲构成方式与所属通路。

    容量与复用倍数是该次运行的配置身份（来自运行命令与文件名），不是测量读数；
    它们决定缓冲存储刻度，并由本模块按 BITS_PER_SAMPLE 换算为 KiB。
    参数侧三臂与联合训练没有样本缓冲，其容量记为 None，存储由 `storage_kib` 单独给出。
    """

    key: str
    filename: str
    display: str
    side: str  # sample / param / reference
    capacity: int | None
    reuse: int
    composition: str  # reservoir / quota / none / all

    @property
    def path(self) -> Path:
        return ARTIFACT_DIR / self.filename

    def storage_kib(self) -> float:
        """该臂的存储占用（KiB）。"""

        if self.composition == "all":
            return sample_storage_kib(TRAIN_TOTAL)
        if self.capacity is not None:
            return sample_storage_kib(self.capacity)
        if self.key == "ewc":
            # 弹性权重巩固需同时保留参数副本与其对角曲率估计（3.6.4）。
            return param_storage_kib(2.0)
        if self.side == "param":
            return param_storage_kib(1.0)
        return 0.0  # 朴素更新不携带任何历史信息


# 展示名直接表达机制与角色，纯代号不作唯一名称。
ARMS: tuple[Arm, ...] = (
    Arm("naive", "metrics_naive.json", "朴素更新", "reference", None, 1, "none"),
    Arm("m50", "metrics_expreplay_m50.json", "回放容量 50", "sample", 50, 1, "reservoir"),
    Arm("m200", "metrics_expreplay.json", "回放容量 200（官方）", "sample", 200, 1, "reservoir"),
    Arm("m400", "metrics_expreplay_m400.json", "回放容量 400", "sample", 400, 1, "reservoir"),
    Arm("m800", "metrics_expreplay_m800.json", "回放容量 800", "sample", 800, 1, "reservoir"),
    Arm(
        "m18854",
        "metrics_expreplay_m18854.json",
        "回放容量 18,854",
        "sample",
        18854,
        1,
        "reservoir",
    ),
    Arm("m200_r2", "metrics_expreplay_m200_r2.json", "容量 200 复用 2", "sample", 200, 2, "reservoir"),
    Arm("m200_r4", "metrics_expreplay_m200_r4.json", "容量 200 复用 4", "sample", 200, 4, "reservoir"),
    Arm("m200_r8", "metrics_expreplay_m200_r8.json", "容量 200 复用 8", "sample", 200, 8, "reservoir"),
    Arm("m800_r2", "metrics_expreplay_m800_r2.json", "容量 800 复用 2", "sample", 800, 2, "reservoir"),
    Arm(
        "quota",
        "metrics_expreplay_m200_quota.json",
        "按年度配额 复用 1",
        "sample",
        200,
        1,
        "quota",
    ),
    Arm(
        "quota_r2",
        "metrics_expreplay_m200_quota_r2.json",
        "按年度配额 复用 2（本章方法）",
        "sample",
        200,
        2,
        "quota",
    ),
    Arm("freemoca", "metrics_freemoca.json", "逐参数位移插值", "param", None, 1, "none"),
    Arm("ewc", "metrics_ewc.json", "弹性权重巩固", "param", None, 1, "none"),
    Arm("lwf", "metrics_lwf.json", "无遗忘学习", "param", None, 1, "none"),
    Arm("cumulative", "metrics_cumulative.json", "联合训练（上界）", "reference", None, 1, "all"),
)

BY_KEY: dict[str, Arm] = {arm.key: arm for arm in ARMS}


# ---------------------------------------------------------------- 读数


@dataclass(frozen=True)
class Record:
    test_year: int
    f1: float
    precision: float
    recall: float
    accuracy: float
    n: int
    n_pos: int


@dataclass(frozen=True)
class ArmReadout:
    """一条臂在报告口径下的读数。"""

    key: str
    display: str
    cross_year_f1: float
    yearly: dict[int, Record]
    storage_kib: float
    capacity: int | None
    reuse: int
    composition: str
    sha256: str

    def f1_percent(self) -> dict[int, float]:
        return {year: record.f1 * 100.0 for year, record in self.yearly.items()}


def _load_records(registry: Registry, arm: Arm) -> list[dict[str, Any]]:
    path = registry.add(f"{arm.display} 指标制品", arm.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload["records"]
    if not isinstance(raw, list):
        raise ValueError(f"{arm.filename} 的 records 不是列表")
    return raw


def load_arm(registry: Registry, key: str) -> ArmReadout:
    """读一条臂：取报告 experience 的 backward 记录，重算跨年平均 F1。"""

    arm = BY_KEY[key]
    raw = _load_records(registry, arm)
    picked = [r for r in raw if r["experience"] == REPORT_EXPERIENCE and r["mode"] == REPORT_MODE]
    if len(picked) != len(TEST_YEARS):
        raise ValueError(
            f"{arm.filename} 在 experience={REPORT_EXPERIENCE} 的 {REPORT_MODE} 记录有 "
            f"{len(picked)} 条，期望 {len(TEST_YEARS)} 条"
        )
    yearly: dict[int, Record] = {}
    for r in picked:
        year = int(r["test_year"])
        if year in yearly:
            raise ValueError(f"{arm.filename} 的测试年 {year} 重复")
        yearly[year] = Record(
            test_year=year,
            f1=float(r["f1"]),
            precision=float(r["precision"]),
            recall=float(r["recall"]),
            accuracy=float(r["accuracy"]),
            n=int(r["n"]),
            n_pos=int(r["n_pos"]),
        )
    if sorted(yearly) != list(TEST_YEARS):
        raise ValueError(f"{arm.filename} 的测试年集合与合同不一致：{sorted(yearly)}")
    return ArmReadout(
        key=arm.key,
        display=arm.display,
        cross_year_f1=sum(r.f1 for r in yearly.values()) / len(TEST_YEARS),
        yearly=yearly,
        storage_kib=arm.storage_kib(),
        capacity=arm.capacity,
        reuse=arm.reuse,
        composition=arm.composition,
        sha256=registry.dump()[-1]["sha256"],
    )


def load_all(registry: Registry) -> dict[str, ArmReadout]:
    return {arm.key: load_arm(registry, arm.key) for arm in ARMS}


# ---------------------------------------------------------------- 派生量


def positive_rate_percent(readout: ArmReadout) -> dict[int, float]:
    """各年度正例率（%）。

    3.2.1 规定每个年度的训练分片与测试分片类别构成一致，故该率由测试分片的
    n_pos/n 直接给出，与 3.2.2、3.6.8 报告的训练正例率同值。本函数不引入外部常数。
    任一条臂的 n_pos 与 n 都相同（测试分片固定），此处以朴素臂为准。
    """

    return {
        year: 100.0 * record.n_pos / record.n for year, record in sorted(readout.yearly.items())
    }


def positive_counts(readout: ArmReadout) -> dict[int, tuple[int, int]]:
    """各测试年度的（样本数, 正例数），用于图注披露测试分片规模。"""

    return {year: (record.n, record.n_pos) for year, record in sorted(readout.yearly.items())}


def gap_channels_percent(
    registry: Registry, readout: ArmReadout, joint: ArmReadout
) -> dict[str, float]:
    """按定理 3（式 3.14）把总缺口分解为漂移通道与枯竭通道。

    返回单位为百分点。9/12 与 3/12 的权重来自两个集合的基数，不另设参数。
    """

    a = readout.f1_percent()
    j = joint.f1_percent()
    drift = sum(j[y] - a[y] for y in NINE_YEARS) / len(NINE_YEARS)
    deplete = sum(j[y] - a[y] for y in THREE_YEARS) / len(THREE_YEARS)
    total = sum(j[y] - a[y] for y in TEST_YEARS) / len(TEST_YEARS)
    reconstructed = len(NINE_YEARS) / 12.0 * drift + len(THREE_YEARS) / 12.0 * deplete
    if abs(reconstructed - total) > 1e-9:
        raise ValueError("缺口的通道分解与总缺口不相等，式 (3.14) 未成立")
    return {"drift": drift, "depletion": deplete, "total": total}


def closure_percent(readout: ArmReadout, naive: ArmReadout, joint: ArmReadout) -> float:
    """缺口闭合率（%），式 (3.22)。"""

    span = (joint.cross_year_f1 - naive.cross_year_f1) * 100.0
    got = (readout.cross_year_f1 - naive.cross_year_f1) * 100.0
    return got / span * 100.0


# ---------------------------------------------------------------- 外部给定常数（显式登记）

# 官方蓄水池在容量 200 下运行至 12 个年度结束后的年度构成审计（零训练）。
# 来源：主代理 2026-10-14 实测的官方抽样过程逐年度审计结果，与 3.6.8 表 3-7 同值。
# 该量不对应任何 `metrics_*.json` 字段，故在此以常量表登记，并在图件清单中标为
# evidence_mode="外部给定常数（零训练审计）"；不得当作本模块从制品重算的读数。
BUFFER_AUDIT: tuple[tuple[int, int, int], ...] = (
    # (年度, 缓冲槽位数, 其中正例数)
    (2013, 11, 8),
    (2018, 25, 12),
    (2022, 25, 13),
    (2023, 14, 1),
    (2024, 10, 0),
    (2025, 7, 0),
)
BUFFER_AUDIT_SOURCE = (
    "主代理 2026-10-14 零训练审计实测（官方全局蓄水池，容量 200），"
    "与 3.6.8 表 3-7 同值；无对应制品字段"
)
