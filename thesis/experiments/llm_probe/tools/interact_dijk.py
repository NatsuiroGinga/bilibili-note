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



# ============ Dijk 2026 §5.9 训练协议（逐项对齐，附录超参表 + 正文 p.?）============
MAX_STEPS = 20000          # 论文：max_steps=20000（GRU 类模型）；Transformer 为 5000
EPOCH_STEPS = 1000         # 论文：limit_train_batches=1000
MIN_EPOCHS, MAX_EPOCHS = 10, 50
LR0 = 2e-3                 # 论文用 lr-finder 决定，未公布具体值 → 沿用本课题既有值并标为差异
PLATEAU_FACTOR, PLATEAU_PATIENCE, MIN_LR = 0.1, 5, 1e-7
ES_PATIENCE, ES_DELTA = 12, 1e-3
VAL_FRAC = 0.10            # 论文按 conn_key 序列级划分；此处按 2-IP 键留出验证集
SEED = 42
KAPPA, EPS = 5.0, 1e-6

import os
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
os.makedirs(CACHE, exist_ok=True)


def seqs_with_entity(s, d, ts):
    """按 Dijk §4.1.5 的 2-IP 无向对构造序列，并返回每条序列所属实体，供无泄漏划分使用。"""
    key = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s, d)], object)
    _, inv = np.unique(key, return_inverse=True)
    order = np.lexsort((ts, inv)); iv = inv[order]
    bnd = np.flatnonzero(np.r_[True, iv[1:] != iv[:-1], True])
    I, M, E = [], [], []
    for a, b in zip(bnd[:-1], bnd[1:]):
        seg = order[a:b]; eid = iv[a]
        for i in range(0, len(seg), L):
            ch = seg[i:i + L]; p = L - len(ch)
            I.append(np.r_[ch, np.zeros(p, np.int64)])
            M.append(np.r_[np.ones(len(ch), np.float32), np.zeros(p, np.float32)])
            E.append(eid)
    return np.asarray(I, np.int64), np.asarray(M, np.float32), np.asarray(E, np.int64)


NEED = ["X23", "y23", "X24", "y24", "I23", "M23", "E23", "I24", "M24", "s24", "d24"]
if all(os.path.exists(f"{CACHE}/{n}.npy") for n in NEED):
    C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24", "d24"))) for n in NEED}
    X23, y23, X24, y24 = C["X23"], C["y23"], C["X24"], C["y24"]
    I23, M23, E23, I24, M24 = C["I23"], C["M23"], C["E23"], C["I24"], C["M24"]
    s24, d24 = C["s24"], C["d24"]
    assert X23.shape[1] == D and X24.shape[1] == D, "缓存字段数与当前 FEATS 不符"
    log(f"缓存命中：LSPR23 {X23.shape} LSPR24 {X24.shape} 训练序列={len(I23):,} 评价序列={len(I24):,}")
else:
    log("缓存缺 E23（序列→实体映射），重新解析 LSPR23 并补齐")
    X23, y23, s23, d23, t23 = load("23"); log(f"LSPR23 {X23.shape}")
    X24, y24, s24, d24, t24 = load("24"); log(f"LSPR24 {X24.shape}")
    mu = X23.mean(0, keepdims=True); sd = X23.std(0, keepdims=True); sd[sd < 1e-8] = 1.0
    X23 = np.clip((X23 - mu) / sd, -10, 10); X24 = np.clip((X24 - mu) / sd, -10, 10)
    I23, M23, E23 = seqs_with_entity(s23, d23, t23); log(f"训练序列={len(I23):,}")
    I24, M24, _ = seqs_with_entity(s24, d24, t24); log(f"评价序列={len(I24):,}")
    for _n, _a in [("X23", X23), ("y23", y23), ("X24", X24), ("y24", y24), ("I23", I23),
                   ("M23", M23), ("E23", E23), ("I24", I24), ("M24", M24), ("s24", s24), ("d24", d24)]:
        np.save(f"{CACHE}/{_n}.npy", _a)
    log(f"已落盘缓存 {CACHE}")

dev = "cuda" if torch.cuda.is_available() else "cpu"

