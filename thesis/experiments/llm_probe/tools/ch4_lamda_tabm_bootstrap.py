#!/usr/bin/env python
"""第四章 tabm4 / tabm8 相对 base 的配对 bootstrap 诊断。

目的：在"目标知情评价面板"（12 年测试集，2023/2024 目标年标签已参与臂选择）
上量化样本不确定性，不重训、不新增随机种子。结论仅代表该面板内的测试样本噪声，
不冒充独立最终测试。

设计（冻结）：
  - 配对：每年在同一个有放回重采样索引下同时抽取 base 与 tabm 的分数，
    保留样本级相关（同一测试样本的两种模型分数同时进/出重采样）；
  - 年度内 F1 使用标准公式，阈值固定 0.5（判定规则 y_score >= 0.5），
    分母为 0 时记 0，与 ch4_lamda_posthoc_prior_diag.py::f1_at 同义；
  - 12 年统计量 Δ = mean_F1(tabm) − mean_F1(base)，年度等权；
  - B = 10,000，95% 百分位区间，种子 42（np.random.default_rng(42)）。

实现要点：把每个样本编码为 8 类 (y, pred_base, pred_tabm)，一次重采样的
F1 只需该 8 类的计数，避免逐次 gather 分数与布尔运算。每年独立重采样，
12 年统计量按年累加后除以 12；年度重采样与年际独立，与"每年抽 n_year 个样本"
一致。随机数按年份外层、重复内层、行主序生成，结果可复现。

运行：/opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_tabm_bootstrap.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

TOOLS_DIR = Path(__file__).resolve().parent
RUNS = TOOLS_DIR.parent / "runs/diagnostics"
BASE_DIR = RUNS / "ch4-lamda-paat-pilot"
TABM_DIR = RUNS / "ch4-lamda-tabm-pilot"
OUT = TABM_DIR / "tabm-bootstrap.json"

YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
ARMS = ["tabm4", "tabm8"]
TAU = 0.5
N_BOOT = 10_000
SEED = 42
CHI = 2.5  # 95% 百分位区间
CHUNK = 256  # 每次向量化的重采样行数，控制内存

REFERENCE = TABM_DIR / "tabm-comparison.json"
GATE_TOL = 1e-9


def f1_at(score: np.ndarray, y: np.ndarray, tau: float) -> float:
    """标准二分类 F1，与 ch4_lamda_posthoc_prior_diag.py::f1_at 同义。"""
    pred = score >= tau
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    d = 2 * tp + fp + fn
    return float(2 * tp / d) if d else 0.0


def f1_from_counts(tp: np.ndarray, fp: np.ndarray, fn: np.ndarray) -> np.ndarray:
    """向量化 F1；分母为 0 时记 0，与 f1_at 同义。"""
    d = 2 * tp + fp + fn
    return np.where(d > 0, 2 * tp / np.maximum(d, 1), 0.0)


def classify(y: np.ndarray, pred_base: np.ndarray, pred_tabm: np.ndarray) -> np.ndarray:
    """编码为 0..7：cat = 4*y + 2*pred_base + pred_tabm。"""
    return (4 * (y == 1).astype(np.int8)
            + 2 * pred_base.astype(np.int8)
            + pred_tabm.astype(np.int8))


def boot_counts(cat: np.ndarray, rng: np.random.Generator, n_boot: int) -> np.ndarray:
    """每年：返回 (n_boot, 8) 的类别计数。同一索引同时服务两臂（配对）。"""
    n = cat.size
    counts = np.empty((n_boot, 8), dtype=np.int64)
    cat = cat.astype(np.int64)
    for start in range(0, n_boot, CHUNK):
        stop = min(start + CHUNK, n_boot)
        c = stop - start
        idx = rng.integers(0, n, size=(c, n))
        # 行偏移使一次 bincount 即可按重采样行分组计数
        g = cat[idx] + 8 * np.arange(c, dtype=np.int64)[:, None]
        counts[start:stop] = np.bincount(g.ravel(), minlength=8 * c).reshape(c, 8)
    return counts


def delta_from_counts(counts: np.ndarray) -> np.ndarray:
    """由 8 类计数还原逐年 ΔF1 = F1(tabm) − F1(base)。

    cat = 4*y + 2*pred_base + pred_tabm：
      base TP: y=1,pb=1 → 6,7；FP: y=0,pb=1 → 2,3；FN: y=1,pb=0 → 4,5
      tabm TP: y=1,pt=1 → 5,7；FP: y=0,pt=1 → 1,3；FN: y=1,pt=0 → 4,6
    """
    tp_b = counts[:, 6] + counts[:, 7]
    fp_b = counts[:, 2] + counts[:, 3]
    fn_b = counts[:, 4] + counts[:, 5]
    tp_t = counts[:, 5] + counts[:, 7]
    fp_t = counts[:, 1] + counts[:, 3]
    fn_t = counts[:, 4] + counts[:, 6]
    return f1_from_counts(tp_t, fp_t, fn_t) - f1_from_counts(tp_b, fp_b, fn_b)


def ci(values: np.ndarray) -> list[float]:
    lo, hi = np.percentile(values, [CHI, 100.0 - CHI])
    return [float(lo), float(hi)]


def excludes_zero(interval: list[float]) -> bool:
    return bool(interval[0] > 0.0 or interval[1] < 0.0)


def main() -> None:
    rng = np.random.default_rng(SEED)

    # ---------- 读入并核对对齐 ----------
    y_by_year: dict[int, np.ndarray] = {}
    cat_by_year: dict[str, dict[int, np.ndarray]] = {arm: {} for arm in ARMS}
    point_f1: dict[str, dict[str, float]] = {"base": {}}
    for arm in ARMS:
        point_f1[arm] = {}

    for year in YEARS:
        b = np.load(BASE_DIR / f"preds_base_{year}.npz")
        y_true = b["y_true"]
        score_base = b["y_score"]
        if not np.isclose(float(b["threshold"]), TAU):
            raise SystemExit(f"{year}: base threshold 不是 0.5")
        pred_base = score_base >= TAU
        y_by_year[year] = y_true
        point_f1["base"][str(year)] = f1_at(score_base, y_true, TAU)

        for arm in ARMS:
            t = np.load(TABM_DIR / f"preds_{arm}_{year}.npz")
            if not np.array_equal(y_true, t["y_true"]):
                raise SystemExit(f"{year}/{arm}: y_true 与 base 不一致，无法配对")
            if not np.isclose(float(t["threshold"]), TAU):
                raise SystemExit(f"{year}/{arm}: threshold 不是 0.5")
            score_tabm = t["y_score"]
            point_f1[arm][str(year)] = f1_at(score_tabm, y_true, TAU)
            cat_by_year[arm][year] = classify(y_true, pred_base, score_tabm >= TAU)

    # ---------- 点估计与复现门禁 ----------
    ref = json.loads(REFERENCE.read_text(encoding="utf-8"))
    if abs(float(np.mean(list(point_f1["base"].values()))) - ref["reference_base_mean"]) > GATE_TOL:
        raise SystemExit("base 12 年均值未复现 tabm-comparison.json")
    for arm in ARMS:
        if abs(float(np.mean(list(point_f1[arm].values()))) - ref["arms"][arm]["mean_f1"]) > GATE_TOL:
            raise SystemExit(f"{arm} 12 年均值未复现 tabm-comparison.json")

    # ---------- 配对 bootstrap ----------
    delta_draws: dict[str, np.ndarray] = {}
    year_draws: dict[str, dict[int, np.ndarray]] = {arm: {} for arm in ARMS}
    for arm in ARMS:
        delta_sum = np.zeros(N_BOOT, dtype=np.float64)
        for year in YEARS:
            counts = boot_counts(cat_by_year[arm][year], rng, N_BOOT)
            d = delta_from_counts(counts)
            year_draws[arm][year] = d
            delta_sum += d
        delta_draws[arm] = delta_sum / len(YEARS)

    # ---------- 汇总 ----------
    result: dict[str, object] = {
        "schema_version": "ch4-tabm-bootstrap-v1",
        "panel_note": (
            "目标知情评价面板：2023/2024 目标年标签已参与臂选择，"
            "本区间只量化测试样本不确定性，不构成独立最终检验。"
            "未重训，仅重采样测试样本。"
        ),
        "method": {
            "statistic": "Δ = mean_F1(tabm) − mean_F1(base)，12 年年度等权平均",
            "decision_rule": "y_score >= 0.5",
            "f1_rule": "标准 F1 = 2TP/(2TP+FP+FN)，分母为 0 时记 0",
            "n_boot": N_BOOT,
            "seed": SEED,
            "rng": "np.random.default_rng(42)",
            "ci": "95% 百分位区间（2.5 / 97.5 分位）",
            "paired": True,
            "pairing_detail": (
                "每年在同一次有放回重采样索引下同时抽取 base 与 tabm 的分数；"
                "年际独立重采样，每年样本数为该年测试集规模"
            ),
            "no_retraining": True,
            "years": YEARS,
        },
        "point_f1": point_f1,
        "arms": {},
    }

    arm_out: dict[str, object] = {}
    for arm in ARMS:
        point_12y = float(np.mean([point_f1[arm][str(y)] for y in YEARS])
                          - np.mean([point_f1["base"][str(y)] for y in YEARS]))
        ci_12y = ci(delta_draws[arm])
        per_year = {}
        for year in (2023, 2024):
            point_year = point_f1[arm][str(year)] - point_f1["base"][str(year)]
            ci_year = ci(year_draws[arm][year])
            per_year[str(year)] = {
                "delta_point": point_year,
                "ci95": ci_year,
                "ci_excludes_zero": excludes_zero(ci_year),
            }
        arm_out[arm] = {
            "delta_12y_point": point_12y,
            "ci95_12y": ci_12y,
            "ci_excludes_zero": excludes_zero(ci_12y),
            "per_year": per_year,
        }
    result["arms"] = arm_out
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
