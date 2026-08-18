# -*- coding: utf-8 -*-
"""第三章双机制 2x2 交互实验（预注册）。

组合创新的判据不是「两个机制各自有增益」，而是「组合增益 > 单机制增益之和」。
对位朱焱雷第三章表 3-7（p.42）：ET-BERT 上 DS+RGO 提升 12.30% > 单模块之和 9.00%。

两个因子必须结构正交，否则交互项恒为零：
  因子 A「因果前缀聚合」（计算侧）：把同一 2-IP 前缀上 h 的均值作为上下文拼进来。
      模型看到的是「这条边上此前的流平均长什么样」——提供绝对上下文。
  因子 B「实体前缀在线标准化」（控制侧）：用同一 2-IP 前缀上 x 的均值/方差把输入标准化。
      模型看到的是「这条流相对该边常态偏离多少」——去掉绝对量，只留相对偏离。

  两者都在同一实体键上算前缀统计量，但用途相反：A 加上下文，B 减掉上下文。
  跨年度漂移下绝对特征值会整体平移，相对偏离可能稳定——这是 B 的可证伪预测。

四格（× 种子 42/43/44 = 12 次训练）：
  C00  A off B off   逐流 MLP + 全局标准化           （对位既有 0.1590128242）
  C01  A off B on    逐流 MLP + 实体前缀在线标准化
  C10  A on  B off   序列因果前缀均值 + 全局标准化    （对位既有 0.1848~0.2879）
  C11  A on  B on    两者同时

容量控制：A off 时 ctx 位置填零向量，参数量与 A on 完全相同，只是不携带信息。
评价：四格同时报逐流 AP 与实体级 AP（n=1 / n=10），交互判据在两个口径上分别检验。
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



import os

CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
os.makedirs(CACHE, exist_ok=True)
NEED = ["X23", "y23", "X24", "y24", "I23", "M23", "I24", "M24", "s24", "d24"]
HIT = all(os.path.exists(f"{CACHE}/{n}.npy") for n in NEED)

if HIT:
    # 缓存命中：跳过 CSV 解析与序列构造（省约 4 分钟）
    C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24", "d24"))) for n in NEED}
    X23, y23, X24, y24 = C["X23"], C["y23"], C["X24"], C["y24"]
    I23, M23, I24, M24 = C["I23"], C["M23"], C["I24"], C["M24"]
    s24, d24 = C["s24"], C["d24"]
    assert X23.shape[1] == D and X24.shape[1] == D, f"缓存字段数与当前 FEATS 不符：{X23.shape[1]}/{X24.shape[1]} vs {D}"
    assert len(y23) == len(X23) and len(y24) == len(X24), "缓存行数不一致"
    log(f"缓存命中 {CACHE}：LSPR23 {X23.shape} LSPR24 {X24.shape} "
        f"训练序列={len(I23):,} 评价序列={len(I24):,}")
else:
    X23, y23, s23, d23, t23 = load("23"); log(f"LSPR23 {X23.shape}")
    X24, y24, s24, d24, t24 = load("24"); log(f"LSPR24 {X24.shape}")
    mu = X23.mean(0, keepdims=True); sd = X23.std(0, keepdims=True); sd[sd < 1e-8] = 1.0
    X23 = np.clip((X23 - mu) / sd, -10, 10); X24 = np.clip((X24 - mu) / sd, -10, 10)


    I23, M23 = seqs(s23, d23, t23); log(f"训练序列={len(I23):,}")
    I24, M24 = seqs(s24, d24, t24); log(f"评价序列={len(I24):,}")
    for _n, _a in [("X23", X23), ("y23", y23), ("X24", X24), ("y24", y24),
                   ("I23", I23), ("M23", M23), ("I24", I24), ("M24", M24),
                   ("s24", s24), ("d24", d24)]:
        np.save(f"{CACHE}/{_n}.npy", _a)
    log(f"标准化数组与序列索引已落盘到 {CACHE}")

dev = "cuda" if torch.cuda.is_available() else "cpu"




# ============ 缓存读取（修复上一版只写不读的缺陷）============
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
KAPPA = 5.0          # 实体前缀统计量向全局收缩的强度，n 小时靠全局
EPS = 1e-6

# ============ LSPR24 实体键（只用于分组与评价，绝不入模）============
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32)
np.maximum.at(ent_lab, ent24, y24)
log(f"LSPR24 实体数={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 实体先验={ent_lab.mean():.10f}")

gX23 = torch.from_numpy(X23).to(dev); gy23 = torch.from_numpy(y23).to(dev)
gX24 = torch.from_numpy(X24).to(dev)
gI23 = torch.from_numpy(I23).to(dev); gM23 = torch.from_numpy(M23).to(dev)
gI24 = torch.from_numpy(I24).to(dev); gM24 = torch.from_numpy(M24).to(dev)
log(f"矩阵已上卡，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


class TwoWay(nn.Module):
    """同一骨架，两个布尔因子。除因子外一切相同。"""

    def __init__(self, agg: bool, norm: bool):
        super().__init__()
        self.agg, self.norm = agg, norm
        self.f = nn.Sequential(nn.Linear(D, HID), nn.ReLU(), nn.Dropout(0.1))
        self.g = nn.Sequential(nn.Linear(HID * 2, HID), nn.ReLU(), nn.Dropout(0.1))
        self.o = nn.Linear(HID, 1)          # 四格参数量完全相同

    def _prefix_standardize(self, x, m):
        """因子 B：按同一 2-IP 前缀的在线均值/方差标准化输入。

        x 已经过 LSPR23 全局标准化（全局均值 0、方差 1），故收缩目标为 (0, 1)。
        n 小时 lam→0，退化为全局标准化，与 B off 连续衔接，不会在 t=1 处爆炸。
        """
        mm = m.unsqueeze(-1)
        n = torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)
        mu = torch.cumsum(x * mm, 1) / n
        ex2 = torch.cumsum((x * mm) ** 2, 1) / n
        var = (ex2 - mu ** 2).clamp(min=0.0)
        lam = n / (n + KAPPA)
        mu_s = lam * mu                                  # 全局均值 0
        var_s = lam * var + (1.0 - lam) * 1.0            # 全局方差 1
        return (x - mu_s) / torch.sqrt(var_s + EPS)

    def forward(self, x, m):
        if self.norm:
            x = self._prefix_standardize(x, m)
        h = self.f(x) * m.unsqueeze(-1)
        if self.agg:
            c = torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)
            c = c * m.unsqueeze(-1)
        else:
            c = torch.zeros_like(h)                      # 容量相同，不携带信息
        return self.o(self.g(torch.cat([h, c], -1)))


CELLS = [("C00", False, False, "A关 B关：逐流+全局标准化"),
         ("C01", False, True,  "A关 B开：逐流+实体前缀标准化"),
         ("C10", True,  False, "A开 B关：因果前缀聚合+全局标准化"),
         ("C11", True,  True,  "A开 B开：两者同时")]
SEEDS = [42, 43, 44]

pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=pos)

RUNS = []
for cid, agg, norm, desc in CELLS:
    for sd_ in SEEDS:
        torch.manual_seed(sd_); np.random.seed(sd_)
        net = TwoWay(agg, norm).to(dev)
        RUNS.append({"cid": cid, "desc": desc, "seed": sd_, "net": net,
                     "opt": torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=0.01),
                     "gen": torch.Generator().manual_seed(sd_),
                     "npar": sum(p.numel() for p in net.parameters())})
log(f"已构建 {len(RUNS)} 个模型（4 格 × 3 种子），参数量 {RUNS[0]['npar']:,}（四格相同）")

for r in RUNS:
    r["net"].train()
T0T = time.time()
for st in range(STEPS):
    for r in RUNS:
        sel = torch.randint(0, len(I23), (BS,), generator=r["gen"]).to(dev)
        idx = gI23[sel]; msk = gM23[sel]
        xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
        yb = gy23[idx.reshape(-1)].reshape(BS, L)
        lo = r["net"](xb, msk).squeeze(-1)
        loss = (lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
        r["opt"].zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(r["net"].parameters(), 1.0); r["opt"].step()
    if st % 250 == 0 or st == STEPS - 1:
        torch.cuda.synchronize(); el = time.time() - T0T
        log(f"步 {st+1}/{STEPS}  已用 {el/60:.1f} 分  剩余 {el/max(st+1,1)*(STEPS-st-1)/60:.1f} 分")
log(f"12 次训练完成，{(time.time()-T0T)/60:.1f} 分钟")


def entity_ap(sc, seen, n_th):
    """实体级 AP：每个实体取其第 n_th 大的流分数作为实体分数。"""
    es = np.full(N_ENT, -np.inf, np.float32)
    if n_th == 1:
        np.maximum.at(es, ent24[seen], sc[seen])
    else:
        order = np.lexsort((-sc[seen], ent24[seen]))
        e = ent24[seen][order]; v = sc[seen][order]
        start = np.flatnonzero(np.r_[True, e[1:] != e[:-1]])
        cnt = np.diff(np.r_[start, len(e)])
        take = start + np.minimum(cnt, n_th) - 1
        es[e[start]] = v[take]
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok]), ok.sum()


R = {c[0]: {"flow": [], "e1": [], "e10": []} for c in CELLS}
for r in RUNS:
    r["net"].eval()
    sc = torch.zeros(len(y24), device=dev); sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    with torch.no_grad():
        for a in range(0, len(I24), 1024):
            idx = gI24[a:a + 1024]; msk = gM24[a:a + 1024]; b = idx.shape[0]
            xb = gX24[idx.reshape(-1)].reshape(b, L, D)
            p = torch.sigmoid(r["net"](xb, msk).squeeze(-1))
            fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
            sc[fi[fm]] = p.reshape(-1)[fm]; sn[fi[fm]] = True
    s_ = sn.cpu().numpy(); sc_ = sc.cpu().numpy()
    fap = average_precision_score(y24[s_], sc_[s_])
    e1, nent = entity_ap(sc_, s_, 1)
    e10, _ = entity_ap(sc_, s_, 10)
    log(f"{r['cid']} seed={r['seed']}: 逐流AP={fap:.10f} 实体AP(n=1)={e1:.10f} 实体AP(n=10)={e10:.10f} 覆盖实体={nent:,}")
    R[r["cid"]]["flow"].append(fap); R[r["cid"]]["e1"].append(e1); R[r["cid"]]["e10"].append(e10)

DESC = {c[0]: c[3] for c in CELLS}
for metric, label, prior in [("flow", "逐流 AP", 0.0257073138),
                             ("e1", "实体 AP (n=1)", float(ent_lab.mean())),
                             ("e10", "实体 AP (n=10)", float(ent_lab.mean()))]:
    print("\n" + "=" * 104, flush=True)
    print(f"【{label}】随机先验 = {prior:.10f}", flush=True)
    print(f"{'格':<5}{'配置':<34}{'seed42':>11}{'seed43':>11}{'seed44':>11}{'均值':>11}{'标准差':>10}", flush=True)
    mu = {}; sd = {}
    for cid in ["C00", "C01", "C10", "C11"]:
        a = np.array(R[cid][metric]); mu[cid] = a.mean(); sd[cid] = a.std(ddof=1)
        print(f"{cid:<5}{DESC[cid]:<34}{a[0]:>11.6f}{a[1]:>11.6f}{a[2]:>11.6f}{a.mean():>11.6f}{a.std(ddof=1):>10.6f}", flush=True)
    eA = mu["C10"] - mu["C00"]       # 只开 A 的主效应
    eB = mu["C01"] - mu["C00"]       # 只开 B 的主效应
    eAB = mu["C11"] - mu["C00"]      # 组合总效应
    inter = eAB - (eA + eB)          # 交互项
    pooled = np.sqrt(sum(sd[c] ** 2 for c in mu) / 4)
    print("-" * 104, flush=True)
    print(f"  A 主效应（C10−C00）        = {eA:+.6f}", flush=True)
    print(f"  B 主效应（C01−C00）        = {eB:+.6f}", flush=True)
    print(f"  单机制之和                 = {eA + eB:+.6f}", flush=True)
    print(f"  组合总效应（C11−C00）      = {eAB:+.6f}", flush=True)
    print(f"  ★ 交互项                   = {inter:+.6f}   四格合并σ = {pooled:.6f}", flush=True)
    if inter > pooled:
        print(f"  → 超可加，组合成立（对位朱表 3-7：12.30% > 9.00%）", flush=True)
    elif inter < -pooled:
        print(f"  → 次可加，两机制冗余，组合不成立", flush=True)
    else:
        print(f"  → 落在噪声内，本实验不足以判定组合是否成立", flush=True)
print("\n" + "=" * 104, flush=True)
print("预注册：交互项为零或为负时照实记录，不改判据凑超可加。", flush=True)
print("外部参照 逐流：XGBoost全量=0.224442  Dijk表5 XGB=0.2416  逐流MLP=0.159013", flush=True)
print("外部参照 实体：XGBoost分数实体聚合 AP=0.523326(n=1) / 0.547484(n=100)  DR@4%FPR=0.7207~0.8324", flush=True)
print("=" * 104, flush=True)
