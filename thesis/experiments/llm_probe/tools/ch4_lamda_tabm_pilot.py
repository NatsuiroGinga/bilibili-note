#!/usr/bin/env python
"""第四章 TabM 架构探针：BatchEnsemble 型参数高效集成 vs 第三章回放底座。

判据冻结于 `.Codex/docs/2026-10-20-第四章TabM架构探针/plan.md`（看到读数前）。
机制事实源：`wiki/papers/methodology/2025-Gorishniy-TabM参数高效集成.md`
（Gorishniy et al., ICLR 2025, arXiv:2410.24210v3）。

移植（非复现）：每层 BatchEnsemble 适配 `W_eff_i = W ⊙ (r_i s_i^T)`，等价实现为
`y_i = s_i ⊙ (W(r_i ⊙ x_i) + b) + β_i`；首层 `r_i` 随机符号 ±1（其余 r=1、s=1、β=0），
初始网络≈TabM-mini（成员只在第一次特征混合前分离）；训练优化成员 BCE 均值；
推理聚合成员概率均值。k∈{4,8}：骨干 512/384/256/128 远窄于论文 512–1024 块宽，
k=32 不迁移（论文图 7：k 与宽深交互）。
与论文协议的偏差（任务化适配，须随结果披露）：保持第三章冻结协议
SGD(lr=0.01, momentum=0.9, wd=1e-6) / batch 1024 / 10 epoch / 无裁剪无早停，只换结构。

协议与 base 臂逐位同源：`build_parts`（来自 2x2 模块，quota/deficit/repeat 2）、
`ch3.iterate_batches_parts` 同一流、优化器年度重建、`ch3.evaluate`/`ch3.score_shard`。

臂：tabm4 / tabm8。参照（只读）：`runs/diagnostics/ch4-lamda-paat-pilot/base-result.json`
（12y mean = 0.8169830287163194）。

冻结判据：
- 支持：2023 与 2024 backward F1 均 ≥ base + 1.0 pp，且 12y mean ≥ base − 0.20 pp；
- 否决：2023 或 2024 增益 < +0.3 pp，或 12y mean < base − 0.50 pp；
- 中间带：只做一轮机制诊断（AUC/阈值定位），不追加调参轮。
- 机制核查（披露项）：2023/2024 的 delta_auc——AUC 下降伴随 F1 上升属阈值位置效应。

运行：/opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_tabm_pilot.py --arm tabm4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = ch3.SEED
THRESHOLD = 0.5
RUN_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-tabm-pilot"
BASE_RESULT = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-paat-pilot/base-result.json"
ARMS = ("tabm4", "tabm8")

BASE_MEAN = 0.8169830287163194
BASE_F1_2023 = 0.8243143068939955
BASE_F1_2024 = 0.7421875


class BatchEnsembleLinear(nn.Module):
    """共享主权重 W/b ＋成员专属 r（输入缩放）、s（输出缩放）、β（成员偏置）。

    等价于逐成员 `W_eff_i = W ⊙ (r_i s_i^T)`：`y_i = s_i ⊙ (W(r_i ⊙ x_i) + b) + β_i`，
    不物化 W_eff（wiki 笔记物理页 4，§3.2）。输入 (B, k, in) → 输出 (B, k, out)。
    """

    def __init__(self, in_dim: int, out_dim: int, k: int, first: bool) -> None:
        super().__init__()
        self.k = k
        self.weight = nn.Parameter(torch.empty(out_dim, in_dim))
        self.bias = nn.Parameter(torch.zeros(out_dim))
        nn.init.kaiming_uniform_(self.weight, a=5 ** 0.5)  # 与 nn.Linear 默认一致
        self.r = nn.Parameter(torch.ones(k, in_dim))
        self.s = nn.Parameter(torch.ones(k, out_dim))
        self.beta = nn.Parameter(torch.zeros(k, out_dim))
        if first:
            # 论文 §3.3：第一组乘性适配用随机符号 ±1，使成员在第一次特征混合前分离
            signs = torch.randint(0, 2, (k, in_dim)).float() * 2.0 - 1.0
            with torch.no_grad():
                self.r.copy_(signs)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, k, in) —— 首层由 TabMMLP 先按 r 展开成员轴
        h = torch.matmul(x, self.weight.t()) + self.bias   # (B, k, out)，W 对成员共享
        return self.s * h + self.beta


class TabMMLP(nn.Module):
    """官方 ChenEncoderMLP 的逐层 BatchEnsemble 化（同宽同深同 Dropout 位置）。"""

    def __init__(self, input_dim: int, k: int) -> None:
        super().__init__()
        self.k = k
        self.enc1 = BatchEnsembleLinear(input_dim, 512, k, first=True)
        self.enc2 = BatchEnsembleLinear(512, 384, k, first=False)
        self.enc3 = BatchEnsembleLinear(384, 256, k, first=False)
        self.enc4 = BatchEnsembleLinear(256, 128, k, first=False)
        self.cls1 = BatchEnsembleLinear(128, 100, k, first=False)
        self.cls2 = BatchEnsembleLinear(100, 100, k, first=False)
        self.cls3 = BatchEnsembleLinear(100, 1, k, first=False)
        self.drop = nn.Dropout(0.2)

    def forward(self, x: torch.Tensor, return_members: bool = False) -> torch.Tensor:
        if x.dim() == 2:
            b = x.shape[0]
            h = x.unsqueeze(1).expand(b, self.k, x.shape[1]) * self.enc1.r  # (B,k,in)
        else:
            h = x
        for layer in (self.enc1, self.enc2, self.enc3, self.enc4):
            h = torch.relu(layer(h))
        h = self.drop(torch.relu(self.cls1(h)))
        h = self.drop(torch.relu(self.cls2(h)))
        out = torch.sigmoid(self.cls3(h))                  # (B, k, 1)
        if return_members:
            return out
        return out.mean(dim=1)                             # 推理：成员概率均值


def f1_of(y: np.ndarray, score: np.ndarray) -> float:
    p = (score >= THRESHOLD).astype(int)
    tp = int(((p == 1) & (y == 1)).sum())
    fp = int(((p == 1) & (y == 0)).sum())
    fn = int(((p == 0) & (y == 1)).sum())
    d = 2 * tp + fp + fn
    return float(2 * tp / d) if d else 0.0


def train_epochs_tabm(model: TabMMLP, parts, epochs: int, device: torch.device,
                      rng: np.random.Generator, arm: str, year: int) -> dict[str, Any]:
    """镜像 `ch3.train_epochs`：优化器年度重建、同 `iterate_batches_parts` 流；
    仅损失改为成员 BCE 均值（对 (B,k,1) 与展开标签取 BCELoss，均值等价成员均值）。"""
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss()
    model.train()
    bce_hist: list[float] = []
    n_total = 0
    for ep in range(epochs):
        bce_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)          # (B,1)
            opt.zero_grad()
            out = model(xt, return_members=True)                       # (B,k,1)
            loss = criterion(out, yt.unsqueeze(1).expand(-1, model.k, -1))
            bce_sum = bce_sum + loss.detach()
            n_batches += 1
            loss.backward()
            opt.step()
        bce_m = float(bce_sum.item() / max(n_batches, 1))
        bce_hist.append(bce_m)
        n_total += n_batches
        print(f"[{arm}][train] {year} epoch={ep + 1}/{epochs} bce={bce_m:.6f} "
              f"n_batches={n_batches}", flush=True)
    return {"optimizer_type": "SGD", "epoch_mean_bce": bce_hist, "n_batches": n_total}


def run_arm(arm: str) -> int:
    k = int(arm.removeprefix("tabm"))
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    years = list(ch3.DOMAIN_YEARS)
    print(f"[arm] {arm} k={k} device={DEVICE.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"seed={SEED} threshold={THRESHOLD}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)

    model = TabMMLP(input_dim, k).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] k={k} params={n_params:,} "
          f"(官方 MLP 基座 594,753 参数，见 preflight E1 frozen_config)", flush=True)

    current_year_f1: dict[str, float] = {}
    preds: dict[int, dict[str, np.ndarray]] = {}
    train_logs: dict[str, dict[str, Any]] = {}
    t0 = time.time()
    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        parts, _meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        n_rows = int(sum(p[0].shape[0] for p in parts))
        pos_rows = int(sum(int((p[1] == 1).sum()) for p in parts))
        print(f"[parts] {year}: rows={n_rows:,} pos={pos_rows:,} "
              f"pos_rate={pos_rows / max(n_rows, 1):.4f}", flush=True)

        t_epoch = time.time()
        train_logs[str(year)] = train_epochs_tabm(model, parts, ch3.OFFICIAL_EPOCHS,
                                                  DEVICE, rng, arm, year)
        xt, yt = ch3.load_year(year, "test")
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        current_year_f1[str(year)] = float(m["f1"])
        del xt, yt
        print(f"[{year}] current_f1={m['f1']:.4f} ({time.time() - t_epoch:.0f}s)", flush=True)

        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
                del xt, yt

    backward_f1 = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"]) for ty in years}
    mean_f1 = float(np.mean(list(backward_f1.values())))

    # 机制核查：2023/2024 delta_auc vs base 分数（base preds 只读）
    auc_check: dict[str, Any] = {}
    from sklearn.metrics import roc_auc_score
    for ty in (2023, 2024):
        zb = np.load(TOOLS_DIR.parent / f"runs/diagnostics/ch4-lamda-paat-pilot/preds_base_{ty}.npz")
        y_true = zb["y_true"].astype(np.int8)
        auc_base = float(roc_auc_score(y_true, zb["y_score"].astype(np.float64)))
        auc_tabm = float(roc_auc_score(y_true, preds[ty]["y_score"].astype(np.float64)))
        auc_check[str(ty)] = {"auc_base": auc_base, "auc_tabm": auc_tabm,
                              "delta_auc": auc_tabm - auc_base}

    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(THRESHOLD))

    d_2023 = (backward_f1["2023"] - BASE_F1_2023) * 100
    d_2024 = (backward_f1["2024"] - BASE_F1_2024) * 100
    d_mean = (mean_f1 - BASE_MEAN) * 100
    support = d_2023 >= 1.0 and d_2024 >= 1.0 and d_mean >= -0.20
    reject = d_2023 < 0.3 or d_2024 < 0.3 or d_mean < -0.50
    verdict = "support" if support else ("reject" if reject else "mixed_band")

    payload: dict[str, Any] = {
        "arm": arm, "k": k, "n_params": n_params,
        "transplant_notes": {
            "first_adapter_init": "random_sign_pm1",
            "other_adapters_init": "r=1,s=1,beta=0",
            "train_loss": "mean_of_member_bce",
            "eval": "mean_of_member_sigmoid",
            "protocol_deviation": "SGD(0.01,0.9,1e-6)/batch1024/10ep，无裁剪无早停；论文用 AdamW+clip+早停；属任务化适配，非复现",
        },
        "protocol": {"domain_years": years, "epochs": ch3.OFFICIAL_EPOCHS,
                     "batch": ch3.OFFICIAL_BATCH, "lr": ch3.OFFICIAL_LR,
                     "momentum": ch3.OFFICIAL_MOMENTUM, "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
                     "memory": ch3.OFFICIAL_MEMORY, "seed": SEED, "threshold": THRESHOLD},
        "mean_f1": mean_f1, "f1_2023": backward_f1["2023"], "f1_2024": backward_f1["2024"],
        "backward_f1": backward_f1, "current_year_f1": current_year_f1,
        "criteria": {
            "delta_2023_pp": d_2023, "delta_2024_pp": d_2024, "delta_mean12_pp": d_mean,
            "support": support, "reject": reject, "verdict": verdict,
            "auc_check": auc_check,
        },
        "wall_seconds": round(time.time() - t0, 1),
        "train_logs": train_logs,
        "ts": datetime.now(UTC).isoformat(),
    }
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    (RUN_DIR / f"{arm}-result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[criteria] d2023={d_2023:+.2f}pp d2024={d_2024:+.2f}pp dmean={d_mean:+.2f}pp "
          f"-> {verdict}", flush=True)
    print(f"[auc_check] {json.dumps(auc_check)}", flush=True)
    print(f"=== {arm}: 12y mean={mean_f1:.10f} | 2023={backward_f1['2023']:.6f} "
          f"2024={backward_f1['2024']:.6f} | {payload['wall_seconds']:.0f}s ===", flush=True)
    maybe_comparison()
    return 0


def maybe_comparison() -> None:
    res = {}
    for arm in ARMS:
        p = RUN_DIR / f"{arm}-result.json"
        if p.is_file():
            res[arm] = json.loads(p.read_text(encoding="utf-8"))
    if not res:
        return
    comp = {"schema_version": "ch4-tabm-pilot-comparison-v1", "reference_base_mean": BASE_MEAN,
            "base_f1": {"2023": BASE_F1_2023, "2024": BASE_F1_2024},
            "arms": {a: {"mean_f1": r["mean_f1"], "f1_2023": r["f1_2023"],
                         "f1_2024": r["f1_2024"], "verdict": r["criteria"]["verdict"],
                         "auc_check": r["criteria"]["auc_check"]}
                     for a, r in res.items()},
            "ts": datetime.now(UTC).isoformat()}
    (RUN_DIR / "tabm-comparison.json").write_text(
        json.dumps(comp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章 TabM 架构探针")
    parser.add_argument("--arm", choices=ARMS, required=True)
    args = parser.parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return run_arm(args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
