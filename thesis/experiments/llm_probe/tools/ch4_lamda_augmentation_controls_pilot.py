#!/usr/bin/env python
"""第四章增广对照先导：`swap20` 与 `flip20`（描述性对照，不设判据）。

## 只回答一个问题

`adapt`（自适应活跃特征掩码）相对 `base` 的 12 年平均 F1 增益（+0.6436 pp），
是否只是「任意输入扰动」或「样本间支撑混合」就能解释？本脚本运行两个对照臂：

- `swap20`：样本间交换 20% 的特征位置（全体下标，不只活跃位）——检验「支撑混合」；
- `flip20`：随机翻转 20% 的全体 `(样本, 特征)` 元素——检验「任意输入扰动」。

**本脚本是描述性对照，不设支持／证伪判据。** 全部读数为单训练种子 42。

## 公共协议（逐字沿用 `ch4_lamda_feature_dropout_pilot.py` 的 `base`）

年份、`epochs=10`、`batch=1024`、`lr=0.01`、`momentum=0.9`、`weight_decay=1e-6`、
`seed=42`、`threshold=0.5`、`memory=200`、`buffer_scheme="quota"`、
`reuse_scheme="deficit"`、`buffer_repeat=2`、`pos_ratio=0.5`、`deficit_gamma=1.0`。
模型与数据加载 import `ch3_lamda_domain_il_e4`；缓冲构造复用
`ch4_lamda_training_process_2x2.build_parts`。本脚本只新增文件，不改动任何既有文件。

## 扰动定义

两臂都使用独立随机源 `mask_rng = np.random.default_rng(SEED + 1)`，**不消耗**训练洗牌
`rng` 与缓冲构造 `buf_rng`；只在训练批次上施加，`ch3.evaluate` 与 `ch3.score_shard`
绝不施加。

`swap20`（逐批）：

    perm = mask_rng.permutation(B)                    # 与批次同序的随机配对
    for each sample i: 随机选 20% 的特征下标（全体 D 个下标，不放回）
    xb[i, idx] = xb[perm[i], idx]                     # 不重新二值化，dtype/形状不变

`flip20`（逐批）：

    随机选 20% 的 (样本, 特征) 元素（全体 B*D 个，不放回）
    xb[flat_idx] = 1 - xb[flat_idx]                   # 0/1 二值输入，dtype/形状不变

实测扰动率＝实际改变值的元素数 / 该批全部元素数。`swap20` 另报「被选位置上实际
改变的比例」，因为配对样本的取值可能相同。

## 产物（新运行目录）

- `{arm}-result.json`：公共协议、`wall_seconds`、逐年 F1、12 年平均、逐轮 loss、
  实测扰动率。
- `preds_{arm}_{year}.npz`：`y_true/y_score/threshold`。
- `controls-comparison.json`：以既有 `ch4-lamda-feature-dropout-pilot` 的
  `preds_base_*.npz`／`preds_drop20_*.npz` 与 `ch4-lamda-adaptive-mask-pilot` 的
  `preds_adapt_*.npz` 为参照，给出逐年 ΔF1 与 12 年平均 Δ。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_augmentation_controls_pilot.py --arm swap20
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_augmentation_controls_pilot.py --arm flip20

第二臂完成后自动写出 `controls-comparison.json`。
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

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
import ch4_lamda_feature_dropout_pilot as fixed  # noqa: E402  （复用公共协议与工具）
import ch4_lamda_training_process_2x2 as ch4  # noqa: E402  （复用 build_parts）

# ---------------------------------------------------------------------------
# 冻结配置
# ---------------------------------------------------------------------------
RUN_NAME = "ch4-lamda-augmentation-controls-pilot"
DIAG_ROOT = Path(__file__).resolve().parents[1] / "runs" / "diagnostics"
RUN_DIR = DIAG_ROOT / RUN_NAME
FEATURE_DROPOUT_DIR = DIAG_ROOT / "ch4-lamda-feature-dropout-pilot"
ADAPTIVE_MASK_DIR = DIAG_ROOT / "ch4-lamda-adaptive-mask-pilot"

ARMS: tuple[str, ...] = ("swap20", "flip20")
PERTURB_FRACTION = 0.20

# 参照臂：base/drop20 来自固定率先导，adapt 来自自适应先导
REFERENCE_ARMS: tuple[str, ...] = ("base", "drop20", "adapt")
REFERENCE_DIRS: dict[str, Path] = {
    "base": FEATURE_DROPOUT_DIR,
    "drop20": FEATURE_DROPOUT_DIR,
    "adapt": ADAPTIVE_MASK_DIR,
}

# base 复现门（参照结果的完整性核验；本脚本不重训 base）
GATE_BASE_REF = 0.8169830287163194
GATE_BASE_TOL = 1e-6

DATA_ROOT_ENV = fixed.DATA_ROOT_ENV

# 公共协议：逐字沿用固定率先导的登记，仅改写 train_fn 的说明
PUBLIC_PROTOCOL: dict[str, Any] = dict(fixed.FROZEN_COMMON)
PUBLIC_PROTOCOL["train_fn"] = (
    "train_epochs_with_augmentation_control（ch3.train_epochs 的逐句镜像，"
    "仅增加 swap20/flip20 训练批次扰动）"
)

CONTROL_PROTOCOL: dict[str, Any] = {
    "status": "描述性对照，不设支持/证伪判据；单训练种子 42",
    "mask_rng": "mask_rng = np.random.default_rng(ch3.SEED + 1)，独立于 rng 与 buf_rng",
    "rng_seed": ch3.SEED + 1,
    "applies_to": "仅训练批次；ch3.evaluate 与 ch3.score_shard 不施加",
    "fraction": PERTURB_FRACTION,
    "swap20": {
        "purpose": "检验样本间支撑混合是否足以解释增益",
        "pairing": "perm = mask_rng.permutation(B)",
        "selection": "每个样本从全体 D 个特征下标中不放回随机选 round(0.20*D) 个",
        "replacement": "xb[i, idx] = xb[perm[i], idx]",
        "post_transform": "无：不重新二值化，dtype 与形状不变",
        "measured": "实际改变值元素数 / 该批全部元素数；另报被选位置上实际改变比例",
    },
    "flip20": {
        "purpose": "检验任意输入扰动是否足以解释增益",
        "selection": "每批从 B*D 个 (样本, 特征) 元素中不放回随机选 round(0.20*B*D) 个",
        "replacement": "x = 1 - x（0/1 二值输入）",
        "post_transform": "无：dtype 与形状不变",
        "measured": "实际翻转元素数 / 该批全部元素数",
    },
}


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


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写出（先 .partial，再 os.replace）。"""
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def resolve_data_root() -> Path:
    """数据根只从环境变量解析，不写死绝对路径。"""
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


