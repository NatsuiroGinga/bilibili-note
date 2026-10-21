#!/usr/bin/env python
"""第四章 NCL 负相关先导 + 训练通道诊断：三臂串行（train_single / ncl05 / ncl2）。

判据与臂定义冻结于 `thesis/methods/第四章-NCL与训练通道诊断先导设计.md`
（2026-10-21，看到任何 NCL 臂读数之前）。本脚本只实现，不改判据、λ 或臂定义。

三臂（uniform tabm4 为参照，只读其既有制品，不重跑）：

- train_single（D0）：每批用独立 rng 流 `np.random.default_rng(42)` 均匀随机抽
  1 个成员计算该成员 BCE；评测合同不变（4 成员概率平均）。该臂是训练通道诊断，
  不承担机制存废，结果只登记。
- ncl05 / ncl2：L = (1/k) Σ_i BCE(s_i, y) + λ·(1/k) Σ_i p_i，
  p_i = (s_i − s̄) Σ_{j≠i}(s_j − s̄)，λ ∈ {0.5, 2.0}；全局，无年度条件化；
  评测合同不变。

**惩罚尺度登记（实现披露，不改公式）**：由代数恒等式
Σ_{j≠i}(s_j − s̄) = −(s_i − s̄)，故 mean_i p_i = −Var_i(s_i)（总体方差）。
最小化该惩罚项等价于增大成员方差（抬高歧义 Ā），与设计 §一的方向声明一致。
λ 无数值文献依据，按设计登记为任务化设定。逐 epoch 的 bce、惩罚值、
λ·|惩罚|/bce 比值全部写入 `{arm}-result.json` 的 train_logs。

协议骨架逐位复用 `ch4_lamda_tabm_pilot`：`TabMMLP`、`f1_of`、优化器年度重建、
`build_parts`（来自 2x2 模块）、`ch3` 的评测/打分函数与协议常量；
批次流使用 `ch3.iterate_batches_parts`（标准一维标签）。成员逐项分数复用
`ch4_lamda_member_disagreement_diag.score_members` 与
`pairwise_disagreement_rate`，保证与 uniform 参照的分歧率口径一致。

逐 epoch 成员分歧探针（三臂全部年份）：每个 epoch 结束后，在当前年度训练池
（`x_curr`）的固定等距子样本（≤4096 行，不使用标签，eval 模式、不消耗
Dropout RNG、不更新参数）上计算 4 成员分数的 pairwise 不一致率（0.5 判定）
与平均成员标准差，写入 `train_logs[year].epoch_disagreement`（每年 10 点）。
这是「成员合流（ρ 随联合训练上升）」假设的直接测量。

运行（每臂约 830 s，三臂串行）：
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_ncl_pilot.py --arm train_single
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_ncl_pilot.py --arm ncl05
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_ncl_pilot.py --arm ncl2
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
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
import ch4_lamda_posthoc_prior_diag as posthoc  # noqa: E402  （只用 oracle_f1）
from ch4_lamda_member_disagreement_diag import (  # noqa: E402  （只读复用分歧率口径）
    pairwise_disagreement_rate,
    score_members,
)
from ch4_lamda_tabm_pilot import TabMMLP, f1_of  # noqa: E402
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = ch3.SEED
THRESHOLD = ch3.THRESHOLD
K = 4
YEARS = list(ch3.DOMAIN_YEARS)

RUN_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-ncl-pilot"
BASE_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-paat-pilot"
UNIFORM_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-tabm-pilot"
UNIFORM_DIAG = UNIFORM_DIR / "member-disagreement-diag.json"
DESIGN_DOC = "thesis/methods/第四章-NCL与训练通道诊断先导设计.md"

ARMS = ("train_single", "ncl05", "ncl2")
NCL_ARMS = ("ncl05", "ncl2")
NCL_LAMBDA = {"ncl05": 0.5, "ncl2": 2.0}

# 参照：uniform tabm4 既有制品（只读；不重跑）
UNIFORM_MEAN = 0.832346367494066
UNIFORM_F1_2023 = 0.8681241184767278
UNIFORM_F1_2024 = 0.7703703703703704

# 冻结判据（设计文档 §三）
SUPPORT_DELTA_PP = 0.5          # 2023 与 2024 各 >= +0.5 pp
SUPPORT_MEAN_MIN_PP = -0.20     # 12 年平均 >= uniform − 0.20 pp
DUAL_CHANNEL_ACCOUNT_PP = 0.47  # 理论文档 H2a 的训练通道账（设计 §三 D0 对照）
PROBE_MAX_ROWS = 4096           # 逐 epoch 分歧探针的固定子样本上限


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写出：先写 .partial 再 replace。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def save_npz(path: Path, **arrays: np.ndarray) -> None:
    """原子写出 npz：临时文件用 .npz 后缀，避免 np.savez 再追加扩展名。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.stem}.partial.npz"
    np.savez_compressed(tmp, **arrays)
    tmp.replace(path)


