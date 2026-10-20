#!/usr/bin/env python
"""第四章自适应特征掩码确认性先导（单臂 `adapt`）。

## 只回答一个问题

在 `ch4-lamda-feature-dropout-pilot` 的固定率读数已经产出之后，把年度掩码强度设为
**当前年度活跃支撑规模的函数**，能否在保持后期年度增益的同时避免早期年度过正则化，
从而放大 12 年平均增益（研究问题卡 §二 H2）。

## 判据来源（逐字执行，不得改动）

`thesis/methods/第四章研究问题卡-特征支撑增广.md` §四（冻结算规则）与 §五（支持／证伪判据）。
本脚本是**结果知情后的确认性检验**，不是预注册假设；正文不得写成「预先注册的 adaptive 机制」。

## 冻结算规则（研究问题卡 §四）

对每个年度 t：

    n_t = 当前年度训练分片中至少一个样本取 1 的特征坐标数   # 只用 train，不用标签、不用测试分片
    p_t = 0.20 * clip((n_t - 3000) / 500, 0, 1)

逐年度预期：2013–2017 为 0；2018 约 0.198；2019–2025 为 0.20。

## 掩码形式（与固定率先导逐字相同）

直接导入 `ch4_lamda_feature_dropout_pilot.train_epochs_with_feature_dropout`，
按年度传入标量 `p_t`：

    keep = (mask_rng.random(xb.shape) >= p_t).astype(np.float32)
    xb = xb * keep

只在训练批次上施加；`ch3.evaluate` 与 `ch3.score_shard` 绝不施加。
`mask_rng = np.random.default_rng(ch3.SEED + 1)` 只创建一次，独立于训练洗牌 `rng`
与缓冲构造 `buf_rng`；`p_t == 0` 的年度不生成掩码、不消费 `mask_rng`，与固定率臂的行为一致。

## 公共协议（逐字沿用，不得改）

年份、`epochs=10`、`batch=1024`、`lr=0.01`、`momentum=0.9`、`wd=1e-6`、`seed=42`、
`threshold=0.5`、`memory=200`、`buffer_scheme="quota"`、`reuse_scheme="deficit"`、
`buffer_repeat=2`、`pos_ratio=0.5`、`deficit_gamma=1.0`；模型与数据加载 import
`ch3_lamda_domain_il_e4`，缓冲构造复用 `ch4_lamda_training_process_2x2.build_parts`。

## 产物

- `adapt-result.json`：公共协议、`wall_seconds`、逐年 `n_t/p_t`、逐年 F1、12 年平均、逐轮 loss。
- `preds_adapt_{year}.npz`：`y_true/y_score/threshold`（与既有预测同序）。
- `adapt-comparison.json`：以既有 `preds_base_*.npz`、`preds_drop20_*.npz` 为参照的
  逐年 ΔF1、12 年平均 Δ，以及研究问题卡 §五 六条判据的逐条判定。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_adaptive_mask_pilot.py
"""

from __future__ import annotations

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

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）
import ch4_lamda_feature_dropout_pilot as fixed  # noqa: E402  （逐字复用训练函数与协议）
import ch4_lamda_training_process_2x2 as ch4  # noqa: E402  （复用 build_parts）

# ---------------------------------------------------------------------------
# 冻结配置（研究问题卡 §四／§五；不得改动）
# ---------------------------------------------------------------------------
ARM = "adapt"
RUN_NAME = "ch4-lamda-adaptive-mask-pilot"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs" / "diagnostics" / RUN_NAME
REF_RUN_DIR = Path(__file__).resolve().parents[1] / "runs" / "diagnostics" / "ch4-lamda-feature-dropout-pilot"
REF_ARMS: tuple[str, ...] = ("base", "drop20")

# 自适应调度规则（研究问题卡 §四，逐字）
P_MAX = 0.20
N_LOW = 3000
N_SPAN = 500

# 研究问题卡 §五 的判据年度窗口（DOMAIN_YEARS 中 2018–2023 恰为六个年度）
CRITERION_YEARS: tuple[int, ...] = (2018, 2019, 2020, 2021, 2022, 2023)

