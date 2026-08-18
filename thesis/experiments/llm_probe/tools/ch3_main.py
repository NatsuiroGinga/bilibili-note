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





# ============ 第三章双机制主实验（一次性，跑完即定稿）============
# 机制一 A｜表示层·因果前缀跨流聚合   ctx_t = Σ_{i≤t}h_i / Σ_{i≤t}m_i
#   谱系 Lee&Stolfo 2000 TISSEC Table VIII p.243 / Vision-RWKV ICLR2025 式(5) Table5 71.1→75.1
#   改造 定长窗→无界因果前缀；手工计数→可微表示；单主机→2-IP 无向边
# 机制二 B｜决策层·实体级可学 Lp 池化  S_e = (Σ s_f^p / n)^{1/p}，p 可学
#   谱系 Gehri 2023 CyCon 主机级聚合 / Gulcehre 2014 ECML（mean/RMS/max 均为 Lp 特例）
#   改造 固定聚合算子→算子本身可学；训练期以实体级辅助损失驱动 p
#
# 协议：固定 20000 步，**不早停、不做基于验证集的 epoch 选择**。
#   依据：本课题实测三种同年度验证划分在 20 epoch 上动态范围仅 2.8e-5~1.2e-2，
#   而跨年度 AP 变化 0.09~0.39，相关性 -0.40~+0.42 无一致方向（见 select_signal.log）。
#   故改为固定预算 + 末 5 个检查点预测平均，彻底移除模型选择环节。
MAX_STEPS, EPOCH_STEPS, AVG_LAST = 20000, 1000, 5
LR0, SEED, KAPPA, EPS = 2e-3, 42, 5.0, 1e-6
AUX_W = 1.0                                  # 实体级辅助损失权重，先验固定为 1.0

import os
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
NEED = ["X23", "y23", "X24", "y24", "I23", "M23", "E23", "T23", "I24", "M24", "s24", "d24"]
assert all(os.path.exists(f"{CACHE}/{n}.npy") for n in NEED), "缓存不全，先跑一次 select_signal.py"
C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24", "d24"))) for n in NEED}
X23, y23, X24, y24 = C["X23"], C["y23"], C["X24"], C["y24"]
I23, M23, I24, M24, s24, d24 = C["I23"], C["M23"], C["I24"], C["M24"], C["s24"], C["d24"]
log(f"缓存命中：训练序列={len(I23):,} 评价序列={len(I24):,}")
dev = "cuda" if torch.cuda.is_available() else "cpu"

key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 实体先验={ent_lab.mean():.10f}")

gX23 = torch.from_numpy(X23).to(dev); gy23 = torch.from_numpy(y23).to(dev)
gX24 = torch.from_numpy(X24).to(dev)
gI23 = torch.from_numpy(I23).to(dev); gM23 = torch.from_numpy(M23).to(dev)
gI24 = torch.from_numpy(I24).to(dev); gM24 = torch.from_numpy(M24).to(dev)
log(f"矩阵已上卡，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


def lp_pool(s, m, p):
    """(Σ s^p / n)^{1/p}，用 log 域实现避免 p 大时溢出。s∈(0,1)，m 为掩码。"""
    ls = torch.log(s.clamp(min=1e-7))
    n = m.sum(1).clamp(min=1.0)
    z = (p * ls).masked_fill(m < 0.5, -1e30)
    return torch.exp((torch.logsumexp(z, dim=1) - torch.log(n)) / p)


class Model(nn.Module):
    def __init__(self, agg, lp):
        super().__init__()
        self.agg, self.lp = agg, lp
        self.f = nn.Sequential(nn.Linear(D, HID), nn.ReLU(), nn.Dropout(0.1))
        self.g = nn.Sequential(nn.Linear(HID * 2, HID), nn.ReLU(), nn.Dropout(0.1))
        self.o = nn.Linear(HID, 1)
        self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))   # p = exp(p_log) ∈ (0,∞)，初值 2.0

    @property
    def p(self):
        # 幂平均 M_p 对任意实 p 有定义：p→0 几何平均、p=1 算术平均、p=2 RMS、p→∞ 上界。
        # 原 softplus(·)+1 的 p≥1 下界来自「Lp 须为合法范数」，但此处是池化概率而非算范数，
        # 该约束无依据且已实测把 p 顶死在边界，故移除。
        return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def forward(self, x, m):
        h = self.f(x) * m.unsqueeze(-1)
        c = ((torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
             if self.agg else torch.zeros_like(h))
        return self.o(self.g(torch.cat([h, c], -1))).squeeze(-1)


def pgroups(net):
    dec, nod = [], []
    for n_, p_ in net.named_parameters():
        (nod if (n_.endswith(".bias") or n_ == "p_log") else dec).append(p_)
    return [{"params": dec, "weight_decay": 0.01}, {"params": nod, "weight_decay": 0.0}]


def entity_ap_from(sc, seen, mode, p=None):
    """mode='max' 传统上界聚合（p→∞ 特例）；mode='lp' 学到的 Lp 池化。"""
    if mode == "max":
        es = np.full(N_ENT, -np.inf, np.float32)
        np.maximum.at(es, ent24[seen], sc[seen])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[seen], np.clip(sc[seen], 1e-7, 1.0).astype(np.float64) ** p)
        np.add.at(cnt, ent24[seen], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok])


