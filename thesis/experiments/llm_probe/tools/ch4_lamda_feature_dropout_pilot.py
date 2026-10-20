#!/usr/bin/env python
"""第四章最小材料性先导：训练时输入活跃特征的随机丢弃。

## 只回答一个问题

在**训练**的每个批次前对输入特征做独立随机丢弃（保留概率 `1-p`），能否改善
12 年平均 F1。这是「特征支撑集翻转」这一病灶的材料性检验，不是机制定案。

## 冻结公共协议（逐字沿用 `ch4_lamda_cold_init_pilot.py`，不得改动）

- 年份：`ch3.DOMAIN_YEARS`（12 年）
- `epochs=10`、`batch=1024`、`lr=0.01`、`momentum=0.9`、`weight_decay=1e-6`
- `seed=42`、`threshold=0.5`
- 容量 `memory=200`、`buffer_scheme="quota"`、`reuse_scheme="deficit"`、
  `buffer_repeat=2`、`pos_ratio=0.5`、`deficit_gamma=1.0`
- 优化器每年在训练函数体内重建（与 `ch3.train_epochs` 一致）

模型与数据加载直接 import `ch3_lamda_domain_il_e4`；缓冲构造直接复用
`ch4_lamda_training_process_2x2.build_parts`。本脚本不改动任何既有文件。

## 三臂

- `base`：与 `ch4_lamda_cold_init_pilot.py --arm base` 的年度循环逐句一致
  （无冷坐标缩放、无特征丢弃）。复现门：12 年平均 F1 必须等于
  `0.8169830287163194`（绝对容差 `1e-6`）。
- `drop10`：`p=0.10`；`drop20`：`p=0.20`。其余与 `base` 完全相同，只在**训练**的
  每个批次前做一次输入特征丢弃：

      keep = (mask_rng.random(xb.shape) >= p).astype(np.float32)
      xb = xb * torch.from_numpy(keep).to(device)

  掩码随机源 `mask_rng = np.random.default_rng(ch3.SEED + 1)`，**独立于**训练洗牌
  `rng` 与缓冲构造 `buf_rng` ⇒ 各臂的数据顺序与 base 逐位一致。
  **只在训练时丢弃；评价与打分绝不丢弃。** 丢弃后的特征不做任何再二值化或其他变换。

## 训练函数

`ch3.train_epochs`（penalty／rho_sched／l2 全关）的逐句镜像，仅增加可选的逐批特征
丢弃；`p=0` 时完全不生成掩码，因此 `base` 与 `ch3.train_epochs` 逐位一致。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_feature_dropout_pilot.py --arm base
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_feature_dropout_pilot.py --arm drop10
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_feature_dropout_pilot.py --arm drop20
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
import ch4_lamda_training_process_2x2 as ch4  # noqa: E402  （复用 build_parts）

# ---------------------------------------------------------------------------
# 冻结配置
# ---------------------------------------------------------------------------
RUN_NAME = "ch4-lamda-feature-dropout-pilot"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs" / "diagnostics" / RUN_NAME

ARMS: tuple[str, ...] = ("base", "drop10", "drop20")
ARM_P: dict[str, float] = {"base": 0.0, "drop10": 0.10, "drop20": 0.20}

GATE_BASE_REF = 0.8169830287163194
GATE_BASE_TOL = 1e-6

DATA_ROOT_ENV = "LAMDA_DATA_ROOT"

# 三臂必须逐字相同的公共协议（结果 JSON 中完整登记）
FROZEN_COMMON: dict[str, Any] = {
    "strategy": "expreplay",
    "buffer_scheme": "quota",
    "reuse_scheme": "deficit",
    "buffer_repeat": 2,
    "memory": 200,
    "pos_ratio": 0.5,
    "deficit_gamma": 1.0,
    "epochs": ch3.OFFICIAL_EPOCHS,
    "batch": ch3.OFFICIAL_BATCH,
    "lr": ch3.OFFICIAL_LR,
    "momentum": ch3.OFFICIAL_MOMENTUM,
    "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
    "seed": ch3.SEED,
    "threshold": ch3.THRESHOLD,
    "domain_years": list(ch3.DOMAIN_YEARS),
    "optimizer_lifetime": "per_year_rebuild_inside_train_fn",
    "rng_streams": "train_rng=default_rng(SEED); buf_rng=default_rng(SEED)（各臂同序消费）",
    "model": "ch3.ChenEncoderMLP",
    "train_fn": "train_epochs_with_feature_dropout（ch3.train_epochs 的逐句镜像）",
    "evaluate_fn": "ch3.evaluate",
    "score_fn": "ch3.score_shard",
}

FEATURE_DROPOUT_PROTOCOL: dict[str, Any] = {
    "applies_to": "仅训练批次；评价 ch3.evaluate 与打分 ch3.score_shard 不丢弃",
    "mask_formula": "keep = (mask_rng.random(xb.shape) >= p).astype(np.float32); xb = xb * keep",
    "rng": "mask_rng = np.random.default_rng(ch3.SEED + 1)，独立于 rng 与 buf_rng",
    "rng_seed": ch3.SEED + 1,
    "post_transform": "无：丢弃后不重新二值化，不做其他变换",
    "p_by_arm": ARM_P,
}


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
# 训练：ch3.train_epochs（penalty/rho_sched/l2 全关）的逐句镜像 + 可选特征丢弃
# ---------------------------------------------------------------------------
def train_epochs_with_feature_dropout(
    model: nn.Module,
    parts: list[tuple[np.ndarray, np.ndarray]],
    epochs: int,
    batch: int,
    lr: float,
    device: torch.device,
    rng: np.random.Generator,
    p: float,
    mask_rng: np.random.Generator,
    year: int,
) -> dict[str, Any]:
    """逐句镜像 `ch3.train_epochs`，唯一增量是训练批次前的特征丢弃。

    - `p == 0` 时**完全不生成掩码**、不消费 `mask_rng`，故 `base` 与 `ch3.train_epochs`
      逐位一致（复现门验证）。
    - `mask_rng` 与 `rng`／`buf_rng` 相互独立，批序与 base 逐位一致。
    - 训练轮内打印 `epoch`、`mean_loss`、实测丢弃率 `1 - keep.mean()`。
    """
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=ch3.OFFICIAL_MOMENTUM,
                          weight_decay=ch3.OFFICIAL_WEIGHT_DECAY)
    criterion = nn.BCELoss()
    model.train()
    epoch_records: list[dict[str, Any]] = []
    for epoch in range(1, epochs + 1):
        epoch_bce = torch.zeros((), device=device)
        n_epoch_batches = 0
        total_entries = 0
        total_dropped = 0.0
        for xb, yb in ch3.iterate_batches_parts(parts, batch, rng, True):
            xt = torch.from_numpy(xb.astype(np.float32)).to(device)
            yt = torch.from_numpy(yb).to(device).unsqueeze(1)
            if p > 0.0:
                keep = (mask_rng.random(tuple(xt.shape)) >= p).astype(np.float32)
                xt = xt * torch.from_numpy(keep).to(device)
                total_entries += int(keep.size)
                total_dropped += float(keep.size - keep.sum())
            opt.zero_grad()
            out = model(xt)
            loss = criterion(out, yt)
            epoch_bce = epoch_bce + loss.detach()
            n_epoch_batches += 1
            loss.backward()
            opt.step()
        mean_loss = float(epoch_bce.item() / max(n_epoch_batches, 1))
        measured = float(total_dropped / total_entries) if total_entries else 0.0
        epoch_records.append({
            "epoch": epoch,
            "mean_loss": mean_loss,
            "dropout_measured": measured,
        })
        print(
            f"[epoch] year={year} epoch={epoch}/{epochs} mean_loss={mean_loss:.6f} "
            f"dropout_measured={measured:.6f}",
            flush=True,
        )
    return {"epoch_records": epoch_records}


# ---------------------------------------------------------------------------
# 单臂主循环
# ---------------------------------------------------------------------------
def run_arm(arm: str) -> int:
    assert arm in ARMS, arm
    p = ARM_P[arm]
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[arm] {arm} p={p} device={device.type}", flush=True)
    print(
        f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
        f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
        f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch4.MEMORY} "
        f"buffer_scheme={ch4.BUFFER_SCHEME} reuse_scheme={ch4.REUSE_SCHEME} "
        f"buffer_repeat={ch4.BUFFER_REPEAT} pos_ratio={ch4.POS_RATIO} "
        f"deficit_gamma={ch4.DEFICIT_GAMMA} seed={ch3.SEED} "
        f"threshold={ch3.THRESHOLD} p={p} mask_seed={ch3.SEED + 1}",
        flush=True,
    )

    years = list(ch3.DOMAIN_YEARS)
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in years:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    input_dim = int(store[years[0]][0].shape[1])

    # 开局播种一次；各臂的 rng 与 buf_rng 同种子、同序消费（与 base 逐位一致）
    rng = np.random.default_rng(ch3.SEED)
    buf_rng = np.random.default_rng(ch3.SEED)
    # 掩码随机源独立于 rng 与 buf_rng；base 不消费它
    mask_rng = np.random.default_rng(ch3.SEED + 1)

    model: torch.nn.Module | None = None
    records: list[dict] = []
    preds: dict[int, dict[str, np.ndarray]] = {}
    epoch_records_by_year: dict[str, list[dict[str, Any]]] = {}
    dropout_by_year: dict[str, float] = {}
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
        train_info = train_epochs_with_feature_dropout(
            model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
            ch3.OFFICIAL_LR, device, rng, p, mask_rng, year,
        )
        epoch_records_by_year[str(year)] = train_info["epoch_records"]
        drop_vals = [r["dropout_measured"] for r in train_info["epoch_records"]]
        dropout_by_year[str(year)] = float(np.mean(drop_vals)) if drop_vals else 0.0
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
        "p": p,
        "ts": now_utc(),
        "public_protocol": FROZEN_COMMON,
        "feature_dropout_protocol": FEATURE_DROPOUT_PROTOCOL,
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
        "dropout_measured_by_year": dropout_by_year,
        "dropout_measured_mean": float(
            np.mean([dropout_by_year[str(y)] for y in years])
        ),
        "records": records,
    }
    write_json(RUN_DIR / f"{arm}-result.json", payload)
    print(f"[done] {arm} 用时 {payload['wall_seconds']:.1f}s", flush=True)

    # 复现门：base 末年 12 年平均 F1 必须复现参照值；不通过立即停止，不得调数
    if arm == "base":
        delta = abs(final_avg - GATE_BASE_REF)
        ok = delta < GATE_BASE_TOL
        print(
            f"[gate] base 复现门：末年 12 年平均 F1 = {final_avg:.10f}，"
            f"参照 {GATE_BASE_REF:.10f}，绝对差 {delta:.3e} ⇒ "
            f"{'PASS' if ok else 'FAIL'}",
            flush=True,
        )
        if not ok:
            print(
                "[gate] base 未复现参照值，按任务要求立即停止，不得调数凑。",
                flush=True,
            )
            return 1

    write_comparison_if_ready()
    return 0


def write_comparison_if_ready() -> None:
    """三臂结果都在时写出 comparison.json。"""
    paths = {arm: RUN_DIR / f"{arm}-result.json" for arm in ARMS}
    if not all(path.is_file() for path in paths.values()):
        return

    results = {arm: json.loads(path.read_text()) for arm, path in paths.items()}
    years = [str(y) for y in ch3.DOMAIN_YEARS]
    base = results["base"]

    per_year: dict[str, dict[str, float]] = {}
    for y in years:
        fb = float(base["per_year_f1_final_experience"][y])
        row: dict[str, float] = {"f1_base": fb}
        for arm in ("drop10", "drop20"):
            fa = float(results[arm]["per_year_f1_final_experience"][y])
            row[f"f1_{arm}"] = fa
            row[f"delta_{arm}_minus_base"] = fa - fb
        per_year[y] = row

    mean_base = float(np.mean([per_year[y]["f1_base"] for y in years]))
    arm_summary: dict[str, Any] = {}
    for arm in ("drop10", "drop20"):
        mean_arm = float(np.mean([per_year[y][f"f1_{arm}"] for y in years]))
        arm_summary[arm] = {
            "p": ARM_P[arm],
            "mean_f1": mean_arm,
            "delta_mean_f1_minus_base": mean_arm - mean_base,
            "dropout_measured_mean": float(results[arm]["dropout_measured_mean"]),
        }

    payload = {
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "reference_arm": "base",
        "comparison_arms": ["drop10", "drop20"],
        "public_protocol": FROZEN_COMMON,
        "feature_dropout_protocol": FEATURE_DROPOUT_PROTOCOL,
        "per_year": per_year,
        "mean_f1_base": mean_base,
        "arms": arm_summary,
        "base_gate": {
            "expected": GATE_BASE_REF,
            "observed": float(base["final_avg_f1"]),
            "abs_delta": abs(float(base["final_avg_f1"]) - GATE_BASE_REF),
            "passed": abs(float(base["final_avg_f1"]) - GATE_BASE_REF) < GATE_BASE_TOL,
        },
        "notes": [
            "ΔF1 = drop* − base，单种子 42，未做多种子训练。",
            "本文件只报告材料性先导读数，不作机制定案。",
        ],
    }
    write_json(RUN_DIR / "comparison.json", payload)
    print(f"[comparison] 已写出 {RUN_DIR / 'comparison.json'}", flush=True)


def main(arm: str) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    ch3.DATA_ROOT = resolve_data_root()   # 覆盖被导入模块的数据根，不写死绝对路径
    return run_arm(arm)


if __name__ == "__main__":
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    p = argparse.ArgumentParser(
        description="第四章输入特征丢弃先导（base / drop10 / drop20）")
    p.add_argument("--arm", choices=ARMS, required=True)
    a = p.parse_args()
    _log_fh = (RUN_DIR / f"{a.arm}.log").open("a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_fh)
    sys.stderr = _Tee(sys.__stderr__, _log_fh)
    try:
        raise SystemExit(main(a.arm))
    finally:
        _log_fh.flush()