SUPPORT_MEAN_DELTA_PP = 0.50       # S1: adapt − base ≥ +0.50 pp
SUPPORT_VS_DROP20_PP = -0.20        # S2: adapt ≥ drop20 − 0.20 pp
SUPPORT_POSITIVE_YEARS = 5         # S3: 2018–2023 中 adapt − base > 0 的年度数 ≥ 5
FALSIFY_MEAN_DELTA_PP = 0.00       # F1: adapt − base ≤ 0.00 pp
FALSIFY_VS_DROP20_PP = -0.30       # F2: adapt < drop20 − 0.30 pp
FALSIFY_NEGATIVE_YEARS = 3         # F3: 2018–2023 中 adapt − base < 0 的年度数 ≥ 3

DATA_ROOT_ENV = fixed.DATA_ROOT_ENV

# 公共协议：逐字沿用固定率先导的登记，仅改写 train_fn 的说明
PUBLIC_PROTOCOL: dict[str, Any] = dict(fixed.FROZEN_COMMON)
PUBLIC_PROTOCOL["train_fn"] = (
    "train_epochs_with_feature_dropout（从 ch4_lamda_feature_dropout_pilot 逐字导入，"
    "按年度传入标量 p_t）"
)

ADAPTIVE_MASK_PROTOCOL: dict[str, Any] = {
    "status": "结果知情后的确认性检验，不是预注册假设",
    "rule": "n_t = 当前年度训练分片中至少一个样本取 1 的特征坐标数；"
            "p_t = 0.20 * clip((n_t - 3000) / 500, 0, 1)",
    "uses_only": "当前年度 train 特征矩阵；不使用标签、不使用测试分片",
    "mask_formula": "keep = (mask_rng.random(xb.shape) >= p_t).astype(np.float32); xb = xb * keep",
    "applies_to": "仅训练批次；ch3.evaluate 与 ch3.score_shard 不施加",
    "rng": "mask_rng = np.random.default_rng(ch3.SEED + 1)，独立于 rng 与 buf_rng",
    "rng_seed": ch3.SEED + 1,
    "post_transform": "无：丢弃后不重新二值化，不做其他变换",
    "p_max": P_MAX,
    "n_low": N_LOW,
    "n_span": N_SPAN,
    "expected_p_t": {
        "2013-2017": 0.0,
        "2018": "约 0.198",
        "2019-2025": 0.20,
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
# 冻结调度规则
# ---------------------------------------------------------------------------
def active_coordinate_count(x: np.ndarray) -> int:
    """当前年度训练分片中至少一个样本取 1 的特征坐标数。

    只读取特征矩阵 `x`；不接触标签或测试分片。
    """
    return int(np.count_nonzero(np.any(x, axis=0)))


def adaptive_mask_rate(n_t: int) -> float:
    """研究问题卡 §四 的冻结规则：p_t = 0.20 * clip((n_t - 3000) / 500, 0, 1)。"""
    return float(P_MAX * np.clip((n_t - N_LOW) / N_SPAN, 0.0, 1.0))


def f1_from_scores(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> float:
    """与 `ch3.evaluate` 同一 TP/FP/FN 口径。"""
    pred = (y_score >= threshold).astype(int)
    tp = int(np.count_nonzero((pred == 1) & (y_true == 1)))
    fp = int(np.count_nonzero((pred == 1) & (y_true == 0)))
    fn = int(np.count_nonzero((pred == 0) & (y_true == 1)))
    denom = 2 * tp + fp + fn
    return float(2 * tp / denom) if denom else 0.0


# ---------------------------------------------------------------------------
# 单臂主循环（固定率先导 `run_arm` 的逐句镜像，唯一差别是 p 随年度变化）
# ---------------------------------------------------------------------------
def run_adapt() -> int:
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[arm] {ARM} device={device.type}", flush=True)

    years = list(ch3.DOMAIN_YEARS)
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in years:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    # 冻结调度：n_t 只用当前年度 train 特征矩阵
    n_by_year: dict[str, int] = {}
    p_by_year: dict[str, float] = {}
    for y in years:
        n_t = active_coordinate_count(store[y][0])
        p_t = adaptive_mask_rate(n_t)
        n_by_year[str(y)] = n_t
        p_by_year[str(y)] = p_t
        print(f"[adaptive] year={y} n_t={n_t} p_t={p_t:.6f}", flush=True)

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

    input_dim = int(store[years[0]][0].shape[1])

    # 与固定率臂完全相同的三个随机流；mask_rng 只创建一次
    rng = np.random.default_rng(ch3.SEED)
    buf_rng = np.random.default_rng(ch3.SEED)
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
        p_t = p_by_year[str(year)]
        t0 = time.time()
        train_info = fixed.train_epochs_with_feature_dropout(
            model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
            ch3.OFFICIAL_LR, device, rng, p_t, mask_rng, year,
        )
        epoch_records_by_year[str(year)] = train_info["epoch_records"]
        drop_vals = [r["dropout_measured"] for r in train_info["epoch_records"]]
        dropout_by_year[str(year)] = float(np.mean(drop_vals)) if drop_vals else 0.0
        print(
            f"[{year}] trained on {n_train:,} rows in {time.time() - t0:.1f}s "
            f"(n_t={n_by_year[str(year)]} p_t={p_t:.6f})",
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
                f1m = f1_from_scores(yt, sc, ch3.THRESHOLD)
                assert abs(f1m - float(rec["f1"])) < 1e-12, (
                    f"evaluate 与分数口径不一致 {ARM} {ty}: {rec['f1']} vs {f1m}"
                )
                print(
                    f"[preds] {ARM} 末年模型 @{ty}: f1={f1m:.4f} n={int(yt.size)} "
                    f"pos={int((yt == 1).sum())} nonfinite={preds[ty]['n_nonfinite']}",
                    flush=True,
                )

    final = max(years)
    last = [r for r in records if r["experience"] == final and r["mode"] == "backward"]
    per_year = {str(int(r["test_year"])): float(r["f1"]) for r in last}
    final_avg = float(np.mean([r["f1"] for r in last]))
    print(
        f"\n=== {ARM}：末年 {final} 的 avg_f1（官方报告口径）= {final_avg:.10f} ===",
        flush=True,
    )

    for ty, d in preds.items():
        np.savez_compressed(
            RUN_DIR / f"preds_{ARM}_{ty}.npz",
            y_true=d["y_true"],
            y_score=d["y_score"],
            threshold=np.float32(ch3.THRESHOLD),
        )

    all_epoch_records = [r for year in years for r in epoch_records_by_year[str(year)]]
    payload: dict[str, Any] = {
        "run_name": RUN_NAME,
        "arm": ARM,
        "status": "结果知情后的确认性检验，不是预注册假设",
        "ts": now_utc(),
        "public_protocol": PUBLIC_PROTOCOL,
        "adaptive_mask_protocol": ADAPTIVE_MASK_PROTOCOL,
        "wall_seconds": round(time.time() - t_start, 3),
        "final_experience": final,
        "per_year_active_coordinates": n_by_year,
        "per_year_mask_rate": p_by_year,
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
    write_json(RUN_DIR / f"{ARM}-result.json", payload)
    print(f"[done] {ARM} 用时 {payload['wall_seconds']:.1f}s", flush=True)

    write_comparison()
    return 0


# ---------------------------------------------------------------------------
# 与既有 base / drop20 的对照与研究问题卡 §五 判据
# ---------------------------------------------------------------------------
def load_reference_predictions(ref_arm: str) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """读取既有预测，返回 (y_true, y_score)，并核验 F1 与既有结果 JSON 一致。"""
    ref_json = json.loads((REF_RUN_DIR / f"{ref_arm}-result.json").read_text())
    ref_f1 = ref_json["per_year_f1_final_experience"]
    y_true: dict[str, np.ndarray] = {}
    y_score: dict[str, np.ndarray] = {}
    for y in ch3.DOMAIN_YEARS:
        key = str(y)
        path = REF_RUN_DIR / f"preds_{ref_arm}_{y}.npz"
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
        y_true[key] = yt
        y_score[key] = sc
    return y_true, y_score


def write_comparison() -> None:
    years = [str(y) for y in ch3.DOMAIN_YEARS]
    adapt_json = json.loads((RUN_DIR / f"{ARM}-result.json").read_text())
    adapt_f1 = adapt_json["per_year_f1_final_experience"]
    n_by_year = adapt_json["per_year_active_coordinates"]
    p_by_year = adapt_json["per_year_mask_rate"]

    refs: dict[str, dict[str, float]] = {}
    ref_true: dict[str, dict[str, np.ndarray]] = {}
    for ref_arm in REF_ARMS:
        yt_ref, sc_ref = load_reference_predictions(ref_arm)
        ref_true[ref_arm] = yt_ref
        refs[ref_arm] = {
            y: f1_from_scores(yt_ref[y], sc_ref[y], ch3.THRESHOLD) for y in years
        }

    # 顺序一致性：adapt 与 base 的 y_true 必须逐年度逐位相同
    for y in years:
        with np.load(RUN_DIR / f"preds_{ARM}_{y}.npz") as d:
            yt_adapt = d["y_true"]
            sc_adapt = d["y_score"]
            thr = float(d["threshold"])
        assert np.array_equal(yt_adapt, ref_true["base"][y]), (
            f"adapt 与 base 的 y_true 顺序不一致：{y}"
        )
        f1_adapt = f1_from_scores(yt_adapt, sc_adapt, thr)
        assert abs(f1_adapt - float(adapt_f1[y])) < 1e-9, (
            f"adapt npz 与结果 JSON 不一致 {y}: {f1_adapt} vs {adapt_f1[y]}"
        )

    per_year: dict[str, dict[str, float]] = {}
    for y in years:
        row: dict[str, float] = {
            "n_t": float(n_by_year[y]),
            "p_t": float(p_by_year[y]),
            "f1_adapt": float(adapt_f1[y]),
        }
        for ref_arm in REF_ARMS:
            row[f"f1_{ref_arm}"] = float(refs[ref_arm][y])
            row[f"delta_adapt_minus_{ref_arm}"] = float(adapt_f1[y]) - float(refs[ref_arm][y])
        per_year[y] = row

    mean_adapt = float(np.mean([adapt_f1[y] for y in years]))
    mean_ref = {a: float(np.mean([refs[a][y] for y in years])) for a in REF_ARMS}
    delta_base = mean_adapt - mean_ref["base"]
    delta_drop20 = mean_adapt - mean_ref["drop20"]

    crit_years = [str(y) for y in CRITERION_YEARS]
    positive_years = [y for y in crit_years if per_year[y]["delta_adapt_minus_base"] > 0]
    negative_years = [y for y in crit_years if per_year[y]["delta_adapt_minus_base"] < 0]

    delta_base_pp = delta_base * 100.0
    delta_drop20_pp = delta_drop20 * 100.0

    support = [
        {
            "id": "S1",
            "text": "adapt − base ≥ +0.50 pp（12 年平均）",
            "measured_pp": delta_base_pp,
            "threshold_pp": SUPPORT_MEAN_DELTA_PP,
            "passed": bool(delta_base_pp >= SUPPORT_MEAN_DELTA_PP),
        },
        {
            "id": "S2",
            "text": "adapt ≥ drop20 − 0.20 pp（12 年平均）",
            "measured_pp": delta_drop20_pp,
            "threshold_pp": SUPPORT_VS_DROP20_PP,
            "passed": bool(delta_drop20_pp >= SUPPORT_VS_DROP20_PP),
        },
        {
            "id": "S3",
            "text": "2018–2023 六个年度中 adapt − base 为正的年度数 ≥ 5",
            "measured_count": len(positive_years),
            "positive_years": positive_years,
            "threshold_count": SUPPORT_POSITIVE_YEARS,
            "passed": bool(len(positive_years) >= SUPPORT_POSITIVE_YEARS),
        },
    ]
    falsification = [
        {
            "id": "F1",
            "text": "adapt − base ≤ 0.00 pp（12 年平均）",
            "measured_pp": delta_base_pp,
            "threshold_pp": FALSIFY_MEAN_DELTA_PP,
            "passed": bool(delta_base_pp <= FALSIFY_MEAN_DELTA_PP),
        },
        {
            "id": "F2",
            "text": "adapt < drop20 − 0.30 pp（12 年平均）",
            "measured_pp": delta_drop20_pp,
            "threshold_pp": FALSIFY_VS_DROP20_PP,
            "passed": bool(delta_drop20_pp < FALSIFY_VS_DROP20_PP),
        },
        {
            "id": "F3",
            "text": "2018–2023 中 adapt − base 为负的年度数 ≥ 3",
            "measured_count": len(negative_years),
            "negative_years": negative_years,
            "threshold_count": FALSIFY_NEGATIVE_YEARS,
            "passed": bool(len(negative_years) >= FALSIFY_NEGATIVE_YEARS),
        },
    ]
    support_all = all(c["passed"] for c in support)
    falsified_any = any(c["passed"] for c in falsification)
    if support_all and not falsified_any:
        verdict = "支持 H2"
    elif falsified_any and not support_all:
        verdict = "证伪 H2"
    elif support_all and falsified_any:
        verdict = "判据冲突（支持与证伪同时触发，需人工裁决）"
    else:
        verdict = "未达支持阈值且未触发证伪（不确定）"

    payload: dict[str, Any] = {
        "run_name": RUN_NAME,
        "arm": ARM,
        "ts": now_utc(),
        "label": "结果知情后的确认性检验，不是预注册假设",
        "disclosure": (
            "H2 的调度规则与阈值是在看到 H1 固定率逐年结果之后提出的；本文件只作"
            "确认性检验，正文不得写成「预先注册的 adaptive 机制」。单训练种子 42，"
            "未做多种子训练；不做训练随机性下的稳健性主张。"
        ),
        "references": {
            "base": str(REF_RUN_DIR / "preds_base_{year}.npz"),
            "drop20": str(REF_RUN_DIR / "preds_drop20_{year}.npz"),
            "reference_run": "ch4-lamda-feature-dropout-pilot",
        },
        "public_protocol": PUBLIC_PROTOCOL,
        "adaptive_mask_protocol": ADAPTIVE_MASK_PROTOCOL,
        "per_year": per_year,
        "summary": {
            "mean_f1_adapt": mean_adapt,
            "mean_f1_base": mean_ref["base"],
            "mean_f1_drop20": mean_ref["drop20"],
            "delta_mean_adapt_minus_base": delta_base,
            "delta_mean_adapt_minus_drop20": delta_drop20,
            "delta_mean_adapt_minus_base_pp": delta_base_pp,
            "delta_mean_adapt_minus_drop20_pp": delta_drop20_pp,
            "criterion_years": list(CRITERION_YEARS),
            "positive_years_2018_2023_vs_base": positive_years,
            "negative_years_2018_2023_vs_base": negative_years,
        },
        "criteria": {
            "support": support,
            "falsification": falsification,
            "support_all_passed": support_all,
            "falsified_any_passed": falsified_any,
            "verdict": verdict,
        },
        "integrity_checks": {
            "adapt_y_true_equals_base_by_year": True,
            "adapt_npz_f1_equals_result_json": True,
            "reference_npz_f1_equals_reference_result_json": True,
            "mask_rng_independent_of_train_and_buffer_rng": True,
            "evaluation_and_scoring_never_masked": True,
        },
    }
    write_json(RUN_DIR / "adapt-comparison.json", payload)

    print("\n=== adapt vs base / drop20 ===", flush=True)
    for y in years:
        r = per_year[y]
        print(
            f"{y}: n_t={int(r['n_t'])} p_t={r['p_t']:.6f} "
            f"f1_adapt={r['f1_adapt']:.6f} "
            f"d_base={r['delta_adapt_minus_base'] * 100:+.3f}pp "
            f"d_drop20={r['delta_adapt_minus_drop20'] * 100:+.3f}pp",
            flush=True,
        )
    print(
        f"12-year mean: adapt={mean_adapt:.10f} base={mean_ref['base']:.10f} "
        f"drop20={mean_ref['drop20']:.10f}",
        flush=True,
    )
    print(
        f"12-year mean delta: vs base={delta_base_pp:+.4f}pp vs drop20={delta_drop20_pp:+.4f}pp",
        flush=True,
    )
    print("判据：", flush=True)
    for c in support + falsification:
        print(f"  {c['id']} {'PASS' if c['passed'] else 'FAIL'} — {c['text']}", flush=True)
    print(f"结论：{verdict}", flush=True)
    print(f"[comparison] 已写出 {RUN_DIR / 'adapt-comparison.json'}", flush=True)


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    ch3.DATA_ROOT = resolve_data_root()   # 覆盖被导入模块的数据根，不写死绝对路径
    return run_adapt()


if __name__ == "__main__":
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    _log_fh = (RUN_DIR / f"{ARM}.log").open("a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_fh)
    sys.stderr = _Tee(sys.__stderr__, _log_fh)
    try:
        raise SystemExit(main())
    finally:
        _log_fh.flush()
