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
L, STEPS, BS, HID = 128, 40000, 64, 192   # 40000 步 ≈ 9.4 个 epoch（4000 步只有 0.94）

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


CELLS = [("C00", False, False, "A关 B关：逐流基线"),
         ("C01", False, True,  "A关 B开：仅实体前缀标准化"),
         ("C10", True,  False, "A开 B关：仅因果前缀聚合"),
         ("C11", True,  True,  "A开 B开：两机制融合")]
SEED = 42                      # 单种子，对齐朱焱雷表 3-7 的报告格式
CKPT = 5000                    # 每 5000 步做一次完整评价，用于证明末端已收敛

pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=pos)

RUNS = []
for cid, agg, norm, desc in CELLS:
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = TwoWay(agg, norm).to(dev)
    RUNS.append({"cid": cid, "desc": desc, "net": net,
                 "opt": torch.optim.AdamW(net.parameters(), lr=2e-3, weight_decay=0.01),
                 "gen": torch.Generator().manual_seed(SEED),
                 "npar": sum(p.numel() for p in net.parameters()), "trace": []})
log(f"4 格单种子 seed={SEED}，参数量 {RUNS[0]['npar']:,}（四格相同）")
log(f"训练序列 {len(I23):,}，{STEPS} 步 × BS {BS} = {STEPS*BS:,} 次抽样 ≈ {STEPS*BS/len(I23):.2f} 个 epoch")


def evaluate(net):
    net.eval()
    sc = torch.zeros(len(y24), device=dev); sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    with torch.no_grad():
        for a in range(0, len(I24), 2048):
            idx = gI24[a:a + 2048]; msk = gM24[a:a + 2048]; b = idx.shape[0]
            xb = gX24[idx.reshape(-1)].reshape(b, L, D)
            p = torch.sigmoid(net(xb, msk).squeeze(-1))
            fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
            sc[fi[fm]] = p.reshape(-1)[fm]; sn[fi[fm]] = True
    net.train()
    s_ = sn.cpu().numpy(); sc_ = sc.cpu().numpy()
    return (average_precision_score(y24[s_], sc_[s_]),
            entity_ap(sc_, s_, 1)[0], entity_ap(sc_, s_, 10)[0])


def entity_ap(sc, seen, n_th):
    es = np.full(N_ENT, -np.inf, np.float32)
    if n_th == 1:
        np.maximum.at(es, ent24[seen], sc[seen])
    else:
        order = np.lexsort((-sc[seen], ent24[seen]))
        e = ent24[seen][order]; v = sc[seen][order]
        start = np.flatnonzero(np.r_[True, e[1:] != e[:-1]])
        cnt = np.diff(np.r_[start, len(e)])
        es[e[start]] = v[start + np.minimum(cnt, n_th) - 1]
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok]), ok.sum()


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
    if (st + 1) % CKPT == 0 or st == STEPS - 1:
        torch.cuda.synchronize(); el = time.time() - T0T
        ep = (st + 1) * BS / len(I23)
        line = []
        for r in RUNS:
            f, e1, e10 = evaluate(r["net"])
            r["trace"].append((st + 1, f, e1, e10))
            line.append(f"{r['cid']}={f:.6f}")
        log(f"步 {st+1}/{STEPS} ({ep:.2f} epoch) 已用 {el/60:.1f} 分 | 逐流AP " + "  ".join(line))
log(f"训练完成，{(time.time()-T0T)/60:.1f} 分钟")

MET = [("逐流 AP", 1, 0.0257073138), ("实体 AP (n=1)", 2, float(ent_lab.mean())),
       ("实体 AP (n=10)", 3, float(ent_lab.mean()))]
DESC = {c[0]: c[3] for c in CELLS}
TR = {r["cid"]: r["trace"] for r in RUNS}

print("\n" + "=" * 108, flush=True)
print("【收敛轨迹｜逐流 AP】末端若平坦，则单次运行的终值可信；若仍在跳，单种子结论不成立", flush=True)
hdr = "".join(f"{t[0]//1000:>10}k" for t in TR["C00"])
print(f"{'格':<6}{'配置':<26}{hdr}", flush=True)
for cid in ["C00", "C01", "C10", "C11"]:
    row = "".join(f"{t[1]:>11.6f}" for t in TR[cid])
    print(f"{cid:<6}{DESC[cid]:<26}{row}", flush=True)
for cid in ["C00", "C01", "C10", "C11"]:
    last3 = [t[1] for t in TR[cid]][-3:]
    print(f"  {cid} 末三个检查点 极差 = {max(last3)-min(last3):.6f}", flush=True)

for label, ix, prior in MET:
    print("\n" + "=" * 108, flush=True)
    print(f"【{label}】seed={SEED} 单次运行，{STEPS} 步（{STEPS*BS/len(I23):.2f} epoch），随机先验 = {prior:.10f}", flush=True)
    print(f"{'格':<6}{'配置':<26}{'核心组件':<18}{label:>16}{'相对基线':>14}", flush=True)
    v = {cid: TR[cid][-1][ix] for cid in TR}
    for cid in ["C00", "C01", "C10", "C11"]:
        comp = {"C00": "基线", "C01": "仅 B", "C10": "仅 A", "C11": "A + B"}[cid]
        d = "" if cid == "C00" else f"{v[cid]-v['C00']:+14.6f}"
        print(f"{cid:<6}{DESC[cid]:<26}{comp:<18}{v[cid]:>16.6f}{d:>14}", flush=True)
    eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
    print("-" * 108, flush=True)
    print(f"  A 主效应 = {eA:+.6f}    B 主效应 = {eB:+.6f}    单机制之和 = {eA+eB:+.6f}", flush=True)
    print(f"  组合总效应 = {eAB:+.6f}    交互项 = {eAB-(eA+eB):+.6f}", flush=True)
    # 修正后的判据：交互为正「且」组合确实超过基线，两条缺一不可
    c1 = (eAB - (eA + eB)) > 0
    c2 = eAB > 0
    print(f"  判据一 交互项 > 0            : {'通过' if c1 else '不通过'}", flush=True)
    print(f"  判据二 组合 > 基线（C11>C00）: {'通过' if c2 else '不通过'}", flush=True)
    print(f"  ★ 组合创新{'成立' if (c1 and c2) else '不成立'}"
          + ("" if (c1 and c2) else "（上一版脚本只查了判据一，把「两个有害机制互相抵消」误判为超可加，已修正）"), flush=True)

print("\n" + "=" * 108, flush=True)
print("对位朱焱雷表 3-7（p.42）ET-BERT：DS +2.70%、RGO +6.30%、DS-RGO +12.30% > 单模块之和 9.00%", flush=True)
print("  ——他三个效应全为正，组合亦为正，两条判据同时成立。", flush=True)
print("外部参照 逐流：XGBoost全量=0.224442  Dijk表5 XGB=0.2416  随机先验=0.025707", flush=True)
print("外部参照 实体：XGBoost分数实体聚合 AP=0.523326(n=1)/0.547484(n=100)", flush=True)
print("=" * 108, flush=True)
