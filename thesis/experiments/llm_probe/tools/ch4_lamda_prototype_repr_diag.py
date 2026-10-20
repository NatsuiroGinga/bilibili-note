#!/usr/bin/env python
"""Path A：在回放构成模型的 128 维表示空间测历史正例原型迁移。

只读已训练的 `replay-model.pt` 与既有预测，不训练。
对每个末期目标年度：
- 历史正例：目标年之前各年度 train 分片的正例，每年度最多 1000 条，取 encoder 128 维表示；
- 原型：L2 归一化后的历史正例均值；
- 测试样本：目标年 test 分片，encoder 表示与原型余弦相似度；
- 与既有多末模型 MLP 分数（preds_replay_{year}.npz）比较：AUC、匹配告警预算下的 F1、融合分数。

判据（Path A，看到读数前冻结）：
- 支持：至少 2 个末期年度的「融合 F1 − MLP F1」≥ +1.0 pp，且原型分数 AUC ≥ 0.70；
- 否决：融合 F1 不高于 MLP，或原型 AUC < 0.60。
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
OUT = RUN / "prototype-repr-diag.json"
YEARS = list(ch3.DOMAIN_YEARS)
TARGETS = [2020, 2021, 2022, 2023, 2024]
CAP_PER_YEAR = 1000


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
    state = torch.load(RUN / "replay-model.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(state)
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
        P = np.concatenate(pos)
        proto = P.mean(axis=0)
        proto /= np.linalg.norm(proto) + 1e-12

        xte, yte = ch3.load_year(target, "test")
        H = feats(xte)
        sim = H @ proto
        z = np.load(RUN / f"preds_replay_{target}.npz")
        mlp = z["y_score"].astype(np.float64)
        yt = z["y_true"].astype(np.int8)
        assert np.array_equal(yt, yte.astype(np.int8))
        comb = 0.5 * rankdata(sim) / len(sim) + 0.5 * rankdata(mlp) / len(mlp)
        n_alert = int((mlp >= ch3.THRESHOLD).sum())
        mlp_f1 = f1_of(yt, (mlp >= ch3.THRESHOLD).astype(np.int8))
        sim_f1 = topn_f1(sim, yt, n_alert)
        comb_f1 = topn_f1(comb, yt, n_alert)
        try:
            auc_sim = float(roc_auc_score(yt, sim))
        except ValueError:
            auc_sim = None
        results.append(
            {
                "year": target,
                "n_test": int(yt.size),
                "n_pos": int((yt == 1).sum()),
                "n_alert_mlp": n_alert,
                "mlp_f1": mlp_f1,
                "proto_only_f1_topn": sim_f1,
                "combined_f1_topn": comb_f1,
                "delta_combined_minus_mlp_pp": (comb_f1 - mlp_f1) * 100,
                "proto_auc": auc_sim,
            }
        )
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)

    support = sum(
        1 for r in results if r["delta_combined_minus_mlp_pp"] >= 1.0 and (r["proto_auc"] or 0) >= 0.70
    )
    falsify = all(r["delta_combined_minus_mlp_pp"] <= 0 for r in results) or all(
        (r["proto_auc"] or 0) < 0.60 for r in results
    )
    verdict = "support" if support >= 2 else ("reject" if falsify else "mixed")
    payload = {
        "schema_version": "ch4-prototype-repr-diag-v1",
        "model": str(RUN / "replay-model.pt"),
        "targets": TARGETS,
        "cap_per_year": CAP_PER_YEAR,
        "results": results,
        "criteria": {
            "n_support_years": support,
            "support": support >= 2,
            "falsify": falsify,
            "verdict": verdict,
        },
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[verdict] {verdict} -> {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
