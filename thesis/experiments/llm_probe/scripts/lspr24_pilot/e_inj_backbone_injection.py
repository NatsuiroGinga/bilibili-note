"""E-INJ：骨干 + RWKV 机制注入的增量实验（TQH-C2 真实数据，免训练代理）。

=== 这个实验回答什么 ===
不问「RWKV 适不适合当骨干」（注入框架下该问题不存在），
只问：**给定一个已经能编码单连接的骨干，额外注入跨连接状态机制能否带来增量，
且该增量是否特异于 RWKV-7 的 delta 规则而非任意状态？**

对照设计（全部共享同一骨干特征，唯一变量是注入的状态机制）：
  B0  骨干only            —— 单连接特征，无跨连接状态
  B1  骨干 + EMA 状态      —— 固定标量衰减，≈ RetNet
  B2  骨干 + 对角衰减状态   —— 输入条件对角衰减，≈ GLA / Mamba-1
  B3  骨干 + delta 规则状态 —— 含移除键主动擦除，≈ RWKV-7

判据（错误相对下降口径，门槛 16.1%）：
  注入有效  : max(B1,B2,B3) 相对 B0 错误相对下降 >= 16.1%
  RWKV 特异 : B3 相对 max(B1,B2) 错误相对下降 >= 5%

=== 防捷径 ===
- 身份与路径列（orig_h/resp_h/orig_p/resp_p/profile/capture_id/encryption_profile/uid/ts）
  一律不进特征，只用于分组与划分。
- 已知 A 组单元格内含流级捷径（5 个流特征即 err=0），因此**只做跨 testbed 评测**：
  A+C 训练，D 测试。
- 报告泄漏审计：用注入状态特征反预测 testbed，AUC 过高则该组结果作废。

结论仅为机制筛选，不满足公平预算，不得写入论文。
"""

from __future__ import annotations

import glob
import os
import re
import time

import numpy as np
import pyarrow.parquet as pq
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

SEED = 42
D_STATE = 16
FEATURE_DIR = os.environ.get("TQH_FEATURES", "/root/autodl-tmp/ab-pilot/tqh/features")

# 禁入：身份、路径捷径、标签、生成参数（interval_s/jitter_pct 是元数据不是可观测量）
FORBIDDEN = {
    "ts", "uid", "orig_h", "resp_h", "orig_p", "resp_p", "profile",
    "encryption_profile", "capture_id", "label_raw", "y",
    "interval_s", "jitter_pct",
}
# 类别列单独做序数编码
CATEGORICAL = {"proto", "conn_state", "history", "ja4", "ja4s", "ja4h"}


def load_cells():
    """载入单元格特征，按 testbed 分组返回。

    注意：A/B/C 在 `features/`，D 在 `features_D/`（两个 zip 的顶层目录名不同），
    必须同时扫描，否则 D 缺失会导致跨 testbed 测试集为空。
    """
    roots = [FEATURE_DIR, FEATURE_DIR.replace("/features", "/features_D")]
    paths = []
    for r in roots:
        paths += glob.glob(os.path.join(r, "[ABCD]_i*.parquet"))
    rows = []
    for p in sorted(paths):
        m = re.match(r"([ABCD])_i(\d+)_j(\d+)", os.path.basename(p))
        if not m:
            continue
        tb, itv, jit = m.group(1), int(m.group(2)), int(m.group(3))
        t = pq.read_table(p)
        cols = {c.name for c in t.schema}
        rows.append((tb, itv, jit, t, cols))
    return rows


