#!/usr/bin/env python
"""第四章效率轴阶段一诊断：年度训练预算的逐轮 F1 轨迹。

只回答一个问题：固定 10 轮中，有多少轮花在当前年度 F1 到达平台之前？

- 同协议训练 `base`（BSQ-DWR，memory=200/quota/deficit/repeat2），12 个年度。
- 每个年度每一轮后，评价**该年度测试分片**，记录 F1/FNR/FPR/loss。
  该评价是**收敛诊断**，只用于判断平台，不用于模型选择，也不进入论文结果。
- 训练循环逐句复刻 `ch3.train_epochs` 的优化器生命周期与批迭代；评价后恢复
  `model.train()`，避免 Dropout 在后续轮次被关闭。
- 终局复现门：末年模型在 12 个测试年度上的平均 F1 必须等于
  `0.8169830287163194`（绝对容差 `1e-6`）。不通过即说明逐轮评价改变了训练轨迹，
  停止并报告。

判据见 `thesis/methods/第四章研究问题卡-训练预算效率.md` §5.1，在看到轨迹前冻结。
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
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics/ch4-lamda-epoch-trajectory-v1"
OUT_PATH = RUN_DIR / "epoch-trajectory.json"
GATE_REF = 0.8169830287163194
GATE_TOL = 1e-6


def write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    years = list(ch3.DOMAIN_YEARS)
    print(f"[config] device={DEVICE.type} years={years} epochs={ch3.OFFICIAL_EPOCHS} "
          f"batch={ch3.OFFICIAL_BATCH} lr={ch3.OFFICIAL_LR} seed={SEED}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)

    model: nn.Module | None = None
    trajectory: list[dict] = []
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,}", flush=True)

        parts, meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        n_train = int(sum(p[0].shape[0] for p in parts))
        print(f"[parts] {year}: n_parts={len(parts)} sizes={[int(p[0].shape[0]) for p in parts]} "
              f"total={n_train:,}", flush=True)

        opt = torch.optim.SGD(
            model.parameters(),
            lr=ch3.OFFICIAL_LR,
            momentum=ch3.OFFICIAL_MOMENTUM,
            weight_decay=ch3.OFFICIAL_WEIGHT_DECAY,
        )
        criterion = nn.BCELoss()
        model.train()

        xt, yt = ch3.load_year(year, "test")
        epoch_rows: list[dict] = []
        for epoch in range(1, ch3.OFFICIAL_EPOCHS + 1):
            total_loss = 0.0
            n_seen = 0
            for xb, yb in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True):
                xbt = torch.from_numpy(xb.astype(np.float32)).to(DEVICE)
                ybt = torch.from_numpy(yb).to(DEVICE).unsqueeze(1)
                opt.zero_grad()
                out = model(xbt)
                loss = criterion(out, ybt)
                loss.backward()
                opt.step()
                total_loss += float(loss.item()) * int(xb.shape[0])
                n_seen += int(xb.shape[0])
            mean_loss = total_loss / max(1, n_seen)

            metrics = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
            model.train()  # evaluate 内部切到 eval，必须恢复训练模式（Dropout）
            epoch_rows.append(
                {
                    "epoch": epoch,
                    "mean_loss": mean_loss,
                    "f1": float(metrics["f1"]),
                    "accuracy": float(metrics["accuracy"]),
                    "precision": float(metrics["precision"]),
                    "recall": float(metrics["recall"]),
                }
            )
            print(f"[{year}] epoch {epoch}/{ch3.OFFICIAL_EPOCHS} "
                  f"loss={mean_loss:.6f} f1={metrics['f1']:.6f}", flush=True)

        trajectory.append(
            {
                "year": year,
                "n_train": n_train,
                "n_parts": len(parts),
                "n_test": int(yt.size),
                "epochs": epoch_rows,
            }
        )
        del xt, yt

    # 终局复现门：末年模型在 12 个测试年度上的平均 F1
    final_per_year: dict[str, dict] = {}
    for y in years:
        xt, yt = ch3.load_year(y, "test")
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        final_per_year[str(y)] = {
            "f1": float(m["f1"]),
            "accuracy": float(m["accuracy"]),
            "precision": float(m["precision"]),
            "recall": float(m["recall"]),
            "n": int(m["n"]),
            "n_pos": int(m["n_pos"]),
        }
        del xt, yt
    final_mean = float(np.mean([final_per_year[str(y)]["f1"] for y in years]))
    gate_ok = abs(final_mean - GATE_REF) <= GATE_TOL
    print(f"[gate] final 12-year mean f1={final_mean:.10f} ref={GATE_REF:.10f} "
          f"abs_delta={abs(final_mean - GATE_REF):.3e} -> {'PASS' if gate_ok else 'FAIL'}",
          flush=True)

    # 平台分析
    analysis: list[dict] = []
    for row in trajectory:
        f1s = [e["f1"] for e in row["epochs"]]
        final_f1 = f1s[-1]
        plateau = next((i + 1 for i, v in enumerate(f1s) if v >= final_f1 - 0.001), None)
        f1_at_6 = f1s[5] if len(f1s) >= 6 else None
        analysis.append(
            {
                "year": row["year"],
                "final_f1": final_f1,
                "plateau_epoch": plateau,
                "f1_epoch6": f1_at_6,
                "f1_loss_at_6": (final_f1 - f1_at_6) if f1_at_6 is not None else None,
            }
        )

    n_early = sum(1 for a in analysis if a["plateau_epoch"] is not None and a["plateau_epoch"] <= 6)
    mean_loss_at_6 = float(np.mean([a["f1_loss_at_6"] for a in analysis]))
    early_2013_2014 = all(
        a["plateau_epoch"] is not None and a["plateau_epoch"] <= 7
        for a in analysis
        if a["year"] in (2013, 2014)
    )
    median_plateau = float(np.median([a["plateau_epoch"] for a in analysis]))
    n_big_loss = sum(1 for a in analysis if a["f1_loss_at_6"] > 0.003)
    any_last = any(a["plateau_epoch"] == 10 for a in analysis if a["year"] in (2013, 2014))

    support = (n_early >= 8) and (mean_loss_at_6 >= -0.001) and early_2013_2014
    falsify = (median_plateau >= 9) or (n_big_loss >= 6) or any_last
    if support and not falsify:
        verdict = "support_efficiency_axis"
    elif falsify and not support:
        verdict = "reject_efficiency_axis"
    else:
        verdict = "mixed_needs_review"

    payload = {
        "schema_version": "ch4-epoch-trajectory-v1",
        "kind": "convergence_diagnostic_target_informed",
        "data_revision": "ad9614bdd5556767f97ced2fce797c2f06408ebf",
        "seed": SEED,
        "device": DEVICE.type,
        "protocol": {
            "years": years,
            "epochs": ch3.OFFICIAL_EPOCHS,
            "batch": ch3.OFFICIAL_BATCH,
            "lr": ch3.OFFICIAL_LR,
            "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
            "memory": 200,
            "buffer_scheme": "quota",
            "reuse_scheme": "deficit",
            "buffer_repeat": 2,
            "pos_ratio": 0.5,
            "deficit_gamma": 1.0,
            "threshold": ch3.THRESHOLD,
        },
        "notes": [
            "每轮评价对象是该年度测试分片，属目标知情收敛诊断，不用于模型选择。",
            "评价后恢复 model.train()，不改变 Dropout 与训练随机流。",
            "终局复现门必须通过，否则逐轮评价已改变训练轨迹，本诊断无效。",
        ],
        "final_gate": {
            "observed": final_mean,
            "expected": GATE_REF,
            "abs_delta": abs(final_mean - GATE_REF),
            "passed": gate_ok,
        },
        "final_per_year": final_per_year,
        "trajectory": trajectory,
        "plateau_analysis": analysis,
        "criteria": {
            "n_plateau_le_6": n_early,
            "mean_f1_loss_at_6": mean_loss_at_6,
            "early_years_plateau_le_7": early_2013_2014,
            "median_plateau": median_plateau,
            "n_years_f1_loss_at_6_gt_0_3pp": n_big_loss,
            "any_early_year_plateau_eq_10": any_last,
            "support_efficiency_axis": support,
            "falsify_efficiency_axis": falsify,
            "verdict": verdict,
        },
        "wall_seconds": round(time.time() - t_start, 1),
    }
    write_json(OUT_PATH, payload)
    print(f"[criteria] {json.dumps(payload['criteria'], ensure_ascii=False)}", flush=True)
    print(f"[done] {OUT_PATH} wall={payload['wall_seconds']}s", flush=True)
    return 0 if gate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
