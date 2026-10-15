#!/usr/bin/env python
"""第四章最小先导：跨年度动量状态的衰减／重置（单一冻结种子 42）。

判据与配置来源（**逐条照抄，不得改动**）：
- `.Codex/docs/2026-10-15-第四章先导-动量状态/implementation_plan.md`

## 主线（复现门）

按 `ch3_lamda_domain_il_e4.py::main()` 的年度循环，以及
`ch4_lamda_group_robust_pilot.py` 的**逐句镜像方式**（不改原脚本、不 shell 出去调它）：
`strategy=expreplay`、`buffer-scheme=quota`、`reuse-scheme=deficit`、`buffer-repeat=2`、
容量 `200`、`10` 轮、批 `1024`、`lr=0.01`、`momentum=0.9`、`weight_decay=1e-6`、
`seed=42`、阈值 `0.5`。

## ⚠️ 与实施计划的实质冲突（**必须在报告中如实记录**）

实施计划 §2 把 `β=1.0` 标为「现状（必须逐位复现 `0.8170`）」。**该标注与基线的实际
优化器生命周期不符**，两条独立证据：

1. **官方源码**：`.Codex/docs/2026-10-14-LAMDA官方持续学习协议/official-src/
   domain_il_experiment.py` 第 194 行在**年度循环体内**构造
   `optim = torch.optim.SGD(...)`；每个年度都是新的优化器实例，`momentum_buffer`
   在每年年初为 `None`。
2. **E4 复现**：`ch3_lamda_domain_il_e4.py::train_epochs()` 第 388 行同样在**函数体内**
   构造优化器，而 `main()` 每个年度调用该函数一次 ⇒ 每年年初动量缓冲都是空的。

⇒ **基线（官方与 E4 一致）在每个年度边界已经把动量缓冲完全重置**；「上一个年度的梯度方向
被带进当前年度」这一前提在基线中不成立。因此：

- `β=1.0`（保持缓冲、不做衰减）在本脚本中是**引入跨年度携带**，而不是「现状」；
  它**不会**复现 `0.8170`。
- 与 E4 基线**逐位等价**的是 `β=0.0`：把缓冲乘 0 后，SGD 首个 `step()` 走
  `buf = 0·0.9 + d_p = d_p`，与新建优化器的 `buf = clone(d_p)` **逐位相同**
  （本机实测见 `_selfcheck_zero_buffer_equals_fresh_optimizer`）。

**这是先导要给出的实测结论之一**，不是本脚本的缺陷：主线的正确性由
`_selfcheck_train_fn_parity`（本脚本训练函数与 `ch3.train_epochs` 逐位相等）与
`β=0.0` 臂的 `0.8170` 复现共同证明。

## 干预（**冻结**）

进入新年度的第一个 batch 之前，对动量缓冲做 $\\mathbf{m}\\leftarrow\\beta\\cdot\\mathbf{m}$。
**其余一字不动**（缓冲构成、复用倍数、轮数、批大小、学习率、阈值、种子）。

| 臂 | β | 含义（**照实施计划 §2**） |
| --- | --- | --- |
| `beta1` | 1.0 | 计划称「现状」；实测为**完全携带**（不衰减） |
| `beta05` | 0.5 | 部分衰减 |
| `beta0` | 0.0 | 完全重置 ⇒ **实测等价于基线**，复现 `0.8170` |

**只允许动量缓冲被 β 改变**——由 `_selfcheck_scale_only_momentum` 断言并打印：
缩放前后**全部参数逐位不变**，且缓冲逐位等于 `beta × 旧缓冲`。

## 机制层观测量（边界余弦，**真算**）

进入新年度时取**缩放前**的动量缓冲 $\\mathbf{m}$，与该年度**前 5 个 batch**（即该年度
训练流真正会消费的前 5 批，用训练 rng 的状态快照复现）在**同一批**上的损失梯度均值
$\\mathbf{g}_{\\text{new}}$ 计算 $\\cos(\\mathbf{m}, \\mathbf{g}_{\\text{new}})$。

- 取**缩放前**的 $\\mathbf{m}$：这是「被携带进来的历史状态」；缩放后的缓冲在 `β=0`
  时恒为零向量，余弦无定义。两者都打印（`m_norm_before` / `m_norm_after`）。
- 梯度在 `model.eval()` 下计算（无 dropout）⇒ **不消耗 torch 全局随机源**，
  训练轨迹逐位不变。
- 该观测不 `step()`、不写参数，算完 `zero_grad()`。

## 数据根

`DATA_ROOT` **必须**从环境变量 `LAMDA_DATA_ROOT` 解析；未设置或不存在即报错退出，
**不在本脚本写死绝对路径**。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_momentum_state_pilot.py --beta 1.0
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_momentum_state_pilot.py --beta 0.5
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_momentum_state_pilot.py --beta 0.0
"""