def build(rows):
    """构造骨干特征、端点键、时间戳、标签、testbed。"""
    common = set.intersection(*[c for *_, c in rows])
    num_cols = sorted(c for c in common if c not in FORBIDDEN and c not in CATEGORICAL)
    cat_cols = sorted(c for c in common if c in CATEGORICAL)
    print(f"骨干数值列 {len(num_cols)}：{num_cols}", flush=True)
    print(f"类别列 {len(cat_cols)}：{cat_cols}", flush=True)

    Xs, eps, tss, ys, tbs = [], [], [], [], []
    cat_maps = {c: {} for c in cat_cols}
    for tb, itv, jit, t, _ in rows:
        n = t.num_rows
        num = np.column_stack([
            np.nan_to_num(t.column(c).to_numpy(zero_copy_only=False).astype(np.float64), nan=0.0,
                          posinf=0.0, neginf=0.0)
            for c in num_cols
        ])
        cat = np.zeros((n, len(cat_cols)), dtype=np.float32)
        for j, c in enumerate(cat_cols):
            vals = t.column(c).to_pylist()
            mp = cat_maps[c]
            cat[:, j] = [mp.setdefault(v, len(mp)) for v in vals]
        Xs.append(np.hstack([num, cat]).astype(np.float32))
        # 端点键：受害主机（内部 IP），仅用于分组，绝不进特征
        oh = t.column("orig_h").to_pylist()
        rh = t.column("resp_h").to_pylist()
        ep = [f"{tb}|{a if a.startswith('172.') or a.startswith('10.') else b}" for a, b in zip(oh, rh)]
        eps += ep
        tss.append(t.column("ts").to_numpy(zero_copy_only=False).astype(np.float64))
        lab = t.column("label_raw").to_pylist()
        ys.append(np.array([1 if v == "malicious_c2" else 0 for v in lab], dtype=np.int8))
        tbs += [tb] * n
    return (np.vstack(Xs), np.array(eps, dtype=object), np.concatenate(tss),
            np.concatenate(ys), np.array(tbs, dtype=object), num_cols + cat_cols)


def state_features(X, eps, ts, kind, rng):
    """为每条连接计算其端点历史的状态读出（因果：只用当前及之前的连接）。"""
    n, d = X.shape
    Wv = rng.normal(0, 1 / np.sqrt(d), (d, D_STATE)).astype(np.float32)
    Ww = rng.normal(0, 1 / np.sqrt(d), (d, D_STATE)).astype(np.float32)
    Wk = rng.normal(0, 1 / np.sqrt(d), (d, D_STATE)).astype(np.float32)
    Wkap = rng.normal(0, 1 / np.sqrt(d), (d, D_STATE)).astype(np.float32)
    Wr = rng.normal(0, 1 / np.sqrt(d), (d, D_STATE)).astype(np.float32)
    Wa = rng.normal(0, 1 / np.sqrt(d), (d, D_STATE)).astype(np.float32)

    Xn = (X - X.mean(0)) / (X.std(0) + 1e-6)
    V, G, K, KAP, R, A = Xn @ Wv, 1 / (1 + np.exp(-(Xn @ Ww))), Xn @ Wk, Xn @ Wkap, Xn @ Wr, 1 / (1 + np.exp(-(Xn @ Wa)))
    out = np.zeros((n, D_STATE * 2), dtype=np.float32)

    order = np.lexsort((ts, eps))
    cur_ep, s_vec, s_mat = None, None, None
    ema_slow = None
    for idx in order:
        e = eps[idx]
        if e != cur_ep:
            cur_ep = e
            s_vec = np.zeros(D_STATE, dtype=np.float32)
            ema_slow = np.zeros(D_STATE, dtype=np.float32)
            s_mat = np.zeros((D_STATE, D_STATE), dtype=np.float32)
        if kind == "ema":
            s_vec = 0.9 * s_vec + V[idx]
            ema_slow = 0.99 * ema_slow + V[idx]
            out[idx] = np.concatenate([s_vec, ema_slow])
        elif kind == "diag":
            s_vec = G[idx] * s_vec + V[idx]
            ema_slow = 0.99 * ema_slow + V[idx]
            out[idx] = np.concatenate([s_vec, ema_slow])
        elif kind == "delta":
            kh = KAP[idx] / (np.linalg.norm(KAP[idx]) + 1e-8)
            s_mat = s_mat * G[idx][None, :] - np.outer(s_mat @ kh, A[idx] * kh) + np.outer(V[idx], K[idx])
            rd = R[idx] @ s_mat
            ema_slow = 0.99 * ema_slow + V[idx]
            out[idx] = np.concatenate([rd, ema_slow])
    return out


