# -*- coding: utf-8 -*-
"""E5 机制余量证伪：在冻结的 A1 逐窗分数上，只改「逐窗分数 -> 事件级告警」的
决策规则，测量事件召回还剩多少余量。

唯一问题：不改打分、不重训模型，决策规则层的事件召回余量有多大？
- M1 证据累积（连续 k 次 / 衰减累积 / 窗口内 top-m 均值）
- M2 条件化预算分配（按 protected_endpoint 分配误报预算）

判据在 PREREG_* 常量中预注册，运行后不得修改。
oracle 上界与诚实估计分开报告，绝不混写。

只读冻结制品：
  runs/diagnostics/lspr24-a1-error-anatomy-v1/val_scores.parquet
  runs/data-prepared/lspr24-screen-wide-v1/development-wide.parquet（仅 2 列元数据）
不重训、不改写任何上游制品。screening_only=true。

内存纪律：cgroup 上限从 /sys/fs/cgroup 读取，VmRSS 从 /proc/self/status 读取，
禁止 free / /proc/meminfo / psutil。
"""
import json
import time
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pyarrow.parquet as pq

PREPARED = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/data-prepared/lspr24-screen-wide-v1"
SRC_RUN = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/lspr24-a1-error-anatomy-v1"
OUT_DIR = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/lspr24-decision-rule-headroom-v1"

WINDOW_SECONDS = 5.0
FP_BUDGETS: Tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)
PRIMARY_BUDGET = 0.01

# ---- A1 冻结事实（来自 lspr24-a1-error-anatomy-v1/result.json，用于完整性断言）----
REF = {
    "n_val_rows": 927295,
    "n_positive_windows": 20851,
    "n_events": 1519,
    "n_single_window_events": 1089,
    "n_val_windows_all_including_censored": 2313382,
    "endpoint_hours_all": 3213.0305555555556,
    "curve": {
        0.01: {"allowed_fp": 32, "threshold": 0.9454711079597473, "event_recall": 0.532587228439763},
        0.1: {"allowed_fp": 321, "threshold": 0.12988199293613434, "event_recall": 0.631336405529954},
        1.0: {"allowed_fp": 3213, "threshold": 0.0014314892468973994, "event_recall": 0.7623436471362739},
        10.0: {"allowed_fp": 32130, "threshold": 0.00011061941040679812, "event_recall": 0.8492429229756419},
    },
}

# ---- 预注册判据（运行前写死，跑完不得修改）----
PREREG = {
    "primary_budget_fp_per_endpoint_hour": PRIMARY_BUDGET,
    "fp_accounting_primary": "逐窗计数：一次误报 = 一个 label=0 窗口触发告警（与 A1 源码 actual_fp 口径一致）",
    "fp_accounting_secondary": "事件化计数：同端点 window_row_index 连续的告警负窗合并为一次，仅作同工作点诊断",
    "honest_protocol": "按活动时间前后对半分；前半仅用于选规则超参/预算分配份额，后半用自身负窗重新标定阈值并评价",
    "uncertainty_protocol": ("配对自助：以 protected_endpoint_sha256 为重抽样单元，1000 次，"
                             "每次重抽后同时用现行 max 规则与候选规则在同一批端点上算事件召回，"
                             "取差值 Δ。同时报告边际区间与配对区间。种子 42。"
                             "依据 E1 实测：端点簇边际半宽 0.2346 是事件簇 0.0253 的 9.3 倍"),
    "M1_go": "漏检多窗事件成员窗分数 p75 >= 0.3 且 诚实估计 Δ 配对 95% 区间下界 > 0 且 Δ 点估计 >= 0.03",
    "M1_reject": "漏检多窗事件成员窗分数 p75 < 0.1 或 诚实 Δ 配对 95% 区间含 0 或 oracle 上界 Δ 点估计 < 0.02",
    "M2_go": "端点边际斜率 Gini >= 0.3 且 诚实估计 Δ 配对 95% 区间下界 > 0 且 Δ 点估计 >= 0.03",
    "M2_reject": "端点边际斜率 Gini < 0.15 或 诚实 Δ 配对 95% 区间含 0 或 oracle 上界 Δ 点估计 < 0.02",
}
N_BOOTSTRAP = 1000
BOOTSTRAP_SEED = 42
PREREG_M1_P75_GO = 0.3
PREREG_M1_P75_REJECT = 0.1
PREREG_M1_HONEST_GAIN_GO = 0.03
PREREG_M1_ORACLE_GAIN_REJECT = 0.02
PREREG_M2_GINI_GO = 0.3
PREREG_M2_GINI_REJECT = 0.15
PREREG_M2_HONEST_GAIN_GO = 0.03
PREREG_M2_ORACLE_GAIN_REJECT = 0.02

# ---- 预注册规则网格（跑完不得增删）----
CONSEC_K = (2, 3, 4, 5)
DECAY_RHO = (0.5, 0.7, 0.9)
TOPM_ML = ((2, 3), (2, 5), (2, 10), (3, 5), (3, 10))
GAP_POLICIES = ("seq", "reset")  # seq=按端点可评价窗序列累积；reset=wri 不连续即清零
LMAX = 10

_LOG_LINES: List[str] = []


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    _LOG_LINES.append(line)
    try:
        with open(f"{OUT_DIR}/run.log", "w" if len(_LOG_LINES) == 1 else "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _read_int(path: str) -> Optional[int]:
    try:
        with open(path) as f:
            v = f.read().strip()
        return None if v == "max" else int(v)
    except (OSError, ValueError):
        return None


def mem_line(tag: str) -> str:
    limit = _read_int("/sys/fs/cgroup/memory.max")
    cur = _read_int("/sys/fs/cgroup/memory.current")
    if limit is None:
        limit = _read_int("/sys/fs/cgroup/memory/memory.limit_in_bytes")
        cur = _read_int("/sys/fs/cgroup/memory/memory.usage_in_bytes")
    rss = 0
    try:
        with open("/proc/self/status") as f:
            for ln in f:
                if ln.startswith("VmRSS:"):
                    rss = int(ln.split()[1]) * 1024
                    break
    except OSError:
        pass
    g = 1024 ** 3
    if limit is None or cur is None:
        return f"[内存 {tag}] cgroup 不可读 VmRSS={rss / g:.2f}GiB"
    return (f"[内存 {tag}] cgroup 上限={limit / g:.2f}GiB 已用={cur / g:.2f}GiB "
            f"可用={(limit - cur) / g:.2f}GiB VmRSS={rss / g:.2f}GiB")


def pct(x: np.ndarray, qs: Sequence[int] = (25, 50, 75, 90)) -> Dict[str, Optional[float]]:
    if x.size == 0:
        return {f"p{q}": None for q in qs} | {"max": None, "min": None, "mean": None, "n": 0}
    out: Dict[str, Optional[float]] = {f"p{q}": float(np.percentile(x, q)) for q in qs}
    out["max"] = float(x.max())
    out["min"] = float(x.min())
    out["mean"] = float(x.mean())
    out["n"] = int(x.size)
    return out


def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=np.float64))
    if x.size == 0 or x.sum() <= 0:
        return 0.0
    n = x.size
    idx = np.arange(1, n + 1)
    return float(2.0 * np.sum(idx * x) / (n * np.sum(x)) - (n + 1.0) / n)


# =============================== 阈值与评价 ===============================
def threshold_at_budget(neg_desc: np.ndarray, allowed: int) -> float:
    """与 A1 完全一致的定预算取阈规则。neg_desc 为负窗统计量降序数组。"""
    if neg_desc.size == 0:
        return float(-np.inf)
    if allowed <= 0:
        return float(np.nextafter(neg_desc[0], np.inf))
    if allowed >= neg_desc.size:
        return float(np.nextafter(neg_desc[-1], -np.inf))
    return float(neg_desc[allowed - 1])