# ---------------------------------------------------------------------------
# 扰动算子
# ---------------------------------------------------------------------------
def sample_distinct_feature_indices(
    mask_rng: np.random.Generator,
    n_rows: int,
    n_features: int,
    k: int,
    margin: float = 0.35,
    max_attempts: int = 8,
) -> np.ndarray:
    """为每行不放回地抽取 `k` 个互不相同的特征下标（均匀 k-子集）。

    做法：先按 `k*(1+margin)` 有放回抽，排序并标记不同值；再对每行的不同值赋
    独立随机键，取键最小的 `k` 个。**不能直接取「前 k 个不同值」**，那会系统性
    偏向低编号特征。抽取余量使「不同值不足 k」的概率可忽略；极少见时用逐行
    `choice(replace=False)` 兜底。返回形状 `(n_rows, k)` 的 int64 数组。
    """
    if k <= 0 or n_rows <= 0:
        return np.empty((n_rows, max(k, 0)), dtype=np.int64)

    draw = int(np.ceil(k * (1.0 + margin)))
    attempts = 0
    remaining = np.arange(n_rows)
    out = np.empty((n_rows, k), dtype=np.int64)

    while remaining.size and attempts < max_attempts:
        attempts += 1
        idx = mask_rng.integers(0, n_features, size=(remaining.size, draw), dtype=np.int64)
        s = np.sort(idx, axis=1)
        keep = np.ones(s.shape, dtype=bool)
        keep[:, 1:] = s[:, 1:] != s[:, :-1]
        counts = keep.sum(axis=1)
        enough = counts >= k

        if enough.any():
            rows_ok = remaining[enough]
            keep_ok = keep[enough]
            s_ok = s[enough]
            # 对每行的不同值赋独立随机键；取键最小的 k 个 ⇒ 均匀随机 k-子集
            keys = mask_rng.random(s_ok.shape, dtype=np.float32)
            keys[~keep_ok] = np.inf
            positions = np.argpartition(keys, k - 1, axis=1)[:, :k]
            out[rows_ok] = np.take_along_axis(s_ok, positions, axis=1)
        remaining = remaining[~enough]

    # 兜底：余量仍不足的行（本数据上不应出现）改用逐行不放回抽样
    for row in remaining:
        out[row] = mask_rng.choice(n_features, size=k, replace=False)

    return out


