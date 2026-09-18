#!/usr/bin/env python3
"""课程学习前置统计（零训练）：修复难度分桶 × 修复率 × 评分穿越代价。

定义：
  R_t = {y=1, z_θ⁻(x) < 0.5}（缺口臂自身 θ⁻ 的当年测试预测中旧模型漏判恶意）；
  难度 = d_i = 0.5 − z⁻_score(x_i)，按当年分位数切五桶（桶1=贴边最浅）；
  修复率 = 该桶中缺口臂 current 预测判对的比例；
  穿越代价 = 把该样本抬到 0.5+ 需越过的当年测试良性 θ⁻ 分数的个数
             （同源良性密度代理，非训练侧精确值，判读时披露）。
判据（先于结果冻结）：桶5/桶1 平均穿越代价比 ≥2 → 课程有病灶依据；
<1.5 → 摘除课程；1.5~2 → 仅作消融轴。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

RUN = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/thesis/experiments/llm_probe/"
    "runs/diagnostics/ch3-lamda-dual-player-screening-mps-seed42-v2"
)
YEARS = {2016: 2014, 2017: 2016}
ARM = "gap_repair"
N_BUCKETS = 5


def load(arm: str, through: int, surface: str) -> list[dict]:
    path = RUN / "predictions" / arm / f"trained-through-{through}" / f"{surface}.jsonl"
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def probe(year: int) -> dict:
    prev = {r["sample_identity_sha256"]: r for r in load(ARM, YEARS[year], "next_year")}
    cur = load(ARM, year, "current_year")
    fn_rows = [r for r in cur if r["label"] == 1 and not prev[r["sample_identity_sha256"]]["predicted_malicious"]]
    ben_scores = np.sort(
        np.asarray(
            [prev[r["sample_identity_sha256"]]["score"] for r in cur if r["label"] == 0],
            dtype=np.float64,
        )
    )
    diffs = np.asarray([0.5 - prev[r["sample_identity_sha256"]]["score"] for r in fn_rows])
    fixed = np.asarray([r["predicted_malicious"] for r in fn_rows], dtype=bool)
    edges = np.quantile(diffs, np.linspace(0, 1, N_BUCKETS + 1))
    out = {}
    for b in range(N_BUCKETS):
        lo, hi = edges[b], edges[b + 1]
        sel = (diffs >= lo) & (diffs <= hi if b == N_BUCKETS - 1 else diffs < hi)
        bucket_diff = diffs[sel]
        # 穿越代价：每个样本从 0.5−d 抬到 0.5+ 越过的良个数 = #{ben ∈ (0.5−d, 0.5]}
        low = np.clip(0.5 - bucket_diff, 0, None)
        crossed = np.searchsorted(ben_scores, 0.5, side="right") - np.searchsorted(ben_scores, low, side="left")
        out[f"bucket{b + 1}"] = {
            "n": int(sel.sum()),
            "score_diff_range": [round(float(bucket_diff.min()), 4), round(float(bucket_diff.max()), 4)] if sel.any() else None,
            "repair_rate": round(float(fixed[sel].mean()), 4) if sel.any() else None,
            "crossed_benign_median": float(np.median(crossed)) if len(crossed) else None,
            "crossed_benign_mean": round(float(crossed.mean()), 2) if len(crossed) else None,
        }
    r1 = out["bucket1"]["crossed_benign_mean"]
    r5 = out[f"bucket{N_BUCKETS}"]["crossed_benign_mean"]
    out["cost_ratio_b5_over_b1"] = round(r5 / r1, 2) if r1 else None
    return out


def main() -> None:
    result = {"arm": ARM, "surface_note": "测试良性 θ⁻ 分数为同源良性密度代理；样本级 FP 归因不可得", "years": {}}
    for y in YEARS:
        result["years"][str(y)] = probe(y)
        print(y, json.dumps(result["years"][str(y)], ensure_ascii=False, indent=1))
    path = Path(__file__).resolve().parent / "curriculum-buckets.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK ->", path)


if __name__ == "__main__":
    main()
