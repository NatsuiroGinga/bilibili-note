#!/usr/bin/env python3
"""E1（修正版）：尾锚假设的零训练 oracle 检验——修复外溢是否集中于冻结高分良性尾。

修正（响应网页审查报告 §2.4/§4-诊断1/§5.1 与本地 E1 v0 的 clip 方向 bug）：
  1. 反事实参照从"上一模型判定"改为"ER 同运行判定"（旧版会把被修复的旧 FP 再钉回错误）；
  2. 尾集两种定义：T_all = 全部良性按 θ⁻ 分数 TopK；T_keep = θ⁻ 判对（score<0.5）良性按其分数 TopK；
  3. 主指标：n₊（ER 判对→缺口判错 的良性）落入尾集的覆盖率随 K 曲线 + oracle 裁剪后 FPR
     （把尾集内样本预测强制改回 ER 判定 = 保护完美生效上界）。
判读（先冻结）：T_keep 在 K ≤ 当年已登记良性参考预算内覆盖率 ≥50% 且裁剪后 FPR ≤ ER
→ 尾锚有作用面；否则优先解释为覆盖不足（报告 §8.5 行 4），尾锚预期降级、转诊断2。
θ⁻ 为缺口臂自己的上一冻结模型（与尾锚臂将实际可用的冻结评分器同构）。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

RUN = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/thesis/experiments/llm_probe/"
    "runs/diagnostics/ch3-lamda-dual-player-screening-mps-seed42-v2"
)
THRESHOLD = 0.5
YEARS = {2016: 2014, 2017: 2016}
TARGET_ARMS = ["gap_repair", "gap_repair_dual_player"]
KS = [100, 275, 500, 1000, 2000]
_CACHE: dict[tuple[str, int, str], dict[str, dict]] = {}


def load(arm: str, through: int, surface: str) -> dict[str, dict]:
    key = (arm, through, surface)
    if key not in _CACHE:
        path = RUN / "predictions" / arm / f"trained-through-{through}" / f"{surface}.jsonl"
        _CACHE[key] = {
            (row := json.loads(line))["sample_identity_sha256"]: row
            for line in path.open(encoding="utf-8")
        }
    return _CACHE[key]


def probe(arm: str, year: int) -> dict:
    cur = load(arm, year, "current_year")
    prev = load(arm, YEARS[year], "next_year")
    er = load("experience_replay", year, "current_year")
    keys = sorted(cur)
    assert set(prev) == set(er) == set(keys)
    label = np.asarray([cur[k]["label"] for k in keys], dtype=bool)
    arm_pred = np.asarray([cur[k]["predicted_malicious"] for k in keys])
    er_pred = np.asarray([er[k]["predicted_malicious"] for k in keys])
    prev_score = np.asarray([prev[k]["score"] for k in keys], dtype=np.float64)
    benign = ~label
    # n₊：ER 判对 → 本臂判错的良性；n₋：反向
    n_plus_idx = np.flatnonzero(benign & ~er_pred & arm_pred)
    n_minus = int(np.sum(benign & er_pred & ~arm_pred))
    er_fpr = float(np.sum(benign & er_pred) / np.sum(benign))
    out: dict = {
        "n_plus": int(len(n_plus_idx)),
        "n_minus": n_minus,
        "net_fp_delta": int(len(n_plus_idx)) - n_minus,
        "er_fpr": round(er_fpr, 6),
        "arm_fp_total": int(np.sum(benign & arm_pred)),
        "defs": {},
    }
    b_idx = np.flatnonzero(benign)
    keep_idx = b_idx[prev_score[b_idx] < THRESHOLD]  # θ⁻ 判对的良性
    for name, pool in (("T_all", b_idx), ("T_keep", keep_idx)):
        order = pool[np.argsort(-prev_score[pool])]
        rows = {}
        for K in KS:
            top = set(order[:K].tolist())
            cover = float(np.mean([i in top for i in n_plus_idx.tolist()])) if len(n_plus_idx) else None
            clipped = arm_pred.copy()
            for i in top:
                clipped[i] = er_pred[i]  # oracle：尾集内钉回 ER 判定
            fpr = float(np.sum(benign & clipped) / np.sum(benign))
            rows[str(K)] = {"coverage_n_plus": round(cover, 4) if cover is not None else None,
                            "fpr_after_oracle_clip": round(fpr, 6),
                            "passes_ER_FPR": fpr <= er_fpr}
        out["defs"][name] = rows
    return out


def main() -> None:
    result = {"note": "E1 修正版：clip→ER 参照；T_all/T_keep 双定义", "arms": {}}
    for arm in TARGET_ARMS:
        result["arms"][arm] = {}
        for year in YEARS:
            d = probe(arm, year)
            result["arms"][arm][str(year)] = d
            print(f"== {arm} {year} == n+={d['n_plus']} n-={d['n_minus']} ER_FPR={d['er_fpr']}")
            for name, rows in d["defs"].items():
                line = "  ".join(f"K={k}:cov={v['coverage_n_plus']},clipFPR={v['fpr_after_oracle_clip']}"
                                 f"{'✓' if v['passes_ER_FPR'] else '✗'}" for k, v in rows.items())
                print(f"  {name:>6}: {line}")
    path = Path(__file__).resolve().parent / "oracle-tail-clip.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK ->", path)


if __name__ == "__main__":
    main()
