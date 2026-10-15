"""第四章候选（先验/标签转移）的零训练判别诊断。

问题：候选 II 的一致性定理依赖 p(x|y) 跨年度不变、只有 p(y) 变。
本脚本直接测这个前提，**不训练任何模型**。

判据（跑前冻结，写在本文件内）：
  对每个年度 Y 与标签 y，计算逐特征 Bernoulli 均值向量 mu[Y,y] ∈ [0,1]^4561。
  - 跨年距离 D_cross(y) = mean over year pairs |mu[Y,y] - mu[Y',y]| 的均值（L1/维数）
  - 同年零假设 D_null(y) = 同一年内把该标签样本随机对半切开，两半均值向量之差（重复 R 次取均值）
  **若 D_cross ≈ D_null（比值 ≤ 2），p(x|y) 在该标签上可视为跨年稳定 ⇒ 标签转移假设成立。**
  **若 D_cross >> D_null，p(x|y) 本身在漂移 ⇒ 标签转移假设不成立，候选 II 须重写或放弃。**

控制：同一年内对半切提供"采样噪声尺度"；这正是缺少它就无法判读的地方。

运行（本机唯一实验环境）：
  LAMDA_DATA_ROOT=... /opt/miniconda3/envs/rwkv/bin/python prior_shift_diag.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
NULL_REPEATS = 8
RNG_SEED = 42


def data_root() -> Path:
    v = os.environ.get("LAMDA_DATA_ROOT")
    if not v:
        sys.exit("LAMDA_DATA_ROOT 未设置；不得回退到硬编码路径")
    p = Path(v)
    if not p.is_dir():
        sys.exit(f"LAMDA_DATA_ROOT 不存在: {p}")
    return p


def load_year(root: Path, year: int, split: str) -> tuple[np.ndarray, np.ndarray]:
    path = root / f"Baseline/{year}/{year}_{split}.parquet"
    table = pq.read_table(path)
    feat_cols = [c for c in table.column_names if c.startswith("feat_")]
    n = table.num_rows
    x = np.empty((n, len(feat_cols)), dtype=np.int8)
    for i, c in enumerate(feat_cols):
        x[:, i] = table.column(c).to_numpy(zero_copy_only=False)
    y = table.column("label").to_numpy(zero_copy_only=False).astype(np.int8)
    del table
    return x, y


def main() -> None:
    root = data_root()
    rng = np.random.default_rng(RNG_SEED)
    out_dir = Path(__file__).resolve().parent

    means: dict[str, dict[str, list[float]]] = {}   # year -> label -> mu
    nulls: dict[str, list[float]] = {"0": [], "1": []}
    counts: dict[str, dict[str, int]] = {}

    for year in YEARS:
        t0 = time.time()
        x, y = load_year(root, year, "train")
        entry: dict[str, list[float]] = {}
        cnt: dict[str, int] = {}
        for lab in (0, 1):
            idx = np.flatnonzero(y == lab)
            cnt[str(lab)] = int(idx.size)
            if idx.size == 0:
                continue
            # int64 求和后除以条数：避免 float32 上采样的显存/内存放大
            mu = x[idx].sum(axis=0, dtype=np.int64) / float(idx.size)
            entry[str(lab)] = mu.tolist()
            # 同年零假设：随机对半切，重复 NULL_REPEATS 次
            if idx.size >= 20:
                d_acc = 0.0
                for _ in range(NULL_REPEATS):
                    perm = rng.permutation(idx.size)
                    half = idx.size // 2
                    ia = idx[perm[:half]]
                    ib = idx[perm[half:2 * half]]
                    a = x[ia].sum(axis=0, dtype=np.int64) / float(half)
                    b = x[ib].sum(axis=0, dtype=np.int64) / float(half)
                    d_acc += float(np.abs(a - b).mean())
                nulls[str(lab)].append(d_acc / NULL_REPEATS)
        means[str(year)] = entry
        counts[str(year)] = cnt
        del x, y
        print(f"[{year}] pos={cnt.get('1', 0)} neg={cnt.get('0', 0)} "
              f"wall={time.time() - t0:.1f}s", flush=True)

    # 跨年距离：同标签、不同年度之间的均值向量 L1/维数
    report: dict[str, object] = {
        "years": YEARS,
        "null_repeats": NULL_REPEATS,
        "counts": counts,
        "per_label": {},
    }
    for lab in ("0", "1"):
        vecs = [(yr, np.asarray(means[str(yr)][lab], dtype=np.float64))
                for yr in YEARS if lab in means[str(yr)]]
        pairs = []
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                d = float(np.abs(vecs[i][1] - vecs[j][1]).mean())
                pairs.append({"a": vecs[i][0], "b": vecs[j][0], "d": d})
        d_cross = float(np.mean([p["d"] for p in pairs]))
        d_null = float(np.mean(nulls[lab]))
        report["per_label"][lab] = {
            "n_years": len(vecs),
            "d_cross_mean": d_cross,
            "d_null_mean": d_null,
            "ratio": (d_cross / d_null) if d_null > 0 else None,
            "pairs": sorted(pairs, key=lambda p: -p["d"])[:8],
            "d_cross_min": float(min(p["d"] for p in pairs)) if pairs else None,
            "d_cross_max": float(max(p["d"] for p in pairs)) if pairs else None,
        }

    out = out_dir / "prior_shift_diag.json"
    tmp = out.with_suffix(".json.partial")
    tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, out)

    print("\n=== 判读 ===")
    for lab, name in (("0", "良性"), ("1", "恶意")):
        r = report["per_label"][lab]
        print(f"{name} p(x|y={lab}): 跨年 {r['d_cross_mean']:.5f} | "
              f"同年零假设 {r['d_null_mean']:.5f} | 比值 {r['ratio']:.2f}")
    print(f"\n写出 {out}")


if __name__ == "__main__":
    main()
