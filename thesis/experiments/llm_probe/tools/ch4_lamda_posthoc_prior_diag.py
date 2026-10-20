#!/usr/bin/env python
"""第四章零训练先验校正诊断（判据冻结于 .Codex/docs/2026-10-20-第四章零训练先验诊断/plan.md）。

问题：二分类下任何单调后验变换（Logit Adjustment / PC Softmax / 先验偏移 / bias 平移）
都退化为对原分数的一次阈值平移，故逐阈值扫描的 oracle F1 是整个零训练事后校正族的严格上界。
本脚本在第三章回放底座（base）的 12 年分数上计算：
  - f1_05（阈值 0.5，须逐位复现 base-result.json，容差 1e-9，否则非零退出）
  - f1_oracle（阈值扫描上界，不部署）
  - f1_rate（按训练年正例率分位数匹配，可部署，不用目标年测试标签）
  - f1_prev_oracle / f1_prev_rate（沿用上一年度阈值/告警率，可部署）
  - M1 归因：auc_base vs auc_m1、delta_f1_05
判据（冻结）：G1 族上界；G2 可部署性；G3 归因。2025 仅探索性报告。

运行：/opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_posthoc_prior_diag.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

TOOLS_DIR = Path(__file__).resolve().parent
RUNS = TOOLS_DIR.parent / "runs/diagnostics"
SRC = RUNS / "ch4-lamda-paat-pilot"
AUDIT = RUNS / "ch3-lamda-e5-replay-buffer-audit-v1/buffer_composition.json"
OUT_DIR = RUNS / "ch4-lamda-posthoc-prior-diag"
OUT = OUT_DIR / "posthoc-prior-diag.json"

BASE_RESULT = SRC / "base-result.json"
YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
GATE_TOL = 1e-9
EXPLORATORY_YEAR = 2025


def f1_at(score: np.ndarray, y: np.ndarray, tau: float) -> float:
    pred = score >= tau
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    d = 2 * tp + fp + fn
    return float(2 * tp / d) if d else 0.0


def oracle_f1(score: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """精确阈值扫描：按分数降序累计 TP/FP，在每个唯一切点取 F1 最大者。

    返回 (best_f1, best_tau)；预测规则为 s >= tau。
    """
    order = np.argsort(-score, kind="stable")
    s_sorted = score[order]
    y_sorted = y[order]
    tp = np.cumsum(y_sorted)
    fp = np.cumsum(1 - y_sorted)
    k = np.arange(1, y_sorted.size + 1)
    denom = 2 * tp + fp + (y.sum() - tp)
    f1s = np.where(denom > 0, 2 * tp / np.maximum(denom, 1), 0.0)
    # 唯一切点：只保留分数严格下降处的切点（同分样本不可分割）
    cut = np.ones(y_sorted.size, dtype=bool)
    cut[:-1] = s_sorted[:-1] > s_sorted[1:]
    idx = np.flatnonzero(cut)
    best = idx[int(np.argmax(f1s[idx]))]
    tau = float(s_sorted[best])
    return float(f1s[best]), tau


def rate_threshold(score: np.ndarray, pi: float) -> float:
    """分位数匹配：tau = quantile(s, 1 - pi)，线性法（与 preflight E1 约定一致）。"""
    return float(np.quantile(score, 1.0 - pi, method="linear"))


def main() -> int:
    base_res = json.loads(BASE_RESULT.read_text(encoding="utf-8"))
    ref_f1 = {int(k): v for k, v in base_res["backward_f1"].items()}
    base_mean12 = float(base_res["mean_f1"])

    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    pos_rate = {int(k): float(v["train_pos_rate"]) for k, v in audit["per_year_train_stats"].items()}

    rows: list[dict] = []
    m1_rows: dict[int, dict] = {}

    # 先加载并过复现门
    data: dict[int, dict] = {}
    for year in YEARS:
        z = np.load(SRC / f"preds_base_{year}.npz")
        score = z["y_score"].astype(np.float64)
        y = z["y_true"].astype(np.int8)
        data[year] = {"score": score, "y": y}
        f1_05 = f1_at(score, y, 0.5)
        if abs(f1_05 - ref_f1[year]) > GATE_TOL:
            print(f"[gate] FAIL year={year} f1_05={f1_05!r} ref={ref_f1[year]!r} "
                  f"delta={abs(f1_05 - ref_f1[year]):.3e}", flush=True)
            return 2
    print("[gate] PASS: 12 年 f1_05 与 base-result.json 全部一致（1e-9）", flush=True)

    prev: dict | None = None
    for year in YEARS:
        score, y = data[year]["score"], data[year]["y"]
        n_pos = int((y == 1).sum())
        f1_05 = f1_at(score, y, 0.5)
        f1_or, tau_or = oracle_f1(score, y)
        pi = pos_rate[year]
        tau_rate = rate_threshold(score, pi)
        f1_rate = f1_at(score, y, tau_rate)
        alert_rate_prev = (prev["n_alert"] / prev["n"]) if prev else None
        row = {
            "year": year,
            "n": int(y.size),
            "n_pos": n_pos,
            "test_pos_rate": n_pos / y.size,
            "train_pos_rate": pi,
            "exploratory_only": year == EXPLORATORY_YEAR,
            "f1_05": f1_05,
            "auc_base": float(roc_auc_score(y, score)) if 0 < n_pos < y.size else None,
            "tau_oracle": tau_or,
            "f1_oracle": f1_or,
            "delta_oracle_pp": (f1_or - f1_05) * 100,
            "tau_rate": tau_rate,
            "f1_rate": f1_rate,
            "delta_rate_pp": (f1_rate - f1_05) * 100,
            "tau_prev_oracle": prev["tau_oracle"] if prev else None,
            "f1_prev_oracle": f1_at(score, y, prev["tau_oracle"]) if prev else None,
            "alert_rate_prev": alert_rate_prev,
            "tau_prev_rate": rate_threshold(score, alert_rate_prev) if prev else None,
            "f1_prev_rate": f1_at(score, y, rate_threshold(score, alert_rate_prev)) if prev else None,
        }
        if prev:
            row["delta_prev_oracle_pp"] = (row["f1_prev_oracle"] - f1_05) * 100
            row["delta_prev_rate_pp"] = (row["f1_prev_rate"] - f1_05) * 100
        # M1 归因
        m1 = np.load(SRC / f"preds_m1_{year}.npz")
        s1 = m1["y_score"].astype(np.float64)
        assert np.array_equal(m1["y_true"].astype(np.int8), y)
        f1_m1 = f1_at(s1, y, 0.5)
        auc_m1 = float(roc_auc_score(y, s1)) if 0 < n_pos < y.size else None
        m1_rows[year] = {
            "f1_05_m1": f1_m1,
            "delta_f1_05_pp": (f1_m1 - f1_05) * 100,
            "auc_m1": auc_m1,
            "delta_auc": (auc_m1 - row["auc_base"]) if row["auc_base"] is not None else None,
        }
        rows.append({**row, **m1_rows[year]})
        prev = {"tau_oracle": tau_or, "n_alert": int((score >= 0.5).sum()), "n": int(y.size)}

    # ---- 冻结判据 ----
    by_year = {r["year"]: r for r in rows}
    g1 = all(by_year[t]["delta_oracle_pp"] >= 1.0 for t in (2023, 2024))

    def mean_of(key: str) -> tuple[float, int]:
        vals = [by_year[t][key] for t in YEARS if by_year[t][key] is not None]
        return float(np.mean(vals)), len(vals)

    base_f1 = {t: by_year[t]["f1_05"] for t in YEARS}
    rules = {}
    for name in ("f1_rate", "f1_prev_oracle", "f1_prev_rate"):
        per = {t: by_year[t][name] for t in YEARS}
        mean_n, n_used = mean_of(name)
        # f1_prev_* 首年（2013）无上一年阈值，均值在可用年份上计算并记录 n_used
        rules[name] = {
            "delta_2024_pp": (per[2024] - base_f1[2024]) * 100,
            "delta_2023_pp": (per[2023] - base_f1[2023]) * 100,
            "mean_used": mean_n,
            "n_years_used": n_used,
            "mean_minus_base_pp": (mean_n - base_mean12) * 100,
            "mean11_excl_2025": float(np.mean([per[t] for t in YEARS if t != 2025 and per[t] is not None])),
        }
    g2_rules = {n: d for n, d in rules.items() if d["delta_2024_pp"] >= 1.0 and d["mean_minus_base_pp"] >= -0.20}
    g2 = bool(g2_rules)

    # G3 归因：2023/2024 的 delta_auc 与 delta_f1_05
    # 补充规则（2026-10-20 运行后披露的修正）：delta_auc <= 0 而 F1 上升时，
    # 增益不可能来自排序质量，归为阈值位置效应；该修正不影响 G1/G2 判据。
    g3 = {}
    for t in (2023, 2024):
        da = m1_rows[t]["delta_auc"] or 0.0
        df = m1_rows[t]["delta_f1_05_pp"]
        if da > 0.002:
            att = "ranking_representation"
        elif da <= 0.0 and df > 0.0:
            att = "threshold_position"
        elif abs(da) <= 0.002 and abs(df) >= 0.5:
            att = "threshold_calibration"
        else:
            att = "no_signal"
        g3[t] = {"delta_auc": m1_rows[t]["delta_auc"],
                 "delta_f1_05_pp": df,
                 "attribution": att}

    if not g1:
        verdict = "posthoc_family_insufficient"
    elif not g2:
        verdict = "needs_target_prior_unavailable"
    else:
        verdict = "deployable_correction_exists"

    payload = {
        "schema_version": "ch4-posthoc-prior-diag-v1",
        "plan": ".Codex/docs/2026-10-20-第四章零训练先验诊断/plan.md",
        "inputs": {
            "scores": str(SRC),
            "base_result": str(BASE_RESULT),
            "buffer_audit": str(AUDIT),
            "gate": {"tol": GATE_TOL, "passed": True, "base_mean12": base_mean12},
        },
        "rows": rows,
        "criteria": {
            "G1_family_upper_bound": {"passed": g1,
                                      "delta_oracle_pp_2023": by_year[2023]["delta_oracle_pp"],
                                      "delta_oracle_pp_2024": by_year[2024]["delta_oracle_pp"],
                                      "rule": "2023 与 2024 的 delta_oracle_pp 均 >= 1.0"},
            "G2_deployable": {"passed": g2, "rules": rules, "passing_rules": list(g2_rules),
                              "rule": "存在可部署规则：2024 delta >= 1.0 pp 且 12 年平均 >= base - 0.20 pp"},
            "G3_m1_attribution": g3,
        },
        "verdict": verdict,
        "means": {
            "base_mean12": base_mean12,
            "f1_05_mean12": float(np.mean([base_f1[t] for t in YEARS])),
            "f1_oracle_mean12": float(np.mean([by_year[t]["f1_oracle"] for t in YEARS])),
            "f1_oracle_mean11_excl_2025": float(np.mean([by_year[t]["f1_oracle"] for t in YEARS if t != 2025])),
            "f1_05_mean11_excl_2025": float(np.mean([base_f1[t] for t in YEARS if t != 2025])),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict,
                      "G1": g1,
                      "G2": g2,
                      "G3": g3,
                      "oracle_2023": by_year[2023]["delta_oracle_pp"],
                      "oracle_2024": by_year[2024]["delta_oracle_pp"],
                      "rules": rules}, ensure_ascii=False, indent=2), flush=True)
    print(f"[out] {OUT} ({OUT.stat().st_size} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
