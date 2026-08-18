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








# ============ 第四章证伪实验 v2（修三处设计缺陷后重做）============
# v1 的三处缺陷与修法：
#   缺陷一 源年度阈值在训练数据上校准（in-sample，DR=0.9995 即过拟合证据），
#          同时污染 BBSE 的混淆矩阵（TPR_s=1.0 也是 in-sample）
#          → 修：LSPR23 按实体切 20% 留出，只在留出区校准阈值与估混淆矩阵
#   缺陷二 源年度用「序列」、目标年用「实体」作决策单元，聚合粒度错配
#          → 修：两边统一用「2-IP 实体」，需重建源年度实体键
#   缺陷三 BBSE 用最早 10% 前缀估计，却与全年先验比（0.0447 vs 0.0257，差 1.74 倍）
#          → 修：对照真值改为前缀自身先验；同时报「估前缀」与「估全年」两种口径
import os, json, time as _t
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch4-drift-v2"
os.makedirs(OUT, exist_ok=True)
SEED, KAPPA, EPS, AUX_W = 42, 5.0, 1e-6, 1.0
STEPS, EPOCH_STEPS, AVG_LAST = 20000, 1000, 5
TARGET_FPR = 0.04
HOLDOUT_FRAC = 0.20        # 源年度留出实体比例（缺陷一）
PREFIX_FRAC = 0.10

# ---- 缺陷二：重建源年度实体键（缓存无 s23/d23，重解析一次并落盘）----
NEED = ["X23","y23","X24","y24","I23","M23","I24","M24","s24","d24","t24","ent23"]
if not all(os.path.exists(f"{CACHE}/{n}.npy") for n in NEED):
    log("缓存缺 ent23（源年度实体键），重解析 LSPR23 补齐")
    _X, _y, _s, _d, _t23 = load("23")
    _k = np.array([a+"|"+b if a<=b else b+"|"+a for a,b in zip(_s,_d)], object)
    _, _inv = np.unique(_k, return_inverse=True)
    np.save(f"{CACHE}/ent23.npy", _inv.astype(np.int64))
    log(f"ent23 已落盘：源年度实体 {_inv.max()+1:,}")
    del _X,_y,_s,_d,_t23,_k,_inv
C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24","d24"))) for n in NEED}
X23,y23,X24,y24 = C["X23"],C["y23"],C["X24"],C["y24"]
I23,M23,I24,M24,s24,d24,t24,ent23 = C["I23"],C["M23"],C["I24"],C["M24"],C["s24"],C["d24"],C["t24"],C["ent23"]
N23 = int(ent23.max())+1
lab23 = np.zeros(N23, np.float32); np.maximum.at(lab23, ent23, y23)
log(f"源年度实体={N23:,} 正例实体={int(lab23.sum()):,} 实体先验={lab23.mean():.10f}")

ent24 = None
_k24 = np.array([a+"|"+b if a<=b else b+"|"+a for a,b in zip(s24,d24)], object)
_, ent24 = np.unique(_k24, return_inverse=True); del _k24
N24 = int(ent24.max())+1
lab24 = np.zeros(N24, np.float32); np.maximum.at(lab24, ent24, y24)
log(f"目标年实体={N24:,} 正例实体={int(lab24.sum()):,} 实体先验={lab24.mean():.10f}")
log(f"逐流先验：源={y23.mean():.10f} 目标={y24.mean():.10f} 比值={y23.mean()/y24.mean():.4f}")

# ---- 缺陷一：源年度按实体切留出，训练区与校准区实体不相交 ----
# 分层切分：实体规模极度重尾且恶意流高度集中，随机切会把大部分正例切进留出区。
# 实测随机切的后果：留出区逐流先验 36.5% vs 源年度 10.06%（74% 正例落入 20% 留出）。
# 故按「实体是否含恶意流」× 「实体流数分位」双重分层，保证留出区先验贴近全局。
rs = np.random.RandomState(SEED)
_cnt23 = np.bincount(ent23, minlength=N23)
_pos23 = np.zeros(N23, np.float64); np.add.at(_pos23, ent23, y23)
_mal = _pos23 > 0
_size_bin = np.digitize(_cnt23, np.quantile(_cnt23[_cnt23 > 0], [0.5, 0.9, 0.99]))
hold_ent = set()
for _m in (False, True):
    for _b in range(4):
        _g = np.flatnonzero((_mal == _m) & (_size_bin == _b))
        if len(_g) == 0: continue
        _pick = rs.permutation(len(_g))[:max(1, int(round(len(_g)*HOLDOUT_FRAC)))]
        hold_ent.update(_g[_pick].tolist())
