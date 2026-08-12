"""方案 A/B 前提筛选（服务器版，消费本机预聚合缓存）。

输入：ab_windows_cache.npz（本机已完成 parquet 扫描与 5 秒窗口聚合）
输出：A 前提（多时间尺度）与 B 前提（字段交互）的 PR-AUC 对照

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


def load():
    z = np.load(CACHE)
    return z["cur"], z["win"], z["y"], z["uniq"]


def add_history(cur, uniq, lags):
    """向量化历史拼接：同端点同差值命中（跨端点因高位编码不同必然不等）。"""
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


def evaluate(name, x, y, win, split_w, leaf=31, depth=None, iters=200):
    tr = win < split_w
    va = ~tr
    t0 = time.time()
    clf = HistGradientBoostingClassifier(
        max_iter=iters, learning_rate=0.1, max_leaf_nodes=leaf, max_depth=depth,
        early_stopping=True, validation_fraction=0.1, random_state=SEED,
    )
    clf.fit(x[tr], y[tr])
    p = clf.predict_proba(x[va])[:, 1]
    ap = average_precision_score(y[va], p)
    auc = roc_auc_score(y[va], p)
    print(f"  {name:30} PR-AUC={ap:.4f}  ROC-AUC={auc:.4f}  dim={x.shape[1]:4}  "
          f"iter={clf.n_iter_:3}  {time.time()-t0:.0f}s", flush=True)
    return ap


def main() -> None:
    cur, win, y, uniq = load()
    print(f"窗口 {len(y):,} × {cur.shape[1]} 维，正类率 {y.mean():.4f}，"
          f"线程 {os.cpu_count()}", flush=True)
    split_w = int(np.quantile(win, 0.75))
    print(f"按窗口时间切分：训练 {(win < split_w).sum():,} / 验证 {(win >= split_w).sum():,}\n", flush=True)

    print("=" * 82, flush=True)
    print("方案 A 前提：多时间尺度记忆是否必需？", flush=True)
    print("=" * 82, flush=True)
    a_none = evaluate("H=1 仅当前窗", cur, y, win, split_w)
    a_fast = evaluate("快尺度 lag 1-4", add_history(cur, uniq, [1, 2, 3, 4]), y, win, split_w)
    a_slow = evaluate("慢尺度 lag 8/16/24/32", add_history(cur, uniq, [8, 16, 24, 32]), y, win, split_w)
    a_both = evaluate("快+慢 双尺度（A 的动机）",
                      add_history(cur, uniq, [1, 2, 3, 4, 8, 16, 24, 32]), y, win, split_w)

    print("\n" + "=" * 82, flush=True)
    print("方案 B 前提：字段交互是否携带可加效应之外的信息？", flush=True)
    print("=" * 82, flush=True)
    b_add = evaluate("纯可加（决策桩 depth=1）", cur, y, win, split_w, leaf=2, depth=1)
    b_int = evaluate("允许交互 leaf=31", cur, y, win, split_w, leaf=31)
    b_deep = evaluate("强交互 leaf=127", cur, y, win, split_w, leaf=127)

    print("\n" + "=" * 82, flush=True)
    print("先导裁决依据（非最终，不得写入论文）", flush=True)
    print("=" * 82, flush=True)
    best_single = max(a_fast, a_slow)
    print(f"A 前提  双尺度 {a_both:.4f} vs 最佳单尺度 {best_single:.4f}"
          f"  →  {(a_both - best_single) / best_single * 100:+.1f}%", flush=True)
    print(f"        含历史 {max(a_fast, a_slow, a_both):.4f} vs 无历史 {a_none:.4f}"
          f"  →  {(max(a_fast, a_slow, a_both) - a_none) / a_none * 100:+.1f}%", flush=True)
    print(f"B 前提  允许交互 {b_int:.4f} vs 纯可加 {b_add:.4f}"
          f"  →  {(b_int - b_add) / b_add * 100:+.1f}%", flush=True)
    print(f"        强交互边际 {(b_deep - b_int) / b_int * 100:+.1f}%", flush=True)


if __name__ == "__main__":
    main()
