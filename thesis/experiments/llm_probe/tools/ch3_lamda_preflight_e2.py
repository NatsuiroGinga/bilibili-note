#!/usr/bin/env python
"""E2：LAMDA 官方基线复现（数据门禁）——四模型 × 两划分。

冻结规格见 `.Codex/docs/2026-10-14-LAMDA前置实验/implementation_plan.md` §三
与同目录 `run-log.md` 的「已冻结值」表。**判据跑前冻结，不得按结果调参。**

口径（逐字照官方脚本 `anoshift_experiment_models_separate.py`，commit 7728bfa）：
- 训练 = 2013_train ∪ 2014_train 排除 year_month ∈ {2013-12, 2014-08}（137,869 行）
- IID  = 2013_test ∪ 2014_test 的 {2013-12, 2014-08} 两月
- FAR  = 2018–2025 的 **test 分片**
- 阈值固定 0.5，不做标定；指标 F1 / ROC-AUC / PR-AUC / FPR / FNR

**必须分两相跑（各起一个进程）**——2026-10-14 实测故障：
    torch 一旦被 import，同进程内 LightGBM 立刻 `OMP: Error #179` + SIGSEGV（exit 139）。
    探针 A（只 lightgbm，fit 成功 exit 0）vs 探针 B（先 import e1[带 torch] 再 lightgbm，exit 139）。
    ⇒ 故本文件**模块级不 import torch**，torch 只在 `--phase mlp` 分支内惰性导入；
      `--phase gbdt` 分支带 `assert "torch" not in sys.modules` 机械断言。
**也不 import `ch3_lamda_preflight_e1`**——e1 第 39 行模块级 `import torch`，会污染 GBDT 相。
本文件因此自带 e1 的数据读取与指标助手（口径逐字一致），并由 `EXPECTED_*` 断言守住漂移。

**运行（严格串行，两次调用）**：
    PY=/opt/miniconda3/envs/rwkv/bin/python
    $PY thesis/experiments/llm_probe/tools/ch3_lamda_preflight_e2.py --phase mlp
    $PY thesis/experiments/llm_probe/tools/ch3_lamda_preflight_e2.py --phase gbdt
两相各写一次 `metrics.json`（后写的合并前相结果），崩一相不丢另一相。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# 必须在 import lightgbm/xgboost 之前设：多线程 OMP 初始化在本机失败
# （`OMP: Error #179: Function pthread_mutex_init failed`），4 线程实测最快且稳定。
os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
import pyarrow.parquet as pq
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    roc_auc_score,
)

RUN_NAME = "ch3-lamda-preflight-e2-baseline-replication-v1"
RUN_DIR = Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME
THRESHOLD = 0.5
FAR_YEARS = tuple(range(2018, 2026))

# ---- 与 ch3_lamda_preflight_e1 逐字一致；改动任一处都会使 E1/E2 不可比 ----
SEED = 42
EPOCHS = 6
BATCH_SIZE = 512
LEARNING_RATE = 0.001
SCORING_BATCH = 4096
EXPECTED_PARAM_COUNT = 594_753
EXPECTED_FEATURES = 4_561
SOURCE_YEARS = (2013, 2014)
IID_MONTHS = ("2013-12", "2014-08")
EXPECTED_TRAIN_ROWS = 137_869
EXPECTED_IID_TEST_ROWS = 3_065
DATA_ROOT = Path(
    "/Users/bilibili/personal/note/.worktrees/ch3-drift-20260908/"
    "thesis/experiments/llm_probe/runs/data-raw/"
    "lamda-iclr2026-baseline-ad9614bdd5556767"
)

# n_jobs 由官方脚本原值 8 改为 4：**资源参数，非科研参数**。依据：本机多线程 OMP
# 初始化失败（`OMP: Error #179`），实测 4 线程最快（12.1 s）且稳定。
# 该改动只影响墙钟，不影响拟合结果；已登记进 run-log。
N_JOBS = 4
LIGHTGBM_PARAMS = dict(
    learning_rate=0.02, num_leaves=256, min_child_samples=30,
    subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
    reg_alpha=1.5, reg_lambda=1.5, n_estimators=5000, metric="auc", n_jobs=N_JOBS,
)
XGBOOST_PARAMS = dict(max_depth=12, eta=0.05, n_estimators=3000,
                      objective="binary:logistic", tree_method="hist", n_jobs=N_JOBS)


# ---------------------------------------------------------------- 助手（镜像 e1）


def now_utc() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".partial")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def set_status(path: Path, state: str, **extra: Any) -> None:
    write_json(path, {"status": state, "ts": now_utc(), **extra})


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
    return {"threshold": float(threshold), "fpr": fpr, "fnr": fnr,
            "fp": fp, "tn": tn, "fn": fn, "tp": tp}


def ranking_metrics(labels: np.ndarray, scores: np.ndarray) -> dict[str, float | None]:
    if np.unique(labels).size < 2:
        return {"auroc": None, "average_precision": None}
    return {"auroc": float(roc_auc_score(labels, scores)),
            "average_precision": float(average_precision_score(labels, scores))}


def metrics_at(labels: np.ndarray, scores: np.ndarray) -> dict:
    m = fpr_fnr(labels, scores, THRESHOLD)
    m.update(ranking_metrics(labels, scores))
    m["f1"] = float(f1_score(labels, (scores >= THRESHOLD).astype(int), zero_division=0))
    m["n"] = int(labels.size)
    m["n_pos"] = int((labels == 1).sum())
    return m


# ---------------------------------------------------------------- 数据


def build_sets():
    feature_names = feature_names_from_schema(DATA_ROOT / "Baseline/2013/2013_train.parquet")
    assert len(feature_names) == EXPECTED_FEATURES, f"features {len(feature_names)}"

    train_parts, iid_parts, far_parts = [], [], []
    for year in SOURCE_YEARS:
        tr = read_shard(DATA_ROOT / f"Baseline/{year}/{year}_train.parquet", feature_names)
        te = read_shard(DATA_ROOT / f"Baseline/{year}/{year}_test.parquet", feature_names)
        keep = ~np.isin(tr["months"], IID_MONTHS)
        train_parts.append((tr["X"][keep], tr["y"][keep]))
        iid_keep = np.isin(te["months"], IID_MONTHS)
        iid_parts.append((te["X"][iid_keep], te["y"][iid_keep]))
        print(f"[load] {year}: train_kept={int(keep.sum())} iid={int(iid_keep.sum())}", flush=True)

    for year in FAR_YEARS:
        te = read_shard(DATA_ROOT / f"Baseline/{year}/{year}_test.parquet", feature_names)
        far_parts.append((te["X"], te["y"]))
        print(f"[load] {year}: far_test={te['rows']} pos={int((te['y'] == 1).sum())}", flush=True)

    Xtr = np.concatenate([p[0] for p in train_parts]); ytr = np.concatenate([p[1] for p in train_parts])
    Xiid = np.concatenate([p[0] for p in iid_parts]); yiid = np.concatenate([p[1] for p in iid_parts])
    Xfar = np.concatenate([p[0] for p in far_parts]); yfar = np.concatenate([p[1] for p in far_parts])
    assert Xtr.shape[0] == EXPECTED_TRAIN_ROWS, f"train rows {Xtr.shape[0]}"
    assert Xiid.shape[0] == EXPECTED_IID_TEST_ROWS, f"iid rows {Xiid.shape[0]}"
    print(f"[sets] train={Xtr.shape} iid={Xiid.shape} far={Xfar.shape} far_pos={int((yfar==1).sum())}", flush=True)
    return Xtr, ytr, Xiid, yiid, Xfar, yfar


def to_sparse(x: np.ndarray):
    """二值特征 int8 → CSR float32。

    **不先做稠密 astype(float32) 副本**：137,869×4,561 的稠密 float32 约 2.5 GiB，
    本机内存只有 16 GiB 且当前可用不足 1 GiB，该拷贝是本机 OOM 的直接元凶之一。
    先由 int8 稠密建 CSR（只存非零），再对稀疏矩阵 astype，峰值降两个数量级。
    """
    from scipy.sparse import csr_matrix
    return csr_matrix(x).astype(np.float32)


# ---------------------------------------------------------------- 相：MLP


def run_mlp(Xtr, ytr, Xiid, yiid, Xfar, yfar, flush) -> None:
    import torch  # noqa: PLC0415 —— 只在本相导入，见文件头故障说明

    set_status(RUN_DIR / "status.json", "running", phase="mlp")
    device = torch.device("mps")
    torch.manual_seed(SEED); np.random.seed(SEED)
    mlp = build_mlp(torch, EXPECTED_FEATURES)
    n_params = sum(p.numel() for p in mlp.parameters())
    assert n_params == EXPECTED_PARAM_COUNT, f"param count {n_params}"
    mlp.to(device)
    opt = torch.optim.Adam(mlp.parameters(), lr=LEARNING_RATE)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    rng = np.random.default_rng(SEED)
    t0 = time.time()
    for epoch in range(1, EPOCHS + 1):
        mlp.train()
        order = rng.permutation(Xtr.shape[0])
        losses = []
        for s in range(0, Xtr.shape[0], BATCH_SIZE):
            idx = order[s : s + BATCH_SIZE]
            if idx.size < 2:
                continue
            xb = torch.from_numpy(Xtr[idx].astype(np.float32)).to(device)
            yb = torch.from_numpy(ytr[idx].astype(np.float32)).to(device)
            opt.zero_grad(); loss = loss_fn(mlp(xb), yb); loss.backward(); opt.step()
            losses.append(float(loss.detach()))
        print(f"[mlp] epoch {epoch}/{EPOCHS} loss={np.mean(losses):.6f}", flush=True)

    with torch.inference_mode():
        mlp.eval()
        results = {"MLP": {
            "IID": metrics_at(yiid, score_matrix(torch, mlp, Xiid, device)),
            "FAR": metrics_at(yfar, score_matrix(torch, mlp, Xfar, device)),
        }}
    receipts = {"MLP": {"device": "mps", "params": n_params,
                       "wall_seconds": time.time() - t0, "torch": torch.__version__}}
    flush("mlp_done", results, receipts)
    del mlp, opt
    torch.mps.empty_cache()


def build_mlp(torch, input_dim: int):
    """镜像 e1.LamdaMLP（input→128→64→32→1，BN+ReLU+Dropout0.5）。
    结构漂移由 `EXPECTED_PARAM_COUNT` 断言守住。"""
    from torch import nn

    class LamdaMLP(nn.Module):
        def __init__(self, dim: int) -> None:
            super().__init__()
            layers: list[nn.Module] = []
            width = dim
            for next_width in (128, 64, 32):
                layers.extend([nn.Linear(width, next_width), nn.BatchNorm1d(next_width),
                               nn.ReLU(), nn.Dropout(0.5)])
                width = next_width
            layers.append(nn.Linear(width, 1))
            self.network = nn.Sequential(*layers)

        def forward(self, x):
            return self.network(x).squeeze(1)

    return LamdaMLP(input_dim)


def score_matrix(torch, model, features: np.ndarray, device) -> np.ndarray:
    chunks: list[np.ndarray] = []
    for start in range(0, features.shape[0], SCORING_BATCH):
        batch = torch.from_numpy(features[start : start + SCORING_BATCH].astype(np.float32)).to(device)
        chunks.append(torch.sigmoid(model(batch)).cpu().numpy().astype(np.float64))
    return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float64)


# ---------------------------------------------------------------- 相：GBDT + SVM


def run_gbdt(Xtr, ytr, Xiid, yiid, Xfar, yfar, flush) -> None:
    # 机械断言：本相进程内绝不能有 torch（否则 LightGBM 必 SIGSEGV）
    assert "torch" not in sys.modules, "GBDT 相混入了 torch，必然触发 OMP #179"

    results: dict[str, dict] = {}
    receipts: dict[str, dict] = {}

    set_status(RUN_DIR / "status.json", "running", phase="lightgbm")
    import lightgbm as lgb
    t0 = time.time()
    Xtr_sp = to_sparse(Xtr)
    del Xtr
    Xiid_sp = to_sparse(Xiid)
    Xfar_sp = to_sparse(Xfar)
    del Xiid, Xfar
    print(f"[lgb] sparse built density={Xtr_sp.nnz / (Xtr_sp.shape[0] * Xtr_sp.shape[1]):.4f}", flush=True)
    gbm = lgb.LGBMClassifier(**LIGHTGBM_PARAMS)
    gbm.fit(Xtr_sp, ytr)
    results["LightGBM"] = {"IID": metrics_at(yiid, gbm.predict_proba(Xiid_sp)[:, 1]),
                           "FAR": metrics_at(yfar, gbm.predict_proba(Xfar_sp)[:, 1])}
    receipts["LightGBM"] = {"device": "cpu", "wall_seconds": time.time() - t0,
                            "version": lgb.__version__, "input": "csr_sparse_float32"}
    print(f"[lgb] done in {receipts['LightGBM']['wall_seconds']:.1f}s", flush=True)
    del gbm
    flush("lightgbm_done", results, receipts)

    set_status(RUN_DIR / "status.json", "running", phase="xgboost")
    import xgboost as xgb
    t0 = time.time()
    clf = xgb.XGBClassifier(**XGBOOST_PARAMS)
    clf.fit(Xtr_sp, ytr)
    results["XGBoost"] = {"IID": metrics_at(yiid, clf.predict_proba(Xiid_sp)[:, 1]),
                          "FAR": metrics_at(yfar, clf.predict_proba(Xfar_sp)[:, 1])}
    receipts["XGBoost"] = {"device": "cpu", "wall_seconds": time.time() - t0,
                           "version": xgb.__version__, "input": "csr_sparse_float32"}
    print(f"[xgb] done in {receipts['XGBoost']['wall_seconds']:.1f}s", flush=True)
    del clf
    flush("xgboost_done", results, receipts)

    set_status(RUN_DIR / "status.json", "running", phase="svm")
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.svm import LinearSVC
    t0 = time.time()
    svm = CalibratedClassifierCV(LinearSVC(max_iter=10000))
    svm.fit(Xtr_sp, ytr)
    results["SVM"] = {"IID": metrics_at(yiid, svm.predict_proba(Xiid_sp)[:, 1]),
                      "FAR": metrics_at(yfar, svm.predict_proba(Xfar_sp)[:, 1])}
    receipts["SVM"] = {"device": "cpu", "wall_seconds": time.time() - t0,
                       "input": "csr_sparse_float32"}
    print(f"[svm] done in {receipts['SVM']['wall_seconds']:.1f}s", flush=True)
    del svm
    flush("gbdt_done", results, receipts)


# ---------------------------------------------------------------- 入口


def main(phase: str = "all") -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    status_path = RUN_DIR / "status.json"
    metrics_path = RUN_DIR / "metrics.json"
    t_start = time.time()
    set_status(status_path, "running", phase="load")

    results: dict[str, dict] = {}
    receipts: dict[str, dict] = {}
    if metrics_path.is_file():
        prev = json.loads(metrics_path.read_text(encoding="utf-8"))
        results.update(prev.get("results") or {})
        receipts.update(prev.get("receipts") or {})

    def flush(label: str, fresh_results: dict, fresh_receipts: dict) -> None:
        """每完成一个模型立即落盘，崩溃不丢已完成的结果。"""
        results.update(fresh_results); receipts.update(fresh_receipts)
        write_json(metrics_path, {
            "run_name": RUN_NAME, "threshold": THRESHOLD, "phase": label,
            "results": results, "receipts": receipts,
            "wall_seconds_total": time.time() - t_start, "ts": now_utc(),
        })

    Xtr, ytr, Xiid, yiid, Xfar, yfar = build_sets()

    if phase in ("all", "mlp"):
        run_mlp(Xtr, ytr, Xiid, yiid, Xfar, yfar, flush)
        del Xtr, ytr, Xiid, yiid, Xfar, yfar
    if phase in ("all", "gbdt"):
        run_gbdt(Xtr, ytr, Xiid, yiid, Xfar, yfar, flush)

    set_status(status_path, "completed", status="completed", phase=phase,
               completed_models=sorted(results))

    print(f"\n=== E2 复现表（阈值 {THRESHOLD}）===")
    for split in ("IID", "FAR"):
        print(f"-- {split} --")
        for name in ("LightGBM", "XGBoost", "MLP", "SVM"):
            if name not in results:
                continue
            m = results[name][split]
            print(f"  {name:9s} F1={m['f1']:.4f} ROC-AUC={m['auroc']:.4f} "
                  f"PR-AUC={m['average_precision']:.4f} FPR={m['fpr']:.4f} "
                  f"FNR={m['fnr']:.4f} n={m['n']}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E2 基线复现（分相运行）")
    parser.add_argument("--phase", choices=("all", "mlp", "gbdt"), default="all",
                        help="mlp 与 gbdt 必须分两个进程跑；all 仅作调试用（会崩）")
    args = parser.parse_args()
    raise SystemExit(main(args.phase))
