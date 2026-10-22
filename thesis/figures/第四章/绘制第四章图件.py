#!/usr/bin/env python3
"""绘制第四章的五幅图件。

- 图 4-1 预算约束成员化训练的总体结构（依据 4.3、4.4 正文）
- 图 4-2 三类显式分工约束的成员分歧轨迹与跨年读数
- 图 4-3 参数总量与跨年平均 F1 的对照（五种配置的预算位置）
- 图 4-4 成员数与骨干宽度的敏感性曲线
- 图 4-5 增益的双通道分解与成员分歧的逐年形态

规格来源：仓库根 `AGENTS.md`「学位论文图件合同」与
`thesis/figures/AGENTS.md`。样式基础设施复用 `thesis/figures/第三章/figstyle.py`，
本脚本只负责第四章的图件内容、数据断言、导出与清单登记。

运行方式（在仓库根执行）：
    uv run --project "thesis/figures/第四章" --locked python \
        "thesis/figures/第四章/绘制第四章图件.py"

图 4-2、4-3、4-4、4-5 的每一个绘制数值都来自运行制品 JSON，并在读取阶段
逐项断言；图 4-1 的参数量与损失/评测合同同样从 tabm4-result.json 读取后绘制。
"""

from __future__ import annotations

import hashlib
import json
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "第三章"))

import figstyle as fs  # noqa: E402

from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402

DIAG = REPO / "thesis/experiments/llm_probe/runs/diagnostics"
NCL_DIR = DIAG / "ch4-lamda-ncl-pilot"
CORR_DIR = DIAG / "ch4-lamda-corr-pilot"
GENERAL_DIR = DIAG / "ch4-lamda-general-pilot"
BASELINE_DIR = DIAG / "ch4-lamda-baselines-pilot"
TABM_DIR = DIAG / "ch4-lamda-tabm-pilot"
PAAT_DIR = DIAG / "ch4-lamda-paat-pilot"

YEARS = (
    "2013",
    "2014",
    "2016",
    "2017",
    "2018",
    "2019",
    "2020",
    "2021",
    "2022",
    "2023",
    "2024",
    "2025",
)
EPOCHS = tuple(range(1, 11))
ARMS = ("train_single", "ncl05", "ncl2", "corr05", "corr10")
NCL_ARMS = ("train_single", "ncl05", "ncl2")
CORR_ARMS = ("corr05", "corr10")
GENERATOR_REL = "thesis/figures/第四章/绘制第四章图件.py"

# 4.3.2 节登记的参数拆分；其和必须等于 tabm4-result.json 的总参数量。
SHARED_TRUNK_PARAMS = 2686014
MEMBER_ADAPTER_PARAMS = 37291


# ---------------------------------------------------------------- 读取与断言


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_close(
    actual: float,
    expected: float,
    *,
    tol: float = 1e-12,
    what: str,
) -> None:
    if abs(actual - expected) > tol:
        raise ValueError(f"{what} 不一致：{actual!r} vs {expected!r}（容差 {tol}）")


def assert_equal(actual: object, expected: object, what: str) -> None:
    if actual != expected:
        raise ValueError(f"{what} 不一致：{actual!r} vs {expected!r}")


def load_constraint_arms() -> dict[str, dict[str, object]]:
    """读取五臂逐轮不一致率，并与各自的汇总文件逐项核对。"""

    ncl_comparison = load_json(NCL_DIR / "ncl-comparison.json")
    corr_comparison = load_json(CORR_DIR / "corr-comparison.json")
    comparisons = {
        "train_single": ncl_comparison,
        "ncl05": ncl_comparison,
        "ncl2": ncl_comparison,
        "corr05": corr_comparison,
        "corr10": corr_comparison,
    }
    directories = {
        "train_single": NCL_DIR,
        "ncl05": NCL_DIR,
        "ncl2": NCL_DIR,
        "corr05": CORR_DIR,
        "corr10": CORR_DIR,
    }

    arms: dict[str, dict[str, object]] = {}
    for arm in ARMS:
        result = load_json(directories[arm] / f"{arm}-result.json")
        summary = comparisons[arm]["arms"][arm]
        assert_equal(result["arm"], arm, f"{arm} 的 arm 字段")
        assert_equal(
            tuple(result["train_logs"]),
            YEARS,
            f"{arm} 的 train_logs 年度顺序",
        )
        assert_equal(result["mean_f1"], summary["mean_f1"], f"{arm} 的 12 年平均 F1")
        assert_equal(result["f1_2023"], summary["f1_2023"], f"{arm} 的 F1-2023")
        assert_equal(result["f1_2024"], summary["f1_2024"], f"{arm} 的 F1-2024")

        epoch_rates: dict[str, list[float]] = {}
        for year in YEARS:
            entries = result["train_logs"][year]["epoch_disagreement"]
            assert_equal(
                [entry["epoch"] for entry in entries],
                list(EPOCHS),
                f"{arm} {year} 的轮次序号",
            )
            assert all(int(entry["n"]) == 4096 for entry in entries)
            epoch_rates[year] = [
                float(entry["pairwise_disagreement_rate"]) for entry in entries
            ]

        check = summary["epoch_disagreement_2024"]
        assert_equal(check["rates"], epoch_rates["2024"], f"{arm} 的 2024 逐轮数组")
        assert_close(
            float(check["first"]),
            epoch_rates["2024"][0],
            what=f"{arm} 的 2024 首轮不一致率",
        )
        assert_close(
            float(check["last"]),
            epoch_rates["2024"][-1],
            what=f"{arm} 的 2024 末轮不一致率",
        )
        assert_close(
            float(check["delta_first_to_last"]),
            epoch_rates["2024"][-1] - epoch_rates["2024"][0],
            what=f"{arm} 的 2024 首末轮差",
        )

        arms[arm] = {
            "mean_f1": float(result["mean_f1"]),
            "f1_2023": float(result["f1_2023"]),
            "f1_2024": float(result["f1_2024"]),
            "epoch_rates": epoch_rates,
            "first_epoch_by_year": [epoch_rates[year][0] for year in YEARS],
        }

    # 4.5.4 节直接引用的两条轨迹读数：ncl05 的年内 first3/last3 比，
    # 以及单路损失臂同期不衰减/反向的读数。这里把正文数字变成脚本断言。
    def first3_last3(rates: list[float]) -> float:
        return (sum(rates[:3]) / 3.0) / (sum(rates[-3:]) / 3.0)

    ncl05_ratios = {
        year: first3_last3(arms["ncl05"]["epoch_rates"][year])
        for year in ("2021", "2022", "2023", "2024")
    }
    for year, expected in zip(("2021", "2022", "2023", "2024"), (3.2, 2.3, 2.6, 2.5)):
        assert_close(
            ncl05_ratios[year],
            expected,
            tol=0.05,
            what=f"ncl05 {year} 的 first3/last3 比",
        )
    train_single_ratios = {
        year: first3_last3(arms["train_single"]["epoch_rates"][year])
        for year in ("2021", "2022", "2023")
    }
    for year, expected in zip(("2021", "2022", "2023"), (0.8, 0.4, 1.1)):
        assert_close(
            train_single_ratios[year],
            expected,
            tol=0.05,
            what=f"train_single {year} 的 first3/last3 比",
        )

    arms["ncl05"]["first3_last3"] = ncl05_ratios
    arms["train_single"]["first3_last3"] = train_single_ratios
    return arms


