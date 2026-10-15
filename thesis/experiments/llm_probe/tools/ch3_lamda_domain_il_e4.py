#!/usr/bin/env python
"""E4：LAMDA 官方 Domain-IL 协议复现（**数据门禁：持续学习轨道**）。

逐字对齐官方 `code/Supplementary_material/continual_learning/domain_il_experiment.py`
（commit `7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249`，副本已落
`.Codex/docs/2026-10-14-LAMDA官方持续学习协议/official-src/`）。

## 官方协议（逐条抄自源码）

| 项 | 官方值 | 出处 |
| --- | --- | --- |
| 年份序列 | `[2013,2014,2016,...,2025]` 共 12 年 | 第 15 行 |
| 数据路径 | `Domain-IL-Baseline/<年>/<年>_{train,test}.parquet` | 第 30 行 |
| 模型 | `ChenEncoderMLP`：4561→512→384→256→128（ReLU），再接 128→100→ReLU→Drop(0.2)→100→ReLU→Drop(0.2)→1→**Sigmoid** | 第 43–59 行 |
| 损失 | `BCELoss` | 第 159 行 |
| 优化器 | `SGD(lr=0.01, momentum=0.9, weight_decay=1e-6)` | 第 194 行 |
| 轮数 / 批量 | `10` / `1024` | 第 21–22 行 |
| 策略 | `naive`（只用当年）／`cumulative`（=**Joint**，用所有已见年）／`expreplay`（当年 + 容量 **200** 蓄水池） | 第 171–191 行 |
| 蓄水池 RNG | `np.random.default_rng(42)` | 第 16、75 行 |
| 判定阈值 | `0.5` | 第 117 行 |
| 评价 | 每个 experience 做 backward（已见年）+ forward（未见年），写 `results_all.csv` | 第 207–223 行 |
| 聚合 | `for-graph.py` 按 (experience, mode) 求 `avg_f1`；`for-table.py` 跨 run 求 mean±SEM | 官方两脚本 |

**报告口径**：官方论文引用的 `2025 Domain-IL 平均 F1`（Joint `88.52±0.46` vs Naive `72.71±0.83`）
= **最后一个 experience（2025）的 `avg_f1`**（该 experience 只有 backward，覆盖 12 个测试年）。

## ⚠️ 与官方的三处偏离（**必须随结果一并报告**）

1. **数据目录替换**：官方读 `Domain-IL-Baseline/`，**该视图在 HuggingFace 上不存在**
   （2026-10-14 实测列全 `main` 分支递归树：只有 `Baseline`、`var_thresh_0.0001`、`var_thresh_0.01`、
   `NPZ_Version`、`metadata.csv`）。官方 `readme.md` 却写「For the Domain-IL, it is already available」。
   ⇒ 本脚本**假设 `Domain-IL-Baseline ≡ Baseline`**（同为两类别全量视图，列名同构）。
   **这是假设，不是核实事实**；若官方另有构造规则，本复现无效。
2. **存储 dtype**：官方 `torch.tensor(..., dtype=torch.float32, device=device)` 全量上设备；
   12 年 train 合计 `806,700` 行 × 4,561 维 × 4 B = **13.7 GiB**，本机 16 GiB 不可行。
   ⇒ 本脚本在**主机内存存 int8**（二值 0/1 精确可表示），**逐批转 float32 上设备**——
   **数值完全一致，仅存储 dtype 不同**。
3. **设备**：官方 CUDA，本机 **MPS**（资源差异，非协议差异）。

**另**：官方未设 torch 种子（`run-experiments.sh` 循环 3 次却不传 seed）；
本脚本**显式设种子并记录**，故本机 1 次运行为确定性结果，不作 3 seed 复现。

## 运行

    /opt/miniconda3/envs/rwkv/bin/python \
        thesis/experiments/llm_probe/tools/ch3_lamda_domain_il_e4.py --strategy naive
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
import pyarrow.parquet as pq
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

RUN_NAME = "ch3-lamda-domain-il-e4-replication-v1"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME
DATA_ROOT = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/"
    "thesis/experiments/llm_probe/runs/data-raw/"
    "lamda-iclr2026-baseline-ad9614bdd5556767"
)

# ---- 逐字对齐官方 ----
DOMAIN_YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
OFFICIAL_EPOCHS = 10
OFFICIAL_BATCH = 1024
OFFICIAL_LR = 1e-2
OFFICIAL_MOMENTUM = 0.9
OFFICIAL_WEIGHT_DECAY = 1e-6
OFFICIAL_MEMORY = 200
OFFICIAL_RNG_SEED = 42
THRESHOLD = 0.5
SEED = 42  # 官方未设；本脚本显式设置并记录


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def load_year(year: int, split: str) -> tuple[np.ndarray, np.ndarray]:
    """返回 (X_int8, y_float32)。官方在别处读 Domain-IL-Baseline，本机替换为 Baseline（偏离 1）。"""
    path = DATA_ROOT / f"Baseline/{year}/{year}_{split}.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    table = pq.read_table(path)
    feat_cols = [c for c in table.column_names if c.startswith("feat_")]
    n = table.num_rows
    x = np.empty((n, len(feat_cols)), dtype=np.int8)
    for i, c in enumerate(feat_cols):
        x[:, i] = table.column(c).to_numpy(zero_copy_only=False)
    y = table.column("label").to_numpy(zero_copy_only=False).astype(np.float32)
    del table
    return x, y


class ChenEncoderMLP(nn.Module):
    """官方第 43–59 行，逐层照抄。"""

    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 512), nn.ReLU(),
            nn.Linear(512, 384), nn.ReLU(),
            nn.Linear(384, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU(),
        )
        self.classifier = nn.Sequential(
            nn.Linear(128, 100), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(100, 100), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(100, 1), nn.Sigmoid(),
        )

    def forward(self, x):
        return self.classifier(self.encoder(x))


FREEMOCA_LAMBDA_MIN = 0.1  # 取自官方 main_domain.py 的 Domain-IL 调用（非本项目设定）
FREEMOCA_LAMBDA_MAX = 0.9

# ⚠️ 以下两个是**任务化设定，无文献依据**（本仓库「魔法数字门禁」要求显式登记）
# EWC / LwF 的强度参数。对参数侧效率曲线的**形状**不敏感，但对**绝对高度**敏感；
# 正式对比前须做敏感性（见 task_plan 的待办）。
EWC_LAMBDA = 1000.0
LWF_LAMBDA = 1.0
LWF_TEMPERATURE = 2.0
FISHER_SAMPLE = 4096  # Fisher 对角线的子采样上限（控制成本；全量 8 万行不必要）

# ⚠️ 模块二轮次调度的目标适应步长。**任务化设定，无直接文献依据**（魔法数字门禁要求登记）。
#
# 标定依据：轮次调度**只改暴露量的分布，不改其总量**——否则测出的是「总量变化」而非
# 「再分配」的效果。标定方法是令调度臂的每轮倍数均值等于同一容量下常数臂的最优值
# （N=200 上为 4），据此反推 a*。该值只决定 λ_r 的绝对高度，不决定其随 ρ 的走向。
#
# 2026-10-14 修正：初值 0.9975 按先导短跑的 ρ 分布标定，与全量实测不符。全量 110 次
# 调度实测 ρ：均值 +0.027、标准差 0.360、范围 [-0.839, +0.936]，|ρ|<0.3 占 65.5%，
# 故 E[1/(1-ρ)] 远小于先导假设，λ_r 被压到 0.0025 量级、平均倍数仅 1.45（目标 4）。
# 按该实测 ρ 分布重解得 a* = 0.99173（平均倍数 4.0，扫描值见下）。
# 旧标定下那次运行的总量未对齐（≈m=1 而非 m=4），其读数作废，不得引用。
# a* 敏感性扫描（同一 ρ 序列）：0.9950→2.36、0.9900→4.94、0.9850→7.15、0.9800→9.36。
RHO_A_STAR = 0.99173


def compute_fisher(model, parts, batch: int, device) -> list:
    """经验 Fisher 对角线的子采样估计（平方梯度期望）。"""
    fisher = [torch.zeros_like(p) for p in model.parameters()]
    model.eval()
    criterion = nn.BCELoss()
    n_seen = 0
    for xb, yb in iterate_batches_parts(parts, batch, np.random.default_rng(0), False):
        xt = torch.from_numpy(xb.astype(np.float32)).to(device)
        yt = torch.from_numpy(yb).to(device).unsqueeze(1)
        model.zero_grad()
        criterion(model(xt), yt).backward()
        for f, p in zip(fisher, model.parameters()):
            if p.grad is not None:
                f += p.grad.detach() ** 2 * xt.shape[0]
        n_seen += xt.shape[0]
        if n_seen >= FISHER_SAMPLE:
            break
    return [f / max(n_seen, 1) for f in fisher]


def freemoca_interpolate(prev_state: dict, model, lmin: float = FREEMOCA_LAMBDA_MIN,
                         lmax: float = FREEMOCA_LAMBDA_MAX, eps: float = 1e-12) -> None:
    """逐字对齐官方 `models.py::compute_layerwise_lambdas` + `interpolate_models`。

    - 位移分 `s = |new − old|.mean()`（**按参数张量**，官方如此，非按"层"）
    - 归一化 `ŝ = (s − s_min)/(s_max − s_min + ε)`；`s_max−s_min < ε` 时取区间中点
    - 反向映射 `λ = λ_min + (1 − ŝ)(λ_max − λ_min)`（**位移大 ⇒ 更保守**）
    - 插值 `θ ← (1−λ)·θ_prev + λ·θ_cur`；非浮点或形状不符的取新值
    """
    cur = model.state_dict()
    scores = {}
    for name, new_p in cur.items():
        old_p = prev_state.get(name)
        if old_p is None or old_p.shape != new_p.shape:
            continue
        if not (torch.is_floating_point(new_p) and torch.is_floating_point(old_p)):
            continue
        scores[name] = (new_p.detach().float() - old_p.float()).abs().mean().item()

    if not scores:
        return
    vals = list(scores.values())
    s_min, s_max = min(vals), max(vals)
    if s_max - s_min < eps:
        lam = {n: 0.5 * (lmin + lmax) for n in scores}
    else:
        lam = {n: lmin + (1.0 - (s - s_min) / (s_max - s_min)) * (lmax - lmin)
               for n, s in scores.items()}

    with torch.no_grad():
        for name, new_p in cur.items():
            old_p = prev_state.get(name)
            if old_p is None or old_p.shape != new_p.shape or name not in lam:
                continue
            if not (torch.is_floating_point(new_p) and torch.is_floating_point(old_p)):
                continue
            a = lam[name]
            new_p.copy_((1.0 - a) * old_p.to(new_p.device) + a * new_p)


def quota_buffer(store: dict, years_seen: list[int], capacity: int,
                 rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """**按年等额 + 年内正负各半**的配额缓冲（容量不变，只改构成）。

    **设计已冻结（2026-10-14，跑前写死，禁止看结果再调）**：
    1. 已见 `k` 年 ⇒ 每年配额 `capacity // k`（余数丢弃，不调剂）
    2. 年内配额**正负各半**；某一年正例不足时，**不足部分用负例补齐**（不跨年调剂）
    3. 年内的具体样本用**固定种子**随机抽取

    动机（E5 实测，可复核）：官方均匀蓄水池的 200 槽位中，2023 只有 1 个正例、2024 与 2025 各 0 个，
    而这三年的正例率分别是 `14.52% / 1.64% / 0.05%`。**本臂只改缓冲构成，其他一切不动。**
    """
    k = len(years_seen)
    per = capacity // k
    xs, ys = [], []
    for year in years_seen:
        X, Y = store[year]
        pos = np.flatnonzero(Y == 1)
        neg = np.flatnonzero(Y == 0)
        want_pos = per // 2
        n_pos = min(pos.size, want_pos)
        n_neg = min(neg.size, per - n_pos)          # 正例不足时用负例补足本年的配额
        if n_pos:
            xs.append(X[rng.choice(pos, size=n_pos, replace=False)])
            ys.append(np.ones(n_pos, dtype=np.float32))
        if n_neg:
            xs.append(X[rng.choice(neg, size=n_neg, replace=False)])
            ys.append(np.zeros(n_neg, dtype=np.float32))
    if not xs:
        return np.zeros((0, next(iter(store.values()))[0].shape[1]), dtype=np.int8), np.zeros(0, dtype=np.float32)
    return np.concatenate(xs), np.concatenate(ys)


class ReplayBuffer:
    """官方第 61–88 行：容量 200 的蓄水池抽样，RNG 种子 42。"""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        # 第三项为来源年度：只为支持按年度分配复用（模块二的复用分配）而记，
        # 不影响抽样语义；官方语义下该字段从不被读取。
        self.data: list[tuple[np.ndarray, float, int]] = []
        self.n_seen = 0
        self.rng = np.random.default_rng(OFFICIAL_RNG_SEED)

    def add_batch(self, x: np.ndarray, y: np.ndarray, year: int) -> None:
        for xi, yi in zip(x, y):
            self.n_seen += 1
            if len(self.data) < self.capacity:
                self.data.append((xi, float(yi), year))
            else:
                j = int(self.rng.integers(0, self.n_seen))
                if j < self.capacity:
                    self.data[j] = (xi, float(yi), year)

    def sample(self) -> tuple[np.ndarray, np.ndarray]:
        xs = np.stack([d[0] for d in self.data])
        ys = np.array([d[1] for d in self.data], dtype=np.float32)
        return xs, ys

    def blocks(self) -> list[tuple[int, np.ndarray, np.ndarray]]:
        """按来源年度切块，返回 [(year, X, y), ...]，年度升序。"""
        by_year: dict[int, list[int]] = {}
        for i, (_, _, yr) in enumerate(self.data):
            by_year.setdefault(yr, []).append(i)
        out = []
        for yr in sorted(by_year):
            idx = by_year[yr]
            xs = np.stack([self.data[i][0] for i in idx])
            ys = np.array([self.data[i][1] for i in idx], dtype=np.float32)
            out.append((yr, xs, ys))
        return out

    def __len__(self) -> int:
        return len(self.data)


def iterate_batches(x: np.ndarray, y: np.ndarray, batch: int, rng: np.random.Generator, shuffle: bool):
    idx = rng.permutation(x.shape[0]) if shuffle else np.arange(x.shape[0])
    for s in range(0, idx.size, batch):
        sel = idx[s : s + batch]
        if sel.size < 2:
            continue
        yield x[sel], y[sel]


def iterate_batches_parts(parts, batch: int, rng: np.random.Generator, shuffle: bool):
    """**虚拟拼接**：对多个 (X_int8, y) 分片做全局洗牌与取批，但**不做物理拷贝**。

    动机：`cumulative` 末年 12 年合计 806,700×4,561 int8 = 3.4 GiB；
    官方语义是「先 `np.concatenate` 再全局 shuffle」，物理拼接会再要 3.4 GiB，
    本机 16 GiB 会 OOM。本函数用全局排列 + `searchsorted` 映射回分片，**语义与物理拼接逐位一致**。
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
        ys = np.empty(sel.size, dtype=np.float32)
        for pi in np.unique(which):
            m = which == pi
            loc = sel[m] - cum[pi]
            xs[m] = parts[pi][0][loc]
            ys[m] = parts[pi][1][loc]
        yield xs, ys


