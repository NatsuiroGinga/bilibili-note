#!/usr/bin/env python
"""第五章系统统一入口：数据预算 × 成员引擎双开关，串行产出四格系统消融。

形态决定来源：`thesis/methods/第五章形态与实现计划.md`（2026-10-22）。
本脚本只做**组装与验收**，不引入新算法、不改变任何研究语义。

## 双开关（冻结）

| 开关 | 取值 | 语义 |
| --- | --- | --- |
| `--data-budget` | `naive` | 每年只用当年训练分片：`parts=[(x_curr, y_curr)]` |
| | `quota_deficit` | 第三章冻结回放：`build_parts`（限额 200、年度等额、年内正负各半、缺口加权复用 `m_max=2`） |
| `--member-engine` | `off` | 官方 `ChenEncoderMLP` 单模型 |
| | `tabm4` | 第四章 `TabMMLP(k=4)`：首层随机符号、成员 BCE 均值训练、成员概率均值评测 |

四格：`naive`（naive+off）、`replay`（quota_deficit+off）、
`naive_members`（naive+tabm4）、`full`（quota_deficit+tabm4）。

**复用策略（避免等价重写漂移）**：
- `quota_deficit` 直接导入 `ch4_lamda_training_process_2x2.build_parts`——它与
  `ch3.main` 的 `expreplay + quota + deficit + repeat=2` 分支逐句一致；
- `tabm4` 直接导入 `ch4_lamda_tabm_pilot.TabMMLP` 与 `train_epochs_tabm`——不镜像重写。

## 公共协议（逐位一致）

种子 42；`buf_rng=default_rng(42)`；SGD(lr=0.01, momentum=0.9, weight_decay=1e-6)；
batch 1024；10 epoch；优化器年度重建；阈值 0.5；12 年 backward 面板（末年 2025 的模型
对全部 12 个测试分片逐样本打分）＋每年 current_year 评价。

## 等价性检查（不符时如实报告，不改数）

- `replay` 应与 `ch3-lamda-domain-il-e4-replication-v1/
  metrics_expreplay_m200_quota_deficit_r2.json` 的 12y 读数 `0.8169830287163194` 一致；
- `full` 应与 `ch4-lamda-tabm-pilot/tabm4-result.json` 的 `0.832346367494066` 一致。
容差 `1e-6`（float 精度）；`full` 另做逐样本分数对照（参照 preds 只读）。

## 运行

    PY=/opt/miniconda3/envs/rwkv/bin/python
    export LAMDA_DATA_ROOT=<...>/runs/data-raw/lamda-iclr2026-baseline-ad9614bdd5556767
    $PY tools/ch5_system_runner.py --run-all
    # 单格：$PY tools/ch5_system_runner.py --data-budget quota_deficit --member-engine tabm4

产物目录：`runs/diagnostics/ch5-system/`（`{cell}-result.json`、`preds_{cell}_{year}.npz`、
`system-comparison.json`、`run-status.json`）。
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import threading
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
import ch4_lamda_tabm_pilot as tabm  # noqa: E402  （TabMMLP 与训练函数的事实源）
from ch4_lamda_training_process_2x2 import (  # noqa: E402  （quota_deficit 事实源）
    BUFFER_REPEAT as REPLAY_BUFFER_REPEAT,
    MEMORY as REPLAY_MEMORY,
    build_parts,
)

RUN_NAME = "ch5-system"
PROBE_ROOT = TOOLS_DIR.parent                      # thesis/experiments/llm_probe
RUN_DIR = PROBE_ROOT / "runs/diagnostics" / RUN_NAME
DATA_ROOT_ENV = "LAMDA_DATA_ROOT"

SEED = ch3.SEED
THRESHOLD = ch3.THRESHOLD
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# 四格与开关的映射（冻结；argparse 的 choices 防止事后加格）
CELLS: tuple[str, ...] = ("naive", "replay", "naive_members", "full")
CELL_SPEC: dict[str, dict[str, str]] = {
    "naive":         {"data_budget": "naive",        "member_engine": "off"},
    "replay":        {"data_budget": "quota_deficit", "member_engine": "off"},
    "naive_members": {"data_budget": "naive",        "member_engine": "tabm4"},
    "full":          {"data_budget": "quota_deficit", "member_engine": "tabm4"},
}

TABM_K = 4
MEMORY_SAMPLE_INTERVAL_S = 0.2

CH3_REFERENCE = (PROBE_ROOT / "runs/diagnostics/ch3-lamda-domain-il-e4-replication-v1"
                 / "metrics_expreplay_m200_quota_deficit_r2.json")
TABM_REFERENCE = (PROBE_ROOT / "runs/diagnostics/ch4-lamda-tabm-pilot/tabm4-result.json")
EQUIVALENCE_TOL = 1e-6

# 参照读数（用于打印与 comparison 的期望值；实际比较在运行时从制品读取）
EXPECTED = {
    "replay": {"source": str(CH3_REFERENCE.relative_to(PROBE_ROOT)),
               "mean_f1_12y": 0.8169830287163194},
    "full":   {"source": str(TABM_REFERENCE.relative_to(PROBE_ROOT)),
               "mean_f1_12y": 0.832346367494066},
}


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """原子写出：先写 `.partial`，再 `os.replace`（与既有脚本同型）。"""
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def write_npz(path: Path, **arrays: np.ndarray) -> None:
    tmp = path.with_name(path.name + ".partial")
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, **arrays)
    os.replace(tmp, path)


def resolve_data_root() -> Path:
    """数据根只从环境变量或仓库相对路径解析，不在本脚本写死本机绝对路径。"""
    raw = os.environ.get(DATA_ROOT_ENV)
    if raw:
        root = Path(raw)
        if not root.is_dir():
            raise SystemExit(f"ERROR: {DATA_ROOT_ENV} 指向的目录不存在：{root}")
        return root
    candidate = (PROBE_ROOT / "runs/data-raw"
                 / "lamda-iclr2026-baseline-ad9614bdd5556767")
    if candidate.is_dir():
        return candidate
    legacy = Path(ch3.DATA_ROOT)
    if legacy.is_dir():
        print(f"[data] 警告：未设置 {DATA_ROOT_ENV}，回退到被导入模块的 DATA_ROOT={legacy}",
              flush=True)
        return legacy
    raise SystemExit(
        f"ERROR: 未设置 {DATA_ROOT_ENV}，且仓库相对候选与既有 DATA_ROOT 均不存在。"
        f"请导出 {DATA_ROOT_ENV}=<repo>/thesis/experiments/llm_probe/runs/data-raw/"
        f"lamda-iclr2026-baseline-ad9614bdd5556767")


def update_run_status(status: str, completed: list[str], current: str | None,
                      data_load_seconds: float | None = None,
                      error: str | None = None) -> None:
    payload: dict[str, Any] = {
        "schema_version": "ch5-system-status-v1",
        "run_name": RUN_NAME,
        "status": status,
        "current_cell": current,
        "completed_cells": completed,
        "planned_cells": list(CELLS),
        "ts": now_utc(),
    }
    if data_load_seconds is not None:
        payload["data_load_seconds"] = round(data_load_seconds, 1)
    if error:
        payload["error"] = error
    write_json(RUN_DIR / "run-status.json", payload)


# ---------------------------------------------------------------------------
# MPS 采样峰值（torch 2.12：`current_allocated_memory`，无 `_bytes` 后缀）
# ---------------------------------------------------------------------------
class MpsMemorySampler:
    """后台线程按固定间隔采样 MPS 已分配内存，记录 cell 内峰值。

    `current_allocated_memory()` 是分配器当前在用字节数；峰值由多次采样近似。
    采样线程只读分配器计数，不改变任何训练随机源或数值路径。
    """

    def __init__(self, interval: float = MEMORY_SAMPLE_INTERVAL_S) -> None:
        self.interval = interval
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self.samples = 0
        self.peak_current = 0
        self.peak_driver = 0
        self.first_current: int | None = None

    def _sample(self) -> None:
        if DEVICE.type != "mps":
            return
        try:
            cur = int(torch.mps.current_allocated_memory())
            drv = int(torch.mps.driver_allocated_memory())
        except Exception:  # 采样失败只丢收据，不影响训练
            return
        with self._lock:
            if self.first_current is None:
                self.first_current = cur
            self.samples += 1
            self.peak_current = max(self.peak_current, cur)
            self.peak_driver = max(self.peak_driver, drv)

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            self._sample()

    def start(self) -> None:
        self._sample()
        if DEVICE.type == "mps":
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._sample()

    def receipt(self) -> dict[str, Any]:
        with self._lock:
            return {
                "device": DEVICE.type,
                "api": "torch.mps.current_allocated_memory",
                "sampling_interval_seconds": self.interval,
                "n_samples": self.samples,
                "baseline_current_allocated_memory_bytes": self.first_current,
                "peak_current_allocated_memory_bytes": self.peak_current,
                "peak_current_allocated_memory_mib": round(self.peak_current / (1024 ** 2), 1),
                "peak_driver_allocated_memory_bytes": self.peak_driver,
                "peak_driver_allocated_memory_mib": round(self.peak_driver / (1024 ** 2), 1),
                "note": "峰值由后台线程按间隔采样近似；current_allocated_memory 为分配器在用字节数。",
            }


# ---------------------------------------------------------------------------
# 参数量与配置断言
# ---------------------------------------------------------------------------
def expected_params(input_dim: int, member_engine: str) -> int:
    """按 `ChenEncoderMLP` / `TabMMLP(k=4)` 的结构逐层计算参数量（不构造模型、不耗随机源）。"""
    dims = ((input_dim, 512), (512, 384), (384, 256), (256, 128),
            (128, 100), (100, 100), (100, 1))
    base = sum(inp * out + out for inp, out in dims)
    if member_engine == "off":
        return base
    adapters = sum(TABM_K * (inp + 2 * out) for inp, out in dims)
    return base + adapters


def build_cell_parts(cell: str, store: dict[int, tuple[np.ndarray, np.ndarray]],
                     years: list[int], idx: int, x_curr: np.ndarray, y_curr: np.ndarray,
                     buf_rng: np.random.Generator
                     ) -> tuple[list[tuple[np.ndarray, np.ndarray]], dict[str, Any]]:
    """按 `data_budget` 开关构造当前年度的训练分片。"""
    data_budget = CELL_SPEC[cell]["data_budget"]
    if data_budget == "naive":
        return [(x_curr, y_curr)], {"blocks": [], "reps": {}}
    if data_budget == "quota_deficit":
        return build_parts(store, years, idx, x_curr, y_curr, buf_rng)
    raise ValueError(data_budget)


def assert_parts_contract(cell: str, idx: int, current_year: int, parts, meta,
                          x_curr: np.ndarray, y_curr: np.ndarray) -> dict[str, Any]:
    """机械核对当前格的数据预算语义；失败即该格读数不可解释。"""
    data_budget = CELL_SPEC[cell]["data_budget"]
    n_parts = len(parts)
    first_is_current = bool(parts[0][0] is x_curr and parts[0][1] is y_curr)
    checks: dict[str, Any] = {"n_parts": n_parts, "first_is_current": first_is_current}
    if data_budget == "naive":
        checks["naive_single_part"] = bool(n_parts == 1)
        checks["naive_rows_match_current"] = bool(
            parts[0][0].shape[0] == x_curr.shape[0] and parts[0][1] is y_curr)
    else:
        if idx == 0:
            checks["first_year_single_part"] = bool(n_parts == 1)
        else:
            reps = meta.get("reps", {})
            blocks = meta.get("blocks", [])
            checks["reps_keys_match_blocks"] = bool(
                set(reps) == {int(b[0]) for b in blocks})
            checks["parts_count_matches_reps"] = bool(
                n_parts == 1 + sum(int(v) for v in reps.values()))
            checks["reps_within_bounds"] = bool(
                all(1 <= int(v) <= REPLAY_BUFFER_REPEAT for v in reps.values()))
            per = REPLAY_MEMORY // idx  # build_parts 的年度等额配额
            checks["block_rows_within_quota"] = bool(
                all(0 < int(b[1].shape[0]) <= max(per, 1) for b in blocks))
            checks["blocks_before_current_year"] = bool(
                all(int(b[0]) < current_year for b in blocks))
    passed = all(bool(v) for v in checks.values())
    if not passed:
        raise RuntimeError(f"[{cell}] 配置断言失败：{json.dumps(checks, ensure_ascii=False)}")
    return checks


def assert_model_contract(cell: str, model, n_params: int, input_dim: int) -> dict[str, Any]:
    engine = CELL_SPEC[cell]["member_engine"]
    expected_class = "ChenEncoderMLP" if engine == "off" else "TabMMLP"
    member_k = 1 if engine == "off" else TABM_K
    expected_n = expected_params(input_dim, engine)
    checks = {
        "engine": engine,
        "class": type(model).__name__,
        "class_matches": type(model).__name__ == expected_class,
        "n_params": n_params,
        "expected_n_params": expected_n,
        "params_match": n_params == expected_n,
        "member_k": member_k,
        "member_k_matches": (getattr(model, "k", None) == member_k) if engine == "tabm4" else True,
    }
    if not all(bool(checks[k]) for k in ("class_matches", "params_match", "member_k_matches")):
        raise RuntimeError(f"[{cell}] 模型配置断言失败：{json.dumps(checks, ensure_ascii=False)}")
    return checks


# ---------------------------------------------------------------------------
# 评价与等价性
# ---------------------------------------------------------------------------
def f1_of(y: np.ndarray, score: np.ndarray) -> float:
    """与第四章 tabm 产物同一口径：阈值 0.5，F1=2TP/(2TP+FP+FN)。"""
    return tabm.f1_of(np.asarray(y), np.asarray(score))


def load_reference(cell: str) -> dict[str, Any] | None:
    if cell == "replay":
        data = json.loads(CH3_REFERENCE.read_text(encoding="utf-8"))
        last = [r for r in data["records"]
                if r["experience"] == 2025 and r["mode"] == "backward"]
        per_year = {str(int(r["test_year"])): float(r["f1"]) for r in last}
        return {
            "source": str(CH3_REFERENCE.relative_to(PROBE_ROOT)),
            "mean_f1_12y": float(np.mean([float(r["f1"]) for r in last])),
            "f1_2023": per_year["2023"],
            "f1_2024": per_year["2024"],
            "f1_2025": per_year["2025"],
            "backward_f1": per_year,
            "preds_dir": None,
            "preds_prefix": None,
        }
    if cell == "full":
        data = json.loads(TABM_REFERENCE.read_text(encoding="utf-8"))
        return {
            "source": str(TABM_REFERENCE.relative_to(PROBE_ROOT)),
            "mean_f1_12y": float(data["mean_f1"]),
            "f1_2023": float(data["f1_2023"]),
            "f1_2024": float(data["f1_2024"]),
            "f1_2025": float(data["backward_f1"]["2025"]),
            "backward_f1": {str(k): float(v) for k, v in data["backward_f1"].items()},
            "preds_dir": str(TABM_REFERENCE.parent.relative_to(PROBE_ROOT)),
            "preds_prefix": "preds_tabm4_",
        }
    return None


def equivalence_check(cell: str, panel: dict[str, Any], years: list[int]) -> dict[str, Any] | None:
    ref = load_reference(cell)
    if ref is None:
        return None
    keys = ("mean_f1_12y", "f1_2023", "f1_2024", "f1_2025")
    deltas = {k: float(panel[k]) - float(ref[k]) for k in keys}
    per_year_delta = {
        ty: float(panel["backward_f1"][ty]) - float(ref["backward_f1"][ty])
        for ty in panel["backward_f1"] if ty in ref["backward_f1"]
    }
    max_abs = max([abs(v) for v in deltas.values()] + [abs(v) for v in per_year_delta.values()])
    out: dict[str, Any] = {
        "reference_source": ref["source"],
        "tolerance": EQUIVALENCE_TOL,
        "reference": {k: ref[k] for k in keys} | {"backward_f1": ref["backward_f1"]},
        "runner": {k: panel[k] for k in keys} | {"backward_f1": panel["backward_f1"]},
        "deltas": deltas,
        "per_year_deltas": per_year_delta,
        "max_abs_delta": max_abs,
        "passed": bool(max_abs <= EQUIVALENCE_TOL),
    }
    if ref["preds_dir"] is not None:
        ref_dir = PROBE_ROOT / ref["preds_dir"]
        max_score_diff = 0.0
        y_true_equal = True
        missing: list[str] = []
        for ty in years:
            ref_path = ref_dir / f"{ref['preds_prefix']}{ty}.npz"
            our_path = RUN_DIR / f"preds_{cell}_{ty}.npz"
            if not ref_path.is_file() or not our_path.is_file():
                missing.append(str(ty))
                continue
            rz = np.load(ref_path)
            oz = np.load(our_path)
            if not np.array_equal(rz["y_true"], oz["y_true"]):
                y_true_equal = False
            d = np.abs(rz["y_score"].astype(np.float64) - oz["y_score"].astype(np.float64))
            if d.size:
                max_score_diff = max(max_score_diff, float(d.max()))
        out["preds_check"] = {
            "reference_dir": ref["preds_dir"],
            "missing_years": missing,
            "y_true_equal": bool(y_true_equal),
            "max_abs_score_diff": max_score_diff,
            "identical": bool(not missing and y_true_equal and max_score_diff == 0.0),
        }
    else:
        out["preds_check"] = None
    return out


# ---------------------------------------------------------------------------
# 单格运行
# ---------------------------------------------------------------------------
def run_cell(cell: str, store: dict[int, tuple[np.ndarray, np.ndarray]],
             years: list[int], input_dim: int) -> dict[str, Any]:
    spec = CELL_SPEC[cell]
    data_budget = spec["data_budget"]
    member_engine = spec["member_engine"]

    # 每格都从同一种子重新开始；模型构造必须是首个消耗全局 torch 随机源的动作
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    rng = np.random.default_rng(SEED)          # 训练洗牌流
    buf_rng = np.random.default_rng(SEED)      # 缓冲构造流（与 ch3 的 SEED 一致）

    print(f"[cell] {cell} start data_budget={data_budget} member_engine={member_engine} "
          f"device={DEVICE.type}", flush=True)
    print(f"[config] seed={SEED} epochs={ch3.OFFICIAL_EPOCHS} batch={ch3.OFFICIAL_BATCH} "
          f"lr={ch3.OFFICIAL_LR} momentum={ch3.OFFICIAL_MOMENTUM} "
          f"weight_decay={ch3.OFFICIAL_WEIGHT_DECAY} memory={ch3.OFFICIAL_MEMORY} "
          f"buffer_repeat=2 threshold={THRESHOLD}", flush=True)

    sampler = MpsMemorySampler()
    sampler.start()
    t_cell = time.time()

    if member_engine == "off":
        model = ch3.ChenEncoderMLP(input_dim).to(DEVICE)
        member_k = 1
    else:
        model = tabm.TabMMLP(input_dim, TABM_K).to(DEVICE)
        member_k = TABM_K
    n_params = int(sum(p.numel() for p in model.parameters()))
    model_checks = assert_model_contract(cell, model, n_params, input_dim)
    print(f"[model] cell={cell} class={type(model).__name__} params={n_params:,} "
          f"member_k={member_k} expected={model_checks['expected_n_params']:,}", flush=True)

    per_year: dict[str, dict[str, Any]] = {}
    current_year_f1: dict[str, float] = {}
    current_year_metrics: dict[str, dict[str, Any]] = {}

    for idx, year in enumerate(years):
        x_curr, y_curr = store[year]
        parts, meta = build_cell_parts(cell, store, years, idx, x_curr, y_curr, buf_rng)
        parts_checks = assert_parts_contract(cell, idx, year, parts, meta, x_curr, y_curr)

        rows = int(sum(int(p[0].shape[0]) for p in parts))
        pos = int(sum(int((p[1] == 1).sum()) for p in parts))
        blocks = [{"source_year": int(b[0]), "rows": int(b[1].shape[0]),
                   "pos": int((b[2] == 1).sum())} for b in meta.get("blocks", [])]
        reps = {str(int(k)): int(v) for k, v in meta.get("reps", {}).items()}
        print(f"[parts] {cell} {year}: n_parts={len(parts)} rows={rows:,} pos={pos:,} "
              f"pos_rate={pos / max(rows, 1):.4f}", flush=True)
        if blocks:
            print(f"[audit] {cell} {year}: blocks="
                  + ", ".join(f"{b['source_year']}({b['rows']}/{b['pos']})" for b in blocks)
                  + f" reps={reps}", flush=True)

        t_train = time.time()
        if member_engine == "off":
            ch3.train_epochs(model, parts, ch3.OFFICIAL_EPOCHS, ch3.OFFICIAL_BATCH,
                             ch3.OFFICIAL_LR, DEVICE, rng)
        else:
            tabm.train_epochs_tabm(model, parts, ch3.OFFICIAL_EPOCHS, DEVICE, rng,
                                   arm="tabm4", year=year)
        train_seconds = time.time() - t_train

        xt, yt = ch3.load_year(year, "test")
        t_eval = time.time()
        m = ch3.evaluate(model, xt, yt, ch3.OFFICIAL_BATCH, DEVICE)
        eval_seconds = time.time() - t_eval
        current_year_f1[str(year)] = float(m["f1"])
        current_year_metrics[str(year)] = m
        del xt, yt

        per_year[str(year)] = {
            "year": year,
            "parts_contract": parts_checks,
            "n_parts": len(parts),
            "rows": rows,
            "pos": pos,
            "pos_rate": pos / max(rows, 1),
            "blocks": blocks,
            "reps": reps,
            "train_seconds": round(train_seconds, 1),
            "eval_seconds": round(eval_seconds, 2),
            "current_year_f1": float(m["f1"]),
            "current_year_metrics": m,
        }
        print(f"[{cell}][{year}] current_f1={m['f1']:.4f} train={train_seconds:.1f}s "
              f"eval={eval_seconds:.1f}s", flush=True)

    # 末年模型对 12 个测试分片逐样本打分（backward 面板；参照脚本同口径）
    preds: dict[int, dict[str, np.ndarray]] = {}
    test_sizes: dict[str, dict[str, int]] = {}
    t_score = time.time()
    for ty in years:
        xt, yt = ch3.load_year(ty, "test")
        sc = ch3.score_shard(model, xt, ch3.OFFICIAL_BATCH, DEVICE).astype(np.float32)
        preds[ty] = {"y_true": yt.astype(np.int8), "y_score": sc}
        test_sizes[str(ty)] = {"n": int(yt.size), "n_pos": int((yt == 1).sum())}
        del xt, yt
    score_seconds = time.time() - t_score

    backward_f1 = {str(ty): f1_of(preds[ty]["y_true"], preds[ty]["y_score"])
                   for ty in years}
    mean_f1 = float(np.mean(list(backward_f1.values())))

    # 评测合同自检：current_year 与逐样本分数口径在末年必须一致
    last_year = str(years[-1])
    consistency_diff = abs(float(current_year_f1[last_year]) - backward_f1[last_year])
    consistency_passed = bool(consistency_diff < 1e-12)
    if not consistency_passed:
        raise RuntimeError(
            f"[{cell}] 评测口径不一致 @{last_year}: evaluate={current_year_f1[last_year]} "
            f"vs score_shard={backward_f1[last_year]}")

    for ty, d in preds.items():
        write_npz(RUN_DIR / f"preds_{cell}_{ty}.npz",
                  y_true=d["y_true"], y_score=d["y_score"],
                  threshold=np.float32(THRESHOLD))

    sampler.stop()
    wall_seconds = time.time() - t_cell
    panel = {
        "panel_definition": "末年 2025 的模型对全部 12 个年度测试分片逐样本打分（backward）",
        "mean_f1_12y": mean_f1,
        "f1_2023": backward_f1["2023"],
        "f1_2024": backward_f1["2024"],
        "f1_2025": backward_f1["2025"],
        "backward_f1": backward_f1,
        "current_year_f1": current_year_f1,
        "current_year_metrics": current_year_metrics,
        "test_sizes": test_sizes,
    }
    equivalence = equivalence_check(cell, panel, years)

    result: dict[str, Any] = {
        "schema_version": "ch5-system-cell-result-v1",
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "cell": cell,
        "config": {"data_budget": data_budget, "member_engine": member_engine},
        "protocol": {
            "domain_years": list(years),
            "seed": SEED,
            "buf_rng_seed": SEED,
            "epochs": ch3.OFFICIAL_EPOCHS,
            "batch": ch3.OFFICIAL_BATCH,
            "lr": ch3.OFFICIAL_LR,
            "momentum": ch3.OFFICIAL_MOMENTUM,
            "weight_decay": ch3.OFFICIAL_WEIGHT_DECAY,
            "memory": ch3.OFFICIAL_MEMORY,
            "buffer_scheme": "quota" if data_budget == "quota_deficit" else None,
            "reuse_scheme": "deficit" if data_budget == "quota_deficit" else None,
            "buffer_repeat": 2 if data_budget == "quota_deficit" else None,
            "pos_ratio": 0.5 if data_budget == "quota_deficit" else None,
            "deficit_gamma": 1.0 if data_budget == "quota_deficit" else None,
            "optimizer_type": "SGD",
            "optimizer_lifetime": "每年度在训练函数体内重建",
            "threshold": THRESHOLD,
            "device": DEVICE.type,
            "data_root": str(ch3.DATA_ROOT),
            "test_file_pattern": "Baseline/{year}/{year}_test.parquet",
            "current_year": "每个 experience 训练结束后立即评价当年测试分片",
            "backward_panel": "末年模型对 12 个年度测试分片打分",
            "score": ("单模型 sigmoid" if member_engine == "off"
                      else "成员 sigmoid 概率均值"),
        },
        "model": {
            "engine": member_engine,
            "class": type(model).__name__,
            "n_params": n_params,
            "member_k": member_k,
            "input_dim": input_dim,
            "contract": model_checks,
        },
        "per_year": per_year,
        "panel": panel,
        "equivalence": equivalence,
        "efficiency": {
            "wall_seconds_cell": round(wall_seconds, 1),
            "wall_seconds_scope": "cell 内（模型构造＋训练＋评价＋打分）；共享数据加载不计入",
            "score_seconds": round(score_seconds, 1),
            "mps_memory": sampler.receipt(),
        },
        "eval_consistency": {
            "year": years[-1],
            "evaluate_f1": current_year_f1[last_year],
            "score_shard_f1": backward_f1[last_year],
            "abs_diff": consistency_diff,
            "passed": consistency_passed,
        },
    }

    print(f"=== {cell}: 12y mean={mean_f1:.10f} | 2023={backward_f1['2023']:.6f} "
          f"2024={backward_f1['2024']:.6f} 2025={backward_f1['2025']:.6f} | "
          f"wall={wall_seconds:.0f}s peak_mps={sampler.receipt()['peak_current_allocated_memory_mib']}MiB ===",
          flush=True)
    if equivalence is not None:
        print(f"[equivalence] {cell}: max_abs_delta={equivalence['max_abs_delta']:.3e} "
              f"passed={equivalence['passed']} source={equivalence['reference_source']}",
              flush=True)
        if equivalence.get("preds_check"):
            pc = equivalence["preds_check"]
            print(f"[equivalence] {cell}: preds identical={pc['identical']} "
                  f"max_score_diff={pc['max_abs_score_diff']:.3e}", flush=True)

    write_json(RUN_DIR / f"{cell}-result.json", result)

    # 释放本格模型与 MPS 缓存；数据 store 由调用方共享
    del model
    gc.collect()
    if DEVICE.type == "mps":
        torch.mps.empty_cache()
    return result


# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------
def build_comparison(completed: list[str], data_load_seconds: float,
                     data_root: Path) -> dict[str, Any]:
    cells: dict[str, Any] = {}
    equivalence: dict[str, Any] = {}
    for cell in CELLS:
        path = RUN_DIR / f"{cell}-result.json"
        if not path.is_file():
            continue
        r = json.loads(path.read_text(encoding="utf-8"))
        cells[cell] = {
            "data_budget": r["config"]["data_budget"],
            "member_engine": r["config"]["member_engine"],
            "mean_f1_12y": r["panel"]["mean_f1_12y"],
            "f1_2023": r["panel"]["f1_2023"],
            "f1_2024": r["panel"]["f1_2024"],
            "f1_2025": r["panel"]["f1_2025"],
            "n_params": r["model"]["n_params"],
            "member_k": r["model"]["member_k"],
            "wall_seconds": r["efficiency"]["wall_seconds_cell"],
            "peak_mps_current_allocated_memory_mib":
                r["efficiency"]["mps_memory"]["peak_current_allocated_memory_mib"],
            "eval_consistency_passed": r["eval_consistency"]["passed"],
        }
        if r.get("equivalence") is not None:
            equivalence[cell] = r["equivalence"]
    return {
        "schema_version": "ch5-system-comparison-v1",
        "run_name": RUN_NAME,
        "ts": now_utc(),
        "cell_matrix": {c: dict(CELL_SPEC[c]) for c in CELLS},
        "protocol_summary": {
            "seed": SEED, "epochs": ch3.OFFICIAL_EPOCHS, "batch": ch3.OFFICIAL_BATCH,
            "optimizer": "SGD(0.01,0.9,1e-6)", "threshold": THRESHOLD,
            "panel": "final experience 2025 backward over 12 test years + per-year current_year",
            "device": DEVICE.type,
        },
        "data_root": str(data_root),
        "data_load_seconds_shared": round(data_load_seconds, 1),
        "cells": cells,
        "completed_cells": list(completed),
        "missing_cells": [c for c in CELLS if c not in cells],
        "equivalence_checks": equivalence,
        "expected_equivalence": {
            "replay": EXPECTED["replay"],
            "full": EXPECTED["full"],
            "tolerance": EQUIVALENCE_TOL,
            "note": "等价性不符时保留本 runner 读数并如实报告差异，不改动任何数字。",
        },
    }


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="第五章系统统一入口：数据预算 × 成员引擎双开关，四格系统消融")
    parser.add_argument("--data-budget", choices=("naive", "quota_deficit"),
                        help="数据预算开关：naive=只用当年；quota_deficit=第三章冻结回放")
    parser.add_argument("--member-engine", choices=("off", "tabm4"),
                        help="成员引擎开关：off=官方单模型；tabm4=TabMMLP(k=4)")
    parser.add_argument("--run-all", action="store_true",
                        help="按 naive → replay → naive_members → full 串行跑四格")
    args = parser.parse_args()

    if args.run_all:
        if args.data_budget or args.member_engine:
            parser.error("--run-all 不能与单个格开关同时使用")
        cells = list(CELLS)
    else:
        if not args.data_budget or not args.member_engine:
            parser.error("单格运行必须同时指定 --data-budget 与 --member-engine，或使用 --run-all")
        matches = [c for c, s in CELL_SPEC.items()
                   if s["data_budget"] == args.data_budget
                   and s["member_engine"] == args.member_engine]
        if len(matches) != 1:
            parser.error("开关组合不在四格之内")
        cells = matches

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    data_root = resolve_data_root()
    ch3.DATA_ROOT = data_root  # 覆盖被导入模块的数据根（不修改原脚本）
    print(f"[run] {RUN_NAME} cells={cells} device={DEVICE.type} data_root={data_root}",
          flush=True)

    update_run_status("running", completed=[], current=cells[0])
    t_load = time.time()
    store: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for year in ch3.DOMAIN_YEARS:
        t0 = time.time()
        store[year] = ch3.load_year(year, "train")
        print(f"[load] {year} train={store[year][0].shape} ({time.time() - t0:.1f}s)",
              flush=True)
    data_load_seconds = time.time() - t_load
    input_dim = int(store[ch3.DOMAIN_YEARS[0]][0].shape[1])
    print(f"[load] 全部年度完成：{data_load_seconds:.1f}s input_dim={input_dim}", flush=True)
    update_run_status("running", completed=[], current=cells[0],
                      data_load_seconds=data_load_seconds)

    completed: list[str] = []
    try:
        for cell in cells:
            update_run_status("running", completed=completed, current=cell,
                              data_load_seconds=data_load_seconds)
            run_cell(cell, store, list(ch3.DOMAIN_YEARS), input_dim)
            completed.append(cell)
            write_json(RUN_DIR / "system-comparison.json",
                       build_comparison(completed, data_load_seconds, data_root))
            update_run_status("running", completed=completed,
                              current=(cells[cells.index(cell) + 1]
                                       if cell != cells[-1] else None),
                              data_load_seconds=data_load_seconds)
    except Exception as exc:  # 保留状态与原始日志，退出码非零
        update_run_status("failed", completed=completed, current=None,
                          data_load_seconds=data_load_seconds, error=repr(exc))
        raise
    finally:
        del store
        gc.collect()
        if DEVICE.type == "mps":
            torch.mps.empty_cache()

    write_json(RUN_DIR / "system-comparison.json",
               build_comparison(completed, data_load_seconds, data_root))
    update_run_status("completed", completed=completed, current=None,
                      data_load_seconds=data_load_seconds)
    print(f"[done] {RUN_NAME} completed={completed} "
          f"artifacts={RUN_DIR}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
