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







# ============ 第四章证伪实验：先验漂移是否真的破坏停止边界 ============
# 候选：跨年度漂移下的实体级约束早停告警
#   第三层机制增量 = 用无标签目标前缀做 BBSE 先验估计，重标定源年度学到的停止边界
# 本实验只回答一个问题：这个漂移问题真的存在吗？
#   证伪判据一：源年度冻结阈值在目标年实测实体 FPR ∈ [0.03,0.05] 且 DR 与 oracle 差 ≤ 0.02
#              → 阈值本来就迁得过去，不存在需要校正的漂移，机制增量不成立
#   证伪判据二：BBSE 先验估计相对误差 > 50% → 工具链输入端就断了，机制不可实现
import os, json, time as _t
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch4-drift"
os.makedirs(OUT, exist_ok=True)
SEED, KAPPA, EPS, AUX_W = 42, 5.0, 1e-6, 1.0
STEPS, EPOCH_STEPS, AVG_LAST = 20000, 1000, 5
TARGET_FPR = 0.04
PREFIX_FRAC = 0.10        # 目标年最早 10% 作「无标签前缀」，只用其特征，不看标签

NEED = ["X23","y23","X24","y24","I23","M23","I24","M24","s24","d24","t24"]
C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24","d24"))) for n in NEED}
X23,y23,X24,y24 = C["X23"],C["y23"],C["X24"],C["y24"]
I23,M23,I24,M24,s24,d24,t24 = C["I23"],C["M23"],C["I24"],C["M24"],C["s24"],C["d24"],C["t24"]
log(f"缓存命中：训练序列={len(I23):,} 评价序列={len(I24):,}")
dev = "cuda" if torch.cuda.is_available() else "cpu"

# ---- 实体键：源年度与目标年度各建一套，只作分组 ----
def ents(s, d):
    k = np.array([a+"|"+b if a<=b else b+"|"+a for a,b in zip(s,d)], object)
    _, inv = np.unique(k, return_inverse=True)
    return inv, inv.max()+1

# 源年度实体需要 s23/d23，缓存里没有 → 用 I23 的分块结构恢复：同一实体的序列在构造时连续
# 更稳妥：直接按序列分组做「源年度实体」，一个序列即一个决策单元（保守，且与训练单元一致）
ent24, N24 = ents(s24, d24)
lab24 = np.zeros(N24, np.float32); np.maximum.at(lab24, ent24, y24)
log(f"目标年实体={N24:,} 正例实体={int(lab24.sum()):,} 实体先验={lab24.mean():.10f}")
log(f"逐流先验：源={y23.mean():.10f}  目标={y24.mean():.10f}  比值={y23.mean()/y24.mean():.4f}")

gX23=torch.from_numpy(X23).to(dev); gy23=torch.from_numpy(y23).to(dev)
gX24=torch.from_numpy(X24).to(dev)
gI23=torch.from_numpy(I23).to(dev); gM23=torch.from_numpy(M23).to(dev)
gI24=torch.from_numpy(I24).to(dev); gM24=torch.from_numpy(M24).to(dev)
log(f"矩阵已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

def lp_pool(s,m,p):
    ls=torch.log(s.clamp(min=1e-7)); n=m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p*ls).masked_fill(m<0.5,-1e30),1)-torch.log(n))/p)

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.f=nn.Sequential(nn.Linear(D,HID),nn.ReLU(),nn.Dropout(0.1))
        self.g=nn.Sequential(nn.Linear(HID*2,HID),nn.ReLU(),nn.Dropout(0.1))
        self.o=nn.Linear(HID,1); self.p_log=nn.Parameter(torch.tensor(float(np.log(2.0))))
    @property
    def p(self): return torch.exp(self.p_log).clamp(1e-3,1e3)
    def forward(self,x,m):
        h=self.f(x)*m.unsqueeze(-1)
        c=(torch.cumsum(h,1)/torch.cumsum(m,1).clamp(min=1.0).unsqueeze(-1))*m.unsqueeze(-1)
        return self.o(self.g(torch.cat([h,c],-1))).squeeze(-1)

_sl=(y23[I23.reshape(-1)].reshape(I23.shape)*M23).max(1)>0
_spw=float((1-_sl.mean())/max(_sl.mean(),1e-8))
_pos=torch.tensor([(1-y23.mean())/y23.mean()],device=dev)
_lf=nn.BCEWithLogitsLoss(reduction="none",pos_weight=_pos); _bs=nn.BCELoss(reduction="none")