def perturb_swap20(
    xb: np.ndarray, mask_rng: np.random.Generator
) -> dict[str, float]:
    """样本间交换 20% 的特征位置；原地修改 `xb`，返回实测统计。"""
    n_rows, n_features = xb.shape
    k = int(round(PERTURB_FRACTION * n_features))
    perm = mask_rng.permutation(n_rows)
    idx = sample_distinct_feature_indices(mask_rng, n_rows, n_features, k)

    rows = np.arange(n_rows)[:, None]
    current = xb[rows, idx]
    partner = xb[perm[:, None], idx]
    changed = current != partner
    xb[rows, idx] = partner

    changed_count = int(np.count_nonzero(changed))
    selected_slots = int(idx.size)
    total_values = int(xb.size)
    return {
        "nominal_rate": float(PERTURB_FRACTION),
        "selected_slots": float(selected_slots),
        "changed_values": float(changed_count),
        "measured_rate": float(changed_count / total_values),
        "selected_change_rate": float(changed_count / max(selected_slots, 1)),
        "self_pair_fraction": float(np.count_nonzero(perm == np.arange(n_rows)) / max(n_rows, 1)),
    }


def perturb_flip20(
    xb: np.ndarray, mask_rng: np.random.Generator
) -> dict[str, float]:
    """随机翻转 20% 的全体 (样本, 特征) 元素；原地修改 `xb`，返回实测统计。"""
    total_values = int(xb.size)
    n_selected = int(round(PERTURB_FRACTION * total_values))
    sel = mask_rng.choice(total_values, size=n_selected, replace=False)

    flat = xb.reshape(-1)
    before = flat[sel].copy()
    flat[sel] = (1 - before).astype(xb.dtype)
    changed_count = int(np.count_nonzero(flat[sel] != before))

    return {
        "nominal_rate": float(PERTURB_FRACTION),
        "selected_slots": float(n_selected),
        "changed_values": float(changed_count),
        "measured_rate": float(changed_count / max(total_values, 1)),
        "selected_change_rate": 1.0 if n_selected else 0.0,
    }


