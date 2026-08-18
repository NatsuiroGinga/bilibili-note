# -*- coding: utf-8 -*-
"""第三章 CPA-ELP 超参搜索：合规选择协议下的 24 配置格点（只跑 C11 格 agg=True, lp=True）。

动机：新协议（LSPR23 实体不相交验证集选检查点、LSPR24 只评一次）下的超参一个都没调过。
现行 L=128 / AUX_W=1.0 / HID=192 / 20000 步是从旧冻结配置继承的，而旧配置是看着 LSPR24
调出来的——对新协议而言等于随机取值。本脚本在事前声明的 24 点格上做一次合规搜索。

============================ 选择协议（本任务的全部意义）============================
一、验证集只用 LSPR23「实体不相交」子集，切分代码逐字复用 tools/ch3_2x2_fairsel.py 第 80-89 行。
二、每个配置跑满 N_EPOCH 轮不早停，逐 epoch 在验证集上算逐流 AP。
三、检查点：取验证 AP **前 5 名** epoch 的 state_dict 逐参数算术平均（k=5 事前固定，
    不得按结果调整，也不得在 argmax 与 top-k 之间比较后择优）。平均后的模型直接用于推理，
    不再做预测平均。
四、两级选择都只用验证集：配置内部按上述 top-5 平均定检查点；配置之间按「top-5 平均权重
    在验证集上重算的 AP」排序，取唯一最终配置。并列（1e-5 内）按 CONFIGS 声明顺序取第一个。
五、LSPR24 只对最终选出的那一个配置评价一次。

============================ LSPR24 隔离的机械保证 ============================
不是靠注释约定，是靠加载顺序 + 单一加载入口 + 计数断言：

  guarded_load()  ：所有 np.load 的唯一入口。名字里含 "24" 且 SELECTION_FROZEN 为假时直接断言失败。
                    因此选择阶段不可能有任何 LSPR24 数组进入本进程。
  阶段闸门        ：24 个配置全部训练并选出唯一胜者后，先把选择结果写盘，再置 SELECTION_FROZEN=True。
  load24()        ：首行断言 SELECTION_FROZEN，并把 _N24_LOADS 加一。
  score24()       ：首行断言 SELECTION_FROZEN，并把 _EVAL24_CALLS 加一。
  收尾断言        ：_N24_LOADS == 1 且 _EVAL24_CALLS == 1。

  训练与选择函数 train_and_select() / val_ap() / select_winner() 的函数体内不出现任何
  LSPR24 标识符；调用它们时进程内也没有 LSPR24 数据。
==============================================================================

评价口径逐字复刻 tools/ch3_full.py：实体构造第 130-133 行、ent_ap 第 213-225 行
（Lp 聚合含末尾 .astype(np.float32)）、dr_at_fpr 第 236-240 行。机制的数学形式一律不改。
不创建 SwanLab 运行身份。不落盘 24 份分数，只保存最终选中配置的逐流分数。
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
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-hparam-fairsel"
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
# L=128 / AUX_W=1.0 / HID=192 是既有 ch3_2x2_fairsel C11 的复现锚点，先跑它，
# 一旦分块、切分或步数缩放退化，三分钟内被锚点断言拦住，而不是跑满两小时才发现。
# 并列裁决只用声明顺序 CONFIGS[i]["idx"]，与执行顺序无关。
EXEC_L_ORDER = (128, 64, 32)

# ---- 其余设定：照抄 ch3_2x2_fairsel.py / ch3_full.py，不调 ----
SEED, BS, LR, DP = 42, 64, 2e-3, 0.1
EPOCH_STEPS = 1000
BASE_L, BASE_EPOCH = 128, 20          # L=128 对应 20 epoch × 1000 步 = 20000 步
TOPK = 5                              # 事前固定的检查点平均个数
VAL_FRAC, TIME_TAIL = 0.10, 0.15      # 切分参数照抄 ch3_2x2_fairsel 第 54 行
TIE_EPS = 1e-5                        # 验证 AP 并列判定阈值

# ---- 对照基准（外部给定常数，不参与任何选择）----
XGB_REF = {"e_lp_at_p1p056": 0.533104, "dr_max": 0.692819, "fap": 0.222391}
C11_REF = {"e_lp": 0.518350, "dr_max": 0.714096, "fap": 0.291843}
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


def guarded_load(name, allow_pickle=False):
    """所有 np.load 的唯一入口。选择阶段禁止读入任何名字含 '24' 的数组。"""
    assert SELECTION_FROZEN or "24" not in name, \
        f"阶段闸门未开：选择阶段禁止读入 {name}.npy"
    return np.load(f"{CACHE}/{name}.npy", allow_pickle=allow_pickle)


# =====================================================================================
# 阶段一：只读入 LSPR23
# =====================================================================================
log("=" * 108)
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
log(f"步数缩放（∝ 训练序列数）：" + "  ".join(
    f"L={L}:{PREP[L]['n_epoch']}轮/{PREP[L]['steps']:,}步/真实流visits {PREP[L]['real_flow_visits']:,.0f}"
    for L in sorted(PREP)))
log(f"  各 L 真实流访问数极差 {(max(_v)-min(_v))/np.mean(_v)*100:.3f}%（整轮取整所致）")

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
def val_ap(net, gI, gM, gval, Lu):
    """LSPR23 实体不相交验证集上的逐流 AP，照抄 ch3_2x2_fairsel.val_ap()。

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
    P = np.concatenate(P); Y = np.concatenate(Y)
    assert Y.max() > 0, "验证集无正例，选择信号无效"
    return float(average_precision_score(Y, P))


