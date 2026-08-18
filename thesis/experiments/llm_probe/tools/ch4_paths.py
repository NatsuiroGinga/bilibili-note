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


# ============ 三条补救路径同场对比 ============
# 路径1  换工作点重试 BBSE —— 排除「饱和工作点导致病态求逆」这个可能
# 路径2  EM 先验估计（Saerens-Latinne-Decaestecker 1998）—— 不依赖单点混淆矩阵
# 路径3  无标签目标前缀直接分位数校准 —— 不估先验，直接在前缀上定阈值
RES = {}
print("\n"+"="*108, flush=True)
print("【基准】源年度冻结阈值直接迁移（已知失败，作对照）", flush=True)
thr_src = thr_at_fpr(S23, seq_lab23, TARGET_FPR)
ok = np.isfinite(S24)
thr_ora = thr_at_fpr(S24[ok], lab24[ok], TARGET_FPR)
fpr_frz, dr_frz = fpr_dr(S24[ok], lab24[ok], thr_src)
fpr_ora, dr_ora = fpr_dr(S24[ok], lab24[ok], thr_ora)
print(f"  冻结迁移    阈值={thr_src:.10f}  FPR={fpr_frz:.4f}  DR={dr_frz:.4f}", flush=True)
print(f"  oracle 上界 阈值={thr_ora:.10f}  FPR={fpr_ora:.4f}  DR={dr_ora:.4f}", flush=True)
RES["frozen"]={"thr":thr_src,"fpr":fpr_frz,"dr":dr_frz}
RES["oracle"]={"thr":thr_ora,"fpr":fpr_ora,"dr":dr_ora}

cut = np.quantile(t24, PREFIX_FRAC)
pre = (t24 <= cut) & seen24          # 目标年最早 10%，只用特征不看标签
log(f"目标年无标签前缀 {int(pre.sum()):,} 流（占 {pre.mean():.4f}）")

print("\n"+"-"*108, flush=True)
print("【路径1·诊断】扫工作点检验 BBSE 前提是否成立", flush=True)
print("  自检结论：合成数据上 TPR 饱和到 1.0 时 BBSE 误差仍仅 0.016~0.029，", flush=True)
print("            故「饱和导致病态求逆」已被否掉。若此处仍失败，病因是 p(x|y) 改变（非纯标签漂移）。", flush=True)
print("  判据：q < FPR_s 即 π̂ 为负，直接证明 p(x|y) 变了——纯标签漂移下 q ≥ FPR_s 恒成立。", flush=True)
print(f"{'源FPR':>8}{'源TPR':>9}{'TPR-FPR':>10}{'目标越阈率q':>13}{'BBSE π̂':>12}{'相对误差':>11}", flush=True)
pi_true = float(y24[seen24].mean())
best1 = None
for f_op in [0.001,0.005,0.01,0.02,0.05,0.10,0.20,0.30,0.50]:
    op = thr_at_fpr(sc23[seen23], y23[seen23], f_op)
    tpr_s = float((sc23[seen23][y23[seen23]==1] >= op).mean())
    fpr_s = float((sc23[seen23][y23[seen23]==0] >= op).mean())
    q = float((sc24[pre] >= op).mean())
    den = tpr_s - fpr_s
    pi = (q - fpr_s)/den if abs(den) > 1e-8 else float("nan")
    pic = float(np.clip(pi, 0.0, 1.0))
    rel = abs(pic - pi_true)/pi_true
    flag = ("  q<FPR_s→p(x|y)已变" if q < fpr_s else "") or ("  ←最佳" if (best1 is None or rel < best1[1]) else "")
    if best1 is None or rel < best1[1]: best1 = (f_op, rel, pic)
    print(f"{fpr_s:>8.4f}{tpr_s:>9.4f}{den:>10.4f}{q:>13.6f}{pic:>12.8f}{rel:>11.4f}{flag}", flush=True)
