#!/usr/bin/env python
"""第四章材料性验证（2×2）：初始化尺度 × 优化器类型（单一冻结种子 42）。

判据与配置来源（**逐条照抄，不得改动**）：
- `.Codex/docs/2026-10-15-第四章材料性验证/implementation_plan.md`

## 只回答一个问题

**「首年度／次年度被浪费的训练轮次」对最终指标有没有可测影响。**
至少一臂 |Δ| 超过种子噪声上界且方向为改善 ⇒ 靶子材料；四臂全部落在噪声内 ⇒ 不可分辨。

## 主线（复现门）

按 `ch3_lamda_domain_il_e4.py::main()` 的年度循环、以及
`ch4_lamda_group_robust_pilot.py` 的逐句镜像方式（不改原脚本、不 shell 出去调它）：
`strategy=expreplay`、`buffer-scheme=quota`、`reuse-scheme=deficit`、`buffer-repeat=2`、
容量 `200`、`10` 轮、批 `1024`、`lr=0.01`、`momentum=0.9`、`weight_decay=1e-6`、
`seed=42`、阈值 `0.5`。`--arm base` 必须逐位复现 `0.8169830287163194`。

## 四臂（实施计划 §1）

| 臂 | 初始化 | 优化器 |
| --- | --- | --- |
| `base` | PyTorch 默认 | SGD（复现门） |
| `he` | He 尺度 | SGD |
| `adam` | PyTorch 默认 | Adam |
| `he_adam` | He 尺度 | Adam |

**只允许这两处改动**；缓冲构成、复用倍数、轮数、批大小、学习率、阈值、种子、年内正负比例
一律不动，由 `_selfcheck_config_isolation` 机械比对并打印。

## 优化器生命周期（**与基线的实质关系，必须报告**）

基线 `ch3.train_epochs` 在**函数体内**构造 `torch.optim.SGD`（第 388 行），而 `main()` 每个年度
调用它一次 ⇒ **基线每个年度重建优化器**，动量缓冲／Adam 的一二阶矩在每个年度边界都归零。

本脚本的 `adam`／`he_adam` 臂**保持这一生命周期不变**：`train_epochs_with_optimizer` 同样在函数
体内构造优化器，每年度调用一次 ⇒ 同样每年重建。**四臂的优化器生命周期逐位相同**，
故「重建时机」不构成第二个变量；唯一差异是优化器**类型**。
`_selfcheck_train_fn_parity` 断言本脚本的训练镜像函数（SGD）与 `ch3.train_epochs` 逐位一致。

## Adam 超参（实施计划 §1 冻结）

**lr 保持 `0.01` 不变**（只换优化器类型，不调 lr），`weight_decay` 保持基线值 `1e-6`（非解耦
L2，与 SGD 的 `weight_decay` 语义一致）；其余取 `torch.optim.Adam` 默认
（`betas=(0.9, 0.999)`、`eps=1e-8`、`amsgrad=False`）。**若 Adam 臂发散或明显不稳，如实报告
并把「lr 也需调整」记为发现，不得自行调 lr 重跑。**

## He 初始化（实施计划 §1 的「He 尺度」）

对**全部 7 个 `nn.Linear`**（encoder 4 层 + classifier 3 层）的 **weight** 重初始化为
`kaiming_uniform_(a=0, mode="fan_in", nonlinearity="relu")` 的等价形式：`U(−b, b)`，
`b = sqrt(6/fan_in)`，理论 std `sqrt(2/fan_in)`。**bias 保持 PyTorch 默认**。

重初始化用**独立 `torch.Generator`**（不消耗全局 torch 随机源）⇒ He 臂在模型构造结束后的
全局 RNG 状态与 `base` 臂**逐位相同**，故 dropout 掩码、批序、缓冲构造与 base 逐位一致。
该等式由 `_selfcheck_he_init_isolation` 断言并打印。

## 自检（实施计划 §4，四条必须全部实际执行并打印）

1. `base` 臂逐位复现 `0.8169830287163194`（复现门，`_gate`）
2. 参数隔离证明：四臂配置除初始化与优化器外逐字相同（`_selfcheck_config_isolation`）
3. `he` 臂初始化尺度：实测各层 weight std 与 He／默认理论值比对（`_print_init_stats`）
4. `adam` 臂：打印实际优化器类型、betas、eps、weight_decay（训练中每年打印）

## 数据根

`DATA_ROOT` **必须**从环境变量 `LAMDA_DATA_ROOT` 解析；未设置或不存在即报错退出，
**不在本脚本写死绝对路径**。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_training_process_2x2.py --arm base
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_training_process_2x2.py --arm he
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_training_process_2x2.py --arm adam
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_training_process_2x2.py --arm he_adam
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

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
# 冻结配置（照 implementation_plan.md §1、§2，不得改动）
# ---------------------------------------------------------------------------
RUN_NAME = "ch4-lamda-training-process-2x2"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME

BUFFER_SCHEME = "quota"      # 第三章冻结值
REUSE_SCHEME = "deficit"     # 第三章冻结值
BUFFER_REPEAT = 2            # 第三章冻结值（deficit 的 m_max）
MEMORY = 200                 # 第三章冻结容量
POS_RATIO = 0.5              # 第三章冻结值
DEFICIT_GAMMA = 1.0          # 第三章冻结值

# 四臂的两根轴（实施计划 §1 冻结；argparse `choices` 限定，防止事后加臂）
ARMS: tuple[str, ...] = ("base", "he", "adam", "he_adam")
HE_ARMS = ("he", "he_adam")
ADAM_ARMS = ("adam", "he_adam")
ARM_SPEC: dict[str, dict[str, str]] = {
    "base":    {"init": "pytorch_default",   "optimizer": "SGD"},
    "he":      {"init": "he_scale_kaiming_a0_fan_in", "optimizer": "SGD"},
    "adam":    {"init": "pytorch_default",   "optimizer": "Adam"},
    "he_adam": {"init": "he_scale_kaiming_a0_fan_in", "optimizer": "Adam"},
}

BOOTSTRAP_N = 2000           # 配对 bootstrap 重采样次数（实施计划 §2）
BOOTSTRAP_SEED = 42

GATE_BASE_REF = 0.8169830287163194   # metrics_expreplay_m200_quota_deficit_r2.json 实测
GATE_BASE_TOL = 1e-6

# 种子噪声尺度（本课题实测，实施计划 §2 跑前写死，单位为 F1）
NOISE_LOW = 0.0014           # 0.14 点
NOISE_HIGH = 0.0116          # 1.16 点

DATA_ROOT_ENV = "LAMDA_DATA_ROOT"

# 与两根轴无关、四臂**必须逐字相同**的配置（`_selfcheck_config_isolation` 机械比对）
FROZEN_COMMON: dict[str, Any] = {
    "strategy": "expreplay",
    "buffer_scheme": BUFFER_SCHEME,
    "reuse_scheme": REUSE_SCHEME,
    "buffer_repeat": BUFFER_REPEAT,
    "memory": MEMORY,
    "pos_ratio": POS_RATIO,
    "deficit_gamma": DEFICIT_GAMMA,
    "epochs": ch3.OFFICIAL_EPOCHS,
    "batch": ch3.OFFICIAL_BATCH,
    "lr": ch3.OFFICIAL_LR,
    "momentum": ch3.OFFICIAL_MOMENTUM,
    "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
    "seed": ch3.SEED,
    "threshold": ch3.THRESHOLD,
    "domain_years": list(ch3.DOMAIN_YEARS),
    "optimizer_lifetime": "per_year_rebuild_inside_train_fn",
    "rng_streams": "train_rng=default_rng(seed); buf_rng=default_rng(SEED)（各臂同序消费）",
}

CRITERIA_TEXT = (
    "主判据：**末年 2025 对 12 个测试分片的平均 F1**（官方报告口径），"
    "Δ = F1_arm − F1_base。"
    "种子噪声尺度（本课题实测，跑前写死）：跨配置种子波动 0.14–1.16 点（= 0.0014–0.0116 F1）。"
    "材料（靶子成立）：至少一臂 |Δ| 超过噪声上界 0.0116，且方向为改善（Δ > 0）。"
    "不可分辨：全部 |Δ| 落在噪声内。"
    "恶化：至少一臂显著恶化（Δ < −0.0116）⇒ 该干预不成立，但仍说明该因材料。"
    "辅助：2013／2014／2024 三个年度的 F1（缺陷所在年度与目标年度）；"
    "若材料性只体现在 2013／2014 而不传导到整体，如实报告——那说明缺陷是局部的，不构成章级问题。"
    "不确定性：单一冻结种子 42（禁多种子）；测试集配对 bootstrap n=2000，"
    "只量化样本不确定性，不冒充训练随机性。"
)


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
# parts 构造（逐句镜像 E4 的 expreplay + quota + deficit 分支）
# ---------------------------------------------------------------------------
def build_parts(
    store: dict[int, tuple[np.ndarray, np.ndarray]],
    years: list[int],
    idx: int,
    x_curr: np.ndarray,
    y_curr: np.ndarray,
    buf_rng: np.random.Generator,
) -> tuple[list[tuple[np.ndarray, np.ndarray]], dict[str, Any]]:
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
# 优化器工厂（唯一可变的第二根轴）
# ---------------------------------------------------------------------------
def sgd_builder(params: Any) -> torch.optim.Optimizer:
    """基线的优化器构造，逐字取自 `ch3.train_epochs` 第 388–389 行。"""
    return torch.optim.SGD(params, lr=ch3.OFFICIAL_LR, momentum=ch3.OFFICIAL_MOMENTUM,
                           weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)


def adam_builder(params: Any) -> torch.optim.Optimizer:
    """Adam 臂：**只换类型**——lr 与 weight_decay 保持基线值，其余取 torch 默认。

    `decoupled_weight_decay=False`（torch 2.12 默认 ⇒ 未传）使 `weight_decay` 为
    **L2 入梯度**，与基线 SGD 的 `weight_decay` 语义一致，避免把「解耦 L2」混进来。
    """
    return torch.optim.Adam(params, lr=ch3.OFFICIAL_LR,
                            weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)


def optimizer_builder(arm: str) -> Callable[[Any], torch.optim.Optimizer]:
    return adam_builder if arm in ADAM_ARMS else sgd_builder


# ---------------------------------------------------------------------------
# 训练：与 `ch3.train_epochs` 逐句同型，唯一差别是优化器由外部工厂构造
# ---------------------------------------------------------------------------
def train_epochs_with_optimizer(
    model: nn.Module,
    parts: list[tuple[np.ndarray, np.ndarray]],
    epochs: int,
    batch: int,
    device: torch.device,
    rng: np.random.Generator,
    opt_builder: Callable[[Any], torch.optim.Optimizer],
) -> dict[str, Any]:
    """`ch3.train_epochs`（penalty/rho_sched/l2 全关）的逐句镜像。

    优化器在**函数体内**由 `opt_builder` 构造 ⇒ 每年度调用一次 ⇒ **每年重建优化器**，
    与 `ch3.train_epochs` 的优化器生命周期逐位相同（基线行为）。
    其余（轮数、批大小、取批、shuffle、损失、学习率、weight_decay）逐位相同，
    由 `_selfcheck_train_fn_parity` 对 SGD 情况断言。
    """
    opt = opt_builder(model.parameters())
    criterion = nn.BCELoss()
    model.train()
    epoch_losses: list[float] = []
    n_batches = 0
    n_nonfinite_loss = 0
    was_nonfinite = False
    for _ in range(epochs):
        epoch_bce = torch.zeros((), device=device)
        n_epoch_batches = 0
        for xb, yb in ch3.iterate_batches_parts(parts, batch, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            out = model(xt)
            loss_data = criterion(out, yt)
            loss = loss_data
            epoch_bce = epoch_bce + loss_data.detach()
            n_epoch_batches += 1
            if not bool(torch.isfinite(loss_data)):
                n_nonfinite_loss += 1
            loss.backward()
            opt.step()
        if not _params_finite(model):
            was_nonfinite = True
        epoch_losses.append(float(epoch_bce.item() / max(n_epoch_batches, 1)))
        n_batches += n_epoch_batches
    defaults = opt.defaults
    return {
        "optimizer_type": type(opt).__name__,
        "defaults": {k: (list(v) if isinstance(v, tuple) else v) for k, v in defaults.items()},
        "epoch_mean_loss": epoch_losses,
        "n_batches": n_batches,
        "n_nonfinite_loss": n_nonfinite_loss,
        "params_nonfinite": was_nonfinite,
    }


def _params_finite(model: nn.Module) -> bool:
    return all(bool(torch.isfinite(p.detach()).all()) for p in model.parameters())


# ---------------------------------------------------------------------------
# He 初始化
# ---------------------------------------------------------------------------
def he_init_inplace(model: nn.Module, gen: torch.Generator) -> int:
    """把全部 `nn.Linear` 的 **weight** 重初始化为 He 尺度（`kaiming_uniform_(a=0, fan_in)`）。

    等价的显式形式：`U(−b, b)`，`b = sqrt(6/fan_in)`，理论 std `sqrt(2/fan_in)`。
    **bias 保持 PyTorch 默认**（只有 weight 被改）。

    **不消耗全局 torch 随机源**（用独立 `torch.Generator`）⇒ 构造结束后的全局 RNG 状态与
    `base` 臂逐位相同，dropout 掩码与批序不受影响。
    """
    n = 0
    with torch.no_grad():
        for m in model.modules():
            if isinstance(m, nn.Linear):
                fan_in = m.weight.shape[1]
                bound = math.sqrt(6.0 / fan_in)
                m.weight.copy_(
                    torch.empty_like(m.weight).uniform_(-bound, bound, generator=gen))
                n += 1
    return n


def init_stats(model: nn.Module) -> list[dict[str, Any]]:
    """逐层实测 weight std，与 He 理论值 `sqrt(2/fan_in)`、默认理论值 `sqrt(1/(3·fan_in))` 比对。"""
    rows: list[dict[str, Any]] = []
    for name, m in model.named_modules():
        if not isinstance(m, nn.Linear):
            continue
        fan_in = int(m.weight.shape[1])
        w = m.weight.detach().float()
        meas = float(w.std().item())
        he_std = math.sqrt(2.0 / fan_in)
        def_std = math.sqrt(1.0 / (3.0 * fan_in))
        rows.append({
            "name": name,
            "weight_shape": list(m.weight.shape),
            "fan_in": fan_in,
            "measured_weight_std": meas,
            "he_theory_std_sqrt2_over_fanin": he_std,
            "default_theory_std_sqrt1_over_3fanin": def_std,
            "measured_over_he_theory": meas / he_std,
            "measured_over_default_theory": meas / def_std,
        })
    return rows


def build_model(arm: str, input_dim: int, device: torch.device) -> tuple[nn.Module, dict[str, Any]]:
    """构造模型并按臂施加初始化。`base`／`adam` 走 PyTorch 默认，`he`／`he_adam` 走 He 尺度。"""
    rng_before = torch.get_rng_state()
    model = ch3.ChenEncoderMLP(input_dim)
    info: dict[str, Any] = {
        "arm": arm,
        "init_kind": ARM_SPEC[arm]["init"],
        "n_layers_reinitialized": 0,
        "rng_state_before_construct": rng_before,
    }
    if arm in HE_ARMS:
        gen = torch.Generator(device="cpu").manual_seed(ch3.SEED)
        info["n_layers_reinitialized"] = he_init_inplace(model, gen)
        info["he_generator_seed"] = ch3.SEED
    rng_after = torch.get_rng_state()
    info["rng_state_after_build"] = rng_after
    info["global_torch_rng_draws_consumed"] = int(
        (rng_after.to(torch.int64) != rng_before.to(torch.int64)).sum().item() > 0)
    info["layers"] = init_stats(model)
    return model.to(device), info


# ---------------------------------------------------------------------------
# 运行内自检
# ---------------------------------------------------------------------------
def _print_init_stats(arm: str, rows: list[dict[str, Any]]) -> None:
    """自检 3：逐层打印实测 weight std 与理论值（He／默认）。"""
    print(f"[selfcheck-init] arm={arm} 逐层 weight std（实测 vs He 理论 vs 默认理论）:", flush=True)
    for r in rows:
        print(f"  {r['name']:<28} fan_in={r['fan_in']:<5} "
              f"实测={r['measured_weight_std']:.6f} "
              f"He理论={r['he_theory_std_sqrt2_over_fanin']:.6f} "
              f"默认理论={r['default_theory_std_sqrt1_over_3fanin']:.6f} "
              f"实测/He={r['measured_over_he_theory']:.3f} "
              f"实测/默认={r['measured_over_default_theory']:.3f}", flush=True)
    ratios = [r["measured_over_default_theory"] for r in rows]
    print(f"[selfcheck-init] arm={arm} 实测/默认理论 std 比值："
          f"min={min(ratios):.3f} max={max(ratios):.3f}（He 尺度预期 ≈ "
          f"{math.sqrt(2.0 / 1.0) / math.sqrt(1.0 / 3.0):.3f}）×", flush=True)


def _selfcheck_init_matches_arm(arm: str, rows: list[dict[str, Any]]) -> None:
    """断言实测初始化尺度与臂的声明一致（He 臂 ≈ He 理论，base 臂 ≈ 默认理论）。"""
    assert rows, "未取到任何 nn.Linear 层，初始化解剖不成立"
    if arm in HE_ARMS:
        for r in rows:
            assert abs(r["measured_over_he_theory"] - 1.0) < 0.05, \
                f"{r['name']} 实测 std 与 He 理论偏离过大：{r['measured_over_he_theory']}"
    else:
        for r in rows:
            assert abs(r["measured_over_default_theory"] - 1.0) < 0.05, \
                f"{r['name']} 实测 std 与默认理论偏离过大：{r['measured_over_default_theory']}"
    print(f"[selfcheck-init] arm={arm} 实测尺度与声明的初始化一致（全部 {len(rows)} 层，±5%）",
          flush=True)


def _selfcheck_he_init_isolation(input_dim: int) -> None:
    """断言 He 重初始化**只改 weight、不改 bias、不消耗全局 torch 随机源**。

    这是「he 臂与 base 臂唯一差异是 weight 初始化」的机制性证明：
    构造结束后的全局 RNG 状态逐位相同 ⇒ 后续 dropout／批序／缓冲构造与 base 逐位一致。
    """
    torch.manual_seed(ch3.SEED)
    m_base = ch3.ChenEncoderMLP(input_dim)
    st_base = torch.get_rng_state()
    torch.manual_seed(ch3.SEED)
    m_he = ch3.ChenEncoderMLP(input_dim)
    gen = torch.Generator(device="cpu").manual_seed(ch3.SEED)
    n = he_init_inplace(m_he, gen)
    st_he = torch.get_rng_state()
    assert torch.equal(st_base, st_he), \
        "He 重初始化改变了全局 torch RNG 状态（应使用独立 generator）"
    params_base = dict(m_base.named_parameters())
    params_he = dict(m_he.named_parameters())
    assert set(params_base) == set(params_he), "两模型参数名不一致"
    n_weight_changed = 0
    for name, pb in params_base.items():
        ph = params_he[name]
        if name.endswith("weight"):
            assert not torch.equal(pb, ph), f"{name} 在 He 臂未被改动"
            n_weight_changed += 1
        else:
            assert torch.equal(pb, ph), f"{name}（bias）在 He 臂被意外改动"
    assert n_weight_changed == n == 7, \
        f"被重初始化的层数异常：{n_weight_changed} vs {n}（预期 7）"
    print(f"[selfcheck-he-isolation] He 重初始化只改 weight（{n_weight_changed} 层）、"
          f"bias 逐位不变，且**全局 torch RNG 状态逐位不变**", flush=True)


def _selfcheck_config_isolation() -> None:
    """自检 2：四臂配置除 `init`／`optimizer` 外逐字相同（打印比对 + 断言）。"""
    table = {arm: {**FROZEN_COMMON, **ARM_SPEC[arm]} for arm in ARMS}
    keys = sorted({k for cfg in table.values() for k in cfg})
    print("[selfcheck-config] 四臂配置对照（除 init／optimizer 外必须逐字相同）:", flush=True)
    for k in keys:
        vals = {arm: table[arm].get(k) for arm in ARMS}
        same = len({json.dumps(v, ensure_ascii=False, sort_keys=True, default=str)
                    for v in vals.values()}) == 1
        tag = "同" if same else "**异**"
        print(f"  {k:<22} [{tag}] " + " | ".join(f"{arm}={vals[arm]!r}" for arm in ARMS),
              flush=True)
    for arm in ARMS:
        rest = {k: v for k, v in table[arm].items() if k not in ("init", "optimizer")}
        assert rest == FROZEN_COMMON, f"{arm} 的非目标配置与冻结公共配置不一致"
    axes = {k: {arm: table[arm][k] for arm in ARMS} for k in ("init", "optimizer")}
    assert set(axes["init"].values()) == {"pytorch_default", "he_scale_kaiming_a0_fan_in"}
    assert set(axes["optimizer"].values()) == {"SGD", "Adam"}
    n_diff = sum(1 for k in keys
                 if len({json.dumps(table[arm].get(k), ensure_ascii=False, sort_keys=True,
                                    default=str) for arm in ARMS}) > 1)
    assert n_diff == 2, f"变化的配置键数为 {n_diff}，应为 2（只有 init 与 optimizer）"
    print("[selfcheck-config] PASS：仅 init 与 optimizer 两个键在四臂间不同，其余逐字相同",
          flush=True)


def _selfcheck_train_fn_parity(
    base_model: nn.Module,
    parts: list[tuple[np.ndarray, np.ndarray]],
    batch: int,
    device: torch.device,
    seed: int,
) -> None:
    """断言本脚本训练镜像函数（SGD）与 `ch3.train_epochs` **逐位一致**。

    两边各用同一基础模型的深拷贝、同一 numpy/torch 种子跑 1 轮，逐张量比较参数。
    这证明 adam 臂与 base 臂的唯一差异只剩**优化器类型**，训练代码本身没引入差异。
    """
    a = copy.deepcopy(base_model)
    b = copy.deepcopy(base_model)
    torch.manual_seed(seed)
    ch3.train_epochs(a, parts, 1, batch, ch3.OFFICIAL_LR, device, np.random.default_rng(seed))
    torch.manual_seed(seed)
    train_epochs_with_optimizer(b, parts, 1, batch, device, np.random.default_rng(seed),
                                sgd_builder)
    ok = all(torch.equal(x.detach(), y.detach())
             for x, y in zip(a.parameters(), b.parameters()))
    assert ok, "本脚本训练镜像函数（SGD）与 ch3.train_epochs 不逐位一致"
    print("[selfcheck-parity] 训练镜像函数（SGD）与 ch3.train_epochs 逐位一致"
          "（1 轮，全参数张量相等）", flush=True)


def _selfcheck_optimizer(arm: str) -> None:
    """自检 4：打印本臂实际使用的优化器类型与超参（含 Adam 的 betas）。"""
    params = [nn.Parameter(torch.zeros(3))]
    opt = optimizer_builder(arm)(params)
    defaults = {k: (list(v) if isinstance(v, tuple) else v) for k, v in opt.defaults.items()}
    print(f"[selfcheck-optimizer] arm={arm} type={type(opt).__name__} "
          f"lr={defaults.get('lr')} betas={defaults.get('betas')} "
          f"eps={defaults.get('eps')} weight_decay={defaults.get('weight_decay')}", flush=True)
    expect = "Adam" if arm in ADAM_ARMS else "SGD"
    assert type(opt).__name__ == expect, f"{arm} 优化器类型 {type(opt).__name__} != {expect}"
    assert float(defaults["lr"]) == ch3.OFFICIAL_LR, "lr 偏离冻结值 0.01"
    if arm in ADAM_ARMS:
        assert list(defaults["betas"]) == [0.9, 0.999], "Adam betas 非 torch 默认"
    assert float(opt.defaults["weight_decay"]) == ch3.OFFICIAL_WEIGHT_DECAY, \
        "weight_decay 偏离冻结值 1e-6"


# ---------------------------------------------------------------------------
# 指标与配对 bootstrap
# ---------------------------------------------------------------------------
def _f1_of_scores(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> float:
    pred = (np.asarray(y_score) >= threshold).astype(int)
    return float(f1_score(np.asarray(y_true).astype(int), pred, zero_division=0))


def paired_bootstrap(y_true: np.ndarray, score_arm: np.ndarray, score_ref: np.ndarray,
                     n_boot: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    """单年度配对 bootstrap：对同一年度测试分片的逐样本判定重采样，给 ΔF1 的 95% 区间。

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
        "ci95_low": float(lo),
        "ci95_high": float(hi),
        "contains_zero": bool(lo <= 0.0 <= hi),
        "n_boot": int(n_boot),
        "n_test": n,
        "n_pos_test": int((yt == 1).sum()),
        "note": "该区间只量化样本不确定性，不冒充训练随机性",
    }


