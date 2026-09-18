#!/usr/bin/env python3
"""LAMDA 双玩家速率约束 v2 逐年 pooled 与配对翻转独立分析（screening_only）。

口径与 2026-09-09-LAMDA缺口修复/analysis/stats-appendix.md 一致：
- pooled 六指标由 2016+2017 current_year 逐样本合并复算；
- 配对翻转用上一冻结模型 next_year 预测→本年度 current_year 预测；
- 输出 JSON 收据与 markdown 表，供交接包与恢复卡引用。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

RUN = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-lamda-20260908/thesis/experiments/llm_probe/"
    "runs/diagnostics/ch3-lamda-dual-player-screening-mps-seed42-v2"
)
OUT = Path(__file__).resolve().parent
ARMS = ["experience_replay", "gap_repair", "dual_player", "gap_repair_dual_player"]
THRESHOLD = 0.5
DEV_YEARS = [2016, 2017]
PREV_MODEL = {2016: 2014, 2017: 2016}


def load_jsonl(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            key = row["sample_identity_sha256"]
            if key in rows:
                raise AssertionError(f"重复身份：{path}")
            rows[key] = row
    return rows


def metrics_of(rows: list[dict]) -> dict:
    labels = np.asarray([r["label"] for r in rows], dtype=np.int64)
    scores = np.asarray([r["score"] for r in rows], dtype=np.float64)
    pred = scores >= THRESHOLD
    tp = int(np.sum(pred & (labels == 1)))
    fp = int(np.sum(pred & (labels == 0)))
    tn = int(np.sum(~pred & (labels == 0)))
    fn = int(np.sum(~pred & (labels == 1)))
    return {
        "n": len(rows),
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "AP": average_precision_score(labels, scores),
        "AUROC": roc_auc_score(labels, scores),
        "F1": tp / (tp + 0.5 * (fp + fn)) if tp else 0.0,
        "FPR": fp / (fp + tn) if (fp + tn) else None,
        "FNR": fn / (fn + tp) if (fn + tp) else None,
        "Brier": float(np.mean((scores - labels) ** 2)),
    }


def per_year_check(arm: str) -> dict:
    """单年复算并对齐工具 metrics 文件，输出最大绝对偏差。"""
    worst = 0.0
    for year in DEV_YEARS:
        rows = list(load_jsonl(RUN / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl").values())
        mine = metrics_of(rows)
        tool = json.load(open(RUN / "metrics" / arm / f"year-{year}.json"))["evaluation"]["current_year"]["metrics"]
        for key in ("AP", "AUROC", "F1", "FPR", "FNR", "Brier"):
            worst = max(worst, abs(float(mine[key]) - float(tool[key])))
    return {"max_abs_deviation_vs_tool": worst}


def transitions(arm: str) -> dict:
    repair_num = repair_den = flip_num = flip_den = fpr_num = benign_den = 0
    for year in DEV_YEARS:
        prev = load_jsonl(RUN / "predictions" / arm / f"trained-through-{PREV_MODEL[year]}" / "next_year.jsonl")
        cur = load_jsonl(RUN / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl")
        assert prev.keys() == cur.keys(), f"配对身份集合不一致：{arm} {year}"
        for key, new in cur.items():
            old_pred = prev[key]["predicted_malicious"]
            label = new["label"]
            assert label == prev[key]["label"]
            if label == 1:
                if not old_pred:
                    repair_den += 1
                    repair_num += int(new["predicted_malicious"])
                else:
                    flip_den += 1
                    flip_num += int(not new["predicted_malicious"])
            else:
                benign_den += 1
                if old_pred is False and new["predicted_malicious"]:
                    fpr_num += 1
    return {
        "malicious_repair": {"num": repair_num, "den": repair_den, "rate": repair_num / repair_den},
        "malicious_negative_flip": {"num": flip_num, "den": flip_den, "rate": flip_num / flip_den},
        "benign_new_false_positive": {"num": fpr_num, "den": benign_den, "rate": fpr_num / benign_den},
    }


def multiplier_diagnostics(arm: str) -> dict:
    out = {}
    for year in DEV_YEARS:
        epochs = json.load(open(RUN / "metrics" / arm / f"year-{year}.json"))["epochs"]
        out[str(year)] = {
            "lambda_benign_max": max(ep["lambda_benign"] for ep in epochs),
            "lambda_malicious_max": max(ep["lambda_malicious"] for ep in epochs),
            "lambda_benign_final": epochs[-1]["lambda_benign"],
            "lambda_malicious_final": epochs[-1]["lambda_malicious"],
            "dual_updates_total": sum(ep["auxiliary"]["dual_updates"] for ep in epochs),
            "repair_candidates_final": epochs[-1]["auxiliary"]["repair_candidates"],
        }
    return out


def main() -> None:
    result: dict = {"arms": {}, "delta_vs_er": {}}
    base = None
    for arm in ARMS:
        rows = []
        for year in DEV_YEARS:
            rows.extend(load_jsonl(RUN / "predictions" / arm / f"trained-through-{year}" / "current_year.jsonl").values())
        entry = {
            "pooled": metrics_of(rows),
            "per_year_check": per_year_check(arm),
            "transitions": transitions(arm),
        }
        if arm in ("dual_player", "gap_repair_dual_player"):
            entry["multipliers"] = multiplier_diagnostics(arm)
        result["arms"][arm] = entry
        if arm == "experience_replay":
            base = entry["pooled"]
    for arm in ARMS[1:]:
        pooled = result["arms"][arm]["pooled"]
        result["delta_vs_er"][arm] = {key: pooled[key] - base[key] for key in ("AP", "AUROC", "F1", "FPR", "FNR", "Brier")}
    (OUT / "v2-independent-analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False)[:400], "...")
    print("OK ->", OUT / "v2-independent-analysis.json")


if __name__ == "__main__":
    main()
