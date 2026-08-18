# -*- coding: utf-8 -*-
"""E1 证伪实验：验证集事件切分对删失窗的敏感性（时间容差重定义）。

背景：A1 误差解剖（a1_error_anatomy_v2.py）报告"1089 个单窗事件（占事件数
71.7%）贡献 57.1% 的误差"，据此推出"误差靶子是历史贫瘠的孤立事件"。事件按
window_row_index 严格 +1 连续切段（原脚本约 473 行），而宽表把时间轴填成
稠密 5 秒栅格，label=-1（删失）占 60.4075%。删失窗可能把本来连续的长事件
切碎，人为制造出大量"单窗事件"——这是本脚本要证伪或证实的怀疑。

只读共享视图与已冻结制品，不重训、不改模型：
- runs/diagnostics/lspr24-a1-error-anatomy-v1/val_scores.parquet（冻结逐窗分数）
- runs/data-prepared/lspr24-screen-wide-v1/development-wide.parquet（仅元数据列）
- runs/data-prepared/lspr24-screen-wide-v1/development-labels.parquet
- runs/data-prepared/lspr24-screen-wide-v1/temporal-relations.parquet（仅 lag<=4）
- runs/data-prepared/lspr24-screen-wide-v1/dataset-manifest.json

产物写 runs/diagnostics/lspr24-a1-event-definition-falsification-v1/。
screening_only=true, formal_paper_evidence=false, final_accessed=false。
不得访问最终封存区（final_split=final-not-materialized，视图中本不存在，
下方对 split_name 唯一值的断言即是该边界的运行时校验）。

内存纪律（沿用 a1_error_anatomy_v2.py 的加固规则）：
- 容器 cgroup 内存上限只从 /sys/fs/cgroup 读取，禁止 free / /proc/meminfo /
  psutil.virtual_memory()。
- 本脚本不加载 408 维特征矩阵（预计峰值 < 6 GiB），只读取元数据列、冻结分数
  与 temporal-relations 的 lag<=4 关系。
"""
import gc
import json
import sys
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# ---------------- 路径 ----------------
DATA_ROOT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-prepared/lspr24-screen-wide-v1"
A1_DIR = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/lspr24-a1-error-anatomy-v1"
OUT_DIR = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/lspr24-a1-event-definition-falsification-v1"

# ---------------- 预注册常量（跑完不得修改） ----------------
SEED = 42
N_BOOTSTRAP = 1000
G_VALUES: Tuple[int, ...] = (0, 1, 2, 4, 8, 12, 24)  # 时间容差，单位：5 秒窗
FP_BUDGETS: Tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)  # 次 / 端点 / 小时
WINDOW_SECONDS = 5.0
N_ENDPOINTS_EXPECTED = 468
N_ROWS_EXPECTED = 7946899
LABEL_DIST_EXPECTED = {-1: 4800524, 0: 3018069, 1: 128306}
N_VA_EXPECTED = 927295
N_VAL_ALL_EXPECTED = 2313382

# G=0 复现门禁：必须逐位匹配 A 线原报告，否则停下报告差异，不继续。
EXPECTED_N_EVENTS_G0 = 1519
EXPECTED_N_SINGLE_G0 = 1089

# 判伪影 / 判真实 / 子判据阈值（预注册，禁止依据结果调整）
ARTIFACT_RATIO_G2 = 0.50
ARTIFACT_CENSORED_SHARE = 0.30
GENUINE_RATIO_G12 = 0.80
GENUINE_CENSORED_SHARE = 0.05
HISTORY_RICHNESS_MEDIAN_GE = 3
PARTIAL_ARTIFACT_SUGGESTED_G = 2  # 部分伪影时冻结的默认 G（与判伪影判据引用同一个 G）

# E3 判据阈值
E3_RECALL_DROP_MINOR = 0.05
E3_RECALL_DROP_MAJOR = 0.10
E3_CI_HALFWIDTH_OK = 0.05
E3_CI_HALFWIDTH_BAD = 0.10

# 参考核对值（来自 A1 result.json，仅用于交叉核验，不参与判据计算）
REF_EVENT_RECALL_AT_001 = 0.532587228439763
REF_EP_HOURS_ALL = 3213.0305555555556
REF_EP_HOURS_EVALUABLE = 1287.9097222222222

NEIGHBOR_CATEGORIES = ("positive", "negative", "censored_active", "empty", "boundary")

_CGROUP_V2_MAX = "/sys/fs/cgroup/memory.max"
_CGROUP_V2_CUR = "/sys/fs/cgroup/memory.current"
_CGROUP_V1_LIMIT = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
_CGROUP_V1_USAGE = "/sys/fs/cgroup/memory/memory.usage_in_bytes"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _read_cgroup_int(path: str):
    with open(path) as f:
        raw = f.read().strip()
    if raw == "max":
        return None
    return int(raw)