_hf_chk = np.fromiter((e in hold_ent for e in ent23), bool, len(ent23))
log(f"分层切分核验：留出流先验={y23[_hf_chk].mean():.6f}  训练流先验={y23[~_hf_chk].mean():.6f}  "
    f"全局={y23.mean():.6f}  留出流占比={_hf_chk.mean():.4f}")
assert abs(y23[_hf_chk].mean() - y23.mean()) / y23.mean() < 0.35, \
    f"留出区先验偏离全局超 35%：{y23[_hf_chk].mean():.6f} vs {y23.mean():.6f}"
flow_hold = np.fromiter((e in hold_ent for e in ent23), bool, len(ent23))
seq_ent = ent23[I23[:,0]]                                  # 每条序列所属实体（块首流）
seq_hold = np.fromiter((e in hold_ent for e in seq_ent), bool, len(seq_ent))
tr_seq = np.flatnonzero(~seq_hold)
assert len(set(seq_ent[tr_seq]).intersection(hold_ent))==0, "训练序列混入留出实体"
log(f"源年度留出：实体 {len(hold_ent):,}/{N23:,}  训练序列 {len(tr_seq):,}/{len(I23):,}  "
    f"留出流 {int(flow_hold.sum()):,}（{flow_hold.mean():.4f}）")

dev = "cuda" if torch.cuda.is_available() else "cpu"
gX23=torch.from_numpy(X23).to(dev); gy23=torch.from_numpy(y23).to(dev)
gX24=torch.from_numpy(X24).to(dev)
gI23=torch.from_numpy(I23).to(dev); gM23=torch.from_numpy(M23).to(dev)
gI24=torch.from_numpy(I24).to(dev); gM24=torch.from_numpy(M24).to(dev)
gtr=torch.from_numpy(tr_seq).to(dev)
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

ytr = y23[I23[tr_seq].reshape(-1)]
_sl=(y23[I23[tr_seq].reshape(-1)].reshape(len(tr_seq),L)*M23[tr_seq]).max(1)>0
_spw=float((1-_sl.mean())/max(_sl.mean(),1e-8))
_pos=torch.tensor([(1-ytr.mean())/ytr.mean()],device=dev)
_lf=nn.BCEWithLogitsLoss(reduction="none",pos_weight=_pos); _bs=nn.BCELoss(reduction="none")
log(f"训练区逐流先验={ytr.mean():.10f} pos_weight={_pos.item():.4f}  序列级 pos_weight={_spw:.4f}")

torch.manual_seed(SEED); np.random.seed(SEED)
net=Model().to(dev)
dec=[p for n,p in net.named_parameters() if not(n.endswith(".bias") or n=="p_log")]
nod=[p for n,p in net.named_parameters() if (n.endswith(".bias") or n=="p_log")]
opt=torch.optim.AdamW([{"params":dec,"weight_decay":0.01},{"params":nod,"weight_decay":0.0}],lr=2e-3)
gen=torch.Generator().manual_seed(SEED); snaps=[]; t0=_t.time()
net.train()
for st in range(STEPS):
    sel=gtr[torch.randint(0,len(tr_seq),(BS,),generator=gen).to(dev)]
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
P_LEARNED=float(np.mean([(lambda sd:(net.load_state_dict(sd),float(net.p.item()))[1])(sd) for sd in snaps]))
log(f"训练完成 {(_t.time()-t0)/60:.1f} 分，p={P_LEARNED:.4f}（仅用留出外实体）")

@torch.no_grad()
def score(gI,gM,gX,n):
    acc=None; seen=None
    for sd in snaps:
        net.load_state_dict(sd); net.eval()
        sc=torch.zeros(n,device=dev); sn=torch.zeros(n,dtype=torch.bool,device=dev)
        for a in range(0,len(gI),2048):
            idx=gI[a:a+2048]; msk=gM[a:a+2048]; b=idx.shape[0]
            pr=torch.sigmoid(net(gX[idx.reshape(-1)].reshape(b,L,D),msk))
            fi=idx.reshape(-1); fm=msk.reshape(-1)>0
            sc[fi[fm]]=pr.reshape(-1)[fm]; sn[fi[fm]]=True
        s_=sc.cpu().numpy(); n_=sn.cpu().numpy()
        acc=s_ if acc is None else acc+s_; seen=n_ if seen is None else (seen|n_)
    net.train(); return acc/len(snaps), seen

