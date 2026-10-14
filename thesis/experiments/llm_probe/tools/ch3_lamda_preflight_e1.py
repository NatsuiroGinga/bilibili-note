#!/usr/bin/env python3
"""E1：LAMDA 跨年阈值迁移诊断（screening_only，单种子 42，MPS）。

诊断问题：源期标定的误报预算阈值迁移到目标年时失效到什么程度，
该失效能否仅用「该年自校准阈值」修复（决策层问题），
还是自校准后 FNR 仍高（表示层退化）。

协议（与上游 anoshift_experiment_models_separate.py commit 7728bfa 逐字对齐）：
- 训练 = 2013_train ∪ 2014_train 中 year_month 不属于 {2013-12, 2014-08} 的行；
- IID 测试月只从 test 分片取；
- 目标年（2016--2025）评价面板 = 该年 train+test 分片合并
  （与计划 §2.1 参考读数口径一致：2020 正例 46,355 = 37,084+9,271 等）。
- A 组阈值在源期 test 分片全部良性行上标定（训练从未接触任何 test 行 ⇒ held-out）；
- B 组阈值用该年自身良性行标定（诊断口径，目标知情）。

发布 4561 维特征空间使用未来年份协变量，结果一律 screening_only。
2024/2025 正例枯竭（794/23），按路线总控 D1 裁决只作探索性披露。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import resource
import sys
import time
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import sklearn
import torch
from sklearn.metrics import average_precision_score, roc_auc_score
from torch import nn

# ---------------------------------------------------------------- 冻结配置

SEED = 42
EPOCHS = 6
BATCH_SIZE = 512
LEARNING_RATE = 0.001
SCORING_BATCH = 4096
EXPECTED_PARAM_COUNT = 594_753
EXPECTED_FEATURES = 4_561
SOURCE_YEARS = (2013, 2014)
TARGET_YEARS = tuple(range(2016, 2026))
IID_MONTHS = ("2013-12", "2014-08")
FP_BUDGETS = (0.001, 0.01)
DATA_MANIFEST_FIELDS = ("hash", "label", "family", "vt_count", "year_month")
OFFICIAL_CODE_REVISION = "7728bfafcd5539a286b5f8c47b6f1e3b2d1f4249"

# 与数据审计一致的期望行数；SHA256 通过后这些断言只在协议装配出错时触发
EXPECTED_TRAIN_ROWS = 137_869            # 69,144+80,946 - (7,545+4,676)
EXPECTED_SOURCE_CAL_BENIGN = 19_496      # (17,287-8,877)+(20,237-9,151)
EXPECTED_IID_TEST_ROWS = 3_065           # 1,944+1,121
EXPECTED_SHARD_ROWS = {
    (2013, "train"): 69_144, (2013, "test"): 17_287,
    (2014, "train"): 80_946, (2014, "test"): 20_237,
    (2016, "train"): 87_354, (2016, "test"): 21_839,
    (2017, "train"): 79_315, (2017, "test"): 19_829,
    (2018, "train"): 83_433, (2018, "test"): 20_859,
    (2019, "train"): 72_840, (2019, "test"): 18_210,
    (2020, "train"): 81_658, (2020, "test"): 20_415,
    (2021, "train"): 64_924, (2021, "test"): 16_231,
    (2022, "train"): 69_132, (2022, "test"): 17_284,
    (2023, "train"): 43_483, (2023, "test"): 10_871,
    (2024, "train"): 38_741, (2024, "test"): 9_686,
    (2025, "train"): 35_730, (2025, "test"): 8_933,
}

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_ROOT = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/"
    "thesis/experiments/llm_probe/runs/data-raw/"
    "lamda-iclr2026-baseline-ad9614bdd5556767"
)


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def append_progress(path: Path, payload: dict[str, Any]) -> None:
    line = json.dumps({"ts": now_utc(), **payload}, ensure_ascii=False)
    with path.open("a") as handle:
        handle.write(line + "\n")


def set_status(path: Path, state: str, **extra: Any) -> None:
    write_json(path, {"status": state, "ts": now_utc(), **extra})


def log(message: str) -> None:
    print(f"[{datetime.now(UTC).strftime('%H:%M:%S')}] {message}", flush=True)


# ---------------------------------------------------------------- 数据读取


def read_shard(path: Path, feature_names: list[str]) -> dict[str, np.ndarray]:
    table = pq.read_table(path, columns=["label", "year_month", *feature_names])
    n_rows = table.num_rows
    features = np.empty((n_rows, len(feature_names)), dtype=np.int8)
    for index, name in enumerate(feature_names):
        features[:, index] = table.column(name).to_numpy(zero_copy_only=False)
    labels = table.column("label").to_numpy(zero_copy_only=False).astype(np.int8)
    months = np.array(table.column("year_month").to_pylist(), dtype="U7")
    del table
    return {"X": features, "y": labels, "months": months, "path": path, "rows": n_rows}


def feature_names_from_schema(path: Path) -> list[str]:
    schema = pq.read_schema(path)
    names = [name for name in schema.names if name.startswith("feat_")]
    names.sort(key=lambda item: int(item.split("_")[1]))
    return names


def score_matrix(model: nn.Module, features: np.ndarray, device: torch.device) -> np.ndarray:
    model.eval()
    chunks: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, features.shape[0], SCORING_BATCH):
            batch = torch.from_numpy(features[start : start + SCORING_BATCH].astype(np.float32)).to(device)
            chunks.append(torch.sigmoid(model(batch)).cpu().numpy().astype(np.float64))
    return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float64)


# ---------------------------------------------------------------- 指标


def fpr_fnr(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, float]:
    pred = scores >= threshold
    benign = labels == 0
    malicious = labels == 1
    fp = int(np.count_nonzero(pred & benign))
    tn = int(np.count_nonzero(~pred & benign))
    fn = int(np.count_nonzero(~pred & malicious))
    tp = int(np.count_nonzero(pred & malicious))
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return {
        "threshold": float(threshold),
        "fpr": fpr, "fnr": fnr,
        "fp": fp, "tn": tn, "fn": fn, "tp": tp,
    }


def threshold_at_budget(benign_scores: np.ndarray, budget: float) -> float:
    return float(np.quantile(benign_scores, 1.0 - budget, method="linear"))


def ranking_metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, float | None]:
    unique = np.unique(labels)
    if unique.size < 2:
        return {"auroc": None, "average_precision": None}
    return {
        "auroc": float(roc_auc_score(labels, scores)),
        "average_precision": float(average_precision_score(labels, scores)),
    }


# ---------------------------------------------------------------- 模型（与 v3 先例一致）


class LamdaMLP(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        width = input_dim
        for next_width in (128, 64, 32):
            layers.extend([nn.Linear(width, next_width), nn.BatchNorm1d(next_width), nn.ReLU(), nn.Dropout(0.5)])
            width = next_width
        layers.append(nn.Linear(width, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x).squeeze(1)


# ---------------------------------------------------------------- 主流程


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "predictions").mkdir(exist_ok=True)
    status_path = out_dir / "status.json"
    progress_path = out_dir / "progress.jsonl"
    started = time.monotonic()

    set_status(status_path, "running", phase="init")

    code_path = Path(__file__).resolve()
    code_sha = sha256_file(code_path)

    # --- 数据身份核验（文件级 SHA256 对输入 manifest） ---
    input_manifest_path = DATA_ROOT / "manifest.json"
    input_manifest = json.loads(input_manifest_path.read_text())
    official_files = {entry["path"]: entry["official_sha256"] for entry in input_manifest["files"]}
    needed_paths = [f"Baseline/{y}/{y}_{shard}.parquet" for y in (*SOURCE_YEARS, *TARGET_YEARS) for shard in ("train", "test")]
    file_receipts: dict[str, dict[str, Any]] = {}
    for rel in needed_paths:
        local = DATA_ROOT / rel
        digest = sha256_file(local)
        matched = official_files.get(rel)
        file_receipts[rel] = {"sha256": digest, "matches_official_manifest": digest == matched}
        if digest != matched:
            set_status(status_path, "failed", phase="data_verify", reason=f"sha256 mismatch: {rel}")
            return 2
    log(f"data identity verified: {len(needed_paths)} shards match official manifest")

    # --- 环境与设备 ---
    if not torch.mps.is_available():
        set_status(status_path, "failed", phase="init", reason="MPS unavailable")
        return 2
    device = torch.device("mps")
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    # --- 读取源期分片 ---
    set_status(status_path, "running", phase="load_source")
    feature_names = feature_names_from_schema(DATA_ROOT / "Baseline/2013/2013_train.parquet")
    if len(feature_names) != EXPECTED_FEATURES:
        set_status(status_path, "failed", phase="load_source", reason=f"feature count {len(feature_names)}")
        return 2
    shards: dict[tuple[int, str], dict[str, np.ndarray]] = {}
    for year in SOURCE_YEARS:
        for shard in ("train", "test"):
            path = DATA_ROOT / f"Baseline/{year}/{year}_{shard}.parquet"
            shards[(year, shard)] = read_shard(path, feature_names)
            observed = shards[(year, shard)]["rows"]
            assert observed == EXPECTED_SHARD_ROWS[(year, shard)], f"{year}_{shard} rows {observed}"
            append_progress(progress_path, {"phase": "load_source", "shard": f"{year}_{shard}", "rows": observed})
            log(f"loaded {year}_{shard}: rows={observed} pos={int((shards[(year, shard)]['y'] == 1).sum())}")

    # --- 装配训练 / 标定 / IID 集合 ---
    iid_mask_source = np.zeros(0, dtype=bool)
    train_parts, source_test_parts = [], []
    for year in SOURCE_YEARS:
        train = shards[(year, "train")]
        test = shards[(year, "test")]
        not_iid = ~np.isin(train["months"], IID_MONTHS)
        train_parts.append((train["X"][not_iid], train["y"][not_iid]))
        source_test_parts.append((test["X"], test["y"], test["months"]))
        iid_mask = np.isin(test["months"], IID_MONTHS)
        iid_mask_source = iid_mask if iid_mask_source.size == 0 else np.concatenate([iid_mask_source, iid_mask])
    X_train = np.concatenate([part[0] for part in train_parts])
    y_train = np.concatenate([part[1] for part in train_parts])
    X_source_test = np.concatenate([part[0] for part in source_test_parts])
    y_source_test = np.concatenate([part[1] for part in source_test_parts])
    months_source_test = np.concatenate([part[2] for part in source_test_parts])
    assert X_train.shape[0] == EXPECTED_TRAIN_ROWS, f"train rows {X_train.shape[0]}"
    cal_mask = y_source_test == 0
    assert int(np.count_nonzero(cal_mask)) == EXPECTED_SOURCE_CAL_BENIGN, "calibration benign count"
    X_iid = X_source_test[iid_mask_source]
    y_iid = y_source_test[iid_mask_source]
    assert X_iid.shape[0] == EXPECTED_IID_TEST_ROWS, "iid rows"
    assert set(np.unique(y_train).tolist()).issubset({0, 1})
    log(f"train rows={X_train.shape[0]} pos={int((y_train == 1).sum())}; calibration benign={int(np.count_nonzero(cal_mask))}; iid rows={X_iid.shape[0]}")

    # --- 训练（MPS） ---
    set_status(status_path, "running", phase="train")
    model = LamdaMLP(EXPECTED_FEATURES)
    param_count = sum(p.numel() for p in model.parameters())
    assert param_count == EXPECTED_PARAM_COUNT, f"param count {param_count}"
    model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.BCEWithLogitsLoss()
    shuffle_rng = np.random.default_rng(SEED)
    n_train = X_train.shape[0]
    epoch_history = []
    iid_scores_last = None
    for epoch in range(1, EPOCHS + 1):
        model.train()
        order = shuffle_rng.permutation(n_train)
        losses: list[float] = []
        for start in range(0, n_train, BATCH_SIZE):
            index = order[start : start + BATCH_SIZE]
            if index.size < 2:
                continue
            xb = torch.from_numpy(X_train[index].astype(np.float32)).to(device)
            yb = torch.from_numpy(y_train[index].astype(np.float32)).to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        iid_scores_last = score_matrix(model, X_iid, device)
        iid_ap = float(average_precision_score(y_iid, iid_scores_last))
        epoch_history.append({"epoch": epoch, "train_loss_mean": float(np.mean(losses)), "iid_average_precision": iid_ap})
        append_progress(progress_path, {"phase": "train", "epoch": epoch, "train_loss_mean": float(np.mean(losses)), "iid_average_precision": iid_ap})
        log(f"epoch {epoch}/{EPOCHS} train_loss={float(np.mean(losses)):.6f} iid_AP={iid_ap:.6f}")

    # --- 源期标定与 IID 语境读数 ---
    set_status(status_path, "running", phase="calibrate")
    source_test_scores = score_matrix(model, X_source_test, device)
    cal_scores = source_test_scores[cal_mask]
    assert np.isfinite(cal_scores).all()
    thresholds = {f"{budget:.4f}": threshold_at_budget(cal_scores, budget) for budget in FP_BUDGETS}
    calibration_receipt = {
        "calibration_set": "source_period_test_shard_benign_all_months",
        "n_benign": int(np.count_nonzero(cal_mask)),
        "budgets": {
            f"{budget:.4f}": {
                "threshold": thresholds[f"{budget:.4f}"],
                "realized_fpr_on_calibration_set": float(np.count_nonzero(cal_scores >= thresholds[f"{budget:.4f}"]) / cal_scores.size),
                "realized_fp_count": int(np.count_nonzero(cal_scores >= thresholds[f"{budget:.4f}"])),
            }
            for budget in FP_BUDGETS
        },
    }
    iid_context = {
        "n_rows": int(X_iid.shape[0]),
        "n_pos": int((y_iid == 1).sum()),
        **ranking_metrics(y_iid, iid_scores_last),
        "group_a": {f"{budget:.4f}": fpr_fnr(y_iid, iid_scores_last, thresholds[f"{budget:.4f}"]) for budget in FP_BUDGETS},
    }
    log(f"thresholds: {thresholds}; calibration FPR receipt: { {k: v['realized_fpr_on_calibration_set'] for k, v in calibration_receipt['budgets'].items()} }")
    log(f"IID context: AUROC={iid_context['auroc']:.6f} AP={iid_context['average_precision']:.6f} A-FNR@0.1%={iid_context['group_a']['0.0010']['fnr']:.6f}")

    # --- 目标年逐年评价（train+test 合并） ---
    set_status(status_path, "running", phase="evaluate")
    per_year: dict[str, Any] = {}
    for year in TARGET_YEARS:
        year_start = time.monotonic()
        arrays = []
        for shard in ("train", "test"):
            path = DATA_ROOT / f"Baseline/{year}/{year}_{shard}.parquet"
            shard_data = read_shard(path, feature_names)
            assert shard_data["rows"] == EXPECTED_SHARD_ROWS[(year, shard)], f"{year}_{shard}"
            arrays.append(shard_data)
        X_year = np.concatenate([item["X"] for item in arrays])
        y_year = np.concatenate([item["y"] for item in arrays])
        m_year = np.concatenate([item["months"] for item in arrays])
        del arrays
        scores = score_matrix(model, X_year, device)
        assert np.isfinite(scores).all()
        metrics_row: dict[str, Any] = {
            "n_rows": int(X_year.shape[0]),
            "n_pos": int((y_year == 1).sum()),
            "n_benign": int((y_year == 0).sum()),
            "panel": "train_plus_test_combined",
            **ranking_metrics(y_year, scores),
        }
        # A 组：源标定阈值
        metrics_row["group_a"] = {f"{budget:.4f}": fpr_fnr(y_year, scores, thresholds[f"{budget:.4f}"]) for budget in FP_BUDGETS}
        # B 组：该年自身良性自校准（诊断口径，目标知情）
        benign_scores = scores[y_year == 0]
        group_b = {}
        for budget in FP_BUDGETS:
            thr_b = threshold_at_budget(benign_scores, budget)
            group_b[f"{budget:.4f}"] = fpr_fnr(y_year, scores, thr_b)
        metrics_row["group_b"] = group_b
        per_year[str(year)] = metrics_row
        np.savez_compressed(
            out_dir / "predictions" / f"{year}.npz",
            scores=scores.astype(np.float32), labels=y_year.astype(np.uint8), months=m_year,
        )
        a_fnr = metrics_row["group_a"]["0.0010"]["fnr"]
        b_fnr = metrics_row["group_b"]["0.0010"]["fnr"]
        log(f"year {year}: n={metrics_row['n_rows']} pos={metrics_row['n_pos']} AUROC={metrics_row['auroc']:.6f} AP={metrics_row['average_precision']:.6f} FNR@0.1% A={a_fnr:.6f} B={b_fnr:.6f}")
        append_progress(progress_path, {"phase": "evaluate", "year": year, "auroc": metrics_row["auroc"], "average_precision": metrics_row["average_precision"], "group_a_fnr_0.0010": a_fnr, "group_b_fnr_0.0010": b_fnr, "elapsed_seconds": time.monotonic() - year_start})
        del X_year, y_year, m_year, scores

    # --- 资源收据 ---
    mps_receipt: dict[str, Any] = {}
    try:
        mps_receipt = {
            "current_allocated_bytes": int(torch.mps.current_allocated_memory()),
            "driver_allocated_bytes": int(torch.mps.driver_allocated_memory()),
            "recommended_max_bytes": int(torch.mps.recommended_max_memory()),
        }
    except Exception as error:  # noqa: BLE001
        mps_receipt = {"error": repr(error)}
    resource_receipt = {
        "device": str(device),
        "device_name": "Apple Silicon unified memory (MPS)",
        "mps": mps_receipt,
        "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024,
        "wall_clock_seconds": time.monotonic() - started,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "sklearn": sklearn.__version__,
        "platform": platform.platform(),
    }

    # --- 汇总落盘 ---
    set_status(status_path, "running", phase="write_outputs")
    # 训练区拟合度语境（分数重算）：直接对训练矩阵打分
    train_fit_scores = score_matrix(model, X_train, device)
    train_fit = {"train_rows": int(X_train.shape[0]), **ranking_metrics(y_train, train_fit_scores)}
    del train_fit_scores

    metrics_payload = {
        "run_id": "ch3-lamda-preflight-e1-threshold-transfer-v1",
        "protocol": "screening_only",
        "published_feature_space_uses_future_covariates": True,
        "strict_source_inductive_protocol": False,
        "official_vectorization_code_revision": OFFICIAL_CODE_REVISION,
        "seed": SEED,
        "frozen_config": {
            "epochs": EPOCHS, "batch_size": BATCH_SIZE, "learning_rate": LEARNING_RATE,
            "optimizer": "Adam", "loss": "BCEWithLogitsLoss",
            "model": "LamdaMLP(4561->128->64->32->1, BatchNorm+ReLU+Dropout(0.5) x3)",
            "parameter_count": param_count,
            "device": "mps",
            "threshold_convention": "np.quantile(benign_scores, 1-budget, method='linear'); predict_malware = score >= threshold",
            "fp_budgets": list(FP_BUDGETS),
            "panel_note": "target years evaluated on train+test combined, matching plan §2.1 reference readings",
        },
        "code_sha256": code_sha,
        "data_identity": {"input_manifest_sha256": sha256_file(input_manifest_path), "shards": file_receipts},
        "data_summary": {
            "train_rows": int(X_train.shape[0]),
            "train_pos": int((y_train == 1).sum()),
            "iid_months": list(IID_MONTHS),
            "expected_train_rows": EXPECTED_TRAIN_ROWS,
        },
        "epoch_history": epoch_history,
        "train_fit_context": train_fit,
        "calibration": calibration_receipt,
        "iid_context": iid_context,
        "per_year": per_year,
        "disclosure_rule": "years with n_pos < 500 (2024: 794, 2025: 23) are exploratory only per route-control D1 ruling; decided before this run",
        "resource": resource_receipt,
    }
    write_json(out_dir / "metrics.json", metrics_payload)

    manifest_payload = {
        "run_id": "ch3-lamda-preflight-e1-threshold-transfer-v1",
        "generated_at": now_utc(),
        "entry_script": str(code_path),
        "entry_script_sha256": code_sha,
        "input_manifest_path": str(input_manifest_path),
        "input_manifest_sha256": sha256_file(input_manifest_path),
        "outputs": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
            for path in sorted(out_dir.rglob("*"))
            if path.is_file() and path.name not in {"run-manifest.json", "status.json"}
        },
        "notes": [
            "predictions npz 保存逐年 scores/labels/months（行序=分片读取顺序，train 在前 test 在后），可由相同读取程序复现逐样本",
            "无凭据写入任何文件",
        ],
    }
    write_json(out_dir / "run-manifest.json", manifest_payload)
    set_status(status_path, "completed", phase="done", wall_clock_seconds=time.monotonic() - started)
    log(f"completed in {time.monotonic() - started:.1f}s; outputs at {out_dir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # 失败也保留状态与原始 traceback（不吞异常、不清理现场）
        error_dir = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
        set_status(error_dir / "status.json", "failed", phase="exception", traceback=traceback.format_exc())
        traceback.print_exc()
        sys.exit(1)