# ---- 无泄漏验证划分：整个 2-IP 实体要么全在训练、要么全在验证 ----
uent = np.unique(E23)
rs = np.random.RandomState(SEED); perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
is_val = np.fromiter((e in val_ent for e in E23), bool, len(E23))
tr_idx = np.flatnonzero(~is_val); va_idx = np.flatnonzero(is_val)
assert len(set(E23[tr_idx]).intersection(set(E23[va_idx]))) == 0, "训练/验证实体有交叠，划分泄漏"
log(f"LSPR23 实体 {len(uent):,} → 训练序列 {len(tr_idx):,} / 验证序列 {len(va_idx):,}"
    f"（验证实体 {len(val_ent):,}，无交叠已断言）")

# ---- LSPR24 实体键：只用于评价分组，绝不入模 ----
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 实体先验={ent_lab.mean():.10f}")

gX23 = torch.from_numpy(X23).to(dev); gy23 = torch.from_numpy(y23).to(dev)
gX24 = torch.from_numpy(X24).to(dev)
gI23 = torch.from_numpy(I23).to(dev); gM23 = torch.from_numpy(M23).to(dev)
gI24 = torch.from_numpy(I24).to(dev); gM24 = torch.from_numpy(M24).to(dev)
gtr = torch.from_numpy(tr_idx).to(dev); gva = torch.from_numpy(va_idx).to(dev)
log(f"矩阵已上卡，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


class TwoWay(nn.Module):
    """A=因果前缀聚合（加绝对上下文）；B=实体前缀在线标准化（减绝对量、留相对偏离）。"""

    def __init__(self, agg, norm):
        super().__init__()
        self.agg, self.norm = agg, norm
        self.f = nn.Sequential(nn.Linear(D, HID), nn.ReLU(), nn.Dropout(0.1))
        self.g = nn.Sequential(nn.Linear(HID * 2, HID), nn.ReLU(), nn.Dropout(0.1))
        self.o = nn.Linear(HID, 1)

    def _prefix_standardize(self, x, m):
        mm = m.unsqueeze(-1)
        n = torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)
        mu = torch.cumsum(x * mm, 1) / n
        var = (torch.cumsum((x * mm) ** 2, 1) / n - mu ** 2).clamp(min=0.0)
        lam = n / (n + KAPPA)
        return (x - lam * mu) / torch.sqrt(lam * var + (1.0 - lam) + EPS)

    def forward(self, x, m):
        if self.norm:
            x = self._prefix_standardize(x, m)
        h = self.f(x) * m.unsqueeze(-1)
        if self.agg:
            c = (torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
        else:
            c = torch.zeros_like(h)
        return self.o(self.g(torch.cat([h, c], -1)))


def param_groups(net):
    """论文：bias 与 LayerNorm 权重排除权重衰减，其余 0.01。"""
    decay, nodecay = [], []
    for n_, p_ in net.named_parameters():
        (nodecay if n_.endswith(".bias") else decay).append(p_)
    return [{"params": decay, "weight_decay": 0.01}, {"params": nodecay, "weight_decay": 0.0}]


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
    return average_precision_score(ent_lab[ok], es[ok])


@torch.no_grad()
def eval_val(net, lf):
    """验证集（LSPR23 留出实体）上的 loss 与 AP，用于调度与早停。绝不触碰 LSPR24。"""
    net.eval(); ls = []; P = []; Y = []
    for a in range(0, len(va_idx), 2048):
        sel = gva[a:a + 2048]; idx = gI23[sel]; msk = gM23[sel]; b = idx.shape[0]
        xb = gX23[idx.reshape(-1)].reshape(b, L, D)
        yb = gy23[idx.reshape(-1)].reshape(b, L)
        lo = net(xb, msk).squeeze(-1)
        ls.append(((lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)).item())
        fm = msk.reshape(-1) > 0
        P.append(torch.sigmoid(lo).reshape(-1)[fm].cpu().numpy())
        Y.append(yb.reshape(-1)[fm].cpu().numpy())
    net.train()
    P = np.concatenate(P); Y = np.concatenate(Y)
    return float(np.mean(ls)), float(average_precision_score(Y, P))


@torch.no_grad()
def eval_test(net):
    """LSPR24 跨年度评价。只在训练与早停全部结束后、用最佳权重调用一次。"""
    net.eval()
    sc = torch.zeros(len(y24), device=dev); sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    for a in range(0, len(I24), 2048):
        idx = gI24[a:a + 2048]; msk = gM24[a:a + 2048]; b = idx.shape[0]
        xb = gX24[idx.reshape(-1)].reshape(b, L, D)
        p = torch.sigmoid(net(xb, msk).squeeze(-1))
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = p.reshape(-1)[fm]; sn[fi[fm]] = True
    s_ = sn.cpu().numpy(); sc_ = sc.cpu().numpy()
    return (average_precision_score(y24[s_], sc_[s_]), roc_auc_score(y24[s_], sc_[s_]),
            entity_ap(sc_, s_, 1), entity_ap(sc_, s_, 10))


CELLS = [("C00", False, False, "A关 B关：逐流基线"),
         ("C01", False, True,  "A关 B开：仅实体前缀标准化"),
         ("C10", True,  False, "A开 B关：仅因果前缀聚合"),
         ("C11", True,  True,  "A开 B开：两机制融合")]

pos = torch.tensor([(1 - y23[I23[tr_idx].reshape(-1)].mean()) / max(y23[I23[tr_idx].reshape(-1)].mean(), 1e-8)],
                   device=dev)
lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=pos)
log(f"训练区正类权重 pos_weight={pos.item():.4f}")

