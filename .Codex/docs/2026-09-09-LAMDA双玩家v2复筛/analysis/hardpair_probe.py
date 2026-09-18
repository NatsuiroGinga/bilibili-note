#!/usr/bin/env python3
"""零训练病灶探针：ER 漏判恶意与高分良性的硬对邻接结构。

目的：检验"修复漏判必然抬良性误报"的几何成因假设。
可证伪点：若漏判恶意分数大多位于良性分布低位（与高分良性可分），
则方向冲突假设被反驳，问题在实现而非分数空间结构。
输入：ch3-lamda-dual-player-screening-mps-seed42-v2 的 ER 臂逐样本预测。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

RUN = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/thesis/experiments/llm_probe/"
    "runs/diagnostics/ch3-lamda-dual-player-screening-mps-seed42-v2"
)
ARMS = ["experience_replay", "gap_repair"]
THRESHOLD = 0.5
YEARS = [2016, 2017]


def load(arm: str, year: int, surface: str = "current_year") -> list[dict]:
    path = RUN / "predictions" / arm / f"trained-through-{year}" / f"{surface}.jsonl"
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def probe(arm: str) -> dict:
    out = {}
    for year in YEARS:
        rows = load(arm, year)
        scores = np.asarray([r["score"] for r in rows])
        labels = np.asarray([r["label"] for r in rows])
        mal = scores[labels == 1]
        ben = scores[labels == 0]
        fn = mal[mal < THRESHOLD]
        fp = ben[ben >= THRESHOLD]
        # 硬对：漏判恶意 vs 全部良性；漏判恶意分数超过多少良性样本
        hard_pair_auc = roc_auc_score(
            np.r_[np.ones(len(fn)), np.zeros(len(ben))], np.r_[fn, ben]
        ) if len(fn) else None
        below = {
            q: float(np.mean(fn >= np.quantile(ben, q / 100))) if len(fn) else None
            for q in (50, 90, 99)
        }
        # 把 FN 全部拉回 0.5 以上需要的阈值移动，与其代价（新增 FP）
        if len(fn):
            new_fp_at_fn_threshold = int(np.sum(ben >= fn.min()))
            new_fp_fixing_half = int(np.sum(ben >= np.quantile(fn, 0.5)))
        else:
            new_fp_at_fn_threshold = new_fp_fixing_half = -1
        out[str(year)] = {
            "n": len(rows),
            "fn_n": int(len(fn)),
            "fp_n": int(len(fp)),
            "fn_score_quantiles": [round(float(x), 4) for x in np.quantile(fn, [0.1, 0.5, 0.9])] if len(fn) else None,
            "benign_quantiles": [round(float(x), 4) for x in np.quantile(ben, [0.5, 0.9, 0.99])],
            "fn_above_benign_median": below[50],
            "fn_above_benign_p90": below[90],
            "fn_above_benign_p99": below[99],
            "hard_pair_auc": hard_pair_auc,
            "new_fp_if_threshold_to_lowest_fn": new_fp_at_fn_threshold,
            "new_fp_if_threshold_fixes_half_fn": new_fp_fixing_half,
        }
    return out


def main() -> None:
    result = {arm: probe(arm) for arm in ARMS}
    # gap 臂新增误报的出身：其 FP 有多少是 ER 臂判对的良性（分数空间挤压证据）
    er_ben = {y: {r["sample_identity_sha256"]: r for r in load("experience_replay", y) if r["label"] == 0} for y in YEARS}
    gap_new_fp_origin = {}
    for y in YEARS:
        gap_fp = [r for r in load("gap_repair", y) if r["label"] == 0 and r["predicted_malicious"]]
        prev_wrong = sum(1 for r in gap_fp if er_ben[y][r["sample_identity_sha256"]]["predicted_malicious"])
        gap_new_fp_origin[str(y)] = {
            "gap_fp_total": len(gap_fp),
            "fp_already_fp_in_er": prev_wrong,
            "fp_new_by_gap_only": len(gap_fp) - prev_wrong,
        }
    result["gap_fp_origin_vs_er"] = gap_new_fp_origin
    path = RUN.parent if False else Path(__file__).resolve().parent / "hardpair-probe.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
