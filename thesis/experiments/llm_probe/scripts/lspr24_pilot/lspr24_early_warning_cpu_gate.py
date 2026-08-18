# -*- coding: utf-8 -*-
"""LSPR24 早期预警 B 子任务 CPU 可学习性门（四档：C0 / C0b / C1 / C2）。

先修正 gate-0 遗留的子段边界问题：
- 合同 lspr24-screen-6-2-2-v1 的切分键（tools/lspr24_g0/src/screen/wide.rs
  ActivitySplit::from_active_windows）是「去重后的活动窗口起始时间集合」
  （BTreeSet<window_start_ns>，仅含至少分配到一个受保护端点的流所在窗口），
  排序后取整数下标 values[len*60/100] 作为 validation_start_ns。
- 因此 [0,40%)/[40%,50%)/[50%,60%) 子段边界应取该序列的
  values[len*40/100] 与 values[len*50/100]（活动键边界），
  而非 gate-0 使用的 train 内 window_start_ns 行分位 2/3、5/6。
- 本脚本先核验活动键推导能精确复现合同 train/validation 边界，
  再在两套边界下分别报告锚点普查，最后用活动键边界跑四档门。

四档（全部只用 label∈{0,1} 的合法锚点；训练 seg0，评价 seg2，seg1 仅诊断）：
- C0  常数：预测恒为训练段底率（AP 数学上等于评价段底率）。
- C0b 离散时间风险：只用时间协变量
      （seconds_since_previous_active_window、consecutive_empty_window_count、
        端点内窗口序号）的 XGBoost，同预算。
- C1  当前窗 XGBoost：锚点当前窗 408 个 win_* 特征。
- C2  XGBoost+手工因果历史：408 当前窗 + lag1..4 展平 + 4 命中掩码 = 2044 列，
      连接逻辑复用 a1_history_ceiling.py（temporal-relations lag<=4，
      按 (target,lag) 去重，禁止跨端点/跨 split，零填充+掩码）。

预注册裁决（按实测底率换算）：
- 主判据：(AP_C2 - AP_C1) / (1 - AP_C1) >= 0.02
- 辅助判据：AP_C2 - AP_C1 >= 5 × seg2 实测底率
- 两个判据都不过 → 停掉未来预测支路，不启动神经模型。
- 同时报告 C1 相对 C0/C0b 的增量，判断任务本身是否可学。

内存纪律（2026-08-12 服务器 C56 容器内存耗尽重启后补齐，参见
.Codex/docs/RWKV/2026-08-12-跨年度恶意质量保护部分传输-Q0实施与运行报告.md
同批事故记录）：
- 容器 cgroup 上限（/sys/fs/cgroup/memory.max）与 `free`/psutil 报的宿主机
  数值不一致（本次实测相差约 8.4 倍），禁止用 free/psutil 判断可用内存。
- 408 维特征矩阵与 C2 展平矩阵按 row group / 子段分批构建，避免整表 Arrow
  副本与 numpy 副本、或多段展平矩阵同时驻留内存。
- 每次大分配前用 cgroup 上限核算「所需字节 × 1.3 安全系数」是否超出可用
  内存，超出则主动 raise 退出，而不是被容器 OOM Kill。

screening_only=true, formal_paper_evidence=false, final_accessed=false。
"""
import gc
import json
import os
import time

import numpy as np
import pyarrow.compute as pc
import pyarrow.parquet as pq
import xgboost as xgb
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-prepared/lspr24-screen-wide-v1"
OUT_DIR = (
    "/root/autodl-tmp/thesis/experiments/llm_probe/runs/candidates/lspr24-early-warning-cpu-gate-v1"
)
WIN_NS = 5_000_000_000
K = 4
G_EVENT = 1
LAGS = (1, 2, 3, 4)
SEED = 42
DEVICE = os.environ.get("XGB_DEVICE", "cpu")
GIB = 1024.0**3
MEM_SAFETY_FACTOR = 1.3

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
    "device": DEVICE,
    "seed": SEED,
    "eval_metric": "aucpr",
}
NUM_ROUND = 800

T0 = time.time()


def log(msg: str) -> None:
    print(f"[{time.time() - T0:8.1f}s] {msg}", flush=True)


# ---------- 内存自检（容器 cgroup 口径，禁止 free/psutil） ----------


