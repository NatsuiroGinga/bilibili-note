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






# ============ 第三章全套实验（对位朱焱雷 §3.6 八小节）============
# E7 延迟-准确率曲线  → 3.6.8 真实受限环境（同时是第四章候选二的生死线）
# E1 主性能对比      → 3.6.2      E2 稳定性 → 3.6.3      E3 2x2 消融 → 3.6.4
# E4 机理可视化数据  → 3.6.5      E5 长度敏感性 → 3.6.6  E6 类别分面 → 3.6.7
import os, json, time as _t
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-full"
os.makedirs(OUT, exist_ok=True)
SEED, KAPPA, EPS, AUX_W = 42, 5.0, 1e-6, 1.0
EPOCH_STEPS, AVG_LAST = 1000, 5

NEED = ["X23","y23","X24","y24","I23","M23","I24","M24","s24","d24","t24","cat24"]
if not all(os.path.exists(f"{CACHE}/{n}.npy") for n in NEED):
    log("缓存缺 t24/cat24（时间戳与攻击类别，评价分面用），补齐")
    import pyarrow.parquet as _pq
    _pf = _pq.ParquetFile(P24)
    _n = _pf.metadata.num_rows
    t24 = np.empty(_n, np.float64); cat24 = np.empty(_n, object); _o = 0
    for _rg in range(_pf.metadata.num_row_groups):
        _tb = _pf.read_row_group(_rg, columns=["mTimestampStart", "Category"])
        _k = _tb.num_rows
        t24[_o:_o+_k] = np.asarray(_tb.column("mTimestampStart").to_numpy(zero_copy_only=False), np.float64)
        cat24[_o:_o+_k] = _tb.column("Category").to_pylist(); _o += _k
        del _tb
    np.save(f"{CACHE}/t24.npy", t24); np.save(f"{CACHE}/cat24.npy", cat24)
C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24","d24","cat24"))) for n in NEED}
X23,y23,X24,y24 = C["X23"],C["y23"],C["X24"],C["y24"]
I23,M23,I24,M24 = C["I23"],C["M23"],C["I24"],C["M24"]
s24,d24,t24,cat24 = C["s24"],C["d24"],C["t24"],C["cat24"]
log(f"缓存命中：训练序列={len(I23):,} 评价序列={len(I24):,}")
dev = "cuda" if torch.cuda.is_available() else "cpu"

