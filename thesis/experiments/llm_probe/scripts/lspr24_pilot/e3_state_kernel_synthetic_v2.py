"""E3-v2：状态核机制存在性合成实验（修正版，免训练结构对比）。

=== v1 的设计缺陷（已否决 v1 结论）===
v1 让信标事件特征 ~ direction*N(2.0,0.3)、良性 ~ N(0,1)，两者**边缘分布就可分**，
`max`/`std` 直接暴露信标存在，无状态基线因此以 PR-AUC 0.9957 碾压所有状态核。
该结果否决的是任务设计，不是机制。

=== v2 的修正 ===
1. 正负端点的事件**边缘特征分布完全相同**：都是 N(0,I) 加上一个沿"端点专属随机方向"的
   小幅一致分量（eps=0.35）。
2. **负端点也有方向一致的干扰事件**，数量与正端点信标数匹配，只是**到达时刻是泊松而非周期**。
   这样"方向一致性"不再是判据，唯一判据是**到达时序的规律性**。
3. 输入显式含 Δt（对数），使时序信息对所有核都可得——公平。
4. 每个核在若干随机种子与尺度上取最优，抵消免训练随机投影的运气差异。
5. 全部核输出维度对齐到同一预算。

四种递归状态核：
  (a) 无状态       —— 边缘统计量，应当接近随机
  (b) 多时间常数 EMA —— 固定标量衰减，≈ RetNet
  (c) 输入条件对角衰减 —— ≈ GLA / Mamba-1
  (d) 完整 delta 规则  —— ≈ RWKV-7，含移除键主动擦除

门槛：(d) 相对 (b)/(c) 错误相对下降 >= 5% → RWKV-7 特异性有初步信号；
      (d) <= (b) → 特异性否决。
另需 (b)/(c)/(d) 至少一个显著优于 (a)，否则说明任务本身不需要状态，实验无效。

本实验不使用任何真实数据，结论仅为机制存在性，不得写入论文。
"""

from __future__ import annotations

import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

SEED = 42
D_IN = 8
D_STATE = 16
N_ENDPOINTS = 3000
T_MAX = 200.0        # 观测时长（秒的抽象单位）
EPS_DIR = 0.35       # 一致方向分量幅度（正负端点相同）
SCALES = (0.3, 1.0, 3.0)   # 每个核的尺度搜索
KERNEL_SEEDS = (0, 1, 2)


def gen_endpoint(rng, positive: bool, period: float, jitter: float, benign_rate: float):
    """生成一个端点的事件序列。

    正负端点的差异**只在**「方向一致事件的到达时序」：
      positive → 周期 period、抖动 jitter 的更新过程
      negative → 同等数量的泊松到达
    边缘特征分布两者完全一致。
    """
    direction = rng.normal(0, 1, D_IN)
    direction /= np.linalg.norm(direction)

    # 背景事件：泊松，各向同性
    n_bg = rng.poisson(benign_rate * T_MAX)
    t_bg = np.sort(rng.uniform(0, T_MAX, size=max(n_bg, 1)))
    x_bg = rng.normal(0, 1, (len(t_bg), D_IN))

    # 一致方向事件：正端点周期到达，负端点泊松到达，数量匹配
    if positive:
        t_sig, t = [], rng.uniform(0, period)
        while t < T_MAX:
            t_sig.append(t)
            t += max(period * (1.0 + rng.uniform(-jitter, jitter)), 1e-3)
        t_sig = np.array(t_sig)
    else:
        n_sig = max(int(T_MAX / period), 1)
        t_sig = np.sort(rng.uniform(0, T_MAX, size=n_sig))
    if len(t_sig) == 0:
        t_sig = np.array([rng.uniform(0, T_MAX)])
    x_sig = rng.normal(0, 1, (len(t_sig), D_IN)) + EPS_DIR * direction

    ts = np.concatenate([t_bg, t_sig])
    xs = np.vstack([x_bg, x_sig])
    order = np.argsort(ts)
    ts, xs = ts[order], xs[order]
    dt = np.diff(ts, prepend=ts[0])
    # 输入 = 特征 + log Δt（时序信息对所有核可得）
    feats = np.hstack([xs, np.log1p(dt)[:, None]]).astype(np.float32)
    return feats


