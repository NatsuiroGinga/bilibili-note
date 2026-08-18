# -*- coding: utf-8 -*-
"""A1 强树（lag0..4 展平 XGBoost）验证集误差解剖。

复用 a1_history_ceiling.py 的连接与展平逻辑重训 A1，封存验证集逐样本概率，
然后按事件位置 / 端点流量 / 数据质量 / 时间位置分面解剖 1-AP 的残余误差，
并在固定误报预算下报告窗口级与事件级召回。

只读共享视图；产物写 runs/diagnostics/lspr24-a1-error-anatomy-v1/。
screening_only=true, formal_paper_evidence=false, final_accessed=false。

内存纪律（2026-08-12 C56 容器 OOM 重启复盘后加固）：
- 容器 cgroup 内存上限须从 /sys/fs/cgroup 读取，禁止使用 free / /proc/meminfo /
  psutil.virtual_memory()（它们在容器内报告宿主机数值，曾造成 8.4 倍的乐观误判）。
- 408 维特征矩阵按 parquet row group 分批读取，避免 Arrow 整表与 numpy 副本同时驻留。
- 训练矩阵 X_tr 与验证矩阵 X_va 顺序构造：X_tr -> dtrain -> 释放 X_tr -> X_va ->
  dvalid -> 释放 X_va，不允许两者同时与特征矩阵 F 一起常驻。
"""
import gc
import json
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-prepared/lspr24-screen-wide-v1"
OUT_DIR = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/lspr24-a1-error-anatomy-v1"
LAGS = (1, 2, 3, 4)
SEED = 42
REF_AP_A1 = 0.9807915803958434
N_ENDPOINTS_EXPECTED = 468
WINDOW_SECONDS = 5.0
FP_BUDGETS = (0.01, 0.1, 1.0, 10.0)  # 次 / 端点 / 小时

# 大分配前的安全系数：可用内存需 >= 预计需求 * 该系数才放行，否则主动退出。
MEMORY_SAFETY_FACTOR = 1.3
_CGROUP_V2_MAX = "/sys/fs/cgroup/memory.max"
_CGROUP_V2_CUR = "/sys/fs/cgroup/memory.current"
_CGROUP_V1_LIMIT = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
_CGROUP_V1_USAGE = "/sys/fs/cgroup/memory/memory.usage_in_bytes"

XGB_PARAMS = {
    "objective": "binary:logistic",
    "eta": 0.05,
    "max_depth": 8,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1,
    "min_child_weight": 1,
    "max_bin": 256,
    "tree_method": "hist",
    "device": "cuda",
    "seed": SEED,
    "eval_metric": "aucpr",
}
NUM_ROUND = 800


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _read_cgroup_int(path: str):
    """读取单个 cgroup 数值文件；v2 的 'max'（无上限）返回 None。"""
    with open(path) as f:
        raw = f.read().strip()
    if raw == "max":
        return None
    return int(raw)


def _cgroup_memory_limit_and_usage():
    """读取容器 cgroup 内存上限与当前用量（字节），优先 v2、回退 v1。

    禁止使用 free / /proc/meminfo / psutil.virtual_memory()：容器内这些接口
    报告宿主机总内存而非 cgroup 限额，2026-08-12 曾据此产生 8.4 倍的乐观
    误判（宿主机 free 754GiB vs 容器 cgroup 上限 90GiB），是本次 OOM 重启的
    直接诱因之一。任一路径缺失或不可解析都返回 (None, None)，调用方需自行
    降级为“跳过预检”而非抛错阻塞非容器环境下的本地静态检查。
    """
    try:
        limit = _read_cgroup_int(_CGROUP_V2_MAX)
        usage = _read_cgroup_int(_CGROUP_V2_CUR)
        if usage is not None:
            return limit, usage
    except (FileNotFoundError, ValueError, OSError):
        pass
    try:
        limit = _read_cgroup_int(_CGROUP_V1_LIMIT)
        usage = _read_cgroup_int(_CGROUP_V1_USAGE)
        return limit, usage
    except (FileNotFoundError, ValueError, OSError):
        return None, None


def _vm_rss_bytes() -> int:
    """读取当前进程 VmRSS（字节），来自 /proc/self/status；失败返回 -1。"""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024  # kB -> bytes
    except (FileNotFoundError, ValueError, OSError):
        pass
    return -1


def _vm_rss_line() -> str:
    rss = _vm_rss_bytes()
    if rss < 0:
        return "VmRSS=未知"
    return f"VmRSS={rss / (1024 ** 3):.2f}GiB"