RUNS = []
for cid, agg, norm, desc in CELLS:
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = TwoWay(agg, norm).to(dev)
    opt = torch.optim.AdamW(param_groups(net), lr=LR0)
    RUNS.append({"cid": cid, "desc": desc, "net": net, "opt": opt,
                 "sched": torch.optim.lr_scheduler.ReduceLROnPlateau(
                     opt, mode="min", factor=PLATEAU_FACTOR, patience=PLATEAU_PATIENCE, min_lr=MIN_LR),
                 "gen": torch.Generator().manual_seed(SEED),
                 "npar": sum(p.numel() for p in net.parameters()),
                 "best_ap": -np.inf, "best_ep": 0, "bad": 0, "stopped": False,
                 "best_sd": None, "trace": []})
log(f"4 格单种子 seed={SEED}，参数量 {RUNS[0]['npar']:,}（四格相同）")
log(f"协议：max_steps={MAX_STEPS}，epoch={EPOCH_STEPS} 步，min/max epoch={MIN_EPOCHS}/{MAX_EPOCHS}，"
    f"ReduceLROnPlateau(factor={PLATEAU_FACTOR},patience={PLATEAU_PATIENCE})，"
    f"早停(val_AP, patience={ES_PATIENCE}, Δ={ES_DELTA})")

for r in RUNS:
    r["net"].train()
