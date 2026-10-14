#!/usr/bin/env python
"""E3：LAMDA 标签可靠性时间诊断（**最小证伪实验，不是机制实验**）。

## 这个实验要证伪什么

待验证假设（2026-10-14 主代理推论，尚未过证据门）：

> 「CITADEL / SEED / ADAPT / LFreeDA 都在优化『如何少要标签』，
>   但都默认**要来的标签本身可信**；而 LAMDA 的标签（VirusTotal `vt_detection >= 4`）
>   可能随年份退化。若成立，则『标签可靠性感知的训练』是一个未被占的机制。」

**本脚本只诊断标签自身，不训练任何模型、不用 feat_* 列、不用 GPU。**

## 判据（跑前冻结，2026-10-14，**不得按结果改**）

可观测信号（逐年）：
- `S1` = POS 中 `vt_count == 4` 的占比  —— 恰在阈值上的正例：**一票之差就翻标签**
- `S2` = POS 的 `vt_count` 中位数       —— 检测共识强度
- `S3` = NEG 中 `vt_count == 3` 的占比  —— 良性里最接近阈值的
- `S4` = 同年家族标签冲突率             —— 同一 family 同时出现两种 label

判决：
| 观察 | 裁定 |
| --- | --- |
| S1 随年份**上升** 或 S2 随年份**下降**（早期 vs 晚期有量级差异） | **标签可靠性存在时间退化** ⇒ 假设**未被证伪**，可进入机制设计 |
| S2 或 S4 与 E1 的跨年 AUROC/FNR **相关** | 该退化**可能影响训练** ⇒ 进一步支持 |
| 各年 S1/S2/S3/S4 **基本持平**（无时间趋势） | **否决**该机制——标签没有变得更不可信，无从修起 |

**注意**：`vt_count` 是 LAMDA 的**标签来源**。此处只把它当**标签质量的诊断量**，
**绝不作为训练特征**（作特征即标签泄漏，路线总控已冻结该边界）。

## 口径

- 单位：**整年样本**（该年 train + test 合并）——本实验诊断标签，不是评价模型。
- 视图：`Baseline`（冻结视图），只读。
- `family` 为空／缺失的样本在家族类指标中单列，不混入。

## 运行

    /opt/miniconda3/envs/rwkv/bin/python \
        thesis/experiments/llm_probe/tools/ch3_lamda_label_reliability_e3.py
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

RUN_NAME = "ch3-lamda-e3-label-reliability-v1"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME
DATA_ROOT = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/"
    "thesis/experiments/llm_probe/runs/data-raw/"
    "lamda-iclr2026-baseline-ad9614bdd5556767"
)
YEARS = tuple(y for y in range(2013, 2026) if y != 2015)
POS_THRESHOLD = 4  # LAMDA 的标签规则：vt_detection >= 4 ⇒ 恶意
COLUMNS = ("label", "vt_count", "family", "year_month")


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def year_arrays(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    labels, vts, families = [], [], []
    shard_rows = {}
    for split in ("train", "test"):
        path = DATA_ROOT / f"Baseline/{year}/{year}_{split}.parquet"
        if not path.is_file():
            raise FileNotFoundError(path)
        table = pq.read_table(path, columns=list(COLUMNS))
        shard_rows[split] = table.num_rows
        labels.append(table.column("label").to_numpy(zero_copy_only=False).astype(np.int8))
        vts.append(table.column("vt_count").to_numpy(zero_copy_only=False).astype(np.int32))
        families.append(np.array(table.column("family").to_pylist(), dtype=object))
        del table
    return (np.concatenate(labels), np.concatenate(vts), np.concatenate(families), shard_rows)


def diagnose(year: int) -> dict:
    y, vt, fam, shard_rows = year_arrays(year)
    pos = y == 1
    neg = ~pos
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    vt_pos, vt_neg = vt[pos], vt[neg]

    # --- S1 / S2：正例侧的阈值邻近与共识强度 ---
    s1 = float(np.count_nonzero(vt_pos == POS_THRESHOLD) / n_pos) if n_pos else None
    s2 = float(np.median(vt_pos)) if n_pos else None
    pos_p25 = float(np.percentile(vt_pos, 25)) if n_pos else None
    pos_p75 = float(np.percentile(vt_pos, 75)) if n_pos else None
    pos_frac_le5 = float(np.count_nonzero(vt_pos <= 5) / n_pos) if n_pos else None

    # --- S3：良性侧的阈值邻近 ---
    s3 = float(np.count_nonzero(vt_neg == POS_THRESHOLD - 1) / n_neg) if n_neg else None
    neg_frac_zero = float(np.count_nonzero(vt_neg == 0) / n_neg) if n_neg else None
    neg_vt_median = float(np.median(vt_neg)) if n_neg else None
    neg_vt_max = int(vt_neg.max()) if n_neg else None

    # --- S4：家族标签冲突 ---
    valid = np.array([f is not None and f != "" for f in fam])
    fam_v, y_v = fam[valid], y[valid]
    if fam_v.size:
        uniq, inv = np.unique(fam_v, return_inverse=True)
        # 每个家族的两种标签计数
        n_fam = uniq.size
        pos_cnt = np.bincount(inv, weights=(y_v == 1).astype(np.float64), minlength=n_fam)
        tot_cnt = np.bincount(inv, minlength=n_fam)
        conflicting = int(np.count_nonzero((pos_cnt > 0) & (pos_cnt < tot_cnt)))
        s4 = float(conflicting / n_fam) if n_fam else None
        # 家族出现次数分布
        appears_once = int(np.count_nonzero(tot_cnt == 1))
        singleton_mass = float(tot_cnt[tot_cnt == 1].sum() / fam_v.size)
        # 只出现在正例 / 只出现在负例 的家族占比
        pos_only = float(np.count_nonzero(pos_cnt == tot_cnt) / n_fam)
        neg_only = float(np.count_nonzero(pos_cnt == 0) / n_fam)
    else:
        n_fam = 0
        s4 = singleton_mass = pos_only = neg_only = None
        appears_once = 0

    return {
        "year": year,
        "shard_rows": shard_rows,
        "n": int(y.size), "n_pos": n_pos, "n_neg": n_neg,
        "pos_rate": float(n_pos / y.size),
        "S1_pos_frac_at_threshold": s1,
        "S2_pos_vt_median": s2,
        "pos_vt_p25": pos_p25, "pos_vt_p75": pos_p75,
        "pos_frac_vt_le5": pos_frac_le5,
        "S3_neg_frac_below_threshold": s3,
        "neg_vt_median": neg_vt_median, "neg_vt_max": neg_vt_max,
        "neg_frac_vt_zero": neg_frac_zero,
        "S4_family_conflict_rate": s4,
        "n_families": int(n_fam),
        "families_appearing_once": appears_once,
        "singleton_sample_mass": singleton_mass,
        "family_pos_only_frac": pos_only,
        "family_neg_only_frac": neg_only,
        "n_family_missing": int((~valid).sum()),
    }


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    status = RUN_DIR / "status.json"
    write_json(status, {"status": "running", "ts": now_utc()})
    t0 = time.time()
    rows = []
    for year in YEARS:
        r = diagnose(year)
        rows.append(r)
        print(
            f"[{year}] n={r['n']:>7} pos={r['n_pos']:>6} "
            f"S1(at4)={r['S1_pos_frac_at_threshold']:.4f} "
            f"S2(vt_med)={r['S2_pos_vt_median']:.1f} "
            f"S3(neg@3)={r['S3_neg_frac_below_threshold']:.4f} "
            f"S4(conflict)={r['S4_family_conflict_rate']:.4f} "
            f"singleton_mass={r['singleton_sample_mass']:.4f}",
            flush=True,
        )
    write_json(RUN_DIR / "metrics.json", {
        "run_name": RUN_NAME, "view": "Baseline", "pos_threshold": POS_THRESHOLD,
        "years": rows, "wall_seconds": time.time() - t0, "ts": now_utc(),
        "caveat": "vt_count 仅作标签质量诊断量，绝不作为训练特征（否则标签泄漏）",
    })
    write_json(status, {"status": "completed", "ts": now_utc()})
    print(f"\n[done] {RUN_DIR}/metrics.json  wall={time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