print(f"  → 最佳工作点 源FPR={best1[0]}  π̂={best1[2]:.8f}  真值={pi_true:.8f}  相对误差={best1[1]:.4f}", flush=True)
k1 = best1[1] <= 0.50
n_neg = sum(1 for f_op in [0.001,0.005,0.01,0.02,0.05,0.10,0.20,0.30,0.50]
            if (lambda op: float((sc24[pre]>=op).mean()) < float((sc23[seen23][y23[seen23]==0]>=op).mean()))
               (thr_at_fpr(sc23[seen23], y23[seen23], f_op)))
print(f"  → {n_neg}/9 个工作点出现 q < FPR_s（π̂ 为负）", flush=True)
print(f"  ★ 路径1 {'可用' if k1 else '不可用'}；'''若多数工作点 q<FPR_s，则本课题不是纯标签漂移，BBSE 前提失效'''", flush=True)
RES["path1_bbse_sweep"]={"best_src_fpr":best1[0],"pi_hat":best1[2],"rel_err":best1[1],"usable":bool(k1)}

print("\n"+"-"*108, flush=True)
print("【路径2】EM 先验估计（Saerens-Latinne-Decaestecker 1998）+ 前置概率校准", flush=True)
print("  自检发现：EM 要求输入是「源先验下的校准后验」。本课题模型用 pos_weight=8.9438 训练，", flush=True)
print("            输出不是校准后验，直接喂入必然跑飞（合成数据上估到 1.0，误差 37.9）。", flush=True)
print("            故先在源年度用保序回归校准，再跑 EM，并同时报未校准版作对照。", flush=True)
from sklearn.isotonic import IsotonicRegression
pi_s = float(y23[seen23].mean())
_sub = np.random.RandomState(SEED).choice(np.flatnonzero(seen23), size=min(2000000, int(seen23.sum())), replace=False)
_iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(sc23[_sub], y23[_sub])
_cal_src = _iso.predict(sc23[_sub])
print(f"  源年度校准检查：校准后均值={_cal_src.mean():.8f}  源先验={pi_s:.8f}  差={_cal_src.mean()-pi_s:+.2e}", flush=True)
p_x_raw = sc24[pre].astype(np.float64).clip(1e-7, 1-1e-7)
p_x = np.clip(_iso.predict(sc24[pre]).astype(np.float64), 1e-7, 1-1e-7)
pi_em = pi_s
for it in range(200):
    w1 = (pi_em/pi_s)*p_x
    w0 = ((1-pi_em)/(1-pi_s))*(1-p_x)
    post = w1/(w1+w0)
    new = float(post.mean())
    if abs(new - pi_em) < 1e-10: break
    pi_em = new
rel2 = abs(pi_em - pi_true)/pi_true
pi_raw = pi_s
for _ in range(200):
    w1r=(pi_raw/pi_s)*p_x_raw; w0r=((1-pi_raw)/(1-pi_s))*(1-p_x_raw)
    nr=float((w1r/(w1r+w0r)).mean())
    if abs(nr-pi_raw)<1e-10: break
    pi_raw=nr
print(f"  源先验={pi_s:.8f}  迭代 {it+1} 轮收敛", flush=True)
print(f"  未校准对照 π̂={pi_raw:.8f} 相对误差={abs(pi_raw-pi_true)/pi_true:.4f}", flush=True)
print(f"  EM 估计 π̂ = {pi_em:.8f}   真值 = {pi_true:.8f}   相对误差 = {rel2:.4f}", flush=True)
k2 = rel2 <= 0.50
print(f"  ★ 路径2 {'可用' if k2 else '不可用'}", flush=True)
RES["path2_em"]={"pi_hat":pi_em,"rel_err":rel2,"iters":it+1,"usable":bool(k2)}

print("\n"+"-"*108, flush=True)
print("【路径3】无标签目标前缀直接分位数校准 —— 不估先验，直接定阈值", flush=True)
print("  原理：前缀中恶意流占比极低（约 2.6%），把前缀整体近似为负例分布，", flush=True)
print("        取其 (1-4%) 分位数作阈值。偏差方向已知：略偏保守。", flush=True)
# 实体级：先在前缀上按实体聚合，再取分位数
def ent_from(mask, p):
    num=np.zeros(N24,np.float64); cnt=np.zeros(N24,np.float64)
    np.add.at(num, ent24[mask], np.clip(sc24[mask],1e-7,1.0).astype(np.float64)**p)
    np.add.at(cnt, ent24[mask], 1.0)
    return np.where(cnt>0,(num/np.maximum(cnt,1))**(1.0/p),-np.inf).astype(np.float32)