def bootstrap_mean_over_years(
    years: list[int], ref_key: str, arm_key: str,
    n_boot: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """12 年平均 F1 之 Δ 的配对 bootstrap。

    每轮迭代内：对每个**测试年度分片**分别做逐样本重采样、各算该年 F1 差，再对 12 年取平均
    ⇒ 直接对应主判据（12 年平均 F1）。**该区间只量化样本不确定性，不冒充训练随机性。**
    """
    data: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    for ty in years:
        pr = np.load(RUN_DIR / f"preds_{ref_key}_{ty}.npz")
        pa = np.load(RUN_DIR / f"preds_{arm_key}_{ty}.npz")
        assert np.array_equal(pr["y_true"], pa["y_true"]), f"两臂 y_true 顺序不一致 @{ty}"
        data.append((pr["y_true"].astype(int),
                     (pa["y_score"] >= ch3.THRESHOLD).astype(int),
                     (pr["y_score"] >= ch3.THRESHOLD).astype(int)))
    obs = float(np.mean([float(f1_score(y, a, zero_division=0))
                         - float(f1_score(y, r, zero_division=0)) for y, a, r in data]))
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        vals = []
        for y, a, r in data:
            idx = rng.integers(0, y.size, size=y.size)
            vals.append(float(f1_score(y[idx], a[idx], zero_division=0))
                        - float(f1_score(y[idx], r[idx], zero_division=0)))
        diffs[i] = float(np.mean(vals))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "observed_delta_mean_f1": obs,
        "ci95_low": float(lo),
        "ci95_high": float(hi),
        "contains_zero": bool(lo <= 0.0 <= hi),
        "n_boot": int(n_boot),
        "n_years": len(data),
        "note": "该区间只量化样本不确定性，不冒充训练随机性",
    }


