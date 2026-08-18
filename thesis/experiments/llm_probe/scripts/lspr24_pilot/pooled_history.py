"""长时历史是否只输在维度灾难？——池化压缩 vs 原始拼接。

Q2 发现 lag1-32 原始拼接（476 维）反而不如 lag1-4（264 维），
但这可能是维度灾难而非"长时无信息"。本实验用固定维度的池化摘要区分两者：

  - 长历史池化：把 lag 5-32 压成 mean/max/last 三组摘要（维度与 lag1-4 相当）
  - 若池化后长历史带来增益 → 长时确有信息，但必须压缩才可用（这正是 RWKV 状态做的事）
  - 若池化后仍无增益 → 长时确实无信息，"长时状态检测"定位不成立

同时给出错误相对下降口径的数字（已裁决为主门槛）。
"""

from __future__ import annotations

import os
import sys
import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score

CACHE = sys.argv[1] if len(sys.argv) > 1 else "/root/autodl-tmp/ab-pilot/ab_windows_cache.npz"
SEED = 42


def gather(cur, uniq, lag):
    """返回 (值矩阵, 命中掩码)。"""
    n, d = cur.shape
    tgt = uniq - lag
    pos = np.clip(np.searchsorted(uniq, tgt), 0, n - 1)
    hit = uniq[pos] == tgt
    val = np.zeros((n, d), dtype=np.float32)
    val[hit] = cur[pos[hit]]
    return val, hit


def concat_hist(cur, uniq, lags):
    out = [cur]
    for lag in lags:
        val, hit = gather(cur, uniq, lag)
        out.append(np.hstack([val, hit[:, None].astype(np.float32)]))
    return np.hstack(out)


def pooled_hist(cur, uniq, lags):
    """把多个滞后步压成 mean / max / 命中计数，维度与单步相当。"""
    n, d = cur.shape
    acc = np.zeros((n, d), dtype=np.float32)
    mx = np.full((n, d), -np.inf, dtype=np.float32)
    cnt = np.zeros(n, dtype=np.float32)
    for lag in lags:
        val, hit = gather(cur, uniq, lag)
        acc[hit] += val[hit]
        np.maximum(mx[hit], val[hit], out=mx[hit])
        cnt += hit
    mean = acc / np.maximum(cnt, 1)[:, None]
    mx[~np.isfinite(mx)] = 0.0
    return np.hstack([mean, mx, cnt[:, None]])


def ev(name, x, y, win, split_w, leaf=127):
    tr = win < split_w
    va = ~tr
    t0 = time.time()
    clf = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.1, max_leaf_nodes=leaf,
        early_stopping=True, validation_fraction=0.1, random_state=SEED,
    )
    clf.fit(x[tr], y[tr])
    ap = average_precision_score(y[va], clf.predict_proba(x[va])[:, 1])
    print(f"  {name:40} PR-AUC={ap:.4f}  err={1-ap:.4f}  dim={x.shape[1]:4}  {time.time()-t0:.0f}s",
          flush=True)
    return ap


def main() -> None:
    z = np.load(CACHE)
    cur, win, y, uniq = z["cur"], z["win"], z["y"], z["uniq"]
    split_w = int(np.quantile(win, 0.75))
    print(f"窗口 {len(y):,}，正类率 {y.mean():.4f}，线程 {os.cpu_count()}\n", flush=True)

    print("=" * 90, flush=True)
    print("长时历史：原始拼接 vs 池化压缩（控制维度）", flush=True)
    print("=" * 90, flush=True)
    base = ev("纯当前窗（无历史）", cur, y, win, split_w)
    short = ev("短历史 lag1-4 原始拼接", concat_hist(cur, uniq, [1, 2, 3, 4]), y, win, split_w)
    long_cat = ev("长历史 lag1-32 原始拼接（476维）",
                  concat_hist(cur, uniq, [1, 2, 3, 4, 8, 16, 24, 32]), y, win, split_w)
    long_pool = ev("短拼接 + 长历史池化摘要",
                   np.hstack([concat_hist(cur, uniq, [1, 2, 3, 4]),
                              pooled_hist(cur, uniq, [5, 8, 12, 16, 20, 24, 28, 32])]),
                   y, win, split_w)
    very_long = ev("短拼接 + 超长池化 lag33-128",
                   np.hstack([concat_hist(cur, uniq, [1, 2, 3, 4]),
                              pooled_hist(cur, uniq, list(range(33, 129, 8)))]),
                   y, win, split_w)

    print("\n" + "=" * 90, flush=True)
    # 16.1% 是本课题早期先导实验自定的门槛，不是朱焱雷论文中的数字。
    # 2026-08-17 核对其原件全文搜索 16.1 零命中；其第三章表 3-7 报的是
    # PGD-20 鲁棒准确率的绝对百分点提升（ET-BERT +12.30、BUPT-CNN +9.30）。
    print("错误相对下降口径（已裁决为主门槛，本课题自定阈值 16.1%）", flush=True)
    print("=" * 90, flush=True)
    eb = 1 - base
    for nm, ap in [("短历史 lag1-4", short), ("长历史原始拼接", long_cat),
                   ("长历史池化", long_pool), ("超长池化", very_long)]:
        er = (eb - (1 - ap)) / eb * 100
        flag = "达标" if er >= 16.1 else "未达标"
        print(f"  {nm:24} 相对纯当前窗错误下降 {er:+6.1f}%   [{flag}]", flush=True)
    best_short = short
    print(f"\n  长历史池化相对短历史的额外错误下降："
          f"{((1-best_short) - (1-long_pool)) / (1-best_short) * 100:+.1f}%", flush=True)
    print(f"  超长池化相对短历史的额外错误下降："
          f"{((1-best_short) - (1-very_long)) / (1-best_short) * 100:+.1f}%", flush=True)


if __name__ == "__main__":
    main()