def ncl_penalty(s: torch.Tensor) -> torch.Tensor:
    """mean_i p_i，p_i = (s_i − s̄) Σ_{j≠i}(s_j − s̄)。

    输入 s: (B, k) 的成员概率。由恒等式 mean_i p_i = −Var_i(s_i)（ddof=0），
    最小化该项等价于增大成员方差（设计 §一：抬高歧义 Ā）。
    """
    d = s - s.mean(dim=1, keepdim=True)
    d_others = d.sum(dim=1, keepdim=True) - d
    return (d * d_others).mean()


def epoch_probe_indices(n: int) -> np.ndarray:
    """固定等距索引：≤4096 行；无 RNG、不随 epoch 变化。"""
    if n <= PROBE_MAX_ROWS:
        return np.arange(n, dtype=np.int64)
    return np.linspace(0, n - 1, num=PROBE_MAX_ROWS).round().astype(np.int64)


@torch.inference_mode()
def probe_epoch_disagreement(model: TabMMLP, x_probe: np.ndarray,
                             device: torch.device) -> dict[str, Any]:
    """eval 模式前向固定子样本，返回 pairwise 不一致率与平均成员标准差。

    Dropout 在 eval 下关闭，故本探针不消耗训练 RNG、不更新参数，
    不改变后续训练轨迹；结束后恢复 `model.train()`。
    """
    was_training = model.training
    model.eval()
    chunks: list[np.ndarray] = []
    for s in range(0, x_probe.shape[0], ch3.OFFICIAL_BATCH):
        xt = torch.from_numpy(x_probe[s:s + ch3.OFFICIAL_BATCH].astype(np.float32)).to(device)
        out = model(xt, return_members=True).squeeze(-1)               # (B,k)
        chunks.append(out.float().cpu().numpy())
    members = (np.concatenate(chunks, axis=0) if chunks
               else np.zeros((0, model.k), dtype=np.float32))
    std = np.std(members, axis=1, ddof=0)
    res = {
        "n": int(members.shape[0]),
        "pairwise_disagreement_rate": pairwise_disagreement_rate(members, THRESHOLD),
        "mean_member_std": float(std.mean()) if members.size else None,
    }
    if was_training:
        model.train()
    return res


def train_epochs_train_single(model: TabMMLP, parts, epochs: int, device: torch.device,
                              rng: np.random.Generator, member_rng: np.random.Generator,
                              arm: str, year: int,
                              x_probe: np.ndarray) -> dict[str, Any]:
    """D0：每批独立 rng 均匀抽 1 个成员算 BCE；优化器年度重建、同批次流。"""
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = torch.nn.BCELoss()
    model.train()
    sel_hist: list[float] = []
    all_hist: list[float] = []
    disag_hist: list[dict[str, Any]] = []
    draw_counts = [0] * model.k
    n_total = 0
    for ep in range(epochs):
        sel_sum = torch.zeros((), device=device)
        all_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)          # (B,1)
            opt.zero_grad()
            out = model(xt, return_members=True)                       # (B,k,1)
            m = int(member_rng.integers(0, model.k))                   # 每批一个成员
            draw_counts[m] += 1
            loss = criterion(out[:, m, 0], yt[:, 0])
            with torch.no_grad():
                all_bce = criterion(out, yt.unsqueeze(1).expand(-1, model.k, -1))
                sel_sum = sel_sum + loss.detach()
                all_sum = all_sum + all_bce
            n_batches += 1
            loss.backward()
            opt.step()
        sel_m = float(sel_sum.item() / max(n_batches, 1))
        all_m = float(all_sum.item() / max(n_batches, 1))
        dis = probe_epoch_disagreement(model, x_probe, device)
        dis["epoch"] = ep + 1
        sel_hist.append(sel_m)
        all_hist.append(all_m)
        disag_hist.append(dis)
        n_total += n_batches
        print(f"[{arm}][train] {year} epoch={ep + 1}/{epochs} bce_selected={sel_m:.6f} "
              f"bce_all_members={all_m:.6f} probe_dis={dis['pairwise_disagreement_rate']:.6f} "
              f"probe_std={dis['mean_member_std']:.6f} draws={draw_counts} "
              f"n_batches={n_batches}", flush=True)
    return {
        "optimizer_type": "SGD",
        "epoch_mean_bce_selected_member": sel_hist,
        "epoch_mean_bce_all_members": all_hist,
        "member_draw_counts": draw_counts,
        "member_rng": "np.random.default_rng(42)，与训练洗牌流独立",
        "epoch_disagreement": disag_hist,
        "n_batches": n_total,
    }