def load_budget_points() -> tuple[list[dict[str, object]], dict[str, object]]:
    """读取图 4-3 与图 4-4 共用的配置读数，并核对三个汇总文件。"""

    tabm4 = load_json(TABM_DIR / "tabm4-result.json")
    tabm8 = load_json(TABM_DIR / "tabm8-result.json")
    halfwidth = load_json(GENERAL_DIR / "halfwidth-result.json")
    k2 = load_json(GENERAL_DIR / "k2-result.json")
    base = load_json(PAAT_DIR / "base-result.json")
    deep4 = load_json(BASELINE_DIR / "deep4-result.json")
    mcdrop = load_json(BASELINE_DIR / "mcdrop-result.json")
    swa = load_json(BASELINE_DIR / "swa-result.json")

    general = load_json(GENERAL_DIR / "general-comparison.json")
    baselines = load_json(BASELINE_DIR / "baselines-comparison.json")
    tabm_comparison = load_json(TABM_DIR / "tabm-comparison.json")

    # 图 4-1 的算量：共享主干与成员适配之和必须等于结果 JSON 的总参数量。
    assert_equal(int(tabm4["k"]), 4, "tabm4 的成员数")
    assert_equal(
        SHARED_TRUNK_PARAMS + MEMBER_ADAPTER_PARAMS,
        int(tabm4["n_params"]),
        "共享主干 + 成员适配",
    )

    # 成员数曲线三点与结果 JSON 逐位一致。
    result_by_arm = {"k2": k2, "tabm4": tabm4, "tabm8": tabm8}
    assert_equal(
        [entry["k"] for entry in general["k_curve"]],
        [2, 4, 8],
        "k 曲线的成员数顺序",
    )
    for entry in general["k_curve"]:
        arm = entry["arm"]
        result = result_by_arm[arm]
        assert_equal(entry["mean_f1"], result["mean_f1"], f"{arm} 的 12 年平均 F1")
        assert_equal(entry["f1_2023"], result["f1_2023"], f"{arm} 的 F1-2023")
        assert_equal(entry["f1_2024"], result["f1_2024"], f"{arm} 的 F1-2024")
        assert_equal(entry["n_params"], result["n_params"], f"{arm} 的参数量")
        assert_equal(entry["wall_seconds"], result["wall_seconds"], f"{arm} 的墙钟")

    width = general["width_variant"]
    assert_equal(width["arm"], "halfwidth", "宽度变体的 arm")
    assert_equal(width["n_params"], halfwidth["n_params"], "半宽骨干的参数量")
    assert_close(
        float(width["delta_mean12_pp"]),
        (halfwidth["mean_f1"] - tabm4["mean_f1"]) * 100.0,
        tol=1e-9,
        what="半宽骨干的 12 年平均差",
    )
    assert_close(
        float(width["delta_2024_pp"]),
        (halfwidth["f1_2024"] - tabm4["f1_2024"]) * 100.0,
        tol=1e-9,
        what="半宽骨干的 2024 年度差",
    )
    assert_close(
        float(width["param_ratio"]),
        halfwidth["n_params"] / tabm4["n_params"],
        tol=1e-12,
        what="半宽骨干的参数比例",
    )

    # 外部基线汇总与各自的结果 JSON 一致；base 的参数量取同架构的
    # mcdrop / swa 运行登记值（base-result.json 本身未写 n_params）。
    table = baselines["table"]
    assert_equal(table["base"]["mean_f1"], base["mean_f1"], "底座 12 年平均 F1")
    assert_equal(table["base"]["f1_2023"], base["f1_2023"], "底座 F1-2023")
    assert_equal(table["base"]["f1_2024"], base["f1_2024"], "底座 F1-2024")
    assert_equal(table["uniform_tabm4"]["mean_f1"], tabm4["mean_f1"], "均匀成员化 F1")
    assert_equal(table["uniform_tabm4"]["n_params"], tabm4["n_params"], "均匀成员化参数量")
    assert_equal(table["deep4"]["mean_f1"], deep4["mean_f1"], "深度集成 F1")
    assert_equal(table["deep4"]["n_params"], deep4["n_params"], "深度集成参数量")
    base_n_params = int(mcdrop["n_params"])
    assert_equal(base_n_params, int(swa["n_params"]), "底座同架构参数量")
    assert_equal(base_n_params, int(deep4["n_params_per_member"]), "深度集成单成员参数量")
    assert_equal(
        baselines["reference_constants"]["base_mean_f1"],
        base["mean_f1"],
        "baselines-comparison 的底座参考值",
    )
    assert_equal(
        baselines["reference_constants"]["uniform_tabm4_mean_f1"],
        tabm4["mean_f1"],
        "baselines-comparison 的均匀成员化参考值",
    )
    assert_close(
        float(baselines["budget_claim"]["abs_diff"]),
        abs(tabm4["mean_f1"] - deep4["mean_f1"]),
        tol=1e-12,
        what="预算主张的绝对差",
    )
    if not baselines["budget_claim"]["supported"]:
        raise ValueError("baselines-comparison 的预算主张未通过")

    assert_equal(
        tabm_comparison["reference_base_mean"],
        base["mean_f1"],
        "tabm-comparison 的底座参考值",
    )
    assert_equal(
        tabm_comparison["base_f1"]["2023"],
        base["f1_2023"],
        "tabm-comparison 的底座 F1-2023",
    )
    assert_equal(
        tabm_comparison["base_f1"]["2024"],
        base["f1_2024"],
        "tabm-comparison 的底座 F1-2024",
    )
    for arm in ("tabm4", "tabm8"):
        result = result_by_arm[arm]
        assert_equal(
            tabm_comparison["arms"][arm]["mean_f1"],
            result["mean_f1"],
            f"tabm-comparison 的 {arm} 12 年平均",
        )
        assert_equal(
            tabm_comparison["arms"][arm]["f1_2023"],
            result["f1_2023"],
            f"tabm-comparison 的 {arm} F1-2023",
        )
        assert_equal(
            tabm_comparison["arms"][arm]["f1_2024"],
            result["f1_2024"],
            f"tabm-comparison 的 {arm} F1-2024",
        )

    points: list[dict[str, object]] = [
        {
            "key": "base",
            "label": "第三章底座",
            "n_params": base_n_params,
            "mean_f1": float(base["mean_f1"]),
            "f1_2024": float(base["f1_2024"]),
            "role": "base",
        },
        {
            "key": "uniform",
            "label": "均匀成员化（k=4）",
            "n_params": int(tabm4["n_params"]),
            "mean_f1": float(tabm4["mean_f1"]),
            "f1_2024": float(tabm4["f1_2024"]),
            "role": "uniform",
        },
        {
            "key": "tabm8",
            "label": "成员数 8",
            "n_params": int(tabm8["n_params"]),
            "mean_f1": float(tabm8["mean_f1"]),
            "f1_2024": float(tabm8["f1_2024"]),
            "role": "k8",
        },
        {
            "key": "k2",
            "label": "成员数 2",
            "n_params": int(k2["n_params"]),
            "mean_f1": float(k2["mean_f1"]),
            "f1_2024": float(k2["f1_2024"]),
            "role": "k2",
        },
        {
            "key": "halfwidth",
            "label": "半宽骨干",
            "n_params": int(halfwidth["n_params"]),
            "mean_f1": float(halfwidth["mean_f1"]),
            "f1_2024": float(halfwidth["f1_2024"]),
            "role": "halfwidth",
        },
        {
            "key": "deep4",
            "label": "深度集成（4 成员）",
            "n_params": int(deep4["n_params"]),
            "mean_f1": float(deep4["mean_f1"]),
            "f1_2024": float(deep4["f1_2024"]),
            "role": "deep4",
        },
    ]
    return points, {
        "general": general,
        "baselines": baselines,
        "tabm_comparison": tabm_comparison,
        "tabm4": tabm4,
        "tabm8": tabm8,
        "halfwidth": halfwidth,
        "k2": k2,
        "base": base,
        "deep4": deep4,
        "mcdrop": mcdrop,
        "swa": swa,
    }


def load_dual_channel() -> tuple[list[dict[str, object]], dict[str, float], dict]:
    """读取图 4-5 的逐年双通道分解，并逐项断言分解恒等式。"""

    base = load_json(PAAT_DIR / "base-result.json")
    tabm4 = load_json(TABM_DIR / "tabm4-result.json")
    diag = load_json(TABM_DIR / "member-disagreement-diag.json")

    if not diag["identity_gate"]["passed"]:
        raise ValueError("member-disagreement-diag.json 的恒等门未通过")
    assert_equal(diag["arm"], "tabm4", "分歧诊断的 arm")
    assert_equal(diag["k"], 4, "分歧诊断的成员数")
    assert_equal(
        tuple(diag["years"]),
        YEARS,
        "分歧诊断的年度顺序",
    )
    assert_equal(
        tuple(base["backward_f1"]),
        YEARS,
        "base-result 的年度顺序",
    )
    assert_equal(
        tuple(tabm4["backward_f1"]),
        YEARS,
        "tabm4-result 的年度顺序",
    )

    rows: list[dict[str, object]] = []
    for year in YEARS:
        members = [float(value) for value in diag["years"][year]["f1_per_member"]]
        assert_equal(len(members), 4, f"{year} 的成员 F1 个数")
        ensemble = float(tabm4["backward_f1"][year])
        base_f1 = float(base["backward_f1"][year])
        member_mean = sum(members) / len(members)
        train_channel = member_mean - base_f1
        eval_channel = ensemble - member_mean
        total = ensemble - base_f1
        assert_close(
            train_channel + eval_channel,
            total,
            tol=1e-12,
            what=f"{year} 的双通道分解恒等式",
        )
        assert_close(
            float(diag["identity_gate"]["per_year"][year]["diag_f1"]),
            ensemble,
            tol=1e-12,
            what=f"{year} 的恒等门 diag_f1",
        )
        assert_close(
            float(diag["years"][year]["f1_ensemble"]),
            ensemble,
            tol=1e-12,
            what=f"{year} 的分歧诊断集成 F1",
        )
        rows.append(
            {
                "year": year,
                "base_f1": base_f1,
                "member_mean": member_mean,
                "ensemble_f1": ensemble,
                "train_channel": train_channel,
                "eval_channel": eval_channel,
                "total": total,
                "member_std_pos": float(diag["years"][year]["member_std_pos"]),
                "member_std_neg": float(diag["years"][year]["member_std_neg"]),
                "pairwise_disagreement": float(
                    diag["years"][year]["pairwise_disagreement_rate"]
                ),
            }
        )

    means = {
        "train_channel": sum(row["train_channel"] for row in rows) / len(rows),
        "eval_channel": sum(row["eval_channel"] for row in rows) / len(rows),
        "total": sum(row["total"] for row in rows) / len(rows),
    }
    # 4.5.2 与表 4-5 的 12 年口径（含 2025 年的零值）。
    assert_close(means["train_channel"] * 100.0, 0.47, tol=0.005, what="训练通道 12 年均值")
    assert_close(means["eval_channel"] * 100.0, 1.07, tol=0.005, what="评测通道 12 年均值")
    assert_close(means["total"] * 100.0, 1.54, tol=0.005, what="总增益 12 年均值")
    assert_close(
        means["total"] * 100.0,
        (tabm4["mean_f1"] - base["mean_f1"]) * 100.0,
        tol=1e-9,
        what="双通道总均值与 tabm4-base 差",
    )

    # 正文 4.6.5 的两个比值读数。
    ratio_2023 = rows[9]["member_std_pos"] / rows[9]["member_std_neg"]
    ratio_2024 = rows[10]["member_std_pos"] / rows[10]["member_std_neg"]
    assert 16.0 < ratio_2023 < 17.0
    assert 42.0 < ratio_2024 < 44.0
    assert_close(ratio_2023, 16.6, tol=0.1, what="2023 正/负成员标准差比")
    assert_close(ratio_2024, 42.9, tol=0.2, what="2024 正/负成员标准差比")

    return rows, means, diag


