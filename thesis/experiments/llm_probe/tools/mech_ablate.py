# -*- coding: utf-8 -*-
"""RWKV-7 机制单因子消融（每档只对 B 改一处）：每档只加一个机制，定位增益/损害的来源。

前次错误：C 档一次性加入衰减+delta移除键+外积状态+查询读出+多头，
C=0.1257 < A=0.1590 < B=0.2879，但无法归因到具体机制。

本次阶梯（其余一切与 B 完全相同：同编码器、同输出头、同 83 字段、同 4000 步、同 seed 42）：
  B   因果前缀均值                    ctx_t = Σ_{i≤t} h_i / Σ_{i≤t} m_i
  D1  + 标量指数衰减                  s_t = w·s_{t-1} + h_t,  z_t = w·z_{t-1} + m_t,  ctx=s/z   （w 单个可学标量）
  D2  + 逐通道可学衰减                同上但 w 为逐通道向量（RWKV 的 diag(w) 形式）
  D3  + 数据依赖衰减                  w_t = sigmoid(Linear(h_t))，逐步逐通道（RWKV-6/7 的动态衰减）
  D4  + 外积状态与查询读出             S_t = w_t⊙S_{t-1} + v_t k_tᵀ,  ctx_t = S_t q_t（线性注意力，无移除键）
  D5  + delta 移除键                  S_t = w_t⊙S_{t-1} − S_{t-1}(a_t⊙k̂_t)k̂_tᵀ + v_t k̂_tᵀ（完整 RWKV-7）
"""

import time
import zipfile

import numpy as np
import pyarrow.csv as pacsv
import pyarrow.parquet as pq
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


BASE = "/root/autodl-tmp/thesis/experiments/llm_probe/data/raw"
P24 = f"{BASE}/lspr24-v1/lspr24_v2.parquet"
Z23 = f"{BASE}/lspr23-v1/ls23pr_flows.zip"
DROP = {
    "Flow ID", "SrcIP", "DstIP", "mTimestampStart", "mTimestampLast",
    "SigID revision", "Category", "Severity", "Anomaly_event",
    "Conn_state", "Service", "Segment_src", "Segment_dst",
    "Expoid_src", "Expoid_dst", "Label_src", "Label_dst", "Label",
}
L, STEPS, BS, HID = 128, 4000, 64, 192

pf = pq.ParquetFile(P24)
FEATS = [c for c in pf.schema_arrow.names if c not in DROP]
D = len(FEATS)
GRP = ["SrcIP", "DstIP", "mTimestampStart"]
log(f"特征数={D}")


def load(kind):
    if kind == "23":
        with zipfile.ZipFile(Z23) as zf:
            inner = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
            with zf.open(inner) as fh:
                t = pacsv.read_csv(fh, read_options=pacsv.ReadOptions(block_size=1 << 26),
                                   convert_options=pacsv.ConvertOptions(include_columns=FEATS + ["Label"] + GRP))
        y = np.asarray(t.column("Label").to_numpy(zero_copy_only=False)).astype(np.float32)
        X = np.empty((t.num_rows, D), np.float32)
        for j, c in enumerate(FEATS):
            X[:, j] = np.asarray(t.column(c).to_numpy(zero_copy_only=False), np.float32)
        s = np.asarray(t.column("SrcIP").to_pylist(), object)
        d = np.asarray(t.column("DstIP").to_pylist(), object)
        ts = np.asarray(t.column("mTimestampStart").to_numpy(zero_copy_only=False), np.float64)
    else:
        n = pf.metadata.num_rows
        X = np.empty((n, D), np.float32); y = np.empty(n, np.float32)
        s = np.empty(n, object); d = np.empty(n, object); ts = np.empty(n, np.float64)
        o = 0
        for rg in range(pf.metadata.num_row_groups):
            t = pf.read_row_group(rg, columns=FEATS + ["Label"] + GRP)
            k = t.num_rows
            for j, c in enumerate(FEATS):
                X[o:o + k, j] = np.asarray(t.column(c).to_numpy(zero_copy_only=False), np.float32)
            y[o:o + k] = np.asarray(t.column("Label").to_numpy(zero_copy_only=False), np.float32)
            s[o:o + k] = t.column("SrcIP").to_pylist(); d[o:o + k] = t.column("DstIP").to_pylist()
            ts[o:o + k] = np.asarray(t.column("mTimestampStart").to_numpy(zero_copy_only=False), np.float64)
            o += k
            del t
    X[~np.isfinite(X)] = 0.0
    return X, y, s, d, ts


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
import os
os.makedirs(CACHE, exist_ok=True)
X23, y23, s23, d23, t23 = load("23"); log(f"LSPR23 {X23.shape}")
X24, y24, s24, d24, t24 = load("24"); log(f"LSPR24 {X24.shape}")
mu = X23.mean(0, keepdims=True); sd = X23.std(0, keepdims=True); sd[sd < 1e-8] = 1.0
X23 = np.clip((X23 - mu) / sd, -10, 10); X24 = np.clip((X24 - mu) / sd, -10, 10)


