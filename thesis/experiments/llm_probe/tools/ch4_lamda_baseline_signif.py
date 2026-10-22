#!/usr/bin/env python
"""第四章基线对比的配对 bootstrap 显著性（判据冻结于本文件头）。

问题：uniform tabm4 相对三条外部基线（deep4/swa/mcdrop）的 12 年平均 F1 差是否显著。
方法：与 `ch4_lamda_tabm_bootstrap.py` 同一配对方案——每年同一次有放回重采样索引
同时抽取两臂分数（保留样本级相关），B=5000、种子 42、95% 百分位区间。
只读既有制品，不训练；tabm4 vs base 的区间已在 `tabm-bootstrap.json`（CI [1.22,1.87]）。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

W = Path(__file__).resolve().parents[1] / "runs/diagnostics"
YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
B = 5000
SEED = 42


def f1(y: np.ndarray, s: np.ndarray, thr: float = 0.5) -> float:
    p = (s >= thr).astype(int)
    tp = int(((p == 1) & (y == 1)).sum())
    fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum())
    d = 2 * tp + fp + fn
    return 2 * tp / d if d else 0.0


def load(arm: str, src: str) -> dict:
    return {y: np.load(W / src / f"preds_{arm}_{y}.npz") for y in YEARS}


def main() -> int:
    tab = load("tabm4", "ch4-lamda-tabm-pilot")
    arms = {
        "deep4": load("deep4", "ch4-lamda-baselines-pilot"),
        "swa": load("swa", "ch4-lamda-baselines-pilot"),
        "mcdrop": load("mcdrop", "ch4-lamda-baselines-pilot"),
    }
    rng = np.random.default_rng(SEED)
    out: dict = {"schema_version": "ch4-baseline-signif-v1", "B": B, "seed": SEED,
                 "pairing": "每年同索引同时抽两臂（配对）", "rows": {}}
    for arm, D in arms.items():
        plug = float(np.mean([f1(D[y]["y_true"].astype(np.int8), D[y]["y_score"].astype(np.float64)) for y in YEARS]))
        plug_tab = float(np.mean([f1(tab[y]["y_true"].astype(np.int8), tab[y]["y_score"].astype(np.float64)) for y in YEARS]))
        deltas = np.empty(B)
        for b in range(B):
            per = []
            for y in YEARS:
                n = D[y]["y_true"].shape[0]
                ii = rng.integers(0, n, n)
                yi = D[y]["y_true"].astype(np.int8)
                sa = tab[y]["y_score"].astype(np.float64)[ii]
                sb = D[y]["y_score"].astype(np.float64)[ii]
                per.append(f1(yi, sa) - f1(yi, sb))   # tabm4 − 基线，逐年
            deltas[b] = np.mean(per) * 100             # 12 年等权平均，单位 pp
        lo, hi = np.percentile(deltas, [2.5, 97.5])
        out["rows"][arm] = {
            "plugin_diff_pp": (plug_tab - plug) * 100,
            "boot_mean_pp": float(np.mean(deltas)),
            "ci95_pp": [float(lo), float(hi)],
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
        }
        print(arm, out["rows"][arm], flush=True)
    dst = W / "ch4-lamda-baselines-pilot/baseline-signif.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("written:", dst, dst.stat().st_size, "bytes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