# ---------------------------------------------------------------- 图 4-1


def draw_architecture(total_params: int) -> fs.Canvas:
    """预算约束成员化训练的总体结构。"""

    cv = fs.canvas(165.0, 125.0)

    input_face = "#F7F7F7"
    struct_face = "#ECECEC"
    loss_face = "#E2E2E2"
    eval_face = "#F0F0F0"
    out_face = "#FCFCFC"
    loop_face = "#F7F7F7"

    # 左列：年度训练构成
    fs.box(
        cv,
        0.025,
        0.620,
        0.205,
        0.280,
        (
            fs.Line("年度 t 训练批", 9.0),
            fs.Line("第三章回放构成", 8.0),
            fs.Line("当年分片 + 历史回放", 8.0),
            fs.Line("存储 200/配额/复用冻结", 8.0),
        ),
        face=input_face,
        edge="#555555",
        linewidth=0.9,
        radius=0.010,
        zorder=3,
    )

    # 中列：成员化结构
    fs.box(
        cv,
        0.280,
        0.600,
        0.305,
        0.320,
        (),
        face=struct_face,
        edge="#333333",
        linewidth=0.9,
        radius=0.010,
        zorder=2,
    )
    fs.text(
        cv,
        0.292,
        0.897,
        "成员化结构（k = 4）",
        size=9.0,
        ha="left",
        color=fs.INK,
    )
    fs.box(
        cv,
        0.296,
        0.770,
        0.273,
        0.100,
        (
            fs.Line("共享主干 2,686,014 参数", 8.0),
            fs.Line("编码器 512/384/256/128", 8.0),
            fs.Line("分类头 100/100/1", 8.0),
        ),
        face=fs.WHITE,
        edge="#666666",
        linewidth=0.8,
        radius=0.008,
        zorder=4,
    )

    member_xs = [0.296 + index * 0.0717 for index in range(4)]
    for index, x in enumerate(member_xs, start=1):
        fs.box(
            cv,
            x,
            0.665,
            0.058,
            0.075,
            (fs.Line(f"M{index}", 8.0),),
            face=fs.WHITE,
            edge="#666666",
            linewidth=0.8,
            radius=0.006,
            zorder=4,
        )
        fs.arrow(
            cv,
            (x + 0.029, 0.770),
            (x + 0.029, 0.740),
            color=fs.INK,
            linewidth=0.6,
            head=4.5,
            zorder=5,
        )

    fs.text(
        cv,
        0.4325,
        0.640,
        "成员适配参数（37,291）",
        size=8.0,
        color=fs.MUTED,
    )
    fs.text(
        cv,
        0.4325,
        0.613,
        r"$W_i = W \circ (r_i s_i^{T})$",
        size=8.0,
        color=fs.INK,
    )

    # 右上：成员均值损失
    fs.box(
        cv,
        0.630,
        0.680,
        0.345,
        0.240,
        (
            fs.Line("成员均值损失", 9.0),
            fs.Line(
                r"$L = \frac{1}{k}\sum_i \mathrm{BCE}(s_i(x), y)$",
                8.0,
                kind="math",
            ),
            fs.Line("全体成员共享同一训练批次", 8.0),
            fs.Line("SGD 0.01/动量 0.9/10 轮", 8.0),
        ),
        face=loss_face,
        edge="#333333",
        linewidth=0.9,
        radius=0.010,
        zorder=3,
    )

    # 右下：概率均值评测
    fs.box(
        cv,
        0.630,
        0.380,
        0.345,
        0.220,
        (
            fs.Line("概率均值评测", 9.0),
            fs.Line(
                r"$\hat{s}(x) = \frac{1}{k}\sum_i s_i(x)$",
                8.0,
                kind="math",
            ),
            fs.Line("阈值 0.5；12 年回看 F1", 8.0),
            fs.Line("成员维度与训练目标一致", 8.0),
        ),
        face=eval_face,
        edge="#333333",
        linewidth=0.9,
        radius=0.010,
        zorder=3,
    )

    # 中下：逐年回看读数
    fs.box(
        cv,
        0.280,
        0.340,
        0.305,
        0.180,
        (
            fs.Line("逐年回看读数", 9.0),
            fs.Line("当年 + 已到达年度", 8.0),
            fs.Line("12 年平均 F1", 8.0),
        ),
        face=out_face,
        edge="#555555",
        linewidth=0.9,
        radius=0.010,
        zorder=3,
    )

    # 左下：年度序列
    fs.box(
        cv,
        0.025,
        0.340,
        0.205,
        0.180,
        (
            fs.Line("年度序列", 9.0),
            fs.Line("t = 2013 ... 2025", 8.0),
            fs.Line("每年更新 10 轮", 8.0),
        ),
        face=loop_face,
        edge="#555555",
        linewidth=0.9,
        linestyle=(0, (5, 3)),
        radius=0.010,
        zorder=3,
    )

    # 数据流
    fs.arrow(cv, (0.230, 0.760), (0.280, 0.760), color=fs.INK, head=6.0)
    fs.text(cv, 0.255, 0.778, r"$P_t$", size=8.0, color=fs.MUTED)

    fs.arrow(cv, (0.585, 0.820), (0.630, 0.820), color=fs.INK, head=6.0)
    fs.text(cv, 0.6075, 0.838, "训练", size=8.0, color=fs.MUTED)

    fs.arrow(
        cv,
        (0.630, 0.720),
        (0.585, 0.720),
        color=fs.INK,
        linewidth=0.9,
        linestyle=(0, (4, 2)),
        head=6.0,
    )
    fs.text(cv, 0.6075, 0.702, "梯度", size=8.0, color=fs.MUTED)

    fs.arrow(cv, (0.560, 0.600), (0.630, 0.560), color=fs.INK, head=6.0)
    fs.text(cv, 0.6075, 0.578, "评测", size=8.0, color=fs.MUTED)

    fs.arrow(cv, (0.630, 0.450), (0.585, 0.450), color=fs.INK, head=6.0)
    fs.text(cv, 0.6075, 0.468, "F1", size=8.0, color=fs.MUTED)

    fs.arrow(cv, (0.280, 0.430), (0.230, 0.430), color=fs.INK, head=6.0)
    fs.text(cv, 0.255, 0.448, r"$t+1$", size=8.0, color=fs.MUTED)

    fs.arrow(
        cv,
        (0.1275, 0.520),
        (0.1275, 0.620),
        color=fs.INK,
        linewidth=0.9,
        linestyle=(0, (4, 2)),
        head=6.0,
    )
    fs.text(cv, 0.145, 0.570, "年度推进", size=8.0, color=fs.MUTED, ha="left")

    # 说明
    fs.text(
        cv,
        0.500,
        0.250,
        "单次逐年前推：k 个成员沿批量轴并行；参数总量 2,723,305"
        "（共享主干 2,686,014 + 成员适配 37,291，1.4%）。",
        size=8.0,
        color=fs.MUTED,
    )
    fs.text(
        cv,
        0.500,
        0.195,
        "成员均值损失与概率均值评测在成员维度一致；"
        "显式分工约束不进入最终配置（见 4.3.4）。",
        size=8.0,
        color=fs.MUTED,
    )
    fs.text(
        cv,
        0.500,
        0.140,
        "评测合同：成员概率均值，阈值 0.5；回看 12 个测试年度。",
        size=8.0,
        color=fs.MUTED,
    )
    return cv


