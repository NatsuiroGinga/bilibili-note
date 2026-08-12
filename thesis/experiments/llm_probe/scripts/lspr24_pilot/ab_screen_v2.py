"""方案 A / B 前提筛选先导实验（向量化 + 磁盘缓存版）。

相对 v1 的两处修正：
1. 历史特征拼接由逐行 Python 循环改为 searchsorted 全向量化；
2. 窗口聚合结果落盘缓存，后续消融不再重跑 parquet 全量扫描。

两个可证伪前提：
  A 前提：信息分布在多个时间尺度 → 快(lag1-4)+慢(lag8-32) 应显著优于最佳单尺度。
  B 前提：字段间存在交互信息   → 允许交互的模型应显著优于纯可加模型（决策桩）。

安全边界：只用 last_us < CUT_US 的开发区行；身份仅用于端点分组，绝不进特征；
绝对时间仅用于窗口归属与切分，绝不进特征。
"""

from __future__ import annotations

import logging
import os
import sys
import time

import numpy as np
import pyarrow.parquet as pq
import pyarrow.compute as pc
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)

PARQUET = "/Users/bilibili/personal/note/thesis/experiments/llm_probe/data/raw/lspr24-v1/lspr24_v2.parquet"
CACHE = "/tmp/ab_windows_cache.npz"
CUT_US = 1709802623 * 1_000_000
BEAT_US = 5_000_000
TOP_ENDPOINTS = 300
SEED = 42
EP_SHIFT = 1 << 40  # 端点编码位移，保证 ep*SHIFT+win 无碰撞

AGG_COLS = [
    "Tot Fwd Pkts", "Tot Bwd Pkts",
    "Total Length of Fwd Packet", "Total Length of Bwd Packet",
    "Flow Duration", "Flow IAT Mean", "Packet Length Mean", "Packet Length Std",
    "SYN Flag Cnt", "RST Flag Cnt", "ACK Flag Cnt", "PSH Flag Cnt", "FIN Flag Cnt",
    "Down/Up Ratio", "Fwd Seg Size Min", "Active Mean", "Idle Mean",
]


def defended_endpoint(b):
    """返回每行的被防御端点字符串数组；两端外部则为 None。"""
    es = np.asarray(b.column("External_src").to_pylist(), dtype=object)
    ed = np.asarray(b.column("External_dst").to_pylist(), dtype=object)
    sip = np.asarray(b.column("SrcIP").to_pylist(), dtype=object)
    dip = np.asarray(b.column("DstIP").to_pylist(), dtype=object)
    src_in = es == "0"
    dst_in = ed == "0"
    return np.where(src_in, sip, np.where(dst_in, dip, None))


