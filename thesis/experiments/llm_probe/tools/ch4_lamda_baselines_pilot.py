#!/usr/bin/env python
"""第四章外部基线矩阵：deep4 / swa / mcdrop（判据冻结，只登记不作裁决）。

设计源：`thesis/methods/第四章-外部基线矩阵设计.md`（2026-10-21 晚冻结，看到读数前）。
协议骨架：`tools/ch4_lamda_tabm_pilot.py`（同一 `build_parts` / `ch3.iterate_batches_parts` /
`ch3.evaluate` / `ch3.score_shard` 路径，不改既有文件）。

## 三臂（逐字按冻结设计）

- `deep4`：4 个独立 `ch3.ChenEncoderMLP`（成员种子 42/43/44/45）。每个成员
  `torch.manual_seed(seed)` 后构造并训练完整 12 年；训练洗牌流为独立
  `np.random.default_rng(seed)`。**回放构成四成员共享**：`build_parts` 只用一个
  `buf_rng=42` 预计算一次，四成员复用同一 parts。评测＝4 模型 sigmoid 概率平均。
- `swa`：单 `ch3.ChenEncoderMLP`（种子 42），SGD 训练中从第 5 个 epoch 起逐 epoch 维护
  参数运行平均（**手动平均**，未用 `torch.optim.swa_utils.AveragedModel`），覆盖第 5–10 轮；
  年度切换时重置 SWA 状态。每年训练完把平均权重装入独立副本，对该年训练数据做一遍
  train 模式前向（BN 重校准；本骨干无 BatchNorm，该步为协议性 no-op，已登记）后评测；
  在线模型保持末轮权重进入下一年。
- `mcdrop`：单 `ch3.ChenEncoderMLP`（种子 42）正常训练；评测时 `model.train()` 保持
  Dropout，T=10 次前向取概率均值。推理使用固定独立种子（`MCDROP_INFER_SEED`），并在推理
  前后保存/恢复全局 torch/MPS RNG 状态，使训练流不被评测扰动。

## 协议（逐位一致）

SGD(0.01, 0.9, 1e-6) / batch 1024 / 10 epoch/年 / 阈值 0.5 / 优化器年度重建 /
`build_parts`（quota + deficit, memory=200, repeat=2）/ 12 年 backward 面板。
产物：`runs/diagnostics/ch4-lamda-baselines-pilot/preds_{arm}_{year}.npz`、
`{arm}-result.json`、三臂齐全后 `baselines-comparison.json`。

只登记读数，无 pass/fail 门；唯一设门处是章级预算主张
「|uniform tabm4 12y − deep4 12y| ≤ 1.0 pp」，在 `baselines-comparison.json` 中给出布尔。

运行（数据根优先 `LAMDA_DATA_ROOT`，未设置则继承 `ch3.DATA_ROOT`）：
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_baselines_pilot.py --arm deep4
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_baselines_pilot.py --arm swa
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_baselines_pilot.py --arm mcdrop
    /opt/miniconda3/envs/rwkv/bin/python tools/ch4_lamda_baselines_pilot.py --arm all
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

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

TOOLS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS_DIR))
import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
from ch4_lamda_training_process_2x2 import build_parts  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
SEED = ch3.SEED
THRESHOLD = 0.5
RUN_DIR = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-baselines-pilot"
UNIFORM_RESULT = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-tabm-pilot/tabm4-result.json"
BASE_RESULT = TOOLS_DIR.parent / "runs/diagnostics/ch4-lamda-paat-pilot/base-result.json"

ARMS = ("deep4", "swa", "mcdrop")
MEMBER_SEEDS = (42, 43, 44, 45)
SWA_START_EPOCH = 5           # 1-based：第 5–10 轮，共 6 个快照（后 6 个 epoch）
MCDROP_T = 10                 # 任务化设定；冻结设计登记为「标准实践 T=10，无文献数值依据」
MCDROP_INFER_SEED = 20261021  # 固定推理流种子（任务化设定，与训练洗牌流分离）

# 冻结设计中的参照常数（用于对照表溯源；计算仍以产物文件为准）
UNIFORM_MEAN = 0.832346367494066
UNIFORM_F1_2023 = 0.8681241184767278
UNIFORM_F1_2024 = 0.7703703703703704
BASE_MEAN = 0.8169830287163194
BUDGET_TOL = 0.01


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------
def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def resolve_data_root() -> tuple[Path, str]:
    """数据根优先取 `LAMDA_DATA_ROOT`；未设置时继承冻结模块的 `ch3.DATA_ROOT`。"""
    raw = os.environ.get("LAMDA_DATA_ROOT")
    if raw:
        root = Path(raw)
        if not root.is_dir():
            raise SystemExit(f"ERROR: LAMDA_DATA_ROOT 指向的目录不存在：{root}")
        return root, "env:LAMDA_DATA_ROOT"
    return Path(ch3.DATA_ROOT), "ch3.DATA_ROOT(inherited, frozen module)"


def _call_first(names: tuple[str, ...]) -> tuple[int | None, str | None]:
    for name in names:
        fn = getattr(torch.mps, name, None)
        if callable(fn):
            return int(fn()), name
    return None, None


def mps_mem_snapshot(label: str) -> dict[str, Any]:
    """采样 MPS 内存（字节）。torch 2.12 实测接口为 `current_allocated_memory` /
    `driver_allocated_memory`；`*_bytes` 别名不存在，按别名顺序兼容读取并记录实际 API。"""
    if DEVICE.type != "mps":
        return {"label": label, "mps": False}
    torch.mps.synchronize()
    cur, cur_api = _call_first(("current_allocated_bytes", "current_allocated_memory"))
    drv, drv_api = _call_first(("driver_allocated_bytes", "driver_allocated_memory"))
    return {
        "label": label,
        "mps": True,
        "current_allocated_bytes": cur,
        "driver_allocated_bytes": drv,
        "current_api": cur_api,
        "driver_api": drv_api,
    }


def _peak(samples: list[dict[str, Any]], key: str) -> int | None:
    vals = [int(s[key]) for s in samples if s.get(key) is not None]
    return max(vals) if vals else None


def _rng_snapshot() -> tuple[Any, Any]:
    cpu = torch.get_rng_state()
    mps = torch.mps.get_rng_state() if DEVICE.type == "mps" else None
    return cpu, mps


def _rng_restore(snapshot: tuple[Any, Any]) -> None:
    cpu, mps = snapshot
    torch.set_rng_state(cpu)
    if mps is not None:
        torch.mps.set_rng_state(mps)


def metrics_from_scores(y_true: np.ndarray, score: np.ndarray) -> dict[str, Any]:
    """与 `ch3.evaluate` 同口径（阈值 0.5，sklearn 指标）。"""
    y = y_true.astype(int)
    p = (score >= THRESHOLD).astype(int)
    return {
        "accuracy": float(accuracy_score(y, p)),
        "precision": float(precision_score(y, p, zero_division=0)),
        "recall": float(recall_score(y, p, zero_division=0)),
        "f1": float(f1_score(y, p, zero_division=0)),
        "n": int(y.size),
        "n_pos": int((y == 1).sum()),
    }


def f1_of(y: np.ndarray, score: np.ndarray) -> float:
    return float(metrics_from_scores(y, score)["f1"])


def _assert_finite(name: str, arr: np.ndarray) -> None:
    if not np.isfinite(arr).all():
        raise RuntimeError(f"[NaN/Inf] {name} 含非有限值，立即停止（不自行改设计）")


# ---------------------------------------------------------------------------
# 数据与 parts：三臂共用同一构造入口
# ---------------------------------------------------------------------------
def precompute_parts(store: dict[int, tuple[np.ndarray, np.ndarray]],
                     years: list[int]) -> tuple[dict[int, list[tuple[np.ndarray, np.ndarray]]],
                                                 dict[str, Any]]:
    """用**唯一** `buf_rng = default_rng(42)` 预计算 12 年 parts。

    预计算不改变抽取顺序（第 0 年不抽，其后逐年按 `split_by_year` 抽），
    因而回放构成与逐年在训练循环内构造逐位一致；四成员复用同一 parts。
    """
    buf_rng = np.random.default_rng(SEED)
    parts_by_year: dict[int, list[tuple[np.ndarray, np.ndarray]]] = {}
    meta: dict[str, Any] = {}
    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        parts, _ = build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        parts_by_year[year] = parts
        n_rows = int(sum(p[0].shape[0] for p in parts))
        pos_rows = int(sum(int((p[1] == 1).sum()) for p in parts))
        meta[str(year)] = {
            "n_parts": len(parts),
            "rows": n_rows,
            "pos": pos_rows,
            "pos_rate": pos_rows / max(n_rows, 1),
        }
        print(f"[parts] {year}: n_parts={len(parts)} rows={n_rows:,} pos={pos_rows:,} "
              f"pos_rate={pos_rows / max(n_rows, 1):.4f}", flush=True)
    return parts_by_year, meta


def load_store(years: list[int]) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    t = time.time()
    store = {y: ch3.load_year(y, "train") for y in years}
    print(f"[data] train store loaded in {time.time() - t:.1f}s root={ch3.DATA_ROOT}", flush=True)
    return store


# ---------------------------------------------------------------------------
# 训练（镜像 `ch3.train_epochs`；返回逐 epoch BCE）
# ---------------------------------------------------------------------------
def train_epochs_logged(model: nn.Module, parts, epochs: int, device: torch.device,
                        rng: np.random.Generator, label: str, year: int) -> dict[str, Any]:
    """`ch3.train_epochs`（penalty/rho_sched/l2 全关）的逐句镜像。

    优化器在函数体内构造 ⇒ 每年重建（与基线一致）。唯一附加行为是逐 epoch 记录 BCE
    与非有限值检查；损失、取批、shuffle、学习率、batch 逐位相同。
    """
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss()
    model.train()
    bce_hist: list[float] = []
    n_total = 0
    for ep in range(epochs):
        bce_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            out = model(xt)
            loss = criterion(out, yt)
            bce_sum = bce_sum + loss.detach()
            n_batches += 1
            loss.backward()
            opt.step()
        bce_m = float(bce_sum.item() / max(n_batches, 1))
        # 逐 epoch 一次检查（NaN/Inf 会经累加传播到轮均值），避免每批强制 MPS 同步扭曲墙钟。
        if not np.isfinite(bce_m):
            raise RuntimeError(f"[NaN/Inf] {label} {year} epoch={ep + 1} bce={bce_m}，"
                               f"立即停止（不自行改设计）")
        bce_hist.append(bce_m)
        n_total += n_batches
        print(f"[{label}][train] {year} epoch={ep + 1}/{epochs} bce={bce_m:.6f} "
              f"n_batches={n_batches}", flush=True)
    return {"optimizer_type": "SGD", "epoch_mean_bce": bce_hist, "n_batches": n_total}


def train_epochs_swa(model: nn.Module, parts, epochs: int, device: torch.device,
                     rng: np.random.Generator, label: str, year: int
                     ) -> tuple[dict[str, Any], list[torch.Tensor], int]:
    """同 `train_epochs_logged`，并在第 `SWA_START_EPOCH` 轮起维护参数运行平均。

    手动平均（未用 `torch.optim.swa_utils.AveragedModel`）：每个 epoch 末取一次参数快照，
    在线均值 `avg_k = avg_{k-1} + (w_k - avg_{k-1}) / k`，平均张量保存在 CPU，避免占 MPS 显存。
    返回 (训练日志, 平均参数列表, 快照数)。
    """
    opt = torch.optim.SGD(model.parameters(), lr=ch3.OFFICIAL_LR,
                          momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss()
    model.train()
    bce_hist: list[float] = []
    n_total = 0
    avg: list[torch.Tensor] | None = None
    n_snapshots = 0
    for ep in range(epochs):
        bce_sum = torch.zeros((), device=device)
        n_batches = 0
        for xb, yb in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            out = model(xt)
            loss = criterion(out, yt)
            bce_sum = bce_sum + loss.detach()
            n_batches += 1
            loss.backward()
            opt.step()
        bce_m = float(bce_sum.item() / max(n_batches, 1))
        # 逐 epoch 一次检查（NaN/Inf 会经累加传播到轮均值），避免每批强制 MPS 同步扭曲墙钟。
        if not np.isfinite(bce_m):
            raise RuntimeError(f"[NaN/Inf] {label} {year} epoch={ep + 1} bce={bce_m}，"
                               f"立即停止（不自行改设计）")
        bce_hist.append(bce_m)
        n_total += n_batches

        if ep + 1 >= SWA_START_EPOCH:
            n_snapshots += 1
            with torch.no_grad():
                cpu_params = [p.detach().float().cpu() for p in model.parameters()]
                if avg is None:
                    avg = [p.clone() for p in cpu_params]
                else:
                    alpha = 1.0 / float(n_snapshots)
                    for a, p in zip(avg, cpu_params):
                        # 运行均值：a <- a*(1-1/k) + p*(1/k)
                        a.mul_(1.0 - alpha).add_(p, alpha=alpha)
            print(f"[{label}][swa] {year} epoch={ep + 1} snapshot={n_snapshots} "
                  f"(running mean over {n_snapshots} epoch-ends)", flush=True)

        print(f"[{label}][train] {year} epoch={ep + 1}/{epochs} bce={bce_m:.6f} "
              f"n_batches={n_batches}", flush=True)

    if avg is None:
        raise RuntimeError(f"[swa] {year} 未产生任何平均快照（SWA_START_EPOCH={SWA_START_EPOCH}, "
                           f"epochs={epochs}）")
    return {"optimizer_type": "SGD", "epoch_mean_bce": bce_hist, "n_batches": n_total,
            "swa_snapshots": n_snapshots}, avg, n_snapshots


def clone_model(model: nn.Module, input_dim: int) -> nn.Module:
    """构造同结构副本并载入当前参数；构造期间的全局 RNG 状态被保存/恢复。"""
    snap = _rng_snapshot()
    try:
        clone = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
    finally:
        _rng_restore(snap)
    clone.load_state_dict(model.state_dict())
    clone.eval()
    return clone


def apply_swa_average(model: nn.Module, avg: list[torch.Tensor]) -> None:
    with torch.no_grad():
        for p, a in zip(model.parameters(), avg):
            p.copy_(a.to(device=p.device, dtype=p.dtype))


def recalibrate_bn(model: nn.Module, parts) -> dict[str, Any]:
    """用平均权重对该年训练数据做一遍 train 模式前向（BN 重校准）。

    `ch3.ChenEncoderMLP` **不含 BatchNorm**（仅 Linear/ReLU/Dropout），故本步对统计量
    无任何作用，登记为 `no_op_no_batchnorm`；仍按冻结设计执行一遍前向，
    并在前后保存/恢复全局 RNG，避免评测步骤扰动训练流。
    """
    bn_types = (nn.BatchNorm1d, nn.BatchNorm2d, nn.BatchNorm3d, nn.SyncBatchNorm)
    bn_modules = [m for m in model.modules() if isinstance(m, bn_types)]
    snap = _rng_snapshot()
    try:
        model.train()
        with torch.no_grad():
            for xb, _ in ch3.iterate_batches_parts(parts, ch3.OFFICIAL_BATCH,
                                                   np.random.default_rng(0), False):
                model(torch.from_numpy(xb.astype(np.float32)).to(DEVICE))
    finally:
        _rng_restore(snap)
        model.eval()
    return {
        "bn_modules": len(bn_modules),
        "forward": "one train-mode pass over the year's training parts (no grad)",
        "status": "applied" if bn_modules else "no_op_no_batchnorm",
        "rng": "global torch/mps RNG snapshot saved/restored around the pass",
    }


# ---------------------------------------------------------------------------
# 推理
# ---------------------------------------------------------------------------
def mc_score_shard(model: nn.Module, x: np.ndarray, n_passes: int = MCDROP_T) -> np.ndarray:
    """MC Dropout：train 模式保持 Dropout，T 次前向取概率均值。

    推理使用固定独立种子（`MCDROP_INFER_SEED`）并保存/恢复全局 CPU/MPS RNG 状态 ⇒
    推理流可复现且不扰动训练流（下一年的 dropout 抽样与无评测时逐位相同）。
    """
    snap = _rng_snapshot()
    try:
        torch.manual_seed(MCDROP_INFER_SEED)
        if DEVICE.type == "mps":
            torch.mps.manual_seed(MCDROP_INFER_SEED)
        model.train()
        out = []
        dummy = np.zeros(x.shape[0], dtype=np.float32)
        with torch.no_grad():
            for xb, _ in ch3.iterate_batches(x, dummy, ch3.OFFICIAL_BATCH,
                                             np.random.default_rng(0), False):
                xt = torch.from_numpy(xb.astype(np.float32)).to(DEVICE)
                acc = torch.zeros(xt.shape[0], device=DEVICE)
                for _t in range(n_passes):
                    acc = acc + model(xt).squeeze(1)
                out.append((acc / float(n_passes)).cpu().numpy())
    finally:
        model.eval()
        _rng_restore(snap)
    return np.concatenate(out).astype(np.float32) if out else np.zeros(0, dtype=np.float32)


# ---------------------------------------------------------------------------
# 公共协议描述
# ---------------------------------------------------------------------------
def protocol_payload(years: list[int]) -> dict[str, Any]:
    return {
        "domain_years": years,
        "epochs": ch3.OFFICIAL_EPOCHS,
        "batch": ch3.OFFICIAL_BATCH,
        "lr": ch3.OFFICIAL_LR,
        "momentum": ch3.OFFICIAL_MOMENTUM,
        "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
        "memory": ch3.OFFICIAL_MEMORY,
        "optimizer": "SGD",
        "optimizer_lifetime": "per_year_rebuild_inside_train_fn",
        "loss": "BCE",
        "threshold": THRESHOLD,
        "buffer_scheme": "quota",
        "reuse_scheme": "deficit",
        "buffer_repeat": 2,
        "pos_ratio": 0.5,
        "deficit_gamma": 1.0,
        "seed": SEED,
        "data_root": str(ch3.DATA_ROOT),
        "data_root_source": DATA_ROOT_SOURCE,
        "device": DEVICE.type,
    }


DATA_ROOT_SOURCE = "unresolved"


def _base_result_payload(arm: str, years: list[int], parts_meta: dict[str, Any],
                         payload: dict[str, Any], mem_samples: list[dict[str, Any]],
                         predicted: dict[int, dict[str, np.ndarray]],
                         current_year_f1: dict[str, float],
                         current_year_n: dict[str, int],
                         current_year_pos: dict[str, int]) -> dict[str, Any]:
    backward_f1 = {str(ty): f1_of(predicted[ty]["y_true"], predicted[ty]["y_score"])
                   for ty in years}
    mean_f1 = float(np.mean(list(backward_f1.values())))
    before, after = mem_samples[0], mem_samples[-1]
    efficiency = {
        "device": DEVICE.type,
        "n_params": payload["n_params"],
        "wall_seconds": payload["wall_seconds"],
        "mps_memory": {
            "available": DEVICE.type == "mps",
            "sampling": "训练前、每年（或每成员）评价后、打分结束后各采样一次；peak 为采样最大值，非硬件峰值",
            "api_note": ("torch 2.12 的 MPS 内存接口为 current_allocated_memory / "
                         "driver_allocated_memory（字节）；*_bytes 别名不存在"),
            "samples": mem_samples,
            "sampled_peak_current_allocated_bytes": _peak(mem_samples, "current_allocated_bytes"),
            "sampled_peak_driver_allocated_bytes": _peak(mem_samples, "driver_allocated_bytes"),
            "before_training_driver_allocated_bytes": before.get("driver_allocated_bytes"),
            "after_training_driver_allocated_bytes": after.get("driver_allocated_bytes"),
        },
    }
    payload.update({
        "schema_version": "ch4-baselines-arm-v1",
        "arm": arm,
        "protocol": protocol_payload(years),
        "parts_meta": parts_meta,
        "mean_f1": mean_f1,
        "f1_2023": backward_f1["2023"],
        "f1_2024": backward_f1["2024"],
        "backward_f1": backward_f1,
        "current_year_f1": current_year_f1,
        "current_year_n": current_year_n,
        "current_year_pos": current_year_pos,
        "efficiency": efficiency,
        "mps_memory": efficiency["mps_memory"],
        "ts": now_utc(),
    })
    return payload


def save_preds(arm: str, predicted: dict[int, dict[str, np.ndarray]]) -> None:
    for ty, d in predicted.items():
        _assert_finite(f"preds_{arm}_{ty}", d["y_score"])
        np.savez_compressed(RUN_DIR / f"preds_{arm}_{ty}.npz",
                            y_true=d["y_true"], y_score=d["y_score"],
                            threshold=np.float32(THRESHOLD))


def _print_arm_summary(arm: str, payload: dict[str, Any]) -> None:
    print(f"=== {arm}: 12y mean={payload['mean_f1']:.10f} | "
          f"2023={payload['f1_2023']:.6f} 2024={payload['f1_2024']:.6f} | "
          f"params={payload['n_params']:,} | wall={payload['wall_seconds']:.0f}s ===",
          flush=True)


# ---------------------------------------------------------------------------
# 臂 1：deep4
# ---------------------------------------------------------------------------
def run_deep4() -> dict[str, Any]:
    years = list(ch3.DOMAIN_YEARS)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    print(f"[arm] deep4 device={DEVICE.type} members={MEMBER_SEEDS}", flush=True)
    print(f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"threshold={THRESHOLD}", flush=True)

    t_data = time.time()
    store = load_store(years)
    input_dim = int(store[years[0]][0].shape[1])
    parts_by_year, parts_meta = precompute_parts(store, years)
    data_prep_seconds = round(time.time() - t_data, 1)

    mem_samples = [mps_mem_snapshot("before_training")]
    current_sum: dict[int, np.ndarray | None] = {y: None for y in years}
    current_y: dict[int, np.ndarray | None] = {y: None for y in years}
    backward_sum: dict[int, np.ndarray | None] = {y: None for y in years}
    backward_y: dict[int, np.ndarray | None] = {y: None for y in years}
    member_train_wall: dict[str, float] = {}
    member_logs: dict[str, Any] = {}
    n_params_per_member = 0
    t_arm = time.time()

    for mi, seed in enumerate(MEMBER_SEEDS):
        torch.manual_seed(seed)
        model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
        if mi == 0:
            n_params_per_member = sum(p.numel() for p in model.parameters())
        rng = np.random.default_rng(seed)
        member_train_wall[str(seed)] = 0.0
        member_logs[str(seed)] = {}
        print(f"[deep4][member] seed={seed} start", flush=True)

        for idx, year in enumerate(years):
            parts = parts_by_year[year]
            t_epoch = time.time()
            member_logs[str(seed)][str(year)] = train_epochs_logged(
                model, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng, f"deep4-seed{seed}", year)
            member_train_wall[str(seed)] += time.time() - t_epoch

            xt, yt = ch3.load_year(year, "test")
            sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE)
            _assert_finite(f"deep4 member seed={seed} current {year}", sc)
            y_int = yt.astype(np.int8)
            if current_sum[year] is None:
                current_sum[year] = sc.astype(np.float64)
                current_y[year] = y_int
            else:
                current_sum[year] = current_sum[year] + sc.astype(np.float64)
            del xt, yt
            print(f"[deep4][seed{seed}][{year}] member_f1={f1_of(y_int, sc):.4f} "
                  f"({time.time() - t_epoch:.0f}s)", flush=True)

        for ty in years:
            xt, yt = ch3.load_year(ty, "test")
            sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE)
            _assert_finite(f"deep4 member seed={seed} backward {ty}", sc)
            y_int = yt.astype(np.int8)
            if backward_sum[ty] is None:
                backward_sum[ty] = sc.astype(np.float64)
                backward_y[ty] = y_int
            else:
                backward_sum[ty] = backward_sum[ty] + sc.astype(np.float64)
            del xt, yt
        mem_samples.append(mps_mem_snapshot(f"after_member_{seed}"))
        del model
        if DEVICE.type == "mps":
            torch.mps.empty_cache()
        print(f"[deep4][member] seed={seed} done train_wall={member_train_wall[str(seed)]:.0f}s",
              flush=True)

    n_members = float(len(MEMBER_SEEDS))
    predicted: dict[int, dict[str, np.ndarray]] = {}
    current_year_f1: dict[str, float] = {}
    current_year_n: dict[str, int] = {}
    current_year_pos: dict[str, int] = {}
    for ty in years:
        assert current_sum[ty] is not None and current_y[ty] is not None
        score = (current_sum[ty] / n_members).astype(np.float32)
        _assert_finite(f"deep4 ensemble current {ty}", score)
        m = metrics_from_scores(current_y[ty], score)
        current_year_f1[str(ty)] = float(m["f1"])
        current_year_n[str(ty)] = int(m["n"])
        current_year_pos[str(ty)] = int(m["n_pos"])
        print(f"[deep4][ensemble][{ty}] current_f1={m['f1']:.4f}", flush=True)

        assert backward_sum[ty] is not None and backward_y[ty] is not None
        bscore = (backward_sum[ty] / n_members).astype(np.float32)
        _assert_finite(f"deep4 ensemble backward {ty}", bscore)
        predicted[ty] = {"y_true": backward_y[ty], "y_score": bscore}

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    save_preds("deep4", predicted)
    mem_samples.append(mps_mem_snapshot("after_training"))
    wall_seconds = round(time.time() - t_arm, 1)

    payload: dict[str, Any] = {
        "arm": "deep4",
        "definition": {
            "ensemble": "k=4 independent ch3.ChenEncoderMLP",
            "member_seeds": list(MEMBER_SEEDS),
            "member_seeding": ("torch.manual_seed(seed) before each member's construction and "
                               "full 12-year run; np.random.default_rng(seed) training shuffle"),
            "replay_composition": ("shared across members: build_parts precomputed once with "
                                   "one buf_rng=default_rng(42)"),
            "eval": "mean of 4 member sigmoid probabilities",
            "wall_clock": "arm wall (4 trainings + evaluations); per-member train sums recorded",
        },
        "n_params_per_member": n_params_per_member,
        "n_params": n_params_per_member * len(MEMBER_SEEDS),
        "wall_seconds": wall_seconds,
        "data_prep_seconds": data_prep_seconds,
        "member_train_wall_seconds": member_train_wall,
        "sum_member_train_seconds": round(sum(member_train_wall.values()), 1),
        "train_logs": member_logs,
    }
    payload = _base_result_payload("deep4", years, parts_meta, payload, mem_samples,
                                   predicted, current_year_f1, current_year_n, current_year_pos)
    write_json(RUN_DIR / "deep4-result.json", payload)
    _print_arm_summary("deep4", payload)
    print(f"[deep4][efficiency] sum_member_train={payload['sum_member_train_seconds']:.1f}s "
          f"wall={wall_seconds:.1f}s params/member={n_params_per_member:,} "
          f"peak_current={payload['mps_memory']['sampled_peak_current_allocated_bytes']} "
          f"peak_driver={payload['mps_memory']['sampled_peak_driver_allocated_bytes']}",
          flush=True)
    del store, parts_by_year, predicted
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    return payload


# ---------------------------------------------------------------------------
# 臂 2：swa
# ---------------------------------------------------------------------------
def run_swa() -> dict[str, Any]:
    years = list(ch3.DOMAIN_YEARS)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    print(f"[arm] swa device={DEVICE.type} start_epoch={SWA_START_EPOCH} "
          f"epochs={ch3.OFFICIAL_EPOCHS}", flush=True)

    t_data = time.time()
    store = load_store(years)
    input_dim = int(store[years[0]][0].shape[1])
    parts_by_year, parts_meta = precompute_parts(store, years)
    data_prep_seconds = round(time.time() - t_data, 1)

    model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    rng = np.random.default_rng(SEED)
    print(f"[swa][model] params={n_params:,}", flush=True)

    mem_samples = [mps_mem_snapshot("before_training")]
    current_year_f1: dict[str, float] = {}
    current_year_n: dict[str, int] = {}
    current_year_pos: dict[str, int] = {}
    predicted: dict[int, dict[str, np.ndarray]] = {}
    train_logs: dict[str, Any] = {}
    bn_recal_log: dict[str, Any] = {}
    year_wall: dict[str, float] = {}
    live_model_train_wall = 0.0
    t_arm = time.time()
    eval_model: nn.Module | None = None

    for idx, year in enumerate(years):
        parts = parts_by_year[year]
        t_year = time.time()
        t_train = time.time()
        logs, avg, n_snap = train_epochs_swa(model, parts, ch3.OFFICIAL_EPOCHS, DEVICE,
                                             rng, "swa", year)
        train_logs[str(year)] = logs
        live_model_train_wall += time.time() - t_train

        if eval_model is not None:
            del eval_model
        eval_model = clone_model(model, input_dim)
        apply_swa_average(eval_model, avg)
        bn_recal_log[str(year)] = recalibrate_bn(eval_model, parts)

        xt, yt = ch3.load_year(year, "test")
        m = ch3.evaluate(eval_model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        current_year_f1[str(year)] = float(m["f1"])
        current_year_n[str(year)] = int(m["n"])
        current_year_pos[str(year)] = int(m["n_pos"])
        del xt, yt
        year_wall[str(year)] = round(time.time() - t_year, 1)
        mem_samples.append(mps_mem_snapshot(f"after_year_{year}"))
        print(f"[swa][{year}] current_f1={m['f1']:.4f} snapshots={n_snap} "
              f"bn={bn_recal_log[str(year)]['status']} ({year_wall[str(year)]:.0f}s)", flush=True)

    # 末年平均权重模型作为 backward 面板模型
    assert eval_model is not None
    for ty in years:
        xt, yt = ch3.load_year(ty, "test")
        sc = ch3.score_shard(eval_model, xt, ch3.OFFICIAL_BATCH, DEVICE)
        _assert_finite(f"swa backward {ty}", sc)
        predicted[ty] = {"y_true": yt.astype(np.int8), "y_score": sc.astype(np.float32)}
        del xt, yt

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    save_preds("swa", predicted)
    mem_samples.append(mps_mem_snapshot("after_training"))
    wall_seconds = round(time.time() - t_arm, 1)

    payload: dict[str, Any] = {
        "arm": "swa",
        "definition": {
            "method": "manual_parameter_running_mean",
            "not_used": "torch.optim.swa_utils.AveragedModel",
            "start_epoch_1based": SWA_START_EPOCH,
            "epochs": ch3.OFFICIAL_EPOCHS,
            "snapshots_per_year": ch3.OFFICIAL_EPOCHS - SWA_START_EPOCH + 1,
            "snapshot_schedule": "one parameter snapshot at the end of each epoch >= start epoch",
            "state_reset": "per year (SWA state is reinitialized at every year boundary)",
            "live_model_after_eval": "continues with the final-epoch weights; average is eval-only",
            "eval_model": "separate clone with averaged parameters",
            "bn_recalibration": "train-mode forward over the year's training parts; model has no "
                                "BatchNorm, so the pass is a protocol no-op",
        },
        "n_params": n_params,
        "wall_seconds": wall_seconds,
        "data_prep_seconds": data_prep_seconds,
        "live_model_train_seconds": round(live_model_train_wall, 1),
        "year_wall_seconds": year_wall,
        "bn_recalibration": bn_recal_log,
        "train_logs": train_logs,
    }
    payload = _base_result_payload("swa", years, parts_meta, payload, mem_samples,
                                   predicted, current_year_f1, current_year_n, current_year_pos)
    write_json(RUN_DIR / "swa-result.json", payload)
    _print_arm_summary("swa", payload)
    print(f"[swa][efficiency] live_train={live_model_train_wall:.1f}s wall={wall_seconds:.1f}s "
          f"params={n_params:,} "
          f"peak_current={payload['mps_memory']['sampled_peak_current_allocated_bytes']} "
          f"peak_driver={payload['mps_memory']['sampled_peak_driver_allocated_bytes']}", flush=True)
    del store, parts_by_year, model, eval_model, predicted
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    return payload


# ---------------------------------------------------------------------------
# 臂 3：mcdrop
# ---------------------------------------------------------------------------
def run_mcdrop() -> dict[str, Any]:
    years = list(ch3.DOMAIN_YEARS)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    print(f"[arm] mcdrop device={DEVICE.type} T={MCDROP_T} infer_seed={MCDROP_INFER_SEED}",
          flush=True)

    t_data = time.time()
    store = load_store(years)
    input_dim = int(store[years[0]][0].shape[1])
    parts_by_year, parts_meta = precompute_parts(store, years)
    data_prep_seconds = round(time.time() - t_data, 1)

    model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters())
    rng = np.random.default_rng(SEED)
    print(f"[mcdrop][model] params={n_params:,}", flush=True)

    mem_samples = [mps_mem_snapshot("before_training")]
    current_year_f1: dict[str, float] = {}
    current_year_n: dict[str, int] = {}
    current_year_pos: dict[str, int] = {}
    predicted: dict[int, dict[str, np.ndarray]] = {}
    train_logs: dict[str, Any] = {}
    year_wall: dict[str, float] = {}
    train_wall = 0.0
    t_arm = time.time()

    for year in years:
        parts = parts_by_year[year]
        t_year = time.time()
        t_train = time.time()
        train_logs[str(year)] = train_epochs_logged(model, parts, ch3.OFFICIAL_EPOCHS,
                                                    DEVICE, rng, "mcdrop", year)
        train_wall += time.time() - t_train

        xt, yt = ch3.load_year(year, "test")
        sc = mc_score_shard(model, xt, MCDROP_T)
        _assert_finite(f"mcdrop current {year}", sc)
        m = metrics_from_scores(yt.astype(np.int8), sc)
        current_year_f1[str(year)] = float(m["f1"])
        current_year_n[str(year)] = int(m["n"])
        current_year_pos[str(year)] = int(m["n_pos"])
        del xt, yt
        year_wall[str(year)] = round(time.time() - t_year, 1)
        mem_samples.append(mps_mem_snapshot(f"after_year_{year}"))
        print(f"[mcdrop][{year}] current_f1={m['f1']:.4f} T={MCDROP_T} "
              f"({year_wall[str(year)]:.0f}s)", flush=True)

    for ty in years:
        xt, yt = ch3.load_year(ty, "test")
        sc = mc_score_shard(model, xt, MCDROP_T)
        _assert_finite(f"mcdrop backward {ty}", sc)
        predicted[ty] = {"y_true": yt.astype(np.int8), "y_score": sc.astype(np.float32)}
        del xt, yt

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    save_preds("mcdrop", predicted)
    mem_samples.append(mps_mem_snapshot("after_training"))
    wall_seconds = round(time.time() - t_arm, 1)

    payload: dict[str, Any] = {
        "arm": "mcdrop",
        "definition": {
            "method": "MC dropout, mean of T sigmoid probabilities",
            "T": MCDROP_T,
            "T_basis": "task setting: standard practice T=10; no direct literature value registered",
            "inference_mode": "model.train() keeps Dropout active during all T passes",
            "inference_rng": (f"fixed independent seed {MCDROP_INFER_SEED}; global torch/mps RNG "
                              "snapshot saved before and restored after inference"),
            "training": "standard single-model training (same as base protocol)",
        },
        "n_params": n_params,
        "wall_seconds": wall_seconds,
        "data_prep_seconds": data_prep_seconds,
        "train_seconds": round(train_wall, 1),
        "year_wall_seconds": year_wall,
        "train_logs": train_logs,
    }
    payload = _base_result_payload("mcdrop", years, parts_meta, payload, mem_samples,
                                   predicted, current_year_f1, current_year_n, current_year_pos)
    write_json(RUN_DIR / "mcdrop-result.json", payload)
    _print_arm_summary("mcdrop", payload)
    print(f"[mcdrop][efficiency] train={train_wall:.1f}s wall={wall_seconds:.1f}s "
          f"params={n_params:,} "
          f"peak_current={payload['mps_memory']['sampled_peak_current_allocated_bytes']} "
          f"peak_driver={payload['mps_memory']['sampled_peak_driver_allocated_bytes']}", flush=True)
    del store, parts_by_year, model, predicted
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    return payload


# ---------------------------------------------------------------------------
# 三臂对照
# ---------------------------------------------------------------------------
def _entry(result: dict[str, Any], source: str) -> dict[str, Any]:
    return {
        "mean_f1": float(result["mean_f1"]),
        "f1_2023": float(result["f1_2023"]),
        "f1_2024": float(result["f1_2024"]),
        "n_params": int(result["n_params"]),
        "n_params_per_model": result.get("n_params_per_member"),
        "wall_seconds": result.get("wall_seconds"),
        "source": source,
    }


def write_comparison() -> dict[str, Any] | None:
    """三臂结果齐全后写 `baselines-comparison.json`。"""
    missing = [a for a in ARMS if not (RUN_DIR / f"{a}-result.json").is_file()]
    if missing:
        print(f"[comparison] 未写：缺少臂 {missing}", flush=True)
        return None
    if not UNIFORM_RESULT.is_file() or not BASE_RESULT.is_file():
        print("[comparison] 未写：缺少 uniform/base 参照产物", flush=True)
        return None

    results = {a: json.loads((RUN_DIR / f"{a}-result.json").read_text(encoding="utf-8"))
               for a in ARMS}
    uniform = json.loads(UNIFORM_RESULT.read_text(encoding="utf-8"))
    base = json.loads(BASE_RESULT.read_text(encoding="utf-8"))

    table = {
        a: _entry(r, f"{RUN_DIR.name}/{a}-result.json") for a, r in results.items()
    }
    table["uniform_tabm4"] = {
        "mean_f1": float(uniform["mean_f1"]),
        "f1_2023": float(uniform["f1_2023"]),
        "f1_2024": float(uniform["f1_2024"]),
        "n_params": int(uniform["n_params"]),
        "n_params_per_model": None,
        "wall_seconds": uniform.get("wall_seconds"),
        "source": str(UNIFORM_RESULT.relative_to(TOOLS_DIR.parent)),
    }
    table["base"] = {
        "mean_f1": float(base["mean_f1"]),
        "f1_2023": float(base["f1_2023"]),
        "f1_2024": float(base["f1_2024"]),
        "n_params": None,
        "n_params_per_model": None,
        "wall_seconds": base.get("wall_seconds"),
        "source": str(BASE_RESULT.relative_to(TOOLS_DIR.parent)),
    }

    deep4_mean = float(results["deep4"]["mean_f1"])
    diff = abs(float(uniform["mean_f1"]) - deep4_mean)
    budget_claim = {
        "statement": "|uniform tabm4 12y mean F1 - deep4 12y mean F1| <= 1.0 pp",
        "uniform_mean_f1": float(uniform["mean_f1"]),
        "deep4_mean_f1": deep4_mean,
        "abs_diff": diff,
        "tol": BUDGET_TOL,
        "supported": bool(diff <= BUDGET_TOL),
        "note": ("supported=True ⇒ 支持“预算内可行化”主张；False ⇒ 主张降级为“预算内近优”，"
                 "如实登记，不改判据"),
    }

    uniform_wall = float(uniform["wall_seconds"])
    deep4_wall = float(results["deep4"]["wall_seconds"])
    deep4_train_sum = results["deep4"].get("sum_member_train_seconds")
    efficiency = {
        "deep4_wall_seconds": deep4_wall,
        "deep4_sum_member_train_seconds": deep4_train_sum,
        "uniform_tabm4_wall_seconds": uniform_wall,
        "deep4_over_uniform_wall_ratio": deep4_wall / uniform_wall,
        "deep4_sum_member_train_over_uniform_wall_ratio": (
            None if deep4_train_sum is None else float(deep4_train_sum) / uniform_wall),
        "deep4_n_params_total": int(results["deep4"]["n_params"]),
        "deep4_n_params_per_member": int(results["deep4"]["n_params_per_member"]),
        "uniform_n_params": int(uniform["n_params"]),
        "note": ("墙钟为各臂协议墙钟（不含数据加载）。deep4_wall_seconds 含 4 次训练、"
                 "逐成员年度评测与最终 backward 打分；deep4_sum_member_train_seconds 为纯训练和。"
                 "uniform 为单次训练运行。冻结设计的效率对照点按实测如实登记，不预设 ≈4×。"),
    }

    deltas: dict[str, Any] = {}
    for name, entry in table.items():
        deltas[name] = {
            "vs_uniform_pp": (entry["mean_f1"] - table["uniform_tabm4"]["mean_f1"]) * 100,
            "vs_base_pp": (entry["mean_f1"] - table["base"]["mean_f1"]) * 100,
        }

    payload = {
        "schema_version": "ch4-lamda-baselines-comparison-v1",
        "design": "thesis/methods/第四章-外部基线矩阵设计.md",
        "arms_order": list(ARMS),
        "reference_constants": {
            "uniform_tabm4_mean_f1": UNIFORM_MEAN,
            "uniform_tabm4_f1_2023": UNIFORM_F1_2023,
            "uniform_tabm4_f1_2024": UNIFORM_F1_2024,
            "base_mean_f1": BASE_MEAN,
        },
        "table": table,
        "budget_claim": budget_claim,
        "efficiency": efficiency,
        "descriptive_deltas_12y_pp": deltas,
        "ts": now_utc(),
    }
    write_json(RUN_DIR / "baselines-comparison.json", payload)
    print(f"[comparison] budget_claim.supported={budget_claim['supported']} "
          f"abs_diff={diff:.6f} efficiency_ratio={efficiency['deep4_over_uniform_wall_ratio']:.3f}",
          flush=True)
    return payload


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def main() -> int:
    global DATA_ROOT_SOURCE
    parser = argparse.ArgumentParser(description="第四章外部基线矩阵：deep4 / swa / mcdrop")
    parser.add_argument("--arm", choices=(*ARMS, "all"), required=True)
    args = parser.parse_args()

    data_root, source = resolve_data_root()
    ch3.DATA_ROOT = data_root
    DATA_ROOT_SOURCE = source
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[run] arm={args.arm} device={DEVICE.type} data_root={data_root} "
          f"source={source} run_dir={RUN_DIR}", flush=True)
    runners = {"deep4": run_deep4, "swa": run_swa, "mcdrop": run_mcdrop}
    arms = list(ARMS) if args.arm == "all" else [args.arm]
    for arm in arms:
        print(f"\n########## {arm} ##########", flush=True)
        runners[arm]()
        write_comparison()

    print(f"[done] arms={arms}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