key24 = np.array([a+"|"+b if a<=b else b+"|"+a for a,b in zip(s24,d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max()+1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 先验={ent_lab.mean():.10f}")
# 每个实体内按时间排序的流序（供 E7 延迟曲线用「前 k 条」）
_ord = np.lexsort((t24, ent24))
_e = ent24[_ord]
_start = np.flatnonzero(np.r_[True, _e[1:] != _e[:-1]])
_rank = np.empty(len(_ord), np.int64)
_rank[_ord] = np.arange(len(_ord)) - np.repeat(_start, np.diff(np.r_[_start, len(_ord)]))
log(f"实体内时序秩已建，实体流数中位={np.median(np.diff(np.r_[_start,len(_ord)])):.0f}")

gX23 = torch.from_numpy(X23).to(dev); gy23 = torch.from_numpy(y23).to(dev)
gX24 = torch.from_numpy(X24).to(dev)
gI23 = torch.from_numpy(I23).to(dev); gM23 = torch.from_numpy(M23).to(dev)
gI24 = torch.from_numpy(I24).to(dev); gM24 = torch.from_numpy(M24).to(dev)
log(f"矩阵已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p*ls).masked_fill(m<0.5,-1e30),1)-torch.log(n))/p)

class Model(nn.Module):
    def __init__(self, agg, lp, hid=192, dp=0.1):
        super().__init__(); self.agg, self.lp = agg, lp
        self.f = nn.Sequential(nn.Linear(D,hid), nn.ReLU(), nn.Dropout(dp))
        self.g = nn.Sequential(nn.Linear(hid*2,hid), nn.ReLU(), nn.Dropout(dp))
        self.o = nn.Linear(hid,1); self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))
    @property
    def p(self): return torch.exp(self.p_log).clamp(1e-3,1e3)
    def forward(self,x,m):
        h = self.f(x)*m.unsqueeze(-1)
        c = ((torch.cumsum(h,1)/torch.cumsum(m,1).clamp(min=1.0).unsqueeze(-1))*m.unsqueeze(-1)
             if self.agg else torch.zeros_like(h))
        return self.o(self.g(torch.cat([h,c],-1))).squeeze(-1)

_sl = (y23[I23.reshape(-1)].reshape(I23.shape)*M23).max(1) > 0
_spw = float((1-_sl.mean())/max(_sl.mean(),1e-8))
_pos = torch.tensor([(1-y23.mean())/y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=_pos)
_bs = nn.BCELoss(reduction="none")

def train_one(agg, lp, seed, steps, L_use, hid=192, tag=""):
    torch.manual_seed(seed); np.random.seed(seed)
    net = Model(agg, lp, hid).to(dev)
    dec=[p for n,p in net.named_parameters() if not (n.endswith(".bias") or n=="p_log")]
    nod=[p for n,p in net.named_parameters() if (n.endswith(".bias") or n=="p_log")]
    opt = torch.optim.AdamW([{"params":dec,"weight_decay":0.01},{"params":nod,"weight_decay":0.0}], lr=2e-3)
    gen = torch.Generator().manual_seed(seed); snaps=[]; t0=_t.time()
    net.train()
    for st in range(steps):
        sel = torch.randint(0,len(I23),(BS,),generator=gen).to(dev)
        idx=gI23[sel][:,:L_use]; msk=gM23[sel][:,:L_use]
        xb=gX23[idx.reshape(-1)].reshape(BS,L_use,D); yb=gy23[idx.reshape(-1)].reshape(BS,L_use)
        lo=net(xb,msk); loss=(_lf(lo,yb)*msk).sum()/msk.sum().clamp(min=1)
        if lp:
            sq=lp_pool(torch.sigmoid(lo),msk,net.p).clamp(1e-6,1-1e-6); ysq=(yb*msk).amax(1)
            w=1.0+(_spw-1.0)*ysq; loss=loss+AUX_W*((_bs(sq,ysq)*w).sum()/w.sum())
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
        if steps-st<=AVG_LAST*EPOCH_STEPS and (st+1)%EPOCH_STEPS==0:
            snaps.append({k:v.detach().clone() for k,v in net.state_dict().items()})
    tr_t=_t.time()-t0
    if not snaps: snaps=[{k:v.detach().clone() for k,v in net.state_dict().items()}]
    acc=None; seen=None; ps=[]; t1=_t.time()
    for sd_ in snaps:
        net.load_state_dict(sd_); net.eval(); ps.append(net.p.item())
        sc=torch.zeros(len(y24),device=dev); sn=torch.zeros(len(y24),dtype=torch.bool,device=dev)
        with torch.no_grad():
            for a in range(0,len(I24),2048):
                idx=gI24[a:a+2048][:,:L_use]; msk=gM24[a:a+2048][:,:L_use]; b=idx.shape[0]
                pr=torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b,L_use,D),msk))
                fi=idx.reshape(-1); fm=msk.reshape(-1)>0
                sc[fi[fm]]=pr.reshape(-1)[fm]; sn[fi[fm]]=True
        s_=sc.cpu().numpy(); n_=sn.cpu().numpy()
        acc = s_ if acc is None else acc+s_; seen = n_ if seen is None else (seen|n_)
    ev_t=_t.time()-t1
    log(f"  {tag} 训练{tr_t/60:.1f}分 推理{ev_t:.0f}秒 p={np.mean(ps):.4f}")
    return acc/len(snaps), seen, float(np.mean(ps)), tr_t, ev_t, sum(p.numel() for p in net.parameters())