# ---------------------------------------------------------------------------
# 训练：ch3.train_epochs（penalty/rho_sched/l2 全关）的逐句镜像 + 批次扰动
# ---------------------------------------------------------------------------
def train_epochs_with_augmentation_control(
    model: nn.Module,
    parts: list[tuple[np.ndarray, np.ndarray]],
    epochs: int,
    batch: int,
    lr: float,
    device: torch.device,
    rng: np.random.Generator,
    mask_rng: np.random.Generator,
    arm: str,
    year: int,
) -> dict[str, Any]:
    """逐句镜像 `ch3.train_epochs`，唯一增量是训练批次前的对照扰动。"""
    opt = torch.optim.SGD(
        model.parameters(),
        lr=lr,
        momentum=ch3.OFFICIAL_MOMENTUM,
        weight_decay=ch3.OFFICIAL_WEIGHT_DECAY,
    )
    criterion = nn.BCELoss()
    model.train()
    epoch_records: list[dict[str, Any]] = []

    for epoch in range(1, epochs + 1):
        epoch_bce = torch.zeros((), device=device)
        n_epoch_batches = 0
        total_values = 0
        total_rows = 0
        total_changed = 0.0
        total_selected = 0
        total_selected_changed = 0.0
        total_self_pair_rows = 0.0
        nonbinary_values = 0
        checked_binary = False

        for xb, yb in ch3.iterate_batches_parts(parts, batch, rng, True):
            if arm == "flip20" and not checked_binary:
                # 只在本年度首个训练批上核验 0/1 二值性（扰动前、不参与训练计算）
                nonbinary_values = int(np.count_nonzero((xb != 0) & (xb != 1)))
                checked_binary = True

            if arm == "swap20":
                stats = perturb_swap20(xb, mask_rng)
                total_self_pair_rows += stats["self_pair_fraction"] * xb.shape[0]
            elif arm == "flip20":
                stats = perturb_flip20(xb, mask_rng)
            else:  # pragma: no cover - argparse 已限制
                raise ValueError(arm)

            total_values += int(xb.size)
            total_rows += int(xb.shape[0])
            total_changed += stats["changed_values"]
            total_selected += int(stats["selected_slots"])
            total_selected_changed += stats["changed_values"]

            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            opt.zero_grad()
            out = model(xt)
            loss = criterion(out, yt)
            epoch_bce = epoch_bce + loss.detach()
            n_epoch_batches += 1
            loss.backward()
            opt.step()

        mean_loss = float(epoch_bce.item() / max(n_epoch_batches, 1))
        measured = float(total_changed / total_values) if total_values else 0.0
        selected_rate = (
            float(total_selected_changed / total_selected) if total_selected else 0.0
        )
        record: dict[str, Any] = {
            "epoch": epoch,
            "mean_loss": mean_loss,
            "perturbation_measured": measured,
            "selected_change_rate": selected_rate,
        }
        if arm == "swap20":
            record["self_pair_fraction"] = (
                float(total_self_pair_rows / max(total_rows, 1)) if total_rows else 0.0
            )
        if arm == "flip20":
            record["nonbinary_values_first_batch"] = nonbinary_values
        epoch_records.append(record)
        print(
            f"[epoch] year={year} arm={arm} epoch={epoch}/{epochs} "
            f"mean_loss={mean_loss:.6f} perturbation_measured={measured:.6f} "
            f"selected_change_rate={selected_rate:.6f}"
            + (
                f" nonbinary={nonbinary_values}"
                if arm == "flip20"
                else ""
            ),
            flush=True,
        )

    return {"epoch_records": epoch_records}