# ---------------------------------------------------------------- 图 4-2


def _arm_style(arm: str) -> dict[str, object]:
    return {
        "train_single": {
            "label": "单路损失（D0）",
            "color": "#7F7F7F",
            "linestyle": (0, (5, 2)),
            "marker": "o",
            "markersize": 4.0,
            "filled": False,
        },
        "ncl05": {
            "label": "NCL λ=0.5",
            "color": fs.INK,
            "linestyle": "-",
            "marker": "o",
            "markersize": 4.2,
            "filled": True,
        },
        "ncl2": {
            "label": "NCL λ=2.0",
            "color": "#555555",
            "linestyle": (0, (4, 1.2, 1, 1.2)),
            "marker": "s",
            "markersize": 3.8,
            "filled": False,
        },
        "corr05": {
            "label": "相关惩罚 λ=0.5",
            "color": fs.INK,
            "linestyle": "-",
            "marker": "^",
            "markersize": 4.4,
            "filled": True,
        },
        "corr10": {
            "label": "相关惩罚 λ=1.0",
            "color": "#7F7F7F",
            "linestyle": (0, (5, 2)),
            "marker": "D",
            "markersize": 3.6,
            "filled": False,
        },
    }[arm]


def _plot_arm(ax, x_values, y_values, arm: str) -> None:
    style = _arm_style(arm)
    ax.plot(
        x_values,
        y_values,
        label=str(style["label"]),
        color=str(style["color"]),
        linestyle=style["linestyle"],
        linewidth=1.0 if arm in ("ncl05", "corr05") else 0.9,
        marker=str(style["marker"]),
        markersize=float(style["markersize"]),
        markerfacecolor=str(style["color"]) if style["filled"] else fs.WHITE,
        markeredgecolor=str(style["color"]),
        markeredgewidth=0.8,
        zorder=4 if arm in ("ncl05", "corr05") else 3,
    )


def _style_trajectory_axis(ax, title: str, ylabel: str, ylim: tuple[float, float]) -> None:
    ax.set_title(fs.checked(title, 9.0), loc="left", size=9.0, pad=4.0)
    ax.set_ylabel(fs.checked(ylabel, 9.0), size=9.0, labelpad=5.0)
    ax.set_ylim(*ylim)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(fs.INK)
    ax.tick_params(axis="both", labelsize=8.0, length=2.5, width=0.6, pad=2.5)