def ent_ap(sc, seen, p=None, first_k=None):
    """实体级 AP。first_k 不为空时只用每个实体按时间的前 k 条流（延迟约束）。"""
    m = seen.copy()
    if first_k is not None: m &= (_rank < first_k)
    if not m.any(): return float("nan"), 0
    if p is None:
        es=np.full(N_ENT,-np.inf,np.float32); np.maximum.at(es,ent24[m],sc[m])
    else:
        num=np.zeros(N_ENT,np.float64); cnt=np.zeros(N_ENT,np.float64)
        np.add.at(num,ent24[m],np.clip(sc[m],1e-7,1.0).astype(np.float64)**p); np.add.at(cnt,ent24[m],1.0)
        es=np.where(cnt>0,(num/np.maximum(cnt,1))**(1.0/p),-np.inf).astype(np.float32)
    ok=np.isfinite(es)
    return average_precision_score(ent_lab[ok],es[ok]), int(ok.sum())

def dr_at_fpr(sc, seen, target=0.04, p=None, first_k=None):
    m=seen.copy()
    if first_k is not None: m &= (_rank<first_k)
    if p is None:
        es=np.full(N_ENT,-np.inf,np.float32); np.maximum.at(es,ent24[m],sc[m])
    else:
        num=np.zeros(N_ENT,np.float64); cnt=np.zeros(N_ENT,np.float64)
        np.add.at(num,ent24[m],np.clip(sc[m],1e-7,1.0).astype(np.float64)**p); np.add.at(cnt,ent24[m],1.0)
        es=np.where(cnt>0,(num/np.maximum(cnt,1))**(1.0/p),-np.inf).astype(np.float32)
    ok=np.isfinite(es); v=es[ok]; l=ent_lab[ok]
    neg=np.sort(v[l==0])[::-1]
    if len(neg)==0: return float("nan")
    thr=neg[min(int(len(neg)*target),len(neg)-1)]
    return float((v[l==1]>=thr).mean())

RES={}
log("="*90); log("E1/E3 主性能与 2x2 消融（20000 步，末5检查点平均）")
CELLS=[("C00",False,False),("C01",False,True),("C10",True,False),("C11",True,True)]
for cid,agg,lp in CELLS:
    sc,seen,p,tr,ev,npar = train_one(agg,lp,SEED,20000,L,tag=cid)
    RES[cid]={"sc":sc,"seen":seen,"p":p,"tr":tr,"ev":ev,"npar":npar}
    fap=average_precision_score(y24[seen],sc[seen]); fauc=roc_auc_score(y24[seen],sc[seen])
    e1,_=ent_ap(sc,seen); elp,_=ent_ap(sc,seen,p if lp else None)
    RES[cid].update(fap=fap,fauc=fauc,e_max=e1,e_lp=elp,
                    dr=dr_at_fpr(sc,seen,0.04,p if lp else None))
    log(f"{cid}: 逐流AP={fap:.6f} AUC={fauc:.6f} 实体AP(max)={e1:.6f} 实体AP(Lp)={elp:.6f} DR@4%FPR={RES[cid]['dr']:.4f}")
np.save(f"{OUT}/scores_C11.npy", RES["C11"]["sc"]); np.save(f"{OUT}/seen_C11.npy", RES["C11"]["seen"])

log("="*90); log("E7 延迟-准确率曲线（每实体只用按时间的前 k 条流）→ 3.6.8，同时判第四章候选二生死")
KS=[1,2,3,5,10,20,50,100,None]
CURVE={}
for cid in ["C00","C11"]:
    r=RES[cid]; row=[]
    for k in KS:
        ap,ne=ent_ap(r["sc"],r["seen"],r["p"] if cid=="C11" else None,k)
        dr=dr_at_fpr(r["sc"],r["seen"],0.04,r["p"] if cid=="C11" else None,k)
        cov=float((r["seen"]&(_rank<k)).sum())/max(r["seen"].sum(),1) if k else 1.0
        row.append((k,ap,dr,ne,cov))
    CURVE[cid]=row
    log(f"  {cid}:")
    for k,ap,dr,ne,cov in row:
        log(f"    前{str(k or '全部'):>4}条  实体AP={ap:.6f}  DR@4%FPR={dr:.4f}  覆盖实体={ne:,}  用流占比={cov:.4f}")