from __future__ import annotations

import argparse
import copy
import hashlib
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
RUN_NAME = "ch4-lamda-momentum-state-pilot"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME

BUFFER_SCHEME = "quota"      # 第三章冻结值
REUSE_SCHEME = "deficit"     # 第三章冻结值
BUFFER_REPEAT = 2            # 第三章冻结值（deficit 的 m_max）
MEMORY = 200                 # 第三章冻结容量
POS_RATIO = 0.5              # 第三章冻结值
DEFICIT_GAMMA = 1.0          # 第三章冻结值

# 三臂（实施计划 §2 冻结；`choices` 限定，防止事后挑 β）
BETAS: tuple[float, ...] = (1.0, 0.5, 0.0)
BETA_ARMS: dict[float, str] = {1.0: "beta1", 0.5: "beta05", 0.0: "beta0"}

BOUNDARY_BATCHES = 5         # 实施计划 §3：新年度前 5 个 batch 的梯度均值

BOOTSTRAP_N = 2000           # 配对 bootstrap 重采样次数（计划 §4）
BOOTSTRAP_SEED = 42
GATE_ER_REF = 0.8169830287163194   # 第三章 metrics_expreplay_m200_quota_deficit_r2.json 实测
GATE_ER_TOL = 1e-6

DATA_ROOT_ENV = "LAMDA_DATA_ROOT"

CRITERIA_TEXT = (
    "主判据：2024 年度测试分片 F1，ΔF1 = F1_beta − F1_beta1（β0−β1 与 β05−β1）。"
    "支持：至少一臂 ΔF1(2024) > 0 且配对 bootstrap 95% CI 不含 0，"
    "且 cos 的年度分布显著非正。"
    "部分支持：ΔF1(2024) > 0 但 CI 含 0，或 cos 非正但 F1 未动。"
    "证伪：两臂 ΔF1(2024) ≤ 0，或 cos 显著为正（提升另有原因）。"
    "强证伪：两臂 ΔF1(2024) ≤ 0 且 CI 不含 0。"
    "不确定性：单一冻结种子 42（禁多种子）；测试集配对 bootstrap n=2000，"
    "只量化样本不确定性，不冒充训练随机性。"
)

# 与实施计划 §2「β=1.0 = 现状，必须复现 0.8170」的实质冲突（证据见模块文档）
BASELINE_MOMENTUM_LIFETIME = {
    "claim_in_plan": "β=1.0 为「现状」，应逐位复现 0.8170",
    "observed_conflict": (
        "基线的优化器在**每个年度重新构造**，动量缓冲每年年初即为空；"
        "「上个年度方向被带入当前年度」在基线中不成立。β=1.0 因此是**引入携带**，"
        "不复现 0.8170；与基线逐位等价的是 β=0.0"
    ),
    "evidence": [
        "official-src/domain_il_experiment.py:194 —— optim 构造在年度循环体内",
        "ch3_lamda_domain_il_e4.py:388 —— train_epochs 内构造 optim，main 每年调用一次",
        "本脚本 _selfcheck_zero_buffer_equals_fresh_optimizer —— 零缓冲与新建优化器逐位等价",
    ],
    "planned_stop_condition": "implementation_plan.md §6：β=1.0 复现不出 0.8170 ⇒ 停，报主代理",
}


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
# 动量缓冲工具
# ---------------------------------------------------------------------------
def _buffers_of(opt: torch.optim.Optimizer, model: nn.Module) -> list[torch.Tensor | None]:
    """按 `model.parameters()` 顺序取出各参数的动量缓冲（未初始化者为 None）。"""
    return [opt.state.get(p, {}).get("momentum_buffer") for p in model.parameters()]


def momentum_vec(opt: torch.optim.Optimizer, model: nn.Module) -> torch.Tensor:
    """把全部动量缓冲摊平拼接成一个向量（未初始化者记为零）；CPU float32。"""
    vs = []
    for p, b in zip(model.parameters(), _buffers_of(opt, model)):
        vs.append(torch.zeros(p.numel()) if b is None else b.detach().reshape(-1).cpu())
    return torch.cat(vs) if vs else torch.zeros(0)