Spre = ent_from(pre, P_LEARNED)
okp = np.isfinite(Spre)
print(f"  前缀覆盖实体 {int(okp.sum()):,}/{N24:,}", flush=True)
_both = okp & ok
print("  【自检要求的诊断】前缀实体分数 vs 全年实体分数的分布差异（仅两者都有的实体）：", flush=True)
for _q in (0.90, 0.96, 0.99):
    _a=float(np.quantile(Spre[_both],_q)); _b=float(np.quantile(S24[_both],_q))
    print(f"    {_q*100:.0f}% 分位  前缀={_a:.10f}  全年={_b:.10f}  比值={_a/max(_b,1e-12):.4f}", flush=True)
_ratio = float(np.quantile(Spre[_both],1-TARGET_FPR)/max(np.quantile(S24[_both],1-TARGET_FPR),1e-12))
print(f"    → 96% 分位比值 {_ratio:.4f}；偏离 1.0 越远，路径3 的 FPR 偏差越大", flush=True)
RES["path3_diag_quantile_ratio"]=_ratio
for q_lvl in [TARGET_FPR]:
    thr_p = float(np.quantile(Spre[okp], 1.0 - q_lvl))
    fpr_p, dr_p = fpr_dr(S24[ok], lab24[ok], thr_p)
    print(f"  分位数校准  阈值={thr_p:.10f}  目标年实测FPR={fpr_p:.4f}  DR={dr_p:.4f}", flush=True)
    RES["path3_quantile"]={"thr":thr_p,"fpr":fpr_p,"dr":dr_p}
k3 = (0.03 <= RES["path3_quantile"]["fpr"] <= 0.05)
print(f"  ★ 路径3 {'可用' if k3 else '不可用'}（判据：实测 FPR ∈ [0.03,0.05]）", flush=True)

print("\n"+"="*108, flush=True)
print("【三路对比】相对 oracle 的 DR 损失与 FPR 偏离", flush=True)
print(f"{'方法':<28}{'阈值':>14}{'实测FPR':>10}{'DR':>9}{'DR损失':>10}{'FPR偏离':>10}", flush=True)
rows=[("源年度冻结迁移（基准）", RES["frozen"]),
      ("路径3 前缀分位数校准", RES["path3_quantile"]),
      ("目标年 oracle（上界）", RES["oracle"])]
if k1:
    thr_b = thr_at_fpr(S24[ok], lab24[ok], TARGET_FPR)  # 占位，先验估计需再推导阈值
for nm, r in rows:
    print(f"{nm:<28}{r['thr']:>14.10f}{r['fpr']:>10.4f}{r['dr']:>9.4f}"
          f"{dr_ora-r['dr']:>10.4f}{r['fpr']-TARGET_FPR:>+10.4f}", flush=True)
print("-"*108, flush=True)
print(f"  路径1 BBSE 扫工作点  最佳相对误差 {best1[1]:.4f}  {'可用' if k1 else '不可用'}", flush=True)
print(f"  路径2 EM 估计        相对误差 {rel2:.4f}  {'可用' if k2 else '不可用'}", flush=True)
print(f"  路径3 分位数校准     DR 损失 {dr_ora-RES['path3_quantile']['dr']:.4f}  {'可用' if k3 else '不可用'}", flush=True)
surv=[n for n,f in [("路径1",k1),("路径2",k2),("路径3",k3)] if f]
print(f"\n  ★ 存活路径：{('、'.join(surv)) if surv else '无——第四章机制增量整体不成立'}", flush=True)
print("="*108, flush=True)
RES["prior_true"]=pi_true; RES["p_learned"]=P_LEARNED
RES["survivors"]=surv
json.dump(RES, open(f"{OUT}/ch4_three_paths.json","w"), ensure_ascii=False, indent=2)
log(f"结果已存 {OUT}/ch4_three_paths.json")
