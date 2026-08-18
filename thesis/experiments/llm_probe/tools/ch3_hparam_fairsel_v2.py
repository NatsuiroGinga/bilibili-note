# -*- coding: utf-8 -*-
"""第三章 CPA-ELP：统一「top-5 预测平均」检查点策略下的 24 配置超参搜索 + 2x2 四格重跑。

本脚本在 tools/ch3_hparam_fairsel.py 的基础上改，不重写：分块、切分、步数缩放、训练循环、
评价口径全部保持逐字一致（L=128/AUX_W=1.0/HID=192 复现既有 ch3_2x2_fairsel C11 的逐 epoch
验证曲线，脚本内以硬断言校验，容差 1e-4）。

============================ 相对 v1 的唯一实质修正 ============================
v1 把「top-5」实现成了**权重平均**（state_dict 逐参数算术平均后再推理一次）。
这与冻结脚本 tools/ch3_full.py 第 196-210 行实际做的事不同——那里做的是**预测平均**：

    for sd_ in snaps:            # 逐个载入检查点
        net.load_state_dict(sd_) # 各自推理一遍
        acc = acc + s_           # 累加预测分数
    return acc/len(snaps)        # 平均预测
    p = np.mean(ps)              # p 取算术均值

本脚本改回预测平均：对验证 AP 前 5 名 epoch 的检查点**各自推理一遍再平均预测分数**；
报告的 p 取 5 份的**算术均值**（权重空间平均 p_log 再取指数会得到几何均值，不采用）。
k=5 事前固定，不得按结果调整，不得在 argmax / 权重平均 / 预测平均之间比较后择优——
选择只读 val_ap_pred_avg 这一个字段；权重平均值仅作跨度对比的诊断量落盘，不进入排序。
==============================================================================

============================ 两组实验 ============================
第一组 24 配置超参搜索（只跑 C11 格 agg=True, lp=True）
  事前声明的搜索空间：L∈{32,64,128} × AUX_W∈{0.25,0.5,1.0,2.0} × HID∈{192,384}，不得扩大。
  第一级：每个配置内部取验证 AP 前 5 名 epoch，做预测平均，得到该配置的代表分数。
  第二级：24 个配置之间按「其 top-5 预测平均模型在 LSPR23 验证集上的 AP」排序，取唯一胜者。
  两级选择都只用 LSPR23 实体不相交验证集。LSPR24 只对最终选出的那一个配置评价一次。

第二组 2x2 四格重跑（C00/C01/C10/C11），超参固定 L=128 / AUX_W=1.0 / HID=192，本组不调参。
  四格定义逐字取 ch3_full.py 第 154-166、186-189 行的 Model(agg, lp)：
    agg=True  用因果前缀均值 ctx=cumsum(h)/cumsum(m)；agg=False 时 ctx 填零向量（容量相同）。
    lp=True   训练损失加序列级 Lp 池化辅助 BCE；lp=False 不加。
  重跑理由：既有 2x2 用的是单 epoch argmax，与本轮 top-5 预测平均不是同一策略。
  全章必须用同一套检查点策略，否则主表与消融表不可比。

============================ LSPR24 隔离的机械保证 ============================
  guarded_load()  ：所有 np.load 的唯一入口。名字里含 "24" 且 SELECTION_FROZEN 为假时断言失败。
  阶段闸门        ：28 次训练全部完成、24 配置选出唯一胜者后，先把选择结果写盘，再置 True。
  load24()        ：首行断言 SELECTION_FROZEN，_N24_LOADS 加一，最终必须 == 1。
  score24()       ：首行断言 SELECTION_FROZEN，_EVAL24_CALLS 加一，最终必须 == 5
                    （第一组胜者 1 次 + 第二组四格 4 次），并逐次记录是哪一组的哪个配置。
  train_and_select() / val_ap() / val_scores() / select_winner() 函数体内不出现任何
  LSPR24 标识符；调用它们时进程内也没有 LSPR24 数据。
==============================================================================

评价口径逐字复刻 ch3_full.py：实体构造第 130-133 行、ent_ap 第 213-225 行
（Lp 聚合含末尾 .astype(np.float32)）、dr_at_fpr 第 236-240 行。机制的数学形式一律不改。
不创建 SwanLab 运行身份。只保存最终选中配置与四格 C11 的逐流分数，其余不落盘。
"""

import json
import os
import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, roc_auc_score

T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:8.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
XGBD = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-xgb-entity"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-hparam-fairsel-v2"
os.makedirs(OUT, exist_ok=True)

# ================= 事前声明的搜索空间：24 个配置，运行开始后不得扩大或改序 =================
GRID_L = (32, 64, 128)
GRID_AUXW = (0.25, 0.5, 1.0, 2.0)
GRID_HID = (192, 384)
CONFIGS = [{"idx": i, "L": l, "AUX_W": a, "HID": h, "name": f"L{l}-AUXW{a}-HID{h}"}
           for i, (l, a, h) in enumerate((l, a, h) for l in GRID_L
                                         for a in GRID_AUXW for h in GRID_HID)]
assert len(CONFIGS) == 24, f"搜索空间应为 24 个配置，实为 {len(CONFIGS)}"
# 执行顺序把 L=128 排在最前，与上面的「声明顺序」相互独立：
# 2x2 的 C11 格（L=128 / AUX_W=1.0 / HID=192）与既有 ch3_2x2_fairsel C11 是同一个训练，
# 先跑它，一旦分块、切分、步数缩放或训练流退化，七分钟内被锚点断言拦住，而不是跑满两小时才发现。
# 并列裁决只用声明顺序 CONFIGS[i]["idx"]，与执行顺序无关。
EXEC_L_ORDER = (128, 64, 32)

# ---- 第二组：2x2 四格。C11 排最前，用它做锚点校验；四格定义见 ch3_full.py 第 244 行 ----
CELL_L, CELL_AUXW, CELL_HID = 128, 1.0, 192
CELLS = [("C11", True, True), ("C00", False, False), ("C01", False, True), ("C10", True, False)]

# ---- 其余设定：照抄 ch3_2x2_fairsel.py / ch3_full.py，不调 ----
SEED, BS, LR, DP = 42, 64, 2e-3, 0.1
EPOCH_STEPS = 1000
BASE_L, BASE_EPOCH = 128, 20          # L=128 对应 20 epoch × 1000 步 = 20000 步
TOPK = 5                              # 事前固定的检查点个数
VAL_FRAC, TIME_TAIL = 0.10, 0.15      # 切分参数照抄 ch3_2x2_fairsel 第 54 行
TIE_EPS = 1e-5                        # 验证 AP 并列判定阈值