def train_epochs_ncl(model: TabMMLP, parts, epochs: int, device: torch.device,
                     rng: np.random.Generator, arm: str, year: int,
                     lam: float, x_probe: np.ndarray) -> dict[str, Any]:
    """NCL：L = mean_i BCE(s_i,y) + λ·mean_i p_i；优化器年度重建、同批次流。"""
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    model.train()
    loss_hist: list[float] = []
    bce_hist: list[float] = []
    pen_hist: list[float] = []
    var_hist: list[float] = []
    ratio_hist: list[float] = []
    disag_hist: list[dict[str, Any]] = []
    n_total = 0
    for ep in range(epochs):
        loss_sum = torch.zeros((), device=device)
        bce_sum = torch.zeros((), device=device)
        pen_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)          # (B,1)
            opt.zero_grad()
            out = model(xt, return_members=True)                       # (B,k,1)
            target = yt.unsqueeze(1).expand(-1, model.k, -1)           # (B,k,1)
            elem = F.binary_cross_entropy(out, target, reduction="none").squeeze(-1)
            bce = elem.mean()                                          # mean_i BCE_i
            pen = ncl_penalty(out.squeeze(-1))                         # mean_i p_i
            loss = bce + lam * pen
            with torch.no_grad():
                loss_sum = loss_sum + loss.detach()
                bce_sum = bce_sum + bce.detach()
                pen_sum = pen_sum + pen.detach()
            n_batches += 1
            loss.backward()
            opt.step()
        loss_m = float(loss_sum.item() / max(n_batches, 1))
        bce_m = float(bce_sum.item() / max(n_batches, 1))
        pen_m = float(pen_sum.item() / max(n_batches, 1))
        var_m = -pen_m
        ratio_m = abs(lam * pen_m) / max(abs(bce_m), 1e-12)
        dis = probe_epoch_disagreement(model, x_probe, device)
        dis["epoch"] = ep + 1
        loss_hist.append(loss_m)
        bce_hist.append(bce_m)
        pen_hist.append(pen_m)
        var_hist.append(var_m)
        ratio_hist.append(ratio_m)
        disag_hist.append(dis)
        n_total += n_batches
        print(f"[{arm}][train] {year} epoch={ep + 1}/{epochs} loss={loss_m:.6f} "
              f"bce={bce_m:.6f} penalty={pen_m:.6e} member_var={var_m:.6e} "
              f"lam_pen_over_bce={ratio_m:.3e} probe_dis={dis['pairwise_disagreement_rate']:.6f} "
              f"probe_std={dis['mean_member_std']:.6f} n_batches={n_batches}", flush=True)
    return {
        "optimizer_type": "SGD",
        "lambda": lam,
        "epoch_mean_loss": loss_hist,
        "epoch_mean_bce": bce_hist,
        "epoch_mean_penalty": pen_hist,
        "epoch_mean_member_variance": var_hist,
        "epoch_mean_abs_lambda_penalty_over_bce": ratio_hist,
        "penalty_identity": "mean_i p_i = -Var_i(s_i)（ddof=0，总体方差）",
        "penalty_scale_note": "λ 无直接文献依据，按冻结设计登记为任务化设定",
        "epoch_disagreement": disag_hist,
        "n_batches": n_total,
    }


