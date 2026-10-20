#!/usr/bin/env python
"""第四章效果臂先导：LSUV 数据依赖初始化标定 vs base。

只回答一个问题：把默认初始化替换为按真实批次逐层标定到单位方差的 LSUV
（Mishkin & Matas, ICLR 2016），能否改善 12 年平均 F1？

## 冻结判据（研究问题卡 §十，在看到读数前）

支持（三条同时）：
1. lsuv − base ≥ +0.50 pp（12 年平均 F1）；
2. lsuv ≥ he 臂（0.8205）+ 0.30 pp，即 ≥ 0.8235；
3. 2013／2014 的 F1 ≥ base 同年 − 0.20 pp。
证伪（任一）：lsuv ≤ he；或 lsuv − base ≤ +0.10 pp；或 2013/2014 恶化 > 0.50 pp。

## LSUV 实现约束

- 只在模型创建时做一次，用 2013 训练分片的**确定性切片** `X[0:2048]`（不洗牌、
  不消耗任何随机流——`rng`/`buf_rng` 与 base 逐位一致）。
- 逐 Linear 层前向该切片，实测输出 std，`w /= std`、`b /= std`，迭代至多 10 次
  直到 std ∈ [0.9, 1.1]；ReLU 层按 LSUV 原文以输出 std（非 sqrt(2) 补偿）标定。
- 评价/训练路径零改动。

## 复现门

base 末年 12 年平均 F1 必须等于 `0.8169830287163194`（容差 1e-6）。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

SEED = ch3.SEED
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics/ch4-lamda-lsuv-pilot"
GATE_REF = 0.8169830287163194
GATE_TOL = 1e-6
HE_REF = 0.8205
ARMS = ("base", "lsuv")
LSUV_BATCH = 2048
LSUV_ITERS = 10
LSUV_TOL = (0.9, 1.1)


def lsuv_calibrate(model: nn.Module, x_cal: np.ndarray) -> list[dict]:
    """按 LSUV 原文逐层把 Linear 输出标定到单位方差。返回逐层记录。"""
    linears = [m for m in model.modules() if isinstance(m, nn.Linear)]
    records: list[dict] = []
    xb = torch.from_numpy(x_cal[:LSUV_BATCH].astype(np.float32)).to(DEVICE)
    for li, layer in enumerate(linears):
        with torch.no_grad():
            for _ in range(LSUV_ITERS):
                # 前向到该层为止（含该层，不含其后的 ReLU/Sigmoid）
                out = xb
                for m in model.encoder if layer in model.encoder.modules() else model.classifier:
                    out = m(out)
                    if m is layer:
                        break
                std = float(out.std())
                if LSUV_TOL[0] <= std <= LSUV_TOL[1]:
                    break
                factor = 1.0 / max(std, 1e-12)
                layer.weight.data.mul_(factor)
                if layer.bias is not None:
                    layer.bias.data.mul_(factor)
        records.append(
            {
                "layer_index": li,
                "layer": str(layer),
                "final_output_std": std,
                "iters_used": _ + 1 if "_" in dir() else None,
            }
        )
        print(f"[lsuv] layer {li}: std={std:.6f}", flush=True)
    return records


def run_arm(arm: str) -> int:
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    print(f"[arm] {arm} device={DEVICE.type}", flush=True)

    years = list(ch3.DOMAIN_YEARS)
    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)

    model: nn.Module | None = None
    lsuv_records: list[dict] = []
    preds: dict[int, dict] = {}
    t0 = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
            if arm == "lsuv":
                lsuv_records = lsuv_calibrate(model, x_curr)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,}", flush=True)
        parts, _ = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                         ch3.OFFICIAL_LR, DEVICE, rng)
        for ty in years[: idx + 1]:
            xt, yt = ch3.load_year(ty, "test")
            ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
        print(f"[{year}] done ({time.time() - t0:.0f}s)", flush=True)

    last = []
    for ty in years:
        p = (preds[ty]["y_score"] >= ch3.THRESHOLD).astype(int)
        yt = preds[ty]["y_true"]
        tp = int(((p == 1) & (yt == 1)).sum())
        fp = int(((p == 1) & (yt == 0)).sum())
        fn = int(((p == 0) & (yt == 1)).sum())
        d = 2 * tp + fp + fn
        f1 = 2 * tp / d if d else 0.0
        last.append({"year": ty, "f1": float(f1)})
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=preds[ty]["y_true"], y_score=preds[ty]["y_score"],
                            threshold=np.float32(ch3.THRESHOLD))
    mean_f1 = float(np.mean([r["f1"] for r in last]))
    per_year = {str(r["year"]): r["f1"] for r in last}
    print(f"=== {arm}: 12y mean f1 = {mean_f1:.10f} ===", flush=True)

    payload = {"arm": arm, "mean_f1": mean_f1, "per_year": per_year,
               "lsuv_records": lsuv_records, "wall_seconds": round(time.time() - t0, 1)}
    if arm == "base":
        ok = abs(mean_f1 - GATE_REF) <= GATE_TOL
        payload["gate"] = {"expected": GATE_REF, "observed": mean_f1,
                           "abs_delta": abs(mean_f1 - GATE_REF), "passed": ok}
        print(f"[gate] {'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            return 1
    (RUN_DIR / f"{arm}-result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
