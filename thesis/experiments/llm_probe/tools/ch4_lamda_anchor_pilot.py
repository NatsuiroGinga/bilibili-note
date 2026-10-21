#!/usr/bin/env python
"""第四章成员-年度锚定先导：三臂串行（c_anchor / a_route2 / c_anti）。

判据、分组与臂定义冻结于 `thesis/methods/第四章-成员年度锚定先导设计.md`
（2026-10-21，看到任何锚定臂读数之前）。本脚本只实现，不改判据、权重比值或分组。
形式化定义见 `thesis/methods/第四章-评测平均刻画与成员年度锚定形式化.md` §3.1、§3.3。

三臂（uniform tabm4 为参照，只读其既有制品，不重跑）：

- c_anchor（形式 C）：组损失加权。年度按 `DOMAIN_YEARS` 索引奇偶分
  G0={2013,2016,2018,2020,2022,2024}、G1={2014,2017,2019,2021,2023,2025}；
  成员 0/1 绑 G0、2/3 绑 G1。属组 w=2、非属组 w=2/3，比值 3:1。
- a_route2（形式 A）：同样的年度组；年 t∈G_j 只训练/评测成员 {2j,2j+1}，
  训练损失只在激活成员上取均值，评测只平均激活成员，k_t≡2。
- c_anti（反向对照）：与 c_anchor 完全相同，仅属组分配取反（0/1 绑 G1、2/3 绑 G0）。

**权重均值口径（设计内部算术冲突的处置，必须披露）**：
设计原文同时写「属组 w=2、非属组 w=2/3」与「权重均值恒为 1」。在 4 成员、每组 2 成员的
冻结分组下，逐样本权重均值 = (2·2 + 2·(2/3))/4 = 4/3，并不等于 1。为同时满足
「比值 3:1」与「总梯度尺度与 uniform 严格一致（均值 1）」，本实现保留原始权重表
（2 与 2/3），并逐样本除以其成员权重均值（常数 4/3）——等价有效权重 1.5/0.5，
比值仍是 3:1、均值恰为 1。原始表、归一化因子与有效权重全部写入结果 JSON。

协议骨架逐位复用 `ch4_lamda_tabm_pilot`：`TabMMLP`、`f1_of`、优化器年度重建、
`build_parts`（来自 2x2 模块）、`ch3` 的评测/打分函数与协议常量。
批次流使用 `ch3.iterate_batches_parts` 的逐行镜像（仅把标签扩为 (y, year_id) 两列并
随同一次置换洗牌），**不改 ch3 任何函数**。

运行（每臂约 900 s，三臂串行）：
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_anchor_pilot.py --arm c_anchor
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_anchor_pilot.py --arm a_route2
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_anchor_pilot.py --arm c_anti
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
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
import ch4_lamda_posthoc_prior_diag as posthoc  # noqa: E402
from ch4_lamda_tabm_bootstrap import (  # noqa: E402  （复用已冻结的配对 bootstrap 实现）
    boot_counts,
    ci,
    classify,
    delta_from_counts,
)
from ch4_lamda_tabm_pilot import TabMMLP, f1_of  # noqa: E402
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = ch3.SEED
THRESHOLD = ch3.THRESHOLD
K = 4
YEARS = list(ch3.DOMAIN_YEARS)

RUN_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-anchor-pilot"
UNIFORM_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-tabm-pilot"

ARMS = ("c_anchor", "a_route2", "c_anti")
ANCHOR_ARMS = ("c_anchor", "a_route2")

# 参照：uniform tabm4 既有制品（只读；不重跑）
UNIFORM_MEAN = 0.832346367494066
UNIFORM_F1_2023 = 0.8681241184767278
UNIFORM_F1_2024 = 0.7703703703703704

# 冻结判据（设计文档 §二）
SUPPORT_DELTA_PP = 0.5          # 2023 与 2024 各 ≥ +0.5 pp
SUPPORT_MEAN_MIN_PP = -0.20     # 12 年平均 ≥ uniform − 0.20 pp
DIRECTION_GAP_PP = 0.5          # C − C' 在 2024 ≥ +0.5 pp

# 年度→组：按 DOMAIN_YEARS 索引奇偶（纯轮转，无标签依赖）
YEAR_GROUP = {year: i % 2 for i, year in enumerate(YEARS)}
GROUP_YEARS = {
    0: [y for y in YEARS if YEAR_GROUP[y] == 0],
    1: [y for y in YEARS if YEAR_GROUP[y] == 1],
}
# 成员→组（形式 C 与 A 的轮转分配）
MEMBER_GROUP_ANCHOR = (0, 0, 1, 1)
MEMBER_GROUP_ANTI = (1, 1, 0, 0)

# 原始权重表（设计冻结值）与逐样本归一化因子
W_IN_GROUP = 2.0
W_OUT_GROUP = 2.0 / 3.0
N_MEMBERS_IN_GROUP = 2
W_RAW_MEAN = (N_MEMBERS_IN_GROUP * W_IN_GROUP
              + (K - N_MEMBERS_IN_GROUP) * W_OUT_GROUP) / K  # = 4/3


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写出：先写 .partial 再 os.replace。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def active_members(year: int) -> tuple[int, int]:
    """形式 A：年 t∈G_j 只激活成员 {2j,2j+1}。"""
    j = YEAR_GROUP[year]
    return 2 * j, 2 * j + 1


def part_years_from_meta(meta: dict[str, Any], years: list[int], idx: int) -> list[int]:
    """从 `build_parts` 的现成年度键恢复每个 part 的来源年。

    `build_parts` 返回 `parts = [(x_curr, y_curr)] + 按 blocks 顺序的复用块`，
    构造顺序与 `reps` 一一对应，故不需新增数据视图。
    """
    out = [years[idx]]
    for yr, _x, _y in meta["blocks"]:
        out += [yr] * int(meta["reps"][yr])
    return out


def augment_parts_with_year(parts: list[tuple[np.ndarray, np.ndarray]],
                            part_years: list[int]) -> list[tuple[np.ndarray, np.ndarray]]:
    """把每个 part 的标签扩为 (N,2)=[y, year_id]，随同一次置换洗牌。"""
    if len(parts) != len(part_years):
        raise RuntimeError(f"parts/part_years 长度不一致：{len(parts)} vs {len(part_years)}")
    out: list[tuple[np.ndarray, np.ndarray]] = []
    for (x, y), yr in zip(parts, part_years):
        n = int(y.shape[0])
        y2 = np.empty((n, 2), dtype=np.float32)
        y2[:, 0] = y.astype(np.float32).reshape(n)
        y2[:, 1] = np.float32(yr)
        out.append((x, y2))
    return out


def iterate_batches_parts_year(parts, batch: int, rng: np.random.Generator, shuffle: bool):
    """`ch3.iterate_batches_parts` 的逐行镜像，仅把标签缓冲扩为 (N,2)。

    全局置换与取批逻辑逐字相同（`rng.permutation(total)` + `searchsorted`），
    因此年度 id 与样本在同一次洗牌中移动；ch3 原函数不被修改。
    """
    dim = parts[0][0].shape[1]
    sizes = np.array([p[0].shape[0] for p in parts])
    cum = np.concatenate([[0], np.cumsum(sizes)])
    total = int(cum[-1])
    idx = rng.permutation(total) if shuffle else np.arange(total)
    for s in range(0, idx.size, batch):
        sel = idx[s : s + batch]
        if sel.size < 2:
            continue
        which = np.searchsorted(cum, sel, side="right") - 1
        xs = np.empty((sel.size, dim), dtype=np.int8)
        ys = np.empty((sel.size, 2), dtype=np.float32)
        for pi in np.unique(which):
            m = which == pi
            loc = sel[m] - cum[pi]
            xs[m] = parts[pi][0][loc]
            ys[m] = parts[pi][1][loc]
        yield xs, ys


def train_epochs_weighted(model: TabMMLP, parts, epochs: int, device: torch.device,
                          rng: np.random.Generator, arm: str, year: int,
                          member_group: tuple[int, int, int, int]) -> dict[str, Any]:
    """形式 C：L = (1/k) Σ_i w_{i,g(x)}·BCE(s_i,y)，逐样本权重均值归一为 1。"""
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss(reduction="none")
    mg = torch.tensor(member_group, dtype=torch.long, device=device)  # (k,)
    w_in = torch.tensor(W_IN_GROUP, dtype=torch.float32, device=device)
    w_out = torch.tensor(W_OUT_GROUP, dtype=torch.float32, device=device)
    model.train()
    loss_hist: list[float] = []
    bce_hist: list[float] = []
    n_total = 0
    for ep in range(epochs):
        loss_sum = torch.zeros((), device=device)
        bce_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in iterate_batches_parts_year(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb[:, 0].copy()).to(device)          # (B,)
            yid = yb[:, 1].astype(np.int64)
            yg = torch.from_numpy(np.array([YEAR_GROUP[int(v)] for v in yid],
                                           dtype=np.int64)).to(device)  # (B,)
            match = mg.unsqueeze(0) == yg.unsqueeze(1)                   # (B,k)
            w = torch.where(match, w_in, w_out)
            w = w / w.mean(dim=1, keepdim=True)                          # 逐样本均值 = 1
            opt.zero_grad()
            out = model(xt, return_members=True)                         # (B,k,1)
            target = yt.unsqueeze(1).unsqueeze(2).expand(-1, model.k, -1)
            elem = criterion(out, target)                                # (B,k,1)
            loss = (elem * w.unsqueeze(2)).mean()
            with torch.no_grad():
                bce_sum = bce_sum + elem.mean()
            loss_sum = loss_sum + loss.detach()
            n_batches += 1
            loss.backward()
            opt.step()
        loss_m = float(loss_sum.item() / max(n_batches, 1))
        bce_m = float(bce_sum.item() / max(n_batches, 1))
        loss_hist.append(loss_m)
        bce_hist.append(bce_m)
        n_total += n_batches
        print(f"[{arm}][train] {year} epoch={ep + 1}/{epochs} loss={loss_m:.6f} "
              f"bce_unweighted={bce_m:.6f} n_batches={n_batches}", flush=True)
    return {
        "optimizer_type": "SGD",
        "epoch_mean_loss": loss_hist,
        "epoch_mean_bce_unweighted": bce_hist,
        "n_batches": n_total,
        "weights": {
            "raw_in_group": W_IN_GROUP,
            "raw_out_group": W_OUT_GROUP,
            "per_sample_raw_mean": W_RAW_MEAN,
            "normalization": "w / mean_i(w)，逐样本；有效权重 1.5 / 0.5，均值 1",
            "effective_in_group": W_IN_GROUP / W_RAW_MEAN,
            "effective_out_group": W_OUT_GROUP / W_RAW_MEAN,
            "ratio": W_IN_GROUP / W_OUT_GROUP,
        },
    }


def train_epochs_routed(model: TabMMLP, parts, epochs: int, device: torch.device,
                        rng: np.random.Generator, arm: str, year: int) -> dict[str, Any]:
    """形式 A：年 t∈G_j 只在成员 {2j,2j+1} 上取 BCE 均值；非激活成员该年无梯度。"""
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss(reduction="none")
    model.train()
    loss_hist: list[float] = []
    n_total = 0
    for ep in range(epochs):
        loss_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in iterate_batches_parts_year(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb[:, 0].copy()).to(device)
            yid = yb[:, 1].astype(np.int64)
            yg = torch.from_numpy(np.array([YEAR_GROUP[int(v)] for v in yid],
                                           dtype=np.int64)).to(device)
            start = 2 * yg                                            # (B,)
            idx = torch.stack([start, start + 1], dim=1)               # (B,2)
            opt.zero_grad()
            out = model(xt, return_members=True)                       # (B,k,1)
            target = yt.unsqueeze(1).unsqueeze(2).expand(-1, model.k, -1)
            elem = criterion(out, target).squeeze(-1)                  # (B,k)
            loss = elem.gather(1, idx).mean()                          # 激活成员均值
            loss_sum = loss_sum + loss.detach()
            n_batches += 1
            loss.backward()
            opt.step()
        loss_m = float(loss_sum.item() / max(n_batches, 1))
        loss_hist.append(loss_m)
        n_total += n_batches
        print(f"[{arm}][train] {year} epoch={ep + 1}/{epochs} loss={loss_m:.6f} "
              f"n_batches={n_batches}", flush=True)
    return {"optimizer_type": "SGD", "epoch_mean_loss": loss_hist, "n_batches": n_total}


@torch.inference_mode()
def evaluate_routed(model: TabMMLP, x: np.ndarray, y: np.ndarray, batch: int,
                    device: torch.device, year: int) -> dict[str, Any]:
    """形式 A 评测：只平均该年激活成员；其余与 `ch3.evaluate` 同型。"""
    model.eval()
    members = torch.tensor(active_members(year), dtype=torch.long, device=device)
    preds, labels = [], []
    for xb, yb in ch3.iterate_batches(x, y, batch, np.random.default_rng(0), False):
        xt = torch.from_numpy(xb.astype(np.float32)).to(device)
        out = model(xt, return_members=True).squeeze(-1)               # (B,k)
        s = out[:, members].mean(dim=1)
        preds.append((s >= THRESHOLD).cpu().numpy().astype(int))
        labels.append(yb.astype(int))
    p = np.concatenate(preds) if preds else np.zeros(0, dtype=int)
    lab = np.concatenate(labels) if labels else np.zeros(0, dtype=int)
    return {
        "accuracy": float(accuracy_score(lab, p)),
        "precision": float(precision_score(lab, p, zero_division=0)),
        "recall": float(recall_score(lab, p, zero_division=0)),
        "f1": float(f1_score(lab, p, zero_division=0)),
        "n": int(lab.size), "n_pos": int((lab == 1).sum()),
    }


@torch.inference_mode()
def score_shard_routed(model: TabMMLP, x: np.ndarray, batch: int,
                       device: torch.device, year: int) -> np.ndarray:
    """形式 A 逐样本打分：只平均该年激活成员，按原始顺序返回。"""
    model.eval()
    members = torch.tensor(active_members(year), dtype=torch.long, device=device)
    dummy = np.zeros(x.shape[0], dtype=np.float32)
    out = []
    for xb, _ in ch3.iterate_batches(x, dummy, batch, np.random.default_rng(0), False):
        xt = torch.from_numpy(xb.astype(np.float32)).to(device)
        s = model(xt, return_members=True).squeeze(-1)[:, members].mean(dim=1)
        out.append(s.cpu().numpy())
    return np.concatenate(out).astype(np.float32) if out else np.zeros(0, dtype=np.float32)


def load_uniform_preds(year: int) -> tuple[np.ndarray, np.ndarray]:
    z = np.load(UNIFORM_DIR / f"preds_tabm4_{year}.npz")
    return z["y_true"].astype(np.int8), z["y_score"].astype(np.float64)


def auc_check(arm_preds: dict[int, dict[str, np.ndarray]]) -> dict[str, Any]:
    """2023/2024 的 delta_auc 与 oracle 余量（披露项，设计文档 §二「机制核查」）。"""
    out: dict[str, Any] = {}
    for year in (2023, 2024):
        y_arm = arm_preds[year]["y_true"].astype(np.int8)
        s_arm = arm_preds[year]["y_score"].astype(np.float64)
        y_uni, s_uni = load_uniform_preds(year)
        if not np.array_equal(y_arm, y_uni):
            raise RuntimeError(f"{year}: 臂与 uniform 的 y_true 不一致，无法配对")
        auc_arm = float(posthoc.roc_auc_score(y_arm, s_arm))
        auc_uni = float(posthoc.roc_auc_score(y_uni, s_uni))
        f1_arm = f1_of(y_arm, s_arm)
        f1_uni = f1_of(y_uni, s_uni)
        oracle_arm, tau_arm = posthoc.oracle_f1(s_arm, y_arm)
        oracle_uni, _tau_uni = posthoc.oracle_f1(s_uni, y_uni)
        margin_arm = (oracle_arm - f1_arm) * 100.0
        margin_uni = (oracle_uni - f1_uni) * 100.0
        delta_f1_pp = (f1_arm - f1_uni) * 100.0
        out[str(year)] = {
            "auc_arm": auc_arm,
            "auc_uniform": auc_uni,
            "delta_auc": auc_arm - auc_uni,
            "f1_arm": f1_arm,
            "f1_uniform": f1_uni,
            "delta_f1_pp": delta_f1_pp,
            "oracle_f1_arm": oracle_arm,
            "oracle_tau_arm": tau_arm,
            "oracle_margin_arm_pp": margin_arm,
            "oracle_margin_uniform_pp": margin_uni,
            # 设计 §二：增益须高于 uniform 自身阈值上界（2024 实测 +0.63 pp）
            "gain_exceeds_uniform_oracle_margin": bool(delta_f1_pp > margin_uni),
        }
    return out


def bootstrap_2024(arm_preds: dict[int, dict[str, np.ndarray]]) -> dict[str, Any]:
    """2024 单年配对 bootstrap（同 `ch4_lamda_tabm_bootstrap` 已冻结方案）。"""
    year = 2024
    y_arm = arm_preds[year]["y_true"].astype(np.int8)
    s_arm = arm_preds[year]["y_score"].astype(np.float64)
    y_uni, s_uni = load_uniform_preds(year)
    if not np.array_equal(y_arm, y_uni):
        raise RuntimeError(f"{year}: 臂与 uniform 的 y_true 不一致，无法配对")
    cat = classify(y_arm, s_uni >= THRESHOLD, s_arm >= THRESHOLD)
    rng = np.random.default_rng(42)
    counts = boot_counts(cat, rng, 10_000)
    draws = delta_from_counts(counts)
    point = f1_of(y_arm, s_arm) - f1_of(y_uni, s_uni)
    interval = ci(draws)
    return {
        "delta_point": point,
        "ci95": interval,
        "ci_excludes_zero": bool(interval[0] > 0.0 or interval[1] < 0.0),
        "n_boot": 10_000,
        "seed": 42,
        "paired_with": "uniform_tabm4",
        "rule": "y_score >= 0.5；95% 百分位区间；只量化测试样本不确定性，不冒充训练随机性",
    }


def run_arm(arm: str) -> int:
    if arm not in ARMS:
        raise ValueError(arm)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    print(f"[arm] {arm} k={K} device={DEVICE.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"seed={SEED} threshold={THRESHOLD}", flush=True)
    print(f"[groups] G0={GROUP_YEARS[0]} G1={GROUP_YEARS[1]}", flush=True)
    print(f"[weights] raw in/out={W_IN_GROUP}/{W_OUT_GROUP} raw_mean={W_RAW_MEAN:.6f} "
          f"effective in/out={W_IN_GROUP / W_RAW_MEAN}/{W_OUT_GROUP / W_RAW_MEAN}",
          flush=True)
    if arm == "a_route2":
        print("[route] year_group j -> active members {2j,2j+1}; k_t=2", flush=True)

    store = {y: ch3.load_year(y, "train") for y in YEARS}
    input_dim = int(store[YEARS[0]][0].shape[1])
    rng = np.random.default_rng(SEED)
    buf_rng = np.random.default_rng(SEED)
    model = TabMMLP(input_dim, K).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[model] k={K} params={n_params:,}", flush=True)

    current_year_f1: dict[str, float] = {}
    preds: dict[int, dict[str, np.ndarray]] = {}
    train_logs: dict[str, dict[str, Any]] = {}
    t0 = time.time()

    for idx, year in enumerate(YEARS):
        x_curr, y_curr = store[year]
        parts, meta = build_parts(store, YEARS, idx, x_curr, y_curr, buf_rng)
        pyears = part_years_from_meta(meta, YEARS, idx)
        parts2 = augment_parts_with_year(parts, pyears)
        n_rows = int(sum(p[0].shape[0] for p in parts2))
        pos_rows = int(sum(int((p[1][:, 0] == 1).sum()) for p in parts2))
        print(f"[parts] {year}: parts={len(parts2)} rows={n_rows:,} pos={pos_rows:,} "
              f"pos_rate={pos_rows / max(n_rows, 1):.4f} replay_years="
              f"{sorted({yr for yr in pyears if yr != year})}", flush=True)

        t_epoch = time.time()
        if arm == "a_route2":
            train_logs[str(year)] = train_epochs_routed(
                model, parts2, ch3.OFFICIAL_EPOCHS, DEVICE, rng, arm, year)
        else:
            member_group = MEMBER_GROUP_ANCHOR if arm == "c_anchor" else MEMBER_GROUP_ANTI
            train_logs[str(year)] = train_epochs_weighted(
                model, parts2, ch3.OFFICIAL_EPOCHS, DEVICE, rng, arm, year, member_group)
        del parts, parts2

        xt, yt = ch3.load_year(year, "test")
        if arm == "a_route2":
            m = evaluate_routed(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE, year)
        else:
            m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        current_year_f1[str(year)] = float(m["f1"])
        del xt, yt
        print(f"[{year}] current_f1={m['f1']:.4f} ({time.time() - t_epoch:.0f}s)", flush=True)

        if idx == len(YEARS) - 1:
            for ty in YEARS:
                xt, yt = ch3.load_year(ty, "test")
                if arm == "a_route2":
                    sc = score_shard_routed(model, xt, ch3.OFFICIAL_BATCH, DEVICE, ty)
                else:
                    sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE)
                preds[ty] = {"y_true": yt.astype(np.int8),
                             "y_score": sc.astype(np.float32)}
                del xt, yt

    backward_f1 = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"])
                   for ty in YEARS}
    mean_f1 = float(np.mean(list(backward_f1.values())))
    auc_oracle = auc_check(preds)
    boot = bootstrap_2024(preds)

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(THRESHOLD))

    d_2023 = (backward_f1["2023"] - UNIFORM_F1_2023) * 100.0
    d_2024 = (backward_f1["2024"] - UNIFORM_F1_2024) * 100.0
    d_mean = (mean_f1 - UNIFORM_MEAN) * 100.0
    support_2023 = d_2023 >= SUPPORT_DELTA_PP
    support_2024 = d_2024 >= SUPPORT_DELTA_PP
    support_mean12 = d_mean >= SUPPORT_MEAN_MIN_PP
    support = bool(support_2023 and support_2024 and support_mean12)

    mechanism: dict[str, Any] = {
        "year_groups": {str(g): GROUP_YEARS[g] for g in (0, 1)},
        "year_group_rule": "DOMAIN_YEARS 索引奇偶；纯轮转，无标签依赖",
    }
    if arm == "a_route2":
        mechanism.update({
            "form": "A",
            "member_active_by_year_group": {
                "0": [0, 1], "1": [2, 3]},
            "train_loss": "激活成员 BCE 均值",
            "eval": "只平均激活成员",
            "k_t": 2,
        })
    else:
        mechanism.update({
            "form": "C",
            "member_group": {"0": list(MEMBER_GROUP_ANCHOR if arm == "c_anchor"
                                       else MEMBER_GROUP_ANTI),
                             "1": [1 - v for v in (MEMBER_GROUP_ANCHOR if arm == "c_anchor"
                                                   else MEMBER_GROUP_ANTI)]},
            "member_group_by_member": list(MEMBER_GROUP_ANCHOR if arm == "c_anchor"
                                           else MEMBER_GROUP_ANTI),
            "train_loss": "1/k Σ_i w_{i,g(x)}·BCE(s_i,y)，逐样本权重均值归一",
            "eval": "全体成员概率均值（与 uniform 同一公式）",
            "weights": {
                "raw_in_group": W_IN_GROUP, "raw_out_group": W_OUT_GROUP,
                "per_sample_raw_mean": W_RAW_MEAN,
                "effective_in_group": W_IN_GROUP / W_RAW_MEAN,
                "effective_out_group": W_OUT_GROUP / W_RAW_MEAN,
                "ratio": W_IN_GROUP / W_OUT_GROUP,
                "mean_after_normalization": 1.0,
                "design_disclosure": (
                    "设计原文写 w=2 / w=2/3 且均值恒为 1；在 2+2 组分配下原始表均值实为 "
                    "4/3。实现保留 3:1 比值与逐样本均值 1（有效 1.5/0.5），"
                    "以维持「总梯度尺度与 uniform 严格一致」的冻结合同。"
                ),
            },
        })

    payload: dict[str, Any] = {
        "arm": arm, "k": K, "n_params": n_params,
        "mechanism": mechanism,
        "protocol": {
            "domain_years": YEARS, "epochs": ch3.OFFICIAL_EPOCHS,
            "batch": ch3.OFFICIAL_BATCH, "lr": ch3.OFFICIAL_LR,
            "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
            "memory": ch3.OFFICIAL_MEMORY, "seed": SEED, "threshold": THRESHOLD,
            "optimizer_lifetime": "per_year_rebuild_inside_train_fn",
            "parts_source": "ch4_lamda_training_process_2x2.build_parts",
            "batch_stream": "ch3.iterate_batches_parts 的逐行镜像（标签扩为 (y, year_id)）",
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
            "support_2023": bool(support_2023),
            "support_2024": bool(support_2024),
            "support_mean12": bool(support_mean12),
            "support": support,
            "thresholds": {
                "year_delta_pp": SUPPORT_DELTA_PP,
                "mean12_min_pp": SUPPORT_MEAN_MIN_PP,
                "direction_gap_pp": DIRECTION_GAP_PP,
            },
            "direction_valid": None,
            "direction_note": (
                "C − C' 在 2024 的判据需要 c_anti 完成后在 anchor-comparison.json 判定"
                if arm == "c_anchor" else
                ("设计未给形式 A 设置反向对照臂，方向有效性不适用"
                 if arm == "a_route2" else
                 "本臂为反向对照，不参与形式选择")
            ),
            "auc_oracle_check": auc_oracle,
            "bootstrap_2024": boot,
        },
        "train_logs": train_logs,
        "wall_seconds": round(time.time() - t0, 1),
        "ts": now_utc(),
    }
    write_json(RUN_DIR / f"{arm}-result.json", payload)
    print(f"[criteria] d2023={d_2023:+.2f}pp d2024={d_2024:+.2f}pp "
          f"dmean={d_mean:+.2f}pp support={support}", flush=True)
    print(f"[auc_oracle] {json.dumps(auc_oracle, ensure_ascii=False)}", flush=True)
    print(f"[bootstrap_2024] {json.dumps(boot, ensure_ascii=False)}", flush=True)
    print(f"=== {arm}: 12y mean={mean_f1:.10f} | 2023={backward_f1['2023']:.6f} "
          f"2024={backward_f1['2024']:.6f} | {payload['wall_seconds']:.0f}s ===",
          flush=True)
    maybe_comparison()
    return 0


def maybe_comparison() -> None:
    """汇总已完成的臂；三臂齐备时机械执行冻结的形式选择规则。"""
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
        arms_summary[arm] = {
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
            "auc_oracle_check": c["auc_oracle_check"],
            "bootstrap_2024": c["bootstrap_2024"],
        }

    comp: dict[str, Any] = {
        "schema_version": "ch4-anchor-pilot-comparison-v1",
        "reference_uniform_tabm4": {
            "mean_f1": UNIFORM_MEAN,
            "f1_2023": UNIFORM_F1_2023,
            "f1_2024": UNIFORM_F1_2024,
            "preds_dir": "runs/diagnostics/ch4-lamda-tabm-pilot",
        },
        "criteria_text": {
            "support": ("该臂 2023 与 2024 相对 uniform tabm4 各 >= +0.5 pp，"
                        "且 12 年平均 >= uniform − 0.20 pp"),
            "direction_validity": "C − C' 在 2024 >= +0.5 pp（只对通过支持判据的 C 臂判定）",
            "form_selection": ("恰一臂通过 -> 选该臂；两臂通过 -> 取 2024 增量更高者；"
                               "两臂皆败 -> 第二机制设计重开"),
        },
        "arms": arms_summary,
        "status": "partial",
        "ts": now_utc(),
    }

    if all(arm in res for arm in ARMS):
        gap = (res["c_anchor"]["f1_2024"] - res["c_anti"]["f1_2024"]) * 100.0
        direction_valid = bool(gap >= DIRECTION_GAP_PP)
        comp["direction_check"] = {
            "definition": "F1_2024(c_anchor) − F1_2024(c_anti) >= +0.5 pp",
            "f1_2024_c_anchor": res["c_anchor"]["f1_2024"],
            "f1_2024_c_anti": res["c_anti"]["f1_2024"],
            "gap_pp": gap,
            "direction_valid": direction_valid,
            "applies_to": "c_anchor",
            "note": "形式 A 无反向对照臂，方向有效性不适用",
        }
        eligibility = {
            "c_anchor": bool(res["c_anchor"]["criteria"]["support"] and direction_valid),
            "a_route2": bool(res["a_route2"]["criteria"]["support"]),
        }
        eligible = [a for a in ANCHOR_ARMS if eligibility[a]]
        if len(eligible) == 1:
            selected: str | None = eligible[0]
            outcome = "select"
            reason = f"恰一臂通过：{selected}"
        elif len(eligible) == 2:
            selected = max(eligible,
                           key=lambda a: res[a]["criteria"]["delta_2024_pp"])
            outcome = "select_higher_2024"
            reason = f"两臂通过，取 2024 增量更高者：{selected}"
        else:
            selected = None
            outcome = "reopen_mechanism_design"
            reason = "两臂皆败，第二机制设计重开"
        # 次要读数（披露，不改判据）：若把设计中的「通过」严格解释为只看支持判据，
        # 不把方向有效性当作选择门槛，结果如下；主判据仍按 eligibility_rule 执行。
        support_only = [a for a in ANCHOR_ARMS if res[a]["criteria"]["support"]]
        if len(support_only) == 1:
            so_selected: str | None = support_only[0]
            so_outcome = "select"
        elif len(support_only) == 2:
            so_selected = max(support_only,
                              key=lambda a: res[a]["criteria"]["delta_2024_pp"])
            so_outcome = "select_higher_2024"
        else:
            so_selected = None
            so_outcome = "reopen_mechanism_design"
        comp["form_selection"] = {
            "eligibility": eligibility,
            "eligibility_rule": ("c_anchor = support AND direction_valid；"
                                 "a_route2 = support（无反向对照）"),
            "eligible_arms": eligible,
            "selected": selected,
            "outcome": outcome,
            "reason": reason,
            "support_only_disclosure": {
                "eligible_arms": support_only,
                "selected": so_selected,
                "outcome": so_outcome,
                "note": ("若「通过」只按支持判据解释（不把方向有效性作为门槛），"
                         "结果的次要读数；主判据按 eligibility_rule 执行。"),
            },
        }
        comp["status"] = "complete"

    write_json(RUN_DIR / "anchor-comparison.json", comp)
    if comp["status"] == "complete":
        sel = comp["form_selection"]
        print(f"[form_selection] selected={sel['selected']} outcome={sel['outcome']} "
              f"reason={sel['reason']}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="第四章成员-年度锚定先导（三臂）")
    parser.add_argument("--arm", choices=ARMS, required=True)
    args = parser.parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return run_arm(args.arm)


if __name__ == "__main__":
    raise SystemExit(main())