def load_uniform_disagreement() -> dict[str, float] | None:
    """读取 uniform tabm4 的 2023/2024 pairwise 不一致率（只读参照）。"""
    if not UNIFORM_DIAG.is_file():
        return None
    d = json.loads(UNIFORM_DIAG.read_text(encoding="utf-8"))
    return {str(y): float(d["years"][str(y)]["pairwise_disagreement_rate"])
            for y in (2023, 2024)}


def member_stats(members: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    """单年度成员分歧与集成读数（与 member-disagreement-diag 同口径）。"""
    ens = members.mean(axis=1)
    std = np.std(members, axis=1, ddof=0)
    pos = y == 1
    neg = y == 0
    return {
        "n": int(y.size),
        "n_pos": int(pos.sum()),
        "n_neg": int(neg.sum()),
        "f1_per_member": [f1_of(y, members[:, i]) for i in range(members.shape[1])],
        "f1_ensemble": f1_of(y, ens),
        "mean_member_std": float(np.mean(std)),
        "member_std_pos": float(np.mean(std[pos])) if pos.any() else None,
        "member_std_neg": float(np.mean(std[neg])) if neg.any() else None,
        "auc_per_member": [float(roc_auc_score(y, members[:, i].astype(np.float64)))
                           for i in range(members.shape[1])],
        "auc_ensemble": float(roc_auc_score(y, ens.astype(np.float64))),
        "mean_ensemble_score": float(np.mean(ens)),
        "pairwise_disagreement_rate": pairwise_disagreement_rate(members, THRESHOLD),
        "threshold": THRESHOLD,
    }


def auc_oracle_check(preds: dict[int, dict[str, np.ndarray]]) -> dict[str, Any]:
    """2023/2024 的 delta_auc（vs base 分数）与自身 oracle 余量（披露项）。"""
    out: dict[str, Any] = {}
    for year in (2023, 2024):
        y_arm = preds[year]["y_true"].astype(np.int8)
        s_arm = preds[year]["y_score"].astype(np.float64)
        zb = np.load(BASE_DIR / f"preds_base_{year}.npz")
        y_base = zb["y_true"].astype(np.int8)
        s_base = zb["y_score"].astype(np.float64)
        if not np.array_equal(y_arm, y_base):
            raise RuntimeError(f"{year}: 臂与 base 的 y_true 不一致，无法配对")
        auc_arm = float(roc_auc_score(y_arm, s_arm))
        auc_base = float(roc_auc_score(y_base, s_base))
        f1_arm = f1_of(y_arm, s_arm)
        f1_base = f1_of(y_base, s_base)
        oracle_arm, tau_arm = posthoc.oracle_f1(s_arm, y_arm)
        oracle_base, _tau_base = posthoc.oracle_f1(s_base, y_base)
        out[str(year)] = {
            "auc_arm": auc_arm,
            "auc_base": auc_base,
            "delta_auc": auc_arm - auc_base,
            "f1_arm": f1_arm,
            "f1_base": f1_base,
            "delta_f1_pp": (f1_arm - f1_base) * 100.0,
            "oracle_f1_arm": oracle_arm,
            "oracle_tau_arm": tau_arm,
            "oracle_margin_arm_pp": (oracle_arm - f1_arm) * 100.0,
            "oracle_margin_base_pp": (oracle_base - f1_base) * 100.0,
            "base_preds": f"runs/diagnostics/ch4-lamda-paat-pilot/preds_base_{year}.npz",
        }
    return out


def run_arm(arm: str) -> int:
    if arm not in ARMS:
        raise ValueError(arm)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    is_ncl = arm in NCL_ARMS
    lam = NCL_LAMBDA.get(arm)
    print(f"[arm] {arm} kind={'NCL' if is_ncl else 'D0'} lambda={lam} "
          f"k={K} device={DEVICE.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"seed={SEED} threshold={THRESHOLD}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in YEARS}
    input_dim = int(store[YEARS[0]][0].shape[1])
    rng = np.random.default_rng(SEED)          # 训练洗牌流（与既有先导同源）
    buf_rng = np.random.default_rng(SEED)      # build_parts 流
    member_rng = np.random.default_rng(SEED)   # D0 成员抽样流（独立）

    model = TabMMLP(input_dim, K).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] k={K} params={n_params:,}", flush=True)

    current_year_f1: dict[str, float] = {}
    preds: dict[int, dict[str, np.ndarray]] = {}
    train_logs: dict[str, dict[str, Any]] = {}
    disagreement: dict[str, float] = {}
    members_2024: np.ndarray | None = None
    y_2024: np.ndarray | None = None
    mem_vs_mean_diff: float | None = None
    t0 = time.time()

    for idx, year in enumerate(YEARS):
        x_curr, y_curr = store[year]
        parts, _meta = build_parts(store, YEARS, idx, x_curr, y_curr, buf_rng)
        n_rows = int(sum(p[0].shape[0] for p in parts))
        pos_rows = int(sum(int((p[1] == 1).sum()) for p in parts))
        probe_idx = epoch_probe_indices(int(x_curr.shape[0]))
        x_probe = x_curr[probe_idx]
        print(f"[parts] {year}: rows={n_rows:,} pos={pos_rows:,} "
              f"pos_rate={pos_rows / max(n_rows, 1):.4f} "
              f"probe_rows={x_probe.shape[0]:,}", flush=True)

        t_epoch = time.time()
        if is_ncl:
            train_logs[str(year)] = train_epochs_ncl(
                model, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng, arm, year, float(lam),
                x_probe)
        else:
            train_logs[str(year)] = train_epochs_train_single(
                model, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng, member_rng, arm, year,
                x_probe)
        del parts, x_probe

        xt, yt = ch3.load_year(year, "test")
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        current_year_f1[str(year)] = float(m["f1"])
        print(f"[{year}] current_f1={m['f1']:.4f} ({time.time() - t_epoch:.0f}s)",
              flush=True)

        if idx == len(YEARS) - 1:
            for ty in YEARS:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE)
                preds[ty] = {"y_true": yt.astype(np.int8),
                             "y_score": sc.astype(np.float32)}
                if ty in (2023, 2024):
                    mem = score_members(model, xt, ch3.OFFICIAL_BATCH, DEVICE)
                    disagreement[str(ty)] = pairwise_disagreement_rate(mem, THRESHOLD)
                    if ty == 2024:
                        members_2024 = mem
                        y_2024 = preds[ty]["y_true"]
                        mem_vs_mean_diff = float(np.max(np.abs(
                            mem.mean(axis=1) - preds[ty]["y_score"])))
                del xt, yt
        else:
            del xt, yt

    backward_f1 = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"])
                   for ty in YEARS}
    mean_f1 = float(np.mean(list(backward_f1.values())))
    auc_oracle = auc_oracle_check(preds)

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    for ty, d in preds.items():
        save_npz(RUN_DIR / f"preds_{arm}_{ty}.npz",
                 y_true=d["y_true"], y_score=d["y_score"],
                 threshold=np.float32(THRESHOLD))
    members_path = RUN_DIR / f"preds_{arm}_2024_members.npz"
    if members_2024 is not None and y_2024 is not None:
        save_npz(members_path, y_true=y_2024, members=members_2024.astype(np.float32),
                 threshold=np.float32(THRESHOLD))

    uni_dis = load_uniform_disagreement()
    uni_2024 = uni_dis["2024"] if uni_dis else None
    uni_2023 = uni_dis["2023"] if uni_dis else None
    rate_2024 = disagreement.get("2024")
    rate_2023 = disagreement.get("2023")
    raised_2024 = bool(rate_2024 > uni_2024) if (rate_2024 is not None
                                                 and uni_2024 is not None) else None

    d_2023 = (backward_f1["2023"] - UNIFORM_F1_2023) * 100.0
    d_2024 = (backward_f1["2024"] - UNIFORM_F1_2024) * 100.0
    d_mean = (mean_f1 - UNIFORM_MEAN) * 100.0
    support_2023 = bool(d_2023 >= SUPPORT_DELTA_PP)
    support_2024 = bool(d_2024 >= SUPPORT_DELTA_PP)
    support_mean12 = bool(d_mean >= SUPPORT_MEAN_MIN_PP)
    support = bool(support_2023 and support_2024 and support_mean12)

    if is_ncl:
        mechanism: dict[str, Any] = {
            "form": "NCL",
            "lambda": lam,
            "train_loss": "mean_i BCE(s_i,y) + lambda * mean_i p_i",
            "penalty_definition": "p_i = (s_i - s_bar) * sum_{j!=i}(s_j - s_bar)",
            "penalty_identity": "mean_i p_i = -Var_i(s_i)（ddof=0）；最小化等价于增大成员方差",
            "lambda_source": "无直接文献依据；任务化设定（冻结设计 §二）",
            "year_conditioning": "无（全局）",
            "eval_contract": "4 成员概率平均（model(x) 返回均值；ch3.evaluate/score_shard 同合同）",
            "disagreement_2024_rule": ("必须高于 uniform；不升 = 机制未按宣称方式起作用，"
                                       "即使 F1 过门也只标「增益来源不明」"),
        }
    else:
        mechanism = {
            "form": "D0",
            "train_loss": "每批由独立 rng 均匀抽 1 个成员，计算该成员 BCE",
            "member_rng": "np.random.default_rng(42)，与训练洗牌流分离",
            "year_conditioning": "无（全局）",
            "eval_contract": "4 成员概率平均（model(x) 返回均值；ch3.evaluate/score_shard 同合同）",
            "note": "训练通道诊断，不承担机制存废，结果只登记",
        }
    mechanism.update({
        "epoch_disagreement_probe": {
            "source": "当前年度训练池（x_curr）的固定等距子样本，≤4096 行；不使用标签",
            "index_rule": "np.linspace(0, n-1, min(n, 4096)).round()；无 RNG，不随 epoch 变化",
            "model_mode": "eval（关闭 Dropout；不消耗训练 RNG、不更新参数，训练轨迹不变）",
            "metrics": ["pairwise_disagreement_rate（0.5 判定，成员对均值）", "mean_member_std"],
            "field": "train_logs[year].epoch_disagreement（每年 10 点）",
        },
        "disagreement": {
            "2023": rate_2023,
            "2024": rate_2024,
            "uniform_2023": uni_2023,
            "uniform_2024": uni_2024,
            "delta_2024": (rate_2024 - uni_2024) if (rate_2024 is not None
                                                    and uni_2024 is not None) else None,
            "raised_2024": raised_2024,
            "uniform_source": "runs/diagnostics/ch4-lamda-tabm-pilot/member-disagreement-diag.json",
        },
        "member_stats_2024": (member_stats(members_2024, y_2024)
                              if members_2024 is not None and y_2024 is not None else None),
        "members_2024_npz": (f"runs/diagnostics/ch4-lamda-ncl-pilot/"
                             f"preds_{arm}_2024_members.npz"
                             if members_2024 is not None else None),
        "member_mean_vs_saved_score_max_abs_diff": mem_vs_mean_diff,
    })

    payload: dict[str, Any] = {
        "schema_version": "ch4-ncl-pilot-arm-v1",
        "design_doc": DESIGN_DOC,
        "arm": arm,
        "kind": "NCL" if is_ncl else "D0",
        "k": K,
        "n_params": n_params,
        "device": DEVICE.type,
        "mechanism": mechanism,
        "protocol": {
            "domain_years": YEARS, "epochs": ch3.OFFICIAL_EPOCHS,
            "batch": ch3.OFFICIAL_BATCH, "lr": ch3.OFFICIAL_LR,
            "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
            "memory": ch3.OFFICIAL_MEMORY, "seed": SEED, "threshold": THRESHOLD,
            "optimizer_lifetime": "per_year_rebuild_inside_train_fn",
            "parts_source": "ch4_lamda_training_process_2x2.build_parts",
            "batch_stream": "ch3.iterate_batches_parts（标准一维标签）",
            "data_root": str(ch3.DATA_ROOT),
        },
        "mean_f1": mean_f1,
        "f1_2023": backward_f1["2023"],
        "f1_2024": backward_f1["2024"],
        "backward_f1": backward_f1,
        "current_year_f1": current_year_f1,
        "criteria": {
            "reference_uniform_tabm4": {
                "mean_f1": UNIFORM_MEAN,
                "f1_2023": UNIFORM_F1_2023,
                "f1_2024": UNIFORM_F1_2024,
            },
            "delta_2023_pp": d_2023,
            "delta_2024_pp": d_2024,
            "delta_mean12_pp": d_mean,
            "support_2023": support_2023,
            "support_2024": support_2024,
            "support_mean12": support_mean12,
            "support": support,
            "criteria_applicable": bool(is_ncl),
            "thresholds": {
                "year_delta_pp": SUPPORT_DELTA_PP,
                "mean12_min_pp": SUPPORT_MEAN_MIN_PP,
            },
            "verdict": (("support" if support else "not_support") if is_ncl
                        else "register_only"),
            "verdict_note": (
                "NCL 支持判据：2023/2024 各 >= +0.5 pp 且 12y mean >= uniform − 0.20 pp"
                if is_ncl else
                "D0 为训练通道诊断，不承担机制存废；布尔值仅作披露"
            ),
            "auc_oracle_check": auc_oracle,
        },
        "train_logs": train_logs,
        "wall_seconds": round(time.time() - t0, 1),
        "ts": now_utc(),
    }
    write_json(RUN_DIR / f"{arm}-result.json", payload)
    print(f"[criteria] d2023={d_2023:+.2f}pp d2024={d_2024:+.2f}pp "
          f"dmean={d_mean:+.2f}pp support={support} "
          f"applicable={is_ncl}", flush=True)
    print(f"[disagreement] 2023={rate_2023} 2024={rate_2024} "
          f"uniform_2024={uni_2024} raised={raised_2024}", flush=True)
    print(f"[auc_oracle] {json.dumps(auc_oracle, ensure_ascii=False)}", flush=True)
    print(f"=== {arm}: 12y mean={mean_f1:.10f} | 2023={backward_f1['2023']:.6f} "
          f"2024={backward_f1['2024']:.6f} | {payload['wall_seconds']:.0f}s ===",
          flush=True)
    maybe_comparison()
    return 0