# ---------------------------------------------------------------------------
# 单臂主循环（固定率先导 `run_arm` 的逐句镜像）
# ---------------------------------------------------------------------------
def run_arm(arm: str) -> int:
    assert arm in ARMS, arm
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[arm] {arm} device={device.type} fraction={PERTURB_FRACTION}", flush=True)
    print(
        f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
        f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
        f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch4.MEMORY} "
        f"buffer_scheme={ch4.BUFFER_SCHEME} reuse_scheme={ch4.REUSE_SCHEME} "
        f"buffer_repeat={ch4.BUFFER_REPEAT} pos_ratio={ch4.POS_RATIO} "
        f"deficit_gamma={ch4.DEFICIT_GAMMA} seed={ch3.SEED} "
        f"threshold={ch3.THRESHOLD} mask_seed={ch3.SEED + 1}",
        flush=True,
    )

    years = list(ch3.DOMAIN_YEARS)
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in years:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    input_dim = int(store[years[0]][0].shape[1])

    # 三个随机流与固定率先导完全同序；mask_rng 独立
    rng = np.random.default_rng(ch3.SEED)
    buf_rng = np.random.default_rng(ch3.SEED)
    mask_rng = np.random.default_rng(ch3.SEED + 1)

    model: torch.nn.Module | None = None
    records: list[dict] = []
    preds: dict[int, dict[str, np.ndarray]] = {}
    epoch_records_by_year: dict[str, list[dict[str, Any]]] = {}
    perturbation_by_year: dict[str, float] = {}
    selected_change_by_year: dict[str, float] = {}
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(input_dim).to(device)
            print(f"[model] params={sum(q.numel() for q in model.parameters()):,}", flush=True)

        parts, meta = ch4.build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        sizes = [int(part[0].shape[0]) for part in parts]
        print(f"[parts] {year}: n_parts={len(parts)} sizes={sizes}", flush=True)
        for yr, _, yb in meta["blocks"]:
            nb = int(yb.size)
            pb = int((yb == 1).sum())
            src = store[yr][1]
            ns, psrc = int(src.size), int((src == 1).sum())
            print(
                f"[audit] 截至{year} 缓冲块 {yr}: {nb}槽 正例{pb} 负例{nb - pb} "
                f"| 源 {psrc}/{ns} = {psrc / max(ns, 1):.4f}",
                flush=True,
            )
        if meta["reps"]:
            print(f"[reuse] 截至{year} deficit 复用 = {meta['reps']}", flush=True)

        n_train = int(sum(part[0].shape[0] for part in parts))
        t0 = time.time()
        train_info = train_epochs_with_augmentation_control(
            model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
            ch3.OFFICIAL_LR, device, rng, mask_rng, arm, year,
        )
        epoch_records_by_year[str(year)] = train_info["epoch_records"]
        rates = [r["perturbation_measured"] for r in train_info["epoch_records"]]
        sel_rates = [r["selected_change_rate"] for r in train_info["epoch_records"]]
        perturbation_by_year[str(year)] = float(np.mean(rates)) if rates else 0.0
        selected_change_by_year[str(year)] = float(np.mean(sel_rates)) if sel_rates else 0.0
        print(
            f"[{year}] trained on {n_train:,} rows in {time.time() - t0:.1f}s "
            f"perturbation_measured={perturbation_by_year[str(year)]:.6f} "
            f"selected_change_rate={selected_change_by_year[str(year)]:.6f}",
            flush=True,
        )

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

        # 末年模型对全部 12 个测试分片逐样本打分（主判据与预测制品）
        if idx == len(years) - 1:
            for ty in years:
                xt, yt = ch3.load_year(ty, "test")
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, device).astype(np.float32)
                preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc,
                             "n_nonfinite": int((~np.isfinite(sc)).sum())}
                rec = next(
                    r for r in records
                    if r["experience"] == year and r["test_year"] == ty
                    and r["mode"] == "backward"
                )
                pred = (sc >= ch3.THRESHOLD).astype(int)
                tp = int(np.count_nonzero((pred == 1) & (yt == 1)))
                fp = int(np.count_nonzero((pred == 1) & (yt == 0)))
                fn = int(np.count_nonzero((pred == 0) & (yt == 1)))
                f1m = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
                assert abs(f1m - float(rec["f1"])) < 1e-12, (
                    f"evaluate 与分数口径不一致 {arm} {ty}: {rec['f1']} vs {f1m}"
                )
                print(
                    f"[preds] {arm} 末年模型 @{ty}: f1={f1m:.4f} n={int(yt.size)} "
                    f"pos={int((yt == 1).sum())} nonfinite={preds[ty]['n_nonfinite']}",
                    flush=True,
                )

    final = max(years)
    last = [r for r in records if r["experience"] == final and r["mode"] == "backward"]
    per_year = {str(int(r["test_year"])): float(r["f1"]) for r in last}
    final_avg = float(np.mean([r["f1"] for r in last]))
    print(
        f"\n=== {arm}：末年 {final} 的 avg_f1（官方报告口径）= {final_avg:.10f} ===",
        flush=True,
    )

    for ty, d in preds.items():
        np.savez_compressed(
            RUN_DIR / f"preds_{arm}_{ty}.npz",
            y_true=d["y_true"],
            y_score=d["y_score"],
            threshold=np.float32(ch3.THRESHOLD),
        )

    all_epoch_records = [r for year in years for r in epoch_records_by_year[str(year)]]
    payload: dict[str, Any] = {
        "run_name": RUN_NAME,
        "arm": arm,
        "status": "描述性对照，不设支持/证伪判据；单训练种子 42",
        "ts": now_utc(),
        "public_protocol": PUBLIC_PROTOCOL,
        "augmentation_control_protocol": CONTROL_PROTOCOL,
        "wall_seconds": round(time.time() - t_start, 3),
        "final_experience": final,
        "per_year_f1_final_experience": per_year,
        "final_avg_f1": final_avg,
        "n_test_years": len(last),
        "params_finite_final": bool(
            all(bool(torch.isfinite(q.detach()).all()) for q in model.parameters())
        ),
        "epoch_records_by_year": epoch_records_by_year,
        "epoch_losses": [r["mean_loss"] for r in all_epoch_records],
        "perturbation_measured_by_year": perturbation_by_year,
        "perturbation_measured_mean": float(
            np.mean([perturbation_by_year[str(y)] for y in years])
        ),
        "selected_change_rate_by_year": selected_change_by_year,
        "selected_change_rate_mean": float(
            np.mean([selected_change_by_year[str(y)] for y in years])
        ),
        "records": records,
    }
    write_json(RUN_DIR / f"{arm}-result.json", payload)
    print(f"[done] {arm} 用时 {payload['wall_seconds']:.1f}s", flush=True)

    write_comparison_if_ready()
    return 0