# ---------------------------------------------------------------------------
# 单臂主循环
# ---------------------------------------------------------------------------
def run_arm(arm: str) -> int:
    key = arm
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[arm] {key} init={ARM_SPEC[arm]['init']} optimizer={ARM_SPEC[arm]['optimizer']} "
          f"device={device.type}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={MEMORY} "
          f"buffer_scheme={BUFFER_SCHEME} reuse_scheme={REUSE_SCHEME} "
          f"buffer_repeat={BUFFER_REPEAT} pos_ratio={POS_RATIO} deficit_gamma={DEFICIT_GAMMA} "
          f"seed={ch3.SEED} threshold={ch3.THRESHOLD} arm={key}", flush=True)
    print(f"[lifecycle] 优化器在训练函数体内构造、每年度重建"
          f"（与 ch3.train_epochs 一致）⇒ 四臂的优化器生命周期逐位相同，"
          f"唯一差异是优化器类型", flush=True)

    years = ch3.DOMAIN_YEARS
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in ch3.DOMAIN_YEARS:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    input_dim = int(store[years[0]][0].shape[1])

    # ---- 自检阶段：全部在任何训练之前完成；结束后重播种，使主循环的 RNG 状态与 E4 基线一致 ----
    _selfcheck_config_isolation()
    _selfcheck_he_init_isolation(input_dim)
    _selfcheck_optimizer(arm)
    probe_parts, _ = build_parts(store, years, 1, store[years[1]][0], store[years[1]][1],
                                 np.random.default_rng(ch3.SEED))
    _selfcheck_train_fn_parity(ch3.ChenEncoderMLP(input_dim).to(device), probe_parts,
                               ch3.OFFICIAL_BATCH, device, ch3.SEED)

    # 自检消耗了全局 torch 随机源 ⇒ 重播种，使主循环与 E4 基线（开局播种一次）逐位相同
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)
    rng = np.random.default_rng(ch3.SEED)         # 训练洗牌流（四臂同种子）
    buf_rng = np.random.default_rng(ch3.SEED)     # 缓冲构造流（四臂同种子，独立于训练流）

    model: nn.Module | None = None
    init_info: dict[str, Any] = {}
    records: list[dict] = []
    opt_trace: dict[str, dict] = {}
    preds: dict[int, dict] = {}
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model, init_info = build_model(arm, input_dim, device)
            init_info.pop("rng_state_before_construct", None)
            init_info.pop("rng_state_after_build", None)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,} "
                  f"init={init_info['init_kind']} "
                  f"n_layers_reinit={init_info['n_layers_reinitialized']}", flush=True)
            _print_init_stats(arm, init_info["layers"])
            _selfcheck_init_matches_arm(arm, init_info["layers"])

        parts, meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
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

        n_train = int(sum(p[0].shape[0] for p in parts))
        t0 = time.time()
        if arm in ADAM_ARMS:
            trace = train_epochs_with_optimizer(model, parts, ch3.OFFICIAL_EPOCHS,
                                               ch3.OFFICIAL_BATCH, device, rng,
                                               optimizer_builder(arm))
            opt_trace[str(year)] = trace
            d = trace["defaults"]
            print(f"[opt] {year} type={trace['optimizer_type']} betas={d.get('betas')} "
                  f"eps={d.get('eps')} lr={d.get('lr')} weight_decay={d.get('weight_decay')} "
                  f"| epoch_mean_loss="
                  + ", ".join(f"{v:.4f}" for v in trace["epoch_mean_loss"]), flush=True)
            if trace["n_nonfinite_loss"] or trace["params_nonfinite"] or \
                    not _params_finite(model):
                print(f"[diverge] {year} 检测到非有限值："
                      f"n_nonfinite_loss={trace['n_nonfinite_loss']} "
                      f"params_nonfinite={trace['params_nonfinite']} "
                      f"params_finite_now={_params_finite(model)}", flush=True)
        else:
            ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                             ch3.OFFICIAL_LR, device, rng)
        print(f"[{year}] trained on {n_train:,} rows in {time.time() - t0:.1f}s "
              f"params_finite={_params_finite(model)}", flush=True)

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
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc,
                             "n_nonfinite": int((~np.isfinite(sc)).sum())}
                rec = next(r for r in records if r["experience"] == year
                           and r["test_year"] == ty and r["mode"] == "backward")
                f1m = _f1_of_scores(yt, sc, ch3.THRESHOLD)
                assert abs(f1m - float(rec["f1"])) < 1e-12, \
                    f"evaluate 与分数口径不一致 {key} {ty}: {rec['f1']} vs {f1m}"
                print(f"[preds] {key} 末年模型 @{ty}: f1={f1m:.4f} n={int(yt.size)} "
                      f"pos={int((yt == 1).sum())} nonfinite={preds[ty]['n_nonfinite']}",
                      flush=True)

    final = max(years)
    last = [r for r in records if r["experience"] == final and r["mode"] == "backward"]
    per_year = {str(int(r["test_year"])): float(r["f1"]) for r in last}
    final_avg = float(np.mean([r["f1"] for r in last]))
    print(f"\n=== {key}：末年 {final} 的 avg_f1（官方报告口径）= {final_avg:.4f} ===", flush=True)

    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{key}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(ch3.THRESHOLD))

    # ---- 结果落盘（多臂合并；每次运行各自追加自己的臂）----
    res_path = RUN_DIR / "e4x_results.json"
    results: dict[str, Any] = json.loads(res_path.read_text()) if res_path.exists() else {}
    results.setdefault("run_name", RUN_NAME)
    results["ts"] = now_utc()
    results["criteria_text"] = CRITERIA_TEXT
    arms = results.setdefault("arms", {})
    arms[key] = {
        "init": ARM_SPEC[arm]["init"],
        "optimizer": ARM_SPEC[arm]["optimizer"],
        "final_year": final,
        "final_avg_f1_backward": final_avg,
        "per_year_f1_final_experience": per_year,
        "wall_seconds": round(time.time() - t_start, 1),
        "init_info": init_info,
        "records": records,
    }
    if arm in ADAM_ARMS:
        arms[key]["optimizer_trace"] = opt_trace
    arms[key]["params_finite_final"] = _params_finite(model)

    done = [k for k in ARMS if k in arms]
    if all((RUN_DIR / f"preds_{k}_{ty}.npz").exists() for k in done for ty in years):
        results["comparison"] = build_comparison(years, results)
        results["criteria_mechanical"] = mechanical_criteria(results["comparison"])
        print(f"[comparison] 已据 {done} 重算 ΔF1、配对 bootstrap 与机械判据对照", flush=True)
    write_json(res_path, results)
    print(f"[done] {key} 用时 {time.time() - t_start:.1f}s，制品 {res_path}", flush=True)

    # ---- 复现门（照实施计划 §5、§6）----
    if arm == "base":
        delta = abs(final_avg - GATE_BASE_REF)
        ok = delta < GATE_BASE_TOL
        print(f"[gate] base 复现门：末年 12 年平均 F1 = {final_avg:.10f}，"
              f"参照 {GATE_BASE_REF:.10f}，绝对差 {delta:.3e} ⇒ "
              f"{'PASS' if ok else 'FAIL'}", flush=True)
        if not ok:
            print("[gate] base 未复现参照值。按实施计划 §6 立即停止并报主代理，**不得调数凑**。",
                  flush=True)
            return 1
    return 0