def _read_cgroup_memory() -> tuple[int, int]:
    """读取 cgroup 内存上限与当前用量（字节）。

    优先 cgroup v2（memory.max / memory.current），失败回退 v1
    （memory.limit_in_bytes / memory.usage_in_bytes）。禁止使用
    free/`/proc/meminfo`/psutil.virtual_memory()：它们在容器内报告的是宿主机
    数值，2026-08-12 事故实测两者相差约 8.4 倍，会造成乐观误判。
    """
    v2_max = "/sys/fs/cgroup/memory.max"
    v2_cur = "/sys/fs/cgroup/memory.current"
    v1_lim = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
    v1_use = "/sys/fs/cgroup/memory/memory.usage_in_bytes"
    try:
        with open(v2_max) as f:
            raw_limit = f.read().strip()
        with open(v2_cur) as f:
            usage = int(f.read().strip())
        if raw_limit != "max":
            return int(raw_limit), usage
    except (FileNotFoundError, ValueError, OSError):
        pass
    try:
        with open(v1_lim) as f:
            limit = int(f.read().strip())
        with open(v1_use) as f:
            usage = int(f.read().strip())
        return limit, usage
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise RuntimeError(
            "无法读取 cgroup 内存上限（v2 memory.max 为 max 且 v1 回退失败），"
            "禁止回退 free/psutil 判断容器可用内存"
        ) from exc


def _read_process_rss_bytes() -> int:
    """读取当前进程 VmRSS（字节），来自 /proc/self/status。"""
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                kb = int(line.split()[1])
                return kb * 1024
    raise RuntimeError("/proc/self/status 中未找到 VmRSS 行")


def log_memory_state(tag: str) -> None:
    """记录当前 cgroup 用量与进程 RSS，供事后核对内存轨迹。"""
    limit, usage = _read_cgroup_memory()
    rss = _read_process_rss_bytes()
    log(
        f"[mem:{tag}] cgroup上限={limit / GIB:.2f}GiB 已用={usage / GIB:.2f}GiB "
        f"可用={(limit - usage) / GIB:.2f}GiB 进程VmRSS={rss / GIB:.2f}GiB"
    )