def maybe_comparison() -> None:
    """汇总已完成臂；三臂齐备时机械执行冻结的 NCL 择优规则。"""
    res: dict[str, Any] = {}
    for arm in ARMS:
        p = RUN_DIR / f"{arm}-result.json"
        if p.is_file():
            res[arm] = json.loads(p.read_text(encoding="utf-8"))
    if not res:
        return

    arms_summary: dict[str, Any] = {}
    for arm, r in res.items():
        c = r["criteria"]
        traj = r["train_logs"]["2024"]["epoch_disagreement"]
        rates = [d["pairwise_disagreement_rate"] for d in traj]
        stds = [d["mean_member_std"] for d in traj]
        arms_summary[arm] = {
            "kind": r["kind"],
            "mean_f1": r["mean_f1"],
            "f1_2023": r["f1_2023"],
            "f1_2024": r["f1_2024"],
            "delta_2023_pp": c["delta_2023_pp"],
            "delta_2024_pp": c["delta_2024_pp"],
            "delta_mean12_pp": c["delta_mean12_pp"],
            "support": c["support"],
            "criteria_applicable": c["criteria_applicable"],
            "support_components": {
                "2023": c["support_2023"],
                "2024": c["support_2024"],
                "mean12": c["support_mean12"],
            },
            "verdict": c["verdict"],
            "disagreement_2024": r["mechanism"]["disagreement"]["2024"],
            "disagreement_2024_raised": r["mechanism"]["disagreement"]["raised_2024"],
            "epoch_disagreement_2024": {
                "rates": rates,
                "mean_member_std": stds,
                "first": rates[0],
                "last": rates[-1],
                "delta_first_to_last": rates[-1] - rates[0],
            },
            "auc_oracle_check": c["auc_oracle_check"],
        }

    comp: dict[str, Any] = {
        "schema_version": "ch4-ncl-pilot-comparison-v1",
        "design_doc": DESIGN_DOC,
        "reference_uniform_tabm4": {
            "mean_f1": UNIFORM_MEAN,
            "f1_2023": UNIFORM_F1_2023,
            "f1_2024": UNIFORM_F1_2024,
            "preds_dir": "runs/diagnostics/ch4-lamda-tabm-pilot",
            "disagreement_2024": (load_uniform_disagreement() or {}).get("2024"),
        },
        "criteria_text": {
            "ncl_support": ("ncl05 与 ncl2 分别判定：2023 与 2024 相对 uniform tabm4 "
                            "各 >= +0.5 pp，且 12 年平均 >= uniform − 0.20 pp"),
            "d0": "非存废，只登记；D0 的 12 年读数与 tabm4 之差 = 训练通道直接估计",
            "selection": ("若两臂均过支持判据，取 2024 增量高者；若仅一臂过，取该臂；"
                          "均不过 -> NCL 关闭"),
            "mechanism": ("2024 pairwise 不一致率必须上升（uniform 为 0.21%）；"
                          "不升 = 机制未按宣称方式起作用，即使 F1 过门也只标「增益来源不明」"),
        },
        "arms": arms_summary,
        "status": "partial",
        "ts": now_utc(),
    }

    if all(arm in res for arm in ARMS):
        d0 = res["train_single"]
        comp["d0_training_channel"] = {
            "description": "D0 训练通道诊断，非机制；与 uniform tabm4 对照",
            "d0_mean_f1": d0["mean_f1"],
            "uniform_mean_f1": UNIFORM_MEAN,
            "d0_minus_tabm4_mean12_pp": d0["criteria"]["delta_mean12_pp"],
            "tabm4_minus_d0_mean12_pp": -d0["criteria"]["delta_mean12_pp"],
            "dual_channel_account_pp": DUAL_CHANNEL_ACCOUNT_PP,
            "difference_from_account_pp": (-d0["criteria"]["delta_mean12_pp"]
                                           - DUAL_CHANNEL_ACCOUNT_PP),
            "d0_delta_2023_pp": d0["criteria"]["delta_2023_pp"],
            "d0_delta_2024_pp": d0["criteria"]["delta_2024_pp"],
        }

        mech_arms: dict[str, Any] = {}
        for arm in NCL_ARMS:
            dis = res[arm]["mechanism"]["disagreement"]
            mech_arms[arm] = {
                "rate_2023": dis["2023"],
                "rate_2024": dis["2024"],
                "uniform_2024": dis["uniform_2024"],
                "delta_2024": dis["delta_2024"],
                "raised_2024": dis["raised_2024"],
            }
        comp["ncl_mechanism_check"] = {
            "rule": "2024 pairwise 不一致率必须上升（uniform 为 0.21%）",
            "uniform_2024": (load_uniform_disagreement() or {}).get("2024"),
            "arms": mech_arms,
            "all_ncl_raised": all(mech_arms[a]["raised_2024"] is True for a in NCL_ARMS),
        }

        eligible = [a for a in NCL_ARMS if res[a]["criteria"]["support"]]
        if len(eligible) == 1:
            selected: str | None = eligible[0]
            outcome = "select"
            reason = f"恰一臂通过支持判据：{selected}"
        elif len(eligible) == 2:
            selected = max(eligible,
                           key=lambda a: res[a]["criteria"]["delta_2024_pp"])
            outcome = "select_higher_2024"
            reason = f"两臂通过支持判据，取 2024 增量高者：{selected}"
        else:
            selected = None
            outcome = "ncl_closed"
            reason = "两臂均未通过支持判据，NCL 关闭"

        if selected is not None:
            verified = res[selected]["mechanism"]["disagreement"]["raised_2024"]
            gain_source = ("mechanism_verified" if verified is True
                           else "gain_source_unclear")
            gain_note = ("2024 不一致率上升，机制按宣称方式起作用" if verified is True
                         else "2024 不一致率未上升，增益来源不明（机制核查未通过）")
        else:
            gain_source = None
            gain_note = None
        comp["selection"] = {
            "eligible_arms": eligible,
            "selected": selected,
            "outcome": outcome,
            "reason": reason,
            "gain_source_label": gain_source,
            "gain_source_note": gain_note,
            "rule": "两臂均过 -> 取 2024 增量高者；仅一臂过 -> 取该臂；均不过 -> NCL 关闭",
        }
        comp["status"] = "complete"

    write_json(RUN_DIR / "ncl-comparison.json", comp)
    if comp["status"] == "complete":
        sel = comp["selection"]
        print(f"[selection] selected={sel['selected']} outcome={sel['outcome']} "
              f"gain_source={sel['gain_source_label']} reason={sel['reason']}",
              flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章 NCL 负相关先导（三臂）")
    parser.add_argument("--arm", choices=ARMS, required=True)
    args = parser.parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return run_arm(args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
