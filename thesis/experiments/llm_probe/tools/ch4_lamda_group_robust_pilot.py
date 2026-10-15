#!/usr/bin/env python
"""第四章最小先导：跨年度组鲁棒训练（GroupDRO 对 ER，单一冻结种子 42）。

判据与配置来源（**逐条照抄，不得改动**）：
- `.Codex/docs/2026-10-15-第四章先导-组鲁棒/implementation_plan.md`
- 上位判据冻结处 `thesis/methods/第四章研究问题卡-条件漂移下的鲁棒训练.md`

## 主线（复现门）

按 `ch3_lamda_domain_il_e4.py::main()` 的年度循环、以及
`ch4_lamda_rank_gated_acquisition_e2.py` 主线**逐句镜像**（不改原脚本、不 shell 出去调它）：
`strategy=expreplay`、`buffer-scheme=quota`、`reuse-scheme=deficit`、`buffer-repeat=2`、
容量 `200`、`10` 轮、批 `1024`、`lr=0.01`、`seed=42`、阈值 `0.5`。

`--arm er` 的期望末年 `2025` 的 12 年平均 F1 == `0.8170`
（第三章制品 `metrics_expreplay_m200_quota_deficit_r2.json` 实测
`0.8169830287163194`，逐年度值同文件）。

## 两臂

| 臂 | 目标 |
| --- | --- |
| `er` | 经验风险最小化——直接调 `ch3.train_epochs`，逐位复现第三章基线 |
| `groupdro` | 组鲁棒——只改**损失加权**，其余逐位不变 |

**唯一变量**：`groupdro` 臂把批内样本损失按组权重 $q_{g(x)}$ 加权后归一化，
$q$ 用指数梯度 $q_g \\propto q_g\\exp(\\eta\\,\\bar\\ell_g)$ 逐批更新。
缓冲构成、复用倍数、轮数、批大小、学习率、随机源与批序均与 `er` 臂相同，
运行内断言见 `_selfcheck_iterator_parity` 与 `_selfcheck_uniform_loss_is_er`
（两者均在每次运行中实际执行并打印）。

## 组定义（冻结，照实施计划 §2）

某次训练用到的 parts 里，**每个年度块自成一組**（当年度分片为一组，缓冲中每个年度块各为一组）。
组权重向量长度随已见年度增长。

## η——实施计划的规格缺口，本脚本登记取值

实施计划只写 $q_g \\propto q_g\\exp(\\eta\\,\\bar\\ell_g)$，**未给出 η 的数值**。
本脚本取 **η = 1.0**。依据：Sagawa 等 (ICLR 2020) 的指数梯度形式；
本地全文笔记 `wiki/papers/methodology/2020-Sagawa-GroupDRO群体移位.md`
第 24 行与第 52 行给出该形式但同样未给常数，故 η=1.0 是该形式的
**无标定默认步长**，**不是从本数据标定所得**。该取值属实现缺口填充，
已在交付报告中显式披露。

## 数据根

`DATA_ROOT` **必须**从环境变量 `LAMDA_DATA_ROOT` 解析；未设置或不存在即报错退出，
**不在本脚本写死绝对路径**。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_group_robust_pilot.py --arm er
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_group_robust_pilot.py --arm groupdro

## 实现说明（规格未规定、由本脚本确定并登记，**非科研数值改动**）

1. 两臂用**同一随机源构造方式**（`train_rng = default_rng(SEED)`、
   `buf_rng = default_rng(SEED)`，且都在每个年度按同一顺序消费），
   使两臂的 parts 与批序**逐位一致**，唯一差异是损失加权。
2. `groupdro` 的 $q$ 在**每个年度重新置为均匀**（每次训练 = 一个年度；
   各组标签随缓冲块变化，跨年度沿用需重索引）。年度内逐批更新，
   末轮末批后的 $q$ 记为本年度"末轮组权重"。
3. 组内均值损失只统计**该批内出现的组**；批内缺失的组权重不动。
   $q$ 每批更新后整体归一化（$\\sum_g q_g = 1$）。
4. 逐样本预测（`preds_<arm>_<year>.npz`）取**末年模型**（experience = 2025）对
   该年度测试分片的分数，与"末年 12 年平均 F1"口径一致。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）

# ---------------------------------------------------------------------------
# 冻结配置（照 implementation_plan.md §2、§3，不得改动）
# ---------------------------------------------------------------------------
RUN_NAME = "ch4-lamda-group-robust-pilot"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME

BUFFER_SCHEME = "quota"      # 第三章冻结值
REUSE_SCHEME = "deficit"     # 第三章冻结值
BUFFER_REPEAT = 2            # 第三章冻结值（deficit 的 m_max）
MEMORY = 200                 # 第三章冻结容量
POS_RATIO = 0.5              # 第三章冻结值
DEFICIT_GAMMA = 1.0          # 第三章冻结值
GROUP_DRO_ETA = 1.0          # 实施计划未给值；取 Sagawa 参考实现的无标定默认步长（见模块文档）

BOOTSTRAP_N = 2000           # 配对 bootstrap 重采样次数（计划 §3）
BOOTSTRAP_SEED = 42
GATE_ER_REF = 0.8169830287163194   # 第三章 metrics_expreplay_m200_quota_deficit_r2.json 实测
GATE_ER_TOL = 1e-6

DATA_ROOT_ENV = "LAMDA_DATA_ROOT"

CRITERIA_TEXT = (
    "主判据：2024 年度测试分片上的 F1，ΔF1 = F1_groupdro − F1_er。"
    "支持：ΔF1(2024) > 0 且配对 bootstrap 95% CI 不含 0，且早期年度（2013/2014/2016）的 F1 "
    "下降不超过同年零假设尺度。"
    "部分支持：2024 改善但 CI 含 0。"
    "证伪：2024 不升，或早期年度显著下降（搬移错误而非降低最坏风险）。"
    "强证伪：ΔF1(2024) ≤ 0 且 CI 不含 0 ⇒ 卡作废，第四章重新选题。"
    "不确定性：单一冻结种子 42（禁多种子）；测试集配对 bootstrap n=2000，"
    "只量化样本不确定性，不冒充训练随机性。"
)

ARMS = ("er", "groupdro")


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写出（与 ch3 的 write_json 同型：先写 .partial，再 os.replace）。"""
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def resolve_data_root() -> Path:
    """数据根**只**从环境变量解析；未设置或不存在即报错退出（不写死绝对路径）。"""
    raw = os.environ.get(DATA_ROOT_ENV)
    if not raw:
        raise SystemExit(
            f"ERROR: 环境变量 {DATA_ROOT_ENV} 未设置。请先导出数据根路径，例如：\n"
            f"  export {DATA_ROOT_ENV}=<repo>/thesis/experiments/llm_probe/runs/data-raw/"
            f"lamda-iclr2026-baseline-ad9614bdd5556767"
        )
    root = Path(raw)
    if not root.is_dir():
        raise SystemExit(f"ERROR: {DATA_ROOT_ENV} 指向的目录不存在：{root}")
    return root


