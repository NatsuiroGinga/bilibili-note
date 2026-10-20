#!/usr/bin/env python
"""第四章材料性诊断（模型侧、零训练）：基线误差是否集中在冷坐标样本上。

只读现有基线逐样本预测 `preds_base_<year>.npz` 与年度 Parquet。
冷坐标定义：本年度训练分片首次激活、且此前任何年度训练分片从未激活
（即模型在进入本年度时没有任何梯度历史）。统计测试样本中落在这个集合上的活跃坐标数。
2013 年没有更早训练分片，单独标注。

产物：cold-error-stratification.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

YEARS = [2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
DATA_ROOT = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/"
    "thesis/experiments/llm_probe/runs/data-raw/"
    "lamda-iclr2026-baseline-ad9614bdd5556767"
)
PRED_DIR = Path(__file__).resolve().parents[1] / "ch4-lamda-training-process-2x2"
OUT_PATH = Path(__file__).resolve().parent / "cold-error-stratification.json"


def load_split(year: int, split: str) -> tuple[list[str], np.ndarray, np.ndarray]:
    path = DATA_ROOT / f"Baseline/{year}/{year}_{split}.parquet"
    table = pq.read_table(path)
    feat_cols = [c for c in table.column_names if c.startswith("feat_")]
    x = np.empty((table.num_rows, len(feat_cols)), dtype=np.int8)
    for i, col in enumerate(feat_cols):
        x[:, i] = table.column(col).to_numpy(zero_copy_only=False)
    y = table.column("label").to_numpy(zero_copy_only=False).astype(np.float32)
    del table
    return feat_cols, x, y


def f1(y: np.ndarray, pred: np.ndarray) -> float | None:
    tp = int(np.count_nonzero((pred == 1) & (y == 1)))
    fp = int(np.count_nonzero((pred == 1) & (y == 0)))
    fn = int(np.count_nonzero((pred == 0) & (y == 1)))
    if tp + fp + fn == 0:
        return None
    return 2 * tp / (2 * tp + fp + fn)


def confusion(y: np.ndarray, pred: np.ndarray) -> dict:
    return {
        "n": int(y.size),
        "pos": int(np.count_nonzero(y == 1)),
        "neg": int(np.count_nonzero(y == 0)),
        "tp": int(np.count_nonzero((pred == 1) & (y == 1))),
        "fp": int(np.count_nonzero((pred == 1) & (y == 0))),
        "fn": int(np.count_nonzero((pred == 0) & (y == 1))),
        "tn": int(np.count_nonzero((pred == 0) & (y == 0))),
    }


def rates(y: np.ndarray, pred: np.ndarray) -> dict:
    c = confusion(y, pred)
    return {
        **c,
        "f1": f1(y, pred),
        "error_rate": float(np.mean(pred != y)) if y.size else None,
        "fnr": (c["fn"] / c["pos"]) if c["pos"] else None,
        "fpr": (c["fp"] / c["neg"]) if c["neg"] else None,
    }


def main() -> int:
    ever_train = None
    rows: list[dict] = []

    for year in YEARS:
        feat_cols, xtr, _ = load_split(year, "train")
        active_train = np.any(xtr != 0, axis=0)
        del xtr
        if ever_train is None:
            ever_train = np.zeros_like(active_train)
        cold_year = active_train & ~ever_train
        ever_train |= active_train

        _, xte, yte = load_split(year, "test")
        pred_path = PRED_DIR / f"preds_base_{year}.npz"
        if not pred_path.is_file():
            print(f"{year}: missing {pred_path.name}", flush=True)
            del xte, yte
            continue
        z = np.load(pred_path, allow_pickle=True)
        y_true = z["y_true"].astype(np.float32)
        y_score = z["y_score"].astype(np.float32)
        threshold = float(z["threshold"])
        if y_true.size != yte.size or not np.array_equal(y_true, yte):
            print(
                f"{year}: prediction/label mismatch "
                f"({y_true.size} vs {yte.size}); skipped",
                flush=True,
            )
            del xte, yte
            continue

        active_test = np.any(xte != 0, axis=0)
        cold_idx = np.flatnonzero(cold_year)
        if cold_idx.size:
            cold_counts = np.count_nonzero(xte[:, cold_idx], axis=1)
        else:
            cold_counts = np.zeros(xte.shape[0], dtype=np.int64)
        has_cold = cold_counts > 0
        pred = (y_score >= threshold).astype(np.float32)

        overall = rates(yte, pred)
        with_cold = rates(yte[has_cold], pred[has_cold])
        without_cold = rates(yte[~has_cold], pred[~has_cold])

        bins = [
            ("0", cold_counts == 0),
            ("1", cold_counts == 1),
            ("2-3", (cold_counts >= 2) & (cold_counts <= 3)),
            ("4+", cold_counts >= 4),
        ]
        bin_rows = []
        for name, mask in bins:
            if bool(mask.any()):
                bin_rows.append({"cold_count": name, **rates(yte[mask], pred[mask])})

        errors = pred != yte
        rows.append(
            {
                "year": year,
                "row_match": True,
                "threshold": threshold,
                "active_train_coords": int(np.count_nonzero(active_train)),
                "active_test_coords": int(np.count_nonzero(active_test)),
                "cold_test_coords": int(cold_idx.size),
                "cold_share_of_test_active": float(
                    cold_idx.size / max(1, np.count_nonzero(active_test))
                ),
                "test_samples_with_cold": int(np.count_nonzero(has_cold)),
                "test_fraction_with_cold": float(has_cold.mean()),
                "cold_count_mean_among_has": (
                    float(cold_counts[has_cold].mean()) if bool(has_cold.any()) else 0.0
                ),
                "cold_count_max": int(cold_counts.max()) if cold_counts.size else 0,
                "overall": overall,
                "with_cold": with_cold,
                "without_cold": without_cold,
                "error_share_from_cold_samples": (
                    float(np.count_nonzero(errors & has_cold) / max(1, np.count_nonzero(errors)))
                    if bool(errors.any())
                    else None
                ),
                "error_rate_gap_cold_minus_rest": (
                    (with_cold["error_rate"] - without_cold["error_rate"])
                    if with_cold["error_rate"] is not None
                    and without_cold["error_rate"] is not None
                    else None
                ),
                "cold_count_bins": bin_rows,
            }
        )
        print(
            f"{year}: cold_coords={cold_idx.size} samples_with_cold={has_cold.mean():.3f} "
            f"F1={overall['f1']:.4f} F1_cold={with_cold['f1']} F1_no_cold={without_cold['f1']} "
            f"err_gap={rows[-1]['error_rate_gap_cold_minus_rest']}",
            flush=True,
        )
        del xte, yte

    payload = {
        "schema_version": "ch4-cold-error-stratification-v1",
        "kind": "zero_training_model_side_diagnostic",
        "prediction_source": str(PRED_DIR),
        "data_root": str(DATA_ROOT),
        "definitions": {
            "cold_coord_at_year_start": "本年度训练分片首次激活、且此前任何年度训练分片从未激活",
            "has_cold": "测试样本至少含一个年度起点冷坐标",
        },
        "notes": [
            "冷坐标样本与其余样本的差异是描述性分层，不构成因果归因。",
            "2013 年没有更早训练分片，其 cold 集合按定义等于全部训练活跃集合，不单独解释。",
            "本诊断只读取现有 base 臂逐样本预测，不重新训练。",
        ],
        "years_detail": rows,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"written: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