def draw_constraint_trajectories(arms: dict[str, dict[str, object]]) -> Figure:
    """三类显式分工约束的跨年起点与 2024 年内逐轮轨迹。"""

    width_mm, height_mm = 165.0, 125.0
    fig = Figure(
        figsize=(fs.mm_to_inch(width_mm), fs.mm_to_inch(height_mm)),
        dpi=200,
        facecolor=fs.WHITE,
    )
    axes = {
        "a": fig.add_axes((0.075, 0.660, 0.405, 0.260)),
        "b": fig.add_axes((0.575, 0.660, 0.405, 0.260)),
        "c": fig.add_axes((0.075, 0.245, 0.405, 0.260)),
        "d": fig.add_axes((0.575, 0.245, 0.405, 0.260)),
    }

    year_x = list(range(len(YEARS)))
    epoch_x = list(EPOCHS)

    # (a) NCL 系的跨年起点
    for arm in NCL_ARMS:
        _plot_arm(
            axes["a"],
            year_x,
            [rate * 100.0 for rate in arms[arm]["first_epoch_by_year"]],
            arm,
        )
    _style_trajectory_axis(
        axes["a"],
        "(a) 跨年起点：NCL 系\nncl05：2.25%（2016）至 0.24%（2024）",
        "首轮不一致率（%）",
        (0.0, 4.0),
    )
    axes["a"].set_xticks(year_x)
    axes["a"].set_xticklabels(YEARS, rotation=45, ha="right", size=8.0)
    axes["a"].set_yticks([0.0, 1.0, 2.0, 3.0, 4.0])
    axes["a"].legend(
        loc="upper right",
        frameon=False,
        fontsize=8.0,
        handlelength=2.8,
        labelspacing=0.5,
    )

    # (b) 相关系数的跨年起点
    for arm in CORR_ARMS:
        _plot_arm(
            axes["b"],
            year_x,
            [rate * 100.0 for rate in arms[arm]["first_epoch_by_year"]],
            arm,
        )
    _style_trajectory_axis(
        axes["b"],
        "(b) 跨年起点：相关系",
        "首轮不一致率（%）",
        (0.0, 35.0),
    )
    axes["b"].set_xticks(year_x)
    axes["b"].set_xticklabels(YEARS, rotation=45, ha="right", size=8.0)
    axes["b"].set_yticks([0.0, 10.0, 20.0, 30.0])
    axes["b"].legend(
        loc="upper left",
        frameon=False,
        fontsize=8.0,
        handlelength=2.8,
        labelspacing=0.5,
    )
    axes["b"].text(
        0.03,
        0.38,
        "2021 至 2022 年度\n起点约 30%；\n12 年平均 F1 为 0",
        transform=axes["b"].transAxes,
        size=8.0,
        color=fs.MUTED,
        ha="left",
        va="center",
        zorder=6,
    )

    # (c) NCL 系的 2024 年内逐轮
    for arm in NCL_ARMS:
        _plot_arm(
            axes["c"],
            epoch_x,
            [rate * 100.0 for rate in arms[arm]["epoch_rates"]["2024"]],
            arm,
        )
    _style_trajectory_axis(
        axes["c"],
        "(c) 2024 年内逐轮：NCL 系\nncl05：首轮 0.24% 至末轮 0.06%",
        "不一致率（%）",
        (0.0, 0.30),
    )
    axes["c"].set_xticks(epoch_x)
    axes["c"].set_xticklabels([str(epoch) for epoch in EPOCHS], size=8.0)
    axes["c"].set_xlabel(fs.checked("训练轮次", 9.0), size=9.0, labelpad=4.0)
    axes["c"].set_yticks([0.0, 0.1, 0.2, 0.3])
    axes["c"].legend(
        loc="upper right",
        frameon=False,
        fontsize=8.0,
        handlelength=2.8,
        labelspacing=0.5,
    )

    # (d) 相关系数的 2024 年内逐轮
    for arm in CORR_ARMS:
        _plot_arm(
            axes["d"],
            epoch_x,
            [rate * 100.0 for rate in arms[arm]["epoch_rates"]["2024"]],
            arm,
        )
    _style_trajectory_axis(
        axes["d"],
        "(d) 2024 年内逐轮：相关系",
        "不一致率（%）",
        (0.0, 1.1),
    )
    axes["d"].set_xticks(epoch_x)
    axes["d"].set_xticklabels([str(epoch) for epoch in EPOCHS], size=8.0)
    axes["d"].set_xlabel(fs.checked("训练轮次", 9.0), size=9.0, labelpad=4.0)
    axes["d"].set_yticks([0.0, 0.5, 1.0])
    axes["d"].legend(
        loc="lower left",
        frameon=False,
        fontsize=8.0,
        handlelength=2.8,
        labelspacing=0.5,
    )
    axes["d"].text(
        0.03,
        0.46,
        "两臂逐轮约 0.9% 至 1.0%，\n分歧未随训练收缩",
        transform=axes["d"].transAxes,
        size=8.0,
        color=fs.MUTED,
        ha="left",
        va="center",
        zorder=6,
    )

    fig.text(
        0.5,
        0.145,
        fs.checked(
            "12 年平均 F1：单路损失 82.03%；NCL λ=0.5 83.01%；"
            "NCL λ=2.0 83.15%；相关惩罚 λ=0.5 与 λ=1.0 均为 0.00%。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    fig.text(
        0.5,
        0.085,
        fs.checked(
            "ncl05 年内 first3 至 last3 比：2021 3.2；2022 2.3；"
            "2023 2.6；2024 2.5。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    fig.text(
        0.5,
        0.030,
        fs.checked(
            "单路损失同期为 0.8、0.4、1.1，部分年度不衰减或反向；"
            "0 值表示该年度首轮成员判定完全一致。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    return fig


# ---------------------------------------------------------------- 图 4-3


def draw_budget_map(points: list[dict[str, object]]) -> Figure:
    """参数总量与 12 年平均 F1 的预算位置图。"""

    width_mm, height_mm = 150.0, 100.0
    fig = Figure(
        figsize=(fs.mm_to_inch(width_mm), fs.mm_to_inch(height_mm)),
        dpi=200,
        facecolor=fs.WHITE,
    )
    ax = fig.add_axes((0.110, 0.205, 0.865, 0.700))

    by_key = {point["key"]: point for point in points}
    x = {key: float(point["n_params"]) / 1e6 for key, point in by_key.items()}
    y = {key: float(point["mean_f1"]) * 100.0 for key, point in by_key.items()}

    ax.set_xscale("log")
    ax.set_xlim(1.15, 13.0)
    ax.set_ylim(81.35, 83.55)
    ax.set_xticks([1.2, 1.5, 2.0, 3.0, 5.0, 10.0])
    ax.set_xticklabels(["1.2", "1.5", "2.0", "3.0", "5.0", "10.0"], size=8.0)
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9), numticks=100))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(axis="x", which="minor", length=0)
    ax.set_yticks([81.5, 82.0, 82.5, 83.0, 83.5])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.1f}"))
    ax.set_xlabel(fs.checked("参数总量（百万）", 9.0), size=9.0, labelpad=5.0)
    ax.set_ylabel(fs.checked("12 年平均 F1（%）", 9.0), size=9.0, labelpad=5.0)
    ax.grid(axis="both", color="#D9D9D9", linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(fs.INK)
    ax.tick_params(axis="both", labelsize=8.0, length=2.5, width=0.6, pad=2.5)

    # 标记：灰度可读依靠形状与填充，不依赖颜色。
    ax.scatter(
        x["base"],
        y["base"],
        s=62.0,
        marker="o",
        facecolors=fs.WHITE,
        edgecolors=fs.INK,
        linewidths=1.0,
        zorder=5,
    )
    ax.scatter(
        x["uniform"],
        y["uniform"],
        s=120.0,
        marker="o",
        facecolors=fs.INK,
        edgecolors=fs.INK,
        linewidths=1.4,
        zorder=6,
    )
    ax.scatter(
        x["tabm8"],
        y["tabm8"],
        s=72.0,
        marker="^",
        facecolors=fs.WHITE,
        edgecolors="#333333",
        linewidths=1.0,
        zorder=5,
    )
    ax.scatter(
        x["halfwidth"],
        y["halfwidth"],
        s=68.0,
        marker="D",
        facecolors=fs.WHITE,
        edgecolors="#555555",
        linewidths=1.0,
        zorder=5,
    )
    ax.scatter(
        x["deep4"],
        y["deep4"],
        s=76.0,
        marker="s",
        facecolors="#BFBFBF",
        edgecolors="#333333",
        linewidths=1.0,
        zorder=5,
    )

    def annotate(key: str, text_xy: tuple[float, float], text: str, ha: str = "left") -> None:
        ax.annotate(
            fs.checked(text, 8.0),
            xy=(x[key], y[key]),
            xytext=text_xy,
            textcoords="data",
            ha=ha,
            va="center",
            size=8.0,
            color=fs.INK,
            arrowprops={
                "arrowstyle": "-",
                "linewidth": 0.5,
                "color": "#777777",
                "shrinkA": 1.0,
                "shrinkB": 3.0,
            },
            zorder=7,
        )

    annotate(
        "halfwidth",
        (1.32, 83.10),
        "半宽骨干\n1.29M / 82.62%",
    )
    annotate(
        "base",
        (1.58, 81.52),
        "第三章底座\n2.69M / 81.70%",
    )
    annotate(
        "uniform",
        (3.05, 83.32),
        "均匀成员化（k=4）\n2.72M / 83.23%\n单次预算",
    )
    annotate(
        "tabm8",
        (3.12, 82.83),
        "成员数 8\n2.76M / 82.92%",
    )
    annotate(
        "deep4",
        (6.6, 81.72),
        "深度集成（4 成员）\n10.75M / 82.33%\n4× 预算",
    )

    fig.text(
        0.5,
        0.055,
        fs.checked(
            "横轴为对数刻度；单次预算指一次逐年前推与 2.72M 参数；"
            "全部读数来自同一协议下的冻结配置。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    return fig


# ---------------------------------------------------------------- 图 4-4


def draw_sensitivity(points: list[dict[str, object]]) -> Figure:
    """成员数与骨干宽度的敏感性曲线。"""

    width_mm, height_mm = 150.0, 95.0
    fig = Figure(
        figsize=(fs.mm_to_inch(width_mm), fs.mm_to_inch(height_mm)),
        dpi=200,
        facecolor=fs.WHITE,
    )
    ax = fig.add_axes((0.105, 0.205, 0.790, 0.700))
    twin = ax.twinx()

    by_key = {point["key"]: point for point in points}
    k_values = [2.0, 4.0, 8.0]
    mean_values = [
        float(by_key["k2"]["mean_f1"]) * 100.0,
        float(by_key["uniform"]["mean_f1"]) * 100.0,
        float(by_key["tabm8"]["mean_f1"]) * 100.0,
    ]
    f1_2024_values = [
        float(by_key["k2"]["f1_2024"]) * 100.0,
        float(by_key["uniform"]["f1_2024"]) * 100.0,
        float(by_key["tabm8"]["f1_2024"]) * 100.0,
    ]
    halfwidth_x = 4.28
    halfwidth_mean = float(by_key["halfwidth"]["mean_f1"]) * 100.0
    halfwidth_2024 = float(by_key["halfwidth"]["f1_2024"]) * 100.0

    ax.plot(
        k_values,
        mean_values,
        color=fs.INK,
        linestyle="-",
        linewidth=1.4,
        marker="o",
        markersize=5.0,
        markerfacecolor=fs.INK,
        markeredgecolor=fs.INK,
        label="12 年平均 F1",
        zorder=5,
    )
    twin.plot(
        k_values,
        f1_2024_values,
        color="#666666",
        linestyle=(0, (5, 2)),
        linewidth=1.1,
        marker="s",
        markersize=4.4,
        markerfacecolor=fs.WHITE,
        markeredgecolor="#666666",
        label="2024 年度 F1",
        zorder=4,
    )
    ax.plot(
        [halfwidth_x],
        [halfwidth_mean],
        linestyle="none",
        marker="D",
        markersize=5.0,
        markerfacecolor=fs.WHITE,
        markeredgecolor=fs.INK,
        markeredgewidth=1.0,
        zorder=6,
    )
    twin.plot(
        [halfwidth_x],
        [halfwidth_2024],
        linestyle="none",
        marker="D",
        markersize=5.0,
        markerfacecolor=fs.WHITE,
        markeredgecolor="#666666",
        markeredgewidth=1.0,
        zorder=6,
    )

    ax.set_xlim(1.35, 9.0)
    ax.set_xticks([2.0, 4.0, 8.0])
    ax.set_xticklabels(["2", "4", "8"], size=8.0)
    ax.set_xlabel(fs.checked("成员数 k", 9.0), size=9.0, labelpad=5.0)
    ax.set_ylim(80.8, 83.6)
    ax.set_yticks([81.0, 82.0, 83.0])
    ax.set_ylabel(fs.checked("12 年平均 F1（%）", 9.0), size=9.0, labelpad=5.0)
    twin.set_ylim(69.5, 78.0)
    twin.set_yticks([70.0, 72.0, 74.0, 76.0, 78.0])
    twin.set_ylabel(
        fs.checked("2024 年度 F1（%）", 9.0),
        size=9.0,
        labelpad=6.0,
        color="#555555",
    )
    twin.tick_params(axis="y", labelsize=8.0, colors="#555555", length=2.5, width=0.6, pad=2.5)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top",):
        ax.spines[side].set_visible(False)
        twin.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(fs.INK)
    twin.spines["right"].set_linewidth(0.7)
    twin.spines["right"].set_color("#666666")
    ax.tick_params(axis="both", labelsize=8.0, length=2.5, width=0.6, pad=2.5)

    ax.annotate(
        fs.checked("本章配置", 8.0),
        xy=(4.0, mean_values[1]),
        xytext=(4.0, 83.42),
        textcoords="data",
        ha="center",
        va="center",
        size=8.0,
        color=fs.INK,
        arrowprops={"arrowstyle": "-", "linewidth": 0.5, "color": "#777777"},
        zorder=7,
    )
    handles = [
        Line2D([0], [0], color=fs.INK, linestyle="-", linewidth=1.4, marker="o", markersize=5.0, label="12 年平均 F1"),
        Line2D([0], [0], color="#666666", linestyle=(0, (5, 2)), linewidth=1.1, marker="s", markersize=4.4, markerfacecolor=fs.WHITE, label="2024 年度 F1"),
        Line2D([0], [0], color=fs.INK, linestyle="none", marker="D", markersize=5.0, markerfacecolor=fs.WHITE, label="半宽骨干"),
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.03),
        ncol=3,
        frameon=False,
        fontsize=8.0,
        handlelength=2.8,
        columnspacing=1.8,
        borderaxespad=0.0,
    )

    fig.text(
        0.5,
        0.075,
        fs.checked(
            "半宽骨干为 k=4 的宽度变体（空心菱形，横向略移）；参数为全宽的 47.2%。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    fig.text(
        0.5,
        0.025,
        fs.checked(
            "其 12 年平均 F1 为 82.62%、低 0.61 pp；2024 年度为 74.33%、低 2.71 pp。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    return fig


# ---------------------------------------------------------------- 图 4-5


def draw_dual_channel(
    rows: list[dict[str, object]],
    means: dict[str, float],
) -> Figure:
    """增益的双通道逐年分解与成员分歧的逐年形态。"""

    width_mm, height_mm = 165.0, 112.0
    fig = Figure(
        figsize=(fs.mm_to_inch(width_mm), fs.mm_to_inch(height_mm)),
        dpi=200,
        facecolor=fs.WHITE,
    )
    ax = fig.add_axes((0.075, 0.235, 0.505, 0.640))
    ax2 = fig.add_axes((0.665, 0.235, 0.325, 0.640))

    positions = list(range(len(YEARS)))
    average_position = 12.5
    train = [row["train_channel"] * 100.0 for row in rows]
    eval_channel = [row["eval_channel"] * 100.0 for row in rows]
    total = [row["total"] * 100.0 for row in rows]

    bar_width = 0.62
    ax.bar(
        positions,
        eval_channel,
        width=bar_width,
        color="#D9D9D9",
        edgecolor=fs.INK,
        linewidth=0.6,
        label="评测平均通道",
        zorder=3,
    )
    ax.bar(
        positions,
        train,
        bottom=eval_channel,
        width=bar_width,
        color=fs.WHITE,
        edgecolor=fs.INK,
        linewidth=0.6,
        hatch="///",
        label="训练通道",
        zorder=4,
    )
    ax.plot(
        positions,
        total,
        linestyle="none",
        marker="D",
        markersize=3.8,
        markerfacecolor=fs.INK,
        markeredgecolor=fs.INK,
        label="合计",
        zorder=6,
    )

    mean_train = means["train_channel"] * 100.0
    mean_eval = means["eval_channel"] * 100.0
    mean_total = means["total"] * 100.0
    ax.bar(
        [average_position],
        [mean_eval],
        width=bar_width,
        color="#D9D9D9",
        edgecolor=fs.INK,
        linewidth=0.6,
        zorder=3,
    )
    ax.bar(
        [average_position],
        [mean_train],
        bottom=[mean_eval],
        width=bar_width,
        color=fs.WHITE,
        edgecolor=fs.INK,
        linewidth=0.6,
        hatch="///",
        zorder=4,
    )
    ax.plot(
        [average_position],
        [mean_total],
        linestyle="none",
        marker="D",
        markersize=3.8,
        markerfacecolor=fs.INK,
        markeredgecolor=fs.INK,
        zorder=6,
    )
    ax.axvline(11.75, color="#BDBDBD", linewidth=0.5, linestyle=(0, (3, 2)), zorder=1)
    ax.axhline(0.0, color=fs.INK, linewidth=0.6, zorder=2)

    ax.set_xlim(-0.7, 13.1)
    ax.set_ylim(-2.3, 5.3)
    ax.set_xticks(positions + [average_position])
    ax.set_xticklabels(list(YEARS) + [""], rotation=45, ha="right", size=8.0)
    ax.annotate(
        fs.checked("12 年均值", 8.0),
        xy=(average_position, mean_total + 0.05),
        xytext=(10.55, 2.35),
        textcoords="data",
        ha="left",
        va="center",
        size=8.0,
        color=fs.INK,
        arrowprops={"arrowstyle": "-", "linewidth": 0.5, "color": "#777777"},
        zorder=6,
    )
    ax.set_yticks([-2.0, 0.0, 2.0, 4.0])
    ax.set_ylabel(fs.checked("相对底座 F1 变化（百分点）", 9.0), size=9.0, labelpad=5.0)
    ax.set_title(fs.checked("(a) 双通道逐年分解", 9.0), loc="left", size=9.0, pad=4.0)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.5, zorder=1)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(fs.INK)
    ax.tick_params(axis="both", labelsize=8.0, length=2.5, width=0.6, pad=2.5)
    ax.legend(
        loc="upper left",
        frameon=False,
        fontsize=8.0,
        ncol=3,
        handlelength=1.8,
        columnspacing=1.4,
        labelspacing=0.5,
    )

    # (b) 成员分歧的逐年形态：正例侧与负例侧成员标准差。
    pos = [row["member_std_pos"] for row in rows]
    neg = [row["member_std_neg"] for row in rows]
    ax2.plot(
        positions,
        pos,
        color=fs.INK,
        linestyle="-",
        linewidth=1.1,
        marker="o",
        markersize=4.0,
        markerfacecolor=fs.INK,
        markeredgecolor=fs.INK,
        label="正例侧成员标准差",
        zorder=4,
    )
    ax2.plot(
        positions,
        neg,
        color="#666666",
        linestyle=(0, (5, 2)),
        linewidth=1.0,
        marker="s",
        markersize=3.8,
        markerfacecolor=fs.WHITE,
        markeredgecolor="#666666",
        label="负例侧成员标准差",
        zorder=3,
    )
    ax2.set_yscale("log")
    ax2.set_ylim(5e-4, 2e-1)
    ax2.set_yticks([1e-3, 1e-2, 1e-1])
    ax2.set_yticklabels(["0.001", "0.01", "0.1"], size=8.0)
    ax2.set_xticks(positions)
    ax2.set_xticklabels(YEARS, rotation=45, ha="right", size=8.0)
    ax2.set_ylabel(fs.checked("成员间标准差（对数刻度）", 9.0), size=9.0, labelpad=5.0)
    ratio_2023 = float(rows[9]["member_std_pos"]) / float(rows[9]["member_std_neg"])
    ratio_2024 = float(rows[10]["member_std_pos"]) / float(rows[10]["member_std_neg"])
    ax2.set_title(
        fs.checked(
            f"(b) 成员分歧的逐年形态\n2023 正/负 {ratio_2023:.1f}×；"
            f"2024 正/负 {ratio_2024:.1f}×",
            9.0,
        ),
        loc="left",
        size=9.0,
        pad=4.0,
    )
    ax2.grid(axis="y", color="#D9D9D9", linewidth=0.5, zorder=1)
    ax2.set_axisbelow(True)
    for side in ("top", "right"):
        ax2.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax2.spines[side].set_linewidth(0.7)
        ax2.spines[side].set_color(fs.INK)
    ax2.tick_params(axis="both", labelsize=8.0, length=2.5, width=0.6, pad=2.5)
    ax2.legend(
        loc="lower left",
        frameon=False,
        fontsize=8.0,
        handlelength=2.8,
        labelspacing=0.5,
    )

    fig.text(
        0.5,
        0.128,
        fs.checked(
            "分解为恒等式：训练通道 = 成员 F1 均值 - 底座 F1；"
            "评测通道 = 集成 F1 - 成员 F1 均值；12 年均值含 2025 年零值。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    fig.text(
        0.5,
        0.075,
        fs.checked(
            "2025 年测试分片仅 5 条正例，全部成员与集成的 F1 均为 0；"
            "2023 与 2024 年正例样本分别为 1,578 与 159 条。",
            8.0,
        ),
        ha="center",
        va="center",
        size=8.0,
        color=fs.MUTED,
    )
    return fig


# ---------------------------------------------------------------- 清单登记


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stem_key(stem: str) -> tuple[int, int, str]:
    match = re.search(r"图(\d+)-(\d+)", stem)
    if match:
        return (int(match.group(1)), int(match.group(2)), stem)
    return (99, 99, stem)


def build_entry(
    stem: str,
    caption: str,
    spec_width: float,
    spec_height: float,
    evidence_mode: str,
    data_keys: list[str],
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    outputs: dict[str, str] = {}
    sizes: dict[str, int] = {}
    hashes: dict[str, str] = {}
    for suffix in ("png", "pdf", "svg"):
        path = HERE / f"{stem}.{suffix}"
        if not path.exists():
            raise FileNotFoundError(f"缺少输出文件：{path}")
        outputs[suffix] = path.name
        sizes[suffix] = path.stat().st_size
        hashes[suffix] = sha256(path)

    from PIL import Image

    with Image.open(HERE / outputs["png"]) as image:
        px_w, px_h = image.size
    ppi_w = px_w / (spec_width / 25.4)
    ppi_h = px_h / (spec_height / 25.4)
    if min(ppi_w, ppi_h) < 300.0 - 1e-6:
        raise ValueError(f"{stem} 实测 ppi 低于 300：{ppi_w:.1f}x{ppi_h:.1f}")

    entry: dict[str, object] = {
        "stem": stem,
        "caption": caption,
        "generator": GENERATOR_REL,
        "environment_ref": "matplotlib_environment",
        "typography_ref": "matplotlib_typography",
        "width_mm": round(spec_width, 2),
        "height_mm": round(spec_height, 2),
        "png_dpi": fs.PNG_DPI,
        "png_pixels": [px_w, px_h],
        "png_ppi_measured": [round(ppi_w, 1), round(ppi_h, 1)],
        "bytes": sizes["png"],
        "bytes_by_format": sizes,
        "sha256": hashes["png"],
        "sha256_by_format": hashes,
        "outputs": outputs,
        "evidence_mode": evidence_mode,
        "data_keys": data_keys,
    }
    if extra:
        entry.update(extra)
    return entry


def update_manifest(entries: list[dict[str, object]]) -> Path:
    path = HERE / "图件清单.json"
    manifest = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    new_stems = {entry["stem"] for entry in entries}
    figures = [
        figure
        for figure in manifest.get("figures", [])
        if figure.get("stem") not in new_stems
    ]
    figures.extend(entries)
    manifest["figures"] = sorted(figures, key=lambda item: stem_key(str(item["stem"])))

    import matplotlib
    import numpy
    import PIL

    manifest["contract"] = (
        "AGENTS.md 学位论文图件合同（2026-08-13 重定）；数据图按合同 "
        "300 dpi 下限、实际 400 dpi 导出 PNG+PDF+SVG"
    )
    manifest["figure_mode"] = "matplotlib 数据图/示意图（数值从运行制品 JSON 读取）"
    manifest["grayscale_readable"] = True
    manifest["data_mode"] = (
        "图 4-1 的结构与算量取自 tabm4-result.json 与 4.3、4.4 正文；"
        "图 4-2 读取五臂 train_logs 的 epoch_disagreement；"
        "图 4-3 读取 general-comparison.json、baselines-comparison.json 与结果 JSON；"
        "图 4-4 读取 general-comparison.json 的 k_curve 与 width_variant；"
        "图 4-5 读取 member-disagreement-diag.json、tabm4-result.json 与 base-result.json。"
    )
    executable = Path(sys.executable)
    try:
        executable_label = str(executable.relative_to(HERE))
    except ValueError:
        executable_label = executable.name
    manifest["matplotlib_environment"] = {
        "generator": GENERATOR_REL,
        "style_module": "thesis/figures/第三章/figstyle.py",
        "uv_project": "thesis/figures/第四章",
        "uv_lock_sha256": sha256(HERE / "uv.lock"),
        "command": (
            'uv run --project "thesis/figures/第四章" --locked python '
            '"thesis/figures/第四章/绘制第四章图件.py"'
        ),
        "python": ".".join(str(v) for v in sys.version_info[:3]),
        "python_executable": executable_label,
        "matplotlib": matplotlib.__version__,
        "numpy": numpy.__version__,
        "pillow": PIL.__version__,
        "os": platform.platform(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    manifest["matplotlib_typography"] = {
        "cjk_font_requested": fs.CJK_FONT.requested,
        "cjk_font_used": fs.CJK_FONT.family,
        "cjk_font_path": fs.CJK_FONT.path,
        "cjk_face_index": fs.CJK_FONT.face_index,
        "latin_font_used": fs.LATIN_FONT.family,
        "latin_font_path": fs.LATIN_FONT.path,
        "math_fontset": (
            "stix" if fs.MATH_FONT is None else f"custom ({fs.MATH_FONT.family})"
        ),
        "min_font_pt": fs.MIN_FONT_PT,
        "main_font_pt": fs.MAIN_FONT_PT,
        "main_line_pt": fs.MAIN_LINE_PT,
        "aux_line_pt": fs.AUX_LINE_PT,
        "png_dpi": fs.PNG_DPI,
    }
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------- 主流程


def main() -> None:
    arms = load_constraint_arms()
    points, budget_data = load_budget_points()
    rows, means, _ = load_dual_channel()

    architecture = draw_architecture()
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图4-1-预算约束成员化训练的总体结构",
            width_mm=165.0,
            height_mm=125.0,
            draw=None,
        ),
        architecture,
    )

    trajectories = draw_constraint_trajectories(arms)
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图4-2-三类显式分工约束的成员分歧轨迹与跨年读数",
            width_mm=165.0,
            height_mm=125.0,
            draw=None,
        ),
        fs.Canvas(trajectories, trajectories.axes[0], 165.0, 125.0),
    )

    budget_map = draw_budget_map(points)
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图4-3-参数总量与跨年平均F1的对照",
            width_mm=150.0,
            height_mm=100.0,
            draw=None,
        ),
        fs.Canvas(budget_map, budget_map.axes[0], 150.0, 100.0),
    )

    sensitivity = draw_sensitivity(points)
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图4-4-成员数与骨干宽度的敏感性曲线",
            width_mm=150.0,
            height_mm=95.0,
            draw=None,
        ),
        fs.Canvas(sensitivity, sensitivity.axes[0], 150.0, 95.0),
    )

    dual_channel = draw_dual_channel(rows, means)
    fs.save_figure(
        HERE,
        fs.FigureSpec(
            stem="图4-5-增益的双通道分解与成员分歧的逐年形态",
            width_mm=165.0,
            height_mm=112.0,
            draw=None,
        ),
        fs.Canvas(dual_channel, dual_channel.axes[0], 165.0, 112.0),
    )

    tabm4 = budget_data["tabm4"]
    entries = [
        build_entry(
            "图4-1-预算约束成员化训练的总体结构",
            "预算约束成员化训练的总体结构。年度 t 的训练批由第三章回放构成 P_t 给出；"
            "共享主干上并行训练 k=4 个成员，成员适配参数为输入与输出尺度向量；"
            "训练信号为全体成员二元交叉熵的均值，评测取成员概率均值，阈值 0.5，"
            "当年更新 10 轮后回看全部已到达年度。",
            165.0,
            125.0,
            "架构示意（依据 4.3、4.4 正文与 tabm4-result.json 的参数量）",
            [
                "thesis/chapters/第四章-LAMDA/4.3-方法框架设计.md §4.3.1–§4.3.4",
                "thesis/chapters/第四章-LAMDA/4.4-算法实现与模型适配.md",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "tabm4-result.json.{n_params,k,protocol}",
            ],
            {
                "parameters": {
                    "shared_trunk": 2686014,
                    "member_adapters": 37291,
                    "total": int(tabm4["n_params"]),
                    "k": int(tabm4["k"]),
                },
                "verification": {
                    "total": "共享主干 + 成员适配 = 2,686,014 + 37,291 = 2,723,305",
                    "k": "tabm4-result.json.k = 4",
                    "protocol": "tabm4-result.json.protocol 与 4.6.1 节一致",
                },
            },
        ),
        build_entry(
            "图4-2-三类显式分工约束的成员分歧轨迹与跨年读数",
            "三类显式分工约束的成员分歧轨迹与跨年读数。上排为五臂在 12 个年度的"
            "首轮成员判定不一致率（跨年起点），下排为 2024 年度十轮训练内的不一致率轨迹；"
            "左列为 NCL 系与单路损失参照，右列为成对相关惩罚。"
            "NCL 臂的跨年起点由 2016 年度的 2.25% 降至 2024 年度的 0.24%，"
            "成对相关惩罚臂在 2020 至 2022 年度维持约 30% 的起点，"
            "但 12 年平均 F1 为 0。",
            165.0,
            125.0,
            "真实数据：五臂 train_logs 的 epoch_disagreement 逐轮探针",
            [
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-ncl-pilot/"
                "<arm>-result.json.train_logs.<year>.epoch_disagreement",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-corr-pilot/"
                "<arm>-result.json.train_logs.<year>.epoch_disagreement",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-ncl-pilot/"
                "ncl-comparison.json.arms.<arm>.epoch_disagreement_2024",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-corr-pilot/"
                "corr-comparison.json.arms.<arm>.epoch_disagreement_2024",
            ],
            {
                "years": list(YEARS),
                "arms": {
                    arm: {
                        "mean_f1": float(arms[arm]["mean_f1"]),
                        "f1_2023": float(arms[arm]["f1_2023"]),
                        "f1_2024": float(arms[arm]["f1_2024"]),
                        "first_epoch_by_year": [
                            round(rate, 12) for rate in arms[arm]["first_epoch_by_year"]
                        ],
                        "within_2024": [
                            round(rate, 12) for rate in arms[arm]["epoch_rates"]["2024"]
                        ],
                    }
                    for arm in ARMS
                },
                "verification": {
                    "years_order": "train_logs 键序与 12 个年度逐位一致",
                    "epoch_order": "每个年度 10 轮，epoch 序号 1 至 10",
                    "probe_n": "每个轮次探针 n=4096",
                    "summary_match": "2024 逐轮数组与 comparison 的 epoch_disagreement_2024.rates 逐位一致",
                    "first3_last3": "ncl05 2021-2024 比值 3.2/2.3/2.6/2.5；"
                    "train_single 2021-2023 比值 0.8/0.4/1.1",
                },
            },
        ),
        build_entry(
            "图4-3-参数总量与跨年平均F1的对照",
            "参数总量与跨年平均 F1 的对照（五种配置的预算位置）。横轴为参数总量，"
            "对数刻度；纵轴为 12 年平均 F1。均匀成员化位于左上（2.72M 参数、83.23%），"
            "深度集成位于右上（10.75M 参数、82.33%），底座与半宽骨干位于左侧。",
            150.0,
            100.0,
            "真实数据：general-comparison.json、baselines-comparison.json 与结果 JSON",
            [
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-general-pilot/"
                "general-comparison.json.k_curve 与 width_variant",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-baselines-pilot/"
                "baselines-comparison.json.table 与 budget_claim",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "tabm4-result.json.{mean_f1,n_params}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-paat-pilot/"
                "base-result.json.mean_f1",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-baselines-pilot/"
                "deep4-result.json.{mean_f1,n_params}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-baselines-pilot/"
                "mcdrop-result.json.n_params（底座同架构参数量）",
            ],
            {
                "points": [
                    {
                        "key": point["key"],
                        "label": point["label"],
                        "n_params": int(point["n_params"]),
                        "mean_f1": float(point["mean_f1"]),
                        "budget_label": (
                            "单次预算"
                            if point["key"] == "uniform"
                            else ("4× 预算" if point["key"] == "deep4" else None)
                        ),
                    }
                    for point in points
                    if point["key"] != "k2"
                ],
                "verification": {
                    "k_curve_match": "k2/tabm4/tabm8 的 mean_f1、f1_2023、f1_2024、n_params、"
                    "wall_seconds 与各自结果 JSON 逐位一致",
                    "width_match": "半宽骨干的 delta_mean12_pp、delta_2024_pp、param_ratio "
                    "由 halfwidth 与 tabm4 结果逐位计算",
                    "budget_claim": "baselines-comparison.json.budget_claim.abs_diff 与 "
                    "tabm4-base 差逐位一致，supported=true",
                    "base_n_params": "base-result.json 未登记 n_params；取同架构 mcdrop/swa "
                    "与 deep4 单成员的 2,687,293",
                },
            },
        ),
        build_entry(
            "图4-4-成员数与骨干宽度的敏感性曲线",
            "成员数与骨干宽度的敏感性曲线。左轴为 12 年平均 F1，右轴为 2024 年度 F1；"
            "实线圆点为 12 年平均，虚线方点为 2024 年度，成员数取 2、4、8。"
            "半宽骨干为 k=4 的骨干宽度变体，以空心菱形并入，横向略移以区分；"
            "其 12 年平均低 0.61 个百分点，2024 年度低 2.71 个百分点。",
            150.0,
            95.0,
            "真实数据：general-comparison.json 的 k_curve 与 width_variant",
            [
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-general-pilot/"
                "general-comparison.json.k_curve[0..2]",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-general-pilot/"
                "general-comparison.json.width_variant",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-general-pilot/"
                "k2-result.json.{mean_f1,f1_2024,n_params}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "tabm4-result.json.{mean_f1,f1_2024,n_params}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "tabm8-result.json.{mean_f1,f1_2024,n_params}",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-general-pilot/"
                "halfwidth-result.json.{mean_f1,f1_2024,n_params}",
            ],
            {
                "k_curve": [
                    {
                        "k": entry["k"],
                        "arm": entry["arm"],
                        "mean_f1": float(entry["mean_f1"]),
                        "f1_2024": float(entry["f1_2024"]),
                        "n_params": int(entry["n_params"]),
                        "wall_seconds": float(entry["wall_seconds"]),
                    }
                    for entry in budget_data["general"]["k_curve"]
                ],
                "width_variant": {
                    "arm": "halfwidth",
                    "mean_f1": float(budget_data["halfwidth"]["mean_f1"]),
                    "f1_2024": float(budget_data["halfwidth"]["f1_2024"]),
                    "n_params": int(budget_data["halfwidth"]["n_params"]),
                    "param_ratio": float(
                        budget_data["general"]["width_variant"]["param_ratio"]
                    ),
                    "delta_mean12_pp": float(
                        budget_data["general"]["width_variant"]["delta_mean12_pp"]
                    ),
                    "delta_2024_pp": float(
                        budget_data["general"]["width_variant"]["delta_2024_pp"]
                    ),
                },
                "verification": {
                    "k2_match": "k_curve[0] 与 k2-result.json 逐位一致",
                    "tabm4_match": "k_curve[1] 与 tabm4-result.json 逐位一致",
                    "tabm8_match": "k_curve[2] 与 tabm8-result.json 逐位一致",
                    "halfwidth_match": "width_variant 由 halfwidth-result.json 与 "
                    "tabm4-result.json 逐位计算",
                },
            },
        ),
        build_entry(
            "图4-5-增益的双通道分解与成员分歧的逐年形态",
            "增益的双通道分解与成员分歧的逐年形态。左图为 base 至 uniform 的逐年增益，"
            "按评测平均通道与训练通道堆叠，黑色菱形为合计；最右侧为 12 年均值。"
            "右图为正例侧与负例侧成员间标准差的逐年形态，对数刻度；"
            "2023 与 2024 年正例侧分别为负例侧的 16.6 与 42.9 倍。",
            165.0,
            112.0,
            "真实数据：member-disagreement-diag.json、tabm4-result.json 与 base-result.json",
            [
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "member-disagreement-diag.json.years.<year>.f1_per_member",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "member-disagreement-diag.json.years.<year>.f1_ensemble",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "member-disagreement-diag.json.years.<year>.member_std_pos",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "member-disagreement-diag.json.years.<year>.member_std_neg",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-tabm-pilot/"
                "tabm4-result.json.backward_f1",
                "thesis/experiments/llm_probe/runs/diagnostics/ch4-lamda-paat-pilot/"
                "base-result.json.backward_f1",
            ],
            {
                "years": list(YEARS),
                "rows": [
                    {
                        "year": row["year"],
                        "base_f1": row["base_f1"],
                        "member_mean_f1": row["member_mean"],
                        "ensemble_f1": row["ensemble_f1"],
                        "train_channel_pp": row["train_channel"] * 100.0,
                        "eval_channel_pp": row["eval_channel"] * 100.0,
                        "total_pp": row["total"] * 100.0,
                        "member_std_pos": row["member_std_pos"],
                        "member_std_neg": row["member_std_neg"],
                    }
                    for row in rows
                ],
                "means_pp": {
                    "train_channel": means["train_channel"] * 100.0,
                    "eval_channel": means["eval_channel"] * 100.0,
                    "total": means["total"] * 100.0,
                },
                "verification": {
                    "identity_gate": "member-disagreement-diag.json.identity_gate.passed = true",
                    "ensemble_match": "每年 f1_ensemble 与 tabm4-result.json.backward_f1 逐位一致",
                    "per_member_count": "每年 f1_per_member 长度 = k = 4",
                    "channel_identity": "训练通道 + 评测通道 = 合计（容差 1e-12）",
                    "means": "12 年均值（含 2025 年零值）为 0.47、1.07、1.54 个百分点",
                    "std_ratio": "2023 与 2024 年正/负成员标准差比分别为 16.6 与 42.9",
                },
            },
        ),
    ]

    manifest = update_manifest(entries)
    for line in fs.verify_outputs(HERE, entries):
        print(line)
    print(f"图件清单：{manifest}")
    print("[数据核对]")
    print("  图 4-2 ncl05 跨年起点：")
    for year in ("2016", "2023", "2024"):
        rate = arms["ncl05"]["first_epoch_by_year"][YEARS.index(year)] * 100.0
        print(f"    {year}: {rate:.4f}%")
    print("  图 4-3 预算位置：")
    for point in points:
        print(
            f"    {point['label']}: {point['n_params']:,} 参数，"
            f"12 年平均 F1 {point['mean_f1'] * 100.0:.4f}%"
        )
    print("  图 4-4 成员数曲线：")
    for entry in budget_data["general"]["k_curve"]:
        print(
            f"    k={entry['k']}: 12y {entry['mean_f1'] * 100.0:.4f}%，"
            f"2024 {entry['f1_2024'] * 100.0:.4f}%"
        )
    print("  图 4-5 双通道 12 年均值：")
    print(
        f"    训练 {means['train_channel'] * 100.0:.4f} pp，"
        f"评测 {means['eval_channel'] * 100.0:.4f} pp，"
        f"合计 {means['total'] * 100.0:.4f} pp"
    )


if __name__ == "__main__":
    main()
