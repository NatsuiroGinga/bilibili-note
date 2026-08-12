"""E3：状态核机制存在性合成实验（免训练，纯结构对比）。

问题：RWKV-7 的广义 delta 规则（移除键主动擦除）相对纯衰减（被动遗忘），
在「良性多路复用干扰下积累带抖动周期信标」这一任务上是否存在优势？

设计：合成端点事件序列 = 泊松良性事件 + 周期 T 带抖动 σ 的信标事件。
用固定随机投影实现四种递归状态核（全部免训练，公平比较结构而非学习）：
  (a) 无状态       —— 只看当前事件
  (b) 多时间常数 EMA —— 固定标量衰减，≈ RetNet
  (c) 输入条件对角衰减 —— ≈ GLA / Mamba-1
  (d) 完整 delta 规则  —— S_t = S_{t-1}(diag(w) - κ̂ᵀ(a⊙κ̂)) + vᵀk，≈ RWKV-7

各核把序列压成状态特征，喂同一个 HistGradientBoostingClassifier 判「该端点是否含信标」。

门槛：(d) 相对 (b)/(c) 错误相对下降 >= 5% → RWKV-7 特异性有初步信号；
      (d) <= (b) → 特异性否决，机制故事在最有利的合成条件下即不成立。

本实验不使用任何真实数据，结论仅为机制存在性，不得写入论文。
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

SEED = 42
D_IN = 16          # 事件特征维
D_STATE = 32       # 状态维
N_ENDPOINTS = 4000
SEQ_LEN = 256      # 每端点事件数


@dataclass(frozen=True)
class Scenario:
    """合成场景：信标周期、抖动、良性干扰强度。"""
    period: int
    jitter: float
    benign_rate: float


def synth_endpoint(rng, has_beacon: bool, sc: Scenario):
    """生成一个端点的事件序列：良性泊松事件 + 可选带抖动周期信标。"""
    t = 0.0
    events = []
    # 良性事件：泊松到达，特征来自宽分布
    n_benign = rng.poisson(sc.benign_rate * SEQ_LEN)
    benign_t = np.sort(rng.uniform(0, SEQ_LEN, size=n_benign))
    for bt in benign_t:
        events.append((bt, rng.normal(0, 1, D_IN), 0))
    if has_beacon:
        # 信标：周期 period，抖动比例 jitter，特征集中在一个固定方向附近
        direction = rng.normal(0, 1, D_IN)
        direction /= np.linalg.norm(direction)
        t = rng.uniform(0, sc.period)
        while t < SEQ_LEN:
            f = direction * rng.normal(2.0, 0.3) + rng.normal(0, 0.4, D_IN)
            events.append((t, f, 1))
            step = sc.period * (1.0 + rng.uniform(-sc.jitter, sc.jitter))
            t += max(step, 1e-3)
    if not events:
        events = [(0.0, rng.normal(0, 1, D_IN), 0)]
    events.sort(key=lambda z: z[0])
    ts = np.array([e[0] for e in events], dtype=np.float32)
    feats = np.stack([e[1] for e in events]).astype(np.float32)
    return ts, feats


def kernel_none(ts, x, P):
    """(a) 无状态：只用事件特征的简单汇总。"""
    return np.concatenate([x.mean(0), x.std(0), x.max(0), [len(x)]])


def kernel_ema(ts, x, P):
    """(b) 多时间常数 EMA：固定标量衰减，≈ RetNet。"""
    h = x @ P["W_v"]
    outs = []
    for w in (0.5, 0.9, 0.99):
        s = np.zeros(D_STATE, dtype=np.float32)
        acc = []
        for i in range(len(h)):
            s = w * s + h[i]
            acc.append(s)
        acc = np.stack(acc)
        outs.append(np.concatenate([acc[-1], acc.std(0)]))
    return np.concatenate(outs)


def kernel_diag(ts, x, P):
    """(c) 输入条件对角衰减：≈ GLA / Mamba-1。"""
    h = x @ P["W_v"]
    g = 1.0 / (1.0 + np.exp(-(x @ P["W_w"])))   # 每步每通道衰减率
    s = np.zeros(D_STATE, dtype=np.float32)
    acc = []
    for i in range(len(h)):
        s = g[i] * s + h[i]
        acc.append(s.copy())
    acc = np.stack(acc)
    return np.concatenate([acc[-1], acc.std(0), acc.max(0)])


def kernel_delta(ts, x, P):
    """(d) 完整 delta 规则：S_t = S_{t-1}(diag(w) - κ̂ᵀ(a⊙κ̂)) + vᵀk，≈ RWKV-7。

    用矩阵状态 S ∈ R^{D_STATE×D_STATE}，读出取 r·S。
    """
    v = x @ P["W_v"]
    k = x @ P["W_k"]
    kap = x @ P["W_kappa"]
    r = x @ P["W_r"]
    w = 1.0 / (1.0 + np.exp(-(x @ P["W_w"])))
    a = 1.0 / (1.0 + np.exp(-(x @ P["W_a"])))
    S = np.zeros((D_STATE, D_STATE), dtype=np.float32)
    acc = []
    for i in range(len(v)):
        kh = kap[i] / (np.linalg.norm(kap[i]) + 1e-8)
        # S <- S (diag(w) - kh^T (a*kh)) + v^T k
        S = S * w[i][None, :] - np.outer(S @ kh, a[i] * kh) + np.outer(v[i], k[i])
        acc.append(r[i] @ S)
    acc = np.stack(acc)
    return np.concatenate([acc[-1], acc.std(0), acc.max(0)])


KERNELS = {
    "(a) 无状态": kernel_none,
    "(b) EMA 固定衰减 ≈RetNet": kernel_ema,
    "(c) 对角数据依赖衰减 ≈GLA": kernel_diag,
    "(d) delta 规则 ≈RWKV-7": kernel_delta,
}


def run(sc: Scenario) -> dict:
    rng = np.random.default_rng(SEED)
    P = {
        "W_v": rng.normal(0, 1 / np.sqrt(D_IN), (D_IN, D_STATE)).astype(np.float32),
        "W_k": rng.normal(0, 1 / np.sqrt(D_IN), (D_IN, D_STATE)).astype(np.float32),
        "W_kappa": rng.normal(0, 1 / np.sqrt(D_IN), (D_IN, D_STATE)).astype(np.float32),
        "W_r": rng.normal(0, 1 / np.sqrt(D_IN), (D_IN, D_STATE)).astype(np.float32),
        "W_w": rng.normal(0, 1 / np.sqrt(D_IN), (D_IN, D_STATE)).astype(np.float32),
        "W_a": rng.normal(0, 1 / np.sqrt(D_IN), (D_IN, D_STATE)).astype(np.float32),
    }
    y = (rng.random(N_ENDPOINTS) < 0.3).astype(np.int8)
    seqs = [synth_endpoint(rng, bool(y[i]), sc) for i in range(N_ENDPOINTS)]

    res = {}
    for name, fn in KERNELS.items():
        t0 = time.time()
        X = np.stack([fn(ts, f, P) for ts, f in seqs]).astype(np.float32)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        xtr, xva, ytr, yva = train_test_split(X, y, test_size=0.3, random_state=SEED, stratify=y)
        clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1,
                                             early_stopping=True, random_state=SEED)
        clf.fit(xtr, ytr)
        ap = average_precision_score(yva, clf.predict_proba(xva)[:, 1])
        res[name] = ap
        print(f"    {name:28} PR-AUC={ap:.4f}  err={1-ap:.4f}  dim={X.shape[1]:3}  {time.time()-t0:.0f}s",
              flush=True)
    return res


def main() -> None:
    print(f"E3 状态核机制存在性合成实验 | 端点 {N_ENDPOINTS}，序列长 {SEQ_LEN}，状态维 {D_STATE}\n", flush=True)
    scenarios = [
        ("低干扰 短周期", Scenario(period=16, jitter=0.0, benign_rate=0.2)),
        ("低干扰 长周期强抖动", Scenario(period=64, jitter=0.7, benign_rate=0.2)),
        ("高干扰 长周期强抖动", Scenario(period=64, jitter=0.7, benign_rate=2.0)),
        ("极高干扰 长周期强抖动", Scenario(period=64, jitter=0.7, benign_rate=6.0)),
    ]
    summary = {}
    for label, sc in scenarios:
        print(f"  场景「{label}」 period={sc.period} jitter={sc.jitter} benign_rate={sc.benign_rate}", flush=True)
        summary[label] = run(sc)
        print(flush=True)

    print("=" * 88, flush=True)
    print("门槛判定：(d) 相对 (b)/(c) 错误相对下降 >= 5% 视为 RWKV-7 特异性有初步信号", flush=True)
    print("=" * 88, flush=True)
    for label, r in summary.items():
        e = {k: 1 - v for k, v in r.items()}
        d = e["(d) delta 规则 ≈RWKV-7"]
        vs_b = (e["(b) EMA 固定衰减 ≈RetNet"] - d) / max(e["(b) EMA 固定衰减 ≈RetNet"], 1e-9) * 100
        vs_c = (e["(c) 对角数据依赖衰减 ≈GLA"] - d) / max(e["(c) 对角数据依赖衰减 ≈GLA"], 1e-9) * 100
        vs_a = (e["(a) 无状态"] - d) / max(e["(a) 无状态"], 1e-9) * 100
        flag = "有信号" if (vs_b >= 5 and vs_c >= 5) else ("否决" if vs_b <= 0 else "弱")
        print(f"  {label:22} delta vs EMA {vs_b:+6.1f}%  vs 对角 {vs_c:+6.1f}%  vs 无状态 {vs_a:+6.1f}%   [{flag}]",
              flush=True)


if __name__ == "__main__":
    main()