def pad_batch(seqs):
    """把变长序列右侧补零成 (B, T, D)，并返回有效长度掩码。"""
    n = len(seqs)
    tmax = max(len(s) for s in seqs)
    d = seqs[0].shape[1]
    X = np.zeros((n, tmax, d), dtype=np.float32)
    M = np.zeros((n, tmax), dtype=np.float32)
    for i, s in enumerate(seqs):
        X[i, : len(s)] = s
        M[i, : len(s)] = 1.0
    return X, M


def k_none(X, M, P, scale):
    """(a) 无状态：边缘统计量。"""
    cnt = M.sum(1, keepdims=True)
    mean = (X * M[..., None]).sum(1) / np.maximum(cnt, 1)
    var = ((X - mean[:, None, :]) ** 2 * M[..., None]).sum(1) / np.maximum(cnt, 1)
    mx = np.where(M[..., None] > 0, X, -np.inf).max(1)
    mx[~np.isfinite(mx)] = 0.0
    return np.hstack([mean, np.sqrt(var), mx, cnt])


def k_ema(X, M, P, scale):
    """(b) 多时间常数 EMA：固定标量衰减，≈ RetNet。"""
    V = X @ P["Wv"] * scale
    outs = []
    for w in (0.5, 0.9, 0.99):
        s = np.zeros((X.shape[0], D_STATE), dtype=np.float32)
        acc_last = np.zeros_like(s)
        acc_sq = np.zeros_like(s)
        for t in range(X.shape[1]):
            m = M[:, t : t + 1]
            s = w * s + V[:, t] * m
            acc_last = np.where(m > 0, s, acc_last)
            acc_sq += s * s * m
        outs += [acc_last, np.sqrt(acc_sq / np.maximum(M.sum(1, keepdims=True), 1))]
    return np.hstack(outs)


def k_diag(X, M, P, scale):
    """(c) 输入条件对角衰减：≈ GLA / Mamba-1。"""
    V = X @ P["Wv"] * scale
    G = 1.0 / (1.0 + np.exp(-(X @ P["Ww"])))
    s = np.zeros((X.shape[0], D_STATE), dtype=np.float32)
    acc_last = np.zeros_like(s)
    acc_sq = np.zeros_like(s)
    acc_max = np.full_like(s, -np.inf)
    for t in range(X.shape[1]):
        m = M[:, t : t + 1]
        s = G[:, t] * s + V[:, t] * m
        acc_last = np.where(m > 0, s, acc_last)
        acc_sq += s * s * m
        acc_max = np.where(m > 0, np.maximum(acc_max, s), acc_max)
    acc_max[~np.isfinite(acc_max)] = 0.0
    return np.hstack([acc_last, np.sqrt(acc_sq / np.maximum(M.sum(1, keepdims=True), 1)), acc_max])


def k_delta(X, M, P, scale):
    """(d) 完整 delta 规则：S_t = S_{t-1}(diag(w) - κ̂ᵀ(a⊙κ̂)) + vᵀk，≈ RWKV-7。"""
    B, T, _ = X.shape
    V = X @ P["Wv"] * scale
    K = X @ P["Wk"]
    KAP = X @ P["Wkappa"]
    R = X @ P["Wr"]
    W = 1.0 / (1.0 + np.exp(-(X @ P["Ww"])))
    A = 1.0 / (1.0 + np.exp(-(X @ P["Wa"])))
    S = np.zeros((B, D_STATE, D_STATE), dtype=np.float32)
    acc_last = np.zeros((B, D_STATE), dtype=np.float32)
    acc_sq = np.zeros((B, D_STATE), dtype=np.float32)
    for t in range(T):
        m = M[:, t][:, None]
        kh = KAP[:, t] / (np.linalg.norm(KAP[:, t], axis=1, keepdims=True) + 1e-8)
        Skh = np.einsum("bij,bj->bi", S, kh)                       # S·κ̂
        S = S * W[:, t][:, None, :] - np.einsum("bi,bj->bij", Skh, A[:, t] * kh)
        S = S + np.einsum("bi,bj->bij", V[:, t] * m, K[:, t])
        out = np.einsum("bi,bij->bj", R[:, t], S)
        acc_last = np.where(m > 0, out, acc_last)
        acc_sq += out * out * m
    return np.hstack([acc_last, np.sqrt(acc_sq / np.maximum(M.sum(1, keepdims=True), 1))])


