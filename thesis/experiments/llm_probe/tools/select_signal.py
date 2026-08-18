# -*- coding: utf-8 -*-
"""第三章双机制 2x2 交互实验（对齐 Dijk 2026 §5.9 训练协议）。

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
L, BS, HID = 128, 64, 192

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




# ============ 模型选择信号诊断 ============
# 问题：同年度实体不相交验证集 AP 从 epoch 1 起即为 0.9997，早停全选 epoch 1，无选择力。
# 本实验不早停，跑满预算，在每个 epoch 同时测四个信号，最后算它们与跨年度目标的相关性，
# 直接回答「这个数据集上到底有没有能预测跨年度性能的验证信号」。
MAX_STEPS, EPOCH_STEPS = 20000, 1000
LR0, PLATEAU_FACTOR, PLATEAU_PATIENCE, MIN_LR = 2e-3, 0.1, 5, 1e-7
SEED, KAPPA, EPS = 42, 5.0, 1e-6
VAL_FRAC, TIME_TAIL = 0.10, 0.15      # 实体留出比例 / 时间尾部比例
TGT_SUB = 0.20                        # 逐 epoch 诊断用的 LSPR24 子采样比例

import os
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
os.makedirs(CACHE, exist_ok=True)


def seqs_full(s, d, ts):
    """返回序列索引、掩码、所属实体、序列起始时间。"""
    key = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s, d)], object)
    _, inv = np.unique(key, return_inverse=True)
    order = np.lexsort((ts, inv)); iv = inv[order]
    bnd = np.flatnonzero(np.r_[True, iv[1:] != iv[:-1], True])
    I, M, E, T = [], [], [], []
    for a, b in zip(bnd[:-1], bnd[1:]):
        seg = order[a:b]; eid = iv[a]
        for i in range(0, len(seg), L):
            ch = seg[i:i + L]; p = L - len(ch)
            I.append(np.r_[ch, np.zeros(p, np.int64)])
            M.append(np.r_[np.ones(len(ch), np.float32), np.zeros(p, np.float32)])
            E.append(eid); T.append(ts[ch[0]])
    return (np.asarray(I, np.int64), np.asarray(M, np.float32),
            np.asarray(E, np.int64), np.asarray(T, np.float64))


NEED = ["X23", "y23", "X24", "y24", "I23", "M23", "E23", "T23", "I24", "M24", "s24", "d24"]
if all(os.path.exists(f"{CACHE}/{n}.npy") for n in NEED):
    C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24", "d24"))) for n in NEED}
    X23, y23, X24, y24 = C["X23"], C["y23"], C["X24"], C["y24"]
    I23, M23, E23, T23 = C["I23"], C["M23"], C["E23"], C["T23"]
    I24, M24, s24, d24 = C["I24"], C["M24"], C["s24"], C["d24"]
    log(f"缓存命中：训练序列={len(I23):,} 评价序列={len(I24):,}")
else:
    log("缓存缺 T23（序列起始时间），重新解析 LSPR23 补齐")
    X23, y23, s23, d23, t23 = load("23"); log(f"LSPR23 {X23.shape}")
    X24, y24, s24, d24, t24 = load("24"); log(f"LSPR24 {X24.shape}")
    mu = X23.mean(0, keepdims=True); sd = X23.std(0, keepdims=True); sd[sd < 1e-8] = 1.0
    X23 = np.clip((X23 - mu) / sd, -10, 10); X24 = np.clip((X24 - mu) / sd, -10, 10)
    I23, M23, E23, T23 = seqs_full(s23, d23, t23); log(f"训练序列={len(I23):,}")
    I24, M24, _, _ = seqs_full(s24, d24, t24); log(f"评价序列={len(I24):,}")
    for _n, _a in [("X23", X23), ("y23", y23), ("X24", X24), ("y24", y24), ("I23", I23), ("M23", M23),
                   ("E23", E23), ("T23", T23), ("I24", I24), ("M24", M24), ("s24", s24), ("d24", d24)]:
        np.save(f"{CACHE}/{_n}.npy", _a)
    log(f"已落盘缓存 {CACHE}")

dev = "cuda" if torch.cuda.is_available() else "cpu"

# ---- 三种验证划分 ----
rs = np.random.RandomState(SEED)
uent = np.unique(E23); perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))     # 实体不相交
t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
m_time = T23 >= t_cut                                                 # 时间尾部
m_both = m_time & m_ent                                               # 时间尾部 ∩ 实体不相交
# 训练区：三者都排除，保证任何一个验证信号都不含训练样本
tr_mask = ~(m_ent | m_time)
tr_idx = np.flatnonzero(tr_mask)
V = {"实体不相交": np.flatnonzero(m_ent & ~m_time), "时间尾部": np.flatnonzero(m_time & ~m_ent),
     "时间尾部∩实体不相交": np.flatnonzero(m_both)}
log(f"LSPR23 实体 {len(uent):,}  时间切点分位 {1-TIME_TAIL:.2f}")
log(f"训练序列 {len(tr_idx):,} | " + " | ".join(f"{k} {len(v):,}" for k, v in V.items()))
for k, v in V.items():
    assert len(np.intersect1d(v, tr_idx)) == 0, f"{k} 与训练区有交叠"
log("三个验证集与训练区均无交叠（已断言）")

key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
sub24 = np.flatnonzero(np.random.RandomState(SEED).random(len(I24)) < TGT_SUB)   # 逐 epoch 诊断子集
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} | 逐epoch诊断子集 {len(sub24):,}/{len(I24):,} 序列")

gX23 = torch.from_numpy(X23).to(dev); gy23 = torch.from_numpy(y23).to(dev)
gX24 = torch.from_numpy(X24).to(dev); gy24 = torch.from_numpy(y24).to(dev)
gI23 = torch.from_numpy(I23).to(dev); gM23 = torch.from_numpy(M23).to(dev)
gI24 = torch.from_numpy(I24).to(dev); gM24 = torch.from_numpy(M24).to(dev)
gtr = torch.from_numpy(tr_idx).to(dev)
gV = {k: torch.from_numpy(v).to(dev) for k, v in V.items()}
gsub = torch.from_numpy(sub24).to(dev)
log(f"矩阵已上卡，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


class TwoWay(nn.Module):
    def __init__(self, agg, norm):
        super().__init__()
        self.agg, self.norm = agg, norm
        self.f = nn.Sequential(nn.Linear(D, HID), nn.ReLU(), nn.Dropout(0.1))
        self.g = nn.Sequential(nn.Linear(HID * 2, HID), nn.ReLU(), nn.Dropout(0.1))
        self.o = nn.Linear(HID, 1)

    def _ps(self, x, m):
        mm = m.unsqueeze(-1); n = torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)
        mu = torch.cumsum(x * mm, 1) / n
        var = (torch.cumsum((x * mm) ** 2, 1) / n - mu ** 2).clamp(min=0.0)
        lam = n / (n + KAPPA)
        return (x - lam * mu) / torch.sqrt(lam * var + (1.0 - lam) + EPS)

    def forward(self, x, m):
        if self.norm:
            x = self._ps(x, m)
        h = self.f(x) * m.unsqueeze(-1)
        c = ((torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
             if self.agg else torch.zeros_like(h))
        return self.o(self.g(torch.cat([h, c], -1)))


def pgroups(net):
    dec, nod = [], []
    for n_, p_ in net.named_parameters():
        (nod if n_.endswith(".bias") else dec).append(p_)
    return [{"params": dec, "weight_decay": 0.01}, {"params": nod, "weight_decay": 0.0}]


def ent_ap(sc, seen, n_th):
    es = np.full(N_ENT, -np.inf, np.float32)
    if n_th == 1:
        np.maximum.at(es, ent24[seen], sc[seen])
    else:
        o = np.lexsort((-sc[seen], ent24[seen])); e = ent24[seen][o]; v = sc[seen][o]
        st = np.flatnonzero(np.r_[True, e[1:] != e[:-1]]); cn = np.diff(np.r_[st, len(e)])
        es[e[st]] = v[st + np.minimum(cn, n_th) - 1]
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok])


@torch.no_grad()
def ap_on(net, gidx, gI, gM, gX, gy):
    net.eval(); P = []; Y = []
    for a in range(0, len(gidx), 2048):
        sel = gidx[a:a + 2048]; idx = gI[sel]; msk = gM[sel]; b = idx.shape[0]
        lo = net(gX[idx.reshape(-1)].reshape(b, L, D), msk).squeeze(-1)
        fm = msk.reshape(-1) > 0
        P.append(torch.sigmoid(lo).reshape(-1)[fm].cpu().numpy())
        Y.append(gy[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
    net.train()
    P = np.concatenate(P); Y = np.concatenate(Y)
    return float(average_precision_score(Y, P)) if Y.max() > 0 else float("nan")


@torch.no_grad()
def full_target(net):
    net.eval()
    sc = torch.zeros(len(y24), device=dev); sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    for a in range(0, len(I24), 2048):
        idx = gI24[a:a + 2048]; msk = gM24[a:a + 2048]; b = idx.shape[0]
        p = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk).squeeze(-1))
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = p.reshape(-1)[fm]; sn[fi[fm]] = True
    net.train()
    s_ = sn.cpu().numpy(); sc_ = sc.cpu().numpy()
    return (average_precision_score(y24[s_], sc_[s_]), roc_auc_score(y24[s_], sc_[s_]),
            ent_ap(sc_, s_, 1), ent_ap(sc_, s_, 10))


CELLS = [("C00", False, False, "A关 B关：逐流基线"), ("C01", False, True, "A关 B开：仅实体前缀标准化"),
         ("C10", True, False, "A开 B关：仅因果前缀聚合"), ("C11", True, True, "A开 B开：两机制融合")]
ytr = y23[I23[tr_idx].reshape(-1)]
pos = torch.tensor([(1 - ytr.mean()) / max(ytr.mean(), 1e-8)], device=dev)
lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=pos)
log(f"训练区正类权重 pos_weight={pos.item():.4f}")

RUNS = []
for cid, agg, norm, desc in CELLS:
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = TwoWay(agg, norm).to(dev)
    opt = torch.optim.AdamW(pgroups(net), lr=LR0)
    RUNS.append({"cid": cid, "desc": desc, "net": net, "opt": opt,
                 "sched": torch.optim.lr_scheduler.ReduceLROnPlateau(opt, "min", factor=PLATEAU_FACTOR,
                                                                     patience=PLATEAU_PATIENCE, min_lr=MIN_LR),
                 "gen": torch.Generator().manual_seed(SEED), "hist": [], "snap": {}})
N_EPOCH = MAX_STEPS // EPOCH_STEPS
log(f"4 格 seed={SEED}，{N_EPOCH} epoch × {EPOCH_STEPS} 步，**不早停**，逐 epoch 记录四个信号")

for r in RUNS:
    r["net"].train()
T0T = time.time()
for ep in range(1, N_EPOCH + 1):
    for _ in range(EPOCH_STEPS):
        for r in RUNS:
            sel = gtr[torch.randint(0, len(tr_idx), (BS,), generator=r["gen"]).to(dev)]
            idx = gI23[sel]; msk = gM23[sel]
            lo = r["net"](gX23[idx.reshape(-1)].reshape(BS, L, D), msk).squeeze(-1)
            yb = gy23[idx.reshape(-1)].reshape(BS, L)
            loss = (lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
            r["opt"].zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(r["net"].parameters(), 1.0); r["opt"].step()
    parts = []
    for r in RUNS:
        rec = {k: ap_on(r["net"], gV[k], gI23, gM23, gX23, gy23) for k in V}
        rec["跨年度(子集)"] = ap_on(r["net"], gsub, gI24, gM24, gX24, gy24)
        r["hist"].append((ep, rec))
        r["snap"][ep] = {k: v.detach().clone() for k, v in r["net"].state_dict().items()}
        r["sched"].step(1.0 - rec["实体不相交"])
        parts.append(f"{r['cid']} 实体{rec['实体不相交']:.4f} 时间{rec['时间尾部']:.4f} "
                     f"双重{rec['时间尾部∩实体不相交']:.4f} 跨年{rec['跨年度(子集)']:.4f}")
    log(f"ep {ep}/{N_EPOCH} {(time.time()-T0T)/60:.1f}分 | " + " | ".join(parts))
log(f"训练完成 {(time.time()-T0T)/60:.1f} 分钟")

SIG = list(V.keys())
print("\n" + "=" * 116, flush=True)
print("【核心诊断】各验证信号与跨年度 AP 的相关性（跨 epoch，皮尔逊 + 斯皮尔曼）", flush=True)
print("  含义：相关性接近 0 或为负 → 该信号无法用于跨年度模型选择", flush=True)
print(f"{'格':<6}{'信号':<24}{'皮尔逊 r':>12}{'斯皮尔曼 ρ':>14}{'信号动态范围':>16}{'跨年动态范围':>16}", flush=True)
from scipy.stats import spearmanr, pearsonr
for r in RUNS:
    tgt = np.array([h[1]["跨年度(子集)"] for h in r["hist"]])
    for s in SIG:
        v = np.array([h[1][s] for h in r["hist"]])
        pr = pearsonr(v, tgt)[0] if v.std() > 1e-9 else float("nan")
        sp = spearmanr(v, tgt)[0] if v.std() > 1e-9 else float("nan")
        print(f"{r['cid']:<6}{s:<24}{pr:>12.4f}{sp:>14.4f}{v.max()-v.min():>16.6f}{tgt.max()-tgt.min():>16.6f}", flush=True)

print("\n" + "=" * 116, flush=True)
print("【各信号会选出哪个 epoch，以及该 epoch 的真实跨年度表现】", flush=True)
print(f"{'格':<6}{'选择信号':<24}{'选中epoch':>10}{'该信号值':>12}{'→ 跨年度AP(全量)':>20}", flush=True)
FIN = {}
for r in RUNS:
    FIN[r["cid"]] = {}
    for s in SIG + ["最后一个epoch", "跨年度最优(事后诸葛,不可用)"]:
        if s == "最后一个epoch":
            pick = r["hist"][-1][0]; sval = float("nan")
        elif s.startswith("跨年度最优"):
            i = int(np.argmax([h[1]["跨年度(子集)"] for h in r["hist"]])); pick = r["hist"][i][0]
            sval = r["hist"][i][1]["跨年度(子集)"]
        else:
            i = int(np.argmax([h[1][s] for h in r["hist"]])); pick = r["hist"][i][0]
            sval = r["hist"][i][1][s]
        r["net"].load_state_dict(r["snap"][pick])
        f = full_target(r["net"])
        FIN[r["cid"]][s] = (pick, f)
        print(f"{r['cid']:<6}{s:<24}{pick:>10}{sval:>12.4f}{f[0]:>20.10f}", flush=True)

for label, ix, prior in [("逐流 AP", 0, 0.0257073138), ("实体 AP (n=1)", 2, float(ent_lab.mean()))]:
    for s in SIG + ["最后一个epoch"]:
        v = {c: FIN[c][s][1][ix] for c in FIN}
        eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
        c1 = (eAB - (eA + eB)) > 0; c2 = eAB > 0
        print(f"\n【{label}｜选择信号={s}】先验={prior:.6f}", flush=True)
        print(f"  C00={v['C00']:.6f}  C01={v['C01']:.6f}  C10={v['C10']:.6f}  C11={v['C11']:.6f}", flush=True)
        print(f"  A={eA:+.6f} B={eB:+.6f} 之和={eA+eB:+.6f} 组合={eAB:+.6f} 交互={eAB-(eA+eB):+.6f}", flush=True)
        print(f"  判据一 交互>0: {'通过' if c1 else '不通过'} | 判据二 组合>基线: {'通过' if c2 else '不通过'}"
              f" | ★ 组合创新{'成立' if (c1 and c2) else '不成立'}", flush=True)

print("\n" + "=" * 116, flush=True)
print("外部参照：XGBoost全量逐流=0.224442  实体聚合=0.523326(n=1)  Dijk表5 XGB=0.2416  随机=0.025707", flush=True)
print("注意：「跨年度(子集)」仅用于诊断信号相关性，不参与任何权重选择；每格的最终数字来自所列选择信号。", flush=True)
print("=" * 116, flush=True)