def build_comparison(years: list[int], results: dict[str, Any]) -> dict[str, Any]:
    """以 `base` 为参照：各臂逐年 ΔF1、单年度配对 bootstrap、12 年平均 Δ 的 bootstrap。"""
    ref_key = "base"
    comp: dict[str, Any] = {
        "reference_arm": ref_key,
        "primary_test_year": 2024,
        "aux_test_years": [2013, 2014],
        "noise_low": NOISE_LOW,
        "noise_high": NOISE_HIGH,
        "arms_present": sorted(results["arms"]),
        "arms_missing": sorted(set(ARMS) - set(results["arms"])),
        "per_arm": {},
    }
    if ref_key not in results["arms"]:
        return comp
    ref_arm = results["arms"][ref_key]
    ref_per_year = ref_arm["per_year_f1_final_experience"]
    comp["mean_f1_base"] = float(np.mean([float(ref_per_year[str(ty)]) for ty in years]))
    for arm in ARMS:
        if arm == ref_key or arm not in results["arms"]:
            continue
        a = results["arms"][arm]
        per_year: dict[str, dict] = {}
        boots: dict[str, dict] = {}
        for ty in years:
            pr = np.load(RUN_DIR / f"preds_{ref_key}_{ty}.npz")
            pa = np.load(RUN_DIR / f"preds_{arm}_{ty}.npz")
            assert np.array_equal(pr["y_true"], pa["y_true"]), f"两臂 y_true 顺序不一致 @{ty}"
            dr = float(ref_per_year[str(ty)])
            da = float(a["per_year_f1_final_experience"][str(ty)])
            per_year[str(ty)] = {"f1_base": dr, "f1_arm": da, "delta": da - dr}
            boots[str(ty)] = paired_bootstrap(pr["y_true"], pa["y_score"], pr["y_score"])
        mean_f1 = float(np.mean([v["f1_arm"] for v in per_year.values()]))
        comp["per_arm"][arm] = {
            "init": ARM_SPEC[arm]["init"],
            "optimizer": ARM_SPEC[arm]["optimizer"],
            "per_year": per_year,
            "bootstrap_per_year": boots,
            "mean_f1_arm": mean_f1,
            "delta_mean_f1": mean_f1 - comp["mean_f1_base"],
            "bootstrap_mean_over_years": bootstrap_mean_over_years(years, ref_key, arm),
            "delta_f1_2024": per_year["2024"]["delta"],
            "bootstrap_2024": boots["2024"],
            "delta_f1_2013": per_year["2013"]["delta"],
            "delta_f1_2014": per_year["2014"]["delta"],
        }
    return comp


