#!/usr/bin/env python
"""第四章 机制二第三轮：成对相关惩罚先导（corr05 / corr10 两臂串行）。

判据与臂定义冻结于 `thesis/methods/第四章-成对相关惩罚先导设计.md`
（2026-10-21，看到任何读数之前）。本脚本只实现，不改判据、λ 或臂定义；
**第三轮即最终轮**：两臂皆败则机制二关闭、章级设计重构，无第四轮。

两臂（uniform tabm4 为参照，只读其既有制品，不重跑）：

- corr05（λ=0.5）、corr10（λ=1.0）；
  L = (1/k) Σ_i BCE(s_i, y) + λ·(2/(k(k−1))) Σ_{i<j} r_P(s_i, s_j)，

其中 r_P 为**批内跨样本**的成员分数 Pearson 相关（N=batch 内样本数）：

    r_P(u,v) = Σ_n (u_n−ū)(v_n−v̄) / sqrt(Σ_n (u_n−ū)² · Σ_n (v_n−v̄)²)

**零方差批处理（实现披露）**：分母加 ε=1e-8 防止除零；若某成员在当前批内的
分数完全相同时，其方差恰为 0，与它相关的成员对定义 r_P=0 并跳过（不计入该对
的梯度），避免常数向量之间的相关无定义。正常批内不会触发该分支。

协议骨架逐位复用 `ch4_lamda_ncl_pilot`：`TabMMLP`、`f1_of`、优化器年度重建、
`build_parts`（来自 2x2 模块）、`ch3` 的评测/打分函数与协议常量、批次流
`ch3.iterate_batches_parts`、成员逐项分数与分歧率口径
（`ch4_lamda_member_disagreement_diag`）、自身 oracle 余量
（`ch4_lamda_posthoc_prior_diag.oracle_f1`）。种子、批流、parts 构造与 uniform
逐位一致，故与参照的差异只来自损失项。

逐 epoch 成员分歧探针（S1'）：每个 epoch 结束后，在当前年度训练池（`x_curr`）
的固定等距子样本（≤4096 行，不使用标签，eval 模式、不消耗 Dropout RNG、
不更新参数）上计算 4 成员分数的 pairwise 不一致率（0.5 判定）与平均成员标准差，
写入 `train_logs[year].epoch_disagreement`（每年 10 点）。

运行（每臂约 860 s，两臂串行）：
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_corr_pilot.py --arm corr05
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_corr_pilot.py --arm corr10
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

RUN_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-corr-pilot"
BASE_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-paat-pilot"
UNIFORM_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-tabm-pilot"
UNIFORM_DIAG = UNIFORM_DIR / "member-disagreement-diag.json"
DESIGN_DOC = "thesis/methods/第四章-成对相关惩罚先导设计.md"

ARMS = ("corr05", "corr10")
CORR_LAMBDA = {"corr05": 0.5, "corr10": 1.0}
EPS = 1e-8                 # Pearson 分母的防零方差常数（冻结设计 §一）

# 参照：uniform tabm4 既有制品（只读；不重跑）
UNIFORM_MEAN = 0.832346367494066
UNIFORM_F1_2023 = 0.8681241184767278
UNIFORM_F1_2024 = 0.7703703703703704
UNIFORM_DISAGREEMENT_2024 = 0.002082042810929864  # 0.2082%

# 冻结判据（设计文档 §三）
SUPPORT_DELTA_PP = 0.5          # 2023 与 2024 各 >= +0.5 pp
SUPPORT_MEAN_MIN_PP = -0.20     # 12 年平均 >= uniform − 0.20 pp
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


def pearson_pairwise_penalty(s: torch.Tensor, eps: float = EPS) -> torch.Tensor:
    """批内跨样本成员分数 Pearson 相关的成对均值。

    s: (B, k) 的成员概率，B=batch 内样本数、k=成员数。按样本维中心化后，

        cov_ij = (1/B) Σ_n (s_ni−s̄_i)(s_nj−s̄_j)
        r_ij   = cov_ij / (sqrt(var_i·var_j) + ε)

    返回 (2/(k(k−1))) Σ_{i<j} r_ij。最小化该项即压低成员间跨样本相关。

    零方差处理：某成员在当前批内分数完全相同时 var_i=0，其与任意成员的
    Pearson 相关无定义；该对**定义 r=0 并跳过**（梯度不进入该对），
    其余对仍按全部 k(k−1)/2 个对的归一化计入。

    数值形式：ε 加在**开方之前**（分母 = sqrt((var_i+ε)(var_j+ε))），
    与「分母加 ε」语义一致，且避免 `sqrt(0)` 的无限导数把 NaN 写进参数
    （首次实现曾因此在 2025 年饱和批上发散，已按设计要求的零方差跳过语义修正）。
    ε=1e-8 不改变正常批读数（var≫ε 时相对偏差 ~1e-6 量级）。
    """
    b, k = s.shape
    if b < 2 or k < 2:
        return s.new_zeros(())
    d = s - s.mean(dim=0, keepdim=True)          # (B,k) 按样本维中心化
    cov = d.t() @ d / b                          # (k,k) 总体协方差（ddof=0）
    var = torch.diagonal(cov)                    # (k,)
    std = torch.sqrt(var + eps)                  # 有限导数；零方差成员为 sqrt(ε)
    denom = std.unsqueeze(0) * std.unsqueeze(1)
    r = cov / denom                              # (k,k)
    valid = var > 0                              # 完全常数的成员 → 相关无定义
    pair_valid = valid.unsqueeze(0) & valid.unsqueeze(1)
    r = torch.where(pair_valid, r, torch.zeros_like(r))
    mask = torch.triu(torch.ones(k, k, dtype=s.dtype, device=s.device), diagonal=1)
    pair_count = k * (k - 1) / 2
    return (r * mask).sum() / pair_count


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


def train_epochs_corr(model: TabMMLP, parts, epochs: int, device: torch.device,
                      rng: np.random.Generator, arm: str, year: int,
                      lam: float, x_probe: np.ndarray) -> dict[str, Any]:
    """成对相关惩罚：L = mean_i BCE(s_i,y) + λ·mean_{i<j} r_P(s_i,s_j)。

    优化器年度重建、批次流与 NCL/uniform 逐位一致；唯一差别是损失项。
    """
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    model.train()
    loss_hist: list[float] = []
    bce_hist: list[float] = []
    corr_hist: list[float] = []
    ratio_hist: list[float] = []
    zero_var_pairs: list[int] = []
    disag_hist: list[dict[str, Any]] = []
    n_total = 0
    for ep in range(epochs):
        loss_sum = torch.zeros((), device=device)
        bce_sum = torch.zeros((), device=device)
        corr_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)          # (B,1)
            opt.zero_grad()
            out = model(xt, return_members=True)                       # (B,k,1)
            target = yt.unsqueeze(1).expand(-1, model.k, -1)           # (B,k,1)
            elem = F.binary_cross_entropy(out, target, reduction="none").squeeze(-1)
            bce = elem.mean()                                          # mean_i BCE_i
            s = out.squeeze(-1)                                        # (B,k)
            corr = pearson_pairwise_penalty(s)                         # mean_{i<j} r_P
            loss = bce + lam * corr
            with torch.no_grad():
                loss_sum = loss_sum + loss.detach()
                bce_sum = bce_sum + bce.detach()
                corr_sum = corr_sum + corr.detach()
                if model.k > 1:
                    var = s.var(dim=0, unbiased=False)
                    n_zero = int((var <= 0).sum().item())
                    if n_zero:
                        zero_var_pairs.append(n_zero)
            n_batches += 1
            loss.backward()
            opt.step()
        loss_m = float(loss_sum.item() / max(n_batches, 1))
        bce_m = float(bce_sum.item() / max(n_batches, 1))
        corr_m = float(corr_sum.item() / max(n_batches, 1))
        ratio_m = abs(lam * corr_m) / max(abs(bce_m), 1e-12)
        dis = probe_epoch_disagreement(model, x_probe, device)
        dis["epoch"] = ep + 1
        loss_hist.append(loss_m)
        bce_hist.append(bce_m)
        corr_hist.append(corr_m)
        ratio_hist.append(ratio_m)
        disag_hist.append(dis)
        n_total += n_batches
        print(f"[{arm}][train] {year} epoch={ep + 1}/{epochs} loss={loss_m:.6f} "
              f"bce={bce_m:.6f} corr={corr_m:.6e} lam_abs_corr_over_bce={ratio_m:.3e} "
              f"probe_dis={dis['pairwise_disagreement_rate']:.6f} "
              f"probe_std={dis['mean_member_std']:.6f} n_batches={n_batches}", flush=True)
    return {
        "optimizer_type": "SGD",
        "lambda": lam,
        "epoch_mean_loss": loss_hist,
        "epoch_mean_bce": bce_hist,
        "epoch_mean_pearson_corr": corr_hist,
        "epoch_mean_abs_lambda_corr_over_bce": ratio_hist,
        "zero_variance_event_batches": len(zero_var_pairs),
        "zero_variance_rule": "某成员批内分数完全相同时 var=0，其所在成员对 r_P 定义为 0 并跳过",
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
    lam = CORR_LAMBDA[arm]
    print(f"[arm] {arm} kind=corr lambda={lam} k={K} device={DEVICE.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"seed={SEED} threshold={THRESHOLD} eps={EPS}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in YEARS}
    input_dim = int(store[YEARS[0]][0].shape[1])
    rng = np.random.default_rng(SEED)          # 训练洗牌流（与既有先导同源）
    buf_rng = np.random.default_rng(SEED)      # build_parts 流

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
        train_logs[str(year)] = train_epochs_corr(
            model, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng, arm, year, float(lam),
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
    uni_2024 = uni_dis["2024"] if uni_dis else UNIFORM_DISAGREEMENT_2024
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

    mechanism: dict[str, Any] = {
        "form": "pairwise_pearson_corr",
        "lambda": lam,
        "train_loss": ("mean_i BCE(s_i,y) + lambda * 2/(k(k-1)) * "
                       "sum_{i<j} r_P(s_i,s_j)"),
        "corr_definition": ("批内跨样本 Pearson 相关：s_i 与 s_j 为 N 维向量，"
                            "N=batch 内样本数"),
        "eps": EPS,
        "zero_variance_rule": ("分母加 eps 防零方差批；某成员批内分数完全相同时 "
                               "r_P 定义为 0 并跳过该对"),
        "lambda_source": ("Harangi 2023 实测稳定区间 λ=0.5–1；本数据无直接依据，"
                          "按冻结设计登记为任务化设定"),
        "year_conditioning": "无（全局）",
        "eval_contract": ("4 成员概率平均（model(x) 返回均值；"
                          "ch3.evaluate/score_shard 同合同）"),
        "disagreement_2024_rule": ("披露项：须上升（uniform 0.2082%）；不升 = 机制未按"
                                   "宣称方式起作用，即使 F1 过门也只标「增益来源不明」"),
        "epoch_disagreement_probe": {
            "source": ("当前年度训练池（x_curr）的固定等距子样本，≤4096 行；"
                       "不使用标签"),
            "index_rule": ("np.linspace(0, n-1, min(n, 4096)).round()；"
                           "无 RNG，不随 epoch 变化"),
            "model_mode": ("eval（关闭 Dropout；不消耗训练 RNG、不更新参数，"
                           "训练轨迹不变）"),
            "metrics": ["pairwise_disagreement_rate（0.5 判定，成员对均值）",
                        "mean_member_std"],
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
            "uniform_source": ("runs/diagnostics/ch4-lamda-tabm-pilot/"
                               "member-disagreement-diag.json"),
        },
        "member_stats_2024": (member_stats(members_2024, y_2024)
                              if members_2024 is not None and y_2024 is not None else None),
        "members_2024_npz": (f"runs/diagnostics/ch4-lamda-corr-pilot/"
                             f"preds_{arm}_2024_members.npz"
                             if members_2024 is not None else None),
        "member_mean_vs_saved_score_max_abs_diff": mem_vs_mean_diff,
    }

    payload: dict[str, Any] = {
        "schema_version": "ch4-corr-pilot-arm-v1",
        "design_doc": DESIGN_DOC,
        "arm": arm,
        "kind": "CORR",
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
            "thresholds": {
                "year_delta_pp": SUPPORT_DELTA_PP,
                "mean12_min_pp": SUPPORT_MEAN_MIN_PP,
            },
            "verdict": "support" if support else "not_support",
            "verdict_note": ("支持判据：2023 与 2024 相对 uniform tabm4 各 >= +0.5 pp，"
                             "且 12 年平均 >= uniform − 0.20 pp"),
            "auc_oracle_check": auc_oracle,
        },
        "train_logs": train_logs,
        "wall_seconds": round(time.time() - t0, 1),
        "ts": now_utc(),
    }
    write_json(RUN_DIR / f"{arm}-result.json", payload)
    print(f"[criteria] d2023={d_2023:+.2f}pp d2024={d_2024:+.2f}pp "
          f"dmean={d_mean:+.2f}pp support={support}", flush=True)
    print(f"[disagreement] 2023={rate_2023} 2024={rate_2024} "
          f"uniform_2024={uni_2024} raised={raised_2024}", flush=True)
    print(f"[auc_oracle] {json.dumps(auc_oracle, ensure_ascii=False)}", flush=True)
    print(f"=== {arm}: 12y mean={mean_f1:.10f} | 2023={backward_f1['2023']:.6f} "
          f"2024={backward_f1['2024']:.6f} | {payload['wall_seconds']:.0f}s ===",
          flush=True)
    maybe_comparison()
    return 0


def maybe_comparison() -> None:
    """汇总已完成臂；两臂齐备时机械执行冻结的择优规则。

    outcome 取值（任务预登记）：
    - `corr_selected`：至少一臂通过支持判据，按规则选出臂；
    - `round3_fail_chapter_restructure`：两臂均败，机制二关闭，章级设计重构（无第四轮）。
    """
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
            "lambda": r["mechanism"]["lambda"],
            "mean_f1": r["mean_f1"],
            "f1_2023": r["f1_2023"],
            "f1_2024": r["f1_2024"],
            "delta_2023_pp": c["delta_2023_pp"],
            "delta_2024_pp": c["delta_2024_pp"],
            "delta_mean12_pp": c["delta_mean12_pp"],
            "support": c["support"],
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
        "schema_version": "ch4-corr-pilot-comparison-v1",
        "design_doc": DESIGN_DOC,
        "reference_uniform_tabm4": {
            "mean_f1": UNIFORM_MEAN,
            "f1_2023": UNIFORM_F1_2023,
            "f1_2024": UNIFORM_F1_2024,
            "disagreement_2024": (load_uniform_disagreement() or {}).get(
                "2024", UNIFORM_DISAGREEMENT_2024),
            "preds_dir": "runs/diagnostics/ch4-lamda-tabm-pilot",
        },
        "criteria_text": {
            "support": ("2023 与 2024 相对 uniform tabm4 各 >= +0.5 pp，"
                        "且 12 年平均 >= uniform − 0.20 pp"),
            "selection": ("若两臂均过支持判据，取 2024 增量高者；若仅一臂过，取该臂；"
                          "均不过 -> 机制二关闭，章级设计重构（无第四轮）"),
            "mechanism": ("2024 pairwise 不一致率须上升（uniform 0.2082%）；"
                          "不升 = 增益来源不明"),
        },
        "arms": arms_summary,
        "status": "partial",
        "ts": now_utc(),
    }

    if all(arm in res for arm in ARMS):
        eligible = [a for a in ARMS if res[a]["criteria"]["support"]]
        if len(eligible) == 1:
            selected: str | None = eligible[0]
            reason = f"恰一臂通过支持判据：{selected}"
        elif len(eligible) == 2:
            selected = max(eligible,
                           key=lambda a: res[a]["criteria"]["delta_2024_pp"])
            reason = f"两臂通过支持判据，取 2024 增量高者：{selected}"
        else:
            selected = None
            reason = "两臂均未通过支持判据，机制二关闭，章级设计重构（无第四轮）"

        outcome = "corr_selected" if selected is not None \
            else "round3_fail_chapter_restructure"

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
            "mechanism_2_status": "kept" if selected is not None else "closed",
            "gain_source_label": gain_source,
            "gain_source_note": gain_note,
            "rule": ("两臂均过 -> 取 2024 增量高者；仅一臂过 -> 取该臂；"
                     "均不过 -> 机制二关闭，章级设计重构（预登记，无第四轮）"),
        }
        comp["status"] = "complete"

    write_json(RUN_DIR / "corr-comparison.json", comp)
    if comp["status"] == "complete":
        sel = comp["selection"]
        print(f"[selection] selected={sel['selected']} outcome={sel['outcome']} "
              f"gain_source={sel['gain_source_label']} reason={sel['reason']}",
              flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章成对相关惩罚先导（corr05/corr10）")
    parser.add_argument("--arm", choices=ARMS, required=True)
    args = parser.parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return run_arm(args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