CELLS = [("C00", False, False, "A关 B关：逐流基线 + 传统上界聚合"),
         ("C01", False, True,  "A关 B开：仅实体级可学Lp池化"),
         ("C10", True,  False, "A开 B关：仅因果前缀聚合"),
         ("C11", True,  True,  "A开 B开：两机制融合")]
pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=pos)
_seqlab = (y23[I23.reshape(-1)].reshape(I23.shape) * M23).max(1) > 0
_spw = float((1 - _seqlab.mean()) / max(_seqlab.mean(), 1e-8))
log(f"序列级正类先验={_seqlab.mean():.10f}  辅助损失 pos_weight={_spw:.4f}"
    f"（逐流 pos_weight={pos.item():.4f}）")
_bce_seq = nn.BCELoss(reduction="none")


def lf_seq(pred, tgt):
    """带 pos_weight 的序列级 BCE。此前遗漏该权重，19.87:1 的负样本把 p 单调压到下界。"""
    w = 1.0 + (_spw - 1.0) * tgt
    return (_bce_seq(pred, tgt) * w).sum() / w.sum()

RUNS = []
for cid, agg, lp, desc in CELLS:
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = Model(agg, lp).to(dev)
    RUNS.append({"cid": cid, "desc": desc, "net": net, "lp": lp,
                 "opt": torch.optim.AdamW(pgroups(net), lr=LR0),
                 "gen": torch.Generator().manual_seed(SEED), "snap": []})
N_EPOCH = MAX_STEPS // EPOCH_STEPS
log(f"4 格 seed={SEED}，参数量 {sum(p.numel() for p in RUNS[0]['net'].parameters()):,}")
log(f"协议：固定 {MAX_STEPS} 步（{N_EPOCH} epoch），不早停、不选 epoch，末 {AVG_LAST} 个检查点预测平均")

for r in RUNS:
    r["net"].train()
T0T = time.time()
for ep in range(1, N_EPOCH + 1):
    for _ in range(EPOCH_STEPS):
        for r in RUNS:
            sel = torch.randint(0, len(I23), (BS,), generator=r["gen"]).to(dev)
            idx = gI23[sel]; msk = gM23[sel]
            xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
            yb = gy23[idx.reshape(-1)].reshape(BS, L)
            lo = r["net"](xb, msk)
            lflow = (lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
            laux = torch.zeros((), device=dev)
            if r["lp"]:                                   # 机制二：实体级辅助损失，驱动 p 可学
                sq = lp_pool(torch.sigmoid(lo), msk, r["net"].p).clamp(1e-6, 1 - 1e-6)
                ysq = (yb * msk).amax(1)
                laux = lf_seq(sq, ysq)
            loss = lflow + AUX_W * laux
            r["opt"].zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(r["net"].parameters(), 1.0); r["opt"].step()
            r["l_flow"] = float(lflow); r["l_aux"] = float(laux)
    if ep > N_EPOCH - AVG_LAST:
        for r in RUNS:
            r["snap"].append({k: v.detach().clone() for k, v in r["net"].state_dict().items()})
    log(f"ep {ep}/{N_EPOCH} 用时 {(time.time()-T0T)/60:.1f} 分 | " + " | ".join(
        f"{r['cid']} p={r['net'].p.item():.4f} 流损={r.get('l_flow',0):.4f} 辅损={r.get('l_aux',0):.4f}"
        for r in RUNS if r["lp"]))
log(f"训练完成 {(time.time()-T0T)/60:.1f} 分钟")


@torch.no_grad()
def predict(net):
    net.eval()
    sc = torch.zeros(len(y24), device=dev); sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    for a in range(0, len(I24), 2048):
        idx = gI24[a:a + 2048]; msk = gM24[a:a + 2048]; b = idx.shape[0]
        pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk))
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
    net.train()
    return sc.cpu().numpy(), sn.cpu().numpy()