def mechanical_criteria(comp: dict[str, Any]) -> dict[str, Any]:
    """实施计划 §2 判据的**机械对照**（只做分类，不代替主代理裁决）。"""
    out: dict[str, Any] = {
        "noise_band_f1": [NOISE_LOW, NOISE_HIGH],
        "primary_metric": "12_year_mean_f1 (final experience 2025, backward)",
        "arms": {},
    }
    improved: list[str] = []
    worsened: list[str] = []
    within: list[str] = []
    for arm, d in comp["per_arm"].items():
        delta = float(d["delta_mean_f1"])
        b = d["bootstrap_mean_over_years"]
        if abs(delta) <= NOISE_HIGH:
            cls = "不可分辨（落在噪声内）"
            within.append(arm)
        elif delta > NOISE_HIGH:
            cls = "材料（改善，超过噪声上界）"
            improved.append(arm)
        else:
            cls = "恶化（超过噪声上界，方向为负）"
            worsened.append(arm)
        out["arms"][arm] = {
            "delta_mean_f1": delta,
            "delta_f1_2013": d["delta_f1_2013"],
            "delta_f1_2014": d["delta_f1_2014"],
            "delta_f1_2024": d["delta_f1_2024"],
            "exceeds_noise_high": bool(abs(delta) > NOISE_HIGH),
            "direction": "improve" if delta > 0 else ("worse" if delta < 0 else "zero"),
            "bootstrap_mean_over_years": b,
            "mechanical_class": cls,
        }
    out["n_improved"] = len(improved)
    out["n_worsened"] = len(worsened)
    out["n_within_noise"] = len(within)
    out["improved_arms"] = improved
    out["worsened_arms"] = worsened
    out["within_noise_arms"] = within
    if improved:
        out["mechanical_verdict"] = "材料（靶子成立）：至少一臂 |Δ| 超过噪声上界且方向为改善"
    elif worsened:
        out["mechanical_verdict"] = "恶化：至少一臂显著恶化 ⇒ 该干预不成立（但仍说明该因材料）"
    else:
        out["mechanical_verdict"] = "不可分辨：全部 |Δ| 落在噪声内"
    out["note"] = "本块只做实施计划 §2 判据的机械分类，**不代替主代理裁决**"
    return out