def measure_rho(model, curr_part, mem_blk, batch, device, rng) -> float:
    """当前年度批与历史批的梯度余弦相似度。

    用两批各一次前向与反向取梯度。全程不改变参数（算完即 `zero_grad`），
    因此对训练结果无影响，只作可观测量。
    """
    criterion = nn.BCELoss()
    was_training = model.training
    model.train()

    def _grad(part):
        x, y = part
        n = min(batch, x.shape[0])
        sel = rng.integers(0, x.shape[0], size=n)
        xt = torch.from_numpy(x[sel].astype(np.float32)).to(device)
        yt = torch.from_numpy(y[sel]).to(device).unsqueeze(1)
        model.zero_grad()
        criterion(model(xt), yt).backward()
        g = torch.cat([p.grad.flatten() for p in model.parameters()
                       if p.grad is not None]).detach().clone()
        model.zero_grad()
        return g

    g_c = _grad(curr_part)
    g_m = _grad(mem_blk)
    denom = float(g_c.norm()) * float(g_m.norm()) + 1e-12
    rho = float((g_c * g_m).sum()) / denom
    if not was_training:
        model.eval()
    return rho


def train_epochs(model, parts, epochs, batch, lr, device, rng, penalty=None,
                 rho_sched=None, l2_beta: float = 0.0, theta_star: list | None = None) -> None:
    """`parts` 为 [(X_int8, y_float32), ...]，按官方语义全局洗牌后取批（虚拟拼接，见上）。

    `penalty`（可选）＝`("ewc", fisher_list, anchor_list)` 或 `("lwf", prev_model)`，
    分别对应参数侧的两条经典保持路线；**默认 None ⇒ 行为与官方 naive 逐位一致**。

    `rho_sched`（可选）＝`(mem_blk, curr_part, a_star, m_cap[, ema_beta])`：模块二的**轮次调度**形态。
    每轮开始前实测历史梯度与当前梯度的余弦相似度 $\\rho_r$，由一阶条件反解该轮的
    历史权重 $\\lambda_r = (1-a^{*})/(1-\\rho_r)$，再换算成该轮的记忆块重复份数。
    `ema_beta > 0` 时改用 EMA 平滑后的 $\\hat\\rho_r$：首轮直接取实测值，其后
    $\\hat\\rho_r = \\beta\\,\\hat\\rho_{r-1} + (1-\\beta)\\,\\rho_r$。EMA 状态是本函数局部变量，
    而 `train_epochs` 每年度调用一次 ⇒ **平滑只在同一年度的轮次之间延续，不跨年度**。
    默认 None ⇒ 与统一复用逐位一致。

    `l2_beta > 0` 且 `theta_star` 非空 ⇒ 参数锚定兜底（FOREVER 式）：每批损失加
    $\\beta\\,\\|\\Theta-\\Theta^{*}\\|^2 = \\beta\\sum_j \\|\\Theta_j - \\Theta_j^{*}\\|_2^2$
    （与 FOREVER Eq. 11 同形，不加 0.5 系数）。`theta_star` 为上一经验（年度）
    训练结束的权重张量列表，由调用方每年重设一次、年度内固定；首年无历史不锚定。
    每轮结束打印该轮数据损失与锚定项的轮均比值（可观察指标，量级对齐验收用）。
    """
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=OFFICIAL_MOMENTUM,
                          weight_decay=OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss()
    if penalty and penalty[0] == "lwf":
        penalty[1].eval()
    model.train()
    rho_ema_val = None   # EMA 状态仅在同一年度的轮次之间延续（本函数每年调用一次，天然逐年重置）
    l2_active = l2_beta > 0.0 and theta_star is not None
    for _ in range(epochs):
        epoch_bce = torch.zeros((), device=device)   # 轮内数据损失累计（轮末一次 item，避免逐批同步）
        epoch_l2 = torch.zeros((), device=device)
        n_batches = 0
        epoch_parts = parts
        if rho_sched is not None:
            mem_blk, curr_part, a_star, m_cap = rho_sched[:4]
            ema_beta = rho_sched[4] if len(rho_sched) > 4 else 0.0
            rho_raw = measure_rho(model, curr_part, mem_blk, batch, device, rng)
            if ema_beta > 0.0:
                rho_ema_val = rho_raw if rho_ema_val is None \
                    else ema_beta * rho_ema_val + (1.0 - ema_beta) * rho_raw
                rho = rho_ema_val
            else:
                rho = rho_raw
            lam = (1.0 - a_star) / (1.0 - rho) if abs(1.0 - rho) > 1e-6 else 1.0
            lam = min(max(lam, 0.0), 1.0)
            n_c, n_m = int(curr_part[0].shape[0]), int(mem_blk[0].shape[0])
            if lam >= 1.0:
                m_r = max(1, n_c // n_m)
            else:
                m_r = int(round(lam * n_c / max((1.0 - lam) * n_m, 1e-9)))
            m_r = min(max(m_r, 1), m_cap)
            epoch_parts = [curr_part] + [mem_blk] * m_r
            if ema_beta > 0.0:
                print(f"[sched] rho_raw={rho_raw:+.4f} rho={rho:+.4f} lambda={lam:.4f} repeat={m_r}", flush=True)
            else:
                print(f"[sched] rho={rho:+.4f} lambda={lam:.4f} repeat={m_r}", flush=True)
        for xb, yb in iterate_batches_parts(epoch_parts, batch, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            out = model(xt)
            loss_data = criterion(out, yt)
            loss = loss_data
            if l2_beta > 0.0 and theta_star is not None:
                l2_val = sum((p - a).pow(2).sum()
                             for p, a in zip(model.parameters(), theta_star))
                loss = loss + l2_beta * l2_val
                epoch_l2 = epoch_l2 + l2_val.detach()
            epoch_bce = epoch_bce + loss_data.detach()
            n_batches += 1
            if penalty and penalty[0] == "ewc":
                _, fisher, anchor = penalty
                pen = sum((f * (p - a) ** 2).sum()
                          for f, p, a in zip(fisher, model.parameters(), anchor))
                loss = loss + 0.5 * EWC_LAMBDA * pen
            elif penalty and penalty[0] == "lwf":
                _, prev_model = penalty
                with torch.no_grad():
                    tgt = torch.sigmoid(prev_model(xt) / LWF_TEMPERATURE)
                pred = torch.sigmoid(out / LWF_TEMPERATURE)
                loss = loss + LWF_LAMBDA * (LWF_TEMPERATURE ** 2) * \
                    torch.nn.functional.binary_cross_entropy(pred, tgt)
            loss.backward()
            opt.step()
        if l2_active:
            bce_m = epoch_bce.item() / max(n_batches, 1)
            l2_m = epoch_l2.item() / max(n_batches, 1)
            print(f"[anchor] bce={bce_m:.6f} l2={l2_m:.6e} beta*l2/bce={(l2_beta * l2_m) / max(bce_m, 1e-12):.4f}",
                  flush=True)


@torch.inference_mode()
def evaluate(model, x, y, batch, device) -> dict:
    model.eval()
    preds, labels = [], []
    for xb, yb in iterate_batches(x, y, batch, np.random.default_rng(0), False):
        xt = torch.from_numpy(xb.astype(np.float32)).to(device)
        out = model(xt).squeeze(1).cpu().numpy()
        preds.append((out >= THRESHOLD).astype(int))
        labels.append(yb.astype(int))
    p = np.concatenate(preds) if preds else np.zeros(0, dtype=int)
    l = np.concatenate(labels) if labels else np.zeros(0, dtype=int)
    return {
        "accuracy": float(accuracy_score(l, p)),
        "precision": float(precision_score(l, p, zero_division=0)),
        "recall": float(recall_score(l, p, zero_division=0)),
        "f1": float(f1_score(l, p, zero_division=0)),
        "n": int(l.size), "n_pos": int((l == 1).sum()),
    }


def split_by_year(store: dict, years_seen: list[int], capacity: int,
                  rng: np.random.Generator, scheme: str = "quota"
                  ) -> list[tuple[int, np.ndarray, np.ndarray]]:
    """按年度把缓冲切成若干块，返回 [(year, X_int8, y_float32), ...]。

    **2×2 四格（2026-10-15 加）**——用来分离此前被捆绑在一起的两件事：
    「年度间如何分配位置」与「年度内是否按标签分层」。既有的 `quota` 臂同时改了这两件，
    因而它的增益无法归给其中任何一个。

      scheme="quota"         —— 年度间等额 + 年内正负各半（本章模块一，既有行为，逐位不变）
      scheme="prop_strat"    —— 年度间按样本量比例 + 年内正负各半
      scheme="equal_unstrat" —— 年度间等额 + 年内不分层
    第四格「按样本量比例 + 不分层」即官方全局蓄水池（`buffer_scheme="reservoir"`）。

    保留年度标签，以便下游对每个年度单独设定复用次数（模块二的复用分配）。
    """
    k = len(years_seen)
    if scheme == "prop_strat":
        # 按各年度样本量比例分配，向下取整（不强制回补到 capacity，与 quota 的余数丢弃口径一致）
        sizes = np.array([store[y][0].shape[0] for y in years_seen], dtype=float)
        per_year = {y: int(a) for y, a in
                    zip(years_seen, np.floor(capacity * sizes / sizes.sum()).astype(int))}
    else:
        per_year = {y: capacity // k for y in years_seen}
    out = []
    for year in years_seen:
        X, Y = store[year]
        per = per_year[year]
        if per <= 0:
            continue
        if scheme == "equal_unstrat":
            idx = rng.choice(X.shape[0], size=min(per, X.shape[0]), replace=False)
            xs, ys = X[idx], Y[idx].astype(np.float32)
        else:
            pos = np.flatnonzero(Y == 1)
            neg = np.flatnonzero(Y == 0)
            want_pos = per // 2
            n_pos = min(pos.size, want_pos)
            n_neg = min(neg.size, per - n_pos)
            xs, ys = [], []
            if n_pos:
                xs.append(X[rng.choice(pos, size=n_pos, replace=False)])
                ys.append(np.ones(n_pos, dtype=np.float32))
            if n_neg:
                xs.append(X[rng.choice(neg, size=n_neg, replace=False)])
                ys.append(np.zeros(n_neg, dtype=np.float32))
            if xs:
                xs, ys = np.concatenate(xs), np.concatenate(ys)
        if xs.size:
            out.append((year, xs, ys))
    return out


def reuse_by_deficit(blocks: list[tuple[int, np.ndarray, np.ndarray]], m_max: int) -> dict[int, int]:
    """模块二的**复用分配**：使各年度的**正例总暴露量**相等。

    规则（跑前冻结）：记第 s 年缓冲块的正例数为 $p_s$，则复用次数
        $$m_s = \\text{clip}\\left(\\mathrm{round}(m_{max} \\cdot \\bar p / p_s),\\; 1,\\; m_{max}\\right)$$
    其中 $\\bar p$ 为各年度 $p_s$ 的均值。**正例越少、重复越多**，用计算补偿稀缺。
    该规则不含阈值参数，只用到 $p_s$ 这个可观测计数。
    """
    ps = np.array([int((y == 1).sum()) for _, _, y in blocks], dtype=float)
    if ps.size == 0 or ps.min() <= 0:
        return {yr: m_max for yr, _, _ in blocks}
    target = m_max * ps.mean()
    out = {}
    for (yr, _, y), p in zip(blocks, ps):
        out[yr] = int(np.clip(round(target / p), 1, m_max))
    return out


def main(strategy: str, epochs: int, batch: int, lr: float, memory: int, years_limit: int | None,
         buffer_repeat: int = 1, seed: int = SEED, buffer_scheme: str = "reservoir",
         reuse_scheme: str = "uniform", reuse_schedule: str = "off",
         reuse_cap: int = 64, rho_a_star: float = RHO_A_STAR, rho_ema: float = 0.0,
         anchor_beta: float = 0.0) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    # 存储预算曲线需要对同一策略跑多个容量 ⇒ 文件名必须带容量，否则互相覆盖。
    # 后缀仅在**偏离官方默认**时追加，以保持既有 `metrics_expreplay_m200.json` 等文件名不变。
    if strategy == "expreplay":
        tag = f"{strategy}_m{memory}"
        if buffer_scheme != "reservoir":
            tag += f"_{buffer_scheme}"
        if reuse_scheme != "uniform":
            tag += f"_{reuse_scheme}"
        if buffer_repeat != 1:
            tag += f"_r{buffer_repeat}"
        # 调度开关同样必须进 tag：否则 rho 臂写回 `expreplay_m200`，覆盖无调度的基线产物
        # （2026-10-14 实测事故：rho 臂覆盖了 metrics_expreplay_m200.json / status_*.json）。
        if reuse_schedule != "off":
            tag += f"_{reuse_schedule}"
            # 上界偏离近乎不限的默认值时必须进 tag，否则判别实验会覆盖无上界的旧读数
            if reuse_cap != 64:
                tag += f"_cap{reuse_cap}"
            # EMA 平滑系数进 tag：不同 β 的读数互不覆盖（β=0 不进 tag，与既有产物命名一致）
            if rho_ema > 0.0:
                tag += f"_ema{int(round(rho_ema * 100))}"
            # 参数锚定系数进 tag：不同 β 的读数互不覆盖（β=0 不进 tag）
            if anchor_beta > 0.0:
                tag += f"_anc{anchor_beta:g}"
    else:
        tag = strategy
    if seed != SEED:                      # 多种子复现：官方未设种子，本脚本默认 42
        tag += f"_s{seed}"
    # 运行身份横幅：把真正生效的配置打进日志，使「参数忘了往下传」这类错误当场可见
    # 轮次调度的三个标定量必须进横幅（2026-10-15 缺口：此前只能从 tag 反推 a*/β/cap）
    sched_banner = (f" a_star={rho_a_star} rho_ema={rho_ema} reuse_cap={reuse_cap}"
                    if reuse_schedule == "rho" else "")
    print(f"[run] strategy={strategy} memory={memory} scheme={buffer_scheme} "
          f"reuse={reuse_scheme} repeat={buffer_repeat} seed={seed}{sched_banner} tag={tag}", flush=True)
    status = RUN_DIR / f"status_{tag}.json"
    metrics_path = RUN_DIR / f"metrics_{tag}.json"
    write_json(status, {"status": "running", "strategy": strategy, "ts": now_utc()})

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    rng = np.random.default_rng(seed)

    years = DOMAIN_YEARS if not years_limit else DOMAIN_YEARS[:years_limit]
    # 配额方案每轮从**已见年度**重建缓冲，与此处增量式的蓄水池互斥（同一时间只启用一个）
    buffer = (ReplayBuffer(memory)
              if (strategy == "expreplay" and buffer_scheme == "reservoir") else None)
    # 配额缓冲用**独立** RNG：不扰动 train_epochs 的洗牌流，使两臂在训练侧逐位可比
    buf_rng = np.random.default_rng(SEED)

    # 预载全部年份到主机内存（int8；官方逐次读盘，见偏离 2 的注释）
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in DOMAIN_YEARS:
        store[y] = load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    model = None
    records: list[dict] = []
    ewc_state = None   # (fisher_list, anchor_list)，均为**上一任务**的量
    lwf_prev = None    # 上一任务模型副本
    rho_sched = None   # 模块二的轮次调度模板，(mem_blk, curr_part)，每个年度重设
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ChenEncoderMLP(x_curr.shape[1]).to(device)
            n_params = sum(p.numel() for p in model.parameters())
            print(f"[model] params={n_params:,}", flush=True)

        if strategy in ("naive", "freemoca", "ewc", "lwf"):
            parts = [(x_curr, y_curr)]
        elif strategy == "cumulative":
            parts = [store[y] for y in years[: idx + 1]]
        elif strategy == "expreplay":
            if buffer_scheme != "reservoir":
                # 官方语义是「当年训练前，缓冲只含**此前**年度」（add_batch 在评价之后）
                if idx == 0:
                    parts = [(x_curr, y_curr)]
                else:
                    blocks = split_by_year(store, years[:idx], memory, buf_rng, buffer_scheme)
                    if not blocks:
                        parts = [(x_curr, y_curr)]
                    else:
                        # 缓冲构成诊断（只读记录，不改训练行为、不动随机源）：
                        # 之前没有任何产物记录过**配额臂**的年度构成——表 3-7 记的是官方蓄水池。
                        for yr, _, yb in blocks:
                            nb = int(yb.size)
                            pb = int((yb == 1).sum())
                            src = store[yr][1]
                            ns, psrc = int(src.size), int((src == 1).sum())
                            print(f"[audit] 截至{year} 缓冲块 {yr}: {nb}槽 正例{pb} 负例{nb - pb} "
                                  f"| 源 {psrc}/{ns} = {psrc / max(ns, 1):.4f}", flush=True)
                    if not blocks:
                        pass
                    elif reuse_scheme == "deficit":
                        # 模块二的复用分配：每个年度按其正例数获得不同重复次数
                        reps = reuse_by_deficit(blocks, buffer_repeat)
                        parts = [(x_curr, y_curr)]
                        for yr, X, y in blocks:
                            parts += [(X.astype(np.int8), y.astype(np.float32))] * reps[yr]
                    else:
                        # 模块二的统一复用：所有年度共用同一倍数
                        blk = (np.concatenate([X for _, X, _ in blocks]).astype(np.int8),
                               np.concatenate([y for _, _, y in blocks]).astype(np.float32))
                        parts = [(x_curr, y_curr)] + [blk] * buffer_repeat
            elif len(buffer):
                xb, yb = buffer.sample()
                blk = (xb.astype(np.int8), yb.astype(np.float32))
                # 模块二（$m$ 杠杆）：把**同一批**历史样本在拼接集中重复 `buffer_repeat` 次。
                # 因 `iterate_batches_parts` 做全局洗牌，这等价于「每条历史样本每轮被看
                # `buffer_repeat` 次」——**不增加一个比特存储**，只增加计算量（每轮多
                # `200*(r-1)` 行，占 `~0.3%`）。
                parts = [(x_curr, y_curr)] + [blk] * buffer_repeat
                if reuse_schedule == "rho":
                    # 轮次调度由 train_epochs 自行决定每轮份数，此处只放一份作模板
                    rho_sched = (blk, (x_curr, y_curr))
                    parts = [(x_curr, y_curr), blk]
            else:
                parts = [(x_curr, y_curr)]
        else:
            raise ValueError(strategy)

        n_train = int(sum(p[0].shape[0] for p in parts))
        # FreeMOCA 需要 θ_prev（只看不存样本；t=1 不插值，对齐官方 Algorithm 1 第 5 行）
        prev_state = ({k: v.detach().clone() for k, v in model.state_dict().items()}
                      if (strategy == "freemoca" and idx > 0) else None)
        # EWC / LwF 的参数侧惩罚（t=1 无历史 ⇒ 无惩罚）
        # 注：EWC 用**上一任务的** Fisher 与锚点（不做多任务累加，简化版，已登记）
        penalty = None
        if strategy == "ewc" and ewc_state is not None:
            penalty = ("ewc", ewc_state[0], ewc_state[1])
        elif strategy == "lwf" and lwf_prev is not None:
            penalty = ("lwf", lwf_prev)
        t0 = time.time()
        # 参数锚定兜底（FOREVER Eq.11 式）：Θ* 取**上一经验（年度）训练结束的权重**
        # （FOREVER Algorithm 1 的任务末权重粒度）。首年无历史不锚定；锚定每年重设、
        # 年度内固定，不随轮次更新。
        anchor_theta = ([p.detach().clone() for p in model.parameters()]
                        if (anchor_beta > 0.0 and idx > 0) else None)
        train_epochs(model, parts, epochs, batch, lr, device, rng, penalty=penalty,
                     rho_sched=(*rho_sched, rho_a_star, reuse_cap, rho_ema) if rho_sched else None,
                     l2_beta=anchor_beta, theta_star=anchor_theta)
        rho_sched = None
        if prev_state is not None:
            freemoca_interpolate(prev_state, model)
            print(f"[{year}] FreeMOCA 逐参数插值完成（λ∈[{FREEMOCA_LAMBDA_MIN},{FREEMOCA_LAMBDA_MAX}]）", flush=True)
        # 任务结束后更新参数侧状态，供**下一任务**使用（EWC 用本任务 Fisher＋锚点；LwF 存本任务模型）
        if strategy == "ewc":
            ewc_state = (compute_fisher(model, parts, batch, device),
                         [p.detach().clone() for p in model.parameters()])
            print(f"[{year}] EWC Fisher 已更新（λ={EWC_LAMBDA}）", flush=True)
        elif strategy == "lwf":
            lwf_prev = copy.deepcopy(model)
        print(f"[{year}] trained on {n_train:,} rows in {time.time()-t0:.1f}s", flush=True)

        for j, ty in enumerate(years[: idx + 1]):
            xt, yt = load_year(ty, "test")
            m = evaluate(model, xt, yt, batch, device)
            records.append({"experience": year, "test_year": ty, "mode": "backward", **m})
        for ty in years[idx + 1 :]:
            xt, yt = load_year(ty, "test")
            m = evaluate(model, xt, yt, batch, device)
            records.append({"experience": year, "test_year": ty, "mode": "forward", **m})

        if buffer is not None:
            buffer.add_batch(x_curr, y_curr, year)

        # 每个 experience 立即落盘（长任务检查点）
        back = [r for r in records if r["experience"] == year and r["mode"] == "backward"]
        fwd = [r for r in records if r["experience"] == year and r["mode"] == "forward"]
        write_json(metrics_path, {
            "run_name": RUN_NAME, "strategy": strategy, "records": records,
            "avg_f1_by_experience": {
                str(year): {
                    "backward": float(np.mean([r["f1"] for r in back])) if back else None,
                    "forward": float(np.mean([r["f1"] for r in fwd])) if fwd else None,
                    "n_backward": len(back), "n_forward": len(fwd),
                }
            },
            "wall_seconds": time.time() - t_start, "ts": now_utc(),
        })
        print(f"[{year}] avg_f1 backward={np.mean([r['f1'] for r in back]):.4f}", flush=True)

    write_json(status, {"status": "completed", "strategy": strategy, "ts": now_utc()})
    final = max(years)
    last = [r for r in records if r["experience"] == final and r["mode"] == "backward"]
    print(f"\n=== {strategy}：末年 {final} 的 avg_f1（官方报告口径）= "
          f"{np.mean([r['f1'] for r in last]):.4f} ===")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="LAMDA 官方 Domain-IL 复现")
    p.add_argument("--strategy", choices=("naive", "cumulative", "expreplay", "freemoca", "ewc", "lwf"), required=True)
    p.add_argument("--epochs", type=int, default=OFFICIAL_EPOCHS)
    p.add_argument("--batch", type=int, default=OFFICIAL_BATCH)
    p.add_argument("--lr", type=float, default=OFFICIAL_LR)
    p.add_argument("--memory", type=int, default=OFFICIAL_MEMORY)
    p.add_argument("--reuse-schedule", choices=("off", "rho"), default="off",
                   help="off = 各轮次复用倍数相同（默认）；rho = 每轮实测历史梯度与当前梯度的"
                        "余弦相似度，由一阶条件反解该轮的历史权重（模块二的轮次调度形态）。"
                        "仅对 --strategy expreplay 生效。")
    p.add_argument("--reuse-cap", type=int, default=64,
                   help="轮次调度的**每轮复用倍数上界**（默认 64，即近乎不限）。判别实验用："
                        "四篇先例全部约束每步上界（3×/20×/每步1:5/总量不变），本脚本原本只约束"
                        "均值。设为 8 即把分布夹到 [1,8] 而均值仍可由 --rho-a-star 标定到 4。")
    p.add_argument("--rho-a-star", type=float, default=RHO_A_STAR,
                   help="轮次调度的标定量 a*（默认取模块常量）。改上界或 EMA 后须重新标定："
                        "cap=8 无平滑取 0.99091；cap8+β=0.5 取 0.990196；cap8+β=0.7 取 0.989397。")
    p.add_argument("--rho-ema", type=float, default=0.0,
                   help="轮次调度的 ρ EMA 平滑系数 β（0 = 关闭，默认）。>0 时每轮改用 "
                        "ρ_smooth = β·ρ_smooth_prev + (1−β)·ρ_now，只在同一年度的轮次之间延续、"
                        "不跨年度。取值依据（魔法数字门禁登记）：110 个实测 ρ 去趋势后 lag-1 自相关 "
                        "−0.12（近白噪声），EMA 只降噪不丢动态；β∈{0.5,0.7,0.9} 相对年内均值的平均跟踪"
                        "误差 0.158/0.140/0.205，β=0.9 已因滞后反弹，故取 0.5 与 0.7 两档。"
                        "β 使 m_r(ρ) 凸映射下的均值下降，a* 须重标：β=0.5→0.990196，β=0.7→0.989397"
                        "（cap 8，用 cap8 跑实测 ρ 离线二分标定到平均 repeat≈4）。")
    p.add_argument("--anchor-beta", type=float, default=0.0,
                   help="参数锚定兜底系数 β（0 = 关闭，默认）。>0 时每批损失加 β·‖Θ−Θ*‖²，"
                        "Θ* 取**上一经验（年度）训练结束的权重**，每年重设、年度内固定，"
                        "首年无历史不锚定。形式与 FOREVER Eq.11 同形（其 Algorithm 1 锚定"
                        "上一任务末权重 Θ^{k-1}；粒度选择的文献依据）。β 量级对齐原则取自"
                        "FOREVER（其 Fig.6 讨论：β_base 使正则项与任务损失处于可比数值量级，"
                        "名义 1e-3 为其 LLM 短回放场景的标定值，不直接照搬）。本数据标定："
                        "源侧 2013→2014 两年短程扫描 β∈{1e-4,1e-3,1e-2}，取锚定项/数据损失"
                        "轮均比值最接近 0.1 者（0.1 = 全程作用相对 FOREVER 短回放事件的保守化，"
                        "任务化设定，无直接文献页码）。实测比值见 [anchor] 行（标定与正式臂日志）。")
    p.add_argument("--reuse-scheme", choices=("uniform", "deficit"), default="uniform",
                   help="uniform = 所有年度共用同一复用倍数（默认，文件名不变）；"
                        "deficit = 按各年度缓冲块的正例数分配复用次数，正例少的年度重复更多。"
                        "仅对 --strategy expreplay 生效。")
    p.add_argument("--buffer-scheme",
                   choices=("reservoir", "quota", "prop_strat", "equal_unstrat"),
                   default="reservoir",
                   help="reservoir = 官方全局蓄水池（默认，文件名不变），即「按样本量比例 + 年内不分层」；"
                        "quota = 按年等额＋年内正负各半（本章模块一）；"
                        "prop_strat = 按样本量比例＋年内正负各半；"
                        "equal_unstrat = 按年等额＋年内不分层。"
                        "后两者与 quota 构成 2×2，用于分离「年度间分配」与「年内分层」"
                        "（2026-10-15 加：quota 臂此前把这两件事捆绑在一起）。"
                        "仅对 --strategy expreplay 生效。")
    p.add_argument("--buffer-repeat", type=int, default=1,
                   help="模块二（$m$ 杠杆）：历史样本块每轮重复次数。默认 1 = 官方语义，"
                        "文件名与既有产物保持一致。仅对 --strategy expreplay 生效。")
    p.add_argument("--seed", type=int, default=SEED,
                   help="多种子复现用；官方未设种子（其 run 脚本循环 3 次不传 seed）。"
                        "默认 42 = 本脚本既有全部产物所用的种子，文件名不变。")
    p.add_argument("--years-limit", type=int, default=None,
                   help="只跑前 N 个 experience（调试用；正式复现不设）")
    a = p.parse_args()
    raise SystemExit(main(a.strategy, a.epochs, a.batch, a.lr, a.memory, a.years_limit,
                          a.buffer_repeat, a.seed, a.buffer_scheme, a.reuse_scheme,
                          a.reuse_schedule, a.reuse_cap, a.rho_a_star, a.rho_ema,
                          a.anchor_beta))