# ---------------------------------------------------------------------------
# 对照汇总（描述性；不设判据）
# ---------------------------------------------------------------------------
def f1_from_scores(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> float:
    """与 `ch3.evaluate` 同一 TP/FP/FN 口径。"""
    pred = (y_score >= threshold).astype(int)
    tp = int(np.count_nonzero((pred == 1) & (y_true == 1)))
    fp = int(np.count_nonzero((pred == 1) & (y_true == 0)))
    fn = int(np.count_nonzero((pred == 0) & (y_true == 1)))
    denom = 2 * tp + fp + fn
    return float(2 * tp / denom) if denom else 0.0


def load_reference_f1(ref_arm: str) -> dict[str, float]:
    """读取参照臂的预测，核验其与结果 JSON 一致，返回逐年 F1。"""
    ref_dir = REFERENCE_DIRS[ref_arm]
    ref_json = json.loads((ref_dir / f"{ref_arm}-result.json").read_text())
    ref_f1 = ref_json["per_year_f1_final_experience"]
    out: dict[str, float] = {}
    for y in ch3.DOMAIN_YEARS:
        key = str(y)
        path = ref_dir / f"preds_{ref_arm}_{y}.npz"
        with np.load(path) as d:
            threshold = float(d["threshold"])
            assert abs(threshold - ch3.THRESHOLD) < 1e-12, (
                f"参照阈值不一致 {path}: {threshold} vs {ch3.THRESHOLD}"
            )
            yt = d["y_true"]
            sc = d["y_score"]
        f1 = f1_from_scores(yt, sc, threshold)
        assert abs(f1 - float(ref_f1[key])) < 1e-9, (
            f"参照 npz 与结果 JSON 不一致 {ref_arm} {key}: {f1} vs {ref_f1[key]}"
        )
        out[key] = float(ref_f1[key])
    return out


def load_control_f1(arm: str, ref_y_true: dict[str, np.ndarray]) -> dict[str, float]:
    """读取对照臂预测，核验 y_true 顺序与 F1，返回逐年 F1。"""
    result = json.loads((RUN_DIR / f"{arm}-result.json").read_text())
    arm_f1 = result["per_year_f1_final_experience"]
    out: dict[str, float] = {}
    for y in ch3.DOMAIN_YEARS:
        key = str(y)
        path = RUN_DIR / f"preds_{arm}_{y}.npz"
        with np.load(path) as d:
            threshold = float(d["threshold"])
            assert abs(threshold - ch3.THRESHOLD) < 1e-12, (
                f"对照阈值不一致 {path}: {threshold} vs {ch3.THRESHOLD}"
            )
            yt = d["y_true"]
            sc = d["y_score"]
        assert np.array_equal(yt, ref_y_true[key]), (
            f"{arm} 与 base 的 y_true 顺序不一致：{key}"
        )
        f1 = f1_from_scores(yt, sc, threshold)
        assert abs(f1 - float(arm_f1[key])) < 1e-9, (
            f"{arm} npz 与结果 JSON 不一致 {key}: {f1} vs {arm_f1[key]}"
        )
        out[key] = float(arm_f1[key])
    return out


def write_comparison_if_ready() -> None:
    """两臂结果与预测都齐备时写出 controls-comparison.json。"""
    result_paths = {arm: RUN_DIR / f"{arm}-result.json" for arm in ARMS}
    preds_ready = all(
        (RUN_DIR / f"preds_{arm}_{y}.npz").is_file()
        for arm in ARMS for y in ch3.DOMAIN_YEARS
    )
    if not (all(path.is_file() for path in result_paths.values()) and preds_ready):
        print("[comparison] 两臂结果尚未齐备，跳过对照汇总", flush=True)
        return

    years = [str(y) for y in ch3.DOMAIN_YEARS]
    refs = {arm: load_reference_f1(arm) for arm in REFERENCE_ARMS}

    # y_true 顺序基准：base
    ref_true: dict[str, np.ndarray] = {}
    for y in ch3.DOMAIN_YEARS:
        with np.load(FEATURE_DROPOUT_DIR / f"preds_base_{y}.npz") as d:
            ref_true[str(y)] = d["y_true"].copy()

    controls = {
        arm: load_control_f1(arm, ref_true) for arm in ARMS
    }

    per_year: dict[str, dict[str, float]] = {}
    for y in years:
        row: dict[str, float] = {}
        for arm in REFERENCE_ARMS:
            row[f"f1_{arm}"] = float(refs[arm][y])
        for arm in ARMS:
            row[f"f1_{arm}"] = float(controls[arm][y])
        for arm in ARMS:
            for ref_arm in REFERENCE_ARMS:
                row[f"delta_{arm}_minus_{ref_arm}"] = (
                    float(controls[arm][y]) - float(refs[ref_arm][y])
                )
        per_year[y] = row

    summary: dict[str, Any] = {
        "mean_f1": {
            **{arm: float(np.mean([refs[arm][y] for y in years])) for arm in REFERENCE_ARMS},
            **{arm: float(np.mean([controls[arm][y] for y in years])) for arm in ARMS},
        },
        "delta_mean_f1": {},
        "delta_mean_f1_pp": {},
    }
    for arm in ARMS:
        for ref_arm in REFERENCE_ARMS:
            delta = summary["mean_f1"][arm] - summary["mean_f1"][ref_arm]
            summary["delta_mean_f1"][f"{arm}_minus_{ref_arm}"] = float(delta)
            summary["delta_mean_f1_pp"][f"{arm}_minus_{ref_arm}"] = float(delta * 100.0)

    base_result = json.loads((FEATURE_DROPOUT_DIR / "base-result.json").read_text())
    base_observed = float(base_result["final_avg_f1"])
    payload: dict[str, Any] = {
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "label": "描述性对照，不设支持/证伪判据；单训练种子 42",
        "disclosure": (
            "本文件只报告 swap20 与 flip20 相对 base/drop20/adapt 的逐年度与 12 年平均"
            "ΔF1，用于判断自适应掩码增益是否可由任意输入扰动或样本间支撑混合解释。"
            "未做多种子训练，不作训练随机性下的稳健性主张，也不据此单独裁决机制存废。"
        ),
        "public_protocol": PUBLIC_PROTOCOL,
        "augmentation_control_protocol": CONTROL_PROTOCOL,
        "references": {
            "base": str(FEATURE_DROPOUT_DIR / "preds_base_{year}.npz"),
            "drop20": str(FEATURE_DROPOUT_DIR / "preds_drop20_{year}.npz"),
            "adapt": str(ADAPTIVE_MASK_DIR / "preds_adapt_{year}.npz"),
        },
        "per_year": per_year,
        "summary": summary,
        "integrity_checks": {
            "base_gate_expected": GATE_BASE_REF,
            "base_gate_observed": base_observed,
            "base_gate_abs_delta": abs(base_observed - GATE_BASE_REF),
            "base_gate_passed": abs(base_observed - GATE_BASE_REF) < GATE_BASE_TOL,
            "control_y_true_equals_base_by_year": True,
            "control_npz_f1_equals_result_json": True,
            "reference_npz_f1_equals_reference_result_json": True,
            "mask_rng_independent_of_train_and_buffer_rng": True,
            "evaluation_and_scoring_never_perturbed": True,
        },
        "notes": [
            "ΔF1 = 对照臂 − 参照臂；正值表示对照臂更高。",
            "swap20 检验「样本间支撑混合」；flip20 检验「任意输入扰动」。",
            "实测扰动率见各臂 result JSON 的 perturbation_measured_by_year。",
            "单种子 42；本文件不是判据，不给出支持/证伪结论。",
        ],
    }
    write_json(RUN_DIR / "controls-comparison.json", payload)

    print("\n=== 增广对照 vs base / drop20 / adapt ===", flush=True)
    header = (
        "year      f1_swap20  d_base   d_drop20  d_adapt    "
        "f1_flip20  d_base   d_drop20  d_adapt"
    )
    print(header, flush=True)
    for y in years:
        r = per_year[y]
        print(
            f"{y}  {r['f1_swap20']:.6f}  "
            f"{r['delta_swap20_minus_base'] * 100:+.3f}  "
            f"{r['delta_swap20_minus_drop20'] * 100:+.3f}  "
            f"{r['delta_swap20_minus_adapt'] * 100:+.3f}  "
            f"{r['f1_flip20']:.6f}  "
            f"{r['delta_flip20_minus_base'] * 100:+.3f}  "
            f"{r['delta_flip20_minus_drop20'] * 100:+.3f}  "
            f"{r['delta_flip20_minus_adapt'] * 100:+.3f}",
            flush=True,
        )
    print(
        "12-year mean: "
        + " ".join(f"{arm}={summary['mean_f1'][arm]:.10f}" for arm in REFERENCE_ARMS + ARMS),
        flush=True,
    )
    for arm in ARMS:
        for ref_arm in REFERENCE_ARMS:
            print(
                f"  {arm} - {ref_arm}: "
                f"{summary['delta_mean_f1_pp'][f'{arm}_minus_{ref_arm}']:+.4f} pp",
                flush=True,
            )
    print(f"[comparison] 已写出 {RUN_DIR / 'controls-comparison.json'}", flush=True)


def main(arm: str) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    ch3.DATA_ROOT = resolve_data_root()   # 覆盖被导入模块的数据根，不写死绝对路径
    return run_arm(arm)


if __name__ == "__main__":
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(
        description="第四章增广对照先导（swap20 / flip20）")
    parser.add_argument("--arm", choices=ARMS, required=True)
    args = parser.parse_args()
    _log_fh = (RUN_DIR / f"{args.arm}.log").open("a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_fh)
    sys.stderr = _Tee(sys.__stderr__, _log_fh)
    try:
        raise SystemExit(main(args.arm))
    finally:
        _log_fh.flush()
