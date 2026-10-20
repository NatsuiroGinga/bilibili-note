#!/usr/bin/env python
"""第四章最小证伪先导：年度起点冷坐标的首层权重列尺度放大。

## 只回答一个问题

在每年开始时，把「本年度训练分片首次激活、此前任何年度训练分片从未激活」的特征坐标
（冷坐标）对应的首层权重列按数据依赖尺度放大，能否改善 12 年平均 F1。

这是材料性检验，不是机制定案。

## 冻结公共协议（逐字沿用，不得改动）

- 年份：`ch3.DOMAIN_YEARS`（12 年）
- `epochs=10`、`batch=1024`、`lr=0.01`、`momentum=0.9`、`weight_decay=1e-6`
- `seed=42`、`threshold=0.5`
- 容量 `memory=200`、`buffer_scheme="quota"`、`reuse_scheme="deficit"`、
  `buffer_repeat=2`、`pos_ratio=0.5`、`deficit_gamma=1.0`
- 优化器由 `ch3.train_epochs` 在函数体内每年重建

模型与数据加载直接 import `ch3_lamda_domain_il_e4`；缓冲构造直接复用
`ch4_lamda_training_process_2x2.build_parts`。本脚本不改动任何既有文件。

## 两臂

- `base`：与 `ch4_lamda_training_process_2x2.run_arm("base")` 的年度循环逐句一致，
  但跳过与单臂无关的四个自检。复现门：末年 2025 的 12 年平均 F1 必须等于
  `0.8169830287163194`（绝对容差 `1e-6`）。
- `coldinit`：与 `base` 完全相同，只在 idx>0 的每年训练开始前做一次确定性缩放：

      active_curr = np.any(x_curr != 0, axis=0)
      cold = active_curr & ~ever_active          # ever_active 只累计此前年度 train
      p = nnz(x_curr) / x_curr.size
      target_std = sqrt(2 / max(1, p * d))
      cur_std = std(model.encoder[0].weight[:, cold])
      factor = min(64, max(1, target_std / max(cur_std, 1e-12)))
      weight[:, cold] *= factor

  **不消耗任何随机数**；第一年（2013）不缩放；`ever_active` 不读测试分片。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_cold_init_pilot.py --arm base
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_cold_init_pilot.py --arm coldinit
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

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
import ch4_lamda_training_process_2x2 as ch4  # noqa: E402  （复用 build_parts）

# ---------------------------------------------------------------------------
# 冻结配置
# ---------------------------------------------------------------------------
RUN_NAME = "ch4-lamda-cold-init-pilot"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs" / "diagnostics" / RUN_NAME

ARMS: tuple[str, ...] = ("base", "coldinit")
GATE_BASE_REF = 0.8169830287163194
GATE_BASE_TOL = 1e-6

MAX_SCALE = 64.0
DATA_ROOT_ENV = "LAMDA_DATA_ROOT"

# 两臂必须逐字相同的公共协议（结果 JSON 中完整登记）
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
    "optimizer_lifetime": "per_year_rebuild_inside_ch3.train_epochs",
    "rng_streams": "train_rng=default_rng(SEED); buf_rng=default_rng(SEED)（各臂同序消费）",
    "model": "ch3.ChenEncoderMLP",
    "train_fn": "ch3.train_epochs",
    "evaluate_fn": "ch3.evaluate",
    "score_fn": "ch3.score_shard",
}

COLD_INIT_PROTOCOL: dict[str, Any] = {
    "enabled": True,
    "cold_definition": "active_curr & ~ever_active；ever_active 只累计此前年度 **train** 分片",
    "p_formula": "count_nonzero(x_curr) / x_curr.size",
    "target_std_formula": "sqrt(2 / max(1, p * d))",
    "factor_formula": "min(64, max(1, target_std / max(cur_std, 1e-12)))",
    "target_tensor": "model.encoder[0].weight[:, cold]（首个 nn.Linear，shape=(512, d)）",
    "application": "仅 idx>0 且 cold_count>0 时原地乘以 factor；第一年 2013 不缩放",
    "rng": "确定性乘法，不消耗任何随机数",
    "test_split_usage": "ever_active 与 cold 均只读训练分片，不读测试分片",
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
# 冷坐标缩放（coldinit 臂唯一的行为差异）
# ---------------------------------------------------------------------------
def cold_scale_inplace(
    model: torch.nn.Module,
    x_curr: np.ndarray,
    ever_active: np.ndarray,
    idx: int,
) -> dict[str, Any]:
    """按冻结公式计算并（idx>0 时）施加首层冷坐标列缩放。

    纯确定性乘法，不消耗任何随机数；返回值只用于日志与结果 JSON。
    """
    active_curr = np.any(x_curr != 0, axis=0)
    cold = active_curr & ~ever_active
    cold_count = int(np.count_nonzero(cold))

    p = float(np.count_nonzero(x_curr)) / float(x_curr.size)
    target_std = math.sqrt(2.0 / max(1.0, p * x_curr.shape[1]))

    w = model.encoder[0].weight.data
    cur_std: float | None = None
    factor = 1.0
    applied = False

    if cold_count > 0:
        mask = torch.as_tensor(cold, device=w.device, dtype=torch.bool)
        cur_std = float(w[:, mask].std().item())
        if math.isfinite(cur_std):
            factor = min(MAX_SCALE, max(1.0, target_std / max(cur_std, 1e-12)))
            if idx > 0:
                with torch.no_grad():
                    w[:, mask] *= factor
                applied = True

    # 只累计训练分片；必须在缩放之后更新，使本年度冷坐标按定义是「此前从未激活」
    ever_active |= active_curr

    return {
        "year": int(ch3.DOMAIN_YEARS[idx]),
        "cold_count": cold_count,
        "p": p,
        "input_dim": int(x_curr.shape[1]),
        "target_std": target_std,
        "cur_std": cur_std,
        "factor": factor,
        "applied": applied,
    }


# ---------------------------------------------------------------------------
# 单臂主循环
# ---------------------------------------------------------------------------
def run_arm(arm: str) -> int:
    assert arm in ARMS, arm
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[arm] {arm} device={device.type}", flush=True)
    print(
        f"[config] epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
        f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
        f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch4.MEMORY} "
        f"buffer_scheme={ch4.BUFFER_SCHEME} reuse_scheme={ch4.REUSE_SCHEME} "
        f"buffer_repeat={ch4.BUFFER_REPEAT} pos_ratio={ch4.POS_RATIO} "
        f"deficit_gamma={ch4.DEFICIT_GAMMA} seed={ch3.SEED} "
        f"threshold={ch3.THRESHOLD}",
        flush=True,
    )

    years = list(ch3.DOMAIN_YEARS)
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in years:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    input_dim = int(store[years[0]][0].shape[1])

    # 开局播种一次；两臂的 rng 与 buf_rng 同种子、同序消费（与 run_arm 一致）
    rng = np.random.default_rng(ch3.SEED)
    buf_rng = np.random.default_rng(ch3.SEED)

    model: torch.nn.Module | None = None
    ever_active = np.zeros(input_dim, dtype=bool)
    records: list[dict] = []
    preds: dict[int, dict[str, np.ndarray]] = {}
    cold_stats: dict[str, dict[str, Any]] = {}
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(input_dim).to(device)
            print(f"[model] params={sum(p.numel() for p in model.parameters()):,}", flush=True)

        if arm == "coldinit":
            stats = cold_scale_inplace(model, x_curr, ever_active, idx)
            cold_stats[str(year)] = stats
            cur = "None" if stats["cur_std"] is None else f"{stats['cur_std']:.6e}"
            print(
                f"[coldinit] year={stats['year']} cold_count={stats['cold_count']} "
                f"p={stats['p']:.6e} target_std={stats['target_std']:.6f} "
                f"cur_std={cur} factor={stats['factor']:.6f} applied={stats['applied']}",
                flush=True,
            )

        parts, meta = ch4.build_parts(store, years, idx, x_curr, y_curr, buf_rng)
        sizes = [int(p[0].shape[0]) for p in parts]
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

        n_train = int(sum(p[0].shape[0] for p in parts))
        t0 = time.time()
        ch3.train_epochs(
            model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
            ch3.OFFICIAL_LR, device, rng,
        )
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

    payload: dict[str, Any] = {
        "run_name": RUN_NAME,
        "arm": arm,
        "ts": now_utc(),
        "public_protocol": FROZEN_COMMON,
        "cold_init_protocol": {**COLD_INIT_PROTOCOL, "enabled": arm == "coldinit"},
        "wall_seconds": round(time.time() - t_start, 3),
        "final_experience": final,
        "per_year_f1_final_experience": per_year,
        "final_avg_f1": final_avg,
        "n_test_years": len(last),
        "params_finite_final": bool(
            all(bool(torch.isfinite(p.detach()).all()) for p in model.parameters())
        ),
        "records": records,
    }
    if arm == "coldinit":
        payload["cold_stats_per_year"] = cold_stats

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
    """两臂结果都在时写出 comparison.json。"""
    base_path = RUN_DIR / "base-result.json"
    cold_path = RUN_DIR / "coldinit-result.json"
    if not (base_path.is_file() and cold_path.is_file()):
        return

    base = json.loads(base_path.read_text())
    cold = json.loads(cold_path.read_text())
    years = [str(y) for y in ch3.DOMAIN_YEARS]

    per_year: dict[str, dict[str, float]] = {}
    for y in years:
        fb = float(base["per_year_f1_final_experience"][y])
        fc = float(cold["per_year_f1_final_experience"][y])
        per_year[y] = {
            "f1_base": fb,
            "f1_coldinit": fc,
            "delta_coldinit_minus_base": fc - fb,
        }

    mean_base = float(np.mean([per_year[y]["f1_base"] for y in years]))
    mean_cold = float(np.mean([per_year[y]["f1_coldinit"] for y in years]))

    payload = {
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "reference_arm": "base",
        "comparison_arm": "coldinit",
        "public_protocol": FROZEN_COMMON,
        "per_year": per_year,
        "mean_f1_base": mean_base,
        "mean_f1_coldinit": mean_cold,
        "delta_mean_f1_coldinit_minus_base": mean_cold - mean_base,
        "base_gate": {
            "expected": GATE_BASE_REF,
            "observed": float(base["final_avg_f1"]),
            "abs_delta": abs(float(base["final_avg_f1"]) - GATE_BASE_REF),
            "passed": abs(float(base["final_avg_f1"]) - GATE_BASE_REF) < GATE_BASE_TOL,
        },
        "cold_stats_per_year": cold.get("cold_stats_per_year", {}),
        "notes": [
            "ΔF1 = coldinit − base，单种子 42，未做多种子训练。",
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
    p = argparse.ArgumentParser(description="第四章冷坐标首层列尺度先导（base / coldinit）")
    p.add_argument("--arm", choices=ARMS, required=True)
    a = p.parse_args()
    _log_fh = (RUN_DIR / f"{a.arm}.log").open("a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_fh)
    sys.stderr = _Tee(sys.__stderr__, _log_fh)
    try:
        raise SystemExit(main(a.arm))
    finally:
        _log_fh.flush()
