#!/usr/bin/env python
"""架构探针 #2：冻结 MLP 末层表征的 kNN 头（零训练）。

在回放构成模型的 128 维 encoder 表示上，用历史正例构造 kNN 头：
- 对每个目标年，历史正例（目标年之前各年 train 正例，每年最多 1000）取表示；
- 测试样本与全部历史正例的余弦相似度，取 top-k 均值作为 kNN 分数；
- k ∈ {16, 64}；与 MLP 分数（preds_replay_{year}.npz）做 rank 融合；
- 在匹配 MLP 告警预算下比较 F1。

预冻结判据（看到读数前）：
- 支持：至少 2 个末期年度「融合 F1 − MLP F1」≥ +1.0 pp，且对应 kNN AUC ≥ 0.70；
- 否决：所有年度融合 F1 ≤ MLP F1，或所有 kNN AUC < 0.60。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
RUN = Path(__file__).resolve().parents[1] / "runs/diagnostics/ch4-lamda-inversion-pilot"
OUT = RUN / "knn-head-diag.json"
YEARS = list(ch3.DOMAIN_YEARS)
TARGETS = [2020, 2021, 2022, 2023, 2024]
CAP_PER_YEAR = 1000
KS = (16, 64)


def f1_of(y: np.ndarray, p: np.ndarray) -> float:
    tp = int(((p == 1) & (y == 1)).sum())
    fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum())
    d = 2 * tp + fp + fn
    return float(2 * tp / d) if d else 0.0


def topn_f1(score: np.ndarray, y: np.ndarray, n: int) -> float:
    thr = np.sort(score)[-n] if n > 0 else np.inf
    return f1_of(y, (score >= thr).astype(np.int8))


def main() -> int:
    model = ch3.ChenEncoderMLP(4561).to(DEVICE)
    model.load_state_dict(torch.load(RUN / "replay-model.pt", map_location="cpu", weights_only=True))
    model.eval()

    def feats(x: np.ndarray) -> np.ndarray:
        outs = []
        with torch.no_grad():
            for s in range(0, x.shape[0], 2048):
                xb = torch.from_numpy(x[s : s + 2048].astype(np.float32)).to(DEVICE)
                outs.append(model.encoder(xb).cpu().numpy())
        h = np.concatenate(outs)
        return h / (np.linalg.norm(h, axis=1, keepdims=True) + 1e-12)

    results = []
    for target in TARGETS:
        pos = []
        for y in [yy for yy in YEARS if yy < target]:
            x, yv = ch3.load_year(y, "train")
            idx = np.flatnonzero(yv == 1)
            if idx.size > CAP_PER_YEAR:
                idx = np.random.default_rng(42).choice(idx, CAP_PER_YEAR, replace=False)
            pos.append(feats(x[idx]))
            del x, yv
        P = np.concatenate(pos)  # (m, 128)
        xte, yte = ch3.load_year(target, "test")
        H = feats(xte)
        z = np.load(RUN / f"preds_replay_{target}.npz")
        mlp = z["y_score"].astype(np.float64)
        yt = z["y_true"].astype(np.int8)
        assert np.array_equal(yt, yte.astype(np.int8))
        n_alert = int((mlp >= ch3.THRESHOLD).sum())
        mlp_f1 = f1_of(yt, (mlp >= ch3.THRESHOLD).astype(np.int8))

        # chunked similarity to avoid an (n_test, m_pos) dense blow-up
        sims = {k: np.empty(H.shape[0], dtype=np.float64) for k in KS}
        for s in range(0, H.shape[0], 2048):
            S = H[s : s + 2048] @ P.T
            kk = min(max(KS), S.shape[1])
            part = np.partition(S, -kk, axis=1)[:, -kk:]
            for k in KS:
                sims[k][s : s + 2048] = part[:, -min(k, kk) :].mean(axis=1)

        row = {"year": target, "n_test": int(yt.size), "n_pos": int((yt == 1).sum()),
               "n_alert_mlp": n_alert, "mlp_f1": mlp_f1}
        for k in KS:
            sim = sims[k]
            comb = 0.5 * rankdata(sim) / len(sim) + 0.5 * rankdata(mlp) / len(mlp)
            try:
                auc = float(roc_auc_score(yt, sim))
            except ValueError:
                auc = None
            f1c = topn_f1(comb, yt, n_alert)
            row[f"knn{k}_auc"] = auc
            row[f"combined{k}_f1_topn"] = f1c
            row[f"delta{k}_combined_minus_mlp_pp"] = (f1c - mlp_f1) * 100
        results.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)

    support = 0
    for r in results:
        for k in KS:
            if r[f"delta{k}_combined_minus_mlp_pp"] >= 1.0 and (r[f"knn{k}_auc"] or 0) >= 0.70:
                support += 1
                break
    falsify = all(
        max(r[f"delta{k}_combined_minus_mlp_pp"] for k in KS) <= 0 for r in results
    ) or all((r[f"knn{k}_auc"] or 0) < 0.60 for r in results for k in KS)
    verdict = "support" if support >= 2 else ("reject" if falsify else "mixed")
    payload = {
        "schema_version": "ch4-knn-head-diag-v1",
        "model": str(RUN / "replay-model.pt"),
        "targets": TARGETS,
        "cap_per_year": CAP_PER_YEAR,
        "ks": list(KS),
        "results": results,
        "criteria": {"k_support_years": support, "support": support >= 2,
                     "falsify": falsify, "verdict": verdict},
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[verdict] {verdict} -> {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