def build_cache() -> None:
    pf = pq.ParquetFile(PARQUET)

    t0 = time.time()
    from collections import Counter
    counter: Counter = Counter()
    for rg in range(pf.metadata.num_row_groups):
        b = pf.read_row_group(rg, columns=["SrcIP", "DstIP", "External_src", "External_dst", "mTimestampLast"])
        b = b.filter(pc.less(b.column("mTimestampLast"), CUT_US))
        if b.num_rows == 0:
            continue
        ep = defended_endpoint(b)
        counter.update([e for e in ep if e is not None])
    top = [ip for ip, _ in counter.most_common(TOP_ENDPOINTS)]
    code = {ip: i for i, ip in enumerate(top)}
    logger.info("一遍：被防御端点 %d 个，取 top %d，耗时 %.1fs", len(counter), len(top), time.time() - t0)

    t0 = time.time()
    keys_l, feats_l, labs_l = [], [], []
    cols = ["SrcIP", "DstIP", "External_src", "External_dst", "mTimestampLast", "Label"] + AGG_COLS
    for rg in range(pf.metadata.num_row_groups):
        b = pf.read_row_group(rg, columns=cols)
        b = b.filter(pc.less(b.column("mTimestampLast"), CUT_US))
        if b.num_rows == 0:
            continue
        ep = defended_endpoint(b)
        ec = np.array([code.get(e, -1) for e in ep], dtype=np.int64)
        keep = ec >= 0
        if not keep.any():
            continue
        last = b.column("mTimestampLast").to_numpy()[keep]
        win = (last // BEAT_US).astype(np.int64)
        keys_l.append(ec[keep] * EP_SHIFT + win)
        labs_l.append(b.column("Label").to_numpy(zero_copy_only=False)[keep].astype(np.int8))
        f = np.column_stack([
            b.column(c).to_numpy(zero_copy_only=False)[keep].astype(np.float64) for c in AGG_COLS
        ])
        feats_l.append(np.nan_to_num(f, nan=0.0, posinf=0.0, neginf=0.0))
    keys = np.concatenate(keys_l); feats = np.vstack(feats_l); labs = np.concatenate(labs_l)
    logger.info("二遍：流级行 %d，耗时 %.1fs", len(keys), time.time() - t0)

    # 向量化窗口聚合：按 key 排序后用 reduceat 分段统计
    t0 = time.time()
    order = np.argsort(keys, kind="stable")
    keys, feats, labs = keys[order], feats[order], labs[order]
    uniq, start = np.unique(keys, return_index=True)
    cnt = np.diff(np.append(start, len(keys))).astype(np.float32)
    ssum = np.add.reduceat(feats, start, axis=0)
    smax = np.maximum.reduceat(feats, start, axis=0)
    ylab = np.maximum.reduceat(labs.astype(np.int8), start)
    mean = ssum / cnt[:, None]
    cur = np.hstack([cnt[:, None], ssum, mean, smax]).astype(np.float32)
    ep_code = (uniq // EP_SHIFT).astype(np.int32)
    win = (uniq % EP_SHIFT).astype(np.int64)
    logger.info("聚合：窗口 %d 个 × %d 维，正类率 %.4f，耗时 %.1fs",
                len(uniq), cur.shape[1], ylab.mean(), time.time() - t0)

    np.savez_compressed(CACHE, cur=cur, win=win, ep=ep_code, y=ylab, uniq=uniq)
    logger.info("缓存已落盘：%s", CACHE)


def add_history(cur, uniq, lags):
    """向量化历史拼接：uniq 已升序，用 searchsorted 定位 key-lag 的同端点历史窗。"""
    n, d = cur.shape
    out = [cur]
    for L in lags:
        tgt = uniq - L
        pos = np.searchsorted(uniq, tgt)
        pos_c = np.clip(pos, 0, n - 1)
        hit = uniq[pos_c] == tgt          # 同端点同差值命中（跨端点因高位不同必然不等）
        blk = np.zeros((n, d + 1), dtype=np.float32)
        blk[hit, :d] = cur[pos_c[hit]]
        blk[hit, d] = 1.0
        out.append(blk)
    return np.hstack(out)


def evaluate(name, x, y, win, split_w, max_leaf_nodes=31, max_depth=None):
    tr = win < split_w
    va = ~tr
    if y[tr].sum() < 10 or y[va].sum() < 10:
        logger.warning("%s：正类过少，跳过", name)
        return None
    t0 = time.time()
    clf = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.1,
        max_leaf_nodes=max_leaf_nodes, max_depth=max_depth,
        early_stopping=True, validation_fraction=0.1, random_state=SEED,
    )
    clf.fit(x[tr], y[tr])
    p = clf.predict_proba(x[va])[:, 1]
    ap = average_precision_score(y[va], p)
    auc = roc_auc_score(y[va], p)
    print(f"  {name:32} PR-AUC={ap:.4f}  ROC-AUC={auc:.4f}  维度={x.shape[1]:4}  {time.time()-t0:.0f}s")
    return ap


def main() -> None:
    if not os.path.exists(CACHE):
        build_cache()
    z = np.load(CACHE)
    cur, win, y, uniq = z["cur"], z["win"], z["y"], z["uniq"]
    logger.info("载入缓存：窗口 %d × %d 维，正类率 %.4f", len(y), cur.shape[1], y.mean())

    split_w = int(np.quantile(win, 0.75))
    logger.info("按窗口时间切分：训练 %d / 验证 %d", int((win < split_w).sum()), int((win >= split_w).sum()))

    print("\n" + "=" * 80)
    print("方案 A 前提：多时间尺度是否必需？")
    print("=" * 80)
    ap1 = evaluate("H=1 仅当前窗（无历史）", cur, y, win, split_w)
    apf = evaluate("快尺度 lag 1-4", add_history(cur, uniq, [1, 2, 3, 4]), y, win, split_w)
    aps = evaluate("慢尺度 lag 8/16/24/32", add_history(cur, uniq, [8, 16, 24, 32]), y, win, split_w)
    apb = evaluate("快+慢 双尺度（A 的动机）", add_history(cur, uniq, [1, 2, 3, 4, 8, 16, 24, 32]), y, win, split_w)

    print("\n" + "=" * 80)
    print("方案 B 前提：字段交互是否携带可加效应之外的信息？")
    print("=" * 80)
    ap_add = evaluate("纯可加（决策桩 depth=1）", cur, y, win, split_w, max_leaf_nodes=2, max_depth=1)
    ap_int = evaluate("允许交互（leaf=31）", cur, y, win, split_w, max_leaf_nodes=31)
    ap_deep = evaluate("强交互（leaf=127）", cur, y, win, split_w, max_leaf_nodes=127)

    print("\n" + "=" * 80)
    print("先导裁决依据（非最终，不得写入论文）")
    print("=" * 80)
    if None not in (ap1, apf, aps, apb):
        best_single = max(apf, aps)
        print(f"A 前提  双尺度 {apb:.4f} vs 最佳单尺度 {best_single:.4f}  →  {(apb-best_single)/best_single*100:+.1f}%")
        print(f"        含历史 {max(apf,aps,apb):.4f} vs 无历史 {ap1:.4f}      →  {(max(apf,aps,apb)-ap1)/ap1*100:+.1f}%")
    if None not in (ap_add, ap_int, ap_deep):
        print(f"B 前提  允许交互 {ap_int:.4f} vs 纯可加 {ap_add:.4f}    →  {(ap_int-ap_add)/ap_add*100:+.1f}%")
        print(f"        强交互 {ap_deep:.4f} 边际                    →  {(ap_deep-ap_int)/ap_int*100:+.1f}%")


if __name__ == "__main__":
    main()