torch.manual_seed(SEED); np.random.seed(SEED)
net=Model().to(dev)
dec=[p for n,p in net.named_parameters() if not(n.endswith(".bias") or n=="p_log")]
nod=[p for n,p in net.named_parameters() if (n.endswith(".bias") or n=="p_log")]
opt=torch.optim.AdamW([{"params":dec,"weight_decay":0.01},{"params":nod,"weight_decay":0.0}],lr=2e-3)
gen=torch.Generator().manual_seed(SEED); snaps=[]; t0=_t.time()
net.train()
for st in range(STEPS):
    sel=torch.randint(0,len(I23),(BS,),generator=gen).to(dev)
    idx=gI23[sel]; msk=gM23[sel]
    lo=net(gX23[idx.reshape(-1)].reshape(BS,L,D),msk)
    yb=gy23[idx.reshape(-1)].reshape(BS,L)
    loss=(_lf(lo,yb)*msk).sum()/msk.sum().clamp(min=1)
    sq=lp_pool(torch.sigmoid(lo),msk,net.p).clamp(1e-6,1-1e-6); ysq=(yb*msk).amax(1)
    w=1.0+(_spw-1.0)*ysq; loss=loss+AUX_W*((_bs(sq,ysq)*w).sum()/w.sum())
    opt.zero_grad(set_to_none=True); loss.backward()
    torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
    if STEPS-st<=AVG_LAST*EPOCH_STEPS and (st+1)%EPOCH_STEPS==0:
        snaps.append({k:v.detach().clone() for k,v in net.state_dict().items()})
log(f"C11 训练完成 {(_t.time()-t0)/60:.1f} 分，检查点 {len(snaps)} 个，p={net.p.item():.4f}")
P_LEARNED=float(np.mean([  # 末5检查点的 p 均值
    (lambda sd: (net.load_state_dict(sd), float(net.p.item()))[1])(sd) for sd in snaps]))

@torch.no_grad()
def score(gI,gM,gX,n_flow):
    acc=None; seen=None
    for sd in snaps:
        net.load_state_dict(sd); net.eval()
        sc=torch.zeros(n_flow,device=dev); sn=torch.zeros(n_flow,dtype=torch.bool,device=dev)
        for a in range(0,len(gI),2048):
            idx=gI[a:a+2048]; msk=gM[a:a+2048]; b=idx.shape[0]
            pr=torch.sigmoid(net(gX[idx.reshape(-1)].reshape(b,L,D),msk))
            fi=idx.reshape(-1); fm=msk.reshape(-1)>0
            sc[fi[fm]]=pr.reshape(-1)[fm]; sn[fi[fm]]=True
        s_=sc.cpu().numpy(); n_=sn.cpu().numpy()
        acc=s_ if acc is None else acc+s_; seen=n_ if seen is None else (seen|n_)
    net.train()
    return acc/len(snaps), seen

sc23,seen23 = score(gI23,gM23,gX23,len(y23))
sc24,seen24 = score(gI24,gM24,gX24,len(y24))
log(f"打分完成：源年覆盖 {seen23.mean():.4f}  目标年覆盖 {seen24.mean():.4f}")

# ---- 源年度实体：用序列作决策单元（与训练单元一致，保守口径）----
seq_lab23=(y23[I23.reshape(-1)].reshape(I23.shape)*M23).max(1)
def seq_scores(sc,I,M,p):
    v=sc[I.reshape(-1)].reshape(I.shape); m=M
    num=(np.clip(v,1e-7,1.0)**p*m).sum(1); cnt=m.sum(1).clip(min=1)
    return (num/cnt)**(1.0/p)
S23=seq_scores(sc23,I23,M23,P_LEARNED)

def ent_scores(sc,seen,p):
    num=np.zeros(N24,np.float64); cnt=np.zeros(N24,np.float64)
    np.add.at(num,ent24[seen],np.clip(sc[seen],1e-7,1.0).astype(np.float64)**p)
    np.add.at(cnt,ent24[seen],1.0)
    return np.where(cnt>0,(num/np.maximum(cnt,1))**(1.0/p),-np.inf).astype(np.float32)
S24=ent_scores(sc24,seen24,P_LEARNED)

def fpr_dr(scores,labels,thr):
    neg=labels==0; pos=labels==1
    return float((scores[neg]>=thr).mean()), float((scores[pos]>=thr).mean())

def thr_at_fpr(scores,labels,target):
    neg=np.sort(scores[labels==0])[::-1]
    return float(neg[min(int(len(neg)*target),len(neg)-1)])

