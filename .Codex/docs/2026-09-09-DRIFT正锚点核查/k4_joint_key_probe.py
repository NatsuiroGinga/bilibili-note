#!/usr/bin/env python3
"""K4 联合表示键补测（零前向，消费 T17/T18 特征缓存）。

背景：正锚点主裁决（低阶键）问二 net=-207 不通过；本补测检验报告的条件键
K4（字符/子词表示级联合特征）能否把 override 掰成 net>0。
K4 特征（从缓存 tok_feat/char_feat 直接计算，零前向）：
  h_c 与 h_s 均为 512 维（max 256 + mean 256）；K4 = [cos(h_c,h_s),
  |h_c-h_s| 的 L2 范数, 逐元素积的 L2 范数]。
判据（冻结，对齐主探针）：T17 cell 表 → T18 验证，coverage>0 且 net>0。
主对照：低阶键（K1/K2/K3）在同一脚本内重跑（数值对齐主探针 result）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
import pyarrow.parquet as pq

ROOT = Path("/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/thesis/experiments/llm_probe")
sys.path.insert(0, str(ROOT / "tools"))
DATA = ROOT / "runs/data-raw/drift-dga-2026-rev-3b31077020cd1c013d0a75cad51042a2327c4521"
OUT = Path(__file__).resolve().parent


def cos_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    num = (a * b).sum(axis=1)
    den = np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-12
    return (num / den).astype(np.float32)


def load_year(year: str, limit: int | None = None) -> dict:
    cache = Path(f"/tmp/drift-anchor-t17-features-{300000 if limit is None else 2*limit}.npz")
    z = np.load(cache)
    tok, char = z["tok"], z["char"]
    tb = pq.read_table(DATA / "DRIFT_input_eSLD" / f"{year}_benign_val.parquet").to_pylist()
    td = pq.read_table(DATA / "DRIFT_input_eSLD" / f"{year}_dga_val.parquet").to_pylist()
    if limit:
        tb, td = tb[:limit], td[:limit]
    labels = np.asarray([int(r["label"]) for r in tb + td], dtype=np.int64)
    labels01 = labels == 1
    n = len(labels)
    assert tok.shape[0] == n == char.shape[0], (tok.shape, n)
    # 中和均值：与主探针同源——T17 缓存特征的合并均值（类无关）
    tok_mean = tok.mean(axis=0, dtype=np.float64).astype(np.float32)
    char_mean = char.mean(axis=0, dtype=np.float64).astype(np.float32)
    return {"tok": tok, "char": char, "labels01": labels01, "n": n, "year": year,
            "tok_mean": tok_mean, "char_mean": char_mean}


def build_keys(d: dict, use_k4: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """复用主探针 cell 定义；use_k4 时叠 K4 联合键分位箱。"""
    import torch

    import ch3_drift_official_branch_conflict_diagnostic as diag

    model = _get_model()
    probs = diag.probabilities(
        model,
        d["tok"],
        d["char"],
        d["tok_mean"],
        d["char_mean"],
        torch.device("mps"),
        8192,
    )
    fusion = probs["static_fusion"]
    pred = fusion >= 0.5
    pred_c = probs["char_counterfactual"] >= 0.5
    pred_s = probs["subword_counterfactual"] >= 0.5
    conf_c = np.abs(probs["char_counterfactual"] - 0.5)
    conf_s = np.abs(probs["subword_counterfactual"] - 0.5)
    labels01 = d["labels01"]
    wrong = pred != labels01
    k1 = (pred.astype(int) * 4) + (pred_c.astype(int) * 2) + pred_s.astype(int)
    k2 = (conf_c > conf_s).astype(int)
    diff = np.abs(probs["char_counterfactual"] - probs["subword_counterfactual"])
    if use_k4:
        cos = cos_rows(d["tok"][:, :512], d["char"][:, :512])
        l2_diff = np.linalg.norm(d["tok"] - d["char"], axis=1).astype(np.float32)
        joint = np.sqrt(np.abs(np.minimum(l2_diff, 100.0)))  # 压缩尺度
        if d["year"] == "T17":
            _EDGES["k3"] = np.quantile(diff, [0.25, 0.5, 0.75])
            _EDGES["k4"] = np.quantile(joint, [0.25, 0.5, 0.75])
        k4 = np.digitize(joint, _EDGES["k4"])
        cell = ((k1 * 8) + (k2 * 4) + np.digitize(diff, _EDGES["k3"])) * 4 + k4
    else:
        if d["year"] == "T17":
            _EDGES["k3"] = np.quantile(diff, [0.25, 0.5, 0.75])
        cell = (k1 * 8) + (k2 * 4) + np.digitize(diff, _EDGES["k3"])
    return cell, wrong, {"fusion": fusion, "pred": pred, "pred_c": pred_c, "pred_s": pred_s, "labels01": labels01, "conf_c": conf_c, "conf_s": conf_s}


_MODEL = None
_EDGES: dict = {}  # T17 拟合、T18 复用的分箱边界（跨年一致性）


def _get_model():
    global _MODEL
    if _MODEL is None:
        import ch3_drift_official_checkpoint_t17_eval as official

        _MODEL = official.load_model(REF, CKPT, torch.device("mps"))
    return _MODEL


REF = ROOT / "runs/source-snapshots/2026-DSN-DRIFT-e20d1fdf56c623993966c6786f61c01f91dec6d2"
CKPT = ROOT / "runs/models/drift-official-dsn2026/finetuning.pt"


def two_question(a: dict, b: dict, cell_a: np.ndarray, cell_b: np.ndarray, aux_a: dict, aux_b: dict) -> dict:
    cells = np.unique(cell_a[(aux_a["pred_c"] == aux_a["labels01"]) ^ (aux_a["pred_s"] == aux_a["labels01"])])
    u17 = {}
    for c in cells:
        m = cell_a == c
        if m.sum() < 50:
            continue
        r_c = int((m & a["wrong"] & (aux_a["pred_c"] == aux_a["labels01"])).sum())
        i_c = int((m & ~a["wrong"] & (aux_a["pred_c"] != aux_a["fusion"])).sum())
        r_s = int((m & a["wrong"] & (aux_a["pred_s"] == aux_a["labels01"])).sum())
        i_s = int((m & ~a["wrong"] & (aux_a["pred_s"] != aux_a["fusion"])).sum())
        u17[int(c)] = {"u_c": r_c - i_c, "u_s": r_s - i_s}
    cov = resc = ind = 0
    for c, u in u17.items():
        m = cell_b == c
        if not m.any():
            continue
        best = max(("u_c", "u_s"), key=lambda k: u[k])
        if u[best] <= 0:
            continue
        rec = aux_b["pred_c"] if best == "u_c" else aux_b["pred_s"]
        use = m & (rec != aux_b["fusion"])
        cov += int(use.sum())
        resc += int((use & (rec == aux_b["labels01"])).sum())
        ind += int((use & (rec != aux_b["labels01"])).sum())
    return {"coverage": cov, "rescued": resc, "induced": ind, "net": resc - ind}


def main(limit: int | None = None) -> None:
    results: dict = {}
    for use_k4, name in ((False, "low_order_keys"), (True, "k4_joint_keys")):
        a = load_year("T17", limit)
        b = load_year("T18", limit)
        a["wrong"] = b["wrong"] = None  # 占位，build_keys 后填
        cell_a, wrong_a, aux_a = build_keys(a, use_k4)
        cell_b, wrong_b, aux_b = build_keys(b, use_k4)
        a["wrong"], b["wrong"] = wrong_a, wrong_b
        r = two_question(a, b, cell_a, cell_b, aux_a, aux_b)
        r["criteria_pass"] = bool(r["coverage"] > 0 and r["net"] > 0)
        results[name] = r
        print(name, json.dumps(r, ensure_ascii=False), flush=True)
    out = OUT / ("k4-result-DRYRUN.json" if limit else "k4-result.json")
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OK ->", out)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", type=int, default=None)
    main(p.parse_args().dry_run)