class _Tee:
    """把 stdout 同时写到控制台与日志文件。"""

    def __init__(self, *streams: Any) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for s in self._streams:
            s.write(data)
        return len(data)

    def flush(self) -> None:
        for s in self._streams:
            s.flush()

    @property
    def encoding(self) -> str:
        return "utf-8"


# ---------------------------------------------------------------------------
# parts 构造（逐句镜像 E2 主线；**多带一份每块所属年度**）
# ---------------------------------------------------------------------------
def build_parts_and_groups(
    store: dict[int, tuple[np.ndarray, np.ndarray]],
    years: list[int],
    idx: int,
    year: int,
    x_curr: np.ndarray,
    y_curr: np.ndarray,
    buf_rng: np.random.Generator,
) -> tuple[list[tuple[np.ndarray, np.ndarray]], list[int], dict[str, Any]]:
    """返回 (parts, gids, meta)。

    `parts`、`blocks`、`reps` 的构造与 `ch3.main` 的
    `expreplay + buffer_scheme=quota + reuse_scheme=deficit` 分支逐句一致；
    `gids[i]` = `parts[i]` 所属的**年度组标签**（当年度分片为 `year`，
    缓冲块为各自来源年度）。**这是在同一条数据流上附加的只读标注，不改变任何构造。**
    """
    if idx == 0:
        return [(x_curr, y_curr)], [year], {"blocks": [], "reps": {}}

    blocks = ch3.split_by_year(store, years[:idx], MEMORY, buf_rng, BUFFER_SCHEME, POS_RATIO)
    if not blocks:
        return [(x_curr, y_curr)], [year], {"blocks": [], "reps": {}}

    reps = ch3.reuse_by_deficit(blocks, BUFFER_REPEAT, DEFICIT_GAMMA)
    parts: list[tuple[np.ndarray, np.ndarray]] = [(x_curr, y_curr)]
    gids: list[int] = [year]
    for yr, X, y in blocks:
        parts += [(X.astype(np.int8), y.astype(np.float32))] * reps[yr]
        gids += [yr] * reps[yr]
    return parts, gids, {"blocks": blocks, "reps": dict(reps)}