print("\n"+"="*104, flush=True)
print("【第四章证伪实验】源年度冻结阈值能否迁到目标年度", flush=True)
thr_src = thr_at_fpr(S23, seq_lab23, TARGET_FPR)
fpr_src, dr_src = fpr_dr(S23, seq_lab23, thr_src)
ok=np.isfinite(S24)
thr_ora = thr_at_fpr(S24[ok], lab24[ok], TARGET_FPR)
fpr_frz, dr_frz = fpr_dr(S24[ok], lab24[ok], thr_src)
fpr_ora, dr_ora = fpr_dr(S24[ok], lab24[ok], thr_ora)
print(f"  源年度校准        阈值={thr_src:.8f}  实测FPR={fpr_src:.4f}  DR={dr_src:.4f}", flush=True)
print(f"  冻结迁到目标年    阈值={thr_src:.8f}  实测FPR={fpr_frz:.4f}  DR={dr_frz:.4f}", flush=True)
print(f"  目标年 oracle     阈值={thr_ora:.8f}  实测FPR={fpr_ora:.4f}  DR={dr_ora:.4f}", flush=True)
print(f"  → FPR 偏离目标 {TARGET_FPR}: {fpr_frz-TARGET_FPR:+.4f}   DR 相对 oracle 损失: {dr_ora-dr_frz:+.4f}", flush=True)
k1 = (0.03<=fpr_frz<=0.05) and (dr_ora-dr_frz)<=0.02
print(f"  ★ 证伪判据一（阈值本就迁得过去）: {'成立→机制增量不必要' if k1 else '不成立→漂移问题真实存在'}", flush=True)

print("\n"+"-"*104, flush=True)
print("【BBSE 先验估计】只用目标年最早 10% 的特征，不看其标签", flush=True)
cut=np.quantile(t24, PREFIX_FRAC)
pre=(t24<=cut)&seen24
# BBSE: 用源年度混淆矩阵反解目标先验。阈值取源年度 0.5 分位工作点。
op = thr_at_fpr(sc23[seen23], y23[seen23], 0.10)
tpr_s = float((sc23[seen23][y23[seen23]==1]>=op).mean())
fpr_s = float((sc23[seen23][y23[seen23]==0]>=op).mean())
q_t = float((sc24[pre]>=op).mean())
pi_hat = (q_t - fpr_s)/max(tpr_s - fpr_s, 1e-8)
pi_hat = float(np.clip(pi_hat, 0.0, 1.0))
pi_true = float(y24[seen24].mean())
rel = abs(pi_hat-pi_true)/max(pi_true,1e-12)
print(f"  源年度工作点 阈值={op:.8f}  TPR={tpr_s:.4f}  FPR={fpr_s:.4f}", flush=True)
print(f"  目标年前缀 {int(pre.sum()):,} 流（占 {pre.mean():.4f}），越阈率 q={q_t:.6f}", flush=True)
print(f"  BBSE 估计先验 = {pi_hat:.8f}   真值 = {pi_true:.8f}   相对误差 = {rel:.4f}", flush=True)
k2 = rel > 0.50
print(f"  ★ 证伪判据二（先验估不准）: {'成立→工具链断裂' if k2 else '不成立→BBSE 可用'}", flush=True)

print("\n"+"="*104, flush=True)
print(f"总裁决：机制增量{'不成立' if (k1 or k2) else '成立，可进入第四章正式设计'}", flush=True)
print(f"  逐流先验 源={y23.mean():.6f} 目标={y24.mean():.6f} 比值={y23.mean()/y24.mean():.4f}", flush=True)
print(f"  学到的 Lp 指数 p={P_LEARNED:.4f}", flush=True)
print("="*104, flush=True)

json.dump({"thr_src":thr_src,"fpr_src":fpr_src,"dr_src":dr_src,
           "fpr_frozen_on_target":fpr_frz,"dr_frozen_on_target":dr_frz,
           "thr_oracle":thr_ora,"fpr_oracle":fpr_ora,"dr_oracle":dr_ora,
           "bbse_pi_hat":pi_hat,"pi_true":pi_true,"bbse_rel_err":rel,
           "kill1_threshold_transfers":bool(k1),"kill2_bbse_broken":bool(k2),
           "p_learned":P_LEARNED,"prior_src":float(y23.mean()),"prior_tgt":float(y24.mean())},
          open(f"{OUT}/ch4_drift_results.json","w"), ensure_ascii=False, indent=2)
log(f"结果已存 {OUT}/ch4_drift_results.json")