def scale_momentum(opt: torch.optim.Optimizer, model: nn.Module, beta: float) -> int:
    """年度边界干预：对每个动量缓冲做原地 `m ← beta·m`。返回被缩放的缓冲个数。"""
    n = 0
    with torch.no_grad():
        for b in _buffers_of(opt, model):
            if b is not None:
                b.mul_(beta)
                n += 1
    return n


def param_digest(model: nn.Module) -> str:
    """全部参数的 sha256（边界干预「参数逐位不变」的证明用）。"""
    h = hashlib.sha256()
    for p in model.parameters():
        h.update(p.detach().float().cpu().numpy().tobytes())
    return h.hexdigest()


def _params_bitwise_equal(a: nn.Module, b: nn.Module) -> bool:
    return all(torch.equal(x.detach(), y.detach())
               for x, y in zip(a.parameters(), b.parameters()))


def _rng_snapshot(rng: np.random.Generator) -> dict:
    return copy.deepcopy(rng.bit_generator.state)


def _rng_restore(snapshot: dict) -> np.random.Generator:
    g = np.random.default_rng(0)
    g.bit_generator.state = snapshot
    return g


# ---------------------------------------------------------------------------
# parts 构造（逐句镜像 E4 的 expreplay + quota + deficit 分支）
# ---------------------------------------------------------------------------
def build_parts(store: dict[int, tuple[np.ndarray, np.ndarray]], years: list[int], idx: int,
                x_curr: np.ndarray, y_curr: np.ndarray,
                buf_rng: np.random.Generator) -> tuple[list[tuple[np.ndarray, np.ndarray]], dict[str, Any]]:
    """与 `ch3.main` 的 `expreplay + buffer_scheme=quota + reuse_scheme=deficit` 分支逐句一致。

    **不附加任何标注、不改任何构造。**
    """
    if idx == 0:
        return [(x_curr, y_curr)], {"blocks": [], "reps": {}}
    blocks = ch3.split_by_year(store, years[:idx], MEMORY, buf_rng, BUFFER_SCHEME, POS_RATIO)
    if not blocks:
        return [(x_curr, y_curr)], {"blocks": [], "reps": {}}
    reps = ch3.reuse_by_deficit(blocks, BUFFER_REPEAT, DEFICIT_GAMMA)
    parts: list[tuple[np.ndarray, np.ndarray]] = [(x_curr, y_curr)]
    for yr, X, y in blocks:
        parts += [(X.astype(np.int8), y.astype(np.float32))] * reps[yr]
    return parts, {"blocks": blocks, "reps": dict(reps)}