def evaluate(name, F, y, tb, train_tb, test_tb):
    tr = np.isin(tb, train_tb)
    te = np.isin(tb, test_tb)
    if y[tr].sum() < 10 or y[te].sum() < 10:
        print(f"  {name:26} 正例不足，跳过", flush=True)
        return None
    t0 = time.time()
    clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1,
                                         early_stopping=True, random_state=SEED)
    clf.fit(F[tr], y[tr])
    p = clf.predict_proba(F[te])[:, 1]
    ap = average_precision_score(y[te], p)
    print(f"  {name:26} PR-AUC={ap:.4f}  err={1-ap:.4f}  dim={F.shape[1]:3}  "
          f"训练{tr.sum():6}/测试{te.sum():6}  {time.time()-t0:.0f}s", flush=True)
    return ap


def leak_audit(F, tb, train_tb, test_tb):
    """泄漏审计：用特征反预测 testbed，AUC 过高说明特征带 testbed 指纹。"""
    mask = np.isin(tb, list(train_tb) + list(test_tb))
    z = (tb[mask] == test_tb[0]).astype(np.int8)
    clf = HistGradientBoostingClassifier(max_iter=60, random_state=SEED)
    half = len(z) // 2
    idx = np.random.default_rng(SEED).permutation(len(z))
    clf.fit(F[mask][idx[:half]], z[idx[:half]])
    return roc_auc_score(z[idx[half:]], clf.predict_proba(F[mask][idx[half:]])[:, 1])


def main() -> None:
    rows = load_cells()
    tb_seen = sorted({r[0] for r in rows})
    print(f"载入 {len(rows)} 个单元格文件，testbed = {tb_seen}", flush=True)
    assert "D" in tb_seen, f"D 测试床缺失（只找到 {tb_seen}），检查 features_D/ 是否已解压"
    X, eps, ts, y, tb, names = build(rows)
    print(f"\n连接总数 {len(y):,}，恶意 {y.sum():,}（{y.mean()*100:.2f}%），"
          f"端点 {len(set(eps)):,}，testbed 分布 {dict(zip(*np.unique(tb, return_counts=True)))}\n", flush=True)

    TRAIN, TEST = ["A", "C"], ["D"]
    print(f"跨 testbed 评测：训练 {TRAIN} → 测试 {TEST}（规避已知的单元格内流级捷径）\n", flush=True)

    rng = np.random.default_rng(SEED)
    print("=" * 96, flush=True)
    print("注入增量对照（唯一变量 = 跨连接状态机制）", flush=True)
    print("=" * 96, flush=True)
    b0 = evaluate("B0 骨干only", X, y, tb, TRAIN, TEST)
    res = {}
    for kind, label in (("ema", "B1 骨干+EMA ≈RetNet"),
                        ("diag", "B2 骨干+对角衰减 ≈GLA"),
                        ("delta", "B3 骨干+delta ≈RWKV-7")):
        S = state_features(X, eps, ts, kind, np.random.default_rng(SEED))
        res[kind] = evaluate(label, np.hstack([X, S]), y, tb, TRAIN, TEST)
        if kind == "delta":
            auc = leak_audit(S, tb, TRAIN, TEST)
            print(f"  └ 泄漏审计：delta 状态特征反预测 testbed AUC={auc:.4f}"
                  f"{'  ⚠ 过高，结果存疑' if auc > 0.9 else ''}", flush=True)

    print("\n" + "=" * 96, flush=True)
    print("判定（错误相对下降口径，注入门槛 16.1%，特异性门槛 5%）", flush=True)
    print("=" * 96, flush=True)
    if b0 and all(res.values()):
        e0 = 1 - b0
        e = {k: 1 - v for k, v in res.items()}
        best = min(e.values())
        print(f"  注入有效性 : 最佳注入 {1-best:.4f} vs 骨干only {b0:.4f}"
              f"  →  错误相对下降 {(e0-best)/e0*100:+.1f}%"
              f"  [{'达标' if (e0-best)/e0*100 >= 16.1 else '未达标'}]", flush=True)
        base = min(e["ema"], e["diag"])
        print(f"  RWKV 特异性 : delta {1-e['delta']:.4f} vs 最佳非 delta {1-base:.4f}"
              f"  →  {(base-e['delta'])/base*100:+.1f}%"
              f"  [{'有信号' if (base-e['delta'])/base*100 >= 5 else '否决'}]", flush=True)


if __name__ == "__main__":
    main()