def seqs(s, d, ts):
    key = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s, d)], object)
    _, inv = np.unique(key, return_inverse=True)
    order = np.lexsort((ts, inv)); iv = inv[order]
    bnd = np.flatnonzero(np.r_[True, iv[1:] != iv[:-1], True])
    I, M = [], []
    for a, b in zip(bnd[:-1], bnd[1:]):
        seg = order[a:b]
        for i in range(0, len(seg), L):
            ch = seg[i:i + L]; p = L - len(ch)
            I.append(np.r_[ch, np.zeros(p, np.int64)])
            M.append(np.r_[np.ones(len(ch), np.float32), np.zeros(p, np.float32)])
    return np.asarray(I, np.int64), np.asarray(M, np.float32)


I23, M23 = seqs(s23, d23, t23); log(f"训练序列={len(I23):,}")
I24, M24 = seqs(s24, d24, t24); log(f"评价序列={len(I24):,}")
dev = "cuda" if torch.cuda.is_available() else "cpu"



class Ablate(nn.Module):
    """单因子消融：所有档共用同一编码器 f、同一输出头 g/o，只有 ctx() 里改一处。

    B   ctx = Σh / Σm                       因果前缀均值（基线）
    S1  ctx = s/z, s=w·s+h, z=w·z+m         只加「数据依赖衰减」
    S2  ctx = Σh                            只去「归一化」（不除以计数）
    S3  ctx = (S q)/z, S = Σ v k̂ᵀ           只换「外积状态+查询读出」，归一化保留
    S4  S3 再加 delta 移除键                 只加「移除键」
    S5  ctx = (Σh/Σm) ⊙ σ(Q h)              只加「内容相关门控读出」，状态仍是向量
    """

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.f = nn.Sequential(nn.Linear(D, HID), nn.ReLU(), nn.Dropout(0.1))
        self.g = nn.Sequential(nn.Linear(HID * 2, HID), nn.ReLU(), nn.Dropout(0.1))
        self.o = nn.Linear(HID, 1)
        if mode == "S1":
            self.wg = nn.Linear(HID, HID)
        if mode in ("S3", "S4"):
            self.nh = 4; self.dh = HID // self.nh
            self.k = nn.Linear(HID, HID); self.v = nn.Linear(HID, HID); self.q = nn.Linear(HID, HID)
        if mode == "S4":
            self.a = nn.Linear(HID, HID)
        if mode == "S5":
            self.q = nn.Linear(HID, HID)

    def ctx(self, h, m):
        B_, T, _ = h.shape
        cnt = torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)

        if self.mode == "B":
            return torch.cumsum(h, 1) / cnt
        if self.mode == "S2":
            return torch.cumsum(h, 1)                      # 唯一改动：不除
        if self.mode == "S5":
            return (torch.cumsum(h, 1) / cnt) * torch.sigmoid(self.q(h))
        if self.mode == "S1":
            w = torch.sigmoid(self.wg(h))
            s = torch.zeros(B_, HID, device=h.device, dtype=h.dtype)
            z = torch.zeros(B_, HID, device=h.device, dtype=h.dtype)
            out = []
            for t in range(T):
                wt = w[:, t]
                s = wt * s + h[:, t]
                z = wt * z + m[:, t].unsqueeze(-1)
                out.append(s / z.clamp(min=1e-6))
            return torch.stack(out, 1)

        # S3 / S4：外积状态，无衰减（w=1），**保留归一化**
        k = torch.nn.functional.normalize(self.k(h).view(B_, T, self.nh, self.dh), dim=-1)
        v = self.v(h).view(B_, T, self.nh, self.dh)
        q = self.q(h).view(B_, T, self.nh, self.dh)
        a = torch.sigmoid(self.a(h)).view(B_, T, self.nh, self.dh) if self.mode == "S4" else None
        S = torch.zeros(B_, self.nh, self.dh, self.dh, device=h.device, dtype=h.dtype)
        out = []
        for t in range(T):
            if self.mode == "S4":
                rem = (a[:, t] * k[:, t]).unsqueeze(-2) * k[:, t].unsqueeze(-1)
                S = S - torch.einsum("bhij,bhjk->bhik", S, rem)
            S = S + v[:, t].unsqueeze(-1) * k[:, t].unsqueeze(-2)
            out.append(torch.einsum("bhij,bhj->bhi", S, q[:, t]).reshape(B_, HID))
        return torch.stack(out, 1) / cnt                   # 与 B 同口径归一化

    def forward(self, x, m):
        h = self.f(x) * m.unsqueeze(-1)
        c = self.ctx(h, m) * m.unsqueeze(-1)
        return self.o(self.g(torch.cat([h, c], -1)))



