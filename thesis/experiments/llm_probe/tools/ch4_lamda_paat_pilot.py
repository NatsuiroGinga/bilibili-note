#!/usr/bin/env python
"""第四章 PAAT（原型锚定年度训练）先导：四臂主实验 + replay×PAAT 追加两臂。

方案（逐字来源，除下述一处索引笔误修正外）：
- `thesis/methods/第四章-原型锚定年度训练算法（PAAT）方案.md`

主实验四臂（同协议、同种子 42）：
- `base`：第三章 replay 臂的逐句镜像（`build_parts` + `ch3.train_epochs`），复现门
  `末年 12 年平均 F1 = 0.8169830287163194`（容差 `1e-6`）。
- `m1`：原型/对比表示学习。在 `ChenEncoderMLP` 之外新增 `proj = nn.Linear(128, 64)`，
  `z = normalize(proj(encoder(x)))`；维护运行原型 `mu_pos`/`mu_neg`（首批为类均值，
  之后 EMA 0.9/0.1）；`L = BCE + 0.5 * CE([cos_neg, cos_pos] / 0.1, y)`。
- `m2`：正例稀缺的平衡回合。把 `build_parts` 的 parts 物理拼接成池（仅用于采样），
  每轮批次数 = `ceil(total_rows / 1024)`，每批 512 正 + 512 负（专用
  `np.random.default_rng(42)` 流，不足时有放回），普通 BCE。
- `m1m2`：两机制同时开启。

追加两臂（replay × PAAT 的 2×2 另外两格）：
- `orig`：原论文 naive 算法（无回放，`parts=[(x_curr, y_curr)]`，全参数训练），
  复现门 `末年 12 年平均 F1 = 0.7244106926575061`（容差 `1e-3`）。
- `orig_m1m2`：naive + M1+M2（无回放；M2 只从当前年度训练区平衡采样）。

## 唯一偏离方案字面表述之处（必须随结果报告）

方案把原型损失写作 `CE(stack([cos(z, mu_pos), cos(z, mu_neg)], dim=1) / 0.1, y)`。
本数据集标签 `y=1` 表示正例（恶意），而 `stack` 的第 0 列是 `mu_pos`。若逐字实现，
目标索引与类别语义相反，正例会被告知去对齐 `mu_neg`（对抗性损失）。本脚本按方案
**科学意图**（正例对齐 `mu_pos`）实现为 `stack([cos_neg, cos_pos])`，即类别索引
与 `y` 一致；其余（温度 0.1、权重 0.5、EMA 0.9、首批类均值初始化）逐字不变。
该修正不改变任何协议、数据、指标或判据。

## 公共协议（逐字沿用）

`ch3.DOMAIN_YEARS`；10 轮、批 1024、SGD(lr=0.01, momentum=0.9, wd=1e-6)、BCE、
阈值 0.5、seed 42；回放构成 `build_parts`（memory 200 / quota / deficit / repeat 2 /
pos_ratio 0.5 / gamma 1.0）。优化器在训练函数体内构造 ⇒ 每年重建（与基线一致）。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_paat_pilot.py --arm base
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_paat_pilot.py --arm m2
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_paat_pilot.py --arm m1
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_paat_pilot.py --arm m1m2
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_paat_pilot.py --arm orig
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_paat_pilot.py --arm orig_m1m2
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_paat_pilot.py --compare-only
"""

from __future__ import annotations

import argparse
import json
import math
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
import torch.nn.functional as F

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

# ---------------------------------------------------------------------------
# 冻结配置
# ---------------------------------------------------------------------------
RUN_NAME = "ch4-lamda-paat-pilot"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME

ARMS = ("base", "m1", "m2", "m1m2", "orig", "orig_m1m2")
REPLAY_ARMS = ("base", "m1", "m2", "m1m2")
ORIG_ARMS = ("orig", "orig_m1m2")
M1_ARMS = ("m1", "m1m2", "orig_m1m2")
M2_ARMS = ("m2", "m1m2", "orig_m1m2")

SEED = int(ch3.SEED)
THRESHOLD = float(ch3.THRESHOLD)
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# 复现门：值来自方案／任务书，容差照给定
GATES: dict[str, tuple[float, float]] = {
    "base": (0.8169830287163194, 1e-6),
    "orig": (0.7244106926575061, 1e-3),
}