def eval_global(g: np.ndarray, y: np.ndarray, event_id: np.ndarray, n_events: int,
                allowed: int) -> Dict:
    neg_desc = np.sort(g[y == 0])[::-1]
    thr = threshold_at_budget(neg_desc, allowed)
    det = g >= thr
    ev = np.unique(event_id[det & (y == 1)])
    ev = ev[ev >= 0]
    n_pos = int((y == 1).sum())
    return {
        "threshold": thr,
        "fp": int((det & (y == 0)).sum()),
        "n_detected_events": int(ev.size),
        "event_recall": float(ev.size / n_events) if n_events else None,
        "window_recall": float((det & (y == 1)).sum() / n_pos) if n_pos else None,
    }


def bootstrap_paired(det_base: np.ndarray, det_cand: np.ndarray, ev_ep_sub: np.ndarray,
                     n_boot: int = N_BOOTSTRAP, seed: int = BOOTSTRAP_SEED) -> Dict:
    """以 protected_endpoint 为簇的配对自助。同一批重抽端点上同时算两个规则的事件召回。"""
    if ev_ep_sub.size == 0:
        return {"n_event_bearing_endpoints": 0, "n_events": 0}
    _, inv = np.unique(ev_ep_sub, return_inverse=True)
    k = int(inv.max()) + 1
    cnt = np.bincount(inv, minlength=k).astype(np.float64)
    nb = np.bincount(inv, weights=det_base.astype(np.float64), minlength=k)
    nc = np.bincount(inv, weights=det_cand.astype(np.float64), minlength=k)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, k, size=(n_boot, k))
    den = cnt[idx].sum(axis=1)
    rb = nb[idx].sum(axis=1) / den
    rc = nc[idx].sum(axis=1) / den
    dd = rc - rb
    lo_b, hi_b = np.percentile(rb, 2.5), np.percentile(rb, 97.5)
    lo_c, hi_c = np.percentile(rc, 2.5), np.percentile(rc, 97.5)
    lo_d, hi_d = np.percentile(dd, 2.5), np.percentile(dd, 97.5)
    return {
        "n_event_bearing_endpoints": k, "n_events": int(cnt.sum()),
        "point_baseline_event_recall": float(det_base.mean()),
        "point_candidate_event_recall": float(det_cand.mean()),
        "point_delta": float(det_cand.mean() - det_base.mean()),
        "marginal_ci95_baseline": [float(lo_b), float(hi_b)],
        "marginal_halfwidth_baseline": float((hi_b - lo_b) / 2),
        "marginal_ci95_candidate": [float(lo_c), float(hi_c)],
        "marginal_halfwidth_candidate": float((hi_c - lo_c) / 2),
        "paired_mean_delta": float(dd.mean()),
        "paired_ci95_delta": [float(lo_d), float(hi_d)],
        "paired_halfwidth_delta": float((hi_d - lo_d) / 2),
        "paired_ci_lower_gt_zero": bool(lo_d > 0),
        "paired_ci_contains_zero": bool(lo_d <= 0.0 <= hi_d),
        "marginal_over_paired_halfwidth_ratio": (
            float((hi_b - lo_b) / (hi_d - lo_d)) if hi_d > lo_d else None),
    }


def fp_episode_count(det: np.ndarray, y: np.ndarray, contig_step: np.ndarray) -> int:
    """事件化误报计数：同端点 wri 连续的告警负窗合并为一次。det/y 为排序空间全长数组。"""
    a = det & (y == 0)
    if not a.any():
        return 0
    prev = np.zeros_like(a)
    prev[1:] = a[:-1] & contig_step[1:]
    return int((a & ~prev).sum())


# =============================== 规则统计量 ===============================
def build_shifted(s: np.ndarray, step_ok: np.ndarray, lmax: int) -> Tuple[np.ndarray, np.ndarray]:
    n = s.size
    shifted = np.full((n, lmax), -np.inf, dtype=np.float64)
    valid = np.zeros((n, lmax), dtype=bool)
    shifted[:, 0] = s
    valid[:, 0] = True
    for j in range(1, lmax):
        shifted[j:, j] = s[: n - j]
        sh = np.zeros(n, dtype=bool)
        sh[j - 1:] = step_ok[: n - j + 1]
        valid[:, j] = valid[:, j - 1] & sh
    return shifted, valid


def stat_consec(shifted: np.ndarray, valid: np.ndarray, k: int) -> np.ndarray:
    m = np.where(valid[:, :k], shifted[:, :k], -np.inf)
    return m.min(axis=1)


def stat_topm(shifted: np.ndarray, valid: np.ndarray, m: int, L: int) -> np.ndarray:
    blk = np.where(valid[:, :L], shifted[:, :L], -np.inf)
    part = -np.partition(-blk, m - 1, axis=1)[:, :m]
    return part.mean(axis=1)


def stat_decay(s: np.ndarray, step_ok: np.ndarray, rho: float) -> np.ndarray:
    n = s.size
    h = np.empty(n, dtype=np.float64)
    prev = 0.0
    for i in range(n):
        cur = rho * prev + s[i] if (i > 0 and step_ok[i]) else s[i]
        h[i] = cur
        prev = cur
    return h


def build_all_stats(s: np.ndarray, step_seq: np.ndarray, step_reset: np.ndarray) -> Dict[str, np.ndarray]:
    stats: Dict[str, np.ndarray] = {"max_baseline(A1现行规则)": s}
    for pol, step in (("seq", step_seq), ("reset", step_reset)):
        shifted, valid = build_shifted(s, step, LMAX)
        for k in CONSEC_K:
            stats[f"连续{k}次越界|gap={pol}"] = stat_consec(shifted, valid, k)
        for m, L in TOPM_ML:
            stats[f"trailing{L}窗top{m}均值|gap={pol}"] = stat_topm(shifted, valid, m, L)
        del shifted, valid
        for rho in DECAY_RHO:
            stats[f"衰减累积rho={rho}|gap={pol}"] = stat_decay(s, step, rho)
        log(f"  规则统计量已构建 gap={pol} {mem_line('rule')}")
    return stats


# =============================== 端点预算分配 ===============================
def endpoint_groups(values: np.ndarray, ep: np.ndarray, n_ep: int) -> Tuple[np.ndarray, np.ndarray]:
    """按端点分组并组内升序，返回 (排序值, 每端点起止边界)。"""
    o = np.lexsort((values, ep))
    return values[o], np.searchsorted(ep[o], np.arange(n_ep + 1))


