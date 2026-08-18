# -*- coding: utf-8 -*-
"""第三章 E5：序列长度 L 的敏感性实验（对齐 Dijk 2026 §5.9 训练协议）。

本脚本只跑 E5。E6（攻击类别分面）由 tools/ch3_e6.py 单独承担，它消费冻结的
scores_C11.npy，与本脚本重训出的模型不是同一个实例——两者若都产出分面表会互相矛盾。

模型固定为第三章最终方法 CPA-ELP，即 ch3_full.py 的 C11 格（agg=True, lp=True）：
  机制一 因果前缀聚合：把同一 2-IP 无向对前缀上 h 的均值拼进逐流表示，
      ctx_t = Σ_{i<=t} h_i / Σ_{i<=t} m_i，只用过去，不泄漏未来。
  机制二 实体级可学习 Lp 池化：S_e = (Σ s_f^p / n)^{1/p}，p = exp(p_log) 由
      序列级辅助 BCE 损失驱动学习，训练时以该辅助损失接入，评价时作为实体聚合算子。

订正：ch3_full.py 的文件头把因子 B 写成「实体前缀在线标准化」，与其代码不符。
该文件第 154-166、186-189 行实现的 B 是上述 Lp 辅助损失开关（形参 lp），
没有任何输入标准化分支。冻结脚本不改，此处按代码事实记录，正文以代码为准。

要回答的问题：把同一实体的流切成多长的序列，跨年度性能才最好。
四档 L ∈ {16, 32, 64, 128} × 种子 42/43/44 = 12 次训练。

两处必须成立的公平性约束，否则 L 的效应会被预算差异冒充：
  1. 每档 L 按该 L 重新分块，而不是把 L=128 的块截断到前 L 列。截断会丢掉
     每条实体序列第 L 位之后的全部流，小 L 因此只见到数据的一个偏置子集。
  2. 步数按 steps ∝ n_seq(L) 缩放，保证各档见到的真实流数相同。旧写法固定
     steps × L，恒定的是含填充槽位的算力而非真实流，实测让小 L 多训 1.34~2.13 倍。

锚点：L=128 的分块已实测与 ch3_full.py 所用缓存 I23/M23 逐元素相同，故
L=128 seed=42 必须复现冻结的 C11 结果，脚本以硬断言校验，不复现即中止。
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







# ============ E5 重跑（修正旧版四处设计缺陷）============
# 缺陷 1：[:, :L_use] 截断固定 128 块的前 L_use 位 → 逐流覆盖率≈L/128，小 L 只见数据子集
#    修法：按每个 L 重新分块，断言 seen.all() 恒为 1.0
# 缺陷 2：评价基率随 L 改变，四档 AP 不在同一标尺上
#    修法：覆盖恒为全量后基率恒为 0.0257073138，脚本每档打印核对
# 缺陷 3：等步数下真实流预算差 1.34~2.13 倍，L 效应被预算差冒充
#    修法：steps ∝ n_seq(L)，等 epoch 等真实流
# 缺陷 4：检查点摊到全程 [0.2..1.0]，集成里混入欠训模型，L=128 对不上冻结 C11
#    修法：ck_every 按流位置恒定，L=128 还原 [16000..20000]，并以硬断言校验锚点
import os, json, time as _t
SWAN_WORKSPACE, SWAN_PROJECT = "mortiswang", "malicious-traffic-llm"
CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-e5e6-v2"
os.makedirs(OUT, exist_ok=True)
SEEDS = (42, 43, 44)          # 朱论文不报种子，本章更严格：四档 L 各三种子，报均值与样本标准差
KAPPA, EPS, AUX_W = 5.0, 1e-6, 1.0
EPOCH_STEPS, AVG_LAST = 1000, 5
BASE_L, BASE_STEPS = 128, 20000          # 等流量预算基准：128 × 20000 = 2,560,000 个流位置

NEED = ["X23","y23","X24","y24","s24","d24","cat24"]
C = {n: np.load(f"{CACHE}/{n}.npy", allow_pickle=(n in ("s24","d24","cat24"))) for n in NEED}
X23,y23,X24,y24,s24,d24,cat24 = (C[k] for k in NEED)
log(f"缓存命中：LSPR23 {X23.shape} LSPR24 {X24.shape}")
dev = "cuda" if torch.cuda.is_available() else "cpu"

key24 = np.array([a+"|"+b if a<=b else b+"|"+a for a,b in zip(s24,d24)], object)
_, ent24 = np.unique(key24, return_inverse=True); N24 = int(ent24.max())+1
lab24 = np.zeros(N24, np.float32); np.maximum.at(lab24, ent24, y24)
log(f"目标年实体={N24:,} 正例实体={int(lab24.sum()):,}")

# ---- E5 修法核心：按每个 L 重新分块，而不是截断 ----
# T23.npy 是序列起始时间（长度=序列数），**不能**当逐流时间戳用，形状不匹配。
# 逐流时间戳需单独缓存，缺失时重解析一次 LSPR23。
if not os.path.exists(f"{CACHE}/t23_flow.npy"):
    log("缓存缺 t23_flow（逐流时间戳），重解析 LSPR23 补齐")
    _Xd,_yd,_sd,_dd,_td = load("23")
    np.save(f"{CACHE}/t23_flow.npy", _td.astype(np.float64))
    del _Xd,_yd,_sd,_dd,_td
_t23 = np.load(f"{CACHE}/t23_flow.npy")
_e23 = np.load(f"{CACHE}/ent23.npy")
_t24 = np.load(f"{CACHE}/t24.npy")
def rechunk(ent, ts, Lu):
    order = np.lexsort((ts, ent)); iv = ent[order]
    bnd = np.flatnonzero(np.r_[True, iv[1:] != iv[:-1], True])
    I, M = [], []
    for a, b in zip(bnd[:-1], bnd[1:]):
        seg = order[a:b]
        for i in range(0, len(seg), Lu):
            ch = seg[i:i+Lu]; p = Lu - len(ch)
            I.append(np.r_[ch, np.zeros(p, np.int64)])
            M.append(np.r_[np.ones(len(ch), np.float32), np.zeros(p, np.float32)])
    return np.asarray(I, np.int64), np.asarray(M, np.float32)

assert len(_t23) == len(_e23), f"t23_flow 与 ent23 长度不符：{len(_t23)} vs {len(_e23)}"
log(f"逐流时间戳已载入：LSPR23 {len(_t23):,} 条")

gX23=torch.from_numpy(X23).to(dev); gy23=torch.from_numpy(y23).to(dev)
gX24=torch.from_numpy(X24).to(dev)
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

_pos=torch.tensor([(1-y23.mean())/y23.mean()],device=dev)
_lf=nn.BCEWithLogitsLoss(reduction="none",pos_weight=_pos); _bs=nn.BCELoss(reduction="none")

# rechunk 是 150,680 个实体上的 Python 循环，同一 L 的三个种子结果完全相同。
# 不缓存则 12 次运行要重算 24 遍（训练侧 + 评价侧），小 L 时每遍上百万次 np.r_。
# 纯缓存，不改语义：run_L 只读这两个数组，不写。
_CHUNK_CACHE = {}
def chunks_for(Lu):
    if Lu not in _CHUNK_CACHE:
        _t0 = _t.time()
        _CHUNK_CACHE[Lu] = (rechunk(_e23, _t23, Lu), rechunk(ent24, _t24, Lu))
        log(f"  L={Lu} 分块用时 {_t.time()-_t0:.1f}s（后续种子直接复用）")
    return _CHUNK_CACHE[Lu]

def run_L(Lu, SEED):
    (I23u, M23u), (I24u, M24u) = chunks_for(Lu)
    # 旧写法 steps=BASE_L*BASE_STEPS/Lu 恒定的是「含填充槽位」即算力，不是真实流。
    # 实测 L=128 填充率约 0.47，小 L 填充更少，故旧写法让小 L 多训 1.34~2.13 倍真实流，
    # 偏置方向与结论方向共线。改为 steps ∝ n_seq(L)，即等 epoch、等真实流。
    steps = int(round(BASE_STEPS*len(I23u)/NSEQ_BASE))
    sl=(y23[I23u.reshape(-1)].reshape(I23u.shape)*M23u).max(1)>0
    spw=float((1-sl.mean())/max(sl.mean(),1e-8))
    gI=torch.from_numpy(I23u).to(dev); gM=torch.from_numpy(M23u).to(dev)
    gI4=torch.from_numpy(I24u).to(dev); gM4=torch.from_numpy(M24u).to(dev)
    fill=float(M23u.mean()); real_per_step=BS*len(_e23)/len(I23u)
    log(f"  L={Lu} seed={SEED}: 训练序列 {len(I23u):,} 评价序列 {len(I24u):,} 填充率 {fill:.4f} "
        f"步数 {steps:,} 真实流visits {steps*real_per_step:,.0f} 槽位visits {steps*BS*Lu:,}")
    torch.manual_seed(SEED); np.random.seed(SEED)
    net=Model().to(dev)
    dec=[p for n,p in net.named_parameters() if not(n.endswith(".bias") or n=="p_log")]
    nod=[p for n,p in net.named_parameters() if (n.endswith(".bias") or n=="p_log")]
    opt=torch.optim.AdamW([{"params":dec,"weight_decay":0.01},{"params":nod,"weight_decay":0.0}],lr=2e-3)
    import swanlab
    # 规则要求「创建运行前机械断言工作区与项目名」，故断言在 init 之前，不依赖运行后自省。
    # swanlab 0.9.0 的 Run 无 public 属性（实测公开属性仅 id/name/path/url/dir/config 等），
    # 早前凭记忆写 _sw.public.cloud.project_name，推上服务器后首个 run 即崩。
    assert SWAN_WORKSPACE == "mortiswang" and SWAN_PROJECT == "malicious-traffic-llm", \
        f"SwanLab 目的地未经本轮授权：{SWAN_WORKSPACE}/{SWAN_PROJECT}"
    _cfg = {"L":Lu,"seed":SEED,"steps":steps,"BS":BS,"HID":HID,"lr":2e-3,
            "AUX_W":AUX_W,"AVG_LAST":AVG_LAST,"fill_rate":fill,
            "real_flow_visits":int(steps*real_per_step),"spw":spw,
            "source":"LSPR23","target":"LSPR24","protocol":"zero-shot cross-year"}
    # 首轮实测：seed42 建 run 成功，seed43 建 run 时服务端返回 [Unauthorized]，
    # 而 `swanlab verify` 显示登录态正常——是建 run 的瞬时失败，不是凭据失效。
    # 遥测服务抖一下不该让 12 次训练全部作废，故重试三次；仍失败则降级为本地模式继续训练，
    # 并把降级事实记进结果 JSON，使「这次运行有没有云端记录」可审计，而不是静默丢失。
    _sw, _sw_mode = None, "online"
    for _try in range(3):
        try:
            _sw = swanlab.init(workspace=SWAN_WORKSPACE, project=SWAN_PROJECT,
                               name=f"ch3-E5-L{Lu}-seed{SEED}", mode="online", config=_cfg)
            break
        except Exception as e:
            log(f"  SwanLab 建 run 失败（第 {_try+1}/3 次）：{type(e).__name__}: {e}")
            _t.sleep(10*(_try+1))
    if _sw is None:
        _sw_mode = "local"
        _sw = swanlab.init(project=SWAN_PROJECT, name=f"ch3-E5-L{Lu}-seed{SEED}",
                           mode="local", config=_cfg)
        log(f"  SwanLab 三次建 run 均失败，本次降级为 local 模式，训练照常进行")
    log(f"  SwanLab[{_sw_mode}]: id={_sw.id} name={_sw.name}")
    # 训练与评价整体包进 try/finally：任何断言失败或异常都必须先 finish 掉云端 run，
    # 否则失败的 run 永远停在「运行中」，12 次训练的看板分不清哪几次真正跑完。
    try:
        gen=torch.Generator().manual_seed(SEED); snaps=[]; t0=_t.time()
        _hb = max(1, steps//50)
        # 检查点间隔按「流位置」恒定：L=128 时 = EPOCH_STEPS = 1000，还原 C11 的 [16000..20000]。
        # 旧写法 steps//AVG_LAST 会把检查点摊到全程 [0.2,0.4,0.6,0.8,1.0]，
        # 使集成里混入只训到 20% 的模型，L=128 必然对不上冻结的 C11。
        ck_every=max(1, int(EPOCH_STEPS*BASE_L/Lu))
        ck_every=min(ck_every, max(1, steps//AVG_LAST))
        first_ck=steps-AVG_LAST*ck_every
        # first_ck<=0 时首个检查点会落到训练早期，集成退化为「全程平均」，
        # 与 C11「只平均最后 5 个 epoch」的语义不同，必须中止而不是静默产出。
        assert first_ck > 0, \
            f"L={Lu} 步数 {steps} 放不下 {AVG_LAST} 个间隔 {ck_every} 的末段检查点（first_ck={first_ck}）"
        log(f"  L={Lu} seed={SEED}: 检查点 {[first_ck+ck_every*(i+1) for i in range(AVG_LAST)]}")
        net.train()
        for st in range(steps):
            sel=torch.randint(0,len(I23u),(BS,),generator=gen).to(dev)
            idx=gI[sel]; msk=gM[sel]
            lo=net(gX23[idx.reshape(-1)].reshape(BS,Lu,D),msk)
            yb=gy23[idx.reshape(-1)].reshape(BS,Lu)
            loss=(_lf(lo,yb)*msk).sum()/msk.sum().clamp(min=1)
            sq=lp_pool(torch.sigmoid(lo),msk,net.p).clamp(1e-6,1-1e-6); ysq=(yb*msk).amax(1)
            w=1.0+(spw-1.0)*ysq; loss=loss+AUX_W*((_bs(sq,ysq)*w).sum()/w.sum())
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(),1.0); opt.step()
            if (st+1) % _hb == 0:
                _el=_t.time()-t0
                # detach 后再取标量：直接 float(带梯度张量) 会触发 PyTorch UserWarning，
                # 每次心跳刷一行，把真正的进度信息淹没在警告里。
                swanlab.log({"train/loss":float(loss.detach()),"train/p":float(net.p.detach()),
                             "train/throughput_steps_per_s":(st+1)/max(_el,1e-9)}, step=st+1)
            if st+1>first_ck and (st+1-first_ck)%ck_every==0 and len(snaps)<AVG_LAST:
                snaps.append({k:v.detach().clone() for k,v in net.state_dict().items()})
        assert len(snaps)==AVG_LAST, f"L={Lu} seed={SEED} 检查点数 {len(snaps)} != {AVG_LAST}"
        ps=[]; acc=None; seen=None
        with torch.no_grad():
            for sd in snaps:
                net.load_state_dict(sd); net.eval(); ps.append(net.p.item())
                sc=torch.zeros(len(y24),device=dev); sn=torch.zeros(len(y24),dtype=torch.bool,device=dev)
                for a in range(0,len(I24u),2048):
                    idx=gI4[a:a+2048]; msk=gM4[a:a+2048]; b=idx.shape[0]
                    pr=torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b,Lu,D),msk))
                    fi=idx.reshape(-1); fm=msk.reshape(-1)>0
                    sc[fi[fm]]=pr.reshape(-1)[fm]; sn[fi[fm]]=True
                s_=sc.cpu().numpy(); n_=sn.cpu().numpy()
                acc=s_ if acc is None else acc+s_; seen=n_ if seen is None else (seen|n_)
        net.train()
        sc=acc/len(snaps); p_=float(np.mean(ps))
        assert seen.all(), f"L={Lu} seed={SEED} 逐流覆盖不全：{seen.mean():.6f}（修法要求恒为 1.0）"
        fap=average_precision_score(y24,sc)
        # 实体聚合必须逐字复刻 ch3_full.py:221-225 的 ent_ap(p=...)，包括最后的 float32 转换。
        # 实测：只把 float32 改成 float64，逐流 AP 仍逐位一致（Δ3.9e-07），实体 AP 却差 1.03e-03，
        # 因为 float32 舍入会改变 47,115 个实体中近邻分数的排序，而正例只有 752 个，
        # 头部几次顺序翻转就够把 AP 推动 1e-3。两者都不算错，但不是同一个估计量，
        # 第三章其余实体 AP 全部是 float32 口径，此处不对齐则 E5 那一列与全章不可比。
        num=np.zeros(N24,np.float64); cnt=np.zeros(N24,np.float64)
        np.add.at(num,ent24,np.clip(sc,1e-7,1.0).astype(np.float64)**p_); np.add.at(cnt,ent24,1.0)
        es=np.where(cnt>0,(num/np.maximum(cnt,1))**(1.0/p_),-np.inf).astype(np.float32)
        ok=np.isfinite(es)
        assert ok.all(), f"L={Lu} seed={SEED} 有 {int((~ok).sum())} 个实体无分数，覆盖断言应已拦截"
        eap=average_precision_score(lab24[ok],es[ok])
        swanlab.log({"target/flow_ap":fap,"target/entity_ap":eap,"target/p_learned":p_})
        log(f"  L={Lu} seed={SEED}: 覆盖={seen.mean():.6f} 评价基率={y24.mean():.10f} 逐流AP={fap:.6f} 实体AP={eap:.6f} p={p_:.4f} 用时{(_t.time()-t0)/60:.1f}分")
        return {"L":Lu,"seed":SEED,"steps":steps,"fill_rate":fill,"real_flow_visits":steps*real_per_step,
                "slot_visits":steps*BS*Lu,"seq_pos_rate":float(sl.mean()),"spw":spw,
                "n_seq_tr":len(I23u),"n_seq_ev":len(I24u),"swanlab_mode":_sw_mode,"swanlab_id":_sw.id,
                "coverage":float(seen.mean()),"eval_prior":float(y24.mean()),"fap":fap,"eap":eap,"p":p_}
    finally:
        _sw.finish()

NSEQ_BASE = len(chunks_for(BASE_L)[0][0])   # 走缓存，L=128 的分块只算一次
log(f"等真实流预算基准：L={BASE_L} 的序列数 = {NSEQ_BASE:,}，各 L 步数按 n_seq(L) 等比缩放")
log("="*92); log("E5 重跑：按每个 L 重新分块 + 等真实流预算 + 覆盖率断言 + 检查点对齐 C11")
# L=128 放在最前面：它是对齐冻结 C11 的锚点，一旦对不上，说明分块、步数或检查点
# 有一处退化，此时应当立刻中止，而不是白跑完剩下 11 次训练再发现整张表不可信。
ANCHOR = {"fap": 0.231571, "eap": 0.462988, "p": 1.2236}
E5=[]
for Lu in (128,16,32,64):
    for _sd in SEEDS:
        r = run_L(Lu,_sd); E5.append(r)
        if Lu==BASE_L and _sd==42:
            d=(abs(r["fap"]-ANCHOR["fap"]), abs(r["eap"]-ANCHOR["eap"]), abs(r["p"]-ANCHOR["p"]))
            log(f"  锚点校验 L=128 seed=42 vs 冻结 C11："
                f"逐流AP {r['fap']:.6f}/{ANCHOR['fap']:.6f}(Δ{d[0]:.2e}) "
                f"实体AP {r['eap']:.6f}/{ANCHOR['eap']:.6f}(Δ{d[1]:.2e}) "
                f"p {r['p']:.4f}/{ANCHOR['p']:.4f}(Δ{d[2]:.2e})")
            # 分块已实测与 ch3_full 所用缓存 I23/M23 逐元素相同，训练流、检查点与实体聚合
            # （含 float32 转换）也已逐字还原，故差异只应来自评价分批的浮点重结合。
            # 首轮实测逐流 AP Δ=3.9e-07，容差取 1e-4 已留三个数量级余量，
            # 足以捕获「检查点摊到全程」「按列截断代替重新分块」这类会把 AP 推动 0.05 以上的退化。
            assert all(x < 1e-4 for x in d[:2]) and d[2] < 1e-2, \
                f"L=128 seed=42 未复现冻结 C11，Δ={d}；分块/步数/检查点/实体聚合存在退化，本表不可信"
print("\n"+"="*92, flush=True)
import statistics as _st
print(f"{'L':>5}{'填充率':>9}{'步数':>9}{'真实流visits':>15}{'逐流AP 三种子':>34}{'均值':>10}{'标准差':>10}{'实体AP均值':>12}", flush=True)
for Lu in (16,32,64,128):
    g=[r for r in E5 if r["L"]==Lu]; f=[r["fap"] for r in g]; e=[r["eap"] for r in g]
    print(f"{Lu:>5}{g[0]['fill_rate']:>9.4f}{g[0]['steps']:>9,}{g[0]['real_flow_visits']:>15,.0f}"
          f"{'/'.join(f'{x:.6f}' for x in f):>34}{_st.mean(f):>10.6f}{_st.stdev(f):>10.6f}{_st.mean(e):>12.6f}", flush=True)
# 是否允许按 L 排序，用单因素方差分析裁决，不用「跨度 > 2σ」这类启发式。
# 该启发式在四组各三种子的构造上实测假阳性率约 23%，即近四分之一的纯噪声数据
# 会被判成「跨度超噪声，可比较」，据此排序会把随机波动写成 L 的效应。
from scipy import stats as _ss
_stat = {}
for _key, _name in (("fap","逐流AP"), ("eap","实体AP")):
    _groups = [[r[_key] for r in E5 if r["L"]==L] for L in (16,32,64,128)]
    _F, _p = _ss.f_oneway(*_groups)
    _means = [_st.mean(g) for g in _groups]
    _stat[_key] = {"F":float(_F), "p":float(_p), "means":_means,
                   "range":max(_means)-min(_means),
                   "pooled_sd":float(_st.median([_st.stdev(g) for g in _groups]))}
    print(f"  {_name}：F(3,8)={_F:.3f}  p={_p:.4f}  四档均值跨度={max(_means)-min(_means):.6f}  "
          f"{'p<0.05，L 的效应可报' if _p < 0.05 else 'p>=0.05，本节不对 L 排序，只报各档数值'}", flush=True)
print("  判据在实验前固定：p<0.05 才允许陈述 L 之间的优劣，否则只陈述「四档差异未达显著」。", flush=True)
print("  三种子仅 df=(3,8)，检出力很低；未达显著只说明本预算下证据不足，不等于四档确实相同。", flush=True)
print("  覆盖率恒为 1.0000、评价基率恒为 0.0257073138、真实流预算已按 n_seq(L) 对齐。", flush=True)
print("  注意：随 L 变化的还有序列级正类率与辅助损失权重 spw，本节 L 效应是三者复合。", flush=True)

json.dump({"E5":E5,"anova":_stat}, open(f"{OUT}/e5_v2.json","w"), ensure_ascii=False, indent=2)
log(f"结果已存 {OUT}/e5_v2.json")
log("E6（攻击类别分面）不在本脚本内：它由 tools/ch3_e6.py 消费冻结的 scores_C11.npy，与此处重训的模型不是同一实例，两处都产表会互相矛盾。")
