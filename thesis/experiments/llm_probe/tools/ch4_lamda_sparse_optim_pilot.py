#!/usr/bin/env python
"""第四章训练方法探针：稀疏感知优化器（Adagrad）vs 协议 SGD。

数据是 4561 维稀疏二值特征（激活率 0.27–1.58%）。协议用稠密 SGD（lr=0.01），
每步对全部坐标做同一更新；Adagrad 按坐标累积二阶矩，给稀有/新激活坐标更大的
有效步长——这是**训练方法**层面的改动，不是架构或决策层。

三臂（同协议、同回放构成、同种子 42）：
- base：SGD lr=0.01（复现门 0.8169830287163194）
- adagrad001：Adagrad lr=0.01
- adagrad01：Adagrad lr=0.1

冻结判据（看到读数前）：
- 支持：任一 Adagrad 臂 12 年平均 F1 − base ≥ +0.50 pp，且 2018–2024 中不低于 base−0.20 pp 的年度数 ≥ 6；
- 否决：全部 Adagrad 臂 − base ≤ +0.10 pp。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402
from ch4_lamda_training_process_2x2 import build_parts, train_epochs_with_optimizer  # noqa: E402

SEED = ch3.SEED
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics/ch4-lamda-sparse-optim-pilot"
GATE_REF = 0.8169830287163194
ARMS = ("base", "adagrad001", "adagrad01")


def builder(arm: str):
    if arm == "base":
        return lambda p: torch.optim.SGD(p, lr=0.01, momentum=0.9, weight_decay=1e-6)
    lr = 0.01 if arm == "adagrad001" else 0.1
    return lambda p: torch.optim.Adagrad(p, lr=lr, weight_decay=1e-6)


def f1_of(yt: np.ndarray, score: np.ndarray) -> float:
    p = (score >= ch3.THRESHOLD).astype(int)
    yt = yt.astype(int)
    tp = int(((p == 1) & (yt == 1)).sum())
    fp = int(((p == 1) & (yt == 0)).sum())
    fn = int(((p == 0) & (yt == 1)).sum())
    d = 2 * tp + fp + fn
    return float(2 * tp / d) if d else 0.0


def run_arm(arm: str) -> int:
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    years = list(ch3.DOMAIN_YEARS)
    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)
    model = None
    preds = {}
    t0 = time.time()
    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,}", flush=True)
        parts, _ = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        train_epochs_with_optimizer(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                                    DEVICE, rng, builder(arm))
        print(f"[{year}] trained ({time.time() - t0:.0f}s)", flush=True)
        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
                del xt, yt
    backward = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"]) for ty in years}
    mean_f1 = float(np.mean(list(backward.values())))
    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(ch3.THRESHOLD))
    payload = {"arm": arm, "mean_f1": mean_f1, "backward_f1": backward,
               "wall_seconds": round(time.time() - t0, 1)}
    if arm == "base":
        payload["gate"] = {"expected": GATE_REF, "observed": mean_f1,
                           "abs_delta": abs(mean_f1 - GATE_REF),
                           "passed": abs(mean_f1 - GATE_REF) <= 1e-6}
        print(f"[gate] {'PASS' if payload['gate']['passed'] else 'FAIL'}", flush=True)
    (RUN_DIR / f"{arm}-result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"=== {arm}: 12y mean={mean_f1:.10f} ===", flush=True)
    return 0


def main() -> int:
    arm = sys.argv[1] if len(sys.argv) > 1 else ""
    if arm not in ARMS:
        print(f"usage: {sys.argv[0]} {'|'.join(ARMS)}")
        return 2
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return run_arm(arm)


if __name__ == "__main__":
    raise SystemExit(main())