sc23,seen23 = score(gI23,gM23,gX23,len(y23))
sc24,seen24 = score(gI24,gM24,gX24,len(y24))
log(f"打分完成：源覆盖 {seen23.mean():.4f} 目标覆盖 {seen24.mean():.4f}")

# ---- 缺陷二：两边统一用实体级聚合 ----
def ent_score(sc, seen, ent, N, p, extra=None):
    m = seen if extra is None else (seen & extra)
    num=np.zeros(N,np.float64); cnt=np.zeros(N,np.float64)
    np.add.at(num, ent[m], np.clip(sc[m],1e-7,1.0).astype(np.float64)**p)
    np.add.at(cnt, ent[m], 1.0)
    return np.where(cnt>0,(num/np.maximum(cnt,1))**(1.0/p),-np.inf).astype(np.float32)

def thr_at_fpr(s,l,t):
    neg=np.sort(s[l==0])[::-1]; return float(neg[min(int(len(neg)*t),len(neg)-1)])
def fpr_dr(s,l,t):
    return float((s[l==0]>=t).mean()), float((s[l==1]>=t).mean())

S23h = ent_score(sc23, seen23, ent23, N23, P_LEARNED, extra=flow_hold)   # 只用留出流
hold_mask = np.isfinite(S23h)
S24  = ent_score(sc24, seen24, ent24, N24, P_LEARNED)
ok24 = np.isfinite(S24)
log(f"源留出实体 {int(hold_mask.sum()):,}（正例 {int(lab23[hold_mask].sum()):,}）  目标实体 {int(ok24.sum()):,}")

print("\n"+"="*104, flush=True)
print("【v2】源年度留出实体上校准 → 冻结迁到目标年（决策单元两边统一为 2-IP 实体）", flush=True)
thr_src = thr_at_fpr(S23h[hold_mask], lab23[hold_mask], TARGET_FPR)
fpr_s, dr_s = fpr_dr(S23h[hold_mask], lab23[hold_mask], thr_src)
thr_ora = thr_at_fpr(S24[ok24], lab24[ok24], TARGET_FPR)
fpr_f, dr_f = fpr_dr(S24[ok24], lab24[ok24], thr_src)
fpr_o, dr_o = fpr_dr(S24[ok24], lab24[ok24], thr_ora)
print(f"  源留出校准    阈值={thr_src:.10f}  FPR={fpr_s:.4f}  DR={dr_s:.4f}   ← v1 此处为 0.9995（in-sample 过拟合）", flush=True)
print(f"  冻结迁目标年  阈值={thr_src:.10f}  FPR={fpr_f:.4f}  DR={dr_f:.4f}", flush=True)
print(f"  目标年 oracle 阈值={thr_ora:.10f}  FPR={fpr_o:.4f}  DR={dr_o:.4f}", flush=True)
print(f"  → FPR 偏离 {fpr_f-TARGET_FPR:+.4f}   DR 相对 oracle 损失 {dr_o-dr_f:+.4f}   阈值比 {thr_src/max(thr_ora,1e-12):.2f}×", flush=True)
k1 = (0.03<=fpr_f<=0.05) and (dr_o-dr_f)<=0.02
print(f"  ★ 判据一（阈值本就迁得过去）：{'成立→机制增量不必要' if k1 else '不成立→漂移问题真实存在'}", flush=True)

print("\n"+"-"*104, flush=True)
print("【v2】BBSE：混淆矩阵只在源留出流上估，对照真值改为前缀自身先验", flush=True)
cut=np.quantile(t24,PREFIX_FRAC); pre=(t24<=cut)&seen24
pi_pre = float(y24[pre].mean()); pi_all = float(y24[seen24].mean())
print(f"  前缀 {int(pre.sum()):,} 流  前缀先验={pi_pre:.10f}  全年先验={pi_all:.10f}  比值={pi_pre/pi_all:.4f}", flush=True)
hf = seen23 & flow_hold
print(f"{'源FPR':>8}{'源TPR':>9}{'TPR-FPR':>10}{'目标q':>11}{'π̂':>13}{'对前缀误差':>12}{'对全年误差':>12}", flush=True)
best=None
for f_op in [0.001,0.005,0.01,0.02,0.05,0.10,0.20,0.30,0.50]:
    op=thr_at_fpr(sc23[hf], y23[hf], f_op)
    tpr=float((sc23[hf][y23[hf]==1]>=op).mean()); fpr=float((sc23[hf][y23[hf]==0]>=op).mean())
    q=float((sc24[pre]>=op).mean()); den=tpr-fpr
    pi=(q-fpr)/den if abs(den)>1e-8 else float("nan")
    pic=float(np.clip(pi,0,1))
    e_pre=abs(pic-pi_pre)/pi_pre; e_all=abs(pic-pi_all)/pi_all
    tag = "  q<FPR→π̂<0" if q<fpr else ""
    if best is None or e_pre<best[1]: best=(f_op,e_pre,pic,q<fpr)
    print(f"{fpr:>8.4f}{tpr:>9.4f}{den:>10.4f}{q:>11.6f}{pic:>13.8f}{e_pre:>12.4f}{e_all:>12.4f}{tag}", flush=True)