# 方案 §二 / 任务书的机制超参（逐字）
PROTO_LAMBDA = 0.5
PROTO_TAU = 0.1
PROTO_EMA = 0.9
BAL_POS = 512
BAL_NEG = 512

DATA_ROOT_ENV = "LAMDA_DATA_ROOT"

# 公共协议（写进每臂结果 JSON，便于独立复核）
COMMON_PROTOCOL: dict[str, Any] = {
    "domain_years": list(ch3.DOMAIN_YEARS),
    "epochs": int(ch3.OFFICIAL_EPOCHS),
    "batch": int(ch3.OFFICIAL_BATCH),
    "optimizer": "SGD",
    "lr": float(ch3.OFFICIAL_LR),
    "momentum": float(ch3.OFFICIAL_MOMENTUM),
    "weight_decay": float(ch3.OFFICIAL_WEIGHT_DECAY),
    "loss": "BCE",
    "threshold": THRESHOLD,
    "seed": SEED,
    "memory": int(ch3.OFFICIAL_MEMORY),
    "buffer_scheme": "quota",
    "reuse_scheme": "deficit",
    "buffer_repeat": 2,
    "pos_ratio": 0.5,
    "deficit_gamma": 1.0,
    "optimizer_lifetime": "per_year_rebuild_inside_train_fn",
    "train_eval_protocol": "ch4_lamda_inversion_pilot.py::replay",
}


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写出：先写 `.partial`，再 `os.replace`。"""
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def resolve_data_root() -> Path:
    """数据根只从环境变量解析；不写死本机绝对路径。"""
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


def f1_of(yt: np.ndarray, score: np.ndarray) -> float:
    p = (score >= THRESHOLD).astype(int)
    yt = yt.astype(int)
    tp = int(((p == 1) & (yt == 1)).sum())
    fp = int(((p == 1) & (yt == 0)).sum())
    fn = int(((p == 0) & (yt == 1)).sum())
    d = 2 * tp + fp + fn
    return float(2 * tp / d) if d else 0.0


# ---------------------------------------------------------------------------
# 机制一：投影头与运行原型
# ---------------------------------------------------------------------------
class ProjectionHead(nn.Module):
    """`g: R^128 -> R^64`，输出 L2 归一化。"""

    def __init__(self) -> None:
        super().__init__()
        self.proj = nn.Linear(128, 64)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.proj(h), dim=1)


def make_projection_head(device: torch.device) -> ProjectionHead:
    """构造投影头，但**不推进全局 torch RNG**。

    这样 `m1` 与 `base` 在同一批序下的 dropout 掩码逐位一致，唯一差异是原型损失；
    否则投影头的初始化会额外消耗全局随机源，给单机制臂引入第二个变量。
    """
    state = torch.get_rng_state()
    head = ProjectionHead()
    torch.set_rng_state(state)
    return head.to(device)


class PrototypeState:
    """跨批次、跨年度维持的两类运行原型（投影空间，64 维）。"""

    def __init__(self) -> None:
        self.mu_pos: torch.Tensor | None = None
        self.mu_neg: torch.Tensor | None = None
        self.n_updates = 0

    def update(self, z: torch.Tensor, y: torch.Tensor) -> None:
        """首批用类均值初始化；之后 `mu <- 0.9*mu + 0.1*batch_mean`；缺失类不更新。"""
        with torch.no_grad():
            z = z.detach()
            labels = y.reshape(-1)
            for cls, attr in ((1, "mu_pos"), (0, "mu_neg")):
                mask = labels == cls
                if not bool(mask.any()):
                    continue
                batch_mean = z[mask].mean(dim=0)
                cur = getattr(self, attr)
                if cur is None:
                    setattr(self, attr, batch_mean.detach().clone())
                else:
                    cur.mul_(PROTO_EMA).add_(batch_mean, alpha=1.0 - PROTO_EMA)
                self.n_updates += 1

    def ready(self) -> bool:
        return self.mu_pos is not None and self.mu_neg is not None


def proto_loss(z: torch.Tensor, y: torch.Tensor, state: PrototypeState) -> torch.Tensor:
    """`CE([cos(z, mu_neg), cos(z, mu_pos)] / tau, y)`。

    类别索引与标签约定一致（y=1 正例 → 第 1 列 `mu_pos`）。方案原文写作
    `[mu_pos, mu_neg]`，与该约定相反；本脚本按科学意图修正，见模块 docstring。
    """
    assert state.mu_pos is not None and state.mu_neg is not None
    cos_pos = F.cosine_similarity(z, state.mu_pos.unsqueeze(0), dim=1)
    cos_neg = F.cosine_similarity(z, state.mu_neg.unsqueeze(0), dim=1)
    logits = torch.stack([cos_neg, cos_pos], dim=1) / PROTO_TAU
    return F.cross_entropy(logits, y.squeeze(1).long())


# ---------------------------------------------------------------------------
# 机制二：平衡回合采样
# ---------------------------------------------------------------------------
def build_pool(parts: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    """把 parts 物理拼接成采样池（方案明确允许，仅用于采样）。"""
    x = np.concatenate([p[0] for p in parts], axis=0)
    y = np.concatenate([p[1] for p in parts], axis=0).astype(np.float32)
    return x, y


def iter_balanced_batches(
    x_pool: np.ndarray,
    y_pool: np.ndarray,
    rng: np.random.Generator,
) -> Any:
    """每轮生成与 base 相同的批次数；每批 512 正 + 512 负，不足时有放回。"""
    pos_idx = np.flatnonzero(y_pool == 1)
    neg_idx = np.flatnonzero(y_pool == 0)
    if pos_idx.size == 0 or neg_idx.size == 0:
        raise RuntimeError(f"采样池缺少类别：pos={pos_idx.size} neg={neg_idx.size}")
    n_batches = int(math.ceil(y_pool.size / ch3.OFFICIAL_BATCH))
    for _ in range(n_batches):
        p = rng.choice(pos_idx, size=BAL_POS, replace=pos_idx.size < BAL_POS)
        n = rng.choice(neg_idx, size=BAL_NEG, replace=neg_idx.size < BAL_NEG)
        sel = np.concatenate([p, n])
        yield x_pool[sel], y_pool[sel]


# ---------------------------------------------------------------------------
# 训练（m1 / m2 / m1m2）
# ---------------------------------------------------------------------------
def train_epochs_paat(
    model: nn.Module,
    proj: ProjectionHead | None,
    parts: list[tuple[np.ndarray, np.ndarray]],
    epochs: int,
    device: torch.device,
    rng: np.random.Generator,
    bal_rng: np.random.Generator,
    use_proto: bool,
    use_balanced: bool,
    proto_state: PrototypeState,
    year: int,
    arm: str,
) -> dict[str, Any]:
    """与 `ch3.train_epochs` 同型：优化器在函数体内构造 ⇒ 每年度重建。

    `use_balanced=False` 时批序与 base 逐位一致（同一 `rng` 流）；
    `use_balanced=True` 时改用专用 `bal_rng` 流，批次数与 base 相同。
    """
    params = list(model.parameters())
    if use_proto:
        assert proj is not None
        params += list(proj.parameters())
    opt = torch.optim.SGD(params, lr=ch3.OFFICIAL_LR, momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss()
    model.train()

    pool = build_pool(parts) if use_balanced else None
    epoch_logs: list[dict[str, float]] = []
    n_total_batches = 0
    for ep in range(epochs):
        bce_sum = torch.zeros((), device=device)
        proto_sum = torch.zeros((), device=device)
        n_proto_steps = 0
        n_batches = 0
        iterator = (iter_balanced_batches(pool[0], pool[1], bal_rng)
                    if use_balanced else
                    ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True))
        for xb, yb in iterator:
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            h = model.encoder(xt)
            out = model.classifier(h)
            loss_bce = criterion(out, yt)
            loss = loss_bce
            if use_proto:
                assert proj is not None
                z = proj(h)
                proto_state.update(z, yt)
                if proto_state.ready():
                    l_proto = proto_loss(z, yt, proto_state)
                    loss = loss + PROTO_LAMBDA * l_proto
                    proto_sum = proto_sum + l_proto.detach()
                    n_proto_steps += 1
            bce_sum = bce_sum + loss_bce.detach()
            n_batches += 1
            loss.backward()
            opt.step()
        bce_m = float(bce_sum.item() / max(n_batches, 1))
        proto_m = float(proto_sum.item() / max(n_proto_steps, 1)) if n_proto_steps else 0.0
        epoch_logs.append({"epoch": float(ep + 1), "bce": bce_m, "proto": proto_m,
                           "n_batches": float(n_batches)})
        print(f"[{arm}][train] {year} epoch={ep + 1}/{epochs} bce={bce_m:.6f} "
              f"proto={proto_m:.6f} n_batches={n_batches}", flush=True)
        n_total_batches += n_batches
    return {
        "optimizer_type": type(opt).__name__,
        "epoch_mean_bce": [e["bce"] for e in epoch_logs],
        "epoch_mean_proto": [e["proto"] for e in epoch_logs],
        "n_batches": n_total_batches,
        "proto_updates_total": proto_state.n_updates,
    }


# ---------------------------------------------------------------------------
# 单臂主循环
# ---------------------------------------------------------------------------
def run_arm(arm: str) -> int:
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    years = list(ch3.DOMAIN_YEARS)
    print(f"[arm] {arm} device={DEVICE.type} proto={arm in M1_ARMS} "
          f"balanced={arm in M2_ARMS}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"seed={SEED} threshold={THRESHOLD} proto_lambda={PROTO_LAMBDA} "
          f"proto_tau={PROTO_TAU} proto_ema={PROTO_EMA} "
          f"balanced={BAL_POS}+{BAL_NEG}", flush=True)

    store = {y: ch3.load_year(y, "train") for y in years}
    input_dim = int(store[years[0]][0].shape[1])
    rng = np.random.default_rng(SEED)          # 训练洗牌流（m1 / base 用）
    buf_rng = np.random.default_rng(SEED)      # 回放构成流（四臂同序消费）
    bal_rng = np.random.default_rng(SEED)      # M2 专用平衡采样流

    model: nn.Module | None = None
    proj: ProjectionHead | None = None
    proto_state = PrototypeState()
    current_year_f1: dict[str, float] = {}
    preds: dict[int, dict[str, np.ndarray]] = {}
    train_logs: dict[str, dict[str, Any]] = {}
    t0 = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
            if arm in M1_ARMS:
                proj = make_projection_head(DEVICE)
            n_params = sum(p.numel() for p in model.parameters())
            n_proj = sum(p.numel() for p in proj.parameters()) if proj is not None else 0
            print(f"[model] params={n_params:,} proj_params={n_proj:,}", flush=True)

        if arm in ORIG_ARMS:
            # 原论文 naive：只用当前年度，无回放
            parts = [(x_curr, y_curr)]
        else:
            parts, _meta = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        n_rows = int(sum(p[0].shape[0] for p in parts))
        pos_rows = int(sum(int((p[1] == 1).sum()) for p in parts))
        print(f"[parts] {year}: n_parts={len(parts)} rows={n_rows:,} pos={pos_rows:,} "
              f"pos_rate={pos_rows / max(n_rows, 1):.4f}", flush=True)

        t_epoch = time.time()
        if arm in ("base", "orig"):
            # base：与 inversion pilot 的 replay 臂逐句一致；orig：与其 naive 臂逐句一致
            ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                             ch3.OFFICIAL_LR, DEVICE, rng)
            train_logs[str(year)] = {"trainer": "ch3.train_epochs"}
        else:
            train_logs[str(year)] = train_epochs_paat(
                model, proj, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng, bal_rng,
                use_proto=arm in M1_ARMS, use_balanced=arm in M2_ARMS,
                proto_state=proto_state, year=year, arm=arm)
            if arm in M1_ARMS and proto_state.mu_pos is not None and proto_state.mu_neg is not None:
                print(f"[{arm}][proto] {year} |mu_pos|={float(proto_state.mu_pos.norm()):.4f} "
                      f"|mu_neg|={float(proto_state.mu_neg.norm()):.4f} "
                      f"updates={proto_state.n_updates}", flush=True)

        xt, yt = ch3.load_year(year, "test")
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        current_year_f1[str(year)] = float(m["f1"])
        del xt, yt
        print(f"[{year}] current_f1={m['f1']:.4f} ({time.time() - t_epoch:.0f}s)", flush=True)

        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
                del xt, yt

    backward_f1 = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"]) for ty in years}
    mean_f1 = float(np.mean(list(backward_f1.values())))
    for ty, d in preds.items():
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(THRESHOLD))

    payload: dict[str, Any] = {
        "arm": arm,
        "mechanisms": {"m1_prototype": arm in M1_ARMS, "m2_balanced": arm in M2_ARMS},
        "protocol": COMMON_PROTOCOL,
        "mechanism_config": {
            "proto_lambda": PROTO_LAMBDA if arm in M1_ARMS else None,
            "proto_tau": PROTO_TAU if arm in M1_ARMS else None,
            "proto_ema": PROTO_EMA if arm in M1_ARMS else None,
            "proto_label_order": "stack([cos_neg, cos_pos]), target=y（方案字面顺序的索引修正，见脚本头）"
                                 if arm in M1_ARMS else None,
            "balanced_pos": BAL_POS if arm in M2_ARMS else None,
            "balanced_neg": BAL_NEG if arm in M2_ARMS else None,
            "balanced_batches": "ceil(total_rows / 1024)" if arm in M2_ARMS else None,
        },
        "mean_f1": mean_f1,
        "f1_2023": backward_f1["2023"],
        "f1_2024": backward_f1["2024"],
        "backward_f1": backward_f1,
        "current_year_f1": current_year_f1,
        "wall_seconds": round(time.time() - t0, 1),
        "train_logs": train_logs,
        "ts": now_utc(),
    }
    gate_ok = True
    if arm in GATES:
        ref, tol = GATES[arm]
        delta = abs(mean_f1 - ref)
        gate_ok = delta <= tol
        payload["gate"] = {"expected": ref, "observed": mean_f1,
                           "abs_delta": delta, "tol": tol, "passed": gate_ok}
        print(f"[gate] {arm}: {'PASS' if gate_ok else 'FAIL'} "
              f"(obs={mean_f1:.10f} ref={ref:.10f} |Δ|={delta:.3e})", flush=True)
    write_json(RUN_DIR / f"{arm}-result.json", payload)
    print(f"=== {arm}: 12y mean={mean_f1:.10f} | 2023={backward_f1['2023']:.6f} "
          f"2024={backward_f1['2024']:.6f} | {payload['wall_seconds']:.0f}s ===", flush=True)

    maybe_write_comparison()
    return 0 if gate_ok else 1


# ---------------------------------------------------------------------------
# 比较与方案 §四判据
# ---------------------------------------------------------------------------
def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_comparison() -> dict[str, Any] | None:
    results = {arm: _load_json(RUN_DIR / f"{arm}-result.json") for arm in ARMS}
    if results["base"] is None:
        return None
    base = results["base"]
    base_mean = float(base["mean_f1"])
    base_by_year = base["backward_f1"]

    comp: dict[str, Any] = {
        "run_name": RUN_NAME,
        "reference_arm": "base",
        "protocol": COMMON_PROTOCOL,
        "base": {
            "mean_f1": base_mean,
            "f1_2023": float(base["f1_2023"]),
            "f1_2024": float(base["f1_2024"]),
            "gate": base.get("gate"),
        },
        "arms_present": [a for a in ARMS if results[a] is not None],
        "arms_missing": [a for a in ARMS if results[a] is None],
        "per_arm": {},
        "ts": now_utc(),
    }

    for arm in ARMS:
        r = results[arm]
        if r is None or arm == "base":
            continue
        per_year: dict[str, dict[str, float]] = {}
        for ty in ch3.DOMAIN_YEARS:
            key = str(ty)
            f_base = float(base_by_year[key])
            f_arm = float(r["backward_f1"][key])
            per_year[key] = {"f1_base": f_base, "f1_arm": f_arm, "delta": f_arm - f_base}
        comp["per_arm"][arm] = {
            "mean_f1": float(r["mean_f1"]),
            "delta_mean_f1": float(r["mean_f1"]) - base_mean,
            "f1_2023": float(r["f1_2023"]),
            "delta_f1_2023": float(r["f1_2023"]) - float(base["f1_2023"]),
            "f1_2024": float(r["f1_2024"]),
            "delta_f1_2024": float(r["f1_2024"]) - float(base["f1_2024"]),
            "per_year": per_year,
            "wall_seconds": r.get("wall_seconds"),
        }

    # ---- replay × PAAT 2×2：orig / orig_m1m2 / base / m1m2 ----
    cells = ("orig", "orig_m1m2", "base", "m1m2")
    if all(results[a] is not None for a in cells):
        def _v(a: str, key: str) -> float:
            return float(results[a][key])

        eff_without = {k: _v("orig_m1m2", k) - _v("orig", k)
                       for k in ("mean_f1", "f1_2023", "f1_2024")}
        eff_with = {k: _v("m1m2", k) - _v("base", k)
                    for k in ("mean_f1", "f1_2023", "f1_2024")}
        inter = {k: eff_with[k] - eff_without[k] for k in eff_without}
        per_year_inter = {}
        for ty in ch3.DOMAIN_YEARS:
            key = str(ty)
            with_replay = (float(results["m1m2"]["backward_f1"][key])
                           - float(results["base"]["backward_f1"][key]))
            without = (float(results["orig_m1m2"]["backward_f1"][key])
                       - float(results["orig"]["backward_f1"][key]))
            per_year_inter[key] = {"with_replay": with_replay,
                                   "without_replay": without,
                                   "interaction": with_replay - without}
        stack_ok = eff_without["mean_f1"] >= 0.003
        comp["paat_2x2"] = {
            "cells": list(cells),
            "mean_f1": {a: _v(a, "mean_f1") for a in cells},
            "f1_2023": {a: _v(a, "f1_2023") for a in cells},
            "f1_2024": {a: _v(a, "f1_2024") for a in cells},
            "orig_gate": results["orig"].get("gate"),
            "paat_effect_without_replay": {
                "mean_f1": eff_without["mean_f1"],
                "f1_2023": eff_without["f1_2023"],
                "f1_2024": eff_without["f1_2024"],
                "definition": "orig_m1m2 − orig",
            },
            "paat_effect_with_replay": {
                "mean_f1": eff_with["mean_f1"],
                "f1_2023": eff_with["f1_2023"],
                "f1_2024": eff_with["f1_2024"],
                "definition": "m1m2 − base",
            },
            "interaction": {
                "mean_f1": inter["mean_f1"],
                "f1_2023": inter["f1_2023"],
                "f1_2024": inter["f1_2024"],
                "definition": "(m1m2 − base) − (orig_m1m2 − orig)",
                "per_year": per_year_inter,
            },
            "extra_criterion": {
                "text": "若 orig_m1m2 − orig < +0.3 pp，则「叠加到原论文算法」不成立",
                "threshold_mean_f1": 0.003,
                "observed_mean_f1": eff_without["mean_f1"],
                "satisfied": bool(stack_ok),
                "verdict": "成立" if stack_ok else "不成立",
            },
        }
    else:
        comp["paat_2x2"] = {"status": "未完成",
                            "missing": [a for a in cells if results[a] is None]}

    # 方案 §四判据：主判据 3 条（完整算法 = m1m2），否决 3 条。
    criteria: list[dict[str, Any]] = []
    full = comp["per_arm"].get("m1m2")
    singles = {a: comp["per_arm"].get(a) for a in ("m1", "m2")}

    def _c(cid: str, kind: str, text: str, observed: Any, satisfied: bool,
           threshold: Any = None) -> None:
        criteria.append({"id": cid, "kind": kind, "text": text, "threshold": threshold,
                         "observed": observed,
                         "satisfied": bool(satisfied),
                         "verdict": ("满足" if satisfied else "不满足")
                         if kind == "support" else ("触发否决" if satisfied else "未触发")})

    if full is not None:
        _c("C1", "support",
           "完整算法（m1m2）在 2023 与 2024 的 F1 均 ≥ base + 1.0 pp",
           {"delta_f1_2023": full["delta_f1_2023"],
            "delta_f1_2024": full["delta_f1_2024"]},
           full["delta_f1_2023"] >= 0.01 and full["delta_f1_2024"] >= 0.01,
           threshold={"delta_f1_each": 0.01})
        _c("C2", "support",
           "完整算法（m1m2）12 年平均 F1 ≥ base − 0.20 pp",
           {"delta_mean_f1": full["delta_mean_f1"]},
           full["delta_mean_f1"] >= -0.002,
           threshold={"delta_mean_f1_min": -0.002})
        single_mean = {a: (singles[a]["delta_mean_f1"] if singles[a] else None)
                       for a in ("m1", "m2")}
        any_single_pos = any(v is not None and v > 0.0 for v in single_mean.values())
        full_ge_singles = all(
            singles[a] is None or full["delta_mean_f1"] >= singles[a]["delta_mean_f1"]
            for a in ("m1", "m2"))
        _c("C3", "support",
           "两个单机制臂中至少一个相对 base 有正贡献，且完整算法 ≥ 两个单机制臂",
           {"single_delta_mean_f1": single_mean,
            "full_delta_mean_f1": full["delta_mean_f1"],
            "any_single_positive": any_single_pos,
            "full_ge_all_singles": full_ge_singles},
           any_single_pos and full_ge_singles)
        _c("C4", "veto",
           "否决：2023 或 2024 的增益 < 0.3 pp",
           {"delta_f1_2023": full["delta_f1_2023"],
            "delta_f1_2024": full["delta_f1_2024"]},
           full["delta_f1_2023"] < 0.003 or full["delta_f1_2024"] < 0.003,
           threshold={"delta_f1_each_min": 0.003})
        _c("C5", "veto",
           "否决：12 年平均低于 base − 0.5 pp",
           {"delta_mean_f1": full["delta_mean_f1"]},
           full["delta_mean_f1"] < -0.005,
           threshold={"delta_mean_f1_min": -0.005})
    _c("C6", "veto",
       "否决：两个单机制均无正贡献",
       {a: (singles[a]["delta_mean_f1"] if singles[a] is not None else None)
        for a in ("m1", "m2")},
       all(s is not None and s["delta_mean_f1"] <= 0.0 for s in singles.values())
       and all(s is not None for s in singles.values()),
       threshold={"delta_mean_f1_each": 0.0})

    veto_ids = [c["id"] for c in criteria if c["kind"] == "veto" and c["satisfied"]]
    support_ids = [c["id"] for c in criteria if c["kind"] == "support" and c["satisfied"]]
    n_support = sum(1 for c in criteria if c["kind"] == "support")
    if full is None:
        overall = "未判定：m1m2 臂尚未运行"
    elif veto_ids:
        overall = f"方案 §四否决（触发 {', '.join(veto_ids)}）"
    elif len(support_ids) == n_support:
        overall = "方案 §四主判据全部满足（支持）"
    else:
        overall = f"未通过主判据（仅满足 {', '.join(support_ids) or '无'}；未触发否决）"

    comp["criteria"] = criteria
    extra = comp.get("paat_2x2", {}).get("extra_criterion")
    comp["criteria_summary"] = {
        "support_criteria": [c["id"] for c in criteria if c["kind"] == "support"],
        "support_satisfied": support_ids,
        "veto_criteria": [c["id"] for c in criteria if c["kind"] == "veto"],
        "veto_triggered": veto_ids,
        "overall": overall,
        "orig_stack_criterion": extra,
        "note": "判据文字与阈值逐字取自方案 §四；Δ 单位均为 F1（1.0 pp = 0.01 F1）。"
                "C7（追加）只判断 PAAT 能否叠加到原论文 naive 算法。",
    }
    return comp


def maybe_write_comparison() -> dict[str, Any] | None:
    comp = build_comparison()
    if comp is None:
        return None
    write_json(RUN_DIR / "paat-comparison.json", comp)
    present = comp["arms_present"]
    print(f"[comparison] 已写出 paat-comparison.json（present={present}）", flush=True)
    if "m1m2" in comp["per_arm"]:
        print(f"[comparison] {comp['criteria_summary']['overall']}", flush=True)
    return comp


def main(arm: str) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return run_arm(arm)


if __name__ == "__main__":
    ch3.DATA_ROOT = resolve_data_root()   # 只读覆盖被导入模块的数据根，不写死路径
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(description="第四章 PAAT 四臂先导")
    parser.add_argument("--arm", choices=ARMS,
                        help="base / m1 / m2 / m1m2；不给且 --compare-only 时只重算比较")
    parser.add_argument("--compare-only", action="store_true",
                        help="不训练，只根据既有 result JSON 重算 paat-comparison.json")
    args = parser.parse_args()
    if args.compare_only:
        comp = maybe_write_comparison()
        raise SystemExit(0 if comp is not None else 2)
    if not args.arm:
        parser.error("需要 --arm {base,m1,m2,m1m2} 或 --compare-only")
    raise SystemExit(main(args.arm))