def _check_memory_budget(label: str, need_gib: float) -> None:
    """大分配前核对容器可用内存；不足安全系数即主动 raise 退出，不硬撑。"""
    limit, usage = _cgroup_memory_limit_and_usage()
    if limit is None or usage is None:
        log(
            f"[内存自检] 无法读取 cgroup 内存上限/用量，跳过 {label} 的预算检查"
            f"（{_vm_rss_line()}）"
        )
        return
    avail_gib = (limit - usage) / (1024 ** 3)
    need_with_margin = need_gib * MEMORY_SAFETY_FACTOR
    log(
        f"[内存自检] 即将分配 {label}: 约 {need_gib:.2f}GiB（含 {MEMORY_SAFETY_FACTOR}x "
        f"安全系数需 {need_with_margin:.2f}GiB），容器可用 {avail_gib:.2f}GiB "
        f"（上限 {limit / (1024 ** 3):.2f}GiB，已用 {usage / (1024 ** 3):.2f}GiB，"
        f"{_vm_rss_line()}）"
    )
    if avail_gib < need_with_margin:
        raise MemoryError(
            f"内存预算不足：{label} 预计 {need_gib:.2f}GiB x {MEMORY_SAFETY_FACTOR} 安全系数 = "
            f"{need_with_margin:.2f}GiB，容器仅可用 {avail_gib:.2f}GiB，主动终止避免 OOM 重启"
        )


def per_positive_error_attribution(y: np.ndarray, s: np.ndarray) -> Tuple[float, np.ndarray]:
    """按正类逐样本分解 1-AP。

    AP = mean over positives of precision(该正类分数所在并列组末端)。
    返回 (ap, contrib)；contrib 与 y 同长，contrib[i]=(1-prec_i)/n_pos（仅正类非零），
    sum(contrib) == 1 - AP（精确，与 sklearn 并列处理一致）。
    """
    n = len(y)
    order = np.argsort(-s, kind="mergesort")
    ys = y[order].astype(np.int64)
    ss = s[order]
    cum_tp = np.cumsum(ys)
    prec = cum_tp / np.arange(1, n + 1, dtype=np.float64)
    is_end = np.empty(n, dtype=bool)
    is_end[-1] = True
    is_end[:-1] = ss[1:] != ss[:-1]
    end_idx = np.where(is_end, np.arange(n), n)
    end_idx = np.flip(np.minimum.accumulate(np.flip(end_idx)))
    prec_group = prec[end_idx]
    n_pos = int(ys.sum())
    ap = float(prec_group[ys == 1].mean())
    contrib_sorted = np.where(ys == 1, (1.0 - prec_group) / n_pos, 0.0)
    contrib = np.zeros(n, dtype=np.float64)
    contrib[order] = contrib_sorted
    return ap, contrib


def slice_stats(
    name: str,
    sl_mask: np.ndarray,
    y: np.ndarray,
    s: np.ndarray,
    contrib: np.ndarray,
    total_err: float,
    ap_base: float,
    s_max: float,
    s_min: float,
) -> Dict:
    """单个分面切片的 AP、误差贡献与三种反事实修复 Delta_AP。"""
    n = int(sl_mask.sum())
    n_pos = int(y[sl_mask].sum())
    n_neg = n - n_pos
    err_abs = float(contrib[sl_mask].sum())
    out: Dict = {
        "slice": name,
        "n_windows": n,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "pos_rate": (n_pos / n) if n else None,
        "ap_within": (
            float(average_precision_score(y[sl_mask], s[sl_mask])) if n_pos > 0 and n_neg > 0 else None
        ),
        "mean_score_pos": float(s[sl_mask & (y == 1)].mean()) if n_pos else None,
        "error_contribution_abs": err_abs,
        "error_contribution_share": err_abs / total_err if total_err > 0 else None,
    }
    pos_in = sl_mask & (y == 1)
    neg_in = sl_mask & (y == 0)
    if n_pos > 0:
        s_cf = s.copy()
        s_cf[pos_in] = s_max + 1.0
        out["delta_ap_fix_pos"] = float(average_precision_score(y, s_cf)) - ap_base
    else:
        out["delta_ap_fix_pos"] = 0.0
    if n_neg > 0:
        s_cf = s.copy()
        s_cf[neg_in] = s_min - 1.0
        out["delta_ap_fix_neg"] = float(average_precision_score(y, s_cf)) - ap_base
    else:
        out["delta_ap_fix_neg"] = 0.0
    if n > 0:
        s_cf = s.copy()
        s_cf[pos_in] = s_max + 1.0
        s_cf[neg_in] = s_min - 1.0
        out["delta_ap_fix_both"] = float(average_precision_score(y, s_cf)) - ap_base
    else:
        out["delta_ap_fix_both"] = 0.0
    return out