def check_memory_budget(desc: str, needed_bytes: int) -> None:
    """大分配前的内存守卫。

    可用内存不足 `所需字节 * MEM_SAFETY_FACTOR` 时主动 raise 退出，避免被
    容器 OOM Kill 而不留下任何诊断信息。
    """
    limit, usage = _read_cgroup_memory()
    available = limit - usage
    needed_with_margin = needed_bytes * MEM_SAFETY_FACTOR
    log(
        f"即将分配 {desc}: 所需 {needed_bytes / GIB:.2f}GiB，"
        f"容器可用 {available / GIB:.2f}GiB"
        f"（含 {MEM_SAFETY_FACTOR}x 安全系数需 {needed_with_margin / GIB:.2f}GiB）"
    )
    if available < needed_with_margin:
        raise RuntimeError(
            f"内存预算不足，主动退出以避免 OOM Kill：{desc} 需要 "
            f"{needed_bytes / GIB:.2f}GiB（含安全系数 {needed_with_margin / GIB:.2f}GiB），"
            f"容器仅剩 {available / GIB:.2f}GiB 可用"
            f"（cgroup 上限 {limit / GIB:.2f}GiB，已用 {usage / GIB:.2f}GiB）"
        )


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    log(f"device={DEVICE}")
    log_memory_state("startup")

    with open(f"{ROOT}/dataset-manifest.json") as f:
        manifest = json.load(f)
    feat_cols = manifest["model_feature_columns"]
    assert len(feat_cols) == 408, f"特征列数 {len(feat_cols)} != 408"

    # ---------- 1. 读取宽表元数据列 + 标签 ----------
    log("读取 development-wide.parquet 元数据列")
    meta = pq.read_table(
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
    n = meta.num_rows
    assert n == 7946899, f"宽表行数 {n} != 7946899"
    wri = meta.column("window_row_index").to_numpy().astype(np.int64)
    ws_raw = meta.column("window_start_ns").to_numpy().astype(np.int64)
    ep_dict = pc.dictionary_encode(meta.column("protected_endpoint_sha256").combine_chunks())
    ep_raw = ep_dict.indices.to_numpy().astype(np.int64)
    n_endpoints = len(ep_dict.dictionary)
    split_dict = pc.dictionary_encode(meta.column("split_name").combine_chunks())
    split_codes_raw = split_dict.indices.to_numpy()
    split_names = split_dict.dictionary.to_pylist()
    act_raw = meta.column("has_activity").to_numpy(zero_copy_only=False).astype(bool)
    sspaw_raw = (
        meta.column("seconds_since_previous_active_window")
        .to_numpy(zero_copy_only=False)
        .astype(np.float32)
    )
    cewc_raw = (
        meta.column("consecutive_empty_window_count")
        .to_numpy(zero_copy_only=False)
        .astype(np.float32)
    )
    del meta, ep_dict, split_dict
    gc.collect()
    log(f"端点数={n_endpoints}, split 取值={split_names}")

    lab_tbl = pq.read_table(f"{ROOT}/development-labels.parquet")
    lab_wri = lab_tbl.column("window_row_index").to_numpy().astype(np.int64)
    lab_val = lab_tbl.column("label").to_numpy().astype(np.int64)
    del lab_tbl
    gc.collect()
    assert wri.min() == 0 and wri.max() == n - 1 and len(np.unique(wri)) == n
    lab_row = np.empty(n, dtype=np.int64)
    lab_row[lab_wri] = lab_val
    label_raw = lab_row[wri]
    lbl_counts = {int(v): int(c) for v, c in zip(*np.unique(label_raw, return_counts=True))}
    assert lbl_counts == {-1: 4800524, 0: 3018069, 1: 128306}, f"标签分布 {lbl_counts} 与合同不符"
    log(f"标签分布={lbl_counts}")
    log_memory_state("阶段1-元数据与标签载入完成")

    train_code = split_names.index("train")
    is_train_raw = split_codes_raw == train_code
    val_min = int(ws_raw[~is_train_raw].min())
    train_max = int(ws_raw[is_train_raw].max())

    # ---------- 2. 合同切分键核验与新边界推导 ----------
    log("核验合同切分键（去重活动窗口起始时间 + 整数下标）")
    active_starts = np.unique(ws_raw[act_raw])
    n_act = len(active_starts)
    b60_derived = int(active_starts[n_act * 60 // 100])
    key_verified = b60_derived == val_min
    log(
        f"活动窗起始去重数={n_act}, 推导60%边界={b60_derived}, "
        f"validation_min={val_min}, train_max={train_max}, 核验={'通过' if key_verified else '失败'}"
    )
    b40_new = int(active_starts[n_act * 40 // 100])
    b50_new = int(active_starts[n_act * 50 // 100])
    log(f"活动键边界: b40={b40_new}, b50={b50_new}")

    # ---------- 3. 排序 (endpoint, window_start_ns)，复现 gate-0 结构 ----------
    log("排序 (endpoint, window_start_ns)")
    order = np.lexsort((ws_raw, ep_raw))
    ep = ep_raw[order]
    ws = ws_raw[order]
    label = label_raw[order]
    is_train = is_train_raw[order]
    sspaw = sspaw_raw[order]
    cewc = cewc_raw[order]

    same_ep = ep[1:] == ep[:-1]
    diffs = ws[1:] - ws[:-1]
    grid_viol = int(np.count_nonzero(same_ep & (diffs != WIN_NS)))
    assert grid_viol == 0, "宽表网格存在非 5 秒违约，与 gate-0 结论矛盾"
    contig_prev = np.zeros(n, dtype=bool)
    contig_prev[1:] = same_ep & (diffs == WIN_NS)

    # gate-0 旧边界（train 内行分位 2/3、5/6），用于对照
    train_ws = ws[is_train]
    t40_old = int(np.quantile(train_ws, 2.0 / 3.0, method="higher"))
    t50_old = int(np.quantile(train_ws, 5.0 / 6.0, method="higher"))
    log(f"gate-0 行分位边界: t40={t40_old}, t50={t50_old}")
    log_memory_state("阶段3-排序完成")

    def make_seg(b40: int, b50: int) -> np.ndarray:
        seg = np.full(n, -1, dtype=np.int8)
        seg[is_train & (ws < b40)] = 0
        seg[is_train & (ws >= b40) & (ws < b50)] = 1
        seg[is_train & (ws >= b50)] = 2
        return seg

    seg_new = make_seg(b40_new, b50_new)
    seg_old = make_seg(t40_old, t50_old)

    # ---------- 4. 事件合并（全局，段无关），供独立前体簇 ----------
    log("扫描正类连续段与事件（G_event=1）")
    is_pos = label == 1
    kn = np.isin(label, (0, 1))
    prev_pos = np.zeros(n, dtype=bool)
    prev_pos[1:] = is_pos[:-1]
    run_start_mask = is_pos & ~(prev_pos & contig_prev)
    next_pos = np.zeros(n, dtype=bool)
    next_pos[:-1] = is_pos[1:]
    contig_next = np.zeros(n, dtype=bool)
    contig_next[:-1] = contig_prev[1:]
    run_end_mask = is_pos & ~(next_pos & contig_next)
    run_starts = np.flatnonzero(run_start_mask)
    run_ends = np.flatnonzero(run_end_mask)
    assert len(run_starts) == len(run_ends)
    events = []
    for s_i, e_i in zip(run_starts.tolist(), run_ends.tolist()):
        if events:
            ps, pe = events[-1]
            gap = s_i - pe - 1
            if (
                0 <= gap <= G_EVENT
                and ep[s_i] == ep[pe]
                and ws[s_i] - ws[pe] == (s_i - pe) * WIN_NS
                and (gap == 0 or bool(np.all(label[pe + 1 : s_i] == 0)))
            ):
                events[-1][1] = e_i
                continue
        events.append([s_i, e_i])
    evt_id = np.full(n, -1, dtype=np.int64)
    for k_i, (s_i, e_i) in enumerate(events):
        evt_id[s_i : e_i + 1] = k_i
    log(f"正类连续段={len(run_starts)}, 合并后事件={len(events)}")

    # ---------- 5. K=4 后继链（段无关部分） ----------
    log("构造 K=4 后继链")
    ok_all = np.ones(n, dtype=bool)
    known_all = kn.copy()
    d = np.zeros(n, dtype=np.int8)
    for j in range(K, 0, -1):
        ok_j = np.zeros(n, dtype=bool)
        ok_j[: n - j] = (ep[j:] == ep[:-j]) & (ws[j:] - ws[:-j] == j * WIN_NS)
        kn_j = np.zeros(n, dtype=bool)
        kn_j[: n - j] = kn[j:]
        pos_j = np.zeros(n, dtype=bool)
        pos_j[: n - j] = is_pos[j:]
        ok_all &= ok_j
        known_all &= kn_j
        d[pos_j] = j

    def anchors_for(seg: np.ndarray) -> dict:
        seg_k = np.full(n, -2, dtype=np.int8)
        seg_k[: n - K] = seg[K:]
        chain_same_seg = seg_k == seg
        anchor_valid = (label == 0) & ok_all & known_all & (seg >= 0) & chain_same_seg
        anchor_pos = anchor_valid & (d > 0)
        stats = {}
        for s in (0, 1, 2):
            m_valid = anchor_valid & (seg == s)
            m_pos = anchor_pos & (seg == s)
            n_valid = int(np.count_nonzero(m_valid))
            n_pos = int(np.count_nonzero(m_pos))
            idx_pos = np.flatnonzero(m_pos)
            first_pos_idx = idx_pos + d[idx_pos].astype(np.int64)
            clusters = np.unique(evt_id[first_pos_idx])
            assert not np.any(clusters < 0)
            stats[s] = {
                "anchors_valid": n_valid,
                "anchors_positive": n_pos,
                "base_rate": (n_pos / n_valid) if n_valid else None,
                "first_positive_step_hist": {
                    int(j): int(np.count_nonzero(m_pos & (d == j))) for j in range(1, K + 1)
                },
                "independent_precursor_clusters": int(len(clusters)),
                "windows_in_segment": int(np.count_nonzero(seg == s)),
            }
        return {"stats": stats, "anchor_valid": anchor_valid, "anchor_pos": anchor_pos}

    log("锚点普查：活动键新边界")
    res_new = anchors_for(seg_new)
    log("锚点普查：gate-0 行分位旧边界（对照）")
    res_old = anchors_for(seg_old)
    for s in (0, 1, 2):
        nnew, nold = res_new["stats"][s], res_old["stats"][s]
        log(
            f"seg{s}: 新 合法={nnew['anchors_valid']} 正={nnew['anchors_positive']} "
            f"簇={nnew['independent_precursor_clusters']} | 旧 合法={nold['anchors_valid']} "
            f"正={nold['anchors_positive']} 簇={nold['independent_precursor_clusters']}"
        )

    gate_b_new = {
        "thresholds": {
            "seg0_pos_anchors": 512,
            "seg1_pos_anchors": 128,
            "seg2_pos_anchors": 128,
            "clusters_each": 10,
        },
        "measured_pos_anchors": {s: res_new["stats"][s]["anchors_positive"] for s in (0, 1, 2)},
        "measured_clusters": {
            s: res_new["stats"][s]["independent_precursor_clusters"] for s in (0, 1, 2)
        },
    }
    gate_b_new["pass"] = (
        res_new["stats"][0]["anchors_positive"] >= 512
        and res_new["stats"][1]["anchors_positive"] >= 128
        and res_new["stats"][2]["anchors_positive"] >= 128
        and all(res_new["stats"][s]["independent_precursor_clusters"] >= 10 for s in (0, 1, 2))
    )
    log(f"新边界 gate_b pass={gate_b_new['pass']}")

    # ---------- 6. 历史连接（复用 a1_history_ceiling.py 逻辑） ----------
    log("流式扫描 temporal-relations.parquet 提取 lag<=4 关系")
    max_wri = int(wri.max())
    pos_map = np.full(max_wri + 1, -1, dtype=np.int64)
    pos_map[wri] = np.arange(n, dtype=np.int64)
    hist_wri = np.full((n, len(LAGS)), -1, dtype=np.int64)
    conflict_count = 0
    rel_rows_scanned = 0
    rel_rows_lag14 = 0
    pf = pq.ParquetFile(f"{ROOT}/temporal-relations.parquet")
    for rg in range(pf.metadata.num_row_groups):
        tbl = pf.read_row_group(
            rg, columns=["target_window_row_index", "lag", "history_window_row_index"]
        )
        lag_arr = tbl["lag"].to_numpy().astype(np.int64)
        rel_rows_scanned += len(lag_arr)
        keep = lag_arr <= 4
        if not keep.any():
            continue
        tgt = tbl["target_window_row_index"].to_numpy().astype(np.int64)[keep]
        hst = tbl["history_window_row_index"].to_numpy().astype(np.int64)[keep]
        lg = lag_arr[keep]
        rel_rows_lag14 += len(lg)
        tpos = pos_map[tgt]
        assert (tpos >= 0).all()
        for k_i, k in enumerate(LAGS):
            m = lg == k
            if not m.any():
                continue
            tp, hv = tpos[m], hst[m]
            prev = hist_wri[tp, k_i]
            bad = (prev != -1) & (prev != hv)
            conflict_count += int(bad.sum())
            hist_wri[tp, k_i] = hv
        del tbl
    assert rel_rows_scanned == 420587899, "relations 总行数与合同不符"
    assert conflict_count == 0, "同一(target,lag)出现不一致 history"
    log(f"relations 扫描完成: lag<=4 行 {rel_rows_lag14}, 冲突 {conflict_count}")

    log("构建历史行位置与掩码（禁止跨端点/跨切分）")
    has_rel = hist_wri >= 0
    hist_pos = np.where(has_rel, pos_map[np.clip(hist_wri, 0, max_wri)], -1)
    in_dev = has_rel & (hist_pos >= 0)
    tgt_rows = np.arange(n, dtype=np.int64)
    mask_hist = np.zeros((n, len(LAGS)), dtype=bool)
    stats_cross_ep = 0
    stats_cross_sp = 0
    for k_i in range(len(LAGS)):
        hp = hist_pos[:, k_i]
        v = in_dev[:, k_i]
        same_e = np.zeros(n, dtype=bool)
        same_s = np.zeros(n, dtype=bool)
        same_e[v] = ep_raw[hp[v]] == ep_raw[tgt_rows[v]]
        same_s[v] = is_train_raw[hp[v]] == is_train_raw[tgt_rows[v]]
        stats_cross_ep += int((v & ~same_e).sum())
        stats_cross_sp += int((v & same_e & ~same_s).sum())
        mask_hist[:, k_i] = v & same_e & same_s
    assert stats_cross_ep == 0, "relations 存在跨端点连接"
    log(f"掩码统计: 跨端点剔除 {stats_cross_ep}, 跨切分剔除 {stats_cross_sp}")
    log_memory_state("阶段6-历史连接完成")

    # 子段归属（file-order 域）
    seg_orig = np.empty(n, dtype=np.int8)
    seg_orig[order] = seg_new

    # ---------- 7. 特征矩阵（按 row group 分批读取，避免整表 Arrow 副本与
    #               numpy 副本同时驻留） ----------
    log("载入 408 维特征矩阵 (float32，按 row group 分批读取)")
    t0 = time.time()
    dfeat = len(feat_cols)
    f_needed_bytes = n * dfeat * 4
    check_memory_budget(f"F 特征矩阵 ({n}x{dfeat} float32)", f_needed_bytes)
    F = np.empty((n, dfeat), dtype=np.float32)
    pf_feat = pq.ParquetFile(f"{ROOT}/development-wide.parquet")
    n_row_groups = pf_feat.metadata.num_row_groups
    row_offset = 0
    for rg in range(n_row_groups):
        rg_rows = pf_feat.metadata.row_group(rg).num_rows
        tbl_rg = pf_feat.read_row_group(rg, columns=feat_cols)
        assert (
            tbl_rg.num_rows == rg_rows
        ), f"row group {rg} 元数据行数 {rg_rows} 与实读行数 {tbl_rg.num_rows} 不符"
        for j, c in enumerate(feat_cols):
            F[row_offset : row_offset + rg_rows, j] = (
                tbl_rg[c].to_numpy(zero_copy_only=False).astype(np.float32)
            )
        row_offset += rg_rows
        del tbl_rg
        gc.collect()
    assert row_offset == n, f"row group 累计行数 {row_offset} != {n}"
    log(f"特征载入完成 {time.time() - t0:.1f}s，共 {n_row_groups} 个 row group")
    log_memory_state("阶段7-特征矩阵载入完成")

    # 端点内窗口序号（排序域，因果：端点首个物化窗为参照）
    ep_first = np.zeros(n, dtype=np.int64)
    block_start = np.r_[True, ep[1:] != ep[:-1]]
    first_ws = ws[block_start]
    ep_first = np.repeat(first_ws, np.diff(np.r_[np.flatnonzero(block_start), n]))
    ep_rank = ((ws - ep_first) // WIN_NS).astype(np.float32)

    anchor_valid = res_new["anchor_valid"]
    y_all = res_new["anchor_pos"].astype(np.float32)

    seg_rows = {}  # 排序域下标
    for s in (0, 1, 2):
        seg_rows[s] = np.flatnonzero(anchor_valid & (seg_new == s))

    cross_subseg_hist = {}
    for s in (0, 1, 2):
        rows_orig = order[seg_rows[s]]
        cnt = 0
        for k_i in range(len(LAGS)):
            hp = hist_pos[rows_orig, k_i]
            mk = mask_hist[rows_orig, k_i]
            cnt += int(np.count_nonzero(mk & (seg_orig[hp] != s)))
        cross_subseg_hist[s] = cnt
    log(f"锚点历史跨子段计数（同 split 内，允许并计数）={cross_subseg_hist}")

    def matrix_c0b(rows_sorted: np.ndarray) -> np.ndarray:
        X = np.empty((len(rows_sorted), 3), dtype=np.float32)
        X[:, 0] = sspaw[rows_sorted]
        X[:, 1] = cewc[rows_sorted]
        X[:, 2] = ep_rank[rows_sorted]
        return X

    def matrix_c1(rows_sorted: np.ndarray) -> np.ndarray:
        return F[order[rows_sorted]]

    def matrix_c2(rows_sorted: np.ndarray) -> np.ndarray:
        rows_orig = order[rows_sorted]
        m = len(rows_orig)
        X = np.zeros((m, dfeat * 5 + len(LAGS)), dtype=np.float32)
        X[:, :dfeat] = F[rows_orig]
        for k_i in range(len(LAGS)):
            hp = hist_pos[rows_orig, k_i]
            mk = mask_hist[rows_orig, k_i]
            blk = X[:, dfeat * (k_i + 1) : dfeat * (k_i + 2)]
            sel = np.nonzero(mk)[0]
            blk[sel] = F[hp[sel]]
            X[:, dfeat * 5 + k_i] = mk.astype(np.float32)
        return X

    y_tr = y_all[seg_rows[0]]
    y_s1 = y_all[seg_rows[1]]
    y_s2 = y_all[seg_rows[2]]
    y_by_seg = {0: y_tr, 1: y_s1, 2: y_s2}
    base0 = float(y_tr.mean())
    base1 = float(y_s1.mean()) if len(y_s1) else None
    base2 = float(y_s2.mean())
    log(
        f"锚点数 seg0={len(y_tr)}(正{int(y_tr.sum())}) seg1={len(y_s1)}(正{int(y_s1.sum())}) "
        f"seg2={len(y_s2)}(正{int(y_s2.sum())}); 底率 seg0={base0:.9f} seg2={base2:.9f}"
    )

    tiers = {}

    # C0 常数
    p2_const = np.full(len(y_s2), base0, dtype=np.float64)
    p1_const = np.full(len(y_s1), base0, dtype=np.float64)
    tiers["C0_constant"] = {
        "description": "预测恒为训练段(seg0)实测底率；AP 数学上等于评价段底率",
        "train_base_rate_seg0": base0,
        "seg2_average_precision": float(average_precision_score(y_s2, p2_const)),
        "seg1_average_precision": (
            float(average_precision_score(y_s1, p1_const)) if len(y_s1) else None
        ),
        "n_features": 0,
    }
    log(f"C0 AP_seg2={tiers['C0_constant']['seg2_average_precision']:.10f}")

    def fit_tier(tag: str, build, n_feat_desc: str, n_cols: int) -> dict:
        """逐段构建矩阵并立即转换为 QuantileDMatrix。

        不同时持有 seg0/seg1/seg2 的完整展平矩阵：每段构建 -> 转
        QuantileDMatrix -> del 稠密矩阵 -> gc.collect() 后才构建下一段，
        C2（2044 列）峰值内存从「三段合计约 5.7 GiB」降到「单段最大约
        3.2 GiB（seg2）」。
        """
        log(f"[{tag}] 逐段构建矩阵（不同时持有多段完整展平矩阵）")
        log_memory_state(f"{tag}-开始")
        build_s_total = 0.0
        dm_s_total = 0.0

        def build_dmatrix(seg_label: str, s: int, ref):
            nonlocal build_s_total, dm_s_total
            rows_sorted = seg_rows[s]
            needed = len(rows_sorted) * n_cols * 4
            check_memory_budget(
                f"[{tag}] {seg_label} 矩阵 ({len(rows_sorted)}x{n_cols} float32)", needed
            )
            t0 = time.time()
            X = build(rows_sorted)
            build_s = time.time() - t0
            build_s_total += build_s
            log(f"[{tag}] {seg_label} 矩阵 {X.shape} 构建 {build_s:.1f}s")
            y = y_by_seg[s]
            t0 = time.time()
            if ref is None:
                dm = xgb.QuantileDMatrix(X, label=y, max_bin=256)
            else:
                dm = xgb.QuantileDMatrix(X, label=y, max_bin=256, ref=ref)
            dm_s = time.time() - t0
            dm_s_total += dm_s
            del X
            gc.collect()
            log_memory_state(f"{tag}-{seg_label}-矩阵已释放")
            return dm

        dtrain = build_dmatrix("seg0(train)", 0, None)
        dv2 = build_dmatrix("seg2(eval)", 2, dtrain)
        dv1 = build_dmatrix("seg1(diag)", 1, dtrain)

        log(f"[{tag}] 训练 {NUM_ROUND} 轮")
        t0 = time.time()
        booster = xgb.train(XGB_PARAMS, dtrain, num_boost_round=NUM_ROUND)
        fit_s = time.time() - t0
        p2 = booster.predict(dv2)
        p1 = booster.predict(dv1)
        ap2 = float(average_precision_score(y_s2, p2))
        auc2 = float(roc_auc_score(y_s2, p2))
        ap1 = float(average_precision_score(y_s1, p1)) if len(y_s1) else None
        log(f"[{tag}] AP_seg2={ap2:.10f} AUC_seg2={auc2:.10f} AP_seg1={ap1} fit={fit_s:.1f}s")
        del dtrain, dv2, dv1, booster
        gc.collect()
        log_memory_state(f"{tag}-结束")
        return {
            "description": n_feat_desc,
            "seg2_average_precision": ap2,
            "seg2_roc_auc": auc2,
            "seg1_average_precision": ap1,
            "matrix_build_seconds": build_s_total,
            "dmatrix_seconds": dm_s_total,
            "fit_seconds": fit_s,
        }

    tiers["C0b_discrete_time_hazard"] = fit_tier(
        "C0b",
        matrix_c0b,
        "仅时间协变量: seconds_since_previous_active_window, consecutive_empty_window_count, 端点内窗口序号 (3 列, 同预算 XGBoost)",
        3,
    )
    tiers["C1_current_window"] = fit_tier("C1", matrix_c1, "锚点当前窗 408 个 win_* 特征", dfeat)
    tiers["C2_current_plus_causal_history"] = fit_tier(
        "C2",
        matrix_c2,
        "408 当前窗 + lag1..4 展平 + 4 命中掩码 = 2044 列（复用 a1 连接逻辑）",
        dfeat * 5 + len(LAGS),
    )

    # ---------- 8. 预注册裁决 ----------
    ap_c0 = tiers["C0_constant"]["seg2_average_precision"]
    ap_c0b = tiers["C0b_discrete_time_hazard"]["seg2_average_precision"]
    ap_c1 = tiers["C1_current_window"]["seg2_average_precision"]
    ap_c2 = tiers["C2_current_plus_causal_history"]["seg2_average_precision"]
    rel_gain = (ap_c2 - ap_c1) / (1.0 - ap_c1) if ap_c1 < 1 else float("nan")
    delta = ap_c2 - ap_c1
    aux_threshold = 5.0 * base2
    main_pass = rel_gain >= 0.02
    aux_pass = delta >= aux_threshold
    c1_vs_c0 = ap_c1 - ap_c0
    c1_vs_c0b = ap_c1 - ap_c0b
    task_learnable = ap_c1 > ap_c0 and ap_c1 > ap_c0b

    if not task_learnable:
        verdict = "task_not_learnable"
        verdict_text = "C1 未超过常数/离散时间风险基线：B 任务本身在当前特征下不可学"
    elif main_pass or aux_pass:
        verdict = "c2_history_increment_present"
        verdict_text = (
            "C2 相对 C1 存在独立历史增量（至少一个预注册判据通过），未来预测支路可进入下一步"
        )
    else:
        verdict = "stop_future_prediction_branch"
        verdict_text = (
            "两个预注册判据都未通过：C2 相对 C1 无独立增量，按方案册停掉未来预测支路，"
            "不启动任何神经模型"
        )

    result = {
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "contract": "lspr24-screen-6-2-2-v1",
        "contract_sha256": "715da51fc8b6d95aea20c02722e7555d3b2e574c4844668f3947e83c8c12cbc0",
        "view_root": ROOT,
        "generated_unix": time.time(),
        "params": {"K": K, "G_event": G_EVENT, "window_ns": WIN_NS, "seed": SEED, "device": DEVICE},
        "split_key_audit": {
            "contract_key": "去重活动窗口起始时间集合(BTreeSet<window_start_ns>, 仅含有流窗口), 边界=values[len*p/100]",
            "source": "tools/lspr24_g0/src/screen/wide.rs ActivitySplit::from_active_windows",
            "n_distinct_active_starts": int(n_act),
            "derived_60pct_boundary_ns": b60_derived,
            "contract_validation_min_ns": val_min,
            "contract_train_max_ns": train_max,
            "key_reproduces_contract_boundary": bool(key_verified),
            "new_b40_ns": b40_new,
            "new_b50_ns": b50_new,
            "gate0_row_quantile_t40_ns": t40_old,
            "gate0_row_quantile_t50_ns": t50_old,
            "b40_shift_seconds": (b40_new - t40_old) / 1e9,
            "b50_shift_seconds": (b50_new - t50_old) / 1e9,
        },
        "anchors_new_boundaries": {str(s): res_new["stats"][s] for s in (0, 1, 2)},
        "anchors_gate0_boundaries": {str(s): res_old["stats"][s] for s in (0, 1, 2)},
        "anchor_delta_new_minus_gate0": {
            str(s): {
                "anchors_valid": res_new["stats"][s]["anchors_valid"]
                - res_old["stats"][s]["anchors_valid"],
                "anchors_positive": res_new["stats"][s]["anchors_positive"]
                - res_old["stats"][s]["anchors_positive"],
            }
            for s in (0, 1, 2)
        },
        "gate_b_data_thresholds_new_boundaries": gate_b_new,
        "history_join_assertions": {
            "relations_rows_scanned": rel_rows_scanned,
            "relations_rows_lag_le_4": rel_rows_lag14,
            "target_lag_history_conflicts": conflict_count,
            "cross_endpoint_masked": stats_cross_ep,
            "cross_split_masked": stats_cross_sp,
            "anchor_history_cross_subsegment_count": cross_subseg_hist,
            "anchor_history_cross_subsegment_policy": "允许（因果过去、同 split 内），仅计数",
        },
        "xgboost_params": {k: str(v) for k, v in XGB_PARAMS.items()},
        "num_boost_round": NUM_ROUND,
        "train_segment": "seg0 活动键[0,40%)",
        "eval_segment": "seg2 活动键[50%,60%)",
        "anchor_counts": {
            "seg0": {"n": int(len(y_tr)), "pos": int(y_tr.sum()), "base_rate": base0},
            "seg1": {"n": int(len(y_s1)), "pos": int(y_s1.sum()), "base_rate": base1},
            "seg2": {"n": int(len(y_s2)), "pos": int(y_s2.sum()), "base_rate": base2},
        },
        "tiers": tiers,
        "preregistered_decision": {
            "main_criterion": "(AP_C2-AP_C1)/(1-AP_C1) >= 0.02",
            "main_value": rel_gain,
            "main_pass": bool(main_pass),
            "aux_criterion": "AP_C2-AP_C1 >= 5*seg2底率",
            "aux_threshold": aux_threshold,
            "aux_value": delta,
            "aux_pass": bool(aux_pass),
            "c1_minus_c0": c1_vs_c0,
            "c1_minus_c0b": c1_vs_c0b,
            "task_learnable_c1_beats_baselines": bool(task_learnable),
            "verdict": verdict,
            "verdict_text": verdict_text,
        },
        "total_wall_seconds": time.time() - T0,
    }
    with open(f"{OUT_DIR}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"result.json 已写出; verdict={verdict}")
    log(
        f"AP_C0={ap_c0:.10f} AP_C0b={ap_c0b:.10f} AP_C1={ap_c1:.10f} AP_C2={ap_c2:.10f} "
        f"rel_gain={rel_gain:.6f} delta={delta:.6f} aux_thr={aux_threshold:.6f}"
    )
    log_memory_state("结束")


if __name__ == "__main__":
    main()
