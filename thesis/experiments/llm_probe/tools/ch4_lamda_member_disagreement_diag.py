#!/usr/bin/env python
"""第四章 TabM 任务化改造先导诊断：uniform tabm4 的成员分歧读数。

背景：研究问题卡（`thesis/methods/第四章-TabM任务化改造研究问题卡.md`）§六.3。
uniform tabm4 的模型权重当时未保存，只能以同种子 42 重训一次，并归档
**成员逐项预测**，直接测量「成员分歧在正例稀缺年是否更大」——这是 H3
（任务化增量的作用面＝稀缺年边界分数方差）的直接可观测量。

本脚本是**诊断**，不是机制实验：
- 只归档读数，不做任何判据裁决，不比较任何门限；
- 不修改 `ch4_lamda_tabm_pilot.py`、`ch3_lamda_domain_il_e4.py` 或任何既有文件；
- 只新增本脚本与 `runs/diagnostics/ch4-lamda-tabm-pilot/member-disagreement-diag.json`。

复刻口径（逐句对齐 `tabm.run_arm("tabm4")`）：
`torch.manual_seed(42)` → `np.random.seed(42)` → 12 年 train 分片一次载入 →
`rng`/`buf_rng = default_rng(42)` → `TabMMLP(input_dim, 4)` → 逐年
`build_parts` + `tabm.train_epochs_tabm(10 epoch, batch 1024, SGD 0.01/0.9/1e-6)`。
原脚本每年训练后的 `ch3.evaluate` 是 `model.eval()` 下的只读前向，不更新参数、
不消耗 Dropout 所需的全局 RNG，故省略不改变训练轨迹；其等价性由下面的恒等门核验。

恒等门：用本脚本的**逐成员前向**结果取成员均值，算出的 F1 必须与
`tabm4-result.json` 的 `backward_f1` 逐年在 `1e-9` 内一致，否则非零退出。

运行：
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_member_disagreement_diag.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import roc_auc_score

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
import ch4_lamda_tabm_pilot as tabm  # noqa: E402  （只读导入；不改原脚本）
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

ARM = "tabm4"
SEED = ch3.SEED
THRESHOLD = tabm.THRESHOLD
DEVICE = tabm.DEVICE
RUN_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-tabm-pilot"
RESULT_PATH = RUN_DIR / f"{ARM}-result.json"
OUT_PATH = RUN_DIR / "member-disagreement-diag.json"
GATE_TOL = 1e-9
STD_DDOF = 0  # 总体标准差；逐样本跨成员计算


@torch.inference_mode()
def score_members(model: "tabm.TabMMLP", x: np.ndarray, batch: int,
                  device: torch.device) -> np.ndarray:
    """手动逐层前向并保留成员维，返回 (N, k) 的逐成员 sigmoid 分数。

    语义逐句复刻 `tabm.TabMMLP.forward(return_members=True)`：
    x→(B,k,in) 按 `enc1.r` 展开 → 四个 BatchEnsemble 层各自 `relu(layer(h))` →
    `drop(relu(cls1))` → `drop(relu(cls2))` → `sigmoid(cls3)`。
    `model.eval()` 与 `ch3.score_shard` 一致地关闭 Dropout（`drop` 此时为恒等）。
    分片迭代顺序与 `ch3.score_shard` 相同（`default_rng(0)`、不打乱）。
    """
    model.eval()
    k = model.k
    dummy = np.zeros(x.shape[0], dtype=np.float32)
    chunks: list[np.ndarray] = []
    for xb, _ in ch3.iterate_batches(x, dummy, batch, np.random.default_rng(0), False):
        xt = torch.from_numpy(xb.astype(np.float32)).to(device)
        b = xt.shape[0]
        h = xt.unsqueeze(1).expand(b, k, xt.shape[1]) * model.enc1.r  # (B,k,in)
        for layer in (model.enc1, model.enc2, model.enc3, model.enc4):
            h = torch.relu(layer(h))
        h = model.drop(torch.relu(model.cls1(h)))
        h = model.drop(torch.relu(model.cls2(h)))
        out = torch.sigmoid(model.cls3(h))                             # (B,k,1)
        chunks.append(out.squeeze(-1).float().cpu().numpy())
    if not chunks:
        return np.zeros((0, k), dtype=np.float32)
    return np.concatenate(chunks, axis=0).astype(np.float32)


def safe_auc(y: np.ndarray, score: np.ndarray) -> float | None:
    """单类样本时 AUC 无定义，记 None（不伪造成 0.5）。"""
    if int((y == 1).sum()) == 0 or int((y == 0).sum()) == 0:
        return None
    return float(roc_auc_score(y.astype(np.int8), score.astype(np.float64)))


def pairwise_disagreement_rate(members: np.ndarray, threshold: float) -> float:
    """两成员在 `>= threshold` 判定下不一致的样本占比，再对全部成员对取均值。"""
    hard = (members >= threshold).astype(np.int8)
    rates: list[float] = []
    for i, j in combinations(range(members.shape[1]), 2):
        rates.append(float((hard[:, i] != hard[:, j]).mean()))
    return float(np.mean(rates)) if rates else 0.0


def yearly_metrics(members: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """单年度的逐成员与集成读数；不做任何裁决。"""
    k = members.shape[1]
    ensemble = members.mean(axis=1)
    f1_per_member = [tabm.f1_of(y, members[:, i]) for i in range(k)]
    f1_ensemble = tabm.f1_of(y, ensemble)
    std_per_sample = np.std(members, axis=1, ddof=STD_DDOF)
    pos = y == 1
    neg = y == 0
    return {
        "n": int(y.size),
        "n_pos": int(pos.sum()),
        "n_neg": int(neg.sum()),
        "f1_per_member": f1_per_member,
        "f1_ensemble": f1_ensemble,
        "gain_over_best_member_pp": (f1_ensemble - max(f1_per_member)) * 100.0,
        "mean_member_std": float(np.mean(std_per_sample)),
        "member_std_pos": float(np.mean(std_per_sample[pos])) if pos.any() else None,
        "member_std_neg": float(np.mean(std_per_sample[neg])) if neg.any() else None,
        "auc_per_member": [safe_auc(y, members[:, i]) for i in range(k)],
        "auc_ensemble": safe_auc(y, ensemble),
        "pairwise_disagreement_rate": pairwise_disagreement_rate(members, THRESHOLD),
        "mean_ensemble_score": float(np.mean(ensemble)),
        "std_ddof": STD_DDOF,
        "threshold": THRESHOLD,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                   encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    t0 = time.time()
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    years = list(ch3.DOMAIN_YEARS)
    k = int(ARM.removeprefix("tabm"))
    print(f"[config] arm={ARM} k={k} device={DEVICE.type} seed={SEED} "
          f"epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)

    model = tabm.TabMMLP(input_dim, k).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] k={k} params={n_params:,}", flush=True)

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        parts, _meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        n_rows = int(sum(p[0].shape[0] for p in parts))
        pos_rows = int(sum(int((p[1] == 1).sum()) for p in parts))
        print(f"[parts] {year}: rows={n_rows:,} pos={pos_rows:,} "
              f"pos_rate={pos_rows / max(n_rows, 1):.4f}", flush=True)
        t_epoch = time.time()
        tabm.train_epochs_tabm(model, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng, ARM, year)
        print(f"[{year}] trained ({time.time() - t_epoch:.0f}s)", flush=True)
        del parts

    # 全部 12 个测试年逐成员打分（末年模型，与 tabm.run_arm 的 backward 口径一致）
    members_by_year: dict[int, np.ndarray] = {}
    labels_by_year: dict[int, np.ndarray] = {}
    for ty in years:
        xt, yt = ch3.load_year(ty, "test")
        members_by_year[ty] = score_members(model, xt, ch3.OFFICIAL_BATCH, DEVICE)
        labels_by_year[ty] = yt.astype(np.int8)
        del xt, yt
        print(f"[score] {ty}: members={members_by_year[ty].shape}", flush=True)

    # ---- 恒等门：成员均值 F1 必须与已归档 tabm4-result.json 逐年一致 ----
    if not RESULT_PATH.is_file():
        print(f"[gate][FAIL] 缺少参照结果 {RESULT_PATH}", flush=True)
        return 2
    ref = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    ref_f1: dict[str, float] = ref["backward_f1"]
    gate_rows: dict[str, dict[str, float]] = {}
    gate_ok = True
    for ty in years:
        got = tabm.f1_of(labels_by_year[ty], members_by_year[ty].mean(axis=1))
        want = float(ref_f1[str(ty)])
        diff = abs(got - want)
        gate_rows[str(ty)] = {"diag_f1": got, "result_json_f1": want, "abs_diff": diff}
        if diff > GATE_TOL:
            gate_ok = False
            print(f"[gate][FAIL] {ty}: diag={got!r} ref={want!r} diff={diff:.3e} "
                  f"> tol={GATE_TOL:.1e}", flush=True)
    max_diff = max(r["abs_diff"] for r in gate_rows.values())
    print(f"[gate] {'PASS' if gate_ok else 'FAIL'} max_abs_diff={max_diff:.3e} "
          f"tol={GATE_TOL:.1e}", flush=True)
    if not gate_ok:
        return 1

    # 附加核验（不设门）：与已归档集成分数 npz 的逐样本差，用于说明重训一致性
    archived_max_abs_diff: dict[str, float] = {}
    for ty in years:
        zpath = RUN_DIR / f"preds_{ARM}_{ty}.npz"
        if zpath.is_file():
            archived = np.load(zpath)["y_score"].astype(np.float64)
            diag = members_by_year[ty].mean(axis=1).astype(np.float64)
            if archived.shape == diag.shape:
                archived_max_abs_diff[str(ty)] = float(np.max(np.abs(archived - diag)))
    print(f"[archive-check] max_abs_score_diff="
          f"{max(archived_max_abs_diff.values(), default=float('nan')):.3e}", flush=True)

    year_metrics = {str(ty): yearly_metrics(members_by_year[ty], labels_by_year[ty])
                    for ty in years}

    payload: dict[str, Any] = {
        "schema_version": "ch4-tabm-member-disagreement-diag-v1",
        "arm": ARM,
        "k": k,
        "seed": SEED,
        "device": DEVICE.type,
        "n_params": n_params,
        "identity_gate": {
            "passed": True,
            "tol": GATE_TOL,
            "max_abs_diff": max_diff,
            "reference": str(RESULT_PATH.relative_to(TOOLS_DIR.parent)),
            "per_year": gate_rows,
        },
        "archived_score_check": {
            "note": "重训后成员均值分数与已归档 npz 的逐样本最大绝对差；不设门，仅披露",
            "max_abs_diff_per_year": archived_max_abs_diff,
        },
        "protocol": {
            "domain_years": years,
            "epochs": ch3.OFFICIAL_EPOCHS,
            "batch": ch3.OFFICIAL_BATCH,
            "lr": ch3.OFFICIAL_LR,
            "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
            "memory": ch3.OFFICIAL_MEMORY,
            "threshold": THRESHOLD,
            "eval": "mean_of_member_sigmoid",
            "score_fn": "manual_per_member_forward",
        },
        "years": year_metrics,
        "wall_seconds": round(time.time() - t0, 1),
        "ts": datetime.now(UTC).isoformat(),
    }
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    write_json(OUT_PATH, payload)
    print(f"[done] wrote {OUT_PATH} ({time.time() - t0:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
