"""A/B 判别与骨干正当性先导实验（服务器版，消费预聚合缓存）。

回答三个问题：
  Q1 字段交互的增益，在已经提供历史特征后是否依然存在？
     （若消失 → 交互与历史在抢同一份信息，B 的独立价值存疑）
  Q2 历史增益里有多少只是 lag-1 的"最近有活动"存在性？
     （若 lag-1 就拿走大部分 → "长时"定位站不住）
  Q3 在强交互条件下，加历史相对纯当前窗还能拿多少？
     （这是 RWKV 骨干必须从 FIELD-TRANSFORMER 手里赢下的margin）

不读原始 parquet、不接触最终 20%、不含身份或绝对时间特征。
"""

from __future__ import annotations

import os
import sys
import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

CACHE = sys.argv[1] if len(sys.argv) > 1 else "/root/autodl-tmp/ab-pilot/ab_windows_cache.npz"
SEED = 42


def add_history(cur, uniq, lags):
    n, d = cur.shape
    out = [cur]
    for lag in lags:
        tgt = uniq - lag
        pos = np.clip(np.searchsorted(uniq, tgt), 0, n - 1)
        hit = uniq[pos] == tgt
        blk = np.zeros((n, d + 1), dtype=np.float32)
        blk[hit, :d] = cur[pos[hit]]
        blk[hit, d] = 1.0
        out.append(blk)
    return np.hstack(out)


def ev(name, x, y, win, split_w, leaf=31, depth=None):
    tr = win < split_w
    va = ~tr
    t0 = time.time()
    clf = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.1, max_leaf_nodes=leaf, max_depth=depth,
        early_stopping=True, validation_fraction=0.1, random_state=SEED,
    )
    clf.fit(x[tr], y[tr])
    p = clf.predict_proba(x[va])[:, 1]
    ap = average_precision_score(y[va], p)
    auc = roc_auc_score(y[va], p)
    print(f"  {name:36} PR-AUC={ap:.4f}  ROC-AUC={auc:.4f}  dim={x.shape[1]:4}  {time.time()-t0:.0f}s",
          flush=True)
    return ap


def main() -> None:
    z = np.load(CACHE)
    cur, win, y, uniq = z["cur"], z["win"], z["y"], z["uniq"]
    split_w = int(np.quantile(win, 0.75))
    print(f"窗口 {len(y):,} × {cur.shape[1]} 维，正类率 {y.mean():.4f}，线程 {os.cpu_count()}\n", flush=True)

    x_l1 = add_history(cur, uniq, [1])
    x_f = add_history(cur, uniq, [1, 2, 3, 4])
    x_all = add_history(cur, uniq, [1, 2, 3, 4, 8, 16, 24, 32])

    print("=" * 86, flush=True)
    print("Q1 字段交互增益在有历史条件下是否依然存在？", flush=True)
    print("=" * 86, flush=True)
    q1_add = ev("含历史 + 纯可加（stump）", x_f, y, win, split_w, leaf=2, depth=1)
    q1_int = ev("含历史 + 允许交互（leaf=31）", x_f, y, win, split_w, leaf=31)
    q1_deep = ev("含历史 + 强交互（leaf=127）", x_f, y, win, split_w, leaf=127)

    print("\n" + "=" * 86, flush=True)
    print("Q2 历史增益的构成：lag-1 存在性 vs 真实长时结构", flush=True)
    print("=" * 86, flush=True)
    q2_0 = ev("无历史", cur, y, win, split_w, leaf=127)
    q2_1 = ev("仅 lag-1", x_l1, y, win, split_w, leaf=127)
    q2_4 = ev("lag 1-4", x_f, y, win, split_w, leaf=127)
    q2_all = ev("lag 1-32 全historical", x_all, y, win, split_w, leaf=127)

    print("\n" + "=" * 86, flush=True)
    print("Q3 RWKV 骨干必须赢下的 margin（纯当前窗强交互 vs 加历史）", flush=True)
    print("=" * 86, flush=True)
    print(f"  纯当前窗强交互（FIELD-TRANSFORMER 代理）  PR-AUC={q2_0:.4f}", flush=True)
    print(f"  加全历史强交互（RWKV 骨干代理）           PR-AUC={q2_all:.4f}", flush=True)

    print("\n" + "=" * 86, flush=True)
    print("先导裁决依据（非最终，不得写入论文）", flush=True)
    print("=" * 86, flush=True)
    print(f"Q1  交互增益（有历史时）  {q1_int:.4f} vs 可加 {q1_add:.4f}"
          f"  →  {(q1_int - q1_add) / q1_add * 100:+.1f}%", flush=True)
    print(f"    强交互边际            {(q1_deep - q1_int) / q1_int * 100:+.1f}%", flush=True)
    print(f"Q2  lag-1 拿走历史增益的  {(q2_1 - q2_0) / max(q2_all - q2_0, 1e-9) * 100:.0f}%"
          f"（lag1 {q2_1:.4f}，全史 {q2_all:.4f}，无史 {q2_0:.4f}）", flush=True)
    print(f"    lag5-32 额外贡献      {(q2_all - q2_4) / q2_4 * 100:+.2f}%", flush=True)
    print(f"Q3  骨干 margin           {(q2_all - q2_0) / q2_0 * 100:+.1f}%"
          f"  ← RWKV 必须从纯当前窗字段模型手里赢下这个数", flush=True)


if __name__ == "__main__":
    main()