# ---- 对照基准（外部给定常数，不参与任何选择）----
XGB_REF = {"e_lp_at_p1p056": 0.533104, "e_max": 0.512899, "dr_max": 0.692819, "fap": 0.222391}
# 既有 2x2（单 epoch argmax 协议，tools/ch3_2x2_fairsel.py）的四格数字，只作对比参照
ARGMAX_2X2 = {
    "C00": {"fap": 0.382100, "e_max": 0.334994, "e_lp": 0.334994, "dr_main": 0.683511,
            "dr_max": 0.683511, "sel_epoch": 14, "p": 2.0000},
    "C01": {"fap": 0.299701, "e_max": 0.305702, "e_lp": 0.408513, "dr_main": 0.777926,
            "dr_max": 0.712766, "sel_epoch": 14, "p": 0.5233},
    "C10": {"fap": 0.402103, "e_max": 0.385970, "e_lp": 0.385970, "dr_main": 0.722074,
            "dr_max": 0.722074, "sel_epoch": 19, "p": 2.0000},
    "C11": {"fap": 0.291843, "e_max": 0.291739, "e_lp": 0.518350, "dr_main": 0.703457,
            "dr_max": 0.714096, "sel_epoch": 10, "p": 1.0562}}
# 既有 ch3_2x2_fairsel C11（L=128, AUX_W=1.0, HID=192, seed 42）的逐 epoch 验证 AP，
# 取自服务器 ch3-2x2-fairsel/selection_frozen.json。本脚本必须逐 epoch 复现它。
ANCHOR_VAL_AP = [
    0.9940881852537848, 0.9951702097178784, 0.9941451939007750, 0.9974822236379134,
    0.9986953443771412, 0.9993982197475862, 0.9983241878694655, 0.9984883053304557,
    0.9995490855535429, 0.9997422904785787, 0.9993566776851756, 0.9987991163538222,
    0.9995882257540040, 0.9989801167851958, 0.9993629271578841, 0.9986831067482045,
    0.9995602120158671, 0.9961684807109266, 0.9987698054147961, 0.9990249114903877]
ANCHOR_TOL = 1e-4

# ---- 阶段闸门与计数器 ----
SELECTION_FROZEN = False
_N24_LOADS = 0
_EVAL24_CALLS = 0
_EVAL24_LEDGER = []


def guarded_load(name, allow_pickle=False):
    """所有 np.load 的唯一入口。选择阶段禁止读入任何名字含 '24' 的数组。"""
    assert SELECTION_FROZEN or "24" not in name, \
        f"阶段闸门未开：选择阶段禁止读入 {name}.npy"
    return np.load(f"{CACHE}/{name}.npy", allow_pickle=allow_pickle)


# =====================================================================================
# 阶段一：只读入 LSPR23
# =====================================================================================
log("=" * 112)
log("阶段一 选择：只读入 LSPR23，LSPR24 不进入本进程")
X23 = guarded_load("X23")
y23 = guarded_load("y23")
e23f = guarded_load("ent23")            # 逐流实体 id
t23f = guarded_load("t23_flow")         # 逐流时间戳
I23c = guarded_load("I23")              # L=128 冻结分块，仅作复现锚点
M23c = guarded_load("M23")
E23c = guarded_load("E23")              # L=128 冻结的逐序列实体
T23c = guarded_load("T23")              # L=128 冻结的逐序列起始时间
D = X23.shape[1]
assert D == 83, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {D}"
assert len(e23f) == len(t23f) == len(y23) == len(X23)
log(f"LSPR23 流={len(y23):,} 特征数={D} L=128 冻结序列={len(I23c):,}")

dev = "cuda" if torch.cuda.is_available() else "cpu"
assert dev == "cuda", "本任务必须在 GPU 上运行"
log(f"torch {torch.__version__} | {torch.cuda.get_device_name(0)}")

# ---- 分块：按实体 lexsort((ts, ent)) 排序后每 L 条切一段，不足补零并用 mask 标记 ----
_ORD = np.lexsort((t23f, e23f))
_IV = e23f[_ORD]
_BND = np.flatnonzero(np.r_[True, _IV[1:] != _IV[:-1], True])
_SEGLEN = np.diff(_BND)
del _IV
log(f"LSPR23 实体段已建：{len(_SEGLEN):,} 个实体，最长 {_SEGLEN.max():,} 条流")


def rechunk23(Lu):
    """向量化分块，语义与 tools/ch3_e5e6.py rechunk() 相同（填充索引 0、mask 0）。
    L=128 的结果与冻结缓存 I23/M23 逐元素相同，脚本内以硬断言校验。"""
    nch = -(-_SEGLEN // Lu)
    n = int(nch.sum())
    off = np.repeat(np.cumsum(nch) - nch, nch)
    starts = np.repeat(_BND[:-1], nch) + (np.arange(n) - off) * Lu
    ends = np.repeat(_BND[1:], nch)
    real = np.minimum(Lu, ends - starts)
    col = np.arange(Lu)
    Mb = col[None, :] < real[:, None]
    pos = np.minimum(starts[:, None] + col[None, :], len(_ORD) - 1)
    Iu = np.where(Mb, _ORD[pos], 0).astype(np.int64)
    return Iu, Mb.astype(np.float32), starts


# ---- 验证实体集合：逐字复用 ch3_2x2_fairsel.py 第 80-83 行，与 L 无关 ----
_rs = np.random.RandomState(SEED)
_uent = np.unique(E23c)
assert np.array_equal(_uent, np.unique(e23f)), "逐流实体集合与冻结序列实体集合不一致"
_perm = _rs.permutation(len(_uent))
VAL_ENT = set(_uent[_perm[:max(1, int(len(_uent) * VAL_FRAC))]].tolist())
assert len(_uent) == 150680, f"LSPR23 实体数自检失败：{len(_uent)}"
log(f"LSPR23 实体 {len(_uent):,}，验证实体 {len(VAL_ENT):,}（RandomState(42) 排列，与 L 无关）")


def split_for(EL, TL):
    """逐字复用 ch3_2x2_fairsel.py 第 84-90 行的切分逻辑，只把 E23/T23 换成该 L 的逐序列版本。"""
    m_ent = np.fromiter((e in VAL_ENT for e in EL), bool, len(EL))    # 实体不相交
    t_cut = np.quantile(TL, 1.0 - TIME_TAIL)
    m_time = TL >= t_cut                                              # 时间尾部（不作选择信号）
    tr_idx = np.flatnonzero(~(m_ent | m_time))                        # 训练区：两者都排除
    val_idx = np.flatnonzero(m_ent & ~m_time)                         # 唯一选择信号的来源
    assert len(np.intersect1d(val_idx, tr_idx)) == 0, "验证集与训练区有交叠"
    return tr_idx, val_idx


# ---- 逐 L 预备：分块、切分、步数、序列级正类权重 ----
PREP = {}
for Lu in sorted(set(GRID_L)):
    _t0 = time.time()
    Iu, Mu, st = rechunk23(Lu)
    EL, TL = e23f[_ORD[st]], t23f[_ORD[st]]
    tr_idx, val_idx = split_for(EL, TL)
    sl = (y23[Iu.reshape(-1)].reshape(Iu.shape) * Mu).max(1) > 0
    spw = float((1 - sl.mean()) / max(sl.mean(), 1e-8))
    PREP[Lu] = {"I": Iu, "M": Mu, "tr": tr_idx, "val": val_idx, "spw": spw,
                "n_seq": len(Iu), "fill": float(Mu.mean()), "seq_pos_rate": float(sl.mean())}
    log(f"  L={Lu:>3} 分块 {len(Iu):,} 序列 填充率 {Mu.mean():.4f} | 训练 {len(tr_idx):,} "
        f"验证 {len(val_idx):,} | 序列级正类率 {sl.mean():.6f} spw={spw:.4f} | {time.time()-_t0:.1f}s")
    del sl
    if Lu == BASE_L:
        assert np.array_equal(Iu, I23c), "L=128 分块与冻结缓存 I23 不一致"
        assert np.array_equal(Mu, M23c), "L=128 分块与冻结缓存 M23 不一致"
        assert np.array_equal(EL, E23c), "L=128 逐序列实体与冻结缓存 E23 不一致"
        assert np.array_equal(TL, T23c), "L=128 逐序列时间与冻结缓存 T23 不一致"
        assert len(tr_idx) == 208598, f"L=128 训练序列数自检失败：{len(tr_idx)}"
        assert len(val_idx) == 22444, f"L=128 验证序列数自检失败：{len(val_idx)}"
        log("  L=128 分块/切分自检通过：与 ch3_2x2_fairsel 逐元素一致，208,598 训练 / 22,444 验证")

del I23c, M23c, E23c, T23c

# ---- 步数按 steps ∝ n_train_seq(L) 缩放，保证各 L 见到相同的真实流数 ----
_base_tr = len(PREP[BASE_L]["tr"])
for Lu in PREP:
    tgt = BASE_EPOCH * EPOCH_STEPS * len(PREP[Lu]["tr"]) / _base_tr
    PREP[Lu]["n_epoch"] = max(1, int(round(tgt / EPOCH_STEPS)))
    PREP[Lu]["steps"] = PREP[Lu]["n_epoch"] * EPOCH_STEPS
    PREP[Lu]["real_flow_visits"] = PREP[Lu]["steps"] * BS * len(y23) / PREP[Lu]["n_seq"]
_v = [PREP[L]["real_flow_visits"] for L in PREP]
log("步数缩放（∝ 训练序列数）：" + "  ".join(
    f"L={L}:{PREP[L]['n_epoch']}轮/{PREP[L]['steps']:,}步/真实流visits {PREP[L]['real_flow_visits']:,.0f}"
    for L in sorted(PREP)))
log(f"  各 L 真实流访问数极差 {(max(_v)-min(_v))/np.mean(_v)*100:.3f}%（整轮取整所致）")
assert PREP[128]["n_epoch"] == 20 and PREP[64]["n_epoch"] == 29 and PREP[32]["n_epoch"] == 48, \
    "步数缩放与上一轮已算好的 20/29/48 轮不一致"

# ---- 上卡：LSPR23 特征与标签常驻，分块矩阵按 L 分块换入换出 ----
gX23 = torch.from_numpy(X23).to(dev)
gy23 = torch.from_numpy(y23).to(dev)
log(f"LSPR23 特征已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


# ---- 模型与损失：逐字照抄 ch3_full.py 第 150-172 行 ----
def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p * ls).masked_fill(m < 0.5, -1e30), 1) - torch.log(n)) / p)


