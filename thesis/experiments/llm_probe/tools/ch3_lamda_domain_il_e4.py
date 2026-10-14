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
        self.data: list[tuple[np.ndarray, float]] = []
        self.n_seen = 0
        self.rng = np.random.default_rng(OFFICIAL_RNG_SEED)

    def add_batch(self, x: np.ndarray, y: np.ndarray, year: int) -> None:
        for xi, yi in zip(x, y):
            self.n_seen += 1
            if len(self.data) < self.capacity:
                self.data.append((xi, float(yi)))
            else:
                j = int(self.rng.integers(0, self.n_seen))
                if j < self.capacity:
                    self.data[j] = (xi, float(yi))

    def sample(self) -> tuple[np.ndarray, np.ndarray]:
        xs = np.stack([d[0] for d in self.data])
        ys = np.array([d[1] for d in self.data], dtype=np.float32)
        return xs, ys

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


def train_epochs(model, parts, epochs, batch, lr, device, rng, penalty=None) -> None:
    """`parts` 为 [(X_int8, y_float32), ...]，按官方语义全局洗牌后取批（虚拟拼接，见上）。

    `penalty`（可选）＝`("ewc", fisher_list, anchor_list)` 或 `("lwf", prev_model)`，
    分别对应参数侧的两条经典保持路线；**默认 None ⇒ 行为与官方 naive 逐位一致**。
    """
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=OFFICIAL_MOMENTUM,
                          weight_decay=OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss()
    if penalty and penalty[0] == "lwf":
        penalty[1].eval()
    model.train()
    for _ in range(epochs):
        for xb, yb in iterate_batches_parts(parts, batch, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            out = model(xt)
            loss = criterion(out, yt)
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


def main(strategy: str, epochs: int, batch: int, lr: float, memory: int, years_limit: int | None,
         buffer_repeat: int = 1, seed: int = SEED) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    # 存储预算曲线需要对同一策略跑多个容量 ⇒ 文件名必须带容量，否则互相覆盖。
    # 后缀仅在**偏离官方默认**时追加，以保持既有 `metrics_expreplay_m200.json` 等文件名不变。
    if strategy == "expreplay":
        tag = f"{strategy}_m{memory}"
        if buffer_repeat != 1:
            tag += f"_r{buffer_repeat}"
    else:
        tag = strategy
    if seed != SEED:                      # 多种子复现：官方未设种子，本脚本默认 42
        tag += f"_s{seed}"
    status = RUN_DIR / f"status_{tag}.json"
    metrics_path = RUN_DIR / f"metrics_{tag}.json"
    write_json(status, {"status": "running", "strategy": strategy, "ts": now_utc()})

    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    rng = np.random.default_rng(seed)

    years = DOMAIN_YEARS if not years_limit else DOMAIN_YEARS[:years_limit]
    buffer = ReplayBuffer(memory) if strategy == "expreplay" else None

    # 预载全部年份到主机内存（int8；官方逐次读盘，见偏离 2 的注释）
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in DOMAIN_YEARS:
        store[y] = load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    model = None
    records: list[dict] = []
    ewc_state = None   # (fisher_list, anchor_list)，均为**上一任务**的量
    lwf_prev = None    # 上一任务模型副本
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
            if len(buffer):
                xb, yb = buffer.sample()
                blk = (xb.astype(np.int8), yb.astype(np.float32))
                # 模块二（$m$ 杠杆）：把**同一批**历史样本在拼接集中重复 `buffer_repeat` 次。
                # 因 `iterate_batches_parts` 做全局洗牌，这等价于「每条历史样本每轮被看
                # `buffer_repeat` 次」——**不增加一个比特存储**，只增加计算量（每轮多
                # `200*(r-1)` 行，占 `~0.3%`）。
                parts = [(x_curr, y_curr)] + [blk] * buffer_repeat
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
        train_epochs(model, parts, epochs, batch, lr, device, rng, penalty=penalty)
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
                          a.buffer_repeat, a.seed))