# ---------------------------------------------------------------------------
def main(arm: str) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    protocol_path = RUN_DIR / "e4x_protocol.json"
    protocol = {
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "purpose": "只回答一个问题：「首年度/次年度被浪费的训练轮次」对最终指标有没有可测影响。"
                   "四臂全落在种子噪声内 ⇒ 靶子作废。",
        "arms": {a: ARM_SPEC[a] for a in ARMS},
        "frozen_common": FROZEN_COMMON,
        "criteria_text": CRITERIA_TEXT,
        "criteria_noise_band_f1": [NOISE_LOW, NOISE_HIGH],
        "primary_metric": "末年 2025 对 12 个测试分片的平均 F1（官方报告口径）",
        "aux_metrics": "2013／2014／2024 三个年度的 F1",
        "optimizer_lifetime": {
            "baseline": "ch3.train_epochs 第 388 行在函数体内构造 SGD；main 每年调用一次 ⇒ 每年重建",
            "this_script": "train_epochs_with_optimizer 同样在函数体内构造 ⇒ 每年重建，四臂一致",
            "consequence": "优化器重建时机不是本实验的变量；adam 臂与 base 臂的唯一差异是优化器类型",
            "evidence": "official-src/domain_il_experiment.py:194（官方亦在年度循环体内构造）",
        },
        "adam_hyperparams": {"lr": ch3.OFFICIAL_LR, "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
                             "betas": [0.9, 0.999], "eps": 1e-8,
                             "note": "只换优化器类型，lr 与 weight_decay 保持基线值；"
                                     "lr 不因发散而调整"},
        "he_init": {"scope": "全部 7 个 nn.Linear 的 weight；bias 保持默认",
                    "rule": "U(-sqrt(6/fan_in), sqrt(6/fan_in))（等价 kaiming_uniform_(a=0, fan_in)）",
                    "theory_std": "sqrt(2/fan_in)",
                    "rng": "独立 torch.Generator(seed=42)，不消耗全局 torch 随机源"},
        "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED,
        "gate_base": {"expected": GATE_BASE_REF, "tol": GATE_BASE_TOL,
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
    p = argparse.ArgumentParser(
        description="第四章材料性验证（2×2）：初始化尺度 × 优化器类型")
    p.add_argument("--arm", choices=ARMS, required=True,
                   help="base = 默认初始化 + SGD（复现门）；he = He 尺度 + SGD；"
                        "adam = 默认初始化 + Adam；he_adam = He 尺度 + Adam")
    a = p.parse_args()
    try:
        raise SystemExit(main(a.arm))
    finally:
        _log_fh.flush()