KERNELS = {
    "(a) 无状态": k_none,
    "(b) EMA 固定衰减 ≈RetNet": k_ema,
    "(c) 对角数据依赖衰减 ≈GLA": k_diag,
    "(d) delta 规则 ≈RWKV-7": k_delta,
}


def make_proj(rng):
    d = D_IN + 1
    f = lambda o: rng.normal(0, 1 / np.sqrt(d), (d, D_STATE)).astype(np.float32)
    return {n: f(n) for n in ("Wv", "Wk", "Wkappa", "Wr", "Ww", "Wa")}


def score(F, y):
    F = np.nan_to_num(F, nan=0.0, posinf=0.0, neginf=0.0)
    xtr, xva, ytr, yva = train_test_split(F, y, test_size=0.3, random_state=SEED, stratify=y)
    clf = HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1,
                                         early_stopping=True, random_state=SEED)
    clf.fit(xtr, ytr)
    return average_precision_score(yva, clf.predict_proba(xva)[:, 1])


def run(period, jitter, benign_rate):
    rng = np.random.default_rng(SEED)
    y = (rng.random(N_ENDPOINTS) < 0.3).astype(np.int8)
    seqs = [gen_endpoint(rng, bool(y[i]), period, jitter, benign_rate) for i in range(N_ENDPOINTS)]
    X, M = pad_batch(seqs)
    res = {}
    for name, fn in KERNELS.items():
        t0 = time.time()
        best = 0.0
        # 每个核在种子×尺度上取最优，抵消免训练随机投影的运气差异
        combos = [(0, 1.0)] if name.startswith("(a)") else [(s, sc) for s in KERNEL_SEEDS for sc in SCALES]
        for sd, sc in combos:
            P = make_proj(np.random.default_rng(1000 + sd))
            best = max(best, score(fn(X, M, P, sc), y))
        res[name] = best
        print(f"    {name:28} PR-AUC={best:.4f}  err={1-best:.4f}  ({len(combos)} 组合, {time.time()-t0:.0f}s)",
              flush=True)
    return res


def main() -> None:
    print(f"E3-v2 状态核机制存在性（修正版）| 端点 {N_ENDPOINTS}，观测 {T_MAX}，状态维 {D_STATE}")
    print("正负端点边缘特征分布完全相同，唯一差异是一致方向事件的到达时序规律性\n", flush=True)
    scenarios = [
        ("短周期 无抖动 低干扰", 10.0, 0.0, 0.15),
        ("短周期 强抖动 低干扰", 10.0, 0.7, 0.15),
        ("长周期 无抖动 高干扰", 40.0, 0.0, 1.0),
        ("长周期 强抖动 高干扰", 40.0, 0.7, 1.0),
    ]
    summary = {}
    for label, p, j, b in scenarios:
        print(f"  场景「{label}」period={p} jitter={j} benign_rate={b}", flush=True)
        summary[label] = run(p, j, b)
        print(flush=True)

    print("=" * 92, flush=True)
    print("判定：先看状态核是否显著优于无状态（否则任务无效）；再看 (d) 相对 (b)/(c)", flush=True)
    print("=" * 92, flush=True)
    for label, r in summary.items():
        e = {k: 1 - v for k, v in r.items()}
        a, b, c, d = (e["(a) 无状态"], e["(b) EMA 固定衰减 ≈RetNet"],
                      e["(c) 对角数据依赖衰减 ≈GLA"], e["(d) delta 规则 ≈RWKV-7"])
        best_state = min(b, c, d)
        valid = (a - best_state) / max(a, 1e-9) * 100
        vs_b = (b - d) / max(b, 1e-9) * 100
        vs_c = (c - d) / max(c, 1e-9) * 100
        tag = "任务无效(状态无用)" if valid < 5 else ("有信号" if (vs_b >= 5 and vs_c >= 5) else
                                                  ("否决" if vs_b <= 0 else "弱"))
        print(f"  {label:20} 状态vs无状态 {valid:+6.1f}% | delta vs EMA {vs_b:+6.1f}% "
              f"vs 对角 {vs_c:+6.1f}%   [{tag}]", flush=True)


if __name__ == "__main__":
    main()