RES = {}
for r in RUNS:
    acc = None; seen = None; ps = []
    for sd_ in r["snap"]:                                 # 末 AVG_LAST 个检查点的预测平均
        r["net"].load_state_dict(sd_)
        sc, sn = predict(r["net"])
        ps.append(r["net"].p.item())
        acc = sc if acc is None else acc + sc
        seen = sn if seen is None else (seen | sn)
    sc = acc / len(r["snap"])
    p_avg = float(np.mean(ps))
    fap = average_precision_score(y24[seen], sc[seen])
    fauc = roc_auc_score(y24[seen], sc[seen])
    e_max = entity_ap_from(sc, seen, "max")
    e_lp = entity_ap_from(sc, seen, "lp", p_avg) if r["lp"] else e_max
    RES[r["cid"]] = (fap, fauc, e_max, e_lp, p_avg)
    log(f"{r['cid']} 检查点平均({len(r['snap'])}个) → 逐流AP={fap:.10f} AUC={fauc:.6f} "
        f"实体AP(上界)={e_max:.10f} 实体AP(Lp)={e_lp:.10f} p={p_avg:.4f}")

print("\n" + "=" * 114, flush=True)
print("表 3-x  第三章双机制 2×2 消融（LSPR23→LSPR24 零样本，seed=42 单次，固定 20000 步 + 末5检查点平均）", flush=True)
DESC = {c[0]: c[3] for c in CELLS}
for label, ix, prior in [("跨年度逐流 AP", 0, 0.0257073138), ("跨年度实体级 AP", 3, float(ent_lab.mean()))]:
    print("\n" + "-" * 114, flush=True)
    print(f"【{label}】随机先验 = {prior:.10f}", flush=True)
    print(f"{'格':<6}{'配置':<34}{'核心组件':<12}{label:>18}{'相对基线':>14}", flush=True)
    v = {c: RES[c][ix] for c in RES}
    for cid in ["C00", "C01", "C10", "C11"]:
        comp = {"C00": "基线", "C01": "仅 B", "C10": "仅 A", "C11": "A + B"}[cid]
        d = "" if cid == "C00" else f"{v[cid]-v['C00']:+.6f}"
        print(f"{cid:<6}{DESC[cid]:<34}{comp:<12}{v[cid]:>18.6f}{d:>14}", flush=True)
    eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
    print(f"  A 主效应={eA:+.6f}   B 主效应={eB:+.6f}   单机制之和={eA+eB:+.6f}   "
          f"组合={eAB:+.6f}   交互项={eAB-(eA+eB):+.6f}", flush=True)
    c1 = (eAB - (eA + eB)) > 0; c2 = eAB > 0
    print(f"  判据一 交互项>0（超可加）: {'通过' if c1 else '不通过'}   "
          f"判据二 组合>基线: {'通过' if c2 else '不通过'}   ★ 组合创新{'成立' if (c1 and c2) else '不成立'}", flush=True)

print("\n" + "-" * 114, flush=True)
print("学到的 Lp 池化指数：" + "  ".join(f"{c}: p={RES[c][4]:.4f}" for c in RES if RES[c][4] != RUNS[0]["net"].p.item() or True), flush=True)
print("  参考：p=1 即均值池化，p→∞ 即上界（max）池化，均为 Gulcehre 2014 Lp 单元的特例", flush=True)
print("\n外部参照（同一冻结数据与字段预算）：", flush=True)
print(f"  XGBoost 全量逐流 AP = 0.224442     XGBoost 分数实体聚合 AP = 0.523326(n=1)", flush=True)
print(f"  Dijk 2026 表5 XGBoost = 0.2416     Dijk 表5 GRU+SesH = 0.1758     Transformer+2-H = 0.0742", flush=True)
print(f"  逐流 MLP = 0.159013                随机先验 = 0.025707", flush=True)
print("\n协议声明（须写入 §3.6 实验设置）：", flush=True)
print("  本章不使用基于验证集的早停或 epoch 选择。依据：三种同年度验证划分（实体不相交/时间尾部/双重）", flush=True)
print("  在 20 个 epoch 上的动态范围仅 2.8e-5~1.2e-2，而跨年度 AP 变化 0.09~0.39，", flush=True)
print("  皮尔逊相关 -0.40~+0.42 且无一致方向，故同年度验证集不具备跨年度模型选择能力。", flush=True)
print("=" * 114, flush=True)
