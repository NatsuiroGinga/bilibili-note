#!/usr/bin/env python
"""第四章倒置决策先导：可塑性方法（年度头适配）vs 回放构成。

四臂（同协议、同种子 42）：
- naive：全参数年度微调，无回放（官方朴素基线）
- head：冻结 encoder，只训练 classifier（年度头适配＝可塑性方法）
- replay：全参数年度微调 + BSQ-DWR 回放构成（现第三章）
- head_replay：冻结 encoder + BSQ-DWR 回放构成（倒置方案的新第四章修复）

记录：
1. 每个年度训练后，当前年度测试分片的 F1（可塑性）；
2. 末年模型对 12 个测试年度的 backward F1（保持）；
3. 末年逐样本预测；replay 臂保存模型状态供原型诊断复用。

判据见 thesis/methods/第四章-倒置决策判据.md（在看到读数前冻结）。
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
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

SEED = ch3.SEED
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics/ch4-lamda-inversion-pilot"
ARMS = ("naive", "head", "replay", "head_replay")
HEAD_ARMS = ("head", "head_replay")
REPLAY_ARMS = ("replay", "head_replay")
GATES = {
    "replay": (0.8169830287163194, 1e-6),
    "naive": (0.7244106926575061, 1e-3),
}


def write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


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
    print(f"[arm] {arm} device={DEVICE.type}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)

    model = None
    current_year_f1: dict[str, float] = {}
    preds: dict[int, dict] = {}
    t0 = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
            # 头适配臂：第一年先训练完整模型，使编码器学到表示；第一年结束后再冻结编码器。
            # 若在创建时立即冻结，编码器停留在随机初始化（输出 std 3e-5），
            # 分类头只能学出常数，整臂 F1=0——那是实现缺陷，不是科学结果。
            n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,} "
                  f"trainable={n_trainable:,}", flush=True)

        if arm in REPLAY_ARMS:
            parts, _ = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        else:
            parts = [(x_curr, y_curr)]

        t_epoch = time.time()
        ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                         ch3.OFFICIAL_LR, DEVICE, rng)
        xt, yt = ch3.load_year(year, "test")
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        current_year_f1[str(year)] = float(m["f1"])
        del xt, yt
        print(f"[{year}] current_f1={m['f1']:.4f} ({time.time() - t_epoch:.0f}s)", flush=True)

        if idx == 0 and arm in HEAD_ARMS:
            for p in model.encoder.parameters():
                p.requires_grad = False
            print("[freeze] encoder frozen after first year", flush=True)

        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
                del xt, yt

    backward_f1 = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"]) for ty in years}
    mean_f1 = float(np.mean(list(backward_f1.values())))
    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(ch3.THRESHOLD))
    if arm == "replay":
        torch.save(model.state_dict(), RUN_DIR / "replay-model.pt")

    payload = {
        "arm": arm,
        "mean_f1": mean_f1,
        "backward_f1": backward_f1,
        "current_year_f1": current_year_f1,
        "wall_seconds": round(time.time() - t0, 1),
    }
    if arm in GATES:
        ref, tol = GATES[arm]
        payload["gate"] = {"expected": ref, "observed": mean_f1,
                           "abs_delta": abs(mean_f1 - ref), "passed": abs(mean_f1 - ref) <= tol}
        print(f"[gate] {arm}: {'PASS' if payload['gate']['passed'] else 'FAIL'} "
              f"(obs={mean_f1:.10f} ref={ref:.10f})", flush=True)
    write_json(RUN_DIR / f"{arm}-result.json", payload)
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
