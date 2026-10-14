#!/usr/bin/env python
"""E2：LAMDA 官方基线复现（数据门禁）——四模型 × 两划分。

冻结规格见 `.Codex/docs/2026-10-14-LAMDA前置实验/implementation_plan.md` §三
与同目录 `run-log.md` 的「已冻结值」表。**判据跑前冻结，不得按结果调参。**

口径（逐字照官方脚本 `anoshift_experiment_models_separate.py`，commit 7728bfa）：
- 训练 = 2013_train ∪ 2014_train 排除 year_month ∈ {2013-12, 2014-08}（137,869 行）
- IID  = 2013_test ∪ 2014_test 的 {2013-12, 2014-08} 两月
- FAR  = 2018–2025 的 **test 分片**
- 阈值固定 0.5，不做标定；指标 F1 / ROC-AUC / PR-AUC / FPR / FNR

**运行（单进程、串行）**：
    /opt/miniconda3/envs/rwkv/bin/python \
        thesis/experiments/llm_probe/tools/ch3_lamda_preflight_e2.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# 必须在 import lightgbm/xgboost 之前设：多线程 OMP 初始化在本机失败
# （`OMP: Error #179: Function pthread_mutex_init failed`），4 线程实测最快且稳定。
os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ch3_lamda_preflight_e1 as e1  # noqa: E402

import torch  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402

RUN_NAME = "ch3-lamda-preflight-e2-baseline-replication-v1"
RUN_DIR = (
    Path(__file__).resolve().parents[1] / "runs/diagnostics" / RUN_NAME
)
THRESHOLD = 0.5
FAR_YEARS = tuple(range(2018, 2026))

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


def metrics_at(labels: np.ndarray, scores: np.ndarray) -> dict:
    m = e1.fpr_fnr(labels, scores, THRESHOLD)
    m.update(e1.ranking_metrics(labels, scores))
    m["f1"] = float(f1_score(labels, (scores >= THRESHOLD).astype(int), zero_division=0))
    m["n"] = int(labels.size)
    m["n_pos"] = int((labels == 1).sum())
    return m


def build_sets():
    feature_names = e1.feature_names_from_schema(e1.DATA_ROOT / "Baseline/2013/2013_train.parquet")
    assert len(feature_names) == e1.EXPECTED_FEATURES

    train_parts, iid_parts, far_parts = [], [], []
    for year in e1.SOURCE_YEARS:
        tr = e1.read_shard(e1.DATA_ROOT / f"Baseline/{year}/{year}_train.parquet", feature_names)
        te = e1.read_shard(e1.DATA_ROOT / f"Baseline/{year}/{year}_test.parquet", feature_names)
        keep = ~np.isin(tr["months"], e1.IID_MONTHS)
        train_parts.append((tr["X"][keep], tr["y"][keep]))
        iid_keep = np.isin(te["months"], e1.IID_MONTHS)
        iid_parts.append((te["X"][iid_keep], te["y"][iid_keep]))
        print(f"[load] {year}: train_kept={int(keep.sum())} iid={int(iid_keep.sum())}", flush=True)

    for year in FAR_YEARS:
        te = e1.read_shard(e1.DATA_ROOT / f"Baseline/{year}/{year}_test.parquet", feature_names)
        far_parts.append((te["X"], te["y"]))
        print(f"[load] {year}: far_test={te['rows']} pos={int((te['y'] == 1).sum())}", flush=True)

    Xtr = np.concatenate([p[0] for p in train_parts]); ytr = np.concatenate([p[1] for p in train_parts])
    Xiid = np.concatenate([p[0] for p in iid_parts]); yiid = np.concatenate([p[1] for p in iid_parts])
    Xfar = np.concatenate([p[0] for p in far_parts]); yfar = np.concatenate([p[1] for p in far_parts])
    assert Xtr.shape[0] == e1.EXPECTED_TRAIN_ROWS, f"train rows {Xtr.shape[0]}"
    assert Xiid.shape[0] == e1.EXPECTED_IID_TEST_ROWS, f"iid rows {Xiid.shape[0]}"
    print(f"[sets] train={Xtr.shape} iid={Xiid.shape} far={Xfar.shape} far_pos={int((yfar==1).sum())}", flush=True)
    return Xtr, ytr, Xiid, yiid, Xfar, yfar


def sparse(x: np.ndarray):
    """二值特征 → CSR 稀疏矩阵（float32）。137,869×4,561 稠密 float32 约 2.5 GiB，
    稀疏后大幅下降；本机内存紧张，GBDT/SVM 一律走稀疏。"""
    from scipy.sparse import csr_matrix
    return csr_matrix(x.astype(np.float32))


def main(phase: str = "all") -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    status_path = RUN_DIR / "status.json"
    metrics_path = RUN_DIR / "metrics.json"
    e1.set_status(status_path, "running", phase="load")
    t_start = time.time()
    Xtr, ytr, Xiid, yiid, Xfar, yfar = build_sets()

    # 分相运行时合并已完成相的结果（两相各写一次 metrics.json）
    results: dict[str, dict] = {}
    receipts: dict[str, dict] = {}
    if metrics_path.is_file():
        prev = json.loads(metrics_path.read_text(encoding="utf-8"))
        results.update(prev.get("results") or {})
        receipts.update(prev.get("receipts") or {})

    def flush(phase: str) -> None:
        """每完成一个模型立即落盘，崩溃不丢已完成的结果。"""
        e1.write_json(metrics_path, {
            "run_name": RUN_NAME, "threshold": THRESHOLD, "phase": phase,
            "results": results, "receipts": receipts,
            "wall_seconds_total": time.time() - t_start,
        })

    # ---- MLP（MPS） ----
    e1.set_status(status_path, "running", phase="mlp")
    device = torch.device("mps")
    torch.manual_seed(e1.SEED); np.random.seed(e1.SEED)
    mlp = e1.LamdaMLP(e1.EXPECTED_FEATURES)
    n_params = sum(p.numel() for p in mlp.parameters())
    assert n_params == e1.EXPECTED_PARAM_COUNT, f"param count {n_params}"
    mlp.to(device)
    opt = torch.optim.Adam(mlp.parameters(), lr=e1.LEARNING_RATE)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    rng = np.random.default_rng(e1.SEED)
    t0 = time.time()
    for epoch in range(1, e1.EPOCHS + 1):
        mlp.train()
        order = rng.permutation(Xtr.shape[0])
        losses = []
        for s in range(0, Xtr.shape[0], e1.BATCH_SIZE):
            idx = order[s : s + e1.BATCH_SIZE]
            if idx.size < 2:
                continue
            xb = torch.from_numpy(Xtr[idx].astype(np.float32)).to(device)
            yb = torch.from_numpy(ytr[idx].astype(np.float32)).to(device)
            opt.zero_grad(); loss = loss_fn(mlp(xb), yb); loss.backward(); opt.step()
            losses.append(float(loss.detach()))
        print(f"[mlp] epoch {epoch}/{e1.EPOCHS} loss={np.mean(losses):.6f}", flush=True)
    mlp_wall = time.time() - t0
    results["MLP"] = {"IID": metrics_at(yiid, e1.score_matrix(mlp, Xiid, device)),
                      "FAR": metrics_at(yfar, e1.score_matrix(mlp, Xfar, device))}
    receipts["MLP"] = {"device": "mps", "params": n_params, "wall_seconds": mlp_wall}
    del mlp, opt
    torch.mps.empty_cache()

    # ---- LightGBM ----
    e1.set_status(status_path, "running", phase="lightgbm")
    import lightgbm as lgb
    t0 = time.time()
    Xtr_sp, Xiid_sp, Xfar_sp = sparse(Xtr), sparse(Xiid), sparse(Xfar)
    del Xtr, Xiid, Xfar  # 释放稠密副本（约 0.63 GiB），GBDT/SVM 走稀疏
    print(f"[lgb] sparse built density={Xtr_sp.nnz / (Xtr_sp.shape[0] * Xtr_sp.shape[1]):.4f}", flush=True)
    gbm = lgb.LGBMClassifier(**LIGHTGBM_PARAMS)
    gbm.fit(Xtr_sp, ytr)
    results["LightGBM"] = {"IID": metrics_at(yiid, gbm.predict_proba(Xiid_sp)[:, 1]),
                           "FAR": metrics_at(yfar, gbm.predict_proba(Xfar_sp)[:, 1])}
    receipts["LightGBM"] = {"device": "cpu", "wall_seconds": time.time() - t0,
                            "version": lgb.__version__, "input": "csr_sparse_float32"}
    print(f"[lgb] done in {receipts['LightGBM']['wall_seconds']:.1f}s", flush=True)
    del gbm
    flush("lightgbm_done")

    # ---- XGBoost ----
    e1.set_status(status_path, "running", phase="xgboost")
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
    flush("xgboost_done")

    # ---- SVM ----
    e1.set_status(status_path, "running", phase="svm")
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

    flush("done")
    e1.set_status(status_path, "done", status="completed")

    print("\n=== E2 复现表（阈值 0.5）===")
    for split in ("IID", "FAR"):
        print(f"-- {split} --")
        for name in ("LightGBM", "XGBoost", "MLP", "SVM"):
            m = results[name][split]
            print(f"  {name:9s} F1={m['f1']:.4f} ROC-AUC={m['auroc']:.4f} "
                  f"PR-AUC={m['average_precision']:.4f} FPR={m['fpr']:.4f} FNR={m['fnr']:.4f} n={m['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