def iterate_batches_parts_grouped(
    parts: list[tuple[np.ndarray, np.ndarray]],
    gids: list[int],
    batch: int,
    rng: np.random.Generator,
    shuffle: bool,
):
    """与 `ch3.iterate_batches_parts` **逐位同型**的虚拟拼接取批器，额外产出组标签批。

    除多产出一列 `gb`（每样本的年度组标签）外，索引、切分、`sel.size < 2` 跳过规则
    与 `ch3.iterate_batches_parts` 完全相同；对同一 rng 状态产出相同批次。
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
        gb = np.empty(sel.size, dtype=np.int64)
        for pi in np.unique(which):
            m = which == pi
            loc = sel[m] - cum[pi]
            xs[m] = parts[pi][0][loc]
            ys[m] = parts[pi][1][loc]
            gb[m] = gids[pi]
        yield xs, ys, gb


# ---------------------------------------------------------------------------
# GroupDRO 训练：**只改损失加权**，其余与 ch3.train_epochs 逐句同型
# ---------------------------------------------------------------------------
def train_epochs_groupdro(
    model: nn.Module,
    parts: list[tuple[np.ndarray, np.ndarray]],
    gids: list[int],
    epochs: int,
    batch: int,
    lr: float,
    device: torch.device,
    rng: np.random.Generator,
    eta: float,
) -> dict[str, Any]:
    """组鲁棒训练。优化器、轮数、批大小、学习率、取批与 shuffle 与 `ch3.train_epochs` 相同。

    唯一改动：批内逐样本损失按 $q_{g(x)}$ 加权后归一化；
    $q$ 由指数梯度 $q_g \\leftarrow q_g\\exp(\\eta\\,\\bar\\ell_g)$ 逐批更新并归一化，
    其中 $\\bar\\ell_g$ 为该批内组 $g$ 的均值 BCE（批内缺失的组不更新）。
    $q$ 均匀时该损失**恒等于** `nn.BCELoss()`（mean），即退化为 ER 的损失
    （运行内由 `_selfcheck_uniform_loss_is_er` 断言）。
    """
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss(reduction="none")
    model.train()

    groups = sorted({int(g) for g in gids})
    gidx = {g: i for i, g in enumerate(groups)}
    q = np.full(len(groups), 1.0 / len(groups), dtype=np.float64)

    trace: dict[str, Any] = {"groups": groups, "eta": eta,
                             "q_epoch_end": [], "epoch_mean_loss": [], "q_final": None}

    for _ in range(epochs):
        epoch_loss = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb, gb in iterate_batches_parts_grouped(parts, gids, batch, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            gi = np.array([gidx[int(g)] for g in gb], dtype=np.int64)

            opt.zero_grad()
            out = model(xt)
            per_sample = criterion(out, yt).squeeze(1)        # (B,) 逐样本 BCE

            # --- 组权重指数梯度更新（逐批；只用批内出现的组的均值损失）---
            per_sample_np = per_sample.detach().cpu().numpy()
            for g in np.unique(gi):
                q[g] = q[g] * np.exp(eta * float(per_sample_np[gi == g].mean()))
            q = q / q.sum()

            w = torch.from_numpy(q[gi]).to(device)
            loss = (per_sample * w).sum() / w.sum()
            epoch_loss = epoch_loss + loss.detach()
            n_batches += 1
            loss.backward()
            opt.step()

        trace["q_epoch_end"].append([float(v) for v in q])
        trace["epoch_mean_loss"].append(float(epoch_loss.item() / max(n_batches, 1)))

    trace["q_final"] = [float(v) for v in q]
    return trace


# ---------------------------------------------------------------------------
# 运行内自检（**证明 groupdro 只改损失加权**）
# ---------------------------------------------------------------------------
def _selfcheck_iterator_parity(
    parts: list[tuple[np.ndarray, np.ndarray]],
    gids: list[int],
    batch: int,
    seed: int,
    max_batches: int = 3,
) -> None:
    """断言分组取批器与 `ch3.iterate_batches_parts` **逐位一致**（同批序、同数组）。

    用两个**独立**的 rng（同种子）分别驱动两个迭代器，不触碰训练随机源。
    """
    a = ch3.iterate_batches_parts(parts, batch, np.random.default_rng(seed), True)
    b = iterate_batches_parts_grouped(parts, gids, batch, np.random.default_rng(seed), True)
    n = 0
    for (xa, ya), (xb, yb, gb) in zip(a, b):
        assert xa.shape == xb.shape and ya.shape == yb.shape, "取批形状不一致"
        assert np.array_equal(xa, xb) and np.array_equal(ya, yb), "取批内容不一致"
        assert gb.size == xb.shape[0], "组标签批长度与样本批不一致"
        n += 1
        if n >= max_batches:
            break
    assert n > 0, "未取到任何批，自检不成立"
    print(f"[selfcheck] 分组取批器与 ch3.iterate_batches_parts 逐位一致（前 {n} 批）", flush=True)


def _selfcheck_uniform_loss_is_er(
    model: nn.Module,
    parts: list[tuple[np.ndarray, np.ndarray]],
    gids: list[int],
    batch: int,
    device: torch.device,
    seed: int,
) -> None:
    """断言：q 均匀时组加权损失 == `nn.BCELoss()`（mean），即退化为 ER 的损失。"""
    crit_mean = nn.BCELoss()
    crit_none = nn.BCELoss(reduction="none")
    it = iterate_batches_parts_grouped(parts, gids, batch, np.random.default_rng(seed), False)
    xb, yb, gb = next(it)
    xt = torch.from_numpy(xb.astype(np.float32)).to(device)
    yt = torch.from_numpy(yb).to(device).unsqueeze(1)
    uniq = np.unique(gb)
    q = np.full(uniq.size, 1.0 / uniq.size)
    w = torch.from_numpy(q[np.searchsorted(uniq, gb)]).to(device)

    was_training = model.training
    model.eval()
    with torch.no_grad():
        out = model(xt)
        per_sample = crit_none(out, yt).squeeze(1)
        weighted = float(((per_sample * w).sum() / w.sum()).item())
        er_loss = float(crit_mean(out, yt).item())
    if was_training:
        model.train()
    assert abs(weighted - er_loss) < 1e-6, \
        f"q 均匀时组加权损失({weighted}) 不等于 ER 损失({er_loss})"
    print(f"[selfcheck] q 均匀时组加权损失 {weighted:.8f} == ER 损失 {er_loss:.8f}"
          f"（差 {abs(weighted - er_loss):.2e}）", flush=True)


# ---------------------------------------------------------------------------
# 指标与配对 bootstrap
# ---------------------------------------------------------------------------
def _f1_of_scores(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> float:
    pred = (np.asarray(y_score) >= threshold).astype(int)
    return float(f1_score(np.asarray(y_true).astype(int), pred, zero_division=0))


def paired_bootstrap(
    y_true: np.ndarray,
    score_groupdro: np.ndarray,
    score_er: np.ndarray,
    n_boot: int = BOOTSTRAP_N,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """配对 bootstrap：对同一年度测试分片的逐样本判定重采样，给 ΔF1 的 95% 区间。

    **该区间只量化样本不确定性，不冒充训练随机性。**
    """
    n = int(y_true.size)
    rng = np.random.default_rng(seed)
    pg = (score_groupdro >= ch3.THRESHOLD).astype(int)
    pe = (score_er >= ch3.THRESHOLD).astype(int)
    yt = y_true.astype(int)
    obs_g = float(f1_score(yt, pg, zero_division=0))
    obs_e = float(f1_score(yt, pe, zero_division=0))
    diffs = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        diffs[i] = float(f1_score(yt[idx], pg[idx], zero_division=0)) - \
            float(f1_score(yt[idx], pe[idx], zero_division=0))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "observed_delta_f1": obs_g - obs_e,
        "f1_groupdro": obs_g,
        "f1_er": obs_e,
        "mean_delta_f1": float(diffs.mean()),
        "ci95_low": float(lo),
        "ci95_high": float(hi),
        "contains_zero": bool(lo <= 0.0 <= hi),
        "n_boot": int(n_boot),
        "n_test": n,
        "n_pos_test": int((yt == 1).sum()),
        "note": "该区间只量化样本不确定性，不冒充训练随机性",
    }


# ---------------------------------------------------------------------------
# 单臂主循环
# ---------------------------------------------------------------------------
def run_arm(arm: str) -> int:
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[arm] {arm} device={device.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} memory={MEMORY} buffer_scheme={BUFFER_SCHEME} "
          f"reuse_scheme={REUSE_SCHEME} buffer_repeat={BUFFER_REPEAT} "
          f"pos_ratio={POS_RATIO} deficit_gamma={DEFICIT_GAMMA} seed={ch3.SEED} "
          f"threshold={ch3.THRESHOLD} arm={arm}"
          + (f" groupdro_eta={GROUP_DRO_ETA}" if arm == "groupdro" else ""), flush=True)

    rng = np.random.default_rng(ch3.SEED)         # 训练洗牌流（两臂同种子）
    buf_rng = np.random.default_rng(ch3.SEED)     # 缓冲构造流（两臂同种子，独立于训练流）

    years = ch3.DOMAIN_YEARS
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in ch3.DOMAIN_YEARS:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    model: nn.Module | None = None
    records: list[dict] = []
    weight_trace: dict[int, dict] = {}
    preds: dict[int, dict] = {}
    selfchecked = False
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(x_curr.shape[1]).to(device)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,}", flush=True)

        parts, gids, meta = build_parts_and_groups(store, years, idx, year, x_curr, y_curr, buf_rng)
        sizes = [int(p[0].shape[0]) for p in parts]
        print(f"[parts] {year}: n_parts={len(parts)} sizes={sizes} groups={sorted(set(gids))}",
              flush=True)
        for yr, _, yb in meta["blocks"]:
            nb = int(yb.size)
            pb = int((yb == 1).sum())
            src = store[yr][1]
            ns, psrc = int(src.size), int((src == 1).sum())
            print(f"[audit] 截至{year} 缓冲块 {yr}: {nb}槽 正例{pb} 负例{nb - pb} "
                  f"| 源 {psrc}/{ns} = {psrc / max(ns, 1):.4f}", flush=True)
        if meta["reps"]:
            print(f"[reuse] 截至{year} deficit 复用 = {meta['reps']}", flush=True)

        if not selfchecked and len(parts) > 1:
            _selfcheck_iterator_parity(parts, gids, ch3.OFFICIAL_BATCH, ch3.SEED)
            _selfcheck_uniform_loss_is_er(model, parts, gids, ch3.OFFICIAL_BATCH, device, ch3.SEED)
            selfchecked = True

        n_train = int(sum(p[0].shape[0] for p in parts))
        t0 = time.time()
        if arm == "er":
            # 逐位复现第三章基线：直接调用原脚本的训练函数
            ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                             ch3.OFFICIAL_LR, device, rng)
        elif arm == "groupdro":
            trace = train_epochs_groupdro(model, parts, gids, ch3.OFFICIAL_EPOCHS,
                                          ch3.OFFICIAL_BATCH, ch3.OFFICIAL_LR, device, rng,
                                          GROUP_DRO_ETA)
            weight_trace[year] = trace
            gs = trace["groups"]
            qf = trace["q_final"]
            order = np.argsort(-np.asarray(qf))
            print(f"[q] {year} 末轮组权重（降序）: "
                  + ", ".join(f"{gs[i]}={qf[i]:.4f}" for i in order), flush=True)
            print(f"[q] {year} 组权重熵={_entropy(qf):.4f} max组={gs[int(order[0])]} "
                  f"maxq={qf[int(order[0])]:.4f}", flush=True)
            print(f"[q] {year} epoch 均损失: "
                  + ", ".join(f"{v:.4f}" for v in trace["epoch_mean_loss"]), flush=True)
        else:  # pragma: no cover
            raise ValueError(arm)
        print(f"[{year}] trained on {n_train:,} rows in {time.time() - t0:.1f}s", flush=True)

        for ty in years[: idx + 1]:
            xt, yt = ch3.load_year(ty, "test")
            m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, device)
            records.append({"experience": year, "test_year": ty, "mode": "backward", **m})
        for ty in years[idx + 1 :]:
            xt, yt = ch3.load_year(ty, "test")
            m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, device)
            records.append({"experience": year, "test_year": ty, "mode": "forward", **m})

        back = [r for r in records if r["experience"] == year and r["mode"] == "backward"]
        print(f"[{year}] avg_f1 backward={np.mean([r['f1'] for r in back]):.4f}", flush=True)

        # 末年的模型对全部 12 个测试分片逐样本打分（主判据与 bootstrap 用）
        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, device).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
                rec = next(r for r in records
                           if r["experience"] == year and r["test_year"] == ty
                           and r["mode"] == "backward")
                f1m = _f1_of_scores(yt, sc, ch3.THRESHOLD)
                assert abs(f1m - float(rec["f1"])) < 1e-12, \
                    f"evaluate 与分数口径不一致 {arm} {ty}: {rec['f1']} vs {f1m}"
                print(f"[preds] {arm} 末年模型 @{ty}: f1={f1m:.4f} n={int(yt.size)} "
                      f"pos={int((yt == 1).sum())}", flush=True)

    final = max(years)
    last = [r for r in records if r["experience"] == final and r["mode"] == "backward"]
    per_year = {int(r["test_year"]): float(r["f1"]) for r in last}
    final_avg = float(np.mean([r["f1"] for r in last]))
    print(f"\n=== {arm}：末年 {final} 的 avg_f1（官方报告口径）= {final_avg:.4f} ===", flush=True)

    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(ch3.THRESHOLD))

    # ---- 结果落盘（多臂合并；两次运行各自追加自己的臂）----
    res_path = RUN_DIR / "e4p_results.json"
    results: dict[str, Any] = json.loads(res_path.read_text()) if res_path.exists() else {}
    results.setdefault("run_name", RUN_NAME)
    results["ts"] = now_utc()
    results["criteria_text"] = CRITERIA_TEXT
    arms = results.setdefault("arms", {})
    arms[arm] = {
        "final_year": final,
        "final_avg_f1_backward": final_avg,
        "per_year_f1_final_experience": per_year,
        "wall_seconds": round(time.time() - t_start, 1),
        "records": records,
    }
    if arm == "groupdro":
        arms[arm]["groupdro_eta"] = GROUP_DRO_ETA
        arms[arm]["group_weight_trace"] = {str(k): v for k, v in weight_trace.items()}

    if all((RUN_DIR / f"preds_{a}_{ty}.npz").exists() for a in ARMS for ty in years):
        results["comparison"] = build_comparison(years, results)
        print("[comparison] 两臂预测齐备，已计算 ΔF1 与配对 bootstrap", flush=True)
    write_json(res_path, results)
    print(f"[done] {arm} 用时 {time.time() - t_start:.1f}s，制品 {res_path}", flush=True)

    if arm == "er":
        delta = abs(final_avg - GATE_ER_REF)
        ok = delta < GATE_ER_TOL
        print(f"[gate] er 复现门：末年 12 年平均 F1 = {final_avg:.10f}，"
              f"参照 {GATE_ER_REF:.10f}，绝对差 {delta:.3e} ⇒ "
              f"{'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            print("[gate] er 未复现参照值，按实施计划 §6 停止（不得调数凑）", flush=True)
            return 1
    return 0


def _entropy(q: list[float]) -> float:
    arr = np.asarray(q, dtype=np.float64)
    arr = arr[arr > 0]
    return float(-(arr * np.log(arr)).sum())


def build_comparison(years: list[int], results: dict[str, Any]) -> dict[str, Any]:
    """由两臂的逐样本预测计算 ΔF1（逐年）与配对 bootstrap（主判据 2024）。"""
    comp: dict[str, Any] = {"pair": ["groupdro", "er"], "per_year": {}, "bootstrap": {}}
    er_arm = results["arms"].get("er", {})
    gr_arm = results["arms"].get("groupdro", {})
    for ty in years:
        e = np.load(RUN_DIR / f"preds_er_{ty}.npz")
        g = np.load(RUN_DIR / f"preds_groupdro_{ty}.npz")
        assert np.array_equal(e["y_true"], g["y_true"]), f"两臂 y_true 顺序不一致 @{ty}"
        der = float(er_arm["per_year_f1_final_experience"][str(ty)])
        dgr = float(gr_arm["per_year_f1_final_experience"][str(ty)])
        boot = paired_bootstrap(e["y_true"], g["y_score"], e["y_score"])
        comp["per_year"][str(ty)] = {"f1_er": der, "f1_groupdro": dgr, "delta": dgr - der}
        comp["bootstrap"][str(ty)] = boot
    comp["mean_f1_er"] = float(np.mean([v["f1_er"] for v in comp["per_year"].values()]))
    comp["mean_f1_groupdro"] = float(np.mean([v["f1_groupdro"] for v in comp["per_year"].values()]))
    comp["primary_test_year"] = 2024
    comp["primary"] = {
        "delta_f1_2024": comp["per_year"]["2024"]["delta"],
        "bootstrap": comp["bootstrap"]["2024"],
    }
    return comp


# ---------------------------------------------------------------------------
def main(arm: str) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    protocol_path = RUN_DIR / "e4p_protocol.json"
    if not protocol_path.exists():
        protocol = {
            "run_name": RUN_NAME,
            "ts": now_utc(),
            "criteria_text": CRITERIA_TEXT,
            "arms": list(ARMS),
            "mainline": {
                "strategy": "expreplay", "buffer_scheme": BUFFER_SCHEME,
                "reuse_scheme": REUSE_SCHEME, "buffer_repeat": BUFFER_REPEAT,
                "memory": MEMORY, "epochs": ch3.OFFICIAL_EPOCHS, "batch": ch3.OFFICIAL_BATCH,
                "lr": ch3.OFFICIAL_LR, "pos_ratio": POS_RATIO, "deficit_gamma": DEFICIT_GAMMA,
                "seed": ch3.SEED, "threshold": ch3.THRESHOLD,
                "domain_years": list(ch3.DOMAIN_YEARS),
            },
            "group_definition": "某次训练用到的 parts 里，每个年度块自成一組"
                                "（当年度分片为一组，缓冲中每个年度块各为一组）",
            "groupdro": {
                "eta": GROUP_DRO_ETA,
                "eta_provenance": "实施计划未给 η 数值；取 Sagawa ICLR2020 指数梯度形式的"
                                  "无标定默认步长 1.0，非本数据标定值（规格缺口，见报告）",
                "q_init": "每个年度重新置为均匀（每次训练 = 一个年度）",
                "q_update": "逐批：批内各组均值 BCE ℓ̄_g，q_g ← q_g·exp(η·ℓ̄_g)，再整体归一化",
                "loss": "批内逐样本 BCE 按 q_{g(x)} 加权后归一化 Σq·ℓ/Σq",
                "only_variable": "组加权损失；缓冲构成/复用倍数/轮数/批大小/学习率/随机源/批序"
                                 "均与 er 臂逐位相同",
            },
            "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED,
            "gate_er": {"expected": GATE_ER_REF, "tol": GATE_ER_TOL,
                        "reference_artifact": "ch3-lamda-domain-il-e4-replication-v1/"
                                              "metrics_expreplay_m200_quota_deficit_r2.json"},
            "data_root": str(ch3.DATA_ROOT),
            "env_data_root_var": DATA_ROOT_ENV,
        }
        write_json(protocol_path, protocol)
        print(f"[protocol] 已写出 {protocol_path}", flush=True)

    return run_arm(arm)


if __name__ == "__main__":
    ch3.DATA_ROOT = resolve_data_root()   # 覆盖被导入模块的 DATA_ROOT（不写死绝对路径）
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    _log_fh = (RUN_DIR / "full_pilot.log").open("a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_fh)
    sys.stderr = _Tee(sys.__stderr__, _log_fh)
    p = argparse.ArgumentParser(description="第四章最小先导：跨年度组鲁棒训练（GroupDRO 对 ER）")
    p.add_argument("--arm", choices=ARMS, required=True,
                   help="er = 经验风险最小化（第三章基线，必须复现 0.8170）；"
                        "groupdro = 组鲁棒（只改损失加权）")
    a = p.parse_args()
    try:
        raise SystemExit(main(a.arm))
    finally:
        _log_fh.flush()