full=CURVE["C11"][-1][1]
for k,ap,dr,ne,cov in CURVE["C11"]:
    if k and ap>=0.95*full:
        log(f"  ★ C11 前 {k} 条流即达全量 AP 的 95%（{ap:.6f}/{full:.6f}），延迟权衡{'弱' if k<=3 else '显著存在'}"); break

log("="*90); log("E2 训练稳定性（3 种子）→ 3.6.3")
STAB={}
for cid,agg,lp in [("C00",False,False),("C11",True,True)]:
    aps=[]
    for sd_ in [42,43,44]:
        if sd_==42: aps.append(RES[cid]["fap"]); continue
        sc,seen,p,_,_,_ = train_one(agg,lp,sd_,20000,L,tag=f"{cid}-s{sd_}")
        aps.append(average_precision_score(y24[seen],sc[seen]))
    STAB[cid]=aps
    log(f"  {cid}: {aps[0]:.6f} {aps[1]:.6f} {aps[2]:.6f} | 均值={np.mean(aps):.6f} 标准差={np.std(aps,ddof=1):.6f}")

log("="*90); log("E5 序列长度 L 敏感性 → 3.6.6")
LEN={}
for Lu in [16,32,64,128]:
    sc,seen,p,_,_,_ = train_one(True,True,SEED,8000,Lu,tag=f"L={Lu}")
    ap=average_precision_score(y24[seen],sc[seen]); e,_=ent_ap(sc,seen,p)
    LEN[Lu]=(ap,e,p); log(f"  L={Lu:>3}: 逐流AP={ap:.6f} 实体AP={e:.6f} p={p:.4f}")

log("="*90); log("E6 攻击类别分面 → 3.6.7")
FACET={}
r=RES["C11"]; sc,seen=r["sc"],r["seen"]
cats=np.array([c if c else "(空)" for c in cat24], object)
pos_cats=[c for c in np.unique(cats[(y24>0)&seen]) if (((cats==c)&(y24>0)&seen).sum()>=50)]
neg=(y24==0)&seen
for c in pos_cats:
    m=(((cats==c)&(y24>0))|neg)&seen
    ap=average_precision_score(y24[m],sc[m]); n=int(((cats==c)&(y24>0)&seen).sum())
    FACET[str(c)]=(ap,n); log(f"  {str(c)[:38]:<40} 正例={n:>7,}  AP={ap:.6f}")

log("="*90); log("E4 机理数据 → 3.6.5")
log(f"  学到的 Lp 指数: C01={RES['C01']['p']:.4f}  C11={RES['C11']['p']:.4f}（p=1 均值, p→∞ 上界）")
log(f"  参数量: {RES['C11']['npar']:,}（四格相同）")
log(f"  训练/推理耗时: " + "  ".join(f"{c}={RES[c]['tr']/60:.1f}分/{RES[c]['ev']:.0f}秒" for c in RES))

json.dump({"cells":{c:{k:(float(v) if isinstance(v,(int,float,np.floating)) else None)
                       for k,v in RES[c].items() if k not in("sc","seen")} for c in RES},
           "curve":{c:[[k,float(a),float(d),int(n),float(cv)] for k,a,d,n,cv in CURVE[c]] for c in CURVE},
           "stability":{c:[float(x) for x in v] for c,v in STAB.items()},
           "length":{str(k):[float(v[0]),float(v[1]),float(v[2])] for k,v in LEN.items()},
           "facet":{k:[float(v[0]),int(v[1])] for k,v in FACET.items()}},
          open(f"{OUT}/ch3_full_results.json","w"), ensure_ascii=False, indent=2)
log(f"全部结果已存 {OUT}/ch3_full_results.json")