def main() -> None:
    t_start = time.time()
    cg_limit, cg_usage = _cgroup_memory_limit_and_usage()
    if cg_limit is not None and cg_usage is not None:
        log(
            f"[内存自检] 容器 cgroup 上限={cg_limit / (1024 ** 3):.2f}GiB "
            f"当前用量={cg_usage / (1024 ** 3):.2f}GiB "
            f"可用={(cg_limit - cg_usage) / (1024 ** 3):.2f}GiB {_vm_rss_line()}"
        )
    else:
        log(
            f"[内存自检] 无法读取 cgroup 内存信息（非容器环境或路径缺失），"
            f"跳过容量预检 {_vm_rss_line()}"
        )

    with open(f"{ROOT}/dataset-manifest.json") as f:
        manifest = json.load(f)
    feat_cols = manifest["model_feature_columns"]
    assert len(feat_cols) == 408

    log("读取元数据列")
    meta_tbl = pq.read_table(
        f"{ROOT}/development-wide.parquet",
        columns=[
            "window_row_index",
            "window_start_ns",
            "protected_endpoint_sha256",
            "split_name",
            "has_activity",
            "seconds_since_previous_active_window",
            "consecutive_empty_window_count",
        ],
    )
    wri = meta_tbl["window_row_index"].to_numpy().astype(np.int64)
    win_start_ns = meta_tbl["window_start_ns"].to_numpy().astype(np.int64)
    ep_series = meta_tbl["protected_endpoint_sha256"].to_pandas()
    ep_codes, ep_uniques = pd.factorize(ep_series)
    ep_codes = ep_codes.astype(np.int32)
    sp_raw = meta_tbl["split_name"].to_pandas()
    sp_codes = (sp_raw == "validation").to_numpy().astype(np.int8)
    has_act = meta_tbl["has_activity"].to_pandas().astype("float64").to_numpy()
    ssp = meta_tbl["seconds_since_previous_active_window"].to_pandas().astype("float64").to_numpy()
    cec = meta_tbl["consecutive_empty_window_count"].to_pandas().astype("float64").to_numpy()
    n_rows = len(wri)
    assert n_rows == 7946899
    assert len(ep_uniques) == N_ENDPOINTS_EXPECTED, f"端点数 {len(ep_uniques)} != 468"
    del meta_tbl
    log(f"元数据列已加载 n_rows={n_rows} {_vm_rss_line()}")

    log("读取标签")
    lab_tbl = pq.read_table(f"{ROOT}/development-labels.parquet")
    assert np.array_equal(lab_tbl["window_row_index"].to_numpy().astype(np.int64), wri)
    labels = lab_tbl["label"].to_numpy().astype(np.int64)
    del lab_tbl
    dist = {int(k): int(v) for k, v in zip(*np.unique(labels, return_counts=True))}
    assert dist == {-1: 4800524, 0: 3018069, 1: 128306}, f"标签分布不符: {dist}"
    log(f"标签已加载 {_vm_rss_line()}")

    max_wri = int(wri.max())
    pos = np.full(max_wri + 1, -1, dtype=np.int64)
    pos[wri] = np.arange(n_rows, dtype=np.int64)

    log("流式扫描 temporal-relations.parquet (lag<=4)")
    hist_wri = np.full((n_rows, len(LAGS)), -1, dtype=np.int64)
    conflict_count = 0
    pf = pq.ParquetFile(f"{ROOT}/temporal-relations.parquet")
    for rg in range(pf.metadata.num_row_groups):
        tbl = pf.read_row_group(
            rg, columns=["target_window_row_index", "lag", "history_window_row_index"]
        )
        lag_arr = tbl["lag"].to_numpy().astype(np.int64)
        keep = lag_arr <= 4
        if not keep.any():
            continue
        tgt = tbl["target_window_row_index"].to_numpy().astype(np.int64)[keep]
        hst = tbl["history_window_row_index"].to_numpy().astype(np.int64)[keep]
        lg = lag_arr[keep]
        tpos = pos[tgt]
        for k_i, k in enumerate(LAGS):
            m = lg == k
            if not m.any():
                continue
            tp, hv = tpos[m], hst[m]
            prev = hist_wri[tp, k_i]
            bad = (prev != -1) & (prev != hv)
            conflict_count += int(bad.sum())
            hist_wri[tp, k_i] = hv
    assert conflict_count == 0
    log(f"历史关系扫描完成 {_vm_rss_line()}")

    log("构建历史行位置与掩码")
    has_rel = hist_wri >= 0
    hist_pos = np.where(has_rel, pos[np.clip(hist_wri, 0, max_wri)], -1)
    in_dev = has_rel & (hist_pos >= 0)
    tgt_rows = np.arange(n_rows, dtype=np.int64)
    mask = np.zeros((n_rows, len(LAGS)), dtype=bool)
    for k_i in range(len(LAGS)):
        hp = hist_pos[:, k_i]
        v = in_dev[:, k_i]
        same_ep = np.zeros(n_rows, dtype=bool)
        same_sp = np.zeros(n_rows, dtype=bool)
        same_ep[v] = ep_codes[hp[v]] == ep_codes[tgt_rows[v]]
        same_sp[v] = sp_codes[hp[v]] == sp_codes[tgt_rows[v]]
        mask[:, k_i] = v & same_ep & same_sp
    log(f"历史掩码构建完成 {_vm_rss_line()}")

    evaluable = np.isin(labels, (0, 1))
    train_m = evaluable & (sp_codes == 0)
    val_m = evaluable & (sp_codes == 1)
    n_tr, n_va = int(train_m.sum()), int(val_m.sum())
    assert n_tr == 2219080 and n_va == 927295
    y_tr = labels[train_m].astype(np.float32)
    y_va = labels[val_m].astype(np.float32)
    assert int(y_tr.sum()) == 107455 and int(y_va.sum()) == 20851

    # ---------- 缺陷 1 修复：408 维特征矩阵按 row group 分批读取 ----------
    # 原实现一次性 pq.read_table 读入 Arrow 整表（408 列 x 7,946,899 行），
    # 与同时分配的 numpy 副本 F 同时驻留，直到列循环结束才 del。改为逐 row
    # group 读取，每批用完立即 del，Arrow 侧峰值降到整表的 1/num_row_groups。
    log("载入 408 维特征矩阵（按 row group 分批读取）")
    t0 = time.time()
    f_need_gib = n_rows * len(feat_cols) * 4 / (1024 ** 3)
    _check_memory_budget("F 特征矩阵 (n_rows x 408 float32)", f_need_gib)
    F = np.empty((n_rows, len(feat_cols)), dtype=np.float32)
    pf_feat = pq.ParquetFile(f"{ROOT}/development-wide.parquet")
    n_row_groups = pf_feat.metadata.num_row_groups
    rg_sizes = [pf_feat.metadata.row_group(i).num_rows for i in range(n_row_groups)]
    assert sum(rg_sizes) == n_rows, f"row group 行数之和 {sum(rg_sizes)} != n_rows {n_rows}"
    row_start = 0
    for rg_i, rg_n in enumerate(rg_sizes):
        row_end = row_start + rg_n
        batch_tbl = pf_feat.read_row_group(rg_i, columns=feat_cols)
        assert batch_tbl.num_rows == rg_n, (
            f"row group {rg_i} 实际行数 {batch_tbl.num_rows} != 元数据 {rg_n}"
        )
        for j, c in enumerate(feat_cols):
            F[row_start:row_end, j] = batch_tbl[c].to_numpy(zero_copy_only=False).astype(np.float32)
        del batch_tbl
        row_start = row_end
        log(
            f"  row group {rg_i + 1}/{n_row_groups} 已写入 [{row_end - rg_n}:{row_end}) "
            f"{_vm_rss_line()}"
        )
    assert row_start == n_rows, f"累计行数 {row_start} != n_rows {n_rows}"
    del pf_feat
    log(f"特征载入 {time.time() - t0:.1f}s {_vm_rss_line()}")

    d = len(feat_cols)
    x_cols = d * 5 + len(LAGS)

    def build_matrix(row_mask: np.ndarray) -> np.ndarray:
        rows = np.nonzero(row_mask)[0]
        n = len(rows)
        X = np.zeros((n, x_cols), dtype=np.float32)
        X[:, :d] = F[rows]
        for k_i in range(len(LAGS)):
            hp = hist_pos[rows, k_i]
            mk = mask[rows, k_i]
            blk = X[:, d * (k_i + 1) : d * (k_i + 2)]
            sel = np.nonzero(mk)[0]
            blk[sel] = F[hp[sel]]
            X[:, d * 5 + k_i] = mk.astype(np.float32)
        return X

    # ---------- 缺陷 2 修复：X_tr 与 X_va 顺序构造，不同时驻留 ----------
    # 原实现先后构建 X_tr（18.2GB）与 X_va（7.6GB），二者与 F（12.08GiB）
    # 同时常驻直到脚本末尾才释放 X_tr、且从未显式释放 X_va。改为 X_tr ->
    # dtrain -> del X_tr -> X_va -> dvalid(ref=dtrain) -> del X_va 的顺序流程。
    # fit_s 的计时口径保持与原实现一致：仅累加 dtrain 构造 + dvalid 构造 +
    # xgb.train 三段耗时，不含 X_tr/X_va 的 numpy 构建时间（原实现同样不计入）。
    log("构建训练矩阵 X_tr (2044 列)")
    _check_memory_budget("X_tr 训练矩阵 (n_tr x 2044 float32)", n_tr * x_cols * 4 / (1024 ** 3))
    X_tr = build_matrix(train_m)
    log(f"X_tr 构建完成 {_vm_rss_line()}")

    log("训练 A1 (lag0..4)：转换 dtrain 并立即释放 X_tr")
    t0 = time.time()
    dtrain = xgb.QuantileDMatrix(X_tr, label=y_tr, max_bin=256)
    t_dtrain = time.time() - t0
    del X_tr
    gc.collect()
    log(f"X_tr 已释放，dtrain 已构建，耗时 {t_dtrain:.1f}s {_vm_rss_line()}")

    log("构建验证矩阵 X_va")
    _check_memory_budget("X_va 验证矩阵 (n_va x 2044 float32)", n_va * x_cols * 4 / (1024 ** 3))
    X_va = build_matrix(val_m)
    log(f"X_va 构建完成 {_vm_rss_line()}")

    t0 = time.time()
    dvalid = xgb.QuantileDMatrix(X_va, label=y_va, max_bin=256, ref=dtrain)
    t_dvalid = time.time() - t0
    del X_va
    gc.collect()
    log(f"X_va 已释放，dvalid 已构建，耗时 {t_dvalid:.1f}s {_vm_rss_line()}")

    t0 = time.time()
    booster = xgb.train(XGB_PARAMS, dtrain, num_boost_round=NUM_ROUND)
    t_train = time.time() - t0
    fit_s = t_dtrain + t_dvalid + t_train
    scores = booster.predict(dvalid).astype(np.float64)
    del dtrain, dvalid
    gc.collect()
    log(f"A1 训练完成 fit={fit_s:.1f}s {_vm_rss_line()}")

    ap_a1 = float(average_precision_score(y_va, scores))
    auc_a1 = float(roc_auc_score(y_va, scores))
    log(f"A1 复测 AP={ap_a1:.10f} AUC={auc_a1:.10f} fit={fit_s:.1f}s (参考 {REF_AP_A1:.10f})")
    ap_drift = ap_a1 - REF_AP_A1

    # ---------- 封存逐样本概率 ----------
    val_rows = np.nonzero(val_m)[0]
    y = y_va.astype(np.int64)
    ap_attr, contrib = per_positive_error_attribution(y, scores)
    total_err = 1.0 - ap_a1
    attr_check = float(contrib.sum())
    log(f"逐正类误差归因: AP_attr={ap_attr:.10f} sum(contrib)={attr_check:.10f} vs 1-AP={total_err:.10f}")
    assert abs(ap_attr - ap_a1) < 1e-6, f"归因 AP 与 sklearn AP 不一致: diff={ap_attr - ap_a1}"

    scores_df = pd.DataFrame(
        {
            "window_row_index": wri[val_rows],
            "protected_endpoint_sha256": ep_series.to_numpy()[val_rows],
            "window_start_ns": win_start_ns[val_rows],
            "label": y,
            "score": scores,
            "error_contribution": contrib,
        }
    )
    scores_df.to_parquet(f"{OUT_DIR}/val_scores.parquet", index=False)
    log(f"val_scores.parquet 已封存 {_vm_rss_line()}")

    s_max, s_min = float(scores.max()), float(scores.min())
    val_ep = ep_codes[val_rows]
    val_wri = wri[val_rows]
    val_ns = win_start_ns[val_rows]

    def facet(name_masks: List[Tuple[str, np.ndarray]]) -> List[Dict]:
        return [
            slice_stats(nm, mk, y, scores, contrib, total_err, ap_a1, s_max, s_min)
            for nm, mk in name_masks
        ]

    # ---------- 分面 1：事件位置 ----------
    log("分面 1：事件位置")
    pos_idx = np.nonzero(y == 1)[0]
    order_p = np.lexsort((val_wri[pos_idx], val_ep[pos_idx]))
    p_sorted = pos_idx[order_p]
    ep_s = val_ep[p_sorted]
    wri_s = val_wri[p_sorted]
    new_event = np.ones(len(p_sorted), dtype=bool)
    if len(p_sorted) > 1:
        new_event[1:] = (ep_s[1:] != ep_s[:-1]) | (wri_s[1:] - wri_s[:-1] != 1)
    event_id_sorted = np.cumsum(new_event) - 1
    n_events = int(event_id_sorted[-1]) + 1 if len(p_sorted) else 0
    event_id = np.full(n_va, -1, dtype=np.int64)
    event_id[p_sorted] = event_id_sorted
    ev_len = np.bincount(event_id_sorted, minlength=n_events)
    pos_in_event = np.zeros(len(p_sorted), dtype=np.int64)
    starts = np.nonzero(new_event)[0]
    for st_i, st in enumerate(starts):
        en = starts[st_i + 1] if st_i + 1 < len(starts) else len(p_sorted)
        pos_in_event[st:en] = np.arange(en - st)
    ev_len_per_pos = ev_len[event_id_sorted]
    cat_sorted = np.full(len(p_sorted), "middle", dtype=object)
    cat_sorted[pos_in_event == 0] = "first"
    cat_sorted[pos_in_event == ev_len_per_pos - 1] = "last"
    cat_sorted[ev_len_per_pos == 1] = "single"
    pos_cat = np.full(n_va, "", dtype=object)
    pos_cat[p_sorted] = cat_sorted

    # 事件首窗的前一窗语境（验证首窗真实性）
    first_rows = p_sorted[new_event]
    prev_ctx = {"clean_start": 0, "after_censored": 0, "no_prev_window": 0, "truncated_from_train_positive": 0, "cross_endpoint_or_gap": 0}
    ev_prev_label = np.full(n_events, -9, dtype=np.int64)
    for e_i, r in enumerate(first_rows):
        w_prev = val_wri[r] - 1
        if w_prev < 0 or w_prev > max_wri or pos[w_prev] < 0:
            prev_ctx["no_prev_window"] += 1
            ev_prev_label[e_i] = -9
            continue
        pr = pos[w_prev]
        if ep_codes[pr] != val_ep[r]:
            prev_ctx["cross_endpoint_or_gap"] += 1
            ev_prev_label[e_i] = -9
            continue
        lb = labels[pr]
        ev_prev_label[e_i] = lb
        if lb == 0:
            prev_ctx["clean_start"] += 1
        elif lb == -1:
            prev_ctx["after_censored"] += 1
        else:
            prev_ctx["truncated_from_train_positive"] += 1

    event_masks = [(c, (pos_cat == c) & (y == 1)) for c in ("first", "middle", "last", "single")]
    facet_event = facet(event_masks)

    ev_len_hist = {str(k): int(v) for k, v in zip(*np.unique(ev_len, return_counts=True))}
    log(f"分面 1 完成 {_vm_rss_line()}")

    # ---------- 分面 2：端点流量 5 档 ----------
    log("分面 2：端点流量分档")
    ib = feat_cols.index("win_inbound_bytes_sum")
    ob = feat_cols.index("win_outbound_bytes_sum")
    val_all_rows = np.nonzero(sp_codes == 1)[0]  # 含删失窗
    vol_by_ep = np.zeros(N_ENDPOINTS_EXPECTED, dtype=np.float64)
    bytes_all = (
        np.nan_to_num(F[val_all_rows, ib].astype(np.float64))
        + np.nan_to_num(F[val_all_rows, ob].astype(np.float64))
    )
    np.add.at(vol_by_ep, ep_codes[val_all_rows], bytes_all)
    ep_rank = np.argsort(vol_by_ep)
    quint_of_ep = np.zeros(N_ENDPOINTS_EXPECTED, dtype=np.int64)
    bounds = np.linspace(0, N_ENDPOINTS_EXPECTED, 6).astype(int)
    for qi in range(5):
        quint_of_ep[ep_rank[bounds[qi] : bounds[qi + 1]]] = qi
    vol_masks = []
    for qi in range(5):
        eps_q = np.nonzero(quint_of_ep == qi)[0]
        nm = f"volume_q{qi + 1}_[{vol_by_ep[eps_q].min():.3e},{vol_by_ep[eps_q].max():.3e}]bytes_{len(eps_q)}eps"
        vol_masks.append((nm, np.isin(val_ep, eps_q)))
    facet_volume = facet(vol_masks)
    log(f"分面 2 完成 {_vm_rss_line()}")

    # ---------- 分面 3：数据质量 ----------
    log("分面 3：数据质量")
    miss_cols = [j for j, c in enumerate(feat_cols) if c.endswith("_missing_rate")]
    miss_rate_row = np.nanmean(F[val_rows][:, miss_cols].astype(np.float64), axis=1)
    ha_v = has_act[val_rows]
    ssp_v = ssp[val_rows]
    cec_v = cec[val_rows]
    quality_masks = [
        ("missing_rate=0", miss_rate_row == 0),
        ("missing_rate(0,0.25]", (miss_rate_row > 0) & (miss_rate_row <= 0.25)),
        ("missing_rate(0.25,0.75]", (miss_rate_row > 0.25) & (miss_rate_row <= 0.75)),
        ("missing_rate(0.75,1]", miss_rate_row > 0.75),
        ("has_activity=1", ha_v == 1),
        ("has_activity=0", ha_v == 0),
        ("sec_since_prev_active<=5", ssp_v <= 5),
        ("sec_since_prev_active(5,60]", (ssp_v > 5) & (ssp_v <= 60)),
        ("sec_since_prev_active(60,600]", (ssp_v > 60) & (ssp_v <= 600)),
        ("sec_since_prev_active>600", ssp_v > 600),
        ("sec_since_prev_active=NaN", np.isnan(ssp_v)),
        ("consec_empty=0", cec_v == 0),
        ("consec_empty[1,2]", (cec_v >= 1) & (cec_v <= 2)),
        ("consec_empty[3,11]", (cec_v >= 3) & (cec_v <= 11)),
        ("consec_empty>=12", cec_v >= 12),
    ]
    facet_quality = facet(quality_masks)
    log(f"分面 3 完成 {_vm_rss_line()}")

    # ---------- 分面 4：时间位置 5 段 ----------
    log("分面 4：时间位置")
    t_lo, t_hi = val_ns.min(), val_ns.max()
    t_edges = np.linspace(t_lo, t_hi + 1, 6)
    time_masks = []
    for ti in range(5):
        mk = (val_ns >= t_edges[ti]) & (val_ns < t_edges[ti + 1])
        time_masks.append((f"time_seg{ti + 1}", mk))
    facet_time = facet(time_masks)
    log(f"分面 4 完成 {_vm_rss_line()}")

    # ---------- 分面 5：固定误报预算召回曲线 ----------
    log("分面 5：误报预算召回")
    n_val_all = len(val_all_rows)  # 含删失
    ep_hours_all = n_val_all * WINDOW_SECONDS / 3600.0
    ep_hours_evaluable = n_va * WINDOW_SECONDS / 3600.0
    neg_scores = np.sort(scores[y == 0])[::-1]
    n_neg_total = len(neg_scores)
    budget_rows = []
    thr_at_budget: Dict[float, float] = {}
    for r in FP_BUDGETS:
        allowed = int(np.floor(r * ep_hours_all))
        if allowed <= 0:
            thr = float(np.nextafter(neg_scores[0], np.inf))
        elif allowed >= n_neg_total:
            thr = float(np.nextafter(neg_scores[-1], -np.inf))
        else:
            thr = float(neg_scores[allowed - 1])
        det = scores >= thr
        actual_fp = int((det & (y == 0)).sum())
        tp = int((det & (y == 1)).sum())
        win_recall = tp / int(y.sum())
        det_events = np.unique(event_id[det & (y == 1)])
        event_recall = len(det_events) / n_events if n_events else None
        thr_at_budget[r] = thr
        budget_rows.append(
            {
                "budget_fp_per_endpoint_hour": r,
                "allowed_fp_total": allowed,
                "threshold": thr,
                "actual_fp": actual_fp,
                "actual_fp_per_endpoint_hour": actual_fp / ep_hours_all,
                "window_recall": win_recall,
                "missed_positive_windows": int(y.sum()) - tp,
                "event_recall": event_recall,
                "missed_events": (n_events - len(det_events)) if n_events else None,
                "precision_at_threshold": tp / max(tp + actual_fp, 1),
            }
        )

    # 各事件位置组在各预算下的召回与漏报
    event_budget = {}
    for c in ("first", "middle", "last", "single"):
        mk = (pos_cat == c) & (y == 1)
        n_c = int(mk.sum())
        row = {"n_pos": n_c, "mean_score": float(scores[mk].mean()) if n_c else None}
        for r in FP_BUDGETS:
            det = scores[mk] >= thr_at_budget[r]
            row[f"recall@{r}fp_eph"] = float(det.mean()) if n_c else None
            row[f"missed@{r}fp_eph"] = int(n_c - det.sum())
        event_budget[c] = row

    # 漏报正类中首窗/单窗占比（预算 1.0）
    missed_mask = (y == 1) & (scores < thr_at_budget[1.0])
    missed_comp = {c: int(((pos_cat == c) & missed_mask).sum()) for c in ("first", "middle", "last", "single")}
    log(f"分面 5 完成 {_vm_rss_line()}")

    # ---------- 误差集中度 ----------
    log("误差集中度")
    all_slices = (
        [("event_position:" + s["slice"], s) for s in facet_event]
        + [("endpoint_volume:" + s["slice"], s) for s in facet_volume]
        + [("data_quality:" + s["slice"], s) for s in facet_quality]
        + [("time_position:" + s["slice"], s) for s in facet_time]
    )
    ranked = sorted(
        (
            {
                "slice": nm,
                "n_pos": s["n_pos"],
                "error_contribution_share": s["error_contribution_share"],
                "delta_ap_fix_pos": s["delta_ap_fix_pos"],
                "delta_ap_fix_both": s["delta_ap_fix_both"],
            }
            for nm, s in all_slices
        ),
        key=lambda x: -(x["error_contribution_share"] or 0),
    )
    eligible = [r for r in ranked if r["n_pos"] >= 200]
    top = eligible[0] if eligible else None
    max_share = top["error_contribution_share"] if top else 0.0
    if top and max_share >= 0.40:
        concentration_verdict = "attributable_target_exists"
        verdict_text = (
            f"存在可归因靶子：切片 {top['slice']} 占总误差 {max_share:.1%}（正类 {top['n_pos']}），"
            f"该切片做到完美对应 Delta_AP={top['delta_ap_fix_both']:.6f}"
        )
    elif max_share < 0.25:
        concentration_verdict = "no_attributable_target"
        verdict_text = f"无可归因靶子：最大合格切片贡献 {max_share:.1%} < 25%，误差近似均匀散布"
    else:
        concentration_verdict = "partially_concentrated"
        verdict_text = f"部分集中：最大合格切片 {top['slice']} 贡献 {max_share:.1%} ∈ [25%,40%)"

    result = {
        "purpose": "任务 A：A1 强树（lag0..4 展平 XGBoost）验证集残余误差解剖",
        "contract_version": manifest["contract_version"],
        "contract_sha256": manifest["contract_sha256"],
        "a1_retrain": {
            "validation_average_precision": ap_a1,
            "validation_roc_auc": auc_a1,
            "reference_ap_a1": REF_AP_A1,
            "ap_drift_vs_reference": ap_drift,
            "fit_seconds": fit_s,
            "total_error_1_minus_ap": total_err,
            "attribution_sum_check": attr_check,
        },
        "event_definition": {
            "rule": "验证集内同 protected_endpoint 且 window_row_index 连续的 label=1 极大段",
            "n_events": n_events,
            "n_positive_windows": int(y.sum()),
            "event_length_histogram": ev_len_hist,
            "first_window_prev_context": prev_ctx,
        },
        "facet_1_event_position": {
            "slices": facet_event,
            "per_budget_recall": event_budget,
            "missed_positive_composition_at_1fp_eph": missed_comp,
        },
        "facet_2_endpoint_volume_quintiles": {"slices": facet_volume},
        "facet_3_data_quality": {"slices": facet_quality},
        "facet_4_time_position": {
            "slices": facet_time,
            "val_window_start_ns_range": [int(t_lo), int(t_hi)],
        },
        "facet_5_fp_budget_curve": {
            "endpoint_hours_basis_all_val_windows": ep_hours_all,
            "endpoint_hours_basis_evaluable_only": ep_hours_evaluable,
            "n_val_windows_all_including_censored": n_val_all,
            "caveat": "删失窗(label=-1)无法计入 FP 统计，监控时长按全部验证窗计算",
            "curve": budget_rows,
        },
        "facet_6_error_concentration": {
            "ranked_slices_top15": ranked[:15],
            "max_eligible_slice": top,
            "max_eligible_share": max_share,
            "preregistered_verdict": concentration_verdict,
            "preregistered_verdict_text": verdict_text,
        },
        "total_wall_seconds": time.time() - t_start,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
    }
    with open(f"{OUT_DIR}/result.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    log(f"result.json 已写出 verdict={concentration_verdict} {_vm_rss_line()}")
    log("DONE")


if __name__ == "__main__":
    main()