# ============ 全部常驻显存 + 18 次训练交错执行 ============
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
os.makedirs(CACHE, exist_ok=True)
for nm, arr in [("X23", X23), ("X24", X24), ("y23", y23), ("y24", y24),
                ("I23", I23), ("M23", M23), ("I24", I24), ("M24", M24)]:
    p = f"{CACHE}/{nm}.npy"
    if not os.path.exists(p):
        np.save(p, arr)
log(f"标准化数组已缓存到 {CACHE}（后续运行可跳过 CSV 解析）")

gX23 = torch.from_numpy(X23).to(dev)          # 5.4 GB 常驻显存
gy23 = torch.from_numpy(y23).to(dev)
gX24 = torch.from_numpy(X24).to(dev)          # 6.7 GB 常驻显存
log(f"训练/评价矩阵已上卡，显存占用 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

MODES = ["B", "S1", "S2", "S3", "S4", "S5"]
SEEDS = [42, 43, 44]
NAME = {
    "B":  "因果前缀均值（基线）",
    "S1": "只加-数据依赖衰减",
    "S2": "只去-归一化",
    "S3": "只换-外积状态与查询读出",
    "S4": "只换-外积并加delta移除键",
    "S5": "只加-内容相关门控读出",
}

pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=pos)

RUNS = []
for m in MODES:
    for sd_ in SEEDS:
        torch.manual_seed(sd_); np.random.seed(sd_)      # 与串行版逐字一致的初始化
        net = Ablate(m).to(dev)
        RUNS.append({
            "mode": m, "seed": sd_, "net": net,
            "opt": torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=0.01),
            "gen": torch.Generator().manual_seed(sd_),    # 与串行版一致的批次采样
            "npar": sum(p.numel() for p in net.parameters()),
        })