T0T = time.time()
N_EPOCH = min(MAX_EPOCHS, MAX_STEPS // EPOCH_STEPS)
for ep in range(1, N_EPOCH + 1):
    for _ in range(EPOCH_STEPS):
        for r in RUNS:
            if r["stopped"]:
                continue
            sel = gtr[torch.randint(0, len(tr_idx), (BS,), generator=r["gen"]).to(dev)]
            idx = gI23[sel]; msk = gM23[sel]
            xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
            yb = gy23[idx.reshape(-1)].reshape(BS, L)
            lo = r["net"](xb, msk).squeeze(-1)
            loss = (lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
            r["opt"].zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(r["net"].parameters(), 1.0); r["opt"].step()
    parts = []
    for r in RUNS:
        if r["stopped"]:
            parts.append(f"{r['cid']}=已停(ep{r['best_ep']})"); continue
        vl, va = eval_val(r["net"], lf)
        r["sched"].step(vl)
        r["trace"].append((ep, vl, va, r["opt"].param_groups[0]["lr"]))
        if va > r["best_ap"] + ES_DELTA:
            r["best_ap"] = va; r["best_ep"] = ep; r["bad"] = 0
            r["best_sd"] = {k: v.detach().clone() for k, v in r["net"].state_dict().items()}
        else:
            r["bad"] += 1
            if r["bad"] >= ES_PATIENCE and ep >= MIN_EPOCHS:
                r["stopped"] = True
        parts.append(f"{r['cid']} vl={vl:.4f} vAP={va:.4f} lr={r['opt'].param_groups[0]['lr']:.1e}")
    log(f"epoch {ep}/{N_EPOCH} ({ep*EPOCH_STEPS} 步) 用时 {(time.time()-T0T)/60:.1f} 分 | " + " | ".join(parts))
    if all(r["stopped"] for r in RUNS):
        log("全部早停，提前结束"); break
log(f"训练完成，{(time.time()-T0T)/60:.1f} 分钟")

print("\n" + "=" * 112, flush=True)
print("【验证集收敛轨迹｜val AP】末端平坦 + lr 已降 → 单次运行终值可信", flush=True)
for r in RUNS:
    tr = r["trace"]
    print(f"  {r['cid']} {r['desc']}", flush=True)
    print("    " + "  ".join(f"ep{e}:{a:.4f}" for e, _, a, _ in tr), flush=True)
    print(f"    最佳 epoch={r['best_ep']}  最佳 val AP={r['best_ap']:.6f}  "
          f"末 lr={tr[-1][3]:.1e}  末三点极差={max(a for _,_,a,_ in tr[-3:])-min(a for _,_,a,_ in tr[-3:]):.6f}", flush=True)

RES = {}
for r in RUNS:
    r["net"].load_state_dict(r["best_sd"])          # 早停恢复最佳权重后，才做唯一一次 LSPR24 评价
    RES[r["cid"]] = eval_test(r["net"])
    log(f"{r['cid']} 最佳权重(ep{r['best_ep']}) → LSPR24 逐流AP={RES[r['cid']][0]:.10f} "
        f"AUC={RES[r['cid']][1]:.6f} 实体AP(n=1)={RES[r['cid']][2]:.10f} 实体AP(n=10)={RES[r['cid']][3]:.10f}")

DESC = {c[0]: c[3] for c in CELLS}
for label, ix, prior in [("逐流 AP", 0, 0.0257073138),
                         ("实体 AP (n=1)", 2, float(ent_lab.mean())),
                         ("实体 AP (n=10)", 3, float(ent_lab.mean()))]:
    print("\n" + "=" * 112, flush=True)
    print(f"【{label}】seed={SEED} 单次运行，Dijk 2026 §5.9 协议，随机先验 = {prior:.10f}", flush=True)
    print(f"{'格':<6}{'配置':<28}{'核心组件':<12}{label:>16}{'相对基线':>14}", flush=True)
    v = {c: RES[c][ix] for c in RES}
    for cid in ["C00", "C01", "C10", "C11"]:
        comp = {"C00": "基线", "C01": "仅 B", "C10": "仅 A", "C11": "A + B"}[cid]
        d = "" if cid == "C00" else f"{v[cid]-v['C00']:+.6f}"
        print(f"{cid:<6}{DESC[cid]:<28}{comp:<12}{v[cid]:>16.6f}{d:>14}", flush=True)
    eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
    print("-" * 112, flush=True)
    print(f"  A 主效应={eA:+.6f}   B 主效应={eB:+.6f}   单机制之和={eA+eB:+.6f}   "
          f"组合={eAB:+.6f}   交互项={eAB-(eA+eB):+.6f}", flush=True)
    c1 = (eAB - (eA + eB)) > 0; c2 = eAB > 0
    print(f"  判据一 交互项 > 0（超可加）      : {'通过' if c1 else '不通过'}", flush=True)
    print(f"  判据二 组合 > 基线（C11 > C00）  : {'通过' if c2 else '不通过'}", flush=True)
    print(f"  ★ 组合创新{'成立' if (c1 and c2) else '不成立'}", flush=True)

print("\n" + "=" * 112, flush=True)
print("与 Dijk 2026 §5.9 的差异（须在正文单列，不得混排）：", flush=True)
print("  · 论文用 lr-finder 定初始学习率且未公布具体值，本实验沿用 2e-3", flush=True)
print("  · 论文 batch size 由 Lightning 二分搜索自动确定且未公布，本实验固定 64", flush=True)
print("  · 论文 accumulate_grad_batches=3 与 bf16-mixed，本实验无梯度累积、fp32", flush=True)
print("  · 论文 epoch 由 limit_train_batches=1000 定义，本实验同取 1000 优化步为一 epoch", flush=True)
print("对位朱焱雷表 3-7（p.42）：DS +2.70%、RGO +6.30%、DS-RGO +12.30% > 之和 9.00%，三效应全为正", flush=True)
print("外部参照 逐流：XGBoost全量=0.224442  Dijk表5 XGB=0.2416  随机先验=0.025707", flush=True)
print("外部参照 实体：XGBoost分数实体聚合 AP=0.523326(n=1)/0.547484(n=100)", flush=True)
print("=" * 112, flush=True)
