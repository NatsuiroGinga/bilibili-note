#!/usr/bin/env python
"""第四章 E2：排序门控主动获取先导（RGA 侧，单一冻结种子 42）。

判据与配置来源（**逐条照抄，不得改动**）：
- `.Codex/docs/2026-10-15-第四章E2/implementation_plan.md`
- 上位判据冻结处 `thesis/methods/第四章-RGA-DBA研究问题卡.md` §4.2

## 主线（复现门）

按 `ch3_lamda_domain_il_e4.py::main()` 的年度循环**逐句镜像**（不改原脚本、不 shell 出去调它）：
`strategy=expreplay`、`buffer-scheme=quota`、`reuse-scheme=deficit`、`buffer-repeat=2`、
容量 `200`、`10` 轮、批 `1024`、`lr=0.01`、`seed=42`、阈值 `0.5`。
期望末年 `2025` 的 12 年平均 F1 == `0.8170`（与 `full_expreplay_m200_quota_deficit_r2_diag.log` 末行一致）。

## 侧支（不回流主线）

在分叉年度 $Y\\in\\{2016,2017,2018,2024\\}$ 的 $Y-1$ 边界上，深拷贝模型与缓冲；用 $Y-1$ 模型
给 $D_Y^{train}$ 打分；对 $\\Lambda\\in\\{200,800\\}$ 分别取 **top-$\\Lambda$**（active）、
**均匀随机 $\\Lambda$ 条**（passive）与 **$|\\text{score}-0.5|$ 升序前 $\\Lambda$ 条**（uncertainty），
同条数、同预算、同训练配置，与主线缓冲**合并**训练 10 轮；另有 `buffer_only`
（零标注，只用缓冲）。每臂在 $D_Y^{test}$ 上评价并保存逐样本 `y_true`/`y_score`，
供离线配对 bootstrap（$n=2000$）。$\\Lambda$ 每档共 3 条策略臂，四年合计 $4\\times(3\\times2+1)=28$ 臂。

**uncertainty 臂（2026-10-15 预注册增补）**：主动学习的标准基线不是随机而是**不确定采样**，
只与随机比较的结论会被审稿以「未对比标准主动学习基线」打掉。故 `active` 的对照除 `passive`
外还须含 `uncertainty`，报告须同时给出 $F_1^{active}-F_1^{uncertainty}$；若该差不为正，
须明说「主动获取相对不确定采样无优势」。**主判据仍为 $\\Delta F_1=F_1^{active}-F_1^{passive}$，不变。**

## 数据根

`DATA_ROOT` **必须**从环境变量 `LAMDA_DATA_ROOT` 解析；未设置或不存在即报错退出，
**不在本脚本写死绝对路径**。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_rank_gated_acquisition_e2.py --main-only   # 只跑主线复现门
    $PY thesis/experiments/llm_probe/tools/ch4_lamda_rank_gated_acquisition_e2.py              # 主线 ＋ 侧支

## 实现说明（规格未规定、由本脚本确定并登记，**非科研数值改动**）

1. **侧支在主循环结束后执行**（用分叉点快照），以保证侧支**不消耗主线任何随机源**，
   主线逐位复现 `0.8170`。快照取自主线处理 $Y$ 时、训练 $Y$ **之前**的模型与缓冲
   （即 $Y-1$ 结束态），与计划「主线跑完 $Y-1$ 后深拷贝」语义一致。
2. passive 抽样用 `np.random.default_rng(SEED + Y*1000 + Λ)`（**计划指定**）。
3. 侧支**每臂**训练的洗牌 RNG 与 torch dropout 种子由 `arm_key` 派生（计划未规定，
   只要求确定性可复现）：`arm_key = Y*100000 + kind_id*1000 + Λ`，
   `kind_id`：`0=active`、`1=passive`、`2=buffer_only`、`3=uncertainty`。
4. 侧支的**缓冲部分沿用主线同一构成**（`reuse_by_deficit(blocks, 2)` 的逐年重复），
   使「当前年数据」成为主线与侧支之间**唯一**变量。
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
import torch
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import ch3_lamda_domain_il_e4 as ch3  # noqa: E402  （只读导入；不改原脚本）

# ---------------------------------------------------------------------------
# 冻结配置（照 implementation_plan.md §1–§7，不得改动）
# ---------------------------------------------------------------------------
RUN_NAME = "ch4-lamda-rank-gated-acquisition-e2"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME

FORK_YEARS = [2016, 2017, 2018, 2024]   # {2016, 2017, 2018, 2024}；封印期 2019–2023 一次都不读
LAMBDA_GRID = [200, 800]                # Λ 网格
BUFFER_SCHEME = "quota"                 # 第三章冻结值
REUSE_SCHEME = "deficit"                # 第三章冻结值
BUFFER_REPEAT = 2                       # 第三章冻结值（deficit 的 m_max）
MEMORY = 200                            # 第三章冻结容量
POS_RATIO = 0.5                         # 第三章冻结值
BOOTSTRAP_N = 2000                      # 配对 bootstrap 重采样次数
BOOTSTRAP_SEED = 42                     # bootstrap 的确定性种子

CRITERIA_TEXT = (
    "主判据：ΔF1(s) = F1_active(s) − F1_passive(s) 随 α_s 的单调性。"
    "支持：ΔF1(2024) 显著为正，且大于 ΔF1(2017)，后者不小于 ΔF1(2016) 与 ΔF1(2018)"
    "（后两者预期落 |·|<0.5）。"
    "部分支持：仅 2024 显著为正。"
    "证伪：任一臂 ΔF1<0；或四年均不可分辨。"
    "强证伪：ΔF1(2024)≤0。"
    "不确定性：单一冻结种子 42（禁多种子）；配对 bootstrap(n=2000) 95% 区间，"
    "该区间只量化样本不确定性，不冒充训练随机性。"
)

DATA_ROOT_ENV = "LAMDA_DATA_ROOT"


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


def metrics_from_preds(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    """由逐样本判定计算全套指标（与 ch3.evaluate 的 sklearn 口径一致）。"""
    yt = y_true.astype(int)
    yp = y_pred.astype(int)
    tn, fp, fn, tp = confusion_matrix(yt, yp, labels=[0, 1]).ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    return {
        "accuracy": float(accuracy_score(yt, yp)),
        "precision": float(precision_score(yt, yp, zero_division=0)),
        "recall": float(recall_score(yt, yp, zero_division=0)),
        "f1": float(f1_score(yt, yp, zero_division=0)),
        "fpr": fpr,
        "fnr": fnr,
        "balanced_accuracy": float(balanced_accuracy_score(yt, yp)),
        "n": int(yt.size),
        "n_pos": int((yt == 1).sum()),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
    }


# ---------------------------------------------------------------------------
# 主线：逐句镜像 ch3.main() 的年度循环（expreplay + quota + deficit + repeat=2）
# ---------------------------------------------------------------------------
def run_mainline(capture_fork: bool) -> tuple[list[dict], dict[int, dict], dict[int, dict], float]:
    """返回 (records, snapshots, full_preds, final_avg_f1)。

    snapshots[Y]  = {"model": deepcopy, "blocks": deepcopy, "reps": dict}（Y-1 结束态）
    full_preds[Y] = {"y_true": ..., "y_score": ...}（主线全标注臂在 D_Y^test 上的逐样本预测）
    """
    torch.manual_seed(ch3.SEED)
    np.random.seed(ch3.SEED)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"[device] {device.type}", flush=True)
    rng = np.random.default_rng(ch3.SEED)
    # 配额缓冲用**独立** RNG：不扰动 train_epochs 的洗牌流（与 ch3.main 一致）
    buf_rng = np.random.default_rng(ch3.SEED)

    years = ch3.DOMAIN_YEARS
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for y in ch3.DOMAIN_YEARS:
        store[y] = ch3.load_year(y, "train")
        print(f"[load] {y} train={store[y][0].shape}", flush=True)

    model = None
    records: list[dict] = []
    snapshots: dict[int, dict] = {}
    full_preds: dict[int, dict] = {}
    t_start = time.time()

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        if model is None:
            model = ch3.ChenEncoderMLP(x_curr.shape[1]).to(device)
            n_params = sum(p.numel() for p in model.parameters())
            print(f"[model] params={n_params:,}", flush=True)

        # ---- parts 构造（expreplay + 非 reservoir + deficit 分支，逐句镜像）----
        blocks: list[tuple[int, np.ndarray, np.ndarray]] = []
        reps: dict[int, int] = {}
        if idx == 0:
            parts = [(x_curr, y_curr)]
        else:
            blocks = ch3.split_by_year(store, years[:idx], MEMORY, buf_rng, BUFFER_SCHEME, POS_RATIO)
            if not blocks:
                parts = [(x_curr, y_curr)]
            else:
                for yr, _, yb in blocks:
                    nb = int(yb.size)
                    pb = int((yb == 1).sum())
                    src = store[yr][1]
                    ns, psrc = int(src.size), int((src == 1).sum())
                    print(f"[audit] 截至{year} 缓冲块 {yr}: {nb}槽 正例{pb} 负例{nb - pb} "
                          f"| 源 {psrc}/{ns} = {psrc / max(ns, 1):.4f}", flush=True)
            if not blocks:
                pass
            elif REUSE_SCHEME == "deficit":
                reps = ch3.reuse_by_deficit(blocks, BUFFER_REPEAT, 1.0)
                parts = [(x_curr, y_curr)]
                for yr, X, y in blocks:
                    parts += [(X.astype(np.int8), y.astype(np.float32))] * reps[yr]
            else:  # pragma: no cover - 本实验固定 deficit
                raise ValueError(REUSE_SCHEME)

        # ---- 分叉点快照（训练 Y 之前 = Y-1 结束态）----
        if capture_fork and year in FORK_YEARS:
            snapshots[year] = {
                "model": copy.deepcopy(model),
                "blocks": copy.deepcopy(blocks),
                "reps": dict(reps),
            }

        n_train = int(sum(p[0].shape[0] for p in parts))
        t0 = time.time()
        ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                         ch3.OFFICIAL_LR, device, rng)
        print(f"[{year}] trained on {n_train:,} rows in {time.time() - t0:.1f}s", flush=True)

        # ---- 评价（backward + forward，逐句镜像）----
        for ty in years[: idx + 1]:
            xt, yt = ch3.load_year(ty, "test")
            m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, device)
            records.append({"experience": year, "test_year": ty, "mode": "backward", **m})
            if capture_fork and ty == year and year in FORK_YEARS:
                # 主线全标注臂在 D_Y^test 上的逐样本预测（只读；eval 前向不消耗 torch RNG）
                sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, device)
                full_preds[year] = {"y_true": yt.astype(np.int8), "y_score": sc}
        for ty in years[idx + 1:]:
            xt, yt = ch3.load_year(ty, "test")
            m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, device)
            records.append({"experience": year, "test_year": ty, "mode": "forward", **m})

        back = [r for r in records if r["experience"] == year and r["mode"] == "backward"]
        print(f"[{year}] avg_f1 backward={np.mean([r['f1'] for r in back]):.4f}", flush=True)

    final = max(years)
    last = [r for r in records if r["experience"] == final and r["mode"] == "backward"]
    final_avg_f1 = float(np.mean([r["f1"] for r in last]))
    print(f"\n=== expreplay：末年 {final} 的 avg_f1（官方报告口径）= {final_avg_f1:.4f} ===", flush=True)
    print(f"[mainline] wall={time.time() - t_start:.1f}s records={len(records)}", flush=True)
    return records, snapshots, full_preds, final_avg_f1


# ---------------------------------------------------------------------------
# 侧支：active / passive / buffer_only
# ---------------------------------------------------------------------------
def arm_key(year: int, kind_id: int, lam: int) -> int:
    """侧支每臂的确定性键（实现说明 3）。kind_id: 0=active, 1=passive, 2=buffer_only。"""
    return year * 100000 + kind_id * 1000 + lam


def build_parts(sub_x: np.ndarray | None, sub_y: np.ndarray | None,
                blocks: list[tuple[int, np.ndarray, np.ndarray]],
                reps: dict[int, int]) -> list[tuple[np.ndarray, np.ndarray]]:
    """当前年子集（可空）＋ 主线缓冲（沿用主线同一构成），与主线 parts 结构一致。"""
    parts: list[tuple[np.ndarray, np.ndarray]] = []
    if sub_x is not None and sub_x.shape[0] > 0:
        parts.append((sub_x.astype(np.int8), sub_y.astype(np.float32)))
    for yr, X, y in blocks:
        parts += [(X.astype(np.int8), y.astype(np.float32))] * reps[yr]
    return parts


def paired_bootstrap(y_true: np.ndarray, score_active: np.ndarray, score_passive: np.ndarray,
                     n_boot: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    """配对 bootstrap：对同一年度测试分片的逐样本判定重采样，给 ΔF1 的 95% 区间。

    **该区间只量化样本不确定性，不冒充训练随机性。**
    """
    n = int(y_true.size)
    rng = np.random.default_rng(seed)
    pa = (score_active >= ch3.THRESHOLD).astype(int)
    pp = (score_passive >= ch3.THRESHOLD).astype(int)
    yt = y_true.astype(int)
    diffs = np.empty(n_boot, dtype=np.float64)
    obs_a = float(f1_score(yt, pa, zero_division=0))
    obs_p = float(f1_score(yt, pp, zero_division=0))
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        fa = f1_score(yt[idx], pa[idx], zero_division=0)
        fp = f1_score(yt[idx], pp[idx], zero_division=0)
        diffs[i] = float(fa) - float(fp)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "observed_delta_f1": obs_a - obs_p,
        "mean_delta_f1": float(diffs.mean()),
        "ci95_low": float(lo),
        "ci95_high": float(hi),
        "n_boot": int(n_boot),
        "n_test": n,
        "note": "该区间只量化样本不确定性，不冒充训练随机性",
    }


def run_side(snapshots: dict[int, dict]) -> tuple[dict, dict, dict]:
    """返回 (arms, deltas, bootstraps)。arms[year][arm_name] = 指标 dict。"""
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    arms: dict[str, dict] = {}
    deltas: dict[str, dict] = {}
    bootstraps: dict[str, dict] = {}

    for year in FORK_YEARS:
        snap = snapshots[year]
        x_tr, y_tr = ch3.load_year(year, "train")
        x_te, y_te = ch3.load_year(year, "test")
        print(f"\n[side] === 分叉年度 {year}：train={x_tr.shape} 正例{int((y_tr == 1).sum())} | "
              f"test={x_te.shape} 正例{int((y_te == 1).sum())} ===", flush=True)

        # 用 Y-1 模型给 D_Y^train 逐样本打分（样本外；只读，不消耗外部随机源）
        scores = ch3.score_shard(snap["model"], x_tr, ch3.OFFICIAL_BATCH, device)
        order = np.argsort(-scores, kind="stable")                       # 分数降序；stable 保证并列时按原序
        order_unc = np.argsort(np.abs(scores - ch3.THRESHOLD), kind="stable")  # |score-0.5| 升序（最不确定优先）

        arm_metrics: dict[str, dict] = {}
        preds_store: dict[str, dict] = {}

        for lam in LAMBDA_GRID:
            # ---- active：top-Λ ----
            idx_a = order[:lam]
            # ---- passive：均匀随机 Λ 条（计划指定 RNG）----
            rng_p = np.random.default_rng(ch3.SEED + year * 1000 + lam)
            idx_p = rng_p.choice(x_tr.shape[0], size=lam, replace=False)
            # ---- uncertainty：决策边界最近的 Λ 条 ----
            idx_u = order_unc[:lam]

            for kind_id, name, idx in ((0, f"active_L{lam}", idx_a),
                                       (1, f"passive_L{lam}", idx_p),
                                       (3, f"uncertainty_L{lam}", idx_u)):
                acquired_pos = int((y_tr[idx] == 1).sum())
                parts = build_parts(x_tr[idx], y_tr[idx], snap["blocks"], snap["reps"])
                model = copy.deepcopy(snap["model"])
                torch.manual_seed(ch3.SEED + arm_key(year, kind_id, lam))
                train_rng = np.random.default_rng(ch3.SEED + arm_key(year, kind_id, lam))
                t0 = time.time()
                ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                                 ch3.OFFICIAL_LR, device, train_rng)
                m = ch3.evaluate(model, x_te, y_te, ch3.OFFICIAL_BATCH, device)
                sc = ch3.score_shard(model, x_te, ch3.OFFICIAL_BATCH, device)
                pred = (sc >= ch3.THRESHOLD).astype(int)
                mm = metrics_from_preds(y_te, pred)
                _assert_metric_parity(name, year, m, mm)
                mm["acquired_pos"] = acquired_pos
                mm["n_acquired"] = int(lam)
                mm["n_train_rows"] = int(sum(p[0].shape[0] for p in parts))
                mm["wall_s"] = round(time.time() - t0, 1)
                arm_metrics[name] = mm
                preds_store[name] = {"y_true": y_te.astype(np.int8), "y_score": sc}
                print(f"[side] {year} {name}: f1={mm['f1']:.4f} P={mm['precision']:.4f} "
                      f"R={mm['recall']:.4f} FPR={mm['fpr']:.4f} FNR={mm['fnr']:.4f} "
                      f"BA={mm['balanced_accuracy']:.4f} 取得正例={acquired_pos}/{lam} "
                      f"({mm['wall_s']}s)", flush=True)

        # ---- buffer_only：零标注，只用主线缓冲 ----
        parts = build_parts(None, None, snap["blocks"], snap["reps"])
        model = copy.deepcopy(snap["model"])
        torch.manual_seed(ch3.SEED + arm_key(year, 2, 0))
        train_rng = np.random.default_rng(ch3.SEED + arm_key(year, 2, 0))
        t0 = time.time()
        ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                         ch3.OFFICIAL_LR, device, train_rng)
        m = ch3.evaluate(model, x_te, y_te, ch3.OFFICIAL_BATCH, device)
        sc = ch3.score_shard(model, x_te, ch3.OFFICIAL_BATCH, device)
        pred = (sc >= ch3.THRESHOLD).astype(int)
        mm = metrics_from_preds(y_te, pred)
        _assert_metric_parity("buffer_only", year, m, mm)
        mm["acquired_pos"] = 0
        mm["n_acquired"] = 0
        mm["n_train_rows"] = int(sum(p[0].shape[0] for p in parts))
        mm["wall_s"] = round(time.time() - t0, 1)
        arm_metrics["buffer_only"] = mm
        preds_store["buffer_only"] = {"y_true": y_te.astype(np.int8), "y_score": sc}
        print(f"[side] {year} buffer_only: f1={mm['f1']:.4f} P={mm['precision']:.4f} "
              f"R={mm['recall']:.4f} FPR={mm['fpr']:.4f} FNR={mm['fnr']:.4f} "
              f"BA={mm['balanced_accuracy']:.4f} 取得正例=0 ({mm['wall_s']}s)", flush=True)

        # ---- 保存逐样本预测（供离线核对）----
        for name, d in preds_store.items():
            np.savez_compressed(RUN_DIR / f"preds_{year}_{name}.npz",
                                y_true=d["y_true"], y_score=d["y_score"],
                                threshold=np.float32(ch3.THRESHOLD))
        # ---- ΔF1 与配对 bootstrap（主判据 active−passive；同时报 active−uncertainty）----
        deltas[str(year)] = {}
        bootstraps[str(year)] = {}
        for lam in LAMBDA_GRID:
            a_name, p_name = f"active_L{lam}", f"passive_L{lam}"
            u_name = f"uncertainty_L{lam}"
            fa, fp_ = arm_metrics[a_name]["f1"], arm_metrics[p_name]["f1"]
            fu = arm_metrics[u_name]["f1"]
            deltas[str(year)][f"L{lam}"] = {
                "active_minus_passive": fa - fp_,
                "active_minus_uncertainty": fa - fu,
                "uncertainty_minus_passive": fu - fp_,
            }
            bootstraps[str(year)][f"L{lam}"] = {
                "active_minus_passive": paired_bootstrap(
                    preds_store[a_name]["y_true"], preds_store[a_name]["y_score"],
                    preds_store[p_name]["y_score"]),
                "active_minus_uncertainty": paired_bootstrap(
                    preds_store[a_name]["y_true"], preds_store[a_name]["y_score"],
                    preds_store[u_name]["y_score"]),
            }
            b_ap = bootstraps[str(year)][f"L{lam}"]["active_minus_passive"]
            b_au = bootstraps[str(year)][f"L{lam}"]["active_minus_uncertainty"]
            print(f"[side] {year} ΔF1 active−passive(L{lam}) = {fa - fp_:+.4f} "
                  f"95%=[{b_ap['ci95_low']:+.4f}, {b_ap['ci95_high']:+.4f}] | "
                  f"active−uncertainty = {fa - fu:+.4f} "
                  f"95%=[{b_au['ci95_low']:+.4f}, {b_au['ci95_high']:+.4f}]", flush=True)

        arms[str(year)] = arm_metrics

    return arms, deltas, bootstraps


def _assert_metric_parity(name: str, year: int, ev: dict, mm: dict) -> None:
    """核对 evaluate() 与本脚本手工口径的一致性（四条主指标）。"""
    for k in ("f1", "precision", "recall", "accuracy"):
        if abs(float(ev[k]) - float(mm[k])) > 1e-12:
            raise AssertionError(
                f"指标口径不一致 {year}.{name}.{k}: evaluate={ev[k]} manual={mm[k]}")


# ---------------------------------------------------------------------------
def main(main_only: bool) -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    # 运行前写出冻结判据与配置（计划 §3）
    protocol = {
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "criteria_text": CRITERIA_TEXT,
        "mainline": {
            "strategy": "expreplay", "buffer_scheme": BUFFER_SCHEME,
            "reuse_scheme": REUSE_SCHEME, "buffer_repeat": BUFFER_REPEAT,
            "memory": MEMORY, "epochs": ch3.OFFICIAL_EPOCHS, "batch": ch3.OFFICIAL_BATCH,
            "lr": ch3.OFFICIAL_LR, "seed": ch3.SEED, "threshold": ch3.THRESHOLD,
            "domain_years": list(ch3.DOMAIN_YEARS),
        },
        "side": {
            "fork_years": FORK_YEARS, "lambda_grid": LAMBDA_GRID,
            "arms": ["active", "passive", "uncertainty", "buffer_only"],
            "arms_per_lambda": 3,
            "total_arm_instances": len(FORK_YEARS) * (3 * len(LAMBDA_GRID) + 1),
            "arm_definition": {
                "active": "用 Y-1 模型给 D_Y^train 打分，取 top-Λ（分数降序），与主线缓冲合并训练 10 轮",
                "passive": "从 D_Y^train 均匀随机抽 Λ 条（rng=default_rng(SEED+Y*1000+Λ)），"
                           "与主线缓冲合并训练 10 轮",
                "uncertainty": "用 Y-1 模型给 D_Y^train 打分，取 |score-0.5| 升序前 Λ 条"
                               "（决策边界最近、模型最不确定的样本），与主线缓冲合并训练 10 轮",
                "buffer_only": "零标注，只用主线缓冲训练 10 轮",
                "full": "主线全标注臂（引用主线读数，不重跑）",
            },
            "primary_contrast": "active − passive（主判据，不变）",
            "secondary_contrast_required": "active − uncertainty（必须同时报；若不为正须明说"
                                           "「主动获取相对不确定采样无优势」，不得隐去）",
            "uncertainty_arm_rationale": (
                "2026-10-15 预注册增补（出结果前）：主动学习的标准基线不是随机而是不确定采样；"
                "只与随机比较的结论会被审稿以「未对比标准主动学习基线」打掉。故 active 的对照除 "
                "passive 外还须含 uncertainty。三种策略在正例率 1.64% 的年份里预期差异显著："
                "active 走高置信正例、uncertainty 走决策边界。"
            ),
            "buffer_composition": "沿用主线同一构成 reuse_by_deficit(blocks, 2) 的逐年重复",
            "bootstrap_n": BOOTSTRAP_N, "bootstrap_seed": BOOTSTRAP_SEED,
            "sealed_years_untouched": [2019, 2020, 2021, 2022, 2023],
        },
        "data_root": str(ch3.DATA_ROOT),
        "env_data_root_var": DATA_ROOT_ENV,
    }
    write_json(RUN_DIR / "e2_protocol.json", protocol)
    print(f"[protocol] 已写出 {RUN_DIR / 'e2_protocol.json'}", flush=True)

    t_all = time.time()
    records, snapshots, full_preds, final_f1 = run_mainline(capture_fork=not main_only)

    result: dict[str, Any] = {
        "run_name": RUN_NAME, "ts": now_utc(), "main_only": main_only,
        "mainline": {
            "final_year": max(ch3.DOMAIN_YEARS),
            "avg_f1_backward": final_f1,
            "gate_expected": 0.8170,
        },
    }
    if main_only:
        print(f"[gate] 主线复现门：末年 {max(ch3.DOMAIN_YEARS)} 的 12 年平均 F1 = {final_f1:.4f}"
              f"（期望 0.8170）", flush=True)
        result["mainline"]["records"] = records
        write_json(RUN_DIR / "e2_results.json", result)
        print(f"[done] --main-only 用时 {time.time() - t_all:.1f}s", flush=True)
        return 0

    # ---- 侧支（主循环结束后执行，不扰动主线随机源）----
    arms, deltas, bootstraps = run_side(snapshots)

    # 主线全标注臂（full）读数：直接引用主线 backward 记录 ＋ 捕获的逐样本预测
    full_arm: dict[str, dict] = {}
    for year in FORK_YEARS:
        rec = [r for r in records if r["experience"] == year and r["test_year"] == year
               and r["mode"] == "backward"]
        if not rec:
            continue
        r0 = rec[0]
        entry = {
            "accuracy": r0["accuracy"], "precision": r0["precision"],
            "recall": r0["recall"], "f1": r0["f1"],
            "n": r0["n"], "n_pos": r0["n_pos"],
            "acquired_pos": int((full_preds[year]["y_true"] == 1).sum()),
            "n_acquired": r0["n"],
            "note": "主线全标注臂（引用主线读数，不重跑）",
        }
        if year in full_preds:
            fp = full_preds[year]
            mmm = metrics_from_preds(fp["y_true"], (fp["y_score"] >= ch3.THRESHOLD).astype(int))
            entry.update({"fpr": mmm["fpr"], "fnr": mmm["fnr"],
                          "balanced_accuracy": mmm["balanced_accuracy"]})
            np.savez_compressed(RUN_DIR / f"preds_{year}_full.npz",
                                y_true=fp["y_true"], y_score=fp["y_score"],
                                threshold=np.float32(ch3.THRESHOLD))
        full_arm[str(year)] = entry
        arms[str(year)]["full"] = entry

    result["arms"] = arms
    result["delta_f1_active_minus_passive"] = deltas
    result["paired_bootstrap"] = bootstraps
    result["mainline"]["records"] = records
    write_json(RUN_DIR / "e2_results.json", result)
    print(f"\n[done] 全量用时 {time.time() - t_all:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    ch3.DATA_ROOT = resolve_data_root()   # 覆盖被导入模块的 DATA_ROOT（不写死绝对路径）
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    _log_fh = (RUN_DIR / "full_e2.log").open("w", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, _log_fh)
    sys.stderr = _Tee(sys.__stderr__, _log_fh)
    p = argparse.ArgumentParser(description="第四章 E2：排序门控主动获取先导")
    p.add_argument("--main-only", action="store_true",
                   help="只跑主线年度流（复现门，期望末年 12 年平均 F1 == 0.8170），不跑侧支")
    a = p.parse_args()
    try:
        raise SystemExit(main(a.main_only))
    finally:
        _log_fh.flush()