log(f"已构建 {len(RUNS)} 个模型（{len(MODES)} 档 × {len(SEEDS)} 种子），显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

gI23 = torch.from_numpy(I23).to(dev)
gM23 = torch.from_numpy(M23).to(dev)
for r in RUNS:
    r["net"].train()

T_TRAIN = time.time()
for st in range(STEPS):
    for r in RUNS:
        sel = torch.randint(0, len(I23), (BS,), generator=r["gen"]).to(dev)
        idx = gI23[sel]; msk = gM23[sel]
        xb = gX23[idx.reshape(-1)].reshape(BS, L, D)     # gather 在卡上做，无 H2D
        yb = gy23[idx.reshape(-1)].reshape(BS, L)
        lo = r["net"](xb, msk).squeeze(-1)
        loss = (lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
        r["opt"].zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(r["net"].parameters(), 1.0); r["opt"].step()
    if st % 250 == 0 or st == STEPS - 1:
        torch.cuda.synchronize()
        el = time.time() - T_TRAIN
        eta = el / max(st + 1, 1) * (STEPS - st - 1)
        log(f"步 {st+1}/{STEPS}  已用 {el/60:.1f} 分  预计剩余 {eta/60:.1f} 分  "
            f"显存 {torch.cuda.memory_allocated()/2**30:.1f}/{torch.cuda.max_memory_allocated()/2**30:.1f} GiB")
log(f"18 次训练全部完成，共 {(time.time()-T_TRAIN)/60:.1f} 分钟")

gI24 = torch.from_numpy(I24).to(dev)
gM24 = torch.from_numpy(M24).to(dev)
R = {m: [] for m in MODES}; P = {}
for r in RUNS:
    r["net"].eval()
    sc = torch.zeros(len(y24), device=dev); seen = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    with torch.no_grad():
        for a in range(0, len(I24), 1024):
            idx = gI24[a:a + 1024]; msk = gM24[a:a + 1024]; b = idx.shape[0]
            xb = gX24[idx.reshape(-1)].reshape(b, L, D)
            p = torch.sigmoid(r["net"](xb, msk).squeeze(-1))
            fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
            sc[fi[fm]] = p.reshape(-1)[fm]; seen[fi[fm]] = True
    s_ = seen.cpu().numpy(); sc_ = sc.cpu().numpy()
    ap = average_precision_score(y24[s_], sc_[s_]); auc = roc_auc_score(y24[s_], sc_[s_])
    log(f"{r['mode']} seed={r['seed']}: AP={ap:.10f} AUC={auc:.6f} 参数={r['npar']:,} 覆盖={s_.mean():.4f}")
    R[r["mode"]].append(ap); P[r["mode"]] = r["npar"]

print("\n" + "=" * 100, flush=True)
print(f"{'档':<4}{'相对B的唯一改动':<28}{'seed42':>10}{'seed43':>10}{'seed44':>10}{'均值':>10}{'标准差':>9}{'参数':>10}", flush=True)
mean = {}
for m in MODES:
    a = np.array(R[m]); mean[m] = a.mean()
    print(f"{m:<4}{NAME[m]:<28}{a[0]:>10.6f}{a[1]:>10.6f}{a[2]:>10.6f}{a.mean():>10.6f}{a.std(ddof=1):>9.6f}{P[m]:>10,}", flush=True)
print("-" * 100, flush=True)
print("单因子效应（各档均值 − B 均值），判据：|差| 是否超过两档合并标准差", flush=True)
sdB = np.array(R["B"]).std(ddof=1)
for m in MODES[1:]:
    d = mean[m] - mean["B"]
    pooled = np.sqrt((np.array(R[m]).std(ddof=1) ** 2 + sdB ** 2) / 2)
    print(f"  {m:<4}{NAME[m]:<28}Δ={d:+.6f}  合并σ={pooled:.6f}  {'超噪声' if abs(d) > pooled else '噪声内'}", flush=True)
print("-" * 100, flush=True)
print("累加式阶梯（单种子）：B=0.184848 D1=0.249087 D2=0.221080 D3=0.222485 D4=0.067493 D5=0.217323", flush=True)
print("预注册判据：若「状态必须有界」成立 → S2 应崩到 0.07 附近，S3 应保持 0.20+", flush=True)
print("外部参照：XGBoost全量=0.224442  Dijk表5 XGB=0.2416  逐流MLP=0.159013  随机先验=0.025707", flush=True)
print("=" * 100, flush=True)