def train_and_select(cfg, gI, gM, gtr, gval, Lu, n_epoch, spw):
    """训练满 n_epoch 不早停，逐 epoch 记录验证 AP，取前 TOPK 名 epoch 的权重算术平均。

    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    torch.manual_seed(SEED); np.random.seed(SEED)
    net = Model(True, True, cfg["HID"]).to(dev)          # 只跑 C11 格
    dec = [p for n, p in net.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    nod = [p for n, p in net.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    opt = torch.optim.AdamW([{"params": dec, "weight_decay": 0.01},
                             {"params": nod, "weight_decay": 0.0}], lr=LR)
    gen = torch.Generator().manual_seed(SEED)
    aux_w = cfg["AUX_W"]
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
            log(f"    {cfg['name']} ep {ep:>2}/{n_epoch} 验证AP={v:.6f} p={net.p.item():.4f} "
                f"累计{(time.time()-t0)/60:.1f}分")
    tr_t = time.time() - t0

    # ---- top-5 权重平均：k 事前固定，排序键 (-验证AP, epoch)，同分取更早的 epoch ----
    rank = sorted(range(n_epoch), key=lambda i: (-hist[i][1], hist[i][0]))
    top = sorted(rank[:TOPK])
    avg = {k: torch.stack([snaps[i][k] for i in top], 0).mean(0) for k in snaps[0]}
    net.load_state_dict({k: v.to(dev) for k, v in avg.items()})
    v_avg = val_ap(net, gI, gM, gval, Lu)
    p_avg = net.p.item()
    top_info = [[hist[i][0], hist[i][1]] for i in top]
    log(f"  {cfg['name']} 训练 {tr_t/60:.2f} 分 | top{TOPK} epoch="
        f"{[t[0] for t in top_info]} 验证AP={['%.6f' % t[1] for t in top_info]}")
    log(f"  {cfg['name']} → top{TOPK} 平均后 验证AP={v_avg:.6f} p={p_avg:.4f} "
        f"（逐 epoch argmax 为 {max(h[1] for h in hist):.6f} @ep{max(hist, key=lambda h: h[1])[0]}）")
    out = {"idx": cfg["idx"], "name": cfg["name"], "L": Lu, "AUX_W": aux_w, "HID": cfg["HID"],
           "n_epoch": n_epoch, "steps": n_epoch * EPOCH_STEPS, "spw": spw,
           "val_ap_history": hist, "topk_epochs": [t[0] for t in top_info],
           "topk_val_aps": [t[1] for t in top_info],
           "val_ap_avg": v_avg, "p_avg": p_avg,
           "val_ap_argmax": max(h[1] for h in hist),
           "argmax_epoch": max(hist, key=lambda h: h[1])[0],
           "train_seconds": tr_t,
           "npar": sum(p.numel() for p in net.parameters()),
           "peak_gib": torch.cuda.max_memory_allocated() / 2 ** 30}
    return out, {k: v.clone() for k, v in avg.items()}


RES, AVGW = {}, {}
log("=" * 108)
log(f"24 配置串行训练，seed={SEED}，只跑 C11 格（agg=True, lp=True），不早停，无学习率调度器")
for Lu in EXEC_L_ORDER:
    pr = PREP[Lu]
    gI = torch.from_numpy(pr["I"]).to(dev)
    gM = torch.from_numpy(pr["M"]).to(dev)
    gtr = torch.from_numpy(pr["tr"]).to(dev)
    gval = torch.from_numpy(pr["val"]).to(dev)
    log("-" * 108)
    log(f"L={Lu} 块：{pr['n_epoch']} 轮 × {EPOCH_STEPS} 步，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")
    for cfg in [c for c in CONFIGS if c["L"] == Lu]:
        torch.cuda.reset_peak_memory_stats()
        r, w = train_and_select(cfg, gI, gM, gtr, gval, Lu, pr["n_epoch"], pr["spw"])
        RES[cfg["idx"]] = r; AVGW[cfg["idx"]] = w
        if Lu == BASE_L and cfg["AUX_W"] == 1.0 and cfg["HID"] == 192:
            d = [abs(r["val_ap_history"][i][1] - ANCHOR_VAL_AP[i]) for i in range(BASE_EPOCH)]
            log(f"  ★ 锚点校验 vs ch3_2x2_fairsel C11：逐 epoch 验证 AP 最大差 {max(d):.3e}"
                f"（容差 {ANCHOR_TOL:.0e}），argmax epoch {r['argmax_epoch']}（冻结记录为 10）")
            assert max(d) < ANCHOR_TOL, \
                f"L=128/AUX_W=1.0/HID=192 未复现既有 C11 验证曲线，最大差 {max(d):.3e}；" \
                f"分块、切分、步数或训练流存在退化，本表不可信"
    del gI, gM, gtr, gval
    torch.cuda.empty_cache()

# =====================================================================================
# 选择：两级都只用验证集
# =====================================================================================
log("=" * 108)
ORDER = sorted(RES.values(), key=lambda r: (-r["val_ap_avg"], r["idx"]))
WIN = ORDER[0]
TIES = [r["name"] for r in ORDER if abs(r["val_ap_avg"] - WIN["val_ap_avg"]) < TIE_EPS]
log(f"24 配置按 top{TOPK} 平均权重的验证 AP 降序：")
for i, r in enumerate(ORDER, 1):
    log(f"  {i:>2}. {r['name']:<22} 验证AP(平均后)={r['val_ap_avg']:.6f} "
        f"top{TOPK}epoch={r['topk_epochs']} p={r['p_avg']:.4f} "
        f"argmaxAP={r['val_ap_argmax']:.6f} 训练{r['train_seconds']/60:.1f}分")
_sa = [r["val_ap_avg"] for r in ORDER]
_sm = [r["val_ap_argmax"] for r in ORDER]
log(f"验证 AP 跨度：top{TOPK}平均后 {max(_sa)-min(_sa):.3e}（{min(_sa):.6f}~{max(_sa):.6f}）| "
    f"逐 epoch argmax {max(_sm)-min(_sm):.3e}（{min(_sm):.6f}~{max(_sm):.6f}）")
log(f"最终选中：{WIN['name']}（声明序号 {WIN['idx']}），验证 AP={WIN['val_ap_avg']:.6f}")
if len(TIES) > 1:
    log(f"  并列（{TIE_EPS:.0e} 内）：{TIES} —— 按声明顺序取第一个")

_frozen = {
    "protocol": f"逐epoch在LSPR23实体不相交验证集上算逐流AP，取前{TOPK}名epoch的state_dict逐参数"
                f"算术平均作为该配置检查点；配置间按平均后模型的验证AP排序；不早停；无学习率调度器",
    "seed": SEED, "topk": TOPK, "tie_eps": TIE_EPS, "epoch_steps": EPOCH_STEPS,
    "grid": {"L": list(GRID_L), "AUX_W": list(GRID_AUXW), "HID": list(GRID_HID)},
    "declared_order": [c["name"] for c in CONFIGS],
    "exec_L_order": list(EXEC_L_ORDER),
    "per_L": {str(L): {k: (int(v) if isinstance(v, (int, np.integer)) else float(v))
                       for k, v in PREP[L].items() if k not in ("I", "M", "tr", "val")}
              for L in PREP},
    "per_L_split": {str(L): {"n_train_seq": int(len(PREP[L]["tr"])),
                             "n_val_seq": int(len(PREP[L]["val"]))} for L in PREP},
    "configs": {r["name"]: {k: v for k, v in r.items() if k != "val_ap_history"}
                for r in RES.values()},
    "val_ap_history": {r["name"]: r["val_ap_history"] for r in RES.values()},
    "ranking": [r["name"] for r in ORDER],
    "winner": WIN["name"], "winner_idx": WIN["idx"], "winner_val_ap": WIN["val_ap_avg"],
    "ties_within_eps": TIES,
    "val_ap_spread_topk_avg": max(_sa) - min(_sa),
    "val_ap_spread_argmax": max(_sm) - min(_sm)}
json.dump(_frozen, open(f"{OUT}/selection_frozen.json", "w"), ensure_ascii=False, indent=2)
SELECTION_FROZEN = True
log(f"选择阶段结束，结果已冻结写盘 {OUT}/selection_frozen.json")

# 释放 LSPR23 后再读 LSPR24，压低峰值
WIN_W = AVGW[WIN["idx"]]
WIN_L = WIN["L"]
WIN_HID = WIN["HID"]
del gX23, gy23, X23, y23, e23f, t23f, _ORD, _BND, _SEGLEN, PREP, AVGW
torch.cuda.empty_cache()
log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24，只对最终选出的那一个配置评价一次
# =====================================================================================


def load24():
    global _N24_LOADS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入 LSPR24"
    _N24_LOADS += 1
    assert _N24_LOADS == 1, f"LSPR24 只允许从磁盘读入一次，当前第 {_N24_LOADS} 次"
    return (guarded_load("X24"), guarded_load("y24"), guarded_load("s24", True),
            guarded_load("d24", True), guarded_load("t24"), guarded_load("I24"),
            guarded_load("M24"))


log("=" * 108)
log("阶段二 评价：首次读入 LSPR24（选择已冻结）")
X24, y24, s24, d24, t24, I24c, M24c = load24()
assert X24.shape[1] == D

# ---- 实体构造：逐字照抄 ch3_full.py 第 130-133 行 ----
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
_flow_pos = float(y24.astype(np.float64).mean())
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 逐流正例率={_flow_pos:.10f}")
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

# ---- 按胜出配置的 L 对 LSPR24 重新分块 ----
_BND24 = np.flatnonzero(np.r_[True, _e24[1:] != _e24[:-1], True])
_SEG24 = np.diff(_BND24)
_nch = -(-_SEG24 // WIN_L)
_n24 = int(_nch.sum())
_off = np.repeat(np.cumsum(_nch) - _nch, _nch)
_st24 = np.repeat(_BND24[:-1], _nch) + (np.arange(_n24) - _off) * WIN_L
_en24 = np.repeat(_BND24[1:], _nch)
_real = np.minimum(WIN_L, _en24 - _st24)
_col = np.arange(WIN_L)
_Mb = _col[None, :] < _real[:, None]
_p24 = np.minimum(_st24[:, None] + _col[None, :], len(_o24) - 1)
I24 = np.where(_Mb, _o24[_p24], 0).astype(np.int64)
M24 = _Mb.astype(np.float32)
log(f"LSPR24 按 L={WIN_L} 分块：{len(I24):,} 序列 填充率 {M24.mean():.4f}")
if WIN_L == BASE_L:
    assert np.array_equal(I24, I24c), "L=128 的 LSPR24 分块与冻结缓存 I24 不一致"
    assert np.array_equal(M24, M24c), "L=128 的 LSPR24 分块与冻结缓存 M24 不一致"
    log("  L=128 LSPR24 分块自检通过：与冻结缓存 I24/M24 逐元素一致")
del _o24, _e24, _s24, _BND24, _SEG24, _nch, _off, _st24, _en24, _real, _col, _Mb, _p24
del I24c, M24c, t24

gX24 = torch.from_numpy(X24).to(dev)
gI24 = torch.from_numpy(I24).to(dev)
gM24 = torch.from_numpy(M24).to(dev)
del X24
log(f"LSPR24 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


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
def score24(net, Lu):
    """LSPR24 逐流打分。推理循环逐字照抄 ch3_full.py 第 199-207 行（单检查点，无预测平均）。"""
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    assert _EVAL24_CALLS == 1, f"LSPR24 只允许评价一次，当前第 {_EVAL24_CALLS} 次"
    net.eval()
    sc = torch.zeros(len(y24), device=dev)
    sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    for a in range(0, len(gI24), 2048):
        idx = gI24[a:a + 2048]; msk = gM24[a:a + 2048]; b = idx.shape[0]
        pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, Lu, D), msk))
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
    return sc.cpu().numpy(), sn.cpu().numpy()


log("=" * 108)
log(f"加载胜出配置 {WIN['name']} 的 top{TOPK} 平均权重，在 LSPR24 上评价一次")
net = Model(True, True, WIN_HID).to(dev)
net.load_state_dict({k: v.to(dev) for k, v in WIN_W.items()})
p_win = net.p.item()
assert abs(p_win - WIN["p_avg"]) < 1e-9, "权重回载后 p 与选择阶段不一致"
_t1 = time.time()
sc, seen = score24(net, WIN_L)
log(f"推理 {time.time()-_t1:.1f} 秒，逐流覆盖率 {seen.mean():.6f}")
assert seen.all(), f"逐流覆盖不全：{seen.mean():.6f}（按 L 重新分块后应恒为 1.0）"

fap = float(average_precision_score(y24[seen], sc[seen]))
fauc = float(roc_auc_score(y24[seen], sc[seen]))
e_max, n_ok = ent_ap(sc, seen)
e_lp, _ = ent_ap(sc, seen, p_win)
dr_main = dr_at_fpr(sc, seen, 0.04, p_win)
dr_max = dr_at_fpr(sc, seen, 0.04, None)
FINAL = {"config": WIN["name"], "L": WIN_L, "AUX_W": WIN["AUX_W"], "HID": WIN_HID,
         "n_epoch": WIN["n_epoch"], "topk_epochs": WIN["topk_epochs"],
         "val_ap_avg": WIN["val_ap_avg"], "p_learned": p_win,
         "flow_ap": fap, "flow_auc": fauc, "entity_ap_max": float(e_max),
         "entity_ap_lp": float(e_lp), "dr_at_4pct_fpr_lp": float(dr_main),
         "dr_at_4pct_fpr_max": float(dr_max), "n_entity_scored": int(n_ok),
         "coverage": float(seen.mean())}
log("=" * 108)
log(f"【最终配置 {WIN['name']} 在 LSPR24 上的全部指标】")
log(f"  学到的 p = {p_win:.6f}")
log(f"  逐流 AP        = {fap:.6f}   逐流 AUC = {fauc:.6f}")
log(f"  实体 AP(max)   = {e_max:.6f}")
log(f"  实体 AP(Lp)    = {e_lp:.6f}   ← 主对比口径")
log(f"  DR@4%FPR(Lp)   = {dr_main:.6f}")
log(f"  DR@4%FPR(max)  = {dr_max:.6f}   ← 预注册口径")
log(f"  覆盖实体 = {n_ok:,} / {N_ENT:,}")

log("-" * 108)
log("与 XGBoost 基线 / 当前 C11 的差（正号表示本配置更好）")
log(f"  实体AP(Lp)   : 本={e_lp:.6f}  XGB={XGB_REF['e_lp_at_p1p056']:.6f}"
    f"（差 {e_lp-XGB_REF['e_lp_at_p1p056']:+.6f}）  C11={C11_REF['e_lp']:.6f}"
    f"（差 {e_lp-C11_REF['e_lp']:+.6f}）")
log(f"  DR@4%FPR(max): 本={dr_max:.6f}  XGB={XGB_REF['dr_max']:.6f}"
    f"（差 {dr_max-XGB_REF['dr_max']:+.6f}）  C11={C11_REF['dr_max']:.6f}"
    f"（差 {dr_max-C11_REF['dr_max']:+.6f}）")
log(f"  逐流AP       : 本={fap:.6f}  XGB={XGB_REF['fap']:.6f}"
    f"（差 {fap-XGB_REF['fap']:+.6f}）  C11={C11_REF['fap']:.6f}"
    f"（差 {fap-C11_REF['fap']:+.6f}）")
log("=" * 108)
log(f"★ 一句话结论：实体 AP {e_lp:.6f} "
    f"{'超过' if e_lp > XGB_REF['e_lp_at_p1p056'] else '未超过'} XGBoost 基线 "
    f"{XGB_REF['e_lp_at_p1p056']:.6f}，差 {e_lp-XGB_REF['e_lp_at_p1p056']:+.6f}")

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
               "gap": float(e_lp) - xgb_lp_matched}
    log(f"补充：XGB 的 Lp 聚合改用本配置的 p={p_win:.6f} 重算得实体 AP={xgb_lp_matched:.6f}，"
        f"同 p 口径差 {e_lp-xgb_lp_matched:+.6f}")
    del sx, _num, _cnt, _esx

assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
assert _EVAL24_CALLS == 1, f"LSPR24 评价次数应为 1（只评最终配置），实为 {_EVAL24_CALLS}"
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次，"
    f"均发生在选择冻结之后")

np.save(f"{OUT}/scores_winner.npy", sc)
np.save(f"{OUT}/seen_winner.npy", seen)
json.dump({"selection": _frozen, "final": FINAL,
           "xgb_reference": XGB_REF, "c11_reference": C11_REF,
           "matched_p_diagnostic": MATCHED,
           "delta_vs_xgb": {"entity_ap_lp": float(e_lp) - XGB_REF["e_lp_at_p1p056"],
                            "dr_max": float(dr_max) - XGB_REF["dr_max"],
                            "flow_ap": fap - XGB_REF["fap"]},
           "delta_vs_c11": {"entity_ap_lp": float(e_lp) - C11_REF["e_lp"],
                            "dr_max": float(dr_max) - C11_REF["dr_max"],
                            "flow_ap": fap - C11_REF["fap"]},
           "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS}},
          open(f"{OUT}/ch3_hparam_fairsel_results.json", "w"), ensure_ascii=False, indent=2)
log(f"全部结果已存 {OUT}/ch3_hparam_fairsel_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
