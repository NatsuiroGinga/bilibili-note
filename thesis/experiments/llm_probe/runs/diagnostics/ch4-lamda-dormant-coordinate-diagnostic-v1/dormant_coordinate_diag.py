#!/usr/bin/env python
"""第四章材料性诊断：休眠特征坐标的冷启动。

只读、零训练。对每个年度训练分片计算：
- 活跃坐标集合（至少一个样本取 1 的特征）
- 相邻年度 Jaccard
- 冷坐标：本年活跃、但在此前任何年度训练分片中从未活跃
- 含冷坐标的样本占比与冷坐标数分布
- 冷坐标与标签的经验关联

产物：dormant-coordinate-diagnostic.json
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
DATA_ROOT = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/"
    "thesis/experiments/llm_probe/runs/data-raw/"
    "lamda-iclr2026-baseline-ad9614bdd5556767"
)
OUT_DIR = Path(__file__).resolve().parent
OUT_PATH = OUT_DIR / "dormant-coordinate-diagnostic.json"
MAX_LABEL_TEST_COORDS = 2000


def load_year(year: int) -> tuple[list[str], np.ndarray, np.ndarray]:
    path = DATA_ROOT / f"Baseline/{year}/{year}_train.parquet"
    table = pq.read_table(path)
    feat_cols = [c for c in table.column_names if c.startswith("feat_")]
    x = np.empty((table.num_rows, len(feat_cols)), dtype=np.int8)
    for i, col in enumerate(feat_cols):
        x[:, i] = table.column(col).to_numpy(zero_copy_only=False)
    y = table.column("label").to_numpy(zero_copy_only=False).astype(np.float32)
    del table
    return feat_cols, x, y


def rate(mask: np.ndarray, pos: np.ndarray) -> float | None:
    if not bool(mask.any()):
        return None
    return float(pos[mask].mean())


def main() -> int:
    ever_active: np.ndarray | None = None
    prev_active: np.ndarray | None = None
    rows: list[dict] = []

    for index, year in enumerate(YEARS):
        t0 = time.time()
        feat_cols, x, y = load_year(year)
        pos = y > 0.5
        active = np.any(x != 0, axis=0)

        if ever_active is None:
            ever_active = np.zeros_like(active)
            prev_active = np.zeros_like(active)

        cold = active & ~ever_active
        new_vs_prev = active & ~prev_active
        intersection = int(np.count_nonzero(active & prev_active))
        union = int(np.count_nonzero(active | prev_active))

        cold_idx = np.flatnonzero(cold)
        if cold_idx.size:
            cold_counts = np.count_nonzero(x[:, cold_idx], axis=1)
        else:
            cold_counts = np.zeros(x.shape[0], dtype=np.int64)
        has_cold = cold_counts > 0

        label_diffs: list[float] = []
        for j in cold_idx[:MAX_LABEL_TEST_COORDS]:
            col = x[:, j] != 0
            n_on = int(np.count_nonzero(col))
            n_off = int(col.size - n_on)
            if n_on < 10 or n_off < 10:
                continue
            label_diffs.append(float(pos[col].mean() - pos[~col].mean()))

        rows.append(
            {
                "year": year,
                "order_index": index,
                "rows": int(x.shape[0]),
                "positive_rate": float(pos.mean()),
                "active_coords": int(np.count_nonzero(active)),
                "prev_active_coords": int(np.count_nonzero(prev_active)),
                "intersection_with_prev": intersection,
                "union_with_prev": union,
                "jaccard_with_prev": (intersection / union) if union else None,
                "cold_coords": int(cold_idx.size),
                "cold_fraction_of_active": float(cold_idx.size / max(1, np.count_nonzero(active))),
                "new_vs_prev_coords": int(np.count_nonzero(new_vs_prev)),
                "new_vs_prev_fraction_of_active": float(
                    np.count_nonzero(new_vs_prev) / max(1, np.count_nonzero(active))
                ),
                "samples_with_cold": int(np.count_nonzero(has_cold)),
                "samples_with_cold_fraction": float(has_cold.mean()),
                "cold_count_mean_among_has": (
                    float(cold_counts[has_cold].mean()) if bool(has_cold.any()) else 0.0
                ),
                "cold_count_median_among_has": (
                    float(np.median(cold_counts[has_cold])) if bool(has_cold.any()) else 0.0
                ),
                "cold_count_max": int(cold_counts.max()) if cold_counts.size else 0,
                "pos_rate_with_cold": rate(has_cold, pos),
                "pos_rate_without_cold": rate(~has_cold, pos),
                "cold_coord_label_diff_tested": len(label_diffs),
                "cold_coord_label_diff_mean": (
                    float(np.mean(label_diffs)) if label_diffs else None
                ),
                "cold_coord_label_diff_max": (
                    float(np.max(label_diffs)) if label_diffs else None
                ),
                "cold_coord_label_diff_min": (
                    float(np.min(label_diffs)) if label_diffs else None
                ),
                "elapsed_seconds": round(time.time() - t0, 3),
            }
        )

        ever_active |= active
        prev_active = active
        del x, y
        print(
            f"{year}: active={rows[-1]['active_coords']} cold={rows[-1]['cold_coords']} "
            f"samples_with_cold={rows[-1]['samples_with_cold_fraction']:.4f} "
            f"({rows[-1]['elapsed_seconds']}s)",
            flush=True,
        )

    payload = {
        "schema_version": "ch4-dormant-coordinate-diagnostic-v1",
        "kind": "zero_training_data_side_diagnostic",
        "data_revision": "ad9614bdd5556767f97ced2fce797c2f06408ebf",
        "data_root": str(DATA_ROOT),
        "split": "train",
        "years": YEARS,
        "definitions": {
            "active_coord": "本年训练分片中至少一个样本该特征取 1",
            "cold_coord": "本年活跃，且在此前任何年度训练分片中从未活跃",
            "new_vs_prev_coord": "本年活跃，且上一年度训练分片不活跃",
            "jaccard_with_prev": "相邻年度活跃坐标集合的交集 / 并集",
        },
        "notes": [
            "第一年（2013）的全部活跃坐标按定义均为 cold，不单独解释。",
            "冷坐标只说明该坐标此前没有训练梯度历史；其权重是否仍近似初始化，需模型侧诊断确认。",
            "本诊断不读取测试分片，不使用任何模型分数。",
        ],
        "max_label_test_coords": MAX_LABEL_TEST_COORDS,
        "years_detail": rows,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"written: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
