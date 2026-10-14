#!/usr/bin/env python
"""E5：官方 Replay 蓄水池的**构成审计**（零训练，秒级）。

## 为什么要做

E4 实测出 `Naive 0.7244 → Replay 0.7805 → Joint 0.8791`，**`Replay → Joint` 缺口 `9.86` 点**。
其中一个待验证假设：

> 缺口的一部分不是来自「200 个样本太少」，而是来自**均匀抽样把正例率崩塌的年份稀释掉了**。

依据：官方蓄水池是**均匀抽样**（`domain_il_experiment.py:75-78`，`j = int(RNG.integers(0, n_seen))`），
按各年样本量成比例分配槽位；而 LAMDA 的正例率从 2013 的 `51.35%` 崩到 2024 的 `1.64%`。
若成立，2024 的正例在 200 槽位里的期望数应接近 0。

**本脚本只复刻官方抽样并清点构成，不训练任何模型。**

## 判据（跑前冻结）

| 观察 | 裁定 |
| --- | --- |
| 缓冲区内 2023/2024 的**正例槽位数 ≲ 1** | 假设**成立** ⇒ 值得做「按年/按类配额」的对照臂 |
| 缓冲区内这两年的正例槽位数 ≳ 5 | 假设**作废** ⇒ 缺口另有来源，不做配额臂 |

## 口径

- 逐字复刻官方 `ReplayBuffer.add_batch`：年序 `DOMAIN_YEARS`、年内按 parquet 行序、
  `RNG = np.random.default_rng(42)` 在**模块级**初始化（官方第 16 行）。
- 只投影 `label` 列——**不读任何 `feat_*`**。
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics/ch3-lamda-e5-replay-buffer-audit-v1"
DATA_ROOT = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/"
    "thesis/experiments/llm_probe/runs/data-raw/"
    "lamda-iclr2026-baseline-ad9614bdd5556767"
)
DOMAIN_YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
CAPACITY = 200
OFFICIAL_RNG_SEED = 42


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def year_labels(year: int) -> np.ndarray:
    path = DATA_ROOT / f"Baseline/{year}/{year}_train.parquet"
    return pq.read_table(path, columns=["label"]).column("label").to_numpy(zero_copy_only=False)


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(OFFICIAL_RNG_SEED)  # 官方模块级初始化，第 16 行

    slots_year: list[int] = []
    slots_label: list[int] = []
    n_seen = 0
    per_year_stats = {}

    for year in DOMAIN_YEARS:
        y = year_labels(year)
        per_year_stats[year] = {"train_n": int(y.size), "train_pos": int((y == 1).sum()),
                                "train_pos_rate": float((y == 1).mean())}
        for yi in y:  # 年内按 parquet 行序，逐样本（官方也是逐样本 for 循环）
            n_seen += 1
            if len(slots_year) < CAPACITY:
                slots_year.append(year)
                slots_label.append(int(yi))
            else:
                j = int(rng.integers(0, n_seen))
                if j < CAPACITY:
                    slots_year[j] = year
                    slots_label[j] = int(yi)
        print(f"[{year}] seen={n_seen:,}", flush=True)

    comp = Counter(slots_year)
    pos_comp = Counter(y for y, l in zip(slots_year, slots_label) if l == 1)
    total_pos = sum(pos_comp.values())

    print("\n=== 官方 200 槽位蓄水池的**实际**构成 ===")
    print(" 年份  槽位  其中正例   该年训练正例率   槽位占比")
    for year in DOMAIN_YEARS:
        st = per_year_stats[year]
        print(f" {year}  {comp.get(year,0):4d}  {pos_comp.get(year,0):6d}      "
              f"{st['train_pos_rate']*100:6.2f}%        {comp.get(year,0)/CAPACITY*100:5.1f}%")
    print(f" 合计  {sum(comp.values()):4d}  {total_pos:6d}")

    tail = (pos_comp.get(2023, 0), pos_comp.get(2024, 0))
    verdict = ("假设成立 ⇒ 做配额臂" if max(tail) <= 1 else
               "假设作废 ⇒ 缺口另有来源" if min(tail) >= 5 else "边界情形，需人工判读")
    print(f"\n判据（跑前冻结）：2023/2024 正例槽位 = {tail[0]}/{tail[1]} ⇒ **{verdict}**")

    write_json(RUN_DIR / "buffer_composition.json", {
        "ts": now_utc(), "capacity": CAPACITY, "rng_seed": OFFICIAL_RNG_SEED,
        "slots_by_year": {str(k): int(v) for k, v in comp.items()},
        "positive_slots_by_year": {str(k): int(v) for k, v in pos_comp.items()},
        "total_positive_slots": int(total_pos),
        "per_year_train_stats": {str(k): v for k, v in per_year_stats.items()},
        "frozen_criterion": "2023/2024 正例槽位 <=1 ⇒ 假设成立；>=5 ⇒ 作废",
        "frozen_verdict": verdict,
        "note": "官方 ReplayBuffer 逐字复刻（均匀蓄水池，种子 42，模块级 RNG）",
    })
    print(f"\n[done] {RUN_DIR}/buffer_composition.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