class Model(nn.Module):
    def __init__(self, agg, lp, hid=192, dp=DP):
        super().__init__(); self.agg, self.lp = agg, lp
        self.f = nn.Sequential(nn.Linear(D, hid), nn.ReLU(), nn.Dropout(dp))
        self.g = nn.Sequential(nn.Linear(hid * 2, hid), nn.ReLU(), nn.Dropout(dp))
        self.o = nn.Linear(hid, 1); self.p_log = nn.Parameter(torch.tensor(float(np.log(2.0))))

    @property
    def p(self): return torch.exp(self.p_log).clamp(1e-3, 1e3)

    def forward(self, x, m):
        h = self.f(x) * m.unsqueeze(-1)
        c = ((torch.cumsum(h, 1) / torch.cumsum(m, 1).clamp(min=1.0).unsqueeze(-1)) * m.unsqueeze(-1)
             if self.agg else torch.zeros_like(h))
        return self.o(self.g(torch.cat([h, c], -1))).squeeze(-1)


_pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=_pos)
_bs = nn.BCELoss(reduction="none")
log(f"逐流 pos_weight={_pos.item():.6f}（口径照抄 ch3_full，用全量 LSPR23）")


@torch.no_grad()
def val_scores(net, gI, gM, gval, Lu):
    """LSPR23 实体不相交验证集上的逐流预测分数与标签（顺序对所有检查点一致，可逐元素平均）。

    本函数是唯一的模型选择信号来源，只触碰 gX23/gy23/gI/gM/gval。
    """
    was_training = net.training
    net.eval(); P = []; Y = []
    for a in range(0, len(gval), 2048):
        sel = gval[a:a + 2048]; idx = gI[sel]; msk = gM[sel]; b = idx.shape[0]
        lo = net(gX23[idx.reshape(-1)].reshape(b, Lu, D), msk)
        fm = msk.reshape(-1) > 0
        P.append(torch.sigmoid(lo).reshape(-1)[fm].cpu().numpy())
        Y.append(gy23[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
    if was_training:
        net.train()
    return np.concatenate(P), np.concatenate(Y)


def val_ap(net, gI, gM, gval, Lu):
    """单检查点的验证逐流 AP，照抄 ch3_2x2_fairsel.val_ap()。"""
    P, Y = val_scores(net, gI, gM, gval, Lu)
    assert Y.max() > 0, "验证集无正例，选择信号无效"
    return float(average_precision_score(Y, P))


def train_and_select(name, agg, lp, hid, aux_w, gI, gM, gtr, gval, Lu, n_epoch, spw):
    """训练满 n_epoch 不早停，逐 epoch 记录验证 AP，取前 TOPK 名 epoch 做**预测平均**。

    返回的 val_ap_pred_avg 是该配置的唯一代表分数（第二级选择只读它）。
    val_ap_weight_avg 只是跨度对比用的诊断量，不参与任何排序或裁决。
    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = Model(agg, lp, hid).to(dev)
    dec = [p for n, p in net.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    nod = [p for n, p in net.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    opt = torch.optim.AdamW([{"params": dec, "weight_decay": 0.01},
                             {"params": nod, "weight_decay": 0.0}], lr=LR)
    gen = torch.Generator().manual_seed(SEED)
    hist, snaps = [], []
    t0 = time.time()
    net.train()
    for ep in range(1, n_epoch + 1):
        for _ in range(EPOCH_STEPS):
            sel = gtr[torch.randint(0, len(gtr), (BS,), generator=gen).to(dev)]
            idx = gI[sel]; msk = gM[sel]
            xb = gX23[idx.reshape(-1)].reshape(BS, Lu, D)
            yb = gy23[idx.reshape(-1)].reshape(BS, Lu)
            lo = net(xb, msk); loss = (_lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
            if lp:
                sq = lp_pool(torch.sigmoid(lo), msk, net.p).clamp(1e-6, 1 - 1e-6)
                ysq = (yb * msk).amax(1)
                w = 1.0 + (spw - 1.0) * ysq
                loss = loss + aux_w * ((_bs(sq, ysq) * w).sum() / w.sum())
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        v = val_ap(net, gI, gM, gval, Lu)
        hist.append([ep, v, net.p.item()])
        snaps.append({k: t.detach().cpu().clone() for k, t in net.state_dict().items()})
        if ep % 5 == 0 or ep == n_epoch or ep == 1:
            log(f"    {name} ep {ep:>2}/{n_epoch} 验证AP={v:.6f} p={net.p.item():.4f} "
                f"累计{(time.time()-t0)/60:.1f}分")
    tr_t = time.time() - t0

    # ---- top-5 预测平均：k 事前固定，排序键 (-验证AP, epoch)，同分取更早的 epoch ----
    rank = sorted(range(n_epoch), key=lambda i: (-hist[i][1], hist[i][0]))
    top = sorted(rank[:TOPK])
    top_states = [snaps[i] for i in top]
    Pacc, Yv, ps = None, None, []
    for sd_ in top_states:
        net.load_state_dict({k: v.to(dev) for k, v in sd_.items()})
        net.eval()
        ps.append(net.p.item())
        P_, Y_ = val_scores(net, gI, gM, gval, Lu)
        Pacc = P_ if Pacc is None else Pacc + P_
        Yv = Y_ if Yv is None else Yv
    P_avg = Pacc / len(top_states)
    assert Yv.max() > 0, "验证集无正例，选择信号无效"
    v_pred = float(average_precision_score(Yv, P_avg))
    p_pred = float(np.mean(ps))          # 预测平均的 p：算术均值

    # ---- 诊断量：top-5 权重平均（v1 的旧做法），只为回答「跨度变大还是变小」，不参与选择 ----
    wavg = {k: torch.stack([sd_[k] for sd_ in top_states], 0).mean(0) for k in top_states[0]}
    net.load_state_dict({k: v.to(dev) for k, v in wavg.items()})
    v_wavg = val_ap(net, gI, gM, gval, Lu)
    p_wavg = net.p.item()                # 权重空间平均 p_log 再取指数 = 几何均值

    top_info = [[hist[i][0], hist[i][1]] for i in top]
    npar = sum(p.numel() for p in net.parameters())
    log(f"  {name} 训练 {tr_t/60:.2f} 分 | top{TOPK} epoch={[t[0] for t in top_info]} "
        f"验证AP={['%.6f' % t[1] for t in top_info]}")
    log(f"  {name} → top{TOPK} 预测平均 验证AP={v_pred:.6f} p(算术均值)={p_pred:.4f} ｜ "
        f"[诊断] 权重平均 验证AP={v_wavg:.6f} p(几何均值)={p_wavg:.4f} ｜ "
        f"逐epoch argmax {max(h[1] for h in hist):.6f} @ep{max(hist, key=lambda h: h[1])[0]}")
    out = {"name": name, "agg": agg, "lp": lp, "L": Lu, "AUX_W": aux_w, "HID": hid,
           "n_epoch": n_epoch, "steps": n_epoch * EPOCH_STEPS, "spw": spw,
           "val_ap_history": hist, "topk_epochs": [t[0] for t in top_info],
           "topk_val_aps": [t[1] for t in top_info], "topk_ps": ps,
           "val_ap_pred_avg": v_pred, "p_pred_avg": p_pred,
           "val_ap_weight_avg": v_wavg, "p_weight_avg": p_wavg,
           "val_ap_argmax": max(h[1] for h in hist),
           "argmax_epoch": max(hist, key=lambda h: h[1])[0],
           "train_seconds": tr_t, "npar": npar,
           "peak_gib": torch.cuda.max_memory_allocated() / 2 ** 30}
    return out, top_states


def anchor_check(name, r):
    d = [abs(r["val_ap_history"][i][1] - ANCHOR_VAL_AP[i]) for i in range(BASE_EPOCH)]
    log(f"  ★ 锚点校验 {name} vs ch3_2x2_fairsel C11：逐 epoch 验证 AP 最大绝对差 {max(d):.3e}"
        f"（容差 {ANCHOR_TOL:.0e}），argmax epoch {r['argmax_epoch']}（冻结记录为 10）")
    assert max(d) < ANCHOR_TOL, \
        f"{name} 未复现既有 C11 验证曲线，最大差 {max(d):.3e}；分块、切分、步数或训练流存在退化，本表不可信"


RES, TOPW = {}, {}          # 第一组：24 配置
CELLRES, CELLW = {}, {}     # 第二组：2x2 四格
log("=" * 112)
log(f"两组共 {len(CONFIGS)+len(CELLS)} 次训练，进程内串行，seed={SEED}，不早停，无学习率调度器")
log(f"检查点策略：验证 AP 前 {TOPK} 名 epoch 的检查点各自推理后**平均预测分数**；p 取 {TOPK} 份算术均值")

for Lu in EXEC_L_ORDER:
    pr = PREP[Lu]
    gI = torch.from_numpy(pr["I"]).to(dev)
    gM = torch.from_numpy(pr["M"]).to(dev)
    gtr = torch.from_numpy(pr["tr"]).to(dev)
    gval = torch.from_numpy(pr["val"]).to(dev)
    log("-" * 112)
    log(f"L={Lu} 块：{pr['n_epoch']} 轮 × {EPOCH_STEPS} 步，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

    if Lu == CELL_L:
        log(f"### 第二组 2x2 四格重跑（L={CELL_L}, AUX_W={CELL_AUXW}, HID={CELL_HID}），C11 排首位做锚点 ###")
        for cid, agg, lp in CELLS:
            torch.cuda.reset_peak_memory_stats()
            r, w = train_and_select(f"2x2-{cid}", agg, lp, CELL_HID, CELL_AUXW,
                                    gI, gM, gtr, gval, Lu, pr["n_epoch"], pr["spw"])
            r["cell"] = cid
            CELLRES[cid] = r; CELLW[cid] = w
            if cid == "C11":
                anchor_check(f"2x2-{cid}", r)
        log("### 第二组四格训练完成，转入第一组 24 配置搜索 ###")

    for cfg in [c for c in CONFIGS if c["L"] == Lu]:
        torch.cuda.reset_peak_memory_stats()
        r, w = train_and_select(cfg["name"], True, True, cfg["HID"], cfg["AUX_W"],
                                gI, gM, gtr, gval, Lu, pr["n_epoch"], pr["spw"])
        r["idx"] = cfg["idx"]
        RES[cfg["idx"]] = r; TOPW[cfg["idx"]] = w
        if Lu == BASE_L and cfg["AUX_W"] == CELL_AUXW and cfg["HID"] == CELL_HID:
            anchor_check(cfg["name"], r)
            _dd = max(abs(r["val_ap_history"][i][1] - CELLRES["C11"]["val_ap_history"][i][1])
                      for i in range(BASE_EPOCH))
            log(f"  ★ 同参一致性：{cfg['name']} 与 2x2-C11 是同一训练，逐 epoch 验证 AP 最大差 {_dd:.3e}")
            assert _dd < ANCHOR_TOL, f"同参两次训练不一致，最大差 {_dd:.3e}"

    del gI, gM, gtr, gval
    torch.cuda.empty_cache()

# =====================================================================================
# 选择：两级都只用 LSPR23 验证集；第二级只读 val_ap_pred_avg
# =====================================================================================
log("=" * 112)
ORDER = sorted(RES.values(), key=lambda r: (-r["val_ap_pred_avg"], r["idx"]))
WIN = ORDER[0]
TIES = [r["name"] for r in ORDER if abs(r["val_ap_pred_avg"] - WIN["val_ap_pred_avg"]) < TIE_EPS]
log(f"第一组 24 配置按 top{TOPK} **预测平均**的验证 AP 降序（选择只读这一列）：")
for i, r in enumerate(ORDER, 1):
    tie = " ←并列(1e-5内)" if r["name"] in TIES and len(TIES) > 1 else ""
    log(f"  {i:>2}. {r['name']:<22} 验证AP(预测平均)={r['val_ap_pred_avg']:.6f} "
        f"top{TOPK}epoch={r['topk_epochs']} p={r['p_pred_avg']:.4f} "
        f"[诊断 权重平均={r['val_ap_weight_avg']:.6f} argmax={r['val_ap_argmax']:.6f}] "
        f"训练{r['train_seconds']/60:.1f}分{tie}")
_sp = [r["val_ap_pred_avg"] for r in ORDER]
_sw = [r["val_ap_weight_avg"] for r in ORDER]
_sm = [r["val_ap_argmax"] for r in ORDER]
SPREAD = {"pred_avg": {"min": min(_sp), "max": max(_sp), "span": max(_sp) - min(_sp),
                       "std": float(np.std(_sp, ddof=1))},
          "weight_avg": {"min": min(_sw), "max": max(_sw), "span": max(_sw) - min(_sw),
                         "std": float(np.std(_sw, ddof=1))},
          "argmax": {"min": min(_sm), "max": max(_sm), "span": max(_sm) - min(_sm),
                     "std": float(np.std(_sm, ddof=1))}}
log("-" * 112)
log("24 配置之间的验证 AP 跨度（只看验证侧，不涉及 LSPR24）：")
log(f"  top{TOPK} 预测平均（本轮选择用）：{min(_sp):.6f}~{max(_sp):.6f} 跨度 {max(_sp)-min(_sp):.3e} "
    f"标准差 {np.std(_sp, ddof=1):.3e}")
log(f"  top{TOPK} 权重平均（上一轮做法）：{min(_sw):.6f}~{max(_sw):.6f} 跨度 {max(_sw)-min(_sw):.3e} "
    f"标准差 {np.std(_sw, ddof=1):.3e}")
log(f"  逐 epoch argmax（参照）      ：{min(_sm):.6f}~{max(_sm):.6f} 跨度 {max(_sm)-min(_sm):.3e} "
    f"标准差 {np.std(_sm, ddof=1):.3e}")
_cmp = "变小" if (max(_sp) - min(_sp)) < (max(_sw) - min(_sw)) else "变大"
log(f"  ★ 预测平均相对权重平均，24 配置的验证 AP 跨度{_cmp}："
    f"{max(_sw)-min(_sw):.3e} → {max(_sp)-min(_sp):.3e}")
log(f"最终选中：{WIN['name']}（声明序号 {WIN['idx']}），验证 AP={WIN['val_ap_pred_avg']:.6f}")
if len(TIES) > 1:
    log(f"  并列（{TIE_EPS:.0e} 内）：{TIES} —— 按声明顺序取第一个")

log("-" * 112)
log(f"第二组 2x2 四格的 top{TOPK} 预测平均验证 AP（本组不做配置间选择）：")
for cid, _a, _l in [("C00", 0, 0), ("C01", 0, 0), ("C10", 0, 0), ("C11", 0, 0)]:
    r = CELLRES[cid]
    log(f"  {cid} (agg={r['agg']}, lp={r['lp']}) 验证AP(预测平均)={r['val_ap_pred_avg']:.6f} "
        f"top{TOPK}epoch={r['topk_epochs']} p={r['p_pred_avg']:.4f} "
        f"[诊断 权重平均={r['val_ap_weight_avg']:.6f} argmax={r['val_ap_argmax']:.6f}"
        f" @ep{r['argmax_epoch']}]")

_frozen = {
    "protocol": f"逐epoch在LSPR23实体不相交验证集上算逐流AP，取前{TOPK}名epoch的检查点各自推理后"
                f"**平均预测分数**作为该配置的模型；p取{TOPK}份的算术均值；配置间按预测平均模型的"
                f"验证AP排序；不早停；无学习率调度器；k={TOPK}事前固定",
    "checkpoint_rule": "prediction_averaging_of_top5_by_val_ap",
    "selection_field": "val_ap_pred_avg",
    "seed": SEED, "topk": TOPK, "tie_eps": TIE_EPS, "epoch_steps": EPOCH_STEPS,
    "grid": {"L": list(GRID_L), "AUX_W": list(GRID_AUXW), "HID": list(GRID_HID)},
    "declared_order": [c["name"] for c in CONFIGS],
    "exec_L_order": list(EXEC_L_ORDER),
    "per_L": {str(L): {k: (int(v) if isinstance(v, (int, np.integer)) else float(v))
                       for k, v in PREP[L].items() if k not in ("I", "M", "tr", "val")}
              for L in PREP},
    "per_L_split": {str(L): {"n_train_seq": int(len(PREP[L]["tr"])),
                             "n_val_seq": int(len(PREP[L]["val"]))} for L in PREP},
    "hparam_configs": {r["name"]: {k: v for k, v in r.items() if k != "val_ap_history"}
                       for r in RES.values()},
    "hparam_val_ap_history": {r["name"]: r["val_ap_history"] for r in RES.values()},
    "cells_2x2": {c: {k: v for k, v in CELLRES[c].items() if k != "val_ap_history"} for c in CELLRES},
    "cells_2x2_val_ap_history": {c: CELLRES[c]["val_ap_history"] for c in CELLRES},
    "ranking": [r["name"] for r in ORDER],
    "winner": WIN["name"], "winner_idx": WIN["idx"], "winner_val_ap": WIN["val_ap_pred_avg"],
    "ties_within_eps": TIES,
    "val_ap_spread": SPREAD}
json.dump(_frozen, open(f"{OUT}/selection_frozen.json", "w"), ensure_ascii=False, indent=2)
SELECTION_FROZEN = True
log(f"选择阶段结束，结果已冻结写盘 {OUT}/selection_frozen.json")

# 释放 LSPR23 后再读 LSPR24，压低峰值
WIN_W = TOPW[WIN["idx"]]
WIN_L, WIN_HID = WIN["L"], WIN["HID"]
del gX23, gy23, X23, y23, e23f, t23f, _ORD, _BND, _SEGLEN, TOPW
PREP_META = {L: {k: v for k, v in PREP[L].items() if k not in ("I", "M", "tr", "val")} for L in PREP}
del PREP
torch.cuda.empty_cache()
log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24。合法评价次数 = 第一组 1 次 + 第二组 4 次 = 5 次
# =====================================================================================


def load24():
    global _N24_LOADS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入 LSPR24"
    _N24_LOADS += 1
    assert _N24_LOADS == 1, f"LSPR24 只允许从磁盘读入一次，当前第 {_N24_LOADS} 次"
    return (guarded_load("X24"), guarded_load("y24"), guarded_load("s24", True),
            guarded_load("d24", True), guarded_load("t24"), guarded_load("I24"),
            guarded_load("M24"))


log("=" * 112)
log("阶段二 评价：首次读入 LSPR24（选择已冻结）")
X24, y24, s24, d24, t24, I24c, M24c = load24()
assert X24.shape[1] == D

# ---- 实体构造：逐字照抄 ch3_full.py 第 130-133 行 ----
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
_flow_pos = float(y24.astype(np.float64).mean())
log(f"LSPR24 流={len(y24):,} 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 逐流正例率={_flow_pos:.10f}")
assert N_ENT == 47115, f"LSPR24 实体数自检失败：{N_ENT}"
assert int(ent_lab.sum()) == 752, f"LSPR24 正例实体自检失败：{int(ent_lab.sum())}"
assert abs(_flow_pos - 0.0257073138) < 1e-9, f"LSPR24 逐流正例率自检失败：{_flow_pos:.12f}"
log("LSPR24 自检通过：实体 47,115 / 正例实体 752 / 逐流正例率 0.0257073138")
del key24, s24, d24

# ---- 实体内时序秩（ch3_full 第 136-140 行），供 ent_ap/dr_at_fpr 的 first_k 参数用 ----
_o24 = np.lexsort((t24, ent24))
_e24 = ent24[_o24]
_s24 = np.flatnonzero(np.r_[True, _e24[1:] != _e24[:-1]])
_rank = np.empty(len(_o24), np.int64)
_rank[_o24] = np.arange(len(_o24)) - np.repeat(_s24, np.diff(np.r_[_s24, len(_o24)]))
_BND24 = np.flatnonzero(np.r_[True, _e24[1:] != _e24[:-1], True])
_SEG24 = np.diff(_BND24)
del _e24, _s24, t24


def rechunk24(Lu):
    """LSPR24 按 L 重新分块，语义与 rechunk23 相同。"""
    nch = -(-_SEG24 // Lu)
    n = int(nch.sum())
    off = np.repeat(np.cumsum(nch) - nch, nch)
    st = np.repeat(_BND24[:-1], nch) + (np.arange(n) - off) * Lu
    en = np.repeat(_BND24[1:], nch)
    real = np.minimum(Lu, en - st)
    col = np.arange(Lu)
    Mb = col[None, :] < real[:, None]
    pos = np.minimum(st[:, None] + col[None, :], len(_o24) - 1)
    return np.where(Mb, _o24[pos], 0).astype(np.int64), Mb.astype(np.float32)


gX24 = torch.from_numpy(X24).to(dev)
del X24
log(f"LSPR24 特征已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


# ---- 评价口径：逐字照抄 ch3_full.py 第 213-240 行（含末尾 .astype(np.float32)）----
def ent_ap(sc, seen, p=None, first_k=None):
    """实体级 AP。first_k 不为空时只用每个实体按时间的前 k 条流（延迟约束）。"""
    m = seen.copy()
    if first_k is not None: m &= (_rank < first_k)
    if not m.any(): return float("nan"), 0
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p); np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es)
    return average_precision_score(ent_lab[ok], es[ok]), int(ok.sum())


def dr_at_fpr(sc, seen, target=0.04, p=None, first_k=None):
    m = seen.copy()
    if first_k is not None: m &= (_rank < first_k)
    if p is None:
        es = np.full(N_ENT, -np.inf, np.float32); np.maximum.at(es, ent24[m], sc[m])
    else:
        num = np.zeros(N_ENT, np.float64); cnt = np.zeros(N_ENT, np.float64)
        np.add.at(num, ent24[m], np.clip(sc[m], 1e-7, 1.0).astype(np.float64) ** p); np.add.at(cnt, ent24[m], 1.0)
        es = np.where(cnt > 0, (num / np.maximum(cnt, 1)) ** (1.0 / p), -np.inf).astype(np.float32)
    ok = np.isfinite(es); v = es[ok]; l = ent_lab[ok]
    neg = np.sort(v[l == 0])[::-1]
    if len(neg) == 0: return float("nan")
    thr = neg[min(int(len(neg) * target), len(neg) - 1)]
    return float((v[l == 1] >= thr).mean())


@torch.no_grad()
def score24(states, agg, lp, hid, Lu, gI24, gM24, group, name):
    """LSPR24 逐流打分：top-5 检查点各自推理一遍后**平均预测分数**，p 取算术均值。

    推理循环与预测平均逐字照抄 ch3_full.py 第 196-210 行。
    每调用一次记一次评价；合法总次数 = 5（第一组胜者 1 + 第二组四格 4）。
    """
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    log(f"LSPR24 评价 #{_EVAL24_CALLS}/5 ← [{group}] {name}"
        f"（L={Lu}, HID={hid}, agg={agg}, lp={lp}, {len(states)} 个检查点预测平均）")
    _EVAL24_LEDGER.append({"call": _EVAL24_CALLS, "group": group, "config": name,
                           "L": Lu, "HID": hid, "agg": agg, "lp": lp, "n_ckpt": len(states)})
    assert _EVAL24_CALLS <= 5, f"LSPR24 评价次数超出预算：第 {_EVAL24_CALLS} 次"
    net = Model(agg, lp, hid).to(dev)
    acc = None; seen = None; ps = []
    t1 = time.time()
    for sd_ in states:
        net.load_state_dict({k: v.to(dev) for k, v in sd_.items()})
        net.eval(); ps.append(net.p.item())
        sc = torch.zeros(len(y24), device=dev)
        sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
        for a in range(0, len(gI24), 2048):
            idx = gI24[a:a + 2048]; msk = gM24[a:a + 2048]; b = idx.shape[0]
            pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, Lu, D), msk))
            fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
            sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
        s_ = sc.cpu().numpy(); n_ = sn.cpu().numpy()
        acc = s_ if acc is None else acc + s_
        seen = n_ if seen is None else (seen | n_)
        del sc, sn
    log(f"  {len(states)} 遍推理共 {time.time()-t1:.1f} 秒，p 逐检查点={['%.4f' % v for v in ps]} "
        f"→ 算术均值 {np.mean(ps):.6f}")
    del net
    torch.cuda.empty_cache()
    return acc / len(states), seen, float(np.mean(ps))


def metrics_of(sc, seen, p, lp):
    """ch3_full 口径：lp=True 的格用学到的 p 做 Lp 聚合，lp=False 的格退化为 max。"""
    fap = float(average_precision_score(y24[seen], sc[seen]))
    fauc = float(roc_auc_score(y24[seen], sc[seen]))
    e_max, n_ok = ent_ap(sc, seen)
    e_lp, _ = ent_ap(sc, seen, p if lp else None)
    dr_main = dr_at_fpr(sc, seen, 0.04, p if lp else None)
    dr_max = dr_at_fpr(sc, seen, 0.04, None)
    return {"fap": fap, "fauc": fauc, "e_max": float(e_max), "e_lp": float(e_lp),
            "dr_main": float(dr_main), "dr_max": float(dr_max),
            "n_ent_scored": int(n_ok), "p": float(p), "coverage": float(seen.mean())}


def upload_chunks(Lu):
    I_, M_ = rechunk24(Lu)
    log(f"LSPR24 按 L={Lu} 分块：{len(I_):,} 序列 填充率 {M_.mean():.4f}")
    if Lu == BASE_L:
        assert np.array_equal(I_, I24c), "L=128 的 LSPR24 分块与冻结缓存 I24 不一致"
        assert np.array_equal(M_, M24c), "L=128 的 LSPR24 分块与冻结缓存 M24 不一致"
        log("  L=128 LSPR24 分块自检通过：与冻结缓存 I24/M24 逐元素一致")
    gI_ = torch.from_numpy(I_).to(dev); gM_ = torch.from_numpy(M_).to(dev)
    del I_, M_
    log(f"  分块已上卡，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")
    return gI_, gM_


# ---------------- 第一组：最终选中配置，LSPR24 评价一次 ----------------
log("=" * 112)
log(f"第一组 最终配置 {WIN['name']}：加载 top{TOPK} 检查点，在 LSPR24 上评价一次")
gI24, gM24 = upload_chunks(WIN_L)
sc_w, seen_w, p_win = score24(WIN_W, True, True, WIN_HID, WIN_L, gI24, gM24,
                              "第一组-超参搜索", WIN["name"])
assert seen_w.all(), f"逐流覆盖不全：{seen_w.mean():.6f}（按 L 重新分块后应恒为 1.0）"
assert abs(p_win - WIN["p_pred_avg"]) < 1e-9, "权重回载后 p 与选择阶段不一致"
MW = metrics_of(sc_w, seen_w, p_win, True)
log("-" * 112)
log(f"【最终配置 {WIN['name']} 在 LSPR24 上的全部指标】")
log(f"  L={WIN_L} AUX_W={WIN['AUX_W']} HID={WIN_HID} 参数量={WIN['npar']:,} "
    f"top{TOPK}epoch={WIN['topk_epochs']}")
log(f"  top{TOPK} 各 epoch 验证AP = {['%.6f' % v for v in WIN['topk_val_aps']]}，"
    f"预测平均后验证AP = {WIN['val_ap_pred_avg']:.6f}")
log(f"  学到的 p（{TOPK} 份算术均值） = {p_win:.6f}")
log(f"  逐流 AP        = {MW['fap']:.6f}   逐流 AUC = {MW['fauc']:.6f}")
log(f"  实体 AP(max)   = {MW['e_max']:.6f}")
log(f"  实体 AP(Lp)    = {MW['e_lp']:.6f}   ← 主对比口径")
log(f"  DR@4%FPR(Lp)   = {MW['dr_main']:.6f}   ← 主口径")
log(f"  DR@4%FPR(max)  = {MW['dr_max']:.6f}   ← 全格 max 口径")
log(f"  覆盖实体 = {MW['n_ent_scored']:,} / {N_ENT:,}  逐流覆盖率 {MW['coverage']:.6f}")
np.save(f"{OUT}/scores_winner.npy", sc_w); np.save(f"{OUT}/seen_winner.npy", seen_w)
log(f"  最终配置逐流分数已存 {OUT}/scores_winner.npy")

if WIN_L != CELL_L:
    del gI24, gM24
    torch.cuda.empty_cache()
    log(f"胜者分块已释放（L={WIN_L}→{CELL_L} 需重新分块），显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")
    gI24, gM24 = upload_chunks(CELL_L)

# ---------------- 第二组：2x2 四格，各评价一次 ----------------
log("=" * 112)
log(f"第二组 2x2 四格（L={CELL_L}, AUX_W={CELL_AUXW}, HID={CELL_HID}）：每格加载 top{TOPK} 检查点评价一次")
CELL24 = {}
for cid in ["C00", "C01", "C10", "C11"]:
    r = CELLRES[cid]
    sc_c, seen_c, p_c = score24(CELLW[cid], r["agg"], r["lp"], CELL_HID, CELL_L,
                                gI24, gM24, "第二组-2x2四格", cid)
    assert seen_c.all(), f"{cid} 逐流覆盖不全：{seen_c.mean():.6f}"
    assert abs(p_c - r["p_pred_avg"]) < 1e-9, f"{cid} 权重回载后 p 与选择阶段不一致"
    m = metrics_of(sc_c, seen_c, p_c, r["lp"])
    m.update(agg=r["agg"], lp=r["lp"], topk_epochs=r["topk_epochs"],
             topk_val_aps=r["topk_val_aps"], val_ap_pred_avg=r["val_ap_pred_avg"],
             train_seconds=r["train_seconds"], npar=r["npar"])
    CELL24[cid] = m
    log(f"{cid}: top{TOPK}epoch={r['topk_epochs']} 验证AP(预测平均)={r['val_ap_pred_avg']:.6f} "
        f"p={p_c:.4f} | 逐流AP={m['fap']:.6f} AUC={m['fauc']:.6f} 实体AP(max)={m['e_max']:.6f} "
        f"实体AP(Lp)={m['e_lp']:.6f} DR@4%FPR(主)={m['dr_main']:.6f} (max口径={m['dr_max']:.6f})")
    if cid == "C11":
        np.save(f"{OUT}/scores_2x2_C11.npy", sc_c); np.save(f"{OUT}/seen_2x2_C11.npy", seen_c)
        log(f"  2x2 C11 逐流分数已存 {OUT}/scores_2x2_C11.npy")
    del sc_c, seen_c

assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
assert _EVAL24_CALLS == 5, f"LSPR24 评价次数应为 5（第一组 1 + 第二组 4），实为 {_EVAL24_CALLS}"
log("=" * 112)
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次，均在选择冻结之后")
for e in _EVAL24_LEDGER:
    log(f"  #{e['call']} [{e['group']}] {e['config']}（L={e['L']}, HID={e['HID']}, "
        f"agg={e['agg']}, lp={e['lp']}, {e['n_ckpt']} 检查点）")

# =====================================================================================
# 2x2 交互项：五个口径
# =====================================================================================
INTER = {}
log("=" * 112)
log("2x2 交互项：交互 = C11 − C10 − C01 + C00；组合创新 = 交互>0 且 组合>0")
for label, key in [("实体AP(主口径: lp格用Lp, 非lp格用max)", "e_lp"),
                   ("实体AP(全格 max 口径)", "e_max"),
                   ("DR@4%FPR(主口径)", "dr_main"),
                   ("DR@4%FPR(全格 max 口径)", "dr_max"),
                   ("逐流AP", "fap")]:
    v = {c: CELL24[c][key] for c in CELL24}
    eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
    inter = eAB - (eA + eB)
    c1 = inter > 0; c3 = eAB > 0
    INTER[key] = {"label": label, "C00": v["C00"], "C01": v["C01"], "C10": v["C10"], "C11": v["C11"],
                  "A": eA, "B": eB, "sum": eA + eB, "combo": eAB, "interaction": inter,
                  "crit_interaction_pos": bool(c1), "crit_combo_pos": bool(c3),
                  "combo_innovation": bool(c1 and c3)}
    log(f"【{label}】")
    log(f"  C00={v['C00']:.6f}  C01={v['C01']:.6f}  C10={v['C10']:.6f}  C11={v['C11']:.6f}")
    log(f"  A(仅聚合)={eA:+.6f}  B(仅Lp)={eB:+.6f}  之和={eA+eB:+.6f}  组合={eAB:+.6f}  交互={inter:+.6f}")
    log(f"  判据一 交互>0: {'通过' if c1 else '不通过'} | 判据二 组合>基线: {'通过' if c3 else '不通过'}"
        f" | ★ 组合创新{'成立' if (c1 and c3) else '不成立'}")

log("-" * 112)
log("第二组 2x2 新数字 vs 上一轮单 epoch argmax（新 − 旧）")
DELTA_2X2 = {}
for cid in ["C00", "C01", "C10", "C11"]:
    d = {k: CELL24[cid][k] - ARGMAX_2X2[cid][k] for k in ["fap", "e_max", "e_lp", "dr_main", "dr_max"]}
    DELTA_2X2[cid] = d
    log(f"  {cid}: 逐流AP {ARGMAX_2X2[cid]['fap']:.6f}→{CELL24[cid]['fap']:.6f} ({d['fap']:+.6f}) | "
        f"实体AP(主) {ARGMAX_2X2[cid]['e_lp']:.6f}→{CELL24[cid]['e_lp']:.6f} ({d['e_lp']:+.6f}) | "
        f"实体AP(max) {ARGMAX_2X2[cid]['e_max']:.6f}→{CELL24[cid]['e_max']:.6f} ({d['e_max']:+.6f}) | "
        f"DR主 {ARGMAX_2X2[cid]['dr_main']:.6f}→{CELL24[cid]['dr_main']:.6f} ({d['dr_main']:+.6f})")

# =====================================================================================
# 与 XGBoost 基线的差
# =====================================================================================
log("=" * 112)
log(f"与 XGBoost 基线的差（XGB: 实体AP(同p口径)={XGB_REF['e_lp_at_p1p056']:.6f} "
    f"实体AP(max)={XGB_REF['e_max']:.6f} DR@4%FPR(max)={XGB_REF['dr_max']:.6f} "
    f"逐流AP={XGB_REF['fap']:.6f}）")
log(f"  第一组最终配置 {WIN['name']}：")
log(f"    实体AP(Lp)    {MW['e_lp']:.6f}  差 {MW['e_lp']-XGB_REF['e_lp_at_p1p056']:+.6f}")
log(f"    实体AP(max)   {MW['e_max']:.6f}  差 {MW['e_max']-XGB_REF['e_max']:+.6f}")
log(f"    DR@4%FPR(max) {MW['dr_max']:.6f}  差 {MW['dr_max']-XGB_REF['dr_max']:+.6f}")
log(f"    逐流AP        {MW['fap']:.6f}  差 {MW['fap']-XGB_REF['fap']:+.6f}")
for cid in ["C00", "C01", "C10", "C11"]:
    m = CELL24[cid]
    log(f"  2x2 {cid}: 实体AP(主) {m['e_lp']:.6f} ({m['e_lp']-XGB_REF['e_lp_at_p1p056']:+.6f}) | "
        f"实体AP(max) {m['e_max']:.6f} ({m['e_max']-XGB_REF['e_max']:+.6f}) | "
        f"DR(max) {m['dr_max']:.6f} ({m['dr_max']-XGB_REF['dr_max']:+.6f}) | "
        f"逐流AP {m['fap']:.6f} ({m['fap']-XGB_REF['fap']:+.6f})")

log("=" * 112)
log(f"★ 一句话结论：最终配置 {WIN['name']} 的实体 AP {MW['e_lp']:.6f} "
    f"{'超过' if MW['e_lp'] > XGB_REF['e_lp_at_p1p056'] else '未超过'} "
    f"XGBoost 基线 {XGB_REF['e_lp_at_p1p056']:.6f}，差 {MW['e_lp']-XGB_REF['e_lp_at_p1p056']:+.6f}")

# ---- 补充诊断：XGB 的 Lp 聚合在本配置学到的 p 下重算，给出同 p 口径的差 ----
# 这是基线的重新聚合，不是候选配置的评价，不计入 _EVAL24_CALLS。
MATCHED = None
if os.path.exists(f"{XGBD}/scores_xgb.npy"):
    sx = np.load(f"{XGBD}/scores_xgb.npy")
    assert len(sx) == len(y24), f"XGB 分数长度 {len(sx)} 与 LSPR24 流数 {len(y24)} 不符"
    _num = np.zeros(N_ENT, np.float64); _cnt = np.zeros(N_ENT, np.float64)
    np.add.at(_num, ent24, np.clip(sx, 1e-7, 1.0).astype(np.float64) ** p_win)
    np.add.at(_cnt, ent24, 1.0)
    _esx = np.where(_cnt > 0, (_num / np.maximum(_cnt, 1)) ** (1.0 / p_win), -np.inf).astype(np.float32)
    _okx = np.isfinite(_esx)
    xgb_lp_matched = float(average_precision_score(ent_lab[_okx], _esx[_okx]))
    MATCHED = {"p": p_win, "xgb_entity_ap_lp_at_this_p": xgb_lp_matched,
               "gap": float(MW["e_lp"]) - xgb_lp_matched}
    log(f"补充：XGB 的 Lp 聚合改用最终配置的 p={p_win:.6f} 重算得实体 AP={xgb_lp_matched:.6f}，"
        f"同 p 口径差 {MW['e_lp']-xgb_lp_matched:+.6f}")
    del sx, _num, _cnt, _esx

json.dump({"selection": _frozen,
           "group1_final": {"config": WIN["name"], "L": WIN_L, "AUX_W": WIN["AUX_W"],
                            "HID": WIN_HID, "n_epoch": WIN["n_epoch"],
                            "topk_epochs": WIN["topk_epochs"],
                            "topk_val_aps": WIN["topk_val_aps"],
                            "val_ap_pred_avg": WIN["val_ap_pred_avg"],
                            "npar": WIN["npar"], **MW},
           "group2_cells_2x2": CELL24,
           "interaction": INTER,
           "delta_2x2_vs_argmax_protocol": DELTA_2X2,
           "argmax_2x2_reference": ARGMAX_2X2,
           "xgb_reference": XGB_REF,
           "matched_p_diagnostic": MATCHED,
           "val_ap_spread": SPREAD,
           "delta_vs_xgb": {"group1": {"entity_ap_lp": MW["e_lp"] - XGB_REF["e_lp_at_p1p056"],
                                       "entity_ap_max": MW["e_max"] - XGB_REF["e_max"],
                                       "dr_max": MW["dr_max"] - XGB_REF["dr_max"],
                                       "flow_ap": MW["fap"] - XGB_REF["fap"]},
                            "cells": {c: {"entity_ap_lp": CELL24[c]["e_lp"] - XGB_REF["e_lp_at_p1p056"],
                                          "entity_ap_max": CELL24[c]["e_max"] - XGB_REF["e_max"],
                                          "dr_max": CELL24[c]["dr_max"] - XGB_REF["dr_max"],
                                          "flow_ap": CELL24[c]["fap"] - XGB_REF["fap"]}
                                      for c in CELL24}},
           "lspr24": {"n_flow": int(len(y24)), "n_entity": int(N_ENT),
                      "n_pos_entity": int(ent_lab.sum()), "flow_pos_rate": _flow_pos},
           "per_L_meta": {str(L): {k: (int(v) if isinstance(v, (int, np.integer)) else float(v))
                                   for k, v in PREP_META[L].items()} for L in PREP_META},
           "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS,
                         "ledger": _EVAL24_LEDGER}},
          open(f"{OUT}/ch3_hparam_fairsel_v2_results.json", "w"), ensure_ascii=False, indent=2)
log(f"全部结果已存 {OUT}/ch3_hparam_fairsel_v2_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
