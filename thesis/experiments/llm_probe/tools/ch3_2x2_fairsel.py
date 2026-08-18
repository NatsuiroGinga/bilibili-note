# -*- coding: utf-8 -*-
"""第三章 2x2 四格：修正后的检查点选择协议（LSPR23 实体不相交验证集逐 epoch 选优）。

与冻结脚本 tools/ch3_full.py 的**唯一**差异是「取哪个检查点」：
  冻结协议：末 5 个 epoch 的权重平均（无选择）。
  本脚本  ：跑满 20 epoch 不早停，逐 epoch 在 LSPR23「实体不相交」验证集上算逐流 AP，
            取该 AP 最大的那个 epoch 的权重。取消末 5 平均。

机制（Model.agg / Model.lp）、超参、损失、评价口径全部逐字照抄 ch3_full.py，不做任何改动。
验证集构造逐字照抄 tools/select_signal.py 第 151-168 行（同一 RandomState(42) 排列，同一比例）。

============================ LSPR24 隔离保证（本任务的核心）============================
不是靠注释约定，是靠**加载顺序**与**机械断言**：

  阶段一「选择」：进程内只从磁盘读入 LSPR23（X23/y23/I23/M23/E23/T23）。
                  四格全部训练完，逐 epoch 只在 LSPR23 验证集上打分并选出 epoch，
                  随后把「每格选中的 epoch + 该 epoch 的验证 AP」写盘冻结。
                  此刻 LSPR24 的任何数组**根本不存在于本进程**——没有 open()，没有 np.load()。
  阶段闸门      ：SELECTION_FROZEN = True，且 selection_frozen.json 已落盘。
  阶段二「评价」：load24() 首行断言 SELECTION_FROZEN，之后才 np.load LSPR24。
                  score24() 首行同样断言，并对每格计数，最后断言总评价次数 == 4。

  训练/选择函数 train_and_select() 的函数体内不出现任何 24 相关标识符；
  它只能访问模块级的 gX23/gy23/gI23/gM23/gtr/gval。
=====================================================================================
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
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


CACHE = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/dijk-repro/cache"
OUT = "/root/autodl-tmp/thesis/experiments/llm_probe/runs/diagnostics/ch3-2x2-fairsel"
os.makedirs(OUT, exist_ok=True)

# ---- 超参：逐字照抄 ch3_full.py 第 52、106-107 行 ----
L, BS, HID = 128, 64, 192
SEED, AUX_W = 42, 1.0
EPOCH_STEPS = 1000
N_EPOCH = 20                      # 20 epoch × 1000 步 = 20000 步，与冻结预算相同
# ---- 验证划分：逐字照抄 select_signal.py 第 103 行 ----
VAL_FRAC, TIME_TAIL = 0.10, 0.15

# ---- 阶段闸门与计数器 ----
SELECTION_FROZEN = False
_N24_LOADS = 0
_EVAL24_CALLS = 0

CELLS = [("C00", False, False), ("C01", False, True),
         ("C10", True, False), ("C11", True, True)]

# =====================================================================================
# 阶段一：只读入 LSPR23
# =====================================================================================
log("=" * 96)
log("阶段一 选择：只读入 LSPR23，LSPR24 不进入本进程")
X23 = np.load(f"{CACHE}/X23.npy")
y23 = np.load(f"{CACHE}/y23.npy")
I23 = np.load(f"{CACHE}/I23.npy")
M23 = np.load(f"{CACHE}/M23.npy")
E23 = np.load(f"{CACHE}/E23.npy")
T23 = np.load(f"{CACHE}/T23.npy")
D = X23.shape[1]
assert D == 83, f"特征数应为 83（Dijk 2026 附录 A 口径），实为 {D}"
log(f"LSPR23 流={len(y23):,} 特征数={D} 序列={len(I23):,}")

# ---- 三种验证划分：逐字照抄 select_signal.py 第 151-168 行（本任务只用「实体不相交」）----
rs = np.random.RandomState(SEED)
uent = np.unique(E23)
perm = rs.permutation(len(uent))
val_ent = set(uent[perm[:max(1, int(len(uent) * VAL_FRAC))]].tolist())
m_ent = np.fromiter((e in val_ent for e in E23), bool, len(E23))     # 实体不相交
t_cut = np.quantile(T23, 1.0 - TIME_TAIL)
m_time = T23 >= t_cut                                                 # 时间尾部（本任务不用作信号）
tr_mask = ~(m_ent | m_time)                                           # 训练区：两者都排除
tr_idx = np.flatnonzero(tr_mask)
val_idx = np.flatnonzero(m_ent & ~m_time)                             # 唯一选择信号的来源
assert len(np.intersect1d(val_idx, tr_idx)) == 0, "验证集与训练区有交叠"
log(f"LSPR23 实体 {len(uent):,} | 训练序列 {len(tr_idx):,} | 实体不相交验证 {len(val_idx):,}")
assert len(uent) == 150680, f"LSPR23 实体数自检失败：{len(uent)}"
assert len(tr_idx) == 208598, f"训练序列数自检失败：{len(tr_idx)}"
assert len(val_idx) == 22444, f"实体不相交验证序列数自检失败：{len(val_idx)}"
log("切分自检通过：150,680 实体 / 208,598 训练序列 / 22,444 验证序列，与 select_signal 完全一致")

dev = "cuda" if torch.cuda.is_available() else "cpu"
gX23 = torch.from_numpy(X23).to(dev)
gy23 = torch.from_numpy(y23).to(dev)
gI23 = torch.from_numpy(I23).to(dev)
gM23 = torch.from_numpy(M23).to(dev)
gtr = torch.from_numpy(tr_idx).to(dev)
gval = torch.from_numpy(val_idx).to(dev)
log(f"LSPR23 已上卡 {torch.cuda.memory_allocated()/2**30:.2f} GiB")


# ---- 模型与损失：逐字照抄 ch3_full.py 第 150-172 行 ----
def lp_pool(s, m, p):
    ls = torch.log(s.clamp(min=1e-7)); n = m.sum(1).clamp(min=1.0)
    return torch.exp((torch.logsumexp((p * ls).masked_fill(m < 0.5, -1e30), 1) - torch.log(n)) / p)


class Model(nn.Module):
    def __init__(self, agg, lp, hid=192, dp=0.1):
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


_sl = (y23[I23.reshape(-1)].reshape(I23.shape) * M23).max(1) > 0
_spw = float((1 - _sl.mean()) / max(_sl.mean(), 1e-8))
_pos = torch.tensor([(1 - y23.mean()) / y23.mean()], device=dev)
_lf = nn.BCEWithLogitsLoss(reduction="none", pos_weight=_pos)
_bs = nn.BCELoss(reduction="none")
log(f"逐流 pos_weight={_pos.item():.6f}  序列级 spw={_spw:.6f}（口径照抄 ch3_full，用全量 LSPR23）")
del _sl


@torch.no_grad()
def val_ap(net):
    """LSPR23 实体不相交验证集上的逐流 AP。照抄 select_signal.py ap_on()。

    本函数是唯一的模型选择信号来源，只触碰 gX23/gy23/gI23/gM23/gval。
    """
    net.eval(); P = []; Y = []
    for a in range(0, len(val_idx), 2048):
        sel = gval[a:a + 2048]; idx = gI23[sel][:, :L]; msk = gM23[sel][:, :L]; b = idx.shape[0]
        lo = net(gX23[idx.reshape(-1)].reshape(b, L, D), msk)
        fm = msk.reshape(-1) > 0
        P.append(torch.sigmoid(lo).reshape(-1)[fm].cpu().numpy())
        Y.append(gy23[idx.reshape(-1)].reshape(-1)[fm].cpu().numpy())
    net.train()
    P = np.concatenate(P); Y = np.concatenate(Y)
    assert Y.max() > 0, "验证集无正例，选择信号无效"
    return float(average_precision_score(Y, P))


def train_and_select(agg, lp, seed, tag):
    """训练 20 epoch 不早停，逐 epoch 用 LSPR23 验证 AP 选检查点。

    函数体内不出现任何 LSPR24 标识符；此时进程内也没有 LSPR24 数据。
    """
    torch.manual_seed(seed); np.random.seed(seed)
    net = Model(agg, lp, HID).to(dev)
    dec = [p for n, p in net.named_parameters() if not (n.endswith(".bias") or n == "p_log")]
    nod = [p for n, p in net.named_parameters() if (n.endswith(".bias") or n == "p_log")]
    opt = torch.optim.AdamW([{"params": dec, "weight_decay": 0.01},
                             {"params": nod, "weight_decay": 0.0}], lr=2e-3)
    gen = torch.Generator().manual_seed(seed)
    best = {"ap": -1.0, "epoch": None, "p": None, "state": None}
    hist = []
    t0 = time.time()
    net.train()
    for ep in range(1, N_EPOCH + 1):
        for _ in range(EPOCH_STEPS):
            sel = gtr[torch.randint(0, len(tr_idx), (BS,), generator=gen).to(dev)]
            idx = gI23[sel][:, :L]; msk = gM23[sel][:, :L]
            xb = gX23[idx.reshape(-1)].reshape(BS, L, D)
            yb = gy23[idx.reshape(-1)].reshape(BS, L)
            lo = net(xb, msk); loss = (_lf(lo, yb) * msk).sum() / msk.sum().clamp(min=1)
            if lp:
                sq = lp_pool(torch.sigmoid(lo), msk, net.p).clamp(1e-6, 1 - 1e-6)
                ysq = (yb * msk).amax(1)
                w = 1.0 + (_spw - 1.0) * ysq
                loss = loss + AUX_W * ((_bs(sq, ysq) * w).sum() / w.sum())
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        v = val_ap(net); pv = net.p.item()
        hist.append([ep, v, pv])
        star = ""
        if v > best["ap"]:
            best = {"ap": v, "epoch": ep, "p": pv,
                    "state": {k: t.detach().clone() for k, t in net.state_dict().items()}}
            star = "  ← 当前最优"
        log(f"  {tag} ep {ep:>2}/{N_EPOCH} 验证AP={v:.6f} p={pv:.4f} 累计{(time.time()-t0)/60:.1f}分{star}")
    tr_t = time.time() - t0
    log(f"  {tag} 训练完成 {tr_t/60:.2f} 分，选中 epoch {best['epoch']}（验证AP={best['ap']:.6f} p={best['p']:.4f}）")
    return best, hist, tr_t, sum(p.numel() for p in net.parameters())


SEL = {}
log("=" * 96)
log(f"四格 seed={SEED}，{N_EPOCH} epoch × {EPOCH_STEPS} 步 = {N_EPOCH*EPOCH_STEPS} 步，不早停，串行训练")
for cid, agg, lp in CELLS:
    log(f"--- {cid} (agg={agg}, lp={lp}) ---")
    best, hist, tr_t, npar = train_and_select(agg, lp, SEED, cid)
    SEL[cid] = {"agg": agg, "lp": lp, "best": best, "hist": hist, "tr": tr_t, "npar": npar}

# =====================================================================================
# 阶段闸门：先把选择结果写盘冻结，再允许读入 LSPR24
# =====================================================================================
_frozen = {"protocol": "逐epoch在LSPR23实体不相交验证集上取逐流AP最大的epoch，无末5平均，不早停",
           "seed": SEED, "n_epoch": N_EPOCH, "epoch_steps": EPOCH_STEPS,
           "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
           "cells": {c: {"selected_epoch": SEL[c]["best"]["epoch"],
                         "val_ap_at_selected": SEL[c]["best"]["ap"],
                         "p_at_selected": SEL[c]["best"]["p"],
                         "val_ap_history": SEL[c]["hist"],
                         "train_seconds": SEL[c]["tr"]} for c in SEL}}
json.dump(_frozen, open(f"{OUT}/selection_frozen.json", "w"), ensure_ascii=False, indent=2)
SELECTION_FROZEN = True
log("=" * 96)
log(f"选择阶段结束，结果已冻结写盘 {OUT}/selection_frozen.json")
for c in SEL:
    log(f"  {c}: 选中 epoch={SEL[c]['best']['epoch']:>2} 验证AP={SEL[c]['best']['ap']:.6f}")

# 释放 LSPR23 显存后再读 LSPR24，压低峰值
del gX23, gy23, gI23, gM23, gtr, gval, X23, y23, I23, M23, E23, T23
torch.cuda.empty_cache()
log(f"LSPR23 已释放，显存 {torch.cuda.memory_allocated()/2**30:.2f} GiB")

# =====================================================================================
# 阶段二：此刻才第一次读入 LSPR24，每格只评价一次
# =====================================================================================
assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段读入 LSPR24"
_N24_LOADS += 1
log("=" * 96)
log("阶段二 评价：首次读入 LSPR24（选择已冻结）")
X24 = np.load(f"{CACHE}/X24.npy")
y24 = np.load(f"{CACHE}/y24.npy")
I24 = np.load(f"{CACHE}/I24.npy")
M24 = np.load(f"{CACHE}/M24.npy")
s24 = np.load(f"{CACHE}/s24.npy", allow_pickle=True)
d24 = np.load(f"{CACHE}/d24.npy", allow_pickle=True)
t24 = np.load(f"{CACHE}/t24.npy")
assert X24.shape[1] == D

# ---- 实体构造：逐字照抄 ch3_full.py 第 130-141 行 ----
key24 = np.array([a + "|" + b if a <= b else b + "|" + a for a, b in zip(s24, d24)], object)
_, ent24 = np.unique(key24, return_inverse=True)
N_ENT = ent24.max() + 1
ent_lab = np.zeros(N_ENT, np.float32); np.maximum.at(ent_lab, ent24, y24)
_flow_pos = float(y24.astype(np.float64).mean())
log(f"LSPR24 实体={N_ENT:,} 正例实体={int(ent_lab.sum()):,} 实体先验={ent_lab.mean():.10f} 逐流正例率={_flow_pos:.10f}")
assert N_ENT == 47115, f"LSPR24 实体数自检失败：{N_ENT}"
assert int(ent_lab.sum()) == 752, f"LSPR24 正例实体自检失败：{int(ent_lab.sum())}"
assert abs(_flow_pos - 0.0257073138) < 1e-9, f"LSPR24 逐流正例率自检失败：{_flow_pos:.12f}"
log("LSPR24 自检通过：实体 47,115 / 正例实体 752 / 逐流正例率 0.0257073138")
del key24, s24, d24

_ord = np.lexsort((t24, ent24))
_e = ent24[_ord]
_start = np.flatnonzero(np.r_[True, _e[1:] != _e[:-1]])
_rank = np.empty(len(_ord), np.int64)
_rank[_ord] = np.arange(len(_ord)) - np.repeat(_start, np.diff(np.r_[_start, len(_ord)]))
del _ord, _e, _start, t24

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
def score24(net):
    """LSPR24 逐流打分。推理循环逐字照抄 ch3_full.py 第 199-207 行（单检查点，无平均）。"""
    global _EVAL24_CALLS
    assert SELECTION_FROZEN, "阶段闸门未开：禁止在选择阶段评价 LSPR24"
    _EVAL24_CALLS += 1
    net.eval()
    sc = torch.zeros(len(y24), device=dev)
    sn = torch.zeros(len(y24), dtype=torch.bool, device=dev)
    for a in range(0, len(I24), 2048):
        idx = gI24[a:a + 2048][:, :L]; msk = gM24[a:a + 2048][:, :L]; b = idx.shape[0]
        pr = torch.sigmoid(net(gX24[idx.reshape(-1)].reshape(b, L, D), msk))
        fi = idx.reshape(-1); fm = msk.reshape(-1) > 0
        sc[fi[fm]] = pr.reshape(-1)[fm]; sn[fi[fm]] = True
    return sc.cpu().numpy(), sn.cpu().numpy()


RES = {}
log("=" * 96)
log("每格加载选中 epoch 的权重，在 LSPR24 上评价一次")
for cid, agg, lp in CELLS:
    net = Model(agg, lp, HID).to(dev)
    net.load_state_dict(SEL[cid]["best"]["state"])
    p = net.p.item()
    assert abs(p - SEL[cid]["best"]["p"]) < 1e-9, f"{cid} 权重回载后 p 不一致"
    t1 = time.time()
    sc, seen = score24(net)
    ev_t = time.time() - t1
    fap = average_precision_score(y24[seen], sc[seen])
    fauc = roc_auc_score(y24[seen], sc[seen])
    e_max, n_ent_ok = ent_ap(sc, seen)
    e_lp, _ = ent_ap(sc, seen, p if lp else None)     # ch3_full 口径：lp=False 时退化为 max
    dr_main = dr_at_fpr(sc, seen, 0.04, p if lp else None)
    dr_max = dr_at_fpr(sc, seen, 0.04, None)
    RES[cid] = {"agg": agg, "lp": lp, "sel_epoch": SEL[cid]["best"]["epoch"],
                "val_ap": SEL[cid]["best"]["ap"], "p": p,
                "fap": float(fap), "fauc": float(fauc),
                "e_max": float(e_max), "e_lp": float(e_lp),
                "dr_main": float(dr_main), "dr_max": float(dr_max),
                "n_ent_scored": int(n_ent_ok), "tr": SEL[cid]["tr"], "ev": ev_t,
                "npar": SEL[cid]["npar"]}
    log(f"{cid}: epoch={SEL[cid]['best']['epoch']:>2} 验证AP={SEL[cid]['best']['ap']:.6f} p={p:.4f} | "
        f"逐流AP={fap:.6f} AUC={fauc:.6f} 实体AP(max)={e_max:.6f} 实体AP(Lp)={e_lp:.6f} "
        f"DR@4%FPR={dr_main:.6f} (max口径={dr_max:.6f}) 覆盖实体={n_ent_ok:,} 训练{SEL[cid]['tr']/60:.2f}分 推理{ev_t:.1f}秒")
    if cid == "C11":
        np.save(f"{OUT}/scores_C11.npy", sc); np.save(f"{OUT}/seen_C11.npy", seen)
        log(f"  C11 逐流分数已存 {OUT}/scores_C11.npy")
    del sc, seen, net
    torch.cuda.empty_cache()

assert _EVAL24_CALLS == 4, f"LSPR24 评价次数应为 4（每格一次），实为 {_EVAL24_CALLS}"
assert _N24_LOADS == 1, f"LSPR24 应只从磁盘读入 1 次，实为 {_N24_LOADS}"
log(f"隔离断言通过：LSPR24 磁盘读入 {_N24_LOADS} 次，评价 {_EVAL24_CALLS} 次（每格恰一次），均发生在选择冻结之后")

# =====================================================================================
# 交互项与组合创新判据
# =====================================================================================
INTER = {}
log("=" * 96)
log("2x2 交互项：交互 = C11 − C10 − C01 + C00；组合创新 = 交互>0 且 组合>单模块之和")
for label, key in [("实体AP(主口径: lp格用Lp, 非lp格用max)", "e_lp"),
                   ("实体AP(全格 max 口径)", "e_max"),
                   ("DR@4%FPR(主口径)", "dr_main"),
                   ("DR@4%FPR(全格 max 口径)", "dr_max"),
                   ("逐流AP", "fap")]:
    v = {c: RES[c][key] for c in RES}
    eA = v["C10"] - v["C00"]; eB = v["C01"] - v["C00"]; eAB = v["C11"] - v["C00"]
    inter = eAB - (eA + eB)
    c1 = inter > 0; c2 = eAB > (eA + eB); c3 = eAB > 0
    INTER[key] = {"label": label, "C00": v["C00"], "C01": v["C01"], "C10": v["C10"], "C11": v["C11"],
                  "A": eA, "B": eB, "sum": eA + eB, "combo": eAB, "interaction": inter,
                  "crit_interaction_pos": bool(c1), "crit_combo_gt_sum": bool(c2), "crit_combo_pos": bool(c3),
                  "combo_innovation": bool(c1 and c3)}
    log(f"\n【{label}】")
    log(f"  C00={v['C00']:.6f}  C01={v['C01']:.6f}  C10={v['C10']:.6f}  C11={v['C11']:.6f}")
    log(f"  A(仅聚合)={eA:+.6f}  B(仅Lp)={eB:+.6f}  之和={eA+eB:+.6f}  组合={eAB:+.6f}  交互={inter:+.6f}")
    log(f"  判据一 交互>0: {'通过' if c1 else '不通过'} | 判据二 组合>基线: {'通过' if c3 else '不通过'}"
        f" | ★ 组合创新{'成立' if (c1 and c3) else '不成立'}")

# ---- 与冻结协议（末 5 平均）逐格对比：数字取自 ch3-full/ch3_full_results.json ----
FROZEN = {"C00": {"fap": 0.2333664097913168, "e_max": 0.37209568769477186, "e_lp": 0.37209568769477186,
                  "dr_main": 0.6037234042553191, "p": 2.0},
          "C01": {"fap": 0.21993812532593643, "e_max": 0.41994303728364274, "e_lp": 0.39412433100623306,
                  "dr_main": 0.6462765957446809, "p": 0.6068703413009644},
          "C10": {"fap": 0.4277763768979044, "e_max": 0.3496913816510664, "e_lp": 0.3496913816510664,
                  "dr_main": 0.6356382978723404, "p": 2.0},
          "C11": {"fap": 0.2315713900260571, "e_max": 0.3858276572759182, "e_lp": 0.46298806991944896,
                  "dr_main": 0.6954787234042553, "p": 1.2235541820526123}}
log("=" * 96)
log("与冻结协议（末 5 个 epoch 权重平均）的逐格对比：新协议 − 冻结")
DELTA = {}
for cid in ["C00", "C01", "C10", "C11"]:
    d = {k: RES[cid][k] - FROZEN[cid][k] for k in ["fap", "e_max", "e_lp", "dr_main"]}
    DELTA[cid] = d
    log(f"  {cid}: 逐流AP {FROZEN[cid]['fap']:.6f}→{RES[cid]['fap']:.6f} ({d['fap']:+.6f}) | "
        f"实体AP(主) {FROZEN[cid]['e_lp']:.6f}→{RES[cid]['e_lp']:.6f} ({d['e_lp']:+.6f}) | "
        f"实体AP(max) {FROZEN[cid]['e_max']:.6f}→{RES[cid]['e_max']:.6f} ({d['e_max']:+.6f}) | "
        f"DR@4%FPR {FROZEN[cid]['dr_main']:.6f}→{RES[cid]['dr_main']:.6f} ({d['dr_main']:+.6f})")

# ---- 与 XGBoost 实体基线对比 ----
XGB = {"e_lp": 0.531917, "dr_main": 0.816489, "fap": 0.222391}
log("=" * 96)
log("与 XGBoost 实体基线对比（XGB: 实体AP(Lp)=0.531917 DR@4%FPR=0.816489 逐流AP=0.222391）")
for cid in ["C00", "C01", "C10", "C11"]:
    log(f"  {cid}: 实体AP {RES[cid]['e_lp']:.6f} ({RES[cid]['e_lp']-XGB['e_lp']:+.6f}) | "
        f"DR@4%FPR {RES[cid]['dr_main']:.6f} ({RES[cid]['dr_main']-XGB['dr_main']:+.6f}) | "
        f"逐流AP {RES[cid]['fap']:.6f} ({RES[cid]['fap']-XGB['fap']:+.6f})")

json.dump({"protocol": _frozen["protocol"], "seed": SEED,
           "n_train_seq": int(len(tr_idx)), "n_val_seq": int(len(val_idx)),
           "lspr24": {"n_entity": int(N_ENT), "n_pos_entity": int(ent_lab.sum()),
                      "flow_pos_rate": _flow_pos, "entity_prior": float(ent_lab.mean())},
           "cells": RES, "selection": _frozen["cells"], "interaction": INTER,
           "frozen_reference": FROZEN, "delta_vs_frozen": DELTA, "xgb_reference": XGB,
           "isolation": {"lspr24_disk_loads": _N24_LOADS, "lspr24_evals": _EVAL24_CALLS}},
          open(f"{OUT}/ch3_2x2_fairsel_results.json", "w"), ensure_ascii=False, indent=2)
log(f"全部结果已存 {OUT}/ch3_2x2_fairsel_results.json")
log(f"总耗时 {(time.time()-T0)/60:.1f} 分")