# ---------------------------------------------------------------------------
# 训练：与 `ch3.train_epochs` 逐句同型，唯一差别是**优化器由外部持有**
# ---------------------------------------------------------------------------
def train_epochs_persistent(model: nn.Module, parts: list[tuple[np.ndarray, np.ndarray]],
                            epochs: int, batch: int, device: torch.device,
                            rng: np.random.Generator, opt: torch.optim.Optimizer) -> None:
    """`ch3.train_epochs`（penalty/rho_sched/l2 全关）的逐句镜像，优化器为外部对象。

    `ch3.train_epochs` 每次调用都新建 `SGD` ⇒ 动量缓冲每年清空；
    本函数把优化器提到年度循环外，使其跨年度存活——**这是相对 E4 基线唯一的机制性差异**。
    其余（轮数、批大小、取批、shuffle、损失、学习率、momentum、weight_decay）逐位相同，
    由 `_selfcheck_train_fn_parity` 断言。
    """
    criterion = nn.BCELoss()
    model.train()
    for _ in range(epochs):
        for xb, yb in ch3.iterate_batches_parts(parts, batch, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            out = model(xt)
            loss = criterion(out, yt)
            loss.backward()
            opt.step()


# ---------------------------------------------------------------------------
# 机制层观测量：边界余弦
# ---------------------------------------------------------------------------
def boundary_cosine(model: nn.Module, parts: list[tuple[np.ndarray, np.ndarray]], batch: int,
                    device: torch.device, m_vec: torch.Tensor,
                    rng_snapshot: dict) -> dict[str, Any]:
    """cos(m, g_new)：`g_new` = 该年度训练流**前 5 个 batch** 的损失梯度均值。

    用训练 rng 的状态快照复现训练流的前 5 批（当前年度 parts 上的真实批次）；
    在 `model.eval()` 下取梯度（无 dropout ⇒ 不消耗 torch 全局随机源，不改训练轨迹）；
    不 `step()`、不写参数，算完 `zero_grad()`。
    """
    criterion = nn.BCELoss()
    was_training = model.training
    model.eval()
    rng = _rng_restore(rng_snapshot)
    grads: list[torch.Tensor] = []
    for xb, yb in ch3.iterate_batches_parts(parts, batch, rng, True):
        xt = torch.from_numpy(xb.astype(np.float32)).to(device)
        yt = torch.from_numpy(yb).to(device).unsqueeze(1)
        model.zero_grad()
        loss = criterion(model(xt), yt)
        loss.backward()
        grads.append(torch.cat([p.grad.detach().reshape(-1).cpu()
                                for p in model.parameters() if p.grad is not None]))
        if len(grads) >= BOUNDARY_BATCHES:
            break
    model.zero_grad()
    if was_training:
        model.train()
    g_new = torch.stack(grads).mean(dim=0) if grads else torch.zeros_like(m_vec)
    m_norm = float(m_vec.norm())
    g_norm = float(g_new.norm())
    if m_norm == 0.0 or g_norm == 0.0:
        cos: float | None = None
    else:
        cos = float(torch.dot(m_vec, g_new) / (m_norm * g_norm))
    return {
        "n_batches": len(grads),
        "n_grad_dims": int(g_new.numel()),
        "m_norm": m_norm,
        "g_new_norm": g_norm,
        "cos_m_g_new": cos,
    }


# ---------------------------------------------------------------------------
# 运行内自检（**证明只有动量缓冲被改动 / 主线与 E4 逐位一致**）
# ---------------------------------------------------------------------------
def _selfcheck_train_fn_parity(model: nn.Module, parts: list[tuple[np.ndarray, np.ndarray]],
                               batch: int, device: torch.device, seed: int) -> None:
    """断言本脚本训练函数（新建优化器）与 `ch3.train_epochs` **逐位一致**。

    两边各用同一基础模型的深拷贝、同一 numpy 种子、同一 torch 种子跑 1 轮，
    逐张量比较参数。这证明本脚本的训练代码本身没有引入任何差异
    ⇒ 与 E4 基线的唯一差异只剩**优化器生命周期**（本函数不在断言范围内，另行证明）。
    """
    base = copy.deepcopy(model)
    a = copy.deepcopy(base)
    b = copy.deepcopy(base)
    opt_b = torch.optim.SGD(b.parameters(), lr=ch3.OFFICIAL_LR, momentum=ch3.OFFICIAL_MOMENTUM,
                            weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    torch.manual_seed(seed)
    ch3.train_epochs(a, parts, 1, batch, ch3.OFFICIAL_LR, device, np.random.default_rng(seed))
    torch.manual_seed(seed)
    train_epochs_persistent(b, parts, 1, batch, device, np.random.default_rng(seed), opt_b)
    assert _params_bitwise_equal(a, b), "本脚本训练函数与 ch3.train_epochs 不逐位一致"
    print("[selfcheck] 训练函数与 ch3.train_epochs 逐位一致（1 轮，全参数张量相等）", flush=True)


def _selfcheck_zero_buffer_equals_fresh_optimizer(model: nn.Module,
                                                  parts: list[tuple[np.ndarray, np.ndarray]],
                                                  batch: int, device: torch.device,
                                                  seed: int) -> None:
    """断言：动量缓冲被乘 0 后，SGD 的结果与**新建优化器**逐位相同。

    这是「β=0.0 臂 ≡ E4 基线（新优化器每年重建）」的机制性证明
    （SGD 首步：`buf = 0·momentum + d_p = d_p`，与 `buf = clone(d_p)` 逐位相同）。
    """
    a = copy.deepcopy(model)
    b = copy.deepcopy(model)
    opt_a = torch.optim.SGD(a.parameters(), lr=ch3.OFFICIAL_LR, momentum=ch3.OFFICIAL_MOMENTUM,
                            weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    opt_b = torch.optim.SGD(b.parameters(), lr=ch3.OFFICIAL_LR, momentum=ch3.OFFICIAL_MOMENTUM,
                            weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    for p in b.parameters():                      # 预置零缓冲，模拟 β=0 的边界干预
        opt_b.state[p]["momentum_buffer"] = torch.zeros_like(p)
    torch.manual_seed(seed)
    train_epochs_persistent(a, parts, 1, batch, device, np.random.default_rng(seed), opt_a)
    torch.manual_seed(seed)
    train_epochs_persistent(b, parts, 1, batch, device, np.random.default_rng(seed), opt_b)
    assert _params_bitwise_equal(a, b), "零缓冲臂与新建优化器不逐位一致"
    print("[selfcheck] 动量缓冲置零 ≡ 新建优化器（1 轮，全参数张量相等）"
          " ⇒ β=0.0 臂即 E4 基线", flush=True)


def _selfcheck_scale_only_momentum(model: nn.Module, opt: torch.optim.Optimizer,
                                   beta: float, verbose: bool) -> int:
    """执行边界干预并断言**只改动量缓冲**：参数逐位不变，缓冲逐位等于 `beta × 旧缓冲`。

    返回被缩放的缓冲个数。断言在**每个年度边界**都执行；`verbose` 只在首次打印。
    """
    before_digest = param_digest(model)
    before = [None if b is None else b.detach().clone() for b in _buffers_of(opt, model)]
    n_scaled = scale_momentum(opt, model, beta)
    after = _buffers_of(opt, model)
    assert n_scaled == len(before), "被缩放的缓冲个数不等于参数个数"
    assert param_digest(model) == before_digest, "边界干预改动了模型参数（必须只改动量缓冲）"
    n_checked = 0
    for old, new in zip(before, after):
        if old is None:
            continue
        assert new is not None, "缓冲被意外销毁"
        assert torch.equal(new.detach(), old.mul(beta)), "缓冲不逐位等于 beta × 旧缓冲"
        n_checked += 1
    assert n_checked > 0, "没有任何动量缓冲被检查，自检不成立"
    if verbose:
        print(f"[selfcheck] 边界干预只改动量缓冲：参数 sha256={before_digest[:16]}… 逐位不变；"
              f"{n_checked} 个缓冲逐位等于 {beta:g}×旧值", flush=True)
    return n_scaled


# ---------------------------------------------------------------------------
# 指标与配对 bootstrap
# ---------------------------------------------------------------------------
def _f1_of_scores(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> float:
    pred = (np.asarray(y_score) >= threshold).astype(int)
    return float(f1_score(np.asarray(y_true).astype(int), pred, zero_division=0))


def paired_bootstrap(y_true: np.ndarray, score_arm: np.ndarray, score_ref: np.ndarray,
                     n_boot: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    """配对 bootstrap：对同一年度测试分片的逐样本判定重采样，给 ΔF1 的 95% 区间。

    **该区间只量化样本不确定性，不冒充训练随机性。**
    """
    n = int(y_true.size)
    rng = np.random.default_rng(seed)
    pa = (score_arm >= ch3.THRESHOLD).astype(int)
    pr = (score_ref >= ch3.THRESHOLD).astype(int)
    yt = y_true.astype(int)
    obs_a = float(f1_score(yt, pa, zero_division=0))
    obs_r = float(f1_score(yt, pr, zero_division=0))
    diffs = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        diffs[i] = float(f1_score(yt[idx], pa[idx], zero_division=0)) - \
            float(f1_score(yt[idx], pr[idx], zero_division=0))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "observed_delta_f1": obs_a - obs_r,
        "f1_arm": obs_a,
        "f1_ref": obs_r,
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
def run_arm(beta: float) -> int:
    key = BETA_ARMS[beta]
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[arm] {key} beta={beta:g} device={device.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={MEMORY} "
          f"buffer_scheme={BUFFER_SCHEME} reuse_scheme={REUSE_SCHEME} "
          f"buffer_repeat={BUFFER_REPEAT} pos_ratio={POS_RATIO} deficit_gamma={DEFICIT_GAMMA} "
          f"seed={ch3.SEED} threshold={ch3.THRESHOLD} arm={key}", flush=True)

    rng = np.random.default_rng(ch3.SEED)         # 训练洗牌流（三臂同种子）
    buf_rng = np.random.default_rng(ch3.SEED)     # 缓冲构造流（三臂同种子，独立于训练流）

    years = ch3.DOMAIN_YEARS
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in ch3.DOMAIN_YEARS:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    model: nn.Module | None = None
    opt: torch.optim.Optimizer | None = None
    records: list[dict] = []
    boundary_obs: dict[str, dict] = {}
    preds: dict[int, dict] = {}
    selfchecked = False
    first_boundary = True
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(x_curr.shape[1]).to(device)
            # **相对 E4 的唯一机制性差异**：优化器只建一次，跨年度存活
            opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                                  momentum=ch3.OFFICIAL_MOMENTUM,
                                  weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,}", flush=True)

        parts, meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        if not selfchecked:
            # 自检**必须在任何训练之前**执行：它自身消耗 torch 全局随机源（dropout），
            # 结束后 `torch.manual_seed` 重播种，使本臂训练流与 E4 基线（开局播种一次）
            # 逐位相同。放在年中重播种会让后续年度 dropout 掩码错位。
            _selfcheck_train_fn_parity(model, parts, ch3.OFFICIAL_BATCH, device, ch3.SEED)
            _selfcheck_zero_buffer_equals_fresh_optimizer(model, parts, ch3.OFFICIAL_BATCH,
                                                          device, ch3.SEED)
            torch.manual_seed(ch3.SEED)
            selfchecked = True
        sizes = [int(p[0].shape[0]) for p in parts]
        print(f"[parts] {year}: n_parts={len(parts)} sizes={sizes}", flush=True)
        for yr, _, yb in meta["blocks"]:
            nb = int(yb.size)
            pb = int((yb == 1).sum())
            src = store[yr][1]
            ns, psrc = int(src.size), int((src == 1).sum())
            print(f"[audit] 截至{year} 缓冲块 {yr}: {nb}槽 正例{pb} 负例{nb - pb} "
                  f"| 源 {psrc}/{ns} = {psrc / max(ns, 1):.4f}", flush=True)
        if meta["reps"]:
            print(f"[reuse] 截至{year} deficit 复用 = {meta['reps']}", flush=True)

        # ---- 年度边界：先算机制层观测量，再做 beta 干预 ----
        if idx > 0:
            assert opt is not None
            m_vec = momentum_vec(opt, model)
            obs = boundary_cosine(model, parts, ch3.OFFICIAL_BATCH, device, m_vec,
                                  _rng_snapshot(rng))
            obs["beta"] = beta
            # 干预 = 只对动量缓冲做 m ← beta·m；断言参数逐位不变（每个边界都断言）
            n_scaled = _selfcheck_scale_only_momentum(model, opt, beta, verbose=first_boundary)
            first_boundary = False
            obs["n_buffers_scaled"] = n_scaled
            obs["m_norm_after_scale"] = float(momentum_vec(opt, model).norm())
            boundary_obs[str(year)] = obs
            cos_s = "n/a" if obs["cos_m_g_new"] is None else f"{obs['cos_m_g_new']:+.4f}"
            print(f"[boundary] {year}: cos(m,g_new)={cos_s} |m|={obs['m_norm']:.6e} "
                  f"|g_new|={obs['g_new_norm']:.6e} "
                  f"|m_after|={obs['m_norm_after_scale']:.6e} "
                  f"batches={obs['n_batches']} dims={obs['n_grad_dims']} beta={beta:g}",
                  flush=True)

        n_train = int(sum(p[0].shape[0] for p in parts))
        assert opt is not None
        t0 = time.time()
        train_epochs_persistent(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                                device, rng, opt)
        print(f"[{year}] trained on {n_train:,} rows in {time.time() - t0:.1f}s", flush=True)

        for ty in years[: idx + 1]:
            xt, yt = ch3.load_year(ty, "test")
            m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, device)
            records.append({"experience": year, "test_year": ty, "mode": "backward", **m})
        for ty in years[idx + 1:]:
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
                rec = next(r for r in records if r["experience"] == year
                           and r["test_year"] == ty and r["mode"] == "backward")
                f1m = _f1_of_scores(yt, sc, ch3.THRESHOLD)
                assert abs(f1m - float(rec["f1"])) < 1e-12, \
                    f"evaluate 与分数口径不一致 {key} {ty}: {rec['f1']} vs {f1m}"
                print(f"[preds] {key} 末年模型 @{ty}: f1={f1m:.4f} n={int(yt.size)} "
                      f"pos={int((yt == 1).sum())}", flush=True)

    final = max(years)
    last = [r for r in records if r["experience"] == final and r["mode"] == "backward"]
    per_year = {str(int(r["test_year"])): float(r["f1"]) for r in last}
    final_avg = float(np.mean([r["f1"] for r in last]))
    print(f"\n=== {key}（beta={beta:g}）：末年 {final} 的 avg_f1（官方报告口径）= "
          f"{final_avg:.4f} ===", flush=True)

    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{key}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(ch3.THRESHOLD))

    # ---- 结果落盘（多臂合并；每次运行各自追加自己的臂）----
    res_path = RUN_DIR / "e4m_results.json"
    results: dict[str, Any] = json.loads(res_path.read_text()) if res_path.exists() else {}
    results.setdefault("run_name", RUN_NAME)
    results["ts"] = now_utc()
    results["criteria_text"] = CRITERIA_TEXT
    results["baseline_momentum_lifetime"] = BASELINE_MOMENTUM_LIFETIME
    arms = results.setdefault("arms", {})
    arms[key] = {
        "beta": beta,
        "final_year": final,
        "final_avg_f1_backward": final_avg,
        "per_year_f1_final_experience": per_year,
        "wall_seconds": round(time.time() - t_start, 1),
        "boundary_observations": boundary_obs,
        "records": records,
    }
    done_keys = [BETA_ARMS[b] for b in BETAS if BETA_ARMS[b] in arms]
    if all((RUN_DIR / f"preds_{k}_{ty}.npz").exists() for k in done_keys for ty in years):
        results["comparison"] = build_comparison(years, results)
        print(f"[comparison] 已据 {done_keys} 重算 ΔF1 与配对 bootstrap", flush=True)
    write_json(res_path, results)
    print(f"[done] {key} 用时 {time.time() - t_start:.1f}s，制品 {res_path}", flush=True)

    # ---- 复现门（照实施计划 §6）----
    delta = abs(final_avg - GATE_ER_REF)
    ok = delta < GATE_ER_TOL
    print(f"[gate] {key} 复现门：末年 12 年平均 F1 = {final_avg:.10f}，参照 {GATE_ER_REF:.10f}，"
          f"绝对差 {delta:.3e} ⇒ {'PASS' if ok else 'FAIL'}", flush=True)
    if not ok:
        print(f"[gate] {key} 未复现参照值。按实施计划 §6，β=1.0 不通过时**停止并报主代理**，"
              f"不得调数凑。本脚本已知根因：基线每年重建优化器，动量缓冲在年度边界本就为空；"
              f"β=0.0 才是与基线逐位等价的臂（见 [selfcheck] 与 beta0 臂）。", flush=True)
        return 1
    return 0


def build_comparison(years: list[int], results: dict[str, Any]) -> dict[str, Any]:
    """照实施计划 §4：ΔF1 = F1_beta − F1_beta1（β0−β1 与 β05−β1），配对 bootstrap @2024。"""
    ref_key = BETA_ARMS[1.0]
    comp: dict[str, Any] = {
        "reference_arm": ref_key,
        "primary_test_year": 2024,
        "arms_present": sorted(results["arms"]),
        "arms_missing": sorted({BETA_ARMS[b] for b in BETAS} - set(results["arms"])),
        "per_arm": {},
    }
    if ref_key not in results["arms"]:
        return comp
    ref_arm = results["arms"][ref_key]
    for beta in BETAS:
        k = BETA_ARMS[beta]
        if k == ref_key or k not in results["arms"]:
            continue
        arm = results["arms"][k]
        per_year: dict[str, dict] = {}
        boots: dict[str, dict] = {}
        for ty in years:
            pr = np.load(RUN_DIR / f"preds_{ref_key}_{ty}.npz")
            pa = np.load(RUN_DIR / f"preds_{k}_{ty}.npz")
            assert np.array_equal(pr["y_true"], pa["y_true"]), f"两臂 y_true 顺序不一致 @{ty}"
            dr = float(ref_arm["per_year_f1_final_experience"][str(ty)])
            da = float(arm["per_year_f1_final_experience"][str(ty)])
            per_year[str(ty)] = {"f1_beta1": dr, "f1_this_arm": da, "delta": da - dr}
            boots[str(ty)] = paired_bootstrap(pr["y_true"], pa["y_score"], pr["y_score"])
        comp["per_arm"][k] = {
            "beta": beta,
            "per_year": per_year,
            "bootstrap": boots,
            "mean_f1": float(np.mean([v["f1_this_arm"] for v in per_year.values()])),
            "delta_f1_2024": per_year["2024"]["delta"],
            "bootstrap_2024": boots["2024"],
        }
    comp["mean_f1_beta1"] = float(np.mean(
        [float(ref_arm["per_year_f1_final_experience"][str(ty)]) for ty in years]))
    # 补充对照：β=0.0 ≡ E4 基线，直接给出「基线 vs 携带」的读数
    base_key = BETA_ARMS[0.0]
    if base_key in results["arms"]:
        comp["beta0_equals_e4_baseline"] = {
            "final_avg_f1": float(results["arms"][base_key]["final_avg_f1_backward"]),
            "gate_ref": GATE_ER_REF,
            "abs_diff": abs(float(results["arms"][base_key]["final_avg_f1_backward"])
                            - GATE_ER_REF),
        }
    print("[comparison] 主判据 ΔF1(2024)（参照 β=1.0）:", flush=True)
    for beta in BETAS:
        k = BETA_ARMS[beta]
        d = comp["per_arm"].get(k)
        if d is None:
            print(f"  {k}(β={beta:g}): 未运行或为参照臂", flush=True)
            continue
        b = d["bootstrap_2024"]
        print(f"  {k}(β={beta:g}): ΔF1(2024)={d['delta_f1_2024']:+.4f} "
              f"95%=[{b['ci95_low']:+.4f}, {b['ci95_high']:+.4f}] 含0={b['contains_zero']} "
              f"| 12年均F1={d['mean_f1']:.4f} (β=1.0 为 {comp['mean_f1_beta1']:.4f})", flush=True)
    return comp


# ---------------------------------------------------------------------------
def main(beta: float) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    protocol_path = RUN_DIR / "e4m_protocol.json"
    protocol = {
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "hypothesis_H_verbatim": (
            "在年度序列的分布漂移下，SGD 的动量缓冲会把**上一个年度的梯度方向**带进当前年度的训练；"
            "跨年度边界时这些方向来自**分布已经变了的年度**，因而拖累适应。"
        ),
        "observable_definition": (
            "年度边界处，进入新年度时的动量缓冲 m（**缩放前**）与该年度**前 5 个 batch** 的"
            "梯度均值 g_new 的余弦相似度 cos(m, g_new)。"
            "cos ≲ 0 ⇒ 动量携带无关甚至反向的历史方向 ⇒ 假说有机制层支撑；"
            "cos 显著为正 ⇒ 动量仍是有效加速项 ⇒ 假说不成立，即使 F1 有变化也不能归因于它。"
        ),
        "h0_falsification": (
            "年末重置动量不提高 2024 年度 F1；或提高但 cos > 0（即提升另有原因）。"
        ),
        "arms": {BETA_ARMS[b]: b for b in BETAS},
        "arm_semantics_as_written_in_plan": {
            "beta1": "现状（计划称必须逐位复现 0.8170）",
            "beta05": "部分衰减",
            "beta0": "完全重置",
        },
        "criteria_text": CRITERIA_TEXT,
        "mainline": {
            "strategy": "expreplay", "buffer_scheme": BUFFER_SCHEME,
            "reuse_scheme": REUSE_SCHEME, "buffer_repeat": BUFFER_REPEAT,
            "memory": MEMORY, "epochs": ch3.OFFICIAL_EPOCHS, "batch": ch3.OFFICIAL_BATCH,
            "lr": ch3.OFFICIAL_LR, "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY, "pos_ratio": POS_RATIO,
            "deficit_gamma": DEFICIT_GAMMA, "seed": ch3.SEED, "threshold": ch3.THRESHOLD,
            "domain_years": list(ch3.DOMAIN_YEARS),
        },
        "intervention": "进入新年度的第一个 batch 之前，对动量缓冲做 m ← beta·m；其余一字不动",
        "boundary_batches": BOUNDARY_BATCHES,
        "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED,
        "gate_er": {"expected": GATE_ER_REF, "tol": GATE_ER_TOL,
                    "assigned_to_arm_by_plan": BETA_ARMS[1.0],
                    "reference_artifact": "ch3-lamda-domain-il-e4-replication-v1/"
                                          "metrics_expreplay_m200_quota_deficit_r2.json"},
        "baseline_momentum_lifetime": BASELINE_MOMENTUM_LIFETIME,
        "data_root": str(ch3.DATA_ROOT),
        "env_data_root_var": DATA_ROOT_ENV,
    }
    write_json(protocol_path, protocol)
    print(f"[protocol] 已写出 {protocol_path}", flush=True)

    return run_arm(beta)


if __name__ == "__main__":
    ch3.DATA_ROOT = resolve_data_root()   # 覆盖被导入模块的 DATA_ROOT（不写死绝对路径）
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    _log_fh = (RUN_DIR / "full_pilot.log").open("a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_fh)
    sys.stderr = _Tee(sys.__stderr__, _log_fh)
    p = argparse.ArgumentParser(
        description="第四章最小先导：跨年度动量状态的衰减／重置（β 对动量缓冲）")
    p.add_argument("--beta", type=float, required=True, choices=list(BETAS),
                   help="年度边界对动量缓冲的缩放因子（跑前冻结：1.0 / 0.5 / 0.0，"
                        "由 choices 限定，防止事后挑选）。")
    a = p.parse_args()
    try:
        raise SystemExit(main(a.beta))
    finally:
        _log_fh.flush()