k2 = best[1] > 0.50
print(f"  → 最佳工作点 源FPR={best[0]}  π̂={best[2]:.8f}  对前缀真值相对误差={best[1]:.4f}", flush=True)
print(f"  ★ 判据二（先验估不准）：{'成立→BBSE 不可用' if k2 else '不成立→BBSE 可用'}", flush=True)

print("\n"+"-"*104, flush=True)
print("【v2】路径3：无标签前缀分位数校准（含前缀 vs 全年分数分布诊断）", flush=True)
Spre = ent_score(sc24, seen24, ent24, N24, P_LEARNED, extra=pre)
okp = np.isfinite(Spre); both = okp & ok24
print(f"  前缀覆盖实体 {int(okp.sum()):,}/{N24:,}", flush=True)
for q_ in (0.90,0.96,0.99):
    a=float(np.quantile(Spre[both],q_)); b=float(np.quantile(S24[both],q_))
    print(f"    {q_*100:.0f}% 分位  前缀={a:.10f}  全年={b:.10f}  比值={a/max(b,1e-12):.4f}", flush=True)
thr_p=float(np.quantile(Spre[okp],1.0-TARGET_FPR))
fpr_p,dr_p=fpr_dr(S24[ok24],lab24[ok24],thr_p)
print(f"  分位数校准  阈值={thr_p:.10f}  目标年实测FPR={fpr_p:.4f}  DR={dr_p:.4f}  DR损失={dr_o-dr_p:+.4f}", flush=True)
k3 = 0.03<=fpr_p<=0.05
print(f"  ★ 路径3：{'可用' if k3 else '不可用'}（判据：实测 FPR ∈ [0.03,0.05]）", flush=True)

print("\n"+"="*104, flush=True)
print(f"{'方法':<26}{'阈值':>15}{'实测FPR':>10}{'DR':>9}{'DR损失':>10}", flush=True)
for nm,t_,f_,d_ in [("源留出冻结迁移",thr_src,fpr_f,dr_f),("前缀分位数校准",thr_p,fpr_p,dr_p),("目标年 oracle",thr_ora,fpr_o,dr_o)]:
    print(f"{nm:<26}{t_:>15.10f}{f_:>10.4f}{d_:>9.4f}{dr_o-d_:>10.4f}", flush=True)
surv=[n for n,f in [("BBSE",not k2),("前缀分位数",k3)] if f]
print(f"\n  ★ 存活路径：{('、'.join(surv)) if surv else '无'}", flush=True)
print(f"  ★ 漂移问题：{'不存在' if k1 else '真实存在'}", flush=True)
print("="*104, flush=True)
json.dump({"holdout_frac":HOLDOUT_FRAC,"thr_src":thr_src,"fpr_src_holdout":fpr_s,"dr_src_holdout":dr_s,
           "fpr_frozen":fpr_f,"dr_frozen":dr_f,"thr_oracle":thr_ora,"fpr_oracle":fpr_o,"dr_oracle":dr_o,
           "prefix_prior":pi_pre,"full_prior":pi_all,"bbse_best_op":best[0],"bbse_pi_hat":best[2],
           "bbse_rel_err_vs_prefix":best[1],"path3_thr":thr_p,"path3_fpr":fpr_p,"path3_dr":dr_p,
           "kill1_threshold_transfers":bool(k1),"kill2_bbse_broken":bool(k2),"path3_usable":bool(k3),
           "p_learned":P_LEARNED,"survivors":surv},
          open(f"{OUT}/ch4_drift_v2.json","w"), ensure_ascii=False, indent=2)
log(f"结果已存 {OUT}/ch4_drift_v2.json")