def _cgroup_memory_limit_and_usage():
    """读取容器 cgroup 内存上限与当前用量（字节），优先 v2、回退 v1。

    禁止使用 free / /proc/meminfo / psutil.virtual_memory()：容器内这些接口
    报告宿主机总内存而非 cgroup 限额（2026-08-12 曾据此产生 8.4 倍乐观误判）。
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
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except (FileNotFoundError, ValueError, OSError):
        pass
    return -1


def _vm_rss_line() -> str:
    rss = _vm_rss_bytes()
    if rss < 0:
        return "VmRSS=未知"
    return f"VmRSS={rss / (1024 ** 3):.3f}GiB"


def mem_report(label: str) -> Dict:
    """记录一次阶段性内存快照（cgroup 上限/用量 + 当前进程 VmRSS）。"""
    limit, usage = _cgroup_memory_limit_and_usage()
    entry = {"stage": label, "vm_rss": _vm_rss_line()}
    if limit is not None and usage is not None:
        entry["cgroup_limit_gib"] = round(limit / (1024 ** 3), 3)
        entry["cgroup_usage_gib"] = round(usage / (1024 ** 3), 3)
        entry["cgroup_avail_gib"] = round((limit - usage) / (1024 ** 3), 3)
        log(
            f"[内存] {label}: cgroup 上限={entry['cgroup_limit_gib']}GiB "
            f"用量={entry['cgroup_usage_gib']}GiB 可用={entry['cgroup_avail_gib']}GiB "
            f"{entry['vm_rss']}"
        )
    else:
        log(f"[内存] {label}: 无法读取 cgroup 信息 {entry['vm_rss']}")
    return entry


def classify_neighbor(
    w: int, ep_code: int, max_wri: int, ep_codes: np.ndarray, labels: np.ndarray, has_act: np.ndarray
) -> str:
    """把窗口 w（可能不存在）相对锚定端点 ep_code 分类为五类之一。"""
    if w < 0 or w > max_wri:
        return "boundary"
    if ep_codes[w] != ep_code:
        return "boundary"
    lb = int(labels[w])
    if lb == 1:
        return "positive"
    if lb == 0:
        return "negative"
    if lb == -1:
        return "censored_active" if bool(has_act[w]) else "empty"
    raise ValueError(f"未知标签值 {lb} at window_row_index={w}")


def compute_events_for_g(
    ep_sorted: np.ndarray, wri_sorted: np.ndarray, g: int, eligible_prefix: np.ndarray
) -> Tuple[np.ndarray, int, np.ndarray]:
    """按容差 g 合并同端点、间隔 <= g 个窗的正类段为同一事件。

    合并条件（预注册）：同端点 且 gap=wri_cur-wri_prev-1 <= g 且跨越的中间窗
    （若 gap>0）全部满足"验证集内 且 label!=1"（eligible_prefix 的前缀和判定）。
    ep_sorted/wri_sorted 为按 (端点, window_row_index) 升序排好的正类窗口序列。
    """
    n_pos = len(wri_sorted)
    new_event = np.ones(n_pos, dtype=bool)
    if n_pos > 1:
        same_ep = ep_sorted[1:] == ep_sorted[:-1]
        gap = wri_sorted[1:] - wri_sorted[:-1] - 1
        gap_ok = gap <= g
        need_bridge = same_ep & gap_ok & (gap > 0)
        bridge_ok = np.ones(n_pos - 1, dtype=bool)
        idxs = np.nonzero(need_bridge)[0]
        if len(idxs):
            lo = wri_sorted[:-1][idxs] + 1
            hi = wri_sorted[1:][idxs] - 1
            cnt_eligible = eligible_prefix[hi + 1] - eligible_prefix[lo]
            cnt_needed = hi - lo + 1
            bridge_ok[idxs] = cnt_eligible == cnt_needed
        mergeable = same_ep & gap_ok & bridge_ok
        new_event[1:] = ~mergeable
    event_id_sorted = np.cumsum(new_event) - 1
    n_events = int(event_id_sorted[-1]) + 1 if n_pos else 0
    ev_len = np.bincount(event_id_sorted, minlength=n_events) if n_events else np.zeros(0, dtype=np.int64)
    return event_id_sorted, n_events, ev_len


def position_categories(event_id_sorted: np.ndarray, ev_len: np.ndarray) -> np.ndarray:
    """按事件内位置把每个正类窗口标为 first/middle/last/single。"""
    n = len(event_id_sorted)
    cat = np.full(n, "middle", dtype=object)
    if n == 0:
        return cat
    ev_len_per_pos = ev_len[event_id_sorted]
    boundaries = np.nonzero(np.r_[True, event_id_sorted[1:] != event_id_sorted[:-1]])[0]
    pos_in_event = np.zeros(n, dtype=np.int64)
    for i, st in enumerate(boundaries):
        en = boundaries[i + 1] if i + 1 < len(boundaries) else n
        pos_in_event[st:en] = np.arange(en - st)
    cat[pos_in_event == 0] = "first"
    cat[pos_in_event == ev_len_per_pos - 1] = "last"
    cat[ev_len_per_pos == 1] = "single"
    return cat


def compute_threshold(neg_scores_desc: np.ndarray, allowed: int) -> float:
    """与原 a1_error_anatomy_v2.py 完全一致的阈值选取逻辑。"""
    n_neg = len(neg_scores_desc)
    if allowed <= 0:
        return float(np.nextafter(neg_scores_desc[0], np.inf))
    if allowed >= n_neg:
        return float(np.nextafter(neg_scores_desc[-1], -np.inf))
    return float(neg_scores_desc[allowed - 1])


def main() -> None:
    t_start = time.time()
    mem_log: List[Dict] = [mem_report("启动")]

    with open(f"{DATA_ROOT}/dataset-manifest.json") as f:
        manifest = json.load(f)
    assert manifest["training_split"] == "train"
    assert manifest["validation_split"] == "validation"
    assert manifest["final_split"] == "final-not-materialized"

    # ---------- 预注册配置落盘（实现前定的判据，跑完不得修改；此处仅回写供审计） ----------
    config_snapshot = {
        "run_name": "lspr24-a1-event-definition-falsification-v1",
        "purpose": "证伪/证实 A1 误差解剖'单窗事件历史贫瘠'结论是否为验证集删失窗切分伪影",
        "data_sources_read_only": {
            "val_scores": f"{A1_DIR}/val_scores.parquet",
            "development_wide_meta_columns_only": f"{DATA_ROOT}/development-wide.parquet",
            "development_labels": f"{DATA_ROOT}/development-labels.parquet",
            "temporal_relations_lag_le_4": f"{DATA_ROOT}/temporal-relations.parquet",
            "dataset_manifest": f"{DATA_ROOT}/dataset-manifest.json",
        },
        "contract_version": manifest["contract_version"],
        "contract_sha256": manifest["contract_sha256"],
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "G_VALUES": list(G_VALUES),
        "FP_BUDGETS": list(FP_BUDGETS),
        "gate_g0_expected": {"n_events": EXPECTED_N_EVENTS_G0, "n_single": EXPECTED_N_SINGLE_G0},
        "preregistered_thresholds": {
            "ARTIFACT_RATIO_G2": ARTIFACT_RATIO_G2,
            "ARTIFACT_CENSORED_SHARE": ARTIFACT_CENSORED_SHARE,
            "GENUINE_RATIO_G12": GENUINE_RATIO_G12,
            "GENUINE_CENSORED_SHARE": GENUINE_CENSORED_SHARE,
            "HISTORY_RICHNESS_MEDIAN_GE": HISTORY_RICHNESS_MEDIAN_GE,
            "PARTIAL_ARTIFACT_SUGGESTED_G": PARTIAL_ARTIFACT_SUGGESTED_G,
            "E3_RECALL_DROP_MINOR": E3_RECALL_DROP_MINOR,
            "E3_RECALL_DROP_MAJOR": E3_RECALL_DROP_MAJOR,
            "E3_CI_HALFWIDTH_OK": E3_CI_HALFWIDTH_OK,
            "E3_CI_HALFWIDTH_BAD": E3_CI_HALFWIDTH_BAD,
        },
        "reference_values_for_cross_check": {
            "ref_event_recall_at_001": REF_EVENT_RECALL_AT_001,
            "ref_ep_hours_all": REF_EP_HOURS_ALL,
            "ref_ep_hours_evaluable": REF_EP_HOURS_EVALUABLE,
        },
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "not_accessed_final_split": True,
    }
    with open(f"{OUT_DIR}/config.json", "w") as f:
        json.dump(config_snapshot, f, ensure_ascii=False, indent=1)
    log("config.json 已写出")

    # ---------- 阶段 0：加载全量元数据（train+validation，用于邻窗分类与桥接安全检查） ----------
    log("阶段 0：加载全量元数据")
    meta_tbl = pq.read_table(
        f"{DATA_ROOT}/development-wide.parquet",
        columns=["window_row_index", "protected_endpoint_sha256", "split_name", "has_activity"],
    )
    wri = meta_tbl["window_row_index"].to_numpy().astype(np.int64)
    n_rows = len(wri)
    assert n_rows == N_ROWS_EXPECTED, f"n_rows={n_rows} != {N_ROWS_EXPECTED}"
    assert np.array_equal(wri, np.arange(n_rows)), "window_row_index 不是稠密恒等映射，需重新核验桥接逻辑假设"

    ep_series = meta_tbl["protected_endpoint_sha256"].to_pandas()
    ep_codes, ep_uniques = pd.factorize(ep_series)
    ep_codes = ep_codes.astype(np.int32)
    assert len(ep_uniques) == N_ENDPOINTS_EXPECTED, f"端点数 {len(ep_uniques)} != {N_ENDPOINTS_EXPECTED}"

    sp_raw = meta_tbl["split_name"].to_pandas()
    assert set(sp_raw.unique().tolist()) <= {"train", "validation"}, (
        f"split_name 出现未预期取值：{sorted(sp_raw.unique().tolist())}（final split 不得出现在视图中）"
    )
    sp_codes = (sp_raw == "validation").to_numpy().astype(np.int8)
    has_act = meta_tbl["has_activity"].to_pandas().to_numpy().astype(np.int8)
    del meta_tbl
    gc.collect()

    lab_tbl = pq.read_table(f"{DATA_ROOT}/development-labels.parquet")
    assert np.array_equal(lab_tbl["window_row_index"].to_numpy().astype(np.int64), wri)
    labels = lab_tbl["label"].to_numpy().astype(np.int64)
    del lab_tbl
    gc.collect()
    dist = {int(k): int(v) for k, v in zip(*np.unique(labels, return_counts=True))}
    assert dist == LABEL_DIST_EXPECTED, f"标签分布不符: {dist}"

    max_wri = int(wri.max())
    pos = np.full(max_wri + 1, -1, dtype=np.int64)
    pos[wri] = np.arange(n_rows, dtype=np.int64)

    evaluable = np.isin(labels, (0, 1))
    val_m = evaluable & (sp_codes == 1)
    val_all_m = sp_codes == 1
    n_va = int(val_m.sum())
    n_val_all = int(val_all_m.sum())
    assert n_va == N_VA_EXPECTED, f"n_va={n_va} != {N_VA_EXPECTED}"
    assert n_val_all == N_VAL_ALL_EXPECTED, f"n_val_all={n_val_all} != {N_VAL_ALL_EXPECTED}"
    mem_log.append(mem_report("元数据加载完成"))

    # ---------- 阶段 1：加载冻结验证集分数（不重训） ----------
    log("阶段 1：加载冻结验证集分数 val_scores.parquet")
    vs_tbl = pq.read_table(f"{A1_DIR}/val_scores.parquet")
    val_wri_raw = vs_tbl["window_row_index"].to_numpy().astype(np.int64)
    order_va = np.argsort(val_wri_raw, kind="mergesort")
    val_wri = val_wri_raw[order_va]
    val_label = vs_tbl["label"].to_numpy().astype(np.int64)[order_va]
    val_score = vs_tbl["score"].to_numpy().astype(np.float64)[order_va]
    val_contrib = vs_tbl["error_contribution"].to_numpy().astype(np.float64)[order_va]
    val_ep_str = vs_tbl["protected_endpoint_sha256"].to_numpy()[order_va]
    del vs_tbl
    gc.collect()
    assert len(val_wri) == N_VA_EXPECTED
    # 一致性门禁：冻结分数覆盖的窗口集合必须与当前元数据推导的 val_m 完全一致
    assert np.array_equal(val_wri, np.nonzero(val_m)[0]), "val_scores.parquet 的窗口集合与当前元数据 val_m 不一致"
    assert np.array_equal(val_label, labels[val_wri]), "val_scores.parquet 的 label 列与当前标签表不一致"
    val_ep_code = ep_codes[val_wri]
    assert np.array_equal(val_ep_str, ep_uniques[val_ep_code]), "val_scores.parquet 的端点列与当前元数据不一致"
    total_err = float(val_contrib.sum())
    log(f"验证集冻结分数已加载并核验一致 n_va={len(val_wri)} total_err(1-AP)={total_err:.10f}")
    mem_log.append(mem_report("冻结分数加载完成"))

    # ---------- 桥接安全前缀和：eligible_bridge[w] = 验证集内 且 label!=1 ----------
    eligible_bridge = (sp_codes == 1) & (labels != 1)
    eligible_prefix = np.concatenate([[0], np.cumsum(eligible_bridge.astype(np.int64))])
    del eligible_bridge
    gc.collect()

    # ---------- 排好序的正类窗口序列（供事件切分复用） ----------
    pos_idx = np.nonzero(val_label == 1)[0]
    order_p = np.lexsort((val_wri[pos_idx], val_ep_code[pos_idx]))
    p_sorted = pos_idx[order_p]
    ep_sorted = val_ep_code[p_sorted]
    wri_sorted = val_wri[p_sorted]
    score_sorted = val_score[p_sorted]
    contrib_sorted = val_contrib[p_sorted]
    n_pos_total = len(p_sorted)
    assert n_pos_total == 20851, f"验证集正类窗口数 {n_pos_total} != 20851"

    # ================= 任务 2：时间容差重定义 =================
    log("任务 2：时间容差重定义 G 扫描")
    events_by_g: Dict[int, Dict] = {}
    for g in G_VALUES:
        event_id_sorted, n_events, ev_len = compute_events_for_g(ep_sorted, wri_sorted, g, eligible_prefix)
        n_single = int((ev_len == 1).sum())
        events_by_g[g] = {
            "event_id_sorted": event_id_sorted,
            "n_events": n_events,
            "ev_len": ev_len,
            "n_single": n_single,
        }
        log(f"  G={g}: n_events={n_events} n_single={n_single}")

    # ---------- G=0 复现门禁（必须逐位匹配，不一致则停下报告差异） ----------
    g0 = events_by_g[0]
    gate_passed = (g0["n_events"] == EXPECTED_N_EVENTS_G0) and (g0["n_single"] == EXPECTED_N_SINGLE_G0)
    gate_check = {
        "expected_n_events": EXPECTED_N_EVENTS_G0,
        "actual_n_events": g0["n_events"],
        "expected_n_single": EXPECTED_N_SINGLE_G0,
        "actual_n_single": g0["n_single"],
        "passed": bool(gate_passed),
    }
    log(f"G=0 复现门禁: {gate_check}")
    if not gate_passed:
        log("G=0 复现门禁未通过，停止实验并写出差异诊断，不继续后续任务。")
        result = {
            "purpose": "E1 证伪实验：验证集事件切分对删失窗的敏感性（G=0 复现门禁失败提前终止）",
            "gate_check_g0_reproduction": gate_check,
            "screening_only": True,
            "formal_paper_evidence": False,
            "final_accessed": False,
            "status": "gate_failed",
            "total_wall_seconds": time.time() - t_start,
        }
        with open(f"{OUT_DIR}/result.json", "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        sys.exit(1)

    n_events_g0 = g0["n_events"]
    n_single_g0 = g0["n_single"]

    event_sweep = []
    for g in G_VALUES:
        e = events_by_g[g]
        ev_len = e["ev_len"]
        event_sweep.append(
            {
                "G": g,
                "n_events": e["n_events"],
                "n_single": e["n_single"],
                "n_single_ratio_vs_g0": (e["n_single"] / n_single_g0) if n_single_g0 else None,
                "event_length_median": float(np.median(ev_len)) if len(ev_len) else None,
                "event_length_p90": float(np.percentile(ev_len, 90)) if len(ev_len) else None,
            }
        )
    log(f"任务 2 完成: {json.dumps(event_sweep, ensure_ascii=False)}")
    mem_log.append(mem_report("任务2完成"))

    # ================= 任务 1：紧邻窗上下文四(五)分类 =================
    log("任务 1：紧邻窗上下文分类（基于 G=0 事件）")

    def build_neighbor_table(event_mask: np.ndarray) -> Dict:
        """event_mask: 长度 n_events_g0 的布尔数组，选出要统计的事件子集。"""
        boundaries0 = np.nonzero(np.r_[True, g0["event_id_sorted"][1:] != g0["event_id_sorted"][:-1]])[0]
        n_ev = n_events_g0
        starts = boundaries0
        ends = np.r_[boundaries0[1:], len(g0["event_id_sorted"])] - 1
        sel_ev = np.nonzero(event_mask)[0]
        prev_cat = []
        next_cat = []
        for e_i in sel_ev:
            first_pos = starts[e_i]
            last_pos = ends[e_i]
            ep_e = int(ep_sorted[first_pos])
            w_first = int(wri_sorted[first_pos])
            w_last = int(wri_sorted[last_pos])
            prev_cat.append(classify_neighbor(w_first - 1, ep_e, max_wri, ep_codes, labels, has_act))
            next_cat.append(classify_neighbor(w_last + 1, ep_e, max_wri, ep_codes, labels, has_act))
        prev_cat = np.array(prev_cat, dtype=object)
        next_cat = np.array(next_cat, dtype=object)
        n = len(sel_ev)
        table = {}
        for c in NEIGHBOR_CATEGORIES:
            prev_c = int((prev_cat == c).sum())
            next_c = int((next_cat == c).sum())
            either_c = int(((prev_cat == c) | (next_cat == c)).sum())
            table[c] = {
                "prev_count": prev_c,
                "prev_share": (prev_c / n) if n else None,
                "next_count": next_c,
                "next_share": (next_c / n) if n else None,
                "either_count": either_c,
                "either_share": (either_c / n) if n else None,
            }
        return {"n_events": n, "table": table}

    all_events_mask = np.ones(n_events_g0, dtype=bool)
    single_events_mask = g0["ev_len"] == 1
    neighbor_context = {
        "all_events": build_neighbor_table(all_events_mask),
        "single_window_events": build_neighbor_table(single_events_mask),
    }
    single_censored_either_share = neighbor_context["single_window_events"]["table"]["censored_active"]["either_share"]
    log(f"任务 1 完成：单窗事件至少一侧为 censored_active 的比例 = {single_censored_either_share}")
    mem_log.append(mem_report("任务1完成"))

    # ================= 任务 3：冻结分数下的重算（分面 + 预算召回，逐 G） =================
    log("任务 3：冻结分数下按 G 重算位置分面与固定误报预算召回")
    ep_hours_all = n_val_all * WINDOW_SECONDS / 3600.0
    ep_hours_evaluable = n_va * WINDOW_SECONDS / 3600.0
    assert abs(ep_hours_all - REF_EP_HOURS_ALL) < 1e-6
    assert abs(ep_hours_evaluable - REF_EP_HOURS_EVALUABLE) < 1e-6

    neg_scores_desc = np.sort(val_score[val_label == 0])[::-1]
    n_neg_total = len(neg_scores_desc)
    thr_at_budget: Dict[float, float] = {}
    allowed_at_budget: Dict[float, int] = {}
    for r in FP_BUDGETS:
        allowed = int(np.floor(r * ep_hours_all))
        thr_at_budget[r] = compute_threshold(neg_scores_desc, allowed)
        allowed_at_budget[r] = allowed

    detected_mask_by_budget = {r: (score_sorted >= thr_at_budget[r]) for r in FP_BUDGETS}
    window_recall_by_budget = {
        r: {
            "threshold": thr_at_budget[r],
            "allowed_fp_total": allowed_at_budget[r],
            "window_recall": float(detected_mask_by_budget[r].mean()),
            "missed_positive_windows": int(n_pos_total - detected_mask_by_budget[r].sum()),
        }
        for r in FP_BUDGETS
    }

    position_facets_by_g: Dict[int, List[Dict]] = {}
    fp_budget_recall_by_g: Dict[int, List[Dict]] = {}
    for g in G_VALUES:
        e = events_by_g[g]
        cat_sorted = position_categories(e["event_id_sorted"], e["ev_len"])
        facet_rows = []
        for c in ("first", "middle", "last", "single"):
            mk = cat_sorted == c
            n_w = int(mk.sum())
            err_share = float(contrib_sorted[mk].sum() / total_err) if total_err > 0 else None
            facet_rows.append({"position": c, "n_windows": n_w, "error_contribution_share": err_share})
        position_facets_by_g[g] = facet_rows

        budget_rows = []
        for r in FP_BUDGETS:
            det_mask = detected_mask_by_budget[r]
            det_counts = np.bincount(e["event_id_sorted"], weights=det_mask.astype(np.int64), minlength=e["n_events"])
            detected_events = int((det_counts > 0).sum())
            budget_rows.append(
                {
                    "budget_fp_per_endpoint_hour": r,
                    "threshold": thr_at_budget[r],
                    "n_events": e["n_events"],
                    "detected_events": detected_events,
                    "event_recall": (detected_events / e["n_events"]) if e["n_events"] else None,
                    "missed_events": e["n_events"] - detected_events,
                }
            )
        fp_budget_recall_by_g[g] = budget_rows
        log(f"  G={g} 分面与预算召回完成")
    mem_log.append(mem_report("任务3完成"))

    # 交叉核验：G=0、budget=0.01 的事件召回应与 A1 原报告一致
    g0_001 = next(r for r in fp_budget_recall_by_g[0] if r["budget_fp_per_endpoint_hour"] == 0.01)
    recall_diff_vs_ref = abs(g0_001["event_recall"] - REF_EVENT_RECALL_AT_001)
    log(
        f"交叉核验 G=0/0.01档 事件召回={g0_001['event_recall']:.10f} 参考值={REF_EVENT_RECALL_AT_001:.10f} "
        f"diff={recall_diff_vs_ref:.2e}"
    )

    # ================= 任务 4：子判据——单窗事件历史是否贫瘠 =================
    log("任务 4：G=0 单窗事件的 lag1..4 非空历史窗数")
    single_event_ids_g0 = np.nonzero(g0["ev_len"] == 1)[0]
    boundaries0 = np.nonzero(np.r_[True, g0["event_id_sorted"][1:] != g0["event_id_sorted"][:-1]])[0]
    single_starts = boundaries0[single_event_ids_g0]
    anchor_wri = wri_sorted[single_starts]
    assert len(anchor_wri) == n_single_g0

    anchor_local_idx = np.full(n_rows, -1, dtype=np.int64)
    anchor_local_idx[anchor_wri] = np.arange(len(anchor_wri), dtype=np.int64)
    hist_hv = np.full((len(anchor_wri), 4), -1, dtype=np.int64)  # lag 1..4 -> 列 0..3
    conflict_count = 0

    pf = pq.ParquetFile(f"{DATA_ROOT}/temporal-relations.parquet")
    n_row_groups = pf.metadata.num_row_groups
    heartbeat_every = max(1, n_row_groups // 10)
    for rg in range(n_row_groups):
        tbl = pf.read_row_group(rg, columns=["target_window_row_index", "lag", "history_window_row_index"])
        tgt = tbl["target_window_row_index"].to_numpy().astype(np.int64)
        lag_arr = tbl["lag"].to_numpy().astype(np.int64)
        keep_lag = lag_arr <= 4
        if keep_lag.any():
            local = anchor_local_idx[np.clip(tgt, 0, n_rows - 1)]
            keep = keep_lag & (local >= 0) & (tgt < n_rows)
            if keep.any():
                hv = tbl["history_window_row_index"].to_numpy().astype(np.int64)[keep]
                lg = lag_arr[keep]
                lc = local[keep]
                for lag_i in (1, 2, 3, 4):
                    m = lg == lag_i
                    if not m.any():
                        continue
                    lc_m, hv_m = lc[m], hv[m]
                    prev = hist_hv[lc_m, lag_i - 1]
                    bad = (prev != -1) & (prev != hv_m)
                    conflict_count += int(bad.sum())
                    hist_hv[lc_m, lag_i - 1] = hv_m
        del tbl
        if (rg + 1) % heartbeat_every == 0 or rg + 1 == n_row_groups:
            log(f"  temporal-relations 扫描进度 {rg + 1}/{n_row_groups} {_vm_rss_line()}")
    assert conflict_count == 0, f"lag 关系冲突计数应为 0，实际 {conflict_count}"

    nonempty_count = np.zeros(len(anchor_wri), dtype=np.int64)
    for lag_i in (1, 2, 3, 4):
        hv_col = hist_hv[:, lag_i - 1]
        exists = (hv_col >= 0) & (hv_col <= max_wri)
        hv_safe = np.clip(hv_col, 0, max_wri)
        same_ep = ep_codes[hv_safe] == ep_codes[anchor_wri]
        same_sp = sp_codes[hv_safe] == sp_codes[anchor_wri]
        valid_rel = exists & same_ep & same_sp
        has_act_hit = valid_rel & (has_act[hv_safe] == 1)
        nonempty_count += has_act_hit.astype(np.int64)

    hist_median = float(np.median(nonempty_count))
    hist_dist = {str(k): int(v) for k, v in zip(*np.unique(nonempty_count, return_counts=True))}
    history_premise_falsified = hist_median >= HISTORY_RICHNESS_MEDIAN_GE
    history_subcheck = {
        "n_events": int(len(anchor_wri)),
        "median_nonempty_lag_windows": hist_median,
        "distribution_0_to_4": hist_dist,
        "premise_falsified": bool(history_premise_falsified),
        "threshold": HISTORY_RICHNESS_MEDIAN_GE,
    }
    log(f"任务 4 完成: {history_subcheck}")
    mem_log.append(mem_report("任务4完成"))

    # ================= 任务 5（E3 附带项） =================
    log("任务 5：E3 附带项")

    # (a) 分母切换：ep_hours_all -> ep_hours_evaluable，基于 G=0 事件重算四档
    thr_at_budget_eval: Dict[float, float] = {}
    allowed_eval: Dict[float, int] = {}
    for r in FP_BUDGETS:
        allowed_e = int(np.floor(r * ep_hours_evaluable))
        thr_at_budget_eval[r] = compute_threshold(neg_scores_desc, allowed_e)
        allowed_eval[r] = allowed_e

    curve_original = []
    curve_evaluable = []
    delta_rows = []
    for r in FP_BUDGETS:
        det_orig = score_sorted >= thr_at_budget[r]
        det_counts_orig = np.bincount(
            g0["event_id_sorted"], weights=det_orig.astype(np.int64), minlength=n_events_g0
        )
        detected_orig = int((det_counts_orig > 0).sum())
        actual_fp_orig = int((val_score[val_label == 0] >= thr_at_budget[r]).sum())
        row_orig = {
            "budget_fp_per_endpoint_hour": r,
            "allowed_fp_total": allowed_at_budget[r],
            "threshold": thr_at_budget[r],
            "actual_fp": actual_fp_orig,
            "actual_fp_per_endpoint_hour": actual_fp_orig / ep_hours_all,
            "event_recall": detected_orig / n_events_g0,
            "missed_events": n_events_g0 - detected_orig,
        }
        curve_original.append(row_orig)

        det_eval = score_sorted >= thr_at_budget_eval[r]
        det_counts_eval = np.bincount(
            g0["event_id_sorted"], weights=det_eval.astype(np.int64), minlength=n_events_g0
        )
        detected_eval = int((det_counts_eval > 0).sum())
        actual_fp_eval = int((val_score[val_label == 0] >= thr_at_budget_eval[r]).sum())
        row_eval = {
            "budget_fp_per_endpoint_hour": r,
            "allowed_fp_total": allowed_eval[r],
            "threshold": thr_at_budget_eval[r],
            "actual_fp": actual_fp_eval,
            "actual_fp_per_endpoint_hour": actual_fp_eval / ep_hours_evaluable,
            "event_recall": detected_eval / n_events_g0,
            "missed_events": n_events_g0 - detected_eval,
        }
        curve_evaluable.append(row_eval)

        delta_rows.append(
            {
                "budget_fp_per_endpoint_hour": r,
                "allowed_fp_delta": allowed_eval[r] - allowed_at_budget[r],
                "event_recall_delta": row_eval["event_recall"] - row_orig["event_recall"],
            }
        )

    recall_drop_001 = curve_original[0]["event_recall"] - curve_evaluable[0]["event_recall"]
    if recall_drop_001 <= E3_RECALL_DROP_MINOR:
        e3_denominator_verdict = "keep_current_basis_with_note"
    elif recall_drop_001 > E3_RECALL_DROP_MAJOR:
        e3_denominator_verdict = "headline_must_be_restated_as_inflated"
    else:
        e3_denominator_verdict = "intermediate_note_required"

    e3_denominator_switch = {
        "ep_hours_all": ep_hours_all,
        "ep_hours_evaluable": ep_hours_evaluable,
        "curve_original_basis": curve_original,
        "curve_evaluable_basis": curve_evaluable,
        "delta": delta_rows,
        "recall_drop_at_0.01_budget": recall_drop_001,
        "reference_cross_check": {
            "ref_event_recall_at_001": REF_EVENT_RECALL_AT_001,
            "recomputed_original_basis_event_recall_at_001": curve_original[0]["event_recall"],
            "diff": abs(curve_original[0]["event_recall"] - REF_EVENT_RECALL_AT_001),
        },
        "verdict": e3_denominator_verdict,
    }
    log(f"任务 5a 完成: recall_drop@0.01={recall_drop_001:.6f} verdict={e3_denominator_verdict}")

    # (b) 自助法置信区间：0.01 档事件召回（沿用原始 ep_hours_all 分母、G=0 事件）
    thr_001 = thr_at_budget[0.01]
    det_001_sorted = score_sorted >= thr_001
    detected_per_event_001 = (
        np.bincount(g0["event_id_sorted"], weights=det_001_sorted.astype(np.int64), minlength=n_events_g0) > 0
    )
    point_estimate = float(detected_per_event_001.mean())

    event_ep_code_g0 = ep_sorted[boundaries0]
    rng = np.random.default_rng(SEED)

    unique_eps_with_events = np.unique(event_ep_code_g0)
    k_eps = len(unique_eps_with_events)
    flags_by_ep = [detected_per_event_001[event_ep_code_g0 == e] for e in unique_eps_with_events]
    boot_ep = np.empty(N_BOOTSTRAP, dtype=np.float64)
    for b in range(N_BOOTSTRAP):
        draw = rng.integers(0, k_eps, size=k_eps)
        flags = np.concatenate([flags_by_ep[i] for i in draw])
        boot_ep[b] = flags.mean()
    ci_ep = np.percentile(boot_ep, [2.5, 97.5])
    halfwidth_ep = float((ci_ep[1] - ci_ep[0]) / 2.0)

    boot_event = np.empty(N_BOOTSTRAP, dtype=np.float64)
    n_ev_g0 = len(detected_per_event_001)
    for b in range(N_BOOTSTRAP):
        draw = rng.integers(0, n_ev_g0, size=n_ev_g0)
        boot_event[b] = detected_per_event_001[draw].mean()
    ci_event = np.percentile(boot_event, [2.5, 97.5])
    halfwidth_event = float((ci_event[1] - ci_event[0]) / 2.0)

    if halfwidth_ep <= E3_CI_HALFWIDTH_OK:
        e3_ci_verdict = "usable_as_baseline"
    elif halfwidth_ep > E3_CI_HALFWIDTH_BAD:
        e3_ci_verdict = "single_split_single_seed_not_usable_as_primary_baseline"
    else:
        e3_ci_verdict = "intermediate_caution_required"

    e3_bootstrap_ci = {
        "n_bootstrap": N_BOOTSTRAP,
        "seed": SEED,
        "point_estimate_event_recall_at_001": point_estimate,
        "endpoint_cluster_bootstrap": {
            "n_endpoints_with_events": int(k_eps),
            "ci_2.5": float(ci_ep[0]),
            "ci_97.5": float(ci_ep[1]),
            "halfwidth": halfwidth_ep,
        },
        "event_cluster_bootstrap_control": {
            "n_events": int(n_ev_g0),
            "ci_2.5": float(ci_event[0]),
            "ci_97.5": float(ci_event[1]),
            "halfwidth": halfwidth_event,
        },
        "verdict": e3_ci_verdict,
    }
    log(f"任务 5b 完成: 端点簇半宽={halfwidth_ep:.6f} 事件簇半宽={halfwidth_event:.6f} verdict={e3_ci_verdict}")
    mem_log.append(mem_report("任务5完成"))

    # ================= 预注册判据裁决 =================
    log("预注册判据裁决")
    ratio_g2 = event_sweep[G_VALUES.index(2)]["n_single_ratio_vs_g0"]
    ratio_g12 = event_sweep[G_VALUES.index(12)]["n_single_ratio_vs_g0"]
    single_censored_share = single_censored_either_share

    artifact_reasons = []
    if ratio_g2 is not None and ratio_g2 <= ARTIFACT_RATIO_G2:
        artifact_reasons.append(f"n_single(G=2)/n_single(G=0)={ratio_g2:.4f} <= {ARTIFACT_RATIO_G2}")
    if single_censored_share is not None and single_censored_share >= ARTIFACT_CENSORED_SHARE:
        artifact_reasons.append(
            f"单窗事件至少一侧紧邻 censored_active 比例={single_censored_share:.4f} >= {ARTIFACT_CENSORED_SHARE}"
        )
    artifact_condition_met = len(artifact_reasons) > 0

    genuine_reasons = []
    genuine_condition_met = False
    if ratio_g12 is not None and ratio_g12 >= GENUINE_RATIO_G12 and (
        single_censored_share is not None and single_censored_share <= GENUINE_CENSORED_SHARE
    ):
        genuine_condition_met = True
        genuine_reasons.append(f"n_single(G=12)/n_single(G=0)={ratio_g12:.4f} >= {GENUINE_RATIO_G12}")
        genuine_reasons.append(
            f"单窗事件至少一侧紧邻 censored_active 比例={single_censored_share:.4f} <= {GENUINE_CENSORED_SHARE}"
        )

    if artifact_condition_met and not genuine_condition_met:
        final_verdict = "artifact"
    elif genuine_condition_met and not artifact_condition_met:
        final_verdict = "genuine"
    elif artifact_condition_met and genuine_condition_met:
        final_verdict = "conflicting_conditions_both_met_requires_human_adjudication"
    else:
        final_verdict = "partial_artifact"

    partial_headline = None
    if final_verdict == "partial_artifact":
        g_sug = PARTIAL_ARTIFACT_SUGGESTED_G
        sug = events_by_g[g_sug]
        single_share_at_g = next(
            row["error_contribution_share"] for row in position_facets_by_g[g_sug] if row["position"] == "single"
        )
        partial_headline = {
            "suggested_freeze_G": g_sug,
            "n_events": sug["n_events"],
            "n_single": sug["n_single"],
            "single_share_of_events": sug["n_single"] / sug["n_events"] if sug["n_events"] else None,
            "single_error_contribution_share": single_share_at_g,
            "note": "该 G 为预注册判据本身引用的 G=2，非事后挑选；最终是否采用需人裁决。",
        }

    preregistered_verdict = {
        "artifact_condition_met": bool(artifact_condition_met),
        "artifact_reasons": artifact_reasons,
        "genuine_condition_met": bool(genuine_condition_met),
        "genuine_reasons": genuine_reasons,
        "final_verdict": final_verdict,
        "partial_artifact_headline_at_suggested_G": partial_headline,
        "history_richness_premise_falsified": bool(history_premise_falsified),
        "e3_denominator_verdict": e3_denominator_verdict,
        "e3_ci_verdict": e3_ci_verdict,
    }
    log(f"最终判据: {json.dumps(preregistered_verdict, ensure_ascii=False)}")

    # ================= 汇总写出 =================
    result = {
        "purpose": "E1 证伪实验：验证集事件切分（G=0 连续切段）对删失窗（label=-1，占60.4%）的敏感性",
        "hypothesis_under_test": (
            "怀疑：删失窗把本来连续的长事件切碎，人为制造大量单窗事件，"
            "使 A1 误差解剖报告的'历史贫瘠孤立事件'结论成为切分伪影而非真实机制"
        ),
        "contract_version": manifest["contract_version"],
        "contract_sha256": manifest["contract_sha256"],
        "preregistered_thresholds": {
            "G_VALUES": list(G_VALUES),
            "FP_BUDGETS": list(FP_BUDGETS),
            "ARTIFACT_RATIO_G2": ARTIFACT_RATIO_G2,
            "ARTIFACT_CENSORED_SHARE": ARTIFACT_CENSORED_SHARE,
            "GENUINE_RATIO_G12": GENUINE_RATIO_G12,
            "GENUINE_CENSORED_SHARE": GENUINE_CENSORED_SHARE,
            "HISTORY_RICHNESS_MEDIAN_GE": HISTORY_RICHNESS_MEDIAN_GE,
            "E3_RECALL_DROP_MINOR": E3_RECALL_DROP_MINOR,
            "E3_RECALL_DROP_MAJOR": E3_RECALL_DROP_MAJOR,
            "E3_CI_HALFWIDTH_OK": E3_CI_HALFWIDTH_OK,
            "E3_CI_HALFWIDTH_BAD": E3_CI_HALFWIDTH_BAD,
            "N_BOOTSTRAP": N_BOOTSTRAP,
            "SEED": SEED,
        },
        "gate_check_g0_reproduction": gate_check,
        "event_definition_sweep": event_sweep,
        "neighbor_context": neighbor_context,
        "position_facets_by_G": {str(g): position_facets_by_g[g] for g in G_VALUES},
        "fp_budget_recall_by_G": {str(g): fp_budget_recall_by_g[g] for g in G_VALUES},
        "window_recall_by_budget_G_invariant": window_recall_by_budget,
        "history_richness_subcheck_g0_single": history_subcheck,
        "e3_denominator_switch": e3_denominator_switch,
        "e3_bootstrap_ci_0.01_budget_event_recall": e3_bootstrap_ci,
        "preregistered_verdict": preregistered_verdict,
        "cross_checks": {
            "event_recall_at_001_recompute_vs_reference_diff": recall_diff_vs_ref,
        },
        "memory_diagnostics": mem_log,
        "total_wall_seconds": time.time() - t_start,
        "screening_only": True,
        "formal_paper_evidence": False,
        "final_accessed": False,
        "status": "completed",
    }
    with open(f"{OUT_DIR}/result.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    log(f"result.json 已写出 final_verdict={final_verdict} {_vm_rss_line()}")
    log("DONE")


if __name__ == "__main__":
    main()