def concave_hull(points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    hull: List[Tuple[int, int]] = [(0, 0)]
    for p in points:
        while len(hull) >= 2:
            x0, y0 = hull[-2]
            x1, y1 = hull[-1]
            x2, y2 = p
            if (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0) >= 0:
                hull.pop()
            else:
                break
        hull.append(p)
    return hull


def endpoint_staircases(g: np.ndarray, y: np.ndarray, ep: np.ndarray, n_ep: int,
                        ev_ep: np.ndarray, ev_max: np.ndarray) -> List[Dict]:
    """每端点的 (误报代价, 命中事件数) 阶梯与对应阈值。"""
    neg_m = y == 0
    neg_sorted, neg_b = endpoint_groups(g[neg_m], ep[neg_m], n_ep)
    ev_sorted, ev_b = endpoint_groups(ev_max, ev_ep, n_ep)
    out: List[Dict] = []
    for j in range(n_ep):
        seg_neg = neg_sorted[neg_b[j]: neg_b[j + 1]]
        vals = ev_sorted[ev_b[j]: ev_b[j + 1]][::-1]  # 事件最大统计量降序
        pts: List[Tuple[int, int]] = []
        thrs: List[float] = []
        last_fp = -1
        for i, v in enumerate(vals):
            fp = int(seg_neg.size - np.searchsorted(seg_neg, v, side="left"))
            if fp == last_fp and pts:
                pts[-1] = (fp, i + 1)
                thrs[-1] = float(v)
            else:
                pts.append((fp, i + 1))
                thrs.append(float(v))
                last_fp = fp
        out.append({"points": pts, "thresholds": thrs, "n_events": int(vals.size),
                    "max_neg": float(seg_neg[-1]) if seg_neg.size else float("-inf"),
                    "n_neg": int(seg_neg.size)})
    return out


def greedy_allocate(stairs: List[Dict], budget: int) -> Dict:
    """凹包贪心 + 剩余预算精修。返回可达解（下界）与 LP 上界。"""
    segs = []
    for j, st in enumerate(stairs):
        hull = concave_hull(st["points"])
        for a in range(len(hull) - 1):
            dfp = hull[a + 1][0] - hull[a][0]
            dev = hull[a + 1][1] - hull[a][1]
            if dev <= 0:
                continue
            slope = float("inf") if dfp == 0 else dev / dfp
            segs.append((slope, dfp, dev, j, hull[a + 1][1], hull[a + 1][0]))
    segs.sort(key=lambda t: (-t[0], t[1]))
    n_ep = len(stairs)
    spent = 0
    gained = 0
    reach_ev = [0] * n_ep   # 当前已达成的事件数
    reach_fp = [0] * n_ep   # 当前已花费的误报数
    lp_bound = 0.0
    lp_spent = 0
    lp_done = False
    for slope, dfp, dev, j, tgt_ev, tgt_fp in segs:
        if not lp_done:
            if lp_spent + dfp <= budget:
                lp_spent += dfp
                lp_bound += dev
            else:
                lp_bound += (budget - lp_spent) * slope
                lp_done = True
        if tgt_ev <= reach_ev[j]:
            continue
        d_fp = tgt_fp - reach_fp[j]
        if spent + d_fp <= budget:
            spent += d_fp
            gained += tgt_ev - reach_ev[j]
            reach_ev[j] = tgt_ev
            reach_fp[j] = tgt_fp
    # 剩余预算精修：允许推进到任意阶梯点（含非凹包点）
    improved = True
    while improved:
        improved = False
        best = None
        for j, st in enumerate(stairs):
            for fp, ev in st["points"]:
                if ev <= reach_ev[j]:
                    continue
                d_fp = fp - reach_fp[j]
                if d_fp < 0 or spent + d_fp > budget:
                    continue
                d_ev = ev - reach_ev[j]
                key = (d_ev, -d_fp)
                if best is None or key > best[0]:
                    best = (key, j, ev, fp, d_fp, d_ev)
        if best is not None:
            _, j, ev, fp, d_fp, d_ev = best
            reach_ev[j] = ev
            reach_fp[j] = fp
            spent += d_fp
            gained += d_ev
            improved = True
    thr = []
    for j, st in enumerate(stairs):
        if reach_ev[j] == 0:
            thr.append(float("inf"))
        else:
            i = next(i for i, (_, ev) in enumerate(st["points"]) if ev == reach_ev[j])
            thr.append(st["thresholds"][i])
    return {"events": int(gained), "fp_spent": int(spent), "thresholds": thr,
            "fp_per_endpoint": list(reach_fp), "lp_upper_bound_events": float(lp_bound),
            "events_per_endpoint": list(reach_ev)}


def apply_per_endpoint_thresholds(g: np.ndarray, y: np.ndarray, ep: np.ndarray,
                                  thr: Sequence[float], event_id: np.ndarray,
                                  n_events: int) -> Dict:
    t = np.asarray(thr, dtype=np.float64)[ep]
    det = g >= t
    ev = np.unique(event_id[det & (y == 1)])
    ev = ev[ev >= 0]
    return {"fp": int((det & (y == 0)).sum()), "n_detected_events": int(ev.size),
            "event_recall": float(ev.size / n_events) if n_events else None}


def quotas_from_shares(shares: np.ndarray, budget: int) -> np.ndarray:
    raw = shares * budget
    q = np.floor(raw).astype(np.int64)
    rem = budget - int(q.sum())
    if rem > 0:
        order = np.argsort(-(raw - q))
        q[order[:rem]] += 1
    return q


def thresholds_from_quotas(g: np.ndarray, y: np.ndarray, ep: np.ndarray, n_ep: int,
                           quotas: np.ndarray) -> Tuple[List[float], int]:
    """按端点配额在评价半段自身负窗上重新标定阈值。无负窗端点保守取 +inf（不告警）。"""
    neg_m = y == 0
    neg_sorted, neg_b = endpoint_groups(g[neg_m], ep[neg_m], n_ep)
    out: List[float] = []
    n_empty = 0
    for j in range(n_ep):
        seg = neg_sorted[neg_b[j]: neg_b[j + 1]][::-1]  # 降序
        if seg.size == 0:
            out.append(float("inf"))
            n_empty += 1
        else:
            out.append(threshold_at_budget(seg, int(quotas[j])))
    return out, n_empty


# =============================== 主流程 ===============================
def load_frozen() -> Dict:
    log(mem_line("start"))
    log("读取冻结逐窗分数 val_scores.parquet（只读）")
    tbl = pq.read_table(f"{SRC_RUN}/val_scores.parquet")
    wri = tbl["window_row_index"].to_numpy().astype(np.int64)
    ns = tbl["window_start_ns"].to_numpy().astype(np.int64)
    y = tbl["label"].to_numpy().astype(np.int8)
    s = tbl["score"].to_numpy().astype(np.float64)
    ep_str = tbl["protected_endpoint_sha256"].to_pandas().to_numpy()
    del tbl
    assert wri.size == REF["n_val_rows"], f"逐窗行数 {wri.size} != {REF['n_val_rows']}"
    assert int((y == 1).sum()) == REF["n_positive_windows"], "正类窗口数不符"
    assert set(np.unique(y).tolist()) == {0, 1}, "标签集合不符（应只含 0/1）"
    _, ep = np.unique(ep_str, return_inverse=True)
    ep = ep.astype(np.int32)
    n_ep = int(ep.max()) + 1
    log(f"逐窗分数已加载 rows={wri.size} endpoints={n_ep} {mem_line('scores')}")

    log("读取 development-wide.parquet 的 2 列元数据（统计含删失的验证窗总量）")
    meta = pq.read_table(f"{PREPARED}/development-wide.parquet",
                         columns=["window_start_ns", "split_name"])
    sp = meta["split_name"].to_pandas().to_numpy()
    uniq_sp = sorted(set(sp.tolist()))
    assert not any(("final" in x) or ("test" in x) for x in uniq_sp), (
        f"共享视图内出现最终封存段 {uniq_sp}（本实验禁止触及）")
    assert "validation" in uniq_sp, f"未找到 validation 切分，实际为 {uniq_sp}"
    val_all = sp == "validation"
    ns_val_all = meta["window_start_ns"].to_numpy().astype(np.int64)[val_all]
    del meta, sp
    assert ns_val_all.size == REF["n_val_windows_all_including_censored"], (
        f"验证窗总量 {ns_val_all.size} != {REF['n_val_windows_all_including_censored']}")
    log(f"验证窗总量核对通过 n={ns_val_all.size} splits={uniq_sp} {mem_line('meta')}")
    return {"wri": wri, "ns": ns, "y": y, "s": s, "ep": ep, "n_ep": n_ep,
            "ns_val_all": ns_val_all, "split_names": uniq_sp}


def build_events(wri: np.ndarray, ep: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, int, np.ndarray, np.ndarray, np.ndarray]:
    """排序空间内构造事件（同端点 wri 连续的 label=1 极大段）。"""
    n = wri.size
    p = np.nonzero(y == 1)[0]
    new_ev = np.ones(p.size, dtype=bool)
    if p.size > 1:
        new_ev[1:] = (ep[p][1:] != ep[p][:-1]) | (wri[p][1:] - wri[p][:-1] != 1)
    ev_of_pos = np.cumsum(new_ev) - 1
    n_events = int(ev_of_pos[-1]) + 1
    event_id = np.full(n, -1, dtype=np.int64)
    event_id[p] = ev_of_pos
    ev_len = np.bincount(ev_of_pos, minlength=n_events)
    starts = np.nonzero(new_ev)[0]
    ev_ep = ep[p][starts]
    return event_id, n_events, ev_len, ev_ep, p


def event_max(g: np.ndarray, p: np.ndarray, ev_of_pos: np.ndarray, n_events: int) -> np.ndarray:
    out = np.full(n_events, -np.inf, dtype=np.float64)
    np.maximum.at(out, ev_of_pos, g[p])
    return out


def main() -> None:
    t0 = time.time()
    d = load_frozen()
    wri, ns, y, s, ep, n_ep = d["wri"], d["ns"], d["y"], d["s"], d["ep"], d["n_ep"]

    log("按 (endpoint, window_row_index) 排序，进入排序空间")
    order = np.lexsort((wri, ep))
    wri, ns, y, s, ep = wri[order], ns[order], y[order], s[order], ep[order]

    event_id, n_events, ev_len, ev_ep, p_idx = build_events(wri, ep, y)
    ev_of_pos = event_id[p_idx]
    assert n_events == REF["n_events"], f"事件数 {n_events} != {REF['n_events']}"
    assert int((ev_len == 1).sum()) == REF["n_single_window_events"], "单窗事件数不符"
    log(f"事件构造完成 n_events={n_events} 单窗={int((ev_len == 1).sum())} {mem_line('events')}")

    ep_hours_all = d["ns_val_all"].size * WINDOW_SECONDS / 3600.0
    assert abs(ep_hours_all - REF["endpoint_hours_all"]) < 1e-9, "端点小时基数不符"
    allowed_full = {r: int(np.floor(r * ep_hours_all)) for r in FP_BUDGETS}

    # ---------- 基线复现（与 A1 result.json 逐项核对）----------
    log("复现 A1 现行 max 规则的预算曲线")
    base_full = {}
    repro = []
    for r in FP_BUDGETS:
        res = eval_global(s, y, event_id, n_events, allowed_full[r])
        base_full[r] = res
        ref = REF["curve"][r]
        repro.append({"budget": r, "allowed_fp": allowed_full[r], "ref": ref, "recomputed": res,
                      "threshold_match": abs(res["threshold"] - ref["threshold"]) < 1e-12,
                      "event_recall_match": abs(res["event_recall"] - ref["event_recall"]) < 1e-12})
        log(f"  预算 {r}: allowed={allowed_full[r]} thr={res['threshold']:.10g} "
            f"fp={res['fp']} 事件召回={res['event_recall']:.6f} (A1 参考 {ref['event_recall']:.6f})")
    assert all(x["threshold_match"] and x["event_recall_match"] for x in repro), "基线复现与 A1 冻结结果不一致"

    # ---------- 第 1 组：漏检事件分数形态 ----------
    log("第 1 组：漏检事件的分数形态")
    ev_max_s = event_max(s, p_idx, ev_of_pos, n_events)
    group1 = {}
    for r in FP_BUDGETS:
        thr = base_full[r]["threshold"]
        missed = ev_max_s < thr
        assert abs(float((~missed).mean()) - base_full[r]["event_recall"]) < 1e-12, (
            "事件max判定与逐窗判定不一致")
        row = {"threshold": thr, "n_missed_events": int(missed.sum())}
        for tag, sel in (("单窗事件", missed & (ev_len == 1)), ("多窗事件", missed & (ev_len > 1))):
            ids = np.nonzero(sel)[0]
            memb = s[p_idx][np.isin(ev_of_pos, ids)] if ids.size else np.array([])
            row[tag] = {
                "n_events": int(ids.size),
                "成员窗分数分布": pct(memb),
                "每事件max分数分布": pct(ev_max_s[ids]),
                "距阈值差(thr-max)分布": pct(thr - ev_max_s[ids]),
                "max>=0.5的事件数": int((ev_max_s[ids] >= 0.5).sum()),
                "max>=0.1的事件数": int((ev_max_s[ids] >= 0.1).sum()),
            }
        group1[str(r)] = row
        log(f"  预算 {r}: 漏检 {int(missed.sum())} = 单窗 {row['单窗事件']['n_events']} "
            f"+ 多窗 {row['多窗事件']['n_events']}; 多窗成员窗 p75="
            f"{row['多窗事件']['成员窗分数分布']['p75']}")
    p75_multi_primary = group1[str(PRIMARY_BUDGET)]["多窗事件"]["成员窗分数分布"]["p75"]

    # 单窗事件的历史可用性（E1 已实测 lag1..4 非空历史中位数 3.0，证伪「单窗=历史贫瘠」）。
    # 此处用两个可在本视图内直接计算的代理量，按漏检/命中拆分复核。
    ev_start_row = p_idx[np.nonzero(np.concatenate(([True], np.diff(ev_of_pos) != 0)))[0]]
    n_adj = np.zeros(n_events, dtype=np.int64)
    n_prev_same_ep = np.zeros(n_events, dtype=np.int64)
    for e_i, i0 in enumerate(ev_start_row):
        for m in range(1, 5):
            j = i0 - m
            if j < 0 or ep[j] != ep[i0]:
                break
            n_prev_same_ep[e_i] += 1
            if wri[i0] - wri[j] == m:
                n_adj[e_i] += 1
    thr_p = base_full[PRIMARY_BUDGET]["threshold"]
    single = ev_len == 1
    hist_obs = {"note": ("代理量，非 E1 的 temporal-relations lag 定义；"
                         "E1 实测 1089 个单窗事件 lag1..4 非空历史分布 "
                         "{0:41,1:130,2:295,3:321,4:302} 中位数 3.0"),
                "definition_n_adjacent": "事件首窗前 1..4 个 window_row_index 严格相邻且可评价的窗数",
                "definition_n_prev_same_endpoint": "排序空间内紧邻其前、同端点的可评价窗数（上限 4）"}
    for tag, sel in (("单窗-全部", single), ("单窗-0.01档漏检", single & (ev_max_s < thr_p)),
                     ("单窗-0.01档命中", single & (ev_max_s >= thr_p)),
                     ("多窗-0.01档漏检", (~single) & (ev_max_s < thr_p))):
        hist_obs[tag] = {
            "n_events": int(sel.sum()),
            "n_adjacent_hist": {str(v): int(c) for v, c in
                                zip(*np.unique(n_adj[sel], return_counts=True))},
            "n_adjacent_median": float(np.median(n_adj[sel])) if sel.any() else None,
            "n_prev_same_endpoint_median": float(np.median(n_prev_same_ep[sel])) if sel.any() else None,
        }
    group1["single_window_history_availability"] = hist_obs
    log(f"  单窗事件历史代理量：全部中位数(严格相邻)={hist_obs['单窗-全部']['n_adjacent_median']} "
        f"漏检={hist_obs['单窗-0.01档漏检']['n_adjacent_median']} "
        f"命中={hist_obs['单窗-0.01档命中']['n_adjacent_median']}")

    # ---------- 时间对半分（诚实估计用）----------
    uniq_t, cnt_t = np.unique(ns, return_counts=True)
    cum = np.cumsum(cnt_t)
    cut_i = int(np.argmin(np.abs(cum - ns.size / 2.0)))
    t_split = int(uniq_t[cut_i])
    half_a = ns <= t_split
    ev_first_a = np.zeros(n_events, dtype=bool)
    ev_last_a = np.zeros(n_events, dtype=bool)
    starts = np.nonzero(np.concatenate(([True], np.diff(ev_of_pos) != 0)))[0]
    ends = np.concatenate((starts[1:] - 1, [p_idx.size - 1]))
    ev_first_a[ev_of_pos[starts]] = half_a[p_idx[starts]]
    ev_last_a[ev_of_pos[starts]] = half_a[p_idx[ends]]
    straddle = ev_first_a != ev_last_a
    ev_half = np.where(ev_first_a, 0, 1)
    ev_half[straddle] = -1
    n_ev_a = int(((ev_half == 0)).sum())
    n_ev_b = int(((ev_half == 1)).sum())
    n_all_a = int((d["ns_val_all"] <= t_split).sum())
    n_all_b = int((d["ns_val_all"] > t_split).sum())
    hours_a = n_all_a * WINDOW_SECONDS / 3600.0
    hours_b = n_all_b * WINDOW_SECONDS / 3600.0
    allowed_a = {r: int(np.floor(r * hours_a)) for r in FP_BUDGETS}
    allowed_b = {r: int(np.floor(r * hours_b)) for r in FP_BUDGETS}
    eid_a = np.where(half_a & (event_id >= 0) & (ev_half[np.clip(event_id, 0, None)] == 0), event_id, -1)
    eid_b = np.where((~half_a) & (event_id >= 0) & (ev_half[np.clip(event_id, 0, None)] == 1), event_id, -1)
    log(f"时间对半分 t_split={t_split} 前半窗={int(half_a.sum())} 后半窗={int((~half_a).sum())} "
        f"前半事件={n_ev_a} 后半事件={n_ev_b} 跨界事件={int(straddle.sum())} "
        f"allowed_a={allowed_a[PRIMARY_BUDGET]} allowed_b={allowed_b[PRIMARY_BUDGET]}")

    split_meta = {"t_split_ns": t_split, "n_windows_half_a": int(half_a.sum()),
                  "n_windows_half_b": int((~half_a).sum()),
                  "n_all_val_windows_half_a": n_all_a, "n_all_val_windows_half_b": n_all_b,
                  "endpoint_hours_half_a": hours_a, "endpoint_hours_half_b": hours_b,
                  "n_events_half_a": n_ev_a, "n_events_half_b": n_ev_b,
                  "n_events_straddling_excluded": int(straddle.sum()),
                  "allowed_fp_half_a": allowed_a, "allowed_fp_half_b": allowed_b}

    ids_a = np.nonzero(ev_half == 0)[0]
    ids_b = np.nonzero(ev_half == 1)[0]
    ev_ep_a, ev_ep_b = ev_ep[ids_a], ev_ep[ids_b]
    ev_max_a = event_max(np.where(half_a, s, -np.inf), p_idx, ev_of_pos, n_events)
    ev_max_b = event_max(np.where(~half_a, s, -np.inf), p_idx, ev_of_pos, n_events)
    log(f"事件簇统计：全集含事件端点={int(np.unique(ev_ep).size)} "
        f"后半含事件端点={int(np.unique(ev_ep_b).size)}")

    # ---------- 第 2 组：证据累积规则 ----------
    log("第 2 组：构建替代决策规则统计量")
    step_seq = np.zeros(wri.size, dtype=bool)
    step_seq[1:] = ep[1:] == ep[:-1]
    step_reset = np.zeros(wri.size, dtype=bool)
    step_reset[1:] = step_seq[1:] & (wri[1:] - wri[:-1] == 1)
    log(f"  序列可用性：同端点前一可评价窗占比={float(step_seq.mean()):.4f} "
        f"wri 严格相邻前窗占比={float(step_reset.mean()):.4f}")
    stats = build_all_stats(s, step_seq, step_reset)

    oracle_tbl: Dict[str, Dict[str, Dict]] = {}
    honest_tbl: Dict[str, Dict] = {}
    a_tbl: Dict[str, Dict[str, Dict]] = {}
    for name, g in stats.items():
        oracle_tbl[name] = {}
        a_tbl[name] = {}
        for r in FP_BUDGETS:
            oracle_tbl[name][str(r)] = eval_global(g, y, event_id, n_events, allowed_full[r])
            a_tbl[name][str(r)] = eval_global(g[half_a], y[half_a], eid_a[half_a], n_ev_a, allowed_a[r])
    log(f"  {len(stats)} 个规则配置已评估 {mem_line('group2')}")

    group2 = {"oracle_upper_bound": oracle_tbl, "honest": {}}
    for r in FP_BUDGETS:
        base_rec = base_full[r]["event_recall"]
        cand = [(v[str(r)]["event_recall"], k) for k, v in oracle_tbl.items() if not k.startswith("max_baseline")]
        best_rec, best_name = max(cand, key=lambda t: (t[0], [-ord(c) for c in t[1]]))
        # 诚实估计：仅用前半选超参，后半自标定阈值评价
        sel = sorted(((a_tbl[k][str(r)]["event_recall"], k) for k in stats if not k.startswith("max_baseline")),
                     key=lambda t: (-t[0], t[1]))[0]
        sel_name = sel[1]
        b_sel = eval_global(stats[sel_name][~half_a], y[~half_a], eid_b[~half_a], n_ev_b, allowed_b[r])
        b_base = eval_global(s[~half_a], y[~half_a], eid_b[~half_a], n_ev_b, allowed_b[r])
        ev_max_sel_b = event_max(np.where(~half_a, stats[sel_name], -np.inf), p_idx, ev_of_pos, n_events)
        assert abs(float((ev_max_b[ids_b] >= b_base["threshold"]).mean()) - b_base["event_recall"]) < 1e-12
        assert abs(float((ev_max_sel_b[ids_b] >= b_sel["threshold"]).mean()) - b_sel["event_recall"]) < 1e-12
        boot_h = bootstrap_paired(ev_max_b[ids_b] >= b_base["threshold"],
                                  ev_max_sel_b[ids_b] >= b_sel["threshold"], ev_ep_b)
        ev_max_best = event_max(stats[best_name], p_idx, ev_of_pos, n_events)
        boot_o = bootstrap_paired(ev_max_s >= base_full[r]["threshold"],
                                  ev_max_best >= oracle_tbl[best_name][str(r)]["threshold"], ev_ep)
        group2["honest"][str(r)] = {
            "selected_on_half_a": sel_name,
            "half_a_event_recall_of_selected": sel[0],
            "half_b_baseline_max_rule": b_base,
            "half_b_selected_rule": b_sel,
            "honest_gain_event_recall": b_sel["event_recall"] - b_base["event_recall"],
            "paired_endpoint_bootstrap": boot_h,
        }
        group2.setdefault("oracle_summary", {})[str(r)] = {
            "baseline_event_recall": base_rec,
            "best_rule": best_name,
            "best_event_recall": best_rec,
            "oracle_gain_event_recall": best_rec - base_rec,
            "paired_endpoint_bootstrap": boot_o,
        }
        log(f"  预算 {r}: oracle 最优={best_name} 召回={best_rec:.6f} (基线 {base_rec:.6f}, "
            f"增益 {best_rec - base_rec:+.6f}, 配对CI={boot_o.get('paired_ci95_delta')}) | "
            f"诚实选中={sel_name} 后半增益="
            f"{group2['honest'][str(r)]['honest_gain_event_recall']:+.6f} "
            f"配对CI={boot_h.get('paired_ci95_delta')} 边际CI(基线)={boot_h.get('marginal_ci95_baseline')}")

    # 误报口径差异诊断（主预算、基线与 oracle 最优规则同工作点）
    best_name_primary = group2["oracle_summary"][str(PRIMARY_BUDGET)]["best_rule"]
    ep_diag = {}
    for nm in ("max_baseline(A1现行规则)", best_name_primary):
        gg = stats[nm]
        thr = eval_global(gg, y, event_id, n_events, allowed_full[PRIMARY_BUDGET])["threshold"]
        det = gg >= thr
        ep_diag[nm] = {"per_window_fp": int((det & (y == 0)).sum()),
                       "episode_fp": fp_episode_count(det, y, step_reset)}
    group2["fp_accounting_diagnostic@0.01"] = ep_diag
    log(f"  误报口径诊断 {json.dumps(ep_diag, ensure_ascii=False)}")

    # ---------- 第 3 组：端点预算分配 ----------
    log("第 3 组：端点误报预算分配")
    n_ep_no_neg = int((np.bincount(ep[y == 0], minlength=n_ep) == 0).sum())
    stairs_full = endpoint_staircases(s, y, ep, n_ep, ev_ep, ev_max_s)
    free_events = int(sum(max([ev for fp, ev in st["points"] if fp == 0], default=0) for st in stairs_full))
    slopes = []
    for st in stairs_full:
        hull = concave_hull(st["points"])
        best = 0.0
        for a in range(len(hull) - 1):
            dfp = hull[a + 1][0] - hull[a][0]
            dev = hull[a + 1][1] - hull[a][1]
            if dfp >= 1 and dev > 0:
                best = max(best, dev / dfp)
        slopes.append(best)
    slope_gini = gini(np.asarray(slopes))
    group3 = {"n_endpoints": n_ep, "n_endpoints_without_negative_window": n_ep_no_neg,
              "events_reachable_at_zero_fp_cost": free_events,
              "marginal_slope_gini": slope_gini,
              "marginal_slope_distribution": pct(np.asarray(slopes)),
              "oracle_upper_bound": {}, "honest": {}}
    log(f"  零成本可达事件={free_events} 边际斜率 Gini={slope_gini:.4f} 无负窗端点={n_ep_no_neg}")

    # 消融：纯逐端点标定（全部配额=0，不花任何误报预算，不含任何分配信息）
    thr_zero_full, _ = thresholds_from_quotas(s, y, ep, n_ep, np.zeros(n_ep, dtype=np.int64))
    tz = np.asarray(thr_zero_full, dtype=np.float64)
    zc = apply_per_endpoint_thresholds(s, y, ep, thr_zero_full, event_id, n_events)
    boot_zc = bootstrap_paired(ev_max_s >= base_full[PRIMARY_BUDGET]["threshold"],
                               ev_max_s >= tz[ev_ep], ev_ep)
    group3["ablation_zero_cost_per_endpoint_calibration"] = {
        "描述": "每端点阈值取其自身负窗最大值之上，总误报 0，不使用任何预算分配信息",
        "result": zc, "vs_baseline@0.01": boot_zc,
        "baseline@0.01_event_recall": base_full[PRIMARY_BUDGET]["event_recall"],
        "baseline@0.01_fp": base_full[PRIMARY_BUDGET]["fp"]}
    log(f"  消融：零成本逐端点标定 fp={zc['fp']} 事件召回={zc['event_recall']:.6f} "
        f"(基线 0.01 档 {base_full[PRIMARY_BUDGET]['event_recall']:.6f} @ 32 FP) "
        f"配对CI={boot_zc.get('paired_ci95_delta')}")

    for r in FP_BUDGETS:
        alloc = greedy_allocate(stairs_full, allowed_full[r])
        chk = apply_per_endpoint_thresholds(s, y, ep, alloc["thresholds"], event_id, n_events)
        thr_vec = np.asarray(alloc["thresholds"], dtype=np.float64)
        boot_o3 = bootstrap_paired(ev_max_s >= base_full[r]["threshold"],
                                   ev_max_s >= thr_vec[ev_ep], ev_ep)
        group3["oracle_upper_bound"][str(r)] = {
            "paired_endpoint_bootstrap": boot_o3,
            "allowed_fp": allowed_full[r], "greedy_events": alloc["events"],
            "greedy_event_recall": alloc["events"] / n_events,
            "verified_by_thresholds": chk,
            "lp_upper_bound_events": alloc["lp_upper_bound_events"],
            "lp_upper_bound_event_recall": alloc["lp_upper_bound_events"] / n_events,
            "baseline_uniform_event_recall": base_full[r]["event_recall"],
            "oracle_gain_event_recall": alloc["events"] / n_events - base_full[r]["event_recall"],
            "fp_distribution_gini": gini(np.asarray(alloc["fp_per_endpoint"], dtype=np.float64)),
        }
        log(f"  预算 {r}: 分配后事件召回={alloc['events'] / n_events:.6f} "
            f"(均匀 {base_full[r]['event_recall']:.6f}, 增益 "
            f"{alloc['events'] / n_events - base_full[r]['event_recall']:+.6f}) "
            f"实测阈值复核 fp={chk['fp']} 召回={chk['event_recall']:.6f} "
            f"LP上界={alloc['lp_upper_bound_events'] / n_events:.6f}")

    # 诚实估计：前半定份额，后半自标定
    for r in FP_BUDGETS:
        stairs_a = endpoint_staircases(s[half_a], y[half_a], ep[half_a], n_ep,
                                       ev_ep[ids_a], ev_max_a[ids_a])
        alloc_a = greedy_allocate(stairs_a, allowed_a[r])
        fp_vec = np.asarray(alloc_a["fp_per_endpoint"], dtype=np.float64)
        shares = fp_vec / fp_vec.sum() if fp_vec.sum() > 0 else np.zeros(n_ep)
        quotas = quotas_from_shares(shares, allowed_b[r]) if fp_vec.sum() > 0 else np.zeros(n_ep, dtype=np.int64)
        thr_b, n_empty = thresholds_from_quotas(s[~half_a], y[~half_a], ep[~half_a], n_ep, quotas)
        got = apply_per_endpoint_thresholds(s[~half_a], y[~half_a], ep[~half_a], thr_b, eid_b[~half_a], n_ev_b)
        strict = apply_per_endpoint_thresholds(s[~half_a], y[~half_a], ep[~half_a],
                                               alloc_a["thresholds"], eid_b[~half_a], n_ev_b)
        b_base = eval_global(s[~half_a], y[~half_a], eid_b[~half_a], n_ev_b, allowed_b[r])
        # 严格迁移的公平对照：全局阈值同样冻结自前半，以及后半上与候选实测误报数匹配的全局阈值
        thr_a_global = eval_global(s[half_a], y[half_a], eid_a[half_a], n_ev_a, allowed_a[r])["threshold"]
        det_sb = s[~half_a] >= thr_a_global
        ev_sb = np.unique(eid_b[~half_a][det_sb & (y[~half_a] == 1)])
        strict_base = {"threshold": thr_a_global, "fp": int((det_sb & (y[~half_a] == 0)).sum()),
                       "event_recall": float(ev_sb[ev_sb >= 0].size / n_ev_b)}
        matched = eval_global(s[~half_a], y[~half_a], eid_b[~half_a], n_ev_b, strict["fp"])
        # 消融：零配额（纯逐端点标定）与均匀配额
        thr_z, _ = thresholds_from_quotas(s[~half_a], y[~half_a], ep[~half_a], n_ep,
                                          np.zeros(n_ep, dtype=np.int64))
        zero_q = apply_per_endpoint_thresholds(s[~half_a], y[~half_a], ep[~half_a], thr_z,
                                               eid_b[~half_a], n_ev_b)
        eq_q = quotas_from_shares(np.full(n_ep, 1.0 / n_ep), allowed_b[r])
        thr_e, _ = thresholds_from_quotas(s[~half_a], y[~half_a], ep[~half_a], n_ep, eq_q)
        equal_q = apply_per_endpoint_thresholds(s[~half_a], y[~half_a], ep[~half_a], thr_e,
                                                eid_b[~half_a], n_ev_b)
        boot_zq = bootstrap_paired(ev_max_b[ids_b] >= b_base["threshold"],
                                   ev_max_b[ids_b] >= np.asarray(thr_z, dtype=np.float64)[ev_ep_b],
                                   ev_ep_b)
        tb_vec = np.asarray(thr_b, dtype=np.float64)
        assert abs(float((ev_max_b[ids_b] >= tb_vec[ev_ep_b]).mean()) - got["event_recall"]) < 1e-12
        boot_h3 = bootstrap_paired(ev_max_b[ids_b] >= b_base["threshold"],
                                   ev_max_b[ids_b] >= tb_vec[ev_ep_b], ev_ep_b)
        group3["honest"][str(r)] = {
            "paired_endpoint_bootstrap": boot_h3,
            "allowed_fp_half_b": allowed_b[r],
            "half_a_allocation_fp_total": int(fp_vec.sum()),
            "n_endpoints_without_negative_in_half_b": n_empty,
            "half_b_baseline_uniform": b_base,
            "half_b_transferred_share_allocation": got,
            "honest_gain_event_recall": got["event_recall"] - b_base["event_recall"],
            "half_b_strict_thresholds_from_half_a": strict,
            "half_b_strict_global_threshold_from_half_a": strict_base,
            "half_b_baseline_at_matched_fp": matched,
            "ablation_zero_quota_pure_per_endpoint_calibration": zero_q,
            "ablation_zero_quota_vs_baseline_bootstrap": boot_zq,
            "ablation_equal_share_quota": equal_q,
        }
        log(f"  诚实 预算 {r}: 后半均匀={b_base['event_recall']:.6f} 份额迁移="
            f"{got['event_recall']:.6f} (fp={got['fp']}) 增益="
            f"{got['event_recall'] - b_base['event_recall']:+.6f} 配对CI="
            f"{boot_h3.get('paired_ci95_delta')} 边际CI(基线)={boot_h3.get('marginal_ci95_baseline')}")
        log(f"    严格迁移对照 预算 {r}: 候选阈值冻结={strict['event_recall']:.6f}(fp={strict['fp']}) "
            f"全局阈值冻结={strict_base['event_recall']:.6f}(fp={strict_base['fp']}) "
            f"后半同误报全局阈值={matched['event_recall']:.6f}(fp={matched['fp']})")
        log(f"    消融 预算 {r}: 零配额纯逐端点标定={zero_q['event_recall']:.6f}(fp={zero_q['fp']}) "
            f"配对CI={boot_zq.get('paired_ci95_delta')} | 均匀配额={equal_q['event_recall']:.6f}"
            f"(fp={equal_q['fp']})")

    # 逐端点标定的时间可迁移性（只用前半负窗，不用任何标签，冻结后应用到后半）
    thr_z_a, _ = thresholds_from_quotas(s[half_a], y[half_a], ep[half_a], n_ep,
                                        np.zeros(n_ep, dtype=np.int64))
    tza = np.asarray(thr_z_a, dtype=np.float64)
    frozen_z = apply_per_endpoint_thresholds(s[~half_a], y[~half_a], ep[~half_a], thr_z_a,
                                             eid_b[~half_a], n_ev_b)
    matched_z = eval_global(s[~half_a], y[~half_a], eid_b[~half_a], n_ev_b, frozen_z["fp"])
    boot_fz = bootstrap_paired(ev_max_b[ids_b] >= matched_z["threshold"],
                               ev_max_b[ids_b] >= tza[ev_ep_b], ev_ep_b)
    group3["transferability_of_per_endpoint_calibration"] = {
        "描述": "逐端点阈值只由前半段负窗（正常流量）标定后冻结，应用到后半段；"
                "对照为后半段上实测误报数相同的单一全局阈值",
        "half_b_frozen_per_endpoint": frozen_z,
        "half_b_global_threshold_at_matched_fp": matched_z,
        "paired_endpoint_bootstrap": boot_fz,
    }
    log(f"  逐端点标定时间可迁移性：前半标定冻结后应用到后半 fp={frozen_z['fp']} "
        f"召回={frozen_z['event_recall']:.6f}；后半同误报全局阈值 召回="
        f"{matched_z['event_recall']:.6f} 配对CI={boot_fz.get('paired_ci95_delta')}")

    # ---------- 第 4 组：两机制组合 ----------
    log("第 4 组：累积规则 + 端点分配 组合")
    g_best = stats[best_name_primary]
    ev_max_best = event_max(g_best, p_idx, ev_of_pos, n_events)
    stairs_c = endpoint_staircases(g_best, y, ep, n_ep, ev_ep, ev_max_best)
    group4 = {"combined_rule": best_name_primary, "oracle_upper_bound": {}, "honest": {}}
    for r in FP_BUDGETS:
        alloc_c = greedy_allocate(stairs_c, allowed_full[r])
        m1_gain = group2["oracle_summary"][str(r)]["oracle_gain_event_recall"]
        m2_gain = group3["oracle_upper_bound"][str(r)]["oracle_gain_event_recall"]
        comb_gain = alloc_c["events"] / n_events - base_full[r]["event_recall"]
        tc = np.asarray(alloc_c["thresholds"], dtype=np.float64)
        boot_o4 = bootstrap_paired(ev_max_s >= base_full[r]["threshold"],
                                   ev_max_best >= tc[ev_ep], ev_ep)
        group4["oracle_upper_bound"][str(r)] = {
            "paired_endpoint_bootstrap": boot_o4,
            "combined_event_recall": alloc_c["events"] / n_events,
            "baseline_event_recall": base_full[r]["event_recall"],
            "combined_gain": comb_gain, "m1_gain_alone": m1_gain, "m2_gain_alone": m2_gain,
            "additive_prediction": m1_gain + m2_gain,
            "orthogonality_ratio": comb_gain / (m1_gain + m2_gain) if (m1_gain + m2_gain) > 0 else None,
        }
        log(f"  预算 {r}: 组合召回={alloc_c['events'] / n_events:.6f} 组合增益={comb_gain:+.6f} "
            f"(M1 单独 {m1_gain:+.6f} + M2 单独 {m2_gain:+.6f} = {m1_gain + m2_gain:+.6f})")

    sel_name_b = group2["honest"][str(PRIMARY_BUDGET)]["selected_on_half_a"]
    g_sel = stats[sel_name_b]
    ev_max_sel_a = event_max(np.where(half_a, g_sel, -np.inf), p_idx, ev_of_pos, n_events)
    for r in FP_BUDGETS:
        st_a = endpoint_staircases(g_sel[half_a], y[half_a], ep[half_a], n_ep, ev_ep[ids_a], ev_max_sel_a[ids_a])
        al_a = greedy_allocate(st_a, allowed_a[r])
        fv = np.asarray(al_a["fp_per_endpoint"], dtype=np.float64)
        sh = fv / fv.sum() if fv.sum() > 0 else np.zeros(n_ep)
        q = quotas_from_shares(sh, allowed_b[r]) if fv.sum() > 0 else np.zeros(n_ep, dtype=np.int64)
        tb, _ = thresholds_from_quotas(g_sel[~half_a], y[~half_a], ep[~half_a], n_ep, q)
        got = apply_per_endpoint_thresholds(g_sel[~half_a], y[~half_a], ep[~half_a], tb, eid_b[~half_a], n_ev_b)
        b_base = eval_global(s[~half_a], y[~half_a], eid_b[~half_a], n_ev_b, allowed_b[r])
        ev_max_sel_bh = event_max(np.where(~half_a, g_sel, -np.inf), p_idx, ev_of_pos, n_events)
        boot_h4 = bootstrap_paired(ev_max_b[ids_b] >= b_base["threshold"],
                                   ev_max_sel_bh[ids_b] >= np.asarray(tb, dtype=np.float64)[ev_ep_b],
                                   ev_ep_b)
        group4["honest"][str(r)] = {"rule": sel_name_b, "half_b_combined": got,
                                    "half_b_baseline_uniform": b_base,
                                    "honest_gain_event_recall": got["event_recall"] - b_base["event_recall"],
                                    "paired_endpoint_bootstrap": boot_h4}
        log(f"  诚实组合 预算 {r}: {got['event_recall']:.6f} vs 基线 {b_base['event_recall']:.6f} "
            f"增益 {got['event_recall'] - b_base['event_recall']:+.6f} 配对CI="
            f"{boot_h4.get('paired_ci95_delta')}")

    # ---------- 预注册判据裁决 ----------
    pk = str(PRIMARY_BUDGET)
    m1_oracle = group2["oracle_summary"][pk]["oracle_gain_event_recall"]
    m1_honest = group2["honest"][pk]["honest_gain_event_recall"]
    m1_boot = group2["honest"][pk]["paired_endpoint_bootstrap"]
    m2_oracle = group3["oracle_upper_bound"][pk]["oracle_gain_event_recall"]
    m2_honest = group3["honest"][pk]["honest_gain_event_recall"]
    m2_boot = group3["honest"][pk]["paired_endpoint_bootstrap"]
    m1_go = (p75_multi_primary is not None and p75_multi_primary >= PREREG_M1_P75_GO
             and bool(m1_boot.get("paired_ci_lower_gt_zero"))
             and m1_honest >= PREREG_M1_HONEST_GAIN_GO)
    m1_reject = ((p75_multi_primary is not None and p75_multi_primary < PREREG_M1_P75_REJECT)
                 or bool(m1_boot.get("paired_ci_contains_zero"))
                 or m1_oracle < PREREG_M1_ORACLE_GAIN_REJECT)
    m2_go = (slope_gini >= PREREG_M2_GINI_GO and bool(m2_boot.get("paired_ci_lower_gt_zero"))
             and m2_honest >= PREREG_M2_HONEST_GAIN_GO)
    m2_reject = (slope_gini < PREREG_M2_GINI_REJECT
                 or bool(m2_boot.get("paired_ci_contains_zero"))
                 or m2_oracle < PREREG_M2_ORACLE_GAIN_REJECT)
    verdict = {
        "M1_evidence_accumulation": {
            "missed_multiwindow_member_score_p75": p75_multi_primary,
            "oracle_gain@0.01": m1_oracle, "honest_gain@0.01": m1_honest,
            "honest_paired_ci95_delta": m1_boot.get("paired_ci95_delta"),
            "honest_paired_ci_lower_gt_zero": m1_boot.get("paired_ci_lower_gt_zero"),
            "honest_marginal_ci95_baseline": m1_boot.get("marginal_ci95_baseline"),
            "go": bool(m1_go), "reject": bool(m1_reject),
            "verdict": "GO" if m1_go and not m1_reject else ("REJECT" if m1_reject else "INCONCLUSIVE"),
        },
        "M2_conditional_budget_allocation": {
            "marginal_slope_gini": slope_gini,
            "oracle_gain@0.01": m2_oracle, "honest_gain@0.01": m2_honest,
            "honest_paired_ci95_delta": m2_boot.get("paired_ci95_delta"),
            "honest_paired_ci_lower_gt_zero": m2_boot.get("paired_ci_lower_gt_zero"),
            "honest_marginal_ci95_baseline": m2_boot.get("marginal_ci95_baseline"),
            "go": bool(m2_go), "reject": bool(m2_reject),
            "verdict": "GO" if m2_go and not m2_reject else ("REJECT" if m2_reject else "INCONCLUSIVE"),
        },
    }
    both_rejected = verdict["M1_evidence_accumulation"]["verdict"] == "REJECT" and \
        verdict["M2_conditional_budget_allocation"]["verdict"] == "REJECT"
    verdict["route_level_conclusion"] = ("决策规则层无余量，该路线整体否决" if both_rejected
                                         else "至少一个机制未被预注册判据否决，见逐条判定")
    log("=" * 30 + " 预注册判据裁决 " + "=" * 30)
    log(json.dumps(verdict, ensure_ascii=False, indent=2))

    cfg = {"purpose": "E5 机制余量证伪：冻结分数下决策规则层的事件召回余量",
           "prereg": PREREG, "grids": {"consec_k": list(CONSEC_K), "decay_rho": list(DECAY_RHO),
                                       "topm_m_L": [list(x) for x in TOPM_ML],
                                       "gap_policies": list(GAP_POLICIES), "Lmax": LMAX},
           "thresholds": {"M1_p75_go": PREREG_M1_P75_GO, "M1_p75_reject": PREREG_M1_P75_REJECT,
                          "M1_honest_gain_go": PREREG_M1_HONEST_GAIN_GO,
                          "M1_oracle_gain_reject": PREREG_M1_ORACLE_GAIN_REJECT,
                          "M2_gini_go": PREREG_M2_GINI_GO, "M2_gini_reject": PREREG_M2_GINI_REJECT,
                          "M2_honest_gain_go": PREREG_M2_HONEST_GAIN_GO,
                          "M2_oracle_gain_reject": PREREG_M2_ORACLE_GAIN_REJECT},
           "inputs": [f"{SRC_RUN}/val_scores.parquet", f"{PREPARED}/development-wide.parquet"],
           "no_retrain": True, "scores_frozen": True}
    with open(f"{OUT_DIR}/config.json", "w") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    result = {
        "purpose": cfg["purpose"], "prereg": PREREG,
        "baseline_reproduction_vs_a1": repro,
        "split_meta": split_meta,
        "group1_missed_event_score_shape": group1,
        "group2_evidence_accumulation": group2,
        "group3_endpoint_budget_allocation": group3,
        "group4_orthogonality": group4,
        "verdict": verdict,
        "external_facts_used": {
            "E1_endpoint_cluster_bootstrap_ci95_of_baseline_event_recall": [0.2329, 0.7021],
            "E1_event_cluster_bootstrap_ci95": [0.5069, 0.5576],
            "E1_single_window_event_lag1_4_nonempty_history_hist": {"0": 41, "1": 130, "2": 295,
                                                                    "3": 321, "4": 302},
            "note": "以上为 E1 实验实测值，本实验据此改用端点簇配对自助判定",
        },
        "total_wall_seconds": time.time() - t0,
        "screening_only": True, "formal_paper_evidence": False, "final_accessed": False,
        "split_names_seen": d["split_names"],
    }
    with open(f"{OUT_DIR}/result.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log(f"完成 用时 {time.time() - t0:.1f}s {mem_line('end')}")


if __name__ == "__main__":
    main()
